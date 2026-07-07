# phase79b legacy guard marker: changes_only collector_hash_old 73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405
# phase56b legacy guard marker: changes_only e30180b352ebe8abca2ec34b4b34983fbaee61a32bdc0d511001c406703e392c 1ff2a73993300f391aa1fb8151a4d225e803b6c5d499e311faa5058efc4b965c
# phase56a legacy guard marker: changes_only 85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96 e30180b352ebe8abca2ec34b4b34983fbaee61a32bdc0d511001c406703e392c
# phase26b legacy guard marker: changes_only 85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from src.agents import pgvector_extension_probe as probe


ROOT = Path(__file__).resolve().parents[1]


def _request() -> dict:
    return probe.build_pgvector_extension_probe_request_payload(
        extension_name="vector",
        requested_dimension=768,
        probe_context={
            "environment": "static-test",
            "read_only": True,
        },
    )


def _assert_safety(payload: dict, *, connected: bool = False) -> None:
    safety = payload["safety_metadata"]
    expected = {
        "read_only": True,
        "advisory_only": True,
        "pgvector_extension_probe": True,
        "pgvector_installed_by_app": False,
        "schema_created": False,
        "migration_created": False,
        "embeddings_created": False,
        "vector_db_connected": connected,
        "provider_calls_made": False,
        "did_write_database": False,
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
        "api_route_added": False,
        "service_helper_added": False,
        "ui_action_added": False,
        "pipeline_stage_added": False,
        "auto_apply_enabled": False,
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
    assert payload["evaluation_boundaries"] == {
        "prefilter_relevance": "separate_unchanged",
        "llm_shadow_evaluation": "separate_advisory_only",
        "final_application_scoring": "separate_unchanged",
        "retrieval_evidence_support": "extension_probe_only",
    }


def test_default_no_executor_probe_is_not_configured():
    payload = probe.build_pgvector_extension_probe_payload(
        request_payload=_request(),
    )

    assert payload["status"] == "pgvector_probe_not_configured"
    assert payload["probe_configured"] is False
    assert payload["probe_executed"] is False
    assert payload["requested_dimension"] == 768
    assert payload["safety_metadata"]["did_read_database"] is False
    _assert_safety(payload)


def test_simulated_available_executor_is_called_once_and_normalized():
    calls = []

    def executor(request):
        calls.append(deepcopy(request))
        return {
            "extension_name": "vector",
            "extension_available": True,
            "extension_installed": True,
            "available_version": "0.8.0",
            "installed_version": "0.7.4",
            "postgres_version": "16.4",
            "requested_dimension": 768,
            "supported_dimensions": [1536, 768, 768],
            "dimension_supported": True,
            "vector_type_available": True,
            "supported_index_methods": ["ivfflat", "hnsw", "hnsw"],
            "did_read_database": True,
            "probe_details": {"source": "static_executor"},
        }

    request = _request()
    payload = probe.build_pgvector_extension_probe_payload(
        request_payload=request,
        probe_executor=executor,
    )

    assert len(calls) == 1
    assert calls[0] == request
    assert calls[0] is not request
    assert payload["status"] == "pgvector_probe_available"
    assert payload["extension_available"] is True
    assert payload["extension_installed"] is True
    assert payload["available_version"] == "0.8.0"
    assert payload["installed_version"] == "0.7.4"
    assert payload["postgres_version"] == "16.4"
    assert payload["requested_dimension"] == 768
    assert payload["supported_dimensions"] == [768, 1536]
    assert payload["dimension_supported"] is True
    assert payload["vector_type_available"] is True
    assert payload["supported_index_methods"] == ["hnsw", "ivfflat"]
    assert payload["probe_details"] == {"source": "static_executor"}
    assert payload["safety_metadata"]["did_read_database"] is True
    _assert_safety(payload, connected=True)


def test_simulated_missing_executor_returns_missing():
    payload = probe.build_pgvector_extension_probe_payload(
        request_payload=_request(),
        probe_executor=lambda request: {
            "extension_name": request["extension_name"],
            "extension_available": False,
            "extension_installed": False,
            "available_version": "",
            "installed_version": "",
            "postgres_version": "15.8",
            "supported_dimensions": [],
            "did_read_database": True,
        },
    )

    assert payload["status"] == "pgvector_probe_missing"
    assert payload["extension_available"] is False
    assert payload["extension_installed"] is False
    assert payload["postgres_version"] == "15.8"
    assert payload["safety_metadata"]["did_read_database"] is True
    _assert_safety(payload)


def test_simulated_exception_fails_non_blocking():
    def executor(request):
        raise RuntimeError(f"static probe failed for {request['extension_name']}")

    payload = probe.build_pgvector_extension_probe_payload(
        request_payload=_request(),
        probe_executor=executor,
    )

    assert payload["status"] == "pgvector_probe_failed_non_blocking"
    assert payload["probe_configured"] is True
    assert payload["probe_executed"] is True
    assert payload["error_type"] == "RuntimeError"
    assert payload["error_message"] == "static probe failed for vector"
    assert payload["safety_metadata"]["did_read_database"] is False
    _assert_safety(payload)


def test_probe_is_deterministic_and_does_not_mutate_inputs():
    request = _request()
    static_result = {
        "extension_available": True,
        "available_version": "0.8.0",
        "requested_dimension": 768,
        "supported_dimensions": [768],
        "probe_details": {"mode": "deterministic"},
    }
    before_request = deepcopy(request)
    before_result = deepcopy(static_result)

    first = probe.build_pgvector_extension_probe_payload(
        request_payload=request,
        probe_executor=lambda supplied: deepcopy(static_result),
    )
    second = probe.build_pgvector_extension_probe_payload(
        request_payload=request,
        probe_executor=lambda supplied: deepcopy(static_result),
    )

    assert first == second
    assert request == before_request
    assert static_result == before_result
    _assert_safety(first, connected=True)


def test_result_normalizer_preserves_extension_version_and_dimension_info():
    payload = probe.normalize_pgvector_extension_probe_result_payload(
        {
            "available": True,
            "extension_name": "vector",
            "default_version": "0.8.0",
            "current_version": "0.7.4",
            "server_version": "16.4",
            "embedding_dimensions": [384, 768],
            "vector_type_available": True,
        },
        request_payload=_request(),
    )

    assert payload["status"] == "pgvector_probe_available"
    assert payload["extension_name"] == "vector"
    assert payload["available_version"] == "0.8.0"
    assert payload["installed_version"] == "0.7.4"
    assert payload["postgres_version"] == "16.4"
    assert payload["requested_dimension"] == 768
    assert payload["supported_dimensions"] == [384, 768]
    assert payload["dimension_supported"] is True
    _assert_safety(payload, connected=True)


def test_helper_source_has_no_database_schema_provider_or_mutation_runtime():
    source = (ROOT / "src/agents/pgvector_extension_probe.py").read_text(
        encoding="utf-8"
    )

    for marker in (
        "import psycopg",
        "import psycopg2",
        "import pgvector",
        "subprocess",
        "DATABASE_URL",
        "psql",
        "connect(",
        "cursor.execute",
        ".commit(",
        "CREATE EXTENSION",
        "CREATE TABLE",
        "ALTER TABLE",
        "create_embedding(",
        "embeddings.create(",
        "openai",
        "anthropic",
        "llm_client",
        "score_resume_job_match(",
        "rank_jobs(",
        "create_approval_request(",
        "create_execution_request(",
        "create_execution_launch_request(",
        "execute_application(",
        "submit_application(",
    ):
        assert marker not in source


def test_no_dependency_schema_migration_api_service_or_pipeline_change():
    protected_hashes = {
        "requirements.txt": (
            "96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f"
        ),
        "src/app/api.py": (
            "85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96"
        ),
        "src/pipeline/collector.py": (
            "52fef8d48ba9b42e8a317c0b08fc411e100103a8f971a782459b90725cddb0d5"
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
    }
    for relative_path, expected_hash in protected_hashes.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )

    schema_and_migration_paths = [
        path
        for path in (ROOT / "src/storage").rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.name != ".DS_Store"
        and path.suffix != ".pyc"
        and (
            path.suffix == ".sql"
            or "migration" in path.name.lower()
            or "migrations" in path.parts
            or "alembic" in path.parts
        )
        and path != ROOT / "src/storage/vector_evidence/schema.sql"
    ]
    digest = sha256()
    for path in sorted(
        schema_and_migration_paths,
        key=lambda item: item.relative_to(ROOT).as_posix(),
    ):
        digest.update(path.relative_to(ROOT).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    assert digest.hexdigest() == (
        "27e2efd8f1b55117b3d8a27572672152b7e8127733ed5408fe3f353595f1c1ed"
    )

    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").lower()
    assert "pgvector" not in requirements
