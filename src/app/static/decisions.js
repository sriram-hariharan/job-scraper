(() => {
const PENDING_APPLICATION_STORAGE_KEY = "job_operator_pending_application";
const DECISIONS_STATE_EVENT_NAME = "applylens:decisions-dashboard-state";
const DECISIONS_ACTION_EVENT_NAME = "applylens:decisions-dashboard-action";
const DECISIONS_READY_EVENT_NAME = "applylens:decisions-dashboard-ready";

const decisionsState = {
  status: "loading",
  rows: [],
  metaLabel: "Loading...",
  message: "",
  resultKey: "initial",
  filters: { decisions: [], companyContains: "", limit: 15 },
  sort: { key: "", direction: "asc" },
  pagination: { page: 1, pageSize: 15, totalCount: 0, totalPages: 1, hasPrevPage: false, hasNextPage: false },
};
let decisionsRequestId = 0;
let decisionsDashboardInitialized = false;

const qs = (id) => document.getElementById(id);

function publishDecisionsState() {
  const payload = { ...decisionsState, rows: decisionsState.rows.slice(), filters: { ...decisionsState.filters, decisions: decisionsState.filters.decisions.slice() }, pagination: { ...decisionsState.pagination }, sort: { ...decisionsState.sort } };
  window.__APPLYLENS_DECISIONS_STATE__ = payload;
  window.dispatchEvent(new CustomEvent(DECISIONS_STATE_EVENT_NAME, { detail: payload }));
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) throw new Error(`HTTP ${response.status}: ${await response.text()}`);
  return response.json();
}

function postJson(url, payload) {
  return fetchJson(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
}

function extractErrorMessage(error) {
  let message = error?.message || String(error || "Unknown error");
  const match = message.match(/^HTTP \d+:\s*(.*)$/s);
  if (match) message = match[1];
  try { const parsed = JSON.parse(message); if (parsed.detail) message = typeof parsed.detail === "string" ? parsed.detail : JSON.stringify(parsed.detail); } catch { /* keep safe text */ }
  return message;
}

function showAppError(title, error) {
  qs("appErrorTitle").textContent = title;
  qs("appErrorSubtitle").textContent = "Review the message below.";
  qs("appErrorMessage").textContent = extractErrorMessage(error);
  qs("appErrorModal").classList.remove("hidden");
}

function buildDecisionsUrl(pageOverride = null) {
  const params = new URLSearchParams();
  decisionsState.filters.decisions.forEach((value) => params.append("decision", value));
  if (decisionsState.filters.companyContains.trim()) params.set("company_contains", decisionsState.filters.companyContains.trim());
  params.set("limit", String(decisionsState.filters.limit || 15));
  params.set("page", String(pageOverride ?? decisionsState.pagination.page ?? 1));
  return `/decisions?${params.toString()}`;
}

async function loadDecisionsTable(pageOverride = null) {
  const requestId = ++decisionsRequestId;
  decisionsState.status = "loading";
  decisionsState.message = "";
  publishDecisionsState();
  try {
    const data = await fetchJson(buildDecisionsUrl(pageOverride));
    if (requestId !== decisionsRequestId) return;
    const totalCount = Number(data.total_count ?? data.count ?? 0);
    decisionsState.rows = Array.isArray(data.rows) ? data.rows : [];
    decisionsState.pagination = {
      page: Number(data.page || 1), pageSize: Number(data.page_size || 15), totalCount,
      totalPages: Number(data.total_pages || 1), hasPrevPage: Boolean(data.has_prev_page), hasNextPage: Boolean(data.has_next_page),
    };
    decisionsState.metaLabel = `Decision history · ${totalCount} total record${totalCount === 1 ? "" : "s"}`;
    decisionsState.status = "ready";
    decisionsState.resultKey = `${requestId}:${decisionsState.pagination.page}:${totalCount}`;
    publishDecisionsState();
  } catch (error) {
    if (requestId !== decisionsRequestId) return;
    decisionsState.status = "error";
    decisionsState.message = extractErrorMessage(error);
    publishDecisionsState();
  }
}

function persistPendingApplication(job) { sessionStorage.setItem(PENDING_APPLICATION_STORAGE_KEY, JSON.stringify(job)); }
function clearPendingApplication() { sessionStorage.removeItem(PENDING_APPLICATION_STORAGE_KEY); }
function pendingApplication() { try { return JSON.parse(sessionStorage.getItem(PENDING_APPLICATION_STORAGE_KEY) || "null"); } catch { clearPendingApplication(); return null; } }
function closeApplicationModal() { qs("applicationActionModal").classList.add("hidden"); }
function openApplicationModal(job) { if (!job) return; qs("applicationModalCompany").textContent = job.job_company || "-"; qs("applicationModalTitle").textContent = job.job_title || "-"; qs("applicationActionModal").classList.remove("hidden"); }

async function openManualApplication(row) {
  const payload = { job_doc_id: String(row.job_doc_id || ""), job_url: String(row.job_url || row.job_doc_id || ""), job_company: String(row.job_company || ""), job_title: String(row.job_title || ""), source_view: "decisions" };
  await postJson("/application-actions", { ...payload, application_status: "OPENED" });
  persistPendingApplication(payload);
  const target = payload.job_url || payload.job_doc_id;
  if (target) window.open(target, "_blank", "noopener,noreferrer");
}

async function submitApplicationStatus(status) {
  const job = pendingApplication(); if (!job) return;
  await postJson("/application-actions", { ...job, application_status: status });
  clearPendingApplication(); closeApplicationModal(); await loadDecisionsTable();
}

async function handleDecisionsAction(event) {
  const action = event.detail || {};
  if (action.type === "sort_change") { decisionsState.sort = { key: String(action.key || ""), direction: action.direction === "desc" ? "desc" : "asc" }; publishDecisionsState(); return; }
  if (action.type === "apply_filters") { decisionsState.filters = { decisions: Array.isArray(action.filters?.decisions) ? action.filters.decisions : [], companyContains: String(action.filters?.companyContains || ""), limit: Number(action.filters?.limit || 15) }; decisionsState.pagination.page = 1; await loadDecisionsTable(1); return; }
  if (action.type === "clear_filters") { decisionsState.filters = { decisions: [], companyContains: "", limit: 15 }; decisionsState.pagination.page = 1; await loadDecisionsTable(1); return; }
  if (action.type === "page_change") { await loadDecisionsTable(Number(action.page || 1)); return; }
  if (action.type === "retry") { await loadDecisionsTable(); return; }
  if (action.type === "open_application") { try { await openManualApplication(action.row || {}); } catch (error) { showAppError("Failed to open application workflow", error); } }
}

window.__APPLYLENS_DECISIONS_STATE__ = { ...decisionsState };
window.addEventListener(DECISIONS_ACTION_EVENT_NAME, (event) => { handleDecisionsAction(event).catch((error) => showAppError("Failed to update decisions", error)); });
function initializeDecisionsDashboard() {
  if (decisionsDashboardInitialized) { publishDecisionsState(); return; }

  qs("closeAppErrorModalBtn")?.addEventListener(
    "click",
    () => qs("appErrorModal")?.classList.add("hidden"),
  );
  qs("appErrorOkBtn")?.addEventListener(
    "click",
    () => qs("appErrorModal")?.classList.add("hidden"),
  );
  qs("closeApplicationModalBtn")?.addEventListener("click", () => {
    clearPendingApplication();
    closeApplicationModal();
  });

  document.querySelectorAll("[data-status-action]").forEach((button) =>
    button.addEventListener("click", () =>
      submitApplicationStatus(button.dataset.statusAction).catch((error) =>
        showAppError("Failed to update application status", error),
      ),
    ),
  );

  window.addEventListener("focus", () => {
    const job = pendingApplication();
    const modal = qs("applicationActionModal");
    if (job && modal?.classList.contains("hidden")) openApplicationModal(job);
  });

  decisionsDashboardInitialized = true;
  loadDecisionsTable();
}
window.addEventListener(DECISIONS_READY_EVENT_NAME, initializeDecisionsDashboard);
if (document.readyState === "loading") window.addEventListener("DOMContentLoaded", initializeDecisionsDashboard, { once: true });
else initializeDecisionsDashboard();
if (window.__APPLYLENS_DECISIONS_REACT_READY__) initializeDecisionsDashboard();
})();
