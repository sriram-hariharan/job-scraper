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
        logger.info("Pipeline regression check skipped (no previous run)")
        return

    logger.info("")
    logger.info("PIPELINE REGRESSION CHECK")
    logger.info("-------------------------")

    stages = ["scraped", "filtered", "deduped", "ranked", "details"]

    for stage in stages:

        prev_val = prev_run.get(stage, 0)
        curr_val = current_metrics.get(stage, 0)

        if prev_val == 0:
            logger.info(f"{stage:10} baseline unavailable")
            continue

        change = round((curr_val - prev_val) / prev_val * 100, 2)

        # massive drop
        if curr_val < prev_val * 0.4:
            logger.warning(
                f"⚠ PIPELINE DROP: {stage} dropped from {prev_val} → {curr_val} ({change}%)"
            )

        # massive spike (usually bug)
        elif curr_val > prev_val * 2.5:
            logger.warning(
                f"⚠ PIPELINE SPIKE: {stage} jumped from {prev_val} → {curr_val} ({change}%)"
            )

        else:
            logger.info(
                f"{stage:10} OK ({prev_val} → {curr_val})"
            )

    logger.info("")


def check_ats_failure(prev_counts, current_counts, logger):

    if not prev_counts:
        logger.info("ATS failure check skipped (no previous run)")
        return

    logger.info("")
    logger.info("ATS FAILURE CHECK")
    logger.info("----------------")

    for ats, prev_count in prev_counts.items():

        current_count = current_counts.get(ats, 0)

        # scraper likely broken
        if prev_count >= 10 and current_count == 0:
            logger.warning(
                f"⚠ POSSIBLE SCRAPER BREAK: {ats} dropped from {prev_count} → {current_count}"
            )

        # major drop
        elif prev_count >= 20 and current_count < prev_count * 0.25:
            logger.warning(
                f"⚠ ATS DROP DETECTED: {ats} dropped from {prev_count} → {current_count}"
            )

        else:
            logger.info(
                f"{ats:15} OK ({prev_count} → {current_count})"
            )

    logger.info("")