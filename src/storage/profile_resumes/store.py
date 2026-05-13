from __future__ import annotations

import base64
import hashlib
import json
import os
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlsplit, urlunsplit

DEFAULT_PROFILE_RESUMES_SCHEMA_SQL_PATH = Path("src/storage/profile_resumes/schema.sql")


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


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _sql_quote_text(value: Any) -> str:
    return "'" + str(value or "").replace("'", "''") + "'"


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


def profile_resumes_schema_sql_text(
    schema_path: Path = DEFAULT_PROFILE_RESUMES_SCHEMA_SQL_PATH,
) -> str:
    return _read_sql_artifact(schema_path, "profile resumes schema")


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
        raise SystemExit("psql returned empty output for profile-resumes query.")
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Failed to parse profile-resumes query JSON from psql output: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit("Profile-resumes query did not return a JSON object.")
    payload["data"] = data
    return payload


def _run_psql_stdin_command(
    *,
    sql: str,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
) -> Dict[str, Any]:
    database_url_value = _resolve_database_url(database_url, database_url_env, allow_placeholder=bool(print_only))
    cmd: List[str] = [str(psql_bin), database_url_value, "-X", "-q", "-v", "ON_ERROR_STOP=1"]
    redacted_cmd = list(cmd)
    redacted_cmd[1] = _redact_database_url(redacted_cmd[1])
    payload: Dict[str, Any] = {"command": redacted_cmd, "command_text": shlex.join(redacted_cmd)}
    if print_only:
        payload["sql"] = sql
        return payload
    if shutil.which(str(psql_bin)) is None:
        raise SystemExit(f"psql executable not found on PATH: {psql_bin!r}.")
    subprocess.run(cmd, check=True, input=sql, capture_output=True, text=True)
    return payload


def _run_psql_json_stdin_query(
    *,
    sql: str,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
) -> Dict[str, Any]:
    database_url_value = _resolve_database_url(database_url, database_url_env, allow_placeholder=bool(print_only))
    cmd: List[str] = [str(psql_bin), database_url_value, "-X", "-q", "-v", "ON_ERROR_STOP=1", "-t", "-A"]
    redacted_cmd = list(cmd)
    redacted_cmd[1] = _redact_database_url(redacted_cmd[1])
    payload: Dict[str, Any] = {"command": redacted_cmd, "command_text": shlex.join(redacted_cmd), "data": {}}
    if print_only:
        payload["sql"] = sql
        return payload
    if shutil.which(str(psql_bin)) is None:
        raise SystemExit(f"psql executable not found on PATH: {psql_bin!r}.")
    completed = subprocess.run(cmd, check=True, input=sql, capture_output=True, text=True)
    stdout = (completed.stdout or "").strip()
    if not stdout:
        raise SystemExit("psql returned empty output for profile-resumes query.")
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Failed to parse profile-resumes query JSON from psql output: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit("Profile-resumes query did not return a JSON object.")
    payload["data"] = data
    return payload


def _metadata_select_sql() -> str:
    return """
SELECT
    resume_name,
    original_filename,
    content_type,
    size_bytes,
    sha256,
    created_at,
    updated_at
""".strip()


def _row_to_resume_payload(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "resume_name": _clean_text(row.get("resume_name")),
        "path": "",
        "size_bytes": int(row.get("size_bytes", 0) or 0),
        "modified_at": _clean_text(row.get("updated_at")) or _clean_text(row.get("created_at")),
        "created_at": _clean_text(row.get("created_at")),
        "updated_at": _clean_text(row.get("updated_at")),
        "content_type": _clean_text(row.get("content_type")) or "application/pdf",
        "sha256": _clean_text(row.get("sha256")),
        "storage": "postgres",
    }


def upsert_profile_resume_postgres_payload(
    *,
    owner_user_id: str,
    resume_name: str,
    original_filename: str,
    content_type: str,
    file_bytes: bytes,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    safe_owner = _clean_text(owner_user_id)
    safe_resume_name = _clean_text(resume_name)
    if not safe_owner:
        raise ValueError("owner_user_id is required.")
    if not safe_resume_name:
        raise ValueError("resume_name is required.")
    if not file_bytes:
        raise ValueError("Uploaded file is empty.")

    encoded_bytes = base64.b64encode(file_bytes).decode("ascii")
    sha256 = hashlib.sha256(file_bytes).hexdigest()
    schema_sql = profile_resumes_schema_sql_text() + "\n\n" if ensure_schema else ""
    sql = schema_sql + f"""
WITH inserted AS (
    INSERT INTO profile_resumes (
        owner_user_id,
        resume_name,
        original_filename,
        content_type,
        size_bytes,
        sha256,
        file_bytes
    )
    VALUES (
        {_sql_quote_text(safe_owner)},
        {_sql_quote_text(safe_resume_name)},
        {_sql_quote_text(original_filename)},
        {_sql_quote_text(content_type or "application/pdf")},
        {len(file_bytes)},
        {_sql_quote_text(sha256)},
        decode({_sql_quote_text(encoded_bytes)}, 'base64')
    )
    ON CONFLICT (owner_user_id, resume_name) DO NOTHING
    RETURNING resume_name, original_filename, content_type, size_bytes, sha256, created_at, updated_at
)
SELECT json_build_object(
    'inserted', EXISTS (SELECT 1 FROM inserted),
    'resume', COALESCE((SELECT row_to_json(inserted) FROM inserted LIMIT 1), '{{}}'::json)
);
""".strip()

    payload = _run_psql_json_stdin_query(
        sql=sql,
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        print_only=print_only,
    )
    resume = _row_to_resume_payload(dict(payload.get("data", {}).get("resume", {}) or {}))
    return {
        "ok": bool(payload.get("data", {}).get("inserted", False)),
        "inserted": bool(payload.get("data", {}).get("inserted", False)),
        "resume": resume,
        "command": payload.get("command", []),
        "command_text": payload.get("command_text", ""),
        "table_name": "profile_resumes",
    }


def get_profile_resumes_postgres_payload(
    *,
    owner_user_id: str,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    safe_owner = _clean_text(owner_user_id)
    if not safe_owner:
        raise ValueError("owner_user_id is required.")

    schema_sql = profile_resumes_schema_sql_text() + "\n\n" if ensure_schema else ""
    sql = schema_sql + f"""
WITH resume_rows AS (
    {_metadata_select_sql()}
    FROM profile_resumes
    WHERE owner_user_id = {_sql_quote_text(safe_owner)}
    ORDER BY updated_at DESC, resume_name ASC
)
SELECT json_build_object(
    'total_row_count', (SELECT COUNT(*) FROM profile_resumes WHERE owner_user_id = {_sql_quote_text(safe_owner)}),
    'rows', COALESCE((SELECT json_agg(row_to_json(resume_rows)) FROM resume_rows), '[]'::json)
);
""".strip()
    payload = _run_psql_json_stdin_query(
        sql=sql,
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        print_only=print_only,
    )
    rows = [_row_to_resume_payload(dict(row or {})) for row in list(payload.get("data", {}).get("rows", []) or [])]
    return {
        "ok": True,
        "resumes": rows,
        "rows": rows,
        "count": len(rows),
        "postgres": payload.get("data", {}),
        "command": payload.get("command", []),
        "command_text": payload.get("command_text", ""),
    }


def get_profile_resume_blob_postgres_payload(
    *,
    owner_user_id: str,
    resume_name: str,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    safe_owner = _clean_text(owner_user_id)
    safe_resume_name = _clean_text(resume_name)
    if not safe_owner:
        raise ValueError("owner_user_id is required.")
    if not safe_resume_name:
        raise ValueError("resume_name is required.")

    schema_sql = profile_resumes_schema_sql_text() + "\n\n" if ensure_schema else ""
    sql = schema_sql + f"""
SELECT COALESCE(
    (
        SELECT json_build_object(
            'resume_name', resume_name,
            'original_filename', original_filename,
            'content_type', content_type,
            'size_bytes', size_bytes,
            'sha256', sha256,
            'created_at', created_at,
            'updated_at', updated_at,
            'file_base64', encode(file_bytes, 'base64')
        )
        FROM profile_resumes
        WHERE owner_user_id = {_sql_quote_text(safe_owner)}
          AND resume_name = {_sql_quote_text(safe_resume_name)}
        LIMIT 1
    ),
    '{{}}'::json
);
""".strip()
    payload = _run_psql_json_stdin_query(
        sql=sql,
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        print_only=print_only,
    )
    data = dict(payload.get("data", {}) or {})
    file_base64 = _clean_text(data.pop("file_base64", ""))
    file_bytes = base64.b64decode(file_base64) if file_base64 else b""
    return {
        "ok": bool(data and file_bytes),
        "resume": _row_to_resume_payload(data),
        "file_bytes": file_bytes,
        "command": payload.get("command", []),
        "command_text": payload.get("command_text", ""),
    }


def delete_profile_resume_postgres_payload(
    *,
    owner_user_id: str,
    resume_name: str,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    safe_owner = _clean_text(owner_user_id)
    safe_resume_name = _clean_text(resume_name)
    if not safe_owner:
        raise ValueError("owner_user_id is required.")
    if not safe_resume_name:
        raise ValueError("resume_name is required.")

    schema_sql = profile_resumes_schema_sql_text() + "\n\n" if ensure_schema else ""
    sql = schema_sql + f"""
WITH deleted AS (
    DELETE FROM profile_resumes
    WHERE owner_user_id = {_sql_quote_text(safe_owner)}
      AND resume_name = {_sql_quote_text(safe_resume_name)}
    RETURNING resume_name
)
SELECT json_build_object(
    'deleted', EXISTS (SELECT 1 FROM deleted),
    'resume_name', COALESCE((SELECT resume_name FROM deleted LIMIT 1), '')
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
        "ok": bool(payload.get("data", {}).get("deleted", False)),
        "deleted": bool(payload.get("data", {}).get("deleted", False)),
        "resume_name": _clean_text(payload.get("data", {}).get("resume_name")) or safe_resume_name,
        "command": payload.get("command", []),
        "command_text": payload.get("command_text", ""),
    }
