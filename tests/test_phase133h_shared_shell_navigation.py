"""Phase 133H — premium responsive application sidebar + shared shell.

These tests protect the shared shell renderer (src/app/ui_shell.py), the mobile
drawer / collapse behavior owner (src/app/static/shell.js), and the shell CSS
contract (src/app/static/app_redesign.css). They assert structure, ownership,
ARIA, state, and route contracts — never pixel values — per the Phase 133H spec.
"""

from pathlib import Path

from src.app.ui_shell import NAV_GROUPS, NAV_ITEMS, render_top_shell

ROOT = Path(__file__).resolve().parents[1]
UI_SHELL = ROOT / "src/app/ui_shell.py"
SHELL_JS = ROOT / "src/app/static/shell.js"
SHELL_CSS = ROOT / "src/app/static/app_redesign.css"

# Visible label -> existing route. "/" keeps its Executive route; only the
# visible label changes to "Overview".
MAIN_ROUTES = [
    ("/", "Overview"),
    ("/pipeline", "Pipeline"),
    ("/planning", "Planning"),
    ("/decisions-ui", "Decisions"),
    ("/applications", "Applications"),
    ("/scheduler", "Scheduler"),
]

# Distinctive geometry per icon so each nav item's Lucide icon is verifiable.
ICON_SIGNATURES = {
    "Overview": '<rect width="7" height="9" x="14" y="12" rx="1"/>',      # layout-dashboard
    "Planning": '<rect width="8" height="4" x="8" y="2" rx="1" ry="1"/>',  # clipboard-list
    "Decisions": '<path d="M13 6h8"/>',                                    # list-checks
    "Applications": '<path d="M22 13a18.15 18.15 0 0 1-20 0"/>',           # briefcase-business
    "Pipeline": '<rect width="8" height="8" x="13" y="13" rx="2"/>',       # workflow
    "Scheduler": '<circle cx="16" cy="16" r="6"/>',                        # calendar-clock
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_every_main_route_receives_the_shared_shell() -> None:
    for href, _label in MAIN_ROUTES:
        html = render_top_shell(href)
        assert 'id="appShell"' in html
        assert '<nav class="app-shell-nav" aria-label="Dashboard navigation">' in html
        assert 'id="appShellMenuBtn"' in html
        assert 'id="appShellOverlay"' in html


def test_visible_executive_label_is_overview_and_route_is_unchanged() -> None:
    assert ("Overview", "/", "overview") in NAV_ITEMS
    html = render_top_shell("/")
    assert '<span class="app-shell-nav-label">Overview</span>' in html
    # The visible "Executive" label is gone; the route "/" is preserved.
    assert "Executive" not in html
    assert 'href="/"' in html


def test_all_route_hrefs_are_unchanged() -> None:
    hrefs = {href for _label, href, _icon in NAV_ITEMS}
    assert hrefs == {
        "/",
        "/planning",
        "/decisions-ui",
        "/applications",
        "/pipeline",
        "/scheduler",
    }


def test_navigation_groups_map_only_to_existing_routes() -> None:
    labels = {label: (href, group) for group, items in NAV_GROUPS for (label, href, _i) in items}
    workspace = {label for group, items in NAV_GROUPS if group == "Workspace" for (label, _h, _i) in items}
    operations = {label for group, items in NAV_GROUPS if group == "Operations" for (label, _h, _i) in items}
    assert workspace == {"Overview", "Planning", "Decisions", "Applications"}
    assert operations == {"Pipeline", "Scheduler"}
    assert labels["Overview"] == ("/", "Workspace")
    assert labels["Pipeline"] == ("/pipeline", "Operations")


def test_group_labels_are_rendered_with_group_semantics() -> None:
    html = render_top_shell("/")
    assert '<div class="app-shell-nav-group" role="group" aria-label="Workspace">' in html
    assert '<div class="app-shell-nav-group" role="group" aria-label="Operations">' in html
    assert '<div class="app-shell-nav-group-label" aria-hidden="true">Workspace</div>' in html
    assert '<div class="app-shell-nav-group-label" aria-hidden="true">Operations</div>' in html


def test_exactly_one_aria_current_per_main_route() -> None:
    for href, _label in MAIN_ROUTES:
        html = render_top_shell(href)
        assert html.count('aria-current="page"') == 1
        assert html.count('class="app-shell-nav-link active"') == 1


def test_each_main_route_marks_its_own_item_active() -> None:
    for href, label in MAIN_ROUTES:
        html = render_top_shell(href)
        # The active anchor carries the active class, aria-current, and its href.
        active_anchor = html.split('class="app-shell-nav-link active"', 1)[1].split("</a>", 1)[0]
        assert f'href="{href}"' in active_anchor
        assert 'aria-current="page"' in active_anchor
        assert f'>{label}</span>' in active_anchor


def test_each_visible_item_has_its_expected_icon() -> None:
    html = render_top_shell("/")
    assert html.count('class="app-shell-nav-icon"') == len(MAIN_ROUTES)
    for _href, label in MAIN_ROUTES:
        assert ICON_SIGNATURES[label] in html


def test_desktop_expanded_state_exposes_labels() -> None:
    html = render_top_shell("/")
    for _href, label in MAIN_ROUTES:
        assert f'<span class="app-shell-nav-label">{label}</span>' in html


def test_collapsed_state_preserves_icons_and_accessible_names() -> None:
    # Markup always carries icon + accessible name (aria-label/title); the
    # collapsed rail hides labels via CSS while keeping the icon column.
    html = render_top_shell("/pipeline")
    for _href, label in MAIN_ROUTES:
        assert f'aria-label="{label}"' in html
        assert f'title="{label}"' in html
    assert html.count('class="app-shell-nav-icon"') == len(MAIN_ROUTES)
    css = _read(SHELL_CSS)
    assert "body.app-shell-collapsed .app-shell-nav-label" in css
    assert "body.app-shell-collapsed .app-shell-nav-group-label" in css


def test_mobile_trigger_exposes_correct_aria_state() -> None:
    html = render_top_shell("/")
    btn = html.split('id="appShellMenuBtn"', 1)[1].split("</button>", 1)[0]
    assert 'aria-expanded="false"' in btn
    assert 'aria-controls="appShell"' in btn
    assert 'aria-label="Open navigation"' in html


def test_shell_js_owns_a_single_mobile_drawer_lifecycle() -> None:
    js = _read(SHELL_JS)
    assert js.count("function openMobileDrawer") == 1
    assert js.count("function closeMobileDrawer") == 1
    assert 'document.body.classList.add("app-shell-mobile-open")' in js
    assert 'document.body.classList.remove("app-shell-mobile-open")' in js
    # Overlay open/close toggles the [hidden] state.
    assert "appShellOverlay.hidden = false" in js
    assert "appShellOverlay.hidden = true" in js


def test_shell_js_drawer_closes_on_escape_overlay_and_route_selection() -> None:
    js = _read(SHELL_JS)
    assert 'event.key === "Escape"' in js
    assert 'appShellOverlay.addEventListener("click"' in js
    assert 'target.closest(".app-shell-nav-link")' in js
    assert 'closeMobileDrawer({ restoreFocus: false })' in js


def test_shell_js_traps_focus_and_restores_to_trigger() -> None:
    js = _read(SHELL_JS)
    assert "function drawerFocusableElements" in js
    assert 'event.key === "Tab"' in js
    # Focus returns to the trigger on close.
    assert "menuBtn.focus()" in js


def test_body_scroll_lock_is_owned_by_css_open_class() -> None:
    css = _read(SHELL_CSS)
    assert "body.app-shell-mobile-open {" in css
    assert "overflow: hidden !important;" in css
    # Released above the mobile breakpoint.
    assert "@media (min-width: 981px)" in css


def test_menu_trigger_is_not_a_duplicate_collapse_owner() -> None:
    js = _read(SHELL_JS)
    # The sidebar collapse toggle is owned by the dedicated collapse button, not
    # the hamburger. setShellCollapsed drives aria-pressed on the collapse btn.
    assert 'qs("appShellCollapseBtn")' in js
    assert 'const collapseBtn = qs("appShellCollapseBtn")' in js
    # Exactly one click owner each for collapse and for the mobile trigger.
    assert js.count('collapseBtn.addEventListener("click"') == 1
    assert js.count('menuBtn.addEventListener("click"') == 1


def test_theme_toggle_and_new_scan_remain_functional() -> None:
    html = render_top_shell("/")
    assert 'id="themeToggleBtn"' in html
    assert 'href="/scan-workspace"' in html
    assert "New Scan" in html
    js = _read(SHELL_JS)
    assert 'themeToggleBtn.addEventListener("click"' in js


def test_logo_uses_canonical_asset_without_the_oversized_card() -> None:
    html = render_top_shell("/")
    assert 'src="/static/media/app-logo.svg"' in html
    # No duplicated app-name text alongside the canonical asset.
    assert "app-shell-brand-text" not in html
    css = _read(SHELL_CSS)
    assert "Phase 133H" in css
    # Compact brand row replaces the oversized floating logo card.
    assert ".app-shell-brand-logo {" in css
    assert "height: 40px !important;" in css


def test_single_navigation_source_of_truth() -> None:
    html = render_top_shell("/")
    assert html.count('<nav class="app-shell-nav"') == 1
    assert html.count('id="appShell"') == 1


def test_desktop_content_offset_reserves_sidebar_space() -> None:
    css = _read(SHELL_CSS)
    # Content offset still reserves the sidebar width on desktop...
    assert "margin-left: var(--app-shell-width" in css
    # ...and collapses to full width inside the mobile drawer breakpoint.
    assert "margin-left: 0 !important;" in css


def test_shell_renderer_adds_no_request_ownership() -> None:
    src = _read(UI_SHELL)
    assert "fetch(" not in src
    assert "XMLHttpRequest" not in src


def test_shell_js_remains_a_classic_script() -> None:
    js = _read(SHELL_JS)
    # Classic (non-module) script: no ESM import/export that would change its
    # loading contract or collide with the bridge scripts.
    assert "\nimport " not in js
    assert "\nexport " not in js
