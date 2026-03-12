from typing import List, Dict, Any
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.scrapers.workday_scraper import scrape_all_workday
from src.scrapers.greenhouse_scraper import scrape_all_greenhouse
from src.scrapers.lever_scraper import scrape_all_lever
from src.scrapers.ashby_scraper import scrape_all_ashby
from src.scrapers.workable_scraper import scrape_all_workable
from src.scrapers.jobvite_scraper import scrape_all_jobvite
from src.scrapers.smartrecruiters_scraper import scrape_all_smartrecruiters
from src.pipeline.job_filter import filter_jobs
from src.pipeline.dedupe import dedupe_jobs
from src.pipeline.job_ranker import rank_jobs
from src.pipeline.job_details import enrich_job_details
from src.utils.job_cache import load_seen_job_ids, save_new_job_ids, filter_new_jobs
from src.utils.pipeline_metrics import log_stage_metrics
from src.utils.logging import get_logger
from src.discovery.persist_discovered import persist_discovered_companies
from src.utils.log_sections import section
from collections import Counter

logger = get_logger("collector")

def log_company_hiring(jobs, logger):

    company_counts = Counter()

    for job in jobs:
        company = job.get("company")
        if company:
            company_counts[company] += 1

    logger.info("")
    logger.info("COMPANY HIRING FREQUENCY")

    for company, count in company_counts.most_common(10):
        logger.info(f"{count:3} | {company}")

    logger.info("")

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
    log_stage_metrics("SCRAPED", all_jobs)

    # ----- FILTER -----
    section("FILTER PIPELINE", logger)
    filtered_jobs = filter_jobs(all_jobs)
    logger.info(f"Total filtered jobs: {len(filtered_jobs)}")
    log_stage_metrics("FILTERED", filtered_jobs)

    drop_pct = 0
    if all_jobs:
        drop_pct = round((1 - len(filtered_jobs) / len(all_jobs)) * 100, 2)
    logger.info(f"Filter drop rate: {drop_pct}%")

    # ----- DEDUPE -----
    section("DEDUPLICATION", logger)
    deduped_jobs = dedupe_jobs(filtered_jobs)
    log_company_hiring(deduped_jobs, logger)
    log_stage_metrics("DEDUPED", deduped_jobs)

    #----- RANKING -----
    section("RANKING", logger)
    ranked_jobs = rank_jobs(deduped_jobs)
    log_stage_metrics("RANKED", ranked_jobs)

    # ----- JOB DETAIL ENRICHMENT -----
    section("JOB DETAILS", logger)
    detailed_jobs = enrich_job_details(ranked_jobs)
    log_stage_metrics("DETAILS", detailed_jobs)

    # ----- CACHE FILTER -----
    section("CACHE FILTER", logger)
    new_jobs, new_job_ids = filter_new_jobs(detailed_jobs, seen_job_ids)
    logger.info(f"New jobs after cache filtering: {len(new_jobs)}")

    # ----- SAVE CACHE -----
    save_new_job_ids(new_job_ids)

    # ----- SAVE DISCOVERED COMPANIES -----
    persist_discovered_companies()

    return new_jobs