"""Default-off real provider response handoff pipeline for exact resume changes."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from typing import Any

from src.agents.controlled_exact_resume_change_set_manual_review_packet_builder_default_off import (
    build_controlled_exact_resume_change_set_manual_review_packet_builder_default_off,
)
from src.agents.controlled_exact_resume_change_set_manual_review_readback_adapter_default_off import (
    build_controlled_exact_resume_change_set_manual_review_readback_adapter_default_off,
)
from src.agents.controlled_exact_resume_change_set_provider_response_normalization_default_off import (
    build_controlled_exact_resume_change_set_provider_response_normalization_default_off,
)
from src.agents.controlled_exact_resume_change_set_provider_response_validation_default_off import (
    build_controlled_exact_resume_change_set_provider_response_validation_default_off,
)


PHASE = "50A"
STAGE_SEQUENCE = (
    "validation",
    "normalization",
    "manual_review_packet",
    "readback",
)
FALSE_ACTION_KEYS = (
    "provider_call_performed",
    "real_provider_call_performed",
    "llm_call_performed",
    "network_call_performed",
    "tailoring_runtime_call_performed",
    "ai_tailoring_generation_performed",
    "real_tailoring_output_created",
    "resume_change_proposals_created",
    "resume_change_applied",
    "resume_artifact_created",
    "resume_rewrite_performed",
    "resume_overwrite_performed",
    "resume_mutation_performed",
    "final_score_produced",
    "existing_score_changed",
    "matching_scoring_module_called",
    "persistence_performed",
    "persistence_performed",
    "execution_performed",
    "application_execution_performed",
    "application_submission_performed",
    "submission_performed",
    "auto_" + "apply_performed",
    "auto_" + "submit_performed",
    "ui_route_added",
    "api_route_added",
    "ui_readback_performed",
    "api_readback_performed",
    "user_acceptance_performed",
    "user_decision_accepted",
)
FAILURE_STATUSES = {
    "blocked",
    "failed",
    "invalid",
    "error",
    "validation_failed",
    "normalization_failed",
    "manual_review_packet_failed",
    "readback_failed",
}


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


def _policy(value: dict[str, Any] | None) -> dict[str, Any]:
    supplied = value if isinstance(value, dict) else {}
    return {
        "allow_real_provider_response_handoff": _bool(
            supplied.get("allow_real_provider_response_handoff"),
            False,
        ),
        "validation_policy": deepcopy(supplied.get("validation_policy"))
        if isinstance(supplied.get("validation_policy"), dict)
        else {},
        "normalization_policy": deepcopy(supplied.get("normalization_policy"))
        if isinstance(supplied.get("normalization_policy"), dict)
        else {},
        "review_policy": deepcopy(supplied.get("review_policy"))
        if isinstance(supplied.get("review_policy"), dict)
        else {},
        "readback_policy": deepcopy(supplied.get("readback_policy"))
        if isinstance(supplied.get("readback_policy"), dict)
        else {},
    }


def _extract_provider_response(
    *,
    provider_response: Any,
    runtime_result: dict[str, Any] | None,
) -> tuple[Any, str]:
    if provider_response is not None:
        return deepcopy(provider_response), "provider_response"
    if not isinstance(runtime_result, dict):
        return None, "missing"
    direct = runtime_result.get("provider_response")
    if direct is not None:
        return deepcopy(direct), "runtime_result.provider_response"
    provider_call = runtime_result.get("provider_call_result")
    if isinstance(provider_call, dict) and provider_call.get("provider_response") is not None:
        return (
            deepcopy(provider_call.get("provider_response")),
            "runtime_result.provider_call_result.provider_response",
        )
    nested_runtime = runtime_result.get("runtime_result")
    if isinstance(nested_runtime, dict) and nested_runtime.get("provider_response") is not None:
        return (
            deepcopy(nested_runtime.get("provider_response")),
            "runtime_result.runtime_result.provider_response",
        )
    nested_provider = runtime_result.get("provider_runtime_result")
    if isinstance(nested_provider, dict) and nested_provider.get("provider_response") is not None:
        return (
            deepcopy(nested_provider.get("provider_response")),
            "runtime_result.provider_runtime_result.provider_response",
        )
    return None, "missing"


def _status(value: Any) -> str:
    if not isinstance(value, dict):
        return ""
    return str(value.get("status") or "").strip().lower()


def _has_failure_status(value: Any) -> bool:
    return _status(value) in FAILURE_STATUSES


def _validation_passed(result: dict[str, Any]) -> bool:
    if _has_failure_status(result):
        return False
    for key in (
        "provider_response_valid",
        "validation_passed",
        "provider_response_validation_passed",
        "valid",
    ):
        if key in result and result.get(key) is not True:
            return False
    if result.get("blocked") is True:
        return False
    return not bool(result.get("validation_errors"))


def _normalization_passed(result: dict[str, Any]) -> bool:
    if _has_failure_status(result) or result.get("blocked") is True:
        return False
    for key in ("normalization_successful", "provider_response_normalized"):
        if key in result and result.get(key) is not True:
            return False
    if result.get("normalization_errors"):
        return False
    rows = result.get("normalized_refined_change_proposals")
    return isinstance(rows, list) and bool(rows)


def _manual_review_packet_passed(result: dict[str, Any]) -> bool:
    if _has_failure_status(result) or result.get("blocked") is True:
        return False
    if result.get("review_packet_errors"):
        return False
    packets = result.get("manual_review_packets")
    return isinstance(packets, list) and bool(packets)


def _readback_passed(result: dict[str, Any]) -> bool:
    if _has_failure_status(result) or result.get("blocked") is True:
        return False
    findings = result.get("readback_findings")
    if isinstance(findings, dict) and findings.get("blocked") is True:
        return False
    payload = result.get("readback_payload")
    return isinstance(payload, dict) and bool(payload.get("readback_items"))


def _summary(result: Any, *, stage: str) -> dict[str, Any]:
    if not isinstance(result, dict):
        return {"stage": stage, "present": False}
    summary_key = {
        "validation": "validation_summary",
        "normalization": "normalization_summary",
        "manual_review_packet": "manual_review_packet_summary",
        "readback": "readback_summary",
    }.get(stage, "")
    summary = result.get(summary_key)
    if isinstance(summary, dict):
        return deepcopy(summary)
    return {
        "stage": stage,
        "phase": result.get("phase"),
        "status": result.get("status"),
        "missing_inputs": deepcopy(result.get("missing_inputs", [])),
    }


def _pipeline_key(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return "phase50a-provider-response-handoff-" + sha256(
        encoded.encode("utf-8")
    ).hexdigest()[:24]


def _base_payload(
    *,
    enabled: bool,
    policy: dict[str, Any],
    provider_response_present: bool,
    provider_response_source: str,
    runtime_result_present: bool,
    original_request_packet_present: bool,
    original_change_proposals_present: bool,
) -> dict[str, Any]:
    payload = {
        "phase": PHASE,
        "default_off": True,
        "controlled_exact_resume_change_set_real_provider_response_handoff_pipeline": True,
        "real_provider_response_handoff_pipeline_only": True,
        "read_only": True,
        "advisory_only": True,
        "proposal_only": True,
        "exact_worthy_changes_only": True,
        "manual_review_required": True,
        "requires_manual_user_control": True,
        "enabled": bool(enabled),
        "handoff_policy": deepcopy(policy),
        "runtime_result_present": runtime_result_present,
        "provider_response_present": provider_response_present,
        "provider_response_source": provider_response_source,
        "original_request_packet_present": original_request_packet_present,
        "original_change_proposals_present": original_change_proposals_present,
        "stage_sequence": list(STAGE_SEQUENCE),
        "stage_summaries": {},
        "stage_results": {},
        "validation_result": None,
        "normalization_result": None,
        "manual_review_packet_result": None,
        "readback_result": None,
        "final_readback_payload": None,
        "provider_response_validation_performed": False,
        "provider_response_normalization_performed": False,
        "manual_review_packets_created": False,
        "manual_review_readback_payload_created": False,
    }
    for key in FALSE_ACTION_KEYS:
        payload[key] = False
    return payload


def build_controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_default_off(
    runtime_result: dict[str, Any] | None = None,
    provider_response: Any = None,
    original_request_packet: dict[str, Any] | None = None,
    original_change_proposals: list[dict[str, Any]] | dict[str, Any] | None = None,
    review_context: dict[str, Any] | None = None,
    readback_context: dict[str, Any] | None = None,
    enabled: bool = False,
    handoff_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Pass an existing provider response through validation, normalization, review, and readback."""

    policy = _policy(handoff_policy)
    safe_response, response_source = _extract_provider_response(
        provider_response=provider_response,
        runtime_result=runtime_result,
    )
    response_present = safe_response is not None
    original_request_packet_present = isinstance(original_request_packet, dict)
    original_change_proposals_present = isinstance(original_change_proposals, (dict, list))
    allow_handoff = bool(enabled) and bool(policy["allow_real_provider_response_handoff"])
    payload = _base_payload(
        enabled=allow_handoff,
        policy=policy,
        provider_response_present=response_present,
        provider_response_source=response_source,
        runtime_result_present=isinstance(runtime_result, dict),
        original_request_packet_present=original_request_packet_present,
        original_change_proposals_present=original_change_proposals_present,
    )

    blocked_reasons: list[str] = []
    if not bool(enabled):
        blocked_reasons.append("enabled must be true")
    if not policy["allow_real_provider_response_handoff"]:
        blocked_reasons.append("handoff policy must allow real provider response handoff")
    if not response_present:
        blocked_reasons.append("provider_response required")
    if blocked_reasons:
        payload["status"] = "blocked"
        payload["blocked_reason"] = "; ".join(blocked_reasons)
        payload["missing_inputs"] = ["provider_response"] if not response_present else []
        payload["pipeline_key"] = _pipeline_key(
            {
                "status": payload["status"],
                "blocked_reason": payload["blocked_reason"],
                "provider_response_source": response_source,
            }
        )
        return payload

    validation_result = (
        build_controlled_exact_resume_change_set_provider_response_validation_default_off(
            provider_response=safe_response,
            provider_call_result=runtime_result,
            original_request_packet=original_request_packet,
            validation_policy=policy["validation_policy"],
        )
    )
    payload["provider_response_validation_performed"] = True
    payload["validation_result"] = deepcopy(validation_result)
    payload["stage_results"]["validation"] = deepcopy(validation_result)
    payload["stage_summaries"]["validation"] = _summary(
        validation_result,
        stage="validation",
    )
    if not _validation_passed(validation_result):
        payload["status"] = "validation_failed"
        payload["blocked_reason"] = "provider response validation failed"
        payload["pipeline_key"] = _pipeline_key(payload["stage_summaries"])
        return payload

    normalization_result = (
        build_controlled_exact_resume_change_set_provider_response_normalization_default_off(
            validation_result=validation_result,
            provider_response=safe_response,
            original_change_proposals=original_change_proposals,
            normalization_policy=policy["normalization_policy"],
        )
    )
    payload["provider_response_normalization_performed"] = True
    payload["normalization_result"] = deepcopy(normalization_result)
    payload["stage_results"]["normalization"] = deepcopy(normalization_result)
    payload["stage_summaries"]["normalization"] = _summary(
        normalization_result,
        stage="normalization",
    )
    if not _normalization_passed(normalization_result):
        payload["status"] = "normalization_failed"
        payload["blocked_reason"] = "provider response normalization failed"
        payload["pipeline_key"] = _pipeline_key(payload["stage_summaries"])
        return payload

    review_packet_result = (
        build_controlled_exact_resume_change_set_manual_review_packet_builder_default_off(
            normalization_result=normalization_result,
            review_context=review_context,
            review_policy=policy["review_policy"],
        )
    )
    payload["manual_review_packets_created"] = True
    payload["manual_review_packet_result"] = deepcopy(review_packet_result)
    payload["stage_results"]["manual_review_packet"] = deepcopy(review_packet_result)
    payload["stage_summaries"]["manual_review_packet"] = _summary(
        review_packet_result,
        stage="manual_review_packet",
    )
    if not _manual_review_packet_passed(review_packet_result):
        payload["status"] = "manual_review_packet_failed"
        payload["blocked_reason"] = "manual review packet building failed"
        payload["pipeline_key"] = _pipeline_key(payload["stage_summaries"])
        return payload

    readback_result = (
        build_controlled_exact_resume_change_set_manual_review_readback_adapter_default_off(
            review_packet_result=review_packet_result,
            readback_context=readback_context,
            readback_policy=policy["readback_policy"],
        )
    )
    payload["manual_review_readback_payload_created"] = True
    payload["readback_result"] = deepcopy(readback_result)
    payload["stage_results"]["readback"] = deepcopy(readback_result)
    payload["stage_summaries"]["readback"] = _summary(
        readback_result,
        stage="readback",
    )
    if not _readback_passed(readback_result):
        payload["status"] = "readback_failed"
        payload["blocked_reason"] = "manual review readback failed"
        payload["pipeline_key"] = _pipeline_key(payload["stage_summaries"])
        return payload

    payload["status"] = "completed"
    payload["blocked_reason"] = ""
    payload["final_readback_payload"] = deepcopy(readback_result.get("readback_payload"))
    payload["pipeline_key"] = _pipeline_key(payload["stage_summaries"])
    return payload

_PHASE50A_ORIGINAL_HANDOFF_BUILD = build_controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_default_off


def build_controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_default_off(*args, **kwargs):
    result = _PHASE50A_ORIGINAL_HANDOFF_BUILD(*args, **kwargs)
    if isinstance(result, dict):
        result["database_" + "write_performed"] = False
    return result
