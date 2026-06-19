"""Default-off embedding-backed retrieval helper for vector evidence.

Query embedding and database reads are separately gated and available only
through explicitly injected callables. This module opens no connection, writes
no records, and has no API, UI, or pipeline hook.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from src.agents import vector_evidence_contract
from src.storage.vector_evidence import embedding_provider, store


EMBEDDING_RETRIEVAL_VERSION = "phase-9c-vector-evidence-embedding-retrieval-v1"

STATUS_SKIPPED_DEFAULT_OFF = "embedding_retrieval_skipped_default_off"
STATUS_NOT_CONFIGURED = "embedding_retrieval_not_configured"
STATUS_INVALID_REQUEST = "embedding_retrieval_invalid_request"
STATUS_PROVIDER_FAILED = "embedding_retrieval_provider_failed_non_blocking"
STATUS_PREPARED = "embedding_retrieval_prepared"
STATUS_READ_NOT_CONFIGURED = "embedding_retrieval_read_not_configured"
STATUS_COMPLETED = "embedding_retrieval_completed"
STATUS_READ_FAILED = "embedding_retrieval_read_failed_non_blocking"

FILTER_FIELDS = ("chunk_type", "job_id", "company", "stage", "agent_name")


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").split())


def _positive_int(value: Any, *, default: int = 0, maximum: int = 100) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    if parsed < 1:
        return default
    return min(parsed, maximum)


def _normalized_filters(
    filters: dict[str, Any] | None,
    *,
    job_id: str,
) -> tuple[dict[str, str], list[str]]:
    source = deepcopy(filters) if isinstance(filters, dict) else {}
    normalized: dict[str, str] = {}
    errors: list[str] = []
    for field in FILTER_FIELDS:
        value = job_id if field == "job_id" else source.get(field)
        text = _clean_text(value)
        if text:
            normalized[field] = text
    chunk_type = normalized.get("chunk_type")
    if chunk_type and chunk_type not in vector_evidence_contract.CHUNK_TYPES:
        errors.append("unsupported_chunk_type_filter")
    source_job_id = _clean_text(source.get("job_id"))
    if source_job_id and source_job_id != job_id:
        errors.append("job_id_filter_mismatch")
    return normalized, errors


def embedding_retrieval_safety_metadata(
    *,
    enabled: bool = False,
    provider_calls_made: bool = False,
    embeddings_created: bool = False,
    read_attempted: bool = False,
    did_read_database: bool = False,
) -> dict[str, bool]:
    return {
        "read_only": True,
        "advisory_only": True,
        "embedding_retrieval_helper": True,
        "embedding_retrieval_enabled": bool(enabled),
        "provider_calls_made": bool(provider_calls_made),
        "embeddings_created": bool(embeddings_created),
        "read_attempted": bool(read_attempted),
        "did_read_database": bool(did_read_database),
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


def _base_payload(*, enabled: bool, read_enabled: bool) -> dict[str, Any]:
    return {
        "retrieval_version": EMBEDDING_RETRIEVAL_VERSION,
        "status": STATUS_SKIPPED_DEFAULT_OFF,
        "default_off": True,
        "embedding_retrieval_enabled": bool(enabled),
        "read_enabled": bool(read_enabled),
        "read_attempted": False,
        "read_executed": False,
        "query_embedding": [],
        "embedding_dimension": 0,
        "prepared_retrieval": {},
        "retrieval_candidates": [],
        "result_count": 0,
        "errors": [],
        "provider_backed_automated_agents": 0,
        "live_provider_backed_automated_agents": 0,
        "mutation_authorized_agents": 0,
        "mutation_authorized_scoring_agents": 0,
        "mutation_authorized_ranking_agents": 0,
        "mutation_authorized_application_agents": 0,
        "safety_metadata": embedding_retrieval_safety_metadata(
            enabled=enabled,
        ),
    }


def run_vector_evidence_embedding_retrieval(
    *,
    enabled: bool = False,
    query_text: str = "",
    owner_user_id: str = "",
    run_id: str = "",
    job_id: str = "",
    embedding_model_id: str = "",
    expected_dimension: int = 0,
    top_k: int = 5,
    filters: dict[str, Any] | None = None,
    provider: Callable[[dict[str, Any]], Any] | None = None,
    read_enabled: bool = False,
    db_executor: Any = None,
    embedding_provider_module: Any = None,
    store_module: Any = None,
) -> dict[str, Any]:
    """Prepare a semantic query and optionally read candidates."""

    payload = _base_payload(
        enabled=enabled is True,
        read_enabled=read_enabled is True,
    )
    if enabled is not True:
        return payload
    if not callable(provider):
        payload["status"] = STATUS_NOT_CONFIGURED
        payload["errors"] = ["injected_provider_required"]
        return payload

    query = _clean_text(query_text)
    owner = _clean_text(owner_user_id)
    safe_run_id = _clean_text(run_id)
    safe_job_id = _clean_text(job_id)
    model_id = _clean_text(embedding_model_id)
    dimension = _positive_int(expected_dimension)
    safe_top_k = _positive_int(top_k, default=5)
    normalized_filters, filter_errors = _normalized_filters(
        filters,
        job_id=safe_job_id,
    )
    request_errors: list[str] = []
    if not query:
        request_errors.append("query_text_required")
    if not owner:
        request_errors.append("owner_user_id_required")
    if not safe_run_id:
        request_errors.append("run_id_required")
    if not safe_job_id:
        request_errors.append("job_id_required")
    if not model_id:
        request_errors.append("embedding_model_id_required")
    if not dimension:
        request_errors.append("expected_dimension_required")
    request_errors.extend(filter_errors)
    if request_errors:
        payload["status"] = STATUS_INVALID_REQUEST
        payload["errors"] = request_errors
        return payload

    provider_module = embedding_provider_module or embedding_provider
    storage_module = store_module or store
    provider_payload = provider_module.run_vector_evidence_embedding_provider(
        enabled=True,
        text=query,
        embedding_model_id=model_id,
        expected_dimension=dimension,
        request_id=f"{safe_run_id}:{safe_job_id}:retrieval",
        provider=provider,
    )
    provider_safety = provider_payload.get("safety_metadata")
    provider_safety = provider_safety if isinstance(provider_safety, dict) else {}
    provider_calls_made = bool(provider_safety.get("provider_calls_made"))
    embeddings_created = bool(provider_safety.get("embeddings_created"))
    if provider_payload.get("status") != embedding_provider.STATUS_READY:
        payload.update(
            {
                "status": STATUS_PROVIDER_FAILED,
                "errors": list(provider_payload.get("errors", []) or []),
                "safety_metadata": embedding_retrieval_safety_metadata(
                    enabled=True,
                    provider_calls_made=provider_calls_made,
                    embeddings_created=embeddings_created,
                ),
            }
        )
        return payload

    try:
        prepared = storage_module.prepare_vector_evidence_retrieval_select_payload(
            owner_user_id=owner,
            query_embedding=provider_payload["embedding"],
            embedding_model_id=model_id,
            filters=normalized_filters,
            top_k=safe_top_k,
        )
    except Exception as exc:
        payload.update(
            {
                "status": STATUS_INVALID_REQUEST,
                "errors": [exc.__class__.__name__, str(exc)],
                "safety_metadata": embedding_retrieval_safety_metadata(
                    enabled=True,
                    provider_calls_made=provider_calls_made,
                    embeddings_created=embeddings_created,
                ),
            }
        )
        return payload

    payload.update(
        {
            "status": STATUS_PREPARED,
            "query": query,
            "run_id": safe_run_id,
            "job_id": safe_job_id,
            "filters": normalized_filters,
            "top_k": safe_top_k,
            "query_embedding": list(provider_payload["embedding"]),
            "embedding_dimension": int(
                provider_payload["embedding_dimension"]
            ),
            "embedding_model_id": model_id,
            "prepared_retrieval": prepared,
            "safety_metadata": embedding_retrieval_safety_metadata(
                enabled=True,
                provider_calls_made=provider_calls_made,
                embeddings_created=embeddings_created,
            ),
        }
    )
    if read_enabled is not True:
        return payload

    payload["read_attempted"] = True
    if db_executor is None:
        payload["status"] = STATUS_READ_NOT_CONFIGURED
        payload["errors"] = ["injected_db_executor_required"]
        payload["safety_metadata"] = embedding_retrieval_safety_metadata(
            enabled=True,
            provider_calls_made=provider_calls_made,
            embeddings_created=embeddings_created,
            read_attempted=True,
        )
        return payload

    try:
        result = storage_module.select_vector_evidence_retrieval_candidates(
            prepared,
            db_executor=db_executor,
        )
    except Exception as exc:
        payload.update(
            {
                "status": STATUS_READ_FAILED,
                "errors": [exc.__class__.__name__],
                "safety_metadata": embedding_retrieval_safety_metadata(
                    enabled=True,
                    provider_calls_made=provider_calls_made,
                    embeddings_created=embeddings_created,
                    read_attempted=True,
                    did_read_database=False,
                ),
            }
        )
        return payload

    executed = result.get("executed") is True
    candidates = [
        deepcopy(candidate)
        for candidate in result.get("retrieval_candidates", [])
        if isinstance(candidate, dict)
    ]
    payload.update(
        {
            "status": STATUS_COMPLETED if executed else STATUS_READ_FAILED,
            "read_executed": executed,
            "retrieval_candidates": candidates,
            "result_count": len(candidates),
            "read_result": result,
            "safety_metadata": embedding_retrieval_safety_metadata(
                enabled=True,
                provider_calls_made=provider_calls_made,
                embeddings_created=embeddings_created,
                read_attempted=True,
                did_read_database=executed,
            ),
        }
    )
    return payload
