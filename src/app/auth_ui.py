from __future__ import annotations

from html import escape
from typing import Any, Dict

from fastapi import APIRouter, Body, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel

from src.config.consts import (
    AUTH_FIRST_USER_ADMIN_ENABLED,
    AUTH_REGISTRATION_ENABLED,
)

from src.auth.password import hash_password, validate_new_password, verify_password
from src.auth.session import (
    auth_cookie_name,
    auth_cookie_samesite,
    auth_cookie_secure,
    auth_session_ttl_seconds,
    hash_session_token,
    new_auth_session_record,
)
from src.storage.auth.read_postgres import (
    get_auth_postgres_status_payload,
    get_auth_user_by_email_postgres_payload,
    get_auth_user_for_session_token_hash_postgres_payload,
    revoke_auth_session_postgres_payload,
    touch_auth_user_last_login_postgres_payload,
)
from src.storage.auth.store import create_auth_session_postgres_payload, create_auth_user_postgres_payload


router = APIRouter()


class AuthRegisterRequest(BaseModel):
    email: str
    password: str
    display_name: str = ""
    next: str = "/"


class AuthLoginRequest(BaseModel):
    email: str
    password: str
    next: str = "/"


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _env_bool(name: str, default: bool) -> bool:
    import os

    raw = _clean_text(os.environ.get(name)).lower()
    if not raw:
        return bool(default)

    if raw in {"1", "true", "yes", "y", "on"}:
        return True

    if raw in {"0", "false", "no", "n", "off"}:
        return False

    return bool(default)


def _registration_enabled() -> bool:
    return _env_bool(
        "JOB_STACK_AUTH_REGISTRATION_ENABLED",
        bool(AUTH_REGISTRATION_ENABLED),
    )


def _first_user_admin_enabled() -> bool:
    return _env_bool(
        "JOB_STACK_AUTH_FIRST_USER_ADMIN_ENABLED",
        bool(AUTH_FIRST_USER_ADMIN_ENABLED),
    )


def _auth_user_counts() -> Dict[str, int]:
    try:
        payload = get_auth_postgres_status_payload(
            limit=1,
            ensure_schema=True,
        )
    except Exception:
        return {
            "user_count": 0,
            "active_user_count": 0,
        }

    postgres = dict(payload.get("postgres", {}) or {})
    return {
        "user_count": int(postgres.get("user_count", 0) or 0),
        "active_user_count": int(postgres.get("active_user_count", 0) or 0),
    }


def _can_register() -> bool:
    if _registration_enabled():
        return True

    if not _first_user_admin_enabled():
        return False

    counts = _auth_user_counts()
    return int(counts.get("active_user_count", 0) or 0) == 0


def _should_create_admin_user() -> bool:
    if not _first_user_admin_enabled():
        return False

    counts = _auth_user_counts()
    return int(counts.get("active_user_count", 0) or 0) == 0


def _safe_next_path(value: str) -> str:
    raw = _clean_text(value)
    if not raw:
        return "/"

    if not raw.startswith("/") or raw.startswith("//"):
        return "/"

    if raw.startswith("/auth/") or raw in {"/login", "/register", "/logout"}:
        return "/"

    return raw


def _request_ip_address(request: Request) -> str:
    forwarded_for = _clean_text(request.headers.get("x-forwarded-for"))
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()

    if request.client and request.client.host:
        return request.client.host

    return ""


def _public_user_payload(user: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "user_id": _clean_text(user.get("user_id")),
        "email": _clean_text(user.get("email")),
        "display_name": _clean_text(user.get("display_name")),
        "is_active": bool(user.get("is_active", False)),
        "is_admin": bool(user.get("is_admin", False)),
        "created_at": _clean_text(user.get("created_at")),
        "updated_at": _clean_text(user.get("updated_at")),
        "last_login_at": _clean_text(user.get("last_login_at")),
    }


def _set_session_cookie(response: Response, session_token: str) -> None:
    response.set_cookie(
        key=auth_cookie_name(),
        value=session_token,
        max_age=auth_session_ttl_seconds(),
        httponly=True,
        secure=auth_cookie_secure(),
        samesite=auth_cookie_samesite(),
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=auth_cookie_name(),
        path="/",
    )


