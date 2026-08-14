from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

import groq
import openai
import pytest

from src.ai import user_provider_runtime as runtime
from src.ai.provider_model_catalog import list_configurable_providers
from src.evaluation.provider_client_compatibility import _isolated_shared_client


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = ROOT / "src/ai/user_provider_runtime.py"
A_GROQ_SECRET = "synthetic-a-groq-secret"
B_GROQ_SECRET = "synthetic-b-groq-secret"
A_OPENAI_SECRET = "synthetic-a-openai-secret"


class _FakeClient:
    def __init__(self, provider: str, api_key: str) -> None:
        self.provider = provider
        self.api_key = api_key
        self.request_calls = 0
        self.chat = SimpleNamespace(
            completions=SimpleNamespace(create=self._prohibited_request)
        )
        self.responses = SimpleNamespace(create=self._prohibited_request)
        self.models = SimpleNamespace(list=self._prohibited_request)

    def _prohibited_request(self, *_args, **_kwargs):
        self.request_calls += 1
        raise AssertionError("provider request methods must not be called")


def _install_credential_lookup(monkeypatch, credentials):
    calls = []

    def lookup(owner_user_id, provider, **kwargs):
        calls.append((owner_user_id, provider, kwargs))
        return credentials.get((owner_user_id, provider))

    monkeypatch.setattr(
        runtime,
        "_get_user_ai_provider_credential_for_server",
        lookup,
    )
    return calls


def _install_constructors(monkeypatch):
    constructions = []

    def construct(provider):
        def factory(*, api_key):
            client = _FakeClient(provider, api_key)
            constructions.append((provider, api_key, client))
            return client

        return factory

    monkeypatch.setattr(runtime, "Groq", construct("groq"))
    monkeypatch.setattr(runtime, "OpenAI", construct("openai"))
    return constructions


def test_configurable_provider_catalog_is_the_authoritative_allowlist(monkeypatch):
    assert list_configurable_providers() == ["groq", "openai"]
    monkeypatch.setattr(runtime, "list_configurable_providers", lambda: ["openai"])
    monkeypatch.setattr(
        runtime,
        "_get_user_ai_provider_credential_for_server",
        lambda *_args, **_kwargs: pytest.fail("storage must not be called"),
    )

    with pytest.raises(runtime.UserProviderRuntimeConfigurationError) as exc_info:
        runtime.build_user_provider_client("synthetic-user-a", "groq")

    assert exc_info.value.category == "unsupported_provider"


@pytest.mark.parametrize("owner_user_id", ("", "  ", None))
def test_empty_owner_is_rejected_before_storage(monkeypatch, owner_user_id):
    monkeypatch.setattr(
        runtime,
        "_get_user_ai_provider_credential_for_server",
        lambda *_args, **_kwargs: pytest.fail("storage must not be called"),
    )

    with pytest.raises(runtime.UserProviderRuntimeConfigurationError) as exc_info:
        runtime.build_user_provider_client(owner_user_id, "groq")

    assert exc_info.value.category == "invalid_owner"
    assert "synthetic" not in str(exc_info.value)


def test_unknown_provider_is_rejected_before_storage_or_construction(monkeypatch):
    monkeypatch.setattr(
        runtime,
        "_get_user_ai_provider_credential_for_server",
        lambda *_args, **_kwargs: pytest.fail("storage must not be called"),
    )
    monkeypatch.setattr(
        runtime,
        "Groq",
        lambda **_kwargs: pytest.fail("constructor must not be called"),
    )

    with pytest.raises(runtime.UserProviderRuntimeConfigurationError) as exc_info:
        runtime.build_user_provider_client(
            "synthetic-user-a",
            "synthetic-unknown-secret-provider",
        )

    assert exc_info.value.category == "unsupported_provider"
    assert "synthetic-unknown-secret-provider" not in str(exc_info.value)


@pytest.mark.parametrize(
    ("stored_data", "expected"),
    (
        (
            {
                "found": True,
                "owner_user_id": "synthetic-user-a",
                "preferred_provider": " OpenAI ",
            },
            {
                "owner_user_id": "synthetic-user-a",
                "settings_found": True,
                "preferred_provider": "openai",
            },
        ),
        (
            {
                "found": True,
                "owner_user_id": "synthetic-user-a",
                "preferred_provider": None,
            },
            {
                "owner_user_id": "synthetic-user-a",
                "settings_found": True,
                "preferred_provider": None,
            },
        ),
        (
            {
                "found": False,
                "owner_user_id": "synthetic-user-a",
            },
            {
                "owner_user_id": "synthetic-user-a",
                "settings_found": False,
                "preferred_provider": None,
            },
        ),
    ),
)
def test_preferred_provider_preserves_all_three_storage_states(
    monkeypatch,
    stored_data,
    expected,
):
    monkeypatch.setattr(
        runtime,
        "get_user_ai_settings_payload",
        lambda owner_user_id, **_kwargs: {"data": stored_data},
    )

    assert runtime.resolve_user_preferred_provider("synthetic-user-a") == expected


def test_exact_owner_provider_and_storage_options_reach_server_lookup(monkeypatch):
    calls = _install_credential_lookup(
        monkeypatch,
        {("synthetic-user-a", "groq"): A_GROQ_SECRET},
    )
    _install_constructors(monkeypatch)

    runtime.build_user_provider_client(
        " synthetic-user-a ",
        " GROQ ",
        database_url="postgresql://synthetic-runtime-db",
        database_url_env="SYNTHETIC_DATABASE_URL",
        psql_bin="synthetic-psql",
        ensure_schema=False,
    )

    assert calls == [
        (
            "synthetic-user-a",
            "groq",
            {
                "database_url": "postgresql://synthetic-runtime-db",
                "database_url_env": "SYNTHETIC_DATABASE_URL",
                "psql_bin": "synthetic-psql",
                "ensure_schema": False,
            },
        )
    ]


def test_absent_credential_has_bounded_not_configured_result(monkeypatch):
    _install_credential_lookup(monkeypatch, {})

    with pytest.raises(runtime.UserProviderRuntimeConfigurationError) as exc_info:
        runtime.build_user_provider_client("synthetic-user-a", "groq")

    assert exc_info.value.category == "credential_not_configured"
    assert str(exc_info.value).endswith(
        "(category=credential_not_configured, provider=groq)"
    )


def test_groq_and_openai_constructors_receive_only_their_exact_credentials(
    monkeypatch,
):
    _install_credential_lookup(
        monkeypatch,
        {
            ("synthetic-user-a", "groq"): A_GROQ_SECRET,
            ("synthetic-user-a", "openai"): A_OPENAI_SECRET,
        },
    )
    constructions = _install_constructors(monkeypatch)

    groq_client = runtime.build_user_provider_client("synthetic-user-a", "groq")
    openai_client = runtime.build_user_provider_client(
        "synthetic-user-a", "openai"
    )

    assert constructions == [
        ("groq", A_GROQ_SECRET, groq_client),
        ("openai", A_OPENAI_SECRET, openai_client),
    ]
    assert A_GROQ_SECRET != openai_client.api_key
    assert A_OPENAI_SECRET != groq_client.api_key


def test_every_factory_invocation_is_fresh_and_cross_user_isolated(monkeypatch):
    lookup_calls = _install_credential_lookup(
        monkeypatch,
        {
            ("synthetic-user-a", "groq"): A_GROQ_SECRET,
            ("synthetic-user-b", "groq"): B_GROQ_SECRET,
        },
    )
    constructions = _install_constructors(monkeypatch)

    client_a_first = runtime.build_user_provider_client(
        "synthetic-user-a", "groq"
    )
    client_a_second = runtime.build_user_provider_client(
        "synthetic-user-a", "groq"
    )
    client_b = runtime.build_user_provider_client("synthetic-user-b", "groq")

    assert client_a_first is not client_a_second
    assert client_a_first is not client_b
    assert client_a_second is not client_b
    assert [entry[:2] for entry in constructions] == [
        ("groq", A_GROQ_SECRET),
        ("groq", A_GROQ_SECRET),
        ("groq", B_GROQ_SECRET),
    ]
    assert [(owner, provider) for owner, provider, _kwargs in lookup_calls] == [
        ("synthetic-user-a", "groq"),
        ("synthetic-user-a", "groq"),
        ("synthetic-user-b", "groq"),
    ]


def test_factory_does_not_mutate_provider_environment_or_make_requests(
    monkeypatch,
):
    monkeypatch.setenv("GROQ_API_KEY", "sentinel-global-groq")
    monkeypatch.setenv("OPENAI_API_KEY", "sentinel-global-openai")
    _install_credential_lookup(
        monkeypatch,
        {("synthetic-user-a", "groq"): A_GROQ_SECRET},
    )
    _install_constructors(monkeypatch)
    before = {
        "GROQ_API_KEY": os.environ["GROQ_API_KEY"],
        "OPENAI_API_KEY": os.environ["OPENAI_API_KEY"],
    }

    client = runtime.build_user_provider_client("synthetic-user-a", "groq")

    assert client.request_calls == 0
    assert {
        "GROQ_API_KEY": os.environ["GROQ_API_KEY"],
        "OPENAI_API_KEY": os.environ["OPENAI_API_KEY"],
    } == before


def test_factory_never_touches_shared_llm_client_globals(monkeypatch):
    _install_credential_lookup(
        monkeypatch,
        {("synthetic-user-a", "groq"): A_GROQ_SECRET},
    )
    _install_constructors(monkeypatch)
    with _isolated_shared_client() as (shared_client, _observations):
        groq_sentinel = object()
        openai_sentinel = object()
        shared_client._groq_client = groq_sentinel
        shared_client._openai_client = openai_sentinel

        runtime.build_user_provider_client("synthetic-user-a", "groq")

        assert shared_client._groq_client is groq_sentinel
        assert shared_client._openai_client is openai_sentinel


def test_safe_metadata_is_an_exact_non_secret_whitelist(monkeypatch):
    monkeypatch.setattr(
        runtime,
        "get_user_ai_settings_payload",
        lambda owner_user_id, **_kwargs: {
            "data": {
                "found": True,
                "owner_user_id": owner_user_id,
                "preferred_provider": "groq",
                "credential": A_GROQ_SECRET,
            }
        },
    )
    monkeypatch.setattr(
        runtime,
        "get_user_ai_provider_credential_metadata_payload",
        lambda owner_user_id, provider, **_kwargs: {
            "data": {
                "owner_user_id": owner_user_id,
                "provider": provider,
                "configured": True,
                "credential_hint": "••••••••CRET",
                "credential": A_GROQ_SECRET,
                "credential_ciphertext": "synthetic-ciphertext",
                "client": "synthetic-client",
                "api_key": A_GROQ_SECRET,
            }
        },
    )

    metadata = runtime.get_safe_user_provider_runtime_metadata(
        "synthetic-user-a", "groq"
    )

    assert metadata == {
        "owner_user_id": "synthetic-user-a",
        "provider": "groq",
        "settings_found": True,
        "preferred_provider": "groq",
        "configured": True,
        "credential_hint": "••••••••CRET",
    }
    rendered = json.dumps(metadata, ensure_ascii=False)
    assert A_GROQ_SECRET not in rendered
    assert "synthetic-ciphertext" not in rendered
    assert "synthetic-client" not in rendered


@pytest.mark.parametrize(
    "failure",
    (
        RuntimeError(f"database failure {A_GROQ_SECRET}"),
        ValueError(f"decryption failure {A_GROQ_SECRET}"),
    ),
)
def test_storage_and_decryption_fail_closed_with_bounded_error(
    monkeypatch,
    failure,
):
    def fail(*_args, **_kwargs):
        raise failure

    monkeypatch.setattr(
        runtime,
        "_get_user_ai_provider_credential_for_server",
        fail,
    )
    monkeypatch.setenv("GROQ_API_KEY", "sentinel-global-groq")

    with pytest.raises(runtime.UserProviderRuntimeConfigurationError) as exc_info:
        runtime.build_user_provider_client("synthetic-user-a", "groq")

    assert exc_info.value.category == "credential_unavailable"
    assert A_GROQ_SECRET not in str(exc_info.value)
    assert exc_info.value.__cause__ is None
    assert os.environ["GROQ_API_KEY"] == "sentinel-global-groq"


def test_constructor_failure_is_bounded_and_does_not_expose_credential(monkeypatch):
    _install_credential_lookup(
        monkeypatch,
        {("synthetic-user-a", "groq"): A_GROQ_SECRET},
    )

    def fail_constructor(*, api_key):
        raise RuntimeError(f"constructor rejected {api_key}")

    monkeypatch.setattr(runtime, "Groq", fail_constructor)

    with pytest.raises(runtime.UserProviderRuntimeConfigurationError) as exc_info:
        runtime.build_user_provider_client("synthetic-user-a", "groq")

    assert exc_info.value.category == "client_construction_failed"
    assert A_GROQ_SECRET not in str(exc_info.value)
    assert exc_info.value.__cause__ is None


def test_owner_mismatch_and_provider_mismatch_fail_closed(monkeypatch):
    monkeypatch.setattr(
        runtime,
        "get_user_ai_settings_payload",
        lambda *_args, **_kwargs: {
            "data": {"found": True, "owner_user_id": "synthetic-user-b"}
        },
    )
    with pytest.raises(runtime.UserProviderRuntimeConfigurationError) as exc_info:
        runtime.resolve_user_preferred_provider("synthetic-user-a")
    assert exc_info.value.category == "settings_unavailable"

    monkeypatch.setattr(
        runtime,
        "get_user_ai_settings_payload",
        lambda owner_user_id, **_kwargs: {
            "data": {"found": False, "owner_user_id": owner_user_id}
        },
    )
    monkeypatch.setattr(
        runtime,
        "get_user_ai_provider_credential_metadata_payload",
        lambda owner_user_id, provider, **_kwargs: {
            "data": {
                "owner_user_id": owner_user_id,
                "provider": "openai",
                "configured": True,
            }
        },
    )
    with pytest.raises(runtime.UserProviderRuntimeConfigurationError) as exc_info:
        runtime.get_safe_user_provider_runtime_metadata(
            "synthetic-user-a", "groq"
        )
    assert exc_info.value.category == "credential_unavailable"


def test_module_import_has_no_runtime_effects(monkeypatch):
    observations = {"storage": 0, "constructors": 0}

    def prohibited_storage(*_args, **_kwargs):
        observations["storage"] += 1
        raise AssertionError("storage access at import is prohibited")

    def prohibited_constructor(*_args, **_kwargs):
        observations["constructors"] += 1
        raise AssertionError("client construction at import is prohibited")

    store_module = importlib.import_module("src.storage.user_ai_settings.store")
    monkeypatch.setattr(
        store_module,
        "_get_user_ai_provider_credential_for_server",
        prohibited_storage,
    )
    monkeypatch.setattr(
        store_module,
        "get_user_ai_provider_credential_metadata_payload",
        prohibited_storage,
    )
    monkeypatch.setattr(
        store_module,
        "get_user_ai_settings_payload",
        prohibited_storage,
    )
    monkeypatch.setattr(groq, "Groq", prohibited_constructor)
    monkeypatch.setattr(openai, "OpenAI", prohibited_constructor)
    module_name = "src.ai.user_provider_runtime"
    previous = sys.modules.pop(module_name)
    try:
        imported = importlib.import_module(module_name)
        assert imported is not None
        assert observations == {"storage": 0, "constructors": 0}
    finally:
        sys.modules[module_name] = previous


def test_runtime_source_has_no_shared_client_storage_or_execution_ownership():
    source = RUNTIME_PATH.read_text(encoding="utf-8")
    assert "src.ai.llm_client" not in source
    assert "get_groq_client" not in source
    assert "get_openai_client" not in source
    assert "os.environ" not in source
    assert "os.putenv" not in source
    assert "load_dotenv" not in source
    assert "credential_ciphertext" not in source
    assert "Fernet" not in source
    assert "chat.completions.create" not in source
    assert "responses.create" not in source
    assert "models.list" not in source
    assert "print(" not in source
    assert "logging." not in source
    assert "logger." not in source
