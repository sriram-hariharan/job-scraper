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

DEFAULT_APPLICATION_ACTIONS_SCHEMA_SQL_PATH = Path("src/storage/application_actions/schema.sql")


def _json_compact(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _normalize_text(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


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


def _normalize_application_status(value: Any) -> str:
    normalized = _clean_text(value).upper().replace(" ", "_")
    if not normalized:
        raise ValueError("application_status is required.")

    allowed = {
        "OPENED",
        "APPLIED",
        "SAVED",
        "NOT_APPLIED",
        "DISMISSED",
    }
    if normalized not in allowed:
        raise ValueError(
            f"Invalid application_status={normalized!r}. Allowed values: {', '.join(sorted(allowed))}"
        )

    return normalized


def _application_action_key(record: Dict[str, Any]) -> str:
    job_doc_id = _clean_text(record.get("job_doc_id"))
    if job_doc_id:
        return f"job_doc_id::{job_doc_id}"

    job_url = _clean_text(record.get("job_url"))
    if job_url:
        return f"job_url::{job_url}"

    company = _normalize_text(record.get("job_company"))
    title = _normalize_text(record.get("job_title"))
    if company or title:
        return f"title::{company}||{title}"

    return ""


def _build_action_id(normalized_row: Dict[str, Any]) -> str:
    signature_payload = {
        "action_timestamp": normalized_row["action_timestamp"],
        "action_key": normalized_row["action_key"],
        "job_doc_id": normalized_row["job_doc_id"],
        "job_url": normalized_row["job_url"],
        "job_company": normalized_row["job_company"],
        "job_title": normalized_row["job_title"],
        "application_status": normalized_row["application_status"],
        "source_view": normalized_row["source_view"],
        "note": normalized_row["note"],
    }
    blob = _json_compact(signature_payload)
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()


def application_action_db_row(record: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(record, dict):
        raise ValueError("Application action record must be a dictionary.")

    action_timestamp = _clean_text(record.get("action_timestamp"))
    if not action_timestamp:
        raise ValueError("Application action record is missing required field: action_timestamp")

    normalized_row = {
        "action_timestamp": action_timestamp,
        "job_doc_id": _clean_text(record.get("job_doc_id")),
        "job_url": _clean_text(record.get("job_url")),
        "job_company": _clean_text(record.get("job_company")),
        "job_title": _clean_text(record.get("job_title")),
        "application_status": _normalize_application_status(record.get("application_status")),
        "source_view": _clean_text(record.get("source_view")),
        "note": _clean_text(record.get("note")),
    }

    action_key = _application_action_key(normalized_row)
    if not action_key:
        raise ValueError(
            "Application action requires job_doc_id, job_url, or job_company + job_title."
        )

    normalized_row["action_key"] = action_key
    normalized_row["action_id"] = _build_action_id(normalized_row)
    return normalized_row


def application_actions_table_specs() -> Dict[str, Any]:
    return {
        "application_actions": {
            "description": "Append-only operational history of user application actions.",
            "primary_key": ["action_id"],
            "columns": [
                {"name": "action_id", "type": "text", "nullable": False},
                {"name": "action_key", "type": "text", "nullable": False},
                {"name": "action_timestamp", "type": "timestamptz", "nullable": False},
                {"name": "job_doc_id", "type": "text", "nullable": False},
                {"name": "job_url", "type": "text", "nullable": False},
                {"name": "job_company", "type": "text", "nullable": False},
                {"name": "job_title", "type": "text", "nullable": False},
                {"name": "application_status", "type": "text", "nullable": False},
                {"name": "source_view", "type": "text", "nullable": False},
                {"name": "note", "type": "text", "nullable": False},
            ],
            "indexes": [
                {"name": "idx_application_actions_action_key_timestamp", "columns": ["action_key", "action_timestamp"]},
                {"name": "idx_application_actions_status_timestamp", "columns": ["application_status", "action_timestamp"]},
                {"name": "idx_application_actions_company_title", "columns": ["job_company", "job_title"]},
            ],
        }
    }


def render_application_actions_schema_sql() -> str:
    return "\n".join(
        [
            "CREATE TABLE IF NOT EXISTS application_actions (",
            "    action_id TEXT PRIMARY KEY,",
            "    action_key TEXT NOT NULL,",
            "    action_timestamp TIMESTAMPTZ NOT NULL,",
            "    job_doc_id TEXT NOT NULL,",
            "    job_url TEXT NOT NULL,",
            "    job_company TEXT NOT NULL,",
            "    job_title TEXT NOT NULL,",
            "    application_status TEXT NOT NULL,",
            "    source_view TEXT NOT NULL,",
            "    note TEXT NOT NULL",
            ");",
            "",
            "CREATE INDEX IF NOT EXISTS idx_application_actions_action_key_timestamp",
            "ON application_actions (action_key, action_timestamp DESC);",
            "",
            "CREATE INDEX IF NOT EXISTS idx_application_actions_status_timestamp",
            "ON application_actions (application_status, action_timestamp DESC);",
            "",
            "CREATE INDEX IF NOT EXISTS idx_application_actions_company_title",
            "ON application_actions (job_company, job_title);",
        ]
    )


def application_actions_schema_sql_text(
    schema_path: Path = DEFAULT_APPLICATION_ACTIONS_SCHEMA_SQL_PATH,
) -> str:
    return _read_sql_artifact(schema_path, "application actions schema")


def application_actions_schema_sql_payload(
    schema_path: Path = DEFAULT_APPLICATION_ACTIONS_SCHEMA_SQL_PATH,
) -> Dict[str, Any]:
    sql = application_actions_schema_sql_text(schema_path)
    return {
        "path": str(Path(schema_path)),
        "sql": sql,
    }


def application_actions_schema_sql_generation_payload(
    schema_path: Path = DEFAULT_APPLICATION_ACTIONS_SCHEMA_SQL_PATH,
) -> Dict[str, Any]:
    generated_sql = render_application_actions_schema_sql()
    artifact_sql = application_actions_schema_sql_text(schema_path)

    return {
        "artifact_path": str(Path(schema_path)),
        "artifact_sql": artifact_sql,
        "generated_sql": generated_sql,
        "matches_artifact": generated_sql.strip() == artifact_sql.strip(),
    }


def application_actions_contract_health_payload() -> Dict[str, Any]:
    schema_generation = application_actions_schema_sql_generation_payload()

    return {
        "ok": True,
        "artifacts": {
            "schema_sql_path": str(DEFAULT_APPLICATION_ACTIONS_SCHEMA_SQL_PATH),
        },
        "checks": {
            "schema_sql_matches_artifact": bool(schema_generation["matches_artifact"]),
        },
        "all_checks_pass": bool(schema_generation["matches_artifact"]),
    }


def _build_insert_sql(row: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "INSERT INTO application_actions (",
            "    action_id,",
            "    action_key,",
            "    action_timestamp,",
            "    job_doc_id,",
            "    job_url,",
            "    job_company,",
            "    job_title,",
            "    application_status,",
            "    source_view,",
            "    note",
            ")",
            "VALUES (",
            f"    {_sql_quote_text(row['action_id'])},",
            f"    {_sql_quote_text(row['action_key'])},",
            f"    {_sql_quote_text(row['action_timestamp'])}::timestamptz,",
            f"    {_sql_quote_text(row['job_doc_id'])},",
            f"    {_sql_quote_text(row['job_url'])},",
            f"    {_sql_quote_text(row['job_company'])},",
            f"    {_sql_quote_text(row['job_title'])},",
            f"    {_sql_quote_text(row['application_status'])},",
            f"    {_sql_quote_text(row['source_view'])},",
            f"    {_sql_quote_text(row['note'])}",
            ")",
            "ON CONFLICT (action_id) DO NOTHING;",
        ]
    )


def insert_application_action_row_to_postgres(
    *,
    record: Dict[str, Any],
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    allow_contract_drift: bool = False,
) -> Dict[str, Any]:
    contract_health = application_actions_contract_health_payload()
    if not contract_health.get("all_checks_pass", False) and not allow_contract_drift:
        raise SystemExit(
            "Application-actions contract health check failed. Refusing Postgres insert while artifacts are drifting. "
            "Fix the schema artifact mismatch first, or pass --allow-contract-drift if you intentionally want to override."
        )

    row = application_action_db_row(record)
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
        "table_name": "application_actions",
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