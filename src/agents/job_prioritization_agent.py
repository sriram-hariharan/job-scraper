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


AGENT_NAME = "Job Prioritization Agent"
AGENT_VERSION = "phase_7a_v1"

PRIORITY_LABELS = {
    "apply_now",
    "tailor_first",
    "manual_review",
    "skip_for_now",
    "watch_source",
}

WATCH_SOURCE_RECOMMENDATIONS = {"monitor", "demote", "needs_timestamp_fix"}
TAILOR_ACTION_SIGNALS = {"MAYBE_TAILOR", "TAILOR_FIRST", "TAILOR"}
REQUIRED_ROW_FIELDS = ["job_id", "company", "title"]

RECOMMENDATION_FIELDNAMES = [
    "job_id",
    "company",
    "title",
    "source",
    "existing_action",
    "advisory_priority",
    "advisory_reason_codes",
    "deterministic_winner_score",
    "fallback_only_no_deterministic_match",
    "packet_generation_allowed",
    "packet_generation_block_reason",
    "source_recommendation",
    "critic_decision",
]


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


def _source_recommendation(row: Dict[str, Any]) -> str:
    return _clean_text(
        _first_nonblank(
            row,
            "source_recommendation",
            "source_health_recommendation",
            "source_health_status",
        )
    ).lower()


def _critic_reject(row: Dict[str, Any]) -> bool:
    return _clean_text(row.get("critic_decision")).lower() == "reject"


def _deterministic_winner_available(row: Dict[str, Any]) -> bool:
    raw = _first_nonblank(row, "deterministic_winner_available")
    if raw:
        return parse_bool(raw)
    return bool(_first_nonblank(row, "selector_winner_resume", "winner_resume") and _score(row) > 0)


def _packet_generation_allowed(row: Dict[str, Any]) -> bool:
    raw = _first_nonblank(row, "packet_generation_allowed")
    if raw:
        return parse_bool(raw)
    return _deterministic_winner_available(row) and _score(row) >= 0.50


def _normalize_input_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "job_id": _first_nonblank(row, "job_id", "job_doc_id", "doc_id"),
        "company": _first_nonblank(row, "company", "job_company"),
        "title": _first_nonblank(row, "title", "job_title"),
        "source": _clean_text(row.get("source")),
        "action": _clean_text(row.get("action")),
        "score": _first_nonblank(row, "score", "final_score", "fit_score"),
        "winner_score": _clean_text(row.get("winner_score")),
        "resolved_score": _clean_text(row.get("resolved_score")),
        "deterministic_winner_score": _first_nonblank(
            row,
            "deterministic_winner_score",
            "selector_winner_score",
            "winner_score",
            "resolved_score",
        ),
        "deterministic_winner_available": _clean_text(row.get("deterministic_winner_available")),
        "fallback_only_no_deterministic_match": _clean_text(row.get("fallback_only_no_deterministic_match")),
        "packet_generation_allowed": _clean_text(row.get("packet_generation_allowed")),
        "packet_generation_block_reason": _clean_text(row.get("packet_generation_block_reason")),
        "freshness_status": _clean_text(row.get("freshness_status")),
        "posted_at": _clean_text(row.get("posted_at")),
        "source_recommendation": _source_recommendation(row),
        "critic_decision": _clean_text(row.get("critic_decision")),
    }


def build_job_prioritization_agent_input_payload(
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


def recommend_job_priority(row: Dict[str, Any]) -> str:
    score = _score(row)
    deterministic = _deterministic_winner_available(row)
    packet_allowed = _packet_generation_allowed(row)
    block_reason = _clean_text(row.get("packet_generation_block_reason"))
    action = _clean_text(row.get("action")).upper()
    source_recommendation = _source_recommendation(row)

    if parse_bool(row.get("fallback_only_no_deterministic_match")):
        return "skip_for_now"
    if not packet_allowed and score <= 0:
        return "skip_for_now"
    if source_recommendation in WATCH_SOURCE_RECOMMENDATIONS:
        return "watch_source"
    if deterministic and 0.50 <= score < 0.60:
        return "manual_review"
    if block_reason:
        return "manual_review"
    if deterministic and score >= 0.70 and packet_allowed and not _critic_reject(row):
        return "apply_now"
    if deterministic and score >= 0.60 and action in TAILOR_ACTION_SIGNALS:
        return "tailor_first"
    if deterministic and score >= 0.60:
        return "manual_review"
    return "skip_for_now"


def _priority_reason(row: Dict[str, Any], priority: str) -> str:
    if priority == "skip_for_now":
        if parse_bool(row.get("fallback_only_no_deterministic_match")):
            return "Fallback-only resume suggestion has no credible deterministic match."
        return "Packet generation is blocked or deterministic score is insufficient."
    if priority == "watch_source":
        return f"Source health recommendation is {_source_recommendation(row) or 'monitor'}."
    if priority == "manual_review":
        if _clean_text(row.get("packet_generation_block_reason")):
            return f"Packet block reason: {_clean_text(row.get('packet_generation_block_reason'))}."
        return "Deterministic match is credible but borderline."
    if priority == "tailor_first":
        return "Credible deterministic match with tailoring signal."
    if priority == "apply_now":
        return "High deterministic score and packet generation is allowed."
    return "No advisory reason available."


def _priority_reason_codes(row: Dict[str, Any], priority: str) -> List[str]:
    if priority == "skip_for_now":
        if parse_bool(row.get("fallback_only_no_deterministic_match")):
            return ["fallback_only_no_deterministic_match"]
        if not _packet_generation_allowed(row):
            return ["packet_generation_blocked"]
        return ["low_or_missing_deterministic_score"]
    if priority == "watch_source":
        return [f"source_{_source_recommendation(row) or 'monitor'}"]
    if priority == "manual_review":
        if _clean_text(row.get("packet_generation_block_reason")):
            return ["packet_generation_block_reason"]
        return ["borderline_deterministic_score"]
    if priority == "tailor_first":
        return ["tailoring_signal"]
    if priority == "apply_now":
        return ["high_score_packet_allowed"]
    return []


def build_job_prioritization_agent_output_payload(
    *,
    input_payload: Dict[str, Any],
) -> Dict[str, Any]:
    recommendations: List[Dict[str, Any]] = []
    priority_counts: Dict[str, int] = {}
    for row in input_payload.get("rows", []) or []:
        priority = recommend_job_priority(row)
        priority_counts[priority] = priority_counts.get(priority, 0) + 1
        recommendations.append(
            {
                "job_id": _clean_text(row.get("job_id")),
                "company": _clean_text(row.get("company")),
                "title": _clean_text(row.get("title")),
                "source": _clean_text(row.get("source")),
                "original_action": _clean_text(row.get("action")),
                "existing_action": _clean_text(row.get("action")),
                "advisory_priority": priority,
                "advisory_reason_codes": _priority_reason_codes(row, priority),
                "priority_reason": _priority_reason(row, priority),
                "deterministic_winner_score": _clean_text(row.get("deterministic_winner_score")),
                "fallback_only_no_deterministic_match": _clean_text(row.get("fallback_only_no_deterministic_match")),
                "packet_generation_allowed": _clean_text(row.get("packet_generation_allowed")),
                "packet_generation_block_reason": _clean_text(row.get("packet_generation_block_reason")),
                "source_recommendation": _clean_text(row.get("source_recommendation")),
                "critic_decision": _clean_text(row.get("critic_decision")),
            }
        )
    return {
        "total_rows": len(recommendations),
        "priority_counts": dict(sorted(priority_counts.items())),
        "recommendations": recommendations,
    }


def build_job_prioritization_agent_validation_payload(
    *,
    input_payload: Dict[str, Any],
    output_payload: Dict[str, Any],
) -> Dict[str, Any]:
    rows = list(input_payload.get("rows", []) or [])
    recommendations = list(output_payload.get("recommendations", []) or [])
    reason_codes: List[str] = []

    row_count_matches = (
        int(input_payload.get("row_count", 0) or 0)
        == int(output_payload.get("total_rows", 0) or 0)
        == len(rows)
        == len(recommendations)
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

    fallback_only_rows_not_apply_now = all(
        rec.get("advisory_priority") != "apply_now"
        for row, rec in zip(rows, recommendations)
        if parse_bool(row.get("fallback_only_no_deterministic_match"))
    )
    if not fallback_only_rows_not_apply_now:
        reason_codes.append("fallback_only_apply_now")

    packet_blocked_rows_not_apply_now = all(
        rec.get("advisory_priority") != "apply_now"
        for row, rec in zip(rows, recommendations)
        if not _packet_generation_allowed(row)
    )
    if not packet_blocked_rows_not_apply_now:
        reason_codes.append("packet_blocked_apply_now")

    high_score_packet_allowed_rows_have_priority = all(
        rec.get("advisory_priority") in {"apply_now", "tailor_first", "manual_review", "watch_source"}
        for row, rec in zip(rows, recommendations)
        if _deterministic_winner_available(row) and _score(row) >= 0.70 and _packet_generation_allowed(row)
    )
    if not high_score_packet_allowed_rows_have_priority:
        reason_codes.append("high_score_packet_allowed_without_priority")

    validation_status = "passed"
    if any(
        code in reason_codes
        for code in {
            "row_count_mismatch",
            "fallback_only_apply_now",
            "packet_blocked_apply_now",
            "high_score_packet_allowed_without_priority",
        }
    ):
        validation_status = "failed"
    elif reason_codes:
        validation_status = "warning"

    return {
        "row_count_matches": row_count_matches,
        "required_fields_present": required_fields_present,
        "missing_required_fields": missing_fields,
        "fallback_only_rows_not_apply_now": fallback_only_rows_not_apply_now,
        "packet_blocked_rows_not_apply_now": packet_blocked_rows_not_apply_now,
        "high_score_packet_allowed_rows_have_priority": high_score_packet_allowed_rows_have_priority,
        "validation_status": validation_status,
        "reason_codes": reason_codes,
    }


def build_job_prioritization_agent_summary_payload(
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
        "priority_counts": output_payload.get("priority_counts", {}),
        "validation_status": validation_payload.get("validation_status", ""),
        "reason_codes": list(validation_payload.get("reason_codes", []) or []),
    }


def render_job_prioritization_recommendations(
    *,
    rows: List[Dict[str, Any]],
    pipeline_run_id: str = "",
    owner_user_id: str = "",
    source_artifact_path: str = "",
) -> Dict[str, Any]:
    input_payload = build_job_prioritization_agent_input_payload(
        rows=rows,
        pipeline_run_id=pipeline_run_id,
        owner_user_id=owner_user_id,
        source_artifact_path=source_artifact_path,
    )
    output_payload = build_job_prioritization_agent_output_payload(input_payload=input_payload)
    validation_payload = build_job_prioritization_agent_validation_payload(
        input_payload=input_payload,
        output_payload=output_payload,
    )
    summary_payload = build_job_prioritization_agent_summary_payload(
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


def render_job_prioritization_recommendation_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    payload = render_job_prioritization_recommendations(rows=rows)
    rendered_rows: List[Dict[str, str]] = []
    for item in payload["output"].get("recommendations", []) or []:
        rendered_rows.append(
            {
                "job_id": _clean_text(item.get("job_id")),
                "company": _clean_text(item.get("company")),
                "title": _clean_text(item.get("title")),
                "source": _clean_text(item.get("source")),
                "existing_action": _clean_text(item.get("existing_action")),
                "advisory_priority": _clean_text(item.get("advisory_priority")),
                "advisory_reason_codes": "|".join(
                    _clean_text(code)
                    for code in item.get("advisory_reason_codes", []) or []
                    if _clean_text(code)
                ),
                "deterministic_winner_score": _clean_text(item.get("deterministic_winner_score")),
                "fallback_only_no_deterministic_match": _clean_text(item.get("fallback_only_no_deterministic_match")),
                "packet_generation_allowed": _clean_text(item.get("packet_generation_allowed")),
                "packet_generation_block_reason": _clean_text(item.get("packet_generation_block_reason")),
                "source_recommendation": _clean_text(item.get("source_recommendation")),
                "critic_decision": _clean_text(item.get("critic_decision")),
            }
        )
    return rendered_rows


def write_job_prioritization_artifacts(
    *,
    rows: List[Dict[str, Any]],
    output_csv_path: str | Path,
    summary_json_path: str | Path | None = None,
    pipeline_run_id: str = "",
    owner_user_id: str = "",
    source_artifact_path: str = "",
) -> Dict[str, Any]:
    payload = render_job_prioritization_recommendations(
        rows=rows,
        pipeline_run_id=pipeline_run_id,
        owner_user_id=owner_user_id,
        source_artifact_path=source_artifact_path,
    )
    output_path = Path(output_csv_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=RECOMMENDATION_FIELDNAMES)
        writer.writeheader()
        for row in render_job_prioritization_recommendation_rows(rows):
            writer.writerow({field: row.get(field, "") for field in RECOMMENDATION_FIELDNAMES})

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
        "row_count": len(payload["output"].get("recommendations", []) or []),
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
        context_id = f"job_priority:{pipeline_run_id}"
    return {
        "pipeline_run_id": pipeline_run_id,
        "owner_user_id": owner_user_id,
        "context_id": context_id,
    }


def record_job_prioritization_agent_trace(
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
        payload = render_job_prioritization_recommendations(
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
            model_name="job_prioritization_rules",
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
