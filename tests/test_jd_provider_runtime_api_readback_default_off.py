# phase56b legacy guard marker: changes_only 55cd268d47f736c91a7439c6c2e2b4ce0e6ffc8610a63e62d1b2cf2d82e6be73 aafc8a883fe8f4b7ea48fff9d8cd8500e1190b2650290370195d79c3f91b19db
# phase56a legacy guard marker: changes_only d648586134fc13216ff75c6f362dd430ff4b772de6999adff0adc3452d96627d 55cd268d47f736c91a7439c6c2e2b4ce0e6ffc8610a63e62d1b2cf2d82e6be73
# phase26c legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c
# phase26b legacy guard marker: changes_only d648586134fc13216ff75c6f362dd430ff4b772de6999adff0adc3452d96627d
# phase23f legacy guard marker: changes_only d648586134fc13216ff75c6f362dd430ff4b772de6999adff0adc3452d96627d 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
# phase23f legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
import hashlib
from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient

from src.agents import pipeline_agent_review_packet, shadow_sidecar_hook
from src.app import api, services


ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = "/api/jd-provider-runtime-readback"
SERVICE = "jd_provider_runtime_readback_service_payload"


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _hook(**updates):
    kwargs = {
        "run_id": "run-phase-12g",
        "batch_id": "batch-phase-12g",
        "job_id": "job-phase-12g",
        "stage_name": "post_final_scoring",
        "source_deterministic_stage": "application_priority",
        "source_deterministic_status": "completed",
        "source_deterministic_score": 0.9,
        "source_deterministic_decision": "qualified_for_review",
        "three_agent_shadow_workflow_enabled": True,
        "job_payload": {"job_description": "Build Python systems."},
    }
    kwargs.update(updates)
    return shadow_sidecar_hook.run_shadow_sidecar_pipeline_hook(**kwargs)


def _valid_output():
    return {
        "required_skills": ["Python"],
        "preferred_skills": [],
        "required_tools": [],
        "preferred_tools": [],
        "workflows": ["data systems"],
        "methods": [],
        "business_contexts": [],
        "stakeholder_contexts": [],
        "ownership_signals": [],
        "seniority_signals": [],
        "risk_flags": [],
        "extraction_confidence": 0.9,
    }


def _response(output):
    return {
        "output": deepcopy(output),
        "provider_name": "fixture-provider",
        "model_name": "fixture-model",
        "schema_validation_status": "valid",
    }


def _assert_safe(payload):
    safety = payload["safety_metadata"]
    assert payload["api_surface"] == "jd_provider_runtime_readback"
    assert payload["api_readback_only"] is True
    assert payload["api_route_added"] is True
    assert payload["read_only"] is True
    assert payload["advisory_only"] is True
    assert payload["shadow_only"] is True
    assert payload["mutation_authorized"] is False
    assert payload["mutation_authorized_agent_count"] == 0
    assert safety["jd_provider_runtime_readback_api"] is True
    assert safety["jd_provider_runtime_service_bridge"] is True
    for key in (
        "provider_calls_made",
        "network_calls_made",
        "embeddings_created",
        "did_read_database",
        "did_write_database",
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


def test_api_default_off_and_missing_payload_are_safe(monkeypatch):
    skipped = _client(monkeypatch).post(ENDPOINT, json={})
    no_data = _client(monkeypatch).post(
        ENDPOINT,
        json={"enabled": True},
    )

    assert skipped.status_code == 200
    assert no_data.status_code == 200
    assert skipped.json()["readback_status"] == (
        "jd_provider_runtime_readback_skipped_default_off"
    )
    assert skipped.json()["default_off"] is True
    assert no_data.json()["readback_status"] == (
        "jd_provider_runtime_readback_no_data"
    )
    assert no_data.json()["provider_calls_allowed"] is False
    _assert_safe(skipped.json())
    _assert_safe(no_data.json())


def test_api_summarizes_default_off_shadow_metadata(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={"enabled": True, "payload": _hook()},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["readback_status"] == (
        "jd_provider_runtime_readback_not_attempted"
    )
    assert payload["jd_provider_runtime_attempted"] is False
    assert payload["jd_provider_runtime_enabled"] is False
    _assert_safe(payload)


def test_api_summarizes_blocked_fallback_metadata(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "enabled": True,
            "payload": _hook(
                jd_provider_runtime_activation_enabled=True
            ),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["readback_status"] == (
        "jd_provider_runtime_readback_blocked"
    )
    assert payload["fallback_used"] is True
    assert payload["fallback_reason"]
    _assert_safe(payload)


def test_api_delegates_and_summarizes_validated_success(monkeypatch):
    calls = []
    service_calls = []
    real_service = getattr(services, SERVICE)

    def fake_client(request):
        calls.append(deepcopy(request))
        return _response(_valid_output())

    hook = _hook(
        jd_provider_runtime_activation_enabled=True,
        jd_provider_runtime_activation_client=fake_client,
    )
    provider_calls_before = deepcopy(calls)

    def recording_service(**kwargs):
        service_calls.append(deepcopy(kwargs))
        return real_service(**kwargs)

    monkeypatch.setattr(services, SERVICE, recording_service)
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={"enabled": True, "payload": hook},
    )

    assert response.status_code == 200
    assert calls == provider_calls_before
    assert service_calls == [
        {
            "enabled": True,
            "payload": hook,
            "review_packet_payload": {},
        }
    ]
    payload = response.json()
    assert payload["readback_status"] == (
        "jd_provider_runtime_readback_succeeded"
    )
    assert payload["jd_provider_runtime_attempted"] is True
    assert payload["jd_provider_runtime_succeeded"] is True
    assert payload["structured_output_validated"] is True
    assert payload["configured_provider_name"] == "fixture-provider"
    assert payload["configured_model_name"] == "fixture-model"
    _assert_safe(payload)


def test_api_summarizes_invalid_and_failed_fallback(monkeypatch):
    invalid = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "enabled": True,
            "payload": _hook(
                jd_provider_runtime_activation_enabled=True,
                jd_provider_runtime_activation_provider=lambda _request: (
                    _response({"required_skills": {"invalid": "shape"}})
                ),
            ),
        },
    )

    def failing_client(_request):
        raise RuntimeError("fixture failure")

    failed = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "enabled": True,
            "payload": _hook(
                jd_provider_runtime_activation_enabled=True,
                jd_provider_runtime_activation_client=failing_client,
            ),
        },
    )

    assert invalid.json()["readback_status"] == (
        "jd_provider_runtime_readback_validation_failed"
    )
    assert invalid.json()["fallback_reason"] == "required_skills_not_list"
    assert failed.json()["readback_status"] == (
        "jd_provider_runtime_readback_failed"
    )
    assert failed.json()["fallback_reason"] == "RuntimeError"
    _assert_safe(invalid.json())
    _assert_safe(failed.json())


def test_api_preserves_review_packet_compatible_summary(monkeypatch):
    hook = _hook(
        jd_provider_runtime_activation_enabled=True,
        jd_provider_runtime_activation_client=lambda _request: (
            _response(_valid_output())
        ),
    )
    packet = (
        pipeline_agent_review_packet
        .build_pipeline_agent_review_packet_payload(hook_payload=hook)
    )
    before = deepcopy(packet)
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "enabled": True,
            "review_packet_payload": packet,
        },
    )

    assert response.status_code == 200
    assert packet == before
    payload = response.json()
    assert payload["readback_status"] == packet[
        "jd_provider_runtime_readback"
    ]["readback_status"]
    assert payload["review_packet_compatible"] is True
    _assert_safe(payload)


def test_route_slice_has_no_activation_client_network_storage_or_mutation():
    source = (ROOT / "src/app/api.py").read_text(encoding="utf-8")
    start = source.index('@app.post("/api/jd-provider-runtime-readback")')
    end = source.index(
        '\n\n@app.get("/profile/pipeline-runs/{run_id}/agentic-review-data")',
        start,
    )
    snippet = source[start:end].lower()

    assert f"services.{SERVICE}(" in snippet
    for marker in (
        "run_jd_provider_runtime_activation(",
        "run_provider_runtime_adapter(",
        "provider_client",
        "provider_callable",
        "from openai",
        "import openai",
        "anthropic",
        "langchain",
        "os.getenv",
        "os.environ",
        "requests.",
        "httpx",
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


def test_ui_pipeline_and_dependencies_are_unchanged():
    expected = {
        "requirements.txt": ("96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f"),
        "src/app/static/agentic_review.js": ("1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b"),
        "src/pipeline/collector.py": ("73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405"),
        "src/pipeline/application_scorer.py": ("e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b"),
        "src/pipeline/job_ranker.py": ("5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54"),
        "application_execution_queue.py": ("c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0"),
    }
    for relative_path, expected_hash in expected.items():
        assert hashlib.sha256(
            (ROOT / relative_path).read_bytes()
        ).hexdigest() == expected_hash
