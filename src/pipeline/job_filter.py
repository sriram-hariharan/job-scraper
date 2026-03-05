from datetime import datetime, timedelta

JOB_TITLES = [
    "Data Scientist",
    "Senior Data Scientist",
    "Data Analyst",
    "Senior Data Analyst",
    "Machine Learning Engineer",
    "AI Engineer",
    "Applied Scientist"
]
US_STATES = [
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA",
    "HI","ID","IL","IN","IA","KS","KY","LA","ME","MD",
    "MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
    "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC",
    "SD","TN","TX","UT","VT","VA","WA","WV","WI","WY"
]

def title_matches(title: str) -> bool:

    if not title:
        return False

    title_lower = title.lower()

    for role in JOB_TITLES:
        if role.lower() in title_lower:
            return True

    return False


def us_location(location: str):

    if not location:
        return False

    loc = location.upper()

    if "UNITED STATES" in loc:
        return True

    if " USA" in loc:
        return True

    if "REMOTE" in loc:
        return True

    for state in US_STATES:
        if f", {state}" in loc:
            return True

    return False


def posted_within_24h(posted_on):

    if not posted_on:
        return True  # allow if timestamp missing

    try:
        if isinstance(posted_on, datetime):
            posted_time = posted_on
        else:
            posted_time = datetime.fromisoformat(posted_on)

        return posted_time >= datetime.utcnow() - timedelta(hours=24)

    except Exception:
        return True


def filter_jobs(jobs):

    filtered = []

    for job in jobs:

        title = job.get("title")
        location = job.get("location")
        posted = job.get("postedOn") or job.get("posted_on")

        if not title_matches(title):
            continue

        if not us_location(location):
            continue

        if not posted_within_24h(posted):
            continue

        filtered.append(job)

    print("Jobs after filtering:", len(filtered))

    return filtered