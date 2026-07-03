from __future__ import annotations

from hashlib import sha256
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = ROOT / "docs/phase70_ux_polish_agentic_workflow_demo_readiness_default_off.md"
SCAN_WORKSPACE_JS = ROOT / "src/app/static/scan_workspace.js"
PLANNING_UI = ROOT / "src/app/planning_ui.py"
PROTECTED_HASHES = {
    "src/app/api.py": "85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96",
    "src/app/services.py": "f186703fecdda54458c468f9c2ed1de0517fa86942bb3d0fe0b522f0601fe5a8",
    "src/matching/scorer.py": "c3f0b1f4a938ca933b10991af1ddb0aca2790136c7c6b487a8ee79556ee5ceac",
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


def test_demo_readiness_labels_are_present():
    html = PLANNING_UI.read_text(encoding="utf-8")
    script = SCAN_WORKSPACE_JS.read_text(encoding="utf-8")

    assert "Agentic workflow demo readiness" in html
    assert "Demo readiness: backend checkpoint" in html
    assert "Agentic workflow demo readiness" in script
    assert "Demo readiness:" in script


def test_ux_polish_uses_existing_readback_fields():
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


def test_human_readable_workflow_and_demo_readiness_wording_is_visible():
    renderer = _agentic_renderer() + _production_renderer()

    for label in (
        "user-started scan/evaluation",
        "analysis automation: workflow-automatic core LLM inference",
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
        "backend agentic workflow complete",
        "ready for UX polish",
    ):
        assert label in renderer


def test_manual_only_and_human_only_boundary_wording_is_visible():
    renderer = _agentic_renderer() + _production_renderer()

    assert "manual-only mutation: operator action required" in renderer
    assert "human-only handoff/application boundary" in renderer
    assert "ApplyLens never applies for jobs" in renderer


def test_safe_forbidden_states_are_readable_without_implying_failure():
    renderer = _agentic_renderer() + _production_renderer()

    assert "safe: no ATS automation" in renderer
    assert "safe: no application submission" in renderer
    assert "safe: no apply queue enqueue" in renderer
    assert "source resume" in renderer


def test_ui_readback_does_not_create_artifacts_or_call_backends():
    renderer = _agentic_renderer() + _production_renderer()

    assert "fetch(" not in renderer
    assert "postJsonWithTimeout" not in renderer
    assert "create_saved_scan_payload" not in renderer
    assert "build_agentic_workflow_production_readiness_checkpoint" not in renderer
    assert "resume_artifact_created = true" not in renderer


def test_phase68_and_phase69_readback_renderers_remain_intact():
    script = SCAN_WORKSPACE_JS.read_text(encoding="utf-8")

    assert "agentic_workflow_integration_readback" in script
    assert "agentic_workflow_production_readiness_checkpoint" in script
    assert "renderScanWorkspaceAgenticWorkflowIntegrationReadback" in script
    assert "renderScanWorkspaceProductionReadinessCheckpoint" in script


def test_no_backend_workflow_or_scoring_files_changed():
    for relative, expected in PROTECTED_HASHES.items():
        assert _sha256(ROOT / relative) == expected


def test_docs_include_phase70_ux_polish_markers():
    text = DOC_PATH.read_text(encoding="utf-8").lower()
    for marker in (
        "ux polish",
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
