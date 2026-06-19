"""Default-off embedding-backed indexing helper for vector evidence.

Provider execution and database writes are separately gated and available only
through explicitly injected callables. This module opens no connection and has
no API, UI, or pipeline hook.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from src.agents import vector_evidence_contract
from src.storage.vector_evidence import embedding_provider, store


EMBEDDING_INDEXING_VERSION = "phase-9b-vector-evidence-embedding-indexing-v1"

STATUS_SKIPPED_DEFAULT_OFF = "embedding_indexing_skipped_default_off"
STATUS_NOT_CONFIGURED = "embedding_indexing_not_configured"
STATUS_INVALID_REQUEST = "embedding_indexing_invalid_request"
STATUS_PROVIDER_FAILED = "embedding_indexing_provider_failed_non_blocking"
STATUS_PREPARED = "embedding_indexing_prepared"
STATUS_WRITE_NOT_CONFIGURED = "embedding_indexing_write_not_configured"
STATUS_WRITTEN = "embedding_indexing_written"
STATUS_WRITE_FAILED = "embedding_indexing_write_failed_non_blocking"


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").split())


def _positive_int(value: Any) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return 0
    return parsed if parsed > 0 else 0


def embedding_indexing_safety_metadata(
    *,
    enabled: bool = False,
    provider_calls_made: bool = False,
    embeddings_created: bool = False,
    write_attempted: bool = False,
    did_write_database: bool = False,
) -> dict[str, bool]:
    return {
        "read_only": not bool(did_write_database),
        "advisory_only": True,
        "embedding_indexing_helper": True,
        "embedding_indexing_enabled": bool(enabled),
        "provider_calls_made": bool(provider_calls_made),
        "embeddings_created": bool(embeddings_created),
        "write_attempted": bool(write_attempted),
        "did_read_database": False,
        "did_write_database": bool(did_write_database),
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


def _base_payload(*, enabled: bool, write_enabled: bool) -> dict[str, Any]:
    return {
        "indexing_version": EMBEDDING_INDEXING_VERSION,
        "status": STATUS_SKIPPED_DEFAULT_OFF,
        "default_off": True,
        "embedding_indexing_enabled": bool(enabled),
        "write_enabled": bool(write_enabled),
        "write_attempted": False,
        "write_executed": False,
        "chunk_count": 0,
        "prepared_record_count": 0,
        "prepared_records": [],
        "write_results": [],
        "errors": [],
        "provider_backed_automated_agents": 0,
        "live_provider_backed_automated_agents": 0,
        "mutation_authorized_agents": 0,
        "mutation_authorized_scoring_agents": 0,
        "mutation_authorized_ranking_agents": 0,
        "mutation_authorized_application_agents": 0,
        "safety_metadata": embedding_indexing_safety_metadata(
            enabled=enabled,
        ),
    }


def _normalized_chunk(
    source: Any,
    *,
    run_id: str,
    job_id: str,
) -> tuple[dict[str, Any], list[str]]:
    chunk = deepcopy(source) if isinstance(source, dict) else {}
    metadata = (
        deepcopy(chunk.get("metadata"))
        if isinstance(chunk.get("metadata"), dict)
        else {}
    )
    chunk_id = _clean_text(chunk.get("chunk_id"))
    chunk_type = _clean_text(chunk.get("chunk_type"))
    evidence_text = _clean_text(
        chunk.get("evidence_text")
        or chunk.get("normalized_text")
        or chunk.get("text")
    )
    errors: list[str] = []
    if not chunk_id:
        errors.append("chunk_id_required")
    if not chunk_type:
        errors.append("chunk_type_required")
    elif chunk_type not in vector_evidence_contract.CHUNK_TYPES:
        errors.append("unsupported_chunk_type")
    if not evidence_text:
        errors.append("chunk_text_required")
    metadata_run_id = _clean_text(metadata.get("run_id"))
    metadata_job_id = _clean_text(metadata.get("job_id"))
    if metadata_run_id and metadata_run_id != run_id:
        errors.append("chunk_run_id_mismatch")
    if metadata_job_id and metadata_job_id != job_id:
        errors.append("chunk_job_id_mismatch")
    metadata["run_id"] = run_id
    metadata["job_id"] = job_id
    metadata["read_only"] = True
    return {
        "chunk_id": chunk_id,
        "chunk_type": chunk_type,
        "evidence_text": evidence_text,
        "metadata": metadata,
        "embedding": None,
    }, errors


def run_vector_evidence_embedding_indexing(
    *,
    enabled: bool = False,
    chunks: list[dict[str, Any]] | None = None,
    owner_user_id: str = "",
    run_id: str = "",
    job_id: str = "",
    embedding_model_id: str = "",
    expected_dimension: int = 0,
    provider: Callable[[dict[str, Any]], Any] | None = None,
    write_enabled: bool = False,
    db_executor: Any = None,
    embedding_provider_module: Any = None,
    store_module: Any = None,
) -> dict[str, Any]:
    """Prepare embedding-backed chunk records and optionally write them."""

    payload = _base_payload(
        enabled=enabled is True,
        write_enabled=write_enabled is True,
    )
    if enabled is not True:
        return payload
    if not callable(provider):
        payload["status"] = STATUS_NOT_CONFIGURED
        payload["errors"] = ["injected_provider_required"]
        return payload

    owner = _clean_text(owner_user_id)
    safe_run_id = _clean_text(run_id)
    safe_job_id = _clean_text(job_id)
    model_id = _clean_text(embedding_model_id)
    dimension = _positive_int(expected_dimension)
    source_chunks = deepcopy(chunks) if isinstance(chunks, list) else []
    request_errors: list[str] = []
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
    if not source_chunks:
        request_errors.append("chunks_required")
    if request_errors:
        payload["status"] = STATUS_INVALID_REQUEST
        payload["errors"] = request_errors
        return payload

    normalized_chunks: list[dict[str, Any]] = []
    for index, source in enumerate(source_chunks):
        chunk, errors = _normalized_chunk(
            source,
            run_id=safe_run_id,
            job_id=safe_job_id,
        )
        if errors:
            payload["status"] = STATUS_INVALID_REQUEST
            payload["errors"] = [
                f"chunk_{index}:{error}" for error in errors
            ]
            return payload
        normalized_chunks.append(chunk)

    provider_module = embedding_provider_module or embedding_provider
    storage_module = store_module or store
    prepared_records: list[dict[str, Any]] = []
    provider_calls_made = False
    embeddings_created = False
    for chunk in normalized_chunks:
        provider_payload = provider_module.run_vector_evidence_embedding_provider(
            enabled=True,
            text=chunk["evidence_text"],
            embedding_model_id=model_id,
            expected_dimension=dimension,
            request_id=f"{safe_run_id}:{chunk['chunk_id']}",
            provider=provider,
        )
        provider_safety = provider_payload.get("safety_metadata")
        if isinstance(provider_safety, dict):
            provider_calls_made = bool(
                provider_calls_made
                or provider_safety.get("provider_calls_made")
            )
            embeddings_created = bool(
                embeddings_created
                or provider_safety.get("embeddings_created")
            )
        if provider_payload.get("status") != embedding_provider.STATUS_READY:
            payload.update(
                {
                    "status": STATUS_PROVIDER_FAILED,
                    "errors": list(provider_payload.get("errors", []) or []),
                    "safety_metadata": embedding_indexing_safety_metadata(
                        enabled=True,
                        provider_calls_made=provider_calls_made,
                        embeddings_created=embeddings_created,
                    ),
                }
            )
            return payload
        try:
            prepared_chunk = (
                storage_module.prepare_vector_evidence_chunk_insert_payload(
                    chunk,
                    owner_user_id=owner,
                )
            )
            prepared_embedding = (
                storage_module.prepare_vector_evidence_embedding_insert_payload(
                    chunk_id=chunk["chunk_id"],
                    embedding=provider_payload["embedding"],
                    embedding_model_id=model_id,
                )
            )
        except Exception as exc:
            payload.update(
                {
                    "status": STATUS_INVALID_REQUEST,
                    "errors": [exc.__class__.__name__, str(exc)],
                    "safety_metadata": embedding_indexing_safety_metadata(
                        enabled=True,
                        provider_calls_made=provider_calls_made,
                        embeddings_created=embeddings_created,
                    ),
                }
            )
            return payload
        prepared_records.append(
            {
                "chunk": deepcopy(chunk),
                "embedding": list(provider_payload["embedding"]),
                "embedding_dimension": int(
                    provider_payload["embedding_dimension"]
                ),
                "embedding_model_id": model_id,
                "prepared_chunk_insert": prepared_chunk,
                "prepared_embedding_insert": prepared_embedding,
            }
        )

    payload.update(
        {
            "status": STATUS_PREPARED,
            "chunk_count": len(normalized_chunks),
            "prepared_record_count": len(prepared_records),
            "prepared_records": prepared_records,
            "safety_metadata": embedding_indexing_safety_metadata(
                enabled=True,
                provider_calls_made=provider_calls_made,
                embeddings_created=embeddings_created,
            ),
        }
    )
    if write_enabled is not True:
        return payload

    payload["write_attempted"] = True
    if db_executor is None:
        payload["status"] = STATUS_WRITE_NOT_CONFIGURED
        payload["errors"] = ["injected_db_executor_required"]
        payload["safety_metadata"] = embedding_indexing_safety_metadata(
            enabled=True,
            provider_calls_made=provider_calls_made,
            embeddings_created=embeddings_created,
            write_attempted=True,
        )
        return payload

    write_results: list[dict[str, Any]] = []
    try:
        for record in prepared_records:
            chunk_result = storage_module.execute_vector_evidence_chunk_insert(
                record["prepared_chunk_insert"],
                db_executor=db_executor,
            )
            embedding_result = (
                storage_module.execute_vector_evidence_embedding_insert(
                    record["prepared_embedding_insert"],
                    db_executor=db_executor,
                )
            )
            write_results.append(
                {
                    "chunk_insert": chunk_result,
                    "embedding_insert": embedding_result,
                }
            )
    except Exception as exc:
        payload.update(
            {
                "status": STATUS_WRITE_FAILED,
                "write_results": write_results,
                "errors": [exc.__class__.__name__],
                "safety_metadata": embedding_indexing_safety_metadata(
                    enabled=True,
                    provider_calls_made=provider_calls_made,
                    embeddings_created=embeddings_created,
                    write_attempted=True,
                    did_write_database=bool(write_results),
                ),
            }
        )
        return payload

    write_executed = bool(write_results) and all(
        result["chunk_insert"].get("executed") is True
        and result["embedding_insert"].get("executed") is True
        for result in write_results
    )
    payload.update(
        {
            "status": STATUS_WRITTEN if write_executed else STATUS_WRITE_FAILED,
            "write_executed": write_executed,
            "write_results": write_results,
            "safety_metadata": embedding_indexing_safety_metadata(
                enabled=True,
                provider_calls_made=provider_calls_made,
                embeddings_created=embeddings_created,
                write_attempted=True,
                did_write_database=write_executed,
            ),
        }
    )
    return payload
