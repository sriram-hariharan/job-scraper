from html import escape

NAV_ITEMS = [
    ("Executive", "/", "E"),
    ("Planning", "/planning", "P"),
    ("Decisions", "/decisions-ui", "D"),
    ("Intelligence", "/intelligence", "I"),
    ("Applications", "/applications", "A"),
    ("Scheduler", "/scheduler", "S"),
]

USER_NAME = "Sriram"
USER_INITIAL = USER_NAME[:1].upper()


def render_top_shell(active_href: str) -> str:
    nav_links = []

    for label, href, short_label in NAV_ITEMS:
        active_class = "app-shell-nav-link active" if href == active_href else "app-shell-nav-link"
        nav_links.append(
            f"""
            <a
              class="{active_class}"
              href="{escape(href)}"
              data-nav-label="{escape(label)}"
              aria-label="{escape(label)}"
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
    <a class="app-shell-brand" href="/" aria-label="Job Stack home">
      <span class="app-shell-brand-text">Job Stack</span>
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
    <span class="theme-toggle-label">Dark</span>
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
      title="{escape(USER_NAME)}"
    >
      {escape(USER_INITIAL)}
    </button>

    <div class="profile-dropdown hidden" id="profileDropdown">
      <div class="profile-dropdown-name">{escape(USER_NAME)}</div>
      <div class="profile-dropdown-actions">
        <a class="profile-dropdown-nav-btn" href="/profile/saved-scans">
          <span class="profile-dropdown-nav-copy">
            <span class="profile-dropdown-nav-title">Saved Scans</span>
            <span class="profile-dropdown-nav-subtitle">Resume scan history and match snapshots</span>
          </span>
          <span class="profile-dropdown-nav-arrow" aria-hidden="true">›</span>
        </a>

        <a class="profile-dropdown-nav-btn" href="/profile">
          <span class="profile-dropdown-nav-copy">
            <span class="profile-dropdown-nav-title">My Profile</span>
            <span class="profile-dropdown-nav-subtitle">Resumes, preferences, account tools</span>
          </span>
          <span class="profile-dropdown-nav-arrow" aria-hidden="true">›</span>
        </a>

        <button type="button" class="profile-dropdown-danger-btn" disabled>
          Log out
        </button>
      </div>
    </div>
  </div>
</div>
""".strip()
