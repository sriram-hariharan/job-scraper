from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services


ENDPOINT = "/api/manual-execution-request-readback"


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _created_execution_request_payload() -> dict:
    return {
        "execution_request_creation_status": "created",
        "approval_request_id": "manual_guarded_approval_123",
        "queue_handoff_id": "manual_queue_handoff_abc123",
        "execution_request_id": "manual_execution_request_xyz123",
        "execution_request_created": True,
        "source_execution_request_packet_status": "packet_ready_for_human_review",
        "blocked_actions": [],
        "next_safe_step": "review_created_execution_request_before_any_future_execution",
        "context_id": "ctx-1",
        "job_id": "job-1",
    }


def _created_observability_payload() -> dict:
    return {
        "execution_request_observability_status": "observed_created",
        "source_execution_request_creation_status": "created",
        "approval_request_id": "manual_guarded_approval_123",
        "queue_handoff_id": "manual_queue_handoff_abc123",
        "execution_request_id": "manual_execution_request_xyz123",
        "execution_request_created": True,
        "execution_request_was_created": True,
        "execution_request_was_blocked": False,
        "blocked_actions": [],
        "next_safe_step": "review_created_execution_request_before_any_future_execution",
    }


def _blocked_execution_request_payload() -> dict:
    return {
        "execution_request_creation_status": "blocked_missing_execution_request_writer",
        "approval_request_id": "manual_guarded_approval_123",
        "queue_handoff_id": "manual_queue_handoff_abc123",
        "execution_request_id": "",
        "execution_request_created": False,
        "source_execution_request_packet_status": "packet_ready_for_human_review",
        "blocked_actions": ["execution_request_writer_unavailable"],
        "next_safe_step": "configure_existing_execution_request_writer_before_manual_creation",
    }


def _assert_readback_safety(payload: dict) -> None:
    safety = payload["safety_metadata"]
    assert payload["read_only"] is True
    assert payload["manual_surface"] is True
    assert safety["read_only"] is True
    assert safety["execution_request_readback_only"] is True
    assert safety["manual_only"] is True
    assert safety["did_create_execution_request"] is False
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


def test_helper_blocks_missing_execution_request_id():
    payload = services.build_execution_request_readback_payload()

    assert payload["execution_request_readback_status"] == "blocked_missing_execution_request_id"
    assert payload["execution_request_found"] is False
    assert "execution_request_id_missing" in payload["blocked_actions"]
    _assert_readback_safety(payload)


def test_helper_blocks_missing_source_evidence():
    payload = services.build_execution_request_readback_payload(
        execution_request_id="manual_execution_request_xyz123",
    )

    assert payload["execution_request_readback_status"] == "blocked_missing_source"
    assert payload["execution_request_found"] is False
    assert "execution_request_source_evidence_missing" in payload["blocked_actions"]
    _assert_readback_safety(payload)


def test_helper_returns_found_for_created_source_evidence_with_matching_id():
    payload = services.build_execution_request_readback_payload(
        execution_request_id="manual_execution_request_xyz123",
        guarded_execution_request_creation_payload=_created_execution_request_payload(),
        execution_request_creation_observability_payload=_created_observability_payload(),
    )

    assert payload["execution_request_readback_status"] == "found"
    assert payload["execution_request_found"] is True
    assert payload["execution_request_status"] == "created_control_artifact"
    assert payload["approval_request_id"] == "manual_guarded_approval_123"
    assert payload["queue_handoff_id"] == "manual_queue_handoff_abc123"
    assert payload["readback_summary"]["source_execution_request_creation_status"] == "created"
    assert [section["section_id"] for section in payload["detail_sections"]] == [
        "source_ids",
        "creation_source",
        "observability_source",
        "safety",
    ]
    _assert_readback_safety(payload)


def test_helper_returns_not_found_for_blocked_or_not_created_source_evidence():
    payload = services.build_execution_request_readback_payload(
        execution_request_id="manual_execution_request_xyz123",
        guarded_execution_request_creation_payload=_blocked_execution_request_payload(),
    )

    assert payload["execution_request_readback_status"] == "not_found"
    assert payload["execution_request_found"] is False
    assert payload["execution_request_status"] == "not_created"
    assert "execution_request_not_created" in payload["blocked_actions"]
    _assert_readback_safety(payload)


def test_helper_returns_not_found_when_execution_request_id_does_not_match_source():
    payload = services.build_execution_request_readback_payload(
        execution_request_id="manual_execution_request_other",
        guarded_execution_request_creation_payload=_created_execution_request_payload(),
    )

    assert payload["execution_request_readback_status"] == "not_found"
    assert payload["execution_request_status"] == "id_mismatch"
    assert "execution_request_id_not_matched_in_source" in payload["blocked_actions"]
    _assert_readback_safety(payload)


def test_api_route_exists_as_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"POST"}


def test_api_route_returns_readonly_readback(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "execution_request_id": "manual_execution_request_xyz123",
            "guarded_execution_request_creation_payload": _created_execution_request_payload(),
            "execution_request_creation_observability_payload": _created_observability_payload(),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["api_surface"] == "manual_execution_request_readback"
    assert payload["explicit_user_action"] is True
    assert payload["execution_request_readback_status"] == "found"
    assert payload["execution_request_found"] is True
    _assert_readback_safety(payload)


def test_api_route_slice_has_no_request_creation_queue_write_approval_mutation_or_execution_calls():
    source = Path("src/app/api.py").read_text()
    start = source.index("class ManualExecutionRequestReadbackRequest")
    class_end = source.index("@asynccontextmanager")
    route_start = source.index('@app.post("/api/manual-execution-request-readback")')
    route_end = source.index('@app.get("/api/agent-feedback")', route_start)
    snippet = source[start:class_end] + source[route_start:route_end]

    forbidden_markers = [
        "execution_request_writer(",
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


def test_service_helper_slice_has_no_request_creation_queue_write_approval_mutation_or_execution_calls():
    source = Path("src/app/services.py").read_text()
    start = source.index("def build_execution_request_readback_payload")
    end = source.index("def _agentic_workflow_summary_from_artifacts")
    snippet = source[start:end]

    forbidden_markers = [
        "execution_request_writer(",
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


def test_ui_renders_readback_button_and_escapes_output():
    source = Path("src/app/static/agentic_review.js").read_text()
    start = source.index("function renderManualExecutionRequestReadbackSection")
    end = source.index("function renderAgentTraceReadOnlyPanel")
    snippet = source[start:end]

    assert "Manual Execution Request Readback" in snippet
    assert "Read Execution Request" in snippet
    assert "data-manual-execution-request-readback" in snippet
    assert "escapeHtml(approvalRequestId)" in snippet
    assert "escapeHtml(queueHandoffId)" in snippet
    assert "escapeHtml(executionRequestId)" in snippet
    assert "escapeHtml(contextId)" in snippet
    assert "escapeHtml(jobId)" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Readback summary\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Detail sections\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Safety metadata\"" in snippet


def test_ui_click_posts_endpoint_and_existing_execution_request_observability_still_works():
    source = Path("src/app/static/agentic_review.js").read_text()

    assert source.count("/api/manual-execution-request-readback") == 1
    assert "manual_execution_request_readback_result" in source
    assert "renderManualExecutionRequestReadbackSection(tracePayload)" in source
    assert source.count("/api/manual-guarded-execution-request-observability") == 1
    assert "manual_guarded_execution_request_observability_result" in source
    assert "renderManualGuardedExecutionRequestObservabilitySection(tracePayload)" in source
