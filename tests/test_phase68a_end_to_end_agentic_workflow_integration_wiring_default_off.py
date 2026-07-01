from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from src.app import services
from tests.test_phase55a_live_jd_llm_extraction_planning_scan_wiring_default_off import (
    _request_payload,
    _valid_provider_payload as _valid_jd_provider_payload,
)
from tests.test_phase56a_live_tailoring_suggestion_planning_workspace_wiring_default_off import (
    _patch_storage,
    _state_request,
    _stored_scan_payload,
)
from tests.test_phase64a_human_only_manual_application_handoff_packet_wiring_default_off import (
    PROTECTED_HASHES,
)
from tests.test_phase67a_human_only_workflow_readiness_checkpoint_wiring_default_off import (
    _service_payload_with_workflow_checkpoint,
)


ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = ROOT / "docs/phase68_end_to_end_agentic_workflow_integration_wiring_default_off.md"


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _build_scan(monkeypatch, **overrides) -> dict:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    return services.create_saved_scan_payload(**{**_request_payload(), **overrides})


def test_normal_default_readback_does_not_perform_manual_mutation(monkeypatch):
    calls = []
    payload = _build_scan(
        monkeypatch,
        jd_llm_provider_adapter=lambda request: calls.append(request)
        or _valid_jd_provider_payload(),
    )
    readback = payload["agentic_workflow_integration_readback"]

    assert calls == []
    assert readback["phase"] == "68A"
    assert readback["agentic_workflow_integration_performed"] is True
    assert readback["user_started_scan_or_evaluation"] is True
    assert readback["manual_mutation_requires_operator_action"] is True
    assert readback["source_resume_unchanged"] is True
    assert readback["source_resume_overwritten"] is False
    assert readback["safety"]["source_resume_mutated"] is False
    assert readback["safety"]["resume_artifact_created"] is False


def test_user_started_scan_exposes_end_to_end_agentic_workflow_status(monkeypatch):
    payload = _build_scan(monkeypatch)
    readback = payload["scan_review_payload"]["agentic_workflow_integration_readback"]

    assert readback["agentic_workflow_integration_enabled"] is True
    assert readback["agentic_workflow_integration_requested"] is True
    assert readback["agentic_workflow_integration_performed"] is True
    assert readback["user_started_scan_or_evaluation"] is True
    assert readback["scan_evaluation_path"] is True
    assert readback["validation_status"] == "valid"
    assert readback["fallback_used"] is False


def test_core_llm_inference_policy_is_workflow_automatic_in_user_started_scan(
    monkeypatch,
):
    payload = _build_scan(
        monkeypatch,
        enable_jd_llm_extraction=True,
        jd_llm_provider_adapter=lambda _request: _valid_jd_provider_payload(),
    )
    readback = payload["agentic_workflow_integration_readback"]

    assert readback["core_llm_inference_workflow_automatic"] is True
    assert readback["jd_signal_extraction_available"] is True
    assert readback["jd_signal_extraction_performed"] is True
    assert readback["llm_evaluation_available"] is True
    assert readback["llm_evaluation_performed"] is True
    assert readback["jd_llm_extraction_readback"]["llm_call_performed"] is True


def test_jd_skills_requirements_evidence_scoring_and_ranking_are_surfaced_separately(
    monkeypatch,
):
    payload = _build_scan(monkeypatch)
    readback = payload["agentic_workflow_integration_readback"]
    boundaries = readback["responsibility_boundaries"]

    assert readback["jd_signal_extraction_available"] is True
    assert readback["skills_extraction_available"] is True
    assert readback["requirements_extraction_available"] is True
    assert readback["resume_evidence_available"] is True
    assert readback["scoring_ranking_available"] is True
    assert readback["scoring_ranking_performed"] is True
    assert boundaries["scan_flow_stays_in_scan_path"] is True
    assert boundaries["deterministic_prefilter_separate_from_llm_evaluation"] is True
    assert boundaries["jd_intelligence_separate_from_resume_evidence"] is True
    assert boundaries["final_scoring_ranking_separate_from_llm_evaluation"] is True
    assert boundaries["manual_mutation_handoff_separate_from_analysis_automation"] is True


def test_planning_workspace_next_actions_surface_without_creating_artifacts(
    monkeypatch,
):
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())
    payload = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
    )
    readback = payload["agentic_workflow_integration_readback"]

    assert readback["planning_workspace_next_actions_available"] is True
    assert readback["tailoring_suggestion_action_available"] is True
    assert readback["exact_change_proposal_action_available"] is True
    assert readback["tailoring_suggestion_action_status"] == "disabled"
    assert readback["exact_change_proposal_action_status"] == "disabled"
    assert readback["safety"]["resume_artifact_created"] is False
    assert readback["source_resume_unchanged"] is True
    assert readback["source_resume_overwritten"] is False


def test_tailoring_and_exact_change_actions_remain_explicit_not_silent_mutations(
    monkeypatch,
):
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())
    payload = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
    )
    readback = payload["agentic_workflow_integration_readback"]

    assert readback["tailoring_suggestion_action_available"] is True
    assert readback["exact_change_proposal_action_available"] is True
    assert readback["manual_mutation_requires_operator_action"] is True
    assert readback["safety"]["source_resume_mutated"] is False
    assert readback["safety"]["source_resume_state_mutated"] is False


def test_no_live_provider_call_is_made_by_integration_readback_in_tests(monkeypatch):
    calls = []
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())
    payload = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
        live_tailoring_suggestion_adapter=lambda request: calls.append(request),
        live_exact_resume_change_proposal_adapter=lambda request: calls.append(request),
    )
    readback = payload["agentic_workflow_integration_readback"]

    assert calls == []
    assert readback["safety"]["provider_call_performed_by_integration"] is False
    assert readback["safety"]["llm_call_performed_by_integration"] is False
    assert readback["safety"]["network_call_performed_by_integration"] is False


def test_no_ats_submission_or_apply_queue_enqueue(monkeypatch):
    payload = _build_scan(monkeypatch)
    readback = payload["agentic_workflow_integration_readback"]

    assert readback["ats_automation_performed"] is False
    assert readback["application_submission_performed"] is False
    assert readback["apply_queue_enqueued"] is False
    assert readback["safety"]["ats_automation_performed"] is False
    assert readback["safety"]["application_submission_performed"] is False
    assert readback["safety"]["apply_queue_enqueued"] is False


def test_human_only_handoff_readbacks_remain_intact(monkeypatch):
    payload = _service_payload_with_workflow_checkpoint(monkeypatch)
    readback = payload["agentic_workflow_integration_readback"]
    handoff = readback["human_only_handoff_readbacks"]

    assert handoff["operator_approved_artifact_application_readiness_packet_readback"][
        "phase"
    ] == "63A"
    assert handoff["human_only_manual_application_handoff_packet_readback"]["phase"] == "64A"
    assert handoff["human_only_handoff_audit_trail_readback"]["phase"] == "65A"
    assert handoff["human_only_safety_boundary_summary_readback"]["phase"] == "66A"
    assert handoff["human_only_workflow_readiness_checkpoint_readback"]["phase"] == "67A"
    assert handoff["human_only_workflow_readiness_checkpoint_readback"][
        "workflow_readiness_checkpoint_created"
    ] is True


def test_no_scoring_formula_or_weight_changes(monkeypatch):
    payload = _build_scan(monkeypatch)
    readback = payload["agentic_workflow_integration_readback"]

    assert readback["safety"]["scoring_formula_changed"] is False
    assert readback["safety"]["scoring_weights_changed"] is False


def test_ui_readback_display_uses_existing_response_data_and_is_passive():
    script = (ROOT / "src/app/static/scan_workspace.js").read_text(encoding="utf-8")
    getter = script.split(
        "function getScanWorkspaceAgenticWorkflowIntegrationPayload",
        1,
    )[1].split(
        "function renderScanWorkspaceAgenticWorkflowIntegrationReadback",
        1,
    )[0]
    renderer = script.split(
        "function renderScanWorkspaceAgenticWorkflowIntegrationReadback",
        1,
    )[1].split(
        "function getScanWorkspaceHasTailoringPreviewContext",
        1,
    )[0]

    assert "agentic_workflow_integration_readback" in getter
    assert "agentic_workflow_integration_enabled" in renderer
    assert "user_started_scan_or_evaluation" in renderer
    assert "core_llm_inference_workflow_automatic" in renderer
    assert "jd_signal_extraction_available" in renderer
    assert "resume_evidence_available" in renderer
    assert "scoring_ranking_available" in renderer
    assert "planning_workspace_next_actions_available" in renderer
    assert "manual_mutation_requires_operator_action" in renderer
    assert "ats_automation_performed" in renderer
    assert "application_submission_performed" in renderer
    assert "apply_queue_enqueued" in renderer
    assert "build_end_to_end_agentic_workflow_integration_readback" not in renderer
    assert "fetch(" not in renderer
    assert "postJsonWithTimeout" not in renderer


def test_protected_files_are_unchanged():
    for relative, expected in PROTECTED_HASHES.items():
        assert _sha256(ROOT / relative) == expected
    assert _sha256(ROOT / "src/matching/scorer.py") == PROTECTED_HASHES[
        "src/matching/scorer.py"
    ]
    assert _sha256(ROOT / "src/matching/prefilter.py") == PROTECTED_HASHES[
        "src/matching/prefilter.py"
    ]


def test_docs_include_phase68_agentic_workflow_markers():
    text = DOC_PATH.read_text(encoding="utf-8").lower()
    for marker in (
        "end-to-end agentic workflow integration",
        "user-started scan/evaluation",
        "workflow-automatic core llm inference",
        "jd signal extraction",
        "skills extraction",
        "resume evidence",
        "scoring/ranking readback",
        "planning workspace next actions",
        "manual mutation requires operator action",
        "human-only application boundary",
        "no live llm call in tests",
        "no resume artifact creation",
        "no source resume overwrite",
        "no ats automation",
        "no application submission",
        "no auto-apply",
    ):
        assert marker in text
