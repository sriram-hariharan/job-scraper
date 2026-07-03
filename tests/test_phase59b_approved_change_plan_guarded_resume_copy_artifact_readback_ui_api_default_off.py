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
from tests.test_phase58b_manual_exact_change_acceptance_approved_plan_readback_ui_api_default_off import (
    _two_proposal_provider_payload,
)
from tests.test_phase59a_approved_change_plan_guarded_resume_copy_artifact_wiring_default_off import (
    _approved_plan_payload,
)


ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = (
    ROOT
    / "docs/phase59_approved_change_plan_guarded_resume_copy_artifact_readback_ui_api_default_off.md"
)
PROTECTED_HASHES = {
    "src/matching/scorer.py": "c3f0b1f4a938ca933b10991af1ddb0aca2790136c7c6b487a8ee79556ee5ceac",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "src/tailoring/llm.py": "6153c78e5f0eca7c78451f0d234609682e01990041deae7fccb0aa303c653920",
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
    monkeypatch.setattr(api, "_auth_owner_user_id", lambda request: "owner-59b")
    return TestClient(api.app)


def _post_state(client: TestClient, payload: dict) -> dict:
    response = client.post("/planning/saved-scan/phase56a-scan/state", json=payload)
    assert response.status_code == 200
    return response.json()


def test_default_off_api_readback_does_not_create_artifact(monkeypatch):
    calls = []
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())
    monkeypatch.setattr(
        services,
        "_live_exact_resume_change_proposal_provider_adapter",
        lambda request: calls.append(request) or _valid_exact_provider_payload(),
    )

    payload = _post_state(
        _client(monkeypatch),
        {**_state_request(), "approved_change_plan_id": "phase59-plan"},
    )
    readback = payload["guarded_resume_copy_artifact_readback"]

    assert calls == []
    assert readback["artifact_creation_enabled"] is False
    assert readback["artifact_creation_requested"] is False
    assert readback["artifact_created"] is False
    assert readback["validation_status"] == "disabled"
    assert readback["readback_phase"] == "59B"
    assert readback["phase59b_readback_hardened"] is True


def test_enabled_api_readback_exposes_guarded_artifact_observability_fields(monkeypatch):
    plan_payload = _approved_plan_payload(monkeypatch)
    plan_id = plan_payload["manual_exact_change_acceptance_readback"]["approved_change_plan_id"]

    payload = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
        enable_live_exact_resume_change_proposal=True,
        live_exact_resume_change_proposal_adapter=lambda _request: _valid_exact_provider_payload(),
        enable_manual_exact_change_acceptance=True,
        accepted_exact_change_proposal_ids=["phase57-proposal-001"],
        enable_guarded_resume_copy_artifact_creation=True,
        approved_change_plan_id=plan_id,
    )
    readback = payload["guarded_resume_copy_artifact_readback"]

    assert readback["artifact_creation_enabled"] is True
    assert readback["artifact_creation_requested"] is True
    assert readback["artifact_created"] is True
    assert readback["artifact_id"] == readback["stable_artifact_key"]
    assert readback["artifact_kind"] == "guarded_resume_copy_artifact"
    assert readback["output_kind"] == "new_copy_resume_artifact"
    assert readback["source_resume_unchanged"] is True
    assert readback["source_resume_overwritten"] is False
    assert readback["approved_change_plan_id"] == plan_id
    assert readback["applied_approved_change_count"] == 1
    assert readback["validation_status"] == "valid"
    assert readback["fallback_used"] is False
    assert "stable_artifact_key" in readback["api_readback_fields"]
    assert "source_resume_overwritten" in readback["ui_readback_fields"]


def test_valid_approved_plan_input_shows_new_copy_artifact_metadata(monkeypatch):
    plan_payload = _approved_plan_payload(monkeypatch)
    plan_readback = plan_payload["manual_exact_change_acceptance_readback"]

    readback = services._planning_workspace_guarded_resume_copy_artifact_payload(
        manual_acceptance_readback=plan_readback,
        enabled=True,
        approved_change_plan_id=plan_readback["approved_change_plan_id"],
    )

    assert readback["artifact_metadata"]["artifact_created"] is True
    assert readback["artifact_metadata"]["output_kind"] == "new_copy_resume_artifact"
    assert readback["artifact_metadata"]["applied_approved_change_ids"] == [
        "phase57-proposal-001"
    ]
    assert readback["artifact"]["new_copy_only"] is True
    assert readback["artifact"]["persisted"] is False


def test_missing_and_invalid_plan_ids_expose_fallback_metadata(monkeypatch):
    plan_payload = _approved_plan_payload(monkeypatch)
    plan_readback = plan_payload["manual_exact_change_acceptance_readback"]

    missing = services._planning_workspace_guarded_resume_copy_artifact_payload(
        manual_acceptance_readback=plan_readback,
        enabled=True,
        approved_change_plan_id="",
    )
    invalid = services._planning_workspace_guarded_resume_copy_artifact_payload(
        manual_acceptance_readback=plan_readback,
        enabled=True,
        approved_change_plan_id="not-the-plan",
    )

    assert missing["artifact_created"] is False
    assert missing["fallback_reason"] == "approved_change_plan_id_required"
    assert missing["fallback_metadata"]["fallback_error_class"] == "ValueError"
    assert invalid["artifact_created"] is False
    assert invalid["fallback_reason"] == "approved_change_plan_id_mismatch"
    assert invalid["fallback_metadata"]["fallback_reason"] == "approved_change_plan_id_mismatch"
    assert invalid["source_resume_unchanged"] is True
    assert invalid["source_resume_overwritten"] is False


def test_ui_readback_display_uses_existing_response_data_and_is_passive():
    script = (ROOT / "src/app/static/scan_workspace.js").read_text(encoding="utf-8")
    getter = script.split("function getScanWorkspaceGuardedResumeCopyArtifactPayload", 1)[1].split(
        "function renderScanWorkspaceGuardedResumeCopyArtifactReadback",
        1,
    )[0]
    renderer = script.split("function renderScanWorkspaceGuardedResumeCopyArtifactReadback", 1)[1].split(
        "function getScanWorkspaceHasTailoringPreviewContext",
        1,
    )[0]

    assert "guarded_resume_copy_artifact_readback" in getter
    assert "phase59bReadbackHardened" in renderer
    assert "source_resume_overwritten" in renderer
    assert "appliedApprovedChangeCount" in renderer
    assert "artifact_created" in renderer
    assert "_live_exact_resume_change_proposal_provider_adapter" not in getter
    assert "_live_exact_resume_change_proposal_provider_adapter" not in renderer
    assert "fetch(" not in renderer
    assert "postJsonWithTimeout" not in renderer


def test_source_resume_is_not_overwritten_or_mutated(monkeypatch):
    request = _state_request()
    original = deepcopy(request)
    plan_payload = _approved_plan_payload(monkeypatch)
    plan_readback = plan_payload["manual_exact_change_acceptance_readback"]

    readback = services._planning_workspace_guarded_resume_copy_artifact_payload(
        manual_acceptance_readback=plan_readback,
        enabled=True,
        approved_change_plan_id=plan_readback["approved_change_plan_id"],
    )

    assert request == original
    assert readback["source_resume_unchanged"] is True
    assert readback["source_resume_overwritten"] is False
    assert readback["source_resume_mutated"] is False
    assert readback["safety"]["source_resume_mutated"] is False
    assert readback["safety"]["source_resume_overwritten"] is False


def test_no_live_llm_or_provider_calls_are_made_by_artifact_readback(monkeypatch):
    provider_calls = []
    plan_payload = _approved_plan_payload(monkeypatch)
    plan_readback = plan_payload["manual_exact_change_acceptance_readback"]
    monkeypatch.setattr(
        services,
        "_live_exact_resume_change_proposal_provider_adapter",
        lambda request: provider_calls.append(request) or _valid_exact_provider_payload(),
    )

    readback = services._planning_workspace_guarded_resume_copy_artifact_payload(
        manual_acceptance_readback=plan_readback,
        enabled=True,
        approved_change_plan_id=plan_readback["approved_change_plan_id"],
    )

    assert provider_calls == []
    assert readback["artifact_created"] is True
    assert readback["safety"]["provider_call_performed"] is False
    assert readback["safety"]["llm_call_performed"] is False


def test_phase55_56_57_58_and_59a_readbacks_remain_intact(monkeypatch):
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())
    base = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
        enable_live_tailoring_suggestion=True,
        live_tailoring_suggestion_adapter=lambda _request: _valid_tailoring_provider_payload(),
        enable_live_exact_resume_change_proposal=True,
        live_exact_resume_change_proposal_adapter=lambda _request: _two_proposal_provider_payload(),
        enable_manual_exact_change_acceptance=True,
        accepted_exact_change_proposal_ids=["phase57-proposal-001"],
    )
    plan_id = base["manual_exact_change_acceptance_readback"]["approved_change_plan_id"]
    payload = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
        enable_live_tailoring_suggestion=True,
        live_tailoring_suggestion_adapter=lambda _request: _valid_tailoring_provider_payload(),
        enable_live_exact_resume_change_proposal=True,
        live_exact_resume_change_proposal_adapter=lambda _request: _two_proposal_provider_payload(),
        enable_manual_exact_change_acceptance=True,
        accepted_exact_change_proposal_ids=["phase57-proposal-001"],
        enable_guarded_resume_copy_artifact_creation=True,
        approved_change_plan_id=plan_id,
    )
    stored_review = _stored_scan_payload()["scan"]["payload_json"]["scan_review_payload"]

    assert stored_review["jd_llm_extraction_readback"]["validation_status"] == "valid"
    assert payload["live_tailoring_suggestion_readback"]["tailoring_llm_call_performed"] is True
    assert payload["live_exact_resume_change_proposal_readback"]["readback_phase"] == "57B"
    assert payload["manual_exact_change_acceptance_readback"]["readback_phase"] == "58B"
    assert payload["guarded_resume_copy_artifact_readback"]["phase"] == "59A"
    assert payload["guarded_resume_copy_artifact_readback"]["readback_phase"] == "59B"


def test_unaccepted_or_unapproved_proposals_are_not_included(monkeypatch):
    plan_payload = _approved_plan_payload(
        monkeypatch,
        provider_payload=_two_proposal_provider_payload(),
    )
    plan_readback = plan_payload["manual_exact_change_acceptance_readback"]

    readback = services._planning_workspace_guarded_resume_copy_artifact_payload(
        manual_acceptance_readback=plan_readback,
        enabled=True,
        approved_change_plan_id=plan_readback["approved_change_plan_id"],
    )

    assert readback["applied_approved_change_ids"] == ["phase57-proposal-001"]
    assert "phase57-proposal-002" not in readback["applied_approved_change_ids"]
    assert readback["artifact_metadata"]["skipped_change_ids"] == ["phase57-proposal-002"]


def test_no_application_execution_submission_or_scoring_changes(monkeypatch):
    plan_payload = _approved_plan_payload(monkeypatch)
    plan_readback = plan_payload["manual_exact_change_acceptance_readback"]
    readback = services._planning_workspace_guarded_resume_copy_artifact_payload(
        manual_acceptance_readback=plan_readback,
        enabled=True,
        approved_change_plan_id=plan_readback["approved_change_plan_id"],
    )
    safety = readback["safety"]

    assert safety["application_execution_performed"] is False
    assert safety["application_submission_performed"] is False
    assert safety["auto_apply_performed"] is False
    assert safety["scoring_formula_changed"] is False
    assert safety["scoring_weights_changed"] is False
    assert readback["artifact"]["application_execution_performed"] is False
    assert readback["artifact"]["application_submission_performed"] is False


def test_protected_files_are_unchanged():
    for relative, expected in PROTECTED_HASHES.items():
        assert _sha256(ROOT / relative) == expected


def test_docs_include_phase59b_readback_safety_markers():
    text = DOC_PATH.read_text(encoding="utf-8").lower()
    for marker in (
        "default-off",
        "guarded resume copy artifact readback",
        "approved-change plan input",
        "planning workspace action",
        "api readback",
        "deterministic fallback",
        "no live llm call",
        "no source resume overwrite",
        "no application execution",
        "no auto-apply",
    ):
        assert marker in text

