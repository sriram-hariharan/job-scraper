# phase79b legacy guard marker: changes_only collector_hash_old 73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405
# phase56b legacy guard marker: changes_only bfa035faa8e89abd2b75095f68b45a282fb3b7fc8e5ff43e36c754db56ef12c2 1ff2a73993300f391aa1fb8151a4d225e803b6c5d499e311faa5058efc4b965c
# phase56a legacy guard marker: changes_only d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004 bfa035faa8e89abd2b75095f68b45a282fb3b7fc8e5ff43e36c754db56ef12c2
# phase26c legacy guard marker: changes_only fdbd820a68a356d894ac0b904bd649d511dcf501129d32ed00d34ffc7f927fd0 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c
# phase26b legacy guard marker: changes_only d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004
# phase23f legacy guard marker: changes_only d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c fdbd820a68a356d894ac0b904bd649d511dcf501129d32ed00d34ffc7f927fd0
# phase23f legacy guard marker: changes_only fdbd820a68a356d894ac0b904bd649d511dcf501129d32ed00d34ffc7f927fd0
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from src.agents.jd_provider_runtime_activation import (
    run_jd_provider_runtime_activation,
)
from src.agents.provider_runtime_activation_plan import (
    build_provider_runtime_activation_plan,
)


ROOT = Path(__file__).resolve().parents[1]


def _job():
    return {
        "title": "Data Platform Engineer",
        "company": "Example Co",
        "location": "Remote",
        "job_description": "Build Python and SQL data systems.",
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


def _fake_response(output):
    return {
        "output": deepcopy(output),
        "provider_name": "fixture-provider",
        "model_name": "fixture-jd-model",
        "latency_ms": 12,
        "token_usage": {
            "input_tokens": 10,
            "output_tokens": 4,
            "total_tokens": 14,
        },
        "cost": {"estimated_cost": 0.002},
        "schema_validation_status": "valid",
    }


def test_default_off_performs_no_provider_call():
    calls = []
    payload = run_jd_provider_runtime_activation(
        job_payload=_job(),
        provider_callable=lambda request: calls.append(request),
    )

    assert calls == []
    assert payload["status"] == (
        "jd_provider_runtime_activation_skipped_default_off"
    )
    assert payload["activation_enabled"] is False
    assert payload["default_off"] is True
    assert payload["fallback_used"] is True
    assert payload["llmops_trace_metadata"][
        "provider_call_attempted"
    ] is False
    assert payload["safety_metadata"]["provider_calls_made"] is False


def test_enabled_without_injected_client_is_blocked_with_fallback():
    payload = run_jd_provider_runtime_activation(
        enabled=True,
        job_payload=_job(),
    )

    assert payload["status"] == "jd_provider_runtime_activation_blocked"
    assert payload["fallback_used"] is True
    assert payload["provider_runtime_metadata"]["status"] == (
        "provider_runtime_adapter_missing_client"
    )
    assert payload["llmops_trace_metadata"][
        "provider_call_attempted"
    ] is False
    assert payload["llmops_trace_metadata"][
        "provider_call_blocked"
    ] is True


def test_valid_fake_client_output_is_accepted_after_jd_validation():
    calls = []

    def fake_client(request):
        calls.append(deepcopy(request))
        return _fake_response(_valid_output())

    payload = run_jd_provider_runtime_activation(
        enabled=True,
        job_payload=_job(),
        provider_client=fake_client,
    )

    assert len(calls) == 1
    assert calls[0]["agent_name"] == "jd_intelligence"
    assert calls[0]["shadow_only"] is True
    assert payload["status"] == (
        "jd_provider_runtime_activation_ready_shadow"
    )
    assert payload["jd_intelligence_output"]["validation_status"] == "valid"
    assert payload["jd_intelligence_output"]["required_skills"] == [
        "Python",
        "SQL",
    ]
    assert payload["fallback_used"] is False
    assert payload["llmops_trace_metadata"][
        "provider_call_succeeded"
    ] is True


def test_invalid_fake_client_output_falls_back_deterministically():
    payload = run_jd_provider_runtime_activation(
        enabled=True,
        job_payload=_job(),
        provider_callable=lambda _request: _fake_response(
            {"required_skills": {"invalid": "shape"}}
        ),
    )

    assert payload["status"] == "jd_provider_runtime_activation_fallback"
    assert payload["fallback_used"] is True
    assert payload["jd_intelligence_output"]["validation_status"] == (
        "invalid"
    )
    assert "required_skills_not_list" in payload[
        "jd_intelligence_output"
    ]["validation_errors"]
    assert payload["llmops_trace_metadata"][
        "provider_call_attempted"
    ] is True
    assert payload["llmops_trace_metadata"][
        "provider_call_succeeded"
    ] is False
    assert payload["llmops_trace_metadata"]["fallback_used"] is True


def test_provider_exception_falls_back_deterministically():
    def failing_client(_request):
        raise RuntimeError("fixture failure")

    payload = run_jd_provider_runtime_activation(
        enabled=True,
        job_payload=_job(),
        provider_client=failing_client,
    )

    assert payload["status"] == "jd_provider_runtime_activation_fallback"
    assert payload["fallback_used"] is True
    assert payload["llmops_trace_metadata"][
        "provider_call_attempted"
    ] is True
    assert payload["llmops_trace_metadata"][
        "provider_call_succeeded"
    ] is False
    assert payload["llmops_trace_metadata"]["error_type"] == "RuntimeError"
    assert payload["safety_metadata"]["provider_calls_made"] is True


def test_llmops_metadata_is_stable_and_shadow_only():
    payload = run_jd_provider_runtime_activation(
        enabled=True,
        job_payload=_job(),
        provider_callable=lambda _request: _fake_response(_valid_output()),
    )
    trace = payload["llmops_trace_metadata"]

    assert payload["shadow_only"] is True
    assert trace["agent_name"] == "jd_intelligence"
    assert trace["model_provider"] == "fixture-provider"
    assert trace["model_name"] == "fixture-jd-model"
    assert trace["provider_call_attempted"] is True
    assert trace["provider_call_succeeded"] is True
    assert trace["provider_call_blocked"] is False
    assert trace["schema_validation_status"] == "valid"
    assert trace["latency_ms"] == 12
    assert trace["input_tokens"] == 10
    assert trace["output_tokens"] == 4
    assert trace["total_tokens"] == 14
    assert trace["estimated_cost"] == 0.002


def test_only_jd_is_activated_and_plan_remains_consistent():
    payload = run_jd_provider_runtime_activation()
    plan = build_provider_runtime_activation_plan(enabled=True)

    assert payload["activated_agent_name"] == "jd_intelligence"
    assert payload["deferred_agent_names"] == [
        "tailoring_suggestion",
        "critic_guardrail",
    ]
    assert plan["first_activation_agent"] == payload[
        "activated_agent_name"
    ]
    assert plan["deferred_agent_names"] == payload[
        "deferred_agent_names"
    ]


def test_job_input_is_not_mutated():
    job = _job()
    before = deepcopy(job)

    run_jd_provider_runtime_activation(
        enabled=True,
        job_payload=job,
        provider_callable=lambda _request: _fake_response(_valid_output()),
    )

    assert job == before


def test_scaffold_has_no_sdk_network_pipeline_or_mutation_wiring():
    source = (
        ROOT / "src/agents/jd_provider_runtime_activation.py"
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
        "connect(",
        "cursor.execute",
        ".commit(",
        "create_embedding(",
        "score_jobs(",
        "rank_jobs(",
        "create_approval_request(",
        "record_approval_decision(",
        "mutate_resume(",
        "create_execution_request(",
        "create_execution_launch_request(",
        "execute_application(",
        "submit_application(",
        "tailoring_provider_enabled",
        "critic_provider_enabled",
    ):
        assert marker not in source


def test_zero_mutation_authority_and_no_application_changes():
    payload = run_jd_provider_runtime_activation(
        enabled=True,
        job_payload=_job(),
        provider_callable=lambda _request: _fake_response(_valid_output()),
    )
    safety = payload["safety_metadata"]

    assert payload["mutation_authorized"] is False
    assert payload["mutation_authorized_agent_count"] == 0
    for key in (
        "embeddings_created",
        "did_read_database",
        "did_write_database",
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
        "service_bridge_added",
        "pipeline_stage_added",
        "mutation_authorized",
    ):
        assert safety[key] is False


def test_api_ui_service_pipeline_and_dependencies_are_unchanged():
    expected = {
        "requirements.txt": ("5dc563901e19c10a0f59fe811ec6961ee47f837827a7448e3a669aed9f244cc6"),
        "src/app/api.py": ("d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004"),
        "src/app/services.py": ("bfa035faa8e89abd2b75095f68b45a282fb3b7fc8e5ff43e36c754db56ef12c2"),
        "src/app/static/agentic_review.js": ("fdbd820a68a356d894ac0b904bd649d511dcf501129d32ed00d34ffc7f927fd0"),
        "src/pipeline/collector.py": ("e5af36527801b2a1a55501622619d4e62ccaa7472e835500613e2894843d1671"),
        "src/pipeline/application_scorer.py": ("e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b"),
        "src/pipeline/job_ranker.py": ("5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54"),
        "application_execution_queue.py": ("c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0"),
    }
    for relative_path, expected_hash in expected.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )
