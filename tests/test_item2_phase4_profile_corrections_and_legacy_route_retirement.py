"""Item 2 Phase 4 — Correction Pass 1: Profile Dark-Mode Icons, Compact
Pagination, and Legacy Route Retirement.

Protects the three Correction Pass 1 fixes:
1. Advanced Diagnostics / Scheduler Health profile-menu icons are readable in
   dark mode (inline SVG using currentColor, theme-aware foreground color).
2. Profile > Pipeline runs uses the same compact Previous / current-of-total /
   Next pagination model as the shared Overview/Planning tables.
3. The obsolete standalone /intelligence, /applied, and /saved routes are
   retired, while their active replacement surfaces (Applications, the
   floating Job Assistant, RAG/search APIs, saved scans) remain untouched.
"""

from pathlib import Path

from tests.support.phase_guard_registry import get_changed_files

ROOT = Path(__file__).resolve().parents[1]

UI_SHELL_SOURCE = (ROOT / "src/app/ui_shell.py").read_text(encoding="utf-8")
APP_REDESIGN_CSS = (ROOT / "src/app/static/app_redesign.css").read_text(encoding="utf-8")
PROFILE_JS_SOURCE = (ROOT / "src/app/static/profile.js").read_text(encoding="utf-8")
PROFILE_UI_SOURCE = (ROOT / "src/app/profile_ui.py").read_text(encoding="utf-8")
PLANNING_UI_SOURCE = (ROOT / "src/app/planning_ui.py").read_text(encoding="utf-8")
API_SOURCE = (ROOT / "src/app/api.py").read_text(encoding="utf-8")
AUTH_RUNTIME_SOURCE = (ROOT / "src/auth/runtime.py").read_text(encoding="utf-8")
APPLICATION_HUB_UI_SOURCE = (ROOT / "src/app/application_hub_ui.py").read_text(encoding="utf-8")
README_SOURCE = (ROOT / "README.md").read_text(encoding="utf-8")


def _block(source: str, start_marker: str, end_marker: str) -> str:
    return source.split(start_marker, 1)[1].split(end_marker, 1)[0]


# --- 1-12. Correction 1: dark-mode profile-menu icons ------------------------


def test_diagnostics_icon_paths_added_to_icon_registry():
    assert '"diagnostics": (' in UI_SHELL_SOURCE
    diagnostics_entry = _block(UI_SHELL_SOURCE, '"diagnostics": (', '),')
    assert 'm14 13-8.381 8.38a1 1 0 0 1-3.001-3L11 9.999' in diagnostics_entry
    assert '18.352 3.352a1.205 1.205 0 0 0-1.704 0' in diagnostics_entry


def test_advanced_diagnostics_link_uses_inline_diagnostics_icon():
    advanced_diagnostics_link = _block(
        UI_SHELL_SOURCE, 'id="profileAdvancedDiagnosticsLink"', "</a>"
    )
    assert '{_icon_svg("diagnostics")}' in advanced_diagnostics_link
    assert "<img" not in advanced_diagnostics_link
    assert "adv_diagnostics_img.svg" not in advanced_diagnostics_link


def test_scheduler_health_link_still_uses_inline_scheduler_icon():
    scheduler_link = _block(UI_SHELL_SOURCE, 'id="profileSchedulerHealthLink"', "</a>")
    assert '{_icon_svg("scheduler")}' in scheduler_link
    assert "<img" not in scheduler_link


def test_advanced_diagnostics_link_metadata_preserved():
    advanced_diagnostics_link = _block(
        UI_SHELL_SOURCE, 'href="/advanced-diagnostics"', "</a>"
    )
    assert 'id="profileAdvancedDiagnosticsLink"' in advanced_diagnostics_link
    assert 'data-admin-only="true"' in advanced_diagnostics_link
    assert "Advanced Diagnostics" in advanced_diagnostics_link
    assert "Admin workflow diagnostics" in advanced_diagnostics_link
    assert 'class="profile-dropdown-nav-arrow" aria-hidden="true">›</span>' in advanced_diagnostics_link


def test_scheduler_health_link_metadata_preserved():
    scheduler_link = _block(UI_SHELL_SOURCE, 'href="/scheduler"', "</a>")
    assert 'id="profileSchedulerHealthLink"' in scheduler_link
    assert 'data-admin-only="true"' in scheduler_link
    assert "Scheduler Health" in scheduler_link
    assert "Scheduled jobs, run outcomes, and persistence integrity" in scheduler_link


def test_profile_menu_icon_color_uses_theme_variable_not_hardcoded_hex():
    icon_rule = _block(APP_REDESIGN_CSS, ".profile-dropdown-nav-icon {", "}")
    assert "color: var(--app-text) !important;" in icon_rule
    assert "#0f172a" not in icon_rule


def test_profile_menu_icon_fix_has_no_filter_inversion_hack():
    icon_rule = _block(APP_REDESIGN_CSS, ".profile-dropdown-nav-icon {", "}")
    assert "filter" not in icon_rule
    assert "invert(" not in APP_REDESIGN_CSS.split(".profile-dropdown-nav-icon {", 1)[1][:400]


def test_no_new_theme_listener_was_added_for_profile_menu_icons():
    assert "data-theme" not in PROFILE_JS_SOURCE
    assert "MutationObserver" not in PROFILE_JS_SOURCE
    assert "profile-dropdown-nav-icon" not in PROFILE_JS_SOURCE


def test_advanced_diagnostics_svg_asset_still_exists_and_is_still_used_elsewhere():
    asset_path = ROOT / "src/app/static/media/adv_diagnostics_img.svg"
    assert asset_path.exists()
    assert "adv_diagnostics_img.svg" in PLANNING_UI_SOURCE


def test_advanced_diagnostics_svg_asset_no_longer_referenced_in_profile_menu():
    assert "adv_diagnostics_img.svg" not in UI_SHELL_SOURCE


def test_profile_menu_layout_and_arrows_are_unchanged():
    assert UI_SHELL_SOURCE.count('class="profile-dropdown-nav-arrow" aria-hidden="true">›</span>') >= 2
    assert 'class="profile-dropdown-nav-copy"' in UI_SHELL_SOURCE


def test_floating_job_assistant_widget_preserved():
    assert 'id="floatingIntelligenceChat"' in UI_SHELL_SOURCE
    assert 'src="/static/floating_intelligence_chat.js' in UI_SHELL_SOURCE
    assert (ROOT / "src/app/static/floating_intelligence_chat.js").exists()


# --- 13-23. Correction 2: compact pipeline-runs pagination -------------------


def test_build_pagination_sequence_helper_removed_from_profile_js():
    assert "buildPaginationSequence" not in PROFILE_JS_SOURCE


def test_pipeline_runs_pagination_renders_previous_current_next_only():
    render_fn = _block(
        PROFILE_JS_SOURCE, "function renderPipelineRunsPagination()", "\nfunction "
    )
    assert render_fn.count('data-pipeline-runs-page="${currentPage - 1}"') == 1
    assert render_fn.count('data-pipeline-runs-page="${currentPage + 1}"') == 1
    assert render_fn.count('aria-current="page"') == 1
    assert "is-active" not in render_fn
    assert "ellipsis" not in render_fn.lower()


def test_pipeline_runs_pagination_buttons_have_aria_labels_and_disabled_states():
    render_fn = _block(
        PROFILE_JS_SOURCE, "function renderPipelineRunsPagination()", "\nfunction "
    )
    assert 'aria-label="Previous pipeline runs page"' in render_fn
    assert 'aria-label="Next pipeline runs page"' in render_fn
    assert "profileState.pipelineRunsHasPrevious" in render_fn
    assert "profileState.pipelineRunsHasNext" in render_fn


def test_pipeline_runs_pagination_current_indicator_shows_page_of_total():
    render_fn = _block(
        PROFILE_JS_SOURCE, "function renderPipelineRunsPagination()", "\nfunction "
    )
    assert "${currentPage} / ${totalPages}" in render_fn


def test_pipeline_runs_pagination_meta_text_format_preserved():
    render_fn = _block(
        PROFILE_JS_SOURCE, "function renderPipelineRunsPagination()", "\nfunction "
    )
    assert "Showing ${startRow}-${endRow} of ${totalCount} · Page ${currentPage} of ${totalPages}" in render_fn


def test_pipeline_runs_pagination_ids_preserved():
    assert 'qs("pipelineRunsPaginationMeta")' in PROFILE_JS_SOURCE
    assert 'id="pipelineRunsPaginationActions"' in PROFILE_UI_SOURCE


def test_pipeline_runs_pagination_state_and_page_size_preserved():
    assert "pipelineRunsPaginationMeta" in PROFILE_JS_SOURCE
    assert "pipelineRunsPaginationActions" in PROFILE_JS_SOURCE
    assert "profileState.pipelineRunsPageSize || 15" in PROFILE_JS_SOURCE
    assert "function applyPipelineRunsPaginationPayload(data)" in PROFILE_JS_SOURCE
    assert "function loadPipelineRuns(" in PROFILE_JS_SOURCE


def test_pipeline_runs_click_delegation_handler_unchanged():
    handler_block = _block(
        PROFILE_JS_SOURCE,
        'qs("pipelineRunsPaginationActions")?.addEventListener("click"',
        "});",
    )
    assert 'closest("[data-pipeline-runs-page]")' in handler_block
    assert "button.disabled" in handler_block
    assert "loadPipelineRuns(targetPage)" in handler_block


def test_profile_js_cache_marker_bumped_only_on_pipeline_runs_page():
    assert (
        '<script src="/static/profile.js?v=item2_phase4_profile_corrections_r1"></script>'
        in PROFILE_UI_SOURCE
    )
    assert PROFILE_UI_SOURCE.count(
        '/static/profile.js?v=item2_phase4_profile_corrections_r1'
    ) == 1


def test_other_profile_js_cache_markers_are_untouched():
    assert '/static/profile.js?v=agentic_review_v1"></script>' in PROFILE_UI_SOURCE
    assert '/static/profile.js?v=preferences_guided_parity_r9"></script>' in PROFILE_UI_SOURCE
    assert (
        '/static/profile.js?v=profile_saved_scans_e5_discard_icon_profile_resume_roles_r10"></script>'
        in PROFILE_UI_SOURCE
    )


def test_pipeline_runs_api_payload_and_endpoint_untouched():
    changed = get_changed_files(ROOT)
    assert "src/app/services.py" not in changed


# --- 24-25. Correction 3: legacy route retirement ----------------------------


def test_intelligence_applied_saved_route_files_are_deleted():
    assert not (ROOT / "src/app/intelligence_ui.py").exists()
    assert not (ROOT / "src/app/applied_ui.py").exists()
    assert not (ROOT / "src/app/saved_ui.py").exists()


def test_intelligence_js_deleted_as_route_exclusive_asset():
    assert not (ROOT / "src/app/static/intelligence.js").exists()


def test_api_py_no_longer_imports_or_registers_retired_routers():
    assert "intelligence_ui" not in API_SOURCE
    assert "applied_ui" not in API_SOURCE
    assert "saved_ui" not in API_SOURCE
    assert "include_router(intelligence_ui_router)" not in API_SOURCE
    assert "include_router(applied_ui_router)" not in API_SOURCE
    assert "include_router(saved_ui_router)" not in API_SOURCE


def test_intelligence_removed_from_html_navigation_paths_applied_and_saved_still_absent():
    nav_paths_block = _block(AUTH_RUNTIME_SOURCE, "HTML_NAVIGATION_PATHS = {", "}")
    assert '"/intelligence"' not in nav_paths_block
    assert '"/applied"' not in nav_paths_block
    assert '"/saved"' not in nav_paths_block
    assert '"/applications"' in nav_paths_block
    assert '"/profile"' in nav_paths_block


def test_readme_no_longer_documents_the_retired_intelligence_route():
    assert "/intelligence" not in README_SOURCE
    assert "| Applications | `/applications`" in README_SOURCE


def test_applications_route_and_shared_asset_are_preserved():
    assert '@router.get("/applications", response_class=HTMLResponse)' in APPLICATION_HUB_UI_SOURCE
    assert "application_views.js" in APPLICATION_HUB_UI_SOURCE


def test_backend_apis_for_applied_saved_and_rag_are_preserved():
    assert '@app.post("/application-actions")' in API_SOURCE
    assert '@app.get("/applied-jobs")' in API_SOURCE


def test_saved_scans_profile_route_is_unrelated_and_preserved():
    assert '@router.get("/profile/saved-scans", response_class=HTMLResponse)' in PROFILE_UI_SOURCE


def test_no_redirect_compatibility_routes_added_for_retired_paths():
    for retired_path in ("/intelligence", "/applied", "/saved"):
        assert f'RedirectResponse(url="{retired_path}"' not in API_SOURCE
        assert f'redirect("{retired_path}"' not in API_SOURCE


def test_no_navigation_links_to_retired_routes_remain_in_the_shell():
    assert 'href="/intelligence"' not in UI_SHELL_SOURCE
    assert 'href="/applied"' not in UI_SHELL_SOURCE
    assert 'href="/saved"' not in UI_SHELL_SOURCE
