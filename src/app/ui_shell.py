from html import escape

NAV_ITEMS = [
    ("Executive", "/", "E"),
    ("Planning", "/planning", "P"),
    ("Decisions", "/decisions-ui", "D"),
    ("Applications", "/applications", "A"),
    ("Scheduler", "/scheduler", "S"),
]

DEFAULT_USER_NAME = "Account"
DEFAULT_USER_INITIAL = "A"


def render_top_shell(active_href: str) -> str:
    nav_links = []

    for label, href, short_label in NAV_ITEMS:
        active_class = "app-shell-nav-link active" if href == active_href else "app-shell-nav-link"
        active_current = ' aria-current="page"' if href == active_href else ""
        nav_links.append(
            f"""
            <a
              class="{active_class}"
              href="{escape(href)}"
              data-nav-label="{escape(label)}"
              aria-label="{escape(label)}"
              {active_current}
              title="{escape(label)}"
            >
              <span class="app-shell-nav-short" aria-hidden="true">{escape(short_label)}</span>
              <span class="app-shell-nav-label">{escape(label)}</span>
            </a>
            """.strip()
        )

    return f"""
<button
  type="button"
  class="app-shell-menu-btn"
  id="appShellMenuBtn"
  aria-label="Toggle sidebar"
  title="Toggle sidebar"
  aria-pressed="false"
>
  <span class="app-shell-menu-btn-line" aria-hidden="true"></span>
  <span class="app-shell-menu-btn-line" aria-hidden="true"></span>
  <span class="app-shell-menu-btn-line" aria-hidden="true"></span>
</button>

<aside class="app-shell" id="appShell">
  <div class="app-shell-brand-row">
    <a class="app-shell-brand" href="/" aria-label="ApplyLens AI home">
      <img class="app-shell-brand-logo" src="/static/media/app-logo.svg" alt="ApplyLens AI" />
    </a>
  </div>

  <nav class="app-shell-nav" aria-label="Dashboard navigation">
    {''.join(nav_links)}
  </nav>
</aside>

<div class="app-shell-top-right">
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

    <div class="notification-dropdown hidden" id="notificationDropdown">
      <div class="notification-dropdown-header">
        <div>
          <div class="notification-dropdown-title">Notifications</div>
          <div class="subtext" id="notificationSubtitle">Recent scheduler activity</div>
        </div>

        <div class="notification-header-actions">
          <button
            type="button"
            class="ghost-btn notification-refresh-btn"
            id="notificationRefreshBtn"
          >
            Refresh
          </button>

          <button
            type="button"
            class="ghost-btn notification-mark-all-btn"
            id="notificationMarkAllReadBtn"
          >
            Mark all read
          </button>
        </div>
      </div>

      <div class="notification-toolbar">
        <div
          class="binary-toggle binary-toggle--compact notification-unread-toggle"
          id="notificationUnreadToggle"
          role="radiogroup"
          aria-label="Notification filter"
        >
          <label class="binary-toggle-option">
            <input
              type="radio"
              name="notificationUnreadFilter"
              id="notificationShowAll"
              value="all"
              checked
            />
            <span>All</span>
          </label>

          <label class="binary-toggle-option">
            <input
              type="radio"
              name="notificationUnreadFilter"
              id="notificationUnreadOnly"
              value="unread"
            />
            <span>Unread</span>
          </label>
        </div>
      </div>

      <div class="notification-list" id="notificationList">
        <div class="notification-empty">Loading notifications...</div>
      </div>
    </div>
  </div>

  <button
    type="button"
    class="theme-toggle-btn"
    id="themeToggleBtn"
    aria-label="Switch to light theme"
    aria-pressed="false"
    title="Switch to light theme"
  >
    <span class="theme-toggle-track" aria-hidden="true">
      <span class="theme-toggle-knob"></span>
    </span>
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
      title="{escape(DEFAULT_USER_NAME)}"
    >
      {escape(DEFAULT_USER_INITIAL)}
    </button>

    <div class="profile-dropdown hidden" id="profileDropdown">
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
        <a class="profile-dropdown-nav-btn" href="/profile/saved-scans">
          <span class="profile-dropdown-nav-icon profile-dropdown-nav-icon--scans" aria-hidden="true">
            <img src="/static/media/scan_icon.svg" alt="" />
          </span>
          <span class="profile-dropdown-nav-copy">
            <span class="profile-dropdown-nav-title">Saved Scans</span>
            <span class="profile-dropdown-nav-subtitle">Resume scan history and match snapshots</span>
          </span>
          <span class="profile-dropdown-nav-arrow" aria-hidden="true">›</span>
        </a>

        <a class="profile-dropdown-nav-btn" href="/profile">
          <span class="profile-dropdown-nav-icon profile-dropdown-nav-icon--profile" aria-hidden="true">
            <img src="/static/media/profile_icon.svg" alt="" />
          </span>
          <span class="profile-dropdown-nav-copy">
            <span class="profile-dropdown-nav-title">My Profile</span>
            <span class="profile-dropdown-nav-subtitle">Resumes and account tools</span>
          </span>
          <span class="profile-dropdown-nav-arrow" aria-hidden="true">›</span>
        </a>

        <a class="profile-dropdown-nav-btn" href="/profile/preferences">
          <span class="profile-dropdown-nav-icon profile-dropdown-nav-icon--preferences" aria-hidden="true">
            <img src="/static/media/preferences_icon.svg" alt="" />
          </span>
          <span class="profile-dropdown-nav-copy">
            <span class="profile-dropdown-nav-title">Preferences</span>
            <span class="profile-dropdown-nav-subtitle">Role focus, location, and matching signals</span>
          </span>
          <span class="profile-dropdown-nav-arrow" aria-hidden="true">›</span>
        </a>

        <button type="button" class="profile-dropdown-danger-btn" id="profileLogoutBtn">
          Log out
        </button>
      </div>
    </div>
  </div>
</div>

<div class="floating-intelligence-chat" id="floatingIntelligenceChat">
  <section
    class="floating-intelligence-chat-panel hidden"
    id="floatingIntelligenceChatPanel"
    aria-label="Job Assistant"
  >
    <header class="floating-intelligence-chat-header">
      <div class="floating-intelligence-chat-heading">
        <h2>Job Assistant</h2>
        <p>Ask a question or search by keywords.</p>
      </div>
      <button
        type="button"
        class="floating-intelligence-chat-close-btn"
        id="floatingIntelligenceChatCloseBtn"
        aria-label="Close Job Assistant"
      >
        ×
      </button>
    </header>

    <div class="floating-intelligence-chat-controls">
      <p class="floating-intelligence-chat-helper">The assistant will decide whether to search or answer.</p>
      <select id="floatingIntelligenceModeSelect" hidden aria-hidden="true" tabindex="-1">
        <option value="answer" selected>Answer</option>
        <option value="search">Search</option>
      </select>
    </div>

    <div class="floating-intelligence-chat-messages" id="floatingIntelligenceMessages">
      <p>Open the assistant to search jobs or ask grounded questions.</p>
    </div>

    <div class="floating-intelligence-chat-compose">
      <input
        type="text"
        id="floatingIntelligenceInput"
        placeholder="Ask about jobs, companies, skills, or applications..."
      />
      <button type="button" id="floatingIntelligenceSendBtn">Send</button>
    </div>

    <div class="floating-intelligence-chat-status" id="floatingIntelligenceStatus">Idle</div>
  </section>

  <button
    type="button"
    class="floating-intelligence-chat-button"
    id="floatingIntelligenceChatButton"
    aria-label="Open Job Assistant"
  >
    <svg
      class="floating-intelligence-chat-icon"
      viewBox="0 0 24 24"
      aria-hidden="true"
      focusable="false"
    >
      <path
        d="M5.5 6.5h13v8.2h-5.3L9.8 18v-3.3H5.5z"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linejoin="round"
      />
      <path
        d="M8.3 10.3h7.4M8.3 12.8h4.8"
        fill="none"
        stroke="currentColor"
        stroke-width="1.8"
        stroke-linecap="round"
      />
    </svg>
  </button>
</div>
<script src="/static/floating_intelligence_chat.js?v=floating_job_assistant_r1" defer></script>
""".strip()
