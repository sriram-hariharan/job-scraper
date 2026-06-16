from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services


ENDPOINT = "/api/manual-guarded-application-execution-launch-request-observability"


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _ready_preflight() -> dict:
    return {
        "application_execution_preflight_status": "preflight_ready_for_human_review",
        "execution_request_id": "manual_execution_request_xyz123",
        "approval_request_id": "manual_guarded_approval_123",
        "queue_handoff_id": "manual_queue_handoff_abc123",
        "preflight_ready_for_human_review": True,
        "blocked_actions": [],
        "context_id": "ctx-1",
        "job_id": "job-1",
    }


def _ready_preflight_observability() -> dict:
    return {
        "application_execution_preflight_observability_status": "observed_ready",
        "source_application_execution_preflight_status": "preflight_ready_for_human_review",
        "execution_request_id": "manual_execution_request_xyz123",
        "approval_request_id": "manual_guarded_approval_123",
        "queue_handoff_id": "manual_queue_handoff_abc123",
        "preflight_was_ready": True,
        "preflight_was_blocked": False,
        "context_id": "ctx-1",
        "job_id": "job-1",
    }


def _created_launch_request_payload() -> dict:
    def fake_launch_request_writer(entry):
        return {
            "execution_launch_request_id": entry["execution_launch_request_id"],
            "persisted": True,
        }

    return services.build_guarded_application_execution_launch_request_payload(
        reviewer_confirmation=True,
        application_execution_preflight_payload=_ready_preflight(),
        application_execution_preflight_observability_payload=_ready_preflight_observability(),
        execution_launch_request_writer=fake_launch_request_writer,
    )


def _blocked_launch_request_payload() -> dict:
    return services.build_guarded_application_execution_launch_request_payload(
        reviewer_confirmation=True,
        application_execution_preflight_payload=_ready_preflight(),
        application_execution_preflight_observability_payload=_ready_preflight_observability(),
    )


def _assert_observability_safety(payload: dict) -> None:
    safety = payload["safety_metadata"]
    assert payload["manual_surface"] is True
    assert payload["read_only"] is True
    assert safety["read_only"] is True
    assert safety["observability_only"] is True
    assert safety["application_execution_launch_request_audit_only"] is True
    assert safety["manual_only"] is True
    assert safety["did_create_execution_launch_request"] is False
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


def test_helper_observes_created_launch_request_without_execution_or_submission():
    source = _created_launch_request_payload()
    original = deepcopy(source)

    payload = services.build_guarded_application_execution_launch_request_observability_payload(
        guarded_application_execution_launch_request_payload=source,
    )

    assert source == original
    assert payload["application_execution_launch_request_observability_status"] == "observed_created"
    assert payload["source_application_execution_launch_request_status"] == "created"
    assert payload["execution_launch_request_created"] is True
    assert payload["execution_launch_request_was_created"] is True
    assert payload["execution_launch_request_was_blocked"] is False
    assert payload["audit_summary"]["source_created_execution_launch_request"] is True
    assert payload["safety_findings"]["observability_created_execution_launch_request"] is False
    assert payload["safety_findings"]["observability_executed_application"] is False
    _assert_observability_safety(payload)


def test_helper_observes_blocked_launch_request_without_queue_write_or_status_update():
    source = _blocked_launch_request_payload()
    payload = services.build_guarded_application_execution_launch_request_observability_payload(
        guarded_application_execution_launch_request_payload=source,
    )

    assert payload["application_execution_launch_request_observability_status"] == "observed_blocked"
    assert payload["source_application_execution_launch_request_status"] == (
        "blocked_missing_execution_launch_request_writer"
    )
    assert payload["execution_launch_request_created"] is False
    assert payload["execution_launch_request_was_blocked"] is True
    assert "execution_launch_request_writer_unavailable" in payload["blocked_actions"]
    _assert_observability_safety(payload)


def test_helper_missing_or_invalid_source_returns_safe_fallback():
    missing = services.build_guarded_application_execution_launch_request_observability_payload()
    invalid = services.build_guarded_application_execution_launch_request_observability_payload(
        guarded_application_execution_launch_request_payload={
            "application_execution_launch_request_status": "surprising_state",
        },
    )

    assert missing["application_execution_launch_request_observability_status"] == (
        "observed_missing_source"
    )
    assert "guarded_application_execution_launch_request_payload_missing" in missing["blocked_actions"]
    assert invalid["application_execution_launch_request_observability_status"] == (
        "observed_invalid_source"
    )
    assert "application_execution_launch_request_status_unrecognized" in invalid["blocked_actions"]
    _assert_observability_safety(missing)
    _assert_observability_safety(invalid)


def test_api_route_exists_as_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"POST"}


def test_api_route_returns_readonly_launch_request_observability_payload(monkeypatch):
    source = _created_launch_request_payload()
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "guarded_application_execution_launch_request_payload": source,
            "execution_launch_request_id": source["execution_launch_request_id"],
            "execution_request_id": source["execution_request_id"],
            "approval_request_id": source["approval_request_id"],
            "queue_handoff_id": source["queue_handoff_id"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["api_surface"] == "manual_guarded_application_execution_launch_request_observability"
    assert payload["explicit_user_action"] is True
    assert payload["application_execution_launch_request_observability_status"] == "observed_created"
    assert payload["execution_launch_request_was_created"] is True
    _assert_observability_safety(payload)


def test_api_route_slice_has_no_creation_status_update_queue_write_approval_or_execution_calls():
    source = Path("src/app/api.py").read_text()
    start = source.index("class ManualGuardedApplicationExecutionLaunchRequestObservabilityRequest")
    class_end = source.index("@asynccontextmanager")
    route_start = source.index(
        '@app.post("/api/manual-guarded-application-execution-launch-request-observability")'
    )
    route_end = source.index('@app.get("/api/agent-feedback")', route_start)
    snippet = source[start:class_end] + source[route_start:route_end]

    forbidden_markers = [
        "execution_launch_request_writer(",
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
        "def build_guarded_application_execution_launch_request_observability_payload"
    )
    end = source.index("def _agentic_workflow_summary_from_artifacts")
    snippet = source[start:end]

    forbidden_markers = [
        "execution_launch_request_writer(",
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
        "function renderManualGuardedApplicationExecutionLaunchRequestObservabilitySection"
    )
    end = source.index("function renderAgentTraceReadOnlyPanel")
    snippet = source[start:end]

    assert "Manual Execution Launch Request Audit" in snippet
    assert "View Execution Launch Request Audit" in snippet
    assert "data-manual-guarded-application-execution-launch-request-observability" in snippet
    assert "escapeHtml(approvalRequestId)" in snippet
    assert "escapeHtml(queueHandoffId)" in snippet
    assert "escapeHtml(executionRequestId)" in snippet
    assert "escapeHtml(executionLaunchRequestId)" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Audit summary\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Audit events\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Safety metadata\"" in snippet


def test_ui_click_posts_endpoint_and_existing_launch_request_manual_action_still_works():
    source = Path("src/app/static/agentic_review.js").read_text()

    assert source.count("/api/manual-guarded-application-execution-launch-request-observability") == 1
    assert "manual_guarded_application_execution_launch_request_observability_result" in source
    assert (
        "renderManualGuardedApplicationExecutionLaunchRequestObservabilitySection(tracePayload)"
        in source
    )
    assert source.count("/api/manual-guarded-application-execution-launch-request-create") == 1
    assert "manual_guarded_application_execution_launch_request_create_result" in source
    assert "renderManualGuardedApplicationExecutionLaunchRequestCreateSection(tracePayload)" in source
