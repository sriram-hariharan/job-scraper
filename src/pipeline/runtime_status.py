import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


ENV_STATUS_PATH = "JOB_APP_PIPELINE_STATUS_PATH"
ENV_RUN_ID = "JOB_APP_PIPELINE_RUN_ID"
PREFERENCE_RUNTIME_SCHEMA_VERSION = "pipeline-preference-runtime-v1"

STAGE_ORDER = [
    "startup",
    "scraping",
    "filtering",
    "dedupe",
    "ranking",
    "cache_filter",
    "details",
    "intelligence",
    "ai_evaluation_filter",
    "embedding_prefilter",
    "ai_evaluation",
    "resume_matching",
    "application_priority",
    "rag_export",
    "planning",
    "finalization",
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _status_path() -> Optional[Path]:
    raw = os.getenv(ENV_STATUS_PATH, "").strip()
    if not raw:
        return None
    return Path(raw)


def _run_id() -> str:
    return os.getenv(ENV_RUN_ID, "").strip()


def is_enabled() -> bool:
    return _status_path() is not None


def _read_status() -> Dict[str, Any]:
    path = _status_path()
    if path is None or not path.exists():
        return {}

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_status(payload: Dict[str, Any]) -> None:
    path = _status_path()
    if path is None:
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    tmp_path.replace(path)


def initialize_run(
    *,
    output_dir: str,
    log_path: str,
    status_path: str,
    planning_only: bool,
    job_limit: int,
    job_packet_limit: int,
    llm_actions: list[str],
    generate_tailoring: bool,
    generate_llm_tailoring: bool,
    refresh_llm_tailoring: bool,
    generate_llm_fallback: bool,
    generate_llm_adjudication: bool,
    delete_seen_data: str,
) -> None:
    if not is_enabled():
        return

    payload = {
        "run_id": _run_id(),
        "status": "running",
        "started_at": _utc_now(),
        "finished_at": "",
        "current_stage": "startup",
        "completed_stages": [],
        "stage_order": STAGE_ORDER,
        "stage_started_at": _utc_now(),
        "stage_message": "Starting pipeline entrypoint",
        "counts": {},
        "summary_message": "",
        "final_job_count": None,
        "return_code": None,
        "error": "",
        "output_dir": output_dir,
        "log_path": log_path,
        "status_path": status_path,
        "config": {
            "planning_only": planning_only,
            "job_limit": job_limit,
            "job_packet_limit": job_packet_limit,
            "llm_actions": llm_actions,
            "generate_tailoring": generate_tailoring,
            "generate_llm_tailoring": generate_llm_tailoring,
            "refresh_llm_tailoring": refresh_llm_tailoring,
            "generate_llm_fallback": generate_llm_fallback,
            "generate_llm_adjudication": generate_llm_adjudication,
            "delete_seen_data": delete_seen_data,
        },
    }
    _write_status(payload)


def start_stage(stage: str, message: str = "", counts: Optional[Dict[str, Any]] = None) -> None:
    if not is_enabled():
        return

    payload = _read_status()
    payload["status"] = "running"
    payload["current_stage"] = stage
    payload["stage_started_at"] = _utc_now()
    payload["stage_message"] = message or stage
    payload.setdefault("completed_stages", [])
    payload.setdefault("counts", {})
    if counts:
        payload["counts"].update(counts)
    _write_status(payload)


def complete_stage(stage: str, message: str = "", counts: Optional[Dict[str, Any]] = None) -> None:
    if not is_enabled():
        return

    payload = _read_status()
    completed = payload.setdefault("completed_stages", [])
    if stage not in completed:
        completed.append(stage)
    if message:
        payload["stage_message"] = message
    if counts:
        payload.setdefault("counts", {}).update(counts)
    _write_status(payload)


def update_counts(**counts: Any) -> None:
    if not is_enabled():
        return

    payload = _read_status()
    payload.setdefault("counts", {}).update(counts)
    _write_status(payload)


def update_config(**config: Any) -> None:
    if not is_enabled():
        return

    payload = _read_status()
    payload.setdefault("config", {}).update(config)
    _write_status(payload)


def update_stage_message(message: str = "", counts: Optional[Dict[str, Any]] = None) -> None:
    if not is_enabled():
        return

    payload = _read_status()
    if message:
        payload["stage_message"] = message
    if counts:
        payload.setdefault("counts", {}).update(counts)
    _write_status(payload)


def finish_run(
    *,
    return_code: int = 0,
    summary_message: str = "",
    final_job_count: Optional[int] = None,
) -> None:
    if not is_enabled():
        return

    payload = _read_status()
    completed = payload.setdefault("completed_stages", [])
    if "finalization" not in completed:
        completed.append("finalization")

    payload["status"] = "succeeded" if return_code == 0 else "failed"
    payload["finished_at"] = _utc_now()
    payload["return_code"] = return_code
    payload["summary_message"] = summary_message
    payload["final_job_count"] = final_job_count
    payload["current_stage"] = ""
    payload["stage_message"] = summary_message
    _write_status(payload)


def fail_run(stage: str, error: str) -> None:
    if not is_enabled():
        return

    payload = _read_status()
    payload["status"] = "failed"
    payload["finished_at"] = _utc_now()
    payload["return_code"] = 1
    payload["current_stage"] = stage
    payload["stage_message"] = f"Failed in {stage}"
    payload["error"] = error
    _write_status(payload)
