# phase56b legacy guard marker: changes_only 0631df36d23740a835c22bcb2b9bf4ad682279f76794273889006cad9c4ec011 3e6c0325dc306b45465cc84149eecb91b40acdd503603da32648bb1b8c0456ed
# phase56a legacy guard marker: changes_only f9137ef3f8d1cc27fe08f3a592f1cff977a124cb6132a91394ee8350674bea6f 0631df36d23740a835c22bcb2b9bf4ad682279f76794273889006cad9c4ec011
# phase26c legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c
# phase26b legacy guard marker: changes_only f9137ef3f8d1cc27fe08f3a592f1cff977a124cb6132a91394ee8350674bea6f
# phase23f legacy guard marker: changes_only f9137ef3f8d1cc27fe08f3a592f1cff977a124cb6132a91394ee8350674bea6f 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
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


def _vector_payload(items):
    return {
        "status": "vector_evidence_pipeline_hook_context_attached",
        "hook_surface": "vector_evidence_pipeline_hook",
        "evidence_context": {
            "semantic_retrieval": {
                "status": "embedding_retrieval_completed",
                "retrieval_candidates": deepcopy(items),
                "result_count": len(items),
            }
        },
        "safety_metadata": {
            "vector_evidence_context_attached": True,
            "semantic_evidence_attached": True,
            "provider_calls_made": True,
            "embeddings_created": True,
        },
    }


def _evidence(chunk_id, score, text):
    return {
        "chunk_id": chunk_id,
        "chunk_type": "job_description",
        "evidence_text": text,
        "source": "fixture",
        "retrieval_score": score,
    }


def _run(**updates):
    kwargs = {
        "run_id": "run-phase-9j",
        "batch_id": "batch-phase-9j",
        "job_id": "job-phase-9j",
        "stage_name": "post_final_scoring",
        "source_deterministic_stage": "application_priority",
        "source_deterministic_status": "completed",
        "source_deterministic_score": 0.91,
        "source_deterministic_decision": "qualified_for_review",
        "source_deterministic_reason_codes": [
            "application_priority_completed"
        ],
        "existing_trace_context": {"trace_id": "trace-phase-9j"},
    }
    kwargs.update(updates)
    return shadow_sidecar_hook.run_shadow_sidecar_pipeline_hook(**kwargs)


def _assert_workflow_safety(workflow, *, enabled, count):
    assert workflow["three_agent_shadow_workflow_enabled"] is enabled
    assert workflow["ordered_agent_count"] == count
    assert workflow["ordered_agent_names"] == (
        ORDERED_AGENTS if count == 3 else []
    )
    assert workflow["did_call_provider"] is False
    assert workflow["did_create_embeddings"] is False
    assert workflow["did_write_database"] is False
    assert workflow["did_mutate_scoring"] is False
    assert workflow["did_change_ranking"] is False
    assert workflow["did_mutate_queue"] is False
    assert workflow["did_create_approval"] is False
    assert workflow["did_mutate_resume"] is False
    assert workflow["did_execute_application"] is False
    assert workflow["did_submit_application"] is False


def test_default_off_does_not_run_three_agent_chain():
    payload = _run()

    assert payload["chain_attempted"] is False
    assert payload["chain_payload"] == {}
    assert payload["hook_status"] == "hook_not_enabled"


def test_enabled_workflow_runs_exactly_three_existing_agents_in_order():
    payload = _run(three_agent_shadow_workflow_enabled=True)
    chain = payload["chain_payload"]

    assert chain["stage_order"] == ORDERED_AGENTS
    assert len(chain["ordered_agent_results"]) == 3
    assert [
        result["agent_name"] for result in chain["ordered_agent_results"]
    ] == ORDERED_AGENTS
    assert all(
        result["provider_mode"] == "disabled"
        for result in chain["ordered_agent_results"]
    )
    _assert_workflow_safety(
        chain["three_agent_shadow_workflow"],
        enabled=True,
        count=3,
    )


def test_failed_quality_gate_keeps_semantic_evidence_untrusted():
    payload = _run(
        three_agent_shadow_workflow_enabled=True,
        semantic_evidence_quality_gate_enabled=True,
        semantic_evidence_minimum_similarity_score=0.8,
        vector_evidence_hook_payload=_vector_payload(
            [_evidence("low", 0.4, "Low quality evidence")]
        ),
    )
    chain = payload["chain_payload"]

    assert chain["three_agent_shadow_workflow"][
        "semantic_evidence_quality_gate_status"
    ] == "evidence_quality_failed"
    for result in chain["ordered_agent_results"]:
        assert "semantic_evidence_input" not in result


def test_passed_quality_gate_reaches_agents_as_cleaned_advisory_context():
    duplicate = _evidence("best", 0.96, " Strong evidence ")
    payload = _run(
        three_agent_shadow_workflow_enabled=True,
        semantic_evidence_quality_gate_enabled=True,
        semantic_evidence_minimum_similarity_score=0.8,
        semantic_evidence_max_count=2,
        vector_evidence_hook_payload=_vector_payload(
            [
                _evidence("third", 0.82, "Third evidence"),
                duplicate,
                deepcopy(duplicate),
                _evidence("second", 0.9, "Second evidence"),
            ]
        ),
    )
    chain = payload["chain_payload"]

    assert chain["three_agent_shadow_workflow"][
        "semantic_evidence_quality_gate_status"
    ] == "evidence_quality_passed"
    for result in chain["ordered_agent_results"]:
        semantic = result["semantic_evidence_input"]
        assert semantic["advisory_only"] is True
        assert semantic["semantic_evidence_input_shadow_only"] is True
        assert [
            item["chunk_id"] for item in semantic["retrieval_candidates"]
        ] == ["best", "second"]


def test_review_packet_includes_existing_ordered_workflow_summary():
    hook = _run(three_agent_shadow_workflow_enabled=True)
    packet = pipeline_agent_review_packet.build_pipeline_agent_review_packet_payload(
        hook_payload=hook
    )

    workflow = packet["three_agent_shadow_workflow"]
    _assert_workflow_safety(workflow, enabled=True, count=3)


def test_zero_agent_authorization_and_no_mutation_or_external_wiring():
    hook = _run(three_agent_shadow_workflow_enabled=True)
    packet = pipeline_agent_review_packet.build_pipeline_agent_review_packet_payload(
        hook_payload=hook
    )
    assert packet["live_provider_backed_automated_agents"] == 0
    assert packet["mutation_authorized_agents"] == 0

    sources = "\n".join(
        (ROOT / path).read_text(encoding="utf-8")
        for path in (
            "src/agents/shadow_sidecar.py",
            "src/agents/shadow_sidecar_hook.py",
            "src/agents/pipeline_agent_review_packet.py",
        )
    )
    for marker in (
        "create_embedding(",
        "embedding_provider(",
        "execute_vector_evidence_chunk_insert",
        "score_jobs(",
        "rank_jobs(",
        "create_approval_request(",
        "record_approval_decision(",
        "mutate_resume(",
        "create_execution_request(",
        "create_execution_launch_request(",
        "execute_application(",
        "submit_application(",
        "langgraph",
    ):
        assert marker not in sources.lower()


def test_api_ui_pipeline_dependencies_and_decision_modules_are_unchanged():
    expected = {
        "requirements.txt": "96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f",
        "src/app/api.py": "f9137ef3f8d1cc27fe08f3a592f1cff977a124cb6132a91394ee8350674bea6f",
        "src/app/static/agentic_review.js": "1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b",
        "src/pipeline/collector.py": "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405",
        "src/pipeline/application_scorer.py": "e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b",
        "src/pipeline/job_ranker.py": "5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54",
    }
    for relative_path, expected_hash in expected.items():
        assert hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )
