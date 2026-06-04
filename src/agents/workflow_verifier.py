from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

from src.agents import (
    orchestrator_adapter_harness,
    proposal_only_mutation_planner,
    read_only_adapter_chain,
    read_only_chain_artifact_generator,
    dry_run_execution_simulator,
    workflow_planner,
    workflow_registry,
    workflow_runner,
)
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
    "read_only_adapter_preflight.json",
    "read_only_adapter_preflight.md",
    "read_only_adapter_chain_result.json",
    "read_only_adapter_chain_report.md",
    "read_only_chain_artifact_generation_result.json",
    "read_only_chain_artifact_generation_report.md",
    "dry_run_execution_simulation_result.json",
    "dry_run_execution_simulation_report.md",
    "proposal_only_mutation_plan_result.json",
    "proposal_only_mutation_plan_report.md",
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
    "read_only_adapter_preflight_json": "read_only_adapter_preflight.json",
    "read_only_adapter_preflight_md": "read_only_adapter_preflight.md",
    "read_only_adapter_chain_result_json": "read_only_adapter_chain_result.json",
    "read_only_adapter_chain_report_md": "read_only_adapter_chain_report.md",
    "read_only_chain_artifact_generation_result_json": "read_only_chain_artifact_generation_result.json",
    "read_only_chain_artifact_generation_report_md": "read_only_chain_artifact_generation_report.md",
    "dry_run_execution_simulation_result_json": "dry_run_execution_simulation_result.json",
    "dry_run_execution_simulation_report_md": "dry_run_execution_simulation_report.md",
    "proposal_only_mutation_plan_result_json": "proposal_only_mutation_plan_result.json",
    "proposal_only_mutation_plan_report_md": "proposal_only_mutation_plan_report.md",
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
        "read_only_adapter_preflight.json": _read_json(root / "read_only_adapter_preflight.json"),
        "read_only_adapter_chain_result.json": _read_json(root / "read_only_adapter_chain_result.json"),
        "read_only_chain_artifact_generation_result.json": _read_json(root / "read_only_chain_artifact_generation_result.json"),
        "dry_run_execution_simulation_result.json": _read_json(root / "dry_run_execution_simulation_result.json"),
        "proposal_only_mutation_plan_result.json": _read_json(root / "proposal_only_mutation_plan_result.json"),
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
    read_only_preflight_json = dict(loaded.get("read_only_adapter_preflight.json") or {})
    read_only_chain_json = dict(loaded.get("read_only_adapter_chain_result.json") or {})
    read_only_chain_generation_json = dict(loaded.get("read_only_chain_artifact_generation_result.json") or {})
    dry_run_simulation_json = dict(loaded.get("dry_run_execution_simulation_result.json") or {})
    proposal_plan_json = dict(loaded.get("proposal_only_mutation_plan_result.json") or {})
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

    if "read_only_adapter_preflight.json" in present_artifacts:
        preflight_validation = orchestrator_adapter_harness.validate_read_only_adapter_preflight_plan(
            read_only_preflight_json,
            manifest=manifest_json if manifest_json else None,
        )
        preflight_validation_status = _clean_text(preflight_validation.get("validation_status"))
        preflight_validation_passed = preflight_validation_status in {"passed", "warning"}
        checks.append(
            _check(
                "read_only_adapter_preflight_validation_passed_or_warning",
                preflight_validation_passed,
                ", ".join(preflight_validation.get("reason_codes", []) or [])
                if not preflight_validation_passed else "",
            )
        )
        if not preflight_validation_passed:
            reason_codes.append("read_only_adapter_preflight_validation_failed")
        if preflight_validation_status == "warning":
            reason_codes.append("read_only_adapter_preflight_warning")

        preflight_results = list(read_only_preflight_json.get("adapter_preflight_results") or [])
        preflight_mode = _clean_text(read_only_preflight_json.get("execution_mode")) == "read_only_preflight"
        checks.append(_check("read_only_adapter_preflight_mode", preflight_mode))
        if not preflight_mode:
            reason_codes.append("read_only_adapter_preflight_wrong_mode")

        allow_execution_false = not bool(read_only_preflight_json.get("allow_agent_execution"))
        checks.append(_check("read_only_adapter_preflight_agent_execution_disallowed", allow_execution_false))
        if not allow_execution_false:
            reason_codes.append("read_only_adapter_preflight_allows_agent_execution")

        executable_zero = int(read_only_preflight_json.get("executable_adapter_count") or 0) == 0
        checks.append(_check("read_only_adapter_preflight_executable_count_zero", executable_zero))
        if not executable_zero:
            reason_codes.append("read_only_adapter_preflight_executable_count_nonzero")

        enabled_adapters = [
            _clean_text(result.get("agent_key"))
            for result in preflight_results
            if result.get("execution_enabled")
        ]
        checks.append(
            _check(
                "read_only_adapter_preflight_adapters_disabled",
                not enabled_adapters,
                f"enabled: {', '.join(enabled_adapters)}" if enabled_adapters else "",
            )
        )
        if enabled_adapters:
            reason_codes.append("read_only_adapter_preflight_adapter_enabled")

        executed_adapters = [
            _clean_text(result.get("agent_key"))
            for result in preflight_results
            if result.get("did_execute")
        ]
        checks.append(
            _check(
                "read_only_adapter_preflight_adapters_not_executed",
                not executed_adapters,
                f"executed: {', '.join(executed_adapters)}" if executed_adapters else "",
            )
        )
        if executed_adapters:
            reason_codes.append("read_only_adapter_preflight_adapter_executed")

    if "read_only_adapter_chain_result.json" in present_artifacts:
        chain_validation = read_only_adapter_chain.validate_read_only_adapter_chain_result(
            read_only_chain_json
        )
        chain_validation_status = _clean_text(chain_validation.get("validation_status"))
        chain_validation_passed = chain_validation_status in {"passed", "warning"}
        checks.append(
            _check(
                "read_only_adapter_chain_validation_passed_or_warning",
                chain_validation_passed,
                ", ".join(chain_validation.get("reason_codes", []) or [])
                if not chain_validation_passed else "",
            )
        )
        if not chain_validation_passed:
            reason_codes.append("read_only_adapter_chain_validation_failed")
        if chain_validation_status == "warning":
            reason_codes.append("read_only_adapter_chain_warning")

        chain_mode = (
            _clean_text(read_only_chain_json.get("execution_mode"))
            == read_only_adapter_chain.EXECUTION_MODE
        )
        checks.append(_check("read_only_adapter_chain_manual_mode", chain_mode))
        if not chain_mode:
            reason_codes.append("read_only_adapter_chain_wrong_mode")

        chain_not_mutated = not bool(read_only_chain_json.get("did_mutate_production"))
        checks.append(_check("read_only_adapter_chain_did_not_mutate_production", chain_not_mutated))
        if not chain_not_mutated:
            reason_codes.append("read_only_adapter_chain_mutated_production")

        for flag in [
            "allow_production_mutation",
            "allow_queue_action_update",
            "allow_packet_update",
            "allow_tailoring_generation_update",
            "allow_scoring_update",
            "allow_ranking_update",
            "allow_application_submission",
            "allow_live_pipeline_wiring",
        ]:
            flag_disabled = not bool(read_only_chain_json.get(flag))
            checks.append(_check(f"read_only_adapter_chain_{flag}_false", flag_disabled))
            if not flag_disabled:
                reason_codes.append(f"read_only_adapter_chain_{flag}_true")

        chain_order = list(read_only_chain_json.get("adapter_execution_order") or [])
        chain_order_ok = chain_order == read_only_adapter_chain.ADAPTER_EXECUTION_ORDER
        checks.append(
            _check(
                "read_only_adapter_chain_order_matches_expected",
                chain_order_ok,
                f"expected {read_only_adapter_chain.ADAPTER_EXECUTION_ORDER}, found {chain_order}"
                if not chain_order_ok else "",
            )
        )
        if not chain_order_ok:
            reason_codes.append("read_only_adapter_chain_order_mismatch")

    if "read_only_chain_artifact_generation_result.json" in present_artifacts:
        generation_validation = (
            read_only_chain_artifact_generator.validate_chain_artifact_generation_result(
                read_only_chain_generation_json
            )
        )
        generation_validation_status = _clean_text(generation_validation.get("validation_status"))
        generation_validation_passed = generation_validation_status in {"passed", "warning"}
        checks.append(
            _check(
                "read_only_chain_artifact_generation_validation_passed_or_warning",
                generation_validation_passed,
                ", ".join(generation_validation.get("reason_codes", []) or [])
                if not generation_validation_passed else "",
            )
        )
        if not generation_validation_passed:
            reason_codes.append("read_only_chain_artifact_generation_validation_failed")
        if generation_validation_status == "warning":
            reason_codes.append("read_only_chain_artifact_generation_warning")

        generation_mode = (
            _clean_text(read_only_chain_generation_json.get("execution_mode"))
            == read_only_chain_artifact_generator.EXECUTION_MODE
        )
        checks.append(_check("read_only_chain_artifact_generation_explicit_operator_mode", generation_mode))
        if not generation_mode:
            reason_codes.append("read_only_chain_artifact_generation_wrong_mode")

        generation_not_mutated = not bool(read_only_chain_generation_json.get("did_mutate_production"))
        checks.append(_check("read_only_chain_artifact_generation_did_not_mutate_production", generation_not_mutated))
        if not generation_not_mutated:
            reason_codes.append("read_only_chain_artifact_generation_mutated_production")

        generation_context = dict(read_only_chain_generation_json.get("context") or {})
        for required_flag in ["require_explicit_input", "require_explicit_output_dir"]:
            flag_enabled = bool(
                read_only_chain_generation_json.get(required_flag)
                if required_flag in read_only_chain_generation_json
                else generation_context.get(required_flag)
            )
            checks.append(_check(f"read_only_chain_artifact_generation_{required_flag}_true", flag_enabled))
            if not flag_enabled:
                reason_codes.append(f"read_only_chain_artifact_generation_{required_flag}_false")

        for flag in [
            "allow_production_mutation",
            "allow_live_pipeline_wiring",
            "allow_application_submission",
            "allow_queue_action_update",
            "allow_packet_update",
            "allow_tailoring_generation_update",
            "allow_scoring_update",
            "allow_ranking_update",
        ]:
            flag_disabled = not bool(read_only_chain_generation_json.get(flag))
            checks.append(_check(f"read_only_chain_artifact_generation_{flag}_false", flag_disabled))
            if not flag_disabled:
                reason_codes.append(f"read_only_chain_artifact_generation_{flag}_true")

        generation_root_names = set(
            generation_validation.get("output_root_file_names") or []
        )
        production_root_names = sorted(
            generation_root_names.intersection(
                read_only_chain_artifact_generator.PRODUCTION_ROOT_ARTIFACT_NAMES
            )
        )
        root_names_safe = not production_root_names
        checks.append(
            _check(
                "read_only_chain_artifact_generation_no_production_root_artifact_names",
                root_names_safe,
                ", ".join(production_root_names) if production_root_names else "",
            )
        )
        if not root_names_safe:
            reason_codes.append("read_only_chain_artifact_generation_production_root_artifact_names")

    if "dry_run_execution_simulation_result.json" in present_artifacts:
        simulation_validation = (
            dry_run_execution_simulator.validate_dry_run_execution_simulation_result(
                dry_run_simulation_json
            )
        )
        simulation_validation_status = _clean_text(simulation_validation.get("validation_status"))
        simulation_validation_passed = simulation_validation_status in {"passed", "warning"}
        checks.append(
            _check(
                "dry_run_execution_simulation_validation_passed_or_warning",
                simulation_validation_passed,
                ", ".join(simulation_validation.get("reason_codes", []) or [])
                if not simulation_validation_passed else "",
            )
        )
        if not simulation_validation_passed:
            reason_codes.append("dry_run_execution_simulation_validation_failed")
        if simulation_validation_status == "warning":
            reason_codes.append("dry_run_execution_simulation_warning")

        simulation_mode = (
            _clean_text(dry_run_simulation_json.get("execution_mode"))
            == dry_run_execution_simulator.EXECUTION_MODE
        )
        checks.append(_check("dry_run_execution_simulation_explicit_mode", simulation_mode))
        if not simulation_mode:
            reason_codes.append("dry_run_execution_simulation_wrong_mode")

        did_simulate_boolean = isinstance(dry_run_simulation_json.get("did_simulate"), bool)
        checks.append(_check("dry_run_execution_simulation_did_simulate_boolean", did_simulate_boolean))
        if not did_simulate_boolean:
            reason_codes.append("dry_run_execution_simulation_did_simulate_not_boolean")

        for flag in ["did_execute_live", "did_mutate_production"]:
            flag_disabled = not bool(dry_run_simulation_json.get(flag))
            checks.append(_check(f"dry_run_execution_simulation_{flag}_false", flag_disabled))
            if not flag_disabled:
                reason_codes.append(f"dry_run_execution_simulation_{flag}_true")

        safety_flags = dict(dry_run_simulation_json.get("safety_flags") or {})
        context = dict(dry_run_simulation_json.get("context") or {})
        for flag in [
            "allow_db_write",
            "allow_live_pipeline_wiring",
            "allow_application_submission",
            "allow_queue_action_update",
            "allow_packet_update",
            "allow_tailoring_generation_update",
            "allow_scoring_update",
            "allow_ranking_update",
            "allow_scheduler_execution",
        ]:
            value = (
                safety_flags.get(flag)
                if flag in safety_flags
                else context.get(flag, dry_run_simulation_json.get(flag))
            )
            flag_disabled = not bool(value)
            checks.append(_check(f"dry_run_execution_simulation_{flag}_false", flag_disabled))
            if not flag_disabled:
                reason_codes.append(f"dry_run_execution_simulation_{flag}_true")

        simulation_plan = dict(dry_run_simulation_json.get("simulated_execution_plan") or {})
        can_execute_live_false = not bool(simulation_plan.get("can_execute_live"))
        checks.append(_check("dry_run_execution_simulation_can_execute_live_false", can_execute_live_false))
        if not can_execute_live_false:
            reason_codes.append("dry_run_execution_simulation_can_execute_live_true")

        allowed_types = set(dry_run_execution_simulator.SIMULATED_MUTATION_TYPES)
        proposals_safe = True
        bad_proposal_reasons: List[str] = []
        for proposal in list(dry_run_simulation_json.get("simulated_mutation_proposals") or []):
            proposal_mode = _clean_text(dict(proposal).get("proposal_mode"))
            mutation_type = _clean_text(dict(proposal).get("mutation_type"))
            if proposal_mode != "simulated_non_executable":
                proposals_safe = False
                bad_proposal_reasons.append("proposal_mode")
            if bool(dict(proposal).get("can_execute_live")):
                proposals_safe = False
                bad_proposal_reasons.append("can_execute_live")
            if not bool(dict(proposal).get("blocked_by_default")):
                proposals_safe = False
                bad_proposal_reasons.append("blocked_by_default")
            if mutation_type not in allowed_types:
                proposals_safe = False
                bad_proposal_reasons.append("mutation_type")
        checks.append(
            _check(
                "dry_run_execution_simulation_proposals_non_executable",
                proposals_safe,
                ", ".join(sorted(set(bad_proposal_reasons))) if bad_proposal_reasons else "",
            )
        )
        if not proposals_safe:
            reason_codes.append("dry_run_execution_simulation_unsafe_proposal")

        simulation_root_names = set(simulation_validation.get("output_root_file_names") or [])
        production_root_names = sorted(
            simulation_root_names.intersection(
                dry_run_execution_simulator.PRODUCTION_ROOT_ARTIFACT_NAMES
            )
        )
        root_names_safe = not production_root_names
        checks.append(
            _check(
                "dry_run_execution_simulation_no_production_root_artifact_names",
                root_names_safe,
                ", ".join(production_root_names) if production_root_names else "",
            )
        )
        if not root_names_safe:
            reason_codes.append("dry_run_execution_simulation_production_root_artifact_names")

    if "proposal_only_mutation_plan_result.json" in present_artifacts:
        proposal_validation = (
            proposal_only_mutation_planner.validate_proposal_only_mutation_plan_result(
                proposal_plan_json
            )
        )
        proposal_validation_status = _clean_text(proposal_validation.get("validation_status"))
        proposal_validation_passed = proposal_validation_status in {"passed", "warning"}
        checks.append(
            _check(
                "proposal_only_mutation_plan_validation_passed_or_warning",
                proposal_validation_passed,
                ", ".join(proposal_validation.get("reason_codes", []) or [])
                if not proposal_validation_passed else "",
            )
        )
        if not proposal_validation_passed:
            reason_codes.append("proposal_only_mutation_plan_validation_failed")
        if proposal_validation_status == "warning":
            reason_codes.append("proposal_only_mutation_plan_warning")

        proposal_mode = (
            _clean_text(proposal_plan_json.get("execution_mode"))
            == proposal_only_mutation_planner.EXECUTION_MODE
        )
        checks.append(_check("proposal_only_mutation_plan_explicit_mode", proposal_mode))
        if not proposal_mode:
            reason_codes.append("proposal_only_mutation_plan_wrong_mode")

        did_plan_boolean = isinstance(proposal_plan_json.get("did_plan"), bool)
        checks.append(_check("proposal_only_mutation_plan_did_plan_boolean", did_plan_boolean))
        if not did_plan_boolean:
            reason_codes.append("proposal_only_mutation_plan_did_plan_not_boolean")

        for flag in ["did_execute_live", "did_mutate_production", "did_approve", "did_store_approval", "did_write_db"]:
            flag_disabled = not bool(proposal_plan_json.get(flag))
            checks.append(_check(f"proposal_only_mutation_plan_{flag}_false", flag_disabled))
            if not flag_disabled:
                reason_codes.append(f"proposal_only_mutation_plan_{flag}_true")

        safety_flags = dict(proposal_plan_json.get("safety_flags") or {})
        context = dict(proposal_plan_json.get("context") or {})
        for flag in [
            "allow_db_write",
            "allow_live_pipeline_wiring",
            "allow_application_submission",
            "allow_queue_action_update",
            "allow_packet_update",
            "allow_tailoring_generation_update",
            "allow_scoring_update",
            "allow_ranking_update",
            "allow_scheduler_execution",
            "allow_approval_action",
            "allow_mutation_execution",
        ]:
            value = (
                safety_flags.get(flag)
                if flag in safety_flags
                else context.get(flag, proposal_plan_json.get(flag))
            )
            flag_disabled = not bool(value)
            checks.append(_check(f"proposal_only_mutation_plan_{flag}_false", flag_disabled))
            if not flag_disabled:
                reason_codes.append(f"proposal_only_mutation_plan_{flag}_true")

        proposal_plan = dict(proposal_plan_json.get("proposal_plan") or {})
        plan_mode_ok = _clean_text(proposal_plan.get("plan_mode")) == "proposal_only_non_executable"
        checks.append(_check("proposal_only_mutation_plan_non_executable_mode", plan_mode_ok))
        if not plan_mode_ok:
            reason_codes.append("proposal_only_mutation_plan_wrong_plan_mode")
        for flag in ["can_execute_live", "can_mutate", "can_approve"]:
            flag_disabled = not bool(proposal_plan.get(flag))
            checks.append(_check(f"proposal_only_mutation_plan_{flag}_false", flag_disabled))
            if not flag_disabled:
                reason_codes.append(f"proposal_only_mutation_plan_{flag}_true")

        allowed_types = set(proposal_only_mutation_planner.ALLOWED_MUTATION_TYPES)
        proposals_safe = True
        bad_proposal_reasons: List[str] = []
        for proposal in list(proposal_plan_json.get("proposal_only_mutation_items") or []):
            proposal_payload = dict(proposal)
            mutation_type = _clean_text(proposal_payload.get("mutation_type"))
            if _clean_text(proposal_payload.get("proposal_mode")) != "proposal_only_non_executable":
                proposals_safe = False
                bad_proposal_reasons.append("proposal_mode")
            for flag in ["can_execute_live", "can_mutate", "can_approve"]:
                if bool(proposal_payload.get(flag)):
                    proposals_safe = False
                    bad_proposal_reasons.append(flag)
            if not bool(proposal_payload.get("blocked_by_default")):
                proposals_safe = False
                bad_proposal_reasons.append("blocked_by_default")
            if mutation_type not in allowed_types:
                proposals_safe = False
                bad_proposal_reasons.append("mutation_type")
        checks.append(
            _check(
                "proposal_only_mutation_plan_items_non_executable",
                proposals_safe,
                ", ".join(sorted(set(bad_proposal_reasons))) if bad_proposal_reasons else "",
            )
        )
        if not proposals_safe:
            reason_codes.append("proposal_only_mutation_plan_unsafe_item")

        proposal_root_names = set(proposal_validation.get("output_root_file_names") or [])
        production_root_names = sorted(
            proposal_root_names.intersection(
                proposal_only_mutation_planner.PRODUCTION_ROOT_ARTIFACT_NAMES
            )
        )
        record_root_names = sorted(
            proposal_root_names.intersection(
                {"approval_record.json", "mutation_record.json", "audit_ledger_entry.json"}
            )
        )
        checks.append(
            _check(
                "proposal_only_mutation_plan_no_production_root_artifact_names",
                not production_root_names,
                ", ".join(production_root_names) if production_root_names else "",
            )
        )
        if production_root_names:
            reason_codes.append("proposal_only_mutation_plan_production_root_artifact_names")
        checks.append(
            _check(
                "proposal_only_mutation_plan_no_approval_audit_mutation_records",
                not record_root_names,
                ", ".join(record_root_names) if record_root_names else "",
            )
        )
        if record_root_names:
            reason_codes.append("proposal_only_mutation_plan_record_artifact_names")

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
    diagnostic_warning = (
        "rag_evaluation_warning" in reason_codes
        or "read_only_adapter_preflight_warning" in reason_codes
        or "read_only_adapter_chain_warning" in reason_codes
        or "read_only_chain_artifact_generation_warning" in reason_codes
        or "dry_run_execution_simulation_warning" in reason_codes
        or "proposal_only_mutation_plan_warning" in reason_codes
    )
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
            "read_only_adapter_preflight_results": len(list(read_only_preflight_json.get("adapter_preflight_results") or [])),
            "read_only_adapter_chain_adapters": len(list(read_only_chain_json.get("adapter_execution_order") or [])),
            "read_only_chain_artifact_generation_did_run_chain": 1 if bool(read_only_chain_generation_json.get("did_run_chain")) else 0,
            "dry_run_execution_simulation_proposals": len(list(dry_run_simulation_json.get("simulated_mutation_proposals") or [])),
            "proposal_only_mutation_plan_items": len(list(proposal_plan_json.get("proposal_only_mutation_items") or [])),
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
