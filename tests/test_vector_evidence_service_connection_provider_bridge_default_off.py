# phase79b legacy guard marker: changes_only collector_hash_old 73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405
# phase56b legacy guard marker: changes_only bfa035faa8e89abd2b75095f68b45a282fb3b7fc8e5ff43e36c754db56ef12c2 1ff2a73993300f391aa1fb8151a4d225e803b6c5d499e311faa5058efc4b965c
# phase56a legacy guard marker: changes_only d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004 bfa035faa8e89abd2b75095f68b45a282fb3b7fc8e5ff43e36c754db56ef12c2
# phase26c legacy guard marker: changes_only fdbd820a68a356d894ac0b904bd649d511dcf501129d32ed00d34ffc7f927fd0 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c
# phase26b legacy guard marker: changes_only d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004
# phase23f legacy guard marker: changes_only d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c fdbd820a68a356d894ac0b904bd649d511dcf501129d32ed00d34ffc7f927fd0
# phase23f legacy guard marker: changes_only fdbd820a68a356d894ac0b904bd649d511dcf501129d32ed00d34ffc7f927fd0
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


def _assert_safety(payload: dict, *, wrote: bool = False) -> None:
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


def test_default_service_does_not_use_connection_provider():
    calls = []
    payload = _call(
        pgvector_connection_connector=lambda url: calls.append(url),
    )

    assert calls == []
    assert payload["pgvector_connection_provider_requested"] is False
    assert payload["pgvector_connection_provider_enabled"] is False
    assert payload["pgvector_connection_provider_used"] is False
    assert payload["pgvector_connection_provider_default_off"] is True
    assert payload["db_executor_created"] is False
    assert payload["db_connection_opened"] is False
    _assert_safety(payload)


def test_explicit_disabled_provider_does_not_open_connection():
    calls = []
    payload = _call(
        pgvector_connection_provider_enabled=False,
        pgvector_connection_database_url="postgres://fixture",
        pgvector_connection_connector=lambda url: calls.append(url),
    )

    assert calls == []
    assert payload["pgvector_connection_provider_requested"] is False
    assert payload["pgvector_store_path_requested"] is False
    _assert_safety(payload)


def test_enabled_provider_with_missing_config_is_safe():
    calls = []
    payload = _call(
        owner_user_id="owner-1",
        pgvector_connection_provider_enabled=True,
        pgvector_connection_environ={},
        pgvector_connection_connector=lambda url: calls.append(url),
    )

    assert calls == []
    assert payload["pgvector_connection_provider_requested"] is True
    assert payload["pgvector_connection_provider_enabled"] is True
    assert payload["pgvector_connection_provider_used"] is False
    assert payload["pgvector_connection_provider_status"] == (
        "pgvector_connection_provider_missing_config"
    )
    assert payload["pgvector_store_summary"]["status"] == (
        "pgvector_connection_provider_missing_config"
    )
    assert payload["db_executor_created"] is False
    assert payload["db_connection_opened"] is False
    assert payload["chunks_write_attempted"] == 0
    assert payload["retrieval_events_write_attempted"] == 0
    _assert_safety(payload)


def test_fake_provider_executor_flows_into_db_executor_bridge():
    connector_calls = []
    executor_calls = []

    def fake_db_executor(request):
        executor_calls.append(deepcopy(request))
        return {"rows": [{"written": True}], "driver": "fake"}

    def fake_connector(database_url):
        connector_calls.append(database_url)
        return fake_db_executor

    baseline = _call()
    payload = _call(
        owner_user_id="owner-1",
        pgvector_connection_provider_enabled=True,
        pgvector_connection_environ={
            "APPLYLENS_VECTOR_EVIDENCE_DATABASE_URL": (
                "postgres://vector-fixture"
            ),
        },
        pgvector_connection_connector=fake_connector,
    )

    assert connector_calls == ["postgres://vector-fixture"]
    assert len(executor_calls) == 5
    assert [call["prepared_payload"]["table"] for call in executor_calls[:4]] == [
        "vector_evidence_chunks",
        "vector_evidence_chunks",
        "vector_evidence_chunks",
        "vector_evidence_chunks",
    ]
    assert executor_calls[-1]["prepared_payload"]["table"] == (
        "vector_evidence_retrieval_events"
    )
    assert all(
        call["prepared_payload"]["table"] != "vector_evidence_embeddings"
        for call in executor_calls
    )
    assert payload["pgvector_connection_provider_used"] is True
    assert payload["db_executor_created"] is True
    assert payload["db_connection_opened"] is True
    assert payload["pgvector_db_executor_path_used"] is True
    assert payload["chunks_written"] == 4
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
    _assert_safety(payload, wrote=True)


def test_service_provider_bridge_does_not_mutate_inputs_or_connect_on_import():
    sources = _payloads()
    before = deepcopy(sources)
    calls = []
    getattr(services, HELPER)(
        query_text="reliable machine learning platform",
        pgvector_connection_connector=lambda url: calls.append(url),
        **sources,
    )

    assert sources == before
    assert calls == []
    source = (ROOT / "src/app/services.py").read_text(encoding="utf-8")
    start = source.index(
        "def _vector_evidence_pgvector_connection_provider_payload("
    )
    end = source.index(
        "\n\ndef pgvector_extension_probe_service_helper_payload(",
        start,
    )
    snippet = source[start:end]
    assert "build_vector_evidence_db_executor" in snippet
    for marker in (
        "execute_pgvector_schema_setup(",
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


def test_api_ui_pipeline_schema_and_dependencies_remain_unchanged():
    protected_hashes = {
        "src/app/api.py": ("d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004"),
        "src/app/static/agentic_review.js": ("fdbd820a68a356d894ac0b904bd649d511dcf501129d32ed00d34ffc7f927fd0"),
        "src/pipeline/collector.py": ("1d35d00e54d1d858134b2e524955887bd7adbbce3a01e53d1782debc4584490a"),
        "requirements.txt": ("5dc563901e19c10a0f59fe811ec6961ee47f837827a7448e3a669aed9f244cc6"),
        "src/storage/vector_evidence/schema.sql": ("4b34a928393fcce6696a2f35d7ee62339b0483cc248daee3f0e57bdb50c11dff"),
    }
    for relative_path, expected_hash in protected_hashes.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )
