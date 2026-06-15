from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services


ENDPOINT = "/api/manual-human-decision-capture-dry-run"
VALID_DECISIONS = [
    "accept_recommendation_for_review",
    "request_more_tailoring",
    "save_for_later",
    "dismiss_shadow_recommendation",
]


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _handoff_payload() -> dict:
    return {
        "handoff_status": "ready_for_human_review",
        "recommendation_action": "tailor_first",
        "recommendation_label": "strong_match_with_approved_tailoring",
        "required_human_review": True,
        "reviewer_decision_options": list(VALID_DECISIONS),
        "blocking_risks": [],
        "improvement_actions": ["Review approved tailoring suggestions before applying."],
        "stage_statuses": {
            "resume_match": "strong_match",
            "critic_guardrail": "approved",
            "strategy_recommendation": "ready",
        },
        "confidence": 0.91,
        "source_shadow_chain_status": "completed",
        "context_id": "ctx-1",
        "job_id": "job-1",
        "safety_metadata": {
            "dry_run_only": True,
            "review_only": True,
            "human_gate_required": True,
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


def _assert_decision_safety(payload: dict) -> None:
    safety = payload["safety_metadata"]
    assert payload["read_only"] is True
    assert payload["manual_surface"] is True
    assert safety["dry_run_only"] is True
    assert safety["decision_capture_only"] is True
    assert safety["review_only"] is True
    assert safety["human_gate_required"] is True
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


def test_helper_accepts_each_valid_reviewer_decision():
    for decision in VALID_DECISIONS:
        handoff = _handoff_payload()
        original = deepcopy(handoff)

        payload = services.build_human_decision_capture_dry_run_payload(
            handoff_payload=handoff,
            reviewer_decision=decision,
            reviewer_note="Looks reasonable <review>",
        )

        assert handoff == original
        assert payload["decision_capture_status"] == "captured_for_review"
        assert payload["reviewer_decision"] == decision
        assert payload["reviewer_note"] == "Looks reasonable <review>"
        assert payload["accepted_decision"] is True
        assert payload["required_human_review"] is True
        assert payload["source_recommendation_action"] == "tailor_first"
        assert payload["source_handoff_status"] == "ready_for_human_review"
        _assert_decision_safety(payload)


def test_helper_invalid_reviewer_decision_returns_safe_invalid_status():
    payload = services.build_human_decision_capture_dry_run_payload(
        handoff_payload=_handoff_payload(),
        reviewer_decision="approve_and_submit",
    )

    assert payload["decision_capture_status"] == "invalid_reviewer_decision"
    assert payload["accepted_decision"] is False
    assert payload["next_review_action"] == "no_action_invalid_decision"
    assert "invalid_reviewer_decision" in payload["blocking_risks"]
    _assert_decision_safety(payload)


def test_helper_missing_handoff_output_returns_safe_fallback():
    payload = services.build_human_decision_capture_dry_run_payload(
        handoff_payload={},
        reviewer_decision="save_for_later",
    )

    assert payload["decision_capture_status"] == "captured_with_blockers"
    assert payload["accepted_decision"] is True
    assert payload["source_recommendation_action"] == "insufficient_information"
    assert "resume_match_payload_missing" in payload["blocking_risks"]
    assert "critic_guardrail_payload_missing" in payload["blocking_risks"]
    _assert_decision_safety(payload)


def test_api_route_exists_as_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"POST"}


def test_api_route_returns_readonly_decision_capture_payload(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "handoff_payload": _handoff_payload(),
            "reviewer_decision": "request_more_tailoring",
            "reviewer_note": "Need stronger tailoring evidence.",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["api_surface"] == "manual_human_decision_capture_dry_run"
    assert payload["explicit_user_action"] is True
    assert payload["decision_capture_status"] == "captured_for_review"
    assert payload["reviewer_decision"] == "request_more_tailoring"
    _assert_decision_safety(payload)


def test_api_route_slice_has_no_storage_scoring_queue_approval_execution_or_llm_calls():
    source = Path("src/app/api.py").read_text()
    start = source.index("class ManualHumanDecisionCaptureDryRunRequest")
    class_end = source.index("@asynccontextmanager")
    route_start = source.index('@app.post("/api/manual-human-decision-capture-dry-run")')
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
    start = source.index("def build_human_decision_capture_dry_run_payload")
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


def test_ui_renders_and_escapes_decision_capture_output():
    source = Path("src/app/static/agentic_review.js").read_text()
    start = source.index("function renderManualHumanDecisionCaptureDryRunSection")
    end = source.index("function renderAgentTraceReadOnlyPanel")
    snippet = source[start:end]

    assert "Manual Human Decision Capture Dry-run" in snippet
    assert "Capture Decision Dry-run" in snippet
    assert "data-manual-human-decision-capture-dry-run" in snippet
    assert "data-manual-human-decision-capture-dry-run-select" in snippet
    assert "escapeHtml(option)" in snippet
    assert "escapeHtml(jobTitle)" in snippet
    assert "escapeHtml(company)" in snippet
    assert "escapeHtml(location)" in snippet
    assert "escapeHtml(contextId)" in snippet
    assert "escapeHtml(jobId)" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Reviewer note\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Blocking risks\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Safety metadata\"" in snippet


def test_ui_click_posts_endpoint_and_existing_shadow_handoff_surface_still_exists():
    source = Path("src/app/static/agentic_review.js").read_text()

    assert source.count("/api/manual-human-decision-capture-dry-run") == 1
    assert source.count("data-manual-human-decision-capture-dry-run") == 6
    assert "manual_human_decision_capture_dry_run_result" in source
    assert "renderManualHumanDecisionCaptureDryRunSection(tracePayload)" in source
    assert source.count("/api/manual-shadow-recommendation-handoff-dry-run") == 1
    assert "renderManualShadowRecommendationHandoffDryRunSection(tracePayload)" in source
