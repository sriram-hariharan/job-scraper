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
from tests.test_phase62a_verified_artifact_operator_decision_capture_wiring_default_off import (
    _operator_review_packet_readback,
)


ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = (
    ROOT
    / "docs/phase62_verified_artifact_operator_decision_capture_readback_ui_api_default_off.md"
)
PROTECTED_HASHES = {
    "src/matching/scorer.py": "f56624b5b3c7e2bb01a824386b86fbc2a194e727f0437ca0773764eae64ec941",
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
    monkeypatch.setattr(api, "_auth_owner_user_id", lambda request: "owner-62b")
    return TestClient(api.app)


def _post_state(client: TestClient, payload: dict) -> dict:
    response = client.post("/planning/saved-scan/phase56a-scan/state", json=payload)
    assert response.status_code == 200
    return response.json()


def test_default_off_api_readback_does_not_capture_operator_decisions(monkeypatch):
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
            "verified_artifact_operator_decision_packet_id": "phase61-packet",
            "verified_artifact_operator_decision_artifact_id": "phase59-artifact",
            "verified_artifact_operator_decision_value": "accepted",
        },
    )
    readback = payload["verified_artifact_operator_decision_readback"]

    assert calls == []
    assert readback["operator_decision_enabled"] is False
    assert readback["operator_decision_requested"] is False
    assert readback["operator_decision_captured"] is False
    assert readback["validation_status"] == "disabled"
    assert readback["readback_phase"] == "62B"
    assert readback["phase62b_readback_hardened"] is True


def test_enabled_api_readback_exposes_operator_decision_observability_fields(
    monkeypatch,
):
    review = _operator_review_packet_readback(monkeypatch)

    readback = services._planning_workspace_verified_artifact_operator_decision_capture_payload(
        operator_review_packet_readback=review,
        enabled=True,
        operator_review_packet_id=review["operator_review_packet_id"],
        artifact_id=review["artifact_id"],
        decision_value="accepted",
    )
    metadata = readback["operator_decision_metadata"]

    assert readback["readback_phase"] == "62B"
    assert readback["phase62b_readback_hardened"] is True
    assert readback["operator_decision_enabled"] is True
    assert readback["operator_decision_requested"] is True
    assert readback["operator_decision_captured"] is True
    assert readback["operator_decision_value"] == "accepted"
    assert readback["operator_decision_id"] == readback["stable_decision_key"]
    assert readback["operator_review_packet_id"] == review["operator_review_packet_id"]
    assert readback["artifact_id"] == review["artifact_id"]
    assert readback["artifact_verification_passed"] is True
    assert readback["validation_status"] == "valid"
    assert readback["fallback_used"] is False
    assert readback["source_resume_unchanged"] is True
    assert readback["source_resume_overwritten"] is False
    assert metadata["phase62b_readback_hardened"] is True
    assert metadata["operator_decision_id"] == readback["operator_decision_id"]
    assert "operator_decision_metadata" in readback["api_readback_fields"]
    assert "phase62b_readback_hardened" in readback["ui_readback_fields"]


def test_valid_review_packet_metadata_and_decision_show_in_planning_api(monkeypatch):
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
    packet_id = third["verified_artifact_operator_review_packet_readback"][
        "operator_review_packet_id"
    ]
    fourth = _post_state(
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
            "enable_verified_artifact_operator_decision_capture": True,
            "verified_artifact_operator_decision_packet_id": packet_id,
            "verified_artifact_operator_decision_artifact_id": artifact_id,
            "verified_artifact_operator_decision_value": "needs_changes",
        },
    )
    readback = fourth["verified_artifact_operator_decision_readback"]

    assert readback["operator_decision_captured"] is True
    assert readback["operator_decision_value"] == "needs_changes"
    assert readback["operator_decision_metadata"]["validation_status"] == "valid"
    assert readback["operator_decision_metadata"]["operator_review_packet_id"] == packet_id
    assert readback["operator_decision_metadata"]["artifact_id"] == artifact_id


def test_missing_and_invalid_review_packet_ids_expose_fallback_metadata(monkeypatch):
    review = _operator_review_packet_readback(monkeypatch)

    missing = services._planning_workspace_verified_artifact_operator_decision_capture_payload(
        operator_review_packet_readback=review,
        enabled=True,
        operator_review_packet_id="",
        artifact_id=review["artifact_id"],
        decision_value="accepted",
    )
    invalid = services._planning_workspace_verified_artifact_operator_decision_capture_payload(
        operator_review_packet_readback=review,
        enabled=True,
        operator_review_packet_id="not-the-packet",
        artifact_id=review["artifact_id"],
        decision_value="accepted",
    )

    assert missing["operator_decision_captured"] is False
    assert missing["fallback_reason"] == "operator_review_packet_id_required"
    assert missing["fallback_metadata"]["fallback_error_class"] == "ValueError"
    assert missing["operator_decision_metadata"]["fallback_reason"] == (
        "operator_review_packet_id_required"
    )
    assert invalid["operator_decision_captured"] is False
    assert invalid["fallback_reason"] == "operator_review_packet_id_mismatch"
    assert invalid["operator_decision_metadata"]["fallback_reason"] == (
        "operator_review_packet_id_mismatch"
    )


def test_invalid_decision_values_expose_fallback_metadata(monkeypatch):
    review = _operator_review_packet_readback(monkeypatch)

    missing = services._planning_workspace_verified_artifact_operator_decision_capture_payload(
        operator_review_packet_readback=review,
        enabled=True,
        operator_review_packet_id=review["operator_review_packet_id"],
        artifact_id=review["artifact_id"],
        decision_value="",
    )
    invalid = services._planning_workspace_verified_artifact_operator_decision_capture_payload(
        operator_review_packet_readback=review,
        enabled=True,
        operator_review_packet_id=review["operator_review_packet_id"],
        artifact_id=review["artifact_id"],
        decision_value="approved",
    )

    assert missing["operator_decision_captured"] is False
    assert missing["fallback_reason"] == "operator_decision_value_required"
    assert missing["operator_decision_metadata"]["fallback_reason"] == (
        "operator_decision_value_required"
    )
    assert invalid["operator_decision_captured"] is False
    assert invalid["fallback_reason"] == "invalid_operator_decision_value"
    assert invalid["operator_decision_metadata"]["operator_decision_value"] == "approved"


def test_ui_readback_display_uses_existing_response_data_and_is_passive():
    script = (ROOT / "src/app/static/scan_workspace.js").read_text(encoding="utf-8")
    getter = script.split(
        "function getScanWorkspaceVerifiedArtifactOperatorDecisionPayload",
        1,
    )[1].split(
        "function renderScanWorkspaceVerifiedArtifactOperatorDecisionReadback",
        1,
    )[0]
    renderer = script.split(
        "function renderScanWorkspaceVerifiedArtifactOperatorDecisionReadback",
        1,
    )[1].split(
        "function getScanWorkspaceHasTailoringPreviewContext",
        1,
    )[0]

    assert "verified_artifact_operator_decision_readback" in getter
    assert "phase62b_readback_hardened" in renderer
    assert "operator_decision_captured" in renderer
    assert "operator_decision_id" in renderer
    assert "operator_review_packet_id" in renderer
    assert "artifact_verification_passed" in renderer
    assert "source_resume_overwritten" in renderer
    assert "_planning_workspace_verified_artifact_operator_decision_capture_payload" not in renderer
    assert "_live_exact_resume_change_proposal_provider_adapter" not in renderer
    assert "fetch(" not in renderer
    assert "postJsonWithTimeout" not in renderer


def test_decision_capture_does_not_create_a_new_artifact(monkeypatch):
    review = _operator_review_packet_readback(monkeypatch)
    packet_before = deepcopy(review["operator_review_packet"])

    readback = services._planning_workspace_verified_artifact_operator_decision_capture_payload(
        operator_review_packet_readback=review,
        enabled=True,
        operator_review_packet_id=review["operator_review_packet_id"],
        artifact_id=review["artifact_id"],
        decision_value="rejected",
    )

    assert review["operator_review_packet"] == packet_before
    assert readback["operator_decision_captured"] is True
    assert readback["safety"]["artifact_created"] is False
    assert readback["safety"]["artifact_created_by_decision_capture"] is False
    assert readback["operator_decision_packet"]["artifact_creation_performed"] is False


def test_source_resume_is_not_overwritten_or_mutated(monkeypatch):
    request = _state_request()
    original = deepcopy(request)
    review = _operator_review_packet_readback(monkeypatch)

    readback = services._planning_workspace_verified_artifact_operator_decision_capture_payload(
        operator_review_packet_readback=review,
        enabled=True,
        operator_review_packet_id=review["operator_review_packet_id"],
        artifact_id=review["artifact_id"],
        decision_value="accepted",
    )

    assert request == original
    assert readback["source_resume_unchanged"] is True
    assert readback["source_resume_overwritten"] is False
    assert readback["safety"]["source_resume_mutated"] is False
    assert readback["safety"]["source_resume_state_mutated"] is False


def test_no_live_llm_or_provider_calls_are_made(monkeypatch):
    provider_calls = []
    review = _operator_review_packet_readback(monkeypatch)
    monkeypatch.setattr(
        services,
        "_live_exact_resume_change_proposal_provider_adapter",
        lambda request: provider_calls.append(request) or _valid_exact_provider_payload(),
    )

    readback = services._planning_workspace_verified_artifact_operator_decision_capture_payload(
        operator_review_packet_readback=review,
        enabled=True,
        operator_review_packet_id=review["operator_review_packet_id"],
        artifact_id=review["artifact_id"],
        decision_value="accepted",
    )

    assert provider_calls == []
    assert readback["safety"]["provider_call_performed"] is False
    assert readback["safety"]["llm_call_performed"] is False
    assert readback["safety"]["network_call_performed"] is False


def test_phase59_60_61_and_62a_readbacks_remain_intact(monkeypatch):
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
    review_payload = services.save_saved_scan_state_payload(
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
    packet_id = review_payload["verified_artifact_operator_review_packet_readback"][
        "operator_review_packet_id"
    ]
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
        enable_verified_artifact_operator_decision_capture=True,
        verified_artifact_operator_decision_packet_id=packet_id,
        verified_artifact_operator_decision_artifact_id=artifact_id,
        verified_artifact_operator_decision_value="accepted",
    )

    assert payload["guarded_resume_copy_artifact_readback"]["readback_phase"] == "59B"
    assert payload["guarded_resume_copy_artifact_verification_readback"]["readback_phase"] == "60B"
    assert payload["verified_artifact_operator_review_packet_readback"]["readback_phase"] == "61B"
    assert payload["verified_artifact_operator_decision_readback"]["phase"] == "62A"
    assert payload["verified_artifact_operator_decision_readback"]["readback_phase"] == "62B"
    assert payload["verified_artifact_operator_decision_readback"][
        "operator_decision_captured"
    ] is True


def test_no_application_execution_submission_or_scoring_changes(monkeypatch):
    review = _operator_review_packet_readback(monkeypatch)
    readback = services._planning_workspace_verified_artifact_operator_decision_capture_payload(
        operator_review_packet_readback=review,
        enabled=True,
        operator_review_packet_id=review["operator_review_packet_id"],
        artifact_id=review["artifact_id"],
        decision_value="accepted",
    )
    safety = readback["safety"]

    assert safety["application_execution_performed"] is False
    assert safety["application_submission_performed"] is False
    assert safety["auto_apply_performed"] is False
    assert safety["auto_submit_performed"] is False
    assert safety["scoring_formula_changed"] is False
    assert safety["scoring_weights_changed"] is False


def test_phase62a_focused_behavior_remains_intact(monkeypatch):
    review = _operator_review_packet_readback(monkeypatch)
    readback = services._planning_workspace_verified_artifact_operator_decision_capture_payload(
        operator_review_packet_readback=review,
        enabled=True,
        operator_review_packet_id=review["operator_review_packet_id"],
        artifact_id=review["artifact_id"],
        decision_value="accepted",
    )

    assert readback["phase"] == "62A"
    assert readback["operator_decision_captured"] is True
    assert readback["operator_decision_packet"]["operator_decision_only"] is True


def test_protected_files_are_unchanged():
    for relative, expected in PROTECTED_HASHES.items():
        assert _sha256(ROOT / relative) == expected


def test_docs_include_phase62b_readback_safety_markers():
    text = DOC_PATH.read_text(encoding="utf-8").lower()
    for marker in (
        "default-off",
        "verified artifact operator decision capture readback",
        "planning workspace action",
        "api readback",
        "deterministic fallback",
        "no live llm call",
        "no artifact creation",
        "no source resume overwrite",
        "no application execution",
        "no auto-apply",
    ):
        assert marker in text
