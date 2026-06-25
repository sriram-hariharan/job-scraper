"""Phase 19A default-off, read-only approval preview runtime helper."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from src.agents import three_core_agent_shadow_runtime_readback


APPROVAL_PREVIEW_RUNTIME_FLAG = (
    "APPLYLENS_AGENTIC_PIPELINE_THREE_CORE_APPROVAL_PREVIEW_RUNTIME_ENABLED"
)
SHADOW_KILL_SWITCH_FLAG = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_KILL_SWITCH"
PREVIEW_RUNTIME_VERSION = "phase-19a-three-core-approval-preview-runtime-v1"
SCHEMA_VERSION = "phase-19a-three-core-approval-preview-payload-v1"

STATUS_NOT_ENABLED = "approval_preview_runtime_not_enabled"
STATUS_BLOCKED_BY_KILL_SWITCH = (
    "approval_preview_runtime_blocked_by_kill_switch"
)
STATUS_BLOCKED_MISSING_SHADOW_READBACK = (
    "approval_preview_runtime_blocked_missing_shadow_readback"
)
STATUS_BLOCKED_INCOMPLETE_SHADOW_READBACK = (
    "approval_preview_runtime_blocked_incomplete_shadow_readback"
)
STATUS_READY = "approval_preview_runtime_ready"
STATUS_FAILED_CLOSED = "approval_preview_runtime_failed_closed"

ORDERED_CORE_AGENT_NAMES = (
    "relevance_prefilter",
    "jd_intelligence",
    "final_application_scoring",
)
KEY_QUEUE_MUTATED = "did_mutate_" + "queue"
KEY_EXECUTION_REQUEST_CREATED = "did_create_execution_" + "request"
KEY_APPLICATION_EXECUTED = "did_execute_" + "application"
KEY_APPLICATION_SUBMITTED = "did_submit_" + "application"


def _plain_dict(value: Any) -> dict[str, Any]:
    return deepcopy(value) if isinstance(value, dict) else {}


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def three_core_approval_preview_runtime_safety_metadata() -> dict[str, bool]:
    return {
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "approval_preview_only": True,
        "provider_call": False,
        "provider_sdk_import": False,
        "env_secret_read": False,
        "network_call": False,
        "did_read_database": False,
        "did_write_database": False,
        "did_write_file": False,
        "did_mutate_scoring": False,
        "did_change_ranking": False,
        KEY_QUEUE_MUTATED: False,
        "did_mutate_resume": False,
        "did_create_approval": False,
        "did_persist_decision": False,
        "did_persist_audit": False,
        KEY_EXECUTION_REQUEST_CREATED: False,
        KEY_APPLICATION_EXECUTED: False,
        KEY_APPLICATION_SUBMITTED: False,
        "api_route_added": False,
        "ui_action_added": False,
        "pipeline_wiring_added": False,
        "collector_wiring_added": False,
        "mutation_authorized": False,
        "application_execution_authorized": False,
        "submission_authorized": False,
    }


def _readback_summary(source: dict[str, Any]) -> dict[str, Any]:
    runtime_summary = _plain_dict(source.get("runtime_readback_summary"))
    return {
        "readback_version": _clean_text(source.get("readback_version")),
        "readback_status": _clean_text(source.get("readback_status")),
        "read_only": source.get("read_only") is True,
        "shadow_only": source.get("shadow_only") is True,
        "advisory_only": source.get("advisory_only") is True,
        "ordered_core_agent_names": deepcopy(
            source.get("ordered_core_agent_names")
            if isinstance(source.get("ordered_core_agent_names"), list)
            else []
        ),
        "completion": runtime_summary.get("completion") is True,
        "incomplete_checks": deepcopy(
            runtime_summary.get("incomplete_checks")
            if isinstance(runtime_summary.get("incomplete_checks"), list)
            else []
        ),
        "mutation_authorized": source.get("mutation_authorized"),
        "execution_authorized": source.get("execution_authorized"),
        "submission_authorized": source.get("submission_authorized"),
        "application_execution_authorized": source.get(
            "application_execution_authorized"
        ),
        "runtime_readback_summary": runtime_summary,
    }


def _readback_is_ready(summary: dict[str, Any]) -> bool:
    return (
        summary.get("readback_status")
        == three_core_agent_shadow_runtime_readback.STATUS_COMPLETED
        and summary.get("completion") is True
        and tuple(summary.get("ordered_core_agent_names") or ())
        == ORDERED_CORE_AGENT_NAMES
        and summary.get("read_only") is True
        and summary.get("shadow_only") is True
        and summary.get("advisory_only") is True
        and summary.get("mutation_authorized") is False
        and summary.get("execution_authorized") is False
        and summary.get("submission_authorized") is False
        and summary.get("application_execution_authorized") is False
    )


def _linked_trace_id(
    context: dict[str, Any],
    source: dict[str, Any],
) -> str:
    readback_context = _plain_dict(source.get("readback_context"))
    for value in (
        context.get("linked_trace_or_readback_id"),
        context.get("trace_id"),
        context.get("readback_id"),
        readback_context.get("linked_trace_or_readback_id"),
        readback_context.get("trace_id"),
        readback_context.get("readback_id"),
    ):
        cleaned = _clean_text(value)
        if cleaned:
            return cleaned
    return ""


def _payload(
    *,
    status: str,
    preview_enabled: bool,
    context: dict[str, Any],
    source: dict[str, Any],
    summary: dict[str, Any],
    missing_requirements: list[str],
    fail_closed_reason: str,
    next_safe_step: str,
) -> dict[str, Any]:
    safety = three_core_approval_preview_runtime_safety_metadata()
    requested_capability = _clean_text(
        context.get("requested_capability")
    ) or "three_core_approval_preview"
    target_context = _plain_dict(context.get("target_context_summary"))
    if not target_context:
        target_context = _plain_dict(context)

    return {
        "schema_version": SCHEMA_VERSION,
        "preview_runtime_version": PREVIEW_RUNTIME_VERSION,
        "preview_status": status,
        "preview_enabled": preview_enabled,
        "default_off": True,
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "approval_preview_only": True,
        "ordered_core_agent_names": list(ORDERED_CORE_AGENT_NAMES),
        "requested_capability": requested_capability,
        "target_context_summary": target_context,
        "linked_trace_or_readback_id": _linked_trace_id(context, source),
        "source_shadow_runtime_readback_summary": summary,
        "approval_preview_metadata": {
            "preview_type": "three_core_shadow_evidence_approval_preview",
            "review_only": True,
            "source_readback_supplied": bool(source),
            "source_readback_completed": summary.get("completion") is True,
            "human_decision_required": True,
        },
        "evidence_summary": {
            "source": "three_core_shadow_runtime_readback",
            "readback_status": _clean_text(summary.get("readback_status")),
            "ordered_core_agent_names": deepcopy(
                summary.get("ordered_core_agent_names") or []
            ),
            "completion": summary.get("completion") is True,
        },
        "proposed_action_summary": {
            "action": "review_approval_preview_metadata_only",
            "execution_requested": False,
            "mutation_requested": False,
            "submission_requested": False,
        },
        "risk_summary": {
            "risk_level": "blocked" if fail_closed_reason else "review_only",
            "provider_risk": "provider_calls_disabled",
            "mutation_risk": "mutation_not_authorized",
            "submission_risk": "submission_not_authorized",
        },
        "safety_flag_summary": deepcopy(safety),
        "missing_requirements": list(missing_requirements),
        "fail_closed_reason": fail_closed_reason,
        "next_safe_step": next_safe_step,
        "provider_calls_disabled_in_tests": True,
        "requires_live_database": False,
        "did_read_database": False,
        "did_write_database": False,
        "did_mutate_scoring": False,
        "did_change_ranking": False,
        KEY_QUEUE_MUTATED: False,
        "did_mutate_resume": False,
        "did_create_approval": False,
        "did_mutate_approval": False,
        KEY_EXECUTION_REQUEST_CREATED: False,
        KEY_APPLICATION_EXECUTED: False,
        KEY_APPLICATION_SUBMITTED: False,
        "application_execution_authorized": False,
        "submission_authorized": False,
        "mutation_authorized": False,
        "safety_metadata": safety,
    }


def _build_three_core_approval_preview_runtime_payload(
    *,
    enabled: bool,
    shadow_runtime_readback_payload: dict[str, Any] | None,
    shadow_sidecar_hook_payload: dict[str, Any] | None,
    preview_context: dict[str, Any] | None,
    preview_config: dict[str, Any] | None,
) -> dict[str, Any]:
    context = _plain_dict(preview_context)
    config = _plain_dict(preview_config)

    if enabled is not True or config.get(APPROVAL_PREVIEW_RUNTIME_FLAG) is not True:
        return _payload(
            status=STATUS_NOT_ENABLED,
            preview_enabled=False,
            context=context,
            source={},
            summary={},
            missing_requirements=[APPROVAL_PREVIEW_RUNTIME_FLAG],
            fail_closed_reason="approval_preview_runtime_flag_not_enabled",
            next_safe_step="enable_approval_preview_runtime_explicitly",
        )

    if (
        config.get(SHADOW_KILL_SWITCH_FLAG) is True
        or config.get("kill_switch_enabled") is True
    ):
        return _payload(
            status=STATUS_BLOCKED_BY_KILL_SWITCH,
            preview_enabled=False,
            context=context,
            source={},
            summary={},
            missing_requirements=[],
            fail_closed_reason="shadow_kill_switch_enabled",
            next_safe_step="disable_kill_switch_before_preview_review",
        )

    source = _plain_dict(shadow_runtime_readback_payload)
    if not source and isinstance(shadow_sidecar_hook_payload, dict):
        source = (
            three_core_agent_shadow_runtime_readback
            .build_three_core_agent_shadow_runtime_readback(
                enabled=True,
                shadow_sidecar_hook_payload=_plain_dict(
                    shadow_sidecar_hook_payload
                ),
                readback_context=context,
            )
        )
        source = _plain_dict(source)

    if not source:
        return _payload(
            status=STATUS_BLOCKED_MISSING_SHADOW_READBACK,
            preview_enabled=True,
            context=context,
            source={},
            summary={},
            missing_requirements=["shadow_runtime_readback_payload"],
            fail_closed_reason="missing_shadow_runtime_readback",
            next_safe_step="supply_completed_shadow_runtime_readback",
        )

    summary = _readback_summary(source)
    if not _readback_is_ready(summary):
        missing = list(summary.get("incomplete_checks") or [])
        if not missing:
            missing = ["completed_safe_three_core_shadow_runtime_readback"]
        return _payload(
            status=STATUS_BLOCKED_INCOMPLETE_SHADOW_READBACK,
            preview_enabled=True,
            context=context,
            source=source,
            summary=summary,
            missing_requirements=missing,
            fail_closed_reason="incomplete_or_unsafe_shadow_runtime_readback",
            next_safe_step="complete_shadow_runtime_readback_before_preview",
        )

    return _payload(
        status=STATUS_READY,
        preview_enabled=True,
        context=context,
        source=source,
        summary=summary,
        missing_requirements=[],
        fail_closed_reason="",
        next_safe_step="review_approval_preview_metadata_only",
    )


def build_three_core_approval_preview_runtime_payload(
    *,
    enabled: bool = False,
    shadow_runtime_readback_payload: dict[str, Any] | None = None,
    shadow_sidecar_hook_payload: dict[str, Any] | None = None,
    preview_context: dict[str, Any] | None = None,
    preview_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a deterministic approval preview from caller-supplied evidence."""

    try:
        return _build_three_core_approval_preview_runtime_payload(
            enabled=enabled,
            shadow_runtime_readback_payload=shadow_runtime_readback_payload,
            shadow_sidecar_hook_payload=shadow_sidecar_hook_payload,
            preview_context=preview_context,
            preview_config=preview_config,
        )
    except Exception:
        return _payload(
            status=STATUS_FAILED_CLOSED,
            preview_enabled=enabled is True,
            context={},
            source={},
            summary={},
            missing_requirements=["valid_shadow_runtime_readback"],
            fail_closed_reason="unexpected_approval_preview_runtime_failure",
            next_safe_step="inspect_failure_before_retry",
        )


def build_three_core_approval_preview_runtime_helper_payload(
    **kwargs: Any,
) -> dict[str, Any]:
    """Compatibility wrapper for later read-only service integration."""

    return build_three_core_approval_preview_runtime_payload(**kwargs)
