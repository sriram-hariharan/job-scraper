import hashlib
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
        "run_id": "run-phase-9k",
        "batch_id": "batch-phase-9k",
        "job_id": "job-phase-9k",
        "stage_name": "post_final_scoring",
        "source_deterministic_stage": "application_priority",
        "source_deterministic_status": "completed",
        "source_deterministic_score": 0.9,
        "source_deterministic_decision": "qualified_for_review",
        "three_agent_shadow_workflow_enabled": True,
    }
    kwargs.update(updates)
    return shadow_sidecar_hook.run_shadow_sidecar_pipeline_hook(**kwargs)


def _assert_trace_shape(trace, agent_name, latency):
    assert trace["agent_name"] == agent_name
    assert trace["agent_version"]
    assert trace["prompt_version"]
    assert trace["model_provider"] == ""
    assert trace["model_name"] == ""
    assert trace["input_tokens"] == 0
    assert trace["output_tokens"] == 0
    assert trace["estimated_cost"] == 0
    assert trace["latency_ms"] == latency
    assert trace["retry_count"] == 0
    assert isinstance(trace["fallback_used"], bool)
    assert trace["schema_validation_status"]
    assert trace["error_type"] == ""
    assert trace["provider_call_made"] is False


def _assert_safety(safety):
    assert safety["llmops_trace_contract_enabled"] is True
    assert safety["provider_calls_made"] is False
    assert safety["token_usage_recorded"] is True
    assert safety["cost_recorded"] is True
    assert safety["latency_recorded"] is True
    assert safety["did_write_database"] is False
    assert safety["did_mutate_scoring"] is False
    assert safety["did_change_ranking"] is False
    assert safety["did_mutate_queue"] is False
    assert safety["did_create_approval"] is False
    assert safety["did_mutate_resume"] is False
    assert safety["did_execute_application"] is False
    assert safety["did_submit_application"] is False


def test_default_off_does_not_add_llmops_trace_metadata():
    payload = _run()
    chain = payload["chain_payload"]

    assert "three_agent_llmops_trace_contract" not in chain
    for result in chain["ordered_agent_results"]:
        assert "llmops_trace_metadata" not in result


def test_enabled_contract_adds_stable_metadata_to_exactly_three_agents():
    payload = _run(llmops_trace_contract_enabled=True)
    chain = payload["chain_payload"]
    results = chain["ordered_agent_results"]

    assert [result["agent_name"] for result in results] == ORDERED_AGENTS
    assert len(results) == 3
    for result in results:
        _assert_trace_shape(
            result["llmops_trace_metadata"],
            result["agent_name"],
            0,
        )
        _assert_safety(result["safety_metadata"])

    contract = chain["three_agent_llmops_trace_contract"]
    assert contract["ordered_agent_count"] == 3
    assert contract["ordered_agent_names"] == ORDERED_AGENTS
    assert len(contract["agent_traces"]) == 3
    _assert_safety(contract["safety_metadata"])


def test_caller_supplied_latency_and_metadata_are_deterministic():
    metadata = {
        "jd_intelligence": {
            "latency_ms": 11,
            "agent_version": "jd-fixture-v1",
            "prompt_version": "jd-prompt-fixture-v1",
        },
        "tailoring_suggestion": {"latency_ms": 22},
        "critic_guardrail": {"latency_ms": 33},
    }
    payload = _run(
        llmops_trace_contract_enabled=True,
        llmops_trace_metadata_by_agent=metadata,
    )
    traces = {
        result["agent_name"]: result["llmops_trace_metadata"]
        for result in payload["chain_payload"]["ordered_agent_results"]
    }

    assert traces["jd_intelligence"]["latency_ms"] == 11
    assert traces["jd_intelligence"]["agent_version"] == "jd-fixture-v1"
    assert traces["jd_intelligence"]["prompt_version"] == (
        "jd-prompt-fixture-v1"
    )
    assert traces["tailoring_suggestion"]["latency_ms"] == 22
    assert traces["critic_guardrail"]["latency_ms"] == 33


def test_retry_fallback_validation_token_and_cost_fields_are_stable():
    payload = _run(llmops_trace_contract_enabled=True)

    for result in payload["chain_payload"]["ordered_agent_results"]:
        trace = result["llmops_trace_metadata"]
        for field in (
            "input_tokens",
            "output_tokens",
            "total_token_count",
            "estimated_cost",
            "retry_count",
            "fallback_used",
            "schema_validation_status",
            "error_type",
            "provider_call_made",
        ):
            assert field in trace


def test_review_packet_includes_existing_trace_contract_summary():
    hook = _run(llmops_trace_contract_enabled=True)
    packet = pipeline_agent_review_packet.build_pipeline_agent_review_packet_payload(
        hook_payload=hook
    )

    contract = packet["three_agent_llmops_trace_contract"]
    assert contract["ordered_agent_names"] == ORDERED_AGENTS
    assert len(contract["agent_traces"]) == 3
    _assert_safety(contract["safety_metadata"])


def test_zero_agent_authorization_and_no_external_or_mutation_wiring():
    hook = _run(llmops_trace_contract_enabled=True)
    packet = pipeline_agent_review_packet.build_pipeline_agent_review_packet_payload(
        hook_payload=hook
    )
    assert packet["live_provider_backed_automated_agents"] == 0
    assert packet["mutation_authorized_agents"] == 0

    sources = "\n".join(
        (ROOT / path).read_text(encoding="utf-8")
        for path in (
            "src/agents/agent_llmops_trace_contract.py",
            "src/agents/shadow_sidecar_hook.py",
            "src/agents/pipeline_agent_review_packet.py",
        )
    ).lower()
    for marker in (
        "openai",
        "anthropic",
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


def test_api_ui_pipeline_dependencies_and_decision_modules_are_unchanged():
    expected = {
        "requirements.txt": "96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f",
        "src/app/api.py": "ba752c3a7eaef620476abffb0ecb7ebf8ce023346917ff8fedb5579c9504d41f",
        "src/app/static/agentic_review.js": "98ab760d0cd9e0d6aef757d604a84709b28b3c21ddcfe1d8e18a1c9f8685881e",
        "src/pipeline/collector.py": "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405",
        "src/pipeline/application_scorer.py": "e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b",
        "src/pipeline/job_ranker.py": "5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54",
    }
    for relative_path, expected_hash in expected.items():
        assert hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )
