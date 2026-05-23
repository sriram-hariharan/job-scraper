from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import re
from collections import Counter
from pathlib import Path
from src.utils.posted_at_utils import parse_posted_at
from src.utils.workday_timestamp import fetch_workday_timestamp
from src.config.consts import (
    TITLE_INCLUDE_REGEX,
    TITLE_EXCLUDE_REGEX,
    US_STATES,
    US_STATE_NAMES,
    ALL_COUNTRIES,
    PUNCT_REGEX,
    ROMAN_SUFFIX_REGEX,
    WHITESPACE_REGEX,
    TOKEN_SPLIT_REGEX,
    ATS_LEVER,
    ATS_WORKDAY,
    ATS_JOBVITE,
    TIMESTAMP_WORKERS,
    DATE_ONLY_HOUR,
    FRESHNESS_HOURS,
    MAJOR_US_CITIES,
    FOREIGN_CITY_BLOCKLIST,
    USER_PIPELINE_UNKNOWN_TIMESTAMP_JOB_CAP,
)
from src.config.role_taxonomy import (
    DEFAULT_ROLE_FAMILY_IDS,
    ROLE_TAXONOMY,
    compile_role_title_regexes,
)
from src.utils.logging import get_logger
from src.scrapers.ashby_scraper import fetch_ashby_timestamp_result

logger = get_logger(__name__)

US_COUNTRY_REGEX = re.compile(
    r"(?:\bU\.?\s*S\.?\b|\bUSA\b|\bUNITED STATES(?: OF AMERICA)?\b)",
    re.I,
)
US_TIMEZONE_REGEX = re.compile(
    r"(?:\bU\.?\s*S\.?\b|\bUSA\b|\bUNITED STATES)\s+TIME\s*ZONES?\b",
    re.I,
)
NON_WORD_REGEX = re.compile(r"[^\w\s]")
JOB_TEXT_FIELDS_FOR_EXCLUSIONS = (
    "title",
    "company",
    "location",
    "source",
    "url",
    "job_url",
    "summary",
    "description",
    "description_text",
    "short_description",
)
ROLE_TITLE_FILTER_AUDIT_FIELDNAMES = [
    "job_company",
    "job_title",
    "job_location",
    "source",
    "selected_role_families",
    "title_filter_decision",
    "title_filter_reason",
    "matched_role_family",
    "matched_pattern",
    "suspected_role_family_hint",
    "posted_at",
    "url",
]

ROLE_TITLE_HINT_PATTERNS = (
    ("ml_ai_engineering", re.compile(r"\b(?:ml|machine learning|ai|llm|computer vision|research engineer)\b", re.I)),
    ("data_engineering", re.compile(r"\b(?:data platform|data infra|data infrastructure|data engineer)\b", re.I)),
    ("analytics", re.compile(r"\b(?:analytics|data analyst|bi|business intelligence)\b", re.I)),
    ("backend_engineering", re.compile(r"\b(?:backend|back end|api|server side)\b", re.I)),
    ("frontend_engineering", re.compile(r"\b(?:frontend|front end|ui engineer|web developer|react)\b", re.I)),
    ("fullstack_engineering", re.compile(r"\b(?:full stack|fullstack)\b", re.I)),
    ("software_engineering", re.compile(r"\b(?:software engineer|software developer|swe|developer|member of technical staff|mts|forward deployed engineer)\b", re.I)),
    ("cloud_devops", re.compile(r"\b(?:cloud|devops|infrastructure|infra|platform engineer)\b", re.I)),
    ("sre", re.compile(r"\b(?:site reliability|sre|reliability engineer)\b", re.I)),
    ("qa_automation", re.compile(r"\b(?:qa|quality assurance|test engineer|sdet|automation)\b", re.I)),
    ("security", re.compile(r"\b(?:security|appsec|application security)\b", re.I)),
    ("solutions_engineering", re.compile(r"\b(?:solutions engineer|solution engineer|sales engineer|forward deployed)\b", re.I)),
)


def _role_title_regexes(selected_role_families=None):
    if selected_role_families:
        return compile_role_title_regexes(selected_role_families)

    return TITLE_INCLUDE_REGEX, TITLE_EXCLUDE_REGEX

def normalize_title(title):
    if not title:
        return ""

    title = title.lower()
    title = PUNCT_REGEX.sub(" ", title)
    title = ROMAN_SUFFIX_REGEX.sub("", title)
    return WHITESPACE_REGEX.sub(" ", title).strip()


def _normalize_preference_list(values):
    if not values:
        return []
    raw_values = values if isinstance(values, (list, tuple, set)) else [values]
    normalized = []
    for value in raw_values:
        text = WHITESPACE_REGEX.sub(" ", str(value or "").strip().lower())
        if text and text not in normalized:
            normalized.append(text)
    return normalized


def _normalized_job_text(job, field_names=JOB_TEXT_FIELDS_FOR_EXCLUSIONS):
    parts = []
    for field_name in field_names:
        value = job.get(field_name)
        if isinstance(value, list):
            parts.extend(str(item or "") for item in value)
        else:
            parts.append(str(value or ""))
    text = " ".join(part for part in parts if part.strip()).lower()
    text = PUNCT_REGEX.sub(" ", text)
    return WHITESPACE_REGEX.sub(" ", text).strip()


def matched_excluded_keyword(job, excluded_keywords=None):
    haystack = _normalized_job_text(job)
    if not haystack:
        return ""

    for keyword in _normalize_preference_list(excluded_keywords):
        needle = PUNCT_REGEX.sub(" ", keyword)
        needle = WHITESPACE_REGEX.sub(" ", needle).strip()
        if not needle:
            continue
        if re.search(rf"(?<!\w){re.escape(needle)}(?!\w)", haystack):
            return keyword

    return ""


def _selected_role_family_ids(selected_role_families=None):
    if selected_role_families:
        return tuple(
            role_family_id
            for role_family_id in (str(value or "").strip() for value in selected_role_families)
            if role_family_id in ROLE_TAXONOMY
        )

    return DEFAULT_ROLE_FAMILY_IDS


def _first_role_title_include_match(normalized_title, selected_role_families=None):
    for role_family_id in _selected_role_family_ids(selected_role_families):
        role_family = ROLE_TAXONOMY.get(role_family_id, {})
        for pattern in role_family.get("title_include_patterns", ()) or ():
            regex = re.compile(pattern, re.I)
            if regex.search(normalized_title):
                return role_family_id, pattern

    return "", ""


def _suspected_role_family_hint(title, selected_role_families=None):
    raw_title = str(title or "").strip()
    if not raw_title:
        return ""

    selected = set(_selected_role_family_ids(selected_role_families))
    for role_family_id, regex in ROLE_TITLE_HINT_PATTERNS:
        if selected and role_family_id not in selected:
            continue
        if regex.search(raw_title):
            return role_family_id

    return ""


def title_match_detail(title, selected_role_families=None):
    detail = {
        "matched": False,
        "reason": "missing_title",
        "matched_role_family": "",
        "matched_pattern": "",
        "suspected_role_family_hint": "",
    }

    if not title:
        return detail

    include_regexes, exclude_regexes = _role_title_regexes(selected_role_families)
    normalized = normalize_title(title)
    matched_role_family, matched_pattern = _first_role_title_include_match(
        normalized,
        selected_role_families=selected_role_families,
    )
    detail["matched_role_family"] = matched_role_family
    detail["matched_pattern"] = matched_pattern
    detail["suspected_role_family_hint"] = _suspected_role_family_hint(
        title,
        selected_role_families=selected_role_families,
    )

    if not any(regex.search(normalized) for regex in include_regexes):
        detail["reason"] = "no_include_pattern_match"
        return detail

    if any(regex.search(normalized) for regex in exclude_regexes):
        detail["reason"] = "exclude_pattern_match"
        return detail

    detail["matched"] = True
    detail["reason"] = "include_pattern_match"
    return detail


def title_matches(title, selected_role_families=None):
    return bool(title_match_detail(title, selected_role_families=selected_role_families)["matched"])


def build_role_title_filter_audit_row(job, selected_role_families=None):
    title = job.get("title")
    detail = title_match_detail(title, selected_role_families=selected_role_families)
    location = job.get("location")
    if isinstance(location, list):
        location = "; ".join(str(value or "").strip() for value in location if str(value or "").strip())

    selected = _selected_role_family_ids(selected_role_families)
    return {
        "job_company": str(job.get("company") or ""),
        "job_title": str(title or ""),
        "job_location": str(location or ""),
        "source": str(job.get("source") or ""),
        "selected_role_families": "|".join(selected),
        "title_filter_decision": "pass" if detail["matched"] else "reject",
        "title_filter_reason": detail["reason"],
        "matched_role_family": detail["matched_role_family"] if detail["matched"] else "",
        "matched_pattern": detail["matched_pattern"] if detail["matched"] else "",
        "suspected_role_family_hint": detail["suspected_role_family_hint"] if not detail["matched"] else "",
        "posted_at": str(job.get("posted_at") or ""),
        "url": str(job.get("url") or job.get("job_url") or ""),
    }


def role_title_filter_audit_counts(audit_rows):
    rows = list(audit_rows or [])
    pass_count = sum(1 for row in rows if row.get("title_filter_decision") == "pass")
    reject_count = sum(1 for row in rows if row.get("title_filter_decision") == "reject")
    suspected_count = sum(
        1
        for row in rows
        if row.get("title_filter_decision") == "reject"
        and str(row.get("suspected_role_family_hint") or "").strip()
    )
    return {
        "role_title_audit_total": len(rows),
        "role_title_audit_pass": pass_count,
        "role_title_audit_reject": reject_count,
        "role_title_audit_suspected_false_negative": suspected_count,
    }


def write_role_title_filter_audit_csv(audit_rows, output_path):
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=ROLE_TITLE_FILTER_AUDIT_FIELDNAMES)
        writer.writeheader()
        for row in audit_rows or []:
            writer.writerow({field: row.get(field, "") for field in ROLE_TITLE_FILTER_AUDIT_FIELDNAMES})
    return path


def _normalized_location_text(location):
    normalized = str(location or "").upper()
    normalized = normalized.replace("&", " AND ")
    normalized = NON_WORD_REGEX.sub(" ", normalized)
    return WHITESPACE_REGEX.sub(" ", normalized).strip()


def _geotext_has_us_city(location):
    try:
        from geotext import GeoText
    except Exception:
        return False

    try:
        places = GeoText(str(location or ""))
    except Exception:
        return False

    country_mentions = getattr(places, "country_mentions", {}) or {}
    if "US" in country_mentions or "United States" in country_mentions:
        return True

    cities = getattr(places, "cities", []) or []
    for city in cities:
        if str(city or "").strip().upper() in MAJOR_US_CITIES:
            return True

    return False


def us_location(location, source):

    if not location:
        return False

    raw_location = str(location or "")
    loc = raw_location.upper()
    normalized_loc = _normalized_location_text(raw_location)

    if source == "ashby":
        if "REMOTE" in loc and US_COUNTRY_REGEX.search(raw_location):
            return True
        if loc == "REMOTE":
            return True
        if loc == "UNITED STATES":
            return True
        
    if source == ATS_LEVER and "," not in loc and "USA" not in loc and "UNITED STATES" not in loc:
        return False

    if normalized_loc in FOREIGN_CITY_BLOCKLIST:
        return False
    
    # reject foreign countries
    FOREIGN_COUNTRY_REGEX = re.compile("|".join(ALL_COUNTRIES), re.I)
    if FOREIGN_COUNTRY_REGEX.search(loc) and "UNITED STATES" not in loc:
        return False

    if US_COUNTRY_REGEX.search(raw_location):
        return True

    if "REMOTE" in loc and (
        US_COUNTRY_REGEX.search(raw_location) or US_TIMEZONE_REGEX.search(raw_location)
    ):
        return True

    if _geotext_has_us_city(raw_location):
        return True

    tokens = set(TOKEN_SPLIT_REGEX.split(normalized_loc))

    if tokens & US_STATES:
        return True

    if "NYC" in tokens:
        return True

    for state in US_STATE_NAMES:
        if state in normalized_loc:
            return True

    if any(city in normalized_loc for city in MAJOR_US_CITIES):
        return True
    

    return False


def posted_within_24h(posted_at_raw):
    dt = parse_posted_at(posted_at_raw)
    if not dt:
        return False

    now = datetime.now(timezone.utc)

    if dt.hour == DATE_ONLY_HOUR and dt.minute == 0 and dt.second == 0:
        return dt.date() >= (now - timedelta(days=1)).date()

    return dt >= now - timedelta(hours=FRESHNESS_HOURS)


def ashby_posting_id(job):
    raw_job_id = job.get("_job_id")

    if not raw_job_id and isinstance(job.get("meta"), dict):
        raw_job_id = job.get("meta", {}).get("_job_id")

    if not raw_job_id:
        raw_job_id = job.get("job_id")

    job_id = str(raw_job_id or "").strip()
    if job_id.startswith("as_"):
        job_id = job_id[3:]

    return job_id


def _filter_mode_allows_unknown_ashby_timestamp(filter_mode):
    return str(filter_mode or "").strip().lower() in {
        "user_pipeline",
        "planning",
        "user_planning",
        "user_pipeline_planning",
    }


def _filter_diagnostics(rejection_reasons, title_pass, location_pass):
    diagnostics = {
        "title_pass": title_pass,
        "location_pass": location_pass,
    }
    diagnostics.update(dict(rejection_reasons))
    return diagnostics


def filter_jobs(
    jobs,
    selected_role_families=None,
    filter_mode="strict_live",
    return_diagnostics=False,
    role_title_audit_rows=None,
    excluded_keywords=None,
):

    title_pass = 0
    location_pass = 0
    prefiltered = []
    rejection_reasons = Counter()

    for job in jobs:

        title = job.get("title")
        location_field = job.get("location")

        locations = location_field if isinstance(location_field, list) else [location_field]

        title_detail = title_match_detail(title, selected_role_families=selected_role_families)
        if role_title_audit_rows is not None:
            role_title_audit_rows.append(
                build_role_title_filter_audit_row(
                    job,
                    selected_role_families=selected_role_families,
                )
            )

        excluded_keyword = matched_excluded_keyword(job, excluded_keywords=excluded_keywords)
        if excluded_keyword:
            job["_filter_rejection_reason"] = "excluded_keyword"
            job["_matched_excluded_keyword"] = excluded_keyword
            rejection_reasons["excluded_keyword"] += 1
            continue

        if not title_detail["matched"]:
            rejection_reasons["title_mismatch"] += 1
            continue
        title_pass += 1

        if not any(us_location(loc, job.get("source")) for loc in locations):
            rejection_reasons["location_not_us"] += 1
            continue
        
        location_pass += 1
        prefiltered.append(job)

    ashby_missing = [
    job for job in prefiltered
    if job.get("source") == "ashby"
    and not job.get("posted_at")
    and ashby_posting_id(job)
    ]

    if ashby_missing:

        with ThreadPoolExecutor(max_workers=2) as executor:

            futures = {
                executor.submit(
                    fetch_ashby_timestamp_result,
                    job["company"],
                    ashby_posting_id(job)
                ): job
                for job in ashby_missing
            }

            resolved = 0

            for future in as_completed(futures):

                job = futures[future]

                try:
                    result = future.result()
                    if isinstance(result, dict):
                        ts = result.get("posted_at")
                        marker = str(result.get("marker") or "").strip()
                    else:
                        ts = result
                        marker = ""

                    if ts:
                        job["posted_at"] = ts
                        resolved += 1
                    elif marker:
                        job["_ashby_timestamp_status"] = marker

                except Exception:
                    job["_ashby_timestamp_status"] = "ashby_timestamp_request_failed"

    # resolve missing Workday timestamps
    workday_missing = [
        job for job in prefiltered
        if job.get("source") == ATS_WORKDAY
        and not job.get("posted_at")
        and job.get("_externalPath")
        and job.get("_board_url")
    ]

    if workday_missing:
        with ThreadPoolExecutor(max_workers=TIMESTAMP_WORKERS) as executor:
            futures = {
                executor.submit(
                    fetch_workday_timestamp,
                    job["_board_url"],
                    job["_externalPath"]
                ): job
                for job in workday_missing
            }

            resolved = 0
            for future in as_completed(futures):

                job = futures[future]

                try:
                    ts = future.result()
                    if ts:
                        job["posted_at"] = ts
                        resolved += 1
                except Exception:
                    pass

    filtered = []
    freshness_pass = 0
    unknown_timestamp_allowed = 0
    allow_unknown_ashby_timestamp = _filter_mode_allows_unknown_ashby_timestamp(filter_mode)

    for job in prefiltered:
        posted = job.get("posted_at")

        if job.get("source") == ATS_JOBVITE:
            filtered.append(job)
            continue

        if job.get("source") == "ashby" and not posted:
            if (
                allow_unknown_ashby_timestamp
                and unknown_timestamp_allowed < USER_PIPELINE_UNKNOWN_TIMESTAMP_JOB_CAP
            ):
                job.setdefault("_ashby_timestamp_status", "ashby_timestamp_missing")
                job["_freshness_status"] = "unknown_timestamp_allowed"
                unknown_timestamp_allowed += 1
                rejection_reasons["missing_timestamp_allowed"] += 1
                filtered.append(job)
                continue

            rejection_reasons["missing_timestamp"] += 1
            job.setdefault("_ashby_timestamp_status", "ashby_timestamp_missing")
            continue

        if not posted_within_24h(posted):
            rejection_reasons["not_recent"] += 1
            continue
        
        freshness_pass += 1
        filtered.append(job)

    for job in filtered:
        job.pop("_job_id", None)

    logger.info("")
    logger.info("FILTER DROP ANALYSIS")

    for reason, count in rejection_reasons.items():
        logger.info(f"{reason:20} {count}")

    logger.info(
        "Title pass: %s, Location pass: %s, Freshness pass: %s, Missing timestamp allowed: %s",
        title_pass,
        location_pass,
        freshness_pass,
        unknown_timestamp_allowed,
    )
    logger.info("")

    diagnostics = _filter_diagnostics(rejection_reasons, title_pass, location_pass)
    if return_diagnostics:
        return filtered, diagnostics

    return filtered
