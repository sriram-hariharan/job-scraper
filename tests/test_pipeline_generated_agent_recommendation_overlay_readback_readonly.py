from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from src.agents import (
    agent_recommendation_overlay_readback as readback,
    shadow_sidecar_hook,
)
from src.app import api, services


ENDPOINT = "/api/pipeline-generated-agent-recommendation-overlay-readback"
GLOBAL_FLAG = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED"
JD_FLAG = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_JD_INTELLIGENCE_ENABLED"
AUTO_FLAG = (
    "APPLYLENS_AGENTIC_PIPELINE_AGENT_RECOMMENDATION_OVERLAY_AUTO_GENERATE_ENABLED"
)
KILL_SWITCH = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_KILL_SWITCH"


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _hook_payload(*, include_preview: bool = True, **config):
    trace_context = {"trace_id": "trace_overlay_readback"}
    if include_preview:
        trace_context["human_reviewed_influence_preview_result"] = {
            "preview_status": "preview_ready_with_fallback",
            "preview_type": "human_reviewed_shadow_score_influence_preview",
            "proposed_score_adjustment_preview": {
                "proposed_score_delta": 0.0,
                "did_mutate_scoring": False,
            },
            "proposed_ranking_effect_preview": {
                "proposed_ranking_delta": 0,
                "did_change_ranking": False,
            },
        }
    return shadow_sidecar_hook.run_shadow_sidecar_pipeline_hook(
        run_id="run_overlay_readback",
        batch_id="batch_overlay_readback",
        job_id="job_overlay_readback",
        stage_name="post_final_scoring",
        source_deterministic_stage="application_priority",
        source_deterministic_status="completed",
        source_deterministic_score=0.91,
        source_deterministic_decision="qualified_priority_ready",
        source_deterministic_reason_codes=["priority_score_above_threshold"],
        sidecar_config=config,
        job_payload={
            "title": "Data Platform Engineer",
            "job_description": "Build SQL and Airflow data pipelines.",
            "required_skills": ["SQL"],
        },
        existing_trace_context=trace_context,
    )


def _assert_safety(payload):
    safety = payload["safety_metadata"]
    assert safety["read_only"] is True
    assert safety["readback_only"] is True
    assert safety["advisory_only"] is True
    assert safety["pipeline_generated_overlay_readback"] is True
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
    assert payload["requires_live_database"] is False
    assert payload["live_provider_backed_automated_agents"] == 0
    assert payload["mutation_authorized_agents"] == 0


def test_missing_overlay_returns_safe_not_found_state():
    payload = readback.build_pipeline_generated_agent_recommendation_overlay_readback_payload(
        hook_payload={"hook_status": "hook_completed_with_fallback"}
    )

    assert payload["readback_status"] == "pipeline_generated_overlay_not_found"
    assert payload["pipeline_generated_overlay_found"] is False
    assert payload["pipeline_generated_overlay"] == {}
    assert payload["agent_recommendation_overlay"] == {}
    _assert_safety(payload)


def test_generated_ready_overlay_is_read_back_from_hook_payload():
    hook = _hook_payload(**{GLOBAL_FLAG: True, JD_FLAG: True, AUTO_FLAG: True})

    payload = readback.build_pipeline_generated_agent_recommendation_overlay_readback_payload(
        hook_payload=hook
    )

    assert payload["readback_status"] == "pipeline_generated_overlay_readback_ready"
    assert payload["pipeline_generated_overlay_found"] is True
    assert payload["auto_generation_status"] in {"overlay_auto_generated", "overlay_auto_generated_partial"}
    assert payload["agent_recommendation_overlay"]["overlay_status"] in {"overlay_ready", "overlay_partial_insufficient_context"}
    assert payload["recommended_review_action"] in {
        "request_influence_approval",
        "review_agent_preview",
        "no_agent_action",
    }
    _assert_safety(payload)


