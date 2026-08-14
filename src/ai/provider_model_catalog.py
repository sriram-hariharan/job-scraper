"""Static user-configurable provider and model catalog.

The catalog describes configuration candidates only. It does not read runtime
configuration, construct provider clients, or claim live qualification.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Optional


CONFIGURABLE_PROVIDER_ORDER = ("groq", "openai")
CONFIGURATION_CANDIDATE_MODEL_ORDER = (
    ("groq", "openai/gpt-oss-20b"),
    ("groq", "openai/gpt-oss-120b"),
    ("openai", "gpt-5-mini"),
    ("openai", "gpt-5.1"),
)

_CONFIGURABLE_MODEL_DEFINITIONS = (
    {
        "provider": "groq",
        "model_id": "openai/gpt-oss-20b",
        "eligible_benchmark_tiers": ["A", "B", "C"],
        "configuration_status": "configuration_eligible",
        "synthetic_compatibility_status": "synthetic_compatibility_expected",
        "live_qualification_status": "live_qualification_required",
        "user_settings_visible": True,
    },
    {
        "provider": "groq",
        "model_id": "openai/gpt-oss-120b",
        "eligible_benchmark_tiers": ["B", "C"],
        "configuration_status": "configuration_eligible",
        "synthetic_compatibility_status": "synthetic_compatibility_expected",
        "live_qualification_status": "live_qualification_required",
        "user_settings_visible": True,
    },
    {
        "provider": "openai",
        "model_id": "gpt-5-mini",
        "eligible_benchmark_tiers": ["A", "B", "C"],
        "configuration_status": "configuration_eligible",
        "synthetic_compatibility_status": "synthetic_compatibility_expected",
        "live_qualification_status": "live_qualification_required",
        "user_settings_visible": True,
    },
    {
        "provider": "openai",
        "model_id": "gpt-5.1",
        "eligible_benchmark_tiers": ["B", "C"],
        "configuration_status": "configuration_eligible",
        "synthetic_compatibility_status": "synthetic_compatibility_expected",
        "live_qualification_status": "live_qualification_required",
        "user_settings_visible": True,
    },
)


def _normalize_provider(provider: Any) -> str:
    return str(provider or "").strip().lower()


def _normalize_model_id(model_id: Any) -> str:
    return str(model_id or "").strip()


def list_configurable_providers() -> List[str]:
    """Return configurable providers in deterministic display order."""

    return list(CONFIGURABLE_PROVIDER_ORDER)


def list_configurable_models(provider: Any = None) -> List[Dict[str, Any]]:
    """Return defensive model-definition copies, optionally for one provider."""

    provider_name = _normalize_provider(provider)
    if provider is not None and provider_name not in CONFIGURABLE_PROVIDER_ORDER:
        return []

    definitions = _CONFIGURABLE_MODEL_DEFINITIONS
    if provider is not None:
        definitions = tuple(
            definition
            for definition in definitions
            if definition["provider"] == provider_name
        )
    return deepcopy(list(definitions))


def get_configurable_model(
    provider: Any,
    model_id: Any,
) -> Optional[Dict[str, Any]]:
    """Return one exact provider/model definition, or ``None`` when unknown."""

    provider_name = _normalize_provider(provider)
    model_name = _normalize_model_id(model_id)
    for definition in _CONFIGURABLE_MODEL_DEFINITIONS:
        if (
            definition["provider"] == provider_name
            and definition["model_id"] == model_name
        ):
            return deepcopy(definition)
    return None


def is_configuration_eligible(provider: Any, model_id: Any) -> bool:
    """Return whether the exact provider/model pair may be configured."""

    return get_configurable_model(provider, model_id) is not None


def get_eligible_benchmark_tiers(provider: Any, model_id: Any) -> List[str]:
    """Return eligible benchmark tiers for an exact configurable pair."""

    definition = get_configurable_model(provider, model_id)
    if definition is None:
        return []
    return list(definition["eligible_benchmark_tiers"])
