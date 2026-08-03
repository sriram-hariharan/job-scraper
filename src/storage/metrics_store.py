from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict
from urllib.parse import urlsplit

from src.discovery.crawl_scheduler import ACQUISITION_FAILURE_REASONS


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

CREATE TABLE IF NOT EXISTS scraper_source_health_metrics (
    id BIGSERIAL PRIMARY KEY,
    run_id BIGINT NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
    source VARCHAR(64) NOT NULL,
    company VARCHAR(256) NOT NULL DEFAULT '',
    acquisition_status VARCHAR(16) NOT NULL DEFAULT '',
    reason_code VARCHAR(64) NOT NULL DEFAULT '',
    request_count INTEGER NOT NULL DEFAULT 0,
    response_status_counts JSONB NOT NULL DEFAULT '{}'::jsonb,
    retry_count INTEGER NOT NULL DEFAULT 0,
    page_count INTEGER,
    partial_result_count INTEGER NOT NULL DEFAULT 0,
    raw_job_count INTEGER,
    normalized_job_count INTEGER NOT NULL DEFAULT 0,
    filter_drop_count INTEGER NOT NULL DEFAULT 0,
    duplicate_drop_count INTEGER NOT NULL DEFAULT 0,
    final_retained_job_count INTEGER NOT NULL DEFAULT 0,
    canonical_url_present_count INTEGER NOT NULL DEFAULT 0,
    canonical_url_missing_count INTEGER NOT NULL DEFAULT 0,
    timestamp_present_count INTEGER NOT NULL DEFAULT 0,
    timestamp_missing_count INTEGER NOT NULL DEFAULT 0,
    description_present_count INTEGER NOT NULL DEFAULT 0,
    description_missing_count INTEGER NOT NULL DEFAULT 0,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER,
    schedule_advanced BOOLEAN NOT NULL DEFAULT FALSE,
    health VARCHAR(16) NOT NULL DEFAULT 'unknown',
    UNIQUE (run_id, source, company)
);

CREATE INDEX IF NOT EXISTS idx_scraper_source_health_run
ON scraper_source_health_metrics (run_id, source, company);
""".strip()


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _bounded_text(value: Any, limit: int) -> str:
    return " ".join(str(value or "").split())[:limit]


def _safe_identity(value: Any, limit: int) -> str:
    text = _bounded_text(value, limit * 2)
    if "://" in text:
        parsed = urlsplit(text)
        text = f"{parsed.hostname or ''}{parsed.path or ''}"
    return _bounded_text(text, limit)


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


def _metric_value(metric, name, default=None):
    if isinstance(metric, dict):
        return metric.get(name, default)
    return getattr(metric, name, default)


def _optional_nonnegative_int(value):
    if value is None:
        return None
    return max(0, int(value or 0))


def _source_health_row(metric):
    status = _bounded_text(_metric_value(metric, "acquisition_status", ""), 16)
    if status not in {"", "SUCCESS", "EMPTY", "PARTIAL", "FAILED"}:
        status = ""
    reason = _bounded_text(_metric_value(metric, "reason_code", ""), 64)
    if reason not in ACQUISITION_FAILURE_REASONS:
        reason = ""
    health = _bounded_text(_metric_value(metric, "health", "unknown"), 16)
    if health not in {"healthy", "degraded", "unhealthy", "unknown"}:
        health = "unknown"

    response_counts = {}
    for code, count in _metric_value(metric, "response_status_counts", ()) or ():
        safe_code = int(code)
        if 100 <= safe_code <= 599:
            response_counts[str(safe_code)] = max(0, int(count or 0))

    def bounded_timestamp(name):
        value = _metric_value(metric, name)
        if value is None:
            return ""
        if hasattr(value, "isoformat"):
            value = value.isoformat()
        return _bounded_text(value, 64)

    return {
        "source": _safe_identity(_metric_value(metric, "source", ""), 64),
        "company": _safe_identity(_metric_value(metric, "company", ""), 256),
        "acquisition_status": status,
        "reason_code": reason,
        "request_count": max(0, int(_metric_value(metric, "request_count", 0) or 0)),
        "response_status_counts": response_counts,
        "retry_count": max(0, int(_metric_value(metric, "retry_count", 0) or 0)),
        "page_count": _optional_nonnegative_int(_metric_value(metric, "page_count")),
        "partial_result_count": max(0, int(_metric_value(metric, "partial_result_count", 0) or 0)),
        "raw_job_count": _optional_nonnegative_int(_metric_value(metric, "raw_job_count")),
        "normalized_job_count": max(0, int(_metric_value(metric, "normalized_job_count", 0) or 0)),
        "filter_drop_count": max(0, int(_metric_value(metric, "filter_drop_count", 0) or 0)),
        "duplicate_drop_count": max(0, int(_metric_value(metric, "duplicate_drop_count", 0) or 0)),
        "final_retained_job_count": max(0, int(_metric_value(metric, "final_retained_job_count", 0) or 0)),
        "canonical_url_present_count": max(0, int(_metric_value(metric, "canonical_url_present_count", 0) or 0)),
        "canonical_url_missing_count": max(0, int(_metric_value(metric, "canonical_url_missing_count", 0) or 0)),
        "timestamp_present_count": max(0, int(_metric_value(metric, "timestamp_present_count", 0) or 0)),
        "timestamp_missing_count": max(0, int(_metric_value(metric, "timestamp_missing_count", 0) or 0)),
        "description_present_count": max(0, int(_metric_value(metric, "description_present_count", 0) or 0)),
        "description_missing_count": max(0, int(_metric_value(metric, "description_missing_count", 0) or 0)),
        "started_at": bounded_timestamp("started_at"),
        "completed_at": bounded_timestamp("completed_at"),
        "duration_ms": _optional_nonnegative_int(_metric_value(metric, "duration_ms")),
        "schedule_advanced": bool(_metric_value(metric, "schedule_advanced", False)),
        "health": health,
    }


def record_source_health_metrics(run_id, metrics):
    init_metrics_db()
    safe_run_id = int(run_id or 0)
    if safe_run_id <= 0:
        return 0

    rows = [_source_health_row(metric) for metric in metrics or ()]
    rows = [row for row in rows if row["source"]]
    rows.sort(key=lambda row: (row["source"], row["company"]))
    if not rows:
        return 0

    values = []
    for row in rows:
        nullable = lambda value, cast="": (
            "NULL" if value in {None, ""} else f"{_sql_quote_text(value)}{cast}"
        )
        page_count = "NULL" if row["page_count"] is None else str(row["page_count"])
        raw_job_count = "NULL" if row["raw_job_count"] is None else str(row["raw_job_count"])
        duration_ms = "NULL" if row["duration_ms"] is None else str(min(row["duration_ms"], 86_400_000))
        values.append(
            "(" + ", ".join([
                str(safe_run_id),
                _sql_quote_text(row["source"]),
                _sql_quote_text(row["company"]),
                _sql_quote_text(row["acquisition_status"]),
                _sql_quote_text(row["reason_code"]),
                str(row["request_count"]),
                _sql_quote_text(json.dumps(row["response_status_counts"], sort_keys=True)) + "::jsonb",
                str(row["retry_count"]),
                page_count,
                str(row["partial_result_count"]),
                raw_job_count,
                str(row["normalized_job_count"]),
                str(row["filter_drop_count"]),
                str(row["duplicate_drop_count"]),
                str(row["final_retained_job_count"]),
                str(row["canonical_url_present_count"]),
                str(row["canonical_url_missing_count"]),
                str(row["timestamp_present_count"]),
                str(row["timestamp_missing_count"]),
                str(row["description_present_count"]),
                str(row["description_missing_count"]),
                nullable(row["started_at"], "::timestamptz"),
                nullable(row["completed_at"], "::timestamptz"),
                duration_ms,
                "TRUE" if row["schedule_advanced"] else "FALSE",
                _sql_quote_text(row["health"]),
            ]) + ")"
        )

    sql = f"""
INSERT INTO scraper_source_health_metrics (
    run_id, source, company, acquisition_status, reason_code,
    request_count, response_status_counts, retry_count, page_count,
    partial_result_count, raw_job_count, normalized_job_count,
    filter_drop_count, duplicate_drop_count, final_retained_job_count,
    canonical_url_present_count, canonical_url_missing_count,
    timestamp_present_count, timestamp_missing_count,
    description_present_count, description_missing_count,
    started_at, completed_at, duration_ms, schedule_advanced, health
)
VALUES
{",\n".join(values)}
ON CONFLICT (run_id, source, company) DO UPDATE SET
    acquisition_status = EXCLUDED.acquisition_status,
    reason_code = EXCLUDED.reason_code,
    request_count = EXCLUDED.request_count,
    response_status_counts = EXCLUDED.response_status_counts,
    retry_count = EXCLUDED.retry_count,
    page_count = EXCLUDED.page_count,
    partial_result_count = EXCLUDED.partial_result_count,
    raw_job_count = EXCLUDED.raw_job_count,
    normalized_job_count = EXCLUDED.normalized_job_count,
    filter_drop_count = EXCLUDED.filter_drop_count,
    duplicate_drop_count = EXCLUDED.duplicate_drop_count,
    final_retained_job_count = EXCLUDED.final_retained_job_count,
    canonical_url_present_count = EXCLUDED.canonical_url_present_count,
    canonical_url_missing_count = EXCLUDED.canonical_url_missing_count,
    timestamp_present_count = EXCLUDED.timestamp_present_count,
    timestamp_missing_count = EXCLUDED.timestamp_missing_count,
    description_present_count = EXCLUDED.description_present_count,
    description_missing_count = EXCLUDED.description_missing_count,
    started_at = EXCLUDED.started_at,
    completed_at = EXCLUDED.completed_at,
    duration_ms = EXCLUDED.duration_ms,
    schedule_advanced = EXCLUDED.schedule_advanced,
    health = EXCLUDED.health;
""".strip()
    with _db_write_lock:
        _run_psql_statement(sql)
    return len(rows)


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
