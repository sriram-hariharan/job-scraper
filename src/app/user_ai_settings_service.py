"""Owner-scoped service boundary for authenticated user AI settings APIs."""

from __future__ import annotations

from typing import Any, Dict

from src.ai.provider_model_catalog import (
    is_configuration_eligible,
    list_configurable_models,
    list_configurable_providers,
)
from src.ai.user_provider_runtime import (
    UserProviderRuntimeConfigurationError,
    run_user_chat_completion_with_metadata,
)
from src.storage.user_ai_settings.store import (
    clear_user_ai_preferred_provider_payload as clear_preferred_provider_store_payload,
    delete_user_ai_provider_credential_payload as delete_provider_credential_store_payload,
    get_user_ai_settings_payload as get_user_ai_settings_store_payload,
    set_user_ai_preferred_provider_payload as set_preferred_provider_store_payload,
    upsert_user_ai_provider_credential_payload as upsert_provider_credential_store_payload,
)


CONNECTION_TEST_MESSAGES = (
    {"role": "user", "content": "Reply with OK."},
)
CONNECTION_TEST_MAX_TOKENS = 128


class UserAiSettingsServiceError(RuntimeError):
    """Bounded service failure safe for translation at the HTTP boundary."""

    def __init__(self, category: str) -> None:
        self.category = category
        super().__init__(
            "User AI settings operation failed "
            f"(category={category})"
        )


def _require_owner_user_id(owner_user_id: Any) -> str:
    owner = str(owner_user_id or "").strip()
    if not owner:
        raise UserAiSettingsServiceError("invalid_owner")
    return owner


def _normalize_configurable_provider(provider: Any) -> str:
    provider_name = str(provider or "").strip().lower()
    if provider_name not in list_configurable_providers():
        raise UserAiSettingsServiceError("unsupported_provider")
    return provider_name


def _storage_kwargs() -> Dict[str, Any]:
    return {
        "database_url": "",
        "database_url_env": "DATABASE_URL",
        "psql_bin": "psql",
        "print_only": False,
        "ensure_schema": True,
    }


def _safe_settings_data(owner: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    data = dict(payload.get("data", {}) or {})
    if str(data.get("owner_user_id") or "").strip() != owner:
        raise UserAiSettingsServiceError("settings_unavailable")

    stored_providers = dict(data.get("providers", {}) or {})
    providers = {}
    for provider in list_configurable_providers():
        metadata = dict(stored_providers.get(provider, {}) or {})
        providers[provider] = {
            "configured": bool(metadata.get("configured", False)),
            "credential_hint": str(metadata.get("credential_hint") or ""),
        }
    preferred_provider = data.get("preferred_provider")
    if preferred_provider is not None:
        try:
            preferred_provider = _normalize_configurable_provider(preferred_provider)
        except UserAiSettingsServiceError:
            raise UserAiSettingsServiceError("settings_unavailable") from None
    return {
        "ok": True,
        "owner_user_id": owner,
        "preferred_provider": preferred_provider,
        "providers": providers,
    }


def user_ai_settings_payload(*, owner_user_id: str) -> Dict[str, Any]:
    owner = _require_owner_user_id(owner_user_id)
    try:
        payload = get_user_ai_settings_store_payload(owner, **_storage_kwargs())
        return _safe_settings_data(owner, payload)
    except UserAiSettingsServiceError:
        raise
    except Exception:
        raise UserAiSettingsServiceError("settings_unavailable") from None


def user_ai_provider_catalog_payload(*, owner_user_id: str) -> Dict[str, Any]:
    _require_owner_user_id(owner_user_id)
    return {
        "ok": True,
        "providers": [
            {
                "provider": provider,
                "models": list_configurable_models(provider),
            }
            for provider in list_configurable_providers()
        ],
    }


def save_user_ai_preferred_provider_payload(
    *,
    owner_user_id: str,
    provider: str,
) -> Dict[str, Any]:
    owner = _require_owner_user_id(owner_user_id)
    provider_name = _normalize_configurable_provider(provider)
    try:
        set_preferred_provider_store_payload(
            owner,
            provider_name,
            **_storage_kwargs(),
        )
    except Exception:
        raise UserAiSettingsServiceError("settings_write_failed") from None
    return {
        "ok": True,
        "owner_user_id": owner,
        "preferred_provider": provider_name,
    }


def clear_user_ai_preferred_provider_service_payload(
    *,
    owner_user_id: str,
) -> Dict[str, Any]:
    owner = _require_owner_user_id(owner_user_id)
    try:
        clear_preferred_provider_store_payload(owner, **_storage_kwargs())
    except Exception:
        raise UserAiSettingsServiceError("settings_write_failed") from None
    return {
        "ok": True,
        "owner_user_id": owner,
        "preferred_provider": None,
    }


def save_user_ai_provider_credential_payload(
    *,
    owner_user_id: str,
    provider: str,
    credential: str,
) -> Dict[str, Any]:
    owner = _require_owner_user_id(owner_user_id)
    provider_name = _normalize_configurable_provider(provider)
    if not isinstance(credential, str) or not credential.strip():
        raise UserAiSettingsServiceError("invalid_credential")
    try:
        payload = upsert_provider_credential_store_payload(
            owner,
            provider_name,
            credential,
            **_storage_kwargs(),
        )
        data = dict(payload.get("data", {}) or {})
    except Exception:
        raise UserAiSettingsServiceError("credential_write_failed") from None
    if (
        str(data.get("owner_user_id") or "").strip() != owner
        or str(data.get("provider") or "").strip().lower() != provider_name
    ):
        raise UserAiSettingsServiceError("credential_write_failed")
    return {
        "ok": True,
        "provider": provider_name,
        "configured": bool(data.get("configured", True)),
        "credential_hint": str(data.get("credential_hint") or ""),
        "encryption_scheme": str(data.get("encryption_scheme") or ""),
        "created_at": data.get("created_at"),
        "updated_at": data.get("updated_at"),
    }


def delete_user_ai_provider_credential_service_payload(
    *,
    owner_user_id: str,
    provider: str,
) -> Dict[str, Any]:
    owner = _require_owner_user_id(owner_user_id)
    provider_name = _normalize_configurable_provider(provider)
    try:
        payload = delete_provider_credential_store_payload(
            owner,
            provider_name,
            **_storage_kwargs(),
        )
        data = dict(payload.get("data", {}) or {})
    except Exception:
        raise UserAiSettingsServiceError("credential_delete_failed") from None
    return {
        "ok": True,
        "provider": provider_name,
        "deleted": bool(data.get("deleted", False)),
        "configured": False,
        "credential_hint": "",
    }


def test_user_ai_provider_connection_payload(
    *,
    owner_user_id: str,
    provider: str,
    model: str,
) -> Dict[str, Any]:
    owner = _require_owner_user_id(owner_user_id)
    provider_name = _normalize_configurable_provider(provider)
    model_name = str(model or "").strip()
    if not is_configuration_eligible(provider_name, model_name):
        raise UserAiSettingsServiceError("unsupported_provider_model")

    try:
        result = run_user_chat_completion_with_metadata(
            owner,
            provider_name,
            model_name,
            [dict(message) for message in CONNECTION_TEST_MESSAGES],
            temperature=0,
            max_tokens=CONNECTION_TEST_MAX_TOKENS,
            response_mime_type=None,
            response_schema=None,
            return_parsed=False,
            thinking_budget=0,
        )
        content = result.get("content")
        if not str(content or "").strip():
            raise UserAiSettingsServiceError("connection_test_failed")
    except UserProviderRuntimeConfigurationError as exc:
        category = (
            exc.category
            if exc.category in {
                "credential_not_configured",
                "unsupported_provider_model",
            }
            else "connection_test_failed"
        )
        raise UserAiSettingsServiceError(category) from None
    except UserAiSettingsServiceError:
        raise
    except Exception:
        raise UserAiSettingsServiceError("connection_test_failed") from None

    return {
        "ok": True,
        "provider": provider_name,
        "model": model_name,
        "status": "connected",
    }
