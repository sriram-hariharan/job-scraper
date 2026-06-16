from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services


ENDPOINT = "/api/manual-guarded-execution-request-create"


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _ready_packet() -> dict:
    return {
        "execution_request_packet_status": "packet_ready_for_human_review",
        "approval_request_id": "manual_guarded_approval_123",
        "queue_handoff_id": "manual_queue_handoff_abc123",
        "packet_ready_for_human_review": True,
        "blocked_actions": [],
        "missing_requirements": [],
        "source_execution_launch_gate_status": "ready_for_future_manual_execution",
        "source_execution_launch_gate_observability_status": "observed_ready",
        "context_id": "ctx-1",
        "job_id": "job-1",
    }


def _not_ready_packet() -> dict:
    packet = _ready_packet()
    packet.update(
        {
            "execution_request_packet_status": "blocked_execution_launch_not_ready",
            "packet_ready_for_human_review": False,
            "blocked_actions": ["execution_launch_gate_not_ready"],
        }
    )
    return packet


def _ready_launch_gate() -> dict:
    return {
        "execution_launch_gate_status": "ready_for_future_manual_execution",
        "approval_request_id": "manual_guarded_approval_123",
        "queue_handoff_id": "manual_queue_handoff_abc123",
        "ready_for_future_manual_execution": True,
    }


def _ready_launch_gate_observability() -> dict:
    return {
        "execution_launch_gate_observability_status": "observed_ready",
        "approval_request_id": "manual_guarded_approval_123",
        "queue_handoff_id": "manual_queue_handoff_abc123",
        "future_manual_execution_allowed": True,
    }


def _assert_execution_request_safety(payload: dict, *, created: bool) -> None:
    safety = payload["safety_metadata"]
    assert payload["manual_surface"] is True
    assert safety["manual_only"] is True
    assert safety["guarded_execution_request_only"] is True
    assert safety["human_confirmation_required"] is True
    assert safety["did_create_approval"] is False
    assert safety["did_mutate_approval"] is False
    assert safety["did_update_approval_status"] is False
    assert safety["did_mutate_queue"] is created
    assert safety["did_write_queue"] is created
    assert safety["did_create_execution_request"] is created
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

    payload = services.build_guarded_execution_request_creation_payload(
        execution_request_packet_payload=_ready_packet(),
        reviewer_confirmation=False,
        execution_request_writer=lambda entry: calls.append(entry),
    )

    assert payload["execution_request_creation_status"] == "blocked_by_missing_confirmation"
    assert payload["execution_request_created"] is False
    assert "reviewer_confirmation_missing" in payload["blocked_actions"]
    assert calls == []
    _assert_execution_request_safety(payload, created=False)


def test_blocks_when_approval_request_id_is_missing():
    calls = []

    payload = services.build_guarded_execution_request_creation_payload(
        queue_handoff_id="manual_queue_handoff_abc123",
        reviewer_confirmation=True,
        execution_request_packet_payload={"execution_request_packet_status": "packet_ready_for_human_review"},
        execution_request_writer=lambda entry: calls.append(entry),
    )

    assert payload["execution_request_creation_status"] == "blocked_missing_approval_request_id"
    assert "approval_request_id_missing" in payload["blocked_actions"]
    assert calls == []
    _assert_execution_request_safety(payload, created=False)


def test_blocks_when_queue_handoff_id_is_missing():
    calls = []

    payload = services.build_guarded_execution_request_creation_payload(
        approval_request_id="manual_guarded_approval_123",
        reviewer_confirmation=True,
        execution_request_packet_payload={"execution_request_packet_status": "packet_ready_for_human_review"},
        execution_request_writer=lambda entry: calls.append(entry),
    )

    assert payload["execution_request_creation_status"] == "blocked_missing_queue_handoff_id"
    assert "queue_handoff_id_missing" in payload["blocked_actions"]
    assert calls == []
    _assert_execution_request_safety(payload, created=False)


def test_blocks_when_execution_request_packet_preview_is_missing_or_not_ready():
    calls = []
    missing = services.build_guarded_execution_request_creation_payload(
        approval_request_id="manual_guarded_approval_123",
        queue_handoff_id="manual_queue_handoff_abc123",
        reviewer_confirmation=True,
        execution_request_writer=lambda entry: calls.append(entry),
    )
    not_ready = services.build_guarded_execution_request_creation_payload(
        execution_request_packet_payload=_not_ready_packet(),
        reviewer_confirmation=True,
        execution_request_writer=lambda entry: calls.append(entry),
    )

    assert missing["execution_request_creation_status"] == "blocked_by_packet_preview"
    assert not_ready["execution_request_creation_status"] == "blocked_by_packet_preview"
    assert calls == []
    _assert_execution_request_safety(missing, created=False)
    _assert_execution_request_safety(not_ready, created=False)


def test_blocks_when_execution_request_writer_is_unavailable():
    payload = services.build_guarded_execution_request_creation_payload(
        execution_request_packet_payload=_ready_packet(),
        reviewer_confirmation=True,
    )

    assert payload["execution_request_creation_status"] == "blocked_missing_execution_request_writer"
    assert payload["execution_request_created"] is False
    assert "execution_request_writer_unavailable" in payload["blocked_actions"]
    _assert_execution_request_safety(payload, created=False)


def test_creates_exactly_one_execution_request_when_ready_confirmed_and_writer_exists():
    calls = []
    packet = _ready_packet()
    original_packet = deepcopy(packet)

    def fake_execution_request_writer(entry):
        calls.append(entry)
        return {"execution_request_id": entry["execution_request_id"], "persisted": True}

    payload = services.build_guarded_execution_request_creation_payload(
        execution_request_packet_payload=packet,
        reviewer_confirmation=True,
        reviewer_note="Create future execution request.",
        execution_request_writer=fake_execution_request_writer,
    )

    assert packet == original_packet
    assert payload["execution_request_creation_status"] == "created"
    assert payload["approval_request_id"] == "manual_guarded_approval_123"
    assert payload["queue_handoff_id"] == "manual_queue_handoff_abc123"
    assert payload["execution_request_created"] is True
    assert payload["execution_request_id"].startswith("manual_execution_request_")
    assert len(calls) == 1
    assert calls[0]["approval_request_id"] == "manual_guarded_approval_123"
    assert calls[0]["queue_handoff_id"] == "manual_queue_handoff_abc123"
    assert calls[0]["execute_application"] is False
    assert calls[0]["submit_application"] is False
    _assert_execution_request_safety(payload, created=True)


def test_can_build_packet_from_launch_gate_sources_before_blocking_on_missing_writer():
    payload = services.build_guarded_execution_request_creation_payload(
        reviewer_confirmation=True,
        execution_launch_gate_payload=_ready_launch_gate(),
        execution_launch_gate_observability_payload=_ready_launch_gate_observability(),
    )

    assert payload["source_execution_request_packet_status"] == "packet_ready_for_human_review"
    assert payload["execution_request_creation_status"] == "blocked_missing_execution_request_writer"
    _assert_execution_request_safety(payload, created=False)


def test_api_route_exists_as_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"POST"}


def test_api_route_blocks_without_execution_request_writer(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "execution_request_packet_payload": _ready_packet(),
            "reviewer_confirmation": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["api_surface"] == "manual_guarded_execution_request_create"
    assert payload["explicit_user_action"] is True
    assert payload["execution_request_creation_status"] == "blocked_missing_execution_request_writer"
    _assert_execution_request_safety(payload, created=False)


def test_api_route_slice_has_no_approval_status_resume_scoring_ranking_execution_or_submission_calls():
    source = Path("src/app/api.py").read_text()
    start = source.index("class ManualGuardedExecutionRequestCreateRequest")
    class_end = source.index("@asynccontextmanager")
    route_start = source.index('@app.post("/api/manual-guarded-execution-request-create")')
    route_end = source.index('@app.get("/api/agent-feedback")', route_start)
    snippet = source[start:class_end] + source[route_start:route_end]

    forbidden_markers = [
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


def test_service_helper_slice_limits_mutation_to_injected_execution_request_writer():
    source = Path("src/app/services.py").read_text()
    start = source.index("def build_guarded_execution_request_creation_payload")
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
    assert "execution_request_writer(" in snippet


def test_ui_renders_confirmation_control_and_escapes_output():
    source = Path("src/app/static/agentic_review.js").read_text()
    start = source.index("function renderManualGuardedExecutionRequestCreateSection")
    end = source.index("function renderAgentTraceReadOnlyPanel")
    snippet = source[start:end]

    assert "Manual Guarded Execution Request Creation" in snippet
    assert "Create Guarded Execution Request" in snippet
    assert "data-manual-guarded-execution-request-create" in snippet
    assert "data-manual-guarded-execution-request-create-confirmation" in snippet
    assert "escapeHtml(approvalRequestId)" in snippet
    assert "escapeHtml(queueHandoffId)" in snippet
    assert "escapeHtml(contextId)" in snippet
    assert "escapeHtml(jobId)" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Blocked actions\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Safety metadata\"" in snippet


def test_ui_click_posts_endpoint_and_existing_execution_request_packet_preview_still_works():
    source = Path("src/app/static/agentic_review.js").read_text()

    assert source.count("/api/manual-guarded-execution-request-create") == 1
    assert "manual_guarded_execution_request_create_result" in source
    assert "renderManualGuardedExecutionRequestCreateSection(tracePayload)" in source
    assert source.count("/api/manual-execution-request-packet-preview-dry-run") == 1
    assert "manual_execution_request_packet_preview_result" in source
    assert "renderManualExecutionRequestPacketPreviewSection(tracePayload)" in source
