from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from src.app import services
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
from tests.test_phase64a_human_only_manual_application_handoff_packet_wiring_default_off import (
    PROTECTED_HASHES,
    _readiness_readback,
)


ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = ROOT / "docs/phase65_human_only_handoff_audit_trail_wiring_default_off.md"


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _manual_handoff_readback(monkeypatch) -> dict:
    readiness = _readiness_readback(monkeypatch)
    return services._planning_workspace_human_only_manual_application_handoff_packet_payload(
        application_readiness_readback=readiness,
        enabled=True,
        application_readiness_packet_id=readiness["application_readiness_packet_id"],
        artifact_id=readiness["artifact_id"],
    )


def test_default_off_planning_workspace_action_does_not_create_handoff_audit_trail(
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
        handoff_audit_manual_handoff_packet_id="phase64-handoff",
        handoff_audit_application_readiness_packet_id="phase63-readiness",
        handoff_audit_artifact_id="phase59-artifact",
    )
    readback = payload["human_only_handoff_audit_trail_readback"]

    assert calls == []
    assert readback["handoff_audit_trail_enabled"] is False
    assert readback["handoff_audit_trail_requested"] is False
    assert readback["handoff_audit_trail_created"] is False
    assert readback["handoff_audit_trail_id"] == ""
    assert readback["validation_status"] == "disabled"
    assert readback["human_only_application_boundary"] is True
    assert payload["human_only_manual_application_handoff_packet_readback"][
        "manual_handoff_packet_created"
    ] is False


def test_enabled_action_creates_human_only_handoff_audit_from_valid_handoff_packet(
    monkeypatch,
):
    handoff = _manual_handoff_readback(monkeypatch)

    readback = services._planning_workspace_human_only_handoff_audit_trail_payload(
        manual_handoff_readback=handoff,
        enabled=True,
        manual_handoff_packet_id=handoff["manual_handoff_packet_id"],
        application_readiness_packet_id=handoff["application_readiness_packet_id"],
        artifact_id=handoff["artifact_id"],
    )

    assert readback["phase"] == "65A"
    assert readback["handoff_audit_trail_enabled"] is True
    assert readback["handoff_audit_trail_requested"] is True
    assert readback["handoff_audit_trail_created"] is True
    assert readback["handoff_audit_trail_id"].startswith("phase65-handoff-audit-")
    assert readback["manual_handoff_packet_id"] == handoff["manual_handoff_packet_id"]
    assert readback["application_readiness_packet_id"] == handoff[
        "application_readiness_packet_id"
    ]
    assert readback["artifact_id"] == handoff["artifact_id"]
    assert readback["human_only_application_boundary"] is True
    assert readback["audit_event_count"] == 3
    assert readback["ats_automation_performed"] is False
    assert readback["application_submission_performed"] is False
    assert readback["apply_queue_enqueued"] is False
    assert readback["validation_status"] == "valid"
    assert readback["fallback_used"] is False
    assert readback["source_resume_unchanged"] is True
    assert readback["source_resume_overwritten"] is False
    assert readback["handoff_audit_trail"]["resume_artifact_creation_performed"] is False


def test_missing_or_invalid_handoff_packet_ids_fallback_safely(monkeypatch):
    handoff = _manual_handoff_readback(monkeypatch)

    missing = services._planning_workspace_human_only_handoff_audit_trail_payload(
        manual_handoff_readback=handoff,
        enabled=True,
        manual_handoff_packet_id="",
        application_readiness_packet_id=handoff["application_readiness_packet_id"],
        artifact_id=handoff["artifact_id"],
    )
    invalid = services._planning_workspace_human_only_handoff_audit_trail_payload(
        manual_handoff_readback=handoff,
        enabled=True,
        manual_handoff_packet_id="not-the-handoff-packet",
        application_readiness_packet_id=handoff["application_readiness_packet_id"],
        artifact_id=handoff["artifact_id"],
    )

    assert missing["handoff_audit_trail_created"] is False
    assert missing["fallback_reason"] == "manual_handoff_packet_id_required"
    assert missing["fallback_metadata"]["fallback_error_class"] == "ValueError"
    assert invalid["handoff_audit_trail_created"] is False
    assert invalid["fallback_reason"] == "manual_handoff_packet_id_mismatch"
    assert invalid["source_resume_unchanged"] is True
    assert invalid["source_resume_overwritten"] is False


def test_invalid_optional_readiness_or_artifact_ids_fallback_safely(monkeypatch):
    handoff = _manual_handoff_readback(monkeypatch)

    bad_readiness = services._planning_workspace_human_only_handoff_audit_trail_payload(
        manual_handoff_readback=handoff,
        enabled=True,
        manual_handoff_packet_id=handoff["manual_handoff_packet_id"],
        application_readiness_packet_id="not-the-readiness",
        artifact_id=handoff["artifact_id"],
    )
    bad_artifact = services._planning_workspace_human_only_handoff_audit_trail_payload(
        manual_handoff_readback=handoff,
        enabled=True,
        manual_handoff_packet_id=handoff["manual_handoff_packet_id"],
        application_readiness_packet_id=handoff["application_readiness_packet_id"],
        artifact_id="not-the-artifact",
    )

    assert bad_readiness["handoff_audit_trail_created"] is False
    assert bad_readiness["fallback_reason"] == "application_readiness_packet_id_mismatch"
    assert bad_artifact["handoff_audit_trail_created"] is False
    assert bad_artifact["fallback_reason"] == "artifact_id_mismatch"


def test_uncreated_or_non_human_only_handoff_does_not_create_audit_trail():
    uncreated = services.build_planning_workspace_human_only_manual_application_handoff_packet_readback(
        {
            "fallback_used": True,
            "validation_status": "fallback",
            "manual_handoff_packet_requested": True,
            "manual_handoff_packet_created": False,
            "manual_handoff_packet_id": "phase64-uncreated",
            "application_readiness_packet_id": "phase63-readiness",
            "artifact_id": "phase59-artifact",
        },
        enabled=True,
    )
    non_human_only = {
        **services.build_planning_workspace_human_only_manual_application_handoff_packet_readback(
            {
                "fallback_used": False,
                "validation_status": "valid",
                "manual_handoff_packet_requested": True,
                "manual_handoff_packet_created": True,
                "manual_handoff_packet_id": "phase64-non-human",
                "application_readiness_packet_id": "phase63-readiness",
                "artifact_id": "phase59-artifact",
            },
            enabled=True,
        ),
        "human_only_application_boundary": False,
    }

    uncreated_readback = services._planning_workspace_human_only_handoff_audit_trail_payload(
        manual_handoff_readback=uncreated,
        enabled=True,
        manual_handoff_packet_id="phase64-uncreated",
        application_readiness_packet_id="phase63-readiness",
        artifact_id="phase59-artifact",
    )
    non_human_readback = services._planning_workspace_human_only_handoff_audit_trail_payload(
        manual_handoff_readback=non_human_only,
        enabled=True,
        manual_handoff_packet_id="phase64-non-human",
        application_readiness_packet_id="phase63-readiness",
        artifact_id="phase59-artifact",
    )

    assert uncreated_readback["handoff_audit_trail_created"] is False
    assert uncreated_readback["fallback_reason"] == "manual_handoff_packet_required"
    assert non_human_readback["handoff_audit_trail_created"] is False
    assert non_human_readback["fallback_reason"] == "human_only_application_boundary_required"


def test_service_chain_creates_audit_trail_from_valid_manual_handoff(monkeypatch):
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
    handoff_payload = services.save_saved_scan_state_payload(
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
    handoff_id = handoff_payload["human_only_manual_application_handoff_packet_readback"][
        "manual_handoff_packet_id"
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
        enable_human_only_manual_application_handoff_packet=True,
        manual_handoff_application_readiness_packet_id=readiness_id,
        manual_handoff_artifact_id=artifact_id,
        enable_human_only_handoff_audit_trail=True,
        handoff_audit_manual_handoff_packet_id=handoff_id,
        handoff_audit_application_readiness_packet_id=readiness_id,
        handoff_audit_artifact_id=artifact_id,
    )
    readback = payload["human_only_handoff_audit_trail_readback"]

    assert readback["handoff_audit_trail_created"] is True
    assert readback["manual_handoff_packet_id"] == handoff_id
    assert readback["application_readiness_packet_id"] == readiness_id
    assert readback["artifact_id"] == artifact_id
    assert readback["audit_event_count"] == 3
    assert readback["ats_automation_performed"] is False
    assert readback["application_submission_performed"] is False
    assert readback["apply_queue_enqueued"] is False


def test_audit_trail_creation_does_not_create_artifact_or_mutate_resume(monkeypatch):
    request = _state_request()
    original_request = deepcopy(request)
    handoff = _manual_handoff_readback(monkeypatch)
    original_handoff_packet = deepcopy(handoff["manual_handoff_packet"])

    readback = services._planning_workspace_human_only_handoff_audit_trail_payload(
        manual_handoff_readback=handoff,
        enabled=True,
        manual_handoff_packet_id=handoff["manual_handoff_packet_id"],
        application_readiness_packet_id=handoff["application_readiness_packet_id"],
        artifact_id=handoff["artifact_id"],
    )

    assert request == original_request
    assert handoff["manual_handoff_packet"] == original_handoff_packet
    assert readback["handoff_audit_trail_created"] is True
    assert readback["handoff_audit_trail"]["resume_artifact_creation_performed"] is False
    assert readback["safety"]["resume_artifact_created"] is False
    assert readback["safety"]["artifact_created"] is False
    assert readback["safety"]["source_resume_mutated"] is False
    assert readback["safety"]["source_resume_state_mutated"] is False
    assert readback["source_resume_unchanged"] is True
    assert readback["source_resume_overwritten"] is False


def test_no_live_llm_provider_ats_submission_or_apply_queue_enqueue(monkeypatch):
    provider_calls = []
    handoff = _manual_handoff_readback(monkeypatch)
    monkeypatch.setattr(
        services,
        "_live_exact_resume_change_proposal_provider_adapter",
        lambda request: provider_calls.append(request) or _valid_exact_provider_payload(),
    )

    readback = services._planning_workspace_human_only_handoff_audit_trail_payload(
        manual_handoff_readback=handoff,
        enabled=True,
        manual_handoff_packet_id=handoff["manual_handoff_packet_id"],
        application_readiness_packet_id=handoff["application_readiness_packet_id"],
        artifact_id=handoff["artifact_id"],
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


def test_phase60_61_62_63_and_64_readbacks_remain_intact(monkeypatch):
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
    handoff_payload = services.save_saved_scan_state_payload(
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
    handoff_id = handoff_payload["human_only_manual_application_handoff_packet_readback"][
        "manual_handoff_packet_id"
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
        enable_human_only_manual_application_handoff_packet=True,
        manual_handoff_application_readiness_packet_id=readiness_id,
        manual_handoff_artifact_id=artifact_id,
        enable_human_only_handoff_audit_trail=True,
        handoff_audit_manual_handoff_packet_id=handoff_id,
        handoff_audit_application_readiness_packet_id=readiness_id,
        handoff_audit_artifact_id=artifact_id,
    )

    assert payload["guarded_resume_copy_artifact_verification_readback"]["readback_phase"] == "60B"
    assert payload["verified_artifact_operator_review_packet_readback"]["readback_phase"] == "61B"
    assert payload["verified_artifact_operator_decision_readback"]["readback_phase"] == "62B"
    assert payload["operator_approved_artifact_application_readiness_packet_readback"]["readback_phase"] == "63B"
    assert payload["human_only_manual_application_handoff_packet_readback"]["readback_phase"] == "64B"
    assert payload["human_only_handoff_audit_trail_readback"]["phase"] == "65A"


def test_ui_readback_display_uses_existing_response_data_and_is_passive():
    script = (ROOT / "src/app/static/scan_workspace.js").read_text(encoding="utf-8")
    getter = script.split(
        "function getScanWorkspaceHandoffAuditTrailPayload",
        1,
    )[1].split(
        "function renderScanWorkspaceHandoffAuditTrailReadback",
        1,
    )[0]
    renderer = script.split(
        "function renderScanWorkspaceHandoffAuditTrailReadback",
        1,
    )[1].split(
        "function getScanWorkspaceHasTailoringPreviewContext",
        1,
    )[0]

    assert "human_only_handoff_audit_trail_readback" in getter
    assert "enable_human_only_handoff_audit_trail" in script
    assert "handoff_audit_manual_handoff_packet_id" in script
    assert "handoff_audit_application_readiness_packet_id" in script
    assert "handoff_audit_artifact_id" in script
    assert "handoff_audit_trail_created" in renderer
    assert "human_only_application_boundary" in renderer
    assert "ats_automation_performed" in renderer
    assert "application_submission_performed" in renderer
    assert "apply_queue_enqueued" in renderer
    assert "_planning_workspace_human_only_handoff_audit_trail_payload" not in renderer
    assert "_live_exact_resume_change_proposal_provider_adapter" not in renderer
    assert "fetch(" not in renderer
    assert "postJsonWithTimeout" not in renderer


def test_no_scoring_formula_or_weight_changes(monkeypatch):
    handoff = _manual_handoff_readback(monkeypatch)
    readback = services._planning_workspace_human_only_handoff_audit_trail_payload(
        manual_handoff_readback=handoff,
        enabled=True,
        manual_handoff_packet_id=handoff["manual_handoff_packet_id"],
        application_readiness_packet_id=handoff["application_readiness_packet_id"],
        artifact_id=handoff["artifact_id"],
    )

    assert readback["safety"]["scoring_formula_changed"] is False
    assert readback["safety"]["scoring_weights_changed"] is False
    assert readback["safety"]["auto_apply_performed"] is False
    assert readback["safety"]["auto_submit_performed"] is False


def test_protected_files_are_unchanged():
    for relative, expected in PROTECTED_HASHES.items():
        assert _sha256(ROOT / relative) == expected


def test_docs_include_phase65a_human_only_handoff_audit_safety_markers():
    text = DOC_PATH.read_text(encoding="utf-8").lower()
    for marker in (
        "default-off",
        "human-only handoff audit trail",
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
