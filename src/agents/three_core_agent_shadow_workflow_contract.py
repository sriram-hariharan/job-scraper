"""Default-off shadow workflow contract for three core ApplyLens agents."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


CONTRACT_VERSION = "phase-16d-three-core-agent-shadow-workflow-v1"
STATUS_SKIPPED = (
    "three_core_shadow_workflow_contract_skipped_default_off"
)
STATUS_READY = (
    "three_core_shadow_workflow_contract_ready_no_pipeline_connection"
)
STATUS_INCOMPLETE = "three_core_shadow_workflow_contract_incomplete"
ORDERED_CORE_AGENT_NAMES = (
    "relevance_prefilter",
    "jd_intelligence",
    "final_application_scoring",
)


def three_core_agent_shadow_workflow_contract_safety_metadata(
) -> dict[str, bool]:
    return {
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "contract_only": True,
        "shadow_workflow_contract_only": True,
        "three_core_agent_only": True,
        "pipeline_not_connected": True,
        "real_agent_execution_not_authorized": True,
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


def _output_summary(
    descriptor: dict[str, Any],
    agent_name: str,
) -> dict[str, Any]:
    return {
        "descriptor_supplied": bool(descriptor),
        "agent_name": agent_name,
        "status": _text(descriptor.get("status")),
        "agent_version": _text(descriptor.get("agent_version")),
        "source_descriptor": descriptor,
    }


def build_three_core_agent_shadow_workflow_contract(
    *,
    enabled: bool = False,
    three_core_readiness: dict[str, Any] | None = None,
    job_context_descriptor: dict[str, Any] | None = None,
    prefilter_output_descriptor: dict[str, Any] | None = None,
    jd_intelligence_output_descriptor: dict[str, Any] | None = None,
    final_scoring_output_descriptor: dict[str, Any] | None = None,
    shadow_workflow_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Describe a future shadow sequence without executing real agents."""

    readiness = _plain_dict(three_core_readiness)
    job_context = _plain_dict(job_context_descriptor)
    prefilter_output = _plain_dict(prefilter_output_descriptor)
    jd_output = _plain_dict(jd_intelligence_output_descriptor)
    final_scoring_output = _plain_dict(
        final_scoring_output_descriptor
    )
    context = _plain_dict(shadow_workflow_context)
    readiness_names = readiness.get("ordered_core_agent_names")
    readiness_names = (
        tuple(readiness_names)
        if isinstance(readiness_names, (list, tuple))
        else ()
    )
    output_summaries = {
        "relevance_prefilter": _output_summary(
            prefilter_output,
            "relevance_prefilter",
        ),
        "jd_intelligence": _output_summary(
            jd_output,
            "jd_intelligence",
        ),
        "final_application_scoring": _output_summary(
            final_scoring_output,
            "final_application_scoring",
        ),
    }
    complete = all(
        (
            bool(readiness),
            readiness.get("readiness_status")
            == (
                "three_core_workflow_readiness_"
                "ready_no_pipeline_connection"
            ),
            readiness_names == ORDERED_CORE_AGENT_NAMES,
            bool(job_context),
            bool(prefilter_output),
            bool(jd_output),
            bool(final_scoring_output),
        )
    )
    checks = {
        "three_core_readiness_supplied": bool(readiness),
        "three_core_readiness_ready": (
            readiness.get("readiness_status")
            == (
                "three_core_workflow_readiness_"
                "ready_no_pipeline_connection"
            )
        ),
        "job_context_descriptor_supplied": bool(job_context),
        "prefilter_output_descriptor_supplied": bool(
            prefilter_output
        ),
        "jd_intelligence_output_descriptor_supplied": bool(
            jd_output
        ),
        "final_scoring_output_descriptor_supplied": bool(
            final_scoring_output
        ),
        "ordered_core_agent_names_match": (
            readiness_names == ORDERED_CORE_AGENT_NAMES
        ),
        "prefilter_relevance_separation_preserved": True,
        "jd_intelligence_evaluation_separation_preserved": True,
        "final_application_scoring_separation_preserved": True,
        "workflow_connection_not_authorized": True,
        "pipeline_stage_not_added": True,
        "real_agent_execution_not_authorized": True,
        "mutation_not_authorized": True,
        "scoring_mutation_blocked": True,
        "ranking_mutation_blocked": True,
        "queue_mutation_blocked": True,
        "resume_mutation_blocked": True,
        "application_execution_blocked": True,
        "application_submission_blocked": True,
        "shadow_workflow_context_supplied": bool(context),
    }
    if enabled is not True:
        status = STATUS_SKIPPED
        next_safe_step = (
            "enable_three_core_shadow_workflow_contract_only"
        )
    elif complete:
        status = STATUS_READY
        next_safe_step = (
            "review_three_core_shadow_contract_before_dry_run"
        )
    else:
        status = STATUS_INCOMPLETE
        next_safe_step = (
            "complete_three_core_shadow_workflow_contract_inputs"
        )
    return {
        "contract_version": CONTRACT_VERSION,
        "three_core_shadow_workflow_contract_enabled": (
            enabled is True
        ),
        "contract_status": status,
        "default_off": True,
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "contract_only": True,
        "shadow_workflow_contract_only": True,
        "three_core_agent_only": True,
        "pipeline_not_connected": True,
        "real_agent_execution_not_authorized": True,
        "ordered_core_agent_count": len(ORDERED_CORE_AGENT_NAMES),
        "ordered_core_agent_names": list(ORDERED_CORE_AGENT_NAMES),
        "workflow_connection_authorized": False,
        "pipeline_stage_added": False,
        "real_agent_execution_authorized": False,
        "execution_authorized": False,
        "submission_authorized": False,
        "application_execution_authorized": False,
        "final_scoring_mutation_enabled": False,
        "ranking_mutation_enabled": False,
        "queue_mutation_enabled": False,
        "resume_mutation_enabled": False,
        "mutation_authorized": False,
        "mutation_authorized_agent_count": 0,
        "three_core_readiness_summary": {
            "readiness_supplied": bool(readiness),
            "readiness_status": _text(
                readiness.get("readiness_status")
            ),
            "workflow_readiness_only": (
                readiness.get("workflow_readiness_only") is True
            ),
            "workflow_connection_authorized": (
                readiness.get("workflow_connection_authorized") is True
            ),
            "ordered_core_agent_names": list(readiness_names),
            "source_readiness": readiness,
        },
        "job_context_summary": {
            "job_context_supplied": bool(job_context),
            "job_id": _text(job_context.get("job_id")),
            "run_id": _text(job_context.get("run_id")),
            "source_job_context": job_context,
        },
        "planned_core_agent_outputs": output_summaries,
        "ordered_shadow_output_descriptors": [
            deepcopy(output_summaries[name])
            for name in ORDERED_CORE_AGENT_NAMES
        ],
        "three_core_shadow_workflow_contract": {
            "scope": "three_core_agent_shadow_workflow_contract",
            "contract_checks": checks,
            "contract_state": {
                "workflow_connection_authorized": False,
                "pipeline_stage_added": False,
                "real_agent_execution_authorized": False,
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
            "real_agent_execution_allowed": False,
            "provider_execution_allowed": False,
            "scoring_mutation_allowed": False,
            "ranking_mutation_allowed": False,
            "queue_mutation_allowed": False,
            "resume_mutation_allowed": False,
            "application_execution_allowed": False,
            "application_submission_allowed": False,
        },
        "shadow_workflow_context": context,
        "next_safe_step": next_safe_step,
        "safety_metadata": (
            three_core_agent_shadow_workflow_contract_safety_metadata()
        ),
    }
