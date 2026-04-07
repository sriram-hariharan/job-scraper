from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Tuple
import csv
import hashlib
import json
import os
import re
import subprocess
import sys

from src.pipeline.post_run_notification import DEFAULT_NOTIFICATION_RECORDS_DIR

from src.config.consts import _ALLOWED_REWRITE_REVIEW_STATES
from src.config.settings import (
    ACTIVE_APPLICATION_PLANNING_OUTPUT_DIR,
    SCHEDULER_RUN_HISTORY_PATH,
)
from src.storage.application_actions.store import (
    application_action_db_row,
    insert_application_action_row_to_postgres,
)
from src.storage.application_actions.read_postgres import (
    get_latest_application_actions_rows,
)
from src.storage.patch_selections.store import (
    insert_patch_selection_row_to_postgres,
)
from src.storage.patch_selections.read_postgres import (
    get_patch_selections_postgres_status_payload,
)
from src.storage.operator_decisions.store import (
    insert_operator_decision_row_to_postgres,
    operator_decision_db_row,
)
from src.storage.operator_decisions.read_postgres import (
    get_operator_decisions_postgres_status_payload,
)
from src.storage.notification_state.store import (
    insert_notification_state_row_to_postgres,
)
from src.storage.notification_state.read_postgres import (
    get_notification_state_postgres_status_payload,
)
from src.pipeline.scheduler import (
    DEFAULT_LAUNCHD_AGENT_DIR,
    DEFAULT_LAUNCHD_INTERVAL_SECONDS,
    DEFAULT_LAUNCHD_LABEL_PREFIX,
    DEFAULT_LAUNCHD_LOG_DIR,
    DEFAULT_LAUNCHD_OUT_DIR,
    DEFAULT_LAUNCHD_TARGET,
    build_scheduled_job_command,
    build_scheduler_launchd_plist_payload,
    get_scheduled_job_definition,
    get_scheduled_job_definitions,
    get_scheduler_launchd_agent_status,
)
from src.storage.scheduler.contract import (
    scheduler_init_sql_generation_payload,
    scheduler_init_sql_payload,
    scheduler_job_definition_seed_rows,
    scheduler_postgres_table_specs,
    scheduler_schema_sql_payload,
    scheduler_seed_sql_generation_payload,
    scheduler_seed_sql_payload,
)

from src.storage.scheduler.read_postgres import (
    get_scheduler_postgres_status_payload,
)
from src.storage.scheduler.contract import (
    scheduler_contract_health_payload,
)

DEFAULT_OUTPUT_DIR = Path(
    os.environ.get("APPLICATION_PLANNING_OUTPUT_DIR", ACTIVE_APPLICATION_PLANNING_OUTPUT_DIR)
).expanduser()
DEFAULT_CORPUS_PATH = Path("data/rag/job_corpus.jsonl")
DEFAULT_PIPELINE_LOG_PATH = DEFAULT_OUTPUT_DIR / "live_pipeline_run.log"
DEFAULT_PIPELINE_STATUS_PATH = DEFAULT_OUTPUT_DIR / "live_pipeline_status.json"
DEFAULT_PROFILE_RESUME_DIR = Path(
    os.environ.get("RESUME_DIR", "data/profile_resumes")
).expanduser()
DEFAULT_SCHEDULER_RUN_HISTORY_PATH = Path(SCHEDULER_RUN_HISTORY_PATH)
DEFAULT_NOTIFICATION_RECORDS_DIR = Path(DEFAULT_NOTIFICATION_RECORDS_DIR)

_PIPELINE_RUN_STATE: Dict[str, Any] = {
    "process": None,
    "log_handle": None,
    "status": "idle",
    "started_at": "",
    "finished_at": "",
    "return_code": None,
    "command": [],
    "output_dir": str(DEFAULT_OUTPUT_DIR),
    "log_path": str(DEFAULT_PIPELINE_LOG_PATH),
    "status_path": str(DEFAULT_PIPELINE_STATUS_PATH),
    "run_id": "",
    "child_pid": None,
    "error": "",
}

ALLOWED_APPLICATION_STATUSES = {
    "OPENED",
    "APPLIED",
    "SAVED",
    "NOT_APPLIED",
    "DISMISSED",
}

APPLICATION_ACTION_OVERLAY_FIELDS = [
    "application_status",
    "application_label",
    "is_applied",
]

ALLOWED_OPERATOR_DECISIONS = {
    "SELECT_RESUME",
}

_RESUME_PREVIEW_PATH_CACHE: Dict[str, str] = {}

def _get_resume_dir() -> Path:
    resume_dir = DEFAULT_PROFILE_RESUME_DIR
    resume_dir.mkdir(parents=True, exist_ok=True)
    return resume_dir


def _sanitize_resume_filename(value: str) -> str:
    raw = str(value or "").strip()
    safe = Path(raw).name

    if not raw or not safe or safe != raw:
        raise ValueError("Invalid resume filename.")

    if Path(safe).suffix.lower() != ".pdf":
        raise ValueError("Only PDF resumes are supported.")

    if re.search(r"[/\\\\]", safe):
        raise ValueError("Invalid resume filename.")

    return safe


def _resume_payload_for_path(path: Path) -> Dict[str, Any]:
    stat = path.stat()
    return {
        "resume_name": path.name,
        "path": str(path),
        "size_bytes": stat.st_size,
        "modified_at": datetime.fromtimestamp(
            stat.st_mtime,
            tz=timezone.utc,
        ).isoformat(timespec="seconds"),
    }


def profile_resumes_payload() -> Dict[str, Any]:
    resume_dir = _get_resume_dir()

    pdf_paths = [path for path in resume_dir.iterdir() if path.is_file() and path.suffix.lower() == ".pdf"]
    pdf_paths.sort(key=lambda path: (-path.stat().st_mtime, path.name.lower()))

    resumes = [_resume_payload_for_path(path) for path in pdf_paths]

    return {
        "ok": True,
        "resume_dir": str(resume_dir),
        "count": len(resumes),
        "resumes": resumes,
    }


def profile_upload_resume_payload(filename: str, file_bytes: bytes) -> Dict[str, Any]:
    resume_dir = _get_resume_dir()
    safe_name = _sanitize_resume_filename(filename)

    if not file_bytes:
        raise ValueError("Uploaded file is empty.")

    target_path = resume_dir / safe_name
    if target_path.exists():
        raise ValueError(f"Resume already exists: {safe_name}")

    target_path.write_bytes(file_bytes)

    return {
        "ok": True,
        "message": "Resume uploaded.",
        "resume": _resume_payload_for_path(target_path),
    }


def profile_delete_resume_payload(resume_name: str) -> Dict[str, Any]:
    resume_dir = _get_resume_dir()
    safe_name = _sanitize_resume_filename(resume_name)
    target_path = resume_dir / safe_name

    if not target_path.exists():
        raise ValueError(f"Resume not found: {safe_name}")

    if not target_path.is_file():
        raise ValueError(f"Resume is not a file: {safe_name}")

    target_path.unlink()

    return {
        "ok": True,
        "message": "Resume deleted.",
        "resume_name": safe_name,
    }

def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _derive_pipeline_log_path(output_dir: Path) -> Path:
    return output_dir / "live_pipeline_run.log"


def _derive_pipeline_status_path(output_dir: Path) -> Path:
    return output_dir / "live_pipeline_status.json"


def _new_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _load_runtime_status_file(path: str) -> Dict[str, Any]:
    status_path = Path(str(path or "")).expanduser()
    if not status_path.exists():
        return {}

    try:
        return json.loads(status_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _job_app():
    import job_app
    return job_app


def _make_args(**kwargs):
    return SimpleNamespace(**kwargs)


def _normalize_pipeline_llm_actions(value: Any) -> str:
    if isinstance(value, list):
        actions = [str(item).strip() for item in value if str(item).strip()]
    else:
        raw = str(value or "").strip()
        actions = [part.strip() for part in raw.split(",") if part.strip()]

    if not actions:
        actions = ["APPLY", "APPLY_REVIEW_VARIANTS"]

    seen: List[str] = []
    for action in actions:
        if action not in seen:
            seen.append(action)

    return ",".join(seen)


def _normalize_delete_seen_data(value: Any) -> str:
    raw = str(value or "").strip().lower()
    if raw in {"yes", "y", "true", "1"}:
        return "yes"
    if raw in {"ask", "prompt"}:
        return "ask"
    return "no"


def _pipeline_status_snapshot() -> Dict[str, Any]:
    process = _PIPELINE_RUN_STATE.get("process")
    log_handle = _PIPELINE_RUN_STATE.get("log_handle")

    if process is not None:
        return_code = process.poll()
        if return_code is None:
            _PIPELINE_RUN_STATE["status"] = "running"
        else:
            _PIPELINE_RUN_STATE["status"] = "succeeded" if return_code == 0 else "failed"
            _PIPELINE_RUN_STATE["finished_at"] = (
                _PIPELINE_RUN_STATE.get("finished_at") or _utc_now()
            )
            _PIPELINE_RUN_STATE["return_code"] = return_code
            _PIPELINE_RUN_STATE["process"] = None
            _PIPELINE_RUN_STATE["child_pid"] = None

            if log_handle is not None:
                try:
                    log_handle.close()
                except Exception:
                    pass
                _PIPELINE_RUN_STATE["log_handle"] = None

    status = _PIPELINE_RUN_STATE.get("status", "idle")
    return {
        "status": status,
        "started_at": _PIPELINE_RUN_STATE.get("started_at", ""),
        "finished_at": _PIPELINE_RUN_STATE.get("finished_at", ""),
        "return_code": _PIPELINE_RUN_STATE.get("return_code"),
        "command": _PIPELINE_RUN_STATE.get("command", []),
        "output_dir": _PIPELINE_RUN_STATE.get("output_dir", str(DEFAULT_OUTPUT_DIR)),
        "log_path": _PIPELINE_RUN_STATE.get("log_path", str(DEFAULT_PIPELINE_LOG_PATH)),
        "status_path": _PIPELINE_RUN_STATE.get("status_path", str(DEFAULT_PIPELINE_STATUS_PATH)),
        "run_id": _PIPELINE_RUN_STATE.get("run_id", ""),
        "child_pid": _PIPELINE_RUN_STATE.get("child_pid"),
        "error": _PIPELINE_RUN_STATE.get("error", ""),
        "is_running": status == "running",
    }

def _write_runtime_status_file(path: Path, payload: Dict[str, Any]) -> None:
    resolved = Path(path).expanduser()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = resolved.with_suffix(resolved.suffix + ".tmp")
    tmp_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    tmp_path.replace(resolved)

def _pid_exists(pid: Any) -> bool:
    try:
        normalized = int(pid)
    except (TypeError, ValueError):
        return False

    if normalized <= 0:
        return False

    try:
        os.kill(normalized, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False

    return True


def _heal_stale_running_runtime_status(
    snapshot: Dict[str, Any],
    runtime_status: Dict[str, Any],
) -> Dict[str, Any]:
    if snapshot.get("is_running"):
        return runtime_status

    if str(runtime_status.get("status", "") or "").strip().lower() != "running":
        return runtime_status

    child_pid = runtime_status.get("child_pid")
    if child_pid and _pid_exists(child_pid):
        return runtime_status

    healed = dict(runtime_status)
    healed["status"] = "failed"
    healed["finished_at"] = healed.get("finished_at") or _utc_now()
    healed["return_code"] = 1

    reason = (
        "Live pipeline is no longer running. "
        "The API server likely restarted or the child process exited unexpectedly."
    )
    healed["error"] = healed.get("error") or reason
    healed["summary_message"] = healed.get("summary_message") or reason
    healed["stage_message"] = reason

    status_path_raw = str(
        snapshot.get("status_path")
        or healed.get("status_path")
        or ""
    ).strip()
    if status_path_raw:
        _write_runtime_status_file(Path(status_path_raw), healed)

    return healed

def stop_live_pipeline_for_server_shutdown(
    reason: str = "Live pipeline stopped because the API server shut down.",
) -> Dict[str, Any]:
    process = _PIPELINE_RUN_STATE.get("process")
    log_handle = _PIPELINE_RUN_STATE.get("log_handle")
    status_path_raw = str(_PIPELINE_RUN_STATE.get("status_path", "") or "").strip()
    status_path = Path(status_path_raw).expanduser() if status_path_raw else None
    finished_at = _utc_now()

    if process is None:
        if log_handle is not None:
            try:
                log_handle.close()
            except Exception:
                pass
            _PIPELINE_RUN_STATE["log_handle"] = None

        return {
            "ok": True,
            "stopped": False,
            "reason": "no_active_process",
        }

    return_code = process.poll()
    was_running = return_code is None

    if was_running:
        process.terminate()
        try:
            return_code = process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            return_code = process.wait(timeout=5)

    if log_handle is not None:
        try:
            log_handle.close()
        except Exception:
            pass

    _PIPELINE_RUN_STATE["process"] = None
    _PIPELINE_RUN_STATE["child_pid"] = None
    _PIPELINE_RUN_STATE["log_handle"] = None
    _PIPELINE_RUN_STATE["finished_at"] = finished_at
    _PIPELINE_RUN_STATE["return_code"] = return_code if return_code is not None else 1

    if was_running:
        _PIPELINE_RUN_STATE["status"] = "failed"
        _PIPELINE_RUN_STATE["error"] = reason
    else:
        _PIPELINE_RUN_STATE["status"] = "succeeded" if return_code == 0 else "failed"
        _PIPELINE_RUN_STATE["error"] = "" if return_code == 0 else reason

    if status_path and status_path.exists():
        runtime_payload = _load_runtime_status_file(str(status_path))
        if runtime_payload:
            runtime_payload["finished_at"] = finished_at
            runtime_payload["return_code"] = return_code if return_code is not None else 1

            if was_running:
                runtime_payload["status"] = "failed"
                runtime_payload["error"] = reason
                runtime_payload["summary_message"] = reason
                runtime_payload["stage_message"] = reason
            else:
                runtime_payload["status"] = "succeeded" if return_code == 0 else "failed"
                if return_code != 0:
                    runtime_payload["error"] = reason
                    runtime_payload["summary_message"] = runtime_payload.get("summary_message") or reason
                    runtime_payload["stage_message"] = runtime_payload.get("stage_message") or reason

            _write_runtime_status_file(status_path, runtime_payload)

    return {
        "ok": True,
        "stopped": was_running,
        "return_code": return_code,
        "status_path": str(status_path) if status_path else "",
    }


def _runtime_status_is_stale_startup(
    snapshot: Dict[str, Any],
    runtime_status: Dict[str, Any],
) -> bool:
    if snapshot.get("is_running"):
        return False

    if str(runtime_status.get("status", "") or "").strip().lower() != "running":
        return False

    if str(runtime_status.get("current_stage", "") or "").strip().lower() != "startup":
        return False

    if str(runtime_status.get("stage_message", "") or "").strip() != "Launching pipeline subprocess":
        return False

    if list(runtime_status.get("completed_stages", []) or []):
        return False

    if dict(runtime_status.get("counts", {}) or {}):
        return False

    if runtime_status.get("final_job_count") not in (None, "", 0):
        return False

    return True

def pipeline_status_payload() -> Dict[str, Any]:
    snapshot = _pipeline_status_snapshot()
    runtime_status = _load_runtime_status_file(snapshot.get("status_path", ""))

    if runtime_status and _runtime_status_is_stale_startup(snapshot, runtime_status):
        runtime_status = {}

    if runtime_status:
        runtime_status = _heal_stale_running_runtime_status(snapshot, runtime_status)

    merged = dict(snapshot)
    if runtime_status:
        if merged.get("status") == "idle":
            merged["status"] = runtime_status.get("status", merged["status"])

        if not merged.get("started_at"):
            merged["started_at"] = runtime_status.get("started_at", "")
        if not merged.get("finished_at"):
            merged["finished_at"] = runtime_status.get("finished_at", "")
        if merged.get("return_code") is None:
            merged["return_code"] = runtime_status.get("return_code")
        if not merged.get("error"):
            merged["error"] = runtime_status.get("error", "")

        merged.update({
            "run_id": runtime_status.get("run_id", merged.get("run_id", "")),
            "output_dir": runtime_status.get("output_dir", merged.get("output_dir", "")),
            "log_path": runtime_status.get("log_path", merged.get("log_path", "")),
            "status_path": runtime_status.get("status_path", merged.get("status_path", "")),
            "current_stage": runtime_status.get("current_stage", ""),
            "completed_stages": runtime_status.get("completed_stages", []),
            "stage_order": runtime_status.get("stage_order", []),
            "stage_started_at": runtime_status.get("stage_started_at", ""),
            "stage_message": runtime_status.get("stage_message", ""),
            "counts": runtime_status.get("counts", {}),
            "summary_message": runtime_status.get("summary_message", ""),
            "final_job_count": runtime_status.get("final_job_count"),
            "config": runtime_status.get("config", {}),
        })

        merged["is_running"] = merged.get("status") == "running"

    return {
        "ok": True,
        "pipeline": merged,
    }

def scheduler_jobs_payload() -> Dict[str, Any]:
    return {
        "ok": True,
        "jobs": get_scheduled_job_definitions(),
    }


def scheduler_job_command_payload(
    *,
    job_name: str,
    planning_only: bool = False,
    run_application_planning: bool = True,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    job_limit: int = 50,
    job_packet_limit: int = 0,
    llm_actions: Any = "APPLY,APPLY_REVIEW_VARIANTS",
    generate_tailoring: bool = False,
    generate_llm_tailoring: bool = False,
    refresh_llm_tailoring: bool = False,
    generate_llm_fallback: bool = False,
    delete_seen_data: str = "no",
) -> Dict[str, Any]:
    definition = get_scheduled_job_definition(job_name)

    command = build_scheduled_job_command(
        job_name,
        run_application_planning=bool(run_application_planning),
        planning_only=bool(planning_only),
        output_dir=output_dir,
        job_limit=int(job_limit),
        job_packet_limit=int(job_packet_limit),
        llm_actions=llm_actions,
        generate_tailoring=bool(generate_tailoring),
        generate_llm_tailoring=bool(generate_llm_tailoring),
        refresh_llm_tailoring=bool(refresh_llm_tailoring),
        generate_llm_fallback=bool(generate_llm_fallback),
        delete_seen_data=str(delete_seen_data or "no"),
    )

    return {
        "ok": True,
        "job": definition,
        "command": command,
        "command_text": " ".join(command),
        "options": {
            "planning_only": bool(planning_only),
            "run_application_planning": bool(run_application_planning),
            "output_dir": str(output_dir),
            "job_limit": int(job_limit),
            "job_packet_limit": int(job_packet_limit),
            "llm_actions": llm_actions,
            "generate_tailoring": bool(generate_tailoring),
            "generate_llm_tailoring": bool(generate_llm_tailoring),
            "refresh_llm_tailoring": bool(refresh_llm_tailoring),
            "generate_llm_fallback": bool(generate_llm_fallback),
            "delete_seen_data": str(delete_seen_data or "no"),
        },
    }

def _augment_launchd_config_exists(payload: Dict[str, Any]) -> Dict[str, Any]:
    item = dict(payload)
    item["plist_exists"] = Path(item["plist_path"]).expanduser().exists()
    item["stdout_log_exists"] = Path(item["stdout_log_path"]).expanduser().exists()
    item["stderr_log_exists"] = Path(item["stderr_log_path"]).expanduser().exists()
    return item

def scheduler_launchd_config_payload(
    *,
    job_name: str = "",
    planning_only: bool = False,
    run_application_planning: bool = True,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    job_limit: int = 50,
    job_packet_limit: int = 0,
    llm_actions: Any = "APPLY,APPLY_REVIEW_VARIANTS",
    generate_tailoring: bool = False,
    generate_llm_tailoring: bool = False,
    refresh_llm_tailoring: bool = False,
    generate_llm_fallback: bool = False,
    delete_seen_data: str = "no",
    sync_postgres_run_history: bool = False,
    require_postgres_run_history_sync: bool = False,
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    allow_contract_drift: bool = False,
    launchd_interval_seconds: int = DEFAULT_LAUNCHD_INTERVAL_SECONDS,
    launchd_out_dir: Path = DEFAULT_LAUNCHD_OUT_DIR,
    launchd_log_dir: Path = DEFAULT_LAUNCHD_LOG_DIR,
    launchd_label_prefix: str = DEFAULT_LAUNCHD_LABEL_PREFIX,
) -> Dict[str, Any]:
    common_kwargs = {
        "run_application_planning": bool(run_application_planning),
        "output_dir": output_dir,
        "job_limit": int(job_limit),
        "job_packet_limit": int(job_packet_limit),
        "llm_actions": llm_actions,
        "generate_tailoring": bool(generate_tailoring),
        "generate_llm_tailoring": bool(generate_llm_tailoring),
        "refresh_llm_tailoring": bool(refresh_llm_tailoring),
        "generate_llm_fallback": bool(generate_llm_fallback),
        "delete_seen_data": str(delete_seen_data or "no"),
        "history_path": DEFAULT_SCHEDULER_RUN_HISTORY_PATH,
        "sync_postgres_run_history": bool(sync_postgres_run_history),
        "require_postgres_run_history_sync": bool(require_postgres_run_history_sync),
        "database_url_env": database_url_env,
        "psql_bin": psql_bin,
        "allow_contract_drift": bool(allow_contract_drift),
        "launchd_interval_seconds": int(launchd_interval_seconds),
        "launchd_out_dir": launchd_out_dir,
        "launchd_log_dir": launchd_log_dir,
        "launchd_label_prefix": launchd_label_prefix,
    }

    if str(job_name or "").strip():
        item = _augment_launchd_config_exists(
            build_scheduler_launchd_plist_payload(
                job_name=job_name,
                planning_only=bool(planning_only),
                **common_kwargs,
            )
        )
        return {
            "ok": True,
            "mode": "single",
            "item": item,
        }

    items = [
        _augment_launchd_config_exists(
            build_scheduler_launchd_plist_payload(
                job_name="agent_discovery",
                planning_only=False,
                **common_kwargs,
            )
        ),
        _augment_launchd_config_exists(
            build_scheduler_launchd_plist_payload(
                job_name="live_pipeline",
                planning_only=True,
                **common_kwargs,
            )
        ),
    ]

    return {
        "ok": True,
        "mode": "default_pair",
        "items": items,
    }

def scheduler_launchd_agent_status_payload(
    *,
    job_name: str = "",
    planning_only: bool = False,
    run_application_planning: bool = True,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    job_limit: int = 50,
    job_packet_limit: int = 0,
    llm_actions: Any = "APPLY,APPLY_REVIEW_VARIANTS",
    generate_tailoring: bool = False,
    generate_llm_tailoring: bool = False,
    refresh_llm_tailoring: bool = False,
    generate_llm_fallback: bool = False,
    delete_seen_data: str = "no",
    sync_postgres_run_history: bool = False,
    require_postgres_run_history_sync: bool = False,
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    allow_contract_drift: bool = False,
    launchd_interval_seconds: int = DEFAULT_LAUNCHD_INTERVAL_SECONDS,
    launchd_out_dir: Path = DEFAULT_LAUNCHD_OUT_DIR,
    launchd_log_dir: Path = DEFAULT_LAUNCHD_LOG_DIR,
    launchd_label_prefix: str = DEFAULT_LAUNCHD_LABEL_PREFIX,
    launchd_agent_dir: Path = DEFAULT_LAUNCHD_AGENT_DIR,
    launchd_target: str = DEFAULT_LAUNCHD_TARGET,
) -> Dict[str, Any]:
    common_kwargs = {
        "run_application_planning": bool(run_application_planning),
        "output_dir": output_dir,
        "job_limit": int(job_limit),
        "job_packet_limit": int(job_packet_limit),
        "llm_actions": llm_actions,
        "generate_tailoring": bool(generate_tailoring),
        "generate_llm_tailoring": bool(generate_llm_tailoring),
        "refresh_llm_tailoring": bool(refresh_llm_tailoring),
        "generate_llm_fallback": bool(generate_llm_fallback),
        "delete_seen_data": str(delete_seen_data or "no"),
        "history_path": DEFAULT_SCHEDULER_RUN_HISTORY_PATH,
        "sync_postgres_run_history": bool(sync_postgres_run_history),
        "require_postgres_run_history_sync": bool(require_postgres_run_history_sync),
        "database_url_env": database_url_env,
        "psql_bin": psql_bin,
        "allow_contract_drift": bool(allow_contract_drift),
        "launchd_interval_seconds": int(launchd_interval_seconds),
        "launchd_out_dir": launchd_out_dir,
        "launchd_log_dir": launchd_log_dir,
        "launchd_label_prefix": launchd_label_prefix,
        "launchd_agent_dir": launchd_agent_dir,
        "launchd_target": launchd_target,
    }

    if str(job_name or "").strip():
        return {
            "ok": True,
            "mode": "single",
            "item": get_scheduler_launchd_agent_status(
                job_name=job_name,
                planning_only=bool(planning_only),
                **common_kwargs,
            ),
        }

    items = [
        get_scheduler_launchd_agent_status(
            job_name="agent_discovery",
            planning_only=False,
            **common_kwargs,
        ),
        get_scheduler_launchd_agent_status(
            job_name="live_pipeline",
            planning_only=True,
            **common_kwargs,
        ),
    ]

    return {
        "ok": True,
        "mode": "default_pair",
        "items": items,
    }

def scheduler_postgres_status_payload(
    *,
    limit: int = 10,
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
) -> Dict[str, Any]:
    postgres_payload = get_scheduler_postgres_status_payload(
        limit=limit,
        database_url="",
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        print_only=False,
    )

    jsonl_rows = _load_scheduler_history_rows(DEFAULT_SCHEDULER_RUN_HISTORY_PATH)
    postgres_block = dict(postgres_payload.get("postgres", {}) or {})
    postgres_history_row_count = int(postgres_block.get("run_history_count", 0) or 0)

    return {
        "ok": True,
        "query_limit": int(limit),
        "history_jsonl_path": str(DEFAULT_SCHEDULER_RUN_HISTORY_PATH),
        "history_jsonl_row_count": len(jsonl_rows),
        "history_postgres_row_count": postgres_history_row_count,
        "history_count_matches_jsonl": postgres_history_row_count == len(jsonl_rows),
        "postgres_command_text": postgres_payload["command_text"],
        "postgres": postgres_block,
    }

def scheduler_operator_summary_payload(
    *,
    limit: int = 5,
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
) -> Dict[str, Any]:
    normalized_limit = max(int(limit), 1)

    contract = scheduler_contract_health_payload()
    postgres_payload = scheduler_postgres_status_payload(
        limit=normalized_limit,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
    )

    jsonl_rows = _load_scheduler_history_rows(DEFAULT_SCHEDULER_RUN_HISTORY_PATH)
    latest_jsonl_rows = jsonl_rows[:normalized_limit]

    postgres_block = dict(postgres_payload.get("postgres", {}) or {})

    return {
        "ok": True,
        "limit": normalized_limit,
        "contract_health": contract,
        "history": {
            "jsonl_path": str(DEFAULT_SCHEDULER_RUN_HISTORY_PATH),
            "jsonl_row_count": postgres_payload["history_jsonl_row_count"],
            "postgres_row_count": postgres_payload["history_postgres_row_count"],
            "count_matches": postgres_payload["history_count_matches_jsonl"],
        },
        "latest_runs_by_job": postgres_block.get("latest_runs_by_job", []),
        "recent_postgres_runs": postgres_block.get("recent_runs", []),
        "recent_jsonl_runs": latest_jsonl_rows,
        "postgres_summary": {
            "job_definition_count": postgres_block.get("job_definition_count", 0),
            "active_job_count": postgres_block.get("active_job_count", 0),
            "run_history_count": postgres_block.get("run_history_count", 0),
            "success_count": postgres_block.get("success_count", 0),
            "failure_count": postgres_block.get("failure_count", 0),
        },
        "postgres_command_text": postgres_payload["postgres_command_text"],
    }


def _normalize_scheduler_filter_text(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def _load_scheduler_history_rows(
    history_path: Path = DEFAULT_SCHEDULER_RUN_HISTORY_PATH,
) -> List[Dict[str, Any]]:
    if not history_path.exists():
        return []

    rows: List[Dict[str, Any]] = []

    with history_path.open("r", encoding="utf-8") as f:
        for line_number, raw_line in enumerate(f, start=1):
            line = raw_line.strip()
            if not line:
                continue

            try:
                payload = json.loads(line)
            except Exception:
                continue

            if not isinstance(payload, dict):
                continue

            row = dict(payload)
            row["_line_number"] = line_number
            rows.append(row)

    rows.sort(
        key=lambda row: (
            str(row.get("started_at", "") or ""),
            str(row.get("run_id", "") or ""),
            int(row.get("_line_number", 0) or 0),
        ),
        reverse=True,
    )
    return rows


def scheduler_history_payload(
    history_path: Path = DEFAULT_SCHEDULER_RUN_HISTORY_PATH,
    job_name: str = "",
    status: str = "",
    limit: int = 20,
) -> Dict[str, Any]:
    rows = _load_scheduler_history_rows(history_path)

    normalized_job_name = _normalize_scheduler_filter_text(job_name)
    normalized_status = _normalize_scheduler_filter_text(status)

    if normalized_job_name:
        rows = [
            row for row in rows
            if _normalize_scheduler_filter_text(row.get("job_name", "")) == normalized_job_name
        ]

    if normalized_status:
        rows = [
            row for row in rows
            if _normalize_scheduler_filter_text(row.get("status", "")) == normalized_status
        ]

    selected = rows[: max(int(limit), 0)]

    return {
        "ok": True,
        "history_path": str(history_path),
        "filters": {
            "job_name": job_name,
            "status": status,
            "limit": limit,
        },
        "total_matching_rows": len(rows),
        "rows": selected,
        "count": len(selected),
    }

def _load_notification_rows(
    notification_dir: Path = DEFAULT_NOTIFICATION_RECORDS_DIR,
) -> List[Dict[str, Any]]:
    if not notification_dir.exists() or not notification_dir.is_dir():
        return []

    rows: List[Dict[str, Any]] = []

    for path in notification_dir.glob("*.json"):
        if not path.is_file():
            continue

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue

        if not isinstance(payload, dict):
            continue

        row = dict(payload)
        row["_path"] = str(path)
        rows.append(row)

    rows.sort(
        key=lambda row: (
            str(row.get("created_at", "") or ""),
            str(row.get("notification_id", "") or ""),
        ),
        reverse=True,
    )
    return rows


def _normalize_notification_read_flag(value: Any) -> bool:
    if isinstance(value, bool):
        return value

    if value is None:
        raw = ""
    else:
        raw = str(value).strip().lower()

    if raw in {"1", "true", "yes", "y", "read"}:
        return True

    if raw in {"0", "false", "no", "n", "off", "unread"}:
        return False

    raise ValueError("is_read must be a boolean-like value.")


def _normalize_optional_notification_read_filter(value: Any) -> Any:
    raw = str(value or "").strip()
    if not raw:
        return None
    return _normalize_notification_read_flag(raw)

def _load_latest_notification_state_overlay() -> Dict[str, Dict[str, Any]]:
    meta_payload = get_notification_state_postgres_status_payload(
        limit=1,
        database_url="",
        database_url_env="DATABASE_URL",
        psql_bin="psql",
        print_only=False,
    )
    meta_block = dict(meta_payload.get("postgres", {}) or {})
    query_limit = max(int(meta_block.get("latest_state_count", 0) or 0), 1)

    postgres_payload = get_notification_state_postgres_status_payload(
        limit=query_limit,
        database_url="",
        database_url_env="DATABASE_URL",
        psql_bin="psql",
        print_only=False,
    )
    postgres_block = dict(postgres_payload.get("postgres", {}) or {})
    postgres_rows = list(postgres_block.get("latest_rows", []) or [])

    latest_overlay: Dict[str, Dict[str, Any]] = {}
    for row in postgres_rows:
        notification_id = _clean_text(row.get("notification_id"))
        if not notification_id:
            continue

        latest_overlay[notification_id] = {
            "is_read": bool(row.get("is_read", False)),
            "state_timestamp": _clean_text(row.get("state_timestamp")),
        }

    return latest_overlay

def _apply_notification_state_overlay(
    rows: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    latest_by_notification_id = _load_latest_notification_state_overlay()
    overlaid_rows: List[Dict[str, Any]] = []

    for row in rows:
        merged = dict(row)
        merged["is_read"] = bool(merged.get("is_read", False))
        merged["read_state_timestamp"] = ""

        notification_id = str(merged.get("notification_id", "") or "").strip()
        overlay = latest_by_notification_id.get(notification_id)

        if overlay:
            merged["is_read"] = bool(overlay.get("is_read", False))
            merged["read_state_timestamp"] = str(overlay.get("state_timestamp", "") or "").strip()

        overlaid_rows.append(merged)

    return overlaid_rows


def notifications_payload(
    notification_dir: Path = DEFAULT_NOTIFICATION_RECORDS_DIR,
    job_name: str = "",
    level: str = "",
    delivery_status: str = "",
    is_read: str = "",
    limit: int = 20,
) -> Dict[str, Any]:
    rows = _apply_notification_state_overlay(
        _load_notification_rows(notification_dir),
    )

    normalized_job_name = _normalize_scheduler_filter_text(job_name)
    normalized_level = _normalize_scheduler_filter_text(level)
    normalized_delivery_status = _normalize_scheduler_filter_text(delivery_status)
    normalized_is_read = _normalize_optional_notification_read_filter(is_read)

    if normalized_job_name:
        rows = [
            row for row in rows
            if _normalize_scheduler_filter_text(row.get("job_name", "")) == normalized_job_name
        ]

    if normalized_level:
        rows = [
            row for row in rows
            if _normalize_scheduler_filter_text(row.get("level", "")) == normalized_level
        ]

    if normalized_delivery_status:
        rows = [
            row for row in rows
            if _normalize_scheduler_filter_text(row.get("delivery_status", "")) == normalized_delivery_status
        ]

    if normalized_is_read is not None:
        rows = [
            row for row in rows
            if bool(row.get("is_read", False)) == normalized_is_read
        ]

    selected = rows[: max(int(limit), 0)]

    return {
        "ok": True,
        "notification_dir": str(notification_dir),
        "filters": {
            "job_name": job_name,
            "level": level,
            "delivery_status": delivery_status,
            "is_read": is_read,
            "limit": limit,
        },
        "total_matching_rows": len(rows),
        "rows": selected,
        "count": len(selected),
    }


def notifications_summary_payload(
    notification_dir: Path = DEFAULT_NOTIFICATION_RECORDS_DIR,
    limit: int = 10,
) -> Dict[str, Any]:
    rows = _apply_notification_state_overlay(
        _load_notification_rows(notification_dir),
    )
    selected = rows[: max(int(limit), 0)]

    level_counts = Counter(
        str(row.get("level", "") or "<empty>")
        for row in rows
    )
    delivery_status_counts = Counter(
        str(row.get("delivery_status", "") or "<empty>")
        for row in rows
    )
    job_name_counts = Counter(
        str(row.get("job_name", "") or "<empty>")
        for row in rows
    )

    unread_count = sum(1 for row in rows if not bool(row.get("is_read", False)))
    read_count = len(rows) - unread_count

    return {
        "ok": True,
        "total_rows": len(rows),
        "read_count": read_count,
        "unread_count": unread_count,
        "level_counts": dict(sorted(level_counts.items())),
        "delivery_status_counts": dict(sorted(delivery_status_counts.items())),
        "job_name_counts": dict(sorted(job_name_counts.items())),
        "recent_notifications": selected,
        "count": len(selected),
    }


def notifications_unread_count_payload(
    notification_dir: Path = DEFAULT_NOTIFICATION_RECORDS_DIR,
) -> Dict[str, Any]:
    rows = _apply_notification_state_overlay(
        _load_notification_rows(notification_dir),
    )

    unread_count = sum(1 for row in rows if not bool(row.get("is_read", False)))
    read_count = len(rows) - unread_count

    return {
        "ok": True,
        "total_rows": len(rows),
        "read_count": read_count,
        "unread_count": unread_count,
    }

def _dual_write_notification_state_postgres(row: Dict[str, Any]) -> Dict[str, Any]:
    database_url = str(os.environ.get("DATABASE_URL", "") or "").strip()
    if not database_url:
        return {
            "attempted": False,
            "ok": False,
            "skipped": "missing_database_url",
            "table_name": "notification_state_events",
        }

    try:
        payload = insert_notification_state_row_to_postgres(
            record=row,
            database_url="",
            database_url_env="DATABASE_URL",
            psql_bin="psql",
            print_only=False,
            allow_contract_drift=False,
        )
        return {
            "attempted": True,
            "ok": True,
            "table_name": payload.get("table_name", "notification_state_events"),
            "state_id": str(payload.get("row", {}).get("state_id", "") or ""),
            "contract_health_ok": bool(payload.get("contract_health_ok", False)),
            "command_text": str(payload.get("command_text", "") or ""),
        }
    except SystemExit as exc:
        return {
            "attempted": True,
            "ok": False,
            "table_name": "notification_state_events",
            "error_type": "SystemExit",
            "error": str(exc),
        }
    except Exception as exc:
        return {
            "attempted": True,
            "ok": False,
            "table_name": "notification_state_events",
            "error_type": exc.__class__.__name__,
            "error": str(exc),
        }
    
def record_notification_read_state_payload(
    notification_dir: Path = DEFAULT_NOTIFICATION_RECORDS_DIR,
    *,
    notification_id: str = "",
    is_read: Any = True,
) -> Dict[str, Any]:
    clean_notification_id = str(notification_id or "").strip()
    if not clean_notification_id:
        raise ValueError("notification_id is required.")

    rows = _apply_notification_state_overlay(
        _load_notification_rows(notification_dir),
    )

    target_notification = None
    for row in rows:
        if str(row.get("notification_id", "") or "").strip() == clean_notification_id:
            target_notification = dict(row)
            break

    if target_notification is None:
        raise ValueError(f"Notification not found: {clean_notification_id}")

    normalized_is_read = _normalize_notification_read_flag(is_read)

    state_row = {
        "state_timestamp": datetime.now(timezone.utc).isoformat(timespec="microseconds"),
        "notification_id": clean_notification_id,
        "is_read": str(normalized_is_read),
    }

    postgres_write = _dual_write_notification_state_postgres(state_row)

    target_notification["is_read"] = normalized_is_read
    target_notification["read_state_timestamp"] = state_row["state_timestamp"]

    return {
        "ok": True,
        "state_row": state_row,
        "notification": target_notification,
    }

def scheduler_storage_contract_payload(
    *,
    include_sql: bool = False,
    include_generated_seed_sql: bool = False,
    include_generated_init_sql: bool = False,
) -> Dict[str, Any]:
    schema_payload = scheduler_schema_sql_payload()
    seed_payload = scheduler_seed_sql_payload()
    init_payload = scheduler_init_sql_payload()
    seed_generation_payload = scheduler_seed_sql_generation_payload()
    init_generation_payload = scheduler_init_sql_generation_payload()

    payload = {
        "ok": True,
        "tables": scheduler_postgres_table_specs(),
        "seed_rows": {
            "scheduler_job_definitions": scheduler_job_definition_seed_rows(),
        },
        "schema_sql_path": schema_payload["path"],
        "seed_sql_path": seed_payload["path"],
        "init_sql_path": init_payload["path"],
        "seed_sql_matches_artifact": seed_generation_payload["matches_artifact"],
        "init_sql_matches_artifact": init_generation_payload["matches_artifact"],
        "include_sql": bool(include_sql),
        "include_generated_seed_sql": bool(include_generated_seed_sql),
        "include_generated_init_sql": bool(include_generated_init_sql),
    }

    if include_sql:
        payload["schema_sql"] = schema_payload["sql"]
        payload["seed_sql"] = seed_payload["sql"]
        payload["init_sql"] = init_payload["sql"]

    if include_generated_seed_sql:
        payload["seed_sql_generated"] = seed_generation_payload["generated_sql"]

    if include_generated_init_sql:
        payload["init_sql_generated"] = init_generation_payload["generated_sql"]

    return payload

def run_live_pipeline_payload(
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    log_path: Path = DEFAULT_PIPELINE_LOG_PATH,
    job_limit: int = 50,
    job_packet_limit: int = 0,
    llm_actions: Any = "APPLY,APPLY_REVIEW_VARIANTS",
    generate_tailoring: bool = False,
    generate_llm_tailoring: bool = False,
    refresh_llm_tailoring: bool = False,
    generate_llm_fallback: bool = False,
    generate_llm_adjudication: bool = False,
    planning_only: bool = False,
    delete_seen_data: str = "no",
) -> Dict[str, Any]:
    snapshot = _pipeline_status_snapshot()
    if snapshot.get("is_running"):
        raise ValueError("A live pipeline run is already in progress.")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    canonical_log_path = _derive_pipeline_log_path(output_dir)
    canonical_status_path = _derive_pipeline_status_path(output_dir)
    run_id = _new_run_id()

    normalized_llm_actions = _normalize_pipeline_llm_actions(llm_actions)
    normalized_delete_seen_data = _normalize_delete_seen_data(delete_seen_data)

    ja = _job_app()
    effective_generate_llm_adjudication = bool(generate_llm_adjudication)

    args = _make_args(
        run_application_planning=True,
        job_limit=int(job_limit),
        job_packet_limit=int(job_packet_limit),
        output_dir=str(output_dir),
        llm_actions=normalized_llm_actions,
        generate_tailoring=bool(generate_tailoring),
        generate_llm_tailoring=bool(generate_llm_tailoring),
        refresh_llm_tailoring=bool(refresh_llm_tailoring),
        generate_llm_fallback=bool(generate_llm_fallback),
        generate_llm_adjudication=effective_generate_llm_adjudication,
        delete_seen_data=normalized_delete_seen_data,
    )
    cmd = ja._build_main_cmd(args, planning_only=bool(planning_only))

    runtime_payload = {
        "run_id": run_id,
        "child_pid": None,
        "status": "running",
        "started_at": _utc_now(),
        "finished_at": "",
        "current_stage": "startup",
        "completed_stages": [],
        "stage_order": [
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
            "sheet_export",
            "finalization",
        ],
        "stage_started_at": _utc_now(),
        "stage_message": "Launching pipeline subprocess",
        "counts": {},
        "summary_message": "",
        "final_job_count": None,
        "return_code": None,
        "error": "",
        "output_dir": str(output_dir),
        "log_path": str(canonical_log_path),
        "status_path": str(canonical_status_path),
        "config": {
            "planning_only": bool(planning_only),
            "job_limit": int(job_limit),
            "job_packet_limit": int(job_packet_limit),
            "llm_actions": normalized_llm_actions.split(","),
            "generate_tailoring": bool(generate_tailoring),
            "generate_llm_tailoring": bool(generate_llm_tailoring),
            "refresh_llm_tailoring": bool(refresh_llm_tailoring),
            "generate_llm_fallback": bool(generate_llm_fallback),
            "generate_llm_adjudication": effective_generate_llm_adjudication,
            "delete_seen_data": normalized_delete_seen_data,
        },
    }
    canonical_status_path.write_text(
        json.dumps(runtime_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    log_handle = canonical_log_path.open("w", encoding="utf-8", buffering=1)

    child_env = dict(os.environ)
    child_env["JOB_APP_PIPELINE_STATUS_PATH"] = str(canonical_status_path)
    child_env["JOB_APP_PIPELINE_RUN_ID"] = run_id

    try:
        process = subprocess.Popen(
            cmd,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            env=child_env,
        )
    except Exception as exc:
        log_handle.close()
        runtime_payload["status"] = "failed"
        runtime_payload["finished_at"] = _utc_now()
        runtime_payload["return_code"] = 1
        runtime_payload["error"] = repr(exc)
        runtime_payload["summary_message"] = "Failed to launch pipeline subprocess"
        canonical_status_path.write_text(
            json.dumps(runtime_payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        raise
    
    runtime_payload["child_pid"] = process.pid
    _write_runtime_status_file(canonical_status_path, runtime_payload)
    _PIPELINE_RUN_STATE["process"] = process
    _PIPELINE_RUN_STATE["log_handle"] = log_handle
    _PIPELINE_RUN_STATE["status"] = "running"
    _PIPELINE_RUN_STATE["started_at"] = _utc_now()
    _PIPELINE_RUN_STATE["finished_at"] = ""
    _PIPELINE_RUN_STATE["return_code"] = None
    _PIPELINE_RUN_STATE["command"] = cmd
    _PIPELINE_RUN_STATE["output_dir"] = str(output_dir)
    _PIPELINE_RUN_STATE["log_path"] = str(canonical_log_path)
    _PIPELINE_RUN_STATE["status_path"] = str(canonical_status_path)
    _PIPELINE_RUN_STATE["run_id"] = run_id
    _PIPELINE_RUN_STATE["child_pid"] = process.pid
    _PIPELINE_RUN_STATE["error"] = ""

    return {
        "ok": True,
        "message": "Live pipeline started.",
        "pipeline": pipeline_status_payload()["pipeline"],
    }

def _clean_text(value: Any) -> str:
    return str(value or "").strip()

def _normalize_selected_patch_candidate_ids(value: Any) -> List[str]:
    if isinstance(value, list):
        raw_items = value
    else:
        raw_text = _clean_text(value)
        if not raw_text:
            raw_items = []
        else:
            try:
                parsed = json.loads(raw_text)
                raw_items = parsed if isinstance(parsed, list) else [raw_text]
            except Exception:
                raw_items = [part.strip() for part in raw_text.split(",") if part.strip()]

    normalized: List[str] = []
    seen = set()

    for item in raw_items:
        candidate_id = _clean_text(item)
        if not candidate_id or candidate_id in seen:
            continue
        seen.add(candidate_id)
        normalized.append(candidate_id)

    return normalized


def _serialize_selected_patch_candidate_ids(value: Any) -> str:
    return json.dumps(
        _normalize_selected_patch_candidate_ids(value),
        ensure_ascii=False,
    )


def _load_tailoring_json_artifact(path: Path) -> Dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Tailoring artifact must be a JSON object: {path}")
    return data

def _infer_packet_json_path_from_tailoring_artifact(artifact_path: Path) -> Path:
    name = artifact_path.name
    suffix = "__tailoring.json"
    if not name.endswith(suffix):
        return Path("")
    return artifact_path.with_name(f"{name[:-len(suffix)]}.json")


def _artifact_needs_operator_rehydration(payload_data: Dict[str, Any]) -> bool:
    replacement_candidates = list(payload_data.get("replacement_candidates", []) or [])
    if replacement_candidates:
        return False

    return any(
        [
            list(payload_data.get("rewrite_candidates", []) or []),
            list(payload_data.get("bullet_reuse_candidates", []) or []),
            list(payload_data.get("edit_cards", []) or []),
            list(payload_data.get("top_edit_priorities", []) or []),
            list(payload_data.get("bullet_diagnoses", []) or []),
        ]
    )


def _rehydrate_legacy_tailoring_operator_payload(
    artifact_path: Path,
    payload_data: Dict[str, Any],
) -> Dict[str, Any]:
    data = dict(payload_data)

    if not _artifact_needs_operator_rehydration(data):
        return data

    packet_path = _infer_packet_json_path_from_tailoring_artifact(artifact_path)
    if not packet_path or not packet_path.exists() or not packet_path.is_file():
        return data

    try:
        from src.tailoring.packet_support import _load_packet
        from src.tailoring.rendering import _build_payload, _build_operator_markdown_payload

        packet = _load_packet(packet_path)
        rebuilt_base = _build_payload(packet, include_llm_prompts=False)
        rebuilt_operator = _build_operator_markdown_payload(rebuilt_base, None)
    except Exception:
        return data

    merged = dict(data)
    merged.update(rebuilt_operator)
    return merged

def _tailoring_artifact_candidate_ids(payload: Dict[str, Any]) -> List[str]:
    candidate_ids: List[str] = []
    seen = set()

    for row in list(payload.get("replacement_candidates", []) or []):
        candidate_id = _clean_text(row.get("candidate_id"))
        if not candidate_id or candidate_id in seen:
            continue
        seen.add(candidate_id)
        candidate_ids.append(candidate_id)

    return candidate_ids

def _default_selected_candidate_ids_from_replacement_plan(payload: Dict[str, Any]) -> List[str]:
    selected_ids: List[str] = []
    seen = set()

    for row in list(payload.get("app_ready_replacements", []) or []):
        candidate_id = _clean_text(row.get("replacement_candidate_id"))
        if not candidate_id or candidate_id in seen:
            continue
        seen.add(candidate_id)
        selected_ids.append(candidate_id)

    return selected_ids

def _tailoring_artifact_signature(payload: Dict[str, Any]) -> str:
    job = payload.get("job", {}) or {}
    selection = payload.get("selection", {}) or {}

    signature_payload = {
        "company": _clean_text(job.get("company")),
        "title": _clean_text(job.get("title")),
        "selected_resume": _clean_text(selection.get("selected_resume")),
        "replacement_candidate_ids": sorted(_tailoring_artifact_candidate_ids(payload)),
    }

    blob = json.dumps(signature_payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()[:16]

def _load_latest_patch_selection_overlay() -> Dict[str, Dict[str, Any]]:
    meta_payload = get_patch_selections_postgres_status_payload(
        limit=1,
        database_url="",
        database_url_env="DATABASE_URL",
        psql_bin="psql",
        print_only=False,
    )
    meta_block = dict(meta_payload.get("postgres", {}) or {})
    query_limit = max(int(meta_block.get("latest_state_count", 0) or 0), 1)

    postgres_payload = get_patch_selections_postgres_status_payload(
        limit=query_limit,
        database_url="",
        database_url_env="DATABASE_URL",
        psql_bin="psql",
        print_only=False,
    )
    postgres_block = dict(postgres_payload.get("postgres", {}) or {})
    postgres_rows = list(postgres_block.get("latest_rows", []) or [])

    latest_by_path: Dict[str, Dict[str, Any]] = {}
    for row in postgres_rows:
        artifact_path = _clean_text(row.get("tailoring_json_path"))
        if not artifact_path:
            continue

        latest_by_path[artifact_path] = {
            "selection_timestamp": _clean_text(row.get("selection_timestamp")),
            "job_doc_id": _clean_text(row.get("job_doc_id")),
            "queue_rank": _clean_text(row.get("queue_rank")),
            "job_company": _clean_text(row.get("job_company")),
            "job_title": _clean_text(row.get("job_title")),
            "selected_resume": _clean_text(row.get("selected_resume")),
            "tailoring_json_path": artifact_path,
            "artifact_signature": _clean_text(row.get("artifact_signature")),
            "selected_candidate_ids_json": row.get("selected_candidate_ids_json", []),
            "note": _clean_text(row.get("note")),
        }

    return latest_by_path

def _ensure_tailoring_preview_fields(payload_data: Dict[str, Any]) -> Dict[str, Any]:
    from src.tailoring.rendering import build_selected_patch_set_counterfactual_preview

    data = dict(payload_data)

    replacement_candidates = list(data.get("replacement_candidates", []) or [])
    if not replacement_candidates:
        return data

    if not isinstance(data.get("patch_set_counterfactual_preview"), dict):
        data["patch_set_counterfactual_preview"] = build_selected_patch_set_counterfactual_preview(
            data,
            selected_candidate_ids=None,
        )

    return data

def _tailoring_workspace_button_state(
    row: Dict[str, Any],
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> Dict[str, Any]:
    result = {
        "tailoring_ready_replacement_count": 0,
        "tailoring_actionable_replacement_count": 0,
        "tailoring_review_replacement_count": 0,
        "tailoring_has_ready_replacements": False,
        "tailoring_has_review_guidance": False,
        "tailoring_workspace_state": "empty",
    }

    raw_path = _clean_text(row.get("tailoring_json"))
    if not raw_path:
        return result

    try:
        artifact_path = _resolve_planning_artifact_path(raw_path, output_dir=output_dir)
        payload_data = _load_tailoring_json_artifact(artifact_path)

        if artifact_path.name.endswith("__tailoring.json"):
            payload_data = _rehydrate_legacy_tailoring_operator_payload(
                artifact_path,
                payload_data,
            )

        if payload_data.get("replacement_candidates") is not None:
            payload_data = _apply_saved_patch_selection_overlay(
                artifact_path,
                payload_data,
            )

        app_ready = list(payload_data.get("app_ready_replacements", []) or [])
        direct_apply_optional = list(payload_data.get("direct_apply_optional_replacements", []) or [])
        direction_only = list(payload_data.get("direction_only_replacements", []) or [])
        decisions = list(payload_data.get("final_replacement_decisions", []) or [])

        ready_count = len(app_ready)
        actionable_count = len(app_ready) + len(direct_apply_optional)
        review_count = len(direction_only)

        has_replacement_plan = bool(
            decisions or app_ready or direct_apply_optional or direction_only
        )

        if actionable_count > 0:
            workspace_state = "ready"
        elif review_count > 0:
            workspace_state = "review"
        elif has_replacement_plan:
            workspace_state = "review"
        else:
            workspace_state = "empty"

        result.update({
            "tailoring_ready_replacement_count": ready_count,
            "tailoring_actionable_replacement_count": actionable_count,
            "tailoring_review_replacement_count": review_count,
            "tailoring_has_ready_replacements": actionable_count > 0,
            "tailoring_has_review_guidance": review_count > 0,
            "tailoring_workspace_state": workspace_state,
        })
    except Exception:
        return result

    return result

def _apply_saved_patch_selection_overlay(
    artifact_path: Path,
    payload_data: Dict[str, Any],
) -> Dict[str, Any]:
    from src.tailoring.rendering import build_selected_patch_set_counterfactual_preview

    data = _ensure_tailoring_preview_fields(payload_data)
    data.setdefault("selected_patch_candidate_ids", [])
    data.setdefault("selected_patch_selection_status", "none")
    data.setdefault("selected_patch_selection_note", "")
    data.setdefault("selected_patch_selection_timestamp", "")

    latest_by_path = _load_latest_patch_selection_overlay()
    selection_row = latest_by_path.get(str(artifact_path))

    if not selection_row:
        default_selected_ids = _default_selected_candidate_ids_from_replacement_plan(data)
        if not default_selected_ids:
            return data

        data["selected_patch_candidate_ids"] = default_selected_ids
        data["selected_patch_selection_status"] = "auto_from_replacement_plan"
        data["selected_patch_selection_note"] = (
            "No saved manual patch selection found. Defaulting to apply-now replacements from the final replacement plan."
        )
        data["selected_patch_set_counterfactual_preview"] = build_selected_patch_set_counterfactual_preview(
            data,
            selected_candidate_ids=default_selected_ids,
        )
        return data

    saved_signature = _clean_text(selection_row.get("artifact_signature"))
    current_signature = _tailoring_artifact_signature(data)

    data["selected_patch_selection_timestamp"] = _clean_text(selection_row.get("selection_timestamp"))

    if saved_signature and saved_signature != current_signature:
        data["selected_patch_selection_status"] = "stale_signature"
        data["selected_patch_selection_note"] = (
            "Saved patch selection was ignored because the tailoring artifact changed after the selection was recorded."
        )
        return data

    requested_ids = _normalize_selected_patch_candidate_ids(
        selection_row.get("selected_candidate_ids_json", "")
    )
    valid_candidate_ids = set(_tailoring_artifact_candidate_ids(data))
    selected_ids = [candidate_id for candidate_id in requested_ids if candidate_id in valid_candidate_ids]

    if not selected_ids:
        data["selected_patch_selection_status"] = "no_valid_candidates"
        data["selected_patch_selection_note"] = (
            "Saved patch selection exists, but none of the candidate IDs are valid for the current artifact."
        )
        return data

    data["selected_patch_candidate_ids"] = selected_ids
    data["selected_patch_selection_status"] = "applied"
    data["selected_patch_selection_note"] = "Saved patch selection applied to this tailoring artifact."
    data["selected_patch_set_counterfactual_preview"] = build_selected_patch_set_counterfactual_preview(
        data,
        selected_candidate_ids=selected_ids,
    )
    return data

def _sanitize_optional_resume_filename(value: Any) -> str:
    raw = _clean_text(value)
    return _sanitize_resume_filename(raw) if raw else ""


def _normalize_operator_decision(value: Any) -> str:
    normalized = _clean_text(value).upper().replace(" ", "_")
    if not normalized:
        raise ValueError("decision is required.")
    if normalized not in ALLOWED_OPERATOR_DECISIONS:
        allowed = ", ".join(sorted(ALLOWED_OPERATOR_DECISIONS))
        raise ValueError(f"Invalid decision={normalized!r}. Allowed values: {allowed}")
    return normalized


def _operator_decision_key(row: Dict[str, Any]) -> str:
    return _application_action_key(row)


def _validate_operator_decision_identity(row: Dict[str, Any]) -> None:
    if not _operator_decision_key(row):
        raise ValueError(
            "Operator decision requires job_doc_id, job_url, or job_company + job_title."
        )


def _resolve_resume_preview_path(resume_name: str) -> Path:
    safe_name = _sanitize_resume_filename(resume_name)

    cached = _RESUME_PREVIEW_PATH_CACHE.get(safe_name, "")
    if cached:
        cached_path = Path(cached)
        if cached_path.exists() and cached_path.is_file():
            return cached_path

    profile_path = _get_resume_dir() / safe_name
    if profile_path.exists() and profile_path.is_file():
        resolved = profile_path.resolve()
        _RESUME_PREVIEW_PATH_CACHE[safe_name] = str(resolved)
        return resolved

    ignore_dirs = {
        ".git",
        "__pycache__",
        "node_modules",
        ".venv",
        "venv",
        "env",
        "job_scrap312",
    }

    matches: List[Path] = []
    search_root = Path.cwd().resolve()

    for path in search_root.rglob(safe_name):
        if not path.is_file():
            continue
        if path.suffix.lower() != ".pdf":
            continue
        if any(part in ignore_dirs for part in path.parts):
            continue
        matches.append(path.resolve())

    if not matches:
        raise ValueError(f"Resume preview file not found: {safe_name}")

    matches.sort(key=lambda path: (len(path.parts), len(str(path))))
    chosen = matches[0]
    _RESUME_PREVIEW_PATH_CACHE[safe_name] = str(chosen)
    return chosen


def planning_resume_preview_path(resume_name: str) -> Path:
    return _resolve_resume_preview_path(resume_name)

def _slugify_text(value: Any, max_len: int = 80) -> str:
    text = _clean_text(value).lower()
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    if not text:
        text = "item"
    return text[:max_len]


def _load_job_doc_id_to_index(job_corpus_path: Path) -> Dict[str, int]:
    from src.matching.job_adapter import build_job_evidence

    if not job_corpus_path.exists():
        raise ValueError(f"Missing job corpus: {job_corpus_path}")

    mapping: Dict[str, int] = {}
    with job_corpus_path.open("r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            line = line.strip()
            if not line:
                continue

            record = json.loads(line)
            job_evidence = build_job_evidence(record)
            job_doc_id = _clean_text(getattr(job_evidence, "job_doc_id", ""))

            if job_doc_id:
                mapping[job_doc_id] = idx

    if not mapping:
        raise ValueError(f"No usable job_doc_id values found in {job_corpus_path}")

    return mapping


def _load_csv_rows_with_fieldnames(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    if not path.exists():
        raise ValueError(f"Missing CSV: {path}")

    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])

    return rows, fieldnames


def _write_csv_rows(path: Path, fieldnames: List[str], rows: List[Dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _run_checked_cmd(cmd: List[str]) -> None:
    subprocess.run(cmd, check=True)


def _read_regenerated_llm_status(llm_json_path: Path) -> Dict[str, str]:
    defaults = {
        "llm_tailoring_status": "disabled",
        "llm_cache_hit": "",
        "llm_parse_ok": "",
        "llm_provider": "",
        "llm_model": "",
        "llm_error_type": "",
        "llm_retryable": "",
        "llm_retry_used": "",
    }

    if not llm_json_path.exists():
        return defaults

    try:
        data = json.loads(llm_json_path.read_text(encoding="utf-8"))
    except Exception:
        out = dict(defaults)
        out["llm_tailoring_status"] = "unreadable"
        out["llm_error_type"] = "unreadable_json"
        out["llm_retryable"] = "False"
        return out

    parse_ok = bool(data.get("parse_ok"))
    cache_hit = bool(data.get("cache_hit"))
    retry_used = bool(data.get("retry_used"))

    if parse_ok and cache_hit:
        status = "cached"
    elif parse_ok:
        status = "generated"
    else:
        status = "failed"

    return {
        "llm_tailoring_status": status,
        "llm_cache_hit": str(cache_hit),
        "llm_parse_ok": str(parse_ok),
        "llm_provider": str(data.get("provider", "")),
        "llm_model": str(data.get("model", "")),
        "llm_error_type": "" if parse_ok else "llm_parse_failed",
        "llm_retryable": "" if parse_ok else "False",
        "llm_retry_used": str(retry_used),
    }


def _find_planning_row_for_regeneration(
    rows: List[Dict[str, Any]],
    *,
    job_doc_id: str = "",
    queue_rank: str = "",
) -> Dict[str, Any]:
    clean_job_doc_id = _clean_text(job_doc_id)
    clean_queue_rank = _clean_text(queue_rank)

    if clean_job_doc_id:
        for row in rows:
            if _clean_text(row.get("job_doc_id")) == clean_job_doc_id:
                return row

    if clean_queue_rank:
        for row in rows:
            if _clean_text(row.get("queue_rank")) == clean_queue_rank:
                return row

    raise ValueError("Could not find planning row for targeted regeneration.")


def regenerate_selected_resume_tailoring_payload(
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    job_corpus: Path = DEFAULT_CORPUS_PATH,
    *,
    job_doc_id: str = "",
    queue_rank: str = "",
    selected_resume: str = "",
    generate_llm_tailoring: bool = False,
    refresh_llm_tailoring: bool = False,
) -> Dict[str, Any]:
    ja = _job_app()
    merged_rows = ja._build_job_index(output_dir)
    target_row = _find_planning_row_for_regeneration(
        merged_rows,
        job_doc_id=job_doc_id,
        queue_rank=queue_rank,
    )

    chosen_resume = _sanitize_resume_filename(
        selected_resume or target_row.get("operator_selected_resume", "")
    )
    if not chosen_resume:
        raise ValueError("No operator-selected resume is available for regeneration.")

    allowed_resumes = {
        value
        for value in [
            _sanitize_optional_resume_filename(target_row.get("winner_resume")),
            _sanitize_optional_resume_filename(target_row.get("runner_up_resume")),
        ]
        if value
    }
    if chosen_resume not in allowed_resumes:
        allowed = ", ".join(sorted(allowed_resumes))
        raise ValueError(
            f"selected_resume must match the current winner or runner-up. Allowed: {allowed}"
        )

    job_doc_id_value = _clean_text(target_row.get("job_doc_id"))
    if not job_doc_id_value:
        raise ValueError("Target planning row is missing job_doc_id.")

    job_doc_id_to_index = _load_job_doc_id_to_index(job_corpus)
    if job_doc_id_value not in job_doc_id_to_index:
        raise ValueError(f"Could not map job_doc_id to corpus index: {job_doc_id_value}")

    company = _clean_text(target_row.get("job_company"))
    title = _clean_text(target_row.get("job_title"))
    action = _clean_text(target_row.get("action"))

    job_packets_dir = Path(output_dir) / "job_packets"
    job_packets_dir.mkdir(parents=True, exist_ok=True)

    training_log_jsonl_path = Path(output_dir) / "training_logs" / "tailoring_runs.jsonl"
    training_log_jsonl_path.parent.mkdir(parents=True, exist_ok=True)

    file_slug = (
        f"{_slugify_text(company, 30)}__"
        f"{_slugify_text(title, 60)}__"
        f"{_slugify_text(chosen_resume, 40)}"
    )

    packet_json_path = job_packets_dir / f"{file_slug}.json"
    tailoring_json_path = job_packets_dir / f"{file_slug}__tailoring.json"
    tailoring_md_path = job_packets_dir / f"{file_slug}__tailoring.md"
    tailoring_llm_json_path = job_packets_dir / f"{file_slug}__tailoring_llm.json"

    diff_cmd = [
        sys.executable,
        "jd_resume_diff_helper.py",
        "--job-corpus",
        str(job_corpus),
        "--job-index",
        str(job_doc_id_to_index[job_doc_id_value]),
        "--resume-name-contains",
        chosen_resume,
        "--disable-semantic-evidence",
        "--output-json",
        str(packet_json_path),
    ]

    _run_checked_cmd(diff_cmd)

    tailoring_cmd = [
        sys.executable,
        "generate_tailoring_suggestions.py",
        "--packet-json",
        str(packet_json_path),
        "--output-json",
        str(tailoring_json_path),
        "--output-md",
        str(tailoring_md_path),
        "--training-log-jsonl",
        str(training_log_jsonl_path),
    ]

    llm_status = {
        "llm_tailoring_status": "disabled",
        "llm_cache_hit": "",
        "llm_parse_ok": "",
        "llm_provider": "",
        "llm_model": "",
        "llm_error_type": "",
        "llm_retryable": "",
        "llm_retry_used": "",
    }
    llm_json_value = ""

    if generate_llm_tailoring:
        tailoring_cmd.extend(
            [
                "--use-llm",
                "--output-llm-json",
                str(tailoring_llm_json_path),
            ]
        )
        if refresh_llm_tailoring:
            tailoring_cmd.append("--refresh-llm-cache")

    _run_checked_cmd(tailoring_cmd)

    if generate_llm_tailoring:
        llm_status = _read_regenerated_llm_status(tailoring_llm_json_path)
        llm_json_value = str(tailoring_llm_json_path)

    manifest_path = Path(output_dir) / "job_packet_manifest.csv"
    manifest_rows, fieldnames = _load_csv_rows_with_fieldnames(manifest_path)

    if "packet_status" not in fieldnames:
        insert_at = fieldnames.index("packet_json") if "packet_json" in fieldnames else len(fieldnames)
        fieldnames.insert(insert_at, "packet_status")
        for row in manifest_rows:
            row.setdefault("packet_status", "")

    updated = False
    for row in manifest_rows:
        if _clean_text(row.get("job_doc_id")) != job_doc_id_value:
            continue

        row["queue_rank"] = _clean_text(target_row.get("queue_rank"))
        row["needs_variant_review"] = _clean_text(target_row.get("needs_variant_review"))
        row["missing_requirement_count"] = _clean_text(target_row.get("missing_requirement_count"))
        row["queue_priority_reason"] = _clean_text(target_row.get("queue_priority_reason"))
        row["job_doc_id"] = job_doc_id_value
        row["job_company"] = company
        row["job_title"] = title
        row["action"] = action
        row["winner_resume"] = _clean_text(target_row.get("winner_resume"))
        row["winner_score"] = _clean_text(target_row.get("winner_score"))
        row["runner_up_resume"] = _clean_text(target_row.get("runner_up_resume"))
        row["runner_up_score"] = _clean_text(target_row.get("runner_up_score"))
        row["score_gap"] = _clean_text(target_row.get("score_gap"))
        row["is_tie"] = _clean_text(target_row.get("is_tie"))
        row["packet_status"] = "generated"
        row["packet_json"] = str(packet_json_path)
        row["tailoring_json"] = str(tailoring_json_path)
        row["tailoring_md"] = str(tailoring_md_path)
        row["tailoring_llm_json"] = llm_json_value
        row["llm_tailoring_status"] = llm_status["llm_tailoring_status"]
        row["llm_cache_hit"] = llm_status["llm_cache_hit"]
        row["llm_parse_ok"] = llm_status["llm_parse_ok"]
        row["llm_provider"] = llm_status["llm_provider"]
        row["llm_model"] = llm_status["llm_model"]
        row["llm_error_type"] = llm_status["llm_error_type"]
        row["llm_retryable"] = llm_status["llm_retryable"]
        row["llm_retry_used"] = llm_status["llm_retry_used"]
        updated = True
        break

    if not updated:
        manifest_row = {field: "" for field in fieldnames}
        manifest_row["queue_rank"] = _clean_text(target_row.get("queue_rank"))
        manifest_row["needs_variant_review"] = _clean_text(target_row.get("needs_variant_review"))
        manifest_row["missing_requirement_count"] = _clean_text(target_row.get("missing_requirement_count"))
        manifest_row["queue_priority_reason"] = _clean_text(target_row.get("queue_priority_reason"))
        manifest_row["job_doc_id"] = job_doc_id_value
        manifest_row["job_company"] = company
        manifest_row["job_title"] = title
        manifest_row["action"] = action
        manifest_row["winner_resume"] = _clean_text(target_row.get("winner_resume"))
        manifest_row["winner_score"] = _clean_text(target_row.get("winner_score"))
        manifest_row["runner_up_resume"] = _clean_text(target_row.get("runner_up_resume"))
        manifest_row["runner_up_score"] = _clean_text(target_row.get("runner_up_score"))
        manifest_row["score_gap"] = _clean_text(target_row.get("score_gap"))
        manifest_row["is_tie"] = _clean_text(target_row.get("is_tie"))
        manifest_row["packet_status"] = "generated"
        manifest_row["packet_json"] = str(packet_json_path)
        manifest_row["tailoring_json"] = str(tailoring_json_path)
        manifest_row["tailoring_md"] = str(tailoring_md_path)
        manifest_row["tailoring_llm_json"] = llm_json_value
        manifest_row["llm_tailoring_status"] = llm_status["llm_tailoring_status"]
        manifest_row["llm_cache_hit"] = llm_status["llm_cache_hit"]
        manifest_row["llm_parse_ok"] = llm_status["llm_parse_ok"]
        manifest_row["llm_provider"] = llm_status["llm_provider"]
        manifest_row["llm_model"] = llm_status["llm_model"]
        manifest_row["llm_error_type"] = llm_status["llm_error_type"]
        manifest_row["llm_retryable"] = llm_status["llm_retryable"]
        manifest_row["llm_retry_used"] = llm_status["llm_retry_used"]
        manifest_rows.append(manifest_row)

    _write_csv_rows(manifest_path, fieldnames, manifest_rows)

    return {
        "ok": True,
        "job_doc_id": job_doc_id_value,
        "job_company": company,
        "job_title": title,
        "action": action,
        "selected_resume": chosen_resume,
        "packet_json": str(packet_json_path),
        "tailoring_json": str(tailoring_json_path),
        "tailoring_md": str(tailoring_md_path),
        "tailoring_llm_json": llm_json_value,
        "training_log_jsonl": str(training_log_jsonl_path),
        "llm_tailoring_status": llm_status["llm_tailoring_status"],
        "manifest_path": str(manifest_path),
    }

def _normalize_application_status(value: Any) -> str:
    normalized = _clean_text(value).upper().replace(" ", "_")
    if not normalized:
        raise ValueError("application_status is required.")
    if normalized not in ALLOWED_APPLICATION_STATUSES:
        allowed = ", ".join(sorted(ALLOWED_APPLICATION_STATUSES))
        raise ValueError(f"Invalid application_status={normalized!r}. Allowed values: {allowed}")
    return normalized


def _application_action_key(row: Dict[str, Any]) -> str:
    ja = _job_app()

    job_doc_id = _clean_text(row.get("job_doc_id"))
    if job_doc_id:
        return f"job_doc_id::{job_doc_id}"

    job_url = _clean_text(row.get("job_url"))
    if job_url:
        return f"job_url::{job_url}"

    company = ja._normalize_text(row.get("job_company", ""))
    title = ja._normalize_text(row.get("job_title", ""))
    if company or title:
        return f"title::{company}||{title}"

    return ""


def _validate_application_identity(row: Dict[str, Any]) -> None:
    if not _application_action_key(row):
        raise ValueError(
            "Application action requires job_doc_id, job_url, or job_company + job_title."
        )

def _dual_write_application_action_postgres(row: Dict[str, Any]) -> Dict[str, Any]:
    database_url = str(os.environ.get("DATABASE_URL", "") or "").strip()
    if not database_url:
        return {
            "attempted": False,
            "ok": False,
            "skipped": "missing_database_url",
            "table_name": "application_actions",
        }

    try:
        payload = insert_application_action_row_to_postgres(
            record=row,
            database_url="",
            database_url_env="DATABASE_URL",
            psql_bin="psql",
            print_only=False,
            allow_contract_drift=False,
        )
        return {
            "attempted": True,
            "ok": True,
            "table_name": payload.get("table_name", "application_actions"),
            "action_id": str(payload.get("row", {}).get("action_id", "") or ""),
            "action_key": str(payload.get("row", {}).get("action_key", "") or ""),
            "contract_health_ok": bool(payload.get("contract_health_ok", False)),
            "command_text": str(payload.get("command_text", "") or ""),
        }
    except SystemExit as exc:
        return {
            "attempted": True,
            "ok": False,
            "table_name": "application_actions",
            "error_type": "SystemExit",
            "error": str(exc),
        }
    except Exception as exc:
        return {
            "attempted": True,
            "ok": False,
            "table_name": "application_actions",
            "error_type": exc.__class__.__name__,
            "error": str(exc),
        }

def _application_action_latest_sort_key(row: Dict[str, Any]) -> Tuple[str, str]:
    normalized = application_action_db_row(dict(row))
    return (
        str(normalized.get("action_timestamp", "") or ""),
        str(normalized.get("action_id", "") or ""),
    )


def _load_latest_application_actions() -> List[Dict[str, str]]:
    postgres_payload = get_latest_application_actions_rows(
        database_url="",
        database_url_env="DATABASE_URL",
        psql_bin="psql",
        print_only=False,
    )
    postgres_rows = list(postgres_payload.get("rows", []) or [])

    normalized_rows: List[Dict[str, str]] = []
    for row in postgres_rows:
        normalized_rows.append({
            "action_timestamp": _clean_text(row.get("action_timestamp")),
            "job_doc_id": _clean_text(row.get("job_doc_id")),
            "job_url": _clean_text(row.get("job_url")),
            "job_company": _clean_text(row.get("job_company")),
            "job_title": _clean_text(row.get("job_title")),
            "application_status": _clean_text(row.get("application_status")),
            "source_view": _clean_text(row.get("source_view")),
            "note": _clean_text(row.get("note")),
        })

    normalized_rows.sort(
        key=lambda row: _application_action_latest_sort_key(row),
        reverse=True,
    )
    return normalized_rows

def _application_row_key_candidates(row: Dict[str, Any]) -> List[str]:
    ja = _job_app()

    key_candidates: List[str] = []

    direct_key = _application_action_key(row)
    if direct_key:
        key_candidates.append(direct_key)

    job_doc_id = _clean_text(row.get("job_doc_id"))
    if job_doc_id:
        key_candidates.append(f"job_doc_id::{job_doc_id}")

    job_url = _clean_text(row.get("job_url"))
    if job_url:
        key_candidates.append(f"job_url::{job_url}")

    company = ja._normalize_text(row.get("job_company", "") or row.get("company", ""))
    title = ja._normalize_text(row.get("job_title", "") or row.get("title", ""))
    if company or title:
        key_candidates.append(f"title::{company}||{title}")

    deduped: List[str] = []
    for key in key_candidates:
        if key and key not in deduped:
            deduped.append(key)
    return deduped


def _application_overlay_from_row(action_row: Dict[str, Any]) -> Dict[str, Any]:
    status = _clean_text(action_row.get("application_status")).upper()
    is_applied = status == "APPLIED"

    return {
        "application_status": status,
        "application_label": "Applied" if is_applied else "Apply",
        "is_applied": is_applied,
    }


def _load_latest_application_action_overlay() -> Dict[str, Dict[str, Any]]:
    latest_rows = _load_latest_application_actions()
    latest_by_key: Dict[str, Dict[str, Any]] = {}

    for row in latest_rows:
        overlay = _application_overlay_from_row(row)
        for key in _application_row_key_candidates(row):
            latest_by_key[key] = overlay

    return latest_by_key


def _overlay_application_actions(
    rows: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    latest_by_key = _load_latest_application_action_overlay()

    overlaid_rows: List[Dict[str, Any]] = []
    for row in rows:
        merged = dict(row)

        for field in APPLICATION_ACTION_OVERLAY_FIELDS:
            if field == "application_label":
                merged.setdefault(field, "Apply")
            elif field == "is_applied":
                merged.setdefault(field, False)
            else:
                merged.setdefault(field, "")

        overlay = None
        for key in _application_row_key_candidates(row):
            if key in latest_by_key:
                overlay = latest_by_key[key]
                break

        if overlay:
            merged.update(overlay)

        overlaid_rows.append(merged)

    return overlaid_rows

def _exclude_applied_rows(
    rows: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    return [
        row for row in rows
        if not bool(row.get("is_applied", False))
    ]

def _load_job_metadata_overlay_from_corpus(
    job_corpus: Path = DEFAULT_CORPUS_PATH,
) -> Dict[str, Dict[str, Any]]:
    latest_by_key: Dict[str, Dict[str, Any]] = {}

    if not job_corpus.exists():
        return latest_by_key

    with job_corpus.open("r", encoding="utf-8") as f:
        for line in f:
            raw = line.strip()
            if not raw:
                continue

            try:
                record = json.loads(raw)
            except Exception:
                continue

            metadata = record.get("metadata", {}) if isinstance(record.get("metadata"), dict) else {}

            job_doc_id = _clean_text(
                record.get("job_doc_id")
                or record.get("doc_id")
                or metadata.get("job_doc_id")
                or metadata.get("doc_id")
                or record.get("job_url")
                or metadata.get("job_url")
            )
            job_url = _clean_text(
                record.get("job_url")
                or metadata.get("job_url")
                or job_doc_id
            )
            job_company = _clean_text(
                record.get("job_company")
                or record.get("company")
                or metadata.get("job_company")
                or metadata.get("company")
            )
            job_title = _clean_text(
                record.get("job_title")
                or record.get("title")
                or metadata.get("job_title")
                or metadata.get("title")
            )
            posted_at = _clean_text(
                record.get("posted_at")
                or metadata.get("posted_at")
            )

            if not any([job_doc_id, job_url, job_company, job_title]):
                continue

            key_row = {
                "job_doc_id": job_doc_id,
                "job_url": job_url,
                "job_company": job_company,
                "job_title": job_title,
            }
            overlay = {
                "posted_at": posted_at,
                "job_url": job_url,
            }

            for key in _application_row_key_candidates(key_row):
                if key:
                    latest_by_key[key] = overlay

    return latest_by_key

def _overlay_job_metadata(
    rows: List[Dict[str, Any]],
    job_corpus: Path = DEFAULT_CORPUS_PATH,
) -> List[Dict[str, Any]]:
    latest_by_key = _load_job_metadata_overlay_from_corpus(job_corpus)

    overlaid_rows: List[Dict[str, Any]] = []

    for row in rows:
        merged = dict(row)
        merged["posted_at"] = _clean_text(merged.get("posted_at"))
        merged["job_url"] = _clean_text(merged.get("job_url")) or _clean_text(merged.get("job_doc_id"))

        if latest_by_key:
            for key in _application_row_key_candidates(merged):
                overlay = latest_by_key.get(key)
                if not overlay:
                    continue

                if overlay.get("posted_at"):
                    merged["posted_at"] = overlay["posted_at"]
                if overlay.get("job_url") and not _clean_text(merged.get("job_url")):
                    merged["job_url"] = overlay["job_url"]
                break

        overlaid_rows.append(merged)

    return overlaid_rows

def health_payload() -> Dict[str, Any]:
    from src.rag.retriever import get_semantic_status

    semantic_status = get_semantic_status()

    return {
        "ok": True,
        "service": "job-operator-api",
        "semantic_retrieval": semantic_status,
        "rag_answer_ready": bool(semantic_status.get("ready", False)),
    }


def status_payload(
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    job_corpus: Path = DEFAULT_CORPUS_PATH,
    top_k: int = 10,
) -> Dict[str, Any]:
    ja = _job_app()
    best_rows = ja._load_csv_rows(output_dir / "best_resume_variant_by_job.csv")
    shortlist_rows = ja._load_csv_rows(output_dir / "application_shortlist_by_job.csv")
    queue_rows = ja._load_csv_rows(output_dir / "application_execution_queue.csv")
    manifest_rows = ja._load_csv_rows(output_dir / "job_packet_manifest.csv")
    decision_rows = _load_latest_operator_decision_rows()

    merged_rows = ja._build_job_index(output_dir)
    undecided_review_counts = ja._count_undecided_review_rows(merged_rows)

    winner_bucket_counts = Counter(
        str(row.get("winner_bucket", "") or "<empty>")
        for row in best_rows
    )
    fallback_status_counts = Counter(
        str(row.get("llm_fallback_status", "") or "<empty>")
        for row in best_rows
    )
    action_counts = Counter(
        str(row.get("action", "") or "<empty>")
        for row in queue_rows
    )
    llm_tailoring_counts = Counter(
        str(row.get("llm_tailoring_status", "") or "<empty>")
        for row in manifest_rows
    )
    decision_counts = Counter(
        str(row.get("decision", "") or "<empty>")
        for row in decision_rows
    )

    latest_by_key = ja._load_latest_decision_overlay()
    application_overlay_by_key = _load_latest_application_action_overlay()
    job_metadata_by_key = _load_job_metadata_overlay_from_corpus(job_corpus)

    top_rows = sorted(
        queue_rows,
        key=lambda row: (
            int(str(row.get("queue_rank", "999999") or "999999")),
            -ja._parse_float(row.get("winner_score", "0")),
        ),
    )[:top_k]

    top_queue = []
    for row in top_rows:
        overlay_row = dict(row)
        overlay_row["posted_at"] = _clean_text(overlay_row.get("posted_at"))
        overlay_row["job_url"] = _clean_text(overlay_row.get("job_url")) or _clean_text(overlay_row.get("job_doc_id"))
        for field in ja.OPERATOR_DECISION_OVERLAY_FIELDS:
            overlay_row.setdefault(field, "")

        key_candidates = [
            ja._decision_row_key(row),
            f"queue_rank::{str(row.get('queue_rank', '') or '').strip()}",
            (
                f"title::{ja._normalize_text(row.get('job_company', ''))}"
                f"||{ja._normalize_text(row.get('job_title', ''))}"
            ),
        ]

        for key in key_candidates:
            if key and key in latest_by_key:
                overlay_row.update(latest_by_key[key])
                break
        
        for key in _application_row_key_candidates(overlay_row):
            metadata = job_metadata_by_key.get(key)
            if not metadata:
                continue

            if metadata.get("posted_at"):
                overlay_row["posted_at"] = metadata["posted_at"]
            if metadata.get("job_url") and not _clean_text(overlay_row.get("job_url")):
                overlay_row["job_url"] = metadata["job_url"]
            break
        
        for field in APPLICATION_ACTION_OVERLAY_FIELDS:
            if field == "application_label":
                overlay_row.setdefault(field, "Apply")
            elif field == "is_applied":
                overlay_row.setdefault(field, False)
            else:
                overlay_row.setdefault(field, "")

        for key in _application_row_key_candidates(overlay_row):
            if key in application_overlay_by_key:
                overlay_row.update(application_overlay_by_key[key])
                break
        
        top_queue.append(overlay_row)

    return {
        "summary": {
            "job_corpus_path": str(job_corpus),
            "job_corpus_rows": ja._count_jsonl_rows(job_corpus),
            "planning_output_dir": str(output_dir),
            "best_variant_rows": len(best_rows),
            "shortlist_rows": len(shortlist_rows),
            "execution_queue_rows": len(queue_rows),
            "packet_manifest_rows": len(manifest_rows),
            "operator_decisions_storage": "postgres",
            "operator_decisions_rows": len(decision_rows),
        },
        "winner_bucket_counts": dict(sorted(winner_bucket_counts.items())),
        "llm_fallback_status_counts": dict(sorted(fallback_status_counts.items())),
        "queue_action_counts": dict(sorted(action_counts.items())),
        "operator_decision_counts": dict(sorted(decision_counts.items())),
        "undecided_review_counts": dict(sorted(undecided_review_counts.items())),
        "llm_tailoring_status_counts": dict(sorted(llm_tailoring_counts.items())),
        "top_queue_rows": top_queue,
    }


def browse_payload(
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    **filters: Any,
) -> Dict[str, Any]:
    ja = _job_app()
    rows = ja._build_job_index(output_dir)

    resolved_filters = {
        "action": "",
        "needs_review": "",
        "is_tie": "",
        "fallback_status": "",
        "winner_bucket": "",
        "company_contains": "",
        "title_contains": "",
        "limit": 15,
        "undecided_only": "",
        "page": 1,
    }
    resolved_filters.update(filters)

    requested_limit = max(int(resolved_filters.get("limit", 15) or 15), 1)
    current_page = max(int(resolved_filters.get("page", 1) or 1), 1)
    page_size = 15

    selection_filters = dict(resolved_filters)
    selection_filters["limit"] = max(len(rows), 1)
    selection_filters.pop("page", None)

    args = _make_args(**selection_filters)
    selected = ja._select_browse_rows(rows, args)
    selected = _overlay_job_metadata(selected, job_corpus=DEFAULT_CORPUS_PATH)
    selected = _overlay_application_actions(selected)
    selected = _exclude_applied_rows(selected)

    selected = selected[:requested_limit]

    total_count = len(selected)
    total_pages = max((total_count + page_size - 1) // page_size, 1)
    current_page = min(current_page, total_pages)

    start = (current_page - 1) * page_size
    end = start + page_size
    page_rows = selected[start:end]
    page_rows = [
        {
            **dict(row),
            **_tailoring_workspace_button_state(row, output_dir=output_dir),
        }
        for row in page_rows
    ]

    return {
        "filters": {
            "action": resolved_filters.get("action", ""),
            "needs_review": resolved_filters.get("needs_review", ""),
            "is_tie": resolved_filters.get("is_tie", ""),
            "fallback_status": resolved_filters.get("fallback_status", ""),
            "winner_bucket": resolved_filters.get("winner_bucket", ""),
            "company_contains": resolved_filters.get("company_contains", ""),
            "title_contains": resolved_filters.get("title_contains", ""),
            "limit": requested_limit,
            "undecided_only": resolved_filters.get("undecided_only", ""),
            "page": current_page,
        },
        "rows": page_rows,
        "count": len(page_rows),
        "total_count": total_count,
        "page": current_page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_prev_page": current_page > 1,
        "has_next_page": current_page < total_pages,
    }

def review_payload(
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    **filters: Any,
) -> Dict[str, Any]:
    ja = _job_app()
    rows = ja._build_job_index(output_dir)

    resolved_filters = {
        "queue_rank": None,
        "job_doc_id": "",
        "company_contains": "",
        "title_contains": "",
        "include_non_review": False,
        "limit": 5,
        "action": "",
        "undecided_only": "",
    }
    resolved_filters.update(filters)

    args = _make_args(**resolved_filters)
    selected = ja._select_review_rows(rows, args)
    selected = _overlay_job_metadata(selected, job_corpus=DEFAULT_CORPUS_PATH)
    selected = _overlay_application_actions(selected)
    selected = _exclude_applied_rows(selected)

    return {
        "filters": resolved_filters,
        "rows": selected,
        "count": len(selected),
    }


def workflow_payload(
    view: str,
    limit: int = 20,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> Dict[str, Any]:
    ja = _job_app()
    rows = ja._build_job_index(output_dir)
    selected = ja._workflow_view_rows(rows, view)[:limit]
    selected = _overlay_job_metadata(selected, job_corpus=DEFAULT_CORPUS_PATH)
    selected = _overlay_application_actions(selected)
    selected = _exclude_applied_rows(selected)
    return {
        "view": view,
        "rows": selected,
        "count": len(selected),
    }


def planner_payload(
    request: str,
    limit: int = 20,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> Dict[str, Any]:
    ja = _job_app()
    view = ja._infer_planner_view(request)
    rows = ja._build_job_index(output_dir)
    selected = ja._workflow_view_rows(rows, view)[:limit]
    selected = _overlay_job_metadata(selected, job_corpus=DEFAULT_CORPUS_PATH)
    selected = _overlay_application_actions(selected)
    return {
        "request": request,
        "resolved_view": view,
        "rows": selected,
        "count": len(selected),
    }

def _resolve_planning_artifact_path(
    path: str,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> Path:
    raw = str(path or "").strip()
    if not raw:
        raise ValueError("Artifact path is required.")

    resolved = Path(raw).expanduser().resolve()
    output_root = Path(output_dir).expanduser().resolve()

    try:
        resolved.relative_to(output_root)
    except ValueError as exc:
        raise ValueError("Artifact path must stay inside the planning output directory.") from exc

    if not resolved.exists() or not resolved.is_file():
        raise ValueError(f"Artifact not found: {raw}")

    if resolved.suffix.lower() not in {".md", ".json"}:
        raise ValueError(f"Unsupported artifact type: {resolved.suffix}")

    return resolved


def planning_artifact_payload(
    path: str,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> Dict[str, Any]:
    artifact_path = _resolve_planning_artifact_path(path, output_dir=output_dir)
    suffix = artifact_path.suffix.lower()
    text = artifact_path.read_text(encoding="utf-8")

    payload: Dict[str, Any] = {
        "ok": True,
        "path": str(artifact_path),
        "kind": "json" if suffix == ".json" else "text",
    }

    if suffix == ".json":
        data = json.loads(text)
        if isinstance(data, dict):
            if artifact_path.name.endswith("__tailoring.json"):
                data = _rehydrate_legacy_tailoring_operator_payload(
                    artifact_path,
                    data,
                )

            if data.get("replacement_candidates") is not None:
                data = _apply_saved_patch_selection_overlay(
                    artifact_path,
                    data,
                )
        payload["data"] = data
    else:
        payload["text"] = text

    return payload

def _operator_decision_latest_sort_key(row: Dict[str, Any]) -> Tuple[str, str]:
    normalized = operator_decision_db_row(dict(row))
    return (
        str(normalized.get("decision_timestamp", "") or ""),
        str(normalized.get("decision_id", "") or ""),
    )

def _load_latest_operator_decision_rows() -> List[Dict[str, Any]]:
    meta_payload = get_operator_decisions_postgres_status_payload(
        limit=1,
        database_url="",
        database_url_env="DATABASE_URL",
        psql_bin="psql",
        print_only=False,
    )
    meta_block = dict(meta_payload.get("postgres", {}) or {})
    query_limit = max(int(meta_block.get("latest_state_count", 0) or 0), 1)

    postgres_payload = get_operator_decisions_postgres_status_payload(
        limit=query_limit,
        database_url="",
        database_url_env="DATABASE_URL",
        psql_bin="psql",
        print_only=False,
    )
    postgres_block = dict(postgres_payload.get("postgres", {}) or {})
    postgres_rows = list(postgres_block.get("latest_rows", []) or [])

    normalized_rows: List[Dict[str, Any]] = []
    for row in postgres_rows:
        normalized = operator_decision_db_row({
            "decision_timestamp": row.get("decision_timestamp", ""),
            "queue_rank": row.get("queue_rank", ""),
            "job_doc_id": row.get("job_doc_id", ""),
            "job_company": row.get("job_company", ""),
            "job_title": row.get("job_title", ""),
            "planning_action": row.get("planning_action", ""),
            "winner_resume": row.get("winner_resume", ""),
            "winner_score": row.get("winner_score", ""),
            "runner_up_resume": row.get("runner_up_resume", ""),
            "runner_up_score": row.get("runner_up_score", ""),
            "selected_resume": row.get("selected_resume", ""),
            "decision": row.get("decision", ""),
            "note": row.get("note", ""),
        })
        normalized_rows.append(normalized)

    normalized_rows.sort(
        key=lambda row: _operator_decision_latest_sort_key(row),
        reverse=True,
    )
    return normalized_rows


def decisions_payload(
    queue_rank: int | None = None,
    decision: Any = "",
    selected_resume: str = "",
    company_contains: str = "",
    title_contains: str = "",
    limit: int = 15,
    page: int = 1,
) -> Dict[str, Any]:
    ja = _job_app()
    rows = _load_latest_operator_decision_rows()

    resolved_filters = {
        "queue_rank": queue_rank,
        "decision": decision,
        "selected_resume": selected_resume,
        "company_contains": company_contains,
        "title_contains": title_contains,
        "limit": limit,
        "page": page,
    }

    requested_limit = max(int(limit or 15), 1)
    current_page = max(int(page or 1), 1)
    page_size = 15

    selection_filters = dict(resolved_filters)
    selection_filters["limit"] = max(len(rows), 1)
    selection_filters.pop("page", None)

    args = _make_args(**selection_filters)
    selected = ja._select_decision_rows(rows, args)
    selected = _overlay_job_metadata(selected, job_corpus=DEFAULT_CORPUS_PATH)
    selected = _overlay_application_actions(selected)

    selected = selected[:requested_limit]

    total_count = len(selected)
    total_pages = max((total_count + page_size - 1) // page_size, 1)
    current_page = min(current_page, total_pages)

    start_idx = (current_page - 1) * page_size
    end_idx = start_idx + page_size
    page_rows = selected[start_idx:end_idx]

    return {
        "filters": {
            "queue_rank": queue_rank,
            "decision": decision,
            "selected_resume": selected_resume,
            "company_contains": company_contains,
            "title_contains": title_contains,
            "limit": requested_limit,
            "page": current_page,
        },
        "rows": page_rows,
        "count": len(page_rows),
        "total_count": total_count,
        "page": current_page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_prev_page": current_page > 1,
        "has_next_page": current_page < total_pages,
    }

def _dual_write_operator_decision_postgres(row: Dict[str, Any]) -> Dict[str, Any]:
    database_url = str(os.environ.get("DATABASE_URL", "") or "").strip()
    if not database_url:
        return {
            "attempted": False,
            "ok": False,
            "skipped": "missing_database_url",
            "table_name": "operator_decisions",
        }

    try:
        payload = insert_operator_decision_row_to_postgres(
            record=row,
            database_url="",
            database_url_env="DATABASE_URL",
            psql_bin="psql",
            print_only=False,
            allow_contract_drift=False,
        )
        return {
            "attempted": True,
            "ok": True,
            "table_name": payload.get("table_name", "operator_decisions"),
            "decision_id": str(payload.get("row", {}).get("decision_id", "") or ""),
            "decision_key": str(payload.get("row", {}).get("decision_key", "") or ""),
            "contract_health_ok": bool(payload.get("contract_health_ok", False)),
            "command_text": str(payload.get("command_text", "") or ""),
        }
    except SystemExit as exc:
        return {
            "attempted": True,
            "ok": False,
            "table_name": "operator_decisions",
            "error_type": "SystemExit",
            "error": str(exc),
        }
    except Exception as exc:
        return {
            "attempted": True,
            "ok": False,
            "table_name": "operator_decisions",
            "error_type": exc.__class__.__name__,
            "error": str(exc),
        }
    
def record_operator_resume_selection_payload(
    *,
    queue_rank: str = "",
    job_doc_id: str = "",
    job_company: str = "",
    job_title: str = "",
    planning_action: str = "",
    decision: str = "SELECT_RESUME",
    selected_resume: str = "",
    winner_resume: str = "",
    winner_score: str = "",
    runner_up_resume: str = "",
    runner_up_score: str = "",
    note: str = "",
) -> Dict[str, Any]:
    ja = _job_app()

    safe_selected = _sanitize_resume_filename(selected_resume)
    safe_winner = _sanitize_optional_resume_filename(winner_resume)
    safe_runner = _sanitize_optional_resume_filename(runner_up_resume)

    allowed_resumes = {name for name in [safe_winner, safe_runner] if name}
    if not allowed_resumes:
        raise ValueError("No eligible resume choices were provided.")

    if safe_selected not in allowed_resumes:
        allowed = ", ".join(sorted(allowed_resumes))
        raise ValueError(
            f"selected_resume must be one of the eligible choices. Allowed: {allowed}"
        )

    row = {
        "decision_timestamp": datetime.now(timezone.utc).isoformat(timespec="microseconds"),
        "queue_rank": _clean_text(queue_rank),
        "job_doc_id": _clean_text(job_doc_id),
        "job_company": _clean_text(job_company),
        "job_title": _clean_text(job_title),
        "planning_action": _clean_text(planning_action),
        "winner_resume": safe_winner,
        "winner_score": _clean_text(winner_score),
        "runner_up_resume": safe_runner,
        "runner_up_score": _clean_text(runner_up_score),
        "selected_resume": safe_selected,
        "decision": _normalize_operator_decision(decision),
        "note": _clean_text(note),
    }

    _validate_operator_decision_identity(row)
    postgres_write = _dual_write_operator_decision_postgres(row)

    return {
        "ok": True,
        "row": row,
        "csv_write_disabled": True,
        "postgres_write": postgres_write,
    }

def preview_planning_patch_selection_payload(
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    *,
    tailoring_json_path: str = "",
    selected_candidate_ids: Any = None,
) -> Dict[str, Any]:
    from src.tailoring.rendering import build_selected_patch_set_counterfactual_preview

    artifact_path = _resolve_planning_artifact_path(
        tailoring_json_path,
        output_dir=output_dir,
    )

    if artifact_path.suffix.lower() != ".json":
        raise ValueError("Patch selection preview requires a tailoring JSON artifact.")

    payload_data = _load_tailoring_json_artifact(artifact_path)

    replacement_candidates = list(payload_data.get("replacement_candidates", []) or [])
    if not replacement_candidates:
        raise ValueError("Tailoring artifact does not contain replacement candidates.")

    normalized_ids = _normalize_selected_patch_candidate_ids(selected_candidate_ids)
    if not normalized_ids:
        normalized_ids = _default_selected_candidate_ids_from_replacement_plan(payload_data)
    valid_candidate_ids = set(_tailoring_artifact_candidate_ids(payload_data))
    unknown_candidate_ids = [candidate_id for candidate_id in normalized_ids if candidate_id not in valid_candidate_ids]
    if unknown_candidate_ids:
        raise ValueError(
            f"Unknown candidate IDs for this artifact: {', '.join(sorted(unknown_candidate_ids))}"
        )

    preview = build_selected_patch_set_counterfactual_preview(
        payload_data,
        selected_candidate_ids=normalized_ids,
    )

    return {
        "ok": True,
        "path": str(artifact_path),
        "selected_patch_candidate_ids": normalized_ids,
        "selected_patch_set_counterfactual_preview": preview,
    }

def _dual_write_patch_selection_postgres(row: Dict[str, Any]) -> Dict[str, Any]:
    database_url = str(os.environ.get("DATABASE_URL", "") or "").strip()
    if not database_url:
        return {
            "attempted": False,
            "ok": False,
            "skipped": "missing_database_url",
            "table_name": "patch_selections",
        }

    try:
        payload = insert_patch_selection_row_to_postgres(
            record=row,
            database_url="",
            database_url_env="DATABASE_URL",
            psql_bin="psql",
            print_only=False,
            allow_contract_drift=False,
        )
        return {
            "attempted": True,
            "ok": True,
            "table_name": payload.get("table_name", "patch_selections"),
            "selection_id": str(payload.get("row", {}).get("selection_id", "") or ""),
            "contract_health_ok": bool(payload.get("contract_health_ok", False)),
            "command_text": str(payload.get("command_text", "") or ""),
        }
    except SystemExit as exc:
        return {
            "attempted": True,
            "ok": False,
            "table_name": "patch_selections",
            "error_type": "SystemExit",
            "error": str(exc),
        }
    except Exception as exc:
        return {
            "attempted": True,
            "ok": False,
            "table_name": "patch_selections",
            "error_type": exc.__class__.__name__,
            "error": str(exc),
        }
    
def record_planning_patch_selection_payload(
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    *,
    tailoring_json_path: str = "",
    job_doc_id: str = "",
    queue_rank: str = "",
    selected_resume: str = "",
    selected_candidate_ids: Any = None,
    note: str = "",
) -> Dict[str, Any]:
    from src.tailoring.rendering import build_selected_patch_set_counterfactual_preview

    artifact_path = _resolve_planning_artifact_path(
        tailoring_json_path,
        output_dir=output_dir,
    )

    if artifact_path.suffix.lower() != ".json":
        raise ValueError("Patch selection requires a tailoring JSON artifact.")

    payload_data = _load_tailoring_json_artifact(artifact_path)

    replacement_candidates = list(payload_data.get("replacement_candidates", []) or [])
    if not replacement_candidates:
        raise ValueError("Tailoring artifact does not contain replacement candidates.")

    normalized_ids = _normalize_selected_patch_candidate_ids(selected_candidate_ids)
    if not normalized_ids:
        normalized_ids = _default_selected_candidate_ids_from_replacement_plan(payload_data)

    valid_candidate_ids = set(_tailoring_artifact_candidate_ids(payload_data))
    unknown_candidate_ids = [candidate_id for candidate_id in normalized_ids if candidate_id not in valid_candidate_ids]
    if unknown_candidate_ids:
        raise ValueError(
            f"Unknown candidate IDs for this artifact: {', '.join(sorted(unknown_candidate_ids))}"
        )

    job = payload_data.get("job", {}) or {}
    selection = payload_data.get("selection", {}) or {}

    artifact_selected_resume = _clean_text(selection.get("selected_resume"))
    requested_selected_resume = _sanitize_optional_resume_filename(selected_resume)

    if requested_selected_resume and artifact_selected_resume and requested_selected_resume != artifact_selected_resume:
        raise ValueError(
            f"selected_resume does not match the tailoring artifact resume. "
            f"artifact={artifact_selected_resume!r} request={requested_selected_resume!r}"
        )

    row = {
        "selection_timestamp": datetime.now(timezone.utc).isoformat(timespec="microseconds"),
        "job_doc_id": _clean_text(job_doc_id) or _clean_text(job.get("job_doc_id")),
        "queue_rank": _clean_text(queue_rank),
        "job_company": _clean_text(job.get("company")),
        "job_title": _clean_text(job.get("title")),
        "selected_resume": requested_selected_resume or artifact_selected_resume,
        "tailoring_json_path": str(artifact_path),
        "artifact_signature": _tailoring_artifact_signature(payload_data),
        "selected_candidate_ids_json": _serialize_selected_patch_candidate_ids(normalized_ids),
        "note": _clean_text(note),
    }

    ja = _job_app()
    postgres_write = _dual_write_patch_selection_postgres(row)

    preview = build_selected_patch_set_counterfactual_preview(
        payload_data,
        selected_candidate_ids=normalized_ids,
    )

    return {
        "ok": True,
        "csv_write_disabled": True,
        "selected_patch_candidate_ids": normalized_ids,
        "selection": row,
        "postgres_write": postgres_write,
        "selected_patch_set_counterfactual_preview": preview,
    }

def _tailoring_workspace_draft_artifact_path(artifact_path: Path) -> Path:
    name = artifact_path.name
    suffix = "__tailoring.json"

    if name.endswith(suffix):
        prefix = name[:-len(suffix)]
        return artifact_path.with_name(f"{prefix}__tailoring_workspace_draft.json")

    return artifact_path.with_name(f"{artifact_path.stem}__tailoring_workspace_draft.json")


def _normalize_workspace_rewrite_review_decisions(value: Any) -> Dict[str, Dict[str, str]]:
    if isinstance(value, dict):
        raw_items = value
    else:
        raw_text = _clean_text(value)
        if not raw_text:
            return {}

        try:
            parsed = json.loads(raw_text)
        except Exception as exc:
            raise ValueError("rewrite_review_decisions must be a JSON object.") from exc

        if not isinstance(parsed, dict):
            raise ValueError("rewrite_review_decisions must be a JSON object.")

        raw_items = parsed

    normalized: Dict[str, Dict[str, str]] = {}

    for raw_key, raw_value in raw_items.items():
        candidate_id = _clean_text(raw_key)
        if not candidate_id:
            continue

        if isinstance(raw_value, dict):
            state = _clean_text(raw_value.get("state")).lower() or "pending"
            note = _clean_text(raw_value.get("note"))
        else:
            state = _clean_text(raw_value).lower() or "pending"
            note = ""

        if state not in _ALLOWED_REWRITE_REVIEW_STATES:
            allowed = ", ".join(sorted(_ALLOWED_REWRITE_REVIEW_STATES))
            raise ValueError(
                f"Invalid rewrite review state={state!r} for {candidate_id!r}. Allowed: {allowed}"
            )

        normalized[candidate_id] = {
            "state": state,
            "note": note,
        }

    return normalized

def _normalize_workspace_manual_bullet_edits(value: Any) -> Dict[str, str]:
    if isinstance(value, dict):
        raw_items = value
    else:
        raw_text = _clean_text(value)
        if not raw_text:
            return {}

        try:
            parsed = json.loads(raw_text)
        except Exception as exc:
            raise ValueError("manual_bullet_edits must be a JSON object.") from exc

        if not isinstance(parsed, dict):
            raise ValueError("manual_bullet_edits must be a JSON object.")

        raw_items = parsed

    normalized: Dict[str, str] = {}
    for raw_key, raw_value in raw_items.items():
        key = _clean_text(raw_key)
        if not key:
            continue
        normalized[key] = str(raw_value or "")

    return normalized


def _build_tailoring_workspace_default_draft_payload(
    artifact_path: Path,
    payload_data: Dict[str, Any],
    *,
    selected_resume: str = "",
) -> Dict[str, Any]:
    job = payload_data.get("job", {}) or {}
    selection = payload_data.get("selection", {}) or {}

    selected_candidate_ids = _normalize_selected_patch_candidate_ids(
        payload_data.get("selected_patch_candidate_ids", [])
    )
    if not selected_candidate_ids:
        selected_candidate_ids = _default_selected_candidate_ids_from_replacement_plan(
            payload_data
        )

    safe_selected_resume = (
        _sanitize_optional_resume_filename(selected_resume)
        or _sanitize_optional_resume_filename(selection.get("selected_resume"))
    )

    draft_path = _tailoring_workspace_draft_artifact_path(artifact_path)

    return {
        "draft_version": 1,
        "draft_status": "default",
        "saved_at": "",
        "tailoring_json_path": str(artifact_path),
        "draft_json_path": str(draft_path),
        "artifact_signature": _tailoring_artifact_signature(payload_data),
        "job_doc_id": _clean_text(job.get("job_doc_id")),
        "job_company": _clean_text(job.get("company")),
        "job_title": _clean_text(job.get("title")),
        "selected_resume": safe_selected_resume,
        "selected_patch_candidate_ids": selected_candidate_ids,
        "manual_bullet_edits": {},
        "note": "",
        "rewrite_review_decisions": {},
        "source_selected_patch_selection_status": _clean_text(
            payload_data.get("selected_patch_selection_status")
        ),
        "source_selected_patch_selection_note": _clean_text(
            payload_data.get("selected_patch_selection_note")
        ),
        "rewrite_review_telemetry": _build_workspace_rewrite_review_telemetry(
            payload_data,
            selected_candidate_ids=selected_candidate_ids,
            manual_bullet_edits={},
            rewrite_review_decisions={},
        ),
    }


def load_tailoring_workspace_draft_payload(
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    *,
    tailoring_json_path: str = "",
    selected_resume: str = "",
) -> Dict[str, Any]:
    artifact_path = _resolve_planning_artifact_path(
        tailoring_json_path,
        output_dir=output_dir,
    )

    if artifact_path.suffix.lower() != ".json":
        raise ValueError("Workspace draft loading requires a tailoring JSON artifact.")

    payload_data = _load_tailoring_json_artifact(artifact_path)

    if artifact_path.name.endswith("__tailoring.json"):
        payload_data = _rehydrate_legacy_tailoring_operator_payload(
            artifact_path,
            payload_data,
        )

    if payload_data.get("replacement_candidates") is not None:
        payload_data = _apply_saved_patch_selection_overlay(
            artifact_path,
            payload_data,
        )

    default_draft = _build_tailoring_workspace_default_draft_payload(
        artifact_path,
        payload_data,
        selected_resume=selected_resume,
    )

    draft_path = Path(default_draft["draft_json_path"])
    if not draft_path.exists():
        return {
            "ok": True,
            "draft_status": "default",
            "has_saved_draft": False,
            "draft": default_draft,
        }

    saved_data = _load_tailoring_json_artifact(draft_path)
    saved_signature = _clean_text(saved_data.get("artifact_signature"))
    current_signature = _clean_text(default_draft.get("artifact_signature"))

    if saved_signature and saved_signature != current_signature:
        stale_draft = dict(default_draft)
        stale_draft["draft_status"] = "stale_signature"
        stale_draft["note"] = (
            "Saved workspace draft was ignored because the tailoring artifact changed."
        )
        return {
            "ok": True,
            "draft_status": "stale_signature",
            "has_saved_draft": False,
            "draft": stale_draft,
        }

    valid_candidate_ids = set(_tailoring_artifact_candidate_ids(payload_data))
    saved_selected_ids = _normalize_selected_patch_candidate_ids(
        saved_data.get("selected_patch_candidate_ids", [])
    )
    saved_selected_ids = [
        candidate_id
        for candidate_id in saved_selected_ids
        if candidate_id in valid_candidate_ids
    ]
    saved_manual_edits = _normalize_workspace_manual_bullet_edits(
        saved_data.get("manual_bullet_edits", {})
    )
    saved_review_decisions = _derive_workspace_rewrite_review_decisions(
        payload_data,
        selected_candidate_ids=saved_selected_ids,
        manual_bullet_edits=saved_data.get("manual_bullet_edits", {}),
        rewrite_review_decisions=saved_data.get("rewrite_review_decisions", {}),
    )
    saved_review_telemetry = _build_workspace_rewrite_review_telemetry(
        payload_data,
        selected_candidate_ids=saved_selected_ids,
        manual_bullet_edits=saved_manual_edits,
        rewrite_review_decisions=saved_review_decisions,
    )

    merged = dict(default_draft)
    merged.update({
        "draft_status": "saved",
        "saved_at": _clean_text(saved_data.get("saved_at")),
        "selected_resume": (
            _sanitize_optional_resume_filename(saved_data.get("selected_resume"))
            or merged["selected_resume"]
        ),
        "selected_patch_candidate_ids": saved_selected_ids,
        "manual_bullet_edits": saved_manual_edits,
        "note": _clean_text(saved_data.get("note")),
        "rewrite_review_decisions": saved_review_decisions,
        "rewrite_review_telemetry": saved_review_telemetry,
    })

    return {
        "ok": True,
        "draft_status": "saved",
        "has_saved_draft": True,
        "draft": merged,
    }


def save_tailoring_workspace_draft_payload(
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    *,
    tailoring_json_path: str = "",
    selected_resume: str = "",
    selected_patch_candidate_ids: Any = None,
    manual_bullet_edits: Any = None,
    rewrite_review_decisions: Any = None,
    note: str = "",
) -> Dict[str, Any]:
    artifact_path = _resolve_planning_artifact_path(
        tailoring_json_path,
        output_dir=output_dir,
    )

    if artifact_path.suffix.lower() != ".json":
        raise ValueError("Workspace draft saving requires a tailoring JSON artifact.")

    payload_data = _load_tailoring_json_artifact(artifact_path)

    if artifact_path.name.endswith("__tailoring.json"):
        payload_data = _rehydrate_legacy_tailoring_operator_payload(
            artifact_path,
            payload_data,
        )

    if payload_data.get("replacement_candidates") is not None:
        payload_data = _apply_saved_patch_selection_overlay(
            artifact_path,
            payload_data,
        )

    draft_payload = _build_tailoring_workspace_default_draft_payload(
        artifact_path,
        payload_data,
        selected_resume=selected_resume,
    )

    valid_candidate_ids = set(_tailoring_artifact_candidate_ids(payload_data))
    requested_candidate_ids = _normalize_selected_patch_candidate_ids(
        selected_patch_candidate_ids
    )
    if not requested_candidate_ids:
        requested_candidate_ids = list(draft_payload["selected_patch_candidate_ids"])

    unknown_candidate_ids = [
        candidate_id
        for candidate_id in requested_candidate_ids
        if candidate_id not in valid_candidate_ids
    ]
    if unknown_candidate_ids:
        raise ValueError(
            f"Unknown candidate IDs for this artifact: {', '.join(sorted(unknown_candidate_ids))}"
        )

    manual_edit_map = _normalize_workspace_manual_bullet_edits(manual_bullet_edits)
    review_decision_map = _normalize_workspace_rewrite_review_decisions(
        rewrite_review_decisions
    )
    derived_review_decisions = _derive_workspace_rewrite_review_decisions(
        payload_data,
        selected_candidate_ids=requested_candidate_ids,
        manual_bullet_edits=manual_edit_map,
        rewrite_review_decisions=review_decision_map,
    )

    derived_review_telemetry = _build_workspace_rewrite_review_telemetry(
        payload_data,
        selected_candidate_ids=requested_candidate_ids,
        manual_bullet_edits=manual_edit_map,
        rewrite_review_decisions=derived_review_decisions,
    )
    
    saved_at = datetime.now(timezone.utc).isoformat(timespec="microseconds")
    draft_payload.update({
        "draft_status": "saved",
        "saved_at": saved_at,
        "selected_patch_candidate_ids": requested_candidate_ids,
        "manual_bullet_edits": manual_edit_map,
        "note": _clean_text(note),
        "rewrite_review_decisions": derived_review_decisions,
        "rewrite_review_telemetry": derived_review_telemetry,
    })

    draft_path = Path(draft_payload["draft_json_path"])
    draft_path.parent.mkdir(parents=True, exist_ok=True)
    draft_path.write_text(
        json.dumps(draft_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return {
        "ok": True,
        "draft_status": "saved",
        "has_saved_draft": True,
        "draft_json_path": str(draft_path),
        "draft": draft_payload,
    }

def _normalize_tailoring_workspace_compare_text(value: Any) -> str:
    return _normalize_tailoring_workspace_text_key(value)

def _normalize_tailoring_workspace_text_key(value: Any) -> str:
    text = str(value or "").lower()
    text = re.sub(r"[•▪◦·]", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^a-z0-9%$&.,+/\- ]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _tailoring_workspace_candidate_id(item: Dict[str, Any]) -> str:
    return _clean_text(item.get("replacement_candidate_id") or item.get("candidate_id"))


def _tailoring_workspace_bullet_key(item: Dict[str, Any]) -> str:
    candidate_id = _tailoring_workspace_candidate_id(item)
    if candidate_id:
        return f"candidate:{candidate_id}"

    original_text = _clean_text(item.get("original_text"))
    if not original_text:
        return ""

    return f"text:{_normalize_tailoring_workspace_text_key(original_text)}"


def _tailoring_workspace_surfaced_items(payload_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        *list(payload_data.get("app_ready_replacements", []) or []),
        *list(payload_data.get("direct_apply_optional_replacements", []) or []),
        *list(payload_data.get("direction_only_replacements", []) or []),
    ]


def _derive_workspace_rewrite_review_decisions(
    payload_data: Dict[str, Any],
    *,
    selected_candidate_ids: Any,
    manual_bullet_edits: Any,
    rewrite_review_decisions: Any,
) -> Dict[str, Dict[str, str]]:
    selected_set = set(_normalize_selected_patch_candidate_ids(selected_candidate_ids))
    manual_map = _normalize_workspace_manual_bullet_edits(manual_bullet_edits)
    decision_map = _normalize_workspace_rewrite_review_decisions(rewrite_review_decisions)

    derived: Dict[str, Dict[str, str]] = {}

    # Start with the explicit decision map so untouched entries survive.
    for candidate_id, row in decision_map.items():
        derived[candidate_id] = {
            "state": _clean_text(row.get("state")).lower() or "pending",
            "note": _clean_text(row.get("note")),
        }

    for item in _tailoring_workspace_surfaced_items(payload_data):
        candidate_id = _tailoring_workspace_candidate_id(item)
        if not candidate_id:
            continue

        current = dict(derived.get(candidate_id, {"state": "pending", "note": ""}))
        state = _clean_text(current.get("state")).lower() or "pending"
        note = _clean_text(current.get("note"))

        # Only infer edited_after_accept from already-accepted items.
        if state not in {"accepted", "edited_after_accept"}:
            derived[candidate_id] = {
                "state": state,
                "note": note,
            }
            continue

        if candidate_id not in selected_set:
            # If it is no longer selected, keep the explicit state as-is.
            derived[candidate_id] = {
                "state": state,
                "note": note,
            }
            continue

        bullet_key = _tailoring_workspace_bullet_key(item)
        if not bullet_key:
            derived[candidate_id] = {
                "state": state,
                "note": note,
            }
            continue

        manual_text = _clean_text(manual_map.get(bullet_key))
        selected_patch_text = _clean_text(item.get("final_replacement_text"))

        if not manual_text or not selected_patch_text:
            # No actual manual override to compare, so treat this as accepted-as-is.
            derived[candidate_id] = {
                "state": "accepted",
                "note": note,
            }
            continue

        manual_norm = _normalize_tailoring_workspace_compare_text(manual_text)
        selected_norm = _normalize_tailoring_workspace_compare_text(selected_patch_text)

        if manual_norm and selected_norm and manual_norm != selected_norm:
            derived[candidate_id] = {
                "state": "edited_after_accept",
                "note": note,
            }
        else:
            derived[candidate_id] = {
                "state": "accepted",
                "note": note,
            }

    return derived

def _build_workspace_rewrite_review_telemetry(
    payload_data: Dict[str, Any],
    *,
    selected_candidate_ids: Any,
    manual_bullet_edits: Any,
    rewrite_review_decisions: Any,
) -> Dict[str, Any]:
    selected_ids = _normalize_selected_patch_candidate_ids(selected_candidate_ids)
    selected_set = set(selected_ids)
    manual_map = _normalize_workspace_manual_bullet_edits(manual_bullet_edits)
    effective_decisions = _derive_workspace_rewrite_review_decisions(
        payload_data,
        selected_candidate_ids=selected_ids,
        manual_bullet_edits=manual_map,
        rewrite_review_decisions=rewrite_review_decisions,
    )

    surfaced_candidate_ids: List[str] = []
    seen = set()
    for item in _tailoring_workspace_surfaced_items(payload_data):
        candidate_id = _tailoring_workspace_candidate_id(item)
        if not candidate_id or candidate_id in seen:
            continue
        seen.add(candidate_id)
        surfaced_candidate_ids.append(candidate_id)

    pending_candidate_ids: List[str] = []
    reviewed_candidate_ids: List[str] = []

    pending_count = 0
    accepted_count = 0
    accepted_as_is_count = 0
    edited_after_accept_count = 0
    rejected_count = 0

    for candidate_id in surfaced_candidate_ids:
        state_row = effective_decisions.get(candidate_id, {"state": "pending", "note": ""})
        state = _clean_text(state_row.get("state")).lower() or "pending"

        if state == "pending":
            pending_count += 1
            pending_candidate_ids.append(candidate_id)
        else:
            reviewed_candidate_ids.append(candidate_id)

        if state == "accepted":
            accepted_count += 1
            accepted_as_is_count += 1
        elif state == "edited_after_accept":
            accepted_count += 1
            edited_after_accept_count += 1
        elif state == "rejected":
            rejected_count += 1

    reviewed_count = accepted_count + rejected_count
    remaining_to_review_count = pending_count

    return {
        "pending_count": pending_count,
        "accepted_count": accepted_count,
        "accepted_as_is_count": accepted_as_is_count,
        "edited_after_accept_count": edited_after_accept_count,
        "rejected_count": rejected_count,
        "reviewed_count": reviewed_count,
        "remaining_to_review_count": remaining_to_review_count,
        "selected_candidate_count": len(selected_set),
        "manual_edit_count": len(manual_map),
        "reviewed_candidate_ids": reviewed_candidate_ids,
        "pending_candidate_ids": pending_candidate_ids,
    }


def _build_tailoring_workspace_effective_patch_specs(
    payload_data: Dict[str, Any],
    *,
    selected_candidate_ids: List[str],
    manual_bullet_edits: Dict[str, str],
) -> Tuple[List[Dict[str, Any]], List[str]]:
    selected_set = set(_normalize_selected_patch_candidate_ids(selected_candidate_ids))
    manual_map = {
        _clean_text(key): str(value or "")
        for key, value in dict(manual_bullet_edits or {}).items()
        if _clean_text(key)
    }

    unresolved_manual_keys = set(manual_map.keys())
    patch_specs: List[Dict[str, Any]] = []
    seen_bullet_keys = set()

    for item in _tailoring_workspace_surfaced_items(payload_data):
        original_text = _clean_text(item.get("original_text"))
        if not original_text:
            continue

        bullet_key = _tailoring_workspace_bullet_key(item)
        if not bullet_key or bullet_key in seen_bullet_keys:
            continue
        seen_bullet_keys.add(bullet_key)

        candidate_id = _tailoring_workspace_candidate_id(item)

        selected_patch_text = ""
        if candidate_id and candidate_id in selected_set:
            selected_patch_text = _clean_text(item.get("final_replacement_text"))

        has_manual_override = bullet_key in manual_map
        if has_manual_override:
            unresolved_manual_keys.discard(bullet_key)

        effective_patch_text = (
            manual_map.get(bullet_key)
            if has_manual_override
            else selected_patch_text
        )

        if not effective_patch_text or effective_patch_text == original_text:
            continue

        patch_specs.append({
            "bullet_key": bullet_key,
            "candidate_id": candidate_id,
            "source_bullet_id": _clean_text(item.get("source_bullet_id")),
            "source_raw_text": original_text,
            "patch_text": effective_patch_text,
            "patch_source": "manual_edit" if has_manual_override else "selected_patch",
        })

    return patch_specs, sorted(unresolved_manual_keys)


def _load_job_record_for_workspace_preview(
    job_doc_id: str,
    job_corpus_path: Path = DEFAULT_CORPUS_PATH,
) -> Dict[str, Any]:
    from src.matching.job_adapter import build_job_evidence

    clean_job_doc_id = _clean_text(job_doc_id)
    if not clean_job_doc_id:
        raise ValueError("Workspace draft preview requires job_doc_id.")

    if not job_corpus_path.exists():
        raise ValueError(f"Missing job corpus: {job_corpus_path}")

    with job_corpus_path.open("r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue

            record = json.loads(line)
            record_job_doc_id = _clean_text(getattr(build_job_evidence(record), "job_doc_id", ""))
            if record_job_doc_id == clean_job_doc_id:
                return record

    raise ValueError(f"Could not find job_doc_id in corpus: {clean_job_doc_id}")


def _load_resume_evidence_for_workspace_preview(resume_name: str):
    from src.resume.document_store import load_resume_documents_by_name
    from src.resume.evidence_builder import build_resume_evidence

    safe_resume_name = _sanitize_resume_filename(resume_name)
    documents = load_resume_documents_by_name([safe_resume_name])

    if not documents:
        raise ValueError(f"Could not load resume document: {safe_resume_name}")

    return build_resume_evidence(documents[0])


def _workspace_preview_dimension_deltas(
    original_result: Any,
    projected_result: Any,
) -> Dict[str, float]:
    original_map = {
        str(dim.name): float(dim.weighted_score)
        for dim in list(getattr(original_result, "dimension_scores", []) or [])
    }
    projected_map = {
        str(dim.name): float(dim.weighted_score)
        for dim in list(getattr(projected_result, "dimension_scores", []) or [])
    }

    deltas: Dict[str, float] = {}
    for name in sorted(set(original_map) | set(projected_map)):
        delta = projected_map.get(name, 0.0) - original_map.get(name, 0.0)
        if abs(delta) > 1e-12:
            deltas[name] = round(delta, 6)

    return deltas


def _build_workspace_counterfactual_preview(
    original_result: Any,
    projected_result: Any,
    *,
    selected_candidate_ids: List[str],
    patch_specs: List[Dict[str, Any]],
    preview_note: str,
) -> Dict[str, Any]:
    dimension_deltas = _workspace_preview_dimension_deltas(
        original_result,
        projected_result,
    )

    original_missing = list(getattr(original_result.prefilter, "missing_requirements", []) or [])
    projected_missing = list(getattr(projected_result.prefilter, "missing_requirements", []) or [])
    original_matched = list(getattr(original_result.prefilter, "matched_terms", []) or [])
    projected_matched = list(getattr(projected_result.prefilter, "matched_terms", []) or [])

    overall_delta = float(projected_result.final_score) - float(original_result.final_score)

    return {
        "status": "scored",
        "note": preview_note,
        "original_final_score": round(float(original_result.final_score), 6),
        "projected_final_score": round(float(projected_result.final_score), 6),
        "projected_overall_delta": round(overall_delta, 6),
        "projected_dimension_deltas": dimension_deltas,
        "scorer_visible_evidence_changed": bool(
            dimension_deltas
            or original_missing != projected_missing
            or original_matched != projected_matched
            or abs(overall_delta) > 1e-12
        ),
        "selected_patch_count": len(selected_candidate_ids),
        "selected_candidate_ids": list(selected_candidate_ids),
        "requested_candidate_ids": list(selected_candidate_ids),
        "missing_candidate_ids": [],
        "ineligible_candidate_ids": [],
        "duplicate_source_bullet_ids": [],
        "selection_mode": "workspace_draft",
        "workspace_patch_count": len(patch_specs),
    }

def preview_tailoring_workspace_draft_payload(
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    *,
    tailoring_json_path: str = "",
    selected_resume: str = "",
    selected_patch_candidate_ids: Any = None,
    manual_bullet_edits: Any = None,
) -> Dict[str, Any]:
    from src.matching.job_adapter import build_job_evidence
    from src.matching.scorer import score_resume_job_match
    from src.resume.evidence_builder import build_counterfactual_resume_evidence

    draft_response = load_tailoring_workspace_draft_payload(
        output_dir=output_dir,
        tailoring_json_path=tailoring_json_path,
        selected_resume=selected_resume,
    )
    draft = dict(draft_response.get("draft", {}) or {})

    artifact_path = _resolve_planning_artifact_path(
        tailoring_json_path,
        output_dir=output_dir,
    )

    if artifact_path.suffix.lower() != ".json":
        raise ValueError("Workspace draft preview requires a tailoring JSON artifact.")

    payload_data = _load_tailoring_json_artifact(artifact_path)

    if artifact_path.name.endswith("__tailoring.json"):
        payload_data = _rehydrate_legacy_tailoring_operator_payload(
            artifact_path,
            payload_data,
        )

    if payload_data.get("replacement_candidates") is not None:
        payload_data = _apply_saved_patch_selection_overlay(
            artifact_path,
            payload_data,
        )

    valid_candidate_ids = set(_tailoring_artifact_candidate_ids(payload_data))

    if selected_patch_candidate_ids is None:
        effective_selected_ids = _normalize_selected_patch_candidate_ids(
            draft.get("selected_patch_candidate_ids", [])
        )
    else:
        effective_selected_ids = _normalize_selected_patch_candidate_ids(
            selected_patch_candidate_ids
        )

    unknown_candidate_ids = [
        candidate_id
        for candidate_id in effective_selected_ids
        if candidate_id not in valid_candidate_ids
    ]
    if unknown_candidate_ids:
        raise ValueError(
            f"Unknown candidate IDs for this artifact: {', '.join(sorted(unknown_candidate_ids))}"
        )

    if manual_bullet_edits is None:
        effective_manual_edits = _normalize_workspace_manual_bullet_edits(
            draft.get("manual_bullet_edits", {})
        )
    else:
        effective_manual_edits = _normalize_workspace_manual_bullet_edits(
            manual_bullet_edits
        )

    effective_review_decisions = _derive_workspace_rewrite_review_decisions(
        payload_data,
        selected_candidate_ids=effective_selected_ids,
        manual_bullet_edits=effective_manual_edits,
        rewrite_review_decisions=draft.get("rewrite_review_decisions", {}),
    )

    effective_review_telemetry = _build_workspace_rewrite_review_telemetry(
        payload_data,
        selected_candidate_ids=effective_selected_ids,
        manual_bullet_edits=effective_manual_edits,
        rewrite_review_decisions=effective_review_decisions,
    )

    selection = payload_data.get("selection", {}) or {}
    job = payload_data.get("job", {}) or {}

    effective_selected_resume = (
        _sanitize_optional_resume_filename(selected_resume)
        or _sanitize_optional_resume_filename(draft.get("selected_resume"))
        or _sanitize_optional_resume_filename(selection.get("selected_resume"))
    )
    if not effective_selected_resume:
        raise ValueError("Workspace draft preview requires a selected resume.")

    original_resume = _load_resume_evidence_for_workspace_preview(effective_selected_resume)
    job_record = _load_job_record_for_workspace_preview(
        _clean_text(job.get("job_doc_id"))
    )
    job_evidence = build_job_evidence(job_record)

    original_result = score_resume_job_match(original_resume, job_evidence)
    original_score = round(float(original_result.final_score), 6)

    patch_specs, unresolved_manual_keys = _build_tailoring_workspace_effective_patch_specs(
        payload_data,
        selected_candidate_ids=effective_selected_ids,
        manual_bullet_edits=effective_manual_edits,
    )

    manual_edit_count = len(effective_manual_edits)

    if not patch_specs:
        if unresolved_manual_keys:
            preview_status = "workspace_draft_rescore_failed"
            preview_note = (
                "Workspace draft edits could not be mapped back to surfaced bullets for rescoring."
            )
        else:
            preview_status = "no_previewable_changes"
            preview_note = "No previewable workspace draft changes were found."

        return {
            "ok": True,
            "preview_status": preview_status,
            "preview_note": preview_note,
            "tailoring_json_path": str(artifact_path),
            "draft_status": _clean_text(draft_response.get("draft_status")),
            "has_saved_draft": bool(draft_response.get("has_saved_draft", False)),
            "selected_patch_candidate_ids": effective_selected_ids,
            "manual_bullet_edits": effective_manual_edits,
            "manual_edit_count": manual_edit_count,
            "manual_edit_rescore_supported": True,
            "needs_full_draft_rescore": False,
            "original_score": original_score,
            "projected_score": None,
            "projected_delta": None,
            "selected_patch_set_counterfactual_preview": None,
            "unresolved_manual_edit_keys": unresolved_manual_keys,
            "rewrite_review_decisions": effective_review_decisions,
            "rewrite_review_telemetry": effective_review_telemetry,
        }

    counterfactual_resume = original_resume
    patch_status = "ok"

    for patch in patch_specs:
        counterfactual_resume, patch_status = build_counterfactual_resume_evidence(
            counterfactual_resume,
            source_bullet_id=str(patch.get("source_bullet_id", "") or ""),
            patch_text=str(patch.get("patch_text", "") or ""),
            source_raw_text=str(patch.get("source_raw_text", "") or ""),
        )
        if counterfactual_resume is None:
            break

    if counterfactual_resume is None:
        preview_note = f"Workspace draft rescoring failed: {patch_status}."
        if unresolved_manual_keys:
            preview_note += f" Ignored {len(unresolved_manual_keys)} unmapped manual edit key(s)."

        return {
            "ok": True,
            "preview_status": "workspace_draft_rescore_failed",
            "preview_note": preview_note,
            "tailoring_json_path": str(artifact_path),
            "draft_status": _clean_text(draft_response.get("draft_status")),
            "has_saved_draft": bool(draft_response.get("has_saved_draft", False)),
            "selected_patch_candidate_ids": effective_selected_ids,
            "manual_bullet_edits": effective_manual_edits,
            "manual_edit_count": manual_edit_count,
            "manual_edit_rescore_supported": True,
            "needs_full_draft_rescore": False,
            "original_score": original_score,
            "projected_score": None,
            "projected_delta": None,
            "selected_patch_set_counterfactual_preview": None,
            "patch_status": patch_status,
            "unresolved_manual_edit_keys": unresolved_manual_keys,
            "rewrite_review_decisions": effective_review_decisions,
            "rewrite_review_telemetry": effective_review_telemetry,
        }

    projected_result = score_resume_job_match(counterfactual_resume, job_evidence)
    projected_score = round(float(projected_result.final_score), 6)
    projected_delta = round(projected_score - original_score, 6)

    note_parts: List[str] = []
    if effective_selected_ids:
        note_parts.append(f"{len(effective_selected_ids)} selected rewrite(s)")
    if manual_edit_count:
        note_parts.append(f"{manual_edit_count} manual edit(s)")

    if note_parts:
        preview_note = "Workspace draft rescored using " + " and ".join(note_parts) + "."
    else:
        preview_note = "Workspace draft rescored."

    if unresolved_manual_keys:
        preview_note += f" Ignored {len(unresolved_manual_keys)} unmapped manual edit key(s)."

    preview = _build_workspace_counterfactual_preview(
        original_result,
        projected_result,
        selected_candidate_ids=effective_selected_ids,
        patch_specs=patch_specs,
        preview_note=preview_note,
    )

    return {
        "ok": True,
        "preview_status": "workspace_draft_rescored",
        "preview_note": preview_note,
        "tailoring_json_path": str(artifact_path),
        "draft_status": _clean_text(draft_response.get("draft_status")),
        "has_saved_draft": bool(draft_response.get("has_saved_draft", False)),
        "selected_patch_candidate_ids": effective_selected_ids,
        "manual_bullet_edits": effective_manual_edits,
        "manual_edit_count": manual_edit_count,
        "manual_edit_rescore_supported": True,
        "needs_full_draft_rescore": False,
        "original_score": original_score,
        "projected_score": projected_score,
        "projected_delta": projected_delta,
        "selected_patch_set_counterfactual_preview": preview,
        "unresolved_manual_edit_keys": unresolved_manual_keys,
        "rewrite_review_decisions": effective_review_decisions,
        "rewrite_review_telemetry": effective_review_telemetry,
    }

def record_application_action_payload(
    *,
    job_doc_id: str = "",
    job_url: str = "",
    job_company: str = "",
    job_title: str = "",
    application_status: str = "",
    source_view: str = "",
    note: str = "",
) -> Dict[str, Any]:
    row = application_action_db_row(
        {
            "action_timestamp": datetime.now(timezone.utc).isoformat(timespec="microseconds"),
            "job_doc_id": _clean_text(job_doc_id),
            "job_url": _clean_text(job_url),
            "job_company": _clean_text(job_company),
            "job_title": _clean_text(job_title),
            "application_status": _normalize_application_status(application_status),
            "source_view": _clean_text(source_view),
            "note": _clean_text(note),
        }
    )

    _validate_application_identity(row)
    postgres_write = _dual_write_application_action_postgres(row)

    return {
        "ok": True,
        "row": row,
        "overlay": _application_overlay_from_row(row),
        "postgres_write": postgres_write,
    }

def application_actions_payload(
    application_status: str = "",
    company_contains: str = "",
    title_contains: str = "",
    limit: int = 15,
    page: int = 1,
) -> Dict[str, Any]:
    ja = _job_app()
    rows = _load_latest_application_actions()

    if application_status:
        status_target = _normalize_application_status(application_status)
        rows = [
            row for row in rows
            if _clean_text(row.get("application_status")) == status_target
        ]

    if company_contains:
        needle = ja._normalize_text(company_contains)
        rows = [
            row for row in rows
            if needle in ja._normalize_text(row.get("job_company", ""))
        ]

    if title_contains:
        needle = ja._normalize_text(title_contains)
        rows = [
            row for row in rows
            if needle in ja._normalize_text(row.get("job_title", ""))
        ]

    requested_limit = max(int(limit or 15), 1)
    current_page = max(int(page or 1), 1)
    page_size = 15

    rows = rows[:requested_limit]

    total_count = len(rows)
    total_pages = max((total_count + page_size - 1) // page_size, 1)
    current_page = min(current_page, total_pages)

    start_idx = (current_page - 1) * page_size
    end_idx = start_idx + page_size
    page_rows = rows[start_idx:end_idx]

    return {
        "filters": {
            "application_status": application_status,
            "company_contains": company_contains,
            "title_contains": title_contains,
            "limit": requested_limit,
            "page": current_page,
        },
        "rows": page_rows,
        "count": len(page_rows),
        "total_count": total_count,
        "page": current_page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_prev_page": current_page > 1,
        "has_next_page": current_page < total_pages,
    }

def applied_jobs_payload(
    company_contains: str = "",
    title_contains: str = "",
    limit: int = 15,
    page: int = 1,
) -> Dict[str, Any]:
    return application_actions_payload(
        application_status="APPLIED",
        company_contains=company_contains,
        title_contains=title_contains,
        limit=limit,
        page=page,
    )

def jobs_search_lite_payload(
    request: str,
    top_k: int = 10,
) -> Dict[str, Any]:
    from src.rag.corpus_store import _load_job_corpus
    from src.rag.lexical_retriever import _lexical_search
    from src.rag.query_filters import _infer_metadata_filters

    inferred_filters = _infer_metadata_filters(request)
    lexical_results = _lexical_search(
        query=request,
        top_k=top_k,
        filters=inferred_filters or None,
    )

    compact_results = []
    for row in lexical_results:
        metadata = row.get("metadata", {}) or {}
        compact_results.append({
            "score": row.get("score"),
            "doc_id": metadata.get("doc_id", ""),
            "company": metadata.get("company", ""),
            "title": metadata.get("title", ""),
            "location": metadata.get("location", ""),
            "source": metadata.get("source", ""),
            "job_url": metadata.get("job_url", ""),
            "posted_at": metadata.get("posted_at", ""),
            "visa_sponsorship": metadata.get("visa_sponsorship", ""),
            "ai_fit_score": metadata.get("ai_fit_score"),
        })

    compact_results = _overlay_application_actions(compact_results)

    return {
        "ok": True,
        "request": request,
        "mode": "search_lite",
        "corpus_count": len(_load_job_corpus()),
        "inferred_filters": inferred_filters,
        "result_count": len(compact_results),
        "results": compact_results,
    }

def rag_search_payload(
    request: str,
    top_k: int = 5,
    fetch_k: int = 15,
    output_mode: str = "compact",
    include_diagnostics: bool = False,
) -> Dict[str, Any]:
    from src.rag.rag_executor import execute_rag_request

    payload = execute_rag_request(
        request=request,
        top_k=top_k,
        fetch_k=fetch_k,
        filters=None,
        output_mode=output_mode,
        include_diagnostics=include_diagnostics,
        intent_override="search_jobs",
    )

    if payload.get("ok") and isinstance(payload.get("response"), dict):
        response = dict(payload.get("response", {}))
        response["results"] = _overlay_application_actions(response.get("results", []) or [])
        payload = dict(payload)
        payload["response"] = response

    return payload

def rag_answer_payload(
    request: str,
    top_k: int = 5,
    fetch_k: int = 15,
    output_mode: str = "compact",
    include_diagnostics: bool = False,
) -> Dict[str, Any]:
    from src.rag.rag_executor import execute_rag_request

    payload = execute_rag_request(
        request=request,
        top_k=top_k,
        fetch_k=fetch_k,
        filters=None,
        output_mode=output_mode,
        include_diagnostics=include_diagnostics,
        intent_override="answer_job_query",
    )

    if payload.get("ok") and isinstance(payload.get("response"), dict):
        response = dict(payload.get("response", {}))
        response["sources"] = _overlay_application_actions(response.get("sources", []) or [])
        response["job_evidence"] = _overlay_application_actions(response.get("job_evidence", []) or [])
        payload = dict(payload)
        payload["response"] = response

    return payload