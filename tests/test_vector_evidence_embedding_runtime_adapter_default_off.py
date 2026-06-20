import hashlib
from copy import deepcopy
from pathlib import Path

from src.storage.vector_evidence import embedding_runtime_adapter


ROOT = Path(__file__).resolve().parents[1]


def _assert_safety(payload, *, enabled, configured, called, created):
    safety = payload["safety_metadata"]
    assert safety["read_only"] is True
    assert safety["advisory_only"] is True
    assert safety["runtime_adapter_enabled"] is enabled
    assert safety["provider_configured"] is configured
    assert safety["provider_calls_made"] is called
    assert safety["embeddings_created"] is created
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


def _request_kwargs():
    return {
        "text": "semantic evidence",
        "embedding_model_id": "fixture-model",
        "expected_dimension": 3,
        "request_id": "request-phase-9f",
    }


def test_default_off_skips_without_calling_injected_provider():
    calls = []

    payload = (
        embedding_runtime_adapter.run_vector_evidence_embedding_runtime_adapter(
            **_request_kwargs(),
            provider_callable=lambda request: calls.append(request),
        )
    )

    assert payload["status"] == (
        "embedding_runtime_adapter_skipped_default_off"
    )
    assert calls == []
    _assert_safety(
        payload,
        enabled=False,
        configured=True,
        called=False,
        created=False,
    )


def test_enabled_without_provider_returns_not_configured_safely():
    payload = (
        embedding_runtime_adapter.run_vector_evidence_embedding_runtime_adapter(
            enabled=True,
            **_request_kwargs(),
        )
    )

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


def test_injected_callable_returns_phase_9a_validated_embedding():
    calls = []

    def provider(request):
        calls.append(deepcopy(request))
        return {"embedding": [0.25, -0.5, 1]}

    payload = (
        embedding_runtime_adapter.run_vector_evidence_embedding_runtime_adapter(
            enabled=True,
            provider_callable=provider,
            **_request_kwargs(),
        )
    )

    assert len(calls) == 1
    assert payload["status"] == "embedding_runtime_adapter_embedding_ready"
    assert payload["provider_mechanism"] == "injected_provider_callable"
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


def test_existing_encode_client_shape_is_supported_only_when_injected():
    class FakeVector:
        def tolist(self):
            return [0.1, 0.2, 0.3]

    class FakeClient:
        def __init__(self):
            self.calls = []

        def encode(self, text, *, normalize_embeddings):
            self.calls.append((text, normalize_embeddings))
            return FakeVector()

    client = FakeClient()
    payload = (
        embedding_runtime_adapter.run_vector_evidence_embedding_runtime_adapter(
            enabled=True,
            provider_client=client,
            **_request_kwargs(),
        )
    )

    assert client.calls == [("semantic evidence", True)]
    assert payload["provider_mechanism"] == "injected_encode_client"
    assert payload["embedding"] == [0.1, 0.2, 0.3]
    _assert_safety(
        payload,
        enabled=True,
        configured=True,
        called=True,
        created=True,
    )


def test_invalid_provider_response_is_rejected_safely():
    payload = (
        embedding_runtime_adapter.run_vector_evidence_embedding_runtime_adapter(
            enabled=True,
            provider_callable=lambda _request: [0.1, "invalid", 0.3],
            **_request_kwargs(),
        )
    )

    assert payload["status"] == "embedding_runtime_adapter_invalid_response"
    assert payload["errors"] == [
        "embedding_vector_values_must_be_numeric"
    ]
    _assert_safety(
        payload,
        enabled=True,
        configured=True,
        called=True,
        created=False,
    )


def test_provider_exception_is_non_blocking():
    def provider(_request):
        raise RuntimeError("fixture provider failure")

    payload = (
        embedding_runtime_adapter.run_vector_evidence_embedding_runtime_adapter(
            enabled=True,
            provider_callable=provider,
            **_request_kwargs(),
        )
    )

    assert payload["status"] == "embedding_runtime_adapter_failed_non_blocking"
    assert payload["errors"] == ["RuntimeError"]
    _assert_safety(
        payload,
        enabled=True,
        configured=True,
        called=True,
        created=False,
    )


def test_zero_agent_counts_and_no_runtime_or_mutation_wiring():
    payload = (
        embedding_runtime_adapter.run_vector_evidence_embedding_runtime_adapter()
    )
    assert payload["provider_backed_automated_agents"] == 0
    assert payload["live_provider_backed_automated_agents"] == 0
    assert payload["mutation_authorized_agents"] == 0
    assert payload["mutation_authorized_scoring_agents"] == 0
    assert payload["mutation_authorized_ranking_agents"] == 0
    assert payload["mutation_authorized_application_agents"] == 0

    source = (
        ROOT / "src/storage/vector_evidence/embedding_runtime_adapter.py"
    ).read_text(encoding="utf-8").lower()
    for marker in (
        "from openai",
        "import openai",
        "langchain",
        "sentence_transformers",
        "from src.ai.embedding_model",
        "get_model(",
        "os.getenv",
        "os.environ",
        "src.app.api",
        "agentic_review.js",
        "src.pipeline",
        "score_jobs(",
        "rank_jobs(",
        "create_approval_request(",
        "mutate_resume(",
        "create_execution_request(",
        "execute_application(",
        "submit_application(",
    ):
        assert marker not in source


def test_api_ui_pipeline_dependencies_and_decision_modules_are_unchanged():
    expected = {
        "requirements.txt": "96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f",
        "src/app/api.py": "b520bcf22ad0ec85f6ee27ebb9f74c513fa3b76f377f0652cf74474dd67c905f",
        "src/app/static/agentic_review.js": "83a95006d999df32387d3a0732ac96f8ebdc7f49a2115ba23597c03f02f82e1c",
        "src/pipeline/collector.py": "cbcd90f3d8d367ebe6f178c211406da909f340ce62681047b70efe4fb4a30fa7",
        "src/pipeline/application_scorer.py": "e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b",
        "src/pipeline/job_ranker.py": "5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54",
    }
    for relative_path, expected_hash in expected.items():
        assert hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )
