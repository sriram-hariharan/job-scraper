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