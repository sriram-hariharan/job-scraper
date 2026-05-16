from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from src.storage.scheduler_artifacts_store import upsert_scheduler_artifact


DEFAULT_NOTIFICATION_RECORDS_DIR = Path("postgres_artifacts/scheduler/post_run_notification")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _normalize_job_name(value: Any) -> str:
    text = _clean_text(value).lower()
    return text.replace("-", "_").replace(" ", "_")


def _load_delivery_payload(payload_or_path: Any) -> Tuple[Dict[str, Any], Optional[Path]]:
    if isinstance(payload_or_path, dict):
        payload = dict(payload_or_path)
        source_path = _clean_text(payload.get("source_delivery_path"))
        return payload, Path(source_path).expanduser() if source_path else None

    path = Path(str(payload_or_path)).expanduser()
    if not path.exists() or not path.is_file():
        raise ValueError(f"Delivery artifact not found: {path}")

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}")

    return payload, path


def _notification_level(run_status: str, delivery_status: str) -> str:
    normalized_run_status = _clean_text(run_status).lower()
    if normalized_run_status in {"success", "succeeded"}:
        return "success"
    if normalized_run_status in {"failed", "error"}:
        return "error"

    normalized_delivery_status = _clean_text(delivery_status).lower()
    if normalized_delivery_status == "sent_smtp":
        return "success"
    if normalized_delivery_status in {"failed_smtp", "failed_delivery"}:
        return "error"
    if normalized_delivery_status in {"recorded_outbox_only", "dry_run_only"}:
        return "info"

    return "info"


def _notification_message(delivery_payload: Dict[str, Any]) -> str:
    delivery_status = _clean_text(delivery_payload.get("delivery_status"))
    job_name = _normalize_job_name(delivery_payload.get("job_name")) or "scheduled_job"
    run_id = _clean_text(delivery_payload.get("run_id"))

    if delivery_status == "sent_smtp":
        return f"Scheduled run email delivered for {job_name} ({run_id})."

    if delivery_status == "failed_smtp":
        return f"Scheduled run email delivery failed for {job_name} ({run_id})."

    if delivery_status == "recorded_outbox_only":
        return f"Scheduled run email recorded as outbox-only for {job_name} ({run_id})."

    if delivery_status == "dry_run_only":
        return f"Scheduled run email recorded as dry-run for {job_name} ({run_id})."

    return f"Scheduled run email delivery recorded for {job_name} ({run_id})."


def _body_preview(value: Any, max_len: int = 280) -> str:
    text = _clean_text(value).replace("\n", " ")
    if len(text) <= max_len:
        return text
    return text[: max_len - 3].rstrip() + "..."


def build_notification_record_payload(
    payload_or_path: Any,
) -> Dict[str, Any]:
    delivery_payload, delivery_path = _load_delivery_payload(payload_or_path)

    run_id = _clean_text(delivery_payload.get("run_id")) or "unknown_run"
    job_name = _normalize_job_name(delivery_payload.get("job_name")) or "scheduled_job"
    run_status = _clean_text(delivery_payload.get("status"))
    delivery_status = _clean_text(delivery_payload.get("delivery_status"))
    notification_id = f"scheduled_run_email::{run_id}::{job_name}"

    return {
        "notification_id": notification_id,
        "notification_kind": "scheduled_run_email_delivery",
        "created_at": _clean_text(delivery_payload.get("delivered_at")) or _utc_now(),
        "title": _clean_text(delivery_payload.get("subject"))
        or f"Scheduled run notification | {job_name}",
        "message": _notification_message(delivery_payload),
        "level": _notification_level(run_status, delivery_status),
        "is_read": False,
        "job_name": job_name,
        "run_id": run_id,
        "run_status": run_status,
        "delivery_mode": _clean_text(delivery_payload.get("delivery_mode")),
        "delivery_status": delivery_status,
        "delivery_provider": _clean_text(delivery_payload.get("delivery_provider")),
        "delivery_error": _clean_text(delivery_payload.get("delivery_error")),
        "delivery_recipients": list(delivery_payload.get("delivery_recipients", []) or []),
        "delivery_from": _clean_text(delivery_payload.get("delivery_from")),
        "subject": _clean_text(delivery_payload.get("subject")),
        "body_preview": _body_preview(delivery_payload.get("body_text")),
        "post_run_summary_path": _clean_text(delivery_payload.get("post_run_summary_path")),
        "source_artifact_type": _clean_text(delivery_payload.get("source_artifact_type")),
        "source_artifact_path": _clean_text(delivery_payload.get("source_artifact_path")),
        "source_outbox_path": _clean_text(delivery_payload.get("source_outbox_path")),
        "source_delivery_path": str(delivery_path) if delivery_path is not None else "",
    }


def _notification_output_path(
    notification_payload: Dict[str, Any],
    *,
    output_dir: Any = DEFAULT_NOTIFICATION_RECORDS_DIR,
) -> Path:
    run_id = _clean_text(notification_payload.get("run_id")) or "unknown_run"
    job_name = _normalize_job_name(notification_payload.get("job_name")) or "scheduled_job"
    return Path(str(output_dir)).expanduser() / f"{run_id}__{job_name}__notification.json"


def write_notification_record_artifact(
    payload_or_path: Any,
    *,
    output_dir: Any = DEFAULT_NOTIFICATION_RECORDS_DIR,
) -> Dict[str, Any]:
    notification_payload = build_notification_record_payload(payload_or_path)

    output_path = _notification_output_path(
        notification_payload,
        output_dir=output_dir,
    )

    artifact = upsert_scheduler_artifact(
        run_id=_clean_text(notification_payload.get("run_id")),
        job_name=_clean_text(notification_payload.get("job_name")),
        artifact_kind="post_run_notification",
        artifact_name=output_path.name,
        payload_json=notification_payload,
    )

    return {
        "path": artifact["artifact_ref"],
        "payload": notification_payload,
        "artifact_id": artifact["artifact_id"],
        "storage_backend": "postgres",
    }
