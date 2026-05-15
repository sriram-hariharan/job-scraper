from __future__ import annotations

import json
import os
import subprocess
from threading import Lock
from typing import Any, Dict

from models.description import Description


_db_lock = Lock()
_db_initialized = False


_DESCRIPTION_CACHE_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS job_description_cache (
    job_id TEXT PRIMARY KEY,
    html TEXT,
    text TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_job_description_cache_updated
ON job_description_cache (updated_at DESC);
""".strip()


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _database_url() -> str:
    database_url = _clean_text(os.environ.get("DATABASE_URL"))
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is required for Postgres-backed description cache."
        )
    return database_url


def _sql_quote_text(value: Any) -> str:
    return "'" + str(value or "").replace("'", "''") + "'"


def _run_psql_json_query(sql: str) -> Dict[str, Any]:
    command = [
        "psql",
        _database_url(),
        "-X",
        "-t",
        "-A",
        "-v",
        "ON_ERROR_STOP=1",
        "-c",
        sql,
    ]

    completed = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    )

    lines = [
        line.strip()
        for line in completed.stdout.splitlines()
        if line.strip()
    ]
    if not lines:
        return {}

    return dict(json.loads(lines[-1]) or {})


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


def init_cache() -> None:
    global _db_initialized

    with _db_lock:
        if _db_initialized:
            return

        _run_psql_statement(_DESCRIPTION_CACHE_SCHEMA_SQL)
        _db_initialized = True


def get_description(job_id):
    safe_job_id = _clean_text(job_id)
    if not safe_job_id:
        return None

    init_cache()

    sql = f"""
SELECT json_build_object(
    'found', EXISTS (
        SELECT 1
        FROM job_description_cache
        WHERE job_id = {_sql_quote_text(safe_job_id)}
    ),
    'description', COALESCE((
        SELECT json_build_object(
            'job_id', job_id,
            'html', html,
            'text', text
        )
        FROM job_description_cache
        WHERE job_id = {_sql_quote_text(safe_job_id)}
        LIMIT 1
    ), '{{}}'::json)
);
""".strip()

    payload = _run_psql_json_query(sql)

    if not bool(payload.get("found", False)):
        return None

    row = dict(payload.get("description", {}) or {})
    return Description(
        job_id=_clean_text(row.get("job_id")) or safe_job_id,
        html=row.get("html"),
        text=row.get("text"),
    )


def save_description(description: Description):
    if description is None or not _clean_text(description.job_id):
        return

    init_cache()

    sql = f"""
INSERT INTO job_description_cache (
    job_id,
    html,
    text,
    created_at,
    updated_at
)
VALUES (
    {_sql_quote_text(description.job_id)},
    {_sql_quote_text(description.html)},
    {_sql_quote_text(description.text)},
    now(),
    now()
)
ON CONFLICT (job_id) DO UPDATE SET
    html = EXCLUDED.html,
    text = EXCLUDED.text,
    updated_at = now();
""".strip()

    with _db_lock:
        _run_psql_statement(sql)
