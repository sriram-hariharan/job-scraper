from pathlib import Path


JS_PATH = Path("src/app/static/agentic_review.js")


def _source() -> str:
    return JS_PATH.read_text(encoding="utf-8")


def _snippet(start_marker: str, end_marker: str) -> str:
    source = _source()
    start = source.index(start_marker)
    end = source.index(end_marker, start)
    return source[start:end]


def _fixture_helpers() -> str:
    return _snippet(
        "function shouldRenderThreeCoreShadowOperatorCanaryFixture",
        "\nfunction renderThreeCoreShadowOperatorCanaryReadbackSection",
    )


def test_fixture_query_gate_is_explicit_and_default_off():
    snippet = _fixture_helpers()

    assert 'new URLSearchParams(query)' in snippet
    assert '.get("three_core_canary_fixture") === "1"' in snippet
    assert 'window.location.search' in snippet
    assert "search = null" in snippet


def test_fixture_payload_is_deterministic_completed_readback():
    snippet = _fixture_helpers()

    assert "function buildThreeCoreShadowOperatorCanaryFixtureResult" in snippet
    assert '"three_core_shadow_operator_canary_completed"' in snippet
    assert '"three_core_shadow_runtime_readback_completed"' in snippet
    assert "readback_completion: true" in snippet
    assert '"relevance_prefilter"' in snippet
    assert '"jd_intelligence"' in snippet
    assert '"final_application_scoring"' in snippet
    assert "shadow_result_count: 3" in snippet
    assert (
        '"review_three_core_shadow_operator_canary_before_api_or_ui_readback"'
        in snippet
    )


def test_fixture_does_not_overwrite_real_canary_readback():
    snippet = _fixture_helpers()

    assert (
        "source.three_core_shadow_operator_canary_readback_result"
        in snippet
    )
    assert "return source;" in snippet
    assert (
        "three_core_shadow_operator_canary_readback_result:"
        in snippet
    )


def test_fixture_safety_paths_are_false():
    snippet = _fixture_helpers()

    for marker in (
        "provider_calls_made: false",
        "network_calls_made: false",
        "did_read_database: false",
        "did_write_database: false",
        "did_read_files: false",
        "did_write_files: false",
        "did_mutate_scoring: false",
        "did_change_ranking: false",
        "did_mutate_queue: false",
        "did_create_approval: false",
        "did_mutate_approval: false",
        "did_mutate_resume: false",
        "did_create_execution_request: false",
        "did_create_execution_launch_request: false",
        "did_execute_application: false",
        "did_submit_application: false",
        "mutation_authorized: false",
    ):
        assert marker in snippet


def test_trace_render_path_uses_fixture_enriched_payload():
    source = _source()
    panel = _snippet(
        "function renderAgentTraceReadOnlyPanel",
        "\nfunction renderAgentTracePanel",
    )

    assert "withThreeCoreShadowOperatorCanaryFixture(tracePayload)" in panel
    assert (
        "renderThreeCoreShadowOperatorCanaryReadbackSection("
        "fixtureVisibleTracePayload)"
        in panel
    )
    assert "Local fixture preview" in source


def test_fixture_helpers_add_no_controls_calls_or_actions():
    snippet = _fixture_helpers().lower()

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
