from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess
import sys
import uuid
from typing import Any, Callable, Dict, Iterable

from src.app import services
from src.storage.bulk_generation import store
from src.storage.user_pipeline.store import get_user_pipeline_active_run_postgres_payload


ACTIVE_STATUSES = frozenset(store.ACTIVE_STATUSES)
TERMINAL_STATUSES = frozenset(store.TERMINAL_STATUSES)
BULK_BLOCK_MESSAGE = "Bulk Generate must finish or be stopped before this action is available."
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


class BulkGenerationError(RuntimeError):
    def __init__(self, category: str, message: str, *, status_code: int = 409, run: Dict[str, Any] | None = None):
        super().__init__(message)
        self.category = str(category or "bulk_generation_error")[:80]
        self.message = str(message or "Bulk Generate could not be started.")[:500]
        self.status_code = int(status_code)
        self.run = dict(run or {})


def _clean(value: Any, maximum: int = 512) -> str:
    return str(value or "").strip()[:maximum]


def _parse_time(value: Any) -> datetime | None:
    raw = _clean(value)
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _public_status(run: Dict[str, Any], items: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    status = _clean(run.get("status"), 32)
    public_items = []
    for item in list(items or [])[:500]:
        public_items.append({
            "sequence": int(item.get("sequence") or 0),
            "job_identity": _clean(item.get("job_identity")),
            "job_label": _clean(item.get("job_label"), 240),
            "status": _clean(item.get("status"), 32),
            "outcome": _clean(item.get("outcome"), 64),
            "error_category": _clean(item.get("error_category"), 80),
            "error_message": _clean(item.get("error_message"), 500),
        })
    total = int(run.get("total_count") or 0)
    completed = int(run.get("completed_count") or 0)
    current_sequence = run.get("current_sequence")
    current_label = next(
        (item["job_label"] for item in public_items if item["sequence"] == current_sequence),
        "",
    )
    return {
        "ok": True,
        "active": status in ACTIVE_STATUSES,
        "terminal": status in TERMINAL_STATUSES,
        "run_id": _clean(run.get("run_id")),
        "pipeline_run_id": _clean(run.get("pipeline_run_id")),
        "status": status,
        "total": total,
        "completed": completed,
        "succeeded": int(run.get("succeeded_count") or 0),
        "needs_attention": int(run.get("needs_attention_count") or 0),
        "remaining": max(0, total - completed),
        "current_sequence": current_sequence,
        "current_job_identity": _clean(run.get("current_job_identity")),
        "current_job_label": current_label,
        "stop_requested": bool(run.get("stop_requested")),
        "error_category": _clean(run.get("error_category"), 80),
        "error_message": _clean(run.get("error_message"), 500),
        "started_at": _clean(run.get("started_at")),
        "updated_at": _clean(run.get("updated_at")),
        "finished_at": _clean(run.get("finished_at")),
        "items": public_items,
    }


def _reconcile_worker_death(owner_user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    run = dict(payload.get("run", {}) or {})
    status = _clean(run.get("status"), 32)
    if status not in ACTIVE_STATUSES:
        return payload
    pid = _clean(run.get("worker_pid"), 32)
    identity = _clean(run.get("worker_identity"), 80)
    should_fail = False
    if status == "queued" and not pid:
        started = _parse_time(run.get("started_at"))
        should_fail = bool(started and (datetime.now(timezone.utc) - started).total_seconds() > 60)
    elif pid:
        should_fail = services._process_liveness(pid, identity) in {"dead", "identity_mismatch", "malformed"}
    if not should_fail:
        return payload
    store.finish_bulk_generation_run_postgres_payload(
        owner_user_id=owner_user_id,
        run_id=_clean(run.get("run_id")),
        status="failed",
        error_category="worker_unavailable",
        error_message="The Bulk Generate worker stopped before the run completed.",
    )
    return store.get_bulk_generation_run_postgres_payload(
        owner_user_id=owner_user_id, run_id=_clean(run.get("run_id"))
    )


def get_bulk_generation_status(*, owner_user_id: str, run_id: str = "") -> Dict[str, Any]:
    owner = _clean(owner_user_id)
    if not owner:
        raise BulkGenerationError("authentication_required", "Authentication required.", status_code=401)
    try:
        payload = store.get_bulk_generation_run_postgres_payload(
            owner_user_id=owner, run_id=_clean(run_id), active_or_latest=not bool(_clean(run_id))
        )
        if payload.get("found"):
            payload = _reconcile_worker_death(owner, payload)
    except (Exception, SystemExit) as exc:
        raise BulkGenerationError(
            "bulk_generation_state_unavailable",
            "Bulk Generate state is temporarily unavailable.",
            status_code=503,
        ) from exc
    if not payload.get("found"):
        if run_id:
            raise BulkGenerationError("bulk_generation_not_found", "Bulk Generate run was not found.", status_code=404)
        return {"ok": True, "active": False, "terminal": False, "status": "none", "items": []}
    return _public_status(dict(payload.get("run", {}) or {}), payload.get("items", []))


# Item outcomes a re-run may legitimately target. "generated" is deliberately
# excluded by default only from the *eligible* count, not from the view: the
# operator still sees it and may select it explicitly.
RERUNNABLE_ITEM_OUTCOMES = ("no_safe_rewrites", "empty", "failed", "")


def _public_result_item(row: Dict[str, Any]) -> Dict[str, Any]:
    status = _clean(row.get("status"), 32)
    outcome = _clean(row.get("outcome"), 32)
    return {
        "run_id": _clean(row.get("run_id"), 64),
        "sequence": int(row.get("sequence") or 0),
        "job_identity": _clean(row.get("job_identity")),
        "job_doc_id": _clean(row.get("job_doc_id")),
        "queue_rank": _clean(row.get("queue_rank"), 64),
        "selected_resume": _clean(row.get("selected_resume"), 255),
        "job_label": _clean(row.get("job_label"), 255),
        "status": status,
        "outcome": outcome,
        "error_category": _clean(row.get("error_category"), 80),
        # Bounded exactly like every other operator-visible Bulk error string.
        "error_message": _clean(row.get("error_message"), 500),
        "started_at": _clean(row.get("started_at"), 64),
        "finished_at": _clean(row.get("finished_at"), 64),
        "attempt_count": int(row.get("attempt_count") or 1),
        "rerunnable": status != "running" and outcome in RERUNNABLE_ITEM_OUTCOMES,
    }


def get_bulk_generation_pipeline_results(
    *, owner_user_id: str, pipeline_run_id: str
) -> Dict[str, Any]:
    """Read-only latest-attempt-per-job history for one pipeline run.

    Owner scoped. Never mutates. Deliberately separate from
    ``get_bulk_generation_status`` so the canonical polling/guard payload keeps
    its narrow active-run semantics.
    """
    owner = _clean(owner_user_id)
    if not owner:
        raise BulkGenerationError("authentication_required", "Authentication required.", status_code=401)
    pipeline = _clean(pipeline_run_id, 128)
    if not pipeline:
        raise BulkGenerationError(
            "bulk_generation_pipeline_required",
            "A pipeline run is required to load Bulk Generate results.",
            status_code=400,
        )
    try:
        payload = store.get_bulk_generation_pipeline_results_postgres_payload(
            owner_user_id=owner, pipeline_run_id=pipeline
        )
    except (Exception, SystemExit) as exc:
        raise BulkGenerationError(
            "bulk_generation_state_unavailable",
            "Bulk Generate results are temporarily unavailable.",
            status_code=503,
        ) from exc

    items = [_public_result_item(dict(row or {})) for row in payload.get("items", []) or []]
    latest_run = dict(payload.get("latest_run", {}) or {})
    generated = len([row for row in items if row["outcome"] == "generated"])
    needs_attention = len(
        [row for row in items if row["status"] == "needs_attention" or row["outcome"] == "failed"]
    )
    return {
        "ok": True,
        "found": bool(payload.get("found")),
        "pipeline_run_id": pipeline,
        "run_count": int(payload.get("run_count") or 0),
        "latest_run_id": _clean(latest_run.get("run_id"), 64),
        "latest_status": _clean(latest_run.get("status"), 32),
        "latest_started_at": _clean(latest_run.get("started_at"), 64),
        "latest_finished_at": _clean(latest_run.get("finished_at"), 64),
        "processed_count": len(items),
        "generated_count": generated,
        "needs_attention_count": needs_attention,
        "rerunnable_count": len([row for row in items if row["rerunnable"]]),
        "items": items,
    }


def active_bulk_generation_guard_state(*, owner_user_id: str) -> Dict[str, Any]:
    status = get_bulk_generation_status(owner_user_id=owner_user_id)
    return status if status.get("active") else {}


def _candidate_identity(row: Dict[str, Any]) -> str:
    return _clean(row.get("job_doc_id") or row.get("job_url") or row.get("queue_rank"))


def validate_bulk_generation_candidates(
    *, owner_user_id: str, pipeline_run_id: str, candidates: Iterable[Dict[str, Any]]
) -> tuple[Path, Path, list[Dict[str, Any]]]:
    owner, pipeline_run = _clean(owner_user_id), _clean(pipeline_run_id)
    if not owner or not pipeline_run:
        raise BulkGenerationError("invalid_candidates", "Owner and pipeline run are required.", status_code=400)
    requested = [dict(item or {}) for item in candidates]
    if not 1 <= len(requested) <= 500:
        raise BulkGenerationError("invalid_candidates", "Bulk Generate requires between 1 and 500 items.", status_code=400)
    try:
        output_dir, job_corpus = services.resolve_user_pipeline_run_planning_paths(
            owner_user_id=owner, run_id=pipeline_run
        )
        planning_rows = services._job_app()._build_job_index(output_dir)
    except ValueError as exc:
        raise BulkGenerationError("invalid_pipeline_run", str(exc), status_code=400) from exc
    normalized: list[Dict[str, Any]] = []
    seen: set[str] = set()
    for requested_row in requested:
        job_doc_id = _clean(requested_row.get("job_doc_id"))
        queue_rank = _clean(requested_row.get("queue_rank"), 64)
        try:
            row = services._find_planning_row_for_regeneration(
                planning_rows, job_doc_id=job_doc_id, queue_rank=queue_rank
            )
        except ValueError as exc:
            raise BulkGenerationError("stale_candidate", str(exc), status_code=409) from exc
        actual_identity = _candidate_identity(row)
        submitted_identity = _clean(requested_row.get("job_identity") or job_doc_id or queue_rank)
        if not actual_identity or submitted_identity != actual_identity:
            raise BulkGenerationError("stale_candidate", "Bulk Generate candidate identity is stale.", status_code=409)
        actual_rank = _clean(row.get("queue_rank"), 64)
        if queue_rank and queue_rank != actual_rank:
            raise BulkGenerationError("stale_candidate", "Bulk Generate candidate queue rank is stale.", status_code=409)
        if actual_identity in seen:
            raise BulkGenerationError("duplicate_candidate", "Duplicate Bulk Generate candidate identity.", status_code=400)
        seen.add(actual_identity)
        try:
            selected = services._sanitize_resume_filename(requested_row.get("selected_resume"))
        except ValueError as exc:
            raise BulkGenerationError("stale_candidate", "Selected resume is invalid or stale.", status_code=409) from exc
        allowed = {
            value for value in (
                services._sanitize_optional_resume_filename(row.get("winner_resume")),
                services._sanitize_optional_resume_filename(row.get("runner_up_resume")),
            ) if value
        }
        if selected not in allowed:
            raise BulkGenerationError(
                "stale_candidate",
                "Selected resume must still match the current winner or runner-up.",
                status_code=409,
            )
        label = " · ".join(filter(None, [_clean(row.get("job_company"), 100), _clean(row.get("job_title"), 120)]))
        normalized.append({
            "job_identity": actual_identity,
            "job_doc_id": _clean(row.get("job_doc_id")),
            "queue_rank": actual_rank,
            "selected_resume": selected,
            "job_label": label or actual_identity,
        })
    return output_dir, job_corpus, normalized


def _launch_worker(owner_user_id: str, run_id: str) -> subprocess.Popen[Any]:
    command = [
        sys.executable, "-m", "src.app.bulk_generation_worker",
        "--owner-user-id", owner_user_id, "--run-id", run_id,
    ]
    child_env = services._pipeline_child_env()
    return subprocess.Popen(
        command,
        cwd=str(REPOSITORY_ROOT),
        env=child_env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True,
    )


def start_bulk_generation(
    *, owner_user_id: str, pipeline_run_id: str, candidates: Iterable[Dict[str, Any]],
    requested_count: int, review_filter: str = "", match_filter: str = "",
    preference_filter: str = "", launcher: Callable[[str, str], subprocess.Popen[Any]] = _launch_worker,
) -> Dict[str, Any]:
    owner = _clean(owner_user_id)
    try:
        pipeline = get_user_pipeline_active_run_postgres_payload(owner_user_id=owner)
    except (Exception, SystemExit) as exc:
        raise BulkGenerationError("bulk_generation_admission_unavailable", "Bulk Generate admission is temporarily unavailable.", status_code=503) from exc
    if pipeline.get("found"):
        raise BulkGenerationError("live_pipeline_in_progress", "Live Pipeline must finish before Bulk Generate can start.", run=pipeline.get("active_run"))
    _output_dir, _job_corpus, items = validate_bulk_generation_candidates(
        owner_user_id=owner, pipeline_run_id=pipeline_run_id, candidates=candidates
    )
    if int(requested_count) != len(items):
        raise BulkGenerationError("invalid_candidates", "Requested item count does not match candidate order.", status_code=400)
    run_id = f"bulk_{uuid.uuid4().hex}"
    config = {
        "requested_count": len(items),
        "review_filter": _clean(review_filter, 80),
        "match_filter": _clean(match_filter, 80),
        "preference_filter": _clean(preference_filter, 160),
        "generate_llm_tailoring": True,
        "refresh_llm_tailoring": False,
        "parse_retry_limit": 0,
        "sequential": True,
    }
    try:
        created = store.create_bulk_generation_run_postgres_payload(
            owner_user_id=owner, run_id=run_id, pipeline_run_id=pipeline_run_id,
            items=items, config_json=config,
        )
    except (Exception, SystemExit) as exc:
        raise BulkGenerationError("bulk_generation_admission_unavailable", "Bulk Generate admission is temporarily unavailable.", status_code=503) from exc
    if not created.get("created"):
        reason = _clean(created.get("reason"), 80) or "bulk_generation_in_progress"
        raise BulkGenerationError(reason, BULK_BLOCK_MESSAGE, run=created.get("existing_run"))
    try:
        launcher(owner, run_id)
    except Exception as exc:
        store.finish_bulk_generation_run_postgres_payload(
            owner_user_id=owner, run_id=run_id, status="failed",
            error_category="worker_launch_failed",
            error_message="Bulk Generate worker could not be launched.",
        )
        raise BulkGenerationError("worker_launch_failed", "Bulk Generate worker could not be launched.", status_code=503) from exc
    return {
        "ok": True,
        "active": True,
        "terminal": False,
        "run_id": run_id,
        "pipeline_run_id": _clean(pipeline_run_id),
        "status": "queued",
        "total": len(items),
        "completed": 0,
        "succeeded": 0,
        "needs_attention": 0,
        "remaining": len(items),
        "current_sequence": None,
        "current_job_identity": "",
        "stop_requested": False,
        "items": [],
    }


def request_bulk_generation_stop(*, owner_user_id: str, run_id: str) -> Dict[str, Any]:
    try:
        result = store.request_bulk_generation_stop_postgres_payload(
            owner_user_id=owner_user_id, run_id=run_id
        )
    except (Exception, SystemExit) as exc:
        raise BulkGenerationError("bulk_generation_state_unavailable", "Bulk Generate state is temporarily unavailable.", status_code=503) from exc
    if not result.get("found"):
        raise BulkGenerationError("bulk_generation_not_found", "Bulk Generate run was not found.", status_code=404)
    return get_bulk_generation_status(owner_user_id=owner_user_id, run_id=run_id)


def _classify_response(response: Dict[str, Any]) -> tuple[bool, str, str, str]:
    llm_status = _clean(response.get("llm_tailoring_status"), 32).lower()
    workspace = _clean(response.get("tailoring_workspace_state"), 32).lower()
    if response.get("ok") is True:
        # Authoritative workspace state takes precedence over the optional
        # LLM refinement pass for these two usable states: deterministic
        # tailoring (review/direction evidence, or app-ready replacements)
        # is produced independently of the separate --use-llm refinement
        # step, so a usable workspace must not be classified as a provider
        # failure merely because that optional refinement failed/was
        # unreadable. "empty" (no usable evidence at all) is unchanged below:
        # it still requires the LLM pass to not have failed, preserving the
        # existing rule that a genuine failure (no usable result produced)
        # stays a failure.
        if workspace in {"no_safe_rewrites", "review"}:
            return True, "no_safe_rewrites", "", ""
        if workspace == "ready":
            return True, "generated", "", ""
        if llm_status not in {"failed", "unreadable"} and workspace == "empty":
            return True, "empty", "", ""
    category = "provider_failure" if llm_status in {"failed", "unreadable"} else "unusable_workspace"
    return False, "failed", category, "A usable tailoring workspace was not produced."


def run_bulk_generation_worker(
    *, owner_user_id: str, run_id: str,
    regenerate: Callable[..., Dict[str, Any]] = services.regenerate_selected_resume_tailoring_payload,
) -> int:
    owner, safe_run = _clean(owner_user_id), _clean(run_id)
    identity = services._process_start_identity(os.getpid())
    claimed = store.update_bulk_generation_worker_postgres_payload(
        owner_user_id=owner, run_id=safe_run, worker_pid=os.getpid(), worker_identity=identity
    )
    if not claimed.get("updated"):
        return 2
    try:
        payload = store.get_bulk_generation_run_postgres_payload(owner_user_id=owner, run_id=safe_run)
        run, items = dict(payload.get("run", {}) or {}), list(payload.get("items", []) or [])
        config = dict(run.get("config_json", {}) or {})
        if not (
            config.get("sequential") is True
            and config.get("generate_llm_tailoring") is True
            and config.get("refresh_llm_tailoring") is False
            and config.get("parse_retry_limit") == 0
            and int(config.get("requested_count") or 0) == len(items)
        ):
            raise RuntimeError("Persisted Bulk Generate configuration is invalid.")
        output_dir, job_corpus = services.resolve_user_pipeline_run_planning_paths(
            owner_user_id=owner, run_id=_clean(run.get("pipeline_run_id"))
        )
        for item in items:
            current = store.get_bulk_generation_run_postgres_payload(owner_user_id=owner, run_id=safe_run)
            current_run = dict(current.get("run", {}) or {})
            if bool(current_run.get("stop_requested")) or _clean(current_run.get("status")) == "stop_requested":
                store.finish_bulk_generation_run_postgres_payload(owner_user_id=owner, run_id=safe_run, status="stopped")
                return 0
            sequence = int(item.get("sequence") or 0)
            if not store.start_bulk_generation_item_postgres_payload(
                owner_user_id=owner, run_id=safe_run, sequence=sequence
            ).get("started"):
                raise RuntimeError("Bulk Generate item could not be claimed sequentially.")
            succeeded, outcome, category, message = False, "failed", "generation_failed", "Generation failed for this item."
            try:
                response = regenerate(
                    output_dir=output_dir,
                    job_corpus=job_corpus,
                    job_doc_id=_clean(item.get("job_doc_id")),
                    queue_rank=_clean(item.get("queue_rank"), 64),
                    selected_resume=_clean(item.get("selected_resume")),
                    generate_llm_tailoring=True,
                    refresh_llm_tailoring=False,
                    parse_retry_limit=0,
                    owner_user_id=owner,
                )
                succeeded, outcome, category, message = _classify_response(dict(response or {}))
            except services.SelectedResumeRegenerationError:
                category, message = "regeneration_failed", "Could not regenerate the selected resume."
            except ValueError as exc:
                category, message = "stale_candidate", _clean(exc, 500)
            except Exception:
                category, message = "provider_or_generation_failed", "Generation failed for this item."
            store.finish_bulk_generation_item_postgres_payload(
                owner_user_id=owner, run_id=safe_run, sequence=sequence,
                succeeded=succeeded, outcome=outcome,
                error_category=category, error_message=message,
            )
        latest = store.get_bulk_generation_run_postgres_payload(owner_user_id=owner, run_id=safe_run)
        terminal = "stopped" if bool(dict(latest.get("run", {}) or {}).get("stop_requested")) else "completed"
        store.finish_bulk_generation_run_postgres_payload(owner_user_id=owner, run_id=safe_run, status=terminal)
        return 0
    except Exception:
        store.finish_bulk_generation_run_postgres_payload(
            owner_user_id=owner, run_id=safe_run, status="failed",
            error_category="worker_failed", error_message="Bulk Generate worker stopped unexpectedly.",
        )
        return 1
