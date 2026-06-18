from __future__ import annotations

from copy import deepcopy
from typing import Any

from src.agents import agent_recommendation_overlay_readback
from src.agents import shadow_sidecar


READINESS_READY = "overlay_ready"
READINESS_PARTIAL = "overlay_partial_reviewable"
READINESS_NOT_FOUND = "overlay_not_found"
READINESS_BLOCKED = "overlay_blocked"
READINESS_FAILED = "overlay_failed_non_blocking"
READINESS_DISABLED = "overlay_disabled"


def _plain_dict(value: Any) -> dict[str, Any]:
    return deepcopy(value) if isinstance(value, dict) else {}


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def evaluate_pipeline_generated_overlay_readiness_safety() -> dict[str, bool]:
    return {
        "read_only": True,
        "readiness_summary_only": True,
        "advisory_only": True,
        "pipeline_generated_overlay_readiness_summary": True,
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
        "auto_apply_enabled": False,
        "mutation_authorized": False,
    }


def _classify_readiness(
    *,
    readback_status: str,
    auto_generation_status: str,
    overlay_status: str,
) -> tuple[str, bool, bool, list[str], list[str], list[str]]:
    readback = _clean_text(readback_status)
    auto_status = _clean_text(auto_generation_status)
    overlay = _clean_text(overlay_status)

    if (
        readback
        == agent_recommendation_overlay_readback.STATUS_FAILED_NON_BLOCKING
        or auto_status == "overlay_auto_generation_failed_non_blocking"
        or overlay == "overlay_failed_non_blocking"
    ):
        return (
            READINESS_FAILED,
            False,
            False,
            ["overlay_readback_or_generation_failed_non_blocking"],
            [],
            ["retry_read_only_overlay_readback"],
        )

    if auto_status == "overlay_auto_generation_blocked_by_kill_switch" or overlay in {
        "overlay_blocked_by_kill_switch",
        "overlay_blocked_missing_deterministic_context",
    }:
        return (
            READINESS_BLOCKED,
            False,
            False,
            ["overlay_generation_blocked"],
            ["pipeline_generated_overlay_blocked"],
            [],
        )

    if auto_status == "overlay_auto_generation_not_enabled" or overlay == "overlay_not_enabled":
        return (
            READINESS_DISABLED,
            False,
            False,
            ["overlay_auto_generation_not_enabled"],
            [],
            [],
        )

    if (
        readback == agent_recommendation_overlay_readback.STATUS_NOT_FOUND
        or not auto_status
    ):
        return (
            READINESS_NOT_FOUND,
            False,
            False,
            ["pipeline_generated_overlay_not_found"],
            [],
            [],
        )

    if (
        auto_status == "overlay_auto_generated_partial"
        or overlay == "overlay_partial_insufficient_context"
    ):
        return (
            READINESS_PARTIAL,
            True,
            True,
            ["partial_overlay_available_for_operator_review"],
            [],
            ["overlay_context_incomplete"],
        )

    if auto_status == "overlay_auto_generated" and overlay == "overlay_ready":
        return (
            READINESS_READY,
            True,
            False,
            ["pipeline_generated_overlay_ready_for_operator_review"],
            [],
            [],
        )

    return (
        READINESS_PARTIAL,
        True,
        True,
        ["overlay_available_with_unclassified_context"],
        [],
        ["review_overlay_source_context"],
    )


def build_pipeline_generated_agent_recommendation_overlay_readiness_payload(
    *,
    overlay_readback_payload: dict[str, Any] | None = None,
    hook_payload: dict[str, Any] | None = None,
    trace_capture_payload: dict[str, Any] | None = None,
    trace_persistence_payload: dict[str, Any] | None = None,
    trace_readback_payload: dict[str, Any] | None = None,
    readback_source: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Summarize an existing pipeline-generated overlay without regenerating it."""

    existing_readback = _plain_dict(overlay_readback_payload)
    if existing_readback:
        normalized_readback = existing_readback
    else:
        normalized_readback = (
            agent_recommendation_overlay_readback.build_pipeline_generated_agent_recommendation_overlay_readback_payload(
                hook_payload=_plain_dict(hook_payload),
                trace_capture_payload=_plain_dict(trace_capture_payload),
                trace_persistence_payload=_plain_dict(trace_persistence_payload),
                trace_readback_payload=_plain_dict(trace_readback_payload),
                readback_source=_plain_dict(readback_source),
            )
        )

    generated_context = _plain_dict(
        normalized_readback.get("pipeline_generated_overlay")
    )
    overlay = _plain_dict(
        normalized_readback.get("agent_recommendation_overlay")
    )
    readback_status = _clean_text(normalized_readback.get("readback_status"))
    auto_generation_status = _clean_text(
        normalized_readback.get("auto_generation_status")
        or generated_context.get("auto_generation_status")
    )
    overlay_status = _clean_text(
        normalized_readback.get("overlay_status") or overlay.get("overlay_status")
    )
    (
        readiness_status,
        reviewable,
        partial,
        reason_codes,
        blocking_findings,
        warning_findings,
    ) = _classify_readiness(
        readback_status=readback_status,
        auto_generation_status=auto_generation_status,
        overlay_status=overlay_status,
    )

    recommended_action = _clean_text(
        normalized_readback.get("recommended_review_action")
        or overlay.get("recommended_review_action")
    )
    return {
        "schema_version": shadow_sidecar.SCHEMA_VERSION,
        "readiness_status": readiness_status,
        "reviewable": reviewable,
        "partial": partial,
        "source_readback_status": readback_status,
        "auto_generation_status": auto_generation_status,
        "overlay_status": overlay_status,
        "recommended_review_action": recommended_action,
        "reason_codes": reason_codes,
        "blocking_findings": blocking_findings,
        "warning_findings": warning_findings,
        "operator_summary": {
            "summary_type": "pipeline_generated_agent_recommendation_overlay_readiness",
            "readiness_status": readiness_status,
            "reviewable": reviewable,
            "partial": partial,
            "recommended_review_action": recommended_action,
            "human_review_required": True,
            "advisory_only": True,
        },
        "source_overlay_summary": {
            "overlay_found": bool(
                normalized_readback.get("pipeline_generated_overlay_found")
            ),
            "auto_generation_status": auto_generation_status,
            "overlay_status": overlay_status,
            "recommended_review_action": recommended_action,
        },
        "provider_calls_disabled_in_tests": True,
        "requires_live_database": False,
        "live_provider_backed_automated_agents": 0,
        "mutation_authorized_agents": 0,
        "safety_metadata": evaluate_pipeline_generated_overlay_readiness_safety(),
    }


def build_pipeline_generated_agent_recommendation_overlay_readiness_helper_payload(
    **kwargs: Any,
) -> dict[str, Any]:
    return build_pipeline_generated_agent_recommendation_overlay_readiness_payload(
        **kwargs
    )
