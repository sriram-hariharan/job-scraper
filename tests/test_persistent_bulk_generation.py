from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from src.app import api, bulk_generation_service as bulk
from src.storage.bulk_generation import store


TAILORING_ALIAS_VALUES = {
    "TAILORING_EXTRACTION_PROVIDER": "sentinel-extraction-provider",
    "TAILORING_EXTRACTION_MODEL": "sentinel-extraction-model",
    "TAILORING_REWRITE_PROVIDER": "sentinel-rewrite-provider",
    "TAILORING_REWRITE_MODEL": "sentinel-rewrite-model",
    "TAILORING_JUDGE_PROVIDER": "sentinel-judge-provider",
    "TAILORING_JUDGE_MODEL": "sentinel-judge-model",
}


def test_pipeline_child_env_forwards_only_exact_tailoring_model_aliases():
    lower_precedence_values = {
        "LLM_TAILOR_PROVIDER": "lower-extraction-provider",
        "LLM_TAILOR_MODEL": "lower-extraction-model",
        "PATCH_REFINEMENT_WRITER_PROVIDER": "lower-writer-provider",
        "PATCH_REFINEMENT_WRITER_MODEL": "lower-writer-model",
        "PATCH_REFINEMENT_JUDGE_PROVIDER": "lower-judge-provider",
        "PATCH_REFINEMENT_JUDGE_MODEL": "lower-judge-model",
    }
    child_env = bulk.services._pipeline_child_env(
        base_env={
            **TAILORING_ALIAS_VALUES,
            **lower_precedence_values,
            "TAILORING_PHRASE_MODEL": "blocked-unrelated-tailoring-model",
            "UNKNOWN_CONFIGURATION": "blocked-unknown-value",
            "PATH": "/usr/bin",
        }
    )

    assert {
        key: child_env.get(key) for key in TAILORING_ALIAS_VALUES
    } == TAILORING_ALIAS_VALUES
    assert {
        key: child_env.get(key) for key in lower_precedence_values
    } == lower_precedence_values
    assert "TAILORING_" not in bulk.services._PIPELINE_CHILD_ENV_PREFIXES
    assert "TAILORING_PHRASE_MODEL" not in child_env
    assert "UNKNOWN_CONFIGURATION" not in child_env


def test_bulk_worker_and_regeneration_child_preserve_tailoring_aliases(monkeypatch):
    for key, value in TAILORING_ALIAS_VALUES.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv(
        "TAILORING_PHRASE_MODEL",
        "blocked-unrelated-tailoring-model",
    )
    captured = {}
    process = SimpleNamespace(pid=4242)

    def fake_popen(command, **kwargs):
        captured["command"] = list(command)
        captured["env"] = dict(kwargs.get("env") or {})
        return process

    monkeypatch.setattr(bulk.subprocess, "Popen", fake_popen)

    assert bulk._launch_worker("owner-a", "bulk-a") is process
    worker_env = captured["env"]
    assert {
        key: worker_env.get(key) for key in TAILORING_ALIAS_VALUES
    } == TAILORING_ALIAS_VALUES
    assert "TAILORING_PHRASE_MODEL" not in worker_env

    # The worker is the parent of selected-resume regeneration. That second hop
    # copies the worker environment and adds only owner-scoped execution flags.
    monkeypatch.setattr(bulk.services.os, "environ", worker_env)
    regeneration_env = bulk.services._targeted_regeneration_child_env("owner-a")

    assert {
        key: regeneration_env.get(key) for key in TAILORING_ALIAS_VALUES
    } == TAILORING_ALIAS_VALUES
    assert "TAILORING_PHRASE_MODEL" not in regeneration_env
    assert regeneration_env["JOB_STACK_OWNER_USER_ID"] == "owner-a"


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


# ---------------------------------------------------------------------------
# Bulk item classification: authoritative workspace state takes precedence
# over the optional LLM refinement pass's status. A usable deterministic
# result (ready or no_safe_rewrites/review) must not be recorded as a
# provider_failure merely because the separate --use-llm refinement pass
# failed/was unreadable. A genuinely unusable result (no workspace evidence
# at all) remains a failure.
# ---------------------------------------------------------------------------


def test_classify_response_llm_failed_usable_no_safe_rewrites_is_not_provider_failure():
    # Mirrors a real Bulk-generated response shape (see forensic analysis):
    # the deterministic artifact produced review/direction evidence
    # independent of the failed optional LLM refinement.
    response = {
        "ok": True,
        "llm_tailoring_status": "failed",
        "llm_error_type": "llm_parse_failed",
        "tailoring_workspace_state": "no_safe_rewrites",
        "tailoring_actionable_replacement_count": 0,
        "tailoring_review_replacement_count": 2,
    }
    succeeded, outcome, category, message = bulk._classify_response(response)
    assert succeeded is True
    assert outcome == "no_safe_rewrites"
    assert category == ""
    assert message == ""


