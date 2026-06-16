from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services


ENDPOINT = "/api/manual-application-execution-preflight-checklist-dry-run"


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _ready_simulation_payload() -> dict:
    return {
        "application_execution_simulation_status": "simulation_ready",
        "execution_request_id": "manual_execution_request_xyz123",
        "approval_request_id": "manual_guarded_approval_123",
        "queue_handoff_id": "manual_queue_handoff_abc123",
        "simulated_execution_allowed_later": True,
        "blocked_actions": [],
        "next_safe_step": "require_future_guarded_execution_confirmation_before_any_launch",
        "context_id": "ctx-1",
        "job_id": "job-1",
        "safety_metadata": {
            "did_execute_application": False,
            "did_submit_application": False,
            "pipeline_wiring_added": False,
        },
    }


def _ready_simulation_observability_payload() -> dict:
    return {
        "application_execution_simulation_observability_status": "observed_ready",
        "source_application_execution_simulation_status": "simulation_ready",
        "execution_request_id": "manual_execution_request_xyz123",
        "approval_request_id": "manual_guarded_approval_123",
        "queue_handoff_id": "manual_queue_handoff_abc123",
        "simulation_was_ready": True,
        "simulation_was_blocked": False,
        "simulated_execution_allowed_later": True,
        "blocked_actions": [],
        "next_safe_step": "require_future_guarded_execution_confirmation_before_any_launch",
        "safety_metadata": {
            "did_execute_application": False,
            "did_submit_application": False,
            "pipeline_wiring_added": False,
        },
    }


def _assert_preflight_safety(payload: dict) -> None:
    safety = payload["safety_metadata"]
    assert payload["manual_surface"] is True
    assert payload["read_only"] is True
    assert safety["dry_run_only"] is True
    assert safety["application_execution_preflight_checklist_only"] is True
    assert safety["manual_only"] is True
    assert safety["read_only"] is True
    assert safety["human_review_required"] is True
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
    payload = services.build_application_execution_preflight_checklist_payload()

    assert payload["application_execution_preflight_status"] == "blocked_missing_execution_request_id"
    assert "execution_request_id" in payload["missing_requirements"]
    _assert_preflight_safety(payload)


def test_helper_blocks_missing_approval_request_id():
    payload = services.build_application_execution_preflight_checklist_payload(
        execution_request_id="manual_execution_request_xyz123",
    )

    assert payload["application_execution_preflight_status"] == "blocked_missing_approval_request_id"
    assert "approval_request_id_missing" in payload["blocked_actions"]
    _assert_preflight_safety(payload)


def test_helper_blocks_missing_queue_handoff_id():
    payload = services.build_application_execution_preflight_checklist_payload(
        execution_request_id="manual_execution_request_xyz123",
        approval_request_id="manual_guarded_approval_123",
    )

    assert payload["application_execution_preflight_status"] == "blocked_missing_queue_handoff_id"
    assert "queue_handoff_id_missing" in payload["blocked_actions"]
    _assert_preflight_safety(payload)


def test_helper_blocks_missing_or_invalid_simulation_payload():
    missing = services.build_application_execution_preflight_checklist_payload(
        execution_request_id="manual_execution_request_xyz123",
        approval_request_id="manual_guarded_approval_123",
        queue_handoff_id="manual_queue_handoff_abc123",
    )
    invalid = services.build_application_execution_preflight_checklist_payload(
        execution_request_id="manual_execution_request_xyz123",
        approval_request_id="manual_guarded_approval_123",
        queue_handoff_id="manual_queue_handoff_abc123",
        application_execution_simulation_payload={},
    )

    assert missing["application_execution_preflight_status"] == "blocked_missing_simulation"
    assert invalid["application_execution_preflight_status"] == "blocked_missing_simulation"
    assert "application_execution_simulation_missing" in missing["blocked_actions"]
    _assert_preflight_safety(missing)
    _assert_preflight_safety(invalid)


def test_helper_blocks_simulation_not_ready():
    payload = services.build_application_execution_preflight_checklist_payload(
        application_execution_simulation_payload={
            **_ready_simulation_payload(),
            "application_execution_simulation_status": "blocked_execution_request_not_ready",
        },
    )

    assert payload["application_execution_preflight_status"] == "blocked_simulation_not_ready"
    assert "application_execution_simulation_not_ready" in payload["blocked_actions"]
    _assert_preflight_safety(payload)


def test_helper_blocks_missing_or_invalid_simulation_observability():
    missing = services.build_application_execution_preflight_checklist_payload(
        application_execution_simulation_payload=_ready_simulation_payload(),
    )
    invalid = services.build_application_execution_preflight_checklist_payload(
        application_execution_simulation_payload=_ready_simulation_payload(),
        application_execution_simulation_observability_payload={},
    )

    assert missing["application_execution_preflight_status"] == "blocked_missing_simulation_observability"
    assert invalid["application_execution_preflight_status"] == "blocked_missing_simulation_observability"
    assert "application_execution_simulation_observability_missing" in missing["blocked_actions"]
    _assert_preflight_safety(missing)
    _assert_preflight_safety(invalid)


def test_helper_blocks_simulation_not_observed_ready():
    payload = services.build_application_execution_preflight_checklist_payload(
        application_execution_simulation_payload=_ready_simulation_payload(),
        application_execution_simulation_observability_payload={
            **_ready_simulation_observability_payload(),
            "application_execution_simulation_observability_status": "observed_blocked",
        },
    )

    assert payload["application_execution_preflight_status"] == "blocked_simulation_not_observed_ready"
    assert "application_execution_simulation_not_observed_ready" in payload["blocked_actions"]
    _assert_preflight_safety(payload)


def test_helper_returns_preflight_ready_for_human_review_and_deterministic_checks():
    simulation = _ready_simulation_payload()
    observability = _ready_simulation_observability_payload()
    original_simulation = deepcopy(simulation)
    original_observability = deepcopy(observability)

    first = services.build_application_execution_preflight_checklist_payload(
        application_execution_simulation_payload=simulation,
        application_execution_simulation_observability_payload=observability,
    )
    second = services.build_application_execution_preflight_checklist_payload(
        application_execution_simulation_payload=simulation,
        application_execution_simulation_observability_payload=observability,
    )

    assert simulation == original_simulation
    assert observability == original_observability
    assert first == second
    assert first["application_execution_preflight_status"] == "preflight_ready_for_human_review"
    assert first["preflight_ready_for_human_review"] is True
    assert first["failed_checks"] == []
    assert [check["check_id"] for check in first["preflight_checks"]] == [
        "execution_request_id_present",
        "approval_request_id_present",
        "queue_handoff_id_present",
        "simulation_ready",
        "simulation_observed_ready",
        "no_execution_performed",
        "no_submission_performed",
        "no_automatic_pipeline_wiring",
    ]
    _assert_preflight_safety(first)


def test_api_route_exists_as_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"POST"}


def test_api_route_returns_dry_run_readonly_preflight(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "application_execution_simulation_payload": _ready_simulation_payload(),
            "application_execution_simulation_observability_payload": (
                _ready_simulation_observability_payload()
            ),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["api_surface"] == "manual_application_execution_preflight_checklist_dry_run"
    assert payload["explicit_user_action"] is True
    assert payload["application_execution_preflight_status"] == "preflight_ready_for_human_review"
    assert payload["preflight_ready_for_human_review"] is True
    _assert_preflight_safety(payload)


def test_api_route_slice_has_no_creation_status_update_queue_write_approval_or_execution_calls():
    source = Path("src/app/api.py").read_text()
    start = source.index("class ManualApplicationExecutionPreflightChecklistRequest")
    class_end = source.index("@asynccontextmanager")
    route_start = source.index('@app.post("/api/manual-application-execution-preflight-checklist-dry-run")')
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
    start = source.index("def build_application_execution_preflight_checklist_payload")
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


def test_ui_renders_preflight_checklist_button_and_escapes_output():
    source = Path("src/app/static/agentic_review.js").read_text()
    start = source.index("function renderManualApplicationExecutionPreflightChecklistSection")
    end = source.index("function renderAgentTraceReadOnlyPanel")
    snippet = source[start:end]

    assert "Manual Application Execution Preflight Checklist" in snippet
    assert "Preview Application Execution Preflight" in snippet
    assert "data-manual-application-execution-preflight-checklist" in snippet
    assert "escapeHtml(approvalRequestId)" in snippet
    assert "escapeHtml(queueHandoffId)" in snippet
    assert "escapeHtml(executionRequestId)" in snippet
    assert "escapeHtml(contextId)" in snippet
    assert "escapeHtml(jobId)" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Preflight checks\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Safety metadata\"" in snippet


def test_ui_click_posts_endpoint_and_existing_simulation_observability_still_works():
    source = Path("src/app/static/agentic_review.js").read_text()

    assert source.count("/api/manual-application-execution-preflight-checklist-dry-run") == 1
    assert "manual_application_execution_preflight_checklist_result" in source
    assert "renderManualApplicationExecutionPreflightChecklistSection(tracePayload)" in source
    assert source.count("/api/manual-application-execution-simulation-observability") == 1
    assert "manual_application_execution_simulation_observability_result" in source
    assert "renderManualApplicationExecutionSimulationObservabilitySection(tracePayload)" in source
