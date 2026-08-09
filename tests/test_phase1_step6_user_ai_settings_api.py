from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient
from pydantic import SecretStr
import pytest

from src.app import api
from src.app import user_ai_settings_service as service
from src.auth import runtime as auth_runtime


ROOT = Path(__file__).resolve().parents[1]
API_PATH = ROOT / "src/app/api.py"
SERVICE_PATH = ROOT / "src/app/user_ai_settings_service.py"
SYNTHETIC_SECRET = "synthetic-step6-never-return-secret"
AUTHENTICATED_OWNER = "synthetic-authenticated-user"


def _authenticated_client(monkeypatch) -> TestClient:
    def guard(request):
        request.state.auth_user = {"user_id": AUTHENTICATED_OWNER}
        return None

    monkeypatch.setattr(api, "auth_guard_response", guard)
    return TestClient(api.app)


def _unauthenticated_client(monkeypatch) -> TestClient:
    monkeypatch.setattr(api, "auth_guard_response", lambda _request: None)
    return TestClient(api.app)


@pytest.mark.parametrize(
    ("method", "path", "body"),
    (
        ("get", "/ai/settings", None),
        ("get", "/ai/settings/catalog", None),
        ("post", "/ai/settings/preferred-provider", {"provider": "groq"}),
        ("delete", "/ai/settings/preferred-provider", None),
        ("put", "/ai/settings/credentials/groq", {"api_key": "synthetic"}),
        ("delete", "/ai/settings/credentials/groq", None),
        (
            "post",
            "/ai/settings/test-connection",
            {"provider": "groq", "model": "openai/gpt-oss-20b"},
        ),
    ),
)
def test_every_ai_settings_route_requires_authenticated_request_owner(
    monkeypatch,
    method,
    path,
    body,
):
    client = _unauthenticated_client(monkeypatch)
    response = getattr(client, method)(path, json=body) if body else getattr(
        client, method
    )(path)

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required."}


def test_ai_routes_are_not_public_and_owner_can_only_come_from_request_state():
    for path in (
        "/ai/settings",
        "/ai/settings/catalog",
        "/ai/settings/preferred-provider",
        "/ai/settings/credentials/groq",
        "/ai/settings/test-connection",
    ):
        assert auth_runtime._is_public_auth_path(path) is False

    source = API_PATH.read_text(encoding="utf-8")
    routes = source.split('@app.get("/ai/settings")', 1)[1].split(
        '@app.get("/onboarding/preferences")', 1
    )[0]
    assert routes.count("_require_auth_owner_user_id(http_request)") == 7
    assert "owner_user_id=request." not in routes
    assert "owner_user_id=provider" not in routes
    assert "owner_user_id: str" not in routes
    for model in (
        api.UserAiPreferredProviderRequest,
        api.UserAiCredentialRequest,
        api.UserAiTestConnectionRequest,
    ):
        assert "owner_user_id" not in model.model_fields


def test_request_models_forbid_extra_fields_and_credential_uses_secretstr(
    monkeypatch,
):
    assert api.UserAiCredentialRequest.model_fields["api_key"].annotation is SecretStr
    client = _authenticated_client(monkeypatch)

    responses = (
        client.post(
            "/ai/settings/preferred-provider",
            json={"provider": "groq", "owner_user_id": "synthetic-attacker"},
        ),
        client.put(
            "/ai/settings/credentials/groq",
            json={"api_key": SYNTHETIC_SECRET, "extra": "forbidden"},
        ),
        client.post(
            "/ai/settings/test-connection",
            json={
                "provider": "groq",
                "model": "openai/gpt-oss-20b",
                "api_key": SYNTHETIC_SECRET,
            },
        ),
    )

    assert [response.status_code for response in responses] == [422, 422, 422]
    assert all(SYNTHETIC_SECRET not in response.text for response in responses)


