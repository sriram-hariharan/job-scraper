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
    TIMESTAMP_WORKERS,
    DATE_ONLY_HOUR,
    FRESHNESS_HOURS,
    MAJOR_US_CITIES,
    FOREIGN_CITY_BLOCKLIST,
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
    "location_filter_decision",
    "location_filter_reason",
    "freshness_filter_decision",
    "freshness_filter_reason",
    "ashby_timestamp_status",
    "ashby_timestamp_status_code",
    "ashby_timestamp_fetch_decision",
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

SOURCE_HEALTH_REPORT_FIELDNAMES = [
    "source",
    "company",
    "scraped_jobs",
    "title_pass_jobs",
    "title_reject_jobs",
    "location_pass_jobs",
    "location_reject_jobs",
    "freshness_pass_jobs",
    "not_recent_jobs",
    "missing_timestamp_jobs",
    "final_corpus_jobs",
    "final_display_jobs",
    "ashby_timestamp_fetch_success",
    "ashby_timestamp_fetch_429",
    "ashby_timestamp_fetch_failed",
    "notes",
]


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
        "location_filter_decision": "",
        "location_filter_reason": "",
        "freshness_filter_decision": "",
        "freshness_filter_reason": "",
        "ashby_timestamp_status": str(job.get("_ashby_timestamp_status") or ""),
        "ashby_timestamp_status_code": "",
        "ashby_timestamp_fetch_decision": "",
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


def _source_company_key(source, company):
    return (
        str(source or "").strip().lower(),
        str(company or "").strip().lower(),
    )


def _source_company_display(source, company):
    return {
        "source": str(source or "").strip(),
        "company": str(company or "").strip(),
    }


def build_source_health_report_rows(audit_rows=None, final_corpus_jobs=None):
    rows_by_key = {}

    def ensure_row(source, company):
        key = _source_company_key(source, company)
        if key not in rows_by_key:
            display = _source_company_display(source, company)
            rows_by_key[key] = {
                "source": display["source"],
                "company": display["company"],
                "scraped_jobs": 0,
                "title_pass_jobs": 0,
                "title_reject_jobs": 0,
                "location_pass_jobs": 0,
                "location_reject_jobs": 0,
                "freshness_pass_jobs": 0,
                "not_recent_jobs": 0,
                "missing_timestamp_jobs": 0,
                "final_corpus_jobs": 0,
                "final_display_jobs": 0,
                "ashby_timestamp_fetch_success": 0,
                "ashby_timestamp_fetch_429": 0,
                "ashby_timestamp_fetch_failed": 0,
                "notes": "",
            }
        return rows_by_key[key]

    for audit_row in audit_rows or []:
        row = ensure_row(audit_row.get("source"), audit_row.get("job_company"))
        row["scraped_jobs"] += 1

        title_decision = str(audit_row.get("title_filter_decision") or "").strip()
        if title_decision == "pass":
            row["title_pass_jobs"] += 1
        elif title_decision == "reject":
            row["title_reject_jobs"] += 1

        location_decision = str(audit_row.get("location_filter_decision") or "").strip()
        if location_decision == "pass":
            row["location_pass_jobs"] += 1
        elif location_decision == "reject":
            row["location_reject_jobs"] += 1

        freshness_decision = str(audit_row.get("freshness_filter_decision") or "").strip()
        freshness_reason = str(audit_row.get("freshness_filter_reason") or "").strip()
        if freshness_decision == "pass":
            row["freshness_pass_jobs"] += 1
        elif freshness_reason == "not_recent":
            row["not_recent_jobs"] += 1
        elif freshness_reason == "missing_timestamp":
            row["missing_timestamp_jobs"] += 1

        ashby_decision = str(audit_row.get("ashby_timestamp_fetch_decision") or "").strip()
        if ashby_decision == "success":
            row["ashby_timestamp_fetch_success"] += 1
        elif ashby_decision == "429":
            row["ashby_timestamp_fetch_429"] += 1
        elif ashby_decision == "failed":
            row["ashby_timestamp_fetch_failed"] += 1

    for job in final_corpus_jobs or []:
        row = ensure_row(job.get("source"), job.get("company") or job.get("job_company"))
        row["final_corpus_jobs"] += 1
        row["final_display_jobs"] += 1

    return [
        {field: row.get(field, "") for field in SOURCE_HEALTH_REPORT_FIELDNAMES}
        for row in sorted(rows_by_key.values(), key=lambda item: (str(item.get("source", "")).lower(), str(item.get("company", "")).lower()))
    ]


def write_source_health_report_csv(audit_rows, final_corpus_jobs, output_path):
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = build_source_health_report_rows(audit_rows, final_corpus_jobs)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SOURCE_HEALTH_REPORT_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
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


def _ashby_timestamp_cache_key(job):
    company = str(job.get("company") or "").strip().lower()
    job_id = ashby_posting_id(job)
    if not company or not job_id:
        return ""
    return f"{company}:{job_id}"


def _apply_ashby_timestamp_result(job, result):
    if isinstance(result, dict):
        posted_at = result.get("posted_at")
        marker = str(result.get("marker") or "").strip()
        status_code = result.get("status_code")
    else:
        posted_at = result
        marker = ""
        status_code = None

    if posted_at:
        job["posted_at"] = posted_at
    elif marker:
        job["_ashby_timestamp_status"] = marker

    return {
        "posted_at": posted_at,
        "marker": marker,
        "status_code": status_code,
    }


def _audit_update(audit_row, **updates):
    if audit_row is not None:
        for key, value in updates.items():
            audit_row[key] = "" if value is None else value


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
    ashby_timestamp_stats = Counter()
    audit_rows_by_job_id = {}

    for job in jobs:

        title = job.get("title")
        location_field = job.get("location")

        locations = location_field if isinstance(location_field, list) else [location_field]

        title_detail = title_match_detail(title, selected_role_families=selected_role_families)
        audit_row = None
        if role_title_audit_rows is not None:
            audit_row = build_role_title_filter_audit_row(
                job,
                selected_role_families=selected_role_families,
            )
            role_title_audit_rows.append(audit_row)
            audit_rows_by_job_id[id(job)] = audit_row

        excluded_keyword = matched_excluded_keyword(job, excluded_keywords=excluded_keywords)
        if excluded_keyword:
            job["_filter_rejection_reason"] = "excluded_keyword"
            job["_matched_excluded_keyword"] = excluded_keyword
            _audit_update(
                audit_row,
                freshness_filter_decision="reject",
                freshness_filter_reason="excluded_keyword",
            )
            rejection_reasons["excluded_keyword"] += 1
            continue

        if not title_detail["matched"]:
            _audit_update(
                audit_row,
                freshness_filter_decision="reject",
                freshness_filter_reason="title_mismatch",
            )
            rejection_reasons["title_mismatch"] += 1
            continue
        title_pass += 1

        if not any(us_location(loc, job.get("source")) for loc in locations):
            _audit_update(
                audit_row,
                location_filter_decision="reject",
                location_filter_reason="location_not_us",
                freshness_filter_decision="reject",
                freshness_filter_reason="location_not_us",
            )
            rejection_reasons["location_not_us"] += 1
            continue
        
        location_pass += 1
        _audit_update(
            audit_row,
            location_filter_decision="pass",
            location_filter_reason="us_location",
        )
        prefiltered.append(job)

    ashby_missing = [
        job for job in prefiltered
        if job.get("source") == "ashby"
        and not job.get("posted_at")
        and ashby_posting_id(job)
    ]

    if ashby_missing:
        timestamp_cache = {}
        jobs_by_cache_key = {}

        for job in ashby_missing:
            cache_key = _ashby_timestamp_cache_key(job)
            if not cache_key:
                continue

            if cache_key in timestamp_cache:
                ashby_timestamp_stats["ashby_timestamp_cache_hit"] += 1
                _apply_ashby_timestamp_result(job, timestamp_cache[cache_key])
                continue

            if cache_key in jobs_by_cache_key:
                jobs_by_cache_key[cache_key].append(job)
                continue

            jobs_by_cache_key[cache_key] = [job]
            ashby_timestamp_stats["ashby_timestamp_cache_miss"] += 1

        with ThreadPoolExecutor(max_workers=2) as executor:

            futures = {
                executor.submit(
                    fetch_ashby_timestamp_result,
                    jobs[0]["company"],
                    ashby_posting_id(jobs[0])
                ): cache_key
                for cache_key, jobs in jobs_by_cache_key.items()
            }

            for future in as_completed(futures):

                cache_key = futures[future]
                jobs = jobs_by_cache_key.get(cache_key, [])

                try:
                    result = future.result()
                    timestamp_cache[cache_key] = result
                    applied = _apply_ashby_timestamp_result(jobs[0], result) if jobs else {}
                    fetch_decision = "failed"
                    if applied.get("posted_at"):
                        ashby_timestamp_stats["ashby_timestamp_fetch_success"] += 1
                        fetch_decision = "success"
                    elif applied.get("status_code") == 429:
                        ashby_timestamp_stats["ashby_timestamp_fetch_429"] += 1
                        fetch_decision = "429"
                    else:
                        ashby_timestamp_stats["ashby_timestamp_fetch_failed"] += 1

                    for index, timestamp_job in enumerate(jobs):
                        if index > 0:
                            ashby_timestamp_stats["ashby_timestamp_cache_hit"] += 1
                            _apply_ashby_timestamp_result(timestamp_job, result)
                        _audit_update(
                            audit_rows_by_job_id.get(id(timestamp_job)),
                            posted_at=timestamp_job.get("posted_at") or "",
                            ashby_timestamp_status=timestamp_job.get("_ashby_timestamp_status") or "",
                            ashby_timestamp_status_code=applied.get("status_code") or "",
                            ashby_timestamp_fetch_decision=fetch_decision if index == 0 else "cache_hit",
                        )

                except Exception:
                    result = {
                        "posted_at": None,
                        "marker": "ashby_timestamp_request_failed",
                        "status_code": None,
                    }
                    timestamp_cache[cache_key] = result
                    ashby_timestamp_stats["ashby_timestamp_fetch_failed"] += 1
                    for index, job in enumerate(jobs):
                        _apply_ashby_timestamp_result(job, result)
                        _audit_update(
                            audit_rows_by_job_id.get(id(job)),
                            ashby_timestamp_status=job.get("_ashby_timestamp_status") or "",
                            ashby_timestamp_fetch_decision="failed" if index == 0 else "cache_hit",
                        )

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

    for job in prefiltered:
        posted = job.get("posted_at")

        if not posted:
            rejection_reasons["missing_timestamp"] += 1
            if job.get("source") == "ashby":
                job.setdefault("_ashby_timestamp_status", "ashby_timestamp_missing")
            _audit_update(
                audit_rows_by_job_id.get(id(job)),
                ashby_timestamp_status=job.get("_ashby_timestamp_status") or "",
                freshness_filter_decision="reject",
                freshness_filter_reason="missing_timestamp",
                posted_at="",
            )
            continue

        if not posted_within_24h(posted):
            rejection_reasons["not_recent"] += 1
            _audit_update(
                audit_rows_by_job_id.get(id(job)),
                freshness_filter_decision="reject",
                freshness_filter_reason="not_recent",
                posted_at=posted,
            )
            continue
        
        freshness_pass += 1
        _audit_update(
            audit_rows_by_job_id.get(id(job)),
            freshness_filter_decision="pass",
            freshness_filter_reason="fresh",
            posted_at=posted,
        )
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
        0,
    )
    logger.info("")

    diagnostics = _filter_diagnostics(rejection_reasons, title_pass, location_pass)
    diagnostics.update(dict(ashby_timestamp_stats))
    if return_diagnostics:
        return filtered, diagnostics

    return filtered
