"""Phase 19G default-off operator decision capture readback contract."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


OPERATOR_DECISION_CAPTURE_READBACK_FLAG = (
    "APPLYLENS_AGENTIC_PIPELINE_OPERATOR_DECISION_CAPTURE_READBACK_ENABLED"
)
SHADOW_KILL_SWITCH_FLAG = (
    "APPLYLENS_AGENTIC_PIPELINE_SHADOW_KILL_SWITCH"
)
OPERATOR_DECISION_CAPTURE_READBACK_VERSION = (
    "phase-19g-operator-decision-capture-readback-contract-v1"
)
OPERATOR_DECISION_CAPTURE_READBACK_SCHEMA_VERSION = (
    "phase-19g-operator-decision-capture-readback-payload-v1"
)

ALLOWED_ACTIONS = (
    "APPLY",
    "APPLY_REVIEW_VARIANTS",
    "MAYBE_TAILOR",
    "SKIP_FOR_NOW",
    "HOLD",
)

STATUS_NOT_ENABLED = "operator_decision_capture_readback_not_enabled"
STATUS_BLOCKED_BY_KILL_SWITCH = (
    "operator_decision_capture_readback_blocked_by_kill_switch"
)
STATUS_MISSING_ACTION = (
    "operator_decision_capture_readback_missing_action"
)
STATUS_INVALID_ACTION = (
    "operator_decision_capture_readback_invalid_action"
)
STATUS_READY = "operator_decision_capture_readback_ready"
STATUS_FAILED_CLOSED = "operator_decision_capture_readback_failed_closed"

KEY_QUEUE_MUTATED = "did_mutate_" + "queue"
KEY_EXECUTION_REQUEST_CREATED = "did_create_execution_" + "request"
KEY_APPLICATION_EXECUTED = "did_execute_" + "application"
KEY_APPLICATION_SUBMITTED = "did_submit_" + "application"


def _plain_dict(value: Any) -> dict[str, Any]:
    return deepcopy(value) if isinstance(value, dict) else {}


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def operator_decision_capture_readback_safety_metadata(
) -> dict[str, bool]:
    return {
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "contract_only": True,
        "provider_call": False,
        "provider_sdk_import": False,
        "env_secret_read": False,
        "network_call": False,
        "did_read_database": False,
        "did_write_database": False,
        "did_read_file": False,
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
    selected_action: str,
    selected_resume: str,
    selected_variant: str,
    operator_note: str,
    validation_errors: list[str],
    next_safe_step: str,
) -> dict[str, Any]:
    safety = operator_decision_capture_readback_safety_metadata()
    return {
        "schema_version": OPERATOR_DECISION_CAPTURE_READBACK_SCHEMA_VERSION,
        "readback_version": OPERATOR_DECISION_CAPTURE_READBACK_VERSION,
        "capture_status": status,
        "enabled": enabled,
        "default_off": True,
        "selected_action": selected_action,
        "selected_resume": selected_resume,
        "selected_variant": selected_variant,
        "operator_note": operator_note,
        "allowed_actions": list(ALLOWED_ACTIONS),
        "validation_errors": list(validation_errors),
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "contract_only": True,
        "decision_persisted": False,
        "approval_created": False,
        "audit_persisted": False,
        "execution_authorized": False,
        "submission_authorized": False,
        "mutation_authorized": False,
        "next_safe_step": next_safe_step,
        "safety_metadata": safety,
    }


def _build_operator_decision_capture_readback_payload(
    *,
    enabled: bool,
    selected_action: str,
    selected_resume: str,
    selected_variant: str,
    operator_note: str,
    config: dict[str, Any] | None,
) -> dict[str, Any]:
    safe_config = _plain_dict(config)
    action = _clean_text(selected_action).upper()
    resume = _clean_text(selected_resume)
    variant = _clean_text(selected_variant)
    note = _clean_text(operator_note)

    if (
        enabled is not True
        or safe_config.get(OPERATOR_DECISION_CAPTURE_READBACK_FLAG) is not True
    ):
        return _payload(
            status=STATUS_NOT_ENABLED,
            enabled=False,
            selected_action=action,
            selected_resume=resume,
            selected_variant=variant,
            operator_note=note,
            validation_errors=[],
            next_safe_step="enable_capture_readback_contract_explicitly",
        )

    if (
        safe_config.get("kill_switch_enabled") is True
        or safe_config.get(SHADOW_KILL_SWITCH_FLAG) is True
    ):
        return _payload(
            status=STATUS_BLOCKED_BY_KILL_SWITCH,
            enabled=False,
            selected_action=action,
            selected_resume=resume,
            selected_variant=variant,
            operator_note=note,
            validation_errors=[],
            next_safe_step="disable_kill_switch_before_contract_preview",
        )

    if not action:
        return _payload(
            status=STATUS_MISSING_ACTION,
            enabled=True,
            selected_action="",
            selected_resume=resume,
            selected_variant=variant,
            operator_note=note,
            validation_errors=["selected_action_is_required"],
            next_safe_step="supply_one_allowed_operator_action",
        )

    if action not in ALLOWED_ACTIONS:
        return _payload(
            status=STATUS_INVALID_ACTION,
            enabled=True,
            selected_action=action,
            selected_resume=resume,
            selected_variant=variant,
            operator_note=note,
            validation_errors=["selected_action_is_not_allowed"],
            next_safe_step="select_one_allowed_operator_action",
        )

    return _payload(
        status=STATUS_READY,
        enabled=True,
        selected_action=action,
        selected_resume=resume,
        selected_variant=variant,
        operator_note=note,
        validation_errors=[],
        next_safe_step="review_contract_payload_without_persisting",
    )


def build_operator_decision_capture_readback_payload(
    *,
    enabled: bool = False,
    selected_action: str = "",
    selected_resume: str = "",
    selected_variant: str = "",
    operator_note: str = "",
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a deterministic contract payload without persistence."""

    try:
        return _build_operator_decision_capture_readback_payload(
            enabled=enabled,
            selected_action=selected_action,
            selected_resume=selected_resume,
            selected_variant=selected_variant,
            operator_note=operator_note,
            config=config,
        )
    except Exception:
        return _payload(
            status=STATUS_FAILED_CLOSED,
            enabled=False,
            selected_action="",
            selected_resume="",
            selected_variant="",
            operator_note="",
            validation_errors=["unexpected_contract_validation_failure"],
            next_safe_step="inspect_contract_input_before_retry",
        )


def build_operator_decision_capture_readback_helper_payload(
    **kwargs: Any,
) -> dict[str, Any]:
    """Compatibility wrapper for later explicitly approved readback use."""

    return build_operator_decision_capture_readback_payload(**kwargs)
