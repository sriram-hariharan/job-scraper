from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services


ENDPOINT = "/api/manual-shadow-recommendation-handoff-dry-run"


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _shadow_chain_payload() -> dict:
    return {
        "shadow_chain_status": "completed",
        "recommendation_action": "tailor_first",
        "blocking_risks": [],
        "improvement_actions": ["Review approved tailoring suggestions before applying."],
        "stage_statuses": {
            "jd_intelligence": "disabled",
            "resume_match": "strong_match",
            "tailoring_suggestion": "patch_ready_available",
            "critic_guardrail": "approved",
            "strategy_recommendation": "ready",
        },
        "confidence": 0.91,
        "context_id": "ctx-1",
        "job_id": "job-1",
        "stages": {
            "strategy_recommendation": {
                "recommendation_label": "strong_match_with_approved_tailoring",
                "strategy_status": "ready",
            }
        },
        "safety_metadata": {
            "dry_run_only": True,
            "shadow_mode": True,
            "did_call_llm": False,
            "did_mutate_resume": False,
            "did_mutate_scoring": False,
            "did_change_ranking": False,
            "did_mutate_queue": False,
            "did_mutate_approval": False,
            "did_execute_application": False,
            "did_submit_application": False,
            "pipeline_wiring_added": False,
            "advisory_only": True,
        },
    }


def _assert_handoff_safety(payload: dict) -> None:
    safety = payload["safety_metadata"]
    assert payload["read_only"] is True
    assert payload["manual_surface"] is True
    assert safety["dry_run_only"] is True
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


def test_helper_builds_review_only_handoff_from_shadow_chain_payload():
    source = _shadow_chain_payload()
    original = deepcopy(source)

    first = services.build_shadow_recommendation_handoff_payload(
        shadow_chain_payload=source,
    )
    second = services.build_shadow_recommendation_handoff_payload(
        shadow_chain_payload=source,
    )

    assert first == second
    assert source == original
    assert first["service_surface"] == "shadow_recommendation_handoff_dry_run"
    assert first["handoff_status"] == "ready_for_human_review"
    assert first["recommendation_action"] == "tailor_first"
    assert first["recommendation_label"] == "strong_match_with_approved_tailoring"
    assert first["required_human_review"] is True
    assert first["reviewer_decision_options"] == [
        "accept_recommendation_for_review",
        "request_more_tailoring",
        "save_for_later",
        "dismiss_shadow_recommendation",
    ]
    assert first["source_shadow_chain_status"] == "completed"
    _assert_handoff_safety(first)


def test_helper_missing_shadow_chain_returns_safe_fallback():
    payload = services.build_shadow_recommendation_handoff_payload(
        shadow_chain_payload={},
    )

    assert payload["handoff_status"] == "blocked_pending_human_review"
    assert payload["recommendation_action"] == "insufficient_information"
    assert "resume_match_payload_missing" in payload["blocking_risks"]
    assert "critic_guardrail_payload_missing" in payload["blocking_risks"]
    _assert_handoff_safety(payload)


def test_api_route_exists_as_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"POST"}


def test_api_route_returns_readonly_handoff_payload(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={"shadow_chain_payload": _shadow_chain_payload()},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["api_surface"] == "manual_shadow_recommendation_handoff_dry_run"
    assert payload["explicit_user_action"] is True
    assert payload["handoff_status"] == "ready_for_human_review"
    assert payload["recommendation_action"] == "tailor_first"
    _assert_handoff_safety(payload)


def test_api_route_handles_missing_output_normally(monkeypatch):
    response = _client(monkeypatch).post(ENDPOINT, json={})

    assert response.status_code == 200
    payload = response.json()
    assert payload["recommendation_action"] == "insufficient_information"
    assert payload["required_human_review"] is True
    assert "resume_match_payload_missing" in payload["blocking_risks"]
    _assert_handoff_safety(payload)


def test_api_route_slice_has_no_storage_scoring_queue_approval_execution_or_llm_calls():
    source = Path("src/app/api.py").read_text()
    start = source.index("class ManualShadowRecommendationHandoffDryRunRequest")
    class_end = source.index("@asynccontextmanager")
    route_start = source.index('@app.post("/api/manual-shadow-recommendation-handoff-dry-run")')
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
    start = source.index("def build_shadow_recommendation_handoff_payload")
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
        "create_approval",
        "operator_decision",
    ]
    for marker in forbidden_markers:
        assert marker not in snippet


def test_ui_renders_and_escapes_handoff_output():
    source = Path("src/app/static/agentic_review.js").read_text()
    start = source.index("function renderManualShadowRecommendationHandoffDryRunSection")
    end = source.index("function renderAgentTraceReadOnlyPanel")
    snippet = source[start:end]

    assert "Manual Shadow Recommendation Handoff" in snippet
    assert "Build Shadow Recommendation Handoff" in snippet
    assert "data-manual-shadow-recommendation-handoff-dry-run" in snippet
    assert "escapeHtml(jobTitle)" in snippet
    assert "escapeHtml(company)" in snippet
    assert "escapeHtml(location)" in snippet
    assert "escapeHtml(contextId)" in snippet
    assert "escapeHtml(jobId)" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Reviewer decision options\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Blocking risks\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Improvement actions\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Stage statuses\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Safety metadata\"" in snippet
    assert "result.stages" not in snippet


def test_ui_click_posts_endpoint_and_existing_shadow_chain_surface_still_exists():
    source = Path("src/app/static/agentic_review.js").read_text()

    assert source.count("/api/manual-shadow-recommendation-handoff-dry-run") == 1
    assert source.count("data-manual-shadow-recommendation-handoff-dry-run") == 4
    assert "manual_shadow_recommendation_handoff_dry_run_result" in source
    assert "renderManualShadowRecommendationHandoffDryRunSection(tracePayload)" in source
    assert source.count("/api/manual-shadow-agentic-workflow-chain-dry-run") == 1
    assert "renderManualShadowAgenticWorkflowChainDryRunSection(tracePayload)" in source
