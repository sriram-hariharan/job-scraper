"""Default-off Phase 16A runtime readiness plan for live JD."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


RUNTIME_READINESS_PLAN_VERSION = (
    "phase-16a-live-jd-intelligence-runtime-readiness-plan-v1"
)
STATUS_SKIPPED = "runtime_readiness_plan_skipped_default_off"
STATUS_READY = "runtime_readiness_plan_ready_for_review_no_runtime"


def live_jd_intelligence_runtime_readiness_plan_safety_metadata(
) -> dict[str, bool]:
    return {
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "runtime_readiness_plan_only": True,
        "planning_only": True,
        "approval_gate_closed": True,
        "jd_intelligence_only": True,
        "future_runtime_requires_separate_explicit_phase": True,
        "external_adapter_required": True,
        "config_gate_required": True,
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


def _source_summary(
    payload: dict[str, Any],
    *,
    status_key: str,
) -> dict[str, Any]:
    return {
        "supplied": bool(payload),
        "status": _text(payload.get(status_key)),
        "mutation_authorized": (
            payload.get("mutation_authorized") is True
        ),
        "source_payload": payload,
    }


def build_live_jd_intelligence_runtime_readiness_plan(
    *,
    enabled: bool = False,
    phase15_wrap: dict[str, Any] | None = None,
    provider_runtime_readiness: dict[str, Any] | None = None,
    provider_runtime_activation_plan: dict[str, Any] | None = None,
    provider_live_safety_plan: dict[str, Any] | None = None,
    provider_live_config_gate: dict[str, Any] | None = None,
    jd_live_canary_runbook: dict[str, Any] | None = None,
    runtime_readiness_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compose readiness evidence without enabling provider runtime."""

    phase15 = _plain_dict(phase15_wrap)
    runtime_readiness = _plain_dict(provider_runtime_readiness)
    activation_plan = _plain_dict(provider_runtime_activation_plan)
    safety_plan = _plain_dict(provider_live_safety_plan)
    config_gate = _plain_dict(provider_live_config_gate)
    runbook = _plain_dict(jd_live_canary_runbook)
    context = _plain_dict(runtime_readiness_context)
    phase15_boundaries = _plain_dict(
        phase15.get("decision_boundaries")
    )
    phase15_forbidden = _plain_dict(
        phase15.get("forbidden_mutation_and_application_paths")
    )
    checks = {
        "phase15_wrap_supplied": bool(phase15),
        "phase15_wrap_review_only": (
            phase15.get("phase_wrap_review_only") is True
        ),
        "phase15_execution_not_authorized": (
            bool(phase15)
            and phase15.get("execution_authorized") is False
        ),
        "phase15_rollout_not_authorized": (
            bool(phase15)
            and phase15.get("rollout_authorized") is False
        ),
        "phase15_mutation_not_authorized": (
            bool(phase15)
            and phase15.get("mutation_authorized") is False
        ),
        "phase15_approval_gate_closed": (
            bool(phase15)
            and phase15.get("approval_gate_open") is False
        ),
        "phase15_future_runtime_requires_explicit_phase": (
            phase15.get(
                "future_runtime_requires_separate_explicit_phase"
            )
            is True
        ),
        "provider_runtime_readiness_supplied": bool(runtime_readiness),
        "provider_runtime_activation_plan_supplied": bool(
            activation_plan
        ),
        "provider_live_safety_plan_supplied": bool(safety_plan),
        "provider_live_config_gate_supplied": bool(config_gate),
        "jd_live_canary_runbook_supplied": bool(runbook),
        "external_adapter_required": (
            runbook.get("external_adapter_required") is True
            and activation_plan.get(
                "injected_provider_adapter_required"
            )
            is True
            and safety_plan.get("injected_provider_adapter_required")
            is True
        ),
        "config_gate_required": (
            runbook.get("config_gate_allow_required") is True
            and bool(config_gate)
        ),
        "manual_only_boundary_preserved": (
            runbook.get("manual_execution_only") is True
        ),
        "one_job_only_boundary_preserved": (
            runbook.get("one_job_only") is True
        ),
        "shadow_only_boundary_preserved": (
            runtime_readiness.get("shadow_only") is True
            and activation_plan.get("shadow_only_required") is True
            and safety_plan.get("shadow_only_required") is True
            and runbook.get("shadow_only_required") is True
        ),
        "jd_intelligence_only_boundary_preserved": (
            activation_plan.get("first_activation_agent")
            == "jd_intelligence"
            and safety_plan.get("first_real_canary_agent")
            == "jd_intelligence"
            and config_gate.get("allowed_agent_name")
            == "jd_intelligence"
            and runbook.get("allowed_agent_name") == "jd_intelligence"
        ),
        "scoring_influence_blocked": (
            phase15_forbidden.get("scoring_influence_allowed")
            is False
        ),
        "ranking_influence_blocked": (
            phase15_forbidden.get("ranking_influence_allowed")
            is False
        ),
        "queue_influence_blocked": (
            phase15_forbidden.get("queue_influence_allowed") is False
        ),
        "resume_mutation_blocked": (
            phase15_forbidden.get("resume_mutation_allowed") is False
        ),
        "application_execution_blocked": (
            phase15_forbidden.get("application_execution_allowed")
            is False
        ),
        "application_submission_blocked": (
            phase15_forbidden.get("application_submission_allowed")
            is False
        ),
        "prefilter_relevance_separation_preserved": (
            phase15_boundaries.get(
                "prefilter_relevance_is_separate"
            )
            is True
        ),
        "jd_intelligence_evaluation_separation_preserved": (
            phase15_boundaries.get(
                "jd_intelligence_evaluation_is_separate"
            )
            is True
        ),
        "final_application_scoring_separation_preserved": (
            phase15_boundaries.get(
                "final_application_scoring_is_separate"
            )
            is True
        ),
        "runtime_readiness_context_supplied": bool(context),
    }
    return {
        "runtime_readiness_plan_version": (
            RUNTIME_READINESS_PLAN_VERSION
        ),
        "runtime_readiness_plan_enabled": enabled is True,
        "runtime_readiness_plan_status": (
            STATUS_READY if enabled is True else STATUS_SKIPPED
        ),
        "default_off": True,
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "runtime_readiness_plan_only": True,
        "planning_only": True,
        "approval_gate_closed": True,
        "jd_intelligence_only": True,
        "external_adapter_required": True,
        "config_gate_required": True,
        "approval_gate_open": False,
        "approval_recorded": False,
        "operator_approval_recorded": False,
        "execution_authorized": False,
        "rollout_authorized": False,
        "runtime_authorized": False,
        "mutation_authorized": False,
        "mutation_authorized_agent_count": 0,
        "future_runtime_requires_separate_explicit_phase": True,
        "phase15_wrap_summary": {
            "phase15_wrap_supplied": bool(phase15),
            "phase15_wrap_status": _text(
                phase15.get("phase_wrap_status")
            ),
            "phase_wrap_review_only": (
                phase15.get("phase_wrap_review_only") is True
            ),
            "approval_gate_open": (
                phase15.get("approval_gate_open") is True
            ),
            "execution_authorized": (
                phase15.get("execution_authorized") is True
            ),
            "rollout_authorized": (
                phase15.get("rollout_authorized") is True
            ),
            "mutation_authorized": (
                phase15.get("mutation_authorized") is True
            ),
            "source_phase15_wrap": phase15,
        },
        "provider_planning_summaries": {
            "provider_runtime_readiness": _source_summary(
                runtime_readiness,
                status_key="readiness_status",
            ),
            "provider_runtime_activation_plan": _source_summary(
                activation_plan,
                status_key="activation_status",
            ),
            "provider_live_safety_plan": _source_summary(
                safety_plan,
                status_key="plan_status",
            ),
            "provider_live_config_gate": _source_summary(
                config_gate,
                status_key="gate_status",
            ),
            "jd_live_canary_runbook": _source_summary(
                runbook,
                status_key="runbook_status",
            ),
        },
        "phase16a_runtime_readiness_planning": {
            "scope": "live_jd_intelligence_runtime_readiness_plan",
            "runtime_readiness_checks": checks,
            "planning_state": {
                "approval_gate_open": False,
                "approval_recorded": False,
                "operator_approval_recorded": False,
                "execution_authorized": False,
                "rollout_authorized": False,
                "runtime_authorized": False,
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
        "runtime_readiness_context": context,
        "next_safe_step": (
            "review_phase16a_runtime_readiness_plan_without_runtime"
            if enabled is True
            else "enable_phase16a_runtime_readiness_plan_only"
        ),
        "safety_metadata": (
            live_jd_intelligence_runtime_readiness_plan_safety_metadata()
        ),
    }
