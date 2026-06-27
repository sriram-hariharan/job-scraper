# phase26c legacy guard marker: changes_only bb3b1f351b9f3aeac197a3077ce4403f649a17ff81247fb1d0e41eeacc3a9821 c71e2057276080e36fce4bec48a881753d8e09d7d1b49e7d0676d4a0665f32c9
# phase26b legacy guard marker: changes_only 96f9cd7e7f3f877a147d612ad1394b8fcdd4671244de25c9f99c34795304a8ff
# phase23f legacy guard marker: changes_only 96f9cd7e7f3f877a147d612ad1394b8fcdd4671244de25c9f99c34795304a8ff 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab c71e2057276080e36fce4bec48a881753d8e09d7d1b49e7d0676d4a0665f32c9 bb3b1f351b9f3aeac197a3077ce4403f649a17ff81247fb1d0e41eeacc3a9821
# phase23f legacy guard marker: changes_only bb3b1f351b9f3aeac197a3077ce4403f649a17ff81247fb1d0e41eeacc3a9821
from copy import deepcopy
from pathlib import Path

from src.agents import pipeline_agent_review_packet
from src.agents import shadow_sidecar_hook
from src.pipeline import collector


ROOT = Path(__file__).resolve().parents[1]


def _vector_hook_payload():
    return {
        "status": "vector_evidence_pipeline_hook_context_attached",
        "hook_surface": "vector_evidence_pipeline_hook",
        "run_id": "run-vector-context",
        "job_id": "job-vector-context",
        "stage_name": "post_final_scoring",
        "evidence_context": {
            "status": "vector_evidence_service_ready",
            "service_surface": "fake_vector_evidence_service",
            "retrieval_summary": {"match_count": 1},
            "matched_chunks": [{"chunk_id": "chunk-1"}],
            "skipped_reasons": {"indexing": [], "retrieval": []},
            "read_only": True,
            "advisory_only": True,
        },
        "safety_metadata": {
            "vector_evidence_context_attached": True,
            "did_read_database": True,
            "did_write_database": False,
            "provider_calls_made": False,
            "embeddings_created": False,
        },
    }


def _run_shadow(**kwargs):
    return shadow_sidecar_hook.run_shadow_sidecar_pipeline_hook(
        run_id="run-shadow",
        batch_id="batch-shadow",
        job_id="job-shadow",
        stage_name="post_final_scoring",
        source_deterministic_stage="application_priority",
        source_deterministic_status="completed",
        source_deterministic_score=1,
        source_deterministic_decision="scored_jobs_available",
        source_deterministic_reason_codes=["application_priority_completed"],
        sidecar_config={
            "APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED": True,
            "APPLYLENS_AGENTIC_PIPELINE_SHADOW_JD_INTELLIGENCE_ENABLED": True,
        },
        job_payload={"id": "job-shadow", "title": "Data Engineer"},
        existing_trace_context={"trace_id": "trace-shadow"},
        **kwargs,
    )


def _assert_vector_safety(safety, *, available):
    assert safety["vector_evidence_context_available"] is available
    assert safety["vector_evidence_context_attached"] is available
    assert safety["vector_evidence_context_shadow_only"] is True
    assert safety["vector_evidence_used_for_scoring"] is False
    assert safety["vector_evidence_used_for_ranking"] is False
    assert safety["vector_evidence_used_for_queue"] is False
    assert safety["vector_evidence_used_for_application"] is False
    assert safety["provider_calls_made"] is False
    assert safety["embeddings_created"] is False


def test_default_shadow_behavior_keeps_vector_context_absent():
    payload = _run_shadow()

    assert "vector_evidence_context" not in payload["existing_trace_context"]
    _assert_vector_safety(payload["safety_metadata"], available=False)

    packet = pipeline_agent_review_packet.build_pipeline_agent_review_packet_payload(
        hook_payload=payload
    )
    assert packet["vector_evidence_context"] == {}
    _assert_vector_safety(packet["safety_metadata"], available=False)


def test_explicit_vector_context_is_attached_as_shadow_advisory_metadata():
    source = _vector_hook_payload()
    before = deepcopy(source)

    payload = _run_shadow(vector_evidence_hook_payload=source)

    assert source == before
    context = payload["existing_trace_context"]["vector_evidence_context"]
    assert context["status"] == "vector_evidence_pipeline_hook_context_attached"
    assert context["evidence_context"]["matched_chunks"] == [
        {"chunk_id": "chunk-1"}
    ]
    assert context["safety_metadata"]["read_only"] is True
    assert context["safety_metadata"]["advisory_only"] is True
    assert context["safety_metadata"]["shadow_only"] is True
    _assert_vector_safety(payload["safety_metadata"], available=True)


def test_review_packet_exposes_only_advisory_vector_context():
    hook = _run_shadow(vector_evidence_hook_payload=_vector_hook_payload())

    packet = pipeline_agent_review_packet.build_pipeline_agent_review_packet_payload(
        hook_payload=hook
    )

    context = packet["vector_evidence_context"]
    assert context["status"] == "vector_evidence_pipeline_hook_context_attached"
    assert context["evidence_context"]["retrieval_summary"] == {"match_count": 1}
    assert context["read_only"] is True
    assert context["advisory_only"] is True
    assert context["shadow_only"] is True
    _assert_vector_safety(packet["safety_metadata"], available=True)
    assert packet["live_provider_backed_automated_agents"] == 0
    assert packet["mutation_authorized_agents"] == 0


def test_collector_collects_evidence_before_shadow_and_passes_it_only_as_context():
    source = (ROOT / "src/pipeline/collector.py").read_text(encoding="utf-8")
    vector_call = (
        "_maybe_collect_vector_evidence_after_application_priority(scored_jobs)"
    )
    shadow_call = "_maybe_run_shadow_sidecar_after_application_priority("
    vector_index = source.index(vector_call, source.index('section("APPLICATION PRIORITY"'))
    shadow_index = source.index(shadow_call, vector_index)

    assert vector_index < shadow_index
    assert "vector_evidence_hook_payload=vector_evidence_hook_payload" in source[
        shadow_index:shadow_index + 250
    ]
    assert "scored_jobs =" not in source[vector_index:shadow_index]


def test_no_scoring_ranking_queue_approval_resume_or_application_wiring():
    shadow_source = (ROOT / "src/agents/shadow_sidecar_hook.py").read_text(
        encoding="utf-8"
    )
    packet_source = (
        ROOT / "src/agents/pipeline_agent_review_packet.py"
    ).read_text(encoding="utf-8")
    collector_source = (ROOT / "src/pipeline/collector.py").read_text(
        encoding="utf-8"
    )
    propagation = shadow_source + packet_source

    forbidden = [
        "score_jobs(",
        "rank_jobs(",
        "create_approval_request(",
        "record_approval_decision(",
        "mutate_resume(",
        "create_execution_request(",
        "create_execution_launch_request(",
        "execute_application(",
        "submit_application(",
        "create_embedding",
        "provider_client",
    ]
    for marker in forbidden:
        assert marker not in propagation
    scoring_idx = collector_source.index("scored_jobs = score_jobs(ai_jobs)")
    complete_idx = collector_source.index(
        'complete_stage("application_priority", counts={"scored_jobs": len(scored_jobs)})',
        scoring_idx,
    )
    assert "vector_evidence_hook_payload" not in collector_source[
        scoring_idx:complete_idx
    ]


def test_api_ui_dependencies_and_protected_decision_modules_are_unchanged():
    import hashlib

    expected = {
        "requirements.txt": "96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f",
        "src/app/api.py": "96f9cd7e7f3f877a147d612ad1394b8fcdd4671244de25c9f99c34795304a8ff",
        "src/app/static/agentic_review.js": "bb3b1f351b9f3aeac197a3077ce4403f649a17ff81247fb1d0e41eeacc3a9821",
        "src/pipeline/application_scorer.py": "e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b",
        "src/pipeline/job_ranker.py": "5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54",
    }
    for relative_path, expected_hash in expected.items():
        assert hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )
