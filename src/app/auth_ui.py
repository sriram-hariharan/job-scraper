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
from src.auth.runtime import current_user_from_request
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
    except (Exception, SystemExit):
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
        "access_level": _clean_text(user.get("access_level")) or "user",
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
        secure=auth_cookie_secure(),
        samesite=auth_cookie_samesite(),
    )


def _auth_page_html(*, mode: str, next_path: str, error_message: str = "") -> str:
    is_register = mode == "register"
    title = "Create account" if is_register else "Log in"
    subtitle = (
        "Create your workspace to scrape jobs, scan resume fit, and save tailored drafts."
        if is_register
        else "Log in to scrape jobs, scan fit, and continue tailoring with ApplyLens AI."
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
<html lang="en" data-theme="light">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{escape(title)} · ApplyLens AI</title>
  <link rel="stylesheet" href="/static/vendor/tabler/tabler.min.css" />
  <link rel="stylesheet" href="/static/styles.css?v=ui_redesign_v17" />
  <link rel="stylesheet" href="/static/app_redesign.css?v=ui_redesign_v36" />
  <style>
    body {{
      min-height: 100vh;
      margin: 0;
      padding: clamp(18px, 3vw, 36px);
      background:
        radial-gradient(circle at 12% 10%, rgba(37, 99, 235, 0.14), transparent 30%),
        radial-gradient(circle at 90% 12%, rgba(14, 165, 233, 0.14), transparent 28%),
        linear-gradient(135deg, #f6f9ff 0%, #eef7ff 46%, #fbfdff 100%);
      color: #111827;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      overflow-x: hidden;
    }}

    .auth-shell {{
      display: grid;
      grid-template-columns: minmax(0, 1.02fr) minmax(370px, 470px);
      width: min(1120px, 100%);
      min-height: min(700px, calc(100vh - clamp(36px, 6vw, 72px)));
      margin: 0 auto;
      border: 1px solid rgba(148, 163, 184, 0.28);
      border-radius: 32px;
      background: rgba(255, 255, 255, 0.9);
      box-shadow: 0 28px 80px rgba(15, 23, 42, 0.13);
      overflow: hidden;
    }}

    .auth-hero {{
      position: relative;
      display: grid;
      grid-template-rows: auto 1fr auto;
      gap: clamp(26px, 5vw, 60px);
      min-width: 0;
      padding: clamp(32px, 4.5vw, 60px);
      background:
        radial-gradient(circle at 20% 16%, rgba(37, 99, 235, 0.16), transparent 30%),
        radial-gradient(circle at 86% 10%, rgba(34, 211, 238, 0.2), transparent 32%),
        linear-gradient(135deg, #f9fbff 0%, #eef7ff 54%, #effdff 100%);
      border-right: 1px solid rgba(148, 163, 184, 0.24);
    }}

    .auth-brand-lockup {{
      position: relative;
      display: flex;
      align-items: center;
      width: fit-content;
      padding: 0;
      border: 0;
      border-radius: 0;
      background: transparent;
      box-shadow: none;
    }}

    .auth-brand-logo {{
      display: block;
      width: clamp(260px, 31vw, 380px);
      height: clamp(84px, 10vw, 122px);
      object-fit: contain;
      object-position: left center;
      filter: drop-shadow(0 18px 30px rgba(37, 99, 235, 0.12));
    }}

    .auth-brand-text {{
      display: none;
    }}

    .auth-brand-text small {{
      display: none;
    }}

    .auth-hero-copy {{
      position: relative;
      align-self: center;
      display: grid;
      gap: 16px;
      max-width: 560px;
    }}

    .auth-hero-kicker {{
      width: fit-content;
      border: 1px solid rgba(37, 99, 235, 0.18);
      border-radius: 999px;
      padding: 7px 12px;
      background: rgba(255, 255, 255, 0.88);
      color: #2563eb;
      font-size: 12px;
      font-weight: 900;
      letter-spacing: 0.11em;
      text-transform: uppercase;
      box-shadow: 0 10px 24px rgba(37, 99, 235, 0.08);
    }}

    .auth-hero-title {{
      margin: 0;
      color: #111827 !important;
      font-size: clamp(42px, 5vw, 68px) !important;
      font-weight: 950 !important;
      line-height: 1.02 !important;
      letter-spacing: 0 !important;
    }}

    .auth-hero-title span {{
      color: #2563eb !important;
    }}

    .auth-hero-subtitle {{
      max-width: 520px;
      margin: 0;
      color: #475569;
      font-size: 16px;
      line-height: 1.6;
      font-weight: 650;
    }}

    .auth-hero-bullets {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 4px;
    }}

    .auth-hero-bullet {{
      border: 1px solid rgba(37, 99, 235, 0.16);
      border-radius: 999px;
      padding: 8px 12px;
      background: rgba(255, 255, 255, 0.82);
      color: #274160;
      font-size: 13px;
      font-weight: 850;
      box-shadow: 0 12px 28px rgba(15, 23, 42, 0.06);
    }}

    .auth-proof-row {{
      position: relative;
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
    }}

    .auth-proof {{
      min-width: 0;
      border: 1px solid rgba(148, 163, 184, 0.22);
      border-radius: 18px;
      padding: 14px;
      background: rgba(255, 255, 255, 0.7);
      box-shadow: 0 12px 30px rgba(15, 23, 42, 0.06);
    }}

    .auth-proof strong {{
      display: block;
      color: #111827;
      font-size: 15px;
      line-height: 1.1;
    }}

    .auth-proof span {{
      display: block;
      margin-top: 5px;
      color: #64748b;
      font-size: 12px;
      font-weight: 750;
      line-height: 1.35;
    }}

    .auth-card {{
      display: flex;
      flex-direction: column;
      justify-content: center;
      width: 100%;
      min-width: 0;
      padding: clamp(34px, 4vw, 56px);
      background: #ffffff;
    }}

    .auth-form-card {{
      width: min(420px, 100%);
      margin: 0 auto;
    }}

    .auth-form-brand {{
      display: none;
    }}

    .auth-form-logo {{
      display: block;
      width: 190px;
      height: 72px;
      object-fit: contain;
    }}

    .auth-form-brand span {{
      display: none;
    }}

    .auth-title {{
      margin: 0;
      color: #111827 !important;
      font-size: clamp(40px, 4vw, 56px) !important;
      font-weight: 950 !important;
      line-height: 1 !important;
      letter-spacing: 0 !important;
    }}

    .auth-subtitle {{
      margin: 12px 0 26px;
      color: #475569;
      font-size: 16px;
      line-height: 1.55;
    }}

    .auth-form {{
      display: grid;
      gap: 16px;
    }}

    .auth-field {{
      display: grid;
      gap: 8px;
      color: #1f2937;
      font-size: 13px;
      font-weight: 850;
      letter-spacing: 0.01em;
    }}

    .auth-field input {{
      width: 100%;
      border: 1px solid rgba(71, 94, 132, 0.22);
      border-radius: 16px;
      padding: 15px 16px;
      background: #f8fbff;
      color: #111827;
      outline: none;
      font-size: 16px;
      font-weight: 750;
      transition:
        border-color 140ms ease,
        box-shadow 140ms ease,
        background 140ms ease;
    }}

    .auth-field input::placeholder {{
      color: #94a3b8;
    }}

    .auth-field input:focus {{
      border-color: rgba(37, 99, 235, 0.62);
      background: #ffffff;
      box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.12);
    }}

    .auth-field input:-webkit-autofill,
    .auth-field input:-webkit-autofill:hover,
    .auth-field input:-webkit-autofill:focus {{
      -webkit-text-fill-color: #101828;
      box-shadow: 0 0 0 1000px #f8fbff inset;
      caret-color: #101828;
    }}

    .auth-error {{
      display: none;
      border: 1px solid rgba(248, 113, 113, 0.35);
      border-radius: 14px;
      padding: 10px 12px;
      background: #fff1f2;
      color: #b91c1c;
      font-size: 13px;
      line-height: 1.45;
    }}

    .auth-error.is-visible {{
      display: block;
    }}

    .auth-submit {{
      margin-top: 6px;
      width: 100%;
      border: 0;
      border-radius: 16px;
      padding: 15px 16px;
      background: linear-gradient(135deg, #2563eb, #0891b2);
      color: #ffffff;
      cursor: pointer;
      font-size: 16px;
      font-weight: 900;
      box-shadow: 0 18px 34px rgba(37, 99, 235, 0.22);
      transition:
        transform 140ms ease,
        box-shadow 140ms ease,
        filter 140ms ease;
    }}

    .auth-submit:hover:not(:disabled) {{
      transform: translateY(-1px);
      filter: brightness(1.03);
      box-shadow: 0 22px 42px rgba(37, 99, 235, 0.3);
    }}

    .auth-submit:disabled {{
      opacity: 0.65;
      cursor: not-allowed;
    }}

    .auth-alt {{
      display: inline-flex;
      margin-top: 22px;
      color: #2563eb;
      text-decoration: none;
      font-size: 15px;
      font-weight: 800;
    }}

    .auth-alt:hover {{
      color: #0891b2;
    }}

    @media (max-width: 900px) {{
      .auth-shell {{
        grid-template-columns: 1fr;
        min-height: 0;
      }}

      .auth-hero {{
        padding: 24px;
      }}

      .auth-hero-copy {{
        margin: 0;
      }}

      .auth-proof-row {{
        grid-template-columns: 1fr;
      }}

      .auth-card {{
        border-left: 0;
        border-top: 1px solid rgba(71, 94, 132, 0.12);
      }}
    }}

    @media (max-width: 560px) {{
      body {{
        padding: 12px;
      }}

      .auth-shell {{
        border-radius: 24px;
      }}

      .auth-card,
      .auth-hero {{
        padding: 22px;
      }}

      .auth-brand-text {{
        font-size: 18px;
      }}
    }}
  </style>
</head>
<body>
  <main class="auth-shell">
    <section class="auth-hero" aria-label="ApplyLens AI product overview">
      <div class="auth-brand-lockup">
        <img class="auth-brand-logo" src="/static/media/app-logo.svg" alt="ApplyLens AI" />
        <span class="auth-brand-text">
          ApplyLens AI
          <small>Job intelligence</small>
        </span>
      </div>

      <div class="auth-hero-copy">
        <div class="auth-hero-kicker">AI job match workspace</div>
        <h2 class="auth-hero-title">Scan, tailor, and compare with <span>clarity.</span></h2>
        <p class="auth-hero-subtitle">
          Scrape live jobs, review resume fit, apply targeted edits, and keep every saved draft tied to the role it was built for.
        </p>
        <div class="auth-hero-bullets" aria-label="ApplyLens AI workflow">
          <span class="auth-hero-bullet">Live job scraper</span>
          <span class="auth-hero-bullet">AI resume scan</span>
          <span class="auth-hero-bullet">Diff-ready tailoring</span>
        </div>
      </div>

      <div class="auth-proof-row" aria-label="ApplyLens AI highlights">
        <div class="auth-proof">
          <strong>Scrape</strong>
          <span>Build your live job queue</span>
        </div>
        <div class="auth-proof">
          <strong>Scan</strong>
          <span>Find match gaps fast</span>
        </div>
        <div class="auth-proof">
          <strong>Tailor</strong>
          <span>Save job-ready drafts</span>
        </div>
      </div>
    </section>

    <section class="auth-card" aria-label="{escape(title)} form">
      <div class="auth-form-card">
        <div class="auth-form-brand">
          <img class="auth-form-logo" src="/static/media/app-logo.svg" alt="" />
          <span>ApplyLens AI</span>
        </div>
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
            <input id="emailInput" type="email" autocomplete="email" placeholder="you@example.com" required />
          </label>

          <label class="auth-field">
            <span>Password</span>
            <input id="passwordInput" type="password" autocomplete="{"new-password" if is_register else "current-password"}" placeholder="Enter your password" required />
          </label>

          <button id="authSubmitBtn" class="auth-submit" type="submit">
            {escape(submit_label)}
          </button>
        </form>

        <a class="auth-alt" href="{alternate_href}">
          {escape(alternate_label)}
        </a>
      </div>
    </section>
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

        if (payload.first_login) {{
          window.sessionStorage.setItem("applylens_first_run_prompt", "1");
          window.localStorage.setItem("applylens_new_user_empty_state", "1");
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


@router.get("/login")
def login_page(request: Request, next: str = "/"):
    next_path = _safe_next_path(next)

    if current_user_from_request(request):
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

    if current_user_from_request(request):
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
        touched = touch_auth_user_last_login_postgres_payload(
            user_id=str(user.get("user_id", "") or ""),
            ensure_schema=True,
        )

        response = JSONResponse(
            {
                "ok": True,
                "user": _public_user_payload(dict(touched.get("user", {}) or user)),
                "redirect_to": _safe_next_path(payload.next),
                "first_login": True,
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

        is_first_login = not _clean_text(user.get("last_login_at"))

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
                "first_login": is_first_login,
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
        except (Exception, SystemExit):
            pass

    response = JSONResponse({"ok": True, "redirect_to": "/login"})
    _clear_session_cookie(response)
    return response


@router.get("/auth/me")
def auth_me(request: Request):
    user = current_user_from_request(request)
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
        except (Exception, SystemExit):
            pass

    response = RedirectResponse(url="/login", status_code=303)
    _clear_session_cookie(response)
    return response
