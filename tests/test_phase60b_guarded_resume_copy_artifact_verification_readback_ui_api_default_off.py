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
    / "docs/phase60_guarded_resume_copy_artifact_verification_readback_ui_api_default_off.md"
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
    monkeypatch.setattr(api, "_auth_owner_user_id", lambda request: "owner-60b")
    return TestClient(api.app)


def _post_state(client: TestClient, payload: dict) -> dict:
    response = client.post("/planning/saved-scan/phase56a-scan/state", json=payload)
    assert response.status_code == 200
    return response.json()


def _artifact_readback(monkeypatch) -> dict:
    plan_payload = _approved_plan_payload(monkeypatch)
    plan_readback = plan_payload["manual_exact_change_acceptance_readback"]
    return services._planning_workspace_guarded_resume_copy_artifact_payload(
        manual_acceptance_readback=plan_readback,
        enabled=True,
        approved_change_plan_id=plan_readback["approved_change_plan_id"],
    )


def test_default_off_api_readback_does_not_verify_or_create_artifact(monkeypatch):
    calls = []
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())
    monkeypatch.setattr(
        services,
        "_live_exact_resume_change_proposal_provider_adapter",
        lambda request: calls.append(request) or _valid_exact_provider_payload(),
    )

    payload = _post_state(
        _client(monkeypatch),
        {**_state_request(), "guarded_resume_copy_artifact_id": "phase59-artifact"},
    )
    readback = payload["guarded_resume_copy_artifact_verification_readback"]

    assert calls == []
    assert readback["artifact_verification_enabled"] is False
    assert readback["artifact_verification_requested"] is False
    assert readback["artifact_verification_performed"] is False
    assert readback["artifact_verification_passed"] is False
    assert readback["validation_status"] == "disabled"
    assert readback["readback_phase"] == "60B"
    assert readback["phase60b_readback_hardened"] is True
    assert payload["guarded_resume_copy_artifact_readback"]["artifact_created"] is False


def test_enabled_api_readback_exposes_guarded_verification_observability_fields(monkeypatch):
    artifact_readback = _artifact_readback(monkeypatch)

    readback = services._planning_workspace_guarded_resume_copy_artifact_verification_payload(
        guarded_artifact_readback=artifact_readback,
        enabled=True,
        artifact_id=artifact_readback["artifact_id"],
    )
    metadata = readback["verification_metadata"]

    assert readback["readback_phase"] == "60B"
    assert readback["phase60b_readback_hardened"] is True
    assert readback["artifact_verification_enabled"] is True
    assert readback["artifact_verification_requested"] is True
    assert readback["artifact_verification_performed"] is True
    assert readback["artifact_verification_passed"] is True
    assert readback["artifact_id"] == artifact_readback["artifact_id"]
    assert readback["stable_artifact_key"] == artifact_readback["artifact_id"]
    assert readback["approved_change_plan_id"] == artifact_readback["approved_change_plan_id"]
    assert readback["artifact_readable"] is True
    assert readback["source_resume_unchanged"] is True
    assert readback["source_resume_overwritten"] is False
    assert readback["applied_approved_change_count"] == 1
    assert readback["mismatch_count"] == 0
    assert readback["validation_status"] == "valid"
    assert readback["fallback_used"] is False
    assert metadata["phase60b_readback_hardened"] is True
    assert metadata["artifact_id"] == readback["artifact_id"]
    assert "verification_metadata" in readback["api_readback_fields"]
    assert "phase60b_readback_hardened" in readback["ui_readback_fields"]


def test_valid_existing_artifact_metadata_shows_verification_status_in_api(monkeypatch):
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
    artifact_id = second["guarded_resume_copy_artifact_readback"]["artifact_id"]
    third = _post_state(
        client,
        {
            **_state_request(),
            "enable_live_exact_resume_change_proposal": True,
            "enable_manual_exact_change_acceptance": True,
            "accepted_exact_change_proposal_ids": ["phase57-proposal-001"],
            "enable_guarded_resume_copy_artifact_creation": True,
            "approved_change_plan_id": plan_id,
            "enable_guarded_resume_copy_artifact_verification": True,
            "guarded_resume_copy_artifact_id": artifact_id,
        },
    )
    readback = third["guarded_resume_copy_artifact_verification_readback"]

    assert readback["artifact_verification_performed"] is True
    assert readback["artifact_verification_passed"] is True
    assert readback["artifact_readable"] is True
    assert readback["artifact_id"] == artifact_id
    assert readback["verification_metadata"]["validation_status"] == "valid"


def test_missing_and_invalid_artifact_ids_expose_fallback_metadata(monkeypatch):
    artifact_readback = _artifact_readback(monkeypatch)

    missing = services._planning_workspace_guarded_resume_copy_artifact_verification_payload(
        guarded_artifact_readback=artifact_readback,
        enabled=True,
        artifact_id="",
    )
    invalid = services._planning_workspace_guarded_resume_copy_artifact_verification_payload(
        guarded_artifact_readback=artifact_readback,
        enabled=True,
        artifact_id="not-the-artifact",
    )

    assert missing["artifact_verification_performed"] is False
    assert missing["fallback_reason"] == "artifact_id_required"
    assert missing["fallback_metadata"]["fallback_error_class"] == "ValueError"
    assert missing["verification_metadata"]["fallback_reason"] == "artifact_id_required"
    assert invalid["artifact_verification_performed"] is False
    assert invalid["fallback_reason"] == "artifact_id_mismatch"
    assert invalid["verification_metadata"]["fallback_reason"] == "artifact_id_mismatch"
    assert invalid["artifact_readable"] is False


def test_ui_readback_display_uses_existing_response_data_and_is_passive():
    script = (ROOT / "src/app/static/scan_workspace.js").read_text(encoding="utf-8")
    getter = script.split(
        "function getScanWorkspaceGuardedResumeCopyArtifactVerificationPayload",
        1,
    )[1].split(
        "function renderScanWorkspaceGuardedResumeCopyArtifactVerificationReadback",
        1,
    )[0]
    renderer = script.split(
        "function renderScanWorkspaceGuardedResumeCopyArtifactVerificationReadback",
        1,
    )[1].split(
        "function getScanWorkspaceHasTailoringPreviewContext",
        1,
    )[0]

    assert "guarded_resume_copy_artifact_verification_readback" in getter
    assert "enable_guarded_resume_copy_artifact_verification" in script
    assert "guarded_resume_copy_artifact_id" in script
    assert "phase60bReadbackHardened" in renderer
    assert "artifact_verification_performed" in renderer
    assert "artifact_readable" in renderer
    assert "source_resume_overwritten" in renderer
    assert "_live_exact_resume_change_proposal_provider_adapter" not in renderer
    assert "fetch(" not in renderer
    assert "postJsonWithTimeout" not in renderer


def test_verification_does_not_create_a_new_artifact(monkeypatch):
    artifact_readback = _artifact_readback(monkeypatch)
    artifact_before = deepcopy(artifact_readback["artifact"])

    readback = services._planning_workspace_guarded_resume_copy_artifact_verification_payload(
        guarded_artifact_readback=artifact_readback,
        enabled=True,
        artifact_id=artifact_readback["artifact_id"],
    )

    assert readback["verified_artifact"] == artifact_before
    assert artifact_readback["artifact"] == artifact_before
    assert readback["safety"]["artifact_created_by_verification"] is False


def test_source_resume_is_not_overwritten_or_mutated(monkeypatch):
    request = _state_request()
    original = deepcopy(request)
    artifact_readback = _artifact_readback(monkeypatch)

    readback = services._planning_workspace_guarded_resume_copy_artifact_verification_payload(
        guarded_artifact_readback=artifact_readback,
        enabled=True,
        artifact_id=artifact_readback["artifact_id"],
    )

    assert request == original
    assert readback["source_resume_unchanged"] is True
    assert readback["source_resume_overwritten"] is False
    assert readback["safety"]["source_resume_mutated"] is False
    assert readback["safety"]["source_resume_state_mutated"] is False


def test_no_live_llm_or_provider_calls_are_made_by_readback(monkeypatch):
    provider_calls = []
    artifact_readback = _artifact_readback(monkeypatch)
    monkeypatch.setattr(
        services,
        "_live_exact_resume_change_proposal_provider_adapter",
        lambda request: provider_calls.append(request) or _valid_exact_provider_payload(),
    )

    readback = services._planning_workspace_guarded_resume_copy_artifact_verification_payload(
        guarded_artifact_readback=artifact_readback,
        enabled=True,
        artifact_id=artifact_readback["artifact_id"],
    )

    assert provider_calls == []
    assert readback["safety"]["provider_call_performed"] is False
    assert readback["safety"]["llm_call_performed"] is False
    assert readback["safety"]["network_call_performed"] is False


def test_phase58_59_and_60a_readbacks_remain_intact(monkeypatch):
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
    artifact_id = payload["guarded_resume_copy_artifact_readback"]["artifact_id"]
    verified = services.save_saved_scan_state_payload(
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
        enable_guarded_resume_copy_artifact_verification=True,
        guarded_resume_copy_artifact_id=artifact_id,
    )

    assert verified["manual_exact_change_acceptance_readback"]["readback_phase"] == "58B"
    assert verified["guarded_resume_copy_artifact_readback"]["readback_phase"] == "59B"
    assert verified["guarded_resume_copy_artifact_verification_readback"]["phase"] == "60A"
    assert verified["guarded_resume_copy_artifact_verification_readback"]["readback_phase"] == "60B"


def test_no_application_execution_submission_or_scoring_changes(monkeypatch):
    artifact_readback = _artifact_readback(monkeypatch)
    readback = services._planning_workspace_guarded_resume_copy_artifact_verification_payload(
        guarded_artifact_readback=artifact_readback,
        enabled=True,
        artifact_id=artifact_readback["artifact_id"],
    )
    safety = readback["safety"]

    assert safety["application_execution_performed"] is False
    assert safety["application_submission_performed"] is False
    assert safety["auto_apply_performed"] is False
    assert safety["auto_submit_performed"] is False
    assert safety["scoring_formula_changed"] is False
    assert safety["scoring_weights_changed"] is False


def test_protected_files_are_unchanged():
    for relative, expected in PROTECTED_HASHES.items():
        assert _sha256(ROOT / relative) == expected


def test_docs_include_phase60b_readback_safety_markers():
    text = DOC_PATH.read_text(encoding="utf-8").lower()
    for marker in (
        "default-off",
        "guarded artifact verification readback",
        "artifact readback verification",
        "planning workspace action",
        "api readback",
        "deterministic fallback",
        "no live llm call",
        "no artifact creation by verification",
        "no source resume overwrite",
        "no application execution",
        "no auto-apply",
    ):
        assert marker in text