def test_settings_service_returns_exact_safe_step3_metadata(monkeypatch):
    monkeypatch.setattr(
        service,
        "get_user_ai_settings_store_payload",
        lambda owner_user_id, **_kwargs: {
            "data": {
                "found": True,
                "owner_user_id": owner_user_id,
                "preferred_provider": "groq",
                "providers": {
                    "groq": {
                        "configured": True,
                        "credential_hint": "••••••••CRET",
                        "credential": SYNTHETIC_SECRET,
                        "credential_ciphertext": "synthetic-ciphertext",
                    },
                    "openai": {
                        "configured": False,
                        "credential_hint": "",
                    },
                },
                "credential": SYNTHETIC_SECRET,
            }
        },
    )

    payload = service.user_ai_settings_payload(
        owner_user_id=AUTHENTICATED_OWNER
    )

    assert payload == {
        "ok": True,
        "owner_user_id": AUTHENTICATED_OWNER,
        "preferred_provider": "groq",
        "providers": {
            "groq": {
                "configured": True,
                "credential_hint": "••••••••CRET",
            },
            "openai": {"configured": False, "credential_hint": ""},
        },
    }
    rendered = json.dumps(payload, ensure_ascii=False)
    assert SYNTHETIC_SECRET not in rendered
    assert "synthetic-ciphertext" not in rendered
    assert "credential_ciphertext" not in rendered


def test_get_settings_api_uses_authenticated_owner_and_safe_response(
    monkeypatch,
):
    captured = []

    def get_settings(owner_user_id, **_kwargs):
        captured.append(owner_user_id)
        return {
            "data": {
                "owner_user_id": owner_user_id,
                "preferred_provider": None,
                "providers": {
                    "groq": {"configured": False, "credential_hint": ""},
                    "openai": {"configured": False, "credential_hint": ""},
                },
            }
        }

    monkeypatch.setattr(service, "get_user_ai_settings_store_payload", get_settings)
    monkeypatch.setattr(
        service,
        "run_user_chat_completion_with_metadata",
        lambda *_args, **_kwargs: pytest.fail("GET must not call a provider"),
    )
    response = _authenticated_client(monkeypatch).get("/ai/settings")

    assert response.status_code == 200
    assert captured == [AUTHENTICATED_OWNER]
    assert response.json()["owner_user_id"] == AUTHENTICATED_OWNER


def test_catalog_is_exact_ordered_candidate_metadata_and_read_only(monkeypatch):
    monkeypatch.setattr(
        service,
        "run_user_chat_completion_with_metadata",
        lambda *_args, **_kwargs: pytest.fail("catalog must not call a provider"),
    )
    payload = service.user_ai_provider_catalog_payload(
        owner_user_id=AUTHENTICATED_OWNER
    )

    assert [item["provider"] for item in payload["providers"]] == [
        "groq",
        "openai",
    ]
    pairs = [
        (provider["provider"], model["model_id"])
        for provider in payload["providers"]
        for model in provider["models"]
    ]
    assert pairs == [
        ("groq", "openai/gpt-oss-20b"),
        ("groq", "openai/gpt-oss-120b"),
        ("openai", "gpt-5-mini"),
        ("openai", "gpt-5.1"),
    ]
    assert all("llama" not in model.lower() for _provider, model in pairs)
    assert all(
        model["live_qualification_status"] == "live_qualification_required"
        for provider in payload["providers"]
        for model in provider["models"]
    )


def test_catalog_api_is_authenticated_and_deterministic(monkeypatch):
    first = _authenticated_client(monkeypatch).get("/ai/settings/catalog")
    second = _authenticated_client(monkeypatch).get("/ai/settings/catalog")

    assert first.status_code == 200
    assert first.json() == second.json()
    assert [row["provider"] for row in first.json()["providers"]] == [
        "groq",
        "openai",
    ]


def test_preferred_provider_save_and_clear_are_owner_scoped_without_provider_call(
    monkeypatch,
):
    calls = []
    monkeypatch.setattr(
        service,
        "set_preferred_provider_store_payload",
        lambda owner, provider, **kwargs: calls.append(("set", owner, provider, kwargs))
        or {"data": {}},
    )
    monkeypatch.setattr(
        service,
        "clear_preferred_provider_store_payload",
        lambda owner, **kwargs: calls.append(("clear", owner, kwargs))
        or {"data": {}},
    )
    monkeypatch.setattr(
        service,
        "run_user_chat_completion_with_metadata",
        lambda *_args, **_kwargs: pytest.fail("preference writes must not call provider"),
    )

    saved = service.save_user_ai_preferred_provider_payload(
        owner_user_id=AUTHENTICATED_OWNER,
        provider=" OpenAI ",
    )
    cleared = service.clear_user_ai_preferred_provider_service_payload(
        owner_user_id=AUTHENTICATED_OWNER,
    )

    assert saved["preferred_provider"] == "openai"
    assert cleared["preferred_provider"] is None
    assert calls[0][0:3] == ("set", AUTHENTICATED_OWNER, "openai")
    assert calls[1][0:2] == ("clear", AUTHENTICATED_OWNER)


def test_unknown_preferred_provider_fails_before_storage(monkeypatch):
    monkeypatch.setattr(
        service,
        "set_preferred_provider_store_payload",
        lambda *_args, **_kwargs: pytest.fail("storage must not run"),
    )
    with pytest.raises(service.UserAiSettingsServiceError) as exc_info:
        service.save_user_ai_preferred_provider_payload(
            owner_user_id=AUTHENTICATED_OWNER,
            provider="unknown",
        )
    assert exc_info.value.category == "unsupported_provider"


def test_credential_save_replace_uses_exact_encrypted_upsert_boundary_only(
    monkeypatch,
):
    calls = []

    def upsert(owner, provider, credential, **kwargs):
        calls.append((owner, provider, credential, kwargs))
        return {
            "data": {
                "owner_user_id": owner,
                "provider": provider,
                "configured": True,
                "credential_hint": "••••••••CRET",
                "encryption_scheme": "fernet-v1",
                "created_at": "2026-08-09T00:00:00Z",
                "updated_at": "2026-08-09T00:00:00Z",
                "credential": SYNTHETIC_SECRET,
                "credential_ciphertext": "synthetic-ciphertext",
            }
        }

    monkeypatch.setattr(service, "upsert_provider_credential_store_payload", upsert)
    monkeypatch.setattr(
        service,
        "run_user_chat_completion_with_metadata",
        lambda *_args, **_kwargs: pytest.fail("save must not test provider"),
    )

    first = service.save_user_ai_provider_credential_payload(
        owner_user_id=AUTHENTICATED_OWNER,
        provider="groq",
        credential=SYNTHETIC_SECRET,
    )
    second = service.save_user_ai_provider_credential_payload(
        owner_user_id=AUTHENTICATED_OWNER,
        provider="groq",
        credential="synthetic-replacement-secret",
    )

    assert len(calls) == 2
    assert calls[0][0:3] == (
        AUTHENTICATED_OWNER,
        "groq",
        SYNTHETIC_SECRET,
    )
    assert first == second
    rendered = json.dumps(first)
    assert SYNTHETIC_SECRET not in rendered
    assert "synthetic-ciphertext" not in rendered


def test_credential_api_extracts_secretstr_for_exact_authenticated_owner(
    monkeypatch,
):
    captured = []

    def save(**kwargs):
        captured.append(kwargs)
        return {
            "ok": True,
            "provider": kwargs["provider"],
            "configured": True,
            "credential_hint": "••••••••CRET",
        }

    monkeypatch.setattr(service, "save_user_ai_provider_credential_payload", save)
    response = _authenticated_client(monkeypatch).put(
        "/ai/settings/credentials/openai",
        json={"api_key": SYNTHETIC_SECRET},
    )

    assert response.status_code == 200
    assert captured == [
        {
            "owner_user_id": AUTHENTICATED_OWNER,
            "provider": "openai",
            "credential": SYNTHETIC_SECRET,
        }
    ]
    assert SYNTHETIC_SECRET not in response.text


def test_credential_delete_is_exact_and_does_not_clear_or_cross_delete(
    monkeypatch,
):
    calls = []
    monkeypatch.setattr(
        service,
        "delete_provider_credential_store_payload",
        lambda owner, provider, **kwargs: calls.append((owner, provider, kwargs))
        or {
            "data": {
                "owner_user_id": owner,
                "provider": provider,
                "deleted": True,
            }
        },
    )
    monkeypatch.setattr(
        service,
        "clear_preferred_provider_store_payload",
        lambda *_args, **_kwargs: pytest.fail("delete must not clear preference"),
    )

    payload = service.delete_user_ai_provider_credential_service_payload(
        owner_user_id=AUTHENTICATED_OWNER,
        provider="groq",
    )

    assert [(owner, provider) for owner, provider, _kwargs in calls] == [
        (AUTHENTICATED_OWNER, "groq")
    ]
    assert payload == {
        "ok": True,
        "provider": "groq",
        "deleted": True,
        "configured": False,
        "credential_hint": "",
    }


@pytest.mark.parametrize(
    ("provider", "model"),
    (
        ("groq", "arbitrary-model"),
        ("groq", "llama-3.1-8b-instant"),
        ("groq", "gpt-5-mini"),
        ("openai", "openai/gpt-oss-20b"),
    ),
)
def test_connection_rejects_non_catalog_pair_before_execution(
    monkeypatch,
    provider,
    model,
):
    monkeypatch.setattr(
        service,
        "run_user_chat_completion_with_metadata",
        lambda *_args, **_kwargs: pytest.fail("provider execution must not run"),
    )
    with pytest.raises(service.UserAiSettingsServiceError) as exc_info:
        service.test_user_ai_provider_connection_payload(
            owner_user_id=AUTHENTICATED_OWNER,
            provider=provider,
            model=model,
        )
    assert exc_info.value.category == "unsupported_provider_model"


def test_connection_uses_stored_user_runtime_fixed_prompt_and_bounded_request(
    monkeypatch,
):
    calls = []

    def run(*args, **kwargs):
        calls.append((args, kwargs))
        return {
            "content": "provider-generated-body-must-not-return",
            "provider": args[1],
            "model": args[2],
            "fallback_used": False,
        }

    monkeypatch.setattr(service, "run_user_chat_completion_with_metadata", run)

    payload = service.test_user_ai_provider_connection_payload(
        owner_user_id=AUTHENTICATED_OWNER,
        provider="openai",
        model="gpt-5-mini",
    )

    args, kwargs = calls[0]
    assert args[0:3] == (AUTHENTICATED_OWNER, "openai", "gpt-5-mini")
    assert args[3] == [{"role": "user", "content": "Reply with OK."}]
    assert kwargs["max_tokens"] <= 32
    assert kwargs["response_mime_type"] is None
    assert kwargs["return_parsed"] is False
    assert "fallback_enabled" not in kwargs
    assert "credential" not in kwargs
    assert "api_key" not in kwargs
    assert payload == {
        "ok": True,
        "provider": "openai",
        "model": "gpt-5-mini",
        "status": "connected",
    }
    rendered = json.dumps(payload)
    assert "provider-generated-body-must-not-return" not in rendered
    assert "content" not in payload


def test_connection_failure_is_bounded_in_service_and_http_response(monkeypatch):
    def fail(*_args, **_kwargs):
        raise RuntimeError(f"raw SDK response credential={SYNTHETIC_SECRET}")

    monkeypatch.setattr(service, "run_user_chat_completion_with_metadata", fail)

    with pytest.raises(service.UserAiSettingsServiceError) as exc_info:
        service.test_user_ai_provider_connection_payload(
            owner_user_id=AUTHENTICATED_OWNER,
            provider="groq",
            model="openai/gpt-oss-20b",
        )
    assert exc_info.value.category == "connection_test_failed"
    assert SYNTHETIC_SECRET not in str(exc_info.value)

    response = _authenticated_client(monkeypatch).post(
        "/ai/settings/test-connection",
        json={"provider": "groq", "model": "openai/gpt-oss-20b"},
    )
    assert response.status_code == 502
    assert response.json() == {
        "detail": {"ok": False, "error_category": "connection_test_failed"}
    }
    assert SYNTHETIC_SECRET not in response.text


def test_step6_sources_have_no_secret_environment_or_direct_sdk_ownership():
    api_source = API_PATH.read_text(encoding="utf-8")
    service_source = SERVICE_PATH.read_text(encoding="utf-8")
    combined = api_source + service_source
    assert "GROQ_API_KEY" not in service_source
    assert "OPENAI_API_KEY" not in service_source
    assert "os.environ" not in service_source
    assert "os.putenv" not in combined
    assert "Groq(" not in combined
    assert "OpenAI(" not in combined
    assert "chat.completions.create" not in combined
    assert "responses.create" not in combined
    assert "print(request)" not in combined
    assert "model_dump()" not in combined
    assert "get_secret_value()" in api_source
