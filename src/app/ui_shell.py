from html import escape

# Navigation source of truth. Grouped for presentation only; hrefs, ordering of
# destinations, and internal ownership are unchanged. The visible label
# "Overview" maps to the existing Executive route ("/") — this is a
# presentation-label change only, not a route/API/storage rename.
NAV_GROUPS = [
    (
        "Workspace",
        [
            ("Overview", "/", "overview"),
            ("Planning", "/planning", "planning"),
            ("Decisions", "/decisions-ui", "decisions"),
            ("Applications", "/applications", "applications"),
        ],
    ),
    (
        "Operations",
        [
            ("Pipeline", "/pipeline", "pipeline"),
        ],
    ),
]

# Flat view retained for callers/tests that reason about the full route set.
NAV_ITEMS = [
    (label, href, icon)
    for _group, items in NAV_GROUPS
    for (label, href, icon) in items
]

DEFAULT_USER_NAME = "Account"
DEFAULT_USER_INITIAL = "A"

# Inline icon geometry mirrors the Lucide icon family already vendored for the
# React workspace (lucide-react). The shared shell is server-rendered classic
# HTML, not React, so the equivalent Lucide paths are embedded inline to keep a
# single consistent icon family without adding a dependency or a runtime.
_ICON_PATHS = {
    "overview": (
        '<rect width="7" height="9" x="3" y="3" rx="1"/>'
        '<rect width="7" height="5" x="14" y="3" rx="1"/>'
        '<rect width="7" height="9" x="14" y="12" rx="1"/>'
        '<rect width="7" height="5" x="3" y="16" rx="1"/>'
    ),
    "planning": (
        '<rect width="8" height="4" x="8" y="2" rx="1" ry="1"/>'
        '<path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/>'
        '<path d="M12 11h4"/><path d="M12 16h4"/><path d="M8 11h.01"/><path d="M8 16h.01"/>'
    ),
    "decisions": (
        '<path d="m3 17 2 2 4-4"/><path d="m3 7 2 2 4-4"/>'
        '<path d="M13 6h8"/><path d="M13 12h8"/><path d="M13 18h8"/>'
    ),
    "applications": (
        '<path d="M12 12h.01"/>'
        '<path d="M16 6V4a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/>'
        '<path d="M22 13a18.15 18.15 0 0 1-20 0"/>'
        '<rect width="20" height="14" x="2" y="6" rx="2"/>'
    ),
    "pipeline": (
        '<rect width="8" height="8" x="3" y="3" rx="2"/>'
        '<path d="M7 11v4a2 2 0 0 0 2 2h4"/>'
        '<rect width="8" height="8" x="13" y="13" rx="2"/>'
    ),
    "scheduler": (
        '<path d="M21 7.5V6a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h3.5"/>'
        '<path d="M16 2v4"/><path d="M8 2v4"/><path d="M3 10h5"/>'
        '<path d="M17.5 17.5 16 16.3V14"/><circle cx="16" cy="16" r="6"/>'
    ),
    "diagnostics": (
        '<path d="m14 13-8.381 8.38a1 1 0 0 1-3.001-3L11 9.999"/>'
        '<path d="M15.973 4.027A13 13 0 0 0 5.902 2.373c-1.398.342-1.092 2.158.277 2.601a19.9 19.9 0 0 1 5.822 3.024"/>'
        '<path d="M16.001 11.999a19.9 19.9 0 0 1 3.024 5.824c.444 1.369 2.26 1.676 2.603.278A13 13 0 0 0 20 8.069"/>'
        '<path d="M18.352 3.352a1.205 1.205 0 0 0-1.704 0l-5.296 5.296a1.205 1.205 0 0 0 0 1.704l2.296 2.296a1.205 1.205 0 0 0 1.704 0l5.296-5.296a1.205 1.205 0 0 0 0-1.704z"/>'
    ),
    "agentic-operations": (
        '<circle cx="12" cy="5" r="3"/><circle cx="5" cy="19" r="3"/>'
        '<circle cx="19" cy="19" r="3"/><path d="M12 8v4"/>'
        '<path d="M5 16v-4h14v4"/>'
    ),
    "ai-settings": (
        '<path d="M12 2a4 4 0 0 0-4 4v1.1A4.5 4.5 0 0 0 5.5 15H7v1a5 5 0 0 0 10 0v-1h1.5A4.5 4.5 0 0 0 16 7.1V6a4 4 0 0 0-4-4Z"/>'
        '<path d="M9 10h.01"/><path d="M15 10h.01"/>'
        '<path d="M9.5 14.5a4 4 0 0 0 5 0"/>'
    ),
    "menu": (
        '<line x1="4" x2="20" y1="6" y2="6"/>'
        '<line x1="4" x2="20" y1="12" y2="12"/>'
        '<line x1="4" x2="20" y1="18" y2="18"/>'
    ),
    "close": '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
    "collapse": (
        '<rect width="18" height="18" x="3" y="3" rx="2"/>'
        '<path d="M9 3v18"/><path d="m16 15-3-3 3-3"/>'
    ),
    "expand": (
        '<rect width="18" height="18" x="3" y="3" rx="2"/>'
        '<path d="M9 3v18"/><path d="m14 9 3 3-3 3"/>'
    ),
    "logout": (
        '<path d="M10 17l5-5-5-5"/><path d="M15 12H3"/>'
        '<path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/>'
    ),
}


def _icon_svg(name: str) -> str:
    paths = _ICON_PATHS.get(name, "")
    return (
        '<svg class="app-shell-icon" viewBox="0 0 24 24" width="20" height="20" '
        'fill="none" stroke="currentColor" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" '
        f'focusable="false">{paths}</svg>'
    )


def render_top_shell(active_href: str) -> str:
    toolbar_classes = "app-shell-top-right"
    if active_href in {"/onboarding", "/profile/preferences"}:
        toolbar_classes += " app-shell-top-right--flow"

    groups_html = []
    for group_label, items in NAV_GROUPS:
        links = []
        for label, href, icon in items:
            is_active = href == active_href
            active_class = " active" if is_active else ""
            active_current = ' aria-current="page"' if is_active else ""
            links.append(
                f"""
                <a
                  class="app-shell-nav-link{active_class}"
                  href="{escape(href)}"
                  data-nav-label="{escape(label)}"
                  aria-label="{escape(label)}"
                  {active_current}
                  title="{escape(label)}"
                >
                  <span class="app-shell-nav-icon" aria-hidden="true">{_icon_svg(icon)}</span>
                  <span class="app-shell-nav-label">{escape(label)}</span>
                </a>
                """.strip()
            )

        groups_html.append(
            f"""
            <div class="app-shell-nav-group" role="group" aria-label="{escape(group_label)}">
              <div class="app-shell-nav-group-label" aria-hidden="true">{escape(group_label)}</div>
              {''.join(links)}
            </div>
            """.strip()
        )

    return f"""
<button
  type="button"
  class="app-shell-menu-btn"
  id="appShellMenuBtn"
  aria-label="Open navigation"
  aria-controls="appShell"
  aria-expanded="false"
  title="Open navigation"
>
  <span class="app-shell-menu-btn-icon" aria-hidden="true">{_icon_svg("menu")}</span>
</button>

<div class="app-shell-overlay" id="appShellOverlay" hidden></div>

<aside class="app-shell" id="appShell" aria-label="Primary">
  <div class="app-shell-brand-row">
    <a class="app-shell-brand" href="/" aria-label="ApplyLens AI home">
      <img class="app-shell-brand-logo" src="/static/media/app-wordmark.svg?v=applylens_wordmark_r1" alt="ApplyLens AI" />
    </a>

    <button
      type="button"
      class="app-shell-collapse-btn"
      id="appShellCollapseBtn"
      aria-label="Collapse sidebar"
      aria-pressed="false"
      title="Collapse sidebar"
    >
      <span class="app-shell-collapse-icon" aria-hidden="true">{_icon_svg("collapse")}</span>
    </button>

    <button
      type="button"
      class="app-shell-close-btn"
      id="appShellCloseBtn"
      aria-label="Close navigation"
      title="Close navigation"
    >
      <span class="app-shell-close-icon" aria-hidden="true">{_icon_svg("close")}</span>
    </button>
  </div>

  <nav class="app-shell-nav" aria-label="Dashboard navigation">
    {''.join(groups_html)}
  </nav>
</aside>

<div class="{toolbar_classes}" role="group" aria-label="Workspace controls">
  <span class="bulk-generation-guard-description" id="bulkGenerationGuardDescription">
    Checking Bulk Generate status…
  </span>
  <div class="bulk-generation-guard-tooltip hidden" id="bulkGenerationGuardTooltip" role="tooltip"></div>

  <div class="notification-shell" id="notificationShell">
    <button
      type="button"
      class="notification-btn"
      id="notificationButton"
      aria-expanded="false"
      aria-haspopup="true"
      aria-label="Notifications"
      title="Notifications"
    >
      <img
        class="notification-btn-icon"
        src="/static/media/notif_icon.svg"
        alt=""
        aria-hidden="true"
      />
      <span class="notification-badge hidden" id="notificationBadge">0</span>
    </button>

    <div class="notification-center hidden" id="notificationDropdown" role="dialog" aria-label="Notifications">
      <header class="notification-center__head">
        <div class="notification-center__identity">
          <span class="notification-center__tile" aria-hidden="true">
            <svg class="app-shell-icon" viewBox="0 0 24 24" width="17" height="17"
                 fill="none" stroke="currentColor" stroke-width="2"
                 stroke-linecap="round" stroke-linejoin="round" focusable="false">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
              <path d="M13.73 21a2 2 0 0 1-3.46 0" />
            </svg>
          </span>
          <div class="notification-center__heading">
            <div class="notification-center__title">Notifications</div>
            <div class="notification-center__subtitle" id="notificationSubtitle">Activity from your automated workflows</div>
          </div>
          <span class="notification-center__unread hidden" id="notificationUnreadPill">0 new</span>
        </div>
        <div class="notification-center__actions" aria-label="Notification actions">
          <button type="button" class="notification-center__text-btn notification-center__refresh"
                  id="notificationRefreshBtn"
                  aria-label="Refresh notifications" title="Refresh notifications">
            <svg class="app-shell-icon" viewBox="0 0 24 24" width="14" height="14"
                 fill="none" stroke="currentColor" stroke-width="2"
                 stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
              <path d="M21 12a9 9 0 1 1-2.64-6.36" /><path d="M21 3v6h-6" />
            </svg>
            <span>Refresh</span>
          </button>
          <button type="button" class="notification-center__text-btn" id="notificationMarkAllReadBtn"
                  title="Mark all notifications read">Mark all read</button>
          <button type="button" class="notification-center__text-btn notification-center__delete-all"
                  id="notificationDeleteAllBtn" title="Delete all notifications">Delete all</button>
        </div>
      </header>

      <div class="notification-center__filters" role="tablist" aria-label="Notification filters">
        <button type="button" class="notification-chip is-active" role="tab" aria-selected="true"
                id="notificationFilterAll" data-notification-filter="all">All</button>
        <button type="button" class="notification-chip" role="tab" aria-selected="false"
                id="notificationUnreadOnly" data-notification-filter="unread">Unread</button>
        <button type="button" class="notification-chip" role="tab" aria-selected="false"
                data-notification-filter="pipeline">Pipeline</button>
        <button type="button" class="notification-chip" role="tab" aria-selected="false"
                data-notification-filter="discovery">Discovery</button>
      </div>

      <div class="notification-center__feed" id="notificationList" tabindex="0">
        <div class="notification-center__empty">Loading notifications...</div>
      </div>

      <footer class="notification-center__foot">
        <a class="notification-center__foot-link" href="/scheduler">View scheduler activity &#8594;</a>
      </footer>
    </div>
  </div>

  <section
    class="modal-backdrop notification-delete-modal hidden"
    id="notificationDeleteConfirmModal"
    role="dialog"
    aria-modal="true"
    aria-labelledby="notificationDeleteConfirmTitle"
    aria-describedby="notificationDeleteConfirmBody"
    aria-hidden="true"
  >
    <div class="modal-card notification-delete-modal__card" role="document">
      <div class="notification-delete-modal__icon" aria-hidden="true">
        <svg class="app-shell-icon" viewBox="0 0 24 24" width="18" height="18"
             fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round" stroke-linejoin="round" focusable="false">
          <path d="M3 6h18" /><path d="M8 6V4h8v2" />
          <path d="M19 6l-1 14H6L5 6" /><path d="M10 11v5" /><path d="M14 11v5" />
        </svg>
      </div>
      <div class="notification-delete-modal__copy">
        <h3 id="notificationDeleteConfirmTitle">Delete notification?</h3>
        <p id="notificationDeleteConfirmBody">This removes it from Notifications. Scheduler history is not affected.</p>
      </div>
      <div class="modal-actions notification-delete-modal__actions">
        <button type="button" class="notification-center__text-btn notification-delete-modal__cancel" id="notificationDeleteCancelBtn">Cancel</button>
        <button type="button" class="notification-center__text-btn notification-delete-modal__confirm" id="notificationDeleteConfirmBtn">Delete</button>
      </div>
    </div>
  </section>

  <button
    type="button"
    class="theme-toggle-btn"
    id="themeToggleBtn"
    aria-label="Switch to light theme"
    aria-pressed="false"
    title="Switch to light theme"
  >
    <img
      class="theme-toggle-icon"
      src="/static/media/dark_mode.svg"
      alt=""
      aria-hidden="true"
    />
  </button>

  <a
    class="app-shell-primary-link"
    href="/scan-workspace"
    aria-label="New Scan"
    title="New Scan"
  >
    <img
      class="app-shell-primary-link-icon"
      src="/static/media/plus.svg"
      alt=""
      aria-hidden="true"
    />
    <span class="app-shell-primary-link-label">New Scan</span>
  </a>

  <div class="profile-menu-shell" id="profileMenuShell">
    <button
      type="button"
      class="profile-avatar-btn"
      id="profileMenuButton"
      aria-expanded="false"
      aria-haspopup="true"
      aria-controls="profileDropdown"
      aria-label="Account"
      title="{escape(DEFAULT_USER_NAME)}"
    >
      {escape(DEFAULT_USER_INITIAL)}
    </button>

    <div
      class="profile-dropdown hidden"
      id="profileDropdown"
      aria-labelledby="profileMenuButton"
      aria-hidden="true"
    >
      <div class="profile-dropdown-identity">
        <span class="profile-dropdown-avatar" id="profileDropdownAvatar" aria-hidden="true">
          {escape(DEFAULT_USER_INITIAL)}
        </span>
        <span class="profile-dropdown-identity-copy">
          <span class="profile-dropdown-name" id="profileDropdownName">{escape(DEFAULT_USER_NAME)}</span>
          <span class="profile-dropdown-email subtext" id="profileDropdownEmail"></span>
        </span>
      </div>
      <div class="profile-dropdown-actions">
        <section class="profile-dropdown-section" aria-labelledby="profileWorkspaceSectionLabel">
          <div class="profile-dropdown-section-label" id="profileWorkspaceSectionLabel">Workspace</div>
          <nav class="profile-dropdown-nav" aria-labelledby="profileWorkspaceSectionLabel">
            <a class="profile-dropdown-nav-btn" href="/profile/saved-scans">
              <span class="profile-dropdown-nav-icon profile-dropdown-nav-icon--scans" aria-hidden="true">
                <img src="/static/media/scan_icon.svg" alt="" />
              </span>
              <span class="profile-dropdown-nav-title">Saved Scans</span>
            </a>

            <a class="profile-dropdown-nav-btn" href="/profile">
              <span class="profile-dropdown-nav-icon profile-dropdown-nav-icon--profile" aria-hidden="true">
                <img src="/static/media/profile_icon.svg" alt="" />
              </span>
              <span class="profile-dropdown-nav-title">My Profile</span>
            </a>
          </nav>
        </section>

        <section class="profile-dropdown-section" aria-labelledby="profileSettingsSectionLabel">
          <div class="profile-dropdown-section-label" id="profileSettingsSectionLabel">Settings</div>
          <nav class="profile-dropdown-nav" aria-labelledby="profileSettingsSectionLabel">
            <a class="profile-dropdown-nav-btn" href="/profile/preferences">
              <span class="profile-dropdown-nav-icon profile-dropdown-nav-icon--preferences" aria-hidden="true">
                <img src="/static/media/preferences_icon.svg" alt="" />
              </span>
              <span class="profile-dropdown-nav-title">Preferences</span>
            </a>

            <a class="profile-dropdown-nav-btn" href="/profile/ai-settings">
              <span class="profile-dropdown-nav-icon profile-dropdown-nav-icon--ai-settings" aria-hidden="true">
                {_icon_svg("ai-settings")}
              </span>
              <span class="profile-dropdown-nav-title">AI Settings</span>
            </a>
          </nav>
        </section>

        <section
          class="profile-dropdown-section hidden"
          id="profileAdminToolsSection"
          aria-labelledby="profileAdminToolsSectionLabel"
          aria-hidden="true"
        >
          <div class="profile-dropdown-section-label" id="profileAdminToolsSectionLabel">Admin tools</div>
          <nav class="profile-dropdown-nav" aria-labelledby="profileAdminToolsSectionLabel">
            <a
              class="profile-dropdown-nav-btn hidden"
              href="/advanced-diagnostics"
              id="profileAdvancedDiagnosticsLink"
              data-admin-only="true"
            >
              <span class="profile-dropdown-nav-icon profile-dropdown-nav-icon--diagnostics" aria-hidden="true">
                {_icon_svg("diagnostics")}
              </span>
              <span class="profile-dropdown-nav-title">Scan Diagnostics</span>
            </a>

            <a
              class="profile-dropdown-nav-btn hidden"
              href="/agentic-operations"
              id="profileAgenticOperationsLink"
              data-admin-only="true"
            >
              <span class="profile-dropdown-nav-icon profile-dropdown-nav-icon--agentic-operations" aria-hidden="true">
                {_icon_svg("agentic-operations")}
              </span>
              <span class="profile-dropdown-nav-title">Agentic Operations</span>
            </a>

            <a
              class="profile-dropdown-nav-btn hidden"
              href="/scheduler"
              id="profileSchedulerHealthLink"
              data-admin-only="true"
            >
              <span class="profile-dropdown-nav-icon profile-dropdown-nav-icon--scheduler" aria-hidden="true">
                {_icon_svg("scheduler")}
              </span>
              <span class="profile-dropdown-nav-title">Scheduler Health</span>
            </a>
          </nav>
        </section>

        <div class="profile-dropdown-footer">
          <button type="button" class="profile-dropdown-danger-btn" id="profileLogoutBtn">
            <span class="profile-dropdown-danger-icon" aria-hidden="true">{_icon_svg("logout")}</span>
            <span>Log out</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</div>

<div class="floating-intelligence-chat" id="floatingIntelligenceChat">
  <section
    class="floating-intelligence-chat-panel hidden"
    id="floatingIntelligenceChatPanel"
    role="dialog"
    aria-modal="true"
    aria-labelledby="floatingIntelligenceChatTitle"
    aria-describedby="floatingIntelligenceChatSubtitle"
    aria-busy="false"
  >
    <header class="floating-intelligence-chat-header">
      <span class="floating-intelligence-chat-avatar" aria-hidden="true">
        <svg viewBox="0 0 24 24" focusable="false">
          <circle cx="11" cy="11" r="6.2" fill="none" stroke="currentColor" stroke-width="1.9" />
          <path d="M15.6 15.6 20 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
          <path d="M11 7.6l.85 2.05 2.05.85-2.05.85L11 13.4l-.85-2.05-2.05-.85 2.05-.85z" fill="currentColor" />
        </svg>
      </span>
      <div class="floating-intelligence-chat-heading">
        <h2 id="floatingIntelligenceChatTitle">ApplyLens AI</h2>
        <p id="floatingIntelligenceChatSubtitle">Job intelligence assistant</p>
      </div>
      <span class="floating-intelligence-chat-status-badge">Job corpus</span>
      <button
        type="button"
        class="floating-intelligence-chat-header-btn"
        id="floatingIntelligenceNewChatBtn"
        aria-label="Start new chat"
        title="Start new chat"
      >
        <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
          <path
            d="M12 6v12M6 12h12"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
          />
        </svg>
      </button>
      <button
        type="button"
        class="floating-intelligence-chat-close-btn"
        id="floatingIntelligenceChatCloseBtn"
        aria-label="Close Job Assistant"
      >
        <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
          <path
            d="M7 7l10 10M17 7L7 17"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
          />
        </svg>
      </button>
    </header>

    <div class="floating-intelligence-chat-controls">
      <p class="floating-intelligence-chat-helper">The assistant will decide whether to search or answer.</p>
      <select id="floatingIntelligenceModeSelect" hidden aria-hidden="true" tabindex="-1">
        <option value="answer" selected>Answer</option>
        <option value="search">Search</option>
      </select>
    </div>

    <div class="floating-intelligence-chat-viewport">
      <div
        class="floating-intelligence-chat-messages"
        id="floatingIntelligenceMessages"
        role="log"
        aria-live="polite"
        aria-relevant="additions"
        aria-atomic="false"
        aria-labelledby="floatingIntelligenceChatTitle"
      >
        <p>Open the assistant to search jobs or ask grounded questions.</p>
      </div>
      <button
        type="button"
        class="floating-intelligence-chat-jump-btn"
        id="floatingIntelligenceJumpBtn"
        aria-label="Jump to latest message"
        hidden
      >
        <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
          <path
            d="M12 5.5v13M6.2 12.5 12 18.5l5.8-6"
            fill="none"
            stroke="currentColor"
            stroke-width="2.1"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
      </button>
    </div>

    <div class="floating-intelligence-chat-compose">
      <textarea
        id="floatingIntelligenceInput"
        rows="1"
        aria-label="Message ApplyLens AI"
        placeholder="Ask about roles, companies, requirements, or skills"
      ></textarea>
      <button type="button" id="floatingIntelligenceSendBtn" aria-label="Send message">
        <svg
          class="floating-intelligence-chat-send-icon"
          viewBox="0 0 24 24"
          aria-hidden="true"
          focusable="false"
        >
          <path
            d="M5 12h13M12.5 6.2 18.8 12l-6.3 5.8"
            fill="none"
            stroke="currentColor"
            stroke-width="2.1"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
        <svg
          class="floating-intelligence-chat-stop-icon"
          viewBox="0 0 24 24"
          aria-hidden="true"
          focusable="false"
        >
          <rect x="7.5" y="7.5" width="9" height="9" rx="2" fill="currentColor" />
        </svg>
      </button>
    </div>

    <div
      class="floating-intelligence-chat-status"
      id="floatingIntelligenceStatus"
      role="status"
      aria-live="polite"
    >Idle</div>
  </section>

  <button
    type="button"
    class="floating-intelligence-chat-button"
    id="floatingIntelligenceChatButton"
    aria-label="Open Job Assistant"
    aria-haspopup="dialog"
    aria-expanded="false"
    aria-controls="floatingIntelligenceChatPanel"
    title="Open ApplyLens AI assistant"
  >
    <span class="floating-intelligence-chat-button-glow" aria-hidden="true"></span>
    <svg
      class="floating-intelligence-chat-icon"
      viewBox="0 0 28 28"
      aria-hidden="true"
      focusable="false"
    >
      <circle cx="12.6" cy="12.6" r="7.1" fill="none" stroke="currentColor" stroke-width="2.1" />
      <path
        d="M17.9 17.9 23 23"
        fill="none"
        stroke="currentColor"
        stroke-width="2.4"
        stroke-linecap="round"
      />
      <path
        d="M12.6 8.2l1.02 2.46 2.46 1.02-2.46 1.02-1.02 2.46-1.02-2.46-2.46-1.02 2.46-1.02z"
        fill="currentColor"
      />
    </svg>
  </button>
</div>
<script src="/static/floating_intelligence_chat.js?v=floating_job_assistant_r7" defer></script>
""".strip()
