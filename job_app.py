import argparse
import csv
import json
import subprocess
import sys
import textwrap
from collections import Counter
from pathlib import Path
from typing import Dict, List, Any

from src.storage.operator_decisions.store import operator_decision_db_row
from src.storage.operator_decisions.read_postgres import (
    get_operator_decisions_postgres_status_payload,
)
from src.app.services import (
    decisions_payload,
    record_operator_resume_selection_payload,
)

DEFAULT_OUTPUT_DIR = Path("outputs/application_planning")
DEFAULT_CORPUS_PATH = Path("data/rag/job_corpus.jsonl")
WRAP_WIDTH = 100
DEFAULT_REVIEW_EXPORT_PATH = DEFAULT_OUTPUT_DIR / "operator_review_queue.csv"

OPERATOR_DECISION_OVERLAY_FIELDS = [
    "operator_decision_timestamp",
    "operator_decision",
    "operator_selected_resume",
    "operator_note",
]

def _run_cmd(cmd: List[str]) -> None:
    print()
    print("RUNNING:", " ".join(cmd))
    print()
    subprocess.run(cmd, check=True)


def _normalize_text(value: str) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _load_csv_rows(path: Path) -> List[dict]:
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))

def _ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

def _count_jsonl_rows(path: Path) -> int:
    if not path.exists():
        return 0

    count = 0
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                count += 1
    return count


