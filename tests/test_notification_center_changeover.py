"""Focused checks for the notification-center changeover.

Discovery notifications are produced by the existing scheduler delivery path.
Nothing here adds a producer; these tests pin the read window, the compact
inbox markup/rendering, and the absence of a second notification writer.
"""

from __future__ import annotations

from pathlib import Path

from src.app import services

SHELL_JS = Path("src/app/static/shell.js").read_text(encoding="utf-8")
MARKUP = Path("src/app/ui_shell.py").read_text(encoding="utf-8")
STYLES = Path("src/app/static/styles.css").read_text(encoding="utf-8")
REDESIGN = Path("src/app/static/app_redesign.css").read_text(encoding="utf-8")


def test_notification_history_window_is_bounded_and_larger_than_the_old_twelve():
    assert "const NOTIFICATION_HISTORY_LIMIT = 50;" in SHELL_JS
    assert 'params.set("limit", String(NOTIFICATION_HISTORY_LIMIT));' in SHELL_JS
    assert 'params.set("limit", "12");' not in SHELL_JS
    # The feed no longer narrows the request to unread, so read history
    # (including already-read discovery runs) is reachable under All.
    load = SHELL_JS[
        SHELL_JS.index("async function loadNotifications(options = {})")
        : SHELL_JS.index("function renderFilteredNotifications()")
    ]
    assert 'params.set("is_read"' not in load


def test_server_read_path_stays_bounded():
    assert services._SCHEDULER_NOTIFICATION_READ_LIMIT == 500
    assert "selected = rows[: max(int(limit), 0)]" in Path(
        "src/app/services.py"
    ).read_text(encoding="utf-8")


def test_no_second_notification_producer_exists():
    scheduler = Path("src/pipeline/scheduler.py").read_text(encoding="utf-8")
    # Exactly one write site, still gated on the existing delivery payload.
    assert scheduler.count("write_notification_record_artifact(") == 1
    assert "if post_run_email_delivery_payload:" in scheduler
    notification = Path(
        "src/pipeline/post_run_notification.py"
    ).read_text(encoding="utf-8")
    assert '"notification_kind": "scheduled_run_email_delivery"' in notification
    assert 'notification_id = f"scheduled_run_email::{run_id}::{job_name}"' in notification
    # agent_discovery keeps its existing dedicated email rendering branch.
    email = Path("src/pipeline/post_run_email.py").read_text(encoding="utf-8")
    assert 'if job_name == "agent_discovery":' in email


def test_notification_center_markup_replaces_the_giant_card_dropdown():
    assert 'class="notification-center hidden" id="notificationDropdown"' in MARKUP
    assert 'role="dialog"' in MARKUP
    assert "notification-center__head" in MARKUP
    assert "notification-center__feed" in MARKUP
    assert "notification-center__foot" in MARKUP
    assert 'class="notification-center__identity"' in MARKUP
    assert 'class="notification-center__actions"' in MARKUP
    assert 'href="/scheduler"' in MARKUP
    # Old oversized affordances are gone.
    assert 'class="notification-dropdown hidden"' not in MARKUP
    assert "notification-unread-toggle" not in MARKUP
    assert "binary-toggle" not in MARKUP
    # Refresh is now an explicitly labelled control, not an icon-only box.
    assert "<span>Refresh</span>" in MARKUP


def test_notification_filters_are_compact_chips():
    for value in ("all", "unread", "pipeline", "discovery"):
        assert f'data-notification-filter="{value}"' in MARKUP
    assert 'role="tablist"' in MARKUP
    assert "notificationMatchesFilter" in SHELL_JS
    assert 'if (filter === "pipeline") return notificationTypeMeta(row).key === "pipeline";' in SHELL_JS
    assert 'if (filter === "discovery") return notificationTypeMeta(row).key === "discovery";' in SHELL_JS
    # Filtering is local: no request per filter.
    filters = SHELL_JS[
        SHELL_JS.index("function renderFilteredNotifications()")
        : SHELL_JS.index("async function updateNotificationReadState")
    ]
    assert "fetchJson" not in filters


def test_rows_use_real_job_names_for_type_identity():
    meta = SHELL_JS[
        SHELL_JS.index("function notificationTypeMeta(row)")
        : SHELL_JS.index("function notificationMatchesFilter")
    ]
    assert 'jobName === "agent_discovery"' in meta
    assert 'label: "Discovery"' in meta
    assert 'jobName === "live_pipeline"' in meta
    assert 'label: "Pipeline"' in meta


def test_compact_rows_carry_unread_type_status_time_and_row_action():
    render = SHELL_JS[
        SHELL_JS.index("function renderNotificationRows(")
        : SHELL_JS.index("async function fetchJson(")
    ]
    assert "notification-row__dot" in render
    assert "notification-row__tile is-${typeMeta.key}" in render
    assert "notification-pill is-${typeMeta.key}" in render
    assert "badgeMeta.className" in render
    assert "notification-row__time" in render
    assert "data-notification-toggle=" in render
    assert 'aria-label="${toggleLabel}"' in render
    assert "notification-row__sr" in render
    # The old giant card structure is gone.
    assert "notification-item" not in render
    assert "notification-item-actions" not in render
    assert "ghost-btn" not in render


def test_empty_states_are_compact_and_distinct():
    render = SHELL_JS[
        SHELL_JS.index("function renderNotificationRows(")
        : SHELL_JS.index("async function fetchJson(")
    ]
    assert "You're all caught up" in render
    assert "No unread notifications." in render
    assert "No notifications yet" in render
    assert "Scheduler activity will appear here." in render
    assert "notification-center__empty-icon" in render


def test_notification_center_styles_cover_semantics_and_both_themes():
    assert ".notification-center {" in STYLES
    assert ".notification-center__feed" in STYLES
    assert "overscroll-behavior: contain;" in STYLES
    assert ".notification-row.is-unread" in STYLES
    assert ".notification-row__tile.is-discovery" in STYLES
    assert ".notification-row__tile.is-pipeline" in STYLES
    assert ".notification-pill.is-discovery" in STYLES
    assert ".notification-pill.is-pipeline" in STYLES
    assert 'html[data-theme="dark"] .notification-center' in STYLES
    assert "prefers-reduced-motion" in STYLES


def test_read_state_mutation_still_uses_the_guarded_server_route():
    assert 'fetchJson("/notifications/read-state"' in SHELL_JS
    # Viewing is a safe GET; the mutation route is not in the safe allowlist.
    from src.app import api

    assert "/notifications" in api._BULK_SAFE_GET_PATHS
    assert "/notifications/read-state" not in api._BULK_SAFE_GET_PATHS


def test_refresh_control_renders_a_visible_sized_icon_with_a_label():
    """The icon previously relied on CSS sizing alone and rendered blank."""

    head = MARKUP[
        MARKUP.index("notification-center__refresh")
        : MARKUP.index('id="notificationMarkAllReadBtn"')
    ]
    assert 'aria-label="Refresh notifications"' in head
    assert 'title="Refresh notifications"' in head
    # Repository icon convention: explicit width/height attributes, like
    # _icon_svg(), so the glyph never depends on a stylesheet match.
    assert 'class="app-shell-icon"' in head
    assert 'width="14"' in head and 'height="14"' in head
    # Visible label, so the control is never a mystery box.
    assert "<span>Refresh</span>" in head
    assert "notification-center__refresh" in head
    assert 'stroke="currentColor"' in head
    assert 'd="M21 12a9 9 0 1 1-2.64-6.36"' in head
    assert 'd="M21 3v6h-6"' in head
    # Not an empty control.
    assert "<svg" in head and "</svg>" in head


def test_every_notification_icon_declares_explicit_dimensions():
    for marker in ('id="notificationRefreshBtn"', 'class="notification-center__tile"'):
        block = MARKUP[MARKUP.index(marker):]
        svg = block[block.index("<svg"): block.index("</svg>")]
        assert 'width="' in svg and 'height="' in svg
    row_icon = SHELL_JS[
        SHELL_JS.index("notification-row__tile is-${typeMeta.key}")
        : SHELL_JS.index("notification-row__body")
    ]
    assert 'width="15"' in row_icon and 'height="15"' in row_icon


def test_refresh_click_still_reloads_notifications_without_new_routes():
    handler = SHELL_JS[
        SHELL_JS.index("if (notificationRefreshBtn) {")
        : SHELL_JS.index("if (notificationMarkAllReadBtn)")
    ]
    assert "loadNotifications()" in handler
    assert "loadUnreadCount()" in handler
    assert "/notifications/read-state" not in handler


def test_notification_center_uses_a_scoped_plum_identity_not_electric_blue():
    block = STYLES[STYLES.index(".notification-center {"):]
    # Scoped variables keep the identity inside this component.
    for token in ("--nc-plum:", "--nc-primary-soft:", "--nc-plum-accent:"):
        assert token in block
    assert "#7a3e74" in block
    # The previous electric blue/violet interaction colours are gone.
    for banned in ("#4f46e5", "#2563eb", "#6366f1", "#7c3aed", "#a5b4fc", "#c7d2fe"):
        assert banned not in block, banned
    assert "linear-gradient(135deg, rgba(37, 99, 235" not in STYLES


def test_active_filter_uses_plum_and_inactive_stays_neutral():
    block = STYLES[STYLES.index(".notification-chip {"):]
    active = block[block.index(".notification-chip.is-active {"):]
    assert "background: var(--nc-plum);" in active
    assert "color: #ffffff;" in active
    inactive = block[: block.index(".notification-chip.is-active {")]
    # Inactive chips read neutral: app surface, neutral border, neutral ink.
    assert "background: var(--nc-surface);" in inactive
    assert "border: 1px solid var(--nc-border);" in inactive
    assert "color: var(--nc-ink);" in inactive


def test_pipeline_and_discovery_stay_distinct_and_semantics_stay_semantic():
    block = STYLES[STYLES.index(".notification-center {"):]
    assert "--nc-pipeline-fg: #76518c;" in block
    assert "--nc-discovery-fg: #0f8b8d;" in block
    assert "--nc-success-fg: #059669;" in block
    assert "--nc-attention-fg: #b45309;" in block
    assert "--nc-error-fg: #be123c;" in block
    assert ".notification-pill.is-success" in block
    assert ".notification-pill.is-error" in block


def test_unread_uses_plum_family_accents():
    block = STYLES[STYLES.index(".notification-row.is-unread {"):]
    assert "background: var(--nc-unread-surface);" in block
    assert "border-left-color: var(--nc-plum-accent);" in block
    dot = STYLES[STYLES.index(".notification-row.is-unread .notification-row__dot"):]
    assert "var(--nc-plum-accent)" in dot[:120]


def test_dark_theme_overrides_exist_for_the_notification_center():
    dark = STYLES[STYLES.index('html[data-theme="dark"] .notification-center {'):]
    for token in ("--nc-surface:", "--nc-ink:", "--nc-plum:", "--nc-discovery-fg:"):
        assert token in dark[:1600]
    assert 'html[data-theme="dark"] .notification-center__text-btn' in STYLES


NOTIFICATION_CONTROLS = (
    ".notification-btn",
    ".notification-chip",
    ".notification-center__icon-btn",
    ".notification-center__text-btn",
    ".notification-row__action",
)


def _generic_shared_button_rules(sheet):
    """Every rule whose selector is the shared app-wide button chain."""

    import re

    return [
        (match.group(1), match.group(2))
        for match in re.finditer(r"([^{}]+)\{([^{}]*)\}", sheet)
        if "button:not(.agentic-review-tab)" in match.group(1)
    ]


def test_generic_button_paint_cannot_repaint_notification_controls():
    """Shared button paint rules must exclude every notification control.

    The old blue/violet gradient was intentionally deleted (``--app-violet``
    was retired in favour of ``--app-secondary``), so this no longer pins that
    rule. The surviving invariant is what actually protects the notification
    centre: any app-wide button rule that paints a BACKGROUND must exclude all
    notification controls, or those controls get repainted.
    """

    # The generic primary/violet button gradient itself is gone; --app-violet
    # survives as a design token used by narrowly scoped rules only.
    assert (
        "linear-gradient(135deg, var(--app-primary), var(--app-violet))"
        not in REDESIGN
    ), "retired generic button gradient reintroduced"

    generic = _generic_shared_button_rules(REDESIGN)
    assert generic, "shared app-wide button chain disappeared"

    painting = []
    for selector, body in generic:
        declarations = {
            declaration.split(":", 1)[0].strip()
            for declaration in body.split(";")
            if ":" in declaration
        }
        if declarations & {"background", "background-image", "background-color"}:
            painting.append((selector, body))
    assert painting, "no shared button background rule left to guard"

    for selector, _body in painting:
        for control in NOTIFICATION_CONTROLS:
            assert f":not({control})" in selector, (control, selector[:80])

    # No rule that paints buttons app-wide may still match the notification
    # controls, in either stylesheet. This is the invariant that broke twice:
    # those rules use !important, so our normal rules could never win.
    import re

    controls = {
        "notification-chip",
        "notification-center__text-btn",
        "notification-row__action",
    }
    offenders = []
    for sheet, name in ((STYLES, "styles.css"), (REDESIGN, "app_redesign.css")):
        for match in re.finditer(r"([^{}]+)\{([^{}]*)\}", sheet):
            body = match.group(2)
            paints = "background" in body or "color" in body
            # Only !important rules can defeat our class-level selectors.
            if not (paints and "!important" in body):
                continue
            for sel in match.group(1).split(","):
                sel = sel.strip()
                if sel.split(":not(")[0].strip() not in ("button", "body button"):
                    continue
                excluded = set(re.findall(r":not\(\.([a-z0-9_-]+)\)", sel))
                missing = controls - excluded
                if missing:
                    offenders.append((name, sorted(missing), sel[:60]))
    assert not offenders, offenders


def test_panel_surfaces_are_neutral_not_plum():
    block = STYLES[STYLES.index(".notification-center {"): STYLES.index(".notification-center.hidden")]
    assert "--nc-surface: #ffffff;" in block
    assert "--nc-header: #fafafb;" in block
    assert "background: var(--nc-surface);" in block
    assert "border: 1px solid var(--nc-border);" in block

    head = STYLES[STYLES.index(".notification-center__head {"):]
    assert "background: var(--nc-header);" in head[:400]
    foot = STYLES[STYLES.index(".notification-center__foot {"):]
    assert "background: var(--nc-header);" in foot[:300]


def test_refresh_is_a_labelled_control_with_distinct_foreground():
    btn = STYLES[STYLES.index(".notification-center__text-btn {"):]
    rule = btn[: btn.index("}")]
    assert "background: var(--nc-primary-soft);" in rule
    assert "color: var(--nc-plum-strong);" in rule
    # Icon sits beside a visible label; the obsolete icon-only rules are gone.
    modifier = STYLES[STYLES.index(".notification-center__refresh {"):]
    assert "display: inline-flex" in modifier[:120]
    svg = STYLES[STYLES.index(".notification-center__refresh svg"):]
    assert "width: 14px" in svg[:140] and "display: block" in svg[:140]
    assert ".notification-center__icon-btn {" not in STYLES


def test_no_obsolete_notification_blocks_remain_in_either_stylesheet():
    import re

    legacy = re.compile(
        r"\.notification-(?:dropdown|item|list|toolbar|unread-toggle|"
        r"header-actions|refresh-btn|mark-all-btn|empty|toggle-btn|button)"
        r"[a-z0-9_-]*"
    )
    assert not legacy.findall(STYLES)
    assert not legacy.findall(REDESIGN)
    # One base block, one dark override, no duplicate active-filter block.
    assert len(re.findall(r"^\.notification-center \{", STYLES, re.M)) == 1
    assert len(re.findall(r'^html\[data-theme="dark"\] \.notification-center \{', STYLES, re.M)) == 1
    # One base active-filter rule plus one intentional dark override.
    assert len(re.findall(r"^\.notification-chip\.is-active \{", STYLES, re.M)) == 1
    assert len(re.findall(r'^html\[data-theme="dark"\] \.notification-chip\.is-active \{', STYLES, re.M)) == 1



def test_notification_center_styling_has_a_single_source_of_truth():
    """No legacy notification rules survive to override the new center."""

    import re

    legacy = re.compile(
        r"\.notification-(?:dropdown|item|list|toolbar|unread-toggle|"
        r"header-actions|refresh-btn|mark-all-btn|empty|toggle-btn|button)"
        r"[a-z0-9_-]*"
    )
    assert not legacy.findall(STYLES), sorted(set(legacy.findall(STYLES)))

    # Exactly one base rule for the panel, and no id-based override.
    assert len(re.findall(r"^\.notification-center \{", STYLES, re.M)) == 1
    assert "#notificationDropdown" not in STYLES

    # Everything still referenced by markup/JS keeps its styling.
    for live in (
        ".notification-shell",
        ".notification-btn",
        ".notification-badge",
    ):
        assert live in STYLES

    # The bell's sibling popover keeps its own responsive rule.
    assert ".profile-dropdown {" in STYLES


def test_row_read_unread_action_is_visible_at_rest_not_hover_only():
    """The action was opacity:0 until hover, on a transparent background."""

    rule = STYLES[STYLES.index(".notification-row__action {"):]
    base = rule[: rule.index("}")]

    # Visible at rest: no opacity trick, real surface, real border, real ink.
    assert "opacity: 1;" in base
    assert "opacity: 0;" not in base
    assert "background: var(--nc-primary-soft);" in base
    assert "border: 1px solid var(--nc-primary-border);" in base
    assert "color: var(--nc-plum-strong);" in base
    # The hover-only reveal is gone entirely.
    assert ".notification-row:hover .notification-row__action" not in STYLES

    # Glyph is optically centred inside a real box.
    assert "display: inline-grid;" in base
    assert "place-items: center;" in base
    assert "width: 26px;" in base and "height: 26px;" in base
    svg = STYLES[STYLES.index(".notification-row__action svg"):]
    assert "width: 14px" in svg[:120] and "display: block" in svg[:120]

    # Hover and keyboard focus still strengthen it.
    assert ".notification-row__action:hover {" in STYLES
    assert ".notification-row__action:focus-visible {" in STYLES
    assert '.notification-row__action[aria-disabled="true"]' in STYLES

    # Read rows no longer dim the whole row (which washed the action out).
    assert ".notification-row.is-read { opacity: 0.9; }" not in STYLES
    assert ".notification-row.is-read .notification-row__action {" in STYLES
    assert 'html[data-theme="dark"] .notification-row__action {' in STYLES


