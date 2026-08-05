from src.utils.logging import get_logger
from src.utils.job_normalizer import normalize_company, normalize_title

logger = get_logger("dedupe")

_SUPPLEMENTAL_SOURCE = "himalayas"

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


def _is_supplemental(job):
    return str(job.get("source") or "").strip().lower() == _SUPPLEMENTAL_SOURCE


def dedupe_jobs(jobs):

    identity_owners = {}
    title_owners = {}

    unique_jobs = []
    replacement_count = 0

    for job in jobs:

        # ---------- Layer 1: job_id / url ----------
        identity = job_identity(job)

        # ---------- Layer 2: company + title ----------
        key = title_key(job)

        duplicate_index = (
            identity_owners.get(identity)
            if identity and identity in identity_owners
            else title_owners.get(key)
        )

        if duplicate_index is not None:
            retained_job = unique_jobs[duplicate_index]
            if not (_is_supplemental(retained_job) and not _is_supplemental(job)):
                continue

            stale_identities = [
                value
                for value, owner in identity_owners.items()
                if owner == duplicate_index
            ]
            stale_titles = [
                value
                for value, owner in title_owners.items()
                if owner == duplicate_index
            ]
            for value in stale_identities:
                del identity_owners[value]
            for value in stale_titles:
                del title_owners[value]

            unique_jobs[duplicate_index] = job
            if identity:
                identity_owners[identity] = duplicate_index
            title_owners[key] = duplicate_index
            replacement_count += 1
            continue

        retained_index = len(unique_jobs)
        if identity:
            identity_owners[identity] = retained_index
        title_owners[key] = retained_index
        unique_jobs.append(job)

    logger.info(f"Jobs before dedupe: {len(jobs)}")
    logger.info(f"Jobs after dedupe: {len(unique_jobs)}")
    if replacement_count:
        logger.info(
            "Supplemental jobs replaced by higher-priority sources: %s",
            replacement_count,
        )

    return unique_jobs
