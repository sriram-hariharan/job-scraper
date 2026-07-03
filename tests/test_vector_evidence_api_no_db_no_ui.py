# phase56b legacy guard marker: changes_only 4a2936004507cc4cc09615ef41de7e7e170c3c78aa840ce66bfd27484e542668 1ff2a73993300f391aa1fb8151a4d225e803b6c5d499e311faa5058efc4b965c
# phase56a legacy guard marker: changes_only 85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96 4a2936004507cc4cc09615ef41de7e7e170c3c78aa840ce66bfd27484e542668
# phase26c legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c
# phase26b legacy guard marker: changes_only 85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96
# phase23f legacy guard marker: changes_only 85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
# phase23f legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services


ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = "/api/vector-evidence"
SERVICE_HELPER = "vector_evidence_service_helper_payload"


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _metadata(
    *,
    job_id: str,
    company: str,
    stage: str,
    agent_name: str,
) -> dict:
    return {
        "job_id": job_id,
        "company": company,
        "title": "ML Platform Engineer",
        "source": "greenhouse",
        "stage": stage,
        "agent_name": agent_name,
        "trace_id": f"trace-{job_id}",
        "run_id": f"run-{job_id}",
        "resume_version": "resume-v4",
        "profile_version": "profile-v5",
        "created_at": "2026-06-18T17:00:00Z",
        "safety_flags": {"human_review_required": True},
        "read_only": True,
    }


def _request_payload() -> dict:
    return {
        "query_text": "machine learning platform",
        "job_payload": {
            **_metadata(
                job_id="job-1",
                company="Acme AI",
                stage="jd_intelligence",
                agent_name="jd_intelligence_agent",
            ),
            "job_description": (
                "Build reliable machine learning platform services."
            ),
        },
        "resume_profile_payload": {
            **_metadata(
                job_id="job-1",
                company="Acme AI",
                stage="resume_match",
                agent_name="resume_match_agent",
            ),
            "resume_text": (
                "Candidate built Python APIs and production ML systems."
            ),
        },
        "trace_evidence_payload": {
            **_metadata(
                job_id="job-2",
                company="Beta Data",
                stage="trace_readback",
                agent_name="critic_guardrail",
            ),
            "trace_evidence": (
                "Trace found unsupported claim guardrail evidence."
            ),
        },
        "operator_review_packet_payload": {
            **_metadata(
                job_id="job-3",
                company="Gamma Labs",
                stage="operator_review",
                agent_name="pipeline_agent_review_packet",
            ),
            "evidence_text": (
                "Operator review packet requests human provenance confirmation."
            ),
        },
        "top_k": 5,
    }


def _post(monkeypatch, **updates):
    request_payload = _request_payload()
    request_payload.update(updates)
    return _client(monkeypatch).post(ENDPOINT, json=request_payload)


