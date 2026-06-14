from copy import deepcopy
from pathlib import Path

from src.agents.jd_intelligence import build_live_jd_intelligence_dry_run_payload


def _job_input() -> dict:
    return {
        "job_title": "Senior Data Platform Engineer",
        "company": "ExampleCo",
        "location": "Remote",
        "job_description": "Own Python data workflows with Airflow, dbt, and stakeholder reporting.",
        "source_metadata": {
            "source": "manual_fixture",
            "nested": {"job_url": "https://example.test/jobs/123"},
        },
        "context_id": "ctx-123",
        "job_id": "job-123",
    }


def _valid_adapter_payload() -> dict:
    return {
        "required_skills": ["Python", "SQL"],
        "preferred_skills": ["Data modeling"],
        "required_tools": ["Airflow"],
        "preferred_tools": ["dbt"],
        "workflows": ["Data pipeline ownership"],
        "methods": ["Stakeholder reporting"],
        "business_contexts": ["Analytics platform"],
        "stakeholder_contexts": ["Product and finance teams"],
        "ownership_signals": ["Own production workflows"],
        "seniority_signals": ["Senior IC scope"],
        "risk_flags": ["ambiguous on-call expectations"],
        "extraction_confidence": 0.82,
        "model_provider": "fake-provider",
        "model_name": "fake-jd-model",
        "prompt_version": "fake-prompt-v1",
        "token_usage": {"input_token_count": 10, "output_token_count": 20},
        "cost": {"estimated_cost": 0.0, "cost_currency": ""},
        "latency_ms": 42,
    }


def _assert_no_runtime_mutation(payload: dict, *, did_call_llm: bool) -> None:
    safety = payload["safety_metadata"]
    assert safety["dry_run_only"] is True
    assert safety["feature_flag_required"] is True
    assert safety["did_call_llm"] is did_call_llm
    assert safety["did_mutate_scoring"] is False
    assert safety["did_change_ranking"] is False
    assert safety["did_mutate_queue"] is False
    assert safety["did_mutate_approval"] is False
    assert safety["did_execute_application"] is False
    assert safety["did_submit_application"] is False
    assert safety["pipeline_wiring_added"] is False


def test_feature_flag_off_returns_disabled_fallback_without_calling_adapter():
    calls = []

    def adapter(payload):
        calls.append(payload)
        return _valid_adapter_payload()

    payload = build_live_jd_intelligence_dry_run_payload(
        **_job_input(),
        adapter=adapter,
        feature_enabled=False,
    )

    assert calls == []
    assert payload["validation_status"] == "disabled"
    assert payload["fallback_used"] is True
    assert payload["validation_errors"] == ["feature_flag_disabled"]
    assert payload["required_skills"] == []
    _assert_no_runtime_mutation(payload, did_call_llm=False)


def test_missing_adapter_returns_fallback_without_llm_call():
    payload = build_live_jd_intelligence_dry_run_payload(
        **_job_input(),
        feature_enabled=True,
    )

    assert payload["validation_status"] == "fallback"
    assert payload["fallback_used"] is True
    assert payload["validation_errors"] == ["adapter_missing"]
    _assert_no_runtime_mutation(payload, did_call_llm=False)


def test_fake_adapter_valid_dict_returns_validated_jd_intelligence():
    seen_inputs = []

    def adapter(payload):
        seen_inputs.append(payload)
        payload["source_metadata"]["nested"]["job_url"] = "mutated-inside-adapter"
        return _valid_adapter_payload()

    original = _job_input()
    before = deepcopy(original)
    payload = build_live_jd_intelligence_dry_run_payload(
        **original,
        adapter=adapter,
        feature_enabled=True,
    )

    assert original == before
    assert seen_inputs[0]["job_title"] == "Senior Data Platform Engineer"
    assert seen_inputs[0]["prompt_version"] == "live-jd-intelligence-dry-run-v1"
    assert payload["validation_status"] == "valid"
    assert payload["validation_errors"] == []
    assert payload["fallback_used"] is False
    assert payload["required_skills"] == ["Python", "SQL"]
    assert payload["preferred_tools"] == ["dbt"]
    assert payload["seniority_signals"] == ["Senior IC scope"]
    assert payload["extraction_confidence"] == 0.82
    assert payload["model_provider"] == "fake-provider"
    assert payload["model_name"] == "fake-jd-model"
    assert payload["prompt_version"] == "fake-prompt-v1"
    assert payload["token_usage"] == {"input_token_count": 10, "output_token_count": 20}
    assert payload["cost"] == {"estimated_cost": 0.0, "cost_currency": ""}
    assert payload["latency_ms"] == 42
    _assert_no_runtime_mutation(payload, did_call_llm=True)


def test_fake_adapter_valid_json_string_returns_validated_jd_intelligence():
    def adapter(_payload):
        return """
        {
          "required_skills": ["Python"],
          "seniority_indicators": ["Lead-like ownership"],
          "extraction_confidence": "0.7",
          "provider": "fake-provider",
          "model": "fake-json-model",
          "token_usage_json": {"total_token_count": 12},
          "cost_json": {"estimated_cost": 0}
        }
        """

    first = build_live_jd_intelligence_dry_run_payload(
        **_job_input(),
        adapter=adapter,
        config={"enabled": True},
    )
    second = build_live_jd_intelligence_dry_run_payload(
        **_job_input(),
        adapter=adapter,
        config={"enabled": True},
    )

    assert first == second
    assert first["validation_status"] == "valid"
    assert first["required_skills"] == ["Python"]
    assert first["seniority_signals"] == ["Lead-like ownership"]
    assert first["model_provider"] == "fake-provider"
    assert first["model_name"] == "fake-json-model"
    assert first["token_usage"] == {"total_token_count": 12}
    _assert_no_runtime_mutation(first, did_call_llm=True)


def test_fake_adapter_invalid_json_returns_fallback_with_validation_error():
    payload = build_live_jd_intelligence_dry_run_payload(
        **_job_input(),
        adapter=lambda _payload: "{not json",
        feature_enabled=True,
    )

    assert payload["validation_status"] == "fallback"
    assert payload["fallback_used"] is True
    assert payload["validation_errors"] == ["invalid_json_response"]
    assert payload["required_tools"] == []
    _assert_no_runtime_mutation(payload, did_call_llm=True)


def test_fake_adapter_exception_returns_fallback_with_adapter_error():
    def adapter(_payload):
        raise RuntimeError("provider offline")

    payload = build_live_jd_intelligence_dry_run_payload(
        **_job_input(),
        adapter=adapter,
        feature_enabled=True,
    )

    assert payload["validation_status"] == "fallback"
    assert payload["fallback_used"] is True
    assert payload["validation_errors"] == ["adapter_error:RuntimeError"]
    _assert_no_runtime_mutation(payload, did_call_llm=True)


def test_dry_run_helper_source_has_no_pipeline_storage_network_or_real_llm_calls():
    source = Path("src/agents/jd_intelligence.py").read_text()
    helper_source = source[source.index("def build_live_jd_intelligence_dry_run_payload") :]

    forbidden_tokens = [
        "run_chat_completion",
        "src.ai.llm_client",
        "requests.",
        "httpx.",
        "psycopg",
        "create_agent_run(",
        "record_agent_step(",
        "complete_agent_run(",
        "score_resume_job_match",
        "rank_",
        "approval_store",
        "execute_application",
        "submit_application",
        "workflow_runner",
        "pipeline.",
    ]
    for token in forbidden_tokens:
        assert token not in helper_source
