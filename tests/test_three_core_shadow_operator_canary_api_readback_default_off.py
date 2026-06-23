from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api


ENDPOINT = "/api/three-core-shadow-operator-canary-readback"


def _completed_shadow_payload() -> dict:
    ordered_names = [
        "relevance_prefilter",
        "jd_intelligence",
        "final_application_scoring",
    ]
    return {
        "hook_status": "hook_completed_with_fallback",
        "three_core_shadow_pipeline_hook_payload": {
            "hook_status": (
                "three_core_shadow_pipeline_hook_completed_shadow_only"
            ),
            "shadow_result_count": 3,
            "ordered_shadow_results": [
                {"agent_name": name, "status": "completed_shadow_only"}
                for name in ordered_names
            ],
            "connection_plan_summary": {"connection_plan_ready": True},
            "three_core_shadow_pipeline_hook": {
                "hook_checks": {
                    "relevance_prefilter_callable_supplied": True,
                    "jd_intelligence_callable_supplied": True,
                    "final_application_scoring_callable_supplied": True,
                }
            },
            "mutation_authorized": False,
            "workflow_connection_authorized": False,
            "pipeline_connection_authorized": False,
            "pipeline_stage_added": False,
            "execution_authorized": False,
            "submission_authorized": False,
            "forbidden_mutation_and_application_paths": {
                "workflow_connection_allowed": False,
                "pipeline_connection_allowed": False,
                "pipeline_stage_addition_allowed": False,
                "provider_execution_allowed": False,
                "scoring_mutation_allowed": False,
                "ranking_mutation_allowed": False,
                "queue_mutation_allowed": False,
                "resume_mutation_allowed": False,
                "application_execution_allowed": False,
                "application_submission_allowed": False,
            },
            "failure": {},
        },
    }


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def test_api_route_is_post_only_and_default_off(monkeypatch):
    routes = {getattr(route, "path", ""): route for route in api.app.routes}
    assert routes[ENDPOINT].methods == {"POST"}

    response = _client(monkeypatch).post(ENDPOINT, json={})
    assert response.status_code == 200
    payload = response.json()
    assert payload["api_surface"] == (
        "three_core_shadow_operator_canary_readback"
    )
    assert payload["api_readonly"] is True
    assert payload["canary_status"] == (
        "three_core_shadow_operator_canary_skipped_default_off"
    )


def test_api_enabled_completed_payload_returns_completed_readback(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "enabled": True,
            "shadow_sidecar_hook_payload": _completed_shadow_payload(),
            "canary_context": {"surface": "api_test"},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["canary_status"] == (
        "three_core_shadow_operator_canary_completed"
    )
    assert payload["operator_canary_summary"]["readback_completion"] is True
    assert payload["operator_canary_summary"]["shadow_result_count"] == 3


def test_api_safety_metadata_keeps_all_mutation_paths_false(monkeypatch):
    payload = _client(monkeypatch).post(ENDPOINT, json={}).json()
    safety = payload["safety_metadata"]

    for key in (
        "provider_calls_made",
        "provider_sdk_imported",
        "environment_secrets_read",
        "network_calls_made",
        "did_read_database",
        "did_write_database",
        "did_read_files",
        "did_write_files",
        "did_mutate_scoring",
        "did_change_ranking",
        "did_mutate_queue",
        "did_create_approval",
        "did_mutate_approval",
        "did_mutate_resume",
        "did_create_execution_request",
        "did_create_execution_launch_request",
        "did_execute_application",
        "did_submit_application",
        "ui_action_added",
        "pipeline_stage_added",
        "mutation_authorized",
    ):
        assert safety[key] is False


def test_api_route_source_has_no_pipeline_provider_io_or_execution_calls():
    source = Path("src/app/api.py").read_text(encoding="utf-8")
    start = source.index(
        '@app.post("/api/three-core-shadow-operator-canary-readback")'
    )
    end = source.index('\n@app.post("/api/provider-runtime-readback")', start)
    snippet = source[start:end].lower()

    for marker in (
        "collector.",
        "execute_pipeline",
        "requests.",
        "httpx.",
        "openai",
        "anthropic",
        "psycopg",
        "open(",
        "execute_application(",
        "submit_application(",
    ):
        assert marker not in snippet
