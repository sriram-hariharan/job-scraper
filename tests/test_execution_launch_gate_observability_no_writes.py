from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services


ENDPOINT = "/api/manual-execution-launch-gate-observability"


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _ready_launch_gate_payload() -> dict:
    return {
        "execution_launch_gate_status": "ready_for_future_manual_execution",
        "approval_request_id": "manual_guarded_approval_123",
        "queue_handoff_id": "manual_queue_handoff_abc123",
        "execution_launch_allowed_later": True,
        "ready_for_future_manual_execution": True,
        "blocked_actions": [],
        "next_safe_step": "collect_explicit_future_manual_execution_confirmation",
        "context_id": "ctx-1",
        "job_id": "job-1",
        "safety_metadata": {
            "did_execute_application": False,
            "did_submit_application": False,
            "did_mutate_queue": False,
            "did_write_queue": False,
        },
    }


def _blocked_launch_gate_payload() -> dict:
    return {
        "execution_launch_gate_status": "blocked_execution_not_ready",
        "approval_request_id": "manual_guarded_approval_123",
        "queue_handoff_id": "manual_queue_handoff_abc123",
        "execution_launch_allowed_later": False,
        "ready_for_future_manual_execution": False,
        "blocked_actions": ["execution_readiness_not_ready"],
        "next_safe_step": "resolve_execution_readiness_blockers_before_launch_gate",
        "safety_metadata": {
            "did_execute_application": False,
            "did_submit_application": False,
            "did_mutate_queue": False,
            "did_write_queue": False,
        },
    }


def _assert_observability_safety(payload: dict) -> None:
    safety = payload["safety_metadata"]
    assert payload["manual_surface"] is True
    assert payload["read_only"] is True
    assert safety["read_only"] is True
    assert safety["observability_only"] is True
    assert safety["execution_launch_gate_audit_only"] is True
    assert safety["manual_only"] is True
    assert safety["did_create_approval"] is False
    assert safety["did_mutate_approval"] is False
    assert safety["did_update_approval_status"] is False
    assert safety["did_mutate_queue"] is False
    assert safety["did_write_queue"] is False
    assert safety["did_mutate_resume"] is False
    assert safety["did_mutate_scoring"] is False
    assert safety["did_change_ranking"] is False
    assert safety["did_execute_application"] is False
    assert safety["did_submit_application"] is False
    assert safety["pipeline_wiring_added"] is False
    assert safety["auto_apply_enabled"] is False
    assert safety["advisory_only"] is True


def test_helper_observes_ready_launch_gate_without_mutation():
    payload = services.build_execution_launch_gate_observability_payload(
        execution_launch_gate_payload=_ready_launch_gate_payload(),
    )

    assert payload["execution_launch_gate_observability_status"] == "observed_ready"
    assert payload["source_execution_launch_gate_status"] == "ready_for_future_manual_execution"
    assert payload["approval_request_id"] == "manual_guarded_approval_123"
    assert payload["queue_handoff_id"] == "manual_queue_handoff_abc123"
    assert payload["future_manual_execution_allowed"] is True
    assert payload["execution_launch_was_blocked"] is False
    assert payload["execution_launch_was_allowed_later"] is True
    assert payload["audit_summary"]["source_executed_application"] is False
    _assert_observability_safety(payload)


def test_helper_observes_blocked_launch_gate_without_mutation():
    payload = services.build_execution_launch_gate_observability_payload(
        execution_launch_gate_payload=_blocked_launch_gate_payload(),
    )

    assert payload["execution_launch_gate_observability_status"] == "observed_blocked"
    assert payload["source_execution_launch_gate_status"] == "blocked_execution_not_ready"
    assert payload["future_manual_execution_allowed"] is False
    assert payload["execution_launch_was_blocked"] is True
    assert "execution_readiness_not_ready" in payload["blocked_actions"]
    _assert_observability_safety(payload)


def test_helper_missing_or_invalid_source_returns_safe_fallback():
    missing = services.build_execution_launch_gate_observability_payload()
    invalid = services.build_execution_launch_gate_observability_payload(
        execution_launch_gate_payload={"execution_launch_gate_status": "surprising_state"},
    )

    assert missing["execution_launch_gate_observability_status"] == "observed_missing_source"
    assert "execution_launch_gate_payload_missing" in missing["blocked_actions"]
    assert invalid["execution_launch_gate_observability_status"] == "observed_invalid_source"
    assert "execution_launch_gate_status_unrecognized" in invalid["blocked_actions"]
    _assert_observability_safety(missing)
    _assert_observability_safety(invalid)


def test_api_route_exists_as_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"POST"}


def test_api_route_returns_readonly_observability_payload(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "execution_launch_gate_payload": _ready_launch_gate_payload(),
            "approval_request_id": "manual_guarded_approval_123",
            "queue_handoff_id": "manual_queue_handoff_abc123",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["api_surface"] == "manual_execution_launch_gate_observability"
    assert payload["explicit_user_action"] is True
    assert payload["execution_launch_gate_observability_status"] == "observed_ready"
    assert payload["future_manual_execution_allowed"] is True
    _assert_observability_safety(payload)


def test_api_route_slice_has_no_execution_submission_queue_write_or_mutation_calls():
    source = Path("src/app/api.py").read_text()
    start = source.index("class ManualExecutionLaunchGateObservabilityRequest")
    class_end = source.index("@asynccontextmanager")
    route_start = source.index('@app.post("/api/manual-execution-launch-gate-observability")')
    route_end = source.index('@app.get("/api/agent-feedback")', route_start)
    snippet = source[start:class_end] + source[route_start:route_end]

    forbidden_markers = [
        "execute_application(",
        "submit_application(",
        "application_execution_queue",
        "_load_csv_rows",
        ".write(",
        "write_text",
        "record_approval_decision(",
        "approval_status=",
        "create_approval_request(",
        "score_resume_job_match",
        "ranking_update",
        "ranking_mutation",
        "workflow_runner",
        "insert_operator_decision",
    ]
    for marker in forbidden_markers:
        assert marker not in snippet


def test_service_helper_slice_has_no_execution_submission_queue_write_or_mutation_calls():
    source = Path("src/app/services.py").read_text()
    start = source.index("def build_execution_launch_gate_observability_payload")
    end = source.index("def _agentic_workflow_summary_from_artifacts")
    snippet = source[start:end]

    forbidden_markers = [
        "execute_application(",
        "submit_application(",
        "application_execution_queue",
        "_load_csv_rows",
        ".write(",
        "write_text",
        "record_approval_decision(",
        "get_approval_request(",
        "create_approval_request(",
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
    start = source.index("function renderManualExecutionLaunchGateObservabilitySection")
    end = source.index("function renderAgentTraceReadOnlyPanel")
    snippet = source[start:end]

    assert "Manual Execution Launch Gate Audit" in snippet
    assert "View Execution Launch Gate Audit" in snippet
    assert "data-manual-execution-launch-gate-observability" in snippet
    assert "escapeHtml(approvalRequestId)" in snippet
    assert "escapeHtml(queueHandoffId)" in snippet
    assert "escapeHtml(contextId)" in snippet
    assert "escapeHtml(jobId)" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Audit summary\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Safety metadata\"" in snippet


def test_ui_click_posts_endpoint_and_existing_execution_launch_gate_preview_still_works():
    source = Path("src/app/static/agentic_review.js").read_text()

    assert source.count("/api/manual-execution-launch-gate-observability") == 1
    assert "manual_execution_launch_gate_observability_result" in source
    assert "renderManualExecutionLaunchGateObservabilitySection(tracePayload)" in source
    assert source.count("/api/manual-execution-launch-gate-preview-dry-run") == 1
    assert "manual_execution_launch_gate_preview_result" in source
    assert "renderManualExecutionLaunchGatePreviewSection(tracePayload)" in source
