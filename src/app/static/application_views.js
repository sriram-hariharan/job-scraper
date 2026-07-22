(() => {
const APPLICATIONS_STATE_EVENT_NAME = "applylens:applications-dashboard-state";
const APPLICATIONS_ACTION_EVENT_NAME = "applylens:applications-dashboard-action";
const APPLICATIONS_READY_EVENT_NAME = "applylens:applications-dashboard-ready";
const APPLICATION_TAB_CONFIG = {
  APPLIED: { endpoint: "/applied-jobs", pageLabel: "Applied Jobs", emptyLabel: "No applied jobs yet." },
  SAVED: { endpoint: "/saved-jobs", pageLabel: "Saved for Later", emptyLabel: "No jobs have been saved for later." },
};

const applicationState = {
  status: "loading", rows: [], message: "", metaLabel: "Loading...", resultKey: "initial", activeTab: "APPLIED",
  filters: { companyContains: "", titleContains: "", limit: 15 }, sort: { key: "", direction: "asc" },
  pagination: { page: 1, pageSize: 15, totalCount: 0, totalPages: 1, hasPrevPage: false, hasNextPage: false },
};
let applicationRequestId = 0;
let applicationsDashboardInitialized = false;
const qs = (id) => document.getElementById(id);

function publishApplicationsState() {
  const payload = { ...applicationState, rows: applicationState.rows.slice(), filters: { ...applicationState.filters }, sort: { ...applicationState.sort }, pagination: { ...applicationState.pagination } };
  window.__APPLYLENS_APPLICATIONS_STATE__ = payload;
  window.dispatchEvent(new CustomEvent(APPLICATIONS_STATE_EVENT_NAME, { detail: payload }));
}
async function fetchJson(url) { const response = await fetch(url); if (!response.ok) throw new Error(`HTTP ${response.status}: ${await response.text()}`); return response.json(); }
function extractErrorMessage(error) { let message = error?.message || String(error || "Unknown error"); const match = message.match(/^HTTP \d+:\s*(.*)$/s); if (match) message = match[1]; try { const parsed = JSON.parse(message); if (parsed.detail) message = typeof parsed.detail === "string" ? parsed.detail : JSON.stringify(parsed.detail); } catch { /* keep safe text */ } return message; }
function showAppError(title, error) { qs("appErrorTitle").textContent = title; qs("appErrorSubtitle").textContent = "Review the message below."; qs("appErrorMessage").textContent = extractErrorMessage(error); qs("appErrorModal").classList.remove("hidden"); }

function buildApplicationListUrl() {
  const config = APPLICATION_TAB_CONFIG[applicationState.activeTab]; const params = new URLSearchParams();
  if (applicationState.filters.companyContains.trim()) params.set("company_contains", applicationState.filters.companyContains.trim());
  if (applicationState.filters.titleContains.trim()) params.set("title_contains", applicationState.filters.titleContains.trim());
  params.set("limit", String(applicationState.filters.limit || 15)); params.set("page", String(applicationState.pagination.page || 1));
  return `${config.endpoint}?${params.toString()}`;
}

async function loadApplicationView() {
  const requestId = ++applicationRequestId;
  applicationState.status = "loading"; applicationState.message = ""; publishApplicationsState();
  try {
    const data = await fetchJson(buildApplicationListUrl()); const totalCount = Number(data.total_count ?? data.count ?? 0);
    if (requestId !== applicationRequestId) return;
    applicationState.rows = Array.isArray(data.rows) ? data.rows : [];
    applicationState.pagination = { page: Number(data.page || 1), pageSize: Number(data.page_size || 15), totalCount, totalPages: Number(data.total_pages || 1), hasPrevPage: Boolean(data.has_prev_page), hasNextPage: Boolean(data.has_next_page) };
    applicationState.metaLabel = `${APPLICATION_TAB_CONFIG[applicationState.activeTab].pageLabel} · ${totalCount} total job${totalCount === 1 ? "" : "s"}`;
    applicationState.status = "ready"; applicationState.resultKey = `${applicationState.activeTab}:${requestId}:${totalCount}`; publishApplicationsState();
  } catch (error) { if (requestId !== applicationRequestId) return; applicationState.status = "error"; applicationState.message = extractErrorMessage(error); publishApplicationsState(); }
}

async function handleApplicationsAction(event) {
  const action = event.detail || {};
  if (action.type === "sort_change") { applicationState.sort = { key: String(action.key || ""), direction: action.direction === "desc" ? "desc" : "asc" }; publishApplicationsState(); return; }
  if (action.type === "tab_change" && APPLICATION_TAB_CONFIG[action.tab]) { applicationState.activeTab = action.tab; applicationState.pagination.page = 1; await loadApplicationView(); return; }
  if (action.type === "apply_filters") { applicationState.filters = { companyContains: String(action.filters?.companyContains || ""), titleContains: String(action.filters?.titleContains || ""), limit: Number(action.filters?.limit || 15) }; applicationState.pagination.page = 1; await loadApplicationView(); return; }
  if (action.type === "clear_filters") { applicationState.filters = { companyContains: "", titleContains: "", limit: 15 }; applicationState.pagination.page = 1; await loadApplicationView(); return; }
  if (action.type === "page_change") { applicationState.pagination.page = Number(action.page || 1); await loadApplicationView(); return; }
  if (action.type === "retry") await loadApplicationView();
}

window.__APPLYLENS_APPLICATIONS_STATE__ = { ...applicationState };
window.addEventListener(APPLICATIONS_ACTION_EVENT_NAME, (event) => handleApplicationsAction(event).catch((error) => showAppError("Failed to update applications", error)));
function initializeApplicationsDashboard() {
  if (applicationsDashboardInitialized) { publishApplicationsState(); return; }

  qs("closeAppErrorModalBtn")?.addEventListener(
    "click",
    () => qs("appErrorModal")?.classList.add("hidden"),
  );
  qs("appErrorOkBtn")?.addEventListener(
    "click",
    () => qs("appErrorModal")?.classList.add("hidden"),
  );

  applicationsDashboardInitialized = true;
  loadApplicationView();
}
window.addEventListener(APPLICATIONS_READY_EVENT_NAME, initializeApplicationsDashboard);
if (document.readyState === "loading") window.addEventListener("DOMContentLoaded", initializeApplicationsDashboard, { once: true });
else initializeApplicationsDashboard();
if (window.__APPLYLENS_APPLICATIONS_REACT_READY__) initializeApplicationsDashboard();
})();
