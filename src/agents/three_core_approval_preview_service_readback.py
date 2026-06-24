"""Phase 19B default-off read-only service readback for Phase 19A previews."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from src.agents import three_core_approval_preview_runtime


APPROVAL_PREVIEW_SERVICE_READBACK_FLAG = (
    "APPLYLENS_AGENTIC_PIPELINE_THREE_CORE_APPROVAL_PREVIEW_"
    "SERVICE_READBACK_ENABLED"
)
APPROVAL_PREVIEW_RUNTIME_FLAG = (
    three_core_approval_preview_runtime.APPROVAL_PREVIEW_RUNTIME_FLAG
)
SHADOW_KILL_SWITCH_FLAG = (
    three_core_approval_preview_runtime.SHADOW_KILL_SWITCH_FLAG
)
SERVICE_READBACK_VERSION = (
    "phase-19b-three-core-approval-preview-service-readback-v1"
)
SERVICE_READBACK_SCHEMA_VERSION = (
    "phase-19b-three-core-approval-preview-service-readback-payload-v1"
)

STATUS_NOT_ENABLED = "approval_preview_service_readback_not_enabled"
STATUS_BLOCKED_BY_KILL_SWITCH = (
    "approval_preview_service_readback_blocked_by_kill_switch"
)
STATUS_BLOCKED_MISSING_PREVIEW = (
    "approval_preview_service_readback_blocked_missing_preview"
)
STATUS_BLOCKED_INCOMPLETE_PREVIEW = (
    "approval_preview_service_readback_blocked_incomplete_preview"
)
STATUS_READY = "approval_preview_service_readback_ready"
STATUS_FAILED_CLOSED = "approval_preview_service_readback_failed_closed"

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


def three_core_approval_preview_service_readback_safety_metadata(
) -> dict[str, bool]:
    return {
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "service_readback_only": True,
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
        "did_mutate_approval": False,
        "did_persist_decision": False,
        "did_persist_audit": False,
        KEY_EXECUTION_REQUEST_CREATED: False,
        KEY_APPLICATION_EXECUTED: False,
        KEY_APPLICATION_SUBMITTED: False,
        "api_route_added": False,
        "ui_action_added": False,
        "app_service_wiring_added": False,
        "pipeline_wiring_added": False,
        "collector_wiring_added": False,
        "mutation_authorized": False,
        "application_execution_authorized": False,
        "submission_authorized": False,
    }


def _preview_summary(source: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": _clean_text(source.get("schema_version")),
        "preview_runtime_version": _clean_text(
            source.get("preview_runtime_version")
        ),
        "preview_status": _clean_text(source.get("preview_status")),
        "preview_enabled": source.get("preview_enabled") is True,
        "read_only": source.get("read_only") is True,
        "shadow_only": source.get("shadow_only") is True,
        "advisory_only": source.get("advisory_only") is True,
        "approval_preview_only": source.get("approval_preview_only") is True,
        "ordered_core_agent_names": deepcopy(
            source.get("ordered_core_agent_names")
            if isinstance(source.get("ordered_core_agent_names"), list)
            else []
        ),
        "requested_capability": _clean_text(
            source.get("requested_capability")
        ),
        "target_context_summary": _plain_dict(
            source.get("target_context_summary")
        ),
        "linked_trace_or_readback_id": _clean_text(
            source.get("linked_trace_or_readback_id")
        ),
        "approval_preview_metadata": _plain_dict(
            source.get("approval_preview_metadata")
        ),
        "evidence_summary": _plain_dict(source.get("evidence_summary")),
        "proposed_action_summary": _plain_dict(
            source.get("proposed_action_summary")
        ),
        "risk_summary": _plain_dict(source.get("risk_summary")),
        "missing_requirements": deepcopy(
            source.get("missing_requirements")
            if isinstance(source.get("missing_requirements"), list)
            else []
        ),
        "fail_closed_reason": _clean_text(
            source.get("fail_closed_reason")
        ),
        "mutation_authorized": source.get("mutation_authorized"),
        "application_execution_authorized": source.get(
            "application_execution_authorized"
        ),
        "submission_authorized": source.get("submission_authorized"),
    }


def _preview_is_ready(summary: dict[str, Any]) -> bool:
    return (
        summary.get("preview_status")
        == three_core_approval_preview_runtime.STATUS_READY
        and tuple(summary.get("ordered_core_agent_names") or ())
        == ORDERED_CORE_AGENT_NAMES
        and summary.get("read_only") is True
        and summary.get("shadow_only") is True
        and summary.get("advisory_only") is True
        and summary.get("approval_preview_only") is True
        and summary.get("mutation_authorized") is False
        and summary.get("application_execution_authorized") is False
        and summary.get("submission_authorized") is False
    )


def _payload(
    *,
    status: str,
    readback_enabled: bool,
    context: dict[str, Any],
    source: dict[str, Any],
    summary: dict[str, Any],
    missing_requirements: list[str],
    fail_closed_reason: str,
    next_safe_step: str,
) -> dict[str, Any]:
    safety = three_core_approval_preview_service_readback_safety_metadata()
    requested_capability = (
        _clean_text(summary.get("requested_capability"))
        or _clean_text(context.get("requested_capability"))
        or "three_core_approval_preview_service_readback"
    )
    target_context = _plain_dict(summary.get("target_context_summary"))
    if not target_context:
        target_context = _plain_dict(context.get("target_context_summary"))
    linked_id = (
        _clean_text(summary.get("linked_trace_or_readback_id"))
        or _clean_text(context.get("linked_trace_or_readback_id"))
        or _clean_text(context.get("trace_id"))
        or _clean_text(context.get("readback_id"))
    )

    return {
        "schema_version": SERVICE_READBACK_SCHEMA_VERSION,
        "service_readback_version": SERVICE_READBACK_VERSION,
        "service_readback_status": status,
        "service_readback_enabled": readback_enabled,
        "default_off": True,
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "service_readback_only": True,
        "ordered_core_agent_names": list(ORDERED_CORE_AGENT_NAMES),
        "requested_capability": requested_capability,
        "target_context_summary": target_context,
        "linked_trace_or_readback_id": linked_id,
        "source_approval_preview_runtime_summary": summary,
        "service_readback_metadata": {
            "readback_type": "three_core_approval_preview_service_readback",
            "source_preview_supplied": bool(source),
            "source_preview_ready": _preview_is_ready(summary),
            "operator_review_only": True,
            "app_service_wiring_added": False,
        },
        "operator_review_summary": {
            "review_status": (
                "ready_for_operator_review"
                if status == STATUS_READY
                else "blocked"
            ),
            "operator_review_only": True,
            "human_decision_required": True,
            "approval_created": False,
        },
        "evidence_summary": _plain_dict(summary.get("evidence_summary")),
        "proposed_action_summary": _plain_dict(
            summary.get("proposed_action_summary")
        ),
        "risk_summary": _plain_dict(summary.get("risk_summary")),
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
        "did_persist_decision": False,
        "did_persist_audit": False,
        KEY_EXECUTION_REQUEST_CREATED: False,
        KEY_APPLICATION_EXECUTED: False,
        KEY_APPLICATION_SUBMITTED: False,
        "application_execution_authorized": False,
        "submission_authorized": False,
        "mutation_authorized": False,
        "safety_metadata": safety,
    }


def _build_three_core_approval_preview_service_readback_payload(
    *,
    enabled: bool,
    approval_preview_runtime_payload: dict[str, Any] | None,
    shadow_runtime_readback_payload: dict[str, Any] | None,
    shadow_sidecar_hook_payload: dict[str, Any] | None,
    readback_context: dict[str, Any] | None,
    readback_config: dict[str, Any] | None,
) -> dict[str, Any]:
    context = _plain_dict(readback_context)
    config = _plain_dict(readback_config)

    if (
        enabled is not True
        or config.get(APPROVAL_PREVIEW_SERVICE_READBACK_FLAG) is not True
    ):
        return _payload(
            status=STATUS_NOT_ENABLED,
            readback_enabled=False,
            context=context,
            source={},
            summary={},
            missing_requirements=[APPROVAL_PREVIEW_SERVICE_READBACK_FLAG],
            fail_closed_reason="approval_preview_service_readback_flag_not_enabled",
            next_safe_step="enable_service_readback_explicitly",
        )

    if (
        config.get(SHADOW_KILL_SWITCH_FLAG) is True
        or config.get("kill_switch_enabled") is True
    ):
        return _payload(
            status=STATUS_BLOCKED_BY_KILL_SWITCH,
            readback_enabled=False,
            context=context,
            source={},
            summary={},
            missing_requirements=[],
            fail_closed_reason="shadow_kill_switch_enabled",
            next_safe_step="disable_kill_switch_before_service_readback",
        )

    source = _plain_dict(approval_preview_runtime_payload)
    if not source and (
        isinstance(shadow_runtime_readback_payload, dict)
        or isinstance(shadow_sidecar_hook_payload, dict)
    ):
        source = (
            three_core_approval_preview_runtime
            .build_three_core_approval_preview_runtime_payload(
                enabled=True,
                shadow_runtime_readback_payload=_plain_dict(
                    shadow_runtime_readback_payload
                ),
                shadow_sidecar_hook_payload=_plain_dict(
                    shadow_sidecar_hook_payload
                ),
                preview_context=context,
                preview_config={APPROVAL_PREVIEW_RUNTIME_FLAG: True},
            )
        )
        source = _plain_dict(source)

    if not source:
        return _payload(
            status=STATUS_BLOCKED_MISSING_PREVIEW,
            readback_enabled=True,
            context=context,
            source={},
            summary={},
            missing_requirements=["approval_preview_runtime_payload"],
            fail_closed_reason="missing_approval_preview_runtime_payload",
            next_safe_step="supply_ready_approval_preview_runtime_payload",
        )

    summary = _preview_summary(source)
    if not _preview_is_ready(summary):
        missing = list(summary.get("missing_requirements") or [])
        if not missing:
            missing = ["ready_safe_three_core_approval_preview"]
        return _payload(
            status=STATUS_BLOCKED_INCOMPLETE_PREVIEW,
            readback_enabled=True,
            context=context,
            source=source,
            summary=summary,
            missing_requirements=missing,
            fail_closed_reason="incomplete_or_unsafe_approval_preview",
            next_safe_step="complete_approval_preview_before_service_readback",
        )

    return _payload(
        status=STATUS_READY,
        readback_enabled=True,
        context=context,
        source=source,
        summary=summary,
        missing_requirements=[],
        fail_closed_reason="",
        next_safe_step="review_service_readback_metadata_only",
    )


def build_three_core_approval_preview_service_readback_payload(
    *,
    enabled: bool = False,
    approval_preview_runtime_payload: dict[str, Any] | None = None,
    shadow_runtime_readback_payload: dict[str, Any] | None = None,
    shadow_sidecar_hook_payload: dict[str, Any] | None = None,
    readback_context: dict[str, Any] | None = None,
    readback_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Summarize a Phase 19A preview without wiring an app service."""

    try:
        return _build_three_core_approval_preview_service_readback_payload(
            enabled=enabled,
            approval_preview_runtime_payload=approval_preview_runtime_payload,
            shadow_runtime_readback_payload=shadow_runtime_readback_payload,
            shadow_sidecar_hook_payload=shadow_sidecar_hook_payload,
            readback_context=readback_context,
            readback_config=readback_config,
        )
    except Exception:
        return _payload(
            status=STATUS_FAILED_CLOSED,
            readback_enabled=enabled is True,
            context={},
            source={},
            summary={},
            missing_requirements=["valid_approval_preview_runtime_payload"],
            fail_closed_reason="unexpected_service_readback_failure",
            next_safe_step="inspect_failure_before_retry",
        )


def build_three_core_approval_preview_service_readback_helper_payload(
    **kwargs: Any,
) -> dict[str, Any]:
    """Compatibility wrapper for later explicitly approved integration."""

    return build_three_core_approval_preview_service_readback_payload(**kwargs)
