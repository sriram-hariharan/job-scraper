from src.utils.logging import get_logger
from src.utils.job_normalizer import normalize_company, normalize_title

logger = get_logger("dedupe")

def title_key(job):

    company = normalize_company(job.get("company", ""))
    title = normalize_title(job.get("title", ""))

    return f"{company}|{title}"


def job_identity(job):
    """
    Primary identity for fast dedupe
    """

    job_id = job.get("job_id")
    url = job.get("url")

    if job_id:
        return f"id:{job_id}"

    if url:
        return f"url:{url.strip().lower()}"

    return None


def dedupe_jobs(jobs):

    seen_ids = set()
    seen_titles = set()

    unique_jobs = []

    for job in jobs:

        # ---------- Layer 1: job_id / url ----------
        identity = job_identity(job)

        if identity and identity in seen_ids:
            continue

        if identity:
            seen_ids.add(identity)

        # ---------- Layer 2: company + title ----------
        key = title_key(job)

        if key in seen_titles:
            continue

        seen_titles.add(key)
        unique_jobs.append(job)

    logger.info(f"Jobs before dedupe: {len(jobs)}")
    logger.info(f"Jobs after dedupe: {len(unique_jobs)}")

    return unique_jobs