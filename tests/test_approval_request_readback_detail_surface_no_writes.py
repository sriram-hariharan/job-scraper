from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services
from src.storage.agentic_approvals import store


ENDPOINT = "/api/manual-approval-request-readback"


class FakeConnection:
    pass


class FakeReadStorage:
    def __init__(self, rows=None):
        self.rows = dict(rows or {})
        self.calls = []

    def get_approval_request(self, connection, **kwargs):
        self.calls.append((connection, kwargs))
        return self.rows.get(kwargs["approval_request_id"])


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _approval_row() -> dict:
    return {
        "approval_request_id": "manual_guarded_approval_123",
        "dry_run_artifact_id": "approval_preview_123",
        "owner_id": "ctx-1",
        "idempotency_key": "secret-ish-internal-key",
        "approval_status": "pending",
        "proposed_action_type": "review_packet_approval_preview",
        "proposed_action_summary": "Preview approval fields only.",
        "safety_gate_snapshot_json": {"internal": "snapshot"},
        "reviewer_id": "",
        "review_decision": "",
        "review_reason": "",
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
        "expires_at": "2026-01-08T00:00:00+00:00",
        "approved_at": "",
        "denied_at": "",
        "revoked_at": "",
    }


def _created_payload() -> dict:
    return {
        "approval_creation_status": "created",
        "created_approval_request_id": "manual_guarded_approval_123",
        "context_id": "ctx-1",
        "job_id": "job-1",
    }


def _observability_payload() -> dict:
    return {
        "observability_status": "observed_created",
        "created_approval_request_id": "manual_guarded_approval_123",
    }


def _assert_readback_safety(payload: dict) -> None:
    safety = payload["safety_metadata"]
    assert payload["read_only"] is True
    assert payload["manual_surface"] is True
    assert safety["read_only"] is True
    assert safety["approval_request_readback_only"] is True
    assert safety["manual_only"] is True
    assert safety["did_create_approval"] is False
    assert safety["did_mutate_approval"] is False
    assert safety["did_mutate_queue"] is False
    assert safety["did_mutate_resume"] is False
    assert safety["did_mutate_scoring"] is False
    assert safety["did_change_ranking"] is False
    assert safety["did_execute_application"] is False
    assert safety["did_submit_application"] is False
    assert safety["pipeline_wiring_added"] is False
    assert safety["auto_apply_enabled"] is False
    assert safety["advisory_only"] is True


def test_helper_returns_missing_approval_request_id_when_absent():
    payload = services.build_approval_request_readback_payload()

    assert payload["readback_status"] == "missing_approval_request_id"
    assert payload["approval_request_found"] is False
    assert "approval_request_id_missing" in payload["blocked_actions"]
    _assert_readback_safety(payload)


def test_helper_returns_not_found_for_unknown_id():
    storage = FakeReadStorage()
    connection = FakeConnection()

    payload = services.build_approval_request_readback_payload(
        approval_request_id="manual_guarded_approval_missing",
        connection=connection,
        storage_module=storage,
    )

    assert payload["readback_status"] == "not_found"
    assert payload["approval_request_found"] is False
    assert storage.calls == [
        (connection, {"approval_request_id": "manual_guarded_approval_missing"})
    ]
    _assert_readback_safety(payload)


def test_helper_returns_found_for_existing_approval_request():
    row = _approval_row()
    storage = FakeReadStorage({row["approval_request_id"]: row})

    payload = services.build_approval_request_readback_payload(
        guarded_creation_payload=_created_payload(),
        observability_payload=_observability_payload(),
        connection=FakeConnection(),
        storage_module=storage,
    )

    assert payload["readback_status"] == "found"
    assert payload["approval_request_found"] is True
    assert payload["approval_request_id"] == "manual_guarded_approval_123"
    assert payload["approval_request_summary"]["approval_status"] == "pending"
    assert payload["approval_request_fields"]["proposed_action_type"] == "review_packet_approval_preview"
    assert "idempotency_key" not in payload["approval_request_fields"]
    assert "safety_gate_snapshot_json" not in payload["approval_request_fields"]
    assert payload["source_creation_status"] == "created"
    assert payload["source_observability_status"] == "observed_created"
    _assert_readback_safety(payload)


