from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List
import json
import os
import subprocess


DEFAULT_OUTPUT_DIR = Path("outputs/application_planning")
DEFAULT_CORPUS_PATH = Path("data/rag/job_corpus.jsonl")
DEFAULT_DECISIONS_PATH = DEFAULT_OUTPUT_DIR / "operator_decisions.csv"
DEFAULT_APPLICATION_ACTIONS_PATH = DEFAULT_OUTPUT_DIR / "application_actions.csv"
DEFAULT_PIPELINE_LOG_PATH = DEFAULT_OUTPUT_DIR / "live_pipeline_run.log"
DEFAULT_PIPELINE_STATUS_PATH = DEFAULT_OUTPUT_DIR / "live_pipeline_status.json"

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
    selected = _overlay_application_actions(selected)
    return {
        "request": request,
        "resolved_view": view,
        "rows": selected,
        "count": len(selected),
    }


def decisions_payload(
    decisions_path: Path = DEFAULT_DECISIONS_PATH,
    **filters: Any,
) -> Dict[str, Any]:
    ja = _job_app()
    rows = ja._load_csv_rows(decisions_path)
    args = _make_args(**filters)
    selected = ja._select_decision_rows(rows, args)
    selected = _overlay_application_actions(selected)
    return {
        "filters": filters,
        "rows": selected,
        "count": len(selected),
        "decisions_path": str(decisions_path),
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