"""Deterministic dry-run conversion of existing payloads into evidence chunks.

The helper delegates chunk validation and stable identifiers to the Phase 8B
vector evidence contract. It performs no indexing, embeddings, provider calls,
database access, pipeline work, or application mutations.
"""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

from src.agents import vector_evidence_contract


STATUS_READY = "vector_evidence_indexing_dry_run_ready"
STATUS_NO_CHUNKS = "vector_evidence_indexing_dry_run_no_chunks"
STATUS_INVALID = "vector_evidence_indexing_dry_run_invalid"


def _snapshot(value: Any) -> Any:
    return deepcopy(value)


def _plain_dict(value: Any) -> dict[str, Any]:
    return _snapshot(value) if isinstance(value, dict) else {}


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").split())


def _json_text(value: Any) -> str:
    if value in (None, "", [], {}):
        return ""
    if isinstance(value, str):
        return _clean_text(value)
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
    return _clean_text(value)


def _first_value(sources: list[dict[str, Any]], keys: tuple[str, ...]) -> Any:
    for source in sources:
        for key in keys:
            value = source.get(key)
            if value not in (None, "", [], {}):
                return _snapshot(value)
    return None


def _metadata_sources(payload: dict[str, Any]) -> list[dict[str, Any]]:
    sources = [payload]
    for key in (
        "metadata",
        "metadata_json",
        "trace_context_summary",
        "source_deterministic_context",
        "lookup_context",
        "profile",
    ):
        nested = payload.get(key)
        if isinstance(nested, dict):
            sources.append(_snapshot(nested))
    return sources


def _metadata(
    payload: dict[str, Any],
    *,
    default_stage: str,
    default_agent_name: str,
) -> dict[str, Any]:
    sources = _metadata_sources(payload)
    result = {
        field: _clean_text(_first_value(sources, (field,)))
        for field in vector_evidence_contract.METADATA_FIELDS
    }
    result["stage"] = result["stage"] or _clean_text(default_stage)
    result["agent_name"] = result["agent_name"] or _clean_text(default_agent_name)
    result["run_id"] = result["run_id"] or _clean_text(
        _first_value(sources, ("pipeline_run_id", "agent_run_id"))
    )
    result["resume_version"] = result["resume_version"] or _clean_text(
        _first_value(sources, ("resume_name", "resume_id"))
    )
    safety_flags = _first_value(sources, ("safety_flags", "safety_metadata"))
    result["safety_flags"] = (
        _plain_dict(safety_flags) if isinstance(safety_flags, dict) else {}
    )
    result["read_only"] = True
    return result


def _evidence_text(
    payload: dict[str, Any],
    *,
    preferred_keys: tuple[str, ...],
    composite_keys: tuple[str, ...],
) -> str:
    preferred = _first_value([payload], preferred_keys)
    preferred_text = _json_text(preferred)
    if preferred_text:
        return preferred_text

    parts: list[str] = []
    for key in composite_keys:
        text = _json_text(payload.get(key))
        if text:
            parts.append(f"{key}: {text}")
    return "\n".join(parts)


def vector_evidence_indexing_dry_run_safety_metadata() -> dict[str, bool]:
    safety = vector_evidence_contract.vector_evidence_contract_safety_metadata()
    safety.update(
        {
            "vector_evidence_indexing_dry_run": True,
            "service_helper_added": False,
        }
    )
    return safety


def _candidate_spec(
    *,
    payload: dict[str, Any],
    chunk_type: str,
    preferred_keys: tuple[str, ...],
    composite_keys: tuple[str, ...],
    default_stage: str,
    default_agent_name: str,
) -> dict[str, Any] | None:
    text = _evidence_text(
        payload,
        preferred_keys=preferred_keys,
        composite_keys=composite_keys,
    )
    if not text:
        return None
    return {
        "chunk_type": chunk_type,
        "evidence_text": text,
        "metadata": _metadata(
            payload,
            default_stage=default_stage,
            default_agent_name=default_agent_name,
        ),
    }


def _source_specs(
    *,
    job_payload: dict[str, Any],
    job_description_payload: dict[str, Any],
    resume_profile_payload: dict[str, Any],
    trace_evidence_payload: dict[str, Any],
    operator_review_packet_payload: dict[str, Any],
    future_application_outcome_payload: dict[str, Any],
) -> list[tuple[str, dict[str, Any], dict[str, Any]]]:
    job_config = {
        "chunk_type": "job_description",
        "preferred_keys": (
            "job_description",
            "description",
            "retrieval_text",
            "evidence_text",
            "text",
        ),
        "composite_keys": (
            "title",
            "company",
            "required_skills",
            "preferred_skills",
            "responsibilities",
            "qualifications",
        ),
        "default_stage": "job_description",
        "default_agent_name": "jd_intelligence_agent",
    }
    return [
        ("job_payload", job_payload, job_config),
        (
            "job_description_payload",
            job_description_payload,
            _snapshot(job_config),
        ),
        (
            "resume_profile_payload",
            resume_profile_payload,
            {
                "chunk_type": "resume_profile",
                "preferred_keys": (
                    "evidence_text",
                    "resume_text",
                    "profile_text",
                    "summary",
                    "content",
                ),
                "composite_keys": (
                    "resume_name",
                    "headline",
                    "skills",
                    "experience",
                    "projects",
                    "bullets",
                    "preferred_roles",
                ),
                "default_stage": "resume_match",
                "default_agent_name": "resume_match_agent",
            },
        ),
        (
            "trace_evidence_payload",
            trace_evidence_payload,
            {
                "chunk_type": "trace_evidence",
                "preferred_keys": (
                    "evidence_text",
                    "trace_evidence",
                    "trace_evidence_pack",
                ),
                "composite_keys": (
                    "trace_summary",
                    "stage_trace_health",
                    "stage_trace_readiness",
                    "agent_steps",
                    "steps",
                    "output_json",
                    "validation_json",
                ),
                "default_stage": "trace_readback",
                "default_agent_name": "agent_trace",
            },
        ),
        (
            "operator_review_packet_payload",
            operator_review_packet_payload,
            {
                "chunk_type": "operator_review_packet",
                "preferred_keys": ("evidence_text",),
                "composite_keys": (
                    "packet_status",
                    "packet_title",
                    "recommended_operator_action",
                    "review_focus",
                    "overlay_readiness_summary",
                    "trace_context_summary",
                    "operator_review_summary",
                    "safety_metadata",
                ),
                "default_stage": "operator_review",
                "default_agent_name": "pipeline_agent_review_packet",
            },
        ),
        (
            "future_application_outcome_payload",
            future_application_outcome_payload,
            {
                "chunk_type": "future_application_outcome_feedback",
                "preferred_keys": (
                    "outcome_evidence",
                    "evidence_text",
                    "outcome_summary",
                ),
                "composite_keys": (
                    "outcome",
                    "application_status",
                    "operator_decision",
                    "feedback",
                    "notes",
                ),
                "default_stage": "future_application_outcome_feedback",
                "default_agent_name": "future_outcome_feedback",
            },
        ),
    ]


def build_vector_evidence_indexing_dry_run_payload(
    *,
    job_payload: dict[str, Any] | None = None,
    job_description_payload: dict[str, Any] | None = None,
    resume_profile_payload: dict[str, Any] | None = None,
    trace_evidence_payload: dict[str, Any] | None = None,
    operator_review_packet_payload: dict[str, Any] | None = None,
    future_application_outcome_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build deduplicated chunk candidates without indexing or side effects."""

    job = _plain_dict(job_payload)
    job_description = _plain_dict(job_description_payload)
    resume = _plain_dict(resume_profile_payload)
    trace = _plain_dict(trace_evidence_payload)
    review = _plain_dict(operator_review_packet_payload)
    future_outcome = _plain_dict(future_application_outcome_payload)

    candidate_specs: list[dict[str, Any]] = []
    skipped_reasons: list[dict[str, str]] = []
    supplied_source_count = 0

    for source_name, source_payload, config in _source_specs(
        job_payload=job,
        job_description_payload=job_description,
        resume_profile_payload=resume,
        trace_evidence_payload=trace,
        operator_review_packet_payload=review,
        future_application_outcome_payload=future_outcome,
    ):
        if not source_payload:
            continue
        supplied_source_count += 1
        candidate = _candidate_spec(payload=source_payload, **config)
        if candidate is None:
            skipped_reasons.append(
                {"source": source_name, "reason": "no_usable_evidence_text"}
            )
            continue
        candidate_specs.append(candidate)

    normalized = vector_evidence_contract.build_vector_evidence_chunk_candidates(
        candidate_specs
    )
    deduplicated: list[dict[str, Any]] = []
    seen_chunk_ids: set[str] = set()
    for candidate in normalized.get("chunk_candidates", []):
        chunk = _plain_dict(candidate)
        chunk_id = _clean_text(chunk.get("chunk_id"))
        if chunk_id in seen_chunk_ids:
            skipped_reasons.append(
                {
                    "source": _clean_text(chunk.get("chunk_type")),
                    "reason": "duplicate_chunk_candidate",
                }
            )
            continue
        seen_chunk_ids.add(chunk_id)
        deduplicated.append(chunk)

    for invalid in normalized.get("invalid_chunks", []):
        item = _plain_dict(invalid)
        skipped_reasons.append(
            {
                "source": f"candidate_index_{item.get('source_index', '')}",
                "reason": "invalid_chunk_candidate",
            }
        )

    if deduplicated:
        status = STATUS_READY
    elif normalized.get("status") == vector_evidence_contract.STATUS_INVALID_REQUEST:
        status = STATUS_INVALID
    else:
        status = STATUS_NO_CHUNKS

    chunk_types_present = sorted(
        {
            _clean_text(candidate.get("chunk_type"))
            for candidate in deduplicated
            if _clean_text(candidate.get("chunk_type"))
        }
    )
    return {
        "status": status,
        "dry_run_type": "vector_evidence_indexing_dry_run",
        "contract_version": vector_evidence_contract.CONTRACT_VERSION,
        "dry_run_only": True,
        "indexing_executed": False,
        "supplied_source_count": supplied_source_count,
        "chunk_candidates": deduplicated,
        "chunk_count": len(deduplicated),
        "chunk_types_present": chunk_types_present,
        "skipped_reasons": skipped_reasons,
        "provider_backed_automated_agents": 0,
        "live_provider_backed_automated_agents": 0,
        "mutation_authorized_agents": 0,
        "evaluation_boundaries": {
            "prefilter_relevance": "separate_unchanged",
            "llm_shadow_evaluation": "separate_advisory_only",
            "final_application_scoring": "separate_unchanged",
            "retrieval_evidence_support": "indexing_dry_run_only",
        },
        "safety_metadata": vector_evidence_indexing_dry_run_safety_metadata(),
    }
