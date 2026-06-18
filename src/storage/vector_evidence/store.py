"""Default-off pgvector storage adapter for vector evidence.

The module prepares deterministic rows and parameterized SQL only. It imports
no database driver, opens no connection, creates no embedding, calls no
provider, and is not wired into pipeline, API, service, UI, or startup code.
An optional caller-supplied executor is the only execution boundary.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
import math
from pathlib import Path
from typing import Any, Callable

from src.agents import vector_evidence_contract


DEFAULT_SCHEMA_SQL_PATH = Path("src/storage/vector_evidence/schema.sql")
STORE_ADAPTER_VERSION = "phase-8n-pgvector-store-adapter-v1"

PreparedExecutor = Callable[[dict[str, Any]], Any]

_PROVENANCE_FIELDS = (
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
)


def pgvector_store_safety_metadata() -> dict[str, bool]:
    return {
        "read_only": True,
        "advisory_only": True,
        "pgvector_schema_defined": True,
        "pgvector_store_adapter": True,
        "pgvector_installed_by_app": False,
        "schema_created": False,
        "migration_created": False,
        "embeddings_created": False,
        "provider_calls_made": False,
        "vector_db_connected": False,
        "did_read_database": False,
        "did_write_database": False,
        "pipeline_stage_added": False,
        "scoring_mutation": False,
        "ranking_mutation": False,
        "queue_mutation": False,
        "application_submission": False,
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
        "mutation_authorized": False,
    }


def pgvector_schema_sql_text(
    schema_path: Path = DEFAULT_SCHEMA_SQL_PATH,
) -> str:
    path = Path(schema_path)
    if not path.exists():
        raise ValueError(f"Missing vector evidence schema SQL file: {path}")
    sql = path.read_text(encoding="utf-8")
    if not sql.strip():
        raise ValueError(f"Vector evidence schema SQL file is empty: {path}")
    return sql


def pgvector_store_table_specs() -> dict[str, dict[str, Any]]:
    return {
        "vector_evidence_chunks": {
            "primary_key": ["chunk_id"],
            "owner_column": "owner_user_id",
        },
        "vector_evidence_embeddings": {
            "primary_key": [
                "chunk_id",
                "embedding_model_id",
                "embedding_dimension",
                "embedding_content_hash",
            ],
            "foreign_keys": {
                "chunk_id": "vector_evidence_chunks.chunk_id",
            },
        },
        "vector_evidence_retrieval_events": {
            "primary_key": ["retrieval_event_id"],
            "owner_column": "owner_user_id",
        },
    }


def _snapshot(value: Any) -> Any:
    return deepcopy(value)


def _plain_dict(value: Any) -> dict[str, Any]:
    return _snapshot(value) if isinstance(value, dict) else {}


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").split())


def _require_text(value: Any, field_name: str) -> str:
    text = _clean_text(value)
    if not text:
        raise ValueError(f"{field_name} is required.")
    return text


def _positive_int(value: Any, field_name: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a positive integer.") from exc
    if parsed < 1:
        raise ValueError(f"{field_name} must be a positive integer.")
    return parsed


def _nonnegative_int(value: Any, field_name: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a nonnegative integer.") from exc
    if parsed < 0:
        raise ValueError(f"{field_name} must be a nonnegative integer.")
    return parsed


def _json_compact(value: Any) -> str:
    return json.dumps(
        value if value is not None else {},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def _prepared_payload(
    *,
    operation: str,
    table: str,
    row: dict[str, Any],
    sql: str,
    params: tuple[Any, ...],
) -> dict[str, Any]:
    return {
        "adapter_version": STORE_ADAPTER_VERSION,
        "status": "pgvector_store_payload_prepared",
        "default_off": True,
        "operation": operation,
        "table": table,
        "row": _snapshot(row),
        "sql": sql.strip(),
        "params": params,
        "provider_backed_automated_agents": 0,
        "live_provider_backed_automated_agents": 0,
        "mutation_authorized_agents": 0,
        "mutation_authorized_scoring_agents": 0,
        "mutation_authorized_ranking_agents": 0,
        "mutation_authorized_application_agents": 0,
        "safety_metadata": pgvector_store_safety_metadata(),
    }


def prepare_vector_evidence_chunk_insert_payload(
    chunk: dict[str, Any],
    *,
    owner_user_id: str,
    chunk_version: int = 1,
    source_record_id: str = "",
    source_updated_at: str = "",
) -> dict[str, Any]:
    """Prepare one owner-scoped chunk upsert from a Phase 8B contract chunk."""

    source = _plain_dict(chunk)
    metadata = _plain_dict(source.get("metadata"))
    chunk_type = _require_text(source.get("chunk_type"), "chunk_type")
    if chunk_type not in vector_evidence_contract.CHUNK_TYPES:
        raise ValueError(f"unsupported chunk_type: {chunk_type}")
    normalized_text = _require_text(
        source.get("evidence_text") or source.get("normalized_text"),
        "evidence_text",
    )
    if source.get("embedding") not in (None, [], ()):
        raise ValueError("chunk payload must not include an embedding.")

    row = {
        "chunk_id": _require_text(source.get("chunk_id"), "chunk_id"),
        "owner_user_id": _require_text(owner_user_id, "owner_user_id"),
        "chunk_type": chunk_type,
        "chunk_version": _positive_int(chunk_version, "chunk_version"),
        "content_hash": sha256(normalized_text.encode("utf-8")).hexdigest(),
        "normalized_text": normalized_text,
        "metadata": metadata,
        **{
            field: _clean_text(metadata.get(field))
            for field in _PROVENANCE_FIELDS
        },
        "source_record_id": _clean_text(source_record_id),
        "source_updated_at": _clean_text(source_updated_at) or None,
    }
    sql = """
INSERT INTO vector_evidence_chunks (
    chunk_id,
    owner_user_id,
    chunk_type,
    chunk_version,
    content_hash,
    normalized_text,
    metadata_json,
    job_id,
    company,
    title,
    source,
    stage,
    agent_name,
    trace_id,
    run_id,
    resume_version,
    profile_version,
    source_record_id,
    source_updated_at
)
VALUES (
    %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s,
    %s, %s, %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (chunk_id) DO UPDATE SET
    chunk_type = EXCLUDED.chunk_type,
    chunk_version = EXCLUDED.chunk_version,
    content_hash = EXCLUDED.content_hash,
    normalized_text = EXCLUDED.normalized_text,
    metadata_json = EXCLUDED.metadata_json,
    job_id = EXCLUDED.job_id,
    company = EXCLUDED.company,
    title = EXCLUDED.title,
    source = EXCLUDED.source,
    stage = EXCLUDED.stage,
    agent_name = EXCLUDED.agent_name,
    trace_id = EXCLUDED.trace_id,
    run_id = EXCLUDED.run_id,
    resume_version = EXCLUDED.resume_version,
    profile_version = EXCLUDED.profile_version,
    source_record_id = EXCLUDED.source_record_id,
    source_updated_at = EXCLUDED.source_updated_at,
    updated_at = NOW(),
    deleted_at = NULL
RETURNING chunk_id
"""
    params = (
        row["chunk_id"],
        row["owner_user_id"],
        row["chunk_type"],
        row["chunk_version"],
        row["content_hash"],
        row["normalized_text"],
        _json_compact(row["metadata"]),
        *[row[field] for field in _PROVENANCE_FIELDS],
        row["source_record_id"],
        row["source_updated_at"],
    )
    return _prepared_payload(
        operation="prepare_vector_evidence_chunk_insert",
        table="vector_evidence_chunks",
        row=row,
        sql=sql,
        params=params,
    )


def _normalized_embedding(embedding: Any) -> list[float]:
    if not isinstance(embedding, (list, tuple)) or not embedding:
        raise ValueError("embedding must be a non-empty explicit vector.")
    normalized: list[float] = []
    for value in embedding:
        try:
            parsed = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("embedding values must be finite numbers.") from exc
        if not math.isfinite(parsed):
            raise ValueError("embedding values must be finite numbers.")
        normalized.append(parsed)
    return normalized


def prepare_vector_evidence_embedding_insert_payload(
    *,
    chunk_id: str,
    embedding: list[float] | tuple[float, ...],
    embedding_model_id: str,
    embedding_content_hash: str = "",
) -> dict[str, Any]:
    """Prepare an embedding upsert from an explicitly supplied vector only."""

    normalized = _normalized_embedding(embedding)
    vector_text = "[" + ",".join(format(value, ".17g") for value in normalized) + "]"
    row = {
        "chunk_id": _require_text(chunk_id, "chunk_id"),
        "embedding_model_id": _require_text(
            embedding_model_id,
            "embedding_model_id",
        ),
        "embedding_dimension": len(normalized),
        "embedding": normalized,
        "embedding_content_hash": (
            _clean_text(embedding_content_hash)
            or sha256(vector_text.encode("utf-8")).hexdigest()
        ),
    }
    sql = """
INSERT INTO vector_evidence_embeddings (
    chunk_id,
    embedding_model_id,
    embedding_dimension,
    embedding,
    embedding_content_hash
)
VALUES (%s, %s, %s, %s::vector, %s)
ON CONFLICT (
    chunk_id,
    embedding_model_id,
    embedding_dimension,
    embedding_content_hash
) DO UPDATE SET
    embedding = EXCLUDED.embedding,
    updated_at = NOW(),
    deleted_at = NULL
RETURNING chunk_id
"""
    params = (
        row["chunk_id"],
        row["embedding_model_id"],
        row["embedding_dimension"],
        vector_text,
        row["embedding_content_hash"],
    )
    return _prepared_payload(
        operation="prepare_vector_evidence_embedding_insert",
        table="vector_evidence_embeddings",
        row=row,
        sql=sql,
        params=params,
    )


def prepare_vector_evidence_retrieval_event_insert_payload(
    event: dict[str, Any],
) -> dict[str, Any]:
    """Prepare privacy-minimized retrieval telemetry without raw query text."""

    source = _plain_dict(event)
    if _clean_text(source.get("query_text")):
        raise ValueError("query_text must not be stored; supply query_hash.")
    metadata = _plain_dict(source.get("metadata"))
    owner_user_id = _require_text(source.get("owner_user_id"), "owner_user_id")
    request_id = _clean_text(source.get("request_id"))
    query_hash = _clean_text(source.get("query_hash"))
    identity = "\x1f".join(
        (
            owner_user_id,
            request_id,
            query_hash,
            _clean_text(source.get("query_purpose")),
            _clean_text(source.get("run_id")),
        )
    )
    row = {
        "retrieval_event_id": (
            _clean_text(source.get("retrieval_event_id"))
            or f"vector-retrieval:{sha256(identity.encode('utf-8')).hexdigest()[:24]}"
        ),
        "owner_user_id": owner_user_id,
        "request_id": request_id,
        "query_hash": query_hash,
        "query_purpose": _clean_text(source.get("query_purpose")),
        "chunk_type": _clean_text(source.get("chunk_type")),
        "metadata": metadata,
        "job_id": _clean_text(source.get("job_id")),
        "company": _clean_text(source.get("company")),
        "stage": _clean_text(source.get("stage")),
        "agent_name": _clean_text(source.get("agent_name")),
        "trace_id": _clean_text(source.get("trace_id")),
        "run_id": _clean_text(source.get("run_id")),
        "embedding_model_id": _clean_text(source.get("embedding_model_id")),
        "embedding_dimension": (
            _positive_int(source.get("embedding_dimension"), "embedding_dimension")
            if source.get("embedding_dimension") not in (None, "")
            else None
        ),
        "top_k": _positive_int(source.get("top_k"), "top_k"),
        "result_count": _nonnegative_int(
            source.get("result_count", 0),
            "result_count",
        ),
        "fallback_reason": _clean_text(source.get("fallback_reason")),
        "latency_ms": (
            _nonnegative_int(source.get("latency_ms"), "latency_ms")
            if source.get("latency_ms") not in (None, "")
            else None
        ),
        "backend_status": _clean_text(source.get("backend_status")),
    }
    sql = """
INSERT INTO vector_evidence_retrieval_events (
    retrieval_event_id,
    owner_user_id,
    request_id,
    query_hash,
    query_purpose,
    chunk_type,
    metadata_json,
    job_id,
    company,
    stage,
    agent_name,
    trace_id,
    run_id,
    embedding_model_id,
    embedding_dimension,
    top_k,
    result_count,
    fallback_reason,
    latency_ms,
    backend_status
)
VALUES (
    %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s,
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (retrieval_event_id) DO NOTHING
RETURNING retrieval_event_id
"""
    params = (
        row["retrieval_event_id"],
        row["owner_user_id"],
        row["request_id"],
        row["query_hash"],
        row["query_purpose"],
        row["chunk_type"],
        _json_compact(row["metadata"]),
        row["job_id"],
        row["company"],
        row["stage"],
        row["agent_name"],
        row["trace_id"],
        row["run_id"],
        row["embedding_model_id"],
        row["embedding_dimension"],
        row["top_k"],
        row["result_count"],
        row["fallback_reason"],
        row["latency_ms"],
        row["backend_status"],
    )
    return _prepared_payload(
        operation="prepare_vector_evidence_retrieval_event_insert",
        table="vector_evidence_retrieval_events",
        row=row,
        sql=sql,
        params=params,
    )


def execute_prepared_pgvector_payload(
    prepared_payload: dict[str, Any],
    *,
    executor: PreparedExecutor | None = None,
) -> dict[str, Any]:
    """Execute only through an explicitly injected executor; default is inert."""

    prepared = _plain_dict(prepared_payload)
    if not callable(executor):
        return {
            **prepared,
            "status": "pgvector_store_executor_not_configured",
            "executed": False,
            "executor_required": True,
        }
    result = executor(_snapshot(prepared))
    return {
        **prepared,
        "status": "pgvector_store_executor_completed",
        "executed": True,
        "executor_required": True,
        "executor_result": _snapshot(result),
    }


# Short aliases for callers that use storage-domain naming.
prepare_chunk_insert_payload = prepare_vector_evidence_chunk_insert_payload
prepare_embedding_insert_payload = prepare_vector_evidence_embedding_insert_payload
prepare_retrieval_event_insert_payload = (
    prepare_vector_evidence_retrieval_event_insert_payload
)
