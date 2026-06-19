from copy import deepcopy
from pathlib import Path

from src.agents.provider_runtime_adapter import run_provider_runtime_adapter


ROOT = Path(__file__).resolve().parents[1]


def _request():
    return {
        "agent_name": "jd_intelligence",
        "prompt_version": "fixture-v1",
        "input": {"job_description": "Build data systems."},
    }


def _assert_safety(payload, *, called=False):
    safety = payload["safety_metadata"]
    assert safety["read_only"] is True
    assert safety["shadow_only"] is True
    assert safety["provider_calls_made"] is called
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
    assert payload["shadow_only"] is True
    assert payload["mutation_authorized"] is False
    assert payload["mutation_authorized_agent_count"] == 0


def test_default_off_blocks_provider_call():
    calls = []
    payload = run_provider_runtime_adapter(
        request_payload=_request(),
        provider_name="fixture",
        model_name="fixture-model",
        provider_callable=lambda request: calls.append(request),
    )

    assert calls == []
    assert payload["status"] == (
        "provider_runtime_adapter_skipped_default_off"
    )
    assert payload["provider_call_attempted"] is False
    assert payload["provider_call_succeeded"] is False
    assert payload["provider_call_blocked"] is True
    assert payload["fallback_used"] is True
    _assert_safety(payload)


def test_enabled_without_client_returns_missing_client_safely():
    payload = run_provider_runtime_adapter(
        enabled=True,
        request_payload=_request(),
        provider_name="fixture",
        model_name="fixture-model",
    )

    assert payload["status"] == "provider_runtime_adapter_missing_client"
    assert payload["provider_call_attempted"] is False
    assert payload["provider_call_blocked"] is True
    assert payload["error_type"] == "MissingInjectedProviderClient"
    assert payload["schema_validation_status"] == (
        "not_executed_missing_client"
    )
    _assert_safety(payload)


def test_enabled_fake_callable_returns_normalized_output():
    calls = []

    def provider(request):
        calls.append(deepcopy(request))
        return {
            "output": {"required_skills": ["Python"]},
            "provider_name": "fixture-provider",
            "model_name": "fixture-model-v2",
            "schema_validation_status": "valid",
        }

    request = _request()
    payload = run_provider_runtime_adapter(
        enabled=True,
        request_payload=request,
        provider_callable=provider,
    )

    assert calls == [request]
    assert payload["status"] == "provider_runtime_adapter_ready"
    assert payload["provider_mechanism"] == (
        "injected_provider_callable"
    )
    assert payload["provider_call_attempted"] is True
    assert payload["provider_call_succeeded"] is True
    assert payload["provider_call_blocked"] is False
    assert payload["provider_name"] == "fixture-provider"
    assert payload["model_name"] == "fixture-model-v2"
    assert payload["output"] == {"required_skills": ["Python"]}
    assert payload["schema_validation_status"] == "valid"
    assert payload["fallback_used"] is False
    _assert_safety(payload, called=True)


def test_injected_invoke_client_shape_is_supported():
    class FakeClient:
        def __init__(self):
            self.calls = []

        def invoke(self, request):
            self.calls.append(deepcopy(request))
            return {"content": {"critic_status": "approved"}}

    client = FakeClient()
    request = _request()
    payload = run_provider_runtime_adapter(
        enabled=True,
        request_payload=request,
        provider_client=client,
    )

    assert client.calls == [request]
    assert payload["provider_mechanism"] == "injected_invoke_client"
    assert payload["output"] == {"critic_status": "approved"}
    _assert_safety(payload, called=True)


def test_fake_client_exception_is_non_blocking_fallback():
    def provider(_request):
        raise RuntimeError("fixture failure")

    payload = run_provider_runtime_adapter(
        enabled=True,
        request_payload=_request(),
        provider_callable=provider,
    )

    assert payload["status"] == (
        "provider_runtime_adapter_failed_non_blocking"
    )
    assert payload["provider_call_attempted"] is True
    assert payload["provider_call_succeeded"] is False
    assert payload["provider_call_blocked"] is False
    assert payload["fallback_used"] is True
    assert payload["error_type"] == "RuntimeError"
    assert payload["schema_validation_status"] == "fallback"
    _assert_safety(payload, called=True)


def test_token_cost_and_latency_metadata_are_normalized():
    payload = run_provider_runtime_adapter(
        enabled=True,
        request_payload=_request(),
        provider_callable=lambda _request: {
            "output": {"ok": True},
            "latency_ms": "17",
            "token_usage": {
                "prompt_tokens": "12",
                "completion_tokens": 8,
                "total_tokens": "20",
            },
            "cost": {"estimated_cost": "0.0042"},
            "validation_status": "valid",
        },
    )

    assert payload["latency_ms"] == 17
    assert payload["input_tokens"] == 12
    assert payload["output_tokens"] == 8
    assert payload["total_tokens"] == 20
    assert payload["estimated_cost"] == 0.0042
    assert payload["schema_validation_status"] == "valid"


def test_adapter_does_not_mutate_input_request():
    request = _request()
    before = deepcopy(request)

    run_provider_runtime_adapter(
        enabled=True,
        request_payload=request,
        provider_callable=lambda provider_request: {
            "output": {
                "received": deepcopy(provider_request),
            }
        },
    )

    assert request == before


def test_adapter_has_no_sdk_network_storage_or_mutation_wiring():
    source = (
        ROOT / "src/agents/provider_runtime_adapter.py"
    ).read_text(encoding="utf-8").lower()
    forbidden = (
        "from openai",
        "import openai",
        "anthropic",
        "langchain",
        "sentence_transformers",
        "requests.",
        "httpx",
        "urllib",
        "socket",
        "os.getenv",
        "os.environ",
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
    )
    for marker in forbidden:
        assert marker not in source


def test_no_service_api_ui_pipeline_or_dependency_wiring():
    sources = (
        ROOT / "src/app/api.py",
        ROOT / "src/pipeline/collector.py",
        ROOT / "requirements.txt",
    )
    for path in sources:
        source = path.read_text(encoding="utf-8")
        assert "provider_runtime_adapter" not in source
        assert "run_provider_runtime_adapter" not in source
