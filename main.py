from src.pipeline.collector import collect_all_jobs_async
from src.pipeline.excel_writer import write_jobs_to_sheet
from src.utils.logging import get_logger
from src.pipeline.discovery_stage import run_discovery
from src.storage.metrics_store import init_metrics_db
from src.ai.embedding_model import get_model
import asyncio

logger = get_logger(__name__)

async def main_async():
  
    init_metrics_db()
    
    logger.info("Loading embedding model...")
    get_model()

    # run_discovery()

    logger.info("=============================")
    logger.info("SCRAPING JOBS")
    logger.info("=============================\n")

    jobs = await collect_all_jobs_async()

    # if jobs:
    #     write_jobs_to_sheet(jobs)

    # logger.info("Final jobs: %s", len(jobs))


if __name__ == "__main__":
    asyncio.run(main_async())