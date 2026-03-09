from src.pipeline.collector import collect_all_jobs
from src.pipeline.excel_writer import write_jobs_to_sheet
from src.utils.logging import get_logger
from src.discovery.learned_companies import save_learned
from src.pipeline.discovery_stage import run_discovery

logger = get_logger(__name__)

def main():

    run_discovery()
 
    logger.info("=============================")
    logger.info("SCRAPING JOBS")
    logger.info("=============================\n")

    jobs = collect_all_jobs()

    # save newly discovered ATS companies
    save_learned()
    
    if jobs:
        write_jobs_to_sheet(jobs)

    logger.info("Final jobs: %s", len(jobs))

if __name__ == "__main__":
    main()