from pathlib import Path


REVIEW_JS_PATH = Path("src/app/static/agentic_review.js")


def _source() -> str:
    return REVIEW_JS_PATH.read_text(encoding="utf-8")


def _influence_section_snippet() -> str:
    source = _source()
    start = source.index("function renderHumanReviewedInfluencePreviewSection")
    end = source.index("function renderAgentTraceDetailedSections", start)
    return source[start:end]


def _influence_request_snippet() -> str:
    source = _source()
    start = source.index("function humanReviewedInfluencePreviewRequestPayload")
    end = source.index("function renderHumanReviewedInfluencePreviewSection", start)
    return source[start:end]


def _influence_handler_snippet() -> str:
    source = _source()
    start = source.index('event.target.closest("[data-human-reviewed-influence-preview]")')
    end = source.index('event.target.closest("[data-manual-shadow-recommendation-handoff-dry-run]")', start)
    return source[start:end]


def _init_snippet() -> str:
    source = _source()
    start = source.index("async function initAgenticReviewPage")
    end = source.index('window.addEventListener("DOMContentLoaded", initAgenticReviewPage);')
    return source[start:end]


def test_ui_includes_human_reviewed_influence_preview_section_and_control():
    source = _source()
    snippet = _influence_section_snippet()

    assert "function renderHumanReviewedInfluencePreviewSection" in source
    assert "Human-reviewed Influence Preview" in snippet
    assert "data-human-reviewed-influence-preview" in snippet
    assert "data-human-reviewed-influence-preview-status" in snippet
    assert "Preview Human-reviewed Influence" in snippet
    assert "renderHumanReviewedInfluencePreviewSection(tracePayload)" in source
    assert source.index("renderShadowSidecarScoreComparisonSection(tracePayload)") < source.index(
        "renderHumanReviewedInfluencePreviewSection(tracePayload)"
    )


def test_ui_calls_existing_phase6i_api_only_from_explicit_user_action():
    source = _source()
    handler = _influence_handler_snippet()
    init_snippet = _init_snippet()

    assert source.count("/api/human-reviewed-influence-preview") == 1
    assert "/api/human-reviewed-influence-preview" in handler
    assert 'method: "POST"' in handler
    assert "Content-Type" in handler
    assert "data-human-reviewed-influence-preview" in handler
    assert "humanReviewedInfluencePreviewRequestPayload(tracePayload)" in handler
    assert "/api/human-reviewed-influence-preview" not in init_snippet
    assert "/api/human-reviewed-influence-preview" not in source[
        source.index("async function fetchAgentTraceReadOnlyPayload") : source.index(
            "async function refreshAgenticReviewFeedbackSummary"
        )
    ]


def test_ui_builds_readonly_influence_preview_request_from_trace_payload_only():
    snippet = _influence_request_snippet()

    assert "deterministic_score_context" in snippet
    assert "shadow_score_comparison_context" in snippet
    assert "shadow_sidecar_score_comparison_result" in snippet
    assert "source_deterministic_context" in snippet
    assert "shadow_score_comparison_deterministic_context" in snippet
    assert "agent_run.summary_json" in snippet
    assert "fetchJson" not in snippet
    assert "setInterval" not in snippet


def test_ui_renders_default_off_blocked_and_missing_context_states():
    snippet = _influence_section_snippet()

    assert "preview_not_enabled" in snippet
    assert "Human-reviewed influence preview is not enabled. Default-off display is safe." in snippet
    assert "preview_blocked_by_kill_switch" in snippet
    assert "blocked by the kill switch" in snippet
    assert "preview_blocked_missing_deterministic_context" in snippet
    assert "Deterministic score context is missing" in snippet
    assert "preview_blocked_missing_shadow_comparison" in snippet
    assert "Shadow score comparison context is missing" in snippet
    assert "missing deterministic context, and missing shadow comparison" in snippet


def test_ui_renders_preview_contexts_influence_summary_and_effect_previews():
    snippet = _influence_section_snippet()

    required = [
        'renderWorkflowSummaryMetric("Preview", status)',
        'renderWorkflowSummaryMetric("Human review"',
        'renderWorkflowSummaryMetric("Approval gate"',
        "preview_findings",
        "Preview findings",
        "Deterministic score context",
        "Shadow comparison context",
        "Proposed influence summary",
        "Proposed score adjustment preview",
        "Proposed ranking effect preview",
        "Operator review summary",
        "Safety metadata",
        "renderAgentTraceReadOnlyDetails",
    ]
    for phrase in required:
        assert phrase in snippet


def test_ui_renders_human_review_approval_gate_and_no_mutation_summary():
    snippet = _influence_section_snippet()

    required = [
        "human_review_required",
        "approval_gate_required",
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
        "advisory only, requires human review plus an approval gate",
        "never changes scoring, ranking, queues, approvals, resumes, execution requests, launch requests, applications, or submissions",
    ]
    for phrase in required:
        assert phrase in snippet


def test_ui_does_not_add_mutation_override_queue_approval_or_execution_controls():
    snippet = _influence_section_snippet()
    handler = _influence_handler_snippet()
    combined = snippet + "\n" + handler
    forbidden = [
        "data-approve",
        "data-reject",
        "data-submit",
        "data-execute",
        "data-ranking-override",
        "data-scoring-override",
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


def test_ui_does_not_auto_refresh_provider_or_preview_calls():
    source = _source()
    init_snippet = _init_snippet()
    handler = _influence_handler_snippet()

    assert "setInterval" not in handler
    assert "setInterval" not in init_snippet
    assert "provider" not in handler.lower()
    assert "run_llm" not in source
    assert "model_client" not in source
    assert "responses.create" not in source
    assert "chat.completions.create" not in source


def test_no_backend_pipeline_or_schema_files_are_changed_for_influence_preview_ui():
    protected_paths = [
        Path("src/pipeline/collector.py"),
        Path("src/app/api.py"),
        Path("src/app/services.py"),
        Path("src/storage/agent_trace/schema.sql"),
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in protected_paths)

    assert "renderHumanReviewedInfluencePreviewSection" not in combined
    assert "data-human-reviewed-influence-preview" not in combined
    assert "human_reviewed_influence_preview_result" not in combined


def test_live_provider_and_mutation_counts_remain_documented_zero():
    doc = Path("docs/phase6_human_reviewed_influence_preview_ui_readiness_audit.md").read_text(
        encoding="utf-8"
    )

    assert "Live provider-backed automated agents remain zero." in doc
    assert "Mutation-authorized agents remain zero." in doc
