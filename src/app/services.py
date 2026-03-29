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

from src.config.settings import (
    ACTIVE_APPLICATION_PLANNING_OUTPUT_DIR,
    SCHEDULER_RUN_HISTORY_PATH,
)
from src.pipeline.scheduler import (
    build_scheduled_job_command,
    get_scheduled_job_definition,
    get_scheduled_job_definitions,
)
from src.storage.scheduler_store import (
    scheduler_job_definition_seed_rows,
    scheduler_postgres_table_specs,
    scheduler_schema_sql_payload,
)

DEFAULT_OUTPUT_DIR = Path(
    os.environ.get("APPLICATION_PLANNING_OUTPUT_DIR", ACTIVE_APPLICATION_PLANNING_OUTPUT_DIR)
).expanduser()
DEFAULT_CORPUS_PATH = Path("data/rag/job_corpus.jsonl")
DEFAULT_DECISIONS_PATH = DEFAULT_OUTPUT_DIR / "operator_decisions.csv"
DEFAULT_APPLICATION_ACTIONS_PATH = DEFAULT_OUTPUT_DIR / "application_actions.csv"
DEFAULT_PIPELINE_LOG_PATH = DEFAULT_OUTPUT_DIR / "live_pipeline_run.log"
DEFAULT_PIPELINE_STATUS_PATH = DEFAULT_OUTPUT_DIR / "live_pipeline_status.json"
DEFAULT_PROFILE_RESUME_DIR = Path(
    os.environ.get("PROFILE_RESUME_DIR", "data/profile_resumes")
).expanduser()
DEFAULT_PATCH_SELECTIONS_PATH = DEFAULT_OUTPUT_DIR / "patch_selections.csv"
DEFAULT_SCHEDULER_RUN_HISTORY_PATH = Path(SCHEDULER_RUN_HISTORY_PATH)

PATCH_SELECTION_HEADERS = [
    "selection_timestamp",
    "job_doc_id",
    "queue_rank",
    "job_company",
    "job_title",
    "selected_resume",
    "tailoring_json_path",
    "artifact_signature",
    "selected_candidate_ids_json",
    "note",
]

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
    "error": "",
}

APPLICATION_ACTION_HEADERS = [
    "action_timestamp",
    "job_doc_id",
    "job_url",
    "job_company",
    "job_title",
    "application_status",
    "source_view",
    "note",
]

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

OPERATOR_DECISION_HEADERS = [
    "decision_timestamp",
    "queue_rank",
    "job_doc_id",
    "job_company",
    "job_title",
    "planning_action",
    "winner_resume",
    "winner_score",
    "runner_up_resume",
    "runner_up_score",
    "selected_resume",
    "decision",
    "note",
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
        "error": _PIPELINE_RUN_STATE.get("error", ""),
        "is_running": status == "running",
    }


def pipeline_status_payload() -> Dict[str, Any]:
    snapshot = _pipeline_status_snapshot()
    runtime_status = _load_runtime_status_file(snapshot.get("status_path", ""))

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

def scheduler_storage_contract_payload() -> Dict[str, Any]:
    schema_payload = scheduler_schema_sql_payload()

    return {
        "ok": True,
        "tables": scheduler_postgres_table_specs(),
        "seed_rows": {
            "scheduler_job_definitions": scheduler_job_definition_seed_rows(),
        },
        "schema_sql": schema_payload["sql"],
        "schema_sql_path": schema_payload["path"],
    }

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
        delete_seen_data=normalized_delete_seen_data,
    )
    cmd = ja._build_main_cmd(args, planning_only=bool(planning_only))

    runtime_payload = {
        "run_id": run_id,
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


def _load_latest_patch_selection_overlay(
    patch_selections_path: Path = DEFAULT_PATCH_SELECTIONS_PATH,
) -> Dict[str, Dict[str, str]]:
    if not patch_selections_path.exists():
        return {}

    ja = _job_app()
    rows = ja._load_csv_rows(patch_selections_path)
    latest_by_path: Dict[str, Dict[str, str]] = {}

    for row in rows:
        artifact_path = _clean_text(row.get("tailoring_json_path"))
        if not artifact_path:
            continue
        latest_by_path[artifact_path] = dict(row)

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

def _apply_saved_patch_selection_overlay(
    artifact_path: Path,
    payload_data: Dict[str, Any],
    patch_selections_path: Path = DEFAULT_PATCH_SELECTIONS_PATH,
) -> Dict[str, Any]:
    from src.tailoring.rendering import build_selected_patch_set_counterfactual_preview

    data = _ensure_tailoring_preview_fields(payload_data)
    data.setdefault("selected_patch_candidate_ids", [])
    data.setdefault("selected_patch_selection_status", "none")
    data.setdefault("selected_patch_selection_note", "")
    data.setdefault("selected_patch_selection_timestamp", "")

    latest_by_path = _load_latest_patch_selection_overlay(patch_selections_path)
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
    decisions_path: Path = DEFAULT_DECISIONS_PATH,
    *,
    job_doc_id: str = "",
    queue_rank: str = "",
    selected_resume: str = "",
    generate_llm_tailoring: bool = False,
    refresh_llm_tailoring: bool = False,
) -> Dict[str, Any]:
    ja = _job_app()
    merged_rows = ja._build_job_index(output_dir, decisions_path)
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


def _load_latest_application_actions(
    actions_path: Path = DEFAULT_APPLICATION_ACTIONS_PATH,
) -> List[Dict[str, str]]:
    ja = _job_app()
    rows = ja._load_csv_rows(actions_path)
    latest_by_key: Dict[str, Dict[str, str]] = {}

    for row in rows:
        key = _application_action_key(row)
        if not key:
            continue
        latest_by_key[key] = dict(row)

    latest_rows = list(latest_by_key.values())
    latest_rows.sort(
        key=lambda row: (
            str(row.get("action_timestamp", "") or ""),
            _clean_text(row.get("job_company")),
            _clean_text(row.get("job_title")),
        ),
        reverse=True,
    )
    return latest_rows

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


def _load_latest_application_action_overlay(
    actions_path: Path = DEFAULT_APPLICATION_ACTIONS_PATH,
) -> Dict[str, Dict[str, Any]]:
    latest_rows = _load_latest_application_actions(actions_path)
    latest_by_key: Dict[str, Dict[str, Any]] = {}

    for row in latest_rows:
        overlay = _application_overlay_from_row(row)
        for key in _application_row_key_candidates(row):
            latest_by_key[key] = overlay

    return latest_by_key


def _overlay_application_actions(
    rows: List[Dict[str, Any]],
    actions_path: Path = DEFAULT_APPLICATION_ACTIONS_PATH,
) -> List[Dict[str, Any]]:
    latest_by_key = _load_latest_application_action_overlay(actions_path)

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
                or metadata.get("company")
            )
            job_title = _clean_text(
                record.get("job_title")
                or record.get("title")
                or metadata.get("title")
            )
            posted_at = _clean_text(
                record.get("posted_at")
                or metadata.get("posted_at")
            )

            if not posted_at and not job_url:
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
    if not latest_by_key:
        return rows

    overlaid_rows: List[Dict[str, Any]] = []

    for row in rows:
        merged = dict(row)
        merged.setdefault("posted_at", "")
        merged.setdefault("job_url", _clean_text(merged.get("job_doc_id")))

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
    decisions_path: Path = DEFAULT_DECISIONS_PATH,
    top_k: int = 10,
) -> Dict[str, Any]:
    ja = _job_app()
    best_rows = ja._load_csv_rows(output_dir / "best_resume_variant_by_job.csv")
    shortlist_rows = ja._load_csv_rows(output_dir / "application_shortlist_by_job.csv")
    queue_rows = ja._load_csv_rows(output_dir / "application_execution_queue.csv")
    manifest_rows = ja._load_csv_rows(output_dir / "job_packet_manifest.csv")
    decision_rows = ja._load_csv_rows(decisions_path)

    merged_rows = ja._build_job_index(output_dir, decisions_path)
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

    latest_by_key = ja._load_latest_decision_overlay(decisions_path)
    application_overlay_by_key = _load_latest_application_action_overlay(
        DEFAULT_APPLICATION_ACTIONS_PATH
    )
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
            "operator_decisions_file": str(decisions_path),
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
    decisions_path: Path = DEFAULT_DECISIONS_PATH,
    **filters: Any,
) -> Dict[str, Any]:
    ja = _job_app()
    rows = ja._build_job_index(output_dir, decisions_path)
    args = _make_args(**filters)
    selected = ja._select_browse_rows(rows, args)
    selected = _overlay_job_metadata(selected, job_corpus=DEFAULT_CORPUS_PATH)
    selected = _overlay_application_actions(selected)
    return {
        "filters": filters,
        "rows": selected,
        "count": len(selected),
    }


def review_payload(
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    decisions_path: Path = DEFAULT_DECISIONS_PATH,
    **filters: Any,
) -> Dict[str, Any]:
    ja = _job_app()
    rows = ja._build_job_index(output_dir, decisions_path)
    args = _make_args(**filters)
    selected = ja._select_review_rows(rows, args)
    selected = _overlay_job_metadata(selected, job_corpus=DEFAULT_CORPUS_PATH)
    selected = _overlay_application_actions(selected)
    return {
        "filters": filters,
        "rows": selected,
        "count": len(selected),
    }


