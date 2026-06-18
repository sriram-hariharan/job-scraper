"""Deterministic, in-memory contracts for future vector evidence support.

This module normalizes caller-supplied evidence and retrieval payloads only.
It does not create embeddings, connect to a vector database, call providers,
read or write storage, add a pipeline stage, or influence application behavior.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from typing import Any


CONTRACT_VERSION = "phase-8b-vector-evidence-contract-v1"

STATUS_READY = "vector_evidence_contract_ready"
STATUS_NO_CHUNKS = "vector_evidence_no_chunks"
STATUS_INVALID_REQUEST = "vector_evidence_invalid_request"
STATUS_RETRIEVAL_NOT_CONFIGURED = "vector_retrieval_not_configured"

CHUNK_TYPES: tuple[str, ...] = (
    "job_description",
    "resume_profile",
    "trace_evidence",
    "operator_review_packet",
    "future_application_outcome_feedback",
)

METADATA_FIELDS: tuple[str, ...] = (
    "job_id",
    "company",
    "title",
    "source",
    "stage",
    "agent_name",
    "trace_id",
    "run_id",
    "resume_version",
    "profile_version",
    "created_at",
)


def _snapshot(value: Any) -> Any:
    return deepcopy(value)


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").split())


def _plain_dict(value: Any) -> dict[str, Any]:
    return _snapshot(value) if isinstance(value, dict) else {}


def _plain_list(value: Any) -> list[Any]:
    return _snapshot(value) if isinstance(value, list) else []


def _safe_top_k(value: Any) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return 5
    return max(1, min(parsed, 100))


def _text_list(value: Any) -> list[str]:
    if not isinstance(value, (list, tuple, set)):
        return []
    normalized: list[str] = []
    for item in value:
        text = _clean_text(item)
        if text and text not in normalized:
            normalized.append(text)
    return normalized


def vector_evidence_contract_safety_metadata() -> dict[str, bool]:
    return {
        "read_only": True,
        "advisory_only": True,
        "vector_evidence_contract_only": True,
        "embeddings_created": False,
        "vector_db_connected": False,
        "provider_calls_made": False,
        "did_read_database": False,
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
        "auto_apply_enabled": False,
        "mutation_authorized": False,
    }


def _evaluation_boundaries() -> dict[str, str]:
    return {
        "prefilter_relevance": "separate_unchanged",
        "llm_shadow_evaluation": "separate_advisory_only",
        "final_application_scoring": "separate_unchanged",
        "retrieval_evidence_support": "contract_only_advisory",
    }


def _base_payload(*, status: str, contract_type: str) -> dict[str, Any]:
    return {
        "contract_version": CONTRACT_VERSION,
        "status": status,
        "contract_type": contract_type,
        "default_off": True,
        "provider_backed_automated_agents": 0,
        "live_provider_backed_automated_agents": 0,
        "mutation_authorized_agents": 0,
        "evaluation_boundaries": _evaluation_boundaries(),
        "safety_metadata": vector_evidence_contract_safety_metadata(),
    }


def _normalized_metadata(metadata: Any) -> dict[str, Any]:
    source = _plain_dict(metadata)
    normalized: dict[str, Any] = {
        field: _clean_text(source.get(field)) for field in METADATA_FIELDS
    }
    safety_flags = source.get("safety_flags")
    normalized["safety_flags"] = (
        _plain_dict(safety_flags) if isinstance(safety_flags, dict) else {}
    )
    normalized["read_only"] = source.get("read_only") is not False
    return normalized


def _stable_chunk_id(
    *,
    chunk_type: str,
    evidence_text: str,
    metadata: dict[str, Any],
) -> str:
    identity_fields = [
        chunk_type,
        evidence_text,
        *[_clean_text(metadata.get(field)) for field in METADATA_FIELDS],
    ]
    digest = sha256("\x1f".join(identity_fields).encode("utf-8")).hexdigest()
    return f"vector-evidence:{digest[:24]}"


def build_vector_evidence_chunk_candidate(
    *,
    chunk_type: str,
    evidence_text: str,
    metadata: dict[str, Any] | None = None,
    chunk_id: str = "",
) -> dict[str, Any]:
    """Normalize one caller-supplied evidence chunk without embedding it."""

    normalized_type = _clean_text(chunk_type)
    normalized_text = _clean_text(evidence_text)
    normalized_metadata = _normalized_metadata(metadata)
    validation_errors: list[str] = []

    if normalized_type not in CHUNK_TYPES:
        validation_errors.append("unsupported_chunk_type")
    if not normalized_text:
        validation_errors.append("missing_evidence_text")
    if normalized_metadata["read_only"] is not True:
        validation_errors.append("metadata_read_only_required")

    normalized_chunk_id = _clean_text(chunk_id)
    if not normalized_chunk_id and not validation_errors:
        normalized_chunk_id = _stable_chunk_id(
            chunk_type=normalized_type,
            evidence_text=normalized_text,
            metadata=normalized_metadata,
        )

    status = STATUS_READY if not validation_errors else STATUS_INVALID_REQUEST
    payload = _base_payload(
        status=status,
        contract_type="vector_evidence_chunk_candidate",
    )
    payload.update(
        {
            "chunk_candidate": {
                "chunk_id": normalized_chunk_id,
                "chunk_type": normalized_type,
                "evidence_text": normalized_text,
                "metadata": normalized_metadata,
                "embedding": None,
            },
            "validation": {
                "is_valid": not validation_errors,
                "errors": validation_errors,
                "supported_chunk_types": list(CHUNK_TYPES),
            },
        }
    )
    return payload


def build_vector_evidence_chunk_candidates(
    chunk_candidates: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    """Normalize an ordered collection of caller-supplied chunk candidates."""

    source_chunks = _plain_list(chunk_candidates)
    normalized_chunks: list[dict[str, Any]] = []
    invalid_chunks: list[dict[str, Any]] = []

    for index, source in enumerate(source_chunks):
        item = _plain_dict(source)
        normalized = build_vector_evidence_chunk_candidate(
            chunk_type=_clean_text(item.get("chunk_type")),
            evidence_text=_clean_text(
                item.get("evidence_text")
                or item.get("text")
                or item.get("content")
            ),
            metadata=_plain_dict(item.get("metadata")),
            chunk_id=_clean_text(item.get("chunk_id")),
        )
        candidate = _plain_dict(normalized.get("chunk_candidate"))
        if normalized["validation"]["is_valid"]:
            normalized_chunks.append(candidate)
        else:
            invalid_chunks.append(
                {
                    "source_index": index,
                    "chunk_candidate": candidate,
                    "errors": _plain_list(normalized["validation"].get("errors")),
                }
            )

    if not source_chunks:
        status = STATUS_NO_CHUNKS
    elif invalid_chunks:
        status = STATUS_INVALID_REQUEST
    else:
        status = STATUS_READY

    payload = _base_payload(
        status=status,
        contract_type="vector_evidence_chunk_candidate_collection",
    )
    payload.update(
        {
            "chunk_candidates": normalized_chunks,
            "chunk_count": len(normalized_chunks),
            "invalid_chunks": invalid_chunks,
            "invalid_chunk_count": len(invalid_chunks),
            "validation": {
                "is_valid": not invalid_chunks,
                "errors": (
                    ["one_or_more_chunk_candidates_invalid"]
                    if invalid_chunks
                    else []
                ),
            },
        }
    )
    return payload


def build_vector_retrieval_request_contract(
    *,
    query_text: str,
    chunk_types: list[str] | tuple[str, ...] | None = None,
    metadata_filters: dict[str, Any] | None = None,
    top_k: int = 5,
    retrieval_enabled: bool = False,
    request_id: str = "",
) -> dict[str, Any]:
    """Build a retrieval request description without performing retrieval."""

    query = _clean_text(query_text)
    requested_types = _text_list(chunk_types or CHUNK_TYPES)
    unsupported_types = [
        chunk_type for chunk_type in requested_types if chunk_type not in CHUNK_TYPES
    ]
    validation_errors: list[str] = []
    if not query:
        validation_errors.append("missing_query_text")
    if not requested_types:
        validation_errors.append("missing_chunk_types")
    if unsupported_types:
        validation_errors.append("unsupported_chunk_types")

    if validation_errors:
        status = STATUS_INVALID_REQUEST
    elif not retrieval_enabled:
        status = STATUS_RETRIEVAL_NOT_CONFIGURED
    else:
        status = STATUS_READY

    payload = _base_payload(
        status=status,
        contract_type="vector_retrieval_request",
    )
    payload.update(
        {
            "retrieval_configured": False,
            "retrieval_executed": False,
            "request": {
                "request_id": _clean_text(request_id),
                "query_text": query,
                "chunk_types": requested_types,
                "metadata_filters": _normalized_metadata(metadata_filters),
                "top_k": _safe_top_k(top_k),
                "retrieval_enabled": bool(retrieval_enabled),
            },
            "validation": {
                "is_valid": not validation_errors,
                "errors": validation_errors,
                "unsupported_chunk_types": unsupported_types,
            },
        }
    )
    return payload


def build_vector_retrieval_no_result_fallback(
    *,
    request_contract: dict[str, Any] | None = None,
    reason: str = "vector_retrieval_not_configured",
) -> dict[str, Any]:
    """Return a deterministic advisory fallback with no evidence."""

    request = _plain_dict(request_contract)
    status = (
        STATUS_INVALID_REQUEST
        if request.get("status") == STATUS_INVALID_REQUEST
        else STATUS_RETRIEVAL_NOT_CONFIGURED
    )
    payload = _base_payload(
        status=status,
        contract_type="vector_retrieval_response",
    )
    payload.update(
        {
            "request": _plain_dict(request.get("request")),
            "retrieval_configured": False,
            "retrieval_executed": False,
            "evidence_found": False,
            "evidence_results": [],
            "result_count": 0,
            "fallback": {
                "used": True,
                "reason": _clean_text(reason) or STATUS_RETRIEVAL_NOT_CONFIGURED,
                "message": "No vector evidence is available; continue without retrieval influence.",
            },
        }
    )
    return payload


def build_vector_retrieval_response_contract(
    *,
    request_contract: dict[str, Any] | None,
    evidence_results: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Normalize caller-supplied retrieval results without querying a backend."""

    request = _plain_dict(request_contract)
    if request.get("status") != STATUS_READY:
        return build_vector_retrieval_no_result_fallback(
            request_contract=request,
            reason=_clean_text(request.get("status"))
            or STATUS_RETRIEVAL_NOT_CONFIGURED,
        )

    normalized = build_vector_evidence_chunk_candidates(evidence_results)
    if normalized["status"] == STATUS_INVALID_REQUEST:
        payload = _base_payload(
            status=STATUS_INVALID_REQUEST,
            contract_type="vector_retrieval_response",
        )
        payload.update(
            {
                "request": _plain_dict(request.get("request")),
                "retrieval_configured": False,
                "retrieval_executed": False,
                "evidence_found": False,
                "evidence_results": [],
                "result_count": 0,
                "invalid_results": _plain_list(normalized.get("invalid_chunks")),
                "fallback": {
                    "used": True,
                    "reason": "invalid_evidence_results",
                    "message": "Invalid evidence was rejected without retrieval influence.",
                },
            }
        )
        return payload

    results = _plain_list(normalized.get("chunk_candidates"))
    if not results:
        payload = _base_payload(
            status=STATUS_NO_CHUNKS,
            contract_type="vector_retrieval_response",
        )
    else:
        payload = _base_payload(
            status=STATUS_READY,
            contract_type="vector_retrieval_response",
        )
    payload.update(
        {
            "request": _plain_dict(request.get("request")),
            "retrieval_configured": False,
            "retrieval_executed": False,
            "evidence_found": bool(results),
            "evidence_results": results,
            "result_count": len(results),
            "fallback": {
                "used": not results,
                "reason": "vector_evidence_no_chunks" if not results else "",
                "message": (
                    "No vector evidence was supplied; continue without retrieval influence."
                    if not results
                    else ""
                ),
            },
        }
    )
    return payload

