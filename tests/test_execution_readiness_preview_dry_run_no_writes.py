from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services


ENDPOINT = "/api/manual-execution-readiness-preview-dry-run"


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _queue_handoff_observability(*, created: bool = True) -> dict:
    return {
        "queue_handoff_observability_status": "observed_created" if created else "observed_blocked",
        "source_queue_handoff_creation_status": "created" if created else "blocked_by_missing_queue_writer",
        "approval_request_id": "manual_guarded_approval_123",
        "queue_handoff_id": "manual_queue_handoff_abc123",
        "queue_entry_created": created,
        "queue_handoff_was_blocked": not created,
        "queue_handoff_was_created": created,
        "blocked_actions": [] if created else ["queue_writer_unavailable"],
        "context_id": "ctx-1",
        "job_id": "job-1",
    }


def _assert_execution_preview_safety(payload: dict) -> None:
    safety = payload["safety_metadata"]
    assert payload["manual_surface"] is True
    assert payload["read_only"] is True
    assert safety["dry_run_only"] is True
    assert safety["execution_readiness_preview_only"] is True
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


def test_helper_blocks_missing_queue_handoff_id():
    payload = services.build_execution_readiness_preview_payload(
        approval_request_id="manual_guarded_approval_123",
    )

    assert payload["execution_readiness_status"] == "blocked_missing_queue_handoff_id"
    assert "queue_handoff_id" in payload["missing_requirements"]
    assert "queue_handoff_id_missing" in payload["blocked_actions"]
    _assert_execution_preview_safety(payload)


def test_helper_blocks_missing_approval_request_id():
    payload = services.build_execution_readiness_preview_payload(
        queue_handoff_id="manual_queue_handoff_abc123",
    )

    assert payload["execution_readiness_status"] == "blocked_missing_approval_request_id"
    assert "approval_request_id" in payload["missing_requirements"]
    assert "approval_request_id_missing" in payload["blocked_actions"]
    _assert_execution_preview_safety(payload)


def test_helper_blocks_missing_or_invalid_queue_handoff_observability():
    missing = services.build_execution_readiness_preview_payload(
        queue_handoff_id="manual_queue_handoff_abc123",
        approval_request_id="manual_guarded_approval_123",
    )
    invalid = services.build_execution_readiness_preview_payload(
        queue_handoff_id="manual_queue_handoff_abc123",
        approval_request_id="manual_guarded_approval_123",
        queue_handoff_observability_payload={"queue_handoff_observability_status": "observed_invalid_source"},
    )

    assert missing["execution_readiness_status"] == "blocked_missing_queue_handoff_observability"
    assert "queue_handoff_observability_missing" in missing["blocked_actions"]
    assert invalid["execution_readiness_status"] == "blocked_queue_handoff_not_created"
    assert "queue_handoff_not_observed_created" in invalid["blocked_actions"]
    _assert_execution_preview_safety(missing)
    _assert_execution_preview_safety(invalid)


def test_helper_blocks_queue_handoff_not_created():
    payload = services.build_execution_readiness_preview_payload(
        queue_handoff_observability_payload=_queue_handoff_observability(created=False),
    )

    assert payload["execution_readiness_status"] == "blocked_queue_handoff_not_created"
    assert payload["queue_handoff_id"] == "manual_queue_handoff_abc123"
    assert "observed_created_queue_handoff" in payload["missing_requirements"]
    _assert_execution_preview_safety(payload)


def test_helper_returns_ready_for_future_execution_when_source_created_and_ids_present():
    payload = services.build_execution_readiness_preview_payload(
        queue_handoff_observability_payload=_queue_handoff_observability(created=True),
    )

    assert payload["execution_readiness_status"] == "ready_for_future_execution"
    assert payload["approval_request_id"] == "manual_guarded_approval_123"
    assert payload["queue_handoff_id"] == "manual_queue_handoff_abc123"
    assert payload["ready_for_future_execution"] is True
    assert payload["execution_allowed_later"] is True
    assert payload["source_queue_handoff_observability_status"] == "observed_created"
    _assert_execution_preview_safety(payload)


def test_api_route_exists_as_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"POST"}


def test_api_route_returns_dry_run_readonly_preview(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "queue_handoff_observability_payload": _queue_handoff_observability(created=True),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["api_surface"] == "manual_execution_readiness_preview_dry_run"
    assert payload["explicit_user_action"] is True
    assert payload["execution_readiness_status"] == "ready_for_future_execution"
    _assert_execution_preview_safety(payload)


def test_api_route_slice_has_no_execution_submission_queue_write_or_mutation_calls():
    source = Path("src/app/api.py").read_text()
    start = source.index("class ManualExecutionReadinessPreviewRequest")
    class_end = source.index("@asynccontextmanager")
    route_start = source.index('@app.post("/api/manual-execution-readiness-preview-dry-run")')
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
    start = source.index("def build_execution_readiness_preview_payload")
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


def test_ui_renders_execution_readiness_preview_button_and_escapes_output():
    source = Path("src/app/static/agentic_review.js").read_text()
    start = source.index("function renderManualExecutionReadinessPreviewSection")
    end = source.index("function renderAgentTraceReadOnlyPanel")
    snippet = source[start:end]

    assert "Manual Execution Readiness Preview" in snippet
    assert "Preview Execution Readiness" in snippet
    assert "data-manual-execution-readiness-preview" in snippet
    assert "escapeHtml(approvalRequestId)" in snippet
    assert "escapeHtml(queueHandoffId)" in snippet
    assert "escapeHtml(contextId)" in snippet
    assert "escapeHtml(jobId)" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Missing requirements\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Safety metadata\"" in snippet


def test_ui_click_posts_endpoint_and_existing_queue_handoff_observability_still_works():
    source = Path("src/app/static/agentic_review.js").read_text()

    assert source.count("/api/manual-execution-readiness-preview-dry-run") == 1
    assert "manual_execution_readiness_preview_result" in source
    assert "renderManualExecutionReadinessPreviewSection(tracePayload)" in source
    assert source.count("/api/manual-queue-handoff-creation-observability") == 1
    assert "manual_queue_handoff_creation_observability_result" in source
    assert "renderManualQueueHandoffCreationObservabilitySection(tracePayload)" in source
