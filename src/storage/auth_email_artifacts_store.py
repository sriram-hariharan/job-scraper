from __future__ import annotations

import hashlib
import json
import os
import subprocess
from threading import Lock
from typing import Any, Dict


_init_lock = Lock()
_db_initialized = False
_db_write_lock = Lock()


_AUTH_EMAIL_ARTIFACTS_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS auth_email_artifacts (
    artifact_id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL DEFAULT '',
    message_kind TEXT NOT NULL DEFAULT '',
    artifact_kind TEXT NOT NULL,
    artifact_name TEXT NOT NULL DEFAULT '',
    payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_auth_email_artifacts_request_kind
ON auth_email_artifacts (request_id, artifact_kind);

CREATE INDEX IF NOT EXISTS idx_auth_email_artifacts_created
ON auth_email_artifacts (created_at DESC);
""".strip()


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _database_url() -> str:
    database_url = _clean_text(os.environ.get("DATABASE_URL"))
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is required for Postgres-backed auth email artifacts."
        )
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
            "-c",
            sql,
        ],
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
            "-c",
            sql,
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    if not lines:
        return {}

    return dict(json.loads(lines[-1]) or {})


def init_auth_email_artifacts_store() -> None:
    global _db_initialized

    with _init_lock:
        if _db_initialized:
            return

        _run_psql_statement(_AUTH_EMAIL_ARTIFACTS_SCHEMA_SQL)
        _db_initialized = True


def auth_email_artifact_ref(
    *,
    request_id: str,
    artifact_kind: str,
) -> str:
    return f"postgres://auth_email_artifacts/{_clean_text(request_id)}/{_clean_text(artifact_kind)}"


def _artifact_id(request_id: str, artifact_kind: str, message_kind: str) -> str:
    raw = f"{_clean_text(request_id)}::{_clean_text(artifact_kind)}::{_clean_text(message_kind)}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def upsert_auth_email_artifact(
    *,
    request_id: str,
    message_kind: str,
    artifact_kind: str,
    artifact_name: str,
    payload_json: Dict[str, Any],
) -> Dict[str, Any]:
    init_auth_email_artifacts_store()

    safe_request_id = _clean_text(request_id)
    safe_kind = _clean_text(artifact_kind)
    safe_message_kind = _clean_text(message_kind)

    if not safe_request_id:
        raise ValueError("request_id is required for auth email artifact.")
    if not safe_kind:
        raise ValueError("artifact_kind is required for auth email artifact.")

    artifact_id = _artifact_id(safe_request_id, safe_kind, safe_message_kind)

    sql = f"""
WITH upserted AS (
    INSERT INTO auth_email_artifacts (
        artifact_id,
        request_id,
        message_kind,
        artifact_kind,
        artifact_name,
        payload_json,
        created_at,
        updated_at
    )
    VALUES (
        {_sql_quote_text(artifact_id)},
        {_sql_quote_text(safe_request_id)},
        {_sql_quote_text(safe_message_kind)},
        {_sql_quote_text(safe_kind)},
        {_sql_quote_text(artifact_name)},
        {_sql_jsonb(payload_json)},
        now(),
        now()
    )
    ON CONFLICT (artifact_id) DO UPDATE SET
        message_kind = EXCLUDED.message_kind,
        artifact_name = EXCLUDED.artifact_name,
        payload_json = EXCLUDED.payload_json,
        updated_at = now()
    RETURNING artifact_id
)
SELECT json_build_object(
    'upserted', EXISTS (SELECT 1 FROM upserted),
    'artifact_id', (SELECT artifact_id FROM upserted LIMIT 1)
);
""".strip()

    with _db_write_lock:
        result = _run_psql_json_query(sql)

    return {
        "ok": bool(result.get("upserted", False)),
        "artifact_id": _clean_text(result.get("artifact_id")) or artifact_id,
        "artifact_ref": auth_email_artifact_ref(
            request_id=safe_request_id,
            artifact_kind=safe_kind,
        ),
    }


def get_auth_email_artifact_payload(
    *,
    request_id: str,
    artifact_kind: str,
    message_kind: str = "",
) -> Dict[str, Any]:
    init_auth_email_artifacts_store()

    safe_request_id = _clean_text(request_id)
    safe_kind = _clean_text(artifact_kind)
    safe_message_kind = _clean_text(message_kind)

    if not safe_request_id or not safe_kind:
        return {}

    if safe_message_kind:
        artifact_id = _artifact_id(safe_request_id, safe_kind, safe_message_kind)
        where_sql = f"artifact_id = {_sql_quote_text(artifact_id)}"
    else:
        where_sql = (
            f"request_id = {_sql_quote_text(safe_request_id)} "
            f"AND artifact_kind = {_sql_quote_text(safe_kind)}"
        )

    sql = f"""
SELECT json_build_object(
    'found', EXISTS (
        SELECT 1
        FROM auth_email_artifacts
        WHERE {where_sql}
    ),
    'payload', COALESCE((
        SELECT payload_json
        FROM auth_email_artifacts
        WHERE {where_sql}
        ORDER BY updated_at DESC
        LIMIT 1
    ), '{{}}'::jsonb)
);
""".strip()

    result = _run_psql_json_query(sql)
    if not bool(result.get("found", False)):
        return {}

    return dict(result.get("payload", {}) or {})
