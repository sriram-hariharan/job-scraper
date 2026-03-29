from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Tuple

from src.config.settings import ACTIVE_APPLICATION_PLANNING_OUTPUT_DIR


DEFAULT_AGENT_DISCOVERY_SUMMARY_PATH = Path(
    "outputs/scheduler_logs/agent_discovery_summary.json"
)
DEFAULT_LIVE_PIPELINE_OUTPUT_DIR = Path(
    ACTIVE_APPLICATION_PLANNING_OUTPUT_DIR
).expanduser()
DEFAULT_POST_RUN_SUMMARY_DIR = Path("outputs/scheduler_logs/post_run_summaries")

def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _dict_or_empty(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _list_or_empty(value: Any) -> list:
    return list(value) if isinstance(value, list) else []


def _normalize_job_name(value: Any) -> str:
    text = _clean_text(value).lower()
    return text.replace("-", "_").replace(" ", "_")


def _read_json_artifact(path: Any) -> Tuple[Dict[str, Any], bool, bool]:
    artifact_path = Path(str(path)).expanduser()

    if not artifact_path.exists() or not artifact_path.is_file():
        return {}, False, False

    try:
        payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    except Exception:
        return {}, True, False

    if not isinstance(payload, dict):
        return {}, True, False

    return payload, True, True


def _live_pipeline_status_path_from_record(record: Dict[str, Any]) -> Path:
    options = _dict_or_empty(record.get("options"))

    explicit_path = _clean_text(options.get("status_path"))
    if explicit_path:
        return Path(explicit_path).expanduser()

    output_dir = _clean_text(options.get("output_dir")) or str(DEFAULT_LIVE_PIPELINE_OUTPUT_DIR)
    return Path(output_dir).expanduser() / "live_pipeline_status.json"


def _live_pipeline_log_path_from_record(record: Dict[str, Any]) -> str:
    options = _dict_or_empty(record.get("options"))

    explicit_path = _clean_text(options.get("log_path"))
    if explicit_path:
        return explicit_path

    output_dir = _clean_text(options.get("output_dir")) or str(DEFAULT_LIVE_PIPELINE_OUTPUT_DIR)
    return str(Path(output_dir).expanduser() / "live_pipeline_run.log")


def _base_summary_payload(record: Dict[str, Any]) -> Dict[str, Any]:
    options = _dict_or_empty(record.get("options"))

    return {
        "job_name": _normalize_job_name(record.get("job_name")),
        "run_id": _clean_text(record.get("run_id")),
        "status": _clean_text(record.get("status")),
        "started_at": _clean_text(record.get("started_at")),
        "finished_at": _clean_text(record.get("finished_at")),
        "return_code": _safe_int(record.get("return_code"), 1),
        "summary_message": "",
        "error": _clean_text(record.get("error")),
        "artifact_type": "",
        "artifact_path": "",
        "artifact_exists": False,
        "artifact_parse_ok": False,
        "command_text": _clean_text(record.get("command_text")),
        "trigger_source": _clean_text(record.get("trigger_source")),
        "options": options,
        "log_path": _clean_text(options.get("log_path")),
        "status_path": _clean_text(options.get("status_path")),
        "current_stage": "",
        "completed_stages": [],
        "counts": {},
        "final_job_count": None,
        "config": {},
        "component_statuses": {},
        "failure_components": [],
        "component_errors": {},
        "source_counts": {},
        "rollup_counts": {},
    }


def _apply_common_artifact_fields(
    payload: Dict[str, Any],
    artifact: Dict[str, Any],
) -> None:
    started_at = _clean_text(artifact.get("started_at"))
    finished_at = _clean_text(artifact.get("finished_at"))
    status = _clean_text(artifact.get("status"))
    summary_message = _clean_text(artifact.get("summary_message"))
    error = _clean_text(artifact.get("error"))

    if started_at:
        payload["started_at"] = started_at
    if finished_at:
        payload["finished_at"] = finished_at
    if status:
        payload["status"] = status
    if summary_message:
        payload["summary_message"] = summary_message
    if error:
        payload["error"] = error

    if artifact.get("return_code") is not None:
        payload["return_code"] = _safe_int(
            artifact.get("return_code"),
            payload["return_code"],
        )


def _build_agent_discovery_summary_payload(
    record: Dict[str, Any],
    *,
    agent_discovery_summary_path: Any = DEFAULT_AGENT_DISCOVERY_SUMMARY_PATH,
) -> Dict[str, Any]:
    payload = _base_summary_payload(record)

    artifact_path = Path(str(agent_discovery_summary_path)).expanduser()
    artifact, artifact_exists, artifact_parse_ok = _read_json_artifact(artifact_path)

    payload["artifact_type"] = "agent_discovery_summary"
    payload["artifact_path"] = str(artifact_path)
    payload["artifact_exists"] = artifact_exists
    payload["artifact_parse_ok"] = artifact_parse_ok

    if artifact_parse_ok:
        _apply_common_artifact_fields(payload, artifact)
        payload["component_statuses"] = _dict_or_empty(artifact.get("component_statuses"))
        payload["failure_components"] = _list_or_empty(artifact.get("failure_components"))
        payload["component_errors"] = _dict_or_empty(artifact.get("component_errors"))

        discovery_summary = _dict_or_empty(artifact.get("discovery_summary"))
        payload["source_counts"] = _dict_or_empty(discovery_summary.get("sources"))
        payload["rollup_counts"] = _dict_or_empty(
            discovery_summary.get("run_unique_discovered_by_ats")
        )

    if not payload["summary_message"]:
        payload["summary_message"] = (
            "Discovery scheduler run completed successfully"
            if payload["status"] == "succeeded"
            else "Discovery scheduler run completed with failures"
        )

    return payload


def _build_live_pipeline_summary_payload(
    record: Dict[str, Any],
) -> Dict[str, Any]:
    payload = _base_summary_payload(record)

    status_path = _live_pipeline_status_path_from_record(record)
    artifact, artifact_exists, artifact_parse_ok = _read_json_artifact(status_path)

    payload["artifact_type"] = "live_pipeline_status"
    payload["artifact_path"] = str(status_path)
    payload["artifact_exists"] = artifact_exists
    payload["artifact_parse_ok"] = artifact_parse_ok
    payload["status_path"] = str(status_path)
    payload["log_path"] = _live_pipeline_log_path_from_record(record)

    if artifact_parse_ok:
        _apply_common_artifact_fields(payload, artifact)
        payload["log_path"] = _clean_text(artifact.get("log_path")) or payload["log_path"]
        payload["status_path"] = _clean_text(artifact.get("status_path")) or payload["status_path"]
        payload["current_stage"] = _clean_text(artifact.get("current_stage"))
        payload["completed_stages"] = _list_or_empty(artifact.get("completed_stages"))
        payload["counts"] = _dict_or_empty(artifact.get("counts"))
        payload["final_job_count"] = artifact.get("final_job_count")
        payload["config"] = _dict_or_empty(artifact.get("config"))

    if not payload["summary_message"]:
        payload["summary_message"] = (
            "Live pipeline scheduler run completed successfully"
            if payload["status"] == "succeeded"
            else "Live pipeline scheduler run failed"
        )

    return payload


def build_post_run_summary_payload(
    record: Dict[str, Any],
    *,
    agent_discovery_summary_path: Any = DEFAULT_AGENT_DISCOVERY_SUMMARY_PATH,
) -> Dict[str, Any]:
    job_name = _normalize_job_name(record.get("job_name"))

    if job_name == "agent_discovery":
        return _build_agent_discovery_summary_payload(
            record,
            agent_discovery_summary_path=agent_discovery_summary_path,
        )

    if job_name == "live_pipeline":
        return _build_live_pipeline_summary_payload(record)

    payload = _base_summary_payload(record)
    payload["summary_message"] = (
        f"Unsupported scheduled job for normalized post-run summary: {job_name}"
    )
    return payload

def _post_run_summary_output_path(
    record: Dict[str, Any],
    *,
    output_dir: Any = DEFAULT_POST_RUN_SUMMARY_DIR,
) -> Path:
    job_name = _normalize_job_name(record.get("job_name")) or "scheduled_job"
    run_id = _clean_text(record.get("run_id")) or "unknown_run"

    return Path(str(output_dir)).expanduser() / f"{run_id}__{job_name}__post_run_summary.json"


def write_post_run_summary_artifact(
    record: Dict[str, Any],
    *,
    output_dir: Any = DEFAULT_POST_RUN_SUMMARY_DIR,
    agent_discovery_summary_path: Any = DEFAULT_AGENT_DISCOVERY_SUMMARY_PATH,
) -> Dict[str, Any]:
    payload = build_post_run_summary_payload(
        record,
        agent_discovery_summary_path=agent_discovery_summary_path,
    )

    output_path = _post_run_summary_output_path(
        record,
        output_dir=output_dir,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    tmp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    tmp_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    tmp_path.replace(output_path)

    return {
        "path": str(output_path),
        "payload": payload,
    }