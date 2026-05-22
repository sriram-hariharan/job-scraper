from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
from collections import Counter
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
from src.config.role_taxonomy import compile_role_title_regexes
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


def title_matches(title, selected_role_families=None):
    if not title:
        return False

    include_regexes, exclude_regexes = _role_title_regexes(selected_role_families)
    normalized = normalize_title(title)
    if not any(regex.search(normalized) for regex in include_regexes):
        return False

    if any(regex.search(normalized) for regex in exclude_regexes):
        return False

    return True


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
):

    title_pass = 0
    location_pass = 0
    prefiltered = []
    rejection_reasons = Counter()

    for job in jobs:

        title = job.get("title")
        location_field = job.get("location")

        locations = location_field if isinstance(location_field, list) else [location_field]

        if not title_matches(title, selected_role_families=selected_role_families):
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
