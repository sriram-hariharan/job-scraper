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

        if f" {target}" in title_lower:
            return True

    return False


def us_location(location):

    if not location:
        return False

    loc = location.lower()

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