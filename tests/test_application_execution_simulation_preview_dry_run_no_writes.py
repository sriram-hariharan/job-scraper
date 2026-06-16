from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services


ENDPOINT = "/api/manual-application-execution-simulation-preview-dry-run"


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _found_readback(status: str = "ready_for_manual_execution") -> dict:
    return {
        "execution_request_readback_status": "found",
        "execution_request_id": "manual_execution_request_xyz123",
        "approval_request_id": "manual_guarded_approval_123",
        "queue_handoff_id": "manual_queue_handoff_abc123",
        "execution_request_found": True,
        "execution_request_status": status,
        "context_id": "ctx-1",
        "job_id": "job-1",
    }


def _updated_transition_payload() -> dict:
    return {
        "execution_request_status_transition_status": "updated",
        "execution_request_id": "manual_execution_request_xyz123",
        "approval_request_id": "manual_guarded_approval_123",
        "queue_handoff_id": "manual_queue_handoff_abc123",
        "requested_transition": "ready_for_manual_execution",
        "previous_execution_request_status": "created_control_artifact",
        "new_execution_request_status": "ready_for_manual_execution",
        "execution_request_status_updated": True,
        "blocked_actions": [],
        "next_safe_step": "review_updated_execution_request_status_before_any_execution",
        "safety_metadata": {
            "did_update_execution_request_status": True,
            "did_execute_application": False,
            "did_submit_application": False,
        },
    }


def _updated_transition_observability_payload() -> dict:
    return {
        "execution_request_status_transition_observability_status": "observed_updated",
        "source_execution_request_status_transition_status": "updated",
        "execution_request_id": "manual_execution_request_xyz123",
        "approval_request_id": "manual_guarded_approval_123",
        "queue_handoff_id": "manual_queue_handoff_abc123",
        "requested_transition": "ready_for_manual_execution",
        "previous_execution_request_status": "created_control_artifact",
        "new_execution_request_status": "ready_for_manual_execution",
        "execution_request_status_updated": True,
        "execution_request_status_transition_was_blocked": False,
        "execution_request_status_transition_was_applied": True,
        "blocked_actions": [],
        "next_safe_step": "read_execution_request_status_before_any_future_execution",
    }


def _assert_simulation_safety(payload: dict) -> None:
    safety = payload["safety_metadata"]
    assert payload["manual_surface"] is True
    assert payload["read_only"] is True
    assert safety["dry_run_only"] is True
    assert safety["application_execution_simulation_preview_only"] is True
    assert safety["manual_only"] is True
    assert safety["read_only"] is True
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
    payload = services.build_application_execution_simulation_preview_payload()

    assert payload["application_execution_simulation_status"] == "blocked_missing_execution_request_id"
    assert payload["simulated_execution_allowed_later"] is False
    assert "execution_request_id" in payload["missing_requirements"]
    _assert_simulation_safety(payload)


def test_helper_blocks_missing_approval_request_id():
    payload = services.build_application_execution_simulation_preview_payload(
        execution_request_id="manual_execution_request_xyz123",
    )

    assert payload["application_execution_simulation_status"] == "blocked_missing_approval_request_id"
    assert "approval_request_id_missing" in payload["blocked_actions"]
    _assert_simulation_safety(payload)


def test_helper_blocks_missing_queue_handoff_id():
    payload = services.build_application_execution_simulation_preview_payload(
        execution_request_id="manual_execution_request_xyz123",
        approval_request_id="manual_guarded_approval_123",
    )

    assert payload["application_execution_simulation_status"] == "blocked_missing_queue_handoff_id"
    assert "queue_handoff_id_missing" in payload["blocked_actions"]
    _assert_simulation_safety(payload)


def test_helper_blocks_missing_or_invalid_execution_request_readback():
    missing = services.build_application_execution_simulation_preview_payload(
        execution_request_id="manual_execution_request_xyz123",
        approval_request_id="manual_guarded_approval_123",
        queue_handoff_id="manual_queue_handoff_abc123",
    )
    invalid = services.build_application_execution_simulation_preview_payload(
        execution_request_id="manual_execution_request_xyz123",
        approval_request_id="manual_guarded_approval_123",
        queue_handoff_id="manual_queue_handoff_abc123",
        execution_request_readback_payload={"execution_request_readback_status": "insufficient_information"},
    )

    assert missing["application_execution_simulation_status"] == "blocked_missing_execution_request_readback"
    assert "execution_request_readback_missing" in missing["blocked_actions"]
    assert invalid["application_execution_simulation_status"] == "blocked_execution_request_not_found"
    assert "execution_request_not_found" in invalid["blocked_actions"]
    _assert_simulation_safety(missing)
    _assert_simulation_safety(invalid)


def test_helper_blocks_not_found_readback():
    payload = services.build_application_execution_simulation_preview_payload(
        execution_request_id="manual_execution_request_xyz123",
        approval_request_id="manual_guarded_approval_123",
        queue_handoff_id="manual_queue_handoff_abc123",
        execution_request_readback_payload={
            "execution_request_readback_status": "not_found",
            "execution_request_id": "manual_execution_request_xyz123",
            "execution_request_found": False,
        },
    )

    assert payload["application_execution_simulation_status"] == "blocked_execution_request_not_found"
    assert "execution_request_not_found" in payload["blocked_actions"]
    _assert_simulation_safety(payload)


def test_helper_blocks_execution_request_status_not_ready():
    payload = services.build_application_execution_simulation_preview_payload(
        execution_request_readback_payload=_found_readback("created_control_artifact"),
        execution_request_status_transition_observability_payload=_updated_transition_observability_payload(),
    )

    assert payload["application_execution_simulation_status"] == "blocked_execution_request_not_ready"
    assert "execution_request_status_not_ready" in payload["blocked_actions"]
    _assert_simulation_safety(payload)


def test_helper_blocks_missing_status_transition_observability():
    payload = services.build_application_execution_simulation_preview_payload(
        execution_request_readback_payload=_found_readback(),
    )

    assert (
        payload["application_execution_simulation_status"]
        == "blocked_missing_status_transition_observability"
    )
    assert "execution_request_status_transition_observability_missing" in payload["blocked_actions"]
    _assert_simulation_safety(payload)


def test_helper_returns_simulation_ready_when_source_evidence_is_sufficient_and_deterministic():
    readback = _found_readback()
    audit = _updated_transition_observability_payload()
    original_readback = deepcopy(readback)
    original_audit = deepcopy(audit)

    first = services.build_application_execution_simulation_preview_payload(
        execution_request_readback_payload=readback,
        execution_request_status_transition_observability_payload=audit,
    )
    second = services.build_application_execution_simulation_preview_payload(
        execution_request_readback_payload=readback,
        execution_request_status_transition_observability_payload=audit,
    )

    assert readback == original_readback
    assert audit == original_audit
    assert first == second
    assert first["application_execution_simulation_status"] == "simulation_ready"
    assert first["simulated_execution_allowed_later"] is True
    assert [step["step_id"] for step in first["simulated_steps"]] == [
        "load_execution_request_context",
        "validate_manual_execution_gate",
        "prepare_execution_runtime_inputs",
    ]
    assert first["execution_preconditions"]["execution_request_ready_for_manual_execution"] is True
    _assert_simulation_safety(first)


def test_helper_can_build_transition_observability_from_guarded_transition_payload():
    payload = services.build_application_execution_simulation_preview_payload(
        execution_request_readback_payload=_found_readback(),
        execution_request_status_transition_payload=_updated_transition_payload(),
    )

    assert payload["application_execution_simulation_status"] == "simulation_ready"
    assert payload["source_execution_request_status_transition_observability_status"] == "observed_updated"
    _assert_simulation_safety(payload)


def test_api_route_exists_as_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"POST"}


def test_api_route_returns_dry_run_readonly_simulation_preview(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "execution_request_readback_payload": _found_readback(),
            "execution_request_status_transition_observability_payload": (
                _updated_transition_observability_payload()
            ),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["api_surface"] == "manual_application_execution_simulation_preview_dry_run"
    assert payload["explicit_user_action"] is True
    assert payload["application_execution_simulation_status"] == "simulation_ready"
    assert payload["simulated_execution_allowed_later"] is True
    _assert_simulation_safety(payload)


def test_api_route_slice_has_no_creation_status_update_queue_write_approval_or_execution_calls():
    source = Path("src/app/api.py").read_text()
    start = source.index("class ManualApplicationExecutionSimulationPreviewRequest")
    class_end = source.index("@asynccontextmanager")
    route_start = source.index('@app.post("/api/manual-application-execution-simulation-preview-dry-run")')
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
    start = source.index("def build_application_execution_simulation_preview_payload")
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


def test_ui_renders_simulation_preview_button_and_escapes_output():
    source = Path("src/app/static/agentic_review.js").read_text()
    start = source.index("function renderManualApplicationExecutionSimulationPreviewSection")
    end = source.index("function renderAgentTraceReadOnlyPanel")
    snippet = source[start:end]

    assert "Manual Application Execution Simulation Preview" in snippet
    assert "Preview Application Execution Simulation" in snippet
    assert "data-manual-application-execution-simulation-preview" in snippet
    assert "escapeHtml(approvalRequestId)" in snippet
    assert "escapeHtml(queueHandoffId)" in snippet
    assert "escapeHtml(executionRequestId)" in snippet
    assert "escapeHtml(contextId)" in snippet
    assert "escapeHtml(jobId)" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Simulated steps\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Safety metadata\"" in snippet


def test_ui_click_posts_endpoint_and_existing_status_transition_observability_still_works():
    source = Path("src/app/static/agentic_review.js").read_text()

    assert source.count("/api/manual-application-execution-simulation-preview-dry-run") == 1
    assert "manual_application_execution_simulation_preview_result" in source
    assert "renderManualApplicationExecutionSimulationPreviewSection(tracePayload)" in source
    assert source.count("/api/manual-guarded-execution-request-status-transition-observability") == 1
    assert "manual_guarded_execution_request_status_transition_observability_result" in source
    assert "renderManualGuardedExecutionRequestStatusTransitionObservabilitySection(tracePayload)" in source
