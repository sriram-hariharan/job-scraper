# phase56b legacy guard marker: changes_only 0631df36d23740a835c22bcb2b9bf4ad682279f76794273889006cad9c4ec011 73a21e09d6e0c5213c1a7b2ea2f571cef7631c4cb18dcfa8177cfc8e44eb40d5
# phase56a legacy guard marker: changes_only f9137ef3f8d1cc27fe08f3a592f1cff977a124cb6132a91394ee8350674bea6f 0631df36d23740a835c22bcb2b9bf4ad682279f76794273889006cad9c4ec011
# phase26c legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c
# phase26b legacy guard marker: changes_only f9137ef3f8d1cc27fe08f3a592f1cff977a124cb6132a91394ee8350674bea6f
# phase23f legacy guard marker: changes_only f9137ef3f8d1cc27fe08f3a592f1cff977a124cb6132a91394ee8350674bea6f 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
# phase23f legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from src.agents.provider_live_config_gate import (
    POLICY_LIMITS,
    evaluate_provider_live_config_gate,
)


ROOT = Path(__file__).resolve().parents[1]


def _valid_config():
    return {
        "live_canary_enabled": True,
        "agent_name": "jd_intelligence",
        "shadow_only": True,
        "provider_name": "approved-provider",
        "model_name": "approved-model",
        "allowed_provider_names": ["approved-provider"],
        "allowed_model_names": ["approved-model"],
        "timeout_seconds": 10,
        "retry_limit": 1,
        "max_input_tokens": 4_000,
        "max_output_tokens": 1_000,
        "max_estimated_cost": 0.25,
        "structured_output_validation_required": True,
        "deterministic_fallback_required": True,
        "llmops_metadata_required": True,
        "prompt_version": "jd-shadow-prompt-v1",
        "runtime_version": "jd-live-canary-runtime-v1",
        "no_mutation_authority": True,
        "mutation_authorized": False,
        "final_scoring_influence_enabled": False,
        "ranking_influence_enabled": False,
        "queue_influence_enabled": False,
        "resume_mutation_enabled": False,
        "execution_enabled": False,
        "submission_enabled": False,
    }


def _blocked(config=None, *, enabled=True):
    result = evaluate_provider_live_config_gate(
        enabled=enabled,
        config=config,
    )
    assert result["canary_allowed"] is False
    assert result["provider_calls_allowed"] is False
    assert result["provider_calls_made"] is False
    return result


def test_default_and_missing_config_block_live_canary():
    default = _blocked(enabled=False)
    missing = _blocked({}, enabled=True)

    assert default["gate_status"] == (
        "live_config_gate_skipped_default_off"
    )
    assert "live_config_gate_not_enabled" in default["blocked_reasons"]
    assert missing["gate_status"] == "live_config_gate_blocked"
    assert "live_canary_not_explicitly_enabled" in (
        missing["blocked_reasons"]
    )
    assert "agent_name_missing" in missing["blocked_reasons"]


def test_disabled_config_blocks_live_canary():
    config = _valid_config()
    config["live_canary_enabled"] = False

    result = _blocked(config)

    assert "live_canary_not_explicitly_enabled" in (
        result["blocked_reasons"]
    )


def test_non_jd_tailoring_and_critic_agents_are_blocked():
    for agent_name in (
        "other_agent",
        "tailoring_suggestion",
        "critic_guardrail",
    ):
        config = _valid_config()
        config["agent_name"] = agent_name

        result = _blocked(config)

        assert "agent_name_must_be_jd_intelligence" in (
            result["blocked_reasons"]
        )


def test_non_shadow_mode_is_blocked():
    config = _valid_config()
    config["shadow_only"] = False

    result = _blocked(config)

    assert "shadow_only_must_be_true" in result["blocked_reasons"]


def test_provider_and_model_must_be_explicitly_allowlisted():
    provider = _valid_config()
    provider["provider_name"] = "unapproved-provider"
    model = _valid_config()
    model["model_name"] = "unapproved-model"

    provider_result = _blocked(provider)
    model_result = _blocked(model)

    assert "provider_name_not_allowlisted" in (
        provider_result["blocked_reasons"]
    )
    assert "model_name_not_allowlisted" in (
        model_result["blocked_reasons"]
    )


def test_missing_and_excessive_timeout_and_retry_are_blocked():
    cases = (
        ("timeout_seconds", None, "timeout_seconds_missing_or_invalid"),
        (
            "timeout_seconds",
            POLICY_LIMITS["max_timeout_seconds"] + 1,
            "timeout_seconds_exceeds_policy_limit",
        ),
        ("retry_limit", None, "retry_limit_missing_or_invalid"),
        (
            "retry_limit",
            POLICY_LIMITS["max_retry_limit"] + 1,
            "retry_limit_exceeds_policy_limit",
        ),
    )
    for key, value, reason in cases:
        config = _valid_config()
        config[key] = value

        result = _blocked(config)

        assert reason in result["blocked_reasons"]


