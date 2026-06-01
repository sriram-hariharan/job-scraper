from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List


REQUIRED_ARTIFACTS = [
    "application_execution_queue.csv",
    "job_prioritization_recommendations.csv",
    "tailoring_decision_recommendations.csv",
    "tailoring_decision_summary.json",
    "operator_review_recommendations.csv",
    "operator_review_summary.json",
    "agentic_workflow_summary.json",
    "agentic_workflow_summary.md",
]

OPTIONAL_ARTIFACTS = [
    "best_resume_variant_by_job.csv",
    "source_health_report.csv",
]

EXPECTED_ARTIFACTS = REQUIRED_ARTIFACTS + OPTIONAL_ARTIFACTS


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _truthy(value: Any) -> bool:
    return _clean_text(value).lower() in {"1", "true", "yes", "y", "on"}


def _read_csv_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists() or not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists() or not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return dict(payload) if isinstance(payload, dict) else {}


def _artifact_content_text(row: Dict[str, Any]) -> str:
    value = row.get("content_text")
    if value:
        return str(value)
    content_json = row.get("content_json")
    if content_json is not None:
        return json.dumps(content_json)
    return ""


def _csv_rows_from_text(text: str) -> List[Dict[str, str]]:
    if not str(text or "").strip():
        return []
    return [dict(row) for row in csv.DictReader(str(text).splitlines())]


def _json_from_text(text: str) -> Dict[str, Any]:
    if not str(text or "").strip():
        return {}
    try:
        payload = json.loads(text)
    except Exception:
        return {}
    return dict(payload) if isinstance(payload, dict) else {}


def _rows_by_artifact_name(artifact_rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {
        _clean_text(row.get("artifact_name")): dict(row)
        for row in artifact_rows
        if _clean_text(row.get("artifact_name"))
    }


def _load_artifacts_from_dir(output_dir: str | Path) -> Dict[str, Any]:
    root = Path(output_dir)
    return {
        "application_execution_queue.csv": _read_csv_rows(root / "application_execution_queue.csv"),
        "best_resume_variant_by_job.csv": _read_csv_rows(root / "best_resume_variant_by_job.csv"),
        "source_health_report.csv": _read_csv_rows(root / "source_health_report.csv"),
        "job_prioritization_recommendations.csv": _read_csv_rows(root / "job_prioritization_recommendations.csv"),
        "tailoring_decision_recommendations.csv": _read_csv_rows(root / "tailoring_decision_recommendations.csv"),
        "operator_review_recommendations.csv": _read_csv_rows(root / "operator_review_recommendations.csv"),
        "agentic_workflow_summary.json": _read_json(root / "agentic_workflow_summary.json"),
    }


def _load_artifacts_from_rows(artifact_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_name = _rows_by_artifact_name(artifact_rows)
    loaded: Dict[str, Any] = {}
    for name in EXPECTED_ARTIFACTS:
        text = _artifact_content_text(by_name.get(name, {}))
        if name.endswith(".csv"):
            loaded[name] = _csv_rows_from_text(text)
        elif name.endswith(".json"):
            loaded[name] = _json_from_text(text)
        else:
            loaded[name] = text
    return loaded


def _present_artifacts_from_dir(output_dir: str | Path) -> set[str]:
    root = Path(output_dir)
    return {name for name in EXPECTED_ARTIFACTS if (root / name).exists()}


def _present_artifacts_from_rows(artifact_rows: List[Dict[str, Any]]) -> set[str]:
    return set(_rows_by_artifact_name(artifact_rows))


def _job_key(row: Dict[str, Any]) -> str:
    return "||".join(
        [
            _clean_text(row.get("job_id") or row.get("job_doc_id")),
            _clean_text(row.get("company") or row.get("job_company")),
            _clean_text(row.get("title") or row.get("job_title")),
            _clean_text(row.get("source")),
        ]
    ).lower()


def _count_by(rows: List[Dict[str, Any]], field: str) -> Dict[str, int]:
    return dict(sorted(Counter(_clean_text(row.get(field)) or "<empty>" for row in rows).items()))


def _check(name: str, passed: bool, reason: str = "") -> Dict[str, Any]:
    return {
        "name": name,
        "passed": bool(passed),
        "reason": reason,
    }


def verify_agentic_workflow_artifacts(
    *,
    output_dir: str | Path | None = None,
    artifact_rows: List[Dict[str, Any]] | None = None,
    strict: bool = False,
) -> Dict[str, Any]:
    if output_dir is None and artifact_rows is None:
        raise ValueError("Provide output_dir or artifact_rows.")

    if artifact_rows is not None:
        loaded = _load_artifacts_from_rows(list(artifact_rows or []))
        present_artifacts = _present_artifacts_from_rows(list(artifact_rows or []))
    else:
        loaded = _load_artifacts_from_dir(output_dir or "")
        present_artifacts = _present_artifacts_from_dir(output_dir or "")

    missing_required = [name for name in REQUIRED_ARTIFACTS if name not in present_artifacts]
    missing_optional = [name for name in OPTIONAL_ARTIFACTS if name not in present_artifacts]
    missing_artifacts = missing_required + missing_optional

    queue_rows = list(loaded.get("application_execution_queue.csv") or [])
    priority_rows = list(loaded.get("job_prioritization_recommendations.csv") or [])
    tailoring_rows = list(loaded.get("tailoring_decision_recommendations.csv") or [])
    operator_rows = list(loaded.get("operator_review_recommendations.csv") or [])
    summary_json = dict(loaded.get("agentic_workflow_summary.json") or {})

    reason_codes: List[str] = []
    checks: List[Dict[str, Any]] = []

    if missing_required:
        reason_codes.append("missing_required_artifacts")
    if missing_optional:
        reason_codes.append("missing_optional_artifacts")

    queue_action_by_key = {_job_key(row): _clean_text(row.get("action")) for row in queue_rows if _job_key(row)}
    for artifact_name, rows in [
        ("job_prioritization_recommendations.csv", priority_rows),
        ("tailoring_decision_recommendations.csv", tailoring_rows),
        ("operator_review_recommendations.csv", operator_rows),
    ]:
        mismatches = []
        for row in rows:
            key = _job_key(row)
            expected_action = queue_action_by_key.get(key)
            existing_action = _clean_text(row.get("existing_action"))
            if expected_action and existing_action and expected_action != existing_action:
                mismatches.append(key)
        checks.append(
            _check(
                f"{artifact_name}: existing_action_preserved",
                not mismatches,
                f"{len(mismatches)} mismatch(es)" if mismatches else "",
            )
        )
        if mismatches:
            reason_codes.append("existing_action_mismatch")

    missing_priority = [row for row in priority_rows if not _clean_text(row.get("advisory_priority"))]
    checks.append(_check("job_prioritization_rows_have_advisory_priority", not missing_priority))
    if missing_priority:
        reason_codes.append("missing_advisory_priority")

    missing_tailoring = [row for row in tailoring_rows if not _clean_text(row.get("tailoring_decision"))]
    checks.append(_check("tailoring_rows_have_tailoring_decision", not missing_tailoring))
    if missing_tailoring:
        reason_codes.append("missing_tailoring_decision")

    missing_operator = [row for row in operator_rows if not _clean_text(row.get("operator_review_lane"))]
    checks.append(_check("operator_rows_have_operator_review_lane", not missing_operator))
    if missing_operator:
        reason_codes.append("missing_operator_review_lane")

    actual_operator_counts = _count_by(operator_rows, "operator_review_lane") if operator_rows else {}
    summary_operator_counts = dict(summary_json.get("operator_review_lane_counts") or {})
    counts_match = not operator_rows or actual_operator_counts == summary_operator_counts
    checks.append(
        _check(
            "workflow_summary_operator_lane_counts_match",
            counts_match,
            f"expected {actual_operator_counts}, found {summary_operator_counts}" if not counts_match else "",
        )
    )
    if not counts_match:
        reason_codes.append("workflow_summary_operator_count_mismatch")

    bad_fallback_ready = [
        row for row in operator_rows
        if _truthy(row.get("fallback_only_no_deterministic_match"))
        and _clean_text(row.get("operator_review_lane")) == "ready_to_apply"
    ]
    checks.append(_check("fallback_only_rows_not_ready_to_apply", not bad_fallback_ready))
    if bad_fallback_ready:
        reason_codes.append("fallback_only_ready_to_apply")

    bad_packet_block_ready = [
        row for row in operator_rows
        if (
            _clean_text(row.get("packet_generation_allowed")).lower() == "false"
            or _clean_text(row.get("packet_generation_block_reason"))
        )
        and _clean_text(row.get("operator_review_lane")) == "ready_to_apply"
    ]
    checks.append(_check("packet_blocked_rows_not_ready_to_apply", not bad_packet_block_ready))
    if bad_packet_block_ready:
        reason_codes.append("packet_blocked_ready_to_apply")

    required_failure = bool(missing_required)
    strict_missing_failure = bool(strict and missing_artifacts)
    consistency_failure = any(not check["passed"] for check in checks)
    if required_failure or strict_missing_failure or consistency_failure:
        validation_status = "failed"
    elif missing_optional:
        validation_status = "warning"
    else:
        validation_status = "passed"

    return {
        "validation_status": validation_status,
        "strict": bool(strict),
        "checked_artifacts": sorted(present_artifacts),
        "missing_artifacts": missing_artifacts,
        "row_counts": {
            "application_execution_queue": len(queue_rows),
            "best_resume_variant_by_job": len(list(loaded.get("best_resume_variant_by_job.csv") or [])),
            "source_health_report": len(list(loaded.get("source_health_report.csv") or [])),
            "job_prioritization_recommendations": len(priority_rows),
            "tailoring_decision_recommendations": len(tailoring_rows),
            "operator_review_recommendations": len(operator_rows),
        },
        "consistency_checks": checks,
        "reason_codes": sorted(set(reason_codes)),
        "summary": {
            "required_missing_count": len(missing_required),
            "optional_missing_count": len(missing_optional),
            "failed_check_count": sum(1 for check in checks if not check["passed"]),
        },
    }


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify agentic workflow artifacts for a completed run.")
    parser.add_argument("--output-dir", default="outputs/application_planning", help="Run artifact output directory.")
    parser.add_argument("--strict", action="store_true", help="Fail when optional expected artifacts are missing.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args(argv)

    payload = verify_agentic_workflow_artifacts(output_dir=args.output_dir, strict=args.strict)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Agentic workflow verifier: {payload['validation_status']}")
        print(f"Checked artifacts: {len(payload['checked_artifacts'])}")
        print(f"Missing artifacts: {', '.join(payload['missing_artifacts']) or 'none'}")
        if payload["reason_codes"]:
            print(f"Reason codes: {', '.join(payload['reason_codes'])}")
    return 0 if payload["validation_status"] in {"passed", "warning"} else 1


if __name__ == "__main__":
    sys.exit(main())
