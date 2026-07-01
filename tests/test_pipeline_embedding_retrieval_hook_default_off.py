# phase56b legacy guard marker: changes_only 6f14bb0cb8d3ecd9cc192bc13570b24900f2ff8f4e81f9868b1f4f138cc2010d 9154ee68f0a5b394b66e7d187d6a0493a07f1521eeefc9e640637ebca27be711
# phase56a legacy guard marker: changes_only e2eee82ef5c27d75d8326b260d7f9d6f8d55a717b762e64cadd0941de05b808c 6f14bb0cb8d3ecd9cc192bc13570b24900f2ff8f4e81f9868b1f4f138cc2010d
# phase26c legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c
# phase26b legacy guard marker: changes_only e2eee82ef5c27d75d8326b260d7f9d6f8d55a717b762e64cadd0941de05b808c
# phase23f legacy guard marker: changes_only e2eee82ef5c27d75d8326b260d7f9d6f8d55a717b762e64cadd0941de05b808c 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
# phase23f legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
import hashlib
from copy import deepcopy
from pathlib import Path

from src.agents import vector_evidence_pipeline_hook


ROOT = Path(__file__).resolve().parents[1]


def _service(**_kwargs):
    return {
        "status": "vector_evidence_service_ready",
        "service_surface": "fake_vector_evidence_service",
        "retrieval_summary": {"match_count": 0},
        "matched_chunks": [],
        "skipped_reasons": {},
        "safety_metadata": {
            "did_read_database": False,
            "did_write_database": False,
        },
    }


def _base_kwargs():
    return {
        "enabled": True,
        "run_id": "run-phase-9d",
        "job_id": "job-phase-9d",
        "query_text": "semantic retrieval evidence",
        "job_payload": {"id": "job-phase-9d"},
        "vector_evidence_service": _service,
    }


def _semantic_kwargs():
    return {
        "embedding_retrieval_enabled": True,
        "embedding_retrieval_owner_user_id": "owner-phase-9d",
        "embedding_retrieval_model_id": "fixture-model",
        "embedding_retrieval_dimension": 3,
        "embedding_retrieval_top_k": 3,
        "embedding_retrieval_filters": {"chunk_type": "job_description"},
        "embedding_retrieval_provider": lambda _request: [0.1, 0.2, 0.3],
        "embedding_retrieval_read_enabled": True,
    }


def _assert_non_mutating(payload):
    safety = payload["safety_metadata"]
    assert safety["read_only"] is True
    assert safety["advisory_only"] is True
    assert safety["shadow_only"] is True
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


def test_default_hook_does_not_call_embedding_retrieval():
    calls = []

    payload = vector_evidence_pipeline_hook.run_vector_evidence_pipeline_hook(
        **_base_kwargs(),
        embedding_retrieval_helper=lambda **kwargs: calls.append(kwargs),
    )

    assert calls == []
    assert "semantic_retrieval" not in payload["evidence_context"]
    assert payload["safety_metadata"]["embedding_retrieval_enabled"] is False
    assert payload["safety_metadata"]["embedding_retrieval_attempted"] is False
    assert payload["safety_metadata"]["semantic_evidence_attached"] is False
    _assert_non_mutating(payload)


def test_explicit_disabled_flag_does_nothing():
    calls = []

    payload = vector_evidence_pipeline_hook.run_vector_evidence_pipeline_hook(
        **_base_kwargs(),
        embedding_retrieval_enabled=False,
        embedding_retrieval_helper=lambda **kwargs: calls.append(kwargs),
    )

    assert calls == []
    assert "semantic_retrieval" not in payload["evidence_context"]
    _assert_non_mutating(payload)


