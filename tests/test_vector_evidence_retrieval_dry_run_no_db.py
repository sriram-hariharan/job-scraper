# phase107b legacy guard marker: changes_only requirements_hash_old 96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004 src/app/api.py
from copy import deepcopy
from pathlib import Path

from src.agents import vector_evidence_indexing_dry_run as indexing
from src.agents import vector_evidence_retrieval_dry_run as retrieval


ROOT = Path(__file__).resolve().parents[1]


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
        "created_at": "2026-06-18T16:00:00Z",
        "safety_flags": {"human_review_required": True},
        "read_only": True,
    }


def _indexing_payload() -> dict:
    return indexing.build_vector_evidence_indexing_dry_run_payload(
        job_payload={
            **_metadata(
                job_id="job-1",
                company="Acme AI",
                stage="jd_intelligence",
                agent_name="jd_intelligence_agent",
            ),
            "job_description": (
                "Build reliable machine learning platform services with Python."
            ),
        },
        resume_profile_payload={
            **_metadata(
                job_id="job-1",
                company="Acme AI",
                stage="resume_match",
                agent_name="resume_match_agent",
            ),
            "resume_text": (
                "Candidate built Python APIs and production machine learning systems."
            ),
        },
        trace_evidence_payload={
            **_metadata(
                job_id="job-2",
                company="Beta Data",
                stage="trace_readback",
                agent_name="critic_guardrail",
            ),
            "trace_evidence": (
                "Trace validation found unsupported claim risk and guardrail evidence."
            ),
        },
        operator_review_packet_payload={
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
    )


def _assert_safety(payload: dict) -> None:
    safety = payload["safety_metadata"]
    assert safety["read_only"] is True
    assert safety["advisory_only"] is True
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
    assert safety["service_helper_added"] is False
    assert safety["ui_action_added"] is False
    assert safety["pipeline_stage_added"] is False
    assert safety["auto_apply_enabled"] is False
    assert safety["mutation_authorized"] is False
    assert payload["provider_backed_automated_agents"] == 0
    assert payload["live_provider_backed_automated_agents"] == 0
    assert payload["mutation_authorized_agents"] == 0
    assert payload["retrieval_executed"] is False


def _assert_single_match(query: str, expected_chunk_type: str) -> None:
    payload = retrieval.build_vector_evidence_retrieval_dry_run_payload(
        query_text=query,
        indexing_dry_run_payload=_indexing_payload(),
        chunk_type=expected_chunk_type,
    )

    assert payload["status"] == "vector_evidence_retrieval_dry_run_ready"
    assert payload["match_count"] == 1
    assert payload["matched_chunks"][0]["chunk_type"] == expected_chunk_type
    assert payload["matched_chunks"][0]["retrieval_score"] > 0
    assert payload["matched_chunks"][0]["retrieval_confidence"] > 0
    _assert_safety(payload)


def test_retrieves_matching_job_description_chunk():
    _assert_single_match("reliable machine learning platform", "job_description")


def test_retrieves_matching_resume_profile_chunk():
    _assert_single_match("candidate built production systems", "resume_profile")


def test_retrieves_matching_trace_evidence_chunk():
    _assert_single_match("unsupported claim guardrail", "trace_evidence")


def test_retrieves_matching_operator_review_packet_chunk():
    _assert_single_match(
        "operator human provenance confirmation",
        "operator_review_packet",
    )


def test_supports_chunk_type_and_metadata_filters():
    payload = retrieval.build_vector_evidence_retrieval_dry_run_payload(
        query_text="machine learning Python",
        indexing_dry_run_payload=_indexing_payload(),
        filters={
            "chunk_type": "resume_profile",
            "job_id": "job-1",
            "company": "acme ai",
            "agent_name": "resume_match_agent",
            "stage": "resume_match",
        },
    )

    assert payload["match_count"] == 1
    match = payload["matched_chunks"][0]
    assert match["chunk_type"] == "resume_profile"
    assert match["metadata"]["job_id"] == "job-1"
    assert match["metadata"]["company"] == "Acme AI"
    assert match["metadata"]["agent_name"] == "resume_match_agent"
    assert match["metadata"]["stage"] == "resume_match"
    _assert_safety(payload)


def test_returns_deterministic_top_k_ordering():
    indexing_payload = _indexing_payload()
    candidates = deepcopy(indexing_payload["chunk_candidates"])
    candidates.extend(
        [
            {
                **deepcopy(candidates[0]),
                "chunk_id": "vector-evidence:aaa",
                "chunk_type": "job_description",
                "evidence_text": "python machine learning evidence",
            },
            {
                **deepcopy(candidates[0]),
                "chunk_id": "vector-evidence:bbb",
                "chunk_type": "operator_review_packet",
                "evidence_text": "python machine learning evidence",
            },
        ]
    )
    before = deepcopy(candidates)

    first = retrieval.build_vector_evidence_retrieval_dry_run_payload(
        query_text="python machine learning evidence",
        chunk_candidates=candidates,
        top_k=2,
    )
    second = retrieval.build_vector_evidence_retrieval_dry_run_payload(
        query_text="python machine learning evidence",
        chunk_candidates=candidates,
        top_k=2,
    )

    assert first == second
    assert candidates == before
    assert first["top_k"] == 2
    assert first["match_count"] == 2
    ordering = [
        (
            item["retrieval_score"],
            item["chunk_type"],
            item["chunk_id"],
        )
        for item in first["matched_chunks"]
    ]
    assert ordering == sorted(
        ordering,
        key=lambda item: (-item[0], item[1], item[2]),
    )
    _assert_safety(first)


def test_returns_safe_no_result_fallback():
    payload = retrieval.build_vector_evidence_retrieval_dry_run_payload(
        query_text="quantum cryptography",
        indexing_dry_run_payload=_indexing_payload(),
    )

    assert payload["status"] == "vector_evidence_retrieval_dry_run_no_results"
    assert payload["matched_chunks"] == []
    assert payload["match_count"] == 0
    assert payload["fallback"]["used"] is True
    assert payload["fallback"]["reason"] == "no_matching_vector_evidence"
    _assert_safety(payload)


def test_validates_missing_query_safely():
    payload = retrieval.build_vector_evidence_retrieval_dry_run_payload(
        query_text=" ",
        indexing_dry_run_payload=_indexing_payload(),
    )

    assert payload["status"] == "vector_evidence_retrieval_dry_run_invalid_query"
    assert payload["matched_chunks"] == []
    assert payload["match_count"] == 0
    assert payload["request_contract"]["status"] == (
        "vector_evidence_invalid_request"
    )
    assert payload["skipped_reasons"] == [
        {"chunk_id": "", "reason": "missing_query_text"}
    ]
    _assert_safety(payload)


def test_helper_reuses_phase8_contract_and_indexing_dry_run_without_side_effects():
    source = (
        ROOT / "src/agents/vector_evidence_retrieval_dry_run.py"
    ).read_text(encoding="utf-8")

    assert "from src.agents import vector_evidence_contract" in source
    assert "from src.agents import vector_evidence_indexing_dry_run" in source
    assert "build_vector_evidence_chunk_candidates(" in source
    assert "build_vector_retrieval_request_contract(" in source
    for marker in (
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
    ):
        assert marker not in source


def test_no_dependency_schema_api_service_ui_or_pipeline_change():
    helper_marker = "vector_evidence_retrieval_dry_run"
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
    for dependency in ("pgvector", "pinecone", "chromadb", "faiss"):
        assert dependency not in requirements
