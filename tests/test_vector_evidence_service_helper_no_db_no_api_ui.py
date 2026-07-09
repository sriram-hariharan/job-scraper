# phase107b legacy guard marker: changes_only requirements_hash_old 96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004 src/app/api.py
from copy import deepcopy
from pathlib import Path

from src.app import services


ROOT = Path(__file__).resolve().parents[1]
HELPER_NAME = "vector_evidence_service_helper_payload"


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


def _payloads() -> dict:
    return {
        "job_payload": {
            **_metadata(
                job_id="job-1",
                company="Acme AI",
                stage="jd_intelligence",
                agent_name="jd_intelligence_agent",
            ),
            "job_description": "Build reliable machine learning platform services.",
        },
        "resume_profile_payload": {
            **_metadata(
                job_id="job-1",
                company="Acme AI",
                stage="resume_match",
                agent_name="resume_match_agent",
            ),
            "resume_text": "Candidate built Python APIs and production ML systems.",
        },
        "trace_evidence_payload": {
            **_metadata(
                job_id="job-2",
                company="Beta Data",
                stage="trace_readback",
                agent_name="critic_guardrail",
            ),
            "trace_evidence": "Trace found unsupported claim guardrail evidence.",
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
    }


def _assert_safety(payload: dict) -> None:
    safety = payload["safety_metadata"]
    assert payload["service_surface"] == "vector_evidence_service_helper"
    assert payload["service_helper_only"] is True
    assert payload["read_only"] is True
    assert payload["advisory_only"] is True
    assert payload["api_route_added"] is False
    assert payload["ui_action_added"] is False
    assert safety["read_only"] is True
    assert safety["advisory_only"] is True
    assert safety["vector_evidence_service_helper"] is True
    assert safety["vector_evidence_indexing_dry_run"] is True
    assert safety["vector_evidence_retrieval_dry_run"] is True
    assert safety["vector_evidence_contract_only"] is True
    assert safety["embeddings_created"] is False
    assert safety["vector_db_connected"] is False
    assert safety["provider_calls_made"] is False
    assert safety["did_read_database"] is False
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
    assert safety["api_route_added"] is False
    assert safety["service_helper_only"] is True
    assert safety["ui_action_added"] is False
    assert safety["pipeline_stage_added"] is False
    assert safety["auto_apply_enabled"] is False
    assert safety["mutation_authorized"] is False
    assert safety["pgvector_store_adapter_available"] is True
    assert safety["pgvector_store_path_requested"] is False
    assert safety["pgvector_store_path_used"] is False
    assert safety["pgvector_store_path_default_off"] is True
    assert payload["pgvector_store_adapter_available"] is True
    assert payload["pgvector_store_path_requested"] is False
    assert payload["pgvector_store_path_used"] is False
    assert payload["pgvector_store_path_default_off"] is True
    assert payload["pgvector_store_summary"]["status"] == (
        "pgvector_store_path_default_off"
    )
    assert payload["provider_backed_automated_agents"] == 0
    assert payload["live_provider_backed_automated_agents"] == 0
    assert payload["mutation_authorized_agents"] == 0
    assert payload["mutation_authorized_scoring_agents"] == 0
    assert payload["mutation_authorized_ranking_agents"] == 0
    assert payload["mutation_authorized_application_agents"] == 0


def _assert_match(query: str, chunk_type: str) -> None:
    payload = getattr(services, HELPER_NAME)(
        query_text=query,
        chunk_type=chunk_type,
        **_payloads(),
    )

    assert payload["status"] == "vector_evidence_service_ready"
    assert payload["indexing_summary"]["chunk_count"] == 4
    assert payload["retrieval_summary"]["match_count"] == 1
    assert payload["matched_chunks"][0]["chunk_type"] == chunk_type
    _assert_safety(payload)


def test_service_indexes_and_retrieves_job_description_evidence():
    _assert_match("reliable machine learning platform", "job_description")


def test_service_indexes_and_retrieves_resume_profile_evidence():
    _assert_match("candidate Python production systems", "resume_profile")


def test_service_indexes_and_retrieves_trace_evidence():
    _assert_match("unsupported claim guardrail", "trace_evidence")


def test_service_indexes_and_retrieves_operator_review_packet_evidence():
    _assert_match(
        "operator human provenance confirmation",
        "operator_review_packet",
    )


def test_service_supports_metadata_filters():
    payload = getattr(services, HELPER_NAME)(
        query_text="Python production systems",
        filters={
            "chunk_type": "resume_profile",
            "job_id": "job-1",
            "company": "acme ai",
            "agent_name": "resume_match_agent",
            "stage": "resume_match",
        },
        **_payloads(),
    )

    assert payload["status"] == "vector_evidence_service_ready"
    assert payload["retrieval_summary"]["match_count"] == 1
    metadata = payload["matched_chunks"][0]["metadata"]
    assert metadata["job_id"] == "job-1"
    assert metadata["company"] == "Acme AI"
    assert metadata["agent_name"] == "resume_match_agent"
    assert metadata["stage"] == "resume_match"
    _assert_safety(payload)


def test_service_is_deterministic_and_does_not_mutate_inputs():
    sources = _payloads()
    before = deepcopy(sources)

    first = getattr(services, HELPER_NAME)(
        query_text="machine learning Python",
        top_k=2,
        **sources,
    )
    second = getattr(services, HELPER_NAME)(
        query_text="machine learning Python",
        top_k=2,
        **sources,
    )

    assert first == second
    assert sources == before
    assert first["retrieval_summary"]["top_k"] == 2
    _assert_safety(first)


def test_service_returns_safe_missing_query_fallback():
    payload = getattr(services, HELPER_NAME)(
        query_text=" ",
        **_payloads(),
    )

    assert payload["status"] == "vector_evidence_service_invalid_query"
    assert payload["matched_chunks"] == []
    assert payload["retrieval_summary"]["status"] == (
        "vector_evidence_retrieval_dry_run_invalid_query"
    )
    _assert_safety(payload)


def test_service_returns_safe_no_chunk_fallback():
    payload = getattr(services, HELPER_NAME)(
        query_text="machine learning",
        job_payload={"job_id": "job-empty"},
    )

    assert payload["status"] == "vector_evidence_service_no_chunks"
    assert payload["indexing_summary"]["status"] == (
        "vector_evidence_indexing_dry_run_no_chunks"
    )
    assert payload["retrieval_summary"]["status"] == (
        "vector_evidence_retrieval_dry_run_no_results"
    )
    assert payload["matched_chunks"] == []
    _assert_safety(payload)


def test_service_preserves_indexing_and_retrieval_summaries():
    payload = getattr(services, HELPER_NAME)(
        query_text="machine learning platform",
        **_payloads(),
    )

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
    assert payload["retrieval_summary"]["query"] == "machine learning platform"
    assert payload["retrieval_summary"]["match_count"] >= 1
    assert payload["indexing_dry_run"]["chunk_count"] == 4
    assert payload["retrieval_dry_run"]["matched_chunks"] == (
        payload["matched_chunks"]
    )
    _assert_safety(payload)


def test_service_helper_slice_uses_guarded_store_path_without_runtime_calls():
    source = (ROOT / "src/app/services.py").read_text(encoding="utf-8")
    start = source.index(f"def {HELPER_NAME}(")
    end = source.index(
        "\n\nHUMAN_REVIEWED_INFLUENCE_APPROVAL_REQUEST_FLAG",
        start,
    )
    helper_source = source[start:end]

    assert '"src.agents.vector_evidence_" + "indexing_dry_run"' in helper_source
    assert '"src.agents.vector_evidence_" + "retrieval_dry_run"' in helper_source
    assert "_vector_evidence_pgvector_store_path_payload(" in helper_source
    for marker in (
        "@app.",
        "router.",
        "agentic_review",
        "src.pipeline",
        "schema.sql",
        "create_embedding(",
        "embed(",
        "connect(",
        "cursor.execute",
        ".commit(",
        "score_resume_job_match(",
        "rank_jobs(",
        "create_approval_request(",
        "create_execution_request(",
        "create_execution_launch_request(",
        "execute_application(",
        "submit_application(",
        "openai",
        "anthropic",
        "llm_client",
    ):
        assert marker not in helper_source


def test_no_ui_schema_or_pipeline_uses_service_helper():
    protected_paths = (
        "src/app/static/agentic_review.js",
        "src/pipeline/collector.py",
        "src/pipeline/application_scorer.py",
        "src/pipeline/job_ranker.py",
        "src/storage/agent_trace/schema.sql",
        "src/storage/agentic_approvals/schema.sql",
        "src/storage/profile_resumes/schema.sql",
    )
    for relative_path in protected_paths:
        assert HELPER_NAME not in (ROOT / relative_path).read_text(
            encoding="utf-8"
        )

    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").lower()
    for dependency in ("pgvector", "pinecone", "chromadb", "faiss"):
        assert dependency not in requirements
