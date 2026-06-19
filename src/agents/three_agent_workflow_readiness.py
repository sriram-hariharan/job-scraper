"""Deterministic readiness summary for the three-agent shadow workflow."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


READINESS_VERSION = "phase-9q-three-agent-workflow-readiness-v1"
STATUS_READY = "ready_shadow_provider_workflow"
STATUS_INCOMPLETE = "incomplete_shadow_provider_workflow"
STATUS_SKIPPED = "skipped_default_off"
ORDERED_AGENT_NAMES = (
    "jd_intelligence",
    "tailoring_suggestion",
    "critic_guardrail",
)


def _plain_dict(value: Any) -> dict[str, Any]:
    return deepcopy(value) if isinstance(value, dict) else {}


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _non_negative_int(value: Any) -> int:
    try:
        return max(0, int(float(str(value or "0").strip() or "0")))
    except (TypeError, ValueError):
        return 0


def three_agent_workflow_readiness_safety_metadata() -> dict[str, bool]:
    return {
        "read_only": True,
        "advisory_only": True,
        "shadow_only": True,
        "did_write_database": False,
        "did_mutate_scoring": False,
        "did_change_ranking": False,
        "did_mutate_queue": False,
        "did_create_approval": False,
        "did_mutate_approval": False,
        "did_mutate_resume": False,
        "did_create_execution_request": False,
        "did_create_execution_launch_request": False,
        "did_execute_application": False,
        "did_submit_application": False,
        "api_route_added": False,
        "ui_action_added": False,
        "pipeline_stage_added": False,
        "mutation_authorized": False,
    }


def attach_three_agent_workflow_readiness(
    *,
    chain_payload: dict[str, Any] | None,
    enabled: bool = False,
) -> dict[str, Any]:
    """Attach readiness derived only from existing chain metadata."""

    chain = _plain_dict(chain_payload)
    if enabled is not True:
        return chain

    results = chain.get("ordered_agent_results")
    results = results if isinstance(results, list) else []
    ordered_agent_names = [
        _clean_text(_plain_dict(result).get("agent_name"))
        for result in results
    ]
    trace_contract = _plain_dict(
        chain.get("three_agent_llmops_trace_contract")
    )
    handoff = _plain_dict(chain.get("three_agent_provider_handoff"))
    aggregate = _plain_dict(chain.get("three_agent_llmops_aggregate"))
    workflow = _plain_dict(chain.get("three_agent_shadow_workflow"))
    provider_backed_agent_names = [
        _clean_text(name)
        for name in trace_contract.get("provider_backed_agent_names", [])
        if _clean_text(name)
    ]
    provider_backed_agent_count = _non_negative_int(
        trace_contract.get("provider_backed_agent_count")
    )
    llmops_trace_available = bool(
        trace_contract
        and len(trace_contract.get("agent_traces", []) or [])
        == len(ORDERED_AGENT_NAMES)
        and all(
            _plain_dict(result).get("llmops_trace_metadata")
            for result in results
        )
    )
    structured_handoff_available = bool(
        handoff.get("provider_handoff_enabled") is True
        and handoff.get("handoff_payload_schema_version")
    )
    llmops_aggregate_available = bool(
        aggregate.get("llmops_aggregate_recorded") is True
        and aggregate.get("agent_count") == len(ORDERED_AGENT_NAMES)
    )
    quality_gate_status = _clean_text(
        workflow.get("semantic_evidence_quality_gate_status")
    )
    semantic_evidence_quality_gate_available = bool(
        quality_gate_status
        and quality_gate_status
        != "semantic_evidence_quality_gate_not_enabled"
    )
    mutation_authorized_agent_count = _non_negative_int(
        chain.get("mutation_authorized_agents")
    )
    ordered_agents_complete = (
        tuple(ordered_agent_names) == ORDERED_AGENT_NAMES
    )
    provider_agents_complete = (
        provider_backed_agent_count == len(ORDERED_AGENT_NAMES)
        and tuple(provider_backed_agent_names) == ORDERED_AGENT_NAMES
    )
    ready = all(
        (
            ordered_agents_complete,
            provider_agents_complete,
            structured_handoff_available,
            llmops_trace_available,
            llmops_aggregate_available,
            mutation_authorized_agent_count == 0,
        )
    )
    summary = {
        "readiness_version": READINESS_VERSION,
        "three_agent_workflow_readiness_enabled": True,
        "readiness_status": STATUS_READY if ready else STATUS_INCOMPLETE,
        "ordered_agent_count": len(ordered_agent_names),
        "ordered_agent_names": ordered_agent_names,
        "provider_backed_agent_count": provider_backed_agent_count,
        "provider_backed_agent_names": provider_backed_agent_names,
        "structured_handoff_available": structured_handoff_available,
        "llmops_trace_available": llmops_trace_available,
        "llmops_aggregate_available": llmops_aggregate_available,
        "semantic_evidence_quality_gate_available": (
            semantic_evidence_quality_gate_available
        ),
        "mutation_authorized_agent_count": (
            mutation_authorized_agent_count
        ),
        "final_scoring_mutation_enabled": False,
        "ranking_mutation_enabled": False,
        "queue_mutation_enabled": False,
        "approval_mutation_enabled": False,
        "resume_mutation_enabled": False,
        "execution_enabled": False,
        "submission_enabled": False,
        "safety_metadata": (
            three_agent_workflow_readiness_safety_metadata()
        ),
    }
    chain["three_agent_workflow_readiness"] = summary
    return chain
