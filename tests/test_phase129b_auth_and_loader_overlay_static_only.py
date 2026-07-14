from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUTH_UI = ROOT / "src/app/auth_ui.py"
UI = ROOT / "src/app/ui.py"
PLANNING_UI = ROOT / "src/app/planning_ui.py"
APP_JS = ROOT / "src/app/static/app.js"
PLANNING_JS = ROOT / "src/app/static/planning.js"
CSS = ROOT / "src/app/static/styles.css"
AUTH_HERO_ICONS = ROOT / "src/app/static/media/auth_hero_icons"
AUTH_WORKFLOW_ARTWORK = ROOT / "src/app/static/media/auth_workflow_hero.svg"
D3_VENDOR = ROOT / "src/app/static/vendor/d3"


def test_auth_pages_use_current_product_and_safety_copy():
    source = AUTH_UI.read_text(encoding="utf-8")
    for text in (
        "Turn live jobs into<br /><span>review-ready</span><br />applications.",
        'title = "Create your workspace" if is_register else "Welcome back"',
        "Live job pipeline",
        "Hybrid fit scoring",
        "Policy AI review",
        "Tailoring workspace",
        "You stay in control. No auto-apply. No recruiter messages.",
        "Secure and private. Built for your job search.",
    ):
        assert text in source
    assert 'mode == "register"' in source
    assert 'mode === "register" ? "/auth/register" : "/auth/login"' in source


def test_auth_shell_is_cinematic_responsive_and_has_no_fake_social_login():
    source = AUTH_UI.read_text(encoding="utf-8")
    for marker in (
        "height: 100dvh",
        "overflow: hidden",
        "box-sizing: border-box",
        "auth-scene",
        "auth-scene-haze",
        "auth-scene-wave",
        "auth-workflow-artwork",
        'src="/static/media/auth_workflow_hero.svg"',
        "height: min(68vh, 650px)",
        "background: rgba(255, 255, 255, 0.76)",
        ".auth-password-toggle:focus-visible",
        "background: transparent !important",
        "background-image: none !important",
        "#passwordToggleBtn.auth-password-toggle",
        "scale(1.78)",
        "max-width: 500px",
        "backdrop-filter: blur(24px)",
        "@media (max-width: 900px)",
        "@media (max-width: 560px)",
        "overflow-y: auto",
        "@media (prefers-reduced-motion: reduce)",
        'url("/static/media/Login_page_BG_img.jpg")',
    ):
        assert marker in source
    assert "clip-path: polygon" not in source
    assert "auth-workflow-step" not in source
    assert "<span>01</span>" not in source
    assert "auth-workflow-tile--check" not in source
    assert "border: 1px solid rgba(100, 116, 139, 0.24) !important" not in source
    auth_input_css = source[source.index("    .auth-field input {{"):source.index("    .auth-field input::placeholder")]
    assert "font-weight: 450" in auth_input_css
    assert "font-weight: 650" not in auth_input_css
    assert "Scrape roles, score fit, review policy-driven AI notes" in source
    assert source.count('class="auth-hero-bullet"') == 4
    assert "setInterval" not in source
    assert "MutationObserver" not in source
    assert "ChatGPT Image" not in source
    assert (ROOT / "src/app/static/media/Login_page_BG_img.jpg").is_file()
    assert (ROOT / "src/app/static/media/Login_page_BG_img.LICENSE.txt").is_file()
    expected_icons = {
        "collect_jobs.svg",
        "score_fit.svg",
        "review_ai_notes.svg",
        "tailor_safely.svg",
        "apply_with_confidence.svg",
    }
    assert {path.name for path in AUTH_HERO_ICONS.glob("*.svg")} == expected_icons
    assert (AUTH_HERO_ICONS / "LICENSES.txt").is_file()
    for icon_name in expected_icons:
        icon_source = (AUTH_HERO_ICONS / icon_name).read_text(encoding="utf-8")
        assert 'viewBox="0 0 24 24"' in icon_source
        assert "<script" not in icon_source
        assert "<animate" not in icon_source
        assert "foreignObject" not in icon_source
        assert "href=" not in icon_source
        assert "onload=" not in icon_source
        assert "onclick=" not in icon_source
    for forbidden in ("Google login", "Facebook login", "Microsoft login", "Forgot password"):
        assert forbidden not in source


def test_auth_workflow_uses_finished_designer_artwork_only():
    source = AUTH_UI.read_text(encoding="utf-8")

    assert AUTH_WORKFLOW_ARTWORK.is_file()
    artwork_source = AUTH_WORKFLOW_ARTWORK.read_text(encoding="utf-8")
    assert artwork_source.lstrip().startswith("<svg")
    assert not D3_VENDOR.exists()
    assert "/static/vendor/d3/" not in source
    assert "window.d3" not in source
    assert "cdn.jsdelivr.net" not in source
    assert "unpkg.com" not in source
    assert source.count('class="auth-workflow-artwork"') == 1
    assert source.count('src="/static/media/auth_workflow_hero.svg"') == 1
    assert '<svg class="auth-workflow' not in source
    for forbidden in (
        "auth-workflow-scene",
        "auth-workflow-svg",
        "auth-workflow-rail",
        "auth-workflow-node",
        "auth-workflow-icon",
        "updateWorkflowConnector",
        "toWorkflowPoint",
        "connectorLine",
        "curveCatmullRom",
        "curveMonotoneY",
        "workflowPath.setAttribute",
        "scheduleWorkflowContrastUpdate",
        "sampleWorkflowLuminance",
        "relativeLuminance",
        "workflowContrastClasses",
        "workflowBackgroundContext",
        'document.createElement("canvas")',
    ):
        assert forbidden not in source
    assert "setInterval" not in source
    assert "MutationObserver" not in source
    assert "ResizeObserver" not in source
    assert ".auth-password-toggle:focus-visible" in source
    assert 'mode === "register" ? "/auth/register" : "/auth/login"' in source
    for fake_social in ("Google login", "Facebook login", "Microsoft login"):
        assert fake_social not in source


def test_generate_suggestions_waits_for_explicit_workspace_action():
    markup = PLANNING_UI.read_text(encoding="utf-8")
    script = PLANNING_JS.read_text(encoding="utf-8")
    assert "Preparing tailoring workspace" in markup
    assert "Open Tailoring Workspace" in markup
    assert "Tailoring workspace is ready" in script
    assert 'window.location.href = generateSuggestionsState.lastWorkspaceUrl' in script
    assert "window.setTimeout(() =>" not in script[script.index("async function handleGenerateSuggestionsClick"):script.index("async function retryGenerateSuggestions")]
    assert "workflow-overlay__panel" in markup
    assert "workflow-overlay--tailoring" in markup
    assert "workflow-overlay__body" in markup
    assert "workflow-step-viewport" in markup
    assert "generate-suggestions-document-stack" not in markup
    assert "workflow-overlay__footer" in markup
    assert "Your suggestions and review packet are ready for inspection." in script
    assert 'button.disabled = true' in script[script.index("function openGenerateSuggestionsWorkspace"):]


def test_pipeline_overlay_waits_and_offers_planning_action():
    markup = UI.read_text(encoding="utf-8")
    script = APP_JS.read_text(encoding="utf-8")
    assert "Running live job pipeline" in markup
    assert "Pipeline run is ready" in markup
    assert 'id="pipelineSuccessPlanningBtn">View Planning</button>' in markup
    assert 'window.location.href = "/planning"' in script
    assert 'qs("pipelineSuccessOkBtn").addEventListener' in script
    assert "workflow-overlay__panel" in markup
    assert "workflow-overlay--pipeline" in markup
    assert "workflow-step-viewport" in markup
    assert "pipeline-workflow-visual" not in markup
    assert "pipeline-workflow-orbit" not in markup
    assert "pipelineSuccessStageStepper" in markup
    assert "pipelineFailureStageStepper" in markup
    assert "Your job results and planning artifacts are ready to review." in script
    assert 'qs("pipelineSuccessPlanningBtn").disabled = true' in script
    assert "No application actions were taken." in script
    assert "PIPELINE_VISIBLE_STAGE_GROUPS" in script
    for label in [
        "Starting pipeline",
        "Collecting jobs",
        "Filtering and deduplicating",
        "Ranking opportunities",
        "Running job intelligence",
        "Evaluating fit",
        "Matching resumes",
        "Prioritizing applications",
        "Preparing planning artifacts",
        "Finalizing run",
    ]:
        assert label in script


def test_processing_surfaces_share_compact_moving_step_viewport_and_reduced_motion():
    source = CSS.read_text(encoding="utf-8")
    assert ".workflow-overlay__panel" in source
    assert "width: min(840px, 88vw)" in source
    assert "height: auto !important" in source
    assert "max-height: 82dvh !important" in source
    assert ".workflow-overlay__body" in source
    assert ".workflow-overlay--pipeline" in source
    assert ".workflow-overlay--tailoring" in source
    assert 'html[data-theme="light"] .workflow-overlay' in source
    assert 'html[data-theme="dark"] .workflow-overlay--tailoring' in source
    assert "--workflow-accent: #2563eb" in source
    assert "--workflow-accent: #7c3aed" in source
    assert ".workflow-step-viewport" in source
    assert ".workflow-step-track" in source
    assert ".workflow-step.is-complete" in source
    assert ".workflow-step.is-active" in source
    assert ".workflow-step.is-pending" in source
    assert ".workflow-step.is-error" in source
    assert ".workflow-step.is-previous" in source
    assert ".workflow-step.is-active-position" in source
    assert ".workflow-step.is-next" in source
    assert ".workflow-step.is-upcoming" in source
    assert ".workflow-step.is-hidden" in source
    assert "transform 420ms" in source
    assert "@keyframes workflow-step-spin" in source
    assert "@media (max-width: 640px)" in source
    assert "@media (prefers-reduced-motion: reduce)" in source
    assert "phase129b: shared cinematic workflow overlays" not in source
    assert "generate-suggestions-document-stack" not in source
    assert "pipeline-workflow-orbit" not in source
    assert "pipeline-success-gif" not in source
    assert PLANNING_UI.read_text(encoding="utf-8").count("<style>") == 0


def test_step_tracks_update_from_state_without_rebuilding_every_poll():
    app_script = APP_JS.read_text(encoding="utf-8")
    planning_script = PLANNING_JS.read_text(encoding="utf-8")
    pipeline_render = app_script[app_script.index("function renderPipelineStageStepper"):app_script.index("function getPipelineSuccessKey")]
    suggestions_render = planning_script[planning_script.index("function renderGenerateSuggestionsSteps"):planning_script.index("function startGenerateSuggestionsStepTimer")]

    assert "getPipelineVisibleGroupIndex(pipeline.current_stage" in pipeline_render
    assert "target.children.length !== PIPELINE_VISIBLE_STAGE_GROUPS.length" in pipeline_render
    assert 'target.dataset.activeIndex = String(currentGroupIndex)' in pipeline_render
    assert "getWorkflowStepPositionClass" in pipeline_render
    assert "track.children.length !== GENERATE_SUGGESTIONS_STEPS.length" in suggestions_render
    assert 'track.dataset.activeIndex = String(cappedIndex)' in suggestions_render
    assert "getGenerateSuggestionsStepPositionClass" in suggestions_render
    assert "%" not in pipeline_render
    assert "%" not in suggestions_render


def test_phase129b_does_not_touch_backend_markers():
    markers = ("phase129b", "pipelineSuccessPlanningBtn", "auth-workflow-node")
    for relative in (
        "src/app/api.py",
        "src/app/services.py",
        "src/pipeline/collector.py",
        "src/matching/scorer.py",
        "batch_select_best_resume_variant.py",
    ):
        source = (ROOT / relative).read_text(encoding="utf-8")
        assert all(marker not in source for marker in markers), relative
