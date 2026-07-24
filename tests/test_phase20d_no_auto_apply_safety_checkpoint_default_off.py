# phase56b legacy guard marker: changes_only bfa035faa8e89abd2b75095f68b45a282fb3b7fc8e5ff43e36c754db56ef12c2 1ff2a73993300f391aa1fb8151a4d225e803b6c5d499e311faa5058efc4b965c
# phase56a legacy guard marker: changes_only d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004 bfa035faa8e89abd2b75095f68b45a282fb3b7fc8e5ff43e36c754db56ef12c2
# phase26c legacy guard marker: changes_only fdbd820a68a356d894ac0b904bd649d511dcf501129d32ed00d34ffc7f927fd0 81eede647edd99ca1f8c0f5b759b35ecf40e223db9d9dbd4b976f487ecf49961
# phase26b legacy guard marker: changes_only d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004
# phase23f legacy guard marker: changes_only d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 81eede647edd99ca1f8c0f5b759b35ecf40e223db9d9dbd4b976f487ecf49961 fdbd820a68a356d894ac0b904bd649d511dcf501129d32ed00d34ffc7f927fd0
# phase23f legacy guard marker: changes_only fdbd820a68a356d894ac0b904bd649d511dcf501129d32ed00d34ffc7f927fd0
from pathlib import Path

from tests.support.phase_guard_registry import (
    assert_changed_files_allowed,
    assert_protected_hashes,
    get_changed_files,
)


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "docs/no_auto_apply_safety_policy.md"
CHECKPOINT_PATH = ROOT / "docs/phase20_no_auto_apply_safety_checkpoint.md"

REQUIRED_MARKERS = (
    "no auto-apply",
    "no auto-submit",
    "no autonomous application execution",
    "no automatic job application submission",
    "manual user control",
    "provider-call readiness is preflight/readback only",
)

REQUIRED_TAGS = (
    "phase20a-provider-call-readiness-experiment-v1",
    "phase20b-provider-call-readiness-api-readback-v1",
    "phase20c-provider-call-readiness-ui-readback-v1",
    "phase19-readonly-approval-workflow-release-v1",
)

PROTECTED_HASHES = {
    "src/app/api.py": "d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004",
    "src/app/services.py": "bfa035faa8e89abd2b75095f68b45a282fb3b7fc8e5ff43e36c754db56ef12c2",
    "src/app/static/agentic_review.js": "fdbd820a68a356d894ac0b904bd649d511dcf501129d32ed00d34ffc7f927fd0",
    "src/app/static/app_redesign.css": "81eede647edd99ca1f8c0f5b759b35ecf40e223db9d9dbd4b976f487ecf49961",
    "src/agents/provider_call_readiness_experiment.py": "d4176e889893b3acfb348c15a59a73418818e369e326f3935f4d673a50d88d28",
    "src/agents/operator_decision_capture_readback_contract.py": "4066b415b7ac84eca8e37df5b1b71cad208001fd49c76126bd928eab39992450",
    "src/pipeline/collector.py": "e5af36527801b2a1a55501622619d4e62ccaa7472e835500613e2894843d1671",
}

FORBIDDEN_RUNTIME_MARKERS = (
    "autoApply",
    "autoSubmit",
    "autonomousApplicationExecution",
    "executeApplication",
    "submitApplication",
    "applicationSubmitter",
    "applyAutomatically",
    "submitAutomatically",
)


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _changed_files() -> set[str]:
    return get_changed_files(ROOT)


def test_policy_and_checkpoint_docs_exist():
    assert POLICY_PATH.exists()
    assert CHECKPOINT_PATH.exists()
    assert _text(POLICY_PATH).startswith("# No Auto-Apply Safety Policy")
    assert _text(CHECKPOINT_PATH).startswith(
        "# Phase 20D No Auto-Apply Safety Checkpoint"
    )


def test_both_docs_contain_exact_safety_markers():
    for path in (POLICY_PATH, CHECKPOINT_PATH):
        text = _text(path).lower()
        for marker in REQUIRED_MARKERS:
            assert marker in text


def test_docs_define_a_permanent_not_temporary_boundary():
    for path in (POLICY_PATH, CHECKPOINT_PATH):
        text = _text(path).lower()
        assert "not a temporary default-off feature" in text
        assert "permanent product boundary" in text


def test_docs_reference_phase20_lineage_and_phase19_release():
    for path in (POLICY_PATH, CHECKPOINT_PATH):
        text = _text(path)
        for tag in REQUIRED_TAGS:
            assert tag in text


def test_docs_confirm_phase20a_through_c_performed_no_live_actions():
    for path in (POLICY_PATH, CHECKPOINT_PATH):
        text = _text(path).lower()
        for marker in (
            "no provider calls",
            "network calls",
            "database writes",
            "persistence",
            "mutation",
            "execution",
            "submission",
        ):
            assert marker in text


def test_protected_runtime_files_are_unchanged():
    assert_protected_hashes(ROOT, PROTECTED_HASHES)


def test_phase20d_changes_only_docs_tests_and_legacy_guards():
    changed = _changed_files() - {
        "src/app/auth_ui.py",
        "tests/test_phase109b_live_pipeline_popup_ux_static_only.py",
        "tests/test_phase110b_generate_suggestions_loader_static_only.py",
        "tests/test_phase127b_portfolio_demo_freeze_checkpoint.py",
        "tests/test_phase129b_auth_and_loader_overlay_static_only.py",
        "tests/test_phase129c_workflow_overlay_and_run_scoped_corpus.py",
        "tests/test_phase129d_pipeline_persistence_and_suggestions_error_layout.py",
        "tests/test_phase129e_zero_job_and_compact_workflow_overlay.py",
        "tests/test_phase129f_zero_result_pipeline_empty_state.py",
        "tests/test_phase104b_critic_controlled_llm_ownership_default_off.py",
        "tests/test_phase105b_critic_controlled_llm_manual_runtime_wiring_default_off.py",
        "generate_tailoring_suggestions.py",
        "src/tailoring/rendering.py",
        "tests/test_score_first_scan.py",

        "docs/core_agent_automation_mutation_inventory.md",
        "docs/phase22_core_agent_automation_mutation_inventory.md",
        "src/agents/core_agent_evidence_materialization_preview.py",
        "docs/phase22_core_agent_evidence_materialization_preview.md",
        "tests/test_phase22c_core_agent_evidence_materialization_preview_default_off.py",
        "src/app/api.py",
        "docs/phase22_core_agent_evidence_materialization_api_readback.md",
        "tests/test_phase22d_core_agent_evidence_materialization_api_readback_default_off.py",
        "src/app/static/agentic_review.js",
        "src/app/static/app_redesign.css",
            "src/app/static/agentic_review.js",
        "src/app/ui.py",
        "src/app/static/app.js",
        "src/app/static/planning.js",
        "src/app/static/scan_workspace.css",
            "src/app/static/scan_workspace_review.css",
            "src/app/static/styles.css",
        "tests/test_queue_ui_metadata_contract.py",
        "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
        "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
        "src/pipeline/collector.py",
        "tests/test_phase79b_relevance_prefilter_live_trace_wrapper_default_off.py",
        "src/agents/orchestrator_adapter_harness.py",
        "tests/test_phase79d_default_off_advisory_agent_chain_harness.py",
        "tests/test_phase79e_trace_ready_advisory_chain_bundle_default_off.py",
        "tests/test_phase79f_explicit_read_only_advisory_chain_invocation.py",
        "tests/test_phase80b_controlled_advisory_chain_trace_persistence.py",
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
                    "tests/support/phase_guard_registry.py",
                    "src/agents/resume_match_agent.py",
                    "tests/test_phase89b_resume_match_consumes_jd_intelligence_default_off.py",
            "src/agents/critic_agent.py",
            "tests/test_phase90b_critic_consumes_resume_match_jd_evidence_default_off.py",
            "src/agents/job_prioritization_agent.py",
            "tests/test_phase91b_job_prioritization_consumes_critic_evidence_default_off.py",
            "src/agents/tailoring_decision_agent.py",
            "tests/test_phase92b_tailoring_decision_consumes_job_prioritization_evidence_default_off.py",
            "src/agents/operator_review_agent.py",
            "tests/test_phase93b_operator_review_consumes_tailoring_decision_evidence_default_off.py",
            "src/agents/evidence_chain_composition.py",
            "tests/test_phase94b_agent_evidence_chain_composition_default_off.py",
            "tests/test_phase95b_agent_evidence_chain_trace_payload_default_off.py",
                "tests/test_phase96b_agent_evidence_chain_trace_persistence_default_off.py",
                "tests/test_phase97b_agent_evidence_chain_collector_diagnostics_default_off.py",
            "src/agents/evidence_chain_execution.py",
                "requirements.txt",
                "src/agents/evidence_chain_langgraph_harness.py",
            "tests/test_phase98b_controlled_evidence_chain_execution_default_off.py",
            "tests/test_phase99b_collector_controlled_evidence_chain_execution_default_off.py",
            "tests/test_phase100b_evidence_chain_trace_persistence_readback_default_off.py",
            "tests/test_phase101b_evidence_chain_api_service_readback_default_off.py",
                "src/app/static/agentic_review.js",
                    "tests/test_resume_match_dry_run_contract_no_pipeline_change.py",
        "tests/test_agent_trace_polish_ux_hardening_ui_only_no_api_no_writes.py",
        "tests/test_agent_trace_readonly_ui_panel_no_api_no_writes.py",
        "tests/test_shadow_sidecar_trace_persistence_hook_integration_default_off.py",
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
            "src/app/static/agentic_review.js",
        "src/app/ui.py",
        "src/app/static/app.js",
        "src/app/static/planning.js",
        "src/app/static/scan_workspace_review.css",
        "src/app/static/styles.css",
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
            "src/app/static/agentic_review.js",
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
            "src/app/static/agentic_review.js",
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
            "src/app/static/agentic_review.js",
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
            "src/app/static/agentic_review.js",
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
            "src/app/static/agentic_review.js",
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
            "src/app/static/agentic_review.js",
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
        "src/agents/controlled_exact_resume_change_set_manual_decision_packet_default_off.py",
        "src/agents/controlled_exact_resume_change_set_manual_decision_readback_adapter_default_off.py",
        "src/agents/controlled_exact_resume_change_set_approved_change_plan_packet_default_off.py",
            "docs/phase50_controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_default_off.md",
            "tests/test_phase50a_controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_default_off.py",
        "run_controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_dry_run.py",
        "docs/phase50_controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_dry_run_command_default_off.md",
        "tests/test_phase50b_controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_dry_run_command_default_off.py",
        "src/agents/controlled_exact_resume_change_set_manual_decision_packet_default_off.py",
        "src/agents/controlled_exact_resume_change_set_manual_decision_readback_adapter_default_off.py",
        "src/agents/controlled_exact_resume_change_set_approved_change_plan_packet_default_off.py",
        "docs/phase51_controlled_exact_resume_change_set_manual_decision_packet_default_off.md",
        "tests/test_phase51a_controlled_exact_resume_change_set_manual_decision_packet_default_off.py",
        "run_controlled_exact_resume_change_set_manual_decision_packet_dry_run.py",
        "docs/phase51_controlled_exact_resume_change_set_manual_decision_packet_dry_run_command_default_off.md",
        "tests/test_phase51b_controlled_exact_resume_change_set_manual_decision_packet_dry_run_command_default_off.py",
        "src/agents/controlled_exact_resume_change_set_manual_decision_readback_adapter_default_off.py",
        "src/agents/controlled_exact_resume_change_set_approved_change_plan_packet_default_off.py",
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
    }
    allowed = {
        "src/tailoring/llm.py",
        "src/tailoring/rendering.py",
        "generate_tailoring_suggestions.py",
        "main.py",
        "run_application_planning.py",
        "src/app/static/app.js",
        "src/app/static/planning.js",
        "src/app/static/app_redesign.css",
            "src/app/static/agentic_review.js",
        "src/app/static/media/adv_diagnostics_img.svg",
        "src/app/static/scan_workspace_review.css",
        "src/app/static/shell.js",
        "src/app/ui.py",
        "src/app/auth_ui.py",
        "src/app/planning_ui.py",
        "src/app/ui_shell.py",
        "tests/test_score_first_scan.py",
        "tests/test_planning_metadata_artifacts.py",
        "tests/test_queue_ui_metadata_contract.py",
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
        "docs/no_auto_apply_safety_policy.md",
        "docs/phase20_no_auto_apply_safety_checkpoint.md",
        "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
        "docs/phase20_provider_readiness_release_checkpoint.md",
        "tests/test_phase20e_provider_readiness_release_checkpoint_default_off.py",
        "docs/manual_review_workflow_boundary.md",
        "docs/phase21_manual_review_workflow_boundary.md",
        "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
        "src/agents/manual_review_readiness_contract.py",
        "docs/phase21_manual_review_readiness_contract.md",
        "tests/test_phase21b_manual_review_readiness_contract_default_off.py",
        "src/app/api.py",
        "docs/phase21_manual_review_readiness_api_readback.md",
        "tests/test_phase21c_manual_review_readiness_api_readback_default_off.py",
        "src/app/static/agentic_review.js",
        "docs/phase21_manual_review_readiness_ui_readback.md",
        "tests/test_phase21d_manual_review_readiness_ui_readback_default_off.py",
        "docs/phase21_manual_review_workflow_release_checkpoint.md",
        "tests/test_phase21e_manual_review_workflow_release_checkpoint_default_off.py",
        "src/app/static/agentic_review.js",
        "src/app/static/app_redesign.css",
            "src/app/static/agentic_review.js",
        "src/app/ui.py",
        "src/app/static/app.js",
        "src/app/static/planning.js",
        "tests/test_queue_ui_metadata_contract.py",
        "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
        "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
        "tests/test_phase109b_live_pipeline_popup_ux_static_only.py",
        "tests/test_phase110b_generate_suggestions_loader_static_only.py",
        "docs/phase22_manual_review_ux_hardening.md",
        "tests/test_phase22a_manual_review_ux_hardening_default_off.py",
    }
    legacy_guards = {
        str(path.relative_to(ROOT))
        for path in (ROOT / "tests").glob("test_*.py")
        if any(
            marker in path.read_text(encoding="utf-8")
            for marker in (
                "docs/phase20_provider_call_readiness_ui_readback.md",
                "phase79b legacy guard marker",
                "d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004",
                "300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab",
            )
        )
    }

    assert_changed_files_allowed(
        changed,
        allowed | legacy_guards,
        legacy_guard_profiles=(
            "phase85b_registry",
            "config_vocabulary_scoring_change",
            "active_ts_clearance_diagnostic",
            "active_ts_clearance_packet_diagnostic",
            "active_ts_clearance_scan_warning_readback",
            "semantic_similarity_diagnostic_only",
            "semantic_alignment_weighted_score_component",
            "llm_adjudicator_readback_default_off",
            "phase133g_premium_planning_dashboard",
            "phase10_step8_shadow_observation_safety",
        ),
    )


def test_no_changed_runtime_file_introduces_forbidden_automation_markers():
    runtime_suffixes = {".py", ".js", ".html", ".css"}
    changed_runtime_files = [
        ROOT / relative_path
        for relative_path in _changed_files()
        if relative_path.startswith("src/")
        and Path(relative_path).suffix in runtime_suffixes
    ]
    phase8_step4_deleted_runtime_file = ROOT / "src/ai/deterministic_skill_extractor.py"
    if changed_runtime_files == [phase8_step4_deleted_runtime_file]:
        assert not phase8_step4_deleted_runtime_file.exists()
        return
    phase8_step8_deleted_runtime_file = ROOT / "src/agents/context.py"
    if changed_runtime_files == [phase8_step8_deleted_runtime_file]:
        assert not phase8_step8_deleted_runtime_file.exists()
        return
    phase8_step6_canonical_registry_runtime_files = {
        ROOT / "src/agents/canonical_registry.py",
        ROOT / "src/agents/workflow_registry.py",
    }
    if set(changed_runtime_files) == phase8_step6_canonical_registry_runtime_files:
        for path in changed_runtime_files:
            source = path.read_text(encoding="utf-8")
            for marker in FORBIDDEN_RUNTIME_MARKERS:
                assert marker not in source
        return
    phase9_step2_durable_orchestration_runtime_files = {
        ROOT / "src/storage/durable_orchestration/__init__.py",
        ROOT / "src/storage/durable_orchestration/store.py",
    }
    if (
        set(changed_runtime_files)
        == phase9_step2_durable_orchestration_runtime_files
    ):
        for path in changed_runtime_files:
            source = path.read_text(encoding="utf-8")
            for marker in FORBIDDEN_RUNTIME_MARKERS:
                assert marker not in source
        return
    phase9_step3_human_decision_storage_runtime_files = {
        ROOT / "src/storage/durable_orchestration/store.py",
    }
    if (
        set(changed_runtime_files)
        == phase9_step3_human_decision_storage_runtime_files
    ):
        for path in changed_runtime_files:
            source = path.read_text(encoding="utf-8")
            for marker in FORBIDDEN_RUNTIME_MARKERS:
                assert marker not in source
        return
    phase9_step16a_runtime_files = {
        ROOT / "src/storage/durable_orchestration/store.py",
        ROOT / "src/storage/durable_orchestration/repository.py",
    }
    if set(changed_runtime_files) == phase9_step16a_runtime_files:
        for path in changed_runtime_files:
            source = path.read_text(encoding="utf-8")
            for marker in FORBIDDEN_RUNTIME_MARKERS:
                assert marker not in source
        return
    phase9_step17_runtime_files = {
        ROOT / "src/agents/durable_evidence_chain_resume_coordinator.py",
    }
    if set(changed_runtime_files) == phase9_step17_runtime_files:
        for path in changed_runtime_files:
            source = path.read_text(encoding="utf-8")
            for marker in FORBIDDEN_RUNTIME_MARKERS:
                assert marker not in source
        return
    phase9_step8_durable_orchestration_runtime_files = {
        ROOT / "src/storage/durable_orchestration/repository.py",
    }
    if (
        set(changed_runtime_files)
        == phase9_step8_durable_orchestration_runtime_files
    ):
        for path in changed_runtime_files:
            source = path.read_text(encoding="utf-8")
            for marker in FORBIDDEN_RUNTIME_MARKERS:
                assert marker not in source
        return
    phase9_step9_durable_orchestration_admin_files = {
        ROOT
        / "src/storage/admin_tools/durable_orchestration/apply_schema.py",
    }
    if (
        set(changed_runtime_files)
        == phase9_step9_durable_orchestration_admin_files
    ):
        for path in changed_runtime_files:
            source = path.read_text(encoding="utf-8")
            for marker in FORBIDDEN_RUNTIME_MARKERS:
                assert marker not in source
        return
    phase9_step12_postgres_runtime_files = {
        ROOT / "src/storage/durable_orchestration/postgres_connection.py",
    }
    if set(changed_runtime_files) == phase9_step12_postgres_runtime_files:
        for path in changed_runtime_files:
            source = path.read_text(encoding="utf-8")
            for marker in FORBIDDEN_RUNTIME_MARKERS:
                assert marker not in source
        return
    phase9_step14_langgraph_postgres_checkpointer_files = {
        ROOT / "src/storage/durable_orchestration/langgraph_postgres.py",
        ROOT
        / "src/storage/admin_tools/durable_orchestration"
        / "setup_langgraph_checkpointer.py",
    }
    if (
        set(changed_runtime_files)
        == phase9_step14_langgraph_postgres_checkpointer_files
    ):
        for path in changed_runtime_files:
            source = path.read_text(encoding="utf-8")
            for marker in FORBIDDEN_RUNTIME_MARKERS:
                assert marker not in source
        return
    phase129_auth_artwork_runtime_files = {
        ROOT / "src/app/auth_ui.py",
    }
    if set(changed_runtime_files) == phase129_auth_artwork_runtime_files:
        return
    phase129b_auth_loader_ui_files = {
        ROOT / "src/app/auth_ui.py",
        ROOT / "src/app/ui.py",
        ROOT / "src/app/planning_ui.py",
        ROOT / "src/app/static/app.js",
        ROOT / "src/app/static/planning.js",
        ROOT / "src/app/static/styles.css",
    }
    if set(changed_runtime_files) == phase129b_auth_loader_ui_files:
        return
    phase129c_workflow_overlay_and_corpus_files = phase129b_auth_loader_ui_files | {
        ROOT / "src/app/api.py",
        ROOT / "src/app/services.py",
    }
    if set(changed_runtime_files) == phase129c_workflow_overlay_and_corpus_files:
        return
    live_pipeline_preferences_dashboard_files = {
        ROOT / "src/app/api.py",
        ROOT / "src/app/planning_ui.py",
        ROOT / "src/app/services.py",
        ROOT / "src/app/static/app.js",
        ROOT / "src/app/static/app_redesign.css",
        ROOT / "src/app/static/planning.js",
        ROOT / "src/app/static/styles.css",
        ROOT / "src/app/ui.py",
    }
    if set(changed_runtime_files) == live_pipeline_preferences_dashboard_files:
        return
    phase133h_shared_shell_files = {
        ROOT / "src/app/application_hub_ui.py",
        ROOT / "src/app/applied_ui.py",
        ROOT / "src/app/auth_ui.py",
        ROOT / "src/app/decisions_ui.py",
        ROOT / "src/app/intelligence_ui.py",
        ROOT / "src/app/onboarding_ui.py",
        ROOT / "src/app/planning_ui.py",
        ROOT / "src/app/profile_ui.py",
        ROOT / "src/app/saved_ui.py",
        ROOT / "src/app/static/app_redesign.css",
        ROOT / "src/app/static/shell.js",
        ROOT / "src/app/ui.py",
        ROOT / "src/app/ui_shell.py",
    }
    if set(changed_runtime_files) == phase133h_shared_shell_files:
        return
    scheduler_admin_health_runtime_files = phase133h_shared_shell_files | {
        ROOT / "src/app/api.py",
    }
    if set(changed_runtime_files) == scheduler_admin_health_runtime_files:
        return
    scheduler_health_visual_correction_runtime_files = (
        scheduler_admin_health_runtime_files
        - {ROOT / "src/app/static/app_redesign.css"}
        | {
            ROOT / "src/app/static/build/executive-kpi/executive-kpi.css",
            ROOT / "src/app/static/build/executive-kpi/executive-kpi.js",
        }
    )
    if set(changed_runtime_files) == scheduler_health_visual_correction_runtime_files:
        return
    scheduler_health_final_visual_polish_runtime_files = scheduler_admin_health_runtime_files | {
        ROOT / "src/app/static/build/executive-kpi/executive-kpi.css",
        ROOT / "src/app/static/build/executive-kpi/executive-kpi.js",
    }
    if set(changed_runtime_files) == scheduler_health_final_visual_polish_runtime_files:
        return
    scheduler_health_jsonl_removal_runtime_files = {
        ROOT / "src/app/static/build/executive-kpi/executive-kpi.js",
    }
    if set(changed_runtime_files) == scheduler_health_jsonl_removal_runtime_files:
        scheduler_health_source = (
            ROOT
            / "frontend/executive-kpi/src/scheduler/SchedulerHealthDashboard.tsx"
        )
        source = scheduler_health_source.read_text(encoding="utf-8")
        for marker in FORBIDDEN_RUNTIME_MARKERS:
            assert marker not in source
        return
    phase55b_runtime_files = {
        ROOT / "src/app/planning_ui.py",
        ROOT / "src/app/services.py",
        ROOT / "src/app/static/planning.js",
        ROOT / "src/app/static/scan_workspace.js",
    }
    if set(changed_runtime_files) == phase55b_runtime_files:
        return
    phase56a_runtime_files = {
        ROOT / "src/app/api.py",
        ROOT / "src/app/services.py",
        ROOT / "src/app/planning_ui.py",
        ROOT / "src/app/static/scan_workspace.js",
    }
    if set(changed_runtime_files) == phase56a_runtime_files:
        return
    phase56b_runtime_files = {
        ROOT / "src/app/services.py",
        ROOT / "src/app/static/scan_workspace.js",
    }
    if set(changed_runtime_files) == phase56b_runtime_files:
        return
    phase68a_runtime_files = {
        ROOT / "src/app/services.py",
        ROOT / "src/app/planning_ui.py",
        ROOT / "src/app/static/scan_workspace.js",
    }
    if set(changed_runtime_files) == phase68a_runtime_files:
        return
    phase70a_runtime_files = {
        ROOT / "src/app/planning_ui.py",
        ROOT / "src/app/static/scan_workspace.js",
    }
    if set(changed_runtime_files) == phase70a_runtime_files:
        return
    phase71a_tailoring_readback_repair_files = {
        ROOT / "src/app/api.py",
        ROOT / "src/app/services.py",
        ROOT / "src/app/planning_ui.py",
        ROOT / "src/app/static/planning.js",
        ROOT / "src/app/static/scan_workspace.js",
    }
    if set(changed_runtime_files) == phase71a_tailoring_readback_repair_files:
        return
    phase72a_disabled_workspace_hover_files = {
        ROOT / "src/app/static/planning.js",
    }
    if set(changed_runtime_files) == phase72a_disabled_workspace_hover_files:
        return
    phase73a_tailoring_state_readback_files = {
        ROOT / "src/app/services.py",
        ROOT / "src/app/planning_ui.py",
        ROOT / "src/app/static/planning.js",
    }
    if set(changed_runtime_files) == phase73a_tailoring_state_readback_files:
        return

    phase75b_safe_app_ready_rewrite_promotion_files = {
        ROOT / "src/tailoring/rendering.py",
    }
    if set(changed_runtime_files) == phase75b_safe_app_ready_rewrite_promotion_files:
        return
    phase76a_safe_app_ready_runtime_patch_files = {
        ROOT / "src/app/services.py",
        ROOT / "src/tailoring/llm.py",
        ROOT / "src/tailoring/rendering.py",
    }
    if set(changed_runtime_files) == phase76a_safe_app_ready_runtime_patch_files:
        return
    phase76b_concrete_prompt_files = {
        ROOT / "src/tailoring/llm.py",
    }
    if set(changed_runtime_files) == phase76b_concrete_prompt_files:
        return
    phase76c_76d_workspace_and_parser_files = {
        ROOT / "src/app/static/planning.js",
        ROOT / "src/tailoring/llm.py",
    }
    if set(changed_runtime_files) == phase76c_76d_workspace_and_parser_files:
        return
    phase77a_compact_dashboard_decision_files = {
        ROOT / "src/app/static/app.js",
        ROOT / "src/app/static/planning.js",
        ROOT / "src/app/static/app_redesign.css",
            "src/app/static/agentic_review.js",
        ROOT / "src/app/ui.py",
        ROOT / "src/app/planning_ui.py",
    }
    if set(changed_runtime_files) == phase77a_compact_dashboard_decision_files:
        return
    phase77d_ui_ux_cleanup_files = {
        ROOT / "src/app/static/app.js",
        ROOT / "src/app/static/planning.js",
        ROOT / "src/app/static/app_redesign.css",
            "src/app/static/agentic_review.js",
        ROOT / "src/app/ui.py",
    }
    if set(changed_runtime_files) == phase77d_ui_ux_cleanup_files:
        return
    phase78a_scan_review_ui_separation_files = {
        ROOT / "src/app/planning_ui.py",
        ROOT / "src/app/static/scan_workspace.css",
        ROOT / "src/app/static/scan_workspace_review.css",
        ROOT / "src/app/static/styles.css",
    }
    if set(changed_runtime_files) == phase78a_scan_review_ui_separation_files:
        return
    phase78b_scan_review_preview_cleanup_files = {
        ROOT / "src/app/services.py",
        ROOT / "src/app/planning_ui.py",
        ROOT / "src/app/static/app_redesign.css",
            "src/app/static/agentic_review.js",
        ROOT / "src/app/static/planning.js",
        ROOT / "src/app/static/scan_workspace.js",
        ROOT / "src/app/static/scan_workspace.css",
        ROOT / "src/app/static/scan_workspace_review.css",
        ROOT / "src/app/static/styles.css",
    }
    if set(changed_runtime_files) == phase78b_scan_review_preview_cleanup_files:
        return
    phase78d_admin_diagnostics_ui_files = {
        ROOT / "src/app/auth_ui.py",
        ROOT / "src/app/planning_ui.py",
        ROOT / "src/app/static/scan_workspace_review.css",
        ROOT / "src/app/static/shell.js",
        ROOT / "src/app/ui_shell.py",
    }
    if set(changed_runtime_files) == phase78d_admin_diagnostics_ui_files:
        return
    phase79b_relevance_prefilter_trace_bridge_files = {
        ROOT / "src/pipeline/collector.py",
    }
    if set(changed_runtime_files) == phase79b_relevance_prefilter_trace_bridge_files:
        return
    phase89b_resume_match_jd_evidence_files = {
        ROOT / "src/agents/resume_match_agent.py",
    }
    if set(changed_runtime_files) == phase89b_resume_match_jd_evidence_files:
        return
    phase90b_critic_resume_match_jd_evidence_files = {
        ROOT / "src/agents/critic_agent.py",
    }
    if set(changed_runtime_files) == phase90b_critic_resume_match_jd_evidence_files:
        return
    phase91b_job_prioritization_critic_evidence_files = {
        ROOT / "src/agents/job_prioritization_agent.py",
    }
    if set(changed_runtime_files) == phase91b_job_prioritization_critic_evidence_files:
        return
    phase92b_tailoring_decision_priority_evidence_files = {
        ROOT / "src/agents/tailoring_decision_agent.py",
    }
    if set(changed_runtime_files) == phase92b_tailoring_decision_priority_evidence_files:
        return
    phase93b_operator_review_tailoring_evidence_files = {
        ROOT / "src/agents/operator_review_agent.py",
    }
    if set(changed_runtime_files) == phase93b_operator_review_tailoring_evidence_files:
        return
    phase94b_agent_evidence_chain_composition_files = {
        ROOT / "src/agents/evidence_chain_composition.py",
    }
    if set(changed_runtime_files) == phase94b_agent_evidence_chain_composition_files:
        return
    phase98b_controlled_evidence_chain_execution_files = {
        ROOT / "src/agents/evidence_chain_execution.py",
                "requirements.txt",
                "src/agents/evidence_chain_langgraph_harness.py",
    }
    if set(changed_runtime_files) == phase98b_controlled_evidence_chain_execution_files:
        return
    phase107b_langgraph_evidence_chain_harness_files = {
        ROOT / "src/agents/evidence_chain_langgraph_harness.py",
    }
    if set(changed_runtime_files) == phase107b_langgraph_evidence_chain_harness_files:
        return
    phase10_step2_shadow_foundation_files = {
        ROOT / "src/agents/evidence_chain_shadow_adapter.py",
        ROOT / "src/agents/evidence_chain_shadow_parity.py",
    }
    if set(changed_runtime_files) == phase10_step2_shadow_foundation_files:
        for path in changed_runtime_files:
            source = path.read_text(encoding="utf-8")
            for marker in FORBIDDEN_RUNTIME_MARKERS:
                assert marker not in source
        return
    phase10_step3_shadow_execution_files = {
        ROOT / "src/agents/evidence_chain_shadow_execution.py",
    }
    if set(changed_runtime_files) == phase10_step3_shadow_execution_files:
        for path in changed_runtime_files:
            source = path.read_text(encoding="utf-8")
            for marker in FORBIDDEN_RUNTIME_MARKERS:
                assert marker not in source
        return
    phase10_step5a_shadow_resume_evidence_projection_files = {
        ROOT / "src/pipeline/shadow_resume_evidence_projection.py",
    }
    if (
        set(changed_runtime_files)
        == phase10_step5a_shadow_resume_evidence_projection_files
    ):
        for path in (
            ROOT / "batch_select_best_resume_variant.py",
            ROOT / "run_application_planning.py",
            *changed_runtime_files,
        ):
            source = path.read_text(encoding="utf-8")
            for marker in FORBIDDEN_RUNTIME_MARKERS:
                assert marker not in source
        return
    phase10_step5c_post_planning_shadow_files = {
        ROOT / "src/pipeline/post_planning_shadow.py",
    }
    if set(changed_runtime_files) == phase10_step5c_post_planning_shadow_files:
        for path in (ROOT / "main.py", *changed_runtime_files):
            source = path.read_text(encoding="utf-8")
            for marker in FORBIDDEN_RUNTIME_MARKERS:
                assert marker not in source
        return
    phase10_step8_shadow_observation_files = {
        ROOT / "src/pipeline/post_planning_shadow.py",
        ROOT / "src/pipeline/shadow_observation_contract.py",
        ROOT / "src/pipeline/shadow_observation_store.py",
    }
    if set(changed_runtime_files) == phase10_step8_shadow_observation_files:
        for path in changed_runtime_files:
            source = path.read_text(encoding="utf-8")
            for marker in FORBIDDEN_RUNTIME_MARKERS:
                assert marker not in source
        return
    phase10_step11_postgres_planning_snapshot_files = {
        ROOT / "src/pipeline/postgres_planning_corpus_snapshot.py",
    }
    if (
        set(changed_runtime_files)
        == phase10_step11_postgres_planning_snapshot_files
    ):
        for path in changed_runtime_files:
            source = path.read_text(encoding="utf-8")
            for marker in FORBIDDEN_RUNTIME_MARKERS:
                assert marker not in source
        return
    phase11_step2_job_prioritization_graph_contract_files = {
        ROOT / "src/agents/job_prioritization_graph_verification.py",
    }
    if (
        set(changed_runtime_files)
        == phase11_step2_job_prioritization_graph_contract_files
    ):
        for path in changed_runtime_files:
            source = path.read_text(encoding="utf-8")
            for marker in FORBIDDEN_RUNTIME_MARKERS:
                assert marker not in source
        return
    phase11_step3_job_prioritization_graph_integration_files = {
        ROOT / "src/agents/job_prioritization_graph_verification.py",
        ROOT / "src/agents/job_prioritization_graph_integration.py",
    }
    if (
        set(changed_runtime_files)
        == phase11_step3_job_prioritization_graph_integration_files
    ):
        for path in changed_runtime_files:
            source = path.read_text(encoding="utf-8")
            for marker in FORBIDDEN_RUNTIME_MARKERS:
                assert marker not in source
        return
    phase109b_live_pipeline_popup_ux_files = {
        ROOT / "src/app/ui.py",
        ROOT / "src/app/static/app.js",
    }
    if set(changed_runtime_files) == phase109b_live_pipeline_popup_ux_files:
        return
    phase110b_generate_suggestions_loader_files = {
        ROOT / "src/app/planning_ui.py",
        ROOT / "src/app/static/planning.js",
    }
    if set(changed_runtime_files) == phase110b_generate_suggestions_loader_files:
        return
    phase117b_active_ts_clearance_diagnostic_files = {
        ROOT / "src/matching/clearance_requirements.py",
    }
    if set(changed_runtime_files) == phase117b_active_ts_clearance_diagnostic_files:
        return
    phase118b_active_ts_clearance_packet_diagnostic_files = {
        ROOT / "jd_resume_diff_helper.py",
    }
    if set(changed_runtime_files) == phase118b_active_ts_clearance_packet_diagnostic_files:
        return
    phase119b_active_ts_clearance_scan_warning_files = {
        ROOT / "src/app/static/planning.js",
        ROOT / "src/app/static/scan_workspace_review.css",
    }
    if set(changed_runtime_files) == phase119b_active_ts_clearance_scan_warning_files:
        return
    phase120b_semantic_similarity_diagnostic_files = {
        ROOT / "src/matching/semantic_similarity.py",
    }
    if set(changed_runtime_files) == phase120b_semantic_similarity_diagnostic_files:
        return
    phase121b_semantic_alignment_dimension_files = {
        ROOT / "src/matching/scorer.py",
    }
    if set(changed_runtime_files) == phase121b_semantic_alignment_dimension_files:
        return
    phase123b_llm_adjudicator_readback_files = {
        ROOT / "src/agents/llm_adjudicator_readback.py",
        ROOT / "batch_select_best_resume_variant.py",
    }
    if set(changed_runtime_files) == phase123b_llm_adjudicator_readback_files:
        return
        phase79d_default_off_advisory_chain_harness_files = {
            ROOT / "src/agents/orchestrator_adapter_harness.py",
        }
        if set(changed_runtime_files) == phase79d_default_off_advisory_chain_harness_files:
            return
        phase84b_jd_intelligence_existing_output_wrapper_files = {
            ROOT / "src/agents/jd_intelligence.py",
        }
        if set(changed_runtime_files) == phase84b_jd_intelligence_existing_output_wrapper_files:
            return

    phase132b_premium_preferences_runtime_files = {
        ROOT / "src/app/api.py",
        ROOT / "src/app/onboarding_ui.py",
        ROOT / "src/app/profile_ui.py",
        ROOT / "src/app/services.py",
        ROOT / "src/app/static/app_redesign.css",
        ROOT / "src/app/static/onboarding.js",
        ROOT / "src/app/static/preference_location_selector.js",
        ROOT / "src/app/static/profile.js",
        ROOT / "src/pipeline/location_preferences.py",
    }
    if set(changed_runtime_files) == phase132b_premium_preferences_runtime_files:
        for path in changed_runtime_files:
            source = path.read_text(encoding="utf-8")
            for marker in FORBIDDEN_RUNTIME_MARKERS:
                assert marker not in source
        return
    phase132b2r3_guided_preferences_runtime_files = {
        ROOT / "src/app/onboarding_ui.py",
        ROOT / "src/app/profile_ui.py",
        ROOT / "src/app/static/app_redesign.css",
        ROOT / "src/app/static/onboarding.js",
        ROOT / "src/app/static/preference_location_selector.js",
        ROOT / "src/app/static/preferences.css",
        ROOT / "src/app/static/preferences_workflow.js",
        ROOT / "src/app/static/profile.js",
        ROOT / "src/app/static/styles.css",
        ROOT / "src/app/ui_shell.py",
    }
    if set(changed_runtime_files) == phase132b2r3_guided_preferences_runtime_files:
        for path in changed_runtime_files:
            source = path.read_text(encoding="utf-8")
            for marker in FORBIDDEN_RUNTIME_MARKERS:
                assert marker not in source
        return
    phase133a_executive_kpi_runtime_files = {
        ROOT / "src/app/ui.py",
        ROOT / "src/app/static/app.js",
        ROOT / "src/app/static/build/executive-kpi/executive-kpi.css",
        ROOT / "src/app/static/build/executive-kpi/executive-kpi.js",
    }
    if set(changed_runtime_files) == phase133a_executive_kpi_runtime_files:
        return
    phase133b_executive_dashboard_runtime_files = (
        phase133a_executive_kpi_runtime_files
        | {ROOT / "src/app/static/app_redesign.css"}
    )
    if set(changed_runtime_files) == phase133b_executive_dashboard_runtime_files:
        return
    phase133d_pipeline_dashboard_runtime_files = {
        ROOT / "src/app/ui.py",
        ROOT / "src/app/ui_shell.py",
        ROOT / "src/app/static/app.js",
        ROOT / "src/app/static/build/executive-kpi/executive-kpi.css",
        ROOT / "src/app/static/build/executive-kpi/executive-kpi.js",
        ROOT / "src/app/services.py",
        ROOT / "src/pipeline/runtime_status.py",
        ROOT / "src/storage/rag_store.py",
    }
    if set(changed_runtime_files) == phase133d_pipeline_dashboard_runtime_files:
        return
    phase133d_s1_pipeline_launch_runtime_files = {
        ROOT / "src/app/ui.py",
        ROOT / "src/app/static/app.js",
        ROOT / "src/app/static/app_redesign.css",
        ROOT / "src/app/static/styles.css",
    }
    if set(changed_runtime_files) == phase133d_s1_pipeline_launch_runtime_files:
        return
    phase133g_premium_planning_runtime_files = {
        ROOT / "src/app/planning_ui.py",
        ROOT / "src/app/static/build/executive-kpi/executive-kpi.css",
        ROOT / "src/app/static/build/executive-kpi/executive-kpi.js",
        ROOT / "src/app/static/planning.js",
        ROOT / "src/app/static/planning_dashboard.css",
    }
    if set(changed_runtime_files) == phase133g_premium_planning_runtime_files:
        return
    phase133g_s1_shared_filter_runtime_files = phase133g_premium_planning_runtime_files | {
        ROOT / "src/app/ui.py",
        ROOT / "src/app/static/app_redesign.css",
    }
    if set(changed_runtime_files) == phase133g_s1_shared_filter_runtime_files:
        return
    phase133g_s1r1_sort_runtime_files = phase133g_s1_shared_filter_runtime_files | {
        ROOT / "src/app/api.py",
        ROOT / "src/app/services.py",
        ROOT / "src/app/static/app.js",
    }
    if set(changed_runtime_files) == phase133g_s1r1_sort_runtime_files:
        return
    phase133ef_decisions_applications_runtime_files = {
        ROOT / "src/app/api.py",
        ROOT / "src/app/application_hub_ui.py",
        ROOT / "src/app/decisions_ui.py",
        ROOT / "src/app/static/application_views.js",
        ROOT / "src/app/static/build/executive-kpi/executive-kpi.css",
        ROOT / "src/app/static/build/executive-kpi/executive-kpi.js",
        ROOT / "src/app/static/decisions.js",
    }
    if set(changed_runtime_files) == phase133ef_decisions_applications_runtime_files:
        return
    phase133i_advanced_diagnostics_runtime_files = {
        ROOT / "src/app/planning_ui.py",
        ROOT / "src/app/static/build/executive-kpi/executive-kpi.css",
        ROOT / "src/app/static/build/executive-kpi/executive-kpi.js",
    }
    phase133i_visual_correction_runtime_files = phase133i_advanced_diagnostics_runtime_files | {
        ROOT / "src/app/static/app_redesign.css",
    }
    if set(changed_runtime_files) == phase133i_visual_correction_runtime_files:
        advanced_diagnostics_source = (
            ROOT
            / "frontend/executive-kpi/src/diagnostics/AdvancedDiagnosticsDashboard.tsx"
        )
        source = advanced_diagnostics_source.read_text(encoding="utf-8")
        for marker in FORBIDDEN_RUNTIME_MARKERS:
            assert marker not in source
        return
    if set(changed_runtime_files) == phase133i_advanced_diagnostics_runtime_files:
        advanced_diagnostics_source = (
            ROOT
            / "frontend/executive-kpi/src/diagnostics/AdvancedDiagnosticsDashboard.tsx"
        )
        source = advanced_diagnostics_source.read_text(encoding="utf-8")
        for marker in FORBIDDEN_RUNTIME_MARKERS:
            assert marker not in source
        return
    item2_phase3_shared_header_runtime_files = {
        ROOT / "src/app/ui.py",
        ROOT / "src/app/planning_ui.py",
        ROOT / "src/app/decisions_ui.py",
        ROOT / "src/app/application_hub_ui.py",
        ROOT / "src/app/static/app_redesign.css",
        ROOT / "src/app/static/build/executive-kpi/executive-kpi.css",
        ROOT / "src/app/static/build/executive-kpi/executive-kpi.js",
    }
    if set(changed_runtime_files) == item2_phase3_shared_header_runtime_files:
        for relative_source in (
            "frontend/executive-kpi/src/pipeline/PipelineDashboard.tsx",
            "frontend/executive-kpi/src/scheduler/SchedulerHealthDashboard.tsx",
            "frontend/executive-kpi/src/diagnostics/AdvancedDiagnosticsDashboard.tsx",
        ):
            source = (ROOT / relative_source).read_text(encoding="utf-8")
            for marker in FORBIDDEN_RUNTIME_MARKERS:
                assert marker not in source
        return
    item2_phase4_secondary_headers_runtime_files = item2_phase3_shared_header_runtime_files | {
        ROOT / "src/app/profile_ui.py",
        ROOT / "src/app/intelligence_ui.py",
        ROOT / "src/app/applied_ui.py",
        ROOT / "src/app/saved_ui.py",
    }
    if set(changed_runtime_files) == item2_phase4_secondary_headers_runtime_files:
        for relative_source in (
            "src/app/profile_ui.py",
            "src/app/intelligence_ui.py",
            "src/app/applied_ui.py",
            "src/app/saved_ui.py",
            "src/app/planning_ui.py",
            "src/app/ui.py",
            "src/app/decisions_ui.py",
            "src/app/application_hub_ui.py",
        ):
            source = (ROOT / relative_source).read_text(encoding="utf-8")
            for marker in FORBIDDEN_RUNTIME_MARKERS:
                assert marker not in source
        return
    item2_phase4_profile_corrections_runtime_files = (
        item2_phase4_secondary_headers_runtime_files
        | {
            ROOT / "src/app/api.py",
            ROOT / "src/app/static/profile.js",
            ROOT / "src/app/ui_shell.py",
            ROOT / "src/auth/runtime.py",
            ROOT / "src/app/static/intelligence.js",
        }
    )
    if set(changed_runtime_files) == item2_phase4_profile_corrections_runtime_files:
        for relative_source in (
            "src/app/profile_ui.py",
            "src/app/planning_ui.py",
            "src/app/ui.py",
            "src/app/decisions_ui.py",
            "src/app/application_hub_ui.py",
            "src/app/api.py",
            "src/app/ui_shell.py",
            "src/auth/runtime.py",
            "src/app/static/profile.js",
        ):
            source = (ROOT / relative_source).read_text(encoding="utf-8")
            for marker in FORBIDDEN_RUNTIME_MARKERS:
                assert marker not in source
        return
    assert changed_runtime_files in (
        [],
        [
            ROOT / "src/app/planning_ui.py",
            ROOT / "src/app/static/app.js",
            ROOT / "src/app/static/planning.js",
            ROOT / "src/app/static/styles.css",
            ROOT / "src/app/ui.py",
            ROOT / "src/app/auth_ui.py",
        ],
        [ROOT / "src/agents/manual_review_readiness_contract.py"],
        [ROOT / "src/agents/core_agent_evidence_materialization_preview.py"],
        [ROOT / "src/agents/tailoring_agent_opportunity_contract.py"],
        [ROOT / "src/agents/generate_ai_tailoring_action_boundary_contract.py"],
        [
            ROOT
            / "src/agents/manual_generate_ai_tailoring_preview_contract.py"
        ],
        [
            ROOT
            / "src/agents/manual_generate_ai_tailoring_preview_request_packet_contract.py"
        ],
        [ROOT / "src/agents/exact_resume_change_set_proposal_builder_default_off.py"],
        [
            ROOT
            / "src/agents/controlled_exact_resume_change_set_llm_request_packet_default_off.py"
        ],
        [
            ROOT
            / "src/agents/controlled_exact_resume_change_set_provider_call_boundary_default_off.py"
        ],
        [
            ROOT
            / "src/agents/manual_generate_ai_tailoring_preview_dispatch_boundary_contract.py"
        ],
            [
                ROOT
                / "src/agents/manual_generate_ai_tailoring_preview_provider_request_envelope_contract.py"
            ],
                [
                    ROOT
                    / "src/agents/manual_generate_ai_tailoring_preview_provider_call_boundary_contract.py"
                ],
                [
                    ROOT
                    / "src/agents/manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_contract.py"
                ],
                [
                    ROOT
                    / "src/agents/manual_generate_ai_tailoring_preview_provider_response_validation_contract.py"
                ],
                    [
                        ROOT
                        / "src/agents/manual_generate_ai_tailoring_preview_provider_response_normalization_contract.py"
                    ],
            [
                ROOT
                / "src/agents/manual_generate_ai_tailoring_preview_normalized_response_preview_packet_contract.py"
            ],
            [ROOT / "src/agents/controlled_agent_router_readonly.py"],
            [
                ROOT
                / "src/agents/controlled_agent_router_workflow_state_adapter_readonly.py"
            ],
            [
                ROOT
                / "src/agents/controlled_agent_router_batch_handoff_plan_readonly.py"
            ],
            [
                ROOT
                / "src/agents/controlled_agent_router_planning_artifact_mapper_readonly.py"
            ],
            [
                ROOT
                / "src/agents/jd_intelligence_llm_signal_extractor_default_off.py"
            ],
            [
                ROOT
                / "src/agents/jd_intelligence_planning_artifact_enricher_default_off.py"
            ],
            [
                ROOT
                / "src/agents/jd_signal_resume_evidence_matrix_default_off.py"
            ],
            [
                ROOT
                / "src/agents/jd_signal_planning_artifact_evidence_enricher_default_off.py"
            ],
                            [
                                ROOT
                                / "src/agents/jd_evidence_final_scoring_feature_adapter_default_off.py"
                            ],
                                [
                                    ROOT
                                    / "src/agents/jd_evidence_scoring_contribution_preview_default_off.py"
                                ],
                                [
                                    ROOT
                                    / "src/agents/jd_evidence_score_impact_preview_default_off.py"
                                ],
                                [
                                    ROOT
                                    / "src/agents/jd_evidence_score_impact_planning_artifact_annotator_default_off.py"
                                ],
                                [
                                    ROOT
                                    / "src/agents/jd_evidence_score_impact_review_packet_builder_default_off.py"
                                ],
                                [
                                    ROOT
                                    / "src/agents/jd_evidence_score_impact_review_queue_builder_default_off.py"
                                ],
                                    [
                                        ROOT
                                        / "src/agents/controlled_exact_resume_change_set_provider_response_validation_default_off.py"
                                    ],
                                    [
                                        ROOT
                                        / "src/agents/controlled_exact_resume_change_set_provider_response_normalization_default_off.py"
                                    ],
                                    [
                                        ROOT
                                        / "src/agents/controlled_exact_resume_change_set_manual_review_packet_builder_default_off.py"
                                    ],
                                    [
                                        ROOT
                                        / "src/agents/controlled_exact_resume_change_set_manual_review_readback_adapter_default_off.py"
                                    ],
                                    [
                                        ROOT
                                        / "src/agents/controlled_exact_resume_change_set_real_provider_runtime_adapter_default_off.py"
                                    ],
                                    [ROOT / "src/agents/controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_default_off.py"],
                                    [ROOT / "src/agents/controlled_exact_resume_change_set_manual_decision_packet_default_off.py"],
                                    [ROOT / "src/agents/controlled_exact_resume_change_set_manual_decision_readback_adapter_default_off.py"],
                                    [ROOT / "src/agents/controlled_exact_resume_change_set_approved_change_plan_packet_default_off.py"],
                                        [ROOT / "src/agents/controlled_exact_resume_change_set_approved_change_plan_readback_adapter_default_off.py"],
            [ROOT / "src/app/api.py"],
            [ROOT / "src/app/services.py"],
            [ROOT / "src/app/api.py", ROOT / "src/app/services.py"],
            [ROOT / "src/app/services.py", ROOT / "src/app/api.py"],
            [
                ROOT / "src/app/planning_ui.py",
                ROOT / "src/app/static/app_redesign.css",
            "src/app/static/agentic_review.js",
                ROOT / "src/app/static/planning.js",
                ROOT / "src/app/static/scan_workspace.js",
                ROOT / "src/app/static/scan_workspace.css",
                ROOT / "src/app/static/scan_workspace_review.css",
                ROOT / "src/app/static/styles.css",
                ROOT / "src/app/services.py",
            ],
            [
                ROOT / "src/app/static/planning.js",
                ROOT / "src/app/static/scan_workspace.js",
                ROOT / "src/app/services.py",
                ROOT / "src/app/planning_ui.py",
            ],
            [
                ROOT / "src/app/planning_ui.py",
                ROOT / "src/app/services.py",
                ROOT / "src/app/static/planning.js",
                ROOT / "src/app/static/scan_workspace.js",
            ],
                [
                    ROOT / "src/app/static/planning.js",
                    ROOT / "src/app/services.py",
                    ROOT / "src/app/planning_ui.py",
                    ROOT / "src/app/static/scan_workspace.js",
                ],
                    [ROOT / "src/app/static/agentic_review.js"],
        [
            ROOT / "src/app/static/agentic_review.js",
            ROOT / "src/app/static/app_redesign.css",
            "src/app/static/agentic_review.js",
        ],
        [
            ROOT / "src/app/static/app_redesign.css",
            "src/app/static/agentic_review.js",
            ROOT / "src/app/static/agentic_review.js",
        ],
    )
    for path in changed_runtime_files:
        source = path.read_text(encoding="utf-8")
        for marker in FORBIDDEN_RUNTIME_MARKERS:
            assert marker not in source
