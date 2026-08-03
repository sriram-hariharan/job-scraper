from collections import Counter
from src.utils.logging import get_logger

logger = get_logger("ats_health")

_HEALTH_PRIORITY = {
    "unknown": 0,
    "healthy": 1,
    "degraded": 2,
    "unhealthy": 3,
}


def enforce_source_health(source_metrics, logger=logger):
    """Report truthful acquisition health without disabling or mutating a source."""
    enforced = {}
    for metric in source_metrics or ():
        if not getattr(metric, "company", ""):
            continue
        source = str(getattr(metric, "source", "") or "unknown")
        status = str(getattr(metric, "acquisition_status", "") or "")
        health = str(getattr(metric, "health", "unknown") or "unknown")
        if status == "FAILED":
            health = "unhealthy"
        elif status == "PARTIAL" and health == "healthy":
            health = "degraded"
        previous = enforced.get(source, "unknown")
        if _HEALTH_PRIORITY.get(health, 0) > _HEALTH_PRIORITY.get(previous, 0):
            enforced[source] = health
        log = logger.warning if health in {"degraded", "unhealthy"} else logger.info
        log(
            "source_health_event event=classified source=%s company=%s "
            "status=%s health=%s",
            source,
            getattr(metric, "company", ""),
            status,
            health,
        )
    return dict(sorted(enforced.items()))

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
