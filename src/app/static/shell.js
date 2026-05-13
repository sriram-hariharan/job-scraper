const APP_SHELL_COLLAPSED_KEY = "job_stack_app_shell_collapsed";
const JOBSTACK_THEME_KEY = "jobstack.theme";
const APPLYLENS_FIRST_RUN_PROMPT_KEY = "applylens_first_run_prompt";
const APPLYLENS_NEW_USER_EMPTY_KEY = "applylens_new_user_empty_state";
const APPLYLENS_OPEN_PIPELINE_KEY = "applylens_open_live_pipeline";

function qs(id) {
  return document.getElementById(id);
}

function normalizeJobstackTheme(value) {
  return value === "light" ? "light" : "dark";
}

function getStoredJobstackTheme() {
  try {
    return normalizeJobstackTheme(window.localStorage.getItem(JOBSTACK_THEME_KEY));
  } catch (_) {
    return "dark";
  }
}

function updateThemeToggle(theme) {
  const themeToggleBtn = qs("themeToggleBtn");
  if (!themeToggleBtn) return;

  const isLight = theme === "light";
  const nextLabel = isLight ? "Switch to dark theme" : "Switch to light theme";
  themeToggleBtn.dataset.theme = theme;
  themeToggleBtn.setAttribute("aria-label", nextLabel);
  themeToggleBtn.setAttribute("aria-pressed", isLight ? "true" : "false");
  themeToggleBtn.title = nextLabel;

  const icon = themeToggleBtn.querySelector(".theme-toggle-icon");
  if (icon) {
    icon.src = isLight ? "/static/media/dark_mode.svg" : "/static/media/light_mode.svg";
  }
}

function applyJobstackTheme(theme, { persist = true } = {}) {
  const safeTheme = normalizeJobstackTheme(theme);
  document.documentElement.dataset.theme = safeTheme;
  document.documentElement.dataset.bsTheme = safeTheme;
  document.documentElement.style.colorScheme = safeTheme;

  if (persist) {
    try {
      window.localStorage.setItem(JOBSTACK_THEME_KEY, safeTheme);
    } catch (_) {
      // Local storage can be unavailable in privacy modes; theme still applies for this page.
    }
  }

  updateThemeToggle(safeTheme);
}

applyJobstackTheme(getStoredJobstackTheme(), { persist: false });

function setShellCollapsed(isCollapsed, { persist = true } = {}) {
  document.body.classList.toggle("app-shell-collapsed", isCollapsed);

  const menuBtn = qs("appShellMenuBtn");
  if (menuBtn) {
    menuBtn.setAttribute("aria-pressed", isCollapsed ? "true" : "false");
  }

  if (persist) {
    window.localStorage.setItem(APP_SHELL_COLLAPSED_KEY, isCollapsed ? "true" : "false");
  }
}

function normalizeNotificationTitle(row) {
  const raw = String(row?.title || row?.subject || "").trim();
  if (!raw) return "Scheduler update";

  const finalJobsMatch = raw.match(/^Scheduled job\s+([A-Z_]+)\s+\|\s+([^|]+?)\s+\|\s+final_jobs=(\d+)$/i);
  if (finalJobsMatch) {
    const jobName = finalJobsMatch[2].trim().replace(/_/g, " ");
    const count = finalJobsMatch[3];
    return `${jobName} · jobs=${count}`;
  }

  const genericMatch = raw.match(/^Scheduled job\s+([A-Z_]+)\s+\|\s+(.+)$/i);
  if (genericMatch) {
    const rest = genericMatch[2].trim().replace(/_/g, " ");
    return rest;
  }

  return raw.replace(/_/g, " ");
}

function normalizeNotificationMessage(row) {
  const deliveryStatus = String(row?.delivery_status || "").trim().toLowerCase();
  const jobName = String(row?.job_name || "").trim().replace(/_/g, " ");

  if (deliveryStatus === "sent_smtp") {
    return `Email summary sent for ${jobName}.`;
  }

  if (deliveryStatus === "recorded_outbox_only") {
    return `Email summary prepared for ${jobName}, but not sent.`;
  }

  if (deliveryStatus === "dry_run_only") {
    return `Email summary rendered in dry-run mode for ${jobName}.`;
  }

  if (deliveryStatus === "failed_smtp") {
    return `Email delivery failed for ${jobName}.`;
  }

  return String(row?.message || "").trim();
}

