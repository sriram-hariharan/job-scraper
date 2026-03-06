import re
import time

def normalize(text):

    if not text:
        return ""

    # handle Workday multi-location lists
    if isinstance(text, list):
        text = " ".join(sorted(text))

    text = text.lower().strip()

    return text

def dedupe_jobs(jobs):

    seen = set()
    unique_jobs = []

    for job in jobs:

        title = normalize(job.get("title"))
        company = normalize(job.get("company"))
        location = normalize(job.get("location"))

        key = f"{title}|{company}|{location}"

        if key in seen:
            continue

        seen.add(key)
        unique_jobs.append(job)

    print("Jobs after dedupe:", len(unique_jobs))

    return unique_jobs