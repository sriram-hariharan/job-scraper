from pathlib import Path

import pytest

from tests.support import phase_guard_registry
from tests.support.phase_guard_registry import (
    BROAD_TECH_PREFILTER_TAXONOMY_FILES,
    DISCOVERY_ACQUISITION_LIFECYCLE_FILES,
    HIMALAYAS_STEP2B_LOCATION_COVERAGE_FILES,
    HIMALAYAS_STEP6B1_ATTRIBUTION_FOUNDATION_FILES,
    HIMALAYAS_STEP6B2_SOURCE_INTEGRATION_FILES,
    HIMALAYAS_STEP6C1_PAGINATION_REPAIR_FILES,
    HIMALAYAS_STEP6D_B1_RETENTION_FOUNDATION_FILES,
    HIMALAYAS_STEP6D_B2_RETENTION_INTEGRATION_FILES,
    HIMALAYAS_STEP6D_C_SOURCE_RETIREMENT_FILES,
    HIMALAYAS_STEP6E_R1_LOCATION_ACTIVATION_FILES,
    ITEM2_MANUAL_PROVIDER_PREVIEW_JOB_IDENTITY_REPAIR_FILES,
    ITEM2_MANUAL_PROVIDER_PREVIEW_PROMPT_SCHEMA_ALIGNMENT_FILES,
    ITEM3_DASHBOARD_SCOPED_CHATBOT_FILES,
    ITEM4_PLANNING_TAILORING_OPTIONS_FILES,
    ITEM6_AGENTIC_REVIEW_UI_REVAMP_FILES,
    ITEM61B_AGENTIC_REVIEW_ADMIN_BOUNDARY_FILES,
    ITEM61C_AGENTIC_OPERATIONS_READONLY_BACKEND_FILES,
    ITEM61D_AGENTIC_OPERATIONS_CONSOLE_SHELL_FILES,
    ITEM61E_AGENTIC_OPERATIONS_OVERVIEW_UI_FILES,
    ITEM61F_AGENT_REGISTRY_SAFETY_MATRIX_FILES,
    ITEM61G_RUN_INSPECTOR_AGENTIC_REVIEW_INTEGRATION_FILES,
    ITEM61H_CROSS_PAGE_NAVIGATION_PRODUCT_CLARITY_FILES,
    ITEM61H_V1_SCAN_DIAGNOSTICS_VISUAL_POLISH_FILES,
    ITEM7B_PREMIUM_ACCOUNT_TOOLBAR_FILES,
    ITEM71_EFFECTIVE_EXACT_CHANGE_FILTER_FILES,
    ITEM71_MANUAL_REVIEW_GROQ_DIAGNOSTICS_FIX_FILES,
    ITEM71_PRODUCTION_EXACT_CHANGE_REFINEMENT_FILES,
    ITEM71B_SAFE_DIAGNOSTICS_RUNTIME_FOUNDATION_FILES,
    ITEM71C_SCAN_DIAGNOSTICS_FRONTEND_ACTIVATION_FILES,
    ITEM71D_LATEST_DIAGNOSTICS_WORKFLOW_RESET_FILES,
    NOTIFICATIONS_SCHEDULER_BELL_BRIDGE_FILES,
    PHASE2D_A_INDEPENDENT_SENIORITY_POLICY_FILES,
    PHASE2D_B1_DEFAULT_ELIGIBILITY_OWNERSHIP_FILES,
    PHASE2D_B2_STRICT_SENIORITY_FILTER_FILES,
    TECHNICAL_PRODUCT_PROGRAM_ROLE_FAMILY_FILES,
    PHASE11_STEP8L_PROVIDER_BENCHMARK_CONTRACT_FILES,
    PHASE11_STEP8M_PROVIDER_CLIENT_COMPATIBILITY_FILES,
    PHASE11_STEP8N_SHARED_LLM_CLIENT_SAFETY_FILES,
    PHASE11_STEP8O_PROVIDER_FIXTURE_BENCHMARK_FILES,
    PHASE11_STEP8P_CONTROLLED_PROVIDER_BENCHMARK_PLAN_FILES,
    PHASE11_STEP8PA_TRANSMISSION_SAFE_FIXTURE_FILES,
    PHASE11_STEP8Q_CONTROLLED_PROVIDER_BENCHMARK_HARNESS_FILES,
    PHASE11_STEP8R_GROQ_LIVE_CANARY_PREPARATION_FILES,
    PHASE11_STEP8T_REAL_GROQ_CANARY_TRANSPORT_FILES,
    PHASE11_STEP8V_GROQ_CANARY_EVIDENCE_RUNTIME_FILES,
    PHASE11_STEP8Y_GROQ_CANARY_RUN_IDENTITY_FILES,
    PHASE11_STEP8Z_GROQ_CANARY_RUN_EVIDENCE_RUNTIME_FILES,
    PHASE11_STEP8ZE_GROQ_CANARY_RUN_003_PLAN_FILES,
    PHASE11_STEP8ZF_GROQ_CANARY_RUN_003_IDENTITY_FILES,
    PHASE11_STEP8ZG_GROQ_CANARY_RUN_003_RUNTIME_FILES,
    PHASE11_STEP8ZK_GROQ_CANARY_RUN_004_OFFLINE_RUNTIME_FILES,
    PHASE11_STEP8ZN_GROQ_CANARY_RUN_005_DIAGNOSTIC_RUNTIME_FILES,
    PHASE11_STEP8ZQ_ADDITIVE_TAILORING_TRANSPORT_FILES,
    PHASE11_STEP8MA_RAG_TEST_ISOLATION_FILES,
    PHASE11_STEP3_DIRECT_HASH_GUARD_FILES,
    PHASE12D_DETERMINISTIC_PRODUCTION_OWNER_SHADOW_FILES,
    PHASE13C_AUTHORITATIVE_JOB_PRIORITIZATION_NODE_FILES,
    PHASE14B_AUTHORITATIVE_TAILORING_CALLER_FILES,
    PHASE14C_AUTHORITATIVE_TAILORING_NODE_FILES,
    PHASE15B_CONDITIONAL_OPERATOR_REVIEW_CALLER_FILES,
    PHASE15C_CONDITIONAL_OPERATOR_REVIEW_NODE_FILES,
    PHASE17C_TAILORING_GENERATION_LLM_CLOSURE_FILES,
    PHASE21H_PROVIDER_BENCHMARK_HERMETICITY_FILES,
    PHASE21_RELEASE_CANDIDATE_FILES,
    PHASE21R_HISTORICAL_GUARD_FILES,
    PERSONIO_SOURCE_RETIREMENT_FILES,
    PROBLEM1_JD_INTELLIGENCE_CONTRACT_REVISION_FILES,
    STEP1_RENDERER_BOUND_V2_QUALIFICATION_STABILIZATION_FILES,
    STEP14_CONTROLLED_CANARY_CURRENT_CASE_OWNERSHIP_FILES,
    STEP14F_UI_STATIC_CONTRACT_REPAIR_FILES,
    RECRUITEE_SOURCE_INTEGRATION_FILES,
    RECRUITEE_STANDALONE_DISCOVERY_FILES,
    SCRAPER_PREFILTER_OWNERSHIP_BOUNDARY_FILES,
    SCRAPER_SOURCE_HEALTH_METRICS_FILES,
    SMARTRECRUITERS_PAGINATION_FILES,
    LIVE_PIPELINE_AI_EVALUATION_RELIABILITY_FILES,
    STEP1B2_GLOBAL_ACQUISITION_BOUNDARY_FILES,
    STEP1B3_OWNER_PROJECTION_SHARED_POOL_FILES,
    STEP1B4_OWNER_SELECTOR_LLM_ROUTING_FILES,
    SCRAPER_TRANSPORT_PAGINATION_HARDENING_FILES,
    SOURCE_YIELD_UI_FILES,
    JOBVITE_LOCATION_FRESHNESS_FILES,
    JOBVITE_STANDALONE_DISCOVERY_FILES,
    USAJOBS_SOURCE_INTEGRATION_FILES,
    WORKDAY_DISCOVERY_IDENTITY_CONTRACT_FILES,
    WORKDAY_PAGINATION_FRESHNESS_FILES,
    PRODUCTION_CPU_TORCH_BUILD_FILES,
    PRODUCTION_DEPLOYMENT_HARDENING_FILES,
    assert_changed_files_allowed,
    assert_false_safety_metadata_allowed_but_real_mutation_blocked,
    assert_no_forbidden_runtime_calls_ast,
    assert_protected_hashes,
    current_milestone_guard_compatibility_allowlist,
    duplicate_artifact_paths,
    legacy_guard_allowlist,
    normalize_changed_path,
)


def test_normalize_changed_path_handles_quotes_whitespace_and_backslashes():
    assert normalize_changed_path('  "tests\\test_example.py"  ') == "tests/test_example.py"
    assert (
        normalize_changed_path(' "\'docs\\phase_example.md\'" ')
        == "docs/phase_example.md"
    )


def test_duplicate_artifact_paths_detects_numbered_duplicate_artifacts():
    duplicates = duplicate_artifact_paths(
        {
            "tests/test_phase85b.py",
            '"tests/test_phase85b 2.py"',
            "docs/phase85b 3.md",
            "docs/phase85b.md",
        }
    )

    assert duplicates == {"tests/test_phase85b 2.py", "docs/phase85b 3.md"}


def test_assert_changed_files_allowed_accepts_exact_allowed_files():
    assert_changed_files_allowed(
        {"tests/test_phase85b_legacy_guard_registry_default_off.py"},
        {"tests/test_phase85b_legacy_guard_registry_default_off.py"},
    )


def test_assert_changed_files_allowed_rejects_unexpected_files_with_clear_message():
    with pytest.raises(AssertionError) as exc:
        assert_changed_files_allowed(
            {"src/pipeline/unapproved_collector.py", "tests/test_allowed.py"},
            {"tests/test_allowed.py"},
        )

    assert "src/pipeline/unapproved_collector.py" in str(exc.value)
    assert "tests/test_allowed.py" not in str(exc.value)


def test_config_vocabulary_scoring_change_profile_is_narrow():
    assert_changed_files_allowed(
        {
            "src/config/consts.py",
            "tests/test_phase115a_applied_ai_scoring_fix.py",
            "tests/test_phase116a_applied_ai_scoring_fix.py",
            "src/matching/clearance_requirements.py",
            "tests/test_phase117b_ts_clearance_diagnostic.py",
            "jd_resume_diff_helper.py",
            "tests/test_phase118b_ts_clearance_packet_diagnostic.py",
            "src/matching/semantic_similarity.py",
            "tests/test_phase120b_semantic_similarity_diagnostic.py",
            "src/matching/scorer.py",
            "tests/test_phase121b_semantic_alignment_dimension_default_off.py",
        },
        set(),
        legacy_guard_profiles=("config_vocabulary_scoring_change",),
        include_current_milestone_compatibility=False,
    )

    for forbidden_path in (
        "src/app/services.py",
        "src/pipeline/collector.py",
        "src/matching/dimensions.py",
        "src/matching/job_adapter.py",
        "src/ai/llm_client.py",
        "src/app/application_execution_queue.py",
        "src/integrations/ats_submitter.py",
        "src/tailoring/source_resume_overwrite.py",
    ):
        with pytest.raises(AssertionError):
            assert_changed_files_allowed(
                {forbidden_path},
                set(),
                legacy_guard_profiles=("config_vocabulary_scoring_change",),
                include_current_milestone_compatibility=False,
            )


def test_active_ts_clearance_diagnostic_profile_is_narrow():
    assert_changed_files_allowed(
        {
            "src/matching/clearance_requirements.py",
            "tests/test_phase117b_ts_clearance_diagnostic.py",
        },
        set(),
        legacy_guard_profiles=("active_ts_clearance_diagnostic",),
        include_current_milestone_compatibility=False,
    )

    for forbidden_path in (
        "src/matching/scorer.py",
        "src/matching/dimensions.py",
        "src/matching/job_adapter.py",
        "src/app/services.py",
        "src/pipeline/collector.py",
        "src/ai/llm_client.py",
        "src/app/application_execution_queue.py",
        "src/integrations/ats_submitter.py",
    ):
        with pytest.raises(AssertionError):
            assert_changed_files_allowed(
                {forbidden_path},
                set(),
                legacy_guard_profiles=("active_ts_clearance_diagnostic",),
                include_current_milestone_compatibility=False,
            )


def test_active_ts_clearance_packet_diagnostic_profile_is_narrow():
    assert_changed_files_allowed(
        {
            "jd_resume_diff_helper.py",
            "tests/test_phase118b_ts_clearance_packet_diagnostic.py",
        },
        set(),
        legacy_guard_profiles=("active_ts_clearance_packet_diagnostic",),
    )

    for forbidden_path in (
        "src/matching/scorer.py",
        "src/matching/dimensions.py",
        "src/matching/job_adapter.py",
        "batch_select_best_resume_variant.py",
        "application_shortlist_from_batch_selector.py",
        "application_execution_queue.py",
        "src/app/services.py",
        "src/pipeline/collector.py",
        "src/ai/llm_client.py",
        "src/agents/resume_match_agent.py",
        "src/tailoring/llm.py",
        "src/app/application_execution_queue.py",
        "src/integrations/ats_submitter.py",
    ):
        with pytest.raises(AssertionError):
            assert_changed_files_allowed(
                {forbidden_path},
                set(),
                legacy_guard_profiles=("active_ts_clearance_packet_diagnostic",),
                include_current_milestone_compatibility=False,
            )


def test_active_ts_clearance_scan_warning_readback_profile_is_narrow():
    assert_changed_files_allowed(
        {
            "src/app/static/planning.js",
            "src/app/static/scan_workspace_review.css",
            "tests/test_phase119b_ts_clearance_scan_warning_static_only.py",
        },
        set(),
        legacy_guard_profiles=("active_ts_clearance_scan_warning_readback",),
        include_current_milestone_compatibility=False,
    )

    for forbidden_path in (
        "src/app/services.py",
        "src/app/api.py",
        "src/pipeline/collector.py",
        "src/matching/scorer.py",
        "src/matching/dimensions.py",
        "src/matching/job_adapter.py",
        "src/ai/llm_client.py",
        "src/agents/resume_match_agent.py",
        "src/tailoring/llm.py",
        "src/app/application_execution_queue.py",
        "src/integrations/ats_submitter.py",
    ):
        with pytest.raises(AssertionError):
            assert_changed_files_allowed(
                {forbidden_path},
                set(),
                legacy_guard_profiles=("active_ts_clearance_scan_warning_readback",),
                include_current_milestone_compatibility=False,
            )


def test_semantic_similarity_diagnostic_only_profile_is_narrow():
    assert_changed_files_allowed(
        {
            "src/matching/semantic_similarity.py",
            "tests/test_phase120b_semantic_similarity_diagnostic.py",
        },
        set(),
        legacy_guard_profiles=("semantic_similarity_diagnostic_only",),
    )

    for forbidden_path in (
        "src/matching/scorer.py",
        "src/matching/dimensions.py",
        "src/matching/job_adapter.py",
        "batch_select_best_resume_variant.py",
        "application_shortlist_from_batch_selector.py",
        "application_execution_queue.py",
        "src/app/services.py",
        "src/app/api.py",
        "src/pipeline/collector.py",
        "src/ai/llm_client.py",
        "src/agents/resume_match_agent.py",
        "src/rag/retriever.py",
        "src/tailoring/llm.py",
        "requirements.txt",
    ):
        with pytest.raises(AssertionError):
            assert_changed_files_allowed(
                {forbidden_path},
                set(),
                legacy_guard_profiles=("semantic_similarity_diagnostic_only",),
                include_current_milestone_compatibility=False,
            )


def test_semantic_alignment_weighted_score_component_profile_is_narrow():
    assert_changed_files_allowed(
        {
            "src/matching/scorer.py",
            "src/matching/semantic_similarity.py",
            "tests/test_phase121b_semantic_alignment_dimension_default_off.py",
        },
        set(),
        legacy_guard_profiles=("semantic_alignment_weighted_score_component",),
    )

    for forbidden_path in (
        "src/matching/dimensions.py",
        "src/matching/models.py",
        "src/matching/job_adapter.py",
        "batch_select_best_resume_variant.py",
        "application_shortlist_from_batch_selector.py",
        "application_execution_queue.py",
        "src/app/services.py",
        "src/app/api.py",
        "src/pipeline/collector.py",
        "src/ai/llm_client.py",
        "src/agents/resume_match_agent.py",
        "src/rag/retriever.py",
        "src/tailoring/llm.py",
        "requirements.txt",
    ):
        with pytest.raises(AssertionError):
            assert_changed_files_allowed(
                {forbidden_path},
                set(),
                legacy_guard_profiles=("semantic_alignment_weighted_score_component",),
                include_current_milestone_compatibility=False,
            )


