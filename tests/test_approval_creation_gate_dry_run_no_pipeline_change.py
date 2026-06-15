from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services


ENDPOINT = "/api/manual-approval-creation-gate-dry-run"


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _approval_preview_payload(status: str = "ready_for_approval_preview") -> dict:
    return {
        "approval_preview_status": status,
        "approval_preview_type": "review_packet_approval_preview",
        "approval_title": "Review packet approval preview",
        "approval_summary": "Preview <approval> fields only.",
        "proposed_decision": "request_human_review",
        "proposed_next_step": "human_reviewer_confirms_review_packet",
        "required_reviewer_confirmation": True,
        "approval_fields_preview": {
            "title": "Review packet approval preview",
            "source_planned_action": "prepare_review_packet",
            "source_review_packet_status": "ready_for_review",
        },
        "blocked_actions": [],
        "source_review_packet_status": "ready_for_review",
        "context_id": "ctx-1",
        "job_id": "job-1",
        "safety_metadata": {
            "dry_run_only": True,
            "approval_preview_only": True,
            "review_only": True,
            "human_confirmation_required": True,
            "did_create_approval": False,
            "did_mutate_approval": False,
            "did_mutate_queue": False,
            "did_mutate_resume": False,
            "did_mutate_scoring": False,
            "did_change_ranking": False,
            "did_execute_application": False,
            "did_submit_application": False,
            "pipeline_wiring_added": False,
            "advisory_only": True,
        },
    }


def _assert_gate_safety(payload: dict) -> None:
    safety = payload["safety_metadata"]
    assert payload["read_only"] is True
    assert payload["manual_surface"] is True
    assert safety["dry_run_only"] is True
    assert safety["approval_creation_gate_only"] is True
    assert safety["approval_preview_only"] is False
    assert safety["review_only"] is True
    assert safety["human_confirmation_required"] is True
    assert safety["did_create_approval"] is False
    assert safety["did_mutate_approval"] is False
    assert safety["did_mutate_queue"] is False
    assert safety["did_mutate_resume"] is False
    assert safety["did_mutate_scoring"] is False
    assert safety["did_change_ranking"] is False
    assert safety["did_execute_application"] is False
    assert safety["did_submit_application"] is False
    assert safety["pipeline_wiring_added"] is False
    assert safety["advisory_only"] is True


def test_valid_preview_without_confirmation_needs_reviewer_confirmation():
    source = _approval_preview_payload()
    original = deepcopy(source)

    payload = services.build_approval_creation_gate_dry_run_payload(
        approval_preview_payload=source,
        reviewer_confirmation=False,
    )

    assert source == original
    assert payload["approval_creation_gate_status"] == "waiting_for_confirmation"
    assert payload["gate_decision"] == "needs_reviewer_confirmation"
    assert payload["can_create_approval_request_later"] is False
    assert "reviewer_confirmation" in payload["missing_requirements"]
    _assert_gate_safety(payload)


def test_valid_preview_with_confirmation_is_ready_for_future_creation():
    payload = services.build_approval_creation_gate_dry_run_payload(
        approval_preview_payload=_approval_preview_payload(),
        reviewer_confirmation=True,
    )

    assert payload["approval_creation_gate_status"] == "ready"
    assert payload["gate_decision"] == "ready_for_future_approval_creation"
    assert payload["can_create_approval_request_later"] is True
    assert payload["missing_requirements"] == []
    _assert_gate_safety(payload)


def test_missing_or_invalid_preview_returns_safe_blocker():
    missing = services.build_approval_creation_gate_dry_run_payload(
        approval_preview_payload={},
        reviewer_confirmation=True,
    )
    invalid = services.build_approval_creation_gate_dry_run_payload(
        approval_preview_payload=_approval_preview_payload("invalid_source_action"),
        reviewer_confirmation=True,
    )

    assert missing["gate_decision"] in {"blocked_by_missing_preview", "blocked_by_invalid_preview"}
    assert missing["can_create_approval_request_later"] is False
    assert invalid["gate_decision"] == "blocked_by_invalid_preview"
    assert invalid["can_create_approval_request_later"] is False
    assert "approval_preview_invalid" in invalid["blocked_actions"]
    _assert_gate_safety(missing)
    _assert_gate_safety(invalid)


def test_safety_risk_blocks_gate():
    preview = _approval_preview_payload()
    preview["safety_metadata"]["did_mutate_approval"] = True

    payload = services.build_approval_creation_gate_dry_run_payload(
        approval_preview_payload=preview,
        reviewer_confirmation=True,
    )

    assert payload["gate_decision"] == "blocked_by_safety_risk"
    assert payload["can_create_approval_request_later"] is False
    assert "approval_preview_safety_risk" in payload["blocked_actions"]
    _assert_gate_safety(payload)


def test_api_route_exists_as_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"POST"}


def test_api_route_returns_readonly_gate_payload(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "approval_preview_payload": _approval_preview_payload(),
            "reviewer_confirmation": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["api_surface"] == "manual_approval_creation_gate_dry_run"
    assert payload["explicit_user_action"] is True
    assert payload["gate_decision"] == "ready_for_future_approval_creation"
    _assert_gate_safety(payload)


def test_api_route_slice_has_no_storage_scoring_queue_approval_execution_or_llm_calls():
    source = Path("src/app/api.py").read_text()
    start = source.index("class ManualApprovalCreationGateDryRunRequest")
    class_end = source.index("@asynccontextmanager")
    route_start = source.index('@app.post("/api/manual-approval-creation-gate-dry-run")')
    route_end = source.index(
        '@app.post(\n    "/api/agentic-approvals/{approval_request_id}/production-scheduler-observability-reporting-job"'
    )
    snippet = source[start:class_end] + source[route_start:route_end]

    forbidden_markers = [
        "FileResponse(",
        "StreamingResponse(",
        "open(",
        ".write(",
        "write_text",
        "write_bytes",
        "send_file",
        "subprocess",
        "background_tasks.add_task",
        "Thread(",
        "Process(",
        "get_agentic_approval_store",
        "_agentic_approval_storage_connection",
        "cursor.execute",
        ".commit(",
        "src.storage",
        "schema.sql",
        "migration_runner",
        "application_execution_queue",
        "create_approval_request(",
        "submit_application(",
        "execute_application(",
        "score_resume_job_match",
        "ranking_state",
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


def test_service_helper_slice_has_no_storage_scoring_queue_approval_or_pipeline_wiring_calls():
    source = Path("src/app/services.py").read_text()
    start = source.index("def build_approval_creation_gate_dry_run_payload")
    end = source.index("def _artifact_row_by_name")
    snippet = source[start:end]

    forbidden_markers = [
        "insert_",
        "get_rag_job_documents",
        "cursor.execute",
        ".commit(",
        "subprocess",
        "requests.",
        "httpx.",
        "run_chat_completion",
        "score_resume_job_match",
        "ranking_state",
        "ranking_update",
        "ranking_mutation",
        "application_execution_queue",
        "execute_application(",
        "submit_application(",
        "workflow_runner",
        "create_approval_request(",
        "operator_decision",
    ]
    for marker in forbidden_markers:
        assert marker not in snippet


def test_ui_renders_and_escapes_gate_output():
    source = Path("src/app/static/agentic_review.js").read_text()
    start = source.index("function renderManualApprovalCreationGateDryRunSection")
    end = source.index("function renderAgentTraceReadOnlyPanel")
    snippet = source[start:end]

    assert "Manual Approval Creation Gate Dry-run" in snippet
    assert "Check Approval Creation Gate" in snippet
    assert "data-manual-approval-creation-gate-dry-run" in snippet
    assert "data-manual-approval-creation-gate-confirmation" in snippet
    assert "escapeHtml(contextId)" in snippet
    assert "escapeHtml(jobId)" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Missing requirements\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Blocked actions\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Safety metadata\"" in snippet


def test_ui_click_posts_endpoint_and_existing_approval_preview_surface_still_exists():
    source = Path("src/app/static/agentic_review.js").read_text()

    assert source.count("/api/manual-approval-creation-gate-dry-run") == 1
    assert source.count("data-manual-approval-creation-gate-dry-run") == 4
    assert "manual_approval_creation_gate_dry_run_result" in source
    assert "renderManualApprovalCreationGateDryRunSection(tracePayload)" in source
    assert source.count("/api/manual-approval-request-preview-dry-run") == 1
    assert "renderManualApprovalRequestPreviewDryRunSection(tracePayload)" in source
