from pathlib import Path

CACHE_FILE = Path("data/seen_job_ids.txt")

def load_seen_job_ids():

    if not CACHE_FILE.exists():
        return set()

    with open(CACHE_FILE) as f:
        return set(line.strip() for line in f if line.strip())

def save_new_job_ids(job_ids):

    if not job_ids:
        return

    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(CACHE_FILE, "a") as f:
        for job_id in job_ids:
            f.write(job_id + "\n")

def filter_new_jobs(jobs, seen_ids):

    new_jobs = []
    new_job_ids = []

    for job in jobs:

        job_id = job.get("job_id") or job.get("url")

        if not job_id:
            new_jobs.append(job)
            continue

        cache_key = f"{job['source']}|{job_id}"

        if cache_key in seen_ids:
            continue

        new_jobs.append(job)
        new_job_ids.append(cache_key)

    return new_jobs, new_job_ids