import argparse
import csv
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Set
from src.matching.job_adapter import build_job_evidence


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
    return str(value).strip().lower() == "true"


def _requires_resolved_resume_selection(row: dict) -> bool:
    return not (
        _parse_bool(row.get("requires_manual_review", "false"))
        or _parse_bool(row.get("is_tie", "false"))
    )

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
        default="outputs/application_planning",
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

    job_packets_dir = output_dir / "job_packets"
    job_packets_dir.mkdir(parents=True, exist_ok=True)

    best_variant_csv = output_dir / "best_resume_variant_by_job.csv"
    shortlist_csv = output_dir / "application_shortlist_by_job.csv"
    execution_queue_csv = output_dir / "application_execution_queue.csv"

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

    _run_cmd(batch_selector_cmd)

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

    _run_cmd(shortlist_cmd)

    execution_queue_cmd = [
        sys.executable,
        "application_execution_queue.py",
        "--input-csv",
        str(shortlist_csv),
        "--output-csv",
        str(execution_queue_csv),
        "--top-k-console",
        str(args.top_k_console),
    ]
    _run_cmd(execution_queue_cmd)

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

    manifest_rows = []

    for row in selected:
        job_doc_id = row["job_doc_id"]
        if job_doc_id not in job_doc_id_to_index:
            raise RuntimeError(f"Could not map job_doc_id to index: {job_doc_id}")

        job_index = job_doc_id_to_index[job_doc_id]
        winner_resume = row["winner_resume"]
        company = row["job_company"]
        title = row["job_title"]
        resume_selection_resolved = _requires_resolved_resume_selection(row)
        packet_status = "generated" if resume_selection_resolved else "pending_variant_selection"

        file_slug = (
            f"{_slugify(company, 30)}__"
            f"{_slugify(title, 60)}__"
            f"{_slugify(winner_resume, 40)}"
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
                "--output-json",
                str(packet_json_path),
            ]

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
            f"llm_status={llm_status['llm_tailoring_status']}",
            f"llm_cache_hit={llm_status['llm_cache_hit'] or '-'}",
            f"llm_error_type={llm_status['llm_error_type'] or '-'}",
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
                "packet_status": packet_status,
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
            }
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
        "packet_status",
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
    ]
    with manifest_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for manifest_row in manifest_rows:
            writer.writerow(manifest_row)
    
    packet_status_counts = _count_by(manifest_rows, "packet_status")
    packet_created_count = sum(
        1 for row in manifest_rows
        if str(row.get("packet_status", "")).strip() == "generated"
    )
    pending_variant_selection_count = sum(
        1
        for row in manifest_rows
        if str(row.get("packet_status", "")).strip() == "pending_variant_selection"
    )
    action_counts = _count_by(manifest_rows, "action")
    llm_status_counts = _count_by(manifest_rows, "llm_tailoring_status")

    print()
    print("=" * 100)
    print("APPLICATION PLANNING WORKFLOW COMPLETE")
    print("=" * 100)
    print(f"Best-variant CSV : {best_variant_csv}")
    print(f"Shortlist CSV    : {shortlist_csv}")
    print(f"Execution queue  : {execution_queue_csv}")
    print(f"Packet manifest  : {manifest_csv}")
    print(f"Job packets dir  : {job_packets_dir}")
    print(f"Packets created  : {packet_created_count}")
    print(f"Pending variant selection rows : {pending_variant_selection_count}")
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
    print("LLM status counts:")
    for status, count in llm_status_counts.items():
        print(f"  {status}: {count}")

if __name__ == "__main__":
    main()