import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List


def _load_csv_rows(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader]



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

def _normalize_reviewer_status(value: Any) -> str:
    text = str(value or "").strip().lower()
    if not text:
        return "missing"
    if text in {"done", "complete", "completed", "reviewed"}:
        return "done"
    if text in {"pending", "todo", "not_started", "not-started", "in_progress", "in-progress"}:
        return "pending"
    return text


def _normalize_yes_no(value: Any) -> str:
    text = str(value or "").strip().lower()
    if not text:
        return "missing"
    if text in {"yes", "y", "true", "1"}:
        return "yes"
    if text in {"no", "n", "false", "0"}:
        return "no"
    return text


def _rate_row(rows: List[Dict[str, Any]], normalized_key: str, positive_value: str = "yes") -> Dict[str, Any]:
    eligible = [row for row in rows if row.get(normalized_key, "missing") != "missing"]
    numerator = sum(1 for row in eligible if row.get(normalized_key) == positive_value)
    denominator = len(eligible)
    pct = round((numerator / denominator) * 100.0, 2) if denominator else 0.0
    return {
        "numerator": numerator,
        "denominator": denominator,
        "pct": pct,
    }


def _reviewer_group_breakdown(
    rows: List[Dict[str, Any]],
    group_key: str,
    top_n: int,
) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[_bucket_value(row, group_key)].append(row)

    ranked_keys = sorted(grouped.keys(), key=lambda key: (-len(grouped[key]), key))
    output: List[Dict[str, Any]] = []

    for value in ranked_keys[:top_n]:
        group_rows = grouped[value]
        total = len(group_rows)
        output.append(
            {
                "key": value,
                "count": total,
                "reviewer_status": _counter_to_sorted_rows(
                    Counter(row["reviewer_status_normalized"] for row in group_rows),
                    total,
                ),
                "deterministic_correct": _counter_to_sorted_rows(
                    Counter(row["deterministic_correct_normalized"] for row in group_rows),
                    total,
                ),
                "live_better_than_deterministic": _counter_to_sorted_rows(
                    Counter(row["live_better_than_deterministic_normalized"] for row in group_rows),
                    total,
                ),
                "live_blended_better_than_deterministic": _counter_to_sorted_rows(
                    Counter(row["live_blended_better_than_deterministic_normalized"] for row in group_rows),
                    total,
                ),
                "equivalence_correct": _counter_to_sorted_rows(
                    Counter(row["equivalence_correct_normalized"] for row in group_rows),
                    total,
                ),
            }
        )

    return output


def _reviewer_disagreement_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    disagreements: List[Dict[str, Any]] = []

    for row in rows:
        reasons: List[str] = []
        if row.get("deterministic_correct_normalized") == "no":
            reasons.append("deterministic_incorrect")
        if row.get("live_better_than_deterministic_normalized") == "yes":
            reasons.append("live_better")
        if row.get("live_blended_better_than_deterministic_normalized") == "yes":
            reasons.append("live_blended_better")
        if row.get("equivalence_correct_normalized") == "no":
            reasons.append("equivalence_incorrect")

        if not reasons:
            continue

        disagreements.append(
            {
                "packet_key": _bucket_value(row, "packet_key"),
                "resume_key": _bucket_value(row, "resume_key"),
                "company": _bucket_value(row, "company", default=""),
                "title": _bucket_value(row, "title", default=""),
                "selection_outcome_bucket": _bucket_value(row, "selection_outcome_bucket"),
                "live_outcome_bucket": _bucket_value(row, "live_outcome_bucket"),
                "equivalence_outcome_bucket": _bucket_value(row, "equivalence_outcome_bucket"),
                "fingerprint_relationship_bucket": _bucket_value(row, "fingerprint_relationship_bucket"),
                "disagreement_reasons": reasons,
                "reviewer_notes": _bucket_value(row, "reviewer_notes", default=""),
            }
        )

    disagreements.sort(
        key=lambda row: (
            row["packet_key"],
            row["resume_key"],
        )
    )
    return disagreements


