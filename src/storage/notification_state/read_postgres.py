from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterable, List
from urllib.parse import urlsplit, urlunsplit


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


def _sql_quote_text(value: Any) -> str:
    return "'" + str(value or "").replace("'", "''") + "'"


def _build_notification_state_status_sql(
    limit: int,
    *,
    owner_user_id: str = "",
) -> str:
    owner = str(owner_user_id or "").strip()
    if owner:
        state_scope = (
            "WHERE owner_user_id IN ("
            f"{_sql_quote_text(owner)}, ''"
            ")"
        )
        distinct_columns = "notification_id"
        latest_order = (
            "notification_id, "
            f"CASE WHEN owner_user_id = {_sql_quote_text(owner)} THEN 0 ELSE 1 END, "
            "state_timestamp DESC, state_id DESC"
        )
        recent_scope = f"WHERE owner_user_id = {_sql_quote_text(owner)}"
    else:
        state_scope = ""
        distinct_columns = "owner_user_id, notification_id"
        latest_order = "owner_user_id, notification_id, state_timestamp DESC, state_id DESC"
        recent_scope = ""

    return f"""
WITH latest_rows AS (
    SELECT DISTINCT ON ({distinct_columns})
        state_id,
        state_timestamp,
        owner_user_id,
        notification_id,
        is_read,
        is_deleted
    FROM notification_state_events
    {state_scope}
    ORDER BY {latest_order}
),
latest_rows_limited AS (
    SELECT
        state_id,
        state_timestamp,
        owner_user_id,
        notification_id,
        is_read,
        is_deleted
    FROM latest_rows
    ORDER BY state_timestamp DESC, state_id DESC
    LIMIT {limit}
),
recent_rows AS (
    SELECT
        state_id,
        state_timestamp,
        owner_user_id,
        notification_id,
        is_read,
        is_deleted
    FROM notification_state_events
    {recent_scope}
    ORDER BY state_timestamp DESC, state_id DESC
    LIMIT {limit}
)
SELECT json_build_object(
    'total_row_count', (SELECT COUNT(*) FROM notification_state_events),
    'latest_state_count', (SELECT COUNT(*) FROM latest_rows),
    'recent_rows',
        COALESCE(
            (SELECT json_agg(row_to_json(recent_rows) ORDER BY recent_rows.state_timestamp DESC, recent_rows.state_id DESC) FROM recent_rows),
            '[]'::json
        ),
    'latest_rows',
        COALESCE(
            (SELECT json_agg(row_to_json(latest_rows_limited) ORDER BY latest_rows_limited.state_timestamp DESC, latest_rows_limited.state_id DESC) FROM latest_rows_limited),
            '[]'::json
        )
);
""".strip()


MAX_NOTIFICATION_STATE_LOOKUP_IDS = 501


def _build_latest_notification_states_sql(
    notification_ids: Iterable[str],
    *,
    owner_user_id: str,
) -> str:
    owner = str(owner_user_id or "").strip()
    if not owner:
        raise ValueError("owner_user_id is required.")

    normalized_ids = list(
        dict.fromkeys(
            str(notification_id or "").strip()
            for notification_id in notification_ids
            if str(notification_id or "").strip()
        )
    )
    if not normalized_ids:
        raise ValueError("notification_ids must contain at least one identifier.")
    if len(normalized_ids) > MAX_NOTIFICATION_STATE_LOOKUP_IDS:
        raise ValueError(
            f"notification_ids cannot exceed {MAX_NOTIFICATION_STATE_LOOKUP_IDS} identifiers."
        )

    requested_values = ",\n        ".join(
        f"({_sql_quote_text(notification_id)})"
        for notification_id in normalized_ids
    )
    return f"""
WITH requested(notification_id) AS (
    VALUES
        {requested_values}
),
latest_rows AS (
    SELECT DISTINCT ON (events.notification_id)
        events.state_id,
        events.state_timestamp,
        events.owner_user_id,
        events.notification_id,
        events.is_read,
        events.is_deleted
    FROM notification_state_events AS events
    INNER JOIN requested USING (notification_id)
    WHERE events.owner_user_id IN ({_sql_quote_text(owner)}, '')
    ORDER BY
        events.notification_id,
        CASE WHEN events.owner_user_id = {_sql_quote_text(owner)} THEN 0 ELSE 1 END,
        events.state_timestamp DESC,
        events.state_id DESC
)
SELECT json_build_object(
    'latest_rows', COALESCE(
        (
            SELECT json_agg(
                row_to_json(latest_rows)
                ORDER BY latest_rows.state_timestamp DESC, latest_rows.state_id DESC
            )
            FROM latest_rows
        ),
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
        raise SystemExit("psql returned empty output for notification-state Postgres status query.")

    try:
        data = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"Failed to parse notification-state Postgres status JSON from psql output: {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise SystemExit("Notification-state Postgres status query did not return a JSON object.")

    payload["data"] = data
    return payload


def get_notification_state_postgres_status_payload(
    *,
    limit: int = 10,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    owner_user_id: str = "",
) -> Dict[str, Any]:
    normalized_limit = _normalize_positive_int(limit, "limit")
    sql = _build_notification_state_status_sql(
        normalized_limit,
        owner_user_id=owner_user_id,
    )

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


def get_latest_notification_states_postgres_payload(
    *,
    notification_ids: Iterable[str],
    owner_user_id: str,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
) -> Dict[str, Any]:
    normalized_ids = list(
        dict.fromkeys(
            str(notification_id or "").strip()
            for notification_id in notification_ids
            if str(notification_id or "").strip()
        )
    )
    sql = _build_latest_notification_states_sql(
        normalized_ids,
        owner_user_id=owner_user_id,
    )
    query_payload = _run_psql_json_query(
        sql=sql,
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        print_only=print_only,
    )
    return {
        "ok": True,
        "notification_ids": normalized_ids,
        "query_count": len(normalized_ids),
        "command": query_payload["command"],
        "command_text": query_payload["command_text"],
        "postgres": query_payload["data"],
    }
