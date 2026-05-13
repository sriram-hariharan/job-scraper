from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlsplit, urlunsplit

from src.storage.saved_scans.store import saved_scans_schema_sql_text


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


def _normalize_positive_int(value: Any, field_name: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be an integer.") from exc
    if parsed <= 0:
        raise ValueError(f"{field_name} must be > 0.")
    return parsed


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


def _build_saved_scans_sql(limit: int, owner_user_id: str = "") -> str:
    owner_where = _owner_visibility_clause(owner_user_id, prefix="WHERE")
    return f"""
WITH recent_rows AS (
    SELECT
        scan_id,
        owner_user_id,
        owner_email,
        scan_timestamp,
        scan_source,
        scan_status,
        resume_source,
        resume_name,
        resume_filename,
        resume_file_path,
        resume_file_mime_type,
        resume_size_bytes,
        job_doc_id,
        job_url,
        job_company,
        job_title,
        match_rate,
        tailoring_json_path,
        note,
        LEFT(job_description_text, 240) AS job_description_preview,
        LEFT(resume_text, 160) AS resume_text_preview,
        payload_json
    FROM saved_scans
    {owner_where}
    ORDER BY scan_timestamp DESC, scan_id DESC
    LIMIT {limit}
)
SELECT json_build_object(
    'total_row_count', (SELECT COUNT(*) FROM saved_scans {owner_where}),
    'recent_rows',
        COALESCE(
            (SELECT json_agg(row_to_json(recent_rows) ORDER BY recent_rows.scan_timestamp DESC, recent_rows.scan_id DESC) FROM recent_rows),
            '[]'::json
        )
);
""".strip()


def _run_psql_json_query(
    *,
    sql: str,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
) -> Dict[str, Any]:
    database_url_value = _resolve_database_url(database_url, database_url_env, allow_placeholder=bool(print_only))
    cmd: List[str] = [str(psql_bin), database_url_value, "-X", "-v", "ON_ERROR_STOP=1", "-t", "-A", "-c", sql]
    redacted_cmd = list(cmd)
    redacted_cmd[1] = _redact_database_url(redacted_cmd[1])
    payload: Dict[str, Any] = {"command": redacted_cmd, "command_text": shlex.join(redacted_cmd), "data": {}}
    if print_only:
        return payload
    if shutil.which(str(psql_bin)) is None:
        raise SystemExit(f"psql executable not found on PATH: {psql_bin!r}.")
    completed = subprocess.run(cmd, check=True, capture_output=True, text=True)
    stdout = (completed.stdout or "").strip()
    if not stdout:
        raise SystemExit("psql returned empty output for saved-scans query.")
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Failed to parse saved-scans query JSON from psql output: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit("Saved-scans query did not return a JSON object.")
    payload["data"] = data
    return payload


def _run_psql_command(
    *,
    sql: str,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
) -> Dict[str, Any]:
    database_url_value = _resolve_database_url(database_url, database_url_env, allow_placeholder=bool(print_only))
    cmd: List[str] = [str(psql_bin), database_url_value, "-X", "-q", "-v", "ON_ERROR_STOP=1", "-c", sql]
    redacted_cmd = list(cmd)
    redacted_cmd[1] = _redact_database_url(redacted_cmd[1])
    payload: Dict[str, Any] = {"command": redacted_cmd, "command_text": shlex.join(redacted_cmd)}
    if print_only:
        return payload
    if shutil.which(str(psql_bin)) is None:
        raise SystemExit(f"psql executable not found on PATH: {psql_bin!r}.")
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    return payload


def _sql_quote_text(value: Any) -> str:
    return "'" + str(value or "").replace("'", "''") + "'"

def _owner_visibility_clause(owner_user_id: str, *, prefix: str = "WHERE") -> str:
    safe_owner_user_id = str(owner_user_id or "").strip()
    if not safe_owner_user_id:
        return ""

    return (
        f"{prefix} "
        f"owner_user_id = {_sql_quote_text(safe_owner_user_id)}"
    )

def _build_saved_scan_by_id_sql(scan_id: str, owner_user_id: str = "") -> str:
    owner_and = _owner_visibility_clause(owner_user_id, prefix="AND")
    return f"""
SELECT COALESCE(
    (
        SELECT row_to_json(row_data)
        FROM (
            SELECT
                scan_id,
                owner_user_id,
                owner_email,
                scan_timestamp,
                scan_source,
                scan_status,
                resume_source,
                resume_name,
                resume_filename,
                resume_file_path,
                resume_file_mime_type,
                resume_size_bytes,
                job_doc_id,
                job_url,
                job_company,
                job_title,
                match_rate,
                tailoring_json_path,
                note,
                job_description_text,
                resume_text,
                payload_json
            FROM saved_scans
            WHERE scan_id = {_sql_quote_text(scan_id)}
            {owner_and}
            LIMIT 1
        ) row_data
    ),
    '{{}}'::json
);
""".strip()


def get_saved_scan_postgres_payload(
    *,
    scan_id: str,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    ensure_schema: bool = True,
    owner_user_id: str = "",    
) -> Dict[str, Any]:
    safe_scan_id = str(scan_id or "").strip()
    if not safe_scan_id:
        raise ValueError("scan_id is required.")

    schema_payload: Dict[str, Any] = {}
    if ensure_schema:
        schema_payload = _run_psql_command(
            sql=saved_scans_schema_sql_text(),
            database_url=database_url,
            database_url_env=database_url_env,
            psql_bin=psql_bin,
            print_only=print_only,
        )

    query_payload = _run_psql_json_query(
        sql=_build_saved_scan_by_id_sql(safe_scan_id, owner_user_id=owner_user_id),
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        print_only=print_only,
    )
    row = dict(query_payload.get("data", {}) or {})
    return {
        "ok": bool(row),
        "scan": row,
        "schema_command": schema_payload.get("command", []),
        "schema_command_text": schema_payload.get("command_text", ""),
        "command": query_payload["command"],
        "command_text": query_payload["command_text"],
    }


def delete_saved_scan_postgres_payload(
    *,
    scan_id: str,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    ensure_schema: bool = True,
    owner_user_id: str = "",
) -> Dict[str, Any]:
    safe_scan_id = str(scan_id or "").strip()
    if not safe_scan_id:
        raise ValueError("scan_id is required.")

    owner_and = _owner_visibility_clause(owner_user_id, prefix="AND")
    sql = f"""
DELETE FROM saved_scans
WHERE scan_id = {_sql_quote_text(safe_scan_id)}
{owner_and};
""".strip()
    schema_sql = saved_scans_schema_sql_text() + "\n\n" if ensure_schema else ""
    payload = _run_psql_command(
        sql=schema_sql + sql,
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        print_only=print_only,
    )
    return {
        "ok": True,
        "scan_id": safe_scan_id,
        "command": payload.get("command", []),
        "command_text": payload.get("command_text", ""),
    }


def save_saved_scan_draft_postgres_payload(
    *,
    scan_id: str,
    draft: Dict[str, Any],
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    ensure_schema: bool = True,
    owner_user_id: str = "",
) -> Dict[str, Any]:
    safe_scan_id = str(scan_id or "").strip()
    if not safe_scan_id:
        raise ValueError("scan_id is required.")
    safe_draft = draft if isinstance(draft, dict) else {}
    draft_json = json.dumps(safe_draft, sort_keys=True).replace("'", "''")
    owner_and = _owner_visibility_clause(owner_user_id, prefix="AND")
    sql = f"""
UPDATE saved_scans
SET payload_json = jsonb_set(
        jsonb_set(
            payload_json,
            '{{scan_review_payload,draft}}',
            '{draft_json}'::jsonb,
            true
        ),
        '{{scan_review_payload,personal_details,saved}}',
        '{json.dumps(safe_draft.get("personal_details", {}), sort_keys=True).replace("'", "''")}'::jsonb,
        true
    ),
    note = 'Saved scan state updated from AI Optimize scan.'
WHERE scan_id = {_sql_quote_text(safe_scan_id)}
{owner_and};
""".strip()
    schema_sql = saved_scans_schema_sql_text() + "\n\n" if ensure_schema else ""
    payload = _run_psql_command(
        sql=schema_sql + sql,
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        print_only=print_only,
    )
    return {
        "ok": True,
        "scan_id": safe_scan_id,
        "draft": safe_draft,
        "command": payload.get("command", []),
        "command_text": payload.get("command_text", ""),
    }


def get_saved_scans_postgres_payload(
    *,
    limit: int = 25,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    ensure_schema: bool = True,
    owner_user_id: str = "",
) -> Dict[str, Any]:
    normalized_limit = _normalize_positive_int(limit, "limit")
    schema_payload: Dict[str, Any] = {}
    if ensure_schema:
        schema_payload = _run_psql_command(
            sql=saved_scans_schema_sql_text(),
            database_url=database_url,
            database_url_env=database_url_env,
            psql_bin=psql_bin,
            print_only=print_only,
        )

    query_payload = _run_psql_json_query(
        sql=_build_saved_scans_sql(normalized_limit, owner_user_id=owner_user_id),
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        print_only=print_only,
    )
    rows = list(query_payload["data"].get("recent_rows", []) or [])
    return {
        "ok": True,
        "query_limit": normalized_limit,
        "schema_command": schema_payload.get("command", []),
        "schema_command_text": schema_payload.get("command_text", ""),
        "command": query_payload["command"],
        "command_text": query_payload["command_text"],
        "postgres": query_payload["data"],
        "rows": rows,
        "count": len(rows),
    }
