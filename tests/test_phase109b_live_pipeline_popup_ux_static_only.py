# phase109b legacy guard marker: changes_only live_pipeline_popup_ux_static_only d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004 src/app/api.py
from __future__ import annotations

from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
UI_PATH = ROOT / "src/app/ui.py"
APP_JS_PATH = ROOT / "src/app/static/app.js"
CSS_PATH = ROOT / "src/app/static/app_redesign.css"


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _between(source: str, start: str, end: str) -> str:
    start_index = source.index(start)
    end_index = source.index(end, start_index)
    return source[start_index:end_index]


def _pipeline_modal_html() -> str:
    return _between(
        _source(UI_PATH),
        '<section class="modal-backdrop hidden" id="pipelineConfigModal">',
        '<section class="modal-backdrop hidden" id="pipelineConfirmModal">',
    )


def _pipeline_confirm_source() -> str:
    return _between(
        _source(APP_JS_PATH),
        "function renderPipelineConfirmSummary(config)",
        "function stopPipelinePolling()",
    )


def _collect_pipeline_config_source() -> str:
    return _between(
        _source(APP_JS_PATH),
        "function collectPipelineConfig()",
        "function renderPipelineConfirmSummary(config)",
    )


def test_live_pipeline_popup_uses_demo_friendly_sections_and_labels():
    modal = _pipeline_modal_html()

    for label in [
        "Run size",
        "Job limit",
        "Packet limit",
        "Rerun seen jobs",
        "Run mode",
        "Scan + Plan",
        "Plan only",
        "AI planning",
        "AI review",
        "Advanced",
        "Backup ranking",
    ]:
        assert label in modal


def test_live_pipeline_popup_has_short_helper_icons_and_text():
    modal = _pipeline_modal_html()

    for helper in [
        "Maximum jobs allowed into this run.",
        "Maximum detailed planning packets to build. 0 means all selected jobs.",
        "Include jobs that were already seen before.",
        "Scrape jobs, score them, and build planning outputs.",
        "Skip scraping and rebuild planning from existing jobs.",
        "Use AI to review planning decisions and borderline fits. This does not tailor resumes.",
        "Use fallback ranking when normal ranking signals are incomplete.",
    ]:
        assert f'title="{helper}"' in modal
        assert f'aria-label="{helper}"' in modal

    assert modal.count("pipeline-help-icon") >= 7


def test_live_pipeline_popup_does_not_render_internal_or_tailoring_controls():
    modal = _pipeline_modal_html()

    for forbidden in [
        "LLM ACTIONS",
        "APPLY_REVIEW_VARIANTS",
        "MAYBE_TAILOR",
        "SKIP_FOR_NOW",
        "Generate tailoring",
        "Generate LLM tailoring",
        "Refresh LLM tailoring",
        "Generate LLM fallback",
        "Generate LLM adjudication",
        "Refresh AI cache",
        "Evidence trace",
        "LangGraph trace",
    ]:
        assert forbidden not in modal

    assert "data-pipeline-llm-action-toggle" not in modal
    assert 'name="pipelineGenerateTailoring"' not in modal
    assert 'name="pipelineGenerateLlmTailoring"' not in modal
    assert 'name="pipelineRefreshLlmTailoring"' not in modal


def test_pipeline_payload_keeps_backend_fields_without_exposing_removed_controls():
    source = _collect_pipeline_config_source()

    assert "getDefaultPipelineLlmActions()" in source
    assert "llm_actions: effectiveLlmActions" in source
    assert re.search(r"generate_tailoring:\s*false", source)
    assert re.search(r"generate_llm_tailoring:\s*false", source)
    assert re.search(r"refresh_llm_tailoring:\s*false", source)
    assert "generate_llm_fallback: getBinaryToggleBool(\"pipelineGenerateLlmFallback\")" in source
    assert (
        "generate_llm_adjudication: getBinaryToggleBool(\"pipelineGenerateLlmAdjudication\")"
        in source
    )
    assert "delete_seen_data: getPipelineDeleteSeenDataValue()" in source
    assert "evidence" not in source.lower()
    assert "langgraph" not in source.lower()
    assert "trace_persistence" not in source


def test_confirm_summary_uses_user_facing_labels_not_internal_buckets():
    source = _pipeline_confirm_source()

    for label in ["Run mode", "Scan + Plan", "Plan only", "Rerun seen jobs", "AI review", "Backup ranking"]:
        assert label in source

    for forbidden in [
        "LLM actions",
        "Generate tailoring",
        "Generate LLM tailoring",
        "Refresh LLM tailoring",
        "Generate LLM fallback",
        "Generate LLM adjudication",
        "APPLY_REVIEW_VARIANTS",
        "MAYBE_TAILOR",
        "SKIP_FOR_NOW",
    ]:
        assert forbidden not in source


def test_phase109b_adds_only_ui_static_and_focused_test_files():
    changed = set(
        subprocess.check_output(
            ["git", "diff", "--name-only"],
            cwd=ROOT,
            text=True,
        ).splitlines()
    )
    changed.update(
        subprocess.check_output(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=ROOT,
            text=True,
        ).splitlines()
    )

    allowed = {
        "src/app/ui.py",
        "src/app/static/app.js",
        "src/app/static/app_redesign.css",
        "src/app/static/styles.css",
        "tests/test_phase109b_live_pipeline_popup_ux_static_only.py",
        "tests/support/phase_guard_registry.py",
        "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
        "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
        "tests/test_phase104b_critic_controlled_llm_ownership_default_off.py",
        "tests/test_phase105b_critic_controlled_llm_manual_runtime_wiring_default_off.py",
    }
    assert changed <= allowed
    assert "src/app/api.py" not in changed
    assert "src/app/services.py" not in changed
    assert "src/pipeline/collector.py" not in changed


def test_pipeline_modal_uses_existing_compact_helper_icon_only():
    modal = _pipeline_modal_html()

    assert modal.count("packet-info-icon pipeline-help-icon") >= 7
    assert "data-popover" not in modal
    assert "position: fixed" not in modal
