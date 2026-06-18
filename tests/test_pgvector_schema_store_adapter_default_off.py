from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pytest

from src.agents import vector_evidence_contract
from src.storage.vector_evidence import store


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "src/storage/vector_evidence/schema.sql"
STORE_PATH = ROOT / "src/storage/vector_evidence/store.py"


def _chunk() -> dict:
    payload = vector_evidence_contract.build_vector_evidence_chunk_candidate(
        chunk_type="job_description",
        evidence_text="Build reliable Python and machine learning systems.",
        metadata={
            "job_id": "job-1",
            "company": "Acme AI",
            "title": "ML Platform Engineer",
            "source": "greenhouse",
            "stage": "jd_intelligence",
            "agent_name": "jd_intelligence_agent",
            "trace_id": "trace-1",
            "run_id": "run-1",
            "resume_version": "resume-v4",
            "profile_version": "profile-v5",
            "created_at": "2026-06-18T17:00:00Z",
            "safety_flags": {"human_review_required": True},
            "read_only": True,
        },
    )
    assert payload["validation"]["is_valid"] is True
    return payload["chunk_candidate"]


def _assert_safety(payload: dict) -> None:
    safety = payload["safety_metadata"]
    expected = {
        "read_only": True,
        "advisory_only": True,
        "pgvector_schema_defined": True,
        "pgvector_store_adapter": True,
        "pgvector_installed_by_app": False,
        "schema_created": False,
        "migration_created": False,
        "embeddings_created": False,
        "provider_calls_made": False,
        "vector_db_connected": False,
        "did_read_database": False,
        "did_write_database": False,
        "pipeline_stage_added": False,
        "scoring_mutation": False,
        "ranking_mutation": False,
        "queue_mutation": False,
        "application_submission": False,
        "did_mutate_scoring": False,
        "did_change_ranking": False,
        "did_mutate_queue": False,
        "did_create_approval": False,
        "did_mutate_approval": False,
        "did_mutate_resume": False,
        "did_create_execution_request": False,
        "did_create_execution_launch_request": False,
        "did_execute_application": False,
        "did_submit_application": False,
        "mutation_authorized": False,
    }
    for key, value in expected.items():
        assert safety[key] is value

    assert payload["provider_backed_automated_agents"] == 0
    assert payload["live_provider_backed_automated_agents"] == 0
    assert payload["mutation_authorized_agents"] == 0
    assert payload["mutation_authorized_scoring_agents"] == 0
    assert payload["mutation_authorized_ranking_agents"] == 0
    assert payload["mutation_authorized_application_agents"] == 0


def test_pgvector_schema_file_exists_and_defines_required_tables():
    assert SCHEMA_PATH.exists()
    schema = SCHEMA_PATH.read_text(encoding="utf-8")

    for table in (
        "vector_evidence_chunks",
        "vector_evidence_embeddings",
        "vector_evidence_retrieval_events",
    ):
        assert f"CREATE TABLE IF NOT EXISTS {table}" in schema

    assert "embedding VECTOR NOT NULL" in schema
    assert "vector_dims(embedding) = embedding_dimension" in schema
    assert "CREATE EXTENSION" in schema
    assert "intentionally does not run CREATE EXTENSION" in schema
    assert "FROM pg_extension" in schema
    assert "extname = 'vector'" in schema


def test_schema_is_static_and_has_no_automatic_install_or_data_mutation():
    schema = SCHEMA_PATH.read_text(encoding="utf-8")

    assert "\nCREATE EXTENSION" not in schema
    assert "\nINSERT INTO" not in schema
    assert "\nUPDATE " not in schema
    assert "\nDELETE FROM" not in schema
    assert "automatic execution hook" in schema
    assert "No HNSW or IVFFlat index is created" in schema


