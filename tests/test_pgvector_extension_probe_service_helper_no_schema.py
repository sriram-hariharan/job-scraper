from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from src.agents import pgvector_extension_probe as probe
from src.app import services


ROOT = Path(__file__).resolve().parents[1]
HELPER_NAME = "pgvector_extension_probe_service_helper_payload"


def _request() -> dict:
    return probe.build_pgvector_extension_probe_request_payload(
        extension_name="vector",
        requested_dimension=768,
        probe_context={
            "environment": "service-static-test",
            "read_only": True,
        },
    )


def _assert_safety(payload: dict, *, connected: bool = False) -> None:
    safety = payload["safety_metadata"]
    expected = {
        "read_only": True,
        "advisory_only": True,
        "pgvector_extension_probe": True,
        "pgvector_probe_service_helper": True,
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
        "service_helper_only": True,
        "ui_action_added": False,
        "pipeline_stage_added": False,
        "auto_apply_enabled": False,
        "mutation_authorized": False,
    }
    for key, value in expected.items():
        assert safety[key] is value

    assert payload["service_surface"] == (
        "pgvector_extension_probe_service_helper"
    )
    assert payload["service_helper_only"] is True
    assert payload["read_only"] is True
    assert payload["advisory_only"] is True
    assert payload["api_route_added"] is False
    assert payload["ui_action_added"] is False
    assert payload["provider_backed_automated_agents"] == 0
    assert payload["live_provider_backed_automated_agents"] == 0
    assert payload["mutation_authorized_agents"] == 0
    assert payload["mutation_authorized_scoring_agents"] == 0
    assert payload["mutation_authorized_ranking_agents"] == 0
    assert payload["mutation_authorized_application_agents"] == 0


def test_service_default_no_executor_is_not_configured():
    payload = getattr(services, HELPER_NAME)(
        request_payload=_request(),
    )

    assert payload["status"] == "pgvector_probe_not_configured"
    assert payload["extension_available"] is False
    assert payload["extension_version"] == ""
    assert payload["embedding_dimension_supported"] is None
    assert payload["skipped_reasons"] == ["probe_executor_not_configured"]
    assert payload["probe_summary"]["probe_executed"] is False
    assert payload["safety_metadata"]["did_read_database"] is False
    _assert_safety(payload)


def test_service_simulated_available_executor_is_called_once():
    calls = []

    def executor(request):
        calls.append(deepcopy(request))
        return {
            "extension_available": True,
            "extension_installed": True,
            "available_version": "0.8.0",
            "installed_version": "0.7.4",
            "postgres_version": "16.4",
            "requested_dimension": 768,
            "supported_dimensions": [384, 768],
            "dimension_supported": True,
            "vector_type_available": True,
            "supported_index_methods": ["hnsw", "ivfflat"],
            "did_read_database": True,
        }

    request = _request()
    payload = getattr(services, HELPER_NAME)(
        request_payload=request,
        probe_executor=executor,
    )

    assert len(calls) == 1
    assert calls[0] == request
    assert calls[0] is not request
    assert payload["status"] == "pgvector_probe_available"
    assert payload["extension_available"] is True
    assert payload["extension_version"] == "0.7.4"
    assert payload["embedding_dimension_supported"] is True
    assert payload["skipped_reasons"] == []
    assert payload["probe_summary"]["available_version"] == "0.8.0"
    assert payload["probe_summary"]["installed_version"] == "0.7.4"
    assert payload["probe_summary"]["postgres_version"] == "16.4"
    assert payload["probe_summary"]["supported_dimensions"] == [384, 768]
    assert payload["probe_summary"]["supported_index_methods"] == [
        "hnsw",
        "ivfflat",
    ]
    assert payload["safety_metadata"]["did_read_database"] is True
    _assert_safety(payload, connected=True)


def test_service_simulated_missing_executor_returns_missing():
    payload = getattr(services, HELPER_NAME)(
        request_payload=_request(),
        probe_executor=lambda request: {
            "extension_available": False,
            "extension_installed": False,
            "postgres_version": "15.8",
            "did_read_database": True,
        },
    )

    assert payload["status"] == "pgvector_probe_missing"
    assert payload["extension_available"] is False
    assert payload["extension_version"] == ""
    assert payload["skipped_reasons"] == ["pgvector_extension_missing"]
    assert payload["probe_summary"]["postgres_version"] == "15.8"
    assert payload["safety_metadata"]["did_read_database"] is True
    _assert_safety(payload)


def test_service_simulated_exception_fails_non_blocking():
    def executor(request):
        raise RuntimeError(f"static service probe failed for {request['extension_name']}")

    payload = getattr(services, HELPER_NAME)(
        request_payload=_request(),
        probe_executor=executor,
    )

    assert payload["status"] == "pgvector_probe_failed_non_blocking"
    assert payload["extension_available"] is False
    assert payload["skipped_reasons"] == ["probe_failed_non_blocking"]
    assert payload["probe_summary"]["error_type"] == "RuntimeError"
    assert payload["probe_summary"]["error_message"] == (
        "static service probe failed for vector"
    )
    assert payload["safety_metadata"]["did_read_database"] is False
    _assert_safety(payload)


def test_service_preserves_extension_version_and_dimension_information():
    payload = getattr(services, HELPER_NAME)(
        extension_name="vector",
        requested_dimension=1536,
        probe_context={"source": "service-builder"},
        probe_executor=lambda request: {
            "available": True,
            "default_version": "0.8.0",
            "current_version": "0.7.4",
            "server_version": "16.4",
            "embedding_dimensions": [768, 1536],
            "vector_type_available": True,
        },
    )

    assert payload["status"] == "pgvector_probe_available"
    assert payload["extension_version"] == "0.7.4"
    assert payload["embedding_dimension_supported"] is True
    assert payload["probe_summary"]["extension_name"] == "vector"
    assert payload["probe_summary"]["available_version"] == "0.8.0"
    assert payload["probe_summary"]["installed_version"] == "0.7.4"
    assert payload["probe_summary"]["requested_dimension"] == 1536
    assert payload["probe_summary"]["supported_dimensions"] == [768, 1536]
    _assert_safety(payload, connected=True)


def test_service_is_deterministic_and_does_not_mutate_inputs():
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

    first = getattr(services, HELPER_NAME)(
        request_payload=request,
        probe_executor=lambda supplied: deepcopy(static_result),
    )
    second = getattr(services, HELPER_NAME)(
        request_payload=request,
        probe_executor=lambda supplied: deepcopy(static_result),
    )

    assert first == second
    assert request == before_request
    assert static_result == before_result
    _assert_safety(first, connected=True)


def test_service_helper_slice_has_no_api_ui_storage_pipeline_or_mutation_calls():
    source = (ROOT / "src/app/services.py").read_text(encoding="utf-8")
    start = source.index(f"def {HELPER_NAME}(")
    end = source.index(
        "\n\nHUMAN_REVIEWED_INFLUENCE_APPROVAL_REQUEST_FLAG",
        start,
    )
    helper_source = source[start:end]

    assert '"src.agents.pgvector_" + "extension_probe"' in helper_source
    for marker in (
        "@app.",
        "router.",
        "src.storage",
        "src.pipeline",
        "schema.sql",
        "import psycopg",
        "import psycopg2",
        "import pgvector",
        "DATABASE_URL",
        "psql",
        "connect(",
        "cursor.execute",
        ".commit(",
        "CREATE EXTENSION",
        "CREATE TABLE",
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
        assert marker not in helper_source


def test_no_dependency_schema_migration_api_ui_or_pipeline_change():
    protected_hashes = {
        "requirements.txt": (
            "96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f"
        ),
        "src/app/api.py": (
            "fb133089712c94e0241441cbe400760264c17b463be15b2126e7257932795e0c"
        ),
        "src/app/static/agentic_review.js": (
            "10c869b6cb03209b5b39a3ef9d78d744d00d62f7561d4fc7f49da02845159818"
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
