# phase56b legacy guard marker: changes_only e86d8305951082be83084c3c4533c70bcd0ea8121da2a6564d862b7eb7b1fbff 1ff2a73993300f391aa1fb8151a4d225e803b6c5d499e311faa5058efc4b965c
# phase56a legacy guard marker: changes_only 85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96 e86d8305951082be83084c3c4533c70bcd0ea8121da2a6564d862b7eb7b1fbff
# phase26c legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c
# phase26b legacy guard marker: changes_only 85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96
# phase23f legacy guard marker: changes_only 85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
# phase23f legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from src.agents.jd_live_provider_canary_command import (
    run_manual_jd_live_provider_canary_command,
)
from src.agents.jd_live_provider_external_adapter import (
    build_jd_live_provider_external_adapter,
    invoke_jd_live_provider_external_adapter,
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


def _request():
    return {
        "agent_name": "jd_intelligence",
        "shadow_only": True,
        "job_payload": _job(),
    }


def _output():
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


def _response():
    return {
        "output": _output(),
        "latency_ms": 12,
        "token_usage": {
            "input_tokens": 10,
            "output_tokens": 4,
            "total_tokens": 14,
        },
        "cost": {"estimated_cost": 0.002},
    }


def test_missing_adapter_blocks_safely():
    result = invoke_jd_live_provider_external_adapter(
        enabled=True,
        request_payload=_request(),
        live_config=_config(),
    )

    assert result["external_adapter_configured"] is False
    assert result["external_adapter_invoked"] is False
    assert result["external_adapter_failed"] is False
    assert result["adapter_error_type"] == "MissingExternalAdapter"


def test_adapter_is_not_invoked_when_config_gate_blocks():
    calls = []
    config = _config()
    config["shadow_only"] = False

    result = invoke_jd_live_provider_external_adapter(
        enabled=True,
        request_payload=_request(),
        live_config=config,
        external_adapter=lambda request: calls.append(request),
    )

    assert calls == []
    assert result["external_adapter_invoked"] is False
    assert result["adapter_error_type"] == "LiveConfigGateBlocked"


def test_adapter_exception_returns_safe_error_metadata():
    def failing_adapter(_request):
        raise RuntimeError("fixture failure")

    result = invoke_jd_live_provider_external_adapter(
        enabled=True,
        request_payload=_request(),
        live_config=_config(),
        external_adapter=failing_adapter,
    )

    assert result["external_adapter_invoked"] is True
    assert result["external_adapter_succeeded"] is False
    assert result["external_adapter_failed"] is True
    assert result["adapter_error_type"] == "RuntimeError"
    assert result["adapter_error_message"] == "fixture failure"


def test_invalid_adapter_output_is_rejected():
    result = invoke_jd_live_provider_external_adapter(
        enabled=True,
        request_payload=_request(),
        live_config=_config(),
        external_adapter=lambda _request: {"output": []},
    )

    assert result["external_adapter_failed"] is True
    assert result["output_schema_validated"] is False
    assert result["adapter_error_type"] == "InvalidExternalAdapterOutput"
    assert result["adapter_error_message"] == (
        "external_adapter_output_missing"
    )


def test_valid_fake_adapter_output_is_normalized_without_mutation():
    request = _request()
    config = _config()
    request_before = deepcopy(request)
    config_before = deepcopy(config)

    result = invoke_jd_live_provider_external_adapter(
        enabled=True,
        request_payload=request,
        live_config=config,
        external_adapter=lambda _request: _response(),
    )

    assert result["external_adapter_succeeded"] is True
    assert result["output_schema_validated"] is True
    assert result["provider_name"] == "approved-provider"
    assert result["model_name"] == "approved-model"
    assert result["prompt_version"] == "jd-live-canary-prompt-v1"
    assert result["runtime_version"] == "jd-live-canary-runtime-v1"
    assert result["token_usage"]["total_tokens"] == 14
    assert result["estimated_cost"] == 0.002
    assert result["latency_ms"] == 12
    assert result["normalized_response"]["output"] == _output()
    assert request == request_before
    assert config == config_before


def test_valid_fake_adapter_passes_through_manual_command_once():
    calls = []

    def external_adapter(request):
        calls.append(deepcopy(request))
        return _response()

    result = run_manual_jd_live_provider_canary_command(
        enabled=True,
        job_payload=_job(),
        live_config=_config(),
        external_adapter=external_adapter,
    )

    bridge = result["external_adapter_bridge"]
    assert len(calls) == 1
    assert result["provider_call_succeeded"] is True
    assert result["structured_output_validated"] is True
    assert bridge["external_adapter_invoked"] is True
    assert bridge["external_adapter_succeeded"] is True
    assert bridge["output_schema_validated"] is True


def test_invalid_external_output_forces_manual_command_fallback():
    result = run_manual_jd_live_provider_canary_command(
        enabled=True,
        job_payload=_job(),
        live_config=_config(),
        external_adapter=lambda _request: {"output": []},
    )

    bridge = result["external_adapter_bridge"]
    assert result["provider_call_succeeded"] is False
    assert result["fallback_used"] is True
    assert result["structured_output_validated"] is False
    assert bridge["external_adapter_failed"] is True
    assert bridge["output_schema_validated"] is False


def test_batch_and_non_jd_inputs_do_not_invoke_external_adapter():
    calls = []
    adapter = lambda request: calls.append(request)
    batch = run_manual_jd_live_provider_canary_command(
        enabled=True,
        job_payloads=[_job(), _job()],
        live_config=_config(),
        external_adapter=adapter,
    )
    tailoring = _config()
    tailoring["agent_name"] = "tailoring_suggestion"
    non_jd = run_manual_jd_live_provider_canary_command(
        enabled=True,
        job_payload=_job(),
        live_config=tailoring,
        external_adapter=adapter,
    )
    critic = _config()
    critic["agent_name"] = "critic_guardrail"
    critic_result = run_manual_jd_live_provider_canary_command(
        enabled=True,
        job_payload=_job(),
        live_config=critic,
        external_adapter=adapter,
    )

    assert calls == []
    assert batch["one_job_only"] is False
    assert non_jd["jd_only"] is False
    assert critic_result["jd_only"] is False


def test_mutation_authority_and_all_influence_remain_disabled():
    bridge = build_jd_live_provider_external_adapter(
        enabled=True,
        live_config=_config(),
        external_adapter=lambda _request: _response(),
    )
    bridge(_request())
    result = bridge.last_result
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


def test_helper_has_no_sdk_env_direct_network_or_storage_wiring():
    source = (
        ROOT / "src/agents/jd_live_provider_external_adapter.py"
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
    ):
        assert marker not in source


def test_api_ui_service_pipeline_and_dependencies_are_unchanged():
    expected = {
        "requirements.txt": ("96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f"),
        "src/app/api.py": ("85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96"),
        "src/app/services.py": ("e86d8305951082be83084c3c4533c70bcd0ea8121da2a6564d862b7eb7b1fbff"),
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
