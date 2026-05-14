from collections import Counter
from typing import Any, Dict, List
import asyncio
import os
import time
from uuid import uuid4
from pathlib import Path

from src.pipeline.runtime_status import complete_stage, start_stage
from src.utils.log_sections import section
from src.utils.logging import get_logger

logger = get_logger("collector")


def _is_user_pipeline_mode() -> bool:
    return str(os.environ.get("JOB_STACK_USER_PIPELINE_MODE", "") or "").strip().lower() in {
        "1",
        "true",
        "yes",
        "y",
    }


def log_market_insights(jobs: List[Dict[str, Any]]) -> None:
    from src.intelligence.market_insights import (
        detect_ai_hiring_surges,
        detect_emerging_tech,
        detect_hot_companies,
    )

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
    from src.ai.job_fit_evaluator import evaluate_jobs, get_eval_cache_metrics
    from src.ai.llm_client import get_provider_metrics, reset_provider_metrics
    from src.ai.resume_matcher import match_resumes
    from src.ai.skill_llm_enricher import (
        get_skill_cache_metrics,
        reset_skill_cache_metrics,
    )
    from src.discovery.domain_learner import learn_domains_from_jobs
    from src.discovery.persist_discovered import persist_discovered_companies
    from src.intelligence.job_intelligence import (
        build_job_intelligence,
        filter_jobs_for_ai_evaluation,
    )
    from src.intelligence.skill_discovery import discover_new_skills
    from src.intelligence.skill_frequency import top_skills
    from src.pipeline.application_scorer import score_jobs
    from src.pipeline.dedupe import dedupe_jobs
    from src.pipeline.embedding_prefilter import prefilter_jobs_by_embedding
    from src.pipeline.job_details import enrich_job_details
    from src.pipeline.job_filter import filter_jobs
    from src.pipeline.job_ranker import rank_jobs
    from src.rag.export_job_corpus import export_job_corpus
    from src.scrapers.ashby_scraper import scrape_all_ashby
    from src.scrapers.greenhouse_scraper import scrape_all_greenhouse
    from src.scrapers.jobvite_scraper import scrape_all_jobvite
    from src.scrapers.lever_scraper import scrape_all_lever
    from src.scrapers.smartrecruiters_scraper import scrape_all_smartrecruiters
    from src.scrapers.workable_scraper import scrape_all_workable
    from src.scrapers.workday_scraper import scrape_all_workday
    from src.storage.metrics_store import (
        get_hiring_momentum,
        get_last_ats_counts,
        get_last_run,
        record_ats_counts,
        record_company_hiring,
        record_pipeline_run,
    )
    from src.storage.skill_corpus_store import get_top_corpus_skills, store_job_skills
    from src.utils.ats_health import (
        check_ats_failure,
        check_ats_health,
        check_pipeline_regression,
    )
    from src.utils.job_cache import (
        cache_keys_for_jobs,
        filter_new_jobs,
        load_seen_job_ids,
        save_new_job_ids,
    )
    from src.utils.pipeline_metrics import log_stage_metrics

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
        logger.info("[collector] %s starting", name)
        try:
            jobs = await loop.run_in_executor(None, fn)
            elapsed = round(time.time() - start, 2)
            return name, jobs, elapsed, None
        except Exception as exc:
            elapsed = round(time.time() - start, 2)
            return name, [], elapsed, exc

    start_stage("scraping", "Running ATS scrapers")
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
    complete_stage("scraping", counts={"scraped_jobs": len(all_jobs)})

    learn_domains_from_jobs(all_jobs)
    check_ats_health(all_jobs)

    section("FILTER PIPELINE", logger)
    start_stage("filtering", f"Filtering {len(all_jobs)} scraped jobs")

    filtered_jobs = filter_jobs(all_jobs)
    logger.info(f"Total filtered jobs: {len(filtered_jobs)}")

    filtered_counts = log_stage_metrics("FILTERED", filtered_jobs)

    drop_pct = 0
    if all_jobs:
        drop_pct = round((1 - len(filtered_jobs) / len(all_jobs)) * 100, 2)

    logger.info(f"Filter drop rate: {drop_pct}%")
    complete_stage("filtering", counts={"filtered_jobs": len(filtered_jobs)})

    section("DEDUPLICATION", logger)
    start_stage("dedupe", f"Deduplicating {len(filtered_jobs)} filtered jobs")

    deduped_jobs = dedupe_jobs(filtered_jobs)
    log_company_hiring(deduped_jobs, logger)

    deduped_counts = log_stage_metrics("DEDUPED", deduped_jobs)
    complete_stage("dedupe", counts={"deduped_jobs": len(deduped_jobs)})

    section("RANKING", logger)
    start_stage("ranking", f"Ranking {len(deduped_jobs)} deduped jobs")

    ranked_jobs = rank_jobs(deduped_jobs)
    log_stage_metrics("RANKED", ranked_jobs)
    complete_stage("ranking", counts={"ranked_jobs": len(ranked_jobs)})

    section("CACHE FILTER", logger)
    start_stage("cache_filter", f"Filtering cached jobs from {len(ranked_jobs)} ranked jobs")

    new_jobs, new_job_ids = filter_new_jobs(ranked_jobs, seen_job_ids)
    logger.info(f"New jobs after cache filtering: {len(new_jobs)}")
    complete_stage("cache_filter", counts={"new_jobs": len(new_jobs)})

    section("JOB DETAILS", logger)
    start_stage("details", f"Enriching details for {len(new_jobs)} new jobs")

    detailed_jobs = enrich_job_details(new_jobs)
    details_counts = log_stage_metrics("DETAILS", detailed_jobs)
    complete_stage("details", counts={"detailed_jobs": len(detailed_jobs)})

    section("JOB INTELLIGENCE", logger)
    start_stage("intelligence", f"Building intelligence for {len(detailed_jobs)} detailed jobs")

    reset_provider_metrics()
    reset_skill_cache_metrics()

    intelligent_jobs = [build_job_intelligence(job) for job in detailed_jobs]
    logger.info(f"Intelligence extracted for {len(intelligent_jobs)} jobs")
    complete_stage("intelligence", counts={"intelligent_jobs": len(intelligent_jobs)})

    skill_cache_summary = get_skill_cache_metrics()
    logger.info(
        "SKILL CACHE SUMMARY | hits=%s | misses=%s | stores=%s | cache_only_skips=%s | live_failures=%s",
        skill_cache_summary["cache_hits"],
        skill_cache_summary["cache_misses"],
        skill_cache_summary["cache_stores"],
        skill_cache_summary["cache_only_skips"],
        skill_cache_summary["live_failures"],
    )

    skill_run_id = str(uuid4())
    store_job_skills(skill_run_id, intelligent_jobs)

    logger.info("")
    logger.info("TOP EXTRACTED SKILLS")
    logger.info("--------------------")

    for skill, count in top_skills(intelligent_jobs, top_n=50):
        logger.info(f"{count:3} | {skill}")

    for skill, count in get_top_corpus_skills(limit=100):
        logger.info(f"{count:3} | {skill}")

    section("SKILL DISCOVERY", logger)
    new_skills = discover_new_skills(intelligent_jobs)

    if new_skills:
        logger.info(f"New skills discovered: {len(new_skills)}")
        logger.info(", ".join(new_skills[:10]))

    section("AI EVALUATION FILTER", logger)
    start_stage("ai_evaluation_filter", "Selecting jobs eligible for AI evaluation")

    evaluable_jobs = filter_jobs_for_ai_evaluation(intelligent_jobs)
    logger.info(f"Jobs eligible for AI evaluation: {len(evaluable_jobs)}")
    complete_stage("ai_evaluation_filter", counts={"evaluable_jobs": len(evaluable_jobs)})

    section("EMBEDDING PREFILTER", logger)
    start_stage("embedding_prefilter", f"Embedding-prefiltering {len(evaluable_jobs)} evaluable jobs")

    prefilter_input_count = len(evaluable_jobs)
    evaluable_jobs = prefilter_jobs_by_embedding(
        evaluable_jobs,
        top_n=None,
    )
    prefilter_output_count = len(evaluable_jobs)

    logger.info(
        f"Embedding prefilter reduced AI candidates: "
        f"{prefilter_input_count} -> {prefilter_output_count}"
    )

    if prefilter_input_count:
        reduction_pct = round(
            (1 - prefilter_output_count / prefilter_input_count) * 100,
            2,
        )
        logger.info(f"AI candidate reduction rate: {reduction_pct}%")

    complete_stage("embedding_prefilter", counts={"prefilter_jobs": len(evaluable_jobs)})

    section("AI JOB EVALUATION", logger)
    start_stage("ai_evaluation", f"Evaluating {len(evaluable_jobs)} jobs with AI")

    ai_jobs = evaluate_jobs(evaluable_jobs)
    logger.info(f"AI evaluated {len(ai_jobs)} jobs")
    complete_stage("ai_evaluation", counts={"ai_jobs": len(ai_jobs)})

    provider_summary = get_provider_metrics()
    logger.info(
        "LLM PROVIDER SUMMARY | primary_attempts=%s | fallback_attempts=%s | groq_calls=%s | gemini_calls=%s | fallback_successes=%s | provider_failures=%s",
        provider_summary["primary_attempts"],
        provider_summary["fallback_attempts"],
        provider_summary["groq_calls"],
        provider_summary["gemini_calls"],
        provider_summary["fallback_successes"],
        provider_summary["provider_failures"],
    )

    eval_cache_summary = get_eval_cache_metrics()
    logger.info(
        "EVAL CACHE SUMMARY | hits=%s | misses=%s | stores=%s | cache_only_skips=%s | live_failures=%s",
        eval_cache_summary["eval_cache_hits"],
        eval_cache_summary["eval_cache_misses"],
        eval_cache_summary["eval_cache_stores"],
        eval_cache_summary["eval_cache_only_skips"],
        eval_cache_summary["eval_live_failures"],
    )

    section("EMBEDDING RESUME PRIOR", logger)

    if _is_user_pipeline_mode():
        start_stage(
            "resume_matching",
            "Skipping legacy filesystem resume prior for user pipeline run",
        )
        for job in ai_jobs:
            job.setdefault("embedding_resume_prior", None)
            job.setdefault("embedding_resume_prior_score", None)
        logger.info(
            "Skipping legacy filesystem resume matching for user pipeline run; "
            "profile resumes are stored in Postgres."
        )
        complete_stage(
            "resume_matching",
            counts={
                "resume_matched_jobs": 0,
                "skipped_legacy_resume_dir": True,
                "ai_jobs": len(ai_jobs),
            },
        )
    else:
        start_stage(
            "resume_matching",
            f"Computing embedding resume prior for {len(ai_jobs)} AI-evaluated jobs",
        )

        ai_jobs = match_resumes(ai_jobs)
        logger.info("Embedding resume prior completed")
        complete_stage("resume_matching", counts={"resume_matched_jobs": len(ai_jobs)})

    section("APPLICATION PRIORITY", logger)
    start_stage("application_priority", f"Scoring {len(ai_jobs)} jobs for application priority")

    scored_jobs = score_jobs(ai_jobs)
    logger.info(f"Priority scoring completed for {len(scored_jobs)} jobs")
    complete_stage("application_priority", counts={"scored_jobs": len(scored_jobs)})

    corpus_path = str(
        os.environ.get("JOB_STACK_JOB_CORPUS_PATH", "")
        or "data/rag/job_corpus.jsonl"
    ).strip()
    corpus_file = Path(corpus_path)

    start_stage("rag_export", f"Exporting {len(scored_jobs)} jobs to RAG corpus")

    if scored_jobs:
        rag_export_count = export_job_corpus(
            scored_jobs,
            corpus_path,
        )
        logger.info(f"RAG corpus exported: {rag_export_count} documents")
    else:
        if corpus_file.exists() and corpus_file.stat().st_size > 0:
            rag_export_count = 0
            logger.info(
                "RAG export skipped because scored_jobs is empty; preserving existing corpus at %s",
                corpus_path,
            )
        else:
            rag_export_count = export_job_corpus(
                scored_jobs,
                corpus_path,
            )
            logger.info(f"RAG corpus exported: {rag_export_count} documents")

    complete_stage("rag_export", counts={"rag_export_count": rag_export_count})

    log_market_insights(detailed_jobs)

    save_new_job_ids(cache_keys_for_jobs(scored_jobs))
    persist_discovered_companies()

    pipeline_runtime = round(time.time() - start_total, 2)
    logger.info(f"Total pipeline runtime: {pipeline_runtime}s")

    current_metrics = {
        "scraped": len(all_jobs),
        "filtered": len(filtered_jobs),
        "deduped": len(deduped_jobs),
        "ranked": len(ranked_jobs),
        "details": len(detailed_jobs),
        "drop_pct": drop_pct,
    }

    if _is_user_pipeline_mode():
        section("PIPELINE HEALTH", logger)
        logger.info(
            "Skipping global pipeline metrics store for user pipeline run. "
            "User run status is persisted in user_pipeline_runs."
        )
    else:
        prev_run = get_last_run()
        prev_ats_counts = get_last_ats_counts("SCRAPED")

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
        record_ats_counts(run_id, "RANKED", log_stage_metrics("RANKED", ranked_jobs))
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