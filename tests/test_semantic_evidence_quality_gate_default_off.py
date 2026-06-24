import hashlib
from copy import deepcopy
from pathlib import Path

from src.agents import semantic_evidence_quality_gate
from src.agents import shadow_sidecar_hook


ROOT = Path(__file__).resolve().parents[1]


def _evidence(index, score, text=None):
    return {
        "chunk_id": f"chunk-{index}",
        "chunk_type": "job_description",
        "evidence_text": text if text is not None else f"Evidence {index}",
        "source": "fixture",
        "retrieval_score": score,
    }


def _assert_safety(payload, *, enabled, passed, attached):
    safety = payload["safety_metadata"]
    assert safety["read_only"] is True
    assert safety["advisory_only"] is True
    assert safety["semantic_evidence_quality_gate_enabled"] is enabled
    assert safety["semantic_evidence_quality_passed"] is passed
    assert safety["semantic_evidence_attached"] is attached
    assert safety["provider_calls_made"] is False
    assert safety["embeddings_created"] is False
    assert safety["did_read_database"] is False
    assert safety["did_write_database"] is False
    assert safety["did_mutate_scoring"] is False
    assert safety["did_change_ranking"] is False
    assert safety["did_mutate_queue"] is False
    assert safety["did_create_approval"] is False
    assert safety["did_mutate_approval"] is False
    assert safety["did_mutate_resume"] is False
    assert safety["did_create_execution_request"] is False
    assert safety["did_create_execution_launch_request"] is False
    assert safety["did_execute_application"] is False
    assert safety["did_submit_application"] is False


def test_default_off_skips_without_mutating_input():
    evidence = [_evidence(1, 0.95)]
    before = deepcopy(evidence)

    payload = semantic_evidence_quality_gate.run_semantic_evidence_quality_gate(
        evidence_items=evidence
    )

    assert evidence == before
    assert payload["status"] == (
        "semantic_evidence_quality_gate_skipped_default_off"
    )
    assert payload["quality_evidence"] == []
    _assert_safety(payload, enabled=False, passed=False, attached=False)


def test_empty_evidence_fails_safely():
    payload = semantic_evidence_quality_gate.run_semantic_evidence_quality_gate(
        enabled=True,
        evidence_items=[],
    )

    assert payload["status"] == "evidence_quality_failed"
    assert payload["quality_evidence"] == []
    _assert_safety(payload, enabled=True, passed=False, attached=False)


def test_low_similarity_evidence_fails_safely():
    payload = semantic_evidence_quality_gate.run_semantic_evidence_quality_gate(
        enabled=True,
        evidence_items=[_evidence(1, 0.4)],
        minimum_similarity_score=0.8,
    )

    assert payload["status"] == "evidence_quality_failed"
    assert payload["rejected_reasons"] == ["similarity_below_minimum"]
    _assert_safety(payload, enabled=True, passed=False, attached=False)


def test_enough_high_quality_evidence_passes():
    payload = semantic_evidence_quality_gate.run_semantic_evidence_quality_gate(
        enabled=True,
        evidence_items=[_evidence(1, 0.91), _evidence(2, 0.87)],
        minimum_similarity_score=0.8,
        minimum_evidence_count=2,
    )

    assert payload["status"] == "evidence_quality_passed"
    assert [item["chunk_id"] for item in payload["quality_evidence"]] == [
        "chunk-1",
        "chunk-2",
    ]
    _assert_safety(payload, enabled=True, passed=True, attached=True)


def test_duplicate_and_empty_evidence_is_filtered():
    duplicate = _evidence(1, 0.9)
    payload = semantic_evidence_quality_gate.run_semantic_evidence_quality_gate(
        enabled=True,
        evidence_items=[
            duplicate,
            deepcopy(duplicate),
            {
                "chunk_id": "empty",
                "retrieval_score": 0.95,
            },
        ],
    )

    assert payload["status"] == "evidence_quality_passed"
    assert len(payload["quality_evidence"]) == 1
    assert payload["duplicate_count"] == 1
    assert "duplicate_evidence" in payload["rejected_reasons"]
    assert "evidence_content_required" in payload["rejected_reasons"]


def test_output_evidence_is_sorted_and_capped():
    payload = semantic_evidence_quality_gate.run_semantic_evidence_quality_gate(
        enabled=True,
        evidence_items=[
            _evidence(1, 0.81),
            _evidence(2, 0.99),
            _evidence(3, 0.9),
        ],
        minimum_similarity_score=0.8,
        max_evidence_count=2,
    )

    assert [item["chunk_id"] for item in payload["quality_evidence"]] == [
        "chunk-2",
        "chunk-3",
    ]
    assert payload["capped_count"] == 1


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


def _run_shadow(items):
    return shadow_sidecar_hook.run_shadow_sidecar_pipeline_hook(
        stage_name="post_final_scoring",
        source_deterministic_stage="application_priority",
        source_deterministic_status="completed",
        sidecar_config={
            "APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED": True,
            "APPLYLENS_AGENTIC_PIPELINE_SHADOW_JD_INTELLIGENCE_ENABLED": True,
        },
        vector_evidence_hook_payload=_vector_payload(items),
        semantic_evidence_quality_gate_enabled=True,
        semantic_evidence_minimum_similarity_score=0.8,
    )


def test_failed_gate_keeps_semantic_evidence_out_of_shadow_inputs():
    payload = _run_shadow([_evidence(1, 0.4)])
    context = payload["existing_trace_context"]["vector_evidence_context"]

    assert context["semantic_evidence_quality_gate"]["status"] == (
        "evidence_quality_failed"
    )
    assert "semantic_evidence_context" not in context
    assert "semantic_retrieval" not in context["evidence_context"]
    for result in payload.get("chain_payload", {}).get("ordered_agent_results", []):
        assert "semantic_evidence_input" not in result


def test_passed_gate_attaches_only_cleaned_capped_shadow_evidence():
    payload = _run_shadow(
        [_evidence(1, 0.82), _evidence(2, 0.96), _evidence(3, 0.9)]
    )
    semantic = payload["existing_trace_context"][
        "vector_evidence_context"
    ]["semantic_evidence_context"]

    assert semantic["semantic_evidence_input_shadow_only"] is True
    assert [item["chunk_id"] for item in semantic["retrieval_candidates"]] == [
        "chunk-2",
        "chunk-3",
        "chunk-1",
    ]


def test_zero_agent_counts_and_no_external_or_mutation_wiring():
    payload = semantic_evidence_quality_gate.run_semantic_evidence_quality_gate()
    assert payload["provider_backed_automated_agents"] == 0
    assert payload["live_provider_backed_automated_agents"] == 0
    assert payload["mutation_authorized_agents"] == 0
    assert payload["mutation_authorized_scoring_agents"] == 0
    assert payload["mutation_authorized_ranking_agents"] == 0
    assert payload["mutation_authorized_application_agents"] == 0

    source = (
        ROOT / "src/agents/semantic_evidence_quality_gate.py"
    ).read_text(encoding="utf-8").lower()
    for marker in (
        "openai",
        "langchain",
        "sentence_transformers",
        "embedding_provider",
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
        assert marker not in source


def test_api_ui_dependencies_and_protected_decision_modules_are_unchanged():
    expected = {
        "requirements.txt": "96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f",
        "src/app/api.py": "8ab44f7e97113f6d28e9a8f7d032affef2e1f8f891286986d9e95d581ff97fbf",
        "src/app/static/agentic_review.js": "94e9f1c484f6459833141a37cddd7a0bb092fb185c7119b4909a5ed9d925ed6a",
        "src/pipeline/application_scorer.py": "e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b",
        "src/pipeline/job_ranker.py": "5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54",
    }
    for relative_path, expected_hash in expected.items():
        assert hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )
