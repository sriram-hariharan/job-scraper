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

DEFAULT_OPERATOR_DECISIONS_SCHEMA_SQL_PATH = Path("src/storage/operator_decisions_schema.sql")


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


def _normalize_operator_decision(value: Any) -> str:
    normalized = _clean_text(value).upper().replace(" ", "_")
    if not normalized:
        raise ValueError("decision is required.")

    allowed = {"SELECT_RESUME"}
    if normalized not in allowed:
        raise ValueError(
            f"Invalid decision={normalized!r}. Allowed values: {', '.join(sorted(allowed))}"
        )

    return normalized


def _operator_decision_key(record: Dict[str, Any]) -> str:
    job_doc_id = _clean_text(record.get("job_doc_id"))
    if job_doc_id:
        return f"job_doc_id::{job_doc_id}"

    queue_rank = _clean_text(record.get("queue_rank"))
    if queue_rank:
        return f"queue_rank::{queue_rank}"

    company = _normalize_text(record.get("job_company"))
    title = _normalize_text(record.get("job_title"))
    if company or title:
        return f"title::{company}||{title}"

    return ""


def _build_decision_id(normalized_row: Dict[str, Any]) -> str:
    signature_payload = {
        "decision_timestamp": normalized_row["decision_timestamp"],
        "decision_key": normalized_row["decision_key"],
        "queue_rank": normalized_row["queue_rank"],
        "job_doc_id": normalized_row["job_doc_id"],
        "job_company": normalized_row["job_company"],
        "job_title": normalized_row["job_title"],
        "planning_action": normalized_row["planning_action"],
        "winner_resume": normalized_row["winner_resume"],
        "winner_score": normalized_row["winner_score"],
        "runner_up_resume": normalized_row["runner_up_resume"],
        "runner_up_score": normalized_row["runner_up_score"],
        "selected_resume": normalized_row["selected_resume"],
        "decision": normalized_row["decision"],
        "note": normalized_row["note"],
    }
    blob = _json_compact(signature_payload)
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()


def operator_decision_db_row(record: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(record, dict):
        raise ValueError("Operator decision record must be a dictionary.")

    decision_timestamp = _clean_text(record.get("decision_timestamp"))
    if not decision_timestamp:
        raise ValueError("Operator decision record is missing required field: decision_timestamp")

    selected_resume = _clean_text(record.get("selected_resume"))
    if not selected_resume:
        raise ValueError("Operator decision record is missing required field: selected_resume")

    normalized_row = {
        "decision_timestamp": decision_timestamp,
        "queue_rank": _clean_text(record.get("queue_rank")),
        "job_doc_id": _clean_text(record.get("job_doc_id")),
        "job_company": _clean_text(record.get("job_company")),
        "job_title": _clean_text(record.get("job_title")),
        "planning_action": _clean_text(record.get("planning_action")),
        "winner_resume": _clean_text(record.get("winner_resume")),
        "winner_score": _clean_text(record.get("winner_score")),
        "runner_up_resume": _clean_text(record.get("runner_up_resume")),
        "runner_up_score": _clean_text(record.get("runner_up_score")),
        "selected_resume": selected_resume,
        "decision": _normalize_operator_decision(record.get("decision")),
        "note": _clean_text(record.get("note")),
    }

    decision_key = _operator_decision_key(normalized_row)
    if not decision_key:
        raise ValueError(
            "Operator decision requires job_doc_id, queue_rank, or job_company + job_title."
        )

    normalized_row["decision_key"] = decision_key
    normalized_row["decision_id"] = _build_decision_id(normalized_row)
    return normalized_row


def operator_decisions_table_specs() -> Dict[str, Any]:
    return {
        "operator_decisions": {
            "description": "Append-only operational history of selected resume decisions.",
            "primary_key": ["decision_id"],
            "columns": [
                {"name": "decision_id", "type": "text", "nullable": False},
                {"name": "decision_key", "type": "text", "nullable": False},
                {"name": "decision_timestamp", "type": "timestamptz", "nullable": False},
                {"name": "queue_rank", "type": "text", "nullable": False},
                {"name": "job_doc_id", "type": "text", "nullable": False},
                {"name": "job_company", "type": "text", "nullable": False},
                {"name": "job_title", "type": "text", "nullable": False},
                {"name": "planning_action", "type": "text", "nullable": False},
                {"name": "winner_resume", "type": "text", "nullable": False},
                {"name": "winner_score", "type": "text", "nullable": False},
                {"name": "runner_up_resume", "type": "text", "nullable": False},
                {"name": "runner_up_score", "type": "text", "nullable": False},
                {"name": "selected_resume", "type": "text", "nullable": False},
                {"name": "decision", "type": "text", "nullable": False},
                {"name": "note", "type": "text", "nullable": False},
            ],
            "indexes": [
                {"name": "idx_operator_decisions_key_timestamp", "columns": ["decision_key", "decision_timestamp"]},
                {"name": "idx_operator_decisions_queue_rank", "columns": ["queue_rank"]},
                {"name": "idx_operator_decisions_selected_resume", "columns": ["selected_resume"]},
            ],
        }
    }


def render_operator_decisions_schema_sql() -> str:
    return "\n".join(
        [
            "CREATE TABLE IF NOT EXISTS operator_decisions (",
            "    decision_id TEXT PRIMARY KEY,",
            "    decision_key TEXT NOT NULL,",
            "    decision_timestamp TIMESTAMPTZ NOT NULL,",
            "    queue_rank TEXT NOT NULL,",
            "    job_doc_id TEXT NOT NULL,",
            "    job_company TEXT NOT NULL,",
            "    job_title TEXT NOT NULL,",
            "    planning_action TEXT NOT NULL,",
            "    winner_resume TEXT NOT NULL,",
            "    winner_score TEXT NOT NULL,",
            "    runner_up_resume TEXT NOT NULL,",
            "    runner_up_score TEXT NOT NULL,",
            "    selected_resume TEXT NOT NULL,",
            "    decision TEXT NOT NULL,",
            "    note TEXT NOT NULL",
            ");",
            "",
            "CREATE INDEX IF NOT EXISTS idx_operator_decisions_key_timestamp",
            "ON operator_decisions (decision_key, decision_timestamp DESC);",
            "",
            "CREATE INDEX IF NOT EXISTS idx_operator_decisions_queue_rank",
            "ON operator_decisions (queue_rank);",
            "",
            "CREATE INDEX IF NOT EXISTS idx_operator_decisions_selected_resume",
            "ON operator_decisions (selected_resume);",
        ]
    )


def operator_decisions_schema_sql_text(
    schema_path: Path = DEFAULT_OPERATOR_DECISIONS_SCHEMA_SQL_PATH,
) -> str:
    return _read_sql_artifact(schema_path, "operator decisions schema")


def operator_decisions_schema_sql_payload(
    schema_path: Path = DEFAULT_OPERATOR_DECISIONS_SCHEMA_SQL_PATH,
) -> Dict[str, Any]:
    sql = operator_decisions_schema_sql_text(schema_path)
    return {
        "path": str(Path(schema_path)),
        "sql": sql,
    }


def operator_decisions_schema_sql_generation_payload(
    schema_path: Path = DEFAULT_OPERATOR_DECISIONS_SCHEMA_SQL_PATH,
) -> Dict[str, Any]:
    generated_sql = render_operator_decisions_schema_sql()
    artifact_sql = operator_decisions_schema_sql_text(schema_path)

    return {
        "artifact_path": str(Path(schema_path)),
        "artifact_sql": artifact_sql,
        "generated_sql": generated_sql,
        "matches_artifact": generated_sql.strip() == artifact_sql.strip(),
    }


def operator_decisions_contract_health_payload() -> Dict[str, Any]:
    schema_generation = operator_decisions_schema_sql_generation_payload()

    return {
        "ok": True,
        "artifacts": {
            "schema_sql_path": str(DEFAULT_OPERATOR_DECISIONS_SCHEMA_SQL_PATH),
        },
        "checks": {
            "schema_sql_matches_artifact": bool(schema_generation["matches_artifact"]),
        },
        "all_checks_pass": bool(schema_generation["matches_artifact"]),
    }


def _build_insert_sql(row: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "INSERT INTO operator_decisions (",
            "    decision_id,",
            "    decision_key,",
            "    decision_timestamp,",
            "    queue_rank,",
            "    job_doc_id,",
            "    job_company,",
            "    job_title,",
            "    planning_action,",
            "    winner_resume,",
            "    winner_score,",
            "    runner_up_resume,",
            "    runner_up_score,",
            "    selected_resume,",
            "    decision,",
            "    note",
            ")",
            "VALUES (",
            f"    {_sql_quote_text(row['decision_id'])},",
            f"    {_sql_quote_text(row['decision_key'])},",
            f"    {_sql_quote_text(row['decision_timestamp'])}::timestamptz,",
            f"    {_sql_quote_text(row['queue_rank'])},",
            f"    {_sql_quote_text(row['job_doc_id'])},",
            f"    {_sql_quote_text(row['job_company'])},",
            f"    {_sql_quote_text(row['job_title'])},",
            f"    {_sql_quote_text(row['planning_action'])},",
            f"    {_sql_quote_text(row['winner_resume'])},",
            f"    {_sql_quote_text(row['winner_score'])},",
            f"    {_sql_quote_text(row['runner_up_resume'])},",
            f"    {_sql_quote_text(row['runner_up_score'])},",
            f"    {_sql_quote_text(row['selected_resume'])},",
            f"    {_sql_quote_text(row['decision'])},",
            f"    {_sql_quote_text(row['note'])}",
            ")",
            "ON CONFLICT (decision_id) DO NOTHING;",
        ]
    )


def insert_operator_decision_row_to_postgres(
    *,
    record: Dict[str, Any],
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    allow_contract_drift: bool = False,
) -> Dict[str, Any]:
    contract_health = operator_decisions_contract_health_payload()
    if not contract_health.get("all_checks_pass", False) and not allow_contract_drift:
        raise SystemExit(
            "Operator-decisions contract health check failed. Refusing Postgres insert while artifacts are drifting. "
            "Fix the schema artifact mismatch first, or pass --allow-contract-drift if you intentionally want to override."
        )

    row = operator_decision_db_row(record)
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
        "table_name": "operator_decisions",
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