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
from src.pipeline.job_ranker import rank_jobs
from src.pipeline.job_details import enrich_job_details
from src.utils.job_cache import load_seen_job_ids, save_new_job_ids, filter_new_jobs
from src.utils.pipeline_metrics import log_stage_metrics
from src.utils.ats_health import (
    check_ats_health,
    check_pipeline_regression,
    check_ats_failure
)
from src.discovery.persist_discovered import persist_discovered_companies
from src.discovery.domain_learner import learn_domains_from_jobs
from src.utils.metrics_store import (
    init_metrics_db,
    record_pipeline_run,
    record_ats_counts,
    get_last_run,
    get_last_ats_counts
)

from src.utils.log_sections import section
from src.utils.logging import get_logger

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

    init_metrics_db()

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

    

    section("SCRAPER RESULTS", logger)
    total_elapsed = round(time.time() - start_total, 2)
    logger.info(f"Total scraping time: {total_elapsed}s")
    scraped_counts = log_stage_metrics("SCRAPED", all_jobs)

    # ---- DOMAIN LEARNING ----
    learn_domains_from_jobs(all_jobs)

    # ---- ATTS HEALTH CHECK ----
    check_ats_health(all_jobs)

    # ----- FILTER -----
    section("FILTER PIPELINE", logger)
    filtered_jobs = filter_jobs(all_jobs)
    logger.info(f"Total filtered jobs: {len(filtered_jobs)}")
    filtered_counts = log_stage_metrics("FILTERED", filtered_jobs)

    drop_pct = 0
    if all_jobs:
        drop_pct = round((1 - len(filtered_jobs) / len(all_jobs)) * 100, 2)
    logger.info(f"Filter drop rate: {drop_pct}%")

    # ----- DEDUPE -----
    section("DEDUPLICATION", logger)
    deduped_jobs = dedupe_jobs(filtered_jobs)
    log_company_hiring(deduped_jobs, logger)
    deduped_counts = log_stage_metrics("DEDUPED", deduped_jobs)

    #----- RANKING -----
    section("RANKING", logger)
    ranked_jobs = rank_jobs(deduped_jobs)
    ranked_counts = log_stage_metrics("RANKED", ranked_jobs)

    # ----- JOB DETAIL ENRICHMENT -----
    section("JOB DETAILS", logger)
    detailed_jobs = enrich_job_details(ranked_jobs)
    details_counts = log_stage_metrics("DETAILS", detailed_jobs)

    # ----- CACHE FILTER -----
    section("CACHE FILTER", logger)
    new_jobs, new_job_ids = filter_new_jobs(detailed_jobs, seen_job_ids)
    logger.info(f"New jobs after cache filtering: {len(new_jobs)}")

    # ----- SAVE CACHE -----
    save_new_job_ids(new_job_ids)

    # ----- SAVE DISCOVERED COMPANIES -----
    persist_discovered_companies()

    # ----- METRICS -----
    pipeline_runtime = round(time.time() - start_total, 2)
    logger.info(f"Total pipeline runtime: {pipeline_runtime}s")

    prev_run = get_last_run()
    prev_ats_counts = get_last_ats_counts("SCRAPED")

    current_metrics = {
        "scraped": len(all_jobs),
        "filtered": len(filtered_jobs),
        "deduped": len(deduped_jobs),
        "ranked": len(ranked_jobs),
        "details": len(detailed_jobs),
        "drop_pct": drop_pct
    }
    
    check_ats_failure(prev_ats_counts, scraped_counts, logger)

    section("PIPELINE HEALTH", logger)
    check_pipeline_regression(prev_run, current_metrics, logger)

    run_id = record_pipeline_run(
    runtime=pipeline_runtime,
    scraped=len(all_jobs),
    filtered=len(filtered_jobs),
    deduped=len(deduped_jobs),
    ranked=len(ranked_jobs),
    details=len(detailed_jobs),
    new_jobs=len(new_jobs),
    drop_pct=drop_pct
    )

    record_ats_counts(run_id, "SCRAPED", scraped_counts)
    record_ats_counts(run_id, "FILTERED", filtered_counts)
    record_ats_counts(run_id, "DEDUPED", deduped_counts)
    record_ats_counts(run_id, "RANKED", ranked_counts)
    record_ats_counts(run_id, "DETAILS", details_counts)
    logger.info("Pipeline metrics stored")

    return new_jobs