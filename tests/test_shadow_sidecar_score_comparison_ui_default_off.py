from pathlib import Path


REVIEW_JS_PATH = Path("src/app/static/agentic_review.js")


def _source() -> str:
    return REVIEW_JS_PATH.read_text(encoding="utf-8")


def _comparison_section_snippet() -> str:
    source = _source()
    start = source.index("function renderShadowSidecarScoreComparisonSection")
    end = source.index("function renderAgentTraceDetailedSections", start)
    return source[start:end]


def _comparison_request_snippet() -> str:
    source = _source()
    start = source.index("function shadowScoreComparisonRequestPayload")
    end = source.index("function renderShadowSidecarScoreComparisonSection", start)
    return source[start:end]


def _comparison_handler_snippet() -> str:
    source = _source()
    start = source.index('event.target.closest("[data-shadow-sidecar-score-comparison]")')
    end = source.index('event.target.closest("[data-manual-shadow-recommendation-handoff-dry-run]")', start)
    return source[start:end]


def _init_snippet() -> str:
    source = _source()
    start = source.index("async function initAgenticReviewPage")
    end = source.index('window.addEventListener("DOMContentLoaded", initAgenticReviewPage);')
    return source[start:end]


def test_ui_includes_shadow_score_comparison_section_and_control():
    source = _source()
    snippet = _comparison_section_snippet()

    assert "function renderShadowSidecarScoreComparisonSection" in source
    assert "Shadow Score Comparison" in snippet
    assert "data-shadow-sidecar-score-comparison" in snippet
    assert "data-shadow-sidecar-score-comparison-status" in snippet
    assert "Compare Shadow Score" in snippet
    assert "renderShadowSidecarScoreComparisonSection(tracePayload)" in source
    assert source.index("renderShadowSidecarTraceReadbackSection(tracePayload)") < source.index(
        "renderShadowSidecarScoreComparisonSection(tracePayload)"
    )


def test_ui_calls_existing_phase6c_api_only_from_explicit_user_action():
    source = _source()
    handler = _comparison_handler_snippet()
    init_snippet = _init_snippet()

    assert source.count("/api/shadow-sidecar/score-comparison") == 1
    assert "/api/shadow-sidecar/score-comparison" in handler
    assert 'method: "POST"' in handler
    assert "Content-Type" in handler
    assert "data-shadow-sidecar-score-comparison" in handler
    assert "shadowScoreComparisonRequestPayload(tracePayload)" in handler
    assert "/api/shadow-sidecar/score-comparison" not in init_snippet
    assert "/api/shadow-sidecar/score-comparison" not in source[
        source.index("async function fetchAgentTraceReadOnlyPayload") : source.index(
            "async function refreshAgenticReviewFeedbackSummary"
        )
    ]


def test_ui_builds_readonly_score_comparison_request_from_trace_payload_only():
    snippet = _comparison_request_snippet()

    assert "deterministic_score_context" in snippet
    assert "shadow_evidence_snapshot_payload" in snippet
    assert "shadow_score_comparison_deterministic_context" in snippet
    assert "source_deterministic_context" in snippet
    assert "shadow_sidecar_evidence_snapshot_result" in snippet
    assert "shadow_score_comparison_snapshot_payload" in snippet
    assert "fetchJson" not in snippet
    assert "setInterval" not in snippet


def test_ui_renders_default_off_and_safe_blocked_missing_states():
    snippet = _comparison_section_snippet()

    assert "comparison_not_enabled" in snippet
    assert "Shadow score comparison is not enabled. Default-off display is safe." in snippet
    assert "comparison_blocked_by_kill_switch" in snippet
    assert "blocked by the kill switch" in snippet
    assert "comparison_blocked_missing_deterministic_context" in snippet
    assert "Deterministic score context is missing" in snippet
    assert "comparison_blocked_missing_shadow_snapshot" in snippet
    assert "Shadow evidence snapshot is missing" in snippet
    assert "missing deterministic context, and missing shadow snapshot" in snippet


def test_ui_renders_status_score_decision_snapshot_agreement_and_findings():
    snippet = _comparison_section_snippet()

    required = [
        'renderWorkflowSummaryMetric("Comparison", status)',
        'renderWorkflowSummaryMetric("Deterministic score", result.deterministic_score',
        'renderWorkflowSummaryMetric("Decision", result.deterministic_decision',
        'renderWorkflowSummaryMetric("Shadow snapshot", result.shadow_snapshot_status',
        'renderWorkflowSummaryMetric("Agreement", result.agreement_level',
        "comparison_findings",
        "Comparison findings",
        "Operator review summary",
        "Source deterministic context",
        "Source shadow snapshot context",
        "Safety metadata",
        "renderAgentTraceReadOnlyDetails",
    ]
    for phrase in required:
        assert phrase in snippet


def test_ui_renders_no_mutation_safety_summary():
    snippet = _comparison_section_snippet()

    required = [
        "read_only",
        "shadow_only",
        "operator_review_only",
        "did_mutate_scoring",
        "did_change_ranking",
        "did_mutate_queue",
        "did_mutate_approval",
        "did_mutate_resume",
        "did_create_execution_request",
        "did_create_execution_launch_request",
        "did_execute_application",
        "did_submit_application",
        "Manual read-only comparison between deterministic final scoring context and shadow sidecar evidence",
        "never changes scoring, ranking, queues, approvals, resumes, execution requests, launch requests, applications, or submissions",
    ]
    for phrase in required:
        assert phrase in snippet


def test_ui_does_not_add_mutation_override_or_execution_controls():
    snippet = _comparison_section_snippet()
    handler = _comparison_handler_snippet()
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


def test_ui_does_not_auto_refresh_provider_or_comparison_calls():
    source = _source()
    init_snippet = _init_snippet()
    handler = _comparison_handler_snippet()

    assert "setInterval" not in handler
    assert "setInterval" not in init_snippet
    assert "provider" not in handler.lower()
    assert "run_llm" not in source
    assert "model_client" not in source
    assert "responses.create" not in source
    assert "chat.completions.create" not in source


def test_no_backend_pipeline_or_schema_files_are_changed_for_score_comparison_ui():
    protected_paths = [
        Path("src/pipeline/collector.py"),
        Path("src/app/api.py"),
        Path("src/app/services.py"),
        Path("src/storage/agent_trace/schema.sql"),
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in protected_paths)

    assert "renderShadowSidecarScoreComparisonSection" not in combined
    assert "data-shadow-sidecar-score-comparison" not in combined
    assert "shadow_sidecar_score_comparison_result" not in combined


def test_live_provider_and_mutation_counts_remain_documented_zero():
    doc = Path("docs/phase6_shadow_score_comparison_ui_readiness_audit.md").read_text(
        encoding="utf-8"
    )

    assert "Live provider-backed automated agents remain zero." in doc
    assert "Mutation-authorized agents remain zero." in doc
