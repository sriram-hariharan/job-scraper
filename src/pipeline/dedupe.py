<<<<<<< Updated upstream
=======
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

>>>>>>> Stashed changes
def dedupe_jobs(jobs):

    seen = set()
    unique = []

    for job in jobs:

        url = job.get("url")

        if not url:
            continue

        if url in seen:
            continue

        seen.add(url)
        unique.append(job)

    return unique