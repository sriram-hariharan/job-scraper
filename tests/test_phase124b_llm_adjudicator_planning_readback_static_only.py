from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLANNING_JS = ROOT / "src/app/static/planning.js"


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


def test_planning_row_renders_existing_readback_without_new_column():
    source = _source()
    recommendation = _function_block("buildPlanningRecommendationCellHtml")
    renderer = _function_block("buildLlmAdjudicatorReadbackHtml")

    assert "buildLlmAdjudicatorReadbackHtml(row)" in recommendation
    assert "AI review notes" in renderer
    assert "LLM adjudicator readback" not in renderer
    assert "<details" not in renderer
    assert "buildRecommendationDetailsHtml" in renderer
    assert 'colspan="8"' in source


def test_readback_is_hidden_when_missing_disabled_or_not_enabled():
    enabled = _function_block("isLlmAdjudicatorReadbackEnabled")
    renderer = _function_block("buildLlmAdjudicatorReadbackHtml")

    assert '["true", "1", "yes", "on"]' in enabled
    assert "if (!isLlmAdjudicatorReadbackEnabled" in renderer
    assert 'if (rowStatus === "disabled") return "";' in renderer
    assert 'if (!hasEnabledState) return "";' in renderer


def test_readback_parsing_is_defensive_and_errors_are_safe():
    parser = _function_block("parseLlmAdjudicatorReadback")
    renderer = _function_block("buildLlmAdjudicatorReadbackHtml")

    assert "JSON.parse(raw)" in parser
    assert "catch" in parser
    assert "return null" in parser
    for status in ["provider_error", "malformed_response", "unavailable"]:
        assert status in renderer
    assert "Readback unavailable. The deterministic selection remains unchanged." in renderer
    assert "readback?.error" not in renderer
    assert "raw_response_preview" not in renderer


def test_readback_renders_compact_escaped_fields_and_safety_copy():
    renderer = _function_block("buildLlmAdjudicatorReadbackHtml")
    details = _function_block("buildRecommendationDetailsHtml")

    for marker in [
        "provider_used",
        "provider_requested",
        "model_used",
        "model_requested",
        "candidate_resume_names",
        "candidate_scores",
        "adjudicator_recommendation_label",
        "adjudicator_summary",
    ]:
        assert marker in renderer
    assert "Advisory only. Does not override the selected resume or score." in renderer
    assert "escapeHtml(item.label)" in details
    assert "escapeHtml(item.value)" in details


def test_readback_renderer_has_no_fetch_provider_or_mutation_trigger():
    parser = _function_block("parseLlmAdjudicatorReadback")
    renderer = _function_block("buildLlmAdjudicatorReadbackHtml")
    combined = parser + renderer

    for forbidden in [
        "fetch(",
        "postJson(",
        "run_chat_completion",
        "Groq",
        "OPENAI",
        "application_status",
        "winner_resume =",
        "resolved_resume =",
        "final_score =",
        "operator_decision =",
        "tailoring_json =",
    ]:
        assert forbidden not in combined


def test_phase124b_does_not_change_protected_runtime_surfaces():
    readback_markers = (
        "planning-llm-adjudicator-readback",
        "buildLlmAdjudicatorReadbackHtml",
    )
    for relative in [
        "src/app/api.py",
        "src/app/services.py",
        "src/pipeline/collector.py",
        "batch_select_best_resume_variant.py",
        "src/agents/llm_adjudicator_readback.py",
        "src/matching/scorer.py",
    ]:
        source = (ROOT / relative).read_text(encoding="utf-8")
        assert all(marker not in source for marker in readback_markers), relative
