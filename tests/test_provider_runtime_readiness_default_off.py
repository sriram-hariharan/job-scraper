from copy import deepcopy
from pathlib import Path

from src.agents.provider_runtime_readiness import (
    build_provider_runtime_readiness_payload,
)


ROOT = Path(__file__).resolve().parents[1]


def _complete_config():
    return {
        "provider_name": "injected-provider",
        "model_name": "shadow-model-v1",
        "configured_agent_names": [
            "jd_intelligence",
            "tailoring_suggestion",
            "critic_guardrail",
        ],
        "shadow_only": True,
        "mutation_authorized": False,
    }


def _assert_safety(payload):
    safety = payload["safety_metadata"]
    assert safety["read_only"] is True
    assert safety["shadow_only"] is True
    assert safety["provider_calls_made"] is False
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
    assert payload["mutation_authorized"] is False
    assert payload["mutation_authorized_agent_count"] == 0


def test_default_off_returns_skipped_payload():
    payload = build_provider_runtime_readiness_payload()

    assert payload["readiness_status"] == "skipped_default_off"
    assert payload["provider_runtime_readiness_enabled"] is False
    assert payload["provider_runtime_default_off"] is True
    assert payload["provider_calls_allowed"] is False
    assert payload["next_safe_step"] == (
        "enable_provider_runtime_readiness_check"
    )
    _assert_safety(payload)


def test_enabled_missing_provider_configuration_is_deterministic():
    payload = build_provider_runtime_readiness_payload(
        enabled=True,
        config={"model_name": "shadow-model-v1"},
    )

    assert payload["readiness_status"] == (
        "missing_provider_configuration"
    )
    assert payload["missing_configuration_keys"] == [
        "provider_name",
        "configured_agent_names",
    ]
    assert payload["provider_runtime_configured"] is False
    assert payload["provider_calls_allowed"] is False
    _assert_safety(payload)


def test_complete_shadow_configuration_returns_ready_runtime():
    payload = build_provider_runtime_readiness_payload(
        enabled=True,
        config=_complete_config(),
    )

    assert payload["readiness_status"] == (
        "ready_shadow_provider_runtime"
    )
    assert payload["provider_name"] == "injected-provider"
    assert payload["model_name"] == "shadow-model-v1"
    assert payload["provider_runtime_configured"] is True
    assert payload["configured_agent_names"] == [
        "jd_intelligence",
        "tailoring_suggestion",
        "critic_guardrail",
    ]
    assert payload["provider_backed_agent_count"] == 3
    assert payload["shadow_only"] is True
    assert payload["provider_calls_allowed"] is False
    _assert_safety(payload)


def test_provider_calls_allowed_requires_explicit_ready_opt_in():
    default_calls = build_provider_runtime_readiness_payload(
        enabled=True,
        config=_complete_config(),
    )
    explicit_calls = build_provider_runtime_readiness_payload(
        enabled=True,
        config=_complete_config(),
        provider_calls_allowed=True,
    )
    incomplete_calls = build_provider_runtime_readiness_payload(
        enabled=True,
        config={},
        provider_calls_allowed=True,
    )

    assert default_calls["provider_calls_allowed"] is False
    assert explicit_calls["provider_calls_allowed"] is True
    assert explicit_calls["next_safe_step"] == (
        "inject_provider_callable_for_explicit_shadow_test"
    )
    assert incomplete_calls["provider_calls_allowed"] is False


def test_non_shadow_or_mutation_configuration_is_blocked():
    non_shadow = _complete_config()
    non_shadow["shadow_only"] = False
    mutation = _complete_config()
    mutation["mutation_authorized"] = True

    for config in (non_shadow, mutation):
        payload = build_provider_runtime_readiness_payload(
            enabled=True,
            config=config,
            provider_calls_allowed=True,
        )
        assert payload["readiness_status"] == "provider_runtime_blocked"
        assert payload["provider_calls_allowed"] is False
        assert payload["shadow_only"] is True
        assert payload["mutation_authorized"] is False
        assert payload["mutation_authorized_agent_count"] == 0
        _assert_safety(payload)


def test_helper_does_not_mutate_input_configuration():
    config = _complete_config()
    before = deepcopy(config)

    build_provider_runtime_readiness_payload(
        enabled=True,
        config=config,
        provider_calls_allowed=True,
    )

    assert config == before


def test_contract_has_no_provider_sdk_network_storage_or_mutation_wiring():
    source = (
        ROOT / "src/agents/provider_runtime_readiness.py"
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


def test_no_api_ui_pipeline_or_dependency_wiring():
    sources = {
        "api": (ROOT / "src/app/api.py").read_text(encoding="utf-8"),
        "ui": (ROOT / "src/app/static/agentic_review.js").read_text(
            encoding="utf-8"
        ),
        "pipeline": (ROOT / "src/pipeline/collector.py").read_text(
            encoding="utf-8"
        ),
        "dependencies": (ROOT / "requirements.txt").read_text(
            encoding="utf-8"
        ),
    }
    for source in sources.values():
        assert "provider_runtime_readiness" not in source
        assert "build_provider_runtime_readiness_payload" not in source


def test_service_bridge_uses_readiness_contract_without_provider_execution():
    source = (ROOT / "src/app/services.py").read_text(encoding="utf-8")
    start = source.index("def provider_runtime_readiness_service_payload(")
    end = source.index(
        "\ndef vector_evidence_readback_service_helper_payload(",
        start,
    )
    snippet = source[start:end]

    assert "src.agents.provider_runtime_readiness" in snippet
    assert "build_provider_runtime_readiness_payload" in snippet
    assert '"provider_calls_made": False' in snippet
