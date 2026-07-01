# phase56b legacy guard marker: changes_only a92bb0e783fc67d60b5c8e0e480bf2fedf43e7feb5c4e79311bbaef95e2aca02 0604cf7402b6ddc2eb70b3c17999bcb40a055587957af8aa77bfe9bc7fee4431
# phase56a legacy guard marker: changes_only b341950ac8cbd880b3d270ea56183e4aa2076d9cf7119b99ef833ad363dcd7ce a92bb0e783fc67d60b5c8e0e480bf2fedf43e7feb5c4e79311bbaef95e2aca02
# phase26c legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c
# phase26b legacy guard marker: changes_only b341950ac8cbd880b3d270ea56183e4aa2076d9cf7119b99ef833ad363dcd7ce
# phase23f legacy guard marker: changes_only b341950ac8cbd880b3d270ea56183e4aa2076d9cf7119b99ef833ad363dcd7ce 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
# phase23f legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
from copy import deepcopy
from pathlib import Path

from src.agents import vector_evidence_pipeline_hook
from src.pipeline import collector


ROOT = Path(__file__).resolve().parents[1]
FLAG = "APPLYLENS_PIPELINE_VECTOR_EVIDENCE_HOOK_ENABLED"


def _jobs():
    return [
        {
            "id": "job-vector-hook",
            "title": "Data Platform Engineer",
            "company": "ExampleCo",
            "application_priority_score": 0.91,
        }
    ]


def _fake_service(**kwargs):
    return {
        "status": "vector_evidence_service_ready",
        "service_surface": "fake_vector_evidence_service",
        "retrieval_summary": {
            "status": "vector_evidence_retrieval_ready",
            "match_count": 1,
            "query": kwargs["query_text"],
        },
        "matched_chunks": [
            {
                "chunk_id": "chunk-1",
                "content": "Advisory evidence only.",
            }
        ],
        "skipped_reasons": {"indexing": [], "retrieval": []},
        "safety_metadata": {
            "did_read_database": True,
            "did_write_database": False,
            "provider_calls_made": False,
            "embeddings_created": False,
        },
    }


def _assert_advisory_safety(payload, *, enabled, attempted, attached):
    safety = payload["safety_metadata"]
    assert safety["read_only"] is True
    assert safety["advisory_only"] is True
    assert safety["shadow_only"] is True
    assert safety["vector_evidence_hook_enabled"] is enabled
    assert safety["vector_evidence_hook_attempted"] is attempted
    assert safety["vector_evidence_context_attached"] is attached
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
    assert safety["provider_calls_made"] is False
    assert safety["embeddings_created"] is False
    assert safety["mutation_authorized"] is False


def test_default_collector_behavior_does_not_use_vector_evidence(monkeypatch):
    monkeypatch.delenv(FLAG, raising=False)
    jobs = _jobs()
    before = deepcopy(jobs)
    calls = []

    def fail_if_called(**_kwargs):
        calls.append("called")
        raise AssertionError("default-off hook must not call the service")

    payload = collector._maybe_collect_vector_evidence_after_application_priority(
        jobs,
        vector_evidence_service=fail_if_called,
    )

    assert payload is None
    assert calls == []
    assert jobs == before


def test_explicit_disabled_flag_does_nothing():
    jobs = _jobs()
    before = deepcopy(jobs)

    payload = collector._maybe_collect_vector_evidence_after_application_priority(
        jobs,
        enabled=False,
        vector_evidence_service=_fake_service,
    )

    assert payload is None
    assert jobs == before


def test_isolated_hook_default_payload_is_traceable_and_default_off():
    payload = vector_evidence_pipeline_hook.run_vector_evidence_pipeline_hook()

    assert payload["status"] == "vector_evidence_pipeline_hook_default_off"
    assert payload["evidence_context"] == {}
    _assert_advisory_safety(
        payload,
        enabled=False,
        attempted=False,
        attached=False,
    )


def test_enabled_fake_service_attaches_advisory_context_without_job_mutation():
    jobs = _jobs()
    before = deepcopy(jobs)

    payload = collector._maybe_collect_vector_evidence_after_application_priority(
        jobs,
        enabled=True,
        vector_evidence_service=_fake_service,
    )

    assert payload["status"] == "vector_evidence_pipeline_hook_context_attached"
    assert payload["job_id"] == "job-vector-hook"
    assert payload["stage_name"] == "post_final_scoring"
    assert payload["evidence_context"] == {
        "status": "vector_evidence_service_ready",
        "service_surface": "fake_vector_evidence_service",
        "retrieval_summary": {
            "status": "vector_evidence_retrieval_ready",
            "match_count": 1,
            "query": "Data Platform Engineer ExampleCo",
        },
        "matched_chunks": [
            {
                "chunk_id": "chunk-1",
                "content": "Advisory evidence only.",
            }
        ],
        "skipped_reasons": {"indexing": [], "retrieval": []},
        "read_only": True,
        "advisory_only": True,
    }
    assert payload["live_provider_backed_automated_agents"] == 0
    assert payload["mutation_authorized_agents"] == 0
    assert payload["safety_metadata"]["did_read_database"] is True
    _assert_advisory_safety(
        payload,
        enabled=True,
        attempted=True,
        attached=True,
    )
    assert jobs == before


def test_hook_failure_is_non_blocking_and_preserves_pipeline_jobs():
    jobs = _jobs()
    before = deepcopy(jobs)

    def fail_service(**_kwargs):
        raise RuntimeError("fake read failure")

    payload = collector._maybe_collect_vector_evidence_after_application_priority(
        jobs,
        enabled=True,
        vector_evidence_service=fail_service,
    )

    assert payload is None
    assert jobs == before


def test_pipeline_call_site_is_adjacent_and_output_is_not_consumed():
    source = (ROOT / "src/pipeline/collector.py").read_text(encoding="utf-8")
    complete_marker = (
        'complete_stage("application_priority", counts={"scored_jobs": len(scored_jobs)})'
    )
    shadow_marker = "_maybe_run_shadow_sidecar_after_application_priority("
    vector_marker = (
        "_maybe_collect_vector_evidence_after_application_priority(scored_jobs)"
    )
    source_health_marker = "if role_title_audit_rows is not None:"

    assert source.count(vector_marker) == 1
    assert (
        source.index(complete_marker)
        < source.index(vector_marker)
        < source.index(shadow_marker, source.index(vector_marker))
        < source.index(source_health_marker, source.index(vector_marker))
    )
    assert f"{vector_marker}." not in source
    assert f"= {vector_marker}" not in source


def test_hook_contains_no_mutation_provider_embedding_api_or_ui_wiring():
    hook_source = (
        ROOT / "src/agents/vector_evidence_pipeline_hook.py"
    ).read_text(encoding="utf-8")
    collector_source = (ROOT / "src/pipeline/collector.py").read_text(
        encoding="utf-8"
    )
    combined = hook_source + collector_source

    forbidden = [
        "score_jobs(job_payload",
        "rank_jobs(job_payload",
        "create_approval_request(",
        "record_approval_decision(",
        "mutate_resume(",
        "create_execution_request(",
        "create_execution_launch_request(",
        "execute_application(",
        "submit_application(",
        "create_embedding",
        "provider_client(",
        "src.app.api",
        "agentic_review.js",
    ]
    for marker in forbidden:
        assert marker not in combined


def test_dependency_api_ui_and_protected_runtime_hashes_are_unchanged():
    expected = {
        "requirements.txt": "96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f",
        "src/app/api.py": "b341950ac8cbd880b3d270ea56183e4aa2076d9cf7119b99ef833ad363dcd7ce",
        "src/app/static/agentic_review.js": "1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b",
        "src/pipeline/application_scorer.py": "e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b",
        "src/pipeline/job_ranker.py": "5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54",
    }
    import hashlib

    for relative_path, expected_hash in expected.items():
        actual = hashlib.sha256(
            (ROOT / relative_path).read_bytes()
        ).hexdigest()
        assert actual == expected_hash
