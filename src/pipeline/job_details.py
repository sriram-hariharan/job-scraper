from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter
from tqdm import tqdm

from src.utils.logging import get_logger
from src.details.greenhouse_details import fetch_greenhouse_details

logger = get_logger("job_details")


def enrich_job_details(jobs):

    enriched_jobs = []

    def process(job):

        if job.get("source") == "greenhouse":
            return fetch_greenhouse_details(job)

        job["_details_fetched"] = "skipped"
        return job

    with ThreadPoolExecutor(max_workers=20) as executor:

        futures = [executor.submit(process, job) for job in jobs]

        for future in tqdm(
            as_completed(futures),
            total=len(futures),
            desc="Fetching job details"
        ):
            enriched_jobs.append(future.result())

    # breakdown stats
    counts = Counter(job.get("_details_fetched", "unknown") for job in enriched_jobs)

    logger.info(
        "Greenhouse detail extraction | "
        f"html={counts.get('html',0)} | "
        f"nextjs={counts.get('nextjs',0)} | "
        f"api={counts.get('api',0)} | "
        f"failed={counts.get('failed',0)} || "
        f"total={len(enriched_jobs)}"
    )

    return enriched_jobs