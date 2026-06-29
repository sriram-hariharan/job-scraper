"""Default-off provider-call boundary for exact resume change-set refinement."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


PHASE = "44A"
REQUEST_TYPE = "exact_resume_change_set_refinement"
FALSE_ACTION_KEYS = (
    "network_call_performed",
    "tailoring_runtime_call_performed",
    "ai_tailoring_generation_performed",
    "real_tailoring_output_created",
    "resume_change_proposals_created",
    "resume_rewrite_performed",
    "resume_overwrite_performed",
    "resume_mutation_performed",
    "final_score_produced",
    "existing_score_changed",
    "matching_scoring_module_called",
    "database_write_performed",
    "persistence_performed",
    "execution_performed",
    "application_submission_performed",
    "submission_performed",
    "auto_apply_performed",
    "auto_submit_performed",
)


def _bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"1", "true", "yes", "y"}:
            return True
        if text in {"0", "false", "no", "n"}:
            return False
    return default if value is None else bool(value)


def _int_at_least(value: Any, default: int, minimum: int) -> int:
    if isinstance(value, bool):
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed >= minimum else default


def _policy(value: dict[str, Any] | None) -> dict[str, Any]:
    supplied = value if isinstance(value, dict) else {}
    return {
        "require_manual_trigger": _bool(
            supplied.get("require_manual_trigger"),
            True,
        ),
        "require_provider_callable": _bool(
            supplied.get("require_provider_callable"),
            True,
        ),
        "allow_provider_call": _bool(supplied.get("allow_provider_call"), False),
        "capture_raw_response": _bool(supplied.get("capture_raw_response"), True),
        "max_response_chars": _int_at_least(
            supplied.get("max_response_chars"),
            20000,
            1,
        ),
    }


def _looks_like_request_packet(value: Any) -> bool:
    return isinstance(value, dict) and value.get("request_type") == REQUEST_TYPE


def _packet_from_result(value: Any) -> tuple[dict[str, Any] | None, str]:
    if not isinstance(value, dict):
        return None, "missing"
    direct = value.get("request_packet")
    if isinstance(direct, dict):
        if _looks_like_request_packet(direct):
            return deepcopy(direct), "request_result.request_packet"
        nested_packet = direct.get("request_packet")
        if _looks_like_request_packet(nested_packet):
            return (
                deepcopy(nested_packet),
                "request_result.request_packet.request_packet",
            )
    nested_result = value.get("request_result")
    if isinstance(nested_result, dict):
        nested = nested_result.get("request_packet")
        if isinstance(nested, dict):
            return deepcopy(nested), "request_result.request_result.request_packet"
    return None, "missing"


def _resolve_request_packet(
    request_packet: dict[str, Any] | None,
    request_result: dict[str, Any] | None,
) -> tuple[dict[str, Any] | None, str]:
    if isinstance(request_packet, dict):
        return deepcopy(request_packet), "request_packet"
    return _packet_from_result(request_result)


def _response_type(value: Any) -> str:
    if value is None:
        return "none"
    if isinstance(value, dict):
        return "dict"
    if isinstance(value, list):
        return "list"
    if isinstance(value, str):
        return "str"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int) and not isinstance(value, bool):
        return "int"
    if isinstance(value, float):
        return "float"
    return type(value).__name__


def _safe_response(value: Any, *, max_chars: int) -> Any:
    copied = deepcopy(value)
    text = str(copied)
    if len(text) <= max_chars:
        return copied
    return {
        "response_truncated": True,
        "response_excerpt": text[:max_chars],
        "original_response_type": _response_type(value),
    }


def _provider_call_key(
    *,
    source: str,
    valid: bool,
    enabled: bool,
    confirmed: bool,
    callable_valid: bool,
    allowed: bool,
    reason: str,
) -> str:
    return "|".join(
        (
            f"phase={PHASE}",
            f"source={source}",
            f"valid={valid}",
            f"enabled={enabled}",
            f"confirmed={confirmed}",
            f"callable={callable_valid}",
            f"allowed={allowed}",
            f"reason={reason}",
        )
    )


def build_controlled_exact_resume_change_set_provider_call_boundary_default_off(
    request_packet: dict[str, Any] | None = None,
    request_result: dict[str, Any] | None = None,
    provider_callable: Any = None,
    enable_provider_call: bool = False,
    manual_trigger_confirmed: bool = False,
    provider_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Optionally call an injected provider callable behind explicit gates."""

    policy = _policy(provider_policy)
    safe_packet, packet_source = _resolve_request_packet(request_packet, request_result)
    request_packet_present = isinstance(safe_packet, dict)
    request_packet_valid = _looks_like_request_packet(safe_packet)
    callable_present = provider_callable is not None
    callable_valid = callable(provider_callable)
    missing_inputs: list[str] = []
    blocked_reasons: list[str] = []

    if not request_packet_present:
        missing_inputs.append("request_packet")
        blocked_reasons.append("valid request packet required")
    elif not request_packet_valid:
        blocked_reasons.append("request packet type must be exact resume change-set refinement")

    if not bool(enable_provider_call):
        blocked_reasons.append("enable_provider_call must be true")
    if not policy["allow_provider_call"]:
        blocked_reasons.append("provider policy must allow provider call")
    if policy["require_manual_trigger"] and not bool(manual_trigger_confirmed):
        blocked_reasons.append("manual trigger confirmation required")
    if policy["require_provider_callable"] and not callable_valid:
        missing_inputs.append("provider_callable")
        blocked_reasons.append("valid provider callable required")

    provider_call_allowed = not blocked_reasons
    blocked_reason = "; ".join(blocked_reasons)
    provider_response: Any = None
    provider_call_attempted = False
    provider_call_performed = False
    provider_error = ""

    if provider_call_allowed and callable_valid and safe_packet is not None:
        provider_call_attempted = True
        try:
            raw_response = provider_callable(deepcopy(safe_packet))
            provider_response = _safe_response(
                raw_response,
                max_chars=policy["max_response_chars"],
            )
            provider_call_performed = True
        except Exception as exc:  # pragma: no cover - exact exception type is external.
            provider_error = f"{type(exc).__name__}: {exc}"
            blocked_reason = "provider callable raised error"
            provider_call_allowed = False

    response_present = provider_response is not None
    response_kind = _response_type(provider_response)
    provider_call_result = {
        "status": (
            "provider_call_performed"
            if provider_call_performed
            else "provider_call_blocked"
        ),
        "provider_call_allowed": provider_call_allowed,
        "provider_call_attempted": provider_call_attempted,
        "provider_call_performed": provider_call_performed,
        "provider_error": provider_error,
    }
    provider_response_summary = {
        "provider_response_present": response_present,
        "provider_response_type": response_kind,
        "provider_response_validation_performed": False,
        "deep_response_validation_performed": False,
        "raw_response_captured": policy["capture_raw_response"] and response_present,
    }
    findings = {
        "request_packet_source": packet_source,
        "request_packet_copied": request_packet_present,
        "explicit_manual_trigger_required": policy["require_manual_trigger"],
        "injected_provider_callable_only": True,
        "provider_sdk_imported": False,
        "direct_network_call_performed": False,
        "provider_response_validation_deferred": True,
        "executable_callbacks_included": False,
        "function_pointers_included": False,
        "mutation_commands_included": False,
        "db_write_commands_included": False,
        "application_submission_commands_included": False,
    }
    payload = {
        "phase": PHASE,
        "default_off": True,
        "controlled_exact_resume_change_set_provider_call_boundary": True,
        "read_only": True,
        "advisory_only": True,
        "proposal_only": True,
        "provider_call_boundary_only": True,
        "exact_worthy_changes_only": True,
        "manual_review_required": True,
        "requires_manual_user_control": True,
        "manual_trigger_required": True,
        "manual_trigger_confirmed": bool(manual_trigger_confirmed),
        "request_packet_present": request_packet_present,
        "request_packet_valid": request_packet_valid,
        "provider_callable_present": callable_present,
        "provider_callable_valid": callable_valid,
        "enable_provider_call": bool(enable_provider_call),
        "provider_policy": deepcopy(policy),
        "provider_call_allowed": provider_call_allowed,
        "provider_call_blocked_reason": blocked_reason,
        "provider_call_result": provider_call_result,
        "provider_response": provider_response,
        "provider_response_present": response_present,
        "provider_response_type": response_kind,
        "provider_response_summary": provider_response_summary,
        "provider_call_findings": findings,
        "missing_inputs": list(missing_inputs),
        "provider_call_key": _provider_call_key(
            source=packet_source,
            valid=request_packet_valid,
            enabled=bool(enable_provider_call),
            confirmed=bool(manual_trigger_confirmed),
            callable_valid=callable_valid,
            allowed=provider_call_allowed,
            reason=blocked_reason,
        ),
        "provider_call_attempted": provider_call_attempted,
        "provider_call_performed": provider_call_performed,
        "llm_call_performed": provider_call_performed,
    }
    for key in FALSE_ACTION_KEYS:
        payload[key] = False
    return payload
