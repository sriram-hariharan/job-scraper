from typing import List, Dict, Any
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter

from src.scrapers.workday_scraper import scrape_all_workday
from src.scrapers.greenhouse_scraper import scrape_all_greenhouse
from src.scrapers.lever_scraper import scrape_all_lever
from src.scrapers.ashby_scraper import scrape_all_ashby
from src.scrapers.workable_scraper import scrape_all_workable
from src.scrapers.jobvite_scraper import scrape_all_jobvite
from src.scrapers.smartrecruiters_scraper import scrape_all_smartrecruiters

from src.pipeline.job_filter import filter_jobs
from src.pipeline.dedupe import dedupe_jobs
from src.utils.job_cache import load_seen_job_ids, save_new_job_ids, filter_new_jobs
from src.utils.logging import get_logger
from src.discovery.persist_discovered import persist_discovered_companies
from src.utils.log_sections import section

logger = get_logger("collector")

def collect_all_jobs() -> List[Dict[str, Any]]:

    scrapers = [
        ("workday", scrape_all_workday),
        ("greenhouse", scrape_all_greenhouse),
        ("lever", scrape_all_lever),
        ("ashby", scrape_all_ashby),
        ("workable", scrape_all_workable),
        ("jobvite", scrape_all_jobvite),
        ("smartrecruiters", scrape_all_smartrecruiters),
    ]

    all_jobs: List[Dict[str, Any]] = []
    seen_job_ids = load_seen_job_ids()
    logger.info(f"Loaded {len(seen_job_ids)} cached job IDs")

    start_total = time.time()

    with ThreadPoolExecutor(max_workers=max(1, len(scrapers))) as executor:

        futures = {
            executor.submit(fn): (name, time.time())
            for name, fn in scrapers
        }

        for future in as_completed(futures):
            name, start = futures[future]

            try:
                jobs = future.result()
                elapsed = round(time.time() - start, 2)

                logger.info(f"[collector] {name} finished | jobs={len(jobs)} | time={elapsed}s")

                if jobs:
                    all_jobs.extend(jobs)

            except Exception as e:
                elapsed = round(time.time() - start, 2)
                logger.error(f"[collector] {name} failed | time={elapsed}s | error={e}")

    total_elapsed = round(time.time() - start_total, 2)

    section("SCRAPER RESULTS", logger)
    logger.info(f"Total scraping time: {total_elapsed}s")
    counts = Counter(job.get("source", "unknown") for job in all_jobs)

    for source, count in counts.items():
        logger.info(f"{source:15} {count} jobs")

    logger.info("-" * 40)
    logger.info(f"Total raw jobs: {len(all_jobs)}")

    # ----- FILTER -----
    section("FILTER PIPELINE", logger)
    filtered_jobs = filter_jobs(all_jobs)
    logger.info(f"Total filtered jobs: {len(filtered_jobs)}")
    counts = Counter(job.get("source", "unknown") for job in filtered_jobs)

    for source, count in counts.items():
        logger.info(f"{source:15} {count} jobs")

    # ----- DEDUPE -----
    section("DEDUPLICATION", logger)
    deduped_jobs = dedupe_jobs(filtered_jobs)
    logger.info(f"Jobs after dedupe: {len(deduped_jobs)}")

    # ----- CACHE FILTER -----
    section("CACHE FILTER", logger)
    new_jobs, new_job_ids = filter_new_jobs(deduped_jobs, seen_job_ids)
    logger.info(f"New jobs after cache filtering: {len(new_jobs)}")

    # ----- SAVE CACHE -----
    save_new_job_ids(new_job_ids)

    # ----- SAVE DISCOVERED COMPANIES -----
    persist_discovered_companies()

    return new_jobs