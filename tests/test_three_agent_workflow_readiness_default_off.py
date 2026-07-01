# phase56b legacy guard marker: changes_only 5c951b6b6b06b47caa9c7874b94f0f8e968de487817ef4bdceb745c225517386 992b95259e278a6dd0f9b8d37be916ece433b562529fc2d3ff0d683d8f9cc25e
# phase56a legacy guard marker: changes_only a52216e4920bc866d09f8899c12b3a1e8b2dd86a92d9e366d383db09f9e10a32 5c951b6b6b06b47caa9c7874b94f0f8e968de487817ef4bdceb745c225517386
# phase26c legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c
# phase26b legacy guard marker: changes_only a52216e4920bc866d09f8899c12b3a1e8b2dd86a92d9e366d383db09f9e10a32
# phase23f legacy guard marker: changes_only a52216e4920bc866d09f8899c12b3a1e8b2dd86a92d9e366d383db09f9e10a32 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
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


def _provider_trace_metadata():
    return {
        agent_name: {
            "provider_call_made": True,
            "schema_validation_status": "valid",
            "input_tokens": index + 1,
            "output_tokens": index + 2,
            "estimated_cost": 0.001 * (index + 1),
            "latency_ms": 10 * (index + 1),
        }
        for index, agent_name in enumerate(ORDERED_AGENTS)
    }


def _run(**updates):
    kwargs = {
        "run_id": "run-phase-9q",
        "batch_id": "batch-phase-9q",
        "job_id": "job-phase-9q",
        "stage_name": "post_final_scoring",
        "source_deterministic_stage": "application_priority",
        "source_deterministic_status": "completed",
        "source_deterministic_score": 0.94,
        "source_deterministic_decision": "qualified_for_review",
        "three_agent_shadow_workflow_enabled": True,
        "provider_handoff_enabled": True,
        "llmops_aggregate_enabled": True,
        "llmops_trace_metadata_by_agent": _provider_trace_metadata(),
    }
    kwargs.update(updates)
    return shadow_sidecar_hook.run_shadow_sidecar_pipeline_hook(**kwargs)


def test_default_off_does_not_attach_readiness_summary():
    chain = _run()["chain_payload"]

    assert "three_agent_workflow_readiness" not in chain


def test_enabled_summary_reports_three_provider_backed_agents():
    summary = _run(
        workflow_readiness_enabled=True
    )["chain_payload"]["three_agent_workflow_readiness"]

    assert summary["readiness_status"] == (
        "ready_shadow_provider_workflow"
    )
    assert summary["ordered_agent_count"] == 3
    assert summary["ordered_agent_names"] == ORDERED_AGENTS
    assert summary["provider_backed_agent_count"] == 3
    assert summary["provider_backed_agent_names"] == ORDERED_AGENTS


def test_summary_reports_handoff_traces_and_aggregate_available():
    summary = _run(
        workflow_readiness_enabled=True
    )["chain_payload"]["three_agent_workflow_readiness"]

    assert summary["structured_handoff_available"] is True
    assert summary["llmops_trace_available"] is True
    assert summary["llmops_aggregate_available"] is True
    assert summary["semantic_evidence_quality_gate_available"] is False


def test_incomplete_summary_is_deterministic_when_proof_is_missing():
    summary = _run(
        workflow_readiness_enabled=True,
        provider_handoff_enabled=False,
        llmops_aggregate_enabled=False,
    )["chain_payload"]["three_agent_workflow_readiness"]

    assert summary["readiness_status"] == (
        "incomplete_shadow_provider_workflow"
    )
    assert summary["structured_handoff_available"] is False
    assert summary["llmops_aggregate_available"] is False


def test_summary_reports_zero_mutation_authority():
    summary = _run(
        workflow_readiness_enabled=True
    )["chain_payload"]["three_agent_workflow_readiness"]

    assert summary["mutation_authorized_agent_count"] == 0
    assert summary["final_scoring_mutation_enabled"] is False
    assert summary["ranking_mutation_enabled"] is False
    assert summary["queue_mutation_enabled"] is False
    assert summary["approval_mutation_enabled"] is False
    assert summary["resume_mutation_enabled"] is False
    assert summary["execution_enabled"] is False
    assert summary["submission_enabled"] is False


def test_review_packet_exposes_existing_readiness_summary():
    hook = _run(workflow_readiness_enabled=True)
    packet = (
        pipeline_agent_review_packet.build_pipeline_agent_review_packet_payload(
            hook_payload=hook
        )
    )

    assert packet["three_agent_workflow_readiness"] == (
        hook["chain_payload"]["three_agent_workflow_readiness"]
    )
    assert packet["provider_backed_automated_agents"] == 3
    assert packet["mutation_authorized_agents"] == 0


def test_readiness_is_advisory_without_external_or_mutation_wiring():
    summary = _run(
        workflow_readiness_enabled=True
    )["chain_payload"]["three_agent_workflow_readiness"]
    safety = summary["safety_metadata"]

    assert safety["read_only"] is True
    assert safety["advisory_only"] is True
    assert safety["did_write_database"] is False
    assert safety["did_mutate_scoring"] is False
    assert safety["did_change_ranking"] is False
    assert safety["did_mutate_queue"] is False
    assert safety["did_create_approval"] is False
    assert safety["did_mutate_resume"] is False
    assert safety["did_execute_application"] is False
    assert safety["did_submit_application"] is False

    source = (
        ROOT / "src/agents/three_agent_workflow_readiness.py"
    ).read_text(encoding="utf-8").lower()
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
        "src/app/api.py": "a52216e4920bc866d09f8899c12b3a1e8b2dd86a92d9e366d383db09f9e10a32",
        "src/app/static/agentic_review.js": "1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b",
        "src/pipeline/collector.py": "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405",
        "src/pipeline/application_scorer.py": "e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b",
        "src/pipeline/job_ranker.py": "5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54",
    }
    for relative_path, expected_hash in expected.items():
        assert hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )
