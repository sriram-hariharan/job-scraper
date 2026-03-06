<<<<<<< Updated upstream
from ..config.consts import TARGET_TITLES, EXCLUDED_KEYWORDS, NON_US_COUNTRIES, US_STATE_NAMES, US_STATE_ABBREV

def title_matches(title):

    title_lower = title.lower()

    # Reject unwanted roles
    for word in EXCLUDED_KEYWORDS:
        if word in title_lower:
            return False

    # Accept only target roles
    for target in TARGET_TITLES:

        if title_lower.startswith(target):
            return True
=======
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
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
)

>>>>>>> Stashed changes

        if f" {target}" in title_lower:
            return True

    return False

<<<<<<< Updated upstream

def us_location(location):
=======
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
>>>>>>> Stashed changes

    if not location:
        return False

    loc = location.lower()

<<<<<<< Updated upstream
    # -----------------------------
    # Handle Ashby remote patterns
    # -----------------------------

    if "remote" in loc:
        if "canada" not in loc and "europe" not in loc and "uk" not in loc:
            return True

    # -----------------------------
    # Common US cities used without states
    # (Ashby often returns these)
    # -----------------------------

    US_MAJOR_CITIES = [
        "san francisco",
        "new york",
        "seattle",
        "austin",
        "boston",
        "los angeles",
        "denver",
        "chicago",
        "atlanta",
        "miami"
    ]

    for city in US_MAJOR_CITIES:
        if city in loc:
            return True

    # -----------------------------
    # Reject clearly non-US
    # -----------------------------

    for country in NON_US_COUNTRIES:
        if country in loc:
            return False

    # -----------------------------
    # Existing Greenhouse logic
    # -----------------------------

    parts = loc.replace(";", ",").split(",")

    for part in parts:

        part = part.strip()

        if "united states" in part or "usa" in part:
            return True

        for state in US_STATE_NAMES:
            if state in part:
                return True

        for abbr in US_STATE_ABBREV:
            if part.endswith(f" {abbr}") or part.endswith(f", {abbr}"):
                return True

    return False
=======
    if source == ATS_LEVER and "," not in loc and "USA" not in loc and "UNITED STATES" not in loc:
        return False

    if "UNITED STATES" in loc or "USA" in loc or " U.S." in loc:
        return True

    if "REMOTE" in loc and ("US" in loc or "USA" in loc or "UNITED STATES" in loc):
        return True

    # --------------------------------------------------
    # Reject explicit foreign countries FIRST
    # --------------------------------------------------

    for country in ALL_COUNTRIES:
        if country in loc and country != "UNITED STATES":
            return False

    tokens = set(TOKEN_SPLIT_REGEX.split(loc))

    # US state abbreviation
    if tokens & US_STATES:
        return True

    # US state name
    for state in US_STATE_NAMES:
        if state in loc:
            return True

    # city-state format like "New York"
    if "," not in loc:
        words = loc.split()
        if len(words) == 2:
            possible_state = " ".join(words)
            if possible_state in US_STATE_NAMES:
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

    print("\n--- FILTER DEBUG START ---")
    print("Total jobs entering filter:", len(jobs))

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

    print("Jobs passing title filter:", title_pass)
    print("Jobs passing location filter:", location_pass)
    print("Jobs after title/location filtering:", len(prefiltered))

    # ---------------------------------------------------
    # Resolve missing Workday timestamps
    # ---------------------------------------------------

    workday_missing = [
        job for job in prefiltered
        if job.get("source") == ATS_WORKDAY
        and not job.get("posted_at")
        and job.get("_externalPath")
        and job.get("_board_url")
    ]

    print("Workday jobs missing timestamp (to fetch):", len(workday_missing))

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

        print("Resolved timestamps:", resolved)

    # ---------------------------------------------------
    # Freshness filtering
    # ---------------------------------------------------

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

    print("Jobs passing freshness filter:", freshness_pass)
    print("Jobs after filtering:", len(filtered))
    print("--- FILTER DEBUG END ---\n")

    return filtered
>>>>>>> Stashed changes
