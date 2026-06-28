"""Read-only batch handoff planner for the controlled agent router."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from src.agents.controlled_agent_router_workflow_state_adapter_readonly import (
    build_controlled_agent_router_workflow_state_adapter_readonly,
)


PHASE = "33C"
ITEM_ARTIFACT_FIELDS = (
    "job_record",
    "relevance_result",
    "jd_intelligence_result",
    "final_score_result",
    "tailoring_opportunity_result",
    "manual_tailoring_preview_result",
)
GENERATED_TAILORING_MARKERS = (
    "generated_tailoring_text",
    "real_tailoring_output",
    "tailored_resume_text",
    "rewritten resume",
)


def _empty_plan(
    *,
    item_count: int = 0,
    missing_inputs: list[str] | None = None,
    blocked_items: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return _payload(
        item_count=item_count,
        valid_item_count=0,
        invalid_item_count=len(blocked_items or []),
        batch_items=[],
        handoff_plan=[],
        grouped_by_next_allowed_step={},
        routing_summary=[],
        next_step_counts={},
        blocked_items=blocked_items or [],
        missing_inputs=missing_inputs or [],
    )


def _batch_plan_key(
    *,
    item_count: int,
    valid_item_count: int,
    invalid_item_count: int,
    next_step_counts: dict[str, int],
) -> str:
    count_pairs = ",".join(
        f"{step}:{count}" for step, count in next_step_counts.items()
    )
    return "|".join(
        (
            f"phase={PHASE}",
            f"items={item_count}",
            f"valid={valid_item_count}",
            f"invalid={invalid_item_count}",
            f"steps={count_pairs}",
        )
    )


def _payload(
    *,
    item_count: int,
    valid_item_count: int,
    invalid_item_count: int,
    batch_items: list[dict[str, Any]],
    handoff_plan: list[dict[str, Any]],
    grouped_by_next_allowed_step: dict[str, list[dict[str, Any]]],
    routing_summary: list[dict[str, Any]],
    next_step_counts: dict[str, int],
    blocked_items: list[dict[str, Any]],
    missing_inputs: list[str],
) -> dict[str, Any]:
    return {
        "phase": PHASE,
        "default_off": True,
        "read_only": True,
        "advisory_only": True,
        "batch_handoff_plan_only": True,
        "controlled_agent_router_batch_plan": True,
        "allowlisted_routing_only": True,
        "requires_manual_user_control": True,
        "item_count": item_count,
        "valid_item_count": valid_item_count,
        "invalid_item_count": invalid_item_count,
        "batch_items": deepcopy(batch_items),
        "handoff_plan": deepcopy(handoff_plan),
        "grouped_by_next_allowed_step": deepcopy(
            grouped_by_next_allowed_step
        ),
        "routing_summary": deepcopy(routing_summary),
        "next_step_counts": deepcopy(next_step_counts),
        "blocked_items": deepcopy(blocked_items),
        "missing_inputs": list(missing_inputs),
        "batch_plan_key": _batch_plan_key(
            item_count=item_count,
            valid_item_count=valid_item_count,
            invalid_item_count=invalid_item_count,
            next_step_counts=next_step_counts,
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


def _item_id(item: dict[str, Any], index: int) -> str:
    supplied = item.get("item_id")
    return str(supplied) if supplied not in (None, "") else f"item-{index}"


def _adapter_kwargs(
    item: dict[str, Any],
    router_policy: dict[str, Any] | None,
) -> dict[str, Any]:
    kwargs = {field: item.get(field) for field in ITEM_ARTIFACT_FIELDS}
    kwargs["router_policy"] = router_policy
    return kwargs


def _planned_item(
    *,
    item_id: str,
    index: int,
    adapter_result: dict[str, Any],
) -> dict[str, Any]:
    packet = deepcopy(adapter_result["agent_handoff_packet"])
    return {
        "item_id": item_id,
        "input_index": index,
        "next_allowed_step": adapter_result["next_allowed_step"],
        "handoff_reason": adapter_result["handoff_reason"],
        "agent_handoff_packet": packet,
        "required_inputs_for_next_step": deepcopy(
            adapter_result["required_inputs_for_next_step"]
        ),
        "available_inputs_for_next_step": deepcopy(
            adapter_result["available_inputs_for_next_step"]
        ),
        "missing_inputs_for_next_step": deepcopy(
            adapter_result["missing_inputs_for_next_step"]
        ),
        "adapter_key": adapter_result["adapter_key"],
        "non_executable": True,
        "no_executable_callback": True,
        "no_provider_request": True,
        "no_network_request": True,
        "no_mutation_command": True,
        "no_database_write_command": True,
        "no_application_submission_command": True,
    }


def build_controlled_agent_router_batch_handoff_plan_readonly(
    items: list[dict[str, Any]] | None = None,
    router_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a deterministic grouped handoff plan without executing steps."""

    if not isinstance(items, list):
        return _empty_plan(
            item_count=0,
            missing_inputs=["items"],
            blocked_items=[
                {
                    "input_index": None,
                    "item_id": "",
                    "reason": "items must be supplied as a list",
                }
            ],
        )

    if not items:
        return _empty_plan(item_count=0)

    batch_items: list[dict[str, Any]] = []
    handoff_plan: list[dict[str, Any]] = []
    grouped: dict[str, list[dict[str, Any]]] = {}
    routing_summary: list[dict[str, Any]] = []
    next_step_counts: dict[str, int] = {}
    blocked_items: list[dict[str, Any]] = []

    for index, item in enumerate(items):
        if not isinstance(item, dict):
            blocked_items.append(
                {
                    "input_index": index,
                    "item_id": f"item-{index}",
                    "reason": "item must be a dictionary",
                }
            )
            continue

        item_id = _item_id(item, index)
        adapter_result = (
            build_controlled_agent_router_workflow_state_adapter_readonly(
                **_adapter_kwargs(item, router_policy)
            )
        )
        planned = _planned_item(
            item_id=item_id,
            index=index,
            adapter_result=adapter_result,
        )
        next_step = planned["next_allowed_step"]
        batch_items.append(
            {
                "item_id": item_id,
                "input_index": index,
                "valid": True,
                "next_allowed_step": next_step,
                "adapter_key": adapter_result["adapter_key"],
            }
        )
        handoff_plan.append(planned)
        grouped.setdefault(next_step, []).append(deepcopy(planned))
        next_step_counts[next_step] = next_step_counts.get(next_step, 0) + 1
        routing_summary.append(
            {
                "item_id": item_id,
                "input_index": index,
                "next_allowed_step": next_step,
                "handoff_reason": adapter_result["handoff_reason"],
            }
        )

    return _payload(
        item_count=len(items),
        valid_item_count=len(batch_items),
        invalid_item_count=len(blocked_items),
        batch_items=batch_items,
        handoff_plan=handoff_plan,
        grouped_by_next_allowed_step=grouped,
        routing_summary=routing_summary,
        next_step_counts=next_step_counts,
        blocked_items=blocked_items,
        missing_inputs=[],
    )
