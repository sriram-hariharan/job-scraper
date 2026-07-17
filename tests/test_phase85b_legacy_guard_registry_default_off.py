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

    assert current_milestone_guard_compatibility_allowlist() == (
        legacy_guard_allowlist("policy_driven_llm_adjudicator_readback")
        | legacy_guard_allowlist("phase129b_auth_loader_ui")
        | phase129_profile
        | phase132_profile
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

    for forbidden_path in (
        "src/matching/scorer.py",
        "requirements.txt",
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
