from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple


DEFAULT_POST_RUN_EMAIL_DELIVERY_DIR = Path("outputs/scheduler_logs/post_run_email_delivery")
ALLOWED_DELIVERY_MODES = {"outbox_only", "dry_run"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _normalize_job_name(value: Any) -> str:
    text = _clean_text(value).lower()
    return text.replace("-", "_").replace(" ", "_")


def _normalize_delivery_mode(value: Any) -> str:
    mode = _clean_text(value).lower() or "outbox_only"
    if mode not in ALLOWED_DELIVERY_MODES:
        allowed = ", ".join(sorted(ALLOWED_DELIVERY_MODES))
        raise ValueError(f"Unsupported delivery mode={mode!r}. Allowed: {allowed}")
    return mode


def _read_json_payload(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return payload


def _load_outbox_payload(payload_or_path: Any) -> Tuple[Dict[str, Any], Path]:
    if isinstance(payload_or_path, dict):
        payload = dict(payload_or_path)
        raw_path = _clean_text(payload.get("outbox_path"))
        return payload, Path(raw_path).expanduser() if raw_path else Path("")

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


def deliver_post_run_email_outbox(
    payload_or_path: Any,
    *,
    mode: Any = "outbox_only",
    output_dir: Any = DEFAULT_POST_RUN_EMAIL_DELIVERY_DIR,
) -> Dict[str, Any]:
    normalized_mode = _normalize_delivery_mode(mode)
    outbox_payload, outbox_path = _load_outbox_payload(payload_or_path)

    delivery_status = (
        "recorded_outbox_only"
        if normalized_mode == "outbox_only"
        else "dry_run_only"
    )

    delivery_result_payload = {
        "message_kind": "scheduled_run_summary_email_delivery",
        "delivered_at": _utc_now(),
        "delivery_mode": normalized_mode,
        "delivery_status": delivery_status,
        "delivery_provider": "",
        "delivery_error": "",
        "job_name": _normalize_job_name(outbox_payload.get("job_name")),
        "run_id": _clean_text(outbox_payload.get("run_id")),
        "status": _clean_text(outbox_payload.get("status")),
        "subject": _clean_text(outbox_payload.get("subject")),
        "body_text": _clean_text(outbox_payload.get("body_text")),
        "post_run_summary_path": _clean_text(outbox_payload.get("post_run_summary_path")),
        "source_artifact_type": _clean_text(outbox_payload.get("source_artifact_type")),
        "source_artifact_path": _clean_text(outbox_payload.get("source_artifact_path")),
        "source_outbox_path": str(outbox_path) if str(outbox_path) else _clean_text(outbox_payload.get("outbox_path")),
    }

    output_path = _delivery_result_path(
        outbox_payload,
        output_dir=output_dir,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    tmp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    tmp_path.write_text(
        json.dumps(delivery_result_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    tmp_path.replace(output_path)

    return {
        "path": str(output_path),
        "payload": delivery_result_payload,
    }