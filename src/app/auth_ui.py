from __future__ import annotations

from html import escape
from typing import Any, Dict

from fastapi import APIRouter, Body, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel

from src.config.consts import (
    AUTH_FIRST_USER_ADMIN_ENABLED,
    AUTH_REGISTRATION_APPROVAL_REQUIRED,
    AUTH_REGISTRATION_ENABLED,
)

from src.auth.approval_email import (
    build_auth_registration_admin_email_payload,
    build_auth_registration_user_decision_email_payload,
    deliver_auth_approval_email_payload,
)
from src.auth.password import hash_password, validate_new_password, verify_password
from src.auth.runtime import current_user_from_request
from src.auth.session import (
    auth_cookie_name,
    auth_cookie_samesite,
    auth_cookie_secure,
    auth_session_idle_timeout_seconds,
    auth_session_inactivity_warning_seconds,
    auth_session_ttl_seconds,
    hash_session_token,
    new_auth_session_record,
)
from src.storage.auth.read_postgres import (
    get_auth_postgres_status_payload,
    get_pending_auth_registration_requests_postgres_payload,
    get_auth_user_by_email_postgres_payload,
    revoke_auth_session_postgres_payload,
    touch_auth_user_last_login_postgres_payload,
)
from src.storage.auth.store import (
    approve_auth_registration_request_postgres_payload,
    create_auth_registration_request_postgres_payload,
    create_auth_session_postgres_payload,
    create_auth_user_postgres_payload,
    mark_auth_registration_admin_notified_postgres_payload,
    mark_auth_registration_user_notified_postgres_payload,
    reject_auth_registration_request_postgres_payload,
)


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


class AuthRegistrationDecisionRequest(BaseModel):
    decision_note: str = ""


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


