import argparse
import csv
import json
import glob
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_REVIEWER_EVAL_BUNDLE_OUTPUT_DIR = Path(
    "outputs/application_planning_archive/reviewer_eval"
)

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

def _normalize_reviewer_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized_rows: List[Dict[str, Any]] = []

    for raw_row in rows:
        row = dict(raw_row)
        row["reviewer_status_normalized"] = _normalize_reviewer_status(
            row.get("reviewer_status", "")
        )
        row["deterministic_correct_normalized"] = _normalize_yes_no(
            row.get("deterministic_correct", "")
        )
        row["live_better_than_deterministic_normalized"] = _normalize_yes_no(
            row.get("live_better_than_deterministic", "")
        )
        row["live_blended_better_than_deterministic_normalized"] = _normalize_yes_no(
            row.get("live_blended_better_than_deterministic", "")
        )
        row["equivalence_correct_normalized"] = _normalize_yes_no(
            row.get("equivalence_correct", "")
        )
        normalized_rows.append(row)

    return normalized_rows

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

def _reviewer_done_missing_fields(row: Dict[str, Any]) -> List[str]:
    missing: List[str] = []

    required_fields = [
        ("deterministic_correct", row.get("deterministic_correct_normalized", "missing")),
        (
            "live_better_than_deterministic",
            row.get("live_better_than_deterministic_normalized", "missing"),
        ),
        (
            "live_blended_better_than_deterministic",
            row.get("live_blended_better_than_deterministic_normalized", "missing"),
        ),
        ("equivalence_correct", row.get("equivalence_correct_normalized", "missing")),
    ]

    for field_name, normalized_value in required_fields:
        if normalized_value == "missing":
            missing.append(field_name)

    return missing


def _reviewer_validation_issue(
    severity: str,
    issue_type: str,
    packet_key: str,
    resume_key: str,
    message: str,
) -> Dict[str, Any]:
    return {
        "severity": severity,
        "issue_type": issue_type,
        "packet_key": packet_key,
        "resume_key": resume_key,
        "message": message,
    }


def _build_reviewer_validation(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    normalized_rows = _normalize_reviewer_rows(rows)

    issues: List[Dict[str, Any]] = []
    duplicate_counter: Counter = Counter()
    invalid_status_counter: Counter = Counter()
    invalid_yes_no_counter: Counter = Counter()

    allowed_status_values = {"done", "pending", "missing"}
    allowed_yes_no_values = {"yes", "no", "missing"}

    for row in normalized_rows:
        packet_key = _bucket_value(row, "packet_key", default="")
        resume_key = _bucket_value(row, "resume_key", default="")
        reviewer_status = row["reviewer_status_normalized"]

        duplicate_counter[(packet_key, resume_key)] += 1

        if reviewer_status not in allowed_status_values:
            invalid_status_counter[reviewer_status] += 1
            issues.append(
                _reviewer_validation_issue(
                    "error",
                    "invalid_reviewer_status",
                    packet_key,
                    resume_key,
                    f"Invalid reviewer_status value: {reviewer_status}",
                )
            )

        for field_name, normalized_key in [
            ("deterministic_correct", "deterministic_correct_normalized"),
            ("live_better_than_deterministic", "live_better_than_deterministic_normalized"),
            ("live_blended_better_than_deterministic", "live_blended_better_than_deterministic_normalized"),
            ("equivalence_correct", "equivalence_correct_normalized"),
        ]:
            normalized_value = row.get(normalized_key, "missing")
            if normalized_value not in allowed_yes_no_values:
                invalid_yes_no_counter[f"{field_name}:{normalized_value}"] += 1
                issues.append(
                    _reviewer_validation_issue(
                        "error",
                        "invalid_yes_no_value",
                        packet_key,
                        resume_key,
                        f"Invalid {field_name} value: {normalized_value}",
                    )
                )

        if not packet_key:
            issues.append(
                _reviewer_validation_issue(
                    "error",
                    "missing_packet_key",
                    packet_key,
                    resume_key,
                    "Missing packet_key",
                )
            )

        if not resume_key:
            issues.append(
                _reviewer_validation_issue(
                    "error",
                    "missing_resume_key",
                    packet_key,
                    resume_key,
                    "Missing resume_key",
                )
            )

        if reviewer_status == "done":
            missing_fields = _reviewer_done_missing_fields(row)
            if missing_fields:
                issues.append(
                    _reviewer_validation_issue(
                        "error",
                        "done_row_missing_required_fields",
                        packet_key,
                        resume_key,
                        f"Done row missing required reviewer decisions: {', '.join(missing_fields)}",
                    )
                )

            for bucket_field in [
                "selection_outcome_bucket",
                "live_outcome_bucket",
                "equivalence_outcome_bucket",
                "fingerprint_relationship_bucket",
            ]:
                bucket_value = _bucket_value(row, bucket_field, default="")
                if not bucket_value:
                    issues.append(
                        _reviewer_validation_issue(
                            "warning",
                            "done_row_missing_bucket_context",
                            packet_key,
                            resume_key,
                            f"Done row missing {bucket_field}",
                        )
                    )

            disagreement_reasons: List[str] = []
            if row.get("deterministic_correct_normalized") == "no":
                disagreement_reasons.append("deterministic_incorrect")
            if row.get("live_better_than_deterministic_normalized") == "yes":
                disagreement_reasons.append("live_better")
            if row.get("live_blended_better_than_deterministic_normalized") == "yes":
                disagreement_reasons.append("live_blended_better")
            if row.get("equivalence_correct_normalized") == "no":
                disagreement_reasons.append("equivalence_incorrect")

            notes_text = str(row.get("reviewer_notes", "") or "").strip()

            if disagreement_reasons and not notes_text:
                issues.append(
                    _reviewer_validation_issue(
                        "warning",
                        "disagreement_missing_notes",
                        packet_key,
                        resume_key,
                        "Completed disagreement row is missing reviewer_notes",
                    )
                )

    for (packet_key, resume_key), count in sorted(duplicate_counter.items(), key=lambda item: (-item[1], item[0])):
        if count > 1:
            issues.append(
                _reviewer_validation_issue(
                    "error",
                    "duplicate_packet_resume_pair",
                    packet_key,
                    resume_key,
                    f"Duplicate (packet_key, resume_key) rows found: {count}",
                )
            )

    error_count = sum(1 for item in issues if item["severity"] == "error")
    warning_count = sum(1 for item in issues if item["severity"] == "warning")

    summary = {
        "mode": "reviewer_csv_validation",
        "total_rows": len(normalized_rows),
        "completed_rows": sum(
            1 for row in normalized_rows if row["reviewer_status_normalized"] == "done"
        ),
        "error_count": error_count,
        "warning_count": warning_count,
        "is_valid": error_count == 0,
        "issues": sorted(
            issues,
            key=lambda item: (
                item["severity"],
                item["issue_type"],
                item["packet_key"],
                item["resume_key"],
                item["message"],
            ),
        ),
        "issue_type_counts": _counter_to_sorted_rows(
            Counter(item["issue_type"] for item in issues),
            len(issues),
        ) if issues else [],
        "severity_counts": _counter_to_sorted_rows(
            Counter(item["severity"] for item in issues),
            len(issues),
        ) if issues else [],
        "invalid_reviewer_status_values": _counter_to_sorted_rows(
            invalid_status_counter,
            sum(invalid_status_counter.values()),
        ) if invalid_status_counter else [],
        "invalid_yes_no_values": _counter_to_sorted_rows(
            invalid_yes_no_counter,
            sum(invalid_yes_no_counter.values()),
        ) if invalid_yes_no_counter else [],
    }
    return summary


def _print_reviewer_validation(summary: Dict[str, Any]) -> None:
    print("\nReviewer CSV Validation")
    print("-----------------------")
    print(f"total_rows: {summary['total_rows']}")
    print(f"completed_rows: {summary['completed_rows']}")
    print(f"error_count: {summary['error_count']}")
    print(f"warning_count: {summary['warning_count']}")
    print(f"is_valid: {summary['is_valid']}")

    if summary.get("severity_counts"):
        _print_counter_block("Issue Severity Counts", summary["severity_counts"])

    if summary.get("issue_type_counts"):
        _print_counter_block("Issue Type Counts", summary["issue_type_counts"])

    if summary.get("invalid_reviewer_status_values"):
        _print_counter_block(
            "Invalid Reviewer Status Values",
            summary["invalid_reviewer_status_values"],
        )

    if summary.get("invalid_yes_no_values"):
        _print_counter_block(
            "Invalid Yes/No Values",
            summary["invalid_yes_no_values"],
        )

    print("\nValidation Issues")
    print("=================")
    if not summary.get("issues"):
        print("none")
        return

    for item in summary["issues"]:
        packet_key = item.get("packet_key", "") or "missing"
        resume_key = item.get("resume_key", "") or "missing"
        print(
            f"\n[{item['severity']}] {item['issue_type']} | "
            f"packet={packet_key} | resume={resume_key}"
        )
        print(f"  message: {item['message']}")


def _write_reviewer_validation_csv(path: Path, issues: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "severity",
        "issue_type",
        "packet_key",
        "resume_key",
        "message",
    ]

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for item in issues:
            writer.writerow(
                {
                    "severity": str(item.get("severity", "") or "").strip(),
                    "issue_type": str(item.get("issue_type", "") or "").strip(),
                    "packet_key": str(item.get("packet_key", "") or "").strip(),
                    "resume_key": str(item.get("resume_key", "") or "").strip(),
                    "message": str(item.get("message", "") or "").strip(),
                }
            )

def _build_reviewer_summary(rows: List[Dict[str, Any]], top_n: int) -> Dict[str, Any]:
    normalized_rows = _normalize_reviewer_rows(rows)

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

def _print_reviewer_summary(
    summary: Dict[str, Any],
    reviewer_rows_count: int,
    reviewer_csv_path: Path,
) -> None:
    print(
        f"Loaded {reviewer_rows_count} reviewer rows from {reviewer_csv_path}; "
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

def _write_reviewer_disagreement_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "batch_key",
        "source_path",
        "packet_key",
        "resume_key",
        "company",
        "title",
        "selection_outcome_bucket",
        "live_outcome_bucket",
        "equivalence_outcome_bucket",
        "fingerprint_relationship_bucket",
        "disagreement_reasons",
        "reviewer_notes",
    ]

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            writer.writerow(
                {
                    "batch_key": str(row.get("batch_key", "") or "").strip(),
                    "source_path": str(row.get("source_path", "") or "").strip(),
                    "packet_key": str(row.get("packet_key", "") or "").strip(),
                    "resume_key": str(row.get("resume_key", "") or "").strip(),
                    "company": str(row.get("company", "") or "").strip(),
                    "title": str(row.get("title", "") or "").strip(),
                    "selection_outcome_bucket": str(row.get("selection_outcome_bucket", "") or "").strip(),
                    "live_outcome_bucket": str(row.get("live_outcome_bucket", "") or "").strip(),
                    "equivalence_outcome_bucket": str(row.get("equivalence_outcome_bucket", "") or "").strip(),
                    "fingerprint_relationship_bucket": str(row.get("fingerprint_relationship_bucket", "") or "").strip(),
                    "disagreement_reasons": "|".join(row.get("disagreement_reasons", []) or []),
                    "reviewer_notes": str(row.get("reviewer_notes", "") or "").strip(),
                }
            )

def _write_reviewer_summary_outputs(
    summary: Dict[str, Any],
    output_json_path: Optional[Path] = None,
    reviewer_report_md_path: Optional[Path] = None,
    disagreement_csv_path: Optional[Path] = None,
) -> None:
    if output_json_path is not None:
        _write_json_file(output_json_path, summary)
        print(f"\nWrote summary JSON: {output_json_path}")

    if reviewer_report_md_path is not None:
        _write_reviewer_report_markdown(reviewer_report_md_path, summary)
        print(f"Wrote reviewer report markdown: {reviewer_report_md_path}")

    if disagreement_csv_path is not None:
        _write_reviewer_disagreement_csv(
            disagreement_csv_path,
            summary.get("disagreement_rows", []) or [],
        )
        print(f"Wrote disagreement CSV: {disagreement_csv_path}")

def _load_json_object(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object in {path}, got {type(value).__name__}")
    return value


def _resolve_summary_json_paths(
    input_values: List[str],
    glob_pattern: str,
) -> List[Path]:
    raw_paths: List[str] = []

    for raw_value in input_values:
        text = str(raw_value or "").strip()
        if not text:
            continue
        parts = [part.strip() for part in text.split(",") if part.strip()]
        raw_paths.extend(parts)

    if glob_pattern.strip():
        matched = sorted(glob.glob(glob_pattern.strip()))
        raw_paths.extend(matched)

    seen = set()
    resolved: List[Path] = []

    for raw_path in raw_paths:
        path = Path(raw_path)
        normalized = str(path)
        if normalized in seen:
            continue
        seen.add(normalized)
        if not path.exists():
            raise FileNotFoundError(f"Summary JSON file not found: {path}")
        resolved.append(path)

    if not resolved:
        raise ValueError("No summary JSON files resolved for rollup analysis.")

    resolved.sort(key=lambda path: str(path))
    return resolved


def _metric_from_summary(summary: Dict[str, Any], key: str) -> Dict[str, Any]:
    metrics = summary.get("headline_metrics", {}) or {}
    metric = metrics.get(key, {}) or {}
    numerator = int(metric.get("numerator", 0) or 0)
    denominator = int(metric.get("denominator", 0) or 0)
    pct = round((numerator / denominator) * 100.0, 2) if denominator else 0.0
    return {
        "numerator": numerator,
        "denominator": denominator,
        "pct": pct,
    }


def _rollup_metric(summaries: List[Dict[str, Any]], key: str) -> Dict[str, Any]:
    numerator = 0
    denominator = 0

    for summary in summaries:
        metric = _metric_from_summary(summary, key)
        numerator += int(metric["numerator"])
        denominator += int(metric["denominator"])

    pct = round((numerator / denominator) * 100.0, 2) if denominator else 0.0
    return {
        "numerator": numerator,
        "denominator": denominator,
        "pct": pct,
    }


def _build_rollup_recommendations(rollup: Dict[str, Any]) -> List[str]:
    metrics = rollup.get("weighted_headline_metrics", {}) or {}

    deterministic_metric = metrics.get("deterministic_correct_rate", {}) or {}
    live_metric = metrics.get("live_better_than_deterministic_rate", {}) or {}
    live_blended_metric = metrics.get("live_blended_better_than_deterministic_rate", {}) or {}
    equivalence_metric = metrics.get("equivalence_judgment_correct_rate", {}) or {}

    deterministic_num = int(deterministic_metric.get("numerator", 0) or 0)
    deterministic_den = int(deterministic_metric.get("denominator", 0) or 0)
    live_num = int(live_metric.get("numerator", 0) or 0)
    live_blended_num = int(live_blended_metric.get("numerator", 0) or 0)
    equivalence_num = int(equivalence_metric.get("numerator", 0) or 0)
    equivalence_den = int(equivalence_metric.get("denominator", 0) or 0)

    recommendations: List[str] = []

    if deterministic_den > 0 and deterministic_num == deterministic_den and live_num == 0 and live_blended_num == 0:
        recommendations.append(
            "Keep runtime winner selection deterministic-first. Across the reviewed batches in this rollup, there is no evidence that live or live_blended should replace deterministic selection."
        )
    else:
        recommendations.append(
            "Do not change runtime winner selection yet. The reviewed batches do not justify a runtime policy change without more labeled evidence."
        )

    if equivalence_den > 0 and equivalence_num < equivalence_den:
        recommendations.append(
            "Focus any next offline analysis on equivalence interpretation quality instead of winner selection logic, because at least one reviewed batch shows equivalence overstatement."
        )

    if live_num > 0 or live_blended_num > 0:
        recommendations.append(
            "Inspect the specific batches where live or live_blended beat deterministic before discussing any critic or runtime selector changes."
        )

    return recommendations


def _build_reviewer_summary_rollup(summary_paths: List[Path]) -> Dict[str, Any]:
    loaded_summaries: List[Dict[str, Any]] = []
    per_batch: List[Dict[str, Any]] = []
    disagreement_reason_counter: Counter = Counter()
    disagreement_rows: List[Dict[str, Any]] = []

    total_rows = 0
    completed_reviews = 0

    batches_with_live_wins: List[str] = []
    batches_with_live_blended_wins: List[str] = []
    batches_with_equivalence_errors: List[str] = []

    for path in summary_paths:
        summary = _load_json_object(path)
        if summary.get("mode") != "reviewer_csv":
            raise ValueError(
                f"Summary JSON {path} is not a reviewer CSV summary. Expected mode='reviewer_csv'."
            )

        loaded_summaries.append(summary)

        batch_key = path.stem
        total_rows_batch = int(summary.get("total_rows", 0) or 0)
        completed_reviews_batch = int(summary.get("completed_reviews", 0) or 0)
        completion_rate_pct = float(summary.get("completion_rate_pct", 0.0) or 0.0)

        deterministic_metric = _metric_from_summary(summary, "deterministic_correct_rate")
        live_metric = _metric_from_summary(summary, "live_better_than_deterministic_rate")
        live_blended_metric = _metric_from_summary(summary, "live_blended_better_than_deterministic_rate")
        equivalence_metric = _metric_from_summary(summary, "equivalence_judgment_correct_rate")

        batch_disagreement_rows = summary.get("disagreement_rows", []) or []
        disagreement_count = len(batch_disagreement_rows)

        for row in batch_disagreement_rows:
            disagreement_rows.append(
                {
                    "batch_key": batch_key,
                    "source_path": str(path),
                    "packet_key": str(row.get("packet_key", "") or "").strip(),
                    "resume_key": str(row.get("resume_key", "") or "").strip(),
                    "company": str(row.get("company", "") or "").strip(),
                    "title": str(row.get("title", "") or "").strip(),
                    "selection_outcome_bucket": str(row.get("selection_outcome_bucket", "") or "").strip(),
                    "live_outcome_bucket": str(row.get("live_outcome_bucket", "") or "").strip(),
                    "equivalence_outcome_bucket": str(row.get("equivalence_outcome_bucket", "") or "").strip(),
                    "fingerprint_relationship_bucket": str(row.get("fingerprint_relationship_bucket", "") or "").strip(),
                    "disagreement_reasons": list(row.get("disagreement_reasons", []) or []),
                    "reviewer_notes": str(row.get("reviewer_notes", "") or "").strip(),
                }
            )

        for row in batch_disagreement_rows:
            for reason in row.get("disagreement_reasons", []) or []:
                disagreement_reason_counter[str(reason).strip() or "missing"] += 1

        if int(live_metric["numerator"]) > 0:
            batches_with_live_wins.append(batch_key)
        if int(live_blended_metric["numerator"]) > 0:
            batches_with_live_blended_wins.append(batch_key)
        if int(equivalence_metric["numerator"]) < int(equivalence_metric["denominator"]):
            batches_with_equivalence_errors.append(batch_key)

        total_rows += total_rows_batch
        completed_reviews += completed_reviews_batch

        per_batch.append(
            {
                "batch_key": batch_key,
                "source_path": str(path),
                "total_rows": total_rows_batch,
                "completed_reviews": completed_reviews_batch,
                "completion_rate_pct": completion_rate_pct,
                "headline_metrics": {
                    "deterministic_correct_rate": deterministic_metric,
                    "live_better_than_deterministic_rate": live_metric,
                    "live_blended_better_than_deterministic_rate": live_blended_metric,
                    "equivalence_judgment_correct_rate": equivalence_metric,
                },
                "disagreement_count": disagreement_count,
                "recommendations": _reviewer_recommendations(summary),
            }
        )

    per_batch.sort(key=lambda row: row["batch_key"])

    disagreement_rows.sort(
        key=lambda row: (
            row["batch_key"],
            row["packet_key"],
            row["resume_key"],
        )
    )
    rollup = {
        "mode": "reviewer_summary_rollup",
        "batch_count": len(per_batch),
        "source_paths": [str(path) for path in summary_paths],
        "total_rows": total_rows,
        "completed_reviews": completed_reviews,
        "completion_rate_pct": round((completed_reviews / total_rows) * 100.0, 2) if total_rows else 0.0,
        "disagreement_count": len(disagreement_rows),
        "disagreement_rows": disagreement_rows,
        "weighted_headline_metrics": {
            "deterministic_correct_rate": _rollup_metric(loaded_summaries, "deterministic_correct_rate"),
            "live_better_than_deterministic_rate": _rollup_metric(
                loaded_summaries,
                "live_better_than_deterministic_rate",
            ),
            "live_blended_better_than_deterministic_rate": _rollup_metric(
                loaded_summaries,
                "live_blended_better_than_deterministic_rate",
            ),
            "equivalence_judgment_correct_rate": _rollup_metric(
                loaded_summaries,
                "equivalence_judgment_correct_rate",
            ),
        },
        "aggregate_disagreement_reasons": _counter_to_sorted_rows(
            disagreement_reason_counter,
            sum(disagreement_reason_counter.values()),
        ),
        "batches_with_live_wins": sorted(batches_with_live_wins),
        "batches_with_live_blended_wins": sorted(batches_with_live_blended_wins),
        "batches_with_equivalence_errors": sorted(batches_with_equivalence_errors),
        "per_batch": per_batch,
    }
    rollup["recommendations"] = _build_rollup_recommendations(rollup)
    return rollup


def _print_reviewer_summary_rollup(rollup: Dict[str, Any]) -> None:
    print("\nReviewer Summary Rollup")
    print("-----------------------")
    print(f"batch_count: {rollup['batch_count']}")
    print(f"total_rows: {rollup['total_rows']}")
    print(f"completed_reviews: {rollup['completed_reviews']}")
    print(f"completion_rate_pct: {rollup['completion_rate_pct']:.2f}%")

    _print_reviewer_headline_metrics(rollup["weighted_headline_metrics"])
    _print_counter_block(
        "Aggregate Disagreement Reasons",
        rollup["aggregate_disagreement_reasons"],
    )

    print("\nPer-Batch Metrics")
    print("-----------------")
    for batch in rollup["per_batch"]:
        print(
            f"\n{batch['batch_key']} | rows={batch['total_rows']} | "
            f"completed={batch['completed_reviews']} | "
            f"completion={batch['completion_rate_pct']:.2f}%"
        )
        for metric_key, metric_value in batch["headline_metrics"].items():
            print(
                f"  {metric_key}: "
                f"{metric_value['numerator']}/{metric_value['denominator']} "
                f"({metric_value['pct']:.2f}%)"
            )
        print(f"  disagreement_count: {batch['disagreement_count']}")

    print("\nRollup Recommendations")
    print("----------------------")
    for item in rollup.get("recommendations", []) or []:
        print(f"- {item}")


def _write_reviewer_summary_rollup_markdown(path: Path, rollup: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    metrics = rollup.get("weighted_headline_metrics", {}) or {}

    deterministic_metric = metrics.get("deterministic_correct_rate", {}) or {}
    live_metric = metrics.get("live_better_than_deterministic_rate", {}) or {}
    live_blended_metric = metrics.get("live_blended_better_than_deterministic_rate", {}) or {}
    equivalence_metric = metrics.get("equivalence_judgment_correct_rate", {}) or {}

    lines: List[str] = []
    lines.append("# Tailoring Reviewer Multi-Batch Rollup")
    lines.append("")
    lines.append("## Scope")
    lines.append(f"- batch count: {int(rollup.get('batch_count', 0) or 0)}")
    lines.append(f"- total rows: {int(rollup.get('total_rows', 0) or 0)}")
    lines.append(f"- completed reviews: {int(rollup.get('completed_reviews', 0) or 0)}")
    lines.append(f"- completion rate: {float(rollup.get('completion_rate_pct', 0.0) or 0.0):.2f}%")
    lines.append("")

    lines.append("## Weighted Headline Metrics")
    lines.append(f"- deterministic correct rate: {_headline_metric_text(deterministic_metric)}")
    lines.append(f"- live better than deterministic rate: {_headline_metric_text(live_metric)}")
    lines.append(f"- live blended better than deterministic rate: {_headline_metric_text(live_blended_metric)}")
    lines.append(f"- equivalence judgment correct rate: {_headline_metric_text(equivalence_metric)}")
    lines.append("")

    lines.append("## Recommendation")
    for recommendation in rollup.get("recommendations", []) or []:
        lines.append(f"- {recommendation}")
    lines.append("")

    lines.append("## Aggregate Disagreement Reasons")
    disagreement_rows = rollup.get("aggregate_disagreement_reasons", []) or []
    if disagreement_rows:
        for row in disagreement_rows:
            lines.append(f"- {row['key']}: {row['count']} ({row['pct']:.2f}%)")
    else:
        lines.append("- none")
    lines.append("")

    lines.append("## Per-Batch Metrics")
    for batch in rollup.get("per_batch", []) or []:
        lines.append(f"### {batch['batch_key']}")
        lines.append(f"- source path: {batch['source_path']}")
        lines.append(f"- total rows: {batch['total_rows']}")
        lines.append(f"- completed reviews: {batch['completed_reviews']}")
        lines.append(f"- completion rate: {batch['completion_rate_pct']:.2f}%")
        for metric_key, metric_value in (batch.get("headline_metrics", {}) or {}).items():
            lines.append(
                f"- {metric_key}: "
                f"{metric_value['numerator']}/{metric_value['denominator']} "
                f"({metric_value['pct']:.2f}%)"
            )
        lines.append(f"- disagreement count: {batch['disagreement_count']}")
        lines.append("")

    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

def _write_json_file(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _bundle_base_name_from_path(path: Path) -> str:
    stem = path.stem.strip().lower()
    if not stem:
        return "tailoring_reviewer"
    safe = []
    for ch in stem:
        if ch.isalnum() or ch in {"_", "-"}:
            safe.append(ch)
        else:
            safe.append("_")
    text = "".join(safe).strip("_")
    return text or "tailoring_reviewer"


def _run_reviewer_eval_bundle(
    reviewer_csv_path: Path,
    reviewer_rows: List[Dict[str, Any]],
    output_dir: Path,
    bundle_name: str,
    top_n: int,
) -> Dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)

    validation = _build_reviewer_validation(reviewer_rows)
    _print_reviewer_validation(validation)

    validation_json_path = output_dir / f"{bundle_name}_validation.json"
    validation_csv_path = output_dir / f"{bundle_name}_validation_issues.csv"

    _write_json_file(validation_json_path, validation)
    _write_reviewer_validation_csv(
        validation_csv_path,
        validation.get("issues", []) or [],
    )

    print(f"\nWrote validation JSON: {validation_json_path}")
    print(f"Wrote validation CSV: {validation_csv_path}")

    if not validation.get("is_valid", False):
        raise ValueError(
            f"Reviewer CSV validation failed for {reviewer_csv_path}. "
            f"Fix validation errors before running bundled evaluation."
        )

    summary = _build_reviewer_summary(reviewer_rows, top_n=top_n)

    _print_reviewer_summary(summary, len(reviewer_rows), reviewer_csv_path)

    summary_json_path = output_dir / f"{bundle_name}_human_agreement_summary.json"
    summary_report_md_path = output_dir / f"{bundle_name}_human_agreement_report.md"
    disagreement_csv_path = output_dir / f"{bundle_name}_disagreements.csv"

    _write_reviewer_summary_outputs(
        summary,
        output_json_path=summary_json_path,
        reviewer_report_md_path=summary_report_md_path,
        disagreement_csv_path=disagreement_csv_path,
    )

    rollup = _build_reviewer_summary_rollup([summary_json_path])
    _print_reviewer_summary_rollup(rollup)

    rollup_json_path = output_dir / f"{bundle_name}_human_agreement_rollup.json"
    rollup_md_path = output_dir / f"{bundle_name}_human_agreement_rollup.md"

    _write_json_file(rollup_json_path, rollup)
    _write_reviewer_summary_rollup_markdown(rollup_md_path, rollup)

    print(f"\nWrote rollup JSON: {rollup_json_path}")
    print(f"Wrote rollup markdown: {rollup_md_path}")

    return {
        "validation_json": str(validation_json_path),
        "validation_csv": str(validation_csv_path),
        "summary_json": str(summary_json_path),
        "summary_report_md": str(summary_report_md_path),
        "disagreement_csv": str(disagreement_csv_path),
        "rollup_json": str(rollup_json_path),
        "rollup_md": str(rollup_md_path),
    }

def _validate_mode_args(args: argparse.Namespace) -> None:
    reviewer_mode = bool(args.reviewer_csv_input.strip())
    rollup_mode = bool(args.summary_json_input or args.summary_json_glob.strip())

    if reviewer_mode and rollup_mode:
        raise ValueError(
            "Do not combine reviewer CSV mode with summary-rollup mode in one run."
        )

    if args.validate_reviewer_csv and not reviewer_mode:
        raise ValueError("--validate-reviewer-csv requires --reviewer-csv-input.")

    if args.run_reviewer_eval_bundle and not reviewer_mode:
        raise ValueError("--run-reviewer-eval-bundle requires --reviewer-csv-input.")

    if args.output_reviewer_report_md.strip() and not reviewer_mode:
        raise ValueError(
            "--output-reviewer-report-md requires --reviewer-csv-input."
        )

    if args.output_validation_csv.strip() and not reviewer_mode:
        raise ValueError("--output-validation-csv requires --reviewer-csv-input.")

    if args.output_summary_rollup_md.strip() and not rollup_mode:
        raise ValueError(
            "--output-summary-rollup-md requires summary-rollup mode."
        )

    if args.output_disagreement_csv.strip() and not (reviewer_mode or rollup_mode):
        raise ValueError(
            "--output-disagreement-csv requires reviewer CSV mode or summary-rollup mode."
        )

    if (args.bundle_output_dir.strip() or args.bundle_name.strip()) and not args.run_reviewer_eval_bundle:
        raise ValueError(
            "--bundle-output-dir and --bundle-name require --run-reviewer-eval-bundle."
        )

    if reviewer_mode or rollup_mode:
        jsonl_only_flags: List[str] = []

        if args.output_packet_comparisons_csv.strip():
            jsonl_only_flags.append("--output-packet-comparisons-csv")
        if args.output_reviewer_csv.strip():
            jsonl_only_flags.append("--output-reviewer-csv")
        if args.latest_per_packet_resume:
            jsonl_only_flags.append("--latest-per-packet-resume")
        if args.require_analysis_keys:
            jsonl_only_flags.append("--require-analysis-keys")

        if jsonl_only_flags:
            raise ValueError(
                "JSONL-analysis flags cannot be combined with reviewer/rollup modes: "
                + ", ".join(jsonl_only_flags)
            )

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
        "--validate-reviewer-csv",
        action="store_true",
        help="Validate a reviewer CSV for duplicates, invalid labels, and missing required fields.",
    )
    parser.add_argument(
        "--run-reviewer-eval-bundle",
        action="store_true",
        help="Run validation, summary, disagreement export, and single-batch rollup from one reviewer CSV.",
    )
    parser.add_argument(
        "--summary-json-input",
        action="append",
        default=[],
        help="Optional path to an existing reviewer summary JSON. Repeat this flag to roll up multiple batches.",
    )
    parser.add_argument(
        "--summary-json-glob",
        default="",
        help="Optional glob pattern for reviewer summary JSON files to include in rollup mode.",
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
    parser.add_argument(
        "--output-summary-rollup-md",
        default="",
        help="Optional path to write a markdown report for summary-rollup mode.",
    )
    parser.add_argument(
        "--output-disagreement-csv",
        default="",
        help="Optional path to write disagreement rows as a dedicated CSV in reviewer CSV mode or summary rollup mode.",
    )
    parser.add_argument(
        "--output-validation-csv",
        default="",
        help="Optional path to write reviewer CSV validation issues as a CSV.",
    )
    parser.add_argument(
        "--bundle-output-dir",
        default="",
        help=(
            "Output directory for bundled reviewer evaluation artifacts. "
            "Defaults to outputs/application_planning_archive/reviewer_eval."
        ),
    )
    parser.add_argument(
        "--bundle-name",
        default="",
        help="Optional basename prefix for bundled reviewer evaluation artifacts.",
    )

    args = parser.parse_args()
    _validate_mode_args(args)

    if args.summary_json_input or args.summary_json_glob.strip():
        summary_paths = _resolve_summary_json_paths(
            args.summary_json_input,
            args.summary_json_glob,
        )
        rollup = _build_reviewer_summary_rollup(summary_paths)
        _print_reviewer_summary_rollup(rollup)

        if args.output_json.strip():
            output_path = Path(args.output_json)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(
                json.dumps(rollup, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"\nWrote rollup JSON: {output_path}")

        if args.output_summary_rollup_md.strip():
            report_path = Path(args.output_summary_rollup_md)
            _write_reviewer_summary_rollup_markdown(report_path, rollup)
            print(f"Wrote rollup markdown: {report_path}")
        
        if args.output_disagreement_csv.strip():
            disagreement_csv_path = Path(args.output_disagreement_csv)
            _write_reviewer_disagreement_csv(
                disagreement_csv_path,
                rollup.get("disagreement_rows", []) or [],
            )
            print(f"Wrote disagreement CSV: {disagreement_csv_path}")

        return

    if args.reviewer_csv_input.strip():
        reviewer_csv_path = Path(args.reviewer_csv_input)
        if not reviewer_csv_path.exists():
            raise FileNotFoundError(f"Reviewer CSV file not found: {reviewer_csv_path}")

        reviewer_rows = _load_csv_rows(reviewer_csv_path)
        if not reviewer_rows:
            raise ValueError(f"No rows found in reviewer CSV: {reviewer_csv_path}")
        
        if args.run_reviewer_eval_bundle:
            bundle_output_dir = (
                Path(args.bundle_output_dir.strip())
                if args.bundle_output_dir.strip()
                else DEFAULT_REVIEWER_EVAL_BUNDLE_OUTPUT_DIR
            )
            bundle_name = (
                args.bundle_name.strip()
                or _bundle_base_name_from_path(reviewer_csv_path)
            )

            written_paths = _run_reviewer_eval_bundle(
                reviewer_csv_path=reviewer_csv_path,
                reviewer_rows=reviewer_rows,
                output_dir=bundle_output_dir,
                bundle_name=bundle_name,
                top_n=max(args.top_n, 1),
            )

            print("\nBundled Reviewer Evaluation Outputs")
            print("-----------------------------------")
            for key, value in written_paths.items():
                print(f"{key}: {value}")

            return
        
        if args.validate_reviewer_csv:
            validation = _build_reviewer_validation(reviewer_rows)
            _print_reviewer_validation(validation)

            if args.output_json.strip():
                output_path = Path(args.output_json)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(
                    json.dumps(validation, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                print(f"\nWrote validation JSON: {output_path}")

            if args.output_validation_csv.strip():
                validation_csv_path = Path(args.output_validation_csv)
                _write_reviewer_validation_csv(
                    validation_csv_path,
                    validation.get("issues", []) or [],
                )
                print(f"Wrote validation CSV: {validation_csv_path}")

            return

        summary = _build_reviewer_summary(reviewer_rows, top_n=max(args.top_n, 1))

        _print_reviewer_summary(summary, len(reviewer_rows), reviewer_csv_path)

        _write_reviewer_summary_outputs(
            summary,
            output_json_path=Path(args.output_json) if args.output_json.strip() else None,
            reviewer_report_md_path=(
                Path(args.output_reviewer_report_md)
                if args.output_reviewer_report_md.strip()
                else None
            ),
            disagreement_csv_path=(
                Path(args.output_disagreement_csv)
                if args.output_disagreement_csv.strip()
                else None
            ),
        )

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