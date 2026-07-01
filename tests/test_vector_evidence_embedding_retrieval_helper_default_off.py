# phase56b legacy guard marker: changes_only 912a02bbcf180962ca1b22aedf9dca0b5465b90f4add2444f328c99ccfc6e2d6 8e37487335a2b0bf18fd196554c11509d0e5ee0428244ce9fafce3c3e195e5bd
# phase56a legacy guard marker: changes_only f9137ef3f8d1cc27fe08f3a592f1cff977a124cb6132a91394ee8350674bea6f 912a02bbcf180962ca1b22aedf9dca0b5465b90f4add2444f328c99ccfc6e2d6
# phase26c legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c
# phase26b legacy guard marker: changes_only f9137ef3f8d1cc27fe08f3a592f1cff977a124cb6132a91394ee8350674bea6f
# phase23f legacy guard marker: changes_only f9137ef3f8d1cc27fe08f3a592f1cff977a124cb6132a91394ee8350674bea6f 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
# phase23f legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
import hashlib
from copy import deepcopy
from pathlib import Path

from src.storage.vector_evidence import embedding_retrieval


ROOT = Path(__file__).resolve().parents[1]


def _kwargs():
    return {
        "enabled": True,
        "query_text": "reliable semantic retrieval systems",
        "owner_user_id": "owner-phase-9c",
        "run_id": "run-phase-9c",
        "job_id": "job-phase-9c",
        "embedding_model_id": "fixture-model",
        "expected_dimension": 3,
        "top_k": 3,
        "filters": {"chunk_type": "job_description"},
    }


def _assert_safety(payload, *, called, created, attempted, read):
    safety = payload["safety_metadata"]
    assert safety["read_only"] is True
    assert safety["advisory_only"] is True
    assert safety["embedding_retrieval_enabled"] is (
        payload["embedding_retrieval_enabled"]
    )
    assert safety["provider_calls_made"] is called
    assert safety["embeddings_created"] is created
    assert safety["read_attempted"] is attempted
    assert safety["did_read_database"] is read
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


def test_default_off_skips_provider_and_database():
    provider_calls = []
    db_calls = []

    payload = embedding_retrieval.run_vector_evidence_embedding_retrieval(
        query_text="semantic retrieval",
        provider=lambda request: provider_calls.append(request) or [0.1, 0.2, 0.3],
        db_executor=lambda request: db_calls.append(request),
    )

    assert payload["status"] == "embedding_retrieval_skipped_default_off"
    assert provider_calls == []
    assert db_calls == []
    _assert_safety(
        payload,
        called=False,
        created=False,
        attempted=False,
        read=False,
    )


def test_enabled_without_provider_is_not_configured():
    payload = embedding_retrieval.run_vector_evidence_embedding_retrieval(
        **_kwargs()
    )

    assert payload["status"] == "embedding_retrieval_not_configured"
    assert payload["errors"] == ["injected_provider_required"]
    _assert_safety(
        payload,
        called=False,
        created=False,
        attempted=False,
        read=False,
    )


def test_fake_provider_prepares_query_embedding_without_reading():
    source = _kwargs()
    before = deepcopy(source)
    provider_calls = []

    payload = embedding_retrieval.run_vector_evidence_embedding_retrieval(
        **source,
        provider=lambda request: provider_calls.append(deepcopy(request))
        or {"embedding": [0.25, -0.5, 1]},
    )

    assert source == before
    assert len(provider_calls) == 1
    assert payload["status"] == "embedding_retrieval_prepared"
    assert payload["query_embedding"] == [0.25, -0.5, 1.0]
    assert payload["embedding_dimension"] == 3
    assert payload["prepared_retrieval"]["operation"] == (
        "prepare_vector_evidence_retrieval_select"
    )
    assert payload["prepared_retrieval"]["row"]["owner_user_id"] == (
        "owner-phase-9c"
    )
    assert payload["prepared_retrieval"]["row"]["filters"] == {
        "chunk_type": "job_description",
        "job_id": "job-phase-9c",
    }
    assert payload["read_attempted"] is False
    _assert_safety(
        payload,
        called=True,
        created=True,
        attempted=False,
        read=False,
    )


