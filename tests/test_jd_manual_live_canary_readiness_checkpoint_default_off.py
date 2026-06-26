# phase23f legacy guard marker: changes_only f68ffa1e18343ffe85cbe4493064fb7e6af10edbc27efe3aa6459cd48088bc54 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 83bcc1e4f1c276e42e7306e30a2beb2a60a4f92bc0efe41f2525d4540d866167 898a88b49c765d59c099132a049aad79ea3c42774ad58912c0aac9b0d859d9a2
# phase23f legacy guard marker: changes_only 898a88b49c765d59c099132a049aad79ea3c42774ad58912c0aac9b0d859d9a2
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from src.agents.jd_live_provider_canary_command import (
    run_manual_jd_live_provider_canary_command,
)
from src.agents.jd_live_provider_canary_runbook import (
    build_jd_live_provider_canary_runbook,
)
from src.agents.jd_live_provider_external_adapter import (
    invoke_jd_live_provider_external_adapter,
)
from src.agents.provider_live_config_gate import (
    evaluate_provider_live_config_gate,
)


ROOT = Path(__file__).resolve().parents[1]
PHASE14_ARTIFACTS = (
    "src/agents/jd_live_provider_canary_command.py",
    "src/agents/jd_live_provider_external_adapter.py",
    "src/agents/jd_live_provider_canary_runbook.py",
    "tests/test_jd_live_provider_canary_command_default_off.py",
    "tests/test_jd_live_provider_external_adapter_default_off.py",
    "tests/test_jd_live_provider_canary_runbook_default_off.py",
)
NEXT_SAFE_STEP = (
    "manual_local_one_job_jd_shadow_canary_with_external_adapter"
)


