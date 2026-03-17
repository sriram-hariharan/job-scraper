import argparse
import asyncio
import csv
import json
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

def _normalize_text(value: str) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _company_title_key(company: str, title: str) -> str:
    company_norm = _normalize_text(company)
    title_norm = _normalize_text(title)
    if not company_norm or not title_norm:
        return ""
    return f"{company_norm}||{title_norm}"

def _load_jobs_from_corpus(corpus_path: str):
    path = Path(corpus_path)
    if not path.exists():
        return []

    jobs = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            jobs.append(json.loads(line))

    return jobs


def _load_execution_queue_lookup(output_dir: str) -> dict:
    queue_path = Path(output_dir) / "application_execution_queue.csv"
    if not queue_path.exists():
        return {}

    with queue_path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    lookup = {}
    for row in rows:
        job_doc_id = str(row.get("job_doc_id", "") or "").strip()

        payload = {
            "job_doc_id": job_doc_id,
            "queue_rank": row.get("queue_rank", ""),
            "needs_variant_review": row.get("needs_variant_review", ""),
            "missing_requirement_count": row.get("missing_requirement_count", ""),
            "queue_priority_reason": row.get("queue_priority_reason", ""),
            "action": row.get("action", ""),
            "winner_resume": row.get("winner_resume", ""),
            "winner_score": row.get("winner_score", ""),
            "runner_up_resume": row.get("runner_up_resume", ""),
            "runner_up_score": row.get("runner_up_score", ""),
            "score_gap": row.get("score_gap", ""),
            "is_tie": row.get("is_tie", ""),
        }

        if job_doc_id:
            lookup[job_doc_id] = payload

        company_title = _company_title_key(
            row.get("job_company", ""),
            row.get("job_title", ""),
        )
        if company_title:
            lookup[company_title] = payload

    return lookup


def _load_packet_manifest_lookup(output_dir: str) -> dict:
    manifest_path = Path(output_dir) / "job_packet_manifest.csv"
    if not manifest_path.exists():
        return {}

    with manifest_path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    lookup = {}
    for row in rows:
        job_doc_id = str(row.get("job_doc_id", "") or "").strip()

        payload = {
            "job_doc_id": job_doc_id,
            "packet_json": row.get("packet_json", ""),
            "tailoring_json": row.get("tailoring_json", ""),
            "tailoring_md": row.get("tailoring_md", ""),
            "tailoring_llm_json": row.get("tailoring_llm_json", ""),
            "llm_tailoring_status": row.get("llm_tailoring_status", ""),
            "llm_error_type": row.get("llm_error_type", ""),
        }

        if job_doc_id:
            lookup[job_doc_id] = payload

        company_title = _company_title_key(
            row.get("job_company", ""),
            row.get("job_title", ""),
        )
        if company_title:
            lookup[company_title] = payload

    return lookup


def _merge_application_planning_into_jobs(
    jobs,
    execution_queue_lookup: dict,
    packet_manifest_lookup: dict,
) -> int:
    merged_count = 0

    for job in jobs:
        planning = {}

        key_candidates = [
            str(job.get("job_doc_id") or "").strip(),
            str(job.get("url") or "").strip(),
            str(job.get("link") or "").strip(),
            _company_title_key(job.get("company", ""), job.get("title", "")),
        ]

        for key in key_candidates:
            if key and key in execution_queue_lookup:
                planning.update(execution_queue_lookup[key])
                break

        for key in key_candidates:
            if key and key in packet_manifest_lookup:
                planning.update(packet_manifest_lookup[key])
                break

        resolved_job_doc_id = str(planning.get("job_doc_id") or "").strip()
        if resolved_job_doc_id:
            if not job.get("job_doc_id"):
                job["job_doc_id"] = resolved_job_doc_id
            if not job.get("url"):
                job["url"] = resolved_job_doc_id
            if not job.get("link"):
                job["link"] = resolved_job_doc_id

        job["application_planning"] = planning

        if planning:
            merged_count += 1

    return merged_count


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

    # logger.info("=============================")
    # logger.info("DISCOVERY MODE")
    # logger.info("=============================\n")
    # run_discovery()

    jobs = []
    application_planning_ran = False

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
            application_planning_ran = True
        else:
            logger.warning(
                "Skipping application planning because the job corpus is missing or empty: %s",
                corpus_path,
            )

    if not jobs and application_planning_ran and args.application_planning_only:
        jobs = _load_jobs_from_corpus("data/rag/job_corpus.jsonl")
        logger.info(
            "Loaded %s jobs from data/rag/job_corpus.jsonl for planning-only sheet refresh",
            len(jobs),
        )

    if jobs and application_planning_ran:
        execution_queue_lookup = _load_execution_queue_lookup(
            args.application_planning_output_dir
        )
        packet_manifest_lookup = _load_packet_manifest_lookup(
            args.application_planning_output_dir
        )

        merged_count = _merge_application_planning_into_jobs(
            jobs,
            execution_queue_lookup=execution_queue_lookup,
            packet_manifest_lookup=packet_manifest_lookup,
        )

        logger.info(
            "Merged application-planning metadata into %s jobs from %s and %s",
            merged_count,
            Path(args.application_planning_output_dir) / "application_execution_queue.csv",
            Path(args.application_planning_output_dir) / "job_packet_manifest.csv",
        )

    if jobs:
        write_jobs_to_sheet(jobs)

    logger.info("Final jobs: %s", len(jobs))


if __name__ == "__main__":
    args = _parse_args()
    _validate_application_planning_only_args(args)
    asyncio.run(main_async(args))