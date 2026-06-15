from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services


ENDPOINT = "/api/manual-guarded-approval-creation-observability"


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _created_payload() -> dict:
    return {
        "approval_creation_status": "created",
        "gate_decision": "ready_for_future_approval_creation",
        "created_approval_request_id": "manual_guarded_approval_123",
        "approval_request_preview": {"approval_preview_status": "ready_for_approval_preview"},
        "source_approval_preview_status": "ready_for_approval_preview",
        "blocked_actions": [],
        "required_reviewer_confirmation": True,
        "next_safe_step": "review_created_approval_request",
        "context_id": "ctx-1",
        "job_id": "job-1",
        "safety_metadata": {
            "manual_only": True,
            "guarded_approval_creation_only": True,
            "did_create_approval": True,
            "did_mutate_queue": False,
            "did_execute_application": False,
            "did_submit_application": False,
        },
        "approval_storage_result": {
            "approval_storage_status": "passed",
            "approval_storage_reason_codes": [],
            "approval_audit_event": {
                "audit_event_id": "audit-1",
                "approval_request_id": "manual_guarded_approval_123",
                "event_type": "approval_request_persisted",
            },
        },
    }


def _blocked_payload() -> dict:
    return {
        "approval_creation_status": "blocked_by_gate",
        "gate_decision": "needs_reviewer_confirmation",
        "created_approval_request_id": "",
        "approval_request_preview": {"approval_preview_status": "ready_for_approval_preview"},
        "source_approval_preview_status": "ready_for_approval_preview",
        "blocked_actions": ["approval_creation_gate_not_ready"],
        "required_reviewer_confirmation": True,
        "next_safe_step": "resolve_approval_creation_gate",
    }


def _assert_observability_safety(payload: dict) -> None:
    safety = payload["safety_metadata"]
    assert payload["read_only"] is True
    assert payload["manual_surface"] is True
    assert safety["read_only"] is True
    assert safety["observability_only"] is True
    assert safety["audit_trace_only"] is True
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


def test_helper_returns_observed_created_for_created_source():
    source = _created_payload()
    original = deepcopy(source)

    payload = services.build_guarded_approval_creation_observability_payload(
        guarded_creation_payload=source,
    )

    assert source == original
    assert payload["observability_status"] == "observed_created"
    assert payload["source_approval_creation_status"] == "created"
    assert payload["created_approval_request_id"] == "manual_guarded_approval_123"
    assert payload["creation_was_successful"] is True
    assert payload["creation_was_blocked"] is False
    assert payload["audit_summary"]["storage_status"] == "passed"
    assert payload["audit_events"][0]["audit_event_id"] == "audit-1"
    _assert_observability_safety(payload)


def test_helper_returns_observed_blocked_for_blocked_source():
    payload = services.build_guarded_approval_creation_observability_payload(
        guarded_creation_payload=_blocked_payload(),
    )

    assert payload["observability_status"] == "observed_blocked"
    assert payload["source_approval_creation_status"] == "blocked_by_gate"
    assert payload["creation_was_successful"] is False
    assert payload["creation_was_blocked"] is True
    assert "approval_creation_gate_not_ready" in payload["blocked_actions"]
    _assert_observability_safety(payload)


def test_missing_or_invalid_source_returns_safe_fallback():
    missing = services.build_guarded_approval_creation_observability_payload(
        guarded_creation_payload={},
    )
    invalid = services.build_guarded_approval_creation_observability_payload(
        guarded_creation_payload={"approval_creation_status": "surprise"},
    )

    assert missing["observability_status"] == "observed_missing_source"
    assert missing["creation_was_blocked"] is True
    assert invalid["observability_status"] == "observed_invalid_source"
    assert "guarded_creation_status_unrecognized" in invalid["blocked_actions"]
    _assert_observability_safety(missing)
    _assert_observability_safety(invalid)


def test_api_route_exists_as_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"POST"}


def test_api_route_returns_readonly_observability(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={"guarded_creation_payload": _created_payload()},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["api_surface"] == "manual_guarded_approval_creation_observability"
    assert payload["explicit_user_action"] is True
    assert payload["observability_status"] == "observed_created"
    assert payload["created_approval_request_id"] == "manual_guarded_approval_123"
    _assert_observability_safety(payload)


def test_api_route_slice_has_no_storage_scoring_queue_approval_execution_or_llm_calls():
    source = Path("src/app/api.py").read_text()
    start = source.index("class ManualGuardedApprovalCreationObservabilityRequest")
    class_end = source.index("@asynccontextmanager")
    route_start = source.index('@app.post("/api/manual-guarded-approval-creation-observability")')
    route_end = source.index('@app.get("/api/agent-feedback/summary")')
    snippet = source[start:class_end] + source[route_start:route_end]

    forbidden_markers = [
        "_agentic_approval_storage_connection",
        "create_approval_request(",
        "app_service_persist_agentic_approval_request(",
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


def test_service_helper_slice_has_no_storage_scoring_queue_approval_or_pipeline_wiring_calls():
    source = Path("src/app/services.py").read_text()
    start = source.index("def build_guarded_approval_creation_observability_payload")
    end = source.index("def _artifact_row_by_name")
    snippet = source[start:end]

    forbidden_markers = [
        "create_approval_request(",
        "app_service_persist_agentic_approval_request(",
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


def test_ui_renders_audit_button_and_escapes_output():
    source = Path("src/app/static/agentic_review.js").read_text()
    start = source.index("function renderManualGuardedApprovalCreationObservabilitySection")
    end = source.index("function renderAgentTraceReadOnlyPanel")
    snippet = source[start:end]

    assert "Manual Guarded Approval Creation Audit" in snippet
    assert "View Approval Creation Audit" in snippet
    assert "data-manual-guarded-approval-creation-observability" in snippet
    assert "escapeHtml(contextId)" in snippet
    assert "escapeHtml(jobId)" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Audit summary\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Audit events\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Safety metadata\"" in snippet


def test_ui_click_posts_endpoint_and_existing_guarded_creation_action_still_exists():
    source = Path("src/app/static/agentic_review.js").read_text()

    assert source.count("/api/manual-guarded-approval-creation-observability") == 1
    assert "manual_guarded_approval_creation_observability_result" in source
    assert "renderManualGuardedApprovalCreationObservabilitySection(tracePayload)" in source
    assert source.count("/api/manual-guarded-approval-request-create") == 1
    assert "renderManualGuardedApprovalRequestCreateSection(tracePayload)" in source
