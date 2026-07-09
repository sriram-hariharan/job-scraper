# phase79b legacy guard marker: changes_only collector_hash_old 73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405
# phase56b legacy guard marker: changes_only bfa035faa8e89abd2b75095f68b45a282fb3b7fc8e5ff43e36c754db56ef12c2 1ff2a73993300f391aa1fb8151a4d225e803b6c5d499e311faa5058efc4b965c
# phase56a legacy guard marker: changes_only d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004 bfa035faa8e89abd2b75095f68b45a282fb3b7fc8e5ff43e36c754db56ef12c2
# phase26c legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c
# phase26b legacy guard marker: changes_only d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004
# phase23f legacy guard marker: changes_only d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
# phase23f legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from src.agents.jd_live_provider_canary_command import (
    run_manual_jd_live_provider_canary_command,
)


ROOT = Path(__file__).resolve().parents[1]


def _job():
    return {
        "title": "Data Platform Engineer",
        "company": "Example Co",
        "job_description": "Build Python and SQL data systems.",
    }


def _config():
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
        "prompt_version": "jd-live-canary-prompt-v1",
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


def _valid_output():
    return {
        "required_skills": ["Python", "SQL"],
        "preferred_skills": [],
        "required_tools": ["PostgreSQL"],
        "preferred_tools": [],
        "workflows": ["data systems"],
        "methods": [],
        "business_contexts": [],
        "stakeholder_contexts": [],
        "ownership_signals": [],
        "seniority_signals": [],
        "risk_flags": [],
        "extraction_confidence": 0.9,
    }


def _response(output):
    return {
        "output": deepcopy(output),
        "latency_ms": 12,
        "token_usage": {
            "input_tokens": 10,
            "output_tokens": 4,
            "total_tokens": 14,
        },
        "cost": {"estimated_cost": 0.002},
    }


def test_default_and_disabled_config_block_without_adapter_call():
    calls = []
    default = run_manual_jd_live_provider_canary_command(
        job_payload=_job(),
        provider_adapter=lambda request: calls.append(request),
    )
    disabled = _config()
    disabled["live_canary_enabled"] = False
    blocked = run_manual_jd_live_provider_canary_command(
        enabled=True,
        job_payload=_job(),
        live_config=disabled,
        provider_adapter=lambda request: calls.append(request),
    )

    assert calls == []
    assert default["manual_command_enabled"] is False
    assert default["config_gate_allowed"] is False
    assert default["provider_call_attempted"] is False
    assert blocked["config_gate_allowed"] is False
    assert blocked["provider_call_attempted"] is False


def test_non_shadow_config_is_blocked():
    calls = []
    config = _config()
    config["shadow_only"] = False

    result = run_manual_jd_live_provider_canary_command(
        enabled=True,
        job_payload=_job(),
        live_config=config,
        provider_adapter=lambda request: calls.append(request),
    )

    assert calls == []
    assert result["shadow_only"] is False
    assert result["config_gate_allowed"] is False
    assert result["provider_call_attempted"] is False
    assert result["fallback_reason"] == "shadow_only_must_be_true"


def test_non_jd_tailoring_and_critic_are_blocked():
    for agent_name in (
        "other_agent",
        "tailoring_suggestion",
        "critic_guardrail",
    ):
        calls = []
        config = _config()
        config["agent_name"] = agent_name

        result = run_manual_jd_live_provider_canary_command(
            enabled=True,
            job_payload=_job(),
            live_config=config,
            provider_adapter=lambda request: calls.append(request),
        )

        assert calls == []
        assert result["jd_only"] is False
        assert result["config_gate_allowed"] is False
        assert result["provider_call_attempted"] is False


def test_batch_or_multiple_job_inputs_are_blocked():
    calls = []
    batch = run_manual_jd_live_provider_canary_command(
        enabled=True,
        job_payloads=[_job(), _job()],
        live_config=_config(),
        provider_adapter=lambda request: calls.append(request),
    )
    ambiguous = run_manual_jd_live_provider_canary_command(
        enabled=True,
        job_payload=_job(),
        job_payloads=[_job()],
        live_config=_config(),
        provider_adapter=lambda request: calls.append(request),
    )

    assert calls == []
    assert batch["one_job_only"] is False
    assert batch["fallback_reason"] == "multiple_jobs_not_allowed"
    assert ambiguous["one_job_only"] is False
    assert ambiguous["fallback_reason"] == (
        "multiple_job_inputs_not_allowed"
    )


def test_missing_injected_adapter_blocks_before_canary_runner():
    runner_calls = []
    result = run_manual_jd_live_provider_canary_command(
        enabled=True,
        job_payload=_job(),
        live_config=_config(),
        canary_runner=lambda **kwargs: runner_calls.append(kwargs),
    )

    assert runner_calls == []
    assert result["config_gate_allowed"] is True
    assert result["provider_call_attempted"] is False
    assert result["fallback_used"] is True
    assert result["fallback_reason"] == (
        "missing_injected_provider_adapter"
    )


def test_valid_one_job_config_calls_fake_adapter_exactly_once():
    calls = []
    job = _job()
    config = _config()
    before_job = deepcopy(job)
    before_config = deepcopy(config)

    def adapter(request):
        calls.append(deepcopy(request))
        return _response(_valid_output())

    result = run_manual_jd_live_provider_canary_command(
        enabled=True,
        job_payload=job,
        live_config=config,
        provider_adapter=adapter,
    )

    assert len(calls) == 1
    assert calls[0]["agent_name"] == "jd_intelligence"
    assert calls[0]["shadow_only"] is True
    assert result["command_status"] == (
        "manual_jd_live_canary_command_completed"
    )
    assert result["one_job_only"] is True
    assert result["jd_only"] is True
    assert result["shadow_only"] is True
    assert result["config_gate_allowed"] is True
    assert result["canary_attempted"] is True
    assert result["provider_call_attempted"] is True
    assert result["provider_call_succeeded"] is True
    assert result["structured_output_validated"] is True
    assert result["fallback_used"] is False
    assert job == before_job
    assert config == before_config


def test_invalid_output_and_adapter_exception_fall_back():
    invalid = run_manual_jd_live_provider_canary_command(
        enabled=True,
        job_payload=_job(),
        live_config=_config(),
        provider_adapter=lambda _request: _response(
            {"required_skills": {"invalid": "shape"}}
        ),
    )

    def failing_adapter(_request):
        raise RuntimeError("fixture failure")

    failed = run_manual_jd_live_provider_canary_command(
        enabled=True,
        job_payload=_job(),
        live_config=_config(),
        provider_adapter=failing_adapter,
    )

    assert invalid["fallback_used"] is True
    assert invalid["fallback_reason"] == "required_skills_not_list"
    assert invalid["structured_output_validated"] is False
    assert failed["fallback_used"] is True
    assert failed["fallback_reason"] == (
        "provider_adapter_error:RuntimeError"
    )
    assert failed["llmops_metadata"]["error_type"] == "RuntimeError"


def test_llmops_and_readback_metadata_are_emitted():
    result = run_manual_jd_live_provider_canary_command(
        enabled=True,
        job_payload=_job(),
        live_config=_config(),
        provider_adapter=lambda _request: _response(_valid_output()),
    )
    trace = result["llmops_metadata"]
    readback = result["readback"]

    assert trace["model_provider"] == "approved-provider"
    assert trace["model_name"] == "approved-model"
    assert trace["latency_ms"] == 12
    assert trace["total_tokens"] == 14
    assert trace["estimated_cost"] == 0.002
    assert readback["readback_status"] == (
        "jd_live_canary_readback_succeeded"
    )
    assert readback["provider_call_succeeded"] is True
    assert readback["structured_output_validated"] is True


def test_mutation_and_application_influence_remain_disabled():
    result = run_manual_jd_live_provider_canary_command(
        enabled=True,
        job_payload=_job(),
        live_config=_config(),
        provider_adapter=lambda _request: _response(_valid_output()),
    )
    safety = result["safety_metadata"]

    assert result["mutation_authorized"] is False
    assert result["mutation_authorized_agent_count"] == 0
    assert result["scoring_influence_disabled"] is True
    assert result["ranking_influence_disabled"] is True
    assert result["queue_influence_disabled"] is True
    assert result["resume_mutation_disabled"] is True
    assert result["execution_submission_disabled"] is True
    for key in (
        "did_write_database",
        "did_write_files",
        "did_mutate_scoring",
        "did_change_ranking",
        "did_mutate_queue",
        "did_create_approval",
        "did_mutate_resume",
        "did_create_execution_request",
        "did_execute_application",
        "did_submit_application",
    ):
        assert safety[key] is False


def test_helper_has_no_sdk_env_direct_provider_network_or_storage_wiring():
    source = (
        ROOT / "src/agents/jd_live_provider_canary_command.py"
    ).read_text(encoding="utf-8").lower()
    for marker in (
        "argparse",
        "if __name__",
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
        "provider_client(",
        "provider_client.invoke(",
        "create_embedding(",
        "database_url",
        "connect(",
        "cursor.execute(",
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


def test_api_ui_service_pipeline_and_dependencies_are_unchanged():
    expected = {
        "requirements.txt": ("96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f"),
        "src/app/api.py": ("d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004"),
        "src/app/services.py": ("bfa035faa8e89abd2b75095f68b45a282fb3b7fc8e5ff43e36c754db56ef12c2"),
        "src/app/static/agentic_review.js": ("1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b"),
        "src/pipeline/collector.py": ("1d35d00e54d1d858134b2e524955887bd7adbbce3a01e53d1782debc4584490a"),
        "src/pipeline/application_scorer.py": ("e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b"),
        "src/pipeline/job_ranker.py": ("5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54"),
        "application_execution_queue.py": ("c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0"),
    }

    for relative_path, expected_hash in expected.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )
