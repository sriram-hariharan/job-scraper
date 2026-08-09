from __future__ import annotations

from copy import deepcopy
import inspect
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.ai import user_provider_runtime as runtime
from src.ai.provider_model_catalog import CONFIGURATION_CANDIDATE_MODEL_ORDER
from src.evaluation.provider_client_compatibility import _isolated_shared_client


ROOT = Path(__file__).resolve().parents[1]
MESSAGES = [{"role": "user", "content": "bounded synthetic request"}]
SCHEMA = {
    "type": "object",
    "properties": {"status": {"type": "string"}},
    "required": ["status"],
    "additionalProperties": False,
}
USER_A_SECRET = "synthetic-user-a-provider-secret"


class _CapturingClient:
    def __init__(self, content='{"status":"ok"}', error=None, **message_fields):
        self.calls = []
        self.content = content
        self.error = error
        self.message_fields = message_fields
        self.chat = SimpleNamespace(
            completions=SimpleNamespace(create=self._create)
        )

    def _create(self, **kwargs):
        self.calls.append(deepcopy(kwargs))
        if self.error is not None:
            raise self.error
        message = SimpleNamespace(content=self.content, **self.message_fields)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


@pytest.fixture
def client_module():
    with _isolated_shared_client() as (module, observations):
        yield module, observations


@pytest.mark.parametrize(
    ("provider", "model", "getter_name"),
    (
        ("groq", "openai/gpt-oss-20b", "get_groq_client"),
        ("openai", "gpt-5-mini", "get_openai_client"),
    ),
)
def test_legacy_path_still_acquires_existing_global_client(
    client_module,
    provider,
    model,
    getter_name,
):
    module, _ = client_module
    fake = _CapturingClient(content="bounded legacy success")
    getter_calls = []

    def getter():
        getter_calls.append(provider)
        return fake

    setattr(module, getter_name, getter)

    result = module._run_single_provider(
        provider_name=provider,
        messages=MESSAGES,
        model=model,
        temperature=0,
        max_tokens=32,
    )

    assert result == "bounded legacy success"
    assert getter_calls == [provider]
    assert len(fake.calls) == 1


@pytest.mark.parametrize(
    ("provider", "model", "getter_name"),
    (
        ("groq", "openai/gpt-oss-20b", "get_groq_client"),
        ("openai", "gpt-5-mini", "get_openai_client"),
    ),
)
def test_explicit_client_bypasses_global_acquisition_environment_and_cache(
    client_module,
    provider,
    model,
    getter_name,
):
    module, observations = client_module
    explicit_client = _CapturingClient(content="bounded explicit success")
    groq_sentinel = object()
    openai_sentinel = object()
    module._groq_client = groq_sentinel
    module._openai_client = openai_sentinel
    setattr(
        module,
        getter_name,
        lambda: pytest.fail("global provider getter must be bypassed"),
    )

    result = module._run_single_provider(
        provider_name=provider,
        messages=MESSAGES,
        model=model,
        temperature=0,
        max_tokens=32,
        provider_client=explicit_client,
    )

    assert result == "bounded explicit success"
    assert len(explicit_client.calls) == 1
    assert module._groq_client is groq_sentinel
    assert module._openai_client is openai_sentinel
    assert observations["credential_reads"] == 0


def test_explicit_groq_client_uses_shared_gpt_oss_and_schema_request_surface(
    client_module,
):
    module, _ = client_module
    explicit_client = _CapturingClient()
    module.get_groq_client = lambda: pytest.fail("global getter must be bypassed")
    module.reset_provider_metrics()

    payload = module.run_chat_completion_with_metadata(
        messages=deepcopy(MESSAGES),
        provider="groq",
        model="openai/gpt-oss-20b",
        temperature=0.25,
        max_tokens=96,
        response_mime_type="application/json",
        response_schema=deepcopy(SCHEMA),
        return_parsed=True,
        fallback_enabled=False,
        provider_client=explicit_client,
    )

    assert payload == {
        "content": {"status": "ok"},
        "provider": "groq",
        "model": "openai/gpt-oss-20b",
        "fallback_used": False,
    }
    assert explicit_client.calls == [
        {
            "model": "openai/gpt-oss-20b",
            "temperature": 0.25,
            "max_completion_tokens": 96,
            "messages": MESSAGES,
            "include_reasoning": False,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "structured_output",
                    "strict": True,
                    "schema": SCHEMA,
                },
            },
        }
    ]
    assert module.get_provider_metrics() == {
        "primary_attempts": 1,
        "fallback_attempts": 0,
        "groq_calls": 1,
        "openai_calls": 0,
        "gemini_calls": 0,
        "fallback_successes": 0,
        "provider_failures": 0,
    }


def test_explicit_openai_client_preserves_gpt5_mini_compatibility_and_schema(
    client_module,
):
    module, _ = client_module
    explicit_client = _CapturingClient()
    module.get_openai_client = lambda: pytest.fail("global getter must be bypassed")
    module.reset_provider_metrics()

    payload = module.run_chat_completion_with_metadata(
        messages=deepcopy(MESSAGES),
        provider="openai",
        model="gpt-5-mini",
        temperature=0,
        max_tokens=72,
        response_mime_type="application/json",
        response_schema=deepcopy(SCHEMA),
        return_parsed=True,
        thinking_budget=0,
        fallback_enabled=False,
        provider_client=explicit_client,
    )

    assert payload["content"] == {"status": "ok"}
    request = explicit_client.calls[0]
    assert request == {
        "model": "gpt-5-mini",
        "max_completion_tokens": 72,
        "messages": MESSAGES,
        "reasoning_effort": "minimal",
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "structured_output",
                "strict": True,
                "schema": SCHEMA,
            },
        },
    }
    assert "temperature" not in request
    assert module.get_provider_metrics()["openai_calls"] == 1


@pytest.mark.parametrize("provider", ("groq", "openai"))
def test_explicit_client_preserves_json_object_and_parsed_response_behavior(
    client_module,
    provider,
):
    module, _ = client_module
    model = "openai/gpt-oss-120b" if provider == "groq" else "gpt-5.1"
    explicit_client = _CapturingClient(content='{"items":[1,2]}')

    payload = module.run_chat_completion_with_metadata(
        messages=MESSAGES,
        provider=provider,
        model=model,
        response_mime_type="application/json",
        return_parsed=True,
        fallback_enabled=False,
        provider_client=explicit_client,
    )

    assert payload["content"] == {"items": [1, 2]}
    assert explicit_client.calls[0]["response_format"] == {
        "type": "json_object"
    }


@pytest.mark.parametrize(
    ("provider", "model", "message_fields"),
    (
        (
            "groq",
            "openai/gpt-oss-20b",
            {"refusal": "synthetic refusal", "reasoning": "synthetic reasoning"},
        ),
        ("openai", "gpt-5-mini", {"refusal": "synthetic refusal"}),
    ),
)
def test_explicit_client_preserves_empty_and_refusal_response_handling(
    client_module,
    provider,
    model,
    message_fields,
):
    module, _ = client_module
    explicit_client = _CapturingClient(content=None, **message_fields)

    with pytest.raises(module._ProviderResponseError) as exc_info:
        module._run_single_provider(
            provider_name=provider,
            messages=MESSAGES,
            model=model,
            temperature=0,
            max_tokens=32,
            provider_client=explicit_client,
        )

    rendered = str(exc_info.value)
    assert "refusal_present=true" in rendered
    assert "synthetic refusal" not in rendered
    assert len(explicit_client.calls) == 1


def test_explicit_client_errors_keep_existing_classification_metrics_and_bounds(
    client_module,
):
    module, _ = client_module
    explicit_client = _CapturingClient(
        error=TimeoutError(f"timeout body {USER_A_SECRET}")
    )
    module.reset_provider_metrics()

    with pytest.raises(RuntimeError) as exc_info:
        module.run_chat_completion_with_metadata(
            messages=MESSAGES,
            provider="groq",
            model="openai/gpt-oss-20b",
            fallback_enabled=False,
            provider_client=explicit_client,
        )

    rendered = str(exc_info.value)
    assert "category=timeout" in rendered
    assert USER_A_SECRET not in rendered
    assert len(explicit_client.calls) == 1
    metrics = module.get_provider_metrics()
    assert metrics["primary_attempts"] == 1
    assert metrics["groq_calls"] == 1
    assert metrics["provider_failures"] == 1
    assert metrics["fallback_attempts"] == 0


@pytest.mark.parametrize("fallback_enabled", (True, None))
def test_explicit_client_with_effective_fallback_fails_before_any_request(
    client_module,
    fallback_enabled,
):
    module, _ = client_module
    module.FALLBACK_ENABLED = True
    explicit_client = _CapturingClient()
    module.get_groq_client = lambda: pytest.fail("global getter must not run")
    module.get_openai_client = lambda: pytest.fail("fallback getter must not run")
    module.reset_provider_metrics()

    with pytest.raises(ValueError) as exc_info:
        module.run_chat_completion_with_metadata(
            messages=MESSAGES,
            provider="groq",
            model="openai/gpt-oss-20b",
            fallback_enabled=fallback_enabled,
            fallback_provider="openai",
            fallback_model="gpt-5-mini",
            provider_client=explicit_client,
        )

    assert getattr(exc_info.value, "error_category") == "configuration"
    assert explicit_client.calls == []
    assert all(value == 0 for value in module.get_provider_metrics().values())


def test_content_only_wrapper_propagates_explicit_client(client_module):
    module, _ = client_module
    explicit_client = _CapturingClient(content="bounded content")

    content = module.run_chat_completion(
        messages=MESSAGES,
        provider="openai",
        model="gpt-5.1",
        fallback_enabled=False,
        provider_client=explicit_client,
    )

    assert content == "bounded content"
    assert len(explicit_client.calls) == 1


def test_provider_client_is_appended_to_all_shared_transport_signatures(
    client_module,
):
    module, _ = client_module
    for function_name in (
        "_run_groq_chat_completion",
        "_run_openai_chat_completion",
        "_run_single_provider",
        "run_chat_completion_with_metadata",
        "run_chat_completion",
    ):
        parameters = list(inspect.signature(getattr(module, function_name)).parameters)
        assert parameters[-1] == "provider_client"


@pytest.mark.parametrize(
    ("provider", "model"),
    (
        ("groq", "arbitrary-model"),
        ("groq", "llama-3.1-8b-instant"),
        ("groq", "gpt-5-mini"),
        ("openai", "openai/gpt-oss-20b"),
        ("openai", "unknown-model"),
    ),
)
def test_user_runtime_rejects_non_catalog_and_mismatched_models_before_build(
    monkeypatch,
    provider,
    model,
):
    monkeypatch.setattr(
        runtime,
        "build_user_provider_client",
        lambda *_args, **_kwargs: pytest.fail("client must not be built"),
    )

    with pytest.raises(runtime.UserProviderRuntimeConfigurationError) as exc_info:
        runtime.run_user_chat_completion_with_metadata(
            "synthetic-user-a",
            provider,
            model,
            MESSAGES,
        )

    assert exc_info.value.category == "unsupported_provider_model"
    assert model not in str(exc_info.value)


