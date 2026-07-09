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


ROOT = Path(__file__).resolve().parents[1]
COMMAND_PATH = (
    ROOT / "src/storage/admin_tools/vector_evidence_pgvector_smoke.py"
)


def test_manual_smoke_command_exists_and_is_disabled_by_default():
    calls = []
    payload = command.run_pgvector_real_local_smoke_command(
        environ={},
        connector=lambda url: calls.append(url),
    )

    assert COMMAND_PATH.exists()
    assert calls == []
    assert payload["status"] == (
        "pgvector_real_local_smoke_skipped_default_off"
    )
    assert payload["connection_provider_status"] == (
        "pgvector_connection_provider_disabled"
    )
    assert payload["schema_setup_status"] == "not_executed"
    assert payload["chunk_insert_status"] == "not_executed"
    assert payload["retrieval_event_insert_status"] == "not_executed"


def test_enabled_command_with_missing_config_is_safe():
    calls = []
    payload = command.run_pgvector_real_local_smoke_command(
        environ={
            "APPLYLENS_VECTOR_EVIDENCE_PGVECTOR_ENABLED": "true",
        },
        connector=lambda url: calls.append(url),
    )

    assert calls == []
    assert payload["status"] == "pgvector_real_local_smoke_missing_config"
    assert payload["connection_provider_status"] == (
        "pgvector_connection_provider_missing_config"
    )
    assert payload["errors"] == ["database_url_required"]


def test_enabled_fake_connector_path_exercises_existing_smoke_helper():
    connector_calls = []
    executor_calls = []

    def fake_executor(request):
        executor_calls.append(deepcopy(request))
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
    )

    assert connector_calls == ["postgres://vector-fixture"]
    assert len(executor_calls) == 3
    assert payload["status"] == "pgvector_local_smoke_completed"
    assert payload["connection_provider_status"] == (
        "pgvector_connection_provider_ready"
    )
    assert payload["schema_setup_status"] == "executed"
    assert payload["chunk_insert_status"] == "executed"
    assert payload["retrieval_event_insert_status"] == "executed"
    safety = payload["safety_metadata"]
    assert safety["embeddings_created"] is False
    assert safety["provider_calls_made"] is False
    assert safety["did_mutate_scoring"] is False
    assert safety["did_change_ranking"] is False
    assert safety["did_mutate_queue"] is False
    assert safety["did_create_approval"] is False
    assert safety["did_mutate_resume"] is False
    assert safety["did_create_execution_request"] is False
    assert safety["did_execute_application"] is False
    assert safety["did_submit_application"] is False


def test_import_opens_no_connection_and_runs_no_smoke():
    reloaded = importlib.reload(command)
    source = COMMAND_PATH.read_text(encoding="utf-8")

    assert reloaded.OWNER_USER_ID_ENV == (
        "APPLYLENS_VECTOR_EVIDENCE_OWNER_USER_ID"
    )
    assert source.count("run_pgvector_real_local_smoke_command(") == 2
    assert "if __name__ == \"__main__\":" in source


def test_no_api_ui_pipeline_schema_or_dependency_change():
    protected_hashes = {
        "src/app/api.py": ("d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004"),
        "src/app/static/agentic_review.js": ("fdbd820a68a356d894ac0b904bd649d511dcf501129d32ed00d34ffc7f927fd0"),
        "src/pipeline/collector.py": ("1d35d00e54d1d858134b2e524955887bd7adbbce3a01e53d1782debc4584490a"),
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

    source = COMMAND_PATH.read_text(encoding="utf-8")
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
    ):
        assert marker not in source