def _build_reviewer_summary(rows: List[Dict[str, Any]], top_n: int) -> Dict[str, Any]:
    normalized_rows: List[Dict[str, Any]] = []
    for raw_row in rows:
        row = dict(raw_row)
        row["reviewer_status_normalized"] = _normalize_reviewer_status(row.get("reviewer_status", ""))
        row["deterministic_correct_normalized"] = _normalize_yes_no(row.get("deterministic_correct", ""))
        row["live_better_than_deterministic_normalized"] = _normalize_yes_no(
            row.get("live_better_than_deterministic", "")
        )
        row["live_blended_better_than_deterministic_normalized"] = _normalize_yes_no(
            row.get("live_blended_better_than_deterministic", "")
        )
        row["equivalence_correct_normalized"] = _normalize_yes_no(row.get("equivalence_correct", ""))
        normalized_rows.append(row)

    total = len(normalized_rows)
    completed_rows = [
        row for row in normalized_rows
        if row["reviewer_status_normalized"] == "done"
    ]

    summary = {
        "mode": "reviewer_csv",
        "total_rows": total,
        "completed_reviews": len(completed_rows),
        "completion_rate_pct": round((len(completed_rows) / total) * 100.0, 2) if total else 0.0,
        "reviewer_status": _counter_to_sorted_rows(
            Counter(row["reviewer_status_normalized"] for row in normalized_rows),
            total,
        ),
        "headline_metrics": {
            "deterministic_correct_rate": _rate_row(completed_rows, "deterministic_correct_normalized"),
            "live_better_than_deterministic_rate": _rate_row(
                completed_rows,
                "live_better_than_deterministic_normalized",
            ),
            "live_blended_better_than_deterministic_rate": _rate_row(
                completed_rows,
                "live_blended_better_than_deterministic_normalized",
            ),
            "equivalence_judgment_correct_rate": _rate_row(
                completed_rows,
                "equivalence_correct_normalized",
            ),
        },
        "deterministic_correct": _counter_to_sorted_rows(
            Counter(row["deterministic_correct_normalized"] for row in completed_rows),
            len(completed_rows),
        ),
        "live_better_than_deterministic": _counter_to_sorted_rows(
            Counter(row["live_better_than_deterministic_normalized"] for row in completed_rows),
            len(completed_rows),
        ),
        "live_blended_better_than_deterministic": _counter_to_sorted_rows(
            Counter(row["live_blended_better_than_deterministic_normalized"] for row in completed_rows),
            len(completed_rows),
        ),
        "equivalence_correct": _counter_to_sorted_rows(
            Counter(row["equivalence_correct_normalized"] for row in completed_rows),
            len(completed_rows),
        ),
        "by_selection_outcome_bucket": _reviewer_group_breakdown(
            completed_rows,
            "selection_outcome_bucket",
            top_n,
        ),
        "by_live_outcome_bucket": _reviewer_group_breakdown(
            completed_rows,
            "live_outcome_bucket",
            top_n,
        ),
        "by_equivalence_outcome_bucket": _reviewer_group_breakdown(
            completed_rows,
            "equivalence_outcome_bucket",
            top_n,
        ),
        "by_fingerprint_relationship_bucket": _reviewer_group_breakdown(
            completed_rows,
            "fingerprint_relationship_bucket",
            top_n,
        ),
        "disagreement_rows": _reviewer_disagreement_rows(completed_rows),
    }
    return summary


def _print_reviewer_headline_metrics(metrics: Dict[str, Dict[str, Any]]) -> None:
    print("\nHeadline Metrics")
    print("----------------")
    for key, value in metrics.items():
        print(
            f"{key}: {value['numerator']}/{value['denominator']} "
            f"({value['pct']:.2f}%)"
        )


def _print_reviewer_group_block(title: str, rows: List[Dict[str, Any]]) -> None:
    print(f"\n{title}")
    print("=" * len(title))

    for item in rows:
        print(f"\n{item['key']} | count={item['count']}")
        for key in [
            "reviewer_status",
            "deterministic_correct",
            "live_better_than_deterministic",
            "live_blended_better_than_deterministic",
            "equivalence_correct",
        ]:
            print(f"  {key}")
            for bucket in item[key]:
                print(f"    - {bucket['key']}: {bucket['count']} ({bucket['pct']:.2f}%)")


def _print_reviewer_disagreements(rows: List[Dict[str, Any]]) -> None:
    print("\nReviewer Disagreements")
    print("======================")

    if not rows:
        print("none")
        return

    for item in rows:
        print(
            f"\n{item['packet_key']} | resume={item['resume_key']} | "
            f"reasons={','.join(item['disagreement_reasons'])}"
        )
        print(f"  title: {item['company']} | {item['title']}")
        print(
            f"  selection={item['selection_outcome_bucket']} | "
            f"live={item['live_outcome_bucket']} | "
            f"equivalence={item['equivalence_outcome_bucket']} | "
            f"fingerprint={item['fingerprint_relationship_bucket']}"
        )
        print(f"  notes: {item['reviewer_notes'] or 'n/a'}")


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

def _fingerprint_relationship_bucket(item: Dict[str, Any]) -> str:
    equivalence_bucket = str(item.get("equivalence_outcome_bucket", "") or "").strip()
    live_bucket = str(item.get("live_outcome_bucket", "") or "").strip()

    deterministic_matches_live = bool(item.get("deterministic_matches_live_family", False))
    deterministic_matches_live_blended = bool(item.get("deterministic_matches_live_blended_family", False))
    has_identical_live = deterministic_matches_live or deterministic_matches_live_blended

    if equivalence_bucket == "identical_best":
        return "identical_best"

    if equivalence_bucket == "equivalent_quality":
        if has_identical_live:
            return "equivalent_quality_identical_text"
        return "equivalent_quality_not_identical"

    if live_bucket == "valid_live_present":
        return "valid_live_not_equivalent"

    if live_bucket == "no_valid_live_after_llm":
        return "no_valid_live_after_llm"

    if live_bucket == "llm_not_requested":
        return "llm_not_requested"

    return "other"

def _packet_comparison_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    comparisons: List[Dict[str, Any]] = []

    for row in rows:
        analysis_keys = row.get("analysis_keys", {}) or {}
        job = row.get("job", {}) or {}
        eval_summary = row.get("eval_summary", {}) or {}
        fingerprints = row.get("fingerprints", {}) or {}
        family_fingerprint_matches = fingerprints.get("family_fingerprint_matches", {}) or {}
        artifacts = row.get("artifacts", {}) or {}

        item = {
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
            "packet_json_path": str(row.get("packet_json_path", "") or "").strip(),
            "output_json_path": str(artifacts.get("output_json_path", "") or "").strip(),
            "output_md_path": str(artifacts.get("output_md_path", "") or "").strip(),
            "output_llm_json_path": str(artifacts.get("output_llm_json_path", "") or "").strip(),
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
        item["fingerprint_relationship_bucket"] = _fingerprint_relationship_bucket(item)
        comparisons.append(item)

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
    packet_comparisons = _packet_comparison_rows(rows)
    schema_counter = Counter(_bucket_value(row, "schema_version") for row in rows)
    selection_counter = Counter(_bucket_value(row, "selection_outcome_bucket") for row in rows)
    live_counter = Counter(_bucket_value(row, "live_outcome_bucket") for row in rows)
    equivalence_counter = Counter(_bucket_value(row, "equivalence_outcome_bucket") for row in rows)
    selected_source_counter = Counter(_bucket_value(row, "selected_source") for row in rows)
    compatibility_counter = Counter(_compatibility_value(row) for row in rows)
    fingerprint_relationship_counter = Counter(
        _bucket_value(item, "fingerprint_relationship_bucket")
        for item in packet_comparisons
    )

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
        "fingerprint_relationship_bucket": _counter_to_sorted_rows(
            fingerprint_relationship_counter,
            len(packet_comparisons),
        ),
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
        "packet_comparisons": packet_comparisons,
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
            f"  fingerprint_relationship_bucket={item['fingerprint_relationship_bucket']}"
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

def _write_packet_comparisons_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "packet_key",
        "resume_key",
        "company",
        "title",
        "selected_source",
        "selected_reason",
        "selection_outcome_bucket",
        "live_outcome_bucket",
        "equivalence_outcome_bucket",
        "compatibility_mode",
        "compatibility_reason",
        "preferred_rewrite_fingerprint",
        "selected_candidate_fingerprint",
        "deterministic_family_fingerprint",
        "live_family_fingerprint",
        "live_blended_family_fingerprint",
        "selected_matches_deterministic_family",
        "selected_matches_live_family",
        "selected_matches_live_blended_family",
        "deterministic_matches_live_family",
        "deterministic_matches_live_blended_family",
        "live_matches_live_blended_family",
        "selected_equivalent_candidate_ids",
        "packet_generated_at_utc",
    ]

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()

        for item in rows:
            writer.writerow(
                {
                    "packet_key": item.get("packet_key", ""),
                    "resume_key": item.get("resume_key", ""),
                    "company": item.get("company", ""),
                    "title": item.get("title", ""),
                    "selected_source": item.get("selected_source", ""),
                    "selected_reason": item.get("selected_reason", ""),
                    "selection_outcome_bucket": item.get("selection_outcome_bucket", ""),
                    "live_outcome_bucket": item.get("live_outcome_bucket", ""),
                    "equivalence_outcome_bucket": item.get("equivalence_outcome_bucket", ""),
                    "compatibility_mode": item.get("compatibility_mode", False),
                    "compatibility_reason": item.get("compatibility_reason", ""),
                    "preferred_rewrite_fingerprint": item.get("preferred_rewrite_fingerprint", ""),
                    "selected_candidate_fingerprint": item.get("selected_candidate_fingerprint", ""),
                    "deterministic_family_fingerprint": item.get("deterministic_family_fingerprint", ""),
                    "live_family_fingerprint": item.get("live_family_fingerprint", ""),
                    "live_blended_family_fingerprint": item.get("live_blended_family_fingerprint", ""),
                    "selected_matches_deterministic_family": item.get("selected_matches_deterministic_family", False),
                    "selected_matches_live_family": item.get("selected_matches_live_family", False),
                    "selected_matches_live_blended_family": item.get("selected_matches_live_blended_family", False),
                    "deterministic_matches_live_family": item.get("deterministic_matches_live_family", False),
                    "deterministic_matches_live_blended_family": item.get("deterministic_matches_live_blended_family", False),
                    "live_matches_live_blended_family": item.get("live_matches_live_blended_family", False),
                    "selected_equivalent_candidate_ids": ";".join(
                        item.get("selected_equivalent_candidate_ids", []) or []
                    ),
                    "packet_generated_at_utc": item.get("packet_generated_at_utc", ""),
                }
            )

