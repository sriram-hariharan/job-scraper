# phase26c legacy guard marker: changes_only bb3b1f351b9f3aeac197a3077ce4403f649a17ff81247fb1d0e41eeacc3a9821 c71e2057276080e36fce4bec48a881753d8e09d7d1b49e7d0676d4a0665f32c9
# phase26b legacy guard marker: changes_only 96f9cd7e7f3f877a147d612ad1394b8fcdd4671244de25c9f99c34795304a8ff
# phase23f legacy guard marker: changes_only 96f9cd7e7f3f877a147d612ad1394b8fcdd4671244de25c9f99c34795304a8ff 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab c71e2057276080e36fce4bec48a881753d8e09d7d1b49e7d0676d4a0665f32c9 bb3b1f351b9f3aeac197a3077ce4403f649a17ff81247fb1d0e41eeacc3a9821
# phase23f legacy guard marker: changes_only bb3b1f351b9f3aeac197a3077ce4403f649a17ff81247fb1d0e41eeacc3a9821
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from src.agents import vector_evidence_contract
from src.storage.vector_evidence import store


ROOT = Path(__file__).resolve().parents[1]


class FakeCursor:
    def __init__(self, rows=None, columns=None):
        self.rows = list(rows or [])
        self.description = [(column,) for column in (columns or [])]
        self.executed = []
        self.closed = False

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def fetchall(self):
        return list(self.rows)

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self, cursor):
        self.fake_cursor = cursor
        self.cursor_calls = 0

    def cursor(self):
        self.cursor_calls += 1
        return self.fake_cursor


def _chunk() -> dict:
    payload = vector_evidence_contract.build_vector_evidence_chunk_candidate(
        chunk_type="job_description",
        evidence_text="Build reliable machine learning systems.",
        metadata={
            "job_id": "job-1",
            "company": "Acme AI",
            "title": "ML Platform Engineer",
            "source": "greenhouse",
            "stage": "jd_intelligence",
            "agent_name": "jd_intelligence_agent",
            "trace_id": "trace-1",
            "run_id": "run-1",
            "created_at": "2026-06-18T17:00:00Z",
            "read_only": True,
        },
    )
    return payload["chunk_candidate"]


def _chunk_prepared() -> dict:
    return store.prepare_chunk_insert_payload(
        _chunk(),
        owner_user_id="owner-1",
        source_record_id="job-1",
    )


def _embedding_prepared() -> dict:
    return store.prepare_embedding_insert_payload(
        chunk_id=_chunk()["chunk_id"],
        embedding=[0.25, -0.5, 1.0],
        embedding_model_id="fixture-model-v1",
    )


def _event_prepared() -> dict:
    return store.prepare_retrieval_event_insert_payload(
        {
            "owner_user_id": "owner-1",
            "request_id": "request-1",
            "query_hash": "query-hash",
            "query_purpose": "operator_evidence_review",
            "top_k": 5,
            "result_count": 1,
            "backend_status": "fixture_ready",
        }
    )


def _assert_no_mutation(payload: dict) -> None:
    safety = payload["safety_metadata"]
    assert safety["pgvector_store_db_executor"] is True
    assert safety["db_executor_required"] is True
    assert safety["embeddings_created"] is False
    assert safety["provider_calls_made"] is False
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
    assert safety["pipeline_stage_added"] is False
    assert safety["auto_apply_enabled"] is False
    assert safety["mutation_authorized"] is False
    assert payload["provider_backed_automated_agents"] == 0
    assert payload["live_provider_backed_automated_agents"] == 0
    assert payload["mutation_authorized_agents"] == 0
    assert payload["mutation_authorized_scoring_agents"] == 0
    assert payload["mutation_authorized_ranking_agents"] == 0
    assert payload["mutation_authorized_application_agents"] == 0


def test_no_executor_returns_not_configured_and_writes_nothing():
    operations = (
        store.execute_pgvector_schema_setup(),
        store.execute_vector_evidence_chunk_insert(_chunk_prepared()),
        store.execute_vector_evidence_embedding_insert(_embedding_prepared()),
        store.execute_vector_evidence_retrieval_event_insert(_event_prepared()),
    )

    for payload in operations:
        assert payload["status"] == "pgvector_store_db_executor_not_configured"
        assert payload["executed"] is False
        assert payload["db_executor_supplied"] is False
        safety = payload["safety_metadata"]
        assert safety["db_executor_supplied"] is False
        assert safety["schema_setup_executed"] is False
        assert safety["chunks_written"] is False
        assert safety["embeddings_written"] is False
        assert safety["retrieval_events_written"] is False
        assert safety["did_write_database"] is False
        _assert_no_mutation(payload)


def test_explicit_fake_executor_receives_schema_setup_sql():
    calls = []

    def fake_executor(request):
        calls.append(deepcopy(request))
        return {"schema_applied": True, "driver": "fake"}

    payload = store.execute_pgvector_schema_setup(db_executor=fake_executor)

    assert len(calls) == 1
    assert "CREATE TABLE IF NOT EXISTS vector_evidence_chunks" in calls[0]["sql"]
    assert calls[0]["params"] == ()
    assert payload["status"] == "pgvector_schema_setup_executed"
    assert payload["executed"] is True
    assert payload["executor_result"]["schema_applied"] is True
    assert payload["safety_metadata"]["schema_setup_executed"] is True
    assert payload["safety_metadata"]["did_write_database"] is True
    _assert_no_mutation(payload)


def test_explicit_fake_connection_receives_chunk_insert_query_and_params():
    prepared = _chunk_prepared()
    before = deepcopy(prepared)
    cursor = FakeCursor(
        rows=[(prepared["row"]["chunk_id"],)],
        columns=["chunk_id"],
    )
    connection = FakeConnection(cursor)

    payload = store.execute_vector_evidence_chunk_insert(
        prepared,
        db_executor=connection,
    )

    assert prepared == before
    assert connection.cursor_calls == 1
    assert len(cursor.executed) == 1
    executed_sql, executed_params = cursor.executed[0]
    normalized_sql = " ".join(executed_sql.split())

    assert "INSERT INTO vector_evidence_chunks" in normalized_sql
    assert "chunk_id" in normalized_sql
    assert "RETURNING chunk_id" in normalized_sql
    assert len(executed_params) == len(prepared["params"])
    assert executed_params[0] == prepared["params"][0]
    assert cursor.closed is True
    assert payload["rows"] == [{"chunk_id": prepared["row"]["chunk_id"]}]
    assert payload["safety_metadata"]["chunks_written"] is True
    assert payload["safety_metadata"]["did_write_database"] is True
    _assert_no_mutation(payload)


def test_embedding_insert_requires_explicit_vector_and_uses_fake_executor():
    prepared = _embedding_prepared()
    calls = []

    def fake_executor(request):
        calls.append(deepcopy(request))
        return {"rows": [{"chunk_id": request["prepared_payload"]["row"]["chunk_id"]}]}

    payload = store.execute_vector_evidence_embedding_insert(
        prepared,
        db_executor=fake_executor,
    )

    assert len(calls) == 1
    assert calls[0]["prepared_payload"]["row"]["embedding"] == [0.25, -0.5, 1.0]
    assert "%s::vector" in calls[0]["sql"]
    assert payload["safety_metadata"]["embeddings_written"] is True
    assert payload["safety_metadata"]["embeddings_created"] is False
    assert payload["safety_metadata"]["provider_calls_made"] is False
    _assert_no_mutation(payload)


def test_retrieval_event_insert_uses_explicit_prepared_payload():
    prepared = _event_prepared()
    calls = []

    payload = store.execute_vector_evidence_retrieval_event_insert(
        prepared,
        db_executor=lambda request: calls.append(deepcopy(request))
        or {"rows": [{"retrieval_event_id": prepared["row"]["retrieval_event_id"]}]},
    )

    assert len(calls) == 1
    assert "INSERT INTO vector_evidence_retrieval_events" in calls[0]["sql"]
    assert calls[0]["params"] == prepared["params"]
    assert payload["safety_metadata"]["retrieval_events_written"] is True
    assert payload["safety_metadata"]["did_write_database"] is True
    _assert_no_mutation(payload)


def test_retrieval_select_uses_fake_executor_result_and_normalizes_output():
    prepared = store.prepare_vector_evidence_retrieval_select_payload(
        owner_user_id="owner-1",
        query_embedding=[0.25, -0.5, 1.0],
        embedding_model_id="fixture-model-v1",
        filters={"chunk_type": "job_description", "job_id": "job-1"},
        top_k=3,
    )
    before = deepcopy(prepared)
    rows = [
        {
            "chunk_id": "chunk-1",
            "chunk_type": "job_description",
            "evidence_text": "Build reliable machine learning systems.",
            "metadata": {"job_id": "job-1"},
            "vector_distance": 0.1,
            "retrieval_score": 0.9,
        }
    ]

    payload = store.select_vector_evidence_retrieval_candidates(
        prepared,
        db_executor=lambda request: {"rows": deepcopy(rows), "driver": "fake"},
    )

    assert prepared == before
    assert prepared["params"][:2] == (
        "[0.25,-0.5,1]",
        "[0.25,-0.5,1]",
    )
    assert "chunks.owner_user_id = %s" in prepared["sql"]
    assert "ORDER BY vector_distance ASC" in prepared["sql"]
    assert payload["status"] == "pgvector_retrieval_candidates_selected"
    assert payload["retrieval_candidates"] == rows
    assert payload["result_count"] == 1
    assert payload["safety_metadata"]["read_only"] is True
    assert payload["safety_metadata"]["advisory_only"] is True
    assert payload["safety_metadata"]["did_read_database"] is True
    assert payload["safety_metadata"]["did_write_database"] is False
    _assert_no_mutation(payload)


def test_retrieval_select_without_executor_is_safe_not_configured():
    prepared = store.prepare_vector_evidence_retrieval_select_payload(
        owner_user_id="owner-1",
        query_embedding=[1.0, 0.0],
        embedding_model_id="fixture-model-v1",
    )

    payload = store.select_vector_evidence_retrieval_candidates(prepared)

    assert payload["status"] == "pgvector_store_db_executor_not_configured"
    assert payload["executed"] is False
    assert payload["retrieval_candidates"] == []
    assert payload["result_count"] == 0
    assert payload["safety_metadata"]["db_executor_supplied"] is False
    assert payload["safety_metadata"]["did_read_database"] is False
    _assert_no_mutation(payload)


def test_store_executor_source_has_no_driver_provider_or_automatic_connection():
    source = (
        ROOT / "src/storage/vector_evidence/store.py"
    ).read_text(encoding="utf-8")

    for marker in (
        "import psycopg",
        "import psycopg2",
        "import pgvector",
        "DATABASE_URL",
        "subprocess",
        "psql",
        "create_embedding(",
        "embeddings.create(",
        "openai",
        "anthropic",
        "llm_client",
        "src.pipeline",
        "src.app.api",
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

    assert ".commit(" not in source
    assert "db_executor.cursor()" in source


def test_no_api_ui_pipeline_schema_or_dependency_change():
    protected_hashes = {
        "src/app/api.py": ("96f9cd7e7f3f877a147d612ad1394b8fcdd4671244de25c9f99c34795304a8ff"),
        "src/app/static/agentic_review.js": ("bb3b1f351b9f3aeac197a3077ce4403f649a17ff81247fb1d0e41eeacc3a9821"),
        "src/pipeline/collector.py": ("73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405"),
        "src/pipeline/application_scorer.py": ("e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b"),
        "src/pipeline/job_ranker.py": ("5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54"),
        "application_execution_queue.py": ("c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0"),
        "requirements.txt": ("96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f"),
        "src/storage/vector_evidence/schema.sql": ("4b34a928393fcce6696a2f35d7ee62339b0483cc248daee3f0e57bdb50c11dff"),
    }
    for relative_path, expected_hash in protected_hashes.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )

    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").lower()
    for dependency in ("pgvector", "pinecone", "chromadb", "faiss", "langgraph"):
        assert dependency not in requirements
