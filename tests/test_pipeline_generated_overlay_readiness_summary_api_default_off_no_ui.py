from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services


ENDPOINT = (
    "/api/pipeline-generated-agent-recommendation-overlay-readiness-summary"
)
SERVICE_HELPER = (
    "pipeline_generated_agent_recommendation_overlay_readiness_summary_service_payload"
)


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _overlay_readback(
    *,
    auto_generation_status: str = "overlay_auto_generated",
    overlay_status: str = "overlay_ready",
    recommended_review_action: str = "request_influence_approval",
) -> dict:
    overlay = {
        "overlay_status": overlay_status,
        "recommended_review_action": recommended_review_action,
    }
    return {
        "readback_status": "pipeline_generated_overlay_readback_ready",
        "pipeline_generated_overlay_found": True,
        "pipeline_generated_overlay": {
            "auto_generation_status": auto_generation_status,
            "overlay_generated": True,
            "agent_recommendation_overlay": overlay,
        },
        "agent_recommendation_overlay": overlay,
        "auto_generation_status": auto_generation_status,
        "overlay_status": overlay_status,
        "recommended_review_action": recommended_review_action,
    }


def _assert_api_safety(payload: dict) -> None:
    safety = payload["safety_metadata"]
    assert payload["api_surface"] == (
        "pipeline_generated_agent_recommendation_overlay_readiness_summary"
    )
    assert payload["api_readiness_summary_only"] is True
    assert payload["api_readonly"] is True
    assert payload["read_only"] is True
    assert payload["advisory_only"] is True
    assert payload["ui_action_added"] is False
    assert safety["read_only"] is True
    assert safety["api_readiness_summary_only"] is True
    assert safety["advisory_only"] is True
    assert safety["pipeline_generated_overlay_readiness_summary"] is True
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
    assert safety["ui_action_added"] is False
    assert safety["auto_apply_enabled"] is False
    assert safety["mutation_authorized"] is False
    assert payload["provider_calls_disabled_in_tests"] is True
    assert payload["requires_live_database"] is False
    assert payload["live_provider_backed_automated_agents"] == 0
    assert payload["mutation_authorized_agents"] == 0


def test_api_route_exists_as_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"POST"}


def test_api_returns_readiness_summary_for_ready_overlay(monkeypatch):
    request_payload = {"overlay_readback_payload": _overlay_readback()}
    before = deepcopy(request_payload)

    response = _client(monkeypatch).post(ENDPOINT, json=request_payload)

    assert response.status_code == 200
    assert request_payload == before
    payload = response.json()
    assert payload["readiness_status"] == "overlay_ready"
    assert payload["reviewable"] is True
    assert payload["partial"] is False
    assert payload["recommended_review_action"] == "request_influence_approval"
    _assert_api_safety(payload)


def test_api_returns_reviewable_partial_summary(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "overlay_readback_payload": _overlay_readback(
                auto_generation_status="overlay_auto_generated_partial",
                overlay_status="overlay_partial_insufficient_context",
                recommended_review_action="review_agent_preview",
            )
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["readiness_status"] == "overlay_partial_reviewable"
    assert payload["reviewable"] is True
    assert payload["partial"] is True
    assert payload["warning_findings"] == ["overlay_context_incomplete"]
    _assert_api_safety(payload)


def test_api_returns_safe_not_found_for_missing_overlay(monkeypatch):
    response = _client(monkeypatch).post(ENDPOINT, json={})

    assert response.status_code == 200
    payload = response.json()
    assert payload["readiness_status"] == "overlay_not_found"
    assert payload["reviewable"] is False
    assert payload["partial"] is False
    assert payload["reason_codes"] == ["pipeline_generated_overlay_not_found"]
    _assert_api_safety(payload)


def test_api_delegates_through_service_helper(monkeypatch):
    calls = []
    real_helper = getattr(services, SERVICE_HELPER)

    def recording_helper(**kwargs):
        calls.append(deepcopy(kwargs))
        return real_helper(**kwargs)

    monkeypatch.setattr(services, SERVICE_HELPER, recording_helper)
    request_payload = {
        "hook_payload": {
            "agent_recommendation_overlay_auto_generation": {
                "auto_generation_status": "overlay_auto_generated_partial",
                "overlay_generated": True,
                "agent_recommendation_overlay": {
                    "overlay_status": "overlay_partial_insufficient_context",
                    "recommended_review_action": "review_agent_preview",
                },
            }
        }
    }

    response = _client(monkeypatch).post(ENDPOINT, json=request_payload)

    assert response.status_code == 200
    assert len(calls) == 1
    assert calls[0]["hook_payload"] == request_payload["hook_payload"]
    assert response.json()["readiness_status"] == "overlay_partial_reviewable"


def test_api_route_slice_has_no_provider_storage_or_mutation_calls():
    source = Path("src/app/api.py").read_text(encoding="utf-8")
    start = source.index(
        "def pipeline_generated_agent_recommendation_overlay_readiness_summary("
    )
    end = source.index(
        "\n\n@app.get(\"/profile/pipeline-runs/{run_id}/agentic-review-data\")",
        start,
    )
    route_source = source[start:end]
    forbidden = [
        "src.pipeline",
        "schema.sql",
        "build_agent_recommendation_overlay_payload(",
        "score_resume_job_match(",
        "ranking_update",
        "ranking_mutation",
        "application_execution_queue",
        "create_approval_request(",
        "record_approval_decision(",
        "create_execution_request(",
        "create_execution_launch_request(",
        "execute_application(",
        "submit_application(",
        "insert_",
        "upsert_",
        "delete_",
        "run_chat_completion",
        "openai",
        "anthropic",
        "llm_client",
        "workflow_runner",
    ]

    for marker in forbidden:
        assert marker not in route_source

    assert SERVICE_HELPER in route_source


def test_api_does_not_add_ui_action():
    ui_source = Path("src/app/static/agentic_review.js").read_text(encoding="utf-8")

    assert ENDPOINT not in ui_source
    assert SERVICE_HELPER not in ui_source
    assert "pipeline-generated-overlay-readiness-summary" not in ui_source


def test_api_does_not_change_schema_or_pipeline():
    schema_text = "\n".join(
        [
            Path("src/storage/agentic_approvals/schema.sql").read_text(
                encoding="utf-8"
            ),
            Path("src/storage/agent_trace/schema.sql").read_text(encoding="utf-8"),
        ]
    )
    collector = Path("src/pipeline/collector.py").read_text(encoding="utf-8")

    assert ENDPOINT not in schema_text
    assert ENDPOINT not in collector
    assert SERVICE_HELPER not in schema_text
    assert SERVICE_HELPER not in collector
    assert collector.count("run_shadow_sidecar_pipeline_hook(") == 1


def test_provider_backed_and_mutation_authorized_agents_remain_zero(monkeypatch):
    payload = _client(monkeypatch).post(
        ENDPOINT,
        json={"overlay_readback_payload": _overlay_readback()},
    ).json()

    assert payload["live_provider_backed_automated_agents"] == 0
    assert payload["mutation_authorized_agents"] == 0
    _assert_api_safety(payload)
