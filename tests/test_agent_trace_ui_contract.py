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
