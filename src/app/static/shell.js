const APP_SHELL_COLLAPSED_KEY = "job_stack_app_shell_collapsed";
const JOBSTACK_THEME_KEY = "jobstack.theme";
const APPLYLENS_FIRST_RUN_PROMPT_KEY = "applylens_first_run_prompt";
const APPLYLENS_NEW_USER_EMPTY_KEY = "applylens_new_user_empty_state";
const APPLYLENS_OPEN_PIPELINE_KEY = "applylens_open_live_pipeline";
const APPLYLENS_DEFAULT_IDLE_TIMEOUT_SECONDS = 1800;
const APPLYLENS_DEFAULT_IDLE_WARNING_SECONDS = 60;
const BULK_GENERATION_STATE_EVENT = "applylens:bulk-generation-state";
const BULK_GENERATION_BLOCK_MESSAGE = "Bulk Generate must finish or be stopped before this action is available.";
const BULK_GENERATION_CHECKING_MESSAGE = "Checking Bulk Generate status…";
const BULK_GENERATION_FAILED_MESSAGE = "Bulk Generate status could not be verified. Retry before starting this action.";
const BULK_GENERATION_ACTIVE_STATUSES = new Set(["queued", "running", "stop_requested"]);
const BULK_GENERATION_TERMINAL_STATUSES = new Set(["completed", "stopped", "failed"]);
let bulkGenerationPollTimer = null;
let bulkGenerationCanonicalState = {
  verified: false,
  verification: "checking",
  active: false,
  status: "unknown",
  items: [],
};

// Desktop sidebar collapse-control icons (Lucide PanelLeftClose / Menu),
// mirroring the inline geometry rendered server-side in src/app/ui_shell.py so the
// icon family stays consistent without a runtime dependency.
const APP_SHELL_ICON_SVG_HEAD =
  '<svg class="app-shell-icon" viewBox="0 0 24 24" width="20" height="20" ' +
  'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" ' +
  'stroke-linejoin="round" aria-hidden="true" focusable="false">';
const APP_SHELL_COLLAPSE_SVG =
  APP_SHELL_ICON_SVG_HEAD +
  '<rect width="18" height="18" x="3" y="3" rx="2"/><path d="M9 3v18"/><path d="m16 15-3-3 3-3"/></svg>';
const APP_SHELL_MENU_SVG =
  APP_SHELL_ICON_SVG_HEAD +
  '<line x1="4" x2="20" y1="6" y2="6"/><line x1="4" x2="20" y1="12" y2="12"/><line x1="4" x2="20" y1="18" y2="18"/></svg>';

function qs(id) {
  return document.getElementById(id);
}

function bulkGenerationControlIsSafe(control) {
  if (!(control instanceof Element)) return true;
  if (control.closest("[data-bulk-safe='true']")) return true;
  if (control.matches(
    "#scanWorkspaceCompanyInput, #scanWorkspaceRoleInput, #scanWorkspaceJobUrlInput, " +
    "#scanWorkspaceResumeSelect, #scanWorkspaceResumeFileInput, #scanWorkspaceResumeTextInput, " +
    "#scanWorkspaceResumeBrowseBtn, #scanWorkspaceJobDescriptionInput"
  )) return true;
  if (control.matches(".app-shell-nav-link, .app-shell-brand, .profile-dropdown-nav-btn")) return true;
  const safeIds = new Set([
    "appShellMenuBtn", "appShellCollapseBtn", "appShellCloseBtn", "themeToggleBtn",
    "profileMenuButton", "profileLogoutBtn", "notificationButton", "notificationRefreshBtn",
  ]);
  if (safeIds.has(control.id)) return true;
  const id = String(control.id || "").toLowerCase();
  if (/(close|cancel|minimize|dismiss)/.test(id)) return true;
  const label = String(control.getAttribute("aria-label") || "").toLowerCase();
  if (/(expand|collapse|previous page|next page|sort|filter|pagination)/.test(label)) return true;
  if (control.closest(
    ".shared-filter-select, .shared-table-pagination, .planning-react-filter-grid, " +
    ".planning-react-filter-actions, .executive-queue-filter-card, .operational-filter-card, " +
    ".applications-tabs, .scheduler-runs-filters, .notification-center__filters, " +
    ".notification-center__foot"
  )) return true;
  if (control.matches("input[type='search']")) return true;
  if (control.matches("a[href]")) {
    const rawHref = control.getAttribute("href") || "";
    if (!rawHref.startsWith("/") || rawHref.startsWith("/#") || rawHref === window.location.pathname) return true;
    const safePaths = [
      "/", "/planning", "/decisions-ui", "/applications", "/pipeline", "/scheduler",
      "/agentic-operations", "/profile", "/profile/preferences", "/profile/ai-settings",
      "/profile/saved-scans", "/onboarding", "/logout",
    ];
    return safePaths.includes(rawHref.split("?", 1)[0]) || rawHref.startsWith("/profile/pipeline-runs/");
  }
  return false;
}

function bulkGenerationGuardMessage() {
  if (bulkGenerationCanonicalState.verified && bulkGenerationCanonicalState.active) {
    return BULK_GENERATION_BLOCK_MESSAGE;
  }
  if (bulkGenerationCanonicalState.verification === "failed") {
    return BULK_GENERATION_FAILED_MESSAGE;
  }
  return BULK_GENERATION_CHECKING_MESSAGE;
}

function showBulkGenerationGuardTooltip(control) {
  const tooltip = qs("bulkGenerationGuardTooltip");
  if (!tooltip || !(control instanceof Element)) return;
  const rect = control.getBoundingClientRect();
  tooltip.textContent = bulkGenerationGuardMessage();
  tooltip.style.left = `${Math.max(12, Math.min(window.innerWidth - 332, rect.left))}px`;
  tooltip.style.top = `${Math.min(window.innerHeight - 60, rect.bottom + 8)}px`;
  tooltip.classList.remove("hidden");
}

function hideBulkGenerationGuardTooltip() {
  qs("bulkGenerationGuardTooltip")?.classList.add("hidden");
}

function setBulkGenerationControlGuard(control, blocked) {
  if (!(control instanceof HTMLElement)) return;
  if (blocked) {
    if (control.dataset.bulkGuarded === "true") return;
    control.dataset.bulkGuarded = "true";
    control.dataset.bulkPriorAriaDisabled = control.getAttribute("aria-disabled") || "";
    control.dataset.bulkPriorTabindex = control.getAttribute("tabindex") || "";
    control.dataset.bulkPriorDescribedby = control.getAttribute("aria-describedby") || "";
    control.setAttribute("aria-disabled", "true");
    control.setAttribute("aria-describedby", "bulkGenerationGuardDescription");
    if (!control.hasAttribute("tabindex")) control.setAttribute("tabindex", "0");
    return;
  }
  if (control.dataset.bulkGuarded !== "true") return;
  const priorAria = control.dataset.bulkPriorAriaDisabled || "";
  const priorTabindex = control.dataset.bulkPriorTabindex || "";
  if (priorAria) control.setAttribute("aria-disabled", priorAria);
  else control.removeAttribute("aria-disabled");
  const priorDescribedby = control.dataset.bulkPriorDescribedby || "";
  if (priorDescribedby) control.setAttribute("aria-describedby", priorDescribedby);
  else control.removeAttribute("aria-describedby");
  if (priorTabindex) control.setAttribute("tabindex", priorTabindex);
  else control.removeAttribute("tabindex");
  delete control.dataset.bulkGuarded;
  delete control.dataset.bulkPriorAriaDisabled;
  delete control.dataset.bulkPriorTabindex;
  delete control.dataset.bulkPriorDescribedby;
}

function applyBulkGenerationControlGuards() {
  const shouldBlock = !bulkGenerationCanonicalState.verified || bulkGenerationCanonicalState.active;
  const message = bulkGenerationGuardMessage();
  const description = qs("bulkGenerationGuardDescription");
  const tooltip = qs("bulkGenerationGuardTooltip");
  if (description && description.textContent.trim() !== message) description.textContent = message;
  if (tooltip && !tooltip.classList.contains("hidden") && tooltip.textContent !== message) {
    tooltip.textContent = message;
  }
  document.querySelectorAll("button, a[href], input, select, textarea, [role='button']").forEach((control) => {
    setBulkGenerationControlGuard(control, shouldBlock && !bulkGenerationControlIsSafe(control));
  });
  document.body.classList.toggle("bulk-generation-guard-active", shouldBlock);
  if (!shouldBlock) hideBulkGenerationGuardTooltip();
}

function publishBulkGenerationState(payload, { verification = "verified" } = {}) {
  const status = String(payload?.status || "none");
  const verified = verification === "verified";
  bulkGenerationCanonicalState = {
    ...(payload || {}),
    verified,
    verification,
    active: verified && BULK_GENERATION_ACTIVE_STATUSES.has(status),
    terminal: verified && BULK_GENERATION_TERMINAL_STATUSES.has(status),
  };
  applyBulkGenerationControlGuards();
  window.dispatchEvent(new CustomEvent(BULK_GENERATION_STATE_EVENT, {
    detail: { ...bulkGenerationCanonicalState },
  }));
}

async function refreshBulkGenerationState() {
  try {
    const response = await fetch("/planning/bulk-generation/status", { headers: { Accept: "application/json" } });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok || payload?.ok !== true) throw new Error("Bulk Generate status unavailable");
    publishBulkGenerationState(payload);
  } catch (_) {
    publishBulkGenerationState(
      { ...bulkGenerationCanonicalState, status: "unknown" },
      { verification: "failed" }
    );
  }
  window.clearTimeout(bulkGenerationPollTimer);
  if (!bulkGenerationCanonicalState.terminal) {
    const delay = document.hidden ? 15000 : 3000;
    bulkGenerationPollTimer = window.setTimeout(refreshBulkGenerationState, delay);
  }
  return { ...bulkGenerationCanonicalState };
}

async function requestBulkGenerationStop() {
  const runId = String(bulkGenerationCanonicalState.run_id || "");
  if (!runId || !bulkGenerationCanonicalState.active) return;
  const response = await fetch(`/planning/bulk-generation/runs/${encodeURIComponent(runId)}/stop`, {
    method: "POST", headers: { Accept: "application/json" },
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload?.message || "Could not request Bulk Generate stop.");
  publishBulkGenerationState(payload);
}

window.ApplyLensBulkGeneration = {
  getState: () => ({ ...bulkGenerationCanonicalState }),
  refresh: refreshBulkGenerationState,
  stop: requestBulkGenerationStop,
  isActive: () => bulkGenerationCanonicalState.verified && bulkGenerationCanonicalState.active,
};

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

  const collapseBtn = qs("appShellCollapseBtn");
  if (collapseBtn) {
    collapseBtn.setAttribute("aria-pressed", isCollapsed ? "true" : "false");
    const label = isCollapsed ? "Expand sidebar" : "Collapse sidebar";
    collapseBtn.setAttribute("aria-label", label);
    collapseBtn.title = label;

    const iconWrap = collapseBtn.querySelector(".app-shell-collapse-icon");
    if (iconWrap) {
      iconWrap.innerHTML = isCollapsed ? APP_SHELL_MENU_SVG : APP_SHELL_COLLAPSE_SVG;
    }
  }

  if (persist) {
    window.localStorage.setItem(APP_SHELL_COLLAPSED_KEY, isCollapsed ? "true" : "false");
  }
}

// Bounded notification-center history window. The API stays bounded too:
// its server-side read limit is unchanged.
const NOTIFICATION_HISTORY_LIMIT = 50;
const NOTIFICATION_RECONCILIATION_TIMEOUT_MS = 12000;
let notificationActiveFilter = "all";
let notificationRowsCache = [];

function notificationTypeMeta(row) {
  const jobName = String(row?.job_name || "").trim().toLowerCase();
  if (jobName === "agent_discovery") {
    return {
      key: "discovery",
      label: "Discovery",
      icon: '<circle cx="12" cy="12" r="9" /><polygon points="15.5 8.5 10.5 10.5 8.5 15.5 13.5 13.5" />',
    };
  }
  if (jobName === "live_pipeline") {
    return {
      key: "pipeline",
      label: "Pipeline",
      icon: '<path d="M3 12h4l3 8 4-16 3 8h4" />',
    };
  }
  return {
    key: "other",
    label: jobName ? jobName.replace(/_/g, " ") : "Activity",
    icon: '<circle cx="12" cy="12" r="9" /><path d="M12 8v4" /><path d="M12 16h.01" />',
  };
}

function notificationMatchesFilter(row, filter) {
  if (filter === "unread") return !row?.is_read;
  if (filter === "pipeline") return notificationTypeMeta(row).key === "pipeline";
  if (filter === "discovery") return notificationTypeMeta(row).key === "discovery";
  return true;
}

