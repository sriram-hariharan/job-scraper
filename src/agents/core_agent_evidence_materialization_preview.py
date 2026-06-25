"""Pure, default-off materialization of caller-supplied review evidence."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


PREVIEW_VERSION = (
    "phase-22c-core-agent-evidence-materialization-preview-v1"
)
STATUS_SKIPPED = "core_agent_evidence_preview_skipped_default_off"
STATUS_MISSING_EVIDENCE = "core_agent_evidence_preview_missing_evidence"
STATUS_PARTIAL = "core_agent_evidence_preview_partial_manual_review"
STATUS_READY = "core_agent_evidence_preview_ready_for_manual_review"

CORE_AGENT_SEQUENCE = (
    "relevance_prefilter",
    "jd_intelligence",
    "final_application_scoring",
)

AGENT_BOUNDARIES = {
    "relevance_prefilter": (
        "relevance prefilter owns early relevance gating"
    ),
    "jd_intelligence": (
        "JD intelligence owns JD signal extraction and interpretation"
    ),
    "final_application_scoring": (
        "final application scoring owns final advisory score synthesis"
    ),
    "tailoring_agent": (
        "tailoring agent remains separate from final scoring"
    ),
}

EVIDENCE_FIELD_NAMES = (
    "relevance_prefilter_result",
    "jd_intelligence_signals",
    "final_application_scoring_result",
    "tailoring_opportunity_signals",
    "manual_review_context",
)


def _plain_dict(value: Any) -> dict[str, Any]:
    return deepcopy(value) if isinstance(value, dict) else {}


def _first_summary(
    payload: dict[str, Any],
    field_names: tuple[str, ...],
) -> Any:
    for field_name in field_names:
        value = payload.get(field_name)
        if value not in (None, "", [], {}):
            return deepcopy(value)
    return ""


def _review_rationale(
    manual_review_context: dict[str, Any],
    final_scoring: dict[str, Any],
    relevance: dict[str, Any],
    jd_intelligence: dict[str, Any],
) -> Any:
    fields = (
        "why_job_is_worth_reviewing",
        "review_rationale",
        "action_rationale",
        "queue_priority_reason",
        "rationale",
        "reason",
        "reasons",
    )
    for payload in (
        manual_review_context,
        final_scoring,
        relevance,
        jd_intelligence,
    ):
        summary = _first_summary(payload, fields)
        if summary not in (None, "", [], {}):
            return summary
    return ""


def core_agent_evidence_materialization_safety_metadata(
) -> dict[str, bool]:
    return {
        "read_only": True,
        "advisory_only": True,
        "manual_review_only": True,
        "manual_user_control_required": True,
        "caller_supplied_dictionaries_only": True,
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
        "runtime_tailoring_called": False,
        "scoring_mutated": False,
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


def build_core_agent_evidence_materialization_preview(
    *,
    enabled: bool = False,
    relevance_prefilter_result: dict[str, Any] | None = None,
    jd_intelligence_signals: dict[str, Any] | None = None,
    final_application_scoring_result: dict[str, Any] | None = None,
    tailoring_opportunity_signals: dict[str, Any] | None = None,
    manual_review_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Materialize caller-supplied dictionaries for manual review only."""

    relevance = _plain_dict(relevance_prefilter_result)
    jd_intelligence = _plain_dict(jd_intelligence_signals)
    final_scoring = _plain_dict(final_application_scoring_result)
    tailoring = _plain_dict(tailoring_opportunity_signals)
    review_context = _plain_dict(manual_review_context)

    supplied = {
        "relevance_evidence_supplied": bool(relevance),
        "jd_intelligence_evidence_supplied": bool(jd_intelligence),
        "final_scoring_evidence_supplied": bool(final_scoring),
        "tailoring_opportunity_evidence_supplied": bool(tailoring),
        "manual_review_context_supplied": bool(review_context),
    }
    missing_evidence_fields = [
        field_name
        for field_name, present in zip(
            EVIDENCE_FIELD_NAMES,
            supplied.values(),
        )
        if not present
    ]

    if enabled is not True:
        preview_status = STATUS_SKIPPED
        suggested_manual_review_status = "skipped_default_off"
        next_safe_step = "enable_preview_with_caller_supplied_evidence"
    elif not any(supplied.values()):
        preview_status = STATUS_MISSING_EVIDENCE
        suggested_manual_review_status = "missing_evidence"
        next_safe_step = "supply_deterministic_evidence_for_manual_review"
    elif missing_evidence_fields:
        preview_status = STATUS_PARTIAL
        suggested_manual_review_status = "partial_evidence_manual_review"
        next_safe_step = "review_supplied_evidence_and_missing_fields"
    else:
        preview_status = STATUS_READY
        suggested_manual_review_status = "ready_for_manual_review"
        next_safe_step = "complete_manual_review_under_user_control"

    tailoring_summary = _first_summary(
        tailoring,
        (
            "tailoring_opportunity_summary",
            "summary",
            "tailoring_actions",
            "opportunities",
            "missing_requirements",
        ),
    )
    rationale = _review_rationale(
        review_context,
        final_scoring,
        relevance,
        jd_intelligence,
    )

    manual_review_packet = {
        **supplied,
        "suggested_manual_review_status": suggested_manual_review_status,
        "why_job_is_worth_reviewing": rationale,
        "missing_evidence_fields": list(missing_evidence_fields),
        "tailoring_opportunity_summary": tailoring_summary,
        "future_user_triggered_action": "Generate AI Tailoring",
        "ai_tailoring_generation_performed": False,
        "tailoring_suggestions_boundary": (
            "Generated tailoring suggestions are preview/manual-review only "
            "unless the user accepts edits."
        ),
        "manual_review_context": deepcopy(review_context),
    }

    return {
        "preview_version": PREVIEW_VERSION,
        "preview_status": preview_status,
        "core_agent_evidence_materialization_enabled": enabled is True,
        "default_off": True,
        "read_only": True,
        "advisory_only": True,
        "manual_review_only": True,
        "manual_user_control_required": True,
        "no_auto_apply": True,
        "no_auto_submit": True,
        "no_autonomous_application_execution": True,
        "no_automatic_job_application_submission": True,
        "no_provider_calls": True,
        "no_network_calls": True,
        "no_database_writes": True,
        "no_persistence": True,
        "no_mutation": True,
        "no_execution": True,
        "no_submission": True,
        "core_agent_sequence": list(CORE_AGENT_SEQUENCE),
        "agent_boundaries": deepcopy(AGENT_BOUNDARIES),
        "relevance_prefilter_evidence": deepcopy(relevance),
        "jd_intelligence_evidence": deepcopy(jd_intelligence),
        "final_application_scoring_evidence": deepcopy(final_scoring),
        "tailoring_opportunity_evidence": deepcopy(tailoring),
        "manual_review_evidence_packet": manual_review_packet,
        "next_safe_step": next_safe_step,
        "safety_metadata": (
            core_agent_evidence_materialization_safety_metadata()
        ),
    }
