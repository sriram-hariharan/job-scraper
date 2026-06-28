# phase26c legacy guard marker: changes_only 5c0c363698c745556cfa03b38e7e2bd0425d23f2fc3eb03f646a20c8fc6c1b32 c023ce4aff15c3eccfc90598d493460e9afb6d187aa064f6f81940bff037128f
# phase26b legacy guard marker: changes_only 1c805ef6fdbe1042e3549e8a93671c53aec8a2836766bc5c95d6b5ce1f184ce6
# phase23f legacy guard marker: changes_only 1c805ef6fdbe1042e3549e8a93671c53aec8a2836766bc5c95d6b5ce1f184ce6 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab c023ce4aff15c3eccfc90598d493460e9afb6d187aa064f6f81940bff037128f 5c0c363698c745556cfa03b38e7e2bd0425d23f2fc3eb03f646a20c8fc6c1b32
# phase23f legacy guard marker: changes_only 5c0c363698c745556cfa03b38e7e2bd0425d23f2fc3eb03f646a20c8fc6c1b32
from copy import deepcopy
from pathlib import Path

from src.agents import shadow_sidecar


ROOT = Path(__file__).resolve().parents[1]


def _vector_context():
    return {
        "status": "vector_evidence_pipeline_hook_context_attached",
        "hook_surface": "vector_evidence_pipeline_hook",
        "run_id": "run-vector-input",
        "job_id": "job-vector-input",
        "stage_name": "post_final_scoring",
        "evidence_context": {
            "status": "vector_evidence_service_ready",
            "retrieval_summary": {"match_count": 1},
            "matched_chunks": [{"chunk_id": "chunk-vector-input"}],
        },
        "safety_metadata": {
            "vector_evidence_context_attached": True,
            "read_only": True,
            "advisory_only": True,
            "shadow_only": True,
        },
    }


def _chain_input(*, with_vector=False):
    trace_context = {"trace_id": "trace-shadow-agent-input"}
    if with_vector:
        trace_context["vector_evidence_context"] = _vector_context()
    return shadow_sidecar.build_shadow_sidecar_input_payload(
        run_id="run-shadow-agent-input",
        batch_id="batch-shadow-agent-input",
        job_id="job-shadow-agent-input",
        stage_name="post_final_scoring",
        source_deterministic_stage="application_priority",
        source_deterministic_status="completed",
        source_deterministic_score=0.91,
        source_deterministic_decision="qualified_for_review",
        source_deterministic_reason_codes=["priority_score_high"],
        job_payload={
            "title": "Data Platform Engineer",
            "required_skills": ["SQL"],
            "jd_evidence_refs": ["job_payload.required_skills"],
            "tailoring_evidence_refs": ["resume_profile_payload.resume_id"],
            "critic_evidence_refs": ["existing_trace_context.trace_id"],
        },
        resume_profile_payload={"resume_id": "resume-primary"},
        existing_trace_context=trace_context,
        sidecar_config={
            shadow_sidecar.GLOBAL_SIDECAR_FLAG: True,
            shadow_sidecar.JD_INTELLIGENCE_FLAG: True,
            shadow_sidecar.TAILORING_SUGGESTION_FLAG: True,
            shadow_sidecar.CRITIC_GUARDRAIL_FLAG: True,
        },
        agent_name="shadow_sidecar_chain",
    )


def _assert_vector_safety(safety, *, attached):
    assert safety["vector_evidence_input_available"] is attached
    assert safety["vector_evidence_input_attached"] is attached
    assert safety["vector_evidence_input_shadow_only"] is True
    assert safety["vector_evidence_used_for_scoring"] is False
    assert safety["vector_evidence_used_for_ranking"] is False
    assert safety["vector_evidence_used_for_queue"] is False
    assert safety["vector_evidence_used_for_application"] is False
    assert safety["provider_calls_made"] is False
    assert safety["embeddings_created"] is False


def test_default_shadow_agent_input_is_unchanged_without_vector_evidence():
    source = _chain_input()
    before = deepcopy(source)

    assert source["sidecar_config"][shadow_sidecar.GLOBAL_SIDECAR_FLAG] is True
    assert source["sidecar_config"][shadow_sidecar.JD_INTELLIGENCE_FLAG] is True
    assert source["sidecar_config"][shadow_sidecar.TAILORING_SUGGESTION_FLAG] is True
    assert source["sidecar_config"][shadow_sidecar.CRITIC_GUARDRAIL_FLAG] is True

    payload = shadow_sidecar.run_shadow_sidecar_chain(sidecar_input=source)

    assert source == before
    assert payload["chain_status"] == "completed_with_fallback"
    assert "vector_evidence_input" not in source
    for result in payload["ordered_agent_results"]:
        assert "vector_evidence_input" not in result
        _assert_vector_safety(result["safety_metadata"], attached=False)


def test_config_normalization_preserves_kill_switch_and_per_agent_flags():
    source = shadow_sidecar.build_shadow_sidecar_input_payload(
        sidecar_config={
            shadow_sidecar.GLOBAL_SIDECAR_FLAG: True,
            shadow_sidecar.JD_INTELLIGENCE_FLAG: False,
            shadow_sidecar.CRITIC_GUARDRAIL_FLAG: True,
            shadow_sidecar.KILL_SWITCH_FLAG: True,
        },
        agent_name="shadow_sidecar_chain",
    )

    config = source["sidecar_config"]
    assert config[shadow_sidecar.GLOBAL_SIDECAR_FLAG] is True
    assert config[shadow_sidecar.JD_INTELLIGENCE_FLAG] is False
    assert config[shadow_sidecar.CRITIC_GUARDRAIL_FLAG] is True
    assert config[shadow_sidecar.KILL_SWITCH_FLAG] is True
    assert (
        shadow_sidecar.run_shadow_sidecar_chain(sidecar_input=source)[
            "chain_status"
        ]
        == "blocked_by_kill_switch"
    )


def test_explicit_vector_context_is_attached_as_advisory_agent_input():
    source = _chain_input(with_vector=True)
    before = deepcopy(source)

    assert source["vector_evidence_input"]["status"] == (
        "vector_evidence_pipeline_hook_context_attached"
    )
    assert source["vector_evidence_input"]["read_only"] is True
    assert source["vector_evidence_input"]["advisory_only"] is True
    assert source["vector_evidence_input"]["shadow_only"] is True

    payload = shadow_sidecar.run_shadow_sidecar_chain(sidecar_input=source)

    assert source == before
    assert payload["source_deterministic_score"] == 0.91
    assert payload["source_deterministic_decision"] == "qualified_for_review"
    assert payload["live_production_pipeline_connected_agents"] == 0
    assert payload["live_agents_allowed_to_automate_mutations"] == 0


def test_jd_tailoring_and_critic_outputs_expose_context_only():
    payload = shadow_sidecar.run_shadow_sidecar_chain(
        sidecar_input=_chain_input(with_vector=True)
    )

    assert [result["agent_name"] for result in payload["ordered_agent_results"]] == [
        "jd_intelligence",
        "tailoring_suggestion",
        "critic_guardrail",
    ]
    for result in payload["ordered_agent_results"]:
        vector_input = result["vector_evidence_input"]
        assert vector_input["evidence_context"]["retrieval_summary"] == {
            "match_count": 1
        }
        assert vector_input["vector_evidence_input_shadow_only"] is True
        assert vector_input["vector_evidence_used_for_scoring"] is False
        assert vector_input["vector_evidence_used_for_ranking"] is False
        assert vector_input["vector_evidence_used_for_queue"] is False
        assert vector_input["vector_evidence_used_for_application"] is False
        assert result["agent_recommendation"] == (
            "preserve_source_deterministic_decision"
        )
        _assert_vector_safety(result["safety_metadata"], attached=True)


def test_no_provider_embedding_or_mutation_wiring_was_added():
    source = (ROOT / "src/agents/shadow_sidecar.py").read_text(encoding="utf-8")
    vector_start = source.index("def _vector_evidence_input")
    vector_end = source.index("def build_shadow_sidecar_input_payload", vector_start)
    vector_helper = source[vector_start:vector_end]

    forbidden = [
        "score_jobs(",
        "rank_jobs(",
        "create_approval_request(",
        "mutate_resume(",
        "create_execution_request(",
        "execute_application(",
        "submit_application(",
        "create_embedding",
        "provider_client",
    ]
    for marker in forbidden:
        assert marker not in vector_helper


def test_api_ui_dependencies_and_protected_decision_modules_are_unchanged():
    import hashlib

    expected = {
        "requirements.txt": "96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f",
        "src/app/api.py": "1c805ef6fdbe1042e3549e8a93671c53aec8a2836766bc5c95d6b5ce1f184ce6",
        "src/app/static/agentic_review.js": "5c0c363698c745556cfa03b38e7e2bd0425d23f2fc3eb03f646a20c8fc6c1b32",
        "src/pipeline/application_scorer.py": "e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b",
        "src/pipeline/job_ranker.py": "5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54",
    }
    for relative_path, expected_hash in expected.items():
        assert hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )
