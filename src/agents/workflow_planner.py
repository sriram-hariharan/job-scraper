from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any, Dict, List

from src.agents import workflow_registry


PLANNER_VERSION = "agentic_workflow_planner_v1"
EXECUTION_MODE = "dry_run"
EXECUTION_PLAN_JSON_NAME = "agentic_workflow_execution_plan.json"
EXECUTION_PLAN_MD_NAME = "agentic_workflow_execution_plan.md"

ARTIFACT_NAME_TO_KIND = {
    "source_health_report.csv": "source_health_report",
    "best_resume_variant_by_job.csv": "best_resume_variant_by_job",
    "application_shortlist_by_job.csv": "application_shortlist_by_job",
    "application_execution_queue.csv": "application_execution_queue",
    "job_prioritization_recommendations.csv": "job_prioritization_recommendations",
    "job_prioritization_summary.json": "job_prioritization_summary",
    "tailoring_decision_recommendations.csv": "tailoring_decision_recommendations",
    "tailoring_decision_summary.json": "tailoring_decision_summary",
    "operator_review_recommendations.csv": "operator_review_recommendations",
    "operator_review_summary.json": "operator_review_summary",
    "agentic_workflow_summary.json": "agentic_workflow_summary_json",
    "agentic_workflow_summary.md": "agentic_workflow_summary_md",
    "agentic_workflow_manifest.json": "agentic_workflow_manifest_json",
    "agentic_workflow_manifest.md": "agentic_workflow_manifest_md",
    "agentic_workflow_execution_plan.json": "agentic_workflow_execution_plan_json",
    "agentic_workflow_execution_plan.md": "agentic_workflow_execution_plan_md",
    "agentic_workflow_verification.json": "agentic_workflow_verification_json",
    "job_packet_manifest.csv": "job_packet_manifest",
}


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _artifact_kind(value: Any) -> str:
    return ARTIFACT_NAME_TO_KIND.get(_clean_text(value), "")


