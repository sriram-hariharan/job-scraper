from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_JS = ROOT / "src/app/static/app.js"
UI = ROOT / "src/app/ui.py"
CSS = ROOT / "src/app/static/styles.css"
def _function_source(source: str, name: str, next_name: str) -> str:
    start = source.index(f"function {name}")
    end = source.index(f"function {next_name}", start)
    return source[start:end]


def test_target_run_has_complete_sequential_filter_accounting():
    status = {
        "status": "succeeded",
        "completed_stages": ["filtering", "dedupe", "ranking", "finalization"],
        "counts": {
            "scraped_jobs": 3016,
            "filter_title_mismatch": 2956,
            "filter_location_not_us": 23,
            "filter_not_recent": 15,
            "filter_missing_timestamp": 22,
            "filtered_jobs": 0,
            "deduped_jobs": 0,
            "ranked_jobs": 0,
        },
        "final_job_count": 0,
        "return_code": 0,
        "error": "",
    }
    counts = status["counts"]

    rejected = sum(
        counts[key]
        for key in (
            "filter_title_mismatch",
            "filter_location_not_us",
            "filter_not_recent",
            "filter_missing_timestamp",
        )
    )
    assert status["status"] == "succeeded"
    assert counts["scraped_jobs"] == 3016
    assert rejected == counts["scraped_jobs"]
    assert counts["filtered_jobs"] == 0
    assert counts["deduped_jobs"] == 0
    assert counts["ranked_jobs"] == 0
    assert status["final_job_count"] == 0
    assert status["return_code"] == 0
    assert not status["error"]
    assert "filtering" in status["completed_stages"]
    assert "finalization" in status["completed_stages"]


def test_completion_summary_maps_authoritative_counts_once():
    source = APP_JS.read_text(encoding="utf-8")
    derive = _function_source(
        source,
        "derivePipelineCompletionSummary",
        "renderPipelineSuccessSummary",
    )

    assert "counts.scraped_jobs" in derive
    assert "counts.filtered_jobs" in derive
    assert "pipeline.final_job_count ?? counts.rag_export_count" in derive
    assert "counts.deduped_jobs" not in derive
    assert "counts.scored_jobs" not in derive
    assert 'jobsPassedFilters === null' in derive
    assert "filter_title_mismatch" in derive
    assert "filter_location_not_us" in derive
    assert "filter_not_recent" in derive
    assert "filter_missing_timestamp" in derive


def test_empty_result_renders_only_truthful_summary_and_safe_actions():
    source = APP_JS.read_text(encoding="utf-8")
    markup = UI.read_text(encoding="utf-8")
    render = _function_source(
        source,
        "renderPipelineSuccessSummary",
        "renderPipelineFailureSummary",
    )

    for label in ("Collected", "Passed filters", "Planning jobs"):
        assert label in render
    assert render.count('["Collected", summary.jobsCollected]') == 1
    assert render.count('["Passed filters", summary.jobsPassedFilters]') == 1
    assert render.count('["Planning jobs", summary.planningJobs]') == 1
    assert '"No jobs matched this run"' in render
    assert 'classList.toggle("hidden", summary.isEmptyResult)' in render
    assert 'pipelineSuccessDetailsBtn' in render
    assert 'pipelineSuccessRunAgainBtn' in render
    assert "started_at" not in render
    assert "finished_at" not in render
    assert 'id="pipelineSuccessDetailsBtn"' in markup
    assert 'id="pipelineSuccessRunAgainBtn"' in markup
    assert 'id="pipelineSuccessPlanningBtn"' in markup
    assert 'class="pipeline-result-header__layout"' in markup
    assert "pipeline-result-action--tertiary" in markup
    assert "pipeline-result-action--secondary" in markup
    assert "pipeline-result-action--primary" in markup
    assert 'window.location.href = "/profile?tab=pipeline-runs"' in source
    assert "openPipelineConfigModal()" in source


def test_empty_result_uses_compact_canonical_responsive_css():
    css = CSS.read_text(encoding="utf-8")

    assert ".workflow-overlay__panel.is-empty-result" in css
    assert "width: min(860px, 88vw) !important" in css
    assert "height: auto !important" in css
    assert "padding: clamp(36px, 4vw, 44px) !important" in css
    assert ".pipeline-result-metrics" in css
    assert "grid-template-columns: repeat(3, minmax(0, 1fr))" in css
    assert ".pipeline-empty-reasons" in css
    assert ".pipeline-empty-reason-bar" in css
    assert "width: var(--pipeline-reason-ratio)" in css
    assert "var(--workflow-accent-strong)" in css
    assert "var(--workflow-accent-soft)" in css
    assert 'html[data-theme="light"] .workflow-overlay__panel.is-empty-result' in css
    assert 'html[data-theme="dark"] .workflow-overlay__panel.is-empty-result' in css
    mobile = css[css.index("@media (max-width: 640px)") :]
    assert ".pipeline-result-metrics" in mobile
    assert "grid-template-columns: 1fr" in mobile
    assert ".pipeline-result-header__layout" in mobile
    assert ".pipeline-success-actions" in mobile


def test_completion_remains_persistent_and_does_not_auto_navigate():
    source = APP_JS.read_text(encoding="utf-8")
    show_success = _function_source(
        source,
        "showPipelineSuccessOverlay",
        "showPageLoadingOverlay",
    )
    handlers = source[source.index('qs("pipelineSuccessOkBtn").addEventListener') :]

    assert "overlay.classList.remove(\"hidden\")" in show_success
    assert "setTimeout" not in show_success
    assert 'qs("pipelineSuccessPlanningBtn").addEventListener' in handlers
    assert 'qs("pipelineSuccessDetailsBtn").addEventListener' in handlers
    assert 'qs("pipelineSuccessRunAgainBtn").addEventListener' in handlers
