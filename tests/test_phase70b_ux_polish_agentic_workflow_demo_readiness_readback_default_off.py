from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from tests.support.phase_guard_registry import assert_protected_hashes


ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = (
    ROOT
    / "docs/phase70_ux_polish_agentic_workflow_demo_readiness_readback_default_off.md"
)
SCAN_WORKSPACE_JS = ROOT / "src/app/static/scan_workspace.js"
PLANNING_UI = ROOT / "src/app/planning_ui.py"
PROTECTED_HASHES = {
    "src/app/api.py": "d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004",
    "src/app/services.py": "bfa035faa8e89abd2b75095f68b45a282fb3b7fc8e5ff43e36c754db56ef12c2",
    "src/matching/scorer.py": "f56624b5b3c7e2bb01a824386b86fbc2a194e727f0437ca0773764eae64ec941",
    "src/matching/dimensions.py": "3ccd5e87b9a8aee7901b3efb5ef7582b0fd652aa498f862d0486fbbd97740b9b",
    "application_execution_" + "queue" + ".py": (
        "c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0"
    ),
    "generate_tailoring_" + "suggestions" + ".py": (
        "2422452d1c7a54777684b399730d02c11e58ce1ad6ac5658527ad71bb9050f28"
    ),
}


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _agentic_renderer() -> str:
    script = SCAN_WORKSPACE_JS.read_text(encoding="utf-8")
    return script.split(
        "function renderScanWorkspaceAgenticWorkflowIntegrationReadback",
        1,
    )[1].split("function getScanWorkspaceProductionReadinessCheckpointPayload", 1)[0]


def _production_renderer() -> str:
    script = SCAN_WORKSPACE_JS.read_text(encoding="utf-8")
    return script.split(
        "function renderScanWorkspaceProductionReadinessCheckpoint",
        1,
    )[1].split("function getScanWorkspaceHasTailoringPreviewContext", 1)[0]


def test_final_demo_readiness_readback_labels_are_visible():
    html = PLANNING_UI.read_text(encoding="utf-8")
    script = SCAN_WORKSPACE_JS.read_text(encoding="utf-8")

    assert "Agentic workflow demo readiness" in html
    assert "Demo readiness: backend checkpoint readback" in html
    assert "demo-ready scan/evaluation connected" in script
    assert "backend agentic workflow complete" in script
    assert "ready for UX polish / demo readiness" in script


def test_ux_readback_polish_uses_existing_fields_only():
    renderer = _agentic_renderer() + _production_renderer()

    for field in (
        "user_started_scan_or_evaluation",
        "core_llm_inference_workflow_automatic",
        "jd_signal_extraction_available",
        "skills_extraction_available",
        "resume_evidence_available",
        "scoring_ranking_available",
        "planning_workspace_next_actions_available",
        "tailoring_suggestion_action_available",
        "exact_change_proposal_action_available",
        "guarded_resume_artifact_path_available",
        "artifact_verification_path_available",
        "human_only_handoff_path_available",
        "backend_agentic_workflow_complete",
        "workflow_ready_for_ux_polish",
    ):
        assert field in renderer


def test_workflow_automatic_and_manual_only_wording_are_visible():
    renderer = _agentic_renderer() + _production_renderer()

    assert "analysis automation: workflow-automatic core LLM inference" in renderer
    assert "manual-only mutation: operator action required before any resume change" in renderer
    assert "human-only handoff/application boundary" in renderer
    assert "ApplyLens never applies for jobs" in renderer


def test_final_action_path_labels_are_human_readable():
    renderer = _agentic_renderer() + _production_renderer()

    for label in (
        "JD signal extraction",
        "skills extraction",
        "resume evidence",
        "scoring/ranking readback",
        "planning workspace next actions",
        "tailoring suggestion action: explicit manual next action",
        "exact change proposal action: explicit manual next action",
        "guarded resume artifact path: explicit manual/operator path",
        "artifact verification path: explicit manual/operator path",
        "human-only handoff path",
    ):
        assert label in renderer


def test_safe_states_are_clear_without_dominating_the_readback():
    renderer = _agentic_renderer() + _production_renderer()

    assert "safe: no ATS automation" in renderer
    assert "safe: no application submission" in renderer
    assert "safe: no apply queue enqueue" in renderer
    assert "attention: ATS automation reported" in renderer
    assert "attention: application submission reported" in renderer
    assert "attention: apply queue enqueue reported" in renderer


def test_ui_polish_does_not_call_backend_or_create_artifacts():
    renderer = _agentic_renderer() + _production_renderer()

    assert "fetch(" not in renderer
    assert "postJsonWithTimeout" not in renderer
    assert "build_agentic_workflow_production_readiness_checkpoint" not in renderer
    assert "create_saved_scan_payload" not in renderer
    assert "resume_artifact_created = true" not in renderer


def test_phase70a_readback_behavior_remains_intact():
    script = SCAN_WORKSPACE_JS.read_text(encoding="utf-8")

    assert "Agentic workflow demo readiness" in script
    assert "Demo readiness:" in script
    assert "agentic_workflow_integration_readback" in script
    assert "agentic_workflow_production_readiness_checkpoint" in script


def test_no_backend_workflow_or_scoring_files_changed():
    assert_protected_hashes(
        ROOT,
        PROTECTED_HASHES,
        compatibility_profiles=(
            "phase129c_workflow_overlay_and_run_scoped_corpus",
        ),
    )


def test_docs_include_phase70b_markers():
    text = DOC_PATH.read_text(encoding="utf-8").lower()
    for marker in (
        "ux polish readback",
        "agentic workflow demo readiness",
        "existing readback fields",
        "user-started scan/evaluation",
        "workflow-automatic core llm inference",
        "planning workspace next actions",
        "manual-only mutation",
        "human-only handoff",
        "backend agentic workflow complete",
        "ready for ux polish",
        "no backend workflow change",
        "no live llm call in tests",
        "no resume artifact creation",
        "no source resume overwrite",
        "no ats automation",
        "no application submission",
        "no auto-apply",
    ):
        assert marker in text
