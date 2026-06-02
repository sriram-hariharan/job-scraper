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

from src.agents import workflow_planner


RUNNER_VERSION = "agentic_workflow_runner_v1"
EXECUTION_MODE = "dry_run"
DRY_RUN_RESULT_JSON_NAME = "agentic_workflow_dry_run_result.json"
DRY_RUN_REPORT_MD_NAME = "agentic_workflow_dry_run_report.md"


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
    context: Dict[str, Any] | None = None,
    env: Dict[str, str] | None = None,
) -> Dict[str, Any]:
    execution_plan = deepcopy(plan) if plan is not None else workflow_planner.build_agentic_workflow_execution_plan()
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
    }
    result["validation"] = validate_agentic_workflow_dry_run_result(result, plan=execution_plan)
    result["summary"] = {
        "did_execute_any_step": any(step.get("did_execute") for step in step_results),
        "would_trace_step_count": sum(1 for step in step_results if step.get("would_trace")),
        "missing_input_artifact_count": len(list(run_context.get("input_artifacts_missing") or [])),
        "status_counts": dict(sorted(Counter(step.get("execution_status", "") for step in step_results).items())),
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
