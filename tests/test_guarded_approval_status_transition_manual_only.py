from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services
from src.storage.agentic_approvals import store


ENDPOINT = "/api/manual-guarded-approval-status-transition"


class FakeConnection:
    pass


class FakeStorageModule:
    def __init__(self):
        self.decisions = []

    def record_approval_decision(self, connection, **kwargs):
        self.decisions.append((connection, kwargs))
        return {
            "approval_request_id": kwargs["approval_request_id"],
            "approval_status": kwargs["approval_status"],
            "reviewer_id": kwargs["reviewer_id"],
            "review_reason": kwargs.get("review_reason", ""),
        }


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _found_readback() -> dict:
    return {
        "readback_status": "found",
        "approval_request_id": "manual_guarded_approval_123",
        "approval_request_found": True,
        "approval_request_summary": {"approval_status": "pending"},
        "approval_request_fields": {"approval_status": "pending"},
        "context_id": "ctx-1",
        "job_id": "job-1",
    }


def _ready_preview(transition: str = "approve") -> dict:
    target = {
        "approve": "approved",
        "reject": "denied",
        "needs_changes": "pending",
    }[transition]
    return {
        "transition_preview_status": "preview_ready",
        "approval_request_id": "manual_guarded_approval_123",
        "proposed_transition": transition,
        "transition_allowed_later": True,
        "would_change_status_to": target,
        "required_reviewer_confirmation": True,
        "blocked_actions": [],
        "source_readback_status": "found",
        "context_id": "ctx-1",
        "job_id": "job-1",
    }


def _assert_transition_safety(payload: dict, *, updated: bool) -> None:
    safety = payload["safety_metadata"]
    assert payload["manual_surface"] is True
    assert safety["manual_only"] is True
    assert safety["guarded_status_transition_only"] is True
    assert safety["human_confirmation_required"] is True
    assert safety["did_create_approval"] is False
    assert safety["did_mutate_approval"] is updated
    assert safety["did_update_approval_status"] is updated
    assert safety["did_mutate_queue"] is False
    assert safety["did_mutate_resume"] is False
    assert safety["did_mutate_scoring"] is False
    assert safety["did_change_ranking"] is False
    assert safety["did_execute_application"] is False
    assert safety["did_submit_application"] is False
    assert safety["pipeline_wiring_added"] is False
    assert safety["auto_apply_enabled"] is False
    assert safety["advisory_only"] is (not updated)


def test_blocks_when_preview_is_missing_and_does_not_open_storage():
    storage = FakeStorageModule()
    connection_calls = []

    payload = services.build_guarded_approval_status_transition_payload(
        approval_request_id="manual_guarded_approval_123",
        proposed_transition="approve",
        reviewer_confirmation=True,
        approval_request_readback_payload=_found_readback(),
        transition_preview_payload={},
        connection_provider=lambda: connection_calls.append("called") or FakeConnection(),
        storage_module=storage,
    )

    assert payload["approval_status_transition_status"] == "blocked_by_preview"
    assert payload["transition_applied"] is False
    assert "transition_preview_not_ready" in payload["blocked_actions"]
    assert connection_calls == []
    assert storage.decisions == []
    _assert_transition_safety(payload, updated=False)


def test_blocks_when_reviewer_confirmation_is_missing():
    storage = FakeStorageModule()
    connection_calls = []

    payload = services.build_guarded_approval_status_transition_payload(
        proposed_transition="approve",
        reviewer_confirmation=False,
        transition_preview_payload=_ready_preview("approve"),
        approval_request_readback_payload=_found_readback(),
        connection_provider=lambda: connection_calls.append("called") or FakeConnection(),
        storage_module=storage,
    )

    assert payload["approval_status_transition_status"] == "blocked_by_missing_confirmation"
    assert "reviewer_confirmation_missing" in payload["blocked_actions"]
    assert connection_calls == []
    assert storage.decisions == []
    _assert_transition_safety(payload, updated=False)


def test_blocks_missing_approval_request_id():
    payload = services.build_guarded_approval_status_transition_payload(
        proposed_transition="approve",
        reviewer_confirmation=True,
        transition_preview_payload={"transition_preview_status": "preview_ready"},
        approval_request_readback_payload={},
    )

    assert payload["approval_status_transition_status"] == "blocked_missing_approval_request_id"
    assert payload["approval_request_id"] == ""
    assert "approval_request_id_missing" in payload["blocked_actions"]
    _assert_transition_safety(payload, updated=False)


def test_blocks_invalid_transition_without_storage():
    storage = FakeStorageModule()

    payload = services.build_guarded_approval_status_transition_payload(
        approval_request_id="manual_guarded_approval_123",
        proposed_transition="ship_it",
        reviewer_confirmation=True,
        transition_preview_payload=_ready_preview("approve"),
        approval_request_readback_payload=_found_readback(),
        connection=FakeConnection(),
        storage_module=storage,
    )

    assert payload["approval_status_transition_status"] == "blocked_invalid_transition"
    assert "proposed_transition_invalid" in payload["blocked_actions"]
    assert storage.decisions == []
    _assert_transition_safety(payload, updated=False)


def test_blocks_when_readback_says_approval_request_not_found():
    storage = FakeStorageModule()

    payload = services.build_guarded_approval_status_transition_payload(
        approval_request_id="manual_guarded_approval_123",
        proposed_transition="approve",
        reviewer_confirmation=True,
        transition_preview_payload=_ready_preview("approve"),
        approval_request_readback_payload={
            "readback_status": "not_found",
            "approval_request_id": "manual_guarded_approval_123",
            "approval_request_found": False,
        },
        connection=FakeConnection(),
        storage_module=storage,
    )

    assert payload["approval_status_transition_status"] == "blocked_not_found"
    assert "approval_request_not_found" in payload["blocked_actions"]
    assert storage.decisions == []
    _assert_transition_safety(payload, updated=False)


def test_updates_exactly_one_approval_request_status_when_preview_ready_and_confirmed():
    storage = FakeStorageModule()
    connection = FakeConnection()
    preview = _ready_preview("approve")
    readback = _found_readback()
    original_preview = deepcopy(preview)
    original_readback = deepcopy(readback)

    payload = services.build_guarded_approval_status_transition_payload(
        proposed_transition="approve",
        reviewer_confirmation=True,
        reviewer_note="Looks good for review.",
        transition_preview_payload=preview,
        approval_request_readback_payload=readback,
        connection=connection,
        storage_module=storage,
    )

    assert preview == original_preview
    assert readback == original_readback
    assert payload["approval_status_transition_status"] == "updated"
    assert payload["approval_request_id"] == "manual_guarded_approval_123"
    assert payload["applied_transition"] == "approve"
    assert payload["previous_status"] == "pending"
    assert payload["new_status"] == "approved"
    assert payload["transition_applied"] is True
    assert len(storage.decisions) == 1
    passed_connection, kwargs = storage.decisions[0]
    assert passed_connection is connection
    assert kwargs["approval_request_id"] == "manual_guarded_approval_123"
    assert kwargs["approval_status"] == "approved"
    assert kwargs["reviewer_id"] == "manual_operator"
    assert kwargs["review_reason"] == "Looks good for review."
    _assert_transition_safety(payload, updated=True)


def test_reject_transition_uses_existing_denied_storage_status():
    storage = FakeStorageModule()

    payload = services.build_guarded_approval_status_transition_payload(
        proposed_transition="reject",
        reviewer_confirmation=True,
        transition_preview_payload=_ready_preview("reject"),
        approval_request_readback_payload=_found_readback(),
        connection=FakeConnection(),
        storage_module=storage,
    )

    assert payload["approval_status_transition_status"] == "updated"
    assert payload["applied_transition"] == "reject"
    assert payload["new_status"] == "denied"
    assert storage.decisions[0][1]["approval_status"] == "denied"
    _assert_transition_safety(payload, updated=True)


def test_needs_changes_blocks_because_existing_storage_has_no_matching_status():
    storage = FakeStorageModule()

    payload = services.build_guarded_approval_status_transition_payload(
        proposed_transition="needs_changes",
        reviewer_confirmation=True,
        transition_preview_payload=_ready_preview("needs_changes"),
        approval_request_readback_payload=_found_readback(),
        connection=FakeConnection(),
        storage_module=storage,
    )

    assert payload["approval_status_transition_status"] == "blocked_invalid_transition"
    assert "transition_not_supported_by_existing_storage_status_values" in payload["blocked_actions"]
    assert storage.decisions == []
    _assert_transition_safety(payload, updated=False)


def test_api_route_exists_as_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"POST"}


def test_api_route_updates_with_fake_storage_only(monkeypatch):
    connection = FakeConnection()
    calls = []

    def fake_record_approval_decision(passed_connection, **kwargs):
        calls.append((passed_connection, kwargs))
        return {
            "approval_request_id": kwargs["approval_request_id"],
            "approval_status": kwargs["approval_status"],
            "reviewer_id": kwargs["reviewer_id"],
        }

    monkeypatch.setattr(api, "_agentic_approval_storage_connection", lambda: connection)
    monkeypatch.setattr(store, "record_approval_decision", fake_record_approval_decision)

    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "proposed_transition": "approve",
            "reviewer_confirmation": True,
            "transition_preview_payload": _ready_preview("approve"),
            "approval_request_readback_payload": _found_readback(),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["api_surface"] == "manual_guarded_approval_status_transition"
    assert payload["explicit_user_action"] is True
    assert payload["approval_status_transition_status"] == "updated"
    assert payload["new_status"] == "approved"
    assert len(calls) == 1
    assert calls[0][0] is connection
    _assert_transition_safety(payload, updated=True)


def test_api_blocks_without_confirmation_and_does_not_open_storage(monkeypatch):
    calls = []
    monkeypatch.setattr(api, "_agentic_approval_storage_connection", lambda: calls.append("connection"))
    monkeypatch.setattr(store, "record_approval_decision", lambda *args, **kwargs: calls.append("decision"))

    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "proposed_transition": "approve",
            "reviewer_confirmation": False,
            "transition_preview_payload": _ready_preview("approve"),
            "approval_request_readback_payload": _found_readback(),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["approval_status_transition_status"] == "blocked_by_missing_confirmation"
    assert payload["transition_applied"] is False
    assert calls == []
    _assert_transition_safety(payload, updated=False)


def test_api_route_slice_has_no_queue_scoring_ranking_execution_or_submission_calls():
    source = Path("src/app/api.py").read_text()
    start = source.index("class ManualGuardedApprovalStatusTransitionRequest")
    class_end = source.index("@asynccontextmanager")
    route_start = source.index('@app.post("/api/manual-guarded-approval-status-transition")')
    route_end = source.index('@app.get("/api/agent-feedback")', route_start)
    snippet = source[start:class_end] + source[route_start:route_end]

    forbidden_markers = [
        "application_execution_queue",
        "submit_application(",
        "execute_application(",
        "score_resume_job_match",
        "ranking_state",
        "ranking_update",
        "ranking_mutation",
        "run_chat_completion",
        "openai",
        "anthropic",
        "llm_client",
        "insert_operator_decision",
    ]
    for marker in forbidden_markers:
        assert marker not in snippet


def test_service_helper_slice_limits_mutation_to_explicit_status_update_call_site():
    source = Path("src/app/services.py").read_text()
    start = source.index("def build_guarded_approval_status_transition_payload")
    end = source.index("def _agentic_workflow_summary_from_artifacts")
    snippet = source[start:end]

    forbidden_markers = [
        "application_execution_queue",
        "execute_application(",
        "submit_application(",
        "score_resume_job_match",
        "ranking_state",
        "ranking_update",
        "ranking_mutation",
        "workflow_runner",
        "insert_operator_decision",
        "create_approval_request(",
    ]
    for marker in forbidden_markers:
        assert marker not in snippet
    assert "record_approval_decision(" in snippet


def test_ui_renders_confirmation_control_and_escapes_output():
    source = Path("src/app/static/agentic_review.js").read_text()
    start = source.index("function renderManualGuardedApprovalStatusTransitionSection")
    end = source.index("function renderAgentTraceReadOnlyPanel")
    snippet = source[start:end]

    assert "Manual Guarded Approval Status Transition" in snippet
    assert "Apply Guarded Status Transition" in snippet
    assert "data-manual-guarded-approval-status-transition" in snippet
    assert "data-manual-guarded-approval-status-transition-confirmation" in snippet
    assert "escapeHtml(approvalRequestId)" in snippet
    assert "escapeHtml(proposedTransition)" in snippet
    assert "escapeHtml(contextId)" in snippet
    assert "escapeHtml(jobId)" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Applied transition\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Safety metadata\"" in snippet


def test_ui_click_posts_endpoint_and_existing_transition_preview_surface_still_works():
    source = Path("src/app/static/agentic_review.js").read_text()

    assert source.count("/api/manual-guarded-approval-status-transition") == 1
    assert "manual_guarded_approval_status_transition_result" in source
    assert "renderManualGuardedApprovalStatusTransitionSection(tracePayload)" in source
    assert source.count("/api/manual-approval-status-transition-preview-dry-run") == 1
    assert "renderManualApprovalStatusTransitionPreviewSection(tracePayload)" in source
