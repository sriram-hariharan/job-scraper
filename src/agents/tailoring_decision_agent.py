from __future__ import annotations

import os
import csv
import json
import re
from copy import deepcopy
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
TAILORING_DECISION_FIELDNAMES = [
    "job_id",
    "company",
    "title",
    "source",
    "existing_action",
    "advisory_priority",
    "tailoring_decision",
    "tailoring_reason_codes",
    "deterministic_winner_score",
    "fallback_only_no_deterministic_match",
    "packet_generation_allowed",
    "packet_generation_block_reason",
    "critic_decision",
    "critic_reason_codes",
    "winner_resume",
    "resolved_resume",
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
        "source": _clean_text(row.get("source")),
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
        "winner_resume": _first_nonblank(row, "winner_resume", "selector_winner_resume"),
        "resolved_resume": _clean_text(row.get("resolved_resume")),
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
                "source": _clean_text(row.get("source")),
                "existing_action": _clean_text(row.get("existing_action")),
                "advisory_priority": _clean_text(row.get("advisory_priority")),
                "tailoring_decision": decision,
                "tailoring_reason_codes": _decision_reason_codes(row, decision),
                "deterministic_winner_score": _clean_text(row.get("deterministic_winner_score")),
                "fallback_only_no_deterministic_match": _clean_text(row.get("fallback_only_no_deterministic_match")),
                "missing_gap_count": _clean_text(row.get("missing_gap_count")),
                "winner_resume": _clean_text(row.get("winner_resume")),
                "resolved_resume": _clean_text(row.get("resolved_resume")),
                "packet_generation_allowed": _clean_text(row.get("packet_generation_allowed")),
                "packet_generation_block_reason": _clean_text(row.get("packet_generation_block_reason")),
                "critic_decision": _clean_text(row.get("critic_decision")),
                "critic_reason_codes": _clean_text(row.get("critic_reason_codes")),
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


def render_tailoring_decision_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    payload = render_tailoring_decisions(rows=rows)
    rendered_rows: List[Dict[str, str]] = []
    for item in payload["output"].get("decisions", []) or []:
        rendered_rows.append(
            {
                "job_id": _clean_text(item.get("job_id")),
                "company": _clean_text(item.get("company")),
                "title": _clean_text(item.get("title")),
                "source": _clean_text(item.get("source")),
                "existing_action": _clean_text(item.get("existing_action")),
                "advisory_priority": _clean_text(item.get("advisory_priority")),
                "tailoring_decision": _clean_text(item.get("tailoring_decision")),
                "tailoring_reason_codes": "|".join(
                    _clean_text(code)
                    for code in item.get("tailoring_reason_codes", []) or []
                    if _clean_text(code)
                ),
                "deterministic_winner_score": _clean_text(item.get("deterministic_winner_score")),
                "fallback_only_no_deterministic_match": _clean_text(item.get("fallback_only_no_deterministic_match")),
                "packet_generation_allowed": _clean_text(item.get("packet_generation_allowed")),
                "packet_generation_block_reason": _clean_text(item.get("packet_generation_block_reason")),
                "critic_decision": _clean_text(item.get("critic_decision")),
                "critic_reason_codes": _clean_text(item.get("critic_reason_codes")),
                "winner_resume": _clean_text(item.get("winner_resume")),
                "resolved_resume": _clean_text(item.get("resolved_resume")),
            }
        )
    return rendered_rows


def write_tailoring_decision_artifacts(
    *,
    rows: List[Dict[str, Any]],
    output_csv_path: str | Path,
    summary_json_path: str | Path | None = None,
    pipeline_run_id: str = "",
    owner_user_id: str = "",
    source_artifact_path: str = "",
) -> Dict[str, Any]:
    payload = render_tailoring_decisions(
        rows=rows,
        pipeline_run_id=pipeline_run_id,
        owner_user_id=owner_user_id,
        source_artifact_path=source_artifact_path,
    )
    output_path = Path(output_csv_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=TAILORING_DECISION_FIELDNAMES)
        writer.writeheader()
        for row in render_tailoring_decision_rows(rows):
            writer.writerow({field: row.get(field, "") for field in TAILORING_DECISION_FIELDNAMES})

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
        "row_count": len(payload["output"].get("decisions", []) or []),
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


TAILORING_SUGGESTION_DRY_RUN_SIGNAL_FIELDS = (
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
)


def _tailoring_suggestion_safety_metadata() -> Dict[str, bool]:
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


def _tailoring_suggestion_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [_clean_text(item) for item in value if _clean_text(item)]
    if isinstance(value, tuple):
        return [_clean_text(item) for item in value if _clean_text(item)]
    text = _clean_text(value)
    if not text:
        return []
    return [_clean_text(item) for item in re.split(r"[;,|]", text) if _clean_text(item)]


def _tailoring_suggestion_float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _tailoring_suggestion_int(value: Any) -> int:
    try:
        return max(0, int(float(value or 0)))
    except (TypeError, ValueError):
        return 0


def _tailoring_suggestion_norm(value: Any) -> str:
    return re.sub(r"[^a-z0-9+#.$%]+", " ", _clean_text(value).lower()).strip()


def _tailoring_suggestion_contains(text: str, signal: str) -> bool:
    signal_norm = _tailoring_suggestion_norm(signal)
    return bool(signal_norm and signal_norm in _tailoring_suggestion_norm(text))


def _tailoring_suggestion_resume_id(row: Dict[str, Any], index: int) -> str:
    return (
        _clean_text(row.get("resume_id"))
        or _clean_text(row.get("resume_name"))
        or _clean_text(row.get("name"))
        or _clean_text(row.get("id"))
        or f"resume_{index + 1}"
    )


def _tailoring_suggestion_evidence_items(row: Dict[str, Any]) -> List[Dict[str, str]]:
    items: List[Dict[str, str]] = []

    def add_item(text: Any, source_field: str, source_id: str = "") -> None:
        clean = _clean_text(text)
        if clean:
            items.append(
                {
                    "source_field": source_field,
                    "source_bullet_id": source_id,
                    "text": clean,
                }
            )

    bullets = row.get("bullets")
    bullet_ids = row.get("bullet_ids")
    if isinstance(bullets, list):
        ids = bullet_ids if isinstance(bullet_ids, list) else []
        for index, bullet in enumerate(bullets):
            add_item(bullet, "bullets", _clean_text(ids[index]) if index < len(ids) else f"bullet_{index + 1}")
    else:
        add_item(bullets, "bullets", _clean_text(row.get("source_bullet_id")) or _clean_text(row.get("bullet_id")))

    for field_name in (
        "raw_text",
        "normalized_text",
        "evidence_text",
        "summary",
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
        value = row.get(field_name)
        if isinstance(value, list):
            for index, item in enumerate(value):
                add_item(item, field_name, f"{field_name}_{index + 1}")
        elif isinstance(value, dict):
            for key, item in sorted(value.items()):
                add_item(item, field_name, _clean_text(key))
        else:
            add_item(value, field_name, _clean_text(row.get(f"{field_name}_id")))
    return items


def _tailoring_suggestion_unsupported_risk(signal: str, field_name: str) -> str:
    signal_norm = _tailoring_suggestion_norm(signal)
    if field_name in {"required_tools", "preferred_tools"}:
        return "unsupported_tool"
    if field_name in {"business_contexts", "stakeholder_contexts"}:
        return "unsupported_domain_or_context"
    if re.search(r"(\$|%|\b\d+(?:\.\d+)?x\b|\b\d+(?:\.\d+)?\s*(?:million|m|k|users|requests|latency|revenue)\b)", signal_norm):
        return "unsupported_metric"
    return "unsupported_claim"


def _tailoring_suggestion_empty_payload(
    *,
    selected_resume_id: str,
    missing_evidence: List[str],
    source_fields_used: List[str],
    context_id: str,
    job_id: str,
) -> Dict[str, Any]:
    return {
        "suggestion_status": "insufficient_evidence",
        "selected_resume_id": _clean_text(selected_resume_id),
        "patch_ready_suggestions": [],
        "guidance_only_suggestions": [],
        "rejected_suggestions": [],
        "missing_evidence": list(dict.fromkeys(missing_evidence)),
        "unsupported_claim_risks": [],
        "projected_score_delta": 0.0,
        "rationale": "Tailoring suggestion dry-run has limited evidence; no resume content, score, ranking, queue, approval, execution, or submission was changed.",
        "source_fields_used": source_fields_used,
        "context_id": _clean_text(context_id),
        "job_id": _clean_text(job_id),
        "safety_metadata": _tailoring_suggestion_safety_metadata(),
    }


def build_tailoring_suggestion_dry_run_payload(
    *,
    jd_intelligence: Dict[str, Any] | None = None,
    jd_signals: Dict[str, Any] | None = None,
    resume_match_payload: Dict[str, Any] | None = None,
    resume_variants: List[Dict[str, Any]] | None = None,
    resume_evidence_rows: List[Dict[str, Any]] | None = None,
    selected_resume_id: str = "",
    context_id: str = "",
    job_id: str = "",
) -> Dict[str, Any]:
    """Build deterministic tailoring suggestions from JD signals and resume evidence only."""

    jd_source = deepcopy(jd_intelligence if jd_intelligence is not None else jd_signals or {})
    match_payload = deepcopy(resume_match_payload or {})
    variants = deepcopy(resume_variants if resume_variants is not None else resume_evidence_rows or [])
    if not isinstance(jd_source, dict):
        jd_source = {}
    if not isinstance(match_payload, dict):
        match_payload = {}
    if not isinstance(variants, list):
        variants = []

    normalized_signals = {
        field_name: _tailoring_suggestion_list(jd_source.get(field_name))
        for field_name in TAILORING_SUGGESTION_DRY_RUN_SIGNAL_FIELDS
    }
    source_fields_used = [field for field, values in normalized_signals.items() if values]
    selected_id = (
        _clean_text(selected_resume_id)
        or _clean_text(match_payload.get("selected_resume_id"))
    )
    resume_rows = [row for row in variants if isinstance(row, dict)]
    selected_row: Dict[str, Any] = {}
    for index, row in enumerate(resume_rows):
        row_id = _tailoring_suggestion_resume_id(row, index)
        if selected_id and row_id == selected_id:
            selected_row = row
            break
    if not selected_row and resume_rows:
        selected_row = resume_rows[0]
        selected_id = _tailoring_suggestion_resume_id(selected_row, 0)

    missing_evidence: List[str] = []
    if not source_fields_used:
        missing_evidence.append("jd_signals_missing")
    if not match_payload:
        missing_evidence.append("resume_match_payload_missing")
    if not resume_rows:
        missing_evidence.append("resume_evidence_missing")
    if missing_evidence:
        return _tailoring_suggestion_empty_payload(
            selected_resume_id=selected_id,
            missing_evidence=missing_evidence,
            source_fields_used=source_fields_used,
            context_id=context_id,
            job_id=job_id,
        )

    evidence_items = _tailoring_suggestion_evidence_items(selected_row)
    if not evidence_items:
        missing_evidence.append("selected_resume_evidence_missing")

    patch_ready: List[Dict[str, Any]] = []
    guidance_only: List[Dict[str, Any]] = []
    rejected: List[Dict[str, Any]] = []
    unsupported_claim_risks: List[Dict[str, str]] = []
    suggestion_index = 1

    for field_name in TAILORING_SUGGESTION_DRY_RUN_SIGNAL_FIELDS:
        for signal in normalized_signals[field_name]:
            matched_items = [
                item for item in evidence_items
                if _tailoring_suggestion_contains(item.get("text"), signal)
            ]
            if matched_items and not patch_ready:
                item = matched_items[0]
                source_bullet_id = _clean_text(item.get("source_bullet_id")) or _clean_text(item.get("source_field"))
                original_text = _clean_text(item.get("text"))
                patch_ready.append(
                    {
                        "suggestion_id": f"tailoring_dry_run_{suggestion_index:03d}",
                        "source_bullet_id": source_bullet_id,
                        "original_text": original_text,
                        "suggested_text": original_text,
                        "reason": f"Existing resume evidence directly supports JD signal: {signal}.",
                        "evidence_spans": [original_text],
                        "jd_signal_links": [{"field": field_name, "signal": signal}],
                        "patch_ready": True,
                        "projected_score_delta": 0.03,
                        "risk_flags": [],
                    }
                )
                suggestion_index += 1
                continue

            risk = _tailoring_suggestion_unsupported_risk(signal, field_name)
            missing_key = f"{field_name}:{signal}:resume_evidence_missing"
            missing_evidence.append(missing_key)
            unsupported_claim_risks.append(
                {
                    "field": field_name,
                    "signal": signal,
                    "risk": risk,
                }
            )
            suggestion = {
                "suggestion_id": f"tailoring_dry_run_{suggestion_index:03d}",
                "source_bullet_id": "",
                "original_text": "",
                "suggested_text": f"Gather direct resume evidence before claiming {signal}.",
                "reason": f"No direct resume evidence was found for JD signal: {signal}.",
                "evidence_spans": [],
                "jd_signal_links": [{"field": field_name, "signal": signal}],
                "patch_ready": False,
                "projected_score_delta": 0.0,
                "risk_flags": [risk],
            }
            suggestion_index += 1
            if risk in {"unsupported_tool", "unsupported_metric", "unsupported_domain_or_context"}:
                rejected.append(suggestion)
            elif not guidance_only:
                guidance_only.append(suggestion)

    match_missing = [
        _clean_text(item)
        for item in list(match_payload.get("missing_evidence") or [])
        if _clean_text(item)
    ]
    missing_evidence = list(dict.fromkeys(missing_evidence + match_missing))
    projected_delta = round(sum(float(item.get("projected_score_delta", 0.0) or 0.0) for item in patch_ready), 4)
    if patch_ready:
        suggestion_status = "patch_ready_available"
    elif guidance_only:
        suggestion_status = "guidance_only"
    elif rejected:
        suggestion_status = "rejected_unsupported_claims"
    else:
        suggestion_status = "insufficient_evidence"

    return {
        "suggestion_status": suggestion_status,
        "selected_resume_id": selected_id,
        "patch_ready_suggestions": patch_ready,
        "guidance_only_suggestions": guidance_only,
        "rejected_suggestions": rejected,
        "missing_evidence": missing_evidence,
        "unsupported_claim_risks": unsupported_claim_risks,
        "projected_score_delta": projected_delta,
        "rationale": "Tailoring suggestion dry-run only promotes patch-ready edits when JD signals are directly supported by resume evidence.",
        "source_fields_used": source_fields_used,
        "context_id": _clean_text(context_id),
        "job_id": _clean_text(job_id),
        "safety_metadata": _tailoring_suggestion_safety_metadata(),
    }


def build_live_tailoring_suggestion_shadow_payload(
    *,
    jd_intelligence: Dict[str, Any] | None = None,
    resume_profile: Dict[str, Any] | None = None,
    context_id: str = "",
    job_id: str = "",
    adapter: Any = None,
    feature_enabled: bool = False,
) -> Dict[str, Any]:
    """Validate one injected tailoring provider response without applying edits."""

    fallback = build_tailoring_suggestion_dry_run_payload(
        jd_intelligence=jd_intelligence,
        resume_match_payload={"selected_resume_id": "shadow-resume"},
        resume_evidence_rows=[
            {
                "resume_id": "shadow-resume",
                **deepcopy(resume_profile or {}),
            }
        ],
        selected_resume_id="shadow-resume",
        context_id=context_id,
        job_id=job_id,
    )
    base = {
        **deepcopy(fallback),
        "read_only": True,
        "advisory_only": True,
        "suggestion_plan_only": True,
        "validation_status": "disabled",
        "validation_errors": ["feature_flag_disabled"],
        "fallback_used": True,
        "model_provider": "deterministic",
        "model_name": "tailoring_suggestion_shadow_fallback",
        "prompt_version": "tailoring-suggestion-shadow-v1",
        "token_usage": {},
        "cost": {},
        "latency_ms": 0,
    }
    base["safety_metadata"] = {
        **_tailoring_suggestion_safety_metadata(),
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
        "jd_intelligence": deepcopy(jd_intelligence or {}),
        "resume_profile": deepcopy(resume_profile or {}),
        "context_id": _clean_text(context_id),
        "job_id": _clean_text(job_id),
        "prompt_version": "tailoring-suggestion-shadow-v1",
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
            parsed = {**deepcopy(raw_response), **{
                key: deepcopy(value)
                for key, value in raw.items()
                if key != "raw_response"
            }}
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
    normalized_groups: Dict[str, List[Dict[str, Any]]] = {}
    for field_name in (
        "patch_ready_suggestions",
        "guidance_only_suggestions",
        "rejected_suggestions",
    ):
        value = parsed.get(field_name, [])
        if not isinstance(value, list):
            errors.append(f"{field_name}_not_list")
            normalized_groups[field_name] = []
            continue
        normalized_groups[field_name] = [
            deepcopy(item) for item in value if isinstance(item, dict)
        ]
        if len(normalized_groups[field_name]) != len(value):
            errors.append(f"{field_name}_items_must_be_objects")
    if not any(normalized_groups.values()):
        errors.append("provider_suggestions_missing")

    token_usage = parsed.get("token_usage")
    cost = parsed.get("cost")
    payload = {
        **deepcopy(base),
        **normalized_groups,
        "missing_evidence": _tailoring_suggestion_list(
            parsed.get("missing_evidence")
        ),
        "unsupported_claim_risks": [
            deepcopy(item)
            for item in parsed.get("unsupported_claim_risks", [])
            if isinstance(item, dict)
        ]
        if isinstance(parsed.get("unsupported_claim_risks", []), list)
        else [],
        "projected_score_delta": _tailoring_suggestion_float(
            parsed.get("projected_score_delta")
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
        "prompt_version": _clean_text(
            parsed.get("prompt_version")
        )
        or "tailoring-suggestion-shadow-v1",
        "token_usage": deepcopy(token_usage)
        if isinstance(token_usage, dict)
        else {},
        "cost": deepcopy(cost) if isinstance(cost, dict) else {},
        "latency_ms": _tailoring_suggestion_int(parsed.get("latency_ms")),
    }
    payload["suggestion_status"] = (
        "patch_ready_available"
        if payload["patch_ready_suggestions"]
        else "guidance_only"
        if payload["guidance_only_suggestions"]
        else "rejected_unsupported_claims"
        if payload["rejected_suggestions"]
        else "insufficient_evidence"
    )
    payload["safety_metadata"] = {
        **_tailoring_suggestion_safety_metadata(),
        "feature_flag_required": True,
        "deterministic_only": False,
        "did_call_llm": True,
        "did_write_database": False,
        "did_create_approval": False,
    }
    return payload
