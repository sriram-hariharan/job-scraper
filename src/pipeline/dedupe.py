from src.utils.logging import get_logger
from src.utils.job_normalizer import job_fingerprint

logger = get_logger("dedupe")

def normalize(text):
    #Old implementation

    if not text:
        return ""

    # handle Workday multi-location lists
    if isinstance(text, list):
        text = " ".join(sorted(text))

    text = text.lower().strip()

    return text

def job_identity(job: dict) -> str:
    """
    Determine best identity key for a job.
    Priority:
    1. ATS job ID
    2. URL
    3. fingerprint fallback
    """

    if job.get("job_id"):
        return f"id:{job['job_id']}"

    if job.get("url"):
        return f"url:{job['url'].strip().lower()}"

    return f"fp:{job_fingerprint(job)}"

def dedupe_jobs(jobs):

    seen = set()
    unique_jobs = []

    for job in jobs:
        fingerprint = job_fingerprint(job)

        if fingerprint in seen:
            continue

        seen.add(fingerprint)
        unique_jobs.append(job)

    logger.info(f"Jobs before dedupe: {len(jobs)}")
    logger.info(f"Jobs after dedupe: {len(unique_jobs)}")
    return unique_jobs