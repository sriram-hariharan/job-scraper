"""Deterministic lexical retrieval over Phase 8 vector evidence candidates.

This dry-run helper normalizes caller-supplied Phase 8C chunk candidates and
performs bounded token-overlap matching in memory. It does not create
embeddings, connect to a vector database, call providers, access storage, add a
pipeline stage, or influence scoring, ranking, queues, approvals, or actions.
"""

from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

from src.agents import vector_evidence_contract
from src.agents import vector_evidence_indexing_dry_run


STATUS_READY = "vector_evidence_retrieval_dry_run_ready"
STATUS_NO_RESULTS = "vector_evidence_retrieval_dry_run_no_results"
STATUS_INVALID_QUERY = "vector_evidence_retrieval_dry_run_invalid_query"

FILTER_FIELDS: tuple[str, ...] = (
    "chunk_type",
    "job_id",
    "company",
    "agent_name",
    "stage",
)


def _snapshot(value: Any) -> Any:
    return deepcopy(value)


def _plain_dict(value: Any) -> dict[str, Any]:
    return _snapshot(value) if isinstance(value, dict) else {}


def _plain_list(value: Any) -> list[Any]:
    return _snapshot(value) if isinstance(value, list) else []


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").split())


def _normalized_filter_text(value: Any) -> str:
    return _clean_text(value).casefold()


def _safe_top_k(value: Any) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return 5
    return max(1, min(parsed, 100))


def _tokens(value: Any) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", _clean_text(value).casefold())
        if token
    }


def vector_evidence_retrieval_dry_run_safety_metadata() -> dict[str, bool]:
    safety = vector_evidence_contract.vector_evidence_contract_safety_metadata()
    safety.update(
        {
            "vector_evidence_retrieval_dry_run": True,
            "service_helper_added": False,
        }
    )
    return safety


def _candidate_input(
    *,
    indexing_dry_run_payload: dict[str, Any],
    chunk_candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    direct = _plain_list(chunk_candidates)
    if direct:
        return [_plain_dict(candidate) for candidate in direct]
    if indexing_dry_run_payload.get("dry_run_type") not in {
        "",
        "vector_evidence_indexing_dry_run",
    }:
        return []
    return [
        _plain_dict(candidate)
        for candidate in _plain_list(
            indexing_dry_run_payload.get("chunk_candidates")
        )
    ]


def _normalized_filters(
    *,
    filters: dict[str, Any],
    chunk_type: str,
    job_id: str,
    company: str,
    agent_name: str,
    stage: str,
) -> dict[str, str]:
    source = _plain_dict(filters)
    explicit = {
        "chunk_type": chunk_type,
        "job_id": job_id,
        "company": company,
        "agent_name": agent_name,
        "stage": stage,
    }
    normalized: dict[str, str] = {}
    for field in FILTER_FIELDS:
        value = explicit[field] if _clean_text(explicit[field]) else source.get(field)
        text = _clean_text(value)
        if text:
            normalized[field] = text
    return normalized


def _filter_mismatches(
    candidate: dict[str, Any],
    filters: dict[str, str],
) -> list[str]:
    metadata = _plain_dict(candidate.get("metadata"))
    mismatches: list[str] = []
    for field in FILTER_FIELDS:
        expected = filters.get(field)
        if not expected:
            continue
        actual = (
            candidate.get("chunk_type")
            if field == "chunk_type"
            else metadata.get(field)
        )
        if _normalized_filter_text(actual) != _normalized_filter_text(expected):
            mismatches.append(field)
    return mismatches


def _lexical_score(
    *,
    query_tokens: set[str],
    evidence_text: str,
) -> tuple[float, list[str], int]:
    evidence_tokens = _tokens(evidence_text)
    matched_tokens = sorted(query_tokens & evidence_tokens)
    if not query_tokens:
        return 0.0, [], len(evidence_tokens)
    score = len(matched_tokens) / len(query_tokens)
    return round(score, 6), matched_tokens, len(evidence_tokens)


def _base_payload(
    *,
    status: str,
    query: str,
    filters: dict[str, str],
    top_k: int,
) -> dict[str, Any]:
    return {
        "status": status,
        "dry_run_type": "vector_evidence_retrieval_dry_run",
        "contract_version": vector_evidence_contract.CONTRACT_VERSION,
        "dry_run_only": True,
        "retrieval_executed": False,
        "query": query,
        "filters": _snapshot(filters),
        "top_k": top_k,
        "matched_chunks": [],
        "match_count": 0,
        "skipped_reasons": [],
        "provider_backed_automated_agents": 0,
        "live_provider_backed_automated_agents": 0,
        "mutation_authorized_agents": 0,
        "evaluation_boundaries": {
            "prefilter_relevance": "separate_unchanged",
            "llm_shadow_evaluation": "separate_advisory_only",
            "final_application_scoring": "separate_unchanged",
            "retrieval_evidence_support": "lexical_retrieval_dry_run_only",
        },
        "safety_metadata": vector_evidence_retrieval_dry_run_safety_metadata(),
    }


def build_vector_evidence_retrieval_dry_run_payload(
    *,
    query_text: str,
    indexing_dry_run_payload: dict[str, Any] | None = None,
    chunk_candidates: list[dict[str, Any]] | None = None,
    filters: dict[str, Any] | None = None,
    chunk_type: str = "",
    job_id: str = "",
    company: str = "",
    agent_name: str = "",
    stage: str = "",
    top_k: int = 5,
) -> dict[str, Any]:
    """Return deterministic advisory matches over in-memory chunk candidates."""

    query = _clean_text(query_text)
    safe_top_k = _safe_top_k(top_k)
    normalized_filters = _normalized_filters(
        filters=_plain_dict(filters),
        chunk_type=chunk_type,
        job_id=job_id,
        company=company,
        agent_name=agent_name,
        stage=stage,
    )
    payload = _base_payload(
        status=STATUS_INVALID_QUERY if not query else STATUS_NO_RESULTS,
        query=query,
        filters=normalized_filters,
        top_k=safe_top_k,
    )

    request_contract = (
        vector_evidence_contract.build_vector_retrieval_request_contract(
            query_text=query,
            chunk_types=(
                [normalized_filters["chunk_type"]]
                if normalized_filters.get("chunk_type")
                else list(vector_evidence_contract.CHUNK_TYPES)
            ),
            metadata_filters=normalized_filters,
            top_k=safe_top_k,
            retrieval_enabled=True,
        )
    )
    payload["request_contract"] = request_contract
    if request_contract.get("status") == vector_evidence_contract.STATUS_INVALID_REQUEST:
        payload["status"] = STATUS_INVALID_QUERY
        payload["skipped_reasons"] = [
            {
                "chunk_id": "",
                "reason": error,
            }
            for error in request_contract.get("validation", {}).get("errors", [])
        ]
        return payload

    indexing_payload = _plain_dict(indexing_dry_run_payload)
    if indexing_payload and indexing_payload.get("status") == (
        vector_evidence_indexing_dry_run.STATUS_INVALID
    ):
        payload["skipped_reasons"].append(
            {"chunk_id": "", "reason": "invalid_indexing_dry_run_payload"}
        )

    candidates = _candidate_input(
        indexing_dry_run_payload=indexing_payload,
        chunk_candidates=_plain_list(chunk_candidates),
    )
    normalized = vector_evidence_contract.build_vector_evidence_chunk_candidates(
        candidates
    )
    query_tokens = _tokens(query)
    matches: list[dict[str, Any]] = []
    skipped_reasons: list[dict[str, Any]] = list(payload["skipped_reasons"])

    for invalid in normalized.get("invalid_chunks", []):
        item = _plain_dict(invalid)
        candidate = _plain_dict(item.get("chunk_candidate"))
        skipped_reasons.append(
            {
                "chunk_id": _clean_text(candidate.get("chunk_id")),
                "reason": "invalid_chunk_candidate",
            }
        )

    for candidate_value in normalized.get("chunk_candidates", []):
        candidate = _plain_dict(candidate_value)
        chunk_id_value = _clean_text(candidate.get("chunk_id"))
        mismatches = _filter_mismatches(candidate, normalized_filters)
        if mismatches:
            skipped_reasons.append(
                {
                    "chunk_id": chunk_id_value,
                    "reason": "metadata_filter_mismatch",
                    "fields": mismatches,
                }
            )
            continue

        score, matched_tokens, evidence_token_count = _lexical_score(
            query_tokens=query_tokens,
            evidence_text=_clean_text(candidate.get("evidence_text")),
        )
        if score <= 0:
            skipped_reasons.append(
                {
                    "chunk_id": chunk_id_value,
                    "reason": "no_lexical_overlap",
                }
            )
            continue

        matches.append(
            {
                **candidate,
                "retrieval_score": score,
                "retrieval_confidence": score,
                "matched_query_tokens": matched_tokens,
                "query_token_count": len(query_tokens),
                "evidence_token_count": evidence_token_count,
            }
        )

    ordered_matches = sorted(
        matches,
        key=lambda item: (
            -float(item.get("retrieval_score", 0.0)),
            _clean_text(item.get("chunk_type")),
            _clean_text(item.get("chunk_id")),
        ),
    )
    selected = ordered_matches[:safe_top_k]
    payload.update(
        {
            "status": STATUS_READY if selected else STATUS_NO_RESULTS,
            "matched_chunks": selected,
            "match_count": len(selected),
            "candidate_count": len(normalized.get("chunk_candidates", [])),
            "skipped_reasons": skipped_reasons,
            "fallback": {
                "used": not selected,
                "reason": "no_matching_vector_evidence" if not selected else "",
                "message": (
                    "No lexical evidence matched; continue without retrieval influence."
                    if not selected
                    else ""
                ),
            },
        }
    )
    return payload

