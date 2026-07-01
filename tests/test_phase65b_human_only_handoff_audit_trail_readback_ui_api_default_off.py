from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from src.app import services
from tests.test_phase56a_live_tailoring_suggestion_planning_workspace_wiring_default_off import (
    _patch_storage,
    _state_request,
    _stored_scan_payload,
    _valid_provider_payload as _valid_tailoring_provider_payload,
)
from tests.test_phase58b_manual_exact_change_acceptance_approved_plan_readback_ui_api_default_off import (
    _two_proposal_provider_payload,
)
from tests.test_phase64a_human_only_manual_application_handoff_packet_wiring_default_off import (
    PROTECTED_HASHES,
    _client,
    _post_state,
)
from tests.test_phase65a_human_only_handoff_audit_trail_wiring_default_off import (
    _manual_handoff_readback,
)


ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = (
    ROOT
    / "docs/phase65_human_only_handoff_audit_trail_readback_ui_api_default_off.md"
)


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _service_payload_with_manual_handoff(monkeypatch) -> dict:
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
    return services.save_saved_scan_state_payload(
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


def test_default_off_api_readback_does_not_create_handoff_audit_trail_packets(
    monkeypatch,
):
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())
    calls = []
    monkeypatch.setattr(
        services,
        "_live_exact_resume_change_proposal_provider_adapter",
        lambda request: calls.append(request) or _two_proposal_provider_payload(),
    )

    payload = _post_state(
        _client(monkeypatch),
        {
            **_state_request(),
            "handoff_audit_manual_handoff_packet_id": "phase64-handoff",
            "handoff_audit_application_readiness_packet_id": "phase63-readiness",
            "handoff_audit_artifact_id": "phase59-artifact",
        },
    )
    readback = payload["human_only_handoff_audit_trail_readback"]

    assert calls == []
    assert readback["phase"] == "65A"
    assert readback["readback_phase"] == "65B"
    assert readback["phase65b_readback_hardened"] is True
    assert readback["api_readback"] is True
    assert readback["ui_readback"] is True
    assert readback["handoff_audit_trail_enabled"] is False
    assert readback["handoff_audit_trail_requested"] is False
    assert readback["handoff_audit_trail_created"] is False
    assert readback["validation_status"] == "disabled"


def test_enabled_api_readback_exposes_human_only_handoff_audit_observability(
    monkeypatch,
):
    handoff_payload = _service_payload_with_manual_handoff(monkeypatch)
    plan_id = handoff_payload["manual_exact_change_acceptance_readback"][
        "approved_change_plan_id"
    ]
    artifact_id = handoff_payload["guarded_resume_copy_artifact_readback"]["artifact_id"]
    review_packet_id = handoff_payload["verified_artifact_operator_review_packet_readback"][
        "operator_review_packet_id"
    ]
    decision_id = handoff_payload["verified_artifact_operator_decision_readback"][
        "operator_decision_id"
    ]
    readiness_id = handoff_payload[
        "operator_approved_artifact_application_readiness_packet_readback"
    ]["application_readiness_packet_id"]
    handoff = handoff_payload["human_only_manual_application_handoff_packet_readback"]

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
        handoff_audit_manual_handoff_packet_id=handoff["manual_handoff_packet_id"],
        handoff_audit_application_readiness_packet_id=handoff[
            "application_readiness_packet_id"
        ],
        handoff_audit_artifact_id=handoff["artifact_id"],
    )
    readback = payload["human_only_handoff_audit_trail_readback"]
    metadata = readback["handoff_audit_trail_metadata"]

    assert readback["readback_phase"] == "65B"
    assert readback["handoff_audit_trail_enabled"] is True
    assert readback["handoff_audit_trail_requested"] is True
    assert readback["handoff_audit_trail_created"] is True
    assert readback["handoff_audit_trail_id"] == readback["stable_audit_key"]
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
    assert metadata["handoff_audit_trail_id"] == readback["handoff_audit_trail_id"]


def test_valid_manual_handoff_metadata_shows_audit_trail_metadata(monkeypatch):
    handoff = _manual_handoff_readback(monkeypatch)
    readback = services._planning_workspace_human_only_handoff_audit_trail_payload(
        manual_handoff_readback=handoff,
        enabled=True,
        manual_handoff_packet_id=handoff["manual_handoff_packet_id"],
        application_readiness_packet_id=handoff["application_readiness_packet_id"],
        artifact_id=handoff["artifact_id"],
    )

    assert readback["api_readback_fields"] == readback["ui_readback_fields"]
    for field in (
        "handoff_audit_trail_enabled",
        "handoff_audit_trail_requested",
        "handoff_audit_trail_created",
        "handoff_audit_trail_id",
        "stable_audit_key",
        "manual_handoff_packet_id",
        "stable_handoff_packet_key",
        "application_readiness_packet_id",
        "stable_readiness_packet_key",
        "artifact_id",
        "stable_artifact_key",
        "human_only_application_boundary",
        "audit_event_count",
        "ats_automation_performed",
        "application_submission_performed",
        "apply_queue_enqueued",
        "validation_status",
        "fallback_used",
        "fallback_reason",
        "fallback_error_class",
        "source_resume_unchanged",
        "source_resume_overwritten",
        "handoff_audit_trail_metadata",
    ):
        assert field in readback["api_readback_fields"]


