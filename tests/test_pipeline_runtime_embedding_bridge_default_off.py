# phase56b legacy guard marker: changes_only 56d8d73b5891c88ba482fe8a28a634010b5664408ddf35aabcbc89c8aee5005f 1ff2a73993300f391aa1fb8151a4d225e803b6c5d499e311faa5058efc4b965c
# phase56a legacy guard marker: changes_only 85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96 56d8d73b5891c88ba482fe8a28a634010b5664408ddf35aabcbc89c8aee5005f
# phase26c legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c
# phase26b legacy guard marker: changes_only 85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96
# phase23f legacy guard marker: changes_only 85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
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
        "run_id": "run-phase-9h",
        "job_id": "job-phase-9h",
        "query_text": "runtime semantic evidence",
        "job_payload": {"id": "job-phase-9h"},
        "vector_evidence_service": _service,
        "embedding_retrieval_enabled": True,
        "embedding_retrieval_owner_user_id": "owner-phase-9h",
        "embedding_retrieval_model_id": "fixture-model",
        "embedding_retrieval_dimension": 3,
        "embedding_retrieval_top_k": 3,
        "embedding_retrieval_filters": {
            "chunk_type": "job_description"
        },
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


def test_default_hook_does_not_use_runtime_embedding_bridge():
    runtime_calls = []

    payload = vector_evidence_pipeline_hook.run_vector_evidence_pipeline_hook(
        enabled=True,
        vector_evidence_service=_service,
        runtime_embedding_service_helper=lambda **kwargs: runtime_calls.append(
            kwargs
        ),
    )

    assert runtime_calls == []
    assert payload["safety_metadata"]["runtime_embedding_bridge_enabled"] is False
    assert payload["safety_metadata"]["runtime_embedding_attempted"] is False
    _assert_non_mutating(payload)


def test_explicit_disabled_bridge_preserves_direct_provider_path():
    runtime_calls = []
    reader_calls = []

    def reader(request):
        reader_calls.append(deepcopy(request))
        return {"rows": []}

    payload = vector_evidence_pipeline_hook.run_vector_evidence_pipeline_hook(
        **_base_kwargs(),
        runtime_embedding_bridge_enabled=False,
        runtime_embedding_provider=lambda _request: [9, 9, 9],
        runtime_embedding_service_helper=lambda **kwargs: runtime_calls.append(
            kwargs
        ),
        embedding_retrieval_provider=lambda _request: [0.1, 0.2, 0.3],
        embedding_retrieval_db_executor=reader,
    )

    assert runtime_calls == []
    assert len(reader_calls) == 1
    assert "runtime_embedding_bridge" not in (
        payload["evidence_context"]["semantic_retrieval"]
    )
    assert payload["safety_metadata"]["runtime_embedding_attempted"] is False
    _assert_non_mutating(payload)


def test_fake_runtime_provider_and_reader_attach_semantic_evidence():
    provider_calls = []
    reader_calls = []
    rows = [
        {
            "chunk_id": "chunk-phase-9h",
            "chunk_type": "job_description",
            "evidence_text": "Runtime semantic evidence.",
            "retrieval_score": 0.95,
        }
    ]

    def provider(request):
        provider_calls.append(deepcopy(request))
        return [0.1, 0.2, 0.3]

    def reader(request):
        reader_calls.append(deepcopy(request))
        return {"rows": deepcopy(rows)}

    payload = vector_evidence_pipeline_hook.run_vector_evidence_pipeline_hook(
        **_base_kwargs(),
        runtime_embedding_bridge_enabled=True,
        runtime_embedding_provider=provider,
        embedding_retrieval_db_executor=reader,
    )

    semantic = payload["evidence_context"]["semantic_retrieval"]
    assert semantic["status"] == "embedding_retrieval_completed"
    assert semantic["retrieval_candidates"] == rows
    assert semantic["runtime_embedding_bridge"]["status"] == (
        "embedding_runtime_adapter_embedding_ready"
    )
    assert semantic["runtime_embedding_bridge"][
        "runtime_embedding_attempted"
    ] is True
    assert len(provider_calls) == 1
    assert len(reader_calls) == 1
    safety = payload["safety_metadata"]
    assert safety["runtime_embedding_bridge_enabled"] is True
    assert safety["runtime_embedding_attempted"] is True
    assert safety["semantic_evidence_attached"] is True
    assert safety["provider_calls_made"] is True
    assert safety["embeddings_created"] is True
    assert safety["did_read_database"] is True
    _assert_non_mutating(payload)


def test_runtime_provider_exception_is_non_blocking():
    def provider(_request):
        raise RuntimeError("fixture runtime provider failure")

    payload = vector_evidence_pipeline_hook.run_vector_evidence_pipeline_hook(
        **_base_kwargs(),
        runtime_embedding_bridge_enabled=True,
        runtime_embedding_provider=provider,
        embedding_retrieval_db_executor=lambda _request: {"rows": []},
    )

    semantic = payload["evidence_context"]["semantic_retrieval"]
    assert semantic["status"] == (
        "embedding_retrieval_provider_failed_non_blocking"
    )
    assert semantic["runtime_embedding_bridge"]["status"] == (
        "embedding_runtime_adapter_failed_non_blocking"
    )
    assert payload["safety_metadata"]["runtime_embedding_attempted"] is True
    assert payload["safety_metadata"]["semantic_evidence_attached"] is False
    assert payload["safety_metadata"]["did_read_database"] is False
    _assert_non_mutating(payload)


def test_reader_exception_is_non_blocking():
    def reader(_request):
        raise RuntimeError("fixture reader failure")

    payload = vector_evidence_pipeline_hook.run_vector_evidence_pipeline_hook(
        **_base_kwargs(),
        runtime_embedding_bridge_enabled=True,
        runtime_embedding_provider=lambda _request: [0.1, 0.2, 0.3],
        embedding_retrieval_db_executor=reader,
    )

    semantic = payload["evidence_context"]["semantic_retrieval"]
    assert semantic["status"] == (
        "embedding_retrieval_read_failed_non_blocking"
    )
    assert semantic["errors"] == ["RuntimeError"]
    assert payload["safety_metadata"]["semantic_evidence_attached"] is False
    assert payload["safety_metadata"]["did_read_database"] is False
    _assert_non_mutating(payload)


def test_zero_agent_counts_and_no_mutation_or_application_wiring():
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
        "record_approval_decision(",
        "mutate_resume(",
        "create_execution_request(",
        "create_execution_launch_request(",
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
        "src/app/api.py": "85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96",
        "src/app/static/agentic_review.js": "1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b",
        "src/pipeline/application_scorer.py": "e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b",
        "src/pipeline/job_ranker.py": "5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54",
    }
    for relative_path, expected_hash in expected.items():
        assert hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )
