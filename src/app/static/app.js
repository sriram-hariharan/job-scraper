const state = {
  currentMode: "browse",
  workflowView: null,
  pendingApplicationJob: null,
  applicationModalOpen: false,
  pendingPipelineConfig: null,
};

const PENDING_APPLICATION_STORAGE_KEY = "job_operator_pending_application";
let pipelinePollTimer = null;

const DEFAULT_OUTPUT_DIR = "outputs/application_planning";
const DEFAULT_STAGE_ORDER = [
  "startup",
  "scraping",
  "filtering",
  "dedupe",
  "ranking",
  "cache_filter",
  "details",
  "intelligence",
  "ai_evaluation_filter",
  "embedding_prefilter",
  "ai_evaluation",
  "resume_matching",
  "application_priority",
  "rag_export",
  "planning",
  "sheet_export",
  "finalization",
];

const STAGE_LABELS = {
  startup: "Startup",
  scraping: "Scraping",
  filtering: "Filtering",
  dedupe: "Dedupe",
  ranking: "Ranking",
  cache_filter: "Cache Filter",
  details: "Details",
  intelligence: "Intelligence",
  ai_evaluation_filter: "AI Eval Filter",
  embedding_prefilter: "Embedding Prefilter",
  ai_evaluation: "AI Evaluation",
  resume_matching: "Resume Matching",
  application_priority: "Application Priority",
  rag_export: "RAG Export",
  planning: "Planning",
  sheet_export: "Sheet Export",
  finalization: "Finalization",
};

const COUNT_LABELS = {
  scraped_jobs: "Scraped",
  filtered_jobs: "Filtered",
  deduped_jobs: "Deduped",
  ranked_jobs: "Ranked",
  new_jobs: "New",
  detailed_jobs: "Detailed",
  intelligent_jobs: "Intelligence",
  evaluable_jobs: "AI Eligible",
  prefilter_jobs: "Prefilter",
  ai_jobs: "AI Evaluated",
  resume_matched_jobs: "Resume Matched",
  scored_jobs: "Scored",
  rag_export_count: "RAG Exported",
  final_jobs: "Final Jobs",
};

