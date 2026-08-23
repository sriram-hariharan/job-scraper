"""Focused contracts for Item 7B's shared toolbar and account popover."""

import json
from pathlib import Path
import subprocess

from src.app.ui_shell import render_top_shell


ROOT = Path(__file__).resolve().parents[1]
SHELL_SOURCE = (ROOT / "src/app/ui_shell.py").read_text(encoding="utf-8")
SHELL_JS = (ROOT / "src/app/static/shell.js").read_text(encoding="utf-8")
SHELL_CSS = (ROOT / "src/app/static/app_redesign.css").read_text(encoding="utf-8")
ITEM7_CSS = SHELL_CSS.split("/* Item 7B:", 1)[1]

CACHE_OWNERS = (
    "src/app/application_hub_ui.py",
    "src/app/decisions_ui.py",
    "src/app/onboarding_ui.py",
    "src/app/planning_ui.py",
    "src/app/profile_ui.py",
    "src/app/ui.py",
)


def _function(source: str, name: str, next_name: str) -> str:
    return source.split(f"function {name}", 1)[1].split(f"function {next_name}", 1)[0]


def test_toolbar_is_a_compact_unframed_accessible_action_cluster() -> None:
    markup = render_top_shell("/")

    assert 'role="group" aria-label="Workspace controls"' in markup
    assert markup.count('id="notificationButton"') == 1
    assert markup.count('id="themeToggleBtn"') == 1
    assert 'href="/scan-workspace"' in markup
    assert 'aria-label="New Scan"' in markup
    assert markup.count('id="profileMenuButton"') == 1
    assert 'aria-controls="profileDropdown"' in markup
    assert "app-shell-toolbar-separator" not in markup
    assert "theme-toggle-track" not in markup

    assert "width: 42px !important" in ITEM7_CSS
    assert "min-width: 108px !important" in ITEM7_CSS
    assert "min-height: 42px !important" in ITEM7_CSS
    assert ".app-shell-top-right:not(.app-shell-top-right--flow)" in ITEM7_CSS
    for neutral_outer_surface in (
        "padding: 0 !important",
        "border: 0 !important",
        "border-radius: 0 !important",
        "background: transparent !important",
        "box-shadow: none !important",
        "backdrop-filter: none !important",
    ):
        assert neutral_outer_surface in ITEM7_CSS


def test_notification_button_click_opens_the_existing_surface() -> None:
    notification_functions = "function closeNotifications" + SHELL_JS.split(
        "function closeNotifications", 1
    )[1].split("async function loadUnreadCount", 1)[0]
    registration = "if (notificationButton && notificationDropdown)" + SHELL_JS.split(
        "if (notificationButton && notificationDropdown)", 1
    )[1].split("if (notificationRefreshBtn)", 1)[0]
    script = f"""
const state = {{ hidden: true, expanded: "false", listener: null }};
const notificationButton = {{
  addEventListener: (name, listener) => {{ if (name === "click") state.listener = listener; }},
  setAttribute: (name, value) => {{ if (name === "aria-expanded") state.expanded = value; }},
  getBoundingClientRect: () => ({{ left: 100, width: 42, bottom: 60 }}),
}};
const notificationDropdown = {{
  classList: {{
    contains: (name) => name === "hidden" && state.hidden,
    add: (name) => {{ if (name === "hidden") state.hidden = true; }},
    remove: (name) => {{ if (name === "hidden") state.hidden = false; }},
  }},
  style: {{ setProperty: () => {{}} }},
}};
const window = {{ innerWidth: 1200, innerHeight: 800 }};
const document = {{ documentElement: {{ clientWidth: 1200, clientHeight: 800 }} }};
const closeProfileMenu = () => {{}};
const loadNotifications = async () => {{}};
const loadUnreadCount = async () => {{}};
eval({json.dumps(notification_functions)});
eval({json.dumps(registration)});
(async () => {{
  await state.listener({{ stopPropagation: () => {{}} }});
  console.log(JSON.stringify({{ hidden: state.hidden, expanded: state.expanded }}));
}})();
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(result.stdout) == {"hidden": False, "expanded": "true"}


def test_account_popover_has_compact_grouped_navigation_and_exact_routes() -> None:
    markup = render_top_shell("/")

    assert 'id="profileDropdown"' in markup
    assert 'aria-labelledby="profileMenuButton"' in markup
    assert 'aria-hidden="true"' in markup
    for label in ("Workspace", "Settings", "Admin tools"):
        assert f">{label}</div>" in markup
    for href, label in (
        ("/profile/saved-scans", "Saved Scans"),
        ("/profile", "My Profile"),
        ("/profile/preferences", "Preferences"),
        ("/profile/ai-settings", "AI Settings"),
        ("/advanced-diagnostics", "Scan Diagnostics"),
        ("/agentic-operations", "Agentic Operations"),
        ("/scheduler", "Scheduler Health"),
    ):
        assert f'href="{href}"' in markup
        assert f">{label}</span>" in markup

    assert "profile-dropdown-nav-subtitle" not in markup
    assert "profile-dropdown-nav-arrow" not in markup
    assert "profile-dropdown-footer" in markup
    assert 'id="profileLogoutBtn"' in markup
    assert '{_icon_svg("logout")}' in SHELL_SOURCE


def test_scan_diagnostics_and_agentic_operations_use_distinct_icons() -> None:
    markup = render_top_shell("/")
    diagnostics = markup.split('id="profileAdvancedDiagnosticsLink"', 1)[1].split(
        "</a>", 1
    )[0]
    operations = markup.split('id="profileAgenticOperationsLink"', 1)[1].split(
        "</a>", 1
    )[0]

    assert "profile-dropdown-nav-icon--diagnostics" in diagnostics
    assert "profile-dropdown-nav-icon--agentic-operations" in operations
    assert '<circle cx="12" cy="5" r="3"/>' not in diagnostics
    assert '<circle cx="12" cy="5" r="3"/>' in operations


def test_admin_group_uses_existing_admin_predicate_and_hides_as_one_unit() -> None:
    predicate = _function(SHELL_JS, "setProfileShellUser", "loadProfileShellUser")

    assert 'qs("profileAdminToolsSection")' in SHELL_JS
    assert 'Boolean(user?.is_admin) || accessLevel === "admin"' in predicate
    assert 'profileAdminToolsSection.classList.toggle("hidden", !isAdmin)' in predicate
    assert (
        'profileAdminToolsSection.setAttribute("aria-hidden", '
        'isAdmin ? "false" : "true")'
    ) in predicate
    for owner in (
        "profileAdvancedDiagnosticsLink",
        "profileAgenticOperationsLink",
        "profileSchedulerHealthLink",
    ):
        assert f'{owner}.classList.toggle("hidden", !isAdmin)' in predicate
        assert f"{owner}.tabIndex = isAdmin ? 0 : -1" in predicate

    markup = render_top_shell("/")
    before_admin_id, after_admin_id = markup.split('id="profileAdminToolsSection"', 1)
    admin_section = before_admin_id.rsplit("<section", 1)[1] + after_admin_id.split(
        "</section>", 1
    )[0]
    assert 'class="profile-dropdown-section hidden"' in admin_section
    assert 'aria-hidden="true"' in admin_section


def test_popover_lifecycle_is_anchored_non_modal_and_restores_focus_on_escape() -> None:
    close_menu = _function(SHELL_JS, "closeProfileMenu", "openProfileMenu")
    open_menu = _function(SHELL_JS, "openProfileMenu", "userInitialFromName")

    assert 'dropdown.setAttribute("aria-hidden", "true")' in close_menu
    assert 'menuButton.setAttribute("aria-expanded", "false")' in close_menu
    assert "if (restoreFocus && wasOpen)" in close_menu
    assert "menuButton.focus()" in close_menu
    assert 'dropdown.setAttribute("aria-hidden", "false")' in open_menu
    assert 'menuButton.setAttribute("aria-expanded", "true")' in open_menu
    assert 'closeProfileMenu({ restoreFocus: true })' in SHELL_JS
    account_markup = render_top_shell("/").split('id="profileDropdown"', 1)[1].split(
        'id="floatingIntelligenceChat"', 1
    )[0]
    assert 'role="dialog"' not in account_markup


def test_popover_is_viewport_safe_and_deliberate_in_both_themes() -> None:
    for contract in (
        "width: min(348px, calc(100vw - 24px)) !important",
        "max-height: min(560px, calc(100dvh - 88px)) !important",
        "overflow-y: auto !important",
        "overscroll-behavior: contain",
        "grid-template-columns: 40px minmax(0, 1fr) !important",
        "grid-template-columns: 20px minmax(0, 1fr) !important",
        "min-height: 42px !important",
        "background: #111827 !important",
        'html[data-theme="light"] .profile-dropdown',
        "background: #ffffff !important",
        "@media (max-width: 680px)",
    ):
        assert contract in ITEM7_CSS

    assert ".profile-dropdown-section.hidden" in ITEM7_CSS
    assert "display: none !important" in ITEM7_CSS


def test_existing_theme_notification_and_logout_lifecycles_are_preserved() -> None:
    for contract in (
        'const JOBSTACK_THEME_KEY = "jobstack.theme"',
        "document.documentElement.dataset.bsTheme = safeTheme",
        "document.documentElement.style.colorScheme = safeTheme",
        'themeToggleBtn.setAttribute("aria-pressed",',
        'fetchJson("/notifications/unread-count")',
        'fetchJson(`/notifications?${params.toString()}`)',
        'fetchJson("/notifications/read-state", {',
        'fetchJson("/auth/logout", {',
        'method: "POST"',
    ):
        assert contract in SHELL_JS

    assert SHELL_JS.count('fetchJson("/auth/me")') == 1
    for forbidden in (
        "/application-actions",
        "/pipeline/run",
        "/scheduler/run",
        "/provider/",
        "/resume/mutate",
    ):
        assert forbidden not in SHELL_JS


def test_changed_shared_assets_use_one_finite_cache_key_on_shell_pages() -> None:
    for relative_path in CACHE_OWNERS:
        source = (ROOT / relative_path).read_text(encoding="utf-8")
        assert "/static/app_redesign.css?v=item7b_v1_toolbar_notification_r1" in source
        assert "/static/shell.js?v=item7b_account_toolbar_r1" in source
