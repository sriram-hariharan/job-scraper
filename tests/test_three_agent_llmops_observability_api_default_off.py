import hashlib
from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services


ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = "/api/three-agent-llmops-observability-readback"
SERVICE = "three_agent_llmops_observability_readback_service_payload"


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _chain():
    names = [
        "jd_intelligence",
        "tailoring_suggestion",
        "critic_guardrail",
    ]
    return {
        "ordered_agent_results": [
            {
                "agent_name": name,
                "llmops_trace_metadata": {
                    "provider_call_made": True,
                    "model_provider": "fixture",
                    "model_name": f"fixture-{index + 1}",
                    "input_tokens": 10 * (index + 1),
                    "output_tokens": 2 * (index + 1),
                    "total_token_count": 12 * (index + 1),
                    "estimated_cost": 0.001 * (index + 1),
                    "latency_ms": 5 * (index + 1),
                    "fallback_used": index == 1,
                    "schema_validation_status": (
                        "fallback" if index == 1 else "valid"
                    ),
                    "error_type": "",
                },
            }
            for index, name in enumerate(names)
        ],
        "three_agent_llmops_aggregate": {
            "total_input_tokens": 60,
            "total_output_tokens": 12,
            "total_tokens": 72,
            "total_estimated_cost": 0.006,
            "total_latency_ms": 30,
            "max_agent_latency_ms": 15,
            "provider_call_count": 3,
            "fallback_count": 1,
            "schema_valid_count": 2,
            "schema_invalid_count": 1,
            "agent_count": 3,
            "agent_names": names,
            "aggregate_status": "aggregate_complete",
        },
        "three_agent_workflow_readiness": {
            "readiness_status": "ready_shadow_provider_workflow",
            "provider_backed_agent_count": 3,
            "mutation_authorized_agent_count": 0,
        },
    }


def _assert_safety(payload):
    safety = payload["safety_metadata"]
    assert payload["api_surface"] == (
        "three_agent_llmops_observability_readback"
    )
    assert payload["api_readback_only"] is True
    assert payload["api_route_added"] is True
    assert payload["read_only"] is True
    assert payload["advisory_only"] is True
    assert payload["ui_action_added"] is False
    assert payload["pipeline_stage_added"] is False
    assert safety["read_only"] is True
    assert safety["advisory_only"] is True
    assert safety["readback_only"] is True
    assert safety["llmops_observability_readback_api"] is True
    assert safety["llmops_observability_service_bridge"] is True
    assert safety["provider_calls_made"] is False
    assert safety["embeddings_created"] is False
    assert safety["did_read_database"] is False
    assert safety["did_write_database"] is False
    assert safety["did_mutate_scoring"] is False
    assert safety["did_change_ranking"] is False
    assert safety["did_mutate_queue"] is False
    assert safety["did_create_approval"] is False
    assert safety["did_mutate_resume"] is False
    assert safety["did_execute_application"] is False
    assert safety["did_submit_application"] is False


def test_api_route_exists_as_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"POST"}


def test_api_default_off_skips_safely(monkeypatch):
    response = _client(monkeypatch).post(ENDPOINT, json={})

    assert response.status_code == 200
    payload = response.json()
    assert payload["readback_status"] == "skipped_default_off"
    assert payload["observability_readback_enabled"] is False
    assert payload["default_off"] is True
    assert payload["agents"] == []
    _assert_safety(payload)


def test_api_enabled_delegates_through_service_bridge(monkeypatch):
    calls = []
    real_service = getattr(services, SERVICE)

    def recording_service(**kwargs):
        calls.append(deepcopy(kwargs))
        return real_service(**kwargs)

    monkeypatch.setattr(services, SERVICE, recording_service)
    chain = _chain()
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={"enabled": True, "chain_payload": chain},
    )

    assert response.status_code == 200
    assert calls == [
        {
            "enabled": True,
            "payload": {},
            "chain_payload": chain,
            "review_packet_payload": {},
        }
    ]
    assert response.json()["readback_status"] == "ready"


def test_api_returns_rows_aggregate_and_readiness(monkeypatch):
    chain = _chain()
    request_payload = {
        "enabled": True,
        "review_packet_payload": {
            "three_agent_llmops_trace_contract": {
                "agent_traces": [
                    result["llmops_trace_metadata"]
                    | {"agent_name": result["agent_name"]}
                    for result in chain["ordered_agent_results"]
                ]
            },
            "three_agent_llmops_aggregate": chain[
                "three_agent_llmops_aggregate"
            ],
            "three_agent_workflow_readiness": chain[
                "three_agent_workflow_readiness"
            ],
        },
    }
    before = deepcopy(request_payload)
    response = _client(monkeypatch).post(ENDPOINT, json=request_payload)

    assert response.status_code == 200
    assert request_payload == before
    payload = response.json()
    assert payload["agent_count"] == 3
    assert payload["provider_backed_agent_count"] == 3
    assert payload["agents"][0]["agent_name"] == "jd_intelligence"
    assert payload["agents"][0]["latency_ms"] == 5
    assert payload["agents"][1]["fallback_used"] is True
    assert payload["aggregate"] == chain[
        "three_agent_llmops_aggregate"
    ]
    assert payload["workflow_readiness"] == chain[
        "three_agent_workflow_readiness"
    ]
    _assert_safety(payload)


def test_api_enabled_missing_payload_returns_safe_status(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={"enabled": True},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["readback_status"] == "missing_three_agent_chain"
    assert payload["agent_count"] == 0
    assert payload["aggregate"]["total_tokens"] == 0
    _assert_safety(payload)


def test_route_slice_has_no_provider_storage_or_mutation_wiring():
    source = (ROOT / "src/app/api.py").read_text(encoding="utf-8")
    start = source.index(
        '@app.post("/api/three-agent-llmops-observability-readback")'
    )
    end = source.index(
        '\n\n@app.get("/profile/pipeline-runs/{run_id}/agentic-review-data")',
        start,
    )
    snippet = source[start:end].lower()

    assert SERVICE in snippet
    for marker in (
        "src.storage",
        "src.pipeline",
        "schema.sql",
        "openai",
        "anthropic",
        "langchain",
        "create_embedding(",
        "database_url",
        "connect(",
        "insert_",
        "upsert_",
        "score_jobs(",
        "rank_jobs(",
        "create_approval_request(",
        "mutate_resume(",
        "create_execution_request(",
        "execute_application(",
        "submit_application(",
    ):
        assert marker not in snippet


def test_no_ui_pipeline_dependency_or_decision_module_change():
    expected = {
        "requirements.txt": "96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f",
        "src/app/static/agentic_review.js": "450b95cdb1a838854a8be1ed11f3ae9f0fa886d11cc0724eb5e63384936f75bc",
        "src/pipeline/collector.py": "cbcd90f3d8d367ebe6f178c211406da909f340ce62681047b70efe4fb4a30fa7",
        "src/pipeline/application_scorer.py": "e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b",
        "src/pipeline/job_ranker.py": "5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54",
    }
    for relative_path, expected_hash in expected.items():
        assert hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )
