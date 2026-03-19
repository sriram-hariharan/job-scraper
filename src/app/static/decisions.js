function escapeHtml(value) {
  if (value === null || value === undefined) return "";
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
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
  qs("decisionsShownCount").textContent = String(safeRows.length);
  qs("decisionsJobsTouched").textContent = String(distinctDecisionJobCount(safeRows));
}

function qs(id) {
  return document.getElementById(id);
}

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`HTTP ${response.status}: ${text}`);
  }
  return response.json();
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

function renderDecisionRows(rows, metaLabel) {
  const tbody = qs("decisionsTableBody");
  const safeRows = Array.isArray(rows) ? rows : [];

  if (!safeRows.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="10" class="empty-state">No decisions found.</td>
      </tr>
    `;
    qs("decisionsTableMeta").textContent = metaLabel;
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
      </tr>
    `;
  }).join("");

  qs("decisionsTableMeta").textContent = metaLabel;
}

async function loadDecisionsTable() {
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
}

function attachDecisionHandlers() {
  qs("decisionApplyFiltersBtn").addEventListener("click", async () => {
    try {
      await loadDecisionsTable();
    } catch (err) {
      alert(`Failed to load decisions table: ${err.message}`);
    }
  });

  qs("decisionClearFiltersBtn").addEventListener("click", async () => {
    clearDecisionFilters();
    try {
      await loadDecisionsTable();
    } catch (err) {
      alert(`Failed to reload decisions table: ${err.message}`);
    }
  });
}

window.addEventListener("DOMContentLoaded", async () => {
  attachDecisionHandlers();
  try {
    await loadDecisionsTable();
  } catch (err) {
    alert(`Failed to initialize decisions dashboard: ${err.message}`);
  }
});