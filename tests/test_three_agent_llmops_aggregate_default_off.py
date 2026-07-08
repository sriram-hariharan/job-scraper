# phase79b legacy guard marker: changes_only collector_hash_old 73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405
# phase56b legacy guard marker: changes_only e30180b352ebe8abca2ec34b4b34983fbaee61a32bdc0d511001c406703e392c 1ff2a73993300f391aa1fb8151a4d225e803b6c5d499e311faa5058efc4b965c
# phase56a legacy guard marker: changes_only 85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96 e30180b352ebe8abca2ec34b4b34983fbaee61a32bdc0d511001c406703e392c
# phase26c legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c
# phase26b legacy guard marker: changes_only 85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96
# phase23f legacy guard marker: changes_only 85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
# phase23f legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
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
        "run_id": "run-phase-9p",
        "batch_id": "batch-phase-9p",
        "job_id": "job-phase-9p",
        "stage_name": "post_final_scoring",
        "source_deterministic_stage": "application_priority",
        "source_deterministic_status": "completed",
        "source_deterministic_score": 0.91,
        "source_deterministic_decision": "qualified_for_review",
        "three_agent_shadow_workflow_enabled": True,
    }
    kwargs.update(updates)
    return shadow_sidecar_hook.run_shadow_sidecar_pipeline_hook(**kwargs)


def _metadata():
    return {
        "jd_intelligence": {
            "input_tokens": 10,
            "output_tokens": 4,
            "estimated_cost": 0.001,
            "latency_ms": 11,
            "provider_call_made": True,
            "fallback_used": False,
            "schema_validation_status": "valid",
        },
        "tailoring_suggestion": {
            "input_tokens": 20,
            "output_tokens": 6,
            "estimated_cost": 0.002,
            "latency_ms": 22,
            "provider_call_made": True,
            "fallback_used": True,
            "schema_validation_status": "fallback",
        },
        "critic_guardrail": {
            "input_tokens": 30,
            "output_tokens": 8,
            "estimated_cost": 0.003,
            "latency_ms": 33,
            "provider_call_made": True,
            "fallback_used": False,
            "schema_validation_status": "valid",
        },
    }


def test_default_off_does_not_attach_aggregate_metrics():
    chain = _run(llmops_trace_contract_enabled=True)["chain_payload"]

    assert "three_agent_llmops_aggregate" not in chain


def test_enabled_aggregate_summarizes_exactly_three_ordered_agents():
    chain = _run(
        llmops_aggregate_enabled=True,
        llmops_trace_metadata_by_agent=_metadata(),
    )["chain_payload"]
    aggregate = chain["three_agent_llmops_aggregate"]

    assert aggregate["agent_count"] == 3
    assert aggregate["agent_names"] == ORDERED_AGENTS
    assert aggregate["aggregate_status"] == "aggregate_complete"
    assert aggregate["llmops_aggregate_enabled"] is True
    assert aggregate["llmops_aggregate_recorded"] is True


def test_token_cost_and_latency_totals_are_deterministic():
    aggregate = _run(
        llmops_aggregate_enabled=True,
        llmops_trace_metadata_by_agent=_metadata(),
    )["chain_payload"]["three_agent_llmops_aggregate"]

    assert aggregate["total_input_tokens"] == 60
    assert aggregate["total_output_tokens"] == 18
    assert aggregate["total_tokens"] == 78
    assert aggregate["total_estimated_cost"] == 0.006
    assert aggregate["total_latency_ms"] == 66
    assert aggregate["max_agent_latency_ms"] == 33


def test_provider_fallback_and_schema_counts_are_deterministic():
    aggregate = _run(
        llmops_aggregate_enabled=True,
        llmops_trace_metadata_by_agent=_metadata(),
    )["chain_payload"]["three_agent_llmops_aggregate"]

    assert aggregate["provider_call_count"] == 3
    assert aggregate["provider_calls_made"] is True
    assert aggregate["fallback_count"] == 1
    assert aggregate["schema_valid_count"] == 2
    assert aggregate["schema_invalid_count"] == 1


def test_review_packet_exposes_existing_chain_aggregate():
    hook = _run(
        llmops_aggregate_enabled=True,
        llmops_trace_metadata_by_agent=_metadata(),
    )
    packet = (
        pipeline_agent_review_packet.build_pipeline_agent_review_packet_payload(
            hook_payload=hook
        )
    )

    assert packet["three_agent_llmops_aggregate"] == (
        hook["chain_payload"]["three_agent_llmops_aggregate"]
    )
    assert packet["provider_backed_automated_agents"] == 3
    assert packet["mutation_authorized_agents"] == 0


def test_aggregate_is_advisory_and_does_not_add_external_or_mutation_wiring():
    aggregate = _run(
        llmops_aggregate_enabled=True,
        llmops_trace_metadata_by_agent=_metadata(),
    )["chain_payload"]["three_agent_llmops_aggregate"]
    safety = aggregate["safety_metadata"]

    assert safety["read_only"] is True
    assert safety["advisory_only"] is True
    assert safety["provider_calls_made"] is True
    assert safety["embeddings_created"] is False
    assert safety["did_write_database"] is False
    assert safety["did_mutate_scoring"] is False
    assert safety["did_change_ranking"] is False
    assert safety["did_mutate_queue"] is False
    assert safety["did_create_approval"] is False
    assert safety["did_mutate_resume"] is False
    assert safety["did_execute_application"] is False
    assert safety["did_submit_application"] is False

    source = (ROOT / "src/agents/three_agent_llmops_aggregate.py").read_text(
        encoding="utf-8"
    ).lower()
    for marker in (
        "openai",
        "anthropic",
        "langchain",
        "create_embedding(",
        "database_url",
        "connect(",
        "score_jobs(",
        "rank_jobs(",
        "create_approval_request(",
        "mutate_resume(",
        "create_execution_request(",
        "execute_application(",
        "submit_application(",
    ):
        assert marker not in source


def test_api_ui_pipeline_dependencies_and_decision_modules_are_unchanged():
    expected = {
        "requirements.txt": "96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f",
        "src/app/api.py": "85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96",
        "src/app/static/agentic_review.js": "1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b",
        "src/pipeline/collector.py": "71b2ca0b50320688c2ed10396dfbffe952e7ed326fc745955eb1fb8010850a50",
        "src/pipeline/application_scorer.py": "e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b",
        "src/pipeline/job_ranker.py": "5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54",
    }
    for relative_path, expected_hash in expected.items():
        assert hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )
