from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

from src.agents import orchestrator_adapter_harness, workflow_planner


RUNNER_VERSION = "agentic_workflow_runner_v1"
EXECUTION_MODE = "dry_run"
DRY_RUN_RESULT_JSON_NAME = "agentic_workflow_dry_run_result.json"
DRY_RUN_REPORT_MD_NAME = "agentic_workflow_dry_run_report.md"
FIXTURE_VALIDATION_GATE_ENABLED = True


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _truthy(value: Any) -> bool:
    return _clean_text(value).lower() in {"1", "true", "yes", "y", "on"}


def _feature_flags_snapshot(
    feature_flags: Iterable[str],
    env: Dict[str, str] | None = None,
) -> Dict[str, bool]:
    env_map = env if env is not None else os.environ
    return {
        _clean_text(flag): _truthy(env_map.get(_clean_text(flag)))
        for flag in feature_flags
        if _clean_text(flag)
    }


def _fixture_validation_gate_result(
    preflight_plan: Dict[str, Any] | None,
) -> Dict[str, Any]:
    plan = dict(preflight_plan or {})
    fixture_validation = plan.get("fixture_validation")
    reason_codes: List[str] = []

    if not isinstance(fixture_validation, dict):
        fixture_validation = {}
        reason_codes.append("missing_fixture_validation_summary")

    if fixture_validation.get("fixture_validation_passed") is not True:
        reason_codes.append("fixture_validation_not_passed")
    if _clean_text(fixture_validation.get("fixture_validation_status")) != "passed":
        reason_codes.append("fixture_validation_status_not_passed")
    if int(fixture_validation.get("fixture_validation_checked_count") or 0) != 3:
        reason_codes.append("fixture_validation_checked_count_mismatch")
    if int(fixture_validation.get("fixture_validation_expected_fixture_count") or 0) != 3:
        reason_codes.append("fixture_validation_expected_count_mismatch")
    if list(fixture_validation.get("fixture_validation_failed_fixture_ids") or []):
        reason_codes.append("fixture_validation_failed_fixture_ids_non_empty")
    if list(fixture_validation.get("fixture_validation_unexpected_fixture_filenames") or []):
        reason_codes.append("unexpected_fixture_file")

    results = fixture_validation.get("fixture_validation_results")
    results = list(results or []) if isinstance(results, list) else []
    results_by_filename = {
        _clean_text(result.get("fixture_filename")): result
        for result in results
        if isinstance(result, dict) and _clean_text(result.get("fixture_filename"))
    }
    approved_filenames = set(orchestrator_adapter_harness.APPROVED_FIXTURE_FILENAMES)
    missing_approved_filenames = sorted(approved_filenames.difference(results_by_filename))
    if missing_approved_filenames:
        reason_codes.append("approved_fixture_missing_from_results")

    for filename in sorted(approved_filenames.intersection(results_by_filename)):
        result = dict(results_by_filename[filename])
        if result.get("expected_matches_actual") is not True:
            reason_codes.append(f"{filename}:fixture_expected_mismatch")
        if result.get("did_execute_fixture") is not False:
            reason_codes.append(f"{filename}:did_execute_fixture")
        if result.get("did_mutate_production") is not False:
            reason_codes.append(f"{filename}:did_mutate_production")
        if result.get("did_write_db") is not False:
            reason_codes.append(f"{filename}:did_write_db")

    executable_adapter_count = int(plan.get("executable_adapter_count") or 0)
    allow_agent_execution = bool(plan.get("allow_agent_execution"))
    did_execute_count = int(dict(plan.get("summary") or {}).get("did_execute_count") or 0)
    did_execute_live = bool(plan.get("did_execute_live"))
    did_mutate_production = bool(plan.get("did_mutate_production"))
    did_write_db = bool(plan.get("did_write_db"))

    if executable_adapter_count > 0:
        reason_codes.append("executable_adapter_count_nonzero")
    if allow_agent_execution:
        reason_codes.append("allow_agent_execution_true")
    if did_execute_count != 0:
        reason_codes.append("did_execute_count_nonzero")
    if did_execute_live:
        reason_codes.append("did_execute_live_true")
    if did_mutate_production:
        reason_codes.append("did_mutate_production_true")
    if did_write_db:
        reason_codes.append("did_write_db_true")

    reason_codes = sorted(set(reason_codes))
    return {
        "fixture_validation_gate_enabled": FIXTURE_VALIDATION_GATE_ENABLED,
        "fixture_validation_gate_status": "failed" if reason_codes else "passed",
        "fixture_validation_gate_passed": not reason_codes,
        "fixture_validation_gate_reason_codes": reason_codes,
        "fixture_validation": fixture_validation,
        "blocked_by_fixture_validation_gate": bool(reason_codes),
        "executable_adapter_count": executable_adapter_count,
        "allow_agent_execution": allow_agent_execution,
        "did_execute_count": did_execute_count,
        "did_execute_live": did_execute_live,
        "did_mutate_production": did_mutate_production,
        "did_write_db": did_write_db,
    }


def build_agentic_workflow_run_context(
    *,
    pipeline_run_id: str = "",
    owner_user_id: str = "",
    input_artifacts_present: Iterable[str] | None = None,
    feature_flags_snapshot: Dict[str, Any] | None = None,
    plan: Dict[str, Any] | None = None,
    env: Dict[str, str] | None = None,
    created_at_utc: str = "",
) -> Dict[str, Any]:
    execution_plan = deepcopy(plan) if plan is not None else workflow_planner.build_agentic_workflow_execution_plan()
    present = sorted({_clean_text(item) for item in list(input_artifacts_present or []) if _clean_text(item)})
    expected_inputs = sorted(
        {_clean_text(item) for item in list(execution_plan.get("expected_input_artifacts") or []) if _clean_text(item)}
    )
    missing = [artifact for artifact in expected_inputs if artifact not in present]
    flags = (
        dict(feature_flags_snapshot)
        if feature_flags_snapshot is not None
        else _feature_flags_snapshot(execution_plan.get("feature_flags") or [], env=env)
    )
    return {
        "pipeline_run_id": _clean_text(pipeline_run_id),
        "owner_user_id": _clean_text(owner_user_id),
        "workflow_name": _clean_text(execution_plan.get("workflow_name")),
        "workflow_version": _clean_text(execution_plan.get("workflow_version")),
        "execution_mode": EXECUTION_MODE,
        "input_artifacts_present": present,
        "input_artifacts_missing": missing,
        "feature_flags_snapshot": flags,
        "created_at_utc": _clean_text(created_at_utc) or _utc_now_iso(),
    }


def _step_would_trace(step: Dict[str, Any], context: Dict[str, Any]) -> bool:
    flags = dict(context.get("feature_flags_snapshot") or {})
    return bool(flags.get("APPLYLENS_AGENT_TRACE_ENABLED")) and bool(_clean_text(step.get("trace_step_name")))


def _build_step_result(step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    reason_codes = ["dry_run_only", "agent_execution_disabled"]
    if step.get("mutates_production_decisions"):
        reason_codes.append("production_mutation_blocked")
    return {
        "step_index": int(step.get("step_index") or 0),
        "agent_key": _clean_text(step.get("agent_key")),
        "agent_name": _clean_text(step.get("agent_name")),
        "execution_status": "skipped_dry_run",
        "execution_enabled": False,
        "would_read_artifacts": list(step.get("input_artifacts") or []),
        "would_write_artifacts": list(step.get("output_artifacts") or []),
        "would_trace": _step_would_trace(step, context),
        "reason_codes": reason_codes,
        "did_execute": False,
        "mutates_production_decisions": bool(step.get("mutates_production_decisions")),
    }


def run_agentic_workflow_dry_run(
    *,
    pipeline_run_id: str = "",
    owner_user_id: str = "",
    input_artifacts_present: Iterable[str] | None = None,
    plan: Dict[str, Any] | None = None,
    preflight_plan: Dict[str, Any] | None = None,
    context: Dict[str, Any] | None = None,
    env: Dict[str, str] | None = None,
) -> Dict[str, Any]:
    execution_plan = deepcopy(plan) if plan is not None else workflow_planner.build_agentic_workflow_execution_plan()
    preflight_payload = (
        deepcopy(preflight_plan)
        if preflight_plan is not None
        else orchestrator_adapter_harness.build_read_only_adapter_preflight_plan(
            pipeline_run_id=pipeline_run_id,
            owner_user_id=owner_user_id,
            execution_plan=execution_plan,
        )
    )
    gate = _fixture_validation_gate_result(preflight_payload)
    run_context = (
        dict(context)
        if context is not None
        else build_agentic_workflow_run_context(
            pipeline_run_id=pipeline_run_id,
            owner_user_id=owner_user_id,
            input_artifacts_present=input_artifacts_present,
            plan=execution_plan,
            env=env,
        )
    )
    step_results = [
        _build_step_result(step, run_context)
        for step in list(execution_plan.get("ordered_steps") or [])
    ]
    result = {
        "runner_version": RUNNER_VERSION,
        "execution_mode": EXECUTION_MODE,
        "workflow_name": _clean_text(execution_plan.get("workflow_name")),
        "workflow_version": _clean_text(execution_plan.get("workflow_version")),
        "pipeline_run_id": _clean_text(run_context.get("pipeline_run_id")),
        "owner_user_id": _clean_text(run_context.get("owner_user_id")),
        "planned_step_count": len(step_results),
        "executed_step_count": 0,
        "skipped_step_count": len(step_results),
        "ordered_step_results": step_results,
        "context": run_context,
        **gate,
    }
    result["validation"] = validate_agentic_workflow_dry_run_result(result, plan=execution_plan)
    result["summary"] = {
        "did_execute_any_step": any(step.get("did_execute") for step in step_results),
        "would_trace_step_count": sum(1 for step in step_results if step.get("would_trace")),
        "missing_input_artifact_count": len(list(run_context.get("input_artifacts_missing") or [])),
        "status_counts": dict(sorted(Counter(step.get("execution_status", "") for step in step_results).items())),
        "did_execute_count": gate["did_execute_count"],
        "blocked_by_fixture_validation_gate": gate["blocked_by_fixture_validation_gate"],
    }
    return result


def validate_agentic_workflow_dry_run_result(
    result: Dict[str, Any],
    *,
    plan: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    execution_plan = deepcopy(plan) if plan is not None else workflow_planner.build_agentic_workflow_execution_plan()
    expected_order = [
        _clean_text(step.get("agent_key"))
        for step in list(execution_plan.get("ordered_steps") or [])
    ]
    steps = list(result.get("ordered_step_results") or [])
    actual_order = [_clean_text(step.get("agent_key")) for step in steps]
    reason_codes: List[str] = []

    if _clean_text(result.get("execution_mode")) != EXECUTION_MODE:
        reason_codes.append("execution_mode_not_dry_run")
    if int(result.get("executed_step_count") or 0) != 0:
        reason_codes.append("executed_step_count_nonzero")
    if result.get("fixture_validation_gate_passed") is False:
        reason_codes.append("fixture_validation_gate_failed")
    if actual_order != expected_order:
        reason_codes.append("step_order_mismatch")

    for step in steps:
        agent_key = _clean_text(step.get("agent_key")) or "<unknown>"
        if step.get("did_execute"):
            reason_codes.append(f"{agent_key}:did_execute")
        if step.get("execution_enabled"):
            reason_codes.append(f"{agent_key}:execution_enabled")
        if _clean_text(step.get("execution_status")) != "skipped_dry_run":
            reason_codes.append(f"{agent_key}:execution_status_not_skipped_dry_run")
        if step.get("mutates_production_decisions"):
            reason_codes.append(f"{agent_key}:mutates_production_decisions")

    return {
        "validation_status": "failed" if reason_codes else "passed",
        "reason_codes": sorted(set(reason_codes)),
        "expected_order": expected_order,
        "actual_order": actual_order,
        "executed_step_count": int(result.get("executed_step_count") or 0),
        "step_count": len(steps),
    }


def render_agentic_workflow_dry_run_report_markdown(
    result: Dict[str, Any] | None = None,
) -> str:
    payload = deepcopy(result) if result is not None else run_agentic_workflow_dry_run()
    validation = dict(payload.get("validation") or validate_agentic_workflow_dry_run_result(payload))
    lines = [
        "# Agentic Workflow Dry-Run Report",
        "",
        f"Workflow: `{payload.get('workflow_name', '')}`",
        f"Workflow version: `{payload.get('workflow_version', '')}`",
        f"Runner version: `{payload.get('runner_version', '')}`",
        f"Execution mode: `{payload.get('execution_mode', '')}`",
        f"Executed step count: `{payload.get('executed_step_count', 0)}`",
        f"Fixture validation gate: `{payload.get('fixture_validation_gate_status', '')}`",
        f"Validation: `{validation.get('validation_status', '')}`",
        "",
        "## Step Results",
        "",
    ]
    for step in list(payload.get("ordered_step_results") or []):
        lines.extend(
            [
                f"### {step.get('step_index')}. {step.get('agent_name', '')}",
                "",
                f"- Agent key: `{step.get('agent_key', '')}`",
                f"- Status: `{step.get('execution_status', '')}`",
                f"- Execution enabled: `{bool(step.get('execution_enabled'))}`",
                f"- Did execute: `{bool(step.get('did_execute'))}`",
                f"- Would trace: `{bool(step.get('would_trace'))}`",
                f"- Would read: {', '.join(f'`{item}`' for item in step.get('would_read_artifacts', []) or []) or 'none'}",
                f"- Would write: {', '.join(f'`{item}`' for item in step.get('would_write_artifacts', []) or []) or 'none'}",
                f"- Reasons: {', '.join(f'`{item}`' for item in step.get('reason_codes', []) or []) or 'none'}",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def write_agentic_workflow_dry_run_artifacts(
    *,
    output_dir: str | Path,
    result_json_path: str | Path | None = None,
    report_md_path: str | Path | None = None,
    result: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    root = Path(output_dir)
    json_path = Path(result_json_path) if result_json_path else root / DRY_RUN_RESULT_JSON_NAME
    md_path = Path(report_md_path) if report_md_path else root / DRY_RUN_REPORT_MD_NAME
    payload = deepcopy(result) if result is not None else run_agentic_workflow_dry_run()
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(render_agentic_workflow_dry_run_report_markdown(payload), encoding="utf-8")
    return {
        "json_path": str(json_path),
        "md_path": str(md_path),
        "payload": payload,
        "validation_status": payload.get("validation", {}).get("validation_status", ""),
    }


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a dry-run agentic workflow runner result.")
    parser.add_argument("--dry-run", action="store_true", help="Generate a dry-run result without executing agents.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--pipeline-run-id", default="", help="Optional pipeline run id for the dry-run context.")
    parser.add_argument("--owner-user-id", default="", help="Optional owner user id for the dry-run context.")
    args = parser.parse_args(argv)

    if not args.dry_run:
        parser.error("Only --dry-run mode is supported.")

    payload = run_agentic_workflow_dry_run(
        pipeline_run_id=args.pipeline_run_id,
        owner_user_id=args.owner_user_id,
    )
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        validation = dict(payload.get("validation") or {})
        print(f"Agentic workflow dry-run: {validation.get('validation_status', '')}")
        print(f"Planned steps: {payload.get('planned_step_count', 0)}")
        print(f"Executed steps: {payload.get('executed_step_count', 0)}")
    return 0 if payload.get("validation", {}).get("validation_status") == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
