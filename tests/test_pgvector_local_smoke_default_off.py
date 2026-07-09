# phase79b legacy guard marker: changes_only collector_hash_old 73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405
# phase56b legacy guard marker: changes_only bfa035faa8e89abd2b75095f68b45a282fb3b7fc8e5ff43e36c754db56ef12c2 1ff2a73993300f391aa1fb8151a4d225e803b6c5d499e311faa5058efc4b965c
# phase56a legacy guard marker: changes_only d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004 bfa035faa8e89abd2b75095f68b45a282fb3b7fc8e5ff43e36c754db56ef12c2
# phase26c legacy guard marker: changes_only fdbd820a68a356d894ac0b904bd649d511dcf501129d32ed00d34ffc7f927fd0 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c
# phase26b legacy guard marker: changes_only d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004
# phase23f legacy guard marker: changes_only d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c fdbd820a68a356d894ac0b904bd649d511dcf501129d32ed00d34ffc7f927fd0
# phase23f legacy guard marker: changes_only fdbd820a68a356d894ac0b904bd649d511dcf501129d32ed00d34ffc7f927fd0
import importlib
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from src.storage.vector_evidence import smoke


ROOT = Path(__file__).resolve().parents[1]


def _assert_safety(payload: dict, *, wrote: bool = False) -> None:
    safety = payload["safety_metadata"]
    assert safety["pgvector_local_smoke"] is True
    assert safety["operator_triggered_only"] is True
    assert safety["default_off"] is True
    assert safety["embeddings_written"] is False
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


def test_default_smoke_path_is_skipped_without_connection():
    calls = []
    payload = smoke.run_vector_evidence_pgvector_smoke(
        connector=lambda url: calls.append(url)
    )

    assert calls == []
    assert payload["status"] == "pgvector_local_smoke_skipped_default_off"
    assert payload["enabled"] is False
    assert payload["operations_attempted"] == []
    _assert_safety(payload)


def test_explicit_disabled_smoke_does_nothing():
    calls = []
    payload = smoke.run_vector_evidence_pgvector_smoke(
        enabled=False,
        owner_user_id="owner-1",
        database_url="postgres://fixture",
        connector=lambda url: calls.append(url),
    )

    assert calls == []
    assert payload["operations_completed"] == []
    _assert_safety(payload)


def test_import_opens_no_connection_and_runs_no_smoke():
    reloaded = importlib.reload(smoke)
    source = (
        ROOT / "src/storage/vector_evidence/smoke.py"
    ).read_text(encoding="utf-8")

    assert reloaded.SMOKE_VERSION.startswith("phase-8t")
    assert "run_vector_evidence_pgvector_smoke()" not in source
    assert "if __name__ ==" not in source


def test_enabled_fake_connector_exercises_schema_chunk_and_event():
    connector_calls = []
    executor_calls = []

    def fake_executor(request):
        executor_calls.append(deepcopy(request))
        table = request.get("prepared_payload", {}).get("table", "")
        if table == "vector_evidence_chunks":
            return {"rows": [{"chunk_id": "smoke-chunk"}]}
        if table == "vector_evidence_retrieval_events":
            return {"rows": [{"retrieval_event_id": "smoke-event"}]}
        return {"schema_applied": True}

    def fake_connector(database_url):
        connector_calls.append(database_url)
        return fake_executor

    payload = smoke.run_vector_evidence_pgvector_smoke(
        enabled=True,
        owner_user_id="owner-1",
        database_url="postgres://fixture",
        connector=fake_connector,
    )

    assert connector_calls == ["postgres://fixture"]
    assert len(executor_calls) == 3
    assert "CREATE TABLE IF NOT EXISTS vector_evidence_chunks" in (
        executor_calls[0]["sql"]
    )
    assert executor_calls[1]["prepared_payload"]["table"] == (
        "vector_evidence_chunks"
    )
    assert executor_calls[2]["prepared_payload"]["table"] == (
        "vector_evidence_retrieval_events"
    )
    assert all(
        call.get("prepared_payload", {}).get("table")
        != "vector_evidence_embeddings"
        for call in executor_calls
    )
    assert payload["status"] == "pgvector_local_smoke_completed"
    assert payload["operations_completed"] == [
        "schema_setup",
        "chunk_insert",
        "retrieval_event_insert",
    ]
    assert payload["schema_setup_executed"] is True
    assert payload["chunk_insert_executed"] is True
    assert payload["retrieval_event_insert_executed"] is True
    _assert_safety(payload, wrote=True)


def test_enabled_smoke_requires_explicit_connector():
    payload = smoke.run_vector_evidence_pgvector_smoke(
        enabled=True,
        owner_user_id="owner-1",
        database_url="postgres://fixture",
    )

    assert payload["status"] == "pgvector_local_smoke_connector_not_configured"
    assert payload["operations_attempted"] == []
    _assert_safety(payload)


def test_no_api_ui_pipeline_schema_or_dependency_change():
    protected_hashes = {
        "src/app/api.py": ("d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004"),
        "src/app/static/agentic_review.js": ("fdbd820a68a356d894ac0b904bd649d511dcf501129d32ed00d34ffc7f927fd0"),
        "src/pipeline/collector.py": ("1d35d00e54d1d858134b2e524955887bd7adbbce3a01e53d1782debc4584490a"),
        "src/pipeline/application_scorer.py": ("e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b"),
        "src/pipeline/job_ranker.py": ("5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54"),
        "application_execution_queue.py": ("c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0"),
        "requirements.txt": ("5dc563901e19c10a0f59fe811ec6961ee47f837827a7448e3a669aed9f244cc6"),
        "src/storage/vector_evidence/schema.sql": ("4b34a928393fcce6696a2f35d7ee62339b0483cc248daee3f0e57bdb50c11dff"),
    }
    for relative_path, expected_hash in protected_hashes.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )

    source = (
        ROOT / "src/storage/vector_evidence/smoke.py"
    ).read_text(encoding="utf-8")
    for marker in (
        "prepare_embedding_insert_payload(",
        "execute_vector_evidence_embedding_insert(",
        "create_embedding(",
        "embeddings.create(",
        "openai",
        "anthropic",
        "src.pipeline",
        "src.app.api",
        "score_resume_job_match(",
        "rank_jobs(",
        "create_approval_request(",
        "record_approval_decision(",
        "create_execution_request(",
        "create_execution_launch_request(",
        "execute_application(",
        "submit_application(",
        ".commit(",
    ):
        assert marker not in source
