from __future__ import annotations

import os
from typing import Any, Dict
from urllib.parse import quote

from fastapi import Request
from fastapi.responses import JSONResponse, RedirectResponse, Response

from src.auth.session import (
    auth_cookie_name,
    auth_session_idle_timeout_seconds,
    hash_session_token,
)
from src.storage.auth.read_postgres import get_auth_user_for_session_token_hash_postgres_payload


PUBLIC_AUTH_EXACT_PATHS = {
    "/health",
    "/login",
    "/register",
    "/logout",
    "/auth/login",
    "/auth/register",
    "/auth/logout",
    "/auth/session-config",
    "/auth/me",
    "/favicon.ico",
}

PUBLIC_AUTH_PREFIXES = (
    "/static/",
)

HTML_NAVIGATION_PATHS = {
    "/",
    "/planning",
    "/decisions-ui",
    "/applications",
    "/scheduler",
    "/profile",
    "/profile/preferences",
    "/profile/saved-scans",
    "/onboarding",
    "/scan-workspace",
    "/tailoring-workspace",
}


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def auth_enabled() -> bool:
    raw = _clean_text(os.environ.get("JOB_STACK_AUTH_ENABLED", "true")).lower()
    return raw not in {"0", "false", "no", "off"}


def _is_public_auth_path(path: str) -> bool:
    safe_path = _clean_text(path) or "/"

    if safe_path in PUBLIC_AUTH_EXACT_PATHS:
        return True

    return any(safe_path.startswith(prefix) for prefix in PUBLIC_AUTH_PREFIXES)


def _request_next_path(request: Request) -> str:
    path = request.url.path or "/"
    query = _clean_text(request.url.query)
    return f"{path}?{query}" if query else path


def _login_redirect_response(request: Request) -> RedirectResponse:
    next_path = _request_next_path(request)
    encoded_next = quote(next_path, safe="/?:=&")
    return RedirectResponse(
        url=f"/login?next={encoded_next}",
        status_code=303,
    )


def _should_redirect_to_login(request: Request) -> bool:
    if request.method.upper() != "GET":
        return False

    path = request.url.path or "/"
    if path in HTML_NAVIGATION_PATHS:
        return True

    sec_fetch_mode = _clean_text(request.headers.get("sec-fetch-mode")).lower()
    if sec_fetch_mode == "navigate":
        return True

    accept = _clean_text(request.headers.get("accept")).lower()
    return "text/html" in accept and path not in {"/auth/me"}


def current_user_from_request(request: Request) -> Dict[str, Any]:
    session_token = _clean_text(request.cookies.get(auth_cookie_name()))
    if not session_token:
        return {}

    try:
        payload = get_auth_user_for_session_token_hash_postgres_payload(
            session_token_hash=hash_session_token(session_token),
            idle_timeout_seconds=auth_session_idle_timeout_seconds(),
            ensure_schema=False,
        )
    except Exception:
        return {}

    if not payload.get("ok"):
        return {}

    user = dict(payload.get("user", {}) or {})
    if not user:
        return {}

    return user


def auth_guard_response(request: Request) -> Response | None:
    if not auth_enabled():
        return None

    path = request.url.path or "/"
    if _is_public_auth_path(path):
        return None

    user = current_user_from_request(request)
    if user:
        request.state.auth_user = user
        return None

    if _should_redirect_to_login(request):
        return _login_redirect_response(request)

    return JSONResponse(
        {"detail": "Not authenticated."},
        status_code=401,
    )
