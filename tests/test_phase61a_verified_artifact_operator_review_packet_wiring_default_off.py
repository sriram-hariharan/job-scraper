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
DOC_PATH = ROOT / "docs/phase61_verified_artifact_operator_review_packet_wiring_default_off.md"
PROTECTED_HASHES = {
    "src/matching/scorer.py": "c3f0b1f4a938ca933b10991af1ddb0aca2790136c7c6b487a8ee79556ee5ceac",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "src/tailoring/llm.py": "d47c5d84758ca185a2fd4d8e2062018b48498592a4b79e88182036c2c4edbc28",
    "generate_tailoring_" + "suggestions" + ".py": (
        "a5e3dda138232fadc6d69bd9f2468459ce2759d961687bf1fa9ee9970c5490c2"
    ),
    "application_execution_" + "queue" + ".py": (
        "c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0"
    ),
}


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _client(monkeypatch) -> TestClient:
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    monkeypatch.setattr(api, "_auth_owner_user_id", lambda request: "owner-61a")
    return TestClient(api.app)


def _post_state(client: TestClient, payload: dict) -> dict:
    response = client.post("/planning/saved-scan/phase56a-scan/state", json=payload)
    assert response.status_code == 200
    return response.json()


def _verified_artifact_readback(monkeypatch) -> dict:
    plan_payload = _approved_plan_payload(monkeypatch)
    plan_readback = plan_payload["manual_exact_change_acceptance_readback"]
    artifact_readback = services._planning_workspace_guarded_resume_copy_artifact_payload(
        manual_acceptance_readback=plan_readback,
        enabled=True,
        approved_change_plan_id=plan_readback["approved_change_plan_id"],
    )
    return services._planning_workspace_guarded_resume_copy_artifact_verification_payload(
        guarded_artifact_readback=artifact_readback,
        enabled=True,
        artifact_id=artifact_readback["artifact_id"],
    )


def test_default_off_planning_workspace_action_does_not_create_operator_review_packet(
    monkeypatch,
):
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
        verified_artifact_operator_review_artifact_id="phase59-artifact",
    )
    readback = payload["verified_artifact_operator_review_packet_readback"]

    assert calls == []
    assert readback["operator_review_packet_enabled"] is False
    assert readback["operator_review_packet_requested"] is False
    assert readback["operator_review_packet_created"] is False
    assert readback["operator_review_packet_id"] == ""
    assert readback["validation_status"] == "disabled"
    assert payload["guarded_resume_copy_artifact_readback"]["artifact_created"] is False


def test_enabled_action_creates_operator_review_packet_from_verified_artifact_metadata_only(
    monkeypatch,
):
    verification = _verified_artifact_readback(monkeypatch)

    readback = services._planning_workspace_verified_artifact_operator_review_packet_payload(
        verification_readback=verification,
        enabled=True,
        artifact_id=verification["artifact_id"],
    )

    assert readback["operator_review_packet_enabled"] is True
    assert readback["operator_review_packet_requested"] is True
    assert readback["operator_review_packet_created"] is True
    assert readback["operator_review_packet_id"].startswith(
        "phase61-verified-artifact-review-"
    )
    assert readback["stable_packet_key"] == readback["operator_review_packet_id"]
    assert readback["artifact_id"] == verification["artifact_id"]
    assert readback["artifact_verification_passed"] is True
    assert readback["approved_change_plan_id"] == verification["approved_change_plan_id"]
    assert readback["review_item_count"] == 1
    assert readback["validation_status"] == "valid"
    assert readback["fallback_used"] is False
    assert readback["operator_review_packet"]["operator_review_only"] is True
    assert readback["operator_review_packet"]["artifact_creation_performed"] is False


def test_api_creates_operator_review_packet_from_verified_artifact(monkeypatch):
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
            "enable_verified_artifact_operator_review_packet": True,
            "verified_artifact_operator_review_artifact_id": artifact_id,
        },
    )
    readback = third["verified_artifact_operator_review_packet_readback"]

    assert readback["operator_review_packet_created"] is True
    assert readback["artifact_id"] == artifact_id
    assert readback["artifact_verification_passed"] is True
    assert readback["review_item_count"] == 1
    assert "operator_review_packet_id" in readback["api_readback_fields"]


def test_missing_or_invalid_artifact_ids_fallback_safely(monkeypatch):
    verification = _verified_artifact_readback(monkeypatch)

    missing = services._planning_workspace_verified_artifact_operator_review_packet_payload(
        verification_readback=verification,
        enabled=True,
        artifact_id="",
    )
    invalid = services._planning_workspace_verified_artifact_operator_review_packet_payload(
        verification_readback=verification,
        enabled=True,
        artifact_id="not-the-artifact",
    )

    assert missing["operator_review_packet_created"] is False
    assert missing["fallback_reason"] == "artifact_id_required"
    assert missing["fallback_metadata"]["fallback_error_class"] == "ValueError"
    assert invalid["operator_review_packet_created"] is False
    assert invalid["fallback_reason"] == "artifact_id_mismatch"
    assert invalid["source_resume_unchanged"] is True
    assert invalid["source_resume_overwritten"] is False


def test_unverified_artifact_metadata_does_not_create_review_packet(monkeypatch):
    verification = _verified_artifact_readback(monkeypatch)
    unverified = {**verification, "artifact_verification_passed": False}

    readback = services._planning_workspace_verified_artifact_operator_review_packet_payload(
        verification_readback=unverified,
        enabled=True,
        artifact_id=verification["artifact_id"],
    )

    assert readback["operator_review_packet_requested"] is True
    assert readback["operator_review_packet_created"] is False
    assert readback["artifact_verification_passed"] is False
    assert readback["fallback_reason"] == "artifact_verification_required"


def test_review_packet_creation_does_not_create_a_new_artifact(monkeypatch):
    verification = _verified_artifact_readback(monkeypatch)
    artifact_before = deepcopy(verification["verified_artifact"])

    readback = services._planning_workspace_verified_artifact_operator_review_packet_payload(
        verification_readback=verification,
        enabled=True,
        artifact_id=verification["artifact_id"],
    )

    assert verification["verified_artifact"] == artifact_before
    assert readback["operator_review_packet_created"] is True
    assert readback["safety"]["artifact_created"] is False
    assert readback["safety"]["artifact_created_by_review_packet"] is False
    assert readback["operator_review_packet"]["artifact_creation_performed"] is False


def test_source_resume_is_not_overwritten_or_mutated(monkeypatch):
    request = _state_request()
    original = deepcopy(request)
    verification = _verified_artifact_readback(monkeypatch)

    readback = services._planning_workspace_verified_artifact_operator_review_packet_payload(
        verification_readback=verification,
        enabled=True,
        artifact_id=verification["artifact_id"],
    )

    assert request == original
    assert readback["source_resume_unchanged"] is True
    assert readback["source_resume_overwritten"] is False
    assert readback["safety"]["source_resume_mutated"] is False
    assert readback["safety"]["source_resume_state_mutated"] is False


def test_no_live_llm_or_provider_calls_are_made(monkeypatch):
    provider_calls = []
    verification = _verified_artifact_readback(monkeypatch)
    monkeypatch.setattr(
        services,
        "_live_exact_resume_change_proposal_provider_adapter",
        lambda request: provider_calls.append(request) or _valid_exact_provider_payload(),
    )

    readback = services._planning_workspace_verified_artifact_operator_review_packet_payload(
        verification_readback=verification,
        enabled=True,
        artifact_id=verification["artifact_id"],
    )

    assert provider_calls == []
    assert readback["safety"]["provider_call_performed"] is False
    assert readback["safety"]["llm_call_performed"] is False
    assert readback["safety"]["network_call_performed"] is False


def test_phase58_59_and_60_readbacks_remain_intact(monkeypatch):
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
    artifact_payload = services.save_saved_scan_state_payload(
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
    artifact_id = artifact_payload["guarded_resume_copy_artifact_readback"]["artifact_id"]
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
        enable_guarded_resume_copy_artifact_verification=True,
        guarded_resume_copy_artifact_id=artifact_id,
        enable_verified_artifact_operator_review_packet=True,
        verified_artifact_operator_review_artifact_id=artifact_id,
    )

    assert payload["manual_exact_change_acceptance_readback"]["readback_phase"] == "58B"
    assert payload["guarded_resume_copy_artifact_readback"]["readback_phase"] == "59B"
    assert payload["guarded_resume_copy_artifact_verification_readback"]["phase"] == "60A"
    assert payload["guarded_resume_copy_artifact_verification_readback"]["readback_phase"] == "60B"
    assert payload["verified_artifact_operator_review_packet_readback"]["phase"] == "61A"


def test_ui_readback_display_uses_existing_response_data_and_is_passive():
    script = (ROOT / "src/app/static/scan_workspace.js").read_text(encoding="utf-8")
    getter = script.split(
        "function getScanWorkspaceVerifiedArtifactOperatorReviewPacketPayload",
        1,
    )[1].split(
        "function renderScanWorkspaceVerifiedArtifactOperatorReviewPacketReadback",
        1,
    )[0]
    renderer = script.split(
        "function renderScanWorkspaceVerifiedArtifactOperatorReviewPacketReadback",
        1,
    )[1].split(
        "function getScanWorkspaceHasTailoringPreviewContext",
        1,
    )[0]

    assert "verified_artifact_operator_review_packet_readback" in getter
    assert "enable_verified_artifact_operator_review_packet" in script
    assert "verified_artifact_operator_review_artifact_id" in script
    assert "operator_review_packet_created" in renderer
    assert "artifact_verification_passed" in renderer
    assert "source_resume_overwritten" in renderer
    assert "_live_exact_resume_change_proposal_provider_adapter" not in renderer
    assert "fetch(" not in renderer
    assert "postJsonWithTimeout" not in renderer


def test_no_application_execution_submission_or_scoring_changes(monkeypatch):
    verification = _verified_artifact_readback(monkeypatch)
    readback = services._planning_workspace_verified_artifact_operator_review_packet_payload(
        verification_readback=verification,
        enabled=True,
        artifact_id=verification["artifact_id"],
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


def test_docs_include_phase61a_review_packet_safety_markers():
    text = DOC_PATH.read_text(encoding="utf-8").lower()
    for marker in (
        "default-off",
        "verified artifact operator review packet",
        "planning workspace action",
        "deterministic fallback",
        "no live llm call",
        "no artifact creation",
        "no source resume overwrite",
        "no application execution",
        "no auto-apply",
    ):
        assert marker in text
