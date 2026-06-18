from pathlib import Path


REVIEW_JS_PATH = Path("src/app/static/agentic_review.js")


def _source() -> str:
    return REVIEW_JS_PATH.read_text(encoding="utf-8")


def _section_snippet() -> str:
    source = _source()
    start = source.index(
        "function renderPipelineGeneratedOverlayReviewPacketSection"
    )
    end = source.index("function renderAgentRecommendationOverlaySection", start)
    return source[start:end]


def _request_snippet() -> str:
    source = _source()
    start = source.index(
        "function pipelineGeneratedOverlayReviewPacketRequestPayload"
    )
    end = source.index("function renderHumanReviewedInfluencePreviewSection", start)
    return source[start:end]


def _handler_snippet() -> str:
    source = _source()
    start = source.index(
        'event.target.closest("[data-pipeline-generated-overlay-review-packet]")'
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


def test_ui_includes_review_packet_fetch_and_display_hook():
    source = _source()
    section = _section_snippet()
    handler = _handler_snippet()

    assert "function renderPipelineGeneratedOverlayReviewPacketSection" in source
    assert "Pipeline Agent Review Packet" in section
    assert "data-pipeline-generated-overlay-review-packet" in section
    assert "Build Review Packet" in section
    assert "renderPipelineGeneratedOverlayReviewPacketSection(tracePayload)" in source
    assert 'method: "POST"' in handler
    assert "reviewPacketApiPath" in handler
    assert '"/api/pipeline"' in handler
    assert '"agent"' in handler
    assert '"review"' in handler
    assert '"packet"' in handler


def test_ui_builds_packet_request_from_existing_readonly_payloads():
    snippet = _request_snippet()

    required = [
        "overlay_readback_payload",
        "overlay_payload",
        "pipeline_generated_overlay_payload",
        "agent_recommendation_overlay_payload",
        "trace_context_payload",
        "pipelineGeneratedAgentRecommendationOverlayReadinessSummaryRequestPayload",
    ]
    for phrase in required:
        assert phrase in snippet
    assert "fetchJson" not in snippet
    assert "setInterval" not in snippet


def test_ui_displays_ready_and_partial_reviewable_packet_states():
    snippet = _section_snippet()

    assert "review_packet_ready" in snippet
    assert "ready for operator review" in snippet
    assert "review_packet_partial_reviewable" in snippet
    assert "safe partial review packet is available and reviewable" in snippet
    assert "warning, not a failure" in snippet


def test_ui_displays_missing_blocked_failed_and_disabled_states_safely():
    snippet = _section_snippet()

    assert "review_packet_not_found" in snippet
    assert "No pipeline-generated overlay was found" in snippet
    assert "review_packet_blocked" in snippet
    assert "blocked by overlay generation constraints" in snippet
    assert "review_packet_failed_non_blocking" in snippet
    assert "failed non-blocking" in snippet
    assert "review_packet_disabled" in snippet
    assert "overlay generation was disabled" in snippet


def test_ui_displays_required_packet_fields_and_expandable_details():
    snippet = _section_snippet()
    required = [
        'renderWorkflowSummaryMetric("Packet", status)',
        'renderWorkflowSummaryMetric("Overlay found"',
        'renderWorkflowSummaryMetric("Readiness"',
        'renderWorkflowSummaryMetric("Reviewable"',
        'renderWorkflowSummaryMetric("Partial"',
        'renderWorkflowSummaryMetric("Auto generation"',
        'renderWorkflowSummaryMetric("Overlay"',
        'renderWorkflowSummaryMetric("Operator action"',
        "Review focus",
        "Trace context summary",
        "Evaluation boundaries",
        "Overlay readback summary",
        "Overlay readiness summary",
        "Safety metadata",
        "renderAgentTraceReadOnlyDetails",
    ]
    for phrase in required:
        assert phrase in snippet


def test_ui_labels_packet_advisory_readonly_and_no_mutation():
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


def test_ui_adds_no_override_queue_approval_resume_or_execution_controls():
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
        "create_approval_request(",
        "create_execution_request(",
        "create_execution_launch_request(",
        "execute_application(",
        "submit_application(",
    ]
    combined_lower = combined.lower()
    for marker in forbidden:
        assert marker.lower() not in combined_lower


def test_ui_calls_packet_api_only_from_explicit_action_without_provider_trigger():
    source = _source()
    handler = _handler_snippet()
    init_snippet = _init_snippet()

    assert "reviewPacketApiPath" in handler
    assert "reviewPacketApiPath" not in init_snippet
    assert "setInterval" not in handler
    assert "setInterval" not in init_snippet
    assert "provider" not in handler.lower()
    assert "run_llm" not in source
    assert "model_client" not in source
    assert "responses.create" not in source
    assert "chat.completions.create" not in source


def test_no_backend_pipeline_or_schema_wiring_for_packet_ui():
    markers = [
        "renderPipelineGeneratedOverlayReviewPacketSection",
        "data-pipeline-generated-overlay-review-packet",
        "pipeline_generated_overlay_review_packet_result",
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
        "def pipeline_generated_overlay_review_packet("
    )
    route_end = api_source.index(
        '@app.get("/profile/pipeline-runs/{run_id}/agentic-review-data")',
        route_start,
    )
    route_source = api_source[route_start:route_end]

    assert '"live_provider_backed_automated_agents": 0' in route_source
    assert '"mutation_authorized_agents": 0' in route_source
