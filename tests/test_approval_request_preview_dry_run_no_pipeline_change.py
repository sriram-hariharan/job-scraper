from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services


ENDPOINT = "/api/manual-approval-request-preview-dry-run"


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _review_packet_payload(source_planned_action: str = "prepare_review_packet") -> dict:
    return {
        "review_packet_status": "ready_for_review",
        "source_planned_action": source_planned_action,
        "packet_title": "Review packet preview",
        "packet_sections": [{"section_id": "summary", "heading": "Summary", "items": ["Review <safe>"]}],
        "reviewer_checklist": ["Confirm safety metadata."],
        "included_stage_summaries": {"critic_guardrail": "approved"},
        "blocked_actions": [],
        "required_human_confirmation": True,
        "next_safe_step": "review_packet_with_human_confirmation",
        "context_id": "ctx-1",
        "job_id": "job-1",
    }


def _assert_approval_preview_safety(payload: dict) -> None:
    safety = payload["safety_metadata"]
    assert payload["read_only"] is True
    assert payload["manual_surface"] is True
    assert safety["dry_run_only"] is True
    assert safety["approval_preview_only"] is True
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


def test_helper_builds_approval_preview_from_review_packet_preview():
    source = _review_packet_payload("prepare_review_packet")
    original = deepcopy(source)

    payload = services.build_approval_request_preview_dry_run_payload(
        review_packet_payload=source,
    )

    assert source == original
    assert payload["approval_preview_status"] == "ready_for_approval_preview"
    assert payload["approval_preview_type"] == "review_packet_approval_preview"
    assert payload["approval_title"] == "Review packet approval preview"
    assert payload["proposed_decision"] == "request_human_review"
    assert payload["required_reviewer_confirmation"] is True
    assert payload["approval_fields_preview"]["packet_title"] == "Review packet preview"
    assert payload["source_review_packet_status"] == "ready_for_review"
    _assert_approval_preview_safety(payload)


def test_helper_builds_safe_previews_for_other_source_actions():
    expected_statuses = {
        "request_tailoring_revision": "tailoring_revision_approval_preview",
        "save_for_later": "save_for_later_approval_preview",
        "dismiss_recommendation": "dismissal_approval_preview",
    }

    for source_action, expected_status in expected_statuses.items():
        payload = services.build_approval_request_preview_dry_run_payload(
            review_packet_payload=_review_packet_payload(source_action),
        )

        assert payload["approval_preview_status"] == expected_status
        assert payload["approval_fields_preview"]["source_planned_action"] == source_action
        assert payload["required_reviewer_confirmation"] is True
        _assert_approval_preview_safety(payload)


def test_helper_missing_or_invalid_source_returns_safe_fallback():
    missing = services.build_approval_request_preview_dry_run_payload(review_packet_payload={})
    invalid = services.build_approval_request_preview_dry_run_payload(
        review_packet_payload=_review_packet_payload("submit_now"),
    )

    assert missing["approval_preview_status"] in {"insufficient_information", "invalid_source_action"}
    assert missing["required_reviewer_confirmation"] is True
    assert invalid["approval_preview_status"] == "invalid_source_action"
    assert invalid["proposed_decision"] == "no_approval_preview"
    assert "invalid_source_planned_action" in invalid["blocked_actions"]
    _assert_approval_preview_safety(missing)
    _assert_approval_preview_safety(invalid)


def test_api_route_exists_as_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"POST"}


def test_api_route_returns_readonly_approval_preview(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={"review_packet_payload": _review_packet_payload("request_tailoring_revision")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["api_surface"] == "manual_approval_request_preview_dry_run"
    assert payload["explicit_user_action"] is True
    assert payload["approval_preview_status"] == "tailoring_revision_approval_preview"
    assert payload["approval_fields_preview"]["included_stage_summaries"]["critic_guardrail"] == "approved"
    _assert_approval_preview_safety(payload)


def test_api_route_slice_has_no_storage_scoring_queue_approval_execution_or_llm_calls():
    source = Path("src/app/api.py").read_text()
    start = source.index("class ManualApprovalRequestPreviewDryRunRequest")
    class_end = source.index("@asynccontextmanager")
    route_start = source.index('@app.post("/api/manual-approval-request-preview-dry-run")')
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
    start = source.index("def build_approval_request_preview_dry_run_payload")
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


def test_ui_renders_and_escapes_approval_preview_output():
    source = Path("src/app/static/agentic_review.js").read_text()
    start = source.index("function renderManualApprovalRequestPreviewDryRunSection")
    end = source.index("function renderAgentTraceReadOnlyPanel")
    snippet = source[start:end]

    assert "Manual Approval Request Preview Dry-run" in snippet
    assert "Preview Approval Request" in snippet
    assert "data-manual-approval-request-preview-dry-run" in snippet
    assert "escapeHtml(contextId)" in snippet
    assert "escapeHtml(jobId)" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Approval title\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Approval summary\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Approval fields preview\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Safety metadata\"" in snippet


def test_ui_click_posts_endpoint_and_existing_review_packet_surface_still_exists():
    source = Path("src/app/static/agentic_review.js").read_text()

    assert source.count("/api/manual-approval-request-preview-dry-run") == 1
    assert source.count("data-manual-approval-request-preview-dry-run") == 4
    assert "manual_approval_request_preview_dry_run_result" in source
    assert "renderManualApprovalRequestPreviewDryRunSection(tracePayload)" in source
    assert source.count("/api/manual-review-packet-preview-dry-run") == 1
    assert "renderManualReviewPacketPreviewDryRunSection(tracePayload)" in source
