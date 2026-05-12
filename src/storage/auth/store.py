from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlsplit, urlunsplit

DEFAULT_AUTH_SCHEMA_SQL_PATH = Path("src/storage/auth/schema.sql")

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


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
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _normalize_email(value: Any) -> str:
    return _clean_text(value).lower()


def _validate_email(value: Any) -> str:
    email = _clean_text(value)
    normalized_email = _normalize_email(email)

    if not normalized_email:
        raise ValueError("email is required.")

    if not _EMAIL_PATTERN.match(normalized_email):
        raise ValueError("email must be a valid email address.")

    return email


def _default_display_name(email: str) -> str:
    local_part = _clean_text(email).split("@", 1)[0].replace(".", " ").replace("_", " ")
    display_name = " ".join(part.capitalize() for part in local_part.split() if part)
    return display_name or "User"


def _sql_quote_text(value: Any) -> str:
    text = str(value or "")
    return "'" + text.replace("'", "''") + "'"


def _sql_bool_literal(value: Any) -> str:
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"

    raw = str(value or "").strip().lower()
    if raw in {"true", "1", "yes", "y"}:
        return "TRUE"
    if raw in {"false", "0", "no", "n"}:
        return "FALSE"

    raise ValueError(f"Cannot coerce boolean SQL literal from value={value!r}")


def _sql_timestamptz_or_null(value: Any) -> str:
    text = _clean_text(value)
    if not text:
        return "NULL"
    return f"{_sql_quote_text(text)}::timestamptz"


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


def _run_psql_json_query(
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
        "-v",
        "ON_ERROR_STOP=1",
        "-t",
        "-A",
        "-c",
        sql,
    ]

    redacted_cmd = list(cmd)
    redacted_cmd[1] = _redact_database_url(redacted_cmd[1])

    payload: Dict[str, Any] = {
        "command": redacted_cmd,
        "command_text": shlex.join(redacted_cmd),
        "data": {},
    }

    if print_only:
        return payload

    if shutil.which(str(psql_bin)) is None:
        raise SystemExit(
            f"psql executable not found on PATH: {psql_bin!r}. "
            "Install psql or pass --psql-bin with the correct executable path."
        )

    completed = subprocess.run(
        cmd,
        check=True,
        capture_output=True,
        text=True,
    )

    stdout = (completed.stdout or "").strip()
    if not stdout:
        raise SystemExit("psql returned empty output for auth storage query.")

    json_line = ""
    for line in reversed(stdout.splitlines()):
        candidate = line.strip()
        if candidate.startswith("{") and candidate.endswith("}"):
            json_line = candidate
            break

    if not json_line:
        raise SystemExit(
            "Failed to locate JSON object in auth storage psql output. "
            f"Raw stdout: {stdout[:1000]}"
        )

    try:
        data = json.loads(json_line)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Failed to parse auth storage JSON from psql output: {exc}") from exc

    if not isinstance(data, dict):
        raise SystemExit("Auth storage query did not return a JSON object.")

    payload["data"] = data
    return payload


def auth_user_db_row(record: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(record, dict):
        raise ValueError("Auth user record must be a dictionary.")

    email = _validate_email(record.get("email"))
    normalized_email = _normalize_email(email)

    password_hash = _clean_text(record.get("password_hash"))
    if not password_hash:
        raise ValueError("password_hash is required.")

    created_at = _clean_text(record.get("created_at")) or _utc_now_iso()
    updated_at = _clean_text(record.get("updated_at")) or created_at
    display_name = _clean_text(record.get("display_name")) or _default_display_name(email)

    return {
        "user_id": _clean_text(record.get("user_id")) or uuid.uuid4().hex,
        "email": email,
        "normalized_email": normalized_email,
        "password_hash": password_hash,
        "display_name": display_name,
        "is_active": bool(record.get("is_active", True)),
        "is_admin": bool(record.get("is_admin", False)),
        "created_at": created_at,
        "updated_at": updated_at,
        "last_login_at": _clean_text(record.get("last_login_at")),
    }


def auth_session_db_row(record: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(record, dict):
        raise ValueError("Auth session record must be a dictionary.")

    user_id = _clean_text(record.get("user_id"))
    if not user_id:
        raise ValueError("user_id is required.")

    session_token_hash = _clean_text(record.get("session_token_hash"))
    if not session_token_hash:
        raise ValueError("session_token_hash is required.")

    expires_at = _clean_text(record.get("expires_at"))
    if not expires_at:
        raise ValueError("expires_at is required.")

    created_at = _clean_text(record.get("created_at")) or _utc_now_iso()
    last_seen_at = _clean_text(record.get("last_seen_at")) or created_at

    return {
        "session_id": _clean_text(record.get("session_id")) or uuid.uuid4().hex,
        "user_id": user_id,
        "session_token_hash": session_token_hash,
        "created_at": created_at,
        "expires_at": expires_at,
        "last_seen_at": last_seen_at,
        "revoked_at": _clean_text(record.get("revoked_at")),
        "user_agent": _clean_text(record.get("user_agent")),
        "ip_address": _clean_text(record.get("ip_address")),
    }


def auth_table_specs() -> Dict[str, Any]:
    return {
        "auth_users": {
            "description": "Registered dashboard users with password hashes.",
            "primary_key": ["user_id"],
            "columns": [
                {"name": "user_id", "type": "text", "nullable": False},
                {"name": "email", "type": "text", "nullable": False},
                {"name": "normalized_email", "type": "text", "nullable": False},
                {"name": "password_hash", "type": "text", "nullable": False},
                {"name": "display_name", "type": "text", "nullable": False},
                {"name": "is_active", "type": "boolean", "nullable": False},
                {"name": "is_admin", "type": "boolean", "nullable": False},
                {"name": "created_at", "type": "timestamptz", "nullable": False},
                {"name": "updated_at", "type": "timestamptz", "nullable": False},
                {"name": "last_login_at", "type": "timestamptz", "nullable": True},
            ],
            "indexes": [
                {"name": "idx_auth_users_active", "columns": ["is_active"]},
                {"name": "idx_auth_users_created_at", "columns": ["created_at"]},
            ],
        },
        "auth_sessions": {
            "description": "Hashed session-token records for signed dashboard sessions.",
            "primary_key": ["session_id"],
            "columns": [
                {"name": "session_id", "type": "text", "nullable": False},
                {"name": "user_id", "type": "text", "nullable": False},
                {"name": "session_token_hash", "type": "text", "nullable": False},
                {"name": "created_at", "type": "timestamptz", "nullable": False},
                {"name": "expires_at", "type": "timestamptz", "nullable": False},
                {"name": "last_seen_at", "type": "timestamptz", "nullable": False},
                {"name": "revoked_at", "type": "timestamptz", "nullable": True},
                {"name": "user_agent", "type": "text", "nullable": False},
                {"name": "ip_address", "type": "text", "nullable": False},
            ],
            "indexes": [
                {"name": "idx_auth_sessions_user_id", "columns": ["user_id"]},
                {"name": "idx_auth_sessions_token_hash", "columns": ["session_token_hash"]},
                {"name": "idx_auth_sessions_expires_at", "columns": ["expires_at"]},
            ],
            "foreign_keys": [
                {
                    "column": "user_id",
                    "references": "auth_users.user_id",
                }
            ],
        },
    }


def render_auth_schema_sql() -> str:
    return "\n".join(
        [
            "CREATE TABLE IF NOT EXISTS auth_users (",
            "    user_id TEXT PRIMARY KEY,",
            "    email TEXT NOT NULL,",
            "    normalized_email TEXT NOT NULL UNIQUE,",
            "    password_hash TEXT NOT NULL,",
            "    display_name TEXT NOT NULL,",
            "    is_active BOOLEAN NOT NULL DEFAULT TRUE,",
            "    is_admin BOOLEAN NOT NULL DEFAULT FALSE,",
            "    created_at TIMESTAMPTZ NOT NULL,",
            "    updated_at TIMESTAMPTZ NOT NULL,",
            "    last_login_at TIMESTAMPTZ",
            ");",
            "",
            "CREATE INDEX IF NOT EXISTS idx_auth_users_active",
            "ON auth_users (is_active);",
            "",
            "CREATE INDEX IF NOT EXISTS idx_auth_users_created_at",
            "ON auth_users (created_at DESC);",
            "",
            "CREATE TABLE IF NOT EXISTS auth_sessions (",
            "    session_id TEXT PRIMARY KEY,",
            "    user_id TEXT NOT NULL REFERENCES auth_users(user_id) ON DELETE CASCADE,",
            "    session_token_hash TEXT NOT NULL UNIQUE,",
            "    created_at TIMESTAMPTZ NOT NULL,",
            "    expires_at TIMESTAMPTZ NOT NULL,",
            "    last_seen_at TIMESTAMPTZ NOT NULL,",
            "    revoked_at TIMESTAMPTZ,",
            "    user_agent TEXT NOT NULL,",
            "    ip_address TEXT NOT NULL",
            ");",
            "",
            "CREATE INDEX IF NOT EXISTS idx_auth_sessions_user_id",
            "ON auth_sessions (user_id);",
            "",
            "CREATE INDEX IF NOT EXISTS idx_auth_sessions_token_hash",
            "ON auth_sessions (session_token_hash);",
            "",
            "CREATE INDEX IF NOT EXISTS idx_auth_sessions_expires_at",
            "ON auth_sessions (expires_at);",
        ]
    )


def auth_schema_sql_text(
    schema_path: Path = DEFAULT_AUTH_SCHEMA_SQL_PATH,
) -> str:
    return _read_sql_artifact(schema_path, "auth schema")


def auth_schema_sql_payload(
    schema_path: Path = DEFAULT_AUTH_SCHEMA_SQL_PATH,
) -> Dict[str, Any]:
    sql = auth_schema_sql_text(schema_path)
    return {
        "path": str(Path(schema_path)),
        "sql": sql,
    }


def auth_schema_sql_generation_payload(
    schema_path: Path = DEFAULT_AUTH_SCHEMA_SQL_PATH,
) -> Dict[str, Any]:
    generated_sql = render_auth_schema_sql()
    artifact_sql = auth_schema_sql_text(schema_path)

    return {
        "artifact_path": str(Path(schema_path)),
        "artifact_sql": artifact_sql,
        "generated_sql": generated_sql,
        "matches_artifact": generated_sql.strip() == artifact_sql.strip(),
    }


def auth_contract_health_payload() -> Dict[str, Any]:
    schema_generation = auth_schema_sql_generation_payload()

    return {
        "ok": True,
        "artifacts": {
            "schema_sql_path": str(DEFAULT_AUTH_SCHEMA_SQL_PATH),
        },
        "checks": {
            "schema_sql_matches_artifact": bool(schema_generation["matches_artifact"]),
        },
        "all_checks_pass": bool(schema_generation["matches_artifact"]),
    }


def _build_create_user_sql(row: Dict[str, Any], *, ensure_schema: bool) -> str:
    schema_sql = auth_schema_sql_text() + "\n\n" if ensure_schema else ""

    return schema_sql + "\n".join(
        [
            "WITH attempted_insert AS (",
            "    INSERT INTO auth_users (",
            "        user_id,",
            "        email,",
            "        normalized_email,",
            "        password_hash,",
            "        display_name,",
            "        is_active,",
            "        is_admin,",
            "        created_at,",
            "        updated_at,",
            "        last_login_at",
            "    )",
            "    VALUES (",
            f"        {_sql_quote_text(row['user_id'])},",
            f"        {_sql_quote_text(row['email'])},",
            f"        {_sql_quote_text(row['normalized_email'])},",
            f"        {_sql_quote_text(row['password_hash'])},",
            f"        {_sql_quote_text(row['display_name'])},",
            f"        {_sql_bool_literal(row['is_active'])},",
            f"        {_sql_bool_literal(row['is_admin'])},",
            f"        {_sql_quote_text(row['created_at'])}::timestamptz,",
            f"        {_sql_quote_text(row['updated_at'])}::timestamptz,",
            f"        {_sql_timestamptz_or_null(row.get('last_login_at'))}",
            "    )",
            "    ON CONFLICT (normalized_email) DO NOTHING",
            "    RETURNING",
            "        user_id,",
            "        email,",
            "        normalized_email,",
            "        display_name,",
            "        is_active,",
            "        is_admin,",
            "        created_at,",
            "        updated_at,",
            "        last_login_at",
            "),",
            "resolved_user AS (",
            "    SELECT",
            "        user_id,",
            "        email,",
            "        normalized_email,",
            "        display_name,",
            "        is_active,",
            "        is_admin,",
            "        created_at,",
            "        updated_at,",
            "        last_login_at",
            "    FROM attempted_insert",
            "    UNION ALL",
            "    SELECT",
            "        user_id,",
            "        email,",
            "        normalized_email,",
            "        display_name,",
            "        is_active,",
            "        is_admin,",
            "        created_at,",
            "        updated_at,",
            "        last_login_at",
            "    FROM auth_users",
            f"    WHERE normalized_email = {_sql_quote_text(row['normalized_email'])}",
            "    LIMIT 1",
            ")",
            "SELECT json_build_object(",
            "    'inserted', EXISTS (SELECT 1 FROM attempted_insert),",
            "    'user', COALESCE((SELECT row_to_json(resolved_user) FROM resolved_user LIMIT 1), '{}'::json)",
            ");",
        ]
    )


def _build_create_session_sql(row: Dict[str, Any], *, ensure_schema: bool) -> str:
    schema_sql = auth_schema_sql_text() + "\n\n" if ensure_schema else ""

    return schema_sql + "\n".join(
        [
            "WITH inserted_session AS (",
            "    INSERT INTO auth_sessions (",
            "        session_id,",
            "        user_id,",
            "        session_token_hash,",
            "        created_at,",
            "        expires_at,",
            "        last_seen_at,",
            "        revoked_at,",
            "        user_agent,",
            "        ip_address",
            "    )",
            "    VALUES (",
            f"        {_sql_quote_text(row['session_id'])},",
            f"        {_sql_quote_text(row['user_id'])},",
            f"        {_sql_quote_text(row['session_token_hash'])},",
            f"        {_sql_quote_text(row['created_at'])}::timestamptz,",
            f"        {_sql_quote_text(row['expires_at'])}::timestamptz,",
            f"        {_sql_quote_text(row['last_seen_at'])}::timestamptz,",
            f"        {_sql_timestamptz_or_null(row.get('revoked_at'))},",
            f"        {_sql_quote_text(row['user_agent'])},",
            f"        {_sql_quote_text(row['ip_address'])}",
            "    )",
            "    RETURNING",
            "        session_id,",
            "        user_id,",
            "        created_at,",
            "        expires_at,",
            "        last_seen_at,",
            "        revoked_at,",
            "        user_agent,",
            "        ip_address",
            ")",
            "SELECT json_build_object(",
            "    'inserted', TRUE,",
            "    'session', COALESCE((SELECT row_to_json(inserted_session) FROM inserted_session LIMIT 1), '{}'::json)",
            ");",
        ]
    )


def create_auth_user_postgres_payload(
    *,
    record: Dict[str, Any],
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    allow_contract_drift: bool = False,
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    contract_health = auth_contract_health_payload()
    if not contract_health.get("all_checks_pass", False) and not allow_contract_drift:
        raise SystemExit(
            "Auth contract health check failed. Refusing Postgres insert while artifacts are drifting. "
            "Fix the schema artifact mismatch first, or pass --allow-contract-drift if you intentionally want to override."
        )

    row = auth_user_db_row(record)
    query_payload = _run_psql_json_query(
        sql=_build_create_user_sql(row, ensure_schema=ensure_schema),
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        print_only=print_only,
    )

    return {
        "ok": True,
        "contract_health_ok": bool(contract_health["all_checks_pass"]),
        "table_name": "auth_users",
        "row": row,
        "inserted": bool(query_payload.get("data", {}).get("inserted", False)),
        "user": dict(query_payload.get("data", {}).get("user", {}) or {}),
        "command": query_payload["command"],
        "command_text": query_payload["command_text"],
    }


def create_auth_session_postgres_payload(
    *,
    record: Dict[str, Any],
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    allow_contract_drift: bool = False,
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    contract_health = auth_contract_health_payload()
    if not contract_health.get("all_checks_pass", False) and not allow_contract_drift:
        raise SystemExit(
            "Auth contract health check failed. Refusing Postgres insert while artifacts are drifting. "
            "Fix the schema artifact mismatch first, or pass --allow-contract-drift if you intentionally want to override."
        )

    row = auth_session_db_row(record)
    query_payload = _run_psql_json_query(
        sql=_build_create_session_sql(row, ensure_schema=ensure_schema),
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        print_only=print_only,
    )

    return {
        "ok": True,
        "contract_health_ok": bool(contract_health["all_checks_pass"]),
        "table_name": "auth_sessions",
        "row": row,
        "inserted": bool(query_payload.get("data", {}).get("inserted", False)),
        "session": dict(query_payload.get("data", {}).get("session", {}) or {}),
        "command": query_payload["command"],
        "command_text": query_payload["command_text"],
    }