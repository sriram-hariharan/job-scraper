const PENDING_APPLICATION_STORAGE_KEY = "job_operator_pending_application";
const SCAN_WORKSPACE_SPLIT_STORAGE_KEY = "scan_workspace_left_width_pct";

let currentTailoringMarkdownRaw = "";
let tailoringCopyResetTimer = null;
let resumeChoiceState = {
  row: null,
  candidates: [],
  selectedResume: "",
  isBusy: false,
  previewRequestSeq: 0,
  previewAbortController: null,
  previewObjectUrl: "",
};

const PLANNING_TABLE_LAST_RESPONSE_STORAGE_KEY = "planningTableLastResponse_v4";
const PIPELINE_DATA_VERSION_STORAGE_KEY = "job_operator_pipeline_data_version";
const PLANNING_TABLE_REQUEST_TIMEOUT_MS = 0;
const PLANNING_TABLE_PREFETCH_TIMEOUT_MS = 12000;

const planningTableState = {
  rows: [],
  metaLabel: "Loading...",
  sort: {
    key: "",
    direction: "asc",
  },
  pagination: {
    page: 1,
    pageSize: 15,
    totalCount: 0,
    totalPages: 1,
    hasPrevPage: false,
    hasNextPage: false,
  },
  isLoading: false,
  requestSeq: 0,
  activeController: null,
  responseCache: new Map(),
  prefetchInFlight: new Set(),
  prefetchVisibleTimer: null,
  pipelineDataVersion: "",
};

let currentTailoringState = {
  row: null,
  tailoringJsonPath: "",
  artifactData: null,
  selectedCandidateIds: [],
  livePreview: null,
  previewRequestSeq: 0,
  isPreviewing: false,
  isSaving: false,
};

const tailoringWorkspaceState = {
  artifact: null,
  draftPayload: null,
  manualBulletEdits: {},
  selectedCandidateIds: [],
  rewriteReviewDecisions: {},
  candidateLookup: new Map(),
  previewPayload: null,
  savedSelectionPayload: null,
  selectedTab: "ready",
  activeInlineScoreKey: "",
  activeReviewEditCandidateId: "",
  isPreviewing: false,
  isSaving: false,
  previewReadyKey: "",
  reviewTelemetryFilter: "",
  previewMode: "pdf",
  documentPreviewPayload: null,
  documentPreviewRequestSeq: 0,
  documentPreviewTimer: null,
  isDocumentPreviewLoading: false,
  focusedBulletKey: "",
};

const tailoringWorkspacePdfState = {
  pdfDoc: null,
  resumeName: "",
  scale: 1,
  fitScale: 1,
  isFitPage: false,
  resizeTimer: null,
  renderToken: 0,
  pdfjsPromise: null,
  pageTextIndex: [],
  highlightedCandidateId: "",
};

const scanWorkspaceState = {
  preloadPayload: null,
  personalDetails: {},
  selectedCandidateIds: [],
  rewriteReviewDecisions: {},
  suggestionDecisionOverrides: {},
  excludedScanIssueIds: [],
  selectedTab: "personal_details",
  activeCandidateId: "",
  annotationMarkerSignature: "",
  previewPayload: null,
  isPreviewing: false,
  isSaving: false,
};

const SCAN_WORKSPACE_PERSONAL_DETAIL_FIELDS = ["name", "city", "state", "contact", "email", "linkedin", "github"];
const SCAN_WORKSPACE_US_STATES = [
  ["", "State"],
  ["AL", "Alabama"], ["AK", "Alaska"], ["AZ", "Arizona"], ["AR", "Arkansas"], ["CA", "California"],
  ["CO", "Colorado"], ["CT", "Connecticut"], ["DE", "Delaware"], ["DC", "District of Columbia"],
  ["FL", "Florida"], ["GA", "Georgia"], ["HI", "Hawaii"], ["ID", "Idaho"], ["IL", "Illinois"],
  ["IN", "Indiana"], ["IA", "Iowa"], ["KS", "Kansas"], ["KY", "Kentucky"], ["LA", "Louisiana"],
  ["ME", "Maine"], ["MD", "Maryland"], ["MA", "Massachusetts"], ["MI", "Michigan"], ["MN", "Minnesota"],
  ["MS", "Mississippi"], ["MO", "Missouri"], ["MT", "Montana"], ["NE", "Nebraska"], ["NV", "Nevada"],
  ["NH", "New Hampshire"], ["NJ", "New Jersey"], ["NM", "New Mexico"], ["NY", "New York"],
  ["NC", "North Carolina"], ["ND", "North Dakota"], ["OH", "Ohio"], ["OK", "Oklahoma"], ["OR", "Oregon"],
  ["PA", "Pennsylvania"], ["RI", "Rhode Island"], ["SC", "South Carolina"], ["SD", "South Dakota"],
  ["TN", "Tennessee"], ["TX", "Texas"], ["UT", "Utah"], ["VT", "Vermont"], ["VA", "Virginia"],
  ["WA", "Washington"], ["WV", "West Virginia"], ["WI", "Wisconsin"], ["WY", "Wyoming"],
];

const scanWorkspacePdfState = {
  pdfDoc: null,
  pdfjsPromise: null,
  renderToken: 0,
  scale: 1,
  fitScale: 1,
  isFitPage: true,
  resizeTimer: null,
  resumeName: "",
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

function clampToRange(value, min, max) {
  return Math.min(max, Math.max(min, value));
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
  th.classList.toggle("sortable-col", sortable);

  const currentWidth = th.style.width;
  th.innerHTML = buildResizableHeaderInnerHtml(label, key, { sortable });
  if (currentWidth) {
    th.style.width = currentWidth;
  }
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
    .filter(Boolean);
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
  } else {
    menu.hidden = true;
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

  getMultiSelectOptions(root).forEach((option) => {
    option.classList.remove("is-selected");
    option.setAttribute("aria-checked", "false");
  });

  updateMultiSelectLabel(root);
}

function setMultiSelectValues(id, values) {
  const root = getMultiSelectRoot(id);
  if (!root) return;

  const selectedValues = new Set(
    (Array.isArray(values) ? values : [])
      .map((value) => String(value || "").trim())
      .filter(Boolean)
  );

  getMultiSelectOptions(root).forEach((option) => {
    const optionValue = String(option.dataset.value || "").trim();
    const isSelected = selectedValues.has(optionValue);

    option.classList.toggle("is-selected", isSelected);
    option.setAttribute("aria-checked", isSelected ? "true" : "false");
  });

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

  getMultiSelectOptions(root).forEach((option) => {
    option.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();

      const isSelected = option.classList.toggle("is-selected");
      option.setAttribute("aria-checked", isSelected ? "true" : "false");
      updateMultiSelectLabel(root);
    });
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

function buildAdvisoryPriorityHtml(row) {
  const priority = String(row?.advisory_priority || "").trim().toLowerCase();
  const label = formatAdvisoryPriorityLabel(priority);
  if (!label) return "";

  const existingAction = String(row?.existing_action || row?.action || "").trim();
  const reasonCodes = String(row?.advisory_reason_codes || "").trim();
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
    <div class="queue-advisory-priority planning-advisory-priority">
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

function buildTailoringDecisionHtml(row) {
  const decision = String(row?.tailoring_decision || "").trim().toLowerCase();
  const label = formatTailoringDecisionLabel(decision);
  if (!label) return "";

  const existingAction = String(row?.existing_action || row?.action || "").trim();
  const advisoryPriority = String(row?.advisory_priority || "").trim();
  const reasonCodes = String(row?.tailoring_reason_codes || "").trim();
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
    <div class="queue-tailoring-decision planning-tailoring-decision">
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

function buildOperatorReviewHtml(row) {
  const lane = String(row?.operator_review_lane || "").trim().toLowerCase();
  const label = formatOperatorReviewLaneLabel(lane);
  if (!label) return "";

  const existingAction = String(row?.existing_action || row?.action || "").trim();
  const advisoryPriority = String(row?.advisory_priority || "").trim();
  const tailoringDecision = String(row?.tailoring_decision || "").trim();
  const reasonCodes = String(row?.operator_review_reason_codes || "").trim();
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
    <div class="queue-operator-review planning-operator-review">
      <span class="queue-operator-pill queue-operator-pill--${escapeHtml(lane)}">${escapeHtml(label)}</span>
      ${buildRecommendationDetailsHtml(details)}
    </div>
  `;
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

async function loadAgenticWorkflowSummaryPanel() {
  const panel = qs("agenticWorkflowSummaryPanel");
  if (!panel) return;
  try {
    const data = await fetchJson("/status");
    renderAgenticWorkflowSummaryPanel(data.agentic_workflow_summary);
  } catch (err) {
    panel.classList.add("hidden");
    panel.innerHTML = "";
    console.warn("Failed to load agentic workflow summary", err);
  }
}

async function loadAgenticWorkflowVerificationPanel() {
  const panel = qs("agenticWorkflowVerificationPanel");
  if (!panel) return;
  try {
    const data = await fetchJson("/status");
    renderAgenticWorkflowVerificationPanel(data.agentic_workflow_verification);
  } catch (err) {
    panel.classList.add("hidden");
    panel.innerHTML = "";
    console.warn("Failed to load agentic workflow verification", err);
  }
}

function formatScore100(value) {
  if (value === null || value === undefined || String(value).trim() === "") return "-";
  const parsed = Number(String(value).replaceAll(",", "").trim());
  if (!Number.isFinite(parsed)) return String(value);
  const normalized = Math.abs(parsed) <= 1 ? parsed * 100 : parsed;
  return normalized.toFixed(2);
}

function formatSignedScore100(value) {
  if (value === null || value === undefined || String(value).trim() === "") return "-";
  const parsed = Number(String(value).replaceAll(",", "").trim());
  if (!Number.isFinite(parsed)) return String(value);

  const normalized = Math.abs(parsed) <= 1 ? parsed * 100 : parsed;
  const prefix = normalized > 0 ? "+" : "";
  return `${prefix}${normalized.toFixed(2)}`;
}

function humanizeUnderscoreLabel(value, emptyLabel = "-") {
  const text = String(value || "").trim();
  if (!text) return emptyLabel;
  return text.replaceAll("_", " ");
}

function setInnerHtmlIfPresent(id, html) {
  const el = qs(id);
  if (!el) return;
  el.innerHTML = html;
}

function previewToneForStatus(status) {
  const normalized = String(status || "").trim().toLowerCase();

  if (normalized === "scored") return "safe";
  if (
    normalized === "no_patch_ready_rewrites" ||
    normalized === "no_valid_selected_candidates" ||
    normalized === "none"
  ) {
    return "muted";
  }
  if (
    normalized === "duplicate_source_bullet_id" ||
    normalized === "stale_signature" ||
    normalized === "no_valid_candidates"
  ) {
    return "caution";
  }
  return "danger";
}

function selectionToneForStatus(status) {
  const normalized = String(status || "").trim().toLowerCase();

  if (normalized === "applied") return "safe";
  if (normalized === "none") return "muted";
  if (normalized === "stale_signature" || normalized === "no_valid_candidates") return "caution";
  return "muted";
}

function getTailoringWorkspaceModeToggleButton() {
  return qs("tailoringWorkspaceModeToggleBtn");
}

function getTailoringWorkspacePreviewMode() {
  return String(tailoringWorkspaceState.previewMode || "pdf").trim().toLowerCase() === "edit"
    ? "edit"
    : "pdf";
}

function buildTailoringWorkspacePreviewDisplayName() {
  const resumeName = normalizeResumeName(tailoringWorkspacePdfState.resumeName || "");
  return resumeName ? humanizeResumeDisplayName(resumeName) : "No resume selected";
}

function syncTailoringWorkspacePreviewName() {
  const nameEl = qs("tailoringWorkspacePreviewName");
  if (!nameEl) return;
  nameEl.textContent = buildTailoringWorkspacePreviewDisplayName();
}

function syncTailoringWorkspaceModeToggleUi() {
  const btn = getTailoringWorkspaceModeToggleButton();
  if (!btn) return;

  const mode = getTailoringWorkspacePreviewMode();
  btn.dataset.previewMode = mode;
  btn.setAttribute("aria-pressed", mode === "edit" ? "true" : "false");
  btn.setAttribute(
    "aria-label",
    mode === "edit" ? "Switch to original PDF preview" : "Switch to edit mode"
  );

  const pdfSegment = btn.querySelector('[data-mode-segment="pdf"]');
  const editSegment = btn.querySelector('[data-mode-segment="edit"]');

  if (pdfSegment) {
    pdfSegment.classList.toggle("is-active", mode === "pdf");
  }
  if (editSegment) {
    editSegment.classList.toggle("is-active", mode === "edit");
  }

  syncTailoringWorkspacePreviewName();
}

function setTailoringWorkspacePreviewMode(mode) {
  const nextMode = String(mode || "").trim().toLowerCase() === "edit" ? "edit" : "pdf";
  if (tailoringWorkspaceState.previewMode === nextMode) return;

  tailoringWorkspaceState.previewMode = nextMode;
  syncTailoringWorkspaceModeToggleUi();

  const liveDraftRoot = qs("tailoringWorkspaceLiveDraftPreview");
  const pdfScroller = qs("tailoringWorkspacePdfScroller");
  const pdfPages = qs("tailoringWorkspacePdfPages");
  const previewEmpty = qs("tailoringWorkspacePreviewEmpty");
  const zoomOutBtn = qs("tailoringWorkspaceZoomOutBtn");
  const zoomResetBtn = qs("tailoringWorkspaceZoomResetBtn");
  const zoomInBtn = qs("tailoringWorkspaceZoomInBtn");

  if (liveDraftRoot) {
    liveDraftRoot.classList.toggle("hidden", nextMode !== "edit");
  }

  if (pdfScroller) {
    pdfScroller.classList.toggle("hidden", nextMode !== "pdf");
  }

  [zoomOutBtn, zoomResetBtn, zoomInBtn].forEach((btn) => {
    if (!btn) return;
    btn.classList.toggle("hidden", nextMode === "edit");
    btn.disabled = nextMode === "edit";
  });

  if (nextMode === "edit") {
    scheduleTailoringWorkspaceDocumentPreview({ immediate: true });
    setTailoringWorkspacePreviewMeta(getTailoringWorkspaceDocumentPreviewMeta());
    clearTailoringWorkspacePdfHighlight({ restoreMeta: false });
  } else {
    if (pdfPages && tailoringWorkspacePdfState.pdfDoc) {
      pdfPages.classList.remove("hidden");
    }
    if (previewEmpty && !tailoringWorkspacePdfState.pdfDoc) {
      previewEmpty.classList.remove("hidden");
    }
    setTailoringWorkspacePreviewMeta(buildTailoringWorkspaceDefaultPreviewMeta());
    syncTailoringWorkspacePreviewHighlight();
  }
}

function renderPatchPreviewDimensionDeltas(deltas) {
  const entries = Object.entries(deltas || {});
  if (!entries.length) {
    return `<div class="tailoring-empty-inline">No scorer-visible dimension deltas.</div>`;
  }

  const sorted = entries.sort((a, b) => Math.abs(Number(b[1] || 0)) - Math.abs(Number(a[1] || 0)));

  return `
    <div class="tailoring-chip-group">
      ${sorted.map(([key, value]) => {
        const numeric = Number(value || 0);
        const tone = numeric > 0 ? "safe" : numeric < 0 ? "danger" : "muted";
        return buildTailoringTonePill(
          `${humanizeUnderscoreLabel(key)} ${formatSignedScore100(numeric)}`,
          tone
        );
      }).join("")}
    </div>
  `;
}

function renderPatchPreviewCandidateList(candidateIds, emptyLabel = "None") {
  const safeIds = Array.isArray(candidateIds)
    ? candidateIds.map((item) => String(item || "").trim()).filter(Boolean)
    : [];

  if (!safeIds.length) {
    return `<div class="tailoring-empty-inline">${escapeHtml(emptyLabel)}</div>`;
  }

  return `
    <div class="tailoring-chip-group">
      ${safeIds.map((candidateId) => buildTailoringTonePill(candidateId, "neutral")).join("")}
    </div>
  `;
}

function renderPatchPreviewCard({
  title = "",
  preview = null,
  selectionStatus = "",
  selectionNote = "",
  explicitSelectedIds = [],
  emptyLabel = "No patch preview available.",
} = {}) {
  const hasPreview = preview && typeof preview === "object" && Object.keys(preview).length > 0;

  if (!hasPreview) {
    return `
      <section class="tailoring-section-block">
        <div class="tailoring-section-title">${escapeHtml(title)}</div>

        <div class="tailoring-info-row">
          <span class="tailoring-info-label">Selection status</span>
          <span class="tailoring-info-value">
            ${buildTailoringTonePill(humanizeUnderscoreLabel(selectionStatus || "none"), selectionToneForStatus(selectionStatus || "none"))}
          </span>
        </div>

        ${selectionNote ? `
          <div class="tailoring-info-block">
            <div class="tailoring-info-label">Note</div>
            <div class="tailoring-card-copy">${escapeHtml(selectionNote)}</div>
          </div>
        ` : ""}

        ${explicitSelectedIds.length ? `
          <div class="tailoring-info-block">
            <div class="tailoring-info-label">Selected candidate IDs</div>
            ${renderPatchPreviewCandidateList(explicitSelectedIds)}
          </div>
        ` : ""}

        <div class="tailoring-empty-state">
          ${escapeHtml(emptyLabel)}
        </div>
      </section>
    `;
  }

  const status = String(preview.status || "").trim();
  const note = String(preview.note || "").trim();
  const selectedCandidateIds = Array.isArray(preview.selected_candidate_ids) ? preview.selected_candidate_ids : [];
  const requestedCandidateIds = Array.isArray(preview.requested_candidate_ids) ? preview.requested_candidate_ids : [];
  const missingCandidateIds = Array.isArray(preview.missing_candidate_ids) ? preview.missing_candidate_ids : [];
  const ineligibleCandidateIds = Array.isArray(preview.ineligible_candidate_ids) ? preview.ineligible_candidate_ids : [];
  const duplicateSourceBulletIds = Array.isArray(preview.duplicate_source_bullet_ids) ? preview.duplicate_source_bullet_ids : [];
  const selectionMode = String(preview.selection_mode || "").trim();
  const projectedOverallDelta = preview.projected_overall_delta;
  const scorerVisibleEvidenceChanged = Boolean(preview.scorer_visible_evidence_changed);
  const selectedPatchCount = Number(preview.selected_patch_count || 0);
  const dimensionDeltas = preview.projected_dimension_deltas || {};

  const scopeLabel =
    selectionMode === "selected_candidate_ids"
      ? "Selected candidate IDs"
      : "All patch-ready rewrites";

  return `
    <section class="tailoring-section-block">
      <div class="tailoring-section-title">${escapeHtml(title)}</div>

      <div class="tailoring-card-topline">
        <div class="tailoring-chip-group">
          ${buildTailoringTonePill(scopeLabel, "neutral")}
          ${buildTailoringTonePill(humanizeUnderscoreLabel(status, "unknown"), previewToneForStatus(status))}
          ${selectionStatus ? buildTailoringTonePill(humanizeUnderscoreLabel(selectionStatus), selectionToneForStatus(selectionStatus)) : ""}
        </div>
      </div>

      <div class="tailoring-meta-grid">
        <div class="info-pair tailoring-meta-item">
          <span class="label">Selected patch count</span>
          <span>${escapeHtml(String(selectedPatchCount))}</span>
        </div>

        <div class="info-pair tailoring-meta-item">
          <span class="label">Projected overall delta</span>
          <span>${escapeHtml(formatSignedScore100(projectedOverallDelta))}</span>
        </div>

        <div class="info-pair tailoring-meta-item">
          <span class="label">Scorer-visible evidence changed</span>
          <span>${scorerVisibleEvidenceChanged ? "Yes" : "No"}</span>
        </div>

        <div class="info-pair tailoring-meta-item">
          <span class="label">Original score</span>
          <span>${escapeHtml(formatScore100(preview.original_final_score))}</span>
        </div>

        <div class="info-pair tailoring-meta-item">
          <span class="label">Projected score</span>
          <span>${escapeHtml(formatScore100(preview.projected_final_score))}</span>
        </div>
      </div>

      ${selectionNote ? `
        <div class="tailoring-info-block">
          <div class="tailoring-info-label">Saved selection note</div>
          <div class="tailoring-card-copy">${escapeHtml(selectionNote)}</div>
        </div>
      ` : ""}

      ${note ? `
        <div class="tailoring-info-block">
          <div class="tailoring-info-label">Preview note</div>
          <div class="tailoring-card-copy">${escapeHtml(note)}</div>
        </div>
      ` : ""}

      ${requestedCandidateIds.length ? `
        <div class="tailoring-info-block">
          <div class="tailoring-info-label">Requested candidate IDs</div>
          ${renderPatchPreviewCandidateList(requestedCandidateIds)}
        </div>
      ` : ""}

      ${selectedCandidateIds.length ? `
        <div class="tailoring-info-block">
          <div class="tailoring-info-label">Applied candidate IDs</div>
          ${renderPatchPreviewCandidateList(selectedCandidateIds)}
        </div>
      ` : ""}

      ${missingCandidateIds.length ? `
        <div class="tailoring-info-block">
          <div class="tailoring-info-label">Missing candidate IDs</div>
          ${renderPatchPreviewCandidateList(missingCandidateIds)}
        </div>
      ` : ""}

      ${ineligibleCandidateIds.length ? `
        <div class="tailoring-info-block">
          <div class="tailoring-info-label">Ineligible candidate IDs</div>
          ${renderPatchPreviewCandidateList(ineligibleCandidateIds)}
        </div>
      ` : ""}

      ${duplicateSourceBulletIds.length ? `
        <div class="tailoring-info-block">
          <div class="tailoring-info-label">Duplicate source bullet IDs</div>
          ${renderPatchPreviewCandidateList(duplicateSourceBulletIds)}
        </div>
      ` : ""}

      <div class="tailoring-info-block">
        <div class="tailoring-info-label">Projected dimension deltas</div>
        ${renderPatchPreviewDimensionDeltas(dimensionDeltas)}
      </div>
    </section>
  `;
}

function renderTailoringPatchPreviewSummary(artifact) {
  const root = qs("tailoringPatchPreviewSummary");
  if (!root) return;

  const payload = artifact && artifact.kind === "json" && artifact.data && typeof artifact.data === "object"
    ? artifact.data
    : null;

  const shouldShow = shouldShowPatchPreviewSection(payload);
  setTailoringSectionVisible("tailoringPatchPreviewSummary", shouldShow);

  if (!shouldShow) {
    root.innerHTML = "";
    return;
  }

  const selectedPreview = payload.selected_patch_set_counterfactual_preview || null;
  const autoPreview = payload.patch_set_counterfactual_preview || null;
  const selectionStatus = String(payload.selected_patch_selection_status || "none").trim();
  const selectionNote = String(payload.selected_patch_selection_note || "").trim();
  const explicitSelectedIds = Array.isArray(payload.selected_patch_candidate_ids)
    ? payload.selected_patch_candidate_ids
    : [];

  root.innerHTML = `
    ${renderPatchPreviewCard({
      title: "Saved Patch Selection Preview",
      preview: selectedPreview,
      selectionStatus,
      selectionNote,
      explicitSelectedIds,
      emptyLabel: selectionStatus === "none"
        ? "No saved patch selection yet."
        : "Saved patch selection preview is not available.",
    })}

    ${renderPatchPreviewCard({
      title: "Auto Preview (All Patch-Ready Rewrites)",
      preview: autoPreview,
      emptyLabel: "Automatic patch preview is not available.",
    })}
  `;
}

function renderTailoringPatchSelectionSummary(artifact) {
  const root = qs("tailoringPatchSelectionShell");
  if (!root) return;

  const payload = artifact && artifact.kind === "json" && artifact.data && typeof artifact.data === "object"
    ? artifact.data
    : null;

  const shouldShow = shouldShowPatchSelectionSection(payload);
  setTailoringSectionVisible("tailoringPatchSelectionShell", shouldShow);

  if (!shouldShow) {
    root.innerHTML = "";
    return;
  }

  const selectedIds = Array.isArray(payload.selected_patch_candidate_ids)
    ? payload.selected_patch_candidate_ids
    : [];
  const selectionStatus = String(payload.selected_patch_selection_status || "none").trim();
  const selectionNote = String(payload.selected_patch_selection_note || "").trim();
  const preview = payload.selected_patch_set_counterfactual_preview || null;

  root.innerHTML = `
    <section class="tailoring-section-block">
      <div class="tailoring-section-title">Current saved selection</div>

      <div class="tailoring-card-topline">
        <div class="tailoring-chip-group">
          ${buildTailoringTonePill(humanizeUnderscoreLabel(selectionStatus || "none"), selectionToneForStatus(selectionStatus || "none"))}
          ${buildTailoringTonePill(`${selectedIds.length} selected`, selectedIds.length ? "neutral" : "muted")}
        </div>
      </div>

      ${selectionNote ? `
        <div class="tailoring-info-block">
          <div class="tailoring-info-label">Selection note</div>
          <div class="tailoring-card-copy">${escapeHtml(selectionNote)}</div>
        </div>
      ` : ""}

      <div class="tailoring-info-block">
        <div class="tailoring-info-label">Selected candidate IDs</div>
        ${renderPatchPreviewCandidateList(selectedIds, "No saved candidate selection.")}
      </div>

      ${preview ? `
        <div class="tailoring-info-block">
          <div class="tailoring-info-label">Projected overall delta</div>
          <div class="tailoring-card-copy">${escapeHtml(formatSignedScore100(preview.projected_overall_delta))}</div>
        </div>
      ` : `
        <div class="tailoring-empty-inline">No saved selected-set preview available yet.</div>
      `}
    </section>
  `;
}

function planningUndecidedOnlyEnabled() {
  const selected = document.querySelector("input[name='planningUndecidedOnlyToggle']:checked");
  return selected ? selected.value === "yes" : false;
}

const PLANNING_SORT_COLUMNS = [
  { key: "queue_rank", label: "Rank", type: "number" },
  { key: "job_title", label: "Job title", type: "text", getValue: (row) => row.job_title || "" },
  { key: "posted_at", label: "Posted at", type: "date", getValue: (row) => row.posted_at || "" },
  { key: "recommendation", label: "Recommendation", type: "text", getValue: (row) => formatQueueActionLabel(row.action) },
  { key: "packet_status", label: "Packet / Workspace", type: "text", getValue: (row) => `${formatPacketStatusLabel(row.packet_generation_allowed)} ${row.tailoring_workspace_state || ""}` },
  { key: "winner_score", label: "Match", type: "number" },
  { key: "selected_resume", label: "Selected Resume", type: "text", getValue: (row) => row.operator_selected_resume || row.winner_resume || "" },
  { key: "review", label: "Review", sortable: false },
];

const PACKET_HELP_TEXT = "A packet is a review bundle for this job. It includes the job, selected resume, match signals, gaps, and tailoring guidance. It does not apply to the job.";

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
  const modal = getAppErrorModal();
  const titleEl = qs("appErrorTitle");
  const subtitleEl = qs("appErrorSubtitle");
  const messageEl = qs("appErrorMessage");
  const message = extractErrorMessage(err);

  if (!modal || !titleEl || !subtitleEl || !messageEl) {
    console.error(title || "Something went wrong", message);
    return;
  }

  titleEl.textContent = title || "Something went wrong";
  subtitleEl.textContent = subtitle;
  messageEl.textContent = message;
  modal.classList.remove("hidden");
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

function countPlanningActiveFilters() {
  let count = 0;
  if (getMultiSelectValues("planningActionFilter").length) count += 1;
  if (getMultiSelectValues("planningWinnerBucket").length) count += 1;
  if (getMultiSelectValues("planningTailoringFilter").length) count += 1;
  if (planningUndecidedOnlyEnabled()) count += 1;
  return count;
}

function updatePlanningStats(totalCount) {
  setTextIfPresent("planningJobsShown", totalCount ?? 0);
  setTextIfPresent("planningActiveFilters", countPlanningActiveFilters());
}

function setPlanningRequestedPage(page) {
  const parsed = Number(page);
  planningTableState.pagination.page = Number.isFinite(parsed) && parsed > 0 ? Math.floor(parsed) : 1;
}

function buildPlanningPaginationSequence(currentPage, totalPages) {
  if (totalPages <= 7) {
    return Array.from({ length: totalPages }, (_, index) => index + 1);
  }

  const pages = [1];
  const windowStart = Math.max(2, currentPage - 1);
  const windowEnd = Math.min(totalPages - 1, currentPage + 1);

  if (windowStart > 2) {
    pages.push("ellipsis-left");
  }

  for (let page = windowStart; page <= windowEnd; page += 1) {
    pages.push(page);
  }

  if (windowEnd < totalPages - 1) {
    pages.push("ellipsis-right");
  }

  pages.push(totalPages);
  return pages;
}

function renderPlanningPagination() {
  const metaEl = qs("planningPaginationMeta");
  const actionsEl = qs("planningPaginationActions");
  if (!metaEl || !actionsEl) return;

  const {
    page,
    pageSize,
    totalCount,
    totalPages,
    hasPrevPage,
    hasNextPage,
  } = planningTableState.pagination;

  if (!totalCount) {
    metaEl.textContent = "Page 1 of 1 · 0 jobs";
    actionsEl.innerHTML = "";
    return;
  }

  const startRow = (page - 1) * pageSize + 1;
  const endRow = Math.min(page * pageSize, totalCount);

  metaEl.textContent = `Page ${page} of ${totalPages} · Showing ${startRow}-${endRow} of ${totalCount} jobs`;

  const sequence = buildPlanningPaginationSequence(page, totalPages);

  actionsEl.innerHTML = `
    <button
      type="button"
      class="ghost-btn planning-pagination-btn"
      data-planning-page="${page - 1}"
      ${hasPrevPage ? "" : "disabled"}
    >
      Prev
    </button>

    ${sequence.map((item) => {
      if (typeof item !== "number") {
        return `<span class="planning-pagination-ellipsis">…</span>`;
      }

      return `
        <button
          type="button"
          class="ghost-btn planning-pagination-btn ${item === page ? "is-active" : ""}"
          data-planning-page="${item}"
          ${item === page ? "disabled" : ""}
        >
          ${item}
        </button>
      `;
    }).join("")}

    <button
      type="button"
      class="ghost-btn planning-pagination-btn"
      data-planning-page="${page + 1}"
      ${hasNextPage ? "" : "disabled"}
    >
      Next
    </button>
  `;

}

async function fetchJson(url, options = {}) {
  const {
    timeoutMs = PLANNING_TABLE_REQUEST_TIMEOUT_MS,
    signal: externalSignal,
    ...fetchOptions
  } = options || {};

  const controller = new AbortController();
  let timedOut = false;
  let timeoutId = null;

  const handleExternalAbort = () => {
    controller.abort();
  };

  if (externalSignal) {
    if (externalSignal.aborted) {
      controller.abort();
    } else {
      externalSignal.addEventListener("abort", handleExternalAbort, { once: true });
    }
  }

  if (Number.isFinite(timeoutMs) && timeoutMs > 0) {
    timeoutId = window.setTimeout(() => {
      timedOut = true;
      controller.abort();
    }, timeoutMs);
  }

  try {
    const response = await fetch(url, {
      cache: fetchOptions.cache || "no-store",
      ...fetchOptions,
      signal: controller.signal,
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(`HTTP ${response.status}: ${text}`);
    }

    return response.json();
  } catch (err) {
    if (err && err.name === "AbortError" && timedOut) {
      throw new Error(`Request timed out after ${Math.round(timeoutMs / 1000)}s.`);
    }
    throw err;
  } finally {
    if (timeoutId !== null) {
      window.clearTimeout(timeoutId);
    }
    if (externalSignal) {
      externalSignal.removeEventListener("abort", handleExternalAbort);
    }
  }
}

function readPipelineDataVersion() {
  try {
    return window.localStorage.getItem(PIPELINE_DATA_VERSION_STORAGE_KEY) || "";
  } catch {
    return "";
  }
}

function clearPlanningTableResponseCache({ removeSession = true } = {}) {
  planningTableState.responseCache.clear();
  planningTableState.prefetchInFlight.clear();

  if (!removeSession) return;
  try {
    window.sessionStorage.removeItem(PLANNING_TABLE_LAST_RESPONSE_STORAGE_KEY);
  } catch {
    // ignore session cache failures
  }
}

function invalidatePlanningTableCacheIfPipelineChanged() {
  const currentVersion = readPipelineDataVersion();
  if (planningTableState.pipelineDataVersion === currentVersion) return false;

  planningTableState.pipelineDataVersion = currentVersion;
  clearPlanningTableResponseCache();
  return true;
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

async function postJsonWithTimeout(url, payload, timeoutMs = 20000) {
  return fetchJson(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
    timeoutMs,
  });
}

function buildPlanningUrl(pageOverride = null) {
  const params = new URLSearchParams();
  const actions = getMultiSelectValues("planningActionFilter");
  const winnerBuckets = getMultiSelectValues("planningWinnerBucket");
  const tailoringStates = getMultiSelectValues("planningTailoringFilter");
  const undecidedOnly = planningUndecidedOnlyEnabled() ? "true" : "";
  const limit = qs("planningLimitInput").value || "15";
  const page =
    Number.isFinite(Number(pageOverride)) && Number(pageOverride) > 0
      ? Math.floor(Number(pageOverride))
      : planningTableState.pagination.page || 1;

  appendMultiValueParams(params, "action", actions);
  appendMultiValueParams(params, "winner_bucket", winnerBuckets);
  appendMultiValueParams(params, "tailoring_state", tailoringStates);
  if (undecidedOnly) params.set("undecided_only", undecidedOnly);
  params.set("limit", limit);
  params.set("page", String(page));

  return `/browse?${params.toString()}`;
}

function readPlanningTableLastResponse(url) {
  const cached = planningTableState.responseCache.get(url);
  if (cached) return cached;

  try {
    const raw = window.sessionStorage.getItem(PLANNING_TABLE_LAST_RESPONSE_STORAGE_KEY);
    if (!raw) return null;

    const parsed = JSON.parse(raw);
    if (!parsed || parsed.url !== url || !parsed.data) return null;
    if ((parsed.pipelineDataVersion || "") !== planningTableState.pipelineDataVersion) {
      window.sessionStorage.removeItem(PLANNING_TABLE_LAST_RESPONSE_STORAGE_KEY);
      return null;
    }

    planningTableState.responseCache.set(url, parsed.data);
    return parsed.data;
  } catch {
    return null;
  }
}

function writePlanningTableLastResponse(url, data, { persistToSession = false } = {}) {
  planningTableState.responseCache.set(url, data);

  if (!persistToSession) return;

  try {
    window.sessionStorage.setItem(
      PLANNING_TABLE_LAST_RESPONSE_STORAGE_KEY,
      JSON.stringify({
        url,
        savedAt: Date.now(),
        pipelineDataVersion: planningTableState.pipelineDataVersion,
        data,
      })
    );
  } catch {
    // ignore session cache write failure
  }
}

function capturePlanningTableSnapshot() {
  if (!planningTableState.rows.length && !planningTableState.pagination.totalCount) {
    return null;
  }

  return {
    rows: planningTableState.rows.slice(),
    metaLabel: planningTableState.metaLabel,
    pagination: {
      ...planningTableState.pagination,
    },
  };
}

function restorePlanningTableSnapshot(snapshot, { note = "" } = {}) {
  if (!snapshot) return false;

  planningTableState.pagination = {
    ...snapshot.pagination,
  };

  renderPlanningRows(snapshot.rows, snapshot.metaLabel);

  const tableMeta = qs("planningTableMeta");
  if (tableMeta && note) {
    tableMeta.textContent = `${snapshot.metaLabel} · ${note}`;
  }

  syncPlanningBrowserUrl({ mode: "replace" });
  return true;
}

function applyPlanningTableResponse(data, { historyMode = "replace" } = {}) {
  const rawPageSize = data.page_size ?? 15;
  const parsedPageSize = Number(rawPageSize);
  const pageSize = Number.isFinite(parsedPageSize) && parsedPageSize > 0 ? parsedPageSize : 15;
  const totalCount = Number(data.total_count ?? data.count ?? 0);
  const totalPages = Number(data.total_pages ?? 1);
  const currentPage = Number(data.page ?? planningTableState.pagination.page ?? 1);

  updatePlanningStats(totalCount);

  planningTableState.pagination = {
    page: currentPage,
    pageSize: Number.isFinite(pageSize) && pageSize > 0 ? pageSize : 15,
    totalCount: Number.isFinite(totalCount) ? totalCount : 0,
    totalPages: Number.isFinite(totalPages) && totalPages > 0 ? totalPages : 1,
    hasPrevPage: Boolean(data.has_prev_page),
    hasNextPage: Boolean(data.has_next_page),
  };

  syncPlanningBrowserUrl({ mode: historyMode });

  renderPlanningRows(
    data.rows || [],
    `Planning detail view · ${totalCount} total job${totalCount === 1 ? "" : "s"}`
  );
}

function prefetchPlanningTablePage(pageNumber) {
  const parsedPage = Number(pageNumber);
  if (!Number.isFinite(parsedPage) || parsedPage < 1) return;
  if (parsedPage === Number(planningTableState.pagination.page || 1)) return;

  const totalPages = Number(planningTableState.pagination.totalPages || 1);
  if (parsedPage > totalPages) return;

  const url = buildPlanningUrl(parsedPage);

  if (planningTableState.responseCache.has(url)) return;
  if (planningTableState.prefetchInFlight.has(url)) return;

  planningTableState.prefetchInFlight.add(url);

  fetchJson(url, { timeoutMs: PLANNING_TABLE_PREFETCH_TIMEOUT_MS })
    .then((data) => {
      writePlanningTableLastResponse(url, data, { persistToSession: false });
    })
    .catch(() => {
      // ignore background prefetch failure
    })
    .finally(() => {
      planningTableState.prefetchInFlight.delete(url);
    });
}

function prefetchPlanningTableNeighbors() {
  const currentPage = Number(planningTableState.pagination.page || 1);
  prefetchPlanningTablePage(currentPage + 1);
  prefetchPlanningTablePage(currentPage - 1);
}

function prefetchVisiblePlanningPages() {
  const actionsEl = qs("planningPaginationActions");
  if (!actionsEl) return;

  const currentPage = Number(planningTableState.pagination.page || 1);

  const candidatePages = Array.from(
    actionsEl.querySelectorAll("[data-planning-page]")
  )
    .map((button) => Number(button.dataset.planningPage || ""))
    .filter((page) => {
      if (!Number.isFinite(page) || page < 1) return false;
      if (page === currentPage) return false;
      return Math.abs(page - currentPage) <= 2;
    });

  Array.from(new Set(candidatePages)).forEach((page) => {
    prefetchPlanningTablePage(page);
  });
}

function isValidPlanningSortKey(key) {
  return PLANNING_SORT_COLUMNS.some(
    (column) => column.sortable !== false && column.key === key
  );
}

function readPlanningUrlState(search = window.location.search) {
  const params = search instanceof URLSearchParams
    ? search
    : new URLSearchParams(String(search || ""));

  const parsedPage = Number(params.get("page") || "1");
  const page = Number.isFinite(parsedPage) && parsedPage > 0 ? parsedPage : 1;

  const limitValue = String(params.get("limit") || "15").trim();
  const limit = limitValue || "15";

  const rawSortKey = String(params.get("sort_key") || "").trim();
  const sortKey = isValidPlanningSortKey(rawSortKey) ? rawSortKey : "";

  return {
    actions: params.getAll("action").map((value) => String(value || "").trim()).filter(Boolean),
    winnerBuckets: params.getAll("winner_bucket").map((value) => String(value || "").trim()).filter(Boolean),
    tailoringStates: params.getAll("tailoring_state").map((value) => String(value || "").trim()).filter(Boolean),
    undecidedOnly: params.get("undecided_only") === "true",
    limit,
    page,
    sortKey,
    sortDirection: params.get("sort_dir") === "desc" ? "desc" : "asc",
  };
}

function applyPlanningUrlState(search = window.location.search) {
  const state = readPlanningUrlState(search);

  setMultiSelectValues("planningActionFilter", state.actions);
  setMultiSelectValues("planningWinnerBucket", state.winnerBuckets);
  setMultiSelectValues("planningTailoringFilter", state.tailoringStates);

  const undecidedYes = document.querySelector("input[name='planningUndecidedOnlyToggle'][value='yes']");
  const undecidedNo = document.querySelector("input[name='planningUndecidedOnlyToggle'][value='no']");

  if (state.undecidedOnly && undecidedYes) {
    undecidedYes.checked = true;
  } else if (undecidedNo) {
    undecidedNo.checked = true;
  }

  const limitInput = qs("planningLimitInput");
  if (limitInput) {
    limitInput.value = state.limit;
  }

  planningTableState.sort.key = state.sortKey;
  planningTableState.sort.direction = state.sortDirection;
  setPlanningRequestedPage(state.page);

  return state;
}

function buildPlanningBrowserUrl() {
  const params = new URLSearchParams();
  const actions = getMultiSelectValues("planningActionFilter");
  const winnerBuckets = getMultiSelectValues("planningWinnerBucket");
  const tailoringStates = getMultiSelectValues("planningTailoringFilter");
  const undecidedOnly = planningUndecidedOnlyEnabled();
  const limit = String(qs("planningLimitInput")?.value || "15").trim() || "15";
  const page = Number(planningTableState.pagination.page || 1);

  appendMultiValueParams(params, "action", actions);
  appendMultiValueParams(params, "winner_bucket", winnerBuckets);
  appendMultiValueParams(params, "tailoring_state", tailoringStates);

  if (undecidedOnly) params.set("undecided_only", "true");
  if (limit !== "15") params.set("limit", limit);
  if (Number.isFinite(page) && page > 1) params.set("page", String(page));

  if (isValidPlanningSortKey(planningTableState.sort.key)) {
    params.set("sort_key", planningTableState.sort.key);
    params.set(
      "sort_dir",
      planningTableState.sort.direction === "desc" ? "desc" : "asc"
    );
  }

  const query = params.toString();
  return query ? `${window.location.pathname}?${query}` : window.location.pathname;
}

function syncPlanningBrowserUrl({ mode = "replace" } = {}) {
  const nextUrl = buildPlanningBrowserUrl();
  const currentUrl = `${window.location.pathname}${window.location.search}`;

  if (currentUrl === nextUrl) return;

  window.history[mode === "push" ? "pushState" : "replaceState"](
    { planningDashboard: true },
    "",
    nextUrl
  );
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

function getTailoringModal() {
  return qs("tailoringModal");
}

function getResumeChoiceModal() {
  return qs("resumeChoiceModal");
}

function normalizeResumeName(value) {
  return String(value || "")
    .trim()
    .replace(/\\/g, "/")
    .split("/")
    .pop()
    .trim();
}

function isOptionalTailoringArtifactPath(value) {
  const name = String(value || "")
    .trim()
    .replace(/\\/g, "/")
    .split("/")
    .pop()
    .toLowerCase();
  return name.endsWith("__tailoring.json") || name.endsWith("_tailoring.json");
}

function normalizeResumePreviewName(value) {
  const safeName = normalizeResumeName(value);
  if (!safeName || safeName.toLowerCase().endsWith(".json") || isOptionalTailoringArtifactPath(safeName)) {
    return "";
  }
  return safeName;
}

function buildResumePdfFileUrl(resumeName, context = null) {
  const safeName = normalizeResumePreviewName(resumeName);
  const packetKey =
    String(context?.packetJsonKey || context?.packetJsonPath || "").trim();
  const params = new URLSearchParams();
  params.set("resume_name", safeName || "__resolve_from_packet__");

  // Packet context is only required when the resume must be resolved from the packet.
  // If the selected resume PDF name is already known, stale/expired packet_json must not block preview rendering.
  if (!safeName && packetKey) {
    params.set("packet_json", packetKey);
    const derivedOutputDir =
      phase71bDeriveRunScopedPlanningOutputDir(packetKey) ||
      String(context?.planningOutputDir || "").trim();
    if (derivedOutputDir) params.set("output_dir", derivedOutputDir);
  }

  return `/planning/resume-preview?${params.toString()}`;
}

function buildResumePreviewFrameUrl(rawUrl) {
  return `${rawUrl}#toolbar=0&navpanes=0&scrollbar=1&view=FitH`;
}

function clearResumeChoicePreviewResources({
  revokeObjectUrl = true,
  abortRequest = true,
} = {}) {
  if (abortRequest && resumeChoiceState.previewAbortController) {
    try {
      resumeChoiceState.previewAbortController.abort();
    } catch {
      // ignore abort cleanup failure
    }
  }
  resumeChoiceState.previewAbortController = null;

  if (revokeObjectUrl && resumeChoiceState.previewObjectUrl) {
    try {
      URL.revokeObjectURL(resumeChoiceState.previewObjectUrl);
    } catch {
      // ignore revoke cleanup failure
    }
    resumeChoiceState.previewObjectUrl = "";
  }
}

function resetResumeChoicePreviewSurface({
  placeholderText = "Select a resume on the left to load its PDF preview.",
  clearSelection = false,
} = {}) {
  const previewFrame = qs("resumeChoicePreviewFrame");
  const previewPages = qs("resumeChoicePreviewPages");
  const previewEmpty = qs("resumeChoicePreviewEmpty");
  const previewName = qs("resumeChoicePreviewName");
  const selectBtn = qs("resumeChoiceSelectBtn");
  const llmBtn = qs("resumeChoiceGenerateLlmBtn");

  if (previewFrame) {
    previewFrame.src = "about:blank";
    previewFrame.classList.add("hidden");
  }

  if (previewPages) {
    previewPages.innerHTML = "";
    previewPages.classList.add("hidden");
  }

  previewEmpty.textContent = placeholderText;
  previewEmpty.classList.remove("hidden");

  if (clearSelection) {
    previewName.textContent = "Select a resume to preview";
    selectBtn.disabled = true;
    if (llmBtn) {
      llmBtn.disabled = true;
    }
  }
}

function normalizeTailoringWorkspaceText(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/[•▪◦·]/g, " ")
    .replace(/\s+/g, " ")
    .replace(/[^a-z0-9%$&.,+\-/ ]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function getTailoringWorkspaceCanonicalBulletText(item, mode = "") {
  const normalizedMode = String(mode || "").trim().toLowerCase();

  if (normalizedMode === "direction_only") {
    return String(
      item?.current_evidence || item?.original_text || item?.parent_bullet || ""
    ).trim();
  }

  return String(
    item?.current_evidence || item?.original_text || item?.parent_bullet || ""
  ).trim();
}

function getTailoringWorkspaceDisplayBulletText(item, mode = "") {
  return getTailoringWorkspaceCanonicalBulletText(item, mode);
}

function extractTailoringWorkspaceAnchorText(value, maxWords = 12) {
  const normalized = normalizeTailoringWorkspaceText(value);
  if (!normalized) return "";
  return normalized.split(" ").slice(0, maxWords).join(" ");
}

function getTailoringWorkspaceSelectableItems(payload) {
  return [
    ...(Array.isArray(payload?.app_ready_replacements) ? payload.app_ready_replacements : []),
    ...(Array.isArray(payload?.direct_apply_optional_replacements)
      ? payload.direct_apply_optional_replacements
      : []),
    ...(Array.isArray(payload?.direction_only_replacements)
      ? payload.direction_only_replacements
      : []),
  ];
}

function buildTailoringWorkspaceCandidateLookup(payload) {
  const lookup = new Map();

  getTailoringWorkspaceSelectableItems(payload).forEach((item) => {
    const candidateId = getTailoringReplacementCandidateId(item);
    if (!candidateId) return;
    lookup.set(candidateId, item);
  });

  return lookup;
}

function getTailoringWorkspaceCandidateItem(candidateId) {
  const safeCandidateId = String(candidateId || "").trim();
  if (!safeCandidateId) return null;
  return tailoringWorkspaceState.candidateLookup.get(safeCandidateId) || null;
}

function buildTailoringWorkspacePdfLineIndex(textContent, viewport) {
  const items = Array.isArray(textContent?.items) ? textContent.items : [];
  const lines = [];
  const yTolerance = 6;

  items.forEach((item) => {
    const text = String(item?.str || "").trim();
    if (!text) return;

    const transform = Array.isArray(item.transform) ? item.transform : [1, 0, 0, 1, 0, 0];
    const [x, y] = viewport.convertToViewportPoint(transform[4], transform[5]);
    const width = Math.max(12, Number(item.width || 0) * viewport.scale);
    const height = Math.max(12, Math.abs((item.height || transform[3] || 0) * viewport.scale));
    const top = y - height;

    let line = lines.find((entry) => Math.abs(entry.top - top) <= yTolerance);
    if (!line) {
      line = {
        top,
        left: x,
        right: x + width,
        bottom: top + height,
        segments: [],
      };
      lines.push(line);
    }

    line.left = Math.min(line.left, x);
    line.right = Math.max(line.right, x + width);
    line.bottom = Math.max(line.bottom, top + height);
    line.segments.push({ x, text });
  });

  return lines
    .sort((a, b) => a.top - b.top)
    .map((line, index) => {
      const text = line.segments
        .sort((a, b) => a.x - b.x)
        .map((segment) => segment.text)
        .join(" ")
        .replace(/\s+/g, " ")
        .trim();

      return {
        lineId: index + 1,
        text,
        normalizedText: normalizeTailoringWorkspaceText(text),
        bbox: {
          left: Math.max(0, line.left - 6),
          top: Math.max(0, line.top - 2),
          width: Math.max(24, line.right - line.left + 12),
          height: Math.max(18, line.bottom - line.top + 4),
        },
      };
    });
}

function isTailoringWorkspacePdfSectionHeading(text) {
  const safeText = String(text || "").replace(/\s+/g, " ").trim();
  if (!safeText) return false;
  if (safeText.length > 48) return false;
  if (/[a-z]/.test(safeText)) return false;

  const alphaChars = safeText.replace(/[^A-Z]/g, "");
  if (alphaChars.length < 4) return false;

  return true;
}

function getTailoringWorkspacePdfMatchArea(bbox) {
  const width = Math.max(0, Number(bbox?.width || 0));
  const height = Math.max(0, Number(bbox?.height || 0));
  return width * height;
}

function shouldReplaceTailoringWorkspaceBestPdfMatch(candidate, best) {
  if (!best) return true;

  const candidateScore = Number(candidate?.score || 0);
  const bestScore = Number(best?.score || 0);
  if (candidateScore !== bestScore) {
    return candidateScore > bestScore;
  }

  const candidateArea = getTailoringWorkspacePdfMatchArea(candidate?.bbox);
  const bestArea = getTailoringWorkspacePdfMatchArea(best?.bbox);
  if (candidateArea !== bestArea) {
    return candidateArea < bestArea;
  }

  return String(candidate?.lineText || "").length < String(best?.lineText || "").length;
}

function buildTailoringWorkspacePdfBlockIndex(lines) {
  const safeLines = Array.isArray(lines) ? lines : [];
  const blocks = [];
  const bulletStartPattern = /^[•●▪◦·-]\s*/;

  let currentBlock = null;

  safeLines.forEach((line) => {
    const safeText = String(line?.text || "").trim();
    if (!safeText) return;

    const startsBullet = bulletStartPattern.test(safeText);
    const isSectionHeading = isTailoringWorkspacePdfSectionHeading(safeText);
    const isDateHeading = Boolean(splitTailoringWorkspaceTrailingDateRange(safeText));
    const prevLine =
      currentBlock && currentBlock.lines.length
        ? currentBlock.lines[currentBlock.lines.length - 1]
        : null;
    const prevIsSectionHeading = prevLine
      ? isTailoringWorkspacePdfSectionHeading(prevLine.text)
      : false;

    const verticalGap = prevLine
      ? Math.max(
          0,
          Number(line.bbox.top || 0) -
            (Number(prevLine.bbox.top || 0) + Number(prevLine.bbox.height || 0))
        )
      : Number.POSITIVE_INFINITY;

    const canContinueCurrent =
      Boolean(currentBlock) &&
      Boolean(prevLine) &&
      !startsBullet &&
      !isSectionHeading &&
      !isDateHeading &&
      !prevIsSectionHeading &&
      verticalGap <= 18 &&
      Number(line.bbox.left || 0) >= Number(currentBlock.anchorLeft || 0) - 12;

    if (!canContinueCurrent) {
      currentBlock = {
        blockId: blocks.length + 1,
        anchorLeft: Number(line.bbox.left || 0),
        lines: [],
      };
      blocks.push(currentBlock);
    }

    currentBlock.lines.push(line);
  });

  return blocks.map((block) => {
    const left = Math.min(...block.lines.map((line) => Number(line.bbox.left || 0)));
    const top = Math.min(...block.lines.map((line) => Number(line.bbox.top || 0)));
    const right = Math.max(
      ...block.lines.map((line) => Number(line.bbox.left || 0) + Number(line.bbox.width || 0))
    );
    const bottom = Math.max(
      ...block.lines.map((line) => Number(line.bbox.top || 0) + Number(line.bbox.height || 0))
    );

    const text = block.lines
      .map((line) => String(line.text || "").trim())
      .join(" ")
      .replace(/\s+/g, " ")
      .trim();

    return {
      blockId: block.blockId,
      matchKind: "block",
      text,
      normalizedText: normalizeTailoringWorkspaceText(text),
      bbox: {
        left: Math.max(0, left - 8),
        top: Math.max(0, top - 4),
        width: Math.max(36, right - left + 16),
        height: Math.max(22, bottom - top + 8),
      },
    };
  });
}

function scoreTailoringWorkspaceLineMatch(targetText, lineText) {
  const targetNormalized = normalizeTailoringWorkspaceText(targetText);
  const lineNormalized = normalizeTailoringWorkspaceText(lineText);

  if (!targetNormalized || !lineNormalized) return 0;
  if (lineNormalized.includes(targetNormalized)) return 1000 + targetNormalized.length;

  const anchor = extractTailoringWorkspaceAnchorText(targetText);
  if (anchor && lineNormalized.includes(anchor)) return 800 + anchor.length;

  const anchorTokens = (anchor || targetNormalized)
    .split(" ")
    .filter((token) => token.length >= 4);

  let hits = 0;
  anchorTokens.forEach((token) => {
    if (lineNormalized.includes(token)) hits += 1;
  });

  if (!hits) return 0;
  return hits * 25;
}

function findTailoringWorkspaceBestPdfMatch(targetText) {
  const safeTarget = String(targetText || "").trim();
  if (!safeTarget) return null;

  let bestBlock = null;
  let bestLine = null;

  tailoringWorkspacePdfState.pageTextIndex.forEach((pageEntry) => {
    (pageEntry.blocks || []).forEach((block) => {
      const score = scoreTailoringWorkspaceLineMatch(safeTarget, block.text);
      if (!score) return;

      const candidate = {
        pageNumber: pageEntry.pageNumber,
        blockId: block.blockId,
        matchKind: "block",
        lineText: block.text,
        bbox: block.bbox,
        score,
      };

      if (shouldReplaceTailoringWorkspaceBestPdfMatch(candidate, bestBlock)) {
        bestBlock = candidate;
      }
    });

    (pageEntry.lines || []).forEach((line) => {
      const score = scoreTailoringWorkspaceLineMatch(safeTarget, line.text);
      if (!score) return;

      const candidate = {
        pageNumber: pageEntry.pageNumber,
        lineId: line.lineId,
        matchKind: "line",
        lineText: line.text,
        bbox: line.bbox,
        score,
      };

      if (shouldReplaceTailoringWorkspaceBestPdfMatch(candidate, bestLine)) {
        bestLine = candidate;
      }
    });
  });

  if (bestBlock && bestBlock.score >= 50) return bestBlock;
  return bestLine && bestLine.score >= 50 ? bestLine : null;
}

function findTailoringWorkspaceBestPdfMatchFromTargets(targetTexts) {
  const targets = (Array.isArray(targetTexts) ? targetTexts : [])
    .map((value) => String(value || "").trim())
    .filter(Boolean);

  let best = null;

  targets.forEach((targetText) => {
    const match = findTailoringWorkspaceBestPdfMatch(targetText);
    if (!match) return;

    if (shouldReplaceTailoringWorkspaceBestPdfMatch(match, best)) {
      best = match;
    }
  });

  return best;
}

function getTailoringWorkspaceDisplayZoomPercent() {
  const scale = Number(tailoringWorkspacePdfState.scale || 1);
  const fitScale = Number(tailoringWorkspacePdfState.fitScale || 0);

  if (Number.isFinite(fitScale) && fitScale > 0) {
    return Math.max(1, Math.round((scale / fitScale) * 100));
  }

  return Math.max(1, Math.round(scale * 100));
}

function buildTailoringWorkspaceDefaultPreviewMeta() {
  if (!tailoringWorkspacePdfState.pdfDoc) {
    return "Resume preview is not available for this workspace row.";
  }

  const pageCount = tailoringWorkspacePdfState.pdfDoc.numPages;
  return `${pageCount} page${pageCount === 1 ? "" : "s"} • ${getTailoringWorkspaceDisplayZoomPercent()}%`;
}

function clearTailoringWorkspacePdfHighlight({ restoreMeta = true } = {}) {
  const pagesRoot = qs("tailoringWorkspacePdfPages");
  if (pagesRoot) {
    pagesRoot.querySelectorAll(".tailoring-workspace-pdf-highlight").forEach((node) => node.remove());
  }

  tailoringWorkspacePdfState.highlightedCandidateId = "";
  syncTailoringWorkspaceFocusedCards();

  if (restoreMeta) {
    setTailoringWorkspacePreviewMeta(buildTailoringWorkspaceDefaultPreviewMeta());
  }
}

function applyTailoringWorkspacePdfHighlight(match, candidateId = "") {
  clearTailoringWorkspacePdfHighlight({ restoreMeta: false });

  if (!match) return;

  const pageShell = document.querySelector(
    `.tailoring-workspace-pdf-page[data-page-number="${String(match.pageNumber)}"]`
  );
  if (!pageShell) return;

  const overlay = pageShell.querySelector(".tailoring-workspace-pdf-overlay");
  if (!overlay) return;

  const highlight = document.createElement("div");
  highlight.className = "tailoring-workspace-pdf-highlight";
  highlight.style.left = `${match.bbox.left}px`;
  highlight.style.top = `${match.bbox.top}px`;
  highlight.style.width = `${match.bbox.width}px`;
  highlight.style.height = `${match.bbox.height}px`;

  overlay.appendChild(highlight);
  tailoringWorkspacePdfState.highlightedCandidateId = String(candidateId || "").trim();
  syncTailoringWorkspaceFocusedCards();

  pageShell.scrollIntoView({
    behavior: "smooth",
    block: "center",
  });

  setTailoringWorkspacePreviewMeta(
    `Matched bullet on page ${match.pageNumber} • ${getTailoringWorkspaceDisplayZoomPercent()}%`
  );
}

function focusTailoringWorkspaceBulletKeyInPreview(bulletKey, candidateId = "") {
  const safeBulletKey = String(bulletKey || "").trim();
  setTailoringWorkspaceFocusedBulletKey(safeBulletKey);

  if (!safeBulletKey) {
    clearTailoringWorkspacePdfHighlight();
    if (getTailoringWorkspacePreviewMode() === "edit") {
      renderTailoringWorkspaceLiveDraftPreviewInto();
    }
    return;
  }

  const row = getTailoringWorkspaceEditableBulletRowByKey(safeBulletKey);
  if (!row) {
    syncTailoringWorkspaceFocusedCards();
    return;
  }

  if (getTailoringWorkspacePreviewMode() === "edit") {
    renderTailoringWorkspaceLiveDraftPreviewInto();
    syncTailoringWorkspaceFocusedCards();
    setTailoringWorkspacePreviewMeta(getTailoringWorkspaceDocumentPreviewMeta());

    window.requestAnimationFrame(() => {
      const activeLine = qs("tailoringWorkspaceLiveDraftPreview")
        ?.querySelector(".tailoring-workspace-doc-line--focused");
      activeLine?.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
    });
    return;
  }

  if (!tailoringWorkspacePdfState.pdfDoc) return;

  const targetTexts = [
    row.currentText,
    row.baseText,
    row.originalText,
  ]
    .map((value) => String(value || "").trim())
    .filter(Boolean);

  if (!targetTexts.length) {
    clearTailoringWorkspacePdfHighlight();
    return;
  }

  const match = findTailoringWorkspaceBestPdfMatchFromTargets(targetTexts);
  if (!match) {
    clearTailoringWorkspacePdfHighlight({ restoreMeta: false });
    setTailoringWorkspacePreviewMeta("Could not find a matching bullet in the current PDF preview.");
    return;
  }

  applyTailoringWorkspacePdfHighlight(
    match,
    String(candidateId || row.candidateId || "").trim()
  );
}

function focusTailoringWorkspaceCandidateInPreview(candidateId) {
  const safeCandidateId = String(candidateId || "").trim();
  if (!safeCandidateId) return;

  const bulletKey = getTailoringWorkspaceBulletKeyForCandidate(safeCandidateId);
  if (!bulletKey) return;

  focusTailoringWorkspaceBulletKeyInPreview(bulletKey, safeCandidateId);
}

function syncTailoringWorkspacePreviewHighlight() {
  const focusedBulletKey = String(tailoringWorkspaceState.focusedBulletKey || "").trim();
  if (focusedBulletKey) {
    focusTailoringWorkspaceBulletKeyInPreview(focusedBulletKey);
    return;
  }

  const selectedIds = getTailoringWorkspaceSelectedCandidateIds();
  if (!selectedIds.length) {
    clearTailoringWorkspacePdfHighlight();
    if (getTailoringWorkspacePreviewMode() === "edit") {
      renderTailoringWorkspaceLiveDraftPreviewInto();
    }
    return;
  }

  focusTailoringWorkspaceCandidateInPreview(selectedIds[selectedIds.length - 1]);
}

function syncTailoringWorkspaceFocusedCards() {
  const root = qs("tailoringWorkspaceInteractiveSummary");
  if (!root) return;

  const activeBulletKey = String(tailoringWorkspaceState.focusedBulletKey || "").trim();

  const cards = Array.from(
    root.querySelectorAll("[data-tailoring-focus-candidate], [data-tailoring-focus-bullet-key]")
  );

  cards.forEach((card) => {
    const candidateId = String(card.dataset.tailoringFocusCandidate || "").trim();
    const bulletKey = String(
      card.dataset.tailoringFocusBulletKey ||
        getTailoringWorkspaceBulletKeyForCandidate(candidateId)
    ).trim();

    const isActive = Boolean(activeBulletKey && bulletKey === activeBulletKey);
    const shouldMute = Boolean(activeBulletKey && bulletKey && bulletKey !== activeBulletKey);

    card.classList.toggle("tailoring-edit-card--active", isActive);
    card.classList.toggle("tailoring-edit-card--muted", shouldMute);
  });
}

function setTailoringWorkspacePreviewMeta(message) {
  const meta = qs("tailoringWorkspacePreviewMeta");
  if (meta) {
    meta.textContent = message || "";
  }
}

function updateTailoringWorkspaceZoomLabel() {
  const label = qs("tailoringWorkspaceZoomResetBtn");
  if (!label) return;
  label.textContent = `${getTailoringWorkspaceDisplayZoomPercent()}%`;
}

function getTailoringWorkspaceScrollerMetrics() {
  const scroller = qs("tailoringWorkspacePdfScroller");
  if (!scroller) return null;

  const styles = window.getComputedStyle(scroller);
  const horizontalPadding =
    parseFloat(styles.paddingLeft || "0") + parseFloat(styles.paddingRight || "0");
  const verticalPadding =
    parseFloat(styles.paddingTop || "0") + parseFloat(styles.paddingBottom || "0");

  return {
    scroller,
    availableWidth: Math.max(240, scroller.clientWidth - horizontalPadding - 4),
    availableHeight: Math.max(240, scroller.clientHeight - verticalPadding - 4),
  };
}

function clearTailoringWorkspacePinnedLayoutHeight() {
  const layout = document.querySelector(".tailoring-workspace-layout");
  if (!layout) return;

  layout.style.height = "";
  layout.style.minHeight = "";
}

function syncTailoringWorkspaceLayoutToFirstPage() {
  const layout = document.querySelector(".tailoring-workspace-layout");
  const rightPane = document.querySelector(".tailoring-workspace-pane--right");
  const scroller = qs("tailoringWorkspacePdfScroller");
  const firstPage = scroller?.querySelector(".tailoring-workspace-pdf-page");

  if (!layout || !rightPane || !scroller || !firstPage) return;

  if (window.innerWidth <= 1280) {
    clearTailoringWorkspacePinnedLayoutHeight();
    scroller.scrollTop = 0;
    scroller.scrollLeft = 0;
    return;
  }

  const scrollerStyles = window.getComputedStyle(scroller);
  const paddingY =
    parseFloat(scrollerStyles.paddingTop || "0") +
    parseFloat(scrollerStyles.paddingBottom || "0");
  const borderY =
    parseFloat(scrollerStyles.borderTopWidth || "0") +
    parseFloat(scrollerStyles.borderBottomWidth || "0");

  const currentScrollerOuterHeight = scroller.offsetHeight;
  const currentRightPaneHeight = rightPane.offsetHeight;
  const rightPaneChromeHeight = Math.max(0, currentRightPaneHeight - currentScrollerOuterHeight);

  const targetScrollerOuterHeight = Math.ceil(firstPage.offsetHeight + paddingY + borderY);
  const targetLayoutHeight = Math.ceil(rightPaneChromeHeight + targetScrollerOuterHeight);

  layout.style.height = `${targetLayoutHeight}px`;
  layout.style.minHeight = `${targetLayoutHeight}px`;

  scroller.scrollTop = 0;
  scroller.scrollLeft = 0;
}

async function computeTailoringWorkspaceFitPageScale() {
  const pdfDoc = tailoringWorkspacePdfState.pdfDoc;
  const metrics = getTailoringWorkspaceScrollerMetrics();

  if (!pdfDoc || !metrics) {
    return 1;
  }

  const firstPage = await pdfDoc.getPage(1);
  const baseViewport = firstPage.getViewport({ scale: 1 });

  const fitWidthScale = metrics.availableWidth / baseViewport.width;

  if (!Number.isFinite(fitWidthScale) || fitWidthScale <= 0) {
    return 1;
  }

  return Math.max(0.45, Math.min(2.5, fitWidthScale));
}

async function applyTailoringWorkspaceFitPageScale({ rerender = true } = {}) {
  if (!tailoringWorkspacePdfState.pdfDoc) return;

  await new Promise((resolve) => {
    window.requestAnimationFrame(() => resolve());
  });

  const fitScale = await computeTailoringWorkspaceFitPageScale();
  tailoringWorkspacePdfState.fitScale = fitScale;
  tailoringWorkspacePdfState.scale = fitScale;
  tailoringWorkspacePdfState.isFitPage = true;

  updateTailoringWorkspaceZoomLabel();

  if (rerender) {
    await renderTailoringWorkspacePdfPages();
  }
}

function scheduleTailoringWorkspaceFitPageRerender() {
  if (!tailoringWorkspacePdfState.pdfDoc || !tailoringWorkspacePdfState.isFitPage) return;

  if (tailoringWorkspacePdfState.resizeTimer) {
    window.clearTimeout(tailoringWorkspacePdfState.resizeTimer);
  }

  tailoringWorkspacePdfState.resizeTimer = window.setTimeout(async () => {
    tailoringWorkspacePdfState.resizeTimer = null;
    await applyTailoringWorkspaceFitPageScale();
  }, 80);
}

async function getTailoringWorkspacePdfJs() {
  if (!tailoringWorkspacePdfState.pdfjsPromise) {
    tailoringWorkspacePdfState.pdfjsPromise = import("/static/vendor/pdfjs/pdf.mjs").then((pdfjsLib) => {
      pdfjsLib.GlobalWorkerOptions.workerSrc = "/static/vendor/pdfjs/pdf.worker.mjs";
      return pdfjsLib;
    });
  }

  return tailoringWorkspacePdfState.pdfjsPromise;
}

async function clearTailoringWorkspacePdfView(emptyText = "Resume preview is not available for this workspace row.") {
  const empty = qs("tailoringWorkspacePreviewEmpty");
  const pages = qs("tailoringWorkspacePdfPages");

  clearTailoringWorkspacePdfHighlight({ restoreMeta: false });
  clearTailoringWorkspacePinnedLayoutHeight();

  if (tailoringWorkspacePdfState.resizeTimer) {
    window.clearTimeout(tailoringWorkspacePdfState.resizeTimer);
    tailoringWorkspacePdfState.resizeTimer = null;
  }

  if (pages) {
    pages.innerHTML = "";
    pages.classList.add("hidden");
  }

  if (empty) {
    empty.textContent = emptyText;
    empty.classList.remove("hidden");
  }

  if (tailoringWorkspacePdfState.pdfDoc) {
    try {
      await tailoringWorkspacePdfState.pdfDoc.destroy();
    } catch (err) {
      console.warn("Failed to destroy previous PDF document", err);
    }
  }

  tailoringWorkspacePdfState.pdfDoc = null;
  tailoringWorkspacePdfState.resumeName = "";
  tailoringWorkspacePdfState.pageTextIndex = [];
  tailoringWorkspacePdfState.highlightedCandidateId = "";
  tailoringWorkspacePdfState.scale = 1;
  tailoringWorkspacePdfState.fitScale = 1;
  tailoringWorkspacePdfState.isFitPage = true;

  if (getTailoringWorkspacePreviewMode() === "edit") {
    renderTailoringWorkspaceLiveDraftPreviewInto();
  }

  setTailoringWorkspacePreviewMeta(emptyText);
  updateTailoringWorkspaceZoomLabel();
}

async function renderTailoringWorkspacePdfPages() {
  const pagesRoot = qs("tailoringWorkspacePdfPages");
  const empty = qs("tailoringWorkspacePreviewEmpty");
  const pdfDoc = tailoringWorkspacePdfState.pdfDoc;

  if (!pagesRoot || !empty || !pdfDoc) return;

  const token = ++tailoringWorkspacePdfState.renderToken;
  const scale = tailoringWorkspacePdfState.scale;
  const pageCount = pdfDoc.numPages;
  const deviceScale = window.devicePixelRatio || 1;

  pagesRoot.innerHTML = "";
  pagesRoot.classList.add("hidden");
  empty.classList.remove("hidden");
  empty.textContent = `Rendering ${pageCount} page${pageCount === 1 ? "" : "s"}...`;
  setTailoringWorkspacePreviewMeta(
    `Rendering ${pageCount} page${pageCount === 1 ? "" : "s"} at ${getTailoringWorkspaceDisplayZoomPercent()}%...`
  );
  updateTailoringWorkspaceZoomLabel();

  const fragment = document.createDocumentFragment();
  const pageTextIndex = [];

  for (let pageNumber = 1; pageNumber <= pageCount; pageNumber += 1) {
    if (token !== tailoringWorkspacePdfState.renderToken) return;

    const page = await pdfDoc.getPage(pageNumber);
    const viewport = page.getViewport({ scale });

    const canvas = document.createElement("canvas");
    canvas.className = "tailoring-workspace-pdf-canvas";

    const context = canvas.getContext("2d", { alpha: false });

    canvas.width = Math.floor(viewport.width * deviceScale);
    canvas.height = Math.floor(viewport.height * deviceScale);
    canvas.style.width = `${viewport.width}px`;
    canvas.style.height = `${viewport.height}px`;

    const renderContext =
      deviceScale === 1
        ? {
            canvasContext: context,
            viewport,
          }
        : {
            canvasContext: context,
            viewport,
            transform: [deviceScale, 0, 0, deviceScale, 0, 0],
          };

    await page.render(renderContext).promise;

    const textContent = await page.getTextContent();
    const lineIndex = buildTailoringWorkspacePdfLineIndex(textContent, viewport);
    const blockIndex = buildTailoringWorkspacePdfBlockIndex(lineIndex);

    if (token !== tailoringWorkspacePdfState.renderToken) return;

    const pageShell = document.createElement("div");
    pageShell.className = "tailoring-workspace-pdf-page";
    pageShell.dataset.pageNumber = String(pageNumber);
    pageShell.style.width = `${viewport.width}px`;
    pageShell.style.height = `${viewport.height}px`;

    const overlay = document.createElement("div");
    overlay.className = "tailoring-workspace-pdf-overlay";

    pageShell.appendChild(canvas);
    pageShell.appendChild(overlay);
    fragment.appendChild(pageShell);

    pageTextIndex.push({
      pageNumber,
      width: viewport.width,
      height: viewport.height,
      lines: lineIndex,
      blocks: blockIndex,
    });
  }

  if (token !== tailoringWorkspacePdfState.renderToken) return;

  tailoringWorkspacePdfState.pageTextIndex = pageTextIndex;

  pagesRoot.innerHTML = "";
  pagesRoot.appendChild(fragment);
  pagesRoot.classList.remove("hidden");
  empty.classList.add("hidden");

  syncTailoringWorkspaceLayoutToFirstPage();

  if (getTailoringWorkspacePreviewMode() === "edit") {
    scheduleTailoringWorkspaceDocumentPreview({ immediate: true });
    setTailoringWorkspacePreviewMeta(getTailoringWorkspaceDocumentPreviewMeta());
    return;
  }

  setTailoringWorkspacePreviewMeta(buildTailoringWorkspaceDefaultPreviewMeta());
  syncTailoringWorkspacePreviewHighlight();
}

async function setTailoringWorkspacePreview(resumeName) {
  const context = getTailoringWorkspaceContext() || getScanWorkspaceContext();
  const safeName = normalizeResumePreviewName(resumeName || context?.resumeName || "");
  const nameEl = qs("tailoringWorkspacePreviewName");

  tailoringWorkspacePdfState.resumeName = safeName;
  syncTailoringWorkspacePreviewName();

  if (!safeName && !getTailoringWorkspaceBasePacketKey(context)) {
    await clearTailoringWorkspacePdfView("No resume selected for this workspace row.");
    return;
  }

  try {
    const pdfjsLib = await getTailoringWorkspacePdfJs();
    const pdfUrl = buildResumePdfFileUrl(safeName, context);
    const loadToken = ++tailoringWorkspacePdfState.renderToken;

    const empty = qs("tailoringWorkspacePreviewEmpty");
    const pages = qs("tailoringWorkspacePdfPages");

    if (pages) {
      pages.innerHTML = "";
      pages.classList.add("hidden");
    }

    if (empty) {
      empty.textContent = "Loading PDF preview...";
      empty.classList.remove("hidden");
    }

    setTailoringWorkspacePreviewMeta("Loading PDF preview...");
    updateTailoringWorkspaceZoomLabel();

    const loadingTask = pdfjsLib.getDocument(pdfUrl);
    const pdfDoc = await loadingTask.promise;

    if (loadToken !== tailoringWorkspacePdfState.renderToken) {
      try {
        await pdfDoc.destroy();
      } catch {}
      return;
    }

    if (tailoringWorkspacePdfState.pdfDoc && tailoringWorkspacePdfState.pdfDoc !== pdfDoc) {
      try {
        await tailoringWorkspacePdfState.pdfDoc.destroy();
      } catch (err) {
        console.warn("Failed to destroy stale PDF document", err);
      }
    }

    tailoringWorkspacePdfState.pdfDoc = pdfDoc;
    tailoringWorkspacePdfState.scale = 1;
    tailoringWorkspacePdfState.fitScale = 1;
    tailoringWorkspacePdfState.isFitPage = true;

    updateTailoringWorkspaceZoomLabel();
    await applyTailoringWorkspaceFitPageScale();
  } catch (err) {
    console.error("Failed to load workspace PDF preview", err);
    await clearTailoringWorkspacePdfView("Failed to load PDF preview.");
  }
}

function bindTailoringWorkspacePreviewControls() {
  const zoomOutBtn = qs("tailoringWorkspaceZoomOutBtn");
  const zoomResetBtn = qs("tailoringWorkspaceZoomResetBtn");
  const zoomInBtn = qs("tailoringWorkspaceZoomInBtn");

  if (!zoomOutBtn || !zoomResetBtn || !zoomInBtn) return;
  if (zoomOutBtn.dataset.bound === "true") return;

  zoomOutBtn.dataset.bound = "true";
  updateTailoringWorkspaceZoomLabel();

  zoomOutBtn.addEventListener("click", async () => {
    if (!tailoringWorkspacePdfState.pdfDoc) return;
    tailoringWorkspacePdfState.isFitPage = false;
    tailoringWorkspacePdfState.scale = Math.max(0.45, tailoringWorkspacePdfState.scale - 0.08);
    updateTailoringWorkspaceZoomLabel();
    await renderTailoringWorkspacePdfPages();
  });

  zoomResetBtn.addEventListener("click", async () => {
    if (!tailoringWorkspacePdfState.pdfDoc) return;
    await applyTailoringWorkspaceFitPageScale();
  });

  zoomInBtn.addEventListener("click", async () => {
    if (!tailoringWorkspacePdfState.pdfDoc) return;
    tailoringWorkspacePdfState.isFitPage = false;
    tailoringWorkspacePdfState.scale = Math.min(1.8, tailoringWorkspacePdfState.scale + 0.08);
    updateTailoringWorkspaceZoomLabel();
    await renderTailoringWorkspacePdfPages();
  });

  const modeToggleBtn = getTailoringWorkspaceModeToggleButton();
  if (modeToggleBtn && modeToggleBtn.dataset.bound !== "true") {
    modeToggleBtn.dataset.bound = "true";
    modeToggleBtn.addEventListener("click", () => {
      const nextMode = getTailoringWorkspacePreviewMode() === "pdf" ? "edit" : "pdf";
      setTailoringWorkspacePreviewMode(nextMode);
    });
  }

  syncTailoringWorkspaceModeToggleUi();

  window.addEventListener("resize", () => {
    if (!tailoringWorkspacePdfState.pdfDoc) return;
    if (tailoringWorkspacePdfState.isFitPage) {
      scheduleTailoringWorkspaceFitPageRerender();
    }
  });
}

function getResumeChoiceCandidates(row) {
  const candidates = [];
  const seen = new Set();

  [
    {
      role: "Top recommendation",
      resume_name: normalizeResumeName(row.winner_resume),
      score: row.winner_score || "",
    },
    {
      role: "Backup",
      resume_name: normalizeResumeName(row.runner_up_resume),
      score: row.runner_up_score || "",
    },
  ].forEach((item) => {
    if (!item.resume_name) return;
    const key = item.resume_name.toLowerCase();
    if (seen.has(key)) return;
    seen.add(key);
    candidates.push(item);
  });

  return candidates;
}

function buildResumeChoiceLoadingStepsHtml(steps) {
  if (!Array.isArray(steps) || !steps.length) {
    return "";
  }

  return steps.map((step) => {
    const state = String(step?.state || "pending").trim();
    const label = String(step?.label || "").trim();
    const icon = state === "complete" ? "✓" : state === "current" ? "…" : "○";

    return `
      <div class="resume-choice-loading-step resume-choice-loading-step--${escapeHtml(state)}">
        <span class="resume-choice-loading-step-icon">${escapeHtml(icon)}</span>
        <span class="resume-choice-loading-step-label">${escapeHtml(label)}</span>
      </div>
    `;
  }).join("");
}

function setResumeChoiceLoadingContent({
  title = "Generating tailoring suggestions",
  text = "Rebuilding packet and tailoring for the selected resume.",
  steps = [],
} = {}) {
  const titleEl = qs("resumeChoiceLoadingTitle");
  const textEl = qs("resumeChoiceLoadingText");
  const stepsEl = qs("resumeChoiceLoadingSteps");

  if (titleEl) titleEl.textContent = title;
  if (textEl) textEl.textContent = text;

  if (!stepsEl) return;

  if (!Array.isArray(steps) || !steps.length) {
    stepsEl.innerHTML = "";
    stepsEl.classList.add("hidden");
    return;
  }

  stepsEl.innerHTML = buildResumeChoiceLoadingStepsHtml(steps);
  stepsEl.classList.remove("hidden");
}

function resetResumeChoiceLoadingContent() {
  setResumeChoiceLoadingContent({
    title: "Generating tailoring suggestions",
    text: "Rebuilding packet and tailoring for the selected resume.",
    steps: [],
  });
}

async function persistSelectedResumeChoice(row, selectedResume) {
  await postJson("/planning/select-resume", {
    queue_rank: row.queue_rank || "",
    job_doc_id: row.job_doc_id || "",
    job_company: row.job_company || "",
    job_title: row.job_title || "",
    planning_action: row.action || "",
    decision: "SELECT_RESUME",
    selected_resume: selectedResume,
    winner_resume: row.winner_resume || "",
    winner_score: row.winner_score || "",
    runner_up_resume: row.runner_up_resume || "",
    runner_up_score: row.runner_up_score || "",
    note: "Selected from planning resume choices modal.",
  });
}

async function regenerateSelectedResumeChoice(row, selectedResume, {
  generateLlmTailoring = false,
  refreshLlmTailoring = false,
} = {}) {
  await postJson("/planning/regenerate-selected-resume", {
    queue_rank: row.queue_rank || "",
    job_doc_id: row.job_doc_id || "",
    selected_resume: selectedResume,
    generate_llm_tailoring: generateLlmTailoring,
    refresh_llm_tailoring: refreshLlmTailoring,
  });
}

function setResumeChoiceBusyState(isBusy, statusText = "") {
  resumeChoiceState.isBusy = Boolean(isBusy);

  const modal = getResumeChoiceModal();
  const overlay = qs("resumeChoiceLoadingOverlay");
  const selectBtn = qs("resumeChoiceSelectBtn");
  const llmBtn = qs("resumeChoiceGenerateLlmBtn");
  const cancelBtn = qs("resumeChoiceCancelBtn");
  const closeBtn = qs("closeResumeChoiceModalBtn");
  const selectedResume = normalizeResumeName(resumeChoiceState.selectedResume);

  const previewWrap = modal?.querySelector(".resume-choice-preview-frame-wrap");
  const previewPages = qs("resumeChoicePreviewPages");

  if (resumeChoiceState.isBusy) {
    if (previewPages) {
      previewPages.scrollTop = 0;
      previewPages.scrollLeft = 0;
    }
    if (previewWrap) {
      previewWrap.scrollTop = 0;
      previewWrap.scrollLeft = 0;
    }
  }

  modal.classList.toggle("is-busy", resumeChoiceState.isBusy);
  overlay.classList.toggle("hidden", !resumeChoiceState.isBusy);

  selectBtn.disabled = resumeChoiceState.isBusy || !selectedResume;
  if (llmBtn) {
    llmBtn.disabled = resumeChoiceState.isBusy || !selectedResume;
  }
  cancelBtn.disabled = resumeChoiceState.isBusy;
  closeBtn.disabled = resumeChoiceState.isBusy;

  qs("resumeChoiceList")
    .querySelectorAll("[data-resume-choice='true']")
    .forEach((btn) => {
      btn.disabled = resumeChoiceState.isBusy;
    });

  if (statusText) {
    qs("resumeChoiceSaveStatus").textContent = statusText;
  }
}

function resetResumeChoiceModal() {
  clearResumeChoicePreviewResources();

  resumeChoiceState = {
    row: null,
    candidates: [],
    selectedResume: "",
    isBusy: false,
    previewRequestSeq: 0,
    previewAbortController: null,
    previewObjectUrl: "",
  };

  qs("resumeChoiceCompany").textContent = "-";
  qs("resumeChoiceTitle").textContent = "-";
  qs("resumeChoiceAction").textContent = "-";
  qs("resumeChoiceGap").textContent = "-";
  qs("resumeChoiceSaveStatus").textContent = "No resume selected yet.";
  qs("resumeChoiceList").innerHTML = `<div class="resume-choice-empty">No resume choices available.</div>`;

  resetResumeChoicePreviewSurface({ clearSelection: true });

  qs("resumeChoiceLoadingOverlay").classList.add("hidden");
  qs("resumeChoiceCancelBtn").disabled = false;
  qs("closeResumeChoiceModalBtn").disabled = false;

  resetResumeChoiceLoadingContent();
}

function closeResumeChoiceModal(force = false) {
  if (resumeChoiceState.isBusy && !force) return;
  resetResumeChoiceModal();
  getResumeChoiceModal().classList.add("hidden");
}

function renderResumeChoiceCards() {
  const container = qs("resumeChoiceList");
  const selectedResume = normalizeResumeName(resumeChoiceState.selectedResume);

  if (!resumeChoiceState.candidates.length) {
    container.innerHTML = `<div class="resume-choice-empty">No resume choices available.</div>`;
    return;
  }

  container.innerHTML = resumeChoiceState.candidates.map((candidate) => {
    const resumeName = normalizeResumeName(candidate.resume_name);
    const isSelected = selectedResume && selectedResume === resumeName;

    return `
      <button
        type="button"
        class="resume-choice-card ${isSelected ? "is-selected" : ""}"
        data-resume-choice="true"
        data-resume-name="${escapeHtml(resumeName)}"
        ${resumeChoiceState.isBusy ? "disabled" : ""}
      >
        <div class="resume-choice-card-role">${escapeHtml(candidate.role)}</div>
        <div class="resume-choice-card-name">${escapeHtml(humanizeResumeDisplayName(resumeName))}</div>
        <div class="resume-choice-card-meta">Score: ${escapeHtml(candidate.score || "-")}</div>
      </button>
    `;
  }).join("");
}

async function setResumeChoicePreview(resumeName) {
  const safeName = normalizeResumeName(resumeName);
  const previewFrame = qs("resumeChoicePreviewFrame");
  const previewPages = qs("resumeChoicePreviewPages");
  const previewEmpty = qs("resumeChoicePreviewEmpty");
  const previewName = qs("resumeChoicePreviewName");
  const selectBtn = qs("resumeChoiceSelectBtn");
  const llmBtn = qs("resumeChoiceGenerateLlmBtn");
  const previewWrap = previewPages?.parentElement || qs("resumeChoicePreviewFrameWrap");

  if (!safeName) {
    clearResumeChoicePreviewResources();
    resetResumeChoicePreviewSurface({ clearSelection: true });
    return;
  }

  const loadToken = ++resumeChoiceState.previewRequestSeq;
  clearResumeChoicePreviewResources();

  resumeChoiceState.selectedResume = safeName;
  previewName.textContent = humanizeResumeDisplayName(safeName);

  if (previewFrame) {
    previewFrame.src = "about:blank";
    previewFrame.classList.add("hidden");
  }

  if (previewPages) {
    previewPages.innerHTML = "";
    previewPages.classList.add("hidden");
  }

  if (previewWrap) {
    previewWrap.scrollTop = 0;
    previewWrap.scrollLeft = 0;
  }

  previewEmpty.textContent = "Loading PDF preview...";
  previewEmpty.classList.remove("hidden");

  selectBtn.disabled = resumeChoiceState.isBusy ? true : false;
  if (llmBtn) {
    llmBtn.disabled = resumeChoiceState.isBusy ? true : false;
  }

  qs("resumeChoiceSaveStatus").textContent = `Selected: ${humanizeResumeDisplayName(safeName)}`;
  renderResumeChoiceCards();

  try {
    const pdfjsLib = await getScanWorkspacePdfJs();
    if (loadToken !== resumeChoiceState.previewRequestSeq) return;

    const pdfUrl = buildResumePdfFileUrl(safeName);
    const loadingTask = pdfjsLib.getDocument(pdfUrl);
    const pdf = await loadingTask.promise;

    if (loadToken !== resumeChoiceState.previewRequestSeq) {
      try {
        await loadingTask.destroy();
      } catch {
        // ignore stale preview cleanup failure
      }
      return;
    }

    const pageCount = Math.max(pdf.numPages || 1, 1);
    const previewInnerWidth = Math.max(
      (previewWrap?.clientWidth || previewPages?.clientWidth || 720) - 36,
      320
    );

    previewPages.innerHTML = "";

    for (let pageNumber = 1; pageNumber <= pageCount; pageNumber += 1) {
      const page = await pdf.getPage(pageNumber);
      if (loadToken !== resumeChoiceState.previewRequestSeq) return;

      const baseViewport = page.getViewport({ scale: 1 });
      const renderScale = previewInnerWidth / baseViewport.width;
      const viewport = page.getViewport({ scale: renderScale });
      const outputScale = Math.max(window.devicePixelRatio || 1, 1);

      const pageWrap = document.createElement("div");
      pageWrap.className = "resume-choice-preview-page";

      const canvas = document.createElement("canvas");
      canvas.className = "resume-choice-preview-canvas";
      canvas.width = Math.ceil(viewport.width * outputScale);
      canvas.height = Math.ceil(viewport.height * outputScale);
      canvas.style.width = `${Math.ceil(viewport.width)}px`;
      canvas.style.height = `${Math.ceil(viewport.height)}px`;

      pageWrap.appendChild(canvas);
      previewPages.appendChild(pageWrap);

      const context = canvas.getContext("2d", { alpha: false });
      await page.render({
        canvasContext: context,
        viewport,
        transform: outputScale !== 1 ? [outputScale, 0, 0, outputScale, 0, 0] : null,
      }).promise;
    }

    if (loadToken !== resumeChoiceState.previewRequestSeq) return;

    previewPages.classList.remove("hidden");
    previewEmpty.classList.add("hidden");

    if (previewWrap) {
      previewWrap.scrollTop = 0;
      previewWrap.scrollLeft = 0;
    }
  } catch (error) {
    if (loadToken !== resumeChoiceState.previewRequestSeq) return;

    if (previewPages) {
      previewPages.innerHTML = "";
      previewPages.classList.add("hidden");
    }

    previewEmpty.textContent = "Could not load PDF preview.";
    previewEmpty.classList.remove("hidden");
    console.error("Resume choice PDF preview failed", error);
  }
}

function openResumeChoiceModal(row) {
  resetResumeChoiceModal();

  const normalizedRow = {
    ...row,
    winner_resume: normalizeResumeName(row.winner_resume),
    runner_up_resume: normalizeResumeName(row.runner_up_resume),
    operator_selected_resume: normalizeResumeName(row.operator_selected_resume),
  };

  resumeChoiceState.row = normalizedRow;
  resumeChoiceState.candidates = getResumeChoiceCandidates(normalizedRow);

  qs("resumeChoiceCompany").textContent = normalizedRow.job_company || "-";
  qs("resumeChoiceTitle").textContent = normalizedRow.job_title || "-";
  qs("resumeChoiceAction").textContent = normalizedRow.action || "-";
  qs("resumeChoiceGap").textContent = normalizedRow.score_gap || "-";

  renderResumeChoiceCards();
  getResumeChoiceModal().classList.remove("hidden");

  const defaultResume =
    normalizedRow.operator_selected_resume ||
    normalizedRow.winner_resume ||
    normalizedRow.runner_up_resume;

  if (defaultResume) {
    void setResumeChoicePreview(defaultResume);
  }
}

async function submitResumeChoiceSelection({ generateLlmTailoring = false } = {}) {
  const row = resumeChoiceState.row;
  const selectedResume = normalizeResumeName(resumeChoiceState.selectedResume);

  if (!row || !selectedResume) {
    throw new Error("Select a resume before saving.");
  }

  const displayName = humanizeResumeDisplayName(selectedResume);

  const stepLabels = generateLlmTailoring
    ? [
        "Save selected resume",
        "Run LLM tailoring for selected resume",
        "Refresh planning row",
      ]
    : [
        "Save selected resume",
        "Regenerate deterministic tailoring",
        "Refresh planning row",
      ];

  const loadingTitle = generateLlmTailoring
    ? "Generating LLM tailoring"
    : "Updating selected resume";

  const loadingText = generateLlmTailoring
    ? "Saving the selected resume, then running explicit LLM tailoring for that choice."
    : "Saving the selected resume and regenerating deterministic tailoring.";

  const renderSteps = (currentIndex) => {
    const steps = stepLabels.map((label, index) => ({
      label,
      state:
        index < currentIndex
          ? "complete"
          : index === currentIndex
            ? "current"
            : "pending",
    }));

    setResumeChoiceLoadingContent({
      title: loadingTitle,
      text: loadingText,
      steps,
    });
  };

  setResumeChoiceBusyState(true, `Saving ${displayName}...`);
  renderSteps(0);
  await persistSelectedResumeChoice(row, selectedResume);

  setResumeChoiceBusyState(
    true,
    generateLlmTailoring
      ? `Running LLM tailoring for ${displayName}...`
      : `Generating deterministic tailoring for ${displayName}...`
  );
  renderSteps(1);
  await regenerateSelectedResumeChoice(row, selectedResume, {
    generateLlmTailoring,
    refreshLlmTailoring: false,
  });

  setResumeChoiceBusyState(true, "Refreshing planning row...");
  renderSteps(2);
  await loadPlanningTable();
  closeResumeChoiceModal(true);
}

function buildResumeChoiceButtonHtml(row) {
  const hasWinner = normalizeResumeName(row.winner_resume);
  const hasRunner = normalizeResumeName(row.runner_up_resume);
  const needsReview = normalizeBool(row.needs_variant_review);

  if (!needsReview || !hasWinner || !hasRunner) {
    return "";
  }

  const buttonLabel = normalizeResumeName(row.operator_selected_resume)
    ? "Review Choices"
    : "View Resume Choices";

  return `
    <button
      type="button"
      class="ghost-btn btn-sm"
      data-view-resume-choices="true"
      data-queue-rank="${escapeHtml(row.queue_rank || "")}"
      data-job-doc-id="${escapeHtml(row.job_doc_id || "")}"
      data-job-url="${escapeHtml(row.job_url || row.job_doc_id || "")}"
      data-job-company="${escapeHtml(row.job_company || "")}"
      data-job-title="${escapeHtml(row.job_title || "")}"
      data-action="${escapeHtml(row.action || "")}"
      data-score-gap="${escapeHtml(row.score_gap || "")}"
      data-winner-resume="${escapeHtml(row.winner_resume || "")}"
      data-winner-score="${escapeHtml(row.winner_score || "")}"
      data-runner-up-resume="${escapeHtml(row.runner_up_resume || "")}"
      data-runner-up-score="${escapeHtml(row.runner_up_score || "")}"
      data-operator-selected-resume="${escapeHtml(row.operator_selected_resume || "")}"
    >
      ${buttonLabel}
    </button>
  `;
}

function buildOperatorDecisionCellHtml(row) {
  const decision = String(row.operator_decision || "").trim();
  const buttonHtml = buildResumeChoiceButtonHtml(row);

  if (!decision && !buttonHtml) {
    return "-";
  }

  return `
    <div class="planning-decision-cell">
      <div class="planning-decision-label">${escapeHtml(decision || "Pending")}</div>
      ${buttonHtml}
    </div>
  `;
}

function closeTailoringModal() {
  getTailoringModal().classList.add("hidden");
}

function clearTailoringCopyResetTimer() {
  if (tailoringCopyResetTimer) {
    window.clearTimeout(tailoringCopyResetTimer);
    tailoringCopyResetTimer = null;
  }
}

function setTailoringCopyButtonState({ label = "Copy notes", disabled = true, copied = false } = {}) {
  const button = qs("copyTailoringMarkdownBtn");
  const labelEl = qs("copyTailoringMarkdownLabel");
  if (!button || !labelEl) return;

  button.disabled = disabled;
  button.classList.toggle("is-copied", copied);
  labelEl.textContent = label;
}

function syncTailoringCopyButtonState() {
  setTailoringCopyButtonState({
    label: "Copy notes",
    disabled: !String(currentTailoringMarkdownRaw || "").trim(),
    copied: false,
  });
}

function copyTextToClipboard(text) {
  if (navigator.clipboard && typeof navigator.clipboard.writeText === "function") {
    return navigator.clipboard.writeText(text);
  }

  return new Promise((resolve, reject) => {
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "fixed";
    textarea.style.top = "-1000px";
    textarea.style.left = "-1000px";
    document.body.appendChild(textarea);
    textarea.select();

    try {
      const ok = document.execCommand("copy");
      document.body.removeChild(textarea);
      if (!ok) {
        reject(new Error("Clipboard copy command failed."));
        return;
      }
      resolve();
    } catch (err) {
      document.body.removeChild(textarea);
      reject(err);
    }
  });
}

async function handleCopyTailoringMarkdown() {
  const markdown = String(currentTailoringMarkdownRaw || "").trim();
  if (!markdown) return;

  clearTailoringCopyResetTimer();

  try {
    await copyTextToClipboard(markdown);
    setTailoringCopyButtonState({
      label: "Copied",
      disabled: false,
      copied: true,
    });

    tailoringCopyResetTimer = window.setTimeout(() => {
      syncTailoringCopyButtonState();
    }, 1600);
  } catch (err) {
    setTailoringCopyButtonState({
      label: "Copy failed",
      disabled: false,
      copied: false,
    });

    tailoringCopyResetTimer = window.setTimeout(() => {
      syncTailoringCopyButtonState();
    }, 1600);

    showAppError("Failed to copy notes", err);
  }
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

function normalizeBool(value) {
  if (value === true || value === false) return value;
  const normalized = String(value || "").trim().toLowerCase();
  return normalized === "true" || normalized === "yes" || normalized === "1";
}

function buildPlanningPill(label) {
  return `<span class="pill">${escapeHtml(label || "-")}</span>`;
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

function buildCompactTextHtml(
  value,
  { maxLength = 36, emptyLabel = "-", truncate = true, wrap = false } = {}
) {
  const fullRaw = String(value || "").trim();
  const className = wrap ? "resizable-cell-text resume-cell-text" : "resizable-cell-text";

  if (!fullRaw) {
    return `<span class="${className}">${escapeHtml(emptyLabel)}</span>`;
  }

  const full = humanizeResumeDisplayName(fullRaw);
  const visible = truncate ? truncateText(full, maxLength) : full;

  return `<span class="${className}" title="${escapeHtml(full)}">${escapeHtml(visible)}</span>`;
}

function humanizeWinnerBucket(value) {
  const normalized = String(value || "").trim().toLowerCase();

  if (normalized === "strong") return "Strong";
  if (normalized === "solid") return "Solid";
  if (normalized === "moderate") return "Moderate";
  if (normalized === "weak") return "Weak";
  if (normalized === "filtered_out") return "No match";
  if (!normalized) return "-";

  return normalized.replaceAll("_", " ");
}

function humanizeFallbackStatus(value) {
  const normalized = String(value || "").trim().toLowerCase();

  if (!normalized || normalized === "disabled") return "Off";
  if (normalized === "cache_hit") return "Cache";
  if (normalized === "used") return "Used";

  return normalized.replaceAll("_", " ");
}

function deriveReviewStateLabel(row) {
  const selectionSignal = String(row.selection_signal || "").trim().toLowerCase();
  const winnerBucket = String(row.winner_bucket || "").trim().toLowerCase();
  const hasWinner = String(row.winner_resume || "").trim().length > 0;
  const needsVariantReview = normalizeBool(row.needs_variant_review);

  if (!hasWinner || winnerBucket === "filtered_out" || selectionSignal === "no_credible_match") {
    return "No match";
  }

  if (selectionSignal === "manual_review_close_call") {
    return needsVariantReview ? "Close review" : "Close call";
  }

  if (selectionSignal === "effective_tie") {
    return needsVariantReview ? "Tie review" : "Tie";
  }

  if (needsVariantReview) {
    return "Review";
  }

  return "Ready";
}

function buildMatchStrengthHtml(row) {
  return buildPlanningPill(humanizeWinnerBucket(row.winner_bucket));
}

function buildReviewStateHtml(row) {
  return buildPlanningPill(deriveReviewStateLabel(row));
}

function buildFallbackResumeHtml(row) {
  const status = String(row.llm_fallback_status || "").trim().toLowerCase();
  if (!row.llm_fallback_best_resume || !status || status === "disabled") {
    return "-";
  }
  return buildCompactTextHtml(row.llm_fallback_best_resume, { truncate: false, wrap: true });
}

function buildAdjudicationHintHtml(row) {
  const adjudicatedResume = String(row.llm_adjudication_resume || "").trim();
  if (!adjudicatedResume) return "-";

  const confidence = humanizeUnderscoreLabel(row.llm_adjudication_confidence || "", "");
  const differs = normalizeBool(row.llm_adjudication_differs_from_deterministic);
  const reason = String(row.llm_adjudication_reason || "").trim();

  const badgeLabel = differs ? "LLM differs" : "LLM agrees";
  const metaBits = [confidence].filter(Boolean);
  const metaText = metaBits.length ? metaBits.join(" · ") : "";

  return `
    <div class="planning-decision-cell" title="${escapeHtml(reason || adjudicatedResume)}">
      <div class="planning-decision-label">${buildPlanningPill(badgeLabel)}</div>
      <div>${buildCompactTextHtml(adjudicatedResume, { truncate: false, wrap: true })}</div>
      ${metaText ? `<div class="subtext">${escapeHtml(metaText)}</div>` : ""}
    </div>
  `;
}

function buildReasonHtml(value) {
  const full = String(value || "").trim();
  if (!full) return "-";
  const visible = truncateText(full, 72);
  return `<span title="${escapeHtml(full)}">${escapeHtml(visible)}</span>`;
}

function buildPlanningPriorityReason(row) {
  const operatorDecision = String(row.operator_decision || "").trim().toUpperCase();
  const selectedResume = normalizeResumeName(row.operator_selected_resume);
  const action = String(row.action || "").trim();

  if (operatorDecision === "SELECT_RESUME" && selectedResume) {
    const displayName = humanizeResumeDisplayName(selectedResume);
    return `Resume variant selected: ${displayName}. Tailoring workspace and follow-on actions now use this chosen variant for the row.`;
  }

  return String(row.queue_priority_reason || "").trim();
}

function uniqueNonEmpty(values) {
  const out = [];
  const seen = new Set();

  values.forEach((value) => {
    const text = String(value || "").trim();
    if (!text) return;

    const key = text.toLowerCase();
    if (seen.has(key)) return;

    seen.add(key);
    out.push(text);
  });

  return out;
}

function buildTailoringStatusBadge(label, tone = "muted") {
  return `
    <span class="tailoring-status-badge tailoring-status-badge--${escapeHtml(tone)}">
      ${escapeHtml(label)}
    </span>
  `;
}

function ensureTailoringWorkspaceReviewTelemetryStrip() {
  const meta = qs("tailoringWorkspaceMeta");
  const tabsShell = qs("tailoringWorkspaceSelectedTabsShell");
  const anchor = tabsShell || meta;
  if (!anchor || !anchor.parentElement) return null;

  let strip = qs("tailoringWorkspaceReviewTelemetryStrip");
  if (!strip) {
    strip = document.createElement("div");
    strip.id = "tailoringWorkspaceReviewTelemetryStrip";
    strip.className = "tailoring-workspace-review-telemetry hidden";
  }

  if (anchor.nextElementSibling !== strip) {
    anchor.insertAdjacentElement("afterend", strip);
  }

  return strip;
}

function getTailoringWorkspaceReviewFilterItems() {
  const telemetry = getTailoringWorkspaceEffectiveReviewTelemetry();
  const payload = getTailoringWorkspacePayload();
  const activeTab = String(tailoringWorkspaceState.selectedTab || "").trim();
  const activeFilter = String(tailoringWorkspaceState.reviewTelemetryFilter || "").trim();

  if (!telemetry || typeof telemetry !== "object") {
    return [];
  }

  const appReady = Array.isArray(payload?.app_ready_replacements) ? payload.app_ready_replacements : [];
  const directApplyOptional = Array.isArray(payload?.direct_apply_optional_replacements)
    ? payload.direct_apply_optional_replacements
    : [];
  const actionableCount = appReady.length + directApplyOptional.length;

  if (activeTab === "free_edit") {
    return [
      {
        key: "manual_edits",
        label: "Manual edits",
        value: Number(telemetry.manual_edit_count || 0),
        tone: Number(telemetry.manual_edit_count || 0) > 0 ? "neutral" : "muted",
        active: activeFilter === "manual_edits",
      },
    ];
  }

  if (activeTab === "ready") {
    if (!actionableCount) return [];
    return [
      {
        key: "selected",
        label: "Selected",
        value: Number(telemetry.selected_candidate_count || 0),
        tone: Number(telemetry.selected_candidate_count || 0) > 0 ? "safe" : "muted",
        active: activeFilter === "selected",
      },
    ];
  }

  return [
    {
      key: "remaining",
      label: "Remaining",
      value: Number(telemetry.remaining_to_review_count || 0),
      tone: Number(telemetry.remaining_to_review_count || 0) > 0 ? "caution" : "muted",
      active: activeFilter === "remaining",
    },
    {
      key: "accepted_as_is",
      label: "Accepted as-is",
      value: Number(telemetry.accepted_as_is_count || 0),
      tone: Number(telemetry.accepted_as_is_count || 0) > 0 ? "safe" : "muted",
      active: activeFilter === "accepted_as_is",
    },
    {
      key: "edited_after_accept",
      label: "Edited after accept",
      value: Number(telemetry.edited_after_accept_count || 0),
      tone: Number(telemetry.edited_after_accept_count || 0) > 0 ? "neutral" : "muted",
      active: activeFilter === "edited_after_accept",
    },
    {
      key: "rejected",
      label: "Rejected",
      value: Number(telemetry.rejected_count || 0),
      tone: Number(telemetry.rejected_count || 0) > 0 ? "danger" : "muted",
      active: activeFilter === "rejected",
    },
  ];
}

function buildTailoringWorkspaceReviewFilterChip(item) {
  return `
    <button
      type="button"
      class="tailoring-review-filter-chip tailoring-review-filter-chip--${escapeHtml(item.tone || "muted")} ${item.active ? "is-active" : ""}"
      data-tailoring-review-filter="${escapeHtml(item.key || "")}"
    >
      <span class="tailoring-review-filter-chip-label">${escapeHtml(item.label)}</span>
      <span class="tailoring-review-filter-chip-count">${escapeHtml(String(item.value ?? 0))}</span>
    </button>
  `;
}

function getTailoringWorkspaceFilteredReviewItems(items) {
  const safeItems = Array.isArray(items) ? items : [];
  const filterKey = String(tailoringWorkspaceState.reviewTelemetryFilter || "").trim();
  const effectiveMap = buildTailoringWorkspaceEffectiveReviewDecisionMap(
    getTailoringWorkspacePayload()
  );

  if (!filterKey || filterKey === "manual_edits" || filterKey === "selected") {
    return safeItems;
  }

  return safeItems.filter((item) => {
    const candidateId = getTailoringReplacementCandidateId(item);
    const reviewState = String(
      candidateId && effectiveMap[candidateId]
        ? effectiveMap[candidateId].state
        : "pending"
    ).trim().toLowerCase();

    if (filterKey === "remaining") {
      return reviewState === "pending";
    }
    if (filterKey === "accepted_as_is") {
      return reviewState === "accepted";
    }
    if (filterKey === "edited_after_accept") {
      return reviewState === "edited_after_accept";
    }
    if (filterKey === "rejected") {
      return reviewState === "rejected";
    }

    return true;
  });
}

function getTailoringWorkspaceFilteredFreeEditRows(payload) {
  const rows = buildTailoringWorkspaceEditableBulletRows(payload);
  const filterKey = String(tailoringWorkspaceState.reviewTelemetryFilter || "").trim();

  if (filterKey !== "manual_edits") {
    return rows;
  }

  return rows.filter((row) => row.hasManualEdit || row.changeSource === "manual_edit");
}

function renderTailoringWorkspaceReviewTelemetryStrip() {
  const strip = ensureTailoringWorkspaceReviewTelemetryStrip();
  if (!strip) return;

  const items = getTailoringWorkspaceReviewFilterItems();
  if (!items.length) {
    strip.innerHTML = "";
    strip.classList.add("hidden");
    return;
  }

  strip.innerHTML = `
    <div class="tailoring-workspace-review-telemetry-row">
      ${items.map(buildTailoringWorkspaceReviewFilterChip).join("")}
    </div>
  `;
  strip.classList.remove("hidden");

  if (strip.dataset.bound !== "true") {
    strip.dataset.bound = "true";

    strip.addEventListener("click", (event) => {
      const button = event.target.closest("[data-tailoring-review-filter]");
      if (!button) return;

      const nextFilter = String(button.dataset.tailoringReviewFilter || "").trim();
      tailoringWorkspaceState.reviewTelemetryFilter =
        tailoringWorkspaceState.reviewTelemetryFilter === nextFilter ? "" : nextFilter;

      rerenderTailoringWorkspaceSelectionView();
    });
  }
}

function deriveTailoringOverviewState(row, llmJsonArtifact) {
  const llmData = llmJsonArtifact && llmJsonArtifact.kind === "json" && llmJsonArtifact.data && typeof llmJsonArtifact.data === "object"
    ? llmJsonArtifact.data
    : {};

  const rawStatus = String(row.llm_tailoring_status || "").trim();
  const statusKey = rawStatus.toLowerCase();
  const rawErrorType = String(row.llm_error_type || "").trim();
  const parseOk = llmData.parse_ok;

  const deterministicAvailable = Boolean(row.tailoring_md);
  const llmSucceeded = (statusKey === "generated" || statusKey === "cached") && parseOk !== false;
  const llmFailed = Boolean(row.tailoring_llm_json) && (
    !llmSucceeded && (
      rawErrorType ||
      parseOk === false ||
      (statusKey && statusKey !== "disabled" && statusKey !== "pending_variant_selection" && statusKey !== "skipped_action_filter")
    )
  );

  let statusLabel = "Unavailable";
  let statusTone = "muted";

  if (deterministicAvailable || llmSucceeded) {
    statusLabel = "Suggested";
    statusTone = "success";
  } else if (llmFailed) {
    statusLabel = "Failed";
    statusTone = "danger";
  }

  const errorParts = uniqueNonEmpty([
    rawErrorType,
    llmFailed && statusKey ? rawStatus : "",
    parseOk === false && !rawErrorType && !rawStatus ? "parse_failed" : "",
  ]);

  return {
    statusLabel,
    statusTone,
    errorDisplay: errorParts.length
      ? errorParts.map(escapeHtml).join(' <span class="error-separator">●</span> ')
      : "-",
  };
}

function updateTailoringOverview(row, llmJsonArtifact) {
  const state = deriveTailoringOverviewState(row, llmJsonArtifact);

  qs("tailoringModalStatus").innerHTML = buildTailoringStatusBadge(
    state.statusLabel,
    state.statusTone
  );
  qs("tailoringModalError").innerHTML = state.errorDisplay;
}

function buildProviderBadge(provider, model, fallbackUsed) {
  const normalized = String(provider || "").trim().toLowerCase();
  if (!normalized) {
    return `<span class="summary-chip chip-muted">LLM provider unknown</span>`;
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

function buildTailoringSourceChips({ deterministicAvailable, llmGenerated, llmCached, llmFailed }) {
  const chips = [];

  if (deterministicAvailable) {
    chips.push(`<span class="summary-chip tailoring-source-chip tailoring-source-chip-deterministic">Deterministic</span>`);
  }

  if (llmGenerated) {
    chips.push(`<span class="summary-chip tailoring-source-chip tailoring-source-chip-llm">LLM generated</span>`);
  }

  if (llmCached) {
    chips.push(`<span class="summary-chip tailoring-source-chip tailoring-source-chip-llm">LLM cached</span>`);
  }

  if (llmFailed) {
    chips.push(`<span class="summary-chip tailoring-source-chip tailoring-source-chip-failed">LLM failed</span>`);
  }

  if (!chips.length) {
    chips.push(`<span class="summary-chip chip-muted">No tailoring provenance</span>`);
  }

  return chips.join("");
}

function deriveTailoringProvenance(row, llmJsonArtifact) {
  const llmData = llmJsonArtifact && llmJsonArtifact.kind === "json" && llmJsonArtifact.data && typeof llmJsonArtifact.data === "object"
    ? llmJsonArtifact.data
    : {};

  const status = String(row.llm_tailoring_status || "").trim().toLowerCase();
  const parseOk = llmData.parse_ok;
  const provider = String(llmData.provider || "").trim();
  const model = String(llmData.model || "").trim();
  const fallbackUsed = normalizeBool(llmData.fallback_used || llmData.llm_fallback_used);
  const deterministicAvailable = Boolean(row.tailoring_md);

  const llmGenerated = status === "generated" && parseOk !== false;
  const llmCached = status === "cached" && parseOk !== false;
  const llmSucceeded = llmGenerated || llmCached;

  const llmFailed = Boolean(row.tailoring_llm_json) && (
    !llmSucceeded &&
    status &&
    status !== "disabled" &&
    status !== "pending_variant_selection" &&
    status !== "skipped_action_filter"
  );

  return {
    provider,
    model,
    fallbackUsed,
    deterministicAvailable,
    llmGenerated,
    llmCached,
    llmFailed,
  };
}

function updateTailoringProvenance(row, llmJsonArtifact) {
  const meta = deriveTailoringProvenance(row, llmJsonArtifact);

  qs("tailoringProviderMeta").innerHTML = meta.llmGenerated || meta.provider
    ? buildProviderBadge(meta.provider, meta.model, meta.fallbackUsed)
    : `<span class="summary-chip chip-muted">LLM not invoked</span>`;

  qs("tailoringSourceChips").innerHTML = buildTailoringSourceChips(meta);
}

function resetTailoringModalViewState() {
  const modalScroll = qs("tailoringModalScroll");
  if (modalScroll) {
    modalScroll.scrollTop = 0;
  }

  ["tailoringInteractiveSummary", "tailoringJsonContent", "tailoringMarkdownContent", "tailoringLlmJsonContent", "tailoringPacketJsonContent"].forEach((id) => {
    const el = qs(id);
    if (el) {
      el.scrollTop = 0;
    }
  });

  collapseTailoringManualAccordions();
}

function resetTailoringModalContent() {
  currentTailoringMarkdownRaw = "";
  clearTailoringCopyResetTimer();

  qs("tailoringModalCompany").textContent = "-";
  qs("tailoringModalTitle").textContent = "-";
  qs("tailoringModalStatus").innerHTML = buildTailoringStatusBadge("Unavailable", "muted");
  qs("tailoringModalError").textContent = "-";
  qs("tailoringModalMarkdownPath").textContent = "-";
  qs("tailoringModalJsonPath").textContent = "-";
  qs("tailoringModalLlmJsonPath").textContent = "-";
  qs("tailoringModalPacketPath").textContent = "-";

  qs("tailoringProviderMeta").innerHTML = `<span class="summary-chip chip-muted">Loading provider…</span>`;
  qs("tailoringSourceChips").innerHTML = `<span class="summary-chip chip-muted">Loading provenance…</span>`;

  setTailoringSectionVisible("tailoringInteractiveSummary", true);
  setTailoringSectionVisible("tailoringPatchPreviewSummary", false);
  setTailoringSectionVisible("tailoringPatchSelectionShell", false);

  setInnerHtmlIfPresent("tailoringInteractiveSummary", `
    <div class="tailoring-empty-state">No guidance summary loaded.</div>
  `);

  setInnerHtmlIfPresent("tailoringPatchPreviewSummary", "");
  setInnerHtmlIfPresent("tailoringPatchSelectionShell", "");

  qs("tailoringJsonContent").textContent = "No artifact loaded.";
  qs("tailoringMarkdownContent").innerHTML = "<p>No artifact loaded.</p>";
  qs("tailoringLlmJsonContent").textContent = "No artifact loaded.";
  qs("tailoringPacketJsonContent").textContent = "No artifact loaded.";

  setTailoringCopyButtonState({ label: "Copy notes", disabled: true, copied: false });

  resetTailoringModalViewState();
}

function openTailoringModal(row) {
  resetTailoringModalContent();

  qs("tailoringModalCompany").textContent = row.job_company || "-";
  qs("tailoringModalTitle").textContent = row.job_title || "-";
  updateTailoringOverview(row, null);
  qs("tailoringModalMarkdownPath").textContent = row.tailoring_md || "-";
  qs("tailoringModalJsonPath").textContent = row.tailoring_json || "-";
  qs("tailoringModalLlmJsonPath").textContent = row.tailoring_llm_json || "-";
  qs("tailoringModalPacketPath").textContent = row.packet_json || "-";

  qs("tailoringProviderMeta").innerHTML = `<span class="summary-chip chip-muted">Loading provider…</span>`;
  qs("tailoringSourceChips").innerHTML = buildTailoringSourceChips({
    deterministicAvailable: Boolean(row.tailoring_md),
    llmGenerated: false,
    llmFailed: false,
  });

  setTailoringSectionVisible("tailoringInteractiveSummary", true);
  setTailoringSectionVisible("tailoringPatchPreviewSummary", false);
  setTailoringSectionVisible("tailoringPatchSelectionShell", false);

  setInnerHtmlIfPresent("tailoringInteractiveSummary", `
    <div class="tailoring-empty-state">Loading guidance summary...</div>
  `);

  setInnerHtmlIfPresent("tailoringPatchPreviewSummary", "");
  setInnerHtmlIfPresent("tailoringPatchSelectionShell", "");

  qs("tailoringJsonContent").textContent = "Loading deterministic tailoring JSON...";
  qs("tailoringMarkdownContent").innerHTML = "<p>Loading tailoring markdown...</p>";
  qs("tailoringLlmJsonContent").textContent = "Loading LLM tailoring JSON...";
  qs("tailoringPacketJsonContent").textContent = "Loading packet JSON...";

  currentTailoringMarkdownRaw = "";
  setTailoringCopyButtonState({ label: "Loading notes...", disabled: true, copied: false });

  resetTailoringModalViewState();

  getTailoringModal().classList.remove("hidden");
}

function buildPlanningEndpoint(path, outputDir = "") {
  const phase71bArtifactPathForOutputDir =
    typeof safePath !== "undefined" ? safePath :
    typeof path !== "undefined" ? path :
    typeof artifactPath !== "undefined" ? artifactPath :
    typeof tailoringJsonPath !== "undefined" ? tailoringJsonPath :
    "";
  const derivedOutputDir = phase71bDeriveRunScopedPlanningOutputDir(phase71bArtifactPathForOutputDir);
  const safeOutputDir = String(derivedOutputDir || outputDir || "").trim();
  if (!safeOutputDir) return path;

  const params = new URLSearchParams();
  params.set("output_dir", safeOutputDir);
  return `${path}?${params.toString()}`;
}


function phase71bDeriveRunScopedPlanningOutputDir(path) {
  const raw = String(path || "").replace(/\\/g, "/");
  const marker = "/application_planning/job_packets/";
  const idx = raw.indexOf(marker);
  if (idx < 0) {
    return "";
  }
  return raw.slice(0, idx + "/application_planning".length);
}


function buildArtifactUrl(path, outputDir = "") {
  const params = new URLSearchParams();
  params.set("path", path);
  const phase71bArtifactPathForOutputDir =
    typeof safePath !== "undefined" ? safePath :
    typeof path !== "undefined" ? path :
    typeof artifactPath !== "undefined" ? artifactPath :
    typeof tailoringJsonPath !== "undefined" ? tailoringJsonPath :
    "";
  const derivedOutputDir = phase71bDeriveRunScopedPlanningOutputDir(phase71bArtifactPathForOutputDir);
  const safeOutputDir = String(derivedOutputDir || outputDir || "").trim();
  if (safeOutputDir) params.set("output_dir", safeOutputDir);
  return `/planning-artifact?${params.toString()}`;
}

async function loadArtifact(path, outputDir = "") {
  const raw = String(path || "").trim();
  if (!raw || raw === ".") return null;
  return fetchJson(buildArtifactUrl(raw, outputDir));
}

function formatMarkdownInline(text) {
  return escapeHtml(text).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
}

function renderMarkdownArtifact(text, emptyLabel = "Artifact not available.") {
  const lines = String(text || "").split(/\r?\n/);
  const html = [];
  let listItems = [];

  const flushList = () => {
    if (!listItems.length) return;
    html.push(`<ul>${listItems.map((item) => `<li>${formatMarkdownInline(item)}</li>`).join("")}</ul>`);
    listItems = [];
  };

  for (const rawLine of lines) {
    const line = rawLine.trim();

    if (!line) {
      flushList();
      continue;
    }

    const heading = line.match(/^(#{1,3})\s+(.*)$/);
    if (heading) {
      flushList();
      const level = heading[1].length;
      const tag = level === 1 ? "h1" : level === 2 ? "h2" : "h3";
      html.push(`<${tag}>${formatMarkdownInline(heading[2])}</${tag}>`);
      continue;
    }

    const bullet = line.match(/^[-*]\s+(.*)$/);
    if (bullet) {
      listItems.push(bullet[1]);
      continue;
    }

    flushList();
    html.push(`<p>${formatMarkdownInline(line)}</p>`);
  }

  flushList();

  return html.join("") || `<p>${escapeHtml(emptyLabel)}</p>`;
}

function renderArtifactIntoElement(elementId, artifact, emptyLabel = "Artifact not available.") {
  const el = qs(elementId);
  if (!el) return;

  const isMarkdown = elementId === "tailoringMarkdownContent";

  if (!artifact) {
    if (isMarkdown) {
      el.innerHTML = `<p>${escapeHtml(emptyLabel)}</p>`;
    } else {
      el.textContent = emptyLabel;
    }
    el.scrollTop = 0;
    return;
  }

  if (isMarkdown) {
    el.innerHTML = renderMarkdownArtifact(artifact.text || "", emptyLabel);
    el.scrollTop = 0;
    return;
  }

  if (artifact.kind === "json") {
    el.textContent = JSON.stringify(artifact.data || {}, null, 2);
    el.scrollTop = 0;
    return;
  }

  el.textContent = artifact.text || emptyLabel;
  el.scrollTop = 0;
}

function buildTailoringTonePill(label, tone = "muted") {
  return `<span class="tailoring-tone-pill tailoring-tone-pill--${escapeHtml(tone)}">${escapeHtml(label)}</span>`;
}

function buildTailoringList(items) {
  const safeItems = Array.isArray(items) ? items.filter(Boolean) : [];
  if (!safeItems.length) {
    return `<div class="tailoring-empty-inline">None</div>`;
  }

  return `
    <ul class="tailoring-bullet-list">
      ${safeItems.map((item) => `<li>${escapeHtml(String(item))}</li>`).join("")}
    </ul>
  `;
}

function renderTopEditPriorities(items) {
  const safeItems = Array.isArray(items) ? items : [];
  if (!safeItems.length) return "";

  return `
    <section class="tailoring-section-block">
      <div class="tailoring-section-title">Highest-Impact Edits</div>
      <div class="tailoring-priority-grid">
        ${safeItems.map((item) => `
          <article class="tailoring-priority-card">
            <div class="tailoring-card-topline">
              ${buildTailoringTonePill(String(item.priority || "priority").toUpperCase(), item.priority || "muted")}
              ${buildTailoringTonePill(
                String(item.edit_type || "edit").replaceAll("_", " "),
                "neutral"
              )}
            </div>

            ${item.jd_signal ? `<div class="tailoring-card-title">${escapeHtml(item.jd_signal)}</div>` : ""}
            ${item.why_it_matters ? `<div class="tailoring-card-copy">${escapeHtml(item.why_it_matters)}</div>` : ""}
            ${item.target_section ? `<div class="tailoring-card-meta">Where to edit: ${escapeHtml(item.target_section)}</div>` : ""}
            ${item.recommended_rewrite ? `<div class="tailoring-card-rewrite">${escapeHtml(item.recommended_rewrite)}</div>` : ""}
          </article>
        `).join("")}
      </div>
    </section>
  `;
}

function renderEditCards(items) {
  const safeItems = Array.isArray(items) ? items : [];
  if (!safeItems.length) return "";

  return `
    <section class="tailoring-section-block">
      <div class="tailoring-section-title">Bullet-Level Edit Cards</div>
      <div class="tailoring-edit-card-list">
        ${safeItems.map((item, index) => {
          const displayCurrentBullet = getTailoringWorkspaceDisplayBulletText(item);
          const displayParentBullet = String(item?.parent_bullet || "").trim();
          const showParentBullet =
            displayParentBullet &&
            normalizeTailoringWorkspaceBulletText(displayParentBullet) !==
              normalizeTailoringWorkspaceBulletText(displayCurrentBullet);

          return `
            <article class="tailoring-edit-card">
              <div class="tailoring-card-topline">
                <div class="tailoring-edit-card-label">Card ${index + 1}</div>
                <div class="tailoring-chip-group">
                  ${buildTailoringTonePill(String(item.priority || "priority").toUpperCase(), item.priority || "muted")}
                  ${buildTailoringTonePill(
                    String(item.claim_safety || "claim_safety").replaceAll("_", " "),
                    item.claim_safety === "safe_strengthen" ? "safe" : item.claim_safety === "adjacent_only" ? "caution" : "danger"
                  )}
                </div>
              </div>

              ${item.jd_signal_terms?.length ? `
                <div class="tailoring-info-row">
                  <span class="tailoring-info-label">JD signal</span>
                  <span class="tailoring-info-value">${escapeHtml(item.jd_signal_terms.join(", "))}</span>
                </div>
              ` : ""}

              ${item.section ? `
                <div class="tailoring-info-row">
                  <span class="tailoring-info-label">Section</span>
                  <span class="tailoring-info-value">${escapeHtml(item.section)}</span>
                </div>
              ` : ""}

              ${item.source ? `
                <div class="tailoring-info-row">
                  <span class="tailoring-info-label">Evidence source</span>
                  <span class="tailoring-info-value">${escapeHtml(item.source)}</span>
                </div>
              ` : ""}

              ${displayCurrentBullet ? `
                <div class="tailoring-info-block">
                  <div class="tailoring-info-label">Current evidence</div>
                  <div class="tailoring-quote-block">${escapeHtml(displayCurrentBullet)}</div>
                </div>
              ` : ""}

              ${showParentBullet ? `
                <div class="tailoring-info-block">
                  <div class="tailoring-info-label">Parent bullet</div>
                  <div class="tailoring-quote-block">${escapeHtml(displayParentBullet)}</div>
                </div>
              ` : ""}

              ${item.recommended_rewrite ? `
                <div class="tailoring-info-block">
                  <div class="tailoring-info-label">Recommended rewrite direction</div>
                  <div class="tailoring-rewrite-callout">${escapeHtml(item.recommended_rewrite)}</div>
                </div>
              ` : ""}

              ${item.why_current_is_weak ? `
                <div class="tailoring-info-row">
                  <span class="tailoring-info-label">Why current wording is weak</span>
                  <span class="tailoring-info-value">${escapeHtml(item.why_current_is_weak)}</span>
                </div>
              ` : ""}

              ${item.why_rewrite_is_better ? `
                <div class="tailoring-info-row">
                  <span class="tailoring-info-label">Why this rewrite is better</span>
                  <span class="tailoring-info-value">${escapeHtml(item.why_rewrite_is_better)}</span>
                </div>
              ` : ""}

              ${item.placement_guidance ? `
                <div class="tailoring-info-row">
                  <span class="tailoring-info-label">Placement guidance</span>
                  <span class="tailoring-info-value">${escapeHtml(item.placement_guidance)}</span>
                </div>
              ` : ""}
            </article>
          `;
        }).join("")}
      </div>
    </section>
  `;
}

function renderClaimSafetyNotes(data) {
  const notes = data && typeof data === "object" ? data : {};
  const safeToStrengthen = Array.isArray(notes.safe_to_strengthen) ? notes.safe_to_strengthen : [];
  const frameCarefully = Array.isArray(notes.frame_carefully) ? notes.frame_carefully : [];
  const doNotAdd = Array.isArray(notes.do_not_add) ? notes.do_not_add : [];
  const hasContent = safeToStrengthen.length || frameCarefully.length || doNotAdd.length || notes.guardrail;

  if (!hasContent) return "";

  return `
    <section class="tailoring-section-block">
      <div class="tailoring-section-title">Do not exaggerate</div>
      <div class="tailoring-safety-grid">
        <div class="tailoring-safety-card tailoring-safety-card--safe">
          <div class="tailoring-safety-title">Safe to say</div>
          ${buildTailoringList(safeToStrengthen)}
        </div>
        <div class="tailoring-safety-card tailoring-safety-card--caution">
          <div class="tailoring-safety-title">Use carefully</div>
          ${buildTailoringList(frameCarefully)}
        </div>
        <div class="tailoring-safety-card tailoring-safety-card--danger">
          <div class="tailoring-safety-title">Do not claim</div>
          ${buildTailoringList(doNotAdd)}
        </div>
      </div>
      ${notes.guardrail ? `<div class="tailoring-guardrail">${escapeHtml(notes.guardrail)}</div>` : ""}
    </section>
  `;
}

function renderMaterialGaps(items) {
  const safeItems = Array.isArray(items) ? items : [];
  if (!safeItems.length) return "";

  return `
    <section class="tailoring-section-block">
      <div class="tailoring-section-title">Missing proof</div>
      <div class="tailoring-gap-list">
        ${safeItems.map((item) => `
          <article class="tailoring-gap-card">
            <div class="tailoring-card-title">${escapeHtml(item.label || "")}</div>
            ${item.guidance ? `<div class="tailoring-card-copy">${escapeHtml(item.guidance)}</div>` : ""}
          </article>
        `).join("")}
      </div>
    </section>
  `;
}

function renderKeepAsIs(items) {
  const safeItems = Array.isArray(items) ? items : [];
  if (!safeItems.length) return "";

  return `
    <section class="tailoring-section-block">
      <div class="tailoring-section-title">Leave these as they are</div>
      <div class="tailoring-keep-list">
        ${safeItems.map((item) => `
          <article class="tailoring-keep-card">
            ${item.section || item.source ? `
              <div class="tailoring-card-title">
                ${escapeHtml([item.section, item.source].filter(Boolean).join(" • "))}
              </div>
            ` : ""}
            ${item.reason ? `<div class="tailoring-card-copy">${escapeHtml(item.reason)}</div>` : ""}
            ${item.evidence ? `<div class="tailoring-quote-block">${escapeHtml(item.evidence)}</div>` : ""}
            ${item.overlaps?.length ? `
              <div class="tailoring-info-row">
                <span class="tailoring-info-label">Strong match</span>
                <span class="tailoring-info-value">${escapeHtml(item.overlaps.join(", "))}</span>
              </div>
            ` : ""}
          </article>
        `).join("")}
      </div>
    </section>
  `;
}

function getTailoringReplacementCandidateId(item) {
  return String(
    item?.best_candidate_id ||
    item?.replacement_candidate_id ||
    item?.candidate_id ||
    ""
  ).trim();
}

function collectTailoringWorkspaceSelectableCandidateIds(payload) {
  const ids = [];
  const seen = new Set();

  [
    ...(Array.isArray(payload?.app_ready_replacements) ? payload.app_ready_replacements : []),
    ...(Array.isArray(payload?.direct_apply_optional_replacements)
      ? payload.direct_apply_optional_replacements
      : []),
  ].forEach((item) => {
    const candidateId = getTailoringReplacementCandidateId(item);
    if (!candidateId || seen.has(candidateId)) return;
    seen.add(candidateId);
    ids.push(candidateId);
  });

  return ids;
}

function normalizeTailoringWorkspaceSelectedCandidateIds(payload, candidateIds) {
  const validIds = new Set(collectTailoringWorkspaceSelectableCandidateIds(payload));
  const normalized = [];
  const seen = new Set();

  (Array.isArray(candidateIds) ? candidateIds : []).forEach((value) => {
    const candidateId = String(value || "").trim();
    if (!candidateId || seen.has(candidateId) || !validIds.has(candidateId)) return;
    seen.add(candidateId);
    normalized.push(candidateId);
  });

  return normalized;
}

function getTailoringWorkspacePayload() {
  const artifact = tailoringWorkspaceState.artifact;
  return artifact && artifact.kind === "json" && artifact.data && typeof artifact.data === "object"
    ? artifact.data
    : null;
}

function getTailoringWorkspaceSelectedCandidateIds() {
  return Array.isArray(tailoringWorkspaceState.selectedCandidateIds)
    ? tailoringWorkspaceState.selectedCandidateIds.slice()
    : [];
}

function normalizeTailoringWorkspaceCandidateIdList(candidateIds) {
  const normalized = [];
  const seen = new Set();

  (Array.isArray(candidateIds) ? candidateIds : []).forEach((value) => {
    const candidateId = String(value || "").trim();
    if (!candidateId || seen.has(candidateId)) return;
    seen.add(candidateId);
    normalized.push(candidateId);
  });

  return normalized;
}

function haveSameTailoringWorkspaceCandidateIds(left, right) {
  const a = normalizeTailoringWorkspaceCandidateIdList(left);
  const b = normalizeTailoringWorkspaceCandidateIdList(right);

  if (a.length !== b.length) return false;
  return a.every((value, index) => value === b[index]);
}

function getTailoringWorkspacePage() {
  return document.querySelector(".tailoring-workspace-page");
}

function getScanWorkspacePage() {
  return document.querySelector(".scan-workspace-page");
}

function getScanWorkspaceContext() {
  const page = getScanWorkspacePage();
  if (!page) return null;

  return {
    jobDocId: String(page.dataset.jobDocId || "").trim(),
    tailoringJsonPath: String(page.dataset.tailoringJsonPath || "").trim(),
    tailoringJsonKey: String(page.dataset.tailoringJsonKey || "").trim(),
    resumeName: String(page.dataset.resumeName || "").trim(),
    company: String(page.dataset.jobCompany || "").trim(),
    title: String(page.dataset.jobTitle || "").trim(),
    status: String(page.dataset.tailoringStatus || "").trim(),
    tailoringMdPath: String(page.dataset.tailoringMdPath || "").trim(),
    tailoringLlmJsonPath: String(page.dataset.tailoringLlmJsonPath || "").trim(),
    packetJsonPath: String(page.dataset.packetJsonPath || "").trim(),
    packetJsonKey: String(page.dataset.packetJsonKey || "").trim(),
    planningOutputDir: String(page.dataset.planningOutputDir || "").trim(),
  };
}

function getTailoringWorkspaceContext() {
  const page = getTailoringWorkspacePage();
  if (!page) return null;

  return {
    jobDocId: String(page.dataset.jobDocId || "").trim(),
    tailoringJsonPath: String(page.dataset.tailoringJsonPath || "").trim(),
    tailoringJsonKey: String(page.dataset.tailoringJsonKey || "").trim(),
    resumeName: String(page.dataset.resumeName || "").trim(),
    packetJsonKey: String(page.dataset.packetJsonKey || "").trim(),
    planningOutputDir: String(page.dataset.planningOutputDir || "").trim(),
  };
}

function getTailoringWorkspaceSuggestionArtifactKey(context) {
  return String(context?.tailoringJsonKey || context?.tailoringJsonPath || "").trim();
}

function getTailoringWorkspaceBasePacketKey(context) {
  return String(context?.packetJsonKey || context?.packetJsonPath || "").trim();
}

function getTailoringWorkspaceArtifactKey(context) {
  return getTailoringWorkspaceSuggestionArtifactKey(context);
}

function getTailoringWorkspaceResumePreviewName(context, fallback = "") {
  return normalizeResumePreviewName(context?.resumeName || fallback);
}

async function loadTailoringWorkspaceDraft() {
  const context = getTailoringWorkspaceContext();
  if (!context || !getTailoringWorkspaceSuggestionArtifactKey(context)) return null;

  return postJson(buildPlanningEndpoint("/planning/load-workspace-draft", context.planningOutputDir), {
    tailoring_json_path: getTailoringWorkspaceSuggestionArtifactKey(context),
    selected_resume: getTailoringWorkspaceResumePreviewName(context),
  });
}

function buildTailoringWorkspaceDocumentPreviewRequest() {
  const context = getTailoringWorkspaceContext();
  const payload = getTailoringWorkspacePayload();

  if (!context || !getTailoringWorkspaceSuggestionArtifactKey(context)) {
    return null;
  }

  return {
    tailoring_json_path: getTailoringWorkspaceSuggestionArtifactKey(context),
    base_packet_path: getTailoringWorkspaceBasePacketKey(context),
    suggestion_artifact_path: getTailoringWorkspaceSuggestionArtifactKey(context),
    selected_resume: getTailoringWorkspaceResumePreviewName(context),
    selected_patch_candidate_ids: getTailoringWorkspaceSelectedCandidateIds(),
    manual_bullet_edits: normalizeTailoringWorkspaceManualBulletEdits(
      tailoringWorkspaceState.manualBulletEdits || {},
      payload
    ),
  };
}

async function fetchTailoringWorkspaceDocumentPreview() {
  const requestBody = buildTailoringWorkspaceDocumentPreviewRequest();
  if (!requestBody) {
    tailoringWorkspaceState.documentPreviewPayload = null;
    renderTailoringWorkspaceLiveDraftPreviewInto();
    return;
  }

  const requestSeq = ++tailoringWorkspaceState.documentPreviewRequestSeq;
  tailoringWorkspaceState.isDocumentPreviewLoading = true;
  renderTailoringWorkspaceLiveDraftPreviewInto();

  try {
    const response = await postJsonWithTimeout(
      buildPlanningEndpoint("/planning/render-workspace-draft-preview", getTailoringWorkspaceContext()?.planningOutputDir),
      requestBody,
      20000
    );

    if (requestSeq !== tailoringWorkspaceState.documentPreviewRequestSeq) return;
    tailoringWorkspaceState.documentPreviewPayload = response;
  } catch (err) {
    if (requestSeq !== tailoringWorkspaceState.documentPreviewRequestSeq) return;
    tailoringWorkspaceState.documentPreviewPayload = {
      ok: false,
      preview_status: "failed",
      error_message: err instanceof Error ? err.message : "Failed to render working draft preview.",
      pages: [],
    };
  } finally {
    if (requestSeq === tailoringWorkspaceState.documentPreviewRequestSeq) {
      tailoringWorkspaceState.isDocumentPreviewLoading = false;
      renderTailoringWorkspaceLiveDraftPreviewInto();
    }
  }
}

function scheduleTailoringWorkspaceDocumentPreview({ immediate = false } = {}) {
  if (tailoringWorkspaceState.documentPreviewTimer) {
    window.clearTimeout(tailoringWorkspaceState.documentPreviewTimer);
    tailoringWorkspaceState.documentPreviewTimer = null;
  }

  if (immediate) {
    void fetchTailoringWorkspaceDocumentPreview();
    return;
  }

  tailoringWorkspaceState.documentPreviewTimer = window.setTimeout(() => {
    tailoringWorkspaceState.documentPreviewTimer = null;
    void fetchTailoringWorkspaceDocumentPreview();
  }, 180);
}

function getTailoringWorkspaceSavedCandidateIds() {
  const payload = tailoringWorkspaceState.savedSelectionPayload;
  return normalizeTailoringWorkspaceCandidateIdList(
    payload && Array.isArray(payload.selected_patch_candidate_ids)
      ? payload.selected_patch_candidate_ids
      : []
  );
}

function clearTailoringWorkspacePatchPreviewSection() {
  const root = qs("tailoringWorkspacePatchPreviewSummary");
  if (root) {
    root.innerHTML = "";
  }
  setTailoringSectionVisible("tailoringWorkspacePatchPreviewSummary", false);
}

function clearTailoringWorkspaceSavedSelectionSection() {
  const root = qs("tailoringWorkspaceSavedSelectionShell");
  if (root) {
    root.innerHTML = "";
  }
  const card = qs("tailoringWorkspaceSavedSelectionCard");
  if (card) {
    card.classList.add("hidden");
    return;
  }
  setTailoringSectionVisible("tailoringWorkspaceSavedSelectionShell", false);
}

function buildTailoringWorkspaceSavedSelectionPayloadFromArtifact(payload) {
  if (!payload || typeof payload !== "object") return null;

  const selectionStatus = String(payload.selected_patch_selection_status || "").trim().toLowerCase();
  const selectedIds = normalizeTailoringWorkspaceCandidateIdList(payload.selected_patch_candidate_ids || []);

  if (selectionStatus !== "applied" || !selectedIds.length) {
    return null;
  }

  return {
    selected_patch_candidate_ids: selectedIds,
    selected_patch_selection_status: payload.selected_patch_selection_status || "applied",
    selected_patch_selection_note: payload.selected_patch_selection_note || "",
    selected_patch_set_counterfactual_preview: payload.selected_patch_set_counterfactual_preview || null,
  };
}

function buildTailoringWorkspaceSavedSelectionPayloadFromDraft(draft) {
  const safeDraft = draft && typeof draft === "object" ? draft : null;
  if (!safeDraft) return null;

  const selectedIds = normalizeTailoringWorkspaceCandidateIdList(
    safeDraft.selected_patch_candidate_ids || []
  );
  if (!selectedIds.length) return null;

  return {
    selected_patch_candidate_ids: selectedIds,
    selected_patch_selection_status: "applied",
    selected_patch_selection_note:
      String(safeDraft.note || "").trim() || "Saved from tailoring workspace draft.",
    selected_patch_set_counterfactual_preview: null,
  };
}

function getTailoringWorkspaceSavedManualBulletEdits() {
  const draft = tailoringWorkspaceState.draftPayload;
  if (!draft || typeof draft !== "object") return {};

  const raw = draft.manual_bullet_edits;
  if (!raw || typeof raw !== "object") return {};

  const normalized = {};
  Object.entries(raw).forEach(([key, value]) => {
    const safeKey = String(key || "").trim();
    if (!safeKey) return;
    normalized[safeKey] = String(value || "");
  });
  return normalized;
}

function buildTailoringWorkspaceEditableBulletKey(item) {
  const candidateId = getTailoringReplacementCandidateId(item);
  if (candidateId) {
    return `candidate:${candidateId}`;
  }

  const originalText = getTailoringWorkspaceCanonicalBulletText(item);
  if (!originalText) return "";

  return `text:${normalizeTailoringWorkspaceText(originalText)}`;
}

function collectTailoringWorkspaceEditableBullets(payload) {
  const readyItems = [
    ...(Array.isArray(payload?.app_ready_replacements) ? payload.app_ready_replacements : []),
    ...(Array.isArray(payload?.direct_apply_optional_replacements)
      ? payload.direct_apply_optional_replacements
      : []),
  ];

  const reviewItems = Array.isArray(payload?.direction_only_replacements)
    ? payload.direction_only_replacements
    : [];

  const anchorEditableItems = (Array.isArray(payload?.anchor_cards) ? payload.anchor_cards : [])
    .filter((item) => item && item.editable_in_free_edit === true);

  const buckets = [
    ...readyItems.map((item) => ({
      item,
      bucketLabel:
        String(item?.replacement_status || "").trim().toLowerCase() === "direct_apply_ready"
          ? "Ready"
          : "Optional",
    })),
    ...reviewItems.map((item) => ({
      item,
      bucketLabel: "Review",
    })),
    ...anchorEditableItems.map((item) => ({
      item,
      bucketLabel: "Review",
    })),
  ];

  const rows = [];
  const seen = new Set();

  buckets.forEach(({ item, bucketLabel }) => {
    const originalText = getTailoringWorkspaceCanonicalBulletText(item);
    if (!originalText) return;

    const bulletKey = buildTailoringWorkspaceEditableBulletKey(item);
    if (!bulletKey || seen.has(bulletKey)) return;
    seen.add(bulletKey);

    rows.push({
      bulletKey,
      candidateId: getTailoringReplacementCandidateId(item),
      originalText,
      currentText: originalText,
      bucketLabel,
    });
  });

  return rows;
}

function buildTailoringWorkspaceEditableBulletRows(payload) {
  return buildTailoringWorkspaceWorkingDraftRows(payload).map((row) => ({
    ...row,
    currentText: row.currentText,
  }));
}

function buildTailoringWorkspaceEffectiveBaseRows(payload) {
  const selectedIds = new Set(getTailoringWorkspaceSelectedCandidateIds());

  return collectTailoringWorkspaceEditableBullets(payload).map((row) => {
    const item = row.candidateId
      ? getTailoringWorkspaceCandidateItem(row.candidateId)
      : null;

    const selectedPatchText =
      row.candidateId &&
      selectedIds.has(row.candidateId) &&
      item &&
      String(item.final_replacement_text || "").trim()
        ? String(item.final_replacement_text || "").trim()
        : "";

    const baseText = selectedPatchText || row.originalText;
    const baseSource = selectedPatchText ? "selected_patch" : "original";

    return {
      ...row,
      baseText,
      baseSource,
    };
  });
}

function buildTailoringWorkspaceWorkingDraftRows(payload) {
  const manualEdits = normalizeTailoringWorkspaceManualBulletEdits(
    tailoringWorkspaceState.manualBulletEdits || {},
    payload
  );

  return buildTailoringWorkspaceEffectiveBaseRows(payload).map((row) => {
    let currentText = row.baseText;
    let changeSource = row.baseSource;

    if (Object.prototype.hasOwnProperty.call(manualEdits, row.bulletKey)) {
      currentText = String(manualEdits[row.bulletKey] || "");
      changeSource = "manual_edit";
    }

    return {
      ...row,
      currentText,
      changeSource,
      hasSelectedPatch: row.baseSource === "selected_patch",
      hasManualEdit: Object.prototype.hasOwnProperty.call(manualEdits, row.bulletKey),
    };
  });
}

function getTailoringWorkspaceDocumentPreviewMeta() {
  const preview = tailoringWorkspaceState.documentPreviewPayload;
  const pageCount = Number(preview?.page_count || 0);

  return pageCount
    ? `Read-only reconstructed draft • ${pageCount} page${pageCount === 1 ? "" : "s"}`
    : "Read-only reconstructed draft";
}

function stripTailoringWorkspaceLeadingBullet(text) {
  return String(text || "")
    .replace(/^[\s\u200b\u200c\u200d\ufeff]+/, "")
    .replace(/^(?:[●•▪◦·-][\s\u200b\u200c\u200d\ufeff]*)+/, "")
    .replace(/^[\s\u200b\u200c\u200d\ufeff]+/, "")
    .trim();
}

function splitTailoringWorkspaceInlineLabelText(text) {
  const value = String(text || "").trim();
  const match = value.match(/^([^:]{1,80}:)\s+(.*)$/);
  if (!match) return null;

  return {
    label: match[1],
    value: match[2],
  };
}

function normalizeTailoringWorkspaceFlowText(text) {
  return String(text || "")
    .replace(/[\u00a0\u200b\u200c\u200d\ufeff]/g, " ")
    .replace(/\s*[\r\n]+\s*/g, " ")
    .replace(/[ \t]{2,}/g, " ")
    .trim();
}

function splitTailoringWorkspaceInlineLabelBlocks(text) {
  const rawValue = String(text || "");
  if (!rawValue.trim()) return [];

  const startLabelPattern =
    /^([A-Z0-9][A-Za-z0-9&/()+-]*(?:\s+(?:&|[A-Z0-9][A-Za-z0-9&/()+-]*)){0,7}:)\s+(.*)$/;

  const appendToLastBlock = (blocks, extraText) => {
    const cleanExtraText = normalizeTailoringWorkspaceFlowText(extraText);
    if (!cleanExtraText || !blocks.length) return;
    blocks[blocks.length - 1].value =
      `${blocks[blocks.length - 1].value} ${cleanExtraText}`.trim();
  };

  const isLikelyInlineLabelCandidate = (candidate) => {
    const cleanCandidate = String(candidate || "").trim();
    if (!cleanCandidate.endsWith(":")) return false;

    const labelBody = cleanCandidate.slice(0, -1).trim();
    if (!labelBody) return false;

    const tokens = labelBody.split(/\s+/).filter(Boolean);
    const wordTokens = tokens.filter((token) => token !== "&");

    if (wordTokens.length < 2 || wordTokens.length > 4) return false;
    if (
      !tokens.every(
        (token) => token === "&" || /^[A-Z0-9][A-Za-z0-9/()+-]*$/.test(token)
      )
    ) {
      return false;
    }

    const ampIndex = tokens.indexOf("&");
    if (ampIndex >= 0) {
      const beforeAmpCount = tokens
        .slice(0, ampIndex)
        .filter((token) => token !== "&").length;
      const afterAmpCount = tokens
        .slice(ampIndex + 1)
        .filter((token) => token !== "&").length;

      if (beforeAmpCount < 1 || beforeAmpCount > 2) return false;
      if (afterAmpCount < 1 || afterAmpCount > 2) return false;
    }

    return true;
  };

  const findNextInlineLabelBoundary = (textValue) => {
    const normalizedValue = normalizeTailoringWorkspaceFlowText(textValue);
    if (!normalizedValue) return null;

    let best = null;

    for (let colonIndex = 0; colonIndex < normalizedValue.length; colonIndex += 1) {
      if (normalizedValue[colonIndex] !== ":") continue;
      if (
        colonIndex + 1 < normalizedValue.length &&
        !/\s/.test(normalizedValue[colonIndex + 1])
      ) {
        continue;
      }

      const windowStart = Math.max(0, colonIndex - 84);

      for (let start = windowStart; start <= colonIndex; start += 1) {
        if (start > 0 && !/\s/.test(normalizedValue[start - 1])) continue;

        const candidate = normalizedValue.slice(start, colonIndex + 1).trim();
        if (!isLikelyInlineLabelCandidate(candidate)) continue;

        const wordCount = candidate
          .slice(0, -1)
          .split(/\s+/)
          .filter((token) => token && token !== "&").length;
        const hasAmpersand = candidate.includes("&");
        const score = wordCount * 10 + (hasAmpersand ? 4 : 0) - candidate.length * 0.01;

        if (!best || score > best.score || (score === best.score && start > best.start)) {
          best = {
            start,
            label: candidate,
            score,
          };
        }
      }

      if (best) {
        return {
          start: best.start,
          label: best.label,
        };
      }
    }

    return null;
  };

  const pushStartLabelLine = (normalizedLine, blocks) => {
    let remaining = normalizedLine;

    while (remaining) {
      const startMatch = remaining.match(startLabelPattern);
      if (!startMatch) {
        appendToLastBlock(blocks, remaining);
        return;
      }

      const currentLabel = startMatch[1];
      const currentValue = normalizeTailoringWorkspaceFlowText(startMatch[2]);
      const nextBoundary = findNextInlineLabelBoundary(currentValue);

      if (!nextBoundary) {
        blocks.push({
          label: currentLabel,
          value: currentValue,
        });
        return;
      }

      blocks.push({
        label: currentLabel,
        value: normalizeTailoringWorkspaceFlowText(
          currentValue.slice(0, nextBoundary.start)
        ),
      });

      remaining = normalizeTailoringWorkspaceFlowText(
        currentValue.slice(nextBoundary.start)
      );
    }
  };

  const consumeNormalizedLine = (normalizedLine, blocks) => {
    if (!normalizedLine) return;

    const startMatch = normalizedLine.match(startLabelPattern);
    if (startMatch) {
      pushStartLabelLine(normalizedLine, blocks);
      return;
    }

    const boundary = findNextInlineLabelBoundary(normalizedLine);
    if (!boundary) {
      appendToLastBlock(blocks, normalizedLine);
      return;
    }

    appendToLastBlock(blocks, normalizedLine.slice(0, boundary.start));
    pushStartLabelLine(
      normalizeTailoringWorkspaceFlowText(normalizedLine.slice(boundary.start)),
      blocks
    );
  };

  const blocks = [];
  rawValue
    .split(/\r?\n+/)
    .map((line) => normalizeTailoringWorkspaceFlowText(line))
    .filter(Boolean)
    .forEach((line) => {
      consumeNormalizedLine(line, blocks);
    });

  if (blocks.length > 1) {
    return blocks.filter((block) => block && block.label);
  }

  const flattenedBlocks = [];
  consumeNormalizedLine(normalizeTailoringWorkspaceFlowText(rawValue), flattenedBlocks);
  return flattenedBlocks.filter((block) => block && block.label);
}

function getTailoringWorkspaceSectionKeyFromRow(row) {
  if (!row || !row.is_section_heading) return "";
  return normalizeTailoringWorkspaceFlowText(String(row.text || ""))
    .replace(/\s+/g, " ")
    .trim()
    .toUpperCase();
}

function isTailoringWorkspaceRenderableTextRow(row) {
  if (!row) return false;
  if (String(row.kind || "").trim() === "paired_row") return false;
  const text = normalizeTailoringWorkspaceFlowText(String(row.text || ""));
  return Boolean(text);
}

function isTailoringWorkspaceDateRangeText(text) {
  const clean = normalizeTailoringWorkspaceFlowText(text);
  if (!clean || clean.length > 48) return false;

  const month = "(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\\.?";
  const year = "(?:19|20)\\d{2}";
  const point = `(?:${month}\\s+${year}|${year}|Present|Current)`;

  return new RegExp(
    `^${point}(?:\\s*[\\-–—]\\s*${point})?$`,
    "i"
  ).test(clean);
}

function splitTailoringWorkspaceTrailingDateRange(text) {
  const clean = normalizeTailoringWorkspaceFlowText(text);
  if (!clean) return null;

  // A pure date line must never be split again.
  if (isTailoringWorkspaceDateRangeText(clean)) {
    return null;
  }

  const month = "(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\\.?";
  const year = "(?:19|20)\\d{2}";
  const monthYear = `${month}\\s+${year}`;
  const point = `(?:${monthYear}|${year}|Present|Current)`;

  const match = clean.match(
    new RegExp(
      `^(.*?\\S)\\s+((?:${monthYear}|${year}|Present|Current)(?:\\s*[\\-–—]\\s*${point})?)$`,
      "i"
    )
  );

  if (!match) return null;

  const leftText = normalizeTailoringWorkspaceFlowText(match[1]);
  const rightText = normalizeTailoringWorkspaceFlowText(match[2]);

  if (!leftText || !rightText) return null;
  if (isTailoringWorkspaceDateRangeText(leftText)) return null;
  if (!isTailoringWorkspaceDateRangeText(rightText)) return null;

  return { leftText, rightText };
}

function isLikelyTailoringWorkspaceInlineHeaderWithContinuation(
  currentRow,
  nextRow,
  currentSection
) {
  if (!currentRow || !nextRow) return false;

  const sectionKey = String(currentSection || "").trim().toUpperCase();
  if (!sectionKey) return false;

  if (
    sectionKey === "PROFESSIONAL EXPERIENCE" ||
    sectionKey === "WORK EXPERIENCE"
  ) {
    return false;
  }

  if (currentRow.is_bullet || currentRow.is_section_heading) return false;
  if (nextRow.is_bullet || nextRow.is_section_heading) return false;

  if (String(currentRow.kind || "").trim() === "paired_row") return false;
  if (String(nextRow.kind || "").trim() === "paired_row") return false;

  const split = splitTailoringWorkspaceTrailingDateRange(currentRow.text || "");
  if (!split) return false;

  const nextText = normalizeTailoringWorkspaceFlowText(String(nextRow.text || ""));
  if (!nextText) return false;

  if (splitTailoringWorkspaceTrailingDateRange(nextText)) return false;
  if (/:\s*/.test(nextText)) return false;

  const currentIndent = Number(currentRow.left_indent_pt || 0);
  const nextIndent = Number(nextRow.left_indent_pt || 0);
  const nextGap = Number(nextRow.gap_before || 0);

  if (Math.abs(nextIndent - currentIndent) > 12) return false;
  if (nextGap > 10) return false;

  return true;
}

function isLikelyTailoringWorkspaceExperiencePairedRowContinuation(
  previousRow,
  currentRow,
  currentSection,
  nextRow
) {
  if (!previousRow || !currentRow) return false;

  const sectionKey = String(currentSection || "").trim().toUpperCase();
  if (
    sectionKey !== "PROFESSIONAL EXPERIENCE" &&
    sectionKey !== "WORK EXPERIENCE"
  ) {
    return false;
  }

  if (String(previousRow.kind || "").trim() !== "paired_row") return false;
  if (currentRow.is_bullet || currentRow.is_section_heading) return false;
  if (String(currentRow.kind || "").trim() === "paired_row") return false;

  const currentText = normalizeTailoringWorkspaceFlowText(
    String(currentRow.text || "")
  );
  if (!currentText) return false;
  if (isTailoringWorkspaceDateRangeText(currentText)) return false;
  if (/:\s*/.test(currentText)) return false;

  const previousIndent = Number(previousRow.left_indent_pt || 0);
  const currentIndent = Number(currentRow.left_indent_pt || 0);
  const gapBefore = Number(currentRow.gap_before || 0);

  if (Math.abs(currentIndent - previousIndent) > 12) return false;
  if (gapBefore > 10) return false;

  if (nextRow && !nextRow.is_bullet && !nextRow.is_section_heading) {
    return false;
  }

  return true;
}

function isLikelyTailoringWorkspaceSplitHeaderDatePair(
  currentRow,
  nextRow,
  nextNextRow,
  currentSection
) {
  if (!currentRow || !nextRow) return false;

  const sectionKey = String(currentSection || "").trim().toUpperCase();
  if (!sectionKey) return false;

  if (
    sectionKey === "PROFESSIONAL EXPERIENCE" ||
    sectionKey === "WORK EXPERIENCE"
  ) {
    return false;
  }

  if (currentRow.is_bullet || currentRow.is_section_heading) return false;
  if (nextRow.is_bullet || nextRow.is_section_heading) return false;

  if (String(currentRow.kind || "").trim() === "paired_row") return false;
  if (String(nextRow.kind || "").trim() === "paired_row") return false;

  const leftText = normalizeTailoringWorkspaceFlowText(String(currentRow.text || ""));
  const rightText = normalizeTailoringWorkspaceFlowText(String(nextRow.text || ""));

  if (!leftText || !rightText) return false;
  if (isTailoringWorkspaceDateRangeText(leftText)) return false;
  if (!isTailoringWorkspaceDateRangeText(rightText)) return false;

  const currentAlign = String(currentRow.alignment || "left").trim().toLowerCase();
  const nextAlign = String(nextRow.alignment || "left").trim().toLowerCase();

  if (currentAlign !== "left") return false;
  if (nextAlign !== "right") return false;

  const currentIndent = Number(currentRow.left_indent_pt || 0);
  const nextIndent = Number(nextRow.left_indent_pt || 0);
  const nextGap = Number(nextRow.gap_before || 0);

  if (Math.abs(nextIndent - currentIndent) > 12) return false;
  if (nextGap > 4) return false;

  if (nextNextRow) {
    if (nextNextRow.is_bullet || nextNextRow.is_section_heading) return false;

    const nextNextText = normalizeTailoringWorkspaceFlowText(
      String(nextNextRow.text || "")
    );
    const nextNextAlign = String(nextNextRow.alignment || "left").trim().toLowerCase();
    const nextNextIndent = Number(nextNextRow.left_indent_pt || 0);

    if (!nextNextText) return false;
    if (isTailoringWorkspaceDateRangeText(nextNextText)) return false;
    if (nextNextAlign !== "left") return false;
    if (Math.abs(nextNextIndent - currentIndent) > 12) return false;
  }

  return true;
}

function isLikelyTailoringWorkspaceBulletContinuation(
  previousRow,
  currentRow,
  currentSection,
  nextRow
) {
  if (!previousRow || !currentRow) return false;
  if (!previousRow.is_bullet) return false;
  if (currentRow.is_bullet || currentRow.is_section_heading) return false;
  if (String(currentRow.kind || "").trim() === "paired_row") return false;

  const sectionKey = String(currentSection || "").trim().toUpperCase();
  if (!sectionKey) return false;
  if (sectionKey === "SKILLS" || sectionKey === "ACADEMIC PROJECTS") return false;

  const currentText = normalizeTailoringWorkspaceFlowText(String(currentRow.text || ""));
  if (!currentText) return false;

  const nextIsBullet = Boolean(nextRow && nextRow.is_bullet);
  if (nextIsBullet) return false;

  const gapBefore = Number(currentRow.gap_before || 0);
  if (gapBefore > 10) return false;

  if (/^[A-Z][A-Za-z0-9&/,+()\- ]{1,80}:\s*/.test(currentText)) {
    return false;
  }

  return true;
}

function isLikelyTailoringWorkspaceSkillsContinuation(
  previousRow,
  currentRow,
  currentSection
) {
  if (!previousRow || !currentRow) return false;
  if (String(currentSection || "").trim().toUpperCase() !== "SKILLS") return false;
  if (String(previousRow.presentation_role || "").trim() !== "skills_line") return false;
  if (currentRow.is_bullet || currentRow.is_section_heading) return false;
  if (String(currentRow.kind || "").trim() === "paired_row") return false;

  const currentText = normalizeTailoringWorkspaceFlowText(String(currentRow.text || ""));
  if (!currentText) return false;
  if (/:\s*/.test(currentText)) return false;

  const previousIndent = Number(previousRow.left_indent_pt || 0);
  const currentIndent = Number(currentRow.left_indent_pt || 0);
  const gapBefore = Number(currentRow.gap_before || 0);

  if (currentIndent <= previousIndent + 2) return false;
  if (gapBefore > 6) return false;

  return true;
}

function buildTailoringWorkspacePreviewPresentationRows(
  rows,
  {
    initialSection = "",
    allowDocumentHeaderRoles = true,
  } = {}
) {
  const sourceRows = Array.isArray(rows) ? rows : [];
  const presentedRows = [];
  let currentSection = String(initialSection || "").trim().toUpperCase();
  let sawFirstSectionHeading = Boolean(currentSection);
  let preSectionTextCount = 0;

  for (let index = 0; index < sourceRows.length; index += 1) {
    const row = sourceRows[index];
    if (!row || typeof row !== "object") continue;

    const cloned = { ...row };
    const nextRow = sourceRows[index + 1] || null;
    const nextNextRow = sourceRows[index + 2] || null;
    const nextIsBullet = Boolean(nextRow && nextRow.is_bullet);
    const previousPresentedRow =
      presentedRows.length > 0 ? presentedRows[presentedRows.length - 1] : null;

    const sectionKey = getTailoringWorkspaceSectionKeyFromRow(cloned);
    if (sectionKey) {
      currentSection = sectionKey;
      sawFirstSectionHeading = true;
      cloned.presentation_role = "";
      presentedRows.push(cloned);
      continue;
    }

    if (
      isLikelyTailoringWorkspaceExperiencePairedRowContinuation(
        previousPresentedRow,
        cloned,
        currentSection,
        nextRow
      )
    ) {
      const previousLeftText = normalizeTailoringWorkspaceFlowText(
        String(previousPresentedRow.left_text || "")
      );
      const continuationText = normalizeTailoringWorkspaceFlowText(
        String(cloned.text || "")
      );

      previousPresentedRow.left_text = `${previousLeftText} ${continuationText}`.trim();
      previousPresentedRow.patched = Boolean(
        previousPresentedRow.patched || cloned.patched
      );

      if (!previousPresentedRow.patch_source && cloned.patch_source) {
        previousPresentedRow.patch_source = cloned.patch_source;
      }

      continue;
    }

    if (
      isTailoringWorkspaceRenderableTextRow(cloned) &&
      isTailoringWorkspaceRenderableTextRow(nextRow) &&
      isLikelyTailoringWorkspaceSplitHeaderDatePair(
        cloned,
        nextRow,
        nextNextRow,
        currentSection
      )
    ) {
      presentedRows.push({
        ...cloned,
        kind: "paired_row",
        text: "",
        left_text: normalizeTailoringWorkspaceFlowText(String(cloned.text || "")),
        right_text: normalizeTailoringWorkspaceFlowText(String(nextRow.text || "")),
        presentation_role: "",
        alignment: "left",
      });
      index += 1;
      continue;
    }

    if (
      isLikelyTailoringWorkspaceSkillsContinuation(
        previousPresentedRow,
        cloned,
        currentSection
      )
    ) {
      const prevText = normalizeTailoringWorkspaceFlowText(
        String(previousPresentedRow.text || "")
      );
      const nextText = normalizeTailoringWorkspaceFlowText(String(cloned.text || ""));
      previousPresentedRow.text = `${prevText} ${nextText}`.trim();
      previousPresentedRow.patched = Boolean(
        previousPresentedRow.patched || cloned.patched
      );
      if (!previousPresentedRow.patch_source && cloned.patch_source) {
        previousPresentedRow.patch_source = cloned.patch_source;
      }
      continue;
    }

    if (
      isLikelyTailoringWorkspaceBulletContinuation(
        previousPresentedRow,
        cloned,
        currentSection,
        nextRow
      )
    ) {
      const prevText = normalizeTailoringWorkspaceFlowText(
        String(previousPresentedRow.text || "")
      );
      const nextText = normalizeTailoringWorkspaceFlowText(String(cloned.text || ""));
      previousPresentedRow.text = `${prevText} ${nextText}`.trim();
      previousPresentedRow.patched = Boolean(
        previousPresentedRow.patched || cloned.patched
      );
      if (!previousPresentedRow.patch_source && cloned.patch_source) {
        previousPresentedRow.patch_source = cloned.patch_source;
      }
      continue;
    }

    if (
      currentSection === "PROFESSIONAL EXPERIENCE" &&
      isTailoringWorkspaceRenderableTextRow(cloned) &&
      !cloned.is_bullet &&
      !cloned.is_section_heading &&
      nextIsBullet
    ) {
      const split = splitTailoringWorkspaceTrailingDateRange(cloned.text || "");
      if (split) {
        presentedRows.push({
          ...cloned,
          kind: "paired_row",
          text: "",
          left_text: split.leftText,
          right_text: split.rightText,
          presentation_role: "",
          alignment: "left",
        });
        continue;
      }
    }

    const isTextRow = isTailoringWorkspaceRenderableTextRow(cloned);
    if (
      currentSection === "EDUCATION" &&
      isTailoringWorkspaceRenderableTextRow(cloned) &&
      isTailoringWorkspaceRenderableTextRow(nextRow) &&
      isLikelyTailoringWorkspaceInlineHeaderWithContinuation(
        cloned,
        nextRow,
        currentSection
      )
    ) {
      const split = splitTailoringWorkspaceTrailingDateRange(cloned.text || "");
      if (split) {
        presentedRows.push({
          ...cloned,
          kind: "paired_row",
          text: "",
          left_text: split.leftText,
          right_text: split.rightText,
          presentation_role: "",
          alignment: "left",
        });
        continue;
      }
    }
    cloned.presentation_role = "";

    if (!sawFirstSectionHeading && isTextRow && !cloned.is_bullet) {
      if (preSectionTextCount === 0) {
        cloned.presentation_role = "header_name";
        cloned.alignment = "center";
      } else if (preSectionTextCount === 1) {
        cloned.presentation_role = "header_contact";
        cloned.alignment = "center";
      }
      preSectionTextCount += 1;
    } else if (
      currentSection === "PROFESSIONAL EXPERIENCE" &&
      isTextRow &&
      !cloned.is_bullet &&
      !cloned.is_section_heading &&
      nextIsBullet
    ) {
      cloned.presentation_role = "experience_header";
      cloned.alignment = "left";
    } else if (
      currentSection === "ACADEMIC PROJECTS" &&
      isTextRow &&
      !cloned.is_bullet &&
      !cloned.is_section_heading &&
      nextIsBullet
    ) {
      cloned.presentation_role = "experience_header";
      cloned.alignment = "left";
    } else if (
      currentSection === "SKILLS" &&
      isTextRow &&
      !cloned.is_bullet &&
      !cloned.is_section_heading &&
      /:\s*/.test(normalizeTailoringWorkspaceFlowText(String(cloned.text || "")))
    ) {
      cloned.presentation_role = "skills_line";
      cloned.alignment = "left";
    }

    presentedRows.push(cloned);
  }

  return presentedRows.map((row) => ({
    ...row,
    focused: isTailoringWorkspaceFocusedPresentationRow(row),
  }));
}

function renderTailoringWorkspaceLinkedText(text, linkItems = []) {
  const rawText = normalizeTailoringWorkspaceFlowText(String(text || ""));
  const links = (Array.isArray(linkItems) ? linkItems : [])
    .map((item) => ({
      label: String(item?.label || "").trim(),
      uri: String(item?.uri || "").trim(),
    }))
    .filter((item) => item.label && item.uri)
    .map((item) => ({
      ...item,
      pos: rawText.indexOf(item.label),
    }))
    .filter((item) => item.pos >= 0)
    .sort((left, right) => left.pos - right.pos);

  if (!links.length) return escapeHtml(rawText);

  let html = "";
  let lastEnd = 0;
  links.forEach((item) => {
    if (item.pos < lastEnd) return;
    html += escapeHtml(rawText.slice(lastEnd, item.pos));
    html += `
      <a
        class="tailoring-workspace-doc-link"
        href="${escapeHtml(item.uri)}"
        title="${escapeHtml(item.uri)}"
        target="_blank"
        rel="noopener noreferrer"
      >${escapeHtml(item.label)}</a>
    `;
    lastEnd = item.pos + item.label.length;
  });
  html += escapeHtml(rawText.slice(lastEnd));
  return html;
}

function renderTailoringWorkspaceStructuredRow(row) {
  const kind = String(row?.kind || "").trim();
  const gapBefore = Math.max(0, Math.min(28, Number(row?.gap_before || 0)));
  const indent = Math.max(0, Math.min(240, Number(row?.left_indent_pt || 0)));

  if (kind === "paired_row") {
    return `
      <div class="tailoring-workspace-doc-paired-row" style="margin-top:${gapBefore}px; padding-left:${indent}px;">
        <div class="tailoring-workspace-doc-paired-row-left">${escapeHtml(normalizeTailoringWorkspaceFlowText(String(row.left_text || "")))}</div>
        <div class="tailoring-workspace-doc-paired-row-right">${escapeHtml(normalizeTailoringWorkspaceFlowText(String(row.right_text || "")))}</div>
      </div>
    `;
  }

  const rawText = String(row?.text || "");
  const normalizedText = normalizeTailoringWorkspaceFlowText(rawText);
  const alignment = String(row?.alignment || "left").trim().toLowerCase();
  const patched = Boolean(row?.patched);
  const patchSource = String(row?.patch_source || "").trim();
  const decision =
    typeof normalizeScanWorkspaceAnnotationDecision === "function"
      ? normalizeScanWorkspaceAnnotationDecision(
          row?.decision || row?.scan_decision || row?.review_state || row?.state
        )
      : String(row?.decision || row?.scan_decision || row?.review_state || row?.state || "").trim().toLowerCase();
  const isManualEdit = patchSource === "manual_edit";
  const isRejected = decision === "rejected" || patchSource === "rejected";
  const isDirectReplacement =
    patchSource === "selected_patch" ||
    patchSource === "direct_replacement" ||
    String(row?.row_action_type || row?.action_type || "").trim() === "direct_replacement";
  const isHeading = Boolean(row?.is_section_heading);
  const isBullet = Boolean(row?.is_bullet);
  const presentationRole = String(row?.presentation_role || "").trim();
  const normalizedPresentationRole = presentationRole.replace(/_/g, "-");

  const inlineLabelBlocks =
    !isHeading && !isBullet && alignment === "left"
      ? [splitTailoringWorkspaceInlineLabelText(rawText)].filter(Boolean)
      : [];

  const extraClasses = [
    "tailoring-workspace-doc-line",
    isHeading ? "tailoring-workspace-doc-line--heading" : "",
    isBullet ? "tailoring-workspace-doc-line--bullet" : "",
    normalizedPresentationRole
      ? `tailoring-workspace-doc-line--${normalizedPresentationRole}`
      : "",
    patched ? "tailoring-workspace-doc-line--changed" : "",
    isManualEdit ? "tailoring-workspace-doc-line--manual" : "",
    isRejected ? "tailoring-workspace-doc-line--rejected" : "",
    isDirectReplacement ? "tailoring-workspace-doc-line--selected" : "",
    row?.focused ? "tailoring-workspace-doc-line--focused" : "",
  ].filter(Boolean).join(" ");

  const alignStyle =
    alignment === "center"
      ? "text-align:center;"
      : alignment === "right"
        ? "text-align:right;"
        : "text-align:left;";

  let contentHtml = "";

  if (isBullet) {
    contentHtml = `
      <div class="tailoring-workspace-doc-bullet-row" style="padding-left:${indent}px;">
        <div class="tailoring-workspace-doc-bullet-marker">•</div>
        <div class="tailoring-workspace-doc-line-copy tailoring-workspace-doc-bullet-copy">
          <span class="scan-workspace-preview-line-text">${escapeHtml(normalizeTailoringWorkspaceFlowText(stripTailoringWorkspaceLeadingBullet(rawText)))}</span>
        </div>
      </div>
    `;
  } else if (inlineLabelBlocks.length) {
    contentHtml = `
      <div
        class="tailoring-workspace-doc-line-copy tailoring-workspace-doc-multi-inline-label"
        style="${alignStyle} padding-left:${alignment === "left" ? indent : 0}px;"
      >
        ${inlineLabelBlocks.map((block) => `
          <div class="tailoring-workspace-doc-inline-label-row">
            <span class="scan-workspace-preview-line-text">
              <span class="tailoring-workspace-doc-inline-label-prefix">${escapeHtml(block.label)}</span> ${escapeHtml(normalizeTailoringWorkspaceFlowText(block.value))}
            </span>
          </div>
        `).join("")}
      </div>
    `;
  } else {
    contentHtml = `
      <div
        class="tailoring-workspace-doc-line-copy"
        style="${alignStyle} padding-left:${alignment === "left" ? indent : 0}px;"
      >
        <span class="scan-workspace-preview-line-text">${renderTailoringWorkspaceLinkedText(normalizedText, row?.link_items || [])}</span>
      </div>
    `;
  }

  return `
    <div class="${extraClasses}" style="margin-top:${gapBefore}px;">
      ${contentHtml}
      ${isHeading ? `<div class="tailoring-workspace-doc-section-rule"></div>` : ""}
    </div>
  `;
}

function renderTailoringWorkspaceDocumentMirror() {
  if (
    tailoringWorkspaceState.isDocumentPreviewLoading &&
    !tailoringWorkspaceState.documentPreviewPayload
  ) {
    return `
      <div class="tailoring-empty-state">
        Loading reconstructed draft preview...
      </div>
    `;
  }

  const preview = tailoringWorkspaceState.documentPreviewPayload;
  const pages = Array.isArray(preview?.pages) ? preview.pages : [];

  if (!pages.length) {
    const errorMessage = String(preview?.error_message || "").trim();
    return `
      <div class="tailoring-empty-state">
        ${escapeHtml(errorMessage || "Working draft preview is not available.")}
      </div>
    `;
  }

  const showPageLabel = pages.length > 1;
  let carrySection = "";
  const normalizedPages = pages.map((page, pageIndex) => {
    const presentationRows = buildTailoringWorkspacePreviewPresentationRows(
      page.rows,
      {
        initialSection: carrySection,
        allowDocumentHeaderRoles: pageIndex === 0,
      }
    );

    presentationRows.forEach((row) => {
      const sectionKey = getTailoringWorkspaceSectionKeyFromRow(row);
      if (sectionKey) {
        carrySection = sectionKey;
      }
    });

    return {
      ...page,
      presentation_rows: presentationRows,
    };
  });

  const changedCount = normalizedPages.reduce(
    (count, page) =>
      count +
      (Array.isArray(page.presentation_rows)
        ? page.presentation_rows.filter((row) => row && row.patched).length
        : 0),
    0
  );

  return `
    <div class="tailoring-workspace-doc-mirror">
      ${normalizedPages.map((page) => `
        <section class="tailoring-workspace-doc-page">
          ${showPageLabel ? `
            <div class="tailoring-workspace-doc-page-header">
              <span class="tailoring-workspace-doc-page-number">
                Page ${escapeHtml(String(page.page_number || ""))}
              </span>
            </div>
          ` : ""}

          <div class="tailoring-workspace-doc-page-body">
            ${(Array.isArray(page.presentation_rows) ? page.presentation_rows : [])
              .map((row) => renderTailoringWorkspaceStructuredRow(row))
              .join("")}
          </div>
        </section>
      `).join("")}
    </div>
  `;
}

function renderTailoringWorkspaceLiveDraftPreviewInto() {
  const root = qs("tailoringWorkspaceLiveDraftPreview");
  if (!root) return;

  root.innerHTML = renderTailoringWorkspaceDocumentMirror();
}

function getTailoringWorkspaceEditableBulletBaseMap(payload) {
  const baseMap = {};

  buildTailoringWorkspaceEffectiveBaseRows(payload).forEach((row) => {
    if (!row.bulletKey) return;
    baseMap[row.bulletKey] = String(row.baseText || "");
  });

  return baseMap;
}

function normalizeTailoringWorkspaceManualBulletEdits(editMap, payload) {
  const baseMap = getTailoringWorkspaceEditableBulletBaseMap(payload);
  const normalized = {};

  Object.entries(editMap || {}).forEach(([rawKey, rawValue]) => {
    const bulletKey = String(rawKey || "").trim();
    if (!bulletKey || !Object.prototype.hasOwnProperty.call(baseMap, bulletKey)) return;

    const nextValue = String(rawValue || "");
    const originalValue = String(baseMap[bulletKey] || "");

    if (nextValue !== originalValue) {
      normalized[bulletKey] = nextValue;
    }
  });

  return normalized;
}

function normalizeTailoringWorkspaceReviewDecisionMap(value) {
  const allowed = new Set(["pending", "accepted", "edited_after_accept", "rejected"]);
  const normalized = {};

  Object.entries(value || {}).forEach(([rawCandidateId, rawValue]) => {
    const candidateId = String(rawCandidateId || "").trim();
    if (!candidateId) return;

    let state = "pending";
    let note = "";

    if (rawValue && typeof rawValue === "object" && !Array.isArray(rawValue)) {
      state = String(rawValue.state || "").trim().toLowerCase() || "pending";
      note = String(rawValue.note || "").trim();
    } else {
      state = String(rawValue || "").trim().toLowerCase() || "pending";
    }

    if (!allowed.has(state)) return;

    normalized[candidateId] = { state, note };
  });

  return normalized;
}

function getTailoringWorkspaceSavedReviewDecisionMap() {
  const draft = tailoringWorkspaceState.draftPayload;
  if (!draft || typeof draft !== "object") return {};
  return normalizeTailoringWorkspaceReviewDecisionMap(draft.rewrite_review_decisions || {});
}

function getTailoringWorkspaceCurrentReviewDecisionMap() {
  return normalizeTailoringWorkspaceReviewDecisionMap(
    tailoringWorkspaceState.rewriteReviewDecisions || {}
  );
}

function getTailoringWorkspaceBulletKeyForCandidate(candidateId) {
  const item = getTailoringWorkspaceCandidateItem(candidateId);
  return item ? buildTailoringWorkspaceEditableBulletKey(item) : "";
}

function getTailoringWorkspaceBaseTextForCandidate(candidateId) {
  const item = getTailoringWorkspaceCandidateItem(candidateId);
  if (!item) return "";

  const selectedIds = new Set(getTailoringWorkspaceSelectedCandidateIds());
  const currentText = getTailoringWorkspaceCanonicalBulletText(item);
  const selectedPatchText = selectedIds.has(candidateId)
    ? String(item.final_replacement_text || "").trim()
    : "";

  return selectedPatchText || currentText;
}

function getTailoringWorkspaceEditableBulletRowByKey(bulletKey) {
  const safeBulletKey = String(bulletKey || "").trim();
  if (!safeBulletKey) return null;

  const payload = getTailoringWorkspacePayload();
  if (!payload) return null;

  return (
    buildTailoringWorkspaceEditableBulletRows(payload).find(
      (row) => String(row.bulletKey || "").trim() === safeBulletKey
    ) || null
  );
}

function setTailoringWorkspaceFocusedBulletKey(bulletKey) {
  tailoringWorkspaceState.focusedBulletKey = String(bulletKey || "").trim();
}

function getTailoringWorkspaceFocusedPreviewTexts() {
  const row = getTailoringWorkspaceEditableBulletRowByKey(
    tailoringWorkspaceState.focusedBulletKey
  );
  if (!row) return [];

  return [row.currentText, row.baseText, row.originalText]
    .map((value) => normalizeTailoringWorkspaceText(value))
    .filter(Boolean);
}

function doesTailoringWorkspacePreviewTextMatch(targetText, rowText) {
  const safeTarget = normalizeTailoringWorkspaceText(targetText);
  const safeRow = normalizeTailoringWorkspaceText(rowText);

  if (!safeTarget || !safeRow) return false;

  return (
    safeTarget === safeRow ||
    safeTarget.includes(safeRow) ||
    safeRow.includes(safeTarget)
  );
}

function isTailoringWorkspaceFocusedPresentationRow(row) {
  const focusTexts = getTailoringWorkspaceFocusedPreviewTexts();
  if (!focusTexts.length) return false;

  const rowTexts = [
    String(row?.text || ""),
    stripTailoringWorkspaceLeadingBullet(String(row?.text || "")),
    String(row?.left_text || ""),
    String(row?.right_text || ""),
  ]
    .map((value) => normalizeTailoringWorkspaceFlowText(value))
    .map((value) => normalizeTailoringWorkspaceText(value))
    .filter(Boolean);

  return rowTexts.some((rowText) =>
    focusTexts.some((focusText) =>
      doesTailoringWorkspacePreviewTextMatch(focusText, rowText)
    )
  );
}

function buildTailoringWorkspaceEffectiveReviewDecisionMap(payload) {
  const safePayload = payload || getTailoringWorkspacePayload();
  const explicitMap = getTailoringWorkspaceCurrentReviewDecisionMap();
  const manualEdits = normalizeTailoringWorkspaceManualBulletEdits(
    tailoringWorkspaceState.manualBulletEdits || {},
    safePayload
  );
  const derived = {};

  getTailoringWorkspaceSelectableItems(safePayload).forEach((item) => {
    const candidateId = getTailoringReplacementCandidateId(item);
    if (!candidateId) return;

    const current = explicitMap[candidateId] || { state: "pending", note: "" };
    let state = String(current.state || "pending").trim().toLowerCase();
    const note = String(current.note || "").trim();

    if (state === "accepted" || state === "edited_after_accept") {
      const bulletKey = buildTailoringWorkspaceEditableBulletKey(item);
      const manualText = String(manualEdits[bulletKey] || "");
      const baseText = getTailoringWorkspaceBaseTextForCandidate(candidateId);

      const manualNorm = normalizeTailoringWorkspaceText(manualText);
      const baseNorm = normalizeTailoringWorkspaceText(baseText);

      state = manualNorm && baseNorm && manualNorm !== baseNorm
        ? "edited_after_accept"
        : "accepted";
    }

    derived[candidateId] = { state, note };
  });

  return derived;
}

function getTailoringWorkspaceEffectiveReviewState(item) {
  const candidateId = getTailoringReplacementCandidateId(item);
  if (!candidateId) return "pending";

  const map = buildTailoringWorkspaceEffectiveReviewDecisionMap(getTailoringWorkspacePayload());
  return map[candidateId]?.state || "pending";
}

function buildTailoringWorkspaceReviewTelemetry(payload) {
  const safePayload = payload || getTailoringWorkspacePayload();
  if (!safePayload) return null;

  const decisionMap = buildTailoringWorkspaceEffectiveReviewDecisionMap(safePayload);
  const surfacedIds = [];
  const seen = new Set();

  getTailoringWorkspaceSelectableItems(safePayload).forEach((item) => {
    const candidateId = getTailoringReplacementCandidateId(item);
    if (!candidateId || seen.has(candidateId)) return;
    seen.add(candidateId);
    surfacedIds.push(candidateId);
  });

  let pendingCount = 0;
  let acceptedCount = 0;
  let acceptedAsIsCount = 0;
  let editedAfterAcceptCount = 0;
  let rejectedCount = 0;

  const pendingCandidateIds = [];
  const reviewedCandidateIds = [];

  surfacedIds.forEach((candidateId) => {
    const state = String(decisionMap[candidateId]?.state || "pending").trim().toLowerCase();

    if (state === "pending") {
      pendingCount += 1;
      pendingCandidateIds.push(candidateId);
    } else {
      reviewedCandidateIds.push(candidateId);
    }

    if (state === "accepted") {
      acceptedCount += 1;
      acceptedAsIsCount += 1;
    } else if (state === "edited_after_accept") {
      acceptedCount += 1;
      editedAfterAcceptCount += 1;
    } else if (state === "rejected") {
      rejectedCount += 1;
    }
  });

  const manualEdits = normalizeTailoringWorkspaceManualBulletEdits(
    tailoringWorkspaceState.manualBulletEdits || {},
    safePayload
  );

  return {
    pending_count: pendingCount,
    accepted_count: acceptedCount,
    accepted_as_is_count: acceptedAsIsCount,
    edited_after_accept_count: editedAfterAcceptCount,
    rejected_count: rejectedCount,
    reviewed_count: acceptedCount + rejectedCount,
    remaining_to_review_count: pendingCount,
    selected_candidate_count: getTailoringWorkspaceSelectedCandidateIds().length,
    manual_edit_count: Object.keys(manualEdits).length,
    reviewed_candidate_ids: reviewedCandidateIds,
    pending_candidate_ids: pendingCandidateIds,
  };
}

function getTailoringWorkspaceEffectiveReviewTelemetry() {
  const payload = getTailoringWorkspacePayload();
  if (payload) {
    return buildTailoringWorkspaceReviewTelemetry(payload);
  }

  const draft = tailoringWorkspaceState.draftPayload;
  if (
    draft &&
    typeof draft === "object" &&
    draft.rewrite_review_telemetry &&
    typeof draft.rewrite_review_telemetry === "object"
  ) {
    return draft.rewrite_review_telemetry;
  }

  return null;
}

function getTailoringWorkspaceReviewDecisionTone(state) {
  if (state === "accepted") return "safe";
  if (state === "edited_after_accept") return "neutral";
  if (state === "rejected") return "danger";
  return "muted";
}

function getTailoringWorkspaceReviewDecisionLabel(state) {
  if (state === "accepted") return "Accepted as-is";
  if (state === "edited_after_accept") return "Edited after accept";
  if (state === "rejected") return "Rejected";
  return "Pending";
}

function getReplacementReviewState(item, reviewDecisionMap = {}) {
  const candidateId = getTailoringReplacementCandidateId(item);
  if (!candidateId) return "pending";

  const decision = reviewDecisionMap && typeof reviewDecisionMap === "object"
    ? reviewDecisionMap[candidateId]
    : null;

  const state = decision && typeof decision === "object"
    ? String(decision.state || "").trim().toLowerCase()
    : String(decision || "").trim().toLowerCase();

  return state || "pending";
}

function setTailoringWorkspaceReviewDecision(candidateId, state, note = "") {
  const safeCandidateId = String(candidateId || "").trim();
  const safeState = String(state || "").trim().toLowerCase();
  if (!safeCandidateId || !safeState) return;

  const next = {
    ...getTailoringWorkspaceCurrentReviewDecisionMap(),
  };

  next[safeCandidateId] = {
    state: safeState,
    note: String(note || "").trim(),
  };

  tailoringWorkspaceState.rewriteReviewDecisions = next;
  tailoringWorkspaceState.previewPayload = null;
  tailoringWorkspaceState.previewReadyKey = "";
  tailoringWorkspaceState.activeInlineScoreKey = "";
  rerenderTailoringWorkspaceSelectionView();
  focusTailoringWorkspaceCandidateInPreview(safeCandidateId);
}

async function openTailoringWorkspaceManualEditForCandidate(candidateId) {
  const safeCandidateId = String(candidateId || "").trim();
  if (!safeCandidateId) return;

  const bulletKey = getTailoringWorkspaceBulletKeyForCandidate(safeCandidateId);
  if (!bulletKey) return;

  tailoringWorkspaceState.activeReviewEditCandidateId = safeCandidateId;
  tailoringWorkspaceState.selectedTab = "free_edit";
  tailoringWorkspaceState.reviewTelemetryFilter = "";
  rerenderTailoringWorkspaceSelectionView();
  scrollTailoringWorkspaceLeftPaneToTabs();
  focusTailoringWorkspaceCandidateInPreview(safeCandidateId);

  window.requestAnimationFrame(() => {
    const textarea = document.querySelector(
      `[data-tailoring-free-edit-key="${CSS.escape(bulletKey)}"]`
    );
    if (!textarea) return;

    textarea.focus();
    textarea.setSelectionRange(textarea.value.length, textarea.value.length);
    textarea.scrollIntoView({ behavior: "smooth", block: "center" });
  });
}

function syncTailoringWorkspaceReviewDecisionFromTextarea(bulletKey) {
  const payload = getTailoringWorkspacePayload();
  if (!payload) return;

  const rows = buildTailoringWorkspaceEditableBulletRows(payload);
  const row = rows.find((item) => item.bulletKey === bulletKey);
  const candidateId = String(row?.candidateId || "").trim();
  if (!candidateId) return;

  const currentMap = getTailoringWorkspaceCurrentReviewDecisionMap();
  const currentDecision = currentMap[candidateId] || { state: "pending", note: "" };
  const isReviewEditFlow = tailoringWorkspaceState.activeReviewEditCandidateId === candidateId;

  if (!isReviewEditFlow && !["accepted", "edited_after_accept"].includes(currentDecision.state)) {
    return;
  }

  const manualEdits = normalizeTailoringWorkspaceManualBulletEdits(
    tailoringWorkspaceState.manualBulletEdits || {},
    payload
  );
  const manualText = String(manualEdits[bulletKey] || "");
  const baseText = getTailoringWorkspaceBaseTextForCandidate(candidateId);

  const manualNorm = normalizeTailoringWorkspaceText(manualText);
  const baseNorm = normalizeTailoringWorkspaceText(baseText);
  const hasDiff = Boolean(manualNorm && baseNorm && manualNorm !== baseNorm);

  const next = { ...currentMap };

  if (hasDiff) {
    next[candidateId] = {
      state: "edited_after_accept",
      note: currentDecision.note || "",
    };
  } else if (isReviewEditFlow) {
    delete next[candidateId];
  } else if (currentDecision.state === "edited_after_accept") {
    next[candidateId] = {
      state: "accepted",
      note: currentDecision.note || "",
    };
  }

  tailoringWorkspaceState.rewriteReviewDecisions = next;
}

function haveSameTailoringWorkspaceManualBulletEdits(left, right, payload) {
  const a = normalizeTailoringWorkspaceManualBulletEdits(left, payload);
  const b = normalizeTailoringWorkspaceManualBulletEdits(right, payload);

  const aKeys = Object.keys(a).sort();
  const bKeys = Object.keys(b).sort();

  if (aKeys.length !== bKeys.length) return false;

  return aKeys.every((key, index) => {
    const otherKey = bKeys[index];
    return key === otherKey && a[key] === b[otherKey];
  });
}

function getTailoringWorkspaceResolvedScorePreview({
  originalScore = null,
  projectedScore = null,
  projectedDelta = null,
} = {}) {
  const hasOriginal = isFinitePreviewNumber(originalScore);
  const hasProjected = isFinitePreviewNumber(projectedScore);
  const hasDelta = isFinitePreviewNumber(projectedDelta);

  if (!hasOriginal && !hasProjected) {
    return null;
  }

  const resolvedNewScore = hasProjected ? projectedScore : originalScore;
  const resolvedDelta = hasDelta ? projectedDelta : 0;

  return {
    newScore: resolvedNewScore,
    delta: resolvedDelta,
    deltaNumber: Number(String(resolvedDelta).replaceAll(",", "").trim()),
  };
}

function renderTailoringWorkspaceScorePills({
  originalScore = null,
  projectedScore = null,
  projectedDelta = null,
} = {}) {
  const resolved = getTailoringWorkspaceResolvedScorePreview({
    originalScore,
    projectedScore,
    projectedDelta,
  });

  if (!resolved) return "";

  return `
    ${buildTailoringTonePill(`New ${formatScore100(resolved.newScore)}`, "neutral")}
    ${buildTailoringTonePill(
      `Δ ${formatSignedScore100(resolved.delta)}`,
      getTailoringWorkspaceInlineDeltaTone(resolved.deltaNumber)
    )}
  `;
}

function getTailoringWorkspaceInlineScorePreview() {
  const payload = tailoringWorkspaceState.previewPayload;
  if (!payload || typeof payload !== "object") return null;

  const preview =
    payload.selected_patch_set_counterfactual_preview &&
    typeof payload.selected_patch_set_counterfactual_preview === "object"
      ? payload.selected_patch_set_counterfactual_preview
      : null;

  return getTailoringWorkspaceResolvedScorePreview({
    originalScore: preview?.original_final_score ?? payload.original_score,
    projectedScore: preview?.projected_final_score ?? payload.projected_score,
    projectedDelta: preview?.projected_overall_delta ?? payload.projected_delta,
  });
}

function getTailoringWorkspaceInlineDeltaTone(deltaNumber) {
  if (!Number.isFinite(deltaNumber)) return "muted";
  if (deltaNumber > 0) return "safe";
  if (deltaNumber < 0) return "danger";
  return "caution";
}

function refreshTailoringWorkspaceInlineScoreControls() {
  const payload = getTailoringWorkspacePayload();
  const manualEdits = normalizeTailoringWorkspaceManualBulletEdits(
    tailoringWorkspaceState.manualBulletEdits || {},
    payload
  );
  const inlinePreview = getTailoringWorkspaceInlineScorePreview();
  const previewReadyKey = String(tailoringWorkspaceState.previewReadyKey || "").trim();

  document.querySelectorAll("[data-tailoring-free-edit-action]").forEach((button) => {
    const bulletKey = String(button.dataset.tailoringFreeEditAction || "").trim();
    const scoreSlot = document.querySelector(
      `[data-tailoring-free-edit-score="${CSS.escape(bulletKey)}"]`
    );

    const hasEdit = Object.prototype.hasOwnProperty.call(manualEdits, bulletKey);
    const isPreviewReady = previewReadyKey === bulletKey;
    const showInlineScore = Boolean(inlinePreview && isPreviewReady);
    const showPreview = isPreviewReady;

    if (scoreSlot) {
      scoreSlot.innerHTML = showInlineScore
        ? `
          ${buildTailoringTonePill(`New ${formatScore100(inlinePreview.newScore)}`, "neutral")}
          ${buildTailoringTonePill(`Δ ${formatSignedScore100(inlinePreview.delta)}`, getTailoringWorkspaceInlineDeltaTone(inlinePreview.deltaNumber))}
        `
        : "";
    }

    button.classList.toggle("ghost-btn", !showPreview);
    button.classList.toggle("tailoring-inline-save-btn", showPreview);

    if (tailoringWorkspaceState.isSaving) {
      button.textContent = showPreview ? "Saving..." : "Continue";
      button.disabled = true;
      return;
    }

    if (tailoringWorkspaceState.isPreviewing) {
      button.textContent = isPreviewReady ? "Working..." : "Continue";
      button.disabled = true;
      return;
    }

    button.textContent = showPreview ? "Save" : "Continue";
    button.disabled = !hasEdit;
  });
}

function renderTailoringWorkspaceFreeEditSection(payload) {
  const rows = getTailoringWorkspaceFilteredFreeEditRows(payload);
  const filterKey = String(tailoringWorkspaceState.reviewTelemetryFilter || "").trim();
  const showingManualEditsOnly = filterKey === "manual_edits";

  if (!rows.length) {
    return `
      <section class="tailoring-section-block">
        <div class="tailoring-section-title">Free edit</div>
        <div class="tailoring-card-copy">
          ${showingManualEditsOnly
            ? "No manually edited bullets are available yet."
            : "No surfaced bullets are available for manual editing on this row yet."}
        </div>
      </section>
    `;
  }

  return `
    <section class="tailoring-section-block">
      <div class="tailoring-section-title">Free edit</div>
      <div class="tailoring-card-copy">
        ${showingManualEditsOnly
          ? `Showing ${rows.length} manually edited bullet${rows.length === 1 ? "" : "s"}.`
          : "Edit the surfaced bullets directly. The button below previews the whole current draft score, then turns into Save."}
      </div>

      <div class="tailoring-edit-card-list">
        ${rows.map((row, index) => {
          const bucketTone =
            row.bucketLabel === "Ready"
              ? "safe"
              : row.bucketLabel === "Optional"
                ? "caution"
                : "muted";

          const sourceLabel =
            row.baseSource === "selected_patch"
              ? "Selected rewrite base"
              : "Original base";

          const sourceTone =
            row.baseSource === "selected_patch"
              ? "caution"
              : "muted";

          return `
            <article
              class="tailoring-edit-card tailoring-edit-card--compact tailoring-edit-card--clickable"
              data-tailoring-focus-bullet-key="${escapeHtml(row.bulletKey)}"
            >
              <div class="tailoring-card-topline tailoring-card-topline--compact">
                <div class="tailoring-edit-card-label">Bullet ${index + 1}</div>

                <div class="tailoring-chip-group tailoring-chip-group--compact">
                  ${buildTailoringTonePill(row.bucketLabel, bucketTone)}
                  ${buildTailoringTonePill(sourceLabel, sourceTone)}
                  ${row.hasManualEdit ? buildTailoringTonePill("Manual edit", "neutral") : ""}
                </div>
              </div>

              <div class="tailoring-info-block tailoring-info-block--compact">
                <div class="tailoring-info-label">Original bullet</div>
                <div class="tailoring-quote-block">${escapeHtml(row.originalText)}</div>
              </div>

              <div class="tailoring-info-block tailoring-info-block--compact">
                <div class="tailoring-info-label">Editable draft text</div>
                <textarea
                  class="tailoring-free-edit-textarea"
                  data-tailoring-free-edit-key="${escapeHtml(row.bulletKey)}"
                >${escapeHtml(row.currentText)}</textarea>
              </div>

              <div class="tailoring-edit-card-footer tailoring-edit-card-footer--inline">
                <div
                  class="tailoring-chip-group"
                  data-tailoring-free-edit-score="${escapeHtml(row.bulletKey)}"
                ></div>

                <button
                  type="button"
                  class="ghost-btn"
                  data-tailoring-free-edit-action="${escapeHtml(row.bulletKey)}"
                >
                  Continue
                </button>
              </div>
            </article>
          `;
        }).join("")}
      </div>
    </section>
  `;
}

function updateTailoringWorkspaceSelectionActionBar() {
  const statusEl = qs("tailoringWorkspaceSelectionStatus");
  const discardBtn = qs("tailoringWorkspaceDiscardBtn");
  const downloadBtn = qs("tailoringWorkspaceDownloadBtn");
  const saveBtn = qs("tailoringWorkspaceSaveSelectionBtn");

  if (!statusEl || !discardBtn || !downloadBtn || !saveBtn) return;

  const payload = getTailoringWorkspacePayload();
  const selectedIds = getTailoringWorkspaceSelectedCandidateIds();
  const savedIds = getTailoringWorkspaceSavedCandidateIds();
  const hasSelection = selectedIds.length > 0;
  const matchesSavedSelection = haveSameTailoringWorkspaceCandidateIds(selectedIds, savedIds);
  const hasSavedSelection = savedIds.length > 0;

  const currentManualEdits = normalizeTailoringWorkspaceManualBulletEdits(
    tailoringWorkspaceState.manualBulletEdits || {},
    payload
  );
  const savedManualEdits = normalizeTailoringWorkspaceManualBulletEdits(
    getTailoringWorkspaceSavedManualBulletEdits(),
    payload
  );
  const manualMatchesSaved = haveSameTailoringWorkspaceManualBulletEdits(
    currentManualEdits,
    savedManualEdits,
    payload
  );

  const currentReviewDecisions = getTailoringWorkspaceCurrentReviewDecisionMap();
  const savedReviewDecisions = getTailoringWorkspaceSavedReviewDecisionMap();
  const reviewMatchesSaved =
    JSON.stringify(currentReviewDecisions) === JSON.stringify(savedReviewDecisions);

  const hasManualEdits = Object.keys(currentManualEdits).length > 0;
  const hasSavedManualEdits = Object.keys(savedManualEdits).length > 0;
  const hasSavedReviewDecisions = Object.keys(savedReviewDecisions).length > 0;

  const manualDraftChanged = !manualMatchesSaved;
  const reviewDraftChanged = !reviewMatchesSaved;
  const isFreeEditTab = tailoringWorkspaceState.selectedTab === "free_edit";

  const hasAnySavedState =
    hasSavedSelection || hasSavedManualEdits || hasSavedReviewDecisions;

  const hasUnsavedSelectionChange =
    hasSavedSelection ? !matchesSavedSelection : hasSelection;

  const hasUnsavedManualChange =
    hasSavedManualEdits ? manualDraftChanged : hasManualEdits;

  const hasUnsavedReviewChange =
    hasSavedReviewDecisions
      ? reviewDraftChanged
      : Object.keys(currentReviewDecisions).length > 0;

  const hasUnsavedWorkspaceChanges =
    hasUnsavedSelectionChange || hasUnsavedManualChange || hasUnsavedReviewChange;

  const context = getTailoringWorkspaceContext();
  const hasResume = Boolean(context && String(context.resumeName || "").trim());

  const discardTooltip = discardBtn.closest(".tailoring-workspace-action-tooltip");
  const downloadTooltip = downloadBtn.closest(".tailoring-workspace-action-tooltip");
  const saveTooltip = saveBtn.closest(".tailoring-workspace-action-tooltip");
  const discardIcon = discardBtn.querySelector(".tailoring-workspace-icon");

  if (tailoringWorkspaceState.isSaving) {
    statusEl.textContent = isFreeEditTab
      ? "Saving current draft..."
      : "Saving workspace draft...";
  } else if (tailoringWorkspaceState.isPreviewing) {
    statusEl.textContent = isFreeEditTab
      ? "Scoring current draft..."
      : "Previewing score impact for the current workspace draft...";
  } else if (hasUnsavedManualChange && !hasUnsavedSelectionChange && !hasUnsavedReviewChange) {
    statusEl.textContent = hasManualEdits
      ? `Free Edit has unsaved changes across ${Object.keys(currentManualEdits).length} bullet${Object.keys(currentManualEdits).length === 1 ? "" : "s"}.`
      : "Free Edit reverted to the original text. Save to clear the previously saved manual edits.";
  } else if (hasUnsavedReviewChange && !hasUnsavedSelectionChange && !hasUnsavedManualChange) {
    statusEl.textContent = "Review decisions changed. Save to update the workspace draft.";
  } else if (hasSelection && hasUnsavedSelectionChange) {
    statusEl.textContent = `${selectedIds.length} suggestion${selectedIds.length === 1 ? "" : "s"} selected. Save to update the workspace draft.`;
  } else if (!hasSelection && !hasManualEdits && !Object.keys(currentReviewDecisions).length) {
    statusEl.textContent = hasAnySavedState
      ? "No active unsaved changes. A saved workspace draft exists for this row."
      : "No actionable suggestions selected yet.";
  } else if (hasSavedSelection && matchesSavedSelection && !hasUnsavedManualChange && !hasUnsavedReviewChange) {
    statusEl.textContent = `${selectedIds.length} suggestion${selectedIds.length === 1 ? "" : "s"} selected. This matches the current saved selection.`;
  } else {
    statusEl.textContent = "Workspace draft loaded.";
  }

  const shouldShowRevert = hasAnySavedState;
  const canRevert = hasAnySavedState && !tailoringWorkspaceState.isSaving && hasUnsavedWorkspaceChanges;

  if (shouldShowRevert) {
    discardBtn.disabled = !canRevert;
    discardBtn.setAttribute("aria-label", "Revert to saved draft");

    if (discardTooltip) {
      discardTooltip.dataset.tooltip = "Revert to saved draft";
    }

    if (discardIcon) {
      discardIcon.classList.remove("tailoring-workspace-icon--discard");
      discardIcon.classList.add("tailoring-workspace-icon--revert");
    }
  } else {
    discardBtn.disabled =
      tailoringWorkspaceState.isSaving ||
      (!hasSelection && !hasManualEdits && !Object.keys(currentReviewDecisions).length);

    discardBtn.setAttribute("aria-label", "Discard changes");

    if (discardTooltip) {
      discardTooltip.dataset.tooltip = "Discard changes";
    }

    if (discardIcon) {
      discardIcon.classList.remove("tailoring-workspace-icon--revert");
      discardIcon.classList.add("tailoring-workspace-icon--discard");
    }
  }

  saveBtn.disabled =
    tailoringWorkspaceState.isSaving ||
    tailoringWorkspaceState.isPreviewing ||
    !hasUnsavedWorkspaceChanges;

  const exportState = getTailoringWorkspaceExportState();

  downloadBtn.disabled = !exportState.hasResume;

  if (downloadTooltip) {
    downloadTooltip.dataset.tooltip = exportState.tooltip;
  }
  downloadBtn.setAttribute("aria-label", exportState.tooltip);

  if (saveTooltip) {
    saveTooltip.dataset.tooltip = tailoringWorkspaceState.isSaving ? "Saving changes..." : "Save changes";
  }
  saveBtn.setAttribute(
    "aria-label",
    tailoringWorkspaceState.isSaving ? "Saving changes..." : "Save changes"
  );
}

function renderTailoringWorkspacePatchPreviewSection(payload) {
  const root = qs("tailoringWorkspacePatchPreviewSummary");
  if (!root) return;

  const preview = payload && payload.selected_patch_set_counterfactual_preview
    ? payload.selected_patch_set_counterfactual_preview
    : null;

  const previewStatus = String(payload?.preview_status || "").trim();
  const previewNote = String(payload?.preview_note || "").trim();
  const explicitSelectedIds = Array.isArray(payload?.selected_patch_candidate_ids)
    ? payload.selected_patch_candidate_ids
    : [];
  const manualEditCount = Number(payload?.manual_edit_count || 0);
  const originalScore = payload?.original_score;
  const projectedScore = payload?.projected_score;
  const projectedDelta = payload?.projected_delta;

  const hasRenderedPreview = Boolean(
    preview ||
    previewStatus ||
    manualEditCount > 0
  );

  if (!hasRenderedPreview) {
    clearTailoringWorkspacePatchPreviewSection();
    return;
  }

  const synthesizedPreview = preview || (
    originalScore !== undefined ||
    projectedScore !== undefined ||
    projectedDelta !== undefined
      ? {
          status: previewStatus || "preview_only",
          note: previewNote || "Workspace draft preview loaded.",
          original_final_score: originalScore,
          projected_final_score: projectedScore,
          projected_overall_delta: projectedDelta,
          projected_dimension_deltas: {},
          scorer_visible_evidence_changed: false,
          selected_patch_count: explicitSelectedIds.length,
          selected_candidate_ids: explicitSelectedIds,
          selection_mode: "workspace_draft",
        }
      : null
  );

  root.innerHTML = renderPatchPreviewCard({
    title: "Workspace score preview",
    preview: synthesizedPreview,
    selectionStatus: previewStatus || "preview_only",
    selectionNote: synthesizedPreview
      ? ""
      : (previewNote || "Workspace score preview is not available yet."),
    explicitSelectedIds,
    emptyLabel: "Workspace score preview is not available yet.",
  });

  setTailoringSectionVisible("tailoringWorkspacePatchPreviewSummary", true);
}

function renderTailoringWorkspaceSavedSelectionSection(payload) {
  const root = qs("tailoringWorkspaceSavedSelectionShell");
  if (!root) return;

  if (String(tailoringWorkspaceState.selectedTab || "ready").trim() !== "ready") {
    clearTailoringWorkspaceSavedSelectionSection();
    return;
  }

  const selectedIds = normalizeTailoringWorkspaceCandidateIdList(
    payload && Array.isArray(payload.selected_patch_candidate_ids)
      ? payload.selected_patch_candidate_ids
      : []
  );
  const selectionStatus = String(payload?.selected_patch_selection_status || "").trim();
  const selectionNote = String(payload?.selected_patch_selection_note || "").trim();
  const preview = payload?.selected_patch_set_counterfactual_preview || null;

  if (!selectedIds.length || selectionStatus.toLowerCase() !== "applied") {
    clearTailoringWorkspaceSavedSelectionSection();
    return;
  }

  root.innerHTML = `
    <section class="tailoring-section-block">
      <div class="tailoring-section-title">Current saved selection</div>

      <div class="tailoring-card-topline">
        <div class="tailoring-chip-group">
          ${buildTailoringTonePill(humanizeUnderscoreLabel(selectionStatus || "applied"), selectionToneForStatus(selectionStatus || "applied"))}
          ${buildTailoringTonePill(`${selectedIds.length} selected`, "neutral")}
        </div>
      </div>

      ${selectionNote ? `
        <div class="tailoring-info-block">
          <div class="tailoring-info-label">Selection note</div>
          <div class="tailoring-card-copy">${escapeHtml(selectionNote)}</div>
        </div>
      ` : ""}

      <div class="tailoring-info-block">
        <div class="tailoring-info-label">Selected candidate IDs</div>
        ${renderPatchPreviewCandidateList(selectedIds, "No saved candidate selection.")}
      </div>
    </section>

    ${preview ? renderPatchPreviewCard({
      title: "Saved selection impact",
      preview,
      selectionStatus,
      selectionNote,
      explicitSelectedIds: selectedIds,
    }) : ""}
  `;

  const card = qs("tailoringWorkspaceSavedSelectionCard");
  if (card) {
    card.classList.remove("hidden");
  } else {
    setTailoringSectionVisible("tailoringWorkspaceSavedSelectionShell", true);
  }
}

function syncTailoringWorkspaceSavedSelectionIntoArtifact(payload) {
  const artifactPayload = getTailoringWorkspacePayload();
  if (!artifactPayload || !payload) return;

  artifactPayload.selected_patch_candidate_ids = normalizeTailoringWorkspaceCandidateIdList(
    payload.selected_patch_candidate_ids || []
  );
  artifactPayload.selected_patch_selection_status = payload.selected_patch_selection_status || "applied";
  artifactPayload.selected_patch_selection_note = payload.selected_patch_selection_note || "";
  artifactPayload.selected_patch_set_counterfactual_preview =
    payload.selected_patch_set_counterfactual_preview || null;
}

function getTailoringAnchorReviewCase(card) {
  const value = String(card?.review_case || "").trim().toLowerCase();
  return value || "preserve";
}

function getTailoringAnchorReviewLabel(card) {
  const backendLabel = String(card?.review_label || "").trim();
  if (backendLabel) return backendLabel;

  const reviewCase = getTailoringAnchorReviewCase(card);
  if (reviewCase === "fronting") return "Consider fronting";
  if (reviewCase === "support") return "Supporting context";
  return "Preserve evidence";
}

function getTailoringAnchorReviewTone(card) {
  const backendTone = String(card?.review_tone || "").trim().toLowerCase();
  if (backendTone) return backendTone;

  const reviewCase = getTailoringAnchorReviewCase(card);
  if (reviewCase === "fronting") return "caution";
  if (reviewCase === "support") return "neutral";
  return "muted";
}

function getTailoringAnchorReviewNote(card) {
  return String(card?.review_note || "").trim();
}

function getRenderableTailoringAnchorCards(items, limit = 3) {
  const rows = Array.isArray(items) ? items : [];
  return rows.slice(0, limit);
}

function getTailoringWorkspaceSuggestionBuckets() {
  const payload = getTailoringWorkspacePayload();

  const ready = [
    ...(Array.isArray(payload?.app_ready_replacements) ? payload.app_ready_replacements : []),
    ...(Array.isArray(payload?.direct_apply_optional_replacements)
      ? payload.direct_apply_optional_replacements
      : []),
  ];

  const reviewGuidance = Array.isArray(payload?.direction_only_replacements)
    ? payload.direction_only_replacements
    : [];

  const anchorCards = getRenderableTailoringAnchorCards(
    Array.isArray(payload?.anchor_cards) ? payload.anchor_cards : [],
    3
  );

  return {
    ready,
    review: [...reviewGuidance, ...anchorCards],
    reviewGuidance,
    anchorCards,
  };
}

function clearTailoringWorkspaceSelectedTabsSection() {
  const shell = qs("tailoringWorkspaceSelectedTabsShell");
  const readyTab = qs("tailoringWorkspaceSelectedReadyTab");
  const reviewTab = qs("tailoringWorkspaceSelectedReviewTab");
  const freeEditTab = qs("tailoringWorkspaceSelectedFreeEditTab");

  if (readyTab) {
    readyTab.classList.remove("active");
    readyTab.innerHTML = `<span class="tailoring-selected-tab-label">Ready</span><span class="tailoring-selected-tab-count">0</span>`;
  }

  if (reviewTab) {
    reviewTab.classList.remove("active");
    reviewTab.innerHTML = `<span class="tailoring-selected-tab-label">Review</span><span class="tailoring-selected-tab-count">0</span>`;
  }

  if (freeEditTab) {
    freeEditTab.classList.remove("active");
    freeEditTab.innerHTML = `<span class="tailoring-selected-tab-label">Free Edit</span><span class="tailoring-selected-tab-count">0</span>`;
  }

  if (shell) {
    shell.classList.add("hidden");
  }
}

function renderTailoringWorkspaceSelectedTabsSection() {
  const shell = qs("tailoringWorkspaceSelectedTabsShell");
  const readyTab = qs("tailoringWorkspaceSelectedReadyTab");
  const reviewTab = qs("tailoringWorkspaceSelectedReviewTab");
  const freeEditTab = qs("tailoringWorkspaceSelectedFreeEditTab");

  if (!shell || !readyTab || !reviewTab || !freeEditTab) return;

  const payload = getTailoringWorkspacePayload();
  const grouped = getTailoringWorkspaceSuggestionBuckets();
  const readyItems = grouped.ready;
  const reviewItems = grouped.review;
  const freeEditRows = payload ? buildTailoringWorkspaceEditableBulletRows(payload) : [];

  if (!readyItems.length && !reviewItems.length && !freeEditRows.length) {
    clearTailoringWorkspaceSelectedTabsSection();
    return;
  }

  if (!["ready", "review", "free_edit"].includes(tailoringWorkspaceState.selectedTab)) {
    tailoringWorkspaceState.selectedTab = reviewItems.length ? "review" : freeEditRows.length ? "free_edit" : "ready";
  }

  readyTab.classList.toggle("active", tailoringWorkspaceState.selectedTab === "ready");
  reviewTab.classList.toggle("active", tailoringWorkspaceState.selectedTab === "review");
  freeEditTab.classList.toggle("active", tailoringWorkspaceState.selectedTab === "free_edit");

  readyTab.innerHTML = `<span class="tailoring-selected-tab-label">Ready</span><span class="tailoring-selected-tab-count">${readyItems.length}</span>`;
  reviewTab.innerHTML = `<span class="tailoring-selected-tab-label">Review</span><span class="tailoring-selected-tab-count">${reviewItems.length}</span>`;
  freeEditTab.innerHTML = `<span class="tailoring-selected-tab-label">Free Edit</span><span class="tailoring-selected-tab-count">${freeEditRows.length}</span>`;

  readyTab.title = `${readyItems.length} score-ready replacement${readyItems.length === 1 ? "" : "s"}`;
  reviewTab.title = `${reviewItems.length} review guidance item${reviewItems.length === 1 ? "" : "s"}`;
  freeEditTab.title = `${freeEditRows.length} editable bullet${freeEditRows.length === 1 ? "" : "s"}`;

  shell.classList.remove("hidden");
}

function refreshTailoringWorkspaceSelectionPanels() {
  renderTailoringWorkspaceSelectedTabsSection();

  clearTailoringWorkspacePatchPreviewSection();

  if (tailoringWorkspaceState.savedSelectionPayload) {
    renderTailoringWorkspaceSavedSelectionSection(tailoringWorkspaceState.savedSelectionPayload);
  } else {
    clearTailoringWorkspaceSavedSelectionSection();
  }

  refreshTailoringWorkspaceInlineScoreControls();
  updateTailoringWorkspaceSelectionActionBar();
}

function updateTailoringWorkspaceMetaSummary(payload) {
  const meta = qs("tailoringWorkspaceMeta");
  if (!meta) return;

  if (!payload || typeof payload !== "object") {
    meta.textContent = "Suggested changes are not available for this row.";
    renderTailoringWorkspaceReviewTelemetryStrip();
    return;
  }

  const grouped = getTailoringWorkspaceSuggestionBuckets();

  const appReady = Array.isArray(payload.app_ready_replacements) ? payload.app_ready_replacements : [];
  const directApplyOptional = Array.isArray(payload.direct_apply_optional_replacements)
    ? payload.direct_apply_optional_replacements
    : [];
  const directionOnly = grouped.reviewGuidance;
  const anchorCards = grouped.anchorCards;

  const actionableCount = appReady.length + directApplyOptional.length;
  const reviewCount = directionOnly.length;
  const anchorCount = anchorCards.length;
  const editableCount = buildTailoringWorkspaceEditableBulletRows(payload).length;
  const selectedCount = getTailoringWorkspaceSelectedCandidateIds().length;
  const activeTab = String(tailoringWorkspaceState.selectedTab || "").trim();

  if (activeTab === "free_edit") {
    const freeEditRows = getTailoringWorkspaceFilteredFreeEditRows(payload);
    const filterKey = String(tailoringWorkspaceState.reviewTelemetryFilter || "").trim();

    meta.textContent = filterKey === "manual_edits"
      ? freeEditRows.length
        ? `Showing ${freeEditRows.length} manually edited bullet${freeEditRows.length === 1 ? "" : "s"}. Save stores manual edits in the workspace draft.`
        : "No manually edited bullets are available yet."
      : editableCount
        ? `${editableCount} surfaced bullet${editableCount === 1 ? "" : "s"} loaded for free editing. Save stores manual edits in the workspace draft.`
        : "No surfaced bullets are available for free editing on this row yet.";

    renderTailoringWorkspaceReviewTelemetryStrip();
    return;
  }

  if (activeTab === "review") {
    const reviewItems = getTailoringWorkspaceFilteredReviewItems(directionOnly);
    const filterKey = String(tailoringWorkspaceState.reviewTelemetryFilter || "").trim();

    if (filterKey === "remaining") {
      meta.textContent = reviewItems.length
        ? `Showing ${reviewItems.length} remaining review suggestion${reviewItems.length === 1 ? "" : "s"}.`
        : "No remaining review suggestions match the current filter.";
    } else if (filterKey === "accepted_as_is") {
      meta.textContent = reviewItems.length
        ? `Showing ${reviewItems.length} accepted-as-is review suggestion${reviewItems.length === 1 ? "" : "s"}.`
        : "No accepted-as-is review suggestions match the current filter.";
    } else if (filterKey === "edited_after_accept") {
      meta.textContent = reviewItems.length
        ? `Showing ${reviewItems.length} edited-after-accept review suggestion${reviewItems.length === 1 ? "" : "s"}.`
        : "No edited-after-accept review suggestions match the current filter.";
    } else if (filterKey === "rejected") {
      meta.textContent = reviewItems.length
        ? `Showing ${reviewItems.length} rejected review suggestion${reviewItems.length === 1 ? "" : "s"}.`
        : "No rejected review suggestions match the current filter.";
    } else if (reviewCount > 0 && anchorCount > 0) {
      meta.textContent = `Review guidance loaded. ${reviewCount} review suggestion${reviewCount === 1 ? "" : "s"} and ${anchorCount} grounded anchor${anchorCount === 1 ? "" : "s"} available.`;
    } else if (reviewCount > 0) {
      meta.textContent = "Review guidance loaded. This row has review-only suggestions, but no safe selectable rewrites yet.";
    } else if (anchorCount > 0) {
      meta.textContent = `Anchor evidence loaded. ${anchorCount} grounded anchor${anchorCount === 1 ? "" : "s"} found. Review tab shows strong bullets worth keeping visible.`;
    } else {
      meta.textContent = "No review guidance is available for this row.";
    }

    renderTailoringWorkspaceReviewTelemetryStrip();
    return;
  }

  if (actionableCount > 0) {
    if (selectedCount > 0) {
      meta.textContent = `${selectedCount} of ${actionableCount} actionable suggestion${actionableCount === 1 ? "" : "s"} selected. Review evidence stays read-only.`;
    } else {
      meta.textContent = `Actionable suggestions loaded. ${actionableCount} selectable suggestion${actionableCount === 1 ? "" : "s"} available. Review evidence stays read-only.`;
    }
    renderTailoringWorkspaceReviewTelemetryStrip();
    return;
  }

  if (reviewCount > 0 || anchorCount > 0) {
    meta.textContent = anchorCount > 0 && reviewCount === 0
      ? `Anchor evidence loaded. ${anchorCount} grounded anchor${anchorCount === 1 ? "" : "s"} found, but no safe selectable rewrites yet.`
      : "Review guidance loaded. This row has review-only suggestions, but no safe selectable rewrites yet.";
    renderTailoringWorkspaceReviewTelemetryStrip();
    return;
  }

  meta.textContent = "No safe bullet-level rewrites or grounded anchor evidence were found for this row.";
  renderTailoringWorkspaceReviewTelemetryStrip();
}

function updateTailoringWorkspaceHeroStatus(payload) {
  const statusNode =
    qs("tailoringWorkspaceStatusValue") ||
    Array.from(document.querySelectorAll(".tailoring-workspace-hero .info-pair"))
      .find((node) => String(node.querySelector(".label")?.textContent || "").trim().toLowerCase() === "status")
      ?.querySelector("span:last-child");
  if (!statusNode) return;

  if (!payload || typeof payload !== "object") {
    const page = document.querySelector(".tailoring-workspace-page");
    const routeStatus = String(page?.dataset?.tailoringStatus || "").trim();
    statusNode.textContent = routeStatus || "Unavailable";
    return;
  }

  const grouped = getTailoringWorkspaceSuggestionBuckets();
  const readyCount = grouped.ready.length;
  const reviewCount = grouped.review.length;
  const freeEditCount = buildTailoringWorkspaceEditableBulletRows(payload).length;

  if (readyCount > 0) {
    statusNode.textContent = "Ready suggestions";
  } else if (reviewCount > 0) {
    statusNode.textContent = "Review guidance";
  } else if (freeEditCount > 0) {
    statusNode.textContent = "Free edit available";
  } else {
    statusNode.textContent = "No safe rewrites yet";
  }
}

function renderTailoringWorkspaceSimpleSuggestionFallback(payload, error = null) {
  const root = qs("tailoringWorkspaceInteractiveSummary");
  if (!root) return;

  const activeTab = String(tailoringWorkspaceState.selectedTab || "ready").trim();
  const grouped = getTailoringWorkspaceSuggestionBuckets();
  const selectedSet = new Set(getTailoringWorkspaceSelectedCandidateIds());

  const items =
    activeTab === "review"
      ? grouped.reviewGuidance
      : activeTab === "free_edit"
        ? []
        : grouped.ready;

  if (activeTab === "free_edit") {
    try {
      root.innerHTML = renderTailoringWorkspaceFreeEditSection(payload);
      return;
    } catch (freeEditErr) {
      console.error("Failed to render free edit fallback", freeEditErr);
    }
  }

  const rows = Array.isArray(items) ? items : [];
  const title =
    activeTab === "review"
      ? "Review guidance"
      : "Ready suggestions";

  const body = rows.length
    ? rows.map((item, index) => {
        const candidateId = getTailoringReplacementCandidateId(item);
        const originalText = String(
          item?.current_evidence ||
          item?.original_text ||
          item?.parent_bullet ||
          ""
        ).trim();
        const suggestionText = String(
          item?.final_replacement_text ||
          item?.rewrite_direction ||
          item?.why_selected ||
          item?.materiality_reason ||
          ""
        ).trim();
        const isSelected = Boolean(candidateId && selectedSet.has(candidateId));
        const canSelect = activeTab !== "review" && Boolean(candidateId);

        return `
          <article
            class="tailoring-edit-card tailoring-edit-card--compact ${candidateId ? "tailoring-edit-card--clickable" : ""} ${isSelected ? "tailoring-edit-card--selected" : ""}"
            ${candidateId ? `data-tailoring-focus-candidate="${escapeHtml(candidateId)}"` : ""}
          >
            <div class="tailoring-card-topline tailoring-card-topline--compact">
              <div class="tailoring-edit-card-label">${escapeHtml(title)} ${index + 1}</div>
              <div class="tailoring-chip-group tailoring-chip-group--compact">
                ${buildTailoringTonePill(activeTab === "review" ? "Review" : "Ready", activeTab === "review" ? "caution" : "safe")}
                ${isSelected ? buildTailoringTonePill("Selected", "safe") : ""}
              </div>
            </div>
            ${originalText ? `
              <div class="tailoring-info-block tailoring-info-block--compact">
                <div class="tailoring-info-label">Current bullet</div>
                <div class="tailoring-quote-block">${escapeHtml(originalText)}</div>
              </div>
            ` : ""}
            ${suggestionText ? `
              <div class="tailoring-info-block tailoring-info-block--compact">
                <div class="tailoring-info-label">${activeTab === "review" ? "Guidance" : "Suggested edit"}</div>
                <div class="tailoring-rewrite-callout">${escapeHtml(suggestionText)}</div>
              </div>
            ` : ""}
            ${canSelect ? `
              <div class="tailoring-card-actions tailoring-card-actions--compact">
                <button
                  type="button"
                  class="ghost-btn btn-sm tailoring-select-btn ${isSelected ? "is-selected" : ""}"
                  data-tailoring-select-candidate="${escapeHtml(candidateId)}"
                >
                  ${isSelected ? "Remove" : "Add"}
                </button>
              </div>
            ` : ""}
          </article>
        `;
      }).join("")
    : `<div class="tailoring-empty-inline">No ${escapeHtml(title.toLowerCase())} available for this tab.</div>`;

  root.innerHTML = `
    <section class="tailoring-section-block">
      <div class="tailoring-section-title">${escapeHtml(title)}</div>
      <div class="tailoring-card-copy">
        Loaded using the simplified suggestion renderer.
      </div>
      ${error ? `
        <div class="tailoring-card-copy">
          Advanced renderer fallback: ${escapeHtml(error.message || String(error))}
        </div>
      ` : ""}
      <div class="tailoring-edit-card-list">
        ${body}
      </div>
    </section>
  `;
}

function rerenderTailoringWorkspaceSelectionView() {
  if (!tailoringWorkspaceState.artifact) return;

  const payload = getTailoringWorkspacePayload();
  renderTailoringWorkspaceSelectedTabsSection();

  try {
    if (tailoringWorkspaceState.selectedTab === "free_edit") {
      qs("tailoringWorkspaceInteractiveSummary").innerHTML = renderTailoringWorkspaceFreeEditSection(payload);
    } else {
      const reviewFilterKey = String(tailoringWorkspaceState.reviewTelemetryFilter || "").trim();

      const reviewFilteredPayload =
        tailoringWorkspaceState.selectedTab === "review" && payload
          ? {
              ...payload,
              direction_only_replacements: getTailoringWorkspaceFilteredReviewItems(
                payload.direction_only_replacements
              ),
              anchor_cards:
                reviewFilterKey && reviewFilterKey !== "selected" && reviewFilterKey !== "manual_edits"
                  ? []
                  : Array.isArray(payload.anchor_cards)
                    ? payload.anchor_cards
                    : [],
            }
          : payload;

      const artifactForRender =
        reviewFilteredPayload && reviewFilteredPayload !== payload
          ? {
              ...tailoringWorkspaceState.artifact,
              data: reviewFilteredPayload,
            }
          : tailoringWorkspaceState.artifact;

      renderTailoringInteractiveSummaryInto(
        "tailoringWorkspaceInteractiveSummary",
        artifactForRender,
        {
          includeDiagnostics: false,
          selectionEnabled: true,
          selectedCandidateIds: getTailoringWorkspaceSelectedCandidateIds(),
          bucketFilter: tailoringWorkspaceState.selectedTab,
        }
      );
    }
  } catch (renderErr) {
    console.error("Failed to render advanced tailoring suggestions", renderErr);
    renderTailoringWorkspaceSimpleSuggestionFallback(payload, renderErr);
  }

  scheduleTailoringWorkspaceDocumentPreview();
  updateTailoringWorkspaceMetaSummary(payload);
  refreshTailoringWorkspaceSelectionPanels();
}

function initializeTailoringWorkspaceSelectionState(artifact, draftResponse = null) {
  tailoringWorkspaceState.artifact = artifact;
  tailoringWorkspaceState.previewPayload = null;
  tailoringWorkspaceState.activeInlineScoreKey = "";
  tailoringWorkspaceState.activeReviewEditCandidateId = "";
  tailoringWorkspaceState.previewMode = "pdf";
  tailoringWorkspaceState.documentPreviewPayload = null;
  tailoringWorkspaceState.documentPreviewRequestSeq = 0;
  tailoringWorkspaceState.isDocumentPreviewLoading = false;
  tailoringWorkspaceState.focusedBulletKey = "";

  if (tailoringWorkspaceState.documentPreviewTimer) {
    window.clearTimeout(tailoringWorkspaceState.documentPreviewTimer);
    tailoringWorkspaceState.documentPreviewTimer = null;
  }

  const payload =
    artifact && artifact.kind === "json" && artifact.data && typeof artifact.data === "object"
      ? artifact.data
      : null;

  const loadedDraft =
    draftResponse && draftResponse.draft && typeof draftResponse.draft === "object"
      ? draftResponse.draft
      : null;

  tailoringWorkspaceState.draftPayload = loadedDraft;
  tailoringWorkspaceState.manualBulletEdits =
    loadedDraft && loadedDraft.manual_bullet_edits && typeof loadedDraft.manual_bullet_edits === "object"
      ? { ...loadedDraft.manual_bullet_edits }
      : {};
  tailoringWorkspaceState.rewriteReviewDecisions =
    loadedDraft && loadedDraft.rewrite_review_decisions && typeof loadedDraft.rewrite_review_decisions === "object"
      ? normalizeTailoringWorkspaceReviewDecisionMap(loadedDraft.rewrite_review_decisions)
      : {};

  if (!payload) {
    tailoringWorkspaceState.selectedCandidateIds = [];
    tailoringWorkspaceState.candidateLookup = new Map();
    tailoringWorkspaceState.savedSelectionPayload = null;
    return;
  }

  tailoringWorkspaceState.candidateLookup = buildTailoringWorkspaceCandidateLookup(payload);

  const artifactSavedSelection = buildTailoringWorkspaceSavedSelectionPayloadFromArtifact(payload);
  const draftSavedSelection =
    draftResponse && draftResponse.has_saved_draft
      ? buildTailoringWorkspaceSavedSelectionPayloadFromDraft(loadedDraft)
      : null;

  const artifactSelectedIds = normalizeTailoringWorkspaceCandidateIdList(
    String(payload.selected_patch_selection_status || "").trim().toLowerCase() === "applied"
      ? (Array.isArray(payload.selected_patch_candidate_ids) ? payload.selected_patch_candidate_ids : [])
      : []
  );

  const draftSelectedIds = loadedDraft
    ? normalizeTailoringWorkspaceCandidateIdList(loadedDraft.selected_patch_candidate_ids || [])
    : [];

  const draftManualEditCount =
    loadedDraft && loadedDraft.manual_bullet_edits && typeof loadedDraft.manual_bullet_edits === "object"
      ? Object.keys(normalizeTailoringWorkspaceManualBulletEdits(loadedDraft.manual_bullet_edits)).length
      : 0;

  const draftReviewDecisionCount =
    loadedDraft && loadedDraft.rewrite_review_decisions && typeof loadedDraft.rewrite_review_decisions === "object"
      ? Object.keys(normalizeTailoringWorkspaceReviewDecisionMap(loadedDraft.rewrite_review_decisions)).length
      : 0;

  const hasDraftSelectionDelta =
    draftSelectedIds.join("|") !== artifactSelectedIds.join("|");

  const shouldPreferDraftState = Boolean(
    draftResponse &&
    draftResponse.has_saved_draft &&
    (
      hasDraftSelectionDelta ||
      draftManualEditCount > 0 ||
      draftReviewDecisionCount > 0
    )
  );

  tailoringWorkspaceState.savedSelectionPayload =
    shouldPreferDraftState && draftSavedSelection
      ? draftSavedSelection
      : artifactSavedSelection;

  tailoringWorkspaceState.selectedCandidateIds = normalizeTailoringWorkspaceSelectedCandidateIds(
    payload,
    shouldPreferDraftState ? draftSelectedIds : artifactSelectedIds
  );
}

function toggleTailoringWorkspaceCandidateSelection(candidateId) {
  const payload = getTailoringWorkspacePayload();
  const safeCandidateId = String(candidateId || "").trim();

  if (!payload || !safeCandidateId) return;

  const current = new Set(getTailoringWorkspaceSelectedCandidateIds());

  if (current.has(safeCandidateId)) {
    current.delete(safeCandidateId);
  } else {
    current.add(safeCandidateId);
  }

  tailoringWorkspaceState.selectedCandidateIds = normalizeTailoringWorkspaceSelectedCandidateIds(
    payload,
    Array.from(current)
  );

  tailoringWorkspaceState.previewPayload = null;

  rerenderTailoringWorkspaceSelectionView();
  syncTailoringWorkspacePreviewHighlight();
}

function scrollTailoringWorkspaceLeftPaneToTabs() {
  // Keep the context header visible while switching between Ready/Review/Free Edit.
}

function bindTailoringWorkspaceSelectionHandlers() {
  const root = qs("tailoringWorkspaceInteractiveSummary");
  if (root && root.dataset.selectionBound !== "true") {
    root.dataset.selectionBound = "true";

    root.addEventListener("click", async (event) => {
      const reviewActionButton = event.target.closest("[data-tailoring-review-action]");
      if (reviewActionButton) {
        event.preventDefault();
        const candidateId = String(reviewActionButton.dataset.tailoringReviewCandidate || "").trim();
        const nextState = String(reviewActionButton.dataset.tailoringReviewAction || "").trim().toLowerCase();
        if (!candidateId || !nextState) return;
        setTailoringWorkspaceReviewDecision(candidateId, nextState);
        return;
      }

      const reviewEditButton = event.target.closest("[data-tailoring-review-edit]");
      if (reviewEditButton) {
        event.preventDefault();
        const candidateId = String(reviewEditButton.dataset.tailoringReviewEdit || "").trim();
        if (!candidateId) return;
        await openTailoringWorkspaceManualEditForCandidate(candidateId);
        return;
      }

      const selectButton = event.target.closest("[data-tailoring-select-candidate]");
      if (selectButton) {
        event.preventDefault();
        const candidateId = selectButton.dataset.tailoringSelectCandidate || "";
        toggleTailoringWorkspaceCandidateSelection(candidateId);
        focusTailoringWorkspaceCandidateInPreview(candidateId);
        return;
      }

      const actionButton = event.target.closest("[data-tailoring-free-edit-action]");
      if (actionButton) {
        event.preventDefault();

        const bulletKey = String(actionButton.dataset.tailoringFreeEditAction || "").trim();
        if (!bulletKey) return;
        focusTailoringWorkspaceBulletKeyInPreview(bulletKey);

        const payload = getTailoringWorkspacePayload();
        const manualEdits = normalizeTailoringWorkspaceManualBulletEdits(
          tailoringWorkspaceState.manualBulletEdits || {},
          payload
        );
        const hasEdit = Object.prototype.hasOwnProperty.call(manualEdits, bulletKey);
        if (!hasEdit) return;

        const isSaveStep =
          String(tailoringWorkspaceState.previewReadyKey || "").trim() === bulletKey;

        tailoringWorkspaceState.activeInlineScoreKey = bulletKey;

        if (isSaveStep) {
          await saveTailoringWorkspaceSelection();
        } else {
          await previewTailoringWorkspaceSelection({ targetKey: bulletKey });
        }
        return;
      }

      const focusBulletCard = event.target.closest("[data-tailoring-focus-bullet-key]");
      if (
        focusBulletCard &&
        !event.target.closest("[data-tailoring-free-edit-key]") &&
        !event.target.closest("[data-tailoring-free-edit-action]")
      ) {
        event.preventDefault();
        focusTailoringWorkspaceBulletKeyInPreview(
          focusBulletCard.dataset.tailoringFocusBulletKey || ""
        );
        return;
      }

      const focusCard = event.target.closest("[data-tailoring-focus-candidate]");
      if (!focusCard) return;

      event.preventDefault();
      focusTailoringWorkspaceCandidateInPreview(
        focusCard.dataset.tailoringFocusCandidate || ""
      );
    });

    root.addEventListener("input", (event) => {
      const textarea = event.target.closest("[data-tailoring-free-edit-key]");
      if (!textarea) return;

      const bulletKey = String(textarea.dataset.tailoringFreeEditKey || "").trim();
      if (!bulletKey) return;

      focusTailoringWorkspaceBulletKeyInPreview(bulletKey);
      tailoringWorkspaceState.manualBulletEdits[bulletKey] = textarea.value;
      tailoringWorkspaceState.previewPayload = null;
      tailoringWorkspaceState.previewReadyKey = "";
      tailoringWorkspaceState.activeInlineScoreKey = bulletKey;

      syncTailoringWorkspaceReviewDecisionFromTextarea(bulletKey);
      scheduleTailoringWorkspaceDocumentPreview();
      updateTailoringWorkspaceMetaSummary(getTailoringWorkspacePayload());
      refreshTailoringWorkspaceInlineScoreControls();
      updateTailoringWorkspaceSelectionActionBar();
    });

    root.addEventListener("focusin", (event) => {
      const textarea = event.target.closest("[data-tailoring-free-edit-key]");
      if (!textarea) return;

      const bulletKey = String(textarea.dataset.tailoringFreeEditKey || "").trim();
      if (!bulletKey) return;

      focusTailoringWorkspaceBulletKeyInPreview(bulletKey);
    });
  }

  const tabRow = qs("tailoringWorkspaceSelectedTabRow");
  if (tabRow && tabRow.dataset.bound !== "true") {
    tabRow.dataset.bound = "true";

    tabRow.addEventListener("click", (event) => {
      const tabButton = event.target.closest("[data-tailoring-selected-tab]");
      if (!tabButton) return;

      const nextTab = String(tabButton.dataset.tailoringSelectedTab || "").trim();
      if (!nextTab || nextTab === tailoringWorkspaceState.selectedTab) return;

      tailoringWorkspaceState.selectedTab = nextTab;
      tailoringWorkspaceState.reviewTelemetryFilter = "";
      rerenderTailoringWorkspaceSelectionView();
      scrollTailoringWorkspaceLeftPaneToTabs();
    });
  }
}

function getTailoringWorkspaceExportModal() {
  return qs("tailoringWorkspaceExportModal");
}

function closeTailoringWorkspaceExportModal() {
  const modal = getTailoringWorkspaceExportModal();
  if (!modal) return;
  modal.classList.add("hidden");
}

function getTailoringWorkspaceExportState() {
  const context = getTailoringWorkspaceContext();
  const payload = getTailoringWorkspacePayload();

  const resumeName = context ? String(context.resumeName || "").trim() : "";
  const hasResume = Boolean(resumeName);

  const selectedIds = getTailoringWorkspaceSelectedCandidateIds();
  const savedIds = getTailoringWorkspaceSavedCandidateIds();
  const hasSelection = selectedIds.length > 0;
  const matchesSavedSelection = haveSameTailoringWorkspaceCandidateIds(selectedIds, savedIds);
  const hasSavedSelection = savedIds.length > 0;

  const currentManualEdits = normalizeTailoringWorkspaceManualBulletEdits(
    tailoringWorkspaceState.manualBulletEdits || {},
    payload
  );
  const savedManualEdits = normalizeTailoringWorkspaceManualBulletEdits(
    getTailoringWorkspaceSavedManualBulletEdits(),
    payload
  );
  const manualMatchesSaved = haveSameTailoringWorkspaceManualBulletEdits(
    currentManualEdits,
    savedManualEdits,
    payload
  );

  const currentReviewDecisions = getTailoringWorkspaceCurrentReviewDecisionMap();
  const savedReviewDecisions = getTailoringWorkspaceSavedReviewDecisionMap();
  const reviewMatchesSaved =
    JSON.stringify(currentReviewDecisions) === JSON.stringify(savedReviewDecisions);

  const hasManualEdits = Object.keys(currentManualEdits).length > 0;
  const hasSavedManualEdits = Object.keys(savedManualEdits).length > 0;
  const hasSavedReviewDecisions = Object.keys(savedReviewDecisions).length > 0;

  const hasAnySavedState =
    hasSavedSelection || hasSavedManualEdits || hasSavedReviewDecisions;

  const hasUnsavedSelectionChange =
    hasSavedSelection ? !matchesSavedSelection : hasSelection;

  const hasUnsavedManualChange =
    hasSavedManualEdits ? !manualMatchesSaved : hasManualEdits;

  const hasUnsavedReviewChange =
    hasSavedReviewDecisions
      ? !reviewMatchesSaved
      : Object.keys(currentReviewDecisions).length > 0;

  const hasUnsavedWorkspaceChanges =
    hasUnsavedSelectionChange || hasUnsavedManualChange || hasUnsavedReviewChange;

  const canExport =
    hasResume &&
    hasAnySavedState &&
    !hasUnsavedWorkspaceChanges &&
    !tailoringWorkspaceState.isSaving &&
    !tailoringWorkspaceState.isPreviewing;

  let statusLabel = "Unavailable";
  let hint = "A resume is required before export can be offered.";
  let tooltip = "Export unavailable";

  if (!hasResume) {
    statusLabel = "No resume loaded";
    hint = "A resume must be loaded for this workspace row before export is possible.";
    tooltip = "Export unavailable";
  } else if (!hasAnySavedState) {
    statusLabel = "Not saved yet";
    hint = "Save at least one selected suggestion, manual edit, or review decision to enable export.";
    tooltip = "Save draft to export";
  } else if (hasUnsavedWorkspaceChanges) {
    statusLabel = "Unsaved changes";
    hint = "Save the current workspace draft before exporting so the file matches the saved state.";
    tooltip = "Save changes to export";
  } else if (tailoringWorkspaceState.isSaving) {
    statusLabel = "Saving in progress";
    hint = "Wait for the current save to finish before exporting.";
    tooltip = "Saving changes...";
  } else if (tailoringWorkspaceState.isPreviewing) {
    statusLabel = "Preview in progress";
    hint = "Wait for preview scoring to finish before exporting.";
    tooltip = "Preview in progress";
  } else {
    statusLabel = "Ready to export";
    hint = "Choose the format for the saved tailored draft.";
    tooltip = "Export tailored draft";
  }

  return {
    resumeName,
    hasResume,
    hasAnySavedState,
    hasUnsavedWorkspaceChanges,
    canExport,
    statusLabel,
    hint,
    tooltip,
  };
}

function openTailoringWorkspaceExportModal() {
  const modal = getTailoringWorkspaceExportModal();
  const resumeEl = qs("tailoringWorkspaceExportResume");
  const statusEl = qs("tailoringWorkspaceExportStatus");
  const hintEl = qs("tailoringWorkspaceExportHint");
  const pdfBtn = qs("tailoringWorkspaceExportPdfBtn");
  const wordBtn = qs("tailoringWorkspaceExportWordBtn");

  if (!modal || !resumeEl || !statusEl || !hintEl || !pdfBtn || !wordBtn) return;

  const exportState = getTailoringWorkspaceExportState();

  resumeEl.textContent = exportState.resumeName
    ? humanizeResumeDisplayName(exportState.resumeName)
    : "No resume loaded";

  statusEl.textContent = exportState.statusLabel;
  hintEl.textContent = exportState.hint;

  pdfBtn.disabled = !exportState.canExport;
  wordBtn.disabled = !exportState.canExport;

  modal.classList.remove("hidden");
}

async function handleTailoringWorkspaceExportSelection(format) {
  const exportState = getTailoringWorkspaceExportState();
  const context = getTailoringWorkspaceContext();
  const normalizedFormat = String(format || "").trim().toLowerCase();

  if (!exportState.canExport) {
    showAppError("Export unavailable", new Error(exportState.hint));
    return;
  }

  if (!context || !getTailoringWorkspaceSuggestionArtifactKey(context) || !getTailoringWorkspaceResumePreviewName(context)) {
    showAppError("Export unavailable", new Error("Missing tailoring workspace context."));
    return;
  }

  try {
    const response = await fetch(buildPlanningEndpoint(
      "/planning/export-workspace-draft",
      context.planningOutputDir
    ), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        tailoring_json_path: getTailoringWorkspaceSuggestionArtifactKey(context),
        selected_resume: getTailoringWorkspaceResumePreviewName(context),
        format: normalizedFormat,
      }),
    });

    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}: Failed to export tailored draft.`;

      try {
        const payload = await response.json();
        if (payload && typeof payload.detail === "string" && payload.detail.trim()) {
          errorMessage = payload.detail.trim();
        }
      } catch {
        try {
          const rawText = await response.text();
          if (rawText && rawText.trim()) {
            errorMessage = rawText.trim();
          }
        } catch {
          // ignore secondary parse failure
        }
      }

      throw new Error(errorMessage);
    }

    const blob = await response.blob();
    const objectUrl = URL.createObjectURL(blob);

    const disposition = response.headers.get("Content-Disposition") || "";
    const filenameMatch =
      disposition.match(/filename\*=UTF-8''([^;]+)/i) ||
      disposition.match(/filename="([^"]+)"/i) ||
      disposition.match(/filename=([^;]+)/i);

    const fallbackFilename =
      normalizedFormat === "word"
        ? "tailored_draft.docx"
        : "tailored_draft.pdf";

    const filename = filenameMatch
      ? decodeURIComponent(String(filenameMatch[1] || "").trim().replace(/^["']|["']$/g, ""))
      : fallbackFilename;

    const link = document.createElement("a");
    link.href = objectUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(objectUrl);
    
    const exportStatus = String(
      response.headers.get("X-Tailoring-Export-Status") || "complete"
    ).trim().toLowerCase();

    const unresolvedCandidateCount = Number(
      response.headers.get("X-Tailoring-Export-Unresolved-Candidate-Count") || 0
    );

    const unresolvedManualKeyCount = Number(
      response.headers.get("X-Tailoring-Export-Unresolved-Manual-Key-Count") || 0
    );

    const warningMessage = String(
      response.headers.get("X-Tailoring-Export-Warning-Message") || ""
    ).trim();

    const statusEl = qs("tailoringWorkspaceExportStatus");
    const hintEl = qs("tailoringWorkspaceExportHint");

    if (
      exportStatus === "partial" &&
      (unresolvedCandidateCount > 0 || unresolvedManualKeyCount > 0)
    ) {
      if (statusEl) {
        statusEl.textContent = "Exported with warnings";
      }

      if (hintEl) {
        hintEl.textContent =
          warningMessage ||
          "The file downloaded, but some edits could not be mapped exactly into the exported document.";
      }

      return;
    }

    closeTailoringWorkspaceExportModal();

    closeTailoringWorkspaceExportModal();
  } catch (err) {
    showAppError("Failed to export tailored draft", err);
  }
}

function bindTailoringWorkspaceExportModal() {
  const modal = getTailoringWorkspaceExportModal();
  const closeBtn = qs("closeTailoringWorkspaceExportModalBtn");
  const pdfBtn = qs("tailoringWorkspaceExportPdfBtn");
  const wordBtn = qs("tailoringWorkspaceExportWordBtn");

  if (!modal || !closeBtn || !pdfBtn || !wordBtn) return;
  if (modal.dataset.bound === "true") return;

  modal.dataset.bound = "true";

  closeBtn.addEventListener("click", closeTailoringWorkspaceExportModal);

  pdfBtn.addEventListener("click", async () => {
    await handleTailoringWorkspaceExportSelection("pdf");
  });

  wordBtn.addEventListener("click", async () => {
    await handleTailoringWorkspaceExportSelection("word");
  });

  modal.addEventListener("click", (event) => {
    if (event.target === modal) {
      closeTailoringWorkspaceExportModal();
    }
  });
}

async function previewTailoringWorkspaceSelection({ targetKey = "" } = {}) {
  const context = getTailoringWorkspaceContext();
  const selectedIds = getTailoringWorkspaceSelectedCandidateIds();
  const payload = getTailoringWorkspacePayload();

  const manualEdits = normalizeTailoringWorkspaceManualBulletEdits(
    tailoringWorkspaceState.manualBulletEdits || {},
    payload
  );
  const reviewDecisions = getTailoringWorkspaceCurrentReviewDecisionMap();
  const hasManualEdits = Object.keys(manualEdits).length > 0;

  if (!context || !getTailoringWorkspaceSuggestionArtifactKey(context)) return;
  if (!selectedIds.length && !hasManualEdits) return;

  tailoringWorkspaceState.activeInlineScoreKey = String(
    targetKey || tailoringWorkspaceState.activeInlineScoreKey || ""
  ).trim();
  tailoringWorkspaceState.previewReadyKey = "";
  tailoringWorkspaceState.isPreviewing = true;
  refreshTailoringWorkspaceInlineScoreControls();
  updateTailoringWorkspaceSelectionActionBar();

  try {
    const response = await postJson(buildPlanningEndpoint("/planning/preview-workspace-draft", context.planningOutputDir), {
      tailoring_json_path: getTailoringWorkspaceSuggestionArtifactKey(context),
      selected_resume: getTailoringWorkspaceResumePreviewName(context),
      selected_patch_candidate_ids: selectedIds,
      manual_bullet_edits: manualEdits,
      rewrite_review_decisions: reviewDecisions,
    });

    tailoringWorkspaceState.previewPayload = {
      preview_status: String(response.preview_status || "").trim(),
      preview_note: String(response.preview_note || "").trim(),
      selected_patch_candidate_ids: Array.isArray(response.selected_patch_candidate_ids)
        ? response.selected_patch_candidate_ids
        : selectedIds,
      manual_bullet_edits:
        response && response.manual_bullet_edits && typeof response.manual_bullet_edits === "object"
          ? response.manual_bullet_edits
          : manualEdits,
      manual_edit_count: Number(response.manual_edit_count || 0),
      manual_edit_rescore_supported: Boolean(response.manual_edit_rescore_supported),
      needs_full_draft_rescore: Boolean(response.needs_full_draft_rescore),
      original_score: response.original_score,
      projected_score: response.projected_score,
      projected_delta: response.projected_delta,
      selected_patch_set_counterfactual_preview: response.selected_patch_set_counterfactual_preview || null,
      rewrite_review_decisions:
        response && response.rewrite_review_decisions && typeof response.rewrite_review_decisions === "object"
          ? response.rewrite_review_decisions
          : reviewDecisions,
      rewrite_review_telemetry: response.rewrite_review_telemetry || null,
    };

    tailoringWorkspaceState.previewReadyKey = String(
      targetKey || tailoringWorkspaceState.activeInlineScoreKey || ""
    ).trim();
    refreshTailoringWorkspaceInlineScoreControls();
    refreshTailoringWorkspaceSelectionPanels();
  } catch (err) {
    showAppError("Failed to preview workspace draft", err);
  } finally {
    tailoringWorkspaceState.isPreviewing = false;
    refreshTailoringWorkspaceInlineScoreControls();
    updateTailoringWorkspaceSelectionActionBar();
  }
}

async function saveTailoringWorkspaceSelection() {
  const context = getTailoringWorkspaceContext();
  const selectedIds = getTailoringWorkspaceSelectedCandidateIds();

  if (!context || !getTailoringWorkspaceSuggestionArtifactKey(context)) return;

  tailoringWorkspaceState.isSaving = true;
  refreshTailoringWorkspaceInlineScoreControls();
  updateTailoringWorkspaceSelectionActionBar();

  try {
    const response = await postJson(buildPlanningEndpoint("/planning/save-workspace-draft", context.planningOutputDir), {
      tailoring_json_path: getTailoringWorkspaceSuggestionArtifactKey(context),
      selected_resume: getTailoringWorkspaceResumePreviewName(context),
      selected_patch_candidate_ids: selectedIds,
      manual_bullet_edits: normalizeTailoringWorkspaceManualBulletEdits(
        tailoringWorkspaceState.manualBulletEdits || {},
        getTailoringWorkspacePayload()
      ),
      rewrite_review_decisions: getTailoringWorkspaceCurrentReviewDecisionMap(),
      note: "Saved from tailoring workspace draft.",
    });

    const savedDraft =
      response && response.draft && typeof response.draft === "object"
        ? response.draft
        : null;

    tailoringWorkspaceState.draftPayload = savedDraft;
    tailoringWorkspaceState.savedSelectionPayload =
      buildTailoringWorkspaceSavedSelectionPayloadFromDraft(savedDraft);

    tailoringWorkspaceState.previewPayload = null;
    tailoringWorkspaceState.previewReadyKey = "";
    tailoringWorkspaceState.activeInlineScoreKey = "";
    tailoringWorkspaceState.activeReviewEditCandidateId = "";

    if (savedDraft && savedDraft.manual_bullet_edits && typeof savedDraft.manual_bullet_edits === "object") {
      tailoringWorkspaceState.manualBulletEdits = { ...savedDraft.manual_bullet_edits };
    }

    tailoringWorkspaceState.rewriteReviewDecisions =
      savedDraft && savedDraft.rewrite_review_decisions && typeof savedDraft.rewrite_review_decisions === "object"
        ? normalizeTailoringWorkspaceReviewDecisionMap(savedDraft.rewrite_review_decisions)
        : {};

    if (tailoringWorkspaceState.savedSelectionPayload) {
      syncTailoringWorkspaceSavedSelectionIntoArtifact(
        tailoringWorkspaceState.savedSelectionPayload
      );
    }

    rerenderTailoringWorkspaceSelectionView();
  } catch (err) {
    showAppError("Failed to save workspace draft", err);
  } finally {
    tailoringWorkspaceState.isSaving = false;
    refreshTailoringWorkspaceInlineScoreControls();
    updateTailoringWorkspaceSelectionActionBar();
  }
}

function clearTailoringWorkspaceSelection() {
  tailoringWorkspaceState.selectedCandidateIds = [];
  tailoringWorkspaceState.manualBulletEdits = {};
  tailoringWorkspaceState.rewriteReviewDecisions = {};
  tailoringWorkspaceState.previewPayload = null;
  tailoringWorkspaceState.previewReadyKey = "";
  tailoringWorkspaceState.activeInlineScoreKey = "";
  tailoringWorkspaceState.activeReviewEditCandidateId = "";

  rerenderTailoringWorkspaceSelectionView();
  syncTailoringWorkspacePreviewHighlight();
}

function revertTailoringWorkspaceSelectionToSaved() {
  const payload = getTailoringWorkspacePayload();
  const savedIds = getTailoringWorkspaceSavedCandidateIds();

  tailoringWorkspaceState.manualBulletEdits = getTailoringWorkspaceSavedManualBulletEdits();
  tailoringWorkspaceState.rewriteReviewDecisions = getTailoringWorkspaceSavedReviewDecisionMap();
  tailoringWorkspaceState.previewPayload = null;
  tailoringWorkspaceState.previewReadyKey = "";
  tailoringWorkspaceState.activeInlineScoreKey = "";
  tailoringWorkspaceState.activeReviewEditCandidateId = "";

  if (!savedIds.length) {
    tailoringWorkspaceState.selectedCandidateIds = [];
    rerenderTailoringWorkspaceSelectionView();
    syncTailoringWorkspacePreviewHighlight();
    return;
  }

  tailoringWorkspaceState.selectedCandidateIds = payload
    ? normalizeTailoringWorkspaceSelectedCandidateIds(payload, savedIds)
    : normalizeTailoringWorkspaceCandidateIdList(savedIds);

  rerenderTailoringWorkspaceSelectionView();
  syncTailoringWorkspacePreviewHighlight();
}

function bindTailoringWorkspaceActionBar() {
  const discardBtn = qs("tailoringWorkspaceDiscardBtn");
  const downloadBtn = qs("tailoringWorkspaceDownloadBtn");
  const saveBtn = qs("tailoringWorkspaceSaveSelectionBtn");

  if (!discardBtn || !downloadBtn || !saveBtn) return;
  if (discardBtn.dataset.bound === "true") return;

  discardBtn.dataset.bound = "true";

  discardBtn.addEventListener("click", () => {
    const payload = getTailoringWorkspacePayload();
    const savedIds = getTailoringWorkspaceSavedCandidateIds();
    const savedManualEdits = normalizeTailoringWorkspaceManualBulletEdits(
      getTailoringWorkspaceSavedManualBulletEdits(),
      payload
    );
    const savedReviewDecisions = getTailoringWorkspaceSavedReviewDecisionMap();

    const hasAnySavedState =
      savedIds.length > 0 ||
      Object.keys(savedManualEdits).length > 0 ||
      Object.keys(savedReviewDecisions).length > 0;

    if (hasAnySavedState) {
      revertTailoringWorkspaceSelectionToSaved();
    } else {
      clearTailoringWorkspaceSelection();
    }
  });

  downloadBtn.addEventListener("click", () => {
    openTailoringWorkspaceExportModal();
  });

  saveBtn.addEventListener("click", async () => {
    await saveTailoringWorkspaceSelection();
  });

  updateTailoringWorkspaceSelectionActionBar();
}

function renderReplacementDecisionSection({
  title,
  subtitle = "",
  items = [],
  emptyLabel = "None",
  tone = "neutral",
  mode = "replacement",
  selectionEnabled = false,
  selectedCandidateIds = [],
  reviewActionsEnabled = false,
  reviewDecisionMap = null,
  actionPrefix = "tailoring",
}) {
  const safeItems = Array.isArray(items) ? items : [];
  const selectedSet = new Set(
    (Array.isArray(selectedCandidateIds) ? selectedCandidateIds : [])
      .map((value) => String(value || "").trim())
      .filter(Boolean)
  );

  const effectiveReviewDecisionMap =
    reviewDecisionMap && typeof reviewDecisionMap === "object"
      ? reviewDecisionMap
      : actionPrefix === "tailoring"
        ? getTailoringWorkspaceCurrentReviewDecisionMap()
        : {};

  const orderedItems = selectionEnabled
    ? safeItems.slice().sort((left, right) => {
        const leftId = getTailoringReplacementCandidateId(left);
        const rightId = getTailoringReplacementCandidateId(right);

        const leftSelected = Boolean(leftId && selectedSet.has(leftId));
        const rightSelected = Boolean(rightId && selectedSet.has(rightId));

        if (leftSelected === rightSelected) return 0;
        return leftSelected ? -1 : 1;
      })
    : safeItems;

  const selectedCount = selectionEnabled ? selectedSet.size : 0;
  const isScan = actionPrefix === "scan";

  if (!safeItems.length) {
    return `
      <section class="tailoring-section-block">
        <div class="tailoring-section-title">${escapeHtml(title)}</div>
        ${selectionEnabled ? `
          <div class="tailoring-section-meta">
            <span class="tailoring-section-meta-count">${escapeHtml(String(selectedCount))} selected</span>
            <span class="tailoring-section-meta-copy">Preview or save from the toolbar when ready.</span>
          </div>
        ` : ""}
        ${subtitle ? `<div class="tailoring-card-copy">${escapeHtml(subtitle)}</div>` : ""}
        <div class="tailoring-empty-inline">${escapeHtml(emptyLabel)}</div>
      </section>
    `;
  }

  return `
    <section class="tailoring-section-block">
      <div class="tailoring-section-title">${escapeHtml(title)}</div>
      ${subtitle ? `<div class="tailoring-card-copy">${escapeHtml(subtitle)}</div>` : ""}

      <div class="tailoring-edit-card-list">
        ${orderedItems.map((item, index) => {
          const displayCurrentBullet = getTailoringWorkspaceDisplayBulletText(item, mode);
          const priority = String(item.apply_priority || "low");
          const likelyImpactedDimensions = Array.isArray(item.likely_impacted_dimensions)
            ? item.likely_impacted_dimensions.filter(Boolean)
            : [];
          const impactLabels = likelyImpactedDimensions.map((value) =>
            humanizeUnderscoreLabel(value)
          );

          const candidateId = getTailoringReplacementCandidateId(item);
          const isFocusable = Boolean(candidateId);
          const isSelectable = Boolean(selectionEnabled && mode === "replacement" && candidateId);
          const isSelected = Boolean(isSelectable && selectedSet.has(candidateId));

          const reviewState =
            reviewActionsEnabled && mode === "direction_only"
              ? getReplacementReviewState(item, effectiveReviewDecisionMap)
              : "";
          const reviewStatusChip =
            reviewActionsEnabled && candidateId && reviewState && reviewState !== "pending"
              ? buildTailoringTonePill(
                  getTailoringWorkspaceReviewDecisionLabel(reviewState),
                  getTailoringWorkspaceReviewDecisionTone(reviewState)
                )
              : "";

          const statusLabel =
            item.replacement_status === "direct_apply_ready"
              ? (isScan ? "Ready" : "Ready to use")
              : item.replacement_status === "direct_apply_optional"
                ? (isScan ? "Trusted" : "Trusted optional")
                : item.replacement_status === "ai_optimize_optional"
                  ? (isScan ? "AI optional" : "AI optimize optional")
                  : (isScan ? "Review" : "Review only");

          const focusAttr = isFocusable
            ? `data-${actionPrefix}-focus-candidate="${escapeHtml(candidateId)}"`
            : "";

          const reasonText = String(item.why_selected || "").trim();

          const isActiveScanCard =
            isScan &&
            candidateId &&
            scanWorkspaceState.activeCandidateId &&
            scanWorkspaceState.activeCandidateId === candidateId;

          const summarySourceText =
            mode === "direction_only"
              ? (item.rewrite_direction || reasonText || displayCurrentBullet || "")
              : (item.final_replacement_text || displayCurrentBullet || reasonText || "");

          const summaryText = String(summarySourceText || "").trim();

          const showCurrentBulletBlock =
            Boolean(displayCurrentBullet) && (!isScan || mode === "direction_only");

          const replacementLabel =
            mode === "direction_only"
              ? (isScan ? "Direction" : "Suggested change")
              : (isScan ? "Suggestion" : "Suggested edit");

          const currentBulletLabel = isScan ? "Original" : "Current bullet";

          const priorityChip =
            (!isScan || priority === "high") && priority !== "low"
              ? buildTailoringTonePill(
                  priority === "high"
                    ? "High priority"
                    : priority === "medium"
                      ? "Medium priority"
                      : "Low priority",
                  priority === "high"
                    ? "safe"
                    : priority === "medium"
                      ? "caution"
                      : "muted"
                )
              : "";

          const compactImpactHtml = impactLabels.length
            ? `
              <div class="tailoring-chip-group tailoring-chip-group--compact tailoring-edit-impact-chips">
                ${impactLabels
                  .slice(0, 3)
                  .map((label) => buildTailoringTonePill(label, "neutral"))
                  .join("")}
              </div>
            `
            : "";

          const claimSafetyValue = String(item.claim_safety || "").trim();
          const showClaimSafetyChip =
            claimSafetyValue &&
            claimSafetyValue !== "safe_strengthen";

          const claimSafetyLabel = showClaimSafetyChip
            ? humanizeUnderscoreLabel(claimSafetyValue)
            : "";

          const claimSafetyTone =
            claimSafetyValue === "adjacent_only"
              ? "caution"
              : claimSafetyValue
                ? "danger"
                : "";

  const trustReasonText = String(
    item.direction_only_reason ||
    item.why_not_material ||
    item.materiality_reason ||
    ""
  ).trim();
  const rewriteDirectionText = String(item.rewrite_direction || "").trim();
  const compactTrustReasonText =
    trustReasonText && trustReasonText !== rewriteDirectionText
      ? trustReasonText
      : "";

  const compactTrustHtml =
    claimSafetyLabel || compactTrustReasonText
      ? `
        <div class="tailoring-edit-inline-summary tailoring-edit-inline-summary--trust">
          ${claimSafetyLabel ? `
            <div class="tailoring-chip-group tailoring-chip-group--compact tailoring-edit-impact-chips">
              ${buildTailoringTonePill(claimSafetyLabel, claimSafetyTone)}
            </div>
          ` : ""}
          ${compactTrustReasonText ? `
            <div
              class="tailoring-edit-inline-reason tailoring-edit-inline-reason--trust"
              title="${escapeHtml(compactTrustReasonText)}"
            >
              ${escapeHtml(compactTrustReasonText)}
            </div>
          ` : ""}
        </div>
      `
      : "";

          const shouldShowCompactReason =
            reasonText &&
    (!compactTrustReasonText || reasonText !== compactTrustReasonText) &&
    (!rewriteDirectionText || reasonText !== rewriteDirectionText);

          const compactReasonHtml = shouldShowCompactReason
            ? `
              <div
                class="tailoring-edit-inline-reason"
                title="${escapeHtml(reasonText)}"
              >
                ${escapeHtml(reasonText)}
              </div>
            `
            : "";

          const compactScoreHtml =
            mode !== "direction_only" && !isScan
              ? renderTailoringWorkspaceScorePills({
                  originalScore: item.original_final_score,
                  projectedScore: item.projected_final_score,
                  projectedDelta: item.projected_overall_delta,
                })
              : "";
          const criticDetailsHtml = renderScanWorkspaceCriticAdvisoryDetails(item);

          return `
            <article
              class="tailoring-edit-card tailoring-edit-card--compact ${isFocusable ? "tailoring-edit-card--clickable" : ""} ${isSelected ? "tailoring-edit-card--selected" : ""} ${isScan ? "scan-workspace-inventory-card" : ""} ${isActiveScanCard ? "is-active" : ""}"
              ${focusAttr}
            >
              <div class="tailoring-card-topline tailoring-card-topline--compact ${isScan ? "tailoring-card-topline--scan" : ""}">
                <div class="tailoring-edit-card-label">${isScan ? `Item ${index + 1}` : `Suggestion ${index + 1}`}</div>

                <div class="tailoring-chip-group tailoring-chip-group--compact">
                  ${buildTailoringTonePill(statusLabel, tone)}
                  ${priorityChip}
                  ${reviewStatusChip}
                </div>
              </div>

              ${isScan ? `
                <button
                  type="button"
                  class="scan-workspace-inventory-row ${isActiveScanCard ? "is-active" : ""}"
                  data-scan-focus-candidate="${escapeHtml(candidateId)}"
                >
                  <span class="scan-workspace-inventory-row-text">
                    ${escapeHtml(summaryText || "Open suggestion")}
                  </span>
                </button>
              ` : ""}
              
              ${isScan ? `<div class="scan-workspace-inventory-details ${isActiveScanCard ? "is-open" : ""}">` : ""}

              ${showCurrentBulletBlock ? `
                <div class="tailoring-info-block tailoring-info-block--compact">
                  <div class="tailoring-info-label">${currentBulletLabel}</div>
                  <div class="tailoring-quote-block">${escapeHtml(displayCurrentBullet)}</div>
                </div>
              ` : ""}

              ${compactTrustHtml}

              ${mode !== "direction_only" && item.final_replacement_text ? `
                <div class="tailoring-info-block tailoring-info-block--compact">
                  <div class="tailoring-info-label">${replacementLabel}</div>
                  <div class="tailoring-rewrite-callout">${escapeHtml(item.final_replacement_text)}</div>
                </div>
              ` : ""}

              ${mode === "direction_only" && item.rewrite_direction ? `
                <div class="tailoring-info-block tailoring-info-block--compact">
                  <div class="tailoring-info-label">${replacementLabel}</div>
                  <div class="tailoring-rewrite-callout">${escapeHtml(item.rewrite_direction)}</div>
                </div>
              ` : ""}

              ${(compactReasonHtml || compactImpactHtml) ? `
                <div class="tailoring-edit-inline-summary">
                  ${compactReasonHtml}
                  ${compactImpactHtml}
                </div>
              ` : ""}

              ${criticDetailsHtml}

              ${reviewActionsEnabled && mode === "direction_only" && candidateId ? `
                <div class="tailoring-card-actions tailoring-card-actions--compact tailoring-card-actions--review">
                  <button
                    type="button"
                    class="ghost-btn btn-sm tailoring-review-action-btn ${reviewState === "accepted" ? "is-active" : ""}"
                    data-${actionPrefix}-review-state="accepted"
                    data-${actionPrefix}-review-action="accepted"
                    data-${actionPrefix}-review-candidate="${escapeHtml(candidateId)}"
                  >
                    ${isScan ? "Accept" : "Accept as-is"}
                  </button>

                  <button
                    type="button"
                    class="ghost-btn btn-sm tailoring-review-action-btn ${reviewState === "rejected" ? "is-active" : ""}"
                    data-${actionPrefix}-review-state="rejected"
                    data-${actionPrefix}-review-action="rejected"
                    data-${actionPrefix}-review-candidate="${escapeHtml(candidateId)}"
                  >
                    Reject
                  </button>

                  <button
                    type="button"
                    class="ghost-btn btn-sm tailoring-review-action-btn ${reviewState === "edited_after_accept" ? "is-active" : ""}"
                    data-${actionPrefix}-review-edit="${escapeHtml(candidateId)}"
                  >
                    ${isScan ? "Edit" : "Edit manually"}
                  </button>
                </div>
              ` : isSelectable ? `
                <div class="tailoring-card-actions tailoring-card-actions--compact">
                  <div class="tailoring-chip-group">
                    ${compactScoreHtml}
                  </div>

                  <button
                    type="button"
                    class="ghost-btn btn-sm tailoring-select-btn ${isSelected ? "is-selected" : ""}"
                    data-${actionPrefix}-select-candidate="${escapeHtml(candidateId)}"
                  >
                    ${isSelected ? "Remove" : "Add"}
                  </button>
                </div>
              ` : ""}

              ${isSelected ? buildTailoringTonePill("Selected", "safe") : ""}
              ${isScan ? `</div>` : ""}
            </article>
          `;
        }).join("")}
      </div>
    </section>
  `;
}

function hasTailoringItems(items) {
  return Array.isArray(items) && items.some(Boolean);
}

function setTailoringSectionVisible(contentId, isVisible) {
  const root = qs(contentId);
  if (!root) return;

  const section = root.closest("section");
  if (!section) return;

  section.classList.toggle("hidden", !isVisible);
}

function setTailoringManualAccordionExpanded(toggleButton, panel, isExpanded) {
  if (!toggleButton || !panel) return;

  toggleButton.setAttribute("aria-expanded", isExpanded ? "true" : "false");
  panel.classList.toggle("hidden", !isExpanded);
}

function toggleTailoringManualAccordion(toggleButton) {
  if (!toggleButton) return;

  const panelId =
    toggleButton.getAttribute("aria-controls") ||
    toggleButton.dataset.tailoringAccordionToggle;

  const panel = panelId ? qs(panelId) : null;
  if (!panel) return;

  const isExpanded = toggleButton.getAttribute("aria-expanded") === "true";
  setTailoringManualAccordionExpanded(toggleButton, panel, !isExpanded);
}

function collapseTailoringManualAccordions() {
  document.querySelectorAll("[data-tailoring-accordion-toggle]").forEach((toggleButton) => {
    const panelId =
      toggleButton.getAttribute("aria-controls") ||
      toggleButton.dataset.tailoringAccordionToggle;

    const panel = panelId ? qs(panelId) : null;
    setTailoringManualAccordionExpanded(toggleButton, panel, false);
  });
}

function isFinitePreviewNumber(value) {
  if (value === null || value === undefined) return false;

  const text = String(value).trim();
  if (!text || text === "-") return false;

  const parsed = Number(text.replaceAll(",", ""));
  return Number.isFinite(parsed);
}

function hasRenderableDimensionDeltas(deltas) {
  return Object.values(deltas || {}).some((value) => {
    const parsed = Number(value);
    return Number.isFinite(parsed);
  });
}

function hasMeaningfulPatchPreview(preview) {
  if (!preview || typeof preview !== "object" || !Object.keys(preview).length) {
    return false;
  }

  const status = String(preview.status || "").trim().toLowerCase();
  if (!status) return false;

  if (
    [
      "none",
      "no_patch_ready_rewrites",
      "no_valid_selected_candidates",
    ].includes(status)
  ) {
    return false;
  }

  const projectedScorePresent = isFinitePreviewNumber(preview.projected_final_score);
  const originalScorePresent = isFinitePreviewNumber(preview.original_final_score);
  const overallDeltaPresent = isFinitePreviewNumber(preview.projected_overall_delta);
  const evidenceChanged = Boolean(preview.scorer_visible_evidence_changed);
  const dimensionDeltasPresent = hasRenderableDimensionDeltas(preview.projected_dimension_deltas);

  const appliedCandidateIdsPresent =
    Array.isArray(preview.selected_candidate_ids) &&
    preview.selected_candidate_ids.some((value) => String(value || "").trim());

  if (status === "scored") {
    return (
      projectedScorePresent ||
      originalScorePresent ||
      overallDeltaPresent ||
      evidenceChanged ||
      dimensionDeltasPresent ||
      appliedCandidateIdsPresent
    );
  }

  return (
    projectedScorePresent ||
    overallDeltaPresent ||
    evidenceChanged ||
    dimensionDeltasPresent
  );
}

function shouldShowPatchPreviewSection(payload) {
  if (!payload || typeof payload !== "object") return false;

  const selectedPreview = payload.selected_patch_set_counterfactual_preview || null;
  const autoPreview = payload.patch_set_counterfactual_preview || null;

  return (
    hasMeaningfulPatchPreview(selectedPreview) ||
    hasMeaningfulPatchPreview(autoPreview)
  );
}

function shouldShowPatchSelectionSection(payload) {
  if (!payload || typeof payload !== "object") return false;

  const preview = payload.selected_patch_set_counterfactual_preview || null;
  return hasMeaningfulPatchPreview(preview);
}

function renderLegacyDiagnosticDetails(payload) {
  const keepAsIs = Array.isArray(payload.keep_as_is) ? payload.keep_as_is : [];
  const materialGaps = Array.isArray(payload.material_gaps) ? payload.material_gaps : [];
  const claimSafetyNotes = payload.claim_safety_notes || {};

  const hasDiagnosticContent =
    keepAsIs.length ||
    materialGaps.length ||
    (claimSafetyNotes && Object.keys(claimSafetyNotes).length);

  if (!hasDiagnosticContent) return "";

  return `
    <details class="tailoring-section-block">
      <summary class="tailoring-section-title">More detail</summary>
      <div class="tailoring-card-copy">Extra context for review.</div>
      ${renderClaimSafetyNotes(claimSafetyNotes)}
      ${renderMaterialGaps(materialGaps)}
      ${renderKeepAsIs(keepAsIs)}
    </details>
  `;
}

function renderTailoringEmptyState(payload) {
  const notes = payload && typeof payload === "object" ? payload.claim_safety_notes || {} : {};
  const emptyState = payload && typeof payload === "object" ? payload.empty_state_reason || {} : {};
  const materialGaps = Array.isArray(payload?.material_gaps) ? payload.material_gaps : [];
  const frameCarefully = Array.isArray(notes.frame_carefully) ? notes.frame_carefully : [];
  const doNotAdd = Array.isArray(notes.do_not_add) ? notes.do_not_add : [];

  const title = String(emptyState.title || "").trim() || "No safe bullet-level rewrites were found";
  const summary = String(emptyState.summary || "").trim() ||
    "This JD/resume pair does not have enough grounded rewrite evidence to suggest stronger bullet rewrites safely.";

  const mainBlockers = Array.isArray(emptyState.main_blockers) && emptyState.main_blockers.length
    ? emptyState.main_blockers
    : materialGaps.map((item) => item.label || "").filter(Boolean);

  const stillUseful = Array.isArray(emptyState.still_useful)
    ? emptyState.still_useful
    : [];

  const nextStep = String(emptyState.next_step || "").trim();
  const rawMissingJdFocus = Array.isArray(emptyState.missing_jd_focus) ? emptyState.missing_jd_focus : [];
  const resumeLimitationSummary = String(emptyState.resume_limitation_summary || "").trim();
  const keepVisibleNow = Array.isArray(emptyState.keep_visible_now) ? emptyState.keep_visible_now : [];
  const hasKeepCardsBelow = Array.isArray(payload?.keep_as_is) && payload.keep_as_is.length > 0;

  const normalizeList = (items) =>
    items.map((item) => String(item || "").trim().toLowerCase()).filter(Boolean);

  const sameList =
    JSON.stringify(normalizeList(mainBlockers)) === JSON.stringify(normalizeList(rawMissingJdFocus));

  const missingJdFocus = sameList ? [] : rawMissingJdFocus;

  const keepVisibleLines = keepVisibleNow.map((item) => {
    const label = String(item?.label || "").trim();
    const evidence = String(item?.evidence || "").trim();
    const reason = String(item?.reason || "").trim();
    const overlaps = Array.isArray(item?.overlaps) ? item.overlaps.filter(Boolean) : [];

    return [
      label,
      overlaps.length ? `Overlap: ${overlaps.join(", ")}` : "",
      evidence,
      reason,
    ].filter(Boolean).join(" — ");
  }).filter(Boolean);

  return `
    <section class="tailoring-section-block">
      <div class="tailoring-empty-state">
        <div class="tailoring-empty-title">${escapeHtml(title)}</div>
        <div class="tailoring-empty-copy">${escapeHtml(summary)}</div>

        ${mainBlockers.length ? `
          <div class="tailoring-empty-subsection">
            <div class="tailoring-empty-subtitle">Main blockers</div>
            ${buildTailoringList(mainBlockers)}
          </div>
        ` : ""}

        ${missingJdFocus.length ? `
          <div class="tailoring-empty-subsection">
            <div class="tailoring-empty-subtitle">Missing JD focus</div>
            ${buildTailoringList(missingJdFocus)}
          </div>
        ` : ""}

        ${stillUseful.length ? `
          <div class="tailoring-empty-subsection">
            <div class="tailoring-empty-subtitle">Still useful</div>
            ${buildTailoringList(stillUseful)}
          </div>
        ` : ""}

        ${resumeLimitationSummary ? `
          <div class="tailoring-empty-subsection">
            <div class="tailoring-empty-subtitle">Selected resume limitation</div>
            <div class="tailoring-card-copy">${escapeHtml(resumeLimitationSummary)}</div>
          </div>
        ` : ""}

        ${!hasKeepCardsBelow && keepVisibleLines.length ? `
          <div class="tailoring-empty-subsection">
            <div class="tailoring-empty-subtitle">Keep visible now</div>
            ${buildTailoringList(keepVisibleLines)}
          </div>
        ` : ""}

        ${nextStep ? `
          <div class="tailoring-empty-subsection">
            <div class="tailoring-empty-subtitle">Recommended next step</div>
            <div class="tailoring-card-copy">${escapeHtml(nextStep)}</div>
          </div>
        ` : ""}
      </div>
    </section>
  `;
}

function renderTailoringAnchorEvidenceSection({
  title = "Anchor evidence",
  items = [],
  emptyLabel = "No anchor evidence for this row.",
} = {}) {
  const safeItems = getRenderableTailoringAnchorCards(items, 3);

  if (!safeItems.length) {
    return `
      <section class="tailoring-section-block">
        <div class="tailoring-section-title">${escapeHtml(title)}</div>
        <div class="tailoring-empty-inline">${escapeHtml(emptyLabel)}</div>
      </section>
    `;
  }

  return `
    <section class="tailoring-section-block">
      <div class="tailoring-section-title">${escapeHtml(title)}</div>

      <div class="tailoring-edit-card-list">
        ${safeItems.map((item, index) => {
          const signalTerms = Array.isArray(item.jd_signal_terms)
            ? item.jd_signal_terms.filter(Boolean)
            : [];
          const source = String(item.source || "").trim();
          const currentEvidence = String(item.current_evidence || item.parent_bullet || "").trim();
          const reviewCase = getTailoringAnchorReviewCase(item);
          const reviewLabel = getTailoringAnchorReviewLabel(item);
          const reviewTone = getTailoringAnchorReviewTone(item);
          const reviewNote = getTailoringAnchorReviewNote(item);

          const reviewCaseClass =
            reviewCase === "fronting"
              ? "tailoring-edit-card--review-fronting"
              : reviewCase === "support"
                ? "tailoring-edit-card--review-support"
                : "tailoring-edit-card--review-preserve";

          return `
            <article class="tailoring-edit-card tailoring-edit-card--compact ${reviewCaseClass}">
              <div class="tailoring-card-topline tailoring-card-topline--compact">
                <div class="tailoring-edit-card-label">Anchor ${index + 1}</div>

                <div class="tailoring-chip-group tailoring-chip-group--compact">
                  ${buildTailoringTonePill(reviewLabel, reviewTone)}
                  ${signalTerms.slice(0, 2).map((term) => buildTailoringTonePill(term, "neutral")).join("")}
                </div>
              </div>

              ${source ? `
                <div class="tailoring-card-copy">${escapeHtml(source)}</div>
              ` : ""}

              ${currentEvidence ? `
                <div class="tailoring-info-block tailoring-info-block--compact">
                  <div class="tailoring-info-label">Current bullet</div>
                  <div class="tailoring-quote-block">${escapeHtml(currentEvidence)}</div>
                </div>
              ` : ""}

              ${reviewNote ? `
                <div class="tailoring-info-block tailoring-info-block--compact">
                  <div class="tailoring-info-label">Review note</div>
                  <div class="tailoring-card-copy">${escapeHtml(reviewNote)}</div>
                </div>
              ` : ""}
            </article>
          `;
        }).join("")}
      </div>
    </section>
  `;
}

function renderReplacementPlanSummary(summary = {}) {
  const data = summary && typeof summary === "object" ? summary : {};
  const total = Number(data.total_rewrite_bullets || data.total_candidates || 0);
  const ready = Number(
    data.app_ready_count ||
    data.direct_apply_ready_count ||
    0
  );
  const optional = Number(
    data.direct_apply_optional_count ||
    data.ai_optimize_optional_count ||
    0
  );
  const review = Number(data.direction_only_count || 0);
  const keep = Number(data.keep_original_count || 0);

  if (!total && !ready && !optional && !review && !keep) return "";

  const chips = [
    ready ? buildTailoringTonePill(`Ready ${ready}`, "safe") : "",
    optional ? buildTailoringTonePill(`Optional ${optional}`, "caution") : "",
    review ? buildTailoringTonePill(`Review ${review}`, "neutral") : "",
    keep ? buildTailoringTonePill(`Keep ${keep}`, "muted") : "",
  ].filter(Boolean).join("");

  return `
    <section class="tailoring-section-block tailoring-section-block--summary">
      <div class="tailoring-section-title">Suggestion summary</div>
      <div class="tailoring-card-copy">
        ${total
          ? `${escapeHtml(String(total))} rewrite candidate${total === 1 ? "" : "s"} evaluated for this row.`
          : "Suggestion counts loaded for this row."}
      </div>
      ${chips ? `<div class="tailoring-chip-group tailoring-chip-group--compact">${chips}</div>` : ""}
    </section>
  `;
}

function renderTailoringInteractiveSummaryInto(
  rootId,
  artifact,
  {
    includeDiagnostics = true,
    selectionEnabled = false,
    selectedCandidateIds = [],
    bucketFilter = "",
  } = {}
) {
  const root = qs(rootId);
  if (!root) return;

  const payload = artifact && artifact.kind === "json" && artifact.data && typeof artifact.data === "object"
    ? artifact.data
    : null;

  if (!payload) {
    root.innerHTML = `<div class="tailoring-empty-state">Suggested changes are not available for this row.</div>`;
    syncTailoringWorkspaceFocusedCards();
    return;
  }

  const summary = payload.final_replacement_summary || {};
  const appReady = Array.isArray(payload.app_ready_replacements) ? payload.app_ready_replacements : [];
  const directApplyOptional = Array.isArray(payload.direct_apply_optional_replacements)
    ? payload.direct_apply_optional_replacements
    : [];
  const directionOnly = Array.isArray(payload.direction_only_replacements) ? payload.direction_only_replacements : [];
  const anchorCards = Array.isArray(payload.anchor_cards) ? payload.anchor_cards : [];
  const decisions = Array.isArray(payload.final_replacement_decisions) ? payload.final_replacement_decisions : [];

  const hasSuggestionEvidence =
    decisions.length ||
    appReady.length ||
    directApplyOptional.length ||
    directionOnly.length ||
    anchorCards.length;

  if (!hasSuggestionEvidence) {
    root.innerHTML = renderTailoringEmptyState(payload);
    return;
  }

  const recommendedHtml = directionOnly.length
    ? renderReplacementDecisionSection({
        title: "Review guidance",
        subtitle: "Manual guidance only. Use Free Edit for changes you want to keep.",
        items: directionOnly,
        emptyLabel: "No review-only suggestions.",
        tone: "muted",
        mode: "direction_only",
        reviewActionsEnabled: selectionEnabled,
      })
    : "";

  const anchorHtml = anchorCards.length
    ? renderTailoringAnchorEvidenceSection({
        title: "Anchor evidence",
        items: anchorCards,
        emptyLabel: "No anchor evidence for this row.",
      })
    : "";

  const readyHtml = appReady.length
    ? renderReplacementDecisionSection({
        title: "Ready to use",
        subtitle: "Score-safe replacements available for selection.",
        items: appReady,
        emptyLabel: "No ready-to-use edits.",
        tone: "safe",
        mode: "replacement",
        selectionEnabled,
        selectedCandidateIds,
      })
    : "";

  const optionalHtml = directApplyOptional.length
    ? renderReplacementDecisionSection({
        title: "Nice to improve",
        subtitle: "Safe wording improvements with smaller projected impact.",
        items: directApplyOptional,
        emptyLabel: "No optional improvements.",
        tone: "caution",
        mode: "replacement",
        selectionEnabled,
        selectedCandidateIds,
      })
    : "";

  const normalizedBucket = String(bucketFilter || "").trim().toLowerCase();

  let bucketHtml = "";
  if (normalizedBucket === "ready") {
    bucketHtml = `${readyHtml}${optionalHtml}`;
    if (!bucketHtml.trim()) {
      bucketHtml = `
        <section class="tailoring-section-block">
          <div class="tailoring-section-title">Ready to use</div>
          <div class="tailoring-empty-inline">No ready suggestions for this row.</div>
        </section>
      `;
    }
  } else if (normalizedBucket === "review") {
    bucketHtml = `${recommendedHtml}${anchorHtml}`;
    if (!bucketHtml.trim()) {
      bucketHtml = `
        <section class="tailoring-section-block">
          <div class="tailoring-section-title">Review</div>
          <div class="tailoring-empty-inline">No review guidance or anchor evidence is available for this row.</div>
        </section>
      `;
    }
  } else {
    bucketHtml = `${readyHtml}${optionalHtml}${recommendedHtml}${anchorHtml}`;
  }

  const diagnosticsHtml =
    includeDiagnostics && !normalizedBucket && !anchorCards.length
      ? renderLegacyDiagnosticDetails(payload)
      : "";

  root.innerHTML = `
    ${normalizedBucket ? "" : renderReplacementPlanSummary(summary)}
    ${bucketHtml}
    ${diagnosticsHtml}
  `;
}

function renderTailoringInteractiveSummary(artifact) {
  renderTailoringInteractiveSummaryInto("tailoringInteractiveSummary", artifact, {
    includeDiagnostics: true,
  });
}

async function initTailoringWorkspacePage() {
  const page = document.querySelector(".tailoring-workspace-page");
  if (!page) return false;

  const tailoringJsonPath = String(page.dataset.tailoringJsonPath || "").trim();
  const resumeName = String(page.dataset.resumeName || "").trim();
  const meta = qs("tailoringWorkspaceMeta");
  const root = qs("tailoringWorkspaceInteractiveSummary");

  if (!root) return true;

  const previewPromise = setTailoringWorkspacePreview(resumeName);

  if (!tailoringJsonPath) {
    if (meta) {
      meta.textContent = "No tailoring JSON path was provided for this workspace row.";
    }

    root.innerHTML = `
      <div class="tailoring-empty-state">
        Suggested changes are not available for this row yet.
      </div>
    `;

    tailoringWorkspaceState.artifact = null;
    tailoringWorkspaceState.draftPayload = null;
    tailoringWorkspaceState.selectedCandidateIds = [];
    tailoringWorkspaceState.candidateLookup = new Map();
    tailoringWorkspaceState.previewPayload = null;
    tailoringWorkspaceState.savedSelectionPayload = null;

    updateTailoringWorkspaceHeroStatus(null);
    clearTailoringWorkspacePatchPreviewSection();
    clearTailoringWorkspaceSavedSelectionSection();
    updateTailoringWorkspaceSelectionActionBar();

    await previewPromise;
    return true;
  }

  try {
    if (meta) {
      meta.textContent = "Loading action-first suggestion set...";
    }

    const context = getTailoringWorkspaceContext();
    const tailoringJsonArtifact = await loadArtifact(
      getTailoringWorkspaceSuggestionArtifactKey(context) || tailoringJsonPath,
      context?.planningOutputDir
    );

    let draftResponse = null;
    try {
      draftResponse = await loadTailoringWorkspaceDraft();
    } catch (draftErr) {
      console.warn("Failed to load saved workspace draft; falling back to artifact state.", draftErr);
    }

    initializeTailoringWorkspaceSelectionState(tailoringJsonArtifact, draftResponse);
    updateTailoringWorkspaceHeroStatus(tailoringJsonArtifact);
    rerenderTailoringWorkspaceSelectionView();

    await previewPromise;
    syncTailoringWorkspacePreviewHighlight();
  } catch (err) {
    if (meta) {
      meta.textContent = "Failed to load suggestion set.";
    }

    root.innerHTML = `
      <div class="tailoring-empty-state">
        Failed to load suggested changes for this workspace row.
      </div>
    `;

    tailoringWorkspaceState.artifact = null;
    tailoringWorkspaceState.draftPayload = null;
    tailoringWorkspaceState.selectedCandidateIds = [];
    tailoringWorkspaceState.candidateLookup = new Map();
    tailoringWorkspaceState.previewPayload = null;
    tailoringWorkspaceState.savedSelectionPayload = null;

    updateTailoringWorkspaceHeroStatus(null);
    clearTailoringWorkspacePatchPreviewSection();
    clearTailoringWorkspaceSavedSelectionSection();
    updateTailoringWorkspaceSelectionActionBar();

    console.error("Failed to initialize tailoring workspace", err);
  }

  return true;
}

function buildScanWorkspaceBackToTailoringUrl() {
  const context = getScanWorkspaceContext();
  if (!context) return "/tailoring-workspace";

  const params = new URLSearchParams();
  params.set("company", context.company || "");
  params.set("title", context.title || "");
  params.set("resume", normalizeResumePreviewName(context.resumeName) || "");
  params.set("status", context.status || "");
  if (context.jobDocId) params.set("job_doc_id", context.jobDocId);
  if (getTailoringWorkspaceSuggestionArtifactKey(context)) {
    params.set("tailoring_json", getTailoringWorkspaceSuggestionArtifactKey(context));
  }
  if (context.tailoringMdPath) params.set("tailoring_md", context.tailoringMdPath);
  if (context.tailoringLlmJsonPath) params.set("tailoring_llm_json", context.tailoringLlmJsonPath);
  if (context.packetJsonKey || context.packetJsonPath) {
    params.set("packet_json", context.packetJsonKey || context.packetJsonPath);
  }
  if (context.planningOutputDir) params.set("output_dir", context.planningOutputDir);

  return `/tailoring-workspace?${params.toString()}`;
}

async function loadScanWorkspacePreload() {
  const context = getScanWorkspaceContext();
  if (!context || !getTailoringWorkspaceSuggestionArtifactKey(context)) return null;

  return postJson(buildPlanningEndpoint("/planning/scan-preload", context.planningOutputDir), {
    tailoring_json_path: getTailoringWorkspaceSuggestionArtifactKey(context),
    base_packet_path: getTailoringWorkspaceBasePacketKey(context),
    suggestion_artifact_path: getTailoringWorkspaceSuggestionArtifactKey(context),
    selected_resume: getTailoringWorkspaceResumePreviewName(context),
  });
}

function updateScanWorkspaceZoomLabel() {
  const label = qs("scanWorkspaceZoomResetBtn");
  if (!label) return;
  const percent = Math.round((scanWorkspacePdfState.scale || 1) * 100);
  label.textContent = `${percent}%`;
}

function getScanWorkspacePdfScrollerMetrics() {
  const scroller = qs("scanWorkspacePdfScroller");
  if (!scroller) return null;

  const styles = window.getComputedStyle(scroller);
  const horizontalPadding =
    parseFloat(styles.paddingLeft || "0") + parseFloat(styles.paddingRight || "0");

  return {
    scroller,
    availableWidth: Math.max(240, scroller.clientWidth - horizontalPadding - 4),
  };
}

async function getScanWorkspacePdfJs() {
  if (!scanWorkspacePdfState.pdfjsPromise) {
    scanWorkspacePdfState.pdfjsPromise = import("/static/vendor/pdfjs/pdf.mjs").then((pdfjsLib) => {
      pdfjsLib.GlobalWorkerOptions.workerSrc = "/static/vendor/pdfjs/pdf.worker.mjs";
      return pdfjsLib;
    });
  }

  return scanWorkspacePdfState.pdfjsPromise;
}

async function clearScanWorkspacePdfView(emptyText = "Resume preview is not available for this scan.") {
  const empty = qs("scanWorkspacePreviewEmpty");
  const pages = qs("scanWorkspacePdfPages");
  const meta = qs("scanWorkspacePreviewMeta");

  if (scanWorkspacePdfState.resizeTimer) {
    window.clearTimeout(scanWorkspacePdfState.resizeTimer);
    scanWorkspacePdfState.resizeTimer = null;
  }

  if (pages) {
    pages.innerHTML = "";
    pages.classList.add("hidden");
  }

  if (empty) {
    empty.textContent = emptyText;
    empty.classList.remove("hidden");
  }

  if (meta) {
    meta.textContent = emptyText;
  }

  if (scanWorkspacePdfState.pdfDoc) {
    try {
      await scanWorkspacePdfState.pdfDoc.destroy();
    } catch (err) {
      console.warn("Failed to destroy previous scan PDF document", err);
    }
  }

  scanWorkspacePdfState.pdfDoc = null;
  scanWorkspacePdfState.resumeName = "";
  scanWorkspacePdfState.scale = 1;
  scanWorkspacePdfState.fitScale = 1;
  scanWorkspacePdfState.isFitPage = true;
  updateScanWorkspaceZoomLabel();
}

async function computeScanWorkspaceFitPageScale() {
  const pdfDoc = scanWorkspacePdfState.pdfDoc;
  const metrics = getScanWorkspacePdfScrollerMetrics();

  if (!pdfDoc || !metrics) {
    return 1;
  }

  const firstPage = await pdfDoc.getPage(1);
  const baseViewport = firstPage.getViewport({ scale: 1 });

  const fitWidthScale = metrics.availableWidth / baseViewport.width;

  if (!Number.isFinite(fitWidthScale) || fitWidthScale <= 0) {
    return 1;
  }

  return Math.max(0.45, Math.min(2.5, fitWidthScale));
}

async function renderScanWorkspacePdfPages() {
  const pagesRoot = qs("scanWorkspacePdfPages");
  const empty = qs("scanWorkspacePreviewEmpty");
  const meta = qs("scanWorkspacePreviewMeta");
  const pdfDoc = scanWorkspacePdfState.pdfDoc;

  if (!pagesRoot || !empty || !pdfDoc) return;

  const token = ++scanWorkspacePdfState.renderToken;
  const scale = scanWorkspacePdfState.scale;
  const pageCount = pdfDoc.numPages;
  const deviceScale = window.devicePixelRatio || 1;

  pagesRoot.innerHTML = "";
  pagesRoot.classList.add("hidden");
  empty.classList.remove("hidden");
  empty.textContent = `Rendering ${pageCount} page${pageCount === 1 ? "" : "s"}...`;
  if (meta) {
    meta.textContent = `Rendering ${pageCount} page${pageCount === 1 ? "" : "s"}...`;
  }
  updateScanWorkspaceZoomLabel();

  const fragment = document.createDocumentFragment();

  for (let pageNumber = 1; pageNumber <= pageCount; pageNumber += 1) {
    if (token !== scanWorkspacePdfState.renderToken) return;

    const page = await pdfDoc.getPage(pageNumber);
    const viewport = page.getViewport({ scale });

    const canvas = document.createElement("canvas");
    canvas.className = "tailoring-workspace-pdf-canvas";

    const context = canvas.getContext("2d", { alpha: false });

    canvas.width = Math.floor(viewport.width * deviceScale);
    canvas.height = Math.floor(viewport.height * deviceScale);
    canvas.style.width = `${viewport.width}px`;
    canvas.style.height = `${viewport.height}px`;

    const renderContext =
      deviceScale === 1
        ? { canvasContext: context, viewport }
        : {
            canvasContext: context,
            viewport,
            transform: [deviceScale, 0, 0, deviceScale, 0, 0],
          };

    await page.render(renderContext).promise;

    const pageShell = document.createElement("div");
    pageShell.className = "tailoring-workspace-pdf-page";
    pageShell.dataset.pageNumber = String(pageNumber);
    pageShell.style.width = `${viewport.width}px`;
    pageShell.style.height = `${viewport.height}px`;
    pageShell.appendChild(canvas);
    fragment.appendChild(pageShell);
  }

  if (token !== scanWorkspacePdfState.renderToken) return;

  pagesRoot.innerHTML = "";
  pagesRoot.appendChild(fragment);
  pagesRoot.classList.remove("hidden");
  empty.classList.add("hidden");

  if (meta) {
    meta.textContent = humanizeResumeDisplayName(scanWorkspacePdfState.resumeName || "");
  }
}

async function applyScanWorkspaceFitPageScale({ rerender = true } = {}) {
  if (!scanWorkspacePdfState.pdfDoc) return;

  await new Promise((resolve) => {
    window.requestAnimationFrame(() => resolve());
  });

  const fitScale = await computeScanWorkspaceFitPageScale();
  scanWorkspacePdfState.fitScale = fitScale;
  scanWorkspacePdfState.scale = fitScale;
  scanWorkspacePdfState.isFitPage = true;
  updateScanWorkspaceZoomLabel();

  if (rerender) {
    await renderScanWorkspacePdfPages();
  }
}

async function setScanWorkspaceResumePreview(resumeName) {
  const context = getScanWorkspaceContext();
  const safeName = normalizeResumePreviewName(resumeName || context?.resumeName || "");
  const nameEl = qs("scanWorkspacePreviewName");

  scanWorkspacePdfState.resumeName = safeName;
  if (nameEl) {
    nameEl.textContent = humanizeResumeDisplayName(safeName || "");
  }

  if (!safeName && !getTailoringWorkspaceBasePacketKey(context)) {
    await clearScanWorkspacePdfView("No resume selected for this scan.");
    return;
  }

  try {
    const pdfjsLib = await getScanWorkspacePdfJs();
    const pdfUrl = buildResumePdfFileUrl(safeName, context);
    const loadToken = ++scanWorkspacePdfState.renderToken;

    const empty = qs("scanWorkspacePreviewEmpty");
    const pages = qs("scanWorkspacePdfPages");
    const meta = qs("scanWorkspacePreviewMeta");

    if (pages) {
      pages.innerHTML = "";
      pages.classList.add("hidden");
    }

    if (empty) {
      empty.textContent = "Loading PDF preview...";
      empty.classList.remove("hidden");
    }

    if (meta) {
      meta.textContent = "Loading PDF preview...";
    }

    updateScanWorkspaceZoomLabel();

    const loadingTask = pdfjsLib.getDocument(pdfUrl);
    const pdfDoc = await loadingTask.promise;

    if (loadToken !== scanWorkspacePdfState.renderToken) {
      try {
        await pdfDoc.destroy();
      } catch {}
      return;
    }

    if (scanWorkspacePdfState.pdfDoc && scanWorkspacePdfState.pdfDoc !== pdfDoc) {
      try {
        await scanWorkspacePdfState.pdfDoc.destroy();
      } catch (err) {
        console.warn("Failed to destroy stale scan PDF document", err);
      }
    }

    scanWorkspacePdfState.pdfDoc = pdfDoc;
    scanWorkspacePdfState.scale = 1;
    scanWorkspacePdfState.fitScale = 1;
    scanWorkspacePdfState.isFitPage = true;

    await applyScanWorkspaceFitPageScale();
  } catch (err) {
    console.error("Failed to load scan PDF preview", err);
    await clearScanWorkspacePdfView("Failed to load PDF preview.");
  }
}

function getScanWorkspacePayload() {
  return scanWorkspaceState.preloadPayload && typeof scanWorkspaceState.preloadPayload === "object"
    ? scanWorkspaceState.preloadPayload
    : null;
}

function normalizeScanWorkspaceProfileUrl(value, expectedHost) {
  const raw = String(value || "").trim();
  if (!raw) return "";

  const candidate = /^https?:\/\//i.test(raw) ? raw : `https://${raw}`;
  let parsed = null;
  try {
    parsed = new URL(candidate);
  } catch {
    return "";
  }

  const host = parsed.hostname.toLowerCase().replace(/^www\./, "");
  const path = parsed.pathname.replace(/\/+$/, "");
  if (expectedHost === "linkedin") {
    if (host !== "linkedin.com" || !/^\/in\/[^/]+$/i.test(path)) return "";
    if (/github/i.test(path)) return "";
  } else if (expectedHost === "github") {
    if (host !== "github.com" || !/^\/[A-Za-z0-9-]+$/i.test(path)) return "";
  }

  parsed.hash = "";
  parsed.search = "";
  return parsed.toString().replace(/\/$/, "");
}

function normalizeScanWorkspacePersonalDetails(value) {
  const raw = value && typeof value === "object" ? value : {};
  const normalized = {};
  SCAN_WORKSPACE_PERSONAL_DETAIL_FIELDS.forEach((field) => {
    normalized[field] = String(raw[field] || "").trim();
  });
  normalized.state = normalized.state.toUpperCase().slice(0, 2);
  normalized.linkedin = normalizeScanWorkspaceProfileUrl(normalized.linkedin, "linkedin");
  normalized.github = normalizeScanWorkspaceProfileUrl(normalized.github, "github");
  return normalized;
}

function mergeScanWorkspacePersonalDetails(baseDetails = {}, overrideDetails = {}) {
  const base = normalizeScanWorkspacePersonalDetails(baseDetails);
  const override = normalizeScanWorkspacePersonalDetails(overrideDetails);
  const merged = { ...base };
  SCAN_WORKSPACE_PERSONAL_DETAIL_FIELDS.forEach((field) => {
    if (override[field]) merged[field] = override[field];
  });
  return normalizeScanWorkspacePersonalDetails(merged);
}

function getScanWorkspacePersonalDetailsFromPreload(payload = getScanWorkspacePayload()) {
  const envelope = payload?.personal_details && typeof payload.personal_details === "object"
    ? payload.personal_details
    : {};
  const extracted = envelope.extracted && typeof envelope.extracted === "object" ? envelope.extracted : {};
  const current = envelope.current && typeof envelope.current === "object" ? envelope.current : envelope;
  return mergeScanWorkspacePersonalDetails(extracted, current);
}

function getScanWorkspacePersonalDetailsForSave() {
  return normalizeScanWorkspacePersonalDetails(scanWorkspaceState.personalDetails || {});
}

function hasScanWorkspacePersonalDetailsValue(details) {
  return Object.values(normalizeScanWorkspacePersonalDetails(details)).some(Boolean);
}

function setScanWorkspacePersonalDetails(details = {}) {
  scanWorkspaceState.personalDetails = normalizeScanWorkspacePersonalDetails(details);
}

function setScanWorkspacePersonalDetailField(field, value) {
  const safeField = String(field || "").trim();
  if (!SCAN_WORKSPACE_PERSONAL_DETAIL_FIELDS.includes(safeField)) return;

  scanWorkspaceState.personalDetails = {
    ...normalizeScanWorkspacePersonalDetails(scanWorkspaceState.personalDetails || {}),
    [safeField]: String(value || "").trim(),
  };
  scanWorkspaceState.personalDetails = normalizeScanWorkspacePersonalDetails(
    scanWorkspaceState.personalDetails
  );
  scanWorkspaceState.previewPayload = null;

  if (window.scanWorkspacePhase1?.renderPersistenceStatus) {
    window.scanWorkspacePhase1.renderPersistenceStatus();
  }

  if (window.scanWorkspacePhase1?.renderLiveDraftPreview) {
    window.scanWorkspacePhase1.renderLiveDraftPreview();
  }
}

function getScanWorkspaceTrustedSuggestions(payload = getScanWorkspacePayload()) {
  const trusted = payload && payload.trusted_suggestions && typeof payload.trusted_suggestions === "object"
    ? payload.trusted_suggestions
    : {};

  return {
    directApplyReady: Array.isArray(trusted.direct_apply_ready) ? trusted.direct_apply_ready : [],
    directApplyOptional: Array.isArray(trusted.direct_apply_optional) ? trusted.direct_apply_optional : [],
  };
}

function getScanWorkspaceAiSuggestions(payload = getScanWorkspacePayload()) {
  return Array.isArray(payload?.ai_optimize_suggestions) ? payload.ai_optimize_suggestions : [];
}

function getScanWorkspaceGuidance(payload = getScanWorkspacePayload()) {
  return Array.isArray(payload?.directional_guidance) ? payload.directional_guidance : [];
}

function collectScanWorkspaceSelectableCandidateIds(payload = getScanWorkspacePayload()) {
  const trusted = getScanWorkspaceTrustedSuggestions(payload);
  const aiSuggestions = getScanWorkspaceAiSuggestions(payload);

  const ids = [];
  const seen = new Set();

  [
    ...trusted.directApplyReady,
    ...trusted.directApplyOptional,
    ...aiSuggestions,
  ].forEach((item) => {
    const candidateId = getTailoringReplacementCandidateId(item);
    if (!candidateId || seen.has(candidateId)) return;
    seen.add(candidateId);
    ids.push(candidateId);
  });

  return ids;
}

function normalizeScanWorkspaceSelectedCandidateIds(payload, candidateIds) {
  const validIds = new Set(collectScanWorkspaceSelectableCandidateIds(payload));
  const normalized = [];
  const seen = new Set();

  (Array.isArray(candidateIds) ? candidateIds : []).forEach((value) => {
    const candidateId = String(value || "").trim();
    if (!candidateId || seen.has(candidateId) || !validIds.has(candidateId)) return;
    seen.add(candidateId);
    normalized.push(candidateId);
  });

  return normalized;
}

function getScanWorkspaceSelectedCandidateIds() {
  return Array.isArray(scanWorkspaceState.selectedCandidateIds)
    ? scanWorkspaceState.selectedCandidateIds.slice()
    : [];
}

function getScanWorkspaceCurrentReviewDecisionMap() {
  return normalizeTailoringWorkspaceReviewDecisionMap(
    scanWorkspaceState.rewriteReviewDecisions || {}
  );
}

function normalizeScanWorkspaceExcludedIssueIds(value) {
  const seen = new Set();
  const output = [];
  (Array.isArray(value) ? value : []).forEach((item) => {
    const issueId = String(item || "").trim();
    if (!issueId || seen.has(issueId)) return;
    seen.add(issueId);
    output.push(issueId);
  });
  return output;
}

function getScanWorkspaceExcludedIssueIds() {
  return normalizeScanWorkspaceExcludedIssueIds(scanWorkspaceState.excludedScanIssueIds || []);
}

function setScanWorkspaceExcludedIssueIds(issueIds = []) {
  scanWorkspaceState.excludedScanIssueIds = normalizeScanWorkspaceExcludedIssueIds(issueIds);
  scanWorkspaceState.previewPayload = null;
}

function setScanWorkspaceIssueExcluded(issueId, excluded) {
  const safeIssueId = String(issueId || "").trim();
  if (!safeIssueId) return;

  const current = new Set(getScanWorkspaceExcludedIssueIds());
  if (excluded) {
    current.add(safeIssueId);
  } else {
    current.delete(safeIssueId);
  }

  setScanWorkspaceExcludedIssueIds(Array.from(current));
  renderScanWorkspaceView();
  if (window.scanWorkspacePhase1?.renderPersistenceStatus) {
    window.scanWorkspacePhase1.renderPersistenceStatus();
  }
}

function toggleScanWorkspaceCandidateSelection(candidateId) {
  const payload = getScanWorkspacePayload();
  if (!payload) return;

  const safeCandidateId = String(candidateId || "").trim();
  if (!safeCandidateId) return;

  const current = new Set(getScanWorkspaceSelectedCandidateIds());
  if (current.has(safeCandidateId)) {
    current.delete(safeCandidateId);
  } else {
    current.add(safeCandidateId);
  }

  scanWorkspaceState.selectedCandidateIds = normalizeScanWorkspaceSelectedCandidateIds(
    payload,
    Array.from(current)
  );

  const nextOverrides = {
    ...(scanWorkspaceState.suggestionDecisionOverrides || {}),
  };
  delete nextOverrides[safeCandidateId];
  scanWorkspaceState.suggestionDecisionOverrides = nextOverrides;

  scanWorkspaceState.previewPayload = null;
  renderScanWorkspaceView();
  syncScanWorkspaceAnnotationMarkers(scanWorkspaceState.preloadPayload);
  syncScanWorkspaceActiveCandidateToAnnotation(safeCandidateId);
  if (window.scanWorkspacePhase1?.renderLiveDraftPreview) {
    window.scanWorkspacePhase1.renderLiveDraftPreview();
  }
}

function setScanWorkspaceReviewDecision(candidateId, state, note = "") {
  const safeCandidateId = String(candidateId || "").trim();
  const safeState = String(state || "").trim().toLowerCase();
  if (!safeCandidateId || !safeState) return;

  const next = {
    ...getScanWorkspaceCurrentReviewDecisionMap(),
  };

  next[safeCandidateId] = {
    state: safeState,
    note: String(note || "").trim(),
  };

  scanWorkspaceState.rewriteReviewDecisions = next;
  scanWorkspaceState.previewPayload = null;
  renderScanWorkspaceView();
  syncScanWorkspaceAnnotationMarkers(scanWorkspaceState.preloadPayload);
  syncScanWorkspaceActiveCandidateToAnnotation(safeCandidateId);
  if (window.scanWorkspacePhase1?.renderLiveDraftPreview) {
    window.scanWorkspacePhase1.renderLiveDraftPreview();
  }
}

function buildScanWorkspaceScoreSummary() {
  return "";
}

function normalizeScanWorkspaceDisplayValue(value) {
  const text = String(value || "").trim();
  return text && text !== "-" ? text : "";
}

function firstNonEmptyScanWorkspaceValue(...values) {
  for (const value of values) {
    const normalized = normalizeScanWorkspaceDisplayValue(value);
    if (normalized) return normalized;
  }
  return "";
}

function resolveScanWorkspaceHeaderContext(payload = null) {
  const page = getScanWorkspacePage();
  const context = getScanWorkspaceContext() || {};

  const selectedJd = payload?.selected_jd_record || {};
  const jobSnapshot = payload?.job_snapshot || {};
  const job = payload?.job || {};
  const selection = payload?.selection || {};

  const company = firstNonEmptyScanWorkspaceValue(
    page?.dataset?.jobCompany,
    context.company,
    payload?.job_company,
    selectedJd.company,
    selectedJd.job_company,
    job.company,
    job.job_company,
    jobSnapshot.company,
    jobSnapshot.job_company,
    selection.company,
  );

  const title = firstNonEmptyScanWorkspaceValue(
    page?.dataset?.jobTitle,
    context.title,
    payload?.job_title,
    selectedJd.title,
    selectedJd.job_title,
    job.title,
    job.job_title,
    jobSnapshot.title,
    jobSnapshot.job_title,
    selection.title,
  );

  return {
    company: company || "-",
    title: title || "-",
  };
}

function updateScanWorkspaceContextLine(payload = getScanWorkspacePayload()) {
  const line = qs("scanWorkspaceContextLine");
  if (!line) return;

  const { company, title } = resolveScanWorkspaceHeaderContext(payload);
  line.textContent = `${company} / ${title}`;
}

function updateScanWorkspaceMeta() {
  const meta = qs("scanWorkspaceMeta");
  if (!meta) return;
  meta.textContent = "";
}

function updateScanWorkspaceActionBar() {
  // The scan page action bar is owned by scan_workspace.js.
  // planning.js only renders the left inventory rail and tab selection.
}

function renderScanWorkspaceTabs() {
  const personalTab = qs("scanWorkspacePersonalTab");
  const skillsTab = qs("scanWorkspaceTrustedTab");
  const searchabilityTab = qs("scanWorkspaceAiTab");
  const formattingTab = qs("scanWorkspaceFormattingTab");
  const recruiterTipsTab = qs("scanWorkspaceGuidanceTab");
  const payload = getScanWorkspacePayload();

  if (!personalTab || !skillsTab || !searchabilityTab || !formattingTab || !recruiterTipsTab || !payload) return;

  const taxonomy = buildScanWorkspaceTaxonomy(payload);

  personalTab.dataset.scanSelectedTab = "personal_details";
  skillsTab.dataset.scanSelectedTab = "skills";
  searchabilityTab.dataset.scanSelectedTab = "searchability";
  formattingTab.dataset.scanSelectedTab = "formatting";
  recruiterTipsTab.dataset.scanSelectedTab = "recruiter_tips";

  personalTab.classList.toggle("active", scanWorkspaceState.selectedTab === "personal_details");
  skillsTab.classList.toggle("active", scanWorkspaceState.selectedTab === "skills");
  searchabilityTab.classList.toggle("active", scanWorkspaceState.selectedTab === "searchability");
  formattingTab.classList.toggle("active", scanWorkspaceState.selectedTab === "formatting");
  recruiterTipsTab.classList.toggle("active", scanWorkspaceState.selectedTab === "recruiter_tips");

  personalTab.textContent = "Personal Details";
  skillsTab.textContent = "Skills";
  searchabilityTab.textContent = "Searchability";
  formattingTab.textContent = "Formatting";
  recruiterTipsTab.textContent = "Recruiter Tips";

  personalTab.title = "Resume header and contact details";
  skillsTab.title = `${taxonomy.skills.totalCount} skill scan item(s)`;
  searchabilityTab.title = `${taxonomy.searchability.totalCount} searchability item(s)`;
  formattingTab.title = `${taxonomy.formatting.totalCount} formatting item(s)`;
  recruiterTipsTab.title = `${taxonomy.recruiter_tips.totalCount} recruiter tip item(s)`;
}

function getScanWorkspaceIssueContract(payload = getScanWorkspacePayload()) {
  const contract = payload?.scan_issue_contract;
  return contract && typeof contract === "object" ? contract : {};
}

function getScanWorkspaceContractIssues(payload = getScanWorkspacePayload()) {
  const contract = getScanWorkspaceIssueContract(payload);
  const excluded = new Set(getScanWorkspaceExcludedIssueIds());
  return (Array.isArray(contract?.issues) ? contract.issues : []).filter((issue) => {
    const issueId = String(issue?.issue_id || "").trim();
    return !issueId || !excluded.has(issueId);
  });
}

function getScanWorkspaceRawContractIssues(payload = getScanWorkspacePayload()) {
  const contract = getScanWorkspaceIssueContract(payload);
  return Array.isArray(contract?.issues) ? contract.issues : [];
}

function getScanWorkspaceRequiredSkillWeight(payload, scoringMissingRows = []) {
  const dimensions = Array.isArray(payload?.new_scan?.dimension_scores)
    ? payload.new_scan.dimension_scores
    : [];
  const requiredDimension = dimensions.find((dimension) => {
    return String(dimension?.name || "").trim() === "required_skills_alignment";
  });
  const dimensionWeight = Number(requiredDimension?.weight);
  if (Number.isFinite(dimensionWeight) && dimensionWeight > 0) {
    return Math.max(0.05, Math.min(0.35, dimensionWeight));
  }

  const rowWeights = scoringMissingRows
    .map((issue) => Number(issue?.score_priority_weight))
    .filter((weight) => Number.isFinite(weight) && weight > 0);
  if (rowWeights.length) {
    return Math.max(0.05, Math.min(0.35, Math.max(...rowWeights)));
  }

  return 0.2;
}

function getScanWorkspaceExclusionAdjustedScore(
  payload = getScanWorkspacePayload(),
  { excludedIssueIds = getScanWorkspaceExcludedIssueIds() } = {}
) {
  const scoreSnapshot = payload?.scan_score && typeof payload.scan_score === "object"
    ? payload.scan_score
    : {};
  const rawScore = Number(scoreSnapshot.score);
  if (!Number.isFinite(rawScore)) return null;

  const baseScore = Math.max(
    0,
    Math.min(100, rawScore >= 0 && rawScore <= 1 ? rawScore * 100 : rawScore)
  );
  const issues = getScanWorkspaceRawContractIssues(payload);
  const excluded = new Set(normalizeScanWorkspaceExcludedIssueIds(excludedIssueIds));
  if (!issues.length || !excluded.size) {
    return {
      score: Math.round(baseScore),
      delta: 0,
      excludedPenaltyRows: 0,
      source: "backend",
      label: String(scoreSnapshot.label || "Optimization score"),
    };
  }

  const scoringMissingRows = issues.filter((issue) => {
    const groupId = String(issue?.group_id || "").trim();
    const bucket = String(issue?.bucket || "").trim();
    const rowType = String(issue?.row_action_type || issue?.scan_issue_type || "").trim();
    return (
      groupId === "skills" &&
      bucket === "missing" &&
      rowType !== "predicted_skill" &&
      rowType !== "other_keyword"
    );
  });
  const scoringSkillRows = issues.filter((issue) => {
    const groupId = String(issue?.group_id || "").trim();
    const bucket = String(issue?.bucket || "").trim();
    const rowType = String(issue?.row_action_type || issue?.scan_issue_type || "").trim();
    return (
      groupId === "skills" &&
      (bucket === "matched" || bucket === "missing") &&
      rowType !== "predicted_skill" &&
      rowType !== "other_keyword"
    );
  });

  const excludedPenaltyRows = scoringMissingRows.filter((issue) => {
    const issueId = String(issue?.issue_id || "").trim();
    return issueId && excluded.has(issueId);
  }).length;

  if (!scoringMissingRows.length || !excludedPenaltyRows) {
    return {
      score: Math.round(baseScore),
      delta: 0,
      excludedPenaltyRows,
      source: "backend",
      label: String(scoreSnapshot.label || "Optimization score"),
    };
  }

  const requiredSkillWeight = getScanWorkspaceRequiredSkillWeight(payload, scoringMissingRows);
  const requiredSkillPoints = requiredSkillWeight * 100;
  const totalSkillRows = Math.max(scoringSkillRows.length, scoringMissingRows.length, 1);
  const perRowLift = Math.min(3, (requiredSkillPoints / totalSkillRows) * 0.55);
  const maxExclusionLift = Math.min(8, requiredSkillPoints * 0.35);
  const lift = Math.max(
    0,
    Math.min(100 - baseScore, maxExclusionLift, perRowLift * excludedPenaltyRows)
  );
  const adjustedScore = Math.round(baseScore + lift);
  const roundedBaseScore = Math.round(baseScore);
  const delta = Math.max(0, adjustedScore - roundedBaseScore);

  return {
    score: adjustedScore,
    delta,
    excludedPenaltyRows,
    source: "exclusion_rescore_preview",
    label: `Rescored after excluding ${excludedPenaltyRows} irrelevant skill${excludedPenaltyRows === 1 ? "" : "s"}${delta ? ` (+${delta} pts)` : ""}.`,
  };
}

function hasScanWorkspaceIssueContract(payload = getScanWorkspacePayload()) {
  return getScanWorkspaceContractIssues(payload).length > 0;
}

function normalizeScanWorkspaceContractIssue(issue) {
  const raw = issue?.raw && typeof issue.raw === "object" ? issue.raw : {};
  const candidateId = String(
    issue?.candidate_id ||
    issue?.best_candidate_id ||
    raw?.replacement_candidate_id ||
    raw?.candidate_id ||
    issue?.issue_id ||
    ""
  ).trim();

  const sourceLane = String(issue?.source_lane || raw?.replacement_status || "").trim();
  const bucket = String(issue?.bucket || "").trim();
  const bucketLabel = String(issue?.bucket_label || "").trim();

  const rawFinalReplacementText = String(
    raw?.final_replacement_text ||
    raw?.patch_text ||
    ""
  ).trim();

  const issueSuggestedText = String(issue?.suggested_text || "").trim();

  const normalizedStatus = String(
    issue?.status ||
    raw?.replacement_status ||
    raw?.proposal_status ||
    ""
  ).trim();

  const normalizedPatchMethod = String(raw?.patch_generation_method || "").trim();
  const canAccept = Boolean(issue?.can_accept);

  const isExactReplacement =
    canAccept &&
    Boolean(rawFinalReplacementText) &&
    (
      normalizedStatus === "direct_apply_ready" ||
      normalizedStatus === "patch_ready" ||
      normalizedStatus === "direct_apply_optional" ||
      sourceLane === "direct_apply_ready" ||
      sourceLane === "direct_apply_optional" ||
      Boolean(normalizedPatchMethod)
    );

  return {
    ...raw,
    ...issue,
    scan_issue_id: String(issue?.issue_id || "").trim(),
    scan_issue_group_id: String(issue?.group_id || "").trim(),
    scan_issue_group_label: String(issue?.group_label || "").trim(),
    scan_issue_bucket: bucket,
    scan_issue_bucket_label: bucketLabel,
    row_action_type: String(issue?.row_action_type || issue?.scan_issue_type || "").trim(),
    row_action_label: String(issue?.row_action_label || "").trim(),
    severity: String(issue?.severity || "").trim(),
    display_term: String(issue?.display_term || "").trim(),
    canonical_term: String(issue?.canonical_term || "").trim(),
    term_family: String(issue?.term_family || "").trim(),
    skill_type: String(issue?.skill_type || "").trim(),
    skill_type_label: String(issue?.skill_type_label || "").trim(),
    score_priority_rank: Number.isFinite(Number(issue?.score_priority_rank))
      ? Number(issue.score_priority_rank)
      : 0,
    score_priority_label: String(issue?.score_priority_label || "").trim(),
    score_priority_weight: Number.isFinite(Number(issue?.score_priority_weight))
      ? Number(issue.score_priority_weight)
      : 0,
    score_priority_source: String(issue?.score_priority_source || "").trim(),
    predicted_skill: issue?.predicted_skill === true,
    prediction_source: String(issue?.prediction_source || "").trim(),
    matched_count: issue?.matched_count,
    required_count: issue?.required_count,
    coverage_label: String(issue?.coverage_label || "").trim(),
    matched_count_label: String(issue?.matched_count_label || "").trim(),
    jd_context_anchors: Array.isArray(issue?.jd_context_anchors) ? issue.jd_context_anchors : [],
    jd_context_label: String(issue?.jd_context_label || "").trim(),
    has_ai_suggestion: issue?.has_ai_suggestion === true,
    linked_candidate_ids: Array.isArray(issue?.linked_candidate_ids) ? issue.linked_candidate_ids : [],
    best_candidate_id: String(issue?.best_candidate_id || "").trim(),
    source_lane: sourceLane,
    candidate_id: candidateId,
    replacement_candidate_id: candidateId,
    replacement_status: sourceLane || String(raw?.replacement_status || "").trim(),
    original_text: String(issue?.original_text || raw?.original_text || "").trim(),
    current_text: String(issue?.current_text || issue?.original_text || raw?.current_evidence || raw?.original_text || "").trim(),
    current_evidence: String(issue?.current_text || issue?.original_text || raw?.current_evidence || raw?.original_text || "").trim(),
    suggested_text: issueSuggestedText || rawFinalReplacementText,
    final_replacement_text: isExactReplacement ? rawFinalReplacementText : "",
    rewrite_direction: String(
      raw?.rewrite_direction ||
      raw?.rewrite_instruction ||
      (!isExactReplacement ? issueSuggestedText : "")
    ).trim(),
    rewrite_instruction: String(
      raw?.rewrite_instruction ||
      raw?.rewrite_direction ||
      (!isExactReplacement ? issueSuggestedText : "")
    ).trim(),
    scan_issue_exact_replacement: isExactReplacement,
    scan_issue_render_mode: isExactReplacement ? "diff" : "guidance",
    why_selected: String(issue?.reason || raw?.why_selected || raw?.why_this_improves_match || "").trim(),
    supported_jd_signals: Array.isArray(issue?.supported_jd_signals)
      ? issue.supported_jd_signals
      : Array.isArray(raw?.supported_jd_signals)
        ? raw.supported_jd_signals
        : [],
    likely_impacted_dimensions: Array.isArray(issue?.likely_impacted_dimensions)
      ? issue.likely_impacted_dimensions
      : Array.isArray(raw?.likely_impacted_dimensions)
        ? raw.likely_impacted_dimensions
        : [],
    can_accept: canAccept,
    can_accept_all: Boolean(issue?.can_accept_all),
    can_focus_preview: issue?.can_focus_preview === true,
    anchor_strategy: String(issue?.anchor_strategy || raw?.anchor_strategy || "").trim(),
  };
}

function getScanWorkspaceNormalizedContractIssues(payload = getScanWorkspacePayload()) {
  return getScanWorkspaceContractIssues(payload)
    .map((issue) => normalizeScanWorkspaceContractIssue(issue))
    .filter((issue) => String(issue?.candidate_id || issue?.scan_issue_id || "").trim())
    .filter((issue) => issue?.is_visible_in_review !== false);
}

function buildScanWorkspacePersonalDetailsPanel() {
  return {
    key: "personal_details",
    label: "Personal Details",
    title: "Resume contact header",
    matchedCount: 0,
    missingCount: 0,
    aiCount: 0,
    totalCount: 0,
    hideCounts: true,
    groups: [],
  };
}

function buildScanWorkspaceTaxonomyFromIssueContract(payload = getScanWorkspacePayload()) {
  const contract = getScanWorkspaceIssueContract(payload);
  const issues = getScanWorkspaceNormalizedContractIssues(payload);

  const groupRows = Array.isArray(contract?.groups) ? contract.groups : [];
  const defaultGroups = [
    { group_id: "skills", label: "Skills", description: "" },
    { group_id: "searchability", label: "Searchability", description: "" },
    { group_id: "formatting", label: "Formatting", description: "" },
    { group_id: "recruiter_tips", label: "Recruiter Tips", description: "" },
  ];

  const groups = defaultGroups.map((fallbackGroup) => {
    const sourceGroup =
      groupRows.find((group) => String(group?.group_id || "").trim() === fallbackGroup.group_id) ||
      fallbackGroup;

    const groupId = String(sourceGroup?.group_id || fallbackGroup.group_id).trim();
    const groupIssues = issues.filter(
      (issue) => String(issue?.scan_issue_group_id || "").trim() === groupId
    );

    const matchedItems = groupIssues.filter((issue) => issue.scan_issue_bucket === "matched");
    const missingItems = groupIssues.filter((issue) => issue.scan_issue_bucket === "missing");
    const aiItems = groupIssues.filter((issue) => issue.scan_issue_bucket === "ai");
    const predictedItems = groupIssues.filter((issue) => issue.scan_issue_bucket === "predicted");
    const otherKeywordItems = groupIssues.filter((issue) => issue.scan_issue_bucket === "other_keyword");
    const bucketRows = Array.isArray(sourceGroup?.buckets) ? sourceGroup.buckets : [];

    const panel = {
      key: groupId,
      label: String(sourceGroup?.label || fallbackGroup.label).trim(),
      title:
        groupId === "skills"
          ? "Hard + soft skills"
          : String(sourceGroup?.label || fallbackGroup.label).trim(),
      matchedCount: matchedItems.length,
      missingCount: missingItems.length,
      aiCount: aiItems.length,
      totalCount: groupIssues.length,
      predictedCount: predictedItems.length,
      otherKeywordCount: otherKeywordItems.length,
      groups: [],
    };

    if (groupId === "skills") {
      if (otherKeywordItems.length) {
        panel.groups.push({
          title: "Other keywords",
          summary: `${otherKeywordItems.length} lower-impact domain or industry keyword(s).`,
          bucket: "other_keyword",
          items: otherKeywordItems,
        });
      }

      if (predictedItems.length) {
        panel.groups.push({
          title: "Predicted skills",
          summary: `${predictedItems.length} role-adjacent skill(s), not explicit JD requirements.`,
          bucket: "predicted",
          items: predictedItems,
        });
      }

      const skillTypeOrder = [
        { key: "hard_skill", label: "Hard skills" },
        { key: "soft_skill", label: "Soft skills" },
        { key: "other_keyword", label: "Other keywords" },
      ];
      const bucketLabelByKey = new Map(
        bucketRows.map((bucketRow) => [
          String(bucketRow?.bucket || "").trim(),
          String(bucketRow?.label || "").trim(),
        ])
      );
      const fallbackBucketLabels = {
        matched: "Matched",
        missing: "Missing / optimization opportunities",
        ai: "AI suggested",
        predicted: "Predicted skills",
        other_keyword: "Other keywords",
      };

      skillTypeOrder.forEach((skillType) => {
        const skillTypeItems = groupIssues.filter((issue) => {
          const rowSkillType = String(issue?.skill_type || "").trim() || "hard_skill";
          return rowSkillType === skillType.key;
        });
        if (!skillTypeItems.length) return;

        ["matched", "missing", "ai"].forEach((bucketKey) => {
          const bucketItems = skillTypeItems.filter((issue) => issue.scan_issue_bucket === bucketKey);
          if (!bucketItems.length) return;
          const bucketLabel = bucketLabelByKey.get(bucketKey) || fallbackBucketLabels[bucketKey] || humanizeUnderscoreLabel(bucketKey);

          panel.groups.push({
            title: `${skillType.label}: ${bucketLabel}`,
            summary: `${bucketItems.length} ${skillType.label.toLowerCase()} item(s).`,
            bucket: bucketKey,
            items: bucketItems,
          });
        });
      });

      const untypedItems = groupIssues.filter((issue) => !String(issue?.skill_type || "").trim());
      if (panel.groups.length || !untypedItems.length) {
        if (!panel.groups.length) {
          panel.groups.push({
            title: "No scan issues yet",
            summary: String(sourceGroup?.description || "No skill rows are available for this scan.").trim(),
            bucket: "missing",
            items: [],
          });
        }
        return panel;
      }
    }

    const orderedBuckets = bucketRows.length
      ? bucketRows
      : [
          { bucket: "matched", label: "Matched skills" },
          { bucket: "missing", label: "Missing / optimization opportunities" },
          { bucket: "ai", label: "AI suggested" },
        ];

    orderedBuckets.forEach((bucketRow) => {
      const bucketKey = String(bucketRow?.bucket || "").trim();
      if (!bucketKey) return;
      const bucketItems = groupIssues.filter((issue) => issue.scan_issue_bucket === bucketKey);
      if (!bucketItems.length) return;

      panel.groups.push({
        title: String(bucketRow?.label || humanizeUnderscoreLabel(bucketKey) || "Scan items").trim(),
        summary: String(bucketRow?.summary || "").trim(),
        bucket: bucketKey,
        items: bucketItems,
      });
    });

    if (!panel.groups.length) {
      panel.groups.push({
        title: "No scan issues yet",
        summary: String(sourceGroup?.description || "This scan category is reserved for the next backend pass.").trim(),
        bucket: groupId === "skills" ? "missing" : "guidance",
        items: [],
      });
    }

    return panel;
  });

  return {
    personal_details: buildScanWorkspacePersonalDetailsPanel(),
    skills: groups[0],
    searchability: groups[1],
    formatting: groups[2],
    recruiter_tips: groups[3],
  };
}

function buildScanWorkspaceTaxonomy(payload = getScanWorkspacePayload()) {
  if (hasScanWorkspaceIssueContract(payload)) {
    return buildScanWorkspaceTaxonomyFromIssueContract(payload);
  }

  const trusted = getScanWorkspaceTrustedSuggestions(payload);
  const trustedItems = [
    ...trusted.directApplyReady,
    ...trusted.directApplyOptional,
  ];

  const aiItems = getScanWorkspaceAiSuggestions(payload);
  const guidanceItems = getScanWorkspaceGuidance(payload);

  const skillsMissingItems = [
    ...aiItems,
    ...guidanceItems,
  ];

  const searchabilityItems = aiItems.length
    ? aiItems
    : trustedItems;

  const recruiterTipItems = guidanceItems.length
    ? guidanceItems
    : trustedItems;

  return {
    personal_details: buildScanWorkspacePersonalDetailsPanel(),
    skills: {
      key: "skills",
      label: "Skills",
      title: "Hard skills",
      matchedCount: trustedItems.length,
      missingCount: skillsMissingItems.length,
      aiCount: aiItems.length,
      totalCount: trustedItems.length + skillsMissingItems.length,
      groups: [
        {
          title: "Matched skills",
          summary: `${trustedItems.length} ready item(s) already backed by the resume.`,
          bucket: "trusted",
          items: trustedItems,
        },
        {
          title: "Missing / optimization opportunities",
          summary: `${skillsMissingItems.length} item(s) can improve JD signal coverage.`,
          bucket: "ai_optimize",
          items: skillsMissingItems,
        },
      ],
    },

    searchability: {
      key: "searchability",
      label: "Searchability",
      title: "Searchability",
      matchedCount: trustedItems.length,
      missingCount: aiItems.length,
      aiCount: aiItems.length,
      totalCount: searchabilityItems.length,
      groups: [
        {
          title: "Keyword placement",
          summary: "Suggestions that improve where JD language appears in the resume.",
          bucket: aiItems.length ? "ai_optimize" : "trusted",
          items: searchabilityItems,
        },
      ],
    },

    formatting: {
      key: "formatting",
      label: "Formatting",
      title: "Formatting checks",
      matchedCount: 0,
      missingCount: 0,
      aiCount: 0,
      totalCount: 0,
      groups: [
        {
          title: "ATS formatting checks",
          summary: "Text extraction, tables, columns, bullets, and symbol checks will appear after the scan contract is loaded.",
          bucket: "guidance",
          items: [],
        },
      ],
    },

    recruiter_tips: {
      key: "recruiter_tips",
      label: "Recruiter Tips",
      title: "Recruiter tips",
      matchedCount: trustedItems.length,
      missingCount: guidanceItems.length,
      aiCount: aiItems.length,
      totalCount: recruiterTipItems.length,
      groups: [
        {
          title: "Recruiter review notes",
          summary: "Items that improve clarity, salience, and review confidence.",
          bucket: guidanceItems.length ? "guidance" : "trusted",
          items: recruiterTipItems,
        },
      ],
    },
  };
}

function getScanWorkspaceActiveTaxonomyPanel(payload = getScanWorkspacePayload()) {
  const taxonomy = buildScanWorkspaceTaxonomy(payload);
  const selected = String(scanWorkspaceState.selectedTab || "").trim();

  return taxonomy[selected] || taxonomy.personal_details || taxonomy.skills;
}

function getScanWorkspaceItemsForSelectedTab(payload) {
  const panel = getScanWorkspaceActiveTaxonomyPanel(payload);

  return panel.groups.flatMap((group) =>
    Array.isArray(group.items) ? group.items : []
  );
}

function renderScanWorkspaceTaxonomySummary(panel) {
  return `
    <div class="scan-workspace-taxonomy-summary">
      <div>
        <div class="scan-workspace-taxonomy-kicker">
          ${escapeHtml(panel.label)}
        </div>

        <div class="scan-workspace-taxonomy-title">
          ${escapeHtml(panel.title)}
        </div>
      </div>

      ${
        panel.hideCounts
          ? ""
          : `
            <div class="scan-workspace-taxonomy-counts">
              <span class="scan-workspace-taxonomy-count scan-workspace-taxonomy-count--matched">
                <span class="scan-workspace-taxonomy-count-label">Matched</span>
                <span class="scan-workspace-taxonomy-count-value">${panel.matchedCount}</span>
              </span>

              <span class="scan-workspace-taxonomy-count scan-workspace-taxonomy-count--missing">
                <span class="scan-workspace-taxonomy-count-label">Missing</span>
                <span class="scan-workspace-taxonomy-count-value">${panel.missingCount}</span>
              </span>

              <span class="scan-workspace-taxonomy-count scan-workspace-taxonomy-count--ai">
                <span class="scan-workspace-taxonomy-count-label">AI</span>
                <span class="scan-workspace-taxonomy-count-value">${panel.aiCount}</span>
              </span>
            </div>
          `
      }
    </div>
  `;
}

function renderScanWorkspaceTaxonomyGroup(group) {
  const items = Array.isArray(group.items) ? group.items : [];
  const weight = items.reduce((maxWeight, item) => {
    const value = Number(item?.score_priority_weight || 0);
    return Number.isFinite(value) ? Math.max(maxWeight, value) : maxWeight;
  }, 0);
  const weightLabel = weight > 0 ? `Weight ${Math.round(weight * 100)}%` : "";

  return `
    <section class="scan-workspace-taxonomy-group">
      <div class="scan-workspace-taxonomy-group-header">
        <div class="scan-workspace-taxonomy-group-heading">
          <div class="scan-workspace-taxonomy-group-title">
            ${escapeHtml(group.title || "Scan items")}
          </div>

          ${
            weightLabel
              ? `
                <span class="scan-workspace-taxonomy-group-weight">
                  ${escapeHtml(weightLabel)}
                </span>
              `
              : ""
          }

          ${
            group.summary
              ? `
                <div class="scan-workspace-taxonomy-group-summary">
                  ${escapeHtml(group.summary)}
                </div>
              `
              : ""
          }
        </div>

        <div class="scan-workspace-taxonomy-group-count">
          ${items.length}
        </div>
      </div>

      ${renderScanWorkspaceIssueInventory(items, group.bucket || "ai_optimize")}
    </section>
  `;
}

function renderScanWorkspacePersonalDetailsPanel(panel) {
  const details = getScanWorkspacePersonalDetailsForSave();
  const stateOptions = SCAN_WORKSPACE_US_STATES.map(([value, label]) => `
    <option value="${escapeHtml(value)}" ${details.state === value ? "selected" : ""}>
      ${escapeHtml(label)}
    </option>
  `).join("");

  const input = (field, label, type = "text") => `
    <label class="scan-workspace-personal-field">
      <span>${escapeHtml(label)}</span>
      <input
        type="${escapeHtml(type)}"
        value="${escapeHtml(details[field] || "")}"
        data-scan-personal-detail="${escapeHtml(field)}"
        autocomplete="off"
      />
    </label>
  `;

  return `
    <div class="scan-workspace-taxonomy-panel scan-workspace-personal-panel">
      ${renderScanWorkspaceTaxonomySummary(panel)}

      <div class="scan-workspace-personal-grid">
        ${input("name", "Name")}
        ${input("city", "City")}

        <label class="scan-workspace-personal-field">
          <span>State</span>
          <select data-scan-personal-detail="state">
            ${stateOptions}
          </select>
        </label>

        ${input("contact", "Contact", "tel")}
        ${input("email", "Email", "email")}
        ${input("linkedin", "LinkedIn")}
        ${input("github", "GitHub")}
      </div>
    </div>
  `;
}

function renderScanWorkspaceTaxonomyPanel(panel) {
  if (panel?.key === "personal_details") {
    return renderScanWorkspacePersonalDetailsPanel(panel);
  }

  return `
    <div class="scan-workspace-taxonomy-panel">
      ${renderScanWorkspaceTaxonomySummary(panel)}

      ${panel.groups.map((group) => renderScanWorkspaceTaxonomyGroup(group)).join("")}
    </div>
  `;
}

function getScanWorkspaceIssueSignals(item) {
  const values = [
    item?.supported_jd_signals,
    item?.jd_signals,
    item?.matched_signals,
    item?.supported_signals,
  ];

  const signals = [];

  values.forEach((value) => {
    if (Array.isArray(value)) {
      value.forEach((entry) => {
        const safe = String(entry || "").trim();
        if (safe) signals.push(safe);
      });
    } else if (value && typeof value === "object") {
      Object.values(value).forEach((entry) => {
        if (Array.isArray(entry)) {
          entry.forEach((nested) => {
            const safe = String(nested || "").trim();
            if (safe) signals.push(safe);
          });
        } else {
          const safe = String(entry || "").trim();
          if (safe) signals.push(safe);
        }
      });
    } else {
      const safe = String(value || "").trim();
      if (safe) signals.push(safe);
    }
  });

  return Array.from(new Set(signals)).slice(0, 3);
}

function getScanWorkspaceIssueJdContext(item, { full = false } = {}) {
  const anchors = Array.isArray(item?.jd_context_anchors) ? item.jd_context_anchors : [];
  const anchorText = String(anchors[0]?.text || "").trim();
  const directText = String(item?.jd_context_label || "").trim();
  const text = anchorText || directText;
  if (!text) return "";
  if (full) return text;
  return text.length > 140 ? `${text.slice(0, 137)}...` : text;
}

function getScanWorkspaceIssueTitle(item, index) {
  const signals = getScanWorkspaceIssueSignals(item);
  const directTitle = String(
    item?.display_term ||
    item?.title ||
    item?.suggestion_label ||
    item?.proposal_label ||
    item?.rewrite_category ||
    item?.materiality_dimension ||
    item?.dimension ||
    ""
  ).trim();

  if (directTitle) return directTitle;
  if (signals.length) return signals[0];

  const text = String(
    item?.final_replacement_text ||
    item?.rewrite_direction ||
    item?.rewrite_instruction ||
    item?.original_text ||
    item?.current_text ||
    `Suggestion ${index + 1}`
  ).trim();

  return text.length > 52 ? `${text.slice(0, 49)}...` : text;
}

function getScanWorkspaceIssueMeta(bucket) {
  return getScanWorkspaceIssueMetaForItem(null, bucket);
}

function getScanWorkspaceIssueMetaForItem(item, bucket) {
  const rowActionType = String(item?.row_action_type || item?.scan_issue_type || "").trim();
  const rowActionLabel = String(item?.row_action_label || "").trim();
  const groupId = String(item?.scan_issue_group_id || item?.group_id || "").trim();
  const isDeterministicCheckGroup = ["searchability", "formatting", "recruiter_tips"].includes(groupId);
  if (rowActionType === "direct_replacement") return "AI Suggested";
  if (rowActionType === "phrase_generation") return "Phrase";
  if (rowActionType === "manual_guidance") return "Manual edit";
  if (rowActionType === "predicted_skill" || bucket === "predicted") return "Predicted";
  if (rowActionType === "other_keyword" || bucket === "other_keyword") return "";
  if (rowActionLabel && rowActionType !== "matched") return rowActionLabel;
  if (rowActionType === "guidance" && item?.has_ai_suggestion === true) return "AI guidance";
  if (rowActionType === "matched" && isDeterministicCheckGroup) return "Check";
  if (rowActionType === "matched" && groupId === "skills") return "";
  if (rowActionType === "matched") return "Backed";
  if (rowActionType === "guidance") return "Manual edit";
  if (bucket === "matched") return isDeterministicCheckGroup ? "Check" : "Backed";
  if (bucket === "missing") return "Manual edit";
  if (bucket === "predicted") return "Predicted";
  if (bucket === "other_keyword") return "Keyword";
  if (bucket === "ai") return "AI Suggested";
  if (bucket === "ai_optimize") return "AI replacement";
  if (bucket === "trusted") return "Ready";
  if (bucket === "guidance") return "Manual edit";
  return "Review";
}

function getScanWorkspaceIssueCountLabel(bucket) {
  if (bucket === "matched" || bucket === "trusted") return "Done";
  if (bucket === "missing" || bucket === "guidance") return "Open";
  return "Review";
}

function getScanWorkspaceIssueCoverageLabel(item) {
  const groupId = String(item?.scan_issue_group_id || item?.group_id || "").trim();
  const rowActionType = String(item?.row_action_type || item?.scan_issue_type || "").trim();
  if (
    rowActionType === "matched" &&
    ["searchability", "formatting", "recruiter_tips"].includes(groupId)
  ) {
    return "Pass";
  }

  const matchedLabel = String(item?.matched_count_label || "").trim();
  if (matchedLabel) return matchedLabel;

  const direct = String(item?.coverage_label || "").trim();
  if (direct) return direct;

  const matched = Number(item?.matched_count);
  const required = Number(item?.required_count);
  if (Number.isFinite(matched) && Number.isFinite(required) && required > 0) {
    return `${Math.max(0, Math.round(matched))}/${Math.max(1, Math.round(required))}`;
  }

  return "";
}

function coerceScanWorkspaceScorePoints(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return null;
  return Math.round(numeric >= -1 && numeric <= 1 ? numeric * 100 : numeric);
}

function getScanWorkspaceIssueScoreImpact(item) {
  const directPoints = coerceScanWorkspaceScorePoints(item?.projected_score_delta_points);
  if (directPoints !== null) return directPoints;
  return coerceScanWorkspaceScorePoints(item?.projected_overall_delta);
}

function compareScanWorkspaceIssuePriority(left, right) {
  const leftRank = Number(left?.score_priority_rank || 0);
  const rightRank = Number(right?.score_priority_rank || 0);
  const leftEffectiveRank = leftRank > 0 ? leftRank : 99;
  const rightEffectiveRank = rightRank > 0 ? rightRank : 99;
  if (leftEffectiveRank !== rightEffectiveRank) return leftEffectiveRank - rightEffectiveRank;

  const leftWeight = Number(left?.score_priority_weight || 0);
  const rightWeight = Number(right?.score_priority_weight || 0);
  if (leftWeight !== rightWeight) return rightWeight - leftWeight;

  const leftImpact = getScanWorkspaceIssueScoreImpact(left);
  const rightImpact = getScanWorkspaceIssueScoreImpact(right);
  if ((leftImpact || 0) !== (rightImpact || 0)) return (rightImpact || 0) - (leftImpact || 0);

  const leftTitle = getScanWorkspaceIssueTitle(left, 0).toLowerCase();
  const rightTitle = getScanWorkspaceIssueTitle(right, 0).toLowerCase();
  return leftTitle.localeCompare(rightTitle);
}

function getScanWorkspaceIssueRightLabel(item, bucket) {
  const scoreImpact = getScanWorkspaceIssueScoreImpact(item);
  const rowActionType = String(item?.row_action_type || item?.scan_issue_type || "").trim();
  const rowActionLabel = String(item?.row_action_label || "").trim();

  if (scoreImpact !== null && rowActionType === "direct_replacement") {
    if (scoreImpact > 0) return `+${scoreImpact}`;
    if (scoreImpact < 0) return `${scoreImpact}`;
    return "0";
  }

  if (rowActionType === "phrase_generation") return rowActionLabel || "Phrase";
  if (rowActionType === "manual_guidance") return "";
  if (rowActionType === "predicted_skill" || bucket === "predicted") return "";
  if (rowActionType === "other_keyword" || bucket === "other_keyword") return "Keyword";

  const coverage = getScanWorkspaceIssueCoverageLabel(item);
  if (coverage) return coverage;

  return getScanWorkspaceIssueCountLabel(bucket);
}

function getScanWorkspaceIssueScoreTitle(item) {
  const jdContext = getScanWorkspaceIssueJdContext(item, { full: true });
  return jdContext ? `JD: ${jdContext}` : "";
}

function getScanWorkspaceIssueToneClass(bucket) {
  return getScanWorkspaceIssueToneClassForItem(null, bucket);
}

function getScanWorkspaceIssueToneClassForItem(item, bucket) {
  const rowActionType = String(item?.row_action_type || item?.scan_issue_type || "").trim();
  if (rowActionType === "matched") return "is-matched";
  if (rowActionType === "direct_replacement") return "is-ai";
  if (rowActionType === "predicted_skill" || bucket === "predicted") return "is-predicted";
  if (rowActionType === "other_keyword" || bucket === "other_keyword") return "is-other-keyword";
  if (rowActionType === "phrase_generation" || rowActionType === "manual_guidance") return "is-missing";
  if (bucket === "matched" || bucket === "trusted") return "is-matched";
  if (bucket === "ai" || bucket === "ai_optimize") return "is-ai";
  return "is-missing";
}

function getScanWorkspaceCriticDecisionLabel(value) {
  const safeValue = String(value || "").trim();
  if (!safeValue) return "";
  if (safeValue === "downgrade_to_guidance") return "Guidance";
  return humanizeUnderscoreLabel(safeValue, "").replace(/^\w/, (char) => char.toUpperCase());
}

function getScanWorkspaceCriticTone(value) {
  const safeValue = String(value || "").trim();
  if (safeValue === "approve") return "approve";
  if (safeValue === "reject") return "reject";
  if (safeValue === "downgrade_to_guidance") return "guidance";
  return "neutral";
}

function hasScanWorkspaceCriticAdvisory(item) {
  return Boolean(item?.critic_advisory_only && String(item?.critic_decision || "").trim());
}

function formatScanWorkspaceCriticConfidence(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return "";
  const percent = numeric <= 1 ? numeric * 100 : numeric;
  return `${Math.round(percent)}%`;
}

function formatScanWorkspaceCriticScoreDelta(value) {
  if (value === null || value === undefined || String(value).trim() === "") return "";
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return "";
  const normalized = Math.abs(numeric) <= 1 ? numeric * 100 : numeric;
  const prefix = normalized > 0 ? "+" : "";
  return `${prefix}${normalized.toFixed(1)} pts`;
}

function renderScanWorkspaceCriticAdvisorySummary(item) {
  if (!hasScanWorkspaceCriticAdvisory(item)) return "";

  const decision = String(item.critic_decision || "").trim();
  const decisionLabel = getScanWorkspaceCriticDecisionLabel(decision);
  const tone = getScanWorkspaceCriticTone(decision);
  const reasonCodes = Array.isArray(item.critic_reason_codes)
    ? item.critic_reason_codes.map((value) => String(value || "").trim()).filter(Boolean)
    : [];
  const confidence = formatScanWorkspaceCriticConfidence(item.critic_confidence);

  return `
    <span class="scan-workspace-critic-mini scan-workspace-critic-mini--${escapeHtml(tone)}">
      <span class="scan-workspace-critic-mini-label">Critic</span>
      <span class="scan-workspace-critic-mini-decision">${escapeHtml(decisionLabel)}</span>
      ${confidence ? `<span class="scan-workspace-critic-mini-confidence">${escapeHtml(confidence)}</span>` : ""}
      ${reasonCodes.length ? `
        <span class="scan-workspace-critic-mini-reasons">
          ${reasonCodes.slice(0, 2).map((code) => escapeHtml(humanizeUnderscoreLabel(code, ""))).join(" · ")}
        </span>
      ` : ""}
    </span>
  `;
}

function renderScanWorkspaceCriticAdvisoryDetails(item) {
  if (!hasScanWorkspaceCriticAdvisory(item)) return "";

  const decision = String(item.critic_decision || "").trim();
  const tone = getScanWorkspaceCriticTone(decision);
  const decisionLabel = getScanWorkspaceCriticDecisionLabel(decision);
  const confidence = formatScanWorkspaceCriticConfidence(item.critic_confidence);
  const scoreDelta = formatScanWorkspaceCriticScoreDelta(item.critic_score_delta);
  const reasonCodes = Array.isArray(item.critic_reason_codes)
    ? item.critic_reason_codes.map((value) => String(value || "").trim()).filter(Boolean)
    : [];
  const evidenceSpans = Array.isArray(item.critic_evidence_spans)
    ? item.critic_evidence_spans.map((value) => String(value || "").trim()).filter(Boolean)
    : [];
  const notes = String(item.critic_notes || "").trim();

  return `
    <div class="scan-workspace-critic-card scan-workspace-critic-card--${escapeHtml(tone)}">
      <div class="scan-workspace-critic-card-header">
        <span class="scan-workspace-critic-card-kicker">Critic advisory</span>
        <span class="scan-workspace-critic-card-badge">${escapeHtml(decisionLabel)}</span>
        ${confidence ? `<span class="scan-workspace-critic-card-meta">${escapeHtml(confidence)}</span>` : ""}
        ${scoreDelta ? `<span class="scan-workspace-critic-card-meta">${escapeHtml(scoreDelta)}</span>` : ""}
      </div>
      ${reasonCodes.length ? `
        <div class="scan-workspace-critic-reasons">
          ${reasonCodes.map((code) => `
            <span class="scan-workspace-critic-reason">${escapeHtml(humanizeUnderscoreLabel(code, ""))}</span>
          `).join("")}
        </div>
      ` : ""}
      ${notes ? `<div class="scan-workspace-critic-notes">${escapeHtml(notes)}</div>` : ""}
      ${evidenceSpans.length ? `
        <div class="scan-workspace-critic-evidence">
          ${evidenceSpans.slice(0, 2).map((span) => `
            <span>${escapeHtml(span)}</span>
          `).join("")}
        </div>
      ` : ""}
    </div>
  `;
}

function isScanWorkspaceIssueExcludable(item) {
  const groupId = String(item?.scan_issue_group_id || item?.group_id || "").trim();
  const issueId = String(item?.scan_issue_id || item?.issue_id || "").trim();
  const bucket = String(item?.scan_issue_bucket || item?.bucket || "").trim();
  const rowActionType = String(item?.row_action_type || item?.scan_issue_type || "").trim();

  return (
    groupId === "skills" &&
    Boolean(issueId) &&
    bucket === "missing" &&
    rowActionType !== "direct_replacement" &&
    rowActionType !== "predicted_skill" &&
    rowActionType !== "other_keyword" &&
    rowActionType !== "matched"
  );
}

function renderScanWorkspaceIssueInventory(items, bucket) {
  const safeItems = Array.isArray(items)
    ? items.slice().sort(compareScanWorkspaceIssuePriority)
    : [];

  if (!safeItems.length) {
    return `
      <div class="tailoring-empty-state">
        No scan items in this category.
      </div>
    `;
  }

  const activeCandidateId = String(scanWorkspaceState.activeCandidateId || "").trim();

  return `
    <div class="scan-workspace-issue-list">
      ${safeItems
        .map((item, index) => {
          const candidateId = getTailoringReplacementCandidateId(item);
          const scanIssueId = String(item?.scan_issue_id || item?.issue_id || "").trim();
          const rowId = candidateId || scanIssueId;
          if (!rowId) return "";

          const isAnchorable = isScanWorkspacePreviewAnchorableItem(item);
          const isActive = isAnchorable && candidateId === activeCandidateId;
          const title = getScanWorkspaceIssueTitle(item, index);
          const signals = getScanWorkspaceIssueSignals(item);
          const jdContext = getScanWorkspaceIssueJdContext(item);
          const meta = getScanWorkspaceIssueMetaForItem(item, bucket);
          const countLabel = getScanWorkspaceIssueRightLabel(item, bucket);
          const visibleCountLabel = meta && countLabel && meta.toLowerCase() === countLabel.toLowerCase()
            ? ""
            : countLabel;
          const toneClass = getScanWorkspaceIssueToneClassForItem(item, bucket);
          const scoreTitle = getScanWorkspaceIssueScoreTitle(item);
          const scoreImpact = getScanWorkspaceIssueScoreImpact(item);
          const isScoreBubble =
            scoreImpact !== null &&
            item?.row_action_type === "direct_replacement";
          const hasAiBadge = item?.has_ai_suggestion === true || item?.row_action_type === "direct_replacement";
          const showFlagIcon =
            item?.row_action_type === "matched" ||
            bucket === "matched";
          const canExclude = isScanWorkspaceIssueExcludable(item);
          const tokenClass = (value) => String(value || "review")
            .trim()
            .toLowerCase()
            .replace(/[^a-z0-9]+/g, "-")
            .replace(/^-+|-+$/g, "") || "review";
          const metaIcon = hasAiBadge ? "✦" : "";
          const countIcon = !metaIcon && showFlagIcon ? "⚑" : "";
          const shouldShowStandaloneIcon = (hasAiBadge || showFlagIcon) && !meta && !visibleCountLabel;
          const shouldRenderMetaIconOutside = Boolean(metaIcon && meta);
          const criticSummaryHtml = renderScanWorkspaceCriticAdvisorySummary(item);

          return `
            <button
              type="button"
              class="scan-workspace-issue-row ${toneClass} ${isActive ? "is-active" : ""} ${isAnchorable ? "" : "is-static"}"
              ${isAnchorable ? `data-scan-focus-candidate="${escapeHtml(candidateId)}"` : `data-scan-static-issue="${escapeHtml(rowId)}"`}
              ${scoreTitle ? `title="${escapeHtml(scoreTitle)}"` : ""}
            >
              <span class="scan-workspace-issue-status" aria-hidden="true"></span>

              <span class="scan-workspace-issue-main">
                <span class="scan-workspace-issue-title">
                  ${escapeHtml(title)}
                </span>

                ${
                  signals.length
                    ? `
                      <span class="scan-workspace-issue-signals">
                        ${signals.map((signal) => escapeHtml(signal)).join(" · ")}
                      </span>
                    `
                    : ""
                }

                ${
                  jdContext
                    ? `
                      <span class="scan-workspace-issue-jd-context">
                        JD: ${escapeHtml(jdContext)}
                      </span>
                    `
                    : ""
                }
              </span>

              <span class="scan-workspace-issue-right">
                ${
                  canExclude
                    ? `
                      <span
                        role="button"
                        tabindex="0"
                        class="scan-workspace-issue-exclude-btn"
                        data-scan-exclude-issue="${escapeHtml(scanIssueId)}"
                        title="Exclude this missing skill from scan report counts"
                      >
                        Exclude
                      </span>
                    `
                    : ""
                }

                ${
                  shouldShowStandaloneIcon
                    ? `<span class="scan-workspace-issue-token-icon">${hasAiBadge ? "✦" : "⚑"}</span>`
                      : ""
                }

                ${
                  meta
                    ? `
                      <span class="scan-workspace-issue-token-wrap">
                        ${shouldRenderMetaIconOutside ? `<span class="scan-workspace-issue-token-icon scan-workspace-issue-token-icon--outside">${metaIcon}</span>` : ""}
                        <span class="scan-workspace-issue-meta scan-workspace-issue-pill--${escapeHtml(tokenClass(meta))}">
                          ${escapeHtml(meta)}
                        </span>
                      </span>
                    `
                    : ""
                }

                ${criticSummaryHtml}

                ${
                  visibleCountLabel
                    ? `
                      <span class="scan-workspace-issue-count scan-workspace-issue-pill--${escapeHtml(tokenClass(visibleCountLabel))} ${isScoreBubble ? "scan-workspace-issue-count--score" : ""} ${isScoreBubble && scoreImpact > 0 ? "is-positive" : ""} ${isScoreBubble && scoreImpact < 0 ? "is-negative" : ""}">
                        ${countIcon ? `<span class="scan-workspace-issue-token-icon">${countIcon}</span>` : ""}
                        ${escapeHtml(visibleCountLabel)}
                      </span>
                    `
                    : ""
                }
              </span>
            </button>
          `;
        })
        .join("")}
    </div>
  `;
}

function getScanWorkspaceReplacementSuggestions(payload = getScanWorkspacePayload()) {
  if (hasScanWorkspaceIssueContract(payload)) {
    return getScanWorkspaceNormalizedContractIssues(payload);
  }

  const trusted = getScanWorkspaceTrustedSuggestions(payload);

  return [
    ...trusted.directApplyReady,
    ...trusted.directApplyOptional,
    ...getScanWorkspaceAiSuggestions(payload),
    ...getScanWorkspaceGuidance(payload),
  ];
}

function isScanWorkspacePreviewAnchorableItem(item) {
  const candidateId = String(
    item?.best_candidate_id ||
    item?.replacement_candidate_id ||
    item?.candidate_id ||
    item?.scan_issue_id ||
    ""
  ).trim();

  const originalText = String(
    item?.current_text ||
    item?.original_text ||
    item?.source_bullet_text ||
    item?.bullet_text ||
    item?.current_evidence ||
    ""
  ).trim();

  const suggestedText = String(
    item?.final_replacement_text ||
    item?.suggested_text ||
    item?.rewrite_direction ||
    item?.rewrite_instruction ||
    ""
  ).trim();

  if (item?.can_focus_preview === false) return false;
  if (!candidateId) return false;

  return Boolean(originalText || suggestedText);
}

function getScanWorkspaceAnchorableReplacementSuggestions(payload = getScanWorkspacePayload()) {
  return getScanWorkspaceReplacementSuggestions(payload).filter((item) =>
    isScanWorkspacePreviewAnchorableItem(item)
  );
}

function buildScanWorkspaceAnnotationMarkerCopy(item) {
  const originalText = String(
    item?.current_text ||
    item?.original_text ||
    item?.source_bullet_text ||
    item?.bullet_text ||
    ""
  ).trim();

  const suggestedText = String(
    item?.final_replacement_text ||
    item?.rewrite_direction ||
    item?.rewrite_instruction ||
    ""
  ).trim();

  const reasonText = String(
    item?.why_selected ||
    item?.materiality_reason ||
    item?.rewrite_instruction ||
    item?.direction_only_reason ||
    ""
  ).trim();

  return [
    suggestedText ? `Suggestion: ${suggestedText}` : "",
    originalText ? `Original: ${originalText}` : "",
    reasonText ? `Reason: ${reasonText}` : "",
  ]
    .filter(Boolean)
    .join("\n\n");
}

function isScanWorkspaceReplacementLikeSuggestion(item) {
  const sourceLane = String(item?.source_lane || item?.replacement_status || "").trim();
  const actionType = String(item?.row_action_type || item?.scan_issue_type || item?.action_type || "").trim();
  const originalText = String(
    item?.current_text ||
    item?.original_text ||
    item?.source_bullet_text ||
    item?.bullet_text ||
    item?.current_evidence ||
    ""
  ).trim();
  const suggestedText = String(
    item?.final_replacement_text ||
    item?.suggested_text ||
    item?.rewrite_direction ||
    item?.rewrite_instruction ||
    ""
  ).trim();

  if (!originalText || !suggestedText) return false;
  if (item?.scan_issue_exact_replacement === true || item?.scan_issue_render_mode === "diff") return true;

  return (
    sourceLane === "direct_apply_ready" ||
    sourceLane === "direct_apply_optional" ||
    sourceLane === "ai_optimize_optional" ||
    actionType === "direct_replacement" ||
    actionType === "review_replacement" ||
    actionType === "replacement"
  );
}

function buildScanWorkspaceAnnotationMarkersFromPayload(payload) {
  return getScanWorkspaceAnchorableReplacementSuggestions(payload)
    .map((item, index) => {
      const candidateId = getTailoringReplacementCandidateId(item);
      if (!candidateId) return null;

      const originalText = String(
        item?.current_text ||
        item?.original_text ||
        item?.source_bullet_text ||
        item?.bullet_text ||
        item?.current_evidence ||
        ""
      ).trim();

      const suggestedText = String(
        item?.final_replacement_text ||
        item?.suggested_text ||
        item?.rewrite_direction ||
        item?.rewrite_instruction ||
        ""
      ).trim();

      const reasonText = String(
        item?.why_selected ||
        item?.reason ||
        item?.materiality_reason ||
        item?.rewrite_instruction ||
        item?.direction_only_reason ||
        ""
      ).trim();

      const title = String(
        item?.title ||
        item?.suggestion_label ||
        item?.proposal_label ||
        item?.final_replacement_text ||
        item?.suggested_text ||
        item?.rewrite_direction ||
        `Scan suggestion ${index + 1}`
      ).trim();

      const isExactReplacement = isScanWorkspaceReplacementLikeSuggestion(item);

      const topPercent = Math.min(86, 20 + index * 8);

      return {
        id: `scan_marker_${candidateId}`,
        tone:
          item?.scan_issue_bucket === "missing" ||
          item?.replacement_status === "ai_optimize_optional"
            ? "replace"
            : "focus",
        title,
        copy: buildScanWorkspaceAnnotationMarkerCopy(item),
        topPercent,
        leftPercent: 88,
        previewRowIndex: index,
        candidateIds: [candidateId],
        bulletKey: `candidate:${candidateId}`,
        originalText,
        suggestedText,
        reasonText,
        supportedTerms: Array.isArray(item?.supported_jd_signals)
          ? item.supported_jd_signals
          : [],
        canFocusPreview: item?.can_focus_preview !== false,
        anchorStrategy: String(item?.anchor_strategy || "replacement_candidate").trim(),
        anchorText: originalText || suggestedText,
        isExactReplacement,
        renderMode: isExactReplacement ? "diff" : "guidance",
        sourceLabel:
          item?.scan_issue_bucket_label ||
          (item?.scan_issue_bucket === "ai" ||
          item?.replacement_status === "ai_optimize_optional"
            ? "AI suggested"
            : item?.scan_issue_bucket === "missing"
              ? "Optimization opportunity"
              : "Trusted suggestion"),
      };
    })
    .filter(Boolean);
}

function getScanWorkspaceAnnotationMarkerSignature(markers) {
  return JSON.stringify(
    (Array.isArray(markers) ? markers : []).map((marker) => ({
      id: marker.id,
      tone: marker.tone,
      title: marker.title,
      topPercent: marker.topPercent,
      leftPercent: marker.leftPercent,
      previewRowIndex: marker.previewRowIndex,
      candidateIds: marker.candidateIds,
      originalText: marker.originalText,
      suggestedText: marker.suggestedText,
      reasonText: marker.reasonText,
      supportedTerms: marker.supportedTerms,
      bulletKey: marker.bulletKey,
      sourceLabel: marker.sourceLabel,
      canFocusPreview: marker.canFocusPreview,
      anchorStrategy: marker.anchorStrategy,
      anchorText: marker.anchorText,
      isExactReplacement: marker.isExactReplacement,
      renderMode: marker.renderMode,
    }))
  );
}

function updateScanWorkspaceHeaderCounts(payload = getScanWorkspacePayload()) {
  const taxonomy = buildScanWorkspaceTaxonomy(payload);
  const skillsPanel = taxonomy.skills;
  const scoreSnapshot = payload?.scan_score && typeof payload.scan_score === "object"
    ? payload.scan_score
    : {};
  const adjustedScore = getScanWorkspaceExclusionAdjustedScore(payload, {
    excludedIssueIds: getScanWorkspaceExcludedIssueIds(),
  });

  const matchedCount = skillsPanel.matchedCount;
  const aiCount = skillsPanel.aiCount;
  const missingCount = skillsPanel.missingCount;

  const scoreNode = qs("scanWorkspaceScoreValue");
  const matchedCountNode = qs("scanWorkspaceTrustedCount");
  const aiCountNode = qs("scanWorkspaceAiCount");
  const missingCountNode = qs("scanWorkspaceGuidanceCount");

  if (scoreNode && adjustedScore) {
    scoreNode.textContent = String(adjustedScore.score);
    scoreNode.dataset.scanScoreSource = adjustedScore.source;
    scoreNode.setAttribute(
      "aria-label",
      adjustedScore.delta
        ? `${adjustedScore.label}. Score changed by +${adjustedScore.delta} points.`
        : adjustedScore.label
    );
  }

  if (matchedCountNode) {
    matchedCountNode.textContent = String(matchedCount);
    const label = matchedCountNode
      .closest(".scan-workspace-review-inline-metric")
      ?.querySelector(".scan-workspace-review-inline-metric-label");
    if (label) label.textContent = "Matched";
  }

  if (aiCountNode) {
    aiCountNode.textContent = String(aiCount);
    const label = aiCountNode
      .closest(".scan-workspace-review-inline-metric")
      ?.querySelector(".scan-workspace-review-inline-metric-label");
    if (label) label.textContent = "AI";
  }

  if (missingCountNode) {
    missingCountNode.textContent = String(missingCount);
    const label = missingCountNode
      .closest(".scan-workspace-review-inline-metric")
      ?.querySelector(".scan-workspace-review-inline-metric-label");
    if (label) label.textContent = "Missing";
  }
}

function syncScanWorkspaceAnnotationMarkers(payload = getScanWorkspacePayload()) {
  updateScanWorkspaceHeaderCounts(payload);

  if (!window.scanWorkspacePhase1?.setAnnotationMarkers) return;

  if (!payload) {
    if (scanWorkspaceState.annotationMarkerSignature !== "[]") {
      scanWorkspaceState.annotationMarkerSignature = "[]";
      window.scanWorkspacePhase1.setAnnotationMarkers([]);
    }
    return;
  }

  const markers = buildScanWorkspaceAnnotationMarkersFromPayload(payload);
  const markerSignature = getScanWorkspaceAnnotationMarkerSignature(markers);

  if (markerSignature !== scanWorkspaceState.annotationMarkerSignature) {
    scanWorkspaceState.annotationMarkerSignature = markerSignature;
    if (window.scanWorkspacePhase1?.setAnnotationMarkers) {
      window.scanWorkspacePhase1.setAnnotationMarkers(markers);
    }
  }

  const activeCandidateId = String(scanWorkspaceState.activeCandidateId || "").trim();
  if (activeCandidateId && window.scanWorkspacePhase1?.focusCandidateId) {
    window.scanWorkspacePhase1.focusCandidateId(activeCandidateId);
  }
}

function syncScanWorkspaceActiveCandidateToAnnotation(candidateId) {
  const safeCandidateId = String(candidateId || "").trim();
  if (!safeCandidateId || !window.scanWorkspacePhase1?.focusCandidateId) return;

  window.scanWorkspacePhase1.focusCandidateId(safeCandidateId);
}

function findScanWorkspaceCandidateById(candidateId, payload = getScanWorkspacePayload()) {
  const safeCandidateId = String(candidateId || "").trim();
  if (!safeCandidateId || !payload) return null;

  const trusted = getScanWorkspaceTrustedSuggestions(payload);

  const groups = [
    {
      tab: "trusted",
      lane: "direct_apply_ready",
      label: "Trusted suggestion",
      eligibleForDecision: false,
      items: trusted.directApplyReady,
    },
    {
      tab: "trusted",
      lane: "direct_apply_optional",
      label: "Trusted optional",
      eligibleForDecision: false,
      items: trusted.directApplyOptional,
    },
    {
      tab: "ai_optimize",
      lane: "ai_optimize_optional",
      label: "AI suggestion",
      eligibleForDecision: true,
      items: getScanWorkspaceAiSuggestions(payload),
    },
    {
      tab: "guidance",
      lane: "direction_only",
      label: "Guidance",
      eligibleForDecision: false,
      items: getScanWorkspaceGuidance(payload),
    },
  ];

  for (const group of groups) {
    const item = group.items.find(
      (candidate) => getTailoringReplacementCandidateId(candidate) === safeCandidateId
    );

    if (item) {
      return {
        ...group,
        candidateId: safeCandidateId,
        item,
      };
    }
  }

  return null;
}

function getScanWorkspaceCandidateOriginalText(item) {
  return String(
    item?.current_text ||
    item?.original_text ||
    item?.source_bullet_text ||
    item?.bullet_text ||
    ""
  ).trim();
}

function getScanWorkspaceCandidateSuggestedText(item) {
  return String(
    item?.final_replacement_text ||
    item?.rewrite_direction ||
    item?.rewrite_instruction ||
    item?.why_selected ||
    ""
  ).trim();
}

function getScanWorkspaceCandidateReasonText(item) {
  return String(
    item?.why_selected ||
    item?.materiality_reason ||
    item?.why_not_material ||
    item?.direction_only_reason ||
    item?.rewrite_instruction ||
    ""
  ).trim();
}

function getScanWorkspaceCandidateSummaryText(item) {
  return String(
    item?.final_replacement_text ||
    item?.rewrite_direction ||
    item?.rewrite_instruction ||
    item?.why_selected ||
    item?.original_text ||
    item?.current_text ||
    "Selected scan item"
  ).trim();
}

function getScanWorkspaceCandidateDecisionState(candidateId) {
  const safeCandidateId = String(candidateId || "").trim();
  if (!safeCandidateId) return "pending";

  if (getScanWorkspaceSelectedCandidateIds().includes(safeCandidateId)) {
    return "accepted";
  }

  const override = String(
    scanWorkspaceState.suggestionDecisionOverrides?.[safeCandidateId] || ""
  ).trim().toLowerCase();

  return override === "rejected" ? "rejected" : "pending";
}

function setScanWorkspaceSuggestionDecision(candidateId, action) {
  const safeCandidateId = String(candidateId || "").trim();
  const safeAction = String(action || "").trim().toLowerCase();
  if (!safeCandidateId || !safeAction) return;

  const payload = getScanWorkspacePayload();
  const found = findScanWorkspaceCandidateById(safeCandidateId, payload);
  if (!found || !found.eligibleForDecision) return;

  const current = new Set(getScanWorkspaceSelectedCandidateIds());
  const nextOverrides = {
    ...(scanWorkspaceState.suggestionDecisionOverrides || {}),
  };

  if (safeAction === "accept") {
    current.add(safeCandidateId);
    delete nextOverrides[safeCandidateId];
  } else if (safeAction === "reject") {
    current.delete(safeCandidateId);
    nextOverrides[safeCandidateId] = "rejected";
  } else if (safeAction === "reset") {
    current.delete(safeCandidateId);
    delete nextOverrides[safeCandidateId];
  } else {
    return;
  }

  scanWorkspaceState.selectedCandidateIds = normalizeScanWorkspaceSelectedCandidateIds(
    payload,
    Array.from(current)
  );
  scanWorkspaceState.suggestionDecisionOverrides = nextOverrides;
  scanWorkspaceState.previewPayload = null;

  renderScanWorkspaceView();
  syncScanWorkspaceAnnotationMarkers(scanWorkspaceState.preloadPayload);
  syncScanWorkspaceActiveCandidateToAnnotation(safeCandidateId);
  if (window.scanWorkspacePhase1?.renderLiveDraftPreview) {
    window.scanWorkspacePhase1.renderLiveDraftPreview();
  }
}

function renderScanWorkspaceActiveInspector(payload = getScanWorkspacePayload()) {
  // Keep active rail focus local to the left inventory.
  // The right-side resume mirror, annotation popover, and scan decisions are owned by scan_workspace.js.
}

function ensureScanWorkspaceActiveCandidate(payload) {
  const items = getScanWorkspaceItemsForSelectedTab(payload);
  const candidateIds = items
    .map((item) => getTailoringReplacementCandidateId(item))
    .filter(Boolean);

  if (!candidateIds.length) {
    scanWorkspaceState.activeCandidateId = "";
    return "";
  }

  if (!candidateIds.includes(scanWorkspaceState.activeCandidateId)) {
    scanWorkspaceState.activeCandidateId = candidateIds[0];
  }

  return scanWorkspaceState.activeCandidateId;
}

function setScanWorkspaceActiveCandidate(candidateId) {
  const nextId = String(candidateId || "").trim();
  if (!nextId) return;

  if (scanWorkspaceState.activeCandidateId === nextId) {
    syncScanWorkspaceActiveCandidateToAnnotation(nextId);
    return;
  }

  scanWorkspaceState.activeCandidateId = nextId;
  renderScanWorkspaceView();
  syncScanWorkspaceActiveCandidateToAnnotation(nextId);
}

function renderScanWorkspaceView() {
  const payload = getScanWorkspacePayload();
  const root = qs("scanWorkspaceInteractiveSummary");
  if (!root) return;

  if (!payload) {
    root.innerHTML = `
      <div class="tailoring-empty-state">
        No preloaded scan payload is available for this route.
      </div>
    `;
    updateScanWorkspaceMeta();
    updateScanWorkspaceActionBar();
    if (typeof renderScanWorkspaceJdLlmReadback === "function") {
      renderScanWorkspaceJdLlmReadback();
    }
    syncScanWorkspaceAnnotationMarkers(null);
    return;
  }

  ensureScanWorkspaceActiveCandidate(payload);

  const trusted = getScanWorkspaceTrustedSuggestions(payload);
  const aiSuggestions = getScanWorkspaceAiSuggestions(payload);
  const guidance = getScanWorkspaceGuidance(payload);
  const selectedIds = getScanWorkspaceSelectedCandidateIds();
  const reviewDecisionMap = getScanWorkspaceCurrentReviewDecisionMap();

  const activePanel = getScanWorkspaceActiveTaxonomyPanel(payload);
  root.innerHTML = renderScanWorkspaceTaxonomyPanel(activePanel);

  renderScanWorkspaceTabs();
  updateScanWorkspaceMeta();
  updateScanWorkspaceActionBar();
  if (typeof renderScanWorkspaceJdLlmReadback === "function") {
    renderScanWorkspaceJdLlmReadback();
  }
  syncScanWorkspaceAnnotationMarkers(payload);
}

async function previewScanWorkspaceState() {
  const context = getScanWorkspaceContext();
  if (!context || !getTailoringWorkspaceSuggestionArtifactKey(context)) return;

  const selectedIds = getScanWorkspaceSelectedCandidateIds();
  const reviewDecisionMap = getScanWorkspaceCurrentReviewDecisionMap();
  if (!selectedIds.length && !Object.keys(reviewDecisionMap).length) return;

  scanWorkspaceState.isPreviewing = true;
  updateScanWorkspaceActionBar();

  try {
    const response = await postJson(buildPlanningEndpoint("/planning/preview-workspace-draft", context.planningOutputDir), {
      tailoring_json_path: getTailoringWorkspaceSuggestionArtifactKey(context),
      selected_resume: getTailoringWorkspaceResumePreviewName(context),
      selected_patch_candidate_ids: selectedIds,
      manual_bullet_edits: {},
      rewrite_review_decisions: reviewDecisionMap,
    });

    scanWorkspaceState.previewPayload = {
      preview_status: String(response.preview_status || "").trim(),
      preview_note: String(response.preview_note || "").trim(),
      original_score: response.original_score,
      projected_score: response.projected_score,
      projected_delta: response.projected_delta,
      selected_patch_set_counterfactual_preview: response.selected_patch_set_counterfactual_preview || null,
    };

    renderScanWorkspaceView();
    window.setTimeout(() => {
      syncScanWorkspaceAnnotationMarkers(scanWorkspaceState.preloadPayload);
    }, 0);

  } catch (err) {
    showAppError("Failed to preview scan state", err);
  } finally {
    scanWorkspaceState.isPreviewing = false;
    updateScanWorkspaceActionBar();
  }
}

async function saveScanWorkspaceState() {
  const context = getScanWorkspaceContext();
  if (!context || !getTailoringWorkspaceSuggestionArtifactKey(context)) return;

  scanWorkspaceState.isSaving = true;
  updateScanWorkspaceActionBar();

  try {
    const response = await postJson(buildPlanningEndpoint("/planning/save-workspace-draft", context.planningOutputDir), {
      tailoring_json_path: getTailoringWorkspaceSuggestionArtifactKey(context),
      selected_resume: getTailoringWorkspaceResumePreviewName(context),
      selected_patch_candidate_ids: getScanWorkspaceSelectedCandidateIds(),
      manual_bullet_edits: {},
      rewrite_review_decisions: getScanWorkspaceCurrentReviewDecisionMap(),
      excluded_scan_issue_ids: getScanWorkspaceExcludedIssueIds(),
      personal_details: getScanWorkspacePersonalDetailsForSave(),
      note: "Saved from scan workspace.",
    });

    const draft = response && response.draft && typeof response.draft === "object"
      ? response.draft
      : {};

    scanWorkspaceState.selectedCandidateIds = normalizeScanWorkspaceSelectedCandidateIds(
      getScanWorkspacePayload(),
      draft.selected_patch_candidate_ids || []
    );
    scanWorkspaceState.rewriteReviewDecisions = normalizeTailoringWorkspaceReviewDecisionMap(
      draft.rewrite_review_decisions || {}
    );
    scanWorkspaceState.excludedScanIssueIds = normalizeScanWorkspaceExcludedIssueIds(
      draft.excluded_scan_issue_ids || []
    );
    scanWorkspaceState.personalDetails = normalizeScanWorkspacePersonalDetails(
      draft.personal_details || {}
    );
    scanWorkspaceState.previewPayload = null;

    renderScanWorkspaceView();
  } catch (err) {
    showAppError("Failed to save scan state", err);
  } finally {
    scanWorkspaceState.isSaving = false;
    updateScanWorkspaceActionBar();
  }
}

function bindScanWorkspaceHandlers() {
  const root = qs("scanWorkspaceInteractiveSummary");
  if (root && root.dataset.bound !== "true") {
    root.dataset.bound = "true";

    root.addEventListener("click", (event) => {
      const excludeButton = event.target.closest("[data-scan-exclude-issue]");
      if (excludeButton) {
        event.preventDefault();
        event.stopPropagation();
        const issueId = String(excludeButton.dataset.scanExcludeIssue || "").trim();
        if (issueId) {
          setScanWorkspaceIssueExcluded(issueId, true);
        }
        return;
      }

      const reviewActionButton = event.target.closest("[data-scan-review-action]");
      if (reviewActionButton) {
        event.preventDefault();
        const candidateId = String(reviewActionButton.dataset.scanReviewCandidate || "").trim();
        const nextState = String(reviewActionButton.dataset.scanReviewAction || "").trim().toLowerCase();
        if (!candidateId || !nextState) return;
        setScanWorkspaceReviewDecision(candidateId, nextState);
        return;
      }

      const reviewEditButton = event.target.closest("[data-scan-review-edit]");
      if (reviewEditButton) {
        event.preventDefault();
        window.location.href = buildScanWorkspaceBackToTailoringUrl();
        return;
      }

      const selectButton = event.target.closest("[data-scan-select-candidate]");
      if (selectButton) {
        event.preventDefault();
        const candidateId = String(selectButton.dataset.scanSelectCandidate || "").trim();
        if (!candidateId) return;
        toggleScanWorkspaceCandidateSelection(candidateId);
        return;
      }

      const focusCard = event.target.closest("[data-scan-focus-candidate]");
      if (focusCard) {
        const candidateId = String(focusCard.dataset.scanFocusCandidate || "").trim();
        if (candidateId) {
          setScanWorkspaceActiveCandidate(candidateId);
        }
      }
    });

    root.addEventListener("keydown", (event) => {
      const excludeButton = event.target.closest("[data-scan-exclude-issue]");
      if (!excludeButton || (event.key !== "Enter" && event.key !== " ")) return;
      event.preventDefault();
      event.stopPropagation();
      const issueId = String(excludeButton.dataset.scanExcludeIssue || "").trim();
      if (issueId) {
        setScanWorkspaceIssueExcluded(issueId, true);
      }
    });

    const handlePersonalDetailEdit = (event) => {
      const input = event.target.closest("[data-scan-personal-detail]");
      if (!input) return;
      setScanWorkspacePersonalDetailField(
        input.dataset.scanPersonalDetail,
        input.value
      );
    };

    root.addEventListener("input", handlePersonalDetailEdit);
    root.addEventListener("change", handlePersonalDetailEdit);
  }

  const tabRow = qs("scanWorkspaceTabRow");
  if (tabRow && tabRow.dataset.bound !== "true") {
    tabRow.dataset.bound = "true";

    tabRow.addEventListener("click", (event) => {
      const tabButton = event.target.closest("[data-scan-selected-tab]");
      if (!tabButton) return;

      const nextTab = String(tabButton.dataset.scanSelectedTab || "").trim();
      if (!["personal_details", "skills", "searchability", "formatting", "recruiter_tips"].includes(nextTab)) return;

      scanWorkspaceState.selectedTab = nextTab;
      scanWorkspaceState.activeCandidateId = "";
      renderScanWorkspaceView();
      const reviewScroll = qs("scanWorkspaceInteractiveSummary")?.closest(".scan-review-left-scroll");
      if (reviewScroll) {
        reviewScroll.scrollTop = 0;
      }
    });
  }
}

function bindScanWorkspacePreviewControls() {
  const zoomOutBtn = qs("scanWorkspaceZoomOutBtn");
  const zoomResetBtn = qs("scanWorkspaceZoomResetBtn");
  const zoomInBtn = qs("scanWorkspaceZoomInBtn");

  if (!zoomOutBtn || !zoomResetBtn || !zoomInBtn) return;
  if (zoomOutBtn.dataset.bound === "true") return;

  zoomOutBtn.dataset.bound = "true";
  updateScanWorkspaceZoomLabel();

  zoomOutBtn.addEventListener("click", async () => {
    if (!scanWorkspacePdfState.pdfDoc) return;
    scanWorkspacePdfState.isFitPage = false;
    scanWorkspacePdfState.scale = Math.max(0.45, scanWorkspacePdfState.scale - 0.08);
    updateScanWorkspaceZoomLabel();
    await renderScanWorkspacePdfPages();
  });

  zoomResetBtn.addEventListener("click", async () => {
    if (!scanWorkspacePdfState.pdfDoc) return;
    await applyScanWorkspaceFitPageScale();
  });

  zoomInBtn.addEventListener("click", async () => {
    if (!scanWorkspacePdfState.pdfDoc) return;
    scanWorkspacePdfState.isFitPage = false;
    scanWorkspacePdfState.scale = Math.min(1.8, scanWorkspacePdfState.scale + 0.08);
    updateScanWorkspaceZoomLabel();
    await renderScanWorkspacePdfPages();
  });

  window.addEventListener("resize", async () => {
    if (!scanWorkspacePdfState.pdfDoc || !scanWorkspacePdfState.isFitPage) return;

    if (scanWorkspacePdfState.resizeTimer) {
      window.clearTimeout(scanWorkspacePdfState.resizeTimer);
    }

    scanWorkspacePdfState.resizeTimer = window.setTimeout(async () => {
      scanWorkspacePdfState.resizeTimer = null;
      await applyScanWorkspaceFitPageScale();
    }, 80);
  });
}

function applyScanWorkspaceSplitPercent(percent, { persist = true } = {}) {
  const layout = document.querySelector(".scan-workspace-review-shell");
  if (!layout || window.innerWidth <= 1180) return;

  const safePercent = clampToRange(Number(percent) || 34, 28, 38);
  layout.style.setProperty("--scan-workspace-left-width", `${safePercent}%`);

  if (persist) {
    localStorage.setItem(SCAN_WORKSPACE_SPLIT_STORAGE_KEY, String(safePercent));
  }
}

function bindScanWorkspaceDivider() {
  const divider = qs("scanWorkspaceDivider");
  const layout = document.querySelector(".scan-workspace-review-shell");

  if (!divider || !layout || divider.dataset.bound === "true") return;
  divider.dataset.bound = "true";

  const restoreSavedSplit = () => {
    if (window.innerWidth <= 1180) {
      layout.style.removeProperty("--scan-workspace-left-width");
      return;
    }

    const saved = Number(localStorage.getItem(SCAN_WORKSPACE_SPLIT_STORAGE_KEY));
    applyScanWorkspaceSplitPercent(Number.isFinite(saved) ? saved : 34, { persist: false });
  };

  const refreshAfterResize = () => {
    try {
      syncScanWorkspaceAnnotationMarkers(scanWorkspaceState.preloadPayload);
    } catch {
      // Annotation markers are best-effort during split resizing.
    }
  };

  divider.addEventListener("pointerdown", (event) => {
    if (window.innerWidth <= 1180) return;
    if (divider.getAttribute("aria-disabled") === "true") return;

    event.preventDefault();
    window.dispatchEvent(new CustomEvent("scan-workspace-split-resize-start"));
    document.body.classList.add("scan-workspace-resizing");

    const move = (moveEvent) => {
      const rect = layout.getBoundingClientRect();
      const rawPercent = ((moveEvent.clientX - rect.left) / rect.width) * 100;
      applyScanWorkspaceSplitPercent(rawPercent);
    };

    const stop = () => {
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", stop);
      document.body.classList.remove("scan-workspace-resizing");
      refreshAfterResize();
    };

    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", stop, { once: true });
  });

  divider.addEventListener("keydown", (event) => {
    if (window.innerWidth <= 1180) return;
    if (!["ArrowLeft", "ArrowRight"].includes(event.key)) return;

    event.preventDefault();

    const current = Number(localStorage.getItem(SCAN_WORKSPACE_SPLIT_STORAGE_KEY) || "34");
    const next = event.key === "ArrowLeft" ? current - 2 : current + 2;

    window.dispatchEvent(new CustomEvent("scan-workspace-split-resize-start"));
    applyScanWorkspaceSplitPercent(next);
    refreshAfterResize();
  });

  window.addEventListener("resize", restoreSavedSplit);
  restoreSavedSplit();
}

async function initScanWorkspacePage() {
  const page = getScanWorkspacePage();
  if (!page) return false;

  const root = qs("scanWorkspaceInteractiveSummary");
  const meta = qs("scanWorkspaceMeta");
  const context = getScanWorkspaceContext();

  updateScanWorkspaceContextLine(null);
  if (!root) return true;

  setScanWorkspaceResumePreview(context?.resumeName || "");
  bindScanWorkspaceHandlers();
  bindScanWorkspacePreviewControls();

  if (!context || !getTailoringWorkspaceSuggestionArtifactKey(context)) {
    if (meta) {
      meta.textContent = "No tailoring artifact was provided for this scan route.";
    }

    root.innerHTML = `
      <div class="tailoring-empty-state">
        This scan page is ready, but no preloaded tailoring artifact was provided.
      </div>
    `;
    return true;
  }

  let payload = null;

  try {
    if (meta) {
      meta.textContent = "Loading preloaded scan...";
    }

    payload = await loadScanWorkspacePreload();
  } catch (err) {
    if (meta) {
      meta.textContent = "Failed to load scan preload.";
    }

    root.innerHTML = `
      <div class="tailoring-empty-state">
        Failed to load the scan preload payload for this job/resume pair.
      </div>
    `;

    console.error("Failed to fetch scan preload", err);
    return true;
  }

  try {
    scanWorkspaceState.preloadPayload = payload;
    updateScanWorkspaceContextLine(payload);

    const savedDraft = payload && payload.draft && typeof payload.draft === "object"
      ? payload.draft
      : {};

    scanWorkspaceState.selectedCandidateIds = normalizeScanWorkspaceSelectedCandidateIds(
      payload,
      savedDraft.selected_patch_candidate_ids || []
    );
    scanWorkspaceState.rewriteReviewDecisions = normalizeTailoringWorkspaceReviewDecisionMap(
      savedDraft.rewrite_review_decisions || {}
    );
    scanWorkspaceState.excludedScanIssueIds = normalizeScanWorkspaceExcludedIssueIds(
      savedDraft.excluded_scan_issue_ids || []
    );
    const savedPersonalDetails = normalizeScanWorkspacePersonalDetails(savedDraft.personal_details || {});
    const sourcePersonalDetails = getScanWorkspacePersonalDetailsFromPreload(payload);
    scanWorkspaceState.personalDetails = mergeScanWorkspacePersonalDetails(
      sourcePersonalDetails,
      savedPersonalDetails
    );
    scanWorkspaceState.suggestionDecisionOverrides = {};
    scanWorkspaceState.previewPayload = null;

    scanWorkspaceState.selectedTab = "personal_details";

    renderScanWorkspaceView();

    window.setTimeout(() => {
      try {
        syncScanWorkspaceAnnotationMarkers(scanWorkspaceState.preloadPayload);
      } catch (markerErr) {
        console.error("Failed to sync scan annotation markers", markerErr);
      }
    }, 0);
  } catch (err) {
    if (meta) {
      meta.textContent = "Loaded scan preload, but failed to render scan workspace.";
    }

    const errorMessage = String(err?.message || err || "Unknown render error");
    const errorStack = String(err?.stack || "");

    root.innerHTML = `
      <div class="tailoring-empty-state">
        <div>The scan preload loaded, but the scan workspace renderer failed.</div>
        <pre style="white-space:pre-wrap;text-align:left;margin-top:12px;font-size:12px;line-height:1.45;">${escapeHtml(errorMessage)}

    ${escapeHtml(errorStack)}</pre>
      </div>
    `;

    console.error("Failed to render scan workspace after preload", err);
  }

  return true;
}


function buildTailoringWorkspaceUrl(row) {
  const params = new URLSearchParams();

  const selectedResume =
    normalizeResumePreviewName(row.operator_selected_resume) ||
    normalizeResumePreviewName(row.winner_resume);

  params.set("company", row.job_company || "");
  params.set("title", row.job_title || "");
  params.set("resume", selectedResume || "");
  params.set("status", getTailoringWorkspaceRouteStatusLabel(row));

  if (row.job_doc_id) params.set("job_doc_id", row.job_doc_id);
  if (row.tailoring_json_key || row.tailoring_json) params.set("tailoring_json", row.tailoring_json_key || row.tailoring_json);
  if (row.tailoring_md) params.set("tailoring_md", row.tailoring_md);
  if (row.tailoring_llm_json) params.set("tailoring_llm_json", row.tailoring_llm_json);
  if (row.packet_json_key || row.packet_json) params.set("packet_json", row.packet_json_key || row.packet_json);
  if (row.planning_output_dir) params.set("output_dir", row.planning_output_dir);

  return `/tailoring-workspace?${params.toString()}`;
}

function getTailoringWorkspaceRouteStatusLabel(row) {
  const workspaceState = String(row?.tailoring_workspace_state || "").trim().toLowerCase();
  const actionableCount = Number(row?.tailoring_actionable_replacement_count || 0);
  const reviewCount = Number(row?.tailoring_review_replacement_count || 0);
  const rawStatus = String(row?.llm_tailoring_status || "").trim().toLowerCase();

  if (workspaceState === "ready" || actionableCount > 0) return "Ready suggestions";
  if (workspaceState === "review" || reviewCount > 0) return "Review guidance";
  if (workspaceState === "no_safe_rewrites") return "No safe rewrites yet";
  if (rawStatus === "failed") return "No safe rewrites yet";
  if (rawStatus) return humanizeUnderscoreLabel(rawStatus);
  return "Suggestions available";
}

function getWorkspaceBlockedReason(row) {
  const llmStatus = String(row?.llm_tailoring_status || "").trim().toLowerCase();
  const workspaceState = String(row?.tailoring_workspace_state || "").trim().toLowerCase();
  const actionableCount = Number(row?.tailoring_actionable_replacement_count || 0);
  const statusText = [
    row?.tailoring_status,
    row?.llm_tailoring_status,
    row?.tailoring_workspace_state,
  ].map((value) => String(value || "").trim().toLowerCase()).join(" ");

  if (["disabled", "off", "false", "not_enabled"].includes(llmStatus) || /generation\s+is\s+off|llm.*\boff\b|disabled/.test(statusText)) {
    return "LLM tailoring generation is off for this row.";
  }

  if (workspaceState === "no_safe_rewrites") {
    return "";
  }

  if (
    actionableCount <= 0 ||
    ["empty", "unavailable", "review"].includes(workspaceState) ||
    /no safe rewrites|no safe bullet-level rewrites|no safe rewrite candidates/.test(statusText)
  ) {
    return "No safe bullet-level rewrites were found for this row.";
  }

  return "";
}

function buildTailoringButtonHtml(row) {
  const hasArtifacts = Boolean(
    row.tailoring_json || row.tailoring_md || row.tailoring_llm_json || row.packet_json
  );

  const workspaceState = String(row.tailoring_workspace_state || "empty").trim().toLowerCase();
  const actionableCount = Number(row.tailoring_actionable_replacement_count || 0);
  const reviewCount = Number(row.tailoring_review_replacement_count || 0);
  const blockedReason = hasArtifacts ? getWorkspaceBlockedReason(row) : "";

  const label = hasArtifacts ? "Open Workspace" : "Unavailable";
  const disabledAttr = hasArtifacts && !blockedReason ? "" : "disabled";

  let stateClass = "planning-tailoring-btn--empty";
  let reviewActionStateClass = "review-action-button--disabled";
  let titleText = "No tailoring artifacts available for this row.";

  if (hasArtifacts && workspaceState === "ready") {
    stateClass = "planning-tailoring-btn--ready";
    reviewActionStateClass = "review-action-button--available";
    titleText = `${actionableCount} actionable suggestion${actionableCount === 1 ? "" : "s"} available.`;
  } else if (hasArtifacts && workspaceState === "review") {
    stateClass = "planning-tailoring-btn--review";
    reviewActionStateClass = "review-action-button--available";
    titleText = reviewCount > 0
      ? `${reviewCount} review-only suggestion${reviewCount === 1 ? "" : "s"} available. No ready replacements yet.`
      : "Review guidance is available, but there are no ready replacements yet.";
  } else if (hasArtifacts && workspaceState === "no_safe_rewrites") {
    stateClass = "planning-tailoring-btn--review";
    reviewActionStateClass = "review-action-button--available";
    titleText = "Review-only guidance is available. No app-ready replacement is available yet.";
  } else if (hasArtifacts) {
    stateClass = "planning-tailoring-btn--empty";
    reviewActionStateClass = "review-action-button--disabled";
    titleText = "Suggestions loaded, but no safe bullet-level rewrites were found.";
  }

  if (blockedReason) {
    stateClass = "planning-tailoring-btn--empty";
    reviewActionStateClass = "review-action-button--disabled";
    titleText = blockedReason;
  }

  const buttonClass = `ghost-btn planning-tailoring-btn review-action-button ${stateClass} ${reviewActionStateClass}`.trim();
  const titleAttr = `title="${escapeHtml(titleText)}"`;
  const blockedAttr = blockedReason
    ? `data-workspace-blocked-reason="${escapeHtml(blockedReason)}" aria-disabled="true"`
    : "";

  return `
    <button
      type="button"
      class="${buttonClass}"
      ${disabledAttr}
      ${titleAttr}
      ${blockedAttr}
      data-view-tailoring="true"
      data-job-doc-id="${escapeHtml(row.job_doc_id || "")}"
      data-job-company="${escapeHtml(row.job_company || "")}"
      data-job-title="${escapeHtml(row.job_title || "")}"
      data-winner-resume="${escapeHtml(row.winner_resume || "")}"
      data-operator-selected-resume="${escapeHtml(row.operator_selected_resume || "")}"
      data-llm-tailoring-status="${escapeHtml(row.llm_tailoring_status || "")}"
      data-tailoring-json="${escapeHtml(row.tailoring_json || "")}"
      data-tailoring-json-key="${escapeHtml(row.tailoring_json_key || "")}"
      data-tailoring-md="${escapeHtml(row.tailoring_md || "")}"
      data-tailoring-llm-json="${escapeHtml(row.tailoring_llm_json || "")}"
      data-packet-json="${escapeHtml(row.packet_json || "")}"
      data-packet-json-key="${escapeHtml(row.packet_json_key || "")}"
      data-planning-output-dir="${escapeHtml(row.planning_output_dir || "")}"
      data-tailoring-workspace-state="${escapeHtml(row.tailoring_workspace_state || "")}"
      data-tailoring-actionable-replacement-count="${escapeHtml(row.tailoring_actionable_replacement_count || "")}"
      data-tailoring-review-replacement-count="${escapeHtml(row.tailoring_review_replacement_count || "")}"
    >
      ${label}
    </button>
  `;
}

async function handleTailoringClick(button) {
  const blockedReason = String(button.dataset.workspaceBlockedReason || "").trim();
  if (blockedReason) {
    return;
  }

  const row = {
    job_doc_id: button.dataset.jobDocId || "",
    job_company: button.dataset.jobCompany || "",
    job_title: button.dataset.jobTitle || "",
    winner_resume: button.dataset.winnerResume || "",
    operator_selected_resume: button.dataset.operatorSelectedResume || "",
    llm_tailoring_status: button.dataset.llmTailoringStatus || "",
    tailoring_json: button.dataset.tailoringJson || "",
    tailoring_json_key: button.dataset.tailoringJsonKey || "",
    tailoring_md: button.dataset.tailoringMd || "",
    tailoring_llm_json: button.dataset.tailoringLlmJson || "",
    packet_json: button.dataset.packetJson || "",
    packet_json_key: button.dataset.packetJsonKey || "",
    planning_output_dir: button.dataset.planningOutputDir || "",
    tailoring_workspace_state: button.dataset.tailoringWorkspaceState || "",
    tailoring_actionable_replacement_count: button.dataset.tailoringActionableReplacementCount || "",
    tailoring_review_replacement_count: button.dataset.tailoringReviewReplacementCount || "",
  };

  window.location.href = buildTailoringWorkspaceUrl(row);
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

function buildPlanningJobSummaryHtml(row) {
  const title = escapeHtml(row.job_title || "");
  const jobUrl = escapeHtml(row.job_doc_id || row.job_url || "");
  const titleHtml = jobUrl
    ? `<a class="job-link" href="${jobUrl}" target="_blank" rel="noopener noreferrer">${title}</a>`
    : title;
  const company = escapeHtml(row.job_company || "");
  const location = escapeHtml(row.job_location || "");

  return `
    <div class="queue-job-summary">
      <div class="queue-simple-company">${company || "-"}</div>
      <div class="queue-simple-title">${titleHtml}</div>
      ${location ? `<div class="queue-job-location">${location}</div>` : ""}
    </div>
  `;
}

function buildPlanningRecommendationCellHtml(row) {
  const action = escapeHtml(formatQueueActionLabel(row.action) || "-");
  const tone = escapeHtml(getRecommendationTone(row.action));
  const details = buildRecommendationDetailsHtml([
    { label: "Runner-up resume", value: row.runner_up_resume || "" },
    { label: "Runner-up score", value: row.runner_up_score || "" },
    { label: "Score gap", value: row.score_gap || "" },
    { label: "Match strength", value: row.winner_bucket || "" },
    { label: "Review state", value: deriveReviewStateLabel(row) },
    { label: "Missing requirements", value: row.missing_requirement_count || "" },
    { label: "Fallback resume", value: row.llm_fallback_best_resume || "" },
    { label: "Fallback status", value: humanizeFallbackStatus(row.llm_fallback_status || "") },
    { label: "LLM review hint", value: row.llm_adjudication_resume || "" },
    { label: "Next step", value: formatOperatorDecisionLabel(row.operator_decision) || row.operator_decision || "" },
    { label: "Raw operator decision", value: row.operator_decision || "" },
    { label: "Priority reason", value: buildPlanningPriorityReason(row) },
  ]);

  return `
    <div class="queue-recommendation-summary">
      <span class="pill recommendation-chip recommendation-chip--${tone}">${action}</span>
      ${details}
    </div>
  `;
}

function buildPlanningPacketWorkspaceStatusHtml(row) {
  const workspaceState = String(row.tailoring_workspace_state || "").trim();
  const workspaceLabel = workspaceState
    ? humanizeUnderscoreLabel(workspaceState)
    : "Workspace pending";
  return `
    <div class="queue-status-stack">
      ${buildPacketStatusChipHtml(row) || ""}
      <span class="queue-workspace-pill">${escapeHtml(workspaceLabel)}</span>
    </div>
  `;
}

function buildPlanningSelectedResumeHtml(row) {
  return buildCompactTextHtml(row.operator_selected_resume || row.winner_resume, {
    emptyLabel: "-",
    truncate: false,
    wrap: true,
  });
}

function renderPlanningRows(rows, metaLabel) {
  planningTableState.rows = Array.isArray(rows) ? rows.slice() : [];
  planningTableState.metaLabel = metaLabel;

  const tbody = qs("planningTableBody");
  const displayRows = sortRows(planningTableState.rows, PLANNING_SORT_COLUMNS, planningTableState.sort);

  if (!displayRows.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="8" class="empty-state">No rows found.</td>
      </tr>
    `;
    qs("planningTableMeta").textContent = planningTableState.metaLabel;
    updatePlanningStats(0);
    renderSortableHeaders("planningTable", PLANNING_SORT_COLUMNS, planningTableState.sort);
    renderPlanningPagination();
    window.clearTableWrapLoading?.(tbody);
    return;
  }

  tbody.innerHTML = displayRows.map((row) => {
    return `
      <tr>
        <td>${escapeHtml(row.queue_rank || "")}</td>
        <td class="title-cell">${buildPlanningJobSummaryHtml(row)}</td>
        <td>${buildDateTimeCellHtml(row.posted_at)}</td>
        <td>${buildPlanningRecommendationCellHtml(row)}</td>
        <td>${buildPlanningPacketWorkspaceStatusHtml(row)}</td>
        <td>${escapeHtml(formatScore100(row.winner_score))}</td>
        <td>${buildPlanningSelectedResumeHtml(row)}</td>
        <td class="apply-cell sticky-apply-col">${buildTailoringButtonHtml(row)}</td>
      </tr>
    `;
  }).join("");

  qs("planningTableMeta").textContent = planningTableState.metaLabel;
  renderSortableHeaders("planningTable", PLANNING_SORT_COLUMNS, planningTableState.sort);
  renderPlanningPagination();
  window.clearTableWrapLoading?.(tbody);
  initResizableTableColumns("planningTable", "planningTableColumnWidths");
}

async function loadPlanningTable({
  forceNetwork = false,
  requestedPage = null,
  historyMode = "replace",
} = {}) {
  const tbody = qs("planningTableBody");
  if (!tbody) return;
  const pipelineVersionChanged = invalidatePlanningTableCacheIfPipelineChanged();
  const shouldForceNetwork = forceNetwork || pipelineVersionChanged;

  const paginationMeta = qs("planningPaginationMeta");
  const tableMeta = qs("planningTableMeta");

  const resolvedPage =
    Number.isFinite(Number(requestedPage)) && Number(requestedPage) > 0
      ? Math.floor(Number(requestedPage))
      : planningTableState.pagination.page || 1;

  const url = buildPlanningUrl(resolvedPage);
  const cachedData = shouldForceNetwork ? null : readPlanningTableLastResponse(url);
  const stableSnapshot = capturePlanningTableSnapshot();

  planningTableState.requestSeq += 1;
  const requestSeq = planningTableState.requestSeq;

  if (cachedData) {
    applyPlanningTableResponse(cachedData, { historyMode });
    if (tableMeta) {
      tableMeta.textContent = "Showing cached rows while refreshing...";
    }
  } else if (stableSnapshot) {
    window.setTableWrapLoading?.(tbody, "Loading planning rows...");
    if (tableMeta) {
      tableMeta.textContent = `${stableSnapshot.metaLabel} · Loading...`;
    }
    if (paginationMeta) {
      paginationMeta.textContent = "Loading...";
    }
  } else {
    tbody.innerHTML = "";
    window.setTableWrapLoading?.(tbody, "Loading planning rows...");
    if (tableMeta) tableMeta.textContent = "Loading...";
    if (paginationMeta) paginationMeta.textContent = "Loading...";
    await new Promise((resolve) => window.requestAnimationFrame(resolve));
  }

  if (planningTableState.activeController) {
    try {
      planningTableState.activeController.abort();
    } catch {
      // ignore abort failure
    }
  }

  const controller = new AbortController();
  planningTableState.activeController = controller;
  planningTableState.isLoading = true;

  try {
    const data = await fetchJson(url, {
      signal: controller.signal,
      timeoutMs: PLANNING_TABLE_REQUEST_TIMEOUT_MS,
    });

    if (requestSeq !== planningTableState.requestSeq) {
      return;
    }

    writePlanningTableLastResponse(url, data, { persistToSession: true });
    applyPlanningTableResponse(data, { historyMode });
  } catch (err) {
    if (err && err.name === "AbortError") {
      return;
    }

    if (cachedData) {
      if (tableMeta) {
        tableMeta.textContent = `${planningTableState.metaLabel} · refresh failed`;
      }
      return;
    }

    const note =
      err instanceof Error && err.message
        ? err.message
        : "refresh failed";

    if (restorePlanningTableSnapshot(stableSnapshot, { note })) {
      return;
    }

    throw err;
  } finally {
    if (planningTableState.activeController === controller) {
      planningTableState.activeController = null;
    }
    planningTableState.isLoading = false;
    window.clearTableWrapLoading?.(tbody);
  }
}

function clearPlanningFilters() {
  clearMultiSelect("planningActionFilter");
  clearMultiSelect("planningWinnerBucket");
  clearMultiSelect("planningTailoringFilter");

  const defaultUndecided = document.querySelector("input[name='planningUndecidedOnlyToggle'][value='no']");
  if (defaultUndecided) {
    defaultUndecided.checked = true;
  }

  qs("planningLimitInput").value = "15";
  updatePlanningStats(0);
}

function attachPlanningHandlers() {
  initMultiSelect("planningActionFilter");
  initMultiSelect("planningWinnerBucket");
  initMultiSelect("planningTailoringFilter");

  qs("planningApplyFiltersBtn").addEventListener("click", async () => {
    try {
      await loadPlanningTable({
        requestedPage: 1,
        historyMode: "push",
      });
    } catch (err) {
      showAppError("Failed to load planning table", err);
    }
  });

  qs("planningClearFiltersBtn").addEventListener("click", async () => {
    clearPlanningFilters();
    try {
      await loadPlanningTable({
        requestedPage: 1,
        historyMode: "push",
      });
    } catch (err) {
      showAppError("Failed to reload planning table", err);
    }
  });

  qs("planningPaginationActions").addEventListener("click", async (event) => {
    const button = event.target.closest("[data-planning-page]");
    if (!button || button.disabled) return;

    const nextPage = Number(button.dataset.planningPage || "");
    if (!Number.isFinite(nextPage) || nextPage < 1) return;

    try {
      await loadPlanningTable({
        requestedPage: nextPage,
        historyMode: "push",
      });
    } catch (err) {
      showAppError("Failed to change planning page", err);
    }
  });

  qs("planningTableBody").addEventListener("click", async (event) => {
    const resumeChoiceButton = event.target.closest("[data-view-resume-choices='true']");
    if (resumeChoiceButton && !resumeChoiceButton.disabled) {
      openResumeChoiceModal({
        queue_rank: resumeChoiceButton.dataset.queueRank || "",
        job_doc_id: resumeChoiceButton.dataset.jobDocId || "",
        job_url: resumeChoiceButton.dataset.jobUrl || "",
        job_company: resumeChoiceButton.dataset.jobCompany || "",
        job_title: resumeChoiceButton.dataset.jobTitle || "",
        action: resumeChoiceButton.dataset.action || "",
        score_gap: resumeChoiceButton.dataset.scoreGap || "",
        winner_resume: resumeChoiceButton.dataset.winnerResume || "",
        winner_score: resumeChoiceButton.dataset.winnerScore || "",
        runner_up_resume: resumeChoiceButton.dataset.runnerUpResume || "",
        runner_up_score: resumeChoiceButton.dataset.runnerUpScore || "",
        operator_selected_resume: resumeChoiceButton.dataset.operatorSelectedResume || "",
      });
      return;
    }

    const tailoringButton = event.target.closest("[data-view-tailoring='true']");
    if (tailoringButton && !tailoringButton.disabled) {
      try {
        await handleTailoringClick(tailoringButton);
      } catch (err) {
        showAppError("Failed to load tailoring artifacts", err);
      }
      return;
    }

    const applyButton = event.target.closest("[data-apply-job='true']");
    if (!applyButton || applyButton.disabled) return;

    try {
      await handleApplyClick(applyButton);
    } catch (err) {
      showAppError("Failed to open apply workflow", err);
    }
  });

  qs("closeApplicationModalBtn").addEventListener("click", () => {
    clearPendingApplication();
    closeApplicationModal();
  });

  qs("closeResumeChoiceModalBtn").addEventListener("click", closeResumeChoiceModal);
  qs("resumeChoiceCancelBtn").addEventListener("click", closeResumeChoiceModal);

  qs("resumeChoiceList").addEventListener("click", (event) => {
    const choiceButton = event.target.closest("[data-resume-choice='true']");
    if (!choiceButton) return;
    void setResumeChoicePreview(choiceButton.dataset.resumeName || "");
  });

  qs("resumeChoiceSelectBtn").addEventListener("click", async () => {
    try {
      await submitResumeChoiceSelection({ generateLlmTailoring: false });
    } catch (err) {
      setResumeChoiceBusyState(false, "Failed to save resume choice.");
      resetResumeChoiceLoadingContent();
      showAppError("Failed to save selected resume", err);
    }
  });

  qs("resumeChoiceGenerateLlmBtn").addEventListener("click", async () => {
    try {
      await submitResumeChoiceSelection({ generateLlmTailoring: true });
    } catch (err) {
      setResumeChoiceBusyState(false, "Failed to generate LLM tailoring.");
      resetResumeChoiceLoadingContent();
      showAppError("Failed to generate LLM tailoring", err);
    }
  });

  getResumeChoiceModal().addEventListener("click", (event) => {
    if (event.target === getResumeChoiceModal() && !resumeChoiceState.isBusy) {
      closeResumeChoiceModal();
    }
  });

  qs("copyTailoringMarkdownBtn").addEventListener("click", handleCopyTailoringMarkdown);

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

  qs("closeTailoringModalBtn").addEventListener("click", closeTailoringModal);

  getTailoringModal().addEventListener("click", (event) => {
    const toggleButton = event.target.closest("[data-tailoring-accordion-toggle]");
    if (toggleButton) {
      toggleTailoringManualAccordion(toggleButton);
      return;
    }

    if (event.target === getTailoringModal()) {
      closeTailoringModal();
    }
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

  window.addEventListener("focus", () => {
    const pending = loadPendingApplicationFromStorage();
    if (pending && getApplicationModal().classList.contains("hidden")) {
      openApplicationModal(pending);
    }

    if (invalidatePlanningTableCacheIfPipelineChanged()) {
      loadPlanningTable({ forceNetwork: true }).catch((err) => {
        showAppError("Failed to refresh planning dashboard after pipeline run", err);
      });
    }
  });

  window.addEventListener("storage", (event) => {
    if (event.key !== PIPELINE_DATA_VERSION_STORAGE_KEY) return;

    planningTableState.pipelineDataVersion = String(event.newValue || "");
    clearPlanningTableResponseCache();
    loadPlanningTable({ forceNetwork: true }).catch((err) => {
      showAppError("Failed to refresh planning dashboard after pipeline run", err);
    });
  });

  window.addEventListener("popstate", async () => {
    applyPlanningUrlState(window.location.search);

    try {
      await loadPlanningTable();
    } catch (err) {
      showAppError("Failed to restore planning dashboard state", err);
    }
  });
}

window.addEventListener("DOMContentLoaded", async () => {
  const isPlanningPage = Boolean(qs("planningTable"));
  const isTailoringWorkspacePage = Boolean(document.querySelector(".tailoring-workspace-page"));
  const isScanWorkspacePage = Boolean(document.querySelector(".scan-workspace-page"));

  if (isPlanningPage) {
    bindAppErrorModal();
    applyPlanningUrlState(window.location.search);
    attachPlanningHandlers();
    bindTableSorting("planningTable", PLANNING_SORT_COLUMNS, planningTableState.sort, () => {
      syncPlanningBrowserUrl({ mode: "push" });
      renderPlanningRows(planningTableState.rows, planningTableState.metaLabel);
    });

    try {
      await loadPlanningTable();
    } catch (err) {
      showAppError("Failed to initialize planning dashboard", err);
    }
    return;
  }

  if (isTailoringWorkspacePage) {
    bindTailoringWorkspacePreviewControls();
    bindTailoringWorkspaceSelectionHandlers();
    bindTailoringWorkspaceActionBar();
    bindTailoringWorkspaceExportModal();
    await initTailoringWorkspacePage();
    return;
  }

  if (isScanWorkspacePage) {
    bindScanWorkspaceDivider();
    await initScanWorkspacePage();
    return;
  }
});


/*
 * Phase 78B local repair: LinkedIn contact hydration backfill.
 *
 * This does not fabricate a LinkedIn URL and does not hardcode user data.
 * It only propagates an existing linkedin.com URL from loaded scan/workspace
 * payloads, script JSON, local/session storage, or visible source text into
 * the LinkedIn edit field and resume preview contact row when the normal
 * hydration path left LinkedIn empty.
 */
