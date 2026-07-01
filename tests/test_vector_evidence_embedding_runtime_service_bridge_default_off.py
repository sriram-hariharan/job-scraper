# phase56b legacy guard marker: changes_only 912a02bbcf180962ca1b22aedf9dca0b5465b90f4add2444f328c99ccfc6e2d6 8e37487335a2b0bf18fd196554c11509d0e5ee0428244ce9fafce3c3e195e5bd
# phase56a legacy guard marker: changes_only f9137ef3f8d1cc27fe08f3a592f1cff977a124cb6132a91394ee8350674bea6f 912a02bbcf180962ca1b22aedf9dca0b5465b90f4add2444f328c99ccfc6e2d6
# phase26c legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c
# phase26b legacy guard marker: changes_only f9137ef3f8d1cc27fe08f3a592f1cff977a124cb6132a91394ee8350674bea6f
# phase23f legacy guard marker: changes_only f9137ef3f8d1cc27fe08f3a592f1cff977a124cb6132a91394ee8350674bea6f 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
# phase23f legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
import hashlib
from copy import deepcopy
from pathlib import Path

from src.app import services


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
        "requirements.txt": "96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f",
        "src/app/api.py": "f9137ef3f8d1cc27fe08f3a592f1cff977a124cb6132a91394ee8350674bea6f",
        "src/app/static/agentic_review.js": "1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b",
        "src/pipeline/collector.py": "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405",
        "src/pipeline/application_scorer.py": "e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b",
        "src/pipeline/job_ranker.py": "5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54",
    }
    for relative_path, expected_hash in expected.items():
        assert hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )
