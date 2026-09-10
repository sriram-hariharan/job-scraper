"""Focused contracts for the normal-user ApplyLens App Guide."""

from pathlib import Path
import subprocess

from fastapi.testclient import TestClient

from src.app import api
from src.app.guide_ui import TOPICS, TERMS, TOPIC_META, app_guide_page
from src.app.ui_shell import NAV_ITEMS, render_top_shell
from src.auth.runtime import HTML_NAVIGATION_PATHS


ROOT = Path(__file__).resolve().parents[1]
GUIDE_SOURCE = (ROOT / "src/app/guide_ui.py").read_text(encoding="utf-8")
GUIDE_JS = (ROOT / "src/app/static/app_guide.js").read_text(encoding="utf-8")
GUIDE_CSS = (ROOT / "src/app/static/app_guide.css").read_text(encoding="utf-8")
SHELL_CSS = (ROOT / "src/app/static/app_redesign.css").read_text(encoding="utf-8")


def _main_markup() -> str:
    return app_guide_page().split('<main class="page app-guide-page"', 1)[1].split("</main>", 1)[0]


def test_authenticated_normal_user_can_open_guide(monkeypatch) -> None:
    def authenticated_guard(request):
        request.state.auth_user = {
            "user_id": "guide-user",
            "email": "guide-user@example.test",
            "access_level": "user",
            "is_admin": False,
        }
        return None

    monkeypatch.setattr(api, "auth_guard_response", authenticated_guard)
    response = TestClient(api.app).get("/guide")

    assert response.status_code == 200
    assert "ApplyLens AI Guide" in response.text
    assert "/guide" in HTML_NAVIGATION_PATHS


def test_guide_is_one_global_toolbar_control_in_the_required_order() -> None:
    active_shell = render_top_shell("/guide")
    normal_shell = render_top_shell("/")

    assert active_shell.count('href="/guide"') == 1
    assert 'class="app-shell-guide-link active"' in active_shell
    assert 'aria-label="App Guide"' in active_shell
    assert 'aria-current="page"' in active_shell
    assert '<span class="app-shell-guide-link-label">Guide</span>' in active_shell
    assert "profile-dropdown-nav-icon--guide" not in active_shell
    assert '<span class="profile-dropdown-nav-title">App Guide</span>' not in active_shell
    assert 'class="app-shell-guide-link active"' not in normal_shell
    assert active_shell.index('href="/guide"') < active_shell.index('id="notificationShell"')
    assert active_shell.index('id="notificationShell"') < active_shell.index('id="themeToggleBtn"')
    assert active_shell.index('id="themeToggleBtn"') < active_shell.index('href="/scan-workspace"')
    assert active_shell.index('href="/scan-workspace"') < active_shell.index('id="profileMenuShell"')
    assert "/guide" not in {href for _label, href, _icon in NAV_ITEMS}
    assert {href for _label, href, _icon in NAV_ITEMS} == {
        "/", "/planning", "/decisions-ui", "/applications", "/pipeline"
    }


def test_focused_information_architecture_replaces_the_long_card_document() -> None:
    main = _main_markup()

    assert len(TOPICS) == 15
    assert len(TERMS) == 17
    assert main.count('data-guide-topic="') == 17  # Start, 15 feature areas, glossary.
    assert main.count("app-guide-workflow-step app-guide-tone-") == 6
    assert main.count('class="app-guide-diagram"') == 5
    assert 'class="app-guide-nav"' in main
    assert 'class="app-guide-content"' in main
    assert 'class="app-guide-rail"' in main
    assert 'id="appGuideTopicSelect"' in main
    assert 'data-guide-topic="start" tabindex="-1"' in main
    assert 'data-guide-topic="planning" hidden tabindex="-1"' in main
    assert "Get the most out of ApplyLens" in main
    assert "Find your next step." not in main
    assert main.count('class="app-guide-float-card ') == 3
    assert 'class="app-guide-featured"' in main
    assert 'class="app-guide-resume-art"' in main
    assert "<details" not in main
    assert "Expand all" not in main
    assert "Collapse all" not in main
    assert "app-guide-card-grid" not in main


def test_all_verified_normal_user_areas_and_high_confusion_actions_are_covered() -> None:
    main = _main_markup()
    required = (
        "Getting started &amp; Preferences", "Resumes &amp; versions", "Overview &amp; job queue",
        "Pipeline", "Planning", "Match &amp; readiness", "AI Suggestions &amp; Tailoring",
        "Bulk Suggestions", "New Scan &amp; Optimization Review", "Save, Compare &amp; Export",
        "Decisions", "Applications", "Saved Scans &amp; recent activity", "Notifications", "Job Assistant",
        "Matched", "Missing", "Alternative requirement", "AI Suggestions", "Exclude", "Excluded", "Re-include",
        "Generated / Ready", "Safe / no rewrite", "No usable rewrite", "Failed / attention", "eligible",
        "Rerun selected", "rerun all eligible", "PDF or DOCX", "ApplyLens does not submit",
    )
    for concept in required:
        assert concept in main


def test_trust_language_is_integrated_once_and_preserves_human_authority() -> None:
    main = _main_markup()

    assert main.count("app-guide-rail-card app-guide-rail-card--trust") == 1
    for statement in (
        "AI suggests. You decide.",
        "Your evidence is the boundary.",
        "not an employer ATS score or an interview guarantee",
        "Missing means enough evidence was not found",
        "Exclude is reversible",
        "Save is not Apply.",
        "Export creates a file",
        "Export is still yours; it does not submit.",
    ):
        assert statement in main


def test_search_is_local_grouped_deterministic_and_keyboard_accessible() -> None:
    main = _main_markup()

    assert 'type="search"' in main
    assert 'aria-live="polite"' in main
    for group in ("features", "terms", "actions"):
        assert f'data-guide-result-group="{group}"' in main
    assert main.count("data-guide-search-result") >= 45
    assert "fetch(" not in GUIDE_JS
    assert "XMLHttpRequest" not in GUIDE_JS
    assert "WebSocket" not in GUIDE_JS
    assert "normalizeGuideSearch" in GUIDE_JS
    assert "tokens.every" in GUIDE_JS
    assert "event.metaKey || event.ctrlKey" in GUIDE_JS
    assert 'event.key.toLocaleLowerCase() === "k"' in GUIDE_JS
    assert 'event.key !== "Escape"' in GUIDE_JS
    assert 'event.key === "ArrowDown"' in GUIDE_JS
    assert 'event.key === "ArrowUp"' in GUIDE_JS
    assert 'event.key === "Enter"' in GUIDE_JS
    assert "aria-activedescendant" in GUIDE_JS
    assert "setActiveResult" in GUIDE_JS
    assert "HTMLDetailsElement" not in GUIDE_JS
    subprocess.run(["node", "--check", str(ROOT / "src/app/static/app_guide.js")], check=True)


def test_contextual_glossary_and_reference_are_compact_not_card_grids() -> None:
    main = _main_markup()

    assert main.count('id="appGuideRailContext"') == 1
    assert main.count('id="appGuideRailChips"') == 1
    assert main.count('data-guide-glossary-term="') == len(TERMS)
    assert 'class="app-guide-glossary-list"' in main
    assert "app-guide-glossary-row app-guide-tone-" in main
    assert main.count("data-guide-glossary-select") == len(TERMS)
    assert "app-guide-glossary-card" not in main
    assert "data-guide-term" in main
    assert "aria-pressed" in GUIDE_JS
    sync_rail = GUIDE_JS.split("const syncRail =", 1)[1].split("const selectTopic =", 1)[0]
    assert 'const isGlossary = article?.dataset.guideTopic === "glossary"' in sync_rail
    assert "railContext.hidden = isStart || isGlossary" in sync_rail
    assert "if (isStart || isGlossary" in sync_rail


def test_help_card_is_hidden_on_start_and_reuses_start_topic_navigation() -> None:
    main = _main_markup()
    sync_rail = GUIDE_JS.split("const syncRail =", 1)[1].split("const selectTopic =", 1)[0]

    assert 'id="appGuideRailHelp" hidden' in main
    assert "railHelp.hidden = isStart" in sync_rail
    assert "Explore the Guide from the beginning or search for a specific feature." in main
    assert '<a href="#guide-topic-start" id="appGuideBackToStart" data-guide-nav-target="start">Back to Start here' in main
    assert "Browse all topics" not in main
    assert "appGuideBrowseTopics" not in GUIDE_JS
    assert 'document.querySelectorAll("[data-guide-nav-target]")' in GUIDE_JS
    assert "selectTopic(trigger.dataset.guideNavTarget" in GUIDE_JS


def test_theme_responsive_focus_and_global_toolbar_contracts() -> None:
    for token in (
        'html[data-theme="light"] .app-guide-body',
        "@media (max-width: 1280px)",
        "@media (max-width: 900px)",
        "@media (max-width: 680px)",
        "@media (prefers-reduced-motion: reduce)",
        ".app-guide-nav-link:focus-visible",
        "grid-template-columns: minmax(220px, 240px) minmax(0, 1fr)",
        "grid-template-columns: minmax(0, 1fr) minmax(270px, 300px)",
        ".app-guide-mobile-nav",
    ):
        assert token in GUIDE_CSS
    for token in (
        ".app-shell-guide-link",
        ".app-shell-guide-link-label",
        '.app-shell-guide-link[aria-current="page"]',
        'html[data-theme="light"] .app-shell-guide-link',
    ):
        assert token in SHELL_CSS


def test_search_uses_one_focus_surface_and_readable_command_rows() -> None:
    main = _main_markup()

    assert 'class="app-guide-search-result-title"' in main
    assert 'class="app-guide-search-result-description"' in main
    assert 'class="app-guide-search-result-copy"' in main
    assert 'class="app-guide-search-result-icon"' in main
    assert 'class="app-guide-search-result-dot"' in main
    assert 'class="app-guide-search-input"' in main
    assert ".app-guide-search:focus-within" in GUIDE_CSS
    assert "#mainContent .app-guide-search input.app-guide-search-input:focus" in GUIDE_CSS
    assert "border: 0 !important" in GUIDE_CSS
    assert "box-shadow: none !important" in GUIDE_CSS
    assert "background: var(--guide-surface-raised)" in GUIDE_CSS
    assert "overflow-x: hidden" in GUIDE_CSS
    assert "overflow-wrap: anywhere" in GUIDE_CSS
    assert "white-space: normal" in GUIDE_CSS
    result_rule = GUIDE_CSS.split("#mainContent button.app-guide-search-result {", 1)[1].split("}", 1)[0]
    assert "grid-template-columns: 32px minmax(0, 1fr)" in result_rule
    assert "background: transparent !important" in result_rule
    assert "var(--app-action-primary)" not in result_rule


def test_desktop_grid_is_stable_for_every_active_topic_and_glossary() -> None:
    main = _main_markup()
    workspace_rule = GUIDE_CSS.split(".app-guide-workspace {", 1)[1].split("}", 1)[0]
    content_grid_rule = GUIDE_CSS.split(".app-guide-content-grid {", 1)[1].split("}", 1)[0]

    assert "grid-template-columns: minmax(220px, 240px) minmax(0, 1fr)" in workspace_rule
    assert "grid-template-columns: minmax(0, 1fr) minmax(270px, 300px)" in content_grid_rule
    assert ".app-guide-nav,\n.app-guide-content-scroll,\n.app-guide-content-grid,\n.app-guide-content,\n.app-guide-rail" in GUIDE_CSS
    assert "min-width: 0" in GUIDE_CSS
    assert "scrollbar-gutter: stable" in GUIDE_CSS
    assert main.count('class="app-guide-workspace"') == 1
    assert main.count('class="app-guide-content-grid"') == 1
    assert main.index('id="guide-topic-start"') < main.index('id="guide-topic-glossary"')
    assert "app-guide-workspace--glossary" not in main + GUIDE_CSS
    assert "data-guide-topic=\"glossary\"" in main


def test_reserved_header_and_single_center_right_scroll_contract() -> None:
    main = _main_markup()
    scroll_rule = GUIDE_CSS.split(".app-guide-content-scroll {", 1)[1].split("}", 1)[0]
    nav_rule = GUIDE_CSS.split(".app-guide-nav {", 1)[1].split("}", 1)[0]
    rail_rule = "position: sticky;" + GUIDE_CSS.split(".app-guide-rail {\n  position: sticky;", 1)[1].split("}", 1)[0]

    assert 'class="app-guide-global-header"' in main
    assert 'class="app-guide-content-scroll" id="appGuideContentScroll"' in main
    assert main.index('class="app-guide-global-header"') < main.index('class="app-guide-workspace"')
    assert main.index('class="app-guide-content"') < main.index('class="app-guide-rail"')
    assert "overflow-y: auto" in scroll_rule
    assert "scrollbar-gutter: stable" in scroll_rule
    assert "overflow-y: auto" in nav_rule
    assert "position: sticky" in rail_rule
    assert "overflow-y: auto" not in rail_rule
    assert "max-height: calc" not in rail_rule
    assert "app-shell-top-right" not in main


def test_informational_guide_controls_do_not_inherit_primary_cta_surfaces() -> None:
    main = _main_markup()
    popular_rule = GUIDE_CSS.split("#mainContent button.app-guide-popular-chip,", 1)[1].split("}", 1)[0]
    nav_search_rule = GUIDE_CSS.split("#mainContent button.app-guide-nav-search {", 1)[1].split("}", 1)[0]
    rail_rule = GUIDE_CSS.split(".app-guide-rail-term-row {", 1)[1].split("}", 1)[0]

    assert "var(--app-action-primary)" not in popular_rule + nav_search_rule + rail_rule
    assert "background-image: none !important" in popular_rule
    assert "background: var(--guide-surface-raised) !important" in nav_search_rule
    assert "border:" not in rail_rule
    assert "box-shadow:" not in rail_rule
    assert main.count('class="app-guide-rail-term-row"') == 4
    assert "app-guide-rail-term-list\"><button" not in main


def test_search_results_overlay_the_content_without_changing_grid_height() -> None:
    panel_rule = GUIDE_CSS.split(".app-guide-search-panel {", 1)[1].split("}", 1)[0]

    assert "position: absolute" in panel_rule
    assert "top: calc(100% + 9px)" in panel_rule
    assert "max-width: 100%" in panel_rule
    assert "min-width: 0" in panel_rule
    assert "z-index: 20" in GUIDE_CSS.split(".app-guide-search-shell {", 1)[1].split("}", 1)[0]


def test_job_assistant_reuses_shared_bottom_right_shell_positioning() -> None:
    shell = render_top_shell("/guide")
    launcher_rule = SHELL_CSS.split("#floatingIntelligenceChatButton {", 1)[1].split("}", 1)[0]

    assert "#floatingIntelligenceChatButton" not in GUIDE_CSS
    assert shell.count('id="floatingIntelligenceChatButton"') == 1
    assert shell.index('class="app-shell-top-right"') < shell.index('id="floatingIntelligenceChatButton"')
    assert "position: fixed !important" in launcher_rule
    assert "right: 28px !important" in launcher_rule
    assert "bottom: var(--floating-chat-launcher-bottom" in launcher_rule


def test_passive_surfaces_have_no_false_hover_or_button_semantics() -> None:
    main = _main_markup()

    assert main.count('class="app-guide-rail-term-row"') == 4
    assert "app-guide-rail-term-row:hover" not in GUIDE_CSS
    assert "app-guide-glossary-row:hover" not in GUIDE_CSS
    assert ".app-guide-featured:hover .app-guide-resume-sheet--front" not in GUIDE_CSS
    assert "cursor: pointer" not in GUIDE_CSS
    assert '<button type="button" class="app-guide-glossary-term"' in main
    assert '<a href="#guide-topic-glossary" data-guide-nav-target="glossary">See all terms' in main


def test_search_input_is_visually_reset_and_outer_surface_owns_focus() -> None:
    input_rule = GUIDE_CSS.split(
        "#mainContent .app-guide-search input.app-guide-search-input,", 1
    )[1].split("}", 1)[0]
    focus_rule = GUIDE_CSS.split(".app-guide-search:focus-within {", 1)[1].split("}", 1)[0]

    for declaration in (
        "border: 0 !important",
        "border-radius: 0 !important",
        "outline: 0 !important",
        "appearance: none",
        "background: transparent !important",
        "background-image: none !important",
        "box-shadow: none !important",
    ):
        assert declaration in input_rule
    assert "border-color:" in focus_rule
    assert "box-shadow:" in focus_rule


def test_header_canvas_and_horizontal_bounds_match_fixed_toolbar_geometry() -> None:
    header_rule = GUIDE_CSS.split(".app-guide-global-header {", 1)[1].split("}", 1)[0]
    body_rule = GUIDE_CSS.split(".app-guide-body {", 1)[1].split("}", 1)[0]
    workspace_rule = GUIDE_CSS.split(".app-guide-workspace {", 1)[1].split("}", 1)[0]
    scroll_rule = GUIDE_CSS.split(".app-guide-content-scroll {", 1)[1].split("}", 1)[0]
    page_rule = GUIDE_CSS.split("#mainContent.app-guide-page {", 1)[1].split("}", 1)[0]
    collapsed_rule = GUIDE_CSS.split(
        "body.app-shell-collapsed #mainContent.app-guide-page {", 1
    )[1].split("}", 1)[0]

    assert "width: 100%" in header_rule
    assert "min-width: 0" in header_rule
    assert "--guide-header-height: 78px" in body_rule
    assert "height: var(--guide-header-height)" in header_rule
    assert "border-bottom: 1px solid var(--guide-line)" in header_rule
    assert "calc(100vh - var(--guide-header-height))" in workspace_rule
    assert "calc(100dvh - var(--guide-header-height))" in workspace_rule
    assert ".app-guide-global-header::before" not in GUIDE_CSS
    assert ".app-guide-global-header::after" not in GUIDE_CSS
    assert "app-shell-top-right" not in GUIDE_CSS
    assert "margin-bottom: -" not in header_rule
    assert "width: calc(100% - var(--app-shell-width, 268px)) !important" in page_rule
    assert "margin-left: var(--app-shell-width, 268px) !important" in page_rule
    assert "box-sizing: border-box" in page_rule
    assert "width: calc(100% - var(--app-shell-collapsed-width, 68px)) !important" in collapsed_rule
    assert "html {" not in GUIDE_CSS
    assert "scrollbar-gutter: stable" in scroll_rule
    assert "width: 100vw" not in GUIDE_CSS
    assert "right: -" not in GUIDE_CSS


def test_right_rail_matches_compact_passive_target_structure() -> None:
    main = _main_markup()
    header_rule = GUIDE_CSS.split(".app-guide-rail-header {", 1)[1].split("}", 1)[0]
    check_rule = GUIDE_CSS.split(".app-guide-trust-check {", 1)[1].split("}", 1)[0]
    dot_rule = GUIDE_CSS.split(".app-guide-term-dot {", 1)[1].split("}", 1)[0]
    dot_inner_rule = GUIDE_CSS.split(".app-guide-term-dot i {", 1)[1].split("}", 1)[0]

    assert main.count('class="app-guide-rail-header"') == 3
    assert "display: flex" in header_rule
    assert "align-items: center" in header_rule
    assert main.count('class="app-guide-trust-check"') == 6
    assert "border-radius: 50%" in check_rule
    assert "background: var(--guide-green)" in check_rule
    assert main.count("app-guide-term-dot app-guide-term-dot--") == 4
    assert "width: 20px" in dot_rule and "height: 20px" in dot_rule
    assert "color-mix(" in dot_rule
    assert "width: 9px" in dot_inner_rule and "height: 9px" in dot_inner_rule
    assert main.count('class="app-guide-rail-term-row"') == 4
    assert "app-guide-rail-term-row:hover" not in GUIDE_CSS
    assert "cursor: pointer" not in GUIDE_CSS


def test_need_more_help_reuses_bulk_suggestions_icon_helper() -> None:
    rail_source = GUIDE_SOURCE.split("def _context_rail()", 1)[1].split("def app_guide_page", 1)[0]

    assert TOPIC_META["bulk"][0] == "layers"
    assert "Need more help?" in rail_source
    help_source = rail_source.split("Need more help?", 1)[0].rsplit("<section", 1)[1]
    assert "_icon('layers')" in help_source
    assert "_icon('search')" not in help_source


def test_workflow_badges_keep_readable_semantic_foregrounds_in_both_themes() -> None:
    main = _main_markup()
    step_rule = GUIDE_CSS.split(".app-guide-workflow-step {", 1)[1].split("}", 1)[0]
    amber_rule = GUIDE_CSS.split(".app-guide-workflow-step:nth-child(4) {", 1)[1].split("}", 1)[0]
    badge_rule = GUIDE_CSS.split(".app-guide-step-badge {", 1)[1].split("}", 1)[0]
    dark_tokens = GUIDE_CSS.split(".app-guide-body {", 1)[1].split("}", 1)[0]
    light_tokens = GUIDE_CSS.split('html[data-theme="light"] .app-guide-body {', 1)[1].split("}", 1)[0]

    badges = [f'<span class="app-guide-step-badge" aria-hidden="true">{number:02d}</span>' for number in range(1, 7)]
    assert all(badge in main for badge in badges)
    assert [main.index(badge) for badge in badges] == sorted(main.index(badge) for badge in badges)
    assert "--guide-step-foreground: var(--guide-badge-foreground)" in step_rule
    assert "--guide-step-foreground: var(--guide-badge-amber-foreground)" in amber_rule
    assert "color: var(--guide-step-foreground)" in badge_rule
    assert "width: 24px" in badge_rule and "height: 24px" in badge_rule
    assert "font-size: 11px" in badge_rule and "font-weight: 800" in badge_rule
    assert "opacity:" not in badge_rule
    assert "--guide-badge-foreground: #071426" in dark_tokens
    assert "--guide-badge-amber-foreground: #2b1900" in dark_tokens
    assert "--guide-badge-foreground: #ffffff" in light_tokens
    assert "--guide-badge-amber-foreground: #ffffff" in light_tokens


def test_approved_visual_system_has_semantic_depth_without_remote_media() -> None:
    main = _main_markup()

    for token in (
        "--guide-blue", "--guide-violet", "--guide-green", "--guide-teal",
        "--guide-amber", "--guide-rose", ".app-guide-hero-art",
        ".app-guide-featured", ".app-guide-resume-sheet", ".app-guide-rail-card--trust",
    ):
        assert token in GUIDE_CSS
    assert "https://" not in main
    assert "<img" not in main
    assert "😀" not in main


def test_guide_excludes_admin_provider_implementation_and_business_mutations() -> None:
    main = _main_markup().lower()
    for concept in (
        "agentic operations", "scan diagnostics", "scheduler health", "ai settings", "api key",
        "provider", "pipeline_run_id", "owner_id", "postgres", "redis", "sqlite", "database table",
        "worker", "subprocess", "json schema", "artifact path", "feature flag",
    ):
        assert concept not in main

    combined = GUIDE_SOURCE + GUIDE_JS
    for endpoint in (
        "/pipeline/run", "/planning/bulk", "/planning/saved-scan", "/application-actions",
        "/notifications/read-state",
    ):
        assert endpoint not in combined
    assert "fetch(" not in GUIDE_JS
