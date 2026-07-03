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


ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = (
    ROOT
    / "docs/phase59_approved_change_plan_guarded_resume_copy_artifact_wiring_default_off.md"
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


def _client(monkeypatch) -> TestClient:
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    monkeypatch.setattr(api, "_auth_owner_user_id", lambda request: "owner-59a")
    return TestClient(api.app)


def _post_state(client: TestClient, payload: dict) -> dict:
    response = client.post("/planning/saved-scan/phase56a-scan/state", json=payload)
    assert response.status_code == 200
    return response.json()


def _approved_plan_payload(monkeypatch, *, provider_payload: dict | None = None) -> dict:
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())
    return services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
        enable_live_exact_resume_change_proposal=True,
        live_exact_resume_change_proposal_adapter=lambda _request: provider_payload
        or _valid_exact_provider_payload(),
        enable_manual_exact_change_acceptance=True,
        accepted_exact_change_proposal_ids=["phase57-proposal-001"],
    )


def test_default_off_planning_workspace_action_does_not_create_artifact(monkeypatch):
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
        approved_change_plan_id="phase58-plan",
    )
    readback = payload["guarded_resume_copy_artifact_readback"]

    assert calls == []
    assert readback["artifact_creation_enabled"] is False
    assert readback["artifact_creation_requested"] is False
    assert readback["artifact_created"] is False
    assert readback["source_resume_unchanged"] is True
    assert readback["source_resume_overwritten"] is False
    assert readback["validation_status"] == "disabled"


def test_enabled_guarded_action_creates_new_copy_artifact_from_approved_plan_only(monkeypatch):
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
    assert readback["artifact_id"].startswith("phase59-guarded-resume-copy-")
    assert readback["artifact_kind"] == "guarded_resume_copy_artifact"
    assert readback["output_kind"] == "new_copy_resume_artifact"
    assert readback["approved_change_plan_id"] == plan_id
    assert readback["applied_approved_change_count"] == 1
    assert readback["applied_approved_change_ids"] == ["phase57-proposal-001"]
    assert readback["artifact"]["new_copy_only"] is True
    assert readback["artifact"]["persisted"] is False


def test_missing_or_invalid_approved_plan_ids_fallback_safely(monkeypatch):
    plan_payload = _approved_plan_payload(monkeypatch)
    missing = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
        enable_live_exact_resume_change_proposal=True,
        live_exact_resume_change_proposal_adapter=lambda _request: _valid_exact_provider_payload(),
        enable_manual_exact_change_acceptance=True,
        accepted_exact_change_proposal_ids=["phase57-proposal-001"],
        enable_guarded_resume_copy_artifact_creation=True,
        approved_change_plan_id="",
    )["guarded_resume_copy_artifact_readback"]
    invalid = services._planning_workspace_guarded_resume_copy_artifact_payload(
        manual_acceptance_readback=plan_payload["manual_exact_change_acceptance_readback"],
        enabled=True,
        approved_change_plan_id="wrong-plan",
    )

    assert missing["artifact_created"] is False
    assert missing["fallback_reason"] == "approved_change_plan_id_required"
    assert missing["fallback_metadata"]["fallback_error_class"] == "ValueError"
    assert invalid["artifact_created"] is False
    assert invalid["fallback_reason"] == "approved_change_plan_id_mismatch"
    assert invalid["source_resume_unchanged"] is True
    assert invalid["source_resume_overwritten"] is False


def test_unapproved_proposal_ids_are_not_included_in_artifact_path(monkeypatch):
    plan_payload = _approved_plan_payload(
        monkeypatch,
        provider_payload=_two_proposal_provider_payload(),
    )
    plan_readback = plan_payload["manual_exact_change_acceptance_readback"]
    artifact = services._planning_workspace_guarded_resume_copy_artifact_payload(
        manual_acceptance_readback=plan_readback,
        enabled=True,
        approved_change_plan_id=plan_readback["approved_change_plan_id"],
    )

    assert artifact["artifact_created"] is True
    assert artifact["applied_approved_change_ids"] == ["phase57-proposal-001"]
    assert "phase57-proposal-002" not in artifact["applied_approved_change_ids"]
    assert artifact["skipped_change_ids"] == ["phase57-proposal-002"]


def test_source_resume_is_not_overwritten_or_mutated(monkeypatch):
    request = _state_request()
    original = deepcopy(request)
    plan_payload = _approved_plan_payload(monkeypatch)
    plan_id = plan_payload["manual_exact_change_acceptance_readback"]["approved_change_plan_id"]

    payload = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **request,
        enable_live_exact_resume_change_proposal=True,
        live_exact_resume_change_proposal_adapter=lambda _request: _valid_exact_provider_payload(),
        enable_manual_exact_change_acceptance=True,
        accepted_exact_change_proposal_ids=["phase57-proposal-001"],
        enable_guarded_resume_copy_artifact_creation=True,
        approved_change_plan_id=plan_id,
    )
    readback = payload["guarded_resume_copy_artifact_readback"]

    assert request == original
    assert readback["source_resume_unchanged"] is True
    assert readback["source_resume_overwritten"] is False
    assert readback["source_resume_mutated"] is False
    assert readback["safety"]["source_resume_mutated"] is False
    assert readback["safety"]["source_resume_overwritten"] is False


def test_no_live_llm_or_provider_call_is_made_by_guarded_artifact_creation(monkeypatch):
    provider_calls = []
    plan_payload = _approved_plan_payload(monkeypatch)
    plan_readback = plan_payload["manual_exact_change_acceptance_readback"]
    monkeypatch.setattr(
        services,
        "_live_exact_resume_change_proposal_provider_adapter",
        lambda request: provider_calls.append(request) or _valid_exact_provider_payload(),
    )

    artifact = services._planning_workspace_guarded_resume_copy_artifact_payload(
        manual_acceptance_readback=plan_readback,
        enabled=True,
        approved_change_plan_id=plan_readback["approved_change_plan_id"],
    )

    assert provider_calls == []
    assert artifact["artifact_created"] is True
    assert artifact["safety"]["provider_call_performed"] is False
    assert artifact["safety"]["llm_call_performed"] is False


def test_api_exposes_guarded_artifact_readback(monkeypatch):
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())
    monkeypatch.setattr(
        services,
        "_live_exact_resume_change_proposal_provider_adapter",
        lambda _request: _valid_exact_provider_payload(),
    )
    client = _client(monkeypatch)
    first = _post_state(
        client,
        {
            **_state_request(),
            "enable_live_exact_resume_change_proposal": True,
            "enable_manual_exact_change_acceptance": True,
            "accepted_exact_change_proposal_ids": ["phase57-proposal-001"],
        },
    )
    plan_id = first["manual_exact_change_acceptance_readback"]["approved_change_plan_id"]
    second = _post_state(
        client,
        {
            **_state_request(),
            "enable_live_exact_resume_change_proposal": True,
            "enable_manual_exact_change_acceptance": True,
            "accepted_exact_change_proposal_ids": ["phase57-proposal-001"],
            "enable_guarded_resume_copy_artifact_creation": True,
            "approved_change_plan_id": plan_id,
        },
    )

    readback = second["guarded_resume_copy_artifact_readback"]
    assert readback["api_readback"] is True
    assert readback["ui_readback"] is True
    assert readback["artifact_created"] is True
    assert second["draft"]["approved_change_plan_id"] == plan_id


def test_phase55_56_57_and_58_readbacks_remain_intact(monkeypatch):
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())
    base = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
        enable_live_tailoring_suggestion=True,
        live_tailoring_suggestion_adapter=lambda _request: _valid_tailoring_provider_payload(),
        enable_live_exact_resume_change_proposal=True,
        live_exact_resume_change_proposal_adapter=lambda _request: _valid_exact_provider_payload(),
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
        live_exact_resume_change_proposal_adapter=lambda _request: _valid_exact_provider_payload(),
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


def test_ui_readback_display_is_passive_and_posts_explicit_guard_fields():
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
    assert "enable_guarded_resume_copy_artifact_creation" in script
    assert "approved_change_plan_id" in script
    assert "source_resume_overwritten" in renderer
    assert "artifact_created" in renderer
    assert "_live_exact_resume_change_proposal_provider_adapter" not in renderer
    assert "fetch(" not in renderer
    assert "postJsonWithTimeout" not in renderer


def test_no_application_execution_submission_or_scoring_changes(monkeypatch):
    plan_payload = _approved_plan_payload(monkeypatch)
    plan_readback = plan_payload["manual_exact_change_acceptance_readback"]
    artifact = services._planning_workspace_guarded_resume_copy_artifact_payload(
        manual_acceptance_readback=plan_readback,
        enabled=True,
        approved_change_plan_id=plan_readback["approved_change_plan_id"],
    )
    safety = artifact["safety"]

    assert safety["application_execution_performed"] is False
    assert safety["application_submission_performed"] is False
    assert safety["auto_apply_performed"] is False
    assert safety["scoring_formula_changed"] is False
    assert safety["scoring_weights_changed"] is False
    assert artifact["artifact"]["application_execution_performed"] is False
    assert artifact["artifact"]["application_submission_performed"] is False


def test_protected_files_are_unchanged():
    for relative, expected in PROTECTED_HASHES.items():
        assert _sha256(ROOT / relative) == expected


def test_docs_include_phase59_safety_and_wiring_markers():
    text = DOC_PATH.read_text(encoding="utf-8").lower()
    for marker in (
        "default-off",
        "guarded resume copy artifact wiring",
        "approved-change plan input",
        "planning workspace action",
        "deterministic fallback",
        "no live llm call",
        "no source resume overwrite",
        "no application execution",
        "no auto-apply",
    ):
        assert marker in text