def _write_reviewer_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "packet_key",
        "resume_key",
        "company",
        "title",
        "selected_source",
        "selected_reason",
        "selection_outcome_bucket",
        "live_outcome_bucket",
        "equivalence_outcome_bucket",
        "fingerprint_relationship_bucket",
        "compatibility_mode",
        "compatibility_reason",
        "packet_generated_at_utc",
        "packet_json_path",
        "output_json_path",
        "output_md_path",
        "output_llm_json_path",
        "preferred_rewrite_fingerprint",
        "selected_candidate_fingerprint",
        "deterministic_family_fingerprint",
        "live_family_fingerprint",
        "live_blended_family_fingerprint",
        "selected_matches_deterministic_family",
        "selected_matches_live_family",
        "selected_matches_live_blended_family",
        "deterministic_matches_live_family",
        "deterministic_matches_live_blended_family",
        "live_matches_live_blended_family",
        "selected_equivalent_candidate_ids",
        "reviewer_status",
        "deterministic_correct",
        "live_better_than_deterministic",
        "live_blended_better_than_deterministic",
        "equivalence_correct",
        "reviewer_notes",
    ]

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()

        for item in rows:
            writer.writerow(
                {
                    "packet_key": item.get("packet_key", ""),
                    "resume_key": item.get("resume_key", ""),
                    "company": item.get("company", ""),
                    "title": item.get("title", ""),
                    "selected_source": item.get("selected_source", ""),
                    "selected_reason": item.get("selected_reason", ""),
                    "selection_outcome_bucket": item.get("selection_outcome_bucket", ""),
                    "live_outcome_bucket": item.get("live_outcome_bucket", ""),
                    "equivalence_outcome_bucket": item.get("equivalence_outcome_bucket", ""),
                    "fingerprint_relationship_bucket": item.get("fingerprint_relationship_bucket", ""),
                    "compatibility_mode": item.get("compatibility_mode", False),
                    "compatibility_reason": item.get("compatibility_reason", ""),
                    "packet_generated_at_utc": item.get("packet_generated_at_utc", ""),
                    "packet_json_path": item.get("packet_json_path", ""),
                    "output_json_path": item.get("output_json_path", ""),
                    "output_md_path": item.get("output_md_path", ""),
                    "output_llm_json_path": item.get("output_llm_json_path", ""),
                    "preferred_rewrite_fingerprint": item.get("preferred_rewrite_fingerprint", ""),
                    "selected_candidate_fingerprint": item.get("selected_candidate_fingerprint", ""),
                    "deterministic_family_fingerprint": item.get("deterministic_family_fingerprint", ""),
                    "live_family_fingerprint": item.get("live_family_fingerprint", ""),
                    "live_blended_family_fingerprint": item.get("live_blended_family_fingerprint", ""),
                    "selected_matches_deterministic_family": item.get("selected_matches_deterministic_family", False),
                    "selected_matches_live_family": item.get("selected_matches_live_family", False),
                    "selected_matches_live_blended_family": item.get("selected_matches_live_blended_family", False),
                    "deterministic_matches_live_family": item.get("deterministic_matches_live_family", False),
                    "deterministic_matches_live_blended_family": item.get("deterministic_matches_live_blended_family", False),
                    "live_matches_live_blended_family": item.get("live_matches_live_blended_family", False),
                    "selected_equivalent_candidate_ids": ";".join(
                        item.get("selected_equivalent_candidate_ids", []) or []
                    ),
                    "reviewer_status": "",
                    "deterministic_correct": "",
                    "live_better_than_deterministic": "",
                    "live_blended_better_than_deterministic": "",
                    "equivalence_correct": "",
                    "reviewer_notes": "",
                }
            )