def _registration_approval_required() -> bool:
    return _env_bool(
        "JOB_STACK_AUTH_REGISTRATION_APPROVAL_REQUIRED",
        bool(AUTH_REGISTRATION_APPROVAL_REQUIRED),
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

    if _registration_approval_required():
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
    title = "Create your workspace" if is_register else "Welcome back"
    subtitle = (
        "Set up your private workspace to collect jobs, compare fit, and prepare review-ready tailoring suggestions."
        if is_register
        else "Continue your job pipeline, fit reviews, and human-controlled tailoring workflow."
    )
    submit_label = "Create account" if is_register else "Log in"
    alternate_href = f"/login?next={escape(next_path)}" if is_register else f"/register?next={escape(next_path)}"
    alternate_label = "Already have an account? Log in" if is_register else "Need an account? Register"

    display_name_field = ""
    if is_register:
        display_name_field = """
        <label class="auth-field">
          <span>Name</span>
          <input id="displayNameInput" type="text" autocomplete="name" placeholder="John Doe" />
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
  <link rel="stylesheet" href="/static/app_redesign.css?v=phase133h_s1" />
  <style>
    html,
    body {{
      width: 100%;
      height: 100%;
      margin: 0;
      overflow: hidden;
    }}

    *,
    *::before,
    *::after {{
      box-sizing: border-box;
    }}

    body {{
      min-height: 0;
      margin: 0;
      padding: 0;
      background: #dbeafe;
      color: #0f172a;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      overflow-x: hidden;
    }}

    .auth-shell {{
      position: relative;
      display: grid;
      grid-template-columns: minmax(0, 60%) minmax(420px, 40%);
      width: 100%;
      height: 100dvh;
      min-height: 0;
      margin: 0;
      border: 0;
      border-radius: 0;
      background-color: #bfd1e7;
      background-image: url("/static/media/Login_page_BG_img.jpg");
      background-size: cover;
      background-position: center center;
      background-attachment: fixed;
      box-shadow: none;
      overflow: hidden;
    }}

    .auth-shell::before {{
      content: "";
      position: absolute;
      inset: 0;
      z-index: 0;
      background:
        linear-gradient(90deg, rgba(248, 251, 255, 0.5) 0%, rgba(246, 250, 255, 0.34) 27%, rgba(235, 244, 255, 0.08) 49%, transparent 68%),
        linear-gradient(180deg, rgba(255, 255, 255, 0.02), transparent 56%, rgba(7, 27, 61, 0.2));
      pointer-events: none;
    }}

    .auth-hero {{
      position: relative;
      display: grid;
      grid-template-rows: auto minmax(0, 1fr) auto;
      row-gap: clamp(14px, 2vh, 24px);
      min-width: 0;
      height: 100%;
      min-height: 0;
      padding: clamp(58px, 7.5vh, 82px) clamp(84px, 6.2vw, 120px) clamp(46px, 5.5vh, 66px);
      padding-right: clamp(24px, 3vw, 58px);
      background: transparent;
      border-right: 1px solid rgba(255, 255, 255, 0.24);
      overflow: hidden;
      z-index: 1;
    }}

    .auth-scene {{
      position: absolute;
      inset: 0;
      z-index: 0;
      overflow: hidden;
      pointer-events: none;
    }}

    .auth-scene-haze {{
      position: absolute;
      inset: auto 0 18%;
      height: 18%;
      background: linear-gradient(180deg, transparent, rgba(219, 234, 254, 0.1), transparent);
      filter: blur(22px);
    }}

    .auth-scene-wave {{
      position: absolute;
      left: 4%;
      right: 6%;
      bottom: 6%;
      height: 18%;
      border-top: 2px solid rgba(147, 197, 253, 0.48);
      border-radius: 50%;
      transform: rotate(-4deg) skewX(-18deg);
      box-shadow: 0 -18px 42px rgba(96, 165, 250, 0.2);
      opacity: 0.42;
    }}

    .auth-brand-lockup {{
      position: relative;
      z-index: 1;
      grid-column: 1 / -1;
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
      width: clamp(84px, 5.8vw, 98px);
      height: clamp(84px, 5.8vw, 98px);
      object-fit: contain;
      object-position: center;
      clip-path: inset(0 0 40% 0);
      filter: drop-shadow(0 12px 24px rgba(15, 23, 42, 0.14));
      transform: translateY(3px) scale(1.78);
      transform-origin: center;
      margin-left: 4px;
      margin-right: -6px;
    }}

    .auth-brand-text {{
      display: block;
      margin-left: 0;
      color: #07152f;
      font-size: clamp(27px, 2.1vw, 34px);
      font-weight: 900;
      line-height: 1;
      transform: translateY(-1px);
    }}

    .auth-brand-text small {{
      display: none;
    }}

    .auth-brand-text em,
    .auth-form-brand em {{
      color: #2bb673;
      font-style: normal;
    }}

    .auth-hero-copy {{
      position: relative;
      z-index: 2;
      grid-row: 2;
      align-self: start;
      display: grid;
      gap: clamp(11px, 1.4vh, 15px);
      width: min(570px, 64%);
      max-width: 570px;
      margin-top: 0;
    }}

    .auth-hero-kicker {{
      width: fit-content;
      border: 1px solid rgba(37, 99, 235, 0.16);
      border-radius: 999px;
      padding: 7px 12px;
      background: rgba(255, 255, 255, 0.7);
      color: #2563eb;
      font-size: 12px;
      font-weight: 900;
      letter-spacing: 0.11em;
      text-transform: uppercase;
      box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
    }}

    .auth-hero-title {{
      margin: 0;
      max-width: 570px;
      color: #07152f !important;
      font-size: clamp(44px, 3vw, 56px) !important;
      font-weight: 950 !important;
      line-height: 1.02 !important;
      letter-spacing: 0 !important;
    }}

    .auth-hero-title span {{
      color: #2563eb !important;
    }}

    .auth-hero-subtitle {{
      max-width: 500px;
      margin: 0;
      color: #1e293b;
      font-size: clamp(15px, 0.95vw, 17px);
      line-height: 1.5;
      font-weight: 450 !important;
    }}

    .auth-hero-bullets {{
      position: relative;
      z-index: 2;
      display: flex;
      flex-wrap: nowrap;
      gap: 6px;
      width: max-content;
      max-width: none;
      margin-top: 2px;
    }}

    .auth-workflow-artwork {{
      position: absolute;
      top: clamp(85px, 9vh, 105px);
      right: clamp(70px, 5.5vw, 105px);
      width: auto;
      height: min(68vh, 650px);
      object-fit: contain;
      z-index: 1;
      pointer-events: none;
      user-select: none;
    }}

    .auth-safety-line {{
      position: relative;
      z-index: 1;
      grid-column: 1;
      grid-row: 3;
      align-self: end;
      margin: 0;
      max-width: 540px;
      color: #f8fafc;
      font-size: 12px;
      font-weight: 750;
      line-height: 1.5;
      padding-left: 38px;
    }}

    .auth-safety-line::before {{
      content: "✓";
      position: absolute;
      left: 0;
      top: 50%;
      display: grid;
      place-items: center;
      width: 27px;
      height: 27px;
      border-radius: 8px;
      background: #2bb673;
      color: #ffffff;
      font-size: 17px;
      font-weight: 900;
      transform: translateY(-50%);
      box-shadow: 0 8px 20px rgba(43, 182, 115, 0.28);
    }}

    .auth-hero-bullet {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      border: 1px solid rgba(255, 255, 255, 0.70);
      border-radius: 999px;
      padding: 7px 9px;
      background: rgba(255, 255, 255, 0.76);
      color: #1e293b;
      font-size: 11px;
      font-weight: 750;
      line-height: 1;
      white-space: nowrap;
      box-shadow: 0 8px 22px rgba(15, 23, 42, 0.07), inset 0 1px rgba(255, 255, 255, 0.64);
      backdrop-filter: blur(15px) saturate(1.06);
      -webkit-backdrop-filter: blur(15px) saturate(1.06);
    }}

    .auth-hero-bullet img {{
      display: block;
      width: 15px;
      height: 15px;
      object-fit: contain;
      opacity: 1;
      filter: brightness(0) saturate(100%) invert(37%) sepia(92%) saturate(3292%) hue-rotate(216deg) brightness(98%) contrast(91%);
    }}

    .auth-hero-bullet:nth-child(2) img {{
      filter: brightness(0) saturate(100%) invert(47%) sepia(73%) saturate(1217%) hue-rotate(91deg) brightness(92%) contrast(93%);
    }}

    .auth-hero-bullet:nth-child(3) img {{
      filter: brightness(0) saturate(100%) invert(34%) sepia(91%) saturate(3095%) hue-rotate(252deg) brightness(93%) contrast(100%);
    }}

    .auth-hero-bullet:nth-child(4) img {{
      filter: brightness(0) saturate(100%) invert(49%) sepia(78%) saturate(2264%) hue-rotate(151deg) brightness(91%) contrast(94%);
    }}

    .auth-proof-row {{
      display: none;
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
      height: 100%;
      min-height: 0;
      padding: clamp(22px, 4vh, 44px) clamp(28px, 3.5vw, 58px);
      background: transparent;
      z-index: 1;
    }}

    .auth-form-card {{
      width: min(600px, 100%);
      height: min(76dvh, 820px);
      min-height: 620px;
      margin: 0 auto;
      padding: clamp(28px, 3.8vh, 42px) clamp(34px, 3.2vw, 50px);
      border: 1px solid rgba(255, 255, 255, 0.7);
      border-radius: 28px;
      background: rgba(249, 251, 255, 0.78);
      box-shadow: 0 28px 80px rgba(12, 38, 82, 0.22);
      backdrop-filter: blur(24px) saturate(1.25);
      -webkit-backdrop-filter: blur(24px) saturate(1.25);
      display: flex;
      flex-direction: column;
      justify-content: center;
    }}

    .auth-form-brand {{
      display: flex;
      align-items: center;
      justify-content: center;
      margin-bottom: 12px;
    }}

    .auth-form-logo {{
      display: block;
      width: 60px;
      height: 60px;
      object-fit: contain;
      clip-path: inset(0 0 40% 0);
      transform: translateY(2px) scale(1.8);
      transform-origin: center;
      margin-right: -8px;
    }}

    .auth-form-brand span {{
      display: block;
      margin-left: 0;
      color: #07152f;
      font-size: 23px;
      font-weight: 900;
      line-height: 1;
      transform: translateY(-1px);
    }}

    .auth-title {{
      margin: 0;
      text-align: center;
      color: #111827 !important;
      font-size: clamp(30px, 2.2vw, 38px) !important;
      font-weight: 950 !important;
      line-height: 1 !important;
      letter-spacing: 0 !important;
    }}

    .auth-subtitle {{
      max-width: 390px;
      margin: 10px auto 24px;
      text-align: center;
      color: #475569;
      font-size: 14px;
      line-height: 1.5;
    }}

    .auth-form {{
      display: grid;
      gap: 14px;
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
      border-radius: 12px;
      padding: 14px 16px;
      background: #f8fbff;
      color: #111827;
      outline: none;
      font-size: 15px;
      font-weight: 450;
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


    .auth-password-control {{
      position: relative;
      display: flex;
      align-items: center;
    }}

    .auth-password-control input {{
      padding-right: 58px;
    }}

    html body .auth-shell #passwordToggleBtn.auth-password-toggle {{
      position: absolute;
      right: 6px;
      top: 50%;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 40px;
      min-width: 40px;
      height: 40px;
      min-height: 40px;
      margin: 0;
      padding: 0 !important;
      border: 0 !important;
      border-radius: 50%;
      background: transparent !important;
      background-color: transparent !important;
      background-image: none !important;
      box-shadow: none !important;
      color: #64748b;
      cursor: pointer;
      transform: translateY(-50%) !important;
      appearance: none;
      -webkit-appearance: none;
      transition: background 140ms ease, color 140ms ease, opacity 140ms ease;
    }}

    html body .auth-shell #passwordToggleBtn.auth-password-toggle:hover,
    html body .auth-shell #passwordToggleBtn.auth-password-toggle:active,
    html body .auth-shell #passwordToggleBtn.auth-password-toggle.is-visible {{
      border: 0 !important;
      background: rgba(99, 102, 241, 0.08) !important;
      color: #1d4ed8;
      transform: translateY(-50%) !important;
      box-shadow: none !important;
    }}

    html body .auth-shell #passwordToggleBtn.auth-password-toggle:focus-visible {{
      border: 0 !important;
      background: rgba(99, 102, 241, 0.08) !important;
      box-shadow: none !important;
      outline: 2px solid rgba(99, 102, 241, 0.36) !important;
      outline-offset: 1px;
    }}

    .auth-password-toggle img {{
      display: block;
      width: 21px;
      height: 21px;
      opacity: 0.68;
      pointer-events: none;
    }}

    .auth-password-toggle:hover img,
    .auth-password-toggle:focus-visible img,
    .auth-password-toggle.is-visible img {{
      opacity: 0.92;
    }}

    html[data-theme="dark"] body .auth-shell #passwordToggleBtn.auth-password-toggle {{
      border: 0 !important;
      background: transparent !important;
      box-shadow: none !important;
      color: #e2e8f0;
    }}

    html[data-theme="dark"] body .auth-shell #passwordToggleBtn.auth-password-toggle:hover,
    html[data-theme="dark"] body .auth-shell #passwordToggleBtn.auth-password-toggle:focus-visible,
    html[data-theme="dark"] body .auth-shell #passwordToggleBtn.auth-password-toggle:active,
    html[data-theme="dark"] body .auth-shell #passwordToggleBtn.auth-password-toggle.is-visible {{
      border: 0 !important;
      background: rgba(96, 165, 250, 0.1) !important;
      color: #bfdbfe;
      box-shadow: none !important;
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

    .auth-error.is-success {{
      border-color: rgba(34, 197, 94, 0.35);
      background: #f0fdf4;
      color: #166534;
    }}

    .auth-submit {{
      margin-top: 6px;
      width: 100%;
      border: 0;
      border-radius: 12px;
      padding: 14px 16px;
      background: linear-gradient(135deg, #2563eb, #7c3aed);
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
      display: flex;
      justify-content: center;
      margin-top: 20px;
      color: #2563eb;
      text-decoration: none;
      font-size: 14px;
      font-weight: 800;
    }}

    .auth-alt:hover {{
      color: #0891b2;
    }}

    .auth-control-note {{
      margin: 28px 0 0;
      padding-top: 16px;
      border-top: 1px solid rgba(148, 163, 184, 0.2);
      color: #64748b;
      font-size: 12px;
      line-height: 1.5;
      text-align: center;
    }}

    @media (max-width: 900px) {{
      .auth-shell {{
        grid-template-columns: minmax(0, 48%) minmax(380px, 52%);
        min-height: 0;
      }}

      .auth-hero {{
        grid-template-columns: 1fr;
        padding: 24px;
      }}

      .auth-hero-copy {{
        width: 100%;
        max-width: 100%;
        margin: 0;
      }}

      .auth-workflow-artwork {{
        display: none;
      }}

      .auth-card {{
        border-left: 0;
        border-top: 1px solid rgba(71, 94, 132, 0.12);
      }}
    }}

    @media (min-width: 561px) and (max-height: 920px) {{
      .auth-brand-logo {{
        width: 82px;
        height: 82px;
      }}

      .auth-hero-copy {{
        gap: 12px;
      }}

      .auth-hero-title {{
        font-size: clamp(44px, 3vw, 54px) !important;
      }}

      .auth-form-brand {{
        margin-bottom: 10px;
      }}

      .auth-form-logo {{
        height: 50px;
      }}

      .auth-subtitle {{
        margin-bottom: 16px;
      }}

      .auth-form {{
        gap: 12px;
      }}

      .auth-field input {{
        padding-block: 12px;
      }}

      .auth-control-note {{
        margin-top: 24px;
        padding-top: 11px;
      }}
    }}

    @media (max-width: 560px) {{
      html,
      body {{
        height: auto;
        min-height: 100%;
        overflow-x: hidden;
        overflow-y: auto;
      }}

      body {{
        padding: 12px;
      }}

      .auth-shell {{
        grid-template-columns: 1fr;
        height: auto;
        min-height: 100dvh;
        overflow: visible;
      }}

      .auth-card,
      .auth-hero {{
        padding: 22px;
      }}

      .auth-hero {{
        min-height: auto;
        gap: 14px;
        padding-bottom: 28px;
      }}

      .auth-card {{
        min-height: auto;
        padding-top: 0;
        padding-bottom: 28px;
      }}

      .auth-form-card {{
        height: auto;
        min-height: 0;
      }}

      .auth-scene-wave,
      .auth-workflow-artwork {{
        display: none;
      }}

      .auth-brand-logo {{
        width: 70px;
        height: 70px;
      }}

      .auth-hero-title {{
        font-size: clamp(34px, 11vw, 46px) !important;
      }}

      .auth-brand-text {{
        font-size: 18px;
      }}
    }}

    @media (prefers-reduced-motion: reduce) {{
      .auth-shell *,
      .auth-shell *::before,
      .auth-shell *::after {{
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
      }}
    }}
  </style>
</head>
<body>
  <main class="auth-shell">
    <section class="auth-hero" aria-label="ApplyLens AI product overview">
      <div class="auth-scene" aria-hidden="true">
        <div class="auth-scene-haze"></div>
        <div class="auth-scene-wave"></div>
      </div>
      <div class="auth-brand-lockup">
        <img class="auth-brand-logo" src="/static/media/app-logo.svg" alt="ApplyLens AI" />
        <span class="auth-brand-text">
          ApplyLens <em>AI</em>
          <small>Job intelligence</small>
        </span>
      </div>

      <div class="auth-hero-copy">
        <div class="auth-hero-kicker">Human-controlled AI workflow</div>
        <h2 class="auth-hero-title">Turn live jobs into<br /><span>review-ready</span><br />applications.</h2>
        <p class="auth-hero-subtitle">
          Scrape roles, score fit, review policy-driven AI notes, generate tailoring suggestions, and keep every final decision manual.
        </p>
        <div class="auth-hero-bullets" aria-label="ApplyLens AI workflow">
          <span class="auth-hero-bullet"><img src="/static/media/auth_hero_icons/collect_jobs.svg" alt="" aria-hidden="true" />Live job pipeline</span>
          <span class="auth-hero-bullet"><img src="/static/media/auth_hero_icons/score_fit.svg" alt="" aria-hidden="true" />Hybrid fit scoring</span>
          <span class="auth-hero-bullet"><img src="/static/media/auth_hero_icons/review_ai_notes.svg" alt="" aria-hidden="true" />Policy AI review</span>
          <span class="auth-hero-bullet"><img src="/static/media/auth_hero_icons/tailor_safely.svg" alt="" aria-hidden="true" />Tailoring workspace</span>
        </div>
      </div>

      <img
        class="auth-workflow-artwork"
        src="/static/media/auth_workflow_hero.svg"
        alt=""
        aria-hidden="true"
      />
      <p class="auth-safety-line">You stay in control. No auto-apply. No recruiter messages.<br />Your workspace prepares evidence and suggestions.</p>
    </section>

    <section class="auth-card" aria-label="{escape(title)} form">
      <div class="auth-form-card">
        <div class="auth-form-brand">
          <img class="auth-form-logo" src="/static/media/app-logo.svg" alt="" />
          <span>ApplyLens <em>AI</em></span>
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
            <div class="auth-password-control">
              <input id="passwordInput" type="password" autocomplete="{"new-password" if is_register else "current-password"}" placeholder="Enter your password" required />
              <button
                id="passwordToggleBtn"
                class="auth-password-toggle"
                type="button"
                aria-label="Show password"
                aria-pressed="false"
                title="Show password"
              >
                <img id="passwordToggleIcon" src="/static/media/eye-closed.svg" alt="" aria-hidden="true" />
              </button>
            </div>
          </label>

          <button id="authSubmitBtn" class="auth-submit" type="submit">
            {escape(submit_label)}
          </button>
        </form>

        <a class="auth-alt" href="{alternate_href}">
          {escape(alternate_label)}
        </a>
        <p class="auth-control-note">Secure and private. Built for your job search.</p>
      </div>
    </section>
  </main>

  <script>
    const form = document.getElementById("authForm");
    const errorEl = document.getElementById("authError");
    const submitBtn = document.getElementById("authSubmitBtn");
    const passwordInput = document.getElementById("passwordInput");
    const passwordToggleBtn = document.getElementById("passwordToggleBtn");
    const passwordToggleIcon = document.getElementById("passwordToggleIcon");
    const passwordVisibleIconPath = "/static/media/eye.svg";
    const passwordHiddenIconPath = "/static/media/eye-closed.svg";

    function showError(message) {{
      errorEl.textContent = message || "Request failed.";
      errorEl.classList.remove("is-success");
      errorEl.classList.add("is-visible");
    }}

    function showStatus(message) {{
      errorEl.textContent = message || "Request submitted.";
      errorEl.classList.add("is-success");
      errorEl.classList.add("is-visible");
    }}

    if (passwordInput && passwordToggleBtn) {{
      passwordToggleBtn.addEventListener("click", () => {{
        const shouldShow = passwordInput.type === "password";
        passwordInput.type = shouldShow ? "text" : "password";
        passwordToggleBtn.classList.toggle("is-visible", shouldShow);
        passwordToggleBtn.setAttribute("aria-pressed", shouldShow ? "true" : "false");
        passwordToggleBtn.setAttribute("aria-label", shouldShow ? "Hide password" : "Show password");
        passwordToggleBtn.title = shouldShow ? "Hide password" : "Show password";
        if (passwordToggleIcon) {{
          passwordToggleIcon.src = shouldShow ? passwordVisibleIconPath : passwordHiddenIconPath;
        }}
        passwordInput.focus();
      }});
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

        if (payload.pending_approval) {{
          showStatus(payload.message || "Registration request submitted. You will receive an email after admin review.");
          form.reset();
          return;
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


def _require_admin_user(request: Request) -> Dict[str, Any]:
    user = current_user_from_request(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required.")

    user_payload = dict(user)
    if not bool(user_payload.get("is_admin", False)) and _clean_text(user_payload.get("access_level")) != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")

    return user_payload


def _admin_registration_requests_page_html(*, selected_request_id: str = "") -> str:
    selected = escape(_clean_text(selected_request_id))
    return f"""
<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Registration Requests · ApplyLens AI</title>
  <link rel="stylesheet" href="/static/vendor/tabler/tabler.min.css" />
  <link rel="stylesheet" href="/static/styles.css?v=ui_redesign_v17" />
  <link rel="stylesheet" href="/static/app_redesign.css?v=phase133h_s1" />
  <style>
    body {{
      min-height: 100vh;
      margin: 0;
      background: #f6f9ff;
      color: #111827;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}

    .admin-shell {{
      width: min(1120px, calc(100% - 32px));
      margin: 32px auto;
      display: grid;
      gap: 18px;
    }}

    .admin-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 14px;
      border: 1px solid rgba(148, 163, 184, 0.28);
      border-radius: 24px;
      padding: 20px;
      background: #ffffff;
      box-shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
    }}

    .admin-header h1 {{
      margin: 0;
      font-size: 26px;
      font-weight: 950;
      color: #111827;
    }}

    .admin-header p {{
      margin: 6px 0 0;
      color: #64748b;
      font-size: 14px;
      font-weight: 650;
    }}

    .admin-link {{
      color: #2563eb;
      font-weight: 850;
      text-decoration: none;
    }}

    .request-list {{
      display: grid;
      gap: 14px;
    }}

    .request-card {{
      border: 1px solid rgba(148, 163, 184, 0.28);
      border-radius: 22px;
      padding: 18px;
      background: #ffffff;
      box-shadow: 0 14px 34px rgba(15, 23, 42, 0.07);
    }}

    .request-card.is-selected {{
      border-color: rgba(37, 99, 235, 0.55);
      box-shadow: 0 18px 44px rgba(37, 99, 235, 0.14);
    }}

    .request-main {{
      display: grid;
      gap: 8px;
    }}

    .request-title {{
      margin: 0;
      color: #111827;
      font-size: 18px;
      font-weight: 950;
    }}

    .request-meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      color: #475569;
      font-size: 13px;
      font-weight: 700;
    }}

    .request-pill {{
      border: 1px solid rgba(148, 163, 184, 0.28);
      border-radius: 999px;
      padding: 5px 9px;
      background: #f8fafc;
    }}

    .request-note {{
      width: 100%;
      min-height: 72px;
      margin-top: 14px;
      border: 1px solid rgba(148, 163, 184, 0.35);
      border-radius: 14px;
      padding: 10px 12px;
      font: inherit;
      resize: vertical;
      outline: none;
    }}

    .request-actions {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 12px;
    }}

    .request-button {{
      border: 0;
      border-radius: 13px;
      padding: 10px 14px;
      cursor: pointer;
      color: #ffffff;
      font-weight: 900;
    }}

    .request-button.approve {{
      background: #16a34a;
    }}

    .request-button.reject {{
      background: #dc2626;
    }}

    .request-button:disabled {{
      opacity: 0.6;
      cursor: not-allowed;
    }}

    .empty-state,
    .status-box {{
      border: 1px solid rgba(148, 163, 184, 0.28);
      border-radius: 20px;
      padding: 18px;
      background: #ffffff;
      color: #475569;
      font-weight: 750;
    }}

    .status-box.is-error {{
      border-color: rgba(248, 113, 113, 0.35);
      background: #fff1f2;
      color: #b91c1c;
    }}

    .status-box.is-success {{
      border-color: rgba(34, 197, 94, 0.35);
      background: #f0fdf4;
      color: #166534;
    }}
  </style>
</head>
<body>
  <main class="admin-shell">
    <section class="admin-header">
      <div>
        <h1>Registration Requests</h1>
        <p>Approve or reject pending ApplyLens account requests.</p>
      </div>
      <a class="admin-link" href="/">Back to app</a>
    </section>

    <section id="statusBox" class="status-box" hidden></section>
    <section id="requestList" class="request-list" data-selected-request-id="{selected}"></section>
  </main>

  <script>
    const listEl = document.getElementById("requestList");
    const statusEl = document.getElementById("statusBox");
    const selectedRequestId = listEl.dataset.selectedRequestId || "";

    function setStatus(message, kind = "") {{
      statusEl.textContent = message || "";
      statusEl.hidden = !message;
      statusEl.classList.toggle("is-error", kind === "error");
      statusEl.classList.toggle("is-success", kind === "success");
    }}

    function escapeHtml(value) {{
      return String(value || "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }}

    function renderRequests(requests) {{
      if (!requests.length) {{
        listEl.innerHTML = '<div class="empty-state">No pending registration requests.</div>';
        return;
      }}

      listEl.innerHTML = requests.map((request) => {{
        const requestId = escapeHtml(request.request_id);
        const isSelected = selectedRequestId && selectedRequestId === request.request_id;
        return `
          <article class="request-card ${{isSelected ? "is-selected" : ""}}" data-request-id="${{requestId}}">
            <div class="request-main">
              <h2 class="request-title">${{escapeHtml(request.display_name || request.email)}}</h2>
              <div class="request-meta">
                <span class="request-pill">${{escapeHtml(request.email)}}</span>
                <span class="request-pill">Status: ${{escapeHtml(request.status)}}</span>
                <span class="request-pill">Requested: ${{escapeHtml(request.requested_at)}}</span>
                <span class="request-pill">IP: ${{escapeHtml(request.request_ip_address)}}</span>
              </div>
              <div class="request-meta">
                <span>User agent: ${{escapeHtml(request.request_user_agent)}}</span>
              </div>
            </div>
            <textarea class="request-note" placeholder="Optional decision note"></textarea>
            <div class="request-actions">
              <button class="request-button approve" type="button" data-action="approve">Approve</button>
              <button class="request-button reject" type="button" data-action="reject">Reject</button>
            </div>
          </article>
        `;
      }}).join("");
    }}

    async function loadRequests() {{
      setStatus("Loading pending requests...");
      const response = await fetch("/admin/registration-requests/data");
      const payload = await response.json().catch(() => ({{}}));
      if (!response.ok || !payload.ok) {{
        throw new Error(payload.detail || "Failed to load registration requests.");
      }}
      renderRequests(payload.requests || []);
      setStatus("");
    }}

    async function decide(requestId, action, note, button) {{
      button.disabled = true;
      setStatus(`${{action === "approve" ? "Approving" : "Rejecting"}} request...`);

      try {{
        const response = await fetch(`/admin/registration-requests/${{encodeURIComponent(requestId)}}/${{action}}`, {{
          method: "POST",
          headers: {{"Content-Type": "application/json"}},
          body: JSON.stringify({{decision_note: note || ""}}),
        }});

        const payload = await response.json().catch(() => ({{}}));
        if (!response.ok || !payload.ok) {{
          throw new Error(payload.detail || "Request failed.");
        }}

        setStatus(payload.message || "Decision saved.", "success");
        await loadRequests();
      }} catch (error) {{
        setStatus(error instanceof Error ? error.message : "Request failed.", "error");
      }} finally {{
        button.disabled = false;
      }}
    }}

    listEl.addEventListener("click", (event) => {{
      const button = event.target.closest("button[data-action]");
      if (!button) {{
        return;
      }}

      const card = button.closest(".request-card");
      const requestId = card?.dataset?.requestId || "";
      const note = card?.querySelector(".request-note")?.value || "";
      const action = button.dataset.action;

      if (!requestId || !action) {{
        setStatus("Missing request id or action.", "error");
        return;
      }}

      decide(requestId, action, note, button);
    }});

    loadRequests().catch((error) => {{
      setStatus(error instanceof Error ? error.message : "Failed to load registration requests.", "error");
    }});
  </script>
</body>
</html>
""".strip()


@router.get("/admin/registration-requests")
def admin_registration_requests_page(request: Request, request_id: str = ""):
    try:
        _require_admin_user(request)
    except HTTPException as exc:
        if exc.status_code == 401:
            return RedirectResponse(url="/login?next=/admin/registration-requests", status_code=303)
        raise

    return HTMLResponse(
        _admin_registration_requests_page_html(
            selected_request_id=request_id,
        )
    )


@router.get("/admin/registration-requests/data")
def admin_registration_requests_data(request: Request, limit: int = 50):
    _require_admin_user(request)
    payload = get_pending_auth_registration_requests_postgres_payload(
        limit=limit,
        ensure_schema=True,
    )
    return JSONResponse(
        {
            "ok": True,
            "request_count": int(payload.get("request_count", 0) or 0),
            "requests": list(payload.get("requests", []) or []),
        }
    )


@router.post("/admin/registration-requests/{request_id}/approve")
def approve_registration_request(
    request: Request,
    request_id: str,
    payload: AuthRegistrationDecisionRequest = Body(...),
):
    admin_user = _require_admin_user(request)
    result = approve_auth_registration_request_postgres_payload(
        request_id=request_id,
        decided_by_user_id=_clean_text(admin_user.get("user_id")),
        decision_note=payload.decision_note,
        ensure_schema=True,
    )

    if not result.get("request_found", False):
        raise HTTPException(status_code=404, detail="Pending registration request not found.")

    if result.get("existing_user", False):
        raise HTTPException(status_code=409, detail="An account already exists for this email.")

    if not result.get("approved", False):
        raise HTTPException(status_code=409, detail="Registration request could not be approved.")

    request_payload = dict(result.get("request", {}) or {})
    user_email_payload = build_auth_registration_user_decision_email_payload(
        request_payload,
        approved=True,
    )
    delivery = deliver_auth_approval_email_payload(user_email_payload)

    if delivery.get("ok", False):
        mark_auth_registration_user_notified_postgres_payload(
            request_id=str(request_payload.get("request_id", "") or ""),
            ensure_schema=True,
        )

    return JSONResponse(
        {
            "ok": True,
            "approved": True,
            "message": "Registration request approved. The user has been notified.",
            "request": request_payload,
            "user": dict(result.get("user", {}) or {}),
        }
    )


@router.post("/admin/registration-requests/{request_id}/reject")
def reject_registration_request(
    request: Request,
    request_id: str,
    payload: AuthRegistrationDecisionRequest = Body(...),
):
    admin_user = _require_admin_user(request)
    result = reject_auth_registration_request_postgres_payload(
        request_id=request_id,
        decided_by_user_id=_clean_text(admin_user.get("user_id")),
        decision_note=payload.decision_note,
        ensure_schema=True,
    )

    if not result.get("rejected", False):
        raise HTTPException(status_code=404, detail="Pending registration request not found.")

    request_payload = dict(result.get("request", {}) or {})
    user_email_payload = build_auth_registration_user_decision_email_payload(
        request_payload,
        approved=False,
    )
    delivery = deliver_auth_approval_email_payload(user_email_payload)

    if delivery.get("ok", False):
        mark_auth_registration_user_notified_postgres_payload(
            request_id=str(request_payload.get("request_id", "") or ""),
            ensure_schema=True,
        )

    return JSONResponse(
        {
            "ok": True,
            "rejected": True,
            "message": "Registration request rejected. The user has been notified.",
            "request": request_payload,
        }
    )


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
        should_create_direct_user = make_admin or (
            _registration_enabled() and not _registration_approval_required()
        )

        if should_create_direct_user:
            created = create_auth_user_postgres_payload(
                record={
                    "email": payload.email,
                    "password_hash": hash_password(payload.password),
                    "display_name": payload.display_name,
                    "access_level": "admin" if make_admin else "user",
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

        existing_user = get_auth_user_by_email_postgres_payload(
            email=payload.email,
            ensure_schema=True,
        )
        if dict(existing_user.get("user", {}) or {}):
            raise HTTPException(
                status_code=409,
                detail="An account already exists for this email.",
            )

        created_request = create_auth_registration_request_postgres_payload(
            record={
                "email": payload.email,
                "password_hash": hash_password(payload.password),
                "display_name": payload.display_name,
                "status": "pending",
                "request_user_agent": _clean_text(request.headers.get("user-agent")),
                "request_ip_address": _request_ip_address(request),
            },
            ensure_schema=True,
        )

        if created_request.get("existing_user", False):
            raise HTTPException(
                status_code=409,
                detail="An account already exists for this email.",
            )

        request_payload = dict(created_request.get("request", {}) or {})

        if not created_request.get("inserted", False):
            if created_request.get("pending_exists", False):
                return JSONResponse(
                    {
                        "ok": True,
                        "pending_approval": True,
                        "message": "A registration request is already pending for this email. You will receive an email after admin review.",
                    }
                )

            raise HTTPException(
                status_code=409,
                detail="Could not create registration request.",
            )

        admin_email_payload = build_auth_registration_admin_email_payload(request_payload)
        delivery = deliver_auth_approval_email_payload(admin_email_payload)

        if delivery.get("ok", False):
            mark_auth_registration_admin_notified_postgres_payload(
                request_id=str(request_payload.get("request_id", "") or ""),
                ensure_schema=True,
            )

        return JSONResponse(
            {
                "ok": True,
                "pending_approval": True,
                "message": "Registration request submitted. You will receive an email after admin review.",
            }
        )

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


@router.get("/auth/session-config")
def auth_session_config():
    idle_timeout_seconds = auth_session_idle_timeout_seconds()
    warning_seconds = min(
        auth_session_inactivity_warning_seconds(),
        max(1, idle_timeout_seconds - 1),
    )
    return {
        "ok": True,
        "idle_timeout_seconds": idle_timeout_seconds,
        "warning_seconds": warning_seconds,
    }


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
