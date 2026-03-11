from src.utils.logging import get_logger

logger = get_logger("job_details")

def enrich_job_details(jobs):

    enriched_jobs = []

    for job in jobs:

        # placeholder — real logic comes next
        job["_details_fetched"] = False
        enriched_jobs.append(job)

    return enriched_jobs