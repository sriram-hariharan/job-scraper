"""Phase 21B default-off manual-review readiness contract."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


MANUAL_REVIEW_READINESS_CONTRACT_VERSION = (
    "phase-21b-manual-review-readiness-contract-v1"
)
MANUAL_REVIEW_READINESS_SCHEMA_VERSION = (
    "phase-21b-manual-review-readiness-payload-v1"
)

STATUS_NOT_ENABLED = "manual_review_readiness_not_enabled"
STATUS_MISSING_INPUTS = "manual_review_readiness_missing_inputs"
STATUS_READY = "manual_review_readiness_ready"
STATUS_FAILED_CLOSED = "manual_review_readiness_failed_closed"

ALLOWED_ASSISTANCE_MODES = (
    "discovery",
    "filtering",
    "ranking",
    "read-only previews",
    "readiness checks",
    "resume/content guidance",
    "manual review support",
)

FORBIDDEN_ACTIONS = (
    "auto-apply",
    "auto-submit",
    "autonomous application execution",
    "automatic job application submission",
    "bypass of manual review",
)

MANUAL_REVIEW_CHECKLIST_ITEMS = (
    "review_job_details",
    "review_role_fit_and_ranking_evidence",
    "review_resume_and_content_guidance",
    "review_application_materials",
    "confirm_manual_user_control",
    "complete_submission_outside_autonomous_execution",
)


def _plain_dict(value: Any) -> dict[str, Any]:
    return deepcopy(value) if isinstance(value, dict) else {}


def manual_review_readiness_safety_metadata() -> dict[str, bool]:
    return {
        "read_only": True,
        "advisory_only": True,
        "manual_review_required": True,
        "manual_user_control_required": True,
        "provider_call_attempted": False,
        "network_call_attempted": False,
        "database_write_attempted": False,
        "approval_created": False,
        "decision_persisted": False,
        "audit_persisted": False,
        "scoring_mutated": False,
        "ranking_mutated": False,
        "queue_mutated": False,
        "resume_mutated": False,
        "application_mutated": False,
        "execution_authorized": False,
        "submission_authorized": False,
        "mutation_authorized": False,
    }


def _payload(
    *,
    status: str,
    enabled: bool,
    review_inputs_summary: dict[str, Any],
    missing_review_inputs: list[str],
    next_safe_step: str,
) -> dict[str, Any]:
    return {
        "version": MANUAL_REVIEW_READINESS_CONTRACT_VERSION,
        "schema_version": MANUAL_REVIEW_READINESS_SCHEMA_VERSION,
        "readiness_status": status,
        "enabled": enabled,
        "default_off": True,
        "read_only": True,
        "advisory_only": True,
        "manual_review_required": True,
        "manual_user_control_required": True,
        "no_auto_apply": True,
        "no_auto_submit": True,
        "no_autonomous_application_execution": True,
        "no_automatic_job_application_submission": True,
        "allowed_assistance_modes": list(ALLOWED_ASSISTANCE_MODES),
        "forbidden_actions": list(FORBIDDEN_ACTIONS),
        "review_inputs_summary": deepcopy(review_inputs_summary),
        "missing_review_inputs": list(missing_review_inputs),
        "checklist_items": list(MANUAL_REVIEW_CHECKLIST_ITEMS),
        "next_safe_step": next_safe_step,
        "safety_metadata": manual_review_readiness_safety_metadata(),
    }


def _build_manual_review_readiness_payload(
    *,
    enabled: bool,
    review_inputs_summary: dict[str, Any] | None,
) -> dict[str, Any]:
    safe_inputs = _plain_dict(review_inputs_summary)

    if enabled is not True:
        return _payload(
            status=STATUS_NOT_ENABLED,
            enabled=False,
            review_inputs_summary=safe_inputs,
            missing_review_inputs=[],
            next_safe_step="enable_manual_review_readiness_explicitly",
        )

    if not safe_inputs:
        return _payload(
            status=STATUS_MISSING_INPUTS,
            enabled=True,
            review_inputs_summary={},
            missing_review_inputs=["review_inputs_summary"],
            next_safe_step="supply_caller_review_inputs_for_manual_review",
        )

    return _payload(
        status=STATUS_READY,
        enabled=True,
        review_inputs_summary=safe_inputs,
        missing_review_inputs=[],
        next_safe_step="complete_manual_review_under_user_control",
    )


def build_manual_review_readiness_payload(
    *,
    enabled: bool = False,
    review_inputs_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a deterministic manual-review readiness payload."""

    try:
        return _build_manual_review_readiness_payload(
            enabled=enabled,
            review_inputs_summary=review_inputs_summary,
        )
    except Exception:
        return _payload(
            status=STATUS_FAILED_CLOSED,
            enabled=False,
            review_inputs_summary={},
            missing_review_inputs=["valid_caller_review_inputs"],
            next_safe_step="inspect_manual_review_inputs_before_retry",
        )


def build_manual_review_readiness_helper_payload(
    **kwargs: Any,
) -> dict[str, Any]:
    """Compatibility wrapper for later explicitly approved readback use."""

    return build_manual_review_readiness_payload(**kwargs)
