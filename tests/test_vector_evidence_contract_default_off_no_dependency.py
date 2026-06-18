from copy import deepcopy
from pathlib import Path

from src.agents import vector_evidence_contract as contract


ROOT = Path(__file__).resolve().parents[1]


def _metadata() -> dict:
    return {
        "job_id": "job-123",
        "company": "Acme AI",
        "title": "Machine Learning Engineer",
        "source": "greenhouse",
        "stage": "operator_review",
        "agent_name": "jd_intelligence_agent",
        "trace_id": "trace-123",
        "run_id": "run-123",
        "resume_version": "resume-v2",
        "profile_version": "profile-v3",
        "created_at": "2026-06-18T12:00:00Z",
        "safety_flags": {"human_review_required": True},
        "read_only": True,
    }


def _chunk(chunk_type: str = "job_description") -> dict:
    return {
        "chunk_type": chunk_type,
        "evidence_text": " Build reliable machine learning services. ",
        "metadata": _metadata(),
    }


def _enabled_request() -> dict:
    return contract.build_vector_retrieval_request_contract(
        query_text="machine learning platform evidence",
        chunk_types=["job_description", "trace_evidence"],
        metadata_filters={"job_id": "job-123", "read_only": True},
        top_k=3,
        retrieval_enabled=True,
        request_id="request-123",
    )


def _assert_safety(payload: dict) -> None:
    safety = payload["safety_metadata"]
    assert safety == {
        "read_only": True,
        "advisory_only": True,
        "vector_evidence_contract_only": True,
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
        "api_route_added": False,
        "ui_action_added": False,
        "pipeline_stage_added": False,
        "auto_apply_enabled": False,
        "mutation_authorized": False,
    }
    assert payload["provider_backed_automated_agents"] == 0
    assert payload["live_provider_backed_automated_agents"] == 0
    assert payload["mutation_authorized_agents"] == 0
    assert payload["evaluation_boundaries"] == {
        "prefilter_relevance": "separate_unchanged",
        "llm_shadow_evaluation": "separate_advisory_only",
        "final_application_scoring": "separate_unchanged",
        "retrieval_evidence_support": "contract_only_advisory",
    }


def test_helper_builds_normalized_chunk_candidate_and_preserves_metadata():
    source = _chunk()
    before = deepcopy(source)

    payload = contract.build_vector_evidence_chunk_candidate(**source)
    candidate = payload["chunk_candidate"]

    assert source == before
    assert payload["status"] == "vector_evidence_contract_ready"
    assert payload["validation"]["is_valid"] is True
    assert candidate["chunk_id"].startswith("vector-evidence:")
    assert candidate["chunk_type"] == "job_description"
    assert candidate["evidence_text"] == (
        "Build reliable machine learning services."
    )
    assert candidate["embedding"] is None
    for field, value in _metadata().items():
        assert candidate["metadata"][field] == value
    _assert_safety(payload)


def test_helper_supports_all_phase8a_chunk_types():
    payload = contract.build_vector_evidence_chunk_candidates(
        [_chunk(chunk_type) for chunk_type in contract.CHUNK_TYPES]
    )

    assert payload["status"] == "vector_evidence_contract_ready"
    assert payload["chunk_count"] == 5
    assert [item["chunk_type"] for item in payload["chunk_candidates"]] == list(
        contract.CHUNK_TYPES
    )
    assert payload["invalid_chunks"] == []
    _assert_safety(payload)


def test_helper_rejects_missing_or_unsupported_evidence_safely():
    missing = contract.build_vector_evidence_chunk_candidate(
        chunk_type="job_description",
        evidence_text="",
        metadata=_metadata(),
    )
    unsupported = contract.build_vector_evidence_chunk_candidate(
        chunk_type="unknown",
        evidence_text="Evidence",
        metadata=_metadata(),
    )

    assert missing["status"] == "vector_evidence_invalid_request"
    assert "missing_evidence_text" in missing["validation"]["errors"]
    assert unsupported["status"] == "vector_evidence_invalid_request"
    assert "unsupported_chunk_type" in unsupported["validation"]["errors"]
    assert missing["chunk_candidate"]["embedding"] is None
    _assert_safety(missing)
    _assert_safety(unsupported)


def test_helper_builds_default_off_retrieval_request_contract():
    source_filters = {"company": "Acme AI", "read_only": True}
    before = deepcopy(source_filters)

    payload = contract.build_vector_retrieval_request_contract(
        query_text="Find supporting JD evidence",
        chunk_types=["job_description"],
        metadata_filters=source_filters,
        top_k=8,
    )

    assert source_filters == before
    assert payload["status"] == "vector_retrieval_not_configured"
    assert payload["retrieval_configured"] is False
    assert payload["retrieval_executed"] is False
    assert payload["request"]["retrieval_enabled"] is False
    assert payload["request"]["top_k"] == 8
    assert payload["request"]["metadata_filters"]["company"] == "Acme AI"
    _assert_safety(payload)


def test_helper_marks_invalid_retrieval_request_safely():
    payload = contract.build_vector_retrieval_request_contract(
        query_text="",
        chunk_types=["unsupported"],
        retrieval_enabled=True,
    )

    assert payload["status"] == "vector_evidence_invalid_request"
    assert payload["validation"]["is_valid"] is False
    assert payload["validation"]["errors"] == [
        "missing_query_text",
        "unsupported_chunk_types",
    ]
    assert payload["retrieval_executed"] is False
    _assert_safety(payload)


def test_helper_builds_retrieval_response_contract_from_supplied_evidence():
    request = _enabled_request()
    results = [_chunk("job_description"), _chunk("trace_evidence")]
    before = deepcopy((request, results))

    first = contract.build_vector_retrieval_response_contract(
        request_contract=request,
        evidence_results=results,
    )
    second = contract.build_vector_retrieval_response_contract(
        request_contract=request,
        evidence_results=results,
    )

    assert first == second
    assert (request, results) == before
    assert first["status"] == "vector_evidence_contract_ready"
    assert first["evidence_found"] is True
    assert first["result_count"] == 2
    assert first["retrieval_configured"] is False
    assert first["retrieval_executed"] is False
    assert first["fallback"]["used"] is False
    assert all(item["embedding"] is None for item in first["evidence_results"])
    _assert_safety(first)


def test_helper_returns_safe_no_result_fallback():
    default_off_request = contract.build_vector_retrieval_request_contract(
        query_text="Find evidence",
    )

    fallback = contract.build_vector_retrieval_no_result_fallback(
        request_contract=default_off_request
    )
    response = contract.build_vector_retrieval_response_contract(
        request_contract=default_off_request,
        evidence_results=[_chunk()],
    )

    for payload in (fallback, response):
        assert payload["status"] == "vector_retrieval_not_configured"
        assert payload["evidence_found"] is False
        assert payload["evidence_results"] == []
        assert payload["result_count"] == 0
        assert payload["fallback"]["used"] is True
        assert payload["retrieval_executed"] is False
        _assert_safety(payload)


def test_empty_enabled_response_returns_vector_evidence_no_chunks():
    payload = contract.build_vector_retrieval_response_contract(
        request_contract=_enabled_request(),
        evidence_results=[],
    )

    assert payload["status"] == "vector_evidence_no_chunks"
    assert payload["evidence_found"] is False
    assert payload["fallback"]["reason"] == "vector_evidence_no_chunks"
    _assert_safety(payload)


def test_helper_source_has_no_vector_db_embedding_provider_storage_or_mutation_calls():
    source = (
        ROOT / "src/agents/vector_evidence_contract.py"
    ).read_text(encoding="utf-8")
    forbidden = (
        "import pgvector",
        "import pinecone",
        "import chroma",
        "import faiss",
        "import langchain",
        "import langgraph",
        "sentence_transformers",
        "llama_index",
        "openai",
        "anthropic",
        "google.genai",
        "groq",
        "requests.",
        "httpx.",
        "subprocess",
        "socket",
        "psycopg",
        "redis",
        "src.storage",
        "src.pipeline",
        "src.app",
        "create_embedding(",
        "embed(",
        "connect(",
        "cursor.execute",
        ".commit(",
        "score_jobs(",
        "rank_jobs(",
        "create_approval_request(",
        "create_execution_request(",
        "create_execution_launch_request(",
        "execute_application(",
        "submit_application(",
    )
    for marker in forbidden:
        assert marker not in source


def test_no_dependency_schema_api_service_ui_or_pipeline_integration():
    helper_marker = "vector_evidence_contract"
    protected_paths = (
        "requirements.txt",
        "src/app/api.py",
        "src/app/services.py",
        "src/app/static/agentic_review.js",
        "src/pipeline/collector.py",
        "src/pipeline/application_scorer.py",
        "src/pipeline/job_ranker.py",
        "src/storage/agent_trace/schema.sql",
        "src/storage/agentic_approvals/schema.sql",
        "src/storage/profile_resumes/schema.sql",
    )

    for relative_path in protected_paths:
        assert helper_marker not in (ROOT / relative_path).read_text(
            encoding="utf-8"
        )

    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").lower()
    for dependency in ("pgvector", "pinecone", "chromadb", "faiss", "langgraph"):
        assert dependency not in requirements

