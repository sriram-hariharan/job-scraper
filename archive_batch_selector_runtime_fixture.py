import argparse
import csv
import json
import shutil
from datetime import datetime, timezone
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
        rows = list(csv.DictReader(handle))

    if not rows:
        raise ValueError(f"No rows found in {path}")

    return rows


def _required_columns() -> List[str]:
    return [
        "job_doc_id",
        "job_company",
        "job_title",
        "selection_signal",
        "requires_manual_review",
        "is_tie",
        "llm_fallback_best_resume",
        "llm_adjudication_resume",
    ]


def _coverage_summary(rows: List[Dict[str, str]]) -> Dict[str, Any]:
    signal_counts: Dict[str, int] = {}
    fallback_rows = 0
    adjudication_rows = 0
    manual_review_rows = 0
    tie_rows = 0

    for row in rows:
        signal = _text(row.get("selection_signal"))
        signal_counts[signal] = signal_counts.get(signal, 0) + 1

        if _text(row.get("llm_fallback_best_resume")):
            fallback_rows += 1

        if _text(row.get("llm_adjudication_resume")):
            adjudication_rows += 1

        if _boolish(row.get("requires_manual_review")):
            manual_review_rows += 1

        if _boolish(row.get("is_tie")):
            tie_rows += 1

    nondecisive_signal_rows = sum(
        signal_counts.get(key, 0)
        for key in [
            "effective_tie",
            "manual_review_close_call",
            "no_credible_match",
        ]
    )

    return {
        "total_rows": len(rows),
        "selection_signal_counts": dict(sorted(signal_counts.items())),
        "fallback_rows": fallback_rows,
        "adjudication_rows": adjudication_rows,
        "manual_review_rows": manual_review_rows,
        "tie_rows": tie_rows,
        "nondecisive_signal_rows": nondecisive_signal_rows,
        "has_nondecisive_coverage": nondecisive_signal_rows > 0,
        "has_llm_branch_coverage": fallback_rows > 0 or adjudication_rows > 0,
    }


def _archive_slug(summary: Dict[str, Any]) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    total_rows = int(summary.get("total_rows", 0))
    nondecisive = int(summary.get("nondecisive_signal_rows", 0))
    fallback_rows = int(summary.get("fallback_rows", 0))
    adjudication_rows = int(summary.get("adjudication_rows", 0))
    return (
        f"{stamp}"
        f"__rows_{total_rows}"
        f"__nondecisive_{nondecisive}"
        f"__fallback_{fallback_rows}"
        f"__adjudication_{adjudication_rows}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Archive batch-selector runtime CSVs only when they provide useful Scoring V2 branch coverage."
    )
    parser.add_argument(
        "--input-csv",
        default="outputs/application_planning/best_resume_variant_by_job.csv",
        help="Path to batch selector CSV.",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/_archive/scorer_v2_runtime_fixtures",
        help="Archive directory for accepted selector runtime fixtures.",
    )
    parser.add_argument(
        "--min-rows",
        type=int,
        default=10,
        help="Minimum number of rows required before archiving. Default: 10.",
    )
    parser.add_argument(
        "--allow-weak",
        action="store_true",
        help="Archive even if coverage is weak. By default, weak runs fail and are not archived.",
    )
    args = parser.parse_args()

    input_csv = Path(args.input_csv)
    output_dir = Path(args.output_dir)

    rows = _read_rows(input_csv)

    missing_columns = [col for col in _required_columns() if col not in rows[0]]
    if missing_columns:
        raise ValueError(f"CSV missing required columns: {missing_columns}")

    summary = _coverage_summary(rows)
    summary["input_csv"] = str(input_csv)
    summary["min_rows_required"] = int(args.min_rows)

    coverage_ok = (
        summary["total_rows"] >= int(args.min_rows)
        and (
            summary["has_nondecisive_coverage"]
            or summary["has_llm_branch_coverage"]
        )
    )

    summary["coverage_ok"] = coverage_ok
    summary["allow_weak"] = bool(args.allow_weak)

    print("Batch Selector Runtime Fixture Archiver")
    print("--------------------------------------")
    print(f"input_csv: {input_csv}")
    print(f"total_rows: {summary['total_rows']}")
    print(f"selection_signal_counts: {summary['selection_signal_counts']}")
    print(f"fallback_rows: {summary['fallback_rows']}")
    print(f"adjudication_rows: {summary['adjudication_rows']}")
    print(f"manual_review_rows: {summary['manual_review_rows']}")
    print(f"tie_rows: {summary['tie_rows']}")
    print(f"nondecisive_signal_rows: {summary['nondecisive_signal_rows']}")
    print(f"coverage_ok: {summary['coverage_ok']}")

    if not coverage_ok and not args.allow_weak:
        print("\nNot archiving fixture because runtime coverage is too weak.")
        raise SystemExit(1)

    archive_dir = output_dir / _archive_slug(summary)
    archive_dir.mkdir(parents=True, exist_ok=True)

    archived_csv = archive_dir / "best_resume_variant_by_job.csv"
    archived_summary = archive_dir / "runtime_coverage_summary.json"

    shutil.copy2(input_csv, archived_csv)
    archived_summary.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"\nArchived CSV: {archived_csv}")
    print(f"Archived summary: {archived_summary}")


if __name__ == "__main__":
    main()