from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict


_init_lock = Lock()
_db_initialized = False
_db_write_lock = Lock()


_SCHEDULER_ARTIFACTS_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS scheduler_artifacts (
    artifact_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    job_name TEXT NOT NULL DEFAULT '',
    artifact_kind TEXT NOT NULL,
    artifact_name TEXT NOT NULL DEFAULT '',
    payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_scheduler_artifacts_run_kind
ON scheduler_artifacts (run_id, artifact_kind);

CREATE INDEX IF NOT EXISTS idx_scheduler_artifacts_created
ON scheduler_artifacts (created_at DESC);
""".strip()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _database_url() -> str:
    database_url = _clean_text(os.environ.get("DATABASE_URL"))
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is required for Postgres-backed scheduler artifacts."
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


def init_scheduler_artifacts_store() -> None:
    global _db_initialized

    with _init_lock:
        if _db_initialized:
            return

        _run_psql_statement(_SCHEDULER_ARTIFACTS_SCHEMA_SQL)
        _db_initialized = True


def scheduler_artifact_ref(
    *,
    run_id: str,
    artifact_kind: str,
) -> str:
    return f"postgres://scheduler_artifacts/{_clean_text(run_id)}/{_clean_text(artifact_kind)}"


def _artifact_id(run_id: str, artifact_kind: str) -> str:
    raw = f"{_clean_text(run_id)}::{_clean_text(artifact_kind)}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def upsert_scheduler_artifact(
    *,
    run_id: str,
    job_name: str,
    artifact_kind: str,
    artifact_name: str,
    payload_json: Dict[str, Any],
) -> Dict[str, Any]:
    init_scheduler_artifacts_store()

    safe_run_id = _clean_text(run_id)
    safe_kind = _clean_text(artifact_kind)
    if not safe_run_id:
        raise ValueError("run_id is required for scheduler artifact.")
    if not safe_kind:
        raise ValueError("artifact_kind is required for scheduler artifact.")

    artifact_id = _artifact_id(safe_run_id, safe_kind)

    sql = f"""
WITH upserted AS (
    INSERT INTO scheduler_artifacts (
        artifact_id,
        run_id,
        job_name,
        artifact_kind,
        artifact_name,
        payload_json,
        created_at,
        updated_at
    )
    VALUES (
        {_sql_quote_text(artifact_id)},
        {_sql_quote_text(safe_run_id)},
        {_sql_quote_text(job_name)},
        {_sql_quote_text(safe_kind)},
        {_sql_quote_text(artifact_name)},
        {_sql_jsonb(payload_json)},
        now(),
        now()
    )
    ON CONFLICT (artifact_id) DO UPDATE SET
        job_name = EXCLUDED.job_name,
        artifact_name = EXCLUDED.artifact_name,
        payload_json = EXCLUDED.payload_json,
        updated_at = now()
    RETURNING artifact_id, run_id, artifact_kind
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
        "artifact_ref": scheduler_artifact_ref(
            run_id=safe_run_id,
            artifact_kind=safe_kind,
        ),
    }


def get_scheduler_artifact_payload(
    *,
    run_id: str,
    artifact_kind: str,
) -> Dict[str, Any]:
    init_scheduler_artifacts_store()

    safe_run_id = _clean_text(run_id)
    safe_kind = _clean_text(artifact_kind)
    if not safe_run_id or not safe_kind:
        return {}

    artifact_id = _artifact_id(safe_run_id, safe_kind)

    sql = f"""
SELECT json_build_object(
    'found', EXISTS (
        SELECT 1
        FROM scheduler_artifacts
        WHERE artifact_id = {_sql_quote_text(artifact_id)}
    ),
    'payload', COALESCE((
        SELECT payload_json
        FROM scheduler_artifacts
        WHERE artifact_id = {_sql_quote_text(artifact_id)}
        LIMIT 1
    ), '{{}}'::jsonb)
);
""".strip()

    result = _run_psql_json_query(sql)
    if not bool(result.get("found", False)):
        return {}

    return dict(result.get("payload", {}) or {})
