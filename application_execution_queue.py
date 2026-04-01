import argparse
import csv
from pathlib import Path
from typing import List


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

def _requires_manual_review(row: dict) -> bool:
    if _parse_bool(row.get("requires_manual_review", "false")):
        return True
    return str(row.get("selection_signal", "")).strip() == "manual_review_close_call"

def _action_rank(action: str) -> int:
    order = {
        "APPLY": 0,
        "APPLY_REVIEW_VARIANTS": 1,
        "MAYBE_TAILOR": 2,
        "SKIP_FOR_NOW": 3,
    }
    return order.get(action, 99)


def _tie_review_rank(row: dict) -> int:
    action = row.get("action", "")
    is_tie = _parse_bool(row.get("is_tie", "false"))
    requires_manual_review = _requires_manual_review(row)

    if action == "APPLY_REVIEW_VARIANTS":
        return 0
    if action == "MAYBE_TAILOR" and (is_tie or requires_manual_review):
        return 1
    return 2

def _needs_variant_review(row: dict) -> str:
    action = row.get("action", "")
    is_tie = _parse_bool(row.get("is_tie", "false"))
    requires_manual_review = _requires_manual_review(row)

    if action == "APPLY_REVIEW_VARIANTS":
        return "True"
    if action == "MAYBE_TAILOR" and (is_tie or requires_manual_review):
        return "True"
    return "False"

def _queue_priority_reason(row: dict) -> str:
    action = row.get("action", "")
    is_tie = _parse_bool(row.get("is_tie", "false"))
    requires_manual_review = _requires_manual_review(row)
    selection_signal = str(row.get("selection_signal", "")).strip()

    if action == "APPLY":
        return "Highest-priority direct apply candidate."
    if action == "APPLY_REVIEW_VARIANTS":
        if is_tie:
            return "Strong apply candidate, but tied resume variants need manual selection."
        if requires_manual_review:
            return f"Strong apply candidate, but winner versus backup is a selector close call ({selection_signal}); manual variant selection is required."
        return "Strong apply candidate that still requires operator review."
    if action == "MAYBE_TAILOR" and is_tie:
        return "Tailor candidate with tied resume variants; variant choice should be reviewed."
    if action == "MAYBE_TAILOR" and requires_manual_review:
        return f"Tailor candidate with a selector close-call winner ({selection_signal}); review the top resume options before applying."
    if action == "MAYBE_TAILOR":
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
    fieldnames = [
        "queue_rank",
        "action_rank",
        "tie_review_rank",
        "needs_variant_review",
        "missing_requirement_count",
        "queue_priority_reason",
        "job_doc_id",
        "job_company",
        "job_title",
        "posted_at",    
        "action",
        "action_rationale",
        "winner_resume",
        "winner_score",
        "winner_bucket",
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
        "winner_top_dims",
        "winner_missing_requirements",
        "winner_matched_terms",
        "recommendation_summary",
    ]

    with output_csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in queue_rows:
            writer.writerow(row)

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
            f"is_tie={row['is_tie']} | "
            f"needs_variant_review={row['needs_variant_review']}"
        )
        print(
            f"Missing requirements: {row['missing_requirement_count']} | "
            f"gap={_parse_float(row['score_gap']):.3f}"
        )
        print(f"Priority reason: {row['queue_priority_reason']}")
        print()
        

if __name__ == "__main__":
    main()