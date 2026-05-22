import argparse
import csv
from pathlib import Path
from typing import List

from src.config.settings import SCORER_V2_POLICY

SHORTLIST_POLICY = SCORER_V2_POLICY["shortlist"]

HIGH_CONFIDENCE_APPLY_SCORE = SHORTLIST_POLICY["high_confidence_apply_score"]
STRONG_TIE_REVIEW_SCORE = SHORTLIST_POLICY["strong_tie_review_score"]
GOOD_MATCH_SCORE = SHORTLIST_POLICY["good_match_score"]
MAX_DIRECT_APPLY_MISSING_REQUIREMENTS = SHORTLIST_POLICY["max_direct_apply_missing_requirements"]
MAX_STRONG_TIE_MISSING_REQUIREMENTS = SHORTLIST_POLICY["max_strong_tie_missing_requirements"]
BORDERLINE_SCORE = SHORTLIST_POLICY["borderline_score"]
BORDERLINE_LOW_PASS_RATE = SHORTLIST_POLICY["borderline_low_pass_rate"]

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

def _resolved_resume(row: dict) -> str:
    return str(
        row.get("resolved_resume", "") or row.get("winner_resume", "")
    ).strip()


def _resolved_score(row: dict) -> float:
    raw = str(row.get("resolved_score", "") or "").strip()
    if raw:
        return _parse_float(raw)
    return _parse_float(row.get("winner_score", "0"))


def _resolved_bucket(row: dict) -> str:
    raw = str(row.get("resolved_bucket", "") or "").strip()
    if raw:
        return _normalize_text(raw)
    return _normalize_text(row.get("winner_bucket", ""))


def _resolved_top_dims(row: dict) -> str:
    return str(
        row.get("resolved_top_dims", "") or row.get("winner_top_dims", "")
    ).strip()


def _resolved_missing_requirements(row: dict) -> str:
    return str(
        row.get("resolved_missing_requirements", "") or row.get("winner_missing_requirements", "")
    ).strip()


def _resolved_matched_terms(row: dict) -> str:
    return str(
        row.get("resolved_matched_terms", "") or row.get("winner_matched_terms", "")
    ).strip()


def _resolved_resume_source(row: dict) -> str:
    raw = str(row.get("resolved_resume_source", "") or "").strip()
    if raw:
        return raw
    return "deterministic_winner" if _resolved_resume(row) else ""


def _resolved_selection_status(row: dict) -> str:
    raw = str(row.get("resolved_selection_status", "") or "").strip()
    if raw:
        return raw
    return "resolved" if _resolved_resume(row) else "unresolved"


def _variant_review_required(row: dict) -> bool:
    raw = str(row.get("variant_review_required", "") or "").strip()
    if raw:
        return _parse_bool(raw)

    if _parse_bool(row.get("requires_manual_review", "false")):
        return True

    return _selection_signal(row) in {"effective_tie", "manual_review_close_call"} or _parse_bool(row.get("is_tie", "false"))


def _resolved_best_available_imperfect_match(row: dict) -> bool:
    return _parse_bool(row.get("resolved_best_available_imperfect_match", "false"))


def _source_label(source: str) -> str:
    return str(source or "").replace("_", " ").strip() or "selector"

def _requires_manual_review(row: dict) -> bool:
    return _variant_review_required(row)

