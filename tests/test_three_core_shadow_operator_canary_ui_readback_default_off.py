from pathlib import Path


JS_PATH = Path("src/app/static/agentic_review.js")


def _renderer() -> str:
    source = JS_PATH.read_text(encoding="utf-8")
    start = source.index(
        "function renderThreeCoreShadowOperatorCanaryReadbackSection"
    )
    end = source.index(
        "\nfunction renderHumanReviewedInfluencePreviewSection", start
    )
    return source[start:end]


def test_ui_has_passive_three_core_canary_readback_renderer():
    source = JS_PATH.read_text(encoding="utf-8")
    snippet = _renderer()

    assert "Three-Core Shadow Operator Canary" in snippet
    assert "three_core_shadow_operator_canary_readback_result" in snippet
    assert 'renderWorkflowSummaryMetric("Canary status"' in snippet
    assert 'renderWorkflowSummaryMetric("Readback status"' in snippet
    assert 'renderWorkflowSummaryMetric("Readback complete"' in snippet
    assert 'renderWorkflowSummaryMetric("Ordered agents"' in snippet
    assert 'renderWorkflowSummaryMetric("Shadow result count"' in snippet
    assert 'renderWorkflowSummaryMetric("Next safe step"' in snippet
    assert "data-three-core-shadow-operator-canary-safety-summary" in snippet
    assert (
        "renderThreeCoreShadowOperatorCanaryReadbackSection(tracePayload)"
        in source
    )


def test_ui_only_renders_when_a_supplied_payload_is_present():
    snippet = _renderer()

    assert 'if (!Object.keys(result).length) return "";' in snippet
    assert "Passive read-only display of a supplied canary payload." in snippet


def test_ui_renderer_adds_no_action_control_or_api_call():
    snippet = _renderer().lower()

    for marker in (
        "<button",
        "<input",
        "fetch(",
        "fetchjson(",
        "/api/",
        "data-apply",
        "data-submit",
        "data-execute",
        "data-approval",
        "createapproval",
        "executeapplication",
        "submitapplication",
    ):
        assert marker not in snippet


def test_ui_renderer_shows_no_mutation_safety_flags():
    snippet = _renderer()

    for marker in (
        "pipeline_not_connected",
        "did_mutate_scoring",
        "did_change_ranking",
        "did_mutate_queue",
        "did_execute_application",
        "did_submit_application",
        "Safety metadata",
    ):
        assert marker in snippet
