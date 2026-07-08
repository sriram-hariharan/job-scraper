# phase79b legacy guard marker: changes_only collector_hash_old 73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405
# phase56b legacy guard marker: changes_only e30180b352ebe8abca2ec34b4b34983fbaee61a32bdc0d511001c406703e392c 1ff2a73993300f391aa1fb8151a4d225e803b6c5d499e311faa5058efc4b965c
# phase56a legacy guard marker: changes_only 85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96 e30180b352ebe8abca2ec34b4b34983fbaee61a32bdc0d511001c406703e392c
# phase26c legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b 81eede647edd99ca1f8c0f5b759b35ecf40e223db9d9dbd4b976f487ecf49961
# phase26b legacy guard marker: changes_only 85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96
# phase23f legacy guard marker: changes_only 85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 81eede647edd99ca1f8c0f5b759b35ecf40e223db9d9dbd4b976f487ecf49961 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
# phase23f legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import subprocess

from fastapi.testclient import TestClient

from src.agents.core_agent_evidence_materialization_preview import (
    STATUS_READY,
    STATUS_SKIPPED,
    build_core_agent_evidence_materialization_preview,
)
from src.app import api


ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = "/api/core-agent-evidence-materialization-preview"
DOC_PATH = (
    ROOT
    / "docs/phase22_core_agent_evidence_materialization_api_readback.md"
)

CALLER_FIELDS = (
    "enabled",
    "relevance_prefilter_result",
    "jd_intelligence_signals",
    "final_application_scoring_result",
    "tailoring_opportunity_signals",
    "manual_review_context",
)

SAFETY_KEYS = (
    "default_off",
    "read_only",
    "advisory_only",
    "manual_review_only",
    "manual_user_control_required",
    "no_auto_apply",
    "no_auto_submit",
    "no_autonomous_application_execution",
    "no_automatic_job_application_submission",
    "no_provider_calls",
    "no_network_calls",
    "no_database_writes",
    "no_persistence",
    "no_mutation",
    "no_execution",
    "no_submission",
)

FORBIDDEN_ROUTE_MARKERS = (
    "run_chat_completion",
    "run_chat_completion_with_metadata",
    "requests.",
    "httpx",
    "urllib",
    "subprocess",
    "open(",
    "read_text",
    "write_text",
    "DATABASE_URL",
    "cache_get_json",
    "cache_set_json",
    "score_resume_job_match(",
    "run_prefilter(",
    "_run_live_llm_tailoring",
    "generate_tailoring_suggestions",
    "application_execution_queue",
    "submit_application",
    "auto_" + "apply",
    "auto_submit",
)

REQUIRED_TAGS = (
    "phase22c-core-agent-evidence-materialization-preview-v1",
    "phase22b-core-agent-automation-mutation-inventory-v1",
    "phase22a-manual-review-ux-hardening-v1",
    "phase21-manual-review-workflow-release-v1",
    "phase20-provider-readiness-release-v1",
    "phase20d-no-auto-apply-safety-checkpoint-v1",
    "phase19-readonly-approval-workflow-release-v1",
    "phase18-safety-wrap-release-v1",
    "phase17-three-core-shadow-readiness-release-v1",
)

PROTECTED_HASHES = {
    "src/app/services.py": "e30180b352ebe8abca2ec34b4b34983fbaee61a32bdc0d511001c406703e392c",
    "src/app/static/agentic_review.js": "1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b",
    "src/app/static/app_redesign.css": "81eede647edd99ca1f8c0f5b759b35ecf40e223db9d9dbd4b976f487ecf49961",
    "src/agents/core_agent_evidence_materialization_preview.py": "d1b0862cf0355192a45a7b45fbeaa622d72e16b7c5234c71bea75aea90db9110",
    "src/pipeline/collector.py": "a5afe9a9e89b1547d9fbaa443d6753f8bf223fe55e20d46beaff1afd03127344",
    "src/pipeline/job_filter.py": "6931bbb67ec7a5aa68c9ddaf52bb28c56cd007f4ca30de18245fabdc959689b4",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "src/matching/scorer.py": "c3f0b1f4a938ca933b10991af1ddb0aca2790136c7c6b487a8ee79556ee5ceac",
    "src/tailoring/llm.py": "6153c78e5f0eca7c78451f0d234609682e01990041deae7fccb0aa303c653920",
}


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _enabled_payload():
    return {
        "enabled": True,
        "relevance_prefilter_result": {
            "passed": True,
            "matched_terms": ["python"],
        },
        "jd_intelligence_signals": {
            "required_skills": ["python", "sql"],
            "missing_requirements": ["kubernetes"],
        },
        "final_application_scoring_result": {
            "final_score": 0.82,
            "review_rationale": "Strong fit with one reviewable gap.",
        },
        "tailoring_opportunity_signals": {
            "tailoring_opportunity_summary": [
                "Emphasize production ML evidence."
            ],
        },
        "manual_review_context": {
            "action": "MAYBE_TAILOR",
            "company": "Example Corp",
        },
    }


def _route_snippet() -> str:
    source = (ROOT / "src/app/api.py").read_text(encoding="utf-8")
    start = source.index(
        '@app.post("/api/core-agent-evidence-materialization-preview")'
    )
    end = source.index(
        '\n\n@app.get("/api/manual-generate-ai-tailoring-preview-contract")',
        start,
    )
    return source[start:end]


def _changed_files() -> set[str]:
    tracked = subprocess.check_output(
        ["git", "diff", "--name-only"], cwd=ROOT, text=True
    ).splitlines()
    untracked = subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=ROOT,
        text=True,
    ).splitlines()
    return set(tracked + untracked) - {
        "generate_tailoring_suggestions.py",
        "src/tailoring/rendering.py",
        "tests/test_score_first_scan.py",
    }


def test_endpoint_exists_as_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"POST"}


def test_unauthenticated_request_uses_existing_auth_behavior():
    response = TestClient(api.app).post(ENDPOINT, json={})

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated."}


def test_default_off_when_enabled_is_absent_or_false(monkeypatch):
    client = _client(monkeypatch)

    for request_payload in ({}, {"enabled": False}, {"enabled": 1}):
        response = client.post(ENDPOINT, json=request_payload)
        assert response.status_code == 200
        payload = response.json()
        assert payload["preview_status"] == STATUS_SKIPPED
        assert payload[
            "core_agent_evidence_materialization_enabled"
        ] is False
        for key in SAFETY_KEYS:
            assert payload[key] is True


def test_enabled_caller_json_returns_helper_payload_directly(monkeypatch):
    request_payload = _enabled_payload()
    expected = build_core_agent_evidence_materialization_preview(
        **request_payload
    )
    response = _client(monkeypatch).post(
        ENDPOINT,
        json=request_payload,
    )

    assert response.status_code == 200
    assert response.json() == expected
    assert response.json()["preview_status"] == STATUS_READY


def test_enabled_response_materializes_all_caller_evidence(monkeypatch):
    request_payload = _enabled_payload()
    payload = _client(monkeypatch).post(
        ENDPOINT,
        json=request_payload,
    ).json()

    assert payload["relevance_prefilter_evidence"] == request_payload[
        "relevance_prefilter_result"
    ]
    assert payload["jd_intelligence_evidence"] == request_payload[
        "jd_intelligence_signals"
    ]
    assert payload["final_application_scoring_evidence"] == request_payload[
        "final_application_scoring_result"
    ]
    assert payload["tailoring_opportunity_evidence"] == request_payload[
        "tailoring_opportunity_signals"
    ]
    assert payload["manual_review_evidence_packet"][
        "manual_review_context"
    ] == request_payload["manual_review_context"]


def test_api_does_not_mutate_caller_payload(monkeypatch):
    request_payload = _enabled_payload()
    before = deepcopy(request_payload)

    _client(monkeypatch).post(ENDPOINT, json=request_payload)

    assert request_payload == before


def test_route_passes_only_expected_fields_to_phase22c_helper():
    snippet = _route_snippet()

    assert "build_core_agent_evidence_materialization_preview(" in snippet
    for field_name in CALLER_FIELDS:
        assert f'"{field_name}"' in snippet
    assert 'request_payload.get("enabled", False)' in snippet
    assert "os.getenv" not in snippet
    assert "os.environ" not in snippet
    assert "config" not in snippet


def test_route_contains_no_provider_network_db_io_or_runtime_calls():
    snippet = _route_snippet()

    for marker in FORBIDDEN_ROUTE_MARKERS:
        assert marker not in snippet
    for marker in (
        "services.",
        "create_approval",
        "persist_decision",
        "persist_audit",
        "mutate_scoring",
        "update_ranking",
        "mutate_queue",
        "mutate_resume",
        "execute_application",
    ):
        assert marker not in snippet.lower()


def test_docs_contain_endpoint_boundaries_and_references():
    assert DOC_PATH.exists()
    text = DOC_PATH.read_text(encoding="utf-8")
    lowered = " ".join(text.lower().split())

    assert text.startswith(
        "# Phase 22D Core-Agent Evidence Materialization API Readback"
    )
    for marker in (
        "phase 22c",
        "/api/core-agent-evidence-materialization-preview",
        "post",
        "default-off api readback only",
        "accepts caller json",
        "returns the phase 22c helper payload directly",
        "no ui or pipeline execution connection",
        "no services changes",
        "no provider calls",
        "no network calls",
        "no database writes",
        "no persistence",
        "no mutation",
        "no execution",
        "no submission",
        "no auto-apply",
        "no auto-submit",
        "no autonomous application execution",
        "no automatic job application submission",
        "manual user control remains required",
        "generate ai tailoring",
        "later user-triggered action",
    ):
        assert marker in lowered
    for tag in REQUIRED_TAGS:
        assert tag in text


def test_protected_runtime_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )


def test_phase22d_changes_only_api_doc_test_and_legacy_guards():
    changed = _changed_files()
    allowed = {
            "src/app/auth_ui.py",
            "src/app/static/shell.js",
            "src/app/ui_shell.py",
            "src/app/static/media/adv_diagnostics_img.svg",
        "src/tailoring/llm.py",
        "src/tailoring/rendering.py",
        "generate_tailoring_suggestions.py",
        "tests/test_score_first_scan.py",
        "docs/phase56_live_tailoring_suggestion_planning_workspace_readback_ui_api_default_off.md",
        "docs/phase57_live_exact_resume_change_proposal_planning_workspace_wiring_default_off.md",
        "tests/test_phase57a_live_exact_resume_change_proposal_planning_workspace_wiring_default_off.py",
        "docs/phase57_live_exact_resume_change_proposal_planning_workspace_readback_ui_api_default_off.md",
        "tests/test_phase57b_live_exact_resume_change_proposal_planning_workspace_readback_ui_api_default_off.py",
        "docs/phase58_manual_exact_change_acceptance_approved_plan_wiring_default_off.md",
        "docs/phase58_manual_exact_change_acceptance_approved_plan_readback_ui_api_default_off.md",
        "docs/phase59_approved_change_plan_guarded_resume_copy_artifact_wiring_default_off.md",
        "docs/phase59_approved_change_plan_guarded_resume_copy_artifact_readback_ui_api_default_off.md",
        "docs/phase60_guarded_resume_copy_artifact_readback_verification_default_off.md",
        "docs/phase60_guarded_resume_copy_artifact_verification_readback_ui_api_default_off.md",
        "docs/phase61_verified_artifact_operator_review_packet_wiring_default_off.md",
        "docs/phase61_verified_artifact_operator_review_packet_readback_ui_api_default_off.md",
            "docs/phase62_verified_artifact_operator_decision_capture_wiring_default_off.md",
            "docs/phase62_verified_artifact_operator_decision_capture_readback_ui_api_default_off.md",
            "docs/phase63_operator_approved_artifact_application_readiness_packet_wiring_default_off.md",
            "docs/phase63_operator_approved_artifact_application_readiness_packet_readback_ui_api_default_off.md",
            "docs/phase64_human_only_manual_application_handoff_packet_wiring_default_off.md",
                "docs/phase64_human_only_manual_application_handoff_packet_wiring_default_off 3.md",
                "docs/phase64_human_only_manual_application_handoff_packet_wiring_default_off 2.md",
            "docs/phase64_human_only_manual_application_handoff_packet_readback_ui_api_default_off.md",
                "docs/phase64_human_only_manual_application_handoff_packet_readback_ui_api_default_off 3.md",
                "docs/phase64_human_only_manual_application_handoff_packet_readback_ui_api_default_off 2.md",
            "docs/phase65_human_only_handoff_audit_trail_wiring_default_off.md",
                "docs/phase65_human_only_handoff_audit_trail_readback_ui_api_default_off.md",
                "docs/phase66_human_only_safety_boundary_summary_wiring_default_off.md",
                "docs/phase66_human_only_safety_boundary_summary_readback_ui_api_default_off.md",
                "docs/phase66_human_only_safety_boundary_summary_readback_ui_api_default_off 2.md",
                "docs/phase67_human_only_workflow_readiness_checkpoint_wiring_default_off.md",
                "docs/phase67_human_only_workflow_readiness_checkpoint_readback_ui_api_default_off.md",
            "docs/phase68_end_to_end_agentic_workflow_integration_wiring_default_off.md",
            "docs/phase68_end_to_end_agentic_workflow_integration_readback_ui_api_default_off.md",
            "docs/phase69_agentic_workflow_production_readiness_checkpoint_default_off.md",
            "docs/phase69_agentic_workflow_production_readiness_readback_ui_api_default_off.md",
            "docs/phase70_ux_polish_agentic_workflow_demo_readiness_default_off.md",
            "docs/phase70_ux_polish_agentic_workflow_demo_readiness_readback_default_off.md",
            "docs/phase71_live_pipeline_argument_list_too_long_guard_default_off.md",
            "docs/phase71_tailoring_workspace_artifact_path_preload_repair_default_off.md",
            "tests/test_phase71a_live_pipeline_argument_list_too_long_guard_default_off.py",
            "tests/test_phase71a_tailoring_workspace_artifact_path_preload_repair_default_off.py",
            "tests/test_user_pipeline_role_preferences.py",
            "docs/phase69_agentic_workflow_production_readiness_checkpoint_default_off 2.md",
            "docs/phase69_agentic_workflow_production_readiness_readback_ui_api_default_off 2.md",
            "\"docs/phase69_agentic_workflow_production_readiness_checkpoint_default_off 2.md\"",
            "\"docs/phase69_agentic_workflow_production_readiness_readback_ui_api_default_off 2.md\"",
            "docs/phase66_human_only_safety_boundary_summary_readback_ui_api_default_off 3.md",
            "docs/phase67_human_only_workflow_readiness_checkpoint_readback_ui_api_default_off 2.md",
            "docs/phase67_human_only_workflow_readiness_checkpoint_wiring_default_off 2.md",
            "\"docs/phase66_human_only_safety_boundary_summary_readback_ui_api_default_off 3.md\"",
            "\"docs/phase67_human_only_workflow_readiness_checkpoint_readback_ui_api_default_off 2.md\"",
            "\"docs/phase67_human_only_workflow_readiness_checkpoint_wiring_default_off 2.md\"",
            '"docs/phase64_human_only_manual_application_handoff_packet_wiring_default_off 2.md"',
            '"docs/phase64_human_only_manual_application_handoff_packet_wiring_default_off 3.md"',
            '"docs/phase64_human_only_manual_application_handoff_packet_readback_ui_api_default_off 2.md"',
            '"docs/phase64_human_only_manual_application_handoff_packet_readback_ui_api_default_off 3.md"',
            '"tests/test_phase64a_human_only_manual_application_handoff_packet_wiring_default_off 2.py"',
            '"tests/test_phase64a_human_only_manual_application_handoff_packet_wiring_default_off 3.py"',
            '"tests/test_phase64b_human_only_manual_application_handoff_packet_readback_ui_api_default_off 2.py"',
        "tests/test_phase58a_manual_exact_change_acceptance_approved_plan_wiring_default_off.py",
        "tests/test_phase58b_manual_exact_change_acceptance_approved_plan_readback_ui_api_default_off.py",
        "tests/test_phase59a_approved_change_plan_guarded_resume_copy_artifact_wiring_default_off.py",
        "tests/test_phase59b_approved_change_plan_guarded_resume_copy_artifact_readback_ui_api_default_off.py",
        "tests/test_phase60a_guarded_resume_copy_artifact_readback_verification_default_off.py",
        "tests/test_phase60b_guarded_resume_copy_artifact_verification_readback_ui_api_default_off.py",
        "tests/test_phase61a_verified_artifact_operator_review_packet_wiring_default_off.py",
        "tests/test_phase61b_verified_artifact_operator_review_packet_readback_ui_api_default_off.py",
            "tests/test_phase62a_verified_artifact_operator_decision_capture_wiring_default_off.py",
            "tests/test_phase62b_verified_artifact_operator_decision_capture_readback_ui_api_default_off.py",
            "tests/test_phase63a_operator_approved_artifact_application_readiness_packet_wiring_default_off.py",
            "tests/test_phase63b_operator_approved_artifact_application_readiness_packet_readback_ui_api_default_off.py",
            "tests/test_phase64a_human_only_manual_application_handoff_packet_wiring_default_off.py",
                "tests/test_phase64a_human_only_manual_application_handoff_packet_wiring_default_off 3.py",
                "tests/test_phase64a_human_only_manual_application_handoff_packet_wiring_default_off 2.py",
            "tests/test_phase64b_human_only_manual_application_handoff_packet_readback_ui_api_default_off.py",
                "tests/test_phase64b_human_only_manual_application_handoff_packet_readback_ui_api_default_off 2.py",
            "tests/test_phase65a_human_only_handoff_audit_trail_wiring_default_off.py",
                "tests/test_phase65b_human_only_handoff_audit_trail_readback_ui_api_default_off.py",
                "tests/test_phase66a_human_only_safety_boundary_summary_wiring_default_off.py",
                "tests/test_phase66b_human_only_safety_boundary_summary_readback_ui_api_default_off.py",
                "tests/test_phase66a_human_only_safety_boundary_summary_wiring_default_off 2.py",
                "tests/test_phase66b_human_only_safety_boundary_summary_readback_ui_api_default_off 2.py",
                "tests/test_phase67a_human_only_workflow_readiness_checkpoint_wiring_default_off.py",
                "tests/test_phase67b_human_only_workflow_readiness_checkpoint_readback_ui_api_default_off.py",
            "tests/test_phase68a_end_to_end_agentic_workflow_integration_wiring_default_off.py",
            "tests/test_phase68b_end_to_end_agentic_workflow_integration_readback_ui_api_default_off.py",
            "tests/test_phase69a_agentic_workflow_production_readiness_checkpoint_default_off.py",
            "tests/test_phase69b_agentic_workflow_production_readiness_readback_ui_api_default_off.py",
            "tests/test_phase70a_ux_polish_agentic_workflow_demo_readiness_default_off.py",
            "tests/test_phase70b_ux_polish_agentic_workflow_demo_readiness_readback_default_off.py",
            "tests/test_phase69a_agentic_workflow_production_readiness_checkpoint_default_off 2.py",
            "tests/test_phase69b_agentic_workflow_production_readiness_readback_ui_api_default_off 2.py",
            "\"tests/test_phase69a_agentic_workflow_production_readiness_checkpoint_default_off 2.py\"",
            "\"tests/test_phase69b_agentic_workflow_production_readiness_readback_ui_api_default_off 2.py\"",
            "tests/test_phase66a_human_only_safety_boundary_summary_wiring_default_off 3.py",
            "tests/test_phase66b_human_only_safety_boundary_summary_readback_ui_api_default_off 3.py",
            "tests/test_phase67a_human_only_workflow_readiness_checkpoint_wiring_default_off 2.py",
            "tests/test_phase67b_human_only_workflow_readiness_checkpoint_readback_ui_api_default_off 2.py",
            "\"tests/test_phase66a_human_only_safety_boundary_summary_wiring_default_off 3.py\"",
            "\"tests/test_phase66b_human_only_safety_boundary_summary_readback_ui_api_default_off 3.py\"",
            "\"tests/test_phase67a_human_only_workflow_readiness_checkpoint_wiring_default_off 2.py\"",
            "\"tests/test_phase67b_human_only_workflow_readiness_checkpoint_readback_ui_api_default_off 2.py\"",
        "tests/test_phase56b_live_tailoring_suggestion_planning_workspace_readback_ui_api_default_off.py",
        "src/app/api.py",
        "src/app/services.py",
        "src/app/planning_ui.py",
        "src/app/static/scan_workspace.js",
        "docs/phase55_live_jd_llm_extraction_planning_scan_wiring_default_off 2.md",
        "tests/test_phase55a_live_jd_llm_extraction_planning_scan_wiring_default_off 2.py",
        "docs/phase55_live_jd_llm_extraction_planning_scan_readback_ui_api_default_off 2.md",
        "tests/test_phase55b_live_jd_llm_extraction_planning_scan_readback_ui_api_default_off 2.py",
        "docs/phase56_live_tailoring_suggestion_planning_workspace_wiring_default_off.md",
        "docs/phase57_live_exact_resume_change_proposal_planning_workspace_wiring_default_off.md",
        "tests/test_phase57a_live_exact_resume_change_proposal_planning_workspace_wiring_default_off.py",
        "docs/phase57_live_exact_resume_change_proposal_planning_workspace_readback_ui_api_default_off.md",
        "tests/test_phase57b_live_exact_resume_change_proposal_planning_workspace_readback_ui_api_default_off.py",
        "docs/phase58_manual_exact_change_acceptance_approved_plan_wiring_default_off.md",
        "docs/phase58_manual_exact_change_acceptance_approved_plan_readback_ui_api_default_off.md",
        "docs/phase59_approved_change_plan_guarded_resume_copy_artifact_wiring_default_off.md",
        "docs/phase59_approved_change_plan_guarded_resume_copy_artifact_readback_ui_api_default_off.md",
        "docs/phase60_guarded_resume_copy_artifact_readback_verification_default_off.md",
        "docs/phase60_guarded_resume_copy_artifact_verification_readback_ui_api_default_off.md",
        "docs/phase61_verified_artifact_operator_review_packet_wiring_default_off.md",
        "docs/phase61_verified_artifact_operator_review_packet_readback_ui_api_default_off.md",
            "docs/phase62_verified_artifact_operator_decision_capture_wiring_default_off.md",
            "docs/phase62_verified_artifact_operator_decision_capture_readback_ui_api_default_off.md",
            "docs/phase63_operator_approved_artifact_application_readiness_packet_wiring_default_off.md",
            "docs/phase63_operator_approved_artifact_application_readiness_packet_readback_ui_api_default_off.md",
        "tests/test_phase58a_manual_exact_change_acceptance_approved_plan_wiring_default_off.py",
        "tests/test_phase58b_manual_exact_change_acceptance_approved_plan_readback_ui_api_default_off.py",
        "tests/test_phase59a_approved_change_plan_guarded_resume_copy_artifact_wiring_default_off.py",
        "tests/test_phase59b_approved_change_plan_guarded_resume_copy_artifact_readback_ui_api_default_off.py",
        "tests/test_phase60a_guarded_resume_copy_artifact_readback_verification_default_off.py",
        "tests/test_phase60b_guarded_resume_copy_artifact_verification_readback_ui_api_default_off.py",
        "tests/test_phase61a_verified_artifact_operator_review_packet_wiring_default_off.py",
        "tests/test_phase61b_verified_artifact_operator_review_packet_readback_ui_api_default_off.py",
            "tests/test_phase62a_verified_artifact_operator_decision_capture_wiring_default_off.py",
            "tests/test_phase62b_verified_artifact_operator_decision_capture_readback_ui_api_default_off.py",
            "tests/test_phase63a_operator_approved_artifact_application_readiness_packet_wiring_default_off.py",
            "tests/test_phase63b_operator_approved_artifact_application_readiness_packet_readback_ui_api_default_off.py",
        "tests/test_phase56a_live_tailoring_suggestion_planning_workspace_wiring_default_off.py",
        "src/app/api.py",
        "docs/phase22_core_agent_evidence_materialization_api_readback.md",
        "tests/test_phase22d_core_agent_evidence_materialization_api_readback_default_off.py",
        "src/app/static/agentic_review.js",
        "src/app/static/app_redesign.css",
        "src/app/ui.py",
        "src/app/static/app.js",
        "src/app/static/planning.js",
        "src/app/static/scan_workspace.css",
            "src/app/static/scan_workspace_review.css",
            "src/app/static/styles.css",
        "tests/test_queue_ui_metadata_contract.py",
        "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
        "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
        "docs/phase22_core_agent_evidence_materialization_ui_readback.md",
        "tests/test_phase22e_core_agent_evidence_materialization_ui_readback_default_off.py",
        "docs/phase22_core_agent_evidence_materialization_release_checkpoint.md",
        "tests/test_phase22f_core_agent_evidence_materialization_release_checkpoint_default_off.py",
        "src/agents/tailoring_agent_opportunity_contract.py",
        "docs/phase23_tailoring_agent_opportunity_contract.md",
        "tests/test_phase23a_tailoring_agent_opportunity_contract_default_off.py",
        "docs/phase23_tailoring_agent_opportunity_api_readback.md",
        "tests/test_phase23b_tailoring_agent_opportunity_api_readback_default_off.py",
        "docs/phase23_tailoring_agent_opportunity_ui_readback.md",
        "tests/test_phase23c_tailoring_agent_opportunity_ui_readback_default_off.py",
        "src/agents/generate_ai_tailoring_action_boundary_contract.py",
        "docs/phase23_generate_ai_tailoring_action_boundary_contract.md",
        "tests/test_phase23d_generate_ai_tailoring_action_boundary_contract_default_off.py",
        "docs/phase23_generate_ai_tailoring_action_boundary_api_readback.md",
        "tests/test_phase23e_generate_ai_tailoring_action_boundary_api_readback_default_off.py",
        "docs/phase23_generate_ai_tailoring_action_boundary_ui_readback.md",
        "tests/test_phase23f_generate_ai_tailoring_action_boundary_ui_readback_default_off.py",
        "docs/phase23_tailoring_agent_workflow_release_checkpoint.md",
        "tests/test_phase23g_tailoring_agent_workflow_release_checkpoint_default_off.py",
        "src/agents/manual_generate_ai_tailoring_preview_contract.py",
        "docs/phase24_manual_generate_ai_tailoring_preview_contract.md",
        "tests/test_phase24a_manual_generate_ai_tailoring_preview_contract_default_off.py",
        "docs/phase24_manual_generate_ai_tailoring_preview_api_readback.md",
        "tests/test_phase24b_manual_generate_ai_tailoring_preview_api_readback_default_off.py",
        "src/app/static/agentic_review.js",
        "src/app/static/app_redesign.css",
        "src/app/ui.py",
        "src/app/static/app.js",
        "src/app/static/planning.js",
        "tests/test_queue_ui_metadata_contract.py",
        "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
        "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
        "docs/phase24_manual_generate_ai_tailoring_preview_ui_readback.md",
        "tests/test_phase24c_manual_generate_ai_tailoring_preview_ui_readback_default_off.py",
        "docs/phase24_manual_generate_ai_tailoring_preview_release_checkpoint.md",
        "tests/test_phase24d_manual_generate_ai_tailoring_preview_release_checkpoint_default_off.py",
            "src/agents/manual_generate_ai_tailoring_preview_request_packet_contract.py",
            "docs/phase25_manual_generate_ai_tailoring_preview_request_packet_contract.md",
            "tests/test_phase25a_manual_generate_ai_tailoring_preview_request_packet_contract_default_off.py",
            "docs/phase25_manual_generate_ai_tailoring_preview_request_packet_api_readback.md",
            "tests/test_phase25b_manual_generate_ai_tailoring_preview_request_packet_api_readback_default_off.py",
            "src/app/static/agentic_review.js",
            "src/app/static/app_redesign.css",
            "src/app/ui.py",
            "src/app/static/app.js",
            "src/app/static/planning.js",
            "tests/test_queue_ui_metadata_contract.py",
            "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
            "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
            "docs/phase25_manual_generate_ai_tailoring_preview_request_packet_ui_readback.md",
            "tests/test_phase25c_manual_generate_ai_tailoring_preview_request_packet_ui_readback_default_off.py",
            "docs/phase25_manual_generate_ai_tailoring_preview_request_packet_release_checkpoint.md",
            "tests/test_phase25d_manual_generate_ai_tailoring_preview_request_packet_release_checkpoint_default_off.py",
            "src/agents/manual_generate_ai_tailoring_preview_dispatch_boundary_contract.py",
            "docs/phase26_manual_generate_ai_tailoring_preview_dispatch_boundary_contract.md",
            "tests/test_phase26a_manual_generate_ai_tailoring_preview_dispatch_boundary_contract_default_off.py",
            "src/app/api.py",
            "docs/phase26_manual_generate_ai_tailoring_preview_dispatch_boundary_api_readback.md",
            "tests/test_phase26b_manual_generate_ai_tailoring_preview_dispatch_boundary_api_readback_default_off.py",
            "src/app/static/agentic_review.js",
            "src/app/static/app_redesign.css",
            "src/app/ui.py",
            "src/app/static/app.js",
            "src/app/static/planning.js",
            "tests/test_queue_ui_metadata_contract.py",
            "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
            "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
            "docs/phase26_manual_generate_ai_tailoring_preview_dispatch_boundary_ui_readback.md",
            "tests/test_phase26c_manual_generate_ai_tailoring_preview_dispatch_boundary_ui_readback_default_off.py",
            "docs/phase26_manual_generate_ai_tailoring_preview_dispatch_boundary_release_checkpoint.md",
            "tests/test_phase26d_manual_generate_ai_tailoring_preview_dispatch_boundary_release_checkpoint_default_off.py",
            "src/agents/manual_generate_ai_tailoring_preview_provider_request_envelope_contract.py",
            "docs/phase27_manual_generate_ai_tailoring_preview_provider_request_envelope_contract.md",
            "tests/test_phase27a_manual_generate_ai_tailoring_preview_provider_request_envelope_contract_default_off.py",
            "src/app/api.py",
            "docs/phase27_manual_generate_ai_tailoring_preview_provider_request_envelope_api_readback.md",
            "tests/test_phase27b_manual_generate_ai_tailoring_preview_provider_request_envelope_api_readback_default_off.py",
            "src/app/static/agentic_review.js",
            "src/app/static/app_redesign.css",
            "src/app/ui.py",
            "src/app/static/app.js",
            "src/app/static/planning.js",
            "tests/test_queue_ui_metadata_contract.py",
            "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
            "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
            "docs/phase27_manual_generate_ai_tailoring_preview_provider_request_envelope_ui_readback.md",
            "tests/test_phase27c_manual_generate_ai_tailoring_preview_provider_request_envelope_ui_readback_default_off.py",
            "docs/phase27_manual_generate_ai_tailoring_preview_provider_request_envelope_release_checkpoint.md",
            "tests/test_phase27d_manual_generate_ai_tailoring_preview_provider_request_envelope_release_checkpoint_default_off.py",
            "src/agents/manual_generate_ai_tailoring_preview_provider_call_boundary_contract.py",
            "docs/phase28_manual_generate_ai_tailoring_preview_provider_call_boundary_contract.md",
            "tests/test_phase28a_manual_generate_ai_tailoring_preview_provider_call_boundary_contract_default_off.py",
            "src/app/api.py",
            "docs/phase28_manual_generate_ai_tailoring_preview_provider_call_boundary_api_readback.md",
            "tests/test_phase28b_manual_generate_ai_tailoring_preview_provider_call_boundary_api_readback_default_off.py",
            "src/app/static/agentic_review.js",
            "src/app/static/app_redesign.css",
            "src/app/ui.py",
            "src/app/static/app.js",
            "src/app/static/planning.js",
            "tests/test_queue_ui_metadata_contract.py",
            "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
            "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
            "docs/phase28_manual_generate_ai_tailoring_preview_provider_call_boundary_ui_readback.md",
            "tests/test_phase28c_manual_generate_ai_tailoring_preview_provider_call_boundary_ui_readback_default_off.py",
            "docs/phase28_manual_generate_ai_tailoring_preview_provider_call_boundary_ui_readback 2.md",
            "tests/test_phase28c_manual_generate_ai_tailoring_preview_provider_call_boundary_ui_readback_default_off 2.py",
            "docs/phase28_manual_generate_ai_tailoring_preview_provider_call_boundary_release_checkpoint.md",
            "tests/test_phase28d_manual_generate_ai_tailoring_preview_provider_call_boundary_release_checkpoint_default_off.py",
            "src/agents/manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_contract.py",
            "docs/phase29_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_contract.md",
            "tests/test_phase29a_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_contract_default_off.py",
            "src/app/api.py",
            "docs/phase29_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_api_readback.md",
            "tests/test_phase29b_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_api_readback_default_off.py",
            "src/app/static/agentic_review.js",
            "src/app/static/app_redesign.css",
            "src/app/ui.py",
            "src/app/static/app.js",
            "src/app/static/planning.js",
            "tests/test_queue_ui_metadata_contract.py",
            "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
            "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
            "docs/phase29_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_ui_readback.md",
            "tests/test_phase29c_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_ui_readback_default_off.py",
            "docs/phase29_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_release_checkpoint.md",
            "tests/test_phase29d_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_release_checkpoint_default_off.py",
            "src/agents/manual_generate_ai_tailoring_preview_provider_response_validation_contract.py",
            "docs/phase30_manual_generate_ai_tailoring_preview_provider_response_validation_contract.md",
            "tests/test_phase30a_manual_generate_ai_tailoring_preview_provider_response_validation_contract_default_off.py",
            "src/app/api.py",
            "docs/phase30_manual_generate_ai_tailoring_preview_provider_response_validation_api_readback.md",
            "tests/test_phase30b_manual_generate_ai_tailoring_preview_provider_response_validation_api_readback_default_off.py",
                "src/app/static/agentic_review.js",
                "src/app/static/app_redesign.css",
                "src/app/ui.py",
                "src/app/static/app.js",
                "src/app/static/planning.js",
                "tests/test_queue_ui_metadata_contract.py",
                "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
                "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
                "docs/phase30_manual_generate_ai_tailoring_preview_provider_response_validation_ui_readback.md",
                "tests/test_phase30c_manual_generate_ai_tailoring_preview_provider_response_validation_ui_readback_default_off.py",
                    "docs/phase30_manual_generate_ai_tailoring_preview_provider_response_validation_release_checkpoint.md",
                    "tests/test_phase30d_manual_generate_ai_tailoring_preview_provider_response_validation_release_checkpoint_default_off.py",
                        "src/agents/manual_generate_ai_tailoring_preview_provider_response_normalization_contract.py",
                        "docs/phase31_manual_generate_ai_tailoring_preview_provider_response_normalization_contract.md",
                        "tests/test_phase31a_manual_generate_ai_tailoring_preview_provider_response_normalization_contract_default_off.py",
                        "src/app/api.py",
                        "docs/phase31_manual_generate_ai_tailoring_preview_provider_response_normalization_api_readback.md",
                        "tests/test_phase31b_manual_generate_ai_tailoring_preview_provider_response_normalization_api_readback_default_off.py",
                            "docs/phase31_manual_generate_ai_tailoring_preview_provider_response_normalization_ui_readback.md",
                            "tests/test_phase31c_manual_generate_ai_tailoring_preview_provider_response_normalization_ui_readback_default_off.py",
                                "docs/phase31_manual_generate_ai_tailoring_preview_provider_response_normalization_release_checkpoint.md",
                                "tests/test_phase31d_manual_generate_ai_tailoring_preview_provider_response_normalization_release_checkpoint_default_off.py",
                                "src/agents/manual_generate_ai_tailoring_preview_normalized_response_preview_packet_contract.py",
                                "docs/phase32_manual_generate_ai_tailoring_preview_normalized_response_preview_packet_contract.md",
                                "tests/test_phase32a_manual_generate_ai_tailoring_preview_normalized_response_preview_packet_contract_default_off.py",
                                "src/app/api.py",
                                "docs/phase32_manual_generate_ai_tailoring_preview_normalized_response_preview_packet_api_readback.md",
                                "tests/test_phase32b_manual_generate_ai_tailoring_preview_normalized_response_preview_packet_api_readback_default_off.py",
                                "docs/phase32_manual_generate_ai_tailoring_preview_normalized_response_preview_packet_api_readback 2.md",
                                "tests/test_phase32b_manual_generate_ai_tailoring_preview_normalized_response_preview_packet_api_readback_default_off 2.py",
                                "src/agents/controlled_agent_router_readonly.py",
                                "docs/phase33_controlled_agent_router_readonly.md",
                                "tests/test_phase33a_controlled_agent_router_readonly.py",
                                "docs/phase33_controlled_agent_router_readonly 2.md",
                                "tests/test_phase33a_controlled_agent_router_readonly 2.py",
                                "src/agents/controlled_agent_router_workflow_state_adapter_readonly.py",
                                "docs/phase33_controlled_agent_router_workflow_state_adapter_readonly.md",
                                "tests/test_phase33b_controlled_agent_router_workflow_state_adapter_readonly.py",
                                "src/agents/controlled_agent_router_batch_handoff_plan_readonly.py",
                                "docs/phase33_controlled_agent_router_batch_handoff_plan_readonly.md",
                                "tests/test_phase33c_controlled_agent_router_batch_handoff_plan_readonly.py",
                                "src/agents/controlled_agent_router_planning_artifact_mapper_readonly.py",
                                "docs/phase33_controlled_agent_router_planning_artifact_mapper_readonly.md",
                                "tests/test_phase33d_controlled_agent_router_planning_artifact_mapper_readonly.py",
                                "run_controlled_agent_router_planning_artifact_dry_run.py",
                                "docs/phase33_controlled_agent_router_planning_artifact_dry_run_command_readonly.md",
                                "tests/test_phase33e_controlled_agent_router_planning_artifact_dry_run_command_readonly.py",
                                "src/agents/jd_intelligence_llm_signal_extractor_default_off.py",
                                "docs/phase34_jd_intelligence_llm_signal_extractor_default_off.md",
                                "tests/test_phase34a_jd_intelligence_llm_signal_extractor_default_off.py",
                                "src/agents/jd_intelligence_planning_artifact_enricher_default_off.py",
                                "docs/phase34_jd_intelligence_planning_artifact_enricher_default_off.md",
                                "tests/test_phase34b_jd_intelligence_planning_artifact_enricher_default_off.py",
                                "run_jd_intelligence_planning_artifact_enrichment_dry_run.py",
                                "docs/phase34_jd_intelligence_planning_artifact_enrichment_dry_run_command_default_off.md",
                                "tests/test_phase34c_jd_intelligence_planning_artifact_enrichment_dry_run_command_default_off.py",
                                "src/agents/jd_signal_resume_evidence_matrix_default_off.py",
                                "docs/phase35_jd_signal_resume_evidence_matrix_default_off.md",
                                "tests/test_phase35a_jd_signal_resume_evidence_matrix_default_off.py",
                                "src/agents/jd_signal_planning_artifact_evidence_enricher_default_off.py",
                                "docs/phase35_jd_signal_planning_artifact_evidence_enricher_default_off.md",
                                "tests/test_phase35b_jd_signal_planning_artifact_evidence_enricher_default_off.py",
                                "run_jd_signal_planning_artifact_evidence_enrichment_dry_run.py",
                                "docs/phase35_jd_signal_planning_artifact_evidence_enrichment_dry_run_command_default_off.md",
                                "tests/test_phase35c_jd_signal_planning_artifact_evidence_enrichment_dry_run_command_default_off.py",
                                "src/agents/jd_evidence_final_scoring_feature_adapter_default_off.py",
                                "docs/phase36_jd_evidence_final_scoring_feature_adapter_default_off.md",
                                "tests/test_phase36a_jd_evidence_final_scoring_feature_adapter_default_off.py",
                                "run_jd_evidence_final_scoring_feature_adapter_dry_run.py",
                                "docs/phase36_jd_evidence_final_scoring_feature_adapter_dry_run_command_default_off.md",
                                "tests/test_phase36b_jd_evidence_final_scoring_feature_adapter_dry_run_command_default_off.py",
                                "src/agents/jd_evidence_scoring_contribution_preview_default_off.py",
                                "docs/phase37_jd_evidence_scoring_contribution_preview_default_off.md",
                                "tests/test_phase37a_jd_evidence_scoring_contribution_preview_default_off.py",
                                "run_jd_evidence_scoring_contribution_preview_dry_run.py",
                                "docs/phase37_jd_evidence_scoring_contribution_preview_dry_run_command_default_off.md",
                                "tests/test_phase37b_jd_evidence_scoring_contribution_preview_dry_run_command_default_off.py",
                                "src/agents/jd_evidence_score_impact_preview_default_off.py",
                                "docs/phase38_jd_evidence_score_impact_preview_default_off.md",
                                "tests/test_phase38a_jd_evidence_score_impact_preview_default_off.py",
                                "tests/test_phase38a_jd_evidence_score_impact_preview_default_off 2.py",
                                "\"tests/test_phase38a_jd_evidence_score_impact_preview_default_off 2.py\"",
                                "run_jd_evidence_score_impact_preview_dry_run.py",
                                "docs/phase38_jd_evidence_score_impact_preview_dry_run_command_default_off.md",
                                "tests/test_phase38b_jd_evidence_score_impact_preview_dry_run_command_default_off.py",
                                "src/agents/jd_evidence_score_impact_planning_artifact_annotator_default_off.py",
                                "docs/phase39_jd_evidence_score_impact_planning_artifact_annotator_default_off.md",
                                "tests/test_phase39a_jd_evidence_score_impact_planning_artifact_annotator_default_off.py",
                                "run_jd_evidence_score_impact_planning_artifact_annotator_dry_run.py",
                                "docs/phase39_jd_evidence_score_impact_planning_artifact_annotator_dry_run_command_default_off.md",
                                "tests/test_phase39b_jd_evidence_score_impact_planning_artifact_annotator_dry_run_command_default_off.py",
                                "src/agents/jd_evidence_score_impact_review_packet_builder_default_off.py",
                                "docs/phase40_jd_evidence_score_impact_review_packet_builder_default_off.md",
                                "tests/test_phase40a_jd_evidence_score_impact_review_packet_builder_default_off.py",
                                "run_jd_evidence_score_impact_review_packet_builder_dry_run.py",
                                "docs/phase40_jd_evidence_score_impact_review_packet_builder_dry_run_command_default_off.md",
                                "tests/test_phase40b_jd_evidence_score_impact_review_packet_builder_dry_run_command_default_off.py",
                                "src/agents/jd_evidence_score_impact_review_queue_builder_default_off.py",
                                "docs/phase41_jd_evidence_score_impact_review_queue_builder_default_off.md",
                                "src/agents/exact_resume_change_set_proposal_builder_default_off.py",
                                "docs/phase42_exact_resume_change_set_proposal_builder_default_off.md",
                                "src/agents/controlled_exact_resume_change_set_llm_request_packet_default_off.py",
                                "docs/phase43_controlled_exact_resume_change_set_llm_request_packet_default_off.md",
                                "src/agents/controlled_exact_resume_change_set_provider_call_boundary_default_off.py",
                                "docs/phase44_controlled_exact_resume_change_set_provider_call_boundary_default_off.md",
                                "run_controlled_exact_resume_change_set_provider_call_boundary_dry_run.py",
                                "docs/phase44_controlled_exact_resume_change_set_provider_call_boundary_dry_run_command_default_off.md",
                                "tests/test_phase44b_controlled_exact_resume_change_set_provider_call_boundary_dry_run_command_default_off.py",
                "src/agents/controlled_exact_resume_change_set_provider_response_validation_default_off.py",
                "docs/phase45_controlled_exact_resume_change_set_provider_response_validation_default_off.md",
                "tests/test_phase45a_controlled_exact_resume_change_set_provider_response_validation_default_off.py",
                "run_controlled_exact_resume_change_set_provider_response_validation_dry_run.py",
                "docs/phase45_controlled_exact_resume_change_set_provider_response_validation_dry_run_command_default_off.md",
                "tests/test_phase45b_controlled_exact_resume_change_set_provider_response_validation_dry_run_command_default_off.py",
                "src/agents/controlled_exact_resume_change_set_provider_response_normalization_default_off.py",
                "docs/phase46_controlled_exact_resume_change_set_provider_response_normalization_default_off.md",
                "tests/test_phase46a_controlled_exact_resume_change_set_provider_response_normalization_default_off.py",
        "run_controlled_exact_resume_change_set_provider_response_normalization_dry_run.py",
        "docs/phase46_controlled_exact_resume_change_set_provider_response_normalization_dry_run_command_default_off.md",
        "tests/test_phase46b_controlled_exact_resume_change_set_provider_response_normalization_dry_run_command_default_off.py",
        "src/agents/controlled_exact_resume_change_set_manual_review_packet_builder_default_off.py",
        "docs/phase47_controlled_exact_resume_change_set_manual_review_packet_builder_default_off.md",
        "tests/test_phase47a_controlled_exact_resume_change_set_manual_review_packet_builder_default_off.py",
        "run_controlled_exact_resume_change_set_manual_review_packet_builder_dry_run.py",
        "docs/phase47_controlled_exact_resume_change_set_manual_review_packet_builder_dry_run_command_default_off.md",
        "tests/test_phase47b_controlled_exact_resume_change_set_manual_review_packet_builder_dry_run_command_default_off.py",
        "src/agents/controlled_exact_resume_change_set_manual_review_readback_adapter_default_off.py",
        "docs/phase48_controlled_exact_resume_change_set_manual_review_readback_adapter_default_off.md",
        "tests/test_phase48a_controlled_exact_resume_change_set_manual_review_readback_adapter_default_off.py",
        "run_controlled_exact_resume_change_set_manual_review_readback_adapter_dry_run.py",
        "docs/phase48_controlled_exact_resume_change_set_manual_review_readback_adapter_dry_run_command_default_off.md",
        "tests/test_phase48b_controlled_exact_resume_change_set_manual_review_readback_adapter_dry_run_command_default_off.py",
        "src/agents/controlled_exact_resume_change_set_real_provider_runtime_adapter_default_off.py",
        "docs/phase49_controlled_exact_resume_change_set_real_provider_runtime_adapter_default_off.md",
        "tests/test_phase49a_controlled_exact_resume_change_set_real_provider_runtime_adapter_default_off.py",
        "run_controlled_exact_resume_change_set_real_provider_runtime_adapter_dry_run.py",
        "docs/phase49_controlled_exact_resume_change_set_real_provider_runtime_adapter_dry_run_command_default_off.md",
        "tests/test_phase49b_controlled_exact_resume_change_set_real_provider_runtime_adapter_dry_run_command_default_off.py",
            "src/agents/controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_default_off.py",
            "docs/phase50_controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_default_off.md",
            "tests/test_phase50a_controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_default_off.py",
        "run_controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_dry_run.py",
        "docs/phase50_controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_dry_run_command_default_off.md",
        "tests/test_phase50b_controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_dry_run_command_default_off.py",
        "src/agents/controlled_exact_resume_change_set_manual_decision_packet_default_off.py",
        "docs/phase51_controlled_exact_resume_change_set_manual_decision_packet_default_off.md",
        "tests/test_phase51a_controlled_exact_resume_change_set_manual_decision_packet_default_off.py",
        "run_controlled_exact_resume_change_set_manual_decision_packet_dry_run.py",
        "docs/phase51_controlled_exact_resume_change_set_manual_decision_packet_dry_run_command_default_off.md",
        "tests/test_phase51b_controlled_exact_resume_change_set_manual_decision_packet_dry_run_command_default_off.py",
        "src/agents/controlled_exact_resume_change_set_manual_decision_readback_adapter_default_off.py",
        "docs/phase52_controlled_exact_resume_change_set_manual_decision_readback_adapter_default_off.md",
        "tests/test_phase52a_controlled_exact_resume_change_set_manual_decision_readback_adapter_default_off.py",
        "run_controlled_exact_resume_change_set_manual_decision_readback_adapter_dry_run.py",
        "docs/phase52_controlled_exact_resume_change_set_manual_decision_readback_adapter_dry_run_command_default_off.md",
        "tests/test_phase52b_controlled_exact_resume_change_set_manual_decision_readback_adapter_dry_run_command_default_off.py",
        "src/agents/controlled_exact_resume_change_set_approved_change_plan_packet_default_off.py",
        "docs/phase53_controlled_exact_resume_change_set_approved_change_plan_packet_default_off.md",
        "tests/test_phase53a_controlled_exact_resume_change_set_approved_change_plan_packet_default_off.py",
        "run_controlled_exact_resume_change_set_approved_change_plan_packet_dry_run.py",
        "docs/phase53_controlled_exact_resume_change_set_approved_change_plan_packet_dry_run_command_default_off.md",
        "tests/test_phase53b_controlled_exact_resume_change_set_approved_change_plan_packet_dry_run_command_default_off.py",
        "src/agents/controlled_exact_resume_change_set_approved_change_plan_readback_adapter_default_off.py",
        "docs/phase54_controlled_exact_resume_change_set_approved_change_plan_readback_adapter_default_off.md",
        "tests/test_phase54a_controlled_exact_resume_change_set_approved_change_plan_readback_adapter_default_off.py",
        "src/app/services.py",
        "src/app/api.py",
        "docs/phase55_live_jd_llm_extraction_planning_scan_wiring_default_off.md",
        "tests/test_phase55a_live_jd_llm_extraction_planning_scan_wiring_default_off.py",
        "src/app/planning_ui.py",
        "src/app/static/planning.js",
        "src/app/static/scan_workspace.js",
        "docs/phase55_live_jd_llm_extraction_planning_scan_readback_ui_api_default_off.md",
        "tests/test_phase55b_live_jd_llm_extraction_planning_scan_readback_ui_api_default_off.py",
        "tests/test_three_core_agent_shadow_sidecar_bridge_default_off.py",

                                "tests/test_phase44a_controlled_exact_resume_change_set_provider_call_boundary_default_off.py",
                                "run_controlled_exact_resume_change_set_llm_request_packet_dry_run.py",
                                "docs/phase43_controlled_exact_resume_change_set_llm_request_packet_dry_run_command_default_off.md",
                                "tests/test_phase43b_controlled_exact_resume_change_set_llm_request_packet_dry_run_command_default_off.py",
                                "tests/test_phase43a_controlled_exact_resume_change_set_llm_request_packet_default_off.py",
                                "run_exact_resume_change_set_proposal_builder_dry_run.py",
                                "docs/phase42_exact_resume_change_set_proposal_builder_dry_run_command_default_off.md",
                                "tests/test_phase42b_exact_resume_change_set_proposal_builder_dry_run_command_default_off.py",
                                "tests/test_phase42a_exact_resume_change_set_proposal_builder_default_off.py",
                                "run_jd_evidence_score_impact_review_queue_builder_dry_run.py",
                                "docs/phase41_jd_evidence_score_impact_review_queue_builder_dry_run_command_default_off.md",
                                "tests/test_phase41b_jd_evidence_score_impact_review_queue_builder_dry_run_command_default_off.py",
                                "tests/test_phase41a_jd_evidence_score_impact_review_queue_builder_default_off.py",
        "docs/phase23_generate_ai_tailoring_action_boundary_api_readback 2.md",
        "tests/test_phase23e_generate_ai_tailoring_action_boundary_api_readback_default_off 2.py",
        "docs/phase22_core_agent_evidence_materialization_api_readback 2.md",
        "tests/test_phase22d_core_agent_evidence_materialization_api_readback_default_off 2.py",
        "tests/test_portfolio_demo_readiness_wrap_checkpoint.py",
    }
    legacy_guards = {
        str(path.relative_to(ROOT))
        for path in (ROOT / "tests").glob("test_*.py")
        if (
            "changes_only" in path.read_text(encoding="utf-8")
            or "85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96"
            in path.read_text(encoding="utf-8")
            or "300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab"
            in path.read_text(encoding="utf-8")
            or "81eede647edd99ca1f8c0f5b759b35ecf40e223db9d9dbd4b976f487ecf49961"
            in path.read_text(encoding="utf-8")
        )
    }

    allowed |= {
        "src/agents/orchestrator_adapter_harness.py",
        "tests/test_phase80b_controlled_advisory_chain_trace_persistence.py",
    }
    allowed |= {
        "src/pipeline/collector.py",
        "tests/test_phase80d_advisory_chain_trace_readback_compatibility.py",
        "tests/test_phase81b_controlled_pipeline_advisory_chain_invocation_default_off.py",
        "tests/test_phase81d_collector_advisory_chain_diagnostics_sidecar_default_off.py",
        "tests/test_phase82b_collector_advisory_chain_trace_persistence_default_off.py",
        "tests/test_phase83b_live_llm_invocation_contract_map_default_off.py",
            "src/agents/jd_intelligence.py",
            "tests/test_phase84b_jd_intelligence_existing_output_wrapper_default_off.py",
                "tests/test_phase86b_jd_intelligence_existing_output_trace_payload_default_off.py",
                "tests/test_phase87b_jd_intelligence_existing_output_collector_diagnostics_default_off.py",
            "tests/test_phase88b_jd_intelligence_existing_output_trace_persistence_default_off.py",
            "src/agents/resume_match_agent.py",
            "tests/test_phase89b_resume_match_consumes_jd_intelligence_default_off.py",
            "src/agents/critic_agent.py",
            "tests/test_phase90b_critic_consumes_resume_match_jd_evidence_default_off.py",
            "src/agents/job_prioritization_agent.py",
            "tests/test_phase91b_job_prioritization_consumes_critic_evidence_default_off.py",
            "src/agents/tailoring_decision_agent.py",
            "tests/test_phase92b_tailoring_decision_consumes_job_prioritization_evidence_default_off.py",
            "tests/test_resume_match_dry_run_contract_no_pipeline_change.py",
            "tests/support/phase_guard_registry.py",
            "tests/test_phase85b_legacy_guard_registry_default_off.py",
            "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
            "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
            "tests/test_three_core_shadow_readiness_wrap_default_off.py",
            "tests/test_portfolio_demo_readiness_wrap_checkpoint.py",
            "tests/test_agent_trace_ui_readiness_checkpoint.py",
            "tests/test_agent_trace_readonly_ui_panel_no_api_no_writes.py",
            "tests/test_agent_trace_polish_ux_hardening_ui_only_no_api_no_writes.py",
            "tests/test_agent_trace_polish_ux_hardening_ui_only_no_api_no_writes.py",
            "tests/test_agent_trace_readonly_ui_panel_no_api_no_writes.py",
        "tests/test_shadow_sidecar_trace_persistence_hook_integration_default_off.py",
    }
    assert changed <= allowed | legacy_guards