def _classify_action(row: dict) -> tuple[str, str]:
    resolved_resume = _resolved_resume(row)
    resolved_score = _resolved_score(row)
    resolved_bucket = _resolved_bucket(row)
    resolved_top_dims = _resolved_top_dims(row)
    resolved_missing_requirements = _resolved_missing_requirements(row)
    resolved_resume_source = _resolved_resume_source(row)
    resolved_selection_status = _resolved_selection_status(row)
    variant_review_required = _variant_review_required(row)
    best_available_imperfect_match = _resolved_best_available_imperfect_match(row)

    score_gap = _parse_float(row.get("score_gap", "0"))
    selection_signal = _selection_signal(row)
    passed_prefilter = int(row.get("passed_prefilter", "0"))
    resume_variants_considered = int(row.get("resume_variants_considered", "0"))
    missing_count = _count_missing_requirements(resolved_missing_requirements)

    pass_rate = (
        passed_prefilter / resume_variants_considered
        if resume_variants_considered > 0
        else 0.0
    )

    if not resolved_resume or resolved_bucket == "filtered_out":
        return (
            "SKIP_FOR_NOW",
            f"No resolved resume selection is available (status={resolved_selection_status}, source={resolved_resume_source or 'none'}).",
        )

    if best_available_imperfect_match:
        if resolved_score >= GOOD_MATCH_SCORE:
            return (
                "MAYBE_TAILOR",
                f"Resolved via { _source_label(resolved_resume_source) } as a best-available imperfect match (score {resolved_score:.3f}); tailor carefully before applying.",
            )
        return (
            "SKIP_FOR_NOW",
            f"Only a best-available imperfect fallback match was available via { _source_label(resolved_resume_source) } and the score remains weak ({resolved_score:.3f}).",
        )

    if variant_review_required:
        if (
            resolved_score >= STRONG_TIE_REVIEW_SCORE
            and missing_count <= MAX_STRONG_TIE_MISSING_REQUIREMENTS
        ):
            return (
                "APPLY_REVIEW_VARIANTS",
                f"Strong match ({resolved_score:.3f}) but resume choice is still unresolved (source={resolved_resume_source}, signal={selection_signal}, gap {score_gap:.3f}); review top variants before applying.",
            )

        if resolved_score >= GOOD_MATCH_SCORE:
            return (
                "MAYBE_TAILOR",
                f"Good match ({resolved_score:.3f}) but resume choice is still unresolved (source={resolved_resume_source}, signal={selection_signal}); tailor and review manually.",
            )

        if resolved_score >= BORDERLINE_SCORE and pass_rate < BORDERLINE_LOW_PASS_RATE:
            return (
                "MAYBE_TAILOR",
                f"Borderline score ({resolved_score:.3f}) and unresolved variant choice (source={resolved_resume_source}, signal={selection_signal}); worth manual review.",
            )

        return (
            "SKIP_FOR_NOW",
            f"Resume choice is still unresolved (source={resolved_resume_source}, signal={selection_signal}) and the current score is too weak ({resolved_score:.3f}).",
        )

    if (
        resolved_score >= HIGH_CONFIDENCE_APPLY_SCORE
        and missing_count <= MAX_DIRECT_APPLY_MISSING_REQUIREMENTS
    ):
        return (
            "APPLY",
            f"Resolved resume selection via { _source_label(resolved_resume_source) } with strong score ({resolved_score:.3f}) and manageable missing requirements ({missing_count}).",
        )

    if resolved_score >= GOOD_MATCH_SCORE:
        return (
            "MAYBE_TAILOR",
            f"Resolved resume selection via { _source_label(resolved_resume_source) } with a good score ({resolved_score:.3f}); tailor around the missing requirements ({missing_count}).",
        )

    if resolved_score >= BORDERLINE_SCORE and pass_rate < BORDERLINE_LOW_PASS_RATE:
        return (
            "MAYBE_TAILOR",
            f"Resolved resume selection via { _source_label(resolved_resume_source) } with a borderline score ({resolved_score:.3f}) but selective pass rate ({pass_rate:.2%}); worth manual review.",
        )

    return (
        "SKIP_FOR_NOW",
        f"Resolved resume selection exists via { _source_label(resolved_resume_source) }, but the score is still too weak ({resolved_score:.3f}).",
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
        resolved_resume = _resolved_resume(row)
        resolved_score = (
            str(row.get("resolved_score", "") or "").strip()
            or row.get("winner_score", "")
        )
        resolved_bucket = (
            str(row.get("resolved_bucket", "") or "").strip()
            or row.get("winner_bucket", "")
        )
        resolved_top_dims = _resolved_top_dims(row)
        resolved_missing_requirements = _resolved_missing_requirements(row)
        resolved_matched_terms = _resolved_matched_terms(row)
        resolved_resume_source = _resolved_resume_source(row)
        resolved_selection_status = _resolved_selection_status(row)
        variant_review_required = str(_variant_review_required(row))
        resolved_best_available_imperfect_match = str(
            _resolved_best_available_imperfect_match(row)
        )

        shortlist_rows.append(
            {
                "job_doc_id": row["job_doc_id"],
                "job_company": row["job_company"],
                "job_title": row["job_title"],
                "job_location": row.get("job_location", ""),
                "posted_at": row.get("posted_at", ""),
                "freshness_status": row.get("freshness_status", ""),
                "ashby_timestamp_status": row.get("ashby_timestamp_status", ""),
                "action": action,
                "action_rationale": rationale,

                # Primary resolved selection view for downstream consumers
                "winner_resume": resolved_resume,
                "winner_score": resolved_score,
                "winner_bucket": resolved_bucket,
                "winner_top_dims": resolved_top_dims,
                "winner_missing_requirements": resolved_missing_requirements,
                "winner_matched_terms": resolved_matched_terms,
                "recommendation_summary": rationale,

                # Resolution metadata
                "resolved_resume": resolved_resume,
                "resolved_score": resolved_score,
                "resolved_bucket": resolved_bucket,
                "resolved_top_dims": resolved_top_dims,
                "resolved_missing_requirements": resolved_missing_requirements,
                "resolved_matched_terms": resolved_matched_terms,
                "resolved_resume_source": resolved_resume_source,
                "resolved_selection_status": resolved_selection_status,
                "variant_review_required": variant_review_required,
                "resolved_best_available_imperfect_match": resolved_best_available_imperfect_match,

                # Original selector winner retained for audit
                "selector_winner_resume": row["winner_resume"],
                "selector_winner_score": row["winner_score"],
                "selector_winner_bucket": row["winner_bucket"],
                "selector_winner_top_dims": row["winner_top_dims"],
                "selector_winner_missing_requirements": row["winner_missing_requirements"],
                "selector_winner_matched_terms": row["winner_matched_terms"],
                "selector_recommendation_summary": row["recommendation_summary"],

                # Raw selector ambiguity fields retained for audit/backward compatibility
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

                # LLM adjudication audit
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

                # LLM fallback audit
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

    output_csv_path.parent.mkdir(parents=True, exist_ok=True)

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
            f"variant_review_required={row['variant_review_required']} | "
            f"source={row['resolved_resume_source']}"
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
