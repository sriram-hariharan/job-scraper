from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable

from src.storage.user_pipeline.store import (
    _run_psql_json_stdin_query,
    _sql_jsonb,
    _sql_quote_text,
)

DEFAULT_BULK_GENERATION_SCHEMA_SQL_PATH = Path("src/storage/bulk_generation/schema.sql")
ACTIVE_STATUSES = ("queued", "running", "stop_requested")
TERMINAL_STATUSES = ("stopped", "completed", "failed")
_ADVISORY_LOCK_ID = 927461337


def _clean(value: Any, *, maximum: int = 512) -> str:
    return str(value or "").strip()[:maximum]


def _required(value: Any, label: str) -> str:
    clean = _clean(value)
    if not clean:
        raise ValueError(f"{label} is required.")
    return clean


def bulk_generation_schema_sql_text(path: Path = DEFAULT_BULK_GENERATION_SCHEMA_SQL_PATH) -> str:
    sql = Path(path).read_text(encoding="utf-8")
    if not sql.strip():
        raise ValueError(f"Bulk generation schema SQL is empty: {path}")
    return sql


def _prefix(ensure_schema: bool) -> str:
    return bulk_generation_schema_sql_text() + "\n\n" if ensure_schema else ""


def _query(sql: str, **kwargs: Any) -> Dict[str, Any]:
    return _run_psql_json_stdin_query(sql=sql, **kwargs)


def _response(payload: Dict[str, Any], **values: Any) -> Dict[str, Any]:
    return {
        "ok": True,
        **values,
        "command": payload.get("command", []),
        "command_text": payload.get("command_text", ""),
    }


