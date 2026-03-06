import re

def normalize_location(loc):

    if not loc:
        return ""

    # handle multi-location lists from Workday
    if isinstance(loc, list):
        loc = " | ".join(loc)

    loc = loc.replace("US Offsite", "Remote")

    return loc