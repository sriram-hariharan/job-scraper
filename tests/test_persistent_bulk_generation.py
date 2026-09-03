from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from src.app import api, bulk_generation_service as bulk
from src.storage.bulk_generation import store


def test_schema_enforces_one_active_run_per_owner_and_ordered_unique_items():
    sql = store.bulk_generation_schema_sql_text()
    assert "idx_bulk_generation_runs_one_active_owner" in sql
    assert "WHERE status IN ('queued', 'running', 'stop_requested')" in sql
    assert "PRIMARY KEY (run_id, sequence)" in sql
    assert "UNIQUE (run_id, job_identity)" in sql
    assert "owner_user_id TEXT NOT NULL REFERENCES auth_users" in sql


def test_create_persists_browser_order_and_checks_pipeline_under_shared_lock():
    result = store.create_bulk_generation_run_postgres_payload(
        owner_user_id="owner-a",
        run_id="bulk-a",
        pipeline_run_id="pipeline-a",
        items=[
            {"job_identity": "job-z", "job_doc_id": "job-z", "selected_resume": "A.pdf"},
            {"job_identity": "job-a", "job_doc_id": "job-a", "selected_resume": "B.pdf"},
        ],
        config_json={"parse_retry_limit": 0},
        print_only=True,
    )
    sql = result["sql"]
    assert "pg_advisory_xact_lock(927461337)" in sql
    assert "existing_pipeline" in sql
    assert sql.index("'job-z'") < sql.index("'job-a'")
    assert "'parse_retry_limit': 0" not in sql  # JSON is compact and SQL-quoted.
    assert '"parse_retry_limit":0' in sql


def test_create_rejects_duplicate_candidates_before_database_call():
    with pytest.raises(ValueError, match="Duplicate"):
        store.create_bulk_generation_run_postgres_payload(
            owner_user_id="owner-a", run_id="bulk-a", pipeline_run_id="pipeline-a",
            items=[
                {"job_identity": "same", "selected_resume": "A.pdf"},
                {"job_identity": "same", "selected_resume": "A.pdf"},
            ], print_only=True,
        )


def test_candidate_validation_is_owner_run_scoped_and_preserves_order(monkeypatch, tmp_path):
    output = tmp_path / "planning"
    corpus = output / "current_run_job_corpus.jsonl"
    rows = [
        {"job_doc_id": "b", "queue_rank": "2", "winner_resume": "B.pdf", "runner_up_resume": "BB.pdf", "job_company": "B", "job_title": "Two"},
        {"job_doc_id": "a", "queue_rank": "1", "winner_resume": "A.pdf", "runner_up_resume": "AA.pdf", "job_company": "A", "job_title": "One"},
    ]
    calls = []
    monkeypatch.setattr(bulk.services, "resolve_user_pipeline_run_planning_paths", lambda **kwargs: (calls.append(kwargs) or (output, corpus)))
    monkeypatch.setattr(bulk.services, "_job_app", lambda: SimpleNamespace(_build_job_index=lambda _path: rows))
    _, _, normalized = bulk.validate_bulk_generation_candidates(
        owner_user_id="owner-a", pipeline_run_id="pipeline-a",
        candidates=[
            {"job_identity": "b", "job_doc_id": "b", "queue_rank": "2", "selected_resume": "B.pdf"},
            {"job_identity": "a", "job_doc_id": "a", "queue_rank": "1", "selected_resume": "AA.pdf"},
        ],
    )
    assert calls == [{"owner_user_id": "owner-a", "run_id": "pipeline-a"}]
    assert [row["job_identity"] for row in normalized] == ["b", "a"]


def test_candidate_validation_rejects_stale_resume(monkeypatch, tmp_path):
    monkeypatch.setattr(bulk.services, "resolve_user_pipeline_run_planning_paths", lambda **_: (tmp_path, tmp_path / "c"))
    monkeypatch.setattr(bulk.services, "_job_app", lambda: SimpleNamespace(_build_job_index=lambda _: [
        {"job_doc_id": "a", "queue_rank": "1", "winner_resume": "A.pdf", "runner_up_resume": "AA.pdf"}
    ]))
    with pytest.raises(bulk.BulkGenerationError, match="winner or runner-up"):
        bulk.validate_bulk_generation_candidates(
            owner_user_id="owner-a", pipeline_run_id="pipeline-a",
            candidates=[{"job_identity": "a", "job_doc_id": "a", "queue_rank": "1", "selected_resume": "X.pdf"}],
        )


def _install_worker_store(monkeypatch, *, stop_during_first=False):
    state = {
        "run": {
            "run_id": "bulk-a", "owner_user_id": "owner-a", "pipeline_run_id": "pipeline-a",
            "status": "queued", "stop_requested": False,
            "config_json": {
                "sequential": True, "generate_llm_tailoring": True,
                "refresh_llm_tailoring": False, "parse_retry_limit": 0,
                "requested_count": 3,
            },
        },
        "items": [
            {"sequence": 1, "job_identity": "one", "job_doc_id": "one", "queue_rank": "1", "selected_resume": "A.pdf", "status": "pending"},
            {"sequence": 2, "job_identity": "two", "job_doc_id": "two", "queue_rank": "2", "selected_resume": "B.pdf", "status": "pending"},
            {"sequence": 3, "job_identity": "three", "job_doc_id": "three", "queue_rank": "3", "selected_resume": "C.pdf", "status": "pending"},
        ],
        "events": [],
    }
    monkeypatch.setattr(bulk.services, "_process_start_identity", lambda _: "identity")
    monkeypatch.setattr(bulk.services, "resolve_user_pipeline_run_planning_paths", lambda **_: (Path("out"), Path("corpus")))

    def claim(**_):
        state["run"]["status"] = "running"
        return {"updated": True}

    def get(**_):
        return {"found": True, "run": dict(state["run"]), "items": [dict(x) for x in state["items"]]}

    def start(sequence, **_):
        assert not any(row["status"] == "running" for row in state["items"])
        item = state["items"][sequence - 1]
        item["status"] = "running"
        state["events"].append(("start", sequence))
        return {"started": True}

    def finish(sequence, succeeded, **kwargs):
        item = state["items"][sequence - 1]
        assert item["status"] == "running"
        item["status"] = "succeeded" if succeeded else "needs_attention"
        state["events"].append(("persist", sequence, succeeded, kwargs["outcome"]))
        if stop_during_first and sequence == 1:
            state["run"].update(status="stop_requested", stop_requested=True)
        return {"finished": True}

    def terminal(status, **_):
        state["run"]["status"] = status
        state["events"].append(("terminal", status))
        return {"finished": True}

    monkeypatch.setattr(store, "update_bulk_generation_worker_postgres_payload", claim)
    monkeypatch.setattr(store, "get_bulk_generation_run_postgres_payload", get)
    monkeypatch.setattr(store, "start_bulk_generation_item_postgres_payload", start)
    monkeypatch.setattr(store, "finish_bulk_generation_item_postgres_payload", finish)
    monkeypatch.setattr(store, "finish_bulk_generation_run_postgres_payload", terminal)
    return state


def test_worker_is_sequential_persists_before_next_and_continues_after_failure(monkeypatch):
    state = _install_worker_store(monkeypatch)
    active = 0
    maximum = 0
    calls = []

    def regenerate(**kwargs):
        nonlocal active, maximum
        sequence = int(kwargs["queue_rank"])
        if sequence > 1:
            assert state["events"][-2][0] == "persist"
        assert kwargs["parse_retry_limit"] == 0
        assert kwargs["refresh_llm_tailoring"] is False
        active += 1
        maximum = max(maximum, active)
        calls.append(sequence)
        active -= 1
        if sequence == 2:
            raise RuntimeError("bounded test failure")
        return {"ok": True, "llm_tailoring_status": "generated", "tailoring_workspace_state": "ready"}

    assert bulk.run_bulk_generation_worker(owner_user_id="owner-a", run_id="bulk-a", regenerate=regenerate) == 0
    assert calls == [1, 2, 3]
    assert maximum == 1
    assert [event[:2] for event in state["events"]] == [
        ("start", 1), ("persist", 1), ("start", 2), ("persist", 2),
        ("start", 3), ("persist", 3), ("terminal", "completed"),
    ]


def test_stop_after_current_finishes_current_and_starts_no_more(monkeypatch):
    state = _install_worker_store(monkeypatch, stop_during_first=True)
    assert bulk.run_bulk_generation_worker(
        owner_user_id="owner-a", run_id="bulk-a",
        regenerate=lambda **_: {"ok": True, "llm_tailoring_status": "generated", "tailoring_workspace_state": "ready"},
    ) == 0
    assert [event[:2] for event in state["events"]] == [
        ("start", 1), ("persist", 1), ("terminal", "stopped"),
    ]


def test_worker_launch_failure_marks_run_terminal(monkeypatch):
    monkeypatch.setattr(bulk, "validate_bulk_generation_candidates", lambda **_: (Path("out"), Path("corpus"), [{"job_identity": "a", "selected_resume": "A.pdf"}]))
    monkeypatch.setattr(bulk, "get_user_pipeline_active_run_postgres_payload", lambda **_: {"found": False})
    monkeypatch.setattr(store, "create_bulk_generation_run_postgres_payload", lambda **_: {"created": True})
    terminal = []
    monkeypatch.setattr(store, "finish_bulk_generation_run_postgres_payload", lambda **kwargs: terminal.append(kwargs) or {"finished": True})
    with pytest.raises(bulk.BulkGenerationError) as exc:
        bulk.start_bulk_generation(
            owner_user_id="owner-a", pipeline_run_id="pipeline-a",
            candidates=[{}], requested_count=1,
            launcher=lambda *_: (_ for _ in ()).throw(OSError("launch failed")),
        )
    assert exc.value.category == "worker_launch_failed"
    assert terminal[0]["status"] == "failed"


def test_start_fails_before_candidate_loading_when_live_pipeline_is_active(monkeypatch):
    monkeypatch.setattr(bulk, "get_user_pipeline_active_run_postgres_payload", lambda **_: {
        "found": True, "active_run": {"run_id": "pipeline-live", "status": "running"},
    })
    monkeypatch.setattr(bulk, "validate_bulk_generation_candidates", lambda **_: pytest.fail("candidate artifacts must not load"))
    with pytest.raises(bulk.BulkGenerationError) as exc:
        bulk.start_bulk_generation(
            owner_user_id="owner-a", pipeline_run_id="pipeline-a", candidates=[{}], requested_count=1
        )
    assert exc.value.category == "live_pipeline_in_progress"


def test_duplicate_start_is_rejected_without_second_worker(monkeypatch):
    monkeypatch.setattr(bulk, "get_user_pipeline_active_run_postgres_payload", lambda **_: {"found": False})
    monkeypatch.setattr(bulk, "validate_bulk_generation_candidates", lambda **_: (
        Path("out"), Path("corpus"), [{"job_identity": "a", "selected_resume": "A.pdf"}]
    ))
    monkeypatch.setattr(store, "create_bulk_generation_run_postgres_payload", lambda **_: {
        "created": False, "reason": "bulk_generation_in_progress",
        "existing_run": {"run_id": "bulk-existing", "status": "running"},
    })
    launched = []
    with pytest.raises(bulk.BulkGenerationError) as exc:
        bulk.start_bulk_generation(
            owner_user_id="owner-a", pipeline_run_id="pipeline-a", candidates=[{}], requested_count=1,
            launcher=lambda *args: launched.append(args),
        )
    assert exc.value.category == "bulk_generation_in_progress"
    assert launched == []


def test_dead_worker_reconciles_to_bounded_terminal_failure(monkeypatch):
    payloads = iter([
        {"found": True, "run": {"run_id": "bulk-a", "status": "running", "worker_pid": "123", "worker_identity": "expected"}, "items": []},
        {"found": True, "run": {"run_id": "bulk-a", "status": "failed", "error_category": "worker_unavailable"}, "items": []},
    ])
    monkeypatch.setattr(store, "get_bulk_generation_run_postgres_payload", lambda **_: next(payloads))
    monkeypatch.setattr(bulk.services, "_process_liveness", lambda *_: "dead")
    terminal = []
    monkeypatch.setattr(store, "finish_bulk_generation_run_postgres_payload", lambda **kwargs: terminal.append(kwargs) or {"finished": True})
    status = bulk.get_bulk_generation_status(owner_user_id="owner-a")
    assert status["status"] == "failed"
    assert status["active"] is False
    assert terminal[0]["error_category"] == "worker_unavailable"


def test_cross_owner_run_read_returns_not_found(monkeypatch):
    monkeypatch.setattr(store, "get_bulk_generation_run_postgres_payload", lambda **kwargs: {
        "found": False, "run": {}, "items": [], "queried_owner": kwargs["owner_user_id"],
    })
    with pytest.raises(bulk.BulkGenerationError) as exc:
        bulk.get_bulk_generation_status(owner_user_id="owner-b", run_id="bulk-owned-by-a")
    assert exc.value.status_code == 404


def test_stop_storage_is_idempotent_for_terminal_runs():
    result = store.request_bulk_generation_stop_postgres_payload(
        owner_user_id="owner-a", run_id="bulk-a", print_only=True
    )
    assert "CASE WHEN status IN ('queued','running')" in result["sql"]
    assert "ELSE status END" in result["sql"]


def test_live_pipeline_reservation_checks_bulk_under_the_same_advisory_lock():
    from src.storage.user_pipeline.store import reserve_user_pipeline_active_run_postgres_payload

    result = reserve_user_pipeline_active_run_postgres_payload(
        owner_user_id="owner-a", run_id="pipeline-a", print_only=True
    )
    sql = result["sql"]
    assert "pg_advisory_xact_lock(927461337)" in sql
    assert "existing_bulk AS" in sql
    assert "NOT EXISTS (SELECT 1 FROM existing_bulk)" in sql
    assert "THEN 'bulk_generation_in_progress'" in sql


@pytest.mark.parametrize("path", [
    "/pipeline/run", "/planning/regenerate-selected-resume", "/planning/save-workspace-draft",
    "/planning/start-scan", "/profile/resumes/upload", "/application-actions",
    "/ai/settings/test-connection", "/assistant/query", "/notifications/read-state",
    "/notifications/delete", "/notifications/delete-all",
    "/profile/pipeline-runs/run-a/rerun", "/planning/bulk-generation/start",
])
def test_active_bulk_guard_blocks_mutation_and_provider_routes(monkeypatch, path):
    def auth(request):
        request.state.auth_user = {"user_id": "owner-a"}
        return None
    monkeypatch.setattr(api, "auth_guard_response", auth)
    monkeypatch.setattr(api.bulk_generation_service, "active_bulk_generation_guard_state", lambda **_: {
        "run_id": "bulk-a", "status": "running", "active": True,
    })
    client = TestClient(api.app)
    response = client.post(path, json={}) if path != "/assistant/query" else client.get(path)
    assert response.status_code == 409
    assert response.json() == {
        "ok": False,
        "error_category": "bulk_generation_in_progress",
        "message": bulk.BULK_BLOCK_MESSAGE,
        "bulk_run_id": "bulk-a",
        "bulk_status": "running",
    }


def test_safe_reads_and_other_owner_are_not_blocked(monkeypatch):
    def auth(request):
        request.state.auth_user = {"user_id": request.headers.get("x-owner", "owner-a")}
        return None
    monkeypatch.setattr(api, "auth_guard_response", auth)
    monkeypatch.setattr(api.bulk_generation_service, "active_bulk_generation_guard_state", lambda owner_user_id: (
        {"run_id": "bulk-a", "status": "running"} if owner_user_id == "owner-a" else {}
    ))
    monkeypatch.setattr(api.services, "health_payload", lambda: {"ok": True})
    monkeypatch.setattr(api.services, "regenerate_selected_resume_tailoring_payload", lambda **_: {"ok": True})
    client = TestClient(api.app)
    assert client.get("/health", headers={"x-owner": "owner-a"}).status_code == 200
    other = client.post("/planning/regenerate-selected-resume", json={}, headers={"x-owner": "owner-b"})
    assert other.status_code != 409


def test_guard_fails_closed_when_bulk_state_cannot_be_read(monkeypatch):
    def auth(request):
        request.state.auth_user = {"user_id": "owner-a"}
        return None
    monkeypatch.setattr(api, "auth_guard_response", auth)
    monkeypatch.setattr(
        api.bulk_generation_service,
        "active_bulk_generation_guard_state",
        lambda **_: (_ for _ in ()).throw(
            bulk.BulkGenerationError("bulk_generation_state_unavailable", "unavailable", status_code=503)
        ),
    )
    response = TestClient(api.app).post("/application-actions", json={})
    assert response.status_code == 409
    assert response.json()["error_category"] == "bulk_generation_state_unavailable"


def test_pipeline_admission_race_maps_to_same_bounded_conflict(monkeypatch):
    def auth(request):
        request.state.auth_user = {"user_id": "owner-a"}
        return None
    monkeypatch.setattr(api, "auth_guard_response", auth)
    monkeypatch.setattr(api.bulk_generation_service, "active_bulk_generation_guard_state", lambda **_: {})
    monkeypatch.setattr(
        api.services,
        "run_live_pipeline_payload",
        lambda **_: (_ for _ in ()).throw(ValueError("bulk_generation_in_progress")),
    )
    response = TestClient(api.app).post("/pipeline/run", json={})
    assert response.status_code == 409
    assert response.json()["error_category"] == "bulk_generation_in_progress"
    assert response.json()["message"] == bulk.BULK_BLOCK_MESSAGE