def workflow_payload(
    view: str,
    limit: int = 20,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    decisions_path: Path = DEFAULT_DECISIONS_PATH,
) -> Dict[str, Any]:
    ja = _job_app()
    rows = ja._build_job_index(output_dir, decisions_path)
    selected = ja._workflow_view_rows(rows, view)[:limit]
    selected = _overlay_job_metadata(selected, job_corpus=DEFAULT_CORPUS_PATH)
    selected = _overlay_application_actions(selected)
    return {
        "view": view,
        "rows": selected,
        "count": len(selected),
    }


def planner_payload(
    request: str,
    limit: int = 20,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    decisions_path: Path = DEFAULT_DECISIONS_PATH,
) -> Dict[str, Any]:
    ja = _job_app()
    view = ja._infer_planner_view(request)
    rows = ja._build_job_index(output_dir, decisions_path)
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
    patch_selections_path: Path = DEFAULT_PATCH_SELECTIONS_PATH,
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
                    patch_selections_path=patch_selections_path,
                )
        payload["data"] = data
    else:
        payload["text"] = text

    return payload

def decisions_payload(
    decisions_path: Path = DEFAULT_DECISIONS_PATH,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    **filters: Any,
) -> Dict[str, Any]:
    ja = _job_app()
    rows = ja._load_csv_rows(decisions_path)
    args = _make_args(**filters)
    selected = ja._select_decision_rows(rows, args)
    selected = _overlay_job_metadata(selected, job_corpus=DEFAULT_CORPUS_PATH)
    selected = _overlay_application_actions(selected)
    return {
        "filters": filters,
        "rows": selected,
        "count": len(selected),
        "decisions_path": str(decisions_path),
    }

def record_operator_resume_selection_payload(
    decisions_path: Path = DEFAULT_DECISIONS_PATH,
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
    ja._append_csv_row(decisions_path, OPERATOR_DECISION_HEADERS, row)

    return {
        "ok": True,
        "row": row,
        "decisions_path": str(decisions_path),
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

def record_planning_patch_selection_payload(
    patch_selections_path: Path = DEFAULT_PATCH_SELECTIONS_PATH,
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
    ja._append_csv_row(
        patch_selections_path,
        PATCH_SELECTION_HEADERS,
        row,
    )

    preview = build_selected_patch_set_counterfactual_preview(
        payload_data,
        selected_candidate_ids=normalized_ids,
    )

    return {
        "ok": True,
        "patch_selections_path": str(patch_selections_path),
        "selected_patch_candidate_ids": normalized_ids,
        "selection": row,
        "selected_patch_set_counterfactual_preview": preview,
    }

def record_application_action_payload(
    actions_path: Path = DEFAULT_APPLICATION_ACTIONS_PATH,
    job_doc_id: str = "",
    job_url: str = "",
    job_company: str = "",
    job_title: str = "",
    application_status: str = "",
    source_view: str = "",
    note: str = "",
) -> Dict[str, Any]:
    ja = _job_app()

    row = {
        "action_timestamp": datetime.now(timezone.utc).isoformat(timespec="microseconds"),
        "job_doc_id": _clean_text(job_doc_id),
        "job_url": _clean_text(job_url),
        "job_company": _clean_text(job_company),
        "job_title": _clean_text(job_title),
        "application_status": _normalize_application_status(application_status),
        "source_view": _clean_text(source_view),
        "note": _clean_text(note),
    }

    _validate_application_identity(row)
    ja._append_csv_row(actions_path, APPLICATION_ACTION_HEADERS, row)

    return {
        "ok": True,
        "row": row,
        "actions_path": str(actions_path),
    }


def application_actions_payload(
    actions_path: Path = DEFAULT_APPLICATION_ACTIONS_PATH,
    application_status: str = "",
    company_contains: str = "",
    title_contains: str = "",
    limit: int = 100,
) -> Dict[str, Any]:
    ja = _job_app()
    rows = _load_latest_application_actions(actions_path)

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

    selected = rows[:limit]

    return {
        "filters": {
            "application_status": application_status,
            "company_contains": company_contains,
            "title_contains": title_contains,
            "limit": limit,
        },
        "rows": selected,
        "count": len(selected),
        "actions_path": str(actions_path),
    }


def applied_jobs_payload(
    actions_path: Path = DEFAULT_APPLICATION_ACTIONS_PATH,
    company_contains: str = "",
    title_contains: str = "",
    limit: int = 100,
) -> Dict[str, Any]:
    return application_actions_payload(
        actions_path=actions_path,
        application_status="APPLIED",
        company_contains=company_contains,
        title_contains=title_contains,
        limit=limit,
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