def _source(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def _job() -> dict:
    return {
        "title": "Data Platform Engineer",
        "company": "Example Co",
        "job_description": "Build Python and SQL data systems.",
    }


def _valid_config() -> dict:
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


def _valid_output() -> dict:
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


def _valid_response() -> dict:
    return {
        "output": _valid_output(),
        "latency_ms": 12,
        "token_usage": {
            "input_tokens": 10,
            "output_tokens": 4,
            "total_tokens": 14,
        },
        "cost": {"estimated_cost": 0.002},
    }


def test_all_phase14_manual_canary_artifacts_are_present():
    for relative_path in PHASE14_ARTIFACTS:
        assert (ROOT / relative_path).is_file(), relative_path


def test_default_command_and_gate_block_without_adapter_invocation():
    calls = []
    gate = evaluate_provider_live_config_gate()
    command = run_manual_jd_live_provider_canary_command(
        job_payload=_job(),
        external_adapter=lambda request: calls.append(request),
    )

    assert calls == []
    assert gate["canary_allowed"] is False
    assert gate["provider_calls_allowed"] is False
    assert gate["provider_calls_made"] is False
    assert command["manual_command_enabled"] is False
    assert command["canary_attempted"] is False
    assert command["provider_call_attempted"] is False
    assert command["fallback_used"] is True
    assert command["fallback_reason"] == "manual_command_not_enabled"


def test_only_explicit_valid_jd_shadow_config_can_pass_gate():
    valid = evaluate_provider_live_config_gate(
        enabled=True,
        config=_valid_config(),
    )

    assert valid["canary_allowed"] is True
    assert valid["agent_name"] == "jd_intelligence"
    assert valid["shadow_only"] is True
    assert valid["provider_calls_made"] is False
    for agent_name in ("tailoring_suggestion", "critic_guardrail"):
        config = _valid_config()
        config["agent_name"] = agent_name
        blocked = evaluate_provider_live_config_gate(
            enabled=True,
            config=config,
        )
        assert blocked["canary_allowed"] is False
        assert "agent_name_must_be_jd_intelligence" in (
            blocked["blocked_reasons"]
        )


def test_manual_command_is_one_job_only_and_requires_external_injection():
    calls = []
    missing = run_manual_jd_live_provider_canary_command(
        enabled=True,
        job_payload=_job(),
        live_config=_valid_config(),
    )
    batch = run_manual_jd_live_provider_canary_command(
        enabled=True,
        job_payloads=[_job(), _job()],
        live_config=_valid_config(),
        external_adapter=lambda request: calls.append(request),
    )

    assert calls == []
    assert missing["fallback_reason"] == (
        "missing_injected_provider_adapter"
    )
    assert missing["provider_call_attempted"] is False
    assert batch["one_job_only"] is False
    assert batch["fallback_reason"] == "multiple_jobs_not_allowed"
    assert batch["canary_attempted"] is False


def test_external_adapter_contract_is_explicit_and_fail_closed():
    calls = []
    request = {
        "agent_name": "jd_intelligence",
        "shadow_only": True,
        "job_payload": _job(),
    }
    blocked_config = _valid_config()
    blocked_config["shadow_only"] = False

    blocked = invoke_jd_live_provider_external_adapter(
        enabled=True,
        request_payload=request,
        live_config=blocked_config,
        external_adapter=lambda value: calls.append(value),
    )
    invalid = invoke_jd_live_provider_external_adapter(
        enabled=True,
        request_payload=request,
        live_config=_valid_config(),
        external_adapter=lambda _value: {"output": []},
    )

    assert calls == []
    assert blocked["external_adapter_invoked"] is False
    assert blocked["adapter_error_type"] == "LiveConfigGateBlocked"
    assert invalid["external_adapter_invoked"] is True
    assert invalid["external_adapter_succeeded"] is False
    assert invalid["external_adapter_failed"] is True
    assert invalid["output_schema_validated"] is False


def test_fake_external_adapter_path_is_shadow_readback_only():
    calls = []
    job = _job()
    config = _valid_config()
    job_before = deepcopy(job)
    config_before = deepcopy(config)

    def adapter(request):
        calls.append(deepcopy(request))
        return _valid_response()

    result = run_manual_jd_live_provider_canary_command(
        enabled=True,
        job_payload=job,
        live_config=config,
        external_adapter=adapter,
    )

    assert len(calls) == 1
    assert calls[0]["agent_name"] == "jd_intelligence"
    assert calls[0]["shadow_only"] is True
    assert result["one_job_only"] is True
    assert result["jd_only"] is True
    assert result["shadow_only"] is True
    assert result["config_gate_allowed"] is True
    assert result["provider_call_succeeded"] is True
    assert result["structured_output_validated"] is True
    assert result["fallback_used"] is False
    assert result["external_adapter_bridge"][
        "output_schema_validated"
    ] is True
    assert result["readback"]["provider_call_succeeded"] is True
    assert result["llmops_metadata"]["total_tokens"] == 14
    assert result["llmops_metadata"]["estimated_cost"] == 0.002
    assert job == job_before
    assert config == config_before


def test_deterministic_fallback_readback_and_zero_authority_exist():
    failed = run_manual_jd_live_provider_canary_command(
        enabled=True,
        job_payload=_job(),
        live_config=_valid_config(),
        external_adapter=lambda _request: {"output": []},
    )

    assert failed["fallback_used"] is True
    assert failed["provider_call_succeeded"] is False
    assert failed["structured_output_validated"] is False
    assert failed["readback"]["fallback_used"] is True
    assert failed["llmops_metadata"]["fallback_used"] is True
    assert failed["mutation_authorized"] is False
    assert failed["mutation_authorized_agent_count"] == 0
    assert failed["scoring_influence_disabled"] is True
    assert failed["ranking_influence_disabled"] is True
    assert failed["queue_influence_disabled"] is True
    assert failed["resume_mutation_disabled"] is True
    assert failed["execution_submission_disabled"] is True
    safety = failed["safety_metadata"]
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


def test_runbook_closes_rollback_and_operator_readiness_contract():
    runbook = build_jd_live_provider_canary_runbook(enabled=True)
    rollback = runbook["rollback_and_off_switch"]
    sequence = runbook["manual_sequence"]
    proof = runbook["proof_required_before_broader_rollout"]

    assert runbook["allowed_agent_name"] == "jd_intelligence"
    assert runbook["blocked_agent_names"] == [
        "tailoring_suggestion",
        "critic_guardrail",
    ]
    assert runbook["one_job_only"] is True
    assert runbook["shadow_only_required"] is True
    assert runbook["external_adapter_required"] is True
    assert runbook["execution_authorized"] is False
    assert "provide_external_adapter_outside_repository" in sequence
    assert "invoke_phase_14a_manual_command_in_shadow_only_mode" in (
        sequence
    )
    assert rollback["stop_on_any_adapter_error"] is True
    assert rollback["disable_manual_command"] is True
    assert rollback["disable_live_canary_config"] is True
    assert rollback["remove_external_adapter_injection"] is True
    assert rollback["broader_rollout_authorized"] is False
    assert "llmops_and_readback_verified" in proof
    assert "zero_mutation_authority_verified" in proof
    assert NEXT_SAFE_STEP == (
        "manual_local_one_job_jd_shadow_canary_with_external_adapter"
    )


def test_phase14_has_no_sdk_env_direct_network_or_storage_wiring():
    sources = "\n".join(
        _source(path)
        for path in (
            "src/agents/jd_live_provider_canary_command.py",
            "src/agents/jd_live_provider_external_adapter.py",
            "src/agents/jd_live_provider_canary_runbook.py",
        )
    ).lower()
    for marker in (
        "from openai",
        "import openai",
        "from anthropic",
        "import anthropic",
        "langchain",
        "sentence_transformers",
        "requests.",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "os.getenv",
        "os.environ",
        "api_key",
        "provider_client(",
        "provider_client.invoke(",
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
        assert marker not in sources


def test_api_ui_service_pipeline_and_dependencies_are_unchanged():
    expected = {
        "requirements.txt": ("96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f"),
        "src/app/api.py": ("f68ffa1e18343ffe85cbe4493064fb7e6af10edbc27efe3aa6459cd48088bc54"),
        "src/app/services.py": ("2c67ab4d78299de8e54db6ef76ea77598f7e98c1d2f516df97cea4c014e7b6ee"),
        "src/app/static/agentic_review.js": ("898a88b49c765d59c099132a049aad79ea3c42774ad58912c0aac9b0d859d9a2"),
        "src/pipeline/collector.py": ("73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405"),
        "src/pipeline/application_scorer.py": ("e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b"),
        "src/pipeline/job_ranker.py": ("5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54"),
        "application_execution_queue.py": ("c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0"),
    }

    for relative_path, expected_hash in expected.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )
