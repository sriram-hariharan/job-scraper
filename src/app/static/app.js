const state = {
  currentMode: "browse",
  workflowView: null,
};

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

function renderStats(statusData) {
  const summary = statusData.summary || {};
  const undecided = statusData.undecided_review_counts || {};

  qs("statQueueRows").textContent = summary.execution_queue_rows ?? "-";
  qs("statDecisionRows").textContent = summary.operator_decisions_rows ?? "-";
  qs("statUndecidedApplyReview").textContent = undecided.APPLY_REVIEW_VARIANTS ?? 0;
  qs("statUndecidedMaybeTailor").textContent = undecided.MAYBE_TAILOR ?? 0;
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
    </tr>
  `;
}

function renderQueueRows(rows, metaLabel) {
  const tbody = qs("queueTableBody");
  const safeRows = Array.isArray(rows) ? rows : [];

  if (!safeRows.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="12" class="empty-state">No rows found.</td>
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

function clearFilters() {
  qs("actionFilter").value = "";
  qs("undecidedOnly").checked = false;
  qs("limitInput").value = "25";
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
      if (state.currentMode === "workflow" && state.workflowView) {
        await loadWorkflow(state.workflowView);
      } else {
        await loadBrowse();
      }
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
  try {
    await loadStatus();
    await loadBrowse();
  } catch (err) {
    alert(`Failed to initialize dashboard: ${err.message}`);
  }
}

window.addEventListener("DOMContentLoaded", init);