def test_row_action_renders_a_real_sized_icon_and_keeps_its_behaviour():
    render = SHELL_JS[
        SHELL_JS.index("function renderNotificationRows(")
        : SHELL_JS.index("async function fetchJson(")
    ]
    action = render[render.index("notification-row__action"):]

    # Real SVG with explicit dimensions, not a bare text glyph.
    assert 'width="14"' in action and 'height="14"' in action
    assert 'stroke="currentColor"' in action
    assert "\\u2713" not in action and "\\u2709" not in action
    # Distinct glyphs for the two states.
    assert 'd="M20 6 9 17l-5-5"' in action          # check -> mark read
    assert 'd="m22 7-10 5L2 7"' in action           # envelope -> mark unread

    # Behaviour and accessibility unchanged.
    assert 'data-notification-toggle="${notificationId}"' in action
    assert 'data-next-read="${isRead ? "false" : "true"}"' in action
    assert 'aria-label="${toggleLabel}"' in action
    assert 'title="${toggleLabel}"' in action


def test_row_action_remains_subject_to_the_bulk_mutation_guard():
    shell = Path("src/app/static/shell.js").read_text(encoding="utf-8")
    safe = shell[
        shell.index("function bulkGenerationControlIsSafe")
        : shell.index("function setBulkGenerationControlGuard")
    ]
    # Browsing controls are exempt; the row mutation action is not.
    assert ".notification-center__filters" in safe
    assert ".notification-center__foot" in safe
    assert "notification-row__action" not in safe
    assert "notificationMarkAllReadBtn" not in safe
    # The mutation still goes through the guarded server route.
    assert 'fetchJson("/notifications/read-state"' in shell


# ---------------------------------------------------------------------------
# Task A: the scheduler entry point owns its own environment initialization.
# ---------------------------------------------------------------------------

SCHEDULER_PY = Path("src/pipeline/scheduler.py").read_text(encoding="utf-8")


def test_scheduler_entry_point_loads_its_own_environment():
    assert "from dotenv import load_dotenv" in SCHEDULER_PY
    main_body = SCHEDULER_PY[
        SCHEDULER_PY.index("def main() -> int:") : SCHEDULER_PY.index("def main() -> int:") + 900
    ]
    # load_dotenv must run before argument parsing so every job branch, not just
    # the one that happens to import job_app, has DATABASE_URL for post-run
    # summary/outbox/notification persistence.
    load_call = 'load_dotenv(Path(__file__).resolve().parents[2] / ".env")'
    assert load_call in main_body
    assert main_body.index(load_call) < main_body.index("args = _parse_args()")


def test_scheduler_environment_init_does_not_depend_on_job_app_import():
    # The discovery command builder must not need job_app's import side effect.
    builder = SCHEDULER_PY[
        SCHEDULER_PY.index("def build_agent_discovery_command(") :
        SCHEDULER_PY.index("def build_live_pipeline_command(")
    ]
    assert "_job_app()" not in builder
    assert "import job_app" not in builder


def test_scheduler_never_prints_the_database_url_value():
    # "DATABASE_URL" legitimately appears as an env-var *name* argument; what
    # must never happen is the resolved value reaching stdout/stderr.
    printed = [
        line for line in SCHEDULER_PY.splitlines()
        if "print(" in line and "DATABASE_URL" in line
    ]
    assert printed == []
    assert 'os.environ.get("DATABASE_URL")' not in SCHEDULER_PY


# ---------------------------------------------------------------------------
# Task C: deterministic structured title presentation.
# ---------------------------------------------------------------------------


def test_notification_title_parser_uses_the_real_subject_grammar():
    # Matches the subjects built by src/pipeline/post_run_email.py.
    assert "NOTIFICATION_SUBJECT_PATTERN" in SHELL_JS
    assert "display_jobs=" in SHELL_JS
    assert "discovered=" in SHELL_JS
    assert "stage=" in SHELL_JS
    # The stale pattern that never matched the stored subjects is gone.
    assert "final_jobs=" not in SHELL_JS


def test_notification_title_parts_expose_headline_metric_and_full_value():
    parts = SHELL_JS[
        SHELL_JS.index("function notificationTitleParts(row) {") :
        SHELL_JS.index("function normalizeNotificationTitle(row) {")
    ]
    assert "headline" in parts and "metric" in parts and "full" in parts
    # Unknown formats fall back to a compact truncated title.
    assert "truncateNotificationTitle(raw)" in parts


def test_notification_row_renders_headline_with_full_title_tooltip():
    assert "titleParts.headline" in SHELL_JS
    assert 'data-tooltip="${escapeNotificationAttr(titleParts.full)}"' in SHELL_JS
    # Keyboard reachable, not hover-only.
    assert 'tabindex="0"' in SHELL_JS


def test_notification_metric_pill_is_rendered_when_present():
    assert 'notification-pill is-metric' in SHELL_JS
    assert ".notification-pill.is-metric {" in STYLES


def test_title_tooltip_shows_on_hover_and_keyboard_focus():
    assert ".notification-row__title[data-tooltip]::after {" in STYLES
    assert "content: attr(data-tooltip);" in STYLES
    assert (
        ".notification-row__title[data-tooltip]:hover::after,\n"
        ".notification-row__title[data-tooltip]:focus-visible::after {"
    ) in STYLES


# ---------------------------------------------------------------------------
# Task D: the email summary line is no longer presented in the feed.
# ---------------------------------------------------------------------------


def test_email_summary_text_is_not_rendered_in_the_feed():
    assert "Email summary prepared for" not in SHELL_JS
    assert "Email summary sent for" not in SHELL_JS
    assert "Email summary rendered in dry-run mode" not in SHELL_JS
    assert "notification-row__message" not in SHELL_JS
    assert "normalizeNotificationMessage" not in SHELL_JS


def test_email_delivery_status_is_still_served_and_stored():
    # Presentation-only change: the server still reads and returns the field.
    services_py = Path("src/app/services.py").read_text(encoding="utf-8")
    assert "delivery_status" in services_py
    payload = services.notifications_payload(
        None, None, None, None, limit=1, scheduler_notifications_visible=False
    )
    assert "delivery_status" in payload["filters"]


def test_row_badge_is_driven_by_run_status_not_by_email_summary_text():
    assert "notificationBadgeMeta" in SHELL_JS
    start = SHELL_JS.index("function notificationBadgeMeta(row) {")
    badge = SHELL_JS[start : SHELL_JS.index("\nfunction ", start + 1)]
    assert "row?.run_status" in badge
    assert "Email summary" not in badge


# ---------------------------------------------------------------------------
# Task F: deterministic read/unread mutation lifecycle.
# ---------------------------------------------------------------------------


def test_pending_mutations_are_tracked_per_notification_not_per_dom_node():
    # The old guard lived on the button element, which every refresh destroyed.
    assert "const notificationPendingIds = new Set();" in SHELL_JS
    assert "if (notificationPendingIds.has(notificationId)) return;" in SHELL_JS
    assert "notificationPendingIds.add(notificationId);" in SHELL_JS
    assert "notificationPendingIds.delete(notificationId);" in SHELL_JS


def test_only_the_in_flight_row_button_is_disabled():
    sync = SHELL_JS[
        SHELL_JS.index("function syncNotificationPendingButtons() {") :
        SHELL_JS.index("async function loadNotifications(options = {})")
    ]
    assert "notificationPendingIds.has(id)" in sync
    assert 'button.setAttribute("disabled", "disabled")' in sync
    assert 'button.removeAttribute("disabled")' in sync


def test_pending_state_is_reapplied_after_every_render():
    render = SHELL_JS[
        SHELL_JS.index("function renderFilteredNotifications() {") :
        SHELL_JS.index("document.querySelectorAll(\"[data-notification-filter]\")")
    ]
    assert "syncNotificationPendingButtons();" in render


def test_stale_notification_fetches_cannot_overwrite_newer_state():
    load = SHELL_JS[
        SHELL_JS.index("async function loadNotifications(options = {})") :
        SHELL_JS.index("function renderFilteredNotifications()")
    ]
    assert "notificationFetchToken += 1;" in load
    assert "if (token !== notificationFetchToken) return;" in load


