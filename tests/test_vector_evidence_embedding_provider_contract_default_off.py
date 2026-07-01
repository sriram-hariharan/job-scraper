# phase56b legacy guard marker: changes_only ae6dd71675b3004e28f37754c348f648970c154730fb8c1c28ec944f098f381e cc56b3bd7460451ac255f57f6232fed9b607c1a90eac61b108bcf05005908fff
# phase56a legacy guard marker: changes_only 1d8351d5217438a9af900c39f5733381dc22c80722821cf56e88f688d40709cf ae6dd71675b3004e28f37754c348f648970c154730fb8c1c28ec944f098f381e
# phase26c legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c
# phase26b legacy guard marker: changes_only 1d8351d5217438a9af900c39f5733381dc22c80722821cf56e88f688d40709cf
# phase23f legacy guard marker: changes_only 1d8351d5217438a9af900c39f5733381dc22c80722821cf56e88f688d40709cf 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
# phase23f legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
import hashlib
from copy import deepcopy
from pathlib import Path

from src.storage.vector_evidence import embedding_provider


ROOT = Path(__file__).resolve().parents[1]


def _assert_no_mutation_safety(payload, *, called, created):
    safety = payload["safety_metadata"]
    assert safety["read_only"] is True
    assert safety["advisory_only"] is True
    assert safety["embedding_provider_contract"] is True
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


def test_default_off_returns_skipped_and_makes_no_provider_call():
    calls = []

    def provider(_request):
        calls.append("called")
        return [0.1, 0.2]

    payload = embedding_provider.run_vector_evidence_embedding_provider(
        text="semantic evidence",
        embedding_model_id="fixture-model",
        expected_dimension=2,
        provider=provider,
    )

    assert payload["status"] == "embedding_provider_skipped_default_off"
    assert payload["embedding"] == []
    assert calls == []
    _assert_no_mutation_safety(payload, called=False, created=False)


def test_enabled_without_provider_returns_not_configured_safely():
    payload = embedding_provider.run_vector_evidence_embedding_provider(
        enabled=True,
        text="semantic evidence",
        embedding_model_id="fixture-model",
        expected_dimension=2,
    )

    assert payload["status"] == "embedding_provider_not_configured"
    assert payload["errors"] == ["injected_provider_required"]
    assert payload["embedding_provider_enabled"] is True
    assert payload["embedding_provider_configured"] is False
    _assert_no_mutation_safety(payload, called=False, created=False)


def test_enabled_fake_provider_returns_validated_embedding_without_input_mutation():
    calls = []

    def provider(request):
        calls.append(deepcopy(request))
        return {"embedding": [0.25, -0.5, 1]}

    payload = embedding_provider.run_vector_evidence_embedding_provider(
        enabled=True,
        text="  semantic   evidence  ",
        embedding_model_id=" fixture-model ",
        expected_dimension=3,
        request_id=" request-1 ",
        provider=provider,
    )

    assert calls == [
        {
            "request_id": "request-1",
            "text": "semantic evidence",
            "embedding_model_id": "fixture-model",
            "expected_dimension": 3,
        }
    ]
    assert payload["status"] == "embedding_provider_embedding_ready"
    assert payload["embedding"] == [0.25, -0.5, 1.0]
    assert payload["embedding_dimension"] == 3
    assert payload["validation"]["is_valid"] is True
    _assert_no_mutation_safety(payload, called=True, created=True)


def test_invalid_vector_shape_is_rejected_safely():
    payload = embedding_provider.run_vector_evidence_embedding_provider(
        enabled=True,
        text="semantic evidence",
        embedding_model_id="fixture-model",
        expected_dimension=3,
        provider=lambda _request: [0.1, 0.2],
    )

    assert payload["status"] == "embedding_provider_invalid_response"
    assert payload["errors"] == ["embedding_dimension_mismatch"]
    assert payload["embedding"] == []
    _assert_no_mutation_safety(payload, called=True, created=False)


def test_non_numeric_vector_values_are_rejected_safely():
    payload = embedding_provider.run_vector_evidence_embedding_provider(
        enabled=True,
        text="semantic evidence",
        embedding_model_id="fixture-model",
        expected_dimension=2,
        provider=lambda _request: [0.1, "invalid"],
    )

    assert payload["status"] == "embedding_provider_invalid_response"
    assert payload["errors"] == ["embedding_vector_values_must_be_numeric"]
    _assert_no_mutation_safety(payload, called=True, created=False)


def test_provider_exception_is_non_blocking_and_safely_reported():
    def provider(_request):
        raise RuntimeError("fixture provider failure")

    payload = embedding_provider.run_vector_evidence_embedding_provider(
        enabled=True,
        text="semantic evidence",
        embedding_model_id="fixture-model",
        expected_dimension=2,
        provider=provider,
    )

    assert payload["status"] == "embedding_provider_failed_non_blocking"
    assert payload["errors"] == ["RuntimeError"]
    assert payload["embedding"] == []
    _assert_no_mutation_safety(payload, called=True, created=False)


def test_zero_agent_counts_and_no_provider_sdk_or_runtime_wiring():
    payload = embedding_provider.run_vector_evidence_embedding_provider()
    assert payload["provider_backed_automated_agents"] == 0
    assert payload["live_provider_backed_automated_agents"] == 0
    assert payload["mutation_authorized_agents"] == 0
    assert payload["mutation_authorized_scoring_agents"] == 0
    assert payload["mutation_authorized_ranking_agents"] == 0
    assert payload["mutation_authorized_application_agents"] == 0

    source = (
        ROOT / "src/storage/vector_evidence/embedding_provider.py"
    ).read_text(encoding="utf-8")
    forbidden = [
        "import openai",
        "from openai",
        "langchain",
        "sentence_transformers",
        "sentence-transformers",
        "os.environ",
        "requests.",
        "httpx.",
        "src.app.api",
        "agentic_review.js",
        "src.pipeline",
        "execute_vector_evidence",
        "create_approval_request(",
        "execute_application(",
        "submit_application(",
    ]
    for marker in forbidden:
        assert marker not in source.lower()


def test_api_ui_pipeline_dependencies_and_protected_decision_modules_are_unchanged():
    expected = {
        "requirements.txt": "96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f",
        "src/app/api.py": "1d8351d5217438a9af900c39f5733381dc22c80722821cf56e88f688d40709cf",
        "src/app/static/agentic_review.js": "1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b",
        "src/pipeline/collector.py": "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405",
        "src/pipeline/application_scorer.py": "e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b",
        "src/pipeline/job_ranker.py": "5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54",
    }
    for relative_path, expected_hash in expected.items():
        assert hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )
