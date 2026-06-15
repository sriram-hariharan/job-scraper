from __future__ import annotations

import os
import re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

from src.agents import llmops, trace as trace_store
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

    try:
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

        llmops_metadata = llmops.build_llmops_metadata(
            model_provider="deterministic",
            model_name="resume_match_rules",
            agent_name=AGENT_NAME,
            agent_version=AGENT_VERSION,
            schema_validation_status=validation_payload.get("validation_status", ""),
            fallback_used=output_payload.get("fallback_only_no_deterministic_match_count", 0) > 0,
        )
        step_record = llmops.merge_llmops_into_agent_step_kwargs(
            {
                "agent_run_id": agent_run_id,
                "owner_user_id": context["owner_user_id"],
                "pipeline_run_id": context["pipeline_run_id"],
                "context_id": context["context_id"],
                "agent_name": AGENT_NAME,
                "agent_version": AGENT_VERSION,
                "input_json": input_payload,
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


RESUME_MATCH_DRY_RUN_DIMENSIONS = (
    "hard_skills",
    "tools",
    "domain_workflow",
    "seniority",
    "ownership",
    "business_context",
    "stakeholder_communication",
    "production_engineering",
    "ai_ml_rag_llmops",
)


def _dry_run_safety_metadata() -> Dict[str, bool]:
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


def _dry_run_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [_clean_text(item) for item in value if _clean_text(item)]
    if isinstance(value, tuple):
        return [_clean_text(item) for item in value if _clean_text(item)]
    text = _clean_text(value)
    if not text:
        return []
    return [_clean_text(item) for item in re.split(r"[;,]", text) if _clean_text(item)]


def _dry_run_norm(value: Any) -> str:
    return re.sub(r"[^a-z0-9+#.]+", " ", _clean_text(value).lower()).strip()


def _dry_run_contains(text_norm: str, signal: str) -> bool:
    signal_norm = _dry_run_norm(signal)
    if not signal_norm:
        return False
    return signal_norm in text_norm


def _resume_variant_id(row: Dict[str, Any], index: int) -> str:
    return (
        _clean_text(row.get("resume_id"))
        or _clean_text(row.get("resume_name"))
        or _clean_text(row.get("name"))
        or _clean_text(row.get("id"))
        or f"resume_{index + 1}"
    )


def _resume_evidence_values(row: Dict[str, Any], fields: Iterable[str]) -> List[str]:
    values: List[str] = []
    for field_name in fields:
        value = row.get(field_name)
        if isinstance(value, list):
            values.extend(_clean_text(item) for item in value if _clean_text(item))
        elif isinstance(value, dict):
            values.extend(_clean_text(item) for item in value.values() if _clean_text(item))
        elif _clean_text(value):
            values.append(_clean_text(value))
    return values


def _resume_search_text(row: Dict[str, Any]) -> str:
    fields = [
        "resume_id",
        "resume_name",
        "title",
        "summary",
        "raw_text",
        "normalized_text",
        "evidence_text",
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
        "quantified_bullets",
        "bullets",
    ]
    return _dry_run_norm(" ".join(_resume_evidence_values(row, fields)))


def _dimension_signal_map(jd_signals: Dict[str, List[str]]) -> Dict[str, List[str]]:
    return {
        "hard_skills": jd_signals["required_skills"] + jd_signals["preferred_skills"],
        "tools": jd_signals["required_tools"] + jd_signals["preferred_tools"],
        "domain_workflow": (
            jd_signals["workflows"]
            + jd_signals["methods"]
            + jd_signals["business_contexts"]
        ),
        "seniority": jd_signals["seniority_signals"],
        "ownership": jd_signals["ownership_signals"],
        "business_context": jd_signals["business_contexts"],
        "stakeholder_communication": jd_signals["stakeholder_contexts"],
        "production_engineering": [
            signal
            for signal in (
                jd_signals["workflows"]
                + jd_signals["methods"]
                + jd_signals["required_tools"]
                + jd_signals["preferred_tools"]
            )
            if any(token in _dry_run_norm(signal) for token in ("production", "pipeline", "deploy", "airflow", "dbt", "engineering"))
        ],
        "ai_ml_rag_llmops": [
            signal
            for signal in (
                jd_signals["required_skills"]
                + jd_signals["preferred_skills"]
                + jd_signals["required_tools"]
                + jd_signals["preferred_tools"]
                + jd_signals["workflows"]
                + jd_signals["methods"]
            )
            if any(token in _dry_run_norm(signal) for token in ("ai", "ml", "machine learning", "rag", "llm", "llmops", "embedding"))
        ],
    }


def _score_resume_variant(
    *,
    resume_id: str,
    resume_row: Dict[str, Any],
    dimension_signals: Dict[str, List[str]],
) -> Dict[str, Any]:
    text_norm = _resume_search_text(resume_row)
    dimension_scores: Dict[str, float] = {}
    matched_evidence: List[Dict[str, str]] = []
    weak_evidence: List[str] = []
    missing_evidence: List[str] = []

    if not text_norm:
        missing_evidence.append("resume_evidence_missing")

    for dimension in RESUME_MATCH_DRY_RUN_DIMENSIONS:
        signals = list(dict.fromkeys(dimension_signals.get(dimension, [])))
        if not signals:
            dimension_scores[dimension] = 0.0
            missing_evidence.append(f"{dimension}:jd_signals_missing")
            continue

        matched = [signal for signal in signals if _dry_run_contains(text_norm, signal)]
        score = round(len(matched) / len(signals), 4) if signals else 0.0
        dimension_scores[dimension] = score
        for signal in matched:
            matched_evidence.append(
                {
                    "resume_id": resume_id,
                    "dimension": dimension,
                    "signal": signal,
                    "evidence": signal,
                }
            )
        if 0 < score < 0.5:
            weak_evidence.append(f"{dimension}:partial_coverage")
        if score == 0:
            missing_evidence.append(f"{dimension}:no_matching_resume_evidence")

    overall_score = round(
        sum(dimension_scores.values()) / len(RESUME_MATCH_DRY_RUN_DIMENSIONS),
        4,
    )
    if overall_score >= 0.70:
        recommendation_label = "strong_match"
        match_status = "strong_match"
    elif overall_score >= 0.40:
        recommendation_label = "partial_match"
        match_status = "partial_match"
    else:
        recommendation_label = "weak_match"
        match_status = "weak_match"

    return {
        "resume_id": resume_id,
        "score": overall_score,
        "match_status": match_status,
        "recommendation_label": recommendation_label,
        "dimension_scores": dimension_scores,
        "matched_evidence": matched_evidence,
        "weak_evidence": weak_evidence,
        "missing_evidence": missing_evidence,
    }


def build_resume_match_dry_run_payload(
    *,
    jd_intelligence: Dict[str, Any] | None = None,
    jd_signals: Dict[str, Any] | None = None,
    resume_variants: List[Dict[str, Any]] | None = None,
    resume_evidence_rows: List[Dict[str, Any]] | None = None,
    selected_resume_id: str = "",
    context_id: str = "",
    job_id: str = "",
) -> Dict[str, Any]:
    """Compare JD intelligence signals to resume evidence without side effects."""

    jd_source = deepcopy(jd_intelligence if jd_intelligence is not None else jd_signals or {})
    variants = deepcopy(resume_variants if resume_variants is not None else resume_evidence_rows or [])
    if not isinstance(jd_source, dict):
        jd_source = {}
    if not isinstance(variants, list):
        variants = []

    signal_fields = [
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
    ]
    normalized_jd_signals = {
        field_name: _dry_run_list(jd_source.get(field_name))
        for field_name in signal_fields
    }
    source_fields_used = [
        field_name for field_name, values in normalized_jd_signals.items() if values
    ]
    dimension_signals = _dimension_signal_map(normalized_jd_signals)
    missing_evidence: List[str] = []
    risk_flags: List[str] = []
    if not source_fields_used:
        missing_evidence.append("jd_signals_missing")
        risk_flags.append("low_information_jd")
    if not variants:
        missing_evidence.append("resume_evidence_missing")
        risk_flags.append("resume_evidence_unavailable")

    candidate_scores = [
        _score_resume_variant(
            resume_id=_resume_variant_id(row if isinstance(row, dict) else {}, index),
            resume_row=row if isinstance(row, dict) else {},
            dimension_signals=dimension_signals,
        )
        for index, row in enumerate(variants)
    ]
    candidate_scores = sorted(
        candidate_scores,
        key=lambda row: (-float(row.get("score", 0.0)), _clean_text(row.get("resume_id"))),
    )
    selected = (
        next(
            (row for row in candidate_scores if row["resume_id"] == _clean_text(selected_resume_id)),
            None,
        )
        if _clean_text(selected_resume_id)
        else None
    )
    selected = selected or (candidate_scores[0] if candidate_scores else {})
    selected_id = _clean_text(selected.get("resume_id"))

    dimension_scores = dict(selected.get("dimension_scores") or {
        dimension: 0.0 for dimension in RESUME_MATCH_DRY_RUN_DIMENSIONS
    })
    matched_evidence = list(selected.get("matched_evidence") or [])
    weak_evidence = list(selected.get("weak_evidence") or [])
    missing_evidence = list(dict.fromkeys(missing_evidence + list(selected.get("missing_evidence") or [])))
    score = float(selected.get("score", 0.0) or 0.0)
    if not candidate_scores:
        match_status = "insufficient_evidence"
        recommendation_label = "manual_review"
    elif not source_fields_used:
        match_status = "insufficient_jd_signals"
        recommendation_label = "manual_review"
    else:
        match_status = _clean_text(selected.get("match_status")) or "weak_match"
        recommendation_label = _clean_text(selected.get("recommendation_label")) or "manual_review"
    confidence = round(score, 4)
    rationale = (
        "Dry-run resume match compared JD intelligence signals against in-memory resume evidence only."
        if candidate_scores and source_fields_used
        else "Dry-run resume match has limited information; no production score, ranking, queue, or approval was changed."
    )

    return {
        "match_status": match_status,
        "selected_resume_id": selected_id,
        "candidate_resume_scores": candidate_scores,
        "dimension_scores": dimension_scores,
        "matched_evidence": matched_evidence,
        "weak_evidence": weak_evidence,
        "missing_evidence": missing_evidence,
        "risk_flags": list(dict.fromkeys(risk_flags)),
        "recommendation_label": recommendation_label,
        "confidence": confidence,
        "rationale": rationale,
        "source_fields_used": source_fields_used,
        "context_id": _clean_text(context_id),
        "job_id": _clean_text(job_id),
        "safety_metadata": _dry_run_safety_metadata(),
    }
