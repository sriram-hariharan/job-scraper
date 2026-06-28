"""Default-off JD intelligence enricher for planning artifact rows."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from src.agents.controlled_agent_router_planning_artifact_mapper_readonly import (
    build_controlled_agent_router_planning_artifact_mapper_readonly,
)
from src.agents.jd_intelligence_llm_signal_extractor_default_off import (
    build_jd_intelligence_llm_signal_extractor_default_off,
)


PHASE = "34B"
JD_TEXT_FIELDS = ("jd_text", "job_description", "description", "posting_text")


def _is_present(value: Any) -> bool:
    return value not in (None, "", [], {})


def _text(value: Any) -> str:
    return str(value or "").strip()


def _row_key(row: dict[str, Any], index: int) -> str:
    for name in ("item_id", "job_id", "id"):
        value = row.get(name)
        if _is_present(value):
            return str(value)
    return str(index)


def _jd_text(row: dict[str, Any]) -> str:
    for name in JD_TEXT_FIELDS:
        value = row.get(name)
        if _is_present(value):
            return _text(value)
    return ""


def _job_record(row: dict[str, Any]) -> dict[str, Any]:
    record: dict[str, Any] = {}
    for name in ("job_id", "id", "title", "company", "location", "url"):
        if _is_present(row.get(name)):
            record[name] = deepcopy(row[name])
    if "url" in record and "job_url" not in record:
        record["job_url"] = record["url"]
    return record


def _provider_response_for_row(
    provider_responses: Any,
    *,
    row: dict[str, Any],
    index: int,
) -> Any:
    if isinstance(provider_responses, list):
        return provider_responses[index] if index < len(provider_responses) else None
    if isinstance(provider_responses, dict):
        keys = [_row_key(row, index), str(index)]
        for name in ("item_id", "job_id", "id"):
            if _is_present(row.get(name)):
                keys.append(str(row[name]))
        for key in keys:
            if key in provider_responses:
                return provider_responses[key]
    return None


def _empty_mapper_result() -> dict[str, Any]:
    return build_controlled_agent_router_planning_artifact_mapper_readonly(
        planning_rows=[],
        router_policy=None,
    )


def _enricher_key(
    *,
    row_count: int,
    valid_count: int,
    invalid_count: int,
    ready_count: int,
    blocked_count: int,
    next_step_counts: dict[str, int],
) -> str:
    steps = ",".join(f"{step}:{count}" for step, count in next_step_counts.items())
    return "|".join(
        (
            f"phase={PHASE}",
            f"rows={row_count}",
            f"valid={valid_count}",
            f"invalid={invalid_count}",
            f"ready={ready_count}",
            f"blocked={blocked_count}",
            f"steps={steps}",
        )
    )


def _payload(
    *,
    llm_enabled: bool,
    planning_row_count: int,
    valid_planning_row_count: int,
    invalid_planning_row_count: int,
    enriched_rows: list[dict[str, Any]],
    unmapped_rows: list[dict[str, Any]],
    extraction_results: list[dict[str, Any]],
    provider_callable_present: bool,
    provider_responses_present: bool,
    mapper_result: dict[str, Any],
    missing_inputs: list[str],
) -> dict[str, Any]:
    grouped = deepcopy(mapper_result.get("grouped_by_next_allowed_step", {}))
    counts = deepcopy(mapper_result.get("next_step_counts", {}))
    ready_count = sum(
        1 for result in extraction_results if result.get("extraction_ready") is True
    )
    blocked_count = len(extraction_results) - ready_count
    invocation_count = sum(
        1
        for result in extraction_results
        if result.get("provider_callable_invoked") is True
    )
    return {
        "phase": PHASE,
        "default_off": True,
        "jd_intelligence_planning_artifact_enricher": True,
        "llm_capable": True,
        "llm_enabled": llm_enabled,
        "read_only": True,
        "advisory_only": True,
        "requires_manual_user_control": True,
        "planning_row_count": planning_row_count,
        "valid_planning_row_count": valid_planning_row_count,
        "invalid_planning_row_count": invalid_planning_row_count,
        "enriched_rows": deepcopy(enriched_rows),
        "unmapped_rows": deepcopy(unmapped_rows),
        "extraction_results": deepcopy(extraction_results),
        "extraction_ready_count": ready_count,
        "extraction_blocked_count": blocked_count,
        "provider_callable_present": provider_callable_present,
        "provider_callable_invocation_count": invocation_count,
        "provider_responses_present": provider_responses_present,
        "mapper_result": deepcopy(mapper_result),
        "grouped_by_next_allowed_step": grouped,
        "next_step_counts": counts,
        "enricher_findings": {
            "phase34a_extractor_used": True,
            "phase33d_mapper_called": isinstance(mapper_result, dict),
            "provider_callable_invoked_only_when_enabled": True,
            "enriched_row_count": len(enriched_rows),
        },
        "missing_inputs": list(missing_inputs),
        "enricher_key": _enricher_key(
            row_count=planning_row_count,
            valid_count=valid_planning_row_count,
            invalid_count=invalid_planning_row_count,
            ready_count=ready_count,
            blocked_count=blocked_count,
            next_step_counts=counts,
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


def build_jd_intelligence_planning_artifact_enricher_default_off(
    planning_rows: list[dict[str, Any]] | None = None,
    enable_llm: bool = False,
    provider_callable: Any = None,
    provider_responses: Any = None,
    extraction_policy: dict[str, Any] | None = None,
    router_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Enrich planning-like rows with JD signals before read-only router mapping."""

    llm_enabled = enable_llm is True
    provider_callable_present = callable(provider_callable)
    provider_responses_present = provider_responses is not None

    if not isinstance(planning_rows, list):
        return _payload(
            llm_enabled=llm_enabled,
            planning_row_count=0,
            valid_planning_row_count=0,
            invalid_planning_row_count=1,
            enriched_rows=[],
            unmapped_rows=[
                {
                    "input_index": None,
                    "reason": "planning_rows must be supplied as a list",
                }
            ],
            extraction_results=[],
            provider_callable_present=provider_callable_present,
            provider_responses_present=provider_responses_present,
            mapper_result=_empty_mapper_result(),
            missing_inputs=["planning_rows"],
        )

    enriched_rows: list[dict[str, Any]] = []
    unmapped_rows: list[dict[str, Any]] = []
    extraction_results: list[dict[str, Any]] = []

    for index, row in enumerate(planning_rows):
        if not isinstance(row, dict):
            unmapped_rows.append(
                {
                    "input_index": index,
                    "reason": "planning row must be a dictionary",
                }
            )
            continue

        copied = deepcopy(row)
        response = _provider_response_for_row(
            provider_responses,
            row=copied,
            index=index,
        )
        extraction = build_jd_intelligence_llm_signal_extractor_default_off(
            jd_text=_jd_text(copied),
            job_record=_job_record(copied),
            enable_llm=llm_enabled,
            provider_callable=provider_callable if response is None else None,
            provider_response=response,
            extraction_policy=extraction_policy,
        )
        extraction_results.append(
            {
                "input_index": index,
                "row_key": _row_key(copied, index),
                **deepcopy(extraction),
            }
        )
        if extraction.get("extraction_ready") is True:
            jd_signals = deepcopy(extraction.get("jd_signals", {}))
            copied["jd_intelligence_result"] = jd_signals
            copied["jd_intelligence"] = deepcopy(jd_signals)
        enriched_rows.append(copied)

    mapper_result = build_controlled_agent_router_planning_artifact_mapper_readonly(
        planning_rows=enriched_rows,
        router_policy=router_policy,
    )
    return _payload(
        llm_enabled=llm_enabled,
        planning_row_count=len(planning_rows),
        valid_planning_row_count=len(enriched_rows),
        invalid_planning_row_count=len(unmapped_rows),
        enriched_rows=enriched_rows,
        unmapped_rows=unmapped_rows,
        extraction_results=extraction_results,
        provider_callable_present=provider_callable_present,
        provider_responses_present=provider_responses_present,
        mapper_result=mapper_result,
        missing_inputs=[],
    )
