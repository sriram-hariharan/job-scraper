import argparse
import asyncio
import os
import subprocess
import sys
from pathlib import Path
from src.pipeline.collector import collect_all_jobs_async
from src.pipeline.excel_writer import write_jobs_to_sheet
from src.utils.logging import get_logger
from src.pipeline.discovery_stage import run_discovery
from src.storage.metrics_store import init_metrics_db
from src.ai.embedding_model import get_model

logger = get_logger(__name__)

def _parse_args():
    parser = argparse.ArgumentParser(
        description="Run the main scraping pipeline and optionally trigger downstream application planning."
    )
    parser.add_argument(
        "--run-application-planning",
        action="store_true",
        help="After the main pipeline finishes and exports the job corpus, run application planning as a downstream step.",
    )
    parser.add_argument(
        "--application-planning-job-limit",
        type=int,
        default=50,
        help="Job limit to pass to run_application_planning.py.",
    )
    parser.add_argument(
        "--application-planning-job-packet-limit",
        type=int,
        default=0,
        help="Packet limit to pass to run_application_planning.py. Use 0 for all selected rows.",
    )
    parser.add_argument(
        "--application-planning-output-dir",
        default="outputs/application_planning",
        help="Output directory to pass to run_application_planning.py.",
    )
    parser.add_argument(
        "--application-planning-generate-tailoring",
        action="store_true",
        help="Pass --generate-tailoring to run_application_planning.py.",
    )
    parser.add_argument(
        "--application-planning-generate-llm-tailoring",
        action="store_true",
        help="Pass --generate-llm-tailoring to run_application_planning.py.",
    )
    parser.add_argument(
        "--application-planning-refresh-llm-tailoring",
        action="store_true",
        help="Pass --refresh-llm-tailoring to run_application_planning.py.",
    )
    parser.add_argument(
        "--application-planning-llm-actions",
        default="APPLY,APPLY_REVIEW_VARIANTS",
        help="Comma-separated shortlist actions eligible for live LLM tailoring in run_application_planning.py.",
    )
    parser.add_argument(
        "--application-planning-only",
        action="store_true",
        help="Skip scraping and run downstream application planning only, using the existing exported job corpus.",
    )
    return parser.parse_args()


def _run_cmd(cmd):
    logger.info("")
    logger.info("RUNNING: %s", " ".join(cmd))
    logger.info("")
    subprocess.run(cmd, check=True)


def _run_application_planning(args):
    cmd = [
        sys.executable,
        "run_application_planning.py",
        "--job-corpus",
        "data/rag/job_corpus.jsonl",
        "--job-limit",
        str(args.application_planning_job_limit),
        "--job-packet-limit",
        str(args.application_planning_job_packet_limit),
        "--output-dir",
        args.application_planning_output_dir,
        "--llm-tailoring-actions",
        args.application_planning_llm_actions,
    ]

    if args.application_planning_generate_tailoring:
        cmd.append("--generate-tailoring")

    if args.application_planning_generate_llm_tailoring:
        cmd.append("--generate-llm-tailoring")

    if args.application_planning_refresh_llm_tailoring:
        cmd.append("--refresh-llm-tailoring")

    _run_cmd(cmd)

def _corpus_has_job_records(path: str) -> bool:
    corpus_path = Path(path)
    if not corpus_path.exists():
        return False

    with corpus_path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                return True

    return False

def _validate_application_planning_only_args(args) -> None:
    if args.application_planning_only and not args.run_application_planning:
        raise SystemExit(
            "--application-planning-only requires --run-application-planning."
        )
    
async def main_async(args):

    # ----- Delete seen data? -----

    DELETE_SEEN_DATA = None

    while DELETE_SEEN_DATA not in ["y", "n", "yes", "no"]:
        DELETE_SEEN_DATA = input("Delete seen data? (y/n): ").strip().lower()

    if DELETE_SEEN_DATA in ["y", "yes"]:

        seen_file = os.path.join(os.getcwd(), "data", "seen_job_ids.txt")

        if os.path.exists(seen_file):
            os.remove(seen_file)
            logger.info(f"Deleted seen data: {seen_file}")
        else:
            logger.info(f"Seen file not found: {seen_file}")

    # ----- end of delete seen data -----

    init_metrics_db()

    logger.info("Loading embedding model...")
    get_model()

    # run_discovery()

    jobs = []

    if args.application_planning_only:
        logger.info("=============================")
        logger.info("APPLICATION PLANNING ONLY MODE")
        logger.info("=============================\n")
    else:
        logger.info("=============================")
        logger.info("SCRAPING JOBS")
        logger.info("=============================\n")
        jobs = await collect_all_jobs_async()

    if args.run_application_planning:
        logger.info("")
        logger.info("=============================")
        logger.info("APPLICATION PLANNING")
        logger.info("=============================")

        corpus_path = "data/rag/job_corpus.jsonl"
        if _corpus_has_job_records(corpus_path):
            _run_application_planning(args)
        else:
            logger.warning(
                "Skipping application planning because the job corpus is missing or empty: %s",
                corpus_path,
            )

    # if jobs:
    #     write_jobs_to_sheet(jobs)

    # logger.info("Final jobs: %s", len(jobs))


if __name__ == "__main__":
    args = _parse_args()
    _validate_application_planning_only_args(args)
    asyncio.run(main_async(args))