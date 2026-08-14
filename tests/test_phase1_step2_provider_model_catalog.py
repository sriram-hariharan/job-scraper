from __future__ import annotations

import importlib
import os
import sys

from src.ai import provider_model_catalog as catalog
from src.evaluation.provider_benchmark_contract import (
    build_provider_benchmark_contract,
)
from src.evaluation.provider_client_compatibility import (
    _isolated_shared_client,
)


EXPECTED_PROVIDERS = ["groq", "openai"]
EXPECTED_MODELS = [
    ("groq", "openai/gpt-oss-20b", ["A", "B", "C"]),
    ("groq", "openai/gpt-oss-120b", ["B", "C"]),
    ("openai", "gpt-5-mini", ["A", "B", "C"]),
    ("openai", "gpt-5.1", ["B", "C"]),
]
LEGACY_RUNTIME_MODELS = (
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile",
)


def _catalog_rows():
    return catalog.list_configurable_models()


def test_provider_and_model_order_are_exact_and_deterministic():
    assert catalog.list_configurable_providers() == EXPECTED_PROVIDERS
    assert [
        (
            row["provider"],
            row["model_id"],
            row["eligible_benchmark_tiers"],
        )
        for row in _catalog_rows()
    ] == EXPECTED_MODELS
    assert catalog.list_configurable_models() == catalog.list_configurable_models()


def test_qualification_semantics_and_user_visibility_are_explicit():
    for row in _catalog_rows():
        assert row["configuration_status"] == "configuration_eligible"
        assert row["synthetic_compatibility_status"] == (
            "synthetic_compatibility_expected"
        )
        assert row["live_qualification_status"] == "live_qualification_required"
        assert row["user_settings_visible"] is True
        assert "winner" not in row


def test_provider_filtering_and_exact_lookup_preserve_catalog_order():
    assert [
        row["model_id"] for row in catalog.list_configurable_models(" GROQ ")
    ] == ["openai/gpt-oss-20b", "openai/gpt-oss-120b"]
    assert [
        row["model_id"] for row in catalog.list_configurable_models("openai")
    ] == ["gpt-5-mini", "gpt-5.1"]
    assert catalog.list_configurable_models("unknown") == []
    assert catalog.get_configurable_model("groq", "openai/gpt-oss-20b") == (
        _catalog_rows()[0]
    )


def test_unknown_models_and_provider_model_mismatches_are_ineligible():
    assert catalog.is_configuration_eligible("groq", "arbitrary-model") is False
    assert catalog.is_configuration_eligible("unknown", "gpt-5-mini") is False
    assert catalog.is_configuration_eligible("groq", "gpt-5-mini") is False
    assert (
        catalog.is_configuration_eligible("openai", "openai/gpt-oss-20b")
        is False
    )
    assert catalog.get_configurable_model("groq", "gpt-5-mini") is None
    assert catalog.get_eligible_benchmark_tiers("groq", "gpt-5-mini") == []


def test_exact_tier_eligibility_read_api():
    for provider, model_id, tiers in EXPECTED_MODELS:
        assert catalog.is_configuration_eligible(provider, model_id) is True
        assert catalog.get_eligible_benchmark_tiers(provider, model_id) == tiers


def test_benchmark_candidate_and_tier_definitions_remain_in_parity():
    benchmark = build_provider_benchmark_contract()
    benchmark_rows = [
        (
            row["provider"],
            row["model"],
            row["eligible_tiers"],
        )
        for row in benchmark["candidate_definitions"]
    ]
    assert benchmark_rows == EXPECTED_MODELS
    assert benchmark_rows == [
        (
            row["provider"],
            row["model_id"],
            row["eligible_benchmark_tiers"],
        )
        for row in _catalog_rows()
    ]


def test_shared_client_provider_knowledge_matches_every_catalog_pair():
    with _isolated_shared_client() as (client, isolation):
        assert isolation["credential_reads"] == 0
        for provider, model_id, _tiers in EXPECTED_MODELS:
            assert client._KNOWN_MODEL_PROVIDERS[model_id] == provider
            assert client._normalize_and_validate_provider_model(
                provider,
                model_id,
            ) == (provider, model_id)


def test_legacy_llama_models_remain_runtime_supported_but_not_configurable():
    with _isolated_shared_client() as (client, isolation):
        assert isolation["credential_reads"] == 0
        for model_id in LEGACY_RUNTIME_MODELS:
            assert client._KNOWN_MODEL_PROVIDERS[model_id] == "groq"
            assert client._normalize_and_validate_provider_model(
                "groq",
                model_id,
            ) == ("groq", model_id)
            assert catalog.is_configuration_eligible("groq", model_id) is False
    assert not set(LEGACY_RUNTIME_MODELS).intersection(
        row["model_id"] for row in _catalog_rows()
    )


def test_catalog_import_does_not_read_environment_or_credentials(monkeypatch):
    module_name = "src.ai.provider_model_catalog"
    original_module = sys.modules.pop(module_name, None)

    def reject_environment_read(_name, _default=None):
        raise AssertionError("catalog import attempted an environment read")

    monkeypatch.setattr(os, "getenv", reject_environment_read)
    try:
        imported = importlib.import_module(module_name)
        assert imported.list_configurable_providers() == EXPECTED_PROVIDERS
    finally:
        sys.modules.pop(module_name, None)
        if original_module is not None:
            sys.modules[module_name] = original_module


def test_returned_structures_cannot_mutate_authoritative_catalog_state():
    providers = catalog.list_configurable_providers()
    models = catalog.list_configurable_models()
    one_model = catalog.get_configurable_model("groq", "openai/gpt-oss-20b")
    tiers = catalog.get_eligible_benchmark_tiers("groq", "openai/gpt-oss-20b")

    providers.append("mutated")
    models[0]["provider"] = "mutated"
    models[0]["eligible_benchmark_tiers"].append("mutated")
    one_model["model_id"] = "mutated"
    tiers.append("mutated")

    assert catalog.list_configurable_providers() == EXPECTED_PROVIDERS
    assert [
        (
            row["provider"],
            row["model_id"],
            row["eligible_benchmark_tiers"],
        )
        for row in catalog.list_configurable_models()
    ] == EXPECTED_MODELS