def test_api_route_exists_as_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"POST"}


def test_api_route_returns_readonly_readback(monkeypatch):
    row = _approval_row()
    connection = FakeConnection()
    calls = []

    def fake_get_approval_request(passed_connection, **kwargs):
        calls.append((passed_connection, kwargs))
        return row

    monkeypatch.setattr(api, "_agentic_approval_storage_connection", lambda: connection)
    monkeypatch.setattr(store, "get_approval_request", fake_get_approval_request)

    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "guarded_creation_payload": _created_payload(),
            "observability_payload": _observability_payload(),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["api_surface"] == "manual_approval_request_readback"
    assert payload["explicit_user_action"] is True
    assert payload["readback_status"] == "found"
    assert payload["approval_request_found"] is True
    assert calls == [(connection, {"approval_request_id": "manual_guarded_approval_123"})]
    _assert_readback_safety(payload)


def test_api_route_slice_has_no_creation_scoring_queue_execution_or_submission_calls():
    source = Path("src/app/api.py").read_text()
    start = source.index("class ManualApprovalRequestReadbackRequest")
    class_end = source.index("@asynccontextmanager")
    route_start = source.index('@app.post("/api/manual-approval-request-readback")')
    route_end = source.index('@app.get("/api/agent-feedback/summary")')
    snippet = source[start:class_end] + source[route_start:route_end]

    forbidden_markers = [
        "create_approval_request(",
        "app_service_persist_agentic_approval_request(",
        "record_approval_decision(",
        "application_execution_queue",
        "submit_application(",
        "execute_application(",
        "score_resume_job_match",
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
    assert "get_approval_request" not in snippet


def test_service_helper_slice_has_no_creation_scoring_queue_execution_or_submission_calls():
    source = Path("src/app/services.py").read_text()
    start = source.index("def build_approval_request_readback_payload")
    end = source.index("def _artifact_row_by_name")
    snippet = source[start:end]

    forbidden_markers = [
        "create_approval_request(",
        "app_service_persist_agentic_approval_request(",
        "record_approval_decision(",
        "application_execution_queue",
        "execute_application(",
        "submit_application(",
        "score_resume_job_match",
        "ranking_update",
        "ranking_mutation",
        "workflow_runner",
        "insert_operator_decision",
    ]
    for marker in forbidden_markers:
        assert marker not in snippet
    assert ".get_approval_request(" in snippet


def test_ui_renders_readback_button_and_escapes_output():
    source = Path("src/app/static/agentic_review.js").read_text()
    start = source.index("function renderManualApprovalRequestReadbackSection")
    end = source.index("function renderAgentTraceReadOnlyPanel")
    snippet = source[start:end]

    assert "Manual Approval Request Readback" in snippet
    assert "Read Approval Request" in snippet
    assert "data-manual-approval-request-readback" in snippet
    assert "escapeHtml(approvalRequestId)" in snippet
    assert "escapeHtml(contextId)" in snippet
    assert "escapeHtml(jobId)" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Approval request summary\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Approval request fields\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Safety metadata\"" in snippet


def test_ui_click_posts_endpoint_and_existing_guarded_surfaces_still_exist():
    source = Path("src/app/static/agentic_review.js").read_text()

    assert source.count("/api/manual-approval-request-readback") == 1
    assert "manual_approval_request_readback_result" in source
    assert "renderManualApprovalRequestReadbackSection(tracePayload)" in source
    assert source.count("/api/manual-guarded-approval-request-create") == 1
    assert source.count("/api/manual-guarded-approval-creation-observability") == 1
    assert "renderManualGuardedApprovalRequestCreateSection(tracePayload)" in source
    assert "renderManualGuardedApprovalCreationObservabilitySection(tracePayload)" in source
