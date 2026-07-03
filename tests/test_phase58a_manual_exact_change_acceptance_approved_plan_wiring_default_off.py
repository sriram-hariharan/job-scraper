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
    / "docs/phase58_manual_exact_change_acceptance_approved_plan_wiring_default_off.md"
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
    monkeypatch.setattr(api, "_auth_owner_user_id", lambda request: "owner-58a")
    return TestClient(api.app)


def _post_state(client: TestClient, payload: dict) -> dict:
    response = client.post("/planning/saved-scan/phase56a-scan/state", json=payload)
    assert response.status_code == 200
    return response.json()


def test_default_off_planning_workspace_action_does_not_create_approved_plan(monkeypatch):
    calls = []
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())
    monkeypatch.setattr(
        services,
        "_live_exact_resume_change_proposal_provider_adapter",
        lambda request: calls.append(request) or _valid_exact_provider_payload(),
    )

    payload = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
        accepted_exact_change_proposal_ids=["phase57-proposal-001"],
    )

    readback = payload["manual_exact_change_acceptance_readback"]
    assert calls == []
    assert readback["manual_acceptance_enabled"] is False
    assert readback["manual_acceptance_performed"] is False
    assert readback["approved_change_plan_created"] is False
    assert readback["fallback_used"] is True
    assert readback["validation_status"] == "disabled"
    assert readback["accepted_proposal_count"] == 0


def test_enabled_action_creates_plan_only_from_explicitly_accepted_ids(monkeypatch):
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())

    payload = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
        enable_live_exact_resume_change_proposal=True,
        live_exact_resume_change_proposal_adapter=lambda _request: _valid_exact_provider_payload(),
        enable_manual_exact_change_acceptance=True,
        accepted_exact_change_proposal_ids=["phase57-proposal-001"],
    )

    readback = payload["manual_exact_change_acceptance_readback"]
    assert readback["manual_acceptance_enabled"] is True
    assert readback["manual_acceptance_performed"] is True
    assert readback["approved_change_plan_created"] is True
    assert readback["accepted_proposal_count"] == 1
    assert readback["accepted_proposal_ids"] == ["phase57-proposal-001"]
    assert readback["stable_accepted_proposal_keys"] == ["phase57-proposal-001"]
    packet = readback["approved_change_plan_packet"]
    assert packet["payload_type"] == "exact_resume_change_set_approved_change_plan_packet"
    assert [row["proposal_id"] for row in packet["approved_changes"]] == [
        "phase57-proposal-001"
    ]
    assert packet["artifact_created"] is False
    assert packet["resume_change_applied"] is False


def test_unaccepted_proposal_ids_are_not_included(monkeypatch):
    provider_payload = _valid_exact_provider_payload()
    provider_payload["refined_change_proposals"].append(
        {
            **provider_payload["refined_change_proposals"][0],
            "proposal_id": "phase57-proposal-002",
            "target_identifier": "bullet-2",
        }
    )
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())

    payload = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
        enable_live_exact_resume_change_proposal=True,
        live_exact_resume_change_proposal_adapter=lambda _request: provider_payload,
        enable_manual_exact_change_acceptance=True,
        accepted_exact_change_proposal_ids=["phase57-proposal-001"],
    )

    readback = payload["manual_exact_change_acceptance_readback"]
    approved = readback["approved_change_plan_packet"]["approved_changes"]
    assert [row["proposal_id"] for row in approved] == ["phase57-proposal-001"]
    assert readback["skipped_proposal_ids"] == ["phase57-proposal-002"]
    assert readback["rejected_proposal_count"] == 1


def test_missing_or_invalid_proposal_ids_fallback_safely(monkeypatch):
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())

    missing = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
        enable_live_exact_resume_change_proposal=True,
        live_exact_resume_change_proposal_adapter=lambda _request: _valid_exact_provider_payload(),
        enable_manual_exact_change_acceptance=True,
        accepted_exact_change_proposal_ids=[],
    )["manual_exact_change_acceptance_readback"]
    invalid = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
        enable_live_exact_resume_change_proposal=True,
        live_exact_resume_change_proposal_adapter=lambda _request: _valid_exact_provider_payload(),
        enable_manual_exact_change_acceptance=True,
        accepted_exact_change_proposal_ids=["unknown-proposal"],
    )["manual_exact_change_acceptance_readback"]

    assert missing["approved_change_plan_created"] is False
    assert missing["validation_status"] == "fallback"
    assert missing["fallback_reason"] == "accepted_proposal_ids_required"
    assert invalid["approved_change_plan_created"] is False
    assert invalid["validation_status"] == "fallback"
    assert invalid["fallback_reason"] == "unknown_accepted_proposal_ids"
    assert invalid["invalid_proposal_ids"] == ["unknown-proposal"]


def test_manual_acceptance_does_not_call_live_llm_or_provider(monkeypatch):
    calls = []
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())

    payload = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
        enable_live_exact_resume_change_proposal=True,
        live_exact_resume_change_proposal_adapter=lambda _request: _valid_exact_provider_payload(),
        enable_manual_exact_change_acceptance=True,
        accepted_exact_change_proposal_ids=["phase57-proposal-001"],
    )
    monkeypatch.setattr(
        services,
        "_live_exact_resume_change_proposal_provider_adapter",
        lambda request: calls.append(request) or _valid_exact_provider_payload(),
    )
    readback = services._planning_workspace_manual_exact_change_acceptance_payload(
        live_exact_change_readback=payload["live_exact_resume_change_proposal_readback"],
        enabled=True,
        accepted_proposal_ids=["phase57-proposal-001"],
    )

    assert calls == []
    assert readback["approved_change_plan_created"] is True
    assert readback["safety"]["provider_call_performed"] is False
    assert readback["safety"]["llm_call_performed"] is False


def test_phase55_phase56_and_phase57_readbacks_remain_intact(monkeypatch):
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
    assert payload["live_exact_resume_change_proposal_readback"]["exact_change_llm_call_performed"] is True
    assert payload["manual_exact_change_acceptance_readback"]["approved_change_plan_created"] is True


def test_api_acceptance_readback_and_request_fields(monkeypatch):
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
    assert readback["api_readback"] is True
    assert readback["ui_readback"] is True
    assert readback["accepted_proposal_ids"] == ["phase57-proposal-001"]
    assert payload["draft"]["accepted_exact_change_proposal_ids"] == [
        "phase57-proposal-001"
    ]


def test_ui_readback_display_is_passive_and_posts_explicit_acceptance_fields():
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
    assert "accepted_exact_change_proposal_ids" in script
    assert "enable_manual_exact_change_acceptance" in script
    assert "approved_change_plan_created" in renderer
    assert "_live_exact_resume_change_proposal_provider_adapter" not in renderer
    assert "fetch(" not in renderer
    assert "postJsonWithTimeout" not in renderer


def test_no_mutation_artifact_application_or_scoring_side_effects(monkeypatch):
    request = _state_request()
    original = deepcopy(request)
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())

    payload = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **request,
        enable_live_exact_resume_change_proposal=True,
        live_exact_resume_change_proposal_adapter=lambda _request: _valid_exact_provider_payload(),
        enable_manual_exact_change_acceptance=True,
        accepted_exact_change_proposal_ids=["phase57-proposal-001"],
    )

    assert request == original
    safety = payload["manual_exact_change_acceptance_readback"]["safety"]
    assert safety["resume_mutation_performed"] is False
    assert safety["resume_artifact_created"] is False
    assert safety["application_execution_performed"] is False
    assert safety["application_submission_performed"] is False
    assert safety["auto_apply_performed"] is False
    assert safety["scoring_formula_changed"] is False
    assert safety["scoring_weights_changed"] is False


def test_protected_files_are_unchanged():
    for relative, expected in PROTECTED_HASHES.items():
        assert _sha256(ROOT / relative) == expected


def test_docs_include_phase58_safety_and_wiring_markers():
    text = DOC_PATH.read_text(encoding="utf-8").lower()
    for marker in (
        "default-off",
        "manual exact change acceptance",
        "approved-change plan wiring",
        "planning workspace action",
        "deterministic fallback",
        "no live llm call",
        "no resume mutation",
        "no resume artifact creation",
        "no application execution",
        "no auto-apply",
    ):
        assert marker in text
