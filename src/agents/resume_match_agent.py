from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

from src.agents import trace as trace_store
from src.config.settings import SCORER_V2_POLICY
from src.pipeline.resume_selection_credibility import parse_bool, parse_float


AGENT_NAME = "Resume Match Agent"
AGENT_VERSION = "phase_2a_v1"
TRACE_ENABLED_ENV = "APPLYLENS_AGENT_TRACE_ENABLED"
TRACE_STRICT_ENV = "APPLYLENS_AGENT_TRACE_STRICT"


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _truthy(value: Any) -> bool:
    return _clean_text(value).lower() in {"1", "true", "yes", "on"}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _distribution(values: Iterable[Any]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for value in values:
        key = _clean_text(value) or "<empty>"
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (item[0] == "<empty>", item[0])))


def _score_bucket(score: float) -> str:
    if score <= 0:
        return "score_zero"
    if score < 0.50:
        return "score_lt_050"
    if score < 0.60:
        return "score_050_059"
    if score < 0.70:
        return "score_060_069"
    return "score_070_plus"


def _selector_score(row: Dict[str, Any]) -> float:
    raw = _clean_text(row.get("selector_winner_score"))
    if raw:
        return parse_float(raw)
    return parse_float(row.get("winner_score"))


def build_resume_match_agent_input_payload(
    *,
    rows: List[Dict[str, Any]],
    candidate_resume_names: List[str],
    pipeline_run_id: str = "",
    owner_user_id: str = "",
    source_artifact_path: str = "",
    selector_policy: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    considered_values = [
        int(parse_float(row.get("resume_variants_considered", 0)))
        for row in rows
    ]
    return {
        "agent_name": AGENT_NAME,
        "agent_version": AGENT_VERSION,
        "pipeline_run_id": _clean_text(pipeline_run_id),
        "owner_user_id": _clean_text(owner_user_id),
        "job_count": len(rows),
        "resume_variants_considered_distribution": _distribution(considered_values),
        "candidate_resume_names": sorted({_clean_text(name) for name in candidate_resume_names if _clean_text(name)}),
        "selector_policy": selector_policy or SCORER_V2_POLICY.get("selector", {}),
        "source_artifact_path": _clean_text(source_artifact_path),
        "source_artifact_name": Path(source_artifact_path).name if _clean_text(source_artifact_path) else "",
    }


def build_resume_match_agent_output_payload(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    score_buckets = {
        "score_zero": 0,
        "score_lt_050": 0,
        "score_050_059": 0,
        "score_060_069": 0,
        "score_070_plus": 0,
    }
    for row in rows:
        score_buckets[_score_bucket(_selector_score(row))] += 1

    return {
        "total_rows": len(rows),
        "deterministic_winner_count": sum(
            1 for row in rows if parse_bool(row.get("deterministic_winner_available"))
        ),
        "fallback_only_no_deterministic_match_count": sum(
            1 for row in rows if parse_bool(row.get("fallback_only_no_deterministic_match"))
        ),
        "deterministic_equivalent_variant_count": sum(
            1
            for row in rows
            if _clean_text(row.get("resolved_resume_source")) == "deterministic_equivalent_variants"
        ),
        "llm_adjudication_selected_count": sum(
            1
            for row in rows
            if _clean_text(row.get("resolved_resume_source")).startswith("llm_adjudication")
        ),
        "low_confidence_blocked_count": sum(
            1
            for row in rows
            if _clean_text(row.get("packet_generation_block_reason"))
            == "deterministic_score_below_credible_threshold"
        ),
        "packet_generation_allowed_count": sum(
            1 for row in rows if parse_bool(row.get("packet_generation_allowed"))
        ),
        "selected_resume_distribution": _distribution(
            row.get("winner_resume") or row.get("resolved_resume") for row in rows
        ),
        "runner_up_resume_distribution": _distribution(row.get("runner_up_resume") for row in rows),
        "score_buckets": score_buckets,
    }


def build_resume_match_agent_validation_payload(
    *,
    input_payload: Dict[str, Any],
    output_payload: Dict[str, Any],
    rows: List[Dict[str, Any]],
) -> Dict[str, Any]:
    reason_codes: List[str] = []
    input_count = int(input_payload.get("job_count", 0) or 0)
    output_count = int(output_payload.get("total_rows", 0) or 0)
    output_row_count_matches_input = input_count == output_count == len(rows)
    if not output_row_count_matches_input:
        reason_codes.append("output_row_count_mismatch")

    fallback_only_rows = [
        row for row in rows if parse_bool(row.get("fallback_only_no_deterministic_match"))
    ]
    fallback_only_packet_blocked = all(
        not parse_bool(row.get("packet_generation_allowed")) for row in fallback_only_rows
    )
    if not fallback_only_packet_blocked:
        reason_codes.append("fallback_only_packet_allowed")

    zero_score_fallback_rows = [
        row
        for row in fallback_only_rows
        if _selector_score(row) <= 0
    ]
    zero_score_fallback_blocked = all(
        not parse_bool(row.get("packet_generation_allowed"))
        for row in zero_score_fallback_rows
    )
    if not zero_score_fallback_blocked:
        reason_codes.append("zero_score_fallback_packet_allowed")

    deterministic_gte_050_rows = [
        row
        for row in rows
        if parse_bool(row.get("deterministic_winner_available"))
        and _selector_score(row) >= 0.50
    ]
    deterministic_gte_050_can_be_packet_allowed = all(
        parse_bool(row.get("packet_generation_allowed"))
        or _clean_text(row.get("packet_generation_block_reason")) not in {
            "fallback_only_no_deterministic_match",
            "deterministic_score_below_credible_threshold",
        }
        for row in deterministic_gte_050_rows
    )
    if not deterministic_gte_050_can_be_packet_allowed:
        reason_codes.append("credible_deterministic_packet_blocked")

    validation_status = "passed" if not reason_codes else "failed"
    return {
        "output_row_count_matches_input": output_row_count_matches_input,
        "fallback_only_rows_have_packet_generation_allowed_false": fallback_only_packet_blocked,
        "zero_score_fallback_rows_are_not_packet_allowed": zero_score_fallback_blocked,
        "deterministic_rows_with_score_gte_050_can_be_packet_allowed": deterministic_gte_050_can_be_packet_allowed,
        "validation_status": validation_status,
        "reason_codes": reason_codes,
    }


def build_resume_match_agent_summary_payload(
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
        "job_count": input_payload.get("job_count", 0),
        "total_rows": output_payload.get("total_rows", 0),
        "deterministic_winner_count": output_payload.get("deterministic_winner_count", 0),
        "fallback_only_no_deterministic_match_count": output_payload.get(
            "fallback_only_no_deterministic_match_count", 0
        ),
        "packet_generation_allowed_count": output_payload.get("packet_generation_allowed_count", 0),
        "validation_status": validation_payload.get("validation_status", ""),
        "reason_codes": list(validation_payload.get("reason_codes", []) or []),
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
        context_id = f"resume_match:{pipeline_run_id}"
    return {
        "pipeline_run_id": pipeline_run_id,
        "owner_user_id": owner_user_id,
        "context_id": context_id,
    }


def record_resume_match_agent_trace(
    *,
    rows: List[Dict[str, Any]],
    candidate_resume_names: List[str],
    source_artifact_path: str,
    env: Dict[str, str] | None = None,
    trace_module: Any = trace_store,
) -> Dict[str, Any]:
    env_map = env if env is not None else os.environ
    if not agent_trace_enabled(env_map):
        return {"attempted": False, "reason": "trace_disabled"}

    context = trace_context_from_env(env_map)
    if not context["owner_user_id"] or not context["pipeline_run_id"]:
        return {"attempted": False, "reason": "missing_trace_context", **context}

    started_at = _utc_now_iso()
    input_payload = build_resume_match_agent_input_payload(
        rows=rows,
        candidate_resume_names=candidate_resume_names,
        pipeline_run_id=context["pipeline_run_id"],
        owner_user_id=context["owner_user_id"],
        source_artifact_path=source_artifact_path,
    )
    output_payload = build_resume_match_agent_output_payload(rows)
    validation_payload = build_resume_match_agent_validation_payload(
        input_payload=input_payload,
        output_payload=output_payload,
        rows=rows,
    )
    summary_payload = build_resume_match_agent_summary_payload(
        input_payload=input_payload,
        output_payload=output_payload,
        validation_payload=validation_payload,
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

    step_payload = trace_module.record_agent_step(
        record={
            "agent_run_id": agent_run_id,
            "owner_user_id": context["owner_user_id"],
            "pipeline_run_id": context["pipeline_run_id"],
            "context_id": context["context_id"],
            "agent_name": AGENT_NAME,
            "agent_version": AGENT_VERSION,
            "input_json": input_payload,
            "status": "running",
            "started_at": started_at,
        }
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
