from pathlib import Path

import pytest

from tests.support.phase_guard_registry import (
    assert_changed_files_allowed,
    assert_false_safety_metadata_allowed_but_real_mutation_blocked,
    assert_no_forbidden_runtime_calls_ast,
    assert_protected_hashes,
    duplicate_artifact_paths,
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
            {"src/pipeline/collector.py", "tests/test_allowed.py"},
            {"tests/test_allowed.py"},
        )

    assert "src/pipeline/collector.py" in str(exc.value)
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
        },
        set(),
        legacy_guard_profiles=("config_vocabulary_scoring_change",),
    )

    for forbidden_path in (
        "src/app/services.py",
        "src/pipeline/collector.py",
        "src/matching/scorer.py",
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
            )


def test_active_ts_clearance_diagnostic_profile_is_narrow():
    assert_changed_files_allowed(
        {
            "src/matching/clearance_requirements.py",
            "tests/test_phase117b_ts_clearance_diagnostic.py",
        },
        set(),
        legacy_guard_profiles=("active_ts_clearance_diagnostic",),
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
