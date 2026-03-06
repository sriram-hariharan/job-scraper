import re

def normalize_location(loc):

    if not loc:
        return ""

<<<<<<< HEAD
    loc = loc.replace("US Offsite", "Remote")
    loc = loc.replace("(Hybrid)", "Hybrid")
    loc = loc.replace("(Remote)", "Remote")

    loc = re.sub(r"\s+", " ", loc)

    return loc.strip()
=======
    # handle multi-location lists from Workday
    if isinstance(loc, list):
        loc = " | ".join(loc)

    loc = loc.replace("US Offsite", "Remote")

    return loc
>>>>>>> main
