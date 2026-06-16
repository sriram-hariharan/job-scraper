from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services


ENDPOINT = "/api/manual-guarded-execution-launch-request-status-transition-observability"


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _ready_preview() -> dict:
    return {
        "execution_launch_request_status_transition_preview_status": (
            "ready_for_future_status_transition"
        ),
        "execution_launch_request_id": "manual_execution_launch_request_xyz123",
        "execution_request_id": "manual_execution_request_xyz123",
        "approval_request_id": "manual_guarded_approval_123",
        "queue_handoff_id": "manual_queue_handoff_abc123",
        "requested_transition": "ready_for_manual_execution",
        "current_execution_launch_request_status": "created",
        "proposed_execution_launch_request_status": "ready_for_manual_execution",
        "transition_allowed": True,
        "context_id": "ctx-1",
        "job_id": "job-1",
    }


def _found_readback() -> dict:
    return {
        "application_execution_launch_request_readback_status": "found",
        "execution_launch_request_id": "manual_execution_launch_request_xyz123",
        "execution_request_id": "manual_execution_request_xyz123",
        "approval_request_id": "manual_guarded_approval_123",
        "queue_handoff_id": "manual_queue_handoff_abc123",
        "execution_launch_request_found": True,
        "execution_launch_request_status": "created",
    }


def _updated_transition_payload() -> dict:
    def fake_status_writer(entry):
        return {
            "execution_launch_request_id": entry["execution_launch_request_id"],
            "new_execution_launch_request_status": entry["new_execution_launch_request_status"],
            "persisted": True,
        }

    return services.build_guarded_execution_launch_request_status_transition_payload(
        reviewer_confirmation=True,
        execution_launch_request_status_transition_preview_payload=_ready_preview(),
        application_execution_launch_request_readback_payload=_found_readback(),
        execution_launch_request_status_writer=fake_status_writer,
    )


def _blocked_transition_payload() -> dict:
    return services.build_guarded_execution_launch_request_status_transition_payload(
        reviewer_confirmation=True,
        execution_launch_request_status_transition_preview_payload=_ready_preview(),
        application_execution_launch_request_readback_payload=_found_readback(),
    )


def _assert_observability_safety(payload: dict) -> None:
    safety = payload["safety_metadata"]
    assert payload["manual_surface"] is True
    assert payload["read_only"] is True
    assert safety["read_only"] is True
    assert safety["observability_only"] is True
    assert safety["execution_launch_request_status_transition_audit_only"] is True
    assert safety["manual_only"] is True
    assert safety["did_create_execution_launch_request"] is False
    assert safety["did_update_execution_launch_request_status"] is False
    assert safety["did_create_execution_request"] is False
    assert safety["did_update_execution_request_status"] is False
    assert safety["did_create_approval"] is False
    assert safety["did_mutate_approval"] is False
    assert safety["did_update_approval_status"] is False
    assert safety["did_mutate_queue"] is False
    assert safety["did_write_queue"] is False
    assert safety["did_execute_application"] is False
    assert safety["did_submit_application"] is False
    assert safety["did_mutate_resume"] is False
    assert safety["did_mutate_scoring"] is False
    assert safety["did_change_ranking"] is False
    assert safety["pipeline_wiring_added"] is False
    assert safety["auto_apply_enabled"] is False
    assert safety["advisory_only"] is True


def test_helper_observes_updated_transition_without_status_update_or_execution():
    payload = services.build_guarded_execution_launch_request_status_transition_observability_payload(
        guarded_execution_launch_request_status_transition_payload=_updated_transition_payload(),
    )

    assert payload["execution_launch_request_status_transition_observability_status"] == (
        "observed_updated"
    )
    assert payload["source_execution_launch_request_status_transition_status"] == "updated"
    assert payload["execution_launch_request_status_updated"] is True
    assert payload["execution_launch_request_status_transition_was_applied"] is True
    assert payload["execution_launch_request_status_transition_was_blocked"] is False
    assert payload["audit_summary"]["source_updated_execution_launch_request_status"] is True
    assert payload["safety_findings"]["observability_updated_execution_launch_request_status"] is False
    _assert_observability_safety(payload)


def test_helper_observes_blocked_transition_without_queue_write_or_status_update():
    payload = services.build_guarded_execution_launch_request_status_transition_observability_payload(
        guarded_execution_launch_request_status_transition_payload=_blocked_transition_payload(),
    )

    assert payload["execution_launch_request_status_transition_observability_status"] == (
        "observed_blocked"
    )
    assert payload["source_execution_launch_request_status_transition_status"] == (
        "blocked_missing_execution_launch_request_status_writer"
    )
    assert payload["execution_launch_request_status_transition_was_applied"] is False
    assert payload["execution_launch_request_status_transition_was_blocked"] is True
    assert "execution_launch_request_status_writer_unavailable" in payload["blocked_actions"]
    _assert_observability_safety(payload)


def test_helper_missing_or_invalid_source_returns_safe_fallback():
    missing = services.build_guarded_execution_launch_request_status_transition_observability_payload()
    invalid = services.build_guarded_execution_launch_request_status_transition_observability_payload(
        guarded_execution_launch_request_status_transition_payload={
            "execution_launch_request_status_transition_status": "surprising_state",
        },
    )

    assert missing["execution_launch_request_status_transition_observability_status"] == (
        "observed_missing_source"
    )
    assert "guarded_execution_launch_request_status_transition_payload_missing" in missing["blocked_actions"]
    assert invalid["execution_launch_request_status_transition_observability_status"] == (
        "observed_invalid_source"
    )
    assert (
        "guarded_execution_launch_request_status_transition_status_unrecognized"
        in invalid["blocked_actions"]
    )
    _assert_observability_safety(missing)
    _assert_observability_safety(invalid)


def test_api_route_exists_as_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"POST"}


def test_api_route_returns_readonly_transition_observability_payload(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "guarded_execution_launch_request_status_transition_payload": (
                _updated_transition_payload()
            ),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["api_surface"] == (
        "manual_guarded_execution_launch_request_status_transition_observability"
    )
    assert payload["explicit_user_action"] is True
    assert payload["execution_launch_request_status_transition_observability_status"] == (
        "observed_updated"
    )
    _assert_observability_safety(payload)


def test_api_route_slice_has_no_creation_status_update_queue_write_approval_or_execution_calls():
    source = Path("src/app/api.py").read_text()
    start = source.index("class ManualGuardedExecutionLaunchRequestStatusTransitionObservabilityRequest")
    class_end = source.index("@asynccontextmanager")
    route_start = source.index(
        '@app.post("/api/manual-guarded-execution-launch-request-status-transition-observability")'
    )
    route_end = source.index('@app.get("/api/agent-feedback")', route_start)
    snippet = source[start:class_end] + source[route_start:route_end]

    forbidden_markers = [
        "execution_launch_request_writer(",
        "execution_launch_request_status_writer(",
        "execution_request_writer(",
        "execution_request_status_writer(",
        "record_approval_decision(",
        "approval_status=",
        "create_approval_request(",
        "application_execution_queue",
        "_load_csv_rows",
        ".write(",
        "write_text",
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


def test_service_helper_slice_has_no_creation_status_update_queue_write_approval_or_execution_calls():
    source = Path("src/app/services.py").read_text()
    start = source.index(
        "def build_guarded_execution_launch_request_status_transition_observability_payload"
    )
    end = source.index("def _agentic_workflow_summary_from_artifacts")
    snippet = source[start:end]

    forbidden_markers = [
        "execution_launch_request_writer(",
        "execution_launch_request_status_writer(",
        "execution_request_writer(",
        "execution_request_status_writer(",
        "record_approval_decision(",
        "get_approval_request(",
        "create_approval_request(",
        "application_execution_queue",
        "_load_csv_rows",
        ".write(",
        "write_text",
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


def test_ui_renders_audit_button_and_escapes_output():
    source = Path("src/app/static/agentic_review.js").read_text()
    start = source.index(
        "function renderManualGuardedExecutionLaunchRequestStatusTransitionObservabilitySection"
    )
    end = source.index("function renderAgentTraceReadOnlyPanel")
    snippet = source[start:end]

    assert "Manual Execution Launch Status Audit" in snippet
    assert "View Execution Launch Status Audit" in snippet
    assert "data-manual-guarded-execution-launch-request-status-transition-observability" in snippet
    assert "escapeHtml(approvalRequestId)" in snippet
    assert "escapeHtml(queueHandoffId)" in snippet
    assert "escapeHtml(executionRequestId)" in snippet
    assert "escapeHtml(executionLaunchRequestId)" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Audit summary\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Audit events\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Safety metadata\"" in snippet


def test_ui_click_posts_endpoint_and_existing_guarded_transition_still_works():
    source = Path("src/app/static/agentic_review.js").read_text()

    assert (
        source.count(
            "/api/manual-guarded-execution-launch-request-status-transition-observability"
        )
        == 1
    )
    assert "manual_guarded_execution_launch_request_status_transition_observability_result" in source
    assert (
        "renderManualGuardedExecutionLaunchRequestStatusTransitionObservabilitySection(tracePayload)"
        in source
    )
    assert source.count('"/api/manual-guarded-execution-launch-request-status-transition"') == 1
    assert "manual_guarded_execution_launch_request_status_transition_result" in source
    assert "renderManualGuardedExecutionLaunchRequestStatusTransitionSection(tracePayload)" in source
