from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from src.app import services
from tests.test_phase56a_live_tailoring_suggestion_planning_workspace_wiring_default_off import (
    _patch_storage,
    _state_request,
    _stored_scan_payload,
)
from tests.test_phase58b_manual_exact_change_acceptance_approved_plan_readback_ui_api_default_off import (
    _two_proposal_provider_payload,
)
from tests.test_phase64a_human_only_manual_application_handoff_packet_wiring_default_off import (
    PROTECTED_HASHES,
    _client,
    _post_state,
)
from tests.test_phase66a_human_only_safety_boundary_summary_wiring_default_off import (
    _service_payload_with_safety_summary,
)


ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = (
    ROOT
    / "docs/phase67_human_only_workflow_readiness_checkpoint_wiring_default_off.md"
)


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _summary_readback(monkeypatch) -> dict:
    return _service_payload_with_safety_summary(monkeypatch)[
        "human_only_safety_boundary_summary_readback"
    ]


def _service_payload_with_workflow_checkpoint(monkeypatch) -> dict:
    summary_payload = _service_payload_with_safety_summary(monkeypatch)
    plan_id = summary_payload["manual_exact_change_acceptance_readback"][
        "approved_change_plan_id"
    ]
    artifact_id = summary_payload["guarded_resume_copy_artifact_readback"]["artifact_id"]
    review_packet_id = summary_payload["verified_artifact_operator_review_packet_readback"][
        "operator_review_packet_id"
    ]
    decision_id = summary_payload["verified_artifact_operator_decision_readback"][
        "operator_decision_id"
    ]
    readiness_id = summary_payload[
        "operator_approved_artifact_application_readiness_packet_readback"
    ]["application_readiness_packet_id"]
    handoff = summary_payload["human_only_manual_application_handoff_packet_readback"]
    audit = summary_payload["human_only_handoff_audit_trail_readback"]
    summary = summary_payload["human_only_safety_boundary_summary_readback"]

    return services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
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
        enable_human_only_workflow_readiness_checkpoint=True,
        workflow_readiness_safety_boundary_summary_id=summary[
            "safety_boundary_summary_id"
        ],
        workflow_readiness_handoff_audit_trail_id=audit["handoff_audit_trail_id"],
        workflow_readiness_manual_handoff_packet_id=handoff["manual_handoff_packet_id"],
        workflow_readiness_application_readiness_packet_id=handoff[
            "application_readiness_packet_id"
        ],
        workflow_readiness_artifact_id=handoff["artifact_id"],
    )


def test_default_off_planning_workspace_action_does_not_create_checkpoint(monkeypatch):
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
            "workflow_readiness_safety_boundary_summary_id": "phase66-summary",
            "workflow_readiness_handoff_audit_trail_id": "phase65-audit",
            "workflow_readiness_manual_handoff_packet_id": "phase64-handoff",
            "workflow_readiness_application_readiness_packet_id": "phase63-readiness",
            "workflow_readiness_artifact_id": "phase59-artifact",
        },
    )
    readback = payload["human_only_workflow_readiness_checkpoint_readback"]

    assert calls == []
    assert readback["phase"] == "67A"
    assert readback["workflow_readiness_checkpoint_enabled"] is False
    assert readback["workflow_readiness_checkpoint_requested"] is False
    assert readback["workflow_readiness_checkpoint_created"] is False
    assert readback["workflow_readiness_checkpoint_id"] == ""
    assert readback["validation_status"] == "disabled"
    assert readback["fallback_reason"] == "feature_flag_disabled"
    assert payload["human_only_safety_boundary_summary_readback"][
        "safety_boundary_summary_created"
    ] is False


def test_enabled_action_creates_checkpoint_from_valid_safety_summary(monkeypatch):
    summary = _summary_readback(monkeypatch)

    readback = services._planning_workspace_human_only_workflow_readiness_checkpoint_payload(
        safety_boundary_summary_readback=summary,
        enabled=True,
        safety_boundary_summary_id=summary["safety_boundary_summary_id"],
        handoff_audit_trail_id=summary["handoff_audit_trail_id"],
        manual_handoff_packet_id=summary["manual_handoff_packet_id"],
        application_readiness_packet_id=summary["application_readiness_packet_id"],
        artifact_id=summary["artifact_id"],
    )

    assert readback["phase"] == "67A"
    assert readback["workflow_readiness_checkpoint_enabled"] is True
    assert readback["workflow_readiness_checkpoint_requested"] is True
    assert readback["workflow_readiness_checkpoint_created"] is True
    assert readback["workflow_readiness_checkpoint_id"].startswith(
        "phase67-workflow-readiness-"
    )
    assert readback["safety_boundary_summary_id"] == summary["safety_boundary_summary_id"]
    assert readback["handoff_audit_trail_id"] == summary["handoff_audit_trail_id"]
    assert readback["manual_handoff_packet_id"] == summary["manual_handoff_packet_id"]
    assert readback["application_readiness_packet_id"] == summary[
        "application_readiness_packet_id"
    ]
    assert readback["artifact_id"] == summary["artifact_id"]
    assert readback["workflow_ready_for_human_handoff"] is True
    assert readback["validation_status"] == "valid"
    assert readback["fallback_used"] is False


def test_missing_or_invalid_summary_ids_fallback_safely(monkeypatch):
    summary = _summary_readback(monkeypatch)

    missing = services._planning_workspace_human_only_workflow_readiness_checkpoint_payload(
        safety_boundary_summary_readback=summary,
        enabled=True,
        safety_boundary_summary_id="",
    )
    invalid = services._planning_workspace_human_only_workflow_readiness_checkpoint_payload(
        safety_boundary_summary_readback=summary,
        enabled=True,
        safety_boundary_summary_id="not-the-summary",
    )

    assert missing["workflow_readiness_checkpoint_created"] is False
    assert missing["fallback_reason"] == "safety_boundary_summary_id_required"
    assert missing["fallback_metadata"]["fallback_error_class"] == "ValueError"
    assert invalid["workflow_readiness_checkpoint_created"] is False
    assert invalid["fallback_reason"] == "safety_boundary_summary_id_mismatch"
    assert invalid["source_resume_unchanged"] is True
    assert invalid["source_resume_overwritten"] is False


def test_invalid_optional_ids_fallback_safely(monkeypatch):
    summary = _summary_readback(monkeypatch)

    bad_audit = services._planning_workspace_human_only_workflow_readiness_checkpoint_payload(
        safety_boundary_summary_readback=summary,
        enabled=True,
        safety_boundary_summary_id=summary["safety_boundary_summary_id"],
        handoff_audit_trail_id="not-the-audit",
    )
    bad_handoff = services._planning_workspace_human_only_workflow_readiness_checkpoint_payload(
        safety_boundary_summary_readback=summary,
        enabled=True,
        safety_boundary_summary_id=summary["safety_boundary_summary_id"],
        handoff_audit_trail_id=summary["handoff_audit_trail_id"],
        manual_handoff_packet_id="not-the-handoff",
    )
    bad_readiness = services._planning_workspace_human_only_workflow_readiness_checkpoint_payload(
        safety_boundary_summary_readback=summary,
        enabled=True,
        safety_boundary_summary_id=summary["safety_boundary_summary_id"],
        application_readiness_packet_id="not-the-readiness",
    )
    bad_artifact = services._planning_workspace_human_only_workflow_readiness_checkpoint_payload(
        safety_boundary_summary_readback=summary,
        enabled=True,
        safety_boundary_summary_id=summary["safety_boundary_summary_id"],
        artifact_id="not-the-artifact",
    )

    assert bad_audit["fallback_reason"] == "handoff_audit_trail_id_mismatch"
    assert bad_handoff["fallback_reason"] == "manual_handoff_packet_id_mismatch"
    assert bad_readiness["fallback_reason"] == "application_readiness_packet_id_mismatch"
    assert bad_artifact["fallback_reason"] == "artifact_id_mismatch"


def test_checkpoint_does_not_create_artifact_or_mutate_source(monkeypatch):
    readback = _service_payload_with_workflow_checkpoint(monkeypatch)[
        "human_only_workflow_readiness_checkpoint_readback"
    ]

    assert readback["workflow_readiness_checkpoint_created"] is True
    assert readback["safety"]["resume_artifact_created"] is False
    assert readback["safety"]["artifact_created"] is False
    assert readback["safety"]["source_resume_mutated"] is False
    assert readback["safety"]["source_resume_state_mutated"] is False
    assert readback["source_resume_unchanged"] is True
    assert readback["source_resume_overwritten"] is False


def test_no_live_llm_provider_ats_submission_or_apply_queue(monkeypatch):
    readback = _service_payload_with_workflow_checkpoint(monkeypatch)[
        "human_only_workflow_readiness_checkpoint_readback"
    ]
    safety = readback["safety"]

    assert readback["checkpoint_action_llm_call_performed"] is False
    assert readback["checkpoint_action_provider_call_performed"] is False
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


def test_corrected_policy_is_represented(monkeypatch):
    readback = _service_payload_with_workflow_checkpoint(monkeypatch)[
        "human_only_workflow_readiness_checkpoint_readback"
    ]
    metadata = readback["workflow_readiness_checkpoint_metadata"]

    assert readback["human_only_application_boundary"] is True
    assert readback["core_llm_inference_workflow_automatic"] is True
    assert readback["manual_mutation_requires_operator_action"] is True
    assert readback["ats_automation_forbidden"] is True
    assert readback["application_submission_forbidden"] is True
    assert readback["apply_queue_enqueue_forbidden"] is True
    assert readback["source_resume_overwrite_forbidden"] is True
    assert readback["auto_apply_forbidden"] is True
    assert metadata["core_llm_inference_workflow_automatic"] is True
    assert metadata["manual_mutation_requires_operator_action"] is True


def test_prior_phase_readbacks_remain_intact(monkeypatch):
    payload = _service_payload_with_workflow_checkpoint(monkeypatch)

    assert payload["operator_approved_artifact_application_readiness_packet_readback"][
        "phase"
    ] == "63A"
    assert payload["human_only_manual_application_handoff_packet_readback"]["phase"] == "64A"
    assert payload["human_only_handoff_audit_trail_readback"]["phase"] == "65A"
    assert payload["human_only_safety_boundary_summary_readback"]["phase"] == "66A"
    assert payload["human_only_safety_boundary_summary_readback"][
        "safety_boundary_summary_created"
    ] is True
    assert payload["human_only_workflow_readiness_checkpoint_readback"]["phase"] == "67A"
    assert payload["human_only_workflow_readiness_checkpoint_readback"][
        "workflow_readiness_checkpoint_created"
    ] is True


def test_ui_readback_display_uses_existing_response_data_and_is_passive():
    script = (ROOT / "src/app/static/scan_workspace.js").read_text(encoding="utf-8")
    getter = script.split(
        "function getScanWorkspaceWorkflowReadinessCheckpointPayload",
        1,
    )[1].split(
        "function renderScanWorkspaceWorkflowReadinessCheckpointReadback",
        1,
    )[0]
    renderer = script.split(
        "function renderScanWorkspaceWorkflowReadinessCheckpointReadback",
        1,
    )[1].split(
        "function getScanWorkspaceHasTailoringPreviewContext",
        1,
    )[0]

    assert "human_only_workflow_readiness_checkpoint_readback" in getter
    assert "enable_human_only_workflow_readiness_checkpoint" in script
    assert "workflow_readiness_safety_boundary_summary_id" in script
    assert "workflow_readiness_checkpoint_created" in renderer
    assert "workflow_ready_for_human_handoff" in renderer
    assert "core_llm_inference_workflow_automatic" in renderer
    assert "manual_mutation_requires_operator_action" in renderer
    assert "ats_automation_performed" in renderer
    assert "application_submission_performed" in renderer
    assert "apply_queue_enqueued" in renderer
    assert "_planning_workspace_human_only_workflow_readiness_checkpoint_payload" not in renderer
    assert "_live_exact_resume_change_proposal_provider_adapter" not in renderer
    assert "fetch(" not in renderer
    assert "postJsonWithTimeout" not in renderer


def test_no_scoring_formula_or_weight_changes(monkeypatch):
    readback = _service_payload_with_workflow_checkpoint(monkeypatch)[
        "human_only_workflow_readiness_checkpoint_readback"
    ]

    assert readback["safety"]["scoring_formula_changed"] is False
    assert readback["safety"]["scoring_weights_changed"] is False


def test_protected_files_are_unchanged():
    for relative, expected in PROTECTED_HASHES.items():
        assert _sha256(ROOT / relative) == expected


def test_docs_include_phase67a_workflow_readiness_markers():
    text = DOC_PATH.read_text(encoding="utf-8").lower()
    for marker in (
        "default-off",
        "human-only workflow readiness checkpoint",
        "corrected llm inference policy",
        "workflow-automatic core llm inference",
        "manual mutation requires operator action",
        "planning workspace action",
        "deterministic fallback",
        "no live llm call from this checkpoint action",
        "no resume artifact creation",
        "no source resume overwrite",
        "no ats automation",
        "no application submission",
        "no auto-apply",
    ):
        assert marker in text
