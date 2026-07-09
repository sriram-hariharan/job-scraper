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

from src.storage.admin_tools import vector_evidence_pgvector_smoke as command
from src.storage.vector_evidence import smoke


ROOT = Path(__file__).resolve().parents[1]


def _assert_safety(payload: dict, *, read: bool = False) -> None:
    safety = payload["safety_metadata"]
    assert safety["read_only"] is True
    assert safety["advisory_only"] is True
    assert safety["pgvector_smoke_readback"] is True
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
    assert safety["pipeline_stage_added"] is False
    assert safety["auto_apply_enabled"] is False
    assert safety["mutation_authorized"] is False
    assert payload["provider_backed_automated_agents"] == 0
    assert payload["live_provider_backed_automated_agents"] == 0
    assert payload["mutation_authorized_agents"] == 0
    assert payload["mutation_authorized_scoring_agents"] == 0
    assert payload["mutation_authorized_ranking_agents"] == 0
    assert payload["mutation_authorized_application_agents"] == 0


def test_default_readback_is_skipped_and_opens_no_connection():
    payload = smoke.verify_vector_evidence_pgvector_smoke_readback()

    assert payload["status"] == (
        "pgvector_smoke_readback_skipped_default_off"
    )
    assert payload["readback_attempted"] is False
    assert payload["readback_executed"] is False
    assert payload["rows_read"] == 0
    _assert_safety(payload)


def test_enabled_fake_executor_reports_chunk_and_event_found():
    calls = []
    rows = [
        {"record_type": "chunk", "record_id": "smoke-chunk"},
        {"record_type": "retrieval_event", "record_id": "smoke-event"},
    ]

    def fake_executor(request):
        calls.append(deepcopy(request))
        return {"rows": deepcopy(rows)}

    payload = smoke.verify_vector_evidence_pgvector_smoke_readback(
        enabled=True,
        owner_user_id="owner-1",
        smoke_identifier=smoke.SMOKE_IDENTIFIER,
        db_executor=fake_executor,
    )

    assert len(calls) == 1
    assert "FROM vector_evidence_chunks" in calls[0]["sql"]
    assert "FROM vector_evidence_retrieval_events" in calls[0]["sql"]
    assert calls[0]["params"] == (
        "owner-1",
        smoke.SMOKE_IDENTIFIER,
        "owner-1",
        smoke.SMOKE_IDENTIFIER,
    )
    assert payload["status"] == "pgvector_smoke_readback_verified"
    assert payload["readback_attempted"] is True
    assert payload["readback_executed"] is True
    assert payload["smoke_chunk_found"] is True
    assert payload["retrieval_event_found"] is True
    assert payload["rows_read"] == 2
    _assert_safety(payload, read=True)


def test_enabled_readback_can_report_each_record_independently():
    chunk_only = smoke.verify_vector_evidence_pgvector_smoke_readback(
        enabled=True,
        owner_user_id="owner-1",
        smoke_identifier=smoke.SMOKE_IDENTIFIER,
        db_executor=lambda request: {
            "rows": [{"record_type": "chunk", "record_id": "smoke-chunk"}]
        },
    )
    event_only = smoke.verify_vector_evidence_pgvector_smoke_readback(
        enabled=True,
        owner_user_id="owner-1",
        smoke_identifier=smoke.SMOKE_IDENTIFIER,
        db_executor=lambda request: {
            "rows": [
                {
                    "record_type": "retrieval_event",
                    "record_id": "smoke-event",
                }
            ]
        },
    )

    assert chunk_only["smoke_chunk_found"] is True
    assert chunk_only["retrieval_event_found"] is False
    assert event_only["smoke_chunk_found"] is False
    assert event_only["retrieval_event_found"] is True
    _assert_safety(chunk_only, read=True)
    _assert_safety(event_only, read=True)


def test_manual_command_readback_flag_uses_same_explicit_executor():
    connector_calls = []
    executor_calls = []

    def fake_executor(request):
        executor_calls.append(deepcopy(request))
        if request.get("operation") == "read_vector_evidence_smoke_records":
            return {
                "rows": [
                    {"record_type": "chunk", "record_id": "smoke-chunk"},
                    {
                        "record_type": "retrieval_event",
                        "record_id": "smoke-event",
                    },
                ]
            }
        return {"rows": [{"ok": True}]}

    def fake_connector(database_url):
        connector_calls.append(database_url)
        return fake_executor

    payload = command.run_pgvector_real_local_smoke_command(
        owner_user_id="owner-1",
        environ={
            "APPLYLENS_VECTOR_EVIDENCE_PGVECTOR_ENABLED": "true",
            "APPLYLENS_VECTOR_EVIDENCE_DATABASE_URL": (
                "postgres://vector-fixture"
            ),
        },
        connector=fake_connector,
        verify_readback=True,
    )

    assert connector_calls == ["postgres://vector-fixture"]
    assert len(executor_calls) == 4
    assert payload["readback_status"] == "pgvector_smoke_readback_verified"
    assert payload["smoke_chunk_found"] is True
    assert payload["retrieval_event_found"] is True
    assert payload["rows_read"] == 2


def test_missing_owner_or_smoke_identifier_is_safe_not_configured():
    missing_owner = smoke.verify_vector_evidence_pgvector_smoke_readback(
        enabled=True,
        smoke_identifier=smoke.SMOKE_IDENTIFIER,
        db_executor=lambda request: {"rows": []},
    )
    missing_identifier = smoke.verify_vector_evidence_pgvector_smoke_readback(
        enabled=True,
        owner_user_id="owner-1",
        db_executor=lambda request: {"rows": []},
    )

    assert missing_owner["status"] == "pgvector_smoke_readback_not_configured"
    assert missing_identifier["status"] == (
        "pgvector_smoke_readback_not_configured"
    )
    assert missing_owner["readback_attempted"] is False
    assert missing_identifier["readback_attempted"] is False
    _assert_safety(missing_owner)
    _assert_safety(missing_identifier)


def test_import_has_no_connection_or_readback_side_effect():
    reloaded = importlib.reload(smoke)
    source = (
        ROOT / "src/storage/vector_evidence/smoke.py"
    ).read_text(encoding="utf-8")

    assert reloaded.SMOKE_IDENTIFIER == "pgvector-local-smoke"
    assert "verify_vector_evidence_pgvector_smoke_readback()" not in source
    assert "if __name__ ==" not in source


def test_no_api_ui_pipeline_schema_or_dependency_change():
    protected_hashes = {
        "src/app/api.py": ("d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004"),
        "src/app/static/agentic_review.js": ("fdbd820a68a356d894ac0b904bd649d511dcf501129d32ed00d34ffc7f927fd0"),
        "src/pipeline/collector.py": ("1d35d00e54d1d858134b2e524955887bd7adbbce3a01e53d1782debc4584490a"),
        "requirements.txt": ("96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f"),
        "src/storage/vector_evidence/schema.sql": ("4b34a928393fcce6696a2f35d7ee62339b0483cc248daee3f0e57bdb50c11dff"),
    }
    for relative_path, expected_hash in protected_hashes.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )
