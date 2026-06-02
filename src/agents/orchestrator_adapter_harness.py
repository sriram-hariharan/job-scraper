from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from src.agents import orchestrator_adapters, workflow_planner, workflow_registry


HARNESS_VERSION = "read_only_adapter_harness_v1"
EXECUTION_MODE = "read_only_preflight"
PREFLIGHT_JSON_NAME = "read_only_adapter_preflight.json"
PREFLIGHT_MD_NAME = "read_only_adapter_preflight.md"


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _adapter_specs_by_key(contract: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    specs = contract.get("adapter_specs") if isinstance(contract, dict) else {}
    return dict(specs) if isinstance(specs, dict) else {}


def _artifact_presence(artifact_root: str | Path | None, artifact_names: List[str]) -> Dict[str, Dict[str, Any]]:
    root_text = _clean_text(artifact_root)
    if not root_text:
        return {}
    root = Path(root_text)
    return {
        artifact: {
            "path": str(root / artifact),
            "exists": (root / artifact).exists(),
        }
        for artifact in artifact_names
        if _clean_text(artifact)
    }


def build_read_only_adapter_harness_context(
    *,
    pipeline_run_id: str = "",
    owner_user_id: str = "",
    artifact_root: str | Path | None = None,
    created_at_utc: str = "",
    manifest: Dict[str, Any] | None = None,
    contract: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    workflow_manifest = deepcopy(manifest) if manifest is not None else workflow_registry.get_agentic_workflow_manifest()
    adapter_contract = deepcopy(contract) if contract is not None else orchestrator_adapters.get_orchestrator_adapter_contract()
    return {
        "harness_version": HARNESS_VERSION,
        "execution_mode": EXECUTION_MODE,
        "pipeline_run_id": _clean_text(pipeline_run_id),
        "owner_user_id": _clean_text(owner_user_id),
        "artifact_root": _clean_text(artifact_root),
        "created_at_utc": _clean_text(created_at_utc) or _utc_now_iso(),
        "workflow_name": _clean_text(workflow_manifest.get("workflow_name")),
        "workflow_version": _clean_text(workflow_manifest.get("workflow_version")),
        "adapter_contract_version": _clean_text(adapter_contract.get("contract_version")),
        "allow_agent_execution": False,
    }


def _preflight_status(spec: Dict[str, Any]) -> str:
    adapter_status = _clean_text(spec.get("adapter_status"))
    allowed_mode = _clean_text(spec.get("allowed_execution_mode"))
    if (
        adapter_status == "blocked"
        or bool(spec.get("mutates_production_decisions"))
        or bool(spec.get("llm_call_expected"))
        or allowed_mode in orchestrator_adapters.LIVE_EXECUTION_MODES
    ):
        return "blocked"
    if adapter_status == "ready_for_read_only_adapter":
        return "ready_read_only_contract"
    return "needs_adapter"


def _reason_codes_for_result(spec: Dict[str, Any], presence: Dict[str, Dict[str, Any]]) -> List[str]:
    reason_codes = [
        _clean_text(item)
        for item in list(spec.get("reason_codes") or [])
        if _clean_text(item)
    ]
    reason_codes.extend(["read_only_preflight", "agent_execution_disabled"])
    if presence and any(not bool(item.get("exists")) for item in presence.values()):
        reason_codes.append("missing_required_artifacts")
    return sorted(set(reason_codes))


def _build_preflight_result(
    *,
    step: Dict[str, Any],
    spec: Dict[str, Any],
    artifact_root: str | Path | None = None,
) -> Dict[str, Any]:
    required_artifacts = list(spec.get("required_artifacts") or [])
    presence = _artifact_presence(artifact_root, required_artifacts)
    result = {
        "step_index": int(step.get("step_index") or 0),
        "agent_key": _clean_text(step.get("agent_key")),
        "agent_name": _clean_text(step.get("agent_name")),
        "owner_module": _clean_text(spec.get("owner_module") or step.get("owner_module")),
        "adapter_status": _clean_text(spec.get("adapter_status")),
        "allowed_execution_mode": _clean_text(spec.get("allowed_execution_mode")),
        "would_call_entrypoints": [
            _clean_text(item)
            for item in list(spec.get("callable_entrypoint_names") or [])
            if _clean_text(item)
        ],
        "required_artifacts": required_artifacts,
        "produced_artifacts": list(spec.get("produced_artifacts") or []),
        "input_loader_required": bool(spec.get("input_loader_required")),
        "output_validator_required": bool(spec.get("output_validator_required")),
        "artifact_writer_available": bool(spec.get("artifact_writer_available")),
        "trace_supported": bool(spec.get("trace_supported")),
        "db_access_required": bool(spec.get("db_access_required")),
        "env_context_required": bool(spec.get("env_context_required")),
        "llm_call_expected": bool(spec.get("llm_call_expected")),
        "mutates_production_decisions": bool(spec.get("mutates_production_decisions")),
        "preflight_status": _preflight_status(spec),
        "execution_enabled": False,
        "did_execute": False,
    }
    if presence:
        result["artifact_presence"] = presence
    result["reason_codes"] = _reason_codes_for_result(spec, presence)
    return result


def build_read_only_adapter_preflight_plan(
    *,
    pipeline_run_id: str = "",
    owner_user_id: str = "",
    artifact_root: str | Path | None = None,
    created_at_utc: str = "",
    manifest: Dict[str, Any] | None = None,
    contract: Dict[str, Any] | None = None,
    execution_plan: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    workflow_manifest = deepcopy(manifest) if manifest is not None else workflow_registry.get_agentic_workflow_manifest()
    adapter_contract = deepcopy(contract) if contract is not None else orchestrator_adapters.get_orchestrator_adapter_contract()
    planner_payload = (
        deepcopy(execution_plan)
        if execution_plan is not None
        else workflow_planner.build_agentic_workflow_execution_plan(workflow_manifest)
    )
    specs_by_key = _adapter_specs_by_key(adapter_contract)
    context = build_read_only_adapter_harness_context(
        pipeline_run_id=pipeline_run_id,
        owner_user_id=owner_user_id,
        artifact_root=artifact_root,
        created_at_utc=created_at_utc,
        manifest=workflow_manifest,
        contract=adapter_contract,
    )
    results = [
        _build_preflight_result(
            step=step,
            spec=specs_by_key.get(_clean_text(step.get("agent_key")), {}),
            artifact_root=artifact_root,
        )
        for step in list(planner_payload.get("ordered_steps") or [])
    ]
    status_counts = Counter(result.get("preflight_status", "") for result in results)
    missing_required_artifact_count = sum(
        1
        for result in results
        for artifact in dict(result.get("artifact_presence") or {}).values()
        if not bool(artifact.get("exists"))
    )
    plan = {
        "harness_version": HARNESS_VERSION,
        "execution_mode": EXECUTION_MODE,
        "workflow_name": _clean_text(workflow_manifest.get("workflow_name")),
        "workflow_version": _clean_text(workflow_manifest.get("workflow_version")),
        "pipeline_run_id": _clean_text(pipeline_run_id),
        "owner_user_id": _clean_text(owner_user_id),
        "allow_agent_execution": False,
        "planned_adapter_count": len(results),
        "executable_adapter_count": 0,
        "adapter_preflight_results": results,
        "context": context,
        "summary": {
            "status_counts": dict(sorted(status_counts.items())),
            "ready_read_only_contract_count": int(status_counts.get("ready_read_only_contract", 0)),
            "needs_adapter_count": int(status_counts.get("needs_adapter", 0)),
            "blocked_count": int(status_counts.get("blocked", 0)),
            "execution_enabled_count": sum(1 for result in results if result.get("execution_enabled")),
            "did_execute_count": sum(1 for result in results if result.get("did_execute")),
            "missing_required_artifact_count": missing_required_artifact_count,
        },
    }
    plan["validation"] = validate_read_only_adapter_preflight_plan(plan, manifest=workflow_manifest)
    return plan


def validate_read_only_adapter_preflight_plan(
    plan: Dict[str, Any],
    *,
    manifest: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    workflow_manifest = deepcopy(manifest) if manifest is not None else workflow_registry.get_agentic_workflow_manifest()
    expected_order = list(workflow_manifest.get("ordered_agent_keys") or [])
    results = list(plan.get("adapter_preflight_results") or [])
    actual_order = [_clean_text(result.get("agent_key")) for result in results]
    reason_codes: List[str] = []
    warning_codes: List[str] = []

    if _clean_text(plan.get("execution_mode")) != EXECUTION_MODE:
        reason_codes.append("execution_mode_not_read_only_preflight")
    if bool(plan.get("allow_agent_execution")):
        reason_codes.append("allow_agent_execution_true")
    if int(plan.get("executable_adapter_count") or 0) != 0:
        reason_codes.append("executable_adapter_count_nonzero")
    if actual_order != expected_order:
        reason_codes.append("adapter_order_mismatch")

    for result in results:
        agent_key = _clean_text(result.get("agent_key")) or "<unknown>"
        if bool(result.get("execution_enabled")):
            reason_codes.append(f"{agent_key}:execution_enabled")
        if bool(result.get("did_execute")):
            reason_codes.append(f"{agent_key}:did_execute")
        if bool(result.get("mutates_production_decisions")):
            reason_codes.append(f"{agent_key}:mutates_production_decisions")
        if bool(result.get("llm_call_expected")):
            reason_codes.append(f"{agent_key}:llm_call_expected")
        if _clean_text(result.get("allowed_execution_mode")) in orchestrator_adapters.LIVE_EXECUTION_MODES:
            reason_codes.append(f"{agent_key}:live_execution_mode")
        if not list(result.get("reason_codes") or []):
            reason_codes.append(f"{agent_key}:missing_reason_codes")
        if _clean_text(result.get("preflight_status")) not in {
            "ready_read_only_contract",
            "needs_adapter",
            "blocked",
        }:
            reason_codes.append(f"{agent_key}:unknown_preflight_status")
        missing_artifacts = [
            artifact
            for artifact, presence in dict(result.get("artifact_presence") or {}).items()
            if not bool(dict(presence).get("exists"))
        ]
        if missing_artifacts:
            warning_codes.append(f"{agent_key}:missing_required_artifacts")

    missing_results = [key for key in expected_order if key not in actual_order]
    if missing_results:
        reason_codes.append("missing_adapter_preflight_results")

    unique_reasons = sorted(set(reason_codes))
    unique_warnings = sorted(set(warning_codes))
    if unique_reasons:
        status = "failed"
    elif unique_warnings:
        status = "warning"
    else:
        status = "passed"
    return {
        "validation_status": status,
        "reason_codes": unique_reasons,
        "warning_codes": unique_warnings,
        "expected_order": expected_order,
        "actual_order": actual_order,
        "planned_adapter_count": len(results),
        "execution_mode": _clean_text(plan.get("execution_mode")),
    }


def render_read_only_adapter_preflight_markdown(
    plan: Dict[str, Any] | None = None,
) -> str:
    payload = deepcopy(plan) if plan is not None else build_read_only_adapter_preflight_plan()
    validation = dict(payload.get("validation") or validate_read_only_adapter_preflight_plan(payload))
    lines = [
        "# Read-Only Adapter Preflight",
        "",
        "Preflight-only warning: this harness does not execute agents, enable autonomous execution,",
        "call LLMs, wire into live planning, or change production behavior.",
        "",
        f"Workflow: `{_clean_text(payload.get('workflow_name'))}`",
        f"Workflow version: `{_clean_text(payload.get('workflow_version'))}`",
        f"Harness version: `{_clean_text(payload.get('harness_version'))}`",
        f"Execution mode: `{_clean_text(payload.get('execution_mode'))}`",
        f"Allow agent execution: `{bool(payload.get('allow_agent_execution'))}`",
        f"Executable adapter count: `{int(payload.get('executable_adapter_count') or 0)}`",
        f"Validation: `{validation.get('validation_status', '')}`",
        "",
        "## Adapter Results",
        "",
    ]
    for result in list(payload.get("adapter_preflight_results") or []):
        lines.extend(
            [
                f"### {result.get('step_index')}. {result.get('agent_name', '')}",
                "",
                f"- Agent key: `{_clean_text(result.get('agent_key'))}`",
                f"- Owner module: `{_clean_text(result.get('owner_module'))}`",
                f"- Adapter status: `{_clean_text(result.get('adapter_status'))}`",
                f"- Preflight status: `{_clean_text(result.get('preflight_status'))}`",
                f"- Execution enabled: `{bool(result.get('execution_enabled'))}`",
                f"- Did execute: `{bool(result.get('did_execute'))}`",
                f"- Mutates production decisions: `{bool(result.get('mutates_production_decisions'))}`",
                f"- LLM call expected: `{bool(result.get('llm_call_expected'))}`",
                f"- Reasons: {', '.join(f'`{item}`' for item in list(result.get('reason_codes') or [])) or 'none'}",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def write_read_only_adapter_preflight_artifacts(
    *,
    output_dir: str | Path,
    plan_json_path: str | Path | None = None,
    report_md_path: str | Path | None = None,
    plan: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    root = Path(output_dir)
    json_path = Path(plan_json_path) if plan_json_path else root / PREFLIGHT_JSON_NAME
    md_path = Path(report_md_path) if report_md_path else root / PREFLIGHT_MD_NAME
    payload = deepcopy(plan) if plan is not None else build_read_only_adapter_preflight_plan()
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(render_read_only_adapter_preflight_markdown(payload), encoding="utf-8")
    return {
        "json_path": str(json_path),
        "md_path": str(md_path),
        "payload": payload,
        "validation_status": payload.get("validation", {}).get("validation_status", ""),
    }


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a read-only adapter preflight plan.")
    parser.add_argument("--preflight", action="store_true", help="Generate preflight metadata without executing agents.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--pipeline-run-id", default="", help="Optional pipeline run id for the preflight context.")
    parser.add_argument("--owner-user-id", default="", help="Optional owner user id for the preflight context.")
    parser.add_argument("--artifact-root", default="", help="Optional artifact root to inspect for artifact presence.")
    args = parser.parse_args(argv)

    if not args.preflight:
        parser.error("Only --preflight mode is supported.")

    payload = build_read_only_adapter_preflight_plan(
        pipeline_run_id=args.pipeline_run_id,
        owner_user_id=args.owner_user_id,
        artifact_root=args.artifact_root,
    )
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        validation = dict(payload.get("validation") or {})
        print(f"Read-only adapter preflight: {validation.get('validation_status', '')}")
        print(f"Planned adapters: {payload.get('planned_adapter_count', 0)}")
        print(f"Executable adapters: {payload.get('executable_adapter_count', 0)}")
    return 0 if payload.get("validation", {}).get("validation_status") in {"passed", "warning"} else 1


if __name__ == "__main__":
    sys.exit(main())
