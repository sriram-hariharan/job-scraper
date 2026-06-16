from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services


ENDPOINT = "/api/manual-execution-request-status-transition-preview-dry-run"


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _found_readback(status: str = "created_control_artifact") -> dict:
    return {
        "execution_request_readback_status": "found",
        "execution_request_id": "manual_execution_request_xyz123",
        "approval_request_id": "manual_guarded_approval_123",
        "queue_handoff_id": "manual_queue_handoff_abc123",
        "execution_request_found": True,
        "execution_request_status": status,
    }


def _assert_transition_preview_safety(payload: dict) -> None:
    safety = payload["safety_metadata"]
    assert payload["read_only"] is True
    assert payload["manual_surface"] is True
    assert safety["dry_run_only"] is True
    assert safety["execution_request_status_transition_preview_only"] is True
    assert safety["manual_only"] is True
    assert safety["read_only"] is True
    assert safety["human_confirmation_required"] is True
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


def test_helper_blocks_missing_execution_request_id():
    payload = services.build_execution_request_status_transition_preview_payload(
        requested_transition="ready_for_manual_execution",
    )

    assert payload["execution_request_status_transition_preview_status"] == "blocked_missing_execution_request_id"
    assert payload["transition_allowed_later"] is False
    assert "execution_request_id" in payload["missing_requirements"]
    _assert_transition_preview_safety(payload)


def test_helper_blocks_missing_requested_transition():
    payload = services.build_execution_request_status_transition_preview_payload(
        execution_request_id="manual_execution_request_xyz123",
        execution_request_readback_payload=_found_readback(),
    )

    assert payload["execution_request_status_transition_preview_status"] == "blocked_missing_requested_transition"
    assert "requested_transition_missing" in payload["blocked_actions"]
    _assert_transition_preview_safety(payload)


def test_helper_blocks_invalid_requested_transition():
    payload = services.build_execution_request_status_transition_preview_payload(
        execution_request_id="manual_execution_request_xyz123",
        requested_transition="launch_now",
        execution_request_readback_payload=_found_readback(),
    )

    assert payload["execution_request_status_transition_preview_status"] == "blocked_invalid_requested_transition"
    assert "requested_transition_invalid" in payload["blocked_actions"]
    _assert_transition_preview_safety(payload)


def test_helper_blocks_missing_or_invalid_readback():
    missing = services.build_execution_request_status_transition_preview_payload(
        execution_request_id="manual_execution_request_xyz123",
        requested_transition="ready_for_manual_execution",
    )
    invalid = services.build_execution_request_status_transition_preview_payload(
        execution_request_id="manual_execution_request_xyz123",
        requested_transition="ready_for_manual_execution",
        execution_request_readback_payload={"execution_request_readback_status": "insufficient_information"},
    )

    assert missing["execution_request_status_transition_preview_status"] == "blocked_missing_readback"
    assert "execution_request_readback_missing" in missing["blocked_actions"]
    assert invalid["execution_request_status_transition_preview_status"] == "blocked_execution_request_not_found"
    assert "execution_request_not_found" in invalid["blocked_actions"]
    _assert_transition_preview_safety(missing)
    _assert_transition_preview_safety(invalid)


def test_helper_blocks_not_found_readback():
    payload = services.build_execution_request_status_transition_preview_payload(
        execution_request_id="manual_execution_request_xyz123",
        requested_transition="cancelled",
        execution_request_readback_payload={
            "execution_request_readback_status": "not_found",
            "execution_request_id": "manual_execution_request_xyz123",
            "execution_request_found": False,
        },
    )

    assert payload["execution_request_status_transition_preview_status"] == "blocked_execution_request_not_found"
    assert "execution_request_not_found" in payload["blocked_actions"]
    _assert_transition_preview_safety(payload)


def test_helper_blocks_missing_or_invalid_current_status():
    for status in ["", "missing", "unknown", "not_created", "id_mismatch"]:
        payload = services.build_execution_request_status_transition_preview_payload(
            execution_request_id="manual_execution_request_xyz123",
            requested_transition="ready_for_manual_execution",
            execution_request_readback_payload=_found_readback(status),
        )

        assert payload["execution_request_status_transition_preview_status"] == "blocked_invalid_current_status"
        assert "previous_execution_request_status_invalid" in payload["blocked_actions"]
        _assert_transition_preview_safety(payload)


def test_helper_returns_ready_for_future_status_transition_for_valid_transitions():
    expected_status = {
        "ready_for_manual_execution": "ready_for_manual_execution",
        "needs_changes": "needs_changes",
        "cancelled": "cancelled",
        "keep_pending_review": "pending_review",
    }

    for transition, expected_target in expected_status.items():
        payload = services.build_execution_request_status_transition_preview_payload(
            requested_transition=transition,
            execution_request_readback_payload=_found_readback(),
        )

        assert payload["execution_request_status_transition_preview_status"] == "ready_for_future_status_transition"
        assert payload["execution_request_id"] == "manual_execution_request_xyz123"
        assert payload["requested_transition"] == transition
        assert payload["previous_execution_request_status"] == "created_control_artifact"
        assert payload["proposed_execution_request_status"] == expected_target
        assert payload["transition_allowed_later"] is True
        assert payload["transition_preview_only"] is True
        assert payload["required_human_confirmation"] is True
        _assert_transition_preview_safety(payload)


def test_api_route_exists_as_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"POST"}


def test_api_route_returns_dry_run_readonly_preview(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "requested_transition": "needs_changes",
            "execution_request_readback_payload": _found_readback(),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["api_surface"] == "manual_execution_request_status_transition_preview_dry_run"
    assert payload["explicit_user_action"] is True
    assert payload["execution_request_status_transition_preview_status"] == "ready_for_future_status_transition"
    assert payload["proposed_execution_request_status"] == "needs_changes"
    _assert_transition_preview_safety(payload)


def test_api_route_slice_has_no_status_update_storage_or_execution_calls():
    source = Path("src/app/api.py").read_text()
    start = source.index("class ManualExecutionRequestStatusTransitionPreviewRequest")
    class_end = source.index("@asynccontextmanager")
    route_start = source.index('@app.post("/api/manual-execution-request-status-transition-preview-dry-run")')
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


def test_service_helper_slice_has_no_status_update_storage_or_execution_calls():
    source = Path("src/app/services.py").read_text()
    start = source.index("def build_execution_request_status_transition_preview_payload")
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


def test_ui_renders_transition_select_button_and_escapes_output():
    source = Path("src/app/static/agentic_review.js").read_text()
    start = source.index("function renderManualExecutionRequestStatusTransitionPreviewSection")
    end = source.index("function renderAgentTraceReadOnlyPanel")
    snippet = source[start:end]

    assert "Manual Execution Request Status Transition Preview" in snippet
    assert "Preview Execution Request Status Transition" in snippet
    assert "data-manual-execution-request-status-transition-preview-select" in snippet
    assert "data-manual-execution-request-status-transition-preview" in snippet
    assert "escapeHtml(approvalRequestId)" in snippet
    assert "escapeHtml(queueHandoffId)" in snippet
    assert "escapeHtml(executionRequestId)" in snippet
    assert "escapeHtml(contextId)" in snippet
    assert "escapeHtml(jobId)" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Source readback status\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Safety metadata\"" in snippet


def test_ui_click_posts_endpoint_and_existing_execution_request_readback_still_works():
    source = Path("src/app/static/agentic_review.js").read_text()

    assert source.count("/api/manual-execution-request-status-transition-preview-dry-run") == 1
    assert "manual_execution_request_status_transition_preview_result" in source
    assert "renderManualExecutionRequestStatusTransitionPreviewSection(tracePayload)" in source
    assert source.count("/api/manual-execution-request-readback") == 1
    assert "manual_execution_request_readback_result" in source
    assert "renderManualExecutionRequestReadbackSection(tracePayload)" in source
