from __future__ import annotations

from copy import deepcopy
from typing import Any

from src.agents import agent_recommendation_overlay_readback
from src.agents import agent_recommendation_overlay_readiness
from src.agents import shadow_sidecar


PACKET_READY = "review_packet_ready"
PACKET_PARTIAL = "review_packet_partial_reviewable"
PACKET_NOT_FOUND = "review_packet_not_found"
PACKET_BLOCKED = "review_packet_blocked"
PACKET_FAILED = "review_packet_failed_non_blocking"
PACKET_DISABLED = "review_packet_disabled"


def _plain_dict(value: Any) -> dict[str, Any]:
    return deepcopy(value) if isinstance(value, dict) else {}


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _text_list(value: Any) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    return [
        cleaned
        for item in value
        if (cleaned := _clean_text(item))
    ]


def evaluate_pipeline_agent_review_packet_safety() -> dict[str, bool]:
    return {
        "read_only": True,
        "advisory_only": True,
        "review_packet_only": True,
        "pipeline_agent_review_packet": True,
        "provider_calls_disabled_in_tests": True,
        "requires_live_database": False,
        "did_read_database": False,
        "did_write_database": False,
        "did_mutate_scoring": False,
        "did_change_ranking": False,
        "did_mutate_queue": False,
        "did_create_approval": False,
        "did_mutate_approval": False,
        "did_mutate_resume": False,
        "did_create_execution_request": False,
        "did_create_execution_launch_request": False,
        "did_execute_application": False,
        "did_submit_application": False,
        "pipeline_wiring_added": False,
        "api_route_added": False,
        "ui_action_added": False,
        "auto_apply_enabled": False,
        "mutation_authorized": False,
    }


def _packet_status(readiness_status: str) -> str:
    return {
        agent_recommendation_overlay_readiness.READINESS_READY: PACKET_READY,
        agent_recommendation_overlay_readiness.READINESS_PARTIAL: PACKET_PARTIAL,
        agent_recommendation_overlay_readiness.READINESS_NOT_FOUND: PACKET_NOT_FOUND,
        agent_recommendation_overlay_readiness.READINESS_BLOCKED: PACKET_BLOCKED,
        agent_recommendation_overlay_readiness.READINESS_FAILED: PACKET_FAILED,
        agent_recommendation_overlay_readiness.READINESS_DISABLED: PACKET_DISABLED,
    }.get(readiness_status, PACKET_PARTIAL)


def _first_value(sources: list[dict[str, Any]], key: str) -> Any:
    for source in sources:
        value = source.get(key)
        if value not in (None, "", [], {}):
            return deepcopy(value)
    return None


def _trace_sources(*values: Any) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    pending = [_plain_dict(value) for value in values]
    nested_keys = (
        "existing_trace_context",
        "source_trace_context",
        "trace_capture",
        "trace_persistence",
        "trace_readback",
        "persistence_records",
        "agent_run",
        "metadata",
        "metadata_json",
    )
    while pending:
        source = pending.pop(0)
        if not source:
            continue
        sources.append(source)
        for key in nested_keys:
            nested = _plain_dict(source.get(key))
            if nested:
                pending.append(nested)
    return sources


def _trace_context_summary(*values: Any) -> dict[str, Any]:
    sources = _trace_sources(*values)
    return {
        "run_id": _clean_text(
            _first_value(sources, "run_id")
            or _first_value(sources, "pipeline_run_id")
        ),
        "batch_id": _clean_text(_first_value(sources, "batch_id")),
        "job_id": _clean_text(_first_value(sources, "job_id")),
        "context_id": _clean_text(_first_value(sources, "context_id")),
        "trace_id": _clean_text(_first_value(sources, "trace_id")),
        "stage_name": _clean_text(_first_value(sources, "stage_name")),
        "hook_status": _clean_text(_first_value(sources, "hook_status")),
        "trace_capture_status": _clean_text(
            _first_value(sources, "trace_capture_status")
        ),
        "trace_persistence_status": _clean_text(
            _first_value(sources, "trace_persistence_status")
        ),
        "source_deterministic_stage": _clean_text(
            _first_value(sources, "source_deterministic_stage")
        ),
        "source_deterministic_status": _clean_text(
            _first_value(sources, "source_deterministic_status")
        ),
        "source_deterministic_score": _first_value(
            sources, "source_deterministic_score"
        ),
        "source_deterministic_decision": _clean_text(
            _first_value(sources, "source_deterministic_decision")
        ),
        "source_deterministic_reason_codes": _text_list(
            _first_value(sources, "source_deterministic_reason_codes")
        ),
    }


