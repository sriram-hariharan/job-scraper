from typing import List, Dict, Any
import asyncio
import time
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
from src.intelligence.job_intelligence import build_job_intelligence, filter_jobs_for_ai_evaluation
from src.pipeline.application_scorer import score_jobs

from src.ai.job_fit_evaluator import evaluate_jobs
from src.ai.resume_matcher import match_resumes

from src.utils.job_cache import load_seen_job_ids, save_new_job_ids, filter_new_jobs
from src.utils.pipeline_metrics import log_stage_metrics
from src.utils.ats_health import (
    check_ats_health,
    check_pipeline_regression,
    check_ats_failure,
)

from src.discovery.persist_discovered import persist_discovered_companies
from src.discovery.domain_learner import learn_domains_from_jobs

from src.storage.metrics_store import (
    record_pipeline_run,
    record_ats_counts,
    get_last_run,
    get_last_ats_counts,
    record_company_hiring,
    get_hiring_momentum,
)
from src.intelligence.market_insights import (
    detect_hot_companies,
    detect_ai_hiring_surges,
    detect_emerging_tech,
)
from src.intelligence.skill_discovery import discover_new_skills
from src.utils.log_sections import section
from src.utils.logging import get_logger

logger = get_logger("collector")


def log_market_insights(jobs: List[Dict[str, Any]]) -> None:
    section("JOB MARKET INSIGHTS", logger)

    hot_companies = detect_hot_companies(jobs)

    logger.info("")
    logger.info("HOT COMPANIES")
    logger.info("-------------")

    for company, count in hot_companies:
        logger.info(f"{company:25} {count}")

    ai_surges = detect_ai_hiring_surges(jobs)

    logger.info("")
    logger.info("AI HIRING SURGES")
    logger.info("----------------")

    for company, count in ai_surges:
        logger.info(f"{company:25} {count}")

    emerging_tech = detect_emerging_tech(jobs)

    logger.info("")
    logger.info("EMERGING TECH STACK")
    logger.info("-------------------")

    for tech, count in emerging_tech:
        logger.info(f"{tech:20} {count}")


def log_company_hiring(jobs: List[Dict[str, Any]], logger) -> None:
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


async def collect_all_jobs_async() -> List[Dict[str, Any]]:
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
    loop = asyncio.get_running_loop()

    async def run_scraper(name: str, fn):
        start = time.time()
        try:
            jobs = await loop.run_in_executor(None, fn)
            elapsed = round(time.time() - start, 2)
            return name, jobs, elapsed, None
        except Exception as e:
            elapsed = round(time.time() - start, 2)
            return name, [], elapsed, e

    tasks = [
        asyncio.create_task(run_scraper(name, fn))
        for name, fn in scrapers
    ]

    for task in asyncio.as_completed(tasks):
        name, jobs, elapsed, err = await task

        if err:
            logger.error(
                f"[collector] {name} failed | time={elapsed}s | error={err}"
            )
            continue

        logger.info(
            f"[collector] {name} finished | jobs={len(jobs)} | time={elapsed}s"
        )

        if jobs:
            all_jobs.extend(jobs)

    section("SCRAPER RESULTS", logger)

    total_elapsed = round(time.time() - start_total, 2)
    logger.info(f"Total scraping time: {total_elapsed}s")

    scraped_counts = log_stage_metrics("SCRAPED", all_jobs)

    # ---- DOMAIN LEARNING ----
    learn_domains_from_jobs(all_jobs)

    # ---- ATS HEALTH CHECK ----
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

    # ----- RANKING -----
    section("RANKING", logger)

    ranked_jobs = rank_jobs(deduped_jobs)
    ranked_counts = log_stage_metrics("RANKED", ranked_jobs)

    # ----- CACHE FILTER -----
    section("CACHE FILTER", logger)

    new_jobs, new_job_ids = filter_new_jobs(ranked_jobs, seen_job_ids)
    logger.info(f"New jobs after cache filtering: {len(new_jobs)}")

    # ----- JOB DETAIL ENRICHMENT -----
    section("JOB DETAILS", logger)

    detailed_jobs = enrich_job_details(new_jobs)
    details_counts = log_stage_metrics("DETAILS", detailed_jobs)
    # logger.info("DETAIL SAMPLE: %s", detailed_jobs[0])

    # ----- SKILL DISCOVERY -----
    section("SKILL DISCOVERY", logger)

    new_skills = discover_new_skills(detailed_jobs)

    if new_skills:
        logger.info(f"New skills discovered: {len(new_skills)}")
        logger.info(", ".join(new_skills[:10]))

    # ----- JOB INTELLIGENCE -----
    section("JOB INTELLIGENCE", logger)

    intelligent_jobs = [build_job_intelligence(job) for job in detailed_jobs]
    logger.info(f"Intelligence extracted for {len(intelligent_jobs)} jobs")

    # ----- AI EVALUATION FILTER -----
    evaluable_jobs = filter_jobs_for_ai_evaluation(intelligent_jobs)

    # ----- AI JOB EVALUATION -----
    MAX_EVAL_JOBS = 40
    evaluable_jobs = evaluable_jobs[:MAX_EVAL_JOBS]

    section("AI JOB EVALUATION", logger)

    ai_jobs = evaluate_jobs(evaluable_jobs)
    logger.info(f"AI evaluated {len(ai_jobs)} jobs")

    # ----- RESUME MATCHING -----

    section("RESUME MATCHING", logger)
    ai_jobs = match_resumes(ai_jobs)
    logger.info("Resume matching completed")

    # --- DEBUG START ---
    for job in ai_jobs[:10]:
        logger.info(
            "RESUME MATCH | %s | %s | %.4f",
            job.get("title"),
            job.get("best_resume"),
            job.get("resume_match_score") or -1
        )
    # --- DEBUG END ---
    
    # ----- APPLICATION PRIORITY -----
    section("APPLICATION PRIORITY", logger)

    scored_jobs = score_jobs(ai_jobs)
    logger.info(f"Priority scoring completed for {len(scored_jobs)} jobs")

    # ----- JOB MARKET INSIGHTS -----
    log_market_insights(detailed_jobs)

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
        "drop_pct": drop_pct,
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
        drop_pct=drop_pct,
    )

    record_company_hiring(run_id, deduped_jobs)

    record_ats_counts(run_id, "SCRAPED", scraped_counts)
    record_ats_counts(run_id, "FILTERED", filtered_counts)
    record_ats_counts(run_id, "DEDUPED", deduped_counts)
    record_ats_counts(run_id, "RANKED", ranked_counts)
    record_ats_counts(run_id, "DETAILS", details_counts)

    logger.info("Pipeline metrics stored")

    momentum = get_hiring_momentum()

    if momentum:
        logger.info("")
        logger.info("HIRING MOMENTUM")
        logger.info("----------------")

        for company, ats, prev, curr, delta in momentum[:10]:
            logger.info(f"{company:25} {ats:12} {prev} → {curr}  (+{delta})")

    return scored_jobs