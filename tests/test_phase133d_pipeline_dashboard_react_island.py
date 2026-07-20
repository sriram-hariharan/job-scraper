from pathlib import Path

from src.app.ui import executive_dashboard, pipeline_dashboard
from src.app.ui_shell import NAV_ITEMS, render_top_shell


ROOT = Path(__file__).resolve().parents[1]
UI_PATH = ROOT / "src/app/ui.py"
SHELL_PATH = ROOT / "src/app/ui_shell.py"
API_PATH = ROOT / "src/app/api.py"
SERVICES_PATH = ROOT / "src/app/services.py"
APP_JS_PATH = ROOT / "src/app/static/app.js"
RUNTIME_STATUS_PATH = ROOT / "src/pipeline/runtime_status.py"
PIPELINE_COMPONENT_PATH = (
    ROOT / "frontend/executive-kpi/src/pipeline/PipelineDashboard.tsx"
)
PIPELINE_MODEL_PATH = ROOT / "frontend/executive-kpi/src/pipeline/pipelineModel.ts"
MAIN_PATH = ROOT / "frontend/executive-kpi/src/main.tsx"
STYLES_PATH = ROOT / "frontend/executive-kpi/src/styles.css"
BUNDLE_DIR = ROOT / "src/app/static/build/executive-kpi"


def test_pipeline_route_renders_one_react_mount_and_shared_pipeline_navigation():
    markup = pipeline_dashboard()
    executive_markup = executive_dashboard()

    assert markup.count('id="pipelineDashboardRoot"') == 1
    assert 'aria-label="Pipeline monitoring dashboard"' in markup
    assert '/static/build/executive-kpi/executive-kpi.css?v=phase133d' in markup
    assert '/static/build/executive-kpi/executive-kpi.js?v=phase133d' in markup
    assert 'src="/static/app.js?v=phase133d_s1"' in markup
    assert 'src="/static/shell.js?v=phase133h_r1"' in markup
    assert '<body class="pipeline-dashboard-page">' in markup
    assert 'id="executiveKpiRoot"' not in markup
    assert 'id="executiveQueueRoot"' not in markup
    assert markup.count('id="pipelineConfigModal"') == 1
    assert markup.count('id="pipelineConfirmModal"') == 1
    assert 'id="pageLoadingOverlay"' not in markup
    assert 'id="executiveKpiRoot"' in executive_markup
    assert 'id="executiveQueueRoot"' in executive_markup

    assert ("Pipeline", "/pipeline", "pipeline") in NAV_ITEMS
    assert 'href="/pipeline"' in render_top_shell("/pipeline")
    assert 'aria-current="page"' in render_top_shell("/pipeline")


def test_pipeline_page_reuses_existing_status_and_reviewed_launch_pathways():
    component = PIPELINE_COMPONENT_PATH.read_text(encoding="utf-8")
    app_js = APP_JS_PATH.read_text(encoding="utf-8")
    api_source = API_PATH.read_text(encoding="utf-8")
    services_source = SERVICES_PATH.read_text(encoding="utf-8")

    assert 'fetch("/pipeline/status"' in component
    assert 'method: "GET"' in component
    assert "window.openApplyLensPipelineConfig()" in component
    assert 'window.location.assign("/")' not in component
    assert 'fetch("/pipeline/run"' not in component
    assert 'method: "POST"' not in component
    assert 'window.sessionStorage.getItem("applylens_open_live_pipeline") === "1"' in app_js
    assert "openPipelineConfigModal()" in app_js
    assert 'postJson("/pipeline/run", config)' in app_js
    assert 'window.location.assign("/pipeline")' in app_js
    assert 'window.location.pathname === "/pipeline"' in app_js
    assert 'applylens:pipeline-run-accepted' in app_js
    assert 'applylens_pipeline_accepted_run_id' in app_js
    assert '@app.get("/pipeline/status")' in api_source
    assert '@app.post("/pipeline/run")' in api_source
    assert "owner_pipeline_status_payload" in api_source
    assert "run_live_pipeline_payload" in api_source
    assert "def owner_pipeline_status_payload" in services_source
    assert "def pipeline_status_payload" in services_source


def test_pipeline_model_preserves_canonical_stage_order_and_existing_poll_interval():
    model = PIPELINE_MODEL_PATH.read_text(encoding="utf-8")
    runtime = RUNTIME_STATUS_PATH.read_text(encoding="utf-8")
    app_js = APP_JS_PATH.read_text(encoding="utf-8")

    stages = (
        "startup",
        "scraping",
        "filtering",
        "dedupe",
        "ranking",
        "cache_filter",
        "details",
        "intelligence",
        "ai_evaluation_filter",
        "embedding_prefilter",
        "ai_evaluation",
        "resume_matching",
        "application_priority",
        "rag_export",
        "planning",
        "finalization",
    )
    for stage in stages:
        assert f'"{stage}"' in model
        assert f'"{stage}"' in runtime

    assert "PIPELINE_POLL_INTERVAL_MS = 2_000" in model
    assert "}, 2000);" in app_js
    assert "window.setInterval" in PIPELINE_COMPONENT_PATH.read_text(encoding="utf-8")
    assert "shouldPoll" in PIPELINE_COMPONENT_PATH.read_text(encoding="utf-8")


def test_pipeline_component_uses_real_counts_safe_config_and_honest_health_readback():
    component = PIPELINE_COMPONENT_PATH.read_text(encoding="utf-8")
    model = PIPELINE_MODEL_PATH.read_text(encoding="utf-8")

    for count_key in (
        "scraped_jobs",
        "filtered_jobs",
        "deduped_jobs",
        "ranked_jobs",
        "ai_jobs",
        "resume_matched_jobs",
        "final_jobs",
    ):
        assert count_key in model

    assert "numericCount" in component
    assert "Source health data is not available yet" in component
    assert "No source status is inferred from missing job counts." in component
    assert "pipeline.source_health" in component
    assert "output_dir" not in component
    assert "api_key" not in component
    assert "database_url" not in component
    assert "Math.random" not in component
    assert "revenue" not in component.lower()
    assert "orders" not in component.lower()
    assert "customers" not in component.lower()


def test_pipeline_states_accessibility_and_scoped_responsive_theme_styles_exist():
    component = PIPELINE_COMPONENT_PATH.read_text(encoding="utf-8")
    styles = STYLES_PATH.read_text(encoding="utf-8")

    for marker in (
        'kind: "loading"',
        'status === "idle"',
        'pipeline-run-summary--${status}',
        'state === "active"',
        'state === "failed"',
        'role="status"',
        'role="alert"',
        'aria-current={state === "active" ? "step" : undefined}',
        'aria-busy={runActive}',
        'Live run in progress',
        'pipeline-running-strip',
        "Status may be stale",
    ):
        assert marker in component

    assert 'runActive={status === "starting" || status === "running"}' in component
    assert 'runActive ? "Pipeline Running..." : "Run Pipeline"' in component
    assert 'rawStage.toLowerCase() !== "unknown"' in component
    assert 'status === "failed" ? "Pipeline failed" : "Not active"' in component

    assert "#pipelineDashboardRoot" in styles
    assert 'html[data-theme="dark"] #pipelineDashboardRoot' in styles
    assert "@media (max-width: 1100px)" in styles
    assert "@media (max-width: 760px)" in styles
    assert "@media (max-width: 520px)" in styles
    assert "@media (prefers-reduced-motion: reduce)" in styles
    assert ".pipeline-running-indicator__spinner" in styles
    assert "animation: pipeline-running-spin" in styles
    assert ".pipeline-running-strip > span { animation: none; }" in styles
    assert "padding-bottom: 104px" in styles
    assert "grid-template-columns: repeat(4, minmax(0, 1fr))" in styles
    assert "data-stage-index={index + 1}" in component
    assert 'title={titleForStage(stage)}' in component
    assert ".pipeline-run-summary--idle .pipeline-run-message" in styles
    assert "pipeline-empty-panel--compact" in component
    assert "margin-right: var(--pipeline-chat-clearance)" in styles
    assert '<button type="button" onClick={launchPipeline}>Run Pipeline</button>' not in component
    assert "!important" not in styles

    stage_name_rule = styles.split(".pipeline-stage-name {", 1)[1].split("}", 1)[0]
    assert "white-space: normal" in stage_name_rule
    assert "overflow: visible" in stage_name_rule
    assert "text-overflow: ellipsis" not in stage_name_rule
    stage_status_rule = styles.split(".pipeline-stage small {", 1)[1].split("}", 1)[0]
    assert "grid-column: 2" in stage_status_rule


def test_live_launch_handoff_is_non_blocking_and_preserves_historical_details_owner():
    app_js = APP_JS_PATH.read_text(encoding="utf-8")
    profile_js = (ROOT / "src/app/static/profile.js").read_text(encoding="utf-8")
    profile_ui = (ROOT / "src/app/profile_ui.py").read_text(encoding="utf-8")

    launch_handler = app_js.split('qs("confirmPipelineRunBtn").addEventListener', 1)[1].split(
        'qs("closeAppErrorModalBtn")', 1
    )[0]
    handoff = app_js.split("function handoffAcceptedPipelineRun", 1)[1].split(
        "function attachPipelineLaunchHandlers", 1
    )[0]
    assert 'postJson("/pipeline/run", config)' in launch_handler
    assert "handoffAcceptedPipelineRun(payload)" in launch_handler
    assert launch_handler.index('postJson("/pipeline/run", config)') < launch_handler.index(
        "handoffAcceptedPipelineRun(payload)"
    )
    assert "showPageLoadingOverlay" not in launch_handler
    assert "startPipelinePolling" not in launch_handler
    assert "loadPipelineStatus" not in launch_handler
    assert "hidePageLoadingOverlay()" in handoff
    assert "closePipelineConfigModal()" in handoff
    assert "closePipelineConfirmModal()" in handoff
    assert 'window.location.pathname === "/pipeline"' in handoff
    assert "window.dispatchEvent(new CustomEvent(PIPELINE_ACCEPTED_RUN_EVENT_NAME" in handoff
    assert 'window.location.assign("/pipeline")' in app_js
    assert 'id="pipelineRunStatsModal"' in profile_ui
    assert "openPipelineRunStatsModal" in profile_js
    assert 'data-pipeline-run-view' in profile_js


def test_live_sales_dashboard_attribution_is_preserved_without_demo_sales_data():
    source = PIPELINE_COMPONENT_PATH.read_text(encoding="utf-8")

    assert "Adapted from Live Sales Dashboard by vaib215" in source
    assert "https://21st.dev/community/components/vaib215/live-sales-dashboard/default" in source
    assert "Adopted 2026-07-18" in source
    assert "owner-scoped pipeline status" in source
    assert "demo series" in source
    assert "Sales" not in source.replace("Live Sales Dashboard", "")


def test_canonical_bundle_contains_pipeline_mount_without_a_second_build_package():
    main = MAIN_PATH.read_text(encoding="utf-8")
    generated_names = sorted(path.name for path in BUNDLE_DIR.iterdir())
    bundle = (BUNDLE_DIR / "executive-kpi.js").read_text(encoding="utf-8")

    assert 'document.getElementById("pipelineDashboardRoot")' in main
    assert generated_names == ["executive-kpi.css", "executive-kpi.js"]
    assert "pipelineDashboardRoot" in bundle
    assert "/pipeline/status" in bundle
    assert "localhost" not in bundle
    assert not (ROOT / "frontend/pipeline").exists()


def test_pipeline_dashboard_adds_no_pipeline_writer_or_automation_surface():
    component = PIPELINE_COMPONENT_PATH.read_text(encoding="utf-8").lower()
    model = PIPELINE_MODEL_PATH.read_text(encoding="utf-8").lower()
    ui_source = UI_PATH.read_text(encoding="utf-8").lower()
    shell_source = SHELL_PATH.read_text(encoding="utf-8").lower()

    for forbidden in (
        "auto_apply",
        "submit_ats",
        "message_recruiter",
        "mark_applied",
        "score_resume_job_match",
        "run_live_pipeline_payload(",
    ):
        assert forbidden not in component
        assert forbidden not in model
        assert forbidden not in ui_source
        assert forbidden not in shell_source
