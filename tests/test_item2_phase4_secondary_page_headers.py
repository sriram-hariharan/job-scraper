"""Item 2 Phase 4 — Secondary Page and Workspace Headers (static contract).

Protects: the reuse of the existing Item 2 Phase 3 .app-page-header CSS class
contract (no new contract, no page-specific title sizes) across My Profile,
Scan Workspace, and Tailoring Workspace, without changing titles,
descriptions, control IDs, routes, query parameters, workspace behavior, the
seven Phase 3 headers, the global shell, or Advanced Diagnostics'
disabled-execution boundary.

The former Job Intelligence (/intelligence), Applied Jobs (/applied), and
Saved for Later (/saved) header-contract assertions were removed in Item 2
Phase 4 Correction Pass 1 alongside the retirement of those standalone
routes; see tests/test_item2_phase4_profile_corrections_and_legacy_route_retirement.py.
"""

from pathlib import Path

from tests.support.phase_guard_registry import get_changed_files

ROOT = Path(__file__).resolve().parents[1]

APP_REDESIGN_CSS = (ROOT / "src/app/static/app_redesign.css").read_text(encoding="utf-8")
PROFILE_UI_SOURCE = (ROOT / "src/app/profile_ui.py").read_text(encoding="utf-8")
PLANNING_UI_SOURCE = (ROOT / "src/app/planning_ui.py").read_text(encoding="utf-8")
UI_SOURCE = (ROOT / "src/app/ui.py").read_text(encoding="utf-8")
DECISIONS_UI_SOURCE = (ROOT / "src/app/decisions_ui.py").read_text(encoding="utf-8")
APPLICATION_HUB_UI_SOURCE = (ROOT / "src/app/application_hub_ui.py").read_text(encoding="utf-8")
AUTH_UI_SOURCE = (ROOT / "src/app/auth_ui.py").read_text(encoding="utf-8")

ADVANCED_DIAGNOSTICS_TSX = (
    ROOT / "frontend/executive-kpi/src/diagnostics/AdvancedDiagnosticsDashboard.tsx"
).read_text(encoding="utf-8")


def _route_block(source: str, start_marker: str, end_marker: str) -> str:
    return source.split(start_marker, 1)[1].split(end_marker, 1)[0]


# --- 1-6. Pages migrated -----------------------------------------------------


def test_profile_uses_the_shared_header_contract():
    assert 'class="page-header app-page-header"' in PROFILE_UI_SOURCE
    assert 'class="app-page-header__main"' in PROFILE_UI_SOURCE
    assert 'class="app-page-header__title-row"' in PROFILE_UI_SOURCE
    assert 'class="app-page-header__title"' in PROFILE_UI_SOURCE
    assert 'class="subtext app-page-header__description"' in PROFILE_UI_SOURCE


def test_scan_workspace_uses_the_route_owned_header_contract():
    scan_route = _route_block(
        PLANNING_UI_SOURCE,
        '<title>AI Optimize Scan</title>',
        '<title>',
    )

    assert 'class="scan-workspace-header-shell scan-workspace-header-shell--minimal"' in scan_route
    assert 'class="scan-workspace-header-copy"' in scan_route
    assert '<h1>AI Optimize Scan</h1>' in scan_route
    assert 'class="scan-workspace-header-actions"' in scan_route
    assert "app-page-header" not in scan_route


def test_tailoring_workspace_uses_the_route_owned_header_contract():
    tailoring_route = _route_block(
        PLANNING_UI_SOURCE,
        '<title>Tailoring Workspace</title>',
        '<title>',
    )

    assert 'class="tailoring-workspace-header"' in tailoring_route
    assert '<h1 class="tailoring-workspace-title">Tailor resume</h1>' in tailoring_route
    assert 'class="tailoring-workspace-hero tailoring-workspace-context"' in tailoring_route
    assert "app-page-header" not in tailoring_route


# --- 7-8. Titles and descriptions unchanged ----------------------------------


def test_existing_page_titles_are_unchanged():
    assert "My Profile" in PROFILE_UI_SOURCE
    assert "AI Optimize Scan" in PLANNING_UI_SOURCE
    assert "Tailoring Workspace" in PLANNING_UI_SOURCE


def test_current_profile_description_and_tailoring_context_contracts():
    assert "Manage resume files and persisted Live Pipeline runs." in PROFILE_UI_SOURCE

    tailoring_route = _route_block(
        PLANNING_UI_SOURCE,
        '<title>Tailoring Workspace</title>',
        '<title>',
    )

    assert "AI tailoring workspace" in tailoring_route
    assert "Resume variant" in tailoring_route


# --- 9. No invented eyebrows --------------------------------------------------


def test_no_invented_eyebrows_were_added():
    for source in (PROFILE_UI_SOURCE,):
        assert "app-page-header__eyebrow" not in source

    scan_header = _route_block(
        PLANNING_UI_SOURCE,
        '<title>AI Optimize Scan</title>',
        '<title>',
    )
    tailoring_header = _route_block(
        PLANNING_UI_SOURCE,
        '<title>Tailoring Workspace</title>',
        '</header>',
    )
    assert "app-page-header__eyebrow" not in scan_header
    assert "app-page-header__eyebrow" not in tailoring_header


