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

PHASE11_STEP3_DIRECT_HASH_GUARD_FILES = {
    "tests/test_jd_provider_runtime_api_readback_default_off.py",
    "tests/test_pgvector_extension_probe_api_no_schema_no_ui.py",
    "tests/test_pgvector_extension_probe_service_helper_no_schema.py",
    "tests/test_phase8_pgvector_backend_readiness_schema_plan_no_runtime_change.py",
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
    "tests/test_phase69b_agentic_workflow_production_readiness_readback_ui_api_default_off.py",
    "tests/test_provider_runtime_activation_plan_default_off.py",
    "tests/test_provider_runtime_readiness_checkpoint_default_off.py",
    "tests/test_vector_evidence_readback_api_default_off.py",
}

PHASE11_STEP8L_PROVIDER_BENCHMARK_CONTRACT_FILES = {
    "src/evaluation/provider_benchmark_contract.py",
    "tests/fixtures/provider_benchmark/manifest.json",
    "tests/test_provider_benchmark_contract.py",
}

PHASE11_STEP8M_PROVIDER_CLIENT_COMPATIBILITY_FILES = {
    "src/evaluation/provider_client_compatibility.py",
    "tests/test_provider_client_compatibility.py",
}

PHASE11_STEP8N_SHARED_LLM_CLIENT_SAFETY_FILES = {
    "src/ai/llm_client.py",
    "tests/test_llm_client_safety.py",
}

PHASE11_STEP8O_PROVIDER_FIXTURE_BENCHMARK_FILES = {
    "src/evaluation/provider_fixture_benchmark.py",
    "tests/fixtures/provider_benchmark/cases.json",
    "tests/test_provider_fixture_benchmark.py",
}

PHASE11_STEP8P_CONTROLLED_PROVIDER_BENCHMARK_PLAN_FILES = {
    "src/evaluation/controlled_provider_benchmark_plan.py",
    "tests/fixtures/provider_benchmark/run_plan.json",
    "tests/test_controlled_provider_benchmark_plan.py",
}

PHASE11_STEP8PA_TRANSMISSION_SAFE_FIXTURE_FILES = {
    "tests/fixtures/provider_benchmark/cases.json",
    "tests/test_provider_fixture_benchmark.py",
    "tests/test_transmission_safe_provider_fixtures.py",
}

PHASE11_STEP8Q_CONTROLLED_PROVIDER_BENCHMARK_HARNESS_FILES = {
    "src/evaluation/controlled_provider_benchmark_harness.py",
    "tests/fixtures/provider_benchmark/synthetic_authorization.json",
    "tests/fixtures/provider_benchmark/synthetic_pricing.json",
    "tests/test_controlled_provider_benchmark_harness.py",
}

PHASE11_STEP8R_GROQ_LIVE_CANARY_PREPARATION_FILES = {
    "docs/controlled_groq_provider_canary_runbook.md",
    "src/evaluation/controlled_groq_provider_canary.py",
    "tests/fixtures/provider_benchmark/groq_canary_authorization_template.json",
    "tests/fixtures/provider_benchmark/groq_canary_pricing_template.json",
    "tests/test_controlled_groq_provider_canary.py",
}

PHASE11_STEP8T_REAL_GROQ_CANARY_TRANSPORT_FILES = {
    "src/evaluation/controlled_groq_canary_transport.py",
    "tests/test_controlled_groq_canary_transport.py",
}

PHASE11_STEP8V_GROQ_CANARY_EVIDENCE_RUNTIME_FILES = {
    "src/evaluation/controlled_groq_canary_evidence_runtime.py",
    "tests/test_controlled_groq_canary_evidence_runtime.py",
}

PHASE11_STEP8Y_GROQ_CANARY_RUN_IDENTITY_FILES = {
    "src/evaluation/controlled_groq_canary_run_identity.py",
    "tests/test_controlled_groq_canary_run_identity.py",
}

PHASE11_STEP8Z_GROQ_CANARY_RUN_EVIDENCE_RUNTIME_FILES = {
    "src/evaluation/controlled_groq_canary_run_evidence_runtime.py",
    "tests/test_controlled_groq_canary_run_evidence_runtime.py",
}

PHASE11_STEP8ZE_GROQ_CANARY_RUN_003_PLAN_FILES = {
    "src/evaluation/controlled_groq_canary_run_003_plan.py",
    "tests/test_controlled_groq_canary_run_003_plan.py",
}

PHASE11_STEP8ZF_GROQ_CANARY_RUN_003_IDENTITY_FILES = {
    "src/evaluation/controlled_groq_canary_run_003_identity.py",
    "tests/test_controlled_groq_canary_run_003_identity.py",
}

PHASE11_STEP8ZG_GROQ_CANARY_RUN_003_RUNTIME_FILES = {
    "src/evaluation/controlled_groq_canary_run_003_transport.py",
    "src/evaluation/controlled_groq_canary_run_003_evidence_runtime.py",
    "tests/test_controlled_groq_canary_run_003_transport.py",
    "tests/test_controlled_groq_canary_run_003_evidence_runtime.py",
}
PHASE11_STEP8ZK_GROQ_CANARY_RUN_004_OFFLINE_RUNTIME_FILES = {
    "src/evaluation/controlled_groq_canary_run_004_plan.py",
    "src/evaluation/controlled_groq_canary_run_004_identity.py",
    "src/evaluation/controlled_groq_canary_run_004_evidence_runtime.py",
    "tests/test_controlled_groq_canary_run_004_plan.py",
    "tests/test_controlled_groq_canary_run_004_identity.py",
    "tests/test_controlled_groq_canary_run_004_evidence_runtime.py",
}

PHASE11_STEP8ZN_GROQ_CANARY_RUN_005_DIAGNOSTIC_RUNTIME_FILES = {
    "src/evaluation/provider_fixture_benchmark.py",
    "tests/test_provider_fixture_benchmark.py",
    "src/evaluation/controlled_groq_canary_run_005_plan.py",
    "src/evaluation/controlled_groq_canary_run_005_identity.py",
    "src/evaluation/controlled_groq_canary_run_005_evidence_runtime.py",
    "tests/test_controlled_groq_canary_run_005_plan.py",
    "tests/test_controlled_groq_canary_run_005_identity.py",
    "tests/test_controlled_groq_canary_run_005_evidence_runtime.py",
    "tests/test_controlled_groq_canary_run_004_evidence_runtime.py",
}

PHASE11_STEP8ZQ_ADDITIVE_TAILORING_TRANSPORT_FILES = {
    "src/evaluation/controlled_tailoring_benchmark_request_adapter.py",
    "src/evaluation/controlled_groq_tailoring_canary_transport.py",
    "tests/test_controlled_tailoring_benchmark_request_adapter.py",
    "tests/test_controlled_groq_tailoring_canary_transport.py",
}

PHASE11_STEP8MA_RAG_TEST_ISOLATION_FILES = {
    "tests/test_rag_endpoint_behavior.py",
}

PHASE12D_DETERMINISTIC_PRODUCTION_OWNER_SHADOW_FILES = {
    "src/agents/production_shadow_artifact_adapter.py",
    "src/agents/production_shadow_graph.py",
    "src/agents/production_shadow_job_priority_owner.py",
    "src/agents/production_shadow_state.py",
    "tests/test_phase12b_artifact_only_production_shadow_foundation.py",
    "tests/test_phase12d_first_deterministic_production_owner.py",
}

PHASE13C_AUTHORITATIVE_JOB_PRIORITIZATION_NODE_FILES = {
    "application_execution_queue.py",
    "src/agents/job_prioritization_authoritative_graph.py",
    "tests/test_phase13c_first_authoritative_job_prioritization_node.py",
    "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
    "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
    "tests/test_phase8_pgvector_backend_readiness_schema_plan_no_runtime_change.py",
    "tests/support/phase_guard_registry.py",
    "tests/test_phase85b_legacy_guard_registry_default_off.py",
}

PHASE14B_AUTHORITATIVE_TAILORING_CALLER_FILES = {
    "application_execution_queue.py",
    "src/agents/tailoring_decision_agent.py",
    "tests/test_phase14b_authoritative_tailoring_caller_reconciliation.py",
    "tests/support/phase_guard_registry.py",
    "tests/test_phase85b_legacy_guard_registry_default_off.py",
}

PHASE14C_AUTHORITATIVE_TAILORING_NODE_FILES = {
    "application_execution_queue.py",
    "src/agents/tailoring_decision_authoritative_graph.py",
    "tests/test_phase14c_second_authoritative_tailoring_node.py",
    "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
    "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
    "tests/support/phase_guard_registry.py",
    "tests/test_phase85b_legacy_guard_registry_default_off.py",
}

PHASE15B_CONDITIONAL_OPERATOR_REVIEW_CALLER_FILES = {
    "application_execution_queue.py",
    "src/agents/operator_review_agent.py",
    "tests/test_phase15b_conditional_operator_review_caller_reconciliation.py",
    "tests/support/phase_guard_registry.py",
    "tests/test_phase85b_legacy_guard_registry_default_off.py",
}

PHASE15C_CONDITIONAL_OPERATOR_REVIEW_NODE_FILES = {
    "application_execution_queue.py",
    "src/agents/operator_review_authoritative_graph.py",
    "tests/test_phase15b_conditional_operator_review_caller_reconciliation.py",
    "tests/test_phase15c_conditional_authoritative_operator_review_node.py",
    "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
    "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
    "tests/support/phase_guard_registry.py",
    "tests/test_phase85b_legacy_guard_registry_default_off.py",
}

PHASE17C_TAILORING_GENERATION_LLM_CLOSURE_FILES = {
    "generate_tailoring_suggestions.py",
    "src/tailoring/llm.py",
    "src/pipeline/collector.py",
    "src/agents/tailoring_generation_authoritative_graph.py",
    "tests/test_phase17c_lean_tailoring_intelligence_llm_closure.py",
    "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
    "tests/support/phase_guard_registry.py",
} | PHASE11_STEP3_DIRECT_HASH_GUARD_FILES

PHASE21_RELEASE_CANDIDATE_FILES = {
    "README.md",
    "docs/architecture_summary.md",
    "docs/core_agent_automation_mutation_inventory.md",
    "docs/full_fledged_agentic_ai_app_roadmap.md",
    "docs/phase22_core_agent_automation_mutation_inventory.md",
    "src/agents/production_human_checkpoint_coordinator.py",
    "src/app/api.py",
    "src/app/services.py",
    "tests/support/phase_guard_registry.py",
    "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
    "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
    "tests/test_phase85b_legacy_guard_registry_default_off.py",
    "tests/test_phase21_authenticated_decision_action_release_candidate.py",
    "tests/test_phase21_release_candidate_documentation.py",
}

PHASE21H_PROVIDER_BENCHMARK_HERMETICITY_FILES = {
    "tests/fixtures/provider_benchmark/hermetic_groq_canary_pricing.json",
}

PHASE21R_HISTORICAL_GUARD_FILES = {
    "tests/test_controlled_groq_tailoring_canary_transport.py",
    "tests/test_critic_provider_shadow_default_off.py",
    "tests/test_item2_phase4_profile_corrections_and_legacy_route_retirement.py",
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
    "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
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
    "tests/test_phase69b_agentic_workflow_production_readiness_readback_ui_api_default_off.py",
    "tests/test_phase70a_ux_polish_agentic_workflow_demo_readiness_default_off.py",
    "tests/test_phase70b_ux_polish_agentic_workflow_demo_readiness_readback_default_off.py",
    "tests/test_phase8_pgvector_backend_readiness_schema_plan_no_runtime_change.py",
    "tests/test_provider_live_activation_safety_plan_default_off.py",
    "tests/test_provider_live_config_gate_default_off.py",
    "tests/test_provider_runtime_activation_plan_default_off.py",
    "tests/test_provider_runtime_api_readback_default_off.py",
    "tests/test_provider_runtime_readiness_checkpoint_default_off.py",
    "tests/test_provider_runtime_service_bridge_default_off.py",
    "tests/test_provider_runtime_ui_readback_default_off.py",
    "tests/test_shadow_semantic_evidence_agent_input_default_off.py",
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
    "tests/test_three_core_shadow_readiness_wrap_default_off.py",
    "tests/test_vector_evidence_api_no_db_no_ui.py",
    "tests/test_vector_evidence_embedding_indexing_helper_default_off.py",
    "tests/test_vector_evidence_embedding_provider_contract_default_off.py",
    "tests/test_vector_evidence_embedding_retrieval_helper_default_off.py",
    "tests/test_vector_evidence_embedding_runtime_adapter_default_off.py",
    "tests/test_vector_evidence_embedding_runtime_service_bridge_default_off.py",
    "tests/test_vector_evidence_readback_api_default_off.py",
    "tests/test_vector_evidence_readback_service_helper_default_off.py",
    "tests/test_vector_evidence_readback_ui_default_off.py",
    "tests/test_vector_evidence_service_connection_provider_bridge_default_off.py",
    "tests/test_vector_evidence_service_db_executor_bridge_default_off.py",
    "tests/test_vector_evidence_service_pgvector_store_flagged_default_off.py",
    "tests/test_vector_evidence_ui_no_db_readonly.py",
}

SCRAPER_TRANSPORT_PAGINATION_HARDENING_FILES = {
    "src/config/consts.py",
    "src/scrapers/builtin_scraper.py",
    "src/scrapers/greenhouse_scraper.py",
    "src/scrapers/lever_scraper.py",
    "src/scrapers/workable_scraper.py",
    "src/scrapers/workday_scraper.py",
    "src/utils/http_retry.py",
    "tests/support/phase_guard_registry.py",
    "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
    "tests/test_builtin_scraper.py",
    "tests/test_scraper_acquisition_outcomes.py",
    "tests/test_scraper_transport_pagination_hardening.py",
}

STEP1B2_GLOBAL_ACQUISITION_BOUNDARY_FILES = {
    "main.py",
    "src/pipeline/collector.py",
    "src/pipeline/scheduler.py",
    "src/rag/export_job_corpus.py",
    "tests/support/phase_guard_registry.py",
    "tests/test_rag_export_job_corpus.py",
    "tests/test_scheduler_runtime_postgres_correctness.py",
    "tests/test_user_pipeline_role_preferences.py",
}

STEP1B3_OWNER_PROJECTION_SHARED_POOL_FILES = {
    "main.py",
    "src/app/services.py",
    "src/pipeline/collector.py",
    "src/pipeline/runtime_status.py",
    "tests/support/phase_guard_registry.py",
    "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
    "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
    "tests/test_phase71a_live_pipeline_argument_list_too_long_guard_default_off.py",
    "tests/test_phase85b_legacy_guard_registry_default_off.py",
    "tests/test_user_pipeline_role_preferences.py",
}

STEP1B4_OWNER_SELECTOR_LLM_ROUTING_FILES = {
    "batch_select_best_resume_variant.py",
    "tests/support/phase_guard_registry.py",
    "tests/test_phase85b_legacy_guard_registry_default_off.py",
    "tests/test_step1b4_owner_selector_llm_routing.py",
}

ITEM2_MANUAL_PROVIDER_PREVIEW_JOB_IDENTITY_REPAIR_FILES = {
    "tests/test_item2c_manual_provider_preview_live_service_boundary.py",
}

ITEM2_MANUAL_PROVIDER_PREVIEW_PROMPT_SCHEMA_ALIGNMENT_FILES = {
    "src/agents/manual_provider_preview_production_task_contract.py",
    "src/evaluation/provider_model_recommendation_policy.py",
    "tests/test_item2d_manual_provider_preview_live_response_validation.py",
    "tests/test_phase1_step5_user_scoped_shared_transport.py",
    "src/evaluation/controlled_production_parity_benchmark.py",
    "tests/test_controlled_production_parity_benchmark.py",
    "tests/test_production_task_contract_fingerprints.py",
}

# Item 3 floating ApplyLens AI chatbot: Dashboard-scoped retrieval, evidence
# completeness, and the redesigned chatbot UI. Only the files that stale
# registry-backed scope guards actually flag are listed here; the remaining
# Item 3 files (src/app/services.py, src/app/ui_shell.py,
# src/app/static/app_redesign.css, src/storage/rag_store.py and the three
# updated legacy test files) are already accepted by earlier milestone
# allowlists, so re-listing them would widen the surface without need.
ITEM3_DASHBOARD_SCOPED_CHATBOT_FILES = {
    "src/app/static/floating_intelligence_chat.js",
    "src/rag/corpus_store.py",
    "src/rag/lexical_retriever.py",
    "src/rag/query_engine.py",
    "src/rag/rag_answerer.py",
    "src/rag/rag_executor.py",
    "src/rag/rag_tools.py",
    "src/rag/retrieval_ranker.py",
    "tests/test_item3e0_chatbot_capability_matrix.py",
    "tests/test_item3e2_dashboard_scoped_chatbot.py",
}

# Item 4 planning & tailoring options review: authenticated-owner patch
# selection/draft/preview scoping, planning-artifact owner-root path
# hardening, generate_llm_tailoring default-contract audit, and tailoring
# state-field contract coverage. Runtime files (src/app/api.py,
# src/app/services.py, src/app/planning_ui.py, src/app/static/planning.js)
# and the modified test_phase71a_tailoring_workspace_artifact_path_preload_
# repair_default_off.py file are already accepted by
# phase133g_premium_planning_dashboard; only the four new Item 4 test files
# are listed here.
ITEM4_PLANNING_TAILORING_OPTIONS_FILES = {
    "tests/test_item4bc_planning_owner_isolation.py",
    "tests/test_item4cr2_planning_artifact_owner_root.py",
    "tests/test_item4d_generate_llm_tailoring_contract.py",
    "tests/test_item4et_tailoring_state_contract.py",
}

# Item 6 Agentic Review UI revamp: exact final frontend and focused-test
# boundary accepted by stale registry-backed guards.
ITEM6_AGENTIC_REVIEW_UI_REVAMP_FILES = {
    "src/app/profile_ui.py",
    "src/app/static/agentic_review.css",
    "src/app/static/agentic_review.js",
    "tests/support/phase_guard_registry.py",
    "tests/test_agent_trace_readonly_ui_panel_no_api_no_writes.py",
    "tests/test_item2e_manual_provider_preview_ui.py",
    "tests/test_item6b2_consolidated_agentic_review_queue_foundation.py",
    "tests/test_item6b3_selected_job_review_inspector.py",
    "tests/test_item6b45_premium_visual_correction_density.py",
    "tests/test_item6b4_selected_job_evidence_agent_views.py",
    "tests/test_item6b5_contextual_actions_manual_preview_integration.py",
    "tests/test_item6b65a_review_advanced_shell_usability.py",
    "tests/test_item6b65b_agent_trace_master_detail_search_keyboard.py",
    "tests/test_item6b65c_extended_trace_diagnostics_master_detail.py",
    "tests/test_item6b6_final_review_vs_advanced_changeover.py",
    "tests/test_item6c1_extended_diagnostic_detail_layout_action_alignment.py",
    "tests/test_item6c2_final_placement_disclosure_header_alignment.py",
    "tests/test_item6c3_agentic_review_back_navigation_placement_visibility.py",
    "tests/test_item6c_final_agentic_review_visual_system_micro_ux.py",
}

# Item 6.1B Agentic Review admin boundary: exact production and focused-test
# surface accepted by historical registry-backed guards.
ITEM61B_AGENTIC_REVIEW_ADMIN_BOUNDARY_FILES = {
    "src/app/api.py",
    "src/app/profile_ui.py",
    "src/app/static/profile.js",
    "tests/test_item61b_agentic_review_admin_boundary.py",
    "tests/test_agent_trace_api.py",
    "tests/test_phase101b_evidence_chain_api_service_readback_default_off.py",
}

SCRAPER_SOURCE_HEALTH_METRICS_FILES = {
    "src/config/consts.py",
    "src/discovery/crawl_scheduler.py",
    "src/pipeline/collector.py",
    "src/scrapers/ashby_scraper.py",
    "src/scrapers/builtin_scraper.py",
    "src/scrapers/greenhouse_scraper.py",
    "src/scrapers/jobvite_scraper.py",
    "src/scrapers/lever_scraper.py",
    "src/scrapers/smartrecruiters_scraper.py",
    "src/scrapers/workable_scraper.py",
    "src/scrapers/workday_scraper.py",
    "src/storage/metrics_store.py",
    "src/utils/ats_health.py",
    "src/utils/http_retry.py",
    "src/utils/pipeline_metrics.py",
    "src/utils/workday_timestamp.py",
    "tests/support/phase_guard_registry.py",
    "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
    "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
    "tests/test_phase85b_legacy_guard_registry_default_off.py",
    "tests/test_scraper_source_health_metrics.py",
}

DISCOVERY_ACQUISITION_LIFECYCLE_FILES = {
    "src/storage/discovery_store.py",
    "tests/support/phase_guard_registry.py",
    "tests/test_discovery_store_acquisition_lifecycle.py",
    "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
    "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
    "tests/test_phase85b_legacy_guard_registry_default_off.py",
}

SMARTRECRUITERS_PAGINATION_FILES = {
    "src/config/consts.py",
    "src/scrapers/smartrecruiters_scraper.py",
    "tests/support/phase_guard_registry.py",
    "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
    "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
    "tests/test_phase85b_legacy_guard_registry_default_off.py",
    "tests/test_smartrecruiters_pagination.py",
}

WORKDAY_PAGINATION_FRESHNESS_FILES = {
    "src/pipeline/collector.py",
    "src/pipeline/job_filter.py",
    "src/scrapers/workday_scraper.py",
    "src/utils/posted_at_utils.py",
    "src/utils/workday_timestamp.py",
    "tests/support/phase_guard_registry.py",
    "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
    "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
    "tests/test_phase85b_legacy_guard_registry_default_off.py",
    "tests/test_scraper_transport_pagination_hardening.py",
    "tests/test_workday_timestamp_hydration.py",
}

WORKDAY_DISCOVERY_IDENTITY_CONTRACT_FILES = {
    "src/agents/company_discovery_agent.py",
    "src/discovery/career_ats_detector.py",
    "src/discovery/discovery.py",
    "src/discovery/sitemap_fetcher.py",
    "tests/support/phase_guard_registry.py",
    "tests/test_company_discovery_agent.py",
    "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
    "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
    "tests/test_phase85b_legacy_guard_registry_default_off.py",
    "tests/test_workday_discovery_identity_contract.py",
}

RECRUITEE_SOURCE_INTEGRATION_FILES = {
    "src/config/consts.py",
    "src/config/curated_ats_sources.json",
    "src/discovery/curated_ats_sources.py",
    "src/pipeline/collector.py",
    "src/scrapers/recruitee_scraper.py",
    "tests/support/phase_guard_registry.py",
    "tests/test_curated_ats_sources.py",
    "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
    "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
    "tests/test_phase85b_legacy_guard_registry_default_off.py",
    "tests/test_recruitee_scraper.py",
    "tests/test_scraper_acquisition_outcomes.py",
    "tests/test_scraper_parallel_result_contract.py",
    "tests/test_scraper_source_health_metrics.py",
}

RECRUITEE_STANDALONE_DISCOVERY_FILES = {
    "src/agents/company_discovery_agent.py",
    "tests/support/phase_guard_registry.py",
    "tests/test_company_discovery_agent.py",
    "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
    "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
    "tests/test_phase85b_legacy_guard_registry_default_off.py",
}

PERSONIO_SOURCE_RETIREMENT_FILES = {
    "src/config/consts.py",
    "src/config/curated_ats_sources.json",
    "src/discovery/curated_ats_sources.py",
    "src/pipeline/collector.py",
    "src/scrapers/personio_scraper.py",
    "tests/support/phase_guard_registry.py",
    "tests/test_curated_ats_sources.py",
    "tests/test_personio_scraper.py",
    "tests/test_personio_source_retirement.py",
    "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
    "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
    "tests/test_phase85b_legacy_guard_registry_default_off.py",
    "tests/test_scraper_prefilter_ownership_boundary.py",
    "tests/test_scraper_source_health_metrics.py",
    "tests/test_scraper_transport_pagination_hardening.py",
    "tests/test_user_pipeline_role_preferences.py",
}

USAJOBS_SOURCE_INTEGRATION_FILES = {
    "src/config/consts.py",
    "src/config/usajobs_query_profiles.json",
    "src/pipeline/collector.py",
    "src/scrapers/usajobs_scraper.py",
    "tests/support/phase_guard_registry.py",
    "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
    "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
    "tests/test_phase85b_legacy_guard_registry_default_off.py",
    "tests/test_usajobs_scraper.py",
}

HIMALAYAS_STEP6B1_ATTRIBUTION_FOUNDATION_FILES = {
    "src/app/services.py",
    "src/app/static/app.js",
    "src/pipeline/dedupe.py",
    "src/rag/job_document_builder.py",
    "tests/support/phase_guard_registry.py",
    "tests/test_phase16a_lean_deterministic_prefilter_dedupe_orchestration.py",
    "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
    "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
    "tests/test_phase85b_legacy_guard_registry_default_off.py",
    "tests/test_provider_attribution_ui.py",
    "tests/test_rag_export_job_corpus.py",
    "tests/test_supplemental_source_dedupe.py",
}

HIMALAYAS_STEP6B2_SOURCE_INTEGRATION_FILES = {
    "src/config/consts.py",
    "src/config/himalayas_query_profiles.json",
    "src/pipeline/collector.py",
    "src/scrapers/himalayas_scraper.py",
    "tests/support/phase_guard_registry.py",
    "tests/test_himalayas_scraper.py",
    "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
    "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
    "tests/test_phase85b_legacy_guard_registry_default_off.py",
}

HIMALAYAS_STEP6C1_PAGINATION_REPAIR_FILES = {
    "src/scrapers/himalayas_scraper.py",
    "tests/support/phase_guard_registry.py",
    "tests/test_himalayas_scraper.py",
    "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
    "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
    "tests/test_phase85b_legacy_guard_registry_default_off.py",
}

HIMALAYAS_STEP6D_B1_RETENTION_FOUNDATION_FILES = {
    "src/pipeline/himalayas_retention.py",
    "src/rag/export_job_corpus.py",
    "src/rag/job_document_builder.py",
    "src/storage/rag_store.py",
    "src/storage/user_pipeline/schema.sql",
    "src/storage/user_pipeline/store.py",
    "src/utils/job_cache.py",
    "tests/support/phase_guard_registry.py",
    "tests/test_himalayas_active_retention.py",
    "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
    "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
    "tests/test_phase85b_legacy_guard_registry_default_off.py",
}

HIMALAYAS_STEP6D_B2_RETENTION_INTEGRATION_FILES = {
    "src/app/services.py",
    "src/pipeline/collector.py",
    "tests/support/phase_guard_registry.py",
    "tests/test_himalayas_active_retention.py",
    "tests/test_himalayas_retention_integration.py",
    "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
    "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
    "tests/test_phase85b_legacy_guard_registry_default_off.py",
}

HIMALAYAS_STEP6D_C_SOURCE_RETIREMENT_FILES = {
    "manage_himalayas_retention.py",
    "src/app/services.py",
    "src/pipeline/himalayas_retention.py",
    "src/rag/export_job_corpus.py",
    "src/storage/user_pipeline/store.py",
    "tests/support/phase_guard_registry.py",
    "tests/test_himalayas_retention_integration.py",
    "tests/test_himalayas_source_retirement.py",
    "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
    "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
    "tests/test_phase85b_legacy_guard_registry_default_off.py",
}