def _review_focus(readiness_payload: dict[str, Any]) -> list[str]:
    status = _clean_text(readiness_payload.get("readiness_status"))
    focus_by_status = {
        agent_recommendation_overlay_readiness.READINESS_READY: [
            "review_pipeline_generated_overlay_recommendation",
        ],
        agent_recommendation_overlay_readiness.READINESS_PARTIAL: [
            "review_partial_overlay_and_missing_context",
        ],
        agent_recommendation_overlay_readiness.READINESS_NOT_FOUND: [
            "confirm_pipeline_generated_overlay_source",
        ],
        agent_recommendation_overlay_readiness.READINESS_BLOCKED: [
            "review_overlay_generation_blockers",
        ],
        agent_recommendation_overlay_readiness.READINESS_FAILED: [
            "retry_read_only_overlay_readback",
        ],
        agent_recommendation_overlay_readiness.READINESS_DISABLED: [
            "confirm_overlay_auto_generation_configuration",
        ],
    }
    focus = list(focus_by_status.get(status, ["review_overlay_source_context"]))
    for key in ("reason_codes", "blocking_findings", "warning_findings"):
        for finding in _text_list(readiness_payload.get(key)):
            if finding not in focus:
                focus.append(finding)
    return focus


def _recommended_operator_action(readiness_payload: dict[str, Any]) -> str:
    recommended = _clean_text(
        readiness_payload.get("recommended_review_action")
    )
    if recommended:
        return recommended
    return {
        agent_recommendation_overlay_readiness.READINESS_READY: (
            "review_pipeline_generated_overlay"
        ),
        agent_recommendation_overlay_readiness.READINESS_PARTIAL: (
            "review_partial_overlay_context"
        ),
        agent_recommendation_overlay_readiness.READINESS_NOT_FOUND: (
            "inspect_pipeline_generated_overlay_source"
        ),
        agent_recommendation_overlay_readiness.READINESS_BLOCKED: (
            "review_overlay_generation_blockers"
        ),
        agent_recommendation_overlay_readiness.READINESS_FAILED: (
            "retry_read_only_overlay_readback"
        ),
        agent_recommendation_overlay_readiness.READINESS_DISABLED: (
            "confirm_overlay_auto_generation_configuration"
        ),
    }.get(
        _clean_text(readiness_payload.get("readiness_status")),
        "review_overlay_source_context",
    )


def _overlay_source(
    *,
    overlay_payload: Any,
    pipeline_generated_overlay_payload: Any,
    agent_recommendation_overlay_payload: Any,
) -> dict[str, Any]:
    generic = _plain_dict(overlay_payload)
    generated = _plain_dict(pipeline_generated_overlay_payload)
    overlay = _plain_dict(agent_recommendation_overlay_payload)
    if generic.get("readback_status"):
        return generic
    if generic.get("auto_generation_status"):
        return generic
    if generic.get("overlay_status"):
        overlay = generic
    if generated:
        return generated
    if not overlay:
        return {}

    overlay_status = _clean_text(overlay.get("overlay_status"))
    auto_status = {
        "overlay_ready": "overlay_auto_generated",
        "overlay_partial_insufficient_context": "overlay_auto_generated_partial",
        "overlay_not_enabled": "overlay_auto_generation_not_enabled",
        "overlay_blocked_by_kill_switch": (
            "overlay_auto_generation_blocked_by_kill_switch"
        ),
        "overlay_failed_non_blocking": (
            "overlay_auto_generation_failed_non_blocking"
        ),
    }.get(overlay_status, "overlay_auto_generated_partial")
    return {
        "auto_generation_status": auto_status,
        "overlay_generated": bool(overlay),
        "agent_recommendation_overlay": overlay,
    }


def build_pipeline_agent_review_packet_payload(
    *,
    overlay_readback_payload: dict[str, Any] | None = None,
    overlay_payload: dict[str, Any] | None = None,
    pipeline_generated_overlay_payload: dict[str, Any] | None = None,
    agent_recommendation_overlay_payload: dict[str, Any] | None = None,
    hook_payload: dict[str, Any] | None = None,
    trace_context_payload: dict[str, Any] | None = None,
    trace_capture_payload: dict[str, Any] | None = None,
    trace_persistence_payload: dict[str, Any] | None = None,
    trace_readback_payload: dict[str, Any] | None = None,
    readback_source: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a compact operator packet from an existing generated overlay."""

    existing_readback = _plain_dict(overlay_readback_payload)
    direct_overlay_source = _overlay_source(
        overlay_payload=overlay_payload,
        pipeline_generated_overlay_payload=pipeline_generated_overlay_payload,
        agent_recommendation_overlay_payload=agent_recommendation_overlay_payload,
    )
    if direct_overlay_source.get("readback_status"):
        existing_readback = direct_overlay_source
    if existing_readback:
        readback = existing_readback
    else:
        readback = (
            agent_recommendation_overlay_readback.build_pipeline_generated_agent_recommendation_overlay_readback_payload(
                hook_payload=_plain_dict(hook_payload),
                trace_capture_payload=_plain_dict(trace_capture_payload),
                trace_persistence_payload=_plain_dict(trace_persistence_payload),
                trace_readback_payload=_plain_dict(trace_readback_payload),
                readback_source=(
                    _plain_dict(readback_source)
                    or _plain_dict(trace_context_payload)
                    or direct_overlay_source
                ),
            )
        )
    readiness = (
        agent_recommendation_overlay_readiness.build_pipeline_generated_agent_recommendation_overlay_readiness_payload(
            overlay_readback_payload=readback,
        )
    )
    readiness_status = _clean_text(readiness.get("readiness_status"))
    recommended_action = _recommended_operator_action(readiness)
    return {
        "schema_version": shadow_sidecar.SCHEMA_VERSION,
        "packet_status": _packet_status(readiness_status),
        "packet_type": "pipeline_generated_agent_recommendation_overlay_review_packet",
        "read_only": True,
        "advisory_only": True,
        "overlay_found": bool(readback.get("pipeline_generated_overlay_found")),
        "overlay_readiness_status": readiness_status,
        "overlay_reviewability": {
            "reviewable": bool(readiness.get("reviewable")),
            "partial": bool(readiness.get("partial")),
        },
        "auto_generation_status": _clean_text(
            readiness.get("auto_generation_status")
        ),
        "overlay_status": _clean_text(readiness.get("overlay_status")),
        "recommended_operator_action": recommended_action,
        "review_focus": _review_focus(readiness),
        "evaluation_boundaries": {
            "prefilter_relevance": "upstream_deterministic_filter_preserved",
            "shadow_evaluation": "advisory_read_only",
            "final_application_scoring": "unchanged",
        },
        "trace_context_summary": _trace_context_summary(
            hook_payload,
            trace_context_payload,
            trace_capture_payload,
            trace_persistence_payload,
            trace_readback_payload,
            readback_source,
        ),
        "overlay_readback_summary": {
            "readback_status": _clean_text(readback.get("readback_status")),
            "overlay_found": bool(
                readback.get("pipeline_generated_overlay_found")
            ),
            "auto_generation_status": _clean_text(
                readback.get("auto_generation_status")
            ),
            "overlay_status": _clean_text(readback.get("overlay_status")),
            "recommended_review_action": _clean_text(
                readback.get("recommended_review_action")
            ),
        },
        "overlay_readiness_summary": {
            "readiness_status": readiness_status,
            "reviewable": bool(readiness.get("reviewable")),
            "partial": bool(readiness.get("partial")),
            "reason_codes": _text_list(readiness.get("reason_codes")),
            "blocking_findings": _text_list(
                readiness.get("blocking_findings")
            ),
            "warning_findings": _text_list(readiness.get("warning_findings")),
        },
        "provider_calls_disabled_in_tests": True,
        "requires_live_database": False,
        "live_provider_backed_automated_agents": 0,
        "mutation_authorized_agents": 0,
        "safety_metadata": evaluate_pipeline_agent_review_packet_safety(),
    }


def build_pipeline_agent_review_packet_helper_payload(
    **kwargs: Any,
) -> dict[str, Any]:
    return build_pipeline_agent_review_packet_payload(**kwargs)
