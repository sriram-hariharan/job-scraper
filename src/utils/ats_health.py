from collections import Counter
from src.utils.logging import get_logger

logger = get_logger("ats_health")

def check_ats_health(jobs):

    source_counts = Counter(job.get("source", "unknown") for job in jobs)

    logger.info("")
    logger.info("ATS HEALTH CHECK")

    for source, count in source_counts.items():
        logger.info(f"{source:15} {count}")

        if count == 0:
            logger.warning(f"ATS WARNING: {source} returned 0 jobs")

    logger.info("")


def check_pipeline_regression(prev_run, current_metrics, logger):

    if not prev_run:
        logger.info("First run — no historical metrics to compare")
        return

    issues_found = False

    logger.info("")
    logger.info("PIPELINE HEALTH CHECK")
    logger.info("---------------------")

    if current_metrics["drop_pct"] - prev_run["drop_pct"] > 5:
        logger.warning(
            f"Filter drop increased {prev_run['drop_pct']}% → {current_metrics['drop_pct']}%"
        )
        issues_found = True

    if current_metrics["scraped"] < prev_run["scraped"] * 0.5:
        logger.warning(
            f"Scraped jobs dropped {prev_run['scraped']} → {current_metrics['scraped']}"
        )
        issues_found = True

    if current_metrics["filtered"] < prev_run["filtered"] * 0.5:
        logger.warning(
            f"Filtered jobs dropped {prev_run['filtered']} → {current_metrics['filtered']}"
        )
        issues_found = True

    if not issues_found:
        logger.info("Pipeline health OK — no regressions detected")

    logger.info("")