# --- 10-11. Wrapping and no ellipsis/nowrap on the shared title --------------


def test_long_title_wrapping_remains_enabled():
    title_rule = APP_REDESIGN_CSS.split(
        ".page .app-page-header .app-page-header__title-row .app-page-header__title {",
        1,
    )[1].split("}", 1)[0]
    assert "white-space: normal !important;" in title_rule
    assert "overflow-wrap: anywhere !important;" in title_rule


def test_workspace_titles_do_not_use_ellipsis_or_nowrap():
    scan_override = APP_REDESIGN_CSS.split(
        "body .scan-workspace-page.page > .app-page-header.scan-workspace-header-shell "
        ".app-page-header__title-row .app-page-header__title {",
        1,
    )[1].split("}", 1)[0]
    assert "text-overflow: ellipsis" not in scan_override
    assert "white-space: nowrap" not in scan_override
    assert "white-space: normal !important;" in scan_override
    # Must not introduce a page-specific size — same shared scale.
    assert "clamp(30px, 2.5vw, 36px)" in scan_override


# --- 12-16. Control IDs / core IDs preserved ----------------------------------


def test_profile_tabs_and_section_ids_remain():
    assert 'id="profileTabs"' in PROFILE_UI_SOURCE
    assert 'id="resumeSection"' in PROFILE_UI_SOURCE
    assert 'id="profilePipelineRunsSection"' in PROFILE_UI_SOURCE
    assert 'id="profileAdminUsersSection"' in PROFILE_UI_SOURCE


def test_scan_workspace_core_control_ids_remain():
    assert 'id="scanWorkspaceViewSampleBtn"' in PLANNING_UI_SOURCE
    assert "data-scan-mode-panel=" in PLANNING_UI_SOURCE
    assert "data-scan-initial-mode" in PLANNING_UI_SOURCE


def test_tailoring_workspace_core_control_ids_remain():
    assert "tailoring-workspace-hero" in PLANNING_UI_SOURCE
    assert "data-tailoring-json-path" in PLANNING_UI_SOURCE


# --- 17-19. Routes, query params, and behavior unchanged ---------------------


def test_scan_and_tailoring_routes_remain_unchanged():
    assert '@router.get("/scan-workspace", response_class=HTMLResponse)' in PLANNING_UI_SOURCE
    assert '@router.get("/tailoring-workspace", response_class=HTMLResponse)' in PLANNING_UI_SOURCE
    assert '@router.get("/profile", response_class=HTMLResponse)' in PROFILE_UI_SOURCE


def test_workspace_query_parameters_remain_supported():
    scan_route = _route_block(
        PLANNING_UI_SOURCE,
        '@router.get("/scan-workspace", response_class=HTMLResponse)\ndef scan_workspace_route(',
        ") -> str:",
    )
    for param in (
        "company: str = \"\"",
        "title: str = \"\"",
        "resume: str = \"\"",
        "job_doc_id: str = \"\"",
        "tailoring_json: str = \"\"",
        "saved_scan_id: str = \"\"",
        "output_dir: str = \"\"",
    ):
        assert param in scan_route


def test_legacy_scan_workspace_stylesheets_are_unchanged():
    changed = get_changed_files(ROOT)
    assert "src/app/static/scan_workspace.css" not in changed
    assert "src/app/static/scan_workspace_review.css" not in changed


# --- 20-21. Cache markers -----------------------------------------------------


def test_shared_shell_pages_use_the_eucalyptus_release_marker():
    sources = (
        UI_SOURCE,
        PLANNING_UI_SOURCE,
        DECISIONS_UI_SOURCE,
        APPLICATION_HUB_UI_SOURCE,
        PROFILE_UI_SOURCE,
    )
    assert sum(source.count("app_redesign.css?v=eucalyptus_primary_shell_r1") for source in sources) == 15
    assert sum(source.count("shell.js?v=eucalyptus_primary_shell_r1") for source in sources) == 15
    # the shared React bundle is one asset, so it carries one marker on every
    # host that renders it - never split across two release names.
    assert sum(source.count("executive-kpi.css?v=eucalyptus_primary_shell_r1") for source in sources) == 8
    assert sum(source.count("executive-kpi.js?v=eucalyptus_primary_shell_r1") for source in sources) == 8
    assert sum(source.count("executive-kpi.css?v=eucalyptus_action_cascade_r2") for source in sources) == 0
    assert sum(source.count("executive-kpi.js?v=eucalyptus_action_cascade_r2") for source in sources) == 0


