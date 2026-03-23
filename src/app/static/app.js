const state = {
  currentMode: "browse",
  workflowView: null,
  executiveViewMode: "detailed",
  pendingApplicationJob: null,
  applicationModalOpen: false,
  pendingPipelineConfig: null,
  pipelineSuccessVisible: false,
  currentPipelineSuccessKey: null,
  acknowledgedPipelineSuccessKey: null,
};

const queueTableState = {
  rows: [],
  metaLabel: "Loading...",
  sort: {
    key: "",
    direction: "asc",
  },
};

const PENDING_APPLICATION_STORAGE_KEY = "job_operator_pending_application";
const PIPELINE_PENDING_SUCCESS_KEY = "job_operator_pipeline_pending_success";
const PIPELINE_SHOWN_SUCCESS_KEY = "job_operator_pipeline_shown_success";
const EXECUTIVE_VIEW_MODE_STORAGE_KEY = "job_operator_executive_view_mode";
let pipelinePollTimer = null;
let pipelineSuccessGifTimer = null;

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

const QUEUE_SORT_COLUMNS = [
  { key: "queue_rank", label: "Queue Rank", type: "number" },
  { key: "action", label: "Action", type: "text" },
  { key: "job_company", label: "Company", type: "text" },
  { key: "job_title", label: "Title", type: "text" },
  { key: "posted_at", label: "Posted At", type: "date" },
  { key: "winner_resume", label: "Winner Resume", type: "text" },
  { key: "winner_score", label: "Winner Score", type: "number" },
  { key: "runner_up_resume", label: "Runner-Up Resume", type: "text" },
  { key: "score_gap", label: "Score Gap", type: "number" },
  { key: "missing_requirement_count", label: "Missing Req Count", type: "number" },
  { key: "operator_decision", label: "Operator Decision", type: "text" },
  { key: "operator_selected_resume", label: "Selected Resume", type: "text" },
  { key: "queue_priority_reason", label: "Priority Reason", type: "text" },
  { key: "apply", label: "Apply", sortable: false },
];

