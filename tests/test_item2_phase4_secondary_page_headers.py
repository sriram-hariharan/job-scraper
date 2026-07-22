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


def test_scan_workspace_uses_the_shared_header_contract():
    assert (
        'class="page-header scan-workspace-header-shell scan-workspace-header-shell--minimal app-page-header"'
        in PLANNING_UI_SOURCE
    )
    assert 'class="scan-workspace-header-copy app-page-header__title-row"' in PLANNING_UI_SOURCE
    assert '<h1 class="app-page-header__title">AI Optimize Scan</h1>' in PLANNING_UI_SOURCE
    assert 'class="scan-workspace-header-actions app-page-header__actions"' in PLANNING_UI_SOURCE


def test_tailoring_workspace_uses_the_shared_header_contract():
    assert 'class="page-header tailoring-workspace-header app-page-header"' in PLANNING_UI_SOURCE
    assert 'class="app-page-header__main"' in PLANNING_UI_SOURCE
    assert '<h1 class="app-page-header__title">Tailoring Workspace</h1>' in PLANNING_UI_SOURCE


# --- 7-8. Titles and descriptions unchanged ----------------------------------


def test_existing_page_titles_are_unchanged():
    assert "My Profile" in PROFILE_UI_SOURCE
    assert "AI Optimize Scan" in PLANNING_UI_SOURCE
    assert "Tailoring Workspace" in PLANNING_UI_SOURCE


def test_existing_descriptions_are_unchanged():
    assert "Manage resume files and persisted Live Pipeline runs." in PROFILE_UI_SOURCE
    assert (
        "Review suggested bullet replacements on the left and resume preview on the right."
        in PLANNING_UI_SOURCE
    )


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


def test_no_workspace_api_or_javascript_behavior_changed():
    changed = get_changed_files(ROOT)
    assert "src/app/static/scan_workspace.js" not in changed
    assert "src/app/static/scan_workspace.css" not in changed
    assert "src/app/static/scan_workspace_review.css" not in changed


# --- 20-21. Cache markers -----------------------------------------------------


def test_all_migrated_authenticated_pages_use_the_new_cache_marker():
    marker = "item2_phase4_secondary_headers_r1"
    occurrences = (
        UI_SOURCE.count(marker)
        + PLANNING_UI_SOURCE.count(marker)
        + DECISIONS_UI_SOURCE.count(marker)
        + APPLICATION_HUB_UI_SOURCE.count(marker)
        + PROFILE_UI_SOURCE.count(marker)
    )
    # 10 migrated routes x 1 app_redesign.css reference each, after the
    # Correction Pass 1 retirement of /intelligence, /applied, and /saved
    # removed their 3 former occurrences.
    assert occurrences == 10
    # Onboarding/preferences/auth keep their old marker (see test below).
    assert "app_redesign.css?v=scheduler_health_polish_r1" in PROFILE_UI_SOURCE


def test_javascript_and_bundle_cache_markers_are_unchanged_this_phase():
    old_bundle_marker = "item2_phase3_shared_header_r1"
    assert f"executive-kpi.css?v={old_bundle_marker}" in UI_SOURCE
    assert f"executive-kpi.js?v={old_bundle_marker}" in UI_SOURCE
    assert f"executive-kpi.css?v={old_bundle_marker}" in PLANNING_UI_SOURCE
    assert f"executive-kpi.js?v={old_bundle_marker}" in PLANNING_UI_SOURCE
    # shell.js / planning.js / scan_workspace.js markers untouched.
    assert 'shell.js?v=phase133h_r1' in UI_SOURCE
    assert 'planning.js?v=phase133g_s1_r1' in PLANNING_UI_SOURCE


# --- 22. Onboarding/preferences/auth not migrated ----------------------------


def test_onboarding_preferences_auth_headers_are_not_migrated_by_this_phase():
    changed = get_changed_files(ROOT)
    assert "src/app/auth_ui.py" not in changed
    assert "src/app/onboarding_ui.py" not in changed
    assert "app_redesign.css?v=scheduler_health_polish_r1" in PROFILE_UI_SOURCE  # /profile/preferences etc.


# --- 23. Advanced Diagnostics execution remains disabled ----------------------


def test_advanced_diagnostics_execution_remains_disabled():
    run_button_block = ADVANCED_DIAGNOSTICS_TSX.split(
        'className="advanced-diagnostics-run-btn"', 1
    )[1].split("</button>", 1)[0]
    assert "disabled" in run_button_block
    assert "onClick" not in run_button_block


# --- 24. Global shell markup unchanged ---------------------------------------


def test_global_shell_markup_remains_unchanged():
    changed = get_changed_files(ROOT)
    if "src/app/ui_shell.py" in changed:
        # Item 2 Phase 4 Correction Pass 1 intentionally adds a "diagnostics"
        # inline SVG icon to fix the profile-menu dark-mode icon bug; this is
        # the only shell change expected for this phase (see
        # tests/test_item2_phase4_profile_corrections_and_legacy_route_retirement.py).
        ui_shell_source = (ROOT / "src/app/ui_shell.py").read_text(encoding="utf-8")
        assert '"diagnostics": (' in ui_shell_source
        assert '_icon_svg("diagnostics")' in ui_shell_source
    assert "src/app/static/shell.js" not in changed
