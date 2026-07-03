from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services
from tests.test_phase56a_live_tailoring_suggestion_planning_workspace_wiring_default_off import (
    _patch_storage,
    _state_request,
    _stored_scan_payload,
    _valid_provider_payload,
)


ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = (
    ROOT
    / "docs/phase56_live_tailoring_suggestion_planning_workspace_readback_ui_api_default_off.md"
)
PROTECTED_HASHES = {
    "src/matching/scorer.py": "c3f0b1f4a938ca933b10991af1ddb0aca2790136c7c6b487a8ee79556ee5ceac",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "src/tailoring/llm.py": "e2e221f2c2f99c95d97f9e0968254d1bb181c387fc13c82559fa722b6a998d3b",
    "generate_tailoring_" + "suggestions" + ".py": (
        "2422452d1c7a54777684b399730d02c11e58ce1ad6ac5658527ad71bb9050f28"
    ),
    "application_execution_" + "queue" + ".py": (
        "c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0"
    ),
}


def _client(monkeypatch) -> TestClient:
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    monkeypatch.setattr(api, "_auth_owner_user_id", lambda request: "owner-56b")
    return TestClient(api.app)


def _post_state(client: TestClient, payload: dict) -> dict:
    response = client.post("/planning/saved-scan/phase56a-scan/state", json=payload)
    assert response.status_code == 200
    return response.json()


def test_default_off_api_readback_does_not_call_live_tailoring_llm(monkeypatch):
    calls = []
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())
    monkeypatch.setattr(
        services,
        "_live_tailoring_suggestion_provider_adapter",
        lambda request: calls.append(request) or _valid_provider_payload(),
    )

    payload = _post_state(_client(monkeypatch), _state_request())
    readback = payload["live_tailoring_suggestion_readback"]

    assert calls == []
    assert readback["phase"] == "56B"
    assert readback["source_phase"] == "56A"
    assert readback["api_readback"] is True
    assert readback["ui_readback"] is True
    assert readback["tailoring_llm_enabled"] is False
    assert readback["tailoring_llm_call_attempted"] is False
    assert readback["tailoring_llm_call_performed"] is False
    assert readback["fallback_used"] is True
    assert readback["validation_status"] == "disabled"
    assert readback["fallback_reason"] == "feature_flag_disabled"


def test_enabled_api_readback_exposes_live_tailoring_observability(monkeypatch):
    calls = []
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())
    monkeypatch.setattr(
        services,
        "_live_tailoring_suggestion_provider_adapter",
        lambda request: calls.append(request) or _valid_provider_payload(),
    )

    payload = _post_state(
        _client(monkeypatch),
        {**_state_request(), "enable_live_tailoring_suggestion": True},
    )
    readback = payload["live_tailoring_suggestion_readback"]

    assert calls
    assert readback["tailoring_llm_enabled"] is True
    assert readback["tailoring_llm_call_attempted"] is True
    assert readback["tailoring_llm_call_performed"] is True
    assert readback["fallback_used"] is False
    assert readback["validation_status"] == "valid"
    assert readback["provider"] == "fake-provider"
    assert readback["model"] == "fake-model"
    assert readback["prompt_version"] == "fake-prompt-v1"
    assert readback["token_usage"] == {"total_token_count": 42}
    assert readback["cost"] == {"estimated_cost": 0.01, "cost_currency": "USD"}
    assert readback["latency_ms"] == 88


def test_valid_fake_provider_suggestions_are_shown_in_readback_metadata(monkeypatch):
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())
    monkeypatch.setattr(
        services,
        "_live_tailoring_suggestion_provider_adapter",
        lambda _request: _valid_provider_payload(),
    )

    payload = _post_state(
        _client(monkeypatch),
        {**_state_request(), "enable_live_tailoring_suggestion": True},
    )
    readback = payload["live_tailoring_suggestion_readback"]

    assert readback["suggestion_count"] == 1
    assert readback["suggestion_ids"] == ["live_tailoring_001"]
    assert readback["stable_suggestion_keys"] == ["live_tailoring_001"]
    assert readback["suggestions_preview"] == [
        {
            "suggestion_id": "live_tailoring_001",
            "suggestion_type": "patch_ready",
            "source_bullet_id": "bullet-1",
            "target_section": "",
            "patch_ready": True,
        }
    ]


def test_invalid_provider_response_falls_back_and_exposes_metadata(monkeypatch):
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())
    monkeypatch.setattr(
        services,
        "_live_tailoring_suggestion_provider_adapter",
        lambda _request: {"raw_response": "{bad json"},
    )

    payload = _post_state(
        _client(monkeypatch),
        {**_state_request(), "enable_live_tailoring_suggestion": True},
    )
    readback = payload["live_tailoring_suggestion_readback"]

    assert readback["tailoring_llm_call_attempted"] is True
    assert readback["tailoring_llm_call_performed"] is False
    assert readback["fallback_used"] is True
    assert readback["validation_status"] == "fallback"
    assert readback["validation_errors"] == ["invalid_json_response"]
    assert readback["fallback_reason"] == "invalid_json_response"
    assert readback["fallback_error_class"] == "ValueError"


def test_provider_exception_falls_back_and_exposes_error_class(monkeypatch):
    def failing_provider(_request):
        raise RuntimeError("provider unavailable")

    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())
    monkeypatch.setattr(
        services,
        "_live_tailoring_suggestion_provider_adapter",
        failing_provider,
    )

    payload = _post_state(
        _client(monkeypatch),
        {**_state_request(), "enable_live_tailoring_suggestion": True},
    )
    readback = payload["live_tailoring_suggestion_readback"]

    assert readback["tailoring_llm_call_attempted"] is True
    assert readback["tailoring_llm_call_performed"] is False
    assert readback["fallback_used"] is True
    assert readback["validation_status"] == "fallback"
    assert readback["fallback_reason"] == "adapter_error:RuntimeError"
    assert readback["fallback_error_class"] == "RuntimeError"


def test_ui_readback_display_is_passive_and_uses_existing_response_data():
    script = (ROOT / "src/app/static/scan_workspace.js").read_text(encoding="utf-8")
    getter = script.split("function getScanWorkspaceTailoringLlmReadbackPayload", 1)[1].split(
        "function renderScanWorkspaceTailoringLlmReadback", 1
    )[0]
    renderer = script.split("function renderScanWorkspaceTailoringLlmReadback", 1)[1].split(
        "function getScanWorkspaceHasTailoringPreviewContext", 1
    )[0]
    save_function = script.split("async function saveScanWorkspaceDraftState", 1)[1].split(
        "function getScanWorkspaceExportFilename", 1
    )[0]

    assert "live_tailoring_suggestion_readback" in getter
    assert "fallback_reason" in renderer
    assert "fallback_error_class" in renderer
    assert "renderScanWorkspaceTailoringLlmReadback(response)" in save_function
    assert "enable_live_tailoring_suggestion" in save_function
    assert "_live_tailoring_suggestion_provider_adapter" not in renderer


def test_phase55_jd_llm_readback_and_phase56a_behavior_remain_intact(monkeypatch):
    calls = []
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())

    payload = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
        enable_live_tailoring_suggestion=True,
        live_tailoring_suggestion_adapter=lambda request: calls.append(request)
        or _valid_provider_payload(),
    )

    assert calls
    readback = payload["live_tailoring_suggestion_readback"]
    assert readback["tailoring_llm_call_performed"] is True
    assert _stored_scan_payload()["scan"]["payload_json"]["scan_review_payload"][
        "jd_llm_extraction_readback"
    ]["validation_status"] == "valid"


def test_no_mutation_artifact_approved_plan_application_or_scoring_side_effects(
    monkeypatch,
):
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())
    payload = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
        enable_live_tailoring_suggestion=True,
        live_tailoring_suggestion_adapter=lambda _request: _valid_provider_payload(),
    )

    safety = payload["live_tailoring_suggestion_readback"]["safety"]
    for key in (
        "resume_mutation_performed",
        "resume_overwrite_performed",
        "resume_artifact_created",
        "suggestion_application_performed",
        "approved_change_plan_created",
        "exact_resume_change_refinement_performed",
        "application_execution_performed",
        "application_submission_performed",
        "final_scoring_performed",
        "score_formula_changed",
        "scoring_weights_changed",
    ):
        assert safety[key] is False


def test_docs_capture_phase56b_readback_and_safety():
    text = DOC_PATH.read_text(encoding="utf-8").lower()
    for marker in (
        "default-off",
        "live tailoring suggestion readback",
        "planning workspace action",
        "api readback",
        "ui readback",
        "deterministic fallback",
        "does not mutate resumes",
        "does not create resume artifacts",
        "does not execute applications",
        "auto-apply",
    ):
        assert marker in text


def test_protected_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == expected_hash
