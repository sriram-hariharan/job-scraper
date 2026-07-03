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
from tests.test_phase61a_verified_artifact_operator_review_packet_wiring_default_off import (
    _verified_artifact_readback,
)


ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = (
    ROOT
    / "docs/phase62_verified_artifact_operator_decision_capture_wiring_default_off.md"
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
    monkeypatch.setattr(api, "_auth_owner_user_id", lambda request: "owner-62a")
    return TestClient(api.app)


def _post_state(client: TestClient, payload: dict) -> dict:
    response = client.post("/planning/saved-scan/phase56a-scan/state", json=payload)
    assert response.status_code == 200
    return response.json()


def _operator_review_packet_readback(monkeypatch) -> dict:
    verification = _verified_artifact_readback(monkeypatch)
    return services._planning_workspace_verified_artifact_operator_review_packet_payload(
        verification_readback=verification,
        enabled=True,
        artifact_id=verification["artifact_id"],
    )


def test_default_off_planning_workspace_action_does_not_capture_operator_decision(
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
        verified_artifact_operator_decision_packet_id="phase61-packet",
        verified_artifact_operator_decision_artifact_id="phase59-artifact",
        verified_artifact_operator_decision_value="accepted",
    )
    readback = payload["verified_artifact_operator_decision_readback"]

    assert calls == []
    assert readback["operator_decision_enabled"] is False
    assert readback["operator_decision_requested"] is False
    assert readback["operator_decision_captured"] is False
    assert readback["operator_decision_id"] == ""
    assert readback["validation_status"] == "disabled"
    assert payload["verified_artifact_operator_review_packet_readback"][
        "operator_review_packet_created"
    ] is False


def test_enabled_action_captures_operator_decision_from_valid_review_packet_only(
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

    assert readback["operator_decision_enabled"] is True
    assert readback["operator_decision_requested"] is True
    assert readback["operator_decision_captured"] is True
    assert readback["operator_decision_value"] == "accepted"
    assert readback["operator_decision_id"].startswith(
        "phase62-verified-artifact-decision-"
    )
    assert readback["stable_decision_key"] == readback["operator_decision_id"]
    assert readback["operator_review_packet_id"] == review["operator_review_packet_id"]
    assert readback["artifact_id"] == review["artifact_id"]
    assert readback["artifact_verification_passed"] is True
    assert readback["validation_status"] == "valid"
    assert readback["fallback_used"] is False
    assert readback["operator_decision_packet"]["operator_decision_only"] is True
    assert readback["operator_decision_packet"]["artifact_creation_performed"] is False


def test_api_captures_operator_decision_from_review_packet(monkeypatch):
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
    assert readback["operator_review_packet_id"] == packet_id
    assert readback["artifact_id"] == artifact_id
    assert "operator_decision_id" in readback["api_readback_fields"]


def test_missing_or_invalid_review_packet_ids_fallback_safely(monkeypatch):
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
    assert invalid["operator_decision_captured"] is False
    assert invalid["fallback_reason"] == "operator_review_packet_id_mismatch"
    assert invalid["source_resume_unchanged"] is True
    assert invalid["source_resume_overwritten"] is False


def test_invalid_decision_values_fallback_safely(monkeypatch):
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
    assert invalid["operator_decision_captured"] is False
    assert invalid["fallback_reason"] == "invalid_operator_decision_value"
    assert invalid["operator_decision_value"] == "approved"


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


def test_phase59_60_and_61_readbacks_remain_intact(monkeypatch):
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
    assert payload["guarded_resume_copy_artifact_verification_readback"]["phase"] == "60A"
    assert payload["verified_artifact_operator_review_packet_readback"]["phase"] == "61A"
    assert payload["verified_artifact_operator_decision_readback"]["phase"] == "62A"
    assert payload["verified_artifact_operator_decision_readback"][
        "operator_decision_captured"
    ] is True


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
    assert "enable_verified_artifact_operator_decision_capture" in script
    assert "verified_artifact_operator_decision_packet_id" in script
    assert "verified_artifact_operator_decision_artifact_id" in script
    assert "verified_artifact_operator_decision_value" in script
    assert "operator_decision_captured" in renderer
    assert "artifact_verification_passed" in renderer
    assert "source_resume_overwritten" in renderer
    assert "_live_exact_resume_change_proposal_provider_adapter" not in renderer
    assert "fetch(" not in renderer
    assert "postJsonWithTimeout" not in renderer


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


def test_protected_files_are_unchanged():
    for relative, expected in PROTECTED_HASHES.items():
        assert _sha256(ROOT / relative) == expected


def test_docs_include_phase62a_operator_decision_safety_markers():
    text = DOC_PATH.read_text(encoding="utf-8").lower()
    for marker in (
        "default-off",
        "verified artifact operator decision capture",
        "planning workspace action",
        "deterministic fallback",
        "no live llm call",
        "no artifact creation",
        "no source resume overwrite",
        "no application execution",
        "no auto-apply",
    ):
        assert marker in text
