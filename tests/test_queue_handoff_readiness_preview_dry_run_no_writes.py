from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services


ENDPOINT = "/api/manual-queue-handoff-readiness-preview-dry-run"


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _readback(status: str = "approved") -> dict:
    return {
        "readback_status": "found",
        "approval_request_id": "manual_guarded_approval_123",
        "approval_request_found": True,
        "approval_request_summary": {"approval_status": status},
        "approval_request_fields": {"approval_status": status},
        "context_id": "ctx-1",
        "job_id": "job-1",
    }


def _transition_observability() -> dict:
    return {
        "transition_observability_status": "observed_updated",
        "source_transition_status": "updated",
        "approval_request_id": "manual_guarded_approval_123",
        "transition_was_blocked": False,
        "transition_was_applied": True,
        "proposed_transition": "approve",
        "applied_transition": "approve",
        "previous_status": "pending",
        "new_status": "approved",
        "blocked_actions": [],
        "context_id": "ctx-1",
        "job_id": "job-1",
    }


def _assert_queue_preview_safety(payload: dict) -> None:
    safety = payload["safety_metadata"]
    assert payload["manual_surface"] is True
    assert payload["read_only"] is True
    assert safety["dry_run_only"] is True
    assert safety["queue_handoff_preview_only"] is True
    assert safety["manual_only"] is True
    assert safety["read_only"] is True
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


def test_helper_blocks_missing_approval_request_id():
    payload = services.build_queue_handoff_readiness_preview_payload()

    assert payload["queue_handoff_readiness_status"] == "blocked_missing_approval_request_id"
    assert payload["ready_for_future_queue_handoff"] is False
    assert "approval_request_id" in payload["missing_requirements"]
    assert "approval_request_id_missing" in payload["blocked_actions"]
    _assert_queue_preview_safety(payload)


def test_helper_blocks_missing_or_invalid_readback():
    missing = services.build_queue_handoff_readiness_preview_payload(
        approval_request_id="manual_guarded_approval_123",
        approval_status_transition_observability_payload=_transition_observability(),
    )
    invalid = services.build_queue_handoff_readiness_preview_payload(
        approval_request_id="manual_guarded_approval_123",
        approval_request_readback_payload={"readback_status": "storage_read_error"},
        approval_status_transition_observability_payload=_transition_observability(),
    )

    assert missing["queue_handoff_readiness_status"] == "blocked_missing_readback"
    assert "approval_request_readback_missing" in missing["blocked_actions"]
    assert invalid["queue_handoff_readiness_status"] == "blocked_missing_readback"
    assert "approval_request_readback_invalid" in invalid["blocked_actions"]
    _assert_queue_preview_safety(missing)
    _assert_queue_preview_safety(invalid)


def test_helper_blocks_not_found_readback():
    payload = services.build_queue_handoff_readiness_preview_payload(
        approval_request_id="manual_guarded_approval_123",
        approval_request_readback_payload={
            "readback_status": "not_found",
            "approval_request_id": "manual_guarded_approval_123",
            "approval_request_found": False,
        },
        approval_status_transition_observability_payload=_transition_observability(),
    )

    assert payload["queue_handoff_readiness_status"] == "blocked_not_found"
    assert "approval_request_not_found" in payload["blocked_actions"]
    _assert_queue_preview_safety(payload)


def test_helper_blocks_non_approved_approval_status():
    payload = services.build_queue_handoff_readiness_preview_payload(
        approval_request_readback_payload=_readback("pending"),
        approval_status_transition_observability_payload=_transition_observability(),
    )

    assert payload["queue_handoff_readiness_status"] == "blocked_not_approved"
    assert payload["approval_status"] == "pending"
    assert "approved_approval_status" in payload["missing_requirements"]
    _assert_queue_preview_safety(payload)


def test_helper_blocks_missing_transition_observability():
    payload = services.build_queue_handoff_readiness_preview_payload(
        approval_request_readback_payload=_readback("approved"),
        approval_status_transition_observability_payload={},
    )

    assert payload["queue_handoff_readiness_status"] == "blocked_missing_transition_observability"
    assert "approval_status_transition_observability_payload" in payload["missing_requirements"]
    _assert_queue_preview_safety(payload)


def test_helper_returns_ready_for_approved_readback_and_source_evidence():
    payload = services.build_queue_handoff_readiness_preview_payload(
        approval_request_readback_payload=_readback("approved"),
        approval_status_transition_observability_payload=_transition_observability(),
    )

    assert payload["queue_handoff_readiness_status"] == "ready_for_future_queue_handoff"
    assert payload["approval_request_id"] == "manual_guarded_approval_123"
    assert payload["approval_status"] == "approved"
    assert payload["ready_for_future_queue_handoff"] is True
    assert payload["queue_handoff_allowed_later"] is True
    assert payload["source_readback_status"] == "found"
    assert payload["source_transition_observability_status"] == "observed_updated"
    _assert_queue_preview_safety(payload)


def test_api_route_exists_as_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"POST"}


def test_api_route_returns_dry_run_readonly_preview(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "approval_request_readback_payload": _readback("approved"),
            "approval_status_transition_observability_payload": _transition_observability(),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["api_surface"] == "manual_queue_handoff_readiness_preview_dry_run"
    assert payload["explicit_user_action"] is True
    assert payload["queue_handoff_readiness_status"] == "ready_for_future_queue_handoff"
    _assert_queue_preview_safety(payload)


def test_api_route_slice_has_no_queue_write_status_update_or_execution_calls():
    source = Path("src/app/api.py").read_text()
    start = source.index("class ManualQueueHandoffReadinessPreviewRequest")
    class_end = source.index("@asynccontextmanager")
    route_start = source.index('@app.post("/api/manual-queue-handoff-readiness-preview-dry-run")')
    route_end = source.index('@app.get("/api/agent-feedback")', route_start)
    snippet = source[start:class_end] + source[route_start:route_end]

    forbidden_markers = [
        "_agentic_approval_storage_connection",
        "record_approval_decision(",
        "approval_status=",
        "create_approval_request(",
        "application_execution_queue",
        "_load_csv_rows",
        ".write(",
        "write_text",
        "submit_application(",
        "execute_application(",
        "score_resume_job_match",
        "ranking_update",
        "ranking_mutation",
        "run_chat_completion",
        "workflow_runner",
        "insert_operator_decision",
    ]
    for marker in forbidden_markers:
        assert marker not in snippet


def test_service_helper_slice_has_no_queue_write_status_update_or_execution_calls():
    source = Path("src/app/services.py").read_text()
    start = source.index("def build_queue_handoff_readiness_preview_payload")
    end = source.index("def _agentic_workflow_summary_from_artifacts")
    snippet = source[start:end]

    forbidden_markers = [
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


def test_ui_renders_queue_handoff_preview_button_and_escapes_output():
    source = Path("src/app/static/agentic_review.js").read_text()
    start = source.index("function renderManualQueueHandoffReadinessPreviewSection")
    end = source.index("function renderAgentTraceReadOnlyPanel")
    snippet = source[start:end]

    assert "Manual Queue Handoff Readiness Preview" in snippet
    assert "Preview Queue Handoff Readiness" in snippet
    assert "data-manual-queue-handoff-readiness-preview" in snippet
    assert "escapeHtml(approvalRequestId)" in snippet
    assert "escapeHtml(contextId)" in snippet
    assert "escapeHtml(jobId)" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Missing requirements\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Safety metadata\"" in snippet


def test_ui_click_posts_endpoint_and_existing_transition_observability_still_works():
    source = Path("src/app/static/agentic_review.js").read_text()

    assert source.count("/api/manual-queue-handoff-readiness-preview-dry-run") == 1
    assert "manual_queue_handoff_readiness_preview_result" in source
    assert "renderManualQueueHandoffReadinessPreviewSection(tracePayload)" in source
    assert source.count("/api/manual-approval-status-transition-observability") == 1
    assert "manual_approval_status_transition_observability_result" in source
    assert "renderManualApprovalStatusTransitionObservabilitySection(tracePayload)" in source