def test_fake_reader_reads_only_when_explicitly_enabled():
    calls = []
    rows = [
        {
            "chunk_id": "chunk-phase-9c",
            "chunk_type": "job_description",
            "evidence_text": "Reliable semantic retrieval systems.",
            "retrieval_score": 0.91,
        }
    ]

    def reader(request):
        calls.append(deepcopy(request))
        return {"rows": deepcopy(rows)}

    without_read = embedding_retrieval.run_vector_evidence_embedding_retrieval(
        **_kwargs(),
        provider=lambda _request: [0.1, 0.2, 0.3],
        db_executor=reader,
    )
    with_read = embedding_retrieval.run_vector_evidence_embedding_retrieval(
        **_kwargs(),
        provider=lambda _request: [0.1, 0.2, 0.3],
        read_enabled=True,
        db_executor=reader,
    )

    assert without_read["status"] == "embedding_retrieval_prepared"
    assert without_read["read_attempted"] is False
    assert len(calls) == 1
    assert with_read["status"] == "embedding_retrieval_completed"
    assert with_read["read_executed"] is True
    assert with_read["retrieval_candidates"] == rows
    assert with_read["result_count"] == 1
    assert calls[0]["operation"] == "select_vector_evidence_retrieval_candidates"
    _assert_safety(
        with_read,
        called=True,
        created=True,
        attempted=True,
        read=True,
    )


def test_invalid_query_and_ids_are_rejected_before_provider_call():
    calls = []
    invalid = _kwargs()
    invalid.update(
        {
            "query_text": "",
            "owner_user_id": "",
            "run_id": "",
            "job_id": "",
        }
    )

    payload = embedding_retrieval.run_vector_evidence_embedding_retrieval(
        **invalid,
        provider=lambda request: calls.append(request) or [0.1, 0.2, 0.3],
    )

    assert payload["status"] == "embedding_retrieval_invalid_request"
    assert payload["errors"] == [
        "query_text_required",
        "owner_user_id_required",
        "run_id_required",
        "job_id_required",
    ]
    assert calls == []


def test_invalid_embedding_and_provider_exception_are_non_blocking():
    invalid = embedding_retrieval.run_vector_evidence_embedding_retrieval(
        **_kwargs(),
        provider=lambda _request: [0.1, "invalid", 0.3],
    )

    def failing_provider(_request):
        raise RuntimeError("fixture failure")

    failed = embedding_retrieval.run_vector_evidence_embedding_retrieval(
        **_kwargs(),
        provider=failing_provider,
    )

    assert invalid["status"] == "embedding_retrieval_provider_failed_non_blocking"
    assert invalid["errors"] == ["embedding_vector_values_must_be_numeric"]
    assert failed["status"] == "embedding_retrieval_provider_failed_non_blocking"
    assert failed["errors"] == ["RuntimeError"]
    _assert_safety(
        failed,
        called=True,
        created=False,
        attempted=False,
        read=False,
    )


def test_read_enabled_without_executor_is_safe_and_never_writes():
    payload = embedding_retrieval.run_vector_evidence_embedding_retrieval(
        **_kwargs(),
        provider=lambda _request: [0.1, 0.2, 0.3],
        read_enabled=True,
    )

    assert payload["status"] == "embedding_retrieval_read_not_configured"
    assert payload["errors"] == ["injected_db_executor_required"]
    assert payload["read_attempted"] is True
    assert payload["read_executed"] is False
    _assert_safety(
        payload,
        called=True,
        created=True,
        attempted=True,
        read=False,
    )


def test_zero_agent_counts_and_no_runtime_provider_sdk_or_write_wiring():
    payload = embedding_retrieval.run_vector_evidence_embedding_retrieval()
    assert payload["provider_backed_automated_agents"] == 0
    assert payload["live_provider_backed_automated_agents"] == 0
    assert payload["mutation_authorized_agents"] == 0
    assert payload["mutation_authorized_scoring_agents"] == 0
    assert payload["mutation_authorized_ranking_agents"] == 0
    assert payload["mutation_authorized_application_agents"] == 0

    source = (
        ROOT / "src/storage/vector_evidence/embedding_retrieval.py"
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
        "execute_vector_evidence_chunk_insert",
        "execute_vector_evidence_embedding_insert",
        "execute_vector_evidence_retrieval_event_insert",
    ):
        assert marker not in source


def test_api_ui_pipeline_dependencies_and_protected_decision_modules_are_unchanged():
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
