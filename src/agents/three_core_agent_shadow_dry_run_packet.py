"""Default-off dry-run packet for three core ApplyLens shadow agents."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


PACKET_VERSION = "phase-16e-three-core-agent-shadow-dry-run-packet-v1"
STATUS_SKIPPED = (
    "three_core_shadow_dry_run_packet_skipped_default_off"
)
STATUS_READY = "three_core_shadow_dry_run_packet_ready_no_execution"
STATUS_INCOMPLETE = "three_core_shadow_dry_run_packet_incomplete"
ORDERED_CORE_AGENT_NAMES = (
    "relevance_prefilter",
    "jd_intelligence",
    "final_application_scoring",
)


def three_core_agent_shadow_dry_run_packet_safety_metadata(
) -> dict[str, bool]:
    return {
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "dry_run_packet_only": True,
        "three_core_agent_only": True,
        "pipeline_not_connected": True,
        "real_agent_execution_not_authorized": True,
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


def _trace_summary(
    descriptor: dict[str, Any],
    agent_name: str,
) -> dict[str, Any]:
    validation = _plain_dict(descriptor.get("validation_json"))
    return {
        "descriptor_supplied": bool(descriptor),
        "agent_name": agent_name,
        "source_agent_name": _text(descriptor.get("agent_name")),
        "agent_version": _text(descriptor.get("agent_version")),
        "status": _text(descriptor.get("status")),
        "validation_status": (
            "valid"
            if validation.get("is_valid") is True
            else (
                "invalid"
                if validation.get("is_valid") is False
                else ""
            )
        ),
        "source_trace_descriptor": descriptor,
    }


def build_three_core_agent_shadow_dry_run_packet(
    *,
    enabled: bool = False,
    shadow_workflow_contract: dict[str, Any] | None = None,
    job_context_descriptor: dict[str, Any] | None = None,
    prefilter_trace_descriptor: dict[str, Any] | None = None,
    jd_intelligence_trace_descriptor: dict[str, Any] | None = None,
    final_scoring_trace_descriptor: dict[str, Any] | None = None,
    dry_run_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Package supplied shadow traces without running a dry run."""

    contract = _plain_dict(shadow_workflow_contract)
    job_context = _plain_dict(job_context_descriptor)
    prefilter_trace = _plain_dict(prefilter_trace_descriptor)
    jd_trace = _plain_dict(jd_intelligence_trace_descriptor)
    final_scoring_trace = _plain_dict(
        final_scoring_trace_descriptor
    )
    context = _plain_dict(dry_run_context)
    contract_names = contract.get("ordered_core_agent_names")
    contract_names = (
        tuple(contract_names)
        if isinstance(contract_names, (list, tuple))
        else ()
    )
    trace_summaries = {
        "relevance_prefilter": _trace_summary(
            prefilter_trace,
            "relevance_prefilter",
        ),
        "jd_intelligence": _trace_summary(
            jd_trace,
            "jd_intelligence",
        ),
        "final_application_scoring": _trace_summary(
            final_scoring_trace,
            "final_application_scoring",
        ),
    }
    contract_ready = (
        contract.get("contract_status")
        == (
            "three_core_shadow_workflow_contract_"
            "ready_no_pipeline_connection"
        )
    )
    complete = all(
        (
            bool(contract),
            contract_ready,
            contract_names == ORDERED_CORE_AGENT_NAMES,
            bool(job_context),
            bool(prefilter_trace),
            bool(jd_trace),
            bool(final_scoring_trace),
        )
    )
    checks = {
        "shadow_workflow_contract_supplied": bool(contract),
        "shadow_workflow_contract_ready": contract_ready,
        "job_context_descriptor_supplied": bool(job_context),
        "prefilter_trace_descriptor_supplied": bool(prefilter_trace),
        "jd_intelligence_trace_descriptor_supplied": bool(jd_trace),
        "final_scoring_trace_descriptor_supplied": bool(
            final_scoring_trace
        ),
        "ordered_core_agent_names_match": (
            contract_names == ORDERED_CORE_AGENT_NAMES
        ),
        "prefilter_relevance_separation_preserved": True,
        "jd_intelligence_evaluation_separation_preserved": True,
        "final_application_scoring_separation_preserved": True,
        "workflow_connection_not_authorized": True,
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
        "dry_run_context_supplied": bool(context),
    }
    if enabled is not True:
        status = STATUS_SKIPPED
        next_safe_step = (
            "enable_three_core_shadow_dry_run_packet_only"
        )
    elif complete:
        status = STATUS_READY
        next_safe_step = (
            "review_three_core_shadow_dry_run_packet_before_readback"
        )
    else:
        status = STATUS_INCOMPLETE
        next_safe_step = (
            "complete_three_core_shadow_dry_run_packet_inputs"
        )
    return {
        "packet_version": PACKET_VERSION,
        "three_core_shadow_dry_run_packet_enabled": enabled is True,
        "packet_status": status,
        "default_off": True,
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "dry_run_packet_only": True,
        "three_core_agent_only": True,
        "pipeline_not_connected": True,
        "real_agent_execution_not_authorized": True,
        "provider_runtime_not_invoked": True,
        "ordered_core_agent_count": len(ORDERED_CORE_AGENT_NAMES),
        "ordered_core_agent_names": list(ORDERED_CORE_AGENT_NAMES),
        "workflow_connection_authorized": False,
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
        "shadow_workflow_contract_summary": {
            "contract_supplied": bool(contract),
            "contract_status": _text(contract.get("contract_status")),
            "shadow_workflow_contract_only": (
                contract.get("shadow_workflow_contract_only") is True
            ),
            "workflow_connection_authorized": (
                contract.get("workflow_connection_authorized") is True
            ),
            "real_agent_execution_authorized": (
                contract.get("real_agent_execution_authorized") is True
            ),
            "ordered_core_agent_names": list(contract_names),
            "source_contract": contract,
        },
        "job_context_summary": {
            "job_context_supplied": bool(job_context),
            "job_id": _text(job_context.get("job_id")),
            "run_id": _text(job_context.get("run_id")),
            "source_job_context": job_context,
        },
        "core_agent_trace_summaries": trace_summaries,
        "ordered_core_agent_trace_descriptors": [
            deepcopy(trace_summaries[name])
            for name in ORDERED_CORE_AGENT_NAMES
        ],
        "three_core_shadow_dry_run_packet": {
            "scope": "three_core_agent_shadow_dry_run_packet",
            "packet_checks": checks,
            "packet_state": {
                "workflow_connection_authorized": False,
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
        "dry_run_context": context,
        "next_safe_step": next_safe_step,
        "safety_metadata": (
            three_core_agent_shadow_dry_run_packet_safety_metadata()
        ),
    }
