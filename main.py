from src.pipeline.collector import collect_all_jobs
from src.pipeline.excel_writer import write_jobs_to_sheet
from src.utils.logging import get_logger
logger = get_logger(__name__)

def main():

    logger = get_logger(__name__)

    logger.info("=============================")
    logger.info("ATS DISCOVERY")
    logger.info("=============================\n")

    # greenhouse, ashby, lever, workday = discover_from_domains()

    logger.info("=============================")
    logger.info("SCRAPING JOBS")
    logger.info("=============================\n")

    jobs = collect_all_jobs()

    if jobs:
        write_jobs_to_sheet(jobs)

    logger.info("Final jobs: %s", len(jobs))

if __name__ == "__main__":
    main()