def test_missing_or_invalid_handoff_packet_ids_expose_fallback_metadata(monkeypatch):
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
        manual_handoff_packet_id="not-the-packet",
        application_readiness_packet_id=handoff["application_readiness_packet_id"],
        artifact_id=handoff["artifact_id"],
    )

    assert missing["handoff_audit_trail_created"] is False
    assert missing["fallback_used"] is True
    assert missing["fallback_reason"] == "manual_handoff_packet_id_required"
    assert missing["fallback_error_class"] == "ValueError"
    assert missing["fallback_metadata"]["validation_errors"] == [
        "manual_handoff_packet_id_required"
    ]
    assert invalid["handoff_audit_trail_created"] is False
    assert invalid["fallback_reason"] == "manual_handoff_packet_id_mismatch"
    assert invalid["fallback_metadata"]["fallback_error_class"] == "ValueError"


def test_ui_readback_display_uses_existing_response_data_and_is_passive():
    script = (ROOT / "src/app/static/scan_workspace.js").read_text(encoding="utf-8")
    renderer = script.split(
        "function renderScanWorkspaceHandoffAuditTrailReadback",
        1,
    )[1].split(
        "function getScanWorkspaceHasTailoringPreviewContext",
        1,
    )[0]

    assert "handoff_audit_trail_enabled" in renderer
    assert "handoff_audit_trail_requested" in renderer
    assert "handoff_audit_trail_created" in renderer
    assert "handoff_audit_trail_id" in renderer
    assert "manual_handoff_packet_id" in renderer
    assert "application_readiness_packet_id" in renderer
    assert "artifact_id" in renderer
    assert "human_only_application_boundary" in renderer
    assert "audit_event_count" in renderer
    assert "ats_automation_performed" in renderer
    assert "application_submission_performed" in renderer
    assert "apply_queue_enqueued" in renderer
    assert "source_resume_unchanged" in renderer
    assert "source_resume_overwritten" in renderer
    assert "_planning_workspace_human_only_handoff_audit_trail_payload" not in renderer
    assert "fetch(" not in renderer
    assert "postJsonWithTimeout" not in renderer


def test_audit_readback_does_not_create_resume_artifact_or_mutate_source(monkeypatch):
    handoff = _manual_handoff_readback(monkeypatch)
    readback = services._planning_workspace_human_only_handoff_audit_trail_payload(
        manual_handoff_readback=handoff,
        enabled=True,
        manual_handoff_packet_id=handoff["manual_handoff_packet_id"],
        application_readiness_packet_id=handoff["application_readiness_packet_id"],
        artifact_id=handoff["artifact_id"],
    )

    assert readback["handoff_audit_trail"]["resume_artifact_creation_performed"] is False
    assert readback["safety"]["resume_artifact_created"] is False
    assert readback["safety"]["artifact_created"] is False
    assert readback["safety"]["source_resume_mutated"] is False
    assert readback["safety"]["source_resume_state_mutated"] is False
    assert readback["source_resume_unchanged"] is True
    assert readback["source_resume_overwritten"] is False


def test_no_live_llm_provider_ats_submission_or_apply_queue(monkeypatch):
    handoff = _manual_handoff_readback(monkeypatch)
    readback = services._planning_workspace_human_only_handoff_audit_trail_payload(
        manual_handoff_readback=handoff,
        enabled=True,
        manual_handoff_packet_id=handoff["manual_handoff_packet_id"],
        application_readiness_packet_id=handoff["application_readiness_packet_id"],
        artifact_id=handoff["artifact_id"],
    )
    safety = readback["safety"]

    assert safety["provider_call_performed"] is False
    assert safety["llm_call_performed"] is False
    assert safety["network_call_performed"] is False
    assert safety["ats_automation_performed"] is False
    assert safety["application_submission_performed"] is False
    assert safety["apply_queue_enqueued"] is False
    assert safety["application_execution_enqueued"] is False
    assert safety["application_execution_performed"] is False
    assert safety["auto_apply_performed"] is False
    assert safety["auto_submit_performed"] is False


def test_prior_phase_readbacks_and_phase65a_behavior_remain_intact(monkeypatch):
    payload = _service_payload_with_manual_handoff(monkeypatch)
    handoff = payload["human_only_manual_application_handoff_packet_readback"]
    audit_payload = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
        enable_human_only_handoff_audit_trail=True,
        handoff_audit_manual_handoff_packet_id=handoff["manual_handoff_packet_id"],
        handoff_audit_application_readiness_packet_id=handoff[
            "application_readiness_packet_id"
        ],
        handoff_audit_artifact_id=handoff["artifact_id"],
    )

    assert payload["guarded_resume_copy_artifact_verification_readback"]["phase"] == "60A"
    assert payload["verified_artifact_operator_review_packet_readback"]["phase"] == "61A"
    assert payload["verified_artifact_operator_decision_readback"]["phase"] == "62A"
    assert payload["operator_approved_artifact_application_readiness_packet_readback"][
        "phase"
    ] == "63A"
    assert handoff["phase"] == "64A"
    assert audit_payload["human_only_handoff_audit_trail_readback"]["phase"] == "65A"
    assert audit_payload["human_only_handoff_audit_trail_readback"][
        "readback_phase"
    ] == "65B"


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


def test_protected_files_are_unchanged():
    for relative, expected in PROTECTED_HASHES.items():
        assert _sha256(ROOT / relative) == expected


def test_docs_include_phase65b_handoff_audit_readback_markers():
    text = DOC_PATH.read_text(encoding="utf-8").lower()
    for marker in (
        "default-off",
        "human-only handoff audit trail readback",
        "planning workspace action",
        "api readback",
        "ui readback",
        "deterministic fallback",
        "no live llm call",
        "no resume artifact creation",
        "no source resume overwrite",
        "no ats automation",
        "no application submission",
        "no auto-apply",
    ):
        assert marker in text
