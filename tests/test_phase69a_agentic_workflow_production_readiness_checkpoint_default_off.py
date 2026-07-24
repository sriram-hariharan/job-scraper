from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services
from tests.test_phase55a_live_jd_llm_extraction_planning_scan_wiring_default_off import (
    _request_payload,
    _valid_provider_payload as _valid_jd_provider_payload,
)
from tests.test_phase56a_live_tailoring_suggestion_planning_workspace_wiring_default_off import (
    _patch_storage,
    _state_request,
    _stored_scan_payload,
)
from tests.test_phase67a_human_only_workflow_readiness_checkpoint_wiring_default_off import (
    _service_payload_with_workflow_checkpoint,
)


ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = (
    ROOT
    / "docs/phase69_agentic_workflow_production_readiness_checkpoint_default_off.md"
)
PROTECTED_HASHES = {
    "src/matching/scorer.py": "f56624b5b3c7e2bb01a824386b86fbc2a194e727f0437ca0773764eae64ec941",
    "src/matching/dimensions.py": "3ccd5e87b9a8aee7901b3efb5ef7582b0fd652aa498f862d0486fbbd97740b9b",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "application_execution_" + "queue" + ".py": (
        "28ac5d153eeb1d3e6238bed57418a45b603f72caea6c0f671a8dcbb3b0a76097"
    ),
}


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _client(monkeypatch) -> TestClient:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    monkeypatch.setattr(api, "_auth_owner_user_id", lambda request: "owner-69a")
    monkeypatch.setattr(api, "_auth_owner_email", lambda request: "owner69a@example.test")
    return TestClient(api.app)


def _post_scan(client: TestClient, payload: dict | None = None) -> dict:
    response = client.post("/planning/start-scan", json=payload or _request_payload())
    assert response.status_code == 200
    return response.json()


def _post_state(client: TestClient, payload: dict | None = None) -> dict:
    response = client.post(
        "/planning/saved-scan/phase56a-scan/state",
        json=payload or _state_request(),
    )
    assert response.status_code == 200
    return response.json()


def test_default_readback_does_not_perform_manual_mutation(monkeypatch):
    payload = _post_scan(_client(monkeypatch))
    checkpoint = payload["agentic_workflow_production_readiness_checkpoint"]

    assert checkpoint["phase"] == "69A"
    assert checkpoint["production_readiness_checkpoint_performed"] is True
    assert checkpoint["manual_mutation_requires_operator_action"] is True
    assert checkpoint["manual_mutation_performed_by_checkpoint"] is False
    assert checkpoint["source_resume_unchanged"] is True
    assert checkpoint["source_resume_mutated"] is False
    assert checkpoint["source_resume_overwritten"] is False
    assert checkpoint["resume_artifact_created"] is False


def test_checkpoint_exposes_completed_agentic_workflow_status(monkeypatch):
    payload = _post_scan(_client(monkeypatch))
    checkpoint = payload["agentic_workflow_production_readiness_checkpoint"]

    assert checkpoint == payload["scan_review_payload"][
        "agentic_workflow_production_readiness_checkpoint"
    ]
    assert checkpoint["production_readiness_checkpoint_enabled"] is True
    assert checkpoint["production_readiness_checkpoint_requested"] is True
    assert checkpoint["agentic_workflow_integration_available"] is True
    assert checkpoint["user_started_scan_or_evaluation"] is True
    assert checkpoint["validation_status"] == "valid"
    assert checkpoint["fallback_used"] is False
    assert checkpoint["workflow_ready_for_ux_polish"] is True


def test_core_llm_inference_is_workflow_automatic_inside_user_started_scan(
    monkeypatch,
):
    monkeypatch.setattr(
        services,
        "_live_jd_intelligence_provider_adapter",
        lambda _request: _valid_jd_provider_payload(),
    )
    payload = _post_scan(
        _client(monkeypatch),
        {**_request_payload(), "enable_jd_llm_extraction": True},
    )
    checkpoint = payload["agentic_workflow_production_readiness_checkpoint"]

    assert checkpoint["core_llm_inference_workflow_automatic"] is True
    assert checkpoint["jd_signal_extraction_available"] is True
    assert checkpoint["llm_evaluation_available"] is True
    assert checkpoint["agentic_workflow_integration_readback"][
        "jd_signal_extraction_performed"
    ] is True


def test_jd_skills_requirements_evidence_scoring_are_separate(monkeypatch):
    checkpoint = _post_scan(_client(monkeypatch))[
        "agentic_workflow_production_readiness_checkpoint"
    ]
    boundaries = checkpoint["responsibility_boundaries"]

    assert checkpoint["jd_signal_extraction_available"] is True
    assert checkpoint["skills_extraction_available"] is True
    assert checkpoint["requirements_extraction_available"] is True
    assert checkpoint["resume_evidence_available"] is True
    assert checkpoint["scoring_ranking_available"] is True
    assert boundaries["scan_flow_stays_in_scan_path"] is True
    assert boundaries["deterministic_prefilter_separate_from_llm_evaluation"] is True
    assert boundaries["jd_intelligence_separate_from_resume_evidence"] is True
    assert boundaries["final_scoring_ranking_separate_from_llm_evaluation"] is True
    assert boundaries["manual_mutation_handoff_separate_from_analysis_automation"] is True


def test_planning_next_actions_without_artifact_creation(monkeypatch):
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())
    payload = _post_state(_client(monkeypatch))
    checkpoint = payload["agentic_workflow_production_readiness_checkpoint"]

    assert checkpoint["planning_workspace_next_actions_available"] is True
    assert checkpoint["tailoring_suggestion_action_available"] is True
    assert checkpoint["exact_change_proposal_action_available"] is True
    assert checkpoint["resume_artifact_created"] is False
    assert checkpoint["artifact_creation_performed_by_checkpoint"] is False


def test_guarded_artifact_verification_and_handoff_paths_are_explicit(monkeypatch):
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())
    checkpoint = _post_state(_client(monkeypatch))[
        "agentic_workflow_production_readiness_checkpoint"
    ]

    assert checkpoint["guarded_resume_artifact_path_available"] is True
    assert checkpoint["artifact_verification_path_available"] is True
    assert checkpoint["human_only_handoff_path_available"] is True
    assert checkpoint["explicit_operator_paths"]["guarded_resume_artifact_path"] is True
    assert checkpoint["explicit_operator_paths"]["artifact_verification_path"] is True
    assert checkpoint["explicit_operator_paths"]["human_only_handoff_path"] is True
    assert checkpoint["ats_automation_performed"] is False


def test_no_live_provider_call_is_made_by_checkpoint(monkeypatch):
    calls = []
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())
    monkeypatch.setattr(
        services,
        "_live_tailoring_suggestion_provider_adapter",
        lambda request: calls.append(request),
    )
    monkeypatch.setattr(
        services,
        "_live_exact_resume_change_proposal_provider_adapter",
        lambda request: calls.append(request),
        raising=False,
    )

    payload = _post_state(_client(monkeypatch))
    checkpoint = payload["agentic_workflow_production_readiness_checkpoint"]

    assert calls == []
    assert checkpoint["provider_call_performed_by_checkpoint"] is False
    assert checkpoint["llm_call_performed_by_checkpoint"] is False
    assert checkpoint["network_call_performed_by_checkpoint"] is False


def test_no_ats_submission_or_apply_queue_enqueue(monkeypatch):
    checkpoint = _post_scan(_client(monkeypatch))[
        "agentic_workflow_production_readiness_checkpoint"
    ]

    assert checkpoint["ats_automation_performed"] is False
    assert checkpoint["application_submission_performed"] is False
    assert checkpoint["apply_queue_enqueued"] is False
    assert checkpoint["application_execution_enqueued"] is False
    assert checkpoint["application_execution_performed"] is False


def test_prior_phase_readbacks_remain_intact(monkeypatch):
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())
    state_payload = _post_state(_client(monkeypatch))
    workflow_payload = _service_payload_with_workflow_checkpoint(monkeypatch)

    assert state_payload["live_tailoring_suggestion_readback"]["phase"] in {"56A", "56B"}
    assert state_payload["guarded_resume_copy_artifact_readback"]["phase"] in {
        "59A",
        "59B",
    }
    assert state_payload["guarded_resume_copy_artifact_verification_readback"][
        "phase"
    ] in {"60A", "60B"}
    assert workflow_payload["human_only_workflow_readiness_checkpoint_readback"][
        "phase"
    ] in {"67A", "67B"}
    assert workflow_payload["agentic_workflow_integration_readback"]["phase"] == "68A"
    assert workflow_payload["agentic_workflow_production_readiness_checkpoint"][
        "phase"
    ] == "69A"


def test_ui_checkpoint_display_is_passive():
    # id="scanWorkspaceProductionReadinessCheckpointReadback" moved from
    # src/app/planning_ui.py into the React Advanced Diagnostics Command
    # Center (Item 1 Phase 3).
    html = (
        ROOT / "frontend/executive-kpi/src/diagnostics/AdvancedDiagnosticsDashboard.tsx"
    ).read_text(encoding="utf-8")
    script = (ROOT / "src/app/static/scan_workspace.js").read_text(encoding="utf-8")
    getter = script.split(
        "function getScanWorkspaceProductionReadinessCheckpointPayload",
        1,
    )[1].split("function renderScanWorkspaceProductionReadinessCheckpoint", 1)[0]
    renderer = script.split(
        "function renderScanWorkspaceProductionReadinessCheckpoint",
        1,
    )[1].split("function getScanWorkspaceHasTailoringPreviewContext", 1)[0]

    assert '"scanWorkspaceProductionReadinessCheckpointReadback"' in html
    assert "agentic_workflow_production_readiness_checkpoint" in getter
    assert "production_readiness_checkpoint_performed" in renderer
    assert "workflow_ready_for_ux_polish" in renderer
    assert "guarded_resume_artifact_path_available" in renderer
    assert "artifact_verification_path_available" in renderer
    assert "human_only_handoff_path_available" in renderer
    assert "fetch(" not in renderer
    assert "postJsonWithTimeout" not in renderer


def test_no_scoring_formula_or_weight_changes():
    for relative, expected in PROTECTED_HASHES.items():
        assert _sha256(ROOT / relative) == expected


def test_docs_include_phase69_markers():
    text = DOC_PATH.read_text(encoding="utf-8").lower()
    for marker in (
        "agentic workflow production readiness checkpoint",
        "end-to-end agentic workflow integration",
        "user-started scan/evaluation",
        "workflow-automatic core llm inference",
        "jd signal extraction",
        "skills extraction",
        "resume evidence",
        "scoring/ranking readback",
        "planning workspace next actions",
        "explicit manual mutation path",
        "guarded resume artifact path",
        "artifact verification path",
        "human-only handoff path",
        "ready for ux polish",
        "no live llm call in tests",
        "no resume artifact creation",
        "no source resume overwrite",
        "no ats automation",
        "no application submission",
        "no auto-apply",
    ):
        assert marker in text
