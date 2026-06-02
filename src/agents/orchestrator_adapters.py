from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List

from src.agents import workflow_registry


ADAPTER_CONTRACT_VERSION = "orchestrator_adapter_contract_v1"
WORKFLOW_RUNNER_MODE = "dry_run_only"

ADAPTER_STATUSES = {
    "ready_for_read_only_adapter",
    "needs_input_adapter",
    "needs_policy_adapter",
    "blocked",
}
ALLOWED_EXECUTION_MODES = {"dry_run_only", "future_read_only"}
LIVE_EXECUTION_MODES = {"live", "autonomous", "production", "real_execution"}


ORCHESTRATOR_ADAPTER_SPECS: Dict[str, Dict[str, Any]] = {
    "source_health": {
        "agent_key": "source_health",
        "owner_module": "src.agents.source_health_agent",
        "adapter_status": "needs_policy_adapter",
        "callable_entrypoint_names": [
            "parse_source_health_report_csv",
            "build_source_health_agent_input_payload",
            "build_source_health_agent_output_payload",
            "build_source_health_agent_validation_payload",
            "render_source_health_recommendations",
            "record_source_health_agent_trace",
        ],
        "input_loader_required": True,
        "output_validator_required": True,
        "artifact_writer_available": False,
        "trace_supported": True,
        "db_access_required": False,
        "env_context_required": True,
        "llm_call_expected": False,
        "mutates_production_decisions": False,
        "allowed_execution_mode": "dry_run_only",
        "side_effect_policy": "contract_only_payload_rendering; future adapter must define diagnostic artifact policy before execution",
        "required_artifacts": ["source_health_report.csv"],
        "produced_artifacts": ["source_health_report.csv"],
        "reason_codes": [
            "contract_only",
            "needs_input_loader",
            "needs_diagnostic_artifact_policy",
            "trace_context_required",
        ],
    },
    "resume_match": {
        "agent_key": "resume_match",
        "owner_module": "src.agents.resume_match_agent",
        "adapter_status": "needs_input_adapter",
        "callable_entrypoint_names": [
            "build_resume_match_agent_input_payload",
            "build_resume_match_agent_output_payload",
            "build_resume_match_agent_validation_payload",
            "build_resume_match_agent_summary_payload",
            "record_resume_match_agent_trace",
        ],
        "input_loader_required": True,
        "output_validator_required": True,
        "artifact_writer_available": False,
        "trace_supported": True,
        "db_access_required": False,
        "env_context_required": True,
        "llm_call_expected": False,
        "mutates_production_decisions": False,
        "allowed_execution_mode": "dry_run_only",
        "side_effect_policy": "contract_only_payload_rendering; future adapter must load candidate resume context and define diagnostic artifact policy",
        "required_artifacts": ["best_resume_variant_by_job.csv"],
        "produced_artifacts": ["best_resume_variant_by_job.csv"],
        "reason_codes": [
            "contract_only",
            "needs_candidate_resume_context",
            "needs_input_loader",
            "needs_diagnostic_artifact_policy",
            "trace_context_required",
        ],
    },
    "critic": {
        "agent_key": "critic",
        "owner_module": "src.agents.critic_agent",
        "adapter_status": "needs_policy_adapter",
        "callable_entrypoint_names": [
            "build_critic_agent_input_payload",
            "evaluate_critic_suggestion",
            "build_critic_agent_validation_payload",
            "render_critic_decision",
            "build_critic_agent_summary_payload",
            "record_critic_agent_trace",
        ],
        "input_loader_required": True,
        "output_validator_required": True,
        "artifact_writer_available": False,
        "trace_supported": True,
        "db_access_required": False,
        "env_context_required": True,
        "llm_call_expected": False,
        "mutates_production_decisions": False,
        "allowed_execution_mode": "dry_run_only",
        "side_effect_policy": "contract_only_payload_rendering; future adapter must define scan suggestion loader, feature flag policy, and diagnostic artifact policy",
        "required_artifacts": ["scan suggestions"],
        "produced_artifacts": ["critic advisory metadata"],
        "reason_codes": [
            "contract_only",
            "needs_scan_suggestion_loader",
            "needs_feature_flag_policy",
            "needs_diagnostic_artifact_policy",
            "trace_context_required",
        ],
    },
    "job_prioritization": {
        "agent_key": "job_prioritization",
        "owner_module": "src.agents.job_prioritization_agent",
        "adapter_status": "ready_for_read_only_adapter",
        "callable_entrypoint_names": [
            "build_job_prioritization_agent_input_payload",
            "recommend_job_priority",
            "build_job_prioritization_agent_output_payload",
            "build_job_prioritization_agent_validation_payload",
            "render_job_prioritization_recommendations",
            "render_job_prioritization_recommendation_rows",
            "write_job_prioritization_artifacts",
            "record_job_prioritization_agent_trace",
        ],
        "input_loader_required": True,
        "output_validator_required": True,
        "artifact_writer_available": True,
        "prototype_adapter_module": "src.agents.read_only_job_prioritization_adapter",
        "prototype_execution_mode": "manual_read_only_adapter",
        "prototype_execution_enabled": False,
        "trace_supported": True,
        "db_access_required": False,
        "env_context_required": True,
        "llm_call_expected": False,
        "mutates_production_decisions": False,
        "allowed_execution_mode": "future_read_only",
        "side_effect_policy": "contract_only; future adapter may write diagnostic advisory artifacts only under owner-scoped run artifacts",
        "required_artifacts": ["application_execution_queue.csv", "source_health_report.csv"],
        "produced_artifacts": [
            "job_prioritization_recommendations.csv",
            "job_prioritization_summary.json",
        ],
        "reason_codes": [
            "contract_only",
            "artifact_writer_exists",
            "validation_exists",
            "trace_optional",
        ],
    },
    "tailoring_decision": {
        "agent_key": "tailoring_decision",
        "owner_module": "src.agents.tailoring_decision_agent",
        "adapter_status": "ready_for_read_only_adapter",
        "callable_entrypoint_names": [
            "build_tailoring_decision_agent_input_payload",
            "recommend_tailoring_decision",
            "build_tailoring_decision_agent_output_payload",
            "build_tailoring_decision_agent_validation_payload",
            "render_tailoring_decisions",
            "render_tailoring_decision_rows",
            "write_tailoring_decision_artifacts",
            "record_tailoring_decision_agent_trace",
        ],
        "input_loader_required": True,
        "output_validator_required": True,
        "artifact_writer_available": True,
        "prototype_adapter_module": "src.agents.read_only_tailoring_decision_adapter",
        "prototype_execution_mode": "manual_read_only_adapter",
        "prototype_execution_enabled": False,
        "trace_supported": True,
        "db_access_required": False,
        "env_context_required": True,
        "llm_call_expected": False,
        "mutates_production_decisions": False,
        "allowed_execution_mode": "future_read_only",
        "side_effect_policy": "contract_only; future adapter may write diagnostic advisory artifacts only under owner-scoped run artifacts",
        "required_artifacts": [
            "application_execution_queue.csv",
            "job_prioritization_recommendations.csv",
        ],
        "produced_artifacts": [
            "tailoring_decision_recommendations.csv",
            "tailoring_decision_summary.json",
        ],
        "reason_codes": [
            "contract_only",
            "artifact_writer_exists",
            "validation_exists",
            "trace_optional",
        ],
    },
    "operator_review": {
        "agent_key": "operator_review",
        "owner_module": "src.agents.operator_review_agent",
        "adapter_status": "ready_for_read_only_adapter",
        "callable_entrypoint_names": [
            "build_operator_review_agent_input_payload",
            "recommend_operator_lane",
            "build_operator_review_agent_output_payload",
            "build_operator_review_agent_validation_payload",
            "render_operator_review",
            "render_operator_review_rows",
            "write_operator_review_artifacts",
            "record_operator_review_agent_trace",
        ],
        "input_loader_required": True,
        "output_validator_required": True,
        "artifact_writer_available": True,
        "trace_supported": True,
        "db_access_required": False,
        "env_context_required": True,
        "llm_call_expected": False,
        "mutates_production_decisions": False,
        "allowed_execution_mode": "future_read_only",
        "side_effect_policy": "contract_only; future adapter may write diagnostic advisory artifacts only under owner-scoped run artifacts",
        "required_artifacts": [
            "application_execution_queue.csv",
            "job_prioritization_recommendations.csv",
            "tailoring_decision_recommendations.csv",
        ],
        "produced_artifacts": [
            "operator_review_recommendations.csv",
            "operator_review_summary.json",
        ],
        "reason_codes": [
            "contract_only",
            "artifact_writer_exists",
            "validation_exists",
            "trace_optional",
        ],
    },
}


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _adapter_specs_by_key(contract: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    specs = contract.get("adapter_specs") if isinstance(contract, dict) else {}
    return dict(specs) if isinstance(specs, dict) else {}


def get_orchestrator_adapter_contract() -> Dict[str, Any]:
    manifest = workflow_registry.get_agentic_workflow_manifest()
    return {
        "contract_version": ADAPTER_CONTRACT_VERSION,
        "workflow_name": _clean_text(manifest.get("workflow_name")),
        "workflow_version": _clean_text(manifest.get("workflow_version")),
        "contract_only": True,
        "runner_mode": WORKFLOW_RUNNER_MODE,
        "execution_enabled": False,
        "autonomous_execution_enabled": False,
        "ordered_agent_keys": list(manifest.get("ordered_agent_keys") or []),
        "adapter_specs": deepcopy(ORCHESTRATOR_ADAPTER_SPECS),
        "safety_guarantees": [
            "This adapter contract is static metadata only.",
            "No adapter executes agents in this phase.",
            "No adapter mutates production decisions.",
            "workflow_runner.py remains dry-run only.",
        ],
    }


def list_orchestrator_adapter_specs() -> List[Dict[str, Any]]:
    contract = get_orchestrator_adapter_contract()
    specs = _adapter_specs_by_key(contract)
    return [
        deepcopy(specs[key])
        for key in list(contract.get("ordered_agent_keys") or [])
        if key in specs
    ]


def get_orchestrator_adapter_spec(agent_key: str) -> Dict[str, Any]:
    key = _clean_text(agent_key)
    specs = _adapter_specs_by_key(get_orchestrator_adapter_contract())
    if key not in specs:
        raise KeyError(f"Unknown orchestrator adapter key: {agent_key}")
    return deepcopy(specs[key])


def validate_orchestrator_adapter_contract(
    contract: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    payload = deepcopy(contract) if contract is not None else get_orchestrator_adapter_contract()
    manifest = workflow_registry.get_agentic_workflow_manifest()
    registry_keys = list(manifest.get("ordered_agent_keys") or [])
    specs = _adapter_specs_by_key(payload)
    spec_keys = list(specs)
    reason_codes: List[str] = []

    missing_specs = [key for key in registry_keys if key not in specs]
    extra_specs = [key for key in spec_keys if key not in registry_keys]
    if missing_specs:
        reason_codes.append("missing_adapter_specs")
    if extra_specs:
        reason_codes.append("unknown_adapter_specs")

    if payload.get("execution_enabled"):
        reason_codes.append("execution_enabled")
    if payload.get("autonomous_execution_enabled"):
        reason_codes.append("autonomous_execution_enabled")
    if _clean_text(payload.get("runner_mode")) != WORKFLOW_RUNNER_MODE:
        reason_codes.append("runner_mode_not_dry_run_only")

    for key, spec in specs.items():
        agent_key = _clean_text(spec.get("agent_key"))
        if agent_key != key:
            reason_codes.append(f"{key}:agent_key_mismatch")
        if _clean_text(spec.get("adapter_status")) not in ADAPTER_STATUSES:
            reason_codes.append(f"{key}:unknown_adapter_status")
        if spec.get("mutates_production_decisions"):
            reason_codes.append(f"{key}:mutates_production_decisions")
        if spec.get("llm_call_expected"):
            reason_codes.append(f"{key}:llm_call_expected")
        mode = _clean_text(spec.get("allowed_execution_mode"))
        if mode in LIVE_EXECUTION_MODES or mode not in ALLOWED_EXECUTION_MODES:
            reason_codes.append(f"{key}:live_execution_mode")
        entrypoints = spec.get("callable_entrypoint_names")
        if not isinstance(entrypoints, list) or not entrypoints:
            reason_codes.append(f"{key}:missing_callable_entrypoint_names")
        elif any(not isinstance(item, str) or not item.strip() for item in entrypoints):
            reason_codes.append(f"{key}:non_string_callable_entrypoint_name")
        if not spec.get("reason_codes") or not isinstance(spec.get("reason_codes"), list):
            reason_codes.append(f"{key}:missing_reason_codes")
        if _clean_text(spec.get("adapter_status")) == "ready_for_read_only_adapter":
            has_writer = bool(spec.get("artifact_writer_available"))
            side_effect_policy = _clean_text(spec.get("side_effect_policy"))
            if not has_writer and "read_only_output" not in side_effect_policy:
                reason_codes.append(f"{key}:ready_adapter_missing_output_policy")

    unique_reasons = sorted(set(reason_codes))
    if unique_reasons:
        status = "failed"
    else:
        status = "passed"

    return {
        "validation_status": status,
        "reason_codes": unique_reasons,
        "warning_codes": [],
        "registry_agent_keys": registry_keys,
        "adapter_agent_keys": spec_keys,
        "adapter_count": len(specs),
    }


def render_orchestrator_adapter_contract_markdown(
    contract: Dict[str, Any] | None = None,
) -> str:
    payload = deepcopy(contract) if contract is not None else get_orchestrator_adapter_contract()
    validation = validate_orchestrator_adapter_contract(payload)
    specs = _adapter_specs_by_key(payload)
    lines = [
        "# Orchestrator Adapter Contract",
        "",
        "Contract-only warning: this metadata is dry-run only readiness documentation.",
        "It does not execute agents, enable autonomous execution, call LLMs, or change production behavior.",
        "",
        f"Contract version: `{_clean_text(payload.get('contract_version'))}`",
        f"Workflow: `{_clean_text(payload.get('workflow_name'))}`",
        f"Workflow runner mode: `{_clean_text(payload.get('runner_mode'))}`",
        f"Execution enabled: `{bool(payload.get('execution_enabled'))}`",
        f"Validation: `{validation.get('validation_status')}`",
        "",
        "## Adapter Specs",
        "",
    ]
    for key in list(payload.get("ordered_agent_keys") or []):
        spec = specs.get(key, {})
        lines.extend(
            [
                f"### `{key}`",
                "",
                f"- Owner module: `{_clean_text(spec.get('owner_module'))}`",
                f"- Adapter status: `{_clean_text(spec.get('adapter_status'))}`",
                f"- Allowed execution mode: `{_clean_text(spec.get('allowed_execution_mode'))}`",
                f"- Mutates production decisions: `{bool(spec.get('mutates_production_decisions'))}`",
                f"- LLM call expected: `{bool(spec.get('llm_call_expected'))}`",
                f"- Artifact writer available: `{bool(spec.get('artifact_writer_available'))}`",
                f"- Trace supported: `{bool(spec.get('trace_supported'))}`",
                f"- Entrypoints: {', '.join(f'`{item}`' for item in list(spec.get('callable_entrypoint_names') or []))}",
                f"- Reason codes: {', '.join(f'`{item}`' for item in list(spec.get('reason_codes') or []))}",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"
