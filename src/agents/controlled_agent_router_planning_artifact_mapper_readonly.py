"""Read-only mapper from planning-like rows to router batch items."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from src.agents.controlled_agent_router_batch_handoff_plan_readonly import (
    build_controlled_agent_router_batch_handoff_plan_readonly,
)


PHASE = "33D"

JOB_FIELDS = ("job_id", "id", "title", "company", "location", "url")
GENERATED_TAILORING_FIELDS = (
    "generated_text",
    "generated_tailoring_text",
    "tailored_resume_text",
    "real_tailoring_output",
    "resume_rewrite",
    "rewritten_resume",
    "draft_resume",
    "tailored_bullets",
    "generated_bullets",
    "suggestions",
)


def _is_present(value: Any) -> bool:
    return value not in (None, "", [], {})


def _first_present(row: dict[str, Any], names: tuple[str, ...]) -> Any:
    for name in names:
        if name in row and _is_present(row[name]):
            return row[name]
    return None


def _truth_marker(row: dict[str, Any], names: tuple[str, ...]) -> bool | None:
    for name in names:
        value = row.get(name)
        if isinstance(value, bool):
            return value
    return None


def _numeric_value(value: Any) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def _item_id(row: dict[str, Any], index: int) -> str:
    value = _first_present(row, ("item_id", "job_id", "id"))
    return str(value) if value not in (None, "") else f"planning-row-{index}"


def _job_record(row: dict[str, Any]) -> dict[str, Any] | None:
    job = {
        field: deepcopy(row[field])
        for field in JOB_FIELDS
        if field in row and _is_present(row[field])
    }
    if "url" in job and "job_url" not in job:
        job["job_url"] = job["url"]
    return job or None


def _relevance_result(row: dict[str, Any]) -> dict[str, Any] | None:
    supplied = row.get("relevance_result")
    if isinstance(supplied, dict):
        return deepcopy(supplied)

    relevant = _truth_marker(row, ("is_relevant", "relevant", "prefilter_pass"))
    result: dict[str, Any] = {}
    if relevant is not None:
        result["is_relevant"] = relevant
    rejection_reasons = row.get("rejection_reasons")
    if _is_present(rejection_reasons):
        result["rejection_reasons"] = deepcopy(rejection_reasons)
        if relevant is None:
            result["is_relevant"] = False
    return result or None


def _jd_intelligence_result(row: dict[str, Any]) -> dict[str, Any] | None:
    for name in ("jd_intelligence_result", "jd_intelligence"):
        supplied = row.get(name)
        if isinstance(supplied, dict):
            return deepcopy(supplied)

    result: dict[str, Any] = {}
    for source, target in (
        ("jd_signals", "signals"),
        ("required_skills", "required_skills"),
        ("preferred_skills", "preferred_skills"),
        ("responsibilities", "responsibilities"),
    ):
        if _is_present(row.get(source)):
            result[target] = deepcopy(row[source])
    return result or None


def _final_score_result(row: dict[str, Any]) -> dict[str, Any] | None:
    for name in ("final_score", "score", "fit_score", "application_score"):
        value = _numeric_value(row.get(name))
        if value is not None:
            return {"final_score": value, "source_field": name}
    return None


def _tailoring_opportunity_result(row: dict[str, Any]) -> dict[str, Any] | None:
    supplied = row.get("tailoring_opportunity")
    if isinstance(supplied, dict):
        return deepcopy(supplied)

    helpful = _truth_marker(
        row,
        ("tailoring_may_help", "tailoring_recommended"),
    )
    if helpful is None:
        return None
    return {"tailoring_may_help": helpful}


def _manual_tailoring_preview_result(row: dict[str, Any]) -> dict[str, Any] | None:
    supplied = row.get("manual_tailoring_preview")
    if isinstance(supplied, dict):
        source = supplied
    elif any(_is_present(row.get(name)) for name in ("preview_ready", "preview_packet")):
        source = {
            "preview_ready": row.get("preview_ready"),
            "preview_packet_present": _is_present(row.get("preview_packet")),
        }
    else:
        return None

    result: dict[str, Any] = {}
    for key, value in source.items():
        lowered = str(key).lower()
        if key in GENERATED_TAILORING_FIELDS:
            continue
        if any(marker in lowered for marker in ("generated", "rewrite")):
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            result[key] = deepcopy(value)
    return result or {"preview_present": True}


def _mapped_item(row: dict[str, Any], index: int) -> dict[str, Any]:
    item: dict[str, Any] = {"item_id": _item_id(row, index)}
    for key, value in (
        ("job_record", _job_record(row)),
        ("relevance_result", _relevance_result(row)),
        ("jd_intelligence_result", _jd_intelligence_result(row)),
        ("final_score_result", _final_score_result(row)),
        ("tailoring_opportunity_result", _tailoring_opportunity_result(row)),
        ("manual_tailoring_preview_result", _manual_tailoring_preview_result(row)),
    ):
        if value is not None:
            item[key] = value
    return item


def _mapper_key(
    *,
    row_count: int,
    valid_count: int,
    invalid_count: int,
    next_step_counts: dict[str, int],
) -> str:
    steps = ",".join(f"{step}:{count}" for step, count in next_step_counts.items())
    return "|".join(
        (
            f"phase={PHASE}",
            f"rows={row_count}",
            f"valid={valid_count}",
            f"invalid={invalid_count}",
            f"steps={steps}",
        )
    )


def _payload(
    *,
    planning_row_count: int,
    valid_planning_row_count: int,
    invalid_planning_row_count: int,
    mapped_items: list[dict[str, Any]],
    unmapped_rows: list[dict[str, Any]],
    field_mapping_summary: dict[str, int],
    batch_handoff_plan: dict[str, Any],
    missing_inputs: list[str],
) -> dict[str, Any]:
    grouped = batch_handoff_plan.get("grouped_by_next_allowed_step", {})
    counts = batch_handoff_plan.get("next_step_counts", {})
    return {
        "phase": PHASE,
        "default_off": True,
        "read_only": True,
        "advisory_only": True,
        "planning_artifact_mapper_only": True,
        "controlled_agent_router_planning_mapper": True,
        "allowlisted_routing_only": True,
        "requires_manual_user_control": True,
        "planning_row_count": planning_row_count,
        "valid_planning_row_count": valid_planning_row_count,
        "invalid_planning_row_count": invalid_planning_row_count,
        "mapped_items": deepcopy(mapped_items),
        "unmapped_rows": deepcopy(unmapped_rows),
        "field_mapping_summary": deepcopy(field_mapping_summary),
        "batch_handoff_plan": deepcopy(batch_handoff_plan),
        "grouped_by_next_allowed_step": deepcopy(grouped),
        "next_step_counts": deepcopy(counts),
        "mapper_findings": {
            "batch_planner_called": isinstance(batch_handoff_plan, dict),
            "stage_execution_performed": False,
            "mapped_item_count": len(mapped_items),
        },
        "missing_inputs": list(missing_inputs),
        "mapper_key": _mapper_key(
            row_count=planning_row_count,
            valid_count=valid_planning_row_count,
            invalid_count=invalid_planning_row_count,
            next_step_counts=counts,
        ),
        "no_llm_calls": True,
        "llm_call_performed": False,
        "no_provider_calls": True,
        "provider_call_performed": False,
        "no_network_calls": True,
        "network_call_performed": False,
        "dispatch_performed": False,
        "stage_execution_performed": False,
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


def _empty_batch_plan() -> dict[str, Any]:
    return {
        "grouped_by_next_allowed_step": {},
        "next_step_counts": {},
        "handoff_plan": [],
        "batch_items": [],
        "blocked_items": [],
    }


def build_controlled_agent_router_planning_artifact_mapper_readonly(
    planning_rows: list[dict[str, Any]] | None = None,
    router_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Map supplied planning-like rows into a read-only batch handoff plan."""

    if not isinstance(planning_rows, list):
        return _payload(
            planning_row_count=0,
            valid_planning_row_count=0,
            invalid_planning_row_count=1,
            mapped_items=[],
            unmapped_rows=[
                {
                    "input_index": None,
                    "reason": "planning_rows must be supplied as a list",
                }
            ],
            field_mapping_summary={},
            batch_handoff_plan=_empty_batch_plan(),
            missing_inputs=["planning_rows"],
        )

    mapped_items: list[dict[str, Any]] = []
    unmapped_rows: list[dict[str, Any]] = []
    field_mapping_summary = {
        "job_record": 0,
        "relevance_result": 0,
        "jd_intelligence_result": 0,
        "final_score_result": 0,
        "tailoring_opportunity_result": 0,
        "manual_tailoring_preview_result": 0,
    }

    for index, row in enumerate(planning_rows):
        if not isinstance(row, dict):
            unmapped_rows.append(
                {
                    "input_index": index,
                    "reason": "planning row must be a dictionary",
                }
            )
            continue
        item = _mapped_item(row, index)
        mapped_items.append(item)
        for key in field_mapping_summary:
            if key in item:
                field_mapping_summary[key] += 1

    batch_handoff_plan = build_controlled_agent_router_batch_handoff_plan_readonly(
        items=mapped_items,
        router_policy=router_policy,
    )
    return _payload(
        planning_row_count=len(planning_rows),
        valid_planning_row_count=len(mapped_items),
        invalid_planning_row_count=len(unmapped_rows),
        mapped_items=mapped_items,
        unmapped_rows=unmapped_rows,
        field_mapping_summary=field_mapping_summary,
        batch_handoff_plan=batch_handoff_plan,
        missing_inputs=[],
    )