const PIPELINE_PRESETS = {
  full: {
    job_limit: 50,
    job_packet_limit: 0,
    output_dir: DEFAULT_OUTPUT_DIR,
    llm_actions: [],
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
    llm_actions: [],
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
    llm_actions: ["MAYBE_TAILOR"],
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

function normalizeSortValue(value, type = "text") {
  if (value === null || value === undefined) return null;

  if (type === "number") {
    const parsed = Number(String(value).replaceAll(",", "").trim());
    return Number.isFinite(parsed) ? parsed : null;
  }

  if (type === "date") {
    const parsed = new Date(value).getTime();
    return Number.isFinite(parsed) ? parsed : null;
  }

  if (type === "boolean") {
    if (value === true) return 1;
    if (value === false) return 0;

    const normalized = String(value).trim().toLowerCase();
    if (["true", "yes", "1"].includes(normalized)) return 1;
    if (["false", "no", "0"].includes(normalized)) return 0;
    return null;
  }

  return String(value).trim().toLowerCase();
}

function compareSortValues(left, right) {
  if (left === right) return 0;
  if (left === null || left === "") return 1;
  if (right === null || right === "") return -1;
  if (left < right) return -1;
  if (left > right) return 1;
  return 0;
}

function sortRows(rows, columns, sortState) {
  const safeRows = Array.isArray(rows) ? rows.slice() : [];
  if (!sortState.key) return safeRows;

  const column = columns.find((item) => item.key === sortState.key && item.sortable !== false);
  if (!column) return safeRows;

  const direction = sortState.direction === "desc" ? -1 : 1;
  const getValue = column.getValue || ((row) => row[column.key]);
  const type = column.type || "text";

  return safeRows
    .map((row, index) => ({ row, index }))
    .sort((a, b) => {
      const cmp = compareSortValues(
        normalizeSortValue(getValue(a.row), type),
        normalizeSortValue(getValue(b.row), type)
      );
      return cmp === 0 ? a.index - b.index : cmp * direction;
    })
    .map((item) => item.row);
}

function getSortIndicator(sortState, key) {
  if (sortState.key !== key) return "↕";
  return sortState.direction === "desc" ? "↓" : "↑";
}

function renderSortableHeaders(tableId, columns, sortState) {
  const table = qs(tableId);
  if (!table) return;

  const cells = table.querySelectorAll("thead th");
  columns.forEach((column, index) => {
    const th = cells[index];
    if (!th) return;

    const label = column.label || th.dataset.originalLabel || th.textContent.trim();
    th.dataset.originalLabel = label;

    if (column.sortable === false) {
      th.innerHTML = escapeHtml(label);
      th.classList.remove("sortable-col");
      return;
    }

    th.classList.add("sortable-col");
    th.innerHTML = `
      <button
        type="button"
        class="sort-header-btn ${sortState.key === column.key ? "is-active" : ""}"
        data-sort-key="${escapeHtml(column.key)}"
        aria-label="Sort by ${escapeHtml(label)}"
      >
        <span class="sort-header-label">${escapeHtml(label)}</span>
        <span class="sort-header-indicator">${getSortIndicator(sortState, column.key)}</span>
      </button>
    `;
  });
}

function bindTableSorting(tableId, columns, sortState, rerender) {
  const table = qs(tableId);
  if (!table || table.dataset.sortBound === "true") return;

  table.dataset.sortBound = "true";
  renderSortableHeaders(tableId, columns, sortState);

  table.querySelector("thead").addEventListener("click", (event) => {
    const button = event.target.closest("[data-sort-key]");
    if (!button) return;

    const key = button.dataset.sortKey;
    if (!key) return;

    if (sortState.key === key) {
      sortState.direction = sortState.direction === "asc" ? "desc" : "asc";
    } else {
      sortState.key = key;
      sortState.direction = "asc";
    }

    rerender();
  });
}

function qs(id) {
  return document.getElementById(id);
}

function normalizeExecutiveViewMode(value) {
  return String(value || "").trim().toLowerCase() === "simple" ? "simple" : "detailed";
}

function loadExecutiveViewMode() {
  return normalizeExecutiveViewMode(localStorage.getItem(EXECUTIVE_VIEW_MODE_STORAGE_KEY));
}

function syncExecutiveViewModeControls() {
  const mode = normalizeExecutiveViewMode(state.executiveViewMode);
  const radio = document.querySelector(`input[name='executiveViewMode'][value='${mode}']`);
  if (radio) radio.checked = true;
}

function setExecutiveViewMode(mode) {
  state.executiveViewMode = normalizeExecutiveViewMode(mode);
  localStorage.setItem(EXECUTIVE_VIEW_MODE_STORAGE_KEY, state.executiveViewMode);
  syncExecutiveViewModeControls();
  renderQueueRows(queueTableState.rows, queueTableState.metaLabel);
}

function renderQueueHeaders() {
  const headerRow = qs("queueTableHeaderRow");
  if (!headerRow) return;

  if (state.executiveViewMode === "simple") {
    headerRow.innerHTML = `
      <th>Queue Rank</th>
      <th>Job</th>
      <th>Resume Options</th>
      <th class="sticky-apply-col">Apply</th>
    `;
    return;
  }

  headerRow.innerHTML = QUEUE_SORT_COLUMNS
    .map((column) => `<th>${escapeHtml(column.label)}</th>`)
    .join("");

  renderSortableHeaders("queueTable", QUEUE_SORT_COLUMNS, queueTableState.sort);
}

function buildResumeOptionHtml(label, resumeName, score) {
  const safeLabel = escapeHtml(label || "");
  const safeResume = escapeHtml(resumeName || "-");
  const safeScore = escapeHtml(formatScore100(score));

  return `
    <div class="resume-option-block">
      <div><strong>${safeLabel}</strong></div>
      <div>${safeResume}</div>
      <div class="subtext-inline">Score: ${safeScore}</div>
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

const DATE_TIME_FORMATTER = new Intl.DateTimeFormat(undefined, {
  month: "short",
  day: "numeric",
  year: "numeric",
  hour: "numeric",
  minute: "2-digit",
  timeZoneName: "short",
});

function formatDateTime(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return DATE_TIME_FORMATTER.format(date);
}

function formatScore100(value) {
  if (value === null || value === undefined || String(value).trim() === "") return "-";
  const parsed = Number(String(value).replaceAll(",", "").trim());
  if (!Number.isFinite(parsed)) return String(value);
  const normalized = Math.abs(parsed) <= 1 ? parsed * 100 : parsed;
  return normalized.toFixed(2);
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
  const outputDirInput = qs("pipelineOutputDirInput");
  if (!outputDirInput) return;

  const paths = derivePipelinePaths(outputDirInput.value);
  const logPreview = qs("pipelineLogPathPreview");
  const statusPreview = qs("pipelineStatusPathPreview");

  if (logPreview) {
    logPreview.textContent = paths.log_path;
    logPreview.title = paths.log_path;
  }

  if (statusPreview) {
    statusPreview.textContent = paths.status_path;
    statusPreview.title = paths.status_path;
  }
}

function normalizeBinaryToggleValue(value) {
  return value === true || value === "yes" ? "yes" : "no";
}

function getBinaryToggleValue(name) {
  return document.querySelector(`input[name='${name}']:checked`)?.value || "no";
}

function getBinaryToggleBool(name) {
  return getBinaryToggleValue(name) === "yes";
}

function setBinaryToggleValue(name, value) {
  const normalized = normalizeBinaryToggleValue(value);
  const radio = document.querySelector(`input[name='${name}'][value='${normalized}']`);
  if (radio) {
    radio.checked = true;
  }
}

function setPipelineLlmActions(actions) {
  const selected = new Set(actions || []);
  const toggleInputs = document.querySelectorAll("[data-pipeline-llm-action-toggle]");

  if (toggleInputs.length) {
    const actionNames = Array.from(
      new Set(
        Array.from(toggleInputs)
          .map((el) => el.dataset.pipelineLlmActionToggle)
          .filter(Boolean)
      )
    );

    actionNames.forEach((action) => {
      const value = selected.has(action) ? "yes" : "no";
      const radio = document.querySelector(
        `[data-pipeline-llm-action-toggle='${action}'][value='${value}']`
      );
      if (radio) {
        radio.checked = true;
      }
    });
    return;
  }

  document.querySelectorAll("[data-pipeline-llm-action]").forEach((el) => {
    el.checked = selected.has(el.value);
  });
}

function getSelectedPipelineLlmActions() {
  const toggleInputs = document.querySelectorAll("[data-pipeline-llm-action-toggle]");

  if (toggleInputs.length) {
    return Array.from(toggleInputs)
      .filter((el) => el.checked && el.value === "yes")
      .map((el) => el.dataset.pipelineLlmActionToggle)
      .filter(Boolean);
  }

  return Array.from(document.querySelectorAll("[data-pipeline-llm-action]:checked"))
    .map((el) => el.value)
    .filter(Boolean);
}

function getPipelineDeleteSeenDataValue() {
  return getBinaryToggleValue("pipelineDeleteSeenData");
}

function setPipelineDeleteSeenDataValue(value) {
  setBinaryToggleValue("pipelineDeleteSeenData", value);
}

function applyPipelinePreset(name) {
  const preset = PIPELINE_PRESETS[name];
  if (!preset) return;

  const jobLimitInput = qs("pipelineJobLimitInput");
  const jobPacketLimitInput = qs("pipelineJobPacketLimitInput");
  const outputDirInput = qs("pipelineOutputDirInput");

  if (jobLimitInput) jobLimitInput.value = preset.job_limit;
  if (jobPacketLimitInput) jobPacketLimitInput.value = preset.job_packet_limit;
  if (outputDirInput) outputDirInput.value = preset.output_dir;

  setBinaryToggleValue("pipelinePlanningOnly", preset.planning_only);
  setBinaryToggleValue("pipelineGenerateTailoring", preset.generate_tailoring);
  setBinaryToggleValue("pipelineGenerateLlmTailoring", preset.generate_llm_tailoring);
  setBinaryToggleValue("pipelineRefreshLlmTailoring", preset.refresh_llm_tailoring);
  setBinaryToggleValue("pipelineGenerateLlmFallback", preset.generate_llm_fallback);
  setPipelineDeleteSeenDataValue(preset.delete_seen_data);
  setPipelineLlmActions(preset.llm_actions || []);
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

function buildPipelineCountsHtml(pipeline) {
  const counts = pipeline.counts || {};
  const entries = Object.entries(COUNT_LABELS)
    .map(([key, label]) => {
      const value = counts[key];
      if (value === undefined || value === null) return "";
      return `<div class="pipeline-count-chip"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`;
    })
    .filter(Boolean);

  return entries.length
    ? entries.join("")
    : `<div class="pipeline-count-empty">No stage counts yet.</div>`;
}

function renderPipelineCounts(pipeline) {
  qs("pipelineLoadingCounts").innerHTML = buildPipelineCountsHtml(pipeline);
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

function getPipelineSuccessKey(pipeline = {}) {
  return pipeline.finished_at || pipeline.started_at || pipeline.status || "succeeded";
}

function markPipelinePendingSuccess() {
  sessionStorage.setItem(PIPELINE_PENDING_SUCCESS_KEY, "1");
}

function clearPipelinePendingSuccess() {
  sessionStorage.removeItem(PIPELINE_PENDING_SUCCESS_KEY);
}

function hasPipelinePendingSuccess() {
  return sessionStorage.getItem(PIPELINE_PENDING_SUCCESS_KEY) === "1";
}

function markPipelineSuccessShown(successKey) {
  if (successKey) {
    sessionStorage.setItem(PIPELINE_SHOWN_SUCCESS_KEY, successKey);
  }
}

function wasPipelineSuccessAlreadyShown(successKey) {
  if (!successKey) return false;
  return sessionStorage.getItem(PIPELINE_SHOWN_SUCCESS_KEY) === successKey;
}

function renderPipelineSuccessSummary(pipeline = {}) {
  const summaryMessage = pipeline.summary_message || "Run finished successfully.";
  const metaBits = [
    pipeline.started_at ? `Started: ${formatDateTime(pipeline.started_at)}` : "",
    pipeline.finished_at ? `Finished: ${formatDateTime(pipeline.finished_at)}` : "",
    pipeline.final_job_count !== undefined && pipeline.final_job_count !== null
      ? `Final jobs: ${pipeline.final_job_count}`
      : "",
  ].filter(Boolean);

  const metaLine = metaBits.length
    ? `<div class="pipeline-success-summary-text">${escapeHtml(metaBits.join(" · "))}</div>`
    : "";

  qs("pipelineSuccessTitle").textContent = "Pipeline completed";
  qs("pipelineSuccessText").textContent = summaryMessage;
  qs("pipelineSuccessSummary").innerHTML = `
    ${metaLine}
    <div class="pipeline-loading-counts">${buildPipelineCountsHtml(pipeline)}</div>
  `;
}

function stopPipelineSuccessGifTimer() {
  if (pipelineSuccessGifTimer) {
    clearTimeout(pipelineSuccessGifTimer);
    pipelineSuccessGifTimer = null;
  }
}

function restartPipelineSuccessGif() {
  const gif = qs("pipelineSuccessGif");
  const staticCheck = qs("pipelineSuccessStaticCheck");
  if (!gif || !staticCheck) return;

  stopPipelineSuccessGifTimer();

  staticCheck.classList.add("hidden");
  gif.classList.remove("hidden");

  const src = gif.dataset.src || gif.getAttribute("src");
  if (!src) return;

  gif.removeAttribute("src");
  void gif.offsetWidth;

  requestAnimationFrame(() => {
    gif.setAttribute("src", src);

    // Match this to the real GIF duration.
    pipelineSuccessGifTimer = setTimeout(() => {
      gif.classList.add("hidden");
      staticCheck.classList.remove("hidden");
    }, 1800);
  });
}

function showPipelineSuccessOverlay(pipeline = {}) {
  const overlay = qs("pageLoadingOverlay");
  const loadingPane = qs("pipelineOverlayLoading");
  const successPane = qs("pipelineOverlaySuccess");
  const successKey = getPipelineSuccessKey(pipeline);

  if (state.pipelineSuccessVisible && state.currentPipelineSuccessKey === successKey) {
    overlay.classList.remove("hidden");
    return;
  }

  loadingPane.classList.add("hidden");
  successPane.classList.remove("hidden");

  state.pipelineSuccessVisible = true;
  state.currentPipelineSuccessKey = successKey;

  renderPipelineSuccessSummary(pipeline);
  restartPipelineSuccessGif();

  overlay.classList.remove("hidden");
}

function showPageLoadingOverlay(title, text, pipeline = {}) {
  const overlay = qs("pageLoadingOverlay");
  const loadingPane = qs("pipelineOverlayLoading");
  const successPane = qs("pipelineOverlaySuccess");
  const successGif = qs("pipelineSuccessGif");
  const staticCheck = qs("pipelineSuccessStaticCheck");

  stopPipelineSuccessGifTimer();

  state.pipelineSuccessVisible = false;
  state.currentPipelineSuccessKey = null;

  loadingPane.classList.remove("hidden");
  successPane.classList.add("hidden");

  if (successGif) successGif.classList.remove("hidden");
  if (staticCheck) staticCheck.classList.add("hidden");

  qs("pageLoadingTitle").textContent = title || "Running live pipeline...";
  qs("pageLoadingText").textContent = text || "Preparing pipeline run.";
  qs("pipelineLoadingMeta").textContent = buildPipelineMetaText(pipeline);
  renderPipelineCounts(pipeline);
  renderPipelineStageStepper(pipeline);

  overlay.classList.remove("hidden");
}

function hidePageLoadingOverlay() {
  stopPipelineSuccessGifTimer();
  state.pipelineSuccessVisible = false;
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

  if (status === "succeeded") {
    runBtn.disabled = false;
    runBtn.textContent = "Run Live Pipeline";

    const successKey = getPipelineSuccessKey(pipeline);
    const shouldShowSuccess =
      hasPipelinePendingSuccess() && !wasPipelineSuccessAlreadyShown(successKey);

    if (shouldShowSuccess) {
      markPipelineSuccessShown(successKey);
      clearPipelinePendingSuccess();
      showPipelineSuccessOverlay(pipeline);
    } else if (!state.pipelineSuccessVisible) {
      hidePageLoadingOverlay();
    }

    return;
  }

  if (status === "failed") {
    runBtn.disabled = false;
    runBtn.textContent = "Run Live Pipeline";
    clearPipelinePendingSuccess();
    hidePageLoadingOverlay();
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
    planning_only: getBinaryToggleBool("pipelinePlanningOnly"),
    generate_tailoring: getBinaryToggleBool("pipelineGenerateTailoring"),
    generate_llm_tailoring: getBinaryToggleBool("pipelineGenerateLlmTailoring"),
    refresh_llm_tailoring: getBinaryToggleBool("pipelineRefreshLlmTailoring"),
    generate_llm_fallback: getBinaryToggleBool("pipelineGenerateLlmFallback"),
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

function buildQueueRowDetailedHtml(row) {
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
      <td>${escapeHtml(formatDateTime(row.posted_at) || "-")}</td>
      <td>${escapeHtml(row.winner_resume || "")}</td>
      <td>${escapeHtml(formatScore100(row.winner_score))}</td>
      <td>${escapeHtml(row.runner_up_resume || "")}</td>
      <td>${escapeHtml(formatScore100(row.score_gap))}</td>
      <td>${missingRequirementCount}</td>
      <td>${operatorDecision || "-"}</td>
      <td>${operatorSelectedResume || "-"}</td>
      <td class="reason-cell">${reason}</td>
      <td class="apply-cell sticky-apply-col">${applyButtonHtml}</td>
    </tr>
  `;
}

function buildQueueRowSimpleHtml(row) {
  const queueRank = escapeHtml(row.queue_rank || "");
  const action = escapeHtml(row.action || "");
  const company = escapeHtml(row.job_company || "");
  const title = escapeHtml(row.job_title || "");
  const postedAt = escapeHtml(formatDateTime(row.posted_at) || "-");
  const jobUrl = escapeHtml(row.job_doc_id || row.job_url || "");
  const titleHtml = jobUrl
    ? `<a class="job-link" href="${jobUrl}" target="_blank" rel="noopener noreferrer">${title}</a>`
    : title;

  const applyButtonHtml = buildApplicationButtonHtml(row);

  return `
    <tr>
      <td>${queueRank}</td>
      <td class="title-cell">
        <div><strong>${company || "-"}</strong></div>
        <div>${titleHtml}</div>
        <div class="subtext-inline">Posted: ${postedAt}</div>
        <div class="subtext-inline">${action || "-"}</div>
      </td>
      <td>
        ${buildResumeOptionHtml("Best", row.winner_resume || "", row.winner_score || "")}
        ${buildResumeOptionHtml("Backup", row.runner_up_resume || "", row.runner_up_score || "")}
      </td>
      <td class="apply-cell sticky-apply-col">${applyButtonHtml}</td>
    </tr>
  `;
}

function renderQueueRows(rows, metaLabel) {
  queueTableState.rows = Array.isArray(rows) ? rows.slice() : [];
  queueTableState.metaLabel = metaLabel;

  const tbody = qs("queueTableBody");
  const displayRows = sortRows(queueTableState.rows, QUEUE_SORT_COLUMNS, queueTableState.sort);
  const modeLabel = state.executiveViewMode === "simple" ? "Simple mode" : "Detailed mode";

  renderQueueHeaders();

  if (!displayRows.length) {
    const colspan = state.executiveViewMode === "simple" ? 4 : 14;
    tbody.innerHTML = `
      <tr>
        <td colspan="${colspan}" class="empty-state">No rows found.</td>
      </tr>
    `;
  } else if (state.executiveViewMode === "simple") {
    tbody.innerHTML = displayRows.map(buildQueueRowSimpleHtml).join("");
  } else {
    tbody.innerHTML = displayRows.map(buildQueueRowDetailedHtml).join("");
  }

  qs("tableMeta").textContent = `${queueTableState.metaLabel} · ${modeLabel}`;
}

function buildBrowseUrl() {
  const action = qs("actionFilter").value.trim();
  const undecidedOnly = getBinaryToggleBool("executiveUndecidedOnly") ? "true" : "";
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

  async function loadAppliedJobs() {
  state.currentMode = "applied_jobs";
  state.workflowView = null;

  const limit = qs("limitInput").value || "25";
  const data = await fetchJson(`/applied-jobs?limit=${encodeURIComponent(limit)}`);
  const count = data.count ?? 0;

  renderQueueRows(
    data.rows || [],
    `Applied jobs · ${count} row${count === 1 ? "" : "s"}`
  );
}

async function reloadCurrentTable() {
  if (state.currentMode === "applied_jobs") {
    await loadAppliedJobs();
  } else if (state.currentMode === "workflow" && state.workflowView) {
    await loadWorkflow(state.workflowView);
  } else {
    await loadBrowse();
  }
}

function clearFilters() {
  qs("actionFilter").value = "";
  setBinaryToggleValue("executiveUndecidedOnly", false);
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
      showAppError("Failed to open apply workflow", err);
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
      showAppError("Invalid pipeline configuration", err);
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
    markPipelinePendingSuccess();
    await loadPipelineStatus();
    startPipelinePolling();
  } catch (err) {
    clearPipelinePendingSuccess();
      hidePageLoadingOverlay();
      showAppError("Failed to start live pipeline", err);
    }
  });

  qs("pipelineSuccessOkBtn").addEventListener("click", () => {
    state.acknowledgedPipelineSuccessKey = state.currentPipelineSuccessKey;
    hidePageLoadingOverlay();
  }); 

  qs("closeAppErrorModalBtn").addEventListener("click", closeAppErrorModal);
  qs("appErrorOkBtn").addEventListener("click", closeAppErrorModal);

  getAppErrorModal().addEventListener("click", (event) => {
    if (event.target === getAppErrorModal()) {
      closeAppErrorModal();
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
        showAppError("Failed to update application status", err);
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
      showAppError("Failed to load browse data", err);
    }
  });

  qs("clearFiltersBtn").addEventListener("click", async () => {
    clearFilters();
    try {
      await loadBrowse();
    } catch (err) {
      showAppError("Failed to reload browse data", err);
    }
  });

  document.querySelectorAll("input[name='executiveViewMode']").forEach((input) => {
    input.addEventListener("change", () => {
      setExecutiveViewMode(input.value);
    });
  });

  qs("refreshStatusBtn").addEventListener("click", async () => {
    try {
      await loadStatus();
      await loadPipelineStatus();
      await reloadCurrentTable();
    } catch (err) {
      showAppError("Failed to refresh dashboard", err);
    }
  });

  document.querySelectorAll(".quick-view-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      try {
        if (btn.dataset.mode === "applied_jobs") {
          await loadAppliedJobs();
          return;
        }

        const view = btn.dataset.view;
        if (!view) return;

        await loadWorkflow(view);
      } catch (err) {
        showAppError("Failed to load workflow view", err);
      }
    });
  });
}

async function init() {
  try {
    attachEventHandlers();
    attachApplicationHandlers();
    attachPipelineConfigHandlers();
    applyPipelinePreset("full");
    syncPipelinePathPreview();

    state.executiveViewMode = loadExecutiveViewMode();
    syncExecutiveViewModeControls();

    bindTableSorting("queueTable", QUEUE_SORT_COLUMNS, queueTableState.sort, () => {
      renderQueueRows(queueTableState.rows, queueTableState.metaLabel);
    });

    await loadStatus();
    await loadPipelineStatus();
    await loadBrowse();

    const pipelineData = await fetchJson("/pipeline/status");
    if (pipelineData.pipeline && pipelineData.pipeline.is_running) {
      startPipelinePolling();
    }
  } catch (err) {
    console.error(err);
    showAppError("Failed to initialize dashboard", err);
  }
}

window.addEventListener("DOMContentLoaded", init);