def _assert_api_safety(payload: dict) -> None:
    safety = payload["safety_metadata"]
    expected = {
        "read_only": True,
        "advisory_only": True,
        "vector_evidence_api": True,
        "vector_evidence_service_helper": True,
        "embeddings_created": False,
        "vector_db_connected": False,
        "provider_calls_made": False,
        "did_read_database": False,
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

    assert payload["api_surface"] == "vector_evidence"
    assert payload["vector_evidence_api"] is True
    assert payload["vector_evidence_service_helper"] is True
    assert payload["api_route_added"] is True
    assert payload["read_only"] is True
    assert payload["advisory_only"] is True
    assert payload["ui_action_added"] is False
    assert payload["pipeline_stage_added"] is False


def _assert_match(monkeypatch, query: str, chunk_type: str) -> None:
    response = _post(
        monkeypatch,
        query_text=query,
        chunk_type=chunk_type,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "vector_evidence_service_ready"
    assert payload["retrieval_summary"]["match_count"] == 1
    assert payload["matched_chunks"][0]["chunk_type"] == chunk_type
    _assert_api_safety(payload)


def test_api_route_exists_as_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"POST"}


def test_api_retrieves_matching_job_description_evidence(monkeypatch):
    _assert_match(
        monkeypatch,
        "reliable machine learning platform",
        "job_description",
    )


def test_api_retrieves_resume_profile_evidence(monkeypatch):
    _assert_match(
        monkeypatch,
        "candidate Python production systems",
        "resume_profile",
    )


def test_api_retrieves_trace_evidence(monkeypatch):
    _assert_match(
        monkeypatch,
        "unsupported claim guardrail",
        "trace_evidence",
    )


def test_api_retrieves_operator_review_packet_evidence(monkeypatch):
    _assert_match(
        monkeypatch,
        "operator human provenance confirmation",
        "operator_review_packet",
    )


def test_api_supports_metadata_filters(monkeypatch):
    response = _post(
        monkeypatch,
        query_text="Python production systems",
        filters={
            "chunk_type": "resume_profile",
            "job_id": "job-1",
            "company": "acme ai",
            "agent_name": "resume_match_agent",
            "stage": "resume_match",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["retrieval_summary"]["match_count"] == 1
    metadata = payload["matched_chunks"][0]["metadata"]
    assert metadata["job_id"] == "job-1"
    assert metadata["company"] == "Acme AI"
    assert metadata["agent_name"] == "resume_match_agent"
    assert metadata["stage"] == "resume_match"
    _assert_api_safety(payload)


def test_api_is_deterministic_and_does_not_mutate_request(monkeypatch):
    request_payload = _request_payload()
    request_payload.update(
        {
            "query_text": "machine learning Python",
            "top_k": 2,
        }
    )
    before = deepcopy(request_payload)
    client = _client(monkeypatch)

    first = client.post(ENDPOINT, json=request_payload)
    second = client.post(ENDPOINT, json=request_payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()
    assert request_payload == before
    assert first.json()["retrieval_summary"]["top_k"] == 2
    _assert_api_safety(first.json())


def test_api_returns_safe_missing_query_fallback(monkeypatch):
    response = _post(monkeypatch, query_text=" ")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "vector_evidence_service_invalid_query"
    assert payload["matched_chunks"] == []
    assert payload["retrieval_summary"]["status"] == (
        "vector_evidence_retrieval_dry_run_invalid_query"
    )
    _assert_api_safety(payload)


def test_api_returns_safe_no_chunk_fallback(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "query_text": "machine learning",
            "job_payload": {"job_id": "job-empty"},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "vector_evidence_service_no_chunks"
    assert payload["indexing_summary"]["status"] == (
        "vector_evidence_indexing_dry_run_no_chunks"
    )
    assert payload["retrieval_summary"]["status"] == (
        "vector_evidence_retrieval_dry_run_no_results"
    )
    assert payload["matched_chunks"] == []
    _assert_api_safety(payload)


def test_api_preserves_indexing_and_retrieval_summaries(monkeypatch):
    response = _post(
        monkeypatch,
        query_text="machine learning platform",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["indexing_summary"] == {
        "status": "vector_evidence_indexing_dry_run_ready",
        "chunk_count": 4,
        "chunk_types_present": [
            "job_description",
            "operator_review_packet",
            "resume_profile",
            "trace_evidence",
        ],
        "skipped_reasons": [],
    }
    assert payload["retrieval_summary"]["status"] == (
        "vector_evidence_retrieval_dry_run_ready"
    )
    assert payload["indexing_dry_run"]["chunk_count"] == 4
    assert payload["retrieval_dry_run"]["matched_chunks"] == (
        payload["matched_chunks"]
    )
    _assert_api_safety(payload)


def test_api_delegates_to_existing_service_helper_unchanged(monkeypatch):
    calls = []
    real_helper = getattr(services, SERVICE_HELPER)

    def recording_helper(**kwargs):
        calls.append(deepcopy(kwargs))
        return real_helper(**kwargs)

    monkeypatch.setattr(services, SERVICE_HELPER, recording_helper)
    response = _post(
        monkeypatch,
        query_text="machine learning platform",
        top_k=3,
    )

    assert response.status_code == 200
    assert len(calls) == 1
    assert calls[0]["query_text"] == "machine learning platform"
    assert calls[0]["top_k"] == 3
    assert response.json()["service_surface"] == (
        "vector_evidence_service_helper"
    )


def test_api_route_slice_has_no_storage_provider_embedding_or_mutation_calls():
    source = (ROOT / "src/app/api.py").read_text(encoding="utf-8")
    start = source.index('@app.post("/api/vector-evidence")')
    end = source.index(
        '\n\n@app.get("/profile/pipeline-runs/{run_id}/agentic-review-data")',
        start,
    )
    route_source = source[start:end]

    for marker in (
        "src.pipeline",
        "src.storage",
        "schema.sql",
        "create_embedding(",
        "embed(",
        "connect(",
        "cursor.execute",
        ".commit(",
        "score_resume_job_match(",
        "rank_jobs(",
        "create_approval_request(",
        "record_approval_decision(",
        "create_execution_request(",
        "create_execution_launch_request(",
        "execute_application(",
        "submit_application(",
        "openai",
        "anthropic",
        "llm_client",
        "workflow_runner",
    ):
        assert marker not in route_source

    assert SERVICE_HELPER in route_source


def test_no_schema_dependency_ui_or_pipeline_change():
    later_readonly_ui_step_exists = (
        ROOT / "tests/test_vector_evidence_ui_no_db_readonly.py"
    ).exists()
    protected_hashes = {
        "requirements.txt": ("96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f"),
        "src/storage/agent_trace/schema.sql": ("69305cd1bec0be9caa8c8c1b93e8fc10a3e80a92c08acd5683e7800763d2a77a"),
        "src/storage/agentic_approvals/schema.sql": ("57e84094cdbd3a4e8542fd205d89bfde18179c5d07c15084354f31f77bf5d98f"),
        "src/storage/profile_resumes/schema.sql": ("a71d55d9306258661b99f9bc88aa122fbf24443e7bd43a9ba597133289df1e57"),
        "src/app/static/agentic_review.js": ("1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b"),
        "src/pipeline/collector.py": ("73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405"),
        "src/pipeline/application_scorer.py": ("e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b"),
        "src/pipeline/job_ranker.py": ("5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54"),
    }
    for relative_path, expected_hash in protected_hashes.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )

    for relative_path in (
        "src/app/static/agentic_review.js",
        "src/pipeline/collector.py",
        "src/pipeline/application_scorer.py",
        "src/pipeline/job_ranker.py",
    ):
        source = (ROOT / relative_path).read_text(encoding="utf-8")
        if not (
            later_readonly_ui_step_exists
            and relative_path == "src/app/static/agentic_review.js"
        ):
            assert ENDPOINT not in source
        assert SERVICE_HELPER not in source
