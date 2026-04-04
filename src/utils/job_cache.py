from pathlib import Path

CACHE_FILE = Path("data/seen_job_ids.txt")


def load_seen_job_ids():
    if not CACHE_FILE.exists():
        return set()

    with open(CACHE_FILE) as f:
        return set(line.strip() for line in f if line.strip())


def _job_cache_key(job):
    job_id = job.get("job_id") or job.get("url")
    source = job.get("source")

    if not job_id:
        return ""

    return f"{source}:{job_id}"


def cache_keys_for_jobs(jobs):
    keys = []
    for job in jobs:
        cache_key = _job_cache_key(job)
        if cache_key:
            keys.append(cache_key)
    return keys


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
        cache_key = _job_cache_key(job)

        if not cache_key:
            new_jobs.append(job)
            continue

        if cache_key in seen_ids:
            continue

        new_jobs.append(job)
        new_job_ids.append(cache_key)

    return new_jobs, new_job_ids