def test_mutation_refresh_does_not_blank_the_feed():
    load = SHELL_JS[
        SHELL_JS.index("async function loadNotifications(options = {})") :
        SHELL_JS.index("function renderFilteredNotifications()")
    ]
    assert "const silent = Boolean(options.silent);" in load
    assert "if (!silent) {" in load
    # Background mutation reconciliation refreshes silently and is abortable.
    assert "loadNotifications({ silent: true, signal: controller.signal })" in SHELL_JS


def test_toggle_releases_authoritative_lock_before_background_reconciliation():
    handler = SHELL_JS[
        SHELL_JS.index('const toggleBtn = target.closest("[data-notification-toggle]");') :
    ]
    handler = handler[: handler.index("finally {") + 400]
    order = [
        handler.index("await updateNotificationReadState(notificationId, nextRead)"),
        handler.index("applyConfirmedNotificationReadState(notificationId, payload);"),
        handler.index("releaseNotificationMutation(notificationId);"),
        handler.index("startNotificationReconciliation();"),
    ]
    assert order == sorted(order)


def test_background_reconciliation_is_silent_bounded_and_preserves_tokens():
    reconciliation = SHELL_JS[
        SHELL_JS.index("async function reconcileNotificationsInBackground()") :
        SHELL_JS.index("document.querySelectorAll(\"[data-notification-filter]\")")
    ]
    assert "NOTIFICATION_RECONCILIATION_TIMEOUT_MS = 12000" in SHELL_JS
    assert "const controller = new AbortController();" in reconciliation
    assert "() => controller.abort()" in reconciliation
    assert "loadNotifications({ silent: true, signal: controller.signal })" in reconciliation
    assert "loadUnreadCount({ silent: true, signal: controller.signal })" in reconciliation
    assert "window.alert" not in reconciliation


def test_delete_releases_lock_before_background_reconciliation():
    handler = SHELL_JS[
        SHELL_JS.index("if (notificationDeleteConfirmBtn) {") :
        SHELL_JS.index("if (notificationList) {")
    ]
    assert handler.index("applyConfirmedNotificationDelete") < handler.index(
        "releaseNotificationMutation(notificationId);"
    )
    assert handler.index("releaseNotificationMutation(notificationId);") < handler.index(
        "startNotificationReconciliation();"
    )
    assert handler.index("applyConfirmedDeleteAll") < handler.index(
        "releaseNotificationGlobalMutation();"
    )


def test_header_has_separate_responsive_identity_and_action_rows():
    head = STYLES[STYLES.index(".notification-center__head {"):]
    head = head[: head.index(".notification-center__tile {")]
    assert "display: grid;" in head
    assert ".notification-center__identity {" in head
    assert ".notification-center__actions {" in head
    actions = head[head.index(".notification-center__actions {"):]
    assert "flex-wrap: wrap;" in actions
    assert "justify-content: flex-end;" in actions
    assert "position: absolute" not in head


def test_delete_confirmation_is_portaled_and_viewport_contained():
    assert "document.body.appendChild(notificationDeleteConfirmModal);" in SHELL_JS
    modal = STYLES[STYLES.index(".notification-delete-modal {"):]
    modal = modal[: modal.index('html[data-theme="dark"] .notification-delete-modal')]
    assert "position: fixed;" in modal
    assert "inset: 0;" in modal
    assert "place-items: center;" in modal
    assert "max-width: calc(100vw - 32px);" in modal
    assert "left:" not in modal


def test_confirmed_mutations_update_locally_before_background_reconciliation():
    toggle = SHELL_JS[SHELL_JS.index("const payload = await updateNotificationReadState"):]
    assert toggle.index("applyConfirmedNotificationReadState") < toggle.index("startNotificationReconciliation()")
    delete = SHELL_JS[SHELL_JS.index("const payload = await deleteNotification(notificationId)"):]
    assert delete.index("applyConfirmedNotificationDelete") < delete.index("startNotificationReconciliation()")
    assert "notificationConfirmedReadStates" in SHELL_JS
    assert "notificationConfirmedDeletedIds" in SHELL_JS


def test_read_state_mutation_remains_behind_the_bulk_guard():
    # /notifications/read-state must not be added to the bulk-safe allowlist.
    api = Path("src/app/api.py").read_text(encoding="utf-8")
    allowlist = api[
        api.index("_BULK_SAFE_GET_PATHS") : api.index("_BULK_SAFE_GET_PATHS") + 600
    ]
    assert "/notifications/read-state" not in allowlist


# ---------------------------------------------------------------------------
# Task G: durable notification deletion without source-artifact deletion.
# ---------------------------------------------------------------------------


def test_delete_controls_and_confirmation_copy_are_present_without_redesign():
    assert 'id="notificationDeleteAllBtn"' in MARKUP
    assert ">Delete all</button>" in MARKUP
    assert 'id="notificationDeleteConfirmModal"' in MARKUP
    assert "Delete notification?" in MARKUP
    assert "This removes it from Notifications. Scheduler history is not affected." in MARKUP
    assert 'id="notificationDeleteCancelBtn">Cancel</button>' in MARKUP
    assert 'id="notificationDeleteConfirmBtn">Delete</button>' in MARKUP


def test_row_delete_is_compact_accessible_and_does_not_share_navigation_click():
    render = SHELL_JS[
        SHELL_JS.index("function renderNotificationRows(") :
        SHELL_JS.index("async function fetchJson(")
    ]
    assert 'data-notification-delete="${notificationId}"' in render
    assert 'aria-label="Delete notification"' in render
    assert 'title="Delete notification"' in render
    assert "notification-row__delete" in render
    assert "M19 6l-1 14H6L5 6" in render
    handler = SHELL_JS[SHELL_JS.index('const deleteBtn = target.closest("[data-notification-delete]");'):]
    assert handler.index("event.preventDefault();") < handler.index("openNotificationDeleteConfirmation(")
    assert handler.index("event.stopPropagation();") < handler.index("openNotificationDeleteConfirmation(")


def test_delete_routes_use_tombstones_and_remain_bulk_guarded():
    services_py = Path("src/app/services.py").read_text(encoding="utf-8")
    schema = Path("src/storage/notification_state/schema.sql").read_text(encoding="utf-8")
    api = Path("src/app/api.py").read_text(encoding="utf-8")
    assert "is_deleted BOOLEAN NOT NULL DEFAULT FALSE" in schema
    assert "owner_user_id TEXT NOT NULL DEFAULT ''" in schema
    assert '_NOTIFICATION_DELETE_ALL_STATE_ID = "__all_notifications__"' in services_py
    assert '@app.post("/notifications/delete")' in api
    assert '@app.post("/notifications/delete-all")' in api
    allowlist = api[
        api.index("_BULK_SAFE_GET_PATHS") : api.index("_BULK_SAFE_GET_PATHS") + 900
    ]
    assert "/notifications/delete" not in allowlist
    assert "/notifications/delete-all" not in allowlist


def test_delete_modal_supports_both_required_confirmation_variants():
    confirmation = SHELL_JS[
        SHELL_JS.index("function openNotificationDeleteConfirmation(") :
        SHELL_JS.index("async function markAllNotificationsRead")
    ]
    assert '"Delete all notifications?"' in confirmation
    assert '"Delete notification?"' in confirmation
    assert "This removes all notifications from your inbox. Scheduler history is not affected." in confirmation
    assert "This removes it from Notifications. Scheduler history is not affected." in confirmation
    assert 'notificationDeleteConfirmBtn.textContent = deleteAll ? "Delete all" : "Delete";' in confirmation


def test_delete_and_read_share_the_same_per_notification_lock():
    assert 'if (notificationPendingIds.has(notificationId)) return;' in SHELL_JS
    delete_confirm = SHELL_JS[
        SHELL_JS.index("if (notificationDeleteConfirmBtn) {") :
        SHELL_JS.index("if (notificationList) {")
    ]
    assert "notificationPendingIds.add(notificationId);" in delete_confirm
    assert "releaseNotificationMutation(notificationId);" in delete_confirm
    release = SHELL_JS[
        SHELL_JS.index("function releaseNotificationMutation(notificationId)") :
        SHELL_JS.index("function releaseNotificationGlobalMutation()")
    ]
    assert "notificationPendingIds.delete(notificationId);" in release
    assert "notificationPendingActions.delete(notificationId);" in release
    assert "notificationGlobalMutationPending" in delete_confirm


def test_unread_count_has_independent_stale_response_protection():
    loader = SHELL_JS[
        SHELL_JS.index("async function loadUnreadCount(options = {})") :
        SHELL_JS.index("const notificationPendingIds")
    ]
    assert "notificationUnreadFetchToken += 1;" in loader
    assert "if (token !== notificationUnreadFetchToken) return;" in loader


def test_structured_bulk_409_uses_existing_bounded_message():
    fetcher = SHELL_JS[
        SHELL_JS.index("async function fetchJson(") :
        SHELL_JS.index("function resolveTableWrap")
    ]
    assert 'structuredDetail?.error_category === "bulk_generation_in_progress"' in fetcher
    assert "structuredDetail.message || BULK_GENERATION_BLOCK_MESSAGE" in fetcher
