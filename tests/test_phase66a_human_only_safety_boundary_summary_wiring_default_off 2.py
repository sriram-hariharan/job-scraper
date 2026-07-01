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
from tests.test_phase65b_human_only_handoff_audit_trail_readback_ui_api_default_off import (
    _service_payload_with_manual_handoff,
)


ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = ROOT / "docs/phase66_human_only_safety_boundary_summary_wiring_default_off.md"


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _audit_readback(monkeypatch) -> dict:
    handoff = _manual_handoff_readback(monkeypatch)
    return services._planning_workspace_human_only_handoff_audit_trail_payload(
        manual_handoff_readback=handoff,
        enabled=True,
        manual_handoff_packet_id=handoff["manual_handoff_packet_id"],
        application_readiness_packet_id=handoff["application_readiness_packet_id"],
        artifact_id=handoff["artifact_id"],
    )


def _service_payload_with_safety_summary(monkeypatch) -> dict:
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
    audit = services._planning_workspace_human_only_handoff_audit_trail_payload(
        manual_handoff_readback=handoff,
        enabled=True,
        manual_handoff_packet_id=handoff["manual_handoff_packet_id"],
        application_readiness_packet_id=handoff["application_readiness_packet_id"],
        artifact_id=handoff["artifact_id"],
    )

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
        enable_human_only_handoff_audit_trail=True,
        handoff_audit_manual_handoff_packet_id=handoff["manual_handoff_packet_id"],
        handoff_audit_application_readiness_packet_id=handoff[
            "application_readiness_packet_id"
        ],
        handoff_audit_artifact_id=handoff["artifact_id"],
        enable_human_only_safety_boundary_summary=True,
        safety_boundary_handoff_audit_trail_id=audit["handoff_audit_trail_id"],
        safety_boundary_manual_handoff_packet_id=handoff["manual_handoff_packet_id"],
        safety_boundary_application_readiness_packet_id=handoff[
            "application_readiness_packet_id"
        ],
        safety_boundary_artifact_id=handoff["artifact_id"],
    )


def test_default_off_planning_workspace_action_does_not_create_summary(monkeypatch):
    calls = []
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())
    monkeypatch.setattr(
        services,
        "_live_exact_resume_change_proposal_provider_adapter",
        lambda request: calls.append(request) or _two_proposal_provider_payload(),
    )

    payload = _post_state(
        _client(monkeypatch),
        {
            **_state_request(),
            "safety_boundary_handoff_audit_trail_id": "phase65-audit",
            "safety_boundary_manual_handoff_packet_id": "phase64-handoff",
            "safety_boundary_application_readiness_packet_id": "phase63-readiness",
            "safety_boundary_artifact_id": "phase59-artifact",
        },
    )
    readback = payload["human_only_safety_boundary_summary_readback"]

    assert calls == []
    assert readback["phase"] == "66A"
    assert readback["safety_boundary_summary_enabled"] is False
    assert readback["safety_boundary_summary_requested"] is False
    assert readback["safety_boundary_summary_created"] is False
    assert readback["safety_boundary_summary_id"] == ""
    assert readback["validation_status"] == "disabled"
    assert payload["human_only_handoff_audit_trail_readback"][
        "handoff_audit_trail_created"
    ] is False


def test_enabled_action_creates_human_only_safety_boundary_summary(monkeypatch):
    audit = _audit_readback(monkeypatch)

    readback = services._planning_workspace_human_only_safety_boundary_summary_payload(
        handoff_audit_readback=audit,
        enabled=True,
        handoff_audit_trail_id=audit["handoff_audit_trail_id"],
        manual_handoff_packet_id=audit["manual_handoff_packet_id"],
        application_readiness_packet_id=audit["application_readiness_packet_id"],
        artifact_id=audit["artifact_id"],
    )

    assert readback["phase"] == "66A"
    assert readback["safety_boundary_summary_enabled"] is True
    assert readback["safety_boundary_summary_requested"] is True
    assert readback["safety_boundary_summary_created"] is True
    assert readback["safety_boundary_summary_id"].startswith(
        "phase66-safety-boundary-"
    )
    assert readback["handoff_audit_trail_id"] == audit["handoff_audit_trail_id"]
    assert readback["manual_handoff_packet_id"] == audit["manual_handoff_packet_id"]
    assert readback["application_readiness_packet_id"] == audit[
        "application_readiness_packet_id"
    ]
    assert readback["artifact_id"] == audit["artifact_id"]
    assert readback["human_only_application_boundary"] is True
    assert readback["llm_capable_action_count"] == 0
    assert readback["mutation_capable_action_count"] == 0
    assert readback["forbidden_path_count"] == 0
    assert readback["ats_automation_performed"] is False
    assert readback["application_submission_performed"] is False
    assert readback["apply_queue_enqueued"] is False
    assert readback["validation_status"] == "valid"
    assert readback["fallback_used"] is False
    assert readback["source_resume_unchanged"] is True
    assert readback["source_resume_overwritten"] is False


def test_missing_or_invalid_audit_trail_ids_fallback_safely(monkeypatch):
    audit = _audit_readback(monkeypatch)

    missing = services._planning_workspace_human_only_safety_boundary_summary_payload(
        handoff_audit_readback=audit,
        enabled=True,
        handoff_audit_trail_id="",
        manual_handoff_packet_id=audit["manual_handoff_packet_id"],
        application_readiness_packet_id=audit["application_readiness_packet_id"],
        artifact_id=audit["artifact_id"],
    )
    invalid = services._planning_workspace_human_only_safety_boundary_summary_payload(
        handoff_audit_readback=audit,
        enabled=True,
        handoff_audit_trail_id="not-the-audit-trail",
        manual_handoff_packet_id=audit["manual_handoff_packet_id"],
        application_readiness_packet_id=audit["application_readiness_packet_id"],
        artifact_id=audit["artifact_id"],
    )

    assert missing["safety_boundary_summary_created"] is False
    assert missing["fallback_reason"] == "handoff_audit_trail_id_required"
    assert missing["fallback_metadata"]["fallback_error_class"] == "ValueError"
    assert invalid["safety_boundary_summary_created"] is False
    assert invalid["fallback_reason"] == "handoff_audit_trail_id_mismatch"
    assert invalid["source_resume_unchanged"] is True
    assert invalid["source_resume_overwritten"] is False


def test_invalid_optional_ids_fallback_safely(monkeypatch):
    audit = _audit_readback(monkeypatch)

    bad_handoff = services._planning_workspace_human_only_safety_boundary_summary_payload(
        handoff_audit_readback=audit,
        enabled=True,
        handoff_audit_trail_id=audit["handoff_audit_trail_id"],
        manual_handoff_packet_id="not-the-handoff",
        application_readiness_packet_id=audit["application_readiness_packet_id"],
        artifact_id=audit["artifact_id"],
    )
    bad_readiness = services._planning_workspace_human_only_safety_boundary_summary_payload(
        handoff_audit_readback=audit,
        enabled=True,
        handoff_audit_trail_id=audit["handoff_audit_trail_id"],
        manual_handoff_packet_id=audit["manual_handoff_packet_id"],
        application_readiness_packet_id="not-the-readiness",
        artifact_id=audit["artifact_id"],
    )
    bad_artifact = services._planning_workspace_human_only_safety_boundary_summary_payload(
        handoff_audit_readback=audit,
        enabled=True,
        handoff_audit_trail_id=audit["handoff_audit_trail_id"],
        manual_handoff_packet_id=audit["manual_handoff_packet_id"],
        application_readiness_packet_id=audit["application_readiness_packet_id"],
        artifact_id="not-the-artifact",
    )

    assert bad_handoff["fallback_reason"] == "manual_handoff_packet_id_mismatch"
    assert bad_readiness["fallback_reason"] == "application_readiness_packet_id_mismatch"
    assert bad_artifact["fallback_reason"] == "artifact_id_mismatch"


def test_summary_creation_does_not_create_artifact_or_mutate_source(monkeypatch):
    audit = _audit_readback(monkeypatch)
    readback = services._planning_workspace_human_only_safety_boundary_summary_payload(
        handoff_audit_readback=audit,
        enabled=True,
        handoff_audit_trail_id=audit["handoff_audit_trail_id"],
        manual_handoff_packet_id=audit["manual_handoff_packet_id"],
        application_readiness_packet_id=audit["application_readiness_packet_id"],
        artifact_id=audit["artifact_id"],
    )

    assert readback["safety"]["resume_artifact_created"] is False
    assert readback["safety"]["artifact_created"] is False
    assert readback["safety"]["source_resume_mutated"] is False
    assert readback["safety"]["source_resume_state_mutated"] is False
    assert readback["source_resume_unchanged"] is True
    assert readback["source_resume_overwritten"] is False


def test_no_live_llm_provider_ats_submission_or_apply_queue(monkeypatch):
    audit = _audit_readback(monkeypatch)
    readback = services._planning_workspace_human_only_safety_boundary_summary_payload(
        handoff_audit_readback=audit,
        enabled=True,
        handoff_audit_trail_id=audit["handoff_audit_trail_id"],
        manual_handoff_packet_id=audit["manual_handoff_packet_id"],
        application_readiness_packet_id=audit["application_readiness_packet_id"],
        artifact_id=audit["artifact_id"],
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


def test_service_chain_creates_summary_and_preserves_prior_readbacks(monkeypatch):
    payload = _service_payload_with_safety_summary(monkeypatch)

    assert payload["guarded_resume_copy_artifact_verification_readback"]["phase"] == "60A"
    assert payload["verified_artifact_operator_review_packet_readback"]["phase"] == "61A"
    assert payload["verified_artifact_operator_decision_readback"]["phase"] == "62A"
    assert payload["operator_approved_artifact_application_readiness_packet_readback"][
        "phase"
    ] == "63A"
    assert payload["human_only_manual_application_handoff_packet_readback"]["phase"] == "64A"
    assert payload["human_only_handoff_audit_trail_readback"]["phase"] == "65A"
    assert payload["human_only_safety_boundary_summary_readback"]["phase"] == "66A"
    assert payload["human_only_safety_boundary_summary_readback"][
        "safety_boundary_summary_created"
    ] is True


def test_ui_readback_display_uses_existing_response_data_and_is_passive():
    script = (ROOT / "src/app/static/scan_workspace.js").read_text(encoding="utf-8")
    getter = script.split(
        "function getScanWorkspaceSafetyBoundarySummaryPayload",
        1,
    )[1].split(
        "function renderScanWorkspaceSafetyBoundarySummaryReadback",
        1,
    )[0]
    renderer = script.split(
        "function renderScanWorkspaceSafetyBoundarySummaryReadback",
        1,
    )[1].split(
        "function getScanWorkspaceHasTailoringPreviewContext",
        1,
    )[0]

    assert "human_only_safety_boundary_summary_readback" in getter
    assert "enable_human_only_safety_boundary_summary" in script
    assert "safety_boundary_handoff_audit_trail_id" in script
    assert "safety_boundary_summary_created" in renderer
    assert "human_only_application_boundary" in renderer
    assert "llm_capable_action_count" in renderer
    assert "mutation_capable_action_count" in renderer
    assert "forbidden_path_count" in renderer
    assert "ats_automation_performed" in renderer
    assert "application_submission_performed" in renderer
    assert "apply_queue_enqueued" in renderer
    assert "_planning_workspace_human_only_safety_boundary_summary_payload" not in renderer
    assert "_live_exact_resume_change_proposal_provider_adapter" not in renderer
    assert "fetch(" not in renderer
    assert "postJsonWithTimeout" not in renderer


def test_no_scoring_formula_or_weight_changes(monkeypatch):
    audit = _audit_readback(monkeypatch)
    readback = services._planning_workspace_human_only_safety_boundary_summary_payload(
        handoff_audit_readback=audit,
        enabled=True,
        handoff_audit_trail_id=audit["handoff_audit_trail_id"],
        manual_handoff_packet_id=audit["manual_handoff_packet_id"],
        application_readiness_packet_id=audit["application_readiness_packet_id"],
        artifact_id=audit["artifact_id"],
    )

    assert readback["safety"]["scoring_formula_changed"] is False
    assert readback["safety"]["scoring_weights_changed"] is False


def test_protected_files_are_unchanged():
    for relative, expected in PROTECTED_HASHES.items():
        assert _sha256(ROOT / relative) == expected


def test_docs_include_phase66a_safety_markers():
    text = DOC_PATH.read_text(encoding="utf-8").lower()
    for marker in (
        "default-off",
        "human-only safety boundary summary",
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