def test_classify_response_llm_unreadable_usable_no_safe_rewrites_is_not_provider_failure():
    response = {
        "ok": True,
        "llm_tailoring_status": "unreadable",
        "llm_error_type": "unreadable_json",
        "tailoring_workspace_state": "no_safe_rewrites",
    }
    succeeded, outcome, category, message = bulk._classify_response(response)
    assert succeeded is True
    assert outcome == "no_safe_rewrites"
    assert category == ""


def test_classify_response_legacy_review_with_failed_llm_is_not_provider_failure():
    # Legacy compatibility preserved exactly as after the Review-retirement
    # task: "review" still folds into the no_safe_rewrites outcome bucket.
    response = {
        "ok": True,
        "llm_tailoring_status": "failed",
        "tailoring_workspace_state": "review",
    }
    succeeded, outcome, category, message = bulk._classify_response(response)
    assert succeeded is True
    assert outcome == "no_safe_rewrites"


def test_classify_response_llm_failed_usable_ready_is_not_provider_failure():
    response = {
        "ok": True,
        "llm_tailoring_status": "failed",
        "llm_error_type": "llm_parse_failed",
        "tailoring_workspace_state": "ready",
        "tailoring_actionable_replacement_count": 1,
    }
    succeeded, outcome, category, message = bulk._classify_response(response)
    assert succeeded is True
    assert outcome == "generated"
    assert category == ""


def test_classify_response_llm_failed_no_usable_workspace_remains_provider_failure():
    # Genuine failure: no usable deterministic evidence survived either.
    response = {
        "ok": True,
        "llm_tailoring_status": "failed",
        "llm_error_type": "llm_parse_failed",
        "tailoring_workspace_state": "empty",
    }
    succeeded, outcome, category, message = bulk._classify_response(response)
    assert succeeded is False
    assert outcome == "failed"
    assert category == "provider_failure"
    assert message == "A usable tailoring workspace was not produced."


def test_classify_response_llm_failed_unavailable_workspace_remains_provider_failure():
    response = {
        "ok": True,
        "llm_tailoring_status": "unreadable",
        "tailoring_workspace_state": "unavailable",
    }
    succeeded, outcome, category, message = bulk._classify_response(response)
    assert succeeded is False
    assert category == "provider_failure"


def test_classify_response_regeneration_call_itself_failed_remains_failure():
    # ok is False: the regenerate() call itself did not complete usably
    # (e.g. subprocess failure before any output existed). Must not be
    # reclassified as success regardless of any stray workspace field.
    response = {
        "ok": False,
        "llm_tailoring_status": "failed",
        "tailoring_workspace_state": "no_safe_rewrites",
    }
    succeeded, outcome, category, message = bulk._classify_response(response)
    assert succeeded is False
    assert category == "provider_failure"


def test_classify_response_empty_workspace_with_generated_llm_is_unchanged_success():
    # Pre-existing behavior (not touched by this task): empty workspace with
    # a successful LLM pass is still a non-fatal "empty" outcome.
    response = {
        "ok": True,
        "llm_tailoring_status": "generated",
        "tailoring_workspace_state": "empty",
    }
    succeeded, outcome, category, message = bulk._classify_response(response)
    assert succeeded is True
    assert outcome == "empty"


def test_worker_records_llm_failed_no_safe_rewrites_item_as_succeeded_not_needs_attention(
    monkeypatch,
):
    """Integration proof (Test A/D end to end): the real worker, driven by a
    response shape mirroring the six live rows found during forensic
    analysis (grounding-contract llm failure + deterministic no_safe_rewrites
    evidence), persists the item as succeeded - not needs_attention/failed -
    and the outcome/category recorded is exactly the no_safe_rewrites lane,
    with no rejected LLM content promoted into the response.
    """
    state = _install_worker_store(monkeypatch)

    def regenerate(**kwargs):
        sequence = int(kwargs["queue_rank"])
        if sequence == 2:
            # The proven grounding-contract rejection shape: the LLM
            # responded, but the safety validator rejected the proposed
            # rewrite direction as unsupported by resume evidence. The
            # deterministic artifact's review evidence is untouched by this.
            return {
                "ok": True,
                "llm_tailoring_status": "failed",
                "llm_error_type": "llm_parse_failed",
                "tailoring_workspace_state": "no_safe_rewrites",
                "tailoring_actionable_replacement_count": 0,
                "tailoring_review_replacement_count": 1,
            }
        return {"ok": True, "llm_tailoring_status": "generated", "tailoring_workspace_state": "ready"}

    assert bulk.run_bulk_generation_worker(
        owner_user_id="owner-a", run_id="bulk-a", regenerate=regenerate
    ) == 0

    persisted = {event[1]: event for event in state["events"] if event[0] == "persist"}
    # succeeded=True, outcome="no_safe_rewrites" for the previously-misclassified item.
    assert persisted[2][2] is True
    assert persisted[2][3] == "no_safe_rewrites"
    assert state["items"][1]["status"] == "succeeded"
    assert [event[:2] for event in state["events"]] == [
        ("start", 1), ("persist", 1), ("start", 2), ("persist", 2),
        ("start", 3), ("persist", 3), ("terminal", "completed"),
    ]


def test_worker_sequential_and_stop_after_current_semantics_still_hold(monkeypatch):
    # Step E: reruns the two existing pinned sequential/stop-after-current
    # tests inline to confirm this task did not touch worker execution order.
    state = _install_worker_store(monkeypatch, stop_during_first=True)
    assert bulk.run_bulk_generation_worker(
        owner_user_id="owner-a", run_id="bulk-a",
        regenerate=lambda **_: {"ok": True, "llm_tailoring_status": "failed", "tailoring_workspace_state": "no_safe_rewrites"},
    ) == 0
    assert [event[:2] for event in state["events"]] == [
        ("start", 1), ("persist", 1), ("terminal", "stopped"),
    ]
    # Even the stopped-after-current item, now llm-failed + no_safe_rewrites,
    # is recorded as succeeded (not needs_attention) - stop semantics and
    # classification are independent, unchanged concerns.
    assert state["items"][0]["status"] == "succeeded"


# --- Bulk results + re-run center: owner-scoped read-only history -------------


def _result_row(
    job_identity,
    *,
    run_id="bulk-1",
    sequence=1,
    outcome="no_safe_rewrites",
    status="succeeded",
    selected_resume="Resume_A.pdf",
    finished_at="2026-09-07T21:54:09+00:00",
    attempt_count=1,
    **extra,
):
    row = {
        "run_id": run_id,
        "sequence": sequence,
        "job_identity": job_identity,
        "job_doc_id": f"doc-{job_identity}",
        "queue_rank": str(sequence),
        "selected_resume": selected_resume,
        "job_label": f"acme · {job_identity}",
        "status": status,
        "outcome": outcome,
        "error_category": "",
        "error_message": "",
        "started_at": "2026-09-07T21:28:16+00:00",
        "finished_at": finished_at,
        "attempt_count": attempt_count,
        "run_status": "completed",
    }
    row.update(extra)
    return row


def _install_results_store(monkeypatch, items, *, found=True, latest_run=None, run_count=1):
    seen = {}

    def fake(**kwargs):
        seen.update(kwargs)
        return {
            "ok": True,
            "found": found,
            "pipeline_run_id": kwargs["pipeline_run_id"],
            "run_count": run_count,
            "latest_run": latest_run
            or {
                "run_id": "bulk-2",
                "status": "completed",
                "started_at": "2026-09-08T01:00:00+00:00",
                "finished_at": "2026-09-08T01:20:00+00:00",
            },
            "items": items,
        }

    monkeypatch.setattr(store, "get_bulk_generation_pipeline_results_postgres_payload", fake)
    return seen


def test_results_query_is_owner_and_pipeline_scoped():
    result = store.get_bulk_generation_pipeline_results_postgres_payload(
        owner_user_id="owner-a", pipeline_run_id="pipeline-a", print_only=True
    )
    sql = result["sql"]
    assert "bulk_generation_runs" in sql and "bulk_generation_items" in sql
    assert "owner_user_id = 'owner-a'" in sql
    assert "pipeline_run_id = 'pipeline-a'" in sql
    # Read-only: the query itself carries no write verbs. Generated without the
    # shared schema prefix so the assertion covers the statement, not the DDL.
    query_only = store.get_bulk_generation_pipeline_results_postgres_payload(
        owner_user_id="owner-a",
        pipeline_run_id="pipeline-a",
        print_only=True,
        ensure_schema=False,
    )["sql"]
    for verb in ("INSERT", "UPDATE ", "DELETE", "CREATE TABLE", "DROP "):
        assert verb not in query_only.upper()
    assert query_only.upper().lstrip().startswith("WITH")


def test_results_latest_attempt_ranking_is_deterministic():
    sql = store.get_bulk_generation_pipeline_results_postgres_payload(
        owner_user_id="owner-a", pipeline_run_id="pipeline-a", print_only=True
    )["sql"]
    assert "PARTITION BY a.job_identity" in sql
    # Fully tie-broken so "latest attempt" can never depend on row order.
    for tiebreak in (
        "a.finished_at DESC NULLS LAST",
        "a.started_at DESC NULLS LAST",
        "a.run_started_at DESC NULLS LAST",
        "a.run_id DESC",
        "a.sequence DESC",
    ):
        assert tiebreak in sql
    assert "attempt_rank = 1" in sql


def test_results_service_is_owner_scoped_and_passes_owner_through(monkeypatch):
    seen = _install_results_store(monkeypatch, [_result_row("job-1")])
    payload = bulk.get_bulk_generation_pipeline_results(
        owner_user_id="owner-a", pipeline_run_id="pipeline-a"
    )
    assert seen["owner_user_id"] == "owner-a"
    assert seen["pipeline_run_id"] == "pipeline-a"
    assert payload["pipeline_run_id"] == "pipeline-a"


def test_results_require_authentication_and_pipeline(monkeypatch):
    with pytest.raises(bulk.BulkGenerationError) as missing_owner:
        bulk.get_bulk_generation_pipeline_results(owner_user_id="", pipeline_run_id="pipeline-a")
    assert missing_owner.value.status_code == 401

    with pytest.raises(bulk.BulkGenerationError) as missing_pipeline:
        bulk.get_bulk_generation_pipeline_results(owner_user_id="owner-a", pipeline_run_id="")
    assert missing_pipeline.value.status_code == 400


def test_results_pipeline_a_cannot_leak_pipeline_b(monkeypatch):
    seen = _install_results_store(monkeypatch, [], found=False, run_count=0)
    payload = bulk.get_bulk_generation_pipeline_results(
        owner_user_id="owner-a", pipeline_run_id="pipeline-b"
    )
    assert seen["pipeline_run_id"] == "pipeline-b"
    assert payload["found"] is False
    assert payload["items"] == []
    assert payload["processed_count"] == 0


def test_results_keep_full_pipeline_set_after_subset_rerun(monkeypatch):
    # 64-job initial run, then a 5-job subset re-run: the view must still carry
    # all 64 jobs, with only the re-run five showing the newer attempt.
    initial = [
        _result_row(f"job-{index}", run_id="bulk-1", sequence=index)
        for index in range(1, 65)
    ]
    rerun_identities = {"job-1", "job-2", "job-3", "job-4", "job-5"}
    latest = [
        _result_row(
            row["job_identity"],
            run_id="bulk-2",
            sequence=row["sequence"],
            outcome="generated",
            finished_at="2026-09-08T01:19:00+00:00",
            attempt_count=2,
        )
        if row["job_identity"] in rerun_identities
        else row
        for row in initial
    ]
    _install_results_store(monkeypatch, latest, run_count=2)

    payload = bulk.get_bulk_generation_pipeline_results(
        owner_user_id="owner-a", pipeline_run_id="pipeline-a"
    )
    assert payload["processed_count"] == 64
    assert payload["generated_count"] == 5

    by_identity = {row["job_identity"]: row for row in payload["items"]}
    # Re-run jobs show the newer attempt...
    assert by_identity["job-1"]["run_id"] == "bulk-2"
    assert by_identity["job-1"]["outcome"] == "generated"
    assert by_identity["job-1"]["attempt_count"] == 2
    # ...and the other 59 are not forgotten.
    assert by_identity["job-64"]["run_id"] == "bulk-1"
    assert by_identity["job-64"]["outcome"] == "no_safe_rewrites"


def test_results_expose_selected_resume_and_finished_at(monkeypatch):
    _install_results_store(
        monkeypatch,
        [_result_row("job-1", selected_resume="Resume_B.pdf", finished_at="2026-09-07T23:08:00+00:00")],
    )
    row = bulk.get_bulk_generation_pipeline_results(
        owner_user_id="owner-a", pipeline_run_id="pipeline-a"
    )["items"][0]
    assert row["selected_resume"] == "Resume_B.pdf"
    assert row["finished_at"] == "2026-09-07T23:08:00+00:00"
    assert row["job_doc_id"] == "doc-job-1"
    assert row["queue_rank"] == "1"


def test_results_bound_failed_item_error_messages(monkeypatch):
    _install_results_store(
        monkeypatch,
        [
            _result_row(
                "job-1",
                status="needs_attention",
                outcome="failed",
                error_category="provider_failure",
                error_message="x" * 4000,
            )
        ],
    )
    row = bulk.get_bulk_generation_pipeline_results(
        owner_user_id="owner-a", pipeline_run_id="pipeline-a"
    )["items"][0]
    assert len(row["error_message"]) == 500
    assert row["error_category"] == "provider_failure"


def test_results_outcome_vocabulary_is_not_collapsed(monkeypatch):
    _install_results_store(
        monkeypatch,
        [
            _result_row("job-1", outcome="generated"),
            _result_row("job-2", outcome="no_safe_rewrites"),
            _result_row("job-3", outcome="empty"),
            _result_row("job-4", status="needs_attention", outcome="failed"),
        ],
    )
    payload = bulk.get_bulk_generation_pipeline_results(
        owner_user_id="owner-a", pipeline_run_id="pipeline-a"
    )
    outcomes = {row["job_identity"]: row["outcome"] for row in payload["items"]}
    # no_safe_rewrites must never be reported as generated.
    assert outcomes == {
        "job-1": "generated",
        "job-2": "no_safe_rewrites",
        "job-3": "empty",
        "job-4": "failed",
    }
    assert payload["generated_count"] == 1
    assert payload["needs_attention_count"] == 1
    rerunnable = {row["job_identity"]: row["rerunnable"] for row in payload["items"]}
    assert rerunnable == {"job-1": False, "job-2": True, "job-3": True, "job-4": True}
    assert payload["rerunnable_count"] == 3


def test_results_endpoint_is_owner_scoped_and_read_only(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    monkeypatch.setattr(api, "_auth_owner_user_id", lambda request: "owner-a")
    seen = _install_results_store(monkeypatch, [_result_row("job-1")])

    response = TestClient(api.app).get(
        "/planning/bulk-generation/results", params={"pipeline_run_id": "pipeline-a"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["pipeline_run_id"] == "pipeline-a"
    assert seen["owner_user_id"] == "owner-a"
    assert body["items"][0]["job_identity"] == "job-1"


def test_results_endpoint_is_a_safe_get_for_the_active_bulk_guard():
    assert "/planning/bulk-generation/results" in api._BULK_SAFE_GET_PATHS
    assert "/planning/bulk-generation/status" in api._BULK_SAFE_GET_PATHS


def test_results_do_not_alter_existing_status_payload(monkeypatch):
    monkeypatch.setattr(store, "get_bulk_generation_run_postgres_payload", lambda **kwargs: {
        "found": False, "run": {}, "items": [],
    })
    status = bulk.get_bulk_generation_status(owner_user_id="owner-a")
    assert status == {"ok": True, "active": False, "terminal": False, "status": "none", "items": []}


def test_results_pipeline_runs_cte_projects_every_column_latest_run_consumes():
    """Regression: latest_run selects FROM the pipeline_runs CTE, not the base
    table, so any column it consumes must survive that CTE's projection.

    The first implementation projected only run_id/status/started_at/finished_at
    and PostgreSQL rejected the statement with
    `column "total_count" does not exist`, which surfaced as an opaque HTTP 503.
    """
    import re

    sql = store.get_bulk_generation_pipeline_results_postgres_payload(
        owner_user_id="owner-a",
        pipeline_run_id="pipeline-a",
        print_only=True,
        ensure_schema=False,
    )["sql"]

    def cte_body(name: str, terminator: str) -> str:
        start = sql.index(f"{name} AS (")
        return sql[start:sql.index(terminator, start)]

    pipeline_runs = cte_body("WITH pipeline_runs", "), attempts AS (")
    latest_run = cte_body("), latest_run", "\n)\nSELECT json_build_object")

    # latest_run must read from the CTE (that is what makes the projection matter).
    assert "FROM pipeline_runs" in latest_run

    projected = {
        column.strip()
        for column in re.search(
            r"SELECT\s+(.*?)\s+FROM bulk_generation_runs", pipeline_runs, re.S
        ).group(1).replace("\n", " ").split(",")
    }
    consumed = {
        column.strip()
        for column in re.search(
            r"SELECT\s+(.*?)\s+FROM pipeline_runs", latest_run, re.S
        ).group(1).replace("\n", " ").split(",")
    }
    missing = consumed - projected
    assert not missing, f"pipeline_runs CTE drops columns latest_run needs: {sorted(missing)}"

    # The four columns the original defect dropped are explicitly pinned.
    for column in (
        "total_count",
        "completed_count",
        "succeeded_count",
        "needs_attention_count",
    ):
        assert column in projected
