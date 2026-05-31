from __future__ import annotations

import csv
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

from src.agents import llmops, trace as trace_store
from src.agents.resume_match_agent import (
    TRACE_ENABLED_ENV,
    TRACE_STRICT_ENV,
    _truthy,
)


AGENT_NAME = "Source Health Agent"
AGENT_VERSION = "phase_2b_v1"

REQUIRED_COLUMNS = [
    "source",
    "company",
    "scraped_jobs",
    "title_pass_jobs",
    "location_pass_jobs",
    "freshness_pass_jobs",
    "not_recent_jobs",
    "missing_timestamp_jobs",
    "final_corpus_jobs",
]


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _int_value(value: Any) -> int:
    try:
        return int(float(str(value or "0").strip() or "0"))
    except (TypeError, ValueError):
        return 0


def _source_key(row: Dict[str, Any]) -> str:
    return _clean_text(row.get("source")).lower() or "<empty>"


def _company_label(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "source": _clean_text(row.get("source")),
        "company": _clean_text(row.get("company")),
    }


def _sum_by_source(rows: List[Dict[str, Any]], field: str) -> Dict[str, int]:
    totals: Dict[str, int] = {}
    for row in rows:
        source = _source_key(row)
        totals[source] = totals.get(source, 0) + _int_value(row.get(field))
    return dict(sorted(totals.items()))


def parse_source_health_report_csv(path: str | Path) -> List[Dict[str, str]]:
    report_path = Path(path)
    with report_path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def build_source_health_agent_input_payload(
    *,
    rows: List[Dict[str, Any]],
    pipeline_run_id: str = "",
    artifact_name: str = "",
    artifact_path: str = "",
) -> Dict[str, Any]:
    columns = sorted({str(key) for row in rows for key in row.keys()})
    return {
        "agent_name": AGENT_NAME,
        "agent_version": AGENT_VERSION,
        "pipeline_run_id": _clean_text(pipeline_run_id),
        "artifact_name": _clean_text(artifact_name) or (Path(artifact_path).name if artifact_path else ""),
        "artifact_path": _clean_text(artifact_path),
        "total_source_company_rows": len(rows),
        "source_list": sorted({_source_key(row) for row in rows if _source_key(row)}),
        "report_columns_detected": columns,
    }


def recommend_source_health_row(row: Dict[str, Any]) -> str:
    scraped = _int_value(row.get("scraped_jobs"))
    title_pass = _int_value(row.get("title_pass_jobs"))
    location_pass = _int_value(row.get("location_pass_jobs"))
    freshness_pass = _int_value(row.get("freshness_pass_jobs"))
    final_jobs = _int_value(row.get("final_corpus_jobs"))
    missing_timestamp = _int_value(row.get("missing_timestamp_jobs"))
    not_recent = _int_value(row.get("not_recent_jobs"))

    if final_jobs >= 5 and freshness_pass > 0 and missing_timestamp == 0:
        return "promote"
    if missing_timestamp > 0:
        return "needs_timestamp_fix"
    if 1 <= final_jobs <= 4 and freshness_pass > 0:
        return "keep"
    if title_pass > 0 and location_pass > 0 and freshness_pass > 0 and final_jobs == 0:
        return "needs_detail_enrichment"
    if scraped > 0 and final_jobs == 0 and freshness_pass == 0 and not_recent > 0:
        return "demote"
    return "monitor"


def build_source_health_agent_output_payload(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    recommendations = []
    for row in rows:
        recommendation = recommend_source_health_row(row)
        recommendations.append(
            {
                **_company_label(row),
                "recommendation": recommendation,
                "scraped_jobs": _int_value(row.get("scraped_jobs")),
                "freshness_pass_jobs": _int_value(row.get("freshness_pass_jobs")),
                "missing_timestamp_jobs": _int_value(row.get("missing_timestamp_jobs")),
                "final_corpus_jobs": _int_value(row.get("final_corpus_jobs")),
            }
        )

    top_companies = sorted(
        (
            {
                **_company_label(row),
                "final_corpus_jobs": _int_value(row.get("final_corpus_jobs")),
            }
            for row in rows
        ),
        key=lambda item: (-item["final_corpus_jobs"], item["source"], item["company"]),
    )
    top_companies = [item for item in top_companies if item["final_corpus_jobs"] > 0][:10]

    return {
        "total_rows": len(rows),
        "source_counts": {
            source: sum(1 for row in rows if _source_key(row) == source)
            for source in sorted({_source_key(row) for row in rows})
        },
        "final_jobs_by_source": _sum_by_source(rows, "final_corpus_jobs"),
        "scraped_jobs_by_source": _sum_by_source(rows, "scraped_jobs"),
        "title_pass_by_source": _sum_by_source(rows, "title_pass_jobs"),
        "location_pass_by_source": _sum_by_source(rows, "location_pass_jobs"),
        "freshness_pass_by_source": _sum_by_source(rows, "freshness_pass_jobs"),
        "missing_timestamp_by_source": _sum_by_source(rows, "missing_timestamp_jobs"),
        "not_recent_by_source": _sum_by_source(rows, "not_recent_jobs"),
        "top_companies_by_final_jobs": top_companies,
        "zero_final_but_fresh_companies": [
            _company_label(row)
            for row in rows
            if _int_value(row.get("final_corpus_jobs")) == 0
            and _int_value(row.get("freshness_pass_jobs")) > 0
        ],
        "stale_heavy_companies": [
            _company_label(row)
            for row in rows
            if _int_value(row.get("final_corpus_jobs")) == 0
            and _int_value(row.get("not_recent_jobs")) > 0
            and _int_value(row.get("freshness_pass_jobs")) == 0
        ],
        "missing_timestamp_companies": [
            _company_label(row)
            for row in rows
            if _int_value(row.get("missing_timestamp_jobs")) > 0
        ],
        "recommendations": recommendations,
    }


def build_source_health_agent_validation_payload(
    *,
    input_payload: Dict[str, Any],
    output_payload: Dict[str, Any],
    rows: List[Dict[str, Any]],
) -> Dict[str, Any]:
    reason_codes: List[str] = []
    detected = set(input_payload.get("report_columns_detected", []) or [])
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in detected]
    required_columns_present = not missing_columns
    if not required_columns_present:
        reason_codes.append("missing_required_columns")

    row_count_matches = (
        int(input_payload.get("total_source_company_rows", 0) or 0)
        == int(output_payload.get("total_rows", 0) or 0)
        == len(rows)
    )
    if not row_count_matches:
        reason_codes.append("row_count_mismatch")

    recommendation_count_matches_rows = len(output_payload.get("recommendations", []) or []) == len(rows)
    if not recommendation_count_matches_rows:
        reason_codes.append("recommendation_count_mismatch")

    validation_status = "passed" if not reason_codes else "failed"
    return {
        "required_columns_present": required_columns_present,
        "missing_required_columns": missing_columns,
        "row_count_matches": row_count_matches,
        "recommendation_count_matches_rows": recommendation_count_matches_rows,
        "no_mutation_performed": True,
        "validation_status": validation_status,
        "reason_codes": reason_codes,
    }


def build_source_health_agent_summary_payload(
    *,
    input_payload: Dict[str, Any],
    output_payload: Dict[str, Any],
    validation_payload: Dict[str, Any],
) -> Dict[str, Any]:
    recommendation_counts: Dict[str, int] = {}
    for item in output_payload.get("recommendations", []) or []:
        recommendation = _clean_text(item.get("recommendation")) or "monitor"
        recommendation_counts[recommendation] = recommendation_counts.get(recommendation, 0) + 1

    return {
        "agent_name": AGENT_NAME,
        "agent_version": AGENT_VERSION,
        "pipeline_run_id": input_payload.get("pipeline_run_id", ""),
        "total_rows": output_payload.get("total_rows", 0),
        "recommendation_counts": dict(sorted(recommendation_counts.items())),
        "validation_status": validation_payload.get("validation_status", ""),
        "reason_codes": list(validation_payload.get("reason_codes", []) or []),
    }


def render_source_health_recommendations(
    *,
    rows: List[Dict[str, Any]],
    pipeline_run_id: str = "",
    artifact_name: str = "",
    artifact_path: str = "",
) -> Dict[str, Any]:
    input_payload = build_source_health_agent_input_payload(
        rows=rows,
        pipeline_run_id=pipeline_run_id,
        artifact_name=artifact_name,
        artifact_path=artifact_path,
    )
    output_payload = build_source_health_agent_output_payload(rows)
    validation_payload = build_source_health_agent_validation_payload(
        input_payload=input_payload,
        output_payload=output_payload,
        rows=rows,
    )
    summary_payload = build_source_health_agent_summary_payload(
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
        context_id = f"source_health:{pipeline_run_id}"
    return {
        "pipeline_run_id": pipeline_run_id,
        "owner_user_id": owner_user_id,
        "context_id": context_id,
    }


def record_source_health_agent_trace(
    *,
    rows: List[Dict[str, Any]],
    artifact_path: str = "",
    artifact_name: str = "",
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
        payload = render_source_health_recommendations(
            rows=rows,
            pipeline_run_id=context["pipeline_run_id"],
            artifact_name=artifact_name,
            artifact_path=artifact_path,
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
            model_name="source_health_rules",
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