def create_bulk_generation_run_postgres_payload(
    *, owner_user_id: str, run_id: str, pipeline_run_id: str,
    items: Iterable[Dict[str, Any]], config_json: Dict[str, Any] | None = None,
    database_url: str = "", database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql", print_only: bool = False, ensure_schema: bool = True,
) -> Dict[str, Any]:
    owner = _required(owner_user_id, "owner_user_id")
    safe_run = _required(run_id, "run_id")
    pipeline_run = _required(pipeline_run_id, "pipeline_run_id")
    rows = [dict(item or {}) for item in items]
    if not 1 <= len(rows) <= 500:
        raise ValueError("Bulk Generate requires between 1 and 500 items.")
    identities: set[str] = set()
    normalized = []
    for index, row in enumerate(rows, start=1):
        identity = _required(row.get("job_identity"), "job_identity")
        if identity in identities:
            raise ValueError("Duplicate Bulk Generate candidate identity.")
        identities.add(identity)
        normalized.append({
            "sequence": index,
            "job_identity": identity,
            "job_doc_id": _clean(row.get("job_doc_id")),
            "queue_rank": _clean(row.get("queue_rank"), maximum=64),
            "selected_resume": _required(row.get("selected_resume"), "selected_resume"),
            "job_label": _clean(row.get("job_label"), maximum=240),
        })
    config = dict(config_json or {})
    values = ",\n".join(
        "(" + ", ".join([
            _sql_quote_text(safe_run), _sql_quote_text(owner), str(row["sequence"]),
            _sql_quote_text(row["job_identity"]), _sql_quote_text(row["job_doc_id"]),
            _sql_quote_text(row["queue_rank"]), _sql_quote_text(row["selected_resume"]),
            _sql_quote_text(row["job_label"]),
        ]) + ")" for row in normalized
    )
    sql = _prefix(ensure_schema) + f"""
WITH lock AS (SELECT pg_advisory_xact_lock({_ADVISORY_LOCK_ID}) AS locked),
existing_bulk AS (
    SELECT run_id, status FROM bulk_generation_runs
    WHERE owner_user_id = {_sql_quote_text(owner)}
      AND status IN ('queued', 'running', 'stop_requested') LIMIT 1
),
existing_pipeline AS (
    SELECT run_id, status FROM user_pipeline_active_runs
    WHERE owner_user_id = {_sql_quote_text(owner)}
      AND status = 'running' AND expires_at >= now() LIMIT 1
),
inserted_run AS (
    INSERT INTO bulk_generation_runs (
        run_id, owner_user_id, pipeline_run_id, status, total_count, config_json
    )
    SELECT {_sql_quote_text(safe_run)}, {_sql_quote_text(owner)},
           {_sql_quote_text(pipeline_run)}, 'queued', {len(normalized)}, {_sql_jsonb(config)}
    WHERE (SELECT COUNT(*) FROM lock) = 1
      AND NOT EXISTS (SELECT 1 FROM existing_bulk)
      AND NOT EXISTS (SELECT 1 FROM existing_pipeline)
    ON CONFLICT DO NOTHING RETURNING run_id
),
inserted_items AS (
    INSERT INTO bulk_generation_items (
        run_id, owner_user_id, sequence, job_identity, job_doc_id,
        queue_rank, selected_resume, job_label
    )
    SELECT * FROM (VALUES {values}) AS requested(
        run_id, owner_user_id, sequence, job_identity, job_doc_id,
        queue_rank, selected_resume, job_label
    ) WHERE EXISTS (SELECT 1 FROM inserted_run)
    RETURNING sequence
)
SELECT json_build_object(
    'created', EXISTS (SELECT 1 FROM inserted_run),
    'reason', CASE
        WHEN EXISTS (SELECT 1 FROM inserted_run) THEN ''
        WHEN EXISTS (SELECT 1 FROM existing_bulk) THEN 'bulk_generation_in_progress'
        WHEN EXISTS (SELECT 1 FROM existing_pipeline) THEN 'live_pipeline_in_progress'
        ELSE 'admission_conflict' END,
    'item_count', (SELECT COUNT(*) FROM inserted_items),
    'existing_run', COALESCE((SELECT row_to_json(existing_bulk) FROM existing_bulk), '{{}}'::json)
);
""".strip()
    payload = _query(sql, database_url=database_url, database_url_env=database_url_env,
                     psql_bin=psql_bin, print_only=print_only)
    data = dict(payload.get("data", {}) or {})
    return _response(payload, created=bool(data.get("created")), reason=_clean(data.get("reason")),
                     item_count=int(data.get("item_count") or 0),
                     existing_run=dict(data.get("existing_run", {}) or {}), sql=payload.get("sql", ""))


def get_bulk_generation_run_postgres_payload(
    *, owner_user_id: str, run_id: str = "", active_or_latest: bool = False,
    database_url: str = "", database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql", print_only: bool = False, ensure_schema: bool = True,
) -> Dict[str, Any]:
    owner = _required(owner_user_id, "owner_user_id")
    safe_run = _clean(run_id)
    if not safe_run and not active_or_latest:
        raise ValueError("run_id is required.")
    run_filter = (
        f"run_id = {_sql_quote_text(safe_run)}" if safe_run else
        f"owner_user_id = {_sql_quote_text(owner)}"
    )
    ordering = "ORDER BY (status IN ('queued','running','stop_requested')) DESC, started_at DESC" if not safe_run else ""
    sql = _prefix(ensure_schema) + f"""
WITH selected_run AS (
    SELECT * FROM bulk_generation_runs
    WHERE owner_user_id = {_sql_quote_text(owner)} AND {run_filter}
    {ordering} LIMIT 1
), selected_items AS (
    SELECT i.* FROM bulk_generation_items i
    JOIN selected_run r ON r.run_id = i.run_id
    ORDER BY i.sequence
)
SELECT json_build_object(
    'found', EXISTS (SELECT 1 FROM selected_run),
    'run', COALESCE((SELECT row_to_json(selected_run) FROM selected_run), '{{}}'::json),
    'items', COALESCE((SELECT json_agg(row_to_json(selected_items)) FROM selected_items), '[]'::json)
);
""".strip()
    payload = _query(sql, database_url=database_url, database_url_env=database_url_env,
                     psql_bin=psql_bin, print_only=print_only)
    data = dict(payload.get("data", {}) or {})
    return _response(payload, found=bool(data.get("found")), run=dict(data.get("run", {}) or {}),
                     items=list(data.get("items", []) or []), sql=payload.get("sql", ""))


