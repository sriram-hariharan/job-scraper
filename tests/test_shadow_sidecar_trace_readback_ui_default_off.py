from pathlib import Path


REVIEW_JS_PATH = Path("src/app/static/agentic_review.js")


def _source() -> str:
    return REVIEW_JS_PATH.read_text(encoding="utf-8")


def _readback_section_snippet() -> str:
    source = _source()
    start = source.index("function renderShadowSidecarTraceReadbackSection")
    end = source.index("function renderAgentTraceDetailedSections", start)
    return source[start:end]


def _readback_handler_snippet() -> str:
    source = _source()
    start = source.index('event.target.closest("[data-shadow-sidecar-trace-readback]")')
    end = source.index('event.target.closest("[data-manual-shadow-recommendation-handoff-dry-run]")', start)
    return source[start:end]


def _init_snippet() -> str:
    source = _source()
    start = source.index("async function initAgenticReviewPage")
    end = source.index('window.addEventListener("DOMContentLoaded", initAgenticReviewPage);')
    return source[start:end]


def test_ui_includes_shadow_sidecar_trace_readback_section_and_control():
    source = _source()
    snippet = _readback_section_snippet()

    assert "function renderShadowSidecarTraceReadbackSection" in source
    assert "Shadow Sidecar Trace Readback" in snippet
    assert "data-shadow-sidecar-trace-readback" in snippet
    assert "data-shadow-sidecar-trace-readback-status" in snippet
    assert "Read Shadow Trace" in snippet
    assert "renderShadowSidecarTraceReadbackSection(tracePayload)" in source
    assert source.index("renderAgentTraceEvidencePackSection(tracePayload?.trace_evidence_pack)") < source.index(
        "renderShadowSidecarTraceReadbackSection(tracePayload)"
    )


def test_ui_calls_existing_phase5v_api_only_from_explicit_user_action():
    source = _source()
    handler = _readback_handler_snippet()
    init_snippet = _init_snippet()

    assert source.count("/api/shadow-sidecar/trace-readback") == 1
    assert "/api/shadow-sidecar/trace-readback" in handler
    assert 'method: "POST"' in handler
    assert "Content-Type" in handler
    assert "data-shadow-sidecar-trace-readback" in handler
    assert "/api/shadow-sidecar/trace-readback" not in init_snippet
    assert "/api/shadow-sidecar/trace-readback" not in source[
        source.index("async function fetchAgentTraceReadOnlyPayload") : source.index(
            "async function refreshAgenticReviewFeedbackSummary"
        )
    ]


def test_ui_renders_default_off_and_safe_blocked_states():
    snippet = _readback_section_snippet()

    assert "trace_readback_not_enabled" in snippet
    assert "Shadow sidecar trace readback is not enabled. Default-off display is safe." in snippet
    assert "trace_readback_blocked_by_kill_switch" in snippet
    assert "blocked by the kill switch" in snippet
    assert "trace_readback_skipped_no_safe_source" in snippet
    assert "No safe shadow sidecar trace source is available yet" in snippet
    assert "not-enabled, blocked by kill switch, and no safe source" in snippet


def test_ui_renders_readback_status_source_context_and_safety_metadata():
    snippet = _readback_section_snippet()

    assert 'renderWorkflowSummaryMetric("Readback", status)' in snippet
    assert "source_trace_context" in snippet
    assert "Source trace context" in snippet
    assert "Trace readback" in snippet
    assert "Safety metadata" in snippet
    assert "shadow_sidecar_trace_readback_result" in snippet
    assert "renderAgentTraceReadOnlyDetails" in snippet
    assert "escapeHtml" in snippet


def test_ui_renders_no_mutation_safety_summary():
    snippet = _readback_section_snippet()

    required = [
        "read_only",
        "shadow_only",
        "did_mutate_scoring",
        "did_change_ranking",
        "did_mutate_queue",
        "did_mutate_approval",
        "did_mutate_resume",
        "did_create_execution_request",
        "did_create_execution_launch_request",
        "did_execute_application",
        "did_submit_application",
        "Manual read-only shadow trace readback",
        "does not mutate scoring, ranking, queues, approvals, resumes, execution requests, launch requests, applications, or submissions",
    ]
    for phrase in required:
        assert phrase in snippet


def test_ui_does_not_add_mutation_or_override_controls():
    snippet = _readback_section_snippet()
    handler = _readback_handler_snippet()
    combined = snippet + "\n" + handler
    forbidden = [
        "data-approve",
        "data-reject",
        "data-submit",
        "data-execute",
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
        "create_execution_request(",
        "create_execution_launch_request(",
    ]
    combined_lower = combined.lower()
    for marker in forbidden:
        assert marker.lower() not in combined_lower


def test_ui_does_not_auto_refresh_provider_or_readback_calls():
    source = _source()
    init_snippet = _init_snippet()
    handler = _readback_handler_snippet()

    assert "setInterval" not in handler
    assert "setInterval" not in init_snippet
    assert "provider" not in handler.lower()
    assert "run_llm" not in source
    assert "model_client" not in source
    assert "responses.create" not in source
    assert "chat.completions.create" not in source


def test_no_backend_pipeline_or_schema_files_are_changed_for_ui_readback():
    protected_paths = [
        Path("src/pipeline/collector.py"),
        Path("src/app/api.py"),
        Path("src/app/services.py"),
        Path("src/storage/agent_trace/schema.sql"),
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in protected_paths)

    assert "renderShadowSidecarTraceReadbackSection" not in combined
    assert "data-shadow-sidecar-trace-readback" not in combined
    assert "shadow_sidecar_trace_readback_result" not in combined


def test_live_provider_and_mutation_counts_remain_documented_zero():
    doc = Path("docs/phase5_shadow_sidecar_trace_readback_ui_readiness_audit.md").read_text(
        encoding="utf-8"
    )

    assert "Live provider-backed automated agents remain zero." in doc
    assert "Mutation-authorized agents remain zero." in doc
