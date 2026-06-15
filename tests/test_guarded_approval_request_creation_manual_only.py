from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services
from src.storage.agentic_approvals import store


ENDPOINT = "/api/manual-guarded-approval-request-create"


class FakeStorageModule:
    def __init__(self):
        self.created_requests = []

    def create_approval_request(self, connection, **kwargs):
        self.created_requests.append((connection, kwargs))
        return {
            "approval_request_id": kwargs["approval_request_id"],
            "approval_status": "pending",
            "idempotency_key": kwargs["idempotency_key"],
        }


class FakeConnection:
    pass


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _approval_preview_payload() -> dict:
    return {
        "approval_preview_status": "ready_for_approval_preview",
        "approval_preview_type": "review_packet_approval_preview",
        "approval_title": "Review packet approval preview",
        "approval_summary": "Preview approval fields only.",
        "proposed_decision": "request_human_review",
        "proposed_next_step": "human_reviewer_confirms_review_packet",
        "required_reviewer_confirmation": True,
        "approval_fields_preview": {
            "title": "Review packet approval preview",
            "source_planned_action": "prepare_review_packet",
            "source_review_packet_status": "ready_for_review",
            "context_id": "ctx-1",
            "job_id": "job-1",
        },
        "blocked_actions": [],
        "source_review_packet_status": "ready_for_review",
        "context_id": "ctx-1",
        "job_id": "job-1",
    }


def _ready_gate_payload() -> dict:
    return {
        "approval_creation_gate_status": "ready",
        "gate_decision": "ready_for_future_approval_creation",
        "can_create_approval_request_later": True,
        "missing_requirements": [],
        "blocked_actions": [],
        "required_reviewer_confirmation": True,
        "source_approval_preview_status": "ready_for_approval_preview",
        "next_safe_step": "future_explicit_approval_creation_step_required",
        "context_id": "ctx-1",
        "job_id": "job-1",
    }


def _blocked_gate_payload() -> dict:
    return {
        "approval_creation_gate_status": "waiting_for_confirmation",
        "gate_decision": "needs_reviewer_confirmation",
        "can_create_approval_request_later": False,
        "missing_requirements": ["reviewer_confirmation"],
        "blocked_actions": ["reviewer_confirmation"],
        "required_reviewer_confirmation": True,
        "source_approval_preview_status": "ready_for_approval_preview",
    }


def _assert_non_mutating_safety(payload: dict, *, created: bool) -> None:
    safety = payload["safety_metadata"]
    assert safety["manual_only"] is True
    assert safety["guarded_approval_creation_only"] is True
    assert safety["human_confirmation_required"] is True
    assert safety["did_create_approval"] is created
    assert safety["did_mutate_approval"] is False
    assert safety["did_mutate_queue"] is False
    assert safety["did_mutate_resume"] is False
    assert safety["did_mutate_scoring"] is False
    assert safety["did_change_ranking"] is False
    assert safety["did_execute_application"] is False
    assert safety["did_submit_application"] is False
    assert safety["pipeline_wiring_added"] is False
    assert safety["auto_apply_enabled"] is False
    assert safety["advisory_only"] is (not created)


def test_blocks_when_approval_creation_gate_is_missing():
    fake_storage = FakeStorageModule()

    payload = services.build_guarded_approval_request_creation_payload(
        approval_creation_gate_payload={},
        approval_preview_payload={},
        reviewer_confirmation=True,
        connection=FakeConnection(),
        storage_module=fake_storage,
    )

    assert payload["approval_creation_status"] in {
        "insufficient_information",
        "blocked_by_invalid_preview",
        "blocked_by_gate",
    }
    assert payload["created_approval_request_id"] == ""
    assert fake_storage.created_requests == []
    _assert_non_mutating_safety(payload, created=False)


def test_blocks_when_gate_is_not_ready():
    fake_storage = FakeStorageModule()
    connection_calls = []

    payload = services.build_guarded_approval_request_creation_payload(
        approval_creation_gate_payload=_blocked_gate_payload(),
        approval_preview_payload=_approval_preview_payload(),
        reviewer_confirmation=True,
        connection_provider=lambda: connection_calls.append("called") or FakeConnection(),
        storage_module=fake_storage,
    )

    assert payload["approval_creation_status"] == "blocked_by_gate"
    assert payload["gate_decision"] == "needs_reviewer_confirmation"
    assert payload["created_approval_request_id"] == ""
    assert connection_calls == []
    assert fake_storage.created_requests == []
    _assert_non_mutating_safety(payload, created=False)


def test_blocks_when_reviewer_confirmation_is_missing():
    fake_storage = FakeStorageModule()
    connection_calls = []

    payload = services.build_guarded_approval_request_creation_payload(
        approval_creation_gate_payload=_ready_gate_payload(),
        approval_preview_payload=_approval_preview_payload(),
        reviewer_confirmation=False,
        connection_provider=lambda: connection_calls.append("called") or FakeConnection(),
        storage_module=fake_storage,
    )

    assert payload["approval_creation_status"] == "blocked_by_missing_confirmation"
    assert payload["created_approval_request_id"] == ""
    assert "reviewer_confirmation_missing" in payload["blocked_actions"]
    assert connection_calls == []
    assert fake_storage.created_requests == []
    _assert_non_mutating_safety(payload, created=False)


def test_creates_exactly_one_approval_request_when_gate_ready_and_confirmed():
    fake_storage = FakeStorageModule()
    connection = FakeConnection()
    preview = _approval_preview_payload()
    gate = _ready_gate_payload()
    original_preview = deepcopy(preview)
    original_gate = deepcopy(gate)

    payload = services.build_guarded_approval_request_creation_payload(
        approval_creation_gate_payload=gate,
        approval_preview_payload=preview,
        reviewer_confirmation=True,
        connection=connection,
        storage_module=fake_storage,
    )

    assert preview == original_preview
    assert gate == original_gate
    assert payload["approval_creation_status"] == "created"
    assert payload["gate_decision"] == "ready_for_future_approval_creation"
    assert payload["created_approval_request_id"].startswith("manual_guarded_approval_")
    assert payload["approval_request_preview"]["approval_preview_status"] == "ready_for_approval_preview"
    assert len(fake_storage.created_requests) == 1
    passed_connection, create_kwargs = fake_storage.created_requests[0]
    assert passed_connection is connection
    assert create_kwargs["proposed_action_type"] == "review_packet_approval_preview"
    assert create_kwargs["proposed_action_summary"] == "Preview approval fields only."
    assert create_kwargs["queue_safety_gate_snapshot"] == {}
    _assert_non_mutating_safety(payload, created=True)


def test_api_route_exists_as_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"POST"}


def test_api_route_creates_with_fake_storage_only(monkeypatch):
    connection = FakeConnection()
    calls = []

    def fake_create_approval_request(passed_connection, **kwargs):
        calls.append((passed_connection, kwargs))
        return {
            "approval_request_id": kwargs["approval_request_id"],
            "approval_status": "pending",
            "idempotency_key": kwargs["idempotency_key"],
        }

    monkeypatch.setattr(api, "_agentic_approval_storage_connection", lambda: connection)
    monkeypatch.setattr(store, "create_approval_request", fake_create_approval_request)

    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "approval_creation_gate_payload": _ready_gate_payload(),
            "approval_preview_payload": _approval_preview_payload(),
            "reviewer_confirmation": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["api_surface"] == "manual_guarded_approval_request_create"
    assert payload["explicit_user_action"] is True
    assert payload["approval_creation_status"] == "created"
    assert payload["created_approval_request_id"].startswith("manual_guarded_approval_")
    assert len(calls) == 1
    assert calls[0][0] is connection
    _assert_non_mutating_safety(payload, created=True)


def test_api_blocks_without_confirmation_and_does_not_open_storage(monkeypatch):
    calls = []
    monkeypatch.setattr(api, "_agentic_approval_storage_connection", lambda: calls.append("connection"))
    monkeypatch.setattr(store, "create_approval_request", lambda *args, **kwargs: calls.append("create"))

    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "approval_creation_gate_payload": _ready_gate_payload(),
            "approval_preview_payload": _approval_preview_payload(),
            "reviewer_confirmation": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["approval_creation_status"] == "blocked_by_missing_confirmation"
    assert payload["created_approval_request_id"] == ""
    assert calls == []
    _assert_non_mutating_safety(payload, created=False)


def test_api_route_slice_has_no_queue_scoring_ranking_execution_or_submission_calls():
    source = Path("src/app/api.py").read_text()
    start = source.index("class ManualGuardedApprovalRequestCreateRequest")
    class_end = source.index("@asynccontextmanager")
    route_start = source.index('@app.post("/api/manual-guarded-approval-request-create")')
    route_end = source.index(
        '@app.post(\n    "/api/agentic-approvals/{approval_request_id}/production-scheduler-observability-reporting-job"'
    )
    snippet = source[start:class_end] + source[route_start:route_end]

    forbidden_markers = [
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


def test_service_helper_slice_limits_storage_to_explicit_persist_call_site():
    source = Path("src/app/services.py").read_text()
    start = source.index("def build_guarded_approval_request_creation_payload")
    end = source.index("def _artifact_row_by_name")
    snippet = source[start:end]

    forbidden_markers = [
        "application_execution_queue",
        "execute_application(",
        "submit_application(",
        "score_resume_job_match",
        "ranking_update",
        "ranking_mutation",
        "workflow_runner",
        "insert_operator_decision",
        "record_approval_decision(",
    ]
    for marker in forbidden_markers:
        assert marker not in snippet
    assert "app_service_persist_agentic_approval_request(" in snippet


def test_ui_renders_confirmation_control_and_escapes_output():
    source = Path("src/app/static/agentic_review.js").read_text()
    start = source.index("function renderManualGuardedApprovalRequestCreateSection")
    end = source.index("function renderAgentTraceReadOnlyPanel")
    snippet = source[start:end]

    assert "Manual Guarded Approval Request Creation" in snippet
    assert "Create Guarded Approval Request" in snippet
    assert "data-manual-guarded-approval-request-create" in snippet
    assert "data-manual-guarded-approval-request-create-confirmation" in snippet
    assert "escapeHtml(contextId)" in snippet
    assert "escapeHtml(jobId)" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Created approval request id\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Approval request preview\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Safety metadata\"" in snippet


def test_ui_click_posts_endpoint_and_existing_gate_surface_still_works():
    source = Path("src/app/static/agentic_review.js").read_text()

    assert source.count("/api/manual-guarded-approval-request-create") == 1
    assert "manual_guarded_approval_request_create_result" in source
    assert "renderManualGuardedApprovalRequestCreateSection(tracePayload)" in source
    assert source.count("/api/manual-approval-creation-gate-dry-run") == 1
    assert "renderManualApprovalCreationGateDryRunSection(tracePayload)" in source
