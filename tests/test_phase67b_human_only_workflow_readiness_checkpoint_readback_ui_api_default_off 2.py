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
from tests.test_phase67a_human_only_workflow_readiness_checkpoint_wiring_default_off import (
    _service_payload_with_workflow_checkpoint,
    _summary_readback,
)


ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = (
    ROOT
    / "docs/phase67_human_only_workflow_readiness_checkpoint_readback_ui_api_default_off.md"
)


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def test_default_off_api_readback_does_not_create_workflow_checkpoint_packets(
    monkeypatch,
):
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
    assert readback["readback_phase"] == "67B"
    assert readback["phase67b_readback_hardened"] is True
    assert readback["api_readback"] is True
    assert readback["ui_readback"] is True
    assert readback["workflow_readiness_checkpoint_enabled"] is False
    assert readback["workflow_readiness_checkpoint_requested"] is False
    assert readback["workflow_readiness_checkpoint_created"] is False
    assert readback["validation_status"] == "disabled"


def test_enabled_api_readback_exposes_workflow_checkpoint_observability(monkeypatch):
    payload = _service_payload_with_workflow_checkpoint(monkeypatch)
    readback = payload["human_only_workflow_readiness_checkpoint_readback"]
    metadata = readback["workflow_readiness_checkpoint_metadata"]

    assert readback["readback_phase"] == "67B"
    assert readback["phase67b_readback_hardened"] is True
    assert readback["api_readback"] is True
    assert readback["ui_readback"] is True
    assert readback["workflow_readiness_checkpoint_enabled"] is True
    assert readback["workflow_readiness_checkpoint_requested"] is True
    assert readback["workflow_readiness_checkpoint_created"] is True
    assert readback["workflow_readiness_checkpoint_id"] == readback[
        "stable_checkpoint_key"
    ]
    assert readback["safety_boundary_summary_id"] == readback["stable_summary_key"]
    assert readback["handoff_audit_trail_id"] == readback["stable_audit_key"]
    assert readback["manual_handoff_packet_id"] == readback[
        "stable_handoff_packet_key"
    ]
    assert readback["application_readiness_packet_id"] == readback[
        "stable_readiness_packet_key"
    ]
    assert readback["artifact_id"] == readback["stable_artifact_key"]
    assert readback["workflow_ready_for_human_handoff"] is True
    assert readback["validation_status"] == "valid"
    assert readback["fallback_used"] is False
    assert metadata["readback_phase"] == "67B"
    assert metadata["workflow_readiness_checkpoint_id"] == readback[
        "workflow_readiness_checkpoint_id"
    ]


def test_valid_safety_summary_metadata_shows_checkpoint_metadata(monkeypatch):
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
    metadata = readback["workflow_readiness_checkpoint_metadata"]

    assert metadata["workflow_readiness_checkpoint_created"] is True
    assert metadata["safety_boundary_summary_id"] == summary["safety_boundary_summary_id"]
    assert metadata["handoff_audit_trail_id"] == summary["handoff_audit_trail_id"]
    assert metadata["manual_handoff_packet_id"] == summary["manual_handoff_packet_id"]
    assert metadata["application_readiness_packet_id"] == summary[
        "application_readiness_packet_id"
    ]
    assert metadata["artifact_id"] == summary["artifact_id"]
    assert metadata["validation_status"] == "valid"
    assert metadata["fallback_used"] is False


def test_missing_or_invalid_summary_ids_expose_fallback_metadata(monkeypatch):
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
    assert missing["fallback_used"] is True
    assert missing["fallback_reason"] == "safety_boundary_summary_id_required"
    assert missing["fallback_error_class"] == "ValueError"
    assert missing["fallback_metadata"]["validation_errors"] == [
        "safety_boundary_summary_id_required"
    ]
    assert invalid["workflow_readiness_checkpoint_created"] is False
    assert invalid["fallback_reason"] == "safety_boundary_summary_id_mismatch"
    assert invalid["fallback_metadata"]["fallback_error_class"] == "ValueError"


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
    assert "workflow_readiness_checkpoint_enabled" in renderer
    assert "workflow_readiness_checkpoint_requested" in renderer
    assert "workflow_readiness_checkpoint_created" in renderer
    assert "workflow_readiness_checkpoint_id" in renderer
    assert "safety_boundary_summary_id" in renderer
    assert "core_llm_inference_workflow_automatic" in renderer
    assert "manual_mutation_requires_operator_action" in renderer
    assert "workflow_ready_for_human_handoff" in renderer
    assert "ats_automation_performed" in renderer
    assert "application_submission_performed" in renderer
    assert "apply_queue_enqueued" in renderer
    assert "_planning_workspace_human_only_workflow_readiness_checkpoint_payload" not in renderer
    assert "_live_exact_resume_change_proposal_provider_adapter" not in renderer
    assert "fetch(" not in renderer
    assert "postJsonWithTimeout" not in renderer


def test_readback_does_not_create_artifact_or_mutate_source(monkeypatch):
    readback = _service_payload_with_workflow_checkpoint(monkeypatch)[
        "human_only_workflow_readiness_checkpoint_readback"
    ]

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

    assert readback["readback_action_llm_call_performed"] is False
    assert readback["readback_action_provider_call_performed"] is False
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


def test_corrected_policy_is_represented_in_readback(monkeypatch):
    readback = _service_payload_with_workflow_checkpoint(monkeypatch)[
        "human_only_workflow_readiness_checkpoint_readback"
    ]
    metadata = readback["workflow_readiness_checkpoint_metadata"]

    assert readback["core_llm_inference_workflow_automatic"] is True
    assert readback["manual_mutation_requires_operator_action"] is True
    assert readback["ats_automation_forbidden"] is True
    assert readback["application_submission_forbidden"] is True
    assert readback["apply_queue_enqueue_forbidden"] is True
    assert readback["source_resume_overwrite_forbidden"] is True
    assert readback["auto_apply_forbidden"] is True
    assert metadata["core_llm_inference_workflow_automatic"] is True
    assert metadata["manual_mutation_requires_operator_action"] is True


def test_prior_phase_and_phase67a_readbacks_remain_intact(monkeypatch):
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


def test_no_scoring_formula_or_weight_changes(monkeypatch):
    readback = _service_payload_with_workflow_checkpoint(monkeypatch)[
        "human_only_workflow_readiness_checkpoint_readback"
    ]

    assert readback["safety"]["scoring_formula_changed"] is False
    assert readback["safety"]["scoring_weights_changed"] is False


def test_phase67a_focused_behavior_remains_intact(monkeypatch):
    readback = _service_payload_with_workflow_checkpoint(monkeypatch)[
        "human_only_workflow_readiness_checkpoint_readback"
    ]

    assert readback["phase"] == "67A"
    assert readback["workflow_readiness_checkpoint_created"] is True
    assert readback["workflow_ready_for_human_handoff"] is True
    assert readback["fallback_used"] is False


def test_protected_files_are_unchanged():
    for relative, expected in PROTECTED_HASHES.items():
        assert _sha256(ROOT / relative) == expected


def test_docs_include_phase67b_workflow_readiness_readback_markers():
    text = DOC_PATH.read_text(encoding="utf-8").lower()
    for marker in (
        "default-off",
        "human-only workflow readiness checkpoint readback",
        "corrected llm inference policy",
        "workflow-automatic core llm inference",
        "manual mutation requires operator action",
        "planning workspace action",
        "api/readback",
        "deterministic fallback",
        "no live llm call from this readback action",
        "no resume artifact creation",
        "no source resume overwrite",
        "no ats automation",
        "no application submission",
        "no auto-apply",
    ):
        assert marker in text
