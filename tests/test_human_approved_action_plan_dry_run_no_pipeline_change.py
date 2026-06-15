from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services


ENDPOINT = "/api/manual-human-approved-action-plan-dry-run"


DECISION_TO_ACTION = {
    "accept_recommendation_for_review": "prepare_review_packet",
    "request_more_tailoring": "request_tailoring_revision",
    "save_for_later": "save_for_later",
    "dismiss_shadow_recommendation": "dismiss_recommendation",
}


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _decision_capture_payload(decision: str = "accept_recommendation_for_review") -> dict:
    return {
        "decision_capture_status": "captured_for_review",
        "reviewer_decision": decision,
        "reviewer_note": "Looks reasonable <review>",
        "accepted_decision": decision in DECISION_TO_ACTION,
        "next_review_action": "review_shadow_recommendation",
        "source_recommendation_action": "tailor_first",
        "source_handoff_status": "ready_for_human_review",
        "required_human_review": True,
        "blocking_risks": [] if decision in DECISION_TO_ACTION else ["invalid_reviewer_decision"],
        "improvement_actions": ["Review approved tailoring suggestions before applying."],
        "context_id": "ctx-1",
        "job_id": "job-1",
    }


def _assert_action_plan_safety(payload: dict) -> None:
    safety = payload["safety_metadata"]
    assert payload["read_only"] is True
    assert payload["manual_surface"] is True
    assert safety["dry_run_only"] is True
    assert safety["action_plan_only"] is True
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


def test_helper_maps_each_valid_reviewer_decision_to_planned_action():
    for decision, expected_action in DECISION_TO_ACTION.items():
        source = _decision_capture_payload(decision)
        original = deepcopy(source)

        payload = services.build_human_approved_action_plan_dry_run_payload(
            decision_capture_payload=source,
        )

        assert source == original
        assert payload["action_plan_status"] == "ready_for_human_confirmation"
        assert payload["source_reviewer_decision"] == decision
        assert payload["planned_action"] == expected_action
        assert payload["required_human_confirmation"] is True
        assert payload["action_steps"]
        _assert_action_plan_safety(payload)


def test_helper_invalid_decision_returns_safe_no_action():
    payload = services.build_human_approved_action_plan_dry_run_payload(
        decision_capture_payload=_decision_capture_payload("approve_and_submit"),
    )

    assert payload["action_plan_status"] == "invalid_reviewer_decision"
    assert payload["planned_action"] == "no_action_invalid_decision"
    assert payload["action_steps"] == []
    assert "invalid_reviewer_decision" in payload["blocked_actions"]
    _assert_action_plan_safety(payload)


def test_helper_missing_decision_returns_insufficient_information():
    payload = services.build_human_approved_action_plan_dry_run_payload(
        decision_capture_payload={},
    )

    assert payload["action_plan_status"] in {"insufficient_information", "invalid_reviewer_decision"}
    assert payload["planned_action"] in {"insufficient_information", "no_action_invalid_decision"}
    assert payload["required_human_confirmation"] is True
    _assert_action_plan_safety(payload)


def test_api_route_exists_as_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"POST"}


def test_api_route_returns_readonly_action_plan_payload(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "decision_capture_payload": _decision_capture_payload("request_more_tailoring"),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["api_surface"] == "manual_human_approved_action_plan_dry_run"
    assert payload["explicit_user_action"] is True
    assert payload["planned_action"] == "request_tailoring_revision"
    _assert_action_plan_safety(payload)


def test_api_route_slice_has_no_storage_scoring_queue_approval_execution_or_llm_calls():
    source = Path("src/app/api.py").read_text()
    start = source.index("class ManualHumanApprovedActionPlanDryRunRequest")
    class_end = source.index("@asynccontextmanager")
    route_start = source.index('@app.post("/api/manual-human-approved-action-plan-dry-run")')
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
    start = source.index("def build_human_approved_action_plan_dry_run_payload")
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


def test_ui_renders_and_escapes_action_plan_output():
    source = Path("src/app/static/agentic_review.js").read_text()
    start = source.index("function renderManualHumanApprovedActionPlanDryRunSection")
    end = source.index("function renderAgentTraceReadOnlyPanel")
    snippet = source[start:end]

    assert "Manual Human-approved Action Plan Dry-run" in snippet
    assert "Build Action Plan Dry-run" in snippet
    assert "data-manual-human-approved-action-plan-dry-run" in snippet
    assert "escapeHtml(contextId)" in snippet
    assert "escapeHtml(jobId)" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Planned action label\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Action steps\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Blocked actions\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Safety metadata\"" in snippet


def test_ui_click_posts_endpoint_and_existing_human_decision_surface_still_exists():
    source = Path("src/app/static/agentic_review.js").read_text()

    assert source.count("/api/manual-human-approved-action-plan-dry-run") == 1
    assert source.count("data-manual-human-approved-action-plan-dry-run") == 4
    assert "manual_human_approved_action_plan_dry_run_result" in source
    assert "renderManualHumanApprovedActionPlanDryRunSection(tracePayload)" in source
    assert source.count("/api/manual-human-decision-capture-dry-run") == 1
    assert "renderManualHumanDecisionCaptureDryRunSection(tracePayload)" in source