def update_bulk_generation_worker_postgres_payload(
    *, owner_user_id: str, run_id: str, worker_pid: Any, worker_identity: str,
    database_url: str = "", database_url_env: str = "DATABASE_URL", psql_bin: str = "psql",
    print_only: bool = False, ensure_schema: bool = True,
) -> Dict[str, Any]:
    owner, safe_run = _required(owner_user_id, "owner_user_id"), _required(run_id, "run_id")
    sql = _prefix(ensure_schema) + f"""
WITH updated AS (
 UPDATE bulk_generation_runs SET status=CASE WHEN stop_requested THEN 'stop_requested' ELSE 'running' END,
 worker_pid={_sql_quote_text(worker_pid)},
 worker_identity={_sql_quote_text(_clean(worker_identity))}, updated_at=now()
 WHERE owner_user_id={_sql_quote_text(owner)} AND run_id={_sql_quote_text(safe_run)}
   AND status IN ('queued','stop_requested') AND worker_pid='' RETURNING run_id
) SELECT json_build_object('updated', EXISTS (SELECT 1 FROM updated));
""".strip()
    payload = _query(sql, database_url=database_url, database_url_env=database_url_env,
                     psql_bin=psql_bin, print_only=print_only)
    return _response(payload, updated=bool(dict(payload.get("data", {}) or {}).get("updated")), sql=payload.get("sql", ""))


def request_bulk_generation_stop_postgres_payload(
    *, owner_user_id: str, run_id: str,
    database_url: str = "", database_url_env: str = "DATABASE_URL", psql_bin: str = "psql",
    print_only: bool = False, ensure_schema: bool = True,
) -> Dict[str, Any]:
    owner, safe_run = _required(owner_user_id, "owner_user_id"), _required(run_id, "run_id")
    sql = _prefix(ensure_schema) + f"""
WITH selected AS (
 SELECT status FROM bulk_generation_runs WHERE owner_user_id={_sql_quote_text(owner)}
 AND run_id={_sql_quote_text(safe_run)} FOR UPDATE
), updated AS (
 UPDATE bulk_generation_runs SET stop_requested=TRUE,
 status=CASE WHEN status IN ('queued','running') THEN 'stop_requested' ELSE status END,
 updated_at=CASE WHEN status IN ('queued','running') THEN now() ELSE updated_at END
 WHERE owner_user_id={_sql_quote_text(owner)} AND run_id={_sql_quote_text(safe_run)}
 RETURNING status, stop_requested
) SELECT json_build_object('found', EXISTS (SELECT 1 FROM selected),
 'run', COALESCE((SELECT row_to_json(updated) FROM updated), '{{}}'::json));
""".strip()
    payload = _query(sql, database_url=database_url, database_url_env=database_url_env,
                     psql_bin=psql_bin, print_only=print_only)
    data = dict(payload.get("data", {}) or {})
    return _response(payload, found=bool(data.get("found")), run=dict(data.get("run", {}) or {}), sql=payload.get("sql", ""))


def start_bulk_generation_item_postgres_payload(
    *, owner_user_id: str, run_id: str, sequence: int,
    database_url: str = "", database_url_env: str = "DATABASE_URL", psql_bin: str = "psql",
    print_only: bool = False, ensure_schema: bool = True,
) -> Dict[str, Any]:
    owner, safe_run, seq = _required(owner_user_id, "owner_user_id"), _required(run_id, "run_id"), int(sequence)
    sql = _prefix(ensure_schema) + f"""
WITH item AS (
 UPDATE bulk_generation_items SET status='running', started_at=now()
 WHERE owner_user_id={_sql_quote_text(owner)} AND run_id={_sql_quote_text(safe_run)}
 AND sequence={seq} AND status='pending' RETURNING job_identity
), updated AS (
 UPDATE bulk_generation_runs SET current_sequence={seq},
 current_job_identity=COALESCE((SELECT job_identity FROM item), ''), updated_at=now()
 WHERE owner_user_id={_sql_quote_text(owner)} AND run_id={_sql_quote_text(safe_run)}
 AND status IN ('running','stop_requested') AND EXISTS (SELECT 1 FROM item) RETURNING run_id
) SELECT json_build_object('started', EXISTS (SELECT 1 FROM updated));
""".strip()
    payload = _query(sql, database_url=database_url, database_url_env=database_url_env,
                     psql_bin=psql_bin, print_only=print_only)
    return _response(payload, started=bool(dict(payload.get("data", {}) or {}).get("started")), sql=payload.get("sql", ""))


def finish_bulk_generation_item_postgres_payload(
    *, owner_user_id: str, run_id: str, sequence: int, succeeded: bool,
    outcome: str = "", error_category: str = "", error_message: str = "",
    database_url: str = "", database_url_env: str = "DATABASE_URL", psql_bin: str = "psql",
    print_only: bool = False, ensure_schema: bool = True,
) -> Dict[str, Any]:
    owner, safe_run, seq = _required(owner_user_id, "owner_user_id"), _required(run_id, "run_id"), int(sequence)
    item_status = "succeeded" if succeeded else "needs_attention"
    sql = _prefix(ensure_schema) + f"""
WITH item AS (
 UPDATE bulk_generation_items SET status={_sql_quote_text(item_status)},
 outcome={_sql_quote_text(_clean(outcome, maximum=64))},
 error_category={_sql_quote_text(_clean(error_category, maximum=80))},
 error_message={_sql_quote_text(_clean(error_message, maximum=500))}, finished_at=now()
 WHERE owner_user_id={_sql_quote_text(owner)} AND run_id={_sql_quote_text(safe_run)}
 AND sequence={seq} AND status='running' RETURNING sequence
), updated AS (
 UPDATE bulk_generation_runs SET completed_count=completed_count + 1,
 succeeded_count=succeeded_count + {1 if succeeded else 0},
 needs_attention_count=needs_attention_count + {0 if succeeded else 1},
 current_sequence=NULL, current_job_identity='', updated_at=now()
 WHERE owner_user_id={_sql_quote_text(owner)} AND run_id={_sql_quote_text(safe_run)}
 AND EXISTS (SELECT 1 FROM item) RETURNING completed_count
) SELECT json_build_object('finished', EXISTS (SELECT 1 FROM updated));
""".strip()
    payload = _query(sql, database_url=database_url, database_url_env=database_url_env,
                     psql_bin=psql_bin, print_only=print_only)
    return _response(payload, finished=bool(dict(payload.get("data", {}) or {}).get("finished")), sql=payload.get("sql", ""))


def finish_bulk_generation_run_postgres_payload(
    *, owner_user_id: str, run_id: str, status: str,
    error_category: str = "", error_message: str = "",
    database_url: str = "", database_url_env: str = "DATABASE_URL", psql_bin: str = "psql",
    print_only: bool = False, ensure_schema: bool = True,
) -> Dict[str, Any]:
    owner, safe_run = _required(owner_user_id, "owner_user_id"), _required(run_id, "run_id")
    terminal = _clean(status, maximum=32)
    if terminal not in TERMINAL_STATUSES:
        raise ValueError("Bulk Generate terminal status is invalid.")
    sql = _prefix(ensure_schema) + f"""
WITH updated AS (
 UPDATE bulk_generation_runs SET status={_sql_quote_text(terminal)}, current_sequence=NULL,
 current_job_identity='', error_category={_sql_quote_text(_clean(error_category, maximum=80))},
 error_message={_sql_quote_text(_clean(error_message, maximum=500))}, updated_at=now(), finished_at=now()
 WHERE owner_user_id={_sql_quote_text(owner)} AND run_id={_sql_quote_text(safe_run)}
 AND status IN ('queued','running','stop_requested') RETURNING run_id
) SELECT json_build_object('finished', EXISTS (SELECT 1 FROM updated));
""".strip()
    payload = _query(sql, database_url=database_url, database_url_env=database_url_env,
                     psql_bin=psql_bin, print_only=print_only)
    return _response(payload, finished=bool(dict(payload.get("data", {}) or {}).get("finished")), sql=payload.get("sql", ""))


def get_bulk_generation_pipeline_results_postgres_payload(
    *, owner_user_id: str, pipeline_run_id: str,
    database_url: str = "", database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql", print_only: bool = False, ensure_schema: bool = True,
) -> Dict[str, Any]:
    """Latest Bulk Generate attempt per job for one owner's pipeline run.

    Read-only history view over the existing run/item tables. Every attempt for
    the pipeline is considered, so a later subset re-run replaces only the jobs
    it touched and never hides the earlier attempts for the other jobs. Ranking
    is fully tie-broken so the "latest attempt" is deterministic.
    """
    owner = _required(owner_user_id, "owner_user_id")
    pipeline = _required(pipeline_run_id, "pipeline_run_id")
    sql = _prefix(ensure_schema) + f"""
WITH pipeline_runs AS (
    -- Must project every column the latest_run CTE below consumes: it selects
    -- from this CTE, not from the base table.
    SELECT run_id, status, total_count, completed_count, succeeded_count,
           needs_attention_count, started_at, finished_at
    FROM bulk_generation_runs
    WHERE owner_user_id = {_sql_quote_text(owner)}
      AND pipeline_run_id = {_sql_quote_text(pipeline)}
), attempts AS (
    SELECT i.*, r.started_at AS run_started_at, r.status AS run_status
    FROM bulk_generation_items i
    JOIN pipeline_runs r ON r.run_id = i.run_id
    WHERE i.owner_user_id = {_sql_quote_text(owner)}
), ranked AS (
    SELECT a.*,
           COUNT(*) OVER (PARTITION BY a.job_identity) AS attempt_count,
           ROW_NUMBER() OVER (
               PARTITION BY a.job_identity
               ORDER BY a.finished_at DESC NULLS LAST,
                        a.started_at DESC NULLS LAST,
                        a.run_started_at DESC NULLS LAST,
                        a.run_id DESC,
                        a.sequence DESC
           ) AS attempt_rank
    FROM attempts a
), latest AS (
    SELECT run_id, sequence, job_identity, job_doc_id, queue_rank, selected_resume,
           job_label, status, outcome, error_category, error_message,
           started_at, finished_at, attempt_count, run_status
    FROM ranked WHERE attempt_rank = 1
    ORDER BY job_identity
), latest_run AS (
    SELECT run_id, status, total_count, completed_count, succeeded_count,
           needs_attention_count, started_at, finished_at
    FROM pipeline_runs
    ORDER BY started_at DESC, run_id DESC LIMIT 1
)
SELECT json_build_object(
    'found', EXISTS (SELECT 1 FROM pipeline_runs),
    'pipeline_run_id', {_sql_quote_text(pipeline)},
    'run_count', (SELECT COUNT(*) FROM pipeline_runs),
    'latest_run', COALESCE((SELECT row_to_json(latest_run) FROM latest_run), '{{}}'::json),
    'items', COALESCE((SELECT json_agg(row_to_json(latest)) FROM latest), '[]'::json)
);
""".strip()
    payload = _query(sql, database_url=database_url, database_url_env=database_url_env,
                     psql_bin=psql_bin, print_only=print_only)
    data = dict(payload.get("data", {}) or {})
    return _response(
        payload,
        found=bool(data.get("found")),
        pipeline_run_id=pipeline,
        run_count=int(data.get("run_count") or 0),
        latest_run=dict(data.get("latest_run", {}) or {}),
        items=list(data.get("items", []) or []),
        sql=payload.get("sql", ""),
    )