def _auth_page_html(*, mode: str, next_path: str, error_message: str = "") -> str:
    is_register = mode == "register"
    title = "Create account" if is_register else "Log in"
    subtitle = (
        "Create your ApplyLens AI dashboard account."
        if is_register
        else "Log in to continue to ApplyLens AI."
    )
    submit_label = "Create account" if is_register else "Log in"
    alternate_href = f"/login?next={escape(next_path)}" if is_register else f"/register?next={escape(next_path)}"
    alternate_label = "Already have an account? Log in" if is_register else "Need an account? Register"

    display_name_field = ""
    if is_register:
        display_name_field = """
        <label class="auth-field">
          <span>Name</span>
          <input id="displayNameInput" type="text" autocomplete="name" placeholder="Sriram" />
        </label>
        """

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{escape(title)} · ApplyLens AI</title>
  <link rel="stylesheet" href="/static/vendor/tabler/tabler.min.css" />
  <link rel="stylesheet" href="/static/styles.css?v=ui_redesign_v17" />
  <link rel="stylesheet" href="/static/app_redesign.css?v=ui_redesign_v28" />
  <style>
    body {{
      min-height: 100vh;
      display: grid;
      place-items: center;
      padding: 24px;
      background: #070b13;
    }}

    .auth-card {{
      width: min(440px, 100%);
      border: 1px solid rgba(148, 163, 184, 0.25);
      border-radius: 24px;
      padding: 28px;
      background: rgba(15, 23, 42, 0.92);
      box-shadow: 0 24px 80px rgba(0, 0, 0, 0.35);
    }}

    .auth-brand {{
      font-size: 13px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: #93c5fd;
      margin-bottom: 14px;
      font-weight: 700;
    }}

    .auth-title {{
      margin: 0;
      font-size: 28px;
      line-height: 1.15;
      color: #f8fafc;
    }}

    .auth-subtitle {{
      margin: 10px 0 22px;
      color: #94a3b8;
      line-height: 1.5;
    }}

    .auth-form {{
      display: grid;
      gap: 14px;
    }}

    .auth-field {{
      display: grid;
      gap: 8px;
      color: #cbd5e1;
      font-size: 13px;
      font-weight: 650;
    }}

    .auth-field input {{
      width: 100%;
      border: 1px solid rgba(148, 163, 184, 0.32);
      border-radius: 14px;
      padding: 12px 14px;
      background: rgba(2, 6, 23, 0.7);
      color: #f8fafc;
      outline: none;
    }}

    .auth-field input:focus {{
      border-color: rgba(96, 165, 250, 0.9);
      box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.18);
    }}

    .auth-error {{
      display: none;
      border: 1px solid rgba(248, 113, 113, 0.35);
      border-radius: 14px;
      padding: 10px 12px;
      background: rgba(127, 29, 29, 0.25);
      color: #fecaca;
      font-size: 13px;
      line-height: 1.45;
    }}

    .auth-error.is-visible {{
      display: block;
    }}

    .auth-submit {{
      margin-top: 4px;
      width: 100%;
      border: 0;
      border-radius: 14px;
      padding: 12px 14px;
      font-weight: 750;
      background: #3b82f6;
      color: white;
      cursor: pointer;
    }}

    .auth-submit:disabled {{
      opacity: 0.65;
      cursor: not-allowed;
    }}

    .auth-alt {{
      display: block;
      margin-top: 18px;
      color: #93c5fd;
      text-decoration: none;
      font-size: 14px;
    }}
  </style>
</head>
<body>
  <main class="auth-card">
    <div class="auth-brand">ApplyLens AI</div>
    <h1 class="auth-title">{escape(title)}</h1>
    <p class="auth-subtitle">{escape(subtitle)}</p>

    <div id="authError" class="auth-error {"is-visible" if error_message else ""}">
      {escape(error_message)}
    </div>

    <form id="authForm" class="auth-form" data-mode="{escape(mode)}">
      <input id="nextInput" type="hidden" value="{escape(next_path)}" />

      {display_name_field}

      <label class="auth-field">
        <span>Email</span>
        <input id="emailInput" type="email" autocomplete="email" required />
      </label>

      <label class="auth-field">
        <span>Password</span>
        <input id="passwordInput" type="password" autocomplete="{"new-password" if is_register else "current-password"}" required />
      </label>

      <button id="authSubmitBtn" class="auth-submit" type="submit">
        {escape(submit_label)}
      </button>
    </form>

    <a class="auth-alt" href="{alternate_href}">
      {escape(alternate_label)}
    </a>
  </main>

  <script>
    const form = document.getElementById("authForm");
    const errorEl = document.getElementById("authError");
    const submitBtn = document.getElementById("authSubmitBtn");

    function showError(message) {{
      errorEl.textContent = message || "Request failed.";
      errorEl.classList.add("is-visible");
    }}

    form.addEventListener("submit", async (event) => {{
      event.preventDefault();
      errorEl.classList.remove("is-visible");
      submitBtn.disabled = true;

      const mode = form.dataset.mode;
      const body = {{
        email: document.getElementById("emailInput").value,
        password: document.getElementById("passwordInput").value,
        next: document.getElementById("nextInput").value || "/",
      }};

      const displayNameInput = document.getElementById("displayNameInput");
      if (displayNameInput) {{
        body.display_name = displayNameInput.value;
      }}

      try {{
        const response = await fetch(mode === "register" ? "/auth/register" : "/auth/login", {{
          method: "POST",
          headers: {{
            "Content-Type": "application/json",
          }},
          body: JSON.stringify(body),
        }});

        const payload = await response.json().catch(() => ({{}}));
        if (!response.ok || !payload.ok) {{
          throw new Error(payload.detail || "Request failed.");
        }}

        window.location.href = payload.redirect_to || "/";
      }} catch (error) {{
        showError(error instanceof Error ? error.message : "Request failed.");
      }} finally {{
        submitBtn.disabled = false;
      }}
    }});
  </script>
</body>
</html>
""".strip()


def _current_user_from_request(request: Request) -> Dict[str, Any]:
    session_token = _clean_text(request.cookies.get(auth_cookie_name()))
    if not session_token:
        return {}

    try:
        payload = get_auth_user_for_session_token_hash_postgres_payload(
            session_token_hash=hash_session_token(session_token),
            ensure_schema=True,
        )
    except Exception:
        return {}

    if not payload.get("ok"):
        return {}

    user = dict(payload.get("user", {}) or {})
    if not user:
        return {}

    return user


@router.get("/login")
def login_page(request: Request, next: str = "/"):
    next_path = _safe_next_path(next)

    if _current_user_from_request(request):
        return RedirectResponse(url=next_path, status_code=303)

    return HTMLResponse(
        _auth_page_html(
            mode="login",
            next_path=next_path,
        )
    )


@router.get("/register")
def register_page(request: Request, next: str = "/"):
    next_path = _safe_next_path(next)

    if _current_user_from_request(request):
        return RedirectResponse(url=next_path, status_code=303)

    if not _can_register():
        return HTMLResponse(
            _auth_page_html(
                mode="login",
                next_path=next_path,
                error_message="Registration is currently disabled.",
            )
        )

    return HTMLResponse(
        _auth_page_html(
            mode="register",
            next_path=next_path,
        )
    )


@router.post("/auth/register")
def register(request: Request, payload: AuthRegisterRequest = Body(...)):
    try:
        if not _can_register():
            raise HTTPException(
                status_code=403,
                detail="Registration is currently disabled.",
            )

        validate_new_password(payload.password)
        make_admin = _should_create_admin_user()
        created = create_auth_user_postgres_payload(
            record={
                "email": payload.email,
                "password_hash": hash_password(payload.password),
                "display_name": payload.display_name,
                "is_active": True,
                "is_admin": make_admin,
            },
            ensure_schema=True,
        )

        if not created.get("inserted", False):
            raise HTTPException(
                status_code=409,
                detail="An account already exists for this email.",
            )

        user = dict(created.get("user", {}) or {})
        session_token, session_record = new_auth_session_record(
            user_id=str(user.get("user_id", "") or ""),
            user_agent=_clean_text(request.headers.get("user-agent")),
            ip_address=_request_ip_address(request),
        )

        create_auth_session_postgres_payload(
            record=session_record,
            ensure_schema=True,
        )
        touch_auth_user_last_login_postgres_payload(
            user_id=str(user.get("user_id", "") or ""),
            ensure_schema=True,
        )

        response = JSONResponse(
            {
                "ok": True,
                "user": _public_user_payload(user),
                "redirect_to": _safe_next_path(payload.next),
            }
        )
        _set_session_cookie(response, session_token)
        return response

    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except SystemExit as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/auth/login")
def login(request: Request, payload: AuthLoginRequest = Body(...)):
    try:
        loaded = get_auth_user_by_email_postgres_payload(
            email=payload.email,
            ensure_schema=True,
        )

        user = dict(loaded.get("user", {}) or {})
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password.")

        if not bool(user.get("is_active", False)):
            raise HTTPException(status_code=403, detail="This account is inactive.")

        if not verify_password(payload.password, str(user.get("password_hash", "") or "")):
            raise HTTPException(status_code=401, detail="Invalid email or password.")

        session_token, session_record = new_auth_session_record(
            user_id=str(user.get("user_id", "") or ""),
            user_agent=_clean_text(request.headers.get("user-agent")),
            ip_address=_request_ip_address(request),
        )

        create_auth_session_postgres_payload(
            record=session_record,
            ensure_schema=True,
        )
        touched = touch_auth_user_last_login_postgres_payload(
            user_id=str(user.get("user_id", "") or ""),
            ensure_schema=True,
        )

        response = JSONResponse(
            {
                "ok": True,
                "user": _public_user_payload(dict(touched.get("user", {}) or user)),
                "redirect_to": _safe_next_path(payload.next),
            }
        )
        _set_session_cookie(response, session_token)
        return response

    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except SystemExit as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/auth/logout")
def logout(request: Request):
    session_token = _clean_text(request.cookies.get(auth_cookie_name()))

    if session_token:
        try:
            revoke_auth_session_postgres_payload(
                session_token_hash=hash_session_token(session_token),
                ensure_schema=True,
            )
        except Exception:
            pass

    response = JSONResponse({"ok": True, "redirect_to": "/login"})
    _clear_session_cookie(response)
    return response


@router.get("/auth/me")
def auth_me(request: Request):
    user = _current_user_from_request(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated.")

    return {
        "ok": True,
        "user": _public_user_payload(user),
    }


@router.get("/logout")
def logout_redirect(request: Request):
    session_token = _clean_text(request.cookies.get(auth_cookie_name()))

    if session_token:
        try:
            revoke_auth_session_postgres_payload(
                session_token_hash=hash_session_token(session_token),
                ensure_schema=True,
            )
        except Exception:
            pass

    response = RedirectResponse(url="/login", status_code=303)
    _clear_session_cookie(response)
    return response