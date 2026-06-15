from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services


ENDPOINT = "/api/manual-strategy-recommendation-dry-run"


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _jd() -> dict:
    return {
        "required_skills": ["Python", "SQL"],
        "required_tools": ["Airflow"],
        "workflows": ["production data pipelines"],
        "business_contexts": ["finance partners"],
    }


def _resume_match() -> dict:
    return {
        "match_status": "strong_match",
        "recommendation_label": "strong_match",
        "selected_resume_id": "resume-a",
        "confidence": 0.86,
        "missing_evidence": [],
    }


def _tailoring() -> dict:
    return {
        "suggestion_status": "patch_ready_available",
        "selected_resume_id": "resume-a",
        "patch_ready_suggestions": [{"suggestion_id": "tailoring_dry_run_001"}],
        "guidance_only_suggestions": [],
        "rejected_suggestions": [],
        "missing_evidence": [],
        "projected_score_delta": 0.03,
    }


def _critic() -> dict:
    return {
        "critic_status": "approved",
        "approved_suggestions": [{"suggestion_id": "tailoring_dry_run_001"}],
        "downgraded_suggestions": [],
        "rejected_suggestions": [],
        "reason_codes": [],
        "evidence_gaps": [],
        "confidence": 0.88,
    }


def _request_payload() -> dict:
    return {
        "jd_intelligence": _jd(),
        "resume_match_payload": _resume_match(),
        "tailoring_suggestion_payload": _tailoring(),
        "critic_guardrail_payload": _critic(),
        "user_preferences": {"risk_tolerance": "conservative"},
        "context_id": "ctx-1",
        "job_id": "job-1",
    }


def _assert_readonly_safety(payload: dict) -> None:
    safety = payload["safety_metadata"]
    assert payload["read_only"] is True
    assert payload["manual_surface"] is True
    assert safety["dry_run_only"] is True
    assert safety["deterministic_only"] is True
    assert safety["did_call_llm"] is False
    assert safety["did_mutate_resume"] is False
    assert safety["did_mutate_scoring"] is False
    assert safety["did_change_ranking"] is False
    assert safety["did_mutate_queue"] is False
    assert safety["did_mutate_approval"] is False
    assert safety["did_execute_application"] is False
    assert safety["did_submit_application"] is False
    assert safety["pipeline_wiring_added"] is False
    assert safety["advisory_only"] is True


def test_service_returns_manual_strategy_recommendation_dry_run_payload():
    source = _request_payload()
    original = deepcopy(source)

    first = services.build_manual_strategy_recommendation_dry_run_payload(**source)
    second = services.build_manual_strategy_recommendation_dry_run_payload(**source)

    assert first == second
    assert source == original
    assert first["service_surface"] == "manual_strategy_recommendation_dry_run"
    assert first["recommendation_action"] in {"apply_now", "tailor_first"}
    assert first["strategy_status"] == "ready"
    _assert_readonly_safety(first)


def test_api_route_exists_as_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"POST"}


def test_api_route_returns_readonly_strategy_recommendation_payload(monkeypatch):
    response = _client(monkeypatch).post(ENDPOINT, json=_request_payload())

    assert response.status_code == 200
    payload = response.json()
    assert payload["api_surface"] == "manual_strategy_recommendation_dry_run"
    assert payload["explicit_user_action"] is True
    assert payload["strategy_status"] == "ready"
    assert payload["recommendation_action"] in {"apply_now", "tailor_first"}
    _assert_readonly_safety(payload)


def test_api_route_handles_missing_output_normally(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "jd_intelligence": {},
            "resume_match_payload": {},
            "tailoring_suggestion_payload": {},
            "critic_guardrail_payload": {},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["recommendation_action"] == "insufficient_information"
    assert "missing_required_dry_run_inputs" in payload["decision_reasons"]
    assert "resume_match_payload_missing" in payload["blocking_risks"]
    assert "critic_guardrail_payload_missing" in payload["blocking_risks"]
    _assert_readonly_safety(payload)


def test_api_route_slice_has_no_storage_scoring_queue_approval_execution_or_llm_calls():
    source = Path("src/app/api.py").read_text()
    start = source.index("class ManualStrategyRecommendationDryRunRequest")
    class_end = source.index("@asynccontextmanager")
    route_start = source.index('@app.post("/api/manual-strategy-recommendation-dry-run")')
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
        "ranking",
        "run_chat_completion",
        "openai",
        "anthropic",
        "llm_client",
    ]
    for marker in forbidden_markers:
        assert marker not in snippet


def test_service_helper_slice_has_no_storage_scoring_queue_or_llm_calls():
    source = Path("src/app/services.py").read_text()
    start = source.index("def build_manual_strategy_recommendation_dry_run_payload")
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
        "ranking",
        "execute_application",
        "submit_application",
        "workflow_runner",
    ]
    for marker in forbidden_markers:
        assert marker not in snippet


def test_ui_manual_strategy_section_uses_existing_escaped_rendering():
    source = Path("src/app/static/agentic_review.js").read_text()
    start = source.index("function renderManualStrategyRecommendationDryRunSection")
    end = source.index("function renderAgentTraceReadOnlyPanel")
    snippet = source[start:end]

    assert "Manual Strategy Recommendation Dry-run" in snippet
    assert "data-manual-strategy-recommendation-dry-run" in snippet
    assert "escapeHtml(contextId)" in snippet
    assert "escapeHtml(jobId)" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Recommendation label\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Decision reasons\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Blocking risks\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Improvement actions\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Safety metadata\"" in snippet
    assert "does not mutate resume content" in snippet


def test_ui_manual_strategy_click_posts_endpoint_and_existing_dry_runs_still_exist():
    source = Path("src/app/static/agentic_review.js").read_text()

    assert source.count("/api/manual-strategy-recommendation-dry-run") == 1
    assert source.count("data-manual-strategy-recommendation-dry-run") == 4
    assert "manual_strategy_recommendation_dry_run_result" in source
    assert "renderManualStrategyRecommendationDryRunSection(tracePayload)" in source
    assert source.count("/api/manual-jd-intelligence-dry-run") == 1
    assert source.count("/api/manual-resume-match-dry-run") == 1
    assert source.count("/api/manual-tailoring-suggestion-dry-run") == 1
    assert source.count("/api/manual-critic-guardrail-dry-run") == 1
    assert "renderManualJdIntelligenceDryRunSection(tracePayload)" in source
    assert "renderManualResumeMatchDryRunSection(tracePayload)" in source
    assert "renderManualTailoringSuggestionDryRunSection(tracePayload)" in source
    assert "renderManualCriticGuardrailDryRunSection(tracePayload)" in source
