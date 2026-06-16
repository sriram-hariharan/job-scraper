from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services


ENDPOINT = "/api/manual-guarded-application-execution-launch-request-create"


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
    }


def _assert_launch_request_safety(payload: dict, *, created: bool) -> None:
    safety = payload["safety_metadata"]
    assert payload["manual_surface"] is True
    assert safety["manual_only"] is True
    assert safety["guarded_application_execution_launch_request_only"] is True
    assert safety["human_confirmation_required"] is True
    assert safety["did_create_execution_launch_request"] is created
    assert safety["did_create_execution_request"] is False
    assert safety["did_update_execution_request_status"] is False
    assert safety["did_create_approval"] is False
    assert safety["did_mutate_approval"] is False
    assert safety["did_update_approval_status"] is False
    assert safety["did_mutate_queue"] is created
    assert safety["did_write_queue"] is created
    assert safety["did_execute_application"] is False
    assert safety["did_submit_application"] is False
    assert safety["did_mutate_resume"] is False
    assert safety["did_mutate_scoring"] is False
    assert safety["did_change_ranking"] is False
    assert safety["pipeline_wiring_added"] is False
    assert safety["auto_apply_enabled"] is False
    assert safety["advisory_only"] is (not created)


def test_blocks_when_reviewer_confirmation_is_missing():
    calls = []
    payload = services.build_guarded_application_execution_launch_request_payload(
        reviewer_confirmation=False,
        application_execution_preflight_payload=_ready_preflight(),
        application_execution_preflight_observability_payload=_ready_preflight_observability(),
        execution_launch_request_writer=lambda entry: calls.append(entry),
    )

    assert payload["application_execution_launch_request_status"] == "blocked_by_missing_confirmation"
    assert payload["execution_launch_request_created"] is False
    assert "reviewer_confirmation_missing" in payload["blocked_actions"]
    assert calls == []
    _assert_launch_request_safety(payload, created=False)


def test_blocks_when_execution_request_id_is_missing():
    payload = services.build_guarded_application_execution_launch_request_payload(
        approval_request_id="manual_guarded_approval_123",
        queue_handoff_id="manual_queue_handoff_abc123",
        reviewer_confirmation=True,
        application_execution_preflight_payload={
            "application_execution_preflight_status": "preflight_ready_for_human_review",
        },
        application_execution_preflight_observability_payload={
            "application_execution_preflight_observability_status": "observed_ready",
        },
    )

    assert payload["application_execution_launch_request_status"] == "blocked_missing_execution_request_id"
    assert "execution_request_id_missing" in payload["blocked_actions"]
    _assert_launch_request_safety(payload, created=False)


def test_blocks_when_approval_request_id_is_missing():
    payload = services.build_guarded_application_execution_launch_request_payload(
        execution_request_id="manual_execution_request_xyz123",
        queue_handoff_id="manual_queue_handoff_abc123",
        reviewer_confirmation=True,
        application_execution_preflight_payload={
            "application_execution_preflight_status": "preflight_ready_for_human_review",
        },
        application_execution_preflight_observability_payload={
            "application_execution_preflight_observability_status": "observed_ready",
        },
    )

    assert payload["application_execution_launch_request_status"] == "blocked_missing_approval_request_id"
    assert "approval_request_id_missing" in payload["blocked_actions"]
    _assert_launch_request_safety(payload, created=False)


def test_blocks_when_queue_handoff_id_is_missing():
    payload = services.build_guarded_application_execution_launch_request_payload(
        execution_request_id="manual_execution_request_xyz123",
        approval_request_id="manual_guarded_approval_123",
        reviewer_confirmation=True,
        application_execution_preflight_payload={
            "application_execution_preflight_status": "preflight_ready_for_human_review",
        },
        application_execution_preflight_observability_payload={
            "application_execution_preflight_observability_status": "observed_ready",
        },
    )

    assert payload["application_execution_launch_request_status"] == "blocked_missing_queue_handoff_id"
    assert "queue_handoff_id_missing" in payload["blocked_actions"]
    _assert_launch_request_safety(payload, created=False)


def test_blocks_when_preflight_is_missing_or_not_ready():
    missing = services.build_guarded_application_execution_launch_request_payload(
        execution_request_id="manual_execution_request_xyz123",
        approval_request_id="manual_guarded_approval_123",
        queue_handoff_id="manual_queue_handoff_abc123",
        reviewer_confirmation=True,
    )
    not_ready = services.build_guarded_application_execution_launch_request_payload(
        reviewer_confirmation=True,
        application_execution_preflight_payload={
            **_ready_preflight(),
            "application_execution_preflight_status": "blocked_simulation_not_ready",
        },
        application_execution_preflight_observability_payload=_ready_preflight_observability(),
    )

    assert missing["application_execution_launch_request_status"] == "blocked_by_preflight"
    assert not_ready["application_execution_launch_request_status"] == "blocked_by_preflight"
    _assert_launch_request_safety(missing, created=False)
    _assert_launch_request_safety(not_ready, created=False)


def test_blocks_when_preflight_observability_is_missing_or_not_observed_ready():
    missing = services.build_guarded_application_execution_launch_request_payload(
        reviewer_confirmation=True,
        application_execution_preflight_payload=_ready_preflight(),
    )
    not_ready = services.build_guarded_application_execution_launch_request_payload(
        reviewer_confirmation=True,
        application_execution_preflight_payload=_ready_preflight(),
        application_execution_preflight_observability_payload={
            **_ready_preflight_observability(),
            "application_execution_preflight_observability_status": "observed_blocked",
        },
    )

    assert missing["application_execution_launch_request_status"] == "blocked_missing_preflight_observability"
    assert not_ready["application_execution_launch_request_status"] == "blocked_missing_preflight_observability"
    _assert_launch_request_safety(missing, created=False)
    _assert_launch_request_safety(not_ready, created=False)


def test_blocks_when_execution_launch_request_writer_is_unavailable():
    payload = services.build_guarded_application_execution_launch_request_payload(
        reviewer_confirmation=True,
        application_execution_preflight_payload=_ready_preflight(),
        application_execution_preflight_observability_payload=_ready_preflight_observability(),
    )

    assert payload["application_execution_launch_request_status"] == (
        "blocked_missing_execution_launch_request_writer"
    )
    assert payload["execution_launch_request_created"] is False
    assert "execution_launch_request_writer_unavailable" in payload["blocked_actions"]
    _assert_launch_request_safety(payload, created=False)


def test_creates_exactly_one_launch_request_when_ready_confirmed_and_writer_exists():
    calls = []
    preflight = _ready_preflight()
    audit = _ready_preflight_observability()
    original_preflight = deepcopy(preflight)
    original_audit = deepcopy(audit)

    def fake_launch_request_writer(entry):
        calls.append(entry)
        return {"execution_launch_request_id": entry["execution_launch_request_id"], "persisted": True}

    payload = services.build_guarded_application_execution_launch_request_payload(
        reviewer_confirmation=True,
        reviewer_note="Create future launch request.",
        application_execution_preflight_payload=preflight,
        application_execution_preflight_observability_payload=audit,
        execution_launch_request_writer=fake_launch_request_writer,
    )

    assert preflight == original_preflight
    assert audit == original_audit
    assert payload["application_execution_launch_request_status"] == "created"
    assert payload["execution_request_id"] == "manual_execution_request_xyz123"
    assert payload["approval_request_id"] == "manual_guarded_approval_123"
    assert payload["queue_handoff_id"] == "manual_queue_handoff_abc123"
    assert payload["execution_launch_request_created"] is True
    assert payload["execution_launch_request_id"].startswith("manual_execution_launch_request_")
    assert len(calls) == 1
    assert calls[0]["execute_application"] is False
    assert calls[0]["submit_application"] is False
    assert calls[0]["manual_guarded_application_execution_launch_request"] is True
    _assert_launch_request_safety(payload, created=True)


def test_api_route_exists_as_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"POST"}


def test_api_route_blocks_without_execution_launch_request_writer(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "reviewer_confirmation": True,
            "application_execution_preflight_payload": _ready_preflight(),
            "application_execution_preflight_observability_payload": _ready_preflight_observability(),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["api_surface"] == "manual_guarded_application_execution_launch_request_create"
    assert payload["explicit_user_action"] is True
    assert payload["application_execution_launch_request_status"] == (
        "blocked_missing_execution_launch_request_writer"
    )
    _assert_launch_request_safety(payload, created=False)


def test_api_route_slice_has_no_execution_request_approval_resume_scoring_ranking_execution_or_submission_calls():
    source = Path("src/app/api.py").read_text()
    start = source.index("class ManualGuardedApplicationExecutionLaunchRequestCreateRequest")
    class_end = source.index("@asynccontextmanager")
    route_start = source.index('@app.post("/api/manual-guarded-application-execution-launch-request-create")')
    route_end = source.index('@app.get("/api/agent-feedback")', route_start)
    snippet = source[start:class_end] + source[route_start:route_end]

    forbidden_markers = [
        "execution_request_writer(",
        "execution_request_status_writer(",
        "record_approval_decision(",
        "approval_status=",
        "create_approval_request(",
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


def test_service_helper_slice_limits_mutation_to_injected_launch_request_writer():
    source = Path("src/app/services.py").read_text()
    start = source.index("def build_guarded_application_execution_launch_request_payload")
    end = source.index("def _agentic_workflow_summary_from_artifacts")
    snippet = source[start:end]

    forbidden_markers = [
        "record_approval_decision(",
        "get_approval_request(",
        "create_approval_request(",
        "_load_csv_rows",
        "write_text",
        ".write(",
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
    assert "execution_launch_request_writer(" in snippet


def test_ui_renders_confirmation_control_and_escapes_output():
    source = Path("src/app/static/agentic_review.js").read_text()
    start = source.index("function renderManualGuardedApplicationExecutionLaunchRequestCreateSection")
    end = source.index("function renderAgentTraceReadOnlyPanel")
    snippet = source[start:end]

    assert "Manual Guarded Execution Launch Request" in snippet
    assert "Create Guarded Execution Launch Request" in snippet
    assert "data-manual-guarded-application-execution-launch-request-create" in snippet
    assert "data-manual-guarded-application-execution-launch-request-create-confirmation" in snippet
    assert "escapeHtml(approvalRequestId)" in snippet
    assert "escapeHtml(queueHandoffId)" in snippet
    assert "escapeHtml(executionRequestId)" in snippet
    assert "escapeHtml(contextId)" in snippet
    assert "escapeHtml(jobId)" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Safety metadata\"" in snippet


def test_ui_click_posts_endpoint_and_existing_preflight_observability_still_works():
    source = Path("src/app/static/agentic_review.js").read_text()

    assert source.count("/api/manual-guarded-application-execution-launch-request-create") == 1
    assert "manual_guarded_application_execution_launch_request_create_result" in source
    assert "renderManualGuardedApplicationExecutionLaunchRequestCreateSection(tracePayload)" in source
    assert source.count("/api/manual-application-execution-preflight-observability") == 1
    assert "manual_application_execution_preflight_observability_result" in source
    assert "renderManualApplicationExecutionPreflightObservabilitySection(tracePayload)" in source
