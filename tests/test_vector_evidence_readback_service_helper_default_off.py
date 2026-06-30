# phase56b legacy guard marker: changes_only 38c3c389c970d009ec040b6542c81c150d55f9f7f9957d2c0ba2760a3440fe35 9fde4169a5a94ae3ab09c4b19d70257019f997f69e71fe11262ae740937f0728
# phase56a legacy guard marker: changes_only d82ec915f4f41c0c57dabd372defcfd377078e3db4be54f00105a26b0a1d6ee7 38c3c389c970d009ec040b6542c81c150d55f9f7f9957d2c0ba2760a3440fe35
# phase26c legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c
# phase26b legacy guard marker: changes_only d82ec915f4f41c0c57dabd372defcfd377078e3db4be54f00105a26b0a1d6ee7
# phase23f legacy guard marker: changes_only d82ec915f4f41c0c57dabd372defcfd377078e3db4be54f00105a26b0a1d6ee7 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
# phase23f legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from src.app import services


ROOT = Path(__file__).resolve().parents[1]
HELPER = "vector_evidence_readback_service_helper_payload"


def _call(**updates) -> dict:
    return getattr(services, HELPER)(**updates)


def _assert_safety(payload: dict, *, read: bool = False) -> None:
    safety = payload["safety_metadata"]
    assert payload["service_surface"] == (
        "vector_evidence_readback_service_helper"
    )
    assert payload["service_helper_only"] is True
    assert payload["operator_triggered_only"] is True
    assert payload["api_route_added"] is False
    assert payload["ui_action_added"] is False
    assert safety["read_only"] is True
    assert safety["advisory_only"] is True
    assert safety["vector_evidence_readback_service_helper"] is True
    assert safety["operator_triggered_only"] is True
    assert safety["did_read_database"] is read
    assert safety["did_write_database"] is False
    assert safety["embeddings_created"] is False
    assert safety["provider_calls_made"] is False
    assert safety["pipeline_stage_added"] is False
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
    assert safety["auto_apply_enabled"] is False
    assert safety["mutation_authorized"] is False
    assert payload["provider_backed_automated_agents"] == 0
    assert payload["live_provider_backed_automated_agents"] == 0
    assert payload["mutation_authorized_agents"] == 0
    assert payload["mutation_authorized_scoring_agents"] == 0
    assert payload["mutation_authorized_ranking_agents"] == 0
    assert payload["mutation_authorized_application_agents"] == 0


def test_default_service_helper_is_skipped_default_off():
    calls = []
    payload = _call(db_executor=lambda request: calls.append(request))

    assert calls == []
    assert payload["status"] == (
        "pgvector_smoke_readback_skipped_default_off"
    )
    assert payload["default_off"] is True
    assert payload["readback_attempted"] is False
    assert payload["readback_executed"] is False
    assert payload["rows_read"] == 0
    _assert_safety(payload)


def test_enabled_fake_executor_reports_chunk_and_event_found():
    calls = []

    def fake_executor(request):
        calls.append(deepcopy(request))
        return {
            "rows": [
                {"record_type": "chunk", "record_id": "smoke-chunk"},
                {
                    "record_type": "retrieval_event",
                    "record_id": "smoke-event",
                },
            ]
        }

    payload = _call(
        enabled=True,
        owner_user_id="owner-1",
        smoke_identifier="pgvector-local-smoke",
        db_executor=fake_executor,
    )

    assert len(calls) == 1
    assert payload["status"] == "pgvector_smoke_readback_verified"
    assert payload["readback_attempted"] is True
    assert payload["readback_executed"] is True
    assert payload["smoke_chunk_found"] is True
    assert payload["retrieval_event_found"] is True
    assert payload["rows_read"] == 2
    assert payload["db_executor_supplied"] is True
    _assert_safety(payload, read=True)


def test_enabled_fake_executor_can_report_each_record_independently():
    chunk = _call(
        enabled=True,
        owner_user_id="owner-1",
        smoke_identifier="pgvector-local-smoke",
        db_executor=lambda request: {
            "rows": [{"record_type": "chunk", "record_id": "smoke-chunk"}]
        },
    )
    event = _call(
        enabled=True,
        owner_user_id="owner-1",
        smoke_identifier="pgvector-local-smoke",
        db_executor=lambda request: {
            "rows": [
                {
                    "record_type": "retrieval_event",
                    "record_id": "smoke-event",
                }
            ]
        },
    )

    assert chunk["smoke_chunk_found"] is True
    assert chunk["retrieval_event_found"] is False
    assert event["smoke_chunk_found"] is False
    assert event["retrieval_event_found"] is True
    _assert_safety(chunk, read=True)
    _assert_safety(event, read=True)


def test_enabled_fake_connector_builds_executor_through_provider():
    connector_calls = []
    executor_calls = []

    def fake_executor(request):
        executor_calls.append(deepcopy(request))
        return {
            "rows": [
                {"record_type": "chunk", "record_id": "smoke-chunk"},
                {
                    "record_type": "retrieval_event",
                    "record_id": "smoke-event",
                },
            ]
        }

    def fake_connector(database_url):
        connector_calls.append(database_url)
        return fake_executor

    payload = _call(
        enabled=True,
        owner_user_id="owner-1",
        smoke_identifier="pgvector-local-smoke",
        connection_provider_enabled=True,
        connection_database_url="postgres://vector-fixture",
        connection_connector=fake_connector,
    )

    assert connector_calls == ["postgres://vector-fixture"]
    assert len(executor_calls) == 1
    assert payload["pgvector_connection_provider_requested"] is True
    assert payload["pgvector_connection_provider_used"] is True
    assert payload["pgvector_connection_provider_status"] == (
        "pgvector_connection_provider_ready"
    )
    assert payload["db_executor_created"] is True
    assert payload["db_connection_opened"] is True
    assert payload["smoke_chunk_found"] is True
    assert payload["retrieval_event_found"] is True
    _assert_safety(payload, read=True)


def test_missing_owner_or_identifier_is_safe_not_configured():
    calls = []
    missing_owner = _call(
        enabled=True,
        smoke_identifier="pgvector-local-smoke",
        db_executor=lambda request: calls.append(request),
    )
    missing_identifier = _call(
        enabled=True,
        owner_user_id="owner-1",
        db_executor=lambda request: calls.append(request),
    )

    assert calls == []
    assert missing_owner["status"] == "pgvector_smoke_readback_not_configured"
    assert missing_identifier["status"] == (
        "pgvector_smoke_readback_not_configured"
    )
    assert missing_owner["readback_attempted"] is False
    assert missing_identifier["readback_attempted"] is False
    _assert_safety(missing_owner)
    _assert_safety(missing_identifier)


def test_service_import_path_has_no_automatic_connection():
    source = (ROOT / "src/app/services.py").read_text(encoding="utf-8")
    start = source.index(
        "def vector_evidence_readback_service_helper_payload("
    )
    end = source.index(
        "\n\ndef pgvector_extension_probe_service_helper_payload(",
        start,
    )
    snippet = source[start:end]

    assert "verify_vector_evidence_pgvector_smoke_readback" in snippet
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


def test_no_api_ui_pipeline_schema_or_dependency_change():
    protected_hashes = {
        "src/app/api.py": ("d82ec915f4f41c0c57dabd372defcfd377078e3db4be54f00105a26b0a1d6ee7"),
        "src/app/static/agentic_review.js": ("1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b"),
        "src/pipeline/collector.py": ("73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405"),
        "requirements.txt": ("96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f"),
        "src/storage/vector_evidence/schema.sql": ("4b34a928393fcce6696a2f35d7ee62339b0483cc248daee3f0e57bdb50c11dff"),
    }
    for relative_path, expected_hash in protected_hashes.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )
