from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from typing import Any, Dict, List


ARTIFACT_VERSION = "agent-evidence-chain-bundle-v1"
GATE_NAME = "APPLYLENS_AGENTIC_EVIDENCE_CHAIN_COMPOSITION_ENABLED"
TRACE_PAYLOAD_VERSION = "agent-evidence-chain-trace-payload-v1"
TRACE_PAYLOAD_GATE_NAME = "APPLYLENS_AGENTIC_EVIDENCE_CHAIN_TRACE_PAYLOAD_ENABLED"
TRACE_PAYLOAD_SAMPLE_LIMIT = 6
TRACE_PAYLOAD_MAX_SAMPLE_LIMIT = 6
TRACE_PAYLOAD_REDACTION_POLICY = "compact_agent_summaries_only_no_full_nested_artifacts"
TRACE_PERSISTENCE_VERSION = "agent-evidence-chain-trace-persistence-v1"
TRACE_PERSISTENCE_GATE_NAME = (
    "APPLYLENS_AGENTIC_EVIDENCE_CHAIN_TRACE_PERSISTENCE_ENABLED"
)
ORDERED_AGENT_KEYS = [
    "jd_intelligence",
    "resume_match",
    "critic",
    "job_prioritization",
    "tailoring_decision",
    "operator_review",
]
EXPECTED_ARTIFACT_TYPES = {
    "jd_intelligence": "",
    "resume_match": "resume_match_jd_evidence",
    "critic": "critic_resume_match_jd_evidence",
    "job_prioritization": "job_prioritization_critic_evidence",
    "tailoring_decision": "tailoring_decision_priority_evidence",
    "operator_review": "operator_review_tailoring_evidence",
}
REQUIRED_AGENT_KEYS = {"tailoring_decision", "operator_review"}
FALSE_SAFETY_FLAGS = (
    "provider_call_performed",
    "live_llm_call_performed",
    "jd_extraction_performed",
    "jd_wrapper_execution_performed",
    "resume_match_execution_performed",
    "critic_execution_performed",
    "job_prioritization_execution_performed",
    "tailoring_decision_execution_performed",
    "operator_review_execution_performed",
    "trace_persistence_performed",
    "collector_output_changed",
    "production_output_changed",
    "scoring_changed",
    "ranking_changed",
    "filtering_changed",
    "review_queue_mutation_performed",
    "queue_mutation_performed",
    "scheduler_mutation_performed",
    "tailoring_mutation_performed",
    "source_resume_mutation_performed",
    "generated_resume_mutation_performed",
    "tailoring_provider_call_performed",
    "workflow_runner_executed",
    "application_status_changed",
    "auto_apply_performed",
    "ats_submission_performed",
    "apply_click_performed",
    "recruiter_message_sent",
    "mark_applied_performed",
)
TRACE_PAYLOAD_FALSE_SAFETY_FLAGS = (
    "provider_call_performed",
    "live_llm_call_performed",
    "evidence_chain_bundle_execution_performed",
    "jd_extraction_performed",
    "jd_wrapper_execution_performed",
    "resume_match_execution_performed",
    "critic_execution_performed",
    "job_prioritization_execution_performed",
    "tailoring_decision_execution_performed",
    "operator_review_execution_performed",
    "trace_persistence_requested",
    "trace_persistence_performed",
    "trace_store_write_performed",
    "collector_output_changed",
    "production_output_changed",
    "scoring_changed",
    "ranking_changed",
    "filtering_changed",
    "review_queue_mutation_performed",
    "queue_mutation_performed",
    "scheduler_mutation_performed",
    "tailoring_mutation_performed",
    "source_resume_mutation_performed",
    "generated_resume_mutation_performed",
    "tailoring_provider_call_performed",
    "workflow_runner_executed",
    "application_status_changed",
    "auto_apply_performed",
    "ats_submission_performed",
    "apply_click_performed",
    "recruiter_message_sent",
    "mark_applied_performed",
)
TRACE_PERSISTENCE_SAFETY_FLAGS = (
    "provider_call_performed",
    "live_llm_call_performed",
    "evidence_chain_bundle_execution_performed",
    "evidence_chain_trace_payload_execution_performed",
    "jd_extraction_performed",
    "jd_wrapper_execution_performed",
    "resume_match_execution_performed",
    "critic_execution_performed",
    "job_prioritization_execution_performed",
    "tailoring_decision_execution_performed",
    "operator_review_execution_performed",
    "trace_persistence_requested",
    "trace_persistence_performed",
    "trace_store_write_performed",
    "collector_output_changed",
    "production_output_changed",
    "scoring_changed",
    "ranking_changed",
    "filtering_changed",
    "review_queue_mutation_performed",
    "queue_mutation_performed",
    "scheduler_mutation_performed",
    "tailoring_mutation_performed",
    "source_resume_mutation_performed",
    "generated_resume_mutation_performed",
    "tailoring_provider_call_performed",
    "workflow_runner_executed",
    "application_status_changed",
    "auto_apply_performed",
    "ats_submission_performed",
    "apply_click_performed",
    "recruiter_message_sent",
    "mark_applied_performed",
)
RISK_SAFETY_FLAGS = set(FALSE_SAFETY_FLAGS) | {
    "did_call_llm",
    "did_call_live_provider",
    "did_write_database",
    "did_change_pipeline",
    "did_change_scoring",
    "did_change_ranking",
    "did_change_filtering",
    "did_change_queue",
    "did_change_tailoring",
    "did_mutate_source_resume",
    "did_click_apply",
    "did_execute_application",
    "did_submit_application",
    "did_send_recruiter_message",
    "did_mark_applied",
}


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _plain_dict(value: Any) -> Dict[str, Any]:
    return deepcopy(value) if isinstance(value, dict) else {}


def _plain_list(value: Any) -> List[Any]:
    return deepcopy(value) if isinstance(value, list) else []


def _phase94b_safety_metadata() -> Dict[str, bool]:
    return {flag: False for flag in FALSE_SAFETY_FLAGS}


def _phase95b_safety_metadata() -> Dict[str, bool]:
    return {flag: False for flag in TRACE_PAYLOAD_FALSE_SAFETY_FLAGS}


def _phase96b_safety_metadata(
    *,
    persistence_requested: bool = False,
    persistence_performed: bool = False,
) -> Dict[str, bool]:
    safety = {flag: False for flag in TRACE_PERSISTENCE_SAFETY_FLAGS}
    safety["trace_persistence_requested"] = bool(persistence_requested)
    safety["trace_persistence_performed"] = bool(persistence_performed)
    safety["trace_store_write_performed"] = bool(persistence_performed)
    return safety


def _reason_codes(value: Any) -> List[str]:
    return [
        _clean_text(code)
        for code in _plain_list(value)
        if _clean_text(code)
    ]


def _validation_status(artifact: Dict[str, Any]) -> str:
    validation = _plain_dict(artifact.get("validation_summary"))
    if not validation:
        validation = _plain_dict(artifact.get("validation_json"))
    status = _clean_text(validation.get("validation_status")).lower()
    if status:
        return status
    if validation.get("is_valid_for_existing_output_wrapper") is False:
        return "degraded"
    return ""


def _artifact_validity(
    *,
    agent_key: str,
    raw_artifact: Any,
) -> Dict[str, Any]:
    expected_type = EXPECTED_ARTIFACT_TYPES[agent_key]
    present = raw_artifact is not None and raw_artifact != {}
    is_mapping = isinstance(raw_artifact, dict)
    artifact = _plain_dict(raw_artifact)
    actual_type = _clean_text(artifact.get("artifact_type"))
    reason_codes: List[str] = []

    if not present:
        reason_codes.append(f"{agent_key}_artifact_missing")
    elif not is_mapping:
        reason_codes.append(f"{agent_key}_artifact_malformed")
    elif expected_type and actual_type != expected_type:
        reason_codes.append(f"{agent_key}_artifact_type_mismatch")

    validation_status = _validation_status(artifact)
    if validation_status and validation_status != "passed":
        reason_codes.append(f"{agent_key}_validation_{validation_status}")

    valid = present and is_mapping and not any(
        code.endswith("_malformed") or code.endswith("_type_mismatch")
        for code in reason_codes
    )
    return {
        "present": present,
        "is_mapping": is_mapping,
        "expected_artifact_type": expected_type,
        "actual_artifact_type": actual_type,
        "validation_status": validation_status,
        "valid": valid,
        "reason_codes": reason_codes,
    }


def _risky_safety_flags(artifact: Dict[str, Any]) -> List[str]:
    safety = _plain_dict(artifact.get("safety_metadata"))
    merged = {**safety}
    for flag in RISK_SAFETY_FLAGS:
        if flag in artifact:
            merged[flag] = artifact.get(flag)
    return sorted(
        flag
        for flag, value in merged.items()
        if flag in RISK_SAFETY_FLAGS and value is True
    )


def _safety_metadata_rollup(artifacts: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    per_agent = {}
    risky_agents: List[str] = []
    risky_flags_by_agent: Dict[str, List[str]] = {}
    for agent_key in ORDERED_AGENT_KEYS:
        artifact = artifacts.get(agent_key) or {}
        risky_flags = _risky_safety_flags(artifact)
        per_agent[agent_key] = {
            "present": bool(artifact),
            "risky_flags": risky_flags,
            "all_risky_flags_false": not risky_flags,
        }
        if risky_flags:
            risky_agents.append(agent_key)
            risky_flags_by_agent[agent_key] = risky_flags
    return {
        "per_agent": per_agent,
        "risky_agent_keys": risky_agents,
        "risky_flags_by_agent": risky_flags_by_agent,
        "all_supplied_artifacts_safe": not risky_agents,
    }


def _chain_id(
    *,
    supplied_chain_id: str,
    pipeline_run_id: str,
    owner_user_id: str,
    context_id: str,
    artifacts: Dict[str, Dict[str, Any]],
) -> str:
    if _clean_text(supplied_chain_id):
        return _clean_text(supplied_chain_id)
    seed = {
        "artifact_version": ARTIFACT_VERSION,
        "pipeline_run_id": _clean_text(pipeline_run_id),
        "owner_user_id": _clean_text(owner_user_id),
        "context_id": _clean_text(context_id),
        "artifacts": artifacts,
    }
    digest = sha256(json.dumps(seed, sort_keys=True).encode("utf-8")).hexdigest()
    return f"agent_evidence_chain_{digest[:16]}"


def _has_blocking_risk(
    *,
    artifacts: Dict[str, Dict[str, Any]],
    chain_reason_codes: List[str],
) -> bool:
    risk_words = ("blocked", "blocking", "risk", "contradiction", "do_not_tailor")
    domain_reason_codes = [
        code
        for code in chain_reason_codes
        if not _clean_text(code).endswith("_risky_safety_flags")
    ]
    reason_text = " ".join(domain_reason_codes).lower()
    if any(word in reason_text for word in risk_words):
        return True
    operator = artifacts.get("operator_review") or {}
    tailoring = artifacts.get("tailoring_decision") or {}
    critic = artifacts.get("critic") or {}
    return (
        _clean_text(operator.get("operator_review_lane")) == "hold_or_skip"
        or _clean_text(operator.get("operator_review_readiness")) == "blocked_by_risk"
        or _clean_text(tailoring.get("tailoring_readiness")) == "blocked_by_risk"
        or _clean_text(tailoring.get("tailoring_decision")) == "do_not_tailor"
        or bool(_plain_list(critic.get("risk_flags")))
        or bool(_plain_list(critic.get("contradiction_flags")))
    )


def _chain_status_and_readiness(
    *,
    validity: Dict[str, Dict[str, Any]],
    chain_reason_codes: List[str],
    artifacts: Dict[str, Dict[str, Any]],
    safety_rollup: Dict[str, Any],
) -> Dict[str, str]:
    missing_required = [
        key for key in REQUIRED_AGENT_KEYS if not validity[key]["present"]
    ]
    malformed = [
        key
        for key, item in validity.items()
        if item["present"] and not item["valid"]
    ]
    if malformed:
        return {
            "chain_status": "malformed_artifacts",
            "chain_readiness": "needs_manual_review",
        }
    if missing_required:
        return {
            "chain_status": "missing_required_artifacts",
            "chain_readiness": "insufficient_evidence",
        }
    if _has_blocking_risk(artifacts=artifacts, chain_reason_codes=chain_reason_codes):
        return {
            "chain_status": "blocked_by_risk",
            "chain_readiness": "blocked_by_risk",
        }
    if not safety_rollup.get("all_supplied_artifacts_safe"):
        return {
            "chain_status": "partial",
            "chain_readiness": "needs_manual_review",
        }
    if any(not validity[key]["present"] for key in ORDERED_AGENT_KEYS):
        return {
            "chain_status": "partial",
            "chain_readiness": "needs_more_evidence",
        }
    if any(
        validity[key]["validation_status"]
        and validity[key]["validation_status"] != "passed"
        for key in ORDERED_AGENT_KEYS
    ):
        return {
            "chain_status": "partial",
            "chain_readiness": "needs_manual_review",
        }
    return {
        "chain_status": "complete",
        "chain_readiness": "ready_for_human_review",
    }


def _terminal_operator_review_summary(artifact: Dict[str, Any]) -> Dict[str, Any]:
    summary = _plain_dict(artifact.get("review_packet_summary"))
    return {
        "job_id": _clean_text(artifact.get("job_id") or summary.get("job_id")),
        "title": _clean_text(artifact.get("title") or summary.get("title")),
        "company": _clean_text(artifact.get("company") or summary.get("company")),
        "selected_resume_id": _clean_text(
            artifact.get("selected_resume_id") or summary.get("selected_resume_id")
        ),
        "operator_review_lane": _clean_text(artifact.get("operator_review_lane")),
        "operator_review_readiness": _clean_text(
            artifact.get("operator_review_readiness")
        ),
        "human_review_required": bool(artifact.get("human_review_required")),
        "recommended_next_step": _clean_text(artifact.get("recommended_next_step")),
        "confidence": artifact.get("confidence"),
        "reason_codes": _reason_codes(artifact.get("reason_codes")),
    }


def _confidence_summary(artifacts: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    values: Dict[str, float] = {}
    for agent_key, artifact in artifacts.items():
        raw = artifact.get("confidence")
        if isinstance(raw, (int, float)):
            values[agent_key] = float(raw)
    if not values:
        return {"per_agent": {}, "minimum_confidence": None, "maximum_confidence": None}
    return {
        "per_agent": values,
        "minimum_confidence": min(values.values()),
        "maximum_confidence": max(values.values()),
    }


def _trace_payload_sample_limit(value: Any) -> int:
    try:
        limit = int(value)
    except (TypeError, ValueError):
        limit = TRACE_PAYLOAD_SAMPLE_LIMIT
    return max(0, min(limit, TRACE_PAYLOAD_MAX_SAMPLE_LIMIT))


def _bundle_artifact_type(bundle: Dict[str, Any]) -> str:
    return _clean_text(bundle.get("artifact_type")) or "unknown"


def _bundle_status_for_trace(
    bundle: Any,
) -> Dict[str, Any]:
    if bundle is None or bundle == {}:
        return {
            "valid_bundle": False,
            "source_artifact_type": "unknown",
            "chain_status": "missing_bundle",
            "chain_readiness": "insufficient_evidence",
            "reason_codes": ["agent_evidence_chain_bundle_missing"],
            "bundle": {},
        }
    if not isinstance(bundle, dict):
        return {
            "valid_bundle": False,
            "source_artifact_type": "unknown",
            "chain_status": "malformed_bundle",
            "chain_readiness": "insufficient_evidence",
            "reason_codes": ["agent_evidence_chain_bundle_malformed"],
            "bundle": {},
        }
    source_artifact_type = _bundle_artifact_type(bundle)
    if source_artifact_type != "agent_evidence_chain_bundle":
        return {
            "valid_bundle": False,
            "source_artifact_type": source_artifact_type,
            "chain_status": "malformed_bundle",
            "chain_readiness": "insufficient_evidence",
            "reason_codes": ["agent_evidence_chain_bundle_malformed"],
            "bundle": _plain_dict(bundle),
        }
    return {
        "valid_bundle": True,
        "source_artifact_type": source_artifact_type,
        "chain_status": _clean_text(bundle.get("chain_status")) or "unknown",
        "chain_readiness": _clean_text(bundle.get("chain_readiness")) or "unknown",
        "reason_codes": _reason_codes(bundle.get("chain_reason_codes")),
        "bundle": _plain_dict(bundle),
    }


def _trace_step_summary(
    *,
    agent_key: str,
    bundle: Dict[str, Any],
) -> Dict[str, Any]:
    artifacts = _plain_dict(bundle.get("artifacts"))
    artifact = _plain_dict(artifacts.get(agent_key))
    presence = _plain_dict(_plain_dict(bundle.get("artifact_presence")).get(agent_key))
    validity = _plain_dict(_plain_dict(bundle.get("artifact_validity")).get(agent_key))
    validation = _plain_dict(
        _plain_dict(bundle.get("per_agent_validation_summary")).get(agent_key)
    )
    reason_codes = _reason_codes(
        _plain_dict(bundle.get("per_agent_reason_codes")).get(agent_key)
    )
    safety = _plain_dict(artifact.get("safety_metadata"))
    status_fields = {
        key: deepcopy(artifact.get(key))
        for key in (
            "status",
            "critic_status",
            "evidence_quality",
            "priority_recommendation",
            "priority_band",
            "readiness_level",
            "tailoring_decision",
            "tailoring_intensity",
            "tailoring_readiness",
            "operator_review_lane",
            "operator_review_readiness",
            "recommended_next_step",
            "human_review_required",
        )
        if key in artifact
    }
    included_fields = {
        "artifact_type",
        "source_agent",
        "job_id",
        "title",
        "company",
        "selected_resume_id",
        "confidence",
        "reason_codes",
        "validation_summary",
        "safety_metadata",
        *status_fields.keys(),
    }
    return {
        "agent_key": agent_key,
        "artifact_present": bool(presence.get("present") or artifact),
        "artifact_valid": bool(validity.get("valid")),
        "artifact_type": _clean_text(artifact.get("artifact_type")),
        "source_agent": _clean_text(artifact.get("source_agent") or agent_key),
        "job_id": _clean_text(artifact.get("job_id")),
        "title": _clean_text(artifact.get("title")),
        "company": _clean_text(artifact.get("company")),
        "selected_resume_id": _clean_text(artifact.get("selected_resume_id")),
        "status_fields": status_fields,
        "confidence": artifact.get("confidence"),
        "reason_codes": reason_codes,
        "validation_summary": validation,
        "safety_metadata_summary": {
            "present": bool(safety),
            "risky_flags": _risky_safety_flags(artifact),
            "all_risky_flags_false": not _risky_safety_flags(artifact),
        },
        "omitted_field_count": max(0, len(set(artifact.keys()) - included_fields)),
    }


def _trace_sampling_summary(
    *,
    step_summaries: List[Dict[str, Any]],
    sample_limit: int,
) -> Dict[str, int]:
    omitted_field_count = sum(
        int(step.get("omitted_field_count") or 0)
        for step in step_summaries
    )
    return {
        "sample_limit": sample_limit,
        "included_agent_count": len(step_summaries),
        "omitted_agent_count": max(0, len(ORDERED_AGENT_KEYS) - len(step_summaries)),
        "omitted_field_count": omitted_field_count,
    }


def _trace_run_summary(
    *,
    bundle: Dict[str, Any],
    status: Dict[str, Any],
    sampling_summary: Dict[str, int],
) -> Dict[str, Any]:
    validity = _plain_dict(bundle.get("artifact_validity"))
    presence = _plain_dict(bundle.get("artifact_presence"))
    missing_agent_count = sum(
        1
        for key in ORDERED_AGENT_KEYS
        if not _plain_dict(presence.get(key)).get("present")
    )
    malformed_agent_count = sum(
        1
        for key in ORDERED_AGENT_KEYS
        if _plain_dict(presence.get(key)).get("present")
        and not _plain_dict(validity.get(key)).get("valid")
    )
    return {
        "chain_id": _clean_text(bundle.get("chain_id")),
        "pipeline_run_id": _clean_text(bundle.get("pipeline_run_id")),
        "owner_user_id": _clean_text(bundle.get("owner_user_id")),
        "context_id": _clean_text(bundle.get("context_id")),
        "chain_status": status["chain_status"],
        "chain_readiness": status["chain_readiness"],
        "ordered_agent_count": len(ORDERED_AGENT_KEYS),
        "included_agent_count": int(sampling_summary.get("included_agent_count") or 0),
        "missing_agent_count": missing_agent_count,
        "malformed_agent_count": malformed_agent_count,
        "chain_reason_codes": list(status.get("reason_codes") or []),
        "terminal_operator_review_summary": _plain_dict(
            bundle.get("terminal_operator_review_summary")
        ),
        "confidence_summary": _plain_dict(bundle.get("confidence_summary")),
        "validation_summary": _plain_dict(bundle.get("per_agent_validation_summary")),
    }


def build_agent_evidence_chain_trace_payload(
    agent_evidence_chain_bundle: Dict[str, Any] | None = None,
    *,
    enabled: bool = False,
    sample_limit: Any = TRACE_PAYLOAD_SAMPLE_LIMIT,
) -> Dict[str, Any]:
    """Build a compact in-memory trace payload from an existing evidence chain bundle."""

    status = _bundle_status_for_trace(agent_evidence_chain_bundle)
    bundle = _plain_dict(status.get("bundle"))
    safe_sample_limit = _trace_payload_sample_limit(sample_limit)
    sampled_agent_keys = list(ORDERED_AGENT_KEYS)[:safe_sample_limit]
    step_summaries = [
        _trace_step_summary(agent_key=agent_key, bundle=bundle)
        for agent_key in sampled_agent_keys
    ]
    sampling_summary = _trace_sampling_summary(
        step_summaries=step_summaries,
        sample_limit=safe_sample_limit,
    )
    chain_reason_codes = list(dict.fromkeys(status.get("reason_codes") or []))
    safety_metadata = _phase95b_safety_metadata()
    return {
        "artifact_type": "agent_evidence_chain_trace_payload",
        "payload_version": TRACE_PAYLOAD_VERSION,
        "source_artifact_type": status["source_artifact_type"],
        "source_agent": "evidence_chain_composition",
        "gate_name": TRACE_PAYLOAD_GATE_NAME,
        "enabled": bool(enabled),
        "default_off": True,
        "read_only": True,
        "diagnostic_only": True,
        "chain_id": _clean_text(bundle.get("chain_id")),
        "pipeline_run_id": _clean_text(bundle.get("pipeline_run_id")),
        "owner_user_id": _clean_text(bundle.get("owner_user_id")),
        "context_id": _clean_text(bundle.get("context_id")),
        "ordered_agent_keys": list(ORDERED_AGENT_KEYS),
        "agent_run_compatible_summary": _trace_run_summary(
            bundle=bundle,
            status={**status, "reason_codes": chain_reason_codes},
            sampling_summary=sampling_summary,
        ),
        "agent_step_compatible_summaries": step_summaries,
        "chain_status": status["chain_status"],
        "chain_readiness": status["chain_readiness"],
        "per_agent_validation_summary": _plain_dict(
            bundle.get("per_agent_validation_summary")
        ),
        "per_agent_reason_codes": _plain_dict(bundle.get("per_agent_reason_codes")),
        "chain_reason_codes": chain_reason_codes,
        "terminal_operator_review_summary": _plain_dict(
            bundle.get("terminal_operator_review_summary")
        ),
        "confidence_summary": _plain_dict(bundle.get("confidence_summary")),
        "sampling_summary": sampling_summary,
        "redaction_policy": TRACE_PAYLOAD_REDACTION_POLICY,
        "safety_metadata_rollup": _plain_dict(bundle.get("safety_metadata_rollup")),
        "safety_metadata": safety_metadata,
        "trace_persistence_requested": False,
        "trace_persistence_performed": False,
        **safety_metadata,
    }


def _trace_persistence_base_result(
    *,
    trace_payload: Dict[str, Any] | None,
    owner_user_id: str = "",
    pipeline_run_id: str = "",
    context_id: str = "",
    persistence_gate_enabled: bool = False,
    persistence_performed: bool = False,
) -> Dict[str, Any]:
    payload = _plain_dict(trace_payload)
    safety_metadata = _phase96b_safety_metadata(
        persistence_requested=bool(persistence_gate_enabled),
        persistence_performed=bool(persistence_performed),
    )
    return {
        "persistence_version": TRACE_PERSISTENCE_VERSION,
        "artifact_type": "agent_evidence_chain_trace_persistence_result",
        "source_artifact_type": "agent_evidence_chain_trace_payload",
        "gate_name": TRACE_PERSISTENCE_GATE_NAME,
        "attempted": False,
        "recorded": False,
        "reason": "",
        "record_count": 0,
        "run_count": 0,
        "step_count": 0,
        "trace_persistence_enabled": bool(persistence_gate_enabled),
        "trace_store_write_enabled": False,
        "did_prepare_trace_recording_payload": False,
        "did_call_trace_execution_helper": False,
        "did_write_database": bool(persistence_performed),
        "owner_user_id": _clean_text(owner_user_id),
        "pipeline_run_id": _clean_text(pipeline_run_id),
        "context_id": _clean_text(context_id),
        "chain_id": _clean_text(payload.get("chain_id")),
        "safety_metadata": safety_metadata,
        **safety_metadata,
    }


def _trace_payload_validity(trace_payload: Any) -> Dict[str, Any]:
    if trace_payload is None or trace_payload == {} or not isinstance(trace_payload, dict):
        return {
            "valid": False,
            "reason": "trace_payload_missing_or_malformed",
            "payload": {},
        }
    payload = _plain_dict(trace_payload)
    if _clean_text(payload.get("artifact_type")) != "agent_evidence_chain_trace_payload":
        return {
            "valid": False,
            "reason": "trace_payload_wrong_artifact_type",
            "payload": payload,
        }
    return {"valid": True, "reason": "", "payload": payload}


def _trace_store_payload_builder_module() -> Any:
    return __import__(
        "src.storage.agent_trace.store",
        fromlist=[
            "create_agent_run_postgres_payload",
            "record_agent_step_postgres_payload",
        ],
    )


def _trace_persistence_run_record(
    *,
    trace_payload: Dict[str, Any],
    owner_user_id: str,
    pipeline_run_id: str,
    context_id: str,
) -> Dict[str, Any]:
    summary = _plain_dict(trace_payload.get("agent_run_compatible_summary"))
    chain_id = _clean_text(trace_payload.get("chain_id"))
    return {
        "agent_run_id": _clean_text(
            f"agent_evidence_chain_trace:{chain_id or pipeline_run_id}:{context_id}"
        ),
        "owner_user_id": owner_user_id,
        "pipeline_run_id": pipeline_run_id,
        "context_id": context_id,
        "status": "succeeded",
        "started_at": "1970-01-01T00:00:00+00:00",
        "completed_at": "1970-01-01T00:00:00+00:00",
        "summary_json": {
            **summary,
            "artifact_type": _clean_text(trace_payload.get("artifact_type")),
            "payload_version": _clean_text(trace_payload.get("payload_version")),
            "source_agent": "evidence_chain_composition",
            "chain_id": chain_id,
            "chain_status": _clean_text(trace_payload.get("chain_status")),
            "chain_readiness": _clean_text(trace_payload.get("chain_readiness")),
            "chain_reason_codes": _reason_codes(trace_payload.get("chain_reason_codes")),
            "sampling_summary": _plain_dict(trace_payload.get("sampling_summary")),
            "redaction_policy": _clean_text(trace_payload.get("redaction_policy")),
            "safety_metadata": _plain_dict(trace_payload.get("safety_metadata")),
        },
        "error": "",
    }


def _trace_step_status(step_summary: Dict[str, Any]) -> str:
    if not bool(step_summary.get("artifact_present")):
        return "skipped"
    if bool(step_summary.get("artifact_valid")):
        return "succeeded"
    return "degraded"


def _trace_persistence_step_records(
    *,
    trace_payload: Dict[str, Any],
    run_record: Dict[str, Any],
    owner_user_id: str,
    pipeline_run_id: str,
    context_id: str,
) -> List[Dict[str, Any]]:
    step_summaries = [
        _plain_dict(step)
        for step in _plain_list(trace_payload.get("agent_step_compatible_summaries"))
    ]
    records: List[Dict[str, Any]] = []
    for index, step_summary in enumerate(step_summaries):
        agent_key = _clean_text(step_summary.get("agent_key")) or f"agent_{index}"
        records.append(
            {
                "agent_step_id": _clean_text(
                    f"{run_record['agent_run_id']}:{index}:{agent_key}"
                ),
                "agent_run_id": _clean_text(run_record.get("agent_run_id")),
                "owner_user_id": owner_user_id,
                "pipeline_run_id": pipeline_run_id,
                "context_id": context_id,
                "agent_name": agent_key,
                "agent_version": _clean_text(trace_payload.get("payload_version")),
                "input_json": {
                    "source_artifact_type": _clean_text(
                        trace_payload.get("source_artifact_type")
                    ),
                    "chain_id": _clean_text(trace_payload.get("chain_id")),
                    "pipeline_run_id": pipeline_run_id,
                    "owner_user_id": owner_user_id,
                    "context_id": context_id,
                    "gate_name": TRACE_PERSISTENCE_GATE_NAME,
                    "step_index": index,
                    "redaction_policy": _clean_text(trace_payload.get("redaction_policy")),
                },
                "output_json": step_summary,
                "validation_json": _plain_dict(step_summary.get("validation_summary")),
                "status": _trace_step_status(step_summary),
                "started_at": "1970-01-01T00:00:00+00:00",
                "completed_at": "1970-01-01T00:00:00+00:00",
                "latency_ms": None,
                "model_provider": "",
                "model_name": "",
                "token_usage_json": {},
                "cost_json": {},
                "error": "",
            }
        )
    return records


def _build_agent_evidence_chain_trace_recording_payload(
    *,
    trace_payload: Dict[str, Any],
    owner_user_id: str,
    pipeline_run_id: str,
    context_id: str,
) -> Dict[str, Any]:
    trace_store = _trace_store_payload_builder_module()
    run_record = _trace_persistence_run_record(
        trace_payload=trace_payload,
        owner_user_id=owner_user_id,
        pipeline_run_id=pipeline_run_id,
        context_id=context_id,
    )
    run_payload = getattr(trace_store, "create_" "agent_run_postgres_payload")(
        record=run_record,
        print_only=True,
        ensure_schema=False,
    )
    run_snapshot = _plain_dict(run_payload.get("run"))
    step_records = _trace_persistence_step_records(
        trace_payload=trace_payload,
        run_record=run_snapshot,
        owner_user_id=owner_user_id,
        pipeline_run_id=pipeline_run_id,
        context_id=context_id,
    )
    step_payloads = [
        getattr(trace_store, "record_" "agent_step_postgres_payload")(
            record=step_record,
            print_only=True,
            ensure_schema=False,
        )
        for step_record in step_records
    ]
    records = [
        {
            "record_type": "agent_run",
            "table": "agent_runs",
            "sql": _clean_text(run_payload.get("sql")),
            "params": (),
            "snapshot": run_snapshot,
        },
        *[
            {
                "record_type": "agent_step",
                "table": "agent_steps",
                "sql": _clean_text(step_payload.get("sql")),
                "params": (),
                "snapshot": _plain_dict(step_payload.get("step")),
            }
            for step_payload in step_payloads
        ],
    ]
    return {
        "operation": "build_agent_evidence_chain_trace_recording_payload",
        "run_count": 1,
        "step_count": len(step_payloads),
        "record_count": len(records),
        "records": records,
    }


def _execute_agent_evidence_chain_trace_recording(
    recording_payload: Dict[str, Any],
    *,
    cursor: Any | None = None,
    execute_callback: Any | None = None,
) -> Dict[str, Any]:
    executed_operations: List[Dict[str, Any]] = []
    for record in _plain_list(recording_payload.get("records")):
        record_map = _plain_dict(record)
        operation = {
            "record_type": _clean_text(record_map.get("record_type")),
            "table": _clean_text(record_map.get("table")),
            "sql": _clean_text(record_map.get("sql")),
            "params": tuple(record_map.get("params") or ()),
        }
        if cursor is not None:
            getattr(cursor, "execute")(operation["sql"], operation["params"])
        else:
            execute_callback(deepcopy(operation))
        executed_operations.append(
            {
                "record_type": operation["record_type"],
                "table": operation["table"],
            }
        )
    return {
        "operation": "execute_agent_evidence_chain_trace_recording",
        "executed_record_count": len(executed_operations),
        "executed_operations": executed_operations,
    }


def persist_agent_evidence_chain_trace_payload(
    *,
    trace_payload: Dict[str, Any] | None,
    owner_user_id: str = "",
    pipeline_run_id: str = "",
    context_id: str = "",
    cursor: Any | None = None,
    execute_callback: Any | None = None,
    persistence_gate_enabled: bool = False,
    strict: bool = False,
) -> Dict[str, Any]:
    """Persist an evidence-chain trace payload only through an injected executor."""

    context = {
        "owner_user_id": _clean_text(owner_user_id),
        "pipeline_run_id": _clean_text(pipeline_run_id),
        "context_id": _clean_text(context_id),
    }
    payload_state = _trace_payload_validity(trace_payload)
    base_result = _trace_persistence_base_result(
        trace_payload=payload_state.get("payload"),
        persistence_gate_enabled=persistence_gate_enabled,
        **context,
    )
    if not persistence_gate_enabled:
        return {**base_result, "reason": "trace_persistence_disabled"}
    if not all(context.values()):
        return {**base_result, "reason": "missing_trace_context"}
    if cursor is None and execute_callback is None:
        return {**base_result, "reason": "write_executor_missing"}
    if cursor is not None and execute_callback is not None:
        return {**base_result, "reason": "multiple_write_executors"}
    if not payload_state["valid"]:
        return {**base_result, "reason": payload_state["reason"]}

    payload = _plain_dict(payload_state.get("payload"))
    try:
        recording_payload = _build_agent_evidence_chain_trace_recording_payload(
            trace_payload=payload,
            **context,
        )
        execution_result = _execute_agent_evidence_chain_trace_recording(
            recording_payload,
            cursor=cursor,
            execute_callback=execute_callback,
        )
        success_base = _trace_persistence_base_result(
            trace_payload=payload,
            persistence_gate_enabled=persistence_gate_enabled,
            persistence_performed=True,
            **context,
        )
        run_snapshot = _plain_dict(
            _plain_dict((recording_payload.get("records") or [{}])[0]).get("snapshot")
        )
        return {
            **success_base,
            "attempted": True,
            "recorded": True,
            "reason": "",
            "record_count": int(recording_payload.get("record_count") or 0),
            "run_count": int(recording_payload.get("run_count") or 0),
            "step_count": int(recording_payload.get("step_count") or 0),
            "trace_store_write_enabled": True,
            "did_prepare_trace_recording_payload": True,
            "did_call_trace_execution_helper": True,
            "agent_run_id": _clean_text(run_snapshot.get("agent_run_id")),
            "recording_payload": recording_payload,
            "execution_result": execution_result,
        }
    except Exception as exc:
        if strict:
            raise
        return {
            **base_result,
            "attempted": True,
            "recorded": False,
            "reason": "trace_persistence_failed",
            "error_message": str(exc),
        }


def build_agent_evidence_chain_bundle(
    *,
    jd_intelligence: Dict[str, Any] | None = None,
    resume_match_jd_evidence: Dict[str, Any] | None = None,
    critic_resume_match_jd_evidence: Dict[str, Any] | None = None,
    job_prioritization_critic_evidence: Dict[str, Any] | None = None,
    tailoring_decision_priority_evidence: Dict[str, Any] | None = None,
    operator_review_tailoring_evidence: Dict[str, Any] | None = None,
    enabled: bool = False,
    chain_id: str = "",
    pipeline_run_id: str = "",
    owner_user_id: str = "",
    context_id: str = "",
) -> Dict[str, Any]:
    """Bundle already-built agent evidence artifacts without executing agents."""

    raw_artifacts = {
        "jd_intelligence": jd_intelligence,
        "resume_match": resume_match_jd_evidence,
        "critic": critic_resume_match_jd_evidence,
        "job_prioritization": job_prioritization_critic_evidence,
        "tailoring_decision": tailoring_decision_priority_evidence,
        "operator_review": operator_review_tailoring_evidence,
    }
    artifacts = {
        key: _plain_dict(value)
        for key, value in raw_artifacts.items()
    }
    artifact_presence = {
        key: {
            "present": value is not None and value != {},
            "is_mapping": isinstance(value, dict),
        }
        for key, value in raw_artifacts.items()
    }
    artifact_validity = {
        key: _artifact_validity(agent_key=key, raw_artifact=value)
        for key, value in raw_artifacts.items()
    }
    per_agent_validation_summary = {
        key: {
            "validation_status": artifact_validity[key]["validation_status"],
            "valid": artifact_validity[key]["valid"],
            "reason_codes": list(artifact_validity[key]["reason_codes"]),
        }
        for key in ORDERED_AGENT_KEYS
    }
    per_agent_reason_codes = {
        key: list(
            dict.fromkeys(
                [
                    *artifact_validity[key]["reason_codes"],
                    *_reason_codes(artifacts[key].get("reason_codes")),
                ]
            )
        )
        for key in ORDERED_AGENT_KEYS
    }
    chain_reason_codes = list(
        dict.fromkeys(
            code
            for key in ORDERED_AGENT_KEYS
            for code in per_agent_reason_codes[key]
            if code
        )
    )
    safety_rollup = _safety_metadata_rollup(artifacts)
    for agent_key in safety_rollup.get("risky_agent_keys") or []:
        chain_reason_codes.append(f"{agent_key}_risky_safety_flags")
    chain_reason_codes = list(dict.fromkeys(chain_reason_codes))
    status = _chain_status_and_readiness(
        validity=artifact_validity,
        chain_reason_codes=chain_reason_codes,
        artifacts=artifacts,
        safety_rollup=safety_rollup,
    )
    safety_metadata = _phase94b_safety_metadata()
    resolved_chain_id = _chain_id(
        supplied_chain_id=chain_id,
        pipeline_run_id=pipeline_run_id,
        owner_user_id=owner_user_id,
        context_id=context_id,
        artifacts=artifacts,
    )
    return {
        "artifact_type": "agent_evidence_chain_bundle",
        "artifact_version": ARTIFACT_VERSION,
        "source_agent": "evidence_chain_composition",
        "ordered_agent_keys": list(ORDERED_AGENT_KEYS),
        "gate_name": GATE_NAME,
        "enabled": bool(enabled),
        "default_off": True,
        "read_only": True,
        "diagnostic_only": True,
        "chain_id": resolved_chain_id,
        "pipeline_run_id": _clean_text(pipeline_run_id),
        "owner_user_id": _clean_text(owner_user_id),
        "context_id": _clean_text(context_id),
        "artifacts": artifacts,
        "artifact_presence": artifact_presence,
        "artifact_validity": artifact_validity,
        "per_agent_validation_summary": per_agent_validation_summary,
        "per_agent_reason_codes": per_agent_reason_codes,
        "chain_reason_codes": chain_reason_codes,
        "chain_status": status["chain_status"],
        "chain_readiness": status["chain_readiness"],
        "terminal_operator_review_summary": _terminal_operator_review_summary(
            artifacts["operator_review"]
        ),
        "confidence_summary": _confidence_summary(artifacts),
        "safety_metadata_rollup": safety_rollup,
        "safety_metadata": safety_metadata,
        **safety_metadata,
    }
