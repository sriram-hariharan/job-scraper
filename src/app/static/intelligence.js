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

function buildRagUrl() {
  const request = qs("ragRequestInput").value.trim();
  const mode = qs("ragModeSelect").value;
  const topK = qs("ragTopKInput").value || "5";
  const fetchK = qs("ragFetchKInput").value || "15";
  const includeDiagnostics = qs("ragDiagnosticsCheckbox").checked ? "true" : "false";

  if (!request) {
    throw new Error("Request is required.");
  }

  const params = new URLSearchParams({
    request,
    top_k: topK,
    fetch_k: fetchK,
    include_diagnostics: includeDiagnostics,
  });

    if (mode === "search") {
    const liteParams = new URLSearchParams({
      request,
      top_k: topK,
    });
    return `/jobs/search-lite?${liteParams.toString()}`;
    }

    return `/rag/answer?${params.toString()}`;
}

function renderSummary(payload, mode) {
  const summary = qs("ragSummary");
  const meta = qs("ragMeta");

  if (!payload || typeof payload !== "object") {
    summary.innerHTML = `<div class="empty-state">No response.</div>`;
    meta.textContent = "No response";
    return;
  }

  if (mode === "search") {
    const count = payload.result_count ?? 0;
    const inferredFilters = payload.inferred_filters || {};
    meta.textContent = `Search mode · ${count} result${count === 1 ? "" : "s"}`;
    summary.innerHTML = `
      <div class="info-pair"><span class="label">Request</span><span>${escapeHtml(payload.request || "")}</span></div>
      <div class="info-pair"><span class="label">Mode</span><span>${escapeHtml(payload.mode || "search_lite")}</span></div>
      <div class="info-pair"><span class="label">Result Count</span><span>${escapeHtml(String(count))}</span></div>
      <div class="info-pair"><span class="label">Inferred Filters</span><span>${escapeHtml(JSON.stringify(inferredFilters))}</span></div>
    `;
    return;
  }

  const response = payload.response || {};
  const answer = response.answer || "";
  const retrievedCount = response.retrieved_count ?? "";
  const sourceCount = response.source_count ?? "";
  const insufficient = response.insufficient_evidence ?? "";

  meta.textContent = `Answer mode · ${sourceCount || 0} source${sourceCount === 1 ? "" : "s"}`;
  summary.innerHTML = `
    <div class="info-pair"><span class="label">Question</span><span>${escapeHtml(response.question || payload.request || "")}</span></div>
    <div class="info-pair"><span class="label">Retrieved Count</span><span>${escapeHtml(String(retrievedCount))}</span></div>
    <div class="info-pair"><span class="label">Source Count</span><span>${escapeHtml(String(sourceCount))}</span></div>
    <div class="info-pair"><span class="label">Insufficient Evidence</span><span>${escapeHtml(String(insufficient || "false"))}</span></div>
    <div class="answer-block">${escapeHtml(answer)}</div>
  `;
}

function renderSearchResults(results) {
  const container = qs("ragResults");
  const rows = Array.isArray(results) ? results : [];

  if (!rows.length) {
    container.innerHTML = `<div class="empty-state">No search results returned.</div>`;
    return;
  }

  container.innerHTML = rows.map((row, idx) => {
    const title = escapeHtml(row.title || "");
    const jobUrl = escapeHtml(row.job_url || row.doc_id || "");
    const titleHtml = jobUrl
      ? `<a class="job-link" href="${jobUrl}" target="_blank" rel="noopener noreferrer">${title}</a>`
      : title;

    return `
      <div class="result-card">
        <div class="result-header">
          <div class="result-index">#${idx + 1}</div>
          <div class="result-title">${titleHtml}</div>
        </div>
        <div class="result-meta">
          <span>${escapeHtml(row.company || "")}</span>
          <span>score=${escapeHtml(String(row.score ?? ""))}</span>
          <span>${escapeHtml(row.location || "")}</span>
        </div>
        <div class="result-meta">
          <span>source=${escapeHtml(row.source || "")}</span>
          <span>posted_at=${escapeHtml(row.posted_at || "")}</span>
          <span>visa=${escapeHtml(row.visa_sponsorship || "")}</span>
          <span>ai_fit=${escapeHtml(String(row.ai_fit_score ?? ""))}</span>
        </div>
      </div>
    `;
  }).join("");
}

function renderAnswerSources(sources) {
  const container = qs("ragResults");
  const rows = Array.isArray(sources) ? sources : [];

  if (!rows.length) {
    container.innerHTML = `<div class="empty-state">No sources returned.</div>`;
    return;
  }

  container.innerHTML = rows.map((row, idx) => {
    const title = escapeHtml(row.title || "");
    const jobUrl = escapeHtml(row.job_url || "");
    const titleHtml = jobUrl
      ? `<a class="job-link" href="${jobUrl}" target="_blank" rel="noopener noreferrer">${title}</a>`
      : title;

    return `
      <div class="result-card">
        <div class="result-header">
          <div class="result-index">#${idx + 1}</div>
          <div class="result-title">${titleHtml}</div>
        </div>
        <div class="result-meta">
          <span>${escapeHtml(row.source_id || "")}</span>
          <span>${escapeHtml(row.company || "")}</span>
        </div>
      </div>
    `;
  }).join("");
}

async function runRag() {
  const mode = qs("ragModeSelect").value;
  const runBtn = qs("runRagBtn");
  const summary = qs("ragSummary");
  const results = qs("ragResults");
  const meta = qs("ragMeta");

  runBtn.disabled = true;
  runBtn.textContent = "Running...";
  meta.textContent = "Running...";
  summary.innerHTML = `<div class="empty-state">Running request...</div>`;
  results.innerHTML = `<div class="empty-state">Loading results...</div>`;

  try {
    const url = buildRagUrl();
    const payload = await fetchJson(url);

    renderSummary(payload, mode);

    if (mode === "search") {
      renderSearchResults(payload.results || []);
    } else {
      renderAnswerSources((payload.response || {}).sources || []);
    }
  } finally {
    runBtn.disabled = false;
    runBtn.textContent = "Run";
  }
}

function clearRag() {
  qs("ragRequestInput").value = "";
  qs("ragModeSelect").value = "search";
  qs("ragTopKInput").value = "5";
  qs("ragFetchKInput").value = "15";
  qs("ragDiagnosticsCheckbox").checked = false;
  qs("ragSummary").innerHTML = `<div class="empty-state">Run a search or grounded question.</div>`;
  qs("ragResults").innerHTML = `<div class="empty-state">No results yet.</div>`;
  qs("ragMeta").textContent = "Idle";
}

function attachRagHandlers() {
  qs("runRagBtn").addEventListener("click", async () => {
    try {
      await runRag();
    } catch (err) {
      alert(`Failed to run intelligence query: ${err.message}`);
    }
  });

  qs("clearRagBtn").addEventListener("click", () => {
    clearRag();
  });

  qs("ragRequestInput").addEventListener("keydown", async (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      try {
        await runRag();
      } catch (err) {
        alert(`Failed to run intelligence query: ${err.message}`);
      }
    }
  });
}

window.addEventListener("DOMContentLoaded", () => {
  attachRagHandlers();
});