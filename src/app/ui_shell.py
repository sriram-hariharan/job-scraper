from html import escape

PRIMARY_NAV_ITEMS = [
    ("Executive", "/"),
    ("Planning", "/planning"),
    ("Decisions", "/decisions-ui"),
    ("Intelligence", "/intelligence"),
]

APPLICATIONS_NAV_ITEM = ("Applications", "/applications")

USER_NAME = "Sriram"
USER_INITIAL = USER_NAME[:1].upper()


def render_top_shell(active_href: str) -> str:
    primary_links = []
    for label, href in PRIMARY_NAV_ITEMS:
        active_class = "top-nav-link active" if href == active_href else "top-nav-link"
        primary_links.append(
            f'<a class="{active_class}" href="{escape(href)}">{escape(label)}</a>'
        )

    applications_label, applications_href = APPLICATIONS_NAV_ITEM
    applications_class = (
        "state-nav-link active"
        if applications_href == active_href
        else "state-nav-link"
    )

    return f"""
<section class="top-shell">
  <div class="top-shell-left">
    <div class="top-nav-links">
      {''.join(primary_links)}
    </div>
  </div>

  <div class="top-shell-right">
    <div class="state-nav-links">
      <a class="{applications_class}" href="{escape(applications_href)}">{escape(applications_label)}</a>
    </div>

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
          <a class="profile-dropdown-link ghost-link-btn" href="/profile">My Profile</a>
          <button type="button" class="profile-dropdown-item ghost-btn" disabled>Log out</button>
        </div>
      </div>
    </div>
  </div>
</section>
""".strip()