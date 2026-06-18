from copy import deepcopy
from pathlib import Path

from src.agents import vector_evidence_indexing_dry_run as indexing


ROOT = Path(__file__).resolve().parents[1]


def _metadata() -> dict:
    return {
        "job_id": "job-8c",
        "company": "Acme AI",
        "title": "ML Platform Engineer",
        "source": "greenhouse",
        "stage": "operator_review",
        "agent_name": "jd_intelligence_agent",
        "trace_id": "trace-8c",
        "run_id": "run-8c",
        "resume_version": "resume-v4",
        "profile_version": "profile-v5",
        "created_at": "2026-06-18T15:00:00Z",
        "safety_flags": {"human_review_required": True},
        "read_only": True,
    }


def _payloads() -> dict:
    metadata = _metadata()
    return {
        "job_payload": {
            **metadata,
            "job_description": "Build reliable ML platform services.",
        },
        "resume_profile_payload": {
            **metadata,
            "resume_text": "Built Python APIs and production ML systems.",
        },
        "trace_evidence_payload": {
            **metadata,
            "trace_evidence_pack": {
                "findings": ["source evidence available"],
                "readiness_status": "ready",
            },
        },
        "operator_review_packet_payload": {
            **metadata,
            "packet_status": "review_packet_ready",
            "recommended_operator_action": "review_evidence",
            "review_focus": ["confirm provenance"],
        },
    }


def _assert_safety(payload: dict) -> None:
    safety = payload["safety_metadata"]
    assert safety["read_only"] is True
    assert safety["advisory_only"] is True
    assert safety["vector_evidence_indexing_dry_run"] is True
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
    assert payload["indexing_executed"] is False


def test_builds_job_resume_trace_and_operator_review_chunk_candidates():
    payload = indexing.build_vector_evidence_indexing_dry_run_payload(**_payloads())
    by_type = {
        candidate["chunk_type"]: candidate
        for candidate in payload["chunk_candidates"]
    }

    assert payload["status"] == "vector_evidence_indexing_dry_run_ready"
    assert payload["chunk_count"] == 4
    assert payload["chunk_types_present"] == [
        "job_description",
        "operator_review_packet",
        "resume_profile",
        "trace_evidence",
    ]
    assert "Build reliable ML platform services." in by_type[
        "job_description"
    ]["evidence_text"]
    assert "Built Python APIs" in by_type["resume_profile"]["evidence_text"]
    assert "source evidence available" in by_type["trace_evidence"][
        "evidence_text"
    ]
    assert "review_evidence" in by_type["operator_review_packet"][
        "evidence_text"
    ]
    assert all(
        candidate["embedding"] is None
        for candidate in payload["chunk_candidates"]
    )
    _assert_safety(payload)


def test_preserves_phase8_metadata_fields():
    payload = indexing.build_vector_evidence_indexing_dry_run_payload(
        job_payload=_payloads()["job_payload"]
    )
    metadata = payload["chunk_candidates"][0]["metadata"]

    for field, value in _metadata().items():
        assert metadata[field] == value
    _assert_safety(payload)


def test_generates_deterministic_chunk_ids_and_does_not_mutate_inputs():
    sources = _payloads()
    before = deepcopy(sources)

    first = indexing.build_vector_evidence_indexing_dry_run_payload(**sources)
    second = indexing.build_vector_evidence_indexing_dry_run_payload(**sources)

    assert first == second
    assert sources == before
    assert [item["chunk_id"] for item in first["chunk_candidates"]] == [
        item["chunk_id"] for item in second["chunk_candidates"]
    ]
    _assert_safety(first)


def test_deduplicates_duplicate_chunks_deterministically():
    duplicate = {
        **_metadata(),
        "evidence_text": "Same evidence text",
        "stage": "shared_stage",
        "agent_name": "shared_agent",
    }

    payload = indexing.build_vector_evidence_indexing_dry_run_payload(
        job_payload=duplicate,
        job_description_payload=deepcopy(duplicate),
    )

    assert payload["chunk_count"] == 1
    assert payload["chunk_types_present"] == ["job_description"]
    _assert_safety(payload)


def test_future_outcome_is_generated_only_when_explicitly_supplied():
    without_future = indexing.build_vector_evidence_indexing_dry_run_payload(
        job_payload=_payloads()["job_payload"]
    )
    with_future = indexing.build_vector_evidence_indexing_dry_run_payload(
        future_application_outcome_payload={
            **_metadata(),
            "outcome_summary": "Human-recorded interview outcome.",
        }
    )

    assert "future_application_outcome_feedback" not in without_future[
        "chunk_types_present"
    ]
    assert with_future["chunk_types_present"] == [
        "future_application_outcome_feedback"
    ]
    _assert_safety(with_future)


def test_returns_safe_no_chunk_fallback_for_missing_or_unusable_text():
    empty = indexing.build_vector_evidence_indexing_dry_run_payload()
    unusable = indexing.build_vector_evidence_indexing_dry_run_payload(
        job_payload={"job_id": "job-empty"}
    )

    assert empty["status"] == "vector_evidence_indexing_dry_run_no_chunks"
    assert empty["chunk_candidates"] == []
    assert empty["chunk_count"] == 0
    assert unusable["status"] == "vector_evidence_indexing_dry_run_no_chunks"
    assert unusable["skipped_reasons"] == [
        {"source": "job_payload", "reason": "no_usable_evidence_text"}
    ]
    _assert_safety(empty)
    _assert_safety(unusable)


def test_helper_reuses_phase8b_contract_and_has_no_runtime_side_effect_calls():
    source = (
        ROOT / "src/agents/vector_evidence_indexing_dry_run.py"
    ).read_text(encoding="utf-8")

    assert "from src.agents import vector_evidence_contract" in source
    assert "build_vector_evidence_chunk_candidates(" in source
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
    helper_marker = "vector_evidence_indexing_dry_run"
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

