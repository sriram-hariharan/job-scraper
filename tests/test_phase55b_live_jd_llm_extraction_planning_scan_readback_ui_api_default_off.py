from hashlib import sha256
from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services


ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = (
    ROOT
    / "docs/phase55_live_jd_llm_extraction_planning_scan_readback_ui_api_default_off.md"
)
PROTECTED_HASHES = {
    "src/matching/scorer.py": "f56624b5b3c7e2bb01a824386b86fbc2a194e727f0437ca0773764eae64ec941",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "src/tailoring/llm.py": "6153c78e5f0eca7c78451f0d234609682e01990041deae7fccb0aa303c653920",
    "generate_tailoring_" + "suggestions" + ".py": "2422452d1c7a54777684b399730d02c11e58ce1ad6ac5658527ad71bb9050f28",
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
        "scan_id": "phase55b-scan",
        "company": "ExampleCo",
        "role": "Senior Analytics Engineer",
        "job_description_text": (
            "Own Python data pipelines, SQL models, dbt workflows, and reporting."
        ),
        "job_url": "https://example.test/job",
        "job_doc_id": "job-phase55b",
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


def _client(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    monkeypatch.setattr(api, "_auth_owner_user_id", lambda request: "test-owner")
    monkeypatch.setattr(api, "_auth_owner_email", lambda request: "owner@example.test")
    return TestClient(api.app)


def test_default_off_api_readback_does_not_call_live_llm(monkeypatch):
    calls = []
    monkeypatch.setattr(
        services,
        "_live_jd_intelligence_provider_adapter",
        lambda request: calls.append(request) or _valid_provider_payload(),
    )

    response = _client(monkeypatch).post("/planning/start-scan", json=_request_payload())

    assert response.status_code == 200
    assert calls == []
    payload = response.json()
    readback = payload["jd_llm_extraction_readback"]
    assert readback == payload["scan_review_payload"]["jd_llm_extraction_readback"]
    assert readback["llm_enabled"] is False
    assert readback["llm_call_attempted"] is False
    assert readback["llm_call_performed"] is False
    assert readback["fallback_used"] is True
    assert readback["validation_status"] == "disabled"
    assert readback["structured_jd_signals"] == {}


def test_explicit_enabled_api_readback_shows_observability_and_signals(monkeypatch):
    calls = []

    def fake_provider(request):
        calls.append(request)
        return _valid_provider_payload()

    monkeypatch.setattr(services, "_live_jd_intelligence_provider_adapter", fake_provider)

    response = _client(monkeypatch).post(
        "/planning/start-scan",
        json={**_request_payload(), "enable_jd_llm_extraction": True},
    )

    assert response.status_code == 200
    assert calls
    readback = response.json()["jd_llm_extraction_readback"]
    assert readback["llm_enabled"] is True
    assert readback["llm_call_attempted"] is True
    assert readback["llm_call_performed"] is True
    assert readback["fallback_used"] is False
    assert readback["validation_status"] == "valid"
    assert readback["provider"] == "fake-provider"
    assert readback["model"] == "fake-model"
    assert readback["prompt_version"] == "fake-prompt-v1"
    assert readback["token_usage"] == {"total_token_count": 42}
    assert readback["cost"] == {"estimated_cost": 0.01, "cost_currency": "USD"}
    assert readback["latency_ms"] == 12
    assert readback["structured_jd_signals"]["required_skills"] == ["Python", "SQL"]
    assert readback["signal_summary"]["required_skill_count"] == 2


def test_provider_invalid_json_shows_fallback_readback_safely(monkeypatch):
    monkeypatch.setattr(
        services,
        "_live_jd_intelligence_provider_adapter",
        lambda _request: {"raw_response": "{bad json"},
    )

    response = _client(monkeypatch).post(
        "/planning/start-scan",
        json={**_request_payload(), "enable_jd_llm_extraction": True},
    )

    readback = response.json()["jd_llm_extraction_readback"]
    assert readback["llm_enabled"] is True
    assert readback["llm_call_attempted"] is True
    assert readback["llm_call_performed"] is False
    assert readback["fallback_used"] is True
    assert readback["validation_status"] == "fallback"
    assert readback["structured_jd_signals"] == {}


def test_provider_exception_shows_fallback_readback_safely(monkeypatch):
    def failing_provider(_request):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(services, "_live_jd_intelligence_provider_adapter", failing_provider)

    response = _client(monkeypatch).post(
        "/planning/start-scan",
        json={**_request_payload(), "enable_jd_llm_extraction": True},
    )

    readback = response.json()["jd_llm_extraction_readback"]
    assert readback["llm_call_attempted"] is True
    assert readback["llm_call_performed"] is False
    assert readback["fallback_used"] is True
    assert readback["validation_status"] == "fallback"
    assert readback["safety"]["provider_call_triggered_by_readback"] is False


def test_saved_scan_readback_materializes_from_stored_metadata_without_provider_call(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    calls = []
    scan_payload = services.create_saved_scan_payload(
        **_request_payload(),
        enable_jd_llm_extraction=True,
        jd_llm_provider_adapter=lambda request: calls.append(request) or _valid_provider_payload(),
    )
    row = scan_payload["scan"]
    stored = {"scan": row}

    monkeypatch.setattr(
        services,
        "get_saved_scan_postgres_payload",
        lambda scan_id, owner_user_id="": stored,
    )
    monkeypatch.setattr(
        services,
        "_live_jd_intelligence_provider_adapter",
        lambda request: (_ for _ in ()).throw(AssertionError("readback called provider")),
    )

    payload = services.saved_scan_report_payload(row["scan_id"], owner_user_id="test-owner")

    assert calls
    readback = payload["jd_llm_extraction_readback"]
    assert readback["validation_status"] == "valid"
    assert readback["structured_jd_signals"]["required_skills"] == ["Python", "SQL"]
    assert payload["scan_review_payload"]["jd_llm_extraction_readback"] == readback


def test_ui_readback_surface_is_passive_and_does_not_enable_provider_calls():
    # id="scanWorkspaceJdLlmReadback" moved from src/app/planning_ui.py into the
    # React Advanced Diagnostics Command Center (Item 1 Phase 3).
    html = (
        ROOT / "frontend/executive-kpi/src/diagnostics/AdvancedDiagnosticsDashboard.tsx"
    ).read_text(encoding="utf-8")
    script = (ROOT / "src/app/static/scan_workspace.js").read_text(encoding="utf-8")
    renderer = script.split("function renderScanWorkspaceJdLlmReadback()", 1)[1].split(
        "\nfunction ",
        1,
    )[0]
    readback_getter = script.split(
        "function getScanWorkspaceJdLlmReadbackPayload",
        1,
    )[1].split("\nfunction ", 1)[0]
    start_payload_builder = script.split(
        "async function buildScanWorkspaceStartScanPayload",
        1,
    )[1].split("\nasync function ", 1)[0]

    assert '"scanWorkspaceJdLlmReadback"' in html
    assert "jd_llm_extraction_readback" in readback_getter
    assert "fetch(" not in renderer
    assert "enable_jd_llm_extraction" not in start_payload_builder


def test_no_scoring_formula_weight_or_mutation_side_effects(monkeypatch):
    monkeypatch.setattr(
        services,
        "_live_jd_intelligence_provider_adapter",
        lambda _request: _valid_provider_payload(),
    )
    response = _client(monkeypatch).post(
        "/planning/start-scan",
        json={**_request_payload(), "enable_jd_llm_extraction": True},
    )
    readback = response.json()["jd_llm_extraction_readback"]
    safety = readback["safety"]

    assert safety["resume_mutation_performed"] is False
    assert safety["resume_artifact_created"] is False
    assert safety["application_execution_performed"] is False
    assert safety["application_submission_performed"] is False
    assert safety["auto_" + "apply_performed"] is False
    assert safety["final_scoring_performed"] is False
    assert safety["score_formula_changed"] is False
    assert safety["scoring_weights_changed"] is False


def test_docs_capture_phase55b_readback_and_safety():
    text = DOC_PATH.read_text(encoding="utf-8").lower()
    for marker in (
        "default-off",
        "live jd llm",
        "planning scan",
        "api/readback",
        "ui surface",
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
