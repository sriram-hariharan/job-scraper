import argparse
import csv
from pathlib import Path
from typing import List

from src.config.settings import APPLICATION_EXECUTION_QUEUE_POLICY

ACTION_RANK_POLICY = APPLICATION_EXECUTION_QUEUE_POLICY["action_rank"]
TIE_REVIEW_RANK_POLICY = APPLICATION_EXECUTION_QUEUE_POLICY["tie_review_rank"]

def _parse_bool(value: str) -> bool:
    return str(value).strip().lower() == "true"


def _parse_float(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _count_missing_requirements(value: str) -> int:
    text = str(value or "").strip()
    if not text:
        return 0
    return len([part for part in text.split("|") if part.strip()])


def _normalize_text(value: str) -> str:
    return " ".join(str(value or "").lower().split()).strip()

def _variant_review_required(row: dict) -> bool:
    raw = str(row.get("variant_review_required", "") or "").strip()
    if raw:
        return _parse_bool(raw)

    if _parse_bool(row.get("requires_manual_review", "false")):
        return True

    selection_signal = str(row.get("selection_signal", "") or "").strip()
    return selection_signal in {"effective_tie", "manual_review_close_call"} or _parse_bool(
        row.get("is_tie", "false")
    )


def _resolved_resume_source(row: dict) -> str:
    return str(row.get("resolved_resume_source", "") or "").strip()


def _resolved_selection_status(row: dict) -> str:
    return str(row.get("resolved_selection_status", "") or "").strip()


def _action_rank(action: str) -> int:
    return int(ACTION_RANK_POLICY.get(action, ACTION_RANK_POLICY["__default__"]))


def _tie_review_rank(row: dict) -> int:
    action = row.get("action", "")
    variant_review_required = _variant_review_required(row)

    if action == "APPLY_REVIEW_VARIANTS":
        return int(TIE_REVIEW_RANK_POLICY["apply_review_variants"])
    if action == "MAYBE_TAILOR" and variant_review_required:
        return int(TIE_REVIEW_RANK_POLICY["maybe_tailor_variant_review"])
    return int(TIE_REVIEW_RANK_POLICY["default"])


def _needs_variant_review(row: dict) -> str:
    action = row.get("action", "")
    variant_review_required = _variant_review_required(row)

    if action == "APPLY_REVIEW_VARIANTS" and variant_review_required:
        return "True"
    if action == "MAYBE_TAILOR" and variant_review_required:
        return "True"
    return "False"


def _queue_priority_reason(row: dict) -> str:
    action = row.get("action", "")
    variant_review_required = _variant_review_required(row)
    selection_signal = str(row.get("selection_signal", "")).strip()
    resolved_resume_source = _resolved_resume_source(row)
    resolved_selection_status = _resolved_selection_status(row)

    if action == "APPLY":
        if resolved_resume_source and resolved_resume_source != "deterministic_winner":
            return f"Highest-priority apply candidate resolved via {resolved_resume_source}."
        return "Highest-priority direct apply candidate."

    if action == "APPLY_REVIEW_VARIANTS":
        if variant_review_required:
            return (
                f"Strong apply candidate, but resume choice is still unresolved "
                f"(status={resolved_selection_status or 'unresolved'}, "
                f"source={resolved_resume_source or selection_signal or 'selector'})."
            )
        return "Strong apply candidate that still requires operator review."

    if action == "MAYBE_TAILOR":
        if variant_review_required:
            return (
                f"Tailor candidate with unresolved variant choice "
                f"(status={resolved_selection_status or 'unresolved'}, "
                f"source={resolved_resume_source or selection_signal or 'selector'})."
            )
        if resolved_resume_source and resolved_resume_source != "deterministic_winner":
            return f"Tailor candidate resolved via {resolved_resume_source}."
        return "Tailor before applying."

    return "Low-priority hold."

def _load_rows(csv_path: Path) -> List[dict]:
    if not csv_path.exists():
        raise RuntimeError(f"Missing CSV: {csv_path}")

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        raise RuntimeError(f"CSV is empty: {csv_path}")

    return rows


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a ranked application execution queue from the shortlist CSV."
    )
    parser.add_argument(
        "--input-csv",
        default="application_shortlist_by_job.csv",
        help="Path to the shortlist CSV.",
    )
    parser.add_argument(
        "--output-csv",
        default="application_execution_queue.csv",
        help="Path to write the execution queue CSV.",
    )
    parser.add_argument(
        "--top-k-console",
        type=int,
        default=15,
        help="How many queue rows to print to the console.",
    )
    args = parser.parse_args()

    rows = _load_rows(Path(args.input_csv))

    queue_rows = []
    for row in rows:
        missing_requirement_count = _count_missing_requirements(
            row.get("winner_missing_requirements", "")
        )
        queue_rows.append(
            {
                **row,
                "action_rank": str(_action_rank(row.get("action", ""))),
                "tie_review_rank": str(_tie_review_rank(row)),
                "needs_variant_review": _needs_variant_review(row),
                "missing_requirement_count": str(missing_requirement_count),
                "queue_priority_reason": _queue_priority_reason(row),
            }
        )

    queue_rows.sort(
        key=lambda row: (
            int(row["action_rank"]),
            int(row["tie_review_rank"]),
            -_parse_float(row.get("winner_score", "0")),
            int(row["missing_requirement_count"]),
            -_parse_float(row.get("score_gap", "0")),
            _normalize_text(row.get("job_company", "")),
            _normalize_text(row.get("job_title", "")),
        )
    )

    for idx, row in enumerate(queue_rows, start=1):
        row["queue_rank"] = str(idx)

    output_csv_path = Path(args.output_csv)
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)

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
    "action_rationale",

    "winner_resume",
    "winner_score",
    "winner_bucket",
    "winner_top_dims",
    "winner_missing_requirements",
    "winner_matched_terms",
    "recommendation_summary",

    "resolved_resume",
    "resolved_score",
    "resolved_bucket",
    "resolved_top_dims",
    "resolved_missing_requirements",
    "resolved_matched_terms",
    "resolved_resume_source",
    "resolved_selection_status",
    "variant_review_required",
    "resolved_best_available_imperfect_match",

    "selector_winner_resume",
    "selector_winner_score",
    "selector_winner_bucket",
    "selector_winner_top_dims",
    "selector_winner_missing_requirements",
    "selector_winner_matched_terms",
    "selector_recommendation_summary",

    "selection_signal",
    "requires_manual_review",
    "manual_review_gap_epsilon",
    "is_tie",
    "tie_epsilon",
    "runner_up_resume",
    "runner_up_score",
    "score_gap",
    "passed_prefilter",
    "filtered_out",

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

    "llm_fallback_best_resume",
    "llm_fallback_best_score",
    "llm_fallback_backup_resume",
    "llm_fallback_backup_score",
    "llm_fallback_confidence",
    "llm_fallback_reason",
    "llm_fallback_status",
    "llm_fallback_parse_ok",
    "llm_fallback_provider",
    "llm_fallback_model",
    "llm_fallback_cache_hit",
    "llm_fallback_error_type",
]

    with output_csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in queue_rows:
            output_row = {name: row.get(name, "") for name in fieldnames}
            writer.writerow(output_row)

    print("=" * 100)
    print("APPLICATION EXECUTION QUEUE")
    print("=" * 100)
    print(f"Input CSV : {args.input_csv}")
    print(f"Output CSV: {output_csv_path}")
    print(f"Jobs kept : {len(queue_rows)}")
    print()

    for row in queue_rows[:args.top_k_console]:
        print("-" * 100)
        print(
            f"#{row['queue_rank']} | {row['action']} | "
            f"{row['job_company']} | {row['job_title']}"
        )
        print(
            f"Winner: {row['winner_resume']} | "
            f"score={_parse_float(row['winner_score']):.3f} | "
            f"selection={row.get('selection_signal', '')} | "
            f"resolved_source={row.get('resolved_resume_source', '')} | "
            f"needs_variant_review={row['needs_variant_review']}"
        )
        print(
            f"Missing requirements: {row['missing_requirement_count']} | "
            f"gap={_parse_float(row['score_gap']):.3f}"
        )
        print(f"Priority reason: {row['queue_priority_reason']}")
        print()
    
        if row.get("llm_adjudication_resume", ""):
            print(
                f"LLM adjudication: {row['llm_adjudication_resume']} | "
                f"confidence={row.get('llm_adjudication_confidence', '')} | "
                f"differs_from_deterministic={row.get('llm_adjudication_differs_from_deterministic', '')}"
            )
            if row.get("llm_adjudication_reason", ""):
                print(f"LLM adjudication reason: {row['llm_adjudication_reason']}")
        

if __name__ == "__main__":
    main()
