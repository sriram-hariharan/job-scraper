<<<<<<< HEAD
=======
<<<<<<< Updated upstream
=======
>>>>>>> main
import re
import time

def normalize(text):

    if not text:
        return ""

<<<<<<< HEAD
    text = text.lower().strip()

    text = re.sub(r"\s+", " ", text)

    return text

=======
    # handle Workday multi-location lists
    if isinstance(text, list):
        text = " ".join(sorted(text))

    text = text.lower().strip()

    return text

>>>>>>> Stashed changes
>>>>>>> main
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