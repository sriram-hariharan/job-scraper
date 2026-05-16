from __future__ import annotations

import json
import os
import smtplib
import ssl
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Any, Dict, List

from src.storage.auth_email_artifacts_store import upsert_auth_email_artifact


DEFAULT_AUTH_APPROVAL_EMAIL_OUTBOX_DIR = Path("postgres_artifacts/auth_email/auth_approval_email_outbox")
DEFAULT_AUTH_APPROVAL_EMAIL_DELIVERY_DIR = Path("postgres_artifacts/auth_email/auth_approval_email_delivery")

AUTH_APPROVAL_EMAIL_MODES = {"outbox_only", "dry_run", "smtp"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _safe_filename_token(value: Any) -> str:
    text = _clean_text(value).lower()
    safe_chars: List[str] = []
    for char in text:
        if char.isalnum():
            safe_chars.append(char)
        elif char in {"-", "_", ".", "@"}:
            safe_chars.append(char)
        else:
            safe_chars.append("_")

    return "".join(safe_chars).strip("._") or "unknown"


def _normalize_mode(value: Any) -> str:
    mode = _clean_text(value).lower() or "outbox_only"
    if mode not in AUTH_APPROVAL_EMAIL_MODES:
        allowed = ", ".join(sorted(AUTH_APPROVAL_EMAIL_MODES))
        raise ValueError(f"Unsupported auth approval email mode={mode!r}. Allowed: {allowed}")
    return mode


def _normalize_bool(value: Any, *, default: bool) -> bool:
    raw = _clean_text(value).lower()
    if not raw:
        return default
    if raw in {"1", "true", "yes", "y", "on"}:
        return True
    if raw in {"0", "false", "no", "n", "off"}:
        return False
    raise ValueError(f"Unsupported boolean value={value!r}")


def _safe_int(value: Any, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed


def _parse_recipient_list(value: Any) -> List[str]:
    raw = _clean_text(value)
    if not raw:
        return []

    recipients: List[str] = []
    for part in raw.split(","):
        email = _clean_text(part)
        if email and email not in recipients:
            recipients.append(email)

    return recipients


def _admin_emails_from_env() -> List[str]:
    return _parse_recipient_list(os.getenv("JOB_STACK_AUTH_APPROVAL_ADMIN_EMAILS", ""))


def _from_email_from_env() -> str:
    return (
        _clean_text(os.getenv("JOB_STACK_AUTH_APPROVAL_EMAIL_FROM"))
        or _clean_text(os.getenv("JOB_STACK_POST_RUN_EMAIL_FROM"))
        or "noreply@applylensjobs.com"
    )


def _reply_to_from_env() -> str:
    return (
        _clean_text(os.getenv("JOB_STACK_AUTH_APPROVAL_EMAIL_REPLY_TO"))
        or _clean_text(os.getenv("JOB_STACK_POST_RUN_EMAIL_REPLY_TO"))
    )


def _public_base_url_from_env() -> str:
    return _clean_text(os.getenv("JOB_STACK_PUBLIC_BASE_URL")) or "https://applylensjobs.com"


def _request_email(request_payload: Dict[str, Any]) -> str:
    return _clean_text(request_payload.get("email")) or _clean_text(
        request_payload.get("normalized_email")
    )


def _request_display_name(request_payload: Dict[str, Any]) -> str:
    return _clean_text(request_payload.get("display_name")) or _request_email(request_payload)


def _request_id(request_payload: Dict[str, Any]) -> str:
    return _clean_text(request_payload.get("request_id"))


def _request_review_url(request_payload: Dict[str, Any]) -> str:
    base_url = _public_base_url_from_env().rstrip("/")
    request_id = _request_id(request_payload)
    if request_id:
        return f"{base_url}/admin/registration-requests?request_id={request_id}"
    return f"{base_url}/admin/registration-requests"


def build_auth_registration_admin_email_payload(
    request_payload: Dict[str, Any],
) -> Dict[str, Any]:
    request_data = dict(request_payload or {})
    request_id = _request_id(request_data)
    subject = f"ApplyLens registration approval needed | {_request_email(request_data)}"

    body_lines = [
        "A new ApplyLens registration request is waiting for admin review.",
        "",
        f"Name: {_request_display_name(request_data)}",
        f"Email: {_request_email(request_data)}",
        f"Requested At: {_clean_text(request_data.get('requested_at'))}",
        f"Request ID: {request_id}",
        f"IP Address: {_clean_text(request_data.get('request_ip_address'))}",
        f"User Agent: {_clean_text(request_data.get('request_user_agent'))}",
        "",
        f"Review: {_request_review_url(request_data)}",
        "",
        "No password or password hash is included in this email.",
    ]

    return {
        "message_kind": "auth_registration_admin_review",
        "rendered_at": _utc_now(),
        "request_id": request_id,
        "subject": subject,
        "body_text": "\n".join(body_lines).strip(),
        "from_email": _from_email_from_env(),
        "to_emails": _admin_emails_from_env(),
        "reply_to": _reply_to_from_env(),
        "request": {
            "request_id": request_id,
            "email": _request_email(request_data),
            "display_name": _request_display_name(request_data),
            "status": _clean_text(request_data.get("status")),
            "requested_at": _clean_text(request_data.get("requested_at")),
            "request_ip_address": _clean_text(request_data.get("request_ip_address")),
            "request_user_agent": _clean_text(request_data.get("request_user_agent")),
        },
    }


def build_auth_registration_user_decision_email_payload(
    request_payload: Dict[str, Any],
    *,
    approved: bool,
) -> Dict[str, Any]:
    request_data = dict(request_payload or {})
    request_id = _request_id(request_data)
    user_email = _request_email(request_data)
    display_name = _request_display_name(request_data)

    if approved:
        subject = "Your ApplyLens account was approved"
        body_lines = [
            f"Hi {display_name},",
            "",
            "Your ApplyLens account request was approved.",
            "",
            f"Log in here: {_public_base_url_from_env().rstrip('/')}/login",
        ]
        message_kind = "auth_registration_user_approved"
    else:
        subject = "Your ApplyLens account request was not approved"
        decision_note = _clean_text(request_data.get("decision_note"))
        body_lines = [
            f"Hi {display_name},",
            "",
            "Your ApplyLens account request was not approved.",
        ]
        if decision_note:
            body_lines.extend(["", f"Note: {decision_note}"])
        message_kind = "auth_registration_user_rejected"

    return {
        "message_kind": message_kind,
        "rendered_at": _utc_now(),
        "request_id": request_id,
        "subject": subject,
        "body_text": "\n".join(body_lines).strip(),
        "from_email": _from_email_from_env(),
        "to_emails": [user_email] if user_email else [],
        "reply_to": _reply_to_from_env(),
        "request": {
            "request_id": request_id,
            "email": user_email,
            "display_name": display_name,
            "status": _clean_text(request_data.get("status")),
            "decided_at": _clean_text(request_data.get("decided_at")),
            "decision_note": _clean_text(request_data.get("decision_note")),
        },
    }


def _outbox_path(payload: Dict[str, Any], *, output_dir: Any) -> Path:
    message_kind = _safe_filename_token(payload.get("message_kind"))
    source_message_kind = _safe_filename_token(payload.get("source_message_kind"))
    request_id = _safe_filename_token(payload.get("request_id"))
    timestamp = _safe_filename_token(
        payload.get("rendered_at") or payload.get("delivered_at") or _utc_now()
    )

    if source_message_kind and source_message_kind != "unknown":
        return (
            Path(str(output_dir)).expanduser()
            / f"{timestamp}__{request_id}__{message_kind}__{source_message_kind}.json"
        )

    return Path(str(output_dir)).expanduser() / f"{timestamp}__{request_id}__{message_kind}.json"


def write_auth_approval_email_outbox_artifact(
    payload: Dict[str, Any],
    *,
    output_dir: Any = DEFAULT_AUTH_APPROVAL_EMAIL_OUTBOX_DIR,
) -> Dict[str, Any]:
    output_path = _outbox_path(payload, output_dir=output_dir)

    artifact = upsert_auth_email_artifact(
        request_id=_clean_text(payload.get("request_id")),
        message_kind=_clean_text(payload.get("message_kind")),
        artifact_kind="auth_approval_email_outbox",
        artifact_name=output_path.name,
        payload_json=payload,
    )

    return {
        "ok": True,
        "path": artifact["artifact_ref"],
        "payload": payload,
        "artifact_id": artifact["artifact_id"],
        "storage_backend": "postgres",
    }

def _smtp_config_from_env(payload: Dict[str, Any]) -> Dict[str, Any]:
    host = _clean_text(os.getenv("JOB_STACK_POST_RUN_EMAIL_SMTP_HOST"))
    port = _safe_int(os.getenv("JOB_STACK_POST_RUN_EMAIL_SMTP_PORT"), 587)
    username = _clean_text(os.getenv("JOB_STACK_POST_RUN_EMAIL_SMTP_USERNAME"))
    password = os.getenv("JOB_STACK_POST_RUN_EMAIL_SMTP_PASSWORD", "")
    starttls = _normalize_bool(
        os.getenv("JOB_STACK_POST_RUN_EMAIL_SMTP_STARTTLS"),
        default=True,
    )
    timeout_seconds = _safe_int(os.getenv("JOB_STACK_POST_RUN_EMAIL_SMTP_TIMEOUT_SECONDS"), 30)

    from_email = _clean_text(payload.get("from_email"))
    to_emails = list(payload.get("to_emails", []) or [])
    reply_to = _clean_text(payload.get("reply_to"))

    if not host:
        raise ValueError("Missing JOB_STACK_POST_RUN_EMAIL_SMTP_HOST for smtp delivery mode.")
    if port <= 0:
        raise ValueError("JOB_STACK_POST_RUN_EMAIL_SMTP_PORT must be > 0.")
    if not from_email:
        raise ValueError("Missing auth approval from_email.")
    if not to_emails:
        raise ValueError("Missing auth approval recipients.")
    if username and not password:
        raise ValueError("JOB_STACK_POST_RUN_EMAIL_SMTP_PASSWORD is required when SMTP username is set.")
    if timeout_seconds <= 0:
        timeout_seconds = 30

    return {
        "host": host,
        "port": port,
        "username": username,
        "password": password,
        "starttls": starttls,
        "timeout_seconds": timeout_seconds,
        "from_email": from_email,
        "to_emails": to_emails,
        "reply_to": reply_to,
    }


def _build_email_message(payload: Dict[str, Any], smtp_config: Dict[str, Any]) -> EmailMessage:
    message = EmailMessage()
    message["Subject"] = _clean_text(payload.get("subject"))
    message["From"] = smtp_config["from_email"]
    message["To"] = ", ".join(smtp_config["to_emails"])

    if smtp_config.get("reply_to"):
        message["Reply-To"] = smtp_config["reply_to"]

    message.set_content(_clean_text(payload.get("body_text")))
    return message


def _send_via_smtp(payload: Dict[str, Any]) -> Dict[str, Any]:
    smtp_config = _smtp_config_from_env(payload)
    message = _build_email_message(payload, smtp_config)

    with smtplib.SMTP(
        smtp_config["host"],
        smtp_config["port"],
        timeout=smtp_config["timeout_seconds"],
    ) as client:
        client.ehlo()

        if smtp_config["starttls"]:
            client.starttls(context=ssl.create_default_context())
            client.ehlo()

        if smtp_config["username"]:
            client.login(smtp_config["username"], smtp_config["password"])

        client.send_message(message)

    return {
        "delivery_status": "sent_smtp",
        "delivery_provider": "smtp",
        "delivery_error": "",
        "delivery_recipients": smtp_config["to_emails"],
        "delivery_from": smtp_config["from_email"],
    }


def deliver_auth_approval_email_payload(
    payload: Dict[str, Any],
    *,
    mode: Any = None,
    outbox_dir: Any = DEFAULT_AUTH_APPROVAL_EMAIL_OUTBOX_DIR,
    delivery_dir: Any = DEFAULT_AUTH_APPROVAL_EMAIL_DELIVERY_DIR,
) -> Dict[str, Any]:
    normalized_mode = _normalize_mode(
        mode if mode is not None else os.getenv("JOB_STACK_AUTH_APPROVAL_EMAIL_MODE", "outbox_only")
    )

    delivery_payload = {
        "message_kind": "auth_approval_email_delivery",
        "delivered_at": _utc_now(),
        "delivery_mode": normalized_mode,
        "delivery_status": "",
        "delivery_provider": "",
        "delivery_error": "",
        "delivery_recipients": [],
        "delivery_from": "",
        "request_id": _clean_text(payload.get("request_id")),
        "source_message_kind": _clean_text(payload.get("message_kind")),
        "subject": _clean_text(payload.get("subject")),
        "body_text": _clean_text(payload.get("body_text")),
        "outbox_path": "",
    }

    outbox_result = write_auth_approval_email_outbox_artifact(
        payload,
        output_dir=outbox_dir,
    )
    delivery_payload["outbox_path"] = outbox_result["path"]

    try:
        if normalized_mode == "outbox_only":
            delivery_payload["delivery_status"] = "recorded_outbox_only"
        elif normalized_mode == "dry_run":
            delivery_payload["delivery_status"] = "dry_run_only"
        elif normalized_mode == "smtp":
            delivery_payload.update(_send_via_smtp(payload))
        else:
            raise ValueError(f"Unsupported auth approval email mode={normalized_mode!r}")
    except Exception as exc:
        delivery_payload["delivery_status"] = (
            "failed_smtp" if normalized_mode == "smtp" else "failed_delivery"
        )
        delivery_payload["delivery_provider"] = "smtp" if normalized_mode == "smtp" else ""
        delivery_payload["delivery_error"] = repr(exc)

    delivery_path = _outbox_path(delivery_payload, output_dir=delivery_dir)

    artifact = upsert_auth_email_artifact(
        request_id=_clean_text(delivery_payload.get("request_id")),
        message_kind=_clean_text(delivery_payload.get("source_message_kind")),
        artifact_kind="auth_approval_email_delivery",
        artifact_name=delivery_path.name,
        payload_json=delivery_payload,
    )

    return {
        "ok": delivery_payload["delivery_status"] not in {"failed_smtp", "failed_delivery"},
        "path": artifact["artifact_ref"],
        "payload": delivery_payload,
        "outbox_path": outbox_result["path"],
        "artifact_id": artifact["artifact_id"],
        "storage_backend": "postgres",
    }
