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


DEFAULT_AGENT_TRACE_SCHEMA_SQL_PATH = Path("src/storage/agent_trace/schema.sql")


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
    return str(int(value))


def _read_sql_artifact(path: Path, label: str) -> str:
    resolved = Path(path)
    if not resolved.exists():
        raise ValueError(f"Missing {label} SQL file: {resolved}")
    sql = resolved.read_text(encoding="utf-8")
    if not sql.strip():
        raise ValueError(f"{label.capitalize()} SQL file is empty: {resolved}")
    return sql


def agent_trace_schema_sql_text(
    schema_path: Path = DEFAULT_AGENT_TRACE_SCHEMA_SQL_PATH,
) -> str:
    return _read_sql_artifact(schema_path, "agent trace schema")


def render_agent_trace_schema_sql() -> str:
    return "\n".join(
        [
            "CREATE TABLE IF NOT EXISTS agent_runs (",
            "    agent_run_id TEXT PRIMARY KEY,",
            "    owner_user_id TEXT NOT NULL REFERENCES auth_users(user_id) ON DELETE CASCADE,",
            "    pipeline_run_id TEXT NOT NULL DEFAULT '',",
            "    context_id TEXT NOT NULL DEFAULT '',",
            "    status TEXT NOT NULL,",
            "    started_at TIMESTAMPTZ NOT NULL,",
            "    completed_at TIMESTAMPTZ,",
            "    summary_json JSONB NOT NULL DEFAULT '{}'::jsonb,",
            "    error TEXT NOT NULL DEFAULT ''",
            ");",
            "",
            "CREATE INDEX IF NOT EXISTS idx_agent_runs_owner_started",
            "ON agent_runs (owner_user_id, started_at DESC);",
            "",
            "CREATE INDEX IF NOT EXISTS idx_agent_runs_pipeline_started",
            "ON agent_runs (pipeline_run_id, started_at DESC);",
            "",
            "CREATE INDEX IF NOT EXISTS idx_agent_runs_context_started",
            "ON agent_runs (context_id, started_at DESC);",
            "",
            "CREATE INDEX IF NOT EXISTS idx_agent_runs_status_started",
            "ON agent_runs (status, started_at DESC);",
            "",
            "CREATE TABLE IF NOT EXISTS agent_steps (",
            "    agent_step_id TEXT PRIMARY KEY,",
            "    agent_run_id TEXT NOT NULL REFERENCES agent_runs(agent_run_id) ON DELETE CASCADE,",
            "    owner_user_id TEXT NOT NULL REFERENCES auth_users(user_id) ON DELETE CASCADE,",
            "    pipeline_run_id TEXT NOT NULL DEFAULT '',",
            "    context_id TEXT NOT NULL DEFAULT '',",
            "    agent_name TEXT NOT NULL,",
            "    agent_version TEXT NOT NULL DEFAULT '',",
            "    input_json JSONB NOT NULL DEFAULT '{}'::jsonb,",
            "    output_json JSONB NOT NULL DEFAULT '{}'::jsonb,",
            "    validation_json JSONB NOT NULL DEFAULT '{}'::jsonb,",
            "    status TEXT NOT NULL,",
            "    started_at TIMESTAMPTZ NOT NULL,",
            "    completed_at TIMESTAMPTZ,",
            "    latency_ms INTEGER,",
            "    model_provider TEXT NOT NULL DEFAULT '',",
            "    model_name TEXT NOT NULL DEFAULT '',",
            "    token_usage_json JSONB NOT NULL DEFAULT '{}'::jsonb,",
            "    cost_json JSONB NOT NULL DEFAULT '{}'::jsonb,",
            "    error TEXT NOT NULL DEFAULT ''",
            ");",
            "",
            "CREATE INDEX IF NOT EXISTS idx_agent_steps_run_started",
            "ON agent_steps (agent_run_id, started_at);",
            "",
            "CREATE INDEX IF NOT EXISTS idx_agent_steps_owner_started",
            "ON agent_steps (owner_user_id, started_at DESC);",
            "",
            "CREATE INDEX IF NOT EXISTS idx_agent_steps_pipeline_started",
            "ON agent_steps (pipeline_run_id, started_at DESC);",
            "",
            "CREATE INDEX IF NOT EXISTS idx_agent_steps_context_started",
            "ON agent_steps (context_id, started_at DESC);",
            "",
            "CREATE INDEX IF NOT EXISTS idx_agent_steps_status_started",
            "ON agent_steps (status, started_at DESC);",
        ]
    )


def agent_trace_schema_sql_payload(
    schema_path: Path = DEFAULT_AGENT_TRACE_SCHEMA_SQL_PATH,
) -> Dict[str, Any]:
    return {"path": str(Path(schema_path)), "sql": agent_trace_schema_sql_text(schema_path)}


def agent_trace_schema_sql_generation_payload(
    schema_path: Path = DEFAULT_AGENT_TRACE_SCHEMA_SQL_PATH,
) -> Dict[str, Any]:
    generated_sql = render_agent_trace_schema_sql()
    artifact_sql = agent_trace_schema_sql_text(schema_path)
    return {
        "artifact_path": str(Path(schema_path)),
        "artifact_sql": artifact_sql,
        "generated_sql": generated_sql,
        "matches_artifact": generated_sql.strip() == artifact_sql.strip(),
    }


def agent_trace_table_specs() -> Dict[str, Any]:
    return {
        "agent_runs": {
            "primary_key": ["agent_run_id"],
            "owner_column": "owner_user_id",
            "columns": [
                "agent_run_id",
                "owner_user_id",
                "pipeline_run_id",
                "context_id",
                "status",
                "started_at",
                "completed_at",
                "summary_json",
                "error",
            ],
        },
        "agent_steps": {
            "primary_key": ["agent_step_id"],
            "owner_column": "owner_user_id",
            "columns": [
                "agent_step_id",
                "agent_run_id",
                "owner_user_id",
                "pipeline_run_id",
                "context_id",
                "agent_name",
                "agent_version",
                "input_json",
                "output_json",
                "validation_json",
                "status",
                "started_at",
                "completed_at",
                "latency_ms",
                "model_provider",
                "model_name",
                "token_usage_json",
                "cost_json",
                "error",
            ],
        },
    }


def agent_trace_contract_health_payload() -> Dict[str, Any]:
    schema_generation = agent_trace_schema_sql_generation_payload()
    return {
        "ok": True,
        "artifacts": {"schema_sql_path": str(DEFAULT_AGENT_TRACE_SCHEMA_SQL_PATH)},
        "checks": {
            "schema_sql_matches_artifact": bool(schema_generation["matches_artifact"]),
        },
        "all_checks_pass": bool(schema_generation["matches_artifact"]),
        "table_specs": agent_trace_table_specs(),
    }


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
    return urlunsplit((parts.scheme, f"{redacted_userinfo}@{hostinfo}", parts.path, parts.query, parts.fragment))


def _run_postgres_json_query(
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
    psql_cmd: List[str] = [
        str(psql_bin),
        database_url_value,
        "-X",
        "-q",
        "-v",
        "ON_ERROR_STOP=1",
        "-t",
        "-A",
    ]
    redacted_cmd = list(psql_cmd)
    redacted_cmd[1] = _redact_database_url(redacted_cmd[1])
    payload: Dict[str, Any] = {
        "connection": _redact_database_url(database_url_value),
        "driver": "",
        "command": redacted_cmd,
        "command_text": shlex.join(redacted_cmd),
        "data": {},
    }
    if print_only:
        payload["sql"] = sql
        return payload

    driver_name = ""
    connect = None
    dbapi_import_error: ImportError | None = None
    try:
        import psycopg  # type: ignore

        driver_name = "psycopg"
        connect = psycopg.connect
    except ImportError as exc:
        dbapi_import_error = exc
        try:
            import psycopg2  # type: ignore

            driver_name = "psycopg2"
            connect = psycopg2.connect
        except ImportError as exc:
            dbapi_import_error = exc

    if connect is not None:
        payload["driver"] = driver_name
        with connect(database_url_value) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                row = cursor.fetchone()
            conn.commit()
        return _agent_trace_query_payload_from_row(payload, row)

    payload["driver"] = "psql"
    payload["dbapi_import_error"] = str(dbapi_import_error or "")
    if shutil.which(str(psql_bin)) is None:
        raise SystemExit(f"psql executable not found on PATH: {psql_bin!r}.")

    completed = subprocess.run(
        psql_cmd,
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
        raise SystemExit("Postgres returned empty output for agent-trace query.")

    return _agent_trace_query_payload_from_row(payload, [stdout_lines[-1]])


def _agent_trace_query_payload_from_row(
    payload: Dict[str, Any],
    row: Any,
) -> Dict[str, Any]:
    if not row:
        raise SystemExit("Postgres returned empty output for agent-trace query.")

    raw_json = row[0]
    if isinstance(raw_json, dict):
        data = raw_json
    else:
        raw_json = str(raw_json or "").strip()
        if not raw_json:
            raise SystemExit("Postgres returned empty JSON for agent-trace query.")
        try:
            data = json.loads(raw_json)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Failed to parse agent-trace query JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise SystemExit("Agent-trace query did not return a JSON object.")
    payload["data"] = data
    return payload


def _schema_prefix(ensure_schema: bool) -> str:
    return agent_trace_schema_sql_text() + "\n\n" if ensure_schema else ""


def _require_owner_user_id(owner_user_id: Any) -> str:
    owner = _clean_text(owner_user_id)
    if not owner:
        raise ValueError("owner_user_id is required.")
    return owner


def _require_agent_run_id(agent_run_id: Any) -> str:
    safe_id = _clean_text(agent_run_id)
    if not safe_id:
        raise ValueError("agent_run_id is required.")
    return safe_id


def _require_agent_step_id(agent_step_id: Any) -> str:
    safe_id = _clean_text(agent_step_id)
    if not safe_id:
        raise ValueError("agent_step_id is required.")
    return safe_id


def build_agent_run_id(record: Dict[str, Any]) -> str:
    signature = {
        "owner_user_id": _clean_text(record.get("owner_user_id")),
        "pipeline_run_id": _clean_text(record.get("pipeline_run_id")),
        "context_id": _clean_text(record.get("context_id")),
        "started_at": _clean_text(record.get("started_at")),
    }
    return "agent_run_" + hashlib.sha1(_json_compact(signature).encode("utf-8")).hexdigest()


def build_agent_step_id(record: Dict[str, Any]) -> str:
    signature = {
        "agent_run_id": _clean_text(record.get("agent_run_id")),
        "agent_name": _clean_text(record.get("agent_name")),
        "started_at": _clean_text(record.get("started_at")),
        "input_json": record.get("input_json") or {},
    }
    return "agent_step_" + hashlib.sha1(_json_compact(signature).encode("utf-8")).hexdigest()


def agent_run_db_row(record: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(record, dict):
        raise ValueError("Agent run record must be a dictionary.")
    owner = _require_owner_user_id(record.get("owner_user_id"))
    started_at = _clean_text(record.get("started_at")) or _utc_now_iso()
    row = {
        "agent_run_id": _clean_text(record.get("agent_run_id")),
        "owner_user_id": owner,
        "pipeline_run_id": _clean_text(record.get("pipeline_run_id") or record.get("run_id")),
        "context_id": _clean_text(record.get("context_id")),
        "status": _clean_text(record.get("status")) or "running",
        "started_at": started_at,
        "completed_at": _clean_text(record.get("completed_at")),
        "summary_json": record.get("summary_json") or {},
        "error": _clean_text(record.get("error")),
    }
    if not row["agent_run_id"]:
        row["agent_run_id"] = build_agent_run_id(row)
    return row


def agent_step_db_row(record: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(record, dict):
        raise ValueError("Agent step record must be a dictionary.")
    started_at = _clean_text(record.get("started_at")) or _utc_now_iso()
    row = {
        "agent_step_id": _clean_text(record.get("agent_step_id")),
        "agent_run_id": _require_agent_run_id(record.get("agent_run_id")),
        "owner_user_id": _require_owner_user_id(record.get("owner_user_id")),
        "pipeline_run_id": _clean_text(record.get("pipeline_run_id") or record.get("run_id")),
        "context_id": _clean_text(record.get("context_id")),
        "agent_name": _clean_text(record.get("agent_name")),
        "agent_version": _clean_text(record.get("agent_version")),
        "input_json": record.get("input_json") or {},
        "output_json": record.get("output_json") or {},
        "validation_json": record.get("validation_json") or {},
        "status": _clean_text(record.get("status")) or "running",
        "started_at": started_at,
        "completed_at": _clean_text(record.get("completed_at")),
        "latency_ms": record.get("latency_ms"),
        "model_provider": _clean_text(record.get("model_provider")),
        "model_name": _clean_text(record.get("model_name")),
        "token_usage_json": record.get("token_usage_json") or {},
        "cost_json": record.get("cost_json") or {},
        "error": _clean_text(record.get("error")),
    }
    if not row["agent_name"]:
        raise ValueError("agent_name is required.")
    if not row["agent_step_id"]:
        row["agent_step_id"] = build_agent_step_id(row)
    return row


def create_agent_run_postgres_payload(
    *,
    record: Dict[str, Any],
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    row = agent_run_db_row(record)
    sql = _schema_prefix(ensure_schema) + f"""
WITH inserted AS (
    INSERT INTO agent_runs (
        agent_run_id, owner_user_id, pipeline_run_id, context_id, status,
        started_at, completed_at, summary_json, error
    )
    VALUES (
        {_sql_quote_text(row['agent_run_id'])},
        {_sql_quote_text(row['owner_user_id'])},
        {_sql_quote_text(row['pipeline_run_id'])},
        {_sql_quote_text(row['context_id'])},
        {_sql_quote_text(row['status'])},
        {_sql_quote_text(row['started_at'])}::timestamptz,
        {_sql_nullable_timestamptz(row['completed_at'])},
        {_sql_jsonb(row['summary_json'])},
        {_sql_quote_text(row['error'])}
    )
    ON CONFLICT (agent_run_id) DO UPDATE SET
        status = EXCLUDED.status,
        summary_json = EXCLUDED.summary_json,
        error = EXCLUDED.error
    RETURNING *
)
SELECT json_build_object(
    'created', EXISTS (SELECT 1 FROM inserted),
    'run', COALESCE((SELECT row_to_json(inserted) FROM inserted LIMIT 1), '{{}}'::json)
);
""".strip()
    payload = _run_postgres_json_query(sql=sql, database_url=database_url, database_url_env=database_url_env, psql_bin=psql_bin, print_only=print_only)
    data = payload.get("data") or {}
    return {
        "ok": bool(print_only or data.get("created", False)),
        "created": bool(print_only or data.get("created", False)),
        "run": row if print_only else dict(data.get("run", {}) or {}),
        "sql": payload.get("sql", ""),
        "command": payload.get("command", []),
        "command_text": payload.get("command_text", ""),
        "table_name": "agent_runs",
    }


def complete_agent_run_postgres_payload(
    *,
    agent_run_id: str,
    owner_user_id: str,
    summary_json: Dict[str, Any] | None = None,
    completed_at: str = "",
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    return _update_agent_run_status_postgres_payload(
        agent_run_id=agent_run_id,
        owner_user_id=owner_user_id,
        status="succeeded",
        summary_json=summary_json or {},
        completed_at=completed_at,
        error="",
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        print_only=print_only,
        ensure_schema=ensure_schema,
    )


def fail_agent_run_postgres_payload(
    *,
    agent_run_id: str,
    owner_user_id: str,
    error: str,
    summary_json: Dict[str, Any] | None = None,
    completed_at: str = "",
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    return _update_agent_run_status_postgres_payload(
        agent_run_id=agent_run_id,
        owner_user_id=owner_user_id,
        status="failed",
        summary_json=summary_json or {},
        completed_at=completed_at,
        error=error,
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        print_only=print_only,
        ensure_schema=ensure_schema,
    )


def _update_agent_run_status_postgres_payload(
    *,
    agent_run_id: str,
    owner_user_id: str,
    status: str,
    summary_json: Dict[str, Any],
    completed_at: str,
    error: str,
    database_url: str,
    database_url_env: str,
    psql_bin: str,
    print_only: bool,
    ensure_schema: bool,
) -> Dict[str, Any]:
    safe_id = _require_agent_run_id(agent_run_id)
    owner = _require_owner_user_id(owner_user_id)
    completed_sql = _sql_nullable_timestamptz(completed_at) if completed_at else "now()"
    sql = _schema_prefix(ensure_schema) + f"""
WITH updated AS (
    UPDATE agent_runs
    SET status = {_sql_quote_text(status)},
        completed_at = {completed_sql},
        summary_json = {_sql_jsonb(summary_json)},
        error = {_sql_quote_text(error)}
    WHERE agent_run_id = {_sql_quote_text(safe_id)}
      AND owner_user_id = {_sql_quote_text(owner)}
    RETURNING *
)
SELECT json_build_object(
    'updated', EXISTS (SELECT 1 FROM updated),
    'run', COALESCE((SELECT row_to_json(updated) FROM updated LIMIT 1), '{{}}'::json)
);
""".strip()
    payload = _run_postgres_json_query(sql=sql, database_url=database_url, database_url_env=database_url_env, psql_bin=psql_bin, print_only=print_only)
    data = payload.get("data") or {}
    return {
        "ok": bool(print_only or data.get("updated", False)),
        "updated": bool(print_only or data.get("updated", False)),
        "run": {
            "agent_run_id": safe_id,
            "owner_user_id": owner,
            "status": status,
            "summary_json": summary_json,
            "error": _clean_text(error),
        } if print_only else dict(data.get("run", {}) or {}),
        "sql": payload.get("sql", ""),
        "command": payload.get("command", []),
        "command_text": payload.get("command_text", ""),
        "table_name": "agent_runs",
    }


def record_agent_step_postgres_payload(
    *,
    record: Dict[str, Any],
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    row = agent_step_db_row(record)
    sql = _schema_prefix(ensure_schema) + f"""
WITH inserted AS (
    INSERT INTO agent_steps (
        agent_step_id, agent_run_id, owner_user_id, pipeline_run_id, context_id,
        agent_name, agent_version, input_json, output_json, validation_json, status,
        started_at, completed_at, latency_ms, model_provider, model_name,
        token_usage_json, cost_json, error
    )
    VALUES (
        {_sql_quote_text(row['agent_step_id'])},
        {_sql_quote_text(row['agent_run_id'])},
        {_sql_quote_text(row['owner_user_id'])},
        {_sql_quote_text(row['pipeline_run_id'])},
        {_sql_quote_text(row['context_id'])},
        {_sql_quote_text(row['agent_name'])},
        {_sql_quote_text(row['agent_version'])},
        {_sql_jsonb(row['input_json'])},
        {_sql_jsonb(row['output_json'])},
        {_sql_jsonb(row['validation_json'])},
        {_sql_quote_text(row['status'])},
        {_sql_quote_text(row['started_at'])}::timestamptz,
        {_sql_nullable_timestamptz(row['completed_at'])},
        {_sql_nullable_int(row['latency_ms'])},
        {_sql_quote_text(row['model_provider'])},
        {_sql_quote_text(row['model_name'])},
        {_sql_jsonb(row['token_usage_json'])},
        {_sql_jsonb(row['cost_json'])},
        {_sql_quote_text(row['error'])}
    )
    ON CONFLICT (agent_step_id) DO UPDATE SET
        output_json = EXCLUDED.output_json,
        validation_json = EXCLUDED.validation_json,
        status = EXCLUDED.status,
        completed_at = EXCLUDED.completed_at,
        latency_ms = EXCLUDED.latency_ms,
        token_usage_json = EXCLUDED.token_usage_json,
        cost_json = EXCLUDED.cost_json,
        error = EXCLUDED.error
    RETURNING *
)
SELECT json_build_object(
    'recorded', EXISTS (SELECT 1 FROM inserted),
    'step', COALESCE((SELECT row_to_json(inserted) FROM inserted LIMIT 1), '{{}}'::json)
);
""".strip()
    payload = _run_postgres_json_query(sql=sql, database_url=database_url, database_url_env=database_url_env, psql_bin=psql_bin, print_only=print_only)
    data = payload.get("data") or {}
    return {
        "ok": bool(print_only or data.get("recorded", False)),
        "recorded": bool(print_only or data.get("recorded", False)),
        "step": row if print_only else dict(data.get("step", {}) or {}),
        "sql": payload.get("sql", ""),
        "command": payload.get("command", []),
        "command_text": payload.get("command_text", ""),
        "table_name": "agent_steps",
    }


def complete_agent_step_postgres_payload(
    *,
    agent_step_id: str,
    owner_user_id: str,
    output_json: Dict[str, Any] | None = None,
    validation_json: Dict[str, Any] | None = None,
    latency_ms: int | None = None,
    token_usage_json: Dict[str, Any] | None = None,
    cost_json: Dict[str, Any] | None = None,
    completed_at: str = "",
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    return _update_agent_step_status_postgres_payload(
        agent_step_id=agent_step_id,
        owner_user_id=owner_user_id,
        status="succeeded",
        output_json=output_json or {},
        validation_json=validation_json or {},
        latency_ms=latency_ms,
        token_usage_json=token_usage_json or {},
        cost_json=cost_json or {},
        completed_at=completed_at,
        error="",
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        print_only=print_only,
        ensure_schema=ensure_schema,
    )


def fail_agent_step_postgres_payload(
    *,
    agent_step_id: str,
    owner_user_id: str,
    error: str,
    output_json: Dict[str, Any] | None = None,
    validation_json: Dict[str, Any] | None = None,
    completed_at: str = "",
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    return _update_agent_step_status_postgres_payload(
        agent_step_id=agent_step_id,
        owner_user_id=owner_user_id,
        status="failed",
        output_json=output_json or {},
        validation_json=validation_json or {},
        latency_ms=None,
        token_usage_json={},
        cost_json={},
        completed_at=completed_at,
        error=error,
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        print_only=print_only,
        ensure_schema=ensure_schema,
    )


def _update_agent_step_status_postgres_payload(
    *,
    agent_step_id: str,
    owner_user_id: str,
    status: str,
    output_json: Dict[str, Any],
    validation_json: Dict[str, Any],
    latency_ms: int | None,
    token_usage_json: Dict[str, Any],
    cost_json: Dict[str, Any],
    completed_at: str,
    error: str,
    database_url: str,
    database_url_env: str,
    psql_bin: str,
    print_only: bool,
    ensure_schema: bool,
) -> Dict[str, Any]:
    safe_id = _require_agent_step_id(agent_step_id)
    owner = _require_owner_user_id(owner_user_id)
    completed_sql = _sql_nullable_timestamptz(completed_at) if completed_at else "now()"
    sql = _schema_prefix(ensure_schema) + f"""
WITH updated AS (
    UPDATE agent_steps
    SET status = {_sql_quote_text(status)},
        output_json = {_sql_jsonb(output_json)},
        validation_json = {_sql_jsonb(validation_json)},
        completed_at = {completed_sql},
        latency_ms = {_sql_nullable_int(latency_ms)},
        token_usage_json = {_sql_jsonb(token_usage_json)},
        cost_json = {_sql_jsonb(cost_json)},
        error = {_sql_quote_text(error)}
    WHERE agent_step_id = {_sql_quote_text(safe_id)}
      AND owner_user_id = {_sql_quote_text(owner)}
    RETURNING *
)
SELECT json_build_object(
    'updated', EXISTS (SELECT 1 FROM updated),
    'step', COALESCE((SELECT row_to_json(updated) FROM updated LIMIT 1), '{{}}'::json)
);
""".strip()
    payload = _run_postgres_json_query(sql=sql, database_url=database_url, database_url_env=database_url_env, psql_bin=psql_bin, print_only=print_only)
    data = payload.get("data") or {}
    return {
        "ok": bool(print_only or data.get("updated", False)),
        "updated": bool(print_only or data.get("updated", False)),
        "step": {
            "agent_step_id": safe_id,
            "owner_user_id": owner,
            "status": status,
            "output_json": output_json,
            "validation_json": validation_json,
            "error": _clean_text(error),
        } if print_only else dict(data.get("step", {}) or {}),
        "sql": payload.get("sql", ""),
        "command": payload.get("command", []),
        "command_text": payload.get("command_text", ""),
        "table_name": "agent_steps",
    }


def get_agent_run_postgres_payload(
    *,
    owner_user_id: str,
    agent_run_id: str,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    owner = _require_owner_user_id(owner_user_id)
    safe_id = _require_agent_run_id(agent_run_id)
    sql = _schema_prefix(ensure_schema) + f"""
SELECT json_build_object(
    'found', EXISTS (
        SELECT 1 FROM agent_runs
        WHERE owner_user_id = {_sql_quote_text(owner)}
          AND agent_run_id = {_sql_quote_text(safe_id)}
    ),
    'run', COALESCE((
        SELECT row_to_json(agent_runs) FROM agent_runs
        WHERE owner_user_id = {_sql_quote_text(owner)}
          AND agent_run_id = {_sql_quote_text(safe_id)}
        LIMIT 1
    ), '{{}}'::json)
);
""".strip()
    payload = _run_postgres_json_query(sql=sql, database_url=database_url, database_url_env=database_url_env, psql_bin=psql_bin, print_only=print_only)
    data = payload.get("data") or {}
    return {
        "ok": bool(print_only or data.get("found", False)),
        "found": bool(data.get("found", False)),
        "run": dict(data.get("run", {}) or {}),
        "sql": payload.get("sql", ""),
        "command": payload.get("command", []),
        "command_text": payload.get("command_text", ""),
    }


def list_agent_runs_postgres_payload(
    *,
    owner_user_id: str,
    pipeline_run_id: str = "",
    context_id: str = "",
    limit: int = 50,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    owner = _require_owner_user_id(owner_user_id)
    safe_limit = max(1, min(int(limit), 200))
    safe_pipeline_run_id = _clean_text(pipeline_run_id)
    safe_context_id = _clean_text(context_id)
    pipeline_filter = (
        f"AND pipeline_run_id = {_sql_quote_text(safe_pipeline_run_id)}"
        if safe_pipeline_run_id
        else ""
    )
    context_filter = (
        f"AND context_id = {_sql_quote_text(safe_context_id)}"
        if safe_context_id
        else ""
    )
    sql = _schema_prefix(ensure_schema) + f"""
WITH run_rows AS (
    SELECT * FROM agent_runs
    WHERE owner_user_id = {_sql_quote_text(owner)}
    {pipeline_filter}
    {context_filter}
    ORDER BY started_at DESC
    LIMIT {safe_limit}
)
SELECT json_build_object(
    'rows', COALESCE((SELECT json_agg(row_to_json(run_rows)) FROM run_rows), '[]'::json)
);
""".strip()
    payload = _run_postgres_json_query(sql=sql, database_url=database_url, database_url_env=database_url_env, psql_bin=psql_bin, print_only=print_only)
    rows = list((payload.get("data") or {}).get("rows", []) or [])
    return {
        "ok": True,
        "rows": rows,
        "runs": rows,
        "count": len(rows),
        "sql": payload.get("sql", ""),
        "command": payload.get("command", []),
        "command_text": payload.get("command_text", ""),
    }


def list_agent_steps_postgres_payload(
    *,
    owner_user_id: str,
    agent_run_id: str = "",
    pipeline_run_id: str = "",
    context_id: str = "",
    limit: int = 200,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    owner = _require_owner_user_id(owner_user_id)
    safe_limit = max(1, min(int(limit), 500))
    safe_agent_run_id = _clean_text(agent_run_id)
    safe_pipeline_run_id = _clean_text(pipeline_run_id)
    safe_context_id = _clean_text(context_id)
    run_filter = f"AND agent_run_id = {_sql_quote_text(safe_agent_run_id)}" if safe_agent_run_id else ""
    pipeline_filter = f"AND pipeline_run_id = {_sql_quote_text(safe_pipeline_run_id)}" if safe_pipeline_run_id else ""
    context_filter = f"AND context_id = {_sql_quote_text(safe_context_id)}" if safe_context_id else ""
    sql = _schema_prefix(ensure_schema) + f"""
WITH step_rows AS (
    SELECT * FROM agent_steps
    WHERE owner_user_id = {_sql_quote_text(owner)}
    {run_filter}
    {pipeline_filter}
    {context_filter}
    ORDER BY started_at ASC
    LIMIT {safe_limit}
)
SELECT json_build_object(
    'rows', COALESCE((SELECT json_agg(row_to_json(step_rows)) FROM step_rows), '[]'::json)
);
""".strip()
    payload = _run_postgres_json_query(sql=sql, database_url=database_url, database_url_env=database_url_env, psql_bin=psql_bin, print_only=print_only)
    rows = list((payload.get("data") or {}).get("rows", []) or [])
    return {
        "ok": True,
        "rows": rows,
        "steps": rows,
        "count": len(rows),
        "sql": payload.get("sql", ""),
        "command": payload.get("command", []),
        "command_text": payload.get("command_text", ""),
    }

_AGENT_TRACE_RUN_REQUIRED_FIELDS = (
    "agent_run_id",
    "owner_user_id",
    "status",
    "started_at",
)

_AGENT_TRACE_STEP_REQUIRED_FIELDS = (
    "agent_step_id",
    "agent_run_id",
    "owner_user_id",
    "agent_name",
    "status",
    "started_at",
)

_AGENT_TRACE_ERROR_STATUSES = {"error", "failed", "failure"}
_AGENT_TRACE_WARNING_STATUSES = {"blocked", "warning", "warn", "skipped"}


def _agent_trace_dict_rows(rows: Any) -> List[Dict[str, Any]]:
    if rows is None:
        return []
    if not isinstance(rows, list):
        raise ValueError("Agent trace rows must be provided as a list.")
    normalized: List[Dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Every agent trace row must be a dictionary.")
        normalized.append(dict(row))
    return normalized


def _agent_trace_status(value: Any) -> str:
    return _clean_text(value).lower() or "unknown"


def _agent_trace_counter_increment(counter: Dict[str, int], key: str) -> None:
    safe_key = _clean_text(key) or "unknown"
    counter[safe_key] = int(counter.get(safe_key, 0)) + 1


def _agent_trace_numeric(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = _clean_text(value)
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _agent_trace_json_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _agent_trace_missing_required_fields(
    *,
    rows: List[Dict[str, Any]],
    required_fields: tuple[str, ...],
    id_field: str,
) -> List[Dict[str, Any]]:
    missing_rows: List[Dict[str, Any]] = []
    for index, row in enumerate(rows):
        missing_fields = [
            field
            for field in required_fields
            if _clean_text(row.get(field)) == ""
        ]
        if missing_fields:
            missing_rows.append(
                {
                    "index": index,
                    id_field: _clean_text(row.get(id_field)),
                    "missing_fields": missing_fields,
                }
            )
    return missing_rows


def _agent_trace_latency_summary(steps: List[Dict[str, Any]]) -> Dict[str, Any]:
    values = [
        int(value)
        for value in (
            _agent_trace_numeric(step.get("latency_ms"))
            for step in steps
        )
        if value is not None
    ]
    if not values:
        return {
            "count": 0,
            "total_ms": 0,
            "min_ms": 0,
            "max_ms": 0,
            "average_ms": 0,
        }
    total = sum(values)
    return {
        "count": len(values),
        "total_ms": total,
        "min_ms": min(values),
        "max_ms": max(values),
        "average_ms": round(total / len(values), 2),
    }


def _agent_trace_model_usage_summary(steps: List[Dict[str, Any]]) -> Dict[str, Any]:
    model_counts: Dict[str, int] = {}
    provider_counts: Dict[str, int] = {}
    for step in steps:
        provider = _clean_text(step.get("model_provider"))
        model = _clean_text(step.get("model_name"))
        if provider:
            _agent_trace_counter_increment(provider_counts, provider)
        if model or provider:
            model_key = f"{provider}/{model}".strip("/")
            _agent_trace_counter_increment(model_counts, model_key)
    return {
        "provider_counts": dict(sorted(provider_counts.items())),
        "model_counts": dict(sorted(model_counts.items())),
    }


def _agent_trace_token_summary(steps: List[Dict[str, Any]]) -> Dict[str, Any]:
    totals: Dict[str, int] = {}
    for step in steps:
        token_usage = _agent_trace_json_dict(step.get("token_usage_json"))
        for key, value in token_usage.items():
            numeric = _agent_trace_numeric(value)
            if numeric is not None:
                totals[str(key)] = int(totals.get(str(key), 0)) + int(numeric)
    return dict(sorted(totals.items()))


def _agent_trace_cost_summary(steps: List[Dict[str, Any]]) -> Dict[str, Any]:
    totals: Dict[str, float] = {}
    for step in steps:
        cost = _agent_trace_json_dict(step.get("cost_json"))
        for key, value in cost.items():
            numeric = _agent_trace_numeric(value)
            if numeric is not None:
                totals[str(key)] = float(totals.get(str(key), 0.0)) + float(numeric)
    return {key: round(value, 6) for key, value in sorted(totals.items())}


def build_agent_trace_summary_payload(
    *,
    agent_runs: List[Dict[str, Any]] | None = None,
    agent_steps: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """Build a deterministic read-only summary for existing agent trace rows.

    This helper is intentionally in-memory only. It does not read from or write to
    Postgres, does not call external services, and does not mutate input rows.
    """

    runs = _agent_trace_dict_rows(agent_runs)
    steps = _agent_trace_dict_rows(agent_steps)

    run_status_counts: Dict[str, int] = {}
    step_status_counts: Dict[str, int] = {}
    agent_counts: Dict[str, int] = {}

    error_step_count = 0
    warning_step_count = 0
    completed_step_count = 0

    for run in runs:
        _agent_trace_counter_increment(
            run_status_counts,
            _agent_trace_status(run.get("status")),
        )

    for step in steps:
        status = _agent_trace_status(step.get("status"))
        _agent_trace_counter_increment(step_status_counts, status)
        _agent_trace_counter_increment(agent_counts, _clean_text(step.get("agent_name")))

        has_error = bool(_clean_text(step.get("error"))) or status in _AGENT_TRACE_ERROR_STATUSES
        has_warning = status in _AGENT_TRACE_WARNING_STATUSES
        is_completed = bool(_clean_text(step.get("completed_at")))

        if has_error:
            error_step_count += 1
        if has_warning:
            warning_step_count += 1
        if is_completed:
            completed_step_count += 1

    missing_required_fields = {
        "agent_runs": _agent_trace_missing_required_fields(
            rows=runs,
            required_fields=_AGENT_TRACE_RUN_REQUIRED_FIELDS,
            id_field="agent_run_id",
        ),
        "agent_steps": _agent_trace_missing_required_fields(
            rows=steps,
            required_fields=_AGENT_TRACE_STEP_REQUIRED_FIELDS,
            id_field="agent_step_id",
        ),
    }

    all_required_fields_present = not (
        missing_required_fields["agent_runs"]
        or missing_required_fields["agent_steps"]
    )

    return {
        "ok": True,
        "summary_type": "agent_trace",
        "run_count": len(runs),
        "step_count": len(steps),
        "completed_step_count": completed_step_count,
        "error_step_count": error_step_count,
        "warning_step_count": warning_step_count,
        "run_status_counts": dict(sorted(run_status_counts.items())),
        "step_status_counts": dict(sorted(step_status_counts.items())),
        "agent_counts": dict(sorted(agent_counts.items())),
        "latency_summary": _agent_trace_latency_summary(steps),
        "model_usage_summary": _agent_trace_model_usage_summary(steps),
        "token_usage_summary": _agent_trace_token_summary(steps),
        "cost_summary": _agent_trace_cost_summary(steps),
        "missing_required_fields": missing_required_fields,
        "all_required_fields_present": all_required_fields_present,
        "safety_metadata": {
            "did_read_database": False,
            "did_write_database": False,
            "did_create_agent_run": False,
            "did_create_agent_step": False,
            "did_update_agent_run": False,
            "did_update_agent_step": False,
            "did_call_llm": False,
            "did_change_pipeline": False,
            "did_change_scoring": False,
            "did_change_approval": False,
            "did_execute_application": False,
            "did_submit_application": False,
        },
    }

