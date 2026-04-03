import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List


def _text(value: Any) -> str:
    return str(value or "").strip()


def _boolish(value: Any) -> bool:
    return _text(value).lower() in {"1", "true", "yes", "y"}


def _read_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing CSV: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _is_empty(value: Any) -> bool:
    return _text(value) == ""


def _required_columns() -> List[str]:
    return [
        "job_doc_id",
        "job_company",
        "job_title",
        "winner_resume",
        "winner_score",
        "runner_up_resume",
        "runner_up_score",
        "score_gap",
        "is_tie",
        "selection_signal",
        "requires_manual_review",
        "llm_fallback_best_resume",
        "llm_fallback_best_score",
        "llm_fallback_backup_resume",
        "llm_fallback_backup_score",
        "llm_fallback_status",
        "llm_adjudication_resume",
        "llm_adjudication_status",
        "llm_adjudication_differs_from_deterministic",
    ]


def _row_label(row: Dict[str, str]) -> str:
    return " | ".join(
        [
            _text(row.get("job_company")),
            _text(row.get("job_title")),
            _text(row.get("job_doc_id")),
        ]
    )


def _validate_row(row: Dict[str, str]) -> List[str]:
    issues: List[str] = []

    selection_signal = _text(row.get("selection_signal"))
    is_tie = _boolish(row.get("is_tie"))
    requires_manual_review = _boolish(row.get("requires_manual_review"))

    winner_resume = _text(row.get("winner_resume"))
    runner_up_resume = _text(row.get("runner_up_resume"))

    llm_fallback_best_resume = _text(row.get("llm_fallback_best_resume"))
    llm_fallback_backup_resume = _text(row.get("llm_fallback_backup_resume"))
    llm_fallback_status = _text(row.get("llm_fallback_status"))

    llm_adjudication_resume = _text(row.get("llm_adjudication_resume"))
    llm_adjudication_status = _text(row.get("llm_adjudication_status"))
    llm_adjudication_differs = _text(row.get("llm_adjudication_differs_from_deterministic")).lower()

    valid_signals = {
        "no_credible_match",
        "effective_tie",
        "manual_review_close_call",
        "decisive_winner",
    }
    if selection_signal not in valid_signals:
        issues.append(f"invalid selection_signal={selection_signal!r}")

    if selection_signal == "no_credible_match":
        if winner_resume:
            issues.append("no_credible_match should not populate winner_resume")
        if runner_up_resume:
            issues.append("no_credible_match should not populate runner_up_resume")
        if is_tie:
            issues.append("no_credible_match should not set is_tie=true")
        if requires_manual_review:
            issues.append("no_credible_match should not set requires_manual_review=true")
        if llm_adjudication_resume:
            issues.append("no_credible_match should not populate llm_adjudication_resume")
        if llm_adjudication_status not in {"", "disabled"}:
            issues.append("no_credible_match should not run llm adjudication")
        if llm_fallback_status == "disabled" and (llm_fallback_best_resume or llm_fallback_backup_resume):
            issues.append("llm_fallback fields populated while llm_fallback_status=disabled")

    if selection_signal == "decisive_winner":
        if not winner_resume:
            issues.append("decisive_winner must populate winner_resume")
        if is_tie:
            issues.append("decisive_winner should not set is_tie=true")
        if requires_manual_review:
            issues.append("decisive_winner should not set requires_manual_review=true")
        if llm_fallback_best_resume or llm_fallback_backup_resume:
            issues.append("decisive_winner should not populate llm_fallback fields")
        if llm_fallback_status not in {"", "disabled"}:
            issues.append("decisive_winner should not run llm fallback")
        if llm_adjudication_resume:
            issues.append("decisive_winner should not populate llm_adjudication_resume")
        if llm_adjudication_status not in {"", "disabled"}:
            issues.append("decisive_winner should not run llm adjudication")

    if selection_signal == "effective_tie":
        if not winner_resume:
            issues.append("effective_tie must populate winner_resume")
        if not runner_up_resume:
            issues.append("effective_tie must populate runner_up_resume")
        if not is_tie:
            issues.append("effective_tie must set is_tie=true")
        if requires_manual_review:
            issues.append("effective_tie should not set requires_manual_review=true")
        if llm_fallback_best_resume or llm_fallback_backup_resume:
            issues.append("effective_tie should not populate llm_fallback fields")
        if llm_fallback_status not in {"", "disabled"}:
            issues.append("effective_tie should not run llm fallback")

    if selection_signal == "manual_review_close_call":
        if not winner_resume:
            issues.append("manual_review_close_call must populate winner_resume")
        if not runner_up_resume:
            issues.append("manual_review_close_call must populate runner_up_resume")
        if is_tie:
            issues.append("manual_review_close_call should not set is_tie=true")
        if not requires_manual_review:
            issues.append("manual_review_close_call must set requires_manual_review=true")
        if llm_fallback_best_resume or llm_fallback_backup_resume:
            issues.append("manual_review_close_call should not populate llm_fallback fields")
        if llm_fallback_status not in {"", "disabled"}:
            issues.append("manual_review_close_call should not run llm fallback")

    if llm_adjudication_resume:
        if selection_signal not in {"effective_tie", "manual_review_close_call"}:
            issues.append("llm_adjudication_resume populated outside ambiguous selection signals")
        if llm_adjudication_status in {"", "disabled"}:
            issues.append("llm_adjudication_resume populated while adjudication status is empty/disabled")
        if llm_adjudication_differs not in {"true", "false"}:
            issues.append("llm_adjudication_differs_from_deterministic must be true/false when adjudication exists")

    if llm_fallback_best_resume:
        if selection_signal != "no_credible_match":
            issues.append("llm_fallback_best_resume populated outside no_credible_match")
        if llm_fallback_status in {"", "disabled"}:
            issues.append("llm_fallback_best_resume populated while fallback status is empty/disabled")

    return issues


def _build_summary(rows: List[Dict[str, str]]) -> Dict[str, Any]:
    issues: List[Dict[str, Any]] = []
    signal_counts: Dict[str, int] = {}
    fallback_used = 0
    adjudication_used = 0

    for row in rows:
        signal = _text(row.get("selection_signal"))
        signal_counts[signal] = signal_counts.get(signal, 0) + 1

        if _text(row.get("llm_fallback_best_resume")):
            fallback_used += 1
        if _text(row.get("llm_adjudication_resume")):
            adjudication_used += 1

        row_issues = _validate_row(row)
        if row_issues:
            issues.append(
                {
                    "job": _row_label(row),
                    "selection_signal": signal,
                    "issues": row_issues,
                }
            )

    return {
        "total_rows": len(rows),
        "selection_signal_counts": signal_counts,
        "llm_fallback_rows": fallback_used,
        "llm_adjudication_rows": adjudication_used,
        "issue_count": len(issues),
        "all_passed": len(issues) == 0,
        "issues": issues,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate runtime output contract for batch_select_best_resume_variant CSV artifacts."
    )
    parser.add_argument(
        "--input-csv",
        required=True,
        help="Path to the batch selector output CSV.",
    )
    parser.add_argument(
        "--output-json",
        default="outputs/_archive/selector_output_contract/selector_output_contract.json",
        help="Where to write the machine-readable audit report.",
    )
    args = parser.parse_args()

    csv_path = Path(args.input_csv)
    rows = _read_rows(csv_path)
    if not rows:
        raise ValueError(f"No rows found in {csv_path}")

    missing_columns = [col for col in _required_columns() if col not in rows[0]]
    if missing_columns:
        raise ValueError(f"CSV missing required columns: {missing_columns}")

    summary = _build_summary(rows)

    output_path = Path(args.output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print("Batch Selector Output Contract Audit")
    print("-----------------------------------")
    print(f"input_csv: {csv_path}")
    print(f"total_rows: {summary['total_rows']}")
    print(f"llm_fallback_rows: {summary['llm_fallback_rows']}")
    print(f"llm_adjudication_rows: {summary['llm_adjudication_rows']}")
    print(f"issue_count: {summary['issue_count']}")
    print(f"all_passed: {summary['all_passed']}")
    print(f"output_json: {output_path}")

    if summary["selection_signal_counts"]:
        print("\nselection_signal_counts:")
        for key, value in sorted(summary["selection_signal_counts"].items()):
            print(f"- {key}: {value}")

    if not summary["all_passed"]:
        print("\nIssues:")
        for item in summary["issues"]:
            print(f"- {item['job']}")
            for issue in item["issues"]:
                print(f"  * {issue}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()