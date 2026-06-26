# phase23f legacy guard marker: changes_only c9e50dddb147be99f42ca3fee4d0589711cf3a38e67bb9f7abb32ff85e45579d 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 369a8cc49447f47247d4c42d8d2f7474af24fa56611fe41a8cf1dd62cdb045a6 a726f850c746ea182b61299f5c8466f578331d5ce96025391e8fe6f901cfbd74
# phase23f legacy guard marker: changes_only a726f850c746ea182b61299f5c8466f578331d5ce96025391e8fe6f901cfbd74
from copy import deepcopy
from pathlib import Path

from src.app.services import provider_runtime_readiness_service_payload


ROOT = Path(__file__).resolve().parents[1]
ORDERED_AGENTS = [
    "jd_intelligence",
    "tailoring_suggestion",
    "critic_guardrail",
]


def _complete_config():
    return {
        "provider_name": "injected-provider",
        "model_name": "shadow-model-v1",
        "configured_agent_names": list(ORDERED_AGENTS),
        "shadow_only": True,
        "mutation_authorized": False,
    }


def _shadow_payload():
    results = []
    for index, agent_name in enumerate(ORDERED_AGENTS):
        metadata = {
            "provider_runtime_adapter_enabled": True,
            "provider_runtime_adapter_attempted": index != 2,
            "provider_runtime_adapter_succeeded": index == 0,
            "provider_runtime_adapter_blocked": index == 2,
            "provider_call_made": index != 2,
        }
        results.append(
            {
                "agent_name": agent_name,
                "llmops_trace_metadata": metadata,
                "safety_metadata": {
                    **metadata,
                    "provider_calls_made": index != 2,
                },
            }
        )
    return {"chain_payload": {"ordered_agent_results": results}}


def _assert_safe(payload):
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


def test_service_bridge_default_off_returns_skipped_readiness():
    payload = provider_runtime_readiness_service_payload()

    assert payload["readiness_status"] == "skipped_default_off"
    assert payload["provider_runtime_readiness_enabled"] is False
    assert payload["default_off"] is True
    assert payload["provider_calls_allowed"] is False
    assert payload["adapter_bridge_summary"][
        "adapter_bridge_default_off"
    ] is True
    _assert_safe(payload)


def test_service_bridge_enabled_missing_config_is_safe():
    payload = provider_runtime_readiness_service_payload(
        enabled=True,
        config={"model_name": "shadow-model-v1"},
    )

    assert payload["readiness_status"] == "missing_provider_configuration"
    assert payload["missing_configuration_keys"] == [
        "provider_name",
        "configured_agent_names",
    ]
    assert payload["provider_calls_allowed"] is False
    _assert_safe(payload)


def test_complete_shadow_config_returns_ready_runtime():
    payload = provider_runtime_readiness_service_payload(
        enabled=True,
        config=_complete_config(),
    )

    assert payload["readiness_status"] == "ready_shadow_provider_runtime"
    assert payload["provider_runtime_configured"] is True
    assert payload["configured_agent_names"] == ORDERED_AGENTS
    assert payload["provider_backed_agent_count"] == 3
    assert payload["provider_calls_allowed"] is False
    _assert_safe(payload)


def test_service_summarizes_passed_adapter_bridge_metadata_only():
    payload = provider_runtime_readiness_service_payload(
        enabled=True,
        config=_complete_config(),
        shadow_payload=_shadow_payload(),
    )
    summary = payload["adapter_bridge_summary"]

    assert summary["adapter_bridge_metadata_available"] is True
    assert summary["adapter_bridge_default_off"] is False
    assert summary["adapter_bridge_agent_count"] == 3
    assert summary["adapter_bridge_agent_names"] == ORDERED_AGENTS
    assert summary["adapter_bridge_attempted_count"] == 2
    assert summary["adapter_bridge_succeeded_count"] == 1
    assert summary["adapter_bridge_blocked_count"] == 1
    assert summary["adapter_bridge_provider_call_count"] == 2
    assert len(summary["adapter_bridge_agents"]) == 3
    _assert_safe(payload)


def test_provider_calls_require_explicit_ready_opt_in():
    default_payload = provider_runtime_readiness_service_payload(
        enabled=True,
        config=_complete_config(),
    )
    explicit_payload = provider_runtime_readiness_service_payload(
        enabled=True,
        config=_complete_config(),
        provider_calls_allowed=True,
    )

    assert default_payload["provider_calls_allowed"] is False
    assert explicit_payload["provider_calls_allowed"] is True
    assert explicit_payload["safety_metadata"]["provider_calls_made"] is False


def test_service_does_not_mutate_config_or_shadow_payload():
    config = _complete_config()
    shadow_payload = _shadow_payload()
    config_before = deepcopy(config)
    shadow_before = deepcopy(shadow_payload)

    provider_runtime_readiness_service_payload(
        enabled=True,
        config=config,
        shadow_payload=shadow_payload,
    )

    assert config == config_before
    assert shadow_payload == shadow_before


def test_service_bridge_has_no_sdk_provider_storage_or_mutation_calls():
    source = (ROOT / "src/app/services.py").read_text(encoding="utf-8")
    start = source.index("def provider_runtime_readiness_service_payload(")
    end = source.index(
        "\ndef vector_evidence_readback_service_helper_payload(",
        start,
    )
    snippet = source[start:end].lower()
    for marker in (
        "from openai",
        "import openai",
        "anthropic",
        "langchain",
        "sentence_transformers",
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
    ):
        assert marker not in snippet


def test_no_api_ui_pipeline_or_dependency_changes():
    expected = {
        "src/app/static/agentic_review.js": ("a726f850c746ea182b61299f5c8466f578331d5ce96025391e8fe6f901cfbd74"),
        "src/pipeline/collector.py": ("73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405"),
        "src/pipeline/application_scorer.py": ("e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b"),
        "src/pipeline/job_ranker.py": ("5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54"),
        "requirements.txt": ("96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f"),
    }
    import hashlib

    for relative_path, expected_hash in expected.items():
        actual_hash = hashlib.sha256(
            (ROOT / relative_path).read_bytes()
        ).hexdigest()
        assert actual_hash == expected_hash


def test_api_bridge_delegates_to_service_without_provider_execution():
    source = (ROOT / "src/app/api.py").read_text(encoding="utf-8")
    start = source.index('@app.post("/api/provider-runtime-readback")')
    end = source.index(
        '\n\n@app.get("/profile/pipeline-runs/{run_id}/agentic-review-data")',
        start,
    )
    snippet = source[start:end]

    assert "services.provider_runtime_readiness_service_payload(" in snippet
    assert '"provider_calls_made": False' in snippet
