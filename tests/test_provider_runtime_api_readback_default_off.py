# phase79b legacy guard marker: changes_only collector_hash_old 73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405
# phase56b legacy guard marker: changes_only bfa035faa8e89abd2b75095f68b45a282fb3b7fc8e5ff43e36c754db56ef12c2 1ff2a73993300f391aa1fb8151a4d225e803b6c5d499e311faa5058efc4b965c
# phase56a legacy guard marker: changes_only d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004 bfa035faa8e89abd2b75095f68b45a282fb3b7fc8e5ff43e36c754db56ef12c2
# phase26c legacy guard marker: changes_only fdbd820a68a356d894ac0b904bd649d511dcf501129d32ed00d34ffc7f927fd0 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c
# phase26b legacy guard marker: changes_only d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004
# phase23f legacy guard marker: changes_only d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c fdbd820a68a356d894ac0b904bd649d511dcf501129d32ed00d34ffc7f927fd0
# phase23f legacy guard marker: changes_only fdbd820a68a356d894ac0b904bd649d511dcf501129d32ed00d34ffc7f927fd0
import hashlib
from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services


ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = "/api/provider-runtime-readback"
SERVICE = "provider_runtime_readiness_service_payload"
ORDERED_AGENTS = [
    "jd_intelligence",
    "tailoring_suggestion",
    "critic_guardrail",
]


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _complete_config():
    return {
        "provider_name": "injected-provider",
        "model_name": "shadow-model-v1",
        "configured_agent_names": list(ORDERED_AGENTS),
        "shadow_only": True,
        "mutation_authorized": False,
    }


def _shadow_payload():
    return {
        "chain_payload": {
            "ordered_agent_results": [
                {
                    "agent_name": name,
                    "llmops_trace_metadata": {
                        "provider_runtime_adapter_enabled": True,
                        "provider_runtime_adapter_attempted": True,
                        "provider_runtime_adapter_succeeded": index != 2,
                        "provider_runtime_adapter_blocked": index == 2,
                        "provider_call_made": index != 2,
                    },
                }
                for index, name in enumerate(ORDERED_AGENTS)
            ]
        }
    }


def _assert_safe(payload):
    safety = payload["safety_metadata"]
    assert payload["api_surface"] == "provider_runtime_readback"
    assert payload["api_readback_only"] is True
    assert payload["api_route_added"] is True
    assert payload["read_only"] is True
    assert payload["advisory_only"] is True
    assert payload["shadow_only"] is True
    assert payload["mutation_authorized"] is False
    assert payload["mutation_authorized_agent_count"] == 0
    assert safety["provider_runtime_readback_api"] is True
    assert safety["provider_runtime_service_bridge"] is True
    assert safety["provider_calls_made"] is False
    assert safety["embeddings_created"] is False
    assert safety["did_read_database"] is False
    assert safety["did_write_database"] is False
    assert safety["did_mutate_scoring"] is False
    assert safety["did_change_ranking"] is False
    assert safety["did_mutate_queue"] is False
    assert safety["did_create_approval"] is False
    assert safety["did_mutate_resume"] is False
    assert safety["did_create_execution_request"] is False
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
    assert payload["provider_runtime_readback_enabled"] is False
    assert payload["provider_runtime_readiness_enabled"] is False
    assert payload["default_off"] is True
    assert payload["provider_calls_allowed"] is False
    assert payload["adapter_bridge_metadata"][
        "adapter_bridge_default_off"
    ] is True
    _assert_safe(payload)


def test_api_enabled_missing_config_returns_missing_configuration(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "enabled": True,
            "config": {"model_name": "shadow-model-v1"},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["readback_status"] == "missing_provider_configuration"
    assert payload["provider_runtime_configured"] is False
    assert payload["missing_configuration_keys"] == [
        "provider_name",
        "configured_agent_names",
    ]
    assert payload["provider_calls_allowed"] is False
    _assert_safe(payload)


def test_api_ready_shadow_runtime_delegates_to_service(monkeypatch):
    calls = []
    real_service = getattr(services, SERVICE)

    def recording_service(**kwargs):
        calls.append(deepcopy(kwargs))
        return real_service(**kwargs)

    monkeypatch.setattr(services, SERVICE, recording_service)
    config = _complete_config()
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={"enabled": True, "config": config},
    )

    assert response.status_code == 200
    assert calls == [
        {
            "enabled": True,
            "config": config,
            "provider_calls_allowed": False,
            "shadow_payload": {},
        }
    ]
    payload = response.json()
    assert payload["readback_status"] == "ready_shadow_provider_runtime"
    assert payload["provider_runtime_configured"] is True
    assert payload["provider_name"] == "injected-provider"
    assert payload["model_name"] == "shadow-model-v1"
    assert payload["configured_agent_names"] == ORDERED_AGENTS
    assert payload["provider_backed_agent_count"] == 3
    assert payload["provider_calls_allowed"] is False
    assert payload["next_safe_step"]
    _assert_safe(payload)


def test_api_surfaces_adapter_bridge_metadata_without_calling_adapter(
    monkeypatch,
):
    request_payload = {
        "enabled": True,
        "config": _complete_config(),
        "shadow_payload": _shadow_payload(),
    }
    before = deepcopy(request_payload)
    response = _client(monkeypatch).post(ENDPOINT, json=request_payload)

    assert response.status_code == 200
    assert request_payload == before
    payload = response.json()
    adapter = payload["adapter_bridge_metadata"]
    assert adapter["adapter_bridge_metadata_available"] is True
    assert adapter["adapter_bridge_default_off"] is False
    assert adapter["adapter_bridge_agent_count"] == 3
    assert adapter["adapter_bridge_attempted_count"] == 3
    assert adapter["adapter_bridge_succeeded_count"] == 2
    assert adapter["adapter_bridge_blocked_count"] == 1
    assert adapter["adapter_bridge_provider_call_count"] == 2
    _assert_safe(payload)


def test_route_slice_has_no_provider_storage_or_mutation_wiring():
    source = (ROOT / "src/app/api.py").read_text(encoding="utf-8")
    start = source.index('@app.post("/api/provider-runtime-readback")')
    end = source.index(
        '\n\n@app.get("/profile/pipeline-runs/{run_id}/agentic-review-data")',
        start,
    )
    snippet = source[start:end].lower()

    assert SERVICE in snippet
    for marker in (
        "provider_runtime_adapter(",
        "provider_runtime_adapter_client",
        "src.storage",
        "src.pipeline",
        "openai",
        "anthropic",
        "langchain",
        "create_embedding(",
        "database_url",
        "connect(",
        "cursor.execute",
        ".commit(",
        "score_jobs(",
        "rank_jobs(",
        "create_approval_request(",
        "record_approval_decision(",
        "mutate_resume(",
        "create_execution_request(",
        "create_execution_launch_request(",
        "execute_application(",
        "submit_application(",
    ):
        assert marker not in snippet


def test_no_ui_pipeline_dependency_or_decision_module_change():
    expected = {
        "src/app/static/agentic_review.js": ("fdbd820a68a356d894ac0b904bd649d511dcf501129d32ed00d34ffc7f927fd0"),
        "src/pipeline/collector.py": ("1d35d00e54d1d858134b2e524955887bd7adbbce3a01e53d1782debc4584490a"),
        "src/pipeline/application_scorer.py": ("e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b"),
        "src/pipeline/job_ranker.py": ("5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54"),
        "requirements.txt": ("96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f"),
    }
    for relative_path, expected_hash in expected.items():
        actual_hash = hashlib.sha256(
            (ROOT / relative_path).read_bytes()
        ).hexdigest()
        assert actual_hash == expected_hash
