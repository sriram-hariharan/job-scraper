from pathlib import Path

import pytest

from tests.support.phase_guard_registry import (
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


def test_current_milestone_guard_compatibility_is_exact_registered_surface():
    phase129_profile = legacy_guard_allowlist(
        "phase129c_workflow_overlay_and_run_scoped_corpus"
    )
    phase132_profile = legacy_guard_allowlist("phase132b_premium_preferences_ui")
    phase133_profile = legacy_guard_allowlist("phase133a_executive_kpi_react_island")
    phase133b_profile = legacy_guard_allowlist("phase133b_executive_queue_react_island")
    phase133d_profile = legacy_guard_allowlist("phase133d_pipeline_dashboard_react_island")
    phase133g_profile = legacy_guard_allowlist("phase133g_premium_planning_dashboard")
    phase133ef_profile = legacy_guard_allowlist("phase133ef_decisions_applications_dashboards")
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
        legacy_guard_allowlist("policy_driven_llm_adjudicator_readback")
        | legacy_guard_allowlist("phase129b_auth_loader_ui")
        | phase129_profile
        | phase132_profile
        | phase133_profile
        | phase133b_profile
        | phase133d_profile
        | phase133g_profile
        | phase133ef_profile
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
        | phase9_step12_compatibility_profile
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
