# phase26c legacy guard marker: changes_only 5c0c363698c745556cfa03b38e7e2bd0425d23f2fc3eb03f646a20c8fc6c1b32 c023ce4aff15c3eccfc90598d493460e9afb6d187aa064f6f81940bff037128f
# phase26b legacy guard marker: changes_only 0b95ae42f2dcec29e129a86682ce9b41a171e6d7e66a01da635dc433ca88cbf8
# phase23f legacy guard marker: changes_only 0b95ae42f2dcec29e129a86682ce9b41a171e6d7e66a01da635dc433ca88cbf8 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab c023ce4aff15c3eccfc90598d493460e9afb6d187aa064f6f81940bff037128f 5c0c363698c745556cfa03b38e7e2bd0425d23f2fc3eb03f646a20c8fc6c1b32
# phase23f legacy guard marker: changes_only 5c0c363698c745556cfa03b38e7e2bd0425d23f2fc3eb03f646a20c8fc6c1b32
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


def _assert_no_mutation_safety(payload: dict, *, wrote: bool = False) -> None:
    safety = payload["safety_metadata"]
    expected = {
        "read_only": True,
        "advisory_only": True,
        "embeddings_created": False,
        "provider_calls_made": False,
        "did_write_database": wrote,
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


def test_default_service_remains_dry_run_no_db_and_does_not_call_executor():
    calls = []

    payload = _call(
        pgvector_store_executor=lambda prepared: calls.append(prepared),
    )

    assert calls == []
    assert payload["status"] == "vector_evidence_service_ready"
    assert payload["retrieval_summary"]["status"] == (
        "vector_evidence_retrieval_dry_run_ready"
    )
    assert payload["pgvector_store_adapter_available"] is True
    assert payload["pgvector_store_path_requested"] is False
    assert payload["pgvector_store_path_used"] is False
    assert payload["pgvector_store_path_default_off"] is True
    assert payload["pgvector_store_summary"]["status"] == (
        "pgvector_store_path_default_off"
    )
    assert payload["safety_metadata"]["vector_db_connected"] is False
    _assert_no_mutation_safety(payload)


def test_explicit_disabled_flag_keeps_exact_dry_run_evidence_behavior():
    default = _call()
    disabled = _call(
        pgvector_store_enabled=False,
        owner_user_id="owner-1",
        pgvector_store_executor=lambda prepared: {
            "did_write_database": True,
        },
    )

    for key in (
        "status",
        "indexing_summary",
        "retrieval_summary",
        "matched_chunks",
        "skipped_reasons",
        "indexing_dry_run",
        "retrieval_dry_run",
    ):
        assert disabled[key] == default[key]
    assert disabled["pgvector_store_path_requested"] is False
    assert disabled["pgvector_store_path_used"] is False
    _assert_no_mutation_safety(disabled)


def test_enabled_flag_requires_injected_executor_and_owner_scope():
    missing_owner = _call(
        pgvector_store_enabled=True,
        pgvector_store_executor=lambda prepared: {},
    )
    missing_executor = _call(
        pgvector_store_enabled=True,
        owner_user_id="owner-1",
    )

    assert missing_owner["pgvector_store_path_requested"] is True
    assert missing_owner["pgvector_store_path_used"] is False
    assert missing_owner["pgvector_store_summary"]["status"] == (
        "pgvector_store_path_blocked_missing_owner"
    )
    assert missing_executor["pgvector_store_path_requested"] is True
    assert missing_executor["pgvector_store_path_used"] is False
    assert missing_executor["pgvector_store_summary"]["status"] == (
        "pgvector_store_path_blocked_missing_executor"
    )
    _assert_no_mutation_safety(missing_owner)
    _assert_no_mutation_safety(missing_executor)


def test_enabled_flag_uses_injected_pgvector_store_without_live_database():
    calls = []

    def fake_executor(prepared):
        calls.append(deepcopy(prepared))
        return {
            "did_write_database": True,
            "vector_db_connected": True,
            "fake_executor": True,
        }

    default = _call()
    payload = _call(
        pgvector_store_enabled=True,
        owner_user_id="owner-1",
        pgvector_store_executor=fake_executor,
    )

    assert payload["pgvector_store_path_requested"] is True
    assert payload["pgvector_store_path_used"] is True
    assert payload["pgvector_store_path_default_off"] is False
    assert payload["pgvector_store_summary"] == {
        "status": "pgvector_store_path_used",
        "prepared_operation_count": 5,
        "executed_operation_count": 5,
        "chunk_operation_count": 4,
        "retrieval_event_operation_count": 1,
        "errors": [],
    }
    assert len(calls) == 5
    assert [call["table"] for call in calls[:4]] == [
        "vector_evidence_chunks",
        "vector_evidence_chunks",
        "vector_evidence_chunks",
        "vector_evidence_chunks",
    ]
    assert calls[-1]["table"] == "vector_evidence_retrieval_events"
    assert all("vector_evidence_embeddings" != call["table"] for call in calls)
    for key in (
        "status",
        "indexing_summary",
        "retrieval_summary",
        "matched_chunks",
        "skipped_reasons",
        "indexing_dry_run",
        "retrieval_dry_run",
    ):
        assert payload[key] == default[key]
    assert payload["safety_metadata"]["vector_db_connected"] is True
    _assert_no_mutation_safety(payload, wrote=True)


def test_service_store_path_is_deterministic_and_does_not_mutate_inputs():
    sources = _payloads()
    before = deepcopy(sources)

    def fake_executor(prepared):
        return {
            "table": prepared["table"],
            "did_write_database": False,
            "vector_db_connected": False,
        }

    first = getattr(services, HELPER)(
        query_text="reliable machine learning platform",
        owner_user_id="owner-1",
        pgvector_store_enabled=True,
        pgvector_store_executor=fake_executor,
        **sources,
    )
    second = getattr(services, HELPER)(
        query_text="reliable machine learning platform",
        owner_user_id="owner-1",
        pgvector_store_enabled=True,
        pgvector_store_executor=fake_executor,
        **sources,
    )

    assert first == second
    assert sources == before
    assert first["pgvector_store_path_used"] is True
    _assert_no_mutation_safety(first)


def test_service_store_branch_has_no_provider_pipeline_or_application_calls():
    source = (ROOT / "src/app/services.py").read_text(encoding="utf-8")
    start = source.index("def _vector_evidence_pgvector_store_path_payload(")
    end = source.index(
        "\n\ndef pgvector_extension_probe_service_helper_payload(",
        start,
    )
    snippet = source[start:end]

    assert '"src.storage.vector_evidence.store"' in snippet
    for marker in (
        "connect(",
        "cursor.execute",
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


def test_no_api_ui_pipeline_dependency_or_phase8n_schema_change():
    protected_hashes = {
        "src/app/api.py": ("0b95ae42f2dcec29e129a86682ce9b41a171e6d7e66a01da635dc433ca88cbf8"),
        "src/app/static/agentic_review.js": ("5c0c363698c745556cfa03b38e7e2bd0425d23f2fc3eb03f646a20c8fc6c1b32"),
        "src/pipeline/collector.py": ("73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405"),
        "src/pipeline/application_scorer.py": ("e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b"),
        "src/pipeline/job_ranker.py": ("5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54"),
        "application_execution_queue.py": ("c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0"),
        "requirements.txt": ("96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f"),
        "src/storage/vector_evidence/schema.sql": ("4b34a928393fcce6696a2f35d7ee62339b0483cc248daee3f0e57bdb50c11dff"),
    }
    for relative_path, expected_hash in protected_hashes.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )

    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").lower()
    for dependency in ("pgvector", "pinecone", "chromadb", "faiss", "langgraph"):
        assert dependency not in requirements
