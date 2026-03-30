const APP_SHELL_COLLAPSED_KEY = "job_stack_app_shell_collapsed";

function qs(id) {
  return document.getElementById(id);
}

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

window.addEventListener("DOMContentLoaded", () => {
  const menuBtn = qs("appShellMenuBtn");

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

  function closeNotifications() {
    if (!notificationDropdown || !notificationButton) return;
    notificationDropdown.classList.add("hidden");
    notificationButton.setAttribute("aria-expanded", "false");
  }

  function openNotifications() {
    if (!notificationDropdown || !notificationButton) return;
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

  loadUnreadCount();
});