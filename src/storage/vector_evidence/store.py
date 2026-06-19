"""Default-off pgvector storage and injected DB executor for vector evidence.

The module prepares deterministic rows and parameterized SQL. Execution is
available only through a caller-supplied callable or already-open connection.
It imports no database driver, opens no connection, commits no transaction,
creates no embedding, calls no provider, and has no pipeline or startup hook.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
import math
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from src.agents import vector_evidence_contract


DEFAULT_SCHEMA_SQL_PATH = Path("src/storage/vector_evidence/schema.sql")
STORE_ADAPTER_VERSION = "phase-8n-pgvector-store-adapter-v1"
DB_EXECUTOR_VERSION = "phase-8p-pgvector-db-executor-v1"

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


def pgvector_db_executor_safety_metadata(
    *,
    executor_supplied: bool = False,
    read_only: bool = True,
    schema_setup_executed: bool = False,
    chunks_written: bool = False,
    embeddings_written: bool = False,
    retrieval_events_written: bool = False,
    did_read_database: bool = False,
) -> dict[str, bool]:
    safety = pgvector_store_safety_metadata()
    safety.update(
        {
            "read_only": bool(read_only),
            "advisory_only": True,
            "pgvector_store_db_executor": True,
            "db_executor_required": True,
            "db_executor_supplied": bool(executor_supplied),
            "schema_setup_executed": bool(schema_setup_executed),
            "chunks_written": bool(chunks_written),
            "embeddings_written": bool(embeddings_written),
            "retrieval_events_written": bool(retrieval_events_written),
            "embeddings_created": False,
            "provider_calls_made": False,
            "vector_db_connected": bool(executor_supplied),
            "did_read_database": bool(did_read_database),
            "did_write_database": bool(
                schema_setup_executed
                or chunks_written
                or embeddings_written
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
    )
    return safety


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


def _db_executor_base_payload(
    *,
    operation: str,
    executor_supplied: bool,
    read_only: bool,
) -> dict[str, Any]:
    return {
        "adapter_version": STORE_ADAPTER_VERSION,
        "db_executor_version": DB_EXECUTOR_VERSION,
        "status": (
            "pgvector_store_db_executor_ready"
            if executor_supplied
            else "pgvector_store_db_executor_not_configured"
        ),
        "operation": operation,
        "executed": False,
        "db_executor_required": True,
        "db_executor_supplied": bool(executor_supplied),
        "provider_backed_automated_agents": 0,
        "live_provider_backed_automated_agents": 0,
        "mutation_authorized_agents": 0,
        "mutation_authorized_scoring_agents": 0,
        "mutation_authorized_ranking_agents": 0,
        "mutation_authorized_application_agents": 0,
        "safety_metadata": pgvector_db_executor_safety_metadata(
            executor_supplied=executor_supplied,
            read_only=read_only,
        ),
    }


def _row_to_dict(row: Any, description: Iterable[Any]) -> dict[str, Any]:
    if isinstance(row, Mapping):
        return deepcopy(dict(row))
    columns: list[str] = []
    for item in description:
        columns.append(str(item if isinstance(item, str) else item[0]))
    return {
        column: deepcopy(row[index])
        for index, column in enumerate(columns)
        if index < len(row)
    }


def _execute_with_injected_db(
    request_payload: dict[str, Any],
    *,
    db_executor: Any = None,
    fetch_rows: bool = False,
) -> dict[str, Any]:
    request = _plain_dict(request_payload)
    if db_executor is None:
        return {"executed": False, "rows": [], "executor_result": {}}
    if callable(db_executor):
        raw_result = db_executor(deepcopy(request))
        if isinstance(raw_result, dict):
            rows = raw_result.get("rows", [])
            return {
                "executed": True,
                "rows": deepcopy(rows) if isinstance(rows, list) else [],
                "executor_result": deepcopy(raw_result),
            }
        if isinstance(raw_result, list):
            return {
                "executed": True,
                "rows": deepcopy(raw_result),
                "executor_result": {"rows": deepcopy(raw_result)},
            }
        return {
            "executed": True,
            "rows": [],
            "executor_result": {"result": deepcopy(raw_result)},
        }
    if not hasattr(db_executor, "cursor"):
        raise TypeError("db_executor must be callable or connection-like.")

    cursor = db_executor.cursor()
    try:
        sql_value = request.get("sql")
        if not isinstance(sql_value, str) or not sql_value.strip():
            raise ValueError("sql must be a non-empty string.")
        sql = sql_value
        params = request.get("params", ())
        if params:
            cursor.execute(sql, tuple(params))
        else:
            cursor.execute(sql)
        rows = cursor.fetchall() if fetch_rows and hasattr(cursor, "fetchall") else []
        description = getattr(cursor, "description", None) or []
        normalized_rows = [_row_to_dict(row, description) for row in rows]
        return {
            "executed": True,
            "rows": normalized_rows,
            "executor_result": {
                "driver": "injected_connection",
                "row_count": len(normalized_rows),
            },
        }
    finally:
        close = getattr(cursor, "close", None)
        if callable(close):
            close()


def execute_pgvector_schema_setup(
    *,
    db_executor: Any = None,
    schema_path: Path = DEFAULT_SCHEMA_SQL_PATH,
) -> dict[str, Any]:
    """Execute static schema SQL only through an explicitly injected boundary."""

    supplied = db_executor is not None
    payload = _db_executor_base_payload(
        operation="execute_pgvector_schema_setup",
        executor_supplied=supplied,
        read_only=False,
    )
    payload["sql"] = pgvector_schema_sql_text(schema_path)
    payload["params"] = ()
    if not supplied:
        return payload
    execution = _execute_with_injected_db(payload, db_executor=db_executor)
    executed = execution["executed"] is True
    payload.update(
        {
            "status": (
                "pgvector_schema_setup_executed"
                if executed
                else "pgvector_store_db_executor_not_configured"
            ),
            "executed": executed,
            "executor_result": execution["executor_result"],
            "safety_metadata": pgvector_db_executor_safety_metadata(
                executor_supplied=True,
                read_only=False,
                schema_setup_executed=executed,
            ),
        }
    )
    return payload


def _execute_prepared_write(
    prepared_payload: dict[str, Any],
    *,
    db_executor: Any = None,
    expected_table: str,
    operation: str,
    write_flag: str,
) -> dict[str, Any]:
    prepared = _plain_dict(prepared_payload)
    if prepared.get("table") != expected_table:
        raise ValueError(f"prepared payload must target {expected_table}.")
    supplied = db_executor is not None
    payload = {
        **_db_executor_base_payload(
            operation=operation,
            executor_supplied=supplied,
            read_only=False,
        ),
        "prepared_payload": deepcopy(prepared),
        "sql": _require_text(prepared.get("sql"), "sql"),
        "params": tuple(prepared.get("params", ()) or ()),
    }
    if not supplied:
        return payload
    execution = _execute_with_injected_db(
        payload,
        db_executor=db_executor,
        fetch_rows=True,
    )
    executed = execution["executed"] is True
    flags = {
        "chunks_written": False,
        "embeddings_written": False,
        "retrieval_events_written": False,
    }
    flags[write_flag] = executed
    payload.update(
        {
            "status": (
                "pgvector_store_write_executed"
                if executed
                else "pgvector_store_db_executor_not_configured"
            ),
            "executed": executed,
            "rows": execution["rows"],
            "executor_result": execution["executor_result"],
            "safety_metadata": pgvector_db_executor_safety_metadata(
                executor_supplied=True,
                read_only=False,
                **flags,
            ),
        }
    )
    return payload


def execute_vector_evidence_chunk_insert(
    prepared_payload: dict[str, Any],
    *,
    db_executor: Any = None,
) -> dict[str, Any]:
    return _execute_prepared_write(
        prepared_payload,
        db_executor=db_executor,
        expected_table="vector_evidence_chunks",
        operation="execute_vector_evidence_chunk_insert",
        write_flag="chunks_written",
    )


def execute_vector_evidence_embedding_insert(
    prepared_payload: dict[str, Any],
    *,
    db_executor: Any = None,
) -> dict[str, Any]:
    return _execute_prepared_write(
        prepared_payload,
        db_executor=db_executor,
        expected_table="vector_evidence_embeddings",
        operation="execute_vector_evidence_embedding_insert",
        write_flag="embeddings_written",
    )


def execute_vector_evidence_retrieval_event_insert(
    prepared_payload: dict[str, Any],
    *,
    db_executor: Any = None,
) -> dict[str, Any]:
    return _execute_prepared_write(
        prepared_payload,
        db_executor=db_executor,
        expected_table="vector_evidence_retrieval_events",
        operation="execute_vector_evidence_retrieval_event_insert",
        write_flag="retrieval_events_written",
    )


def prepare_vector_evidence_retrieval_select_payload(
    *,
    owner_user_id: str,
    query_embedding: list[float] | tuple[float, ...],
    embedding_model_id: str,
    top_k: int = 5,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Prepare an exact pgvector candidate query from an explicit vector."""

    normalized = _normalized_embedding(query_embedding)
    vector_text = "[" + ",".join(format(value, ".17g") for value in normalized) + "]"
    normalized_filters = _plain_dict(filters)
    clauses = [
        "chunks.owner_user_id = %s",
        "embeddings.embedding_model_id = %s",
        "embeddings.embedding_dimension = %s",
        "chunks.deleted_at IS NULL",
        "embeddings.deleted_at IS NULL",
    ]
    safe_owner_user_id = _require_text(owner_user_id, "owner_user_id")
    safe_embedding_model_id = _require_text(
        embedding_model_id,
        "embedding_model_id",
    )
    where_params: list[Any] = [
        safe_owner_user_id,
        safe_embedding_model_id,
        len(normalized),
    ]
    for field in ("chunk_type", "job_id", "company", "stage", "agent_name"):
        value = _clean_text(normalized_filters.get(field))
        if value:
            column = "chunks.chunk_type" if field == "chunk_type" else f"chunks.{field}"
            clauses.append(f"{column} = %s")
            where_params.append(value)
    safe_top_k = _positive_int(top_k, "top_k")
    params = [vector_text, vector_text, *where_params, safe_top_k]
    sql = f"""
SELECT
    chunks.chunk_id,
    chunks.chunk_type,
    chunks.chunk_version,
    chunks.content_hash,
    chunks.normalized_text AS evidence_text,
    chunks.metadata_json AS metadata,
    chunks.job_id,
    chunks.company,
    chunks.title,
    chunks.source,
    chunks.stage,
    chunks.agent_name,
    chunks.trace_id,
    chunks.run_id,
    chunks.resume_version,
    chunks.profile_version,
    embeddings.embedding_model_id,
    embeddings.embedding_dimension,
    embeddings.embedding <=> %s::vector AS vector_distance,
    1 - (embeddings.embedding <=> %s::vector) AS retrieval_score
FROM vector_evidence_chunks AS chunks
JOIN vector_evidence_embeddings AS embeddings
  ON embeddings.chunk_id = chunks.chunk_id
WHERE {" AND ".join(clauses)}
ORDER BY vector_distance ASC, chunks.chunk_type ASC, chunks.chunk_id ASC
LIMIT %s
""".strip()
    return _prepared_payload(
        operation="prepare_vector_evidence_retrieval_select",
        table="vector_evidence_embeddings",
        row={
            "owner_user_id": safe_owner_user_id,
            "embedding_model_id": safe_embedding_model_id,
            "embedding_dimension": len(normalized),
            "query_embedding": normalized,
            "filters": normalized_filters,
            "top_k": safe_top_k,
        },
        sql=sql,
        params=tuple(params),
    )


def select_vector_evidence_retrieval_candidates(
    prepared_payload: dict[str, Any],
    *,
    db_executor: Any = None,
) -> dict[str, Any]:
    """Run one prepared candidate select through an injected executor."""

    prepared = _plain_dict(prepared_payload)
    supplied = db_executor is not None
    payload = {
        **_db_executor_base_payload(
            operation="select_vector_evidence_retrieval_candidates",
            executor_supplied=supplied,
            read_only=True,
        ),
        "prepared_payload": deepcopy(prepared),
        "sql": _require_text(prepared.get("sql"), "sql"),
        "params": tuple(prepared.get("params", ()) or ()),
        "retrieval_candidates": [],
        "result_count": 0,
    }
    if not supplied:
        return payload
    execution = _execute_with_injected_db(
        payload,
        db_executor=db_executor,
        fetch_rows=True,
    )
    candidates = [
        deepcopy(row) for row in execution["rows"] if isinstance(row, dict)
    ]
    payload.update(
        {
            "status": "pgvector_retrieval_candidates_selected",
            "executed": execution["executed"] is True,
            "retrieval_candidates": candidates,
            "result_count": len(candidates),
            "executor_result": execution["executor_result"],
            "safety_metadata": pgvector_db_executor_safety_metadata(
                executor_supplied=True,
                read_only=True,
                did_read_database=execution["executed"] is True,
            ),
        }
    )
    return payload


def read_vector_evidence_smoke_records(
    *,
    owner_user_id: str,
    smoke_identifier: str,
    db_executor: Any = None,
) -> dict[str, Any]:
    """Read deterministic smoke chunk/event records through an injected DB."""

    safe_owner_user_id = _require_text(owner_user_id, "owner_user_id")
    safe_smoke_identifier = _require_text(
        smoke_identifier,
        "smoke_identifier",
    )
    supplied = db_executor is not None
    sql = """
SELECT
    'chunk' AS record_type,
    chunk_id AS record_id
FROM vector_evidence_chunks
WHERE owner_user_id = %s
  AND source_record_id = %s
  AND source = 'operator_local_smoke'
  AND deleted_at IS NULL
ORDER BY chunk_id
LIMIT 1
"""
    event_sql = """
SELECT
    'retrieval_event' AS record_type,
    retrieval_event_id AS record_id
FROM vector_evidence_retrieval_events
WHERE owner_user_id = %s
  AND request_id = %s
  AND query_purpose = 'pgvector_local_smoke'
  AND deleted_at IS NULL
ORDER BY retrieval_event_id
LIMIT 1
"""
    payload = {
        **_db_executor_base_payload(
            operation="read_vector_evidence_smoke_records",
            executor_supplied=supplied,
            read_only=True,
        ),
        "readback_attempted": supplied,
        "readback_executed": False,
        "smoke_chunk_found": False,
        "retrieval_event_found": False,
        "rows_read": 0,
        "rows": [],
        "sql": f"({sql.strip()})\nUNION ALL\n({event_sql.strip()})",
        "params": (
            safe_owner_user_id,
            safe_smoke_identifier,
            safe_owner_user_id,
            safe_smoke_identifier,
        ),
    }
    if not supplied:
        return payload

    execution = _execute_with_injected_db(
        payload,
        db_executor=db_executor,
        fetch_rows=True,
    )
    rows = [
        deepcopy(row) for row in execution["rows"] if isinstance(row, dict)
    ]
    record_types = {
        str(row.get("record_type", "") or "") for row in rows
    }
    executed = execution["executed"] is True
    payload.update(
        {
            "status": (
                "pgvector_smoke_readback_executed"
                if executed
                else "pgvector_store_db_executor_not_configured"
            ),
            "executed": executed,
            "readback_executed": executed,
            "smoke_chunk_found": "chunk" in record_types,
            "retrieval_event_found": "retrieval_event" in record_types,
            "rows_read": len(rows),
            "rows": rows,
            "executor_result": execution["executor_result"],
            "safety_metadata": pgvector_db_executor_safety_metadata(
                executor_supplied=True,
                read_only=True,
                did_read_database=executed,
            ),
        }
    )
    return payload


# Short aliases for callers that use storage-domain naming.
prepare_chunk_insert_payload = prepare_vector_evidence_chunk_insert_payload
prepare_embedding_insert_payload = prepare_vector_evidence_embedding_insert_payload
prepare_retrieval_event_insert_payload = (
    prepare_vector_evidence_retrieval_event_insert_payload
)