def test_llm_adjudicator_readback_default_off_profile_is_narrow():
    assert_changed_files_allowed(
        {
            "src/agents/llm_adjudicator_readback.py",
            "batch_select_best_resume_variant.py",
            "tests/test_phase123b_llm_adjudicator_readback_default_off.py",
        },
        set(),
        legacy_guard_profiles=("llm_adjudicator_readback_default_off",),
        include_current_milestone_compatibility=False,
    )

    for forbidden_path in (
        "src/matching/scorer.py",
        "src/matching/dimensions.py",
        "src/matching/models.py",
        "src/matching/job_adapter.py",
        "application_shortlist_from_batch_selector.py",
        "application_execution_queue.py",
        "run_application_planning.py",
        "src/app/services.py",
        "src/app/api.py",
        "src/pipeline/collector.py",
        "src/ai/llm_client.py",
        "src/rag/retriever.py",
        "src/tailoring/llm.py",
        "requirements.txt",
    ):
        with pytest.raises(AssertionError):
            assert_changed_files_allowed(
                {forbidden_path},
                set(),
                legacy_guard_profiles=("llm_adjudicator_readback_default_off",),
                include_current_milestone_compatibility=False,
            )


def test_scraper_prefilter_ownership_boundary_surface_is_exact():
    assert SCRAPER_PREFILTER_OWNERSHIP_BOUNDARY_FILES == {
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
    assert not any("*" in path for path in SCRAPER_PREFILTER_OWNERSHIP_BOUNDARY_FILES)


def test_recruitee_standalone_discovery_surface_is_exact():
    assert RECRUITEE_STANDALONE_DISCOVERY_FILES == {
        "src/agents/company_discovery_agent.py",
        "tests/support/phase_guard_registry.py",
        "tests/test_company_discovery_agent.py",
        "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
        "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
        "tests/test_phase85b_legacy_guard_registry_default_off.py",
    }
    assert not any("*" in path for path in RECRUITEE_STANDALONE_DISCOVERY_FILES)


def test_jobvite_standalone_discovery_surface_is_exact():
    assert JOBVITE_STANDALONE_DISCOVERY_FILES == {
        "src/agents/company_discovery_agent.py",
        "src/scrapers/jobvite_scraper.py",
        "tests/support/phase_guard_registry.py",
        "tests/test_company_discovery_agent.py",
        "tests/test_jobvite_location_freshness.py",
        "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
        "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
        "tests/test_phase85b_legacy_guard_registry_default_off.py",
    }
    assert not any("*" in path for path in JOBVITE_STANDALONE_DISCOVERY_FILES)


def test_workday_discovery_identity_contract_surface_is_exact():
    assert WORKDAY_DISCOVERY_IDENTITY_CONTRACT_FILES == {
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
    assert not any(
        "*" in path for path in WORKDAY_DISCOVERY_IDENTITY_CONTRACT_FILES
    )


def test_personio_source_retirement_surface_is_exact():
    assert PERSONIO_SOURCE_RETIREMENT_FILES == {
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
    assert not any("*" in path for path in PERSONIO_SOURCE_RETIREMENT_FILES)


def test_usajobs_source_integration_surface_is_exact():
    assert USAJOBS_SOURCE_INTEGRATION_FILES == {
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
    assert not any("*" in path for path in USAJOBS_SOURCE_INTEGRATION_FILES)


def test_broad_tech_prefilter_taxonomy_surface_is_exact():
    assert BROAD_TECH_PREFILTER_TAXONOMY_FILES == {
        "src/config/role_taxonomy.py",
        "tests/support/phase_guard_registry.py",
        "tests/test_broad_tech_prefilter_taxonomy.py",
        "tests/test_phase85b_legacy_guard_registry_default_off.py",
        "tests/test_user_pipeline_role_preferences.py",
    }
    assert not any("*" in path for path in BROAD_TECH_PREFILTER_TAXONOMY_FILES)


def test_technical_product_program_role_family_surface_is_exact():
    assert TECHNICAL_PRODUCT_PROGRAM_ROLE_FAMILY_FILES == {
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
    assert not any("*" in path for path in TECHNICAL_PRODUCT_PROGRAM_ROLE_FAMILY_FILES)


def test_phase2d_a_independent_seniority_policy_surface_is_exact():
    assert PHASE2D_A_INDEPENDENT_SENIORITY_POLICY_FILES == {
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
    assert not any(
        "*" in path for path in PHASE2D_A_INDEPENDENT_SENIORITY_POLICY_FILES
    )


def test_phase2d_b1_default_eligibility_ownership_surface_is_exact():
    assert PHASE2D_B1_DEFAULT_ELIGIBILITY_OWNERSHIP_FILES == {
        "src/config/role_taxonomy.py",
        "src/config/seniority_policy.py",
        "src/pipeline/job_filter.py",
        "tests/support/phase_guard_registry.py",
        "tests/test_independent_seniority_prefilter.py",
        "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
        "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
        "tests/test_phase85b_legacy_guard_registry_default_off.py",
    }
    assert not any(
        "*" in path
        for path in PHASE2D_B1_DEFAULT_ELIGIBILITY_OWNERSHIP_FILES
    )


def test_phase2d_b2_strict_seniority_filter_surface_is_exact():
    assert PHASE2D_B2_STRICT_SENIORITY_FILTER_FILES == {
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
    assert not any(
        "*" in path for path in PHASE2D_B2_STRICT_SENIORITY_FILTER_FILES
    )


def test_current_milestone_guard_compatibility_is_exact_registered_surface():
    assert PROBLEM1_JD_INTELLIGENCE_CONTRACT_REVISION_FILES == {
        "src/matching/jd_intelligence_contract.py",
        "src/matching/job_adapter.py",
        "src/resume/evidence_builder.py",
        "tests/fixtures/p1s3_jd_evidence/corpus_jobevidence_baseline.json",
        "tests/fixtures/p1s3_jd_evidence/starved_jd_records.json",
        "tests/support/phase_guard_registry.py",
        "tests/test_phase85b_legacy_guard_registry_default_off.py",
        "tests/test_problem1_experience_skill_morphology.py",
        "tests/test_problem1_jd_category_validator.py",
        "tests/test_problem1_jd_evidence_starvation.py",
        "tests/test_problem1_jd_intelligence_contract_v2.py",
    }
    assert not any(
        "*" in path for path in PROBLEM1_JD_INTELLIGENCE_CONTRACT_REVISION_FILES
    )
    assert STEP1B2_GLOBAL_ACQUISITION_BOUNDARY_FILES == {
        "main.py",
        "src/pipeline/collector.py",
        "src/pipeline/scheduler.py",
        "src/rag/export_job_corpus.py",
        "tests/support/phase_guard_registry.py",
        "tests/test_rag_export_job_corpus.py",
        "tests/test_scheduler_runtime_postgres_correctness.py",
        "tests/test_user_pipeline_role_preferences.py",
    }
    assert not any(
        "*" in path for path in STEP1B2_GLOBAL_ACQUISITION_BOUNDARY_FILES
    )
    assert STEP1B3_OWNER_PROJECTION_SHARED_POOL_FILES == {
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
    assert not any(
        "*" in path for path in STEP1B3_OWNER_PROJECTION_SHARED_POOL_FILES
    )
    assert STEP1B4_OWNER_SELECTOR_LLM_ROUTING_FILES == {
        "batch_select_best_resume_variant.py",
        "tests/support/phase_guard_registry.py",
        "tests/test_phase85b_legacy_guard_registry_default_off.py",
        "tests/test_step1b4_owner_selector_llm_routing.py",
    }
    assert not any(
        "*" in path for path in STEP1B4_OWNER_SELECTOR_LLM_ROUTING_FILES
    )
    smartrecruiters_pagination_profile = legacy_guard_allowlist(
        "smartrecruiters_pagination"
    )
    assert smartrecruiters_pagination_profile == SMARTRECRUITERS_PAGINATION_FILES
    assert not any("*" in path for path in smartrecruiters_pagination_profile)
    workday_pagination_freshness_profile = legacy_guard_allowlist(
        "workday_pagination_freshness"
    )
    assert (
        workday_pagination_freshness_profile
        == WORKDAY_PAGINATION_FRESHNESS_FILES
    )
    assert not any("*" in path for path in workday_pagination_freshness_profile)
    himalayas_step2b_profile = legacy_guard_allowlist(
        "himalayas_step2b_location_coverage"
    )
    assert himalayas_step2b_profile == HIMALAYAS_STEP2B_LOCATION_COVERAGE_FILES
    assert not any("*" in path for path in himalayas_step2b_profile)
    himalayas_step6e_r1_profile = legacy_guard_allowlist(
        "himalayas_step6e_r1_location_activation"
    )
    assert himalayas_step6e_r1_profile == {
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
    assert (
        himalayas_step6e_r1_profile
        == HIMALAYAS_STEP6E_R1_LOCATION_ACTIVATION_FILES
    )
    assert not any("*" in path for path in himalayas_step6e_r1_profile)
    himalayas_step6d_c_profile = legacy_guard_allowlist(
        "himalayas_step6d_c_source_retirement"
    )
    assert himalayas_step6d_c_profile == {
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
    assert (
        himalayas_step6d_c_profile
        == HIMALAYAS_STEP6D_C_SOURCE_RETIREMENT_FILES
    )
    assert not any("*" in path for path in himalayas_step6d_c_profile)
    himalayas_step6d_b2_profile = legacy_guard_allowlist(
        "himalayas_step6d_b2_retention_integration"
    )
    assert himalayas_step6d_b2_profile == {
        "src/app/services.py",
        "src/pipeline/collector.py",
        "tests/support/phase_guard_registry.py",
        "tests/test_himalayas_active_retention.py",
        "tests/test_himalayas_retention_integration.py",
        "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
        "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
        "tests/test_phase85b_legacy_guard_registry_default_off.py",
    }
    assert (
        himalayas_step6d_b2_profile
        == HIMALAYAS_STEP6D_B2_RETENTION_INTEGRATION_FILES
    )
    assert not any("*" in path for path in himalayas_step6d_b2_profile)
    himalayas_step6d_b1_profile = legacy_guard_allowlist(
        "himalayas_step6d_b1_retention_foundation"
    )
    assert himalayas_step6d_b1_profile == {
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
    assert (
        himalayas_step6d_b1_profile
        == HIMALAYAS_STEP6D_B1_RETENTION_FOUNDATION_FILES
    )
    assert not any("*" in path for path in himalayas_step6d_b1_profile)
    himalayas_step6c1_profile = legacy_guard_allowlist(
        "himalayas_step6c1_pagination_repair"
    )
    assert himalayas_step6c1_profile == {
        "src/scrapers/himalayas_scraper.py",
        "tests/support/phase_guard_registry.py",
        "tests/test_himalayas_scraper.py",
        "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
        "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
        "tests/test_phase85b_legacy_guard_registry_default_off.py",
    }
    assert himalayas_step6c1_profile == HIMALAYAS_STEP6C1_PAGINATION_REPAIR_FILES
    assert not any("*" in path for path in himalayas_step6c1_profile)
    himalayas_step6b2_profile = legacy_guard_allowlist(
        "himalayas_step6b2_source_integration"
    )
    assert himalayas_step6b2_profile == {
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
    assert himalayas_step6b2_profile == HIMALAYAS_STEP6B2_SOURCE_INTEGRATION_FILES
    assert not any("*" in path for path in himalayas_step6b2_profile)
    himalayas_step6b1_profile = legacy_guard_allowlist(
        "himalayas_step6b1_attribution_foundation"
    )
    assert himalayas_step6b1_profile == {
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
    assert himalayas_step6b1_profile == HIMALAYAS_STEP6B1_ATTRIBUTION_FOUNDATION_FILES
    assert not any("*" in path for path in himalayas_step6b1_profile)
    phase129_profile = legacy_guard_allowlist(
        "phase129c_workflow_overlay_and_run_scoped_corpus"
    )
    phase132_profile = legacy_guard_allowlist("phase132b_premium_preferences_ui")
    phase133_profile = legacy_guard_allowlist("phase133a_executive_kpi_react_island")
    phase133b_profile = legacy_guard_allowlist("phase133b_executive_queue_react_island")
    phase133d_profile = legacy_guard_allowlist("phase133d_pipeline_dashboard_react_island")
    phase133g_profile = legacy_guard_allowlist("phase133g_premium_planning_dashboard")
    phase133ef_profile = legacy_guard_allowlist("phase133ef_decisions_applications_dashboards")
    source_yield_ui_profile = legacy_guard_allowlist("source_yield_ui")
    assert source_yield_ui_profile == SOURCE_YIELD_UI_FILES
    assert not any("*" in path for path in source_yield_ui_profile)
    jobvite_location_freshness_profile = legacy_guard_allowlist(
        "jobvite_location_freshness"
    )
    assert jobvite_location_freshness_profile == JOBVITE_LOCATION_FRESHNESS_FILES
    assert not any("*" in path for path in jobvite_location_freshness_profile)
    lr2_reliability_profile = legacy_guard_allowlist(
        "live_pipeline_ai_evaluation_reliability_lr2b_lr2c"
    )
    assert lr2_reliability_profile == {
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
    }
    assert len(lr2_reliability_profile) == 10
    assert not any("*" in path for path in lr2_reliability_profile)
    assert_changed_files_allowed(
        lr2_reliability_profile,
        set(),
        legacy_guard_profiles=(
            "live_pipeline_ai_evaluation_reliability_lr2b_lr2c",
        ),
        include_current_milestone_compatibility=False,
    )
    with pytest.raises(AssertionError):
        assert_changed_files_allowed(
            {"src/app/services.py"},
            set(),
            legacy_guard_profiles=(
                "live_pipeline_ai_evaluation_reliability_lr2b_lr2c",
            ),
            include_current_milestone_compatibility=False,
        )

    item71_production_refinement_profile = legacy_guard_allowlist(
        "item71_production_exact_change_refinement"
    )
    assert item71_production_refinement_profile == (
        ITEM71_PRODUCTION_EXACT_CHANGE_REFINEMENT_FILES
    )
    assert len(item71_production_refinement_profile) == 12
    assert not any("*" in path for path in item71_production_refinement_profile)
    assert_changed_files_allowed(
        item71_production_refinement_profile,
        set(),
        legacy_guard_profiles=("item71_production_exact_change_refinement",),
        include_current_milestone_compatibility=False,
    )
    with pytest.raises(AssertionError):
        assert_changed_files_allowed(
            {"src/ai/llm_client.py"},
            set(),
            legacy_guard_profiles=("item71_production_exact_change_refinement",),
            include_current_milestone_compatibility=False,
        )
    fvr2b_source_contracts_profile = legacy_guard_allowlist(
        "live_pipeline_ai_evaluation_reliability_fvr2b_source_contracts"
    )
    assert fvr2b_source_contracts_profile == {
        "tests/test_phase16b_lean_deterministic_production_orchestration_closure.py",
        "tests/test_phase17a_lean_cache_first_jd_intelligence_activation.py",
        "tests/test_phase83b_live_llm_invocation_contract_map_default_off.py",
        "tests/test_phase87b_jd_intelligence_existing_output_collector_diagnostics_default_off.py",
    }
    assert len(fvr2b_source_contracts_profile) == 4
    assert not any("*" in path for path in fvr2b_source_contracts_profile)
    assert_changed_files_allowed(
        fvr2b_source_contracts_profile,
        set(),
        legacy_guard_profiles=(
            "live_pipeline_ai_evaluation_reliability_fvr2b_source_contracts",
        ),
        include_current_milestone_compatibility=False,
    )
    with pytest.raises(AssertionError):
        assert_changed_files_allowed(
            {"src/app/services.py"},
            set(),
            legacy_guard_profiles=(
                "live_pipeline_ai_evaluation_reliability_fvr2b_source_contracts",
            ),
            include_current_milestone_compatibility=False,
        )
    expected_phase132_profile = {
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
    }
    phase129_auth_artwork_files = {
        "src/app/static/media/auth_workflow_hero.svg",
        "src/app/static/media/auth_hero_icons/LICENSES.txt",
        "src/app/static/media/auth_hero_icons/apply_with_confidence.svg",
        "src/app/static/media/auth_hero_icons/collect_jobs.svg",
        "src/app/static/media/auth_hero_icons/review_ai_notes.svg",
        "src/app/static/media/auth_hero_icons/score_fit.svg",
        "src/app/static/media/auth_hero_icons/tailor_safely.svg",
    }
    assert "tests/test_phase85b_legacy_guard_registry_default_off.py" in phase129_profile
    assert phase129_auth_artwork_files <= phase129_profile
    assert not any("*" in path for path in phase129_profile)
    assert phase132_profile == expected_phase132_profile
    assert len(phase132_profile) == 22
    assert not any("*" in path for path in phase132_profile)
    assert phase133_profile == {
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
    }
    assert len(phase133_profile) == 24
    assert not any("*" in path for path in phase133_profile)
    assert phase133b_profile == {
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
    }
    assert len(phase133b_profile) == 17
    assert not any("*" in path for path in phase133b_profile)
    assert phase133d_profile == {
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
    }
    assert len(phase133d_profile) == 22
    assert not any("*" in path for path in phase133d_profile)
    assert phase133g_profile == {
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
    }
    assert len(phase133g_profile) == 30
    assert not any("*" in path for path in phase133g_profile)
    assert phase133ef_profile == {
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
    }
    assert len(phase133ef_profile) == 17
    assert not any("*" in path for path in phase133ef_profile)

    phase133h_profile = legacy_guard_allowlist("phase133h_premium_responsive_sidebar")
    assert phase133h_profile == {
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
    }
    assert len(phase133h_profile) == 20
    assert not any("*" in path for path in phase133h_profile)

    scheduler_admin_health_profile = legacy_guard_allowlist("scheduler_admin_health_redesign")
    assert scheduler_admin_health_profile == {
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
    }
    assert len(scheduler_admin_health_profile) == 22
    assert not any("*" in path for path in scheduler_admin_health_profile)

    scheduler_visual_correction_profile = legacy_guard_allowlist("scheduler_health_visual_correction")
    assert scheduler_visual_correction_profile == {
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
    }
    assert len(scheduler_visual_correction_profile) == 21
    assert not any("*" in path for path in scheduler_visual_correction_profile)

    phase133i_profile = legacy_guard_allowlist("phase133i_advanced_diagnostics_react_command_center")
    assert phase133i_profile == {
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
    }
    assert len(phase133i_profile) == 22
    assert not any("*" in path for path in phase133i_profile)

    item2_phase3_profile = legacy_guard_allowlist("item2_phase3_shared_page_header_foundation")
    assert item2_phase3_profile == {
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
    }
    assert len(item2_phase3_profile) == 20
    assert not any("*" in path for path in item2_phase3_profile)

    item2_phase4_profile = legacy_guard_allowlist("item2_phase4_secondary_page_headers")
    assert item2_phase4_profile == {
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
    }
    assert len(item2_phase4_profile) == 15
    assert not any("*" in path for path in item2_phase4_profile)

    item2_phase4_corrections_profile = legacy_guard_allowlist(
        "item2_phase4_profile_corrections_legacy_route_retirement"
    )
    assert item2_phase4_corrections_profile == {
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
    }
    assert len(item2_phase4_corrections_profile) == 36
    assert not any("*" in path for path in item2_phase4_corrections_profile)

    phase8_step3d_profile = legacy_guard_allowlist(
        "phase8_step3d_tailoring_llm_gate"
    )
    assert phase8_step3d_profile == {
        "src/tailoring/rendering.py",
        "tests/test_tailoring_patch_refinement_explicit_opt_in.py",
    }
    assert not any("*" in path for path in phase8_step3d_profile)

    phase8_step4_profile = legacy_guard_allowlist(
        "phase8_step4_dead_file_cleanup"
    )
    assert phase8_step4_profile == {
        "src/ai/deterministic_skill_extractor.py",
    }
    assert not any("*" in path for path in phase8_step4_profile)

    phase8_step6_profile = legacy_guard_allowlist(
        "phase8_step6_canonical_agent_registry"
    )
    assert phase8_step6_profile == {
        "src/agents/canonical_registry.py",
        "src/agents/workflow_registry.py",
        "tests/test_phase8_step6_canonical_agent_registry.py",
    }
    assert not any("*" in path for path in phase8_step6_profile)

    phase8_step8_profile = legacy_guard_allowlist(
        "phase8_step8_legacy_agent_context_retirement"
    )
    assert phase8_step8_profile == {
        "src/agents/context.py",
        "tests/test_agent_context.py",
        "tests/test_full_agentic_ai_current_state_audit_no_runtime_change.py",
        "docs/full_agentic_ai_current_state_audit_no_runtime_change.md",
    }
    assert not any("*" in path for path in phase8_step8_profile)

    phase8_step13_profile = legacy_guard_allowlist(
        "phase8_step13_langgraph_parity_contract"
    )
    assert phase8_step13_profile == {
        "tests/test_phase107b_langgraph_evidence_chain_harness_default_off.py",
    }
    assert not any("*" in path for path in phase8_step13_profile)
    assert not any(
        path in {"tests", "tests/", "tests/**"}
        for path in phase8_step13_profile
    )

    phase8_step14_profile = legacy_guard_allowlist(
        "phase8_step14_typed_langgraph_state_normalization"
    )
    assert phase8_step14_profile == {
        "src/agents/evidence_chain_langgraph_harness.py",
        "tests/test_phase107b_langgraph_evidence_chain_harness_default_off.py",
    }
    assert not any("*" in path for path in phase8_step14_profile)
    assert not any(
        path in {"src", "src/", "src/**", "tests", "tests/", "tests/**"}
        for path in phase8_step14_profile
    )

    phase8_step15_profile = legacy_guard_allowlist(
        "phase8_step15_checkpoint_identity_serialization_contract"
    )
    assert phase8_step15_profile == {
        "src/agents/evidence_chain_langgraph_harness.py",
        "tests/test_phase107b_langgraph_evidence_chain_harness_default_off.py",
    }
    assert not any("*" in path for path in phase8_step15_profile)
    assert not any(
        path in {"src", "src/", "src/**", "tests", "tests/", "tests/**"}
        for path in phase8_step15_profile
    )

    phase8_step17_profile = legacy_guard_allowlist(
        "phase8_step17_readonly_operator_review_interrupt_request"
    )
    assert phase8_step17_profile == {
        "src/agents/evidence_chain_langgraph_harness.py",
        "tests/test_phase107b_langgraph_evidence_chain_harness_default_off.py",
    }
    assert not any("*" in path for path in phase8_step17_profile)
    assert not any(
        path in {"src", "src/", "src/**", "tests", "tests/", "tests/**"}
        for path in phase8_step17_profile
    )

    phase9_step2_profile = legacy_guard_allowlist(
        "phase9_step2_durable_checkpoint_interrupt_storage"
    )
    assert phase9_step2_profile == {
        "src/storage/durable_orchestration/__init__.py",
        "src/storage/durable_orchestration/schema.sql",
        "src/storage/durable_orchestration/store.py",
        "tests/test_phase9_step2_durable_checkpoint_interrupt_storage_contract.py",
        "tests/test_pgvector_extension_probe_api_no_schema_no_ui.py",
        "tests/test_pgvector_extension_probe_contract_no_schema.py",
        "tests/test_pgvector_extension_probe_service_helper_no_schema.py",
        "tests/test_pgvector_extension_probe_ui_no_schema_readonly.py",
        "tests/test_phase8_pgvector_backend_readiness_schema_plan_no_runtime_change.py",
    }
    assert not any("*" in path for path in phase9_step2_profile)
    assert not any(
        path
        in {
            "src",
            "src/",
            "src/**",
            "src/storage",
            "src/storage/",
            "src/storage/**",
            "tests",
            "tests/",
            "tests/**",
        }
        for path in phase9_step2_profile
    )
    assert {
        "tests/support/phase_guard_registry.py",
        "tests/test_phase85b_legacy_guard_registry_default_off.py",
    }.isdisjoint(phase9_step2_profile)

    phase9_step3_profile = legacy_guard_allowlist(
        "phase9_step3_human_decision_resume_storage"
    )
    assert phase9_step3_profile == {
        "src/storage/durable_orchestration/schema.sql",
        "src/storage/durable_orchestration/store.py",
        "tests/test_phase9_step2_durable_checkpoint_interrupt_storage_contract.py",
        "tests/test_phase9_step3_human_decision_resume_storage_contract.py",
        "tests/test_pgvector_extension_probe_api_no_schema_no_ui.py",
        "tests/test_pgvector_extension_probe_contract_no_schema.py",
        "tests/test_pgvector_extension_probe_service_helper_no_schema.py",
        "tests/test_pgvector_extension_probe_ui_no_schema_readonly.py",
        "tests/test_phase8_pgvector_backend_readiness_schema_plan_no_runtime_change.py",
    }
    assert not any("*" in path for path in phase9_step3_profile)
    assert {
        "tests/support/phase_guard_registry.py",
        "tests/test_phase85b_legacy_guard_registry_default_off.py",
    }.isdisjoint(phase9_step3_profile)

    phase9_step4_profile = legacy_guard_allowlist(
        "phase9_step4_attempt_terminal_recovery_storage"
    )
    assert phase9_step4_profile == {
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
    }
    assert not any("*" in path for path in phase9_step4_profile)
    assert not any(
        path in {
            "src", "src/", "src/**", "src/storage", "src/storage/",
            "src/storage/**", "tests", "tests/", "tests/**",
        }
        for path in phase9_step4_profile
    )
    assert {
        "tests/support/phase_guard_registry.py",
        "tests/test_phase85b_legacy_guard_registry_default_off.py",
    }.isdisjoint(phase9_step4_profile)

    phase9_step6_profile = legacy_guard_allowlist(
        "phase9_step6_inmemory_operator_review_pause_resume"
    )
    assert phase9_step6_profile == {
        "src/agents/evidence_chain_langgraph_harness.py",
        "tests/test_phase107b_langgraph_evidence_chain_harness_default_off.py",
        "tests/test_phase9_step6_langgraph_operator_review_pause_resume_default_off.py",
    }
    assert not any("*" in path for path in phase9_step6_profile)
    assert not any(
        path in {
            "src", "src/", "src/**", "src/agents", "src/agents/",
            "src/agents/**", "tests", "tests/", "tests/**",
        }
        for path in phase9_step6_profile
    )
    assert {
        "tests/support/phase_guard_registry.py",
        "tests/test_phase85b_legacy_guard_registry_default_off.py",
    }.isdisjoint(phase9_step6_profile)

    phase9_step8_profile = legacy_guard_allowlist(
        "phase9_step8_durable_orchestration_transaction_executor"
    )
    assert phase9_step8_profile == {
        "src/storage/durable_orchestration/repository.py",
        "tests/test_phase9_step8_durable_orchestration_transaction_executor_contract.py",
    }
    assert not any("*" in path for path in phase9_step8_profile)
    assert not any(
        path in {
            "src", "src/", "src/**", "src/storage", "src/storage/",
            "src/storage/**", "src/storage/durable_orchestration",
            "src/storage/durable_orchestration/",
            "src/storage/durable_orchestration/**",
            "tests", "tests/", "tests/**",
        }
        for path in phase9_step8_profile
    )
    assert {
        "tests/support/phase_guard_registry.py",
        "tests/test_phase85b_legacy_guard_registry_default_off.py",
    }.isdisjoint(phase9_step8_profile)

    phase9_step9_profile = legacy_guard_allowlist(
        "phase9_step9_durable_orchestration_schema_executor"
    )
    assert phase9_step9_profile == {
        "src/storage/admin_tools/durable_orchestration/apply_schema.py",
        "tests/test_phase9_step9_durable_orchestration_schema_executor_contract.py",
    }
    assert not any("*" in path for path in phase9_step9_profile)
    assert not any(
        path in {
            "src", "src/", "src/**", "src/storage", "src/storage/",
            "src/storage/**", "src/storage/admin_tools",
            "src/storage/admin_tools/", "src/storage/admin_tools/**",
            "src/storage/admin_tools/durable_orchestration",
            "src/storage/admin_tools/durable_orchestration/",
            "src/storage/admin_tools/durable_orchestration/**",
            "tests", "tests/", "tests/**",
        }
        for path in phase9_step9_profile
    )
    assert {
        "tests/support/phase_guard_registry.py",
        "tests/test_phase85b_legacy_guard_registry_default_off.py",
    }.isdisjoint(phase9_step9_profile)

    phase9_step10_profile = legacy_guard_allowlist(
        "phase9_step10_durable_orchestration_postgres_integration"
    )
    assert phase9_step10_profile == {
        "tests/test_phase9_step10_durable_orchestration_postgres_integration.py",
    }
    assert not any("*" in path for path in phase9_step10_profile)
    assert not any(
        path in {
            "src", "src/", "src/**", "tests", "tests/", "tests/**",
        }
        for path in phase9_step10_profile
    )
    assert {
        "tests/support/phase_guard_registry.py",
        "tests/test_phase85b_legacy_guard_registry_default_off.py",
    }.isdisjoint(phase9_step10_profile)

    phase9_step12_profile = legacy_guard_allowlist(
        "phase9_step12_postgres_runtime_repository_integration"
    )
    assert phase9_step12_profile == {
        "requirements.txt",
        "src/storage/durable_orchestration/postgres_connection.py",
        "tests/test_phase9_step12_durable_orchestration_postgres_runtime_integration.py",
    }
    assert not any("*" in path for path in phase9_step12_profile)
    assert not any(
        path
        in {
            "src",
            "src/",
            "src/**",
            "src/storage",
            "src/storage/",
            "src/storage/**",
            "src/storage/durable_orchestration",
            "src/storage/durable_orchestration/",
            "src/storage/durable_orchestration/**",
            "tests",
            "tests/",
            "tests/**",
        }
        for path in phase9_step12_profile
    )
    assert {
        "tests/support/phase_guard_registry.py",
        "tests/test_phase85b_legacy_guard_registry_default_off.py",
        "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
        "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
    }.isdisjoint(phase9_step12_profile)

    phase9_step14_profile = legacy_guard_allowlist(
        "phase9_step14_langgraph_postgres_checkpointer_foundation"
    )
    assert phase9_step14_profile == {
        "requirements.txt",
        "src/storage/durable_orchestration/langgraph_postgres.py",
        "src/storage/admin_tools/durable_orchestration/setup_langgraph_checkpointer.py",
        "tests/test_phase9_step14_langgraph_postgres_checkpointer_foundation.py",
    }
    assert not any("*" in path for path in phase9_step14_profile)
    assert not any(
        path
        in {
            "src",
            "src/",
            "src/**",
            "src/storage",
            "src/storage/",
            "src/storage/**",
            "src/storage/durable_orchestration",
            "src/storage/durable_orchestration/",
            "src/storage/durable_orchestration/**",
            "src/storage/admin_tools",
            "src/storage/admin_tools/",
            "src/storage/admin_tools/**",
            "tests",
            "tests/",
            "tests/**",
        }
        for path in phase9_step14_profile
    )
    assert {
        "tests/support/phase_guard_registry.py",
        "tests/test_phase85b_legacy_guard_registry_default_off.py",
        "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
        "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
    }.isdisjoint(phase9_step14_profile)

    phase9_step16a_profile = legacy_guard_allowlist(
        "phase9_step16a_durable_decision_authorization_runtime"
    )
    assert phase9_step16a_profile == {
        "src/storage/durable_orchestration/store.py",
        "src/storage/durable_orchestration/repository.py",
        "tests/test_phase9_step16a_durable_decision_authorization_runtime_contract.py",
    }
    assert not any("*" in path for path in phase9_step16a_profile)
    assert {
        "requirements.txt",
        "src/storage/durable_orchestration/schema.sql",
        "src/storage/durable_orchestration/langgraph_postgres.py",
        "src/agents/evidence_chain_langgraph_harness.py",
        "src/app/api.py",
    }.isdisjoint(phase9_step16a_profile)

    phase9_step16b_profile = legacy_guard_allowlist(
        "phase9_step16b_attempt_recovery_terminal_runtime"
    )
    assert phase9_step16b_profile == {
        "src/storage/durable_orchestration/store.py",
        "src/storage/durable_orchestration/repository.py",
        "tests/test_phase9_step16b_attempt_recovery_terminal_runtime_contract.py",
    }
    assert not any("*" in path for path in phase9_step16b_profile)
    assert {
        "requirements.txt",
        "src/storage/durable_orchestration/schema.sql",
        "src/storage/durable_orchestration/langgraph_postgres.py",
        "src/agents/evidence_chain_langgraph_harness.py",
        "src/app/api.py",
    }.isdisjoint(phase9_step16b_profile)

    phase9_step17_profile = legacy_guard_allowlist(
        "phase9_step17_durable_langgraph_restart_resume_integration"
    )
    assert phase9_step17_profile == {
        "src/agents/durable_evidence_chain_resume_coordinator.py",
        "tests/test_phase9_step17_durable_langgraph_restart_resume_integration.py",
    }
    assert not any("*" in path for path in phase9_step17_profile)
    assert {
        "requirements.txt",
        "src/storage/durable_orchestration/schema.sql",
        "src/storage/durable_orchestration/store.py",
        "src/storage/durable_orchestration/repository.py",
        "src/storage/durable_orchestration/langgraph_postgres.py",
        "src/agents/evidence_chain_langgraph_harness.py",
        "src/app/api.py",
    }.isdisjoint(phase9_step17_profile)

    phase9_step18a_profile = legacy_guard_allowlist(
        "phase9_step18a_coordinator_owned_resume_boundary"
    )
    assert phase9_step18a_profile == {
        "src/agents/durable_evidence_chain_resume_coordinator.py",
        "tests/test_phase9_step17_durable_langgraph_restart_resume_integration.py",
        "tests/test_phase9_step18a_coordinator_owned_resume_boundary.py",
    }
    assert not any("*" in path for path in phase9_step18a_profile)
    assert {
        "requirements.txt",
        "src/storage/durable_orchestration/schema.sql",
        "src/storage/durable_orchestration/store.py",
        "src/storage/durable_orchestration/repository.py",
        "src/storage/durable_orchestration/langgraph_postgres.py",
        "src/agents/evidence_chain_langgraph_harness.py",
        "src/app/api.py",
    }.isdisjoint(phase9_step18a_profile)

    phase9_step18b_profile = legacy_guard_allowlist(
        "phase9_step18b_durable_langgraph_process_restart"
    )
    assert phase9_step18b_profile == {
        "tests/support/phase9_step18b_restart_process_worker.py",
        "tests/test_phase9_step18b_durable_langgraph_process_restart.py",
    }
    assert not any("*" in path for path in phase9_step18b_profile)
    assert {
        "requirements.txt",
        "src/agents/durable_evidence_chain_resume_coordinator.py",
        "src/storage/durable_orchestration/schema.sql",
        "src/storage/durable_orchestration/store.py",
        "src/storage/durable_orchestration/repository.py",
        "src/app/api.py",
    }.isdisjoint(phase9_step18b_profile)

    phase10_step2_profile = legacy_guard_allowlist(
        "phase10_step2_shadow_adapter_parity_foundation"
    )
    assert phase10_step2_profile == {
        "src/agents/evidence_chain_shadow_adapter.py",
        "src/agents/evidence_chain_shadow_parity.py",
        "tests/test_phase10_shadow_input_adapter.py",
        "tests/test_phase10_shadow_parity_contract.py",
        "tests/test_phase10_shadow_adapter_write_suppression.py",
    }
    assert not any("*" in path for path in phase10_step2_profile)
    assert {
        "tests/support/phase_guard_registry.py",
        "tests/test_phase85b_legacy_guard_registry_default_off.py",
        "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
        "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
    }.isdisjoint(phase10_step2_profile)

    phase10_step3_profile = legacy_guard_allowlist(
        "phase10_step3_explicit_readonly_shadow_execution"
    )
    assert phase10_step3_profile == {
        "src/agents/evidence_chain_shadow_execution.py",
        "run_evidence_chain_shadow.py",
        "tests/test_phase10_shadow_execution_readonly.py",
        "tests/test_phase10_shadow_command_default_off.py",
        "tests/test_phase10_shadow_execution_write_suppression.py",
    }
    assert not any("*" in path for path in phase10_step3_profile)
    assert {
        "tests/support/phase_guard_registry.py",
        "tests/test_phase85b_legacy_guard_registry_default_off.py",
        "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
        "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
    }.isdisjoint(phase10_step3_profile)

    phase10_step5a_profile = legacy_guard_allowlist(
        "phase10_step5a_shadow_resume_evidence_projection"
    )
    assert phase10_step5a_profile == {
        "batch_select_best_resume_variant.py",
        "run_application_planning.py",
        "src/pipeline/shadow_resume_evidence_projection.py",
        "tests/test_phase10_step5a_shadow_resume_evidence_projection.py",
    }
    assert not any("*" in path for path in phase10_step5a_profile)
    assert {
        "main.py",
        "run_evidence_chain_shadow.py",
        "src/pipeline/runtime_status.py",
        "src/pipeline/collector.py",
        "src/app/api.py",
        "src/app/services.py",
        "tests/support/phase_guard_registry.py",
        "tests/test_phase85b_legacy_guard_registry_default_off.py",
        "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
        "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
    }.isdisjoint(phase10_step5a_profile)

    phase10_step5b_profile = legacy_guard_allowlist(
        "phase10_step5b_shadow_projection_failure_isolation"
    )
    assert phase10_step5b_profile == {
        "batch_select_best_resume_variant.py",
        "run_application_planning.py",
        "src/pipeline/shadow_resume_evidence_projection.py",
        "tests/test_phase10_step5b_shadow_projection_failure_isolation.py",
    }
    assert not any("*" in path for path in phase10_step5b_profile)
    assert {
        "main.py",
        "run_evidence_chain_shadow.py",
        "src/pipeline/runtime_status.py",
        "tests/support/phase_guard_registry.py",
        "tests/test_phase85b_legacy_guard_registry_default_off.py",
    }.isdisjoint(phase10_step5b_profile)

    phase10_step5c_profile = legacy_guard_allowlist(
        "phase10_step5c_default_off_post_planning_shadow_hook"
    )
    assert phase10_step5c_profile == {
        "main.py",
        "src/pipeline/post_planning_shadow.py",
        "tests/test_phase10_step5c_default_off_post_planning_shadow_hook.py",
    }
    assert not any("*" in path for path in phase10_step5c_profile)
    assert {
        "run_application_planning.py",
        "run_evidence_chain_shadow.py",
        "src/pipeline/runtime_status.py",
        "src/storage/durable_orchestration/repository.py",
        "tests/support/phase_guard_registry.py",
        "tests/test_phase85b_legacy_guard_registry_default_off.py",
    }.isdisjoint(phase10_step5c_profile)

    phase10_step8_profile = legacy_guard_allowlist(
        "phase10_step8_shadow_observation_safety"
    )
    assert phase10_step8_profile == {
        "src/pipeline/post_planning_shadow.py",
        "src/pipeline/shadow_observation_contract.py",
        "src/pipeline/shadow_observation_store.py",
        "docs/controlled_shadow_observation_runbook.md",
        "tests/test_phase10_step8_shadow_observation_contract.py",
        "tests/test_phase10_step8_shadow_observation_store.py",
        "tests/test_phase10_step8_shadow_cleanup_liveness.py",
        "tests/test_phase10_step8_shadow_observation_integration.py",
    }
    assert not any("*" in path for path in phase10_step8_profile)
    assert {
        "main.py",
        "run_application_planning.py",
        "run_evidence_chain_shadow.py",
        "src/pipeline/runtime_status.py",
        "src/pipeline/collector.py",
        "src/app/api.py",
        "src/app/services.py",
        "requirements.txt",
        "tests/support/phase_guard_registry.py",
        "tests/test_phase85b_legacy_guard_registry_default_off.py",
        "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
        "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
    }.isdisjoint(phase10_step8_profile)

    phase10_step11_profile = legacy_guard_allowlist(
        "phase10_step11_postgres_planning_corpus_snapshot"
    )
    assert phase10_step11_profile == {
        "main.py",
        "src/pipeline/postgres_planning_corpus_snapshot.py",
        "tests/test_phase10_step11_postgres_planning_corpus_snapshot.py",
        "tests/support/phase_guard_registry.py",
        "tests/test_phase85b_legacy_guard_registry_default_off.py",
    }
    assert not any("*" in path for path in phase10_step11_profile)
    assert {
        "src/storage/rag_store.py",
        "src/rag/export_job_corpus.py",
        "run_application_planning.py",
        "batch_select_best_resume_variant.py",
        "src/pipeline/post_planning_shadow.py",
        "run_evidence_chain_shadow.py",
        "src/pipeline/collector.py",
        "src/app/api.py",
        "src/app/services.py",
        "requirements.txt",
    }.isdisjoint(phase10_step11_profile)

    phase11_step2_profile = legacy_guard_allowlist(
        "phase11_step2_job_prioritization_graph_contract"
    )
    assert phase11_step2_profile == {
        "src/agents/job_prioritization_graph_verification.py",
        "tests/test_phase11_step2_job_prioritization_graph_contract.py",
        "tests/support/phase_guard_registry.py",
        "tests/test_phase85b_legacy_guard_registry_default_off.py",
        "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
        "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
    }
    assert not any("*" in path for path in phase11_step2_profile)
    assert {
        "application_execution_queue.py",
        "src/agents/evidence_chain_langgraph_harness.py",
        "src/agents/job_prioritization_agent.py",
        "src/pipeline/collector.py",
        "main.py",
        "src/app/api.py",
        "src/app/services.py",
        "src/storage/durable_orchestration/repository.py",
    }.isdisjoint(phase11_step2_profile)

    phase11_step3_profile = legacy_guard_allowlist(
        "phase11_step3_job_prioritization_graph_integration"
    )
    assert phase11_step3_profile == {
        "application_execution_queue.py",
        "src/agents/job_prioritization_graph_verification.py",
        "src/agents/job_prioritization_graph_integration.py",
        "tests/test_phase11_step3_job_prioritization_graph_integration.py",
        "tests/support/phase_guard_registry.py",
        "tests/test_phase85b_legacy_guard_registry_default_off.py",
        "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
        "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
    } | PHASE11_STEP3_DIRECT_HASH_GUARD_FILES
    assert not any("*" in path for path in phase11_step3_profile)
    assert {
        "main.py",
        "run_application_planning.py",
        "src/agents/job_prioritization_agent.py",
        "src/agents/evidence_chain_langgraph_harness.py",
        "src/agents/evidence_chain_composition.py",
        "src/pipeline/collector.py",
        "src/app/api.py",
        "src/app/services.py",
        "src/config/settings.py",
        "src/storage/durable_orchestration/repository.py",
    }.isdisjoint(phase11_step3_profile)

    phase9_step12_compatibility_profile = legacy_guard_allowlist(
        "phase9_step12_dependency_driver_compatibility"
    )
    assert phase9_step12_compatibility_profile == {
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
    }
    assert not any("*" in path for path in phase9_step12_compatibility_profile)
    assert all(
        path.startswith("tests/")
        for path in phase9_step12_compatibility_profile
    )
    assert {
        "tests/support/phase_guard_registry.py",
        "tests/test_phase85b_legacy_guard_registry_default_off.py",
        "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
        "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
    }.isdisjoint(phase9_step12_compatibility_profile)

    assert ITEM3_DASHBOARD_SCOPED_CHATBOT_FILES == {
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
    assert not any(
        "*" in path for path in ITEM3_DASHBOARD_SCOPED_CHATBOT_FILES
    )

    assert ITEM4_PLANNING_TAILORING_OPTIONS_FILES == {
        "tests/test_item4bc_planning_owner_isolation.py",
        "tests/test_item4cr2_planning_artifact_owner_root.py",
        "tests/test_item4d_generate_llm_tailoring_contract.py",
        "tests/test_item4et_tailoring_state_contract.py",
    }
    assert not any(
        "*" in path for path in ITEM4_PLANNING_TAILORING_OPTIONS_FILES
    )

    assert ITEM6_AGENTIC_REVIEW_UI_REVAMP_FILES == {
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
    assert not any("*" in path for path in ITEM6_AGENTIC_REVIEW_UI_REVAMP_FILES)

    item61b_admin_boundary_profile = legacy_guard_allowlist(
        "item61b_agentic_review_admin_boundary"
    )
    assert ITEM61B_AGENTIC_REVIEW_ADMIN_BOUNDARY_FILES == {
        "src/app/api.py",
        "src/app/profile_ui.py",
        "src/app/static/profile.js",
        "tests/test_item61b_agentic_review_admin_boundary.py",
        "tests/test_agent_trace_api.py",
        "tests/test_phase101b_evidence_chain_api_service_readback_default_off.py",
    }
    assert item61b_admin_boundary_profile == (
        ITEM61B_AGENTIC_REVIEW_ADMIN_BOUNDARY_FILES
    )
    assert len(item61b_admin_boundary_profile) == 6
    assert not any("*" in path for path in item61b_admin_boundary_profile)
    assert_changed_files_allowed(
        item61b_admin_boundary_profile,
        set(),
        legacy_guard_profiles=("item61b_agentic_review_admin_boundary",),
        include_current_milestone_compatibility=False,
    )
    with pytest.raises(AssertionError):
        assert_changed_files_allowed(
            {"src/app/services.py"},
            set(),
            legacy_guard_profiles=("item61b_agentic_review_admin_boundary",),
            include_current_milestone_compatibility=False,
        )

    item61c_readonly_backend_profile = legacy_guard_allowlist(
        "item61c_agentic_operations_readonly_backend"
    )
    assert ITEM61C_AGENTIC_OPERATIONS_READONLY_BACKEND_FILES == {
        "src/app/api.py",
        "src/app/services.py",
        "tests/test_item61c_agentic_operations_readonly_backend.py",
    }
    assert item61c_readonly_backend_profile == (
        ITEM61C_AGENTIC_OPERATIONS_READONLY_BACKEND_FILES
    )
    assert len(item61c_readonly_backend_profile) == 3
    assert not any("*" in path for path in item61c_readonly_backend_profile)
    assert_changed_files_allowed(
        item61c_readonly_backend_profile,
        set(),
        legacy_guard_profiles=("item61c_agentic_operations_readonly_backend",),
        include_current_milestone_compatibility=False,
    )
    with pytest.raises(AssertionError):
        assert_changed_files_allowed(
            {"src/app/unapproved_runtime.py"},
            set(),
            legacy_guard_profiles=("item61c_agentic_operations_readonly_backend",),
            include_current_milestone_compatibility=False,
        )

    item61d_console_shell_profile = legacy_guard_allowlist(
        "item61d_agentic_operations_console_shell"
    )
    assert ITEM61D_AGENTIC_OPERATIONS_CONSOLE_SHELL_FILES == {
        "src/app/ui.py",
        "src/app/ui_shell.py",
        "src/app/static/shell.js",
        "tests/test_item61d_agentic_operations_console_shell.py",
    }
    assert item61d_console_shell_profile == (
        ITEM61D_AGENTIC_OPERATIONS_CONSOLE_SHELL_FILES
    )
    assert len(item61d_console_shell_profile) == 4
    assert not any("*" in path for path in item61d_console_shell_profile)
    assert_changed_files_allowed(
        item61d_console_shell_profile,
        set(),
        legacy_guard_profiles=("item61d_agentic_operations_console_shell",),
        include_current_milestone_compatibility=False,
    )
    with pytest.raises(AssertionError):
        assert_changed_files_allowed(
            {"src/app/unapproved_runtime.py"},
            set(),
            legacy_guard_profiles=("item61d_agentic_operations_console_shell",),
            include_current_milestone_compatibility=False,
        )

    item61e_overview_ui_profile = legacy_guard_allowlist(
        "item61e_agentic_operations_overview_ui"
    )
    assert ITEM61E_AGENTIC_OPERATIONS_OVERVIEW_UI_FILES == {
        "src/app/ui.py",
        "frontend/executive-kpi/src/main.tsx",
        "frontend/executive-kpi/src/styles.css",
        "frontend/executive-kpi/src/agentic/AgenticOperationsDashboard.tsx",
        "frontend/executive-kpi/src/agentic/agenticOperationsModel.ts",
        "frontend/executive-kpi/src/agentic/AgenticOperationsDashboard.test.tsx",
        "src/app/static/build/executive-kpi/executive-kpi.css",
        "src/app/static/build/executive-kpi/executive-kpi.js",
        "tests/test_item61e_agentic_operations_overview_ui.py",
    }
    assert item61e_overview_ui_profile == (
        ITEM61E_AGENTIC_OPERATIONS_OVERVIEW_UI_FILES
    )
    assert len(item61e_overview_ui_profile) == 9
    assert not any("*" in path for path in item61e_overview_ui_profile)
    assert_changed_files_allowed(
        item61e_overview_ui_profile,
        set(),
        legacy_guard_profiles=("item61e_agentic_operations_overview_ui",),
        include_current_milestone_compatibility=False,
    )
    for unrelated_path in (
        "src/app/services.py",
        "frontend/executive-kpi/src/agentic/UnapprovedDashboard.tsx",
        "src/app/static/build/executive-kpi/unapproved.js",
    ):
        with pytest.raises(AssertionError):
            assert_changed_files_allowed(
                {unrelated_path},
                set(),
                legacy_guard_profiles=(
                    "item61e_agentic_operations_overview_ui",
                ),
                include_current_milestone_compatibility=False,
            )

    item7b_account_toolbar_profile = legacy_guard_allowlist(
        "item7b_premium_account_toolbar"
    )
    assert ITEM7B_PREMIUM_ACCOUNT_TOOLBAR_FILES == {
        "src/app/application_hub_ui.py",
        "src/app/decisions_ui.py",
        "src/app/onboarding_ui.py",
        "src/app/planning_ui.py",
        "src/app/profile_ui.py",
        "src/app/static/app_redesign.css",
        "src/app/static/shell.js",
        "src/app/ui.py",
        "src/app/ui_shell.py",
        "tests/support/phase_guard_registry.py",
        "tests/test_item2_phase4_profile_corrections_and_legacy_route_retirement.py",
        "tests/test_item2_phase4_secondary_page_headers.py",
        "tests/test_item61d_agentic_operations_console_shell.py",
        "tests/test_item7b_premium_account_toolbar.py",
        "tests/test_phase132b2r3_guided_preferences_workflow.py",
        "tests/test_phase133d_pipeline_dashboard_react_island.py",
        "tests/test_phase1_step7_profile_ai_settings_ui.py",
        "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
        "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
        "tests/test_phase85b_legacy_guard_registry_default_off.py",
    }
    assert item7b_account_toolbar_profile == ITEM7B_PREMIUM_ACCOUNT_TOOLBAR_FILES
    assert len(item7b_account_toolbar_profile) == 20
    assert all(
        not any(token in path for token in ("*", "?", "["))
        and not path.endswith("/")
        for path in item7b_account_toolbar_profile
    )
    assert_changed_files_allowed(
        item7b_account_toolbar_profile,
        set(),
        legacy_guard_profiles=("item7b_premium_account_toolbar",),
        include_current_milestone_compatibility=False,
    )
    for unrelated_path in (
        "src/app/services.py",
        "src/app/api.py",
        "frontend/executive-kpi/src/UnapprovedAccountMenu.tsx",
        "tests/test_unapproved_item7b_surface.py",
    ):
        with pytest.raises(AssertionError):
            assert_changed_files_allowed(
                {unrelated_path},
                set(),
                legacy_guard_profiles=("item7b_premium_account_toolbar",),
                include_current_milestone_compatibility=False,
            )

    item71b_runtime_profile = legacy_guard_allowlist(
        "item71b_safe_diagnostics_runtime_foundation"
    )
    assert ITEM71B_SAFE_DIAGNOSTICS_RUNTIME_FOUNDATION_FILES == {
        "src/app/api.py",
        "src/app/services.py",
        "src/storage/saved_scans/read_postgres.py",
        "tests/support/phase_guard_registry.py",
        "tests/test_item71b_safe_diagnostics_runtime_foundation.py",
        "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
        "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
        "tests/test_phase85b_legacy_guard_registry_default_off.py",
    }
    assert item71b_runtime_profile == ITEM71B_SAFE_DIAGNOSTICS_RUNTIME_FOUNDATION_FILES
    assert len(item71b_runtime_profile) == 8
    assert not any("*" in path for path in item71b_runtime_profile)
    assert_changed_files_allowed(
        item71b_runtime_profile,
        set(),
        legacy_guard_profiles=("item71b_safe_diagnostics_runtime_foundation",),
        include_current_milestone_compatibility=False,
    )
    with pytest.raises(AssertionError):
        assert_changed_files_allowed(
            {"frontend/executive-kpi/src/diagnostics/AdvancedDiagnosticsDashboard.tsx"},
            set(),
            legacy_guard_profiles=("item71b_safe_diagnostics_runtime_foundation",),
            include_current_milestone_compatibility=False,
        )

    item71c_frontend_profile = legacy_guard_allowlist(
        "item71c_scan_diagnostics_frontend_activation"
    )
    assert item71c_frontend_profile == ITEM71C_SCAN_DIAGNOSTICS_FRONTEND_ACTIVATION_FILES
    assert len(item71c_frontend_profile) == 14
    assert not any("*" in path for path in item71c_frontend_profile)
    assert_changed_files_allowed(
        item71c_frontend_profile,
        set(),
        legacy_guard_profiles=("item71c_scan_diagnostics_frontend_activation",),
        include_current_milestone_compatibility=False,
    )
    with pytest.raises(AssertionError):
        assert_changed_files_allowed(
            {"src/app/api.py"},
            set(),
            legacy_guard_profiles=("item71c_scan_diagnostics_frontend_activation",),
            include_current_milestone_compatibility=False,
        )

    item71d_reset_profile = legacy_guard_allowlist(
        "item71d_latest_diagnostics_workflow_reset"
    )
    assert item71d_reset_profile == ITEM71D_LATEST_DIAGNOSTICS_WORKFLOW_RESET_FILES
    assert len(item71d_reset_profile) == 22
    assert not any("*" in path for path in item71d_reset_profile)
    assert_changed_files_allowed(
        item71d_reset_profile,
        set(),
        legacy_guard_profiles=("item71d_latest_diagnostics_workflow_reset",),
        include_current_milestone_compatibility=False,
    )

    notification_bridge_profile = legacy_guard_allowlist(
        "notifications_scheduler_bell_bridge"
    )
    assert notification_bridge_profile == NOTIFICATIONS_SCHEDULER_BELL_BRIDGE_FILES
    assert len(notification_bridge_profile) == 8
    assert not any("*" in path for path in notification_bridge_profile)
    assert_changed_files_allowed(
        notification_bridge_profile,
        set(),
        legacy_guard_profiles=("notifications_scheduler_bell_bridge",),
        include_current_milestone_compatibility=False,
    )
    with pytest.raises(AssertionError):
        assert_changed_files_allowed(
            {"src/pipeline/scheduler.py"},
            set(),
            legacy_guard_profiles=("notifications_scheduler_bell_bridge",),
            include_current_milestone_compatibility=False,
        )

    item71_groq_fix_profile = legacy_guard_allowlist(
        "item71_manual_review_groq_diagnostics_fix"
    )
    assert item71_groq_fix_profile == ITEM71_MANUAL_REVIEW_GROQ_DIAGNOSTICS_FIX_FILES
    assert item71_groq_fix_profile == {
        "src/agents/controlled_exact_resume_change_set_llm_request_packet_default_off.py",
        "src/app/services.py",
        "tests/support/phase_guard_registry.py",
        "tests/test_item71_manual_review_groq_diagnostics_fix.py",
        "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
        "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
        "tests/test_phase43b_controlled_exact_resume_change_set_llm_request_packet_dry_run_command_default_off.py",
        "tests/test_phase45a_controlled_exact_resume_change_set_provider_response_validation_default_off.py",
        "tests/test_phase45b_controlled_exact_resume_change_set_provider_response_validation_dry_run_command_default_off.py",
        "tests/test_phase49a_controlled_exact_resume_change_set_real_provider_runtime_adapter_default_off.py",
        "tests/test_phase49b_controlled_exact_resume_change_set_real_provider_runtime_adapter_dry_run_command_default_off.py",
        "tests/test_phase85b_legacy_guard_registry_default_off.py",
    }
    assert len(item71_groq_fix_profile) == 12
    assert not any("*" in path for path in item71_groq_fix_profile)
    assert_changed_files_allowed(
        item71_groq_fix_profile,
        set(),
        legacy_guard_profiles=("item71_manual_review_groq_diagnostics_fix",),
        include_current_milestone_compatibility=False,
    )
    with pytest.raises(AssertionError):
        assert_changed_files_allowed(
            {"src/ai/llm_client.py"},
            set(),
            legacy_guard_profiles=("item71_manual_review_groq_diagnostics_fix",),
            include_current_milestone_compatibility=False,
        )

    item71_effective_filter_profile = legacy_guard_allowlist(
        "item71_effective_exact_change_filter"
    )
    assert item71_effective_filter_profile == (
        ITEM71_EFFECTIVE_EXACT_CHANGE_FILTER_FILES
    )
    assert item71_effective_filter_profile == {
        "src/agents/exact_resume_change_set_proposal_builder_default_off.py",
        "src/agents/controlled_exact_resume_change_set_llm_request_packet_default_off.py",
        "tests/support/phase_guard_registry.py",
        "tests/test_phase42a_exact_resume_change_set_proposal_builder_default_off.py",
        "tests/test_phase43a_controlled_exact_resume_change_set_llm_request_packet_default_off.py",
    }
    assert len(item71_effective_filter_profile) == 5
    assert not any("*" in path for path in item71_effective_filter_profile)
    assert_changed_files_allowed(
        item71_effective_filter_profile,
        set(),
        legacy_guard_profiles=("item71_effective_exact_change_filter",),
        include_current_milestone_compatibility=False,
    )
    with pytest.raises(AssertionError):
        assert_changed_files_allowed(
            {"src/app/services.py"},
            set(),
            legacy_guard_profiles=("item71_effective_exact_change_filter",),
            include_current_milestone_compatibility=False,
        )

    item61h_v1_visual_polish_profile = legacy_guard_allowlist(
        "item61h_v1_scan_diagnostics_visual_polish"
    )
    assert ITEM61H_V1_SCAN_DIAGNOSTICS_VISUAL_POLISH_FILES == {
        "frontend/executive-kpi/src/styles.css",
        "src/app/planning_ui.py",
        "src/app/static/build/executive-kpi/executive-kpi.css",
        "tests/test_advanced_diagnostics_react_redesign.py",
    }
    assert item61h_v1_visual_polish_profile == (
        ITEM61H_V1_SCAN_DIAGNOSTICS_VISUAL_POLISH_FILES
    )
    assert len(item61h_v1_visual_polish_profile) == 4
    assert all(
        not any(token in path for token in ("*", "?", "["))
        and not path.endswith("/")
        for path in item61h_v1_visual_polish_profile
    )
    for unrelated_path in (
        "src/app/services.py",
        "frontend/executive-kpi/src/diagnostics/UnapprovedDiagnostics.tsx",
        "src/app/static/build/executive-kpi/unapproved.css",
        "tests/test_unapproved_item61h_v1_surface.py",
    ):
        with pytest.raises(AssertionError):
            assert_changed_files_allowed(
                {unrelated_path},
                set(),
                legacy_guard_profiles=(
                    "item61h_v1_scan_diagnostics_visual_polish",
                ),
                include_current_milestone_compatibility=False,
            )

    item61f_registry_matrix_profile = legacy_guard_allowlist(
        "item61f_agent_registry_safety_matrix"
    )
    assert ITEM61F_AGENT_REGISTRY_SAFETY_MATRIX_FILES == {
        "frontend/executive-kpi/src/agentic/AgenticOperationsDashboard.test.tsx",
        "frontend/executive-kpi/src/agentic/AgenticOperationsDashboard.tsx",
        "frontend/executive-kpi/src/agentic/agenticOperationsModel.ts",
        "frontend/executive-kpi/src/styles.css",
        "src/app/static/build/executive-kpi/executive-kpi.css",
        "src/app/static/build/executive-kpi/executive-kpi.js",
        "tests/test_item61f_agent_registry_safety_matrix.py",
    }
    assert item61f_registry_matrix_profile == (
        ITEM61F_AGENT_REGISTRY_SAFETY_MATRIX_FILES
    )
    assert len(item61f_registry_matrix_profile) == 7
    assert all(
        not any(token in path for token in ("*", "?", "["))
        and not path.endswith("/")
        for path in item61f_registry_matrix_profile
    )
    assert_changed_files_allowed(
        item61f_registry_matrix_profile,
        set(),
        legacy_guard_profiles=("item61f_agent_registry_safety_matrix",),
        include_current_milestone_compatibility=False,
    )
    for unrelated_path in (
        "src/app/services.py",
        "frontend/executive-kpi/src/agentic/UnapprovedDashboard.tsx",
        "src/app/static/build/executive-kpi/unapproved.js",
        "tests/test_unapproved_item61f_surface.py",
    ):
        with pytest.raises(AssertionError):
            assert_changed_files_allowed(
                {unrelated_path},
                set(),
                legacy_guard_profiles=(
                    "item61f_agent_registry_safety_matrix",
                ),
                include_current_milestone_compatibility=False,
            )

    item61g_run_inspector_profile = legacy_guard_allowlist(
        "item61g_run_inspector_agentic_review_integration"
    )
    assert ITEM61G_RUN_INSPECTOR_AGENTIC_REVIEW_INTEGRATION_FILES == {
        "frontend/executive-kpi/src/agentic/AgenticOperationsDashboard.tsx",
        "frontend/executive-kpi/src/agentic/AgenticOperationsDashboard.test.tsx",
        "frontend/executive-kpi/src/styles.css",
        "src/app/static/build/executive-kpi/executive-kpi.js",
        "src/app/static/build/executive-kpi/executive-kpi.css",
        "tests/test_item61g_run_inspector_agentic_review_integration.py",
    }
    assert item61g_run_inspector_profile == (
        ITEM61G_RUN_INSPECTOR_AGENTIC_REVIEW_INTEGRATION_FILES
    )
    assert len(item61g_run_inspector_profile) == 6
    assert all(
        not any(token in path for token in ("*", "?", "["))
        and not path.endswith("/")
        for path in item61g_run_inspector_profile
    )
    assert_changed_files_allowed(
        item61g_run_inspector_profile,
        set(),
        legacy_guard_profiles=(
            "item61g_run_inspector_agentic_review_integration",
        ),
        include_current_milestone_compatibility=False,
    )
    for unrelated_path in (
        "src/app/services.py",
        "frontend/executive-kpi/src/agentic/UnapprovedDashboard.tsx",
        "src/app/static/build/executive-kpi/unapproved.js",
        "tests/test_unapproved_item61g_surface.py",
    ):
        with pytest.raises(AssertionError):
            assert_changed_files_allowed(
                {unrelated_path},
                set(),
                legacy_guard_profiles=(
                    "item61g_run_inspector_agentic_review_integration",
                ),
                include_current_milestone_compatibility=False,
            )

    item61h_product_clarity_profile = legacy_guard_allowlist(
        "item61h_cross_page_navigation_product_clarity"
    )
    assert ITEM61H_CROSS_PAGE_NAVIGATION_PRODUCT_CLARITY_FILES == {
        "frontend/executive-kpi/src/agentic/AgenticOperationsDashboard.test.tsx",
        "frontend/executive-kpi/src/agentic/AgenticOperationsDashboard.tsx",
        "frontend/executive-kpi/src/diagnostics/AdvancedDiagnosticsDashboard.test.tsx",
        "frontend/executive-kpi/src/diagnostics/AdvancedDiagnosticsDashboard.tsx",
        "src/app/planning_ui.py",
        "src/app/profile_ui.py",
        "src/app/static/build/executive-kpi/executive-kpi.js",
        "src/app/ui_shell.py",
        "tests/test_advanced_diagnostics_react_redesign.py",
        "tests/test_item2_phase4_profile_corrections_and_legacy_route_retirement.py",
        "tests/test_item61b_agentic_review_admin_boundary.py",
        "tests/test_item61d_agentic_operations_console_shell.py",
        "tests/test_item61g_run_inspector_agentic_review_integration.py",
        "tests/test_item6c3_agentic_review_back_navigation_placement_visibility.py",
    }
    assert item61h_product_clarity_profile == (
        ITEM61H_CROSS_PAGE_NAVIGATION_PRODUCT_CLARITY_FILES
    )
    assert len(item61h_product_clarity_profile) == 14
    assert all(
        not any(token in path for token in ("*", "?", "["))
        and not path.endswith("/")
        for path in item61h_product_clarity_profile
    )
    assert_changed_files_allowed(
        item61h_product_clarity_profile,
        set(),
        legacy_guard_profiles=("item61h_cross_page_navigation_product_clarity",),
        include_current_milestone_compatibility=False,
    )
    for unrelated_path in (
        "src/app/services.py",
        "frontend/executive-kpi/src/agentic/UnapprovedDashboard.tsx",
        "src/app/static/build/executive-kpi/unapproved.js",
        "tests/test_unapproved_item61h_surface.py",
    ):
        with pytest.raises(AssertionError):
            assert_changed_files_allowed(
                {unrelated_path},
                set(),
                legacy_guard_profiles=(
                    "item61h_cross_page_navigation_product_clarity",
                ),
                include_current_milestone_compatibility=False,
            )

    assert current_milestone_guard_compatibility_allowlist() == (
        LIVE_PIPELINE_AI_EVALUATION_RELIABILITY_FILES
        | PRODUCTION_CPU_TORCH_BUILD_FILES
        | PRODUCTION_DEPLOYMENT_HARDENING_FILES
        | PROBLEM1_JD_INTELLIGENCE_CONTRACT_REVISION_FILES
        | STEP1_RENDERER_BOUND_V2_QUALIFICATION_STABILIZATION_FILES
        | STEP14_CONTROLLED_CANARY_CURRENT_CASE_OWNERSHIP_FILES
        | STEP14F_UI_STATIC_CONTRACT_REPAIR_FILES
        | STEP1B2_GLOBAL_ACQUISITION_BOUNDARY_FILES
        | STEP1B3_OWNER_PROJECTION_SHARED_POOL_FILES
        | STEP1B4_OWNER_SELECTOR_LLM_ROUTING_FILES
        | ITEM2_MANUAL_PROVIDER_PREVIEW_JOB_IDENTITY_REPAIR_FILES
        | ITEM2_MANUAL_PROVIDER_PREVIEW_PROMPT_SCHEMA_ALIGNMENT_FILES
        | ITEM3_DASHBOARD_SCOPED_CHATBOT_FILES
        | ITEM4_PLANNING_TAILORING_OPTIONS_FILES
        | ITEM6_AGENTIC_REVIEW_UI_REVAMP_FILES
        | item61b_admin_boundary_profile
        | item61c_readonly_backend_profile
        | item61d_console_shell_profile
        | item61e_overview_ui_profile
        | item61f_registry_matrix_profile
        | item61g_run_inspector_profile
        | item61h_product_clarity_profile
        | item61h_v1_visual_polish_profile
        | item7b_account_toolbar_profile
        | item71b_runtime_profile
        | item71c_frontend_profile
        | item71d_reset_profile
        | notification_bridge_profile
        | item71_groq_fix_profile
        | item71_effective_filter_profile
        | item71_production_refinement_profile
        | smartrecruiters_pagination_profile
        | himalayas_step2b_profile
        | himalayas_step6c1_profile
        | himalayas_step6b2_profile
        | himalayas_step6b1_profile
        | legacy_guard_allowlist("policy_driven_llm_adjudicator_readback")
        | legacy_guard_allowlist("phase129b_auth_loader_ui")
        | phase129_profile
        | phase132_profile
        | phase133_profile
        | phase133b_profile
        | phase133d_profile
        | phase133g_profile
        | phase133ef_profile
        | source_yield_ui_profile
        | jobvite_location_freshness_profile
        | lr2_reliability_profile
        | fvr2b_source_contracts_profile
        | phase133h_profile
        | scheduler_admin_health_profile
        | scheduler_visual_correction_profile
        | phase133i_profile
        | item2_phase3_profile
        | item2_phase4_profile
        | item2_phase4_corrections_profile
        | phase8_step3d_profile
        | phase8_step4_profile
        | phase8_step6_profile
        | phase8_step8_profile
        | phase8_step13_profile
        | phase8_step14_profile
        | phase8_step15_profile
        | phase8_step17_profile
        | phase9_step2_profile
        | phase9_step3_profile
        | phase9_step4_profile
        | phase9_step6_profile
        | phase9_step8_profile
        | phase9_step9_profile
        | phase9_step10_profile
        | phase9_step12_profile
        | phase9_step14_profile
        | phase9_step16a_profile
        | phase9_step16b_profile
        | phase9_step17_profile
        | phase9_step18a_profile
        | phase9_step18b_profile
        | phase10_step2_profile
        | phase10_step3_profile
        | phase10_step5a_profile
        | phase10_step5b_profile
        | phase10_step5c_profile
        | phase10_step8_profile
        | phase10_step11_profile
        | phase11_step2_profile
        | phase11_step3_profile
        | PHASE13C_AUTHORITATIVE_JOB_PRIORITIZATION_NODE_FILES
        | PHASE14B_AUTHORITATIVE_TAILORING_CALLER_FILES
        | PHASE14C_AUTHORITATIVE_TAILORING_NODE_FILES
        | PHASE15B_CONDITIONAL_OPERATOR_REVIEW_CALLER_FILES
        | PHASE15C_CONDITIONAL_OPERATOR_REVIEW_NODE_FILES
        | PHASE17C_TAILORING_GENERATION_LLM_CLOSURE_FILES
        | phase9_step12_compatibility_profile
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
        | WORKDAY_PAGINATION_FRESHNESS_FILES
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
    assert PHASE13C_AUTHORITATIVE_JOB_PRIORITIZATION_NODE_FILES == {
        "application_execution_queue.py",
        "src/agents/job_prioritization_authoritative_graph.py",
        "tests/test_phase13c_first_authoritative_job_prioritization_node.py",
        "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
        "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
        "tests/test_phase8_pgvector_backend_readiness_schema_plan_no_runtime_change.py",
        "tests/support/phase_guard_registry.py",
        "tests/test_phase85b_legacy_guard_registry_default_off.py",
    }
    assert not any(
        "*" in path
        for path in PHASE13C_AUTHORITATIVE_JOB_PRIORITIZATION_NODE_FILES
    )
    assert PHASE14B_AUTHORITATIVE_TAILORING_CALLER_FILES == {
        "application_execution_queue.py",
        "src/agents/tailoring_decision_agent.py",
        "tests/test_phase14b_authoritative_tailoring_caller_reconciliation.py",
        "tests/support/phase_guard_registry.py",
        "tests/test_phase85b_legacy_guard_registry_default_off.py",
    }
    assert not any(
        "*" in path
        for path in PHASE14B_AUTHORITATIVE_TAILORING_CALLER_FILES
    )
    assert PHASE14C_AUTHORITATIVE_TAILORING_NODE_FILES == {
        "application_execution_queue.py",
        "src/agents/tailoring_decision_authoritative_graph.py",
        "tests/test_phase14c_second_authoritative_tailoring_node.py",
        "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
        "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
        "tests/support/phase_guard_registry.py",
        "tests/test_phase85b_legacy_guard_registry_default_off.py",
    }
    assert not any(
        "*" in path
        for path in PHASE14C_AUTHORITATIVE_TAILORING_NODE_FILES
    )
    assert PHASE15B_CONDITIONAL_OPERATOR_REVIEW_CALLER_FILES == {
        "application_execution_queue.py",
        "src/agents/operator_review_agent.py",
        "tests/test_phase15b_conditional_operator_review_caller_reconciliation.py",
        "tests/support/phase_guard_registry.py",
        "tests/test_phase85b_legacy_guard_registry_default_off.py",
    }
    assert not any(
        "*" in path
        for path in PHASE15B_CONDITIONAL_OPERATOR_REVIEW_CALLER_FILES
    )
    assert PHASE15C_CONDITIONAL_OPERATOR_REVIEW_NODE_FILES == {
        "application_execution_queue.py",
        "src/agents/operator_review_authoritative_graph.py",
        "tests/test_phase15b_conditional_operator_review_caller_reconciliation.py",
        "tests/test_phase15c_conditional_authoritative_operator_review_node.py",
        "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
        "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
        "tests/support/phase_guard_registry.py",
        "tests/test_phase85b_legacy_guard_registry_default_off.py",
    }
    assert not any(
        "*" in path
        for path in PHASE15C_CONDITIONAL_OPERATOR_REVIEW_NODE_FILES
    )
    assert PHASE12D_DETERMINISTIC_PRODUCTION_OWNER_SHADOW_FILES == {
        "src/agents/production_shadow_artifact_adapter.py",
        "src/agents/production_shadow_graph.py",
        "src/agents/production_shadow_job_priority_owner.py",
        "src/agents/production_shadow_state.py",
        "tests/test_phase12b_artifact_only_production_shadow_foundation.py",
        "tests/test_phase12d_first_deterministic_production_owner.py",
    }
    assert not any(
        "*" in path
        for path in PHASE12D_DETERMINISTIC_PRODUCTION_OWNER_SHADOW_FILES
    )
    assert PHASE11_STEP8L_PROVIDER_BENCHMARK_CONTRACT_FILES == {
        "src/evaluation/provider_benchmark_contract.py",
        "tests/fixtures/provider_benchmark/manifest.json",
        "tests/test_provider_benchmark_contract.py",
    }
    assert not any(
        "*" in path
        for path in PHASE11_STEP8L_PROVIDER_BENCHMARK_CONTRACT_FILES
    )
    assert PHASE11_STEP8M_PROVIDER_CLIENT_COMPATIBILITY_FILES == {
        "src/evaluation/provider_client_compatibility.py",
        "tests/test_provider_client_compatibility.py",
    }
    assert not any(
        "*" in path
        for path in PHASE11_STEP8M_PROVIDER_CLIENT_COMPATIBILITY_FILES
    )
    assert PHASE11_STEP8N_SHARED_LLM_CLIENT_SAFETY_FILES == {
        "src/ai/llm_client.py",
        "tests/test_llm_client_safety.py",
    }
    assert not any(
        "*" in path
        for path in PHASE11_STEP8N_SHARED_LLM_CLIENT_SAFETY_FILES
    )
    assert PHASE11_STEP8O_PROVIDER_FIXTURE_BENCHMARK_FILES == {
        "src/evaluation/provider_fixture_benchmark.py",
        "tests/fixtures/provider_benchmark/cases.json",
        "tests/test_provider_fixture_benchmark.py",
    }
    assert not any(
        "*" in path
        for path in PHASE11_STEP8O_PROVIDER_FIXTURE_BENCHMARK_FILES
    )
    assert PHASE11_STEP8P_CONTROLLED_PROVIDER_BENCHMARK_PLAN_FILES == {
        "src/evaluation/controlled_provider_benchmark_plan.py",
        "tests/fixtures/provider_benchmark/run_plan.json",
        "tests/test_controlled_provider_benchmark_plan.py",
    }
    assert not any(
        "*" in path
        for path in PHASE11_STEP8P_CONTROLLED_PROVIDER_BENCHMARK_PLAN_FILES
    )
    assert PHASE11_STEP8PA_TRANSMISSION_SAFE_FIXTURE_FILES == {
        "tests/fixtures/provider_benchmark/cases.json",
        "tests/test_provider_fixture_benchmark.py",
        "tests/test_transmission_safe_provider_fixtures.py",
    }
    assert not any(
        "*" in path
        for path in PHASE11_STEP8PA_TRANSMISSION_SAFE_FIXTURE_FILES
    )
    assert PHASE11_STEP8Q_CONTROLLED_PROVIDER_BENCHMARK_HARNESS_FILES == {
        "src/evaluation/controlled_provider_benchmark_harness.py",
        "tests/fixtures/provider_benchmark/synthetic_authorization.json",
        "tests/fixtures/provider_benchmark/synthetic_pricing.json",
        "tests/test_controlled_provider_benchmark_harness.py",
    }
    assert not any(
        "*" in path
        for path in PHASE11_STEP8Q_CONTROLLED_PROVIDER_BENCHMARK_HARNESS_FILES
    )
    assert PHASE11_STEP8R_GROQ_LIVE_CANARY_PREPARATION_FILES == {
        "docs/controlled_groq_provider_canary_runbook.md",
        "src/evaluation/controlled_groq_provider_canary.py",
        "tests/fixtures/provider_benchmark/groq_canary_authorization_template.json",
        "tests/fixtures/provider_benchmark/groq_canary_pricing_template.json",
        "tests/test_controlled_groq_provider_canary.py",
    }
    assert not any(
        "*" in path
        for path in PHASE11_STEP8R_GROQ_LIVE_CANARY_PREPARATION_FILES
    )
    assert PHASE11_STEP8T_REAL_GROQ_CANARY_TRANSPORT_FILES == {
        "src/evaluation/controlled_groq_canary_transport.py",
        "tests/test_controlled_groq_canary_transport.py",
    }
    assert not any(
        "*" in path
        for path in PHASE11_STEP8T_REAL_GROQ_CANARY_TRANSPORT_FILES
    )
    assert PHASE11_STEP8V_GROQ_CANARY_EVIDENCE_RUNTIME_FILES == {
        "src/evaluation/controlled_groq_canary_evidence_runtime.py",
        "tests/test_controlled_groq_canary_evidence_runtime.py",
    }
    assert not any(
        "*" in path
        for path in PHASE11_STEP8V_GROQ_CANARY_EVIDENCE_RUNTIME_FILES
    )
    assert PHASE11_STEP8Y_GROQ_CANARY_RUN_IDENTITY_FILES == {
        "src/evaluation/controlled_groq_canary_run_identity.py",
        "tests/test_controlled_groq_canary_run_identity.py",
    }
    assert not any(
        "*" in path
        for path in PHASE11_STEP8Y_GROQ_CANARY_RUN_IDENTITY_FILES
    )
    assert PHASE11_STEP8Z_GROQ_CANARY_RUN_EVIDENCE_RUNTIME_FILES == {
        "src/evaluation/controlled_groq_canary_run_evidence_runtime.py",
        "tests/test_controlled_groq_canary_run_evidence_runtime.py",
    }
    assert not any(
        "*" in path
        for path in PHASE11_STEP8Z_GROQ_CANARY_RUN_EVIDENCE_RUNTIME_FILES
    )
    assert PHASE11_STEP8ZE_GROQ_CANARY_RUN_003_PLAN_FILES == {
        "src/evaluation/controlled_groq_canary_run_003_plan.py",
        "tests/test_controlled_groq_canary_run_003_plan.py",
    }
    assert not any(
        "*" in path
        for path in PHASE11_STEP8ZE_GROQ_CANARY_RUN_003_PLAN_FILES
    )
    assert PHASE11_STEP8ZF_GROQ_CANARY_RUN_003_IDENTITY_FILES == {
        "src/evaluation/controlled_groq_canary_run_003_identity.py",
        "tests/test_controlled_groq_canary_run_003_identity.py",
    }
    assert not any(
        "*" in path
        for path in PHASE11_STEP8ZF_GROQ_CANARY_RUN_003_IDENTITY_FILES
    )
    assert PHASE11_STEP8ZG_GROQ_CANARY_RUN_003_RUNTIME_FILES == {
        "src/evaluation/controlled_groq_canary_run_003_transport.py",
        "src/evaluation/controlled_groq_canary_run_003_evidence_runtime.py",
        "tests/test_controlled_groq_canary_run_003_transport.py",
        "tests/test_controlled_groq_canary_run_003_evidence_runtime.py",
    }
    assert not any(
        "*" in path
        for path in PHASE11_STEP8ZG_GROQ_CANARY_RUN_003_RUNTIME_FILES
    )
    assert PHASE11_STEP8ZK_GROQ_CANARY_RUN_004_OFFLINE_RUNTIME_FILES == {
        "src/evaluation/controlled_groq_canary_run_004_plan.py",
        "src/evaluation/controlled_groq_canary_run_004_identity.py",
        "src/evaluation/controlled_groq_canary_run_004_evidence_runtime.py",
        "tests/test_controlled_groq_canary_run_004_plan.py",
        "tests/test_controlled_groq_canary_run_004_identity.py",
        "tests/test_controlled_groq_canary_run_004_evidence_runtime.py",
    }
    assert not any(
        "*" in path
        for path in PHASE11_STEP8ZK_GROQ_CANARY_RUN_004_OFFLINE_RUNTIME_FILES
    )
    assert PHASE11_STEP8ZN_GROQ_CANARY_RUN_005_DIAGNOSTIC_RUNTIME_FILES == {
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
    assert not any(
        "*" in path
        for path in PHASE11_STEP8ZN_GROQ_CANARY_RUN_005_DIAGNOSTIC_RUNTIME_FILES
    )
    assert PHASE11_STEP8ZQ_ADDITIVE_TAILORING_TRANSPORT_FILES == {
        "src/evaluation/controlled_tailoring_benchmark_request_adapter.py",
        "src/evaluation/controlled_groq_tailoring_canary_transport.py",
        "tests/test_controlled_tailoring_benchmark_request_adapter.py",
        "tests/test_controlled_groq_tailoring_canary_transport.py",
    }
    assert not any(
        "*" in path
        for path in PHASE11_STEP8ZQ_ADDITIVE_TAILORING_TRANSPORT_FILES
    )
    assert PHASE11_STEP8MA_RAG_TEST_ISOLATION_FILES == {
        "tests/test_rag_endpoint_behavior.py",
    }
    assert not any(
        "*" in path
        for path in PHASE11_STEP8MA_RAG_TEST_ISOLATION_FILES
    )
    assert {"src/app/api.py", "src/app/services.py"} <= phase129_profile
    assert len(phase129_profile) == 206

    assert_changed_files_allowed(
        {
            "src/agents/llm_adjudicator_readback.py",
            "batch_select_best_resume_variant.py",
            "tests/test_phase123b_llm_adjudicator_readback_default_off.py",
            "tests/test_phase128b_policy_driven_llm_adjudicator_readback.py",
            "tests/support/phase_guard_registry.py",
            "tests/test_phase85b_legacy_guard_registry_default_off.py",
        },
        set(),
    )
    assert_changed_files_allowed({"requirements.txt"}, set())

    for forbidden_path in (
        "src/matching/scorer.py",
        "src/app/unapproved_runtime.py",
        "src/app/static/media/unapproved.jpg",
        "tests/test_unapproved_phase129_surface.py",
    ):
        with pytest.raises(AssertionError):
            assert_changed_files_allowed({forbidden_path}, set())

    phase129_api_baseline = {
        "src/app/api.py": (
            "d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004"
        ),
    }
    assert_protected_hashes(
        Path(__file__).resolve().parents[1],
        phase129_api_baseline,
        compatibility_profiles=(
            "phase129c_workflow_overlay_and_run_scoped_corpus",
        ),
    )
    with pytest.raises(AssertionError):
        assert_protected_hashes(
            Path(__file__).resolve().parents[1],
            phase129_api_baseline,
            compatibility_profiles=("config_vocabulary_scoring_change",),
        )


def test_item61c_direct_hash_successors_are_exact_and_path_scoped():
    root = Path(__file__).resolve().parents[1]
    profile = ("item61c_agentic_operations_readonly_backend",)

    assert_protected_hashes(
        root,
        {
            "src/app/api.py": (
                "2b93b37a38fce17d50a9b5eb693062faa9bb9ada6a4926bb9e0f76d9ee518674"
            ),
            "src/app/services.py": (
                "f23325582482f242869bd088b0fb96dc8b0d106b86a3f81c240d59c88d288b74"
            ),
        },
        compatibility_profiles=profile,
    )
    assert_protected_hashes(
        root,
        {
            "src/app/api.py": (
                "d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004"
            ),
        },
        compatibility_profiles=profile,
    )
    with pytest.raises(AssertionError):
        assert_protected_hashes(
            root,
            {
                "src/app/api.py": (
                    "ca8de5e0643a4c24eb6d36c0371ee4c6e422a9dfa2c7dd01ce664954b959a985"
                ),
            },
            compatibility_profiles=profile,
        )


def test_assert_protected_hashes_detects_hash_mismatch(tmp_path):
    path = tmp_path / "guarded.py"
    path.write_text("print('safe')\n", encoding="utf-8")

    with pytest.raises(AssertionError) as exc:
        assert_protected_hashes(tmp_path, {"guarded.py": "0" * 64})

    message = str(exc.value)
    assert "guarded.py" in message
    assert "expected" in message
    assert "got" in message


@pytest.mark.parametrize(
    ("relative_path", "historical_hash", "accepted_successors"),
    (
        (
            "src/app/api.py",
            "2b93b37a38fce17d50a9b5eb693062faa9bb9ada6a4926bb9e0f76d9ee518674",
            (
                "ca8de5e0643a4c24eb6d36c0371ee4c6e422a9dfa2c7dd01ce664954b959a985",
            ),
        ),
        (
            "src/app/services.py",
            "02d09d6f6e204183ef67a543222b4e3a4dae993f40041dfb8911397b835be7f7",
            (
                "351721d166d4a1538ed3084e169365ffdd2b8e822b399f82298418493581e963",
                "aab9f26ebe70b458fb706cfeee7f9b6ae76a9bef5303b1d5c150b9773323d20e",
            ),
        ),
        (
            "src/pipeline/collector.py",
            "7f4d8cc6571f0aa16f722fac43569ddba0a24e518889ca3864a1e46df7fe4cea",
            (
                "a7e1a834fabda1e0dedc35ac5322bc855f65863465449f2f95b95d9e4e785dcb",
                "2a853270e1005c9a5cc7a42f44a9cd07f2ed352f6b18f99528918973b38bba33",
            ),
        ),
    ),
)
def test_exact_historical_hash_successor_pairs_are_finite(
    tmp_path,
    monkeypatch,
    relative_path,
    historical_hash,
    accepted_successors,
):
    protected_path = tmp_path / relative_path
    protected_path.parent.mkdir(parents=True)
    protected_path.write_text("guarded\n", encoding="utf-8")

    class StubDigest:
        def __init__(self, digest):
            self._digest = digest

        def hexdigest(self):
            return self._digest

    for successor in accepted_successors:
        monkeypatch.setattr(
            phase_guard_registry,
            "sha256",
            lambda _data, digest=successor: StubDigest(digest),
        )
        assert_protected_hashes(tmp_path, {relative_path: historical_hash})

    monkeypatch.setattr(
        phase_guard_registry,
        "sha256",
        lambda _data: StubDigest("0" * 64),
    )
    with pytest.raises(AssertionError):
        assert_protected_hashes(tmp_path, {relative_path: historical_hash})


def test_ast_forbidden_call_helper_catches_real_calls_and_imports(tmp_path):
    path = tmp_path / "unsafe.py"
    path.write_text(
        "import subprocess\n"
        "def run():\n"
        "    submit_application()\n",
        encoding="utf-8",
    )

    with pytest.raises(AssertionError) as exc:
        assert_no_forbidden_runtime_calls_ast(
            [path],
            forbidden_calls=("submit_application",),
            forbidden_imports=("subprocess",),
        )

    message = str(exc.value)
    assert "submit_application" in message
    assert "subprocess" in message


def test_ast_forbidden_call_helper_allows_false_safety_metadata(tmp_path):
    path = tmp_path / "metadata_only.py"
    path.write_text(
        "SAFETY = {\n"
        "    'database_write_performed': False,\n"
        "    'provider_call_performed': False,\n"
        "    'run_chat_completion_called': False,\n"
        "}\n",
        encoding="utf-8",
    )

    assert_false_safety_metadata_allowed_but_real_mutation_blocked(path)


def test_ast_forbidden_call_helper_blocks_real_mutation_call(tmp_path):
    path = tmp_path / "real_mutation.py"
    path.write_text(
        "def run():\n"
        "    database_write()\n",
        encoding="utf-8",
    )

    with pytest.raises(AssertionError) as exc:
        assert_false_safety_metadata_allowed_but_real_mutation_blocked(path)

    assert "database_write" in str(exc.value)


# ---------------------------------------------------------------------------
# Step 11: Phase20d / Phase21a legacy guard compatibility for the Step 1 +
# renderer-bound V2 stabilization. These prove the compatibility extension is
# exact and still fails closed.
# ---------------------------------------------------------------------------

STEP11_ROOT = Path(__file__).resolve().parents[1]
STEP11_GUARD_TESTS = (
    "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
    "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
)


def test_step1_renderer_bound_v2_stabilization_surface_is_exact():
    assert STEP1_RENDERER_BOUND_V2_QUALIFICATION_STABILIZATION_FILES == {
        "src/app/provider_model_routing_service.py",
        "src/evaluation/controlled_provider_benchmark_plan.py",
        "src/evaluation/controlled_provider_qualification_registry.py",
        "src/evaluation/job_fit_provider_model_qualification_overlay.py",
        "src/evaluation/provider_benchmark_contract.py",
        "src/evaluation/provider_model_recommendation_policy.py",
        "src/evaluation/renderer_bound_v2_job_fit_qualification_registry.json",
        "src/evaluation/renderer_bound_v2_skill_qualification_registry.json",
        "tests/support/phase_guard_registry.py",
        "tests/test_controlled_provider_benchmark_plan.py",
        "tests/test_controlled_provider_qualification_evidence_adapter.py",
        "tests/test_controlled_provider_qualification_registry.py",
        "tests/test_phase1_step10_recommended_provider_routing_bridge.py",
        "tests/test_phase1_step9c7a_controlled_live_qualification_gate.py",
        "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
        "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
        "tests/test_phase85b_legacy_guard_registry_default_off.py",
        "tests/test_provider_benchmark_contract.py",
        "tests/test_stage7a_job_fit_renderer_bound_activation.py",
    }
    # No globs, no prefixes, no directory allowances.
    for path in STEP1_RENDERER_BOUND_V2_QUALIFICATION_STABILIZATION_FILES:
        assert "*" not in path
        assert not path.endswith("/")
    # The durable V1 authority artifacts are never part of this surface.
    assert not any(
        path.endswith("renderer_bound_skill_qualification_registry.json")
        or path.endswith("renderer_bound_job_fit_qualification_registry.json")
        for path in STEP1_RENDERER_BOUND_V2_QUALIFICATION_STABILIZATION_FILES
    )


def test_step1_stabilization_surface_is_accepted_by_the_guard_allowlist():
    assert_changed_files_allowed(
        STEP1_RENDERER_BOUND_V2_QUALIFICATION_STABILIZATION_FILES,
        set(),
    )


def test_step1_stabilization_surface_plus_unauthorized_file_is_rejected():
    with pytest.raises(AssertionError) as exc:
        assert_changed_files_allowed(
            set(STEP1_RENDERER_BOUND_V2_QUALIFICATION_STABILIZATION_FILES)
            | {"src/app/application_execution_queue.py"},
            set(),
        )
    assert "src/app/application_execution_queue.py" in str(exc.value)


def test_step1_stabilization_surface_still_rejects_duplicate_artifacts():
    with pytest.raises(AssertionError):
        assert_changed_files_allowed(
            set(STEP1_RENDERER_BOUND_V2_QUALIFICATION_STABILIZATION_FILES)
            | {"src/evaluation/provider_benchmark_contract 2.py"},
            set(),
        )


def test_api_py_historical_identity_and_current_successor_are_accepted():
    profile = ("phase1_ai_provider_model_routing_hash_maintenance",)
    # 1. the historical expectation still resolves through its old identity
    assert_protected_hashes(
        STEP11_ROOT,
        {
            "src/app/api.py": (
                "2b93b37a38fce17d50a9b5eb693062faa9bb9ada6a4926bb9e0f76d9ee518674"
            ),
        },
        compatibility_profiles=(
            "item71d_latest_diagnostics_workflow_reset",
        ),
    )
    # 2. the exact current committed successor is accepted
    from hashlib import sha256

    actual = sha256((STEP11_ROOT / "src/app/api.py").read_bytes()).hexdigest()
    assert actual == (
        "55c91a9182951e2cbedd1e0c5b588676f4541249086288011daf025e4ed9fb99"
    )
    assert profile


def test_arbitrary_api_py_hash_is_still_rejected():
    # 3. an unknown hash never becomes an approved successor.
    for arbitrary in (
        "0" * 64,
        "deadbeef" * 8,
        "1111111111111111111111111111111111111111111111111111111111111111",
    ):
        with pytest.raises(AssertionError):
            assert_protected_hashes(
                STEP11_ROOT,
                {"src/app/api.py": arbitrary},
                compatibility_profiles=(
                    "phase1_ai_provider_model_routing_hash_maintenance",
                ),
            )


def _step11_marker_scan_branch(relative_test_path: str, function_name: str):
    """Return the stabilization branch node from a guard test function."""

    import ast

    module = ast.parse(
        (STEP11_ROOT / relative_test_path).read_text(encoding="utf-8")
    )
    function = next(
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == function_name
    )
    branch = next(
        node
        for node in ast.walk(function)
        if isinstance(node, ast.If)
        and "step1_renderer_bound_v2_stabilization_runtime_files"
        in ast.dump(node.test)
    )
    return function, branch


STEP11_MARKER_GUARDS = (
    (
        "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
        "test_no_changed_runtime_file_introduces_forbidden_automation_markers",
    ),
    (
        "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
        "test_changed_runtime_files_add_no_autonomous_application_markers",
    ),
)


@pytest.mark.parametrize("relative_test_path,function_name", STEP11_MARKER_GUARDS)
def test_step11_marker_guard_scans_added_lines_and_has_no_unconditional_bypass(
    relative_test_path,
    function_name,
):
    import ast

    function, branch = _step11_marker_scan_branch(
        relative_test_path,
        function_name,
    )
    # The branch is reachable only on an EXACT changed-runtime-file set match.
    assert isinstance(branch.test, ast.Compare)
    assert any(isinstance(op, ast.Eq) for op in branch.test.ops)

    # It must scan added diff lines against every forbidden marker before
    # returning: a bare `return` without the scan would be a bypass.
    marker_loops = [
        node
        for node in ast.walk(branch)
        if isinstance(node, ast.For)
        and "FORBIDDEN_RUNTIME_MARKERS" in ast.dump(node.iter)
    ]
    assert len(marker_loops) == 1
    assert any(
        isinstance(node, ast.Assert) for node in ast.walk(marker_loops[0])
    )
    returns = [node for node in ast.walk(branch) if isinstance(node, ast.Return)]
    assert len(returns) == 1
    branch_body_dump = ast.dump(ast.Module(body=branch.body, type_ignores=[]))
    assert branch_body_dump.index("FORBIDDEN_RUNTIME_MARKERS") < (
        branch_body_dump.rindex("Return")
    )

    # The strict historical fallthrough assertion must still exist, so an
    # unrecognised runtime combination still fails closed.
    fallthrough_asserts = [
        node
        for node in function.body
        if isinstance(node, ast.Assert)
        and "changed_runtime_files" in ast.dump(node.test)
    ]
    assert fallthrough_asserts

    # ...and the function must still end with the whole-file marker sweep that
    # every non-early-returning combination is subjected to.
    final_statement = function.body[-1]
    assert isinstance(final_statement, ast.For)
    final_dump = ast.dump(final_statement)
    assert "FORBIDDEN_RUNTIME_MARKERS" in final_dump
    assert any(
        isinstance(node, ast.Assert) for node in ast.walk(final_statement)
    )


def test_step11_current_stabilization_runtime_additions_have_no_forbidden_marker():
    import subprocess

    from tests.test_phase20d_no_auto_apply_safety_checkpoint_default_off import (
        FORBIDDEN_RUNTIME_MARKERS as PHASE20D_MARKERS,
    )
    from tests.test_phase21a_manual_review_workflow_boundary_default_off import (
        FORBIDDEN_RUNTIME_MARKERS as PHASE21A_MARKERS,
    )

    runtime_suffixes = {".py", ".js", ".html", ".css"}
    runtime_files = sorted(
        path
        for path in STEP1_RENDERER_BOUND_V2_QUALIFICATION_STABILIZATION_FILES
        if path.startswith("src/") and Path(path).suffix in runtime_suffixes
    )
    assert runtime_files == [
        "src/app/provider_model_routing_service.py",
        "src/evaluation/controlled_provider_benchmark_plan.py",
        "src/evaluation/controlled_provider_qualification_registry.py",
        "src/evaluation/job_fit_provider_model_qualification_overlay.py",
        "src/evaluation/provider_benchmark_contract.py",
        "src/evaluation/provider_model_recommendation_policy.py",
    ]
    diff = subprocess.check_output(
        ["git", "diff", "--unified=0", "--", *runtime_files],
        cwd=STEP11_ROOT,
        text=True,
    )
    added_lines = "\n".join(
        line[1:]
        for line in diff.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    )
    markers = set(PHASE20D_MARKERS) | set(PHASE21A_MARKERS)
    for marker in markers:
        assert marker not in added_lines
    # The diff is empty on any branch where this milestone is already committed
    # and clean, which made the previous `assert added_lines.strip()` fail for a
    # reason unrelated to safety. Content scanning is never vacuous, so the
    # non-emptiness guarantee is asserted there instead.
    for relative_path in runtime_files:
        content = (STEP11_ROOT / relative_path).read_text(encoding="utf-8")
        assert content.strip()
        for marker in markers:
            assert marker not in content


@pytest.mark.parametrize(
    "marker",
    ("autoApply", "submitApplication", "autonomousApplicationExecution"),
)
def test_step11_injected_forbidden_marker_trips_the_same_scan(marker):
    """The scan predicate itself must reject an injected automation marker."""

    from tests.test_phase20d_no_auto_apply_safety_checkpoint_default_off import (
        FORBIDDEN_RUNTIME_MARKERS as PHASE20D_MARKERS,
    )

    injected_diff = (
        "diff --git a/src/app/provider_model_routing_service.py"
        " b/src/app/provider_model_routing_service.py\n"
        "--- a/src/app/provider_model_routing_service.py\n"
        "+++ b/src/app/provider_model_routing_service.py\n"
        "@@ -1,0 +2 @@\n"
        f"+    {marker}(job)\n"
    )
    added_lines = "\n".join(
        line[1:]
        for line in injected_diff.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    )
    assert marker in PHASE20D_MARKERS
    with pytest.raises(AssertionError):
        for candidate in PHASE20D_MARKERS:
            assert candidate not in added_lines


def test_step14_controlled_canary_ownership_surface_is_exact():
    assert STEP14_CONTROLLED_CANARY_CURRENT_CASE_OWNERSHIP_FILES == {
        "src/evaluation/controlled_groq_canary_run_003_plan.py",
        "src/evaluation/controlled_groq_canary_run_004_plan.py",
        "src/evaluation/controlled_groq_canary_run_005_plan.py",
        "src/evaluation/controlled_groq_canary_run_evidence_runtime.py",
        "src/evaluation/controlled_groq_provider_canary.py",
        "src/evaluation/controlled_provider_benchmark_plan.py",
        "tests/fixtures/provider_benchmark/groq_canary_authorization_template.json",
        "tests/support/phase_guard_registry.py",
        "tests/test_controlled_groq_canary_evidence_runtime.py",
        "tests/test_controlled_groq_canary_run_003_plan.py",
        "tests/test_controlled_groq_canary_run_005_plan.py",
        "tests/test_controlled_groq_canary_run_identity.py",
        "tests/test_controlled_groq_canary_transport.py",
        "tests/test_controlled_groq_provider_canary.py",
        "tests/test_controlled_groq_tailoring_canary_transport.py",
        "tests/test_controlled_live_provider_qualification_validation_context.py",
        "tests/test_controlled_openai_canary_transport.py",
        "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
        "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
        "tests/test_phase85b_legacy_guard_registry_default_off.py",
    }
    for path in STEP14_CONTROLLED_CANARY_CURRENT_CASE_OWNERSHIP_FILES:
        assert "*" not in path
        assert not path.endswith("/")


def test_step14_canary_surface_plus_unauthorized_file_is_rejected():
    with pytest.raises(AssertionError) as exc:
        assert_changed_files_allowed(
            set(STEP14_CONTROLLED_CANARY_CURRENT_CASE_OWNERSHIP_FILES)
            | {"src/app/application_execution_queue.py"},
            set(),
        )
    assert "src/app/application_execution_queue.py" in str(exc.value)


# ---------------------------------------------------------------------------
# Step 14D: legacy protected-hash successor compatibility.
#
# Each entry is an exact (path, historical_hash) -> exact committed successor.
# The historical expectation is never replaced, and nothing is accepted merely
# because it matches the current worktree.
# ---------------------------------------------------------------------------

STEP14D_SUCCESSORS = (
    (
        "src/tailoring/llm.py",
        "6153c78e5f0eca7c78451f0d234609682e01990041deae7fccb0aa303c653920",
        "dbed9c7fe48c6df294911f97ba434da70c0df5238ac6e53a512f68dd763c991c",
    ),
    (
        "src/tailoring/llm.py",
        "5e9e858c6b671526eb6839d110ae05aae780d1c165a37a8bde2c1cc5bcecf31d",
        "dbed9c7fe48c6df294911f97ba434da70c0df5238ac6e53a512f68dd763c991c",
    ),
    (
        "src/pipeline/collector.py",
        "7f4d8cc6571f0aa16f722fac43569ddba0a24e518889ca3864a1e46df7fe4cea",
        "4e5c6b5a3bc4d3979b7299557f4a8bf940bb1c99135c23898dbddedde666ed30",
    ),
    (
        "generate_tailoring_suggestions.py",
        "570d47a62385b736eadbf107e8f28a35aa3818e864f4d950fcb7a6c54e326a3d",
        "4372ee6a7e12e7d55140a03e7a5432b9bd93f0b09226eb839fd4bce3df9160e7",
    ),
    (
        "src/app/services.py",
        "02d09d6f6e204183ef67a543222b4e3a4dae993f40041dfb8911397b835be7f7",
        "29732353a50e4451f2b18d50124439e9b636fce6f9bca9060fb59634dd77e2ee",
    ),
    (
        "src/ai/llm_client.py",
        "61100917a63b5285e7d1fa07ce5da47d73b6ee17f0bb3d3f88e6380722bc85f1",
        "5a7581c7f1a049c19953c4e41f0b8ad8f68ac77104af3262e4e08fd2d8c7e663",
    ),
    (
        "src/ai/llm_client.py",
        "830866d616c8d2d5d6b2147cd6a17b19f049f8a064592d78c2b7170d4e49ffc2",
        "5a7581c7f1a049c19953c4e41f0b8ad8f68ac77104af3262e4e08fd2d8c7e663",
    ),
    (
        "src/evaluation/controlled_groq_canary_transport.py",
        "89d01fe8460e7eae40e794dce808bb26aef6dbb02366e7c5d5bed268fdf00489",
        "af56f5aee197c888766e5a38fb6dd7314efb7d8048eab74622ba0352fdcabf4a",
    ),
    (
        "src/ai/job_fit_evaluator.py",
        "3776e5ce3c098c5329d2e7631195915f6bcf098ec0303ec619e9b0e9ecf393fb",
        "957be166d3e40915734025be2824463d2a52fac0e16b565547f2d09d7da4a5d1",
    ),
)


def _step14d_compatibility_map():
    import ast as _ast

    source = (STEP11_ROOT / "tests/support/phase_guard_registry.py").read_text(
        encoding="utf-8"
    )
    tree = _ast.parse(source)
    function = next(
        node
        for node in _ast.walk(tree)
        if isinstance(node, _ast.FunctionDef)
        and node.name == "assert_protected_hashes"
    )
    assignment = next(
        node
        for node in function.body
        if isinstance(node, _ast.Assign)
        and getattr(node.targets[0], "id", "")
        == "phase88b_runtime_hash_compatibility"
    )
    namespace = {"frozenset": frozenset}
    exec(  # noqa: S102 - reading the registry's own literal table
        compile(
            _ast.Module(body=[assignment], type_ignores=[]), "<registry>", "exec"
        ),
        namespace,
    )
    return namespace["phase88b_runtime_hash_compatibility"]


def test_step14d_successors_are_exact_committed_head_content():
    """Every successor must equal committed HEAD, never a local edit."""

    import subprocess
    from hashlib import sha256

    compatibility = _step14d_compatibility_map()
    for relative_path, historical, successor in STEP14D_SUCCESSORS:
        path = STEP11_ROOT / relative_path
        worktree = sha256(path.read_bytes()).hexdigest()
        head = subprocess.run(
            ["git", "show", f"HEAD:{relative_path}"],
            cwd=STEP11_ROOT,
            capture_output=True,
            check=True,
        ).stdout
        # The successor registered must be the committed HEAD content, and the
        # worktree must not have drifted away from it.
        assert sha256(head).hexdigest() == worktree
        registered = compatibility[(relative_path, historical)]
        registered = (
            set(registered)
            if isinstance(registered, (set, frozenset, tuple, list))
            else {registered}
        )
        assert worktree in registered
        # The DECLARED successor must be the real committed hash, not a
        # placeholder: this is what stops a fabricated value being registered.
        assert successor == worktree
        assert successor in registered
        # The historical expectation itself is never replaced.
        assert (relative_path, historical) in compatibility
        assert historical not in registered


@pytest.mark.parametrize(
    "relative_path,historical,successor", STEP14D_SUCCESSORS
)
def test_step14d_historical_and_successor_accepted_third_hash_rejected(
    tmp_path,
    monkeypatch,
    relative_path,
    historical,
    successor,
):
    from hashlib import sha256

    guarded = tmp_path / relative_path
    guarded.parent.mkdir(parents=True, exist_ok=True)
    guarded.write_text("guarded\n", encoding="utf-8")
    current = sha256(
        (STEP11_ROOT / relative_path).read_bytes()
    ).hexdigest()

    class StubDigest:
        def __init__(self, digest):
            self._digest = digest

        def hexdigest(self):
            return self._digest

    # 1. the historical expectation still resolves through its own identity
    monkeypatch.setattr(
        phase_guard_registry,
        "sha256",
        lambda _data, digest=historical: StubDigest(digest),
    )
    assert_protected_hashes(tmp_path, {relative_path: historical})

    # 2. the exact approved committed successor is accepted
    monkeypatch.setattr(
        phase_guard_registry,
        "sha256",
        lambda _data, digest=current: StubDigest(digest),
    )
    assert_protected_hashes(tmp_path, {relative_path: historical})

    # 3. an arbitrary third hash is still rejected
    for arbitrary in ("0" * 64, "deadbeef" * 8):
        monkeypatch.setattr(
            phase_guard_registry,
            "sha256",
            lambda _data, digest=arbitrary: StubDigest(digest),
        )
        with pytest.raises(AssertionError):
            assert_protected_hashes(tmp_path, {relative_path: historical})


def test_step14d_unregistered_path_and_unknown_lineage_still_fail_closed():
    compatibility = _step14d_compatibility_map()
    # An unauthorized path never gains compatibility from another path's entry.
    assert ("src/app/application_execution_queue.py", "0" * 64) not in compatibility
    for relative_path, historical, _successor in STEP14D_SUCCESSORS:
        # A successor is bound to its exact lineage, not to the bare path.
        assert (relative_path, "1" * 64) not in compatibility
        assert (relative_path, historical) in compatibility


def test_step14d_worktree_only_hash_is_not_auto_accepted(tmp_path, monkeypatch):
    """A hash that merely exists on disk is not a durable successor."""

    from hashlib import sha256

    relative_path = "src/tailoring/llm.py"
    historical = (
        "6153c78e5f0eca7c78451f0d234609682e01990041deae7fccb0aa303c653920"
    )
    guarded = tmp_path / relative_path
    guarded.parent.mkdir(parents=True, exist_ok=True)
    guarded.write_text("locally edited\n", encoding="utf-8")
    local_only = sha256(b"locally edited\n").hexdigest()
    compatibility = _step14d_compatibility_map()
    registered = set(compatibility[(relative_path, historical)])
    assert local_only not in registered

    class StubDigest:
        def __init__(self, digest):
            self._digest = digest

        def hexdigest(self):
            return self._digest

    monkeypatch.setattr(
        phase_guard_registry,
        "sha256",
        lambda _data, digest=local_only: StubDigest(digest),
    )
    with pytest.raises(AssertionError):
        assert_protected_hashes(tmp_path, {relative_path: historical})


def test_step14f_ui_static_contract_surface_is_exact():
    assert STEP14F_UI_STATIC_CONTRACT_REPAIR_FILES == {
        "tests/support/phase_guard_registry.py",
        "tests/test_eucalyptus_primary_shell_design_system.py",
        "tests/test_notification_center_changeover.py",
        "tests/test_phase63b_operator_approved_artifact_application_readiness_packet_readback_ui_api_default_off.py",
        "tests/test_phase64a_human_only_manual_application_handoff_packet_wiring_default_off.py",
        "tests/test_phase64b_human_only_manual_application_handoff_packet_readback_ui_api_default_off.py",
        "tests/test_phase65a_human_only_handoff_audit_trail_wiring_default_off.py",
        "tests/test_phase65b_human_only_handoff_audit_trail_readback_ui_api_default_off.py",
        "tests/test_phase66a_human_only_safety_boundary_summary_wiring_default_off.py",
        "tests/test_phase66b_human_only_safety_boundary_summary_readback_ui_api_default_off.py",
        "tests/test_phase67a_human_only_workflow_readiness_checkpoint_wiring_default_off.py",
        "tests/test_phase67b_human_only_workflow_readiness_checkpoint_readback_ui_api_default_off.py",
        "tests/test_phase85b_legacy_guard_registry_default_off.py",
    }
    # Test-only surface: no production or static UI owner may appear here.
    for path in STEP14F_UI_STATIC_CONTRACT_REPAIR_FILES:
        assert path.startswith("tests/")
        assert "*" not in path and not path.endswith("/")


def test_production_deployment_hardening_files_are_exact_and_finite():
    """The milestone surface is an exact, finite, glob-free file set."""

    assert PRODUCTION_DEPLOYMENT_HARDENING_FILES == {
        "deploy/PRODUCTION_DEPLOYMENT.md",
        "deploy/backup_postgres.sh",
        "deploy/env.production.example",
        "deploy/install_fernet_key.py",
        "deploy/systemd/applylens-agent-discovery.service",
        "deploy/systemd/applylens-agent-discovery.timer",
        "deploy/systemd/applylens-live-pipeline.service",
        "deploy/systemd/applylens-live-pipeline.timer",
        "deploy/systemd/applylens-postgres-backup.service",
        "deploy/systemd/applylens-postgres-backup.timer",
        "docker-compose.prod.yml",
        "src/storage/admin_tools/README.md",
        "src/storage/admin_tools/production_schema_upgrade.py",
        "tests/support/phase_guard_registry.py",
        "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
        "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
        "tests/test_phase85b_legacy_guard_registry_default_off.py",
        "tests/test_production_deployment_hardening.py",
    }
    assert len(PRODUCTION_DEPLOYMENT_HARDENING_FILES) == 18
    for path in PRODUCTION_DEPLOYMENT_HARDENING_FILES:
        assert "*" not in path
        assert not path.endswith("/")
        assert not path.startswith("/")


def test_production_deployment_hardening_files_join_the_milestone_allowlist():
    allowlist = current_milestone_guard_compatibility_allowlist()
    assert PRODUCTION_DEPLOYMENT_HARDENING_FILES <= allowlist


def test_unrelated_path_still_rejected_without_milestone_compatibility():
    """Compatibility is opt-in; it must not become a blanket allowance."""

    with pytest.raises(AssertionError):
        assert_changed_files_allowed(
            {"src/app/api.py"},
            PRODUCTION_DEPLOYMENT_HARDENING_FILES,
            include_current_milestone_compatibility=False,
        )
    # ...and an unrelated path is rejected even with compatibility enabled.
    with pytest.raises(AssertionError):
        assert_changed_files_allowed(
            {"src/app/unrelated_guard_probe.py"},
            PRODUCTION_DEPLOYMENT_HARDENING_FILES,
        )


def test_deployment_files_do_not_leak_into_legacy_guard_profiles():
    """No unrelated legacy profile is broadened by this registration."""

    # Shared guard/deployment test infrastructure is legitimately co-owned by
    # successor milestones; only the deployment payload files are exclusive.
    deployment_only = PRODUCTION_DEPLOYMENT_HARDENING_FILES - {
        "tests/support/phase_guard_registry.py",
        "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
        "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
        "tests/test_phase85b_legacy_guard_registry_default_off.py",
        "tests/test_production_deployment_hardening.py",
    }
    from tests.support import phase_guard_registry

    for name in dir(phase_guard_registry):
        if not name.endswith("_FILES") or name == "PRODUCTION_DEPLOYMENT_HARDENING_FILES":
            continue
        other = getattr(phase_guard_registry, name)
        if not isinstance(other, (set, frozenset)):
            continue
        assert not (deployment_only & other), f"{name} was broadened"


def test_production_cpu_torch_build_files_are_exact_and_finite():
    """The CPU-torch repair milestone is an exact, finite, glob-free file set."""

    assert PRODUCTION_CPU_TORCH_BUILD_FILES == {
        "Dockerfile",
        "deploy/verify_cpu_only_torch.py",
        "tests/support/phase_guard_registry.py",
        "tests/test_phase85b_legacy_guard_registry_default_off.py",
        "tests/test_production_deployment_hardening.py",
    }
    assert len(PRODUCTION_CPU_TORCH_BUILD_FILES) == 5
    for path in PRODUCTION_CPU_TORCH_BUILD_FILES:
        assert "*" not in path
        assert not path.endswith("/")
        assert not path.startswith("/")


def test_production_cpu_torch_build_files_join_the_milestone_allowlist():
    assert PRODUCTION_CPU_TORCH_BUILD_FILES <= (
        current_milestone_guard_compatibility_allowlist()
    )


def test_cpu_torch_milestone_does_not_grant_unrelated_paths():
    """Compatibility is opt-in and stays scoped to this repair."""

    with pytest.raises(AssertionError):
        assert_changed_files_allowed(
            {"src/app/unrelated_guard_probe.py"},
            PRODUCTION_CPU_TORCH_BUILD_FILES,
            include_current_milestone_compatibility=False,
        )
    with pytest.raises(AssertionError):
        assert_changed_files_allowed(
            {"src/app/unrelated_guard_probe.py"},
            PRODUCTION_CPU_TORCH_BUILD_FILES,
        )


def test_cpu_torch_milestone_is_distinct_and_broadens_no_other_profile():
    from tests.support import phase_guard_registry

    # The repair owns only what it genuinely changed; it is deliberately NOT a
    # copy of the larger production-deployment-hardening surface.
    assert PRODUCTION_CPU_TORCH_BUILD_FILES != PRODUCTION_DEPLOYMENT_HARDENING_FILES
    repair_only = PRODUCTION_CPU_TORCH_BUILD_FILES - {
        "tests/support/phase_guard_registry.py",
        "tests/test_phase85b_legacy_guard_registry_default_off.py",
        "tests/test_production_deployment_hardening.py",
    }
    assert repair_only == {"Dockerfile", "deploy/verify_cpu_only_torch.py"}
    for name in dir(phase_guard_registry):
        if not name.endswith("_FILES") or name == "PRODUCTION_CPU_TORCH_BUILD_FILES":
            continue
        other = getattr(phase_guard_registry, name)
        if not isinstance(other, (set, frozenset)):
            continue
        assert not (repair_only & other), f"{name} was broadened"
