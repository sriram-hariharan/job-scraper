import argparse
import csv
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Set
from src.matching.job_adapter import build_job_evidence

from src.config.settings import ACTIVE_APPLICATION_PLANNING_OUTPUT_DIR
from src.agents.workflow_summary import write_agentic_workflow_summary_artifacts
from src.agents.workflow_verifier import write_agentic_workflow_verification_artifact
from src.pipeline.resume_selection_credibility import (
    CREDIBILITY_COLUMNS,
    compute_resume_selection_credibility,
    parse_bool as parse_credibility_bool,
)
from src.pipeline.runtime_status import update_stage_message

def _normalize_text(value: str) -> str:
    return " ".join(str(value or "").lower().split()).strip()


def _slugify(value: str, max_len: int = 80) -> str:
    text = _normalize_text(value)
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    if not text:
        text = "item"
    return text[:max_len]

def _job_corpus_has_records(job_corpus_path: Path) -> bool:
    if not job_corpus_path.exists():
        return False

    with job_corpus_path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                return True

    return False

def _run_cmd(cmd: List[str]) -> None:
    print()
    print("RUNNING:", " ".join(cmd))
    print()
    subprocess.run(cmd, check=True)

def _run_optional_cmd(cmd: List[str], step_name: str) -> int:
    print()
    print("RUNNING OPTIONAL:", " ".join(cmd))
    print()
    result = subprocess.run(cmd, check=False)

    if result.returncode == 0:
        print(f"{step_name}: completed")
    else:
        print(
            f"{step_name}: skipped/failed but continuing "
            f"(return_code={result.returncode})"
        )

    return result.returncode

def _planning_status(message: str, **counts) -> None:
    update_stage_message(
        message,
        {key: value for key, value in counts.items() if value is not None},
    )

def _status_label(company: str, title: str, max_len: int = 88) -> str:
    label = f"{company} | {title}".strip(" |")
    if len(label) <= max_len:
        return label
    return label[: max_len - 1].rstrip() + "..."

def _load_job_doc_id_to_index(job_corpus_path: Path) -> Dict[str, int]:
    if not job_corpus_path.exists():
        raise RuntimeError(f"Missing job corpus: {job_corpus_path}")

    mapping: Dict[str, int] = {}
    with job_corpus_path.open() as f:
        for idx, line in enumerate(f):
            line = line.strip()
            if not line:
                continue

            record = json.loads(line)
            job_evidence = build_job_evidence(record)
            job_doc_id = str(job_evidence.job_doc_id or "").strip()

            if job_doc_id:
                mapping[job_doc_id] = idx

    if not mapping:
        raise RuntimeError(
            f"No usable job_doc_id values could be derived from {job_corpus_path}"
        )

    return mapping


def _load_shortlist_rows(shortlist_csv_path: Path) -> List[dict]:
    if not shortlist_csv_path.exists():
        raise RuntimeError(f"Missing shortlist CSV: {shortlist_csv_path}")

    with shortlist_csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        raise RuntimeError(f"Shortlist CSV is empty: {shortlist_csv_path}")

    return rows


def _selected_rows(
    rows: List[dict],
    include_actions: Set[str],
    packet_limit: int,
) -> List[dict]:
    filtered = [row for row in rows if row.get("action", "") in include_actions]

    if packet_limit > 0:
        filtered = filtered[:packet_limit]

    return filtered

def _classify_llm_failure(parse_error: str) -> Dict[str, str]:
    text = str(parse_error or "").lower()

    if any(token in text for token in [
        "resource_exhausted",
        "quota exceeded",
        "rate limit",
        "429",
        "retrydelay",
    ]):
        return {
            "llm_tailoring_status": "rate_limited",
            "llm_error_type": "quota_exhausted",
            "llm_retryable": "True",
        }

    if any(token in text for token in [
        "timed out",
        "timeout",
        "deadline exceeded",
        "temporarily unavailable",
        "unavailable",
        "503",
        "internal error",
    ]):
        return {
            "llm_tailoring_status": "transient_error",
            "llm_error_type": "transient_provider_error",
            "llm_retryable": "True",
        }

    return {
        "llm_tailoring_status": "failed",
        "llm_error_type": "other_failure",
        "llm_retryable": "False",
    }

def _read_llm_tailoring_status(llm_json_path: Path) -> Dict[str, str]:
    if not llm_json_path.exists():
        return {
            "llm_tailoring_status": "missing",
            "llm_cache_hit": "",
            "llm_parse_ok": "",
            "llm_provider": "",
            "llm_model": "",
            "llm_error_type": "",
            "llm_retryable": "",
            "llm_retry_used": "",
        }

    try:
        data = json.loads(llm_json_path.read_text(encoding="utf-8"))
    except Exception:
        return {
            "llm_tailoring_status": "unreadable",
            "llm_cache_hit": "",
            "llm_parse_ok": "",
            "llm_provider": "",
            "llm_model": "",
            "llm_error_type": "unreadable_json",
            "llm_retryable": "False",
            "llm_retry_used": "",
        }

    parse_ok = bool(data.get("parse_ok"))
    cache_hit = bool(data.get("cache_hit"))
    retry_used = bool(data.get("retry_used"))
    parse_error = str(data.get("parse_error", ""))

    if parse_ok and cache_hit:
        status = "cached"
        error_type = ""
        retryable = ""
    elif parse_ok:
        status = "generated"
        error_type = ""
        retryable = ""
    else:
        failure = _classify_llm_failure(parse_error)
        status = failure["llm_tailoring_status"]
        error_type = failure["llm_error_type"]
        retryable = failure["llm_retryable"]

    return {
        "llm_tailoring_status": status,
        "llm_cache_hit": str(cache_hit),
        "llm_parse_ok": str(parse_ok),
        "llm_provider": str(data.get("provider", "")),
        "llm_model": str(data.get("model", "")),
        "llm_error_type": error_type,
        "llm_retryable": retryable,
        "llm_retry_used": str(retry_used),
    }

def _count_by(rows: List[dict], key: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows:
        value = str(row.get(key, "") or "").strip() or "<empty>"
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (item[0] != "<empty>", item[0])))

