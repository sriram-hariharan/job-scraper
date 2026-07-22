from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLANNING_JS = ROOT / "src/app/static/planning.js"
DEMO_DOC = ROOT / "docs/demo_walkthrough.md"


def _source() -> str:
    return PLANNING_JS.read_text(encoding="utf-8")


def _function_block(name: str) -> str:
    source = _source()
    start = source.index(f"function {name}")
    brace = source.index("{", start)
    depth = 0
    for index in range(brace, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[start : index + 1]
    raise AssertionError(f"Could not locate function body for {name}")


def test_ai_review_uses_human_facing_advisory_copy():
    renderer = _function_block("buildLlmAdjudicatorReadbackHtml")

    assert "AI review notes · advisory" in renderer
    assert "LLM adjudicator readback" not in renderer
    assert "Advisory only. Does not override the selected resume or score." in renderer
    assert "AI review notes" in DEMO_DOC.read_text(encoding="utf-8")


def test_recommendation_and_ai_review_have_distinct_disclosure_labels():
    details = _function_block("buildRecommendationDetailsHtml")
    recommendation = _function_block("buildPlanningRecommendationCellHtml")
    details_panel = _function_block("buildPlanningRowDetailsHtml")
    renderer = _function_block("buildLlmAdjudicatorReadbackHtml")

    assert 'summaryLabel = "Why?"' in details
    assert "escapeHtml(summaryLabel)" in details
    assert "buildPlanningAdvisoryIndicatorHtml(row)" in recommendation
    assert "buildLlmAdjudicatorReadbackHtml(row)" in details_panel
    assert '], "View AI review");' in renderer


def test_machine_statuses_are_mapped_to_safe_display_labels():
    formatter = _function_block("formatLlmAdjudicatorReadbackStatus")
    renderer = _function_block("buildLlmAdjudicatorReadbackHtml")

    assert 'status === "ok"' in formatter
    assert 'return "Ready"' in formatter
    for status in ("provider_error", "malformed_response", "unavailable"):
        assert status in formatter
    assert 'return "Unavailable"' in formatter
    assert "formatLlmAdjudicatorReadbackStatus(status)" in renderer


def test_candidate_scores_use_existing_percentage_formatter():
    renderer = _function_block("buildLlmAdjudicatorReadbackHtml")

    assert "formatScore100(score)" in renderer
    assert "String(score)" not in renderer


def test_missing_disabled_and_malformed_readback_remain_safe():
    parser = _function_block("parseLlmAdjudicatorReadback")
    renderer = _function_block("buildLlmAdjudicatorReadbackHtml")

    assert "JSON.parse(raw)" in parser
    assert "catch" in parser
    assert 'if (!isLlmAdjudicatorReadbackEnabled' in renderer
    assert 'if (rowStatus === "disabled") return "";' in renderer
    assert '"malformed_response"' in renderer
    assert "Readback unavailable. The deterministic selection remains unchanged." in renderer
    assert "readback?.error" not in renderer
    assert "raw_response_preview" not in renderer


def test_display_values_remain_escaped_and_no_action_trigger_is_added():
    details = _function_block("buildRecommendationDetailsHtml")
    renderer = _function_block("buildLlmAdjudicatorReadbackHtml")
    combined = details + renderer

    assert "escapeHtml(item.label)" in details
    assert "escapeHtml(item.value)" in details
    assert "escapeHtml(summaryLabel)" in details
    for forbidden in (
        "fetch(",
        "postJson(",
        "run_chat_completion",
        "Groq",
        "application_status",
        "winner_resume =",
        "resolved_resume =",
        "final_score =",
        "operator_decision =",
        "tailoring_json =",
        "ATS",
    ):
        assert forbidden not in combined


def test_phase126b_protected_runtime_surfaces_have_no_ui_copy_markers():
    markers = ("AI review notes · advisory", "formatLlmAdjudicatorReadbackStatus")
    for relative in (
        "src/app/api.py",
        "src/app/services.py",
        "src/pipeline/collector.py",
        "batch_select_best_resume_variant.py",
        "src/agents/llm_adjudicator_readback.py",
        "src/matching/scorer.py",
    ):
        source = (ROOT / relative).read_text(encoding="utf-8")
        assert all(marker not in source for marker in markers), relative