def _parse_float(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _wrap_block(text: str, width: int = WRAP_WIDTH, indent: str = "    ") -> str:
    text = " ".join(str(text or "").split())
    if not text:
        return f"{indent}<empty>"
    return textwrap.fill(text, width=width, initial_indent=indent, subsequent_indent=indent)


def _print_wrapped_field(label: str, value, width: int = WRAP_WIDTH) -> None:
    label_width = 28
    prefix = f"{label:<{label_width}}: "
    text = " ".join(str(value or "").split())
    if not text:
        print(f"{prefix}<empty>")
        return
    wrapped = textwrap.fill(
        text,
        width=width,
        initial_indent=prefix,
        subsequent_indent=" " * len(prefix),
    )
    print(wrapped)


def _build_main_cmd(args, planning_only: bool) -> List[str]:
    cmd = [sys.executable, "-u", "main.py"]

    if args.run_application_planning:
        cmd.append("--run-application-planning")
        cmd.extend([
            "--application-planning-job-limit", str(args.job_limit),
            "--application-planning-job-packet-limit", str(args.job_packet_limit),
            "--application-planning-output-dir", args.output_dir,
            "--application-planning-llm-actions", args.llm_actions,
            "--delete-seen-data", getattr(args, "delete_seen_data", "no"),
        ])

        if args.generate_tailoring:
            cmd.append("--application-planning-generate-tailoring")
        if args.generate_llm_tailoring:
            cmd.append("--application-planning-generate-llm-tailoring")
        if args.refresh_llm_tailoring:
            cmd.append("--application-planning-refresh-llm-tailoring")
        if args.generate_llm_fallback:
            cmd.append("--application-planning-generate-llm-fallback")

    if planning_only:
        cmd.append("--application-planning-only")

    return cmd


def _status(args) -> None:
    output_dir = Path(args.output_dir)
    corpus_path = Path(args.job_corpus)

    best_rows = _load_csv_rows(output_dir / "best_resume_variant_by_job.csv")
    shortlist_rows = _load_csv_rows(output_dir / "application_shortlist_by_job.csv")
    queue_rows = _load_csv_rows(output_dir / "application_execution_queue.csv")
    manifest_rows = _load_csv_rows(output_dir / "job_packet_manifest.csv")
    decision_rows = _load_latest_operator_decision_rows()

    merged_rows = _build_job_index(output_dir)
    undecided_review_counts = _count_undecided_review_rows(merged_rows)

    print("=" * 100)
    print("JOB APP STATUS")
    print("=" * 100)
    print(f"Job corpus                 : {corpus_path}")
    print(f"Job corpus rows            : {_count_jsonl_rows(corpus_path)}")
    print(f"Planning output dir        : {output_dir}")
    print(f"Best-variant rows          : {len(best_rows)}")
    print(f"Shortlist rows             : {len(shortlist_rows)}")
    print(f"Execution queue rows       : {len(queue_rows)}")
    print(f"Packet manifest rows       : {len(manifest_rows)}")
    print("Operator decisions storage : postgres")
    print(f"Operator decisions rows    : {len(decision_rows)}")
    print()

    if best_rows:
        winner_bucket_counts = Counter(
            str(row.get("winner_bucket", "") or "<empty>")
            for row in best_rows
        )
        print("WINNER BUCKET COUNTS")
        print("--------------------")
        for key, count in sorted(winner_bucket_counts.items()):
            print(f"{key:25} {count}")
        print()

        fallback_status_counts = Counter(
            str(row.get("llm_fallback_status", "") or "<empty>")
            for row in best_rows
        )
        print("LLM FALLBACK STATUS COUNTS")
        print("--------------------------")
        for key, count in sorted(fallback_status_counts.items()):
            print(f"{key:25} {count}")
        print()

    if queue_rows:
        action_counts = Counter(
            str(row.get("action", "") or "<empty>")
            for row in queue_rows
        )
        print("QUEUE ACTION COUNTS")
        print("-------------------")
        for key, count in sorted(action_counts.items()):
            print(f"{key:25} {count}")
        print()

        print("TOP QUEUE ROWS")
        print("--------------")
        top_rows = sorted(
            queue_rows,
            key=lambda row: (
                int(str(row.get("queue_rank", "999999") or "999999")),
                -_parse_float(row.get("winner_score", "0")),
            ),
        )[: args.top_k]

        latest_by_key = _load_latest_decision_overlay()

        for row in top_rows:
            overlay_row = dict(row)
            for field in OPERATOR_DECISION_OVERLAY_FIELDS:
                overlay_row.setdefault(field, "")

            key_candidates = [
                _decision_row_key(row),
                f"queue_rank::{str(row.get('queue_rank', '') or '').strip()}",
                (
                    f"title::{_normalize_text(row.get('job_company', ''))}"
                    f"||{_normalize_text(row.get('job_title', ''))}"
                ),
            ]

            for key in key_candidates:
                if key and key in latest_by_key:
                    overlay_row.update(latest_by_key[key])
                    break

            print(
                f"#{overlay_row.get('queue_rank', '')} | {overlay_row.get('action', '')} | "
                f"{overlay_row.get('job_company', '')} | {overlay_row.get('job_title', '')}"
            )
            print(
                f"  winner={overlay_row.get('winner_resume', '')} "
                f"score={_parse_float(overlay_row.get('winner_score', '0')):.3f} "
                f"tie={overlay_row.get('is_tie', '')} "
                f"review={overlay_row.get('needs_variant_review', '')}"
            )
            print(
                f"  missing={overlay_row.get('missing_requirement_count', '')} | "
                f"reason={overlay_row.get('queue_priority_reason', '')}"
            )
            print(
                f"  operator_decision={overlay_row.get('operator_decision', '') or '<empty>'} | "
                f"operator_selected_resume={overlay_row.get('operator_selected_resume', '') or '<empty>'}"
            )
            print()

    if decision_rows:
        decision_counts = Counter(
            str(row.get("decision", "") or "<empty>")
            for row in decision_rows
        )
        print("OPERATOR DECISION COUNTS")
        print("------------------------")
        for key, count in sorted(decision_counts.items()):
            print(f"{key:25} {count}")
        print()

    if undecided_review_counts:
        print("UNDECIDED REVIEW COUNTS")
        print("-----------------------")
        for key, count in sorted(undecided_review_counts.items()):
            print(f"{key:25} {count}")
        print()
    else:
        print("UNDECIDED REVIEW COUNTS")
        print("-----------------------")
        print(f"{'<empty>':25} 0")
        print()

    if manifest_rows:
        llm_tailoring_counts = Counter(
            str(row.get("llm_tailoring_status", "") or "<empty>")
            for row in manifest_rows
        )
        print("LLM TAILORING STATUS COUNTS")
        print("---------------------------")
        for key, count in sorted(llm_tailoring_counts.items()):
            print(f"{key:25} {count}")
        print()


def _build_job_index(
    output_dir: Path,
) -> List[Dict[str, str]]:
    best_rows = _load_csv_rows(output_dir / "best_resume_variant_by_job.csv")
    queue_rows = _load_csv_rows(output_dir / "application_execution_queue.csv")
    manifest_rows = _load_csv_rows(output_dir / "job_packet_manifest.csv")

    merged: Dict[str, Dict[str, str]] = {}

    for source_rows in [best_rows, queue_rows, manifest_rows]:
        for row in source_rows:
            job_doc_id = str(row.get("job_doc_id", "") or "").strip()
            company = str(row.get("job_company", "") or "").strip()
            title = str(row.get("job_title", "") or "").strip()

            key = job_doc_id or f"{_normalize_text(company)}||{_normalize_text(title)}"
            if not key.strip("|"):
                continue

            if key not in merged:
                merged[key] = {}
            merged[key].update(row)

    merged_rows = list(merged.values())
    return _overlay_operator_decisions(merged_rows)


def _select_inspect_rows(rows: List[Dict[str, str]], args) -> List[Dict[str, str]]:
    selected = rows

    if args.queue_rank is not None:
        selected = [
            row for row in selected
            if str(row.get("queue_rank", "") or "").strip() == str(args.queue_rank)
        ]

    if args.job_doc_id:
        target = _normalize_text(args.job_doc_id)
        selected = [
            row for row in selected
            if _normalize_text(row.get("job_doc_id", "")) == target
        ]

    if args.company_contains:
        needle = _normalize_text(args.company_contains)
        selected = [
            row for row in selected
            if needle in _normalize_text(row.get("job_company", ""))
        ]

    if args.title_contains:
        needle = _normalize_text(args.title_contains)
        selected = [
            row for row in selected
            if needle in _normalize_text(row.get("job_title", ""))
        ]

    selected.sort(
        key=lambda row: (
            int(str(row.get("queue_rank", "999999") or "999999")),
            -_parse_float(row.get("winner_score", "0")),
            _normalize_text(row.get("job_company", "")),
            _normalize_text(row.get("job_title", "")),
        )
    )
    return selected[: args.limit]

def _parse_bool_flag(value: str):
    raw = _normalize_text(value)
    if raw in {"true", "1", "yes", "y"}:
        return True
    if raw in {"false", "0", "no", "n"}:
        return False
    return None


def _matches_bool_filter(row_value, expected) -> bool:
    if expected is None:
        return True
    actual = _parse_bool_flag(str(row_value or ""))
    return actual is expected

def _normalize_multi_filter_values(value: Any) -> List[str]:
    if value is None:
        return []

    raw_parts: List[str] = []

    if isinstance(value, (list, tuple, set)):
        for item in value:
            raw_parts.extend(str(item or "").split(","))
    else:
        raw_parts.extend(str(value or "").split(","))

    normalized: List[str] = []
    for part in raw_parts:
        item = _normalize_text(part)
        if item and item not in normalized:
            normalized.append(item)

    return normalized


def _matches_text_filter(row_value: str, filter_value: Any) -> bool:
    allowed = _normalize_multi_filter_values(filter_value)
    if not allowed:
        return True
    return _normalize_text(row_value) in allowed


def _select_browse_rows(rows: List[Dict[str, str]], args) -> List[Dict[str, str]]:
    selected = rows

    if _normalize_multi_filter_values(getattr(args, "action", "")):
        selected = [
            row for row in selected
            if _matches_text_filter(row.get("action", ""), args.action)
        ]

    if _normalize_multi_filter_values(getattr(args, "fallback_status", "")):
        selected = [
            row for row in selected
            if _matches_text_filter(row.get("llm_fallback_status", ""), args.fallback_status)
        ]

    if _normalize_multi_filter_values(getattr(args, "winner_bucket", "")):
        selected = [
            row for row in selected
            if _matches_text_filter(row.get("winner_bucket", ""), args.winner_bucket)
        ]

    needs_review = _parse_bool_flag(args.needs_review)
    if needs_review is not None:
        selected = [
            row for row in selected
            if _matches_bool_filter(row.get("needs_variant_review", ""), needs_review)
        ]

    is_tie = _parse_bool_flag(args.is_tie)
    if is_tie is not None:
        selected = [
            row for row in selected
            if _matches_bool_filter(row.get("is_tie", ""), is_tie)
        ]

    if args.company_contains:
        needle = _normalize_text(args.company_contains)
        selected = [
            row for row in selected
            if needle in _normalize_text(row.get("job_company", ""))
        ]

    if args.title_contains:
        needle = _normalize_text(args.title_contains)
        selected = [
            row for row in selected
            if needle in _normalize_text(row.get("job_title", ""))
        ]

    undecided_only = _parse_bool_flag(args.undecided_only)
    if undecided_only is True:
        selected = [
            row for row in selected
            if not str(row.get("operator_decision", "") or "").strip()
        ]

    selected.sort(
        key=lambda row: (
            int(str(row.get("queue_rank", "999999") or "999999")),
            -_parse_float(row.get("winner_score", "0")),
            _normalize_text(row.get("job_company", "")),
            _normalize_text(row.get("job_title", "")),
        )
    )
    return selected[: args.limit]

def _select_review_rows(rows: List[Dict[str, str]], args) -> List[Dict[str, str]]:
    selected = rows

    if args.action:
        action_target = _normalize_text(args.action)
        selected = [
            row for row in selected
            if _normalize_text(row.get("action", "")) == action_target
        ]
    if args.queue_rank is not None:
        selected = [
            row for row in selected
            if str(row.get("queue_rank", "") or "").strip() == str(args.queue_rank)
        ]

    if args.job_doc_id:
        target = _normalize_text(args.job_doc_id)
        selected = [
            row for row in selected
            if _normalize_text(row.get("job_doc_id", "")) == target
        ]

    if args.company_contains:
        needle = _normalize_text(args.company_contains)
        selected = [
            row for row in selected
            if needle in _normalize_text(row.get("job_company", ""))
        ]

    if args.title_contains:
        needle = _normalize_text(args.title_contains)
        selected = [
            row for row in selected
            if needle in _normalize_text(row.get("job_title", ""))
        ]

    if not args.include_non_review:
        selected = [
            row for row in selected
            if _matches_bool_filter(row.get("needs_variant_review", ""), True)
        ]
    
    undecided_only = _parse_bool_flag(args.undecided_only)
    if undecided_only is True:
        selected = [
            row for row in selected
            if not str(row.get("operator_decision", "") or "").strip()
        ]

    selected.sort(
        key=lambda row: (
            int(str(row.get("queue_rank", "999999") or "999999")),
            -_parse_float(row.get("winner_score", "0")),
            _normalize_text(row.get("job_company", "")),
            _normalize_text(row.get("job_title", "")),
        )
    )
    return selected[: args.limit]

def _workflow_view_rows(rows: List[Dict[str, str]], view: str) -> List[Dict[str, str]]:
    normalized_view = _normalize_text(view)

    def has_decision(row: Dict[str, str]) -> bool:
        return bool(str(row.get("operator_decision", "") or "").strip())

    def selected_runner_up(row: Dict[str, str]) -> bool:
        selected = str(row.get("operator_selected_resume", "") or "").strip()
        runner_up = str(row.get("runner_up_resume", "") or "").strip()
        return bool(selected and runner_up and selected == runner_up)

    if normalized_view == "undecided_apply_review":
        filtered = [
            row for row in rows
            if _normalize_text(row.get("action", "")) == "apply_review_variants"
            and _matches_bool_filter(row.get("needs_variant_review", ""), True)
            and not has_decision(row)
        ]
    elif normalized_view == "undecided_maybe_tailor":
        filtered = [
            row for row in rows
            if _normalize_text(row.get("action", "")) == "maybe_tailor"
            and _matches_bool_filter(row.get("needs_variant_review", ""), True)
            and not has_decision(row)
        ]
    elif normalized_view == "runner_up_selected":
        filtered = [
            row for row in rows
            if selected_runner_up(row)
        ]
    elif normalized_view == "direct_apply_pending":
        filtered = [
            row for row in rows
            if _normalize_text(row.get("action", "")) == "apply"
            and not has_decision(row)
        ]
    else:
        raise SystemExit(
            "Unsupported workflow view. Use one of: "
            "undecided_apply_review, undecided_maybe_tailor, "
            "runner_up_selected, direct_apply_pending"
        )

    filtered.sort(
        key=lambda row: (
            int(str(row.get("queue_rank", "999999") or "999999")),
            -_parse_float(row.get("winner_score", "0")),
            _normalize_text(row.get("job_company", "")),
            _normalize_text(row.get("job_title", "")),
        )
    )
    return filtered

def _infer_planner_view(request: str) -> str:
    text = _normalize_text(request)

    if "runner up" in text or "runner-up" in text:
        return "runner_up_selected"

    if ("undecided" in text or "pending" in text) and (
        "apply review" in text or "review variants" in text or "variant review" in text
    ):
        return "undecided_apply_review"

    if ("undecided" in text or "pending" in text) and (
        "maybe tailor" in text or "tailor" in text
    ):
        return "undecided_maybe_tailor"

    if "direct apply" in text and ("pending" in text or "still pending" in text):
        return "direct_apply_pending"

    raise SystemExit(
        "Could not map planner request to a workflow view. Try one of: "
        "'show undecided apply review jobs', "
        "'show undecided maybe tailor jobs', "
        "'show jobs where i picked the runner up', "
        "'show direct apply jobs still pending'."
    )

def _build_review_export_rows(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    export_rows: List[Dict[str, str]] = []

    for row in rows:
        export_rows.append({
            "queue_rank": str(row.get("queue_rank", "") or ""),
            "job_doc_id": str(row.get("job_doc_id", "") or ""),
            "job_company": str(row.get("job_company", "") or ""),
            "job_title": str(row.get("job_title", "") or ""),
            "action": str(row.get("action", "") or ""),
            "needs_variant_review": str(row.get("needs_variant_review", "") or ""),
            "is_tie": str(row.get("is_tie", "") or ""),
            "winner_resume": str(row.get("winner_resume", "") or ""),
            "winner_score": str(row.get("winner_score", "") or ""),
            "runner_up_resume": str(row.get("runner_up_resume", "") or ""),
            "runner_up_score": str(row.get("runner_up_score", "") or ""),
            "score_gap": str(row.get("score_gap", "") or ""),
            "missing_requirement_count": str(row.get("missing_requirement_count", "") or ""),
            "queue_priority_reason": str(row.get("queue_priority_reason", "") or ""),
            "tailoring_md": str(row.get("tailoring_md", "") or ""),
            "packet_json": str(row.get("packet_json", "") or ""),
            "operator_decision": str(row.get("operator_decision", "") or ""),
            "operator_selected_resume": str(row.get("operator_selected_resume", "") or ""),
            "operator_decision_timestamp": str(row.get("operator_decision_timestamp", "") or ""),
            "operator_note": str(row.get("operator_note", "") or ""),
        })

    return export_rows

def _as_list(value) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str):
        return [value] if value.strip() else []
    return [str(value)]


def _print_string_list(title: str, values, limit: int = 5) -> None:
    items = _as_list(values)
    if not items:
        return
    print(title)
    for item in items[:limit]:
        print(_wrap_block(item))


def _print_kv_block(title: str, mapping, keys: List[str]) -> None:
    if not isinstance(mapping, dict):
        if mapping not in (None, "", []):
            print(title)
            print(_wrap_block(mapping))
        return

    lines = []
    for key in keys:
        value = mapping.get(key)
        if value in (None, "", []):
            continue
        lines.append(f"{key}={value}")

    if not lines:
        return

    print(title)
    for line in lines:
        print(_wrap_block(line))

def _print_any_block(title: str, value) -> None:
    if value in (None, "", []):
        return

    if isinstance(value, dict):
        _print_kv_block(title, value, list(value.keys()))
        return

    if isinstance(value, list):
        if not value:
            return
        print(title)
        for item in value:
            print(_wrap_block(item))
        return

    print(title)
    print(_wrap_block(value))
    
def _print_dimension_deltas(values, limit: int = 5) -> None:
    if not isinstance(values, list) or not values:
        return
    print("TOP DIMENSION DELTAS")
    for item in values[:limit]:
        if not isinstance(item, dict):
            print(_wrap_block(item))
            continue
        dimension = item.get("dimension", "<unknown>")
        delta = item.get("delta")
        selected_score = item.get("selected_score")
        backup_score = item.get("backup_score")
        text = (
            f"{dimension}: delta={delta}, selected={selected_score}, backup={backup_score}"
        )
        print(_wrap_block(text))


def _print_relevant_bullets(values, limit: int = 3) -> None:
    if not isinstance(values, list) or not values:
        return
    print("TOP RELEVANT BULLETS")
    for idx, item in enumerate(values[:limit], start=1):
        if not isinstance(item, dict):
            print(_wrap_block(f"{idx}. {item}"))
            continue
        header_parts = []
        for key in ["section", "source_title", "source_company"]:
            if item.get(key):
                header_parts.append(f"{key}={item.get(key)}")
        if header_parts:
            print(_wrap_block(f"{idx}. " + " | ".join(header_parts)))
        if item.get("text"):
            print(_wrap_block(item.get("text"), indent="      "))

def _print_rag_search_results(results: List[Dict[str, str]]) -> None:
    if not results:
        print("No search results returned.")
        return

    print("SEARCH RESULTS")
    print("--------------")
    for idx, row in enumerate(results, start=1):
        print(
            f"{idx}. {row.get('company', '')} | {row.get('title', '')} | "
            f"score={row.get('score', '')}"
        )
        print(
            f"   location={row.get('location', '') or '<empty>'} | "
            f"source={row.get('source', '') or '<empty>'}"
        )
        print(
            f"   job_url={row.get('job_url', '') or '<empty>'}"
        )
        if row.get("posted_at"):
            print(f"   posted_at={row.get('posted_at', '')}")
        if row.get("visa_sponsorship"):
            print(f"   visa_sponsorship={row.get('visa_sponsorship', '')}")
        if row.get("ai_fit_score") not in (None, ""):
            print(f"   ai_fit_score={row.get('ai_fit_score')}")
        print()


def _print_rag_answer_response(response: Dict[str, str]) -> None:
    _print_wrapped_field("Question", response.get("question", ""))
    _print_wrapped_field("Retrieved count", response.get("retrieved_count", ""))
    _print_wrapped_field("Source count", response.get("source_count", ""))
    _print_wrapped_field("Insufficient evidence", response.get("insufficient_evidence", ""))

    print("ANSWER")
    print(_wrap_block(response.get("answer", "")))

    sources = response.get("sources", []) or []
    if sources:
        print("SOURCES")
        for source in sources:
            print(
                _wrap_block(
                    f"{source.get('source_id', '')} | "
                    f"{source.get('company', '')} | "
                    f"{source.get('title', '')} | "
                    f"{source.get('job_url', '')}"
                )
            )

def _print_packet_summary(packet_json_path: str) -> None:
    path = Path(packet_json_path)
    if not packet_json_path or not path.exists():
        _print_wrapped_field("Packet JSON", "<missing>")
        return

    _print_wrapped_field("Packet JSON", path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        _print_wrapped_field("Packet JSON read error", exc)
        return

    _print_wrapped_field("Packet JSON keys", ", ".join(sorted(data.keys())[:15]))

    summary = data.get("summary")
    selection = data.get("selection")
    guardrail = data.get("guardrail")

    if isinstance(summary, dict):
        summary_lines = []
        for key in [
            "selection_rationale",
            "tailoring_focus",
            "recruiter_summary",
            "job_summary",
        ]:
            if summary.get(key):
                summary_lines.append(f"{key}: {summary.get(key)}")

        if summary_lines or summary.get("resume_gaps") or summary.get("missing_requirements"):
            print("SUMMARY")
            for line in summary_lines:
                print(_wrap_block(line))

            _print_string_list("RESUME GAPS", summary.get("resume_gaps"), limit=6)
            _print_string_list("MISSING REQUIREMENTS", summary.get("missing_requirements"), limit=6)
    elif summary not in (None, "", []):
        _print_any_block("SUMMARY", summary)

    _print_kv_block(
        "SELECTION",
        selection,
        [
            "winner_resume",
            "winner_score",
            "runner_up_resume",
            "runner_up_score",
            "score_gap",
            "is_tie",
            "needs_variant_review",
        ],
    )

    if isinstance(guardrail, dict):
        _print_kv_block(
            "GUARDRAIL",
            guardrail,
            [
                "guardrail_status",
                "guardrail_reason",
                "missing_requirement_count",
            ],
        )
    else:
        _print_any_block("GUARDRAIL", guardrail)

    _print_dimension_deltas(data.get("top_dimension_deltas_vs_backup"), limit=5)
    _print_relevant_bullets(data.get("top_relevant_bullets"), limit=3)

def _load_packet_json(packet_json_path: str):
    path = Path(packet_json_path)
    if not packet_json_path or not path.exists():
        return None

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

def _decision_row_keys(row: Dict[str, str]) -> List[str]:
    keys: List[str] = []

    job_doc_id = str(row.get("job_doc_id", "") or "").strip()
    if job_doc_id:
        keys.append(f"job_doc_id::{job_doc_id}")

    queue_rank = str(row.get("queue_rank", "") or "").strip()
    if queue_rank:
        keys.append(f"queue_rank::{queue_rank}")

    company = _normalize_text(row.get("job_company", ""))
    title = _normalize_text(row.get("job_title", ""))
    if company or title:
        keys.append(f"title::{company}||{title}")

    return keys

def _decision_row_key(row: Dict[str, str]) -> str:
    keys = _decision_row_keys(row)
    return keys[0] if keys else ""

def _load_latest_operator_decision_rows() -> List[Dict[str, str]]:
    meta_payload = get_operator_decisions_postgres_status_payload(
        limit=1,
        database_url="",
        database_url_env="DATABASE_URL",
        psql_bin="psql",
        print_only=False,
    )
    meta_block = dict(meta_payload.get("postgres", {}) or {})
    query_limit = max(int(meta_block.get("latest_state_count", 0) or 0), 1)

    postgres_payload = get_operator_decisions_postgres_status_payload(
        limit=query_limit,
        database_url="",
        database_url_env="DATABASE_URL",
        psql_bin="psql",
        print_only=False,
    )
    postgres_block = dict(postgres_payload.get("postgres", {}) or {})
    postgres_rows = list(postgres_block.get("latest_rows", []) or [])

    normalized_rows: List[Dict[str, str]] = []
    for row in postgres_rows:
        normalized = operator_decision_db_row({
            "decision_timestamp": row.get("decision_timestamp", ""),
            "queue_rank": row.get("queue_rank", ""),
            "job_doc_id": row.get("job_doc_id", ""),
            "job_company": row.get("job_company", ""),
            "job_title": row.get("job_title", ""),
            "planning_action": row.get("planning_action", ""),
            "winner_resume": row.get("winner_resume", ""),
            "winner_score": row.get("winner_score", ""),
            "runner_up_resume": row.get("runner_up_resume", ""),
            "runner_up_score": row.get("runner_up_score", ""),
            "selected_resume": row.get("selected_resume", ""),
            "decision": row.get("decision", ""),
            "note": row.get("note", ""),
        })
        normalized_rows.append(normalized)

    normalized_rows.sort(
        key=lambda row: (
            str(row.get("decision_timestamp", "") or ""),
            str(row.get("decision_id", "") or ""),
        ),
        reverse=True,
    )
    return normalized_rows

def _load_latest_decision_overlay() -> Dict[str, Dict[str, str]]:
    meta_payload = get_operator_decisions_postgres_status_payload(
        limit=1,
        database_url="",
        database_url_env="DATABASE_URL",
        psql_bin="psql",
        print_only=False,
    )
    meta_block = dict(meta_payload.get("postgres", {}) or {})
    query_limit = max(int(meta_block.get("latest_state_count", 0) or 0), 1)

    postgres_payload = get_operator_decisions_postgres_status_payload(
        limit=query_limit,
        database_url="",
        database_url_env="DATABASE_URL",
        psql_bin="psql",
        print_only=False,
    )
    postgres_block = dict(postgres_payload.get("postgres", {}) or {})
    postgres_rows = list(postgres_block.get("latest_rows", []) or [])

    latest_by_key: Dict[str, Dict[str, str]] = {}

    for row in postgres_rows:
        normalized = operator_decision_db_row({
            "decision_timestamp": row.get("decision_timestamp", ""),
            "queue_rank": row.get("queue_rank", ""),
            "job_doc_id": row.get("job_doc_id", ""),
            "job_company": row.get("job_company", ""),
            "job_title": row.get("job_title", ""),
            "planning_action": row.get("planning_action", ""),
            "winner_resume": row.get("winner_resume", ""),
            "winner_score": row.get("winner_score", ""),
            "runner_up_resume": row.get("runner_up_resume", ""),
            "runner_up_score": row.get("runner_up_score", ""),
            "selected_resume": row.get("selected_resume", ""),
            "decision": row.get("decision", ""),
            "note": row.get("note", ""),
        })

        decision_key = str(normalized.get("decision_key", "") or "").strip()
        if not decision_key:
            continue

        latest_by_key[decision_key] = {
            "operator_decision_timestamp": str(normalized.get("decision_timestamp", "") or ""),
            "operator_decision": str(normalized.get("decision", "") or ""),
            "operator_selected_resume": str(normalized.get("selected_resume", "") or ""),
            "operator_note": str(normalized.get("note", "") or ""),
        }

    return latest_by_key


def _overlay_operator_decisions(
    rows: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    latest_by_key = _load_latest_decision_overlay()
    if not latest_by_key:
        return rows

    overlaid_rows: List[Dict[str, str]] = []

    for row in rows:
        merged = dict(row)
        for field in OPERATOR_DECISION_OVERLAY_FIELDS:
            merged.setdefault(field, "")

        key_candidates = _decision_row_keys(row)

        overlay = None
        for key in key_candidates:
            if key and key in latest_by_key:
                overlay = latest_by_key[key]
                break

        if overlay:
            merged.update(overlay)

        overlaid_rows.append(merged)

    return overlaid_rows

def _find_single_job_row(rows: List[Dict[str, str]], args) -> Dict[str, str]:
    selected = rows

    if args.queue_rank is not None:
        selected = [
            row for row in selected
            if str(row.get("queue_rank", "") or "").strip() == str(args.queue_rank)
        ]

    if args.job_doc_id:
        target = _normalize_text(args.job_doc_id)
        selected = [
            row for row in selected
            if _normalize_text(row.get("job_doc_id", "")) == target
        ]

    if args.company_contains:
        needle = _normalize_text(args.company_contains)
        selected = [
            row for row in selected
            if needle in _normalize_text(row.get("job_company", ""))
        ]

    if args.title_contains:
        needle = _normalize_text(args.title_contains)
        selected = [
            row for row in selected
            if needle in _normalize_text(row.get("job_title", ""))
        ]

    selected.sort(
        key=lambda row: (
            int(str(row.get("queue_rank", "999999") or "999999")),
            -_parse_float(row.get("winner_score", "0")),
            _normalize_text(row.get("job_company", "")),
            _normalize_text(row.get("job_title", "")),
        )
    )

    if not selected:
        raise SystemExit("No matching job found in application-planning outputs.")

    if len(selected) > 1:
        raise SystemExit(
            "Decision target is ambiguous. Use --queue-rank or --job-doc-id to select exactly one row."
        )

    return selected[0]

def _select_decision_rows(rows: List[Dict[str, str]], args) -> List[Dict[str, str]]:
    selected = rows

    if args.queue_rank is not None:
        selected = [
            row for row in selected
            if str(row.get("queue_rank", "") or "").strip() == str(args.queue_rank)
        ]

    if _normalize_multi_filter_values(getattr(args, "decision", "")):
        selected = [
            row for row in selected
            if _matches_text_filter(row.get("decision", ""), args.decision)
        ]

    if args.selected_resume:
        target = _normalize_text(args.selected_resume)
        selected = [
            row for row in selected
            if _normalize_text(row.get("selected_resume", "")) == target
        ]

    if args.company_contains:
        needle = _normalize_text(args.company_contains)
        selected = [
            row for row in selected
            if needle in _normalize_text(row.get("job_company", ""))
        ]

    if args.title_contains:
        needle = _normalize_text(args.title_contains)
        selected = [
            row for row in selected
            if needle in _normalize_text(row.get("job_title", ""))
        ]

    selected.sort(
        key=lambda row: (
            str(row.get("decision_timestamp", "") or ""),
            str(row.get("queue_rank", "") or ""),
        ),
        reverse=True,
    )
    return selected[: args.limit]

def _count_undecided_review_rows(rows: List[Dict[str, str]]) -> Dict[str, int]:
    counts = Counter()

    for row in rows:
        action = str(row.get("action", "") or "").strip()
        needs_review = _matches_bool_filter(row.get("needs_variant_review", ""), True)
        operator_decision = str(row.get("operator_decision", "") or "").strip()

        if not action or not needs_review:
            continue
        if operator_decision:
            continue

        counts[action] += 1

    return dict(counts)

def _export_csv_rows(path: Path, headers: List[str], rows: List[Dict[str, str]]) -> None:
    _ensure_parent_dir(path)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({header: row.get(header, "") for header in headers})

def _validate_selected_resume(row: Dict[str, str], selected_resume: str) -> str:
    selected = str(selected_resume or "").strip()
    if not selected:
        raise SystemExit("--selected-resume is required.")

    allowed = {
        str(row.get("winner_resume", "") or "").strip(),
        str(row.get("runner_up_resume", "") or "").strip(),
    }
    allowed = {value for value in allowed if value}

    if allowed and selected not in allowed:
        raise SystemExit(
            f"--selected-resume must match one of the compared variants: {sorted(allowed)}"
        )

    return selected

def _inspect(args) -> None:
    rows = _build_job_index(Path(args.output_dir))
    selected = _select_inspect_rows(rows, args)

    if not selected:
        raise SystemExit("No matching jobs found in application-planning outputs.")

    print("=" * 100)
    print("JOB APP INSPECT")
    print("=" * 100)

    for row in selected:
        _print_wrapped_field("Job doc id", row.get("job_doc_id", ""))
        _print_wrapped_field("Company", row.get("job_company", ""))
        _print_wrapped_field("Title", row.get("job_title", ""))
        _print_wrapped_field("Action", row.get("action", ""))
        _print_wrapped_field("Queue rank", row.get("queue_rank", ""))
        _print_wrapped_field("Winner", row.get("winner_resume", ""))
        _print_wrapped_field("Winner score", f"{_parse_float(row.get('winner_score', '0')):.3f}")
        _print_wrapped_field("Runner up", row.get("runner_up_resume", ""))
        _print_wrapped_field("Runner up score", f"{_parse_float(row.get('runner_up_score', '0')):.3f}")
        _print_wrapped_field("Score gap", f"{_parse_float(row.get('score_gap', '0')):.3f}")
        _print_wrapped_field("Needs variant review", row.get("needs_variant_review", ""))
        _print_wrapped_field("Queue priority reason", row.get("queue_priority_reason", ""))
        _print_wrapped_field("Fallback best", row.get("llm_fallback_best_resume", ""))
        _print_wrapped_field("Fallback best score", f"{_parse_float(row.get('llm_fallback_best_score', '0')):.3f}")
        _print_wrapped_field("Fallback backup", row.get("llm_fallback_backup_resume", ""))
        _print_wrapped_field("Fallback status", row.get("llm_fallback_status", ""))
        _print_wrapped_field("Fallback reason", row.get("llm_fallback_reason", ""))
        _print_wrapped_field("LLM tailoring status", row.get("llm_tailoring_status", ""))
        _print_wrapped_field("LLM error type", row.get("llm_error_type", ""))
        _print_wrapped_field("Tailoring markdown", row.get("tailoring_md", "") or "<missing>")
        _print_wrapped_field("Tailoring LLM JSON", row.get("tailoring_llm_json", "") or "<missing>")
        _print_wrapped_field("Operator decision", row.get("operator_decision", ""))
        _print_wrapped_field("Operator selected resume", row.get("operator_selected_resume", ""))
        _print_wrapped_field("Operator decision timestamp", row.get("operator_decision_timestamp", ""))
        _print_wrapped_field("Operator note", row.get("operator_note", ""))
        _print_packet_summary(row.get("packet_json", ""))
        print("-" * 100)

def _browse(args) -> None:
    rows = _build_job_index(Path(args.output_dir))
    selected = _select_browse_rows(rows, args)

    if not selected:
        raise SystemExit("No matching jobs found in application-planning outputs.")

    print("=" * 100)
    print("JOB APP BROWSE")
    print("=" * 100)
    _print_wrapped_field("Rows returned", len(selected))
    _print_wrapped_field("Action filter", args.action or "<any>")
    _print_wrapped_field("Needs review filter", args.needs_review or "<any>")
    _print_wrapped_field("Tie filter", args.is_tie or "<any>")
    _print_wrapped_field("Fallback status filter", args.fallback_status or "<any>")
    _print_wrapped_field("Winner bucket filter", args.winner_bucket or "<any>")
    _print_wrapped_field("Company contains", args.company_contains or "<any>")
    _print_wrapped_field("Title contains", args.title_contains or "<any>")
    _print_wrapped_field("Undecided only", args.undecided_only or "<any>")
    print()

    for row in selected:
        queue_rank = row.get("queue_rank", "")
        action = row.get("action", "")
        company = row.get("job_company", "")
        title = row.get("job_title", "")
        winner = row.get("winner_resume", "")
        winner_score = _parse_float(row.get("winner_score", "0"))
        runner_up = row.get("runner_up_resume", "")
        score_gap = _parse_float(row.get("score_gap", "0"))
        is_tie = row.get("is_tie", "")
        needs_review = row.get("needs_variant_review", "")
        fallback_best = row.get("llm_fallback_best_resume", "")
        fallback_status = row.get("llm_fallback_status", "")
        operator_decision = row.get("operator_decision", "")
        operator_selected_resume = row.get("operator_selected_resume", "")
        operator_decision_timestamp = row.get("operator_decision_timestamp", "")

        print(f"#{queue_rank} | {action} | {company} | {title}")
        print(
            f"  winner={winner or '<empty>'} | "
            f"score={winner_score:.3f} | "
            f"runner_up={runner_up or '<empty>'}"
        )
        print(
            f"  gap={score_gap:.3f} | "
            f"tie={is_tie or '<empty>'} | "
            f"review={needs_review or '<empty>'}"
        )
        print(
            f"  fallback_best={fallback_best or '<empty>'} | "
            f"fallback_status={fallback_status or '<empty>'}"
        )
        print(
            f"  operator_decision={operator_decision or '<empty>'} | "
            f"operator_selected_resume={operator_selected_resume or '<empty>'}"
        )
        print(
            f"  operator_decision_timestamp={operator_decision_timestamp or '<empty>'}"
        )
        print()

def _review(args) -> None:
    rows = _build_job_index(Path(args.output_dir))
    selected = _select_review_rows(rows, args)

    if not selected:
        raise SystemExit("No matching review rows found in application-planning outputs.")

    print("=" * 100)
    print("JOB APP REVIEW")
    print("=" * 100)

    _print_wrapped_field("Action filter", args.action or "<any>")
    _print_wrapped_field("Undecided only", args.undecided_only or "<any>")
    print()

    for row in selected:
        _print_wrapped_field("Queue rank", row.get("queue_rank", ""))
        _print_wrapped_field("Job doc id", row.get("job_doc_id", ""))
        _print_wrapped_field("Company", row.get("job_company", ""))
        _print_wrapped_field("Title", row.get("job_title", ""))
        _print_wrapped_field("Action", row.get("action", ""))
        _print_wrapped_field("Needs variant review", row.get("needs_variant_review", ""))
        _print_wrapped_field("Is tie", row.get("is_tie", ""))
        _print_wrapped_field("Queue priority reason", row.get("queue_priority_reason", ""))
        _print_wrapped_field("Operator decision", row.get("operator_decision", ""))
        _print_wrapped_field("Operator selected resume", row.get("operator_selected_resume", ""))
        _print_wrapped_field("Operator decision timestamp", row.get("operator_decision_timestamp", ""))
        _print_wrapped_field("Operator note", row.get("operator_note", ""))
        print("VARIANT COMPARISON")
        print(
            _wrap_block(
                f"winner_resume={row.get('winner_resume', '') or '<empty>'} | "
                f"winner_score={_parse_float(row.get('winner_score', '0')):.3f}"
            )
        )
        print(
            _wrap_block(
                f"runner_up_resume={row.get('runner_up_resume', '') or '<empty>'} | "
                f"runner_up_score={_parse_float(row.get('runner_up_score', '0')):.3f}"
            )
        )
        print(
            _wrap_block(
                f"score_gap={_parse_float(row.get('score_gap', '0')):.3f}"
            )
        )

        _print_wrapped_field("Tailoring markdown", row.get("tailoring_md", "") or "<missing>")
        _print_wrapped_field("Packet JSON", row.get("packet_json", "") or "<missing>")

        packet = _load_packet_json(row.get("packet_json", "")) or {}
        summary = packet.get("summary")
        selection = packet.get("selection")
        top_dimension_deltas = packet.get("top_dimension_deltas_vs_backup")
        top_relevant_bullets = packet.get("top_relevant_bullets")

        if isinstance(summary, dict):
            rationale_lines = []
            for key in ["selection_rationale", "tailoring_focus", "recruiter_summary", "job_summary"]:
                if summary.get(key):
                    rationale_lines.append(f"{key}: {summary.get(key)}")
            if rationale_lines:
                print("PACKET SUMMARY")
                for line in rationale_lines:
                    print(_wrap_block(line))
            _print_string_list("RESUME GAPS", summary.get("resume_gaps"), limit=6)
            _print_string_list("MISSING REQUIREMENTS", summary.get("missing_requirements"), limit=6)
        elif summary not in (None, "", []):
            _print_any_block("PACKET SUMMARY", summary)

        if selection:
            _print_kv_block(
                "PACKET SELECTION",
                selection,
                [
                    "winner_resume",
                    "winner_score",
                    "runner_up_resume",
                    "runner_up_score",
                    "score_gap",
                    "is_tie",
                    "needs_variant_review",
                ],
            )

        _print_dimension_deltas(top_dimension_deltas, limit=5)
        _print_relevant_bullets(top_relevant_bullets, limit=5)
        print("-" * 100)

def _decide(args) -> None:
    rows = _build_job_index(Path(args.output_dir))
    row = _find_single_job_row(rows, args)
    selected_resume = _validate_selected_resume(row, args.selected_resume)

    result = record_operator_resume_selection_payload(
        queue_rank=str(row.get("queue_rank", "") or ""),
        job_doc_id=str(row.get("job_doc_id", "") or ""),
        job_company=str(row.get("job_company", "") or ""),
        job_title=str(row.get("job_title", "") or ""),
        planning_action=str(row.get("action", "") or ""),
        decision=str(getattr(args, "decision", "SELECT_RESUME") or "SELECT_RESUME"),
        selected_resume=selected_resume,
        winner_resume=str(row.get("winner_resume", "") or ""),
        winner_score=str(row.get("winner_score", "") or ""),
        runner_up_resume=str(row.get("runner_up_resume", "") or ""),
        runner_up_score=str(row.get("runner_up_score", "") or ""),
        note=str(args.note or "").strip(),
    )

    decision_row = dict(result.get("row", {}) or {})
    postgres_write = dict(result.get("postgres_write", {}) or {})

    print("=" * 100)
    print("JOB APP DECIDE")
    print("=" * 100)
    _print_wrapped_field("Storage", "postgres")
    _print_wrapped_field("CSV write disabled", result.get("csv_write_disabled", False))
    _print_wrapped_field("Queue rank", decision_row.get("queue_rank", ""))
    _print_wrapped_field("Company", decision_row.get("job_company", ""))
    _print_wrapped_field("Title", decision_row.get("job_title", ""))
    _print_wrapped_field("Planning action", decision_row.get("planning_action", ""))
    _print_wrapped_field("Winner resume", decision_row.get("winner_resume", ""))
    _print_wrapped_field("Runner up resume", decision_row.get("runner_up_resume", ""))
    _print_wrapped_field("Selected resume", decision_row.get("selected_resume", ""))
    _print_wrapped_field("Decision", decision_row.get("decision", ""))
    _print_wrapped_field("Note", decision_row.get("note", "") or "<empty>")
    _print_wrapped_field("Postgres write attempted", postgres_write.get("attempted", False))
    _print_wrapped_field("Postgres write ok", postgres_write.get("ok", False))
    _print_wrapped_field("Decision key", postgres_write.get("decision_key", "") or "<empty>")

def _decisions(args) -> None:
    payload = decisions_payload(
        queue_rank=args.queue_rank,
        decision=args.decision,
        selected_resume=args.selected_resume,
        company_contains=args.company_contains,
        title_contains=args.title_contains,
        limit=args.limit,
    )
    selected = list(payload.get("rows", []) or [])
    resolved_filters = dict(payload.get("filters", {}) or {})

    if not selected:
        raise SystemExit("No matching operator decisions found.")

    print("=" * 100)
    print("JOB APP DECISIONS")
    print("=" * 100)
    _print_wrapped_field("Storage", "postgres")
    _print_wrapped_field("Rows returned", len(selected))
    _print_wrapped_field("Decision filter", resolved_filters.get("decision", "") or "<any>")
    _print_wrapped_field("Selected resume filter", resolved_filters.get("selected_resume", "") or "<any>")
    _print_wrapped_field("Company contains", resolved_filters.get("company_contains", "") or "<any>")
    _print_wrapped_field("Title contains", resolved_filters.get("title_contains", "") or "<any>")
    _print_wrapped_field(
        "Queue rank filter",
        resolved_filters.get("queue_rank") if resolved_filters.get("queue_rank") is not None else "<any>",
    )
    print()

    for row in selected:
        print(
            f"{row.get('decision_timestamp', '')} | "
            f"#{row.get('queue_rank', '')} | "
            f"{row.get('decision', '')} | "
            f"{row.get('job_company', '')} | "
            f"{row.get('job_title', '')}"
        )
        print(
            f"  selected_resume={row.get('selected_resume', '') or '<empty>'} | "
            f"planning_action={row.get('planning_action', '') or '<empty>'}"
        )
        print(
            f"  winner={row.get('winner_resume', '') or '<empty>'} | "
            f"runner_up={row.get('runner_up_resume', '') or '<empty>'}"
        )
        print(
            f"  note={row.get('note', '') or '<empty>'}"
        )
        print()

def _export_review_queue(args) -> None:
    rows = _build_job_index(Path(args.output_dir))
    selected = _select_review_rows(rows, args)

    if not selected:
        raise SystemExit("No matching review rows found to export.")

    export_rows = _build_review_export_rows(selected)
    export_path = Path(args.export_path)

    headers = [
        "queue_rank",
        "job_doc_id",
        "job_company",
        "job_title",
        "action",
        "needs_variant_review",
        "is_tie",
        "winner_resume",
        "winner_score",
        "runner_up_resume",
        "runner_up_score",
        "score_gap",
        "missing_requirement_count",
        "queue_priority_reason",
        "tailoring_md",
        "packet_json",
        "operator_decision",
        "operator_selected_resume",
        "operator_decision_timestamp",
        "operator_note",
    ]

    _export_csv_rows(export_path, headers, export_rows)

    print("=" * 100)
    print("JOB APP EXPORT REVIEW QUEUE")
    print("=" * 100)
    _print_wrapped_field("Export path", export_path)
    _print_wrapped_field("Rows exported", len(export_rows))
    _print_wrapped_field("Action filter", args.action or "<any>")
    _print_wrapped_field("Undecided only", args.undecided_only or "<any>")
    _print_wrapped_field("Company contains", args.company_contains or "<any>")
    _print_wrapped_field("Title contains", args.title_contains or "<any>")

def _workflow(args) -> None:
    rows = _build_job_index(Path(args.output_dir))
    selected = _workflow_view_rows(rows, args.view)[: args.limit]

    if not selected:
        raise SystemExit("No matching workflow rows found.")

    print("=" * 100)
    print("JOB APP WORKFLOW")
    print("=" * 100)
    _print_wrapped_field("View", args.view)
    _print_wrapped_field("Rows returned", len(selected))
    print()

    for row in selected:
        print(
            f"#{row.get('queue_rank', '')} | {row.get('action', '')} | "
            f"{row.get('job_company', '')} | {row.get('job_title', '')}"
        )
        print(
            f"  winner={row.get('winner_resume', '') or '<empty>'} | "
            f"runner_up={row.get('runner_up_resume', '') or '<empty>'}"
        )
        print(
            f"  winner_score={_parse_float(row.get('winner_score', '0')):.3f} | "
            f"gap={_parse_float(row.get('score_gap', '0')):.3f} | "
            f"review={row.get('needs_variant_review', '') or '<empty>'}"
        )
        print(
            f"  operator_decision={row.get('operator_decision', '') or '<empty>'} | "
            f"operator_selected_resume={row.get('operator_selected_resume', '') or '<empty>'}"
        )
        print(
            f"  reason={row.get('queue_priority_reason', '') or '<empty>'}"
        )
        print()

def _planner(args) -> None:
    inferred_view = _infer_planner_view(args.request)
    rows = _build_job_index(Path(args.output_dir))
    selected = _workflow_view_rows(rows, inferred_view)[: args.limit]

    if not selected:
        raise SystemExit("No matching planner rows found.")

    print("=" * 100)
    print("JOB APP PLANNER")
    print("=" * 100)
    _print_wrapped_field("Request", args.request)
    _print_wrapped_field("Resolved view", inferred_view)
    _print_wrapped_field("Rows returned", len(selected))
    print()

    for row in selected:
        print(
            f"#{row.get('queue_rank', '')} | {row.get('action', '')} | "
            f"{row.get('job_company', '')} | {row.get('job_title', '')}"
        )
        print(
            f"  winner={row.get('winner_resume', '') or '<empty>'} | "
            f"runner_up={row.get('runner_up_resume', '') or '<empty>'}"
        )
        print(
            f"  winner_score={_parse_float(row.get('winner_score', '0')):.3f} | "
            f"gap={_parse_float(row.get('score_gap', '0')):.3f} | "
            f"review={row.get('needs_variant_review', '') or '<empty>'}"
        )
        print(
            f"  operator_decision={row.get('operator_decision', '') or '<empty>'} | "
            f"operator_selected_resume={row.get('operator_selected_resume', '') or '<empty>'}"
        )
        print(
            f"  reason={row.get('queue_priority_reason', '') or '<empty>'}"
        )
        print()

def _rag(args) -> None:
    from src.rag.rag_executor import execute_rag_request

    payload = execute_rag_request(
        request=args.request,
        top_k=args.top_k,
        fetch_k=args.fetch_k,
        filters=None,
        output_mode=args.output_mode,
        include_diagnostics=args.include_diagnostics,
        intent_override=args.intent or None,
    )

    print("=" * 100)
    print("JOB APP RAG")
    print("=" * 100)
    _print_wrapped_field("Request", args.request)
    _print_wrapped_field("Intent override", args.intent or "<auto>")

    if "natural_intent" in payload:
        _print_wrapped_field("Natural intent", payload.get("natural_intent", ""))
    if "intent" in payload:
        _print_wrapped_field("Final intent", payload.get("intent", ""))
    if "tool_name" in payload:
        _print_wrapped_field("Tool name", payload.get("tool_name", ""))
    _print_wrapped_field("OK", payload.get("ok", False))

    warning = payload.get("warning")
    if warning:
        _print_wrapped_field("Warning", warning.get("message", ""))

    if not payload.get("ok", False):
        _print_wrapped_field("Error", payload.get("error", ""))
        _print_wrapped_field("Error type", payload.get("error_type", ""))
        suggestions = payload.get("suggestions", []) or []
        if suggestions:
            _print_wrapped_field("Suggestions", ", ".join(suggestions))
        details = payload.get("details")
        if details:
            _print_wrapped_field("Details", json.dumps(details, ensure_ascii=False))
        return

    response = payload.get("response", {}) or {}
    intent = payload.get("intent", "")

    if args.include_diagnostics and response.get("diagnostics"):
        _print_wrapped_field(
            "Diagnostics",
            json.dumps(response.get("diagnostics", {}), ensure_ascii=False),
        )

    if intent == "search_jobs":
        _print_wrapped_field("Result count", response.get("result_count", 0))
        print()
        _print_rag_search_results(response.get("results", []) or [])
        return

    if intent == "answer_job_query":
        print()
        _print_rag_answer_response(response)
        return

    _print_wrapped_field("Unhandled response", json.dumps(payload, ensure_ascii=False))

def _parse_args():
    parser = argparse.ArgumentParser(
        description="Thin operator CLI for the existing job pipeline and application-planning outputs."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser(
        "run",
        help="Run the main pipeline, optionally with downstream application planning.",
    )
    run_parser.add_argument("--run-application-planning", action="store_true")
    run_parser.add_argument("--job-limit", type=int, default=50)
    run_parser.add_argument("--job-packet-limit", type=int, default=0)
    run_parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    run_parser.add_argument("--llm-actions", default="APPLY,APPLY_REVIEW_VARIANTS")
    run_parser.add_argument("--generate-tailoring", action="store_true")
    run_parser.add_argument("--generate-llm-tailoring", action="store_true")
    run_parser.add_argument("--refresh-llm-tailoring", action="store_true")
    run_parser.add_argument("--generate-llm-fallback", action="store_true")
    run_parser.add_argument(
        "--delete-seen-data",
        choices=["ask", "yes", "no"],
        default="no",
    )

    planning_parser = subparsers.add_parser(
        "plan",
        help="Run planning-only mode against the existing exported job corpus.",
    )
    planning_parser.add_argument("--run-application-planning", action="store_true", default=True)
    planning_parser.add_argument("--job-limit", type=int, default=50)
    planning_parser.add_argument("--job-packet-limit", type=int, default=0)
    planning_parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    planning_parser.add_argument("--llm-actions", default="APPLY,APPLY_REVIEW_VARIANTS")
    planning_parser.add_argument("--generate-tailoring", action="store_true")
    planning_parser.add_argument("--generate-llm-tailoring", action="store_true")
    planning_parser.add_argument("--refresh-llm-tailoring", action="store_true")
    planning_parser.add_argument("--generate-llm-fallback", action="store_true")
    planning_parser.add_argument(
        "--delete-seen-data",
        choices=["ask", "yes", "no"],
        default="no",
    )

    status_parser = subparsers.add_parser(
        "status",
        help="Summarize the current job corpus and application-planning outputs.",
    )
    status_parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    status_parser.add_argument("--job-corpus", default=str(DEFAULT_CORPUS_PATH))
    status_parser.add_argument("--top-k", type=int, default=10)

    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Inspect one or more jobs from existing application-planning outputs.",
    )
    inspect_parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    inspect_parser.add_argument("--job-doc-id", default="")
    inspect_parser.add_argument("--queue-rank", type=int)
    inspect_parser.add_argument("--company-contains", default="")
    inspect_parser.add_argument("--title-contains", default="")
    inspect_parser.add_argument("--limit", type=int, default=5)

    browse_parser = subparsers.add_parser(
        "browse",
        help="Browse queue/planning rows with compact operator-friendly filters.",
    )
    browse_parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    browse_parser.add_argument("--action", default="")
    browse_parser.add_argument("--needs-review", default="")
    browse_parser.add_argument("--is-tie", default="")
    browse_parser.add_argument("--fallback-status", default="")
    browse_parser.add_argument("--winner-bucket", default="")
    browse_parser.add_argument("--company-contains", default="")
    browse_parser.add_argument("--title-contains", default="")
    browse_parser.add_argument("--limit", type=int, default=20)
    browse_parser.add_argument("--undecided-only", default="")

    review_parser = subparsers.add_parser(
        "review",
        help="Review tied or manual-variant-selection rows in a decision-friendly format.",
    )
    review_parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    review_parser.add_argument("--queue-rank", type=int)
    review_parser.add_argument("--job-doc-id", default="")
    review_parser.add_argument("--company-contains", default="")
    review_parser.add_argument("--title-contains", default="")
    review_parser.add_argument("--include-non-review", action="store_true")
    review_parser.add_argument("--limit", type=int, default=5)
    review_parser.add_argument("--action", default="")
    review_parser.add_argument("--undecided-only", default="")

    decide_parser = subparsers.add_parser(
    "decide",
    help="Record the selected resume variant for one reviewed queue row.",
    )
    decide_parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    decide_parser.add_argument("--queue-rank", type=int)
    decide_parser.add_argument("--job-doc-id", default="")
    decide_parser.add_argument("--company-contains", default="")
    decide_parser.add_argument("--title-contains", default="")
    decide_parser.add_argument(
        "--selected-resume",
        required=True,
        help="Chosen resume variant. Must match the winner or runner-up resume when both are present.",
    )
    decide_parser.add_argument(
        "--decision",
        default="SELECT_RESUME",
        choices=["SELECT_RESUME"],
    )
    decide_parser.add_argument("--note", default="")

    decisions_parser = subparsers.add_parser(
        "decisions",
        help="Browse previously recorded operator decisions.",
    )
    decisions_parser.add_argument("--queue-rank", type=int)
    decisions_parser.add_argument("--decision", default="")
    decisions_parser.add_argument("--selected-resume", default="")
    decisions_parser.add_argument("--company-contains", default="")
    decisions_parser.add_argument("--title-contains", default="")
    decisions_parser.add_argument("--limit", type=int, default=20)

    export_review_parser = subparsers.add_parser(
        "export-review-queue",
        help="Export the current decision-aware human review queue to CSV.",
    )
    export_review_parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    export_review_parser.add_argument("--export-path", default=str(DEFAULT_REVIEW_EXPORT_PATH))
    export_review_parser.add_argument("--queue-rank", type=int)
    export_review_parser.add_argument("--job-doc-id", default="")
    export_review_parser.add_argument("--company-contains", default="")
    export_review_parser.add_argument("--title-contains", default="")
    export_review_parser.add_argument("--include-non-review", action="store_true")
    export_review_parser.add_argument("--action", default="")
    export_review_parser.add_argument("--undecided-only", default="true")
    export_review_parser.add_argument("--limit", type=int, default=500)

    rag_parser = subparsers.add_parser(
        "rag",
        help="Query the local job RAG layer through the existing executor.",
    )
    rag_parser.add_argument("request")
    rag_parser.add_argument(
        "--intent",
        default="",
        choices=["", "search_jobs", "answer_job_query"],
        help="Optional intent override. Leave blank for automatic routing.",
    )
    rag_parser.add_argument("--top-k", type=int, default=5)
    rag_parser.add_argument("--fetch-k", type=int, default=15)
    rag_parser.add_argument("--output-mode", default="compact", choices=["compact", "full"])
    rag_parser.add_argument("--include-diagnostics", action="store_true")

    workflow_parser = subparsers.add_parser(
        "workflow",
        help="Query planning and decision workflow views from merged operator data.",
    )
    workflow_parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    workflow_parser.add_argument(
        "--view",
        required=True,
        choices=[
            "undecided_apply_review",
            "undecided_maybe_tailor",
            "runner_up_selected",
            "direct_apply_pending",
        ],
    )
    workflow_parser.add_argument("--limit", type=int, default=20)

    planner_parser = subparsers.add_parser(
        "planner",
        help="Resolve simple natural-language planning questions into deterministic workflow views.",
    )
    planner_parser.add_argument("request")
    planner_parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    planner_parser.add_argument("--limit", type=int, default=20)

    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    if args.command == "run":
        _run_cmd(_build_main_cmd(args, planning_only=False))
        return

    if args.command == "plan":
        _run_cmd(_build_main_cmd(args, planning_only=True))
        return

    if args.command == "status":
        _status(args)
        return

    if args.command == "inspect":
        _inspect(args)
        return

    if args.command == "browse":
        _browse(args)
        return
    
    if args.command == "review":
        _review(args)
        return
    
    if args.command == "decide":
        _decide(args)
        return
    
    if args.command == "decisions":
        _decisions(args)
        return

    if args.command == "export-review-queue":
        _export_review_queue(args)
        return

    if args.command == "rag":
        _rag(args)
        return
    
    if args.command == "workflow":
        _workflow(args)
        return

    if args.command == "planner":
        _planner(args)
        return

    raise SystemExit(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    main()