def _headline_metric_text(metric: Dict[str, Any]) -> str:
    numerator = int(metric.get("numerator", 0) or 0)
    denominator = int(metric.get("denominator", 0) or 0)
    pct = float(metric.get("pct", 0.0) or 0.0)
    return f"{numerator}/{denominator} ({pct:.2f}%)"


def _reviewer_recommendations(summary: Dict[str, Any]) -> List[str]:
    headline_metrics = summary.get("headline_metrics", {}) or {}

    deterministic_metric = headline_metrics.get("deterministic_correct_rate", {}) or {}
    live_metric = headline_metrics.get("live_better_than_deterministic_rate", {}) or {}
    live_blended_metric = headline_metrics.get("live_blended_better_than_deterministic_rate", {}) or {}
    equivalence_metric = headline_metrics.get("equivalence_judgment_correct_rate", {}) or {}

    recommendations: List[str] = []

    deterministic_num = int(deterministic_metric.get("numerator", 0) or 0)
    deterministic_den = int(deterministic_metric.get("denominator", 0) or 0)
    live_num = int(live_metric.get("numerator", 0) or 0)
    live_blended_num = int(live_blended_metric.get("numerator", 0) or 0)
    equivalence_num = int(equivalence_metric.get("numerator", 0) or 0)
    equivalence_den = int(equivalence_metric.get("denominator", 0) or 0)

    if deterministic_den > 0 and deterministic_num == deterministic_den and live_num == 0 and live_blended_num == 0:
        recommendations.append(
            "Keep runtime winner selection deterministic-first. This reviewed batch shows no evidence that live or live_blended should replace deterministic selection."
        )
    elif deterministic_den > 0 and deterministic_num < deterministic_den:
        recommendations.append(
            "Do not change runtime policy yet. Deterministic selection was not universally supported by this reviewed batch, so gather more labeled evidence before any selector change."
        )

    if equivalence_den > 0 and equivalence_num < equivalence_den:
        recommendations.append(
            "Do not change runtime winner selection. Tighten offline equivalence interpretation/reporting instead, because at least one runtime equivalence judgment was too generous."
        )

    if not recommendations:
        recommendations.append(
            "No automatic policy recommendation triggered. Review the headline metrics and disagreement rows before changing runtime behavior."
        )

    return recommendations


def _write_reviewer_report_markdown(path: Path, summary: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    headline_metrics = summary.get("headline_metrics", {}) or {}
    disagreements = summary.get("disagreement_rows", []) or []

    deterministic_metric = headline_metrics.get("deterministic_correct_rate", {}) or {}
    live_metric = headline_metrics.get("live_better_than_deterministic_rate", {}) or {}
    live_blended_metric = headline_metrics.get("live_blended_better_than_deterministic_rate", {}) or {}
    equivalence_metric = headline_metrics.get("equivalence_judgment_correct_rate", {}) or {}

    total_rows = int(summary.get("total_rows", 0) or 0)
    completed_reviews = int(summary.get("completed_reviews", 0) or 0)
    completion_rate_pct = float(summary.get("completion_rate_pct", 0.0) or 0.0)

    lines: List[str] = []
    lines.append("# Tailoring Reviewer Human-Agreement Report")
    lines.append("")
    lines.append("## Scope")
    lines.append(f"- total rows: {total_rows}")
    lines.append(f"- completed reviews: {completed_reviews}")
    lines.append(f"- reviewer completion rate: {completion_rate_pct:.2f}%")
    lines.append("")

    lines.append("## Headline Metrics")
    lines.append(f"- deterministic correct rate: {_headline_metric_text(deterministic_metric)}")
    lines.append(f"- live better than deterministic rate: {_headline_metric_text(live_metric)}")
    lines.append(f"- live blended better than deterministic rate: {_headline_metric_text(live_blended_metric)}")
    lines.append(f"- equivalence judgment correct rate: {_headline_metric_text(equivalence_metric)}")
    lines.append("")

    lines.append("## Recommendation")
    for recommendation in _reviewer_recommendations(summary):
        lines.append(f"- {recommendation}")
    lines.append("")

    lines.append("## Interpretation")
    if (
        int(deterministic_metric.get("denominator", 0) or 0) > 0
        and int(deterministic_metric.get("numerator", 0) or 0) == int(deterministic_metric.get("denominator", 0) or 0)
        and int(live_metric.get("numerator", 0) or 0) == 0
        and int(live_blended_metric.get("numerator", 0) or 0) == 0
    ):
        lines.append("- Deterministic winner selection was supported by every completed review in this batch.")
    else:
        lines.append("- Deterministic winner selection was not universally supported in this batch.")

    if int(equivalence_metric.get("numerator", 0) or 0) < int(equivalence_metric.get("denominator", 0) or 0):
        lines.append("- The main weakness exposed by this batch is equivalence labeling quality, not winner selection quality.")
    else:
        lines.append("- No equivalence-label disagreement was found in this batch.")
    lines.append("")

    lines.append("## Reviewer Disagreements")
    if disagreements:
        for item in disagreements:
            packet_key = str(item.get("packet_key", "") or "").strip()
            resume_key = str(item.get("resume_key", "") or "").strip()
            company = str(item.get("company", "") or "").strip()
            title = str(item.get("title", "") or "").strip()
            reasons = item.get("disagreement_reasons", []) or []
            selection_bucket = str(item.get("selection_outcome_bucket", "") or "").strip()
            live_bucket = str(item.get("live_outcome_bucket", "") or "").strip()
            equivalence_bucket = str(item.get("equivalence_outcome_bucket", "") or "").strip()
            fingerprint_bucket = str(item.get("fingerprint_relationship_bucket", "") or "").strip()
            notes = str(item.get("reviewer_notes", "") or "").strip()

            lines.append(f"### {packet_key}")
            lines.append(f"- resume: {resume_key}")
            lines.append(f"- title: {company} | {title}")
            lines.append(f"- disagreement reasons: {', '.join(reasons) if reasons else 'unspecified'}")
            lines.append(f"- selection bucket: {selection_bucket}")
            lines.append(f"- live bucket: {live_bucket}")
            lines.append(f"- equivalence bucket: {equivalence_bucket}")
            lines.append(f"- fingerprint relationship bucket: {fingerprint_bucket}")
            lines.append(f"- reviewer notes: {notes or 'n/a'}")
            lines.append("")
    else:
        lines.append("- none")
        lines.append("")

    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze tailoring training-log JSONL outputs or reviewer CSV exports."
    )
    parser.add_argument(
        "--input-jsonl",
        default="./outputs/application_planning/training_logs/tailoring_runs.jsonl",
        help="Path to the tailoring training-log JSONL file.",
    )
    parser.add_argument(
        "--reviewer-csv-input",
        default="",
        help="Optional path to a completed reviewer CSV for human-agreement analysis.",
    )
    parser.add_argument(
        "--output-json",
        default="",
        help="Optional path to write a machine-readable summary JSON.",
    )
    parser.add_argument(
        "--output-packet-comparisons-csv",
        default="",
        help="Optional path to write a CSV export of packet comparison rows.",
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
    parser.add_argument(
        "--output-reviewer-csv",
        default="",
        help="Optional path to write a reviewer CSV for latest keyed packet comparisons.",
    )
    parser.add_argument(
        "--output-reviewer-report-md",
        default="",
        help="Optional path to write a reviewer-facing markdown report for reviewer CSV analysis mode.",
    )
    args = parser.parse_args()

    if args.reviewer_csv_input.strip():
        reviewer_csv_path = Path(args.reviewer_csv_input)
        if not reviewer_csv_path.exists():
            raise FileNotFoundError(f"Reviewer CSV file not found: {reviewer_csv_path}")

        reviewer_rows = _load_csv_rows(reviewer_csv_path)
        if not reviewer_rows:
            raise ValueError(f"No rows found in reviewer CSV: {reviewer_csv_path}")

        summary = _build_reviewer_summary(reviewer_rows, top_n=max(args.top_n, 1))

        print(
            f"Loaded {len(reviewer_rows)} reviewer rows from {reviewer_csv_path}; "
            f"completed reviews={summary['completed_reviews']}"
        )
        _print_counter_block("Reviewer Status", summary["reviewer_status"])
        _print_reviewer_headline_metrics(summary["headline_metrics"])
        _print_counter_block("Deterministic Correct", summary["deterministic_correct"])
        _print_counter_block(
            "Live Better Than Deterministic",
            summary["live_better_than_deterministic"],
        )
        _print_counter_block(
            "Live Blended Better Than Deterministic",
            summary["live_blended_better_than_deterministic"],
        )
        _print_counter_block("Equivalence Correct", summary["equivalence_correct"])
        _print_reviewer_group_block(
            "By Selection Outcome Bucket",
            summary["by_selection_outcome_bucket"],
        )
        _print_reviewer_group_block(
            "By Live Outcome Bucket",
            summary["by_live_outcome_bucket"],
        )
        _print_reviewer_group_block(
            "By Equivalence Outcome Bucket",
            summary["by_equivalence_outcome_bucket"],
        )
        _print_reviewer_group_block(
            "By Fingerprint Relationship Bucket",
            summary["by_fingerprint_relationship_bucket"],
        )
        _print_reviewer_disagreements(summary["disagreement_rows"])

        if args.output_json.strip():
            output_path = Path(args.output_json)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(
                json.dumps(summary, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"\nWrote summary JSON: {output_path}")
        
        if args.output_reviewer_report_md.strip():
            if summary.get("mode") != "reviewer_csv":
                raise ValueError(
                    "--output-reviewer-report-md requires reviewer CSV analysis mode."
                )
            reviewer_report_path = Path(args.output_reviewer_report_md)
            _write_reviewer_report_markdown(reviewer_report_path, summary)
            print(f"Wrote reviewer report markdown: {reviewer_report_path}")

        return

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
    _print_counter_block(
        "Fingerprint Relationship Bucket",
        summary["fingerprint_relationship_bucket"],
    )

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

    if args.output_packet_comparisons_csv.strip():
        csv_path = Path(args.output_packet_comparisons_csv)
        _write_packet_comparisons_csv(csv_path, summary["packet_comparisons"])
        print(f"Wrote packet comparison CSV: {csv_path}")

    if args.output_reviewer_csv.strip():
        reviewer_csv_path = Path(args.output_reviewer_csv)
        _write_reviewer_csv(reviewer_csv_path, summary["packet_comparisons"])
        print(f"Wrote reviewer CSV: {reviewer_csv_path}")

if __name__ == "__main__":
    main()