from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services


ENDPOINT = "/api/manual-queue-handoff-creation-observability"


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _created_handoff_payload() -> dict:
    return {
        "queue_handoff_creation_status": "created",
        "approval_request_id": "manual_guarded_approval_123",
        "queue_handoff_id": "manual_queue_handoff_abc123",
        "queue_entry_created": True,
        "source_queue_handoff_readiness_status": "ready_for_future_queue_handoff",
        "approval_status": "approved",
        "blocked_actions": [],
        "next_safe_step": "review_created_queue_handoff_before_any_execution",
        "context_id": "ctx-1",
        "job_id": "job-1",
        "safety_metadata": {
            "did_mutate_queue": True,
            "did_write_queue": True,
            "did_execute_application": False,
            "did_submit_application": False,
        },
    }


def _blocked_handoff_payload() -> dict:
    return {
        "queue_handoff_creation_status": "blocked_by_missing_queue_writer",
        "approval_request_id": "manual_guarded_approval_123",
        "queue_handoff_id": "",
        "queue_entry_created": False,
        "source_queue_handoff_readiness_status": "ready_for_future_queue_handoff",
        "approval_status": "approved",
        "blocked_actions": ["queue_writer_unavailable"],
        "next_safe_step": "configure_existing_queue_writer_before_manual_handoff",
        "safety_metadata": {
            "did_mutate_queue": False,
            "did_write_queue": False,
            "did_execute_application": False,
            "did_submit_application": False,
        },
    }


def _assert_observability_safety(payload: dict) -> None:
    safety = payload["safety_metadata"]
    assert payload["manual_surface"] is True
    assert payload["read_only"] is True
    assert safety["read_only"] is True
    assert safety["observability_only"] is True
    assert safety["queue_handoff_audit_only"] is True
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


def test_helper_observes_created_queue_handoff_without_mutation():
    payload = services.build_guarded_queue_handoff_creation_observability_payload(
        guarded_queue_handoff_creation_payload=_created_handoff_payload(),
    )

    assert payload["queue_handoff_observability_status"] == "observed_created"
    assert payload["source_queue_handoff_creation_status"] == "created"
    assert payload["approval_request_id"] == "manual_guarded_approval_123"
    assert payload["queue_handoff_id"] == "manual_queue_handoff_abc123"
    assert payload["queue_entry_created"] is True
    assert payload["queue_handoff_was_created"] is True
    assert payload["queue_handoff_was_blocked"] is False
    assert payload["audit_summary"]["source_wrote_queue"] is True
    assert payload["safety_findings"]["observability_wrote_queue"] is False
    _assert_observability_safety(payload)


def test_helper_observes_blocked_queue_handoff_without_mutation():
    payload = services.build_guarded_queue_handoff_creation_observability_payload(
        guarded_queue_handoff_creation_payload=_blocked_handoff_payload(),
    )

    assert payload["queue_handoff_observability_status"] == "observed_blocked"
    assert payload["source_queue_handoff_creation_status"] == "blocked_by_missing_queue_writer"
    assert payload["queue_handoff_was_created"] is False
    assert payload["queue_handoff_was_blocked"] is True
    assert "queue_writer_unavailable" in payload["blocked_actions"]
    _assert_observability_safety(payload)


def test_helper_missing_or_invalid_source_returns_safe_fallback():
    missing = services.build_guarded_queue_handoff_creation_observability_payload()
    invalid = services.build_guarded_queue_handoff_creation_observability_payload(
        guarded_queue_handoff_creation_payload={"queue_handoff_creation_status": "surprising_state"},
    )

    assert missing["queue_handoff_observability_status"] == "observed_missing_source"
    assert "guarded_queue_handoff_creation_payload_missing" in missing["blocked_actions"]
    assert invalid["queue_handoff_observability_status"] == "observed_invalid_source"
    assert "guarded_queue_handoff_creation_status_unrecognized" in invalid["blocked_actions"]
    _assert_observability_safety(missing)
    _assert_observability_safety(invalid)


def test_api_route_exists_as_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"POST"}


def test_api_route_returns_readonly_observability_payload(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "guarded_queue_handoff_creation_payload": _created_handoff_payload(),
            "approval_request_id": "manual_guarded_approval_123",
            "queue_handoff_id": "manual_queue_handoff_abc123",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["api_surface"] == "manual_queue_handoff_creation_observability"
    assert payload["explicit_user_action"] is True
    assert payload["queue_handoff_observability_status"] == "observed_created"
    assert payload["queue_handoff_was_created"] is True
    _assert_observability_safety(payload)


def test_api_route_slice_has_no_queue_write_approval_mutation_or_execution_calls():
    source = Path("src/app/api.py").read_text()
    start = source.index("class ManualQueueHandoffCreationObservabilityRequest")
    class_end = source.index("@asynccontextmanager")
    route_start = source.index('@app.post("/api/manual-queue-handoff-creation-observability")')
    route_end = source.index('@app.get("/api/agent-feedback")', route_start)
    snippet = source[start:class_end] + source[route_start:route_end]

    forbidden_markers = [
        "queue_writer(",
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


def test_service_helper_slice_has_no_queue_write_approval_mutation_or_execution_calls():
    source = Path("src/app/services.py").read_text()
    start = source.index("def build_guarded_queue_handoff_creation_observability_payload")
    end = source.index("def _agentic_workflow_summary_from_artifacts")
    snippet = source[start:end]

    forbidden_markers = [
        "queue_writer(",
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
    start = source.index("function renderManualQueueHandoffCreationObservabilitySection")
    end = source.index("function renderAgentTraceReadOnlyPanel")
    snippet = source[start:end]

    assert "Manual Queue Handoff Audit" in snippet
    assert "View Queue Handoff Audit" in snippet
    assert "data-manual-queue-handoff-creation-observability" in snippet
    assert "escapeHtml(approvalRequestId)" in snippet
    assert "escapeHtml(queueHandoffId)" in snippet
    assert "escapeHtml(contextId)" in snippet
    assert "escapeHtml(jobId)" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Audit summary\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Safety metadata\"" in snippet


def test_ui_click_posts_endpoint_and_existing_guarded_queue_handoff_still_works():
    source = Path("src/app/static/agentic_review.js").read_text()

    assert source.count("/api/manual-queue-handoff-creation-observability") == 1
    assert "manual_queue_handoff_creation_observability_result" in source
    assert "renderManualQueueHandoffCreationObservabilitySection(tracePayload)" in source
    assert source.count("/api/manual-guarded-queue-handoff-create") == 1
    assert "manual_guarded_queue_handoff_create_result" in source
    assert "renderManualGuardedQueueHandoffCreateSection(tracePayload)" in source
