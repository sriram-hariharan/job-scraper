"""Default-off readiness for the three core ApplyLens workflow agents."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


READINESS_VERSION = "phase-16c-three-core-agent-workflow-readiness-v1"
STATUS_SKIPPED = "three_core_workflow_readiness_skipped_default_off"
STATUS_READY = (
    "three_core_workflow_readiness_ready_no_pipeline_connection"
)
STATUS_INCOMPLETE = "three_core_workflow_readiness_incomplete"
ORDERED_CORE_AGENT_NAMES = (
    "relevance_prefilter",
    "jd_intelligence",
    "final_application_scoring",
)
AGENT_NAME_ALIASES = {
    "relevance_prefilter_agent": "relevance_prefilter",
    "jd_intelligence_agent": "jd_intelligence",
    "final_application_scoring_agent": "final_application_scoring",
}


def three_core_agent_workflow_readiness_safety_metadata(
) -> dict[str, bool]:
    return {
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "workflow_readiness_only": True,
        "three_core_agent_only": True,
        "pipeline_not_connected": True,
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


def _canonical_agent_name(
    descriptor: dict[str, Any],
    expected_name: str,
) -> str:
    supplied_name = _text(descriptor.get("agent_name"))
    if not supplied_name:
        return expected_name if descriptor else ""
    return AGENT_NAME_ALIASES.get(supplied_name, supplied_name)


def _agent_summary(
    descriptor: dict[str, Any],
    expected_name: str,
) -> dict[str, Any]:
    return {
        "descriptor_supplied": bool(descriptor),
        "expected_agent_name": expected_name,
        "canonical_agent_name": _canonical_agent_name(
            descriptor,
            expected_name,
        ),
        "source_agent_name": _text(descriptor.get("agent_name")),
        "agent_version": _text(descriptor.get("agent_version")),
        "status": _text(descriptor.get("status")),
        "source_descriptor": descriptor,
    }


def build_three_core_agent_workflow_readiness(
    *,
    enabled: bool = False,
    relevance_prefilter_descriptor: dict[str, Any] | None = None,
    jd_intelligence_descriptor: dict[str, Any] | None = None,
    final_application_scoring_descriptor: dict[str, Any] | None = None,
    phase16b_runtime_preflight: dict[str, Any] | None = None,
    workflow_readiness_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Review core-agent boundaries without connecting the workflow."""

    prefilter = _plain_dict(relevance_prefilter_descriptor)
    jd_intelligence = _plain_dict(jd_intelligence_descriptor)
    final_scoring = _plain_dict(
        final_application_scoring_descriptor
    )
    preflight = _plain_dict(phase16b_runtime_preflight)
    context = _plain_dict(workflow_readiness_context)
    summaries = {
        "relevance_prefilter": _agent_summary(
            prefilter,
            "relevance_prefilter",
        ),
        "jd_intelligence": _agent_summary(
            jd_intelligence,
            "jd_intelligence",
        ),
        "final_application_scoring": _agent_summary(
            final_scoring,
            "final_application_scoring",
        ),
    }
    canonical_names = tuple(
        summaries[name]["canonical_agent_name"]
        for name in ORDERED_CORE_AGENT_NAMES
    )
    complete_inputs = all(
        (
            bool(prefilter),
            bool(jd_intelligence),
            bool(final_scoring),
            bool(preflight),
            canonical_names == ORDERED_CORE_AGENT_NAMES,
        )
    )
    checks = {
        "relevance_prefilter_supplied": bool(prefilter),
        "jd_intelligence_supplied": bool(jd_intelligence),
        "final_application_scoring_supplied": bool(final_scoring),
        "phase16b_preflight_supplied": bool(preflight),
        "ordered_core_agent_names_match": (
            canonical_names == ORDERED_CORE_AGENT_NAMES
        ),
        "prefilter_relevance_separation_preserved": True,
        "jd_intelligence_evaluation_separation_preserved": True,
        "final_application_scoring_separation_preserved": True,
        "workflow_connection_not_authorized": True,
        "pipeline_stage_not_added": True,
        "mutation_not_authorized": True,
        "scoring_mutation_blocked": True,
        "ranking_mutation_blocked": True,
        "queue_mutation_blocked": True,
        "resume_mutation_blocked": True,
        "application_execution_blocked": True,
        "application_submission_blocked": True,
        "provider_runtime_not_required_for_prefilter": True,
        "provider_runtime_not_invoked_by_readiness": True,
        "runtime_preflight_keeps_canary_execution_blocked": (
            bool(preflight)
            and preflight.get("canary_execution_authorized") is False
        ),
        "runtime_preflight_keeps_adapter_invocation_blocked": (
            bool(preflight)
            and preflight.get("adapter_invocation_authorized") is False
        ),
        "workflow_readiness_context_supplied": bool(context),
    }
    if enabled is not True:
        status = STATUS_SKIPPED
        next_safe_step = "enable_three_core_workflow_readiness_only"
    elif complete_inputs:
        status = STATUS_READY
        next_safe_step = (
            "review_three_core_workflow_readiness_before_shadow_connection"
        )
    else:
        status = STATUS_INCOMPLETE
        next_safe_step = "complete_three_core_workflow_readiness_inputs"
    return {
        "readiness_version": READINESS_VERSION,
        "three_core_workflow_readiness_enabled": enabled is True,
        "readiness_status": status,
        "default_off": True,
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "workflow_readiness_only": True,
        "three_core_agent_only": True,
        "pipeline_not_connected": True,
        "ordered_core_agent_count": len(ORDERED_CORE_AGENT_NAMES),
        "ordered_core_agent_names": list(ORDERED_CORE_AGENT_NAMES),
        "workflow_connection_authorized": False,
        "pipeline_stage_added": False,
        "execution_authorized": False,
        "submission_authorized": False,
        "application_execution_authorized": False,
        "final_scoring_mutation_enabled": False,
        "ranking_mutation_enabled": False,
        "queue_mutation_enabled": False,
        "resume_mutation_enabled": False,
        "mutation_authorized": False,
        "mutation_authorized_agent_count": 0,
        "core_agent_summaries": summaries,
        "phase16b_runtime_preflight_summary": {
            "preflight_supplied": bool(preflight),
            "runtime_preflight_status": _text(
                preflight.get("runtime_preflight_status")
            ),
            "runtime_preflight_only": (
                preflight.get("runtime_preflight_only") is True
            ),
            "canary_execution_authorized": (
                preflight.get("canary_execution_authorized") is True
            ),
            "adapter_invocation_authorized": (
                preflight.get("adapter_invocation_authorized") is True
            ),
            "source_preflight": preflight,
        },
        "three_core_workflow_readiness": {
            "scope": "three_core_agent_workflow_readiness",
            "readiness_checks": checks,
            "readiness_state": {
                "workflow_connection_authorized": False,
                "pipeline_stage_added": False,
                "execution_authorized": False,
                "submission_authorized": False,
                "mutation_authorized": False,
            },
        },
        "decision_boundaries": {
            "prefilter_relevance_is_separate": True,
            "jd_intelligence_evaluation_is_separate": True,
            "final_application_scoring_is_separate": True,
            "prefilter_output_modified": False,
            "jd_evaluation_execution_added": False,
            "final_scoring_behavior_modified": False,
        },
        "forbidden_mutation_and_application_paths": {
            "workflow_connection_allowed": False,
            "pipeline_stage_addition_allowed": False,
            "provider_expansion_allowed": False,
            "tailoring_expansion_allowed": False,
            "critic_expansion_allowed": False,
            "scoring_mutation_allowed": False,
            "ranking_mutation_allowed": False,
            "queue_mutation_allowed": False,
            "resume_mutation_allowed": False,
            "application_execution_allowed": False,
            "application_submission_allowed": False,
        },
        "workflow_readiness_context": context,
        "next_safe_step": next_safe_step,
        "safety_metadata": (
            three_core_agent_workflow_readiness_safety_metadata()
        ),
    }
