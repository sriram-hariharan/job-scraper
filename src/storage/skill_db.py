from __future__ import annotations

import json
import os
import subprocess
from threading import Lock
from typing import Any, Set


_init_lock = Lock()
_db_initialized = False
_db_write_lock = Lock()


_MARKET_INTEL_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS discovered_skills (
    skill TEXT PRIMARY KEY,
    first_seen TIMESTAMPTZ NOT NULL DEFAULT now(),
    occurrences INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_discovered_skills_occurrences
ON discovered_skills (occurrences DESC, skill ASC);
""".strip()


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _database_url() -> str:
    database_url = _clean_text(os.environ.get("DATABASE_URL"))
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is required for Postgres-backed skill DB."
        )
    return database_url


def _sql_quote_text(value: Any) -> str:
    return "'" + str(value or "").replace("'", "''") + "'"


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


def _run_psql_json_query(sql: str) -> dict[str, Any]:
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


def init_skill_db() -> None:
    global _db_initialized

    with _init_lock:
        if _db_initialized:
            return

        _run_psql_statement(_MARKET_INTEL_SCHEMA_SQL)
        _db_initialized = True


def get_existing_skills() -> Set[str]:
    init_skill_db()

    sql = """
WITH skill_rows AS (
    SELECT skill
    FROM discovered_skills
    ORDER BY skill ASC
)
SELECT json_build_object(
    'skills', COALESCE((SELECT json_agg(skill) FROM skill_rows), '[]'::json)
);
""".strip()

    payload = _run_psql_json_query(sql)
    return {
        _clean_text(skill)
        for skill in list(payload.get("skills", []) or [])
        if _clean_text(skill)
    }


def insert_or_update_skill(skill) -> None:
    safe_skill = _clean_text(skill).lower()
    if not safe_skill:
        return

    init_skill_db()

    sql = f"""
INSERT INTO discovered_skills (
    skill,
    first_seen,
    occurrences
)
VALUES (
    {_sql_quote_text(safe_skill)},
    now(),
    1
)
ON CONFLICT (skill) DO UPDATE SET
    occurrences = discovered_skills.occurrences + 1;
""".strip()

    with _db_write_lock:
        _run_psql_statement(sql)
