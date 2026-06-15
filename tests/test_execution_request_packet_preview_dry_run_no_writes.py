from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services


ENDPOINT = "/api/manual-execution-request-packet-preview-dry-run"


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _ready_launch_gate_payload() -> dict:
    return {
        "execution_launch_gate_status": "ready_for_future_manual_execution",
        "approval_request_id": "manual_guarded_approval_123",
        "queue_handoff_id": "manual_queue_handoff_abc123",
        "execution_launch_allowed_later": True,
        "ready_for_future_manual_execution": True,
        "blocked_actions": [],
        "next_safe_step": "collect_explicit_future_manual_execution_confirmation",
        "context_id": "ctx-1",
        "job_id": "job-1",
        "safety_metadata": {
            "did_execute_application": False,
            "did_submit_application": False,
            "did_mutate_queue": False,
            "did_write_queue": False,
        },
    }


def _blocked_launch_gate_payload() -> dict:
    payload = _ready_launch_gate_payload()
    payload.update(
        {
            "execution_launch_gate_status": "blocked_execution_not_ready",
            "execution_launch_allowed_later": False,
            "ready_for_future_manual_execution": False,
            "blocked_actions": ["execution_readiness_not_ready"],
            "next_safe_step": "resolve_execution_launch_gate_blockers",
        }
    )
    return payload


def _ready_launch_gate_observability_payload() -> dict:
    return {
        "execution_launch_gate_observability_status": "observed_ready",
        "source_execution_launch_gate_status": "ready_for_future_manual_execution",
        "approval_request_id": "manual_guarded_approval_123",
        "queue_handoff_id": "manual_queue_handoff_abc123",
        "future_manual_execution_allowed": True,
        "execution_launch_was_blocked": False,
        "execution_launch_was_allowed_later": True,
        "blocked_actions": [],
        "next_safe_step": "collect_explicit_future_manual_execution_confirmation",
        "context_id": "ctx-1",
        "job_id": "job-1",
        "safety_metadata": {
            "did_execute_application": False,
            "did_submit_application": False,
            "did_mutate_queue": False,
            "did_write_queue": False,
        },
    }


def _blocked_launch_gate_observability_payload() -> dict:
    payload = _ready_launch_gate_observability_payload()
    payload.update(
        {
            "execution_launch_gate_observability_status": "observed_blocked",
            "source_execution_launch_gate_status": "blocked_execution_not_ready",
            "future_manual_execution_allowed": False,
            "execution_launch_was_blocked": True,
            "execution_launch_was_allowed_later": False,
            "blocked_actions": ["execution_readiness_not_ready"],
        }
    )
    return payload


def _assert_packet_safety(payload: dict) -> None:
    safety = payload["safety_metadata"]
    assert payload["manual_surface"] is True
    assert payload["read_only"] is True
    assert safety["dry_run_only"] is True
    assert safety["execution_request_packet_preview_only"] is True
    assert safety["manual_only"] is True
    assert safety["read_only"] is True
    assert safety["human_review_required"] is True
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
    payload = services.build_execution_request_packet_preview_payload(
        queue_handoff_id="manual_queue_handoff_abc123",
    )

    assert payload["execution_request_packet_status"] == "blocked_missing_approval_request_id"
    assert "approval_request_id" in payload["missing_requirements"]
    assert "approval_request_id_missing" in payload["blocked_actions"]
    _assert_packet_safety(payload)


def test_helper_blocks_missing_queue_handoff_id():
    payload = services.build_execution_request_packet_preview_payload(
        approval_request_id="manual_guarded_approval_123",
    )

    assert payload["execution_request_packet_status"] == "blocked_missing_queue_handoff_id"
    assert "queue_handoff_id" in payload["missing_requirements"]
    assert "queue_handoff_id_missing" in payload["blocked_actions"]
    _assert_packet_safety(payload)


def test_helper_blocks_missing_or_invalid_execution_launch_gate():
    missing = services.build_execution_request_packet_preview_payload(
        approval_request_id="manual_guarded_approval_123",
        queue_handoff_id="manual_queue_handoff_abc123",
        execution_launch_gate_observability_payload=_ready_launch_gate_observability_payload(),
    )
    invalid = services.build_execution_request_packet_preview_payload(
        execution_launch_gate_payload={
            "execution_launch_gate_status": "surprising_state",
            "approval_request_id": "manual_guarded_approval_123",
            "queue_handoff_id": "manual_queue_handoff_abc123",
        },
        execution_launch_gate_observability_payload=_ready_launch_gate_observability_payload(),
    )

    assert missing["execution_request_packet_status"] == "blocked_missing_execution_launch_gate"
    assert "execution_launch_gate_missing" in missing["blocked_actions"]
    assert invalid["execution_request_packet_status"] == "blocked_execution_launch_not_ready"
    assert "execution_launch_gate_not_ready" in invalid["blocked_actions"]
    _assert_packet_safety(missing)
    _assert_packet_safety(invalid)


def test_helper_blocks_when_launch_gate_is_not_ready():
    payload = services.build_execution_request_packet_preview_payload(
        execution_launch_gate_payload=_blocked_launch_gate_payload(),
        execution_launch_gate_observability_payload=_ready_launch_gate_observability_payload(),
    )

    assert payload["execution_request_packet_status"] == "blocked_execution_launch_not_ready"
    assert "ready_execution_launch_gate" in payload["missing_requirements"]
    assert "execution_readiness_not_ready" in payload["blocked_actions"]
    _assert_packet_safety(payload)


def test_helper_blocks_missing_or_invalid_execution_launch_gate_observability():
    missing = services.build_execution_request_packet_preview_payload(
        execution_launch_gate_payload=_ready_launch_gate_payload(),
    )
    invalid = services.build_execution_request_packet_preview_payload(
        execution_launch_gate_payload=_ready_launch_gate_payload(),
        execution_launch_gate_observability_payload=_blocked_launch_gate_observability_payload(),
    )

    assert missing["execution_request_packet_status"] == "blocked_missing_execution_launch_observability"
    assert "execution_launch_gate_observability_missing" in missing["blocked_actions"]
    assert invalid["execution_request_packet_status"] == "blocked_missing_execution_launch_observability"
    assert "execution_launch_gate_observability_not_ready" in invalid["blocked_actions"]
    _assert_packet_safety(missing)
    _assert_packet_safety(invalid)


def test_helper_returns_packet_ready_for_human_review_when_all_evidence_ready():
    payload = services.build_execution_request_packet_preview_payload(
        execution_launch_gate_payload=_ready_launch_gate_payload(),
        execution_launch_gate_observability_payload=_ready_launch_gate_observability_payload(),
        reviewer_note="<review this safely>",
    )

    assert payload["execution_request_packet_status"] == "packet_ready_for_human_review"
    assert payload["packet_ready_for_human_review"] is True
    assert payload["approval_request_id"] == "manual_guarded_approval_123"
    assert payload["queue_handoff_id"] == "manual_queue_handoff_abc123"
    assert payload["source_execution_launch_gate_status"] == "ready_for_future_manual_execution"
    assert payload["source_execution_launch_gate_observability_status"] == "observed_ready"
    assert payload["packet_sections"][-1]["section_id"] == "reviewer_note"
    _assert_packet_safety(payload)


def test_packet_sections_are_deterministic():
    first = services.build_execution_request_packet_preview_payload(
        execution_launch_gate_payload=_ready_launch_gate_payload(),
        execution_launch_gate_observability_payload=_ready_launch_gate_observability_payload(),
    )
    second = services.build_execution_request_packet_preview_payload(
        execution_launch_gate_payload=_ready_launch_gate_payload(),
        execution_launch_gate_observability_payload=_ready_launch_gate_observability_payload(),
    )

    assert first["packet_sections"] == second["packet_sections"]
    assert [section["section_id"] for section in first["packet_sections"]] == [
        "source_ids",
        "launch_gate",
        "launch_gate_audit",
        "human_review",
    ]


def test_api_route_exists_as_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"POST"}


def test_api_route_returns_dry_run_readonly_packet_preview(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "execution_launch_gate_payload": _ready_launch_gate_payload(),
            "execution_launch_gate_observability_payload": _ready_launch_gate_observability_payload(),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["api_surface"] == "manual_execution_request_packet_preview_dry_run"
    assert payload["explicit_user_action"] is True
    assert payload["execution_request_packet_status"] == "packet_ready_for_human_review"
    _assert_packet_safety(payload)


def test_api_route_slice_has_no_execution_submission_queue_write_or_mutation_calls():
    source = Path("src/app/api.py").read_text()
    start = source.index("class ManualExecutionRequestPacketPreviewRequest")
    class_end = source.index("@asynccontextmanager")
    route_start = source.index('@app.post("/api/manual-execution-request-packet-preview-dry-run")')
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
    start = source.index("def build_execution_request_packet_preview_payload")
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


def test_ui_renders_packet_preview_button_and_escapes_output():
    source = Path("src/app/static/agentic_review.js").read_text()
    start = source.index("function renderManualExecutionRequestPacketPreviewSection")
    end = source.index("function renderAgentTraceReadOnlyPanel")
    snippet = source[start:end]

    assert "Manual Execution Request Packet Preview" in snippet
    assert "Preview Execution Request Packet" in snippet
    assert "data-manual-execution-request-packet-preview" in snippet
    assert "escapeHtml(approvalRequestId)" in snippet
    assert "escapeHtml(queueHandoffId)" in snippet
    assert "escapeHtml(contextId)" in snippet
    assert "escapeHtml(jobId)" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Execution request summary\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Packet sections\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Safety metadata\"" in snippet


def test_ui_click_posts_endpoint_and_existing_execution_launch_gate_audit_still_works():
    source = Path("src/app/static/agentic_review.js").read_text()

    assert source.count("/api/manual-execution-request-packet-preview-dry-run") == 1
    assert "manual_execution_request_packet_preview_result" in source
    assert "renderManualExecutionRequestPacketPreviewSection(tracePayload)" in source
    assert source.count("/api/manual-execution-launch-gate-observability") == 1
    assert "manual_execution_launch_gate_observability_result" in source
    assert "renderManualExecutionLaunchGateObservabilitySection(tracePayload)" in source
