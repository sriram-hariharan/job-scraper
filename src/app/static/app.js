const state = {
  currentMode: "browse",
  workflowView: null,
  pendingApplicationJob: null,
  applicationModalOpen: false,
};

const PENDING_APPLICATION_STORAGE_KEY = "job_operator_pending_application";

function escapeHtml(value) {
  if (value === null || value === undefined) return "";
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function qs(id) {
  return document.getElementById(id);
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`HTTP ${response.status}: ${text}`);
  }
  return response.json();
}

async function postJson(url, payload) {
  return fetchJson(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}

function renderStats(statusData) {
  const summary = statusData.summary || {};
  const undecided = statusData.undecided_review_counts || {};

  qs("statQueueRows").textContent = summary.execution_queue_rows ?? "-";
  qs("statDecisionRows").textContent = summary.operator_decisions_rows ?? "-";
  qs("statUndecidedApplyReview").textContent = undecided.APPLY_REVIEW_VARIANTS ?? 0;
  qs("statUndecidedMaybeTailor").textContent = undecided.MAYBE_TAILOR ?? 0;
}

function buildApplicationPayloadFromRow(row) {
  return {
    job_doc_id: row.job_doc_id || "",
    job_url: row.job_url || row.job_doc_id || "",
    job_company: row.job_company || "",
    job_title: row.job_title || "",
    source_view: state.currentMode === "workflow" && state.workflowView
      ? `executive:${state.workflowView}`
      : "executive:browse",
  };
}

function persistPendingApplication(job) {
  state.pendingApplicationJob = job;
  sessionStorage.setItem(PENDING_APPLICATION_STORAGE_KEY, JSON.stringify(job));
}

function loadPendingApplicationFromStorage() {
  const raw = sessionStorage.getItem(PENDING_APPLICATION_STORAGE_KEY);
  if (!raw) return null;

  try {
    const parsed = JSON.parse(raw);
    state.pendingApplicationJob = parsed;
    return parsed;
  } catch {
    sessionStorage.removeItem(PENDING_APPLICATION_STORAGE_KEY);
    state.pendingApplicationJob = null;
    return null;
  }
}

function clearPendingApplication() {
  state.pendingApplicationJob = null;
  sessionStorage.removeItem(PENDING_APPLICATION_STORAGE_KEY);
}

function buildApplicationButtonHtml(row) {
  const isApplied = Boolean(row.is_applied);
  const label = escapeHtml(row.application_label || (isApplied ? "Applied" : "Apply"));
  const buttonClass = isApplied ? "job-apply-btn applied-btn" : "job-apply-btn apply-btn";
  const disabledAttr = isApplied ? "disabled" : "";

  return `
    <button
      type="button"
      class="${buttonClass}"
      ${disabledAttr}
      data-apply-job="true"
      data-job-doc-id="${escapeHtml(row.job_doc_id || "")}"
      data-job-url="${escapeHtml(row.job_url || row.job_doc_id || "")}"
      data-job-company="${escapeHtml(row.job_company || "")}"
      data-job-title="${escapeHtml(row.job_title || "")}"
    >
      ${label}
    </button>
  `;
}

function buildQueueRowHtml(row) {
  const queueRank = escapeHtml(row.queue_rank || "");
  const action = escapeHtml(row.action || "");
  const company = escapeHtml(row.job_company || "");
  const title = escapeHtml(row.job_title || "");
  const jobUrl = escapeHtml(row.job_doc_id || row.job_url || "");
  const titleHtml = jobUrl
    ? `<a class="job-link" href="${jobUrl}" target="_blank" rel="noopener noreferrer">${title}</a>`
    : title;
  const applyButtonHtml = buildApplicationButtonHtml(row);
  const winnerResume = escapeHtml(row.winner_resume || "");
  const winnerScore = escapeHtml(row.winner_score || "");
  const runnerUpResume = escapeHtml(row.runner_up_resume || "");
  const scoreGap = escapeHtml(row.score_gap || "");
  const missingRequirementCount = escapeHtml(row.missing_requirement_count || "");
  const operatorDecision = escapeHtml(row.operator_decision || "");
  const operatorSelectedResume = escapeHtml(row.operator_selected_resume || "");
  const reason = escapeHtml(row.queue_priority_reason || "");

  return `
    <tr>
      <td>${queueRank}</td>
      <td><span class="pill">${action || "-"}</span></td>
      <td>${company}</td>
      <td class="title-cell">${titleHtml}</td>
      <td>${winnerResume}</td>
      <td>${winnerScore}</td>
      <td>${runnerUpResume}</td>
      <td>${scoreGap}</td>
      <td>${missingRequirementCount}</td>
      <td>${operatorDecision || "-"}</td>
      <td>${operatorSelectedResume || "-"}</td>
      <td class="reason-cell">${reason}</td>
      <td class="apply-cell sticky-apply-col">${applyButtonHtml}</td>
    </tr>
  `;
}

function renderQueueRows(rows, metaLabel) {
  const tbody = qs("queueTableBody");
  const safeRows = Array.isArray(rows) ? rows : [];

  if (!safeRows.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="13" class="empty-state">No rows found.</td>
      </tr>
    `;
  } else {
    tbody.innerHTML = safeRows.map(buildQueueRowHtml).join("");
  }

  qs("tableMeta").textContent = metaLabel;
}

function buildBrowseUrl() {
  const action = qs("actionFilter").value.trim();
  const undecidedOnly = qs("undecidedOnly").checked ? "true" : "";
  const limit = qs("limitInput").value || "25";

  const params = new URLSearchParams();
  if (action) params.set("action", action);
  if (undecidedOnly) params.set("undecided_only", undecidedOnly);
  params.set("limit", limit);

  return `/browse?${params.toString()}`;
}

async function loadStatus() {
  const data = await fetchJson("/status");
  renderStats(data);
}

async function loadBrowse() {
  state.currentMode = "browse";
  state.workflowView = null;

  const url = buildBrowseUrl();
  const data = await fetchJson(url);
  const count = data.count ?? 0;

  renderQueueRows(
    data.rows || [],
    `Browse view · ${count} row${count === 1 ? "" : "s"}`
  );
}

async function loadWorkflow(view) {
  state.currentMode = "workflow";
  state.workflowView = view;

  const limit = qs("limitInput").value || "25";
  const params = new URLSearchParams({
    view,
    limit,
  });

  const data = await fetchJson(`/workflow?${params.toString()}`);
  const count = data.count ?? 0;

  renderQueueRows(
    data.rows || [],
    `Workflow view: ${view} · ${count} row${count === 1 ? "" : "s"}`
  );
}

async function reloadCurrentTable() {
  if (state.currentMode === "workflow" && state.workflowView) {
    await loadWorkflow(state.workflowView);
  } else {
    await loadBrowse();
  }
}

function clearFilters() {
  qs("actionFilter").value = "";
  qs("undecidedOnly").checked = false;
  qs("limitInput").value = "25";
}

function getApplicationModal() {
  return qs("applicationActionModal");
}

function openApplicationModal(job) {
  if (!job) return;

  state.applicationModalOpen = true;
  qs("applicationModalCompany").textContent = job.job_company || "-";
  qs("applicationModalTitle").textContent = job.job_title || "-";
  getApplicationModal().classList.remove("hidden");
}

function closeApplicationModal() {
  state.applicationModalOpen = false;
  getApplicationModal().classList.add("hidden");
}

async function submitApplicationStatus(status) {
  const job = state.pendingApplicationJob;
  if (!job) return;

  await postJson("/application-actions", {
    ...job,
    application_status: status,
  });

  clearPendingApplication();
  closeApplicationModal();
  await reloadCurrentTable();
}

async function handleApplyClick(button) {
  const payload = {
    job_doc_id: button.dataset.jobDocId || "",
    job_url: button.dataset.jobUrl || "",
    job_company: button.dataset.jobCompany || "",
    job_title: button.dataset.jobTitle || "",
    source_view: state.currentMode === "workflow" && state.workflowView
      ? `executive:${state.workflowView}`
      : "executive:browse",
  };

  await postJson("/application-actions", {
    ...payload,
    application_status: "OPENED",
  });

  persistPendingApplication(payload);

  const targetUrl = payload.job_url || payload.job_doc_id;
  if (targetUrl) {
    window.open(targetUrl, "_blank", "noopener,noreferrer");
  }
}

function attachApplicationHandlers() {
  qs("queueTableBody").addEventListener("click", async (event) => {
    const button = event.target.closest("[data-apply-job='true']");
    if (!button || button.disabled) return;

    try {
      await handleApplyClick(button);
    } catch (err) {
      alert(`Failed to open apply workflow: ${err.message}`);
    }
  });

  qs("closeApplicationModalBtn").addEventListener("click", () => {
    clearPendingApplication();
    closeApplicationModal();
  });

  getApplicationModal().addEventListener("click", (event) => {
    if (event.target === getApplicationModal()) {
      clearPendingApplication();
      closeApplicationModal();
    }
  });

  document.querySelectorAll("[data-status-action]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const status = btn.dataset.statusAction;
      if (!status) return;

      try {
        await submitApplicationStatus(status);
      } catch (err) {
        alert(`Failed to update application status: ${err.message}`);
      }
    });
  });

  window.addEventListener("focus", () => {
    const pending = loadPendingApplicationFromStorage();
    if (!pending || state.applicationModalOpen) return;
    openApplicationModal(pending);
  });
}

function attachEventHandlers() {
  qs("applyFiltersBtn").addEventListener("click", async () => {
    try {
      await loadBrowse();
    } catch (err) {
      alert(`Failed to load browse data: ${err.message}`);
    }
  });

  qs("clearFiltersBtn").addEventListener("click", async () => {
    clearFilters();
    try {
      await loadBrowse();
    } catch (err) {
      alert(`Failed to reload browse data: ${err.message}`);
    }
  });

  qs("refreshStatusBtn").addEventListener("click", async () => {
    try {
      await loadStatus();
      await reloadCurrentTable();
    } catch (err) {
      alert(`Failed to refresh dashboard: ${err.message}`);
    }
  });

  document.querySelectorAll(".quick-view-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const view = btn.dataset.view;
      if (!view) return;
      try {
        await loadWorkflow(view);
      } catch (err) {
        alert(`Failed to load workflow view: ${err.message}`);
      }
    });
  });
}

async function init() {
  attachEventHandlers();
  attachApplicationHandlers();

  try {
    await loadStatus();
    await loadBrowse();
  } catch (err) {
    alert(`Failed to initialize dashboard: ${err.message}`);
  }
}

window.addEventListener("DOMContentLoaded", init);