def _parse_bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _resolve_packet_resume_selection(row: dict) -> Dict[str, str]:
    credibility = compute_resume_selection_credibility(row)
    if not parse_credibility_bool(credibility["packet_generation_allowed"]):
        block_reason = credibility["packet_generation_block_reason"]
        if block_reason == "fallback_only_no_deterministic_match":
            return {
                "packet_status": "unresolved_no_credible_match",
                "packet_resume": "",
                "packet_resume_source": block_reason,
            }
        if block_reason == "deterministic_score_below_credible_threshold":
            return {
                "packet_status": "blocked_low_confidence_match",
                "packet_resume": "",
                "packet_resume_source": block_reason,
            }
        return {
            "packet_status": "unresolved_missing_winner",
            "packet_resume": "",
            "packet_resume_source": block_reason or "no_deterministic_winner",
        }

    resolved_resume = str(row.get("resolved_resume", "") or "").strip()
    resolved_selection_status = str(
        row.get("resolved_selection_status", "") or ""
    ).strip()
    resolved_resume_source = str(
        row.get("resolved_resume_source", "") or ""
    ).strip()
    variant_review_required = _parse_bool(
        row.get("variant_review_required", "false")
    )

    if resolved_resume and resolved_selection_status == "resolved" and not variant_review_required:
        return {
            "packet_status": "generated",
            "packet_resume": resolved_resume,
            "packet_resume_source": resolved_resume_source or "resolved_selection_projection",
        }

    if variant_review_required:
        return {
            "packet_status": "pending_variant_selection",
            "packet_resume": "",
            "packet_resume_source": resolved_resume_source or "unresolved_variant_review",
        }

    selection_signal = str(row.get("selection_signal", "") or "").strip()
    winner_resume = str(row.get("winner_resume", "") or "").strip()

    llm_fallback_best_resume = str(
        row.get("llm_fallback_best_resume", "") or ""
    ).strip()
    llm_fallback_status = str(
        row.get("llm_fallback_status", "") or ""
    ).strip()

    llm_adjudication_resume = str(
        row.get("llm_adjudication_resume", "") or ""
    ).strip()
    llm_adjudication_status = str(
        row.get("llm_adjudication_status", "") or ""
    ).strip()

    if selection_signal == "no_credible_match":
        return {
            "packet_status": "unresolved_no_credible_match",
            "packet_resume": "",
            "packet_resume_source": "no_credible_match",
        }

    if selection_signal in {"effective_tie", "manual_review_close_call"}:
        if llm_adjudication_resume:
            return {
                "packet_status": "generated",
                "packet_resume": llm_adjudication_resume,
                "packet_resume_source": f"llm_adjudication_{llm_adjudication_status or 'generated'}",
            }

        if llm_adjudication_status == "skipped_equivalent_variants" and winner_resume:
            return {
                "packet_status": "generated",
                "packet_resume": winner_resume,
                "packet_resume_source": "deterministic_equivalent_variants",
            }

        return {
            "packet_status": "pending_variant_selection",
            "packet_resume": "",
            "packet_resume_source": llm_adjudication_status or selection_signal or "ambiguous_selector_result",
        }

    if winner_resume:
        return {
            "packet_status": "generated",
            "packet_resume": winner_resume,
            "packet_resume_source": "deterministic_winner",
        }

    return {
        "packet_status": "unresolved_missing_winner",
        "packet_resume": "",
        "packet_resume_source": "missing_winner_resume",
    }

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the application-planning workflow: batch best-variant selection, shortlist generation, and JD diff packets."
    )
    parser.add_argument(
        "--job-corpus",
        default="data/rag/job_corpus.jsonl",
        help="Path to the retrieval-ready job corpus JSONL.",
    )
    parser.add_argument(
        "--job-limit",
        type=int,
        default=50,
        help="How many jobs from the corpus to evaluate in batch selection. Use 0 for all.",
    )
    parser.add_argument(
        "--manual-review-gap-epsilon",
        type=float,
        default=0.020,
        help="Selector close-call threshold to pass through to batch resume-variant selection.",
    )
    parser.add_argument(
        "--company-contains",
        default="",
        help="Optional case-insensitive company substring filter.",
    )
    parser.add_argument(
        "--title-contains",
        default="",
        help="Optional case-insensitive title substring filter.",
    )
    parser.add_argument(
        "--resume-name-contains",
        default="",
        help="Optional case-insensitive resume filename substring filter.",
    )
    parser.add_argument(
        "--top-k-console",
        type=int,
        default=15,
        help="How many jobs to print in the intermediate batch/shortlist scripts.",
    )
    parser.add_argument(
        "--output-dir",
        default=ACTIVE_APPLICATION_PLANNING_OUTPUT_DIR,
        help="Directory to write planning outputs.",
    )
    parser.add_argument(
        "--include-actions",
        default="APPLY,APPLY_REVIEW_VARIANTS,MAYBE_TAILOR",
        help="Comma-separated shortlist actions for which JD diff packets should be generated.",
    )
    parser.add_argument(
        "--job-packet-limit",
        type=int,
        default=0,
        help="Optional cap on how many JD diff packets to generate. Use 0 for all selected shortlist rows.",
    )
    parser.add_argument(
        "--generate-tailoring",
        action="store_true",
        help="Also generate grounded tailoring JSON/Markdown for each created JD packet.",
    )
    parser.add_argument(
        "--generate-llm-tailoring",
        action="store_true",
        help="Also generate live LLM tailoring JSON for selected shortlist actions.",
    )
    parser.add_argument(
        "--refresh-llm-tailoring",
        action="store_true",
        help="Force regeneration of live LLM tailoring outputs instead of reusing cached LLM JSON.",
    )
    parser.add_argument(
        "--llm-tailoring-actions",
        default="APPLY,MAYBE_TAILOR",
        help="Comma-separated shortlist actions eligible for live LLM tailoring after resume selection is resolved.",
    )
    parser.add_argument(
        "--generate-llm-fallback",
        action="store_true",
        help="When batch selecting resume variants, run LLM fallback ranking for jobs with no credible deterministic winner.",
    )
    parser.add_argument(
        "--training-log-jsonl",
        default="",
        help="Optional JSONL path to append structured tailoring training-log rows. Defaults to <output-dir>/training_logs/tailoring_runs.jsonl.",
    )
    parser.add_argument(
        "--generate-llm-adjudication",
        action="store_true",
        help="When batch selecting resume variants, run bounded LLM adjudication for effective ties and manual-review close calls.",
    )
    args = parser.parse_args()

    job_corpus_path = Path(args.job_corpus)

    if not _job_corpus_has_records(job_corpus_path):
        print()
        print("=" * 100)
        print("APPLICATION PLANNING WORKFLOW SKIPPED")
        print("=" * 100)
        print(f"Reason          : empty or missing job corpus")
        print(f"Job corpus path : {job_corpus_path}")
        print(f"Output dir      : {args.output_dir}")
        return

    if args.generate_llm_tailoring:
        args.generate_tailoring = True

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    training_logs_dir = output_dir / "training_logs"
    training_log_jsonl_path = (
        Path(args.training_log_jsonl).expanduser()
        if str(args.training_log_jsonl).strip()
        else training_logs_dir / "tailoring_runs.jsonl"
    )

    training_log_jsonl_path.parent.mkdir(parents=True, exist_ok=True)

    job_packets_dir = output_dir / "job_packets"
    job_packets_dir.mkdir(parents=True, exist_ok=True)

    best_variant_csv = output_dir / "best_resume_variant_by_job.csv"
    shortlist_csv = output_dir / "application_shortlist_by_job.csv"
    execution_queue_csv = output_dir / "application_execution_queue.csv"
    job_prioritization_csv = output_dir / "job_prioritization_recommendations.csv"
    job_prioritization_summary_json = output_dir / "job_prioritization_summary.json"
    tailoring_decision_csv = output_dir / "tailoring_decision_recommendations.csv"
    tailoring_decision_summary_json = output_dir / "tailoring_decision_summary.json"
    operator_review_csv = output_dir / "operator_review_recommendations.csv"
    operator_review_summary_json = output_dir / "operator_review_summary.json"
    agentic_workflow_summary_json = output_dir / "agentic_workflow_summary.json"
    agentic_workflow_summary_md = output_dir / "agentic_workflow_summary.md"
    agentic_workflow_verification_json = output_dir / "agentic_workflow_verification.json"

    batch_selector_cmd = [
        sys.executable,
        "batch_select_best_resume_variant.py",
        "--job-corpus",
        str(job_corpus_path),
        "--job-limit",
        str(args.job_limit),
        "--manual-review-gap-epsilon",
        str(args.manual_review_gap_epsilon),
        "--top-k-console",
        str(args.top_k_console),
        "--output-csv",
        str(best_variant_csv),
    ]
    if args.company_contains.strip():
        batch_selector_cmd.extend(["--company-contains", args.company_contains])
    if args.title_contains.strip():
        batch_selector_cmd.extend(["--title-contains", args.title_contains])
    if args.resume_name_contains.strip():
        batch_selector_cmd.extend(["--resume-name-contains", args.resume_name_contains])
    if args.generate_llm_fallback:
        batch_selector_cmd.append("--generate-llm-fallback")
    if args.generate_llm_adjudication:
        batch_selector_cmd.append("--generate-llm-adjudication")

    _planning_status(
        "Planning: selecting best resume variants",
        planning_substage="best_variant_selection",
    )
    _run_cmd(batch_selector_cmd)
    _planning_status(
        "Planning: best resume variant selection complete",
        planning_substage="best_variant_selection_complete",
    )

    archive_selector_runtime_fixture_cmd = [
        sys.executable,
        "archive_batch_selector_runtime_fixture.py",
        "--input-csv",
        str(best_variant_csv),
    ]
    _planning_status(
        "Planning: archiving selector runtime fixture",
        planning_substage="selector_fixture_archive",
    )
    _run_optional_cmd(
        archive_selector_runtime_fixture_cmd,
        "selector runtime fixture archiver",
    )

    shortlist_cmd = [
        sys.executable,
        "application_shortlist_from_batch_selector.py",
        "--input-csv",
        str(best_variant_csv),
        "--output-csv",
        str(shortlist_csv),
        "--top-k-console",
        str(args.top_k_console),
    ]
    if args.company_contains.strip():
        shortlist_cmd.extend(["--company-contains", args.company_contains])
    if args.title_contains.strip():
        shortlist_cmd.extend(["--title-contains", args.title_contains])

    _planning_status(
        "Planning: building application shortlist",
        planning_substage="application_shortlist",
    )
    _run_cmd(shortlist_cmd)

    execution_queue_cmd = [
        sys.executable,
        "application_execution_queue.py",
        "--input-csv",
        str(shortlist_csv),
        "--output-csv",
        str(execution_queue_csv),
        "--priority-output-csv",
        str(job_prioritization_csv),
        "--priority-summary-json",
        str(job_prioritization_summary_json),
        "--tailoring-decision-output-csv",
        str(tailoring_decision_csv),
        "--tailoring-decision-summary-json",
        str(tailoring_decision_summary_json),
        "--operator-review-output-csv",
        str(operator_review_csv),
        "--operator-review-summary-json",
        str(operator_review_summary_json),
        "--top-k-console",
        str(args.top_k_console),
    ]
    _planning_status(
        "Planning: building execution queue",
        planning_substage="execution_queue",
    )
    _run_cmd(execution_queue_cmd)

    _planning_status(
        "Planning: loading selected packet rows",
        planning_substage="load_selected_packets",
    )
    job_doc_id_to_index = _load_job_doc_id_to_index(job_corpus_path)
    shortlist_rows = _load_shortlist_rows(execution_queue_csv)

    include_actions = {
        action.strip()
        for action in args.include_actions.split(",")
        if action.strip()
    }
    llm_tailoring_actions = {
        action.strip()
        for action in args.llm_tailoring_actions.split(",")
        if action.strip()
    }
    selected = _selected_rows(
        shortlist_rows,
        include_actions=include_actions,
        packet_limit=args.job_packet_limit,
    )
    total_selected = len(selected)
    _planning_status(
        f"Planning packets: 0/{total_selected} complete",
        planning_substage="packet_generation",
        planning_packets_total=total_selected,
        planning_packets_completed=0,
    )

    manifest_rows = []

    for packet_index, row in enumerate(selected, start=1):
        row = {**row, **compute_resume_selection_credibility(row)}
        job_doc_id = row["job_doc_id"]
        if job_doc_id not in job_doc_id_to_index:
            raise RuntimeError(f"Could not map job_doc_id to index: {job_doc_id}")

        job_index = job_doc_id_to_index[job_doc_id]
        winner_resume = row["winner_resume"]
        company = row["job_company"]
        title = row["job_title"]
        status_label = _status_label(company, title)
        _planning_status(
            f"Planning packet {packet_index}/{total_selected}: {status_label}",
            planning_substage="packet_generation",
            planning_packets_total=total_selected,
            planning_packets_completed=packet_index - 1,
            planning_current_company=company,
            planning_current_title=title,
        )

        packet_resolution = _resolve_packet_resume_selection(row)
        packet_status = packet_resolution["packet_status"]
        packet_resume = packet_resolution["packet_resume"]
        packet_resume_source = packet_resolution["packet_resume_source"]
        resume_selection_resolved = packet_status == "generated"

        file_slug = (
            f"{_slugify(company, 30)}__"
            f"{_slugify(title, 60)}__"
            f"{_slugify(packet_resume or winner_resume or 'unresolved', 40)}"
        )

        packet_json_path = ""
        tailoring_json_path = ""
        tailoring_md_path = ""
        tailoring_llm_json_path = ""
        llm_status = {
            "llm_tailoring_status": "disabled",
            "llm_cache_hit": "",
            "llm_parse_ok": "",
            "llm_provider": "",
            "llm_model": "",
            "llm_error_type": "",
            "llm_retryable": "",
            "llm_retry_used": "",
        }

        if not resume_selection_resolved:
            llm_status["llm_tailoring_status"] = "pending_variant_selection"
        else:
            packet_json_path = job_packets_dir / f"{file_slug}.json"

            diff_cmd = [
                sys.executable,
                "jd_resume_diff_helper.py",
                "--job-corpus",
                str(job_corpus_path),
                "--job-index",
                str(job_index),
                "--resume-name-contains",
                packet_resume,
                "--output-json",
                str(packet_json_path),
            ]

            _planning_status(
                f"Planning packet {packet_index}/{total_selected}: building JD/resume packet",
                planning_substage="jd_resume_packet",
                planning_packets_total=total_selected,
                planning_packets_completed=packet_index - 1,
                planning_current_company=company,
                planning_current_title=title,
            )
            _run_cmd(diff_cmd)

            if args.generate_tailoring:
                tailoring_json_path = job_packets_dir / f"{file_slug}__tailoring.json"
                tailoring_md_path = job_packets_dir / f"{file_slug}__tailoring.md"

                tailoring_cmd = [
                    sys.executable,
                    "generate_tailoring_suggestions.py",
                    "--packet-json",
                    str(packet_json_path),
                    "--output-json",
                    str(tailoring_json_path),
                    "--output-md",
                    str(tailoring_md_path),
                    "--training-log-jsonl",
                    str(training_log_jsonl_path),
                ]

                if args.generate_llm_tailoring:
                    if row["action"] in llm_tailoring_actions:
                        tailoring_llm_json_path = job_packets_dir / f"{file_slug}__tailoring_llm.json"
                        tailoring_cmd.extend(
                            [
                                "--use-llm",
                                "--output-llm-json",
                                str(tailoring_llm_json_path),
                            ]
                        )
                        if args.refresh_llm_tailoring:
                            tailoring_cmd.append("--refresh-llm-cache")
                    else:
                        llm_status["llm_tailoring_status"] = "skipped_action_filter"

                _planning_status(
                    f"Planning packet {packet_index}/{total_selected}: generating tailoring suggestions",
                    planning_substage="tailoring_generation",
                    planning_packets_total=total_selected,
                    planning_packets_completed=packet_index - 1,
                    planning_current_company=company,
                    planning_current_title=title,
                    planning_live_llm_tailoring=bool(tailoring_llm_json_path),
                )
                _run_cmd(tailoring_cmd)

                if tailoring_llm_json_path:
                    llm_status = _read_llm_tailoring_status(tailoring_llm_json_path)

        print(
            "PACKET STATUS:",
            f"action={row['action']}",
            f"selection={row.get('selection_signal', '-')}",
            f"requires_manual_review={row.get('requires_manual_review', '-')}",
            f"is_tie={row.get('is_tie', '-')}",
            f"company={company}",
            f"title={title}",
            f"packet_status={packet_status}",
            f"packet_resume={packet_resume or '-'}",
            f"packet_resume_source={packet_resume_source}",
            f"llm_status={llm_status['llm_tailoring_status']}",
            f"llm_cache_hit={llm_status['llm_cache_hit'] or '-'}",
            f"llm_error_type={llm_status['llm_error_type'] or '-'}",
            f"llm_adjudication_status={row.get('llm_adjudication_status', '-')}",
            f"llm_adjudication_differs={row.get('llm_adjudication_differs_from_deterministic', '-')}",
        )

        manifest_rows.append(
            {
                "queue_rank": row.get("queue_rank", ""),
                "needs_variant_review": row.get("needs_variant_review", ""),
                "missing_requirement_count": row.get("missing_requirement_count", ""),
                "queue_priority_reason": row.get("queue_priority_reason", ""),
                "job_doc_id": job_doc_id,
                "job_company": company,
                "job_title": title,
                "job_location": row.get("job_location", ""),
                "posted_at": row.get("posted_at", ""),
                "freshness_status": row.get("freshness_status", ""),
                "ashby_timestamp_status": row.get("ashby_timestamp_status", ""),
                "action": row["action"],
                "winner_resume": winner_resume,
                "winner_score": row["winner_score"],
                "selection_signal": row.get("selection_signal", ""),
                "requires_manual_review": row.get("requires_manual_review", ""),
                "manual_review_gap_epsilon": row.get("manual_review_gap_epsilon", ""),
                "runner_up_resume": row["runner_up_resume"],
                "runner_up_score": row["runner_up_score"],
                "score_gap": row["score_gap"],
                "is_tie": row["is_tie"],
                "tie_epsilon": row.get("tie_epsilon", ""),
                **{column: row.get(column, "") for column in CREDIBILITY_COLUMNS},
                "packet_status": packet_status,
                "packet_resume": packet_resume,
                "packet_resume_source": packet_resume_source,
                "packet_json": str(packet_json_path),
                "tailoring_json": str(tailoring_json_path) if tailoring_json_path else "",
                "tailoring_md": str(tailoring_md_path) if tailoring_md_path else "",
                "tailoring_llm_json": (
                    str(tailoring_llm_json_path) if tailoring_llm_json_path else ""
                ),
                "llm_tailoring_status": llm_status["llm_tailoring_status"],
                "llm_cache_hit": llm_status["llm_cache_hit"],
                "llm_parse_ok": llm_status["llm_parse_ok"],
                "llm_provider": llm_status["llm_provider"],
                "llm_model": llm_status["llm_model"],
                "llm_error_type": llm_status["llm_error_type"],
                "llm_retryable": llm_status["llm_retryable"],
                "llm_retry_used": llm_status["llm_retry_used"],
                "llm_adjudication_resume": row.get("llm_adjudication_resume", ""),
                "llm_adjudication_confidence": row.get("llm_adjudication_confidence", ""),
                "llm_adjudication_reason": row.get("llm_adjudication_reason", ""),
                "llm_adjudication_status": row.get("llm_adjudication_status", ""),
                "llm_adjudication_parse_ok": row.get("llm_adjudication_parse_ok", ""),
                "llm_adjudication_provider": row.get("llm_adjudication_provider", ""),
                "llm_adjudication_model": row.get("llm_adjudication_model", ""),
                "llm_adjudication_cache_hit": row.get("llm_adjudication_cache_hit", ""),
                "llm_adjudication_differs_from_deterministic": row.get("llm_adjudication_differs_from_deterministic", ""),
                "llm_adjudication_error_type": row.get("llm_adjudication_error_type", ""),
            }
        )
        _planning_status(
            f"Planning packets: {packet_index}/{total_selected} complete",
            planning_substage="packet_generation",
            planning_packets_total=total_selected,
            planning_packets_completed=packet_index,
            planning_packets_generated=sum(
                1
                for manifest_row in manifest_rows
                if str(manifest_row.get("packet_status", "")).strip() == "generated"
            ),
            planning_llm_generated=sum(
                1
                for manifest_row in manifest_rows
                if str(manifest_row.get("llm_tailoring_status", "")).strip() == "generated"
            ),
            planning_llm_failed=sum(
                1
                for manifest_row in manifest_rows
                if str(manifest_row.get("llm_tailoring_status", "")).strip()
                in {"failed", "rate_limited", "transient_error", "missing", "unreadable"}
            ),
        )

    manifest_csv = output_dir / "job_packet_manifest.csv"
    fieldnames = [
        "queue_rank",
        "needs_variant_review",
        "missing_requirement_count",
        "queue_priority_reason",
        "job_doc_id",
        "job_company",
        "job_title",
        "job_location",
        "posted_at",
        "freshness_status",
        "ashby_timestamp_status",
        "action",
        "winner_resume",
        "winner_score",
        "selection_signal",
        "requires_manual_review",
        "manual_review_gap_epsilon",
        "runner_up_resume",
        "runner_up_score",
        "score_gap",
        "is_tie",
        "tie_epsilon",
        *CREDIBILITY_COLUMNS,
        "packet_status",
        "packet_resume",
        "packet_resume_source",
        "packet_json",
        "tailoring_json",
        "tailoring_md",
        "tailoring_llm_json",
        "llm_tailoring_status",
        "llm_cache_hit",
        "llm_parse_ok",
        "llm_provider",
        "llm_model",
        "llm_error_type",
        "llm_retryable",
        "llm_retry_used",
        "llm_adjudication_resume",
        "llm_adjudication_confidence",
        "llm_adjudication_reason",
        "llm_adjudication_status",
        "llm_adjudication_parse_ok",
        "llm_adjudication_provider",
        "llm_adjudication_model",
        "llm_adjudication_cache_hit",
        "llm_adjudication_differs_from_deterministic",
        "llm_adjudication_error_type",
    ]
    _planning_status(
        "Planning: writing packet manifest",
        planning_substage="write_manifest",
        planning_packets_total=total_selected,
        planning_packets_completed=total_selected,
    )
    with manifest_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for manifest_row in manifest_rows:
            writer.writerow(manifest_row)

    try:
        workflow_summary_artifact = write_agentic_workflow_summary_artifacts(
            output_dir=output_dir,
            summary_json_path=agentic_workflow_summary_json,
            summary_md_path=agentic_workflow_summary_md,
        )
    except Exception as exc:
        workflow_summary_artifact = {}
        print(f"Agentic workflow summary artifact skipped: {exc}")

    verifier_strict = _parse_bool(os.getenv("APPLYLENS_WORKFLOW_VERIFIER_STRICT", ""))
    try:
        workflow_verification_artifact = write_agentic_workflow_verification_artifact(
            output_dir=output_dir,
            output_json_path=agentic_workflow_verification_json,
            strict=verifier_strict,
        )
        verification_status = workflow_verification_artifact.get("validation_status", "")
        if verification_status not in {"passed", "warning"} and verifier_strict:
            raise RuntimeError(f"Agentic workflow verifier failed: {verification_status}")
        if verification_status and verification_status != "passed":
            print(f"Agentic workflow verifier status: {verification_status}")
    except Exception as exc:
        workflow_verification_artifact = {}
        if verifier_strict:
            raise
        print(f"Agentic workflow verification artifact skipped: {exc}")
    
    packet_status_counts = _count_by(manifest_rows, "packet_status")
    packet_resume_source_counts = _count_by(manifest_rows, "packet_resume_source")

    packet_created_count = sum(
        1 for row in manifest_rows
        if str(row.get("packet_status", "")).strip() == "generated"
    )
    pending_variant_selection_count = sum(
        1
        for row in manifest_rows
        if str(row.get("packet_status", "")).strip() == "pending_variant_selection"
    )
    unresolved_no_credible_match_count = sum(
        1
        for row in manifest_rows
        if str(row.get("packet_status", "")).strip() == "unresolved_no_credible_match"
    )
    unresolved_missing_winner_count = sum(
        1
        for row in manifest_rows
        if str(row.get("packet_status", "")).strip() == "unresolved_missing_winner"
    )
    action_counts = _count_by(manifest_rows, "action")
    llm_status_counts = _count_by(manifest_rows, "llm_tailoring_status")
    _planning_status(
        f"Application planning completed: {packet_created_count} packets created",
        planning_substage="complete",
        planning_packets_total=total_selected,
        planning_packets_completed=total_selected,
        planning_packets_generated=packet_created_count,
        planning_pending_variant_selection=pending_variant_selection_count,
        planning_unresolved_no_credible_match=unresolved_no_credible_match_count,
        planning_unresolved_missing_winner=unresolved_missing_winner_count,
        planning_llm_generated=llm_status_counts.get("generated", 0),
        planning_llm_cached=llm_status_counts.get("cached", 0),
        planning_llm_failed=sum(
            llm_status_counts.get(status, 0)
            for status in ("failed", "rate_limited", "transient_error", "missing", "unreadable")
        ),
    )

    print()
    print("=" * 100)
    print("APPLICATION PLANNING WORKFLOW COMPLETE")
    print("=" * 100)
    print(f"Best-variant CSV : {best_variant_csv}")
    print(f"Shortlist CSV    : {shortlist_csv}")
    print(f"Execution queue  : {execution_queue_csv}")
    print(f"Packet manifest  : {manifest_csv}")
    if workflow_summary_artifact:
        print(f"Agentic summary  : {workflow_summary_artifact['summary_json_path']}")
    if workflow_verification_artifact:
        print(f"Agentic verifier : {workflow_verification_artifact['json_path']}")
    print(f"Job packets dir  : {job_packets_dir}")
    print(f"Training log     : {training_log_jsonl_path}")
    print(f"Packets created  : {packet_created_count}")
    print(f"Pending variant selection rows : {pending_variant_selection_count}")
    print(f"Unresolved no-credible-match rows : {unresolved_no_credible_match_count}")
    print(f"Unresolved missing-winner rows    : {unresolved_missing_winner_count}")
    print(f"Tailoring step      : {'enabled' if args.generate_tailoring else 'disabled'}")
    print(f"Live LLM tailoring  : {'enabled' if args.generate_llm_tailoring else 'disabled'}")
    if args.generate_llm_tailoring:
        print(f"LLM tailoring acts  : {','.join(sorted(llm_tailoring_actions))}")
        print(f"LLM refresh mode    : {'enabled' if args.refresh_llm_tailoring else 'disabled'}")

    print()
    print("Action counts:")
    for action, count in action_counts.items():
        print(f"  {action}: {count}")
    
    print()
    print("Packet status counts:")
    for status, count in packet_status_counts.items():
        print(f"  {status}: {count}")
    
    print()
    print("Packet resume source counts:")
    for source, count in packet_resume_source_counts.items():
        print(f"  {source}: {count}")

    print()
    print("LLM status counts:")
    for status, count in llm_status_counts.items():
        print(f"  {status}: {count}")

if __name__ == "__main__":
    main()
