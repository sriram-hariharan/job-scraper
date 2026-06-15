from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services


ENDPOINT = "/api/manual-review-packet-preview-dry-run"


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _action_plan_payload(planned_action: str = "prepare_review_packet") -> dict:
    return {
        "action_plan_status": "ready_for_human_confirmation",
        "source_reviewer_decision": "accept_recommendation_for_review",
        "source_recommendation_action": "tailor_first",
        "planned_action": planned_action,
        "planned_action_label": "Prepare review packet",
        "action_steps": ["Collect shadow recommendation and safety metadata."],
        "blocked_actions": [],
        "required_human_confirmation": True,
        "next_safe_step": "prepare_review_packet_for_human_confirmation",
        "context_id": "ctx-1",
        "job_id": "job-1",
    }


def _assert_packet_safety(payload: dict) -> None:
    safety = payload["safety_metadata"]
    assert payload["read_only"] is True
    assert payload["manual_surface"] is True
    assert safety["dry_run_only"] is True
    assert safety["review_packet_preview_only"] is True
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


def test_helper_builds_packet_preview_for_prepare_review_packet():
    source = _action_plan_payload("prepare_review_packet")
    original = deepcopy(source)

    payload = services.build_review_packet_preview_dry_run_payload(
        action_plan_payload=source,
        shadow_chain_payload={
            "stage_statuses": {
                "jd_intelligence": "validated",
                "resume_match": "strong_match",
            }
        },
    )

    assert source == original
    assert payload["review_packet_status"] == "ready_for_review"
    assert payload["source_planned_action"] == "prepare_review_packet"
    assert payload["packet_title"] == "Review packet preview"
    assert payload["packet_sections"]
    assert payload["reviewer_checklist"]
    assert payload["included_stage_summaries"]["resume_match"] == "strong_match"
    _assert_packet_safety(payload)


def test_helper_builds_safe_packet_preview_for_other_planned_actions():
    expected_statuses = {
        "request_tailoring_revision": "revision_review_preview",
        "save_for_later": "save_for_later_preview",
        "dismiss_recommendation": "dismissal_preview",
    }

    for planned_action, expected_status in expected_statuses.items():
        payload = services.build_review_packet_preview_dry_run_payload(
            action_plan_payload=_action_plan_payload(planned_action),
        )

        assert payload["review_packet_status"] == expected_status
        assert payload["source_planned_action"] == planned_action
        assert payload["packet_sections"]
        _assert_packet_safety(payload)


def test_helper_missing_or_invalid_action_plan_returns_safe_fallback():
    missing = services.build_review_packet_preview_dry_run_payload(action_plan_payload={})
    invalid = services.build_review_packet_preview_dry_run_payload(
        action_plan_payload=_action_plan_payload("submit_application_now"),
    )

    assert missing["review_packet_status"] in {"insufficient_information", "invalid_action_plan"}
    assert missing["required_human_confirmation"] is True
    assert invalid["review_packet_status"] == "invalid_action_plan"
    assert invalid["packet_sections"] == []
    assert "invalid_planned_action" in invalid["blocked_actions"]
    _assert_packet_safety(missing)
    _assert_packet_safety(invalid)


def test_api_route_exists_as_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"POST"}


def test_api_route_returns_readonly_review_packet_preview(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "action_plan_payload": _action_plan_payload("prepare_review_packet"),
            "shadow_chain_payload": {
                "stage_statuses": {
                    "critic_guardrail": "approved",
                    "strategy_recommendation": "tailor_first",
                }
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["api_surface"] == "manual_review_packet_preview_dry_run"
    assert payload["explicit_user_action"] is True
    assert payload["review_packet_status"] == "ready_for_review"
    assert payload["included_stage_summaries"]["critic_guardrail"] == "approved"
    _assert_packet_safety(payload)


def test_api_route_slice_has_no_storage_scoring_queue_approval_execution_or_llm_calls():
    source = Path("src/app/api.py").read_text()
    start = source.index("class ManualReviewPacketPreviewDryRunRequest")
    class_end = source.index("@asynccontextmanager")
    route_start = source.index('@app.post("/api/manual-review-packet-preview-dry-run")')
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
    start = source.index("def build_review_packet_preview_dry_run_payload")
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
        "create_approval(",
        "create_approval_request(",
        "operator_decision",
    ]
    for marker in forbidden_markers:
        assert marker not in snippet


def test_ui_renders_and_escapes_packet_preview_output():
    source = Path("src/app/static/agentic_review.js").read_text()
    start = source.index("function renderManualReviewPacketPreviewDryRunSection")
    end = source.index("function renderAgentTraceReadOnlyPanel")
    snippet = source[start:end]

    assert "Manual Review Packet Preview Dry-run" in snippet
    assert "Build Review Packet Preview" in snippet
    assert "data-manual-review-packet-preview-dry-run" in snippet
    assert "escapeHtml(contextId)" in snippet
    assert "escapeHtml(jobId)" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Packet title\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Packet sections\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Reviewer checklist\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Safety metadata\"" in snippet


def test_ui_click_posts_endpoint_and_existing_action_plan_surface_still_exists():
    source = Path("src/app/static/agentic_review.js").read_text()

    assert source.count("/api/manual-review-packet-preview-dry-run") == 1
    assert source.count("data-manual-review-packet-preview-dry-run") == 4
    assert "manual_review_packet_preview_dry_run_result" in source
    assert "renderManualReviewPacketPreviewDryRunSection(tracePayload)" in source
    assert source.count("/api/manual-human-approved-action-plan-dry-run") == 1
    assert "renderManualHumanApprovedActionPlanDryRunSection(tracePayload)" in source
