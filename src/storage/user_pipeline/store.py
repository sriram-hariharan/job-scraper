from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlsplit, urlunsplit

DEFAULT_USER_PIPELINE_SCHEMA_SQL_PATH = Path("src/storage/user_pipeline/schema.sql")


def _read_sql_artifact(path: Path, label: str) -> str:
    resolved = Path(path)
    if not resolved.exists():
        raise ValueError(f"Missing {label} SQL file: {resolved}")

    sql = resolved.read_text(encoding="utf-8")
    if not sql.strip():
        raise ValueError(f"{label.capitalize()} SQL file is empty: {resolved}")

    return sql


def user_pipeline_table_specs() -> Dict[str, Any]:
    return {
        "user_pipeline_runs": {
            "description": "Owner-scoped live pipeline run state and durable status snapshots.",
            "primary_key": ["run_id"],
            "owner_column": "owner_user_id",
            "columns": [
                {"name": "run_id", "type": "text", "nullable": False},
                {"name": "owner_user_id", "type": "text", "nullable": False},
                {"name": "status", "type": "text", "nullable": False},
                {"name": "current_stage", "type": "text", "nullable": False},
                {"name": "stage_message", "type": "text", "nullable": False},
                {"name": "summary_message", "type": "text", "nullable": False},
                {"name": "return_code", "type": "integer", "nullable": True},
                {"name": "started_at", "type": "timestamptz", "nullable": False},
                {"name": "updated_at", "type": "timestamptz", "nullable": False},
                {"name": "completed_at", "type": "timestamptz", "nullable": True},
                {"name": "config_json", "type": "jsonb", "nullable": False},
                {"name": "status_json", "type": "jsonb", "nullable": False},
                {"name": "error", "type": "text", "nullable": False},
            ],
        },
        "user_seen_jobs": {
            "description": "Owner-scoped seen-job registry replacing shared seen_job_ids files.",
            "primary_key": ["owner_user_id", "seen_key"],
            "owner_column": "owner_user_id",
            "columns": [
                {"name": "owner_user_id", "type": "text", "nullable": False},
                {"name": "seen_key", "type": "text", "nullable": False},
                {"name": "source", "type": "text", "nullable": False},
                {"name": "job_url", "type": "text", "nullable": False},
                {"name": "job_doc_id", "type": "text", "nullable": False},
                {"name": "company", "type": "text", "nullable": False},
                {"name": "title", "type": "text", "nullable": False},
                {"name": "first_seen_at", "type": "timestamptz", "nullable": False},
                {"name": "last_seen_at", "type": "timestamptz", "nullable": False},
                {"name": "first_run_id", "type": "text", "nullable": False},
                {"name": "last_run_id", "type": "text", "nullable": False},
                {"name": "metadata_json", "type": "jsonb", "nullable": False},
            ],
        },
        "user_pipeline_artifacts": {
            "description": "Owner-scoped generated pipeline artifacts stored durably in Postgres.",
            "primary_key": ["artifact_id"],
            "owner_column": "owner_user_id",
            "columns": [
                {"name": "artifact_id", "type": "text", "nullable": False},
                {"name": "owner_user_id", "type": "text", "nullable": False},
                {"name": "run_id", "type": "text", "nullable": False},
                {"name": "artifact_kind", "type": "text", "nullable": False},
                {"name": "artifact_name", "type": "text", "nullable": False},
                {"name": "content_type", "type": "text", "nullable": False},
                {"name": "content_json", "type": "jsonb", "nullable": True},
                {"name": "content_text", "type": "text", "nullable": False},
                {"name": "content_bytes", "type": "bytea", "nullable": True},
                {"name": "created_at", "type": "timestamptz", "nullable": False},
            ],
        },
    }


def render_user_pipeline_schema_sql() -> str:
    return "\n".join(
        [
            "CREATE TABLE IF NOT EXISTS user_pipeline_runs (",
            "    run_id TEXT PRIMARY KEY,",
            "    owner_user_id TEXT NOT NULL REFERENCES auth_users(user_id) ON DELETE CASCADE,",
            "    status TEXT NOT NULL,",
            "    current_stage TEXT NOT NULL DEFAULT '',",
            "    stage_message TEXT NOT NULL DEFAULT '',",
            "    summary_message TEXT NOT NULL DEFAULT '',",
            "    return_code INTEGER,",
            "    started_at TIMESTAMPTZ NOT NULL,",
            "    updated_at TIMESTAMPTZ NOT NULL,",
            "    completed_at TIMESTAMPTZ,",
            "    config_json JSONB NOT NULL DEFAULT '{}'::jsonb,",
            "    status_json JSONB NOT NULL DEFAULT '{}'::jsonb,",
            "    error TEXT NOT NULL DEFAULT ''",
            ");",
            "",
            "CREATE INDEX IF NOT EXISTS idx_user_pipeline_runs_owner_started",
            "ON user_pipeline_runs (owner_user_id, started_at DESC);",
            "",
            "CREATE INDEX IF NOT EXISTS idx_user_pipeline_runs_status_started",
            "ON user_pipeline_runs (status, started_at DESC);",
            "",
            "CREATE INDEX IF NOT EXISTS idx_user_pipeline_runs_owner_status_started",
            "ON user_pipeline_runs (owner_user_id, status, started_at DESC);",
            "",
            "CREATE TABLE IF NOT EXISTS user_seen_jobs (",
            "    owner_user_id TEXT NOT NULL REFERENCES auth_users(user_id) ON DELETE CASCADE,",
            "    seen_key TEXT NOT NULL,",
            "    source TEXT NOT NULL DEFAULT '',",
            "    job_url TEXT NOT NULL DEFAULT '',",
            "    job_doc_id TEXT NOT NULL DEFAULT '',",
            "    company TEXT NOT NULL DEFAULT '',",
            "    title TEXT NOT NULL DEFAULT '',",
            "    first_seen_at TIMESTAMPTZ NOT NULL,",
            "    last_seen_at TIMESTAMPTZ NOT NULL,",
            "    first_run_id TEXT NOT NULL DEFAULT '',",
            "    last_run_id TEXT NOT NULL DEFAULT '',",
            "    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,",
            "    PRIMARY KEY (owner_user_id, seen_key)",
            ");",
            "",
            "CREATE INDEX IF NOT EXISTS idx_user_seen_jobs_owner_last_seen",
            "ON user_seen_jobs (owner_user_id, last_seen_at DESC);",
            "",
            "CREATE INDEX IF NOT EXISTS idx_user_seen_jobs_job_doc_id",
            "ON user_seen_jobs (job_doc_id);",
            "",
            "CREATE INDEX IF NOT EXISTS idx_user_seen_jobs_job_url",
            "ON user_seen_jobs (job_url);",
            "",
            "CREATE TABLE IF NOT EXISTS user_pipeline_artifacts (",
            "    artifact_id TEXT PRIMARY KEY,",
            "    owner_user_id TEXT NOT NULL REFERENCES auth_users(user_id) ON DELETE CASCADE,",
            "    run_id TEXT NOT NULL REFERENCES user_pipeline_runs(run_id) ON DELETE CASCADE,",
            "    artifact_kind TEXT NOT NULL,",
            "    artifact_name TEXT NOT NULL,",
            "    content_type TEXT NOT NULL DEFAULT 'application/json',",
            "    content_json JSONB,",
            "    content_text TEXT NOT NULL DEFAULT '',",
            "    content_bytes BYTEA,",
            "    created_at TIMESTAMPTZ NOT NULL",
            ");",
            "",
            "CREATE INDEX IF NOT EXISTS idx_user_pipeline_artifacts_owner_run",
            "ON user_pipeline_artifacts (owner_user_id, run_id, artifact_kind);",
            "",
            "CREATE INDEX IF NOT EXISTS idx_user_pipeline_artifacts_run_kind",
            "ON user_pipeline_artifacts (run_id, artifact_kind);",
            "",
            "CREATE INDEX IF NOT EXISTS idx_user_pipeline_artifacts_owner_created",
            "ON user_pipeline_artifacts (owner_user_id, created_at DESC);",
        ]
    )