def test_terminal_state_releases_guard(monkeypatch):
    monkeypatch.setattr(store, "get_bulk_generation_run_postgres_payload", lambda **_: {
        "found": True,
        "run": {"run_id": "bulk-a", "status": "completed", "total_count": 1, "completed_count": 1, "succeeded_count": 1},
        "items": [],
    })
    assert bulk.get_bulk_generation_status(owner_user_id="owner-a")["active"] is False


def test_shared_shell_owns_polling_progress_stop_and_accessible_guard():
    shell = Path("src/app/static/shell.js").read_text(encoding="utf-8")
    markup = Path("src/app/ui_shell.py").read_text(encoding="utf-8")
    planning = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    assert 'fetch("/planning/bulk-generation/status"' in shell
    assert "document.hidden ? 15000 : 3000" in shell
    assert "BULK_GENERATION_TERMINAL_STATUSES" in shell
    assert "bulkGenerationPollTimer" in shell
    assert "requestBulkGenerationStop" in shell
    assert "aria-describedby" in shell
    assert "event.stopImmediatePropagation()" in shell
    assert bulk.BULK_BLOCK_MESSAGE in shell
    # The visible shell pill was removed by product decision; the canonical
    # state, polling, stop API and guard above are all still asserted.
    assert 'id="bulkGenerationProgressBtn"' not in markup
    assert 'id="bulkGenerationPanel"' not in markup
    assert 'id="bulkGenerationShell"' not in markup
    assert 'id="bulkGenerationGuardDescription"' in markup
    assert 'postJson("/planning/bulk-generation/start"' in planning
    assert "for (let index" not in planning[planning.index("async function executeBulkGenerateSuggestions"):planning.index("function stopBulkGenerateSuggestionsAfterCurrent")]
    assert 'window.addEventListener("pagehide"' not in planning


def test_bulk_guard_exempts_its_own_controls_and_planning_owns_the_bulk_surface():
    """The active-Bulk guard must never block Bulk's own progress controls."""

    shell = Path("src/app/static/shell.js").read_text(encoding="utf-8")
    planning_tsx = Path(
        "frontend/executive-kpi/src/PlanningWorklist.tsx"
    ).read_text(encoding="utf-8")

    safe = shell[
        shell.index("function bulkGenerationControlIsSafe")
        : shell.index("function setBulkGenerationControlGuard")
    ]
    # The existing allowlist seam is what exempts Bulk's own controls.
    assert "control.closest(\"[data-bulk-safe='true']\")" in safe
    assert 'data-bulk-safe={running ? "true" : undefined}' in planning_tsx

    # Unsafe mutation controls keep the original blocked-action treatment.
    guard = shell[
        shell.index("function setBulkGenerationControlGuard")
        : shell.index("function applyBulkGenerationControlGuards")
    ]
    assert 'control.setAttribute("aria-disabled", "true")' in guard
    assert 'control.setAttribute("aria-describedby", "bulkGenerationGuardDescription")' in guard
    assert bulk.BULK_BLOCK_MESSAGE in shell

    # The shared shell no longer renders any visible Bulk surface anywhere;
    # Planning's transformed control is the only Bulk progress affordance.
    assert "renderBulkGenerationShell" not in shell
    assert "planningOwnsBulkSurface" not in shell


def test_global_bulk_pill_is_absent_while_canonical_state_is_preserved():
    """Part A: visual removal only — polling, guard and stop API remain."""

    markup = Path("src/app/ui_shell.py").read_text(encoding="utf-8")
    shell = Path("src/app/static/shell.js").read_text(encoding="utf-8")
    styles = Path("src/app/static/styles.css").read_text(encoding="utf-8")

    # The shared shell is rendered on every page, so absence here is absence
    # on Executive, Planning, Scheduler and every other app page.
    for removed in (
        'id="bulkGenerationShell"',
        'id="bulkGenerationProgressBtn"',
        'id="bulkGenerationPanel"',
        'id="bulkGenerationProgressLabel"',
        'id="bulkGenerationMinimizeBtn"',
    ):
        assert removed not in markup
    assert "renderBulkGenerationShell" not in shell
    assert ".bulk-generation-progress-btn" not in styles
    assert ".bulk-generation-panel" not in styles

    # Canonical state, polling and the guard must all survive the removal.
    assert 'fetch("/planning/bulk-generation/status"' in shell
    assert "bulkGenerationPollTimer" in shell
    assert "applyBulkGenerationControlGuards" in shell
    assert "bulkGenerationCanonicalState" in shell
    assert "requestBulkGenerationStop" in shell
    assert "ApplyLensBulkGeneration" in shell
    assert 'id="bulkGenerationGuardDescription"' in markup
    assert ".bulk-generation-guard-description" in styles
