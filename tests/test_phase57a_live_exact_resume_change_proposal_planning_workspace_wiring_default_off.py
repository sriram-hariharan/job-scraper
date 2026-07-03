from __future__ import annotations

from copy import deepcopy
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


ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = (
    ROOT
    / "docs/phase57_live_exact_resume_change_proposal_planning_workspace_wiring_default_off.md"
)
PROTECTED_HASHES = {
    "src/matching/scorer.py": "c3f0b1f4a938ca933b10991af1ddb0aca2790136c7c6b487a8ee79556ee5ceac",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "src/tailoring/llm.py": "44614b3b0ecf7b13514996b33ddc9d4346024e9cf031f77eaa135e8a0ab30ce8",
    "generate_tailoring_" + "suggestions" + ".py": (
        "2422452d1c7a54777684b399730d02c11e58ce1ad6ac5658527ad71bb9050f28"
    ),
    "application_execution_" + "queue" + ".py": (
        "c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0"
    ),
}


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _valid_exact_provider_payload() -> dict:
    return {
        "refined_change_proposals": [
            {
                "proposal_id": "phase57-proposal-001",
                "change_type": "bullet",
                "target_section": "experience",
                "target_identifier": "bullet-1",
                "current_text": "Built Python pipelines.",
                "proposed_text": "Built Python pipelines emphasizing Airflow orchestration.",
                "change_reason": "Align existing Python evidence with supplied JD Airflow signal.",
                "jd_terms_supported": ["Python", "Airflow"],
                "resume_evidence_used": ["Built Python pipelines."],
                "risk_flags": [],
                "manual_review_required": True,
                "requires_user_acceptance": True,
            }
        ],
        "resume_overwrite_performed": False,
        "resume_mutation_performed": False,
        "application_submission_performed": False,
        "model_provider": "fake-exact-provider",
        "model_name": "fake-exact-model",
        "prompt_version": "fake-exact-prompt-v1",
        "token_usage": {"total_token_count": 55},
        "cost": {"estimated_cost": 0.02, "cost_currency": "USD"},
        "latency_ms": 91,
    }


def _client(monkeypatch) -> TestClient:
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    monkeypatch.setattr(api, "_auth_owner_user_id", lambda request: "owner-57a")
    return TestClient(api.app)


def _post_state(client: TestClient, payload: dict) -> dict:
    response = client.post("/planning/saved-scan/phase56a-scan/state", json=payload)
    assert response.status_code == 200
    return response.json()


def test_default_off_planning_workspace_action_does_not_call_live_exact_change_provider(
    monkeypatch,
):
    calls = []
    _patch_storage(monkeypatch)
    monkeypatch.setattr(
        services,
        "get_saved_scan_postgres_payload",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("unexpected scan read")),
    )

    payload = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
        live_exact_resume_change_proposal_adapter=lambda request: calls.append(request)
        or _valid_exact_provider_payload(),
    )

    assert calls == []
    assert payload["ok"] is True
    assert payload["draft"]["selected_patch_candidate_ids"] == ["candidate-1"]
    readback = payload["live_exact_resume_change_proposal_readback"]
    assert readback["exact_change_llm_enabled"] is False
    assert readback["exact_change_llm_call_attempted"] is False
    assert readback["exact_change_llm_call_performed"] is False
    assert readback["fallback_used"] is True
    assert readback["validation_status"] == "disabled"
    assert readback["fallback_reason"] == "feature_flag_disabled"


def test_enabled_planning_workspace_action_calls_existing_exact_change_runtime_path(
    monkeypatch,
):
    calls = []
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())

    payload = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
        enable_live_exact_resume_change_proposal=True,
        live_exact_resume_change_proposal_adapter=lambda request: calls.append(request)
        or _valid_exact_provider_payload(),
    )

    readback = payload["live_exact_resume_change_proposal_readback"]
    assert calls
    assert calls[0]["request_type"] == "exact_resume_change_set_refinement"
    assert calls[0]["manual_trigger_required"] is True
    assert readback["exact_change_llm_enabled"] is True
    assert readback["exact_change_llm_call_attempted"] is True
    assert readback["exact_change_llm_call_performed"] is True
    assert readback["fallback_used"] is False
    assert readback["validation_status"] == "valid"
    assert readback["provider"] == "fake-exact-provider"
    assert readback["model"] == "fake-exact-model"
    assert readback["prompt_version"] == "fake-exact-prompt-v1"


def test_valid_fake_provider_response_appears_in_workspace_readback_metadata(
    monkeypatch,
):
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())

    payload = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
        enable_live_exact_resume_change_proposal=True,
        live_exact_resume_change_proposal_adapter=lambda _request: _valid_exact_provider_payload(),
    )

    readback = payload["live_exact_resume_change_proposal_readback"]
    assert readback["proposed_change_count"] == 1
    assert readback["proposed_change_ids"] == ["phase57-proposal-001"]
    assert readback["stable_proposed_change_keys"] == ["phase57-proposal-001"]
    assert readback["proposed_changes_preview"][0]["target_identifier"] == "bullet-1"
    assert readback["token_usage"] == {"total_token_count": 55}
    assert readback["cost"] == {"estimated_cost": 0.02, "cost_currency": "USD"}
    assert readback["latency_ms"] == 91


def test_invalid_provider_response_falls_back_safely(monkeypatch):
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())

    payload = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
        enable_live_exact_resume_change_proposal=True,
        live_exact_resume_change_proposal_adapter=lambda _request: {"raw_response": "{bad json"},
    )

    readback = payload["live_exact_resume_change_proposal_readback"]
    assert readback["exact_change_llm_call_attempted"] is True
    assert readback["exact_change_llm_call_performed"] is False
    assert readback["fallback_used"] is True
    assert readback["validation_status"] == "fallback"
    assert "provider response required" in readback["validation_errors"] or readback[
        "validation_errors"
    ]


def test_provider_exception_falls_back_safely(monkeypatch):
    def failing_provider(_request):
        raise RuntimeError("provider unavailable")

    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())

    payload = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
        enable_live_exact_resume_change_proposal=True,
        live_exact_resume_change_proposal_adapter=failing_provider,
    )

    readback = payload["live_exact_resume_change_proposal_readback"]
    assert readback["exact_change_llm_call_attempted"] is True
    assert readback["exact_change_llm_call_performed"] is False
    assert readback["fallback_used"] is True
    assert readback["validation_status"] == "fallback"
    assert readback["fallback_error_class"] == "RuntimeError"
    assert readback["proposed_change_count"] == 0


def test_existing_workspace_output_phase55_and_phase56_readbacks_remain_present(
    monkeypatch,
):
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())

    payload = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
        enable_live_tailoring_suggestion=True,
        live_tailoring_suggestion_adapter=lambda _request: _valid_tailoring_provider_payload(),
        enable_live_exact_resume_change_proposal=True,
        live_exact_resume_change_proposal_adapter=lambda _request: _valid_exact_provider_payload(),
    )

    assert payload["draft"]["draft_status"] == "saved_scan_state"
    assert payload["score_preview"] == {}
    tailoring = payload["live_tailoring_suggestion_readback"]
    exact = payload["live_exact_resume_change_proposal_readback"]
    assert tailoring["phase"] == "56B"
    assert tailoring["tailoring_llm_call_performed"] is True
    assert exact["phase"] == "57A"
    stored_review = _stored_scan_payload()["scan"]["payload_json"]["scan_review_payload"]
    assert stored_review["jd_llm_extraction_readback"]["validation_status"] == "valid"


def test_api_default_off_does_not_call_live_exact_change_provider(monkeypatch):
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
    assert readback["api_readback"] is True
    assert readback["ui_readback"] is True
    assert readback["exact_change_llm_enabled"] is False
    assert readback["exact_change_llm_call_attempted"] is False
    assert readback["validation_status"] == "disabled"


def test_api_enabled_readback_exposes_exact_change_observability(monkeypatch):
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
    assert readback["validation_status"] == "valid"
    assert readback["proposed_change_ids"] == ["phase57-proposal-001"]


def test_ui_readback_display_is_passive_and_uses_existing_response_data():
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
    assert "_live_exact_resume_change_proposal_provider_adapter" not in getter
    assert "_live_exact_resume_change_proposal_provider_adapter" not in renderer
    assert "fetch(" not in renderer
    assert "postJsonWithTimeout" not in renderer
    assert "proposed_change_ids" in renderer
    assert "fallback_error_class" in renderer


def test_no_resume_mutation_artifact_application_or_scoring_side_effects(monkeypatch):
    before_request = _state_request()
    request_copy = deepcopy(before_request)
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())

    payload = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **before_request,
        enable_live_exact_resume_change_proposal=True,
        live_exact_resume_change_proposal_adapter=lambda _request: _valid_exact_provider_payload(),
    )

    assert before_request == request_copy
    safety = payload["live_exact_resume_change_proposal_readback"]["safety"]
    assert safety["resume_mutation_performed"] is False
    assert safety["resume_artifact_created"] is False
    assert safety["approved_change_plan_created"] is False
    assert safety["proposal_approval_performed"] is False
    assert safety["application_execution_performed"] is False
    assert safety["application_submission_performed"] is False
    assert safety["auto_apply_performed"] is False
    assert safety["scoring_formula_changed"] is False
    assert safety["scoring_weights_changed"] is False


def test_phase55_and_phase56_request_flags_remain_intact():
    api_source = (ROOT / "src/app/api.py").read_text(encoding="utf-8")
    services_source = (ROOT / "src/app/services.py").read_text(encoding="utf-8")
    assert "enable_jd_llm_extraction: bool = False" in api_source
    assert "enable_live_tailoring_suggestion: bool = False" in api_source
    assert "enable_live_exact_resume_change_proposal: bool = False" in api_source
    assert "live_tailoring_suggestion_readback" in services_source
    assert "live_exact_resume_change_proposal_readback" in services_source


def test_protected_files_are_unchanged():
    for relative, expected in PROTECTED_HASHES.items():
        assert _sha256(ROOT / relative) == expected


def test_docs_include_phase57_safety_and_wiring_markers():
    doc = DOC_PATH.read_text(encoding="utf-8").lower()
    for marker in (
        "phase 57a",
        "default-off",
        "live exact resume change proposal wiring",
        "planning workspace action",
        "deterministic fallback",
        "phase42 proposal builder",
        "phase43 request packet",
        "phase49 runtime adapter",
        "phase45 validation",
        "phase46 normalization",
        "no resume mutation",
        "no resume artifact creation",
        "no application execution",
        "no application submission",
        "no auto-apply",
        "no approved-change plan",
        "does not change scoring formulas",
    ):
        assert marker in doc
