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

function loadingPanelMarkup(label = "Loading...") {
  return `
    <div class="loading-state panel-loading">
      <div class="loading-spinner"></div>
      <div class="loading-text">${escapeHtml(label)}</div>
    </div>
  `;
}

function resetIntelligenceStats() {
  setTextIfPresent("ragResultsReturned", "0");
  setTextIfPresent("ragCandidatesConsidered", "0");
  setTextIfPresent("ragSourcesUsed", "0");
}

function updateIntelligenceStats({ mode, payload }) {
  if (!payload || typeof payload !== "object") {
    resetIntelligenceStats();
    return;
  }

  if (mode === "search") {
    const resultCount = payload.result_count ?? 0;
    setTextIfPresent("ragResultsReturned", resultCount);
    setTextIfPresent("ragCandidatesConsidered", resultCount);
    setTextIfPresent("ragSourcesUsed", 0);
    return;
  }

  const response = payload.response || {};
  setTextIfPresent("ragResultsReturned", response.source_count ?? 0);
  setTextIfPresent("ragCandidatesConsidered", response.retrieved_count ?? 0);
  setTextIfPresent("ragSourcesUsed", response.source_count ?? 0);
}

function titleCase(value) {
  const text = String(value || "").trim().toLowerCase();
  if (!text) return "";
  return text.charAt(0).toUpperCase() + text.slice(1);
}

function getProviderLogoUrl(provider) {
  const normalized = String(provider || "").trim().toLowerCase();
  if (normalized === "groq") return "/static/provider_logos/groq_ai.png";
  if (normalized === "gemini") return "/static/provider_logos/gemini.png";
  return "";
}

function buildRetrievalChips(retrievalLanes) {
  const lanes = Array.isArray(retrievalLanes) ? retrievalLanes : [];
  if (!lanes.length) {
    return `<span class="summary-chip chip-muted">No retrieval lane</span>`;
  }

  return lanes
    .map((lane) => {
      const normalized = String(lane || "").trim().toLowerCase();
      const label = titleCase(normalized);
      return `<span class="summary-chip retrieval-chip retrieval-${escapeHtml(normalized)}">${escapeHtml(label)}</span>`;
    })
    .join("");
}

function buildProviderBadge(provider, model, fallbackUsed) {
  const normalized = String(provider || "").trim().toLowerCase();
  if (!normalized) {
    return `<span class="summary-chip chip-muted">LLM not invoked</span>`;
  }

  const logoUrl = getProviderLogoUrl(normalized);
  const providerLabel = titleCase(normalized);
  const fallbackHtml = fallbackUsed
    ? `<span class="summary-chip chip-small chip-muted">Fallback</span>`
    : "";

  const logoHtml = logoUrl
    ? `<img class="provider-logo" src="${logoUrl}" alt="${escapeHtml(providerLabel)} logo" title="${escapeHtml(providerLabel)}" />`
    : `<span class="provider-name">${escapeHtml(providerLabel)}</span>`;

  return `
    <span class="summary-powered-label">Powered by</span>
    <span class="summary-chip provider-chip provider-chip-logo-only">
      ${logoHtml}
    </span>
    ${model ? `<span class="summary-model-text">${escapeHtml(model)}</span>` : ""}
    ${fallbackHtml}
  `;
}

function buildAnswerMetaHtml(
  sourceCount,
  retrievalLanes,
  llmProvider,
  llmModel,
  llmFallbackUsed
) {
  return `
    <div class="summary-meta-wrap">
      <span class="summary-meta-text">Answer mode</span>
      <span class="summary-meta-sep">•</span>
      <span class="summary-meta-text">${escapeHtml(String(sourceCount || 0))} source${sourceCount === 1 ? "" : "s"}</span>
      <span class="summary-meta-sep">•</span>
      <div class="summary-chip-row">
        ${buildRetrievalChips(retrievalLanes)}
      </div>
      <span class="summary-meta-sep">•</span>
      <div class="summary-chip-row">
        ${buildProviderBadge(llmProvider, llmModel, llmFallbackUsed)}
      </div>
    </div>
  `;
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
      data-job-doc-id="${escapeHtml(row.job_doc_id || row.doc_id || "")}"
      data-job-url="${escapeHtml(row.job_url || row.doc_id || "")}"
      data-job-company="${escapeHtml(row.job_company || row.company || "")}"
      data-job-title="${escapeHtml(row.job_title || row.title || "")}"
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
  await runRag();
}

async function handleApplyClick(button) {
  const payload = {
    job_doc_id: button.dataset.jobDocId || "",
    job_url: button.dataset.jobUrl || "",
    job_company: button.dataset.jobCompany || "",
    job_title: button.dataset.jobTitle || "",
    source_view: "intelligence",
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

function renderJobEvidence(jobEvidence) {
  const rows = Array.isArray(jobEvidence) ? jobEvidence : [];

  if (!rows.length) {
    return `
      <div class="evidence-section">
        <div class="evidence-section-label">Evidence by Job</div>
        <div class="evidence-scroll">
          <div class="empty-state">No structured evidence was returned for this answer.</div>
        </div>
      </div>
    `;
  }

  return `
    <div class="evidence-section">
      <div class="evidence-section-label">Evidence by Job</div>
      <div class="evidence-scroll">
        ${rows.map((row) => {
          const sourceId = escapeHtml(row.source_id || "");
          const title = escapeHtml(row.title || "");
          const company = escapeHtml(row.company || "");
          const jobUrl = escapeHtml(row.job_url || "");
          const titleHtml = jobUrl
            ? `<a class="job-link" href="${jobUrl}" target="_blank" rel="noopener noreferrer">${title}</a>`
            : title;

          const bullets = Array.isArray(row.evidence_points) ? row.evidence_points : [];
          const bulletsHtml = bullets.length
            ? `
              <ul class="evidence-list">
                ${bullets.map((point) => `<li>${escapeHtml(point)}</li>`).join("")}
              </ul>
            `
            : `<div class="evidence-empty">No structured evidence returned for this job.</div>`;

          return `
            <div class="evidence-card">
              <div class="evidence-card-header">
                <div class="evidence-source-badge">${sourceId}</div>
                <div class="evidence-heading">
                  <div class="evidence-title">${titleHtml}</div>
                  <div class="evidence-company">${company}</div>
                </div>
              </div>
              ${bulletsHtml}
            </div>
          `;
        }).join("")}
      </div>
    </div>
  `;
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

    meta.innerHTML = `
      <div class="summary-meta-wrap">
        <span class="summary-meta-text">Search mode</span>
        <span class="summary-meta-sep">•</span>
        <span class="summary-meta-text">${escapeHtml(String(count))} result${count === 1 ? "" : "s"}</span>
      </div>
    `;

    summary.innerHTML = `
      <div class="info-pair"><span class="label">Request</span><span>${escapeHtml(payload.request || "")}</span></div>
      <div class="info-pair"><span class="label">Mode</span><span>${escapeHtml(payload.mode || "search_lite")}</span></div>
      <div class="info-pair"><span class="label">Result Count</span><span>${escapeHtml(String(count))}</span></div>
      <div class="info-pair"><span class="label">Inferred Filters</span><span>${escapeHtml(JSON.stringify(inferredFilters))}</span></div>
    `;
    return;
  }

  const response = payload.response || {};
  const retrievedCount = response.retrieved_count ?? "";
  const sourceCount = response.source_count ?? "";
  const insufficient = response.insufficient_evidence ?? "";
  const retrievalLanes = Array.isArray(response.retrieval_lanes_used)
    ? response.retrieval_lanes_used
    : [];
  const jobEvidence = Array.isArray(response.job_evidence)
    ? response.job_evidence
    : [];
  const llmProvider = response.llm_provider || "";
  const llmModel = response.llm_model || "";
  const llmFallbackUsed = Boolean(response.llm_fallback_used);

  meta.innerHTML = buildAnswerMetaHtml(
    sourceCount,
    retrievalLanes,
    llmProvider,
    llmModel,
    llmFallbackUsed
  );

  summary.innerHTML = `
    <div class="info-pair"><span class="label">Question</span><span>${escapeHtml(response.question || payload.request || "")}</span></div>
    <div class="info-pair"><span class="label">Jobs Considered</span><span>${escapeHtml(String(retrievedCount))}</span></div>
    <div class="info-pair"><span class="label">Sources Used in Answer</span><span>${escapeHtml(String(sourceCount))}</span></div>
    <div class="info-pair"><span class="label">Insufficient Evidence</span><span>${escapeHtml(insufficient ? "Yes" : "No")}</span></div>
    ${renderJobEvidence(jobEvidence)}
  `;
}

function renderSearchResults(results) {
  const container = qs("ragResults");
  const rows = Array.isArray(results) ? results : [];

  if (!rows.length) {
    container.innerHTML = `<div class="empty-state">No search results returned.</div>`;
    return;
  }

  container.innerHTML = rows
    .map((row, idx) => {
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
            <div class="result-actions">
              ${buildApplicationButtonHtml(row)}
            </div>
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
    })
    .join("");
}

function renderAnswerSources(sources) {
  const container = qs("ragResults");
  const rows = Array.isArray(sources) ? sources : [];

  if (!rows.length) {
    container.innerHTML = `<div class="empty-state">No sources returned.</div>`;
    return;
  }

  container.innerHTML = rows
    .map((row, idx) => {
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
            <div class="result-actions">
              ${buildApplicationButtonHtml(row)}
            </div>
          </div>
          <div class="result-meta">
            <span>${escapeHtml(row.source_id || "")}</span>
            <span>${escapeHtml(row.company || "")}</span>
          </div>
        </div>
      `;
    })
    .join("");
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
  summary.innerHTML = loadingPanelMarkup("Running request...");
  results.innerHTML = loadingPanelMarkup("Loading results...");

  try {
    const url = buildRagUrl();
    const payload = await fetchJson(url);

    updateIntelligenceStats({ mode, payload });
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
  resetIntelligenceStats();
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

  qs("ragResults").addEventListener("click", async (event) => {
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

window.addEventListener("DOMContentLoaded", () => {
  attachRagHandlers();
  resetIntelligenceStats();
});