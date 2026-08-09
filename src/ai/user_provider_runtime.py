"""Dormant user-scoped provider credential and client boundary.

This module does not execute provider requests or participate in production
LLM routing. Callers must supply an already-authenticated owner identifier.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from groq import Groq
from openai import OpenAI

from src.ai.provider_model_catalog import list_configurable_providers
from src.storage.user_ai_settings.store import (
    _get_user_ai_provider_credential_for_server,
    get_user_ai_provider_credential_metadata_payload,
    get_user_ai_settings_payload,
)


class UserProviderRuntimeConfigurationError(RuntimeError):
    """Bounded failure while resolving a user-scoped provider runtime."""

    def __init__(self, category: str, provider: Optional[str] = None) -> None:
        self.category = category
        self.provider = provider
        provider_detail = f", provider={provider}" if provider else ""
        super().__init__(
            "User provider runtime configuration failed "
            f"(category={category}{provider_detail})"
        )


def _require_owner_user_id(owner_user_id: Any) -> str:
    owner = str(owner_user_id or "").strip()
    if not owner:
        raise UserProviderRuntimeConfigurationError("invalid_owner")
    return owner


def _normalize_configurable_provider(provider: Any) -> str:
    provider_name = str(provider or "").strip().lower()
    if provider_name not in list_configurable_providers():
        raise UserProviderRuntimeConfigurationError("unsupported_provider")
    return provider_name


def _storage_kwargs(
    *,
    database_url: str,
    database_url_env: str,
    psql_bin: str,
    ensure_schema: bool,
) -> Dict[str, Any]:
    return {
        "database_url": database_url,
        "database_url_env": database_url_env,
        "psql_bin": psql_bin,
        "ensure_schema": ensure_schema,
    }


def resolve_user_preferred_provider(
    owner_user_id: str,
    *,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    """Return the three-state preferred-provider result without fallback."""

    owner = _require_owner_user_id(owner_user_id)
    try:
        payload = get_user_ai_settings_payload(
            owner,
            **_storage_kwargs(
                database_url=database_url,
                database_url_env=database_url_env,
                psql_bin=psql_bin,
                ensure_schema=ensure_schema,
            ),
        )
        data = dict(payload.get("data", {}) or {})
    except UserProviderRuntimeConfigurationError:
        raise
    except Exception:
        raise UserProviderRuntimeConfigurationError("settings_unavailable") from None

    if str(data.get("owner_user_id") or "").strip() != owner:
        raise UserProviderRuntimeConfigurationError("settings_unavailable")

    settings_found = bool(data.get("found", False))
    preferred_provider = data.get("preferred_provider") if settings_found else None
    if preferred_provider is not None:
        preferred_provider = _normalize_configurable_provider(preferred_provider)

    return {
        "owner_user_id": owner,
        "settings_found": settings_found,
        "preferred_provider": preferred_provider,
    }


def get_safe_user_provider_runtime_metadata(
    owner_user_id: str,
    provider: str,
    *,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    """Return whitelisted provider metadata with no credential or client."""

    owner = _require_owner_user_id(owner_user_id)
    provider_name = _normalize_configurable_provider(provider)
    kwargs = _storage_kwargs(
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        ensure_schema=ensure_schema,
    )
    preferred = resolve_user_preferred_provider(owner, **kwargs)
    try:
        payload = get_user_ai_provider_credential_metadata_payload(
            owner,
            provider_name,
            **kwargs,
        )
        data = dict(payload.get("data", {}) or {})
    except Exception:
        raise UserProviderRuntimeConfigurationError(
            "credential_unavailable", provider_name
        ) from None

    if (
        str(data.get("owner_user_id") or "").strip() != owner
        or str(data.get("provider") or "").strip().lower() != provider_name
    ):
        raise UserProviderRuntimeConfigurationError(
            "credential_unavailable", provider_name
        )

    return {
        "owner_user_id": owner,
        "provider": provider_name,
        "settings_found": preferred["settings_found"],
        "preferred_provider": preferred["preferred_provider"],
        "configured": bool(data.get("configured", False)),
        "credential_hint": str(data.get("credential_hint") or ""),
    }


def _resolve_user_provider_credential(
    owner_user_id: str,
    provider: str,
    *,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    ensure_schema: bool = True,
) -> str:
    owner = _require_owner_user_id(owner_user_id)
    provider_name = _normalize_configurable_provider(provider)
    try:
        credential = _get_user_ai_provider_credential_for_server(
            owner,
            provider_name,
            **_storage_kwargs(
                database_url=database_url,
                database_url_env=database_url_env,
                psql_bin=psql_bin,
                ensure_schema=ensure_schema,
            ),
        )
    except Exception:
        raise UserProviderRuntimeConfigurationError(
            "credential_unavailable", provider_name
        ) from None

    if not isinstance(credential, str) or not credential.strip():
        raise UserProviderRuntimeConfigurationError(
            "credential_not_configured", provider_name
        )
    return credential


def build_user_provider_client(
    owner_user_id: str,
    provider: str,
    *,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    ensure_schema: bool = True,
) -> Any:
    """Construct one fresh SDK client for one exact owner/provider credential."""

    owner = _require_owner_user_id(owner_user_id)
    provider_name = _normalize_configurable_provider(provider)
    credential = _resolve_user_provider_credential(
        owner,
        provider_name,
        database_url=database_url,
        database_url_env=database_url_env,
        psql_bin=psql_bin,
        ensure_schema=ensure_schema,
    )
    try:
        if provider_name == "groq":
            return Groq(api_key=credential)
        return OpenAI(api_key=credential)
    except Exception:
        raise UserProviderRuntimeConfigurationError(
            "client_construction_failed", provider_name
        ) from None
