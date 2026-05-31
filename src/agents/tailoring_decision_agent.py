from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List

from src.agents import llmops, trace as trace_store
from src.agents.resume_match_agent import (
    TRACE_ENABLED_ENV,
    TRACE_STRICT_ENV,
    _truthy,
)
from src.pipeline.resume_selection_credibility import parse_bool, parse_float


AGENT_NAME = "Tailoring Decision Agent"
AGENT_VERSION = "phase_8a_v1"

TAILORING_DECISIONS = {
    "no_tailoring_needed",
    "light_tailoring",
    "tailor_before_apply",
    "manual_review_before_tailoring",
    "do_not_tailor",
}
REQUIRED_ROW_FIELDS = ["job_id", "company", "title"]


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


def _deterministic_winner_available(row: Dict[str, Any]) -> bool:
    raw = _first_nonblank(row, "deterministic_winner_available")
    if raw:
        return parse_bool(raw)
    return bool(_first_nonblank(row, "selector_winner_resume", "winner_resume", "resolved_resume") and _score(row) > 0)


def _packet_generation_allowed(row: Dict[str, Any]) -> bool:
    raw = _first_nonblank(row, "packet_generation_allowed")
    if raw:
        return parse_bool(raw)
    return _deterministic_winner_available(row) and _score(row) >= 0.50


def _split_gap_text(value: Any) -> List[str]:
    text = _clean_text(value)
    if not text:
        return []
    return [part.strip() for part in text.replace(",", "|").split("|") if part.strip()]


def _missing_gap_count(row: Dict[str, Any]) -> int:
    numeric = _first_nonblank(row, "missing_skill_count", "skill_gap_count", "missing_requirement_count")
    if numeric:
        try:
            return max(0, int(float(numeric)))
        except (TypeError, ValueError):
            pass
    gaps = []
    for key in (
        "missing_skills",
        "skill_gaps",
        "winner_missing_requirements",
        "resolved_missing_requirements",
        "selector_winner_missing_requirements",
    ):
        gaps.extend(_split_gap_text(row.get(key)))
    return len(gaps)


def _critic_reject(row: Dict[str, Any]) -> bool:
    return _clean_text(row.get("critic_decision")).lower() == "reject"


def _normalize_input_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "job_id": _first_nonblank(row, "job_id", "job_doc_id", "doc_id"),
        "company": _first_nonblank(row, "company", "job_company"),
        "title": _first_nonblank(row, "title", "job_title"),
        "existing_action": _first_nonblank(row, "existing_action", "action"),
        "advisory_priority": _clean_text(row.get("advisory_priority")),
        "deterministic_winner_score": _first_nonblank(
            row,
            "deterministic_winner_score",
            "selector_winner_score",
            "winner_score",
            "resolved_score",
        ),
        "winner_score": _clean_text(row.get("winner_score")),
        "resolved_score": _clean_text(row.get("resolved_score")),
        "fallback_only_no_deterministic_match": _clean_text(row.get("fallback_only_no_deterministic_match")),
        "packet_generation_allowed": _clean_text(row.get("packet_generation_allowed")),
        "packet_generation_block_reason": _clean_text(row.get("packet_generation_block_reason")),
        "critic_decision": _clean_text(row.get("critic_decision")),
        "critic_reason_codes": _clean_text(row.get("critic_reason_codes")),
        "missing_skill_count": _clean_text(row.get("missing_skill_count")),
        "missing_requirement_count": _clean_text(row.get("missing_requirement_count")),
        "winner_missing_requirements": _clean_text(row.get("winner_missing_requirements")),
        "resolved_missing_requirements": _clean_text(row.get("resolved_missing_requirements")),
        "winner_resume": _first_nonblank(row, "winner_resume", "resolved_resume", "selector_winner_resume"),
        "missing_gap_count": str(_missing_gap_count(row)),
    }


def build_tailoring_decision_agent_input_payload(
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


def recommend_tailoring_decision(row: Dict[str, Any]) -> str:
    score = _score(row)
    advisory_priority = _clean_text(row.get("advisory_priority")).lower()
    block_reason = _clean_text(row.get("packet_generation_block_reason"))

    if parse_bool(row.get("fallback_only_no_deterministic_match")):
        return "do_not_tailor"
    if not _packet_generation_allowed(row) and score <= 0:
        return "do_not_tailor"
    if _critic_reject(row):
        return "do_not_tailor"
    if 0.50 <= score < 0.60 or advisory_priority == "manual_review" or block_reason:
        return "manual_review_before_tailoring"
    if score >= 0.80 and advisory_priority == "apply_now" and _missing_gap_count(row) == 0:
        return "no_tailoring_needed"
    if 0.60 <= score < 0.70 or advisory_priority == "tailor_first":
        return "tailor_before_apply"
    if score >= 0.70 and advisory_priority in {"apply_now", "tailor_first"} and not _critic_reject(row):
        return "light_tailoring"
    return "manual_review_before_tailoring"


def _decision_reason_codes(row: Dict[str, Any], decision: str) -> List[str]:
    if decision == "do_not_tailor":
        if parse_bool(row.get("fallback_only_no_deterministic_match")):
            return ["fallback_only_no_deterministic_match"]
        if _critic_reject(row):
            return ["critic_reject"]
        if not _packet_generation_allowed(row):
            return ["packet_generation_blocked"]
        return ["not_tailoring_candidate"]
    if decision == "manual_review_before_tailoring":
        if _clean_text(row.get("packet_generation_block_reason")):
            return ["packet_generation_block_reason"]
        return ["manual_review_or_borderline_score"]
    if decision == "tailor_before_apply":
        return ["tailoring_likely_worthwhile"]
    if decision == "light_tailoring":
        return ["high_score_light_touch"]
    if decision == "no_tailoring_needed":
        return ["high_score_no_obvious_gaps"]
    return []


def build_tailoring_decision_agent_output_payload(
    *,
    input_payload: Dict[str, Any],
) -> Dict[str, Any]:
    decisions: List[Dict[str, Any]] = []
    decision_counts: Dict[str, int] = {}
    for row in input_payload.get("rows", []) or []:
        decision = recommend_tailoring_decision(row)
        decision_counts[decision] = decision_counts.get(decision, 0) + 1
        decisions.append(
            {
                "job_id": _clean_text(row.get("job_id")),
                "company": _clean_text(row.get("company")),
                "title": _clean_text(row.get("title")),
                "existing_action": _clean_text(row.get("existing_action")),
                "advisory_priority": _clean_text(row.get("advisory_priority")),
                "tailoring_decision": decision,
                "tailoring_reason_codes": _decision_reason_codes(row, decision),
                "deterministic_winner_score": _clean_text(row.get("deterministic_winner_score")),
                "missing_gap_count": _clean_text(row.get("missing_gap_count")),
                "winner_resume": _clean_text(row.get("winner_resume")),
                "packet_generation_allowed": _clean_text(row.get("packet_generation_allowed")),
                "packet_generation_block_reason": _clean_text(row.get("packet_generation_block_reason")),
                "critic_decision": _clean_text(row.get("critic_decision")),
            }
        )
    return {
        "total_rows": len(decisions),
        "decision_counts": dict(sorted(decision_counts.items())),
        "decisions": decisions,
    }


def build_tailoring_decision_agent_validation_payload(
    *,
    input_payload: Dict[str, Any],
    output_payload: Dict[str, Any],
) -> Dict[str, Any]:
    rows = list(input_payload.get("rows", []) or [])
    decisions = list(output_payload.get("decisions", []) or [])
    reason_codes: List[str] = []

    row_count_matches = (
        int(input_payload.get("row_count", 0) or 0)
        == int(output_payload.get("total_rows", 0) or 0)
        == len(rows)
        == len(decisions)
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

    fallback_only_rows_do_not_tailor = all(
        item.get("tailoring_decision") == "do_not_tailor"
        for row, item in zip(rows, decisions)
        if parse_bool(row.get("fallback_only_no_deterministic_match"))
    )
    if not fallback_only_rows_do_not_tailor:
        reason_codes.append("fallback_only_tailoring_allowed")

    critic_reject_rows_do_not_tailor = all(
        item.get("tailoring_decision") == "do_not_tailor"
        for row, item in zip(rows, decisions)
        if _critic_reject(row)
    )
    if not critic_reject_rows_do_not_tailor:
        reason_codes.append("critic_reject_tailoring_allowed")

    high_score_apply_rows_have_tailoring_decision = all(
        item.get("tailoring_decision") in {"no_tailoring_needed", "light_tailoring", "tailor_before_apply"}
        for row, item in zip(rows, decisions)
        if _score(row) >= 0.70
        and _clean_text(row.get("advisory_priority")).lower() == "apply_now"
        and not _critic_reject(row)
    )
    if not high_score_apply_rows_have_tailoring_decision:
        reason_codes.append("high_score_apply_missing_tailoring_decision")

    validation_status = "passed"
    if any(
        code in reason_codes
        for code in {
            "row_count_mismatch",
            "fallback_only_tailoring_allowed",
            "critic_reject_tailoring_allowed",
            "high_score_apply_missing_tailoring_decision",
        }
    ):
        validation_status = "failed"
    elif reason_codes:
        validation_status = "warning"

    return {
        "row_count_matches": row_count_matches,
        "required_fields_present": required_fields_present,
        "missing_required_fields": missing_fields,
        "fallback_only_rows_do_not_tailor": fallback_only_rows_do_not_tailor,
        "critic_reject_rows_do_not_tailor": critic_reject_rows_do_not_tailor,
        "high_score_apply_rows_have_tailoring_decision": high_score_apply_rows_have_tailoring_decision,
        "validation_status": validation_status,
        "reason_codes": reason_codes,
    }


def build_tailoring_decision_agent_summary_payload(
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
        "decision_counts": output_payload.get("decision_counts", {}),
        "validation_status": validation_payload.get("validation_status", ""),
        "reason_codes": list(validation_payload.get("reason_codes", []) or []),
    }


def render_tailoring_decisions(
    *,
    rows: List[Dict[str, Any]],
    pipeline_run_id: str = "",
    owner_user_id: str = "",
    source_artifact_path: str = "",
) -> Dict[str, Any]:
    input_payload = build_tailoring_decision_agent_input_payload(
        rows=rows,
        pipeline_run_id=pipeline_run_id,
        owner_user_id=owner_user_id,
        source_artifact_path=source_artifact_path,
    )
    output_payload = build_tailoring_decision_agent_output_payload(input_payload=input_payload)
    validation_payload = build_tailoring_decision_agent_validation_payload(
        input_payload=input_payload,
        output_payload=output_payload,
    )
    summary_payload = build_tailoring_decision_agent_summary_payload(
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
        context_id = f"tailoring_decision:{pipeline_run_id}"
    return {
        "pipeline_run_id": pipeline_run_id,
        "owner_user_id": owner_user_id,
        "context_id": context_id,
    }


def record_tailoring_decision_agent_trace(
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
        payload = render_tailoring_decisions(
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
            model_name="tailoring_decision_rules",
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
