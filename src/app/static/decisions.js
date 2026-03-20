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

function getAppErrorModal() {
  return qs("appErrorModal");
}

function closeAppErrorModal() {
  getAppErrorModal().classList.add("hidden");
}

function extractErrorMessage(err) {
  let message = err?.message || String(err || "Unknown error");

  const httpMatch = message.match(/^HTTP \d+:\s*(.*)$/s);
  if (httpMatch) {
    message = httpMatch[1];
  }

  try {
    const parsed = JSON.parse(message);
    if (Array.isArray(parsed.detail)) {
      message = parsed.detail
        .map((item) => {
          if (item && item.msg && item.input !== undefined) {
            return `${item.msg} (input: ${item.input})`;
          }
          if (item && item.msg) {
            return item.msg;
          }
          return JSON.stringify(item);
        })
        .join("\n");
    } else if (parsed.detail) {
      message = typeof parsed.detail === "string"
        ? parsed.detail
        : JSON.stringify(parsed.detail, null, 2);
    }
  } catch {
    // leave message as-is
  }

  return message;
}

function showAppError(title, err, subtitle = "Review the message below.") {
  qs("appErrorTitle").textContent = title || "Something went wrong";
  qs("appErrorSubtitle").textContent = subtitle;
  qs("appErrorMessage").textContent = extractErrorMessage(err);
  getAppErrorModal().classList.remove("hidden");
}

function bindAppErrorModal() {
  qs("closeAppErrorModalBtn").addEventListener("click", closeAppErrorModal);
  qs("appErrorOkBtn").addEventListener("click", closeAppErrorModal);

  getAppErrorModal().addEventListener("click", (event) => {
    if (event.target === getAppErrorModal()) {
      closeAppErrorModal();
    }
  });
}

function setTextIfPresent(id, value) {
  const el = qs(id);
  if (el) {
    el.textContent = String(value);
  }
}

function distinctDecisionJobCount(rows) {
  const safeRows = Array.isArray(rows) ? rows : [];
  const keys = new Set();

  for (const row of safeRows) {
    const key = [
      row.job_doc_id || row.job_url || "",
      row.job_company || "",
      row.job_title || "",
    ].join("||");
    if (key !== "||||") keys.add(key);
  }

  return keys.size;
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

function updateDecisionStats(rows) {
  const safeRows = Array.isArray(rows) ? rows : [];
  setTextIfPresent("decisionsShownCount", safeRows.length);
  setTextIfPresent("decisionsJobsTouched", distinctDecisionJobCount(safeRows));
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

function buildDecisionsUrl() {
  const params = new URLSearchParams();
  const decision = qs("decisionFilter").value.trim();
  const companyContains = qs("decisionCompanyFilter").value.trim();
  const limit = qs("decisionLimitInput").value || "50";

  if (decision) params.set("decision", decision);
  if (companyContains) params.set("company_contains", companyContains);
  params.set("limit", limit);

  return `/decisions?${params.toString()}`;
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
  await loadDecisionsTable();
}

async function handleApplyClick(button) {
  const payload = {
    job_doc_id: button.dataset.jobDocId || "",
    job_url: button.dataset.jobUrl || "",
    job_company: button.dataset.jobCompany || "",
    job_title: button.dataset.jobTitle || "",
    source_view: "decisions",
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

function renderDecisionRows(rows, metaLabel) {
  const tbody = qs("decisionsTableBody");
  const safeRows = Array.isArray(rows) ? rows : [];

  if (!safeRows.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="11" class="empty-state">No decisions found.</td>
      </tr>
    `;
    qs("decisionsTableMeta").textContent = metaLabel;
    updateDecisionStats([]);
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
        <td>${escapeHtml(row.decision_timestamp || "")}</td>
        <td>${escapeHtml(row.queue_rank || "")}</td>
        <td><span class="pill">${escapeHtml(row.decision || "")}</span></td>
        <td>${escapeHtml(row.job_company || "")}</td>
        <td class="title-cell">${titleHtml}</td>
        <td>${escapeHtml(row.planning_action || "")}</td>
        <td>${escapeHtml(row.selected_resume || "")}</td>
        <td>${escapeHtml(row.winner_resume || "")}</td>
        <td>${escapeHtml(row.runner_up_resume || "")}</td>
        <td class="reason-cell">${escapeHtml(row.note || "")}</td>
        <td class="apply-cell sticky-apply-col">${buildApplicationButtonHtml(row)}</td>
      </tr>
    `;
  }).join("");

  qs("decisionsTableMeta").textContent = metaLabel;
  updateDecisionStats(safeRows);
}

async function loadDecisionsTable() {
  const tbody = qs("decisionsTableBody");
  tbody.innerHTML = renderTableLoading(11, "Loading decisions...");
  qs("decisionsTableMeta").textContent = "Loading...";

  const url = buildDecisionsUrl();
  const data = await fetchJson(url);
  const count = data.count ?? 0;

  renderDecisionRows(
    data.rows || [],
    `Decisions view · ${count} row${count === 1 ? "" : "s"}`
  );
}

function clearDecisionFilters() {
  qs("decisionFilter").value = "";
  qs("decisionCompanyFilter").value = "";
  qs("decisionLimitInput").value = "50";
  updateDecisionStats([]);
}

function attachDecisionHandlers() {
  qs("decisionApplyFiltersBtn").addEventListener("click", async () => {
    try {
      await loadDecisionsTable();
    } catch (err) {
      showAppError("Failed to load decisions table", err);
    }
  });

  qs("decisionClearFiltersBtn").addEventListener("click", async () => {
    clearDecisionFilters();
    try {
      await loadDecisionsTable();
    } catch (err) {
      showAppError("Failed to reload decisions table", err);
    }
  });

  qs("decisionsTableBody").addEventListener("click", async (event) => {
    const button = event.target.closest("[data-apply-job='true']");
    if (!button || button.disabled) return;

    try {
      await handleApplyClick(button);
    } catch (err) {
      showAppError("Failed to open apply workflow", err);
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
        showAppError("Failed to update application status", err);
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
  bindAppErrorModal();
  attachDecisionHandlers();
  try {
    await loadDecisionsTable();
  } catch (err) {
    showAppError("Failed to initialize decisions dashboard", err);
  }
});