from datetime import datetime, timedelta, timezone
from src.utils.posted_at_utils import parse_posted_at
import re
import pycountry
from geotext import GeoText

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

# also include common aliases
ALL_COUNTRIES.update({
    "UK",
    "U.K.",
    "UNITED KINGDOM",
    "KOREA",
    "SOUTH KOREA",
    "NORTH KOREA",
})

def normalize_title(title):

    if not title:
        return ""

    title = title.lower()
    # remove punctuation
    title = re.sub(r"[^\w\s]", " ", title)
    # remove roman numeral suffixes like I, II, III, IV, V
    title = re.sub(r"\s+(i|ii|iii|iv|v)$", "", title)
    # collapse whitespace
    title = re.sub(r"\s+", " ", title).strip()

    return title

def title_matches(title: str) -> bool:

    if not title:
        return False

    normalized = normalize_title(title)

    # Must match at least one include pattern
    include_match = any(re.search(pattern, normalized) for pattern in TITLE_INCLUDE_PATTERNS)

    if not include_match:
        return False

    # Reject if excluded pattern found
    if any(re.search(pattern, normalized) for pattern in TITLE_EXCLUDE_PATTERNS):
        return False

    return True

def us_location(location: str, source: str):

    if not location:
        return False

    loc = location.upper()

    if source == "lever":
        # Lever returns many international locations as plain city names
        if "," not in loc and "UNITED STATES" not in loc and "USA" not in loc:
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

def posted_within_24h(posted_at_raw):
    dt = parse_posted_at(posted_at_raw)

    # strict freshness rule
    if dt is None:
        return False

    now = datetime.now(timezone.utc)

    return dt >= now - timedelta(hours=24)


def filter_jobs(jobs):

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