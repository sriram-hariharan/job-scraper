from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter
from tqdm import tqdm
from src.utils.logging import get_logger
from src.details.ashby_details import fetch_ashby_details
from src.details.greenhouse_details import fetch_greenhouse_details
from src.details.jobvite_details import fetch_jobvite_details
from src.details.lever_details import fetch_lever_details
from src.details.smartrecruiters_details import fetch_smartrecruiters_details
from src.details.workable_details import fetch_workable_details
from src.details.workday_details import fetch_workday_details
from src.cache.description_cache import (
    init_cache,
    get_description,
    save_description
)

from models.description import Description

logger = get_logger("job_details")

ENRICHABLE_SOURCES = {
    "ashby",
    "greenhouse",
    "jobvite",
    "lever",
    "smartrecruiters",
    "workable",
    "workday",
}

def process_job(job):

    source = job.get("source")
    job_id = job.get("job_id")

    cache_key = f"{source}:{job_id}"

    # -------------------------
    # 1️⃣ Check cache
    # -------------------------

    cached = get_description(cache_key)

    if cached:
        job["description_html"] = cached.html
        job["description_text"] = cached.text
        job["_details_fetched"] = "cache"
        return job

    # -------------------------
    # 2️⃣ Fetch from ATS
    # -------------------------

    if source == "greenhouse":
        job = fetch_greenhouse_details(job)

    elif source == "workday":
        job = fetch_workday_details(job)

    elif source == "ashby":
        job = fetch_ashby_details(job)

    elif source == "lever":
        job = fetch_lever_details(job)

    elif source == "workable":
        job = fetch_workable_details(job)

    elif source == "jobvite":
        job = fetch_jobvite_details(job)

    elif source == "smartrecruiters":
        job = fetch_smartrecruiters_details(job)

    else:
        job["_details_fetched"] = "skipped"
        return job

    # -------------------------
    # 3️⃣ Save to cache
    # -------------------------

    if job.get("description_text"):
        logger.info(f"Caching description for {job_id}")
        save_description(
            Description(
                job_id=cache_key,
                html=job.get("description_html"),
                text=job.get("description_text")
            )
        )

    return job

def enrich_job_details(jobs):
    
    init_cache()
    enriched_jobs = []

    # Only send ATS that actually need enrichment into the thread pool
    jobs_to_enrich = [job for job in jobs if job.get("source") in ENRICHABLE_SOURCES]
    skipped_jobs = [job for job in jobs if job.get("source") not in ENRICHABLE_SOURCES]

    # Mark all non-enriched ATS upfront
    for job in skipped_jobs:
        job["_details_fetched"] = "skipped"

    enriched_jobs.extend(skipped_jobs)

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(process_job, job) for job in jobs_to_enrich]

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
    f"cache={counts.get('cache', 0)} | "
    f"json={counts.get('json', 0)} | "
    f"nextjs={counts.get('nextjs', 0)} | "
    f"api={counts.get('api', 0)} | "
    f"ashby_api={counts.get('ashby_api', 0)} | "
    f"ashby_no_description={counts.get('ashby_no_description', 0)} | "
    f"ashby_request_failed={counts.get('ashby_request_failed', 0)} | "
    f"ashby_parse_failed={counts.get('ashby_parse_failed', 0)} | "
    f"lever_api={counts.get('lever_api', 0)} | "
    f"lever_no_description={counts.get('lever_no_description', 0)} | "
    f"lever_request_failed={counts.get('lever_request_failed', 0)} | "
    f"workable_api={counts.get('workable_api', 0)} | "
    f"workable_no_description={counts.get('workable_no_description', 0)} | "
    f"workable_request_failed={counts.get('workable_request_failed', 0)} | "
    f"jobvite_html={counts.get('jobvite_html', 0)} | "
    f"jobvite_no_description={counts.get('jobvite_no_description', 0)} | "
    f"jobvite_request_failed={counts.get('jobvite_request_failed', 0)} | "
    f"smartrecruiters_api={counts.get('smartrecruiters_api', 0)} | "
    f"smartrecruiters_no_description={counts.get('smartrecruiters_no_description', 0)} | "
    f"smartrecruiters_request_failed={counts.get('smartrecruiters_request_failed', 0)} | "
    f"skipped={counts.get('skipped', 0)} | "
    f"failed={counts.get('failed', 0)} || "
    f"total={len(enriched_jobs)}"
    )

    return enriched_jobs
