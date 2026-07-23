"""Shared test-only helpers for legacy phase guard checks."""

from __future__ import annotations

import ast
from hashlib import sha256
from pathlib import Path
import subprocess
from typing import Iterable, Mapping


KNOWN_LEGACY_DUPLICATE_TEST_PATHS = {
    "tests/test_phase105b_critic_controlled_llm_manual_runtime_wiring_default_off 2.py",
    "tests/test_phase105b_critic_controlled_llm_manual_runtime_wiring_default_off 3.py",
    "tests/test_phase69a_agentic_workflow_production_readiness_checkpoint_default_off 2.py",
    "tests/test_phase69b_agentic_workflow_production_readiness_readback_ui_api_default_off 2.py",
}

def normalize_changed_path(path: str | Path) -> str:
    """Return a normalized repo-relative path string for guard comparisons."""
    value = str(path).strip().replace("\\", "/")
    previous = None
    while value != previous:
        previous = value
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1].strip()
    return value


def get_changed_files(root: str | Path) -> set[str]:
    """Return staged, unstaged, and untracked repo-relative changed paths."""
    repo = Path(root)
    tracked = subprocess.check_output(
        ["git", "diff", "--name-only"], cwd=repo, text=True
    ).splitlines()
    staged = subprocess.check_output(
        ["git", "diff", "--name-only", "--cached"], cwd=repo, text=True
    ).splitlines()
    untracked = subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=repo,
        text=True,
    ).splitlines()
    return {
        normalize_changed_path(path)
        for path in [*tracked, *staged, *untracked]
        if normalize_changed_path(path)
    }


def duplicate_artifact_paths(changed: Iterable[str | Path]) -> set[str]:
    """Detect suspicious duplicate artifact names such as ``foo 2.py``."""
    duplicates = set()
    for path in changed:
        normalized = normalize_changed_path(path)
        if normalized in KNOWN_LEGACY_DUPLICATE_TEST_PATHS:
            continue
        if normalized.endswith((" 2.py", " 3.py", " 2.md", " 3.md")):
            duplicates.add(normalized)
    return duplicates


def reject_duplicate_artifact_paths(
    changed: Iterable[str | Path],
) -> None:
    duplicates = duplicate_artifact_paths(changed)
    assert not duplicates, "Duplicate artifact paths are not allowed: " + ", ".join(
        sorted(duplicates)
    )


def merge_allowed(*groups: Iterable[str | Path]) -> set[str]:
    merged = set()
    for group in groups:
        merged.update(normalize_changed_path(path) for path in group)
    return {path for path in merged if path}


def legacy_guard_allowlist(profile: str) -> set[str]:
    profiles = {
        "config_vocabulary_scoring_change": {
            "src/config/consts.py",
            "tests/test_phase115a_applied_ai_scoring_fix.py",
            "tests/test_phase116a_applied_ai_scoring_fix.py",
            "src/matching/clearance_requirements.py",
            "tests/test_phase117b_ts_clearance_diagnostic.py",
            "jd_resume_diff_helper.py",
            "tests/test_phase118b_ts_clearance_packet_diagnostic.py",
            "tests/test_phase119b_ts_clearance_scan_warning_static_only.py",
            "src/matching/semantic_similarity.py",
            "tests/test_phase120b_semantic_similarity_diagnostic.py",
            "src/matching/scorer.py",
            "tests/test_phase121b_semantic_alignment_dimension_default_off.py",
            "tests/test_phase18_human_approval_gate_contract_default_off.py",
            "tests/test_phase18_live_provider_activation_plan_default_off.py",
            "tests/test_phase18_live_provider_dry_run_packet_contract_default_off.py",
            "tests/test_phase18_live_readiness_approval_boundary_default_off.py",
            "tests/test_phase18_mutation_boundary_readiness_contract_default_off.py",
            "tests/test_phase18_operator_decision_capture_contract_default_off.py",
            "tests/test_phase18_provider_call_boundary_readiness_contract_default_off.py",
            "tests/test_phase18_provider_readback_audit_contract_default_off.py",
            "tests/test_phase18_provider_response_validation_contract_default_off.py",
            "tests/test_phase18_provider_runtime_adapter_contract_default_off.py",
            "tests/test_phase19a_three_core_approval_preview_runtime_readonly_default_off.py",
            "tests/test_phase19b_three_core_approval_preview_service_readback_default_off.py",
            "tests/test_phase19c_three_core_approval_preview_api_readback_default_off.py",
            "tests/test_phase19d_three_core_approval_preview_ui_readback_default_off.py",
            "tests/test_phase19e_three_core_approval_preview_ui_api_fetch_default_off.py",
            "tests/test_phase19f_approval_preview_operator_decision_preview_default_off.py",
            "tests/test_phase19g_operator_decision_capture_readback_contract_default_off.py",
            "tests/test_phase19h_operator_decision_capture_api_readback_default_off.py",
            "tests/test_phase19i_operator_decision_capture_ui_readback_default_off.py",
            "tests/test_phase19j_readonly_approval_workflow_release_checkpoint_default_off.py",
            "tests/test_phase21c_manual_review_readiness_api_readback_default_off.py",
            "tests/test_phase21d_manual_review_readiness_ui_readback_default_off.py",
            "tests/test_phase22a_manual_review_ux_hardening_default_off.py",
            "tests/test_phase22b_core_agent_automation_mutation_inventory_default_off.py",
            "tests/test_phase22c_core_agent_evidence_materialization_preview_default_off.py",
            "tests/test_phase22d_core_agent_evidence_materialization_api_readback_default_off.py",
            "tests/test_phase22e_core_agent_evidence_materialization_ui_readback_default_off.py",
            "tests/test_phase22f_core_agent_evidence_materialization_release_checkpoint_default_off.py",
            "tests/test_phase23a_tailoring_agent_opportunity_contract_default_off.py",
            "tests/test_phase23b_tailoring_agent_opportunity_api_readback_default_off.py",
            "tests/test_phase23c_tailoring_agent_opportunity_ui_readback_default_off.py",
            "tests/test_phase23d_generate_ai_tailoring_action_boundary_contract_default_off.py",
            "tests/test_phase23e_generate_ai_tailoring_action_boundary_api_readback_default_off.py",
            "tests/test_phase23f_generate_ai_tailoring_action_boundary_ui_readback_default_off.py",
            "tests/test_phase23g_tailoring_agent_workflow_release_checkpoint_default_off.py",
            "tests/test_phase24a_manual_generate_ai_tailoring_preview_contract_default_off.py",
            "tests/test_phase24b_manual_generate_ai_tailoring_preview_api_readback_default_off.py",
            "tests/test_phase24c_manual_generate_ai_tailoring_preview_ui_readback_default_off.py",
            "tests/test_phase24d_manual_generate_ai_tailoring_preview_release_checkpoint_default_off.py",
            "tests/test_phase25a_manual_generate_ai_tailoring_preview_request_packet_contract_default_off.py",
            "tests/test_phase25b_manual_generate_ai_tailoring_preview_request_packet_api_readback_default_off.py",
            "tests/test_phase25c_manual_generate_ai_tailoring_preview_request_packet_ui_readback_default_off.py",
            "tests/test_phase25d_manual_generate_ai_tailoring_preview_request_packet_release_checkpoint_default_off.py",
            "tests/test_phase26a_manual_generate_ai_tailoring_preview_dispatch_boundary_contract_default_off.py",
            "tests/test_phase26b_manual_generate_ai_tailoring_preview_dispatch_boundary_api_readback_default_off.py",
            "tests/test_phase26c_manual_generate_ai_tailoring_preview_dispatch_boundary_ui_readback_default_off.py",
            "tests/test_phase26d_manual_generate_ai_tailoring_preview_dispatch_boundary_release_checkpoint_default_off.py",
            "tests/test_phase27a_manual_generate_ai_tailoring_preview_provider_request_envelope_contract_default_off.py",
            "tests/test_phase27b_manual_generate_ai_tailoring_preview_provider_request_envelope_api_readback_default_off.py",
            "tests/test_phase27c_manual_generate_ai_tailoring_preview_provider_request_envelope_ui_readback_default_off.py",
            "tests/test_phase27d_manual_generate_ai_tailoring_preview_provider_request_envelope_release_checkpoint_default_off.py",
            "tests/test_phase28a_manual_generate_ai_tailoring_preview_provider_call_boundary_contract_default_off.py",
            "tests/test_phase28b_manual_generate_ai_tailoring_preview_provider_call_boundary_api_readback_default_off.py",
            "tests/test_phase28c_manual_generate_ai_tailoring_preview_provider_call_boundary_ui_readback_default_off.py",
            "tests/test_phase28d_manual_generate_ai_tailoring_preview_provider_call_boundary_release_checkpoint_default_off.py",
            "tests/test_phase29a_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_contract_default_off.py",
            "tests/test_phase29b_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_api_readback_default_off.py",
            "tests/test_phase29c_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_ui_readback_default_off.py",
            "tests/test_phase29d_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_release_checkpoint_default_off.py",
            "tests/test_phase30a_manual_generate_ai_tailoring_preview_provider_response_validation_contract_default_off.py",
            "tests/test_phase30b_manual_generate_ai_tailoring_preview_provider_response_validation_api_readback_default_off.py",
            "tests/test_phase30c_manual_generate_ai_tailoring_preview_provider_response_validation_ui_readback_default_off.py",
            "tests/test_phase30d_manual_generate_ai_tailoring_preview_provider_response_validation_release_checkpoint_default_off.py",
            "tests/test_phase31a_manual_generate_ai_tailoring_preview_provider_response_normalization_contract_default_off.py",
            "tests/test_phase31b_manual_generate_ai_tailoring_preview_provider_response_normalization_api_readback_default_off.py",
            "tests/test_phase31c_manual_generate_ai_tailoring_preview_provider_response_normalization_ui_readback_default_off.py",
            "tests/test_phase31d_manual_generate_ai_tailoring_preview_provider_response_normalization_release_checkpoint_default_off.py",
            "tests/test_phase32a_manual_generate_ai_tailoring_preview_normalized_response_preview_packet_contract_default_off.py",
            "tests/test_phase32b_manual_generate_ai_tailoring_preview_normalized_response_preview_packet_api_readback_default_off.py",
            "tests/test_phase33a_controlled_agent_router_readonly.py",
            "tests/test_phase33b_controlled_agent_router_workflow_state_adapter_readonly.py",
            "tests/test_phase33c_controlled_agent_router_batch_handoff_plan_readonly.py",
            "tests/test_phase33d_controlled_agent_router_planning_artifact_mapper_readonly.py",
            "tests/test_phase33e_controlled_agent_router_planning_artifact_dry_run_command_readonly.py",
            "tests/test_phase34c_jd_intelligence_planning_artifact_enrichment_dry_run_command_default_off.py",
            "tests/test_phase35a_jd_signal_resume_evidence_matrix_default_off.py",
            "tests/test_phase35b_jd_signal_planning_artifact_evidence_enricher_default_off.py",
            "tests/test_phase35c_jd_signal_planning_artifact_evidence_enrichment_dry_run_command_default_off.py",
            "tests/test_phase36b_jd_evidence_final_scoring_feature_adapter_dry_run_command_default_off.py",
            "tests/test_phase37a_jd_evidence_scoring_contribution_preview_default_off.py",
            "tests/test_phase37b_jd_evidence_scoring_contribution_preview_dry_run_command_default_off.py",
            "tests/test_phase38a_jd_evidence_score_impact_preview_default_off.py",
            "tests/test_phase38b_jd_evidence_score_impact_preview_dry_run_command_default_off.py",
            "tests/test_phase39a_jd_evidence_score_impact_planning_artifact_annotator_default_off.py",
            "tests/test_phase39b_jd_evidence_score_impact_planning_artifact_annotator_dry_run_command_default_off.py",
            "tests/test_phase40a_jd_evidence_score_impact_review_packet_builder_default_off.py",
            "tests/test_phase40b_jd_evidence_score_impact_review_packet_builder_dry_run_command_default_off.py",
            "tests/test_phase41a_jd_evidence_score_impact_review_queue_builder_default_off.py",
            "tests/test_phase41b_jd_evidence_score_impact_review_queue_builder_dry_run_command_default_off.py",
            "tests/test_phase42a_exact_resume_change_set_proposal_builder_default_off.py",
            "tests/test_phase42b_exact_resume_change_set_proposal_builder_dry_run_command_default_off.py",
            "tests/test_phase43a_controlled_exact_resume_change_set_llm_request_packet_default_off.py",
            "tests/test_phase43b_controlled_exact_resume_change_set_llm_request_packet_dry_run_command_default_off.py",
            "tests/test_phase44a_controlled_exact_resume_change_set_provider_call_boundary_default_off.py",
            "tests/test_phase44b_controlled_exact_resume_change_set_provider_call_boundary_dry_run_command_default_off.py",
            "tests/test_phase45a_controlled_exact_resume_change_set_provider_response_validation_default_off.py",
            "tests/test_phase45b_controlled_exact_resume_change_set_provider_response_validation_dry_run_command_default_off.py",
            "tests/test_phase46a_controlled_exact_resume_change_set_provider_response_normalization_default_off.py",
            "tests/test_phase46b_controlled_exact_resume_change_set_provider_response_normalization_dry_run_command_default_off.py",
            "tests/test_phase47a_controlled_exact_resume_change_set_manual_review_packet_builder_default_off.py",
            "tests/test_phase47b_controlled_exact_resume_change_set_manual_review_packet_builder_dry_run_command_default_off.py",
            "tests/test_phase48a_controlled_exact_resume_change_set_manual_review_readback_adapter_default_off.py",
            "tests/test_phase48b_controlled_exact_resume_change_set_manual_review_readback_adapter_dry_run_command_default_off.py",
            "tests/test_phase49a_controlled_exact_resume_change_set_real_provider_runtime_adapter_default_off.py",
            "tests/test_phase49b_controlled_exact_resume_change_set_real_provider_runtime_adapter_dry_run_command_default_off.py",
            "tests/test_phase50a_controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_default_off.py",
            "tests/test_phase50b_controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_dry_run_command_default_off.py",
            "tests/test_phase51a_controlled_exact_resume_change_set_manual_decision_packet_default_off.py",
            "tests/test_phase51b_controlled_exact_resume_change_set_manual_decision_packet_dry_run_command_default_off.py",
            "tests/test_phase52a_controlled_exact_resume_change_set_manual_decision_readback_adapter_default_off.py",
            "tests/test_phase52b_controlled_exact_resume_change_set_manual_decision_readback_adapter_dry_run_command_default_off.py",
            "tests/test_phase53a_controlled_exact_resume_change_set_approved_change_plan_packet_default_off.py",
            "tests/test_phase53b_controlled_exact_resume_change_set_approved_change_plan_packet_dry_run_command_default_off.py",
            "tests/test_phase54a_controlled_exact_resume_change_set_approved_change_plan_readback_adapter_default_off.py",
            "tests/test_phase55a_live_jd_llm_extraction_planning_scan_wiring_default_off.py",
            "tests/test_phase55b_live_jd_llm_extraction_planning_scan_readback_ui_api_default_off.py",
            "tests/test_phase56a_live_tailoring_suggestion_planning_workspace_wiring_default_off.py",
            "tests/test_phase56b_live_tailoring_suggestion_planning_workspace_readback_ui_api_default_off.py",
            "tests/test_phase57a_live_exact_resume_change_proposal_planning_workspace_wiring_default_off.py",
            "tests/test_phase57b_live_exact_resume_change_proposal_planning_workspace_readback_ui_api_default_off.py",
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
            "tests/test_phase68b_end_to_end_agentic_workflow_integration_readback_ui_api_default_off.py",
            "tests/test_phase69a_agentic_workflow_production_readiness_checkpoint_default_off.py",
            "tests/test_phase69a_agentic_workflow_production_readiness_checkpoint_default_off 2.py",
            "tests/test_phase69b_agentic_workflow_production_readiness_readback_ui_api_default_off.py",
            "tests/test_phase69b_agentic_workflow_production_readiness_readback_ui_api_default_off 2.py",
            "tests/test_phase70a_ux_polish_agentic_workflow_demo_readiness_default_off.py",
            "tests/test_phase70b_ux_polish_agentic_workflow_demo_readiness_readback_default_off.py",
            "tests/support/phase_guard_registry.py",
            "tests/test_phase85b_legacy_guard_registry_default_off.py",
            "tests/test_phase18_approval_preview_readonly_default_off.py",
            "tests/test_phase18_safety_wrap_release_checkpoint_default_off.py",
            "tests/test_phase20a_provider_call_readiness_experiment_default_off.py",
            "tests/test_phase20b_provider_call_readiness_api_readback_default_off.py",
            "tests/test_phase20c_provider_call_readiness_ui_readback_default_off.py",
            "tests/test_phase20e_provider_readiness_release_checkpoint_default_off.py",
            "tests/test_phase21b_manual_review_readiness_contract_default_off.py",
            "tests/test_phase21e_manual_review_workflow_release_checkpoint_default_off.py",
            "tests/test_phase34a_jd_intelligence_llm_signal_extractor_default_off.py",
            "tests/test_phase34b_jd_intelligence_planning_artifact_enricher_default_off.py",
            "tests/test_phase36a_jd_evidence_final_scoring_feature_adapter_default_off.py",
            "tests/test_phase104b_critic_controlled_llm_ownership_default_off.py",
            "tests/test_phase105b_critic_controlled_llm_manual_runtime_wiring_default_off.py",
            "tests/test_phase109b_live_pipeline_popup_ux_static_only.py",
            "tests/test_three_core_shadow_readiness_wrap_default_off.py",
            "tests/test_portfolio_demo_readiness_wrap_checkpoint.py",
        },
        "phase85b_registry": {
            "tests/support/phase_guard_registry.py",
            "tests/test_phase85b_legacy_guard_registry_default_off.py",
            "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
            "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
            "tests/test_phase104b_critic_controlled_llm_ownership_default_off.py",
            "tests/test_phase105b_critic_controlled_llm_manual_runtime_wiring_default_off.py",
            "tests/test_three_core_shadow_readiness_wrap_default_off.py",
            "tests/test_portfolio_demo_readiness_wrap_checkpoint.py",
            "tests/test_agent_trace_ui_readiness_checkpoint.py",
            "tests/test_agent_trace_readonly_ui_panel_no_api_no_writes.py",
            "tests/test_agent_trace_polish_ux_hardening_ui_only_no_api_no_writes.py",
            "tests/test_three_core_agent_collector_shadow_wiring_default_off.py",
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
            "src/agents/operator_review_agent.py",
            "tests/test_phase93b_operator_review_consumes_tailoring_decision_evidence_default_off.py",
            "src/agents/evidence_chain_composition.py",
            "tests/test_phase94b_agent_evidence_chain_composition_default_off.py",
            "tests/test_phase95b_agent_evidence_chain_trace_payload_default_off.py",
            "tests/test_phase96b_agent_evidence_chain_trace_persistence_default_off.py",
            "tests/test_phase97b_agent_evidence_chain_collector_diagnostics_default_off.py",
            "src/agents/evidence_chain_execution.py",
            "tests/test_phase98b_controlled_evidence_chain_execution_default_off.py",
            "tests/test_phase99b_collector_controlled_evidence_chain_execution_default_off.py",
            "tests/test_phase100b_evidence_chain_trace_persistence_readback_default_off.py",
            "tests/test_phase101b_evidence_chain_api_service_readback_default_off.py",
            "tests/test_phase102b_jd_intelligence_controlled_llm_ownership_default_off.py",
            "tests/test_phase103b_jd_intelligence_controlled_llm_collector_wiring_default_off.py",
            "tests/test_phase104b_critic_controlled_llm_ownership_default_off.py",
            "tests/test_phase105b_critic_controlled_llm_manual_runtime_wiring_default_off.py",
            "src/app/static/agentic_review.js",
            "tests/test_phase106b_agentic_review_evidence_chain_ui_readback_default_off.py",
            "tests/test_resume_match_dry_run_contract_no_pipeline_change.py",
            "requirements.txt",
            "src/agents/evidence_chain_langgraph_harness.py",
            "tests/test_phase107b_langgraph_evidence_chain_harness_default_off.py",
            "tests/test_phase108a_collector_langgraph_evidence_chain_execution_default_off.py",
            "src/app/ui.py",
            "src/app/static/app.js",
            "tests/test_phase109b_live_pipeline_popup_ux_static_only.py",
            "src/app/planning_ui.py",
            "src/app/static/planning.js",
            "tests/test_phase71a_tailoring_workspace_artifact_path_preload_repair_default_off.py",
            "tests/test_phase110b_generate_suggestions_loader_static_only.py",
            "tests/test_critic_provider_shadow_default_off.py",
            "tests/test_jd_intelligence_provider_shadow_default_off.py",
            "tests/test_jd_live_provider_canary_api_readback_default_off.py",
            "tests/test_jd_live_provider_canary_command_default_off.py",
            "tests/test_jd_live_provider_canary_default_off.py",
            "tests/test_jd_live_provider_canary_readback_default_off.py",
            "tests/test_jd_live_provider_canary_readiness_checkpoint_default_off.py",
            "tests/test_jd_live_provider_canary_runbook_default_off.py",
            "tests/test_jd_live_provider_canary_service_readback_default_off.py",
            "tests/test_jd_live_provider_canary_shadow_bridge_default_off.py",
            "tests/test_jd_live_provider_canary_ui_readback_default_off.py",
            "tests/test_jd_live_provider_external_adapter_default_off.py",
            "tests/test_jd_manual_live_canary_readiness_checkpoint_default_off.py",
            "tests/test_jd_provider_runtime_activation_default_off.py",
            "tests/test_jd_provider_runtime_api_readback_default_off.py",
            "tests/test_jd_provider_runtime_readiness_checkpoint_default_off.py",
            "tests/test_jd_provider_runtime_review_packet_default_off.py",
            "tests/test_jd_provider_runtime_service_readback_default_off.py",
            "tests/test_jd_provider_runtime_shadow_bridge_default_off.py",
            "tests/test_jd_provider_runtime_trace_readback_default_off.py",
            "tests/test_jd_provider_runtime_ui_readback_default_off.py",
            "tests/test_pgvector_connection_provider_default_off.py",
            "tests/test_pgvector_extension_probe_api_no_schema_no_ui.py",
            "tests/test_pgvector_extension_probe_contract_no_schema.py",
            "tests/test_pgvector_extension_probe_service_helper_no_schema.py",
            "tests/test_pgvector_extension_probe_ui_no_schema_readonly.py",
            "tests/test_pgvector_local_smoke_default_off.py",
            "tests/test_pgvector_real_local_smoke_command_default_off.py",
            "tests/test_pgvector_schema_store_adapter_default_off.py",
            "tests/test_pgvector_smoke_readback_verification_default_off.py",
            "tests/test_pgvector_store_db_executor_default_off.py",
            "tests/test_phase8_pgvector_backend_readiness_schema_plan_no_runtime_change.py",
            "tests/test_pipeline_embedding_retrieval_hook_default_off.py",
            "tests/test_pipeline_runtime_embedding_bridge_default_off.py",
            "tests/test_pipeline_vector_evidence_hook_default_off.py",
            "tests/test_provider_live_activation_safety_plan_default_off.py",
            "tests/test_provider_live_config_gate_default_off.py",
            "tests/test_provider_runtime_activation_plan_default_off.py",
            "tests/test_provider_runtime_api_readback_default_off.py",
            "tests/test_provider_runtime_readiness_checkpoint_default_off.py",
            "tests/test_provider_runtime_service_bridge_default_off.py",
            "tests/test_provider_runtime_ui_readback_default_off.py",
            "tests/test_semantic_evidence_quality_gate_default_off.py",
            "tests/test_shadow_agent_vector_evidence_input_default_off.py",
            "tests/test_shadow_semantic_evidence_agent_input_default_off.py",
            "tests/test_shadow_vector_evidence_context_default_off.py",
            "tests/test_tailoring_provider_shadow_default_off.py",
            "tests/test_three_agent_llmops_aggregate_default_off.py",
            "tests/test_three_agent_llmops_observability_api_default_off.py",
            "tests/test_three_agent_llmops_observability_readback_default_off.py",
            "tests/test_three_agent_llmops_observability_service_bridge_default_off.py",
            "tests/test_three_agent_llmops_observability_ui_default_off.py",
            "tests/test_three_agent_llmops_trace_contract_default_off.py",
            "tests/test_three_agent_provider_handoff_default_off.py",
            "tests/test_three_agent_shadow_workflow_default_off.py",
            "tests/test_three_agent_workflow_readiness_default_off.py",
            "tests/test_vector_evidence_api_no_db_no_ui.py",
            "tests/test_vector_evidence_contract_default_off_no_dependency.py",
            "tests/test_vector_evidence_embedding_indexing_helper_default_off.py",
            "tests/test_vector_evidence_embedding_provider_contract_default_off.py",
            "tests/test_vector_evidence_embedding_retrieval_helper_default_off.py",
            "tests/test_vector_evidence_embedding_runtime_adapter_default_off.py",
            "tests/test_vector_evidence_embedding_runtime_service_bridge_default_off.py",
            "tests/test_vector_evidence_indexing_dry_run_no_db.py",
            "tests/test_vector_evidence_readback_api_default_off.py",
            "tests/test_vector_evidence_readback_service_helper_default_off.py",
            "tests/test_vector_evidence_readback_ui_default_off.py",
            "tests/test_vector_evidence_retrieval_dry_run_no_db.py",
            "tests/test_vector_evidence_service_connection_provider_bridge_default_off.py",
            "tests/test_vector_evidence_service_db_executor_bridge_default_off.py",
            "tests/test_vector_evidence_service_helper_no_db_no_api_ui.py",
            "tests/test_vector_evidence_service_pgvector_store_flagged_default_off.py",
            "tests/test_vector_evidence_ui_no_db_readonly.py",
        },
        "active_ts_clearance_diagnostic": {
            "src/matching/clearance_requirements.py",
            "tests/test_phase117b_ts_clearance_diagnostic.py",
        },
        "active_ts_clearance_packet_diagnostic": {
            "jd_resume_diff_helper.py",
            "tests/test_phase118b_ts_clearance_packet_diagnostic.py",
        },
        "active_ts_clearance_scan_warning_readback": {
            "src/app/static/planning.js",
            "src/app/static/scan_workspace_review.css",
            "tests/test_phase119b_ts_clearance_scan_warning_static_only.py",
        },
        "semantic_similarity_diagnostic_only": {
            "src/matching/semantic_similarity.py",
            "tests/test_phase120b_semantic_similarity_diagnostic.py",
        },
        "semantic_alignment_weighted_score_component": {
            "src/matching/scorer.py",
            "src/matching/semantic_similarity.py",
            "tests/test_phase121b_semantic_alignment_dimension_default_off.py",
        },
        "llm_adjudicator_readback_default_off": {
            "src/agents/llm_adjudicator_readback.py",
            "batch_select_best_resume_variant.py",
            "tests/test_phase123b_llm_adjudicator_readback_default_off.py",
        },
        "llm_adjudicator_planning_readback_static_only": {
            "src/app/static/planning.js",
            "tests/test_phase124b_llm_adjudicator_planning_readback_static_only.py",
            "tests/test_phase85b_legacy_guard_registry_default_off.py",
        },
        "hybrid_scoring_readiness_docs_wrap": {
            "README.md",
            "docs/architecture_summary.md",
            "docs/agentic_platform.md",
            "docs/full_fledged_agentic_ai_app_roadmap.md",
            "docs/portfolio_overview.md",
            "docs/demo_walkthrough.md",
            "docs/portfolio_demo_readiness_wrap_checkpoint.md",
            "tests/test_portfolio_demo_readiness_wrap_checkpoint.py",
            "tests/test_phase125b_hybrid_scoring_readiness_docs.py",
            "tests/support/phase_guard_registry.py",
            "tests/test_phase85b_legacy_guard_registry_default_off.py",
            "tests/test_phase33a_controlled_agent_router_readonly.py",
            "tests/test_phase33b_controlled_agent_router_workflow_state_adapter_readonly.py",
            "tests/test_phase33c_controlled_agent_router_batch_handoff_plan_readonly.py",
            "tests/test_phase33d_controlled_agent_router_planning_artifact_mapper_readonly.py",
            "tests/test_phase45a_controlled_exact_resume_change_set_provider_response_validation_default_off.py",
            "tests/test_phase45b_controlled_exact_resume_change_set_provider_response_validation_dry_run_command_default_off.py",
            "tests/test_phase46a_controlled_exact_resume_change_set_provider_response_normalization_default_off.py",
            "tests/test_phase48a_controlled_exact_resume_change_set_manual_review_readback_adapter_default_off.py",
            "tests/test_phase49a_controlled_exact_resume_change_set_real_provider_runtime_adapter_default_off.py",
            "tests/test_phase49b_controlled_exact_resume_change_set_real_provider_runtime_adapter_dry_run_command_default_off.py",
        },
        "planning_ai_review_copy_polish_static_only": {
            "src/app/static/planning.js",
            "docs/demo_walkthrough.md",
            "tests/test_phase124b_llm_adjudicator_planning_readback_static_only.py",
            "tests/test_phase126b_planning_ai_review_copy_polish_static_only.py",
            "tests/support/phase_guard_registry.py",
            "tests/test_phase85b_legacy_guard_registry_default_off.py",
        },
        "portfolio_demo_freeze_checkpoint": {
            "docs/demo_walkthrough.md",
            "docs/portfolio_demo_readiness_wrap_checkpoint.md",
            "tests/test_portfolio_demo_readiness_wrap_checkpoint.py",
            "tests/test_phase127b_portfolio_demo_freeze_checkpoint.py",
            "tests/support/phase_guard_registry.py",
            "tests/test_phase85b_legacy_guard_registry_default_off.py",
        },
        "policy_driven_llm_adjudicator_readback": {
            "src/agents/llm_adjudicator_readback.py",
            "batch_select_best_resume_variant.py",
            "tests/test_phase123b_llm_adjudicator_readback_default_off.py",
            "tests/test_phase128b_policy_driven_llm_adjudicator_readback.py",
            "tests/support/phase_guard_registry.py",
            "tests/test_phase85b_legacy_guard_registry_default_off.py",
        },
        "phase129b_auth_loader_ui": {
            "src/app/auth_ui.py",
            "src/app/static/media/auth_workflow_hero.svg",
            "src/app/static/media/auth_hero_icons/LICENSES.txt",
            "src/app/static/media/auth_hero_icons/apply_with_confidence.svg",
            "src/app/static/media/auth_hero_icons/collect_jobs.svg",
            "src/app/static/media/auth_hero_icons/review_ai_notes.svg",
            "src/app/static/media/auth_hero_icons/score_fit.svg",
            "src/app/static/media/auth_hero_icons/tailor_safely.svg",
            "src/app/ui.py",
            "src/app/planning_ui.py",
            "src/app/static/app.js",
            "src/app/static/planning.js",
            "src/app/static/app_redesign.css",
            "src/app/static/styles.css",
            "src/app/static/media/Login_page_BG_img.jpg",
            "src/app/static/media/Login_page_BG_img.LICENSE.txt",
            "tests/test_phase109b_live_pipeline_popup_ux_static_only.py",
            "tests/test_phase110b_generate_suggestions_loader_static_only.py",
            "tests/test_phase127b_portfolio_demo_freeze_checkpoint.py",
            "tests/test_phase129b_auth_and_loader_overlay_static_only.py",
            "tests/support/phase_guard_registry.py",
            "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
            "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
            "tests/test_phase104b_critic_controlled_llm_ownership_default_off.py",
            "tests/test_phase105b_critic_controlled_llm_manual_runtime_wiring_default_off.py",
        },
        "phase129c_workflow_overlay_and_run_scoped_corpus": {
            "src/app/auth_ui.py",
            "src/app/static/media/auth_workflow_hero.svg",
            "src/app/static/media/auth_hero_icons/LICENSES.txt",
            "src/app/static/media/auth_hero_icons/apply_with_confidence.svg",
            "src/app/static/media/auth_hero_icons/collect_jobs.svg",
            "src/app/static/media/auth_hero_icons/review_ai_notes.svg",
            "src/app/static/media/auth_hero_icons/score_fit.svg",
            "src/app/static/media/auth_hero_icons/tailor_safely.svg",
            "src/app/ui.py",
            "src/app/planning_ui.py",
            "src/app/static/app.js",
            "src/app/static/planning.js",
            "src/app/static/app_redesign.css",
            "src/app/static/styles.css",
            "src/app/api.py",
            "src/app/services.py",
            "src/pipeline/collector.py",
            "src/app/static/media/Login_page_BG_img.jpg",
            "src/app/static/media/Login_page_BG_img.LICENSE.txt",
            "tests/test_phase109b_live_pipeline_popup_ux_static_only.py",
            "tests/test_phase110b_generate_suggestions_loader_static_only.py",
            "tests/test_phase127b_portfolio_demo_freeze_checkpoint.py",
            "tests/test_phase129b_auth_and_loader_overlay_static_only.py",
            "tests/test_phase129c_workflow_overlay_and_run_scoped_corpus.py",
            "tests/test_phase129d_pipeline_persistence_and_suggestions_error_layout.py",
            "tests/test_phase129e_zero_job_and_compact_workflow_overlay.py",
            "tests/test_phase129f_zero_result_pipeline_empty_state.py",
            "tests/test_onboarding_api.py",
            "tests/test_queue_ui_metadata_contract.py",
            "tests/support/phase_guard_registry.py",
            "tests/test_phase85b_legacy_guard_registry_default_off.py",
            "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
            "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
            "tests/test_phase104b_critic_controlled_llm_ownership_default_off.py",
            "tests/test_phase105b_critic_controlled_llm_manual_runtime_wiring_default_off.py",
            "tests/test_agentic_review_ui_compaction_polish_no_backend_change.py",
            "tests/test_agentic_review_ui_portfolio_polish_no_backend_change.py",
            "tests/test_critic_provider_shadow_default_off.py",
            "tests/test_jd_intelligence_provider_shadow_default_off.py",
            "tests/test_jd_live_provider_canary_api_readback_default_off.py",
            "tests/test_jd_live_provider_canary_command_default_off.py",
            "tests/test_jd_live_provider_canary_default_off.py",
            "tests/test_jd_live_provider_canary_readback_default_off.py",
            "tests/test_jd_live_provider_canary_readiness_checkpoint_default_off.py",
            "tests/test_jd_live_provider_canary_runbook_default_off.py",
            "tests/test_jd_live_provider_canary_service_readback_default_off.py",
            "tests/test_jd_live_provider_canary_shadow_bridge_default_off.py",
            "tests/test_jd_live_provider_canary_ui_readback_default_off.py",
            "tests/test_jd_live_provider_external_adapter_default_off.py",
            "tests/test_jd_manual_live_canary_readiness_checkpoint_default_off.py",
            "tests/test_jd_provider_runtime_activation_default_off.py",
            "tests/test_jd_provider_runtime_readiness_checkpoint_default_off.py",
            "tests/test_jd_provider_runtime_review_packet_default_off.py",
            "tests/test_jd_provider_runtime_service_readback_default_off.py",
            "tests/test_jd_provider_runtime_shadow_bridge_default_off.py",
            "tests/test_jd_provider_runtime_trace_readback_default_off.py",
            "tests/test_jd_provider_runtime_ui_readback_default_off.py",
            "tests/test_pgvector_connection_provider_default_off.py",
            "tests/test_pgvector_extension_probe_contract_no_schema.py",
            "tests/test_pgvector_extension_probe_ui_no_schema_readonly.py",
            "tests/test_pgvector_local_smoke_default_off.py",
            "tests/test_pgvector_real_local_smoke_command_default_off.py",
            "tests/test_pgvector_schema_store_adapter_default_off.py",
            "tests/test_pgvector_smoke_readback_verification_default_off.py",
            "tests/test_pgvector_store_db_executor_default_off.py",
            "tests/test_phase106b_agentic_review_evidence_chain_ui_readback_default_off.py",
            "tests/test_phase18_approval_preview_readonly_default_off.py",
            "tests/test_phase18_human_approval_gate_contract_default_off.py",
            "tests/test_phase18_live_provider_activation_plan_default_off.py",
            "tests/test_phase18_live_provider_dry_run_packet_contract_default_off.py",
            "tests/test_phase18_live_readiness_approval_boundary_default_off.py",
            "tests/test_phase18_mutation_boundary_readiness_contract_default_off.py",
            "tests/test_phase18_operator_decision_capture_contract_default_off.py",
            "tests/test_phase18_provider_call_boundary_readiness_contract_default_off.py",
            "tests/test_phase18_provider_readback_audit_contract_default_off.py",
            "tests/test_phase18_provider_response_validation_contract_default_off.py",
            "tests/test_phase18_provider_runtime_adapter_contract_default_off.py",
            "tests/test_phase18_safety_wrap_release_checkpoint_default_off.py",
            "tests/test_phase19a_three_core_approval_preview_runtime_readonly_default_off.py",
            "tests/test_phase19b_three_core_approval_preview_service_readback_default_off.py",
            "tests/test_phase19c_three_core_approval_preview_api_readback_default_off.py",
            "tests/test_phase19d_three_core_approval_preview_ui_readback_default_off.py",
            "tests/test_phase19e_three_core_approval_preview_ui_api_fetch_default_off.py",
            "tests/test_phase19f_approval_preview_operator_decision_preview_default_off.py",
            "tests/test_phase19g_operator_decision_capture_readback_contract_default_off.py",
            "tests/test_phase19h_operator_decision_capture_api_readback_default_off.py",
            "tests/test_phase19i_operator_decision_capture_ui_readback_default_off.py",
            "tests/test_phase19j_readonly_approval_workflow_release_checkpoint_default_off.py",
            "tests/test_phase20a_provider_call_readiness_experiment_default_off.py",
            "tests/test_phase20b_provider_call_readiness_api_readback_default_off.py",
            "tests/test_phase20c_provider_call_readiness_ui_readback_default_off.py",
            "tests/test_phase20e_provider_readiness_release_checkpoint_default_off.py",
            "tests/test_phase21b_manual_review_readiness_contract_default_off.py",
            "tests/test_phase21c_manual_review_readiness_api_readback_default_off.py",
            "tests/test_phase21d_manual_review_readiness_ui_readback_default_off.py",
            "tests/test_phase21e_manual_review_workflow_release_checkpoint_default_off.py",
            "tests/test_phase22a_manual_review_ux_hardening_default_off.py",
            "tests/test_phase22b_core_agent_automation_mutation_inventory_default_off.py",
            "tests/test_phase22c_core_agent_evidence_materialization_preview_default_off.py",
            "tests/test_phase22d_core_agent_evidence_materialization_api_readback_default_off.py",
            "tests/test_phase22e_core_agent_evidence_materialization_ui_readback_default_off.py",
            "tests/test_phase22f_core_agent_evidence_materialization_release_checkpoint_default_off.py",
            "tests/test_phase23a_tailoring_agent_opportunity_contract_default_off.py",
            "tests/test_phase23b_tailoring_agent_opportunity_api_readback_default_off.py",
            "tests/test_phase23c_tailoring_agent_opportunity_ui_readback_default_off.py",
            "tests/test_phase23d_generate_ai_tailoring_action_boundary_contract_default_off.py",
            "tests/test_phase23e_generate_ai_tailoring_action_boundary_api_readback_default_off.py",
            "tests/test_phase23f_generate_ai_tailoring_action_boundary_ui_readback_default_off.py",
            "tests/test_phase23g_tailoring_agent_workflow_release_checkpoint_default_off.py",
            "tests/test_phase24a_manual_generate_ai_tailoring_preview_contract_default_off.py",
            "tests/test_phase24b_manual_generate_ai_tailoring_preview_api_readback_default_off.py",
            "tests/test_phase24c_manual_generate_ai_tailoring_preview_ui_readback_default_off.py",
            "tests/test_phase24d_manual_generate_ai_tailoring_preview_release_checkpoint_default_off.py",
            "tests/test_phase25a_manual_generate_ai_tailoring_preview_request_packet_contract_default_off.py",
            "tests/test_phase25b_manual_generate_ai_tailoring_preview_request_packet_api_readback_default_off.py",
            "tests/test_phase25c_manual_generate_ai_tailoring_preview_request_packet_ui_readback_default_off.py",
            "tests/test_phase25d_manual_generate_ai_tailoring_preview_request_packet_release_checkpoint_default_off.py",
            "tests/test_phase26a_manual_generate_ai_tailoring_preview_dispatch_boundary_contract_default_off.py",
            "tests/test_phase26b_manual_generate_ai_tailoring_preview_dispatch_boundary_api_readback_default_off.py",
            "tests/test_phase26c_manual_generate_ai_tailoring_preview_dispatch_boundary_ui_readback_default_off.py",
            "tests/test_phase26d_manual_generate_ai_tailoring_preview_dispatch_boundary_release_checkpoint_default_off.py",
            "tests/test_phase27a_manual_generate_ai_tailoring_preview_provider_request_envelope_contract_default_off.py",
            "tests/test_phase27b_manual_generate_ai_tailoring_preview_provider_request_envelope_api_readback_default_off.py",
            "tests/test_phase27c_manual_generate_ai_tailoring_preview_provider_request_envelope_ui_readback_default_off.py",
            "tests/test_phase27d_manual_generate_ai_tailoring_preview_provider_request_envelope_release_checkpoint_default_off.py",
            "tests/test_phase28a_manual_generate_ai_tailoring_preview_provider_call_boundary_contract_default_off.py",
            "tests/test_phase28b_manual_generate_ai_tailoring_preview_provider_call_boundary_api_readback_default_off.py",
            "tests/test_phase28c_manual_generate_ai_tailoring_preview_provider_call_boundary_ui_readback_default_off.py",
            "tests/test_phase28d_manual_generate_ai_tailoring_preview_provider_call_boundary_release_checkpoint_default_off.py",
            "tests/test_phase29a_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_contract_default_off.py",
            "tests/test_phase29b_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_api_readback_default_off.py",
            "tests/test_phase29c_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_ui_readback_default_off.py",
            "tests/test_phase29d_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_release_checkpoint_default_off.py",
            "tests/test_phase30a_manual_generate_ai_tailoring_preview_provider_response_validation_contract_default_off.py",
            "tests/test_phase30b_manual_generate_ai_tailoring_preview_provider_response_validation_api_readback_default_off.py",
            "tests/test_phase30c_manual_generate_ai_tailoring_preview_provider_response_validation_ui_readback_default_off.py",
            "tests/test_phase30d_manual_generate_ai_tailoring_preview_provider_response_validation_release_checkpoint_default_off.py",
            "tests/test_phase31a_manual_generate_ai_tailoring_preview_provider_response_normalization_contract_default_off.py",
            "tests/test_phase31b_manual_generate_ai_tailoring_preview_provider_response_normalization_api_readback_default_off.py",
            "tests/test_phase31c_manual_generate_ai_tailoring_preview_provider_response_normalization_ui_readback_default_off.py",
            "tests/test_phase31d_manual_generate_ai_tailoring_preview_provider_response_normalization_release_checkpoint_default_off.py",
            "tests/test_phase32a_manual_generate_ai_tailoring_preview_normalized_response_preview_packet_contract_default_off.py",
            "tests/test_phase32b_manual_generate_ai_tailoring_preview_normalized_response_preview_packet_api_readback_default_off.py",
            "tests/test_phase33a_controlled_agent_router_readonly.py",
            "tests/test_phase33b_controlled_agent_router_workflow_state_adapter_readonly.py",
            "tests/test_phase33c_controlled_agent_router_batch_handoff_plan_readonly.py",
            "tests/test_phase33d_controlled_agent_router_planning_artifact_mapper_readonly.py",
            "tests/test_phase33e_controlled_agent_router_planning_artifact_dry_run_command_readonly.py",
            "tests/test_phase34a_jd_intelligence_llm_signal_extractor_default_off.py",
            "tests/test_phase34b_jd_intelligence_planning_artifact_enricher_default_off.py",
            "tests/test_phase34c_jd_intelligence_planning_artifact_enrichment_dry_run_command_default_off.py",
            "tests/test_phase35a_jd_signal_resume_evidence_matrix_default_off.py",
            "tests/test_phase35b_jd_signal_planning_artifact_evidence_enricher_default_off.py",
            "tests/test_phase35c_jd_signal_planning_artifact_evidence_enrichment_dry_run_command_default_off.py",
            "tests/test_phase36a_jd_evidence_final_scoring_feature_adapter_default_off.py",
            "tests/test_phase36b_jd_evidence_final_scoring_feature_adapter_dry_run_command_default_off.py",
            "tests/test_phase37a_jd_evidence_scoring_contribution_preview_default_off.py",
            "tests/test_phase37b_jd_evidence_scoring_contribution_preview_dry_run_command_default_off.py",
            "tests/test_phase38a_jd_evidence_score_impact_preview_default_off.py",
            "tests/test_phase38b_jd_evidence_score_impact_preview_dry_run_command_default_off.py",
            "tests/test_phase39a_jd_evidence_score_impact_planning_artifact_annotator_default_off.py",
            "tests/test_phase39b_jd_evidence_score_impact_planning_artifact_annotator_dry_run_command_default_off.py",
            "tests/test_phase40a_jd_evidence_score_impact_review_packet_builder_default_off.py",
            "tests/test_phase40b_jd_evidence_score_impact_review_packet_builder_dry_run_command_default_off.py",
            "tests/test_phase41a_jd_evidence_score_impact_review_queue_builder_default_off.py",
            "tests/test_phase41b_jd_evidence_score_impact_review_queue_builder_dry_run_command_default_off.py",
            "tests/test_phase45a_controlled_exact_resume_change_set_provider_response_validation_default_off.py",
            "tests/test_phase45b_controlled_exact_resume_change_set_provider_response_validation_dry_run_command_default_off.py",
            "tests/test_phase46a_controlled_exact_resume_change_set_provider_response_normalization_default_off.py",
            "tests/test_phase48a_controlled_exact_resume_change_set_manual_review_readback_adapter_default_off.py",
            "tests/test_phase49a_controlled_exact_resume_change_set_real_provider_runtime_adapter_default_off.py",
            "tests/test_phase49b_controlled_exact_resume_change_set_real_provider_runtime_adapter_dry_run_command_default_off.py",
            "tests/test_phase70a_ux_polish_agentic_workflow_demo_readiness_default_off.py",
            "tests/test_phase70b_ux_polish_agentic_workflow_demo_readiness_readback_default_off.py",
            "tests/test_pipeline_embedding_retrieval_hook_default_off.py",
            "tests/test_pipeline_runtime_embedding_bridge_default_off.py",
            "tests/test_pipeline_vector_evidence_hook_default_off.py",
            "tests/test_portfolio_demo_readiness_wrap_checkpoint.py",
            "tests/test_provider_live_activation_safety_plan_default_off.py",
            "tests/test_provider_live_config_gate_default_off.py",
            "tests/test_provider_runtime_ui_readback_default_off.py",
            "tests/test_semantic_evidence_quality_gate_default_off.py",
            "tests/test_shadow_agent_vector_evidence_input_default_off.py",
            "tests/test_shadow_semantic_evidence_agent_input_default_off.py",
            "tests/test_shadow_vector_evidence_context_default_off.py",
            "tests/test_tailoring_provider_shadow_default_off.py",
            "tests/test_three_agent_llmops_aggregate_default_off.py",
            "tests/test_three_agent_llmops_observability_readback_default_off.py",
            "tests/test_three_agent_llmops_observability_service_bridge_default_off.py",
            "tests/test_three_agent_llmops_observability_ui_default_off.py",
            "tests/test_three_agent_llmops_trace_contract_default_off.py",
            "tests/test_three_agent_provider_handoff_default_off.py",
            "tests/test_three_agent_shadow_workflow_default_off.py",
            "tests/test_three_agent_workflow_readiness_default_off.py",
            "tests/test_three_core_agent_shadow_sidecar_bridge_default_off.py",
            "tests/test_vector_evidence_embedding_indexing_helper_default_off.py",
            "tests/test_vector_evidence_embedding_provider_contract_default_off.py",
            "tests/test_vector_evidence_embedding_retrieval_helper_default_off.py",
            "tests/test_vector_evidence_embedding_runtime_adapter_default_off.py",
            "tests/test_vector_evidence_embedding_runtime_service_bridge_default_off.py",
            "tests/test_vector_evidence_readback_service_helper_default_off.py",
            "tests/test_vector_evidence_readback_ui_default_off.py",
            "tests/test_vector_evidence_service_connection_provider_bridge_default_off.py",
            "tests/test_vector_evidence_service_db_executor_bridge_default_off.py",
            "tests/test_vector_evidence_service_pgvector_store_flagged_default_off.py",
            "tests/test_vector_evidence_ui_no_db_readonly.py",
        },
        "phase132b_premium_preferences_ui": {
            "src/app/api.py",
            "src/app/onboarding_ui.py",
            "src/app/profile_ui.py",
            "src/app/services.py",
            "src/app/static/app_redesign.css",
            "src/app/static/onboarding.js",
            "src/app/static/preferences.css",
            "src/app/static/preference_location_selector.js",
            "src/app/static/preferences_workflow.js",
            "src/app/static/profile.js",
            "src/app/static/styles.css",
            "src/app/ui_shell.py",
            "src/pipeline/location_preferences.py",
            "tests/support/phase_guard_registry.py",
            "tests/test_location_preference_search_api.py",
            "tests/test_onboarding_ui_contract.py",
            "tests/test_phase132b2r3_guided_preferences_workflow.py",
            "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
            "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
            "tests/test_phase85b_legacy_guard_registry_default_off.py",
            "tests/test_queue_ui_metadata_contract.py",
            "tests/test_role_expansion_ui_contract.py",
        },
        "phase133a_executive_kpi_react_island": {
            ".gitignore",
            "Dockerfile",
            "README.md",
            "frontend/executive-kpi/package-lock.json",
            "frontend/executive-kpi/package.json",
            "frontend/executive-kpi/postcss.config.cjs",
            "frontend/executive-kpi/src/AnalyticsDashboard.test.tsx",
            "frontend/executive-kpi/src/AnalyticsDashboard.tsx",
            "frontend/executive-kpi/src/main.tsx",
            "frontend/executive-kpi/src/main.test.tsx",
            "frontend/executive-kpi/src/styles.css",
            "frontend/executive-kpi/src/test/setup.ts",
            "frontend/executive-kpi/tailwind.config.cjs",
            "frontend/executive-kpi/tsconfig.json",
            "frontend/executive-kpi/vite.config.ts",
            "src/app/static/app.js",
            "src/app/static/build/executive-kpi/executive-kpi.css",
            "src/app/static/build/executive-kpi/executive-kpi.js",
            "src/app/ui.py",
            "tests/support/phase_guard_registry.py",
            "tests/test_phase133a_executive_kpi_react_island.py",
            "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
            "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
            "tests/test_phase85b_legacy_guard_registry_default_off.py",
        },
        "phase133b_executive_queue_react_island": {
            "frontend/executive-kpi/package-lock.json",
            "frontend/executive-kpi/package.json",
            "frontend/executive-kpi/src/ExecutiveQueue.test.tsx",
            "frontend/executive-kpi/src/ExecutiveQueue.tsx",
            "frontend/executive-kpi/src/main.test.tsx",
            "frontend/executive-kpi/src/main.tsx",
            "frontend/executive-kpi/src/styles.css",
            "frontend/executive-kpi/src/test/setup.ts",
            "src/app/static/app.js",
            "src/app/static/build/executive-kpi/executive-kpi.css",
            "src/app/static/build/executive-kpi/executive-kpi.js",
            "src/app/ui.py",
            "tests/support/phase_guard_registry.py",
            "tests/test_phase133a_executive_kpi_react_island.py",
            "tests/test_phase133b_executive_queue_react_island.py",
            "tests/test_phase85b_legacy_guard_registry_default_off.py",
            "tests/test_queue_ui_metadata_contract.py",
        },
        "phase133d_pipeline_dashboard_react_island": {
            "frontend/executive-kpi/src/main.test.tsx",
            "frontend/executive-kpi/src/main.tsx",
            "frontend/executive-kpi/src/pipeline/PipelineDashboard.test.tsx",
            "frontend/executive-kpi/src/pipeline/PipelineDashboard.tsx",
            "frontend/executive-kpi/src/pipeline/pipelineModel.ts",
            "frontend/executive-kpi/src/styles.css",
            "src/app/static/app.js",
            "src/app/static/build/executive-kpi/executive-kpi.css",
            "src/app/static/build/executive-kpi/executive-kpi.js",
            "src/app/services.py",
            "src/app/ui.py",
            "src/app/ui_shell.py",
            "src/pipeline/runtime_status.py",
            "src/storage/rag_store.py",
            "tests/support/phase_guard_registry.py",
            "tests/test_phase129d_pipeline_persistence_and_suggestions_error_layout.py",
            "tests/test_phase133d_pipeline_dashboard_react_island.py",
            "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
            "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
            "tests/test_phase71a_live_pipeline_argument_list_too_long_guard_default_off.py",
            "tests/test_phase85b_legacy_guard_registry_default_off.py",
            "tests/test_user_pipeline_status_reconciliation.py",
        },
        "phase133g_premium_planning_dashboard": {
            "frontend/executive-kpi/src/ExecutiveQueue.test.tsx",
            "frontend/executive-kpi/src/ExecutiveQueue.tsx",
            "frontend/executive-kpi/src/PlanningWorklist.test.tsx",
            "frontend/executive-kpi/src/PlanningWorklist.tsx",
            "frontend/executive-kpi/src/filter/FilterSelect.test.tsx",
            "frontend/executive-kpi/src/filter/FilterSelect.tsx",
            "frontend/executive-kpi/src/main.test.tsx",
            "frontend/executive-kpi/src/main.tsx",
            "frontend/executive-kpi/src/styles.css",
            "frontend/executive-kpi/src/table/TablePrimitives.tsx",
            "src/app/api.py",
            "src/app/planning_ui.py",
            "src/app/services.py",
            "src/app/static/app.js",
            "src/app/static/build/executive-kpi/executive-kpi.css",
            "src/app/static/build/executive-kpi/executive-kpi.js",
            "src/app/static/planning.js",
            "src/app/static/planning_dashboard.css",
            "src/app/ui.py",
            "tests/support/phase_guard_registry.py",
            "tests/test_phase110b_generate_suggestions_loader_static_only.py",
            "tests/test_phase133b_executive_queue_react_island.py",
            "tests/test_phase133g_premium_planning_dashboard.py",
            "tests/test_phase124b_llm_adjudicator_planning_readback_static_only.py",
            "tests/test_phase126b_planning_ai_review_copy_polish_static_only.py",
            "tests/test_phase71a_tailoring_workspace_artifact_path_preload_repair_default_off.py",
            "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
            "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
            "tests/test_phase85b_legacy_guard_registry_default_off.py",
            "tests/test_queue_ui_metadata_contract.py",
        },
        "phase133ef_decisions_applications_dashboards": {
            "frontend/executive-kpi/src/OperationalBridges.test.ts",
            "frontend/executive-kpi/src/OperationalDashboards.test.tsx",
            "frontend/executive-kpi/src/OperationalDashboards.tsx",
            "frontend/executive-kpi/src/main.test.tsx",
            "frontend/executive-kpi/src/main.tsx",
            "frontend/executive-kpi/src/styles.css",
            "frontend/executive-kpi/src/table/TablePrimitives.tsx",
            "src/app/application_hub_ui.py",
            "src/app/api.py",
            "src/app/decisions_ui.py",
            "src/app/static/application_views.js",
            "src/app/static/build/executive-kpi/executive-kpi.css",
            "src/app/static/build/executive-kpi/executive-kpi.js",
            "src/app/static/decisions.js",
            "tests/support/phase_guard_registry.py",
            "tests/test_phase133ef_decisions_applications_dashboards.py",
            "tests/test_phase85b_legacy_guard_registry_default_off.py",
        },
        "phase133h_premium_responsive_sidebar": {
            "src/app/application_hub_ui.py",
            "src/app/applied_ui.py",
            "src/app/auth_ui.py",
            "src/app/decisions_ui.py",
            "src/app/intelligence_ui.py",
            "src/app/onboarding_ui.py",
            "src/app/planning_ui.py",
            "src/app/profile_ui.py",
            "src/app/saved_ui.py",
            "src/app/static/app_redesign.css",
            "src/app/static/shell.js",
            "src/app/ui.py",
            "src/app/ui_shell.py",
            "tests/support/phase_guard_registry.py",
            "tests/test_phase132b2r3_guided_preferences_workflow.py",
            "tests/test_phase133d_pipeline_dashboard_react_island.py",
            "tests/test_phase133h_shared_shell_navigation.py",
            "tests/test_queue_ui_metadata_contract.py",
            "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
            "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
        },
        "scheduler_admin_health_redesign": {
            "src/app/api.py",
            "src/app/application_hub_ui.py",
            "src/app/applied_ui.py",
            "src/app/auth_ui.py",
            "src/app/decisions_ui.py",
            "src/app/intelligence_ui.py",
            "src/app/onboarding_ui.py",
            "src/app/planning_ui.py",
            "src/app/profile_ui.py",
            "src/app/saved_ui.py",
            "src/app/static/app_redesign.css",
            "src/app/static/shell.js",
            "src/app/ui.py",
            "src/app/ui_shell.py",
            "tests/support/phase_guard_registry.py",
            "tests/test_phase132b2r3_guided_preferences_workflow.py",
            "tests/test_phase133h_shared_shell_navigation.py",
            "tests/test_queue_ui_metadata_contract.py",
            "tests/test_scheduler_admin_health_redesign.py",
            "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
            "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
            "tests/test_phase85b_legacy_guard_registry_default_off.py",

        },
        "scheduler_health_visual_correction": {
            "frontend/executive-kpi/src/main.tsx",
            "frontend/executive-kpi/src/scheduler/SchedulerHealthDashboard.tsx",
            "frontend/executive-kpi/src/scheduler/SchedulerHealthDashboard.test.tsx",
            "frontend/executive-kpi/src/scheduler/schedulerModel.ts",
            "frontend/executive-kpi/src/styles.css",
            "src/app/api.py",
            "src/app/static/app_redesign.css",
            "src/app/static/build/executive-kpi/executive-kpi.css",
            "src/app/static/build/executive-kpi/executive-kpi.js",
            "src/app/ui.py",
            "tests/support/phase_guard_registry.py",
            "tests/test_phase132b2r3_guided_preferences_workflow.py",
            "tests/test_phase133a_executive_kpi_react_island.py",
            "tests/test_phase133d_pipeline_dashboard_react_island.py",
            "tests/test_phase133ef_decisions_applications_dashboards.py",
            "tests/test_phase133g_premium_planning_dashboard.py",
            "tests/test_queue_ui_metadata_contract.py",
            "tests/test_scheduler_admin_health_redesign.py",
            "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
            "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
            "tests/test_phase85b_legacy_guard_registry_default_off.py",
        },
        "scheduler_health_final_visual_polish": {
            "frontend/executive-kpi/src/main.tsx",
            "frontend/executive-kpi/src/scheduler/SchedulerHealthDashboard.tsx",
            "frontend/executive-kpi/src/scheduler/SchedulerHealthDashboard.test.tsx",
            "frontend/executive-kpi/src/scheduler/schedulerModel.ts",
            "frontend/executive-kpi/src/styles.css",
            "src/app/api.py",
            "src/app/static/app_redesign.css",
            "src/app/static/build/executive-kpi/executive-kpi.css",
            "src/app/static/build/executive-kpi/executive-kpi.js",
            "src/app/ui.py",
            "tests/support/phase_guard_registry.py",
            "tests/test_phase132b2r3_guided_preferences_workflow.py",
            "tests/test_phase133a_executive_kpi_react_island.py",
            "tests/test_phase133d_pipeline_dashboard_react_island.py",
            "tests/test_phase133ef_decisions_applications_dashboards.py",
            "tests/test_phase133g_premium_planning_dashboard.py",
            "tests/test_queue_ui_metadata_contract.py",
            "tests/test_scheduler_admin_health_redesign.py",
            "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
            "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
            "tests/test_phase85b_legacy_guard_registry_default_off.py",
        },
        "phase133i_advanced_diagnostics_react_command_center": {
            "frontend/executive-kpi/src/main.tsx",
            "frontend/executive-kpi/src/styles.css",
            "frontend/executive-kpi/src/diagnostics/AdvancedDiagnosticsDashboard.tsx",
            "frontend/executive-kpi/src/diagnostics/AdvancedDiagnosticsDashboard.test.tsx",
            "frontend/executive-kpi/src/filter/FilterSelect.tsx",
            "frontend/executive-kpi/src/filter/FilterSelect.test.tsx",
            "src/app/planning_ui.py",
            "src/app/static/app_redesign.css",
            "src/app/static/build/executive-kpi/executive-kpi.css",
            "src/app/static/build/executive-kpi/executive-kpi.js",
            "tests/support/phase_guard_registry.py",
            "tests/test_advanced_diagnostics_react_redesign.py",
            "tests/test_phase56a_live_tailoring_suggestion_planning_workspace_wiring_default_off.py",
            "tests/test_phase55b_live_jd_llm_extraction_planning_scan_readback_ui_api_default_off.py",
            "tests/test_phase68b_end_to_end_agentic_workflow_integration_readback_ui_api_default_off.py",
            "tests/test_phase69a_agentic_workflow_production_readiness_checkpoint_default_off.py",
            "tests/test_phase69b_agentic_workflow_production_readiness_readback_ui_api_default_off.py",
            "tests/test_phase70a_ux_polish_agentic_workflow_demo_readiness_default_off.py",
            "tests/test_phase70b_ux_polish_agentic_workflow_demo_readiness_readback_default_off.py",
            "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
            "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
            "tests/test_phase85b_legacy_guard_registry_default_off.py",
        },
        "item2_phase3_shared_page_header_foundation": {
            "frontend/executive-kpi/src/diagnostics/AdvancedDiagnosticsDashboard.tsx",
            "frontend/executive-kpi/src/diagnostics/AdvancedDiagnosticsDashboard.test.tsx",
            "frontend/executive-kpi/src/pipeline/PipelineDashboard.tsx",
            "frontend/executive-kpi/src/pipeline/PipelineDashboard.test.tsx",
            "frontend/executive-kpi/src/scheduler/SchedulerHealthDashboard.tsx",
            "frontend/executive-kpi/src/scheduler/SchedulerHealthDashboard.test.tsx",
            "frontend/executive-kpi/src/styles.css",
            "src/app/ui.py",
            "src/app/planning_ui.py",
            "src/app/decisions_ui.py",
            "src/app/application_hub_ui.py",
            "src/app/static/app_redesign.css",
            "src/app/static/build/executive-kpi/executive-kpi.css",
            "src/app/static/build/executive-kpi/executive-kpi.js",
            "tests/support/phase_guard_registry.py",
            "tests/test_item2_phase3_shared_page_header_foundation.py",
            "tests/test_scheduler_admin_health_redesign.py",
            "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
            "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
            "tests/test_phase85b_legacy_guard_registry_default_off.py",
        },
        "item2_phase4_secondary_page_headers": {
            "src/app/profile_ui.py",
            "src/app/intelligence_ui.py",
            "src/app/applied_ui.py",
            "src/app/saved_ui.py",
            "src/app/planning_ui.py",
            "src/app/static/app_redesign.css",
            "src/app/ui.py",
            "src/app/decisions_ui.py",
            "src/app/application_hub_ui.py",
            "tests/support/phase_guard_registry.py",
            "tests/test_item2_phase3_shared_page_header_foundation.py",
            "tests/test_item2_phase4_secondary_page_headers.py",
            "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
            "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
            "tests/test_phase85b_legacy_guard_registry_default_off.py",
        },
        "item2_phase4_profile_corrections_legacy_route_retirement": {
            "README.md",
            "frontend/executive-kpi/src/diagnostics/AdvancedDiagnosticsDashboard.tsx",
            "frontend/executive-kpi/src/diagnostics/AdvancedDiagnosticsDashboard.test.tsx",
            "frontend/executive-kpi/src/pipeline/PipelineDashboard.tsx",
            "frontend/executive-kpi/src/pipeline/PipelineDashboard.test.tsx",
            "frontend/executive-kpi/src/scheduler/SchedulerHealthDashboard.tsx",
            "frontend/executive-kpi/src/scheduler/SchedulerHealthDashboard.test.tsx",
            "frontend/executive-kpi/src/styles.css",
            "src/app/api.py",
            "src/app/application_hub_ui.py",
            "src/app/applied_ui.py",
            "src/app/decisions_ui.py",
            "src/app/intelligence_ui.py",
            "src/app/planning_ui.py",
            "src/app/profile_ui.py",
            "src/app/saved_ui.py",
            "src/app/static/app_redesign.css",
            "src/app/static/build/executive-kpi/executive-kpi.css",
            "src/app/static/build/executive-kpi/executive-kpi.js",
            "src/app/static/intelligence.js",
            "src/app/static/profile.js",
            "src/app/ui.py",
            "src/app/ui_shell.py",
            "src/auth/runtime.py",
            "tests/support/phase_guard_registry.py",
            "tests/test_item2_phase3_shared_page_header_foundation.py",
            "tests/test_item2_phase4_secondary_page_headers.py",
            "tests/test_item2_phase4_profile_corrections_and_legacy_route_retirement.py",
            "tests/test_phase133a_executive_kpi_react_island.py",
            "tests/test_phase133d_pipeline_dashboard_react_island.py",
            "tests/test_phase133ef_decisions_applications_dashboards.py",
            "tests/test_phase133g_premium_planning_dashboard.py",
            "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
            "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
            "tests/test_phase85b_legacy_guard_registry_default_off.py",
            "tests/test_scheduler_admin_health_redesign.py",
        },
        "phase8_step3d_tailoring_llm_gate": {
            "src/tailoring/rendering.py",
            "tests/test_tailoring_patch_refinement_explicit_opt_in.py",
        },
        "phase8_step4_dead_file_cleanup": {
            "src/ai/deterministic_skill_extractor.py",
        },
        "phase8_step6_canonical_agent_registry": {
            "src/agents/canonical_registry.py",
            "src/agents/workflow_registry.py",
            "tests/test_phase8_step6_canonical_agent_registry.py",
        },
        "phase8_step8_legacy_agent_context_retirement": {
            "src/agents/context.py",
            "tests/test_agent_context.py",
            "tests/test_full_agentic_ai_current_state_audit_no_runtime_change.py",
            "docs/full_agentic_ai_current_state_audit_no_runtime_change.md",
        },
        "phase8_step13_langgraph_parity_contract": {
            "tests/test_phase107b_langgraph_evidence_chain_harness_default_off.py",
        },
        "phase8_step14_typed_langgraph_state_normalization": {
            "src/agents/evidence_chain_langgraph_harness.py",
            "tests/test_phase107b_langgraph_evidence_chain_harness_default_off.py",
        },
        "phase8_step15_checkpoint_identity_serialization_contract": {
            "src/agents/evidence_chain_langgraph_harness.py",
            "tests/test_phase107b_langgraph_evidence_chain_harness_default_off.py",
        },
        "phase8_step17_readonly_operator_review_interrupt_request": {
            "src/agents/evidence_chain_langgraph_harness.py",
            "tests/test_phase107b_langgraph_evidence_chain_harness_default_off.py",
        },
        "phase9_step2_durable_checkpoint_interrupt_storage": {
            "src/storage/durable_orchestration/__init__.py",
            "src/storage/durable_orchestration/schema.sql",
            "src/storage/durable_orchestration/store.py",
            "tests/test_phase9_step2_durable_checkpoint_interrupt_storage_contract.py",
            "tests/test_pgvector_extension_probe_api_no_schema_no_ui.py",
            "tests/test_pgvector_extension_probe_contract_no_schema.py",
            "tests/test_pgvector_extension_probe_service_helper_no_schema.py",
            "tests/test_pgvector_extension_probe_ui_no_schema_readonly.py",
            "tests/test_phase8_pgvector_backend_readiness_schema_plan_no_runtime_change.py",
        },
        "phase9_step3_human_decision_resume_storage": {
            "src/storage/durable_orchestration/schema.sql",
            "src/storage/durable_orchestration/store.py",
            "tests/test_phase9_step2_durable_checkpoint_interrupt_storage_contract.py",
            "tests/test_phase9_step3_human_decision_resume_storage_contract.py",
            "tests/test_pgvector_extension_probe_api_no_schema_no_ui.py",
            "tests/test_pgvector_extension_probe_contract_no_schema.py",
            "tests/test_pgvector_extension_probe_service_helper_no_schema.py",
            "tests/test_pgvector_extension_probe_ui_no_schema_readonly.py",
            "tests/test_phase8_pgvector_backend_readiness_schema_plan_no_runtime_change.py",
        },
        "phase9_step4_attempt_terminal_recovery_storage": {
            "src/storage/durable_orchestration/schema.sql",
            "src/storage/durable_orchestration/store.py",
            "tests/test_phase9_step2_durable_checkpoint_interrupt_storage_contract.py",
            "tests/test_phase9_step3_human_decision_resume_storage_contract.py",
            "tests/test_phase9_step4_attempt_terminal_recovery_storage_contract.py",
            "tests/test_pgvector_extension_probe_api_no_schema_no_ui.py",
            "tests/test_pgvector_extension_probe_contract_no_schema.py",
            "tests/test_pgvector_extension_probe_service_helper_no_schema.py",
            "tests/test_pgvector_extension_probe_ui_no_schema_readonly.py",
            "tests/test_phase8_pgvector_backend_readiness_schema_plan_no_runtime_change.py",
        },
        "phase9_step6_inmemory_operator_review_pause_resume": {
            "src/agents/evidence_chain_langgraph_harness.py",
            "tests/test_phase107b_langgraph_evidence_chain_harness_default_off.py",
            "tests/test_phase9_step6_langgraph_operator_review_pause_resume_default_off.py",
        },
        "phase9_step8_durable_orchestration_transaction_executor": {
            "src/storage/durable_orchestration/repository.py",
            "tests/test_phase9_step8_durable_orchestration_transaction_executor_contract.py",
        },
    }
    try:
        return set(profiles[profile])
    except KeyError as exc:
        raise AssertionError(f"Unknown legacy guard allowlist profile: {profile}") from exc


def current_milestone_guard_compatibility_allowlist() -> set[str]:
    """Exact current milestone files accepted by stale registry-backed guards."""
    return (
        legacy_guard_allowlist("policy_driven_llm_adjudicator_readback")
        | legacy_guard_allowlist("phase129b_auth_loader_ui")
        | legacy_guard_allowlist("phase129c_workflow_overlay_and_run_scoped_corpus")
        | legacy_guard_allowlist("phase132b_premium_preferences_ui")
        | legacy_guard_allowlist("phase133a_executive_kpi_react_island")
        | legacy_guard_allowlist("phase133b_executive_queue_react_island")
        | legacy_guard_allowlist("phase133d_pipeline_dashboard_react_island")
        | legacy_guard_allowlist("phase133g_premium_planning_dashboard")
        | legacy_guard_allowlist("phase133ef_decisions_applications_dashboards")
        | legacy_guard_allowlist("phase133h_premium_responsive_sidebar")
        | legacy_guard_allowlist("scheduler_admin_health_redesign")
        | legacy_guard_allowlist("scheduler_health_visual_correction")
        | legacy_guard_allowlist("scheduler_health_final_visual_polish")
        | legacy_guard_allowlist("phase133i_advanced_diagnostics_react_command_center")
        | legacy_guard_allowlist("item2_phase3_shared_page_header_foundation")
        | legacy_guard_allowlist("item2_phase4_secondary_page_headers")
        | legacy_guard_allowlist("item2_phase4_profile_corrections_legacy_route_retirement")
        | legacy_guard_allowlist("phase8_step3d_tailoring_llm_gate")
        | legacy_guard_allowlist("phase8_step4_dead_file_cleanup")
        | legacy_guard_allowlist("phase8_step6_canonical_agent_registry")
        | legacy_guard_allowlist("phase8_step8_legacy_agent_context_retirement")
        | legacy_guard_allowlist("phase8_step13_langgraph_parity_contract")
        | legacy_guard_allowlist("phase8_step14_typed_langgraph_state_normalization")
        | legacy_guard_allowlist("phase8_step15_checkpoint_identity_serialization_contract")
        | legacy_guard_allowlist(
            "phase8_step17_readonly_operator_review_interrupt_request"
        )
        | legacy_guard_allowlist(
            "phase9_step2_durable_checkpoint_interrupt_storage"
        )
        | legacy_guard_allowlist(
            "phase9_step3_human_decision_resume_storage"
        )
        | legacy_guard_allowlist(
            "phase9_step4_attempt_terminal_recovery_storage"
        )
        | legacy_guard_allowlist(
            "phase9_step6_inmemory_operator_review_pause_resume"
        )
        | legacy_guard_allowlist(
            "phase9_step8_durable_orchestration_transaction_executor"
        )
    )


def assert_changed_files_allowed(
    changed: Iterable[str | Path],
    allowed: Iterable[str | Path],
    legacy_guard_profiles: Iterable[str] = (),
    include_current_milestone_compatibility: bool = True,
) -> None:
    normalized_changed = merge_allowed(changed)
    normalized_allowed = merge_allowed(allowed)
    for profile in legacy_guard_profiles:
        normalized_allowed |= legacy_guard_allowlist(profile)
    if include_current_milestone_compatibility:
        normalized_allowed |= current_milestone_guard_compatibility_allowlist()
    collapsed_directories = {
        path for path in normalized_changed if path.endswith("/")
    }
    if collapsed_directories:
        exact_changed = get_changed_files(Path.cwd())
        for directory in collapsed_directories:
            descendants = {
                path for path in exact_changed if path.startswith(directory)
            }
            if descendants and descendants <= normalized_allowed:
                normalized_changed.remove(directory)
                normalized_changed.update(descendants)
    reject_duplicate_artifact_paths(normalized_changed)
    extra = normalized_changed - normalized_allowed
    assert not extra, "Unexpected changed files: " + ", ".join(sorted(extra))


def assert_protected_hashes(
    root: str | Path,
    expected_hashes: Mapping[str | Path, str],
    compatibility_profiles: Iterable[str] = (),
) -> None:
    phase88b_runtime_hash_compatibility = {
        (
            "src/app/api.py",
            "d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004",
        ): "fc5487b793cf3e36018bb37863b426ec8f1134224f0e3bf20ad0aa2990b7a241",
        (
            "src/app/services.py",
            "bfa035faa8e89abd2b75095f68b45a282fb3b7fc8e5ff43e36c754db56ef12c2",
        ): "8fdd9eb765fef33d6855a2992c4a5e12aa48c97d055fd41b26076034833a98c6",
        (
            "src/app/static/app_redesign.css",
            "81eede647edd99ca1f8c0f5b759b35ecf40e223db9d9dbd4b976f487ecf49961",
        ): "e4c15f04c6c63a28cfa59784134a69cd3832d7f85169fea31add02a3e76d7828",
        (
            "src/app/api.py",
            "85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96",
        ): "cf11fdbb368ee350613dcae9647573201c26de0aaabf76b5436b71178e0b6f20",
        (
            "src/app/services.py",
            "e30180b352ebe8abca2ec34b4b34983fbaee61a32bdc0d511001c406703e392c",
        ): "8fdd9eb765fef33d6855a2992c4a5e12aa48c97d055fd41b26076034833a98c6",
            (
                "src/agents/jd_intelligence.py",
                "3711372610b48c5762b1bc27c9cdc8182a9a3d735e5f8bade222b9bac3ef4a00",
            ): "c72224bbc8e64b13c725f9180d227c413fb2fd9a65a97e2e72954f61a8f32b45",
            (
                "src/agents/jd_intelligence.py",
                "c0150f2717581647c22bd084e3223691c1ce25d9b573acff10369def28f37f02",
            ): "c72224bbc8e64b13c725f9180d227c413fb2fd9a65a97e2e72954f61a8f32b45",
        (
            "src/pipeline/collector.py",
            "71b2ca0b50320688c2ed10396dfbffe952e7ed326fc745955eb1fb8010850a50",
        ): "29b74e6807b7942b0f35c67b1ed724262a9a8ce1488b7df669faf456a5cfea3f",
        (
            "src/pipeline/collector.py",
            "a5afe9a9e89b1547d9fbaa443d6753f8bf223fe55e20d46beaff1afd03127344",
        ): "29b74e6807b7942b0f35c67b1ed724262a9a8ce1488b7df669faf456a5cfea3f",
        (
            "src/pipeline/collector.py",
            "29b74e6807b7942b0f35c67b1ed724262a9a8ce1488b7df669faf456a5cfea3f",
        ): "e5af36527801b2a1a55501622619d4e62ccaa7472e835500613e2894843d1671",
        (
            "src/pipeline/collector.py",
            "e5af36527801b2a1a55501622619d4e62ccaa7472e835500613e2894843d1671",
        ): "75bda61d0bdc4cf388586d141541be486a9e01b5062f5cc91fe6dc63c46546dc",
        (
            "src/app/static/agentic_review.js",
            "fdbd820a68a356d894ac0b904bd649d511dcf501129d32ed00d34ffc7f927fd0",
        ): "fdbd820a68a356d894ac0b904bd649d511dcf501129d32ed00d34ffc7f927fd0",
    }
    repo = Path(root)
    profiles = tuple(compatibility_profiles)
    compatible_paths = (
        merge_allowed(*(legacy_guard_allowlist(profile) for profile in profiles))
        if profiles
        else None
    )
    for relative_path, expected_hash in expected_hashes.items():
        normalized = normalize_changed_path(relative_path)
        path = repo / normalized
        assert path.exists(), f"Protected path does not exist: {normalized}"
        actual_hash = sha256(path.read_bytes()).hexdigest()
        compatible_hash = phase88b_runtime_hash_compatibility.get(
            (normalized, expected_hash)
        )
        if compatible_hash == actual_hash and (
            compatible_paths is None or normalized in compatible_paths
        ):
            continue
        assert actual_hash == expected_hash, (
            f"Hash mismatch for {normalized}: expected {expected_hash}, got {actual_hash}"
        )


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _call_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


def _normalize_call_marker(marker: str) -> str:
    value = marker.strip()
    if value.endswith("("):
        value = value[:-1]
    return value.strip()


def _call_matches(call_name: str, forbidden: str) -> bool:
    marker = _normalize_call_marker(forbidden)
    if not marker:
        return False
    if marker.startswith("."):
        return call_name.endswith(marker)
    return call_name == marker or call_name.endswith(f".{marker}")


def _imported_names(node: ast.AST) -> set[str]:
    if isinstance(node, ast.Import):
        return {alias.name for alias in node.names}
    if isinstance(node, ast.ImportFrom):
        module = node.module or ""
        names = {module} if module else set()
        names.update(f"{module}.{alias.name}" if module else alias.name for alias in node.names)
        return names
    return set()


def _import_matches(import_name: str, forbidden: str) -> bool:
    marker = forbidden.strip()
    return import_name == marker or import_name.startswith(f"{marker}.")


def assert_no_forbidden_runtime_calls_ast(
    paths: Iterable[str | Path],
    forbidden_calls: Iterable[str] = (),
    forbidden_imports: Iterable[str] = (),
) -> None:
    call_markers = tuple(forbidden_calls)
    import_markers = tuple(forbidden_imports)
    violations: list[str] = []

    for path_value in paths:
        path = Path(path_value)
        if path.suffix != ".py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                call_name = _call_name(node.func)
                for marker in call_markers:
                    if _call_matches(call_name, marker):
                        violations.append(f"{path}: forbidden call {call_name}")
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                for import_name in _imported_names(node):
                    for marker in import_markers:
                        if _import_matches(import_name, marker):
                            violations.append(f"{path}: forbidden import {import_name}")

    assert not violations, "Forbidden runtime calls/imports found: " + "; ".join(
        sorted(violations)
    )


def assert_false_safety_metadata_allowed_but_real_mutation_blocked(
    path: str | Path,
) -> None:
    """Allow false safety metadata while blocking real mutation/provider calls."""
    assert_no_forbidden_runtime_calls_ast(
        [path],
        forbidden_calls=(
            "auto_apply",
            "apply_automatically",
            "submit_application",
            "execute_application",
            "click_apply",
            "mark_as_applied",
            "send_recruiter_message",
            "run_chat_completion",
            "provider_call",
            "database_write",
            "persist_decision",
            "persist_audit",
        ),
        forbidden_imports=(
            "src.ai.llm_client",
            "src.agents.workflow_runner",
            "application_execution_queue",
        ),
    )
