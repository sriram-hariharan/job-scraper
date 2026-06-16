from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services


ENDPOINT = "/api/manual-guarded-execution-launch-request-status-transition"


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _found_readback(status: str = "created") -> dict:
    return {
        "application_execution_launch_request_readback_status": "found",
        "execution_launch_request_id": "manual_execution_launch_request_xyz123",
        "execution_request_id": "manual_execution_request_xyz123",
        "approval_request_id": "manual_guarded_approval_123",
        "queue_handoff_id": "manual_queue_handoff_abc123",
        "execution_launch_request_found": True,
        "execution_launch_request_status": status,
    }


def _ready_preview(transition: str = "ready_for_manual_execution") -> dict:
    target = {
        "ready_for_manual_execution": "ready_for_manual_execution",
        "needs_changes": "needs_changes",
        "cancelled": "cancelled",
        "keep_pending_review": "pending_review",
    }[transition]
    return {
        "execution_launch_request_status_transition_preview_status": (
            "ready_for_future_status_transition"
        ),
        "execution_launch_request_id": "manual_execution_launch_request_xyz123",
        "execution_request_id": "manual_execution_request_xyz123",
        "approval_request_id": "manual_guarded_approval_123",
        "queue_handoff_id": "manual_queue_handoff_abc123",
        "requested_transition": transition,
        "current_execution_launch_request_status": "created",
        "proposed_execution_launch_request_status": target,
        "transition_allowed": True,
        "context_id": "ctx-1",
        "job_id": "job-1",
    }


def _assert_transition_safety(payload: dict, *, updated: bool) -> None:
    safety = payload["safety_metadata"]
    assert payload["manual_surface"] is True
    assert safety["manual_only"] is True
    assert safety["guarded_execution_launch_request_status_transition_only"] is True
    assert safety["human_confirmation_required"] is True
    assert safety["did_create_execution_launch_request"] is False
    assert safety["did_update_execution_launch_request_status"] is updated
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
    assert safety["advisory_only"] is (not updated)


def test_blocks_when_reviewer_confirmation_is_missing():
    calls = []
    payload = services.build_guarded_execution_launch_request_status_transition_payload(
        reviewer_confirmation=False,
        execution_launch_request_status_transition_preview_payload=_ready_preview(),
        application_execution_launch_request_readback_payload=_found_readback(),
        execution_launch_request_status_writer=lambda entry: calls.append(entry),
    )

    assert payload["execution_launch_request_status_transition_status"] == (
        "blocked_by_missing_confirmation"
    )
    assert "reviewer_confirmation_missing" in payload["blocked_actions"]
    assert calls == []
    _assert_transition_safety(payload, updated=False)


def test_blocks_missing_execution_launch_request_id():
    payload = services.build_guarded_execution_launch_request_status_transition_payload(
        requested_transition="ready_for_manual_execution",
        reviewer_confirmation=True,
        execution_launch_request_status_transition_preview_payload={
            "execution_launch_request_status_transition_preview_status": (
                "ready_for_future_status_transition"
            ),
            "requested_transition": "ready_for_manual_execution",
            "proposed_execution_launch_request_status": "ready_for_manual_execution",
        },
    )

    assert payload["execution_launch_request_status_transition_status"] == (
        "blocked_missing_execution_launch_request_id"
    )
    assert "execution_launch_request_id_missing" in payload["blocked_actions"]
    _assert_transition_safety(payload, updated=False)


def test_blocks_missing_requested_transition():
    payload = services.build_guarded_execution_launch_request_status_transition_payload(
        execution_launch_request_id="manual_execution_launch_request_xyz123",
        reviewer_confirmation=True,
        execution_launch_request_status_transition_preview_payload={
            "execution_launch_request_status_transition_preview_status": (
                "ready_for_future_status_transition"
            ),
            "execution_launch_request_id": "manual_execution_launch_request_xyz123",
        },
    )

    assert payload["execution_launch_request_status_transition_status"] == (
        "blocked_missing_requested_transition"
    )
    assert "requested_transition_missing" in payload["blocked_actions"]
    _assert_transition_safety(payload, updated=False)


def test_blocks_invalid_requested_transition():
    payload = services.build_guarded_execution_launch_request_status_transition_payload(
        execution_launch_request_id="manual_execution_launch_request_xyz123",
        requested_transition="launch_now",
        reviewer_confirmation=True,
        execution_launch_request_status_transition_preview_payload=_ready_preview(),
    )

    assert payload["execution_launch_request_status_transition_status"] == (
        "blocked_invalid_requested_transition"
    )
    assert "requested_transition_invalid" in payload["blocked_actions"]
    _assert_transition_safety(payload, updated=False)


def test_blocks_when_transition_preview_is_missing_or_not_ready():
    missing = services.build_guarded_execution_launch_request_status_transition_payload(
        execution_launch_request_id="manual_execution_launch_request_xyz123",
        requested_transition="ready_for_manual_execution",
        reviewer_confirmation=True,
    )
    not_ready = services.build_guarded_execution_launch_request_status_transition_payload(
        execution_launch_request_id="manual_execution_launch_request_xyz123",
        requested_transition="ready_for_manual_execution",
        reviewer_confirmation=True,
        execution_launch_request_status_transition_preview_payload={
            "execution_launch_request_status_transition_preview_status": "blocked_missing_readback",
            "execution_launch_request_id": "manual_execution_launch_request_xyz123",
            "requested_transition": "ready_for_manual_execution",
        },
    )

    assert missing["execution_launch_request_status_transition_status"] == (
        "blocked_by_transition_preview"
    )
    assert not_ready["execution_launch_request_status_transition_status"] == (
        "blocked_by_transition_preview"
    )
    _assert_transition_safety(missing, updated=False)
    _assert_transition_safety(not_ready, updated=False)


def test_blocks_when_execution_launch_request_status_writer_is_unavailable():
    payload = services.build_guarded_execution_launch_request_status_transition_payload(
        reviewer_confirmation=True,
        execution_launch_request_status_transition_preview_payload=_ready_preview("needs_changes"),
        application_execution_launch_request_readback_payload=_found_readback(),
    )

    assert payload["execution_launch_request_status_transition_status"] == (
        "blocked_missing_execution_launch_request_status_writer"
    )
    assert "execution_launch_request_status_writer_unavailable" in payload["blocked_actions"]
    _assert_transition_safety(payload, updated=False)


def test_updates_exactly_one_execution_launch_request_status_when_ready_confirmed_and_writer_exists():
    calls = []
    preview = _ready_preview("ready_for_manual_execution")
    readback = _found_readback()
    original_preview = deepcopy(preview)
    original_readback = deepcopy(readback)

    def fake_status_writer(entry):
        calls.append(entry)
        return {
            "execution_launch_request_id": entry["execution_launch_request_id"],
            "new_execution_launch_request_status": entry["new_execution_launch_request_status"],
            "persisted": True,
        }

    payload = services.build_guarded_execution_launch_request_status_transition_payload(
        reviewer_confirmation=True,
        reviewer_note="Ready for manual execution gate.",
        execution_launch_request_status_transition_preview_payload=preview,
        application_execution_launch_request_readback_payload=readback,
        execution_launch_request_status_writer=fake_status_writer,
    )

    assert preview == original_preview
    assert readback == original_readback
    assert payload["execution_launch_request_status_transition_status"] == "updated"
    assert payload["execution_launch_request_id"] == "manual_execution_launch_request_xyz123"
    assert payload["requested_transition"] == "ready_for_manual_execution"
    assert payload["previous_execution_launch_request_status"] == "created"
    assert payload["new_execution_launch_request_status"] == "ready_for_manual_execution"
    assert payload["execution_launch_request_status_updated"] is True
    assert len(calls) == 1
    assert calls[0]["execution_launch_request_id"] == "manual_execution_launch_request_xyz123"
    assert calls[0]["new_execution_launch_request_status"] == "ready_for_manual_execution"
    assert calls[0]["manual_guarded_execution_launch_request_status_transition"] is True
    assert calls[0]["execute_application"] is False
    assert calls[0]["submit_application"] is False
    _assert_transition_safety(payload, updated=True)


def test_new_status_mapping_is_deterministic_for_all_supported_transitions():
    expected = {
        "ready_for_manual_execution": "ready_for_manual_execution",
        "needs_changes": "needs_changes",
        "cancelled": "cancelled",
        "keep_pending_review": "pending_review",
    }

    for transition, expected_status in expected.items():
        calls = []
        payload = services.build_guarded_execution_launch_request_status_transition_payload(
            requested_transition=transition,
            reviewer_confirmation=True,
            execution_launch_request_status_transition_preview_payload=_ready_preview(transition),
            application_execution_launch_request_readback_payload=_found_readback(),
            execution_launch_request_status_writer=lambda entry, calls=calls: calls.append(entry)
            or entry,
        )

        assert payload["execution_launch_request_status_transition_status"] == "updated"
        assert payload["new_execution_launch_request_status"] == expected_status
        assert calls[0]["new_execution_launch_request_status"] == expected_status
        _assert_transition_safety(payload, updated=True)


def test_api_route_exists_as_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"POST"}


def test_api_route_blocks_without_execution_launch_request_status_writer(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "reviewer_confirmation": True,
            "execution_launch_request_status_transition_preview_payload": _ready_preview(),
            "application_execution_launch_request_readback_payload": _found_readback(),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["api_surface"] == "manual_guarded_execution_launch_request_status_transition"
    assert payload["explicit_user_action"] is True
    assert payload["execution_launch_request_status_transition_status"] == (
        "blocked_missing_execution_launch_request_status_writer"
    )
    _assert_transition_safety(payload, updated=False)


def test_api_route_slice_has_no_execution_creation_approval_resume_scoring_ranking_execution_or_submission_calls():
    source = Path("src/app/api.py").read_text()
    start = source.index("class ManualGuardedExecutionLaunchRequestStatusTransitionRequest")
    class_end = source.index("@asynccontextmanager")
    route_start = source.index(
        '@app.post("/api/manual-guarded-execution-launch-request-status-transition")'
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
        "execute_application(",
        "submit_application(",
        "score_resume_job_match",
        "ranking_state",
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


def test_service_helper_slice_limits_mutation_to_injected_launch_request_status_writer():
    source = Path("src/app/services.py").read_text()
    start = source.index("def build_guarded_execution_launch_request_status_transition_payload")
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
        "execute_application(",
        "submit_application(",
        "score_resume_job_match",
        "ranking_state",
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
    assert "execution_launch_request_status_writer(" in snippet


def test_ui_renders_confirmation_control_and_escapes_output():
    source = Path("src/app/static/agentic_review.js").read_text()
    start = source.index("function renderManualGuardedExecutionLaunchRequestStatusTransitionSection")
    end = source.index("function renderAgentTraceReadOnlyPanel")
    snippet = source[start:end]

    assert "Manual Guarded Execution Launch Request Status Transition" in snippet
    assert "Apply Guarded Execution Launch Request Status" in snippet
    assert "data-manual-guarded-execution-launch-request-status-transition" in snippet
    assert "data-manual-guarded-execution-launch-request-status-transition-confirmation" in snippet
    assert "escapeHtml(approvalRequestId)" in snippet
    assert "escapeHtml(queueHandoffId)" in snippet
    assert "escapeHtml(executionRequestId)" in snippet
    assert "escapeHtml(executionLaunchRequestId)" in snippet
    assert "escapeHtml(requestedTransition)" in snippet
    assert "escapeHtml(contextId)" in snippet
    assert "escapeHtml(jobId)" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Safety metadata\"" in snippet


def test_ui_click_posts_endpoint_and_existing_transition_preview_surface_still_works():
    source = Path("src/app/static/agentic_review.js").read_text()

    assert source.count('"/api/manual-guarded-execution-launch-request-status-transition"') == 1
    assert "manual_guarded_execution_launch_request_status_transition_result" in source
    assert "renderManualGuardedExecutionLaunchRequestStatusTransitionSection(tracePayload)" in source
    assert source.count("/api/manual-execution-launch-request-status-transition-preview-dry-run") == 1
    assert "manual_execution_launch_request_status_transition_preview_result" in source
    assert "renderManualExecutionLaunchRequestStatusTransitionPreviewSection(tracePayload)" in source
