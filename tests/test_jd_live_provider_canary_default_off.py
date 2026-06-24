from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from src.agents.jd_live_provider_canary import (
    run_jd_live_provider_canary,
)


ROOT = Path(__file__).resolve().parents[1]


def _job():
    return {
        "title": "Data Platform Engineer",
        "company": "Example Co",
        "location": "Remote",
        "job_description": "Build Python and SQL data systems.",
        "job_id": "job-13c",
        "context_id": "context-13c",
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
        "preferred_skills": ["Airflow"],
        "required_tools": ["PostgreSQL"],
        "preferred_tools": ["dbt"],
        "workflows": ["data orchestration"],
        "methods": ["data modeling"],
        "business_contexts": ["analytics platform"],
        "stakeholder_contexts": ["data teams"],
        "ownership_signals": ["platform ownership"],
        "seniority_signals": ["senior contributor"],
        "risk_flags": [],
        "extraction_confidence": 0.91,
    }


def _response(output):
    return {
        "output": deepcopy(output),
        "latency_ms": 17,
        "token_usage": {
            "input_tokens": 20,
            "output_tokens": 8,
            "total_tokens": 28,
        },
        "cost": {"estimated_cost": 0.004},
    }


def test_default_and_disabled_config_do_not_call_adapter():
    calls = []
    adapter = lambda request: calls.append(request)

    default = run_jd_live_provider_canary(
        job_payload=_job(),
        provider_adapter=adapter,
    )
    config = _config()
    config["live_canary_enabled"] = False
    disabled = run_jd_live_provider_canary(
        enabled=True,
        job_payload=_job(),
        live_config=config,
        provider_adapter=adapter,
    )

    assert calls == []
    assert default["canary_allowed"] is False
    assert default["canary_attempted"] is False
    assert default["provider_call_attempted"] is False
    assert disabled["canary_allowed"] is False
    assert disabled["provider_call_attempted"] is False


def test_non_jd_tailoring_and_critic_configs_do_not_call_adapter():
    for agent_name in (
        "other_agent",
        "tailoring_suggestion",
        "critic_guardrail",
    ):
        calls = []
        config = _config()
        config["agent_name"] = agent_name

        result = run_jd_live_provider_canary(
            enabled=True,
            job_payload=_job(),
            live_config=config,
            provider_adapter=lambda request: calls.append(request),
        )

        assert calls == []
        assert result["canary_allowed"] is False
        assert result["provider_call_attempted"] is False
        assert result["fallback_used"] is True


def test_missing_injected_adapter_blocks_and_falls_back():
    result = run_jd_live_provider_canary(
        enabled=True,
        job_payload=_job(),
        live_config=_config(),
    )

    assert result["canary_allowed"] is True
    assert result["canary_status"] == "jd_live_canary_blocked"
    assert result["canary_attempted"] is False
    assert result["provider_call_attempted"] is False
    assert result["fallback_used"] is True
    assert result["fallback_reason"] == (
        "missing_injected_provider_adapter"
    )


def test_valid_config_calls_fake_adapter_once_and_validates_output():
    calls = []
    job = _job()
    config = _config()
    job_before = deepcopy(job)
    config_before = deepcopy(config)

    def adapter(request):
        calls.append(deepcopy(request))
        return _response(_valid_output())

    result = run_jd_live_provider_canary(
        enabled=True,
        job_payload=job,
        live_config=config,
        provider_adapter=adapter,
    )

    assert len(calls) == 1
    assert calls[0]["agent_name"] == "jd_intelligence"
    assert calls[0]["shadow_only"] is True
    assert calls[0]["provider_name"] == "approved-provider"
    assert calls[0]["model_name"] == "approved-model"
    assert result["canary_status"] == (
        "jd_live_canary_succeeded_shadow_only"
    )
    assert result["canary_allowed"] is True
    assert result["canary_attempted"] is True
    assert result["provider_call_attempted"] is True
    assert result["provider_call_succeeded"] is True
    assert result["provider_call_failed"] is False
    assert result["structured_output_validated"] is True
    assert result["fallback_used"] is False
    assert result["shadow_only"] is True
    assert result["jd_intelligence_output"]["validation_status"] == "valid"
    assert result["jd_intelligence_output"]["required_skills"] == [
        "Python",
        "SQL",
    ]
    assert job == job_before
    assert config == config_before


def test_invalid_adapter_output_falls_back_deterministically():
    fallback = {"required_skills": ["fallback-python"]}
    result = run_jd_live_provider_canary(
        enabled=True,
        job_payload=_job(),
        live_config=_config(),
        provider_adapter=lambda _request: _response(
            {"required_skills": {"invalid": "shape"}}
        ),
        deterministic_fallback_input=fallback,
    )

    assert result["canary_status"] == "jd_live_canary_fallback"
    assert result["provider_call_attempted"] is True
    assert result["provider_call_succeeded"] is False
    assert result["provider_call_failed"] is True
    assert result["structured_output_validated"] is False
    assert result["fallback_used"] is True
    assert result["fallback_reason"] == "required_skills_not_list"
    assert result["jd_intelligence_output"]["required_skills"] == [
        "fallback-python"
    ]


def test_adapter_exception_falls_back_deterministically():
    def failing_adapter(_request):
        raise RuntimeError("fixture failure")

    result = run_jd_live_provider_canary(
        enabled=True,
        job_payload=_job(),
        live_config=_config(),
        provider_adapter=failing_adapter,
    )

    assert result["canary_status"] == "jd_live_canary_fallback"
    assert result["canary_attempted"] is True
    assert result["provider_call_attempted"] is True
    assert result["provider_call_succeeded"] is False
    assert result["provider_call_failed"] is True
    assert result["fallback_used"] is True
    assert result["fallback_reason"] == (
        "provider_adapter_error:RuntimeError"
    )
    assert result["llmops_metadata"]["error_type"] == "RuntimeError"


def test_adapter_usage_over_configured_budget_falls_back():
    response = _response(_valid_output())
    response["cost"] = {"estimated_cost": 0.3}

    result = run_jd_live_provider_canary(
        enabled=True,
        job_payload=_job(),
        live_config=_config(),
        provider_adapter=lambda _request: response,
    )

    assert result["canary_status"] == "jd_live_canary_fallback"
    assert result["provider_call_attempted"] is True
    assert result["provider_call_succeeded"] is False
    assert result["provider_call_failed"] is True
    assert result["fallback_reason"] == "provider_cost_budget_exceeded"
    assert result["llmops_metadata"]["error_type"] == (
        "BudgetLimitExceeded"
    )


def test_llmops_metadata_is_emitted_for_valid_shadow_canary():
    result = run_jd_live_provider_canary(
        enabled=True,
        job_payload=_job(),
        live_config=_config(),
        provider_adapter=lambda _request: _response(_valid_output()),
    )
    trace = result["llmops_metadata"]

    assert trace["agent_name"] == "jd_intelligence"
    assert trace["prompt_version"] == "jd-live-canary-prompt-v1"
    assert trace["runtime_version"] == "jd-live-canary-runtime-v1"
    assert trace["model_provider"] == "approved-provider"
    assert trace["model_name"] == "approved-model"
    assert trace["provider_call_attempted"] is True
    assert trace["provider_call_succeeded"] is True
    assert trace["schema_validation_status"] == "valid"
    assert trace["latency_ms"] == 17
    assert trace["input_tokens"] == 20
    assert trace["output_tokens"] == 8
    assert trace["total_tokens"] == 28
    assert trace["estimated_cost"] == 0.004
    assert trace["fallback_used"] is False


def test_mutation_authority_and_all_application_influence_remain_zero():
    result = run_jd_live_provider_canary(
        enabled=True,
        job_payload=_job(),
        live_config=_config(),
        provider_adapter=lambda _request: _response(_valid_output()),
    )
    safety = result["safety_metadata"]

    assert result["activated_agent_name"] == "jd_intelligence"
    assert result["deferred_agent_names"] == [
        "tailoring_suggestion",
        "critic_guardrail",
    ]
    assert result["mutation_authorized"] is False
    assert result["mutation_authorized_agent_count"] == 0
    for key in (
        "embeddings_created",
        "did_read_database",
        "did_write_database",
        "did_write_files",
        "did_mutate_scoring",
        "did_change_ranking",
        "did_mutate_queue",
        "did_create_approval",
        "did_mutate_approval",
        "did_mutate_resume",
        "did_write_resume_draft",
        "did_write_cover_letter_draft",
        "did_create_execution_request",
        "did_create_execution_launch_request",
        "did_execute_application",
        "did_submit_application",
        "api_route_added",
        "ui_action_added",
        "service_behavior_added",
        "pipeline_stage_added",
        "mutation_authorized",
    ):
        assert safety[key] is False


def test_helper_has_no_sdk_env_direct_network_client_or_storage_wiring():
    source = (
        ROOT / "src/agents/jd_live_provider_canary.py"
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
        "provider_client(",
        "provider_client.invoke(",
        "database_url",
        "connect(",
        "cursor.execute",
        ".commit(",
        "open(",
        "write_text(",
        "write_bytes(",
        "create_embedding(",
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
        "requirements.txt": (
            "96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f"
        ),
        "src/app/api.py": (
            "8ab44f7e97113f6d28e9a8f7d032affef2e1f8f891286986d9e95d581ff97fbf"
        ),
        "src/app/services.py": (
            "2c67ab4d78299de8e54db6ef76ea77598f7e98c1d2f516df97cea4c014e7b6ee"
        ),
        "src/app/static/agentic_review.js": (
            "241609825c31c047255ba6e439cf728e1758966f506bae014240ac55fd701e16"
        ),
        "src/pipeline/collector.py": (
            "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405"
        ),
        "src/pipeline/application_scorer.py": (
            "e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b"
        ),
        "src/pipeline/job_ranker.py": (
            "5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54"
        ),
        "application_execution_queue.py": (
            "c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0"
        ),
    }

    for relative_path, expected_hash in expected.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )
