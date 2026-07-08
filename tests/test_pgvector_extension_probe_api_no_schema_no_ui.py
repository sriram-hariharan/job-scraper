# phase79b legacy guard marker: changes_only collector_hash_old 73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405 85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services


ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = "/api/pgvector-extension-probe"
SERVICE_HELPER = "pgvector_extension_probe_service_helper_payload"


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _assert_api_safety(payload: dict, *, connected: bool = False) -> None:
    safety = payload["safety_metadata"]
    expected = {
        "read_only": True,
        "advisory_only": True,
        "pgvector_extension_probe": True,
        "pgvector_probe_service_helper": True,
        "pgvector_probe_api": True,
        "pgvector_installed_by_app": False,
        "schema_created": False,
        "migration_created": False,
        "embeddings_created": False,
        "vector_db_connected": connected,
        "provider_calls_made": False,
        "did_read_database": connected,
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
        "api_route_added": True,
        "ui_action_added": False,
        "pipeline_stage_added": False,
        "auto_apply_enabled": False,
        "mutation_authorized": False,
    }
    for key, value in expected.items():
        assert safety[key] is value

    assert payload["api_surface"] == "pgvector_extension_probe"
    assert payload["service_surface"] == (
        "pgvector_extension_probe_service_helper"
    )
    assert payload["pgvector_probe_api"] is True
    assert payload["api_route_added"] is True
    assert payload["read_only"] is True
    assert payload["advisory_only"] is True
    assert payload["ui_action_added"] is False
    assert payload["pipeline_stage_added"] is False
    assert payload["provider_backed_automated_agents"] == 0
    assert payload["live_provider_backed_automated_agents"] == 0
    assert payload["mutation_authorized_agents"] == 0
    assert payload["mutation_authorized_scoring_agents"] == 0
    assert payload["mutation_authorized_ranking_agents"] == 0
    assert payload["mutation_authorized_application_agents"] == 0


def test_api_route_exists_as_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"POST"}


def test_api_default_no_executor_returns_not_configured(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "extension_name": "vector",
            "requested_dimension": 768,
            "probe_context": {"source": "api-static-test"},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "pgvector_probe_not_configured"
    assert payload["extension_available"] is False
    assert payload["extension_version"] == ""
    assert payload["embedding_dimension_supported"] is None
    assert payload["skipped_reasons"] == ["probe_executor_not_configured"]
    assert payload["probe_summary"]["probe_executed"] is False
    _assert_api_safety(payload)


def test_api_preserves_service_payload_shape_and_probe_fields(monkeypatch):
    service_payload = services.pgvector_extension_probe_service_helper_payload(
        extension_name="vector",
        requested_dimension=1536,
        probe_executor=lambda request: {
            "extension_available": True,
            "extension_installed": True,
            "available_version": "0.8.0",
            "installed_version": "0.7.4",
            "postgres_version": "16.4",
            "requested_dimension": 1536,
            "supported_dimensions": [768, 1536],
            "dimension_supported": True,
            "did_read_database": True,
        },
    )
    before = deepcopy(service_payload)
    calls = []

    def static_helper(**kwargs):
        calls.append(deepcopy(kwargs))
        return deepcopy(service_payload)

    monkeypatch.setattr(services, SERVICE_HELPER, static_helper)
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "extension_name": "vector",
            "requested_dimension": 1536,
            "probe_context": {"source": "api-payload-shape-test"},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(calls) == 1
    assert calls[0] == {
        "extension_name": "vector",
        "requested_dimension": 1536,
        "probe_context": {"source": "api-payload-shape-test"},
    }
    for key, value in before.items():
        if key not in {"api_route_added", "safety_metadata"}:
            assert payload[key] == value
    assert service_payload == before
    assert payload["extension_available"] is True
    assert payload["extension_version"] == "0.7.4"
    assert payload["embedding_dimension_supported"] is True
    assert payload["probe_summary"]["available_version"] == "0.8.0"
    assert payload["probe_summary"]["installed_version"] == "0.7.4"
    assert payload["probe_summary"]["requested_dimension"] == 1536
    assert payload["probe_summary"]["supported_dimensions"] == [768, 1536]
    _assert_api_safety(payload, connected=True)


def test_api_route_slice_has_no_db_schema_provider_ui_or_mutation_runtime():
    source = (ROOT / "src/app/api.py").read_text(encoding="utf-8")
    start = source.index('@app.post("/api/pgvector-extension-probe")')
    end = source.index(
        '\n\n@app.get("/profile/pipeline-runs/{run_id}/agentic-review-data")',
        start,
    )
    route_source = source[start:end]

    assert SERVICE_HELPER in route_source
    for marker in (
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
        "record_approval_decision(",
        "create_execution_request(",
        "create_execution_launch_request(",
        "execute_application(",
        "submit_application(",
        "workflow_runner",
    ):
        assert marker not in route_source


def test_no_dependency_schema_migration_or_pipeline_change():
    protected_hashes = {
        "requirements.txt": (
            "96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f"
        ),
        "src/pipeline/collector.py": (
            "cae9f4a51ef14c7b1185a64f2e229591274c284c2985989ec1f5997f7728ee42"
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
