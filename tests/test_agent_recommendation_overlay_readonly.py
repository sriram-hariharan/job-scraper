from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient

from src.agents import agent_recommendation_overlay
from src.app import api, services


ENDPOINT = "/api/agent-recommendation-overlay"
OVERLAY_FLAG = "APPLYLENS_AGENTIC_PIPELINE_AGENT_RECOMMENDATION_OVERLAY_ENABLED"
KILL_SWITCH = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_KILL_SWITCH"


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _enabled_config():
    return {OVERLAY_FLAG: True}


def _deterministic_context():
    return {
        "deterministic_score": 0.91,
        "deterministic_decision": "qualified_priority_ready",
        "decision_counts": {"qualified": 4, "blocked": 0},
    }


def _comparison_context():
    return {
        "comparison_status": "comparison_ready_with_fallback",
        "agreement_level": "needs_operator_review",
        "shadow_snapshot_status": "snapshot_ready_with_fallback",
        "shadow_risk_flag_count": 1,
        "shadow_blocking_finding_count": 0,
        "operator_review_summary": {
            "summary_type": "shadow_sidecar_score_comparison",
            "recommended_review_focus": ["shadow_risk_flags_present"],
        },
    }


def _influence_preview():
    return {
        "preview_status": "preview_ready_with_fallback",
        "preview_type": "human_reviewed_shadow_score_influence_preview",
        "proposed_influence_summary": {
            "recommended_operator_review": "review_shadow_risk_flags_before_any_future_influence",
        },
        "proposed_score_adjustment_preview": {
            "proposed_score_delta": 0.0,
            "did_mutate_scoring": False,
        },
        "proposed_ranking_effect_preview": {
            "proposed_ranking_delta": 0,
            "did_change_ranking": False,
        },
    }


def _approval_request_context():
    return {
        "request_status": "created",
        "approval_request_created": True,
        "created_approval_request_id": "manual_influence_approval_123",
        "approval_request": {
            "approval_request_id": "manual_influence_approval_123",
            "approval_status": "pending",
        },
    }


def _request_payload():
    return {
        "deterministic_score_context": _deterministic_context(),
        "shadow_score_comparison_context": _comparison_context(),
        "human_reviewed_influence_preview_payload": _influence_preview(),
        "influence_approval_request_payload": _approval_request_context(),
        "overlay_config": _enabled_config(),
    }


def _assert_safety(payload: dict) -> None:
    safety = payload["safety_metadata"]
    assert safety["read_only"] is True
    assert safety["advisory_only"] is True
    assert safety["overlay_only"] is True
    assert safety["human_review_required"] is True
    assert safety["approval_gate_required_for_influence"] is True
    assert safety["did_mutate_scoring"] is False
    assert safety["did_change_ranking"] is False
    assert safety["did_mutate_queue"] is False
    assert safety["did_create_approval"] is False
    assert safety["did_mutate_approval"] is False
    assert safety["did_mutate_resume"] is False
    assert safety["did_create_execution_request"] is False
    assert safety["did_create_execution_launch_request"] is False
    assert safety["did_execute_application"] is False
    assert safety["did_submit_application"] is False
    assert safety["auto_apply_enabled"] is False
    assert safety["mutation_authorized"] is False
    assert payload["live_provider_backed_automated_agents"] == 0
    assert payload["mutation_authorized_agents"] == 0
    assert payload["requires_live_database"] is False


def test_default_environment_returns_overlay_not_enabled():
    payload = agent_recommendation_overlay.build_agent_recommendation_overlay_payload(
        deterministic_score_context=_deterministic_context(),
        shadow_score_comparison_context=_comparison_context(),
        human_reviewed_influence_preview_payload=_influence_preview(),
        influence_approval_request_payload=_approval_request_context(),
    )

    assert payload["overlay_status"] == "overlay_not_enabled"
    assert payload["recommended_review_action"] == "insufficient_context"
    _assert_safety(payload)


def test_kill_switch_blocks_overlay():
    payload = agent_recommendation_overlay.build_agent_recommendation_overlay_payload(
        deterministic_score_context=_deterministic_context(),
        shadow_score_comparison_context=_comparison_context(),
        overlay_config={OVERLAY_FLAG: True, KILL_SWITCH: True},
    )

    assert payload["overlay_status"] == "overlay_blocked_by_kill_switch"
    assert payload["recommended_review_action"] == "insufficient_context"
    _assert_safety(payload)


def test_missing_deterministic_context_blocks_safely():
    payload = agent_recommendation_overlay.build_agent_recommendation_overlay_payload(
        deterministic_score_context={},
        shadow_score_comparison_context=_comparison_context(),
        overlay_config=_enabled_config(),
    )

    assert payload["overlay_status"] == "overlay_blocked_missing_deterministic_context"
    assert payload["deterministic_decision_context"]["deterministic_score"] is None
    _assert_safety(payload)


def test_missing_comparison_or_preview_returns_safe_partial_overlay():
    payload = agent_recommendation_overlay.build_agent_recommendation_overlay_payload(
        deterministic_score_context=_deterministic_context(),
        shadow_score_comparison_context={},
        human_reviewed_influence_preview_payload={},
        overlay_config=_enabled_config(),
    )

    assert payload["overlay_status"] == "overlay_partial_insufficient_context"
    assert payload["recommended_review_action"] == "insufficient_context"
    assert "shadow_score_comparison_missing" in {
        finding["finding_code"] for finding in payload["overlay_findings"]
    }
    assert "human_reviewed_influence_preview_missing" in {
        finding["finding_code"] for finding in payload["overlay_findings"]
    }
    _assert_safety(payload)


def test_enabled_overlay_builds_deterministic_advisory_recommendation():
    request = _request_payload()
    before = deepcopy(request)

    first = agent_recommendation_overlay.build_agent_recommendation_overlay_payload(**request)
    second = agent_recommendation_overlay.build_agent_recommendation_overlay_payload(**request)

    assert first == second
    assert request == before
    assert first["overlay_status"] == "overlay_ready"
    assert first["recommended_review_action"] == "approval_pending"
    assert first["deterministic_decision_context"]["deterministic_score"] == 0.91
    assert first["shadow_score_comparison"]["comparison_status"] == (
        "comparison_ready_with_fallback"
    )
    assert first["shadow_score_comparison"]["agreement_level"] == (
        "needs_operator_review"
    )
    assert first["human_reviewed_influence_preview"]["preview_status"] == (
        "preview_ready_with_fallback"
    )
    assert first["approval_request_context"]["request_status"] == "created"
    assert first["operator_review_summary"]["recommended_review_action"] == (
        "approval_pending"
    )
    _assert_safety(first)


def test_enabled_overlay_without_approval_request_recommends_influence_approval():
    payload = agent_recommendation_overlay.build_agent_recommendation_overlay_payload(
        deterministic_score_context=_deterministic_context(),
        shadow_score_comparison_context=_comparison_context(),
        human_reviewed_influence_preview_payload=_influence_preview(),
        influence_approval_request_payload={},
        overlay_config=_enabled_config(),
    )

    assert payload["overlay_status"] == "overlay_ready"
    assert payload["recommended_review_action"] == "request_influence_approval"
    _assert_safety(payload)


def test_service_helper_is_readonly_and_default_off():
    payload = services.agent_recommendation_overlay_service_payload(
        deterministic_score_context=_deterministic_context(),
        shadow_score_comparison_context=_comparison_context(),
    )

    assert payload["overlay_status"] == "overlay_not_enabled"
    assert payload["service_surface"] == "agent_recommendation_overlay_service"
    assert payload["service_helper_only"] is True
    assert payload["api_route_added"] is False
    assert payload["ui_action_added"] is False
    assert payload["safety_metadata"]["service_helper_only"] is True
    _assert_safety(payload)


def test_api_route_exists_as_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"POST"}


def test_api_route_default_off_returns_overlay_not_enabled(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "deterministic_score_context": _deterministic_context(),
            "shadow_score_comparison_context": _comparison_context(),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["overlay_status"] == "overlay_not_enabled"
    assert payload["api_surface"] == "agent_recommendation_overlay"
    assert payload["api_readback_only"] is True
    _assert_safety(payload)


def test_api_route_enabled_returns_readonly_overlay(monkeypatch):
    response = _client(monkeypatch).post(ENDPOINT, json=_request_payload())

    assert response.status_code == 200
    payload = response.json()
    assert payload["overlay_status"] == "overlay_ready"
    assert payload["recommended_review_action"] == "approval_pending"
    assert payload["api_surface"] == "agent_recommendation_overlay"
    assert payload["api_readback_only"] is True
    _assert_safety(payload)


def test_overlay_sources_have_no_scoring_ranking_queue_approval_or_execution_mutation_calls():
    sources = {
        "agent": Path("src/agents/agent_recommendation_overlay.py").read_text(),
        "service": Path("src/app/services.py").read_text(),
        "api": Path("src/app/api.py").read_text(),
    }
    service_start = sources["service"].index("def agent_recommendation_overlay_service_payload")
    service_end = sources["service"].index("HUMAN_REVIEWED_INFLUENCE_APPROVAL_REQUEST_FLAG")
    api_start = sources["api"].index('@app.post("/api/agent-recommendation-overlay")')
    api_end = sources["api"].index('@app.get("/profile/pipeline-runs/{run_id}/agentic-review-data")')
    combined = "\n".join(
        [
            sources["agent"],
            sources["service"][service_start:service_end],
            sources["api"][api_start:api_end],
        ]
    )

    forbidden_markers = [
        "score_resume_job_match",
        "ranking_update",
        "ranking_mutation",
        "application_execution_queue",
        "create_approval_request(",
        "record_approval_decision(",
        "insert_operator_decision",
        "create_execution_request(",
        "create_execution_launch_request(",
        "execute_application(",
        "submit_application(",
        "run_chat_completion",
        "openai",
        "anthropic",
        "llm_client",
        "workflow_runner",
    ]
    for marker in forbidden_markers:
        assert marker not in combined


def test_ui_renders_overlay_and_escapes_output():
    source = Path("src/app/static/agentic_review.js").read_text()
    start = source.index("function renderAgentRecommendationOverlaySection")
    end = source.index("function renderHumanReviewedInfluenceApprovalRequestSection")
    snippet = source[start:end]

    assert "Agent Recommendation Overlay" in snippet
    assert "Build Agent Recommendation Overlay" in snippet
    assert "data-agent-recommendation-overlay" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Deterministic decision context\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Shadow score comparison\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Human-reviewed influence preview\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Approval request context\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Recommended review action\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Safety metadata\"" in snippet


def test_ui_posts_overlay_endpoint_only_from_explicit_action_and_existing_surfaces_remain():
    source = Path("src/app/static/agentic_review.js").read_text()
    handler_start = source.index('event.target.closest("[data-agent-recommendation-overlay]")')
    handler_end = source.index(
        'event.target.closest("[data-manual-shadow-recommendation-handoff-dry-run]")',
        handler_start,
    )
    handler = source[handler_start:handler_end]

    assert source.count("/api/agent-recommendation-overlay") == 1
    assert "/api/agent-recommendation-overlay" in handler
    assert 'method: "POST"' in handler
    assert "agentRecommendationOverlayRequestPayload(tracePayload)" in handler
    assert "agent_recommendation_overlay_result" in source
    assert "renderAgentRecommendationOverlaySection(tracePayload)" in source
    assert "renderHumanReviewedInfluencePreviewSection(tracePayload)" in source
    assert "renderHumanReviewedInfluenceApprovalRequestSection(tracePayload)" in source
    assert "fetchAgentTraceReadOnlyPayload" in source
    init_start = source.index("async function initAgenticReviewPage")
    init_end = source.index('window.addEventListener("DOMContentLoaded", initAgenticReviewPage);')
    assert "/api/agent-recommendation-overlay" not in source[init_start:init_end]


def test_no_schema_files_are_changed_for_overlay_contract():
    protected_paths = [
        Path("src/storage/agentic_approvals/schema.sql"),
        Path("src/storage/agent_trace/schema.sql"),
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in protected_paths)

    assert "agent_recommendation_overlay" not in combined
    assert "AGENT_RECOMMENDATION_OVERLAY" not in combined
