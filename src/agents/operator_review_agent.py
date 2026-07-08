from __future__ import annotations

import os
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from src.agents import llmops, trace as trace_store
from src.agents.resume_match_agent import (
    TRACE_ENABLED_ENV,
    TRACE_STRICT_ENV,
    _truthy,
)
from src.pipeline.resume_selection_credibility import parse_bool, parse_float


AGENT_NAME = "Operator Review Agent"
AGENT_VERSION = "phase_9a_v1"

OPERATOR_REVIEW_LANES = {
    "ready_to_apply",
    "tailor_then_apply",
    "review_before_action",
    "hold_or_skip",
    "source_watch",
}
SOURCE_WATCH_RECOMMENDATIONS = {"monitor", "demote", "needs_timestamp_fix"}
READY_TAILORING_DECISIONS = {"no_tailoring_needed", "light_tailoring"}
TAILORING_SIGNAL_DECISIONS = {"tailor_before_apply", "light_tailoring"}
REQUIRED_ROW_FIELDS = ["job_id", "company", "title"]
OPERATOR_REVIEW_FIELDNAMES = [
    "job_id",
    "company",
    "title",
    "source",
    "existing_action",
    "advisory_priority",
    "tailoring_decision",
    "operator_review_lane",
    "operator_review_reason_codes",
    "deterministic_winner_score",
    "fallback_only_no_deterministic_match",
    "packet_generation_allowed",
    "packet_generation_block_reason",
    "critic_decision",
    "source_recommendation",
    "winner_resume",
    "resolved_resume",
]
OPERATOR_REVIEW_TAILORING_EVIDENCE_ARTIFACT_VERSION = (
    "operator-review-tailoring-evidence-v1"
)
OPERATOR_REVIEW_TAILORING_EVIDENCE_GATE = (
    "APPLYLENS_AGENTIC_OPERATOR_REVIEW_CONSUMES_TAILORING_DECISION_EVIDENCE_ENABLED"
)
OPERATOR_REVIEW_TAILORING_EVIDENCE_FALSE_FLAGS = (
    "provider_call_performed",
    "live_llm_call_performed",
    "jd_extraction_performed",
    "resume_match_execution_performed",
    "critic_execution_performed",
    "job_prioritization_execution_performed",
    "tailoring_decision_execution_performed",
    "trace_persistence_performed",
    "collector_output_changed",
    "production_output_changed",
    "scoring_changed",
    "ranking_changed",
    "filtering_changed",
    "review_queue_mutation_performed",
    "queue_mutation_performed",
    "scheduler_mutation_performed",
    "tailoring_mutation_performed",
    "source_resume_mutation_performed",
    "generated_resume_mutation_performed",
    "tailoring_provider_call_performed",
    "workflow_runner_executed",
    "application_status_changed",
    "auto_apply_performed",
    "ats_submission_performed",
    "apply_click_performed",
    "recruiter_message_sent",
    "mark_applied_performed",
)


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _first_nonblank(row: Dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = _clean_text(row.get(key))
        if value:
            return value
    return ""


def _plain_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _plain_list(value: Any) -> List[Any]:
    return list(value) if isinstance(value, list) else []


def _operator_review_tailoring_safety_metadata() -> Dict[str, bool]:
    return {flag: False for flag in OPERATOR_REVIEW_TAILORING_EVIDENCE_FALSE_FLAGS}


def _operator_review_reason_codes(value: Any) -> List[str]:
    return [
        _clean_text(code)
        for code in _plain_list(value)
        if _clean_text(code)
    ]


def _operator_review_validation_status(value: Any) -> str:
    payload = _plain_dict(value)
    return _clean_text(payload.get("validation_status")).lower()


def _operator_review_identity_conflict(
    *,
    field_name: str,
    primary: Dict[str, Any],
    optional: Dict[str, Any],
    reason_prefix: str,
) -> str:
    primary_value = _clean_text(primary.get(field_name))
    optional_value = _clean_text(optional.get(field_name))
    if primary_value and optional_value and primary_value != optional_value:
        return f"{reason_prefix}_{field_name}_conflict"
    return ""


def _operator_review_tailoring_decision(
    *,
    tailoring_decision: str,
    tailoring_readiness: str,
    confidence: float,
    operator_review_required: bool,
    reason_codes: List[str],
    has_source_context_gap: bool,
) -> Dict[str, Any]:
    decision = _clean_text(tailoring_decision).lower()
    readiness = _clean_text(tailoring_readiness).lower()
    reason_text = " ".join(reason_codes).lower()
    has_blocking_risk = (
        decision == "do_not_tailor"
        or readiness == "blocked_by_risk"
        or "blocking_risk" in reason_text
        or "blocked_by_risk" in reason_text
    )
    if has_blocking_risk:
        return {
            "operator_review_lane": "hold_or_skip",
            "operator_review_readiness": "blocked_by_risk",
            "human_review_required": True,
            "recommended_next_step": "hold_or_skip",
        }
    if (
        decision == "no_tailoring_needed"
        and readiness in {"ready_for_operator_review", "ready_without_tailoring", "ready"}
        and confidence >= 0.75
        and not operator_review_required
        and not reason_codes
    ):
        return {
            "operator_review_lane": "ready_to_apply",
            "operator_review_readiness": "ready_without_tailoring",
            "human_review_required": False,
            "recommended_next_step": "review_and_apply_manually",
        }
    if decision in {"light_tailoring", "tailor_before_apply"} and not operator_review_required:
        return {
            "operator_review_lane": "tailor_then_apply",
            "operator_review_readiness": "needs_tailoring_review",
            "human_review_required": True,
            "recommended_next_step": "review_tailoring_plan",
        }
    if has_source_context_gap and not reason_codes:
        return {
            "operator_review_lane": "source_watch",
            "operator_review_readiness": "insufficient_evidence",
            "human_review_required": True,
            "recommended_next_step": "watch_source",
        }
    if has_source_context_gap and not any(
        code in reason_codes
        for code in {
            "tailoring_decision_evidence_missing",
            "tailoring_decision_evidence_malformed",
        }
    ):
        return {
            "operator_review_lane": "source_watch",
            "operator_review_readiness": "insufficient_evidence",
            "human_review_required": True,
            "recommended_next_step": "watch_source",
        }
    if decision == "manual_review_before_tailoring" or operator_review_required:
        return {
            "operator_review_lane": "review_before_action",
            "operator_review_readiness": "needs_manual_review",
            "human_review_required": True,
            "recommended_next_step": "review_risks_before_action",
        }
    return {
        "operator_review_lane": "review_before_action",
        "operator_review_readiness": "needs_manual_review",
        "human_review_required": True,
        "recommended_next_step": "collect_more_evidence",
    }


def _score(row: Dict[str, Any]) -> float:
    return parse_float(
        _first_nonblank(
            row,
            "deterministic_winner_score",
            "selector_winner_score",
            "winner_score",
            "resolved_score",
        )
    )


def _packet_generation_allowed(row: Dict[str, Any]) -> bool:
    raw = _first_nonblank(row, "packet_generation_allowed")
    if raw:
        return parse_bool(raw)
    return bool(_first_nonblank(row, "winner_resume", "resolved_resume", "selector_winner_resume") and _score(row) >= 0.50)


def _critic_reject(row: Dict[str, Any]) -> bool:
    return _clean_text(row.get("critic_decision")).lower() == "reject"


def _source_recommendation(row: Dict[str, Any]) -> str:
    return _first_nonblank(row, "source_recommendation", "source_health_recommendation", "source_health_status").lower()


def _normalize_input_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "job_id": _first_nonblank(row, "job_id", "job_doc_id", "doc_id"),
        "company": _first_nonblank(row, "company", "job_company"),
        "title": _first_nonblank(row, "title", "job_title"),
        "source": _clean_text(row.get("source")),
        "existing_action": _first_nonblank(row, "existing_action", "action"),
        "advisory_priority": _clean_text(row.get("advisory_priority")),
        "tailoring_decision": _clean_text(row.get("tailoring_decision")),
        "critic_decision": _clean_text(row.get("critic_decision")),
        "deterministic_winner_score": _first_nonblank(
            row,
            "deterministic_winner_score",
            "selector_winner_score",
            "winner_score",
            "resolved_score",
        ),
        "fallback_only_no_deterministic_match": _clean_text(row.get("fallback_only_no_deterministic_match")),
        "packet_generation_allowed": _clean_text(row.get("packet_generation_allowed")),
        "packet_generation_block_reason": _clean_text(row.get("packet_generation_block_reason")),
        "source_recommendation": _source_recommendation(row),
        "winner_resume": _first_nonblank(row, "winner_resume", "selector_winner_resume"),
        "resolved_resume": _clean_text(row.get("resolved_resume")),
    }


def build_operator_review_tailoring_evidence_artifact(
    *,
    tailoring_decision_priority_evidence: Dict[str, Any] | None = None,
    job_prioritization_critic_evidence: Dict[str, Any] | None = None,
    critic_resume_match_jd_evidence: Dict[str, Any] | None = None,
    resume_match_jd_evidence: Dict[str, Any] | None = None,
    jd_intelligence: Dict[str, Any] | None = None,
    enabled: bool = False,
) -> Dict[str, Any]:
    """Build read-only human review evidence from an existing tailoring decision."""

    tailoring_source = _plain_dict(tailoring_decision_priority_evidence)
    priority_source = _plain_dict(job_prioritization_critic_evidence)
    critic_source = _plain_dict(critic_resume_match_jd_evidence)
    resume_source = _plain_dict(resume_match_jd_evidence)
    jd_source = _plain_dict(jd_intelligence)
    reason_codes: List[str] = []

    if tailoring_decision_priority_evidence is None or tailoring_decision_priority_evidence == {}:
        reason_codes.append("tailoring_decision_evidence_missing")
    elif not isinstance(tailoring_decision_priority_evidence, dict):
        reason_codes.append("tailoring_decision_evidence_malformed")
    elif _clean_text(tailoring_source.get("artifact_type")) != "tailoring_decision_priority_evidence":
        reason_codes.append("tailoring_decision_evidence_malformed")

    optional_sources = (
        (
            job_prioritization_critic_evidence,
            priority_source,
            "job_prioritization",
            "job_prioritization_critic_evidence",
        ),
        (
            critic_resume_match_jd_evidence,
            critic_source,
            "critic",
            "critic_resume_match_jd_evidence",
        ),
        (
            resume_match_jd_evidence,
            resume_source,
            "resume_match",
            "resume_match_jd_evidence",
        ),
    )
    for raw_source, source, prefix, artifact_type in optional_sources:
        if raw_source is None or raw_source == {}:
            reason_codes.append(f"{prefix}_context_missing")
        elif not isinstance(raw_source, dict):
            reason_codes.append(f"{prefix}_context_malformed")
        elif _clean_text(source.get("artifact_type")) != artifact_type:
            reason_codes.append(f"{prefix}_context_malformed")

    if jd_intelligence is None or jd_intelligence == {}:
        reason_codes.append("jd_intelligence_context_missing")
    elif not isinstance(jd_intelligence, dict):
        reason_codes.append("jd_intelligence_context_malformed")

    tailoring_validation_status = _operator_review_validation_status(
        tailoring_source.get("validation_summary")
    )
    if tailoring_source and tailoring_validation_status not in {"", "passed"}:
        reason_codes.append("tailoring_decision_validation_degraded")

    for code in _operator_review_reason_codes(tailoring_source.get("reason_codes")):
        reason_codes.append(code)

    for optional_source, prefix in (
        (priority_source, "job_prioritization_context"),
        (critic_source, "critic_context"),
        (resume_source, "resume_match_context"),
        (jd_source, "jd_intelligence_context"),
    ):
        for field_name in ("job_id", "title", "company"):
            conflict = _operator_review_identity_conflict(
                field_name=field_name,
                primary=tailoring_source,
                optional=optional_source,
                reason_prefix=prefix,
            )
            if conflict:
                reason_codes.append(conflict)

    tailoring_decision = _clean_text(tailoring_source.get("tailoring_decision")).lower()
    tailoring_readiness = _clean_text(tailoring_source.get("tailoring_readiness")).lower()
    operator_review_required = bool(tailoring_source.get("operator_review_required"))
    confidence = parse_float(tailoring_source.get("confidence"))
    priority_recommendation = _clean_text(priority_source.get("priority_recommendation")).lower()
    priority_band = _clean_text(priority_source.get("priority_band")).lower()
    critic_risk_flags = _operator_review_reason_codes(critic_source.get("risk_flags"))
    critic_contradiction_flags = _operator_review_reason_codes(
        critic_source.get("contradiction_flags")
    )

    if tailoring_decision == "no_tailoring_needed" and operator_review_required:
        reason_codes.append("no_tailoring_needed_with_operator_review_required")
    if tailoring_decision == "do_not_tailor" and tailoring_readiness in {
        "ready",
        "ready_for_operator_review",
        "ready_without_tailoring",
    }:
        reason_codes.append("do_not_tailor_with_ready_readiness")
    if (
        priority_recommendation == "prioritize"
        and priority_band == "high"
        and (
            tailoring_decision == "do_not_tailor"
            or tailoring_readiness == "blocked_by_risk"
        )
    ):
        reason_codes.append("high_priority_with_blocked_tailoring_decision")
    if tailoring_decision == "no_tailoring_needed" and critic_risk_flags:
        reason_codes.append("no_tailoring_needed_with_critic_risk_flags")
    if tailoring_decision == "no_tailoring_needed" and critic_contradiction_flags:
        reason_codes.append("no_tailoring_needed_with_critic_contradiction_flags")

    job_id = (
        _clean_text(tailoring_source.get("job_id"))
        or _clean_text(priority_source.get("job_id"))
        or _clean_text(critic_source.get("job_id"))
        or _clean_text(resume_source.get("job_id"))
        or _clean_text(jd_source.get("job_id"))
    )
    title = (
        _clean_text(tailoring_source.get("title"))
        or _clean_text(priority_source.get("title"))
        or _clean_text(critic_source.get("title"))
        or _clean_text(resume_source.get("title"))
        or _clean_text(jd_source.get("title"))
    )
    company = (
        _clean_text(tailoring_source.get("company"))
        or _clean_text(priority_source.get("company"))
        or _clean_text(critic_source.get("company"))
        or _clean_text(resume_source.get("company"))
        or _clean_text(jd_source.get("company"))
    )
    selected_resume_id = (
        _clean_text(tailoring_source.get("selected_resume_id"))
        or _clean_text(priority_source.get("selected_resume_id"))
        or _clean_text(critic_source.get("selected_resume_id"))
        or _clean_text(resume_source.get("selected_resume_id"))
    )
    has_source_context_gap = not all([job_id, title, company])
    reason_codes = list(dict.fromkeys(reason_codes))

    review = _operator_review_tailoring_decision(
        tailoring_decision=tailoring_decision,
        tailoring_readiness=tailoring_readiness,
        confidence=confidence,
        operator_review_required=operator_review_required,
        reason_codes=reason_codes,
        has_source_context_gap=has_source_context_gap,
    )
    if "tailoring_decision_evidence_missing" in reason_codes:
        review = {
            "operator_review_lane": "review_before_action",
            "operator_review_readiness": "insufficient_evidence",
            "human_review_required": True,
            "recommended_next_step": "collect_more_evidence",
        }
    elif "tailoring_decision_evidence_malformed" in reason_codes:
        review = {
            "operator_review_lane": "review_before_action",
            "operator_review_readiness": "insufficient_evidence",
            "human_review_required": True,
            "recommended_next_step": "collect_more_evidence",
        }
    elif any(
        code in reason_codes
        for code in {
            "tailoring_decision_validation_degraded",
            "no_tailoring_needed_with_operator_review_required",
            "do_not_tailor_with_ready_readiness",
            "high_priority_with_blocked_tailoring_decision",
            "no_tailoring_needed_with_critic_risk_flags",
            "no_tailoring_needed_with_critic_contradiction_flags",
        }
    ) and review["operator_review_lane"] == "ready_to_apply":
        review = {
            "operator_review_lane": "review_before_action",
            "operator_review_readiness": "needs_manual_review",
            "human_review_required": True,
            "recommended_next_step": "review_risks_before_action",
        }

    validation_status = "passed"
    if any(
        code in reason_codes
        for code in {
            "tailoring_decision_evidence_missing",
            "tailoring_decision_evidence_malformed",
        }
    ):
        validation_status = "failed"
    elif reason_codes:
        validation_status = "degraded"

    review_packet_summary = {
        "job_id": job_id,
        "title": title,
        "company": company,
        "selected_resume_id": selected_resume_id,
        "tailoring_decision": tailoring_decision,
        "tailoring_readiness": tailoring_readiness,
        "tailoring_intensity": _clean_text(tailoring_source.get("tailoring_intensity")).lower(),
        "operator_review_required": operator_review_required,
        "priority_recommendation": priority_recommendation,
        "priority_band": priority_band,
        "critic_risk_flag_count": len(critic_risk_flags),
        "critic_contradiction_count": len(critic_contradiction_flags),
        "confidence": confidence,
        "reason_codes": reason_codes,
    }
    safety_metadata = _operator_review_tailoring_safety_metadata()

    return {
        "artifact_type": "operator_review_tailoring_evidence",
        "artifact_version": OPERATOR_REVIEW_TAILORING_EVIDENCE_ARTIFACT_VERSION,
        "source_agent": "operator_review",
        "source_agent_name": AGENT_NAME,
        "source_agent_version": AGENT_VERSION,
        "upstream_agents": [
            "tailoring_decision",
            "job_prioritization",
            "critic",
            "resume_match",
            "jd_intelligence",
        ],
        "gate_name": OPERATOR_REVIEW_TAILORING_EVIDENCE_GATE,
        "enabled": bool(enabled),
        "default_off": True,
        "read_only": True,
        "diagnostic_only": True,
        "job_id": job_id,
        "title": title,
        "company": company,
        "selected_resume_id": selected_resume_id,
        "operator_review_lane": review["operator_review_lane"],
        "operator_review_readiness": review["operator_review_readiness"],
        "human_review_required": review["human_review_required"],
        "recommended_next_step": review["recommended_next_step"],
        "review_packet_summary": review_packet_summary,
        "reason_codes": reason_codes,
        "validation_summary": {
            "validation_status": validation_status,
            "tailoring_decision_evidence_present": bool(tailoring_source),
            "tailoring_decision_evidence_valid": (
                bool(tailoring_source)
                and "tailoring_decision_evidence_malformed" not in reason_codes
            ),
            "job_prioritization_context_present": bool(priority_source),
            "critic_context_present": bool(critic_source),
            "resume_match_context_present": bool(resume_source),
            "jd_intelligence_context_present": bool(jd_source),
            "source_context_complete": not has_source_context_gap,
            "reason_codes": reason_codes,
        },
        "confidence": confidence,
        "safety_metadata": safety_metadata,
        **safety_metadata,
    }


def build_operator_review_agent_input_payload(
    *,
    rows: List[Dict[str, Any]],
    pipeline_run_id: str = "",
    owner_user_id: str = "",
    source_artifact_path: str = "",
) -> Dict[str, Any]:
    normalized_rows = [_normalize_input_row(row) for row in rows]
    return {
        "agent_name": AGENT_NAME,
        "agent_version": AGENT_VERSION,
        "pipeline_run_id": _clean_text(pipeline_run_id),
        "owner_user_id": _clean_text(owner_user_id),
        "source_artifact_path": _clean_text(source_artifact_path),
        "row_count": len(normalized_rows),
        "rows": normalized_rows,
    }


def recommend_operator_lane(row: Dict[str, Any]) -> str:
    advisory_priority = _clean_text(row.get("advisory_priority")).lower()
    tailoring_decision = _clean_text(row.get("tailoring_decision")).lower()
    packet_allowed = _packet_generation_allowed(row)
    block_reason = _clean_text(row.get("packet_generation_block_reason"))
    source_recommendation = _source_recommendation(row)

    if parse_bool(row.get("fallback_only_no_deterministic_match")):
        return "hold_or_skip"
    if not packet_allowed and _score(row) <= 0:
        return "hold_or_skip"
    if tailoring_decision == "do_not_tailor":
        return "hold_or_skip"
    if _critic_reject(row):
        return "hold_or_skip"
    if advisory_priority == "watch_source" or source_recommendation in SOURCE_WATCH_RECOMMENDATIONS:
        return "source_watch"
    if advisory_priority == "manual_review" or tailoring_decision == "manual_review_before_tailoring" or block_reason:
        return "review_before_action"
    if (
        advisory_priority == "apply_now"
        and tailoring_decision in READY_TAILORING_DECISIONS
        and not _critic_reject(row)
        and packet_allowed
    ):
        return "ready_to_apply"
    if advisory_priority == "tailor_first" or tailoring_decision in TAILORING_SIGNAL_DECISIONS:
        return "tailor_then_apply"
    return "review_before_action"


def _lane_reason_codes(row: Dict[str, Any], lane: str) -> List[str]:
    if lane == "hold_or_skip":
        if parse_bool(row.get("fallback_only_no_deterministic_match")):
            return ["fallback_only_no_deterministic_match"]
        if _critic_reject(row):
            return ["critic_reject"]
        if _clean_text(row.get("tailoring_decision")).lower() == "do_not_tailor":
            return ["tailoring_do_not_tailor"]
        if not _packet_generation_allowed(row):
            return ["packet_generation_blocked"]
        return ["hold_signal"]
    if lane == "source_watch":
        return [f"source_{_source_recommendation(row) or 'watch'}"]
    if lane == "review_before_action":
        if _clean_text(row.get("packet_generation_block_reason")):
            return ["packet_generation_block_reason"]
        return ["manual_review_signal"]
    if lane == "tailor_then_apply":
        return ["tailoring_signal"]
    if lane == "ready_to_apply":
        return ["apply_ready_signals_aligned"]
    return []


def build_operator_review_agent_output_payload(
    *,
    input_payload: Dict[str, Any],
) -> Dict[str, Any]:
    reviews: List[Dict[str, Any]] = []
    lane_counts: Dict[str, int] = {}
    for row in input_payload.get("rows", []) or []:
        lane = recommend_operator_lane(row)
        lane_counts[lane] = lane_counts.get(lane, 0) + 1
        reviews.append(
            {
                "job_id": _clean_text(row.get("job_id")),
                "company": _clean_text(row.get("company")),
                "title": _clean_text(row.get("title")),
                "source": _clean_text(row.get("source")),
                "existing_action": _clean_text(row.get("existing_action")),
                "operator_review_lane": lane,
                "operator_reason_codes": _lane_reason_codes(row, lane),
                "advisory_priority": _clean_text(row.get("advisory_priority")),
                "tailoring_decision": _clean_text(row.get("tailoring_decision")),
                "critic_decision": _clean_text(row.get("critic_decision")),
                "deterministic_winner_score": _clean_text(row.get("deterministic_winner_score")),
                "fallback_only_no_deterministic_match": _clean_text(row.get("fallback_only_no_deterministic_match")),
                "packet_generation_allowed": _clean_text(row.get("packet_generation_allowed")),
                "packet_generation_block_reason": _clean_text(row.get("packet_generation_block_reason")),
                "source_recommendation": _clean_text(row.get("source_recommendation")),
                "winner_resume": _clean_text(row.get("winner_resume")),
                "resolved_resume": _clean_text(row.get("resolved_resume")),
            }
        )
    return {
        "total_rows": len(reviews),
        "lane_counts": dict(sorted(lane_counts.items())),
        "reviews": reviews,
    }


def build_operator_review_agent_validation_payload(
    *,
    input_payload: Dict[str, Any],
    output_payload: Dict[str, Any],
) -> Dict[str, Any]:
    rows = list(input_payload.get("rows", []) or [])
    reviews = list(output_payload.get("reviews", []) or [])
    reason_codes: List[str] = []

    row_count_matches = (
        int(input_payload.get("row_count", 0) or 0)
        == int(output_payload.get("total_rows", 0) or 0)
        == len(rows)
        == len(reviews)
    )
    if not row_count_matches:
        reason_codes.append("row_count_mismatch")

    missing_fields = sorted(
        {
            field
            for row in rows
            for field in REQUIRED_ROW_FIELDS
            if not _clean_text(row.get(field))
        }
    )
    required_fields_present = not missing_fields
    if not required_fields_present:
        reason_codes.append("missing_required_fields")

    fallback_only_rows_not_ready_to_apply = all(
        item.get("operator_review_lane") != "ready_to_apply"
        for row, item in zip(rows, reviews)
        if parse_bool(row.get("fallback_only_no_deterministic_match"))
    )
    if not fallback_only_rows_not_ready_to_apply:
        reason_codes.append("fallback_only_ready_to_apply")

    critic_reject_rows_not_ready_to_apply = all(
        item.get("operator_review_lane") != "ready_to_apply"
        for row, item in zip(rows, reviews)
        if _critic_reject(row)
    )
    if not critic_reject_rows_not_ready_to_apply:
        reason_codes.append("critic_reject_ready_to_apply")

    packet_blocked_rows_not_ready_to_apply = all(
        item.get("operator_review_lane") != "ready_to_apply"
        for row, item in zip(rows, reviews)
        if not _packet_generation_allowed(row)
    )
    if not packet_blocked_rows_not_ready_to_apply:
        reason_codes.append("packet_blocked_ready_to_apply")

    ready_to_apply_rows_have_packet_allowed = all(
        _packet_generation_allowed(row)
        for row, item in zip(rows, reviews)
        if item.get("operator_review_lane") == "ready_to_apply"
    )
    if not ready_to_apply_rows_have_packet_allowed:
        reason_codes.append("ready_to_apply_without_packet_allowed")

    validation_status = "passed"
    if any(
        code in reason_codes
        for code in {
            "row_count_mismatch",
            "fallback_only_ready_to_apply",
            "critic_reject_ready_to_apply",
            "packet_blocked_ready_to_apply",
            "ready_to_apply_without_packet_allowed",
        }
    ):
        validation_status = "failed"
    elif reason_codes:
        validation_status = "warning"

    return {
        "row_count_matches": row_count_matches,
        "required_fields_present": required_fields_present,
        "missing_required_fields": missing_fields,
        "fallback_only_rows_not_ready_to_apply": fallback_only_rows_not_ready_to_apply,
        "critic_reject_rows_not_ready_to_apply": critic_reject_rows_not_ready_to_apply,
        "packet_blocked_rows_not_ready_to_apply": packet_blocked_rows_not_ready_to_apply,
        "ready_to_apply_rows_have_packet_allowed": ready_to_apply_rows_have_packet_allowed,
        "validation_status": validation_status,
        "reason_codes": reason_codes,
    }


def build_operator_review_agent_summary_payload(
    *,
    input_payload: Dict[str, Any],
    output_payload: Dict[str, Any],
    validation_payload: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "agent_name": AGENT_NAME,
        "agent_version": AGENT_VERSION,
        "pipeline_run_id": input_payload.get("pipeline_run_id", ""),
        "owner_user_id": input_payload.get("owner_user_id", ""),
        "row_count": input_payload.get("row_count", 0),
        "lane_counts": output_payload.get("lane_counts", {}),
        "validation_status": validation_payload.get("validation_status", ""),
        "reason_codes": list(validation_payload.get("reason_codes", []) or []),
    }


def render_operator_review(
    *,
    rows: List[Dict[str, Any]],
    pipeline_run_id: str = "",
    owner_user_id: str = "",
    source_artifact_path: str = "",
) -> Dict[str, Any]:
    input_payload = build_operator_review_agent_input_payload(
        rows=rows,
        pipeline_run_id=pipeline_run_id,
        owner_user_id=owner_user_id,
        source_artifact_path=source_artifact_path,
    )
    output_payload = build_operator_review_agent_output_payload(input_payload=input_payload)
    validation_payload = build_operator_review_agent_validation_payload(
        input_payload=input_payload,
        output_payload=output_payload,
    )
    summary_payload = build_operator_review_agent_summary_payload(
        input_payload=input_payload,
        output_payload=output_payload,
        validation_payload=validation_payload,
    )
    return {
        "input": input_payload,
        "output": output_payload,
        "validation": validation_payload,
        "summary": summary_payload,
    }


def render_operator_review_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    payload = render_operator_review(rows=rows)
    rendered_rows: List[Dict[str, str]] = []
    for item in payload["output"].get("reviews", []) or []:
        rendered_rows.append(
            {
                "job_id": _clean_text(item.get("job_id")),
                "company": _clean_text(item.get("company")),
                "title": _clean_text(item.get("title")),
                "source": _clean_text(item.get("source")),
                "existing_action": _clean_text(item.get("existing_action")),
                "advisory_priority": _clean_text(item.get("advisory_priority")),
                "tailoring_decision": _clean_text(item.get("tailoring_decision")),
                "operator_review_lane": _clean_text(item.get("operator_review_lane")),
                "operator_review_reason_codes": "|".join(
                    _clean_text(code)
                    for code in item.get("operator_reason_codes", []) or []
                    if _clean_text(code)
                ),
                "deterministic_winner_score": _clean_text(item.get("deterministic_winner_score")),
                "fallback_only_no_deterministic_match": _clean_text(item.get("fallback_only_no_deterministic_match")),
                "packet_generation_allowed": _clean_text(item.get("packet_generation_allowed")),
                "packet_generation_block_reason": _clean_text(item.get("packet_generation_block_reason")),
                "critic_decision": _clean_text(item.get("critic_decision")),
                "source_recommendation": _clean_text(item.get("source_recommendation")),
                "winner_resume": _clean_text(item.get("winner_resume")),
                "resolved_resume": _clean_text(item.get("resolved_resume")),
            }
        )
    return rendered_rows


def write_operator_review_artifacts(
    *,
    rows: List[Dict[str, Any]],
    output_csv_path: str | Path,
    summary_json_path: str | Path | None = None,
    pipeline_run_id: str = "",
    owner_user_id: str = "",
    source_artifact_path: str = "",
) -> Dict[str, Any]:
    payload = render_operator_review(
        rows=rows,
        pipeline_run_id=pipeline_run_id,
        owner_user_id=owner_user_id,
        source_artifact_path=source_artifact_path,
    )
    output_path = Path(output_csv_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OPERATOR_REVIEW_FIELDNAMES)
        writer.writeheader()
        for row in render_operator_review_rows(rows):
            writer.writerow({field: row.get(field, "") for field in OPERATOR_REVIEW_FIELDNAMES})

    summary_path = None
    if summary_json_path:
        summary_path = Path(summary_json_path)
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(
            json.dumps(payload["summary"], indent=2, sort_keys=True),
            encoding="utf-8",
        )

    return {
        "csv_path": str(output_path),
        "summary_json_path": str(summary_path) if summary_path else "",
        "row_count": len(payload["output"].get("reviews", []) or []),
        "summary": payload["summary"],
        "validation": payload["validation"],
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
        context_id = f"operator_review:{pipeline_run_id}"
    return {
        "pipeline_run_id": pipeline_run_id,
        "owner_user_id": owner_user_id,
        "context_id": context_id,
    }


def record_operator_review_agent_trace(
    *,
    rows: List[Dict[str, Any]],
    source_artifact_path: str = "",
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
        payload = render_operator_review(
            rows=rows,
            pipeline_run_id=context["pipeline_run_id"],
            owner_user_id=context["owner_user_id"],
            source_artifact_path=source_artifact_path,
        )
        run_payload = trace_module.create_agent_run(
            record={
                "owner_user_id": context["owner_user_id"],
                "pipeline_run_id": context["pipeline_run_id"],
                "context_id": context["context_id"],
                "status": "running",
                "started_at": started_at,
                "summary_json": payload["summary"],
            }
        )
        agent_run_id = _clean_text((run_payload.get("run") or {}).get("agent_run_id"))
        if not agent_run_id:
            raise RuntimeError("Agent trace run did not return agent_run_id.")

        llmops_metadata = llmops.build_llmops_metadata(
            model_provider="deterministic",
            model_name="operator_review_rules",
            agent_name=AGENT_NAME,
            agent_version=AGENT_VERSION,
            schema_validation_status=payload["validation"].get("validation_status", ""),
        )
        step_record = llmops.merge_llmops_into_agent_step_kwargs(
            {
                "agent_run_id": agent_run_id,
                "owner_user_id": context["owner_user_id"],
                "pipeline_run_id": context["pipeline_run_id"],
                "context_id": context["context_id"],
                "agent_name": AGENT_NAME,
                "agent_version": AGENT_VERSION,
                "input_json": payload["input"],
                "status": "running",
                "started_at": started_at,
            },
            llmops_metadata,
        )
        step_payload = trace_module.record_agent_step(record=step_record)
        agent_step_id = _clean_text((step_payload.get("step") or {}).get("agent_step_id"))
        if not agent_step_id:
            raise RuntimeError("Agent trace step did not return agent_step_id.")

        completed_at = _utc_now_iso()
        trace_module.complete_agent_step(
            agent_step_id=agent_step_id,
            owner_user_id=context["owner_user_id"],
            output_json=payload["output"],
            validation_json=payload["validation"],
            completed_at=completed_at,
        )
        trace_module.complete_agent_run(
            agent_run_id=agent_run_id,
            owner_user_id=context["owner_user_id"],
            summary_json=payload["summary"],
            completed_at=completed_at,
        )
        return {
            "attempted": True,
            "recorded": True,
            "agent_run_id": agent_run_id,
            "agent_step_id": agent_step_id,
            "summary": payload["summary"],
            "validation": payload["validation"],
        }
    except Exception as exc:
        if agent_trace_strict(env_map):
            raise
        return {"attempted": True, "recorded": False, "warning": str(exc)}
