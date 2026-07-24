import argparse
import asyncio
import csv
import json
import os
import subprocess
import sys
from pathlib import Path

from src.pipeline.runtime_status import (
    complete_stage,
    fail_run,
    finish_run,
    initialize_run,
    start_stage,
    update_config,
    update_counts,
)
from src.rag.export_job_corpus import export_job_corpus
from src.utils.logging import get_logger


def _application_planning_status_counts(output_dir="outputs/application_planning"):
    """Return application-planning counts for clearer runtime status messaging."""
    import csv
    from collections import Counter
    from pathlib import Path

    output_dir = Path(output_dir)
    shortlist_csv = output_dir / "application_shortlist_by_job.csv"
    packet_manifest_csv = output_dir / "job_packet_manifest.csv"

    def _count_rows(path):
        if not path.exists():
            return 0
        with path.open(newline="") as f:
            return sum(1 for _ in csv.DictReader(f))

    def _count_values(path, column):
        if not path.exists():
            return {}
        with path.open(newline="") as f:
            return dict(Counter((row.get(column) or "").strip() for row in csv.DictReader(f)))

    return {
        "planning_total_jobs": _count_rows(shortlist_csv),
        "planning_packet_jobs": _count_rows(packet_manifest_csv),
        "planning_actions": _count_values(shortlist_csv, "action"),
    }


def _application_planning_summary_message(browse_final_job_count):
    counts = _application_planning_status_counts()
    planned = counts.get("planning_total_jobs", 0)
    packets = counts.get("planning_packet_jobs", 0)

    if planned or packets:
        return (
            f"Completed: {browse_final_job_count} display jobs, "
            f"{planned} planned jobs, {packets} packet jobs"
        )

    return f"Completed: {browse_final_job_count} display jobs"


logger = get_logger(__name__)


DEFAULT_JOB_CORPUS_PATH = "data/rag/job_corpus.jsonl"


def _job_corpus_path_from_env(default: str = DEFAULT_JOB_CORPUS_PATH) -> str:
    return str(os.environ.get("JOB_STACK_JOB_CORPUS_PATH", "") or default).strip()


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
    parser.add_argument(
        "--application-planning-corpus-source",
        choices=["filesystem", "postgres"],
        default="filesystem",
        help=(
            "Select the explicit application-planning corpus owner. "
            "Postgres is supported only for planning-only execution."
        ),
    )
    parser.add_argument(
        "--application-planning-generate-llm-fallback",
        action="store_true",
        help="Pass --generate-llm-fallback to run_application_planning.py so filtered-out jobs get cached LLM fallback resume ranking.",
    )
    parser.add_argument(
        "--delete-seen-data",
        choices=["ask", "yes", "no"],
        default="ask",
        help="Control whether seen-job state should be deleted before the run.",
    )
    parser.add_argument(
        "--application-planning-generate-llm-adjudication",
        action="store_true",
        help="Pass --generate-llm-adjudication to run_application_planning.py for bounded LLM review on effective ties and close calls.",
    )
    return parser.parse_args()


def _run_cmd(cmd, *, redact_values=None):
    redactions = [
        str(value)
        for value in list(redact_values or [])
        if str(value or "")
    ]

    def redact(rendered):
        result = str(rendered)
        for value in redactions:
            result = result.replace(value, "[private-planning-corpus]")
        return result

    logger.info("")
    logger.info("RUNNING: %s", redact(" ".join(cmd)))
    logger.info("")
    if not redactions:
        subprocess.run(cmd, check=True)
        return

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        shell=False,
    )
    if process.stdout is None:
        process.kill()
        process.wait()
        raise RuntimeError("application_planning_failed")
    for line in process.stdout:
        sys.stdout.write(redact(line))
    return_code = process.wait()
    if return_code != 0:
        raise RuntimeError("application_planning_failed")


def _write_current_run_planning_corpus(jobs, output_dir):
    path = Path(output_dir) / "current_run_job_corpus.jsonl"
    exported_count = export_job_corpus(jobs, str(path), merge_existing=False)
    logger.info(
        "Current-run planning corpus exported: %s documents at %s",
        exported_count,
        path,
    )
    return str(path)


def _run_application_planning(
    args,
    job_corpus_path=None,
    additional_arguments=None,
):
    resolved_job_corpus_path = str(job_corpus_path or _job_corpus_path_from_env()).strip()

    cmd = [
        sys.executable,
        "run_application_planning.py",
        "--job-corpus",
        resolved_job_corpus_path,
        "--job-limit",
        str(args.application_planning_job_limit),
        "--job-packet-limit",
        str(args.application_planning_job_packet_limit),
        "--output-dir",
        args.application_planning_output_dir,
        "--include-actions",
        args.application_planning_llm_actions,
        "--llm-tailoring-actions",
        args.application_planning_llm_actions,
    ]

    if args.application_planning_generate_tailoring:
        cmd.append("--generate-tailoring")

    if args.application_planning_generate_llm_fallback:
        cmd.append("--generate-llm-fallback")
    
    if args.application_planning_generate_llm_adjudication:
        cmd.append("--generate-llm-adjudication")

    if args.application_planning_generate_llm_tailoring:
        cmd.append("--generate-llm-tailoring")

    if args.application_planning_refresh_llm_tailoring:
        cmd.append("--refresh-llm-tailoring")

    if additional_arguments:
        cmd.extend(list(additional_arguments))

    redact_values = (
        [resolved_job_corpus_path]
        if str(
            getattr(
                args,
                "application_planning_corpus_source",
                "filesystem",
            )
            or "filesystem"
        ).strip()
        == "postgres"
        else None
    )
    if redact_values:
        _run_cmd(cmd, redact_values=redact_values)
    else:
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
    corpus_source = str(
        getattr(args, "application_planning_corpus_source", "filesystem")
        or "filesystem"
    ).strip()
    if corpus_source == "postgres" and not (
        args.run_application_planning and args.application_planning_only
    ):
        raise SystemExit(
            "--application-planning-corpus-source postgres requires both "
            "--run-application-planning and --application-planning-only."
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


def _load_best_variant_lookup(output_dir: str) -> dict:
    batch_path = Path(output_dir) / "best_resume_variant_by_job.csv"
    if not batch_path.exists():
        return {}

    with batch_path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    lookup = {}
    for row in rows:
        job_doc_id = str(row.get("job_doc_id", "") or "").strip()

        payload = {
            "job_doc_id": job_doc_id,
            "winner_resume": row.get("winner_resume", ""),
            "winner_score": row.get("winner_score", ""),
            "winner_bucket": row.get("winner_bucket", ""),
            "runner_up_resume": row.get("runner_up_resume", ""),
            "runner_up_score": row.get("runner_up_score", ""),
            "score_gap": row.get("score_gap", ""),
            "is_tie": row.get("is_tie", ""),
            "tie_epsilon": row.get("tie_epsilon", ""),
            "passed_prefilter": row.get("passed_prefilter", ""),
            "filtered_out": row.get("filtered_out", ""),
            "llm_fallback_best_resume": row.get("llm_fallback_best_resume", ""),
            "llm_fallback_best_score": row.get("llm_fallback_best_score", ""),
            "llm_fallback_backup_resume": row.get("llm_fallback_backup_resume", ""),
            "llm_fallback_backup_score": row.get("llm_fallback_backup_score", ""),
            "llm_fallback_confidence": row.get("llm_fallback_confidence", ""),
            "llm_fallback_reason": row.get("llm_fallback_reason", ""),
            "llm_fallback_status": row.get("llm_fallback_status", ""),
            "llm_fallback_parse_ok": row.get("llm_fallback_parse_ok", ""),
            "llm_fallback_provider": row.get("llm_fallback_provider", ""),
            "llm_fallback_model": row.get("llm_fallback_model", ""),
            "llm_fallback_cache_hit": row.get("llm_fallback_cache_hit", ""),
            "llm_fallback_error_type": row.get("llm_fallback_error_type", ""),
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
    best_variant_lookup: dict,
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
            if key and key in best_variant_lookup:
                planning.update(best_variant_lookup[key])
                break

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


def _resolve_delete_seen_data(args) -> str:
    if args.delete_seen_data in {"yes", "no"}:
        return args.delete_seen_data

    if not sys.stdin or not sys.stdin.isatty():
        logger.info("Non-interactive run detected; keeping seen data by default.")
        return "no"

    delete_seen_data = None
    while delete_seen_data not in {"y", "n", "yes", "no"}:
        delete_seen_data = input("Delete seen data? (y/n): ").strip().lower()

    return "yes" if delete_seen_data in {"y", "yes"} else "no"


def _seen_jobs_backend_from_env() -> str:
    return str(os.environ.get("JOB_STACK_SEEN_JOBS_BACKEND", "") or "").strip().lower()


def _owner_user_id_from_env() -> str:
    return str(os.environ.get("JOB_STACK_OWNER_USER_ID", "") or "").strip()


def _is_user_pipeline_mode() -> bool:
    return str(os.environ.get("JOB_STACK_USER_PIPELINE_MODE", "") or "").strip().lower() in {
        "1",
        "true",
        "yes",
        "y",
    }


def _post_planning_shadow_enabled() -> bool:
    return str(
        os.environ.get(
            "APPLYLENS_DURABLE_EVIDENCE_CHAIN_SHADOW_ENABLED",
            "",
        )
        or ""
    ).strip().lower() in {"1", "true", "yes", "on"}


def _clear_seen_jobs_for_current_backend() -> None:
    backend = _seen_jobs_backend_from_env()
    owner_user_id = _owner_user_id_from_env()

    if backend == "postgres" and owner_user_id:
        from src.storage.user_pipeline.store import clear_user_seen_jobs_postgres_payload

        payload = clear_user_seen_jobs_postgres_payload(
            owner_user_id=owner_user_id,
            database_url="",
            database_url_env="DATABASE_URL",
            psql_bin="psql",
            print_only=False,
            ensure_schema=True,
        )
        logger.info(
            "Deleted seen data from Postgres for owner_user_id=%s deleted_count=%s",
            owner_user_id,
            payload.get("deleted_count", 0),
        )
        return

    seen_file = os.path.join(os.getcwd(), "data", "seen_job_ids.txt")
    if os.path.exists(seen_file):
        os.remove(seen_file)
        logger.info(f"Deleted seen data: {seen_file}")
    else:
        logger.info(f"Seen file not found: {seen_file}")


async def _main_async(
    args,
    *,
    postgres_snapshot=None,
):
    logger.info("Starting main pipeline entrypoint...")

    delete_seen_data = _resolve_delete_seen_data(args)
    corpus_source = str(
        getattr(args, "application_planning_corpus_source", "filesystem")
        or "filesystem"
    ).strip()

    initialize_run(
        output_dir=args.application_planning_output_dir,
        log_path=str(Path(args.application_planning_output_dir) / "live_pipeline_run.log"),
        status_path=str(Path(args.application_planning_output_dir) / "live_pipeline_status.json"),
        planning_only=bool(args.application_planning_only),
        job_limit=int(args.application_planning_job_limit),
        job_packet_limit=int(args.application_planning_job_packet_limit),
        llm_actions=[
            item.strip()
            for item in str(args.application_planning_llm_actions or "").split(",")
            if item.strip()
        ],
        generate_tailoring=bool(args.application_planning_generate_tailoring),
        generate_llm_tailoring=bool(args.application_planning_generate_llm_tailoring),
        refresh_llm_tailoring=bool(args.application_planning_refresh_llm_tailoring),
        generate_llm_fallback=bool(args.application_planning_generate_llm_fallback),
        generate_llm_adjudication=bool(args.application_planning_generate_llm_adjudication),
        delete_seen_data=delete_seen_data,
    )
    update_config(corpus_source=corpus_source)
    if postgres_snapshot is not None:
        update_counts(**postgres_snapshot.counts.runtime_counts())
    logger.info("Application-planning corpus_source=%s", corpus_source)

    if delete_seen_data == "yes":
        _clear_seen_jobs_for_current_backend()

    if _is_user_pipeline_mode():
        start_stage("startup", "Skipping global metrics store for user pipeline run")
        logger.info("Skipping global metrics store initialization for user pipeline run.")
        complete_stage(
            "startup",
            counts={
                "initialized_metrics": False,
                "skipped_global_metrics": True,
            },
        )
    else:
        start_stage("startup", "Initializing metrics store")

        logger.info("Initializing metrics store...")
        from src.storage.metrics_store import init_metrics_db

        init_metrics_db()
        complete_stage("startup", counts={"initialized_metrics": True})

    logger.info("Skipping eager embedding preload; model will load lazily when first needed.")

    jobs = []
    application_planning_ran = False
    post_planning_shadow = None
    planning_corpus_path = (
        str(postgres_snapshot.corpus_path)
        if postgres_snapshot is not None
        else _job_corpus_path_from_env()
    )

    if args.application_planning_only:
        logger.info("=============================")
        logger.info("APPLICATION PLANNING ONLY MODE")
        logger.info("=============================\n")
    else:
        logger.info("=============================")
        logger.info("SCRAPING JOBS")
        logger.info("=============================\n")

        from src.pipeline.collector import collect_all_jobs_async

        jobs = await collect_all_jobs_async()

    if args.run_application_planning:
        logger.info("")
        logger.info("=============================")
        logger.info("APPLICATION PLANNING")
        logger.info("=============================")

        corpus_path = planning_corpus_path
        planning_corpus_path = corpus_path
        if jobs and not args.application_planning_only:
            planning_corpus_path = _write_current_run_planning_corpus(
                jobs,
                args.application_planning_output_dir,
            )

        if _corpus_has_job_records(planning_corpus_path):
            start_stage("planning", "Running application planning")
            if _post_planning_shadow_enabled():
                from src.pipeline.post_planning_shadow import (
                    prepare_post_planning_shadow,
                )

                post_planning_shadow = prepare_post_planning_shadow()
            try:
                _run_application_planning(
                    args,
                    job_corpus_path=planning_corpus_path,
                    additional_arguments=(
                        post_planning_shadow.planning_arguments
                        if post_planning_shadow is not None
                        else None
                    ),
                )
                complete_stage("planning", "Application planning completed")
                application_planning_ran = True
            except BaseException:
                if post_planning_shadow is not None:
                    post_planning_shadow.cleanup()
                raise
        else:
            logger.warning(
                "Skipping application planning because the job corpus is missing or empty: %s",
                planning_corpus_path,
            )

    try:
        if not jobs and application_planning_ran and args.application_planning_only:
            jobs = _load_jobs_from_corpus(planning_corpus_path)
            if postgres_snapshot is not None:
                logger.info(
                    "Loaded %s jobs from private Postgres planning snapshot "
                    "for planning-only sheet refresh",
                    len(jobs),
                )
            else:
                logger.info(
                    "Loaded %s jobs from %s for planning-only sheet refresh",
                    len(jobs),
                    planning_corpus_path,
                )

        if jobs and application_planning_ran:
            best_variant_lookup = _load_best_variant_lookup(args.application_planning_output_dir)
            execution_queue_lookup = _load_execution_queue_lookup(args.application_planning_output_dir)
            packet_manifest_lookup = _load_packet_manifest_lookup(args.application_planning_output_dir)

            merged_count = _merge_application_planning_into_jobs(
                jobs,
                best_variant_lookup=best_variant_lookup,
                execution_queue_lookup=execution_queue_lookup,
                packet_manifest_lookup=packet_manifest_lookup,
            )

            logger.info(
                "Merged application-planning metadata into %s jobs from %s, %s, and %s",
                merged_count,
                Path(args.application_planning_output_dir) / "best_resume_variant_by_job.csv",
                Path(args.application_planning_output_dir) / "application_execution_queue.csv",
                Path(args.application_planning_output_dir) / "job_packet_manifest.csv",
            )

        start_stage("finalization", f"Display jobs: {len(jobs)}")
        logger.info("Display jobs: %s", len(jobs))

        finish_run(
            return_code=0,
            summary_message=(
                "Completed: no new jobs after cache/filtering"
                if len(jobs) == 0
                else _application_planning_summary_message(len(jobs))
            ),
            final_job_count=len(jobs),
        )
    except BaseException:
        if post_planning_shadow is not None:
            post_planning_shadow.cleanup()
        raise

    if post_planning_shadow is not None:
        try:
            post_planning_shadow.complete_after_authoritative_success(
                job_corpus_path=planning_corpus_path,
                output_dir=args.application_planning_output_dir,
            )
        except Exception:
            logger.warning(
                "Post-planning shadow lifecycle failed after authoritative success"
            )
            post_planning_shadow.cleanup()


async def main_async(args):
    _validate_application_planning_only_args(args)
    postgres_snapshot = None
    corpus_source = str(
        getattr(args, "application_planning_corpus_source", "filesystem")
        or "filesystem"
    ).strip()
    try:
        if corpus_source == "postgres":
            from src.pipeline.postgres_planning_corpus_snapshot import (
                create_postgres_planning_corpus_snapshot,
            )

            postgres_snapshot = create_postgres_planning_corpus_snapshot(
                args.application_planning_job_limit
            )
        return await _main_async(
            args,
            postgres_snapshot=postgres_snapshot,
        )
    finally:
        if postgres_snapshot is not None:
            cleanup_complete = postgres_snapshot.cleanup()
            update_counts(
                postgres_snapshot_cleanup_complete=bool(cleanup_complete)
            )
            logger.info(
                "Postgres planning corpus snapshot cleanup_complete=%s",
                bool(cleanup_complete),
            )


if __name__ == "__main__":
    args = _parse_args()
    _validate_application_planning_only_args(args)
    try:
        asyncio.run(main_async(args))
    except Exception as exc:
        fail_run("unknown", repr(exc))
        raise
