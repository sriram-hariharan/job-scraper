# phase56b legacy guard marker: changes_only f388091d0d77f7bc0db4d9072ccabfbc526ac93e81aa949e1526c0b80302f2e8 ba479203ff176589f33ec4456046d8ad57e4fd491376923cc32090eae6693af1
# phase56a legacy guard marker: changes_only ccd2e74eed88a244fd05c430cacf7ba8a2867ac8959de00e21c64cd7fe2d3c39 f388091d0d77f7bc0db4d9072ccabfbc526ac93e81aa949e1526c0b80302f2e8
# phase26c legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c
# phase26b legacy guard marker: changes_only ccd2e74eed88a244fd05c430cacf7ba8a2867ac8959de00e21c64cd7fe2d3c39
# phase23f legacy guard marker: changes_only ccd2e74eed88a244fd05c430cacf7ba8a2867ac8959de00e21c64cd7fe2d3c39 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
# phase23f legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
import hashlib
from copy import deepcopy
from pathlib import Path

from src.storage.vector_evidence import embedding_indexing


ROOT = Path(__file__).resolve().parents[1]


def _chunk():
    return {
        "chunk_id": "chunk-phase-9b",
        "chunk_type": "job_description",
        "evidence_text": "Build reliable semantic retrieval systems.",
        "metadata": {
            "job_id": "job-phase-9b",
            "run_id": "run-phase-9b",
            "company": "ExampleCo",
            "read_only": True,
        },
    }


def _kwargs():
    return {
        "enabled": True,
        "chunks": [_chunk()],
        "owner_user_id": "owner-phase-9b",
        "run_id": "run-phase-9b",
        "job_id": "job-phase-9b",
        "embedding_model_id": "fixture-model",
        "expected_dimension": 3,
    }


def _assert_safety(payload, *, called, created, write_attempted, wrote):
    safety = payload["safety_metadata"]
    assert safety["embedding_indexing_enabled"] is (
        payload["embedding_indexing_enabled"]
    )
    assert safety["provider_calls_made"] is called
    assert safety["embeddings_created"] is created
    assert safety["write_attempted"] is write_attempted
    assert safety["did_write_database"] is wrote
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


def test_default_off_skips_provider_and_writer():
    provider_calls = []
    writer_calls = []

    payload = embedding_indexing.run_vector_evidence_embedding_indexing(
        chunks=[_chunk()],
        provider=lambda request: provider_calls.append(request) or [0.1, 0.2, 0.3],
        db_executor=lambda request: writer_calls.append(request),
    )

    assert payload["status"] == "embedding_indexing_skipped_default_off"
    assert provider_calls == []
    assert writer_calls == []
    _assert_safety(
        payload,
        called=False,
        created=False,
        write_attempted=False,
        wrote=False,
    )


def test_enabled_without_provider_is_not_configured():
    payload = embedding_indexing.run_vector_evidence_embedding_indexing(
        **_kwargs()
    )

    assert payload["status"] == "embedding_indexing_not_configured"
    assert payload["errors"] == ["injected_provider_required"]
    _assert_safety(
        payload,
        called=False,
        created=False,
        write_attempted=False,
        wrote=False,
    )


def test_fake_provider_prepares_embedding_backed_chunk_without_writing():
    source = _kwargs()
    before = deepcopy(source)
    provider_calls = []

    payload = embedding_indexing.run_vector_evidence_embedding_indexing(
        **source,
        provider=lambda request: provider_calls.append(deepcopy(request))
        or {"embedding": [0.25, -0.5, 1]},
    )

    assert source == before
    assert len(provider_calls) == 1
    assert payload["status"] == "embedding_indexing_prepared"
    assert payload["prepared_record_count"] == 1
    record = payload["prepared_records"][0]
    assert record["embedding"] == [0.25, -0.5, 1.0]
    assert record["embedding_dimension"] == 3
    assert record["prepared_chunk_insert"]["table"] == "vector_evidence_chunks"
    assert record["prepared_embedding_insert"]["table"] == (
        "vector_evidence_embeddings"
    )
    assert payload["write_attempted"] is False
    _assert_safety(
        payload,
        called=True,
        created=True,
        write_attempted=False,
        wrote=False,
    )


