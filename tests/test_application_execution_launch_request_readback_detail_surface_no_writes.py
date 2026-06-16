from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services


ENDPOINT = "/api/manual-application-execution-launch-request-readback"


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


def _created_launch_request_observability_payload(source: dict) -> dict:
    return services.build_guarded_application_execution_launch_request_observability_payload(
        guarded_application_execution_launch_request_payload=source,
    )


def _assert_readback_safety(payload: dict) -> None:
    safety = payload["safety_metadata"]
    assert payload["manual_surface"] is True
    assert payload["read_only"] is True
    assert safety["read_only"] is True
    assert safety["application_execution_launch_request_readback_only"] is True
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


def test_helper_blocks_missing_execution_launch_request_id():
    payload = services.build_application_execution_launch_request_readback_payload()

    assert payload["application_execution_launch_request_readback_status"] == (
        "blocked_missing_execution_launch_request_id"
    )
    assert payload["execution_launch_request_found"] is False
    assert "execution_launch_request_id" in payload["missing_requirements"]
    _assert_readback_safety(payload)


def test_helper_blocks_missing_source_evidence():
    payload = services.build_application_execution_launch_request_readback_payload(
        execution_launch_request_id="manual_execution_launch_request_missing",
    )

    assert payload["application_execution_launch_request_readback_status"] == "blocked_missing_source"
    assert payload["execution_launch_request_found"] is False
    assert "launch_request_source_evidence" in payload["missing_requirements"]
    assert "application_execution_launch_request_source_missing" in payload["blocked_actions"]
    _assert_readback_safety(payload)


def test_helper_returns_found_for_created_source_evidence_with_matching_id():
    source = _created_launch_request_payload()
    audit = _created_launch_request_observability_payload(source)
    original_source = deepcopy(source)
    original_audit = deepcopy(audit)

    payload = services.build_application_execution_launch_request_readback_payload(
        execution_launch_request_id=source["execution_launch_request_id"],
        guarded_application_execution_launch_request_payload=source,
        application_execution_launch_request_observability_payload=audit,
    )

    assert source == original_source
    assert audit == original_audit
    assert payload["application_execution_launch_request_readback_status"] == "found"
    assert payload["execution_launch_request_found"] is True
    assert payload["execution_launch_request_status"] == "created"
    assert payload["source_application_execution_launch_request_status"] == "created"
    assert payload["source_application_execution_launch_request_observability_status"] == (
        "observed_created"
    )
    assert payload["readback_summary"]["read_only_source_evidence_only"] is True
    _assert_readback_safety(payload)


def test_helper_returns_not_found_for_blocked_or_not_created_source_evidence():
    source = _blocked_launch_request_payload()
    audit = services.build_guarded_application_execution_launch_request_observability_payload(
        guarded_application_execution_launch_request_payload=source,
    )
    payload = services.build_application_execution_launch_request_readback_payload(
        execution_launch_request_id="manual_execution_launch_request_missing",
        guarded_application_execution_launch_request_payload=source,
        application_execution_launch_request_observability_payload=audit,
    )

    assert payload["application_execution_launch_request_readback_status"] == "not_found"
    assert payload["execution_launch_request_found"] is False
    assert payload["execution_launch_request_status"] == "not_found"
    assert "execution_launch_request_not_created" in payload["blocked_actions"]
    _assert_readback_safety(payload)


def test_api_route_exists_as_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"POST"}


def test_api_route_returns_readonly_launch_request_readback_payload(monkeypatch):
    source = _created_launch_request_payload()
    audit = _created_launch_request_observability_payload(source)
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "execution_launch_request_id": source["execution_launch_request_id"],
            "guarded_application_execution_launch_request_payload": source,
            "application_execution_launch_request_observability_payload": audit,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["api_surface"] == "manual_application_execution_launch_request_readback"
    assert payload["explicit_user_action"] is True
    assert payload["application_execution_launch_request_readback_status"] == "found"
    assert payload["execution_launch_request_found"] is True
    _assert_readback_safety(payload)


def test_api_route_slice_has_no_creation_status_update_queue_write_approval_or_execution_calls():
    source = Path("src/app/api.py").read_text()
    start = source.index("class ManualApplicationExecutionLaunchRequestReadbackRequest")
    class_end = source.index("@asynccontextmanager")
    route_start = source.index('@app.post("/api/manual-application-execution-launch-request-readback")')
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
    start = source.index("def build_application_execution_launch_request_readback_payload")
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


def test_ui_renders_readback_button_and_escapes_output():
    source = Path("src/app/static/agentic_review.js").read_text()
    start = source.index("function renderManualApplicationExecutionLaunchRequestReadbackSection")
    end = source.index("function renderAgentTraceReadOnlyPanel")
    snippet = source[start:end]

    assert "Manual Execution Launch Request Readback" in snippet
    assert "Read Execution Launch Request" in snippet
    assert "Execution launch request found" in snippet
    assert "data-manual-application-execution-launch-request-readback" in snippet
    assert "escapeHtml(approvalRequestId)" in snippet
    assert "escapeHtml(queueHandoffId)" in snippet
    assert "escapeHtml(executionRequestId)" in snippet
    assert "escapeHtml(executionLaunchRequestId)" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Readback summary\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Detail sections\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Safety metadata\"" in snippet


def test_ui_click_posts_endpoint_and_existing_launch_request_observability_still_works():
    source = Path("src/app/static/agentic_review.js").read_text()

    assert source.count("/api/manual-application-execution-launch-request-readback") == 1
    assert "manual_application_execution_launch_request_readback_result" in source
    assert "renderManualApplicationExecutionLaunchRequestReadbackSection(tracePayload)" in source
    assert source.count("/api/manual-guarded-application-execution-launch-request-observability") == 1
    assert "manual_guarded_application_execution_launch_request_observability_result" in source
    assert (
        "renderManualGuardedApplicationExecutionLaunchRequestObservabilitySection(tracePayload)"
        in source
    )
