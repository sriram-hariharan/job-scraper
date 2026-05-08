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

DEFAULT_SAVED_SCANS_SCHEMA_SQL_PATH = Path("src/storage/saved_scans/schema.sql")


def _load_local_dotenv_if_present(dotenv_path: Path = Path(".env")) -> None:
    path = dotenv_path.expanduser()
    if not path.exists() or not path.is_file():
        return

    try:
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            if not key or key in os.environ:
                continue

            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                value = value[1:-1]

            os.environ[key] = value
    except Exception:
        return


_load_local_dotenv_if_present()


def _json_compact(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _sql_quote_text(value: Any) -> str:
    text = str(value or "")
    return "'" + text.replace("'", "''") + "'"


def _sql_quote_jsonb(value: Any) -> str:
    return f"{_sql_quote_text(_json_compact(value))}::jsonb"


def _sql_quote_numeric_or_null(value: Any) -> str:
    if value is None or value == "":
        return "NULL"
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return "NULL"
    if not (0 <= parsed <= 100):
        return "NULL"
    return str(round(parsed, 4))


def _read_sql_artifact(path: Path, label: str) -> str:
    resolved = Path(path)
    if not resolved.exists():
        raise ValueError(f"Missing {label} SQL file: {resolved}")

    sql = resolved.read_text(encoding="utf-8")
    if not sql.strip():
        raise ValueError(f"{label.capitalize()} SQL file is empty: {resolved}")
    return sql


def _resolve_database_url(explicit_value: str, env_var_name: str, *, allow_placeholder: bool) -> str:
    explicit = str(explicit_value or "").strip()
    if explicit:
        return explicit

    env_name = str(env_var_name or "").strip() or "DATABASE_URL"
    env_value = str(os.environ.get(env_name, "") or "").strip()
    if env_value:
        return env_value

    if allow_placeholder:
        return f"${env_name}"

    raise SystemExit(f"Database URL is required. Pass --database-url or set {env_name} in the environment.")


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


def _build_scan_id(row: Dict[str, Any]) -> str:
    signature_payload = {
        "scan_timestamp": row["scan_timestamp"],
        "resume_source": row["resume_source"],
        "resume_name": row["resume_name"],
        "resume_filename": row["resume_filename"],
        "job_company": row["job_company"],
        "job_title": row["job_title"],
        "job_description_text": row["job_description_text"],
    }
    return hashlib.sha1(_json_compact(signature_payload).encode("utf-8")).hexdigest()


def saved_scan_db_row(record: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(record, dict):
        raise ValueError("Saved scan record must be a dictionary.")

    scan_timestamp = _clean_text(record.get("scan_timestamp"))
    if not scan_timestamp:
        raise ValueError("Saved scan record is missing required field: scan_timestamp")

    job_description_text = _clean_text(record.get("job_description_text"))
    if not job_description_text:
        raise ValueError("Saved scan requires job_description_text.")

    resume_source = _clean_text(record.get("resume_source")) or "pasted_text"
    if resume_source not in {"saved_resume", "pasted_text", "uploaded_file"}:
        raise ValueError("resume_source must be saved_resume, pasted_text, or uploaded_file.")

    normalized = {
        "scan_timestamp": scan_timestamp,
        "scan_source": _clean_text(record.get("scan_source")) or "scan_workspace_new_scan",
        "scan_status": _clean_text(record.get("scan_status")) or "intake_saved",
        "resume_source": resume_source,
        "resume_name": _clean_text(record.get("resume_name")),
        "resume_filename": _clean_text(record.get("resume_filename")),
        "resume_file_path": _clean_text(record.get("resume_file_path")),
        "resume_file_mime_type": _clean_text(record.get("resume_file_mime_type")),
        "resume_size_bytes": int(record.get("resume_size_bytes", 0) or 0),
        "resume_text": _clean_text(record.get("resume_text")),
        "job_doc_id": _clean_text(record.get("job_doc_id")),
        "job_url": _clean_text(record.get("job_url")),
        "job_company": _clean_text(record.get("job_company")),
        "job_title": _clean_text(record.get("job_title")),
        "job_description_text": job_description_text,
        "match_rate": record.get("match_rate"),
        "tailoring_json_path": _clean_text(record.get("tailoring_json_path")),
        "note": _clean_text(record.get("note")),
        "payload_json": record.get("payload_json") if isinstance(record.get("payload_json"), dict) else {},
    }
    normalized["scan_id"] = _clean_text(record.get("scan_id")) or _build_scan_id(normalized)
    return normalized


def saved_scans_table_specs() -> Dict[str, Any]:
    return {
        "saved_scans": {
            "description": "Saved scan intake and history records from the scan workspace.",
            "primary_key": ["scan_id"],
            "columns": [
                {"name": "scan_id", "type": "text", "nullable": False},
                {"name": "scan_timestamp", "type": "timestamptz", "nullable": False},
                {"name": "scan_source", "type": "text", "nullable": False},
                {"name": "scan_status", "type": "text", "nullable": False},
                {"name": "resume_source", "type": "text", "nullable": False},
                {"name": "resume_name", "type": "text", "nullable": False},
                {"name": "resume_filename", "type": "text", "nullable": False},
                {"name": "resume_file_path", "type": "text", "nullable": False},
                {"name": "resume_file_mime_type", "type": "text", "nullable": False},
                {"name": "resume_size_bytes", "type": "bigint", "nullable": False},
                {"name": "resume_text", "type": "text", "nullable": False},
                {"name": "job_doc_id", "type": "text", "nullable": False},
                {"name": "job_url", "type": "text", "nullable": False},
                {"name": "job_company", "type": "text", "nullable": False},
                {"name": "job_title", "type": "text", "nullable": False},
                {"name": "job_description_text", "type": "text", "nullable": False},
                {"name": "match_rate", "type": "numeric", "nullable": True},
                {"name": "tailoring_json_path", "type": "text", "nullable": False},
                {"name": "note", "type": "text", "nullable": False},
                {"name": "payload_json", "type": "jsonb", "nullable": False},
            ],
            "indexes": [
                {"name": "idx_saved_scans_timestamp", "columns": ["scan_timestamp"]},
                {"name": "idx_saved_scans_company_title", "columns": ["job_company", "job_title"]},
                {"name": "idx_saved_scans_resume_name", "columns": ["resume_name"]},
            ],
        }
    }


def render_saved_scans_schema_sql() -> str:
    return "\n".join(
        [
            "CREATE TABLE IF NOT EXISTS saved_scans (",
            "    scan_id TEXT PRIMARY KEY,",
            "    scan_timestamp TIMESTAMPTZ NOT NULL,",
            "    scan_source TEXT NOT NULL,",
            "    scan_status TEXT NOT NULL,",
            "    resume_source TEXT NOT NULL,",
            "    resume_name TEXT NOT NULL,",
            "    resume_filename TEXT NOT NULL,",
            "    resume_file_path TEXT NOT NULL,",
            "    resume_file_mime_type TEXT NOT NULL,",
            "    resume_size_bytes BIGINT NOT NULL,",
            "    resume_text TEXT NOT NULL,",
            "    job_doc_id TEXT NOT NULL,",
            "    job_url TEXT NOT NULL,",
            "    job_company TEXT NOT NULL,",
            "    job_title TEXT NOT NULL,",
            "    job_description_text TEXT NOT NULL,",
            "    match_rate NUMERIC,",
            "    tailoring_json_path TEXT NOT NULL,",
            "    note TEXT NOT NULL,",
            "    payload_json JSONB NOT NULL",
            ");",
            "",
            "CREATE INDEX IF NOT EXISTS idx_saved_scans_timestamp",
            "ON saved_scans (scan_timestamp DESC);",
            "",
            "CREATE INDEX IF NOT EXISTS idx_saved_scans_company_title",
            "ON saved_scans (job_company, job_title);",
            "",
            "CREATE INDEX IF NOT EXISTS idx_saved_scans_resume_name",
            "ON saved_scans (resume_name);",
        ]
    )


def saved_scans_schema_sql_text(schema_path: Path = DEFAULT_SAVED_SCANS_SCHEMA_SQL_PATH) -> str:
    return _read_sql_artifact(schema_path, "saved scans schema")


def saved_scans_schema_sql_generation_payload(
    schema_path: Path = DEFAULT_SAVED_SCANS_SCHEMA_SQL_PATH,
) -> Dict[str, Any]:
    generated_sql = render_saved_scans_schema_sql()
    artifact_sql = saved_scans_schema_sql_text(schema_path)
    return {
        "artifact_path": str(Path(schema_path)),
        "artifact_sql": artifact_sql,
        "generated_sql": generated_sql,
        "matches_artifact": generated_sql.strip() == artifact_sql.strip(),
    }


def saved_scans_contract_health_payload() -> Dict[str, Any]:
    schema_generation = saved_scans_schema_sql_generation_payload()
    return {
        "ok": True,
        "artifacts": {"schema_sql_path": str(DEFAULT_SAVED_SCANS_SCHEMA_SQL_PATH)},
        "checks": {"schema_sql_matches_artifact": bool(schema_generation["matches_artifact"])},
        "all_checks_pass": bool(schema_generation["matches_artifact"]),
    }


def _build_insert_sql(row: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "INSERT INTO saved_scans (",
            "    scan_id, scan_timestamp, scan_source, scan_status, resume_source,",
            "    resume_name, resume_filename, resume_file_path, resume_file_mime_type,",
            "    resume_size_bytes, resume_text, job_doc_id, job_url, job_company,",
            "    job_title, job_description_text, match_rate, tailoring_json_path, note, payload_json",
            ")",
            "VALUES (",
            f"    {_sql_quote_text(row['scan_id'])}, {_sql_quote_text(row['scan_timestamp'])}::timestamptz, {_sql_quote_text(row['scan_source'])}, {_sql_quote_text(row['scan_status'])}, {_sql_quote_text(row['resume_source'])},",
            f"    {_sql_quote_text(row['resume_name'])}, {_sql_quote_text(row['resume_filename'])}, {_sql_quote_text(row['resume_file_path'])}, {_sql_quote_text(row['resume_file_mime_type'])},",
            f"    {int(row['resume_size_bytes'])}, {_sql_quote_text(row['resume_text'])}, {_sql_quote_text(row['job_doc_id'])}, {_sql_quote_text(row['job_url'])}, {_sql_quote_text(row['job_company'])},",
            f"    {_sql_quote_text(row['job_title'])}, {_sql_quote_text(row['job_description_text'])}, {_sql_quote_numeric_or_null(row['match_rate'])}, {_sql_quote_text(row['tailoring_json_path'])}, {_sql_quote_text(row['note'])}, {_sql_quote_jsonb(row['payload_json'])}",
            ")",
            "ON CONFLICT (scan_id) DO UPDATE SET",
            "    scan_status = EXCLUDED.scan_status,",
            "    match_rate = EXCLUDED.match_rate,",
            "    note = EXCLUDED.note,",
            "    payload_json = EXCLUDED.payload_json;",
        ]
    )


def insert_saved_scan_row_to_postgres(
    *,
    record: Dict[str, Any],
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    allow_contract_drift: bool = False,
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    contract_health = saved_scans_contract_health_payload()
    if not contract_health.get("all_checks_pass", False) and not allow_contract_drift:
        raise SystemExit("Saved-scans contract health check failed. Fix schema drift before inserting.")

    row = saved_scan_db_row(record)
    sql = (saved_scans_schema_sql_text() + "\n\n" if ensure_schema else "") + _build_insert_sql(row)
    database_url_value = _resolve_database_url(database_url, database_url_env, allow_placeholder=bool(print_only))

    cmd: List[str] = [str(psql_bin), database_url_value, "-X", "-v", "ON_ERROR_STOP=1", "-c", sql]
    redacted_cmd = list(cmd)
    redacted_cmd[1] = _redact_database_url(redacted_cmd[1])

    payload: Dict[str, Any] = {
        "ok": True,
        "contract_health_ok": bool(contract_health["all_checks_pass"]),
        "row": row,
        "command": redacted_cmd,
        "command_text": shlex.join(redacted_cmd),
        "table_name": "saved_scans",
    }
    if print_only:
        return payload
    if shutil.which(str(psql_bin)) is None:
        raise SystemExit(f"psql executable not found on PATH: {psql_bin!r}.")

    subprocess.run(cmd, check=True)
    return payload
