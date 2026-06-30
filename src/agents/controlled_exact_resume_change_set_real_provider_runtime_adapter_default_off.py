"""Default-off real provider runtime adapter for exact resume change sets."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import importlib
import json
from typing import Any


PHASE = "49A"
DEFAULT_ALLOWED_PROVIDER_MODULE_PREFIXES = ("src.tailoring.llm",)
FALSE_ACTION_KEYS = (
    "provider_response_validation_performed",
    "provider_response_normalization_performed",
    "manual_review_packets_created",
    "manual_review_readback_payload_created",
    "ui_route_added",
    "api_route_added",
    "ui_readback_performed",
    "api_readback_performed",
    "user_acceptance_performed",
    "ai_tailoring_generation_performed",
    "real_tailoring_output_created",
    "resume_change_proposals_created",
    "resume_change_applied",
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
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "y"}:
            return True
        if lowered in {"0", "false", "no", "n"}:
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


def _string(value: Any) -> str:
    return str(value or "").strip()


def _policy(provider_policy: dict[str, Any] | None) -> dict[str, Any]:
    supplied = provider_policy if isinstance(provider_policy, dict) else {}
    prefixes = supplied.get("allowed_provider_module_prefixes")
    allowed_prefixes: list[str] = []
    if isinstance(prefixes, list):
        for prefix in prefixes:
            text = _string(prefix)
            if text:
                allowed_prefixes.append(text)
    if not allowed_prefixes:
        allowed_prefixes = list(DEFAULT_ALLOWED_PROVIDER_MODULE_PREFIXES)
    policy = {
        "allow_real_provider_call": _bool(
            supplied.get("allow_real_provider_call"),
            False,
        ),
        "provider_callable_path": _string(supplied.get("provider_callable_path")),
        "allowed_provider_module_prefixes": allowed_prefixes,
        "capture_raw_response": _bool(supplied.get("capture_raw_response"), True),
        "max_response_chars": _int_at_least(
            supplied.get("max_response_chars"),
            12000,
            1,
        ),
        "request_timeout_seconds": supplied.get("request_timeout_seconds"),
        "provider_name": _string(supplied.get("provider_name")),
        "model_name": _string(supplied.get("model_name")),
        "temperature": supplied.get("temperature"),
        "max_output_tokens": supplied.get("max_output_tokens"),
    }
    return policy


def _resolve_request_packet(
    request_packet: dict[str, Any] | None,
    request_result: dict[str, Any] | None,
) -> tuple[dict[str, Any] | None, str]:
    if isinstance(request_packet, dict):
        return deepcopy(request_packet), "request_packet"
    if not isinstance(request_result, dict):
        return None, "missing"
    direct = request_result.get("request_packet")
    if isinstance(direct, dict):
        return deepcopy(direct), "request_result.request_packet"
    nested = request_result.get("request_result")
    if isinstance(nested, dict) and isinstance(nested.get("request_packet"), dict):
        return (
            deepcopy(nested["request_packet"]),
            "request_result.request_result.request_packet",
        )
    llm_packet = request_result.get("llm_request_packet")
    if isinstance(llm_packet, dict):
        return deepcopy(llm_packet), "request_result.llm_request_packet"
    request_payload = request_result.get("request_payload")
    if isinstance(request_payload, dict):
        return deepcopy(request_payload), "request_result.request_payload"
    return None, "missing"


def _module_from_callable_path(path: str) -> str:
    if ":" in path:
        return path.split(":", 1)[0]
    if "." not in path:
        return ""
    return path.rsplit(".", 1)[0]


def _name_from_callable_path(path: str) -> str:
    if ":" in path:
        return path.split(":", 1)[1]
    if "." not in path:
        return ""
    return path.rsplit(".", 1)[1]


def _path_allowed(path: str, allowed_prefixes: list[str]) -> bool:
    module_name = _module_from_callable_path(path)
    if not module_name:
        return False
    for prefix in allowed_prefixes:
        if module_name == prefix or module_name.startswith(prefix + "."):
            return True
    return False


def _resolve_provider_callable(path: str) -> Any:
    module_name = _module_from_callable_path(path)
    callable_name = _name_from_callable_path(path)
    if not module_name or not callable_name:
        raise ValueError("provider callable path must include module and callable name")
    module = importlib.import_module(module_name)
    target: Any = module
    for part in callable_name.split("."):
        if not part:
            raise ValueError("provider callable path contains an empty attribute")
        target = getattr(target, part)
    if not callable(target):
        raise TypeError("provider callable path did not resolve to a callable")
    return target


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


def _sanitize_response(value: Any, *, depth: int = 0) -> Any:
    if depth > 8:
        return str(value)
    if callable(value):
        return {"callable_response_omitted": True, "response_type": type(value).__name__}
    if isinstance(value, dict):
        clean: dict[str, Any] = {}
        for key in sorted(value.keys(), key=str):
            clean[str(key)] = _sanitize_response(value.get(key), depth=depth + 1)
        return clean
    if isinstance(value, list):
        return [_sanitize_response(row, depth=depth + 1) for row in value]
    if isinstance(value, tuple):
        return [_sanitize_response(row, depth=depth + 1) for row in value]
    try:
        return deepcopy(value)
    except Exception:
        return str(value)


def _response_excerpt(value: Any, *, max_chars: int) -> tuple[str, bool]:
    text = str(value)
    if len(text) <= max_chars:
        return text, False
    return text[:max_chars], True


def _runtime_key(
    *,
    packet_source: str,
    request_packet_present: bool,
    enabled: bool,
    confirmed: bool,
    policy_allowed: bool,
    callable_supplied: bool,
    path_supplied: bool,
    path_allowed: bool,
    call_performed: bool,
    blocked_reason: str,
) -> str:
    key_payload = {
        "phase": PHASE,
        "packet_source": packet_source,
        "request_packet_present": request_packet_present,
        "enable_real_provider_call": enabled,
        "manual_trigger_confirmed": confirmed,
        "policy_allowed": policy_allowed,
        "provider_callable_supplied": callable_supplied,
        "provider_callable_path_supplied": path_supplied,
        "provider_callable_path_allowed": path_allowed,
        "real_provider_call_performed": call_performed,
        "blocked_reason": blocked_reason,
    }
    encoded = json.dumps(key_payload, sort_keys=True, separators=(",", ":"), default=str)
    return "phase49a-real-provider-runtime-" + sha256(encoded.encode("utf-8")).hexdigest()[:24]


def _blocked_reason(reasons: list[str]) -> str:
    return "; ".join(reasons)


def build_controlled_exact_resume_change_set_real_provider_runtime_adapter_default_off(
    request_packet: dict[str, Any] | None = None,
    request_result: dict[str, Any] | None = None,
    provider_callable: Any = None,
    enable_real_provider_call: bool = False,
    manual_trigger_confirmed: bool = False,
    provider_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run a real provider callable only after explicit manual gates pass."""

    policy = _policy(provider_policy)
    safe_packet, packet_source = _resolve_request_packet(request_packet, request_result)
    request_packet_present = isinstance(safe_packet, dict) and bool(safe_packet)
    request_result_present = isinstance(request_result, dict)
    callable_supplied = callable(provider_callable)
    callable_path = str(policy["provider_callable_path"])
    callable_path_supplied = bool(callable_path)
    callable_path_allowed = (
        _path_allowed(callable_path, policy["allowed_provider_module_prefixes"])
        if callable_path_supplied
        else False
    )

    reasons: list[str] = []
    if not request_packet_present:
        reasons.append("missing request_packet")
    if not bool(enable_real_provider_call):
        reasons.append("enable_real_provider_call must be true")
    if not bool(manual_trigger_confirmed):
        reasons.append("manual trigger confirmation required")
    if not policy["allow_real_provider_call"]:
        reasons.append("provider policy must allow real provider call")
    if not callable_supplied and not callable_path_supplied:
        reasons.append("provider callable or allowed provider callable path required")
    if callable_path_supplied and not callable_path_allowed:
        reasons.append("provider callable path is outside allowed prefixes")

    real_provider_call_allowed = not reasons
    real_provider_call_blocked_reason = _blocked_reason(reasons)
    real_provider_call_attempted = False
    real_provider_call_performed = False
    provider_runtime_error = ""
    provider_response: Any = None
    provider_response_present = False
    provider_callable_source = "none"

    if real_provider_call_allowed and safe_packet is not None:
        resolved_callable = provider_callable
        provider_callable_source = "provider_callable" if callable_supplied else "provider_callable_path"
        try:
            if not callable_supplied:
                resolved_callable = _resolve_provider_callable(callable_path)
            real_provider_call_attempted = True
            raw_response = resolved_callable(deepcopy(safe_packet))
            sanitized_response = _sanitize_response(raw_response)
            if policy["capture_raw_response"]:
                provider_response = sanitized_response
            else:
                excerpt, truncated = _response_excerpt(
                    sanitized_response,
                    max_chars=policy["max_response_chars"],
                )
                provider_response = {
                    "raw_response_captured": False,
                    "response_excerpt": excerpt,
                    "response_truncated": truncated,
                }
            provider_response_present = True
            real_provider_call_performed = True
        except Exception as exc:  # pragma: no cover - external callable shape varies.
            provider_runtime_error = f"{type(exc).__name__}: {exc}"
            real_provider_call_blocked_reason = "provider runtime raised error"
            real_provider_call_allowed = False

    summary_excerpt, summary_truncated = _response_excerpt(
        provider_response,
        max_chars=policy["max_response_chars"],
    )
    provider_response_summary = {
        "provider_response_present": provider_response_present,
        "provider_response_type": _response_type(provider_response),
        "provider_response_excerpt": summary_excerpt if provider_response_present else "",
        "provider_response_truncated": summary_truncated if provider_response_present else False,
        "capture_raw_response": policy["capture_raw_response"],
        "max_response_chars": policy["max_response_chars"],
        "provider_response_validation_performed": False,
        "provider_response_normalization_performed": False,
    }
    tailoring_runtime_call_performed = (
        real_provider_call_performed
        and provider_callable_source == "provider_callable_path"
        and _module_from_callable_path(callable_path) == "src.tailoring.llm"
    )
    payload = {
        "phase": PHASE,
        "default_off": True,
        "controlled_exact_resume_change_set_real_provider_runtime_adapter": True,
        "real_provider_runtime_adapter_only": True,
        "read_only": True,
        "advisory_only": True,
        "provider_execution_boundary_only": True,
        "proposal_only": True,
        "exact_worthy_changes_only": True,
        "manual_review_required": True,
        "requires_manual_user_control": True,
        "request_packet_present": request_packet_present,
        "request_result_present": request_result_present,
        "provider_policy": deepcopy(policy),
        "provider_callable_supplied": callable_supplied,
        "provider_callable_path_supplied": callable_path_supplied,
        "provider_callable_path_allowed": callable_path_allowed,
        "real_provider_call_allowed": real_provider_call_allowed,
        "real_provider_call_blocked_reason": real_provider_call_blocked_reason,
        "real_provider_call_attempted": real_provider_call_attempted,
        "real_provider_call_performed": real_provider_call_performed,
        "llm_call_performed": real_provider_call_performed,
        "provider_response": provider_response,
        "provider_response_summary": provider_response_summary,
        "provider_runtime_error": provider_runtime_error,
        "provider_runtime_key": _runtime_key(
            packet_source=packet_source,
            request_packet_present=request_packet_present,
            enabled=bool(enable_real_provider_call),
            confirmed=bool(manual_trigger_confirmed),
            policy_allowed=bool(policy["allow_real_provider_call"]),
            callable_supplied=callable_supplied,
            path_supplied=callable_path_supplied,
            path_allowed=callable_path_allowed,
            call_performed=real_provider_call_performed,
            blocked_reason=real_provider_call_blocked_reason,
        ),
        "manual_trigger_confirmed": bool(manual_trigger_confirmed),
        "enable_real_provider_call": bool(enable_real_provider_call),
        "tailoring_runtime_call_performed": tailoring_runtime_call_performed,
    }
    for key in FALSE_ACTION_KEYS:
        payload[key] = False
    return payload
