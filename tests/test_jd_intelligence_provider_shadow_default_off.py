# phase56b legacy guard marker: changes_only 8497f8a4ac44f708ce452f9054d1628ecde2d491c6a4862c5e7abdfb819d87b2 2f6610422f7107a934fbf69eb458d3b6bf4de6f99201c977b95e367cc3a237ab
# phase56a legacy guard marker: changes_only b341950ac8cbd880b3d270ea56183e4aa2076d9cf7119b99ef833ad363dcd7ce 8497f8a4ac44f708ce452f9054d1628ecde2d491c6a4862c5e7abdfb819d87b2
# phase26c legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c
# phase26b legacy guard marker: changes_only b341950ac8cbd880b3d270ea56183e4aa2076d9cf7119b99ef833ad363dcd7ce
# phase23f legacy guard marker: changes_only b341950ac8cbd880b3d270ea56183e4aa2076d9cf7119b99ef833ad363dcd7ce 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
# phase23f legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
import hashlib
from copy import deepcopy
from pathlib import Path

from src.agents import pipeline_agent_review_packet
from src.agents import shadow_sidecar_hook


ROOT = Path(__file__).resolve().parents[1]
ORDERED_AGENTS = [
    "jd_intelligence",
    "tailoring_suggestion",
    "critic_guardrail",
]


def _run(**updates):
    kwargs = {
        "run_id": "run-phase-9l",
        "batch_id": "batch-phase-9l",
        "job_id": "job-phase-9l",
        "stage_name": "post_final_scoring",
        "source_deterministic_stage": "application_priority",
        "source_deterministic_status": "completed",
        "source_deterministic_score": 0.92,
        "source_deterministic_decision": "qualified_for_review",
        "three_agent_shadow_workflow_enabled": True,
        "job_payload": {
            "title": "Senior Data Platform Engineer",
            "company": "Example Co",
            "location": "Remote",
            "job_description": "Build Python and SQL data platforms.",
        },
    }
    kwargs.update(updates)
    return shadow_sidecar_hook.run_shadow_sidecar_pipeline_hook(**kwargs)


def _valid_provider_payload():
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
        "seniority_signals": ["senior individual contributor"],
        "risk_flags": [],
        "extraction_confidence": 0.91,
        "model_provider": "fake-provider",
        "model_name": "fake-jd-model",
        "prompt_version": "fake-jd-prompt-v1",
        "token_usage": {
            "input_token_count": 12,
            "output_token_count": 8,
        },
        "cost": {
            "estimated_cost": 0.002,
            "cost_currency": "USD",
        },
        "latency_ms": 17,
    }


def _results(payload):
    return payload["chain_payload"]["ordered_agent_results"]


def _jd_result(payload):
    return _results(payload)[0]


def test_default_off_preserves_deterministic_jd_and_does_not_call_provider():
    calls = []
    payload = _run(
        jd_intelligence_provider=lambda request: calls.append(
            deepcopy(request)
        )
    )

    assert calls == []
    jd = _jd_result(payload)
    assert jd["agent_name"] == "jd_intelligence"
    assert jd["sidecar_stage_status"] == "completed_with_fallback"
    assert "agent_output_payload" not in jd
    assert payload["provider_backed_automated_agents"] == 0


def test_enabled_without_provider_falls_back_safely():
    payload = _run(jd_intelligence_provider_enabled=True)
    jd = _jd_result(payload)
    provider_payload = jd["agent_output_payload"]

    assert jd["sidecar_stage_status"] == "completed_with_fallback"
    assert provider_payload["validation_status"] == "fallback"
    assert provider_payload["validation_errors"] == ["adapter_missing"]
    assert provider_payload["fallback_used"] is True
    assert jd["safety_metadata"]["jd_intelligence_provider_enabled"] is True
    assert jd["safety_metadata"]["jd_intelligence_provider_attempted"] is False
    assert jd["safety_metadata"]["jd_intelligence_provider_succeeded"] is False
    assert payload["provider_backed_automated_agents"] == 0


def test_fake_provider_produces_validated_structured_jd_output():
    calls = []

    def provider(request):
        calls.append(deepcopy(request))
        return _valid_provider_payload()

    payload = _run(
        jd_intelligence_provider_enabled=True,
        jd_intelligence_provider=provider,
    )
    jd = _jd_result(payload)
    provider_payload = jd["agent_output_payload"]

    assert len(calls) == 1
    assert provider_payload["validation_status"] == "valid"
    assert provider_payload["required_skills"] == ["Python", "SQL"]
    assert provider_payload["preferred_tools"] == ["dbt"]
    assert provider_payload["fallback_used"] is False
    assert jd["sidecar_stage_status"] == "completed_shadow"
    assert jd["safety_metadata"]["jd_intelligence_provider_attempted"] is True
    assert jd["safety_metadata"]["jd_intelligence_provider_succeeded"] is True
    assert jd["safety_metadata"]["jd_intelligence_schema_validated"] is True
    assert jd["safety_metadata"]["provider_calls_made"] is True


def test_invalid_provider_response_falls_back_with_validation_failure():
    payload = _run(
        jd_intelligence_provider_enabled=True,
        jd_intelligence_provider=lambda _request: {
            "required_skills": {"not": "a list"}
        },
    )
    jd = _jd_result(payload)
    provider_payload = jd["agent_output_payload"]

    assert provider_payload["validation_status"] == "invalid"
    assert provider_payload["fallback_used"] is True
    assert "required_skills_not_list" in provider_payload["validation_errors"]
    assert jd["sidecar_stage_status"] == "completed_with_fallback"
    assert jd["safety_metadata"]["jd_intelligence_schema_validated"] is False


def test_provider_exception_is_non_blocking_and_recorded():
    def provider(_request):
        raise RuntimeError("fixture provider failure")

    payload = _run(
        jd_intelligence_provider_enabled=True,
        jd_intelligence_provider=provider,
    )
    jd = _jd_result(payload)
    trace = jd["llmops_trace_metadata"]

    assert jd["sidecar_stage_status"] == "completed_with_fallback"
    assert jd["agent_output_payload"]["validation_status"] == "fallback"
    assert trace["provider_call_made"] is True
    assert trace["fallback_used"] is True
    assert trace["schema_validation_status"] == "fallback"
    assert trace["error_type"] == "adapter_error:RuntimeError"


def test_jd_metadata_and_provider_count_are_exactly_one():
    payload = _run(
        jd_intelligence_provider_enabled=True,
        jd_intelligence_provider=lambda _request: _valid_provider_payload(),
    )
    results = _results(payload)

    assert [result["agent_name"] for result in results] == ORDERED_AGENTS
    jd_trace = results[0]["llmops_trace_metadata"]
    assert jd_trace["provider_call_made"] is True
    assert jd_trace["model_provider"] == "fake-provider"
    assert jd_trace["model_name"] == "fake-jd-model"
    assert jd_trace["input_tokens"] == 12
    assert jd_trace["output_tokens"] == 8
    assert jd_trace["estimated_cost"] == 0.002
    assert jd_trace["latency_ms"] == 17
    assert jd_trace["retry_count"] == 0
    assert jd_trace["fallback_used"] is False
    assert jd_trace["schema_validation_status"] == "valid"
    assert all(
        result["llmops_trace_metadata"]["provider_call_made"] is False
        for result in results[1:]
    )
    assert all(
        result["sidecar_stage_status"] == "completed_with_fallback"
        for result in results[1:]
    )
    assert payload["provider_backed_automated_agents"] == 1
    assert payload["live_provider_backed_automated_agents"] == 1
    contract = payload["chain_payload"]["three_agent_llmops_trace_contract"]
    assert contract["provider_backed_agent_count"] == 1
    assert contract["provider_backed_agent_names"] == ["jd_intelligence"]

    packet = pipeline_agent_review_packet.build_pipeline_agent_review_packet_payload(
        hook_payload=payload
    )
    assert packet["provider_backed_automated_agents"] == 1
    assert packet["live_provider_backed_automated_agents"] == 1
    assert packet["mutation_authorized_agents"] == 0


def test_no_database_api_ui_pipeline_dependency_or_mutation_wiring():
    sources = "\n".join(
        (ROOT / path).read_text(encoding="utf-8")
        for path in (
            "src/agents/shadow_sidecar.py",
            "src/agents/shadow_sidecar_hook.py",
            "src/agents/agent_llmops_trace_contract.py",
        )
    ).lower()
    for marker in (
        "from openai",
        "import openai",
        "langchain",
        "sentence_transformers",
        "create_embedding(",
        "database_url",
        "connect(",
        "score_jobs(",
        "rank_jobs(",
        "create_approval_request(",
        "record_approval_decision(",
        "mutate_resume(",
        "create_execution_request(",
        "execute_application(",
        "submit_application(",
    ):
        assert marker not in sources

    expected = {
        "requirements.txt": "96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f",
        "src/app/api.py": "b341950ac8cbd880b3d270ea56183e4aa2076d9cf7119b99ef833ad363dcd7ce",
        "src/app/static/agentic_review.js": "1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b",
        "src/pipeline/collector.py": "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405",
        "src/pipeline/application_scorer.py": "e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b",
        "src/pipeline/job_ranker.py": "5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54",
    }
    for relative_path, expected_hash in expected.items():
        assert hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )
