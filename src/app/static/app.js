const state = {
  currentMode: "browse",
  workflowView: null,
  executiveViewMode: "detailed",
  pendingApplicationJob: null,
  applicationModalOpen: false,
  pendingPipelineConfig: null,
  pipelineSuccessVisible: false,
  currentPipelineSuccessKey: null,
  pipelineFailureVisible: false,
  currentPipelineFailureKey: null,
  acknowledgedPipelineSuccessKey: null,
  lastPipelineTableRefreshKey: "",
  pipelineGate: null,
};

const queueTableState = {
  rows: [],
  metaLabel: "Loading...",
  page: 1,
  pageSize: 15,
  totalCount: 0,
  totalPages: 1,
  hasPrevPage: false,
  hasNextPage: false,
  sort: {
    key: "",
    direction: "asc",
  },
};

const PENDING_APPLICATION_STORAGE_KEY = "job_operator_pending_application";
const PIPELINE_PENDING_SUCCESS_KEY = "job_operator_pipeline_pending_success";
const PIPELINE_SHOWN_SUCCESS_KEY = "job_operator_pipeline_shown_success";
const PIPELINE_DATA_VERSION_STORAGE_KEY = "job_operator_pipeline_data_version";
const EXECUTIVE_VIEW_MODE_STORAGE_KEY = "job_operator_executive_view_mode";
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
  finalization: "Finalization",
};

const PIPELINE_VISIBLE_STAGE_GROUPS = [
  { key: "starting", label: "Starting pipeline", stages: ["startup"] },
  { key: "collecting", label: "Collecting jobs", stages: ["scraping"] },
  { key: "filtering", label: "Filtering and deduplicating", stages: ["filtering", "dedupe"] },
  { key: "ranking", label: "Ranking opportunities", stages: ["ranking", "cache_filter", "details"] },
  { key: "intelligence", label: "Running job intelligence", stages: ["intelligence"] },
  { key: "evaluating", label: "Evaluating fit", stages: ["ai_evaluation_filter", "embedding_prefilter", "ai_evaluation"] },
  { key: "matching", label: "Matching resumes", stages: ["resume_matching"] },
  { key: "prioritizing", label: "Prioritizing applications", stages: ["application_priority"] },
  { key: "planning", label: "Preparing planning artifacts", stages: ["rag_export", "planning"] },
  { key: "finalizing", label: "Finalizing run", stages: ["finalization"] },
];

const PIPELINE_FINALIZING_FALLBACK = {
  key: "finalizing-results-fallback",
  label: "Finalizing pipeline results",
  description: "Saving run results and preparing the dashboards.",
  stages: [],
  isUiFallback: true,
};

const PIPELINE_STAGE_TO_VISIBLE_GROUP = PIPELINE_VISIBLE_STAGE_GROUPS.reduce((acc, group, index) => {
  group.stages.forEach((stage) => {
    acc[stage] = index;
  });
  return acc;
}, {});

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
  planning_packets_total: "Planning Packets",
  planning_packets_completed: "Packets Done",
  planning_packets_generated: "Packets Created",
  planning_llm_generated: "LLM Generated",
  planning_llm_cached: "LLM Cached",
  planning_llm_failed: "LLM Failed",
  final_jobs: "Final Jobs",
};

const QUEUE_SORT_COLUMNS = [
  { key: "queue_rank", label: "Rank", type: "number" },
  { key: "job_title", label: "Job title", type: "text", getValue: (row) => row.job_title || "" },
  { key: "job_company", label: "Company", type: "text", getValue: (row) => row.job_company || "" },
  { key: "job_location", label: "Location", type: "text", getValue: (row) => row.job_location || "" },
  { key: "posted_at", label: "Posted at", type: "date", getValue: (row) => row.posted_at || "" },
  { key: "recommendation", label: "Recommendation", type: "text", getValue: (row) => formatQueueActionLabel(row.action) },
  { key: "packet_status", label: "Packet", type: "text", getValue: (row) => formatPacketStatusLabel(row.packet_generation_allowed) },
  { key: "winner_score", label: "Match", type: "number" },
  { key: "selected_resume", label: "Selected Resume", type: "text", getValue: (row) => row.operator_selected_resume || row.winner_resume || "" },
  { key: "runner_up_resume", label: "Runner-up resume", type: "text", getValue: (row) => row.runner_up_resume || "" },
  { key: "score_gap", label: "Score gap", type: "number" },
  { key: "missing_requirement_count", label: "Missing req count", type: "number" },
  { key: "next_step", label: "Next step", type: "text", getValue: (row) => formatOperatorDecisionLabel(row.operator_decision) || formatOperatorReviewLaneLabel(row.operator_review_lane) || "" },
  { key: "queue_priority_reason", label: "Priority reason", type: "text", getValue: (row) => formatDiagnosticReasonLabel(row.queue_priority_reason) },
  { key: "apply", label: "Review", sortable: false },
];

const SIMPLE_QUEUE_SORT_COLUMNS = [
  { key: "queue_rank", label: "Rank", type: "number" },
  { key: "job_title", label: "Job title/company", type: "text", getValue: (row) => `${row.job_title || ""} ${row.job_company || ""}` },
  { key: "posted_at", label: "Posted at", type: "date", getValue: (row) => row.posted_at || "" },
  { key: "recommendation", label: "Recommendation", type: "text", getValue: (row) => formatQueueActionLabel(row.action) },
  { key: "packet_status", label: "Packet", type: "text", getValue: (row) => formatPacketStatusLabel(row.packet_generation_allowed) },
  { key: "winner_score", label: "Match", type: "number" },
  { key: "selected_resume", label: "Selected Resume", type: "text", getValue: (row) => row.operator_selected_resume || row.winner_resume || "" },
  { key: "apply", label: "Review", sortable: false },
];

const PACKET_HELP_TEXT = "A packet is a review bundle for this job. It includes the job, selected resume, match signals, gaps, and tailoring guidance. It does not apply to the job.";

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
    generate_llm_adjudication: true,
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

function truncateText(value, maxLength = 36) {
  const text = String(value || "").trim();
  if (!text) return "";
  if (text.length <= maxLength) return text;
  return `${text.slice(0, maxLength - 1)}…`;
}

function stripPdfExtension(value) {
  return String(value || "").trim().replace(/\.pdf$/i, "");
}

function humanizeResumeDisplayName(value) {
  const raw = String(value || "").trim();
  if (!raw) return "";
  return stripPdfExtension(raw).replaceAll("_", " ");
}

function buildResumeCellHtml(
  value,
  { emptyLabel = "-", truncate = false, maxLength = 36, wrap = false } = {}
) {
  const raw = String(value || "").trim();
  const className = wrap ? "resizable-cell-text resume-cell-text" : "resizable-cell-text";

  if (!raw) {
    return `<span class="${className}">${escapeHtml(emptyLabel)}</span>`;
  }

  const full = humanizeResumeDisplayName(raw);
  const visible = truncate ? truncateText(full, maxLength) : full;

  return `<span class="${className}" title="${escapeHtml(full)}">${escapeHtml(visible)}</span>`;
}

function loadTableColumnWidths(storageKey) {
  try {
    const parsed = JSON.parse(localStorage.getItem(storageKey) || "{}");
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch {
    return {};
  }
}

function saveTableColumnWidths(storageKey, widths) {
  localStorage.setItem(storageKey, JSON.stringify(widths));
}

function getTableColumnElement(table, key) {
  return table.querySelector(`col[data-col-key="${key}"]`);
}

function applyTableColumnWidths(tableId, storageKey) {
  const table = document.getElementById(tableId);
  if (!table) return;

  const widths = loadTableColumnWidths(storageKey);
  Object.entries(widths).forEach(([key, width]) => {
    const col = getTableColumnElement(table, key);
    if (col && Number(width) > 0) {
      col.style.width = `${Number(width)}px`;
    }
  });
}

function getTableColumnIndex(th) {
  if (!th || !th.parentElement) return -1;
  return Array.from(th.parentElement.children).indexOf(th);
}

function measureAutoFitColumnWidth(table, th) {
  const columnIndex = getTableColumnIndex(th);
  if (columnIndex < 0) return 140;

  const samples = [];
  const headerLabel = th.querySelector(".resizable-col-label");
  if (headerLabel && headerLabel.textContent.trim()) {
    samples.push({ text: headerLabel.textContent.trim(), source: headerLabel });
  }

  table.querySelectorAll("tbody tr").forEach((row) => {
    const cell = row.children[columnIndex];
    if (!cell) return;

    const preferred =
      cell.querySelector(".resume-cell-text") ||
      cell.querySelector(".resizable-cell-text") ||
      cell;

    const text = String(preferred.textContent || "").trim();
    if (!text) return;

    samples.push({ text, source: preferred });
  });

  const measurer = document.createElement("span");
  measurer.className = "table-width-measure";
  document.body.appendChild(measurer);

  let maxWidth = 140;

  samples.forEach(({ text, source }) => {
    const styles = window.getComputedStyle(source);
    measurer.style.font = styles.font;
    measurer.style.fontFamily = styles.fontFamily;
    measurer.style.fontSize = styles.fontSize;
    measurer.style.fontWeight = styles.fontWeight;
    measurer.style.letterSpacing = styles.letterSpacing;
    measurer.style.textTransform = styles.textTransform;
    measurer.textContent = text;

    maxWidth = Math.max(maxWidth, Math.ceil(measurer.getBoundingClientRect().width) + 32);
  });

  document.body.removeChild(measurer);
  return Math.min(Math.max(maxWidth, 140), 900);
}

function initResizableTableColumns(tableId, storageKey) {
  const table = document.getElementById(tableId);
  if (!table) return;

  applyTableColumnWidths(tableId, storageKey);

  const handles = Array.from(table.querySelectorAll(".col-resize-handle"));

  handles.forEach((handle) => {
    if (handle.dataset.resizeBound === "true") return;
    handle.dataset.resizeBound = "true";

    handle.addEventListener("dblclick", (event) => {
      event.preventDefault();
      event.stopPropagation();

      const th = handle.closest("th");
      if (!th) return;

      const key = handle.dataset.resizeKey;
      if (!key) return;

      const col = getTableColumnElement(table, key);
      if (!col) return;

      const nextWidth = measureAutoFitColumnWidth(table, th);
      col.style.width = `${nextWidth}px`;

      const widths = loadTableColumnWidths(storageKey);
      widths[key] = nextWidth;
      saveTableColumnWidths(storageKey, widths);
    });

    handle.addEventListener("mousedown", (event) => {
      event.preventDefault();
      event.stopPropagation();

      const th = handle.closest("th");
      if (!th) return;

      const key = handle.dataset.resizeKey;
      if (!key) return;

      const col = getTableColumnElement(table, key);
      if (!col) return;

      const widths = loadTableColumnWidths(storageKey);
      const startX = event.clientX;
      const startWidth = th.getBoundingClientRect().width;

      document.body.classList.add("table-column-resizing");

      function onMouseMove(moveEvent) {
        const delta = moveEvent.clientX - startX;
        const nextWidth = Math.max(90, Math.round(startWidth + delta));
        col.style.width = `${nextWidth}px`;
        widths[key] = nextWidth;
      }

      function onMouseUp() {
        document.body.classList.remove("table-column-resizing");
        saveTableColumnWidths(storageKey, widths);
        window.removeEventListener("mousemove", onMouseMove);
        window.removeEventListener("mouseup", onMouseUp);
      }

      window.addEventListener("mousemove", onMouseMove);
      window.addEventListener("mouseup", onMouseUp);
    });
  });
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

function buildResizableHeaderInnerHtml(label, key, { sortable = true } = {}) {
  const safeLabel = escapeHtml(label || "");
  const packetInfoHtml = key === "packet_status"
    ? `<span class="packet-info-icon" title="${escapeHtml(PACKET_HELP_TEXT)}" aria-label="${escapeHtml(PACKET_HELP_TEXT)}">ⓘ</span>`
    : "";

  if (!sortable) {
    return `
      <div class="resizable-col-content">
        <span class="resizable-col-label">${safeLabel}</span>
        ${packetInfoHtml}
      </div>
      <span class="col-resize-handle" data-resize-key="${escapeHtml(key || "")}"></span>
    `;
  }

  return `
    <div class="resizable-col-content">
      <button
        type="button"
        class="sort-header-btn"
        data-sort-key="${escapeHtml(key || "")}"
        aria-label="Sort by ${safeLabel}"
      >
        <span class="sort-header-label resizable-col-label">${safeLabel}</span>
        <span class="sort-header-indicator">↕</span>
      </button>
      ${packetInfoHtml}
    </div>
    <span class="col-resize-handle" data-resize-key="${escapeHtml(key || "")}"></span>
  `;
}

function setResizableHeaderCell(th, column) {
  const key = column.key || "";
  const label = column.label || "";
  const sortable = column.sortable !== false;

  th.dataset.colKey = key;
  th.style.width = th.style.width || "";
  th.classList.toggle("sortable-col", sortable);
  th.innerHTML = buildResizableHeaderInnerHtml(label, key, { sortable });
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

    const button = th.querySelector(".sort-header-btn");
    const labelEl = th.querySelector(".sort-header-label");
    const indicatorEl = th.querySelector(".sort-header-indicator");

    if (column.sortable === false) {
      if (!th.querySelector(".col-resize-handle")) {
        setResizableHeaderCell(th, column);
      }
      th.classList.remove("sortable-col");
      return;
    }

    if (!button || !labelEl || !indicatorEl) {
      setResizableHeaderCell(th, column);
    }

    const nextButton = th.querySelector(".sort-header-btn");
    const nextLabel = th.querySelector(".sort-header-label");
    const nextIndicator = th.querySelector(".sort-header-indicator");

    th.classList.add("sortable-col");
    nextButton.dataset.sortKey = column.key;
    nextButton.setAttribute("aria-label", `Sort by ${label}`);
    nextButton.classList.toggle("is-active", sortState.key === column.key);
    nextLabel.textContent = label;
    nextIndicator.textContent = getSortIndicator(sortState, column.key);
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

function getMultiSelectRoot(id) {
  return qs(id);
}

function getMultiSelectMenu(root) {
  return root?._multiSelectMenu || root?.querySelector(".multi-select-menu") || null;
}

function getMultiSelectOptions(root, selector = ".multi-select-option") {
  const menu = getMultiSelectMenu(root);
  return Array.from((menu || root)?.querySelectorAll(selector) || []);
}

function getMultiSelectValues(id) {
  const root = getMultiSelectRoot(id);
  if (!root) return [];

  return getMultiSelectOptions(root, ".multi-select-option.is-selected")
    .map((option) => String(option.dataset.value || "").trim())
    .filter((value) => Boolean(value) && value !== (root.dataset.allValue || ""));
}

function setMultiSelectOptionSelected(option, isSelected) {
  if (!option) return;
  option.classList.toggle("is-selected", isSelected);
  option.setAttribute("aria-checked", isSelected ? "true" : "false");
}

function resetMultiSelectToAll(id) {
  const root = getMultiSelectRoot(id);
  if (!root) return;
  const allValue = root.dataset.allValue || "";
  getMultiSelectOptions(root).forEach((option) => {
    setMultiSelectOptionSelected(option, Boolean(allValue) && option.dataset.value === allValue);
  });
  updateMultiSelectLabel(root);
}

function appendMultiValueParams(params, key, values) {
  values.forEach((value) => params.append(key, value));
}

function updateMultiSelectLabel(root) {
  if (!root) return;

  const label = root.querySelector(".multi-select-trigger-label");
  if (!label) return;

  const selected = getMultiSelectOptions(root, ".multi-select-option.is-selected");
  const placeholder = root.dataset.placeholder || "All";

  if (!selected.length) {
    label.textContent = placeholder;
  } else if (selected.length === 1) {
    const text = selected[0].querySelector(".multi-select-option-label")?.textContent?.trim();
    label.textContent = text || selected[0].dataset.value || placeholder;
  } else {
    label.textContent = `${selected.length} selected`;
  }
}

function setMultiSelectOpen(root, isOpen) {
  if (!root) return;

  const trigger = root.querySelector(".multi-select-trigger");
  const menu = getMultiSelectMenu(root);
  if (!trigger || !menu) return;

  root.classList.toggle("is-open", isOpen);
  trigger.setAttribute("aria-expanded", isOpen ? "true" : "false");
  if (isOpen) {
    menu.hidden = false;
    menu.dataset.multiSelectOwner = root.id || "";
    if (menu.parentElement !== document.body) {
      document.body.appendChild(menu);
    }
    positionMultiSelectMenu(root);
    menu.querySelector(".multi-select-search-input")?.focus({ preventScroll: true });
  } else {
    const searchInput = menu.querySelector(".multi-select-search-input");
    if (searchInput) {
      searchInput.value = "";
      filterMultiSelectOptions(root, "");
    }
    menu.hidden = true;
    root.classList.remove("opens-upward");
    delete menu.dataset.placement;
    resetMultiSelectMenuPosition(menu);
    if (menu.parentElement !== root) {
      root.appendChild(menu);
    }
  }
}

function resetMultiSelectMenuPosition(menu) {
  if (!menu) return;

  ["position", "left", "right", "top", "bottom", "width", "max-height", "z-index"].forEach((name) => {
    menu.style.removeProperty(name);
  });
}

function positionMultiSelectMenu(root) {
  if (!root) return;

  const trigger = root.querySelector(".multi-select-trigger");
  const menu = getMultiSelectMenu(root);
  if (!trigger || !menu || menu.hidden) return;

  const rect = trigger.getBoundingClientRect();
  const viewportPadding = 16;
  const preferredWidth = Math.max(rect.width, 280);
  const width = Math.min(preferredWidth, window.innerWidth - viewportPadding * 2);
  const left = Math.min(
    Math.max(rect.left, viewportPadding),
    window.innerWidth - width - viewportPadding
  );
  const availableBelow = window.innerHeight - rect.bottom - viewportPadding;
  const availableAbove = rect.top - viewportPadding;
  const openAbove = availableBelow < 190 && availableAbove > availableBelow;
  const availableSpace = openAbove ? availableAbove : availableBelow;
  const maxHeight = Math.max(168, Math.min(380, availableSpace - 8));

  root.classList.toggle("opens-upward", openAbove);
  menu.dataset.placement = openAbove ? "top" : "bottom";

  menu.style.setProperty("position", "fixed", "important");
  menu.style.setProperty("left", `${left}px`, "important");
  menu.style.setProperty("right", "auto", "important");
  menu.style.setProperty("width", `${width}px`, "important");
  menu.style.setProperty("max-height", `${maxHeight}px`, "important");
  menu.style.setProperty("z-index", "10000", "important");
  menu.style.setProperty("top", openAbove ? "auto" : `${rect.bottom + 8}px`, "important");
  menu.style.setProperty(
    "bottom",
    openAbove ? `${window.innerHeight - rect.top + 8}px` : "auto",
    "important"
  );
}

function clearMultiSelect(id) {
  const root = getMultiSelectRoot(id);
  if (!root) return;

  if (root.dataset.allValue) {
    resetMultiSelectToAll(id);
    return;
  }

  getMultiSelectOptions(root).forEach((option) => setMultiSelectOptionSelected(option, false));

  updateMultiSelectLabel(root);
}

function normalizeMultiSelectSearchText(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/[\/_-]+/g, " ")
    .trim()
    .replace(/\s+/g, " ");
}

function filterMultiSelectOptions(root, query) {
  const normalizedQuery = normalizeMultiSelectSearchText(query);
  let visibleCount = 0;
  getMultiSelectOptions(root).forEach((option) => {
    const label = option.querySelector(".multi-select-option-label")?.textContent || "";
    const isVisible = !normalizedQuery || normalizeMultiSelectSearchText(label).includes(normalizedQuery);
    option.hidden = !isVisible;
    if (isVisible) visibleCount += 1;
  });
  const empty = getMultiSelectMenu(root)?.querySelector(".multi-select-empty");
  if (empty) empty.hidden = visibleCount > 0;
}

function bindMultiSelectSearch(root) {
  const searchInput = getMultiSelectMenu(root)?.querySelector(".multi-select-search-input");
  if (!searchInput || searchInput.dataset.bound === "true") return;
  searchInput.dataset.bound = "true";
  searchInput.addEventListener("click", (event) => event.stopPropagation());
  searchInput.addEventListener("input", () => filterMultiSelectOptions(root, searchInput.value));
}

function handleMultiSelectOptionSelection(root, option) {
  const allValue = root.dataset.allValue || "";
  const optionValue = String(option.dataset.value || "");
  if (allValue && optionValue === allValue) {
    getMultiSelectOptions(root).forEach((candidate) => {
      setMultiSelectOptionSelected(candidate, candidate === option);
    });
  } else {
    const isSelected = !option.classList.contains("is-selected");
    setMultiSelectOptionSelected(option, isSelected);
    if (allValue && isSelected) {
      const allOption = getMultiSelectOptions(root).find(
        (candidate) => candidate.dataset.value === allValue
      );
      setMultiSelectOptionSelected(allOption, false);
    }
    if (allValue && !getMultiSelectValues(root.id).length) {
      resetMultiSelectToAll(root.id);
    }
  }
  updateMultiSelectLabel(root);
}

function initMultiSelect(id) {
  const root = getMultiSelectRoot(id);
  if (!root || root.dataset.bound === "true") return;

  const trigger = root.querySelector(".multi-select-trigger");
  const menu = root.querySelector(".multi-select-menu");
  if (!trigger || !menu) return;

  root._multiSelectMenu = menu;
  root.dataset.bound = "true";
  bindMultiSelectSearch(root);
  updateMultiSelectLabel(root);

  trigger.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();

    const willOpen = menu.hidden;
    document.querySelectorAll(".multi-select").forEach((node) => {
      if (node !== root) {
        setMultiSelectOpen(node, false);
      }
    });
    setMultiSelectOpen(root, willOpen);
  });

  menu.addEventListener("click", (event) => {
    const option = event.target.closest(".multi-select-option");
    if (!option || !menu.contains(option)) return;
    event.preventDefault();
    event.stopPropagation();
    handleMultiSelectOptionSelection(root, option);
  });
}

function renderPreferenceOptions(rootId, payload = {}) {
  const root = getMultiSelectRoot(rootId);
  const optionsRoot = getMultiSelectMenu(root)?.querySelector(".multi-select-options");
  if (!root || !optionsRoot) return;
  const options = Array.isArray(payload.preference_options) ? payload.preference_options : [];
  optionsRoot.innerHTML = `
    <button type="button" class="multi-select-option is-selected" data-value="__all__" aria-checked="true">
      <span class="multi-select-option-check">✓</span>
      <span class="multi-select-option-label">All Preferences</span>
    </button>
    ${options.map((option) => `
      <button type="button" class="multi-select-option" data-value="${escapeHtml(option.role_family_id || "")}" aria-checked="false">
        <span class="multi-select-option-check">✓</span>
        <span class="multi-select-option-label">${escapeHtml(option.display_name || option.role_family_id || "")}</span>
      </button>
    `).join("")}
  `;
}

async function loadPreferenceFilterOptions(rootId) {
  try {
    const payload = await fetchJson("/onboarding/preferences");
    renderPreferenceOptions(rootId, payload);
  } catch (error) {
    console.warn("Could not load preference filter options.", error);
  }
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
  document.body.classList.toggle("executive-simple-mode", mode === "simple");
  document.body.classList.toggle("executive-detailed-mode", mode !== "simple");
}

function setExecutiveViewMode(mode) {
  state.executiveViewMode = normalizeExecutiveViewMode(mode);
  localStorage.setItem(EXECUTIVE_VIEW_MODE_STORAGE_KEY, state.executiveViewMode);
  syncExecutiveViewModeControls();
  renderQueueRows(queueTableState.rows, queueTableState.metaLabel);
}

function renderQueueHeaders() {
  const table = qs("queueTable");
  const colgroup = qs("queueTableColgroup");
  const headerRow = qs("queueTableHeaderRow");
  if (!table || !colgroup || !headerRow) return;

  if (state.executiveViewMode === "simple") {
    const simpleWidths = {
      queue_rank: 110,
      job_title: 320,
      posted_at: 150,
      recommendation: 240,
      packet_status: 150,
      winner_score: 120,
      selected_resume: 240,
      apply: 140,
    };
    colgroup.innerHTML = SIMPLE_QUEUE_SORT_COLUMNS.map((column) => {
      if (column.key === "apply") {
        return `<col class="table-static-col" data-static-col-key="apply" style="width: ${simpleWidths.apply}px;" />`;
      }
      return `<col data-col-key="${escapeHtml(column.key)}" style="width: ${simpleWidths[column.key] || 180}px;" />`;
    }).join("");
    headerRow.innerHTML = SIMPLE_QUEUE_SORT_COLUMNS.map((column) => {
      if (column.key === "apply") {
        return `
          <th class="sticky-apply-col apply-col-fixed">
            <div class="resizable-col-content">
              <span class="resizable-col-label">${escapeHtml(column.label)}</span>
            </div>
          </th>
        `;
      }
      return `
        <th data-col-key="${escapeHtml(column.key)}">
          ${buildResizableHeaderInnerHtml(column.label, column.key, { sortable: column.sortable !== false })}
        </th>
      `;
    }).join("");
    renderSortableHeaders("queueTable", SIMPLE_QUEUE_SORT_COLUMNS, queueTableState.sort);
    initResizableTableColumns("queueTable", "queueTableColumnWidths");
    return;
  }

  const detailedWidths = {
    queue_rank: 110,
    job_title: 260,
    job_company: 180,
    job_location: 170,
    posted_at: 150,
    recommendation: 240,
    packet_status: 150,
    winner_score: 120,
    selected_resume: 240,
    runner_up_resume: 220,
    score_gap: 110,
    missing_requirement_count: 140,
    next_step: 170,
    queue_priority_reason: 190,
    apply: 140,
  };

  colgroup.innerHTML = QUEUE_SORT_COLUMNS.map((column) => {
    if (column.key === "apply") {
      return `<col class="table-static-col" data-static-col-key="apply" style="width: ${detailedWidths.apply}px;" />`;
    }
    return `<col data-col-key="${escapeHtml(column.key)}" style="width: ${detailedWidths[column.key] || 180}px;" />`;
  }).join("");

  headerRow.innerHTML = QUEUE_SORT_COLUMNS.map((column) => {
    if (column.key === "apply") {
      return `
        <th class="sticky-apply-col apply-col-fixed">
          <div class="resizable-col-content">
            <span class="resizable-col-label">${escapeHtml(column.label)}</span>
          </div>
        </th>
      `;
    }

    return `
      <th data-col-key="${escapeHtml(column.key)}">
        ${buildResizableHeaderInnerHtml(column.label, column.key, { sortable: column.sortable !== false })}
      </th>
    `;
  }).join("");

  renderSortableHeaders("queueTable", QUEUE_SORT_COLUMNS, queueTableState.sort);
  initResizableTableColumns("queueTable", "queueTableColumnWidths");
}

function buildResumeOptionHtml(label, resumeName, score) {
  const safeLabel = escapeHtml(label || "");
  const safeResume = buildResumeCellHtml(resumeName || "-", { emptyLabel: "-", wrap: true});
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

function setQueueLoadingState(label) {
  const tbody = qs("queueTableBody");
  if (!tbody) return;

  tbody.innerHTML = "";
  renderQueueHeaders();
  window.setTableWrapLoading?.(tbody, label);
  qs("tableMeta").textContent = "Loading...";

  const paginationMeta = qs("queuePaginationMeta");
  const paginationActions = qs("queuePaginationActions");
  if (paginationMeta) paginationMeta.textContent = "Loading...";
  if (paginationActions) paginationActions.innerHTML = "";
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

const DATE_ONLY_FORMATTER = new Intl.DateTimeFormat(undefined, {
  month: "short",
  day: "numeric",
  year: "numeric",
});

const TIME_ONLY_FORMATTER = new Intl.DateTimeFormat(undefined, {
  hour: "numeric",
  minute: "2-digit",
  timeZoneName: "short",
});

const DATE_TIME_FORMATTER = new Intl.DateTimeFormat(undefined, {
  month: "short",
  day: "numeric",
  year: "numeric",
  hour: "numeric",
  minute: "2-digit",
  timeZoneName: "short",
});

function buildDateTimeCellHtml(value) {
  if (!value) return "-";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return escapeHtml(String(value));
  }

  return `
    <div class="datetime-cell">
      <div class="datetime-cell-date">${escapeHtml(DATE_ONLY_FORMATTER.format(date))}</div>
      <div class="datetime-cell-time">${escapeHtml(TIME_ONLY_FORMATTER.format(date))}</div>
    </div>
  `;
}

function buildPostedAtCellHtml(row) {
  if (row?.posted_at) {
    return buildDateTimeCellHtml(row.posted_at);
  }

  if (row?.freshness_status === "unknown_timestamp_allowed") {
    return `<span class="timestamp-unavailable-label">Timestamp unavailable</span>`;
  }

  return "-";
}

function buildJobTitleCellHtml(row, { simple = false, includeLocation = true } = {}) {
  const title = escapeHtml(row.job_title || "");
  const jobUrl = escapeHtml(row.job_doc_id || row.job_url || "");
  const location = escapeHtml(row.job_location || "");
  const titleHtml = jobUrl
    ? `<a class="job-link" href="${jobUrl}" target="_blank" rel="noopener noreferrer">${title}</a>`
    : title;
  const locationHtml = includeLocation && location
    ? `<div class="${simple ? "queue-simple-location" : "queue-job-location"}">${location}</div>`
    : "";

  return `${titleHtml}${locationHtml}`;
}

function formatAdvisoryPriorityLabel(value) {
  const normalized = String(value || "").trim().toLowerCase();
  return {
    apply_now: "Ready for review",
    tailor_first: "Tailor first",
    manual_review: "Manual review",
    skip_for_now: "Review later",
    watch_source: "Watch source",
  }[normalized] || "";
}

function formatQueueActionLabel(value) {
  const normalized = String(value || "").trim().toUpperCase();
  return {
    APPLY: "Ready for review",
    APPLY_REVIEW_VARIANTS: "Review resume choice",
    MAYBE_TAILOR: "Tailor first",
    SKIP_FOR_NOW: "Review later",
  }[normalized] || String(value || "").trim();
}

function formatPacketStatusLabel(value) {
  const normalized = String(value || "").trim().toLowerCase();
  if (["true", "1", "yes", "y", "on"].includes(normalized)) return "Packet ready";
  if (["false", "0", "no", "n", "off"].includes(normalized)) return "No packet";
  return "";
}

function formatDiagnosticReasonLabel(value) {
  const normalized = String(value || "").trim().toLowerCase();
  return {
    no_deterministic_winner: "No clear resume match",
    borderline_deterministic_score: "Borderline match",
    tailoring_signal: "Tailoring may improve fit",
    tailoring_likely_worthwhile: "Tailoring may improve fit",
    packet_generation_blocked: "Packet unavailable",
    deterministic_equivalent_variants: "Close resume match",
    fallback_only_no_deterministic_match: "No credible resume match",
  }[normalized] || String(value || "").replaceAll("_", " ");
}

function formatOperatorDecisionLabel(value) {
  const normalized = String(value || "").trim().toUpperCase();
  return {
    SELECT_RESUME: "Choose resume",
    MAYBE_TAILOR: "Tailor first",
    SKIP_FOR_NOW: "Review later",
    APPLY: "Ready for review",
    APPLY_REVIEW_VARIANTS: "Review resume choice",
  }[normalized] || String(value || "").replaceAll("_", " ");
}

function getRecommendationTone(value) {
  const normalized = String(value || "").trim().toUpperCase();
  return {
    APPLY: "ready",
    APPLY_REVIEW_VARIANTS: "choice",
    SELECT_RESUME: "choice",
    MAYBE_TAILOR: "tailor",
    SKIP_FOR_NOW: "later",
  }[normalized] || "unavailable";
}

function buildPacketStatusChipHtml(row) {
  const packetAllowed = String(row?.packet_generation_allowed || "").trim();
  const label = formatPacketStatusLabel(packetAllowed);
  if (!label) return "";
  const modifier = label === "Packet ready" ? "ready" : "blocked";
  return `<span class="queue-packet-pill queue-packet-pill--${modifier}">${escapeHtml(label)}</span>`;
}

function buildRecommendationDetailsHtml(items) {
  const rows = (items || [])
    .filter((item) => item && String(item.value || "").trim())
    .map((item) => `
      <div class="queue-recommendation-detail-row">
        <dt>${escapeHtml(item.label)}</dt>
        <dd>${escapeHtml(item.value)}</dd>
      </div>
    `)
    .join("");
  if (!rows) return "";
  return `
    <details class="queue-recommendation-details">
      <summary>Why?</summary>
      <dl>${rows}</dl>
    </details>
  `;
}

function buildAdvisoryPriorityHtml(row, { simple = false } = {}) {
  const priority = String(row?.advisory_priority || "").trim().toLowerCase();
  const label = formatAdvisoryPriorityLabel(priority);
  if (!label) return "";

  const reasonCodes = String(row?.advisory_reason_codes || "").trim();
  const existingAction = String(row?.existing_action || row?.action || "").trim();
  const packetAllowed = String(row?.packet_generation_allowed || "").trim();
  const packetBlockReason = String(row?.packet_generation_block_reason || "").trim();
  const details = [
    { label: "Raw action", value: existingAction },
    { label: "Reason", value: reasonCodes.split("|").filter(Boolean).map(formatDiagnosticReasonLabel).join(", ") },
    { label: "Raw reason codes", value: reasonCodes.replaceAll("|", ", ") },
    { label: "Raw packet flag", value: packetAllowed },
    { label: "Raw block reason", value: packetBlockReason },
  ];

  return `
    <div class="${simple ? "queue-advisory-priority queue-advisory-priority--simple" : "queue-advisory-priority"}">
      <span class="queue-advisory-pill queue-advisory-pill--${escapeHtml(priority)}">${escapeHtml(label)}</span>
      ${buildRecommendationDetailsHtml(details)}
    </div>
  `;
}

function formatTailoringDecisionLabel(value) {
  const normalized = String(value || "").trim().toLowerCase();
  return {
    no_tailoring_needed: "No tailoring needed",
    light_tailoring: "Light tailoring",
    tailor_before_apply: "Tailor before apply",
    manual_review_before_tailoring: "Review before tailoring",
    do_not_tailor: "Do not tailor",
  }[normalized] || "";
}

function buildTailoringDecisionHtml(row, { simple = false } = {}) {
  const decision = String(row?.tailoring_decision || "").trim().toLowerCase();
  const label = formatTailoringDecisionLabel(decision);
  if (!label) return "";

  const reasonCodes = String(row?.tailoring_reason_codes || "").trim();
  const existingAction = String(row?.existing_action || row?.action || "").trim();
  const advisoryPriority = String(row?.advisory_priority || "").trim();
  const packetAllowed = String(row?.packet_generation_allowed || "").trim();
  const packetBlockReason = String(row?.packet_generation_block_reason || "").trim();
  const criticDecision = String(row?.critic_decision || "").trim();
  const details = [
    { label: "Raw action", value: existingAction },
    { label: "Advisory priority", value: formatAdvisoryPriorityLabel(advisoryPriority) || advisoryPriority },
    { label: "Reason", value: reasonCodes.split("|").filter(Boolean).map(formatDiagnosticReasonLabel).join(", ") },
    { label: "Raw reason codes", value: reasonCodes.replaceAll("|", ", ") },
    { label: "Raw packet flag", value: packetAllowed },
    { label: "Raw block reason", value: packetBlockReason },
    { label: "Critic", value: criticDecision },
  ];

  return `
    <div class="${simple ? "queue-tailoring-decision queue-tailoring-decision--simple" : "queue-tailoring-decision"}">
      <span class="queue-tailoring-pill queue-tailoring-pill--${escapeHtml(decision)}">${escapeHtml(label)}</span>
      ${buildRecommendationDetailsHtml(details)}
    </div>
  `;
}

function formatOperatorReviewLaneLabel(value) {
  const normalized = String(value || "").trim().toLowerCase();
  return {
    ready_to_apply: "Ready for review",
    tailor_then_apply: "Tailor then apply",
    review_before_action: "Review first",
    hold_or_skip: "Skip for now",
    source_watch: "Source watch",
  }[normalized] || "";
}

function buildOperatorReviewHtml(row, { simple = false } = {}) {
  const lane = String(row?.operator_review_lane || "").trim().toLowerCase();
  const label = formatOperatorReviewLaneLabel(lane);
  if (!label) return "";

  const reasonCodes = String(row?.operator_review_reason_codes || "").trim();
  const existingAction = String(row?.existing_action || row?.action || "").trim();
  const advisoryPriority = String(row?.advisory_priority || "").trim();
  const tailoringDecision = String(row?.tailoring_decision || "").trim();
  const packetAllowed = String(row?.packet_generation_allowed || "").trim();
  const packetBlockReason = String(row?.packet_generation_block_reason || "").trim();
  const criticDecision = String(row?.critic_decision || "").trim();
  const details = [
    { label: "Raw action", value: existingAction },
    { label: "Advisory priority", value: formatAdvisoryPriorityLabel(advisoryPriority) || advisoryPriority },
    { label: "Tailoring", value: formatTailoringDecisionLabel(tailoringDecision) || tailoringDecision },
    { label: "Reason", value: reasonCodes.split("|").filter(Boolean).map(formatDiagnosticReasonLabel).join(", ") },
    { label: "Raw reason codes", value: reasonCodes.replaceAll("|", ", ") },
    { label: "Raw packet flag", value: packetAllowed },
    { label: "Raw block reason", value: packetBlockReason },
    { label: "Critic", value: criticDecision },
  ];

  return `
    <div class="${simple ? "queue-operator-review queue-operator-review--simple" : "queue-operator-review"}">
      <span class="queue-operator-pill queue-operator-pill--${escapeHtml(lane)}">${escapeHtml(label)}</span>
      ${buildRecommendationDetailsHtml(details)}
    </div>
  `;
}

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

function getDefaultPipelineLlmActions() {
  return ["APPLY", "APPLY_REVIEW_VARIANTS"];
}

function getPipelineDeleteSeenDataValue() {
  return getBinaryToggleValue("pipelineDeleteSeenData");
}

function setPipelineDeleteSeenDataValue(value) {
  setBinaryToggleValue("pipelineDeleteSeenData", value);
}

function setPipelineRunOptions(value) {
  [
    "pipelinePlanningOnly",
    "pipelineGenerateTailoring",
    "pipelineGenerateLlmTailoring",
    "pipelineRefreshLlmTailoring",
    "pipelineGenerateLlmFallback",
    "pipelineGenerateLlmAdjudication",
  ].forEach((name) => {
    setBinaryToggleValue(name, value);
  });
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
  setBinaryToggleValue("pipelineGenerateLlmAdjudication", preset.generate_llm_adjudication);
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

function formatWorkflowSummaryCounts(counts = {}) {
  const entries = Object.entries(counts || {}).filter(([, value]) => Number(value || 0) > 0);
  if (!entries.length) return "none";
  return entries
    .map(([key, value]) => `${key.replaceAll("_", " ")}=${value}`)
    .join(", ");
}

function renderWorkflowSummaryMetric(label, value) {
  return `
    <div class="agentic-workflow-metric">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(value ?? 0)}</strong>
    </div>
  `;
}

function renderAgenticWorkflowSummaryPanel(workflowSummary = {}) {
  const panel = qs("agenticWorkflowSummaryPanel");
  if (!panel) return;

  const available = Boolean(workflowSummary?.available);
  const summary = workflowSummary?.summary_json && typeof workflowSummary.summary_json === "object"
    ? workflowSummary.summary_json
    : {};
  const markdown = String(workflowSummary?.summary_markdown || "").trim();

  if (!available && !Object.keys(summary).length && !markdown) {
    panel.classList.add("hidden");
    panel.innerHTML = "";
    return;
  }

  const missingArtifacts = Array.isArray(summary.missing_artifacts) ? summary.missing_artifacts : [];
  panel.classList.remove("hidden");
  panel.innerHTML = `
    <div class="agentic-workflow-header">
      <div>
        <h2>Agentic Workflow Summary</h2>
        <p>Read-only advisory rollup from the latest run artifacts.</p>
      </div>
      <span class="agentic-workflow-badge">Advisory</span>
    </div>
    <div class="agentic-workflow-grid">
      ${renderWorkflowSummaryMetric("Queue jobs", summary.total_queue_jobs)}
      ${renderWorkflowSummaryMetric("Packet jobs", summary.total_packet_jobs)}
      ${renderWorkflowSummaryMetric("Ready for review", summary.ready_to_apply_count)}
      ${renderWorkflowSummaryMetric("Tailor then apply", summary.tailor_then_apply_count)}
      ${renderWorkflowSummaryMetric("Skip for now", summary.hold_or_skip_count)}
      ${renderWorkflowSummaryMetric("Source watch", summary.source_watch_count)}
      ${renderWorkflowSummaryMetric("Fallback only", summary.fallback_only_count)}
      ${renderWorkflowSummaryMetric("Packet blocked", summary.packet_blocked_count)}
    </div>
    <div class="agentic-workflow-counts">
      <div><strong>Priority</strong><span>${escapeHtml(formatWorkflowSummaryCounts(summary.advisory_priority_counts))}</span></div>
      <div><strong>Tailoring</strong><span>${escapeHtml(formatWorkflowSummaryCounts(summary.tailoring_decision_counts))}</span></div>
      <div><strong>Operator lanes</strong><span>${escapeHtml(formatWorkflowSummaryCounts(summary.operator_review_lane_counts))}</span></div>
    </div>
    <div class="agentic-workflow-missing">
      <strong>Missing artifacts</strong>
      <span>${escapeHtml(missingArtifacts.length ? missingArtifacts.join(", ") : "none")}</span>
    </div>
    ${markdown ? `<details class="agentic-workflow-markdown"><summary>Markdown summary</summary><pre>${escapeHtml(markdown)}</pre></details>` : ""}
  `;
}

function formatWorkflowVerificationStatus(status) {
  const value = String(status || "unknown").trim().toLowerCase();
  if (value === "passed") return "Passed";
  if (value === "warning") return "Warning";
  if (value === "failed") return "Failed";
  return "Unknown";
}

function renderWorkflowVerificationList(values, emptyLabel = "none") {
  const entries = Array.isArray(values)
    ? values
    : Object.entries(values || {}).map(([key, value]) => `${key}: ${value}`);
  const cleanEntries = entries.map((value) => String(value || "").trim()).filter(Boolean);
  if (!cleanEntries.length) {
    return `<span class="agentic-workflow-verification-empty">${escapeHtml(emptyLabel)}</span>`;
  }
  return `
    <ul class="agentic-workflow-verification-list">
      ${cleanEntries.map((value) => `<li>${escapeHtml(value)}</li>`).join("")}
    </ul>
  `;
}

function renderWorkflowVerificationChecks(checks = {}) {
  const entries = Array.isArray(checks)
    ? checks.map((value, index) => [`check_${index + 1}`, value])
    : Object.entries(checks || {});
  if (!entries.length) {
    return `<span class="agentic-workflow-verification-empty">none</span>`;
  }
  return `
    <div class="agentic-workflow-verification-checks">
      ${entries.map(([key, value]) => `
        <div class="agentic-workflow-verification-check">
          <strong>${escapeHtml(String(key).replaceAll("_", " "))}</strong>
          <span>${escapeHtml(typeof value === "object" ? JSON.stringify(value) : value)}</span>
        </div>
      `).join("")}
    </div>
  `;
}

function renderAgenticWorkflowVerificationPanel(workflowVerification = {}) {
  const panel = qs("agenticWorkflowVerificationPanel");
  if (!panel) return;

  const available = Boolean(workflowVerification?.available);
  const verification = workflowVerification?.verification_json && typeof workflowVerification.verification_json === "object"
    ? workflowVerification.verification_json
    : {};

  if (!available && !Object.keys(verification).length) {
    panel.classList.add("hidden");
    panel.innerHTML = "";
    return;
  }

  const status = String(verification.validation_status || "unknown").trim().toLowerCase();
  const checkedArtifacts = Array.isArray(verification.checked_artifacts) ? verification.checked_artifacts : [];
  const missingArtifacts = Array.isArray(verification.missing_artifacts) ? verification.missing_artifacts : [];
  const reasonCodes = Array.isArray(verification.reason_codes) ? verification.reason_codes : [];
  const rowCounts = verification.row_counts && typeof verification.row_counts === "object" ? verification.row_counts : {};
  const consistencyChecks = verification.consistency_checks && typeof verification.consistency_checks === "object"
    ? verification.consistency_checks
    : {};
  const summary = verification.summary && typeof verification.summary === "object" ? verification.summary : {};

  panel.classList.remove("hidden");
  panel.innerHTML = `
    <div class="agentic-workflow-header">
      <div>
        <h2>Agentic Workflow Verification</h2>
        <p>Read-only diagnostic checks for the latest run artifacts.</p>
      </div>
      <span class="agentic-workflow-verification-status agentic-workflow-verification-status--${escapeHtml(status)}">
        ${escapeHtml(formatWorkflowVerificationStatus(status))}
      </span>
    </div>
    <div class="agentic-workflow-grid">
      ${renderWorkflowSummaryMetric("Strict mode", verification.strict ? "Yes" : "No")}
      ${renderWorkflowSummaryMetric("Checked artifacts", checkedArtifacts.length)}
      ${renderWorkflowSummaryMetric("Missing artifacts", missingArtifacts.length)}
      ${renderWorkflowSummaryMetric("Reason codes", reasonCodes.length)}
    </div>
    <div class="agentic-workflow-verification-sections">
      <div>
        <strong>Summary</strong>
        ${renderWorkflowVerificationList(summary)}
      </div>
      <div>
        <strong>Row counts</strong>
        ${renderWorkflowVerificationList(rowCounts)}
      </div>
      <div>
        <strong>Missing artifacts</strong>
        ${renderWorkflowVerificationList(missingArtifacts)}
      </div>
      <div>
        <strong>Reason codes</strong>
        ${renderWorkflowVerificationList(reasonCodes)}
      </div>
    </div>
    <details class="agentic-workflow-verification-details">
      <summary>Consistency checks</summary>
      ${renderWorkflowVerificationChecks(consistencyChecks)}
    </details>
  `;
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

function getPipelineVisibleGroupIndex(stage) {
  if (!stage) return 0;
  return PIPELINE_STAGE_TO_VISIBLE_GROUP[stage] ?? 0;
}

function getPipelineStageRenderModel(pipeline = {}, mode = "running") {
  const completedStages = new Set(Array.isArray(pipeline.completed_stages) ? pipeline.completed_stages : []);
  const status = pipeline.status || mode;
  const groups = PIPELINE_VISIBLE_STAGE_GROUPS.slice();
  let activeIndex = mode === "complete"
    ? groups.length - 1
    : getPipelineVisibleGroupIndex(pipeline.current_stage || "");

  if (status === "running" || mode === "running") {
    const allKnownStagesComplete = groups.every(
      (group) => group.stages.length && group.stages.every((stage) => completedStages.has(stage))
    );
    if (allKnownStagesComplete) {
      groups.push(PIPELINE_FINALIZING_FALLBACK);
      activeIndex = groups.length - 1;
    } else {
      const currentGroup = groups[activeIndex];
      const currentComplete = currentGroup?.stages.length
        && currentGroup.stages.every((stage) => completedStages.has(stage));
      if (currentComplete) {
        const nextIncompleteIndex = groups.findIndex(
          (group, index) => index > activeIndex
            && !group.stages.every((stage) => completedStages.has(stage))
        );
        if (nextIncompleteIndex >= 0) activeIndex = nextIncompleteIndex;
      }
    }
  }

  return { groups, activeIndex, completedStages, status };
}

function buildPipelineVisibleStageStepsHtml(pipeline = {}, mode = "running") {
  const { groups, activeIndex, completedStages, status } = getPipelineStageRenderModel(pipeline, mode);

  return groups.map((group, index) => {
    const groupHasCompletedStage = group.stages.length > 0
      && group.stages.every((stage) => completedStages.has(stage));
    const isCurrentGroup = index === activeIndex;
    let stateClass = "is-pending";
    let marker = "";
    let indicatorLabel = "Pending";

    if (!group.isUiFallback && (mode === "complete" || status === "succeeded" || index < activeIndex || groupHasCompletedStage)) {
      stateClass = "is-complete";
      marker = "✓";
      indicatorLabel = "Complete";
    } else if ((mode === "failed" || status === "failed" || status === "stopped") && isCurrentGroup) {
      stateClass = "is-error";
      marker = "!";
      indicatorLabel = "Needs attention";
    } else if ((mode === "running" || status === "running") && isCurrentGroup) {
      stateClass = "is-active";
      indicatorLabel = "Current";
    }

    return `
      <div class="workflow-step pipeline-step ${stateClass}" data-workflow-step-index="${index}">
        <span class="workflow-step__indicator pipeline-step-marker" aria-label="${escapeHtml(indicatorLabel)}">${escapeHtml(marker)}</span>
        <span class="workflow-step__label pipeline-step-label">
          ${escapeHtml(group.label)}
          ${group.description ? `<small>${escapeHtml(group.description)}</small>` : ""}
        </span>
      </div>
    `;
  }).join("");
}

function getWorkflowStepPositionClass(index, activeIndex) {
  const distance = index - activeIndex;
  if (distance < -1 || distance > 2) return "is-hidden";
  if (distance === -1) return "is-previous";
  if (distance === 0) return "is-active-position";
  if (distance === 1) return "is-next";
  return "is-upcoming";
}

function renderPipelineStageStepper(pipeline, targetId = "pipelineStageStepper", mode = "running") {
  const target = qs(targetId);
  if (!target) return;
  const model = getPipelineStageRenderModel(pipeline, mode);
  const currentGroupIndex = model.activeIndex;

  if (target.children.length !== model.groups.length) {
    target.innerHTML = buildPipelineVisibleStageStepsHtml(pipeline, mode);
  }

  target.style.setProperty("--workflow-active-index", String(currentGroupIndex));
  target.dataset.activeIndex = String(currentGroupIndex);

  const completedStages = model.completedStages;
  const status = model.status;
  Array.from(target.children).forEach((step, index) => {
    const group = model.groups[index];
    const groupHasCompletedStage = group.stages.length > 0
      && group.stages.every((stage) => completedStages.has(stage));
    const isCurrentGroup = index === currentGroupIndex;
    const isComplete = !group.isUiFallback
      && (mode === "complete" || status === "succeeded" || index < currentGroupIndex || groupHasCompletedStage);
    const isError = (mode === "failed" || status === "failed" || status === "stopped") && isCurrentGroup;
    const isActive = !isComplete && !isError && isCurrentGroup;
    const stateClass = isComplete ? "is-complete" : (isError ? "is-error" : (isActive ? "is-active" : "is-pending"));
    const marker = isComplete ? "✓" : (isError ? "!" : "");
    const indicatorLabel = isComplete ? "Complete" : (isError ? "Needs attention" : (isActive ? "Current" : "Pending"));
    const indicator = step.querySelector(".workflow-step__indicator");

    step.className = `workflow-step pipeline-step ${stateClass} ${getWorkflowStepPositionClass(index, currentGroupIndex)}`;
    step.setAttribute("aria-hidden", "false");
    if (indicator) {
      indicator.textContent = marker;
      indicator.setAttribute("aria-label", indicatorLabel);
    }
  });

  const viewport = target.closest(".workflow-step-viewport");
  const activeStep = target.querySelector(".workflow-step.is-active");
  if (viewport && activeStep) {
    const viewportRect = viewport.getBoundingClientRect();
    const activeRect = activeStep.getBoundingClientRect();
    if (activeRect.top < viewportRect.top || activeRect.bottom > viewportRect.bottom) {
      activeStep.scrollIntoView({ block: "nearest", behavior: "smooth" });
    }
  }
}

function getPipelineSuccessKey(pipeline = {}) {
  return pipeline.run_id || pipeline.finished_at || pipeline.started_at || pipeline.status || "succeeded";
}

function publishPipelineDataVersion(pipeline = {}) {
  const version = getPipelineSuccessKey(pipeline);
  if (!version || version === "succeeded") return "";

  try {
    window.localStorage.setItem(PIPELINE_DATA_VERSION_STORAGE_KEY, version);
  } catch {
    // ignore localStorage failures
  }

  return version;
}

function refreshTablesAfterPipelineSuccess(pipeline = {}) {
  const version = publishPipelineDataVersion(pipeline);
  if (!version || state.lastPipelineTableRefreshKey === version) return;

  state.lastPipelineTableRefreshKey = version;
  queueTableState.page = 1;

  loadStatus().catch((err) => {
    console.warn("Failed to refresh dashboard stats after pipeline success", err);
  });
  reloadCurrentTable(1).catch((err) => {
    console.warn("Failed to refresh dashboard table after pipeline success", err);
  });
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

function derivePipelineCompletionSummary(pipeline = {}) {
  const counts = pipeline.counts || {};
  const jobsCollected = Number(counts.scraped_jobs ?? 0);
  const passedFiltersValue = counts.filtered_jobs;
  const jobsPassedFilters = passedFiltersValue === undefined || passedFiltersValue === null
    ? null
    : Number(passedFiltersValue);
  const planningJobs = Number(pipeline.final_job_count ?? counts.rag_export_count ?? 0);
  const isEmptyResult = planningJobs === 0;
  const rejectionDefinitions = [
    ["Role or title mismatch", counts.filter_title_mismatch],
    ["Location mismatch", counts.filter_location_not_us],
    ["Outside the freshness window", counts.filter_not_recent],
    ["Missing posting timestamp", counts.filter_missing_timestamp],
    ["Excluded keyword", counts.filter_excluded_keyword],
  ];
  const rejectionReasons = rejectionDefinitions
    .map(([label, value]) => ({ label, count: Number(value ?? 0) }))
    .filter((item) => Number.isFinite(item.count) && item.count > 0)
    .sort((left, right) => right.count - left.count);

  let emptyResultReason = "No detailed rejection breakdown was recorded for this run.";
  if (jobsCollected > 0 && jobsPassedFilters === 0 && rejectionReasons.length) {
    emptyResultReason = "No jobs passed the configured role, location, and freshness filters.";
  } else if (jobsPassedFilters === null) {
    emptyResultReason = "The run completed without a recorded filtering count. Review run details before interpreting the result.";
  } else if (jobsPassedFilters > 0 && planningJobs === 0) {
    emptyResultReason = "Jobs passed filtering, but none remained available for planning.";
  }

  return {
    jobsCollected,
    jobsPassedFilters,
    planningJobs,
    isEmptyResult,
    rejectionReasons,
    emptyResultReason,
  };
}

function renderPipelineSuccessSummary(pipeline = {}) {
  const summary = derivePipelineCompletionSummary(pipeline);
  const collectedDenominator = Math.max(summary.jobsCollected, 1);
  const metrics = [
    ["Collected", summary.jobsCollected],
    ["Passed filters", summary.jobsPassedFilters],
    ["Planning jobs", summary.planningJobs],
  ];
  const metricsHtml = metrics.map(([label, value]) => `
    <div class="pipeline-result-metric">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(value === null ? "Not recorded" : Number(value).toLocaleString())}</strong>
    </div>
  `).join("");
  const reasonsHtml = summary.rejectionReasons.length
    ? `
      <div class="pipeline-empty-reasons__title">Top reasons jobs were excluded</div>
      <ul>
        ${summary.rejectionReasons.slice(0, 4).map((reason) => {
          const ratio = Math.min((reason.count / collectedDenominator) * 100, 100);
          return `
          <li>
            <div class="pipeline-empty-reason-row">
              <span>${escapeHtml(reason.label)}</span>
              <strong>${escapeHtml(reason.count.toLocaleString())}</strong>
            </div>
            <div class="pipeline-empty-reason-bar" aria-hidden="true">
              <span style="--pipeline-reason-ratio: ${ratio.toFixed(3)}%"></span>
            </div>
          </li>
        `;
        }).join("")}
      </ul>
    `
    : `<div class="pipeline-empty-reasons__unavailable">${escapeHtml(summary.emptyResultReason)}</div>`;

  qs("pipelineSuccessTitle").textContent = summary.isEmptyResult
    ? "No jobs matched this run"
    : "Pipeline run is ready";
  qs("pipelineSuccessText").textContent = summary.isEmptyResult
    ? summary.emptyResultReason
    : "Your job results and planning artifacts are ready to review.";
  qs("pipelineResultMetrics").innerHTML = metricsHtml;
  qs("pipelineEmptyReasons").innerHTML = reasonsHtml;
  qs("pipelineEmptyReasons").classList.toggle("hidden", !summary.isEmptyResult);
  qs("pipelineOverlaySuccess").classList.toggle("is-empty-result", summary.isEmptyResult);
  qs("pipelineOverlayCard").classList.toggle("is-empty-result", summary.isEmptyResult);
  qs("pipelineSuccessPlanningBtn").classList.toggle("hidden", summary.isEmptyResult);
  qs("pipelineSuccessDetailsBtn").classList.toggle("hidden", !summary.isEmptyResult);
  qs("pipelineSuccessRunAgainBtn").classList.toggle("hidden", !summary.isEmptyResult);
  qs("pipelineSuccessPlanningBtn").disabled = false;
  renderPipelineStageStepper({ ...pipeline, status: "succeeded" }, "pipelineSuccessStageStepper", "complete");
}

function renderPipelineFailureSummary(pipeline = {}) {
  const currentStage = pipeline.current_stage ? titleCaseStage(pipeline.current_stage) : "";
  const metaBits = [
    pipeline.started_at ? `Started: ${formatDateTime(pipeline.started_at)}` : "",
    pipeline.finished_at ? `Finished: ${formatDateTime(pipeline.finished_at)}` : "",
    currentStage ? `Stage: ${currentStage}` : "",
    pipeline.return_code !== undefined && pipeline.return_code !== null
      ? `Return code: ${pipeline.return_code}`
      : "",
  ].filter(Boolean);

  const metaLine = metaBits.length
    ? `<div class="pipeline-success-summary-text">${escapeHtml(metaBits.join(" · "))}</div>`
    : "";

  qs("pipelineFailureTitle").textContent = "Pipeline could not finish";
  qs("pipelineFailureText").textContent = "The run stopped before completion. Review diagnostics for technical details.";
  qs("pipelineFailureSummary").innerHTML = metaLine;
  qs("pipelineFailureReason").innerHTML = `
    <div class="pipeline-success-summary-text">
      No application actions were taken. Technical details remain available in pipeline diagnostics.
    </div>
  `;
  renderPipelineStageStepper(pipeline, "pipelineFailureStageStepper", "failed");
}

function showPipelineFailureOverlay(pipeline = {}) {
  const overlay = qs("pageLoadingOverlay");
  const loadingPane = qs("pipelineOverlayLoading");
  const successPane = qs("pipelineOverlaySuccess");
  const failurePane = qs("pipelineOverlayFailure");
  const failureKey = getPipelineSuccessKey(pipeline);

  if (state.pipelineFailureVisible && state.currentPipelineFailureKey === failureKey) {
    overlay.classList.remove("hidden");
    return;
  }

  loadingPane.classList.add("hidden");
  successPane.classList.add("hidden");
  failurePane.classList.remove("hidden");
  qs("pipelineOverlayCard").classList.remove("is-success");
  qs("pipelineOverlayCard").classList.remove("is-empty-result");
  qs("pipelineOverlayCard").classList.add("is-error");

  state.pipelineSuccessVisible = false;
  state.currentPipelineSuccessKey = null;
  state.pipelineFailureVisible = true;
  state.currentPipelineFailureKey = failureKey;

  renderPipelineFailureSummary(pipeline);
  const status = String(pipeline.status || "failed").toLowerCase();
  if (status === "cancelled" || status === "canceled" || status === "stopped") {
    qs("pipelineFailureTitle").textContent = "Pipeline run was cancelled";
    qs("pipelineFailureText").textContent = "The run stopped before completion. No application actions were taken.";
  }
  overlay.classList.remove("hidden");
  document.body.classList.add("pipeline-workflow-open");
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
  qs("pipelineOverlayCard").classList.remove("is-error");
  qs("pipelineOverlayCard").classList.add("is-success");

  state.pipelineSuccessVisible = true;
  state.currentPipelineSuccessKey = successKey;

  renderPipelineSuccessSummary(pipeline);
  overlay.classList.remove("hidden");
  document.body.classList.add("pipeline-workflow-open");
}

function showPageLoadingOverlay(title, text, pipeline = {}) {
  const overlay = qs("pageLoadingOverlay");
  const loadingPane = qs("pipelineOverlayLoading");
  const successPane = qs("pipelineOverlaySuccess");
  const failurePane = qs("pipelineOverlayFailure");
  state.pipelineSuccessVisible = false;
  state.currentPipelineSuccessKey = null;
  state.pipelineFailureVisible = false;
  state.currentPipelineFailureKey = null;

  loadingPane.classList.remove("hidden");
  successPane.classList.add("hidden");
  failurePane.classList.add("hidden");
  qs("pipelineOverlayCard").classList.remove("is-success", "is-error", "is-empty-result");

  qs("pageLoadingTitle").textContent = "Running live job pipeline";
  qs("pageLoadingText").textContent = pipeline.status === "running"
    ? "Collecting jobs, filtering duplicates, scoring fit, and preparing planning artifacts."
    : (text || "Preparing your private pipeline run.");
  qs("pipelineLoadingMeta").textContent = buildPipelineMetaText(pipeline);
  renderPipelineCounts(pipeline);
  renderPipelineStageStepper(pipeline);

  overlay.classList.remove("hidden");
  document.body.classList.add("pipeline-workflow-open");
}

function hidePageLoadingOverlay() {
  state.pipelineSuccessVisible = false;
  state.currentPipelineSuccessKey = null;
  state.pipelineFailureVisible = false;
  state.currentPipelineFailureKey = null;
  qs("pageLoadingOverlay").classList.add("hidden");
  document.body.classList.remove("pipeline-workflow-open");
}

function renderPipelineStatus(payload) {
  const pipeline = (payload && payload.pipeline) || {};
  const runBtn = qs("runPipelineBtn");
  const meta = qs("pipelineRunMeta");

  if (!runBtn || !meta) return;

  const status = pipeline.status || "idle";
  meta.textContent = buildPipelineMetaText(pipeline);
  const overlayEl = qs("pageLoadingOverlay");
  const pendingStart = hasPipelinePendingSuccess();

  const terminalFailure = ["failed", "cancelled", "canceled", "stopped"].includes(status);
  const runningLike = ["queued", "starting", "running"].includes(status);

  if (pendingStart && status !== "succeeded" && !terminalFailure) {
    showPageLoadingOverlay(
      "Running live pipeline...",
      pipeline.stage_message || "Starting pipeline run...",
      {
        ...pipeline,
        status: "running",
        current_stage: pipeline.current_stage || "startup",
        stage_message: pipeline.stage_message || "Launching pipeline subprocess",
        stage_order: pipeline.stage_order || DEFAULT_STAGE_ORDER,
        completed_stages: pipeline.completed_stages || [],
        counts: pipeline.counts || {},
      }
    );
    runBtn.disabled = true;
    runBtn.textContent = "Pipeline Running...";
    return;
  }

  if (runningLike) {
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
    refreshTablesAfterPipelineSuccess(pipeline);

    const successKey = getPipelineSuccessKey(pipeline);
    const overlayIsVisible = !overlayEl.classList.contains("hidden");
    if (hasPipelinePendingSuccess() || overlayIsVisible || state.pipelineSuccessVisible) {
      markPipelineSuccessShown(successKey);
      clearPipelinePendingSuccess();
      showPipelineSuccessOverlay(pipeline);
    }

    return;
  }

  if (terminalFailure) {
    runBtn.disabled = false;
    runBtn.textContent = "Run Live Pipeline";

    const overlayIsVisible = !qs("pageLoadingOverlay").classList.contains("hidden");
    const shouldShowFailure =
      hasPipelinePendingSuccess() || overlayIsVisible || state.pipelineFailureVisible;

    if (shouldShowFailure) {
      clearPipelinePendingSuccess();
      showPipelineFailureOverlay(pipeline);
    }

    return;
  }

  runBtn.disabled = false;
  runBtn.textContent = "Run Live Pipeline";
  if (!overlayEl.classList.contains("hidden")) {
    qs("pipelineLoadingMeta").textContent = "Waiting for the latest pipeline status. This window will remain open.";
  }
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

window.openApplyLensPipelineConfig = openPipelineConfigModal;

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
  const effectiveLlmActions = llmActions.length ? llmActions : getDefaultPipelineLlmActions();
  const paths = derivePipelinePaths(DEFAULT_OUTPUT_DIR);

  return {
    job_limit: Number(qs("pipelineJobLimitInput").value || 50),
    job_packet_limit: Number(qs("pipelineJobPacketLimitInput").value || 0),
    output_dir: paths.output_dir,
    log_path: paths.log_path,
    llm_actions: effectiveLlmActions,
    planning_only: getBinaryToggleBool("pipelinePlanningOnly"),
    generate_tailoring: false,
    generate_llm_tailoring: false,
    refresh_llm_tailoring: false,
    generate_llm_fallback: getBinaryToggleBool("pipelineGenerateLlmFallback"),
    generate_llm_adjudication: getBinaryToggleBool("pipelineGenerateLlmAdjudication"),
    delete_seen_data: getPipelineDeleteSeenDataValue(),
  };
}

function renderPipelineConfirmSummary(config) {
  const buildBoolTile = (label, enabled) => `
    <div class="pipeline-confirm-flag ${enabled ? "is-enabled" : "is-disabled"}">
      <div class="pipeline-confirm-flag-copy">
        <div class="pipeline-confirm-flag-label">${escapeHtml(label)}</div>
      </div>
      <div class="pipeline-confirm-flag-pill">${enabled ? "Yes" : "No"}</div>
    </div>
  `;

  const buildMetaRow = (label, value, extraClass = "") => `
    <div class="pipeline-confirm-meta-row">
      <div class="pipeline-confirm-meta-label">${escapeHtml(label)}</div>
      <div class="pipeline-confirm-meta-value ${extraClass}">${escapeHtml(String(value ?? "-"))}</div>
    </div>
  `;

  qs("pipelineConfirmSummary").innerHTML = `
    <div class="pipeline-confirm-shell">
      <section class="pipeline-confirm-hero">
        <div class="pipeline-confirm-hero-badge">Launch review</div>
        <div class="pipeline-confirm-hero-title">Ready to start this pipeline run</div>
        <div class="pipeline-confirm-hero-copy">
          Review the scope, enabled actions, and run options below before launch.
        </div>

        <div class="pipeline-confirm-hero-stats">
          <div class="pipeline-confirm-stat">
            <div class="pipeline-confirm-stat-label">Job limit</div>
            <div class="pipeline-confirm-stat-value">${escapeHtml(String(config.job_limit ?? 0))}</div>
          </div>
          <div class="pipeline-confirm-stat">
            <div class="pipeline-confirm-stat-label">Packet limit</div>
            <div class="pipeline-confirm-stat-value">${escapeHtml(String(config.job_packet_limit ?? 0))}</div>
          </div>
          <div class="pipeline-confirm-stat">
            <div class="pipeline-confirm-stat-label">Run mode</div>
            <div class="pipeline-confirm-stat-value">${config.planning_only ? "Plan only" : "Scan + Plan"}</div>
          </div>
        </div>
      </section>

      <div class="pipeline-confirm-grid">
        <section class="pipeline-confirm-panel pipeline-confirm-panel--scope">
          <div class="pipeline-confirm-panel-title">Run scope</div>
          ${buildMetaRow("Job limit", config.job_limit)}
          ${buildMetaRow("Job packet limit", config.job_packet_limit)}
        </section>

        <section class="pipeline-confirm-panel pipeline-confirm-panel--scope">
          <div class="pipeline-confirm-panel-title">Planning</div>
          ${buildMetaRow("Run mode", config.planning_only ? "Plan only" : "Scan + Plan")}
          ${buildMetaRow("Rerun seen jobs", config.delete_seen_data === "yes" ? "Yes" : "No")}
        </section>
      </div>

      <section class="pipeline-confirm-panel pipeline-confirm-panel--flags">
        <div class="pipeline-confirm-panel-title">Run options</div>
        <div class="pipeline-confirm-flag-grid">
          ${buildBoolTile("AI review", config.generate_llm_adjudication)}
          ${buildBoolTile("Backup ranking", config.generate_llm_fallback)}
        </div>
      </section>
    </div>
  `;
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
      const status = String(data?.pipeline?.status || "").toLowerCase();
      if (["succeeded", "failed", "cancelled", "canceled", "stopped"].includes(status)) {
        stopPipelinePolling();
        await loadStatus();
        await reloadCurrentTable();
      }
    } catch (err) {
      console.error(err);
      const meta = qs("pipelineLoadingMeta");
      if (meta) {
        meta.textContent = "Temporarily unable to refresh pipeline status. Retrying automatically…";
      }
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
  const label = escapeHtml(row.application_label || (isApplied ? "Reviewed" : "Review job"));
  const buttonClass = isApplied
    ? "job-apply-btn review-action-button review-action-button--disabled applied-btn"
    : "job-apply-btn review-action-button review-action-button--available apply-btn";
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

function buildQueueJobSummaryHtml(row, { simple = false } = {}) {
  const company = escapeHtml(row.job_company || "");
  return `
    <div class="${simple ? "queue-simple-job-cell" : "queue-job-summary"}">
      <div class="queue-simple-company">${company || "-"}</div>
      <div class="queue-simple-title">${buildJobTitleCellHtml(row, { simple })}</div>
    </div>
  `;
}

function buildQueueRecommendationCellHtml(row) {
  const action = escapeHtml(formatQueueActionLabel(row.action) || "-");
  const tone = escapeHtml(getRecommendationTone(row.action));
  const advisoryReasons = String(row?.advisory_reason_codes || "")
    .split("|")
    .filter(Boolean)
    .map(formatDiagnosticReasonLabel)
    .join(", ");
  const tailoringReasons = String(row?.tailoring_reason_codes || "")
    .split("|")
    .filter(Boolean)
    .map(formatDiagnosticReasonLabel)
    .join(", ");
  const operatorReasons = String(row?.operator_review_reason_codes || "")
    .split("|")
    .filter(Boolean)
    .map(formatDiagnosticReasonLabel)
    .join(", ");
  const details = buildRecommendationDetailsHtml([
    { label: "Recommendation", value: formatQueueActionLabel(row.action) },
    { label: "Tailoring note", value: formatTailoringDecisionLabel(row.tailoring_decision) },
    { label: "Review lane", value: formatOperatorReviewLaneLabel(row.operator_review_lane) },
    { label: "Why", value: advisoryReasons || tailoringReasons || operatorReasons },
    { label: "Advanced/debug codes", value: [row.action, row.advisory_reason_codes, row.tailoring_reason_codes, row.operator_review_reason_codes].filter(Boolean).join(" · ") },
  ]);
  return `
    <div class="queue-recommendation-summary">
      <span class="pill recommendation-chip recommendation-chip--${tone}">${action}</span>
      ${details}
    </div>
  `;
}

function buildSelectedResumeHtml(row) {
  return buildResumeCellHtml(row.operator_selected_resume || row.winner_resume, {
    emptyLabel: "-",
    wrap: true,
  });
}

function buildQueueRowDetailedHtml(row) {
  const queueRank = escapeHtml(row.queue_rank || "");
  const applyButtonHtml = buildApplicationButtonHtml(row);

  return `
    <tr>
      <td>${queueRank}</td>
      <td class="title-cell">${buildJobTitleCellHtml(row, { includeLocation: false })}</td>
      <td>${escapeHtml(row.job_company || "-")}</td>
      <td>${escapeHtml(row.job_location || "-")}</td>
      <td>${buildPostedAtCellHtml(row)}</td>
      <td>${buildQueueRecommendationCellHtml(row)}</td>
      <td>${buildPacketStatusChipHtml(row) || "-"}</td>
      <td>${escapeHtml(formatScore100(row.winner_score))}</td>
      <td>${buildSelectedResumeHtml(row)}</td>
      <td>${buildResumeCellHtml(row.runner_up_resume || "-", { emptyLabel: "-", wrap: true })}</td>
      <td>${escapeHtml(row.score_gap || "-")}</td>
      <td>${escapeHtml(row.missing_requirement_count || "-")}</td>
      <td>${escapeHtml(formatOperatorDecisionLabel(row.operator_decision) || formatOperatorReviewLaneLabel(row.operator_review_lane) || "-")}</td>
      <td>${escapeHtml(formatDiagnosticReasonLabel(row.queue_priority_reason) || "-")}</td>
      <td class="apply-cell sticky-apply-col">${applyButtonHtml}</td>
    </tr>
  `;
}

function buildQueueRowSimpleHtml(row) {
  const queueRank = escapeHtml(row.queue_rank || "");
  const applyButtonHtml = buildApplicationButtonHtml(row);

  return `
    <tr>
      <td>${queueRank}</td>
      <td class="title-cell queue-simple-job-cell">
        ${buildQueueJobSummaryHtml(row, { simple: true })}
      </td>
      <td>${buildPostedAtCellHtml(row)}</td>
      <td>${buildQueueRecommendationCellHtml(row)}</td>
      <td>${buildPacketStatusChipHtml(row) || "-"}</td>
      <td>${escapeHtml(formatScore100(row.winner_score))}</td>
      <td>${buildSelectedResumeHtml(row)}</td>
      <td class="apply-cell sticky-apply-col">${applyButtonHtml}</td>
    </tr>
  `;
}

function buildPaginationSequence(currentPage, totalPages) {
  const pages = [];
  if (totalPages <= 7) {
    for (let page = 1; page <= totalPages; page += 1) {
      pages.push(page);
    }
    return pages;
  }

  pages.push(1);

  const start = Math.max(2, currentPage - 1);
  const end = Math.min(totalPages - 1, currentPage + 1);

  if (start > 2) pages.push("ellipsis-left");
  for (let page = start; page <= end; page += 1) {
    pages.push(page);
  }
  if (end < totalPages - 1) pages.push("ellipsis-right");

  pages.push(totalPages);
  return pages;
}

function applyQueuePaginationPayload(data) {
  queueTableState.page = Number(data.page || 1);
  queueTableState.pageSize = Number(data.page_size || 15);
  queueTableState.totalCount = Number(data.total_count ?? data.count ?? 0);
  queueTableState.totalPages = Number(data.total_pages || 1);
  queueTableState.hasPrevPage = Boolean(data.has_prev_page);
  queueTableState.hasNextPage = Boolean(data.has_next_page);
}

function renderQueuePagination() {
  const metaEl = qs("queuePaginationMeta");
  const actionsEl = qs("queuePaginationActions");
  if (!metaEl || !actionsEl) return;

  const totalCount = queueTableState.totalCount || 0;
  const totalPages = Math.max(queueTableState.totalPages || 1, 1);
  const currentPage = Math.min(Math.max(queueTableState.page || 1, 1), totalPages);
  const pageSize = Math.max(queueTableState.pageSize || 15, 1);

  if (totalCount === 0) {
    metaEl.textContent = "Page 1 of 1 · 0 jobs";
    actionsEl.innerHTML = "";
    return;
  }

  const startRow = (currentPage - 1) * pageSize + 1;
  const endRow = Math.min(startRow + (queueTableState.rows?.length || 0) - 1, totalCount);

  metaEl.textContent = `Page ${currentPage} of ${totalPages} · Showing ${startRow}-${endRow} of ${totalCount} jobs`;

  const sequence = buildPaginationSequence(currentPage, totalPages);
  const buttons = [];

  buttons.push(`
    <button
      type="button"
      class="application-pagination-btn"
      data-page-target="${currentPage - 1}"
      ${queueTableState.hasPrevPage ? "" : "disabled"}
    >
      Prev
    </button>
  `);

  sequence.forEach((item) => {
    if (typeof item === "string" && item.startsWith("ellipsis")) {
      buttons.push(`<span class="application-pagination-ellipsis">…</span>`);
      return;
    }

    buttons.push(`
      <button
        type="button"
        class="application-pagination-btn ${item === currentPage ? "is-active" : ""}"
        data-page-target="${item}"
      >
        ${item}
      </button>
    `);
  });

  buttons.push(`
    <button
      type="button"
      class="application-pagination-btn"
      data-page-target="${currentPage + 1}"
      ${queueTableState.hasNextPage ? "" : "disabled"}
    >
      Next
    </button>
  `);

  actionsEl.innerHTML = buttons.join("");
}

function renderQueueRows(rows, metaLabel) {
  queueTableState.rows = Array.isArray(rows) ? rows.slice() : [];
  queueTableState.metaLabel = metaLabel;

  const tbody = qs("queueTableBody");
  const displayRows = sortRows(queueTableState.rows, QUEUE_SORT_COLUMNS, queueTableState.sort);
  const modeLabel = state.executiveViewMode === "simple" ? "Simple mode" : "Detailed mode";

  renderQueueHeaders();

  if (!displayRows.length) {
    const colspan = state.executiveViewMode === "simple" ? 8 : 15;
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
  renderQueuePagination();
  window.clearTableWrapLoading?.(tbody);
  initResizableTableColumns("queueTable", "queueTableColumnWidths");
}

function buildBrowseUrl(pageOverride = null) {
  const actions = getMultiSelectValues("actionFilter");
  const preferenceIds = getMultiSelectValues("preferenceFilter");
  const undecidedOnly = getBinaryToggleBool("executiveUndecidedOnly") ? "true" : "";
  const limit = qs("limitInput").value || "15";
  const page = pageOverride ?? queueTableState.page ?? 1;

  const params = new URLSearchParams();
  appendMultiValueParams(params, "action", actions);
  appendMultiValueParams(params, "preference_id", preferenceIds);
  if (undecidedOnly) params.set("undecided_only", undecidedOnly);
  params.set("limit", limit);
  params.set("page", String(page));

  return `/browse?${params.toString()}`;
}

async function loadStatus() {
  const data = await fetchJson("/status");
  renderStats(data);
}

async function loadBrowse(pageOverride = null) {
  state.currentMode = "browse";
  state.workflowView = null;
  setQueueLoadingState("Loading executive jobs...");

  await new Promise((resolve) => window.requestAnimationFrame(resolve));

  try {
    const targetPage = pageOverride ?? queueTableState.page ?? 1;
    const url = buildBrowseUrl(targetPage);
    const data = await fetchJson(url);

    applyQueuePaginationPayload(data);

    const totalCount = data.total_count ?? data.count ?? 0;

    renderQueueRows(
      data.rows || [],
      `Browse view · ${totalCount} total job${totalCount === 1 ? "" : "s"}`
    );
  } catch (err) {
    window.clearTableWrapLoading?.(qs("queueTableBody"));
    throw err;
  }
}

async function loadWorkflow(view) {
  state.currentMode = "workflow";
  state.workflowView = view;
  setQueueLoadingState(`Loading ${String(view || "workflow").replaceAll("_", " ")}...`);

  await new Promise((resolve) => window.requestAnimationFrame(resolve));

  try {
    const limit = qs("limitInput").value || "25";
    const params = new URLSearchParams({
      view,
      limit,
    });

    const data = await fetchJson(`/workflow?${params.toString()}`);
    applyQueuePaginationPayload(data);

    const count = data.count ?? 0;

    renderQueueRows(
      data.rows || [],
      `Workflow view: ${view} · ${count} row${count === 1 ? "" : "s"}`
    );
  } catch (err) {
    window.clearTableWrapLoading?.(qs("queueTableBody"));
    throw err;
  }
}

async function loadAppliedJobs(pageOverride = null) {
  state.currentMode = "applied_jobs";
  state.workflowView = null;
  setQueueLoadingState("Loading applied jobs...");

  await new Promise((resolve) => window.requestAnimationFrame(resolve));

  try {
    const targetPage = pageOverride ?? queueTableState.page ?? 1;
    const limit = qs("limitInput").value || "15";
    const data = await fetchJson(
      `/applied-jobs?limit=${encodeURIComponent(limit)}&page=${encodeURIComponent(targetPage)}`
    );

    applyQueuePaginationPayload(data);

    const totalCount = data.total_count ?? data.count ?? 0;

    renderQueueRows(
      data.rows || [],
      `Applied jobs · ${totalCount} total job${totalCount === 1 ? "" : "s"}`
    );
  } catch (err) {
    window.clearTableWrapLoading?.(qs("queueTableBody"));
    throw err;
  }
}

async function reloadCurrentTable(pageOverride = null) {
  if (state.currentMode === "applied_jobs") {
    await loadAppliedJobs(pageOverride);
  } else if (state.currentMode === "workflow" && state.workflowView) {
    await loadWorkflow(state.workflowView);
  } else {
    await loadBrowse(pageOverride);
  }
}

function clearFilters() {
  clearMultiSelect("actionFilter");
  resetMultiSelectToAll("preferenceFilter");
  setBinaryToggleValue("executiveUndecidedOnly", false);
  qs("limitInput").value = "15";
  queueTableState.page = 1;
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

  const runPipelineBtn = qs("runPipelineBtn");
    if (runPipelineBtn) {
      runPipelineBtn.addEventListener("click", () => {
        openPipelineConfigModal();
      });
    }

  qs("closePipelineConfigModalBtn")?.addEventListener("click", closePipelineConfigModal);
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
    let pipelineStarted = false;
    try {
      const config = state.pendingPipelineConfig || collectPipelineConfig();
      closePipelineConfirmModal();
      markPipelinePendingSuccess();
      window.localStorage.removeItem("applylens_new_user_empty_state");
      document.body.classList.remove("app-new-user-empty");

      showPageLoadingOverlay("Running live pipeline...", "Starting pipeline run...", {
        status: "running",
        current_stage: "startup",
        stage_message: "Launching pipeline subprocess",
        stage_order: DEFAULT_STAGE_ORDER,
        completed_stages: [],
        counts: {},
      });

      await postJson("/pipeline/run", config);
      pipelineStarted = true;
      startPipelinePolling();
      try {
        await loadPipelineStatus();
      } catch (statusErr) {
        console.error(statusErr);
        qs("pipelineLoadingMeta").textContent = "Pipeline started. Waiting for the latest status…";
      }
    } catch (err) {
      if (!pipelineStarted) {
        clearPipelinePendingSuccess();
        showPipelineFailureOverlay({
          status: "failed",
          current_stage: "startup",
          error: extractErrorMessage(err),
        });
      }
    }
  });

  qs("pipelineSuccessOkBtn").addEventListener("click", () => {
    state.acknowledgedPipelineSuccessKey = state.currentPipelineSuccessKey;
    hidePageLoadingOverlay();
  }); 
  qs("pipelineFailureOkBtn").addEventListener("click", () => {
    hidePageLoadingOverlay();
  });
  qs("pipelineSuccessPlanningBtn").addEventListener("click", () => {
    qs("pipelineSuccessPlanningBtn").disabled = true;
    state.acknowledgedPipelineSuccessKey = state.currentPipelineSuccessKey;
    window.location.href = "/planning";
  });
  qs("pipelineSuccessDetailsBtn").addEventListener("click", () => {
    state.acknowledgedPipelineSuccessKey = state.currentPipelineSuccessKey;
    window.location.href = "/profile?tab=pipeline-runs";
  });
  qs("pipelineSuccessRunAgainBtn").addEventListener("click", () => {
    state.acknowledgedPipelineSuccessKey = state.currentPipelineSuccessKey;
    hidePageLoadingOverlay();
    openPipelineConfigModal();
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
  const outputDirInput = qs("pipelineOutputDirInput");
  if (outputDirInput) {
    outputDirInput.addEventListener("input", syncPipelinePathPreview);
  }

  qs("pipelineSelectAllActionsBtn")?.addEventListener("click", () => {
    setPipelineLlmActions(["APPLY", "APPLY_REVIEW_VARIANTS", "MAYBE_TAILOR", "SKIP_FOR_NOW"]);
  });

  qs("pipelineClearAllActionsBtn")?.addEventListener("click", () => {
    setPipelineLlmActions([]);
  });

  qs("pipelineSelectAllRunOptionsBtn")?.addEventListener("click", () => {
    setPipelineRunOptions(true);
  });

  qs("pipelineClearAllRunOptionsBtn")?.addEventListener("click", () => {
    setPipelineRunOptions(false);
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
  initMultiSelect("actionFilter");
  initMultiSelect("preferenceFilter");
  qs("applyFiltersBtn").addEventListener("click", async () => {
    queueTableState.page = 1;
    try {
      await loadBrowse(1);
    } catch (err) {
      showAppError("Failed to load browse data", err);
    }
  });

  qs("clearFiltersBtn").addEventListener("click", async () => {
    clearFilters();
    try {
      await loadBrowse(1);
    } catch (err) {
      showAppError("Failed to reload browse data", err);
    }
  });

  const queuePaginationActions = qs("queuePaginationActions");
  if (queuePaginationActions) {
    queuePaginationActions.addEventListener("click", async (event) => {
      const button = event.target.closest("[data-page-target]");
      if (!button || button.disabled) return;

      const nextPage = Number(button.dataset.pageTarget || "");
      if (!Number.isFinite(nextPage) || nextPage < 1 || nextPage === queueTableState.page) {
        return;
      }

      try {
        await reloadCurrentTable(nextPage);
      } catch (err) {
        showAppError("Failed to change queue page", err);
      }
    });
  }

  document.querySelectorAll("input[name='executiveViewMode']").forEach((input) => {
    input.addEventListener("change", () => {
      setExecutiveViewMode(input.value);
    });
  });

  document.addEventListener("click", (event) => {
    document.querySelectorAll(".multi-select").forEach((root) => {
      if (!root.contains(event.target)) {
        setMultiSelectOpen(root, false);
      }
    });
  });

  const repositionOpenMultiSelects = () => {
    document.querySelectorAll(".multi-select.is-open").forEach((root) => {
      positionMultiSelectMenu(root);
    });
  };
  window.addEventListener("resize", repositionOpenMultiSelects);
  window.addEventListener("scroll", repositionOpenMultiSelects, true);

  const refreshStatusBtn = qs("refreshStatusBtn");
    if (refreshStatusBtn) {
      refreshStatusBtn.addEventListener("click", async () => {
        try {
          await loadStatus();
        } catch (err) {
          showAppError("Failed to refresh dashboard status", err);
        }
      });
    }
}

async function init() {
  try {
    await loadPreferenceFilterOptions("preferenceFilter");
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

    setQueueLoadingState("Loading executive jobs...");

    await loadStatus();
    await loadPipelineStatus();
    await loadBrowse();

    const pipelineData = await fetchJson("/pipeline/status");
    if (pipelineData.pipeline && pipelineData.pipeline.is_running) {
      startPipelinePolling();
    }

    if (window.sessionStorage.getItem("applylens_open_live_pipeline") === "1") {
      window.sessionStorage.removeItem("applylens_open_live_pipeline");
      openPipelineConfigModal();
    }
  } catch (err) {
    console.error(err);
    showAppError("Failed to initialize dashboard", err);
  }
}

window.addEventListener("DOMContentLoaded", init);

function getPipelineGate() {
  return state.pipelineGate || {};
}

function ensurePipelineGateBanner() {
  let banner = qs("pipelineGateBanner");
  if (banner) return banner;

  const pageHeader = document.querySelector(".page-header");
  if (!pageHeader || !pageHeader.parentElement) return null;

  banner = document.createElement("section");
  banner.id = "pipelineGateBanner";
  banner.className = "profile-inline-status hidden pipeline-gate-banner";
  pageHeader.insertAdjacentElement("afterend", banner);
  return banner;
}

function forcePipelineDeleteSeenDataNo() {
  document.querySelectorAll("input[name='pipelineDeleteSeenData']").forEach((input) => {
    input.checked = input.value === "no";
  });
}

function setPipelineDeleteSeenDataDisabled(isDisabled, reason = "") {
  document.querySelectorAll("input[name='pipelineDeleteSeenData']").forEach((input) => {
    if (input.value === "yes") {
      input.disabled = Boolean(isDisabled);
      input.closest(".binary-toggle-option")?.classList.toggle("is-disabled", Boolean(isDisabled));
    }
  });

  if (isDisabled) {
    forcePipelineDeleteSeenDataNo();
  }

  const helper = document.querySelector(".pipeline-toggle-group .control-help");
  if (helper && reason) {
    helper.textContent = reason;
  }
}

function applyPipelineGateUi(gate) {
  const safeGate = gate || {};
  const runButton = qs("runPipelineBtn");
  const banner = ensurePipelineGateBanner();
  const meta = qs("pipelineRunMeta");

  if (!safeGate.can_run_live_pipeline) {
    const message =
      safeGate.live_pipeline_block_reason ||
      "Upload at least one resume before running Live Pipeline.";

    if (runButton) {
      runButton.disabled = true;
      runButton.setAttribute("aria-disabled", "true");
      runButton.title = message;
    }

    if (banner) {
      banner.className = "profile-inline-status info pipeline-gate-banner";
      banner.innerHTML = `
        <strong>Resume required.</strong>
        ${escapeHtml(message)}
        <a class="ghost-btn btn-sm" href="${escapeHtml(safeGate.profile_resume_upload_url || "/profile?onboarding=resume_upload")}">
          Upload resume
        </a>
      `;
    }

    if (meta) {
      meta.textContent = message;
    }
  } else {
    if (runButton) {
      runButton.disabled = false;
      runButton.removeAttribute("aria-disabled");
      runButton.title = "";
    }

    if (banner) {
      banner.className = "profile-inline-status hidden pipeline-gate-banner";
      banner.innerHTML = "";
    }
  }

  const deleteSeenBlocked = !safeGate.can_delete_seen_data;
  setPipelineDeleteSeenDataDisabled(
    deleteSeenBlocked,
    deleteSeenBlocked
      ? safeGate.delete_seen_data_block_reason ||
          "Delete seen data is available after your first successful Live Pipeline run."
      : "No keeps the seen-job cache. Yes reruns jobs that were already seen before."
  );
}

function redirectToResumeOnboardingIfRequired(gate) {
  const safeGate = gate || {};
  if (!safeGate.requires_resume_upload) return;
  if (window.location.pathname !== "/") return;

  const target = safeGate.profile_resume_upload_url || "/profile?onboarding=resume_upload";
  window.location.href = target;
}

async function loadPipelineGateForDashboard() {
  const workspaceState = await fetchJson("/user/workspace-state");
  const gate = workspaceState.pipeline_gate || {};
  state.pipelineGate = gate;
  applyPipelineGateUi(gate);
  redirectToResumeOnboardingIfRequired(gate);
  return gate;
}

function bindPipelineGateGuards() {
  document.addEventListener(
    "click",
    (event) => {
      const gate = getPipelineGate();
      const blocked = gate && gate.can_run_live_pipeline === false;

      const runTrigger = event.target.closest(
        "#runPipelineBtn, #openPipelineConfirmBtn, #confirmPipelineRunBtn"
      );

      if (blocked && runTrigger) {
        event.preventDefault();
        event.stopImmediatePropagation();
        window.location.href = gate.profile_resume_upload_url || "/profile?onboarding=resume_upload";
        return;
      }

      const deleteSeenYes = event.target.closest(
        "input[name='pipelineDeleteSeenData'][value='yes']"
      );

      if (deleteSeenYes && gate && gate.can_delete_seen_data === false) {
        event.preventDefault();
        event.stopImmediatePropagation();
        forcePipelineDeleteSeenDataNo();
      }
    },
    true
  );

  document.addEventListener(
    "change",
    (event) => {
      const gate = getPipelineGate();
      const deleteSeenYes = event.target.closest?.(
        "input[name='pipelineDeleteSeenData'][value='yes']"
      );

      if (deleteSeenYes && gate && gate.can_delete_seen_data === false) {
        event.preventDefault();
        forcePipelineDeleteSeenDataNo();
      }
    },
    true
  );
}

window.addEventListener("DOMContentLoaded", () => {
  bindPipelineGateGuards();

  loadPipelineGateForDashboard().catch((err) => {
    const banner = ensurePipelineGateBanner();
    if (banner) {
      banner.className = "profile-inline-status error pipeline-gate-banner";
      banner.textContent = `Could not load pipeline access state: ${err.message}`;
    }
  });

  window.setInterval(() => {
    if (state.pipelineGate) {
      applyPipelineGateUi(state.pipelineGate);
    }
  }, 1500);
});