def test_store_builds_chunk_insert_payload_from_contract_chunk():
    chunk = _chunk()
    before = deepcopy(chunk)

    payload = store.prepare_chunk_insert_payload(
        chunk,
        owner_user_id="owner-1",
        chunk_version=2,
        source_record_id="job-1",
        source_updated_at="2026-06-18T16:00:00Z",
    )

    assert chunk == before
    assert payload["table"] == "vector_evidence_chunks"
    assert "INSERT INTO vector_evidence_chunks" in payload["sql"]
    assert "ON CONFLICT (chunk_id)" in payload["sql"]
    assert payload["row"]["chunk_id"] == chunk["chunk_id"]
    assert payload["row"]["owner_user_id"] == "owner-1"
    assert payload["row"]["chunk_version"] == 2
    assert payload["row"]["normalized_text"] == chunk["evidence_text"]
    assert payload["row"]["content_hash"] == sha256(
        chunk["evidence_text"].encode("utf-8")
    ).hexdigest()
    assert payload["row"]["job_id"] == "job-1"
    assert payload["row"]["company"] == "Acme AI"
    assert payload["row"]["title"] == "ML Platform Engineer"
    assert payload["row"]["source"] == "greenhouse"
    assert payload["row"]["stage"] == "jd_intelligence"
    assert payload["row"]["agent_name"] == "jd_intelligence_agent"
    assert payload["row"]["trace_id"] == "trace-1"
    assert payload["row"]["run_id"] == "run-1"
    assert payload["row"]["resume_version"] == "resume-v4"
    assert payload["row"]["profile_version"] == "profile-v5"
    assert payload["row"]["metadata"] == chunk["metadata"]
    _assert_safety(payload)


def test_store_builds_embedding_payload_from_explicit_vector_only():
    vector = [0.125, -0.5, 1.0]
    before = deepcopy(vector)

    payload = store.prepare_embedding_insert_payload(
        chunk_id="chunk-1",
        embedding=vector,
        embedding_model_id="fixture-model-v1",
    )

    assert vector == before
    assert payload["table"] == "vector_evidence_embeddings"
    assert "INSERT INTO vector_evidence_embeddings" in payload["sql"]
    assert "%s::vector" in payload["sql"]
    assert payload["row"]["embedding"] == vector
    assert payload["row"]["embedding_dimension"] == 3
    assert payload["row"]["embedding_model_id"] == "fixture-model-v1"
    assert payload["params"][3] == "[0.125,-0.5,1]"
    assert payload["safety_metadata"]["embeddings_created"] is False
    assert payload["safety_metadata"]["provider_calls_made"] is False
    _assert_safety(payload)


def test_store_builds_privacy_minimized_retrieval_event_payload():
    event = {
        "owner_user_id": "owner-1",
        "request_id": "request-1",
        "query_hash": "query-sha256",
        "query_purpose": "operator_evidence_review",
        "chunk_type": "job_description",
        "metadata": {"company_filter": "Acme AI", "read_only": True},
        "job_id": "job-1",
        "company": "Acme AI",
        "stage": "operator_review",
        "agent_name": "vector_evidence_adapter",
        "trace_id": "trace-1",
        "run_id": "run-1",
        "embedding_model_id": "fixture-model-v1",
        "embedding_dimension": 3,
        "top_k": 5,
        "result_count": 2,
        "fallback_reason": "",
        "latency_ms": 12,
        "backend_status": "fixture_ready",
    }
    before = deepcopy(event)

    first = store.prepare_retrieval_event_insert_payload(event)
    second = store.prepare_retrieval_event_insert_payload(event)

    assert event == before
    assert first == second
    assert first["table"] == "vector_evidence_retrieval_events"
    assert "INSERT INTO vector_evidence_retrieval_events" in first["sql"]
    assert first["row"]["retrieval_event_id"].startswith("vector-retrieval:")
    assert first["row"]["metadata"] == event["metadata"]
    assert "query_text" not in first["row"]
    _assert_safety(first)


def test_store_validates_required_fields_and_rejects_implicit_embeddings():
    chunk = _chunk()

    with pytest.raises(ValueError, match="owner_user_id is required"):
        store.prepare_chunk_insert_payload(chunk, owner_user_id="")
    with pytest.raises(ValueError, match="chunk_id is required"):
        store.prepare_chunk_insert_payload(
            {**chunk, "chunk_id": ""},
            owner_user_id="owner-1",
        )
    with pytest.raises(ValueError, match="must not include an embedding"):
        store.prepare_chunk_insert_payload(
            {**chunk, "embedding": [0.1]},
            owner_user_id="owner-1",
        )
    with pytest.raises(ValueError, match="non-empty explicit vector"):
        store.prepare_embedding_insert_payload(
            chunk_id="chunk-1",
            embedding=[],
            embedding_model_id="fixture-model-v1",
        )
    with pytest.raises(ValueError, match="query_text must not be stored"):
        store.prepare_retrieval_event_insert_payload(
            {
                "owner_user_id": "owner-1",
                "query_text": "raw private query",
                "top_k": 5,
            }
        )


def test_default_execution_path_opens_no_connection_and_calls_no_executor():
    prepared = store.prepare_chunk_insert_payload(
        _chunk(),
        owner_user_id="owner-1",
    )
    before = deepcopy(prepared)

    result = store.execute_prepared_pgvector_payload(prepared)

    assert prepared == before
    assert result["status"] == "pgvector_store_executor_not_configured"
    assert result["executed"] is False
    assert result["executor_required"] is True
    _assert_safety(result)


def test_store_supports_only_explicitly_injected_fake_executor():
    prepared = store.prepare_embedding_insert_payload(
        chunk_id="chunk-1",
        embedding=[0.25, 0.75],
        embedding_model_id="fixture-model-v1",
    )
    calls = []

    def fake_executor(payload):
        calls.append(deepcopy(payload))
        return {"row_count": 1, "driver": "fake"}

    result = store.execute_prepared_pgvector_payload(
        prepared,
        executor=fake_executor,
    )

    assert len(calls) == 1
    assert calls[0] == prepared
    assert calls[0] is not prepared
    assert result["status"] == "pgvector_store_executor_completed"
    assert result["executed"] is True
    assert result["executor_result"] == {"row_count": 1, "driver": "fake"}


def test_store_source_has_no_driver_provider_pipeline_or_mutation_runtime():
    source = STORE_PATH.read_text(encoding="utf-8")

    for marker in (
        "import psycopg",
        "import psycopg2",
        "import pgvector",
        "DATABASE_URL",
        "subprocess",
        "psql",
        "connect(",
        ".commit(",
        "create_embedding(",
        "embeddings.create(",
        "openai",
        "anthropic",
        "llm_client",
        "src.pipeline",
        "src.app.api",
        "src.app.services",
        "agentic_review.js",
        "score_resume_job_match(",
        "rank_jobs(",
        "create_approval_request(",
        "record_approval_decision(",
        "create_execution_request(",
        "create_execution_launch_request(",
        "execute_application(",
        "submit_application(",
    ):
        assert marker not in source


def test_no_api_ui_pipeline_scoring_ranking_queue_or_dependency_change():
    protected_hashes = {
        "src/app/api.py": (
            "e2bb58c1c22eba596d73cc18ca336b57b7f9e3cf41ebaf26ec8cb549d10339f3"
        ),
        "src/app/static/agentic_review.js": (
            "2bbaf699e5b65ec0fd2022246f1d2cb161ecf9bdaa0b5ed7234e12789346c790"
        ),
        "src/pipeline/collector.py": (
            "5d30b4e3b7ada5fd94c5dee0344e87c3dbe978a149d16dd4503f7a5d167b16a5"
        ),
        "src/pipeline/application_scorer.py": (
            "e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b"
        ),
        "src/pipeline/job_ranker.py": (
            "5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54"
        ),
        "application_execution_queue.py": (
            "c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0"
        ),
        "requirements.txt": (
            "96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f"
        ),
    }
    for relative_path, expected_hash in protected_hashes.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )

    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").lower()
    assert "pgvector" not in requirements
