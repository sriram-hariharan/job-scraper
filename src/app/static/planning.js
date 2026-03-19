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

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`HTTP ${response.status}: ${text}`);
  }
  return response.json();
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

function renderPlanningRows(rows, metaLabel) {
  const tbody = qs("planningTableBody");
  const safeRows = Array.isArray(rows) ? rows : [];

  if (!safeRows.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="18" class="empty-state">No rows found.</td>
      </tr>
    `;
    qs("planningTableMeta").textContent = metaLabel;
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
      </tr>
    `;
  }).join("");

  qs("planningTableMeta").textContent = metaLabel;
}

async function loadPlanningTable() {
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
}

window.addEventListener("DOMContentLoaded", async () => {
  attachPlanningHandlers();
  try {
    await loadPlanningTable();
  } catch (err) {
    alert(`Failed to initialize planning dashboard: ${err.message}`);
  }
});