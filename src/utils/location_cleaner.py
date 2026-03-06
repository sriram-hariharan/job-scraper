import re

def normalize_location(loc):

    if not loc:
        return ""

    loc = loc.replace("US Offsite", "Remote")
    loc = loc.replace("(Hybrid)", "Hybrid")
    loc = loc.replace("(Remote)", "Remote")

    loc = re.sub(r"\s+", " ", loc)

    return loc.strip()