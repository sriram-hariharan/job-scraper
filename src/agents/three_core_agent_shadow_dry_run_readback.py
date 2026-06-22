"""Default-off readback for the three-core-agent shadow dry-run packet."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


READBACK_VERSION = "phase-16f-three-core-shadow-dry-run-readback-v1"
STATUS_SKIPPED = (
    "three_core_shadow_dry_run_readback_skipped_default_off"
)
STATUS_READY = "three_core_shadow_dry_run_readback_ready"
STATUS_INCOMPLETE = "three_core_shadow_dry_run_readback_incomplete"
ORDERED_CORE_AGENT_NAMES = (
    "relevance_prefilter",
    "jd_intelligence",
    "final_application_scoring",
)


def three_core_agent_shadow_dry_run_readback_safety_metadata(
) -> dict[str, bool]:
    return {
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "readback_only": True,
        "dry_run_readback_only": True,
        "three_core_agent_only": True,
        "pipeline_not_connected": True,
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


def _trace_rows(packet: dict[str, Any]) -> list[dict[str, Any]]:
    source_rows = packet.get("ordered_core_agent_trace_descriptors")
    source_rows = source_rows if isinstance(source_rows, list) else []
    rows: list[dict[str, Any]] = []
    for expected_name, source_value in zip(
        ORDERED_CORE_AGENT_NAMES,
        source_rows,
    ):
        source = _plain_dict(source_value)
        descriptor = _plain_dict(source.get("source_trace_descriptor"))
        rows.append(
            {
                "agent_name": expected_name,
                "descriptor_available": bool(descriptor),
                "source_agent_name": _text(
                    source.get("source_agent_name")
                    or descriptor.get("agent_name")
                ),
                "agent_version": _text(
                    source.get("agent_version")
                    or descriptor.get("agent_version")
                ),
                "status": _text(
                    source.get("status") or descriptor.get("status")
                ),
                "validation_status": _text(
                    source.get("validation_status")
                ),
                "source_trace_descriptor": descriptor,
            }
        )
    return rows


def build_three_core_agent_shadow_dry_run_readback(
    *,
    enabled: bool = False,
    dry_run_packet: dict[str, Any] | None = None,
    readback_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Normalize an existing dry-run packet without executing anything."""

    packet = _plain_dict(dry_run_packet)
    context = _plain_dict(readback_context)
    packet_names = packet.get("ordered_core_agent_names")
    packet_names = (
        tuple(packet_names)
        if isinstance(packet_names, (list, tuple))
        else ()
    )
    rows = _trace_rows(packet)
    row_names = tuple(row["agent_name"] for row in rows)
    row_by_name = {row["agent_name"]: row for row in rows}
    packet_ready = (
        packet.get("packet_status")
        == "three_core_shadow_dry_run_packet_ready_no_execution"
    )
    complete = all(
        (
            bool(packet),
            packet_ready,
            packet_names == ORDERED_CORE_AGENT_NAMES,
            len(rows) == len(ORDERED_CORE_AGENT_NAMES),
            row_names == ORDERED_CORE_AGENT_NAMES,
            all(row["descriptor_available"] for row in rows),
        )
    )
    checks = {
        "dry_run_packet_supplied": bool(packet),
        "dry_run_packet_ready": packet_ready,
        "ordered_core_agent_names_match": (
            packet_names == ORDERED_CORE_AGENT_NAMES
            and row_names == ORDERED_CORE_AGENT_NAMES
        ),
        "ordered_trace_descriptor_count_is_three": (
            len(rows) == len(ORDERED_CORE_AGENT_NAMES)
        ),
        "prefilter_trace_readback_available": (
            row_by_name.get("relevance_prefilter", {}).get(
                "descriptor_available"
            )
            is True
        ),
        "jd_intelligence_trace_readback_available": (
            row_by_name.get("jd_intelligence", {}).get(
                "descriptor_available"
            )
            is True
        ),
        "final_scoring_trace_readback_available": (
            row_by_name.get("final_application_scoring", {}).get(
                "descriptor_available"
            )
            is True
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
        "readback_context_supplied": bool(context),
    }
    if enabled is not True:
        status = STATUS_SKIPPED
        next_safe_step = (
            "enable_three_core_shadow_dry_run_readback_only"
        )
    elif complete:
        status = STATUS_READY
        next_safe_step = (
            "review_three_core_shadow_dry_run_readback_"
            "before_pipeline_connection_plan"
        )
    else:
        status = STATUS_INCOMPLETE
        next_safe_step = (
            "complete_three_core_shadow_dry_run_readback_inputs"
        )
    return {
        "readback_version": READBACK_VERSION,
        "three_core_shadow_dry_run_readback_enabled": enabled is True,
        "readback_status": status,
        "default_off": True,
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "readback_only": True,
        "dry_run_readback_only": True,
        "three_core_agent_only": True,
        "pipeline_not_connected": True,
        "real_agent_execution_not_authorized": True,
        "dry_run_execution_not_authorized": True,
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
        "dry_run_packet_summary": {
            "packet_supplied": bool(packet),
            "packet_status": _text(packet.get("packet_status")),
            "dry_run_packet_only": (
                packet.get("dry_run_packet_only") is True
            ),
            "dry_run_execution_authorized": (
                packet.get("dry_run_execution_authorized") is True
            ),
            "workflow_connection_authorized": (
                packet.get("workflow_connection_authorized") is True
            ),
            "ordered_core_agent_names": list(packet_names),
            "source_packet": packet,
        },
        "agent_trace_readback_rows": rows,
        "three_core_shadow_dry_run_readback": {
            "scope": "three_core_agent_shadow_dry_run_readback",
            "readback_checks": checks,
            "readback_state": {
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
        "readback_context": context,
        "next_safe_step": next_safe_step,
        "safety_metadata": (
            three_core_agent_shadow_dry_run_readback_safety_metadata()
        ),
    }
