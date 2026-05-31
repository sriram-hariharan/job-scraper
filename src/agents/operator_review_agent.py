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
