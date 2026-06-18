"""Explicit local smoke helper for the vector evidence pgvector path.

Nothing runs on import. The smoke requires an explicit enable flag, owner
scope, database configuration, and connector. It creates no embeddings, calls
no model provider, commits no transaction, and has no API, UI, or pipeline
hook.
"""

from __future__ import annotations

from hashlib import sha256
from typing import Any, Mapping

from src.storage.vector_evidence import connection, store


SMOKE_VERSION = "phase-8t-pgvector-local-smoke-v1"


def pgvector_local_smoke_safety_metadata(
    *,
    connection_opened: bool = False,
    schema_setup_executed: bool = False,
    chunks_written: bool = False,
    retrieval_events_written: bool = False,
) -> dict[str, bool]:
    return {
        "read_only": not bool(
            schema_setup_executed
            or chunks_written
            or retrieval_events_written
        ),
        "advisory_only": True,
        "pgvector_local_smoke": True,
        "operator_triggered_only": True,
        "default_off": True,
        "db_connection_opened": bool(connection_opened),
        "db_executor_created": bool(connection_opened),
        "schema_setup_executed": bool(schema_setup_executed),
        "chunks_written": bool(chunks_written),
        "embeddings_written": False,
        "retrieval_events_written": bool(retrieval_events_written),
        "embeddings_created": False,
        "provider_calls_made": False,
        "did_read_database": False,
        "did_write_database": bool(
            schema_setup_executed
            or chunks_written
            or retrieval_events_written
        ),
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
        "pipeline_stage_added": False,
        "auto_apply_enabled": False,
        "mutation_authorized": False,
    }


def _base_payload(status: str) -> dict[str, Any]:
    return {
        "smoke_version": SMOKE_VERSION,
        "status": status,
        "enabled": False,
        "default_off": True,
        "connection_provider_used": False,
        "db_connection_opened": False,
        "db_executor_created": False,
        "schema_setup_executed": False,
        "chunk_insert_executed": False,
        "retrieval_event_insert_executed": False,
        "operations_attempted": [],
        "operations_completed": [],
        "errors": [],
        "provider_backed_automated_agents": 0,
        "live_provider_backed_automated_agents": 0,
        "mutation_authorized_agents": 0,
        "mutation_authorized_scoring_agents": 0,
        "mutation_authorized_ranking_agents": 0,
        "mutation_authorized_application_agents": 0,
        "safety_metadata": pgvector_local_smoke_safety_metadata(),
    }


def _smoke_chunk(owner_user_id: str) -> dict[str, Any]:
    metadata = {
        "job_id": "pgvector-local-smoke-job",
        "company": "ApplyLens Local Smoke",
        "title": "Vector Evidence Smoke",
        "source": "operator_local_smoke",
        "stage": "pgvector_local_smoke",
        "agent_name": "none",
        "trace_id": "pgvector-local-smoke",
        "run_id": "pgvector-local-smoke",
        "resume_version": "",
        "profile_version": "",
        "created_at": "",
        "read_only": True,
    }
    return {
        "chunk_id": (
            "vector-evidence:pgvector-local-smoke:"
            + sha256(owner_user_id.encode("utf-8")).hexdigest()[:16]
        ),
        "chunk_type": "job_description",
        "evidence_text": "Explicit local pgvector smoke evidence.",
        "metadata": metadata,
        "embedding": None,
    }


def run_vector_evidence_pgvector_smoke(
    *,
    enabled: bool = False,
    owner_user_id: str = "",
    database_url: str = "",
    environ: Mapping[str, str] | None = None,
    connector: Any = None,
    connection_module: Any = None,
    store_module: Any = None,
) -> dict[str, Any]:
    """Exercise schema, chunk, and retrieval-event paths when explicitly run."""

    payload = _base_payload("pgvector_local_smoke_skipped_default_off")
    if enabled is not True:
        return payload
    payload["enabled"] = True

    safe_owner_user_id = str(owner_user_id or "").strip()
    if not safe_owner_user_id:
        payload["status"] = "pgvector_local_smoke_missing_owner"
        payload["errors"] = ["owner_user_id_required"]
        return payload
    if connector is None:
        payload["status"] = "pgvector_local_smoke_connector_not_configured"
        payload["errors"] = ["explicit_connector_required"]
        return payload

    provider_module = connection_module or connection
    storage_module = store_module or store
    provider_payload = provider_module.build_vector_evidence_db_executor(
        enabled=True,
        database_url=str(database_url or ""),
        environ=environ,
        connector=connector,
    )
    db_executor = (
        provider_payload.get("db_executor")
        if isinstance(provider_payload, dict)
        else None
    )
    payload["connection_provider_used"] = db_executor is not None
    payload["db_connection_opened"] = bool(
        isinstance(provider_payload, dict)
        and provider_payload.get("db_connection_opened")
    )
    payload["db_executor_created"] = bool(
        isinstance(provider_payload, dict)
        and provider_payload.get("db_executor_created")
    )
    if db_executor is None:
        payload["status"] = str(
            (
                provider_payload.get("status")
                if isinstance(provider_payload, dict)
                else ""
            )
            or "pgvector_local_smoke_not_configured"
        )
        provider_error = (
            str(provider_payload.get("error", "") or "")
            if isinstance(provider_payload, dict)
            else ""
        )
        payload["errors"] = [provider_error] if provider_error else []
        return payload

    schema_executed = False
    chunk_executed = False
    event_executed = False
    try:
        payload["operations_attempted"].append("schema_setup")
        schema_result = storage_module.execute_pgvector_schema_setup(
            db_executor=db_executor
        )
        schema_executed = schema_result.get("executed") is True
        if schema_executed:
            payload["operations_completed"].append("schema_setup")

        chunk_payload = storage_module.prepare_chunk_insert_payload(
            _smoke_chunk(safe_owner_user_id),
            owner_user_id=safe_owner_user_id,
            source_record_id="pgvector-local-smoke",
        )
        payload["operations_attempted"].append("chunk_insert")
        chunk_result = storage_module.execute_vector_evidence_chunk_insert(
            chunk_payload,
            db_executor=db_executor,
        )
        chunk_executed = chunk_result.get("executed") is True
        if chunk_executed:
            payload["operations_completed"].append("chunk_insert")

        event_payload = storage_module.prepare_retrieval_event_insert_payload(
            {
                "owner_user_id": safe_owner_user_id,
                "request_id": "pgvector-local-smoke",
                "query_hash": sha256(
                    b"explicit local pgvector smoke query"
                ).hexdigest(),
                "query_purpose": "pgvector_local_smoke",
                "chunk_type": "job_description",
                "metadata": {"operator_triggered": True},
                "job_id": "pgvector-local-smoke-job",
                "stage": "pgvector_local_smoke",
                "agent_name": "none",
                "top_k": 1,
                "result_count": 0,
                "backend_status": "pgvector_local_smoke",
            }
        )
        payload["operations_attempted"].append("retrieval_event_insert")
        event_result = (
            storage_module.execute_vector_evidence_retrieval_event_insert(
                event_payload,
                db_executor=db_executor,
            )
        )
        event_executed = event_result.get("executed") is True
        if event_executed:
            payload["operations_completed"].append(
                "retrieval_event_insert"
            )
    except Exception as exc:
        payload["status"] = "pgvector_local_smoke_failed_non_blocking"
        payload["errors"] = [type(exc).__name__]
    finally:
        if not callable(db_executor):
            close_connection = getattr(db_executor, "close", None)
            if callable(close_connection):
                try:
                    close_connection()
                except Exception:
                    pass

    payload.update(
        {
            "status": (
                "pgvector_local_smoke_completed"
                if schema_executed and chunk_executed and event_executed
                else payload["status"]
            ),
            "schema_setup_executed": schema_executed,
            "chunk_insert_executed": chunk_executed,
            "retrieval_event_insert_executed": event_executed,
            "safety_metadata": pgvector_local_smoke_safety_metadata(
                connection_opened=payload["db_connection_opened"],
                schema_setup_executed=schema_executed,
                chunks_written=chunk_executed,
                retrieval_events_written=event_executed,
            ),
        }
    )
    return payload
