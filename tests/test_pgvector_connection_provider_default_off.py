import importlib
from hashlib import sha256
from pathlib import Path

from src.storage.vector_evidence import connection


ROOT = Path(__file__).resolve().parents[1]


class FakeConnection:
    pass


def _assert_safety(payload: dict, *, opened: bool = False) -> None:
    safety = payload["safety_metadata"]
    assert safety["pgvector_connection_provider"] is True
    assert safety["default_off"] is True
    assert safety["db_connection_opened"] is opened
    assert safety["db_executor_created"] is opened
    assert safety["schema_setup_executed"] is False
    assert safety["chunks_written"] is False
    assert safety["embeddings_written"] is False
    assert safety["retrieval_events_written"] is False
    assert safety["embeddings_created"] is False
    assert safety["provider_calls_made"] is False
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
    assert safety["pipeline_stage_added"] is False
    assert safety["auto_apply_enabled"] is False
    assert safety["mutation_authorized"] is False
    assert payload["provider_backed_automated_agents"] == 0
    assert payload["live_provider_backed_automated_agents"] == 0
    assert payload["mutation_authorized_agents"] == 0
    assert payload["mutation_authorized_scoring_agents"] == 0
    assert payload["mutation_authorized_ranking_agents"] == 0
    assert payload["mutation_authorized_application_agents"] == 0


def test_missing_enable_flag_does_not_open_connection():
    calls = []
    payload = connection.build_vector_evidence_db_executor(
        environ={"DATABASE_URL": "postgres://fixture"},
        connector=lambda url: calls.append(url),
    )

    assert calls == []
    assert payload["status"] == "pgvector_connection_provider_disabled"
    assert payload["connection"] is None
    assert payload["db_executor"] is None
    _assert_safety(payload)


def test_explicit_false_flag_does_not_open_connection():
    calls = []
    payload = connection.build_vector_evidence_db_executor(
        enabled=False,
        database_url="postgres://fixture",
        connector=lambda url: calls.append(url),
    )

    assert calls == []
    assert payload["status"] == "pgvector_connection_provider_disabled"
    _assert_safety(payload)


def test_enabled_flag_with_missing_config_is_safe():
    calls = []
    payload = connection.build_vector_evidence_db_executor(
        enabled=True,
        environ={},
        connector=lambda url: calls.append(url),
    )

    assert calls == []
    assert payload["status"] == "pgvector_connection_provider_missing_config"
    assert payload["database_url_configured"] is False
    _assert_safety(payload)


def test_enabled_fake_connector_creates_connection_executor_payload():
    calls = []
    fake_connection = FakeConnection()

    def fake_connector(database_url):
        calls.append(database_url)
        return fake_connection

    payload = connection.build_vector_evidence_db_executor(
        environ={
            "APPLYLENS_VECTOR_EVIDENCE_PGVECTOR_ENABLED": "true",
            "APPLYLENS_VECTOR_EVIDENCE_DATABASE_URL": "postgres://vector-fixture",
            "DATABASE_URL": "postgres://shared-fixture",
        },
        connector=fake_connector,
    )

    assert calls == ["postgres://vector-fixture"]
    assert payload["status"] == "pgvector_connection_provider_ready"
    assert payload["driver"] == "injected"
    assert payload["connection"] is fake_connection
    assert payload["db_executor"] is fake_connection
    assert payload["database_url_source"] == (
        "APPLYLENS_VECTOR_EVIDENCE_DATABASE_URL"
    )
    _assert_safety(payload, opened=True)


def test_import_opens_no_connection_and_executes_no_storage_operation():
    reloaded = importlib.reload(connection)
    config = reloaded.vector_evidence_pgvector_connection_config_from_env(
        environ={}
    )

    assert config["status"] == "pgvector_connection_provider_disabled"
    assert config["safety_metadata"]["db_connection_opened"] is False
    source = (
        ROOT / "src/storage/vector_evidence/connection.py"
    ).read_text(encoding="utf-8")
    for marker in (
        "execute_pgvector_schema_setup(",
        "execute_vector_evidence_chunk_insert(",
        "execute_vector_evidence_embedding_insert(",
        "execute_vector_evidence_retrieval_event_insert(",
        "create_embedding(",
        "embeddings.create(",
        "openai",
        "anthropic",
        "src.pipeline",
        "src.app.api",
        "score_resume_job_match(",
        "rank_jobs(",
        "create_approval_request(",
        "record_approval_decision(",
        "create_execution_request(",
        "create_execution_launch_request(",
        "execute_application(",
        "submit_application(",
        ".commit(",
    ):
        assert marker not in source


def test_api_ui_pipeline_schema_and_dependencies_remain_unchanged():
    protected_hashes = {
        "src/app/api.py": (
            "bb4755cd3d74c72e7ed0af24de9d617c0ff568b61639b6d61e59c057348f424a"
        ),
        "src/app/static/agentic_review.js": (
            "6b275f7e838969320c41d9f97a19913218b0d4d2fd24eb7b73cb325f036b9867"
        ),
        "src/pipeline/collector.py": (
            "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405"
        ),
        "requirements.txt": (
            "96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f"
        ),
        "src/storage/vector_evidence/schema.sql": (
            "4b34a928393fcce6696a2f35d7ee62339b0483cc248daee3f0e57bdb50c11dff"
        ),
    }
    for relative_path, expected_hash in protected_hashes.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )
