from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from pathlib import Path

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
from tests.test_phase63a_operator_approved_artifact_application_readiness_packet_wiring_default_off import (
    PROTECTED_HASHES,
    _client,
    _operator_decision_readback,
    _post_state,
)


ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = ROOT / "docs/phase64_human_only_manual_application_handoff_packet_wiring_default_off.md"


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _readiness_readback(monkeypatch, *, decision_value: str = "accepted") -> dict:
    decision = _operator_decision_readback(monkeypatch, decision_value=decision_value)
    return services._planning_workspace_operator_approved_artifact_application_readiness_packet_payload(
        operator_decision_readback=decision,
        enabled=True,
        operator_decision_id=decision["operator_decision_id"],
        operator_review_packet_id=decision["operator_review_packet_id"],
        artifact_id=decision["artifact_id"],
    )


def test_default_off_planning_workspace_action_does_not_create_manual_handoff_packet(
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
        manual_handoff_application_readiness_packet_id="phase63-readiness",
        manual_handoff_artifact_id="phase59-artifact",
    )
    readback = payload["human_only_manual_application_handoff_packet_readback"]

    assert calls == []
    assert readback["manual_handoff_packet_enabled"] is False
    assert readback["manual_handoff_packet_requested"] is False
    assert readback["manual_handoff_packet_created"] is False
    assert readback["manual_handoff_packet_id"] == ""
    assert readback["validation_status"] == "disabled"
    assert readback["human_only_application_boundary"] is True
    assert payload["operator_approved_artifact_application_readiness_packet_readback"][
        "application_readiness_packet_created"
    ] is False


def test_enabled_action_creates_human_only_handoff_packet_from_valid_readiness_packet(
    monkeypatch,
):
    readiness = _readiness_readback(monkeypatch)

    readback = services._planning_workspace_human_only_manual_application_handoff_packet_payload(
        application_readiness_readback=readiness,
        enabled=True,
        application_readiness_packet_id=readiness["application_readiness_packet_id"],
        artifact_id=readiness["artifact_id"],
    )

    assert readback["phase"] == "64A"
    assert readback["manual_handoff_packet_enabled"] is True
    assert readback["manual_handoff_packet_requested"] is True
    assert readback["manual_handoff_packet_created"] is True
    assert readback["manual_handoff_packet_id"].startswith("phase64-manual-handoff-")
    assert readback["application_readiness_packet_id"] == readiness[
        "application_readiness_packet_id"
    ]
    assert readback["artifact_id"] == readiness["artifact_id"]
    assert readback["operator_decision_value"] == "accepted"
    assert readback["human_only_application_boundary"] is True
    assert readback["ats_automation_performed"] is False
    assert readback["application_submission_performed"] is False
    assert readback["apply_queue_enqueued"] is False
    assert readback["validation_status"] == "valid"
    assert readback["fallback_used"] is False
    assert readback["source_resume_unchanged"] is True
    assert readback["source_resume_overwritten"] is False
    assert readback["manual_handoff_packet"]["resume_artifact_creation_performed"] is False


def test_missing_or_invalid_readiness_packet_ids_fallback_safely(monkeypatch):
    readiness = _readiness_readback(monkeypatch)

    missing = services._planning_workspace_human_only_manual_application_handoff_packet_payload(
        application_readiness_readback=readiness,
        enabled=True,
        application_readiness_packet_id="",
        artifact_id=readiness["artifact_id"],
    )
    invalid = services._planning_workspace_human_only_manual_application_handoff_packet_payload(
        application_readiness_readback=readiness,
        enabled=True,
        application_readiness_packet_id="not-the-readiness-packet",
        artifact_id=readiness["artifact_id"],
    )

    assert missing["manual_handoff_packet_created"] is False
    assert missing["fallback_reason"] == "application_readiness_packet_id_required"
    assert missing["fallback_metadata"]["fallback_error_class"] == "ValueError"
    assert invalid["manual_handoff_packet_created"] is False
    assert invalid["fallback_reason"] == "application_readiness_packet_id_mismatch"
    assert invalid["source_resume_unchanged"] is True
    assert invalid["source_resume_overwritten"] is False


def test_uncreated_or_unaccepted_readiness_packets_do_not_create_handoff(monkeypatch):
    disabled = services.build_planning_workspace_operator_approved_artifact_application_readiness_packet_readback(
        {
            "fallback_used": True,
            "validation_status": "fallback",
            "application_readiness_packet_requested": True,
            "application_readiness_packet_created": False,
            "application_readiness_packet_id": "phase63-disabled",
            "operator_decision_value": "accepted",
            "artifact_id": "phase59-artifact",
        },
        enabled=True,
    )
    rejected = _readiness_readback(monkeypatch, decision_value="rejected")

    disabled_readback = services._planning_workspace_human_only_manual_application_handoff_packet_payload(
        application_readiness_readback=disabled,
        enabled=True,
        application_readiness_packet_id="phase63-disabled",
        artifact_id="phase59-artifact",
    )
    rejected_readback = services._planning_workspace_human_only_manual_application_handoff_packet_payload(
        application_readiness_readback=rejected,
        enabled=True,
        application_readiness_packet_id=rejected["application_readiness_packet_id"],
        artifact_id=rejected["artifact_id"],
    )

    assert disabled_readback["manual_handoff_packet_created"] is False
    assert disabled_readback["fallback_reason"] == "application_readiness_packet_required"
    assert rejected_readback["manual_handoff_packet_created"] is False
    assert rejected_readback["fallback_reason"] in {
        "application_readiness_packet_id_required",
        "application_readiness_packet_required",
        "operator_decision_not_accepted",
    }


def test_api_creates_manual_handoff_packet_from_valid_readiness_packet(monkeypatch):
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
    readiness_id = fifth[
        "operator_approved_artifact_application_readiness_packet_readback"
    ]["application_readiness_packet_id"]
    sixth = _post_state(
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
            "enable_human_only_manual_application_handoff_packet": True,
            "manual_handoff_application_readiness_packet_id": readiness_id,
            "manual_handoff_artifact_id": artifact_id,
        },
    )
    readback = sixth["human_only_manual_application_handoff_packet_readback"]

    assert readback["manual_handoff_packet_created"] is True
    assert readback["application_readiness_packet_id"] == readiness_id
    assert readback["artifact_id"] == artifact_id
    assert readback["human_only_application_boundary"] is True
    assert readback["ats_automation_performed"] is False
    assert readback["application_submission_performed"] is False
    assert readback["apply_queue_enqueued"] is False


def test_handoff_packet_creation_does_not_create_artifact_or_mutate_resume(monkeypatch):
    request = _state_request()
    original_request = deepcopy(request)
    readiness = _readiness_readback(monkeypatch)
    original_readiness_packet = deepcopy(readiness["application_readiness_packet"])

    readback = services._planning_workspace_human_only_manual_application_handoff_packet_payload(
        application_readiness_readback=readiness,
        enabled=True,
        application_readiness_packet_id=readiness["application_readiness_packet_id"],
        artifact_id=readiness["artifact_id"],
    )

    assert request == original_request
    assert readiness["application_readiness_packet"] == original_readiness_packet
    assert readback["manual_handoff_packet_created"] is True
    assert readback["manual_handoff_packet"]["resume_artifact_creation_performed"] is False
    assert readback["safety"]["resume_artifact_created"] is False
    assert readback["safety"]["artifact_created"] is False
    assert readback["safety"]["source_resume_mutated"] is False
    assert readback["safety"]["source_resume_state_mutated"] is False
    assert readback["source_resume_unchanged"] is True
    assert readback["source_resume_overwritten"] is False


def test_no_live_llm_provider_ats_submission_or_apply_queue_enqueue(monkeypatch):
    provider_calls = []
    readiness = _readiness_readback(monkeypatch)
    monkeypatch.setattr(
        services,
        "_live_exact_resume_change_proposal_provider_adapter",
        lambda request: provider_calls.append(request) or _valid_exact_provider_payload(),
    )

    readback = services._planning_workspace_human_only_manual_application_handoff_packet_payload(
        application_readiness_readback=readiness,
        enabled=True,
        application_readiness_packet_id=readiness["application_readiness_packet_id"],
        artifact_id=readiness["artifact_id"],
    )
    safety = readback["safety"]

    assert provider_calls == []
    assert safety["provider_call_performed"] is False
    assert safety["llm_call_performed"] is False
    assert safety["network_call_performed"] is False
    assert safety["ats_automation_performed"] is False
    assert safety["apply_queue_enqueued"] is False
    assert safety["application_execution_enqueued"] is False
    assert safety["application_execution_performed"] is False
    assert safety["application_submission_performed"] is False
    assert readback["ats_automation_performed"] is False
    assert readback["application_submission_performed"] is False
    assert readback["apply_queue_enqueued"] is False


def test_phase60_61_62_and_63_readbacks_remain_intact(monkeypatch):
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
    readiness_payload = services.save_saved_scan_state_payload(
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
    readiness_id = readiness_payload[
        "operator_approved_artifact_application_readiness_packet_readback"
    ]["application_readiness_packet_id"]
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
        enable_human_only_manual_application_handoff_packet=True,
        manual_handoff_application_readiness_packet_id=readiness_id,
        manual_handoff_artifact_id=artifact_id,
    )

    assert payload["guarded_resume_copy_artifact_verification_readback"]["readback_phase"] == "60B"
    assert payload["verified_artifact_operator_review_packet_readback"]["readback_phase"] == "61B"
    assert payload["verified_artifact_operator_decision_readback"]["readback_phase"] == "62B"
    readiness = payload[
        "operator_approved_artifact_application_readiness_packet_readback"
    ]
    assert readiness["phase"] == "63A"
    assert readiness["readback_phase"] == "63B"
    assert payload["human_only_manual_application_handoff_packet_readback"][
        "phase"
    ] == "64A"


def test_ui_readback_display_uses_existing_response_data_and_is_passive():
    script = (ROOT / "src/app/static/scan_workspace.js").read_text(encoding="utf-8")
    getter = script.split(
        "function getScanWorkspaceManualApplicationHandoffPacketPayload",
        1,
    )[1].split(
        "function renderScanWorkspaceManualApplicationHandoffPacketReadback",
        1,
    )[0]
    renderer = script.split(
        "function renderScanWorkspaceManualApplicationHandoffPacketReadback",
        1,
    )[1].split(
        "function getScanWorkspaceHasTailoringPreviewContext",
        1,
    )[0]

    assert "human_only_manual_application_handoff_packet_readback" in getter
    assert "enable_human_only_manual_application_handoff_packet" in script
    assert "manual_handoff_application_readiness_packet_id" in script
    assert "manual_handoff_artifact_id" in script
    assert "manual_handoff_packet_created" in renderer
    assert "human_only_application_boundary" in renderer
    assert "ats_automation_performed" in renderer
    assert "application_submission_performed" in renderer
    assert "apply_queue_enqueued" in renderer
    assert "_planning_workspace_human_only_manual_application_handoff_packet_payload" not in renderer
    assert "_live_exact_resume_change_proposal_provider_adapter" not in renderer
    assert "fetch(" not in renderer
    assert "postJsonWithTimeout" not in renderer


def test_no_scoring_formula_or_weight_changes(monkeypatch):
    readiness = _readiness_readback(monkeypatch)
    readback = services._planning_workspace_human_only_manual_application_handoff_packet_payload(
        application_readiness_readback=readiness,
        enabled=True,
        application_readiness_packet_id=readiness["application_readiness_packet_id"],
        artifact_id=readiness["artifact_id"],
    )

    assert readback["safety"]["scoring_formula_changed"] is False
    assert readback["safety"]["scoring_weights_changed"] is False
    assert readback["safety"]["auto_apply_performed"] is False
    assert readback["safety"]["auto_submit_performed"] is False


def test_protected_files_are_unchanged():
    for relative, expected in PROTECTED_HASHES.items():
        assert _sha256(ROOT / relative) == expected


def test_docs_include_phase64a_human_only_handoff_safety_markers():
    text = DOC_PATH.read_text(encoding="utf-8").lower()
    for marker in (
        "default-off",
        "human-only manual application handoff packet",
        "planning workspace action",
        "deterministic fallback",
        "no live llm call",
        "no resume artifact creation",
        "no source resume overwrite",
        "no ats automation",
        "no application submission",
        "no auto-apply",
    ):
        assert marker in text
