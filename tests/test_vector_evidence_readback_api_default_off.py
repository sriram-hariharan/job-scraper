from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services


ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = "/api/vector-evidence-readback"
SERVICE_HELPER = "vector_evidence_readback_service_helper_payload"


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _assert_safety(payload: dict, *, read: bool = False) -> None:
    safety = payload["safety_metadata"]
    assert payload["api_surface"] == "vector_evidence_readback"
    assert payload["vector_evidence_readback_api"] is True
    assert payload["api_route_added"] is True
    assert payload["read_only"] is True
    assert payload["advisory_only"] is True
    assert payload["operator_triggered_only"] is True
    assert payload["ui_action_added"] is False
    assert payload["pipeline_stage_added"] is False
    assert safety["read_only"] is True
    assert safety["advisory_only"] is True
    assert safety["vector_evidence_readback_api"] is True
    assert safety["vector_evidence_readback_service_helper"] is True
    assert safety["operator_triggered_only"] is True
    assert safety["did_read_database"] is read
    assert safety["did_write_database"] is False
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
    assert safety["api_route_added"] is True
    assert safety["ui_action_added"] is False
    assert safety["pipeline_stage_added"] is False
    assert safety["auto_apply_enabled"] is False
    assert safety["mutation_authorized"] is False
    assert payload["provider_backed_automated_agents"] == 0
    assert payload["live_provider_backed_automated_agents"] == 0
    assert payload["mutation_authorized_agents"] == 0
    assert payload["mutation_authorized_scoring_agents"] == 0
    assert payload["mutation_authorized_ranking_agents"] == 0
    assert payload["mutation_authorized_application_agents"] == 0


def test_route_exists_as_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"POST"}


def test_default_call_is_skipped_default_off(monkeypatch):
    response = _client(monkeypatch).post(ENDPOINT, json={})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == (
        "pgvector_smoke_readback_skipped_default_off"
    )
    assert payload["default_off"] is True
    assert payload["readback_attempted"] is False
    assert payload["readback_executed"] is False
    assert payload["rows_read"] == 0
    assert payload["db_connection_opened"] is False
    _assert_safety(payload)


def test_explicit_fake_service_path_returns_readback_fields(monkeypatch):
    service_payload = services.vector_evidence_readback_service_helper_payload(
        enabled=True,
        owner_user_id="owner-1",
        smoke_identifier="pgvector-local-smoke",
        db_executor=lambda request: {
            "rows": [
                {"record_type": "chunk", "record_id": "smoke-chunk"},
                {
                    "record_type": "retrieval_event",
                    "record_id": "smoke-event",
                },
            ]
        },
    )
    before = deepcopy(service_payload)
    calls = []

    def fake_helper(**kwargs):
        calls.append(deepcopy(kwargs))
        return deepcopy(service_payload)

    monkeypatch.setattr(services, SERVICE_HELPER, fake_helper)
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "enabled": True,
            "owner_user_id": "owner-1",
            "smoke_identifier": "pgvector-local-smoke",
        },
    )

    assert response.status_code == 200
    assert calls == [
        {
            "enabled": True,
            "owner_user_id": "owner-1",
            "smoke_identifier": "pgvector-local-smoke",
            "connection_provider_enabled": False,
        }
    ]
    payload = response.json()
    assert service_payload == before
    assert payload["readback_attempted"] is True
    assert payload["readback_executed"] is True
    assert payload["smoke_chunk_found"] is True
    assert payload["retrieval_event_found"] is True
    assert payload["rows_read"] == 2
    _assert_safety(payload, read=True)


def test_route_slice_has_no_storage_pipeline_provider_or_mutation_calls():
    source = (ROOT / "src/app/api.py").read_text(encoding="utf-8")
    start = source.index('@app.post("/api/vector-evidence-readback")')
    end = source.index(
        '\n\n@app.get("/profile/pipeline-runs/{run_id}/agentic-review-data")',
        start,
    )
    snippet = source[start:end]

    assert SERVICE_HELPER in snippet
    for marker in (
        "src.storage",
        "src.pipeline",
        "schema.sql",
        "psycopg",
        "DATABASE_URL",
        "connect(",
        "cursor.execute",
        ".commit(",
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
    ):
        assert marker not in snippet


def test_no_ui_pipeline_schema_or_dependency_change():
    protected_hashes = {
        "src/app/static/agentic_review.js": (
            "54980b376269262288c613d9048129b0e1192810870866852e89d391a50fea7f"
        ),
        "src/pipeline/collector.py": (
            "cbcd90f3d8d367ebe6f178c211406da909f340ce62681047b70efe4fb4a30fa7"
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
        "src/storage/vector_evidence/schema.sql": (
            "4b34a928393fcce6696a2f35d7ee62339b0483cc248daee3f0e57bdb50c11dff"
        ),
    }
    for relative_path, expected_hash in protected_hashes.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )
