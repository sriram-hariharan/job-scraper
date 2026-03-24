import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List


def _load_jsonl_rows(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, 1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON on line {line_number} of {path}: {exc}"
                ) from exc
            if not isinstance(value, dict):
                raise ValueError(
                    f"Expected JSON object on line {line_number} of {path}, got {type(value).__name__}"
                )
            rows.append(value)
    return rows


def _bucket_value(row: Dict[str, Any], key: str, default: str = "missing") -> str:
    value = row.get(key, default)
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _analysis_key(row: Dict[str, Any], key: str, default: str = "missing") -> str:
    analysis_keys = row.get("analysis_keys", {}) or {}
    value = analysis_keys.get(key, default)
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _compatibility_value(row: Dict[str, Any]) -> str:
    return "true" if bool(row.get("compatibility_mode", False)) else "false"


def _counter_to_sorted_rows(counter: Counter, total: int) -> List[Dict[str, Any]]:
    items = sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    rows: List[Dict[str, Any]] = []
    for key, count in items:
        pct = round((count / total) * 100.0, 2) if total else 0.0
        rows.append(
            {
                "key": key,
                "count": count,
                "pct": pct,
            }
        )
    return rows


def _group_breakdown(
    rows: List[Dict[str, Any]],
    key_getter,
    top_n: int,
) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[key_getter(row)].append(row)

    ranked_keys = sorted(
        grouped.keys(),
        key=lambda key: (-len(grouped[key]), key),
    )

    output: List[Dict[str, Any]] = []
    for group_key in ranked_keys[:top_n]:
        group_rows = grouped[group_key]
        total = len(group_rows)

        selection_counter = Counter(
            _bucket_value(row, "selection_outcome_bucket")
            for row in group_rows
        )
        live_counter = Counter(
            _bucket_value(row, "live_outcome_bucket")
            for row in group_rows
        )
        equivalence_counter = Counter(
            _bucket_value(row, "equivalence_outcome_bucket")
            for row in group_rows
        )
        selected_source_counter = Counter(
            _bucket_value(row, "selected_source")
            for row in group_rows
        )
        schema_counter = Counter(
            _bucket_value(row, "schema_version")
            for row in group_rows
        )

        output.append(
            {
                "key": group_key,
                "count": total,
                "selection_outcome_bucket": _counter_to_sorted_rows(selection_counter, total),
                "live_outcome_bucket": _counter_to_sorted_rows(live_counter, total),
                "equivalence_outcome_bucket": _counter_to_sorted_rows(equivalence_counter, total),
                "selected_source": _counter_to_sorted_rows(selected_source_counter, total),
                "schema_version": _counter_to_sorted_rows(schema_counter, total),
            }
        )

    return output

def _has_required_analysis_keys(row: Dict[str, Any]) -> bool:
    packet_key = _analysis_key(row, "packet_key", default="")
    resume_key = _analysis_key(row, "resume_key", default="")
    return bool(packet_key) and packet_key != "missing" and bool(resume_key) and resume_key != "missing"

def _latest_rows_per_packet_resume(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[tuple, List[Dict[str, Any]]] = defaultdict(list)

    for row in rows:
        packet_key = _analysis_key(row, "packet_key")
        resume_key = _analysis_key(row, "resume_key")
        grouped[(packet_key, resume_key)].append(row)

    latest_rows: List[Dict[str, Any]] = []

    for _, group_rows in grouped.items():
        sorted_group = sorted(
            group_rows,
            key=lambda row: (
                _bucket_value(row, "generated_at_utc", default=""),
                _bucket_value(row, "schema_version", default=""),
            ),
        )
        latest_rows.append(sorted_group[-1])

    latest_rows.sort(
        key=lambda row: (
            _analysis_key(row, "packet_key"),
            _analysis_key(row, "resume_key"),
            _bucket_value(row, "generated_at_utc", default=""),
        )
    )
    return latest_rows

def _packet_comparison_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    comparisons: List[Dict[str, Any]] = []

    for row in rows:
        analysis_keys = row.get("analysis_keys", {}) or {}
        job = row.get("job", {}) or {}
        eval_summary = row.get("eval_summary", {}) or {}
        fingerprints = row.get("fingerprints", {}) or {}
        family_fingerprint_matches = fingerprints.get("family_fingerprint_matches", {}) or {}

        comparisons.append(
            {
                "packet_key": _analysis_key(row, "packet_key"),
                "resume_key": _analysis_key(row, "resume_key"),
                "company": str(job.get("company", "") or "").strip(),
                "title": str(job.get("title", "") or "").strip(),
                "selected_source": _bucket_value(row, "selected_source"),
                "selected_reason": _bucket_value(row, "selected_reason"),
                "selection_outcome_bucket": _bucket_value(row, "selection_outcome_bucket"),
                "live_outcome_bucket": _bucket_value(row, "live_outcome_bucket"),
                "equivalence_outcome_bucket": _bucket_value(row, "equivalence_outcome_bucket"),
                "compatibility_mode": bool(row.get("compatibility_mode", False)),
                "compatibility_reason": str(row.get("compatibility_reason", "") or "").strip(),
                "preferred_rewrite_fingerprint": str(
                    eval_summary.get("preferred_rewrite_fingerprint", "") or ""
                ),
                "selected_candidate_fingerprint": str(
                    eval_summary.get("selected_candidate_fingerprint", "") or ""
                ),
                "deterministic_family_fingerprint": str(
                    eval_summary.get("deterministic_family_fingerprint", "") or ""
                ),
                "live_family_fingerprint": str(
                    eval_summary.get("live_family_fingerprint", "") or ""
                ),
                "live_blended_family_fingerprint": str(
                    eval_summary.get("live_blended_family_fingerprint", "") or ""
                ),
                "selected_matches_deterministic_family": bool(
                    eval_summary.get("selected_matches_deterministic_family", False)
                ),
                "selected_matches_live_family": bool(
                    eval_summary.get("selected_matches_live_family", False)
                ),
                "selected_matches_live_blended_family": bool(
                    eval_summary.get("selected_matches_live_blended_family", False)
                ),
                "deterministic_matches_live_family": bool(
                    eval_summary.get("deterministic_matches_live_family", False)
                ),
                "deterministic_matches_live_blended_family": bool(
                    eval_summary.get("deterministic_matches_live_blended_family", False)
                ),
                "live_matches_live_blended_family": bool(
                    eval_summary.get("live_matches_live_blended_family", False)
                ),
                "selected_equivalent_candidate_ids": row.get("selected_equivalent_candidate_ids", []) or [],
                "packet_generated_at_utc": _bucket_value(row, "generated_at_utc", default=""),
            }
        )

    comparisons.sort(
        key=lambda item: (
            item["packet_key"],
            item["resume_key"],
            item["packet_generated_at_utc"],
        )
    )
    return comparisons

def _build_summary(
    rows: List[Dict[str, Any]],
    top_n: int,
    latest_per_packet_resume: bool = False,
    require_analysis_keys: bool = False,
) -> Dict[str, Any]:
    total = len(rows)

    schema_counter = Counter(_bucket_value(row, "schema_version") for row in rows)
    selection_counter = Counter(_bucket_value(row, "selection_outcome_bucket") for row in rows)
    live_counter = Counter(_bucket_value(row, "live_outcome_bucket") for row in rows)
    equivalence_counter = Counter(_bucket_value(row, "equivalence_outcome_bucket") for row in rows)
    selected_source_counter = Counter(_bucket_value(row, "selected_source") for row in rows)
    compatibility_counter = Counter(_compatibility_value(row) for row in rows)

    summary = {
        "filters": {
            "latest_per_packet_resume": bool(latest_per_packet_resume),
            "require_analysis_keys": bool(require_analysis_keys),
        },
        "total_rows": total,
        "schema_version": _counter_to_sorted_rows(schema_counter, total),
        "selection_outcome_bucket": _counter_to_sorted_rows(selection_counter, total),
        "live_outcome_bucket": _counter_to_sorted_rows(live_counter, total),
        "equivalence_outcome_bucket": _counter_to_sorted_rows(equivalence_counter, total),
        "selected_source": _counter_to_sorted_rows(selected_source_counter, total),
        "compatibility_mode": _counter_to_sorted_rows(compatibility_counter, total),
        "by_packet_key": _group_breakdown(
            rows,
            key_getter=lambda row: _analysis_key(row, "packet_key"),
            top_n=top_n,
        ),
        "by_resume_key": _group_breakdown(
            rows,
            key_getter=lambda row: _analysis_key(row, "resume_key"),
            top_n=top_n,
        ),
        "packet_comparisons": _packet_comparison_rows(rows),
    }
    return summary


def _print_counter_block(title: str, rows: List[Dict[str, Any]]) -> None:
    print(f"\n{title}")
    print("-" * len(title))
    for item in rows:
        print(f"{item['key']}: {item['count']} ({item['pct']:.2f}%)")


def _print_group_block(title: str, rows: List[Dict[str, Any]]) -> None:
    print(f"\n{title}")
    print("=" * len(title))

    for item in rows:
        print(f"\n{item['key']} | count={item['count']}")

        print("  selection_outcome_bucket")
        for bucket in item["selection_outcome_bucket"]:
            print(f"    - {bucket['key']}: {bucket['count']} ({bucket['pct']:.2f}%)")

        print("  live_outcome_bucket")
        for bucket in item["live_outcome_bucket"]:
            print(f"    - {bucket['key']}: {bucket['count']} ({bucket['pct']:.2f}%)")

        print("  equivalence_outcome_bucket")
        for bucket in item["equivalence_outcome_bucket"]:
            print(f"    - {bucket['key']}: {bucket['count']} ({bucket['pct']:.2f}%)")

        print("  selected_source")
        for bucket in item["selected_source"]:
            print(f"    - {bucket['key']}: {bucket['count']} ({bucket['pct']:.2f}%)")

        print("  schema_version")
        for bucket in item["schema_version"]:
            print(f"    - {bucket['key']}: {bucket['count']} ({bucket['pct']:.2f}%)")

def _print_packet_comparisons(rows: List[Dict[str, Any]]) -> None:
    print("\nPacket Comparisons")
    print("==================")

    for item in rows:
        print(
            f"\n{item['packet_key']} | resume={item['resume_key']} | "
            f"selected={item['selected_source']} | "
            f"selection_bucket={item['selection_outcome_bucket']}"
        )
        print(f"  title: {item['company']} | {item['title']}")
        print(f"  selected_reason: {item['selected_reason']}")
        print(
            f"  live_outcome={item['live_outcome_bucket']} | "
            f"equivalence_outcome={item['equivalence_outcome_bucket']}"
        )
        print(
            f"  compatibility_mode={item['compatibility_mode']} | "
            f"compatibility_reason={item['compatibility_reason'] or 'n/a'}"
        )
        print(
            f"  fingerprints | selected={item['selected_candidate_fingerprint']} | "
            f"deterministic={item['deterministic_family_fingerprint']} | "
            f"live={item['live_family_fingerprint']} | "
            f"live_blended={item['live_blended_family_fingerprint']}"
        )
        print(
            "  fingerprint_matches | "
            f"selected=deterministic:{item['selected_matches_deterministic_family']} | "
            f"selected=live:{item['selected_matches_live_family']} | "
            f"selected=live_blended:{item['selected_matches_live_blended_family']} | "
            f"deterministic=live:{item['deterministic_matches_live_family']} | "
            f"deterministic=live_blended:{item['deterministic_matches_live_blended_family']} | "
            f"live=live_blended:{item['live_matches_live_blended_family']}"
        )
        print(
            f"  selected_equivalent_candidate_ids: "
            f"{', '.join(item['selected_equivalent_candidate_ids']) if item['selected_equivalent_candidate_ids'] else 'none'}"
        )

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze tailoring training-log JSONL outputs."
    )
    parser.add_argument(
        "--input-jsonl",
        default="./outputs/application_planning/training_logs/tailoring_runs.jsonl",
        help="Path to the tailoring training-log JSONL file.",
    )
    parser.add_argument(
        "--output-json",
        default="",
        help="Optional path to write a machine-readable summary JSON.",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=10,
        help="Number of packet_key and resume_key groups to print.",
    )
    parser.add_argument(
        "--latest-per-packet-resume",
        action="store_true",
        help="Keep only the latest row for each (packet_key, resume_key) pair before summarizing.",
    )
    parser.add_argument(
        "--require-analysis-keys",
        action="store_true",
        help="Drop rows missing stable analysis keys such as packet_key and resume_key before summarizing.",
    )
    args = parser.parse_args()

    input_path = Path(args.input_jsonl)
    if not input_path.exists():
        raise FileNotFoundError(f"Training log file not found: {input_path}")

    rows = _load_jsonl_rows(input_path)
    if not rows:
        raise ValueError(f"No rows found in training log: {input_path}")

    analyzed_rows = rows

    if args.require_analysis_keys:
        analyzed_rows = [
            row for row in analyzed_rows
            if _has_required_analysis_keys(row)
        ]

    if args.latest_per_packet_resume:
        analyzed_rows = _latest_rows_per_packet_resume(analyzed_rows)

    summary = _build_summary(
        analyzed_rows,
        top_n=max(args.top_n, 1),
        latest_per_packet_resume=args.latest_per_packet_resume,
        require_analysis_keys=args.require_analysis_keys,
    )

    print(
        f"Loaded {len(rows)} tailoring log rows from {input_path}; "
        f"analyzing {summary['total_rows']} rows"
    )

    _print_counter_block("Schema Version", summary["schema_version"])
    _print_counter_block("Selection Outcome Bucket", summary["selection_outcome_bucket"])
    _print_counter_block("Live Outcome Bucket", summary["live_outcome_bucket"])
    _print_counter_block("Equivalence Outcome Bucket", summary["equivalence_outcome_bucket"])
    _print_counter_block("Selected Source", summary["selected_source"])
    _print_counter_block("Compatibility Mode", summary["compatibility_mode"])

    _print_group_block("Top Packet Keys", summary["by_packet_key"])
    _print_group_block("Top Resume Keys", summary["by_resume_key"])
    _print_packet_comparisons(summary["packet_comparisons"])

    if args.output_json.strip():
        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"\nWrote summary JSON: {output_path}")


if __name__ == "__main__":
    main()