def test_fake_executor_writes_only_when_explicitly_enabled():
    calls = []

    def executor(request):
        calls.append(deepcopy(request))
        chunk_id = request["prepared_payload"]["row"]["chunk_id"]
        return {"rows": [{"chunk_id": chunk_id}]}

    without_write = embedding_indexing.run_vector_evidence_embedding_indexing(
        **_kwargs(),
        provider=lambda _request: [0.1, 0.2, 0.3],
        db_executor=executor,
    )
    with_write = embedding_indexing.run_vector_evidence_embedding_indexing(
        **_kwargs(),
        provider=lambda _request: [0.1, 0.2, 0.3],
        write_enabled=True,
        db_executor=executor,
    )

    assert without_write["status"] == "embedding_indexing_prepared"
    assert without_write["write_attempted"] is False
    assert len(calls) == 2
    assert with_write["status"] == "embedding_indexing_written"
    assert with_write["write_executed"] is True
    assert {call["prepared_payload"]["table"] for call in calls} == {
        "vector_evidence_chunks",
        "vector_evidence_embeddings",
    }
    _assert_safety(
        with_write,
        called=True,
        created=True,
        write_attempted=True,
        wrote=True,
    )


def test_invalid_chunk_text_and_ids_are_rejected_before_provider_call():
    calls = []
    invalid = _kwargs()
    invalid["owner_user_id"] = ""
    invalid["chunks"] = [
        {
            "chunk_id": "",
            "chunk_type": "job_description",
            "evidence_text": "",
        }
    ]

    missing_owner = embedding_indexing.run_vector_evidence_embedding_indexing(
        **invalid,
        provider=lambda request: calls.append(request) or [0.1, 0.2, 0.3],
    )
    invalid["owner_user_id"] = "owner-phase-9b"
    invalid_chunk = embedding_indexing.run_vector_evidence_embedding_indexing(
        **invalid,
        provider=lambda request: calls.append(request) or [0.1, 0.2, 0.3],
    )

    assert missing_owner["status"] == "embedding_indexing_invalid_request"
    assert "owner_user_id_required" in missing_owner["errors"]
    assert invalid_chunk["status"] == "embedding_indexing_invalid_request"
    assert "chunk_0:chunk_id_required" in invalid_chunk["errors"]
    assert "chunk_0:chunk_text_required" in invalid_chunk["errors"]
    assert calls == []


def test_invalid_embedding_and_provider_exception_are_non_blocking():
    invalid = embedding_indexing.run_vector_evidence_embedding_indexing(
        **_kwargs(),
        provider=lambda _request: [0.1, "invalid", 0.3],
    )

    def failing_provider(_request):
        raise RuntimeError("fixture failure")

    failed = embedding_indexing.run_vector_evidence_embedding_indexing(
        **_kwargs(),
        provider=failing_provider,
    )

    assert invalid["status"] == "embedding_indexing_provider_failed_non_blocking"
    assert invalid["errors"] == ["embedding_vector_values_must_be_numeric"]
    assert failed["status"] == "embedding_indexing_provider_failed_non_blocking"
    assert failed["errors"] == ["RuntimeError"]
    _assert_safety(
        failed,
        called=True,
        created=False,
        write_attempted=False,
        wrote=False,
    )


def test_zero_agent_counts_and_no_runtime_provider_sdk_wiring():
    payload = embedding_indexing.run_vector_evidence_embedding_indexing()
    assert payload["provider_backed_automated_agents"] == 0
    assert payload["live_provider_backed_automated_agents"] == 0
    assert payload["mutation_authorized_agents"] == 0
    assert payload["mutation_authorized_scoring_agents"] == 0
    assert payload["mutation_authorized_ranking_agents"] == 0
    assert payload["mutation_authorized_application_agents"] == 0

    source = (
        ROOT / "src/storage/vector_evidence/embedding_indexing.py"
    ).read_text(encoding="utf-8").lower()
    for marker in (
        "import openai",
        "from openai",
        "langchain",
        "sentence_transformers",
        "os.environ",
        "requests.",
        "httpx.",
        "src.app",
        "src.pipeline",
    ):
        assert marker not in source


def test_api_ui_pipeline_dependencies_and_protected_decision_modules_are_unchanged():
    expected = {
        "requirements.txt": "96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f",
        "src/app/api.py": "ccd2e74eed88a244fd05c430cacf7ba8a2867ac8959de00e21c64cd7fe2d3c39",
        "src/app/static/agentic_review.js": "1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b",
        "src/pipeline/collector.py": "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405",
        "src/pipeline/application_scorer.py": "e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b",
        "src/pipeline/job_ranker.py": "5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54",
    }
    for relative_path, expected_hash in expected.items():
        assert hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )
