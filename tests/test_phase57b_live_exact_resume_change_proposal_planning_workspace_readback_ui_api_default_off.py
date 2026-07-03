from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services
from tests.test_phase56a_live_tailoring_suggestion_planning_workspace_wiring_default_off import (
    _patch_storage,
    _state_request,
    _stored_scan_payload,
    _valid_provider_payload as _valid_tailoring_provider_payload,
)
from tests.test_phase57a_live_exact_resume_change_proposal_planning_workspace_wiring_default_off import (
    _valid_exact_provider_payload,
)


ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = (
    ROOT
    / "docs/phase57_live_exact_resume_change_proposal_planning_workspace_readback_ui_api_default_off.md"
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


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _client(monkeypatch) -> TestClient:
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    monkeypatch.setattr(api, "_auth_owner_user_id", lambda request: "owner-57b")
    return TestClient(api.app)


def _post_state(client: TestClient, payload: dict) -> dict:
    response = client.post("/planning/saved-scan/phase56a-scan/state", json=payload)
    assert response.status_code == 200
    return response.json()


def test_default_off_api_readback_does_not_call_live_exact_change_provider(monkeypatch):
    calls = []
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())
    monkeypatch.setattr(
        services,
        "_live_exact_resume_change_proposal_provider_adapter",
        lambda request: calls.append(request) or _valid_exact_provider_payload(),
    )

    payload = _post_state(_client(monkeypatch), _state_request())
    readback = payload["live_exact_resume_change_proposal_readback"]

    assert calls == []
    assert readback["exact_change_llm_enabled"] is False
    assert readback["exact_change_llm_call_attempted"] is False
    assert readback["exact_change_llm_call_performed"] is False
    assert readback["fallback_used"] is True
    assert readback["validation_status"] == "disabled"
    assert readback["readback_phase"] == "57B"
    assert readback["phase57b_readback_hardened"] is True


def test_enabled_api_readback_exposes_exact_change_observability_fields(monkeypatch):
    calls = []
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())
    monkeypatch.setattr(
        services,
        "_live_exact_resume_change_proposal_provider_adapter",
        lambda request: calls.append(request) or _valid_exact_provider_payload(),
    )

    payload = _post_state(
        _client(monkeypatch),
        {**_state_request(), "enable_live_exact_resume_change_proposal": True},
    )
    readback = payload["live_exact_resume_change_proposal_readback"]

    assert calls
    assert readback["exact_change_llm_enabled"] is True
    assert readback["exact_change_llm_call_attempted"] is True
    assert readback["exact_change_llm_call_performed"] is True
    assert readback["fallback_used"] is False
    assert readback["validation_status"] == "valid"
    assert readback["provider"] == "fake-exact-provider"
    assert readback["model"] == "fake-exact-model"
    assert readback["prompt_version"] == "fake-exact-prompt-v1"
    assert readback["token_usage"] == {"total_token_count": 55}
    assert readback["cost"] == {"estimated_cost": 0.02, "cost_currency": "USD"}
    assert readback["latency_ms"] == 91
    assert "stable_proposed_change_keys" in readback["api_readback_fields"]
    assert "stable_proposed_change_keys" in readback["ui_readback_fields"]


def test_valid_fake_provider_proposed_changes_are_shown_in_readback_metadata(monkeypatch):
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())
    monkeypatch.setattr(
        services,
        "_live_exact_resume_change_proposal_provider_adapter",
        lambda _request: _valid_exact_provider_payload(),
    )

    payload = _post_state(
        _client(monkeypatch),
        {**_state_request(), "enable_live_exact_resume_change_proposal": True},
    )
    readback = payload["live_exact_resume_change_proposal_readback"]

    assert readback["proposed_change_count"] == 1
    assert readback["proposed_change_ids"] == ["phase57-proposal-001"]
    assert readback["stable_proposed_change_keys"] == ["phase57-proposal-001"]
    assert readback["proposal_metadata"]["proposed_change_count"] == 1
    assert readback["proposal_metadata"]["stable_proposed_change_keys"] == [
        "phase57-proposal-001"
    ]
    assert readback["proposed_changes_preview"][0]["manual_review_required"] is True
    assert readback["proposed_changes_preview"][0]["requires_user_acceptance"] is True


def test_invalid_provider_response_falls_back_and_exposes_fallback_metadata(monkeypatch):
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())
    monkeypatch.setattr(
        services,
        "_live_exact_resume_change_proposal_provider_adapter",
        lambda _request: {"raw_response": "{bad json"},
    )

    payload = _post_state(
        _client(monkeypatch),
        {**_state_request(), "enable_live_exact_resume_change_proposal": True},
    )
    readback = payload["live_exact_resume_change_proposal_readback"]

    assert readback["exact_change_llm_call_attempted"] is True
    assert readback["exact_change_llm_call_performed"] is False
    assert readback["fallback_used"] is True
    assert readback["validation_status"] == "fallback"
    assert readback["fallback_reason"] == "provider_response_invalid"
    assert readback["fallback_error_class"] == "ValueError"
    assert readback["fallback_metadata"]["fallback_reason"] == "provider_response_invalid"
    assert readback["fallback_metadata"]["fallback_error_class"] == "ValueError"


def test_provider_exception_falls_back_and_exposes_error_class(monkeypatch):
    def failing_provider(_request):
        raise RuntimeError("provider unavailable")

    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())
    monkeypatch.setattr(
        services,
        "_live_exact_resume_change_proposal_provider_adapter",
        failing_provider,
    )

    payload = _post_state(
        _client(monkeypatch),
        {**_state_request(), "enable_live_exact_resume_change_proposal": True},
    )
    readback = payload["live_exact_resume_change_proposal_readback"]

    assert readback["exact_change_llm_call_attempted"] is True
    assert readback["exact_change_llm_call_performed"] is False
    assert readback["fallback_used"] is True
    assert readback["validation_status"] == "fallback"
    assert readback["fallback_error_class"] == "RuntimeError"
    assert readback["fallback_metadata"]["fallback_error_class"] == "RuntimeError"
    assert readback["proposed_change_count"] == 0


def test_ui_readback_display_uses_existing_response_data_and_is_passive():
    script = (ROOT / "src/app/static/scan_workspace.js").read_text(encoding="utf-8")
    getter = script.split("function getScanWorkspaceExactChangeLlmReadbackPayload", 1)[1].split(
        "function renderScanWorkspaceExactChangeLlmReadback",
        1,
    )[0]
    renderer = script.split("function renderScanWorkspaceExactChangeLlmReadback", 1)[1].split(
        "function getScanWorkspaceHasTailoringPreviewContext",
        1,
    )[0]

    assert "live_exact_resume_change_proposal_readback" in getter
    assert "stable_proposed_change_keys" in renderer
    assert "exactChangeLlmStableProposedChangeKeys" in renderer
    assert "_live_exact_resume_change_proposal_provider_adapter" not in getter
    assert "_live_exact_resume_change_proposal_provider_adapter" not in renderer
    assert "fetch(" not in renderer
    assert "postJsonWithTimeout" not in renderer


def test_phase55_phase56_and_phase57a_readbacks_remain_intact(monkeypatch):
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())

    payload = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
        enable_live_tailoring_suggestion=True,
        live_tailoring_suggestion_adapter=lambda _request: _valid_tailoring_provider_payload(),
        enable_live_exact_resume_change_proposal=True,
        live_exact_resume_change_proposal_adapter=lambda _request: _valid_exact_provider_payload(),
    )

    tailoring = payload["live_tailoring_suggestion_readback"]
    exact = payload["live_exact_resume_change_proposal_readback"]
    stored_review = _stored_scan_payload()["scan"]["payload_json"]["scan_review_payload"]

    assert stored_review["jd_llm_extraction_readback"]["validation_status"] == "valid"
    assert tailoring["tailoring_llm_call_performed"] is True
    assert exact["phase"] == "57A"
    assert exact["readback_phase"] == "57B"
    assert exact["exact_change_llm_call_performed"] is True


def test_no_mutation_artifact_approval_application_or_scoring_side_effects(monkeypatch):
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())

    payload = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
        enable_live_exact_resume_change_proposal=True,
        live_exact_resume_change_proposal_adapter=lambda _request: _valid_exact_provider_payload(),
    )

    safety = payload["live_exact_resume_change_proposal_readback"]["safety"]
    assert safety["resume_mutation_performed"] is False
    assert safety["resume_overwrite_performed"] is False
    assert safety["resume_artifact_created"] is False
    assert safety["suggestion_application_performed"] is False
    assert safety["proposal_approval_performed"] is False
    assert safety["approved_change_plan_created"] is False
    assert safety["application_execution_performed"] is False
    assert safety["application_submission_performed"] is False
    assert safety["auto_apply_performed"] is False
    assert safety["scoring_formula_changed"] is False
    assert safety["scoring_weights_changed"] is False


def test_protected_files_are_unchanged():
    for relative, expected in PROTECTED_HASHES.items():
        assert _sha256(ROOT / relative) == expected


def test_docs_include_phase57b_readback_and_safety_markers():
    doc = DOC_PATH.read_text(encoding="utf-8").lower()
    for marker in (
        "phase 57b",
        "default-off",
        "live exact resume change proposal readback",
        "planning workspace action",
        "api readback",
        "ui readback",
        "deterministic fallback",
        "no resume mutation",
        "no resume artifact creation",
        "no application execution",
        "no auto-apply",
        "no proposal approval",
        "no approved-change plan creation",
    ):
        assert marker in doc
