from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict


_init_lock = Lock()
_db_initialized = False
_db_write_lock = Lock()


_PIPELINE_METRICS_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    runtime_seconds DOUBLE PRECISION NOT NULL DEFAULT 0,
    scraped INTEGER NOT NULL DEFAULT 0,
    filtered INTEGER NOT NULL DEFAULT 0,
    deduped INTEGER NOT NULL DEFAULT 0,
    ranked INTEGER NOT NULL DEFAULT 0,
    details INTEGER NOT NULL DEFAULT 0,
    new_jobs INTEGER NOT NULL DEFAULT 0,
    drop_pct DOUBLE PRECISION NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_timestamp
ON pipeline_runs (timestamp DESC);

CREATE TABLE IF NOT EXISTS ats_metrics (
    id BIGSERIAL PRIMARY KEY,
    run_id BIGINT NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
    stage TEXT NOT NULL,
    ats TEXT NOT NULL,
    count INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_ats_metrics_run_stage
ON ats_metrics (run_id, stage);

CREATE TABLE IF NOT EXISTS company_hiring_metrics (
    id BIGSERIAL PRIMARY KEY,
    run_id BIGINT NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
    company TEXT NOT NULL,
    ats TEXT NOT NULL,
    job_count INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_company_hiring_metrics_run
ON company_hiring_metrics (run_id);

CREATE INDEX IF NOT EXISTS idx_company_hiring_metrics_company_ats
ON company_hiring_metrics (company, ats);
""".strip()


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _database_url() -> str:
    database_url = _clean_text(os.environ.get("DATABASE_URL"))
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is required for Postgres-backed metrics store."
        )
    return database_url


def _sql_quote_text(value: Any) -> str:
    return "'" + str(value or "").replace("'", "''") + "'"


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


def init_metrics_db() -> None:
    global _db_initialized

    with _init_lock:
        if _db_initialized:
            return

        _run_psql_statement(_PIPELINE_METRICS_SCHEMA_SQL)
        _db_initialized = True


def get_last_run():
    init_metrics_db()

    sql = """
SELECT json_build_object(
    'found', EXISTS (
        SELECT 1
        FROM pipeline_runs
    ),
    'run', COALESCE((
        SELECT json_build_object(
            'run_id', id,
            'scraped', scraped,
            'filtered', filtered,
            'deduped', deduped,
            'ranked', ranked,
            'details', details,
            'drop_pct', drop_pct
        )
        FROM pipeline_runs
        ORDER BY id DESC
        LIMIT 1
    ), '{}'::json)
);
""".strip()

    payload = _run_psql_json_query(sql)

    if not bool(payload.get("found", False)):
        return None

    row = dict(payload.get("run", {}) or {})
    return {
        "run_id": int(row.get("run_id", 0) or 0),
        "scraped": int(row.get("scraped", 0) or 0),
        "filtered": int(row.get("filtered", 0) or 0),
        "deduped": int(row.get("deduped", 0) or 0),
        "ranked": int(row.get("ranked", 0) or 0),
        "details": int(row.get("details", 0) or 0),
        "drop_pct": float(row.get("drop_pct", 0) or 0),
    }


def get_last_ats_counts(stage):
    init_metrics_db()

    safe_stage = _clean_text(stage)

    sql = f"""
WITH latest_run AS (
    SELECT id
    FROM pipeline_runs
    ORDER BY id DESC
    LIMIT 1
),
metric_rows AS (
    SELECT ats, count
    FROM ats_metrics
    WHERE run_id = (SELECT id FROM latest_run)
      AND stage = {_sql_quote_text(safe_stage)}
)
SELECT json_build_object(
    'rows', COALESCE((SELECT json_agg(row_to_json(metric_rows)) FROM metric_rows), '[]'::json)
);
""".strip()

    payload = _run_psql_json_query(sql)

    return {
        _clean_text(row.get("ats")): int(row.get("count", 0) or 0)
        for row in list(payload.get("rows", []) or [])
        if _clean_text(row.get("ats"))
    }


def record_pipeline_run(runtime, scraped, filtered, deduped, ranked, details, new_jobs, drop_pct):
    init_metrics_db()

    timestamp = datetime.now(timezone.utc).isoformat()

    sql = f"""
WITH inserted AS (
    INSERT INTO pipeline_runs (
        timestamp,
        runtime_seconds,
        scraped,
        filtered,
        deduped,
        ranked,
        details,
        new_jobs,
        drop_pct
    )
    VALUES (
        {_sql_quote_text(timestamp)}::timestamptz,
        {float(runtime or 0)},
        {int(scraped or 0)},
        {int(filtered or 0)},
        {int(deduped or 0)},
        {int(ranked or 0)},
        {int(details or 0)},
        {int(new_jobs or 0)},
        {float(drop_pct or 0)}
    )
    RETURNING id
)
SELECT json_build_object(
    'run_id', (SELECT id FROM inserted)
);
""".strip()

    with _db_write_lock:
        payload = _run_psql_json_query(sql)

    return int(payload.get("run_id", 0) or 0)


def record_ats_counts(run_id, stage, counts):
    init_metrics_db()

    safe_run_id = int(run_id or 0)
    safe_stage = _clean_text(stage)

    if safe_run_id <= 0 or not isinstance(counts, dict) or not counts:
        return

    values = []
    for ats, count in counts.items():
        safe_ats = _clean_text(ats)
        if not safe_ats:
            continue

        values.append(
            "("
            + ", ".join(
                [
                    str(safe_run_id),
                    _sql_quote_text(safe_stage),
                    _sql_quote_text(safe_ats),
                    str(int(count or 0)),
                ]
            )
            + ")"
        )

    if not values:
        return

    sql = f"""
INSERT INTO ats_metrics (
    run_id,
    stage,
    ats,
    count
)
VALUES
{",\n".join(values)};
""".strip()

    with _db_write_lock:
        _run_psql_statement(sql)


def record_company_hiring(run_id, jobs):
    init_metrics_db()

    safe_run_id = int(run_id or 0)
    if safe_run_id <= 0:
        return

    company_counts = {}

    for job in jobs:
        company = _clean_text(job.get("company"))
        ats = _clean_text(job.get("source"))

        if not company or not ats:
            continue

        key = (company, ats)
        company_counts[key] = company_counts.get(key, 0) + 1

    if not company_counts:
        return

    values = []
    for (company, ats), count in company_counts.items():
        values.append(
            "("
            + ", ".join(
                [
                    str(safe_run_id),
                    _sql_quote_text(company),
                    _sql_quote_text(ats),
                    str(int(count or 0)),
                ]
            )
            + ")"
        )

    sql = f"""
INSERT INTO company_hiring_metrics (
    run_id,
    company,
    ats,
    job_count
)
VALUES
{",\n".join(values)};
""".strip()

    with _db_write_lock:
        _run_psql_statement(sql)


def get_hiring_momentum():
    init_metrics_db()

    sql = """
WITH latest AS (
    SELECT id
    FROM pipeline_runs
    ORDER BY id DESC
    LIMIT 1
),
previous AS (
    SELECT id
    FROM pipeline_runs
    ORDER BY id DESC
    LIMIT 1 OFFSET 1
),
momentum_rows AS (
    SELECT
        c1.company,
        c1.ats,
        c1.job_count AS current_jobs,
        COALESCE(c2.job_count, 0) AS previous_jobs,
        c1.job_count - COALESCE(c2.job_count, 0) AS delta
    FROM company_hiring_metrics c1
    LEFT JOIN company_hiring_metrics c2
        ON c1.company = c2.company
        AND c1.ats = c2.ats
        AND c2.run_id = (SELECT id FROM previous)
    WHERE c1.run_id = (SELECT id FROM latest)
      AND c1.job_count - COALESCE(c2.job_count, 0) <> 0
    ORDER BY delta DESC
)
SELECT json_build_object(
    'rows', COALESCE((SELECT json_agg(row_to_json(momentum_rows)) FROM momentum_rows), '[]'::json)
);
""".strip()

    payload = _run_psql_json_query(sql)

    return [
        (
            _clean_text(row.get("company")),
            _clean_text(row.get("ats")),
            int(row.get("previous_jobs", 0) or 0),
            int(row.get("current_jobs", 0) or 0),
            int(row.get("delta", 0) or 0),
        )
        for row in list(payload.get("rows", []) or [])
    ]
