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
from tests.test_phase57a_live_exact_resume_change_proposal_planning_workspace_wiring_default_off import (
    _valid_exact_provider_payload,
)


ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = (
    ROOT
    / "docs/phase58_manual_exact_change_acceptance_approved_plan_readback_ui_api_default_off.md"
)
PROTECTED_HASHES = {
    "src/matching/scorer.py": "c3f0b1f4a938ca933b10991af1ddb0aca2790136c7c6b487a8ee79556ee5ceac",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "src/tailoring/llm.py": "d47c5d84758ca185a2fd4d8e2062018b48498592a4b79e88182036c2c4edbc28",
    "generate_tailoring_" + "suggestions" + ".py": (
        "559a66a7c7a1963d322a1e7b3f0fd3ede1ea161a9be2d176dcce0ef1016ea9ff"
    ),
    "application_execution_" + "queue" + ".py": (
        "c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0"
    ),
}


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _client(monkeypatch) -> TestClient:
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    monkeypatch.setattr(api, "_auth_owner_user_id", lambda request: "owner-58b")
    return TestClient(api.app)


def _post_state(client: TestClient, payload: dict) -> dict:
    response = client.post("/planning/saved-scan/phase56a-scan/state", json=payload)
    assert response.status_code == 200
    return response.json()


def _two_proposal_provider_payload() -> dict:
    payload = deepcopy(_valid_exact_provider_payload())
    payload["refined_change_proposals"].append(
        {
            **payload["refined_change_proposals"][0],
            "proposal_id": "phase57-proposal-002",
            "target_identifier": "bullet-2",
        }
    )
    return payload


def test_default_off_api_readback_does_not_create_approved_plan(monkeypatch):
    calls = []
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())
    monkeypatch.setattr(
        services,
        "_live_exact_resume_change_proposal_provider_adapter",
        lambda request: calls.append(request) or _valid_exact_provider_payload(),
    )

    payload = _post_state(
        _client(monkeypatch),
        {
            **_state_request(),
            "accepted_exact_change_proposal_ids": ["phase57-proposal-001"],
        },
    )
    readback = payload["manual_exact_change_acceptance_readback"]

    assert calls == []
    assert readback["manual_acceptance_enabled"] is False
    assert readback["manual_acceptance_performed"] is False
    assert readback["approved_change_plan_created"] is False
    assert readback["validation_status"] == "disabled"
    assert readback["readback_phase"] == "58B"
    assert readback["phase58b_readback_hardened"] is True


def test_enabled_api_readback_exposes_manual_acceptance_plan_fields(monkeypatch):
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())
    monkeypatch.setattr(
        services,
        "_live_exact_resume_change_proposal_provider_adapter",
        lambda _request: _valid_exact_provider_payload(),
    )

    payload = _post_state(
        _client(monkeypatch),
        {
            **_state_request(),
            "enable_live_exact_resume_change_proposal": True,
            "enable_manual_exact_change_acceptance": True,
            "accepted_exact_change_proposal_ids": ["phase57-proposal-001"],
        },
    )
    readback = payload["manual_exact_change_acceptance_readback"]

    assert readback["manual_acceptance_enabled"] is True
    assert readback["manual_acceptance_performed"] is True
    assert readback["accepted_proposal_count"] == 1
    assert readback["accepted_proposal_ids"] == ["phase57-proposal-001"]
    assert readback["stable_accepted_proposal_keys"] == ["phase57-proposal-001"]
    assert readback["approved_change_plan_created"] is True
    assert readback["approved_change_plan_id"]
    assert readback["stable_plan_key"] == readback["approved_change_plan_id"]
    assert readback["validation_status"] == "valid"
    assert readback["fallback_used"] is False
    assert "accepted_proposal_ids" in readback["api_readback_fields"]
    assert "stable_plan_key" in readback["ui_readback_fields"]
    assert readback["manual_acceptance_metadata"]["approved_change_plan_created"] is True


def test_accepted_ids_appear_and_unaccepted_ids_are_not_approved(monkeypatch):
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())
    monkeypatch.setattr(
        services,
        "_live_exact_resume_change_proposal_provider_adapter",
        lambda _request: _two_proposal_provider_payload(),
    )

    payload = _post_state(
        _client(monkeypatch),
        {
            **_state_request(),
            "enable_live_exact_resume_change_proposal": True,
            "enable_manual_exact_change_acceptance": True,
            "accepted_exact_change_proposal_ids": ["phase57-proposal-001"],
        },
    )
    readback = payload["manual_exact_change_acceptance_readback"]
    approved = readback["approved_change_plan_packet"]["approved_changes"]

    assert [row["proposal_id"] for row in approved] == ["phase57-proposal-001"]
    assert "phase57-proposal-002" not in readback["accepted_proposal_ids"]
    assert readback["skipped_proposal_ids"] == ["phase57-proposal-002"]
    assert readback["rejected_proposal_count"] == 1
    assert readback["manual_acceptance_metadata"]["skipped_proposal_count"] == 1


def test_missing_and_invalid_accepted_ids_expose_fallback_metadata(monkeypatch):
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())
    monkeypatch.setattr(
        services,
        "_live_exact_resume_change_proposal_provider_adapter",
        lambda _request: _valid_exact_provider_payload(),
    )

    missing = _post_state(
        _client(monkeypatch),
        {
            **_state_request(),
            "enable_live_exact_resume_change_proposal": True,
            "enable_manual_exact_change_acceptance": True,
            "accepted_exact_change_proposal_ids": [],
        },
    )["manual_exact_change_acceptance_readback"]
    invalid = _post_state(
        _client(monkeypatch),
        {
            **_state_request(),
            "enable_live_exact_resume_change_proposal": True,
            "enable_manual_exact_change_acceptance": True,
            "accepted_exact_change_proposal_ids": ["unknown-proposal"],
        },
    )["manual_exact_change_acceptance_readback"]

    assert missing["approved_change_plan_created"] is False
    assert missing["fallback_reason"] == "accepted_proposal_ids_required"
    assert missing["fallback_metadata"]["fallback_reason"] == "accepted_proposal_ids_required"
    assert invalid["approved_change_plan_created"] is False
    assert invalid["fallback_reason"] == "unknown_accepted_proposal_ids"
    assert invalid["fallback_error_class"] == "ValueError"
    assert invalid["fallback_metadata"]["fallback_error_class"] == "ValueError"
    assert invalid["invalid_proposal_ids"] == ["unknown-proposal"]


def test_ui_readback_display_uses_existing_response_data_and_is_passive():
    script = (ROOT / "src/app/static/scan_workspace.js").read_text(encoding="utf-8")
    getter = script.split("function getScanWorkspaceManualExactChangeAcceptancePayload", 1)[1].split(
        "function renderScanWorkspaceManualExactChangeAcceptanceReadback",
        1,
    )[0]
    renderer = script.split("function renderScanWorkspaceManualExactChangeAcceptanceReadback", 1)[1].split(
        "function getScanWorkspaceHasTailoringPreviewContext",
        1,
    )[0]

    assert "manual_exact_change_acceptance_readback" in getter
    assert "phase58bReadbackHardened" in renderer
    assert "manualAcceptanceRejectedCount" in renderer
    assert "manualAcceptanceInvalidCount" in renderer
    assert "approved_change_plan_created" in renderer
    assert "_live_exact_resume_change_proposal_provider_adapter" not in getter
    assert "_live_exact_resume_change_proposal_provider_adapter" not in renderer
    assert "fetch(" not in renderer
    assert "postJsonWithTimeout" not in renderer


def test_no_live_provider_call_is_made_by_manual_acceptance_readback(monkeypatch):
    provider_calls = []
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())

    phase57_payload = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
        enable_live_exact_resume_change_proposal=True,
        live_exact_resume_change_proposal_adapter=lambda _request: _valid_exact_provider_payload(),
    )
    monkeypatch.setattr(
        services,
        "_live_exact_resume_change_proposal_provider_adapter",
        lambda request: provider_calls.append(request) or _valid_exact_provider_payload(),
    )

    readback = services._planning_workspace_manual_exact_change_acceptance_payload(
        live_exact_change_readback=phase57_payload["live_exact_resume_change_proposal_readback"],
        enabled=True,
        accepted_proposal_ids=["phase57-proposal-001"],
    )

    assert provider_calls == []
    assert readback["approved_change_plan_created"] is True
    assert readback["safety"]["provider_call_performed"] is False
    assert readback["safety"]["llm_call_performed"] is False


def test_phase55_phase56_phase57_and_phase58a_readbacks_remain_intact(monkeypatch):
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())

    payload = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
        enable_live_tailoring_suggestion=True,
        live_tailoring_suggestion_adapter=lambda _request: _valid_tailoring_provider_payload(),
        enable_live_exact_resume_change_proposal=True,
        live_exact_resume_change_proposal_adapter=lambda _request: _valid_exact_provider_payload(),
        enable_manual_exact_change_acceptance=True,
        accepted_exact_change_proposal_ids=["phase57-proposal-001"],
    )
    stored_review = _stored_scan_payload()["scan"]["payload_json"]["scan_review_payload"]

    assert stored_review["jd_llm_extraction_readback"]["validation_status"] == "valid"
    assert payload["live_tailoring_suggestion_readback"]["tailoring_llm_call_performed"] is True
    assert payload["live_exact_resume_change_proposal_readback"]["readback_phase"] == "57B"
    assert payload["manual_exact_change_acceptance_readback"]["phase"] == "58A"
    assert payload["manual_exact_change_acceptance_readback"]["readback_phase"] == "58B"


def test_no_mutation_artifact_application_submission_or_scoring_side_effects(monkeypatch):
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())

    payload = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
        enable_live_exact_resume_change_proposal=True,
        live_exact_resume_change_proposal_adapter=lambda _request: _valid_exact_provider_payload(),
        enable_manual_exact_change_acceptance=True,
        accepted_exact_change_proposal_ids=["phase57-proposal-001"],
    )

    safety = payload["manual_exact_change_acceptance_readback"]["safety"]
    assert safety["resume_mutation_performed"] is False
    assert safety["resume_overwrite_performed"] is False
    assert safety["resume_artifact_created"] is False
    assert safety["suggestion_application_performed"] is False
    assert safety["application_execution_performed"] is False
    assert safety["application_submission_performed"] is False
    assert safety["auto_apply_performed"] is False
    assert safety["scoring_formula_changed"] is False
    assert safety["scoring_weights_changed"] is False


def test_protected_files_are_unchanged():
    for relative, expected in PROTECTED_HASHES.items():
        assert _sha256(ROOT / relative) == expected


def test_docs_include_phase58b_readback_safety_markers():
    text = DOC_PATH.read_text(encoding="utf-8").lower()
    for marker in (
        "default-off",
        "manual exact change acceptance readback",
        "approved-change plan readback",
        "planning workspace action",
        "api readback",
        "deterministic fallback",
        "no live llm call",
        "no resume mutation",
        "no resume artifact creation",
        "no application execution",
        "no auto-apply",
    ):
        assert marker in text

