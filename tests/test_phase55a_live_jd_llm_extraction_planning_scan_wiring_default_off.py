from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services


ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = (
    ROOT
    / "docs/phase55_live_jd_llm_extraction_planning_scan_wiring_default_off.md"
)
PROTECTED_HASHES = {
    "src/matching/scorer.py": "c3f0b1f4a938ca933b10991af1ddb0aca2790136c7c6b487a8ee79556ee5ceac",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "src/tailoring/llm.py": "d47c5d84758ca185a2fd4d8e2062018b48498592a4b79e88182036c2c4edbc28",
    "generate_tailoring_" + "suggestions" + ".py": "a5e3dda138232fadc6d69bd9f2468459ce2759d961687bf1fa9ee9970c5490c2",
    "application_execution_" + "queue" + ".py": "c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0",
    "src/agents/jd_intelligence_llm_signal_extractor_default_off.py": (
        "a73124801ce6768aebb934e1c6a7e76d4f9888bbb7b0ca28eb93e882e06f4f6c"
    ),
    "src/agents/jd_intelligence_planning_artifact_enricher_default_off.py": (
        "f8e365ab51de647dc6b45ff0c99cce075273eec61e12fc96c744118e1ca68c53"
    ),
}


def _request_payload() -> dict:
    return {
        "scan_id": "phase55a-scan",
        "company": "ExampleCo",
        "role": "Senior Analytics Engineer",
        "job_description_text": (
            "Own Python data pipelines, SQL models, dbt workflows, and reporting."
        ),
        "job_url": "https://example.test/job",
        "job_doc_id": "job-phase55a",
        "resume_text": "Built Python data pipelines and SQL reporting for analytics teams.",
    }


def _valid_provider_payload() -> dict:
    return {
        "required_skills": ["Python", "SQL"],
        "preferred_skills": ["analytics engineering"],
        "required_tools": ["dbt"],
        "preferred_tools": ["Airflow"],
        "workflows": ["data pipelines"],
        "methods": ["stakeholder reporting"],
        "business_contexts": ["analytics platform"],
        "stakeholder_contexts": ["finance partners"],
        "ownership_signals": ["owns pipeline quality"],
        "seniority_signals": ["senior scope"],
        "risk_flags": [],
        "extraction_confidence": 0.91,
        "model_provider": "fake-provider",
        "model_name": "fake-model",
        "prompt_version": "fake-prompt-v1",
        "token_usage": {"total_token_count": 42},
        "cost": {"estimated_cost": 0.01, "cost_currency": "USD"},
        "latency_ms": 12,
    }


def _build_scan(monkeypatch, **overrides):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    return services.create_saved_scan_payload(**{**_request_payload(), **overrides})


def _metadata(payload: dict) -> dict:
    return payload["scan_review_payload"]["jd_llm_extraction"]


def test_default_off_planning_scan_path_does_not_call_live_llm(monkeypatch):
    calls = []
    source = _request_payload()
    original = deepcopy(source)

    payload = _build_scan(
        monkeypatch,
        jd_llm_provider_adapter=lambda request: calls.append(request)
        or _valid_provider_payload(),
    )

    assert source == original
    assert calls == []
    metadata = _metadata(payload)
    assert metadata["llm_enabled"] is False
    assert metadata["llm_call_attempted"] is False
    assert metadata["llm_call_performed"] is False
    assert metadata["fallback_used"] is True
    assert metadata["validation_status"] == "disabled"
    assert payload["scan_review_payload"]["scan_score"]["source"] == (
        "new_scan_match_score"
    )


def test_enabled_planning_scan_path_calls_existing_jd_extractor_path(monkeypatch):
    calls = []

    def fake_provider(request):
        calls.append(request)
        return _valid_provider_payload()

    payload = _build_scan(
        monkeypatch,
        enable_jd_llm_extraction=True,
        jd_llm_provider_adapter=fake_provider,
    )

    metadata = _metadata(payload)
    assert calls
    assert calls[0]["job_title"] == "Senior Analytics Engineer"
    assert metadata["llm_enabled"] is True
    assert metadata["llm_call_attempted"] is True
    assert metadata["llm_call_performed"] is True
    assert metadata["validation_status"] == "valid"
    assert metadata["provider"] == "fake-provider"
    assert metadata["model"] == "fake-model"
    assert metadata["prompt_version"] == "fake-prompt-v1"
    assert metadata["token_usage"] == {"total_token_count": 42}
    assert metadata["cost"] == {"estimated_cost": 0.01, "cost_currency": "USD"}
    assert metadata["latency_ms"] == 12
    assert metadata["enricher_result"]["enricher_findings"][
        "phase34a_extractor_used"
    ] is True


def test_enabled_valid_provider_response_adds_structured_jd_signals(monkeypatch):
    payload = _build_scan(
        monkeypatch,
        enable_jd_llm_extraction=True,
        jd_llm_provider_adapter=lambda _request: _valid_provider_payload(),
    )

    signals = _metadata(payload)["structured_jd_signals"]
    assert signals["required_skills"] == ["Python", "SQL"]
    assert "dbt" in signals["tools"]
    assert "Airflow" in signals["tools"]
    assert "data pipelines" in signals["responsibilities"]
    assert signals["seniority"] == "senior scope"
    assert signals["confidence"] == 0.91
    assert payload["scan"]["payload_json"]["jd_llm_extraction"]["structured_jd_signals"] == signals


def test_provider_invalid_json_falls_back_safely(monkeypatch):
    payload = _build_scan(
        monkeypatch,
        enable_jd_llm_extraction=True,
        jd_llm_provider_adapter=lambda _request: {"raw_response": "{bad json"},
    )

    metadata = _metadata(payload)
    assert metadata["llm_enabled"] is True
    assert metadata["llm_call_attempted"] is True
    assert metadata["llm_call_performed"] is False
    assert metadata["fallback_used"] is True
    assert metadata["validation_status"] == "fallback"
    assert metadata["structured_jd_signals"] == {}
    assert "provider_callable_error:ValueError" in metadata["validation_errors"]


def test_provider_exception_falls_back_safely(monkeypatch):
    def failing_provider(_request):
        raise RuntimeError("provider unavailable")

    payload = _build_scan(
        monkeypatch,
        enable_jd_llm_extraction=True,
        jd_llm_provider_adapter=failing_provider,
    )

    metadata = _metadata(payload)
    assert metadata["llm_call_attempted"] is True
    assert metadata["llm_call_performed"] is False
    assert metadata["fallback_used"] is True
    assert metadata["validation_status"] == "fallback"
    assert metadata["structured_jd_signals"] == {}
    assert "provider_callable_error:RuntimeError" in metadata["validation_errors"]


def test_existing_deterministic_scan_output_and_score_remain_present(monkeypatch):
    disabled = _build_scan(monkeypatch)
    enabled = _build_scan(
        monkeypatch,
        enable_jd_llm_extraction=True,
        jd_llm_provider_adapter=lambda _request: _valid_provider_payload(),
    )

    for payload in (disabled, enabled):
        review = payload["scan_review_payload"]
        assert review["ok"] is True
        assert review["scan_score"]["source"] == "new_scan_match_score"
        assert isinstance(review["scan_issue_contract"], dict)
        assert isinstance(review["score_preview"], dict)
    assert enabled["scan_review_payload"]["scan_score"] == disabled[
        "scan_review_payload"
    ]["scan_score"]


def test_no_scoring_formula_weight_or_mutation_side_effects(monkeypatch):
    payload = _build_scan(
        monkeypatch,
        enable_jd_llm_extraction=True,
        jd_llm_provider_adapter=lambda _request: _valid_provider_payload(),
    )

    metadata = _metadata(payload)
    for key in (
        "final_scoring_performed",
        "score_formula_changed",
        "scoring_weights_changed",
        "resume_mutation_performed",
        "resume_artifact_created",
        "queue_mutation_performed",
        "approval_mutation_performed",
        "application_execution_performed",
        "application_submission_performed",
        "auto_" + "apply_performed",
    ):
        assert metadata[key] is False


def test_api_route_remains_default_off_unless_explicit_enable(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    monkeypatch.setattr(api, "_auth_owner_user_id", lambda request: "test-owner")
    monkeypatch.setattr(api, "_auth_owner_email", lambda request: "owner@example.test")
    calls = []
    monkeypatch.setattr(
        services,
        "_live_jd_intelligence_provider_adapter",
        lambda request: calls.append(request) or _valid_provider_payload(),
    )
    client = TestClient(api.app)

    default_response = client.post("/planning/start-scan", json=_request_payload())
    enabled_response = client.post(
        "/planning/start-scan",
        json={**_request_payload(), "scan_id": "phase55a-api-enabled", "enable_jd_llm_extraction": True},
    )

    assert default_response.status_code == 200
    assert default_response.json()["scan_review_payload"]["jd_llm_extraction"][
        "validation_status"
    ] == "disabled"
    assert enabled_response.status_code == 200
    assert calls
    assert enabled_response.json()["scan_review_payload"]["jd_llm_extraction"][
        "validation_status"
    ] == "valid"


def test_docs_capture_live_jd_llm_scan_wiring_and_safety():
    text = DOC_PATH.read_text(encoding="utf-8").lower()
    for marker in (
        "default-off",
        "live jd llm extraction",
        "planning/start-scan",
        "deterministic fallback",
        "does not mutate resumes",
        "does not create resume artifacts",
        "does not execute applications",
        "auto-apply",
    ):
        assert marker in text


def test_protected_runtime_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == expected_hash
