from pathlib import Path


REVIEW_JS_PATH = Path("src/app/static/agentic_review.js")


def _source() -> str:
    return REVIEW_JS_PATH.read_text(encoding="utf-8")


def _section_snippet() -> str:
    source = _source()
    start = source.index(
        "function renderPipelineGeneratedAgentRecommendationOverlayReadinessSummarySection"
    )
    end = source.index("function renderAgentRecommendationOverlaySection", start)
    return source[start:end]


def _request_snippet() -> str:
    source = _source()
    start = source.index(
        "function pipelineGeneratedAgentRecommendationOverlayReadinessSummaryRequestPayload"
    )
    end = source.index("function renderHumanReviewedInfluencePreviewSection", start)
    return source[start:end]


def _handler_snippet() -> str:
    source = _source()
    start = source.index(
        'event.target.closest("[data-pipeline-generated-agent-recommendation-overlay-readiness-summary]")'
    )
    end = source.index(
        'event.target.closest("[data-manual-shadow-recommendation-handoff-dry-run]")',
        start,
    )
    return source[start:end]


def _init_snippet() -> str:
    source = _source()
    start = source.index("async function initAgenticReviewPage")
    end = source.index(
        'window.addEventListener("DOMContentLoaded", initAgenticReviewPage);'
    )
    return source[start:end]


def test_ui_includes_readiness_summary_fetch_and_display_hook():
    source = _source()
    section = _section_snippet()
    handler = _handler_snippet()

    assert (
        "function renderPipelineGeneratedAgentRecommendationOverlayReadinessSummarySection"
        in source
    )
    assert "Pipeline-generated Overlay Readiness" in section
    assert (
        "data-pipeline-generated-agent-recommendation-overlay-readiness-summary"
        in section
    )
    assert "Check Overlay Readiness" in section
    assert (
        "renderPipelineGeneratedAgentRecommendationOverlayReadinessSummarySection(tracePayload)"
        in source
    )
    assert 'method: "POST"' in handler
    assert "readinessApiPath" in handler
    assert '"readiness"' in handler
    assert '"summary"' in handler


def test_ui_builds_readonly_request_from_existing_readback_and_trace_shapes():
    snippet = _request_snippet()

    assert "overlay_readback_payload" in snippet
    assert (
        "pipeline_generated_agent_recommendation_overlay_readback_result"
        in snippet
    )
    assert "pipelineGeneratedAgentRecommendationOverlayReadbackRequestPayload" in snippet
    assert "fetchJson" not in snippet
    assert "setInterval" not in snippet


def test_ui_displays_ready_and_partial_reviewable_states():
    snippet = _section_snippet()

    assert "overlay_ready" in snippet
    assert "ready for operator review" in snippet
    assert "overlay_partial_reviewable" in snippet
    assert "safe partial overlay is available and reviewable" in snippet
    assert "warning, not a failure" in snippet


def test_ui_displays_missing_blocked_failed_and_disabled_states_safely():
    snippet = _section_snippet()

    assert "overlay_not_found" in snippet
    assert "No pipeline-generated overlay was found" in snippet
    assert "overlay_blocked" in snippet
    assert "readiness is blocked" in snippet
    assert "overlay_failed_non_blocking" in snippet
    assert "failed non-blocking" in snippet
    assert "overlay_disabled" in snippet
    assert "auto-generation was disabled" in snippet


def test_ui_labels_output_advisory_readonly_and_no_mutation():
    snippet = _section_snippet()
    required = [
        "Advisory read-only",
        "advisory read-only",
        "read_only",
        "advisory_only",
        "did_mutate_scoring",
        "did_change_ranking",
        "did_mutate_queue",
        "did_mutate_approval",
        "did_mutate_resume",
        "did_create_execution_request",
        "did_create_execution_launch_request",
        "did_execute_application",
        "did_submit_application",
        "does not change score, ranking, queue, approval, resume, execution, or submission state",
    ]
    for phrase in required:
        assert phrase in snippet


def test_ui_adds_no_mutation_override_or_execution_controls():
    combined = _section_snippet() + "\n" + _handler_snippet()
    forbidden = [
        "data-approve",
        "data-reject",
        "data-submit",
        "data-execute",
        "data-ranking-override",
        "data-scoring-override",
        "data-queue",
        "data-resume",
        "setAgenticApprovalStatus",
        "approve-application",
        "submit-application",
        "execute-application",
        "/api/manual-guarded",
        "/api/manual-approval",
        "/api/manual-queue",
        "/api/manual-execution",
        "execute_application(",
        "submit_application(",
        "create_approval_request(",
        "create_execution_request(",
        "create_execution_launch_request(",
    ]
    combined_lower = combined.lower()
    for marker in forbidden:
        assert marker.lower() not in combined_lower


def test_ui_calls_readiness_only_from_explicit_action_without_provider_trigger():
    source = _source()
    handler = _handler_snippet()
    init_snippet = _init_snippet()

    assert "readinessApiPath" in handler
    assert "readinessApiPath" not in init_snippet
    assert "setInterval" not in handler
    assert "setInterval" not in init_snippet
    assert "provider" not in handler.lower()
    assert "run_llm" not in source
    assert "model_client" not in source
    assert "responses.create" not in source
    assert "chat.completions.create" not in source


def test_no_backend_pipeline_or_schema_wiring_for_readiness_ui():
    markers = [
        "renderPipelineGeneratedAgentRecommendationOverlayReadinessSummarySection",
        "data-pipeline-generated-agent-recommendation-overlay-readiness-summary",
        "pipeline_generated_agent_recommendation_overlay_readiness_summary_result",
    ]
    protected_paths = [
        Path("src/app/api.py"),
        Path("src/app/services.py"),
        Path("src/pipeline/collector.py"),
        Path("src/storage/agent_trace/schema.sql"),
        Path("src/storage/agentic_approvals/schema.sql"),
    ]
    combined = "\n".join(
        path.read_text(encoding="utf-8") for path in protected_paths
    )

    for marker in markers:
        assert marker not in combined
    assert Path("src/pipeline/collector.py").read_text(
        encoding="utf-8"
    ).count("run_shadow_sidecar_pipeline_hook(") == 1


def test_provider_backed_and_mutation_authorized_agents_remain_zero():
    api_source = Path("src/app/api.py").read_text(encoding="utf-8")
    route_start = api_source.index(
        "def pipeline_generated_agent_recommendation_overlay_readiness_summary("
    )
    route_end = api_source.index(
        '@app.get("/profile/pipeline-runs/{run_id}/agentic-review-data")',
        route_start,
    )
    route_source = api_source[route_start:route_end]

    assert '"live_provider_backed_automated_agents": 0' in route_source
    assert '"mutation_authorized_agents": 0' in route_source
