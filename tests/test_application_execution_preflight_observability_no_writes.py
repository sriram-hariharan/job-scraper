from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services


ENDPOINT = "/api/manual-application-execution-preflight-observability"


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _ready_preflight_payload() -> dict:
    return {
        "application_execution_preflight_status": "preflight_ready_for_human_review",
        "execution_request_id": "manual_execution_request_xyz123",
        "approval_request_id": "manual_guarded_approval_123",
        "queue_handoff_id": "manual_queue_handoff_abc123",
        "preflight_ready_for_human_review": True,
        "passed_checks": ["execution_request_id_present", "simulation_ready"],
        "failed_checks": [],
        "blocked_actions": [],
        "next_safe_step": "perform_human_review_before_any_future_guarded_execution_action",
        "context_id": "ctx-1",
        "job_id": "job-1",
        "safety_metadata": {
            "did_execute_application": False,
            "did_submit_application": False,
            "did_create_execution_request": False,
            "did_update_execution_request_status": False,
        },
    }


def _blocked_preflight_payload() -> dict:
    return {
        "application_execution_preflight_status": "blocked_simulation_not_ready",
        "execution_request_id": "manual_execution_request_xyz123",
        "approval_request_id": "manual_guarded_approval_123",
        "queue_handoff_id": "manual_queue_handoff_abc123",
        "preflight_ready_for_human_review": False,
        "passed_checks": ["execution_request_id_present"],
        "failed_checks": ["simulation_ready"],
        "blocked_actions": ["application_execution_simulation_not_ready"],
        "next_safe_step": "resolve_application_execution_simulation_blockers",
        "safety_metadata": {
            "did_execute_application": False,
            "did_submit_application": False,
            "did_create_execution_request": False,
            "did_update_execution_request_status": False,
        },
    }


def _assert_observability_safety(payload: dict) -> None:
    safety = payload["safety_metadata"]
    assert payload["manual_surface"] is True
    assert payload["read_only"] is True
    assert safety["read_only"] is True
    assert safety["observability_only"] is True
    assert safety["application_execution_preflight_audit_only"] is True
    assert safety["manual_only"] is True
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


def test_helper_observes_ready_preflight_without_execution_or_submission():
    payload = services.build_application_execution_preflight_observability_payload(
        application_execution_preflight_payload=_ready_preflight_payload(),
    )

    assert payload["application_execution_preflight_observability_status"] == "observed_ready"
    assert payload["source_application_execution_preflight_status"] == "preflight_ready_for_human_review"
    assert payload["execution_request_id"] == "manual_execution_request_xyz123"
    assert payload["preflight_was_ready"] is True
    assert payload["preflight_was_blocked"] is False
    assert payload["preflight_ready_for_human_review"] is True
    assert payload["audit_summary"]["source_executed_application"] is False
    assert payload["safety_findings"]["observability_executed_application"] is False
    _assert_observability_safety(payload)


def test_helper_observes_blocked_preflight_without_execution_or_submission():
    payload = services.build_application_execution_preflight_observability_payload(
        application_execution_preflight_payload=_blocked_preflight_payload(),
    )

    assert payload["application_execution_preflight_observability_status"] == "observed_blocked"
    assert payload["source_application_execution_preflight_status"] == "blocked_simulation_not_ready"
    assert payload["preflight_was_ready"] is False
    assert payload["preflight_was_blocked"] is True
    assert "application_execution_simulation_not_ready" in payload["blocked_actions"]
    _assert_observability_safety(payload)


def test_helper_missing_or_invalid_source_returns_safe_fallback():
    missing = services.build_application_execution_preflight_observability_payload()
    invalid = services.build_application_execution_preflight_observability_payload(
        application_execution_preflight_payload={
            "application_execution_preflight_status": "surprising_state",
        },
    )

    assert missing["application_execution_preflight_observability_status"] == "observed_missing_source"
    assert "application_execution_preflight_payload_missing" in missing["blocked_actions"]
    assert invalid["application_execution_preflight_observability_status"] == "observed_invalid_source"
    assert "application_execution_preflight_status_unrecognized" in invalid["blocked_actions"]
    _assert_observability_safety(missing)
    _assert_observability_safety(invalid)


def test_api_route_exists_as_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"POST"}


def test_api_route_returns_readonly_observability_payload(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "application_execution_preflight_payload": _ready_preflight_payload(),
            "execution_request_id": "manual_execution_request_xyz123",
            "approval_request_id": "manual_guarded_approval_123",
            "queue_handoff_id": "manual_queue_handoff_abc123",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["api_surface"] == "manual_application_execution_preflight_observability"
    assert payload["explicit_user_action"] is True
    assert payload["application_execution_preflight_observability_status"] == "observed_ready"
    assert payload["preflight_was_ready"] is True
    _assert_observability_safety(payload)


def test_api_route_slice_has_no_creation_status_update_queue_write_approval_or_execution_calls():
    source = Path("src/app/api.py").read_text()
    start = source.index("class ManualApplicationExecutionPreflightObservabilityRequest")
    class_end = source.index("@asynccontextmanager")
    route_start = source.index('@app.post("/api/manual-application-execution-preflight-observability")')
    route_end = source.index('@app.get("/api/agent-feedback")', route_start)
    snippet = source[start:class_end] + source[route_start:route_end]

    forbidden_markers = [
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
    ]
    for marker in forbidden_markers:
        assert marker not in snippet


def test_service_helper_slice_has_no_creation_status_update_queue_write_approval_or_execution_calls():
    source = Path("src/app/services.py").read_text()
    start = source.index("def build_application_execution_preflight_observability_payload")
    end = source.index("def _agentic_workflow_summary_from_artifacts")
    snippet = source[start:end]

    forbidden_markers = [
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
    ]
    for marker in forbidden_markers:
        assert marker not in snippet


def test_ui_renders_audit_button_and_escapes_output():
    source = Path("src/app/static/agentic_review.js").read_text()
    start = source.index("function renderManualApplicationExecutionPreflightObservabilitySection")
    end = source.index("function renderAgentTraceReadOnlyPanel")
    snippet = source[start:end]

    assert "Manual Application Execution Preflight Audit" in snippet
    assert "View Application Execution Preflight Audit" in snippet
    assert "data-manual-application-execution-preflight-observability" in snippet
    assert "escapeHtml(approvalRequestId)" in snippet
    assert "escapeHtml(queueHandoffId)" in snippet
    assert "escapeHtml(executionRequestId)" in snippet
    assert "escapeHtml(contextId)" in snippet
    assert "escapeHtml(jobId)" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Audit summary\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Safety metadata\"" in snippet


def test_ui_click_posts_endpoint_and_existing_preflight_checklist_still_works():
    source = Path("src/app/static/agentic_review.js").read_text()

    assert source.count("/api/manual-application-execution-preflight-observability") == 1
    assert "manual_application_execution_preflight_observability_result" in source
    assert "renderManualApplicationExecutionPreflightObservabilitySection(tracePayload)" in source
    assert source.count("/api/manual-application-execution-preflight-checklist-dry-run") == 1
    assert "manual_application_execution_preflight_checklist_result" in source
    assert "renderManualApplicationExecutionPreflightChecklistSection(tracePayload)" in source
