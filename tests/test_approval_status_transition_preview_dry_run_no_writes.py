from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services


ENDPOINT = "/api/manual-approval-status-transition-preview-dry-run"


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _found_readback() -> dict:
    return {
        "readback_status": "found",
        "approval_request_id": "manual_guarded_approval_123",
        "approval_request_found": True,
        "approval_request_summary": {"approval_status": "pending"},
        "approval_request_fields": {"approval_status": "pending"},
    }


def _assert_transition_safety(payload: dict) -> None:
    safety = payload["safety_metadata"]
    assert payload["read_only"] is True
    assert payload["manual_surface"] is True
    assert safety["dry_run_only"] is True
    assert safety["transition_preview_only"] is True
    assert safety["approval_request_readback_only"] is False
    assert safety["manual_only"] is True
    assert safety["read_only"] is True
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


def test_helper_blocks_missing_approval_request_id():
    payload = services.build_approval_status_transition_preview_payload(
        proposed_transition="approve",
        approval_request_readback_payload={},
    )

    assert payload["transition_preview_status"] == "blocked_missing_approval_request_id"
    assert payload["transition_allowed_later"] is False
    assert "approval_request_id" in payload["missing_requirements"]
    _assert_transition_safety(payload)


def test_helper_blocks_invalid_proposed_transition():
    payload = services.build_approval_status_transition_preview_payload(
        approval_request_id="manual_guarded_approval_123",
        proposed_transition="ship_it",
        approval_request_readback_payload=_found_readback(),
    )

    assert payload["transition_preview_status"] == "blocked_invalid_transition"
    assert payload["transition_allowed_later"] is False
    assert "proposed_transition_invalid" in payload["blocked_actions"]
    _assert_transition_safety(payload)


def test_helper_blocks_not_found_readback():
    payload = services.build_approval_status_transition_preview_payload(
        approval_request_id="manual_guarded_approval_123",
        proposed_transition="reject",
        approval_request_readback_payload={
            "readback_status": "not_found",
            "approval_request_id": "manual_guarded_approval_123",
            "approval_request_found": False,
        },
    )

    assert payload["transition_preview_status"] == "blocked_not_found"
    assert payload["transition_allowed_later"] is False
    assert "approval_request_not_found" in payload["blocked_actions"]
    _assert_transition_safety(payload)


def test_helper_returns_preview_ready_for_supported_transitions():
    expected_status = {
        "approve": "approved",
        "reject": "denied",
        "needs_changes": "pending",
    }

    for transition, expected_target in expected_status.items():
        payload = services.build_approval_status_transition_preview_payload(
            proposed_transition=transition,
            approval_request_readback_payload=_found_readback(),
        )

        assert payload["transition_preview_status"] == "preview_ready"
        assert payload["approval_request_id"] == "manual_guarded_approval_123"
        assert payload["proposed_transition"] == transition
        assert payload["transition_allowed_later"] is True
        assert payload["would_change_status_to"] == expected_target
        assert payload["required_reviewer_confirmation"] is True
        _assert_transition_safety(payload)


def test_api_route_exists_as_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"POST"}


def test_api_route_returns_dry_run_readonly_preview(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "proposed_transition": "needs_changes",
            "approval_request_readback_payload": _found_readback(),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["api_surface"] == "manual_approval_status_transition_preview_dry_run"
    assert payload["explicit_user_action"] is True
    assert payload["transition_preview_status"] == "preview_ready"
    assert payload["would_change_status_to"] == "pending"
    _assert_transition_safety(payload)


def test_api_route_slice_has_no_status_update_storage_or_execution_calls():
    source = Path("src/app/api.py").read_text()
    start = source.index("class ManualApprovalStatusTransitionPreviewRequest")
    class_end = source.index("@asynccontextmanager")
    route_start = source.index('@app.post("/api/manual-approval-status-transition-preview-dry-run")')
    route_end = source.index('@app.get("/api/agent-feedback/export")')
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


def test_service_helper_slice_has_no_status_update_storage_or_execution_calls():
    source = Path("src/app/services.py").read_text()
    start = source.index("def build_approval_status_transition_preview_payload")
    end = source.index("def _artifact_row_by_name")
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


def test_ui_renders_transition_select_button_and_escapes_output():
    source = Path("src/app/static/agentic_review.js").read_text()
    start = source.index("function renderManualApprovalStatusTransitionPreviewSection")
    end = source.index("function renderAgentTraceReadOnlyPanel")
    snippet = source[start:end]

    assert "Manual Approval Status Transition Preview" in snippet
    assert "Preview Approval Status Transition" in snippet
    assert "data-manual-approval-status-transition-preview-select" in snippet
    assert "data-manual-approval-status-transition-preview" in snippet
    assert "escapeHtml(approvalRequestId)" in snippet
    assert "escapeHtml(contextId)" in snippet
    assert "escapeHtml(jobId)" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Transition label\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Safety metadata\"" in snippet


def test_ui_click_posts_endpoint_and_existing_readback_surface_still_exists():
    source = Path("src/app/static/agentic_review.js").read_text()

    assert source.count("/api/manual-approval-status-transition-preview-dry-run") == 1
    assert "manual_approval_status_transition_preview_result" in source
    assert "renderManualApprovalStatusTransitionPreviewSection(tracePayload)" in source
    assert source.count("/api/manual-approval-request-readback") == 1
    assert "renderManualApprovalRequestReadbackSection(tracePayload)" in source
