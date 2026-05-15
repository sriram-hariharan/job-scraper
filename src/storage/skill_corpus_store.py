from __future__ import annotations

import json
import os
import subprocess
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple


_init_lock = Lock()
_db_initialized = False
_db_write_lock = Lock()


_SKILL_CORPUS_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS extracted_skills (
    run_id TEXT NOT NULL,
    company TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL DEFAULT '',
    skill TEXT NOT NULL,
    skill_type TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_extracted_skills_skill
ON extracted_skills (skill);

CREATE INDEX IF NOT EXISTS idx_extracted_skills_run_id
ON extracted_skills (run_id);

CREATE TABLE IF NOT EXISTS llm_skill_cache (
    cache_key TEXT PRIMARY KEY,
    model TEXT NOT NULL,
    required_skills_json JSONB NOT NULL,
    preferred_skills_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_llm_skill_cache_model
ON llm_skill_cache (model);

CREATE TABLE IF NOT EXISTS llm_job_eval_cache (
    cache_key TEXT PRIMARY KEY,
    model TEXT NOT NULL,
    evaluation_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_llm_job_eval_cache_model
ON llm_job_eval_cache (model);
""".strip()


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _database_url() -> str:
    database_url = _clean_text(os.environ.get("DATABASE_URL"))
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is required for Postgres-backed skill corpus store."
        )
    return database_url


def _sql_quote_text(value: Any) -> str:
    return "'" + str(value or "").replace("'", "''") + "'"


def _sql_jsonb(value: Any) -> str:
    return (
        _sql_quote_text(
            json.dumps(
                value,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        + "::jsonb"
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


def init_db() -> None:
    global _db_initialized

    with _init_lock:
        if _db_initialized:
            return

        _run_psql_statement(_SKILL_CORPUS_SCHEMA_SQL)
        _db_initialized = True


def get_cached_llm_skills(cache_key: str) -> Optional[Dict[str, List[str]]]:
    safe_cache_key = _clean_text(cache_key)
    if not safe_cache_key:
        return None

    init_db()

    sql = f"""
SELECT json_build_object(
    'found', EXISTS (
        SELECT 1
        FROM llm_skill_cache
        WHERE cache_key = {_sql_quote_text(safe_cache_key)}
    ),
    'payload', COALESCE((
        SELECT json_build_object(
            'required_skills', required_skills_json,
            'preferred_skills', preferred_skills_json
        )
        FROM llm_skill_cache
        WHERE cache_key = {_sql_quote_text(safe_cache_key)}
        LIMIT 1
    ), '{{}}'::json)
);
""".strip()

    payload = _run_psql_json_query(sql)

    if not bool(payload.get("found", False)):
        return None

    data = dict(payload.get("payload", {}) or {})
    return {
        "required_skills": list(data.get("required_skills", []) or []),
        "preferred_skills": list(data.get("preferred_skills", []) or []),
    }


def store_cached_llm_skills(
    cache_key: str,
    model: str,
    required_skills: List[str],
    preferred_skills: List[str],
) -> None:
    safe_cache_key = _clean_text(cache_key)
    if not safe_cache_key:
        return

    init_db()

    sql = f"""
INSERT INTO llm_skill_cache (
    cache_key,
    model,
    required_skills_json,
    preferred_skills_json,
    created_at,
    updated_at
)
VALUES (
    {_sql_quote_text(safe_cache_key)},
    {_sql_quote_text(model)},
    {_sql_jsonb(list(required_skills or []))},
    {_sql_jsonb(list(preferred_skills or []))},
    now(),
    now()
)
ON CONFLICT (cache_key) DO UPDATE SET
    model = EXCLUDED.model,
    required_skills_json = EXCLUDED.required_skills_json,
    preferred_skills_json = EXCLUDED.preferred_skills_json,
    updated_at = now();
""".strip()

    with _db_write_lock:
        _run_psql_statement(sql)


def get_cached_job_evaluation(cache_key: str) -> Optional[Dict[str, Any]]:
    safe_cache_key = _clean_text(cache_key)
    if not safe_cache_key:
        return None

    init_db()

    sql = f"""
SELECT json_build_object(
    'found', EXISTS (
        SELECT 1
        FROM llm_job_eval_cache
        WHERE cache_key = {_sql_quote_text(safe_cache_key)}
    ),
    'evaluation', COALESCE((
        SELECT evaluation_json
        FROM llm_job_eval_cache
        WHERE cache_key = {_sql_quote_text(safe_cache_key)}
        LIMIT 1
    ), '{{}}'::jsonb)
);
""".strip()

    payload = _run_psql_json_query(sql)

    if not bool(payload.get("found", False)):
        return None

    return dict(payload.get("evaluation", {}) or {})


def store_cached_job_evaluation(
    cache_key: str,
    model: str,
    evaluation: Dict[str, Any],
) -> None:
    safe_cache_key = _clean_text(cache_key)
    if not safe_cache_key:
        return

    init_db()

    sql = f"""
INSERT INTO llm_job_eval_cache (
    cache_key,
    model,
    evaluation_json,
    created_at,
    updated_at
)
VALUES (
    {_sql_quote_text(safe_cache_key)},
    {_sql_quote_text(model)},
    {_sql_jsonb(dict(evaluation or {}))},
    now(),
    now()
)
ON CONFLICT (cache_key) DO UPDATE SET
    model = EXCLUDED.model,
    evaluation_json = EXCLUDED.evaluation_json,
    updated_at = now();
""".strip()

    with _db_write_lock:
        _run_psql_statement(sql)


def _skill_insert_values(rows: List[Tuple[str, str, str, str, str]]) -> str:
    values = []
    for run_id, company, title, skill, skill_type in rows:
        values.append(
            "("
            + ", ".join(
                [
                    _sql_quote_text(run_id),
                    _sql_quote_text(company),
                    _sql_quote_text(title),
                    _sql_quote_text(skill),
                    _sql_quote_text(skill_type),
                    "now()",
                ]
            )
            + ")"
        )
    return ",\n".join(values)


def store_job_skills(run_id: str, jobs: List[Dict[str, Any]]) -> None:
    init_db()

    safe_run_id = _clean_text(run_id)
    if not safe_run_id:
        return

    rows: List[Tuple[str, str, str, str, str]] = []

    for job in jobs:
        company = _clean_text(job.get("company"))
        title = _clean_text(job.get("title"))

        intel = job.get("intelligence", {}) or {}
        skills = intel.get("skills", {}) or {}

        for skill in skills.get("required", []) or []:
            safe_skill = _clean_text(skill)
            if safe_skill:
                rows.append((safe_run_id, company, title, safe_skill, "required"))

        for skill in skills.get("preferred", []) or []:
            safe_skill = _clean_text(skill)
            if safe_skill:
                rows.append((safe_run_id, company, title, safe_skill, "preferred"))

    if not rows:
        return

    chunk_size = 500

    with _db_write_lock:
        for start in range(0, len(rows), chunk_size):
            chunk = rows[start : start + chunk_size]
            values_sql = _skill_insert_values(chunk)
            sql = f"""
INSERT INTO extracted_skills (
    run_id,
    company,
    title,
    skill,
    skill_type,
    created_at
)
VALUES
{values_sql};
""".strip()
            _run_psql_statement(sql)


def get_top_corpus_skills(limit: int = 100):
    init_db()

    try:
        safe_limit = int(limit)
    except Exception:
        safe_limit = 100

    safe_limit = max(1, min(safe_limit, 10000))

    sql = f"""
WITH skill_rows AS (
    SELECT
        skill,
        COUNT(*)::int AS freq
    FROM extracted_skills
    GROUP BY skill
    ORDER BY freq DESC, skill ASC
    LIMIT {safe_limit}
)
SELECT json_build_object(
    'rows', COALESCE((SELECT json_agg(row_to_json(skill_rows)) FROM skill_rows), '[]'::json)
);
""".strip()

    payload = _run_psql_json_query(sql)

    return [
        (_clean_text(row.get("skill")), int(row.get("freq", 0) or 0))
        for row in list(payload.get("rows", []) or [])
    ]
