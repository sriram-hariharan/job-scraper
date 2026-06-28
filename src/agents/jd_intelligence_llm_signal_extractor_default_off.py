"""Default-off JD intelligence signal extractor with injected LLM response support."""

from __future__ import annotations

from copy import deepcopy
import json
from typing import Any


PHASE = "34A"
PROMPT_VERSION = "phase34a-jd-intelligence-signal-extractor-v1"

LIST_FIELDS = (
    "required_skills",
    "preferred_skills",
    "responsibilities",
    "tools",
    "location_constraints",
    "visa_constraints",
    "red_flags",
    "resume_evidence_needed",
)
TEXT_FIELDS = ("seniority", "domain")


def _text(value: Any) -> str:
    return str(value or "").strip()


def _plain_dict(value: Any) -> dict[str, Any]:
    return deepcopy(value) if isinstance(value, dict) else {}


def _list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [_text(item) for item in value if _text(item)]
    if isinstance(value, tuple):
        return [_text(item) for item in value if _text(item)]
    text = _text(value)
    return [text] if text else []


def _optional_text(value: Any) -> str | None:
    text = _text(value)
    return text or None


def _confidence(value: Any) -> float | str | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return max(0.0, min(1.0, float(value)))
    text = _text(value)
    if not text:
        return None
    try:
        return max(0.0, min(1.0, float(text)))
    except ValueError:
        return text


def _json_from_text(value: str) -> dict[str, Any] | None:
    text = value.strip()
    if not text:
        return None
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end <= start:
            return None
        try:
            payload = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None
    return payload if isinstance(payload, dict) else None


def _response_dict(value: Any) -> tuple[dict[str, Any], str]:
    if isinstance(value, dict):
        for key in ("raw_response", "content", "text", "message"):
            nested = value.get(key)
            if isinstance(nested, str):
                parsed = _json_from_text(nested)
                if parsed is not None:
                    combined = dict(value)
                    for key, value in parsed.items():
                        combined[key] = value
                    return combined, "parsed"
        return deepcopy(value), "parsed"
    if isinstance(value, str):
        parsed = _json_from_text(value)
        if parsed is not None:
            return parsed, "parsed"
        return {}, "unparseable"
    if value is None:
        return {}, "not_supplied"
    return {}, "unsupported_response_type"


def _signals(source: dict[str, Any]) -> dict[str, Any]:
    signals: dict[str, Any] = {field: _list(source.get(field)) for field in LIST_FIELDS}
    for field in TEXT_FIELDS:
        signals[field] = _optional_text(source.get(field))
    signals["confidence"] = _confidence(
        source.get("confidence", source.get("extraction_confidence"))
    )
    return signals


def _request_packet(
    *,
    jd_text: str,
    job_record: dict[str, Any],
    extraction_policy: dict[str, Any],
) -> dict[str, Any]:
    return {
        "phase": PHASE,
        "prompt_version": PROMPT_VERSION,
        "task": "extract_structured_jd_intelligence_signals",
        "jd_text": jd_text,
        "job_record": deepcopy(job_record),
        "extraction_policy": deepcopy(extraction_policy),
        "expected_fields": [*LIST_FIELDS, *TEXT_FIELDS, "confidence"],
        "instructions": (
            "Return JSON with required_skills, preferred_skills, responsibilities, "
            "seniority, domain, tools, location_constraints, visa_constraints, "
            "red_flags, resume_evidence_needed, and confidence. Do not score, "
            "rank, tailor, rewrite, persist, execute, or submit applications."
        ),
    }


def _key(
    *,
    jd_text_present: bool,
    llm_enabled: bool,
    parse_status: str,
    extraction_ready: bool,
) -> str:
    return "|".join(
        (
            f"phase={PHASE}",
            f"jd_text_present={jd_text_present}",
            f"llm_enabled={llm_enabled}",
            f"parse_status={parse_status}",
            f"ready={extraction_ready}",
        )
    )


def build_jd_intelligence_llm_signal_extractor_default_off(
    jd_text: Any = None,
    job_record: dict[str, Any] | None = None,
    enable_llm: bool = False,
    provider_callable: Any = None,
    provider_response: Any = None,
    extraction_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build or parse read-only JD intelligence signals with explicit LLM enable."""

    safe_jd_text = _text(jd_text)
    safe_job_record = _plain_dict(job_record)
    safe_policy = _plain_dict(extraction_policy)
    jd_text_present = bool(safe_jd_text)
    llm_enabled = enable_llm is True
    provider_callable_present = callable(provider_callable)
    provider_response_present = provider_response is not None
    provider_callable_invoked = False
    missing_inputs: list[str] = []
    blocked_reasons: list[str] = []
    parse_status = "not_attempted"
    extraction_source = "blocked"
    response_payload: dict[str, Any] = {}

    request_packet = _request_packet(
        jd_text=safe_jd_text,
        job_record=safe_job_record,
        extraction_policy=safe_policy,
    )

    if not jd_text_present:
        missing_inputs.append("jd_text")
        blocked_reasons.append("jd_text is required")
    elif not llm_enabled:
        blocked_reasons.append("explicit LLM enable is required")
    elif provider_response_present:
        response_payload, parse_status = _response_dict(provider_response)
        extraction_source = "provider_response"
    elif provider_callable_present:
        provider_callable_invoked = True
        try:
            response_payload, parse_status = _response_dict(
                provider_callable(deepcopy(request_packet))
            )
            extraction_source = "provider_callable"
        except Exception as exc:  # defensive: caller-supplied callable only
            response_payload = {}
            parse_status = f"provider_callable_error:{type(exc).__name__}"
            extraction_source = "provider_callable"
    else:
        blocked_reasons.append("provider_response or provider_callable is required")

    if llm_enabled and jd_text_present and parse_status == "not_attempted":
        parse_status = "not_supplied"
    if parse_status not in ("parsed", "not_attempted") and not blocked_reasons:
        blocked_reasons.append(parse_status)

    jd_signals = _signals(response_payload if parse_status == "parsed" else {})
    extraction_ready = parse_status == "parsed" and not missing_inputs
    if not extraction_ready and not blocked_reasons and missing_inputs:
        blocked_reasons.append("missing required inputs")

    payload = {
        "phase": PHASE,
        "default_off": True,
        "jd_intelligence_llm_signal_extractor": True,
        "llm_capable": True,
        "llm_enabled": llm_enabled,
        "read_only": True,
        "advisory_only": True,
        "requires_manual_user_control": True,
        "jd_text_present": jd_text_present,
        "job_record_present": bool(safe_job_record),
        "request_packet": request_packet,
        "provider_response_present": provider_response_present,
        "provider_callable_present": provider_callable_present,
        "provider_callable_invoked": provider_callable_invoked,
        "provider_response_parse_status": parse_status,
        "jd_signals": deepcopy(jd_signals),
        "required_skills": deepcopy(jd_signals["required_skills"]),
        "preferred_skills": deepcopy(jd_signals["preferred_skills"]),
        "responsibilities": deepcopy(jd_signals["responsibilities"]),
        "seniority": jd_signals["seniority"],
        "domain": jd_signals["domain"],
        "tools": deepcopy(jd_signals["tools"]),
        "location_constraints": deepcopy(jd_signals["location_constraints"]),
        "visa_constraints": deepcopy(jd_signals["visa_constraints"]),
        "red_flags": deepcopy(jd_signals["red_flags"]),
        "resume_evidence_needed": deepcopy(jd_signals["resume_evidence_needed"]),
        "confidence": jd_signals["confidence"],
        "extraction_ready": extraction_ready,
        "extraction_source": extraction_source if extraction_ready else "blocked",
        "missing_inputs": list(missing_inputs),
        "blocked_reasons": list(blocked_reasons),
        "extractor_findings": {
            "request_packet_built": True,
            "provider_callable_supplied": provider_callable_present,
            "provider_response_supplied": provider_response_present,
            "provider_callable_invoked": provider_callable_invoked,
            "parsed_signal_field_count": sum(
                1
                for value in jd_signals.values()
                if value not in (None, "", [], {})
            ),
            "final_score_created": False,
            "final_score_changed": False,
        },
        "extractor_key": _key(
            jd_text_present=jd_text_present,
            llm_enabled=llm_enabled,
            parse_status=parse_status,
            extraction_ready=extraction_ready,
        ),
        "stage_execution_performed": False,
        "relevance_prefilter_performed": False,
        "final_scoring_performed": False,
        "tailoring_opportunity_check_performed": False,
        "tailoring_runtime_call_performed": False,
        "ai_tailoring_generation_performed": False,
        "real_tailoring_output_created": False,
        "resume_rewrite_performed": False,
        "resume_overwrite_performed": False,
        "resume_mutation_performed": False,
        "application_submission_performed": False,
        "database_write_performed": False,
        "persistence_performed": False,
        "execution_performed": False,
        "submission_performed": False,
        "auto_apply_performed": False,
        "auto_submit_performed": False,
    }
    return payload