function notificationDestination(row) {
  const kind = String(row?.notification_kind || "").trim().toLowerCase();

  if (kind === "scheduled_run_email_delivery") {
    return "/scheduler";
  }

  return "";
}

function formatNotificationTime(value) {
  const raw = String(value || "").trim();
  if (!raw) return "";

  const date = new Date(raw);
  if (Number.isNaN(date.getTime())) {
    return raw;
  }

  try {
    return date.toLocaleString([], {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  } catch (_) {
    return raw;
  }
}

function notificationBadgeMeta(row) {
  const runStatus = String(row?.run_status || "").trim().toLowerCase();

  if (runStatus === "success" || runStatus === "succeeded") {
    return {
      label: "SUCCESS",
      className: "notification-item-badge notification-item-badge--success",
    };
  }

  if (runStatus === "failed" || runStatus === "error") {
    return {
      label: "FAILED",
      className: "notification-item-badge notification-item-badge--error",
    };
  }

  const level = String(row?.level || "").trim().toLowerCase();
  if (level === "success") {
    return {
      label: "SUCCESS",
      className: "notification-item-badge notification-item-badge--success",
    };
  }
  if (level === "error") {
    return {
      label: "FAILED",
      className: "notification-item-badge notification-item-badge--error",
    };
  }

  return {
    label: "INFO",
    className: "notification-item-badge notification-item-badge--info",
  };
}

function setNotificationLoading(listEl, message) {
  if (!listEl) return;
  listEl.innerHTML = `<div class="notification-empty">${message}</div>`;
}

function renderNotificationRows(listEl, rows, unreadOnly) {
  if (!listEl) return;

  if (!Array.isArray(rows) || rows.length === 0) {
    listEl.innerHTML = `
      <div class="notification-empty">
        ${unreadOnly ? "No unread notifications." : "No notifications yet."}
      </div>
    `;
    return;
  }

  listEl.innerHTML = rows.map((row) => {
    const notificationId = String(row.notification_id || "");
    const title = normalizeNotificationTitle(row);
    const message = normalizeNotificationMessage(row);
    const createdAt = formatNotificationTime(row.created_at || "");
    const isRead = Boolean(row.is_read);
    const badgeMeta = notificationBadgeMeta(row);
    const toggleLabel = isRead ? "Mark unread" : "Mark read";
    const destination = notificationDestination(row);
    

    return `
      <article
        class="notification-item ${isRead ? "is-read" : "is-unread"} ${destination ? "is-clickable" : ""}"
        data-notification-id="${notificationId}"
        data-notification-destination="${destination}"
      >
        <div class="notification-item-topline">
          <span class="${badgeMeta.className}">${badgeMeta.label}</span>
          <span class="notification-item-time">${createdAt}</span>
        </div>

        <div class="notification-item-title">${title}</div>
        <div class="notification-item-message">${message}</div>

        <div class="notification-item-actions">
          <button
            type="button"
            class="ghost-btn notification-toggle-btn"
            data-notification-toggle="${notificationId}"
            data-next-read="${isRead ? "false" : "true"}"
          >
            ${toggleLabel}
          </button>
        </div>
      </article>
    `;
  }).join("");
}

async function fetchJson(url, options = {}) {
  const response = await window.fetch(url, options);
  const payload = await response.json().catch(() => ({}));

  if (!response.ok) {
    const detail = payload && typeof payload.detail === "string"
      ? payload.detail
      : `Request failed: ${response.status}`;
    throw new Error(detail);
  }

  return payload;
}

function resolveTableWrap(target) {
  if (!target) return null;
  if (target.classList?.contains("table-wrap")) return target;
  return target.closest?.(".table-wrap") || null;
}

function ensureTableWrapLoadingOverlay(tableWrap) {
  let overlay = tableWrap.querySelector(".table-wrap-loading-overlay");
  if (overlay) return overlay;

  overlay = document.createElement("div");
  overlay.className = "table-wrap-loading-overlay hidden";
  overlay.innerHTML = `
    <div class="loading-state">
      <div class="loading-spinner"></div>
      <div class="loading-text">Loading...</div>
    </div>
  `;

  tableWrap.appendChild(overlay);
  return overlay;
}

function setTableWrapLoading(target, label = "Loading...") {
  const tableWrap = resolveTableWrap(target);
  if (!tableWrap) return;

  tableWrap.scrollLeft = 0;
  tableWrap.scrollTop = 0;

  const overlay = ensureTableWrapLoadingOverlay(tableWrap);
  const textEl = overlay.querySelector(".loading-text");
  if (textEl) {
    textEl.textContent = label;
  }

  tableWrap.classList.add("table-wrap--loading");
  overlay.classList.remove("hidden");
}

function clearTableWrapLoading(target) {
  const tableWrap = resolveTableWrap(target);
  if (!tableWrap) return;

  tableWrap.classList.remove("table-wrap--loading");

  const overlay = tableWrap.querySelector(".table-wrap-loading-overlay");
  if (overlay) {
    overlay.classList.add("hidden");
  }
}

window.setTableWrapLoading = setTableWrapLoading;
window.clearTableWrapLoading = clearTableWrapLoading;

window.addEventListener("DOMContentLoaded", () => {
  const menuBtn = qs("appShellMenuBtn");
  const themeToggleBtn = qs("themeToggleBtn");

  applyJobstackTheme(getStoredJobstackTheme(), { persist: false });

  const saved = window.localStorage.getItem(APP_SHELL_COLLAPSED_KEY);
  const defaultCollapsed = saved === null ? window.innerWidth < 1220 : saved === "true";
  setShellCollapsed(defaultCollapsed, { persist: false });

  if (menuBtn) {
    menuBtn.addEventListener("click", (event) => {
      event.preventDefault();
      const next = !document.body.classList.contains("app-shell-collapsed");
      setShellCollapsed(next);
    });
  }

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener("click", (event) => {
      event.preventDefault();
      const currentTheme = normalizeJobstackTheme(document.documentElement.dataset.theme);
      applyJobstackTheme(currentTheme === "light" ? "dark" : "light");
    });
  }

  const notificationShell = qs("notificationShell");
  const notificationButton = qs("notificationButton");
  const notificationDropdown = qs("notificationDropdown");
  const notificationBadge = qs("notificationBadge");
  const notificationList = qs("notificationList");
  const notificationShowAll = qs("notificationShowAll");
  const notificationUnreadOnly = qs("notificationUnreadOnly");
  const notificationRefreshBtn = qs("notificationRefreshBtn");
  const notificationMarkAllReadBtn = qs("notificationMarkAllReadBtn");

  const menuShell = qs("profileMenuShell");
  const menuButton = qs("profileMenuButton");
  const dropdown = qs("profileDropdown");
  const profileDropdownAvatar = qs("profileDropdownAvatar");
  const profileDropdownName = qs("profileDropdownName");
  const profileDropdownEmail = qs("profileDropdownEmail");
  const profileLogoutBtn = qs("profileLogoutBtn");

  function storageGet(storage, key) {
    try {
      return storage.getItem(key);
    } catch (_) {
      return null;
    }
  }

  function storageSet(storage, key, value) {
    try {
      storage.setItem(key, value);
    } catch (_) {
      // Storage may be unavailable; the current click still proceeds.
    }
  }

  function storageRemove(storage, key) {
    try {
      storage.removeItem(key);
    } catch (_) {
      // Storage may be unavailable; ignore.
    }
  }

  function openLivePipelineFromShell() {
    storageRemove(window.localStorage, APPLYLENS_NEW_USER_EMPTY_KEY);
    document.body.classList.remove("app-new-user-empty");

    if (window.location.pathname !== "/") {
      storageSet(window.sessionStorage, APPLYLENS_OPEN_PIPELINE_KEY, "1");
      window.location.href = "/";
      return;
    }

    if (typeof window.openApplyLensPipelineConfig === "function") {
      window.openApplyLensPipelineConfig();
      return;
    }

    const runPipelineBtn = qs("runPipelineBtn");
    if (runPipelineBtn) {
      runPipelineBtn.click();
      return;
    }

    storageSet(window.sessionStorage, APPLYLENS_OPEN_PIPELINE_KEY, "1");
  }

  function ensureNewUserEmptyState() {
    if (storageGet(window.localStorage, APPLYLENS_NEW_USER_EMPTY_KEY) !== "1") return;
    if (document.body.classList.contains("auth-page")) return;

    const page = document.querySelector(".page");
    if (!page || page.querySelector(".new-user-empty-state")) return;

    document.body.classList.add("app-new-user-empty");

    const emptyState = document.createElement("section");
    emptyState.className = "new-user-empty-state";
    emptyState.setAttribute("aria-live", "polite");
    emptyState.innerHTML = `
      <div class="new-user-empty-card">
        <div class="new-user-empty-kicker">Welcome to ApplyLens AI</div>
        <h2>Start by running the live scraper.</h2>
        <p>New users need a first job scrape before dashboards, scans, applications, and saved drafts can show useful data.</p>
        <div class="new-user-empty-actions">
          <button type="button" class="new-user-empty-primary" id="newUserRunPipelineBtn">Run live scraper</button>
        </div>
      </div>
    `;
    page.appendChild(emptyState);

    const runBtn = qs("newUserRunPipelineBtn");
    if (runBtn) {
      runBtn.addEventListener("click", openLivePipelineFromShell);
    }
  }

  async function refreshNewUserWorkspaceState() {
    if (document.body.classList.contains("auth-page")) return;

    try {
      const response = await fetch("/user/workspace-state", {
        headers: { Accept: "application/json" },
        credentials: "same-origin",
      });
      if (!response.ok) return;

      const payload = await response.json();
      if (payload && payload.has_owned_data === false) {
        storageSet(window.localStorage, APPLYLENS_NEW_USER_EMPTY_KEY, "1");
        ensureNewUserEmptyState();
        return;
      }

      clearNewUserOnboardingState();
    } catch (_) {
      ensureNewUserEmptyState();
    }
  }

  function closeFirstRunPrompt(modal) {
    storageRemove(window.sessionStorage, APPLYLENS_FIRST_RUN_PROMPT_KEY);
    modal.classList.add("hidden");
    modal.setAttribute("aria-hidden", "true");
  }

  function showFirstRunPrompt() {
    if (storageGet(window.sessionStorage, APPLYLENS_FIRST_RUN_PROMPT_KEY) !== "1") return;

    let modal = qs("firstRunPromptModal");
    if (!modal) {
      modal = document.createElement("section");
      modal.id = "firstRunPromptModal";
      modal.className = "first-run-prompt-modal hidden";
      modal.setAttribute("role", "dialog");
      modal.setAttribute("aria-modal", "true");
      modal.setAttribute("aria-labelledby", "firstRunPromptTitle");
      modal.innerHTML = `
        <div class="first-run-prompt-backdrop"></div>
        <div class="first-run-prompt-card">
          <div class="first-run-prompt-mark" aria-hidden="true">
            <img src="/static/media/app-logo.svg" alt="" />
          </div>
          <div class="first-run-prompt-copy">
            <div class="first-run-prompt-kicker">First setup</div>
            <h2 id="firstRunPromptTitle">Run live scraper to start?</h2>
            <p>This will open the live pipeline setup so ApplyLens AI can build your first job queue and scan data.</p>
          </div>
          <div class="first-run-prompt-actions">
            <button type="button" class="first-run-prompt-secondary" id="firstRunPromptNoBtn">No, go home</button>
            <button type="button" class="first-run-prompt-primary" id="firstRunPromptYesBtn">Yes, open scraper</button>
          </div>
        </div>
      `;
      document.body.appendChild(modal);

      qs("firstRunPromptNoBtn")?.addEventListener("click", () => {
        closeFirstRunPrompt(modal);
        storageSet(window.localStorage, APPLYLENS_NEW_USER_EMPTY_KEY, "1");
        ensureNewUserEmptyState();
        if (window.location.pathname !== "/") {
          window.location.href = "/";
        }
      });

      qs("firstRunPromptYesBtn")?.addEventListener("click", () => {
        closeFirstRunPrompt(modal);
        openLivePipelineFromShell();
      });
    }

    modal.classList.remove("hidden");
    modal.setAttribute("aria-hidden", "false");
  }

  function closeProfileMenu() {
    if (!dropdown || !menuButton) return;
    dropdown.classList.add("hidden");
    menuButton.setAttribute("aria-expanded", "false");
  }

  function openProfileMenu() {
    if (!dropdown || !menuButton) return;
    dropdown.classList.remove("hidden");
    menuButton.setAttribute("aria-expanded", "true");
  }

    function userInitialFromName(name, email) {
    const source = String(name || email || "A").trim();
    return source ? source.charAt(0).toUpperCase() : "A";
  }

  function setProfileShellUser(user) {
    const displayName = String(user?.display_name || user?.email || "Account").trim();
    const email = String(user?.email || "").trim();
    const initial = userInitialFromName(displayName, email);

    if (menuButton) {
      menuButton.textContent = initial;
      menuButton.title = displayName;
      menuButton.setAttribute("aria-label", displayName);
    }

    if (profileDropdownAvatar) {
      profileDropdownAvatar.textContent = initial;
    }

    if (profileDropdownName) {
      profileDropdownName.textContent = displayName;
    }

    if (profileDropdownEmail) {
      profileDropdownEmail.textContent = email;
      profileDropdownEmail.classList.toggle("hidden", !email);
    }
  }

  async function loadProfileShellUser() {
    try {
      const payload = await fetchJson("/auth/me");
      if (payload?.ok && payload?.user) {
        setProfileShellUser(payload.user);
      }
    } catch (_) {
      setProfileShellUser({
        display_name: "Account",
        email: "",
      });
    }
  }

  async function logoutProfileShellUser() {
    if (!profileLogoutBtn) return;

    profileLogoutBtn.setAttribute("disabled", "disabled");

    try {
      const payload = await fetchJson("/auth/logout", {
        method: "POST",
      });

      window.location.href = payload.redirect_to || "/login";
    } catch (error) {
      window.alert(
        `Could not log out. ${error instanceof Error ? error.message : ""}`.trim()
      );
      profileLogoutBtn.removeAttribute("disabled");
    }
  }

  function closeNotifications() {
    if (!notificationDropdown || !notificationButton) return;
    notificationDropdown.classList.add("hidden");
    notificationButton.setAttribute("aria-expanded", "false");
  }

  function positionNotificationDropdown() {
    if (!notificationDropdown || !notificationButton) return;

    const buttonRect = notificationButton.getBoundingClientRect();
    const viewportWidth = window.innerWidth || document.documentElement.clientWidth || 0;
    const viewportHeight = window.innerHeight || document.documentElement.clientHeight || 0;
    const gutter = 14;
    const dropdownWidth = Math.min(440, Math.max(280, viewportWidth - gutter * 2));
    const centeredLeft = buttonRect.left + buttonRect.width / 2 - dropdownWidth / 2;
    const left = Math.min(Math.max(gutter, centeredLeft), viewportWidth - dropdownWidth - gutter);
    const top = Math.min(
      buttonRect.bottom + 12,
      Math.max(gutter, viewportHeight - 160)
    );
    const maxHeight = Math.max(220, viewportHeight - top - gutter);

    notificationDropdown.style.setProperty("width", `${dropdownWidth}px`, "important");
    notificationDropdown.style.setProperty("left", `${left}px`, "important");
    notificationDropdown.style.setProperty("top", `${top}px`, "important");
    notificationDropdown.style.setProperty("right", "auto", "important");
    notificationDropdown.style.setProperty("max-height", `${maxHeight}px`, "important");
  }

  function openNotifications() {
    if (!notificationDropdown || !notificationButton) return;
    positionNotificationDropdown();
    notificationDropdown.classList.remove("hidden");
    notificationButton.setAttribute("aria-expanded", "true");
  }

  async function loadUnreadCount() {
    if (!notificationBadge) return;

    try {
      const payload = await fetchJson("/notifications/unread-count");
      const unreadCount = Number(payload.unread_count || 0);

      if (unreadCount > 0) {
        notificationBadge.textContent = unreadCount > 99 ? "99+" : String(unreadCount);
        notificationBadge.classList.remove("hidden");
      } else {
        notificationBadge.textContent = "0";
        notificationBadge.classList.add("hidden");
      }
    } catch (_) {
      notificationBadge.textContent = "!";
      notificationBadge.classList.remove("hidden");
    }
  }

  async function loadNotifications() {
    if (!notificationList) return;

    const unreadOnly = Boolean(notificationUnreadOnly && notificationUnreadOnly.checked);
    const params = new URLSearchParams();
    params.set("limit", "12");
    if (unreadOnly) {
      params.set("is_read", "false");
    }

    setNotificationLoading(notificationList, "Loading notifications...");

    try {
      const payload = await fetchJson(`/notifications?${params.toString()}`);
      renderNotificationRows(notificationList, payload.rows || [], unreadOnly);
    } catch (error) {
      setNotificationLoading(
        notificationList,
        `Could not load notifications. ${error instanceof Error ? error.message : ""}`.trim()
      );
    }
  }

  async function updateNotificationReadState(notificationId, isRead) {
    await fetchJson("/notifications/read-state", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        notification_id: notificationId,
        is_read: isRead,
      }),
    });
  }

  async function markAllNotificationsRead() {
  const payload = await fetchJson("/notifications?is_read=false&limit=100");
  const unreadRows = Array.isArray(payload.rows) ? payload.rows : [];

  for (const row of unreadRows) {
    const notificationId = String(row.notification_id || "").trim();
    if (!notificationId) continue;

    await updateNotificationReadState(notificationId, true);
  }

  return unreadRows.length;
}

  if (notificationButton && notificationDropdown) {
    notificationButton.addEventListener("click", async (event) => {
      event.stopPropagation();
      const isHidden = notificationDropdown.classList.contains("hidden");

      closeProfileMenu();

      if (isHidden) {
        openNotifications();
        await loadNotifications();
        await loadUnreadCount();
      } else {
        closeNotifications();
      }
    });
  }

  if (notificationRefreshBtn) { 
    notificationRefreshBtn.addEventListener("click", async (event) => {
      event.preventDefault();
      await loadNotifications();
      await loadUnreadCount();
    });
  }

  if (notificationMarkAllReadBtn) {
  notificationMarkAllReadBtn.addEventListener("click", async (event) => {
    event.preventDefault();

    notificationMarkAllReadBtn.setAttribute("disabled", "disabled");

    try {
      await markAllNotificationsRead();
      await loadNotifications();
      await loadUnreadCount();
    } catch (error) {
      window.alert(
        `Could not mark all notifications read. ${error instanceof Error ? error.message : ""}`.trim()
      );
    } finally {
      notificationMarkAllReadBtn.removeAttribute("disabled");
    }
  });
}

  [notificationShowAll, notificationUnreadOnly]
  .filter(Boolean)
  .forEach((input) => {
    input.addEventListener("change", async () => {
      await loadNotifications();
    });
  });

  if (notificationList) {
    notificationList.addEventListener("click", async (event) => {
      const target = event.target;
      if (!(target instanceof HTMLElement)) return;

      const clickableCard = target.closest(".notification-item[data-notification-destination]");
      if (clickableCard && !target.closest("[data-notification-toggle]")) {
        const destination = String(clickableCard.getAttribute("data-notification-destination") || "").trim();
        if (destination) {
          window.location.href = destination;
          return;
        }
      }

      const toggleBtn = target.closest("[data-notification-toggle]");
      if (!toggleBtn) return;

      event.preventDefault();
      event.stopPropagation();

      const notificationId = String(toggleBtn.getAttribute("data-notification-toggle") || "").trim();
      const nextRead = String(toggleBtn.getAttribute("data-next-read") || "").trim() === "true";

      if (!notificationId) return;

      toggleBtn.setAttribute("disabled", "disabled");

      try {
        await updateNotificationReadState(notificationId, nextRead);
        await loadNotifications();
        await loadUnreadCount();
      } catch (error) {
        window.alert(
          `Could not update notification state. ${error instanceof Error ? error.message : ""}`.trim()
        );
      } finally {
        toggleBtn.removeAttribute("disabled");
      }
    });
  }

  if (menuShell && menuButton && dropdown) {
    menuButton.addEventListener("click", (event) => {
      event.stopPropagation();
      const isHidden = dropdown.classList.contains("hidden");

      closeNotifications();

      if (isHidden) {
        openProfileMenu();
      } else {
        closeProfileMenu();
      }
    });
  }

    if (profileLogoutBtn) {
    profileLogoutBtn.addEventListener("click", async (event) => {
      event.preventDefault();
      event.stopPropagation();
      await logoutProfileShellUser();
    });
  }

  document.addEventListener("click", (event) => {
    const target = event.target;

    if (menuShell && target instanceof Node && !menuShell.contains(target)) {
      closeProfileMenu();
    }

    if (notificationShell && target instanceof Node && !notificationShell.contains(target)) {
      closeNotifications();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeProfileMenu();
      closeNotifications();
    }
  });

  window.addEventListener("resize", () => {
    if (notificationDropdown && !notificationDropdown.classList.contains("hidden")) {
      positionNotificationDropdown();
    }
  });

  loadProfileShellUser();
  loadUnreadCount();
  refreshNewUserWorkspaceState();
  showFirstRunPrompt();
});
