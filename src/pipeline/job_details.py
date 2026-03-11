from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter
from tqdm import tqdm
import json
from src.utils.logging import get_logger
from src.details.greenhouse_details import fetch_greenhouse_details
from src.details.workday_details import fetch_workday_details

logger = get_logger("job_details")

ENRICHABLE_SOURCES = {"greenhouse", "workday"}


def enrich_job_details(jobs):

    enriched_jobs = []

    # Only send ATS that actually need enrichment into the thread pool
    jobs_to_enrich = [job for job in jobs if job.get("source") in ENRICHABLE_SOURCES]
    skipped_jobs = [job for job in jobs if job.get("source") not in ENRICHABLE_SOURCES]

    # Mark all non-enriched ATS upfront
    for job in skipped_jobs:
        job["_details_fetched"] = "skipped"

    enriched_jobs.extend(skipped_jobs)

    def process(job):
        source = job.get("source")

        if source == "greenhouse":
            return fetch_greenhouse_details(job)

        if source == "workday":
            return fetch_workday_details(job)

        job["_details_fetched"] = "skipped"
        return job

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(process, job) for job in jobs_to_enrich]

        for future in tqdm(
            as_completed(futures),
            total=len(futures),
            desc="Fetching job details"
        ):
            enriched_jobs.append(future.result())

    counts = Counter(job.get("_details_fetched", "unknown") for job in enriched_jobs)

    logger.info(
    "Job detail extraction | "
    f"company_api={counts.get('company_api', 0)} | "
    f"html={counts.get('html', 0)} | "
    f"json={counts.get('json', 0)} | "
    f"nextjs={counts.get('nextjs', 0)} | "
    f"api={counts.get('api', 0)} | "
    f"skipped={counts.get('skipped', 0)} | "
    f"failed={counts.get('failed', 0)} || "
    f"total={len(enriched_jobs)}"
    )

    return enriched_jobs