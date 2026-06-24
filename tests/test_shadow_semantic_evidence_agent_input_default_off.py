import hashlib
from copy import deepcopy
from pathlib import Path

from src.agents import pipeline_agent_review_packet
from src.agents import shadow_sidecar_hook


ROOT = Path(__file__).resolve().parents[1]


def _semantic_vector_hook_payload():
    return {
        "status": "vector_evidence_pipeline_hook_context_attached",
        "hook_surface": "vector_evidence_pipeline_hook",
        "run_id": "run-phase-9e",
        "job_id": "job-phase-9e",
        "stage_name": "post_final_scoring",
        "evidence_context": {
            "status": "vector_evidence_service_ready",
            "semantic_retrieval": {
                "status": "embedding_retrieval_completed",
                "result_count": 1,
                "retrieval_candidates": [
                    {
                        "chunk_id": "chunk-phase-9e",
                        "chunk_type": "job_description",
                        "evidence_text": "Large evidence text is not duplicated.",
                        "retrieval_score": 0.94,
                    }
                ],
                "read_only": True,
                "advisory_only": True,
                "shadow_only": True,
            },
        },
        "safety_metadata": {
            "vector_evidence_context_attached": True,
            "semantic_evidence_attached": True,
            "provider_calls_made": True,
            "embeddings_created": True,
            "did_read_database": True,
            "did_write_database": False,
        },
    }


def _run_shadow(vector_payload=None):
    return shadow_sidecar_hook.run_shadow_sidecar_pipeline_hook(
        run_id="run-phase-9e",
        batch_id="batch-phase-9e",
        job_id="job-phase-9e",
        stage_name="post_final_scoring",
        source_deterministic_stage="application_priority",
        source_deterministic_status="completed",
        source_deterministic_score=0.88,
        source_deterministic_decision="qualified_for_review",
        source_deterministic_reason_codes=["application_priority_completed"],
        sidecar_config={
            "APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED": True,
            "APPLYLENS_AGENTIC_PIPELINE_SHADOW_JD_INTELLIGENCE_ENABLED": True,
            "APPLYLENS_AGENTIC_PIPELINE_SHADOW_TAILORING_SUGGESTION_ENABLED": True,
            "APPLYLENS_AGENTIC_PIPELINE_SHADOW_CRITIC_GUARDRAIL_ENABLED": True,
        },
        existing_trace_context={"trace_id": "trace-phase-9e"},
        vector_evidence_hook_payload=vector_payload,
    )


def _assert_semantic_safety(safety, *, attached):
    assert safety["semantic_evidence_input_available"] is attached
    assert safety["semantic_evidence_input_attached"] is attached
    assert safety["semantic_evidence_input_shadow_only"] is True
    assert safety["semantic_evidence_used_for_scoring"] is False
    assert safety["semantic_evidence_used_for_ranking"] is False
    assert safety["semantic_evidence_used_for_queue"] is False
    assert safety["semantic_evidence_used_for_application"] is False
    assert safety["did_write_database"] is False


def test_default_shadow_behavior_is_unchanged_without_semantic_evidence():
    payload = _run_shadow()

    assert "vector_evidence_context" not in payload["existing_trace_context"]
    for result in payload["chain_payload"]["ordered_agent_results"]:
        assert "semantic_evidence_input" not in result
        _assert_semantic_safety(result["safety_metadata"], attached=False)


def test_semantic_evidence_is_attached_as_shadow_only_advisory_metadata():
    source = _semantic_vector_hook_payload()
    before = deepcopy(source)

    payload = _run_shadow(source)

    assert source == before
    context = payload["existing_trace_context"]["vector_evidence_context"]
    semantic = context["semantic_evidence_context"]
    assert semantic["status"] == "embedding_retrieval_completed"
    assert semantic["retrieval_candidates"] == [
        {
            "chunk_id": "chunk-phase-9e",
            "chunk_type": "job_description",
            "retrieval_score": 0.94,
        }
    ]
    assert "evidence_text" not in semantic["retrieval_candidates"][0]
    assert semantic["read_only"] is True
    assert semantic["advisory_only"] is True
    assert semantic["shadow_only"] is True
    _assert_semantic_safety(payload["safety_metadata"], attached=True)


def test_jd_tailoring_and_critic_receive_semantic_context_only():
    payload = _run_shadow(_semantic_vector_hook_payload())
    results = payload["chain_payload"]["ordered_agent_results"]

    assert [result["agent_name"] for result in results] == [
        "jd_intelligence",
        "tailoring_suggestion",
        "critic_guardrail",
    ]
    for result in results:
        semantic = result["semantic_evidence_input"]
        assert semantic["status"] == "embedding_retrieval_completed"
        assert semantic["semantic_evidence_input_shadow_only"] is True
        assert result["source_deterministic_score"] == 0.88
        assert result["source_deterministic_decision"] == "qualified_for_review"
        assert result["agent_recommendation"] == (
            "preserve_source_deterministic_decision"
        )
        assert result["safety_metadata"]["provider_calls_made"] is True
        assert result["safety_metadata"]["embeddings_created"] is True
        _assert_semantic_safety(result["safety_metadata"], attached=True)


def test_review_packet_exposes_semantic_evidence_as_read_only_context():
    hook = _run_shadow(_semantic_vector_hook_payload())
    packet = pipeline_agent_review_packet.build_pipeline_agent_review_packet_payload(
        hook_payload=hook
    )

    semantic = packet["semantic_evidence_context"]
    assert semantic["status"] == "embedding_retrieval_completed"
    assert semantic["read_only"] is True
    assert semantic["advisory_only"] is True
    assert semantic["semantic_evidence_used_for_scoring"] is False
    assert packet["safety_metadata"]["provider_calls_made"] is True
    assert packet["safety_metadata"]["embeddings_created"] is True
    _assert_semantic_safety(packet["safety_metadata"], attached=True)


def test_propagation_adds_no_provider_embedding_write_or_mutation_calls():
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
        "provider_client",
        "execute_vector_evidence_chunk_insert",
        "score_jobs(",
        "rank_jobs(",
        "create_approval_request(",
        "mutate_resume(",
        "create_execution_request(",
        "execute_application(",
        "submit_application(",
    ):
        assert marker not in sources


def test_api_ui_pipeline_dependencies_and_decision_modules_are_unchanged():
    expected = {
        "requirements.txt": "96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f",
        "src/app/api.py": "8ab44f7e97113f6d28e9a8f7d032affef2e1f8f891286986d9e95d581ff97fbf",
        "src/app/static/agentic_review.js": "94e9f1c484f6459833141a37cddd7a0bb092fb185c7119b4909a5ed9d925ed6a",
        "src/pipeline/collector.py": "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405",
        "src/pipeline/application_scorer.py": "e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b",
        "src/pipeline/job_ranker.py": "5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54",
    }
    for relative_path, expected_hash in expected.items():
        assert hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )


def test_agent_counts_remain_zero():
    packet = pipeline_agent_review_packet.build_pipeline_agent_review_packet_payload(
        hook_payload=_run_shadow(_semantic_vector_hook_payload())
    )
    assert packet["live_provider_backed_automated_agents"] == 0
    assert packet["mutation_authorized_agents"] == 0
