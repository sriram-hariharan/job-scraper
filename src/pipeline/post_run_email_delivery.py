from __future__ import annotations

import json
import os
import smtplib
import ssl
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.storage.scheduler_artifacts_store import upsert_scheduler_artifact


DEFAULT_POST_RUN_EMAIL_DELIVERY_DIR = Path("outputs/scheduler_logs/post_run_email_delivery")
ALLOWED_DELIVERY_MODES = {"outbox_only", "dry_run", "smtp"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalize_job_name(value: Any) -> str:
    text = _clean_text(value).lower()
    return text.replace("-", "_").replace(" ", "_")


def _normalize_delivery_mode(value: Any) -> str:
    mode = _clean_text(value).lower() or "outbox_only"
    if mode not in ALLOWED_DELIVERY_MODES:
        allowed = ", ".join(sorted(ALLOWED_DELIVERY_MODES))
        raise ValueError(f"Unsupported delivery mode={mode!r}. Allowed: {allowed}")
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


def _read_json_payload(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return payload


def _load_outbox_payload(payload_or_path: Any) -> Tuple[Dict[str, Any], Optional[Path]]:
    if isinstance(payload_or_path, dict):
        payload = dict(payload_or_path)
        raw_path = _clean_text(payload.get("outbox_path"))
        return payload, Path(raw_path).expanduser() if raw_path else None

    path = Path(str(payload_or_path)).expanduser()
    if not path.exists() or not path.is_file():
        raise ValueError(f"Outbox artifact not found: {path}")

    payload = _read_json_payload(path)
    return payload, path


def _delivery_result_path(
    outbox_payload: Dict[str, Any],
    *,
    output_dir: Any = DEFAULT_POST_RUN_EMAIL_DELIVERY_DIR,
) -> Path:
    run_id = _clean_text(outbox_payload.get("run_id")) or "unknown_run"
    job_name = _normalize_job_name(outbox_payload.get("job_name")) or "scheduled_job"
    return Path(str(output_dir)).expanduser() / f"{run_id}__{job_name}__delivery_result.json"


def _smtp_config_from_env() -> Dict[str, Any]:
    host = _clean_text(os.getenv("JOB_STACK_POST_RUN_EMAIL_SMTP_HOST"))
    port = _safe_int(os.getenv("JOB_STACK_POST_RUN_EMAIL_SMTP_PORT"), 587)
    username = _clean_text(os.getenv("JOB_STACK_POST_RUN_EMAIL_SMTP_USERNAME"))
    password = os.getenv("JOB_STACK_POST_RUN_EMAIL_SMTP_PASSWORD", "")
    starttls = _normalize_bool(
        os.getenv("JOB_STACK_POST_RUN_EMAIL_SMTP_STARTTLS"),
        default=True,
    )
    timeout_seconds = _safe_int(
        os.getenv("JOB_STACK_POST_RUN_EMAIL_SMTP_TIMEOUT_SECONDS"),
        30,
    )
    from_addr = _clean_text(os.getenv("JOB_STACK_POST_RUN_EMAIL_FROM"))
    to_addrs = _parse_recipient_list(os.getenv("JOB_STACK_POST_RUN_EMAIL_TO"))
    reply_to = _clean_text(os.getenv("JOB_STACK_POST_RUN_EMAIL_REPLY_TO"))

    if not host:
        raise ValueError("Missing JOB_STACK_POST_RUN_EMAIL_SMTP_HOST for smtp delivery mode.")
    if port <= 0:
        raise ValueError("JOB_STACK_POST_RUN_EMAIL_SMTP_PORT must be > 0.")
    if not from_addr:
        raise ValueError("Missing JOB_STACK_POST_RUN_EMAIL_FROM for smtp delivery mode.")
    if not to_addrs:
        raise ValueError("Missing JOB_STACK_POST_RUN_EMAIL_TO for smtp delivery mode.")
    if username and not password:
        raise ValueError(
            "JOB_STACK_POST_RUN_EMAIL_SMTP_PASSWORD is required when SMTP username is set."
        )
    if timeout_seconds <= 0:
        timeout_seconds = 30

    return {
        "host": host,
        "port": port,
        "username": username,
        "password": password,
        "starttls": starttls,
        "timeout_seconds": timeout_seconds,
        "from_addr": from_addr,
        "to_addrs": to_addrs,
        "reply_to": reply_to,
    }


def _build_smtp_message(
    outbox_payload: Dict[str, Any],
    smtp_config: Dict[str, Any],
) -> EmailMessage:
    message = EmailMessage()
    message["Subject"] = _clean_text(outbox_payload.get("subject"))
    message["From"] = smtp_config["from_addr"]
    message["To"] = ", ".join(smtp_config["to_addrs"])

    if smtp_config.get("reply_to"):
        message["Reply-To"] = smtp_config["reply_to"]

    message.set_content(_clean_text(outbox_payload.get("body_text")))
    return message


def _send_via_smtp(outbox_payload: Dict[str, Any]) -> Dict[str, Any]:
    smtp_config = _smtp_config_from_env()
    message = _build_smtp_message(outbox_payload, smtp_config)

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
            client.login(
                smtp_config["username"],
                smtp_config["password"],
            )

        client.send_message(message)

    return {
        "delivery_status": "sent_smtp",
        "delivery_provider": "smtp",
        "delivery_error": "",
        "delivery_recipients": smtp_config["to_addrs"],
        "delivery_from": smtp_config["from_addr"],
    }


def deliver_post_run_email_outbox(
    payload_or_path: Any,
    *,
    mode: Any = "outbox_only",
    output_dir: Any = DEFAULT_POST_RUN_EMAIL_DELIVERY_DIR,
) -> Dict[str, Any]:
    normalized_mode = _normalize_delivery_mode(mode)
    outbox_payload, outbox_path = _load_outbox_payload(payload_or_path)

    delivery_result_payload = {
        "message_kind": "scheduled_run_summary_email_delivery",
        "delivered_at": _utc_now(),
        "delivery_mode": normalized_mode,
        "delivery_status": "",
        "delivery_provider": "",
        "delivery_error": "",
        "delivery_recipients": [],
        "delivery_from": "",
        "job_name": _normalize_job_name(outbox_payload.get("job_name")),
        "run_id": _clean_text(outbox_payload.get("run_id")),
        "status": _clean_text(outbox_payload.get("status")),
        "subject": _clean_text(outbox_payload.get("subject")),
        "body_text": _clean_text(outbox_payload.get("body_text")),
        "post_run_summary_path": _clean_text(outbox_payload.get("post_run_summary_path")),
        "source_artifact_type": _clean_text(outbox_payload.get("source_artifact_type")),
        "source_artifact_path": _clean_text(outbox_payload.get("source_artifact_path")),
        "source_outbox_path": str(outbox_path) if outbox_path is not None else _clean_text(outbox_payload.get("outbox_path")),
    }

    try:
        if normalized_mode == "outbox_only":
            delivery_result_payload["delivery_status"] = "recorded_outbox_only"
        elif normalized_mode == "dry_run":
            delivery_result_payload["delivery_status"] = "dry_run_only"
        elif normalized_mode == "smtp":
            delivery_result_payload.update(_send_via_smtp(outbox_payload))
        else:
            raise ValueError(f"Unsupported delivery mode={normalized_mode!r}")
    except Exception as exc:
        delivery_result_payload["delivery_status"] = (
            "failed_smtp" if normalized_mode == "smtp" else "failed_delivery"
        )
        delivery_result_payload["delivery_provider"] = (
            "smtp" if normalized_mode == "smtp" else ""
        )
        delivery_result_payload["delivery_error"] = repr(exc)

    output_path = _delivery_result_path(
        outbox_payload,
        output_dir=output_dir,
    )

    artifact = upsert_scheduler_artifact(
        run_id=_clean_text(delivery_result_payload.get("run_id")),
        job_name=_clean_text(delivery_result_payload.get("job_name")),
        artifact_kind="post_run_email_delivery",
        artifact_name=output_path.name,
        payload_json=delivery_result_payload,
    )

    delivery_result_payload["source_delivery_path"] = artifact["artifact_ref"]

    return {
        "path": artifact["artifact_ref"],
        "payload": delivery_result_payload,
        "artifact_id": artifact["artifact_id"],
        "storage_backend": "postgres",
    }
