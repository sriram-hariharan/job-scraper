from __future__ import annotations

from collections import Counter
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


DEFAULT_AGENT_FEEDBACK_SCHEMA_SQL_PATH = Path("src/storage/agent_feedback/schema.sql")

SUPPORTED_AGENT_FEEDBACK_EVENT_TYPES = {
    "suggestion_accepted",
    "suggestion_rejected",
    "suggestion_edited",
    "job_applied",
    "job_skipped",
    "job_saved",
    "resume_selected",
    "scan_rerun",
    "operator_lane_overridden",
    "agentic_review_helpful",
    "agentic_review_not_helpful",
}

SUPPORTED_AGENT_FEEDBACK_TARGET_TYPES = {
    "tailoring_suggestion",
    "scan_issue",
    "pipeline_run_job",
    "job_packet",
    "resume_variant",
    "operator_review_lane",
    "agentic_review_section",
}

AGENT_FEEDBACK_EXPORT_VERSION = "agent_feedback_export_v1"

AGENT_FEEDBACK_LABELS = {
    "suggestion_accepted": "positive",
    "suggestion_rejected": "negative",
    "agentic_review_helpful": "positive",
    "agentic_review_not_helpful": "negative",
    "job_applied": "positive",
    "job_skipped": "negative",
    "job_saved": "neutral_positive",
    "suggestion_edited": "mixed",
    "resume_selected": "positive",
    "scan_rerun": "neutral",
    "operator_lane_overridden": "correction",
}

AGENT_FEEDBACK_LABEL_VALUES = {
    "positive": 1.0,
    "negative": -1.0,
    "neutral_positive": 0.5,
    "mixed": 0.0,
    "neutral": 0.0,
    "correction": 0.0,
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


def _sql_nullable_text(value: Any) -> str:
    text = _clean_text(value)
    return "NULL" if not text else _sql_quote_text(text)


def _sql_jsonb(value: Any) -> str:
    return f"{_sql_quote_text(_json_compact(value))}::jsonb"


def _read_sql_artifact(path: Path, label: str) -> str:
    resolved = Path(path)
    if not resolved.exists():
        raise ValueError(f"Missing {label} SQL file: {resolved}")
    sql = resolved.read_text(encoding="utf-8")
    if not sql.strip():
        raise ValueError(f"{label.capitalize()} SQL file is empty: {resolved}")
    return sql


def agent_feedback_schema_sql_text(
    schema_path: Path = DEFAULT_AGENT_FEEDBACK_SCHEMA_SQL_PATH,
) -> str:
    return _read_sql_artifact(schema_path, "agent feedback schema")


def render_agent_feedback_schema_sql() -> str:
    return "\n".join(
        [
            "CREATE TABLE IF NOT EXISTS agent_feedback_events (",
            "    event_id TEXT PRIMARY KEY,",
            "    owner_user_id TEXT NOT NULL REFERENCES auth_users(user_id) ON DELETE CASCADE,",
            "    pipeline_run_id TEXT,",
            "    context_id TEXT,",
            "    agent_run_id TEXT,",
            "    agent_step_id TEXT,",
            "    target_type TEXT NOT NULL,",
            "    target_id TEXT NOT NULL,",
            "    event_type TEXT NOT NULL,",
            "    payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,",
            "    source TEXT NOT NULL DEFAULT '',",
            "    created_at TIMESTAMPTZ NOT NULL",
            ");",
            "",
            "CREATE INDEX IF NOT EXISTS idx_agent_feedback_events_owner_created",
            "ON agent_feedback_events (owner_user_id, created_at DESC);",
            "",
            "CREATE INDEX IF NOT EXISTS idx_agent_feedback_events_owner_event_type_created",
            "ON agent_feedback_events (owner_user_id, event_type, created_at DESC);",
            "",
            "CREATE INDEX IF NOT EXISTS idx_agent_feedback_events_owner_target_created",
            "ON agent_feedback_events (owner_user_id, target_type, target_id, created_at DESC);",
            "",
            "CREATE INDEX IF NOT EXISTS idx_agent_feedback_events_pipeline_created",
            "ON agent_feedback_events (pipeline_run_id, created_at DESC);",
        ]
    )


def agent_feedback_schema_sql_generation_payload(
    schema_path: Path = DEFAULT_AGENT_FEEDBACK_SCHEMA_SQL_PATH,
) -> Dict[str, Any]:
    generated_sql = render_agent_feedback_schema_sql()
    artifact_sql = agent_feedback_schema_sql_text(schema_path)
    return {
        "artifact_path": str(Path(schema_path)),
        "artifact_sql": artifact_sql,
        "generated_sql": generated_sql,
        "matches_artifact": generated_sql.strip() == artifact_sql.strip(),
    }


def agent_feedback_table_specs() -> Dict[str, Any]:
    return {
        "agent_feedback_events": {
            "primary_key": ["event_id"],
            "owner_column": "owner_user_id",
            "columns": [
                "event_id",
                "owner_user_id",
                "pipeline_run_id",
                "context_id",
                "agent_run_id",
                "agent_step_id",
                "target_type",
                "target_id",
                "event_type",
                "payload_json",
                "source",
                "created_at",
            ],
        },
    }


def agent_feedback_contract_health_payload() -> Dict[str, Any]:
    schema_generation = agent_feedback_schema_sql_generation_payload()
    return {
        "ok": True,
        "artifacts": {"schema_sql_path": str(DEFAULT_AGENT_FEEDBACK_SCHEMA_SQL_PATH)},
        "checks": {
            "schema_sql_matches_artifact": bool(schema_generation["matches_artifact"]),
        },
        "all_checks_pass": bool(schema_generation["matches_artifact"]),
        "event_types": sorted(SUPPORTED_AGENT_FEEDBACK_EVENT_TYPES),
        "target_types": sorted(SUPPORTED_AGENT_FEEDBACK_TARGET_TYPES),
        "table_specs": agent_feedback_table_specs(),
    }


def _resolve_database_url(
    explicit_value: str,
    env_var_name: str,
    *,
    allow_placeholder: bool,
) -> str:
    explicit = _clean_text(explicit_value)
    if explicit:
        return explicit
    env_name = _clean_text(env_var_name) or "DATABASE_URL"
    env_value = _clean_text(os.environ.get(env_name, ""))
    if env_value:
        return env_value
    if allow_placeholder:
        return f"${env_name}"
    raise SystemExit(
        f"Database URL is required. Pass --database-url or set {env_name} in the environment."
    )


def _redact_database_url(value: str) -> str:
    raw = _clean_text(value)
    if not raw:
        return raw
    parts = urlsplit(raw)
    if "@" not in parts.netloc:
        return raw
    userinfo, hostinfo = parts.netloc.rsplit("@", 1)
    redacted_userinfo = f"{userinfo.split(':', 1)[0]}:***" if ":" in userinfo else "***"
    return urlunsplit((parts.scheme, f"{redacted_userinfo}@{hostinfo}", parts.path, parts.query, parts.fragment))


def _feedback_query_payload_from_row(payload: Dict[str, Any], row: Any) -> Dict[str, Any]:
    if not row:
        raise SystemExit("Postgres returned empty output for agent-feedback query.")
    raw_json = row[0]
    if isinstance(raw_json, dict):
        data = raw_json
    else:
        raw_json = _clean_text(raw_json)
        if not raw_json:
            raise SystemExit("Postgres returned empty JSON for agent-feedback query.")
        try:
            data = json.loads(raw_json)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Failed to parse agent-feedback query JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit("Agent-feedback query did not return a JSON object.")
    payload["data"] = data
    return payload


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
        return _feedback_query_payload_from_row(payload, row)

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
        raise SystemExit("Postgres returned empty output for agent-feedback query.")
    return _feedback_query_payload_from_row(payload, [stdout_lines[-1]])


def _schema_prefix(ensure_schema: bool) -> str:
    return agent_feedback_schema_sql_text() + "\n\n" if ensure_schema else ""


def _require_owner_user_id(owner_user_id: Any) -> str:
    owner = _clean_text(owner_user_id)
    if not owner:
        raise ValueError("owner_user_id is required.")
    return owner


def _require_known_event_type(event_type: Any) -> str:
    safe_type = _clean_text(event_type)
    if safe_type not in SUPPORTED_AGENT_FEEDBACK_EVENT_TYPES:
        raise ValueError(f"Unsupported agent feedback event_type: {safe_type or '<empty>'}.")
    return safe_type


def _require_known_target_type(target_type: Any) -> str:
    safe_type = _clean_text(target_type)
    if safe_type not in SUPPORTED_AGENT_FEEDBACK_TARGET_TYPES:
        raise ValueError(f"Unsupported agent feedback target_type: {safe_type or '<empty>'}.")
    return safe_type


def _require_payload_json(payload_json: Any) -> Dict[str, Any]:
    if payload_json is None:
        return {}
    if not isinstance(payload_json, dict):
        raise ValueError("payload_json must be a JSON object.")
    return dict(payload_json)


def build_agent_feedback_event_id(record: Dict[str, Any]) -> str:
    signature = {
        "owner_user_id": _clean_text(record.get("owner_user_id")),
        "pipeline_run_id": _clean_text(record.get("pipeline_run_id")),
        "context_id": _clean_text(record.get("context_id")),
        "agent_run_id": _clean_text(record.get("agent_run_id")),
        "agent_step_id": _clean_text(record.get("agent_step_id")),
        "target_type": _clean_text(record.get("target_type")),
        "target_id": _clean_text(record.get("target_id")),
        "event_type": _clean_text(record.get("event_type")),
        "payload_json": record.get("payload_json") or {},
        "source": _clean_text(record.get("source")),
        "created_at": _clean_text(record.get("created_at")),
    }
    return "agent_feedback_" + hashlib.sha1(_json_compact(signature).encode("utf-8")).hexdigest()


def agent_feedback_event_db_row(record: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(record, dict):
        raise ValueError("Agent feedback event record must be a dictionary.")
    row = {
        "event_id": _clean_text(record.get("event_id")),
        "owner_user_id": _require_owner_user_id(record.get("owner_user_id")),
        "pipeline_run_id": _clean_text(record.get("pipeline_run_id") or record.get("run_id")),
        "context_id": _clean_text(record.get("context_id")),
        "agent_run_id": _clean_text(record.get("agent_run_id")),
        "agent_step_id": _clean_text(record.get("agent_step_id")),
        "target_type": _require_known_target_type(record.get("target_type")),
        "target_id": _clean_text(record.get("target_id")),
        "event_type": _require_known_event_type(record.get("event_type")),
        "payload_json": _require_payload_json(record.get("payload_json")),
        "source": _clean_text(record.get("source")) or "api",
        "created_at": _clean_text(record.get("created_at")) or _utc_now_iso(),
    }
    if not row["target_id"]:
        raise ValueError("target_id is required.")
    if not row["event_id"]:
        row["event_id"] = build_agent_feedback_event_id(row)
    return row


def record_agent_feedback_event(
    *,
    record: Dict[str, Any],
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    row = agent_feedback_event_db_row(record)
    sql = _schema_prefix(ensure_schema) + f"""
WITH inserted AS (
    INSERT INTO agent_feedback_events (
        event_id, owner_user_id, pipeline_run_id, context_id, agent_run_id,
        agent_step_id, target_type, target_id, event_type, payload_json,
        source, created_at
    )
    VALUES (
        {_sql_quote_text(row['event_id'])},
        {_sql_quote_text(row['owner_user_id'])},
        {_sql_nullable_text(row['pipeline_run_id'])},
        {_sql_nullable_text(row['context_id'])},
        {_sql_nullable_text(row['agent_run_id'])},
        {_sql_nullable_text(row['agent_step_id'])},
        {_sql_quote_text(row['target_type'])},
        {_sql_quote_text(row['target_id'])},
        {_sql_quote_text(row['event_type'])},
        {_sql_jsonb(row['payload_json'])},
        {_sql_quote_text(row['source'])},
        {_sql_quote_text(row['created_at'])}::timestamptz
    )
    ON CONFLICT (event_id) DO NOTHING
    RETURNING *
)
SELECT json_build_object(
    'recorded', EXISTS (SELECT 1 FROM inserted),
    'event', COALESCE((SELECT row_to_json(inserted) FROM inserted LIMIT 1), '{{}}'::json)
);
""".strip()
    payload = _run_postgres_json_query(
        sql=sql,
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        print_only=print_only,
    )
    data = payload.get("data") or {}
    return {
        "ok": bool(print_only or data.get("recorded", False)),
        "recorded": bool(print_only or data.get("recorded", False)),
        "event": row if print_only else dict(data.get("event", {}) or {}),
        "sql": payload.get("sql", ""),
        "command": payload.get("command", []),
        "command_text": payload.get("command_text", ""),
        "table_name": "agent_feedback_events",
    }


def list_agent_feedback_events(
    *,
    owner_user_id: str,
    pipeline_run_id: str = "",
    context_id: str = "",
    agent_run_id: str = "",
    target_type: str = "",
    event_type: str = "",
    limit: int = 200,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    owner = _require_owner_user_id(owner_user_id)
    safe_limit = max(1, min(int(limit), 1000))
    filters = [
        f"owner_user_id = {_sql_quote_text(owner)}",
    ]
    for column, value in [
        ("pipeline_run_id", pipeline_run_id),
        ("context_id", context_id),
        ("agent_run_id", agent_run_id),
        ("target_type", target_type),
        ("event_type", event_type),
    ]:
        text = _clean_text(value)
        if text:
            filters.append(f"{column} = {_sql_quote_text(text)}")
    where_sql = "\n      AND ".join(filters)
    sql = _schema_prefix(ensure_schema) + f"""
WITH event_rows AS (
    SELECT * FROM agent_feedback_events
    WHERE {where_sql}
    ORDER BY created_at DESC, event_id DESC
    LIMIT {safe_limit}
)
SELECT json_build_object(
    'rows', COALESCE((SELECT json_agg(row_to_json(event_rows)) FROM event_rows), '[]'::json)
);
""".strip()
    payload = _run_postgres_json_query(
        sql=sql,
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        print_only=print_only,
    )
    rows = list((payload.get("data") or {}).get("rows", []) or [])
    return {
        "ok": True,
        "rows": rows,
        "events": rows,
        "count": len(rows),
        "sql": payload.get("sql", ""),
        "command": payload.get("command", []),
        "command_text": payload.get("command_text", ""),
    }


def summarize_agent_feedback_events(
    *,
    owner_user_id: str,
    pipeline_run_id: str = "",
    context_id: str = "",
    target_type: str = "",
    event_type: str = "",
    limit: int = 1000,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    listed = list_agent_feedback_events(
        owner_user_id=owner_user_id,
        pipeline_run_id=pipeline_run_id,
        context_id=context_id,
        target_type=target_type,
        event_type=event_type,
        limit=limit,
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        print_only=print_only,
        ensure_schema=ensure_schema,
    )
    rows = [dict(row or {}) for row in list(listed.get("events", []) or [])]
    event_type_counts = Counter(_clean_text(row.get("event_type")) for row in rows)
    target_type_counts = Counter(_clean_text(row.get("target_type")) for row in rows)
    event_type_counts.pop("", None)
    target_type_counts.pop("", None)
    latest_event_at = ""
    for row in rows:
        created_at = _clean_text(row.get("created_at"))
        if created_at and (not latest_event_at or created_at > latest_event_at):
            latest_event_at = created_at
    return {
        "ok": True,
        "owner_user_id": _clean_text(owner_user_id),
        "pipeline_run_id": _clean_text(pipeline_run_id),
        "context_id": _clean_text(context_id),
        "target_type": _clean_text(target_type),
        "event_type": _clean_text(event_type),
        "summary": {
            "total_events": len(rows),
            "event_type_counts": dict(sorted(event_type_counts.items())),
            "target_type_counts": dict(sorted(target_type_counts.items())),
            "latest_event_at": latest_event_at,
        },
        "events": rows,
        "sql": listed.get("sql", ""),
        "command": listed.get("command", []),
        "command_text": listed.get("command_text", ""),
    }


def feedback_label_for_event_type(event_type: Any) -> str:
    return AGENT_FEEDBACK_LABELS.get(_clean_text(event_type), "unmapped")


def feedback_value_for_label(label: Any) -> float:
    return float(AGENT_FEEDBACK_LABEL_VALUES.get(_clean_text(label), 0.0))


def build_agent_feedback_evaluation_dataset(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for event in list(events or []):
        if not isinstance(event, dict):
            continue
        event_type = _clean_text(event.get("event_type"))
        feedback_label = feedback_label_for_event_type(event_type)
        rows.append(
            {
                "feedback_event_id": _clean_text(event.get("event_id")),
                "pipeline_run_id": _clean_text(event.get("pipeline_run_id")),
                "context_id": _clean_text(event.get("context_id")),
                "agent_run_id": _clean_text(event.get("agent_run_id")),
                "agent_step_id": _clean_text(event.get("agent_step_id")),
                "target_type": _clean_text(event.get("target_type")),
                "target_id": _clean_text(event.get("target_id")),
                "event_type": event_type,
                "feedback_label": feedback_label,
                "feedback_value": feedback_value_for_label(feedback_label),
                "source": _clean_text(event.get("source")),
                "created_at": _clean_text(event.get("created_at")),
            }
        )
    return rows


def _agent_feedback_counts(events: List[Dict[str, Any]], key: str) -> Dict[str, int]:
    counts = Counter(_clean_text(event.get(key)) for event in events if isinstance(event, dict))
    counts.pop("", None)
    return dict(sorted(counts.items()))


def export_agent_feedback_events(
    *,
    owner_user_id: str,
    pipeline_run_id: str = "",
    target_type: str = "",
    event_type: str = "",
    limit: int = 1000,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    owner = _require_owner_user_id(owner_user_id)
    listed = list_agent_feedback_events(
        owner_user_id=owner,
        pipeline_run_id=pipeline_run_id,
        target_type=target_type,
        event_type=event_type,
        limit=limit,
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        print_only=print_only,
        ensure_schema=ensure_schema,
    )
    events = [dict(row or {}) for row in list(listed.get("events", []) or [])]
    evaluation_rows = build_agent_feedback_evaluation_dataset(events)
    return {
        "ok": True,
        "export_version": AGENT_FEEDBACK_EXPORT_VERSION,
        "owner_user_id": owner,
        "pipeline_run_id": _clean_text(pipeline_run_id),
        "target_type": _clean_text(target_type),
        "event_type": _clean_text(event_type),
        "generated_at_utc": _utc_now_iso(),
        "total_events": len(events),
        "event_type_counts": _agent_feedback_counts(events, "event_type"),
        "target_type_counts": _agent_feedback_counts(events, "target_type"),
        "events": events,
        "evaluation_rows": evaluation_rows,
        "sql": listed.get("sql", ""),
        "command": listed.get("command", []),
        "command_text": listed.get("command_text", ""),
    }


def render_agent_feedback_export_markdown(export_payload: Dict[str, Any]) -> str:
    payload = export_payload if isinstance(export_payload, dict) else {}
    lines = [
        "# Agent Feedback Export",
        "",
        f"Export version: `{_clean_text(payload.get('export_version'))}`",
        f"Generated at UTC: `{_clean_text(payload.get('generated_at_utc'))}`",
        f"Owner user id: `{_clean_text(payload.get('owner_user_id'))}`",
        f"Pipeline run filter: `{_clean_text(payload.get('pipeline_run_id')) or 'all'}`",
        f"Total events: `{int(payload.get('total_events') or 0)}`",
        "",
        "## Event Type Counts",
        "",
    ]
    event_counts = payload.get("event_type_counts") if isinstance(payload.get("event_type_counts"), dict) else {}
    target_counts = payload.get("target_type_counts") if isinstance(payload.get("target_type_counts"), dict) else {}
    if event_counts:
        lines.extend(f"- `{key}`: {value}" for key, value in sorted(event_counts.items()))
    else:
        lines.append("None")
    lines.extend(["", "## Target Type Counts", ""])
    if target_counts:
        lines.extend(f"- `{key}`: {value}" for key, value in sorted(target_counts.items()))
    else:
        lines.append("None")
    lines.extend(["", "## Evaluation Dataset", ""])
    lines.append(f"Rows: `{len(list(payload.get('evaluation_rows') or []))}`")
    return "\n".join(lines).strip() + "\n"


record_agent_feedback_event_postgres_payload = record_agent_feedback_event
list_agent_feedback_events_postgres_payload = list_agent_feedback_events
summarize_agent_feedback_events_postgres_payload = summarize_agent_feedback_events
export_agent_feedback_events_postgres_payload = export_agent_feedback_events