function escapeNotificationAttr(value) {
  return String(value == null ? "" : value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

// Scheduler subjects are produced by src/pipeline/post_run_email.py with the
// fixed grammar "Scheduled job {TOKEN} | {job_name} | {detail}". Parsing is
// deterministic against that grammar only; anything else falls back to a
// compact truncated title with the full value in the tooltip.
const NOTIFICATION_SUBJECT_PATTERN =
  /^Scheduled job\s+([A-Za-z_]+)\s*\|\s*([A-Za-z0-9_]+)\s*(?:\|\s*(.*))?$/;

const NOTIFICATION_TITLE_MAX = 60;

function notificationStatusWord(token) {
  const normalized = String(token || "").trim().toUpperCase();
  if (normalized === "SUCCEEDED") return "completed";
  if (normalized === "FAILED") return "failed";
  if (!normalized) return "updated";
  return normalized.toLowerCase().replace(/_/g, " ");
}

function notificationJobLabel(jobName) {
  const normalized = String(jobName || "").trim().toLowerCase();
  if (normalized === "live_pipeline") return "Live Pipeline";
  if (normalized === "agent_discovery") return "Agent Discovery";
  if (!normalized) return "Scheduler";
  return normalized
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function notificationCountLabel(rawValue, noun) {
  const numeric = Number(String(rawValue).trim());
  if (!Number.isFinite(numeric)) return "";
  return `${numeric.toLocaleString("en-US")} ${noun}`;
}

function notificationDetailMetric(detail) {
  const raw = String(detail || "").trim();
  if (!raw) return "";

  const displayJobs = raw.match(/^display_jobs=(-?\d+)$/);
  if (displayJobs) return notificationCountLabel(displayJobs[1], "jobs");

  const discovered = raw.match(/^discovered=(-?\d+)$/);
  if (discovered) return notificationCountLabel(discovered[1], "discovered");

  const stage = raw.match(/^stage=(.+)$/);
  if (stage) return `stage ${stage[1].trim().replace(/_/g, " ")}`;

  return raw.replace(/_/g, " ").replace(/\s*,\s*/g, ", ");
}

function truncateNotificationTitle(value) {
  const raw = String(value || "").trim();
  if (raw.length <= NOTIFICATION_TITLE_MAX) return raw;
  return `${raw.slice(0, NOTIFICATION_TITLE_MAX - 1).trimEnd()}\u2026`;
}

// Returns { headline, metric, full }. `full` is always the complete original
// subject so the tooltip can surface it on hover and keyboard focus.
function notificationTitleParts(row) {
  const raw = String(row?.title || row?.subject || "").trim();
  if (!raw) {
    return { headline: "Scheduler update", metric: "", full: "Scheduler update" };
  }

  const match = raw.match(NOTIFICATION_SUBJECT_PATTERN);
  if (!match) {
    return { headline: truncateNotificationTitle(raw), metric: "", full: raw };
  }

  const headline = `${notificationJobLabel(match[2])} ${notificationStatusWord(match[1])}`;
  return { headline, metric: notificationDetailMetric(match[3]), full: raw };
}

function normalizeNotificationTitle(row) {
  return notificationTitleParts(row).headline;
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
      className: "notification-pill is-success",
    };
  }

  if (runStatus === "failed" || runStatus === "error") {
    return {
      label: "FAILED",
      className: "notification-pill is-error",
    };
  }

  const level = String(row?.level || "").trim().toLowerCase();
  if (level === "success") {
    return {
      label: "SUCCESS",
      className: "notification-pill is-success",
    };
  }
  if (level === "error") {
    return {
      label: "FAILED",
      className: "notification-pill is-error",
    };
  }

  return {
    label: "INFO",
    className: "notification-pill is-info",
  };
}

function setNotificationLoading(listEl, message) {
  if (!listEl) return;
  listEl.innerHTML = `<div class="notification-center__empty">${message}</div>`;
}

function renderNotificationRows(listEl, rows, unreadOnly) {
  if (!listEl) return;

  if (!Array.isArray(rows) || rows.length === 0) {
    const caughtUp = unreadOnly;
    listEl.innerHTML = `
      <div class="notification-center__empty">
        <span class="notification-center__empty-icon" aria-hidden="true">${caughtUp ? "\u2713" : "\u2022"}</span>
        <strong>${caughtUp ? "You're all caught up" : "No notifications yet"}</strong>
        <span>${caughtUp ? "No unread notifications." : "Scheduler activity will appear here."}</span>
      </div>
    `;
    return;
  }

  listEl.innerHTML = rows.map((row) => {
    const notificationId = escapeNotificationAttr(String(row.notification_id || ""));
    const titleParts = notificationTitleParts(row);
    const createdAt = formatNotificationTime(row.created_at || "");
    const isRead = Boolean(row.is_read);
    const badgeMeta = notificationBadgeMeta(row);
    const typeMeta = notificationTypeMeta(row);
    const destination = notificationDestination(row);
    const toggleLabel = isRead ? "Mark unread" : "Mark read";

    return `
      <article
        class="notification-row ${isRead ? "is-read" : "is-unread"} ${destination ? "is-clickable" : ""}"
        data-notification-id="${notificationId}"
        data-notification-destination="${destination}"
      >
        <span class="notification-row__dot" aria-hidden="true"></span>
        <span class="notification-row__tile is-${typeMeta.key}" aria-hidden="true">
          <svg class="app-shell-icon" viewBox="0 0 24 24" width="15" height="15" fill="none"
               stroke="currentColor" stroke-width="2" stroke-linecap="round"
               stroke-linejoin="round" focusable="false">${typeMeta.icon}</svg>
        </span>
        <div class="notification-row__body">
          <div
            class="notification-row__title"
            tabindex="0"
            data-tooltip="${escapeNotificationAttr(titleParts.full)}"
            aria-label="${escapeNotificationAttr(titleParts.full)}"
          >${titleParts.headline}</div>
          <div class="notification-row__pills">
            <span class="notification-pill is-${typeMeta.key}">${typeMeta.label}</span>
            ${titleParts.metric
              ? `<span class="notification-pill is-metric">${titleParts.metric}</span>`
              : ""}
            <span class="${badgeMeta.className}">${badgeMeta.label}</span>
            ${isRead ? "" : '<span class="notification-row__sr">Unread</span>'}
          </div>
        </div>
        <div class="notification-row__meta">
          <span class="notification-row__time">${createdAt}</span>
          <span class="notification-row__actions">
            <button
              type="button"
              class="notification-row__action"
              data-notification-toggle="${notificationId}"
              data-notification-action="toggle"
              data-next-read="${isRead ? "false" : "true"}"
              aria-label="${toggleLabel}"
              title="${toggleLabel}"
            ><svg class="app-shell-icon" viewBox="0 0 24 24" width="14" height="14" fill="none"
                 stroke="currentColor" stroke-width="2.25" stroke-linecap="round"
                 stroke-linejoin="round" aria-hidden="true" focusable="false">${
              isRead
                ? '<rect x="2" y="4" width="20" height="16" rx="2" /><path d="m22 7-10 5L2 7" />'
                : '<path d="M20 6 9 17l-5-5" />'
            }</svg></button>
            <button
              type="button"
              class="notification-row__action notification-row__delete"
              data-notification-delete="${notificationId}"
              data-notification-action="delete"
              aria-label="Delete notification"
              title="Delete notification"
            ><svg class="app-shell-icon" viewBox="0 0 24 24" width="14" height="14" fill="none"
                 stroke="currentColor" stroke-width="2.1" stroke-linecap="round"
                 stroke-linejoin="round" aria-hidden="true" focusable="false">
              <path d="M3 6h18" /><path d="M8 6V4h8v2" />
              <path d="M19 6l-1 14H6L5 6" /><path d="M10 11v5" /><path d="M14 11v5" />
            </svg></button>
          </span>
        </div>
      </article>
    `;
  }).join("");
}

async function fetchJson(url, options = {}) {
  const response = await window.fetch(url, options);
  const payload = await response.json().catch(() => ({}));

  if (!response.ok) {
    const structuredDetail = payload && typeof payload.detail === "object"
      ? payload.detail
      : null;
    const detail = payload && typeof payload.detail === "string"
      ? payload.detail
      : structuredDetail?.error_category === "bulk_generation_in_progress"
        ? structuredDetail.message || BULK_GENERATION_BLOCK_MESSAGE
        : structuredDetail?.message || payload?.message || `Request failed: ${response.status}`;
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


function currentPathForLoginNext() {
  const path = window.location.pathname || "/";
  const query = window.location.search || "";
  return `${path}${query}`;
}

function redirectToLoginAfterIdle() {
  const next = encodeURIComponent(currentPathForLoginNext());
  window.location.href = `/login?next=${next}`;
}

async function logoutAfterInactivity() {
  try {
    await fetch("/auth/logout", {
      method: "POST",
      credentials: "same-origin",
      headers: {
        Accept: "application/json",
      },
    });
  } catch (_) {
    // Redirect anyway. The server-side session may already be expired.
  }

  redirectToLoginAfterIdle();
}

function initAuthInactivityLogout() {
  if (document.body.classList.contains("auth-page")) return;

  let idleTimeoutSeconds = APPLYLENS_DEFAULT_IDLE_TIMEOUT_SECONDS;
  let idleTimer = null;
  let isLoggingOut = false;
  let lastActivityAt = Date.now();

  function idleLimitMs() {
    return Math.max(1, Number(idleTimeoutSeconds || APPLYLENS_DEFAULT_IDLE_TIMEOUT_SECONDS)) * 1000;
  }

  function hasExceededIdleLimit() {
    return Date.now() - lastActivityAt >= idleLimitMs();
  }

  function triggerIdleLogout() {
    if (isLoggingOut) return;
    isLoggingOut = true;

    if (idleTimer) {
      window.clearTimeout(idleTimer);
      idleTimer = null;
    }

    logoutAfterInactivity();
  }

  function armIdleTimer() {
    if (isLoggingOut) return;

    if (idleTimer) {
      window.clearTimeout(idleTimer);
    }

    const remainingMs = Math.max(1, idleLimitMs() - (Date.now() - lastActivityAt));
    idleTimer = window.setTimeout(() => {
      triggerIdleLogout();
    }, remainingMs);
  }

  function recordUserActivity() {
    if (isLoggingOut) return;

    if (hasExceededIdleLimit()) {
      triggerIdleLogout();
      return;
    }

    lastActivityAt = Date.now();
    armIdleTimer();
  }

  const activityEvents = [
    "click",
    "keydown",
    "mousedown",
    "scroll",
    "touchstart",
    "pointerdown",
  ];

  activityEvents.forEach((eventName) => {
    window.addEventListener(eventName, recordUserActivity, {
      passive: true,
      capture: true,
    });
  });

  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible" && hasExceededIdleLimit()) {
      triggerIdleLogout();
    }
  });

  fetch("/auth/session-config", {
    credentials: "same-origin",
    headers: {
      Accept: "application/json",
    },
  })
    .then((response) => response.ok ? response.json() : {})
    .then((payload) => {
      const configuredTimeout = Number(payload.idle_timeout_seconds || 0);
      if (Number.isFinite(configuredTimeout) && configuredTimeout > 0) {
        idleTimeoutSeconds = configuredTimeout;
      }
      lastActivityAt = Date.now();
      armIdleTimer();
    })
    .catch(() => {
      lastActivityAt = Date.now();
      armIdleTimer();
    });

  armIdleTimer();
}


window.addEventListener("DOMContentLoaded", () => {
  const menuBtn = qs("appShellMenuBtn");
  const collapseBtn = qs("appShellCollapseBtn");
  const themeToggleBtn = qs("themeToggleBtn");

  applyJobstackTheme(getStoredJobstackTheme(), { persist: false });
  applyBulkGenerationControlGuards();

  const guardedControl = (target) => target instanceof Element
    ? target.closest("[data-bulk-guarded='true']")
    : null;
  document.addEventListener("click", (event) => {
    const control = guardedControl(event.target);
    if (!control) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    showBulkGenerationGuardTooltip(control);
  }, true);
  document.addEventListener("keydown", (event) => {
    if (!["Enter", " "].includes(event.key)) return;
    const control = guardedControl(event.target);
    if (!control) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    showBulkGenerationGuardTooltip(control);
  }, true);
  document.addEventListener("mouseover", (event) => {
    const control = guardedControl(event.target);
    if (control) showBulkGenerationGuardTooltip(control);
  });
  document.addEventListener("mouseout", (event) => {
    if (guardedControl(event.target)) hideBulkGenerationGuardTooltip();
  });
  document.addEventListener("focusin", (event) => {
    const control = guardedControl(event.target);
    if (control) showBulkGenerationGuardTooltip(control);
  });
  document.addEventListener("focusout", (event) => {
    if (guardedControl(event.target)) hideBulkGenerationGuardTooltip();
  });

  new MutationObserver(() => {
    if (typeof document !== "undefined" && document.body) {
      applyBulkGenerationControlGuards();
    }
  }).observe(document.body, {
    childList: true,
    subtree: true,
  });

  document.addEventListener("visibilitychange", () => {
    if (!document.hidden && !bulkGenerationCanonicalState.terminal) void refreshBulkGenerationState();
  });
  void refreshBulkGenerationState();

  const saved = window.localStorage.getItem(APP_SHELL_COLLAPSED_KEY);
  const defaultCollapsed = saved === null ? window.innerWidth < 1220 : saved === "true";
  setShellCollapsed(defaultCollapsed, { persist: false });

  // Desktop: sidebar collapse/expand toggle (deterministic, persisted).
  if (collapseBtn) {
    collapseBtn.addEventListener("click", (event) => {
      event.preventDefault();
      const next = !document.body.classList.contains("app-shell-collapsed");
      setShellCollapsed(next);
    });
  }

  // Mobile: left Sheet/drawer. Single owner for open/close, overlay, Escape,
  // focus trap, route-close, and focus restoration. Body scroll lock is applied
  // by the CSS `body.app-shell-mobile-open` rule.
  const appShell = qs("appShell");
  const appShellOverlay = qs("appShellOverlay");
  const appShellCloseBtn = qs("appShellCloseBtn");

  function isMobileDrawerOpen() {
    return document.body.classList.contains("app-shell-mobile-open");
  }

  function drawerFocusableElements() {
    if (!appShell) return [];
    const selector =
      'a[href], button:not([disabled]), input:not([disabled]), [tabindex]:not([tabindex="-1"])';
    return Array.from(appShell.querySelectorAll(selector)).filter(
      (el) => el.offsetParent !== null
    );
  }

  function openMobileDrawer() {
    if (!appShell || isMobileDrawerOpen()) return;
    document.body.classList.add("app-shell-mobile-open");
    if (appShellOverlay) appShellOverlay.hidden = false;
    if (menuBtn) {
      menuBtn.setAttribute("aria-expanded", "true");
      menuBtn.setAttribute("aria-label", "Close navigation");
      menuBtn.title = "Close navigation";
    }
    const focusables = drawerFocusableElements();
    const target = appShellCloseBtn || focusables[0] || appShell;
    if (target && typeof target.focus === "function") target.focus();
  }

  function closeMobileDrawer({ restoreFocus = true } = {}) {
    if (!isMobileDrawerOpen()) return;
    document.body.classList.remove("app-shell-mobile-open");
    if (appShellOverlay) appShellOverlay.hidden = true;
    if (menuBtn) {
      menuBtn.setAttribute("aria-expanded", "false");
      menuBtn.setAttribute("aria-label", "Open navigation");
      menuBtn.title = "Open navigation";
    }
    if (restoreFocus && menuBtn && typeof menuBtn.focus === "function") {
      menuBtn.focus();
    }
  }

  if (menuBtn) {
    menuBtn.addEventListener("click", (event) => {
      event.preventDefault();
      if (isMobileDrawerOpen()) {
        closeMobileDrawer();
      } else {
        openMobileDrawer();
      }
    });
  }

  if (appShellCloseBtn) {
    appShellCloseBtn.addEventListener("click", (event) => {
      event.preventDefault();
      closeMobileDrawer();
    });
  }

  if (appShellOverlay) {
    appShellOverlay.addEventListener("click", () => {
      closeMobileDrawer();
    });
  }

  if (appShell) {
    appShell.addEventListener("click", (event) => {
      const target = event.target;
      if (!(target instanceof Element)) return;
      if (target.closest(".app-shell-nav-link")) {
        closeMobileDrawer({ restoreFocus: false });
      }
    });
  }

  document.addEventListener("keydown", (event) => {
    if (!isMobileDrawerOpen()) return;

    if (event.key === "Escape") {
      event.preventDefault();
      closeMobileDrawer();
      return;
    }

    if (event.key === "Tab") {
      const focusables = drawerFocusableElements();
      if (focusables.length === 0) return;

      const first = focusables[0];
      const last = focusables[focusables.length - 1];
      const active = document.activeElement;

      if (appShell && !appShell.contains(active)) {
        event.preventDefault();
        first.focus();
      } else if (event.shiftKey && active === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && active === last) {
        event.preventDefault();
        first.focus();
      }
    }
  });

  window.addEventListener("resize", () => {
    if (window.innerWidth > 980 && isMobileDrawerOpen()) {
      closeMobileDrawer({ restoreFocus: false });
    }
  });

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
  const notificationRefreshBtn = qs("notificationRefreshBtn");
  const notificationMarkAllReadBtn = qs("notificationMarkAllReadBtn");
  const notificationDeleteAllBtn = qs("notificationDeleteAllBtn");
  const notificationDeleteConfirmModal = qs("notificationDeleteConfirmModal");
  const notificationDeleteConfirmTitle = qs("notificationDeleteConfirmTitle");
  const notificationDeleteConfirmBody = qs("notificationDeleteConfirmBody");
  const notificationDeleteCancelBtn = qs("notificationDeleteCancelBtn");
  const notificationDeleteConfirmBtn = qs("notificationDeleteConfirmBtn");

  // The desktop toolbar has accumulated historical positioning and backdrop
  // filtering layers. Keep the one shared confirmation surface outside that
  // coordinate system so fixed/inset always resolve against the viewport.
  if (
    notificationDeleteConfirmModal
    && notificationDeleteConfirmModal.parentElement !== document.body
  ) {
    document.body.appendChild(notificationDeleteConfirmModal);
  }

  const menuShell = qs("profileMenuShell");
  const menuButton = qs("profileMenuButton");
  const dropdown = qs("profileDropdown");
  const profileDropdownAvatar = qs("profileDropdownAvatar");
  const profileDropdownName = qs("profileDropdownName");
  const profileDropdownEmail = qs("profileDropdownEmail");
  const profileLogoutBtn = qs("profileLogoutBtn");
  const profileAdminToolsSection = qs("profileAdminToolsSection");
  const profileAdvancedDiagnosticsLink = qs("profileAdvancedDiagnosticsLink");
  const profileAgenticOperationsLink = qs("profileAgenticOperationsLink");
  const profileSchedulerHealthLink = qs("profileSchedulerHealthLink");

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

  function isAccountConfigurationRoute(pathname = window.location.pathname) {
    const normalizedPath = String(pathname || "/").trim().replace(/\/+$/, "") || "/";
    return new Set([
      "/onboarding",
      "/profile",
      "/profile/preferences",
      "/profile/ai-settings",
    ]).has(normalizedPath);
  }

  function clearNewUserWorkspaceEmptyState() {
    storageRemove(window.localStorage, APPLYLENS_NEW_USER_EMPTY_KEY);
    document.body.classList.remove("app-new-user-empty");
    document.querySelectorAll(".new-user-empty-state").forEach((node) => node.remove());
  }

  function openLivePipelineFromShell() {
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
    if (isAccountConfigurationRoute()) return;

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
    if (isAccountConfigurationRoute()) return;

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

      clearNewUserWorkspaceEmptyState();
    } catch (_) {
      ensureNewUserEmptyState();
    }
  }

  async function redirectIncompleteOnboarding() {
    if (document.body.classList.contains("auth-page")) return false;

    const currentPath = window.location.pathname || "/";
    if (currentPath === "/profile" || currentPath.startsWith("/static/")) return false;

    try {
      const response = await fetch("/onboarding/status", {
        headers: { Accept: "application/json" },
        credentials: "same-origin",
      });
      if (!response.ok) return false;

      const payload = await response.json();
      if (payload && payload.onboarding_completed === false) {
        const hasProfileResume = payload.requirements?.has_profile_resume === true;
        const destination = hasProfileResume
          ? "/onboarding"
          : "/profile?onboarding=resume_upload";
        if (currentPath !== destination) {
          window.location.href = destination;
          return true;
        }
      }
    } catch (_) {
      // Onboarding is a product setup gate; failed status checks should not block navigation.
    }
    return false;
  }

  function closeFirstRunPrompt(modal) {
    storageRemove(window.sessionStorage, APPLYLENS_FIRST_RUN_PROMPT_KEY);
    modal.classList.add("hidden");
    modal.setAttribute("aria-hidden", "true");
  }

  function showFirstRunPrompt() {
    if (isAccountConfigurationRoute()) return;
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

  function closeProfileMenu({ restoreFocus = false } = {}) {
    if (!dropdown || !menuButton) return;
    const wasOpen = !dropdown.classList.contains("hidden");
    dropdown.classList.add("hidden");
    dropdown.setAttribute("aria-hidden", "true");
    menuButton.setAttribute("aria-expanded", "false");
    if (restoreFocus && wasOpen) {
      menuButton.focus();
    }
  }

  function openProfileMenu() {
    if (!dropdown || !menuButton) return;
    dropdown.classList.remove("hidden");
    dropdown.setAttribute("aria-hidden", "false");
    menuButton.setAttribute("aria-expanded", "true");
  }

    function userInitialFromName(name, email) {
    const source = String(name || email || "A").trim();
    return source ? source.charAt(0).toUpperCase() : "A";
  }

  function setProfileShellUser(user) {
    const displayName = String(user?.display_name || user?.email || "Account").trim();
    const email = String(user?.email || "").trim();
    const accessLevel = String(user?.access_level || "").trim().toLowerCase();
    const isAdmin = Boolean(user?.is_admin) || accessLevel === "admin";
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

    if (profileAdminToolsSection) {
      profileAdminToolsSection.classList.toggle("hidden", !isAdmin);
      profileAdminToolsSection.setAttribute("aria-hidden", isAdmin ? "false" : "true");
    }

    if (profileAdvancedDiagnosticsLink) {
      profileAdvancedDiagnosticsLink.classList.toggle("hidden", !isAdmin);
      profileAdvancedDiagnosticsLink.setAttribute("aria-hidden", isAdmin ? "false" : "true");
      profileAdvancedDiagnosticsLink.tabIndex = isAdmin ? 0 : -1;
    }

    if (profileAgenticOperationsLink) {
      profileAgenticOperationsLink.classList.toggle("hidden", !isAdmin);
      profileAgenticOperationsLink.setAttribute("aria-hidden", isAdmin ? "false" : "true");
      profileAgenticOperationsLink.tabIndex = isAdmin ? 0 : -1;
    }

    if (profileSchedulerHealthLink) {
      profileSchedulerHealthLink.classList.toggle("hidden", !isAdmin);
      profileSchedulerHealthLink.setAttribute("aria-hidden", isAdmin ? "false" : "true");
      profileSchedulerHealthLink.tabIndex = isAdmin ? 0 : -1;
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

  async function openNotifications() {
    if (!notificationDropdown || !notificationButton) return;
    positionNotificationDropdown();
    notificationDropdown.classList.remove("hidden");
    notificationButton.setAttribute("aria-expanded", "true");
    // Every closed -> open transition owns a fresh, bounded server read. The
    // request tokens inside both loaders keep older responses from winning.
    await Promise.all([
      loadNotifications(),
      loadUnreadCount(),
    ]);
  }

  let notificationUnreadCountCache = null;

  function setNotificationUnreadCount(unreadCount) {
    const normalized = Math.max(0, Number(unreadCount || 0));
    notificationUnreadCountCache = normalized;
    if (!notificationBadge) return;
    if (normalized > 0) {
      notificationBadge.textContent = normalized > 99 ? "99+" : String(normalized);
      notificationBadge.classList.remove("hidden");
    } else {
      notificationBadge.textContent = "0";
      notificationBadge.classList.add("hidden");
    }
  }

  function adjustNotificationUnreadCount(delta) {
    if (!Number.isFinite(notificationUnreadCountCache)) return;
    setNotificationUnreadCount(notificationUnreadCountCache + delta);
  }

  async function loadUnreadCount(options = {}) {
    if (!notificationBadge) return;

    const silent = Boolean(options.silent);
    const signal = options.signal;

    notificationUnreadFetchToken += 1;
    const token = notificationUnreadFetchToken;

    try {
      const payload = await fetchJson("/notifications/unread-count", { cache: "no-store", signal });
      if (token !== notificationUnreadFetchToken) return;
      setNotificationUnreadCount(payload.unread_count);
    } catch (error) {
      if (token !== notificationUnreadFetchToken) return;
      if (silent) throw error;
      notificationBadge.textContent = "!";
      notificationBadge.classList.remove("hidden");
    }
  }

  // Notifications with a mutation in flight. Held here rather than on the
  // button element because every refresh re-renders the feed and destroys the
  // node the click started on, which is why the old per-node `disabled` guard
  // allowed conflicting second mutations for the same notification.
  const notificationPendingIds = new Set();
  const notificationPendingActions = new Map();
  const notificationConfirmedReadStates = new Map();
  const notificationConfirmedDeletedIds = new Set();
  let notificationDeleteAllCutoff = "";
  let notificationGlobalMutationPending = false;
  let notificationDeleteIntent = null;
  let notificationDeleteReturnFocus = null;

  // Monotonic token so a slow earlier fetch can never overwrite the cache with
  // pre-mutation rows after a newer fetch has already landed.
  let notificationFetchToken = 0;
  let notificationUnreadFetchToken = 0;

  function syncNotificationPendingButtons() {
    if (!notificationList) return;
    notificationList.querySelectorAll("[data-notification-toggle], [data-notification-delete]").forEach((button) => {
      const id = String(
        button.getAttribute("data-notification-toggle")
        || button.getAttribute("data-notification-delete")
        || ""
      ).trim();
      const pending = id && notificationPendingIds.has(id);
      if (notificationGlobalMutationPending || pending) {
        button.setAttribute("disabled", "disabled");
      } else {
        button.removeAttribute("disabled");
      }
      if (pending && notificationPendingActions.get(id) === button.dataset.notificationAction) {
        button.setAttribute("aria-busy", "true");
      } else {
        button.removeAttribute("aria-busy");
      }
    });
    [notificationDeleteAllBtn, notificationMarkAllReadBtn]
      .filter(Boolean)
      .forEach((button) => {
        button.disabled = notificationGlobalMutationPending || notificationPendingIds.size > 0;
      });
  }

  function releaseNotificationMutation(notificationId) {
    notificationPendingIds.delete(notificationId);
    notificationPendingActions.delete(notificationId);
    syncNotificationPendingButtons();
  }

  function releaseNotificationGlobalMutation() {
    notificationGlobalMutationPending = false;
    syncNotificationPendingButtons();
  }

  async function loadNotifications(options = {}) {
    if (!notificationList) return;

    const silent = Boolean(options.silent);
    const signal = options.signal;
    const params = new URLSearchParams();
    params.set("limit", String(NOTIFICATION_HISTORY_LIMIT));

    // A refresh triggered by a row mutation must not blank the feed; only an
    // explicit open/refresh shows the loading placeholder.
    if (!silent) {
      setNotificationLoading(notificationList, "Loading notifications...");
    }

    notificationFetchToken += 1;
    const token = notificationFetchToken;

    try {
      const payload = await fetchJson(`/notifications?${params.toString()}`, { cache: "no-store", signal });
      if (token !== notificationFetchToken) return;
      const incomingRows = Array.isArray(payload.rows) ? payload.rows : [];
      notificationRowsCache = incomingRows
        .filter((row) => {
          const notificationId = String(row?.notification_id || "").trim();
          if (notificationConfirmedDeletedIds.has(notificationId)) return false;
          if (!notificationDeleteAllCutoff) return true;
          const createdAt = String(row?.created_at || "").trim();
          const createdAtMs = Date.parse(createdAt);
          const cutoffMs = Date.parse(notificationDeleteAllCutoff);
          if (Number.isFinite(createdAtMs) && Number.isFinite(cutoffMs)) {
            return createdAtMs > cutoffMs;
          }
          return createdAt && createdAt > notificationDeleteAllCutoff;
        })
        .map((row) => {
          const notificationId = String(row?.notification_id || "").trim();
          if (!notificationConfirmedReadStates.has(notificationId)) return row;
          const confirmedRead = notificationConfirmedReadStates.get(notificationId);
          if (Boolean(row?.is_read) === confirmedRead) {
            notificationConfirmedReadStates.delete(notificationId);
            return row;
          }
          return { ...row, is_read: confirmedRead };
        });
      renderFilteredNotifications();
    } catch (error) {
      if (token !== notificationFetchToken) return;
      if (silent) throw error;
      setNotificationLoading(
        notificationList,
        `Could not load notifications. ${error instanceof Error ? error.message : ""}`.trim()
      );
    }
  }

  function renderFilteredNotifications() {
    if (!notificationList) return;
    const visible = notificationRowsCache.filter(
      (row) => notificationMatchesFilter(row, notificationActiveFilter)
    );
    renderNotificationRows(notificationList, visible, notificationActiveFilter === "unread");
    syncNotificationPendingButtons();
    // The list is replaced with innerHTML, so apply the existing accessible
    // fail-closed Bulk guard to the new mutation controls synchronously.
    applyBulkGenerationControlGuards();
    const unread = notificationRowsCache.filter((row) => !row?.is_read).length;
    const pill = qs("notificationUnreadPill");
    if (pill) {
      pill.textContent = `${unread} new`;
      pill.classList.toggle("hidden", unread <= 0);
    }
  }

  async function reconcileNotificationsInBackground() {
    const controller = new AbortController();
    const timeoutId = window.setTimeout(
      () => controller.abort(),
      NOTIFICATION_RECONCILIATION_TIMEOUT_MS
    );

    try {
      await Promise.all([
        loadNotifications({ silent: true, signal: controller.signal }),
        loadUnreadCount({ silent: true, signal: controller.signal }),
      ]);
    } catch (_) {
      // The authoritative mutation already succeeded. A later open or manual
      // refresh owns a new reconciliation, so a transient/obsolete background
      // failure must not roll back state or masquerade as mutation failure.
      controller.abort();
    } finally {
      window.clearTimeout(timeoutId);
    }
  }

  function startNotificationReconciliation() {
    void reconcileNotificationsInBackground();
  }

  document.querySelectorAll("[data-notification-filter]").forEach((chip) => {
    chip.addEventListener("click", () => {
      notificationActiveFilter = String(chip.dataset.notificationFilter || "all");
      document.querySelectorAll("[data-notification-filter]").forEach((other) => {
        const active = other === chip;
        other.classList.toggle("is-active", active);
        other.setAttribute("aria-selected", active ? "true" : "false");
      });
      renderFilteredNotifications();
    });
  });

  async function updateNotificationReadState(notificationId, isRead) {
    return fetchJson("/notifications/read-state", {
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

  async function deleteNotification(notificationId) {
    return fetchJson("/notifications/delete", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        notification_id: notificationId,
      }),
    });
  }

  async function deleteAllNotifications() {
    return fetchJson("/notifications/delete-all", {
      method: "POST",
    });
  }

  function applyConfirmedNotificationReadState(notificationId, payload) {
    const confirmed = payload?.notification;
    if (
      !confirmed
      || String(confirmed.notification_id || "").trim() !== notificationId
      || typeof confirmed.is_read !== "boolean"
    ) {
      throw new Error("Notification state response was incomplete.");
    }

    const index = notificationRowsCache.findIndex(
      (row) => String(row?.notification_id || "").trim() === notificationId
    );
    if (index < 0) return;
    const wasRead = Boolean(notificationRowsCache[index]?.is_read);
    const isRead = confirmed.is_read;
    notificationConfirmedReadStates.set(notificationId, isRead);
    notificationFetchToken += 1;
    notificationRowsCache[index] = { ...notificationRowsCache[index], ...confirmed, is_read: isRead };
    if (wasRead !== isRead) adjustNotificationUnreadCount(isRead ? -1 : 1);
    renderFilteredNotifications();
  }

  function applyConfirmedNotificationDelete(notificationId, payload) {
    if (
      payload?.deleted !== true
      || String(payload?.notification_id || "").trim() !== notificationId
    ) {
      throw new Error("Notification delete response was incomplete.");
    }
    const deletedRow = notificationRowsCache.find(
      (row) => String(row?.notification_id || "").trim() === notificationId
    );
    notificationConfirmedDeletedIds.add(notificationId);
    notificationConfirmedReadStates.delete(notificationId);
    notificationFetchToken += 1;
    notificationRowsCache = notificationRowsCache.filter(
      (row) => String(row?.notification_id || "").trim() !== notificationId
    );
    if (deletedRow && !Boolean(deletedRow.is_read)) adjustNotificationUnreadCount(-1);
    renderFilteredNotifications();
  }

  function applyConfirmedDeleteAll(payload) {
    if (payload?.deleted !== true) {
      throw new Error("Delete-all response was incomplete.");
    }
    notificationDeleteAllCutoff = String(payload?.state_row?.state_timestamp || new Date().toISOString());
    notificationConfirmedReadStates.clear();
    notificationFetchToken += 1;
    notificationRowsCache = [];
    setNotificationUnreadCount(0);
    renderFilteredNotifications();
  }

  function closeNotificationDeleteConfirmation({ restoreFocus = true } = {}) {
    if (!notificationDeleteConfirmModal) return;
    notificationDeleteConfirmModal.classList.add("hidden");
    notificationDeleteConfirmModal.setAttribute("aria-hidden", "true");
    const returnFocus = notificationDeleteReturnFocus;
    notificationDeleteIntent = null;
    notificationDeleteReturnFocus = null;
    if (restoreFocus && returnFocus instanceof HTMLElement && returnFocus.isConnected) {
      returnFocus.focus();
    }
  }

  function openNotificationDeleteConfirmation(intent, trigger) {
    if (
      !notificationDeleteConfirmModal
      || !notificationDeleteConfirmTitle
      || !notificationDeleteConfirmBody
      || !notificationDeleteConfirmBtn
    ) return;

    const deleteAll = intent?.kind === "all";
    notificationDeleteIntent = deleteAll
      ? { kind: "all", notificationId: "" }
      : { kind: "one", notificationId: String(intent?.notificationId || "").trim() };
    notificationDeleteReturnFocus = trigger instanceof HTMLElement ? trigger : null;
    notificationDeleteConfirmTitle.textContent = deleteAll
      ? "Delete all notifications?"
      : "Delete notification?";
    notificationDeleteConfirmBody.textContent = deleteAll
      ? "This removes all notifications from your inbox. Scheduler history is not affected."
      : "This removes it from Notifications. Scheduler history is not affected.";
    notificationDeleteConfirmBtn.textContent = deleteAll ? "Delete all" : "Delete";
    notificationDeleteConfirmModal.classList.remove("hidden");
    notificationDeleteConfirmModal.setAttribute("aria-hidden", "false");
    notificationDeleteCancelBtn?.focus();
  }

async function markAllNotificationsRead() {
  const payload = await fetchJson("/notifications?is_read=false&limit=100");
  const unreadRows = Array.isArray(payload.rows) ? payload.rows : [];

  for (const row of unreadRows) {
    const notificationId = String(row.notification_id || "").trim();
    if (!notificationId) continue;

    const confirmed = await updateNotificationReadState(notificationId, true);
    applyConfirmedNotificationReadState(notificationId, confirmed);
  }

  return unreadRows.length;
}

  if (notificationButton && notificationDropdown) {
    notificationButton.addEventListener("click", async (event) => {
      event.stopPropagation();
      const isHidden = notificationDropdown.classList.contains("hidden");

      closeProfileMenu();

      if (isHidden) {
        await openNotifications();
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

    if (notificationGlobalMutationPending || notificationPendingIds.size > 0) return;
    notificationGlobalMutationPending = true;

    notificationMarkAllReadBtn.setAttribute("disabled", "disabled");
    syncNotificationPendingButtons();

    try {
      await markAllNotificationsRead();
      releaseNotificationGlobalMutation();
      startNotificationReconciliation();
    } catch (error) {
      window.alert(
        `Could not mark all notifications read. ${error instanceof Error ? error.message : ""}`.trim()
      );
    } finally {
      releaseNotificationGlobalMutation();
    }
  });
}

  if (notificationDeleteAllBtn) {
    notificationDeleteAllBtn.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      if (notificationGlobalMutationPending || notificationPendingIds.size > 0) return;
      openNotificationDeleteConfirmation({ kind: "all" }, notificationDeleteAllBtn);
    });
  }

  if (notificationDeleteCancelBtn) {
    notificationDeleteCancelBtn.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      if (notificationGlobalMutationPending || notificationPendingIds.size > 0) return;
      closeNotificationDeleteConfirmation();
    });
  }

  if (notificationDeleteConfirmModal) {
    notificationDeleteConfirmModal.addEventListener("click", (event) => {
      if (event.target !== notificationDeleteConfirmModal) return;
      if (notificationGlobalMutationPending || notificationPendingIds.size > 0) return;
      closeNotificationDeleteConfirmation();
    });
  }

  if (notificationDeleteConfirmBtn) {
    notificationDeleteConfirmBtn.addEventListener("click", async (event) => {
      event.preventDefault();
      event.stopPropagation();

      const intent = notificationDeleteIntent;
      if (!intent) return;
      const notificationId = String(intent.notificationId || "").trim();
      if (intent.kind === "one") {
        if (!notificationId) return;
        if (notificationGlobalMutationPending) return;
        if (notificationPendingIds.has(notificationId)) return;
        notificationPendingIds.add(notificationId);
        notificationPendingActions.set(notificationId, "delete");
      } else {
        if (notificationGlobalMutationPending || notificationPendingIds.size > 0) return;
        notificationGlobalMutationPending = true;
      }

      notificationDeleteConfirmBtn.setAttribute("disabled", "disabled");
      notificationDeleteConfirmBtn.setAttribute("aria-busy", "true");
      const confirmLabel = intent.kind === "all" ? "Delete all" : "Delete";
      notificationDeleteConfirmBtn.textContent = "Deleting\u2026";
      notificationDeleteCancelBtn?.setAttribute("disabled", "disabled");
      syncNotificationPendingButtons();

      try {
        if (intent.kind === "one") {
          const payload = await deleteNotification(notificationId);
          applyConfirmedNotificationDelete(notificationId, payload);
        } else {
          const payload = await deleteAllNotifications();
          applyConfirmedDeleteAll(payload);
        }
        closeNotificationDeleteConfirmation({ restoreFocus: false });
        if (intent.kind === "one") {
          releaseNotificationMutation(notificationId);
        } else {
          releaseNotificationGlobalMutation();
        }
        notificationDeleteConfirmBtn.removeAttribute("disabled");
        notificationDeleteConfirmBtn.removeAttribute("aria-busy");
        notificationDeleteConfirmBtn.textContent = confirmLabel;
        notificationDeleteCancelBtn?.removeAttribute("disabled");
        startNotificationReconciliation();
      } catch (error) {
        window.alert(
          `Could not delete notification${intent.kind === "all" ? "s" : ""}. ${error instanceof Error ? error.message : ""}`.trim()
        );
      } finally {
        if (intent.kind === "one") {
          releaseNotificationMutation(notificationId);
        } else {
          releaseNotificationGlobalMutation();
        }
        notificationDeleteConfirmBtn.removeAttribute("disabled");
        notificationDeleteConfirmBtn.removeAttribute("aria-busy");
        notificationDeleteConfirmBtn.textContent = confirmLabel;
        notificationDeleteCancelBtn?.removeAttribute("disabled");
      }
    });
  }

  if (notificationList) {
    notificationList.addEventListener("click", async (event) => {
      const target = event.target;
      // Row actions are compact buttons whose visible surface is almost
      // entirely their nested SVG icon. A click landing on that <svg> or a
      // <path>/<rect> inside it sets event.target to an SVGElement, which is
      // NOT an instanceof HTMLElement even though .closest() works on it
      // identically. Gating on HTMLElement silently dropped exactly those
      // clicks: the icon fill, not the button padding, is what users actually
      // click, so mark-read/unread and delete appeared to "randomly do
      // nothing" depending on the exact pixel clicked.
      if (!(target instanceof Element)) return;

      const deleteBtn = target.closest("[data-notification-delete]");
      if (deleteBtn) {
        event.preventDefault();
        event.stopPropagation();
        const notificationId = String(deleteBtn.getAttribute("data-notification-delete") || "").trim();
        if (!notificationId || notificationGlobalMutationPending) return;
        if (notificationPendingIds.has(notificationId)) return;
        openNotificationDeleteConfirmation(
          { kind: "one", notificationId },
          deleteBtn
        );
        return;
      }

      const clickableCard = target.closest(".notification-row[data-notification-destination]");
      if (clickableCard && !target.closest("[data-notification-toggle], [data-notification-delete]")) {
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
      if (notificationGlobalMutationPending) return;

      // Exactly one mutation per notification may be in flight. A second click
      // on the same row (including on the button re-rendered by the refresh)
      // is dropped rather than racing the first.
      if (notificationPendingIds.has(notificationId)) return;
      notificationPendingIds.add(notificationId);
      notificationPendingActions.set(notificationId, "toggle");
      syncNotificationPendingButtons();

      try {
        const payload = await updateNotificationReadState(notificationId, nextRead);
        applyConfirmedNotificationReadState(notificationId, payload);
        releaseNotificationMutation(notificationId);
        startNotificationReconciliation();
      } catch (error) {
        window.alert(
          `Could not update notification state. ${error instanceof Error ? error.message : ""}`.trim()
        );
      } finally {
        releaseNotificationMutation(notificationId);
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
      if (
        notificationDeleteConfirmModal
        && !notificationDeleteConfirmModal.classList.contains("hidden")
        && !notificationGlobalMutationPending
        && notificationPendingIds.size === 0
      ) {
        closeNotificationDeleteConfirmation();
        return;
      }
      closeProfileMenu({ restoreFocus: true });
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
  redirectIncompleteOnboarding().then(async (redirecting) => {
    if (redirecting || isAccountConfigurationRoute()) return;
    await refreshNewUserWorkspaceState();
    showFirstRunPrompt();
  });
  initAuthInactivityLogout();
});
