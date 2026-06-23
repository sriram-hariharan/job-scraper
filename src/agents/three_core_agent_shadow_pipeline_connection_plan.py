"""Default-off pipeline connection plan for three core shadow agents."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


PLAN_VERSION = "phase-16g-three-core-shadow-pipeline-connection-plan-v1"
STATUS_SKIPPED = (
    "three_core_shadow_pipeline_connection_plan_skipped_default_off"
)
STATUS_READY = (
    "three_core_shadow_pipeline_connection_plan_ready_no_pipeline_change"
)
STATUS_INCOMPLETE = (
    "three_core_shadow_pipeline_connection_plan_incomplete"
)
ORDERED_CORE_AGENT_NAMES = (
    "relevance_prefilter",
    "jd_intelligence",
    "final_application_scoring",
)


def three_core_agent_shadow_pipeline_connection_plan_safety_metadata(
) -> dict[str, bool]:
    return {
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "connection_plan_only": True,
        "pipeline_connection_plan_only": True,
        "three_core_agent_only": True,
        "pipeline_not_connected": True,
        "pipeline_stage_not_added": True,
        "real_agent_execution_not_authorized": True,
        "dry_run_execution_not_authorized": True,
        "provider_runtime_not_invoked": True,
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


def _connection_summary(
    descriptor: dict[str, Any],
    agent_name: str,
) -> dict[str, Any]:
    return {
        "descriptor_supplied": bool(descriptor),
        "agent_name": agent_name,
        "shadow_only": descriptor.get("shadow_only") is True,
        "source_stage": _text(descriptor.get("source_stage")),
        "target_stage": _text(descriptor.get("target_stage")),
        "source_descriptor": descriptor,
    }


def build_three_core_agent_shadow_pipeline_connection_plan(
    *,
    enabled: bool = False,
    dry_run_readback: dict[str, Any] | None = None,
    pipeline_entrypoint_descriptor: dict[str, Any] | None = None,
    prefilter_connection_descriptor: dict[str, Any] | None = None,
    jd_intelligence_connection_descriptor: dict[str, Any] | None = None,
    final_scoring_connection_descriptor: dict[str, Any] | None = None,
    connection_plan_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Describe guarded shadow connections without changing the pipeline."""

    readback = _plain_dict(dry_run_readback)
    entrypoint = _plain_dict(pipeline_entrypoint_descriptor)
    prefilter = _plain_dict(prefilter_connection_descriptor)
    jd_intelligence = _plain_dict(
        jd_intelligence_connection_descriptor
    )
    final_scoring = _plain_dict(
        final_scoring_connection_descriptor
    )
    context = _plain_dict(connection_plan_context)
    readback_names = readback.get("ordered_core_agent_names")
    readback_names = (
        tuple(readback_names)
        if isinstance(readback_names, (list, tuple))
        else ()
    )
    connections = {
        "relevance_prefilter": _connection_summary(
            prefilter,
            "relevance_prefilter",
        ),
        "jd_intelligence": _connection_summary(
            jd_intelligence,
            "jd_intelligence",
        ),
        "final_application_scoring": _connection_summary(
            final_scoring,
            "final_application_scoring",
        ),
    }
    planned_connections_shadow_only = all(
        connections[name]["shadow_only"]
        for name in ORDERED_CORE_AGENT_NAMES
    )
    readback_ready = (
        readback.get("readback_status")
        == "three_core_shadow_dry_run_readback_ready"
    )
    complete = all(
        (
            bool(readback),
            readback_ready,
            readback_names == ORDERED_CORE_AGENT_NAMES,
            bool(entrypoint),
            bool(prefilter),
            bool(jd_intelligence),
            bool(final_scoring),
            planned_connections_shadow_only,
        )
    )
    checks = {
        "dry_run_readback_supplied": bool(readback),
        "dry_run_readback_ready": readback_ready,
        "pipeline_entrypoint_descriptor_supplied": bool(entrypoint),
        "prefilter_connection_descriptor_supplied": bool(prefilter),
        "jd_intelligence_connection_descriptor_supplied": bool(
            jd_intelligence
        ),
        "final_scoring_connection_descriptor_supplied": bool(
            final_scoring
        ),
        "ordered_core_agent_names_match": (
            readback_names == ORDERED_CORE_AGENT_NAMES
        ),
        "planned_connections_are_shadow_only": (
            planned_connections_shadow_only
        ),
        "prefilter_relevance_separation_preserved": True,
        "jd_intelligence_evaluation_separation_preserved": True,
        "final_application_scoring_separation_preserved": True,
        "workflow_connection_not_authorized": True,
        "pipeline_connection_not_authorized": True,
        "pipeline_stage_not_added": True,
        "real_agent_execution_not_authorized": True,
        "dry_run_execution_not_authorized": True,
        "mutation_not_authorized": True,
        "scoring_mutation_blocked": True,
        "ranking_mutation_blocked": True,
        "queue_mutation_blocked": True,
        "resume_mutation_blocked": True,
        "application_execution_blocked": True,
        "application_submission_blocked": True,
        "connection_plan_context_supplied": bool(context),
    }
    if enabled is not True:
        status = STATUS_SKIPPED
        next_safe_step = (
            "enable_three_core_shadow_pipeline_connection_plan_only"
        )
    elif complete:
        status = STATUS_READY
        next_safe_step = (
            "review_three_core_shadow_connection_plan_"
            "before_guarded_pipeline_integration"
        )
    else:
        status = STATUS_INCOMPLETE
        next_safe_step = (
            "complete_three_core_shadow_pipeline_connection_plan_inputs"
        )
    return {
        "plan_version": PLAN_VERSION,
        "three_core_shadow_pipeline_connection_plan_enabled": (
            enabled is True
        ),
        "connection_plan_status": status,
        "default_off": True,
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "connection_plan_only": True,
        "pipeline_connection_plan_only": True,
        "three_core_agent_only": True,
        "pipeline_not_connected": True,
        "pipeline_stage_not_added": True,
        "real_agent_execution_not_authorized": True,
        "dry_run_execution_not_authorized": True,
        "provider_runtime_not_invoked": True,
        "ordered_core_agent_count": len(ORDERED_CORE_AGENT_NAMES),
        "ordered_core_agent_names": list(ORDERED_CORE_AGENT_NAMES),
        "workflow_connection_authorized": False,
        "pipeline_connection_authorized": False,
        "pipeline_stage_added": False,
        "real_agent_execution_authorized": False,
        "dry_run_execution_authorized": False,
        "execution_authorized": False,
        "submission_authorized": False,
        "application_execution_authorized": False,
        "final_scoring_mutation_enabled": False,
        "ranking_mutation_enabled": False,
        "queue_mutation_enabled": False,
        "resume_mutation_enabled": False,
        "mutation_authorized": False,
        "mutation_authorized_agent_count": 0,
        "dry_run_readback_summary": {
            "readback_supplied": bool(readback),
            "readback_status": _text(readback.get("readback_status")),
            "dry_run_readback_only": (
                readback.get("dry_run_readback_only") is True
            ),
            "workflow_connection_authorized": (
                readback.get("workflow_connection_authorized") is True
            ),
            "dry_run_execution_authorized": (
                readback.get("dry_run_execution_authorized") is True
            ),
            "ordered_core_agent_names": list(readback_names),
            "source_readback": readback,
        },
        "pipeline_entrypoint_summary": {
            "entrypoint_supplied": bool(entrypoint),
            "entrypoint_name": _text(
                entrypoint.get("entrypoint_name")
            ),
            "stage_name": _text(entrypoint.get("stage_name")),
            "shadow_only": entrypoint.get("shadow_only") is True,
            "source_entrypoint_descriptor": entrypoint,
        },
        "planned_core_agent_connections": connections,
        "ordered_planned_connections": [
            deepcopy(connections[name])
            for name in ORDERED_CORE_AGENT_NAMES
        ],
        "three_core_shadow_pipeline_connection_plan": {
            "scope": "three_core_agent_shadow_pipeline_connection_plan",
            "connection_plan_checks": checks,
            "connection_plan_state": {
                "workflow_connection_authorized": False,
                "pipeline_connection_authorized": False,
                "pipeline_stage_added": False,
                "real_agent_execution_authorized": False,
                "dry_run_execution_authorized": False,
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
            "pipeline_connection_allowed": False,
            "pipeline_stage_addition_allowed": False,
            "real_agent_execution_allowed": False,
            "dry_run_execution_allowed": False,
            "provider_execution_allowed": False,
            "scoring_mutation_allowed": False,
            "ranking_mutation_allowed": False,
            "queue_mutation_allowed": False,
            "resume_mutation_allowed": False,
            "application_execution_allowed": False,
            "application_submission_allowed": False,
        },
        "connection_plan_context": context,
        "next_safe_step": next_safe_step,
        "safety_metadata": (
            three_core_agent_shadow_pipeline_connection_plan_safety_metadata()
        ),
    }
