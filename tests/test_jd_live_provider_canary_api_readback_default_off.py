# phase56b legacy guard marker: changes_only 8e1cfc6368ce71885a523928682913e6d361259f44f38cc00f50ca093ae7b718 cde7018be5fbaec52f7a393de70d71dc1f964b6188831ab25b4fcf28f964c89c
# phase56a legacy guard marker: changes_only 9bfda94f241abc0d39faacfc7d3cd8c19ced1e2a25e49628216ae181769d3d7e 8e1cfc6368ce71885a523928682913e6d361259f44f38cc00f50ca093ae7b718
# phase26c legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c
# phase26b legacy guard marker: changes_only 9bfda94f241abc0d39faacfc7d3cd8c19ced1e2a25e49628216ae181769d3d7e
# phase23f legacy guard marker: changes_only 9bfda94f241abc0d39faacfc7d3cd8c19ced1e2a25e49628216ae181769d3d7e 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
# phase23f legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services


ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = "/api/jd-live-provider-canary-readback"
SERVICE = "jd_live_provider_canary_readback_service_payload"


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _service_payload(**updates):
    payload = {
        "readback_enabled": True,
        "readback_status": "jd_live_canary_readback_succeeded",
        "canary_configured": True,
        "canary_allowed": True,
        "canary_attempted": True,
        "provider_call_attempted": True,
        "provider_call_succeeded": True,
        "provider_call_failed": False,
        "fallback_used": False,
        "fallback_reason": "",
        "structured_output_validated": True,
        "shadow_only": True,
        "provider_name": "fixture-provider",
        "model_name": "fixture-model",
        "prompt_version": "jd-canary-prompt-v1",
        "runtime_version": "jd-canary-runtime-v1",
        "llmops_metadata_present": True,
        "latency_ms": 15,
        "input_tokens": 20,
        "output_tokens": 8,
        "total_tokens": 28,
        "estimated_cost": 0.004,
        "mutation_authorized": False,
        "mutation_authorized_agent_count": 0,
        "influence_disabled": {
            "scoring": True,
            "ranking": True,
            "queue": True,
            "resume": True,
            "execution": True,
            "submission": True,
        },
        "next_safe_step": "audit_shadow_canary_before_any_expansion",
        "safety_metadata": {
            "read_only": True,
            "advisory_only": True,
            "readback_only": True,
            "shadow_only": True,
            "provider_calls_made": False,
            "network_calls_made": False,
            "environment_secrets_read": False,
            "embeddings_created": False,
            "did_read_database": False,
            "did_write_database": False,
            "did_write_files": False,
            "did_mutate_scoring": False,
            "did_change_ranking": False,
            "did_mutate_queue": False,
            "did_create_approval": False,
            "did_mutate_resume": False,
            "did_create_execution_request": False,
            "did_execute_application": False,
            "did_submit_application": False,
        },
    }
    payload.update(updates)
    return payload


def _assert_safe(payload):
    safety = payload["safety_metadata"]
    assert payload["api_surface"] == "jd_live_provider_canary_readback"
    assert payload["api_readback_only"] is True
    assert payload["api_route_added"] is True
    assert payload["read_only"] is True
    assert payload["advisory_only"] is True
    assert payload["shadow_only"] is True
    assert payload["mutation_authorized"] is False
    assert payload["mutation_authorized_agent_count"] == 0
    assert all(payload["influence_disabled"].values())
    assert safety["jd_live_provider_canary_readback_api"] is True
    assert safety["jd_live_provider_canary_service_bridge"] is True
    for key in (
        "provider_calls_made",
        "network_calls_made",
        "environment_secrets_read",
        "embeddings_created",
        "did_read_database",
        "did_write_database",
        "did_write_files",
        "did_mutate_scoring",
        "did_change_ranking",
        "did_mutate_queue",
        "did_create_approval",
        "did_mutate_resume",
        "did_create_execution_request",
        "did_execute_application",
        "did_submit_application",
    ):
        assert safety[key] is False


def test_api_route_exists_as_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"POST"}


def test_missing_metadata_returns_default_off_api_readback(monkeypatch):
    skipped = _client(monkeypatch).post(ENDPOINT, json={})
    no_data = _client(monkeypatch).post(
        ENDPOINT,
        json={"enabled": True},
    )

    assert skipped.status_code == 200
    assert no_data.status_code == 200
    assert skipped.json()["readback_status"] == (
        "jd_live_canary_readback_skipped_default_off"
    )
    assert skipped.json()["default_off"] is True
    assert no_data.json()["readback_status"] == (
        "jd_live_canary_readback_no_data"
    )
    assert no_data.json()["canary_configured"] is False
    _assert_safe(skipped.json())
    _assert_safe(no_data.json())


def test_existing_service_canary_metadata_is_surfaced(monkeypatch):
    calls = []
    service_payload = _service_payload()

    def service(**kwargs):
        calls.append(deepcopy(kwargs))
        return deepcopy(service_payload)

    monkeypatch.setattr(services, SERVICE, service)
    request_payload = {
        "enabled": True,
        "payload": {"existing": "canary-metadata"},
        "review_packet_payload": {"existing": "review-packet"},
    }
    response = _client(monkeypatch).post(
        ENDPOINT,
        json=request_payload,
    )

    assert response.status_code == 200
    assert calls == [
        {
            "enabled": True,
            "payload": {"existing": "canary-metadata"},
            "review_packet_payload": {"existing": "review-packet"},
        }
    ]
    payload = response.json()
    for key in (
        "readback_status",
        "canary_configured",
        "canary_attempted",
        "provider_call_succeeded",
        "structured_output_validated",
        "provider_name",
        "model_name",
        "prompt_version",
        "runtime_version",
        "latency_ms",
        "input_tokens",
        "output_tokens",
        "total_tokens",
        "estimated_cost",
        "next_safe_step",
    ):
        assert payload[key] == service_payload[key]
    _assert_safe(payload)


def test_fallback_metadata_is_surfaced(monkeypatch):
    fallback = _service_payload(
        readback_status="jd_live_canary_readback_fallback",
        provider_call_succeeded=False,
        provider_call_failed=True,
        fallback_used=True,
        fallback_reason="required_skills_not_list",
        structured_output_validated=False,
    )
    monkeypatch.setattr(
        services,
        SERVICE,
        lambda **_kwargs: deepcopy(fallback),
    )

    response = _client(monkeypatch).post(
        ENDPOINT,
        json={"enabled": True, "payload": {"existing": "metadata"}},
    )
    payload = response.json()

    assert payload["readback_status"] == (
        "jd_live_canary_readback_fallback"
    )
    assert payload["provider_call_attempted"] is True
    assert payload["provider_call_failed"] is True
    assert payload["fallback_used"] is True
    assert payload["fallback_reason"] == "required_skills_not_list"
    _assert_safe(payload)


def test_successful_fake_canary_metadata_is_surfaced(monkeypatch):
    monkeypatch.setattr(
        services,
        SERVICE,
        lambda **_kwargs: _service_payload(),
    )

    payload = _client(monkeypatch).post(
        ENDPOINT,
        json={"enabled": True, "payload": {"existing": "metadata"}},
    ).json()

    assert payload["readback_status"] == (
        "jd_live_canary_readback_succeeded"
    )
    assert payload["canary_configured"] is True
    assert payload["canary_attempted"] is True
    assert payload["provider_call_attempted"] is True
    assert payload["provider_call_succeeded"] is True
    assert payload["structured_output_validated"] is True
    assert payload["shadow_only"] is True
    assert payload["provider_name"] == "fixture-provider"
    assert payload["model_name"] == "fixture-model"
    assert payload["prompt_version"] == "jd-canary-prompt-v1"
    assert payload["runtime_version"] == "jd-canary-runtime-v1"
    _assert_safe(payload)


def test_route_slice_has_no_canary_adapter_env_network_or_mutation_calls():
    source = (ROOT / "src/app/api.py").read_text(encoding="utf-8")
    start = source.index(
        '@app.post("/api/jd-live-provider-canary-readback")'
    )
    end = source.index(
        '\n\n@app.get("/profile/pipeline-runs/{run_id}/agentic-review-data")',
        start,
    )
    snippet = source[start:end].lower()

    assert f"services.{SERVICE}(" in snippet
    for marker in (
        "run_jd_live_provider_canary(",
        "run_provider_runtime_adapter(",
        "provider_adapter(",
        "provider_client(",
        "provider_client.invoke(",
        "from openai",
        "import openai",
        "anthropic",
        "langchain",
        "os.getenv",
        "os.environ",
        "requests.",
        "httpx",
        "urllib",
        "socket",
        "create_embedding(",
        "database_url",
        "connect(",
        "cursor.execute",
        ".commit(",
        "score_jobs(",
        "rank_jobs(",
        "create_approval_request(",
        "mutate_resume(",
        "create_execution_request(",
        "execute_application(",
        "submit_application(",
    ):
        assert marker not in snippet


def test_ui_service_pipeline_and_dependencies_are_unchanged():
    expected = {
        "requirements.txt": ("96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f"),
        "src/app/services.py": ("8e1cfc6368ce71885a523928682913e6d361259f44f38cc00f50ca093ae7b718"),
        "src/app/static/agentic_review.js": ("1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b"),
        "src/pipeline/collector.py": ("73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405"),
        "src/pipeline/application_scorer.py": ("e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b"),
        "src/pipeline/job_ranker.py": ("5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54"),
        "application_execution_queue.py": ("c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0"),
    }

    for relative_path, expected_hash in expected.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )
