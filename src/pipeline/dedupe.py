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