def user_pipeline_schema_sql_text(
    schema_path: Path = DEFAULT_USER_PIPELINE_SCHEMA_SQL_PATH,
) -> str:
    return _read_sql_artifact(schema_path, "user pipeline schema")


def user_pipeline_schema_sql_payload(
    schema_path: Path = DEFAULT_USER_PIPELINE_SCHEMA_SQL_PATH,
) -> Dict[str, Any]:
    sql = user_pipeline_schema_sql_text(schema_path)
    return {
        "path": str(Path(schema_path)),
        "sql": sql,
    }


def user_pipeline_schema_sql_generation_payload(
    schema_path: Path = DEFAULT_USER_PIPELINE_SCHEMA_SQL_PATH,
) -> Dict[str, Any]:
    generated_sql = render_user_pipeline_schema_sql()
    artifact_sql = user_pipeline_schema_sql_text(schema_path)

    return {
        "artifact_path": str(Path(schema_path)),
        "artifact_sql": artifact_sql,
        "generated_sql": generated_sql,
        "matches_artifact": generated_sql.strip() == artifact_sql.strip(),
    }


def user_pipeline_contract_health_payload() -> Dict[str, Any]:
    schema_generation = user_pipeline_schema_sql_generation_payload()

    return {
        "ok": True,
        "artifacts": {
            "schema_sql_path": str(DEFAULT_USER_PIPELINE_SCHEMA_SQL_PATH),
        },
        "checks": {
            "schema_sql_matches_artifact": bool(schema_generation["matches_artifact"]),
        },
        "all_checks_pass": bool(schema_generation["matches_artifact"]),
        "table_specs": user_pipeline_table_specs(),
    }


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_compact(value: Any) -> str:
    return json.dumps(
        value if value is not None else {},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _sql_quote_text(value: Any) -> str:
    return "'" + str(value or "").replace("'", "''") + "'"


def _sql_jsonb(value: Any) -> str:
    return f"{_sql_quote_text(_json_compact(value))}::jsonb"


def _sql_nullable_timestamptz(value: Any) -> str:
    text = _clean_text(value)
    return "NULL" if not text else f"{_sql_quote_text(text)}::timestamptz"


def _sql_nullable_int(value: Any) -> str:
    if value is None or _clean_text(value) == "":
        return "NULL"

    parsed = int(value)
    return str(parsed)


def _resolve_database_url(
    explicit_value: str,
    env_var_name: str,
    *,
    allow_placeholder: bool,
) -> str:
    explicit = str(explicit_value or "").strip()
    if explicit:
        return explicit

    env_name = str(env_var_name or "").strip() or "DATABASE_URL"
    env_value = str(os.environ.get(env_name, "") or "").strip()
    if env_value:
        return env_value

    if allow_placeholder:
        return f"${env_name}"

    raise SystemExit(
        f"Database URL is required. Pass --database-url or set {env_name} in the environment."
    )


def _redact_database_url(value: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return raw

    parts = urlsplit(raw)
    if "@" not in parts.netloc:
        return raw

    userinfo, hostinfo = parts.netloc.rsplit("@", 1)
    redacted_userinfo = f"{userinfo.split(':', 1)[0]}:***" if ":" in userinfo else "***"
    return urlunsplit(
        (
            parts.scheme,
            f"{redacted_userinfo}@{hostinfo}",
            parts.path,
            parts.query,
            parts.fragment,
        )
    )


def _run_psql_json_stdin_query(
    *,
    sql: str,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
) -> Dict[str, Any]:
    database_url_value = _resolve_database_url(
        database_url,
        database_url_env,
        allow_placeholder=bool(print_only),
    )

    cmd: List[str] = [
        str(psql_bin),
        database_url_value,
        "-X",
        "-q",
        "-v",
        "ON_ERROR_STOP=1",
        "-t",
        "-A",
    ]

    redacted_cmd = list(cmd)
    redacted_cmd[1] = _redact_database_url(redacted_cmd[1])

    payload: Dict[str, Any] = {
        "command": redacted_cmd,
        "command_text": shlex.join(redacted_cmd),
        "data": {},
    }

    if print_only:
        payload["sql"] = sql
        return payload

    if shutil.which(str(psql_bin)) is None:
        raise SystemExit(f"psql executable not found on PATH: {psql_bin!r}.")

    completed = subprocess.run(
        cmd,
        check=True,
        input=sql,
        capture_output=True,
        text=True,
    )

    stdout_lines = [
        line.strip()
        for line in str(completed.stdout or "").splitlines()
        if line.strip()
    ]
    if not stdout_lines:
        raise SystemExit("psql returned empty output for user-pipeline query.")

    raw_json = stdout_lines[-1]
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"Failed to parse user-pipeline query JSON from psql output: {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise SystemExit("User-pipeline query did not return a JSON object.")

    payload["data"] = data
    return payload


def _schema_prefix(ensure_schema: bool) -> str:
    return user_pipeline_schema_sql_text() + "\n\n" if ensure_schema else ""


def _require_owner_user_id(owner_user_id: Any) -> str:
    owner = _clean_text(owner_user_id)
    if not owner:
        raise ValueError("owner_user_id is required.")
    return owner


def _require_run_id(run_id: Any) -> str:
    safe_run_id = _clean_text(run_id)
    if not safe_run_id:
        raise ValueError("run_id is required.")
    return safe_run_id


def user_pipeline_run_db_row(record: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(record, dict):
        raise ValueError("User pipeline run record must be a dictionary.")

    run_id = _require_run_id(record.get("run_id"))
    owner_user_id = _require_owner_user_id(record.get("owner_user_id"))
    status = _clean_text(record.get("status")) or "queued"
    now = _utc_now_iso()

    return {
        "run_id": run_id,
        "owner_user_id": owner_user_id,
        "status": status,
        "current_stage": _clean_text(record.get("current_stage")),
        "stage_message": _clean_text(record.get("stage_message")),
        "summary_message": _clean_text(record.get("summary_message")),
        "return_code": record.get("return_code"),
        "started_at": _clean_text(record.get("started_at")) or now,
        "updated_at": _clean_text(record.get("updated_at")) or now,
        "completed_at": _clean_text(record.get("completed_at")),
        "config_json": record.get("config_json") or {},
        "status_json": record.get("status_json") or {},
        "error": _clean_text(record.get("error")),
    }


def upsert_user_pipeline_run_postgres_payload(
    *,
    record: Dict[str, Any],
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    row = user_pipeline_run_db_row(record)

    sql = _schema_prefix(ensure_schema) + f"""
WITH upserted AS (
    INSERT INTO user_pipeline_runs (
        run_id,
        owner_user_id,
        status,
        current_stage,
        stage_message,
        summary_message,
        return_code,
        started_at,
        updated_at,
        completed_at,
        config_json,
        status_json,
        error
    )
    VALUES (
        {_sql_quote_text(row['run_id'])},
        {_sql_quote_text(row['owner_user_id'])},
        {_sql_quote_text(row['status'])},
        {_sql_quote_text(row['current_stage'])},
        {_sql_quote_text(row['stage_message'])},
        {_sql_quote_text(row['summary_message'])},
        {_sql_nullable_int(row['return_code'])},
        {_sql_quote_text(row['started_at'])}::timestamptz,
        {_sql_quote_text(row['updated_at'])}::timestamptz,
        {_sql_nullable_timestamptz(row['completed_at'])},
        {_sql_jsonb(row['config_json'])},
        {_sql_jsonb(row['status_json'])},
        {_sql_quote_text(row['error'])}
    )
    ON CONFLICT (run_id) DO UPDATE SET
        owner_user_id = EXCLUDED.owner_user_id,
        status = EXCLUDED.status,
        current_stage = EXCLUDED.current_stage,
        stage_message = EXCLUDED.stage_message,
        summary_message = EXCLUDED.summary_message,
        return_code = EXCLUDED.return_code,
        updated_at = EXCLUDED.updated_at,
        completed_at = EXCLUDED.completed_at,
        config_json = EXCLUDED.config_json,
        status_json = EXCLUDED.status_json,
        error = EXCLUDED.error
    RETURNING *
)
SELECT json_build_object(
    'upserted', EXISTS (SELECT 1 FROM upserted),
    'run', COALESCE((SELECT row_to_json(upserted) FROM upserted LIMIT 1), '{{}}'::json)
);
""".strip()

    payload = _run_psql_json_stdin_query(
        sql=sql,
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        print_only=print_only,
    )

    return {
        "ok": bool(payload.get("data", {}).get("upserted", False)),
        "upserted": bool(payload.get("data", {}).get("upserted", False)),
        "run": dict(payload.get("data", {}).get("run", {}) or {}),
        "command": payload.get("command", []),
        "command_text": payload.get("command_text", ""),
        "table_name": "user_pipeline_runs",
    }


def update_user_pipeline_run_status_postgres_payload(
    *,
    owner_user_id: str,
    run_id: str,
    status: str,
    current_stage: str = "",
    stage_message: str = "",
    summary_message: str = "",
    return_code: int | None = None,
    completed_at: str = "",
    status_json: Dict[str, Any] | None = None,
    error: str = "",
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    owner = _require_owner_user_id(owner_user_id)
    safe_run_id = _require_run_id(run_id)
    safe_status = _clean_text(status) or "running"

    completed_sql = (
        "now()"
        if safe_status in {"succeeded", "failed", "cancelled"} and not _clean_text(completed_at)
        else _sql_nullable_timestamptz(completed_at)
    )

    sql = _schema_prefix(ensure_schema) + f"""
WITH updated AS (
    UPDATE user_pipeline_runs
    SET
        status = {_sql_quote_text(safe_status)},
        current_stage = {_sql_quote_text(current_stage)},
        stage_message = {_sql_quote_text(stage_message)},
        summary_message = {_sql_quote_text(summary_message)},
        return_code = {_sql_nullable_int(return_code)},
        updated_at = now(),
        completed_at = {completed_sql},
        status_json = {_sql_jsonb(status_json or {})},
        error = {_sql_quote_text(error)}
    WHERE owner_user_id = {_sql_quote_text(owner)}
      AND run_id = {_sql_quote_text(safe_run_id)}
    RETURNING *
)
SELECT json_build_object(
    'updated', EXISTS (SELECT 1 FROM updated),
    'run', COALESCE((SELECT row_to_json(updated) FROM updated LIMIT 1), '{{}}'::json)
);
""".strip()

    payload = _run_psql_json_stdin_query(
        sql=sql,
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        print_only=print_only,
    )

    return {
        "ok": bool(payload.get("data", {}).get("updated", False)),
        "updated": bool(payload.get("data", {}).get("updated", False)),
        "run": dict(payload.get("data", {}).get("run", {}) or {}),
        "command": payload.get("command", []),
        "command_text": payload.get("command_text", ""),
        "table_name": "user_pipeline_runs",
    }


def get_user_pipeline_runs_postgres_payload(
    *,
    owner_user_id: str,
    limit: int = 20,
    status: str = "",
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    owner = _require_owner_user_id(owner_user_id)
    safe_limit = max(1, min(int(limit), 200))
    safe_status = _clean_text(status)

    status_filter = (
        f"AND status = {_sql_quote_text(safe_status)}"
        if safe_status
        else ""
    )

    sql = _schema_prefix(ensure_schema) + f"""
WITH run_rows AS (
    SELECT *
    FROM user_pipeline_runs
    WHERE owner_user_id = {_sql_quote_text(owner)}
    {status_filter}
    ORDER BY started_at DESC
    LIMIT {safe_limit}
)
SELECT json_build_object(
    'total_row_count', (
        SELECT COUNT(*)
        FROM user_pipeline_runs
        WHERE owner_user_id = {_sql_quote_text(owner)}
        {status_filter}
    ),
    'rows', COALESCE((SELECT json_agg(row_to_json(run_rows)) FROM run_rows), '[]'::json)
);
""".strip()

    payload = _run_psql_json_stdin_query(
        sql=sql,
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        print_only=print_only,
    )

    rows = list(payload.get("data", {}).get("rows", []) or [])
    return {
        "ok": True,
        "runs": rows,
        "rows": rows,
        "count": len(rows),
        "total_row_count": int(payload.get("data", {}).get("total_row_count", 0) or 0),
        "command": payload.get("command", []),
        "command_text": payload.get("command_text", ""),
    }


def get_latest_user_pipeline_run_postgres_payload(
    *,
    owner_user_id: str,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    payload = get_user_pipeline_runs_postgres_payload(
        owner_user_id=owner_user_id,
        limit=1,
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        print_only=print_only,
        ensure_schema=ensure_schema,
    )
    rows = list(payload.get("rows", []) or [])
    return {
        "ok": True,
        "found": bool(rows),
        "run": dict(rows[0] or {}) if rows else {},
        "command": payload.get("command", []),
        "command_text": payload.get("command_text", ""),
    }


def _seen_key_from_record(record: Dict[str, Any]) -> str:
    explicit = _clean_text(record.get("seen_key"))
    if explicit:
        return explicit

    identity_parts = [
        _clean_text(record.get("job_doc_id")),
        _clean_text(record.get("job_url")),
        _clean_text(record.get("source")),
        _clean_text(record.get("company")),
        _clean_text(record.get("title")),
    ]
    identity = "|".join(identity_parts).strip("|")

    if not identity:
        raise ValueError("seen_key or job identity fields are required.")

    return hashlib.sha1(identity.encode("utf-8")).hexdigest()


def user_seen_job_db_row(record: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(record, dict):
        raise ValueError("User seen job record must be a dictionary.")

    owner_user_id = _require_owner_user_id(record.get("owner_user_id"))
    seen_key = _seen_key_from_record(record)
    now = _utc_now_iso()

    return {
        "owner_user_id": owner_user_id,
        "seen_key": seen_key,
        "source": _clean_text(record.get("source")),
        "job_url": _clean_text(record.get("job_url")),
        "job_doc_id": _clean_text(record.get("job_doc_id")),
        "company": _clean_text(record.get("company")),
        "title": _clean_text(record.get("title")),
        "first_seen_at": _clean_text(record.get("first_seen_at")) or now,
        "last_seen_at": _clean_text(record.get("last_seen_at")) or now,
        "first_run_id": _clean_text(record.get("first_run_id")),
        "last_run_id": _clean_text(record.get("last_run_id")),
        "metadata_json": record.get("metadata_json") or {},
    }


def upsert_user_seen_job_postgres_payload(
    *,
    record: Dict[str, Any],
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    row = user_seen_job_db_row(record)

    sql = _schema_prefix(ensure_schema) + f"""
WITH upserted AS (
    INSERT INTO user_seen_jobs (
        owner_user_id,
        seen_key,
        source,
        job_url,
        job_doc_id,
        company,
        title,
        first_seen_at,
        last_seen_at,
        first_run_id,
        last_run_id,
        metadata_json
    )
    VALUES (
        {_sql_quote_text(row['owner_user_id'])},
        {_sql_quote_text(row['seen_key'])},
        {_sql_quote_text(row['source'])},
        {_sql_quote_text(row['job_url'])},
        {_sql_quote_text(row['job_doc_id'])},
        {_sql_quote_text(row['company'])},
        {_sql_quote_text(row['title'])},
        {_sql_quote_text(row['first_seen_at'])}::timestamptz,
        {_sql_quote_text(row['last_seen_at'])}::timestamptz,
        {_sql_quote_text(row['first_run_id'])},
        {_sql_quote_text(row['last_run_id'])},
        {_sql_jsonb(row['metadata_json'])}
    )
    ON CONFLICT (owner_user_id, seen_key) DO UPDATE SET
        source = COALESCE(NULLIF(EXCLUDED.source, ''), user_seen_jobs.source),
        job_url = COALESCE(NULLIF(EXCLUDED.job_url, ''), user_seen_jobs.job_url),
        job_doc_id = COALESCE(NULLIF(EXCLUDED.job_doc_id, ''), user_seen_jobs.job_doc_id),
        company = COALESCE(NULLIF(EXCLUDED.company, ''), user_seen_jobs.company),
        title = COALESCE(NULLIF(EXCLUDED.title, ''), user_seen_jobs.title),
        last_seen_at = EXCLUDED.last_seen_at,
        last_run_id = COALESCE(NULLIF(EXCLUDED.last_run_id, ''), user_seen_jobs.last_run_id),
        metadata_json = user_seen_jobs.metadata_json || EXCLUDED.metadata_json
    RETURNING *
)
SELECT json_build_object(
    'upserted', EXISTS (SELECT 1 FROM upserted),
    'seen_job', COALESCE((SELECT row_to_json(upserted) FROM upserted LIMIT 1), '{{}}'::json)
);
""".strip()

    payload = _run_psql_json_stdin_query(
        sql=sql,
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        print_only=print_only,
    )

    return {
        "ok": bool(payload.get("data", {}).get("upserted", False)),
        "upserted": bool(payload.get("data", {}).get("upserted", False)),
        "seen_job": dict(payload.get("data", {}).get("seen_job", {}) or {}),
        "command": payload.get("command", []),
        "command_text": payload.get("command_text", ""),
        "table_name": "user_seen_jobs",
    }


def is_user_seen_job_postgres_payload(
    *,
    owner_user_id: str,
    seen_key: str,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    owner = _require_owner_user_id(owner_user_id)
    safe_seen_key = _clean_text(seen_key)
    if not safe_seen_key:
        raise ValueError("seen_key is required.")

    sql = _schema_prefix(ensure_schema) + f"""
SELECT json_build_object(
    'seen', EXISTS (
        SELECT 1
        FROM user_seen_jobs
        WHERE owner_user_id = {_sql_quote_text(owner)}
          AND seen_key = {_sql_quote_text(safe_seen_key)}
    )
);
""".strip()

    payload = _run_psql_json_stdin_query(
        sql=sql,
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        print_only=print_only,
    )

    return {
        "ok": True,
        "seen": bool(payload.get("data", {}).get("seen", False)),
        "command": payload.get("command", []),
        "command_text": payload.get("command_text", ""),
    }


def get_user_seen_jobs_postgres_payload(
    *,
    owner_user_id: str,
    limit: int = 100,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    owner = _require_owner_user_id(owner_user_id)
    safe_limit = max(1, min(int(limit), 1000))

    sql = _schema_prefix(ensure_schema) + f"""
WITH seen_rows AS (
    SELECT *
    FROM user_seen_jobs
    WHERE owner_user_id = {_sql_quote_text(owner)}
    ORDER BY last_seen_at DESC
    LIMIT {safe_limit}
)
SELECT json_build_object(
    'total_row_count', (
        SELECT COUNT(*)
        FROM user_seen_jobs
        WHERE owner_user_id = {_sql_quote_text(owner)}
    ),
    'rows', COALESCE((SELECT json_agg(row_to_json(seen_rows)) FROM seen_rows), '[]'::json)
);
""".strip()

    payload = _run_psql_json_stdin_query(
        sql=sql,
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        print_only=print_only,
    )

    rows = list(payload.get("data", {}).get("rows", []) or [])
    return {
        "ok": True,
        "seen_jobs": rows,
        "rows": rows,
        "count": len(rows),
        "total_row_count": int(payload.get("data", {}).get("total_row_count", 0) or 0),
        "command": payload.get("command", []),
        "command_text": payload.get("command_text", ""),
    }


def clear_user_seen_jobs_postgres_payload(
    *,
    owner_user_id: str,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    owner = _require_owner_user_id(owner_user_id)

    sql = _schema_prefix(ensure_schema) + f"""
WITH deleted AS (
    DELETE FROM user_seen_jobs
    WHERE owner_user_id = {_sql_quote_text(owner)}
    RETURNING seen_key
)
SELECT json_build_object(
    'deleted_count', (SELECT COUNT(*) FROM deleted)
);
""".strip()

    payload = _run_psql_json_stdin_query(
        sql=sql,
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        print_only=print_only,
    )

    deleted_count = int(payload.get("data", {}).get("deleted_count", 0) or 0)
    return {
        "ok": True,
        "deleted_count": deleted_count,
        "command": payload.get("command", []),
        "command_text": payload.get("command_text", ""),
        "table_name": "user_seen_jobs",
    }


def _sql_nullable_jsonb(value: Any) -> str:
    if value is None:
        return "NULL"
    return _sql_jsonb(value)


def _build_user_pipeline_artifact_id(row: Dict[str, Any]) -> str:
    payload = {
        "owner_user_id": _clean_text(row.get("owner_user_id")),
        "run_id": _clean_text(row.get("run_id")),
        "artifact_kind": _clean_text(row.get("artifact_kind")),
        "artifact_name": _clean_text(row.get("artifact_name")),
    }
    blob = _json_compact(payload)
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()


def user_pipeline_artifact_db_row(record: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(record, dict):
        raise ValueError("User pipeline artifact record must be a dictionary.")

    owner_user_id = _require_owner_user_id(record.get("owner_user_id"))
    run_id = _require_run_id(record.get("run_id"))
    artifact_kind = _clean_text(record.get("artifact_kind"))
    artifact_name = _clean_text(record.get("artifact_name"))

    if not artifact_kind:
        raise ValueError("artifact_kind is required.")
    if not artifact_name:
        raise ValueError("artifact_name is required.")

    row = {
        "artifact_id": _clean_text(record.get("artifact_id")),
        "owner_user_id": owner_user_id,
        "run_id": run_id,
        "artifact_kind": artifact_kind,
        "artifact_name": artifact_name,
        "content_type": _clean_text(record.get("content_type")) or "application/json",
        "content_json": record.get("content_json"),
        "content_text": _clean_text(record.get("content_text")),
        "created_at": _clean_text(record.get("created_at")) or _utc_now_iso(),
    }

    if not row["artifact_id"]:
        row["artifact_id"] = _build_user_pipeline_artifact_id(row)

    return row


def upsert_user_pipeline_artifact_postgres_payload(
    *,
    record: Dict[str, Any],
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    row = user_pipeline_artifact_db_row(record)

    sql = _schema_prefix(ensure_schema) + f"""
WITH upserted AS (
    INSERT INTO user_pipeline_artifacts (
        artifact_id,
        owner_user_id,
        run_id,
        artifact_kind,
        artifact_name,
        content_type,
        content_json,
        content_text,
        content_bytes,
        created_at
    )
    VALUES (
        {_sql_quote_text(row['artifact_id'])},
        {_sql_quote_text(row['owner_user_id'])},
        {_sql_quote_text(row['run_id'])},
        {_sql_quote_text(row['artifact_kind'])},
        {_sql_quote_text(row['artifact_name'])},
        {_sql_quote_text(row['content_type'])},
        {_sql_nullable_jsonb(row['content_json'])},
        {_sql_quote_text(row['content_text'])},
        NULL,
        {_sql_quote_text(row['created_at'])}::timestamptz
    )
    ON CONFLICT (artifact_id) DO UPDATE SET
        artifact_kind = EXCLUDED.artifact_kind,
        artifact_name = EXCLUDED.artifact_name,
        content_type = EXCLUDED.content_type,
        content_json = EXCLUDED.content_json,
        content_text = EXCLUDED.content_text,
        content_bytes = EXCLUDED.content_bytes,
        created_at = EXCLUDED.created_at
    RETURNING
        artifact_id,
        owner_user_id,
        run_id,
        artifact_kind,
        artifact_name,
        content_type,
        created_at
)
SELECT json_build_object(
    'upserted', EXISTS (SELECT 1 FROM upserted),
    'artifact', COALESCE((SELECT row_to_json(upserted) FROM upserted LIMIT 1), '{{}}'::json)
);
""".strip()

    payload = _run_psql_json_stdin_query(
        sql=sql,
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        print_only=print_only,
    )

    return {
        "ok": bool(payload.get("data", {}).get("upserted", False)),
        "upserted": bool(payload.get("data", {}).get("upserted", False)),
        "artifact": dict(payload.get("data", {}).get("artifact", {}) or {}),
        "command": payload.get("command", []),
        "command_text": payload.get("command_text", ""),
        "table_name": "user_pipeline_artifacts",
    }
