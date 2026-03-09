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

from src.pipeline.job_filter import filter_jobs
from src.pipeline.dedupe import dedupe_jobs
    
from src.utils.logging import get_logger

logger = get_logger("collector")

def print_source_counts(title, jobs):

    logger.info(title)

    counts = Counter(job.get("source", "unknown") for job in jobs)

    for source, count in counts.items():
        logger.info(f"{source} {count}")

def collect_all_jobs() -> List[Dict[str, Any]]:

    scrapers = [
        ("workday", scrape_all_workday),
        ("greenhouse", scrape_all_greenhouse),
        ("lever", scrape_all_lever),
        ("ashby", scrape_all_ashby),
        ("workable", scrape_all_workable),
        ("jobvite", scrape_all_jobvite),
    ]

    all_jobs: List[Dict[str, Any]] = []

    start_total = time.time()

    with ThreadPoolExecutor(max_workers=max(1, min(4, len(scrapers)))) as executor:

        futures = {
            executor.submit(fn): (name, time.time())
            for name, fn in scrapers
        }

        for future in as_completed(futures):

            name, start = futures[future]
            elapsed = None

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

    logger.info(f"Total scraping time: {total_elapsed}s")
    logger.info(f"Total raw jobs collected: {len(all_jobs)}")
    
    # ----- DEBUG BEFORE FILTERING -----

    print_source_counts("Raw jobs by source:", all_jobs)

    # ----- FILTER -----

    filtered_jobs = filter_jobs(all_jobs)
    
    logger.info("Jobs missing posted_at in the entire raw dataset:")
    missing = Counter(job["source"] for job in all_jobs if not job.get("posted_at"))
    for source, count in missing.items():
        logger.info(f"{source} {count}")

    logger.info(f"Total filtered jobs: {len(filtered_jobs)}")

    print_source_counts("Filtered jobs by source:", filtered_jobs)

    deduped_jobs = dedupe_jobs(filtered_jobs)

    logger.info(f"Total deduped jobs: {len(deduped_jobs)}")

    return deduped_jobs