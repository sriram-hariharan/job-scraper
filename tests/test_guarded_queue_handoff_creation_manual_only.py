from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services


ENDPOINT = "/api/manual-guarded-queue-handoff-create"


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _ready_payload(approval_status: str = "approved") -> dict:
    return {
        "queue_handoff_readiness_status": "ready_for_future_queue_handoff",
        "approval_request_id": "manual_guarded_approval_123",
        "approval_status": approval_status,
        "ready_for_future_queue_handoff": True,
        "queue_handoff_allowed_later": True,
        "blocked_actions": [],
        "missing_requirements": [],
        "required_human_confirmation": True,
        "source_readback_status": "found",
        "source_transition_observability_status": "observed_updated",
        "context_id": "ctx-1",
        "job_id": "job-1",
    }


def _readback(approval_status: str = "approved") -> dict:
    return {
        "readback_status": "found",
        "approval_request_id": "manual_guarded_approval_123",
        "approval_request_fields": {"approval_status": approval_status},
        "approval_request_summary": {"approval_status": approval_status},
        "context_id": "ctx-1",
        "job_id": "job-1",
    }


def _transition_observability() -> dict:
    return {
        "transition_observability_status": "observed_updated",
        "approval_request_id": "manual_guarded_approval_123",
        "transition_was_applied": True,
        "new_status": "approved",
    }


def _assert_queue_creation_safety(payload: dict, *, created: bool) -> None:
    safety = payload["safety_metadata"]
    assert payload["manual_surface"] is True
    assert safety["manual_only"] is True
    assert safety["guarded_queue_handoff_only"] is True
    assert safety["human_confirmation_required"] is True
    assert safety["did_create_approval"] is False
    assert safety["did_mutate_approval"] is False
    assert safety["did_update_approval_status"] is False
    assert safety["did_mutate_queue"] is created
    assert safety["did_write_queue"] is created
    assert safety["did_mutate_resume"] is False
    assert safety["did_mutate_scoring"] is False
    assert safety["did_change_ranking"] is False
    assert safety["did_execute_application"] is False
    assert safety["did_submit_application"] is False
    assert safety["pipeline_wiring_added"] is False
    assert safety["auto_apply_enabled"] is False
    assert safety["advisory_only"] is (not created)


def test_blocks_when_reviewer_confirmation_is_missing():
    calls = []

    payload = services.build_guarded_queue_handoff_creation_payload(
        queue_handoff_readiness_payload=_ready_payload(),
        reviewer_confirmation=False,
        queue_writer=lambda entry: calls.append(entry),
    )

    assert payload["queue_handoff_creation_status"] == "blocked_by_missing_confirmation"
    assert payload["queue_entry_created"] is False
    assert "reviewer_confirmation_missing" in payload["blocked_actions"]
    assert calls == []
    _assert_queue_creation_safety(payload, created=False)


def test_blocks_when_approval_request_id_is_missing():
    calls = []

    payload = services.build_guarded_queue_handoff_creation_payload(
        queue_handoff_readiness_payload={
            "queue_handoff_readiness_status": "ready_for_future_queue_handoff",
            "approval_status": "approved",
        },
        reviewer_confirmation=True,
        queue_writer=lambda entry: calls.append(entry),
    )

    assert payload["queue_handoff_creation_status"] == "blocked_missing_approval_request_id"
    assert "approval_request_id_missing" in payload["blocked_actions"]
    assert calls == []
    _assert_queue_creation_safety(payload, created=False)


def test_blocks_when_readiness_preview_is_missing_or_not_ready():
    calls = []
    missing = services.build_guarded_queue_handoff_creation_payload(
        approval_request_id="manual_guarded_approval_123",
        reviewer_confirmation=True,
        queue_writer=lambda entry: calls.append(entry),
    )
    not_ready = services.build_guarded_queue_handoff_creation_payload(
        approval_request_id="manual_guarded_approval_123",
        reviewer_confirmation=True,
        queue_handoff_readiness_payload={
            "queue_handoff_readiness_status": "blocked_not_approved",
            "approval_request_id": "manual_guarded_approval_123",
            "approval_status": "pending",
        },
        queue_writer=lambda entry: calls.append(entry),
    )

    assert missing["queue_handoff_creation_status"] == "blocked_by_readiness_preview"
    assert not_ready["queue_handoff_creation_status"] == "blocked_by_readiness_preview"
    assert calls == []
    _assert_queue_creation_safety(missing, created=False)
    _assert_queue_creation_safety(not_ready, created=False)


def test_blocks_when_approval_is_not_approved():
    calls = []

    payload = services.build_guarded_queue_handoff_creation_payload(
        queue_handoff_readiness_payload=_ready_payload("pending"),
        reviewer_confirmation=True,
        queue_writer=lambda entry: calls.append(entry),
    )

    assert payload["queue_handoff_creation_status"] == "blocked_not_approved"
    assert "approval_request_not_approved" in payload["blocked_actions"]
    assert calls == []
    _assert_queue_creation_safety(payload, created=False)


def test_blocks_when_queue_writer_is_unavailable():
    payload = services.build_guarded_queue_handoff_creation_payload(
        queue_handoff_readiness_payload=_ready_payload(),
        reviewer_confirmation=True,
    )

    assert payload["queue_handoff_creation_status"] == "blocked_by_missing_queue_writer"
    assert payload["queue_entry_created"] is False
    assert "queue_writer_unavailable" in payload["blocked_actions"]
    _assert_queue_creation_safety(payload, created=False)


def test_creates_exactly_one_queue_handoff_when_ready_confirmed_and_writer_exists():
    calls = []
    readiness = _ready_payload()
    original_readiness = deepcopy(readiness)

    def fake_queue_writer(entry):
        calls.append(entry)
        return {"queue_handoff_id": entry["queue_handoff_id"], "persisted": True}

    payload = services.build_guarded_queue_handoff_creation_payload(
        queue_handoff_readiness_payload=readiness,
        reviewer_confirmation=True,
        reviewer_note="Approved for handoff.",
        queue_writer=fake_queue_writer,
    )

    assert readiness == original_readiness
    assert payload["queue_handoff_creation_status"] == "created"
    assert payload["approval_request_id"] == "manual_guarded_approval_123"
    assert payload["queue_entry_created"] is True
    assert payload["queue_handoff_id"].startswith("manual_queue_handoff_")
    assert len(calls) == 1
    assert calls[0]["approval_request_id"] == "manual_guarded_approval_123"
    assert calls[0]["approval_status"] == "approved"
    assert calls[0]["execute_application"] is False
    assert calls[0]["submit_application"] is False
    _assert_queue_creation_safety(payload, created=True)


def test_api_route_exists_as_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"POST"}


def test_api_route_blocks_without_queue_writer(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "queue_handoff_readiness_payload": _ready_payload(),
            "reviewer_confirmation": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["api_surface"] == "manual_guarded_queue_handoff_create"
    assert payload["explicit_user_action"] is True
    assert payload["queue_handoff_creation_status"] == "blocked_by_missing_queue_writer"
    _assert_queue_creation_safety(payload, created=False)


def test_api_route_slice_has_no_approval_status_resume_scoring_ranking_execution_or_submission_calls():
    source = Path("src/app/api.py").read_text()
    start = source.index("class ManualGuardedQueueHandoffCreateRequest")
    class_end = source.index("@asynccontextmanager")
    route_start = source.index('@app.post("/api/manual-guarded-queue-handoff-create")')
    route_end = source.index('@app.get("/api/agent-feedback")', route_start)
    snippet = source[start:class_end] + source[route_start:route_end]

    forbidden_markers = [
        "record_approval_decision(",
        "approval_status=",
        "create_approval_request(",
        "execute_application(",
        "submit_application(",
        "score_resume_job_match",
        "ranking_update",
        "ranking_mutation",
        "workflow_runner",
        "insert_operator_decision",
        "mutate_resume(",
        "resume_mutation",
        "resume_update",
    ]
    for marker in forbidden_markers:
        assert marker not in snippet


def test_service_helper_slice_limits_mutation_to_injected_queue_writer():
    source = Path("src/app/services.py").read_text()
    start = source.index("def build_guarded_queue_handoff_creation_payload")
    end = source.index("def _agentic_workflow_summary_from_artifacts")
    snippet = source[start:end]

    forbidden_markers = [
        "record_approval_decision(",
        "get_approval_request(",
        "create_approval_request(",
        "_load_csv_rows",
        "write_text",
        ".write(",
        "execute_application(",
        "submit_application(",
        "score_resume_job_match",
        "ranking_update",
        "ranking_mutation",
        "workflow_runner",
        "insert_operator_decision",
        "mutate_resume(",
        "resume_mutation",
        "resume_update",
    ]
    for marker in forbidden_markers:
        assert marker not in snippet
    assert "queue_writer(" in snippet


def test_ui_renders_confirmation_control_and_escapes_output():
    source = Path("src/app/static/agentic_review.js").read_text()
    start = source.index("function renderManualGuardedQueueHandoffCreateSection")
    end = source.index("function renderAgentTraceReadOnlyPanel")
    snippet = source[start:end]

    assert "Manual Guarded Queue Handoff Creation" in snippet
    assert "Create Guarded Queue Handoff" in snippet
    assert "data-manual-guarded-queue-handoff-create" in snippet
    assert "data-manual-guarded-queue-handoff-create-confirmation" in snippet
    assert "escapeHtml(approvalRequestId)" in snippet
    assert "escapeHtml(contextId)" in snippet
    assert "escapeHtml(jobId)" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Blocked actions\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Safety metadata\"" in snippet


def test_ui_click_posts_endpoint_and_existing_queue_readiness_preview_still_works():
    source = Path("src/app/static/agentic_review.js").read_text()

    assert source.count("/api/manual-guarded-queue-handoff-create") == 1
    assert "manual_guarded_queue_handoff_create_result" in source
    assert "renderManualGuardedQueueHandoffCreateSection(tracePayload)" in source
    assert source.count("/api/manual-queue-handoff-readiness-preview-dry-run") == 1
    assert "manual_queue_handoff_readiness_preview_result" in source
    assert "renderManualQueueHandoffReadinessPreviewSection(tracePayload)" in source
