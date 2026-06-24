"""Phase 20A default-off provider-call readiness experiment."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


PROVIDER_CALL_READINESS_EXPERIMENT_FLAG = (
    "APPLYLENS_AGENTIC_PIPELINE_PROVIDER_CALL_READINESS_EXPERIMENT_ENABLED"
)
SHADOW_KILL_SWITCH_FLAG = (
    "APPLYLENS_AGENTIC_PIPELINE_SHADOW_KILL_SWITCH"
)
PROVIDER_CALL_READINESS_EXPERIMENT_VERSION = (
    "phase-20a-provider-call-readiness-experiment-v1"
)
PROVIDER_CALL_READINESS_EXPERIMENT_SCHEMA_VERSION = (
    "phase-20a-provider-call-readiness-experiment-payload-v1"
)

STATUS_NOT_ENABLED = "provider_call_readiness_experiment_not_enabled"
STATUS_BLOCKED_BY_KILL_SWITCH = (
    "provider_call_readiness_experiment_blocked_by_kill_switch"
)
STATUS_MISSING_PROVIDER_CAPABILITY = (
    "provider_call_readiness_experiment_missing_provider_capability"
)
STATUS_MISSING_REQUEST_PACKET = (
    "provider_call_readiness_experiment_missing_request_packet"
)
STATUS_READY = "provider_call_readiness_experiment_ready"
STATUS_FAILED_CLOSED = "provider_call_readiness_experiment_failed_closed"


def _plain_dict(value: Any) -> dict[str, Any]:
    return deepcopy(value) if isinstance(value, dict) else {}


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def provider_call_readiness_experiment_safety_metadata(
) -> dict[str, bool]:
    return {
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "readiness_only": True,
        "provider_call_attempted": False,
        "provider_call_authorized": False,
        "provider_sdk_imported": False,
        "network_call_attempted": False,
        "environment_read": False,
        "did_read_database": False,
        "did_write_database": False,
        "did_read_file": False,
        "did_write_file": False,
        "did_mutate_scoring": False,
        "did_change_ranking": False,
        "did_mutate_queue": False,
        "did_mutate_resume": False,
        "did_create_approval": False,
        "did_persist_decision": False,
        "did_persist_audit": False,
        "did_create_execution_request": False,
        "did_execute_application": False,
        "did_submit_application": False,
        "api_route_added": False,
        "ui_action_added": False,
        "service_wiring_added": False,
        "pipeline_wiring_added": False,
        "collector_wiring_added": False,
        "mutation_authorized": False,
        "execution_authorized": False,
        "submission_authorized": False,
    }


def _payload(
    *,
    status: str,
    enabled: bool,
    requested_provider_capability: str,
    provider_name: str,
    requested_model: str,
    request_packet_summary: dict[str, Any],
    validation_errors: list[str],
    next_safe_step: str,
) -> dict[str, Any]:
    return {
        "version": PROVIDER_CALL_READINESS_EXPERIMENT_VERSION,
        "schema_version": PROVIDER_CALL_READINESS_EXPERIMENT_SCHEMA_VERSION,
        "readiness_status": status,
        "enabled": enabled,
        "default_off": True,
        "requested_provider_capability": requested_provider_capability,
        "provider_name": provider_name,
        "requested_model": requested_model,
        "request_packet_summary": deepcopy(request_packet_summary),
        "validation_errors": list(validation_errors),
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "provider_call_attempted": False,
        "provider_call_authorized": False,
        "network_call_attempted": False,
        "decision_persisted": False,
        "approval_created": False,
        "audit_persisted": False,
        "execution_authorized": False,
        "submission_authorized": False,
        "mutation_authorized": False,
        "next_safe_step": next_safe_step,
        "safety_metadata": (
            provider_call_readiness_experiment_safety_metadata()
        ),
    }


def _build_provider_call_readiness_experiment_payload(
    *,
    enabled: bool,
    requested_provider_capability: str,
    provider_name: str,
    requested_model: str,
    request_packet_summary: dict[str, Any] | None,
    config: dict[str, Any] | None,
) -> dict[str, Any]:
    safe_config = _plain_dict(config)
    capability = _clean_text(requested_provider_capability)
    safe_provider_name = _clean_text(provider_name)
    safe_requested_model = _clean_text(requested_model)
    safe_request_packet = _plain_dict(request_packet_summary)

    if (
        enabled is not True
        or safe_config.get(
            PROVIDER_CALL_READINESS_EXPERIMENT_FLAG
        ) is not True
    ):
        return _payload(
            status=STATUS_NOT_ENABLED,
            enabled=False,
            requested_provider_capability=capability,
            provider_name=safe_provider_name,
            requested_model=safe_requested_model,
            request_packet_summary=safe_request_packet,
            validation_errors=[],
            next_safe_step="enable_readiness_experiment_explicitly",
        )

    if (
        safe_config.get("kill_switch_enabled") is True
        or safe_config.get(SHADOW_KILL_SWITCH_FLAG) is True
    ):
        return _payload(
            status=STATUS_BLOCKED_BY_KILL_SWITCH,
            enabled=False,
            requested_provider_capability=capability,
            provider_name=safe_provider_name,
            requested_model=safe_requested_model,
            request_packet_summary=safe_request_packet,
            validation_errors=[],
            next_safe_step="disable_kill_switch_before_readiness_review",
        )

    if not capability:
        return _payload(
            status=STATUS_MISSING_PROVIDER_CAPABILITY,
            enabled=True,
            requested_provider_capability="",
            provider_name=safe_provider_name,
            requested_model=safe_requested_model,
            request_packet_summary=safe_request_packet,
            validation_errors=[
                "requested_provider_capability_is_required"
            ],
            next_safe_step="supply_requested_provider_capability",
        )

    if not safe_request_packet:
        return _payload(
            status=STATUS_MISSING_REQUEST_PACKET,
            enabled=True,
            requested_provider_capability=capability,
            provider_name=safe_provider_name,
            requested_model=safe_requested_model,
            request_packet_summary={},
            validation_errors=["request_packet_summary_is_required"],
            next_safe_step="supply_read_only_request_packet_summary",
        )

    return _payload(
        status=STATUS_READY,
        enabled=True,
        requested_provider_capability=capability,
        provider_name=safe_provider_name,
        requested_model=safe_requested_model,
        request_packet_summary=safe_request_packet,
        validation_errors=[],
        next_safe_step="review_readiness_without_calling_provider",
    )


def build_provider_call_readiness_experiment_payload(
    *,
    enabled: bool = False,
    requested_provider_capability: str = "",
    provider_name: str = "",
    requested_model: str = "",
    request_packet_summary: dict[str, Any] | None = None,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a deterministic readiness payload without provider invocation."""

    try:
        return _build_provider_call_readiness_experiment_payload(
            enabled=enabled,
            requested_provider_capability=requested_provider_capability,
            provider_name=provider_name,
            requested_model=requested_model,
            request_packet_summary=request_packet_summary,
            config=config,
        )
    except Exception:
        return _payload(
            status=STATUS_FAILED_CLOSED,
            enabled=False,
            requested_provider_capability="",
            provider_name="",
            requested_model="",
            request_packet_summary={},
            validation_errors=[
                "unexpected_readiness_experiment_validation_failure"
            ],
            next_safe_step="inspect_caller_supplied_readiness_inputs",
        )


def build_provider_call_readiness_experiment_helper_payload(
    **kwargs: Any,
) -> dict[str, Any]:
    """Compatibility wrapper for a later explicitly approved readback."""

    return build_provider_call_readiness_experiment_payload(**kwargs)