@pytest.mark.parametrize(
    ("provider", "model"),
    CONFIGURATION_CANDIDATE_MODEL_ORDER,
)
def test_user_runtime_accepts_every_exact_catalog_pair_and_delegates_once(
    monkeypatch,
    provider,
    model,
):
    client = object()
    build_calls = []
    transport_calls = []

    def build(owner_user_id, provider_name, **kwargs):
        build_calls.append((owner_user_id, provider_name, kwargs))
        return client

    def transport(**kwargs):
        transport_calls.append(kwargs)
        return {
            "content": "bounded success",
            "provider": kwargs["provider"],
            "model": kwargs["model"],
            "fallback_used": False,
        }

    monkeypatch.setattr(runtime, "build_user_provider_client", build)
    monkeypatch.setattr(
        runtime,
        "_run_shared_chat_completion_with_metadata",
        transport,
    )

    result = runtime.run_user_chat_completion_with_metadata(
        " synthetic-user-a ",
        provider.upper(),
        f" {model} ",
        MESSAGES,
        temperature=0.4,
        max_tokens=84,
        response_mime_type="application/json",
        response_schema=SCHEMA,
        return_parsed=True,
        thinking_budget=0,
        database_url="synthetic-db",
        database_url_env="SYNTHETIC_DATABASE_URL",
        psql_bin="synthetic-psql",
        ensure_schema=False,
    )

    assert build_calls == [
        (
            "synthetic-user-a",
            provider,
            {
                "database_url": "synthetic-db",
                "database_url_env": "SYNTHETIC_DATABASE_URL",
                "psql_bin": "synthetic-psql",
                "ensure_schema": False,
            },
        )
    ]
    assert transport_calls == [
        {
            "messages": MESSAGES,
            "model": model,
            "temperature": 0.4,
            "max_tokens": 84,
            "provider": provider,
            "response_mime_type": "application/json",
            "response_schema": SCHEMA,
            "return_parsed": True,
            "thinking_budget": 0,
            "fallback_enabled": False,
            "provider_client": client,
        }
    ]
    assert result == {
        "content": "bounded success",
        "provider": provider,
        "model": model,
        "fallback_used": False,
    }
    rendered = json.dumps(result)
    assert "provider_client" not in rendered
    assert USER_A_SECRET not in rendered


def test_user_a_and_b_requests_receive_distinct_exact_clients(monkeypatch):
    client_a = object()
    client_b = object()
    clients = {
        "synthetic-user-a": client_a,
        "synthetic-user-b": client_b,
    }
    builds = []
    transports = []

    def build(owner_user_id, provider, **_kwargs):
        builds.append((owner_user_id, provider))
        return clients[owner_user_id]

    def transport(**kwargs):
        transports.append(kwargs["provider_client"])
        return {
            "content": "bounded",
            "provider": kwargs["provider"],
            "model": kwargs["model"],
            "fallback_used": False,
        }

    monkeypatch.setattr(runtime, "build_user_provider_client", build)
    monkeypatch.setattr(
        runtime,
        "_run_shared_chat_completion_with_metadata",
        transport,
    )

    for owner_user_id in clients:
        runtime.run_user_chat_completion_with_metadata(
            owner_user_id,
            "groq",
            "openai/gpt-oss-20b",
            MESSAGES,
        )

    assert client_a is not client_b
    assert builds == [
        ("synthetic-user-a", "groq"),
        ("synthetic-user-b", "groq"),
    ]
    assert transports == [client_a, client_b]


def test_user_runtime_provider_failure_is_bounded_without_client_or_credential(
    monkeypatch,
    client_module,
):
    module, _ = client_module
    client = _CapturingClient(
        error=ConnectionError(f"client={object()!r} credential={USER_A_SECRET}")
    )
    monkeypatch.setattr(
        runtime,
        "build_user_provider_client",
        lambda *_args, **_kwargs: client,
    )
    monkeypatch.setattr(
        runtime,
        "_run_shared_chat_completion_with_metadata",
        module.run_chat_completion_with_metadata,
    )

    with pytest.raises(RuntimeError) as exc_info:
        runtime.run_user_chat_completion_with_metadata(
            "synthetic-user-a",
            "groq",
            "openai/gpt-oss-20b",
            MESSAGES,
        )

    rendered = str(exc_info.value)
    assert "category=connection" in rendered
    assert USER_A_SECRET not in rendered
    assert "client=<" not in rendered
    assert len(client.calls) == 1


def test_user_runtime_keeps_shared_transport_import_lazy():
    source = (ROOT / "src/ai/user_provider_runtime.py").read_text(encoding="utf-8")
    prefix = source.split("def _run_shared_chat_completion_with_metadata", 1)[0]
    assert "llm_client" not in prefix
    assert "chat.completions.create" not in source
    assert "responses.create" not in source
    assert "fallback_enabled=False" in source
    assert "provider_client=provider_client" in source
