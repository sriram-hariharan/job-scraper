"""Static contracts for the shared ApplyLens fluid filter-select system."""

from pathlib import Path
from types import SimpleNamespace

from src.app.decisions_ui import decisions_dashboard
from src.app.planning_ui import advanced_diagnostics, planning_dashboard
from src.app.ui import executive_dashboard, pipeline_dashboard, scheduler_dashboard


ROOT = Path(__file__).resolve().parents[1]
COMPONENT = (ROOT / "frontend/executive-kpi/src/filter/FilterSelect.tsx").read_text(encoding="utf-8")
CSS = (ROOT / "frontend/executive-kpi/src/styles.css").read_text(encoding="utf-8")
BUILT_CSS = (ROOT / "src/app/static/build/executive-kpi/executive-kpi.css").read_text(encoding="utf-8")
BUILT_JS = (ROOT / "src/app/static/build/executive-kpi/executive-kpi.js").read_text(encoding="utf-8")
LEGACY_CSS = (ROOT / "src/app/static/styles.css").read_text(encoding="utf-8")
REDESIGN_CSS = (ROOT / "src/app/static/app_redesign.css").read_text(encoding="utf-8")


def _rule(selector: str) -> str:
    return CSS.split(f"{selector} {{", 1)[1].split("}", 1)[0]


def _shared_css() -> str:
    return CSS.split(".shared-filter-select {", 1)[1].split("#planningFiltersRoot {", 1)[0]


def test_public_api_and_portal_positioning_contract_remain_unchanged() -> None:
    props = COMPONENT.split("export type SharedFilterSelectProps = {", 1)[1].split("};", 1)[0]
    for prop in (
        "id:", "label:", "options:", "values:", "onChange:", "placeholder:",
        "allLabel?:", "mode:", "searchable?:", "disabled?:", "portalClassName?:",
    ):
        assert prop in props

    for contract in (
        "createPortal(", "document.body", 'placement = below < 190 && above > below ? "top" : "bottom"',
        "const minimumWidth = Math.min(240, availableWidth)",
        "Math.min(Math.max(rect.width, minimumWidth), availableWidth)",
        "Math.max(viewportPadding, window.innerWidth - width - viewportPadding)",
        'window.addEventListener("resize", handleViewportChange)',
        'window.addEventListener("scroll", handleViewportChange, true)',
        "applylens:shared-filter-select-open",
    ):
        assert contract in COMPONENT


def test_component_exposes_one_panel_rows_and_shared_state_hooks() -> None:
    assert COMPONENT.count('role="listbox"') == 1
    assert 'role="option"' in COMPONENT
    assert 'aria-selected={selected}' in COMPONENT
    assert 'data-state={open ? "open" : "closed"}' in COMPONENT
    assert 'data-searchable={searchable ? "true" : "false"}' in COMPONENT
    assert 'selected ? "is-selected"' in COMPONENT
    assert 'option.isAll ? "is-all"' in COMPONENT
    assert "shared-filter-select__check" in COMPONENT
    assert "shared-filter-select__dot--${option.tone}" in COMPONENT


def test_trigger_and_search_use_eucalyptus_without_electric_focus() -> None:
    shared = _shared_css().lower()
    trigger = _rule(".shared-filter-select__trigger").lower()
    search_focus = _rule(".shared-filter-select__search:focus-within").lower()

    assert "--shared-filter-accent: #3c746a" in shared
    assert "--shared-filter-accent-deep: #28564f" in shared
    # the trigger is now the owner of the shared filter-control sizing tokens;
    # the resolved values are unchanged (46px tall, 12px radius).
    assert "height: var(--filter-control-height)" in trigger
    assert "border-radius: var(--filter-control-radius)" in trigger
    assert "--filter-control-height: 46px" in CSS
    assert "--filter-control-radius: 12px" in CSS
    assert "background-image: none" in trigger
    assert "border-color: var(--filter-menu-search-focus)" in search_focus
    assert "box-shadow: 0 0 0 3px var(--filter-menu-search-ring)" in search_focus
    for forbidden in ("#2563eb", "#60a5fa", "#7c3aed", "electricblue", "violet"):
        assert forbidden not in shared


def test_menu_is_one_unified_surface_with_compact_borderless_rows() -> None:
    menu = _rule(".shared-filter-select__menu")
    options = _rule(".shared-filter-select__options")
    option = _rule(".shared-filter-select__option")

    assert "position: fixed" in menu
    assert "max-width: calc(100vw - 24px)" in menu
    assert "box-sizing: border-box" in menu
    assert "border-radius: 15px" in menu
    assert "overflow: hidden" in menu
    assert "display: grid" in options
    assert "overflow-y: auto" in options
    assert "min-height: 40px" in option
    assert "border: 0" in option
    assert "border-radius: 9px" in option
    assert "font-size: 14px" in option


def test_selected_check_motion_and_reduced_motion_are_shared() -> None:
    shared = _shared_css()
    selected = _rule(".shared-filter-select__option.is-selected")
    check = _rule(".shared-filter-select__check")

    assert "background: var(--filter-menu-accent-soft)" in selected
    assert "color: var(--filter-menu-accent-deep)" in selected
    assert "opacity: 0" in check
    assert "scale(0.76)" in check
    assert ".shared-filter-select__option.is-selected .shared-filter-select__check" in shared
    assert "@media (prefers-reduced-motion: reduce)" in shared


def test_semantic_tones_use_muted_non_blue_non_purple_palette() -> None:
    shared = _shared_css().lower()
    expected = {
        "ready": "#1f9d78",
        "strong": "#1f9d78",
        "choice": "#5c817d",
        "solid": "#4f927f",
        "tailor": "#89935e",
        "moderate": "#b08b43",
        "later": "#c8872c",
        "weak": "#b56f52",
        "unavailable": "#98a2b3",
    }
    for tone, color in expected.items():
        assert f".shared-filter-select__dot--{tone}" in shared
        assert f"background: {color}" in shared

    for forbidden in ("#2563eb", "#60a5fa", "#7c3aed", "purple", "maroon", "burgundy", "wine", "berry"):
        assert forbidden not in shared


def test_callers_share_the_primitive_without_visual_forks() -> None:
    callers = {
        "PlanningWorklist.tsx": 4,
        "ExecutiveQueue.tsx": 2,
        "OperationalDashboards.tsx": 1,
        "diagnostics/AdvancedDiagnosticsDashboard.tsx": 1,
        "scheduler/SchedulerHealthDashboard.tsx": 2,
    }
    source_root = ROOT / "frontend/executive-kpi/src"
    for relative, count in callers.items():
        source = (source_root / relative).read_text(encoding="utf-8")
        assert source.count("<SharedFilterSelect") == count

    assert ".advanced-diagnostics-scan-menu {" not in CSS
    assert ".scheduler-runs-filters .shared-filter-select__trigger" not in CSS


def test_shared_controls_are_excluded_from_every_legacy_button_catchall() -> None:
    for stylesheet in (LEGACY_CSS, REDESIGN_CSS):
        catchalls = [
            line for line in stylesheet.splitlines()
            if "button:not(" in line and ":not(.scan-workspace-surface-tab)" in line
        ]
        assert catchalls
        for selector in catchalls:
            assert ":not(.shared-filter-select__trigger)" in selector
            assert ":not(.shared-filter-select__option)" in selector

        generic_focus = ":where(a, button, input, select, textarea, [tabindex])"
        protected_focus = generic_focus + ":not(.shared-filter-select__trigger):not(.shared-filter-select__option):not(.shared-filter-select__search-input):focus-visible"
        assert protected_focus in stylesheet

    assert "[tabindex]:not(.shared-filter-select__trigger):not(.shared-filter-select__option):focus-visible" in LEGACY_CSS


def test_search_header_is_one_integrated_eucalyptus_owned_control() -> None:
    search = _rule(".shared-filter-select__search").lower()
    search_focus = _rule(".shared-filter-select__search:focus-within").lower()
    search_input = _rule(".shared-filter-select__search input").lower()
    search_input_focus = CSS.split(
        ".shared-filter-select__search input:focus,", 1
    )[1].split("}", 1)[0].lower()
    shared = _shared_css().lower()

    assert 'classname="shared-filter-select__search-input"' in COMPONENT.lower()
    for declaration in (
        "width: calc(100% - 4px)", "max-width: calc(100% - 4px)",
        "min-width: 0", "min-height: 48px", "box-sizing: border-box",
        "border: 1px solid var(--filter-menu-search-border)", "border-radius: 11px",
        "background: var(--filter-menu-search-surface)",
    ):
        assert declaration in search

    for declaration in (
        "border-color: var(--filter-menu-search-focus)",
        "box-shadow: 0 0 0 3px var(--filter-menu-search-ring)",
    ):
        assert declaration in search_focus

    for declaration in (
        "appearance: none", "max-width: 100%", "min-width: 0", "min-height: 0",
        "padding: 0", "border: 0", "border-radius: 0", "outline: 0",
        "background: transparent", "background-image: none", "box-shadow: none",
        "font-size: 14px", "font-weight: 450", "line-height: 1.4",
    ):
        assert declaration in search_input
    for declaration in ("border: 0", "outline: 0", "background: transparent", "box-shadow: none"):
        assert declaration in search_input_focus

    for token in (
        "--filter-menu-search-surface: #f7faf9",
        "--filter-menu-search-border: #dce6e2",
        "--filter-menu-search-focus: #6f9f93",
        "--filter-menu-search-ring: rgba(60, 116, 106, 0.12)",
        "--filter-menu-search-icon: #667085",
        "--filter-menu-search-placeholder: #8a949f",
    ):
        assert token in shared
    for forbidden in ("#2563eb", "#3b82f6", "indigo", "violet", "var(--app-focus)"):
        assert forbidden not in search_focus


def test_important_legacy_input_visuals_exclude_search_input() -> None:
    exclusion = ":not(.shared-filter-select__search-input)"
    for stylesheet in (LEGACY_CSS, REDESIGN_CSS):
        prefix = f"input{exclusion}"
        assert prefix in stylesheet
        assert f"{prefix}:where(:not(.planning-bulk-results__search-input, .planning-bulk-results__checkbox))," in stylesheet
        assert f"{prefix}:where(:not(.planning-bulk-results__search-input, .planning-bulk-results__checkbox))::placeholder," in stylesheet
        assert f"input{exclusion}:focus:where(:not(.planning-bulk-results__search-input, .planning-bulk-results__checkbox))," in stylesheet
    assert f"input{exclusion}:focus-visible:where(:not(.planning-bulk-results__search-input, .planning-bulk-results__checkbox))," in LEGACY_CSS
    assert (
        f'html[data-theme="light"] input{exclusion}'
        ':where(:not(.planning-bulk-results__search-input, .planning-bulk-results__checkbox)),'
    ) in LEGACY_CSS


def test_source_contract_is_present_in_built_assets() -> None:
    compact_built_css = "".join(BUILT_CSS.split())
    for contract in (
        ".shared-filter-select__menu{--filter-menu-surface:#fff",
        "border-radius:15px",
        ".shared-filter-select__option.is-selected",
        ".shared-filter-select__search:focus-within",
        "html[data-theme=dark].shared-filter-select__menu",
    ):
        assert contract in compact_built_css

    built_trigger = compact_built_css.split(".shared-filter-select__trigger{", 1)[1].split("}", 1)[0]
    for declaration in (
        "width:100%",
        "max-width:100%",
        "min-width:0",
        "height:var(--filter-control-height)",
        "box-sizing:border-box",
    ):
        assert declaration in built_trigger
    built_option = compact_built_css.split(".shared-filter-select__option{", 1)[1].split("}", 1)[0]
    for declaration in ("display:grid", "width:100%", "min-height:40px", "border:0", "border-radius:9px"):
        assert declaration in built_option
    built_menu = compact_built_css.split(".shared-filter-select__menu{", 1)[1].split("}", 1)[0]
    for declaration in ("max-width:calc(100vw-24px)", "box-sizing:border-box", "border-radius:15px"):
        assert declaration in built_menu

    for contract in (
        "applylens:shared-filter-select-open",
        "shared-filter-select__menu",
        "shared-filter-select__option",
        "data-searchable",
    ):
        assert contract in BUILT_JS


def test_all_real_shared_select_hosts_use_one_fresh_bundle_marker(monkeypatch) -> None:
    styles_marker = "shared_filter_fluid_select_r2"
    release_marker = "eucalyptus_primary_shell_r1"
    action_marker = "eucalyptus_action_cascade_r2"
    admin_request = SimpleNamespace(
        state=SimpleNamespace(auth_user={"is_admin": True, "user_id": "shared-filter-contract"})
    )
    monkeypatch.setattr("src.app.planning_ui._saved_scan_context_options", lambda **_: [])
    action_hosts = (
        executive_dashboard(),
        planning_dashboard(),
        decisions_dashboard(),
    )
    stable_hosts = (
        scheduler_dashboard(admin_request),
        advanced_diagnostics(admin_request),
    )
    # styles.css keeps its per-route marker; the shared bundle carries one
    # deterministic marker on every host that renders it.
    for html in action_hosts:
        assert f"styles.css?v={action_marker}" in html
        assert f"app_redesign.css?v={release_marker}" in html
        for asset in ("executive-kpi.css", "executive-kpi.js"):
            assert f"{asset}?v={release_marker}" in html
            assert f"{asset}?v={action_marker}" not in html
    for html in stable_hosts:
        assert f"styles.css?v={styles_marker}" in html
        for asset in ("app_redesign.css", "executive-kpi.css", "executive-kpi.js"):
            assert f"{asset}?v={release_marker}" in html

    assert styles_marker not in pipeline_dashboard()
    assert (ROOT / "src/app/static/build/executive-kpi/executive-kpi.css").is_file()
    assert (ROOT / "src/app/static/build/executive-kpi/executive-kpi.js").is_file()


def test_shared_select_and_filter_containers_cannot_expand_page_width() -> None:
    root = _rule(".shared-filter-select")
    trigger = _rule(".shared-filter-select__trigger")
    for declaration in ("width: 100%", "max-width: 100%", "min-width: 0", "box-sizing: border-box"):
        assert declaration in root
        assert declaration in trigger
    advanced_controls = _rule(".advanced-diagnostics-hub-controls")
    assert "width: 100%" in advanced_controls
    assert "min-width: 0" in advanced_controls
    assert ".operational-filter-grid { display: grid; width: 100%; min-width: 0" in CSS
    assert ".scheduler-runs-filters { display: flex; width: 100%; min-width: 0" in CSS
