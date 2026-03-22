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

def _selection_signal(row: dict) -> str:
    return str(row.get("selection_signal", "")).strip()


def _requires_manual_review(row: dict) -> bool:
    if _parse_bool(row.get("requires_manual_review", "false")):
        return True
    return _selection_signal(row) == "manual_review_close_call"

HIGH_CONFIDENCE_APPLY_SCORE = 0.70
STRONG_TIE_REVIEW_SCORE = 0.64
GOOD_MATCH_SCORE = 0.58
MAX_DIRECT_APPLY_MISSING_REQUIREMENTS = 4
MAX_STRONG_TIE_MISSING_REQUIREMENTS = 4

def _classify_action(row: dict) -> tuple[str, str]:
    winner_score = _parse_float(row.get("winner_score", "0"))
    score_gap = _parse_float(row.get("score_gap", "0"))
    is_tie = _parse_bool(row.get("is_tie", "false"))
    requires_manual_review = _requires_manual_review(row)
    selection_signal = _selection_signal(row)
    passed_prefilter = int(row.get("passed_prefilter", "0"))
    filtered_out = int(row.get("filtered_out", "0"))
    resume_variants_considered = int(row.get("resume_variants_considered", "0"))
    missing_count = _count_missing_requirements(row.get("winner_missing_requirements", ""))

    winner_resume = str(row.get("winner_resume", "")).strip()
    winner_bucket = _normalize_text(row.get("winner_bucket", ""))

    if passed_prefilter == 0 or winner_bucket == "filtered_out" or not winner_resume:
        return (
            "SKIP_FOR_NOW",
            "No credible deterministic resume match; all resume variants failed prefilter.",
        )

    pass_rate = (
        passed_prefilter / resume_variants_considered
        if resume_variants_considered > 0
        else 0.0
    )

    if (
        winner_score >= HIGH_CONFIDENCE_APPLY_SCORE
        and not is_tie
        and not requires_manual_review
        and missing_count <= MAX_DIRECT_APPLY_MISSING_REQUIREMENTS
    ):
        return (
            "APPLY",
            f"High winner score ({winner_score:.3f}), clear lead over backup (gap {score_gap:.3f}), and manageable missing requirements ({missing_count}).",
        )

    if (
        winner_score >= STRONG_TIE_REVIEW_SCORE
        and missing_count <= MAX_STRONG_TIE_MISSING_REQUIREMENTS
        and (is_tie or requires_manual_review)
    ):
        if is_tie:
            return (
                "APPLY_REVIEW_VARIANTS",
                f"Strong deterministic match ({winner_score:.3f}) but top variants are effectively tied (gap {score_gap:.3f}); review the tied resume options before applying.",
            )
        return (
            "APPLY_REVIEW_VARIANTS",
            f"Strong deterministic match ({winner_score:.3f}) but winner versus backup is a selector close call (gap {score_gap:.3f}, signal={selection_signal}); review the top resume options before applying.",
        )

    if winner_score >= GOOD_MATCH_SCORE:
        if requires_manual_review:
            return (
                "MAYBE_TAILOR",
                f"Good deterministic match ({winner_score:.3f}) but the winner is a selector close call versus the backup (gap {score_gap:.3f}, signal={selection_signal}); tailor and review the top resume options manually.",
            )
        if is_tie:
            return (
                "MAYBE_TAILOR",
                f"Good deterministic match ({winner_score:.3f}) but the top resume options are effectively tied (gap {score_gap:.3f}); tailor and review the tied variants manually.",
            )
        return (
            "MAYBE_TAILOR",
            f"Good deterministic match ({winner_score:.3f}) but not decisive enough for a straight apply; tailor around the missing requirements ({missing_count}).",
        )

    if winner_score >= 0.50 and pass_rate < 0.50:
        if requires_manual_review:
            return (
                "MAYBE_TAILOR",
                f"Borderline score ({winner_score:.3f}) and selector close call versus backup (gap {score_gap:.3f}, signal={selection_signal}); worth manual review.",
            )
        if is_tie:
            return (
                "MAYBE_TAILOR",
                f"Borderline score ({winner_score:.3f}) and top resume options are effectively tied (gap {score_gap:.3f}, pass rate {pass_rate:.2%}); review the tied variants manually.",
            )
        return (
            "MAYBE_TAILOR",
            f"Borderline score ({winner_score:.3f}) but the job was selective across resume variants (pass rate {pass_rate:.2%}); worth reviewing manually.",
        )

    return (
        "SKIP_FOR_NOW",
        f"Winner score is too weak ({winner_score:.3f}) for a confident application recommendation.",
    )


def _action_rank(action: str) -> int:
    order = {
        "APPLY": 0,
        "APPLY_REVIEW_VARIANTS": 1,
        "MAYBE_TAILOR": 2,
        "SKIP_FOR_NOW": 3,
    }
    return order.get(action, 99)


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
        description="Build an application shortlist from batch resume-variant selector CSV output."
    )
    parser.add_argument(
        "--input-csv",
        default="best_resume_variant_by_job.csv",
        help="Path to the batch selector CSV.",
    )
    parser.add_argument(
        "--output-csv",
        default="application_shortlist_by_job.csv",
        help="Path to write the application shortlist CSV.",
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
        "--top-k-console",
        type=int,
        default=15,
        help="How many shortlist rows to print to the console.",
    )
    args = parser.parse_args()

    rows = _load_rows(Path(args.input_csv))

    if args.company_contains.strip():
        needle = _normalize_text(args.company_contains)
        rows = [
            row for row in rows
            if needle in _normalize_text(row.get("job_company", ""))
        ]

    if args.title_contains.strip():
        needle = _normalize_text(args.title_contains)
        rows = [
            row for row in rows
            if needle in _normalize_text(row.get("job_title", ""))
        ]

    if not rows:
        raise RuntimeError("No rows matched the provided filters.")

    shortlist_rows = []

    for row in rows:
        action, rationale = _classify_action(row)
        shortlist_rows.append(
            {
                "job_doc_id": row["job_doc_id"],
                "job_company": row["job_company"],
                "job_title": row["job_title"],
                "action": action,
                "action_rationale": rationale,
                "winner_resume": row["winner_resume"],
                "winner_score": row["winner_score"],
                "winner_bucket": row["winner_bucket"],
                "selection_signal": row.get("selection_signal", ""),
                "requires_manual_review": row.get("requires_manual_review", ""),
                "manual_review_gap_epsilon": row.get("manual_review_gap_epsilon", ""),
                "is_tie": row["is_tie"],
                "tie_epsilon": row["tie_epsilon"],
                "runner_up_resume": row["runner_up_resume"],
                "runner_up_score": row["runner_up_score"],
                "score_gap": row["score_gap"],
                "passed_prefilter": row["passed_prefilter"],
                "filtered_out": row["filtered_out"],
                "winner_top_dims": row["winner_top_dims"],
                "winner_missing_requirements": row["winner_missing_requirements"],
                "winner_matched_terms": row["winner_matched_terms"],
                "recommendation_summary": row["recommendation_summary"],
            }
        )

    shortlist_rows.sort(
        key=lambda row: (
            _action_rank(row["action"]),
            -_parse_float(row["winner_score"]),
            row["job_company"].lower(),
            row["job_title"].lower(),
        )
    )

    output_csv_path = Path(args.output_csv)
    fieldnames = [
        "job_doc_id",
        "job_company",
        "job_title",
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
        for row in shortlist_rows:
            writer.writerow(row)

    print("=" * 100)
    print("APPLICATION SHORTLIST BY JOB")
    print("=" * 100)
    print(f"Input CSV : {args.input_csv}")
    print(f"Output CSV: {output_csv_path}")
    print(f"Jobs kept : {len(shortlist_rows)}")
    print()

    for row in shortlist_rows[:args.top_k_console]:
        print("-" * 100)
        print(f"{row['action']} | {row['job_company']} | {row['job_title']}")
        print(
            f"Winner: {row['winner_resume']} | "
            f"score={_parse_float(row['winner_score']):.3f} | "
            f"bucket={row['winner_bucket']} | "
            f"selection={row['selection_signal']} | "
            f"requires_manual_review={row['requires_manual_review']}"
        )
        if row["runner_up_resume"]:
            print(
                f"Backup: {row['runner_up_resume']} | "
                f"score={_parse_float(row['runner_up_score']):.3f} | "
                f"gap={_parse_float(row['score_gap']):.3f} | "
                f"is_tie={row['is_tie']}"
            )
        print(f"Rationale: {row['action_rationale']}")
        if row["winner_missing_requirements"]:
            print(f"Missing requirements: {row['winner_missing_requirements']}")
        print(f"Summary: {row['recommendation_summary']}")
        print()


if __name__ == "__main__":
    main()