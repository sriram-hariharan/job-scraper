"""Pure default-off contract for caller-supplied tailoring opportunities."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


CONTRACT_VERSION = "phase-23a-tailoring-agent-opportunity-contract-v1"
STATUS_SKIPPED = "tailoring_agent_opportunity_contract_skipped_default_off"
STATUS_MISSING_EVIDENCE = (
    "tailoring_agent_opportunity_contract_enabled_missing_evidence"
)
STATUS_READY = "tailoring_agent_opportunity_contract_ready_for_manual_review"
FUTURE_USER_TRIGGERED_ACTION = "Generate AI Tailoring"


def _plain_dict(value: Any) -> dict[str, Any]:
    return deepcopy(value) if isinstance(value, dict) else {}


def _plain_list(value: Any) -> list[Any]:
    return deepcopy(value) if isinstance(value, list) else []


def _unique_signals(values: list[Any]) -> list[Any]:
    unique: list[Any] = []
    seen: set[str] = set()
    for value in values:
        if value in (None, "", [], {}):
            continue
        marker = repr(value)
        if marker in seen:
            continue
        seen.add(marker)
        unique.append(deepcopy(value))
    return unique


def _packet_gap_signals(packet: dict[str, Any]) -> list[Any]:
    review_packet = packet.get("manual_review_evidence_packet")
    review_packet = review_packet if isinstance(review_packet, dict) else {}
    values: list[Any] = []
    for source in (packet, review_packet):
        gaps = source.get("missing_evidence_fields")
        if isinstance(gaps, list):
            values.extend(gaps)
    return _unique_signals(values)


def _tailoring_context_signals(context: dict[str, Any]) -> list[Any]:
    values: list[Any] = []
    for field_name in (
        "tailoring_opportunities",
        "opportunities",
        "tailoring_actions",
        "focus_areas",
        "tailoring_opportunity_summary",
        "summary",
    ):
        value = context.get(field_name)
        if isinstance(value, list):
            values.extend(value)
        elif value not in (None, "", {}):
            values.append(value)
    return _unique_signals(values)


def _opportunity(
    *,
    opportunity_type: str,
    source: str,
    signal: Any,
    suggested_next_step: str,
) -> dict[str, Any]:
    return {
        "opportunity_type": opportunity_type,
        "source": source,
        "signal": deepcopy(signal),
        "manual_review_required": True,
        "generate_ai_tailoring_allowed_now": False,
        "suggested_next_step": suggested_next_step,
    }


def tailoring_agent_opportunity_safety_metadata() -> dict[str, bool]:
    return {
        "read_only": True,
        "advisory_only": True,
        "manual_review_only": True,
        "manual_user_control_required": True,
        "tailoring_agent_separate_from_final_scoring": True,
        "provider_call_attempted": False,
        "network_call_attempted": False,
        "file_read_attempted": False,
        "file_write_attempted": False,
        "environment_read_attempted": False,
        "database_read_attempted": False,
        "database_write_attempted": False,
        "persistence_attempted": False,
        "runtime_scoring_called": False,
        "runtime_prefilter_called": False,
        "runtime_matching_called": False,
        "runtime_tailoring_called": False,
        "llm_runtime_called": False,
        "ai_tailoring_generation_performed": False,
        "ranking_mutated": False,
        "queue_mutated": False,
        "resume_mutated": False,
        "application_mutated": False,
        "approval_mutated": False,
        "decision_mutated": False,
        "audit_mutated": False,
        "execution_authorized": False,
        "submission_authorized": False,
        "mutation_authorized": False,
    }


def build_tailoring_agent_opportunity_contract(
    *,
    enabled: bool = False,
    core_agent_evidence_packet: dict[str, Any] | None = None,
    job_evidence: dict[str, Any] | None = None,
    resume_evidence: dict[str, Any] | None = None,
    missing_requirements: list[Any] | None = None,
    matched_terms: list[Any] | None = None,
    tailoring_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Identify review-only opportunities from caller-supplied evidence."""

    safe_packet = _plain_dict(core_agent_evidence_packet)
    safe_job = _plain_dict(job_evidence)
    safe_resume = _plain_dict(resume_evidence)
    safe_missing = _plain_list(missing_requirements)
    safe_matched = _plain_list(matched_terms)
    safe_context = _plain_dict(tailoring_context)

    opportunity_inputs = {
        "core_agent_evidence_packet": deepcopy(safe_packet),
        "job_evidence": deepcopy(safe_job),
        "resume_evidence": deepcopy(safe_resume),
        "missing_requirements": deepcopy(safe_missing),
        "matched_terms": deepcopy(safe_matched),
        "tailoring_context": deepcopy(safe_context),
    }

    opportunities: list[dict[str, Any]] = []
    if enabled is True:
        for signal in _unique_signals(safe_missing):
            opportunities.append(
                _opportunity(
                    opportunity_type="missing_requirement",
                    source="missing_requirements",
                    signal=signal,
                    suggested_next_step=(
                        "review_existing_resume_evidence_for_supported_alignment"
                    ),
                )
            )
        for signal in _packet_gap_signals(safe_packet):
            opportunities.append(
                _opportunity(
                    opportunity_type="evidence_packet_gap",
                    source="core_agent_evidence_packet",
                    signal=signal,
                    suggested_next_step=(
                        "review_missing_evidence_before_tailoring"
                    ),
                )
            )
        for signal in _tailoring_context_signals(safe_context):
            opportunities.append(
                _opportunity(
                    opportunity_type="caller_supplied_tailoring_context",
                    source="tailoring_context",
                    signal=signal,
                    suggested_next_step=(
                        "review_tailoring_opportunity_under_manual_control"
                    ),
                )
            )

    supplied_input_fields = [
        field_name
        for field_name, value in opportunity_inputs.items()
        if value not in ({}, [])
    ]
    if enabled is not True:
        status = STATUS_SKIPPED
        summary = "Tailoring opportunity detection is skipped by default."
        next_safe_step = "enable_contract_with_caller_supplied_evidence"
    elif not supplied_input_fields:
        status = STATUS_MISSING_EVIDENCE
        summary = (
            "No caller-supplied evidence was available; no tailoring "
            "opportunities were identified."
        )
        next_safe_step = "supply_evidence_for_tailoring_opportunity_review"
    else:
        status = STATUS_READY
        summary = (
            f"Identified {len(opportunities)} caller-supplied tailoring "
            "opportunities for manual review."
        )
        next_safe_step = (
            "review_tailoring_opportunities_without_generating_ai_tailoring"
        )

    return {
        "contract_version": CONTRACT_VERSION,
        "contract_status": status,
        "tailoring_agent_opportunity_contract_enabled": enabled is True,
        "default_off": True,
        "read_only": True,
        "advisory_only": True,
        "manual_review_only": True,
        "manual_user_control_required": True,
        "tailoring_agent_separate_from_final_scoring": True,
        "generate_ai_tailoring_user_trigger_required": True,
        "ai_tailoring_generation_performed": False,
        "no_auto_apply": True,
        "no_auto_submit": True,
        "no_autonomous_application_execution": True,
        "no_automatic_job_application_submission": True,
        "no_provider_calls": True,
        "no_network_calls": True,
        "no_database_writes": True,
        "no_persistence": True,
        "no_mutation": True,
        "no_resume_mutation": True,
        "no_application_mutation": True,
        "no_execution": True,
        "no_submission": True,
        "opportunity_inputs": opportunity_inputs,
        "supplied_input_fields": supplied_input_fields,
        "tailoring_opportunity_summary": summary,
        "tailoring_opportunities": opportunities,
        "future_user_triggered_action": FUTURE_USER_TRIGGERED_ACTION,
        "next_safe_step": next_safe_step,
        "safety_metadata": tailoring_agent_opportunity_safety_metadata(),
    }