def test_javascript_and_bundle_cache_markers_follow_the_eucalyptus_release():
    bundle_marker = "eucalyptus_primary_shell_r1"
    action_marker = "eucalyptus_action_cascade_r2"
    planning_marker = "planning_bulk_action_control_r1"
    shared_filter_marker = "shared_filter_fluid_select_r2"
    bulk_marker = "bulk_generate_suggestions_r2"
    release_css = f'/static/build/executive-kpi/executive-kpi.css?v={bundle_marker}'
    release_js = f'/static/build/executive-kpi/executive-kpi.js?v={bundle_marker}'
    action_css = f'/static/build/executive-kpi/executive-kpi.css?v={action_marker}'
    action_js = f'/static/build/executive-kpi/executive-kpi.js?v={action_marker}'

    planning_route = _route_block(
        PLANNING_UI_SOURCE,
        '@router.get("/planning", response_class=HTMLResponse)',
        '@router.get("/scan-workspace", response_class=HTMLResponse)',
    )
    tailoring_route = _route_block(
        PLANNING_UI_SOURCE,
        '@router.get("/tailoring-workspace", response_class=HTMLResponse)',
        '@router.get("/advanced-diagnostics", response_class=HTMLResponse)',
    )
    advanced_diagnostics_route = _route_block(
        PLANNING_UI_SOURCE,
        '@router.get("/advanced-diagnostics", response_class=HTMLResponse)',
        "\ndef scan_workspace(",
    )
    scan_workspace_renderer = PLANNING_UI_SOURCE.split("\ndef scan_workspace(", 1)[1]

    # Planning receives the rebuilt component and the two related cascade
    # stylesheets under one deterministic release marker.
    assert f'/static/styles.css?v={action_marker}' in planning_route
    assert '/static/app_redesign.css?v=eucalyptus_primary_shell_r1' in planning_route
    assert release_css in planning_route
    assert f'/static/planning.js?v={bulk_marker}' in planning_route
    assert release_js in planning_route
    assert action_css not in planning_route
    assert action_js not in planning_route
    assert '/static/shell.js?v=eucalyptus_primary_shell_r1' in planning_route

    assert release_css in UI_SOURCE
    assert release_js in UI_SOURCE
    assert release_css in advanced_diagnostics_route
    assert release_js in advanced_diagnostics_route
    assert f'/static/styles.css?v={shared_filter_marker}' in advanced_diagnostics_route
    assert '/static/app_redesign.css?v=eucalyptus_primary_shell_r1' in advanced_diagnostics_route

    # Tailoring Workspace and Scan Workspace retain their distinct historical
    # script ownership and never acquire the Planning-only marker.
    assert '/static/shell.js?v=eucalyptus_primary_shell_r1' in tailoring_route
    assert '/static/planning.js?v=planning_ui_20260512_tailoring_tabs8' in tailoring_route
    assert planning_marker not in tailoring_route
    assert '/static/shell.js?v=eucalyptus_primary_shell_r1' in scan_workspace_renderer
    assert '/static/planning.js?v=planning_ui_20260518_scan_replacement_markers' in scan_workspace_renderer
    assert '/static/scan_workspace.js?v=scan_workspace_rescan6_popover_phrase_scroll' in scan_workspace_renderer
    assert planning_marker not in scan_workspace_renderer


# --- 22. Onboarding/preferences/auth not migrated ----------------------------


def test_auth_and_shared_shell_preferences_receive_only_the_shared_css_release_marker():
    assert AUTH_UI_SOURCE.count("app_redesign.css?v=eucalyptus_primary_shell_r1") == 2
    assert "app_redesign.css?v=eucalyptus_primary_shell_r1" in PROFILE_UI_SOURCE


# --- 23. Advanced Diagnostics execution remains explicit ----------------------


def test_advanced_diagnostics_execution_requires_explicit_run():
    explicit_provider_actions = {
        "scanWorkspaceLiveTailoringSuggestionToggle": 'runStage("live_tailoring_suggestion")',
        "scanWorkspaceLiveExactChangeProposalToggle": 'runStage("live_exact_resume_change_proposal")',
    }
    for action_id, handler in explicit_provider_actions.items():
        button_block = ADVANCED_DIAGNOSTICS_TSX.split(f'id="{action_id}"', 1)[1].split("</button>", 1)[0]
        assert 'type="button"' in button_block
        assert "disabled" in button_block
        assert "onClick" in button_block
        assert handler in button_block


# --- 24. Global shell ownership remains stable -------------------------------


def test_global_shell_markup_and_mobile_ownership_remain_unchanged():
    changed = get_changed_files(ROOT)
    if "src/app/ui_shell.py" in changed:
        # Item 2 Phase 4 Correction Pass 1 intentionally adds a "diagnostics"
        # inline SVG icon to fix the profile-menu dark-mode icon bug; this is
        # the only shell change expected for this phase (see
        # tests/test_item2_phase4_profile_corrections_and_legacy_route_retirement.py).
        ui_shell_source = (ROOT / "src/app/ui_shell.py").read_text(encoding="utf-8")
        assert '"diagnostics": (' in ui_shell_source
        assert '_icon_svg("diagnostics")' in ui_shell_source
    shell_js = (ROOT / "src/app/static/shell.js").read_text(encoding="utf-8")
    assert "src/app/ui_shell.py" not in changed
    assert "const APP_SHELL_MENU_SVG" in shell_js
    assert 'collapseBtn.addEventListener("click"' in shell_js
    assert shell_js.count('menuBtn.addEventListener("click"') == 1
