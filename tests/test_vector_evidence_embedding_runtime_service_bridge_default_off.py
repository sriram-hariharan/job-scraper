# phase79b legacy guard marker: changes_only collector_hash_old 73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405
# phase56b legacy guard marker: changes_only bfa035faa8e89abd2b75095f68b45a282fb3b7fc8e5ff43e36c754db56ef12c2 1ff2a73993300f391aa1fb8151a4d225e803b6c5d499e311faa5058efc4b965c
# phase56a legacy guard marker: changes_only d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004 bfa035faa8e89abd2b75095f68b45a282fb3b7fc8e5ff43e36c754db56ef12c2
# phase26c legacy guard marker: changes_only fdbd820a68a356d894ac0b904bd649d511dcf501129d32ed00d34ffc7f927fd0 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c
# phase26b legacy guard marker: changes_only d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004
# phase23f legacy guard marker: changes_only d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c fdbd820a68a356d894ac0b904bd649d511dcf501129d32ed00d34ffc7f927fd0
# phase23f legacy guard marker: changes_only fdbd820a68a356d894ac0b904bd649d511dcf501129d32ed00d34ffc7f927fd0
import hashlib
from copy import deepcopy
from pathlib import Path

from src.app import services
from tests.support.phase_guard_registry import assert_protected_hashes


ROOT = Path(__file__).resolve().parents[1]
HELPER = "vector_evidence_embedding_runtime_service_helper_payload"


def _call(**updates):
    kwargs = {
        "text": "semantic query evidence",
        "embedding_model_id": "fixture-model",
        "expected_dimension": 3,
        "request_id": "request-phase-9g",
    }
    kwargs.update(updates)
    return getattr(services, HELPER)(**kwargs)


def _assert_safety(payload, *, enabled, configured, called, created):
    safety = payload["safety_metadata"]
    assert payload["service_surface"] == (
        "vector_evidence_embedding_runtime_service_helper"
    )
    assert payload["service_helper_only"] is True
    assert payload["operator_triggered_only"] is True
    assert payload["api_route_added"] is False
    assert payload["ui_action_added"] is False
    assert safety["read_only"] is True
    assert safety["advisory_only"] is True
    assert safety["embedding_runtime_service_bridge"] is True
    assert safety["runtime_adapter_enabled"] is enabled
    assert safety["provider_configured"] is configured
    assert safety["provider_calls_made"] is called
    assert safety["embeddings_created"] is created
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
    assert safety["pipeline_stage_added"] is False
    assert safety["auto_apply_enabled"] is False
    assert safety["mutation_authorized"] is False
    assert payload["provider_backed_automated_agents"] == 0
    assert payload["live_provider_backed_automated_agents"] == 0
    assert payload["mutation_authorized_agents"] == 0
    assert payload["mutation_authorized_scoring_agents"] == 0
    assert payload["mutation_authorized_ranking_agents"] == 0
    assert payload["mutation_authorized_application_agents"] == 0


def test_default_off_service_helper_skips_without_provider_call():
    calls = []

    payload = _call(
        provider_callable=lambda request: calls.append(deepcopy(request))
    )

    assert calls == []
    assert payload["status"] == (
        "embedding_runtime_adapter_skipped_default_off"
    )
    assert payload["default_off"] is True
    assert payload["embedding"] == []
    _assert_safety(
        payload,
        enabled=False,
        configured=True,
        called=False,
        created=False,
    )


def test_enabled_without_provider_returns_not_configured_safely():
    payload = _call(enabled=True)

    assert payload["status"] == "embedding_runtime_adapter_not_configured"
    assert payload["errors"] == [
        "injected_provider_callable_or_client_required"
    ]
    _assert_safety(
        payload,
        enabled=True,
        configured=False,
        called=False,
        created=False,
    )


def test_enabled_fake_provider_returns_validated_embedding():
    calls = []

    def provider(request):
        calls.append(deepcopy(request))
        return {"embedding": [0.25, -0.5, 1]}

    payload = _call(enabled=True, provider_callable=provider)

    assert len(calls) == 1
    assert payload["status"] == "embedding_runtime_adapter_embedding_ready"
    assert payload["embedding"] == [0.25, -0.5, 1.0]
    assert payload["embedding_dimension"] == 3
    assert payload["provider_contract_payload"]["validation"]["is_valid"] is True
    _assert_safety(
        payload,
        enabled=True,
        configured=True,
        called=True,
        created=True,
    )


def test_provider_exception_is_non_blocking():
    def provider(_request):
        raise RuntimeError("fixture provider failure")

    payload = _call(enabled=True, provider_callable=provider)

    assert payload["status"] == (
        "embedding_runtime_adapter_failed_non_blocking"
    )
    assert payload["errors"] == ["RuntimeError"]
    assert payload["embedding"] == []
    _assert_safety(
        payload,
        enabled=True,
        configured=True,
        called=True,
        created=False,
    )


def test_service_bridge_has_no_database_provider_sdk_or_mutation_wiring():
    source = (ROOT / "src/app/services.py").read_text(encoding="utf-8")
    start = source.index(
        "def vector_evidence_embedding_runtime_service_helper_payload("
    )
    end = source.index(
        "\n\ndef pgvector_extension_probe_service_helper_payload(",
        start,
    )
    snippet = source[start:end].lower()

    assert "run_vector_evidence_embedding_runtime_adapter" in snippet
    for marker in (
        "from openai",
        "import openai",
        "langchain",
        "sentence_transformers",
        "get_model(",
        "os.getenv",
        "database_url",
        "connect(",
        ".commit(",
        "src.pipeline",
        "score_resume_job_match(",
        "rank_jobs(",
        "create_approval_request(",
        "record_approval_decision(",
        "mutate_resume(",
        "create_execution_request(",
        "create_execution_launch_request(",
        "execute_application(",
        "submit_application(",
    ):
        assert marker not in snippet


def test_api_ui_pipeline_dependencies_and_decision_modules_are_unchanged():
    expected = {
        "requirements.txt": "5dc563901e19c10a0f59fe811ec6961ee47f837827a7448e3a669aed9f244cc6",
        "src/app/api.py": "d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004",
        "src/app/static/agentic_review.js": "fdbd820a68a356d894ac0b904bd649d511dcf501129d32ed00d34ffc7f927fd0",
        "src/pipeline/collector.py": "e5af36527801b2a1a55501622619d4e62ccaa7472e835500613e2894843d1671",
        "src/pipeline/application_scorer.py": "e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b",
        "src/pipeline/job_ranker.py": "5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54",
    }
    assert_protected_hashes(
        ROOT,
        expected,
        compatibility_profiles=(
            "phase129c_workflow_overlay_and_run_scoped_corpus",
        ),
    )
