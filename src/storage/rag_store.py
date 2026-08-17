from __future__ import annotations

import json
import os
import subprocess
from threading import Lock
from typing import Any, Dict, Iterable, List

from src.storage.redis_cache import cache_delete_prefix, cache_get_json, cache_set_json


_init_lock = Lock()
_db_initialized = False
_db_write_lock = Lock()

_RAG_JOB_DOCUMENTS_CACHE_PREFIX = "rag:job_documents:v1:"
RAG_JOB_RETENTION_DAYS = 15
DEFAULT_BOUNDED_OWNER_PROJECTION_JOBS = 500_000
MAX_BOUNDED_OWNER_PROJECTION_JOBS = 500_000


def _rag_cache_ttl_seconds() -> int:
    raw = _clean_text(os.environ.get("JOB_STACK_RAG_REDIS_TTL_SECONDS"))
    try:
        ttl = int(raw)
    except Exception:
        ttl = 120

    return max(1, min(ttl, 900))


def _rag_cache_max_bytes() -> int:
    raw = _clean_text(os.environ.get("JOB_STACK_RAG_REDIS_MAX_BYTES"))
    try:
        max_bytes = int(raw)
    except Exception:
        max_bytes = 5_000_000

    return max(100_000, min(max_bytes, 50_000_000))


def _rag_documents_cache_key(limit: int) -> str:
    return f"{_RAG_JOB_DOCUMENTS_CACHE_PREFIX}{int(limit)}"


def _cache_get_docs_safe(key: str):
    try:
        cached = cache_get_json(key)
    except Exception:
        return None

    if isinstance(cached, list):
        return cached

    return None


def _cache_set_docs_safe(key: str, docs: List[Dict[str, Any]]) -> None:
    try:
        payload = json.dumps(
            docs,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        if len(payload.encode("utf-8")) > _rag_cache_max_bytes():
            return

        cache_set_json(
            key,
            docs,
            ttl_seconds=_rag_cache_ttl_seconds(),
        )
    except Exception:
        return


def _invalidate_rag_document_cache() -> bool:
    try:
        cache_delete_prefix(_RAG_JOB_DOCUMENTS_CACHE_PREFIX)
        return True
    except Exception:
        return False


_RAG_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS rag_job_documents (
    merge_key TEXT PRIMARY KEY,
    doc_id TEXT NOT NULL DEFAULT '',
    company TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL DEFAULT '',
    source TEXT NOT NULL DEFAULT '',
    job_url TEXT NOT NULL DEFAULT '',
    retrieval_text TEXT NOT NULL DEFAULT '',
    payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_rag_job_documents_doc_id
ON rag_job_documents (doc_id);

CREATE INDEX IF NOT EXISTS idx_rag_job_documents_company_title
ON rag_job_documents (company, title);

CREATE INDEX IF NOT EXISTS idx_rag_job_documents_updated
ON rag_job_documents (updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_rag_job_documents_source_merge_key
ON rag_job_documents (source, merge_key);
""".strip()


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _database_url() -> str:
    database_url = _clean_text(os.environ.get("DATABASE_URL"))
    if not database_url:
        raise RuntimeError("DATABASE_URL is required for Postgres-backed RAG store.")
    return database_url


def _sql_quote_text(value: Any) -> str:
    return "'" + str(value or "").replace("'", "''") + "'"


def _sql_jsonb(value: Any) -> str:
    return (
        _sql_quote_text(
            json.dumps(
                value or {},
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        + "::jsonb"
    )


def _run_psql_statement(sql: str) -> None:
    subprocess.run(
        [
            "psql",
            _database_url(),
            "-X",
            "-v",
            "ON_ERROR_STOP=1",
        ],
        input=sql,
        check=True,
        capture_output=True,
        text=True,
    )


def _run_psql_json_query(sql: str) -> Dict[str, Any]:
    completed = subprocess.run(
        [
            "psql",
            _database_url(),
            "-X",
            "-t",
            "-A",
            "-v",
            "ON_ERROR_STOP=1",
        ],
        input=sql,
        check=True,
        capture_output=True,
        text=True,
    )

    lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    if not lines:
        return {}

    return dict(json.loads(lines[-1]) or {})


def init_rag_store() -> None:
    global _db_initialized

    with _init_lock:
        if _db_initialized:
            return

        _run_psql_statement(_RAG_SCHEMA_SQL)
        _db_initialized = True


def _doc_merge_key(doc: Dict[str, Any]) -> str:
    metadata = doc.get("metadata") or {}
    if not isinstance(metadata, dict):
        metadata = {}

    for key_name in ("merge_key", "job_doc_id", "doc_id"):
        value = _clean_text(doc.get(key_name))
        if value:
            return f"{key_name}:{value}"

    for key_name in ("job_doc_id", "doc_id"):
        value = _clean_text(metadata.get(key_name))
        if value:
            return f"{key_name}:{value}"

    for key_name in ("url", "link", "job_url"):
        value = _clean_text(doc.get(key_name)) or _clean_text(metadata.get(key_name))
        if value:
            return f"{key_name}:{value}"

    source = _clean_text(metadata.get("source") or doc.get("source"))
    job_id = _clean_text(metadata.get("job_id") or doc.get("job_id"))
    if source and job_id:
        return f"source_job_id:{source}:{job_id}"

    company = " ".join(_clean_text(metadata.get("company") or doc.get("company")).lower().split())
    title = " ".join(_clean_text(metadata.get("title") or doc.get("title")).lower().split())
    if company and title:
        return f"company_title:{company}||{title}"

    return ""


def _doc_row(doc: Dict[str, Any]) -> Dict[str, Any]:
    metadata = doc.get("metadata") or {}
    if not isinstance(metadata, dict):
        metadata = {}

    merge_key = _doc_merge_key(doc)
    if not merge_key:
        raise ValueError("RAG document is missing a stable merge key.")

    return {
        "merge_key": merge_key,
        "doc_id": _clean_text(doc.get("doc_id") or metadata.get("doc_id")),
        "company": _clean_text(doc.get("company") or metadata.get("company")),
        "title": _clean_text(doc.get("title") or metadata.get("title")),
        "source": _clean_text(doc.get("source") or metadata.get("source")),
        "job_url": _clean_text(doc.get("job_url") or metadata.get("job_url") or doc.get("url") or doc.get("link")),
        "retrieval_text": _clean_text(doc.get("retrieval_text") or doc.get("text")),
        "payload_json": dict(doc or {}),
        "metadata_json": dict(metadata or {}),
    }


def upsert_rag_job_documents(docs: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    init_rag_store()

    rows = []
    anonymous_count = 0

    for doc in docs:
        try:
            rows.append(_doc_row(dict(doc or {})))
        except ValueError:
            anonymous_count += 1

    if not rows:
        return {"ok": True, "upserted_count": 0, "anonymous_skipped_count": anonymous_count}

    chunk_size = 250
    upserted_total = 0

    with _db_write_lock:
        for start in range(0, len(rows), chunk_size):
            chunk = rows[start : start + chunk_size]
            values = []
            for row in chunk:
                values.append(
                    "("
                    + ", ".join(
                        [
                            _sql_quote_text(row["merge_key"]),
                            _sql_quote_text(row["doc_id"]),
                            _sql_quote_text(row["company"]),
                            _sql_quote_text(row["title"]),
                            _sql_quote_text(row["source"]),
                            _sql_quote_text(row["job_url"]),
                            _sql_quote_text(row["retrieval_text"]),
                            _sql_jsonb(row["payload_json"]),
                            _sql_jsonb(row["metadata_json"]),
                            "now()",
                            "now()",
                        ]
                    )
                    + ")"
                )

            sql = f"""
WITH upserted AS (
    INSERT INTO rag_job_documents (
        merge_key,
        doc_id,
        company,
        title,
        source,
        job_url,
        retrieval_text,
        payload_json,
        metadata_json,
        created_at,
        updated_at
    )
    VALUES
{",\n".join(values)}
    ON CONFLICT (merge_key) DO UPDATE SET
        doc_id = EXCLUDED.doc_id,
        company = EXCLUDED.company,
        title = EXCLUDED.title,
        source = EXCLUDED.source,
        job_url = EXCLUDED.job_url,
        retrieval_text = EXCLUDED.retrieval_text,
        payload_json = EXCLUDED.payload_json,
        metadata_json = EXCLUDED.metadata_json,
        updated_at = now()
    RETURNING merge_key
)
SELECT json_build_object(
    'upserted_count', (SELECT COUNT(*) FROM upserted)
);
""".strip()

            result = _run_psql_json_query(sql)
            upserted_total += int(result.get("upserted_count", 0) or 0)

    _invalidate_rag_document_cache()

    return {
        "ok": True,
        "upserted_count": upserted_total,
        "anonymous_skipped_count": anonymous_count,
    }


def get_rag_job_documents(limit: int = 100000) -> List[Dict[str, Any]]:
    try:
        safe_limit = int(limit)
    except Exception:
        safe_limit = 100000

    safe_limit = max(1, min(safe_limit, 500000))
    cache_key = _rag_documents_cache_key(safe_limit)

    cached = _cache_get_docs_safe(cache_key)
    if cached is not None:
        return [dict(row or {}) for row in cached]

    init_rag_store()

    sql = f"""
WITH doc_rows AS (
    SELECT payload_json
    FROM rag_job_documents
    ORDER BY updated_at DESC, merge_key ASC
    LIMIT {safe_limit}
)
SELECT json_build_object(
    'rows', COALESCE((SELECT json_agg(payload_json) FROM doc_rows), '[]'::json)
);
""".strip()

    result = _run_psql_json_query(sql)
    docs = [dict(row or {}) for row in list(result.get("rows", []) or [])]
    _cache_set_docs_safe(cache_key, docs)
    return docs


def get_bounded_owner_projection_rag_job_documents(
    limit: int = DEFAULT_BOUNDED_OWNER_PROJECTION_JOBS,
) -> List[Dict[str, Any]]:
    """Read the complete active shared corpus with a fail-loud safety ceiling."""

    try:
        safe_limit = int(limit)
    except Exception:
        safe_limit = DEFAULT_BOUNDED_OWNER_PROJECTION_JOBS
    safe_limit = max(
        1,
        min(safe_limit, MAX_BOUNDED_OWNER_PROJECTION_JOBS),
    )
    cache_key = (
        f"{_RAG_JOB_DOCUMENTS_CACHE_PREFIX}owner_projection:{safe_limit}"
    )

    cached = _cache_get_docs_safe(cache_key)
    if cached is not None:
        docs = [dict(row or {}) for row in cached]
        if len(docs) > safe_limit:
            raise RuntimeError(
                "shared_postgres_active_corpus_safety_limit_exceeded: "
                f"active_rows_at_least={len(docs)} safety_limit={safe_limit}"
            )
        return docs

    init_rag_store()

    sql = f"""
WITH normalized_rows AS (
    SELECT
        payload_json,
        updated_at,
        merge_key,
        COALESCE(
            NULLIF(LOWER(BTRIM(company)), ''),
            'missing-company:' || merge_key
        ) AS company_key,
        COALESCE(
            NULLIF(LOWER(BTRIM(source)), ''),
            'missing-source'
        ) AS source_key
    FROM rag_job_documents
    WHERE updated_at >= statement_timestamp() - INTERVAL '{RAG_JOB_RETENTION_DAYS} days'
),
company_ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY company_key
            ORDER BY updated_at DESC, source_key ASC, merge_key ASC
        ) AS company_rank
    FROM normalized_rows
),
source_balanced AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY company_rank, source_key
            ORDER BY updated_at DESC, company_key ASC, merge_key ASC
        ) AS source_rank
    FROM company_ranked
),
projected_rows AS (
    SELECT
        payload_json,
        updated_at,
        merge_key,
        company_key,
        source_key,
        company_rank,
        source_rank
    FROM source_balanced
    ORDER BY
        company_rank ASC,
        source_rank ASC,
        updated_at DESC,
        source_key ASC,
        company_key ASC,
        merge_key ASC
    LIMIT {safe_limit + 1}
)
SELECT json_build_object(
    'rows', COALESCE(
        (
            SELECT json_agg(
                payload_json ORDER BY
                    company_rank ASC,
                    source_rank ASC,
                    updated_at DESC,
                    source_key ASC,
                    company_key ASC,
                    merge_key ASC
            )
            FROM projected_rows
        ),
        '[]'::json
    )
);
""".strip()

    result = _run_psql_json_query(sql)
    docs = [
        dict(row or {})
        for row in list(result.get("rows", []) or [])
    ]
    if len(docs) > safe_limit:
        raise RuntimeError(
            "shared_postgres_active_corpus_safety_limit_exceeded: "
            f"active_rows_at_least={len(docs)} safety_limit={safe_limit}"
        )
    _cache_set_docs_safe(cache_key, docs)
    return docs


def delete_stale_rag_job_documents() -> Dict[str, Any]:
    """Delete shared jobs not refreshed within the active retention window."""

    init_rag_store()
    sql = f"""
WITH cutoff AS (
    SELECT statement_timestamp() - INTERVAL '{RAG_JOB_RETENTION_DAYS} days' AS stale_before
),
inspected AS (
    SELECT COUNT(*) AS inspected_count
    FROM rag_job_documents
),
stale_candidates AS (
    SELECT COUNT(*) AS candidate_count
    FROM rag_job_documents
    WHERE updated_at < (SELECT stale_before FROM cutoff)
),
deleted AS (
    DELETE FROM rag_job_documents
    WHERE updated_at < (SELECT stale_before FROM cutoff)
    RETURNING merge_key
)
SELECT json_build_object(
    'inspected_count', (SELECT inspected_count FROM inspected),
    'candidate_count', (SELECT candidate_count FROM stale_candidates),
    'deleted_count', (SELECT COUNT(*) FROM deleted)
);
""".strip()

    result = _run_psql_json_query(sql)
    inspected_count = int(result.get("inspected_count", 0) or 0)
    candidate_count = int(result.get("candidate_count", 0) or 0)
    deleted_count = int(result.get("deleted_count", 0) or 0)
    invalidation_attempted = deleted_count > 0
    invalidation_succeeded = (
        _invalidate_rag_document_cache()
        if invalidation_attempted
        else True
    )
    return {
        "ok": bool(invalidation_succeeded),
        "retention_days": RAG_JOB_RETENTION_DAYS,
        "inspected_count": inspected_count,
        "candidate_count": candidate_count,
        "deleted_count": deleted_count,
        "retained_count": max(0, inspected_count - deleted_count),
        "cache_invalidation_attempted": invalidation_attempted,
        "cache_invalidation_succeeded": bool(invalidation_succeeded),
    }


def count_rag_job_documents() -> int:
    init_rag_store()

    sql = """
SELECT json_build_object(
    'count', (SELECT COUNT(*) FROM rag_job_documents)
);
""".strip()

    result = _run_psql_json_query(sql)
    return int(result.get("count", 0) or 0)


def list_himalayas_rag_candidates(
    *,
    after_merge_key: str = "",
    limit: int = 250,
) -> Dict[str, Any]:
    safe_limit = int(limit)
    if safe_limit < 1 or safe_limit > 250:
        raise ValueError("Himalayas RAG candidate limit must be between 1 and 250.")
    cursor = _clean_text(after_merge_key)
    cursor_filter = (
        f"AND merge_key > {_sql_quote_text(cursor)}" if cursor else ""
    )

    init_rag_store()
    sql = f"""
WITH candidates AS (
    SELECT
        merge_key,
        doc_id,
        source,
        payload_json ->> 'expiry_date' AS expiry_date,
        payload_json ->> 'job_id' AS job_id
    FROM rag_job_documents
    WHERE source = 'himalayas'
      {cursor_filter}
    ORDER BY merge_key ASC
    LIMIT {safe_limit}
)
SELECT json_build_object(
    'rows', COALESCE((SELECT json_agg(row_to_json(candidates)) FROM candidates), '[]'::json)
);
""".strip()
    result = _run_psql_json_query(sql)
    rows = [dict(row or {}) for row in list(result.get("rows", []) or [])]
    return {
        "ok": True,
        "rows": rows,
        "count": len(rows),
        "next_cursor": _clean_text(rows[-1].get("merge_key")) if rows else "",
    }


def delete_himalayas_rag_merge_keys(
    merge_keys: Iterable[str],
    *,
    dry_run: bool = True,
) -> Dict[str, Any]:
    keys = sorted(
        {
            value.strip()
            for value in merge_keys
            if isinstance(value, str) and value.strip()
        }
    )
    if len(keys) > 250:
        raise ValueError("At most 250 exact Himalayas RAG merge keys may be deleted.")
    if not keys:
        return {
            "ok": True,
            "dry_run": bool(dry_run),
            "candidate_count": 0,
            "deleted_count": 0,
            "cache_invalidation_attempted": False,
            "cache_invalidation_succeeded": False,
        }

    init_rag_store()
    values = ", ".join(_sql_quote_text(value) for value in keys)
    if dry_run:
        sql = f"""
SELECT json_build_object(
    'candidate_count', (
        SELECT COUNT(*)
        FROM rag_job_documents
        WHERE source = 'himalayas'
          AND merge_key IN ({values})
    )
);
""".strip()
        result = _run_psql_json_query(sql)
        return {
            "ok": True,
            "dry_run": True,
            "candidate_count": int(result.get("candidate_count", 0) or 0),
            "deleted_count": 0,
            "cache_invalidation_attempted": False,
            "cache_invalidation_succeeded": False,
        }

    sql = f"""
WITH deleted AS (
    DELETE FROM rag_job_documents
    WHERE source = 'himalayas'
      AND merge_key IN ({values})
    RETURNING merge_key
)
SELECT json_build_object(
    'deleted_count', (SELECT COUNT(*) FROM deleted)
);
""".strip()
    result = _run_psql_json_query(sql)
    deleted_count = int(result.get("deleted_count", 0) or 0)
    invalidated = _invalidate_rag_document_cache()
    return {
        "ok": bool(invalidated),
        "dry_run": False,
        "candidate_count": deleted_count,
        "deleted_count": deleted_count,
        "cache_invalidation_attempted": True,
        "cache_invalidation_succeeded": bool(invalidated),
    }
