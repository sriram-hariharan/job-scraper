<<<<<<< HEAD
from datetime import datetime, timedelta, timezone
from src.utils.posted_at_utils import parse_posted_at
import re
import pycountry
from geotext import GeoText
=======
<<<<<<< Updated upstream
from ..config.consts import TARGET_TITLES, EXCLUDED_KEYWORDS, NON_US_COUNTRIES, US_STATE_NAMES, US_STATE_ABBREV
>>>>>>> main

# Broader title patterns for AI / ML / Data roles
TITLE_INCLUDE_PATTERNS = [
    r"data scientist",
    r"machine learning engineer",
    r"ml engineer",
    r"ai engineer",
    r"applied scientist",
    r"research scientist",
    r"data analyst",
    r"decision scientist",
    r"ml scientist",
    r"genai",
    r"machine learning",
]

# Exclude senior leadership or irrelevant roles
TITLE_EXCLUDE_PATTERNS = [
    r"director",
    r"vp",
    r"vice president",
    r"manager",
    r"intern",
    r"student",
    r"principal architect"
]

US_STATES = [
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA",
    "HI","ID","IL","IN","IA","KS","KY","LA","ME","MD",
    "MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
    "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC",
    "SD","TN","TX","UT","VT","VA","WA","WV","WI","WY"
]
US_STATE_NAMES = [
"ALABAMA","ALASKA","ARIZONA","ARKANSAS","CALIFORNIA","COLORADO","CONNECTICUT",
"DELAWARE","FLORIDA","GEORGIA","HAWAII","IDAHO","ILLINOIS","INDIANA","IOWA",
"KANSAS","KENTUCKY","LOUISIANA","MAINE","MARYLAND","MASSACHUSETTS","MICHIGAN",
"MINNESOTA","MISSISSIPPI","MISSOURI","MONTANA","NEBRASKA","NEVADA",
"NEW HAMPSHIRE","NEW JERSEY","NEW MEXICO","NEW YORK","NORTH CAROLINA",
"NORTH DAKOTA","OHIO","OKLAHOMA","OREGON","PENNSYLVANIA","RHODE ISLAND",
"SOUTH CAROLINA","SOUTH DAKOTA","TENNESSEE","TEXAS","UTAH","VERMONT",
"VIRGINIA","WASHINGTON","WEST VIRGINIA","WISCONSIN","WYOMING"
]

ALL_COUNTRIES = {c.name.upper() for c in pycountry.countries}

<<<<<<< HEAD
# also include common aliases
ALL_COUNTRIES.update({
    "UK",
    "U.K.",
    "UNITED KINGDOM",
    "KOREA",
    "SOUTH KOREA",
    "NORTH KOREA",
})
=======
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
>>>>>>> main

def normalize_title(title):

    if not title:
        return ""

<<<<<<< HEAD
    title = title.lower()
    # remove punctuation
    title = re.sub(r"[^\w\s]", " ", title)
    # remove roman numeral suffixes like I, II, III, IV, V
    title = re.sub(r"\s+(i|ii|iii|iv|v)$", "", title)
    # collapse whitespace
    title = re.sub(r"\s+", " ", title).strip()

    return title

def title_matches(title: str) -> bool:
=======
<<<<<<< Updated upstream

def us_location(location):
=======
    title = PUNCT_REGEX.sub(" ", title)
    title = ROMAN_SUFFIX_REGEX.sub("", title)
    return WHITESPACE_REGEX.sub(" ", title).strip()


def title_matches(title):
>>>>>>> main

    if not title:
        return False

    normalized = normalize_title(title)
<<<<<<< HEAD

    # Must match at least one include pattern
    include_match = any(re.search(pattern, normalized) for pattern in TITLE_INCLUDE_PATTERNS)

    if not include_match:
        return False

    # Reject if excluded pattern found
    if any(re.search(pattern, normalized) for pattern in TITLE_EXCLUDE_PATTERNS):
=======
    if not any(regex.search(normalized) for regex in TITLE_INCLUDE_REGEX):
        return False

    if any(regex.search(normalized) for regex in TITLE_EXCLUDE_REGEX):
>>>>>>> main
        return False

    return True

<<<<<<< HEAD
def us_location(location: str, source: str):
=======

def us_location(location, source):
>>>>>>> Stashed changes
>>>>>>> main

    if not location:
        return False

    loc = location.upper()

<<<<<<< HEAD
    if source == "lever":
        # Lever returns many international locations as plain city names
        if "," not in loc and "UNITED STATES" not in loc and "USA" not in loc:
=======
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
>>>>>>> main
            return False

    # explicit US indicators
    if "UNITED STATES" in loc or "USA" in loc or " U.S." in loc:
        return True

    # remote but explicitly US
    if "REMOTE" in loc and (
        "US" in loc or "USA" in loc or "UNITED STATES" in loc
    ):
        return True

    # state abbreviation format
    for state in US_STATES:
        if f", {state}" in loc:
            return True

    # state full name format
    for state in US_STATE_NAMES:
        if f", {state}" in loc:
            return True

    # detect country using pycountry list
    for country in ALL_COUNTRIES:
        if country in loc and country != "UNITED STATES":
            return False

    # detect cities using GeoText
    geo = GeoText(location)

    # accept city only if state abbreviation exists
    if geo.cities:
        for state in US_STATES:
            if state in loc:
                return True

    # fallback for office style names
    if "OFFICE" in loc:
        return True

    return False
<<<<<<< HEAD

def posted_within_24h(posted_at_raw):
    dt = parse_posted_at(posted_at_raw)

    # strict freshness rule
    if dt is None:
=======
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
>>>>>>> main
        return False

    now = datetime.now(timezone.utc)

<<<<<<< HEAD
    return dt >= now - timedelta(hours=24)
=======
    if dt.hour == DATE_ONLY_HOUR and dt.minute == 0 and dt.second == 0:
        return dt.date() >= (now - timedelta(days=1)).date()

    return dt >= now - timedelta(hours=FRESHNESS_HOURS)
>>>>>>> main


def filter_jobs(jobs):

<<<<<<< HEAD
    filtered = []

    for job in jobs:
    
        title = job.get("title")
        location = job.get("location")
        posted = job.get("posted_at")
        if not title_matches(title):
            continue

        if not us_location(location, job.get("source")):
            continue

        # allow Jobvite jobs marked as NEW to bypass freshness rule
        if job.get("source") == "jobvite":
            pass
        else:
            if not posted_within_24h(posted):
                continue

        filtered.append(job)

    print("Jobs after filtering:", len(filtered))

    return filtered
=======
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
>>>>>>> main