def test_generated_partial_overlay_is_read_back_from_trace_capture():
    hook = _hook_payload(
        include_preview=False,
        **{GLOBAL_FLAG: True, AUTO_FLAG: True},
    )

    payload = readback.build_pipeline_generated_agent_recommendation_overlay_readback_payload(
        trace_capture_payload=hook["trace_capture"]
    )

    assert payload["readback_status"] == "pipeline_generated_overlay_readback_ready"
    assert payload["auto_generation_status"] == "overlay_auto_generated_partial"
    assert payload["agent_recommendation_overlay"]["overlay_status"] == (
        "overlay_partial_insufficient_context"
    )
    _assert_safety(payload)


def test_blocked_not_enabled_and_failed_overlay_states_are_read_back_safely():
    not_enabled = _hook_payload(**{GLOBAL_FLAG: True, JD_FLAG: True})
    blocked = _hook_payload(
        **{GLOBAL_FLAG: True, JD_FLAG: True, AUTO_FLAG: True, KILL_SWITCH: True}
    )
    failed = {
        "agent_recommendation_overlay_auto_generation": {
            "auto_generation_status": "overlay_auto_generation_failed_non_blocking",
            "overlay_generated": False,
            "agent_recommendation_overlay": {},
        }
    }

    for source, expected in [
        (not_enabled, "overlay_auto_generation_not_enabled"),
        (blocked, "overlay_auto_generation_blocked_by_kill_switch"),
        (failed, "overlay_auto_generation_failed_non_blocking"),
    ]:
        payload = readback.build_pipeline_generated_agent_recommendation_overlay_readback_payload(
            hook_payload=source
        )
        assert payload["readback_status"] == "pipeline_generated_overlay_readback_ready"
        assert payload["auto_generation_status"] == expected
        _assert_safety(payload)


def test_overlay_is_read_back_from_persistence_and_trace_readback_shapes():
    hook = _hook_payload(**{GLOBAL_FLAG: True, JD_FLAG: True, AUTO_FLAG: True})

    from_persistence = readback.build_pipeline_generated_agent_recommendation_overlay_readback_payload(
        trace_persistence_payload=hook["trace_persistence"]
    )

    overlay_auto = hook["agent_recommendation_overlay_auto_generation"]
    trace_readback_payload = {
        "trace_readback": {
            "pipeline_generated_overlay": overlay_auto,
            "agent_recommendation_overlay_auto_generation": overlay_auto,
            "agent_steps": [
                {
                    "agent_name": "agent_recommendation_overlay_auto_generation",
                    "step_name": "agent_recommendation_overlay_auto_generation",
                    "payload": overlay_auto,
                    "step_payload": overlay_auto,
                    "output_payload": overlay_auto,
                    "output_json": overlay_auto,
                    "agent_recommendation_overlay_auto_generation": overlay_auto,
                }
            ],
        },
        "pipeline_generated_overlay": overlay_auto,
        "agent_recommendation_overlay_auto_generation": overlay_auto,
    }

    from_trace_readback = readback.build_pipeline_generated_agent_recommendation_overlay_readback_payload(
        trace_readback_payload=trace_readback_payload
    )

    assert from_persistence["readback_status"] == "pipeline_generated_overlay_not_found"
    assert from_persistence["pipeline_generated_overlay_found"] is False
    assert from_persistence["auto_generation_status"] == ""

    assert from_trace_readback["readback_status"] == "pipeline_generated_overlay_readback_ready"
    assert from_trace_readback["pipeline_generated_overlay_found"] is True
    assert from_trace_readback["auto_generation_status"] in {
        "overlay_auto_generated",
        "overlay_auto_generated_partial",
    }

def test_service_and_api_readback_are_read_only(monkeypatch):
    hook = _hook_payload(**{GLOBAL_FLAG: True, JD_FLAG: True, AUTO_FLAG: True})
    service_payload = (
        services.pipeline_generated_agent_recommendation_overlay_readback_service_payload(
            hook_payload=hook
        )
    )
    response = _client(monkeypatch).post(ENDPOINT, json={"hook_payload": hook})

    assert service_payload["service_surface"] == (
        "pipeline_generated_agent_recommendation_overlay_readback_service"
    )
    assert service_payload["service_helper_only"] is True
    assert service_payload["api_route_added"] is False
    assert response.status_code == 200
    api_payload = response.json()
    assert api_payload["api_surface"] == (
        "pipeline_generated_agent_recommendation_overlay_readback"
    )
    assert api_payload["api_readback_only"] is True
    assert api_payload["auto_generation_status"] in {"overlay_auto_generated", "overlay_auto_generated_partial"}
    _assert_safety(service_payload)
    _assert_safety(api_payload)


def test_api_route_exists_as_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"POST"}


def test_readback_does_not_regenerate_overlay_or_call_providers_or_mutations():
    helper_source = Path("src/agents/agent_recommendation_overlay_readback.py").read_text(
        encoding="utf-8"
    )
    service_source = Path("src/app/services.py").read_text(encoding="utf-8")
    api_source = Path("src/app/api.py").read_text(encoding="utf-8")
    service_start = service_source.index(
        "def pipeline_generated_agent_recommendation_overlay_readback_service_payload"
    )
    service_end = service_source.index("HUMAN_REVIEWED_INFLUENCE_APPROVAL_REQUEST_FLAG")
    api_start = api_source.index(
        '@app.post("/api/pipeline-generated-agent-recommendation-overlay-readback")'
    )
    api_end = api_source.index('@app.get("/profile/pipeline-runs/{run_id}/agentic-review-data")')
    combined = "\n".join(
        [
            helper_source,
            service_source[service_start:service_end],
            api_source[api_start:api_end],
        ]
    )

    forbidden = [
        "build_agent_recommendation_overlay_payload(",
        "create_approval_request(",
        "record_approval_decision(",
        "score_resume_job_match",
        "ranking_update",
        "ranking_mutation",
        "application_execution_queue",
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
    for marker in forbidden:
        assert marker not in combined


def test_ui_renders_readback_states_and_uses_escaped_readonly_details():
    source = Path("src/app/static/agentic_review.js").read_text(encoding="utf-8")
    start = source.index(
        "function renderPipelineGeneratedAgentRecommendationOverlayReadbackSection"
    )
    end = source.index("function renderAgentRecommendationOverlaySection")
    snippet = source[start:end]

    assert "Pipeline-generated Overlay Readback" in snippet
    assert "Read Pipeline Overlay" in snippet
    assert "data-pipeline-generated-agent-recommendation-overlay-readback" in snippet
    assert "pipeline_generated_overlay_not_found" in snippet
    assert "overlay_auto_generation_not_enabled" in snippet
    assert "overlay_auto_generation_blocked_by_kill_switch" in snippet
    assert "overlay_auto_generated_partial" in snippet
    assert "overlay_auto_generation_failed_non_blocking" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Pipeline generated overlay\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Agent recommendation overlay\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Safety metadata\"" in snippet


def test_ui_posts_readback_endpoint_only_from_explicit_action():
    source = Path("src/app/static/agentic_review.js").read_text(encoding="utf-8")
    handler_start = source.index(
        'event.target.closest("[data-pipeline-generated-agent-recommendation-overlay-readback]")'
    )
    handler_end = source.index(
        'event.target.closest("[data-manual-shadow-recommendation-handoff-dry-run]")',
        handler_start,
    )
    handler = source[handler_start:handler_end]

    assert source.count(ENDPOINT) == 1
    assert ENDPOINT in handler
    assert 'method: "POST"' in handler
    assert (
        "pipelineGeneratedAgentRecommendationOverlayReadbackRequestPayload(tracePayload)"
        in handler
    )
    assert "pipeline_generated_agent_recommendation_overlay_readback_result" in source
    init_start = source.index("async function initAgenticReviewPage")
    init_end = source.index('window.addEventListener("DOMContentLoaded", initAgenticReviewPage);')
    assert ENDPOINT not in source[init_start:init_end]


def test_no_schema_change_or_new_pipeline_stage_for_readback():
    schema_text = "\n".join(
        [
            Path("src/storage/agentic_approvals/schema.sql").read_text(encoding="utf-8"),
            Path("src/storage/agent_trace/schema.sql").read_text(encoding="utf-8"),
        ]
    )
    collector = Path("src/pipeline/collector.py").read_text(encoding="utf-8")

    assert "pipeline_generated_agent_recommendation_overlay_readback" not in schema_text
    assert "pipeline_generated_agent_recommendation_overlay_readback" not in collector
    assert collector.count("run_shadow_sidecar_pipeline_hook(") == 1
