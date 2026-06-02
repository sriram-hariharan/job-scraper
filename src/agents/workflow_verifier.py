from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

from src.agents import workflow_planner, workflow_registry, workflow_runner
from src.evaluation.rag_evaluation import (
    RAG_EVALUATION_SUMMARY_ARTIFACT,
    validate_rag_evaluation_payload,
)


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
    "agentic_workflow_manifest.json",
    "agentic_workflow_manifest.md",
    "agentic_workflow_execution_plan.json",
    "agentic_workflow_execution_plan.md",
    "agentic_workflow_dry_run_result.json",
    "agentic_workflow_dry_run_report.md",
    "best_resume_variant_by_job.csv",
    "source_health_report.csv",
    "rag_evaluation_summary.json",
    "rag_evaluation_report.md",
]

EXPECTED_ARTIFACTS = REQUIRED_ARTIFACTS + OPTIONAL_ARTIFACTS
VERIFICATION_JSON_NAME = "agentic_workflow_verification.json"

ARTIFACT_KIND_TO_NAME = {
    "source_health_report": "source_health_report.csv",
    "best_resume_variant_by_job": "best_resume_variant_by_job.csv",
    "application_shortlist_by_job": "application_shortlist_by_job.csv",
    "application_execution_queue": "application_execution_queue.csv",
    "job_prioritization_recommendations": "job_prioritization_recommendations.csv",
    "job_prioritization_summary": "job_prioritization_summary.json",
    "tailoring_decision_recommendations": "tailoring_decision_recommendations.csv",
    "tailoring_decision_summary": "tailoring_decision_summary.json",
    "operator_review_recommendations": "operator_review_recommendations.csv",
    "operator_review_summary": "operator_review_summary.json",
    "agentic_workflow_summary_json": "agentic_workflow_summary.json",
    "agentic_workflow_summary_md": "agentic_workflow_summary.md",
    "agentic_workflow_manifest_json": "agentic_workflow_manifest.json",
    "agentic_workflow_manifest_md": "agentic_workflow_manifest.md",
    "agentic_workflow_execution_plan_json": "agentic_workflow_execution_plan.json",
    "agentic_workflow_execution_plan_md": "agentic_workflow_execution_plan.md",
    "agentic_workflow_dry_run_result_json": "agentic_workflow_dry_run_result.json",
    "agentic_workflow_dry_run_report_md": "agentic_workflow_dry_run_report.md",
    "agentic_workflow_verification_json": "agentic_workflow_verification.json",
    "rag_evaluation_summary_json": "rag_evaluation_summary.json",
    "rag_evaluation_report_md": "rag_evaluation_report.md",
    "job_packet_manifest": "job_packet_manifest.csv",
}


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
        "agentic_workflow_manifest.json": _read_json(root / "agentic_workflow_manifest.json"),
        "agentic_workflow_execution_plan.json": _read_json(root / "agentic_workflow_execution_plan.json"),
        "agentic_workflow_dry_run_result.json": _read_json(root / "agentic_workflow_dry_run_result.json"),
        RAG_EVALUATION_SUMMARY_ARTIFACT: _read_json(root / RAG_EVALUATION_SUMMARY_ARTIFACT),
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
    manifest_json = dict(loaded.get("agentic_workflow_manifest.json") or {})
    execution_plan_json = dict(loaded.get("agentic_workflow_execution_plan.json") or {})
    dry_run_json = dict(loaded.get("agentic_workflow_dry_run_result.json") or {})
    rag_evaluation_json = dict(loaded.get(RAG_EVALUATION_SUMMARY_ARTIFACT) or {})

    reason_codes: List[str] = []
    checks: List[Dict[str, Any]] = []

    if missing_required:
        reason_codes.append("missing_required_artifacts")
    if missing_optional:
        reason_codes.append("missing_optional_artifacts")

    if not manifest_json:
        reason_codes.append("missing_workflow_manifest")
    else:
        manifest_validation = workflow_registry.validate_agentic_workflow_manifest(manifest_json)
        manifest_validation_passed = manifest_validation.get("validation_status") == "passed"
        checks.append(
            _check(
                "workflow_manifest_validation_passed",
                manifest_validation_passed,
                ", ".join(manifest_validation.get("reason_codes", []) or [])
                if not manifest_validation_passed else "",
            )
        )
        if not manifest_validation_passed:
            reason_codes.append("workflow_manifest_validation_failed")

        ordered_keys = list(manifest_json.get("ordered_agent_keys") or [])
        known_keys = set(workflow_registry.ORDERED_AGENT_KEYS)
        unknown_keys = [key for key in ordered_keys if key not in known_keys]
        checks.append(
            _check(
                "workflow_manifest_ordered_agents_known",
                not unknown_keys,
                f"unknown: {', '.join(unknown_keys)}" if unknown_keys else "",
            )
        )
        if unknown_keys:
            reason_codes.append("workflow_manifest_unknown_agent_keys")

        generated_kinds = set(manifest_json.get("generated_artifact_kinds") or [])
        required_from_manifest = [
            ARTIFACT_KIND_TO_NAME[kind]
            for kind in sorted(generated_kinds)
            if ARTIFACT_KIND_TO_NAME.get(kind) in REQUIRED_ARTIFACTS
        ]
        missing_manifest_required = [
            name for name in required_from_manifest if name not in present_artifacts
        ]
        checks.append(
            _check(
                "workflow_manifest_required_artifacts_present",
                not missing_manifest_required,
                f"missing: {', '.join(missing_manifest_required)}"
                if missing_manifest_required else "",
            )
        )
        if missing_manifest_required:
            reason_codes.append("workflow_manifest_required_artifacts_missing")

    if not execution_plan_json:
        reason_codes.append("missing_workflow_execution_plan")
    else:
        plan_manifest = manifest_json if manifest_json else None
        plan_validation = workflow_planner.validate_agentic_workflow_execution_plan(
            execution_plan_json,
            manifest=plan_manifest,
        )
        plan_validation_passed = plan_validation.get("validation_status") == "passed"
        checks.append(
            _check(
                "workflow_execution_plan_validation_passed",
                plan_validation_passed,
                ", ".join(plan_validation.get("reason_codes", []) or [])
                if not plan_validation_passed else "",
            )
        )
        if not plan_validation_passed:
            reason_codes.append("workflow_execution_plan_validation_failed")

        dry_run_mode = _clean_text(execution_plan_json.get("execution_mode")) == "dry_run"
        checks.append(_check("workflow_execution_plan_dry_run_mode", dry_run_mode))
        if not dry_run_mode:
            reason_codes.append("workflow_execution_plan_not_dry_run")

        plan_steps = list(execution_plan_json.get("ordered_steps") or [])
        enabled_steps = [
            _clean_text(step.get("agent_key"))
            for step in plan_steps
            if step.get("execution_enabled")
        ]
        checks.append(
            _check(
                "workflow_execution_plan_steps_disabled",
                not enabled_steps,
                f"enabled: {', '.join(enabled_steps)}" if enabled_steps else "",
            )
        )
        if enabled_steps:
            reason_codes.append("workflow_execution_plan_step_enabled")

        not_planned_steps = [
            _clean_text(step.get("agent_key"))
            for step in plan_steps
            if _clean_text(step.get("execution_status")) != "planned"
        ]
        checks.append(
            _check(
                "workflow_execution_plan_steps_planned",
                not not_planned_steps,
                f"not planned: {', '.join(not_planned_steps)}" if not_planned_steps else "",
            )
        )
        if not_planned_steps:
            reason_codes.append("workflow_execution_plan_step_not_planned")

        expected_order = (
            list(manifest_json.get("ordered_agent_keys") or [])
            if manifest_json
            else list(workflow_registry.ORDERED_AGENT_KEYS)
        )
        plan_order = [_clean_text(step.get("agent_key")) for step in plan_steps]
        order_matches = plan_order == expected_order
        checks.append(
            _check(
                "workflow_execution_plan_order_matches_registry",
                order_matches,
                f"expected {expected_order}, found {plan_order}" if not order_matches else "",
            )
        )
        if not order_matches:
            reason_codes.append("workflow_execution_plan_order_mismatch")

    if not dry_run_json:
        reason_codes.append("missing_workflow_dry_run_result")
    else:
        dry_run_validation = workflow_runner.validate_agentic_workflow_dry_run_result(
            dry_run_json,
            plan=execution_plan_json if execution_plan_json else None,
        )
        dry_run_validation_passed = dry_run_validation.get("validation_status") == "passed"
        checks.append(
            _check(
                "workflow_dry_run_validation_passed",
                dry_run_validation_passed,
                ", ".join(dry_run_validation.get("reason_codes", []) or [])
                if not dry_run_validation_passed else "",
            )
        )
        if not dry_run_validation_passed:
            reason_codes.append("workflow_dry_run_validation_failed")

        dry_run_mode = _clean_text(dry_run_json.get("execution_mode")) == "dry_run"
        checks.append(_check("workflow_dry_run_mode", dry_run_mode))
        if not dry_run_mode:
            reason_codes.append("workflow_dry_run_not_dry_run")

        executed_zero = int(dry_run_json.get("executed_step_count") or 0) == 0
        checks.append(_check("workflow_dry_run_executed_step_count_zero", executed_zero))
        if not executed_zero:
            reason_codes.append("workflow_dry_run_executed_step_count_nonzero")

        dry_run_steps = list(dry_run_json.get("ordered_step_results") or [])
        executed_steps = [
            _clean_text(step.get("agent_key"))
            for step in dry_run_steps
            if step.get("did_execute")
        ]
        checks.append(
            _check(
                "workflow_dry_run_steps_not_executed",
                not executed_steps,
                f"executed: {', '.join(executed_steps)}" if executed_steps else "",
            )
        )
        if executed_steps:
            reason_codes.append("workflow_dry_run_step_executed")

        enabled_dry_run_steps = [
            _clean_text(step.get("agent_key"))
            for step in dry_run_steps
            if step.get("execution_enabled")
        ]
        checks.append(
            _check(
                "workflow_dry_run_steps_disabled",
                not enabled_dry_run_steps,
                f"enabled: {', '.join(enabled_dry_run_steps)}" if enabled_dry_run_steps else "",
            )
        )
        if enabled_dry_run_steps:
            reason_codes.append("workflow_dry_run_step_enabled")

        not_skipped_steps = [
            _clean_text(step.get("agent_key"))
            for step in dry_run_steps
            if _clean_text(step.get("execution_status")) != "skipped_dry_run"
        ]
        checks.append(
            _check(
                "workflow_dry_run_steps_skipped",
                not not_skipped_steps,
                f"not skipped: {', '.join(not_skipped_steps)}" if not_skipped_steps else "",
            )
        )
        if not_skipped_steps:
            reason_codes.append("workflow_dry_run_step_not_skipped")

        expected_count = (
            len(list(execution_plan_json.get("ordered_steps") or []))
            if execution_plan_json
            else len(workflow_registry.ORDERED_AGENT_KEYS)
        )
        count_matches = int(dry_run_json.get("planned_step_count") or 0) == expected_count
        checks.append(
            _check(
                "workflow_dry_run_planned_step_count_matches_registry",
                count_matches,
                f"expected {expected_count}, found {dry_run_json.get('planned_step_count')}"
                if not count_matches else "",
            )
        )
        if not count_matches:
            reason_codes.append("workflow_dry_run_planned_step_count_mismatch")

    if RAG_EVALUATION_SUMMARY_ARTIFACT in present_artifacts:
        rag_validation = validate_rag_evaluation_payload(rag_evaluation_json)
        rag_validation_status = _clean_text(rag_validation.get("validation_status"))
        rag_validation_passed = rag_validation_status in {"passed", "warning"}
        checks.append(
            _check(
                "rag_evaluation_validation_passed_or_warning",
                rag_validation_passed,
                ", ".join(rag_validation.get("reason_codes", []) or [])
                if not rag_validation_passed else "",
            )
        )
        if not rag_validation_passed:
            reason_codes.append("rag_evaluation_validation_failed")
        if rag_validation_status == "warning":
            reason_codes.append("rag_evaluation_warning")

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
    diagnostic_warning = "rag_evaluation_warning" in reason_codes
    if required_failure or strict_missing_failure or consistency_failure:
        validation_status = "failed"
    elif missing_optional or diagnostic_warning:
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
            "rag_evaluation_rows": len(list(rag_evaluation_json.get("rows") or [])),
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


def write_agentic_workflow_verification_artifact(
    *,
    output_dir: str | Path,
    output_json_path: str | Path | None = None,
    strict: bool = False,
) -> Dict[str, Any]:
    payload = verify_agentic_workflow_artifacts(output_dir=output_dir, strict=strict)
    output_path = Path(output_json_path) if output_json_path else Path(output_dir) / VERIFICATION_JSON_NAME
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "json_path": str(output_path),
        "payload": payload,
        "validation_status": payload.get("validation_status", ""),
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
