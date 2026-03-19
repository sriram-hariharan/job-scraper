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

function setTextIfPresent(id, value) {
  const el = qs(id);
  if (el) {
    el.textContent = String(value);
  }
}

function countPlanningActiveFilters() {
  let count = 0;
  if (qs("planningActionFilter").value.trim()) count += 1;
  if (qs("planningWinnerBucket").value.trim()) count += 1;
  if (qs("planningUndecidedOnly").checked) count += 1;
  return count;
}

function renderTableLoading(colspan, label) {
  return `
    <tr>
      <td colspan="${colspan}">
        <div class="loading-state">
          <div class="loading-spinner"></div>
          <div class="loading-text">${escapeHtml(label)}</div>
        </div>
      </td>
    </tr>
  `;
}

function updatePlanningStats(rowCount) {
  setTextIfPresent("planningJobsShown", rowCount ?? 0);
  setTextIfPresent("planningActiveFilters", countPlanningActiveFilters());
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

function buildPlanningUrl() {
  const params = new URLSearchParams();
  const action = qs("planningActionFilter").value.trim();
  const winnerBucket = qs("planningWinnerBucket").value.trim();
  const undecidedOnly = qs("planningUndecidedOnly").checked ? "true" : "";
  const limit = qs("planningLimitInput").value || "50";

  if (action) params.set("action", action);
  if (winnerBucket) params.set("winner_bucket", winnerBucket);
  if (undecidedOnly) params.set("undecided_only", undecidedOnly);
  params.set("limit", limit);

  return `/browse?${params.toString()}`;
}

function buildApplicationPayloadFromRow(row) {
  return {
    job_doc_id: row.job_doc_id || "",
    job_url: row.job_url || row.job_doc_id || "",
    job_company: row.job_company || "",
    job_title: row.job_title || "",
    source_view: "planning",
  };
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

function persistPendingApplication(job) {
  sessionStorage.setItem(PENDING_APPLICATION_STORAGE_KEY, JSON.stringify(job));
}

function loadPendingApplicationFromStorage() {
  const raw = sessionStorage.getItem(PENDING_APPLICATION_STORAGE_KEY);
  if (!raw) return null;

  try {
    return JSON.parse(raw);
  } catch {
    sessionStorage.removeItem(PENDING_APPLICATION_STORAGE_KEY);
    return null;
  }
}

function clearPendingApplication() {
  sessionStorage.removeItem(PENDING_APPLICATION_STORAGE_KEY);
}

function getApplicationModal() {
  return qs("applicationActionModal");
}

function openApplicationModal(job) {
  if (!job) return;
  qs("applicationModalCompany").textContent = job.job_company || "-";
  qs("applicationModalTitle").textContent = job.job_title || "-";
  getApplicationModal().classList.remove("hidden");
}

function closeApplicationModal() {
  getApplicationModal().classList.add("hidden");
}

async function submitApplicationStatus(status) {
  const job = loadPendingApplicationFromStorage();
  if (!job) return;

  await postJson("/application-actions", {
    ...job,
    application_status: status,
  });

  clearPendingApplication();
  closeApplicationModal();
  await loadPlanningTable();
}

async function handleApplyClick(button) {
  const payload = {
    job_doc_id: button.dataset.jobDocId || "",
    job_url: button.dataset.jobUrl || "",
    job_company: button.dataset.jobCompany || "",
    job_title: button.dataset.jobTitle || "",
    source_view: "planning",
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

function renderPlanningRows(rows, metaLabel) {
  const tbody = qs("planningTableBody");
  const safeRows = Array.isArray(rows) ? rows : [];

  if (!safeRows.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="19" class="empty-state">No rows found.</td>
      </tr>
    `;
    qs("planningTableMeta").textContent = metaLabel;
    updatePlanningStats(0);
    return;
  }

  tbody.innerHTML = safeRows.map((row) => {
    const title = escapeHtml(row.job_title || "");
    const jobUrl = escapeHtml(row.job_doc_id || row.job_url || "");
    const titleHtml = jobUrl
      ? `<a class="job-link" href="${jobUrl}" target="_blank" rel="noopener noreferrer">${title}</a>`
      : title;

    return `
      <tr>
        <td>${escapeHtml(row.queue_rank || "")}</td>
        <td><span class="pill">${escapeHtml(row.action || "")}</span></td>
        <td>${escapeHtml(row.job_company || "")}</td>
        <td class="title-cell">${titleHtml}</td>
        <td>${escapeHtml(row.winner_resume || "")}</td>
        <td>${escapeHtml(row.winner_score || "")}</td>
        <td>${escapeHtml(row.runner_up_resume || "")}</td>
        <td>${escapeHtml(row.runner_up_score || "")}</td>
        <td>${escapeHtml(row.score_gap || "")}</td>
        <td>${escapeHtml(row.winner_bucket || "")}</td>
        <td>${escapeHtml(row.is_tie || "")}</td>
        <td>${escapeHtml(row.needs_variant_review || "")}</td>
        <td>${escapeHtml(row.missing_requirement_count || "")}</td>
        <td>${escapeHtml(row.llm_fallback_best_resume || "")}</td>
        <td>${escapeHtml(row.llm_fallback_status || "")}</td>
        <td>${escapeHtml(row.operator_decision || "")}</td>
        <td>${escapeHtml(row.operator_selected_resume || "")}</td>
        <td class="reason-cell">${escapeHtml(row.queue_priority_reason || "")}</td>
        <td class="apply-cell sticky-apply-col">${buildApplicationButtonHtml(row)}</td>
      </tr>
    `;
  }).join("");

  qs("planningTableMeta").textContent = metaLabel;
  updatePlanningStats(safeRows.length);
}

async function loadPlanningTable() {
  const tbody = qs("planningTableBody");
  tbody.innerHTML = renderTableLoading(19, "Loading planning rows...");
  qs("planningTableMeta").textContent = "Loading...";

  const url = buildPlanningUrl();
  const data = await fetchJson(url);
  const count = data.count ?? 0;

  renderPlanningRows(
    data.rows || [],
    `Planning detail view · ${count} row${count === 1 ? "" : "s"}`
  );
}

function clearPlanningFilters() {
  qs("planningActionFilter").value = "";
  qs("planningWinnerBucket").value = "";
  qs("planningUndecidedOnly").checked = false;
  qs("planningLimitInput").value = "50";
  updatePlanningStats(0);
}

function attachPlanningHandlers() {
  qs("planningApplyFiltersBtn").addEventListener("click", async () => {
    try {
      await loadPlanningTable();
    } catch (err) {
      alert(`Failed to load planning table: ${err.message}`);
    }
  });

  qs("planningClearFiltersBtn").addEventListener("click", async () => {
    clearPlanningFilters();
    try {
      await loadPlanningTable();
    } catch (err) {
      alert(`Failed to reload planning table: ${err.message}`);
    }
  });

  qs("planningTableBody").addEventListener("click", async (event) => {
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
    if (!pending || !getApplicationModal().classList.contains("hidden")) return;
    openApplicationModal(pending);
  });
}

window.addEventListener("DOMContentLoaded", async () => {
  attachPlanningHandlers();
  try {
    await loadPlanningTable();
  } catch (err) {
    alert(`Failed to initialize planning dashboard: ${err.message}`);
  }
});