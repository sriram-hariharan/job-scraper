from __future__ import annotations

from typing import Any, Dict

from src.storage.auth.store import (
    _clean_text,
    _normalize_email,
    _run_psql_json_query,
    _sql_quote_text,
    auth_schema_sql_text,
)


def _normalize_positive_int(value: Any, field_name: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be an integer.") from exc

    if parsed <= 0:
        raise ValueError(f"{field_name} must be > 0.")

    return parsed


def _schema_prefix(ensure_schema: bool) -> str:
    return auth_schema_sql_text() + "\n\n" if ensure_schema else ""


def _build_user_by_email_sql(email: str, *, ensure_schema: bool) -> str:
    normalized_email = _normalize_email(email)

    return _schema_prefix(ensure_schema) + f"""
SELECT COALESCE(
    (
        SELECT row_to_json(row_data)
        FROM (
            SELECT
                user_id,
                email,
                normalized_email,
                password_hash,
                display_name,
                access_level,
                is_active,
                is_admin,
                created_at,
                updated_at,
                last_login_at
            FROM auth_users
            WHERE normalized_email = {_sql_quote_text(normalized_email)}
            LIMIT 1
        ) row_data
    ),
    '{{}}'::json
);
""".strip()


def _build_user_by_id_sql(user_id: str, *, ensure_schema: bool) -> str:
    return _schema_prefix(ensure_schema) + f"""
SELECT COALESCE(
    (
        SELECT row_to_json(row_data)
        FROM (
            SELECT
                user_id,
                email,
                normalized_email,
                password_hash,
                display_name,
                access_level,
                is_active,
                is_admin,
                created_at,
                updated_at,
                last_login_at
            FROM auth_users
            WHERE user_id = {_sql_quote_text(user_id)}
            LIMIT 1
        ) row_data
    ),
    '{{}}'::json
);
""".strip()


def _build_active_session_user_sql(session_token_hash: str, *, ensure_schema: bool) -> str:
    return _schema_prefix(ensure_schema) + f"""
WITH matched_session AS (
    SELECT
        session_id,
        user_id,
        created_at,
        expires_at,
        last_seen_at,
        revoked_at,
        user_agent,
        ip_address
    FROM auth_sessions
    WHERE session_token_hash = {_sql_quote_text(session_token_hash)}
      AND revoked_at IS NULL
      AND expires_at > now()
    LIMIT 1
),
touched_session AS (
    UPDATE auth_sessions
    SET last_seen_at = now()
    WHERE session_id IN (SELECT session_id FROM matched_session)
    RETURNING
        session_id,
        user_id,
        created_at,
        expires_at,
        last_seen_at,
        revoked_at,
        user_agent,
        ip_address
),
matched_user AS (
    SELECT
        u.user_id,
        u.email,
        u.normalized_email,
        u.display_name,
        u.access_level,
        u.is_active,
        u.is_admin,
        u.created_at,
        u.updated_at,
        u.last_login_at
    FROM auth_users u
    JOIN touched_session s
      ON s.user_id = u.user_id
    WHERE u.is_active = TRUE
    LIMIT 1
)
SELECT json_build_object(
    'session', COALESCE((SELECT row_to_json(touched_session) FROM touched_session LIMIT 1), '{{}}'::json),
    'user', COALESCE((SELECT row_to_json(matched_user) FROM matched_user LIMIT 1), '{{}}'::json)
);
""".strip()


def _build_revoke_session_sql(session_token_hash: str, *, ensure_schema: bool) -> str:
    return _schema_prefix(ensure_schema) + f"""
WITH revoked_session AS (
    UPDATE auth_sessions
    SET revoked_at = now()
    WHERE session_token_hash = {_sql_quote_text(session_token_hash)}
      AND revoked_at IS NULL
    RETURNING session_id
)
SELECT json_build_object(
    'revoked', EXISTS (SELECT 1 FROM revoked_session),
    'session_id', COALESCE((SELECT session_id FROM revoked_session LIMIT 1), '')
);
""".strip()


def _build_touch_last_login_sql(user_id: str, *, ensure_schema: bool) -> str:
    return _schema_prefix(ensure_schema) + f"""
WITH updated_user AS (
    UPDATE auth_users
    SET
        last_login_at = now(),
        updated_at = now()
    WHERE user_id = {_sql_quote_text(user_id)}
    RETURNING
        user_id,
        email,
        normalized_email,
        display_name,
        access_level,
        is_active,
        is_admin,
        created_at,
        updated_at,
        last_login_at
)
SELECT COALESCE(
    (SELECT row_to_json(updated_user) FROM updated_user LIMIT 1),
    '{{}}'::json
);
""".strip()


def _build_auth_status_sql(limit: int, *, ensure_schema: bool) -> str:
    return _schema_prefix(ensure_schema) + f"""
WITH recent_users AS (
    SELECT
        user_id,
        email,
        normalized_email,
        display_name,
        access_level,
        is_active,
        is_admin,
        created_at,
        updated_at,
        last_login_at
    FROM auth_users
    ORDER BY created_at DESC, user_id DESC
    LIMIT {limit}
),
recent_sessions AS (
    SELECT
        session_id,
        user_id,
        created_at,
        expires_at,
        last_seen_at,
        revoked_at,
        user_agent,
        ip_address
    FROM auth_sessions
    ORDER BY created_at DESC, session_id DESC
    LIMIT {limit}
)
SELECT json_build_object(
    'user_count', (SELECT COUNT(*) FROM auth_users),
    'active_user_count', (SELECT COUNT(*) FROM auth_users WHERE is_active = TRUE),
    'session_count', (SELECT COUNT(*) FROM auth_sessions),
    'active_session_count', (
        SELECT COUNT(*)
        FROM auth_sessions
        WHERE revoked_at IS NULL
          AND expires_at > now()
    ),
    'recent_users',
        COALESCE(
            (SELECT json_agg(row_to_json(recent_users) ORDER BY recent_users.created_at DESC, recent_users.user_id DESC) FROM recent_users),
            '[]'::json
        ),
    'recent_sessions',
        COALESCE(
            (SELECT json_agg(row_to_json(recent_sessions) ORDER BY recent_sessions.created_at DESC, recent_sessions.session_id DESC) FROM recent_sessions),
            '[]'::json
        )
);
""".strip()


def get_auth_user_by_email_postgres_payload(
    *,
    email: str,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    safe_email = _clean_text(email)
    if not safe_email:
        raise ValueError("email is required.")

    query_payload = _run_psql_json_query(
        sql=_build_user_by_email_sql(safe_email, ensure_schema=ensure_schema),
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        print_only=print_only,
    )

    user = dict(query_payload.get("data", {}) or {})
    return {
        "ok": bool(user),
        "user": user,
        "command": query_payload["command"],
        "command_text": query_payload["command_text"],
    }


def get_auth_user_by_id_postgres_payload(
    *,
    user_id: str,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    safe_user_id = _clean_text(user_id)
    if not safe_user_id:
        raise ValueError("user_id is required.")

    query_payload = _run_psql_json_query(
        sql=_build_user_by_id_sql(safe_user_id, ensure_schema=ensure_schema),
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        print_only=print_only,
    )

    user = dict(query_payload.get("data", {}) or {})
    return {
        "ok": bool(user),
        "user": user,
        "command": query_payload["command"],
        "command_text": query_payload["command_text"],
    }


def get_auth_user_for_session_token_hash_postgres_payload(
    *,
    session_token_hash: str,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    safe_token_hash = _clean_text(session_token_hash)
    if not safe_token_hash:
        raise ValueError("session_token_hash is required.")

    query_payload = _run_psql_json_query(
        sql=_build_active_session_user_sql(safe_token_hash, ensure_schema=ensure_schema),
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        print_only=print_only,
    )

    data = dict(query_payload.get("data", {}) or {})
    user = dict(data.get("user", {}) or {})
    session = dict(data.get("session", {}) or {})

    return {
        "ok": bool(user and session),
        "user": user,
        "session": session,
        "command": query_payload["command"],
        "command_text": query_payload["command_text"],
    }


def revoke_auth_session_postgres_payload(
    *,
    session_token_hash: str,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    safe_token_hash = _clean_text(session_token_hash)
    if not safe_token_hash:
        raise ValueError("session_token_hash is required.")

    query_payload = _run_psql_json_query(
        sql=_build_revoke_session_sql(safe_token_hash, ensure_schema=ensure_schema),
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        print_only=print_only,
    )

    data = dict(query_payload.get("data", {}) or {})
    return {
        "ok": True,
        "revoked": bool(data.get("revoked", False)),
        "session_id": str(data.get("session_id", "") or ""),
        "command": query_payload["command"],
        "command_text": query_payload["command_text"],
    }


def touch_auth_user_last_login_postgres_payload(
    *,
    user_id: str,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    safe_user_id = _clean_text(user_id)
    if not safe_user_id:
        raise ValueError("user_id is required.")

    query_payload = _run_psql_json_query(
        sql=_build_touch_last_login_sql(safe_user_id, ensure_schema=ensure_schema),
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        print_only=print_only,
    )

    user = dict(query_payload.get("data", {}) or {})
    return {
        "ok": bool(user),
        "user": user,
        "command": query_payload["command"],
        "command_text": query_payload["command_text"],
    }


def get_auth_postgres_status_payload(
    *,
    limit: int = 10,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    normalized_limit = _normalize_positive_int(limit, "limit")

    query_payload = _run_psql_json_query(
        sql=_build_auth_status_sql(normalized_limit, ensure_schema=ensure_schema),
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        print_only=print_only,
    )

    return {
        "ok": True,
        "query_limit": normalized_limit,
        "postgres": dict(query_payload.get("data", {}) or {}),
        "command": query_payload["command"],
        "command_text": query_payload["command_text"],
    }
