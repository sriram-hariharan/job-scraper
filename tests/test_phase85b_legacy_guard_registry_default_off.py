from pathlib import Path

import pytest

from tests.support.phase_guard_registry import (
    BROAD_TECH_PREFILTER_TAXONOMY_FILES,
    HIMALAYAS_STEP2B_LOCATION_COVERAGE_FILES,
    HIMALAYAS_STEP6B1_ATTRIBUTION_FOUNDATION_FILES,
    HIMALAYAS_STEP6B2_SOURCE_INTEGRATION_FILES,
    HIMALAYAS_STEP6C1_PAGINATION_REPAIR_FILES,
    HIMALAYAS_STEP6D_B1_RETENTION_FOUNDATION_FILES,
    HIMALAYAS_STEP6D_B2_RETENTION_INTEGRATION_FILES,
    HIMALAYAS_STEP6D_C_SOURCE_RETIREMENT_FILES,
    HIMALAYAS_STEP6E_R1_LOCATION_ACTIVATION_FILES,
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
    PERSONIO_SOURCE_INTEGRATION_FILES,
    RECRUITEE_SOURCE_INTEGRATION_FILES,
    SCRAPER_PREFILTER_OWNERSHIP_BOUNDARY_FILES,
    SCRAPER_SOURCE_HEALTH_METRICS_FILES,
    SMARTRECRUITERS_PAGINATION_FILES,
    SCRAPER_TRANSPORT_PAGINATION_HARDENING_FILES,
    SOURCE_YIELD_UI_FILES,
    JOBVITE_LOCATION_FRESHNESS_FILES,
    USAJOBS_SOURCE_INTEGRATION_FILES,
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


def test_personio_source_integration_surface_is_exact():
    assert PERSONIO_SOURCE_INTEGRATION_FILES == {
        "src/config/consts.py",
        "src/config/curated_ats_sources.json",
        "src/discovery/curated_ats_sources.py",
        "src/pipeline/collector.py",
        "src/scrapers/personio_scraper.py",
        "tests/support/phase_guard_registry.py",
        "tests/test_curated_ats_sources.py",
        "tests/test_personio_scraper.py",
        "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
        "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
        "tests/test_phase85b_legacy_guard_registry_default_off.py",
        "tests/test_scraper_prefilter_ownership_boundary.py",
        "tests/test_scraper_source_health_metrics.py",
        "tests/test_scraper_transport_pagination_hardening.py",
    }
    assert not any("*" in path for path in PERSONIO_SOURCE_INTEGRATION_FILES)


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
    smartrecruiters_pagination_profile = legacy_guard_allowlist(
        "smartrecruiters_pagination"
    )
    assert smartrecruiters_pagination_profile == SMARTRECRUITERS_PAGINATION_FILES
    assert not any("*" in path for path in smartrecruiters_pagination_profile)
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

    assert current_milestone_guard_compatibility_allowlist() == (
        smartrecruiters_pagination_profile
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
        | PERSONIO_SOURCE_INTEGRATION_FILES
        | RECRUITEE_SOURCE_INTEGRATION_FILES
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


def test_assert_protected_hashes_detects_hash_mismatch(tmp_path):
    path = tmp_path / "guarded.py"
    path.write_text("print('safe')\n", encoding="utf-8")

    with pytest.raises(AssertionError) as exc:
        assert_protected_hashes(tmp_path, {"guarded.py": "0" * 64})

    message = str(exc.value)
    assert "guarded.py" in message
    assert "expected" in message
    assert "got" in message


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
