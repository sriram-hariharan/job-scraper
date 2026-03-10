from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

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
)
from src.utils.logging import get_logger
from src.scrapers.ashby_scraper import fetch_ashby_timestamp

logger = get_logger(__name__)

def normalize_title(title):
    if not title:
        return ""

    title = title.lower()
    title = PUNCT_REGEX.sub(" ", title)
    title = ROMAN_SUFFIX_REGEX.sub("", title)
    return WHITESPACE_REGEX.sub(" ", title).strip()


def title_matches(title):
    if not title:
        return False

    normalized = normalize_title(title)
    if not any(regex.search(normalized) for regex in TITLE_INCLUDE_REGEX):
        return False

    if any(regex.search(normalized) for regex in TITLE_EXCLUDE_REGEX):
        return False

    return True


def us_location(location, source):

    if not location:
        return False

    loc = location.upper()

    if source == "ashby":
        if "REMOTE" in loc and ("US" in loc or "UNITED STATES" in loc):
            return True
        if loc == "REMOTE":
            return True
        if loc == "UNITED STATES":
            return True
        
    if source == ATS_LEVER and "," not in loc and "USA" not in loc and "UNITED STATES" not in loc:
        return False

    if "UNITED STATES" in loc or "USA" in loc or " U.S." in loc:
        return True

    if "REMOTE" in loc and ("US" in loc or "USA" in loc or "UNITED STATES" in loc):
        return True

    # reject foreign countries
    for country in ALL_COUNTRIES:
        if country in loc and country != "UNITED STATES":
            return False

    tokens = set(TOKEN_SPLIT_REGEX.split(loc))

    if tokens & US_STATES:
        return True

    for state in US_STATE_NAMES:
        if state in loc:
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


def filter_jobs(jobs):

    logger.info("FILTER PIPELINE START")
    logger.info(f"Total jobs entering filter: {len(jobs)}")

    title_pass = 0
    location_pass = 0
    prefiltered = []

    for job in jobs:

        title = job.get("title")
        location_field = job.get("location")

        locations = location_field if isinstance(location_field, list) else [location_field]

        if not title_matches(title):
            continue
        title_pass += 1

        if not any(us_location(loc, job.get("source")) for loc in locations):
            continue
        
        location_pass += 1
        prefiltered.append(job)

    logger.info(f"Jobs passing title filter: {title_pass}")
    logger.info(f"Jobs passing location filter: {location_pass}")
    logger.info(f"Jobs after title/location filtering: {len(prefiltered)}")

    ashby_missing = [
    job for job in prefiltered
    if job.get("source") == "ashby"
    and not job.get("posted_at")
    and job.get("_job_id")
    ]

    logger.info(f"Ashby jobs missing timestamp: {len(ashby_missing)}")

    if ashby_missing:

        with ThreadPoolExecutor(max_workers=2) as executor:

            futures = {
                executor.submit(
                    fetch_ashby_timestamp,
                    job["company"],
                    job["_job_id"]
                ): job
                for job in ashby_missing
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

        logger.info(f"Ashby timestamps resolved: {resolved}")

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

        logger.info(f"Resolved timestamps: {resolved}")

    filtered = []
    freshness_pass = 0

    for job in prefiltered:
        posted = job.get("posted_at")

        if job.get("source") == ATS_JOBVITE:
            filtered.append(job)
            continue

        if not posted_within_24h(posted):
            continue
        
        freshness_pass += 1
        filtered.append(job)

    logger.info(f"Jobs passing freshness filter: {freshness_pass}")
    logger.info(f"Jobs after filtering: {len(filtered)}")
    logger.info("FILTER PIPELINE END")

    for job in filtered:
        job.pop("_job_id", None)

    return filtered