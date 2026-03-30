from __future__ import annotations

import hashlib
import json
import os
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlsplit, urlunsplit

DEFAULT_NOTIFICATION_STATE_SCHEMA_SQL_PATH = Path("src/storage/notification_state/schema.sql")


def _json_compact(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


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

    if ":" in userinfo:
        username, _password = userinfo.split(":", 1)
        redacted_userinfo = f"{username}:***"
    else:
        redacted_userinfo = "***"

    return urlunsplit(
        (
            parts.scheme,
            f"{redacted_userinfo}@{hostinfo}",
            parts.path,
            parts.query,
            parts.fragment,
        )
    )


def _sql_quote_text(value: Any) -> str:
    text = str(value or "")
    return "'" + text.replace("'", "''") + "'"


def _read_sql_artifact(path: Path, label: str) -> str:
    resolved = Path(path)
    if not resolved.exists():
        raise ValueError(f"Missing {label} SQL file: {resolved}")

    sql = resolved.read_text(encoding="utf-8")
    if not sql.strip():
        raise ValueError(f"{label.capitalize()} SQL file is empty: {resolved}")

    return sql


def _normalize_notification_read_flag(value: Any) -> bool:
    if isinstance(value, bool):
        return value

    raw = str(value if value is not None else "").strip().lower()

    if raw in {"1", "true", "yes", "y", "read"}:
        return True
    if raw in {"0", "false", "no", "n", "off", "unread"}:
        return False

    raise ValueError("is_read must be a boolean-like value.")


def _build_state_id(normalized_row: Dict[str, Any]) -> str:
    signature_payload = {
        "state_timestamp": normalized_row["state_timestamp"],
        "notification_id": normalized_row["notification_id"],
        "is_read": normalized_row["is_read"],
    }
    blob = _json_compact(signature_payload)
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()


def notification_state_db_row(record: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(record, dict):
        raise ValueError("Notification state record must be a dictionary.")

    state_timestamp = _clean_text(record.get("state_timestamp"))
    if not state_timestamp:
        raise ValueError("Notification state record is missing required field: state_timestamp")

    notification_id = _clean_text(record.get("notification_id"))
    if not notification_id:
        raise ValueError("Notification state record is missing required field: notification_id")

    is_read = _normalize_notification_read_flag(record.get("is_read"))

    normalized_row = {
        "state_timestamp": state_timestamp,
        "notification_id": notification_id,
        "is_read": is_read,
    }
    normalized_row["state_id"] = _build_state_id(normalized_row)
    return normalized_row


def notification_state_table_specs() -> Dict[str, Any]:
    return {
        "notification_state_events": {
            "description": "Append-only operational history of notification read/unread state changes.",
            "primary_key": ["state_id"],
            "columns": [
                {"name": "state_id", "type": "text", "nullable": False},
                {"name": "state_timestamp", "type": "timestamptz", "nullable": False},
                {"name": "notification_id", "type": "text", "nullable": False},
                {"name": "is_read", "type": "boolean", "nullable": False},
            ],
            "indexes": [
                {"name": "idx_notification_state_notification_timestamp", "columns": ["notification_id", "state_timestamp"]},
                {"name": "idx_notification_state_is_read_timestamp", "columns": ["is_read", "state_timestamp"]},
            ],
        }
    }


def render_notification_state_schema_sql() -> str:
    return "\n".join(
        [
            "CREATE TABLE IF NOT EXISTS notification_state_events (",
            "    state_id TEXT PRIMARY KEY,",
            "    state_timestamp TIMESTAMPTZ NOT NULL,",
            "    notification_id TEXT NOT NULL,",
            "    is_read BOOLEAN NOT NULL",
            ");",
            "",
            "CREATE INDEX IF NOT EXISTS idx_notification_state_notification_timestamp",
            "ON notification_state_events (notification_id, state_timestamp DESC);",
            "",
            "CREATE INDEX IF NOT EXISTS idx_notification_state_is_read_timestamp",
            "ON notification_state_events (is_read, state_timestamp DESC);",
        ]
    )


def notification_state_schema_sql_text(
    schema_path: Path = DEFAULT_NOTIFICATION_STATE_SCHEMA_SQL_PATH,
) -> str:
    return _read_sql_artifact(schema_path, "notification state schema")


def notification_state_schema_sql_payload(
    schema_path: Path = DEFAULT_NOTIFICATION_STATE_SCHEMA_SQL_PATH,
) -> Dict[str, Any]:
    sql = notification_state_schema_sql_text(schema_path)
    return {
        "path": str(Path(schema_path)),
        "sql": sql,
    }


def notification_state_schema_sql_generation_payload(
    schema_path: Path = DEFAULT_NOTIFICATION_STATE_SCHEMA_SQL_PATH,
) -> Dict[str, Any]:
    generated_sql = render_notification_state_schema_sql()
    artifact_sql = notification_state_schema_sql_text(schema_path)

    return {
        "artifact_path": str(Path(schema_path)),
        "artifact_sql": artifact_sql,
        "generated_sql": generated_sql,
        "matches_artifact": generated_sql.strip() == artifact_sql.strip(),
    }


def notification_state_contract_health_payload() -> Dict[str, Any]:
    schema_generation = notification_state_schema_sql_generation_payload()

    return {
        "ok": True,
        "artifacts": {
            "schema_sql_path": str(DEFAULT_NOTIFICATION_STATE_SCHEMA_SQL_PATH),
        },
        "checks": {
            "schema_sql_matches_artifact": bool(schema_generation["matches_artifact"]),
        },
        "all_checks_pass": bool(schema_generation["matches_artifact"]),
    }


def _build_insert_sql(row: Dict[str, Any]) -> str:
    bool_literal = "TRUE" if row["is_read"] else "FALSE"

    return "\n".join(
        [
            "INSERT INTO notification_state_events (",
            "    state_id,",
            "    state_timestamp,",
            "    notification_id,",
            "    is_read",
            ")",
            "VALUES (",
            f"    {_sql_quote_text(row['state_id'])},",
            f"    {_sql_quote_text(row['state_timestamp'])}::timestamptz,",
            f"    {_sql_quote_text(row['notification_id'])},",
            f"    {bool_literal}",
            ")",
            "ON CONFLICT (state_id) DO NOTHING;",
        ]
    )


def insert_notification_state_row_to_postgres(
    *,
    record: Dict[str, Any],
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    allow_contract_drift: bool = False,
) -> Dict[str, Any]:
    contract_health = notification_state_contract_health_payload()
    if not contract_health.get("all_checks_pass", False) and not allow_contract_drift:
        raise SystemExit(
            "Notification-state contract health check failed. Refusing Postgres insert while artifacts are drifting. "
            "Fix the schema artifact mismatch first, or pass --allow-contract-drift if you intentionally want to override."
        )

    row = notification_state_db_row(record)
    sql = _build_insert_sql(row)

    database_url_value = _resolve_database_url(
        database_url,
        database_url_env,
        allow_placeholder=bool(print_only),
    )

    cmd: List[str] = [
        str(psql_bin),
        database_url_value,
        "-X",
        "-v",
        "ON_ERROR_STOP=1",
        "-c",
        sql,
    ]

    redacted_cmd = list(cmd)
    redacted_cmd[1] = _redact_database_url(redacted_cmd[1])

    payload: Dict[str, Any] = {
        "ok": True,
        "contract_health_ok": bool(contract_health["all_checks_pass"]),
        "row": row,
        "command": redacted_cmd,
        "command_text": shlex.join(redacted_cmd),
        "table_name": "notification_state_events",
    }

    if print_only:
        return payload

    if shutil.which(str(psql_bin)) is None:
        raise SystemExit(
            f"psql executable not found on PATH: {psql_bin!r}. "
            "Install psql or pass --psql-bin with the correct executable path."
        )

    subprocess.run(cmd, check=True)
    return payload