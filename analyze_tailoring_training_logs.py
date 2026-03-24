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


def _build_summary(rows: List[Dict[str, Any]], top_n: int) -> Dict[str, Any]:
    total = len(rows)

    schema_counter = Counter(_bucket_value(row, "schema_version") for row in rows)
    selection_counter = Counter(_bucket_value(row, "selection_outcome_bucket") for row in rows)
    live_counter = Counter(_bucket_value(row, "live_outcome_bucket") for row in rows)
    equivalence_counter = Counter(_bucket_value(row, "equivalence_outcome_bucket") for row in rows)
    selected_source_counter = Counter(_bucket_value(row, "selected_source") for row in rows)
    compatibility_counter = Counter(_compatibility_value(row) for row in rows)

    summary = {
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
    args = parser.parse_args()

    input_path = Path(args.input_jsonl)
    if not input_path.exists():
        raise FileNotFoundError(f"Training log file not found: {input_path}")

    rows = _load_jsonl_rows(input_path)
    if not rows:
        raise ValueError(f"No rows found in training log: {input_path}")

    summary = _build_summary(rows, top_n=max(args.top_n, 1))

    print(f"Loaded {summary['total_rows']} tailoring log rows from {input_path}")

    _print_counter_block("Schema Version", summary["schema_version"])
    _print_counter_block("Selection Outcome Bucket", summary["selection_outcome_bucket"])
    _print_counter_block("Live Outcome Bucket", summary["live_outcome_bucket"])
    _print_counter_block("Equivalence Outcome Bucket", summary["equivalence_outcome_bucket"])
    _print_counter_block("Selected Source", summary["selected_source"])
    _print_counter_block("Compatibility Mode", summary["compatibility_mode"])

    _print_group_block("Top Packet Keys", summary["by_packet_key"])
    _print_group_block("Top Resume Keys", summary["by_resume_key"])

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