const PIPELINE_PRESETS = {
  full: {
    job_limit: 50,
    job_packet_limit: 0,
    output_dir: DEFAULT_OUTPUT_DIR,
    llm_actions: ["APPLY", "APPLY_REVIEW_VARIANTS"],
    planning_only: false,
    generate_tailoring: false,
    generate_llm_tailoring: false,
    refresh_llm_tailoring: false,
    generate_llm_fallback: false,
    delete_seen_data: false,
  },
  planning_only: {
    job_limit: 50,
    job_packet_limit: 0,
    output_dir: DEFAULT_OUTPUT_DIR,
    llm_actions: ["APPLY", "APPLY_REVIEW_VARIANTS"],
    planning_only: true,
    generate_tailoring: false,
    generate_llm_tailoring: false,
    refresh_llm_tailoring: false,
    generate_llm_fallback: false,
    delete_seen_data: false,
  },
  tailoring_refresh: {
    job_limit: 50,
    job_packet_limit: 0,
    output_dir: DEFAULT_OUTPUT_DIR,
    llm_actions: ["APPLY", "APPLY_REVIEW_VARIANTS", "MAYBE_TAILOR"],
    planning_only: true,
    generate_tailoring: false,
    generate_llm_tailoring: true,
    refresh_llm_tailoring: true,
    generate_llm_fallback: false,
    delete_seen_data: false,
  },
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

function formatDateTime(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

function titleCaseStage(stage) {
  return STAGE_LABELS[stage] || String(stage || "")
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function normalizeOutputDir(value) {
  const raw = String(value || "").trim() || DEFAULT_OUTPUT_DIR;
  return raw.replace(/\/+$/, "") || DEFAULT_OUTPUT_DIR;
}

function derivePipelinePaths(outputDir) {
  const normalized = normalizeOutputDir(outputDir);
  return {
    output_dir: normalized,
    log_path: `${normalized}/live_pipeline_run.log`,
    status_path: `${normalized}/live_pipeline_status.json`,
  };
}

function syncPipelinePathPreview() {
  const paths = derivePipelinePaths(qs("pipelineOutputDirInput").value);
  const logPreview = qs("pipelineLogPathPreview");
  const statusPreview = qs("pipelineStatusPathPreview");

  logPreview.textContent = paths.log_path;
  logPreview.title = paths.log_path;

  statusPreview.textContent = paths.status_path;
  statusPreview.title = paths.status_path;
}

function setPipelineLlmActions(actions) {
  const selected = new Set(actions || []);
  document.querySelectorAll("[data-pipeline-llm-action]").forEach((el) => {
    el.checked = selected.has(el.value);
  });
}

function getSelectedPipelineLlmActions() {
  return Array.from(document.querySelectorAll("[data-pipeline-llm-action]:checked"))
    .map((el) => el.value)
    .filter(Boolean);
}

function getPipelineDeleteSeenDataValue() {
  return document.querySelector("input[name='pipelineDeleteSeenData']:checked")?.value || "no";
}

function applyPipelinePreset(name) {
  const preset = PIPELINE_PRESETS[name];
  if (!preset) return;

  qs("pipelineJobLimitInput").value = preset.job_limit;
  qs("pipelineJobPacketLimitInput").value = preset.job_packet_limit;
  qs("pipelineOutputDirInput").value = preset.output_dir;
  qs("pipelinePlanningOnlyCheckbox").checked = preset.planning_only;
  qs("pipelineGenerateTailoringCheckbox").checked = preset.generate_tailoring;
  qs("pipelineGenerateLlmTailoringCheckbox").checked = preset.generate_llm_tailoring;
  qs("pipelineRefreshLlmTailoringCheckbox").checked = preset.refresh_llm_tailoring;
  qs("pipelineGenerateLlmFallbackCheckbox").checked = preset.generate_llm_fallback;
  qs("pipelineDeleteSeenDataCheckbox").checked = preset.delete_seen_data;
  setPipelineLlmActions(preset.llm_actions);
  syncPipelinePathPreview();
}

function renderStats(statusData) {
  const summary = statusData.summary || {};
  const undecided = statusData.undecided_review_counts || {};

  qs("statQueueRows").textContent = summary.execution_queue_rows ?? "-";
  qs("statDecisionRows").textContent = summary.operator_decisions_rows ?? "-";
  qs("statUndecidedApplyReview").textContent = undecided.APPLY_REVIEW_VARIANTS ?? 0;
  qs("statUndecidedMaybeTailor").textContent = undecided.MAYBE_TAILOR ?? 0;
}

function buildPipelineMetaText(pipeline) {
  const status = pipeline.status || "idle";
  const currentStage = titleCaseStage(pipeline.current_stage);
  const stageMessage = pipeline.stage_message || "";
  const summaryMessage = pipeline.summary_message || "";
  const startedAt = formatDateTime(pipeline.started_at);
  const finishedAt = formatDateTime(pipeline.finished_at);

  if (status === "running") {
    if (currentStage && stageMessage) {
      return `Pipeline running · ${currentStage} · ${stageMessage}`;
    }
    if (currentStage) {
      return `Pipeline running · ${currentStage}`;
    }
    return startedAt ? `Pipeline running since ${startedAt}` : "Pipeline running.";
  }

  if (status === "succeeded") {
    return summaryMessage
      ? `${summaryMessage}${finishedAt ? ` · finished ${finishedAt}` : ""}`
      : `Pipeline finished successfully${finishedAt ? ` at ${finishedAt}` : ""}.`;
  }

  if (status === "failed") {
    const errorText = pipeline.error ? ` · ${pipeline.error}` : "";
    return `Pipeline failed${finishedAt ? ` at ${finishedAt}` : ""}${errorText}`;
  }

  return "Pipeline idle.";
}

function renderPipelineCounts(pipeline) {
  const counts = pipeline.counts || {};
  const entries = Object.entries(COUNT_LABELS)
    .map(([key, label]) => {
      const value = counts[key];
      if (value === undefined || value === null) return "";
      return `<div class="pipeline-count-chip"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`;
    })
    .filter(Boolean);

  qs("pipelineLoadingCounts").innerHTML = entries.length
    ? entries.join("")
    : `<div class="pipeline-count-empty">No stage counts yet.</div>`;
}

function renderPipelineStageStepper(pipeline) {
  const order = Array.isArray(pipeline.stage_order) && pipeline.stage_order.length
    ? pipeline.stage_order
    : DEFAULT_STAGE_ORDER;

  const completed = new Set(Array.isArray(pipeline.completed_stages) ? pipeline.completed_stages : []);
  const current = pipeline.current_stage || "";
  const status = pipeline.status || "idle";

  const html = order.map((stage) => {
    let stateClass = "pending";
    let marker = "○";

    if (completed.has(stage)) {
      stateClass = "complete";
      marker = "✓";
    } else if (status === "running" && current === stage) {
      stateClass = "current";
      marker = "•";
    } else if (status === "failed" && current === stage) {
      stateClass = "failed";
      marker = "!";
    }

    return `
      <div class="pipeline-step pipeline-step--${stateClass}">
        <div class="pipeline-step-marker">${escapeHtml(marker)}</div>
        <div class="pipeline-step-label">${escapeHtml(titleCaseStage(stage))}</div>
      </div>
    `;
  }).join("");

  qs("pipelineStageStepper").innerHTML = html;
}

function showPageLoadingOverlay(title, text, pipeline = {}) {
  const overlay = qs("pageLoadingOverlay");
  qs("pageLoadingTitle").textContent = title || "Running live pipeline...";
  qs("pageLoadingText").textContent = text || "Preparing pipeline run.";
  qs("pipelineLoadingMeta").textContent = buildPipelineMetaText(pipeline);
  renderPipelineCounts(pipeline);
  renderPipelineStageStepper(pipeline);
  overlay.classList.remove("hidden");
}

function hidePageLoadingOverlay() {
  qs("pageLoadingOverlay").classList.add("hidden");
}

function renderPipelineStatus(payload) {
  const pipeline = (payload && payload.pipeline) || {};
  const runBtn = qs("runPipelineBtn");
  const meta = qs("pipelineRunMeta");

  if (!runBtn || !meta) return;

  const status = pipeline.status || "idle";
  meta.textContent = buildPipelineMetaText(pipeline);

  if (status === "running") {
    runBtn.disabled = true;
    runBtn.textContent = "Pipeline Running...";
    showPageLoadingOverlay(
      `Running · ${titleCaseStage(pipeline.current_stage || "startup")}`,
      pipeline.stage_message || "Pipeline is running.",
      pipeline
    );
    return;
  }

  runBtn.disabled = false;
  runBtn.textContent = "Run Live Pipeline";
  hidePageLoadingOverlay();
}

async function loadPipelineStatus() {
  const data = await fetchJson("/pipeline/status");
  renderPipelineStatus(data);
  return data;
}

function getPipelineConfigModal() {
  return qs("pipelineConfigModal");
}

function getPipelineConfirmModal() {
  return qs("pipelineConfirmModal");
}

function openPipelineConfigModal() {
  syncPipelinePathPreview();
  getPipelineConfigModal().classList.remove("hidden");
}

function closePipelineConfigModal() {
  getPipelineConfigModal().classList.add("hidden");
}

function openPipelineConfirmModal() {
  getPipelineConfirmModal().classList.remove("hidden");
}

function closePipelineConfirmModal() {
  getPipelineConfirmModal().classList.add("hidden");
}

function collectPipelineConfig() {
  const llmActions = getSelectedPipelineLlmActions();
  if (!llmActions.length) {
    throw new Error("Select at least one LLM action.");
  }

  return {
    job_limit: Number(qs("pipelineJobLimitInput").value || 50),
    job_packet_limit: Number(qs("pipelineJobPacketLimitInput").value || 0),
    output_dir: qs("pipelineOutputDirInput").value.trim() || "outputs/application_planning",
    log_path: qs("pipelineLogPathInput").value.trim() || "outputs/application_planning/live_pipeline_run.log",
    llm_actions: llmActions,
    planning_only: qs("pipelinePlanningOnlyCheckbox").checked,
    generate_tailoring: qs("pipelineGenerateTailoringCheckbox").checked,
    generate_llm_tailoring: qs("pipelineGenerateLlmTailoringCheckbox").checked,
    refresh_llm_tailoring: qs("pipelineRefreshLlmTailoringCheckbox").checked,
    generate_llm_fallback: qs("pipelineGenerateLlmFallbackCheckbox").checked,
    delete_seen_data: getPipelineDeleteSeenDataValue(),
  };
}

function renderPipelineConfirmSummary(config) {
  const lines = [
    `Job limit: ${config.job_limit}`,
    `Job packet limit: ${config.job_packet_limit}`,
    `Output directory: ${config.output_dir}`,
    `Log path: ${config.log_path}`,
    `LLM actions: ${config.llm_actions.join(", ")}`,
    `Planning only: ${config.planning_only ? "Yes" : "No"}`,
    `Generate tailoring: ${config.generate_tailoring ? "Yes" : "No"}`,
    `Generate LLM tailoring: ${config.generate_llm_tailoring ? "Yes" : "No"}`,
    `Refresh LLM tailoring: ${config.refresh_llm_tailoring ? "Yes" : "No"}`,
    `Generate LLM fallback: ${config.generate_llm_fallback ? "Yes" : "No"}`,
    `Delete seen data: ${config.delete_seen_data === "yes" ? "Yes" : "No"}`,
  ];

  qs("pipelineConfirmSummary").innerHTML = lines
    .map((line) => `<div class="confirm-summary-line">${escapeHtml(line)}</div>`)
    .join("");
}

function stopPipelinePolling() {
  if (pipelinePollTimer) {
    clearInterval(pipelinePollTimer);
    pipelinePollTimer = null;
  }
}

function startPipelinePolling() {
  stopPipelinePolling();

  pipelinePollTimer = setInterval(async () => {
    try {
      const data = await loadPipelineStatus();
      if (!data.pipeline || !data.pipeline.is_running) {
        stopPipelinePolling();
        await loadStatus();
        await reloadCurrentTable();
      }
    } catch (err) {
      stopPipelinePolling();
      console.error(err);
    }
  }, 2000);
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

  qs("runPipelineBtn").addEventListener("click", () => {
    openPipelineConfigModal();
  });

  qs("closePipelineConfigModalBtn").addEventListener("click", closePipelineConfigModal);
  qs("cancelPipelineConfigBtn").addEventListener("click", closePipelineConfigModal);

  qs("openPipelineConfirmBtn").addEventListener("click", () => {
    try {
      const config = collectPipelineConfig();
      state.pendingPipelineConfig = config;
      renderPipelineConfirmSummary(config);
      closePipelineConfigModal();
      openPipelineConfirmModal();
    } catch (err) {
      alert(`Invalid pipeline configuration: ${err.message}`);
    }
  });

  qs("closePipelineConfirmModalBtn").addEventListener("click", closePipelineConfirmModal);

  qs("backToPipelineConfigBtn").addEventListener("click", () => {
    closePipelineConfirmModal();
    openPipelineConfigModal();
  });

  qs("confirmPipelineRunBtn").addEventListener("click", async () => {
    try {
      const config = state.pendingPipelineConfig || collectPipelineConfig();
      closePipelineConfirmModal();
      showPageLoadingOverlay("Running live pipeline...", "Starting pipeline run...", {
        status: "running",
        current_stage: "startup",
        stage_message: "Launching pipeline subprocess",
        stage_order: DEFAULT_STAGE_ORDER,
        completed_stages: [],
        counts: {},
      });
      await postJson("/pipeline/run", config);
      await loadPipelineStatus();
      startPipelinePolling();
    } catch (err) {
      hidePageLoadingOverlay();
      alert(`Failed to start live pipeline: ${err.message}`);
    }
  });

  getApplicationModal().addEventListener("click", (event) => {
    if (event.target === getApplicationModal()) {
      clearPendingApplication();
      closeApplicationModal();
    }
  });

  getPipelineConfigModal().addEventListener("click", (event) => {
    if (event.target === getPipelineConfigModal()) {
      closePipelineConfigModal();
    }
  });

  getPipelineConfirmModal().addEventListener("click", (event) => {
    if (event.target === getPipelineConfirmModal()) {
      closePipelineConfirmModal();
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

function attachPipelineConfigHandlers() {
  qs("pipelineOutputDirInput").addEventListener("input", syncPipelinePathPreview);

  qs("pipelineSelectAllActionsBtn").addEventListener("click", () => {
    setPipelineLlmActions(["APPLY", "APPLY_REVIEW_VARIANTS", "MAYBE_TAILOR", "SKIP_FOR_NOW"]);
  });

  qs("pipelineClearAllActionsBtn").addEventListener("click", () => {
    setPipelineLlmActions([]);
  });

  document.querySelectorAll("[data-pipeline-preset]").forEach((btn) => {
    btn.addEventListener("click", () => {
      applyPipelinePreset(btn.dataset.pipelinePreset);
    });
  });

  document.querySelectorAll("[data-job-limit-preset]").forEach((btn) => {
    btn.addEventListener("click", () => {
      qs("pipelineJobLimitInput").value = btn.dataset.jobLimitPreset || "50";
    });
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
      await loadPipelineStatus();
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
  attachPipelineConfigHandlers();
  applyPipelinePreset("full");
  syncPipelinePathPreview();

  try {
    await loadStatus();
    await loadPipelineStatus();
    await loadBrowse();

    const pipelineData = await fetchJson("/pipeline/status");
    if (pipelineData.pipeline && pipelineData.pipeline.is_running) {
      startPipelinePolling();
    }
  } catch (err) {
    alert(`Failed to initialize dashboard: ${err.message}`);
  }
}

window.addEventListener("DOMContentLoaded", init);