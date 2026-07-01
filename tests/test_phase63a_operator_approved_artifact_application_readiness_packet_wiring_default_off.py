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
    / "docs/phase63_operator_approved_artifact_application_readiness_packet_wiring_default_off.md"
)
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
    monkeypatch.setattr(api, "_auth_owner_user_id", lambda request: "owner-63a")
    return TestClient(api.app)


def _post_state(client: TestClient, payload: dict) -> dict:
    response = client.post("/planning/saved-scan/phase56a-scan/state", json=payload)
    assert response.status_code == 200
    return response.json()


def _operator_decision_readback(monkeypatch, *, decision_value: str = "accepted") -> dict:
    review = _operator_review_packet_readback(monkeypatch)
    return services._planning_workspace_verified_artifact_operator_decision_capture_payload(
        operator_review_packet_readback=review,
        enabled=True,
        operator_review_packet_id=review["operator_review_packet_id"],
        artifact_id=review["artifact_id"],
        decision_value=decision_value,
    )


def test_default_off_planning_workspace_action_does_not_create_readiness_packet(
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
        application_readiness_operator_decision_id="phase62-decision",
        application_readiness_operator_review_packet_id="phase61-packet",
        application_readiness_artifact_id="phase59-artifact",
    )
    readback = payload[
        "operator_approved_artifact_application_readiness_packet_readback"
    ]

    assert calls == []
    assert readback["application_readiness_packet_enabled"] is False
    assert readback["application_readiness_packet_requested"] is False
    assert readback["application_readiness_packet_created"] is False
    assert readback["application_readiness_packet_id"] == ""
    assert readback["validation_status"] == "disabled"
    assert payload["verified_artifact_operator_decision_readback"][
        "operator_decision_captured"
    ] is False


def test_enabled_action_creates_readiness_packet_from_accepted_decision_only(
    monkeypatch,
):
    decision = _operator_decision_readback(monkeypatch, decision_value="accepted")

    readback = services._planning_workspace_operator_approved_artifact_application_readiness_packet_payload(
        operator_decision_readback=decision,
        enabled=True,
        operator_decision_id=decision["operator_decision_id"],
        operator_review_packet_id=decision["operator_review_packet_id"],
        artifact_id=decision["artifact_id"],
    )

    assert readback["application_readiness_packet_enabled"] is True
    assert readback["application_readiness_packet_requested"] is True
    assert readback["application_readiness_packet_created"] is True
    assert readback["application_readiness_packet_id"].startswith(
        "phase63-application-readiness-"
    )
    assert readback["operator_decision_id"] == decision["operator_decision_id"]
    assert readback["operator_decision_value"] == "accepted"
    assert readback["operator_review_packet_id"] == decision["operator_review_packet_id"]
    assert readback["artifact_id"] == decision["artifact_id"]
    assert readback["artifact_verification_passed"] is True
    assert readback["readiness_item_count"] == 1
    assert readback["validation_status"] == "valid"
    assert readback["fallback_used"] is False
    assert readback["application_execution_enqueued"] is False
    assert readback["application_execution_performed"] is False
    assert readback["application_submission_performed"] is False
    assert readback["application_readiness_packet"]["manual_application_review_only"] is True


def test_rejected_or_needs_changes_decisions_do_not_create_readiness_packets(
    monkeypatch,
):
    rejected = _operator_decision_readback(monkeypatch, decision_value="rejected")
    needs_changes = _operator_decision_readback(monkeypatch, decision_value="needs_changes")

    rejected_readback = services._planning_workspace_operator_approved_artifact_application_readiness_packet_payload(
        operator_decision_readback=rejected,
        enabled=True,
        operator_decision_id=rejected["operator_decision_id"],
        operator_review_packet_id=rejected["operator_review_packet_id"],
        artifact_id=rejected["artifact_id"],
    )
    needs_changes_readback = services._planning_workspace_operator_approved_artifact_application_readiness_packet_payload(
        operator_decision_readback=needs_changes,
        enabled=True,
        operator_decision_id=needs_changes["operator_decision_id"],
        operator_review_packet_id=needs_changes["operator_review_packet_id"],
        artifact_id=needs_changes["artifact_id"],
    )

    assert rejected_readback["application_readiness_packet_created"] is False
    assert rejected_readback["fallback_reason"] == "operator_decision_not_accepted"
    assert rejected_readback["operator_decision_value"] == "rejected"
    assert needs_changes_readback["application_readiness_packet_created"] is False
    assert needs_changes_readback["fallback_reason"] == "operator_decision_not_accepted"
    assert needs_changes_readback["operator_decision_value"] == "needs_changes"


def test_missing_or_invalid_operator_decision_ids_fallback_safely(monkeypatch):
    decision = _operator_decision_readback(monkeypatch)

    missing = services._planning_workspace_operator_approved_artifact_application_readiness_packet_payload(
        operator_decision_readback=decision,
        enabled=True,
        operator_decision_id="",
        operator_review_packet_id=decision["operator_review_packet_id"],
        artifact_id=decision["artifact_id"],
    )
    invalid = services._planning_workspace_operator_approved_artifact_application_readiness_packet_payload(
        operator_decision_readback=decision,
        enabled=True,
        operator_decision_id="not-the-decision",
        operator_review_packet_id=decision["operator_review_packet_id"],
        artifact_id=decision["artifact_id"],
    )

    assert missing["application_readiness_packet_created"] is False
    assert missing["fallback_reason"] == "operator_decision_id_required"
    assert missing["fallback_metadata"]["fallback_error_class"] == "ValueError"
    assert invalid["application_readiness_packet_created"] is False
    assert invalid["fallback_reason"] == "operator_decision_id_mismatch"
    assert invalid["source_resume_unchanged"] is True
    assert invalid["source_resume_overwritten"] is False


def test_api_creates_readiness_packet_from_accepted_operator_decision(monkeypatch):
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
    review_packet_id = third["verified_artifact_operator_review_packet_readback"][
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
            "verified_artifact_operator_decision_packet_id": review_packet_id,
            "verified_artifact_operator_decision_artifact_id": artifact_id,
            "verified_artifact_operator_decision_value": "accepted",
        },
    )
    decision_id = fourth["verified_artifact_operator_decision_readback"][
        "operator_decision_id"
    ]
    fifth = _post_state(
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
            "verified_artifact_operator_decision_packet_id": review_packet_id,
            "verified_artifact_operator_decision_artifact_id": artifact_id,
            "verified_artifact_operator_decision_value": "accepted",
            "enable_operator_approved_artifact_application_readiness_packet": True,
            "application_readiness_operator_decision_id": decision_id,
            "application_readiness_operator_review_packet_id": review_packet_id,
            "application_readiness_artifact_id": artifact_id,
        },
    )
    readback = fifth[
        "operator_approved_artifact_application_readiness_packet_readback"
    ]

    assert readback["application_readiness_packet_created"] is True
    assert readback["operator_decision_id"] == decision_id
    assert readback["operator_decision_value"] == "accepted"
    assert readback["operator_review_packet_id"] == review_packet_id
    assert readback["artifact_id"] == artifact_id
    assert "application_readiness_packet_id" in readback["api_readback_fields"]


def test_readiness_packet_creation_does_not_create_a_new_artifact(monkeypatch):
    decision = _operator_decision_readback(monkeypatch)
    decision_packet_before = deepcopy(decision["operator_decision_packet"])

    readback = services._planning_workspace_operator_approved_artifact_application_readiness_packet_payload(
        operator_decision_readback=decision,
        enabled=True,
        operator_decision_id=decision["operator_decision_id"],
        operator_review_packet_id=decision["operator_review_packet_id"],
        artifact_id=decision["artifact_id"],
    )

    assert decision["operator_decision_packet"] == decision_packet_before
    assert readback["application_readiness_packet_created"] is True
    assert readback["safety"]["artifact_created"] is False
    assert readback["safety"]["artifact_created_by_application_readiness"] is False
    assert readback["application_readiness_packet"]["artifact_creation_performed"] is False


def test_source_resume_is_not_overwritten_or_mutated(monkeypatch):
    request = _state_request()
    original = deepcopy(request)
    decision = _operator_decision_readback(monkeypatch)

    readback = services._planning_workspace_operator_approved_artifact_application_readiness_packet_payload(
        operator_decision_readback=decision,
        enabled=True,
        operator_decision_id=decision["operator_decision_id"],
        operator_review_packet_id=decision["operator_review_packet_id"],
        artifact_id=decision["artifact_id"],
    )

    assert request == original
    assert readback["source_resume_unchanged"] is True
    assert readback["source_resume_overwritten"] is False
    assert readback["safety"]["source_resume_mutated"] is False
    assert readback["safety"]["source_resume_state_mutated"] is False


def test_no_live_llm_provider_execution_submission_or_enqueue(monkeypatch):
    provider_calls = []
    decision = _operator_decision_readback(monkeypatch)
    monkeypatch.setattr(
        services,
        "_live_exact_resume_change_proposal_provider_adapter",
        lambda request: provider_calls.append(request) or _valid_exact_provider_payload(),
    )

    readback = services._planning_workspace_operator_approved_artifact_application_readiness_packet_payload(
        operator_decision_readback=decision,
        enabled=True,
        operator_decision_id=decision["operator_decision_id"],
        operator_review_packet_id=decision["operator_review_packet_id"],
        artifact_id=decision["artifact_id"],
    )
    safety = readback["safety"]

    assert provider_calls == []
    assert safety["provider_call_performed"] is False
    assert safety["llm_call_performed"] is False
    assert safety["network_call_performed"] is False
    assert safety["application_execution_enqueued"] is False
    assert safety["application_execution_performed"] is False
    assert safety["application_submission_performed"] is False
    assert readback["application_execution_enqueued"] is False
    assert readback["application_execution_performed"] is False
    assert readback["application_submission_performed"] is False


def test_phase59_60_61_and_62_readbacks_remain_intact(monkeypatch):
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
    review_packet_id = review_payload["verified_artifact_operator_review_packet_readback"][
        "operator_review_packet_id"
    ]
    decision_payload = services.save_saved_scan_state_payload(
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
        verified_artifact_operator_decision_packet_id=review_packet_id,
        verified_artifact_operator_decision_artifact_id=artifact_id,
        verified_artifact_operator_decision_value="accepted",
    )
    decision_id = decision_payload["verified_artifact_operator_decision_readback"][
        "operator_decision_id"
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
        verified_artifact_operator_decision_packet_id=review_packet_id,
        verified_artifact_operator_decision_artifact_id=artifact_id,
        verified_artifact_operator_decision_value="accepted",
        enable_operator_approved_artifact_application_readiness_packet=True,
        application_readiness_operator_decision_id=decision_id,
        application_readiness_operator_review_packet_id=review_packet_id,
        application_readiness_artifact_id=artifact_id,
    )

    assert payload["guarded_resume_copy_artifact_readback"]["readback_phase"] == "59B"
    assert payload["guarded_resume_copy_artifact_verification_readback"]["readback_phase"] == "60B"
    assert payload["verified_artifact_operator_review_packet_readback"]["readback_phase"] == "61B"
    assert payload["verified_artifact_operator_decision_readback"]["readback_phase"] == "62B"
    assert payload["operator_approved_artifact_application_readiness_packet_readback"][
        "phase"
    ] == "63A"


def test_ui_readback_display_uses_existing_response_data_and_is_passive():
    script = (ROOT / "src/app/static/scan_workspace.js").read_text(encoding="utf-8")
    getter = script.split(
        "function getScanWorkspaceApplicationReadinessPacketPayload",
        1,
    )[1].split(
        "function renderScanWorkspaceApplicationReadinessPacketReadback",
        1,
    )[0]
    renderer = script.split(
        "function renderScanWorkspaceApplicationReadinessPacketReadback",
        1,
    )[1].split(
        "function getScanWorkspaceHasTailoringPreviewContext",
        1,
    )[0]

    assert "operator_approved_artifact_application_readiness_packet_readback" in getter
    assert "enable_operator_approved_artifact_application_readiness_packet" in script
    assert "application_readiness_operator_decision_id" in script
    assert "application_readiness_operator_review_packet_id" in script
    assert "application_readiness_artifact_id" in script
    assert "application_readiness_packet_created" in renderer
    assert "application_execution_enqueued" in renderer
    assert "application_submission_performed" in renderer
    assert "_planning_workspace_operator_approved_artifact_application_readiness_packet_payload" not in renderer
    assert "_live_exact_resume_change_proposal_provider_adapter" not in renderer
    assert "fetch(" not in renderer
    assert "postJsonWithTimeout" not in renderer


def test_no_scoring_formula_or_weight_changes(monkeypatch):
    decision = _operator_decision_readback(monkeypatch)
    readback = services._planning_workspace_operator_approved_artifact_application_readiness_packet_payload(
        operator_decision_readback=decision,
        enabled=True,
        operator_decision_id=decision["operator_decision_id"],
        operator_review_packet_id=decision["operator_review_packet_id"],
        artifact_id=decision["artifact_id"],
    )

    assert readback["safety"]["scoring_formula_changed"] is False
    assert readback["safety"]["scoring_weights_changed"] is False
    assert readback["safety"]["auto_apply_performed"] is False
    assert readback["safety"]["auto_submit_performed"] is False


def test_protected_files_are_unchanged():
    for relative, expected in PROTECTED_HASHES.items():
        assert _sha256(ROOT / relative) == expected


def test_docs_include_phase63a_readiness_packet_safety_markers():
    text = DOC_PATH.read_text(encoding="utf-8").lower()
    for marker in (
        "default-off",
        "operator-approved artifact application-readiness packet",
        "planning workspace action",
        "deterministic fallback",
        "no live llm call",
        "no artifact creation",
        "no source resume overwrite",
        "no application execution",
        "no application submission",
        "no auto-apply",
    ):
        assert marker in text
