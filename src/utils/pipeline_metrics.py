from collections import Counter
from src.utils.logging import get_logger

logger = get_logger("metrics")

def log_stage_metrics(stage_name, jobs):

    counts = Counter(job.get("source", "unknown") for job in jobs)

    logger.info("")
    logger.info(f"PIPELINE METRICS — {stage_name}")

    for source, count in sorted(counts.items()):
        logger.info(f"{source:15} {count}")

    logger.info(f"TOTAL: {len(jobs)}")
    logger.info("")

    return counts