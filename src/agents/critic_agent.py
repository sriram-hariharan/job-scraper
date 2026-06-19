from __future__ import annotations

import os
import re
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List

from src.agents import llmops, trace as trace_store
from src.agents.resume_match_agent import (
    TRACE_ENABLED_ENV,
    TRACE_STRICT_ENV,
    _truthy,
)
from src.pipeline.resume_selection_credibility import parse_float


AGENT_NAME = "Critic Agent"
AGENT_VERSION = "phase_5a_v1"

DECISIONS = {"approve", "reject", "downgrade_to_guidance"}
REASON_CODES = {
    "unsupported_claim",
    "fake_tool_or_domain",
    "exaggerated_scope",
    "weak_score_lift",
    "low_readability",
    "ats_risk",
    "not_actionable",
    "missing_evidence",
    "safe_guidance_only",
}

_TECH_OR_DOMAIN_TERMS = {
    "airflow",
    "aws",
    "azure",
    "databricks",
    "dbt",
    "docker",
    "dynamodb",
    "eks",
    "gcp",
    "graphql",
    "kafka",
    "kubernetes",
    "lambda",
    "langchain",
    "llm",
    "mlflow",
    "postgresql",
    "python",
    "pytorch",
    "react",
    "redis",
    "snowflake",
    "spark",
    "sql",
    "tensorflow",
    "terraform",
    "typescript",
}

_SCOPE_PATTERNS = [
    re.compile(r"\b(company[-\s]?wide|enterprise[-\s]?wide|global|organization[-\s]?wide)\b", re.I),
    re.compile(r"\bowned\b.*\b(end[-\s]?to[-\s]?end|roadmap|strategy)\b", re.I),
]


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_term(value: Any) -> str:
    return re.sub(r"[^a-z0-9+#./-]+", " ", _clean_text(value).lower()).strip()


def _normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", _clean_text(value).lower()).strip()


def _as_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [_clean_text(item) for item in value if _clean_text(item)]
    return [_clean_text(value)] if _clean_text(value) else []


def _joined_allowed_text(input_payload: Dict[str, Any]) -> str:
    pieces: List[str] = []
    pieces.extend(_as_list(input_payload.get("original_resume_evidence")))
    pieces.extend(_as_list(input_payload.get("jd_required_skills")))
    pieces.extend(_as_list(input_payload.get("jd_preferred_skills")))
    pieces.append(_clean_text(input_payload.get("source_bullet")))
    return _normalize_text(" ".join(piece for piece in pieces if piece))


def _evidence_text(input_payload: Dict[str, Any]) -> str:
    pieces = _as_list(input_payload.get("original_resume_evidence"))
    pieces.append(_clean_text(input_payload.get("source_bullet")))
    return _normalize_text(" ".join(piece for piece in pieces if piece))


def _allowed_terms(input_payload: Dict[str, Any]) -> set[str]:
    terms: set[str] = set()
    for key in ("jd_required_skills", "jd_preferred_skills"):
        for value in _as_list(input_payload.get(key)):
            normalized = _normalize_term(value)
            if normalized:
                terms.add(normalized)
    allowed_text = _joined_allowed_text(input_payload)
    for term in _TECH_OR_DOMAIN_TERMS:
        if re.search(rf"\b{re.escape(term)}\b", allowed_text):
            terms.add(term)
    return terms


def _proposed_terms(proposed_text: str) -> set[str]:
    normalized = _normalize_text(proposed_text)
    terms: set[str] = set()
    for term in _TECH_OR_DOMAIN_TERMS:
        if re.search(rf"\b{re.escape(term)}\b", normalized):
            terms.add(term)
    return terms


def _unsupported_terms(input_payload: Dict[str, Any]) -> List[str]:
    proposed_terms = _proposed_terms(_clean_text(input_payload.get("proposed_text")))
    allowed_text = _joined_allowed_text(input_payload)
    allowed_terms = _allowed_terms(input_payload)
    unsupported = []
    for term in sorted(proposed_terms):
        if term in allowed_terms or re.search(rf"\b{re.escape(term)}\b", allowed_text):
            continue
        unsupported.append(term)
    return unsupported


def _numeric_claims(text: str) -> List[str]:
    return re.findall(r"\b\d+(?:\.\d+)?\s*%|\$\s*\d+(?:[.,]\d+)*(?:\s*[kmb])?\b", text, flags=re.I)


def _unsupported_numeric_claims(input_payload: Dict[str, Any]) -> List[str]:
    proposed_claims = _numeric_claims(_clean_text(input_payload.get("proposed_text")))
    evidence = _evidence_text(input_payload)
    unsupported = []
    for claim in proposed_claims:
        normalized_claim = re.sub(r"\s+", "", claim.lower())
        normalized_evidence = re.sub(r"\s+", "", evidence.lower())
        if normalized_claim not in normalized_evidence:
            unsupported.append(claim)
    return unsupported


def _evidence_spans(input_payload: Dict[str, Any]) -> List[str]:
    spans = []
    for value in _as_list(input_payload.get("original_resume_evidence")):
        spans.append(value[:240])
    source_bullet = _clean_text(input_payload.get("source_bullet"))
    if source_bullet and source_bullet not in spans:
        spans.append(source_bullet[:240])
    return spans[:5]


def build_critic_agent_input_payload(
    *,
    suggestion_id: str,
    original_resume_evidence: Iterable[str] | str | None = None,
    jd_required_skills: Iterable[str] | str | None = None,
    jd_preferred_skills: Iterable[str] | str | None = None,
    proposed_text: str = "",
    source_bullet: str = "",
    projected_score_delta: Any = None,
    suggestion_type: str = "patch_ready",
    pipeline_run_id: str = "",
    owner_user_id: str = "",
    source_artifact_path: str = "",
) -> Dict[str, Any]:
    return {
        "agent_name": AGENT_NAME,
        "agent_version": AGENT_VERSION,
        "suggestion_id": _clean_text(suggestion_id),
        "pipeline_run_id": _clean_text(pipeline_run_id),
        "owner_user_id": _clean_text(owner_user_id),
        "original_resume_evidence": _as_list(original_resume_evidence),
        "jd_required_skills": _as_list(jd_required_skills),
        "jd_preferred_skills": _as_list(jd_preferred_skills),
        "proposed_text": _clean_text(proposed_text),
        "source_bullet": _clean_text(source_bullet),
        "projected_score_delta": parse_float(projected_score_delta),
        "suggestion_type": _clean_text(suggestion_type) or "patch_ready",
        "source_artifact_path": _clean_text(source_artifact_path),
    }


def evaluate_critic_suggestion(input_payload: Dict[str, Any]) -> Dict[str, Any]:
    reason_codes: List[str] = []
    notes: List[str] = []
    proposed_text = _clean_text(input_payload.get("proposed_text"))
    suggestion_type = _clean_text(input_payload.get("suggestion_type")) or "patch_ready"
    score_delta = parse_float(input_payload.get("projected_score_delta"))
    evidence = _evidence_text(input_payload)
    allowed_text = _joined_allowed_text(input_payload)

    if not proposed_text:
        reason_codes.append("not_actionable")
    if not evidence:
        reason_codes.append("missing_evidence")

    unsupported_terms = _unsupported_terms(input_payload)
    if unsupported_terms:
        reason_codes.append("fake_tool_or_domain")
        notes.append(f"Unsupported tool/domain terms: {', '.join(unsupported_terms)}")

    unsupported_claims = _unsupported_numeric_claims(input_payload)
    if unsupported_claims:
        reason_codes.append("unsupported_claim")
        notes.append(f"Unsupported numeric claims: {', '.join(unsupported_claims)}")

    for pattern in _SCOPE_PATTERNS:
        if pattern.search(proposed_text) and not pattern.search(allowed_text):
            reason_codes.append("exaggerated_scope")
            break

    if suggestion_type == "patch_ready" and score_delta <= 0:
        reason_codes.append("weak_score_lift")

    if proposed_text and len(proposed_text.split()) < 4:
        reason_codes.append("low_readability")

    reason_codes = sorted(set(reason_codes), key=reason_codes.index)
    hard_reject_reasons = {
        "unsupported_claim",
        "fake_tool_or_domain",
        "exaggerated_scope",
        "weak_score_lift",
        "low_readability",
        "not_actionable",
        "missing_evidence",
    }

    if any(reason in hard_reject_reasons for reason in reason_codes):
        decision = "reject"
        confidence = 0.9
    elif suggestion_type != "patch_ready":
        decision = "downgrade_to_guidance"
        reason_codes.append("safe_guidance_only")
        confidence = 0.76
    else:
        decision = "approve"
        confidence = 0.86

    return {
        "suggestion_id": _clean_text(input_payload.get("suggestion_id")),
        "decision": decision,
        "confidence": confidence,
        "reason_codes": reason_codes,
        "evidence_spans": _evidence_spans(input_payload),
        "score_delta": score_delta,
        "notes": "; ".join(notes),
    }


def build_critic_agent_validation_payload(
    *,
    input_payload: Dict[str, Any],
    output_payload: Dict[str, Any],
) -> Dict[str, Any]:
    reason_codes: List[str] = []
    stable_output_keys = {
        "suggestion_id",
        "decision",
        "confidence",
        "reason_codes",
        "evidence_spans",
        "score_delta",
        "notes",
    }.issubset(set(output_payload.keys()))
    if not stable_output_keys:
        reason_codes.append("missing_output_keys")

    decision_supported = output_payload.get("decision") in DECISIONS
    if not decision_supported:
        reason_codes.append("unsupported_decision")

    output_reason_codes = set(output_payload.get("reason_codes", []) or [])
    reason_codes_supported = output_reason_codes.issubset(REASON_CODES)
    if not reason_codes_supported:
        reason_codes.append("unsupported_reason_code")

    suggestion_id_matches = (
        _clean_text(input_payload.get("suggestion_id"))
        == _clean_text(output_payload.get("suggestion_id"))
    )
    if not suggestion_id_matches:
        reason_codes.append("suggestion_id_mismatch")

    validation_status = "passed" if not reason_codes else "failed"
    return {
        "stable_output_keys": stable_output_keys,
        "decision_supported": decision_supported,
        "reason_codes_supported": reason_codes_supported,
        "suggestion_id_matches": suggestion_id_matches,
        "validation_status": validation_status,
        "reason_codes": reason_codes,
    }


def render_critic_decision(input_payload: Dict[str, Any]) -> Dict[str, Any]:
    output_payload = evaluate_critic_suggestion(input_payload)
    validation_payload = build_critic_agent_validation_payload(
        input_payload=input_payload,
        output_payload=output_payload,
    )
    return {
        "input": input_payload,
        "output": output_payload,
        "validation": validation_payload,
    }


def build_critic_agent_summary_payload(
    *,
    input_payloads: List[Dict[str, Any]],
    output_payloads: List[Dict[str, Any]],
    validation_payloads: List[Dict[str, Any]],
) -> Dict[str, Any]:
    decision_counts: Dict[str, int] = {}
    reason_counts: Dict[str, int] = {}
    for output in output_payloads:
        decision = _clean_text(output.get("decision")) or "unknown"
        decision_counts[decision] = decision_counts.get(decision, 0) + 1
        for reason in output.get("reason_codes", []) or []:
            reason_key = _clean_text(reason)
            if reason_key:
                reason_counts[reason_key] = reason_counts.get(reason_key, 0) + 1
    return {
        "agent_name": AGENT_NAME,
        "agent_version": AGENT_VERSION,
        "pipeline_run_id": _clean_text(input_payloads[0].get("pipeline_run_id")) if input_payloads else "",
        "owner_user_id": _clean_text(input_payloads[0].get("owner_user_id")) if input_payloads else "",
        "suggestion_count": len(input_payloads),
        "decision_counts": dict(sorted(decision_counts.items())),
        "reason_counts": dict(sorted(reason_counts.items())),
        "validation_status": "passed"
        if all(payload.get("validation_status") == "passed" for payload in validation_payloads)
        else "failed",
    }


def agent_trace_enabled(env: Dict[str, str] | None = None) -> bool:
    env_map = env if env is not None else os.environ
    return _truthy(env_map.get(TRACE_ENABLED_ENV))


def agent_trace_strict(env: Dict[str, str] | None = None) -> bool:
    env_map = env if env is not None else os.environ
    return _truthy(env_map.get(TRACE_STRICT_ENV))


def trace_context_from_env(env: Dict[str, str] | None = None) -> Dict[str, str]:
    env_map = env if env is not None else os.environ
    pipeline_run_id = (
        _clean_text(env_map.get("JOB_APP_PIPELINE_RUN_ID"))
        or _clean_text(env_map.get("JOB_STACK_USER_PIPELINE_RUN_ID"))
    )
    owner_user_id = _clean_text(env_map.get("JOB_STACK_OWNER_USER_ID"))
    context_id = _clean_text(env_map.get("APPLYLENS_AGENT_CONTEXT_ID"))
    if not context_id and pipeline_run_id:
        context_id = f"critic:{pipeline_run_id}"
    return {
        "pipeline_run_id": pipeline_run_id,
        "owner_user_id": owner_user_id,
        "context_id": context_id,
    }


def record_critic_agent_trace(
    *,
    input_payloads: List[Dict[str, Any]],
    env: Dict[str, str] | None = None,
    trace_module: Any = trace_store,
) -> Dict[str, Any]:
    env_map = env if env is not None else os.environ
    if not agent_trace_enabled(env_map):
        return {"attempted": False, "reason": "trace_disabled"}

    context = trace_context_from_env(env_map)
    if not context["owner_user_id"] or not context["pipeline_run_id"]:
        return {"attempted": False, "reason": "missing_trace_context", **context}

    try:
        started_at = _utc_now_iso()
        enriched_inputs = [
            {
                **payload,
                "pipeline_run_id": payload.get("pipeline_run_id") or context["pipeline_run_id"],
                "owner_user_id": payload.get("owner_user_id") or context["owner_user_id"],
            }
            for payload in input_payloads
        ]
        rendered = [render_critic_decision(payload) for payload in enriched_inputs]
        output_payload = {
            "decisions": [item["output"] for item in rendered],
        }
        validation_payload = {
            "validation_status": "passed"
            if all(item["validation"].get("validation_status") == "passed" for item in rendered)
            else "failed",
            "validations": [item["validation"] for item in rendered],
        }
        summary_payload = build_critic_agent_summary_payload(
            input_payloads=enriched_inputs,
            output_payloads=output_payload["decisions"],
            validation_payloads=validation_payload["validations"],
        )

        run_payload = trace_module.create_agent_run(
            record={
                "owner_user_id": context["owner_user_id"],
                "pipeline_run_id": context["pipeline_run_id"],
                "context_id": context["context_id"],
                "status": "running",
                "started_at": started_at,
                "summary_json": summary_payload,
            }
        )
        agent_run_id = _clean_text((run_payload.get("run") or {}).get("agent_run_id"))
        if not agent_run_id:
            raise RuntimeError("Agent trace run did not return agent_run_id.")

        llmops_metadata = llmops.build_llmops_metadata(
            model_provider="deterministic",
            model_name="critic_rules",
            agent_name=AGENT_NAME,
            agent_version=AGENT_VERSION,
            schema_validation_status=validation_payload.get("validation_status", ""),
        )
        step_record = llmops.merge_llmops_into_agent_step_kwargs(
            {
                "agent_run_id": agent_run_id,
                "owner_user_id": context["owner_user_id"],
                "pipeline_run_id": context["pipeline_run_id"],
                "context_id": context["context_id"],
                "agent_name": AGENT_NAME,
                "agent_version": AGENT_VERSION,
                "input_json": {"suggestions": enriched_inputs},
                "status": "running",
                "started_at": started_at,
            },
            llmops_metadata,
        )
        step_payload = trace_module.record_agent_step(
            record=step_record
        )
        agent_step_id = _clean_text((step_payload.get("step") or {}).get("agent_step_id"))
        if not agent_step_id:
            raise RuntimeError("Agent trace step did not return agent_step_id.")

        completed_at = _utc_now_iso()
        trace_module.complete_agent_step(
            agent_step_id=agent_step_id,
            owner_user_id=context["owner_user_id"],
            output_json=output_payload,
            validation_json=validation_payload,
            completed_at=completed_at,
        )
        trace_module.complete_agent_run(
            agent_run_id=agent_run_id,
            owner_user_id=context["owner_user_id"],
            summary_json=summary_payload,
            completed_at=completed_at,
        )
        return {
            "attempted": True,
            "recorded": True,
            "agent_run_id": agent_run_id,
            "agent_step_id": agent_step_id,
            "summary": summary_payload,
            "validation": validation_payload,
        }
    except Exception as exc:
        if agent_trace_strict(env_map):
            raise
        return {"attempted": True, "recorded": False, "warning": str(exc)}


def _critic_guardrail_safety_metadata() -> Dict[str, bool]:
    return {
        "dry_run_only": True,
        "deterministic_only": True,
        "did_call_llm": False,
        "did_mutate_resume": False,
        "did_mutate_scoring": False,
        "did_change_ranking": False,
        "did_mutate_queue": False,
        "did_mutate_approval": False,
        "did_execute_application": False,
        "did_submit_application": False,
        "pipeline_wiring_added": False,
    }


def _critic_guardrail_suggestion_list(value: Any) -> List[Dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item or {}) for item in value if isinstance(item, dict)]


def _critic_guardrail_text_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [_clean_text(item) for item in value if _clean_text(item)]
    if isinstance(value, tuple):
        return [_clean_text(item) for item in value if _clean_text(item)]
    if isinstance(value, dict):
        return [_clean_text(item) for item in value.values() if _clean_text(item)]
    return [_clean_text(value)] if _clean_text(value) else []


def _critic_guardrail_float(value: Any) -> float:
    try:
        return max(0.0, min(1.0, float(value or 0.0)))
    except (TypeError, ValueError):
        return 0.0


def _critic_guardrail_int(value: Any) -> int:
    try:
        return max(0, int(float(value or 0)))
    except (TypeError, ValueError):
        return 0


def _critic_guardrail_resume_evidence_text(rows: List[Dict[str, Any]]) -> str:
    pieces: List[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        for field_name in (
            "raw_text",
            "normalized_text",
            "evidence_text",
            "summary",
            "bullets",
            "quantified_bullets",
            "skills",
            "tools",
            "methods",
            "workflows",
            "business_contexts",
            "stakeholder_contexts",
            "ownership_signals",
            "seniority_signals",
            "analytics_ml_signals",
            "domain_signals",
            "tooling_signals",
        ):
            pieces.extend(_critic_guardrail_text_list(row.get(field_name)))
    return _normalize_text(" ".join(pieces))


def _critic_guardrail_jd_terms(jd_source: Dict[str, Any]) -> List[str]:
    terms: List[str] = []
    for field_name in (
        "required_skills",
        "preferred_skills",
        "required_tools",
        "preferred_tools",
        "workflows",
        "methods",
        "business_contexts",
        "stakeholder_contexts",
        "ownership_signals",
        "seniority_signals",
    ):
        terms.extend(_critic_guardrail_text_list(jd_source.get(field_name)))
    return list(dict.fromkeys(term for term in terms if term))


def _critic_guardrail_unsupported_risks(
    suggestion: Dict[str, Any],
    tailoring_payload: Dict[str, Any],
) -> List[str]:
    risks = [
        _clean_text(item)
        for item in list(suggestion.get("risk_flags") or [])
        if _clean_text(item)
    ]
    suggestion_links = {
        (
            _clean_text(link.get("field")),
            _clean_text(link.get("signal")),
        )
        for link in list(suggestion.get("jd_signal_links") or [])
        if isinstance(link, dict)
    }
    for risk in list(tailoring_payload.get("unsupported_claim_risks") or []):
        if not isinstance(risk, dict):
            continue
        risk_key = (_clean_text(risk.get("field")), _clean_text(risk.get("signal")))
        if suggestion_links and risk_key not in suggestion_links:
            continue
        risk_value = _clean_text(risk.get("risk")) or "unsupported_claim"
        risks.append(risk_value)
    return list(dict.fromkeys(risks))


def _critic_guardrail_ats_risks(suggestion: Dict[str, Any]) -> List[str]:
    text = _clean_text(suggestion.get("suggested_text"))
    risks: List[str] = []
    if len(text.split()) > 45:
        risks.append("long_bullet")
    if re.search(r"[^\w\s.,;:()/%$+#&-]", text):
        risks.append("special_character_noise")
    return risks


def _critic_guardrail_readability_risks(suggestion: Dict[str, Any]) -> List[str]:
    text = _clean_text(suggestion.get("suggested_text"))
    risks: List[str] = []
    if text and len(text.split()) < 4:
        risks.append("too_short")
    if text and not re.search(r"[aeiou]", text, re.I):
        risks.append("low_readability")
    return risks


def _critic_guardrail_decision(
    *,
    suggestion: Dict[str, Any],
    tailoring_payload: Dict[str, Any],
    evidence_text: str,
) -> Dict[str, Any]:
    suggestion_id = _clean_text(suggestion.get("suggestion_id"))
    patch_ready = bool(suggestion.get("patch_ready"))
    projected_delta = parse_float(suggestion.get("projected_score_delta"))
    evidence_spans = [
        _clean_text(item)
        for item in list(suggestion.get("evidence_spans") or [])
        if _clean_text(item)
    ]
    suggested_text = _clean_text(suggestion.get("suggested_text"))
    original_text = _clean_text(suggestion.get("original_text"))
    reason_codes: List[str] = []
    notes: List[str] = []

    unsupported_risks = _critic_guardrail_unsupported_risks(suggestion, tailoring_payload)
    ats_risks = _critic_guardrail_ats_risks(suggestion)
    readability_risks = _critic_guardrail_readability_risks(suggestion)
    span_supported = any(_normalize_text(span) and _normalize_text(span) in evidence_text for span in evidence_spans)
    text_supported = bool(
        suggested_text
        and (
            _normalize_text(suggested_text) in evidence_text
            or _normalize_text(original_text) in evidence_text
            or span_supported
        )
    )

    if not suggested_text:
        reason_codes.append("not_actionable")
    if not evidence_spans or not text_supported:
        reason_codes.append("missing_evidence")
    if projected_delta <= 0 and patch_ready:
        reason_codes.append("weak_score_lift")
    if any(risk in unsupported_risks for risk in {"unsupported_tool", "unsupported_metric", "unsupported_domain_or_context", "unsupported_claim"}):
        reason_codes.append("unsupported_claim")
        notes.append("Unsupported claim risk detected in dry-run suggestion.")
    if "inflated_ownership" in unsupported_risks or any(pattern.search(suggested_text) for pattern in _SCOPE_PATTERNS):
        reason_codes.append("exaggerated_scope")
    if ats_risks:
        reason_codes.append("ats_risk")
    if readability_risks:
        reason_codes.append("low_readability")

    reason_codes = list(dict.fromkeys(reason_codes))
    hard_reject = {
        "unsupported_claim",
        "exaggerated_scope",
        "not_actionable",
    }
    if any(reason in hard_reject for reason in reason_codes):
        decision = "reject"
        final_patch_ready = False
        confidence = 0.9
    elif "missing_evidence" in reason_codes or "weak_score_lift" in reason_codes or "low_readability" in reason_codes or not patch_ready:
        decision = "downgrade_to_guidance"
        final_patch_ready = False
        confidence = 0.78
        if not reason_codes:
            reason_codes.append("safe_guidance_only")
    else:
        decision = "approve"
        final_patch_ready = True
        confidence = 0.86

    return {
        "suggestion_id": suggestion_id,
        "decision": decision,
        "confidence": confidence,
        "reason_codes": reason_codes,
        "evidence_spans": evidence_spans[:5],
        "notes": "; ".join(notes),
        "original_patch_ready": patch_ready,
        "final_patch_ready": final_patch_ready,
    }


def build_critic_guardrail_dry_run_payload(
    *,
    tailoring_suggestion_payload: Dict[str, Any] | None = None,
    jd_intelligence: Dict[str, Any] | None = None,
    jd_signals: Dict[str, Any] | None = None,
    resume_variants: List[Dict[str, Any]] | None = None,
    resume_evidence_rows: List[Dict[str, Any]] | None = None,
    context_id: str = "",
    job_id: str = "",
) -> Dict[str, Any]:
    """Validate tailoring suggestions in memory without applying or storing decisions."""

    tailoring_payload = deepcopy(tailoring_suggestion_payload or {})
    jd_source = deepcopy(jd_intelligence if jd_intelligence is not None else jd_signals or {})
    resume_rows = deepcopy(resume_variants if resume_variants is not None else resume_evidence_rows or [])
    if not isinstance(tailoring_payload, dict):
        tailoring_payload = {}
    if not isinstance(jd_source, dict):
        jd_source = {}
    if not isinstance(resume_rows, list):
        resume_rows = []

    source_fields_used = []
    if tailoring_payload:
        source_fields_used.append("tailoring_suggestion_payload")
    if jd_source:
        source_fields_used.append("jd_intelligence")
    if resume_rows:
        source_fields_used.append("resume_evidence_rows")

    suggestion_groups = [
        _critic_guardrail_suggestion_list(tailoring_payload.get("patch_ready_suggestions")),
        _critic_guardrail_suggestion_list(tailoring_payload.get("guidance_only_suggestions")),
        _critic_guardrail_suggestion_list(tailoring_payload.get("rejected_suggestions")),
    ]
    suggestions = [item for group in suggestion_groups for item in group]
    evidence_text = _critic_guardrail_resume_evidence_text(resume_rows)
    evidence_gaps = [
        _clean_text(item)
        for item in list(tailoring_payload.get("missing_evidence") or [])
        if _clean_text(item)
    ]

    if not tailoring_payload or not suggestions:
        missing = ["tailoring_suggestions_missing"]
        if not tailoring_payload:
            missing.append("tailoring_payload_missing")
        return {
            "critic_status": "insufficient_evidence",
            "approved_suggestions": [],
            "downgraded_suggestions": [],
            "rejected_suggestions": [],
            "reason_codes": missing,
            "unsupported_claim_risks": [],
            "ats_risks": [],
            "readability_risks": [],
            "evidence_gaps": list(dict.fromkeys(evidence_gaps + missing)),
            "confidence": 0.0,
            "rationale": "Critic guardrail dry-run has no tailoring suggestions to validate.",
            "source_fields_used": source_fields_used,
            "context_id": _clean_text(context_id),
            "job_id": _clean_text(job_id),
            "safety_metadata": _critic_guardrail_safety_metadata(),
        }

    if not evidence_text:
        evidence_gaps.append("resume_evidence_missing")
    if not _critic_guardrail_jd_terms(jd_source):
        evidence_gaps.append("jd_signals_missing")

    approved: List[Dict[str, Any]] = []
    downgraded: List[Dict[str, Any]] = []
    rejected: List[Dict[str, Any]] = []
    reason_codes: List[str] = []
    unsupported_claim_risks: List[str] = []
    ats_risks: List[str] = []
    readability_risks: List[str] = []

    for suggestion in suggestions:
        decision = _critic_guardrail_decision(
            suggestion=suggestion,
            tailoring_payload=tailoring_payload,
            evidence_text=evidence_text,
        )
        reason_codes.extend(decision.get("reason_codes") or [])
        unsupported_claim_risks.extend(_critic_guardrail_unsupported_risks(suggestion, tailoring_payload))
        ats_risks.extend(_critic_guardrail_ats_risks(suggestion))
        readability_risks.extend(_critic_guardrail_readability_risks(suggestion))
        if decision["decision"] == "approve":
            approved.append(decision)
        elif decision["decision"] == "reject":
            rejected.append(decision)
        else:
            downgraded.append(decision)

    if rejected:
        critic_status = "rejected"
    elif downgraded:
        critic_status = "needs_guidance"
    elif approved:
        critic_status = "approved"
    else:
        critic_status = "insufficient_evidence"

    confidence_values = [
        float(item.get("confidence", 0.0) or 0.0)
        for item in approved + downgraded + rejected
    ]
    confidence = round(sum(confidence_values) / len(confidence_values), 4) if confidence_values else 0.0
    return {
        "critic_status": critic_status,
        "approved_suggestions": approved,
        "downgraded_suggestions": downgraded,
        "rejected_suggestions": rejected,
        "reason_codes": list(dict.fromkeys(reason_codes)),
        "unsupported_claim_risks": list(dict.fromkeys(unsupported_claim_risks)),
        "ats_risks": list(dict.fromkeys(ats_risks)),
        "readability_risks": list(dict.fromkeys(readability_risks)),
        "evidence_gaps": list(dict.fromkeys(evidence_gaps)),
        "confidence": confidence,
        "rationale": "Critic guardrail dry-run approves only low-risk, evidence-backed patch-ready suggestions.",
        "source_fields_used": source_fields_used,
        "context_id": _clean_text(context_id),
        "job_id": _clean_text(job_id),
        "safety_metadata": _critic_guardrail_safety_metadata(),
    }


def build_live_critic_guardrail_shadow_payload(
    *,
    tailoring_suggestion_payload: Dict[str, Any] | None = None,
    jd_intelligence: Dict[str, Any] | None = None,
    resume_profile: Dict[str, Any] | None = None,
    context_id: str = "",
    job_id: str = "",
    adapter: Any = None,
    feature_enabled: bool = False,
) -> Dict[str, Any]:
    """Validate one injected critic response without applying decisions."""

    fallback = build_critic_guardrail_dry_run_payload(
        tailoring_suggestion_payload=tailoring_suggestion_payload,
        jd_intelligence=jd_intelligence,
        resume_evidence_rows=[deepcopy(resume_profile or {})],
        context_id=context_id,
        job_id=job_id,
    )
    base = {
        **deepcopy(fallback),
        "read_only": True,
        "advisory_only": True,
        "guardrail_decision_only": True,
        "validation_status": "disabled",
        "validation_errors": ["feature_flag_disabled"],
        "fallback_used": True,
        "model_provider": "deterministic",
        "model_name": "critic_guardrail_shadow_fallback",
        "prompt_version": "critic-guardrail-shadow-v1",
        "token_usage": {},
        "cost": {},
        "latency_ms": 0,
    }
    base["safety_metadata"] = {
        **_critic_guardrail_safety_metadata(),
        "feature_flag_required": True,
        "did_call_llm": False,
        "did_write_database": False,
        "did_create_approval": False,
    }
    if feature_enabled is not True:
        return base
    if not callable(adapter):
        base["validation_status"] = "fallback"
        base["validation_errors"] = ["adapter_missing"]
        return base

    adapter_input = {
        "tailoring_suggestion_payload": deepcopy(
            tailoring_suggestion_payload or {}
        ),
        "jd_intelligence": deepcopy(jd_intelligence or {}),
        "resume_profile": deepcopy(resume_profile or {}),
        "context_id": _clean_text(context_id),
        "job_id": _clean_text(job_id),
        "prompt_version": "critic-guardrail-shadow-v1",
    }
    try:
        raw = adapter(deepcopy(adapter_input))
    except Exception as exc:
        base["validation_status"] = "fallback"
        base["validation_errors"] = [
            f"adapter_error:{exc.__class__.__name__}"
        ]
        base["safety_metadata"]["did_call_llm"] = True
        base["safety_metadata"]["deterministic_only"] = False
        return base

    parsed = raw
    if isinstance(raw, dict) and "raw_response" in raw:
        raw_response = raw.get("raw_response")
        if isinstance(raw_response, dict):
            parsed = {
                **deepcopy(raw_response),
                **{
                    key: deepcopy(value)
                    for key, value in raw.items()
                    if key != "raw_response"
                },
            }
        else:
            try:
                decoded = json.loads(str(raw_response))
            except (TypeError, ValueError, json.JSONDecodeError):
                decoded = None
            if not isinstance(decoded, dict):
                base["validation_status"] = "fallback"
                base["validation_errors"] = ["invalid_json_response"]
                base["safety_metadata"]["did_call_llm"] = True
                base["safety_metadata"]["deterministic_only"] = False
                return base
            parsed = {
                **decoded,
                **{
                    key: deepcopy(value)
                    for key, value in raw.items()
                    if key != "raw_response"
                },
            }
    if not isinstance(parsed, dict):
        base["validation_status"] = "fallback"
        base["validation_errors"] = ["adapter_response_not_object"]
        base["safety_metadata"]["did_call_llm"] = True
        base["safety_metadata"]["deterministic_only"] = False
        return base

    errors: List[str] = []
    decision_groups: Dict[str, List[Dict[str, Any]]] = {}
    for field_name in (
        "approved_suggestions",
        "downgraded_suggestions",
        "rejected_suggestions",
    ):
        value = parsed.get(field_name, [])
        if not isinstance(value, list):
            errors.append(f"{field_name}_not_list")
            decision_groups[field_name] = []
            continue
        decision_groups[field_name] = [
            deepcopy(item) for item in value if isinstance(item, dict)
        ]
        if len(decision_groups[field_name]) != len(value):
            errors.append(f"{field_name}_items_must_be_objects")
    if not any(decision_groups.values()):
        errors.append("provider_critic_decisions_missing")

    token_usage = parsed.get("token_usage")
    cost = parsed.get("cost")
    payload = {
        **deepcopy(base),
        **decision_groups,
        "critic_status": _clean_text(parsed.get("critic_status"))
        or (
            "rejected"
            if decision_groups["rejected_suggestions"]
            else "needs_guidance"
            if decision_groups["downgraded_suggestions"]
            else "approved"
        ),
        "reason_codes": _critic_guardrail_text_list(
            parsed.get("reason_codes")
        ),
        "unsupported_claim_risks": _critic_guardrail_text_list(
            parsed.get("unsupported_claim_risks")
        ),
        "ats_risks": _critic_guardrail_text_list(parsed.get("ats_risks")),
        "readability_risks": _critic_guardrail_text_list(
            parsed.get("readability_risks")
        ),
        "evidence_gaps": _critic_guardrail_text_list(
            parsed.get("evidence_gaps")
        ),
        "confidence": _critic_guardrail_float(
            parsed.get("confidence")
        ),
        "rationale": _clean_text(parsed.get("rationale")),
        "validation_status": "valid" if not errors else "invalid",
        "validation_errors": errors,
        "fallback_used": bool(errors),
        "model_provider": _clean_text(
            parsed.get("model_provider") or parsed.get("provider")
        ),
        "model_name": _clean_text(
            parsed.get("model_name") or parsed.get("model")
        ),
        "prompt_version": _clean_text(parsed.get("prompt_version"))
        or "critic-guardrail-shadow-v1",
        "token_usage": deepcopy(token_usage)
        if isinstance(token_usage, dict)
        else {},
        "cost": deepcopy(cost) if isinstance(cost, dict) else {},
        "latency_ms": _critic_guardrail_int(parsed.get("latency_ms")),
    }
    payload["safety_metadata"] = {
        **_critic_guardrail_safety_metadata(),
        "feature_flag_required": True,
        "deterministic_only": False,
        "did_call_llm": True,
        "did_write_database": False,
        "did_create_approval": False,
    }
    return payload
