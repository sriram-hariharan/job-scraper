from pathlib import Path


def test_profile_pipeline_agent_trace_panel_contract():
    profile_js = Path("src/app/static/profile.js").read_text(encoding="utf-8")
    review_js = Path("src/app/static/agentic_review.js").read_text(encoding="utf-8")
    profile_css = Path("src/app/static/agentic_review.css").read_text(encoding="utf-8")
    api_source = Path("src/app/api.py").read_text(encoding="utf-8")

    assert "/profile/pipeline-runs/${encodeURIComponent(runId)}/agent-trace" in review_js
    assert "renderAgentTracePanel" in profile_js
    assert "renderAgentTracePanel" in review_js
    assert "No agent trace recorded for this run." in profile_js
    assert "agent-trace-step-status" in profile_js
    assert "renderJsonDetails(\"Input\"" in profile_js
    assert "renderJsonDetails(\"Output\"" in profile_js
    assert "renderJsonDetails(\"Validation\"" in profile_js
    assert "renderJsonDetails(\"Token usage\"" in profile_js
    assert "renderJsonDetails(\"Cost\"" in profile_js
    assert "agent-trace-step-summary" in profile_js

    assert ".agent-trace-panel" in profile_css
    assert ".agent-trace-step-status" in profile_css
    assert ".agent-trace-json-detail" in profile_css
    assert ".agent-trace-json-detail pre" in profile_css
    assert "max-height: 280px" in profile_css
    assert "background: #f8fafc" in profile_css
    assert "color: #0f172a" in profile_css
    assert '@app.get("/profile/pipeline-runs/{run_id}/agent-trace")' in api_source


def test_profile_agent_trace_fetch_does_not_pass_owner_user_id():
    review_js = Path("src/app/static/agentic_review.js").read_text(encoding="utf-8")
    trace_fetch_start = review_js.index("/profile/pipeline-runs/${encodeURIComponent(runId)}/agent-trace")
    trace_fetch_snippet = review_js[trace_fetch_start : trace_fetch_start + 240]

    assert "owner_user_id" not in trace_fetch_snippet
    assert "runId" in trace_fetch_snippet


def test_agentic_review_human_feedback_diagnostics_contract():
    review_js = Path("src/app/static/agentic_review.js").read_text(encoding="utf-8")
    review_css = Path("src/app/static/agentic_review.css").read_text(encoding="utf-8")
    api_source = Path("src/app/api.py").read_text(encoding="utf-8")
    services_source = Path("src/app/services.py").read_text(encoding="utf-8")

    assert "Human Feedback" in review_js
    assert "renderAgenticReviewFeedbackSection" in review_js
    assert "Mark review useful" in review_js
    assert "Mark review not useful" in review_js
    assert "agentic_review_helpful" in review_js
    assert "agentic_review_not_helpful" in review_js
    assert "agentic_review_ui" in review_js
    assert 'fetchJson("/api/agent-feedback"' in review_js
    assert "recordAgenticReviewFeedback" in review_js
    assert "refreshAgenticReviewFeedbackSummary" in review_js
    assert "Feedback recorded." in review_js
    assert "Could not record feedback." in review_js
    assert "total_events" in review_js
    assert "event_type_counts" in review_js
    assert "target_type_counts" in review_js
    assert "latest_event_at" in review_js
    assert "No feedback events recorded for this run yet." in review_js
    assert "/api/agent-feedback/summary?pipeline_run_id=${encodeURIComponent(runId)}&limit=50" in review_js

    feedback_fetch_start = review_js.index("/api/agent-feedback/summary?pipeline_run_id=${encodeURIComponent(runId)}")
    feedback_fetch_snippet = review_js[feedback_fetch_start : feedback_fetch_start + 220]
    assert "owner_user_id" not in feedback_fetch_snippet
    feedback_post_start = review_js.index('fetchJson("/api/agent-feedback"')
    feedback_post_snippet = review_js[feedback_post_start : feedback_post_start + 700]
    assert "owner_user_id" not in feedback_post_snippet
    assert "pipeline_run_id" in feedback_post_snippet
    assert "target_type" in feedback_post_snippet
    assert "target_id" in feedback_post_snippet
    assert "event_type" in feedback_post_snippet
    assert "payload_json" in feedback_post_snippet
    assert "source" in feedback_post_snippet

    assert ".agentic-feedback-card" in review_css
    assert ".agentic-feedback-event" in review_css
    assert ".agentic-feedback-metrics" in review_css
    assert ".agentic-feedback-action" in review_css
    assert ".agentic-feedback-status" in review_css
    assert '@app.get("/api/agent-feedback/summary")' in api_source
    assert '@app.get("/api/agent-feedback")' in api_source
    assert "agent_feedback_summary_payload" in services_source
    assert "list_agent_feedback_payload" in services_source


def test_agentic_review_rag_evaluation_diagnostics_contract():
    review_js = Path("src/app/static/agentic_review.js").read_text(encoding="utf-8")
    review_css = Path("src/app/static/agentic_review.css").read_text(encoding="utf-8")
    services_source = Path("src/app/services.py").read_text(encoding="utf-8")

    assert "RAG Evaluation" in review_js
    assert "renderRagEvaluationSection" in review_js
    assert "getRagEvaluationSummary" in review_js
    assert "query_count" in review_js
    assert "retrieved_chunk_count" in review_js
    assert "average_retrieval_score" in review_js
    assert "top_k_hit_rate" in review_js
    assert "missing_evidence_warning_count" in review_js
    assert "No RAG evaluation data recorded for this run yet." in review_js

    assert ".rag-evaluation-card" in review_css
    assert ".rag-evaluation-metrics" in review_css

    assert "rag_evaluation_summary.json" in services_source
    assert "rag_evaluation_report.md" in services_source
    assert "_rag_evaluation_from_artifacts" in services_source
    assert "build_rag_evaluation_summary" in services_source
