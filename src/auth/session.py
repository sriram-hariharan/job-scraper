from __future__ import annotations

import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Tuple

from src.config.consts import (
    AUTH_SESSION_COOKIE_NAME,
    AUTH_SESSION_COOKIE_SAMESITE,
    AUTH_SESSION_COOKIE_SECURE,
    AUTH_SESSION_TOKEN_BYTES,
    AUTH_SESSION_TTL_SECONDS,
)


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds")


def auth_cookie_name() -> str:
    return (
        _clean_text(os.environ.get("JOB_STACK_AUTH_COOKIE_NAME"))
        or AUTH_SESSION_COOKIE_NAME
    )


def auth_session_ttl_seconds() -> int:
    raw = _clean_text(os.environ.get("JOB_STACK_AUTH_SESSION_TTL_SECONDS"))
    if not raw:
        return int(AUTH_SESSION_TTL_SECONDS)

    try:
        parsed = int(raw)
    except ValueError:
        return int(AUTH_SESSION_TTL_SECONDS)

    if parsed <= 0:
        return int(AUTH_SESSION_TTL_SECONDS)

    return parsed


def auth_cookie_secure() -> bool:
    raw = _clean_text(os.environ.get("JOB_STACK_AUTH_COOKIE_SECURE")).lower()
    if not raw:
        return bool(AUTH_SESSION_COOKIE_SECURE)

    return raw in {"1", "true", "yes", "y", "on"}


def auth_cookie_samesite() -> str:
    raw = _clean_text(os.environ.get("JOB_STACK_AUTH_COOKIE_SAMESITE")).lower()
    if raw in {"lax", "strict", "none"}:
        return raw

    default_value = _clean_text(AUTH_SESSION_COOKIE_SAMESITE).lower()
    return default_value if default_value in {"lax", "strict", "none"} else "lax"


def generate_session_token() -> str:
    return secrets.token_urlsafe(AUTH_SESSION_TOKEN_BYTES)


def hash_session_token(session_token: str) -> str:
    token = _clean_text(session_token)
    if not token:
        raise ValueError("session_token is required.")

    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def session_expires_at_iso(ttl_seconds: int | None = None) -> str:
    ttl = int(ttl_seconds or auth_session_ttl_seconds())
    return _utc_iso(_utc_now() + timedelta(seconds=ttl))


def build_auth_session_record(
    *,
    user_id: str,
    session_token: str,
    user_agent: str = "",
    ip_address: str = "",
    ttl_seconds: int | None = None,
) -> Dict[str, Any]:
    safe_user_id = _clean_text(user_id)
    if not safe_user_id:
        raise ValueError("user_id is required.")

    safe_token = _clean_text(session_token)
    if not safe_token:
        raise ValueError("session_token is required.")

    created_at = _utc_iso(_utc_now())

    return {
        "user_id": safe_user_id,
        "session_token_hash": hash_session_token(safe_token),
        "created_at": created_at,
        "expires_at": session_expires_at_iso(ttl_seconds),
        "last_seen_at": created_at,
        "user_agent": _clean_text(user_agent),
        "ip_address": _clean_text(ip_address),
    }


def new_auth_session_record(
    *,
    user_id: str,
    user_agent: str = "",
    ip_address: str = "",
    ttl_seconds: int | None = None,
) -> Tuple[str, Dict[str, Any]]:
    session_token = generate_session_token()
    record = build_auth_session_record(
        user_id=user_id,
        session_token=session_token,
        user_agent=user_agent,
        ip_address=ip_address,
        ttl_seconds=ttl_seconds,
    )

    return session_token, record