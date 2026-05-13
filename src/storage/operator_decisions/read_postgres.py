from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlsplit, urlunsplit

from src.storage.operator_decisions.store import (
    _sql_quote_text,
    operator_decisions_schema_sql_text,
)


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


def _owner_where_clause(owner_user_id: str, *, prefix: str = "WHERE") -> str:
    safe_owner_user_id = str(owner_user_id or "").strip()
    if not safe_owner_user_id:
        return ""
    return f"{prefix} owner_user_id = {_sql_quote_text(safe_owner_user_id)}"


def _build_operator_decisions_status_sql(limit: int, owner_user_id: str = "") -> str:
    owner_where = _owner_where_clause(owner_user_id, prefix="WHERE")
    return f"""
WITH latest_rows AS (
    SELECT DISTINCT ON (decision_key)
        decision_id,
        owner_user_id,
        decision_key,
        decision_timestamp,
        queue_rank,
        job_doc_id,
        job_company,
        job_title,
        planning_action,
        winner_resume,
        winner_score,
        runner_up_resume,
        runner_up_score,
        selected_resume,
        decision,
        note
    FROM operator_decisions
    {owner_where}
    ORDER BY decision_key, decision_timestamp DESC, decision_id DESC
),
latest_rows_limited AS (
    SELECT
        decision_id,
        owner_user_id,
        decision_key,
        decision_timestamp,
        queue_rank,
        job_doc_id,
        job_company,
        job_title,
        planning_action,
        winner_resume,
        winner_score,
        runner_up_resume,
        runner_up_score,
        selected_resume,
        decision,
        note
    FROM latest_rows
    ORDER BY decision_timestamp DESC, decision_id DESC
    LIMIT {limit}
),
recent_rows AS (
    SELECT
        decision_id,
        owner_user_id,
        decision_key,
        decision_timestamp,
        queue_rank,
        job_doc_id,
        job_company,
        job_title,
        planning_action,
        winner_resume,
        winner_score,
        runner_up_resume,
        runner_up_score,
        selected_resume,
        decision,
        note
    FROM operator_decisions
    {owner_where}
    ORDER BY decision_timestamp DESC, decision_id DESC
    LIMIT {limit}
)
SELECT json_build_object(
    'total_row_count', (SELECT COUNT(*) FROM operator_decisions {owner_where}),
    'latest_state_count', (SELECT COUNT(*) FROM latest_rows),
    'recent_rows',
        COALESCE(
            (SELECT json_agg(row_to_json(recent_rows) ORDER BY recent_rows.decision_timestamp DESC, recent_rows.decision_id DESC) FROM recent_rows),
            '[]'::json
        ),
    'latest_rows',
        COALESCE(
            (SELECT json_agg(row_to_json(latest_rows_limited) ORDER BY latest_rows_limited.decision_timestamp DESC, latest_rows_limited.decision_id DESC) FROM latest_rows_limited),
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
        raise SystemExit("psql returned empty output for operator-decisions Postgres status query.")

    try:
        data = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"Failed to parse operator-decisions Postgres status JSON from psql output: {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise SystemExit("Operator-decisions Postgres status query did not return a JSON object.")

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
        "command": redacted_cmd,
        "command_text": shlex.join(redacted_cmd),
        "stdout": "",
        "stderr": "",
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

    payload["stdout"] = completed.stdout
    payload["stderr"] = completed.stderr
    return payload


def get_operator_decisions_postgres_status_payload(
    *,
    limit: int = 10,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    owner_user_id: str = "",
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    normalized_limit = _normalize_positive_int(limit, "limit")
    if ensure_schema:
        _run_psql_command(
            sql=operator_decisions_schema_sql_text(),
            database_url=database_url,
            database_url_env=database_url_env,
            psql_bin=psql_bin,
            print_only=print_only,
        )

    sql = _build_operator_decisions_status_sql(normalized_limit, owner_user_id=owner_user_id)

    query_payload = _run_psql_json_query(
        sql=sql,
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        print_only=print_only,
    )

    return {
        "ok": True,
        "query_limit": normalized_limit,
        "command": query_payload["command"],
        "command_text": query_payload["command_text"],
        "postgres": query_payload["data"],
    }
