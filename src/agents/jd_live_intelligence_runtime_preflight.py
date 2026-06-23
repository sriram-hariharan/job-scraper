"""Default-off Phase 16B runtime preflight for live JD intelligence."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


RUNTIME_PREFLIGHT_VERSION = (
    "phase-16b-live-jd-intelligence-runtime-preflight-v1"
)
STATUS_SKIPPED = "runtime_preflight_skipped_default_off"
STATUS_READY = "runtime_preflight_ready_for_review_no_runtime"


def live_jd_intelligence_runtime_preflight_safety_metadata(
) -> dict[str, bool]:
    return {
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "runtime_preflight_only": True,
        "planning_only": True,
        "approval_gate_closed": True,
        "jd_intelligence_only": True,
        "one_job_only": True,
        "manual_only": True,
        "external_adapter_required": True,
        "config_gate_required": True,
        "future_runtime_requires_separate_explicit_phase": True,
        "provider_execution_added": False,
        "provider_client_constructed": False,
        "provider_sdk_imported": False,
        "environment_secrets_read": False,
        "network_calls_made": False,
        "did_read_database": False,
        "did_write_database": False,
        "did_read_files": False,
        "did_write_files": False,
        "did_mutate_scoring": False,
        "did_change_ranking": False,
        "did_mutate_queue": False,
        "did_mutate_resume": False,
        "did_execute_application": False,
        "did_submit_application": False,
    }


def _plain_dict(value: Any) -> dict[str, Any]:
    return deepcopy(value) if isinstance(value, dict) else {}


def _text(value: Any) -> str:
    return str(value or "").strip()


def build_live_jd_intelligence_runtime_preflight(
    *,
    enabled: bool = False,
    phase16a_runtime_readiness_plan: dict[str, Any] | None = None,
    provider_live_config_gate: dict[str, Any] | None = None,
    jd_live_canary_runbook: dict[str, Any] | None = None,
    preflight_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Review runtime prerequisites without authorizing any invocation."""

    phase16a = _plain_dict(phase16a_runtime_readiness_plan)
    config_gate = _plain_dict(provider_live_config_gate)
    runbook = _plain_dict(jd_live_canary_runbook)
    context = _plain_dict(preflight_context)
    boundaries = _plain_dict(phase16a.get("decision_boundaries"))
    forbidden = _plain_dict(
        phase16a.get("forbidden_mutation_and_application_paths")
    )
    checks = {
        "phase16a_plan_supplied": bool(phase16a),
        "phase16a_runtime_readiness_plan_only": (
            phase16a.get("runtime_readiness_plan_only") is True
        ),
        "phase16a_execution_not_authorized": (
            bool(phase16a)
            and phase16a.get("execution_authorized") is False
        ),
        "phase16a_runtime_not_authorized": (
            bool(phase16a)
            and phase16a.get("runtime_authorized") is False
        ),
        "phase16a_rollout_not_authorized": (
            bool(phase16a)
            and phase16a.get("rollout_authorized") is False
        ),
        "phase16a_mutation_not_authorized": (
            bool(phase16a)
            and phase16a.get("mutation_authorized") is False
        ),
        "phase16a_approval_gate_closed": (
            bool(phase16a)
            and phase16a.get("approval_gate_open") is False
        ),
        "phase16a_external_adapter_required": (
            phase16a.get("external_adapter_required") is True
        ),
        "phase16a_config_gate_required": (
            phase16a.get("config_gate_required") is True
        ),
        "provider_live_config_gate_supplied": bool(config_gate),
        "provider_live_config_gate_allowed": (
            config_gate.get("canary_allowed") is True
        ),
        "provider_live_config_gate_shadow_only": (
            config_gate.get("shadow_only") is True
        ),
        "provider_live_config_gate_no_mutation_authority": (
            config_gate.get("mutation_authorized") is False
            and config_gate.get("mutation_authorized_agent_count") == 0
        ),
        "jd_live_canary_runbook_supplied": bool(runbook),
        "runbook_manual_only": (
            runbook.get("manual_execution_only") is True
        ),
        "runbook_one_job_only": runbook.get("one_job_only") is True,
        "runbook_shadow_only_required": (
            runbook.get("shadow_only_required") is True
        ),
        "runbook_jd_intelligence_only": (
            runbook.get("allowed_agent_name") == "jd_intelligence"
        ),
        "runbook_external_adapter_required": (
            runbook.get("external_adapter_required") is True
        ),
        "runbook_config_gate_required": (
            runbook.get("config_gate_allow_required") is True
        ),
        "canary_execution_not_authorized": True,
        "adapter_invocation_not_authorized": True,
        "scoring_influence_blocked": (
            forbidden.get("scoring_influence_allowed") is False
        ),
        "ranking_influence_blocked": (
            forbidden.get("ranking_influence_allowed") is False
        ),
        "queue_influence_blocked": (
            forbidden.get("queue_influence_allowed") is False
        ),
        "resume_mutation_blocked": (
            forbidden.get("resume_mutation_allowed") is False
        ),
        "application_execution_blocked": (
            forbidden.get("application_execution_allowed") is False
        ),
        "application_submission_blocked": (
            forbidden.get("application_submission_allowed") is False
        ),
        "prefilter_relevance_separation_preserved": (
            boundaries.get("prefilter_relevance_is_separate") is True
        ),
        "jd_intelligence_evaluation_separation_preserved": (
            boundaries.get(
                "jd_intelligence_evaluation_is_separate"
            )
            is True
        ),
        "final_application_scoring_separation_preserved": (
            boundaries.get(
                "final_application_scoring_is_separate"
            )
            is True
        ),
        "preflight_context_supplied": bool(context),
    }
    return {
        "runtime_preflight_version": RUNTIME_PREFLIGHT_VERSION,
        "runtime_preflight_enabled": enabled is True,
        "runtime_preflight_status": (
            STATUS_READY if enabled is True else STATUS_SKIPPED
        ),
        "default_off": True,
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "runtime_preflight_only": True,
        "planning_only": True,
        "approval_gate_closed": True,
        "jd_intelligence_only": True,
        "one_job_only": True,
        "manual_only": True,
        "external_adapter_required": True,
        "config_gate_required": True,
        "approval_gate_open": False,
        "approval_recorded": False,
        "operator_approval_recorded": False,
        "execution_authorized": False,
        "runtime_authorized": False,
        "rollout_authorized": False,
        "canary_execution_authorized": False,
        "adapter_invocation_authorized": False,
        "mutation_authorized": False,
        "mutation_authorized_agent_count": 0,
        "future_runtime_requires_separate_explicit_phase": True,
        "phase16a_runtime_readiness_plan_summary": {
            "phase16a_plan_supplied": bool(phase16a),
            "runtime_readiness_plan_status": _text(
                phase16a.get("runtime_readiness_plan_status")
            ),
            "runtime_readiness_plan_only": (
                phase16a.get("runtime_readiness_plan_only") is True
            ),
            "approval_gate_open": (
                phase16a.get("approval_gate_open") is True
            ),
            "execution_authorized": (
                phase16a.get("execution_authorized") is True
            ),
            "runtime_authorized": (
                phase16a.get("runtime_authorized") is True
            ),
            "rollout_authorized": (
                phase16a.get("rollout_authorized") is True
            ),
            "mutation_authorized": (
                phase16a.get("mutation_authorized") is True
            ),
            "source_phase16a_plan": phase16a,
        },
        "provider_live_config_gate_summary": {
            "config_gate_supplied": bool(config_gate),
            "gate_status": _text(config_gate.get("gate_status")),
            "canary_allowed_by_config_gate": (
                config_gate.get("canary_allowed") is True
            ),
            "shadow_only": config_gate.get("shadow_only") is True,
            "mutation_authorized": (
                config_gate.get("mutation_authorized") is True
            ),
            "source_config_gate": config_gate,
        },
        "jd_live_canary_runbook_summary": {
            "runbook_supplied": bool(runbook),
            "runbook_status": _text(runbook.get("runbook_status")),
            "manual_execution_only": (
                runbook.get("manual_execution_only") is True
            ),
            "one_job_only": runbook.get("one_job_only") is True,
            "shadow_only_required": (
                runbook.get("shadow_only_required") is True
            ),
            "allowed_agent_name": _text(
                runbook.get("allowed_agent_name")
            ),
            "source_runbook": runbook,
        },
        "phase16b_runtime_preflight": {
            "scope": "live_jd_intelligence_runtime_preflight",
            "runtime_preflight_checks": checks,
            "preflight_state": {
                "approval_gate_open": False,
                "approval_recorded": False,
                "operator_approval_recorded": False,
                "execution_authorized": False,
                "runtime_authorized": False,
                "rollout_authorized": False,
                "canary_execution_authorized": False,
                "adapter_invocation_authorized": False,
                "mutation_authorized": False,
            },
        },
        "decision_boundaries": {
            "prefilter_relevance_is_separate": True,
            "jd_intelligence_evaluation_is_separate": True,
            "final_application_scoring_is_separate": True,
            "prefilter_output_modified": False,
            "jd_evaluation_execution_added": False,
            "final_scoring_input_modified": False,
        },
        "forbidden_mutation_and_application_paths": {
            "broader_provider_expansion_allowed": False,
            "tailoring_expansion_allowed": False,
            "critic_expansion_allowed": False,
            "scoring_influence_allowed": False,
            "ranking_influence_allowed": False,
            "queue_influence_allowed": False,
            "approval_mutation_allowed": False,
            "resume_mutation_allowed": False,
            "execution_request_allowed": False,
            "application_execution_allowed": False,
            "application_submission_allowed": False,
        },
        "preflight_context": context,
        "next_safe_step": (
            "review_phase16b_runtime_preflight_without_runtime"
            if enabled is True
            else "enable_phase16b_runtime_preflight_only"
        ),
        "safety_metadata": (
            live_jd_intelligence_runtime_preflight_safety_metadata()
        ),
    }
