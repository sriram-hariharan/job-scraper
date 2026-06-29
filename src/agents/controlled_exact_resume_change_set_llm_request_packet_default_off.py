"""Default-off controlled LLM request packet for exact resume change sets."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


PHASE = "43A"
CHANGE_TYPES = ("summary", "skill", "bullet", "project", "evidence_note")
FALSE_ACTION_KEYS = (
    "llm_call_performed",
    "provider_call_performed",
    "network_call_performed",
    "tailoring_runtime_call_performed",
    "ai_tailoring_generation_performed",
    "real_tailoring_output_created",
    "resume_change_proposals_created",
    "resume_rewrite_performed",
    "resume_overwrite_performed",
    "resume_mutation_performed",
    "final_score_produced",
    "existing_score_changed",
    "matching_scoring_module_called",
    "database_write_performed",
    "persistence_performed",
    "execution_performed",
    "application_submission_performed",
    "submission_performed",
    "auto_apply_performed",
    "auto_submit_performed",
)


def _string(value: Any) -> str:
    return str(value or "").strip()


def _bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"1", "true", "yes", "y"}:
            return True
        if text in {"0", "false", "no", "n"}:
            return False
    return default if value is None else bool(value)


def _int_at_least(value: Any, default: int, minimum: int) -> int:
    if isinstance(value, bool):
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed >= minimum else default


def _number(value: Any, default: int | float) -> int | float:
    if isinstance(value, bool):
        return default
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    if parsed.is_integer():
        return int(parsed)
    return parsed


def _policy(value: dict[str, Any] | None) -> dict[str, Any]:
    supplied = value if isinstance(value, dict) else {}
    response_format = _string(supplied.get("response_format")) or "json"
    return {
        "max_proposals_per_request": _int_at_least(
            supplied.get("max_proposals_per_request"),
            8,
            0,
        ),
        "include_full_resume_context": _bool(
            supplied.get("include_full_resume_context"),
            False,
        ),
        "include_full_jd_context": _bool(supplied.get("include_full_jd_context"), False),
        "include_tailoring_context": _bool(
            supplied.get("include_tailoring_context"),
            True,
        ),
        "require_manual_trigger": _bool(supplied.get("require_manual_trigger"), True),
        "response_format": response_format,
        "temperature": _number(supplied.get("temperature"), 0),
        "max_output_tokens": _int_at_least(
            supplied.get("max_output_tokens"),
            1800,
            1,
        ),
    }


def _flatten_grouped(value: Any) -> list[Any]:
    if not isinstance(value, dict):
        return []
    rows: list[Any] = []
    for key in CHANGE_TYPES:
        grouped = value.get(key)
        if isinstance(grouped, list):
            rows.extend(grouped)
    for key in sorted(str(key) for key in value.keys()):
        if key in CHANGE_TYPES:
            continue
        grouped = value.get(key)
        if isinstance(grouped, list):
            rows.extend(grouped)
    return rows


def _rows_from_result(proposal_result: dict[str, Any] | None) -> tuple[list[Any], str]:
    if not isinstance(proposal_result, dict):
        return [], "missing"
    if isinstance(proposal_result.get("change_proposals"), list):
        return list(proposal_result["change_proposals"]), "proposal_result.change_proposals"
    nested = proposal_result.get("proposal_result")
    if isinstance(nested, dict) and isinstance(nested.get("change_proposals"), list):
        return (
            list(nested["change_proposals"]),
            "proposal_result.proposal_result.change_proposals",
        )
    grouped = _flatten_grouped(proposal_result.get("change_proposals_by_type"))
    if grouped:
        return grouped, "proposal_result.change_proposals_by_type"
    if isinstance(nested, dict):
        grouped = _flatten_grouped(nested.get("change_proposals_by_type"))
        if grouped:
            return (
                grouped,
                "proposal_result.proposal_result.change_proposals_by_type",
            )
    return [], "missing"


def _resolve_proposals(
    change_proposals: list[Any] | None,
    proposal_result: dict[str, Any] | None,
) -> tuple[list[Any], str, list[str]]:
    if isinstance(change_proposals, list):
        return list(change_proposals), "change_proposals", []
    rows, source = _rows_from_result(proposal_result)
    if rows:
        return rows, source, []
    return [], source, ["change_proposals"]


def _compact_context(value: dict[str, Any] | None, *, include_full: bool) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    if include_full:
        return deepcopy(value)
    compact: dict[str, Any] = {}
    for key in sorted(value.keys()):
        if key in {
            "profile_summary",
            "skills",
            "required_skills",
            "preferred_skills",
            "tools",
            "responsibilities",
            "missing_required_skills",
            "missing_tools",
            "matched_required_skills",
            "matched_tools",
            "suggested_focus",
        }:
            compact[key] = deepcopy(value.get(key))
    return compact


def _schema() -> dict[str, Any]:
    proposal_shape = {
        "type": "object",
        "required": [
            "proposal_id",
            "change_type",
            "target_section",
            "target_identifier",
            "current_text",
            "proposed_text",
            "change_reason",
            "jd_terms_supported",
            "resume_evidence_used",
            "risk_flags",
            "manual_review_required",
            "requires_user_acceptance",
        ],
        "properties": {
            "proposal_id": {"type": "string"},
            "change_type": {"type": "string"},
            "target_section": {"type": "string"},
            "target_identifier": {"type": "string"},
            "current_text": {"type": "string"},
            "proposed_text": {"type": "string"},
            "change_reason": {"type": "string"},
            "jd_terms_supported": {"type": "array", "items": {"type": "string"}},
            "resume_evidence_used": {"type": "array", "items": {"type": "string"}},
            "risk_flags": {"type": "array", "items": {"type": "string"}},
            "manual_review_required": {"type": "boolean"},
            "requires_user_acceptance": {"type": "boolean"},
        },
    }
    return {
        "type": "object",
        "required": [
            "refined_change_proposals",
            "resume_overwrite_performed",
            "resume_mutation_performed",
            "application_submission_performed",
        ],
        "properties": {
            "refined_change_proposals": {
                "type": "array",
                "items": proposal_shape,
            },
            "resume_overwrite_performed": {"const": False},
            "resume_mutation_performed": {"const": False},
            "application_submission_performed": {"const": False},
        },
    }


def _constraints() -> tuple[list[str], list[str], list[str]]:
    safety = [
        "Refine exact resume change proposals only.",
        "Do not generate a full resume.",
        "Do not overwrite resumes.",
        "Do not mutate resumes.",
        "Do not execute applications.",
        "Do not submit applications.",
        "No auto-apply.",
        "No auto-submit.",
        "Manual user acceptance is required.",
    ]
    evidence = [
        "Use only supplied proposals and context.",
        "Do not add unsupported claims.",
        "Do not invent employers, metrics, tools, or experience.",
        "Keep missing evidence explicit.",
    ]
    output = [
        "Return JSON only.",
        "Return refined_change_proposals with the requested fields.",
        "Keep all safety flags false.",
    ]
    return safety, evidence, output


def _messages(
    *,
    included: list[dict[str, Any]],
    resume_context: dict[str, Any] | None,
    jd_context: dict[str, Any] | None,
    tailoring_context: dict[str, Any] | None,
    policy: dict[str, Any],
    safety_constraints: list[str],
    evidence_constraints: list[str],
    output_constraints: list[str],
) -> list[dict[str, Any]]:
    context_payload = {
        "change_proposals": deepcopy(included),
        "resume_context": _compact_context(
            resume_context,
            include_full=policy["include_full_resume_context"],
        ),
        "jd_context": _compact_context(
            jd_context,
            include_full=policy["include_full_jd_context"],
        ),
        "tailoring_context": (
            deepcopy(tailoring_context)
            if policy["include_tailoring_context"] and isinstance(tailoring_context, dict)
            else {}
        ),
        "safety_constraints": list(safety_constraints),
        "evidence_constraints": list(evidence_constraints),
        "output_constraints": list(output_constraints),
    }
    return [
        {
            "role": "system",
            "content": (
                "You must refine exact resume change proposals only. "
                "Do not generate a full resume, invent unsupported claims, overwrite or mutate resumes, "
                "execute or submit applications, auto-apply, or auto-submit."
            ),
        },
        {
            "role": "user",
            "content": deepcopy(context_payload),
        },
    ]


def _request_key(
    *,
    total_count: int,
    valid_count: int,
    invalid_count: int,
    included_count: int,
    excluded_count: int,
) -> str:
    return "|".join(
        (
            f"phase={PHASE}",
            f"proposals={total_count}",
            f"valid={valid_count}",
            f"invalid={invalid_count}",
            f"included={included_count}",
            f"excluded={excluded_count}",
        )
    )


def build_controlled_exact_resume_change_set_llm_request_packet_default_off(
    change_proposals: list[Any] | None = None,
    proposal_result: dict[str, Any] | None = None,
    resume_context: dict[str, Any] | None = None,
    jd_context: dict[str, Any] | None = None,
    tailoring_context: dict[str, Any] | None = None,
    request_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a provider-ready exact-change request packet without dispatch."""

    policy = _policy(request_policy)
    rows, source, missing_inputs = _resolve_proposals(change_proposals, proposal_result)
    invalid_rows: list[dict[str, Any]] = []
    valid_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            invalid_rows.append(
                {
                    "input_index": index,
                    "reason": "change proposal must be a dictionary",
                }
            )
            continue
        valid_rows.append(deepcopy(row))
    if not rows and "change_proposals" not in missing_inputs:
        missing_inputs.append("change_proposals")
    max_items = policy["max_proposals_per_request"]
    included = valid_rows[:max_items]
    excluded = valid_rows[max_items:]
    safety_constraints, evidence_constraints, output_constraints = _constraints()
    request_schema = _schema()
    request_messages = _messages(
        included=included,
        resume_context=resume_context,
        jd_context=jd_context,
        tailoring_context=tailoring_context,
        policy=policy,
        safety_constraints=safety_constraints,
        evidence_constraints=evidence_constraints,
        output_constraints=output_constraints,
    )
    request_packet = {
        "request_type": "exact_resume_change_set_refinement",
        "manual_trigger_required": True,
        "response_format": policy["response_format"],
        "temperature": policy["temperature"],
        "max_output_tokens": policy["max_output_tokens"],
        "request_messages": deepcopy(request_messages),
        "request_schema": deepcopy(request_schema),
        "included_change_proposals": deepcopy(included),
        "excluded_change_proposals": deepcopy(excluded),
        "safety_constraints": list(safety_constraints),
        "evidence_constraints": list(evidence_constraints),
        "output_constraints": list(output_constraints),
        "provider_call_performed": False,
        "network_call_performed": False,
    }
    summary = {
        "request_blocked": not bool(included),
        "included_change_proposal_count": len(included),
        "excluded_change_proposal_count": len(excluded),
        "invalid_change_proposal_count": len(invalid_rows),
        "provider_dispatch_ready": bool(included),
        "provider_call_performed": False,
        "network_call_performed": False,
    }
    findings = {
        "change_proposals_source": source,
        "invalid_change_proposals": deepcopy(invalid_rows),
        "excluded_change_proposals": deepcopy(excluded),
        "copied_inputs_only": True,
        "llm_request_packet_created": True,
        "provider_dispatch_prepared_not_executed": True,
        "executable_callbacks_included": False,
        "function_pointers_included": False,
        "network_payloads_included": False,
        "mutation_commands_included": False,
        "db_write_commands_included": False,
        "application_submission_commands_included": False,
    }
    payload = {
        "phase": PHASE,
        "default_off": True,
        "controlled_exact_resume_change_set_llm_request_packet": True,
        "read_only": True,
        "advisory_only": True,
        "proposal_only": True,
        "llm_request_packet_only": True,
        "provider_request_packet_only": True,
        "exact_worthy_changes_only": True,
        "manual_review_required": True,
        "requires_manual_user_control": True,
        "manual_trigger_required": True,
        "change_proposals_present": bool(rows),
        "change_proposal_count": len(rows),
        "valid_change_proposal_count": len(valid_rows),
        "invalid_change_proposal_count": len(invalid_rows),
        "resume_context_present": isinstance(resume_context, dict),
        "jd_context_present": isinstance(jd_context, dict),
        "tailoring_context_present": isinstance(tailoring_context, dict),
        "request_policy": deepcopy(policy),
        "request_packet": request_packet,
        "request_messages": deepcopy(request_messages),
        "request_schema": deepcopy(request_schema),
        "request_packet_summary": summary,
        "request_findings": findings,
        "missing_inputs": list(missing_inputs),
        "request_key": _request_key(
            total_count=len(rows),
            valid_count=len(valid_rows),
            invalid_count=len(invalid_rows),
            included_count=len(included),
            excluded_count=len(excluded),
        ),
        "llm_request_packet_created": True,
        "provider_dispatch_ready": True,
    }
    for key in FALSE_ACTION_KEYS:
        payload[key] = False
    return payload