def test_fake_provider_and_reader_attach_semantic_evidence_metadata():
    rows = [
        {
            "chunk_id": "chunk-phase-9d",
            "chunk_type": "job_description",
            "evidence_text": "Semantic evidence.",
            "retrieval_score": 0.92,
        }
    ]
    reader_calls = []

    def reader(request):
        reader_calls.append(deepcopy(request))
        return {"rows": deepcopy(rows)}

    payload = vector_evidence_pipeline_hook.run_vector_evidence_pipeline_hook(
        **_base_kwargs(),
        **_semantic_kwargs(),
        embedding_retrieval_db_executor=reader,
    )

    semantic = payload["evidence_context"]["semantic_retrieval"]
    assert semantic["status"] == "embedding_retrieval_completed"
    assert semantic["retrieval_candidates"] == rows
    assert semantic["result_count"] == 1
    assert semantic["read_only"] is True
    assert semantic["advisory_only"] is True
    assert semantic["shadow_only"] is True
    assert len(reader_calls) == 1
    safety = payload["safety_metadata"]
    assert safety["embedding_retrieval_enabled"] is True
    assert safety["embedding_retrieval_attempted"] is True
    assert safety["semantic_evidence_attached"] is True
    assert safety["provider_calls_made"] is True
    assert safety["embeddings_created"] is True
    assert safety["did_read_database"] is True
    _assert_non_mutating(payload)


def test_provider_exception_is_non_blocking():
    def provider(_request):
        raise RuntimeError("fixture provider failure")

    semantic_kwargs = _semantic_kwargs()
    semantic_kwargs["embedding_retrieval_provider"] = provider
    payload = vector_evidence_pipeline_hook.run_vector_evidence_pipeline_hook(
        **_base_kwargs(),
        **semantic_kwargs,
        embedding_retrieval_db_executor=lambda _request: {
            "rows": []
        },
    )

    semantic = payload["evidence_context"]["semantic_retrieval"]
    assert semantic["status"] == "embedding_retrieval_provider_failed_non_blocking"
    assert semantic["errors"] == ["RuntimeError"]
    assert payload["safety_metadata"]["semantic_evidence_attached"] is False
    assert payload["safety_metadata"]["did_read_database"] is False
    _assert_non_mutating(payload)


def test_reader_exception_is_non_blocking():
    def reader(_request):
        raise RuntimeError("fixture reader failure")

    payload = vector_evidence_pipeline_hook.run_vector_evidence_pipeline_hook(
        **_base_kwargs(),
        **_semantic_kwargs(),
        embedding_retrieval_db_executor=reader,
    )

    semantic = payload["evidence_context"]["semantic_retrieval"]
    assert semantic["status"] == "embedding_retrieval_read_failed_non_blocking"
    assert semantic["errors"] == ["RuntimeError"]
    assert payload["safety_metadata"]["semantic_evidence_attached"] is False
    assert payload["safety_metadata"]["did_read_database"] is False
    _assert_non_mutating(payload)


def test_zero_agent_counts_and_no_mutation_or_runtime_wiring():
    payload = vector_evidence_pipeline_hook.run_vector_evidence_pipeline_hook()
    assert payload["provider_backed_automated_agents"] == 0
    assert payload["live_provider_backed_automated_agents"] == 0
    assert payload["mutation_authorized_agents"] == 0
    assert payload["mutation_authorized_scoring_agents"] == 0
    assert payload["mutation_authorized_ranking_agents"] == 0
    assert payload["mutation_authorized_application_agents"] == 0

    source = (
        ROOT / "src/agents/vector_evidence_pipeline_hook.py"
    ).read_text(encoding="utf-8")
    for marker in (
        "score_jobs(",
        "rank_jobs(",
        "create_approval_request(",
        "mutate_resume(",
        "create_execution_request(",
        "execute_application(",
        "submit_application(",
        "execute_vector_evidence_chunk_insert",
        "execute_vector_evidence_embedding_insert",
        "execute_vector_evidence_retrieval_event_insert",
        "src.app.api",
        "agentic_review.js",
    ):
        assert marker not in source


def test_api_ui_dependencies_and_protected_decision_modules_are_unchanged():
    expected = {
        "requirements.txt": "96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f",
        "src/app/api.py": "e2eee82ef5c27d75d8326b260d7f9d6f8d55a717b762e64cadd0941de05b808c",
        "src/app/static/agentic_review.js": "1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b",
        "src/pipeline/application_scorer.py": "e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b",
        "src/pipeline/job_ranker.py": "5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54",
    }
    for relative_path, expected_hash in expected.items():
        assert hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )
