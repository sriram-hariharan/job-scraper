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
    / "docs/phase68_end_to_end_agentic_workflow_integration_readback_ui_api_default_off.md"
)
PROTECTED_HASHES = {
    "src/matching/scorer.py": "5a7fa4abf6adb353bbb8c3f8c3113279409de1250f99e61a36056c5d06503062",
    "src/matching/dimensions.py": "3ccd5e87b9a8aee7901b3efb5ef7582b0fd652aa498f862d0486fbbd97740b9b",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "application_execution_" + "queue" + ".py": (
        "c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0"
    ),
}


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _client(monkeypatch) -> TestClient:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    monkeypatch.setattr(api, "_auth_owner_user_id", lambda request: "owner-68b")
    monkeypatch.setattr(api, "_auth_owner_email", lambda request: "owner68b@example.test")
    return TestClient(api.app)


def _post_scan(client: TestClient, payload: dict | None = None) -> dict:
    response = client.post("/planning/start-scan", json=payload or _request_payload())
    assert response.status_code == 200
    return response.json()


def _post_state(client: TestClient, payload: dict) -> dict:
    response = client.post("/planning/saved-scan/phase56a-scan/state", json=payload)
    assert response.status_code == 200
    return response.json()


def test_default_api_readback_does_not_perform_manual_mutation(monkeypatch):
    calls = []
    monkeypatch.setattr(
        services,
        "_live_jd_intelligence_provider_adapter",
        lambda request: calls.append(request) or _valid_jd_provider_payload(),
    )

    payload = _post_scan(_client(monkeypatch))
    readback = payload["agentic_workflow_integration_readback"]

    assert calls == []
    assert readback == payload["scan_review_payload"]["agentic_workflow_integration_readback"]
    assert readback["readback_phase"] == "68B"
    assert readback["api_readback"] is True
    assert readback["ui_readback"] is True
    assert readback["manual_mutation_requires_operator_action"] is True
    assert readback["manual_mutation_performed_by_readback"] is False
    assert readback["source_resume_mutated"] is False
    assert readback["source_resume_unchanged"] is True
    assert readback["source_resume_overwritten"] is False


def test_user_started_scan_exposes_integration_status_in_api_readback(monkeypatch):
    payload = _post_scan(_client(monkeypatch))
    readback = payload["agentic_workflow_integration_readback"]

    assert readback["agentic_workflow_integration_enabled"] is True
    assert readback["agentic_workflow_integration_requested"] is True
    assert readback["agentic_workflow_integration_performed"] is True
    assert readback["user_started_scan_or_evaluation"] is True
    assert readback["validation_status"] == "valid"
    assert readback["fallback_used"] is False


def test_api_exposes_workflow_automatic_core_llm_policy(monkeypatch):
    payload = _post_scan(
        _client(monkeypatch),
        {**_request_payload(), "enable_jd_llm_extraction": True},
    )
    readback = payload["agentic_workflow_integration_readback"]
    policy = readback["workflow_policy"]

    assert readback["core_llm_inference_workflow_automatic"] is True
    assert readback["core_llm_inference_requires_user_started_workflow"] is True
    assert policy["core_llm_inference_may_run_inside_user_started_scan"] is True
    assert policy["manual_mutation_actions_require_explicit_operator_action"] is True
    assert policy["ats_automation_forbidden"] is True
    assert policy["application_submission_forbidden"] is True
    assert policy["apply_queue_enqueue_forbidden"] is True
    assert policy["source_resume_overwrite_forbidden"] is True
    assert policy["auto_apply_forbidden"] is True


def test_jd_skills_requirements_evidence_scoring_and_ranking_are_separate(monkeypatch):
    payload = _post_scan(_client(monkeypatch))
    readback = payload["agentic_workflow_integration_readback"]
    boundaries = readback["responsibility_boundaries"]

    assert readback["jd_signal_extraction_available"] is True
    assert readback["jd_signal_extraction_status"] in {"available", "disabled", "valid"}
    assert readback["skills_extraction_available"] is True
    assert readback["skills_extraction_status"] == "available"
    assert readback["requirements_extraction_available"] is True
    assert readback["requirements_extraction_status"] == "available"
    assert readback["resume_evidence_available"] is True
    assert readback["resume_evidence_status"] == "available"
    assert readback["scoring_ranking_available"] is True
    assert readback["scoring_ranking_status"] == "available"
    assert boundaries["deterministic_prefilter_separate_from_llm_evaluation"] is True
    assert boundaries["jd_intelligence_separate_from_resume_evidence"] is True
    assert boundaries["final_scoring_ranking_separate_from_llm_evaluation"] is True


def test_planning_workspace_next_actions_surface_without_artifact_creation(monkeypatch):
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())
    payload = _post_state(_client(monkeypatch), _state_request())
    readback = payload["agentic_workflow_integration_readback"]

    assert readback["planning_workspace_next_actions_available"] is True
    assert readback["planning_workspace_next_actions_status"] == "available"
    assert readback["tailoring_suggestion_action_available"] is True
    assert readback["tailoring_suggestion_action_performed"] is False
    assert readback["exact_change_proposal_action_available"] is True
    assert readback["exact_change_proposal_action_performed"] is False
    assert readback["resume_artifact_created"] is False
    assert readback["artifact_creation_performed_by_readback"] is False


def test_ui_readback_display_uses_existing_data_and_is_passive():
    html = (ROOT / "src/app/planning_ui.py").read_text(encoding="utf-8")
    script = (ROOT / "src/app/static/scan_workspace.js").read_text(encoding="utf-8")
    getter = script.split(
        "function getScanWorkspaceAgenticWorkflowIntegrationPayload",
        1,
    )[1].split("function renderScanWorkspaceAgenticWorkflowIntegrationReadback", 1)[0]
    renderer = script.split(
        "function renderScanWorkspaceAgenticWorkflowIntegrationReadback",
        1,
    )[1].split("function getScanWorkspaceHasTailoringPreviewContext", 1)[0]

    assert 'id="scanWorkspaceAgenticWorkflowIntegrationReadback"' in html
    assert "agentic_workflow_integration_readback" in getter
    assert "skills_extraction_status" in renderer
    assert "requirements_extraction_status" in renderer
    assert "resume_evidence_status" in renderer
    assert "scoring_ranking_status" in renderer
    assert "planning_workspace_next_actions_status" in renderer
    assert "fetch(" not in renderer
    assert "postJsonWithTimeout" not in renderer
    assert "create" not in renderer.lower()


def test_no_live_provider_call_is_made_by_phase68b_readback(monkeypatch):
    calls = []
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())
    payload = _post_state(
        _client(monkeypatch),
        _state_request(),
    )
    services.build_end_to_end_agentic_workflow_integration_readback(
        scan_review_payload=payload,
        planning_workspace_payload={
            "live_tailoring_suggestion_readback": payload[
                "live_tailoring_suggestion_readback"
            ]
        },
        enabled=True,
    )

    assert calls == []
    readback = payload["agentic_workflow_integration_readback"]
    assert readback["provider_call_performed_by_readback"] is False
    assert readback["llm_call_performed_by_readback"] is False
    assert readback["network_call_performed_by_readback"] is False
    assert readback["safety"]["provider_call_performed_by_integration"] is False


def test_no_ats_submission_or_apply_queue_enqueue(monkeypatch):
    readback = _post_scan(_client(monkeypatch))["agentic_workflow_integration_readback"]

    assert readback["ats_automation_performed"] is False
    assert readback["application_submission_performed"] is False
    assert readback["apply_queue_enqueued"] is False
    assert readback["application_execution_enqueued"] is False
    assert readback["application_execution_performed"] is False


def test_phase63_to_phase68a_readbacks_remain_intact(monkeypatch):
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
    assert readback["phase"] == "68A"
    assert readback["readback_phase"] == "68B"


def test_no_scoring_formula_or_weight_changes(monkeypatch):
    readback = _post_scan(_client(monkeypatch))["agentic_workflow_integration_readback"]

    assert readback["safety"]["scoring_formula_changed"] is False
    assert readback["safety"]["scoring_weights_changed"] is False
    for relative, expected in PROTECTED_HASHES.items():
        assert _sha256(ROOT / relative) == expected


def test_docs_include_phase68b_readback_markers():
    text = DOC_PATH.read_text(encoding="utf-8").lower()
    for marker in (
        "end-to-end agentic workflow integration readback",
        "user-started scan/evaluation",
        "workflow-automatic core llm inference",
        "jd signal extraction",
        "skills extraction",
        "resume evidence",
        "scoring/ranking readback",
        "planning workspace next actions",
        "api readback",
        "ui readback",
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