HIMALAYAS_STEP6E_R1_LOCATION_ACTIVATION_FILES = {
    "src/config/himalayas_query_profiles.json",
    "src/pipeline/scheduler.py",
    "src/rag/job_document_builder.py",
    "tests/support/phase_guard_registry.py",
    "tests/test_himalayas_activation.py",
    "tests/test_himalayas_scraper.py",
    "tests/test_himalayas_source_retirement.py",
    "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
    "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
    "tests/test_phase85b_legacy_guard_registry_default_off.py",
    "tests/test_rag_export_job_corpus.py",
}

HIMALAYAS_STEP2B_LOCATION_COVERAGE_FILES = {
    "src/config/consts.py",
    "src/config/himalayas_query_profiles.json",
    "src/discovery/crawl_scheduler.py",
    "src/scrapers/himalayas_scraper.py",
    "tests/support/phase_guard_registry.py",
    "tests/test_himalayas_scraper.py",
    "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
    "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
    "tests/test_phase85b_legacy_guard_registry_default_off.py",
}

SCRAPER_PREFILTER_OWNERSHIP_BOUNDARY_FILES = {
    "src/pipeline/collector.py",
    "src/scrapers/greenhouse_scraper.py",
    "src/scrapers/lever_scraper.py",
    "src/scrapers/recruitee_scraper.py",
    "src/scrapers/workday_scraper.py",
    "tests/support/phase_guard_registry.py",
    "tests/test_lever_role_expansion_filtering.py",
    "tests/test_phase85b_legacy_guard_registry_default_off.py",
    "tests/test_recruitee_scraper.py",
    "tests/test_scraper_acquisition_outcomes.py",
    "tests/test_scraper_prefilter_ownership_boundary.py",
    "tests/test_scraper_transport_pagination_hardening.py",
}

BROAD_TECH_PREFILTER_TAXONOMY_FILES = {
    "src/config/role_taxonomy.py",
    "tests/support/phase_guard_registry.py",
    "tests/test_broad_tech_prefilter_taxonomy.py",
    "tests/test_phase85b_legacy_guard_registry_default_off.py",
    "tests/test_user_pipeline_role_preferences.py",
}

TECHNICAL_PRODUCT_PROGRAM_ROLE_FAMILY_FILES = {
    "src/app/onboarding_ui.py",
    "src/config/role_scoring_profiles.py",
    "src/config/role_taxonomy.py",
    "src/intelligence/role_family_classifier.py",
    "src/pipeline/job_filter.py",
    "src/pipeline/job_ranker.py",
    "tests/support/phase_guard_registry.py",
    "tests/test_broad_tech_prefilter_taxonomy.py",
    "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
    "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
    "tests/test_phase85b_legacy_guard_registry_default_off.py",
    "tests/test_role_taxonomy.py",
    "tests/test_role_title_filtering.py",
    "tests/test_technical_product_program_role_families.py",
}

PHASE2D_A_INDEPENDENT_SENIORITY_POLICY_FILES = {
    "src/config/seniority_policy.py",
    "src/pipeline/collector.py",
    "src/pipeline/job_ranker.py",
    "src/storage/onboarding_preferences/store.py",
    "tests/support/phase_guard_registry.py",
    "tests/test_independent_seniority_policy.py",
    "tests/test_onboarding_preferences_store.py",
    "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
    "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
    "tests/test_phase85b_legacy_guard_registry_default_off.py",
    "tests/test_user_pipeline_role_preferences.py",
}

PHASE2D_B1_DEFAULT_ELIGIBILITY_OWNERSHIP_FILES = {
    "src/config/role_taxonomy.py",
    "src/config/seniority_policy.py",
    "src/pipeline/job_filter.py",
    "tests/support/phase_guard_registry.py",
    "tests/test_independent_seniority_prefilter.py",
    "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
    "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
    "tests/test_phase85b_legacy_guard_registry_default_off.py",
}

PHASE2D_B2_STRICT_SENIORITY_FILTER_FILES = {
    "src/agents/deterministic_prefilter_dedupe_authoritative_graph.py",
    "src/app/onboarding_ui.py",
    "src/app/services.py",
    "src/app/static/onboarding.js",
    "src/app/static/preferences_workflow.js",
    "src/app/static/profile.js",
    "src/config/seniority_policy.py",
    "src/pipeline/collector.py",
    "src/pipeline/job_filter.py",
    "src/storage/onboarding_preferences/schema.sql",
    "src/storage/onboarding_preferences/store.py",
    "tests/support/phase_guard_registry.py",
    "tests/test_independent_seniority_policy.py",
    "tests/test_independent_seniority_prefilter.py",
    "tests/test_onboarding_api.py",
    "tests/test_onboarding_preferences_store.py",
    "tests/test_onboarding_ui_contract.py",
    "tests/test_phase132b2r3_guided_preferences_workflow.py",
    "tests/test_phase16a_lean_deterministic_prefilter_dedupe_orchestration.py",
    "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
    "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
    "tests/test_phase85b_legacy_guard_registry_default_off.py",
    "tests/test_role_title_filtering.py",
    "tests/test_strict_seniority_filter.py",
    "tests/test_technical_product_program_role_families.py",
    "tests/test_user_pipeline_role_preferences.py",
}

SOURCE_YIELD_UI_FILES = {
    "frontend/executive-kpi/src/SourceYield.test.tsx",
    "frontend/executive-kpi/src/SourceYield.tsx",
    "frontend/executive-kpi/src/main.test.tsx",
    "frontend/executive-kpi/src/main.tsx",
    "frontend/executive-kpi/src/styles.css",
    "src/app/services.py",
    "src/app/static/app.js",
    "src/app/static/app_redesign.css",
    "src/app/static/build/executive-kpi/executive-kpi.css",
    "src/app/static/build/executive-kpi/executive-kpi.js",
    "src/app/ui.py",
    "tests/support/phase_guard_registry.py",
    "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
    "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
    "tests/test_phase85b_legacy_guard_registry_default_off.py",
    "tests/test_source_yield_status.py",
    "tests/test_source_yield_ui_contract.py",
}

JOBVITE_LOCATION_FRESHNESS_FILES = {
    "src/pipeline/job_filter.py",
    "src/scrapers/jobvite_scraper.py",
    "src/utils/html_timestamp_extractor.py",
    "tests/support/phase_guard_registry.py",
    "tests/test_jobvite_location_freshness.py",
    "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
    "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
    "tests/test_phase85b_legacy_guard_registry_default_off.py",
}

JOBVITE_STANDALONE_DISCOVERY_FILES = {
    "src/agents/company_discovery_agent.py",
    "src/scrapers/jobvite_scraper.py",
    "tests/support/phase_guard_registry.py",
    "tests/test_company_discovery_agent.py",
    "tests/test_jobvite_location_freshness.py",
    "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
    "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
    "tests/test_phase85b_legacy_guard_registry_default_off.py",
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
        "smartrecruiters_pagination": SMARTRECRUITERS_PAGINATION_FILES,
        "workday_pagination_freshness": WORKDAY_PAGINATION_FRESHNESS_FILES,
        "workday_discovery_identity_contract": WORKDAY_DISCOVERY_IDENTITY_CONTRACT_FILES,
        "himalayas_step2b_location_coverage": HIMALAYAS_STEP2B_LOCATION_COVERAGE_FILES,
        "himalayas_step6e_r1_location_activation": HIMALAYAS_STEP6E_R1_LOCATION_ACTIVATION_FILES,
        "himalayas_step6d_c_source_retirement": HIMALAYAS_STEP6D_C_SOURCE_RETIREMENT_FILES,
        "himalayas_step6d_b2_retention_integration": HIMALAYAS_STEP6D_B2_RETENTION_INTEGRATION_FILES,
        "himalayas_step6d_b1_retention_foundation": HIMALAYAS_STEP6D_B1_RETENTION_FOUNDATION_FILES,
        "himalayas_step6c1_pagination_repair": HIMALAYAS_STEP6C1_PAGINATION_REPAIR_FILES,
        "himalayas_step6b2_source_integration": HIMALAYAS_STEP6B2_SOURCE_INTEGRATION_FILES,
        "himalayas_step6b1_attribution_foundation": HIMALAYAS_STEP6B1_ATTRIBUTION_FOUNDATION_FILES,
        "usajobs_source_integration": USAJOBS_SOURCE_INTEGRATION_FILES,
        "personio_source_retirement": PERSONIO_SOURCE_RETIREMENT_FILES,
        "recruitee_source_integration": RECRUITEE_SOURCE_INTEGRATION_FILES,
        "recruitee_standalone_discovery": RECRUITEE_STANDALONE_DISCOVERY_FILES,
        "source_yield_ui": SOURCE_YIELD_UI_FILES,
        "jobvite_location_freshness": JOBVITE_LOCATION_FRESHNESS_FILES,
        "jobvite_standalone_discovery": JOBVITE_STANDALONE_DISCOVERY_FILES,
        "live_pipeline_ai_evaluation_reliability_lr2b": {
            "src/ai/job_fit_evaluator.py",
            "src/evaluation/controlled_openai_canary_transport.py",
            "src/evaluation/controlled_production_parity_benchmark.py",
            "tests/support/phase_guard_registry.py",
            "tests/test_controlled_openai_canary_transport.py",
            "tests/test_controlled_production_parity_benchmark.py",
            "tests/test_phase17b_lean_cache_first_semantic_evaluation_activation.py",
        },
        "live_pipeline_ai_evaluation_reliability_lr2b_lr2c": {
            "src/ai/job_fit_evaluator.py",
            "src/evaluation/controlled_openai_canary_transport.py",
            "src/evaluation/controlled_production_parity_benchmark.py",
            "src/pipeline/collector.py",
            "tests/support/phase_guard_registry.py",
            "tests/test_controlled_openai_canary_transport.py",
            "tests/test_controlled_production_parity_benchmark.py",
            "tests/test_phase17b_lean_cache_first_semantic_evaluation_activation.py",
            "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
            "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
        },
        "live_pipeline_ai_evaluation_reliability_fvr2b_source_contracts": {
            "tests/test_phase16b_lean_deterministic_production_orchestration_closure.py",
            "tests/test_phase17a_lean_cache_first_jd_intelligence_activation.py",
            "tests/test_phase83b_live_llm_invocation_contract_map_default_off.py",
            "tests/test_phase87b_jd_intelligence_existing_output_collector_diagnostics_default_off.py",
        },
        "item61b_agentic_review_admin_boundary": (
            ITEM61B_AGENTIC_REVIEW_ADMIN_BOUNDARY_FILES
        ),
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
        "phase1_ai_provider_model_routing_hash_maintenance": {
            "requirements.txt",
            "src/ai/llm_client.py",
            "src/ai/job_fit_evaluator.py",
            "src/app/services.py",
            "src/app/static/agentic_review.js",
            "src/app/static/app_redesign.css",
            "src/evaluation/controlled_groq_canary_transport.py",
            "src/pipeline/collector.py",
            "src/pipeline/job_ranker.py",
            "src/agents/jd_intelligence.py",
            "src/tailoring/llm.py",
            "tests/support/phase_guard_registry.py",
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
        "phase2d_a_independent_seniority_policy": (
            PHASE2D_A_INDEPENDENT_SENIORITY_POLICY_FILES
        ),
        "phase2d_b1_default_eligibility_ownership": (
            PHASE2D_B1_DEFAULT_ELIGIBILITY_OWNERSHIP_FILES
        ),
        "phase2d_b2_strict_seniority_filter": (
            PHASE2D_B2_STRICT_SENIORITY_FILTER_FILES
        ),
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
        "phase9_step9_durable_orchestration_schema_executor": {
            "src/storage/admin_tools/durable_orchestration/apply_schema.py",
            "tests/test_phase9_step9_durable_orchestration_schema_executor_contract.py",
        },
        "phase9_step10_durable_orchestration_postgres_integration": {
            "tests/test_phase9_step10_durable_orchestration_postgres_integration.py",
        },
        "phase9_step12_postgres_runtime_repository_integration": {
            "requirements.txt",
            "src/storage/durable_orchestration/postgres_connection.py",
            "tests/test_phase9_step12_durable_orchestration_postgres_runtime_integration.py",
        },
        "phase9_step14_langgraph_postgres_checkpointer_foundation": {
            "requirements.txt",
            "src/storage/durable_orchestration/langgraph_postgres.py",
            "src/storage/admin_tools/durable_orchestration/setup_langgraph_checkpointer.py",
            "tests/test_phase9_step14_langgraph_postgres_checkpointer_foundation.py",
        },
        "phase9_step16a_durable_decision_authorization_runtime": {
            "src/storage/durable_orchestration/store.py",
            "src/storage/durable_orchestration/repository.py",
            "tests/test_phase9_step16a_durable_decision_authorization_runtime_contract.py",
        },
        "phase9_step16b_attempt_recovery_terminal_runtime": {
            "src/storage/durable_orchestration/store.py",
            "src/storage/durable_orchestration/repository.py",
            "tests/test_phase9_step16b_attempt_recovery_terminal_runtime_contract.py",
        },
        "phase9_step17_durable_langgraph_restart_resume_integration": {
            "src/agents/durable_evidence_chain_resume_coordinator.py",
            "tests/test_phase9_step17_durable_langgraph_restart_resume_integration.py",
        },
        "phase9_step18a_coordinator_owned_resume_boundary": {
            "src/agents/durable_evidence_chain_resume_coordinator.py",
            "tests/test_phase9_step17_durable_langgraph_restart_resume_integration.py",
            "tests/test_phase9_step18a_coordinator_owned_resume_boundary.py",
        },
        "phase9_step18b_durable_langgraph_process_restart": {
            "tests/support/phase9_step18b_restart_process_worker.py",
            "tests/test_phase9_step18b_durable_langgraph_process_restart.py",
        },
        "phase10_step2_shadow_adapter_parity_foundation": {
            "src/agents/evidence_chain_shadow_adapter.py",
            "src/agents/evidence_chain_shadow_parity.py",
            "tests/test_phase10_shadow_input_adapter.py",
            "tests/test_phase10_shadow_parity_contract.py",
            "tests/test_phase10_shadow_adapter_write_suppression.py",
        },
        "phase10_step3_explicit_readonly_shadow_execution": {
            "src/agents/evidence_chain_shadow_execution.py",
            "run_evidence_chain_shadow.py",
            "tests/test_phase10_shadow_execution_readonly.py",
            "tests/test_phase10_shadow_command_default_off.py",
            "tests/test_phase10_shadow_execution_write_suppression.py",
        },
        "phase10_step5a_shadow_resume_evidence_projection": {
            "batch_select_best_resume_variant.py",
            "run_application_planning.py",
            "src/pipeline/shadow_resume_evidence_projection.py",
            "tests/test_phase10_step5a_shadow_resume_evidence_projection.py",
        },
        "phase10_step5b_shadow_projection_failure_isolation": {
            "batch_select_best_resume_variant.py",
            "run_application_planning.py",
            "src/pipeline/shadow_resume_evidence_projection.py",
            "tests/test_phase10_step5b_shadow_projection_failure_isolation.py",
        },
        "phase10_step5c_default_off_post_planning_shadow_hook": {
            "main.py",
            "src/pipeline/post_planning_shadow.py",
            "tests/test_phase10_step5c_default_off_post_planning_shadow_hook.py",
        },
        "phase10_step8_shadow_observation_safety": {
            "src/pipeline/post_planning_shadow.py",
            "src/pipeline/shadow_observation_contract.py",
            "src/pipeline/shadow_observation_store.py",
            "docs/controlled_shadow_observation_runbook.md",
            "tests/test_phase10_step8_shadow_observation_contract.py",
            "tests/test_phase10_step8_shadow_observation_store.py",
            "tests/test_phase10_step8_shadow_cleanup_liveness.py",
            "tests/test_phase10_step8_shadow_observation_integration.py",
        },
        "phase10_step11_postgres_planning_corpus_snapshot": {
            "main.py",
            "src/pipeline/postgres_planning_corpus_snapshot.py",
            "tests/test_phase10_step11_postgres_planning_corpus_snapshot.py",
            "tests/support/phase_guard_registry.py",
            "tests/test_phase85b_legacy_guard_registry_default_off.py",
        },
        "phase11_step2_job_prioritization_graph_contract": {
            "src/agents/job_prioritization_graph_verification.py",
            "tests/test_phase11_step2_job_prioritization_graph_contract.py",
            "tests/support/phase_guard_registry.py",
            "tests/test_phase85b_legacy_guard_registry_default_off.py",
            "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
            "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
        },
        "phase11_step3_job_prioritization_graph_integration": {
            "application_execution_queue.py",
            "src/agents/job_prioritization_graph_verification.py",
            "src/agents/job_prioritization_graph_integration.py",
            "tests/test_phase11_step3_job_prioritization_graph_integration.py",
            "tests/support/phase_guard_registry.py",
            "tests/test_phase85b_legacy_guard_registry_default_off.py",
            "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
            "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
        }
        | PHASE11_STEP3_DIRECT_HASH_GUARD_FILES,
        "phase13c_authoritative_job_prioritization_node": (
            PHASE13C_AUTHORITATIVE_JOB_PRIORITIZATION_NODE_FILES
        ),
        "phase14b_authoritative_tailoring_caller": (
            PHASE14B_AUTHORITATIVE_TAILORING_CALLER_FILES
        ),
        "phase14c_authoritative_tailoring_node": (
            PHASE14C_AUTHORITATIVE_TAILORING_NODE_FILES
        ),
        "phase15b_conditional_operator_review_caller": (
            PHASE15B_CONDITIONAL_OPERATOR_REVIEW_CALLER_FILES
        ),
        "phase15c_conditional_operator_review_node": (
            PHASE15C_CONDITIONAL_OPERATOR_REVIEW_NODE_FILES
        ),
        "phase17c_tailoring_generation_llm_closure": (
            PHASE17C_TAILORING_GENERATION_LLM_CLOSURE_FILES
        ),
        "phase9_step12_dependency_driver_compatibility": {
            "tests/test_agent_trace_store.py",
            "tests/test_jd_provider_runtime_api_readback_default_off.py",
            "tests/test_pgvector_extension_probe_api_no_schema_no_ui.py",
            "tests/test_pgvector_extension_probe_service_helper_no_schema.py",
            "tests/test_phase8_pgvector_backend_readiness_schema_plan_no_runtime_change.py",
            "tests/test_provider_runtime_activation_plan_default_off.py",
            "tests/test_provider_runtime_api_readback_default_off.py",
            "tests/test_provider_runtime_readiness_checkpoint_default_off.py",
            "tests/test_provider_runtime_service_bridge_default_off.py",
            "tests/test_three_agent_llmops_observability_api_default_off.py",
            "tests/test_vector_evidence_api_no_db_no_ui.py",
            "tests/test_vector_evidence_readback_api_default_off.py",
        },
    }
    try:
        return set(profiles[profile])
    except KeyError as exc:
        raise AssertionError(f"Unknown legacy guard allowlist profile: {profile}") from exc


def current_milestone_guard_compatibility_allowlist() -> set[str]:
    """Exact current milestone files accepted by stale registry-backed guards."""
    return (
        STEP1B2_GLOBAL_ACQUISITION_BOUNDARY_FILES
        | STEP1B3_OWNER_PROJECTION_SHARED_POOL_FILES
        | STEP1B4_OWNER_SELECTOR_LLM_ROUTING_FILES
        | ITEM2_MANUAL_PROVIDER_PREVIEW_JOB_IDENTITY_REPAIR_FILES
        | ITEM2_MANUAL_PROVIDER_PREVIEW_PROMPT_SCHEMA_ALIGNMENT_FILES
        | ITEM3_DASHBOARD_SCOPED_CHATBOT_FILES
        | ITEM4_PLANNING_TAILORING_OPTIONS_FILES
        | ITEM6_AGENTIC_REVIEW_UI_REVAMP_FILES
        | legacy_guard_allowlist("item61b_agentic_review_admin_boundary")
        | legacy_guard_allowlist("smartrecruiters_pagination")
        | legacy_guard_allowlist("workday_pagination_freshness")
        | legacy_guard_allowlist("himalayas_step2b_location_coverage")
        | legacy_guard_allowlist("himalayas_step6c1_pagination_repair")
        | legacy_guard_allowlist("himalayas_step6b2_source_integration")
        | legacy_guard_allowlist("himalayas_step6b1_attribution_foundation")
        | legacy_guard_allowlist("policy_driven_llm_adjudicator_readback")
        | legacy_guard_allowlist("phase129b_auth_loader_ui")
        | legacy_guard_allowlist("phase129c_workflow_overlay_and_run_scoped_corpus")
        | legacy_guard_allowlist("phase132b_premium_preferences_ui")
        | legacy_guard_allowlist("phase2d_a_independent_seniority_policy")
        | legacy_guard_allowlist("phase2d_b1_default_eligibility_ownership")
        | legacy_guard_allowlist("phase2d_b2_strict_seniority_filter")
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
        | legacy_guard_allowlist("source_yield_ui")
        | legacy_guard_allowlist("jobvite_location_freshness")
        | legacy_guard_allowlist(
            "live_pipeline_ai_evaluation_reliability_lr2b_lr2c"
        )
        | legacy_guard_allowlist(
            "live_pipeline_ai_evaluation_reliability_fvr2b_source_contracts"
        )
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
        | legacy_guard_allowlist(
            "phase9_step9_durable_orchestration_schema_executor"
        )
        | legacy_guard_allowlist(
            "phase9_step10_durable_orchestration_postgres_integration"
        )
        | legacy_guard_allowlist(
            "phase9_step12_postgres_runtime_repository_integration"
        )
        | legacy_guard_allowlist(
            "phase9_step14_langgraph_postgres_checkpointer_foundation"
        )
        | legacy_guard_allowlist(
            "phase9_step16a_durable_decision_authorization_runtime"
        )
        | legacy_guard_allowlist(
            "phase9_step16b_attempt_recovery_terminal_runtime"
        )
        | legacy_guard_allowlist(
            "phase9_step17_durable_langgraph_restart_resume_integration"
        )
        | legacy_guard_allowlist(
            "phase9_step18a_coordinator_owned_resume_boundary"
        )
        | legacy_guard_allowlist(
            "phase9_step18b_durable_langgraph_process_restart"
        )
        | legacy_guard_allowlist(
            "phase10_step2_shadow_adapter_parity_foundation"
        )
        | legacy_guard_allowlist(
            "phase10_step3_explicit_readonly_shadow_execution"
        )
        | legacy_guard_allowlist(
            "phase10_step5a_shadow_resume_evidence_projection"
        )
        | legacy_guard_allowlist(
            "phase10_step5b_shadow_projection_failure_isolation"
        )
        | legacy_guard_allowlist(
            "phase10_step5c_default_off_post_planning_shadow_hook"
        )
        | legacy_guard_allowlist(
            "phase10_step8_shadow_observation_safety"
        )
        | legacy_guard_allowlist(
            "phase10_step11_postgres_planning_corpus_snapshot"
        )
        | legacy_guard_allowlist(
            "phase11_step2_job_prioritization_graph_contract"
        )
        | legacy_guard_allowlist(
            "phase11_step3_job_prioritization_graph_integration"
        )
        | legacy_guard_allowlist(
            "phase13c_authoritative_job_prioritization_node"
        )
        | legacy_guard_allowlist(
            "phase14b_authoritative_tailoring_caller"
        )
        | legacy_guard_allowlist(
            "phase14c_authoritative_tailoring_node"
        )
        | legacy_guard_allowlist(
            "phase15b_conditional_operator_review_caller"
        )
        | legacy_guard_allowlist(
            "phase15c_conditional_operator_review_node"
        )
        | legacy_guard_allowlist(
            "phase17c_tailoring_generation_llm_closure"
        )
        | legacy_guard_allowlist(
            "phase9_step12_dependency_driver_compatibility"
        )
        | PHASE11_STEP8L_PROVIDER_BENCHMARK_CONTRACT_FILES
        | PHASE11_STEP8M_PROVIDER_CLIENT_COMPATIBILITY_FILES
        | PHASE11_STEP8N_SHARED_LLM_CLIENT_SAFETY_FILES
        | PHASE11_STEP8O_PROVIDER_FIXTURE_BENCHMARK_FILES
        | PHASE11_STEP8P_CONTROLLED_PROVIDER_BENCHMARK_PLAN_FILES
        | PHASE11_STEP8PA_TRANSMISSION_SAFE_FIXTURE_FILES
        | PHASE11_STEP8Q_CONTROLLED_PROVIDER_BENCHMARK_HARNESS_FILES
        | PHASE11_STEP8R_GROQ_LIVE_CANARY_PREPARATION_FILES
        | PHASE11_STEP8T_REAL_GROQ_CANARY_TRANSPORT_FILES
        | PHASE11_STEP8V_GROQ_CANARY_EVIDENCE_RUNTIME_FILES
        | PHASE11_STEP8Y_GROQ_CANARY_RUN_IDENTITY_FILES
        | PHASE11_STEP8Z_GROQ_CANARY_RUN_EVIDENCE_RUNTIME_FILES
        | PHASE11_STEP8ZE_GROQ_CANARY_RUN_003_PLAN_FILES
        | PHASE11_STEP8ZF_GROQ_CANARY_RUN_003_IDENTITY_FILES
        | PHASE11_STEP8ZG_GROQ_CANARY_RUN_003_RUNTIME_FILES
        | PHASE11_STEP8ZK_GROQ_CANARY_RUN_004_OFFLINE_RUNTIME_FILES
        | PHASE11_STEP8ZN_GROQ_CANARY_RUN_005_DIAGNOSTIC_RUNTIME_FILES
        | PHASE11_STEP8ZQ_ADDITIVE_TAILORING_TRANSPORT_FILES
        | PHASE11_STEP8MA_RAG_TEST_ISOLATION_FILES
        | PHASE12D_DETERMINISTIC_PRODUCTION_OWNER_SHADOW_FILES
        | PHASE21_RELEASE_CANDIDATE_FILES
        | PHASE21H_PROVIDER_BENCHMARK_HERMETICITY_FILES
        | PHASE21R_HISTORICAL_GUARD_FILES
        | SCRAPER_TRANSPORT_PAGINATION_HARDENING_FILES
        | SCRAPER_SOURCE_HEALTH_METRICS_FILES
        | DISCOVERY_ACQUISITION_LIFECYCLE_FILES
        | PERSONIO_SOURCE_RETIREMENT_FILES
        | RECRUITEE_SOURCE_INTEGRATION_FILES
        | RECRUITEE_STANDALONE_DISCOVERY_FILES
        | JOBVITE_STANDALONE_DISCOVERY_FILES
        | WORKDAY_DISCOVERY_IDENTITY_CONTRACT_FILES
        | SCRAPER_PREFILTER_OWNERSHIP_BOUNDARY_FILES
        | BROAD_TECH_PREFILTER_TAXONOMY_FILES
        | TECHNICAL_PRODUCT_PROGRAM_ROLE_FAMILY_FILES
        | PHASE2D_A_INDEPENDENT_SENIORITY_POLICY_FILES
        | PHASE2D_B1_DEFAULT_ELIGIBILITY_OWNERSHIP_FILES
        | PHASE2D_B2_STRICT_SENIORITY_FILTER_FILES
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
            "application_execution_queue.py",
            "c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0",
        ): "9bb4530b5a308356b908a958456ff18415c19e264b5e1c030fe8828d6caa481f",
        (
            "application_execution_queue.py",
            "28ac5d153eeb1d3e6238bed57418a45b603f72caea6c0f671a8dcbb3b0a76097",
        ): "9bb4530b5a308356b908a958456ff18415c19e264b5e1c030fe8828d6caa481f",
        (
            "application_execution_queue.py",
            "17256e6fe4554ca5d3136468cbae7602f765666c9f98e963508b2a6d822a49d5",
        ): "9bb4530b5a308356b908a958456ff18415c19e264b5e1c030fe8828d6caa481f",
        (
            "application_execution_queue.py",
            "417ee7a37bf05c4cbfa7fe01c1b1d09376a2c7680d2a97867d3ebb529c48cf9f",
        ): "9bb4530b5a308356b908a958456ff18415c19e264b5e1c030fe8828d6caa481f",
        (
            "application_execution_queue.py",
            "c68a0a6eda5e96e348dc1b47ccba826df2f1041c18c4cc46f42861fdb35e105e",
        ): "9bb4530b5a308356b908a958456ff18415c19e264b5e1c030fe8828d6caa481f",
        (
            "requirements.txt",
            "5dc563901e19c10a0f59fe811ec6961ee47f837827a7448e3a669aed9f244cc6",
        ): frozenset({
            "75d10d919dd53cdc3e55056abe28503b5b0bde38d5e61d944beb794562886cc3",
            "d396bfd09de172954a0bfd652aceb25c0def1f64081b46067a337f4ebe06714c",
        }),
        (
            "requirements.txt",
            "75d10d919dd53cdc3e55056abe28503b5b0bde38d5e61d944beb794562886cc3",
        ): "d396bfd09de172954a0bfd652aceb25c0def1f64081b46067a337f4ebe06714c",
        (
            "src/app/api.py",
            "d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004",
        ): frozenset({
            "0b9923e4a7df78ca4f0e4983b1718e42c6d827785f83fbed78b0150547353012",
            "f5babdc02fa0f6df589e60b02cb6fa4eba4d073db14cdb95b2f5be550fd43a68",
            "3497214cd9f379a58687739117c40b420f04f17622a4b5d1a5e7d982b0a8e1f6",
            "67a9925651d237f353f42e564e55f36f08dd7f63db8c09ce36fd4d277d6b66c6",
            # Item 4 planning & tailoring options review successor.
            "e658a10a817998be1d7573de7872047d44e1f088b1601e3a806ed2f22b396e2c",
            # Item 6.1B Agentic Review admin boundary successor.
            "ca8de5e0643a4c24eb6d36c0371ee4c6e422a9dfa2c7dd01ce664954b959a985",
        }),
        (
            "src/app/services.py",
            "bfa035faa8e89abd2b75095f68b45a282fb3b7fc8e5ff43e36c754db56ef12c2",
        ): "23401720ca3f4243a2b85eb03f8ac5e49e205b4f8039a8fdf86d18b9b3e1ea3d",
        (
            "src/app/static/app_redesign.css",
            "81eede647edd99ca1f8c0f5b759b35ecf40e223db9d9dbd4b976f487ecf49961",
        ): "e4c15f04c6c63a28cfa59784134a69cd3832d7f85169fea31add02a3e76d7828",
        (
            "src/app/static/app_redesign.css",
            "e4c15f04c6c63a28cfa59784134a69cd3832d7f85169fea31add02a3e76d7828",
        ): frozenset({
            "f544310044957fcd28c74e9375093695a0b94814e2473435ff1fdefe7fc93df5",
            "8f2ab896d709e95a6ae0300004a799e9206e8c20af1c82fa08d9414bd85ef06a",
            "bae6084f3be7e173e2cb9ec4bf39d085531a4f628f88508445b0a583783e0ded",
            # Item 3 floating ApplyLens AI chatbot successor.
            "90aff70ad5eb13958187dbd17f0250ec976ba8bd99a29e78f841bf4d0e8b5cbb",
        }),
        (
            "src/ai/llm_client.py",
            "830866d616c8d2d5d6b2147cd6a17b19f049f8a064592d78c2b7170d4e49ffc2",
        ): frozenset({
            "61100917a63b5285e7d1fa07ce5da47d73b6ee17f0bb3d3f88e6380722bc85f1",
            "ff2f412c4bcc3067e73d4fb78c65b53fa9d9760f56f1451d0dff6d4840386309",
            "687ce0fa50a7a7a6498dc93287489027708fe866da90a97ae2fff941f4bcae44",
            "82aa58a6062c9ed9a3923fdb27bd05dd45bd31e7ce9bf3160351ec84737c5885",
        }),
        (
            "src/ai/llm_client.py",
            "61100917a63b5285e7d1fa07ce5da47d73b6ee17f0bb3d3f88e6380722bc85f1",
        ): frozenset({
            "82aa58a6062c9ed9a3923fdb27bd05dd45bd31e7ce9bf3160351ec84737c5885",
        }),
        (
            "src/evaluation/controlled_groq_canary_transport.py",
            "89d01fe8460e7eae40e794dce808bb26aef6dbb02366e7c5d5bed268fdf00489",
        ): frozenset({
            "06bb37112326d658f9a7bcac6cac0897c3150652a8b734cff0794e1997746741",
        }),
        (
            "src/ai/job_fit_evaluator.py",
            "3776e5ce3c098c5329d2e7631195915f6bcf098ec0303ec619e9b0e9ecf393fb",
        ): frozenset({
            "33a145c4d1aa640f970b698c95298600ea5903711315d44ed136174d6f27a999",
            "b58d270494f9049dbcefcd785a220cb9cfb33aad4b10b75f4c149197cb0ca56e",
            "4c971173cd0e224b441263595e82b4f52eb6b0ed65172eb336e182a206bc5d3b",
        }),
        (
            "src/app/api.py",
            "85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96",
        ): frozenset({
            "0b9923e4a7df78ca4f0e4983b1718e42c6d827785f83fbed78b0150547353012",
            "f5babdc02fa0f6df589e60b02cb6fa4eba4d073db14cdb95b2f5be550fd43a68",
        }),
        (
            "src/app/services.py",
            "e30180b352ebe8abca2ec34b4b34983fbaee61a32bdc0d511001c406703e392c",
        ): "23401720ca3f4243a2b85eb03f8ac5e49e205b4f8039a8fdf86d18b9b3e1ea3d",
        (
            "src/app/api.py",
            "2b93b37a38fce17d50a9b5eb693062faa9bb9ada6a4926bb9e0f76d9ee518674",
        ): frozenset({
            "0b9923e4a7df78ca4f0e4983b1718e42c6d827785f83fbed78b0150547353012",
            "f5babdc02fa0f6df589e60b02cb6fa4eba4d073db14cdb95b2f5be550fd43a68",
            "3497214cd9f379a58687739117c40b420f04f17622a4b5d1a5e7d982b0a8e1f6",
            "67a9925651d237f353f42e564e55f36f08dd7f63db8c09ce36fd4d277d6b66c6",
            # Item 4 planning & tailoring options review successor.
            "e658a10a817998be1d7573de7872047d44e1f088b1601e3a806ed2f22b396e2c",
            # Item 6.1B Agentic Review admin boundary successor.
            "ca8de5e0643a4c24eb6d36c0371ee4c6e422a9dfa2c7dd01ce664954b959a985",
        }),
        (
            "src/app/services.py",
            "02d09d6f6e204183ef67a543222b4e3a4dae993f40041dfb8911397b835be7f7",
        ): frozenset({
            "351721d166d4a1538ed3084e169365ffdd2b8e822b399f82298418493581e963",
            "aab9f26ebe70b458fb706cfeee7f9b6ae76a9bef5303b1d5c150b9773323d20e",
            "0512c0cd141947dbc6f48565b424920393f84fb9fc426dfc2816c504b03f33ce",
            "3b11179b92301e7734cb82ef2f4cc8ba6d251e2ee363cf27d04a0461a0913a7a",
            # Item 3 floating ApplyLens AI chatbot successor.
            "a9211f507cd0294d54040d45df11b846e359f815556306e64bb6785bd1e5ad41",
            # Item 4 planning & tailoring options review successor.
            "c223631f87bd6b358bdd91e732dc54b1fd55568e93ef8c86c3645d321fdf078a",
        }),
        (
            "src/app/services.py",
            "f23325582482f242869bd088b0fb96dc8b0d106b86a3f81c240d59c88d288b74",
        ): frozenset({
            "23401720ca3f4243a2b85eb03f8ac5e49e205b4f8039a8fdf86d18b9b3e1ea3d",
            "b71cf683a281bfa07de70fe41a101975f066c35179e7607af6d078f10ee35835",
            "4f9c9b7a8266d0017bdef62a1db3809fa7d9bd2b4d7d975e8f134e84fe00c386",
            "11cbcf9097bfaa72f6695fc85afd432a6cae6c71efc78bb4ec1e694e037e21a6",
            "0fbfc4ee3b57b29626cce7ffdbd9b1f9a8e1e3475f098371a398161dabfbe51e",
            "e25bf271beb6da9bc27597d1c2a8b564b36970f4db31ce763f5d3a08523419fc",
            "ea8e18c8a25c3630e389a527a42b238bdd09084e3c89b07ed12ec348eec54caf",
            "02d09d6f6e204183ef67a543222b4e3a4dae993f40041dfb8911397b835be7f7",
            "351721d166d4a1538ed3084e169365ffdd2b8e822b399f82298418493581e963",
            "aab9f26ebe70b458fb706cfeee7f9b6ae76a9bef5303b1d5c150b9773323d20e",
            "0512c0cd141947dbc6f48565b424920393f84fb9fc426dfc2816c504b03f33ce",
            "f61e5a6107d3384e6560ba07c9710f878ed9fef796c2f5ddaac7894200619002",
            "226c38184cda172def0848d5fc627c0a28b93cabed46443e3e663ff72cc5b42c",
            "5bc0a8adf0d5c8a848843c814691fd214717e6a9ac41a1ed762dc81355708602",
            "c17198d67a02c645a175854db5df45a68114a36c3a33392ca811c84f9ec50940",
            "f3def96a4b978fd200dab5ce1628a707a8d30a55c2fd1346887e2c72e05657e3",
            "3b11179b92301e7734cb82ef2f4cc8ba6d251e2ee363cf27d04a0461a0913a7a",
            # Item 3 floating ApplyLens AI chatbot successor.
            "a9211f507cd0294d54040d45df11b846e359f815556306e64bb6785bd1e5ad41",
            # Item 4 planning & tailoring options review successor.
            "c223631f87bd6b358bdd91e732dc54b1fd55568e93ef8c86c3645d321fdf078a",
        }),
            (
                "src/agents/jd_intelligence.py",
                "3711372610b48c5762b1bc27c9cdc8182a9a3d735e5f8bade222b9bac3ef4a00",
            ): "c72224bbc8e64b13c725f9180d227c413fb2fd9a65a97e2e72954f61a8f32b45",
            (
                "src/agents/jd_intelligence.py",
                "c0150f2717581647c22bd084e3223691c1ce25d9b573acff10369def28f37f02",
            ): frozenset({
                "c72224bbc8e64b13c725f9180d227c413fb2fd9a65a97e2e72954f61a8f32b45",
                "b52439495d4de5c513bede1008347d0d00791b1a20f6b8bdd3eae1f726f8cd7b",
            }),
            (
                "src/agents/jd_intelligence.py",
                "c72224bbc8e64b13c725f9180d227c413fb2fd9a65a97e2e72954f61a8f32b45",
            ): "b52439495d4de5c513bede1008347d0d00791b1a20f6b8bdd3eae1f726f8cd7b",
        (
            "src/pipeline/job_filter.py",
            "6931bbb67ec7a5aa68c9ddaf52bb28c56cd007f4ca30de18245fabdc959689b4",
        ): "220bd60e1a8650e24c9b35b426f5b16eadeb0a46cbb30295a710af78d0161901",
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
        ): "261e2b0e40adf1e0e79842f281a06d61aad59f2432fbf8fd4fa8a3d5585b3f3e",
        (
            "src/pipeline/collector.py",
            "261e2b0e40adf1e0e79842f281a06d61aad59f2432fbf8fd4fa8a3d5585b3f3e",
        ): frozenset({
            "7f4d8cc6571f0aa16f722fac43569ddba0a24e518889ca3864a1e46df7fe4cea",
            "33815928d0165154f6ec1f102a6c32b510acf167ac8bc83aa42837e4f310529b",
            "83d14c9634cd22cdee8d31fe1be675aba23ab2b5ad333a56fbd6b23638a07dc1",
            "8bc8673fcf3701f1ff232a760082dfe965c4477bb48dd9ee265a2f3ca4c9f282",
                "f52fdf16c5dea4d4afbe0d36aad41a3b774f0aa91d129844138a895fffe88297",
                "29f51fec60aceb8798cbcecda6dbe41f315e79557b193668d019de4e6f716929",
                "c70367eb9a9cd1da5a2f2a4c5f37c4be3e96dbd0f29ec73bfa32bba5cc580ad4",
                "4a9d20dbaf51da7695c0b5e63ac5b4f6b0e9bd4312ff444c7ce6ad3f4887b65e",
                "daa47b63bbfa06d218b82f50a0ae46e536c9bd89e39543f386c1298008757032",
                    "c3d103420c5613c8717c64ec0a66d1636e00c721ec2a754c22978c9feaab85d4",
                    "02be627dd01e1593215a83fc28c1afe94ba9493dae25d4d4894b067acd1b0455",
                    "153a2f59dd9b8efb8fa958751beb3ace7a933509e2abb61fe2054f0468922139",
                    "a7e1a834fabda1e0dedc35ac5322bc855f65863465449f2f95b95d9e4e785dcb",
                    "2a853270e1005c9a5cc7a42f44a9cd07f2ed352f6b18f99528918973b38bba33",
                    "72d18f217f66cb485e51020b9e793e180dd64f37af285d933e34689235006915",
                    "2a9448e511a5f2076104efde4e89e1142834425ed0606e98e5c42028bf6273eb",
                }),
        (
            "src/tailoring/llm.py",
            "6153c78e5f0eca7c78451f0d234609682e01990041deae7fccb0aa303c653920",
        ): "bea546fda6097184041d574340c484e33e8b94c2247aefe6a15107f6110c2d7a",
        (
            "src/tailoring/llm.py",
            "5e9e858c6b671526eb6839d110ae05aae780d1c165a37a8bde2c1cc5bcecf31d",
        ): "bea546fda6097184041d574340c484e33e8b94c2247aefe6a15107f6110c2d7a",
        (
            "src/pipeline/job_ranker.py",
            "5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54",
        ): "fd387af3c640674de4a998078bc3679747c84ee335d5c275008749f8433a09e5",
        (
            "src/pipeline/collector.py",
            "55a5de9a2147c2aa96f94c7466b81998f69a567bd2da8c920b0c94288ed4ab23",
        ): "7f4d8cc6571f0aa16f722fac43569ddba0a24e518889ca3864a1e46df7fe4cea",
        (
            "src/pipeline/collector.py",
            "7f4d8cc6571f0aa16f722fac43569ddba0a24e518889ca3864a1e46df7fe4cea",
        ): frozenset({
            "a7e1a834fabda1e0dedc35ac5322bc855f65863465449f2f95b95d9e4e785dcb",
            "2a853270e1005c9a5cc7a42f44a9cd07f2ed352f6b18f99528918973b38bba33",
            "72d18f217f66cb485e51020b9e793e180dd64f37af285d933e34689235006915",
            "2a9448e511a5f2076104efde4e89e1142834425ed0606e98e5c42028bf6273eb",
        }),
        (
            "src/pipeline/collector.py",
            "75bda61d0bdc4cf388586d141541be486a9e01b5062f5cc91fe6dc63c46546dc",
        ): "261e2b0e40adf1e0e79842f281a06d61aad59f2432fbf8fd4fa8a3d5585b3f3e",
        (
            "src/pipeline/collector.py",
            "6bc823a688fdd7d270739ea9c1dbc83ef561988cc7f5625b8495bf50c7386689",
        ): "261e2b0e40adf1e0e79842f281a06d61aad59f2432fbf8fd4fa8a3d5585b3f3e",
        (
            "generate_tailoring_suggestions.py",
            "2422452d1c7a54777684b399730d02c11e58ce1ad6ac5658527ad71bb9050f28",
        ): "570d47a62385b736eadbf107e8f28a35aa3818e864f4d950fcb7a6c54e326a3d",
        (
            "generate_tailoring_suggestions.py",
            "58ec07a92d2df1ab1ab72a9029d6fd685576c7c0124532bdeefd1e1fd52ed10c",
        ): "570d47a62385b736eadbf107e8f28a35aa3818e864f4d950fcb7a6c54e326a3d",
        (
            "src/app/static/agentic_review.js",
            "fdbd820a68a356d894ac0b904bd649d511dcf501129d32ed00d34ffc7f927fd0",
        ): frozenset({
            "fdbd820a68a356d894ac0b904bd649d511dcf501129d32ed00d34ffc7f927fd0",
            "b84272b1e74152d0f6e93b8d79636f24179a656d9c2a0ab4b66aa722730ade13",
            # Final approved Item 6 Agentic Review UI revamp.
            "959d9f4cd2c33cee9104695118eff1d83d62e99d495142cc380d9b26c38b415f",
        }),
    }
    repo = Path(root)
    profiles = tuple(compatibility_profiles)
    compatible_paths = (
        merge_allowed(
            *(legacy_guard_allowlist(profile) for profile in profiles),
            legacy_guard_allowlist(
                "phase9_step12_postgres_runtime_repository_integration"
            ),
            legacy_guard_allowlist(
                "phase11_step3_job_prioritization_graph_integration"
            ),
            legacy_guard_allowlist(
                "phase17c_tailoring_generation_llm_closure"
            ),
            legacy_guard_allowlist(
                "phase1_ai_provider_model_routing_hash_maintenance"
            ),
            legacy_guard_allowlist("workday_pagination_freshness"),
        )
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
        compatible_hashes = (
            compatible_hash
            if isinstance(compatible_hash, (set, frozenset, tuple))
            else (compatible_hash,)
        )
        if actual_hash in compatible_hashes and (
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