def _infer_dependencies(ordered_agents: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    output_owner_by_artifact: Dict[str, str] = {}
    dependencies: Dict[str, List[str]] = {}
    for agent in ordered_agents:
        agent_key = _clean_text(agent.get("agent_key"))
        deps: List[str] = []
        for artifact in list(agent.get("input_artifacts") or []):
            owner = output_owner_by_artifact.get(_clean_text(artifact))
            if owner and owner != agent_key and owner not in deps:
                deps.append(owner)
        dependencies[agent_key] = deps
        for artifact in list(agent.get("output_artifacts") or []):
            output_owner_by_artifact[_clean_text(artifact)] = agent_key
    return dependencies


def build_agentic_workflow_execution_plan(
    manifest: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    payload = deepcopy(manifest) if manifest is not None else workflow_registry.get_agentic_workflow_manifest()
    ordered_keys = list(payload.get("ordered_agent_keys") or [])
    agents_by_key = dict(payload.get("agents") or {})
    ordered_agents = [agents_by_key[key] for key in ordered_keys if key in agents_by_key]
    dependencies_by_key = _infer_dependencies(ordered_agents)
    steps: List[Dict[str, Any]] = []

    for index, agent in enumerate(ordered_agents, start=1):
        agent_key = _clean_text(agent.get("agent_key"))
        steps.append(
            {
                "step_index": index,
                "agent_key": agent_key,
                "agent_name": _clean_text(agent.get("agent_name")),
                "agent_version": _clean_text(agent.get("agent_version")),
                "owner_module": _clean_text(agent.get("owner_module")),
                "model_provider": _clean_text(agent.get("model_provider")),
                "model_name": _clean_text(agent.get("model_name")),
                "advisory_only": bool(agent.get("advisory_only")),
                "diagnostic_only": bool(agent.get("diagnostic_only")),
                "mutates_production_decisions": bool(agent.get("mutates_production_decisions")),
                "input_artifacts": list(agent.get("input_artifacts") or []),
                "output_artifacts": list(agent.get("output_artifacts") or []),
                "depends_on_agent_keys": dependencies_by_key.get(agent_key, []),
                "trace_step_name": _clean_text(agent.get("agent_name")),
                "execution_status": "planned",
                "execution_enabled": False,
            }
        )

    plan = {
        "workflow_name": _clean_text(payload.get("workflow_name")),
        "workflow_version": _clean_text(payload.get("workflow_version")),
        "planner_version": PLANNER_VERSION,
        "execution_mode": EXECUTION_MODE,
        "ordered_steps": steps,
        "expected_input_artifacts": sorted(
            {
                _clean_text(artifact)
                for step in steps
                for artifact in list(step.get("input_artifacts") or [])
                if _clean_text(artifact)
            }
        ),
        "expected_output_artifacts": sorted(
            {
                _clean_text(artifact)
                for step in steps
                for artifact in list(step.get("output_artifacts") or [])
                if _clean_text(artifact)
            }
        ),
        "feature_flags": list(payload.get("feature_flags") or []),
        "safety_guarantees": list(payload.get("safety_guarantees") or []),
    }
    plan["validation"] = validate_agentic_workflow_execution_plan(plan, manifest=payload)
    return plan


def validate_agentic_workflow_execution_plan(
    plan: Dict[str, Any],
    manifest: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    payload = deepcopy(manifest) if manifest is not None else workflow_registry.get_agentic_workflow_manifest()
    expected_order = list(payload.get("ordered_agent_keys") or [])
    generated_artifact_kinds = set(payload.get("generated_artifact_kinds") or [])
    steps = list(plan.get("ordered_steps") or [])
    actual_order = [_clean_text(step.get("agent_key")) for step in steps]
    reason_codes: List[str] = []

    if actual_order != expected_order:
        reason_codes.append("step_order_mismatch")

    seen_agent_keys: set[str] = set()
    for step in steps:
        agent_key = _clean_text(step.get("agent_key"))
        if step.get("execution_enabled"):
            reason_codes.append(f"{agent_key}:execution_enabled")
        if _clean_text(step.get("execution_status")) != "planned":
            reason_codes.append(f"{agent_key}:execution_status_not_planned")
        if step.get("mutates_production_decisions"):
            reason_codes.append(f"{agent_key}:mutates_production_decisions")
        if not _clean_text(step.get("model_provider")):
            reason_codes.append(f"{agent_key}:missing_model_provider")
        if not _clean_text(step.get("model_name")):
            reason_codes.append(f"{agent_key}:missing_model_name")

        for dependency_key in list(step.get("depends_on_agent_keys") or []):
            dependency_key = _clean_text(dependency_key)
            if dependency_key not in seen_agent_keys:
                reason_codes.append(f"{agent_key}:dependency_not_earlier")

        for artifact in list(step.get("output_artifacts") or []):
            kind = _artifact_kind(artifact)
            if kind and kind not in generated_artifact_kinds:
                reason_codes.append(f"{agent_key}:output_artifact_kind_not_declared")

        seen_agent_keys.add(agent_key)

    missing_steps = [key for key in expected_order if key not in actual_order]
    if missing_steps:
        reason_codes.append("missing_plan_steps")

    return {
        "validation_status": "failed" if reason_codes else "passed",
        "reason_codes": sorted(set(reason_codes)),
        "expected_order": expected_order,
        "actual_order": actual_order,
        "step_count": len(steps),
        "execution_mode": _clean_text(plan.get("execution_mode")),
    }


def render_agentic_workflow_execution_plan_markdown(
    plan: Dict[str, Any] | None = None,
) -> str:
    payload = deepcopy(plan) if plan is not None else build_agentic_workflow_execution_plan()
    validation = dict(payload.get("validation") or validate_agentic_workflow_execution_plan(payload))
    lines = [
        "# Agentic Workflow Execution Plan",
        "",
        f"Workflow: `{payload.get('workflow_name', '')}`",
        f"Workflow version: `{payload.get('workflow_version', '')}`",
        f"Planner version: `{payload.get('planner_version', '')}`",
        f"Execution mode: `{payload.get('execution_mode', '')}`",
        f"Validation: `{validation.get('validation_status', '')}`",
        "",
        "## Ordered Steps",
        "",
    ]
    for step in list(payload.get("ordered_steps") or []):
        lines.extend(
            [
                f"### {step.get('step_index')}. {step.get('agent_name', '')}",
                "",
                f"- Agent key: `{step.get('agent_key', '')}`",
                f"- Version: `{step.get('agent_version', '')}`",
                f"- Model: `{step.get('model_provider', '')}/{step.get('model_name', '')}`",
                f"- Execution enabled: `{bool(step.get('execution_enabled'))}`",
                f"- Execution status: `{step.get('execution_status', '')}`",
                f"- Depends on: {', '.join(f'`{item}`' for item in step.get('depends_on_agent_keys', []) or []) or 'none'}",
                f"- Inputs: {', '.join(f'`{item}`' for item in step.get('input_artifacts', []) or []) or 'none'}",
                f"- Outputs: {', '.join(f'`{item}`' for item in step.get('output_artifacts', []) or []) or 'none'}",
                "",
            ]
        )
    lines.extend(["## Safety Guarantees", ""])
    for guarantee in list(payload.get("safety_guarantees") or []):
        lines.append(f"- {guarantee}")
    return "\n".join(lines).strip() + "\n"


def write_agentic_workflow_execution_plan_artifacts(
    *,
    output_dir: str | Path,
    plan_json_path: str | Path | None = None,
    plan_md_path: str | Path | None = None,
) -> Dict[str, Any]:
    root = Path(output_dir)
    json_path = Path(plan_json_path) if plan_json_path else root / EXECUTION_PLAN_JSON_NAME
    md_path = Path(plan_md_path) if plan_md_path else root / EXECUTION_PLAN_MD_NAME
    plan = build_agentic_workflow_execution_plan()
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(plan, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(render_agentic_workflow_execution_plan_markdown(plan), encoding="utf-8")
    return {
        "json_path": str(json_path),
        "md_path": str(md_path),
        "payload": plan,
        "validation_status": plan.get("validation", {}).get("validation_status", ""),
    }