def test_missing_and_excessive_token_and_cost_budgets_are_blocked():
    cases = (
        (
            "max_input_tokens",
            None,
            "max_input_tokens_missing_or_invalid",
        ),
        (
            "max_input_tokens",
            POLICY_LIMITS["max_input_tokens"] + 1,
            "max_input_tokens_exceeds_policy_limit",
        ),
        (
            "max_output_tokens",
            None,
            "max_output_tokens_missing_or_invalid",
        ),
        (
            "max_output_tokens",
            POLICY_LIMITS["max_output_tokens"] + 1,
            "max_output_tokens_exceeds_policy_limit",
        ),
        (
            "max_estimated_cost",
            None,
            "max_estimated_cost_missing_or_invalid",
        ),
        (
            "max_estimated_cost",
            POLICY_LIMITS["max_estimated_cost"] + 0.01,
            "max_estimated_cost_exceeds_policy_limit",
        ),
    )
    for key, value, reason in cases:
        config = _valid_config()
        config[key] = value

        result = _blocked(config)

        assert reason in result["blocked_reasons"]


def test_validation_fallback_llmops_and_versions_are_required():
    cases = (
        (
            "structured_output_validation_required",
            False,
            "structured_output_validation_must_be_required",
        ),
        (
            "deterministic_fallback_required",
            False,
            "deterministic_fallback_must_be_required",
        ),
        (
            "llmops_metadata_required",
            False,
            "llmops_metadata_must_be_required",
        ),
        ("prompt_version", "", "prompt_version_missing"),
        ("runtime_version", "", "runtime_version_missing"),
    )
    for key, value, reason in cases:
        config = _valid_config()
        config[key] = value

        result = _blocked(config)

        assert reason in result["blocked_reasons"]


def test_mutation_authority_and_any_decision_influence_are_blocked():
    mutation = _valid_config()
    mutation["mutation_authorized"] = True
    mutation["no_mutation_authority"] = False
    mutation_result = _blocked(mutation)

    assert "no_mutation_authority_must_be_true" in (
        mutation_result["blocked_reasons"]
    )
    assert "mutation_authorized_must_be_false" in (
        mutation_result["blocked_reasons"]
    )

    for key in (
        "final_scoring_influence_enabled",
        "ranking_influence_enabled",
        "queue_influence_enabled",
        "resume_mutation_enabled",
        "execution_enabled",
        "submission_enabled",
    ):
        config = _valid_config()
        config[key] = True

        result = _blocked(config)

        assert f"{key}_must_be_false" in result["blocked_reasons"]


def test_fully_valid_jd_shadow_config_allows_future_canary_only():
    config = _valid_config()
    before = deepcopy(config)

    result = evaluate_provider_live_config_gate(
        enabled=True,
        config=config,
    )

    assert result["gate_status"] == (
        "live_config_gate_allowed_for_future_canary"
    )
    assert result["canary_allowed"] is True
    assert result["blocked_reasons"] == []
    assert result["allowed_agent_name"] == "jd_intelligence"
    assert result["provider_calls_allowed"] is True
    assert result["provider_calls_made"] is False
    assert result["shadow_only"] is True
    assert result["mutation_authorized"] is False
    assert result["mutation_authorized_agent_count"] == 0
    assert result["validation_required"] is True
    assert result["fallback_required"] is True
    assert result["llmops_required"] is True
    assert result["next_safe_step"]
    assert config == before
    assert result["config_snapshot"] == before
    assert result["config_snapshot"] is not config


def test_gate_has_no_sdk_network_env_client_storage_or_runtime_wiring():
    source = (
        ROOT / "src/agents/provider_live_config_gate.py"
    ).read_text(encoding="utf-8").lower()
    for marker in (
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
        "run_provider_runtime_adapter(",
        "run_jd_provider_runtime_activation(",
        "provider_callable(",
        "provider_client(",
        "provider_client.invoke(",
        "create_embedding(",
        "database_url",
        "connect(",
        "cursor.execute",
        ".commit(",
        "open(",
        "write_text(",
        "write_bytes(",
        "score_jobs(",
        "rank_jobs(",
        "create_approval_request(",
        "mutate_resume(",
        "create_execution_request(",
        "execute_application(",
        "submit_application(",
    ):
        assert marker not in source


def test_protected_surfaces_dependencies_and_pipeline_are_unchanged():
    expected = {
        "requirements.txt": ("96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f"),
        "src/app/api.py": ("f9137ef3f8d1cc27fe08f3a592f1cff977a124cb6132a91394ee8350674bea6f"),
        "src/app/services.py": ("0631df36d23740a835c22bcb2b9bf4ad682279f76794273889006cad9c4ec011"),
        "src/app/static/agentic_review.js": ("1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b"),
        "src/pipeline/collector.py": ("73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405"),
        "src/pipeline/application_scorer.py": ("e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b"),
        "src/pipeline/job_ranker.py": ("5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54"),
        "application_execution_queue.py": ("c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0"),
    }

    for relative_path, expected_hash in expected.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )
