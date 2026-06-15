from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services


ENDPOINT = "/api/manual-approval-status-transition-observability"


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _updated_transition_payload() -> dict:
    return {
        "approval_status_transition_status": "updated",
        "approval_request_id": "manual_guarded_approval_123",
        "proposed_transition": "approve",
        "applied_transition": "approve",
        "previous_status": "pending",
        "new_status": "approved",
        "transition_applied": True,
        "blocked_actions": [],
        "source_transition_preview_status": "preview_ready",
        "next_safe_step": "review_updated_approval_request_status",
        "context_id": "ctx-1",
        "job_id": "job-1",
        "safety_metadata": {
            "did_update_approval_status": True,
            "did_mutate_queue": False,
            "did_execute_application": False,
            "did_submit_application": False,
        },
    }


def _blocked_transition_payload() -> dict:
    return {
        "approval_status_transition_status": "blocked_by_missing_confirmation",
        "approval_request_id": "manual_guarded_approval_123",
        "proposed_transition": "approve",
        "applied_transition": "",
        "previous_status": "pending",
        "new_status": "pending",
        "transition_applied": False,
        "blocked_actions": ["reviewer_confirmation_missing"],
        "source_transition_preview_status": "preview_ready",
        "next_safe_step": "collect_explicit_reviewer_confirmation",
        "safety_metadata": {
            "did_update_approval_status": False,
            "did_mutate_queue": False,
            "did_execute_application": False,
            "did_submit_application": False,
        },
    }


def _assert_observability_safety(payload: dict) -> None:
    safety = payload["safety_metadata"]
    assert payload["manual_surface"] is True
    assert payload["read_only"] is True
    assert safety["read_only"] is True
    assert safety["observability_only"] is True
    assert safety["transition_audit_only"] is True
    assert safety["manual_only"] is True
    assert safety["did_create_approval"] is False
    assert safety["did_mutate_approval"] is False
    assert safety["did_update_approval_status"] is False
    assert safety["did_mutate_queue"] is False
    assert safety["did_mutate_resume"] is False
    assert safety["did_mutate_scoring"] is False
    assert safety["did_change_ranking"] is False
    assert safety["did_execute_application"] is False
    assert safety["did_submit_application"] is False
    assert safety["pipeline_wiring_added"] is False
    assert safety["auto_apply_enabled"] is False
    assert safety["advisory_only"] is True


def test_helper_observes_updated_transition_without_mutation():
    payload = services.build_guarded_approval_status_transition_observability_payload(
        guarded_status_transition_payload=_updated_transition_payload(),
    )

    assert payload["transition_observability_status"] == "observed_updated"
    assert payload["source_transition_status"] == "updated"
    assert payload["approval_request_id"] == "manual_guarded_approval_123"
    assert payload["transition_was_applied"] is True
    assert payload["transition_was_blocked"] is False
    assert payload["previous_status"] == "pending"
    assert payload["new_status"] == "approved"
    assert payload["audit_summary"]["source_updated_approval_status"] is True
    assert payload["safety_findings"]["observability_updated_approval_status"] is False
    _assert_observability_safety(payload)


def test_helper_observes_blocked_transition_without_mutation():
    payload = services.build_guarded_approval_status_transition_observability_payload(
        guarded_status_transition_payload=_blocked_transition_payload(),
    )

    assert payload["transition_observability_status"] == "observed_blocked"
    assert payload["source_transition_status"] == "blocked_by_missing_confirmation"
    assert payload["transition_was_applied"] is False
    assert payload["transition_was_blocked"] is True
    assert "reviewer_confirmation_missing" in payload["blocked_actions"]
    _assert_observability_safety(payload)


def test_helper_missing_or_invalid_source_returns_safe_fallback():
    missing = services.build_guarded_approval_status_transition_observability_payload()
    invalid = services.build_guarded_approval_status_transition_observability_payload(
        guarded_status_transition_payload={"approval_status_transition_status": "surprising_state"},
    )

    assert missing["transition_observability_status"] == "observed_missing_source"
    assert "guarded_status_transition_payload_missing" in missing["blocked_actions"]
    assert invalid["transition_observability_status"] == "observed_invalid_source"
    assert "guarded_status_transition_status_unrecognized" in invalid["blocked_actions"]
    _assert_observability_safety(missing)
    _assert_observability_safety(invalid)


def test_api_route_exists_as_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"POST"}


def test_api_route_returns_readonly_observability_payload(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "guarded_status_transition_payload": _updated_transition_payload(),
            "approval_request_id": "manual_guarded_approval_123",
            "proposed_transition": "approve",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["api_surface"] == "manual_approval_status_transition_observability"
    assert payload["explicit_user_action"] is True
    assert payload["transition_observability_status"] == "observed_updated"
    assert payload["transition_was_applied"] is True
    _assert_observability_safety(payload)


def test_api_route_slice_has_no_status_update_storage_queue_or_execution_calls():
    source = Path("src/app/api.py").read_text()
    start = source.index("class ManualApprovalStatusTransitionObservabilityRequest")
    class_end = source.index("@asynccontextmanager")
    route_start = source.index('@app.post("/api/manual-approval-status-transition-observability")')
    route_end = source.index('@app.get("/api/agent-feedback")', route_start)
    snippet = source[start:class_end] + source[route_start:route_end]

    forbidden_markers = [
        "_agentic_approval_storage_connection",
        "record_approval_decision(",
        "approval_status=",
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


def test_service_helper_slice_has_no_status_update_storage_queue_or_execution_calls():
    source = Path("src/app/services.py").read_text()
    start = source.index("def build_guarded_approval_status_transition_observability_payload")
    end = source.index("def _agentic_workflow_summary_from_artifacts")
    snippet = source[start:end]

    forbidden_markers = [
        "record_approval_decision(",
        "get_approval_request(",
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
    ]
    for marker in forbidden_markers:
        assert marker not in snippet


def test_ui_renders_audit_button_and_escapes_output():
    source = Path("src/app/static/agentic_review.js").read_text()
    start = source.index("function renderManualApprovalStatusTransitionObservabilitySection")
    end = source.index("function renderAgentTraceReadOnlyPanel")
    snippet = source[start:end]

    assert "Manual Approval Status Transition Audit" in snippet
    assert "View Status Transition Audit" in snippet
    assert "data-manual-approval-status-transition-observability" in snippet
    assert "escapeHtml(approvalRequestId)" in snippet
    assert "escapeHtml(proposedTransition)" in snippet
    assert "escapeHtml(contextId)" in snippet
    assert "escapeHtml(jobId)" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Audit summary\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Safety metadata\"" in snippet


def test_ui_click_posts_endpoint_and_existing_guarded_transition_surface_still_works():
    source = Path("src/app/static/agentic_review.js").read_text()

    assert source.count("/api/manual-approval-status-transition-observability") == 1
    assert "manual_approval_status_transition_observability_result" in source
    assert "renderManualApprovalStatusTransitionObservabilitySection(tracePayload)" in source
    assert source.count("/api/manual-guarded-approval-status-transition") == 1
    assert "manual_guarded_approval_status_transition_result" in source
    assert "renderManualGuardedApprovalStatusTransitionSection(tracePayload)" in source
