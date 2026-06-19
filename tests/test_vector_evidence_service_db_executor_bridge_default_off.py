from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from src.app import services


ROOT = Path(__file__).resolve().parents[1]
HELPER = "vector_evidence_service_helper_payload"


def _metadata(job_id: str, stage: str, agent_name: str) -> dict:
    return {
        "job_id": job_id,
        "company": "Acme AI",
        "title": "ML Platform Engineer",
        "source": "greenhouse",
        "stage": stage,
        "agent_name": agent_name,
        "trace_id": f"trace-{job_id}",
        "run_id": f"run-{job_id}",
        "resume_version": "resume-v4",
        "profile_version": "profile-v5",
        "created_at": "2026-06-18T17:00:00Z",
        "read_only": True,
    }


def _payloads() -> dict:
    return {
        "job_payload": {
            **_metadata("job-1", "jd_intelligence", "jd_intelligence_agent"),
            "job_description": "Build reliable machine learning platform services.",
        },
        "resume_profile_payload": {
            **_metadata("job-1", "resume_match", "resume_match_agent"),
            "resume_text": "Candidate built Python APIs and production ML systems.",
        },
        "trace_evidence_payload": {
            **_metadata("job-2", "trace_readback", "critic_guardrail"),
            "trace_evidence": "Trace found unsupported claim guardrail evidence.",
        },
        "operator_review_packet_payload": {
            **_metadata(
                "job-3",
                "operator_review",
                "pipeline_agent_review_packet",
            ),
            "evidence_text": "Operator review requests provenance confirmation.",
        },
    }


def _call(**updates) -> dict:
    kwargs = {
        "query_text": "reliable machine learning platform",
        **_payloads(),
    }
    kwargs.update(updates)
    return getattr(services, HELPER)(**kwargs)


def _assert_guardrails(payload: dict, *, wrote: bool = False) -> None:
    safety = payload["safety_metadata"]
    assert safety["advisory_only"] is True
    assert safety["embeddings_created"] is False
    assert safety["provider_calls_made"] is False
    assert safety["did_write_database"] is wrote
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


def test_default_service_remains_dry_run_without_db_execution():
    calls = []
    payload = _call(pgvector_db_executor=lambda request: calls.append(request))

    assert calls == []
    assert payload["pgvector_db_executor_path_requested"] is False
    assert payload["pgvector_db_executor_path_used"] is False
    assert payload["pgvector_db_executor_default_off"] is True
    assert payload["chunks_write_attempted"] == 0
    assert payload["retrieval_events_write_attempted"] == 0
    assert payload["safety_metadata"]["db_executor_supplied"] is True
    assert payload["safety_metadata"]["read_only"] is True
    _assert_guardrails(payload)


def test_enabled_db_path_without_executor_is_safe_not_configured():
    payload = _call(
        owner_user_id="owner-1",
        pgvector_store_enabled=True,
        pgvector_db_executor_enabled=True,
    )

    assert payload["pgvector_db_executor_path_requested"] is True
    assert payload["pgvector_db_executor_supplied"] is False
    assert payload["pgvector_db_executor_path_used"] is False
    assert payload["pgvector_store_summary"]["status"] == (
        "pgvector_db_executor_path_not_configured"
    )
    assert payload["chunks_written"] == 0
    assert payload["retrieval_events_written"] == 0
    _assert_guardrails(payload)


def test_explicit_fake_db_executor_receives_chunk_and_event_writes():
    calls = []

    def fake_executor(request):
        calls.append(deepcopy(request))
        return {"rows": [{"written": True}], "driver": "fake"}

    baseline = _call()
    payload = _call(
        owner_user_id="owner-1",
        pgvector_store_enabled=True,
        pgvector_db_executor_enabled=True,
        pgvector_db_executor=fake_executor,
    )

    assert len(calls) == 5
    assert [call["prepared_payload"]["table"] for call in calls[:4]] == [
        "vector_evidence_chunks",
        "vector_evidence_chunks",
        "vector_evidence_chunks",
        "vector_evidence_chunks",
    ]
    assert calls[-1]["prepared_payload"]["table"] == (
        "vector_evidence_retrieval_events"
    )
    assert all(
        call["prepared_payload"]["table"] != "vector_evidence_embeddings"
        for call in calls
    )
    assert payload["pgvector_db_executor_path_requested"] is True
    assert payload["pgvector_db_executor_supplied"] is True
    assert payload["pgvector_db_executor_path_used"] is True
    assert payload["chunks_write_attempted"] == 4
    assert payload["chunks_written"] == 4
    assert payload["retrieval_events_write_attempted"] == 1
    assert payload["retrieval_events_written"] == 1
    for key in (
        "status",
        "indexing_summary",
        "retrieval_summary",
        "matched_chunks",
        "skipped_reasons",
        "indexing_dry_run",
        "retrieval_dry_run",
    ):
        assert payload[key] == baseline[key]
    assert payload["safety_metadata"]["read_only"] is True
    _assert_guardrails(payload, wrote=True)


def test_db_bridge_does_not_mutate_inputs_or_open_connections_automatically():
    sources = _payloads()
    before = deepcopy(sources)
    payload = getattr(services, HELPER)(
        query_text="reliable machine learning platform",
        owner_user_id="owner-1",
        pgvector_store_enabled=True,
        pgvector_db_executor_enabled=True,
        pgvector_db_executor=lambda request: {"rows": []},
        **sources,
    )

    assert sources == before
    assert payload["pgvector_db_executor_path_used"] is True
    source = (ROOT / "src/app/services.py").read_text(encoding="utf-8")
    start = source.index("def _vector_evidence_pgvector_store_path_payload(")
    end = source.index(
        "\n\ndef pgvector_extension_probe_service_helper_payload(",
        start,
    )
    snippet = source[start:end]
    for marker in (
        "psycopg",
        "DATABASE_URL",
        "connect(",
        ".commit(",
        "create_embedding(",
        "embeddings.create(",
        "openai",
        "anthropic",
        "llm_client",
        "src.pipeline",
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
    _assert_guardrails(payload, wrote=True)


def test_api_ui_pipeline_dependencies_and_schema_remain_unchanged():
    protected_hashes = {
        "src/app/api.py": (
            "4daeda11d22dd8f1ddf1be0b47571e8443d48d290a962771a3ec7eb9c63e11f9"
        ),
        "src/app/static/agentic_review.js": (
            "450b95cdb1a838854a8be1ed11f3ae9f0fa886d11cc0724eb5e63384936f75bc"
        ),
        "src/pipeline/collector.py": (
            "cbcd90f3d8d367ebe6f178c211406da909f340ce62681047b70efe4fb4a30fa7"
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

    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").lower()
    for dependency in ("pgvector", "pinecone", "chromadb", "faiss", "langgraph"):
        assert dependency not in requirements
