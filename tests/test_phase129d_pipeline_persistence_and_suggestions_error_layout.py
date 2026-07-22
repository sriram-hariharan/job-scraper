from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_JS = ROOT / "src/app/static/app.js"
PLANNING_JS = ROOT / "src/app/static/planning.js"
PLANNING_UI = ROOT / "src/app/planning_ui.py"
CSS = ROOT / "src/app/static/styles.css"


def _function_source(source: str, name: str) -> str:
    start = source.index(f"function {name}")
    brace = source.index("{", start)
    depth = 0
    for index in range(brace, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[start : index + 1]
    raise AssertionError(f"could not extract {name}")


def test_pipeline_status_keeps_live_monitoring_non_blocking():
    source = APP_JS.read_text(encoding="utf-8")
    render = _function_source(source, "renderPipelineStatus")

    assert '["queued", "starting", "running"]' in render
    assert "showPageLoadingOverlay" not in render
    assert 'status === "succeeded"' in render
    assert "showPipelineSuccessOverlay" not in render
    assert "showPipelineFailureOverlay" not in render
    assert '"cancelled"' in render
    assert '"stopped"' in render
    assert "hidePageLoadingOverlay()" in render
    assert "filtering" in source
    assert "dedupe" in source


def test_executive_pipeline_button_navigates_to_monitoring_when_run_is_active():
    source = APP_JS.read_text(encoding="utf-8")
    render = _function_source(source, "renderPipelineStatus")
    attach = _function_source(source, "attachPipelineLaunchHandlers")

    assert 'runBtn.dataset.pipelineActive = "true"' in render
    assert 'runBtn.textContent = "View Pipeline"' in render
    assert "runBtn.disabled = false" in render
    assert "delete runBtn.dataset.pipelineActive" in render
    assert 'runPipelineBtn.dataset.pipelineActive === "true"' in attach
    assert 'window.location.assign("/pipeline")' in attach
    assert attach.index('window.location.assign("/pipeline")') < attach.index("openPipelineConfigModal()")


def test_transient_poll_failure_retries_without_dismissal_or_navigation():
    source = APP_JS.read_text(encoding="utf-8")
    polling = _function_source(source, "startPipelinePolling")

    catch_block = polling[polling.index("catch (err)") :]
    assert "stopPipelinePolling()" not in catch_block
    assert "hidePageLoadingOverlay" not in catch_block
    assert "window.location" not in catch_block
    assert "Retrying automatically" in catch_block
    assert "setInterval" in polling
    assert "2000" in polling


def test_accepted_launch_hands_monitoring_to_pipeline_dashboard_without_legacy_overlay():
    source = APP_JS.read_text(encoding="utf-8")
    start = source.index('qs("confirmPipelineRunBtn").addEventListener')
    end = source.index('qs("pipelineSuccessOkBtn").addEventListener', start)
    handler = source[start:end]

    assert 'postJson("/pipeline/run", config)' in handler
    assert "handoffAcceptedPipelineRun(payload)" in handler
    assert "startPipelinePolling()" not in handler
    assert "showPageLoadingOverlay" not in handler
    assert "loadPipelineStatus" not in handler


def test_pipeline_navigation_and_dismissal_require_explicit_buttons():
    source = APP_JS.read_text(encoding="utf-8")
    handlers = source[source.index('qs("pipelineSuccessOkBtn").addEventListener') :]

    assert 'qs("pipelineSuccessOkBtn").addEventListener' in handlers
    assert 'qs("pipelineFailureOkBtn").addEventListener' in handlers
    assert 'qs("pipelineSuccessPlanningBtn").addEventListener' in handlers
    assert 'window.location.href = "/planning"' in handlers
    assert 'qs("pipelineSuccessPlanningBtn").disabled = true' in handlers
    assert "setTimeout" not in handlers[: handlers.index('window.location.href = "/planning"') + 40]


def test_generate_suggestions_error_uses_separate_body_and_footer_actions():
    markup = PLANNING_UI.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")
    body_start = markup.index('class="generate-suggestions-loader-body workflow-overlay__body"')
    footer_start = markup.index('class="modal-actions generate-suggestions-loader-actions workflow-overlay__footer"')
    footer_end = markup.index("</div>", footer_start)

    assert 'id="generateSuggestionsError"' in markup[body_start:footer_start]
    assert 'id="generateSuggestionsRetryBtn"' in markup[footer_start:footer_end]
    assert 'id="generateSuggestionsCancelBtn"' in markup[footer_start:footer_end]
    assert ".workflow-overlay--tailoring .workflow-overlay__body" in css
    assert "grid-template-rows: minmax(0, 1fr) auto" in css
    assert ".generate-suggestions-loader-error" in css
    assert "overflow-wrap: anywhere" in css


def test_retry_preserves_run_job_resume_and_explicit_workspace_navigation():
    source = PLANNING_JS.read_text(encoding="utf-8")
    retry = _function_source(source, "retryGenerateSuggestions")
    open_workspace = _function_source(source, "openGenerateSuggestionsWorkspace")

    assert "pipelineRunId" in retry
    assert "jobDocId" in retry
    assert "winnerResume" in retry
    assert "operatorSelectedResume" in retry
    assert "handleGenerateSuggestionsClick(buttonLike)" in retry
    assert "window.location.href = generateSuggestionsState.lastWorkspaceUrl" in open_workspace
