const PENDING_APPLICATION_STORAGE_KEY = "job_operator_pending_application";

let currentTailoringMarkdownRaw = "";
let tailoringCopyResetTimer = null;
let resumeChoiceState = {
  row: null,
  candidates: [],
  selectedResume: "",
  isBusy: false,
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

const planningTableState = {
  rows: [],
  metaLabel: "Loading...",
  sort: {
    key: "",
    direction: "asc",
  },
};

const tailoringWorkspaceState = {
  artifact: null,
  selectedCandidateIds: [],
  candidateLookup: new Map(),
};

const tailoringWorkspacePdfState = {
  pdfDoc: null,
  resumeName: "",
  scale: 1.1,
  renderToken: 0,
  pdfjsPromise: null,
  pageTextIndex: [],
  highlightedCandidateId: "",
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

function getMultiSelectRoot(id) {
  return qs(id);
}

function getMultiSelectValues(id) {
  const root = getMultiSelectRoot(id);
  if (!root) return [];

  return Array.from(root.querySelectorAll(".multi-select-option.is-selected"))
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

  const selected = Array.from(root.querySelectorAll(".multi-select-option.is-selected"));
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
  const menu = root.querySelector(".multi-select-menu");
  if (!trigger || !menu) return;

  root.classList.toggle("is-open", isOpen);
  trigger.setAttribute("aria-expanded", isOpen ? "true" : "false");
  menu.hidden = !isOpen;
}

function clearMultiSelect(id) {
  const root = getMultiSelectRoot(id);
  if (!root) return;

  root.querySelectorAll(".multi-select-option").forEach((option) => {
    option.classList.remove("is-selected");
    option.setAttribute("aria-checked", "false");
  });

  updateMultiSelectLabel(root);
}

function initMultiSelect(id) {
  const root = getMultiSelectRoot(id);
  if (!root || root.dataset.bound === "true") return;

  const trigger = root.querySelector(".multi-select-trigger");
  const menu = root.querySelector(".multi-select-menu");
  if (!trigger || !menu) return;

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

  root.querySelectorAll(".multi-select-option").forEach((option) => {
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
  { key: "action", label: "Action", type: "text" },
  { key: "job_company", label: "Company", type: "text" },
  { key: "job_title", label: "Title", type: "text" },
  { key: "posted_at", label: "Posted At", type: "date" },
  { key: "winner_resume", label: "Winner", type: "text" },
  { key: "winner_score", label: "Score", type: "number" },
  { key: "runner_up_resume", label: "Backup", type: "text" },
  { key: "runner_up_score", label: "Backup Score", type: "number" },
  { key: "score_gap", label: "Gap", type: "number" },
  { key: "winner_bucket", label: "Strength", type: "text" },
  {
    key: "review_state",
    label: "Review",
    type: "text",
    getValue: (row) => deriveReviewStateLabel(row),
  },
  { key: "missing_requirement_count", label: "Missing", type: "number" },
  { key: "llm_fallback_best_resume", label: "Fallback Resume", type: "text" },
  {
    key: "llm_fallback_status",
    label: "Fallback",
    type: "text",
    getValue: (row) => humanizeFallbackStatus(row.llm_fallback_status),
  },
  { key: "operator_decision", label: "Decision", type: "text" },
  { key: "operator_selected_resume", label: "Selected", type: "text" },
  { key: "queue_priority_reason", label: "Why", type: "text" },
  { key: "tailoring", label: "Tailor", sortable: false },
  { key: "apply", label: "Apply", sortable: false },
];

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

function countPlanningActiveFilters() {
  let count = 0;
  if (getMultiSelectValues("planningActionFilter").length) count += 1;
  if (getMultiSelectValues("planningWinnerBucket").length) count += 1;
  if (planningUndecidedOnlyEnabled()) count += 1;
  return count;
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

function updatePlanningStats(rowCount) {
  setTextIfPresent("planningJobsShown", rowCount ?? 0);
  setTextIfPresent("planningActiveFilters", countPlanningActiveFilters());
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

function buildPlanningUrl() {
  const params = new URLSearchParams();
  const actions = getMultiSelectValues("planningActionFilter");
  const winnerBuckets = getMultiSelectValues("planningWinnerBucket");
  const undecidedOnly = planningUndecidedOnlyEnabled() ? "true" : "";
  const limit = qs("planningLimitInput").value || "50";

  appendMultiValueParams(params, "action", actions);
  appendMultiValueParams(params, "winner_bucket", winnerBuckets);
  if (undecidedOnly) params.set("undecided_only", undecidedOnly);
  params.set("limit", limit);

  return `/browse?${params.toString()}`;
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

function getTailoringModal() {
  return qs("tailoringModal");
}

function getResumeChoiceModal() {
  return qs("resumeChoiceModal");
}

function normalizeResumeName(value) {
  return String(value || "").trim();
}

function buildResumePdfFileUrl(resumeName) {
  const params = new URLSearchParams();
  params.set("resume_name", resumeName);
  return `/planning/resume-preview?${params.toString()}`;
}

function buildResumePreviewUrl(resumeName) {
  return `${buildResumePdfFileUrl(resumeName)}#toolbar=0&navpanes=0&scrollbar=1&view=FitH`;
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

  let best = null;

  tailoringWorkspacePdfState.pageTextIndex.forEach((pageEntry) => {
    (pageEntry.lines || []).forEach((line) => {
      const score = scoreTailoringWorkspaceLineMatch(safeTarget, line.text);
      if (!score) return;

      if (!best || score > best.score) {
        best = {
          pageNumber: pageEntry.pageNumber,
          lineText: line.text,
          bbox: line.bbox,
          score,
        };
      }
    });
  });

  return best && best.score >= 50 ? best : null;
}

function buildTailoringWorkspaceDefaultPreviewMeta() {
  if (!tailoringWorkspacePdfState.pdfDoc) {
    return "Resume preview is not available for this workspace row.";
  }

  const pageCount = tailoringWorkspacePdfState.pdfDoc.numPages;
  return `${pageCount} page${pageCount === 1 ? "" : "s"} • ${Math.round(
    tailoringWorkspacePdfState.scale * 100
  )}%`;
}

function clearTailoringWorkspacePdfHighlight({ restoreMeta = true } = {}) {
  const pagesRoot = qs("tailoringWorkspacePdfPages");
  if (pagesRoot) {
    pagesRoot.querySelectorAll(".tailoring-workspace-pdf-highlight").forEach((node) => node.remove());
  }

  tailoringWorkspacePdfState.highlightedCandidateId = "";

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

  pageShell.scrollIntoView({
    behavior: "smooth",
    block: "center",
  });

  setTailoringWorkspacePreviewMeta(
    `Matched bullet on page ${match.pageNumber} • ${Math.round(tailoringWorkspacePdfState.scale * 100)}%`
  );
}

function focusTailoringWorkspaceCandidateInPreview(candidateId) {
  const item = getTailoringWorkspaceCandidateItem(candidateId);
  if (!item || !tailoringWorkspacePdfState.pdfDoc) return;

  const targetText =
    String(item.original_text || "").trim() ||
    String(item.final_replacement_text || "").trim();

  if (!targetText) {
    clearTailoringWorkspacePdfHighlight();
    return;
  }

  const match = findTailoringWorkspaceBestPdfMatch(targetText);
  if (!match) {
    clearTailoringWorkspacePdfHighlight({ restoreMeta: false });
    setTailoringWorkspacePreviewMeta("Could not find a matching bullet in the current PDF preview.");
    return;
  }

  applyTailoringWorkspacePdfHighlight(match, candidateId);
}

function syncTailoringWorkspacePreviewHighlight() {
  const selectedIds = getTailoringWorkspaceSelectedCandidateIds();

  if (!selectedIds.length) {
    clearTailoringWorkspacePdfHighlight();
    return;
  }

  focusTailoringWorkspaceCandidateInPreview(selectedIds[selectedIds.length - 1]);
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
  label.textContent = `${Math.round(tailoringWorkspacePdfState.scale * 100)}%`;
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
    `Rendering ${pageCount} page${pageCount === 1 ? "" : "s"} at ${Math.round(scale * 100)}%...`
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
      lines: lineIndex,
    });
  }

  if (token !== tailoringWorkspacePdfState.renderToken) return;

  tailoringWorkspacePdfState.pageTextIndex = pageTextIndex;

  pagesRoot.innerHTML = "";
  pagesRoot.appendChild(fragment);
  pagesRoot.classList.remove("hidden");
  empty.classList.add("hidden");

  setTailoringWorkspacePreviewMeta(buildTailoringWorkspaceDefaultPreviewMeta());
  syncTailoringWorkspacePreviewHighlight();
}

async function setTailoringWorkspacePreview(resumeName) {
  const safeName = normalizeResumeName(resumeName);
  const nameEl = qs("tailoringWorkspacePreviewName");

  if (nameEl) {
    nameEl.textContent = safeName ? humanizeResumeDisplayName(safeName) : "No resume selected";
  }

  if (!safeName) {
    await clearTailoringWorkspacePdfView("No resume selected for this workspace row.");
    return;
  }

  try {
    const pdfjsLib = await getTailoringWorkspacePdfJs();
    const pdfUrl = buildResumePdfFileUrl(safeName);
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
    tailoringWorkspacePdfState.resumeName = safeName;

    await renderTailoringWorkspacePdfPages();
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
    tailoringWorkspacePdfState.scale = Math.max(0.8, tailoringWorkspacePdfState.scale - 0.1);
    await renderTailoringWorkspacePdfPages();
  });

  zoomResetBtn.addEventListener("click", async () => {
    if (!tailoringWorkspacePdfState.pdfDoc) return;
    tailoringWorkspacePdfState.scale = 1.1;
    await renderTailoringWorkspacePdfPages();
  });

  zoomInBtn.addEventListener("click", async () => {
    if (!tailoringWorkspacePdfState.pdfDoc) return;
    tailoringWorkspacePdfState.scale = Math.min(1.8, tailoringWorkspacePdfState.scale + 0.1);
    await renderTailoringWorkspacePdfPages();
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
  resumeChoiceState = {
    row: null,
    candidates: [],
    selectedResume: "",
    isBusy: false,
  };

  qs("resumeChoiceCompany").textContent = "-";
  qs("resumeChoiceTitle").textContent = "-";
  qs("resumeChoiceAction").textContent = "-";
  qs("resumeChoiceGap").textContent = "-";
  qs("resumeChoicePreviewName").textContent = "Select a resume to preview";
  qs("resumeChoiceSaveStatus").textContent = "No resume selected yet.";
  qs("resumeChoiceList").innerHTML = `<div class="resume-choice-empty">No resume choices available.</div>`;

  const previewFrame = qs("resumeChoicePreviewFrame");
  const previewEmpty = qs("resumeChoicePreviewEmpty");
  const selectBtn = qs("resumeChoiceSelectBtn");
  const llmBtn = qs("resumeChoiceGenerateLlmBtn");

  previewFrame.src = "about:blank";
  previewFrame.classList.add("hidden");
  previewEmpty.classList.remove("hidden");

  qs("resumeChoiceLoadingOverlay").classList.add("hidden");
  qs("resumeChoiceCancelBtn").disabled = false;
  qs("closeResumeChoiceModalBtn").disabled = false;

  selectBtn.disabled = true;
  if (llmBtn) {
    llmBtn.disabled = true;
  }

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

function setResumeChoicePreview(resumeName) {
  const safeName = normalizeResumeName(resumeName);
  const previewFrame = qs("resumeChoicePreviewFrame");
  const previewEmpty = qs("resumeChoicePreviewEmpty");
  const previewName = qs("resumeChoicePreviewName");
  const selectBtn = qs("resumeChoiceSelectBtn");
  const llmBtn = qs("resumeChoiceGenerateLlmBtn");

  if (!safeName) {
    previewFrame.src = "about:blank";
    previewFrame.classList.add("hidden");
    previewEmpty.classList.remove("hidden");
    previewName.textContent = "Select a resume to preview";
    selectBtn.disabled = true;
    if (llmBtn) {
      llmBtn.disabled = true;
    }
    return;
  }

  const previewUrl = buildResumePreviewUrl(safeName);

  resumeChoiceState.selectedResume = safeName;
  previewName.textContent = humanizeResumeDisplayName(safeName);
  previewFrame.src = previewUrl;
  previewFrame.classList.remove("hidden");
  previewEmpty.classList.add("hidden");

  selectBtn.disabled = resumeChoiceState.isBusy ? true : false;
  if (llmBtn) {
    llmBtn.disabled = resumeChoiceState.isBusy ? true : false;
  }
  qs("resumeChoiceSaveStatus").textContent = `Selected: ${humanizeResumeDisplayName(safeName)}`;

  renderResumeChoiceCards();
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
    setResumeChoicePreview(defaultResume);
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

function buildCompactTextHtml(value, { maxLength = 36, emptyLabel = "-" } = {}) {
  const fullRaw = String(value || "").trim();
  if (!fullRaw) return escapeHtml(emptyLabel);

  const full = humanizeResumeDisplayName(fullRaw);
  const visible = truncateText(full, maxLength);

  return `<span title="${escapeHtml(fullRaw)}">${escapeHtml(visible)}</span>`;
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
  return buildCompactTextHtml(row.llm_fallback_best_resume, { maxLength: 28 });
}

function buildReasonHtml(value) {
  const full = String(value || "").trim();
  if (!full) return "-";
  const visible = truncateText(full, 72);
  return `<span title="${escapeHtml(full)}">${escapeHtml(visible)}</span>`;
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

function buildArtifactUrl(path) {
  const params = new URLSearchParams();
  params.set("path", path);
  return `/planning-artifact?${params.toString()}`;
}

async function loadArtifact(path) {
  const raw = String(path || "").trim();
  if (!raw || raw === ".") return null;
  return fetchJson(buildArtifactUrl(raw));
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
        ${safeItems.map((item, index) => `
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

            ${item.current_evidence ? `
              <div class="tailoring-info-block">
                <div class="tailoring-info-label">Current evidence</div>
                <div class="tailoring-quote-block">${escapeHtml(item.current_evidence)}</div>
              </div>
            ` : ""}

            ${item.parent_bullet ? `
              <div class="tailoring-info-block">
                <div class="tailoring-info-label">Parent bullet</div>
                <div class="tailoring-quote-block">${escapeHtml(item.parent_bullet)}</div>
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
        `).join("")}
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

function renderReplacementPlanSummary(summary) {
  const data = summary && typeof summary === "object" ? summary : {};
  const total = Number(data.total_rewrite_bullets || 0);
  const ready = Number(data.direct_apply_ready_count || 0) + Number(data.direct_apply_optional_count || 0);
  const reviewOnly = Number(data.direction_only_count || 0);

  return `
    <section class="tailoring-section-block">
      <div class="tailoring-section-title">Quick summary</div>
      <div class="tailoring-priority-grid">
        <article class="tailoring-priority-card">
          <div class="tailoring-card-topline">
            ${buildTailoringTonePill("TOTAL", "neutral")}
          </div>
          <div class="tailoring-card-title">${escapeHtml(String(total))}</div>
          <div class="tailoring-card-copy">Suggestions found</div>
        </article>

        <article class="tailoring-priority-card">
          <div class="tailoring-card-topline">
            ${buildTailoringTonePill("READY", "safe")}
          </div>
          <div class="tailoring-card-title">${escapeHtml(String(ready))}</div>
          <div class="tailoring-card-copy">Ready to use or lightly polish</div>
        </article>

        <article class="tailoring-priority-card">
          <div class="tailoring-card-topline">
            ${buildTailoringTonePill("REVIEW", "muted")}
          </div>
          <div class="tailoring-card-title">${escapeHtml(String(reviewOnly))}</div>
          <div class="tailoring-card-copy">Needs manual judgment</div>
        </article>
      </div>
    </section>
  `;
}

function getTailoringReplacementCandidateId(item) {
  return String(
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

function updateTailoringWorkspaceMetaSummary(payload) {
  const meta = qs("tailoringWorkspaceMeta");
  if (!meta) return;

  const selectableCount = collectTailoringWorkspaceSelectableCandidateIds(payload).length;
  const selectedCount = getTailoringWorkspaceSelectedCandidateIds().length;

  if (!payload) {
    meta.textContent = "Actionable suggestions are not available for this row.";
    return;
  }

  if (!selectableCount) {
    meta.textContent = "Suggestions loaded. This row has review guidance, but no selectable rewrite candidates.";
    return;
  }

  meta.textContent = `${selectedCount} of ${selectableCount} actionable suggestions selected. Direction-only guidance stays read-only.`;
}

function rerenderTailoringWorkspaceSelectionView() {
  if (!tailoringWorkspaceState.artifact) return;

  renderTailoringInteractiveSummaryInto(
    "tailoringWorkspaceInteractiveSummary",
    tailoringWorkspaceState.artifact,
    {
      includeDiagnostics: false,
      selectionEnabled: true,
      selectedCandidateIds: getTailoringWorkspaceSelectedCandidateIds(),
    }
  );

  updateTailoringWorkspaceMetaSummary(getTailoringWorkspacePayload());
}

function initializeTailoringWorkspaceSelectionState(artifact) {
  tailoringWorkspaceState.artifact = artifact;

  const payload =
    artifact && artifact.kind === "json" && artifact.data && typeof artifact.data === "object"
      ? artifact.data
      : null;

  if (!payload) {
    tailoringWorkspaceState.selectedCandidateIds = [];
    tailoringWorkspaceState.candidateLookup = new Map();
    return;
  }

  tailoringWorkspaceState.candidateLookup = buildTailoringWorkspaceCandidateLookup(payload);

  const selectionStatus = String(payload.selected_patch_selection_status || "").trim().toLowerCase();

  const initialSelectedIds =
    selectionStatus === "applied"
      ? (Array.isArray(payload.selected_patch_candidate_ids) ? payload.selected_patch_candidate_ids : [])
      : [];

  tailoringWorkspaceState.selectedCandidateIds = normalizeTailoringWorkspaceSelectedCandidateIds(
    payload,
    initialSelectedIds
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

  rerenderTailoringWorkspaceSelectionView();
  syncTailoringWorkspacePreviewHighlight();
}

function bindTailoringWorkspaceSelectionHandlers() {
  const root = qs("tailoringWorkspaceInteractiveSummary");
  if (!root || root.dataset.selectionBound === "true") return;

  root.dataset.selectionBound = "true";

  root.addEventListener("click", (event) => {
    const button = event.target.closest("[data-tailoring-select-candidate]");
    if (!button) return;

    event.preventDefault();
    toggleTailoringWorkspaceCandidateSelection(button.dataset.tailoringSelectCandidate || "");
  });
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
}) {
  const safeItems = Array.isArray(items) ? items : [];
  const selectedSet = new Set(
    (Array.isArray(selectedCandidateIds) ? selectedCandidateIds : [])
      .map((value) => String(value || "").trim())
      .filter(Boolean)
  );

  if (!safeItems.length) {
    return `
      <section class="tailoring-section-block">
        <div class="tailoring-section-title">${escapeHtml(title)}</div>
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
        ${safeItems.map((item, index) => {
          const priority = String(item.apply_priority || "low");
          const likelyImpactedDimensions = Array.isArray(item.likely_impacted_dimensions)
            ? item.likely_impacted_dimensions.filter(Boolean)
            : [];

          const candidateId = mode === "replacement" ? getTailoringReplacementCandidateId(item) : "";
          const isSelectable = Boolean(selectionEnabled && mode === "replacement" && candidateId);
          const isSelected = Boolean(isSelectable && selectedSet.has(candidateId));

          const statusLabel =
            item.replacement_status === "direct_apply_ready"
              ? "Ready to use"
              : item.replacement_status === "direct_apply_optional"
                ? "Nice to improve"
                : "Review only";

          return `
            <article class="tailoring-edit-card ${isSelected ? "tailoring-edit-card--selected" : ""}">
              <div class="tailoring-card-topline">
                <div class="tailoring-edit-card-label">Suggestion ${index + 1}</div>
                <div class="tailoring-chip-group">
                  ${buildTailoringTonePill(statusLabel, tone)}
                  ${buildTailoringTonePill(
                    priority === "high" ? "High priority" : priority === "medium" ? "Medium priority" : "Low priority",
                    priority === "high" ? "safe" : priority === "medium" ? "caution" : "muted"
                  )}
                </div>
              </div>

              ${item.original_text ? `
                <div class="tailoring-info-block">
                  <div class="tailoring-info-label">Current bullet</div>
                  <div class="tailoring-quote-block">${escapeHtml(item.original_text)}</div>
                </div>
              ` : ""}

              ${mode !== "direction_only" && item.final_replacement_text ? `
                <div class="tailoring-info-block">
                  <div class="tailoring-info-label">Suggested edit</div>
                  <div class="tailoring-rewrite-callout">${escapeHtml(item.final_replacement_text)}</div>
                </div>
              ` : ""}

              ${mode === "direction_only" && item.rewrite_direction ? `
                <div class="tailoring-info-block">
                  <div class="tailoring-info-label">Suggested change</div>
                  <div class="tailoring-rewrite-callout">${escapeHtml(item.rewrite_direction)}</div>
                </div>
              ` : ""}

              ${item.why_selected ? `
                <div class="tailoring-info-row">
                  <span class="tailoring-info-label">Why this helps</span>
                  <span class="tailoring-info-value">${escapeHtml(item.why_selected)}</span>
                </div>
              ` : ""}

              ${likelyImpactedDimensions.length ? `
                <div class="tailoring-info-row">
                  <span class="tailoring-info-label">What this improves</span>
                  <span class="tailoring-info-value">${escapeHtml(
                    likelyImpactedDimensions.map((value) => humanizeUnderscoreLabel(value)).join(", ")
                  )}</span>
                </div>
              ` : ""}

              ${isSelectable ? `
                <div class="tailoring-card-actions">
                  <button
                    type="button"
                    class="ghost-btn btn-sm tailoring-select-btn ${isSelected ? "is-selected" : ""}"
                    data-tailoring-select-candidate="${escapeHtml(candidateId)}"
                  >
                    ${isSelected ? "Selected" : "Select"}
                  </button>
                </div>
              ` : ""}
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

function renderTailoringInteractiveSummaryInto(
  rootId,
  artifact,
  { includeDiagnostics = true, selectionEnabled = false, selectedCandidateIds = [] } = {}
) {
  const root = qs(rootId);
  if (!root) return;

  const payload = artifact && artifact.kind === "json" && artifact.data && typeof artifact.data === "object"
    ? artifact.data
    : null;

  if (!payload) {
    root.innerHTML = `<div class="tailoring-empty-state">Suggested changes are not available for this row.</div>`;
    return;
  }

  const summary = payload.final_replacement_summary || {};
  const appReady = Array.isArray(payload.app_ready_replacements) ? payload.app_ready_replacements : [];
  const directApplyOptional = Array.isArray(payload.direct_apply_optional_replacements)
    ? payload.direct_apply_optional_replacements
    : [];
  const directionOnly = Array.isArray(payload.direction_only_replacements) ? payload.direction_only_replacements : [];
  const decisions = Array.isArray(payload.final_replacement_decisions) ? payload.final_replacement_decisions : [];

  const hasReplacementPlan =
    decisions.length ||
    appReady.length ||
    directApplyOptional.length ||
    directionOnly.length;

  if (!hasReplacementPlan) {
    root.innerHTML = renderTailoringEmptyState(payload);
    return;
  }

  const recommendedHtml = Array.isArray(directionOnly) && directionOnly.length
    ? renderReplacementDecisionSection({
        title: "Recommended changes",
        subtitle: "These are the main edits to review first.",
        items: directionOnly,
        emptyLabel: "No review-only suggestions.",
        tone: "muted",
        mode: "direction_only",
      })
    : "";

  const readyHtml = Array.isArray(appReady) && appReady.length
    ? renderReplacementDecisionSection({
        title: "Ready to use",
        subtitle: "These edits are ready to use as written.",
        items: appReady,
        emptyLabel: "No ready-to-use edits.",
        tone: "safe",
        mode: "replacement",
        selectionEnabled,
        selectedCandidateIds,
      })
    : "";

  const optionalHtml = Array.isArray(directApplyOptional) && directApplyOptional.length
    ? renderReplacementDecisionSection({
        title: "Nice to improve",
        subtitle: "These are safe wording improvements, but not the main fit drivers.",
        items: directApplyOptional,
        emptyLabel: "No optional improvements.",
        tone: "caution",
        mode: "replacement",
        selectionEnabled,
        selectedCandidateIds,
      })
    : "";

  const diagnosticsHtml = includeDiagnostics
    ? renderLegacyDiagnosticDetails(payload)
    : "";

  root.innerHTML = `
    ${renderReplacementPlanSummary(summary)}
    ${recommendedHtml}
    ${readyHtml}
    ${optionalHtml}
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
    tailoringWorkspaceState.selectedCandidateIds = [];
    tailoringWorkspaceState.candidateLookup = new Map();

    await previewPromise;
    return true;
  }

  try {
    if (meta) {
      meta.textContent = "Loading action-first suggestion set...";
    }

    const tailoringJsonArtifact = await loadArtifact(tailoringJsonPath);

    initializeTailoringWorkspaceSelectionState(tailoringJsonArtifact);
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
    tailoringWorkspaceState.selectedCandidateIds = [];
    tailoringWorkspaceState.candidateLookup = new Map();

    console.error("Failed to initialize tailoring workspace", err);
  }

  return true;
}

function buildTailoringWorkspaceUrl(row) {
  const params = new URLSearchParams();

  const selectedResume =
    normalizeResumeName(row.operator_selected_resume) ||
    normalizeResumeName(row.winner_resume);

  params.set("company", row.job_company || "");
  params.set("title", row.job_title || "");
  params.set("resume", selectedResume || "");
  params.set(
    "status",
    row.llm_tailoring_status
      ? humanizeUnderscoreLabel(row.llm_tailoring_status)
      : "Suggestions available"
  );

  if (row.job_doc_id) params.set("job_doc_id", row.job_doc_id);
  if (row.tailoring_json) params.set("tailoring_json", row.tailoring_json);
  if (row.tailoring_md) params.set("tailoring_md", row.tailoring_md);
  if (row.tailoring_llm_json) params.set("tailoring_llm_json", row.tailoring_llm_json);
  if (row.packet_json) params.set("packet_json", row.packet_json);

  return `/tailoring-workspace?${params.toString()}`;
}

function buildTailoringButtonHtml(row) {
  const hasArtifacts = Boolean(
    row.tailoring_json || row.tailoring_md || row.tailoring_llm_json || row.packet_json
  );
  const label = hasArtifacts ? "Open Workspace" : "Unavailable";
  const disabledAttr = hasArtifacts ? "" : "disabled";

  return `
    <button
      type="button"
      class="ghost-btn"
      ${disabledAttr}
      data-view-tailoring="true"
      data-job-doc-id="${escapeHtml(row.job_doc_id || "")}"
      data-job-company="${escapeHtml(row.job_company || "")}"
      data-job-title="${escapeHtml(row.job_title || "")}"
      data-winner-resume="${escapeHtml(row.winner_resume || "")}"
      data-operator-selected-resume="${escapeHtml(row.operator_selected_resume || "")}"
      data-llm-tailoring-status="${escapeHtml(row.llm_tailoring_status || "")}"
      data-tailoring-json="${escapeHtml(row.tailoring_json || "")}"
      data-tailoring-md="${escapeHtml(row.tailoring_md || "")}"
      data-tailoring-llm-json="${escapeHtml(row.tailoring_llm_json || "")}"
      data-packet-json="${escapeHtml(row.packet_json || "")}"
    >
      ${label}
    </button>
  `;
}

async function handleTailoringClick(button) {
  const row = {
    job_doc_id: button.dataset.jobDocId || "",
    job_company: button.dataset.jobCompany || "",
    job_title: button.dataset.jobTitle || "",
    winner_resume: button.dataset.winnerResume || "",
    operator_selected_resume: button.dataset.operatorSelectedResume || "",
    llm_tailoring_status: button.dataset.llmTailoringStatus || "",
    tailoring_json: button.dataset.tailoringJson || "",
    tailoring_md: button.dataset.tailoringMd || "",
    tailoring_llm_json: button.dataset.tailoringLlmJson || "",
    packet_json: button.dataset.packetJson || "",
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

function renderPlanningRows(rows, metaLabel) {
  planningTableState.rows = Array.isArray(rows) ? rows.slice() : [];
  planningTableState.metaLabel = metaLabel;

  const tbody = qs("planningTableBody");
  const displayRows = sortRows(planningTableState.rows, PLANNING_SORT_COLUMNS, planningTableState.sort);

  if (!displayRows.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="20" class="empty-state">No rows found.</td>
      </tr>
    `;
    qs("planningTableMeta").textContent = planningTableState.metaLabel;
    updatePlanningStats(0);
    renderSortableHeaders("planningTable", PLANNING_SORT_COLUMNS, planningTableState.sort);
    return;
  }

  tbody.innerHTML = displayRows.map((row) => {
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
              <td class="title-cell">
          <div>${titleHtml}</div>
        </td>
        <td>${buildDateTimeCellHtml(row.posted_at)}</td>
        <td>${buildCompactTextHtml(row.winner_resume, { maxLength: 34 })}</td>
        <td>${escapeHtml(formatScore100(row.winner_score))}</td>
        <td>${buildCompactTextHtml(row.runner_up_resume, { maxLength: 34 })}</td>
        <td>${escapeHtml(formatScore100(row.runner_up_score))}</td>
        <td>${escapeHtml(formatScore100(row.score_gap))}</td>
        <td>${buildMatchStrengthHtml(row)}</td>
        <td>${buildReviewStateHtml(row)}</td>
        <td>${escapeHtml(row.missing_requirement_count || "")}</td>
        <td>${buildFallbackResumeHtml(row)}</td>
        <td>${escapeHtml(humanizeFallbackStatus(row.llm_fallback_status || ""))}</td>
        <td>${buildOperatorDecisionCellHtml(row)}</td>
        <td>${buildCompactTextHtml(row.operator_selected_resume, { maxLength: 28, emptyLabel: "-" })}</td>
        <td class="reason-cell">${buildReasonHtml(row.queue_priority_reason)}</td>
        <td>${buildTailoringButtonHtml(row)}</td>
        <td class="apply-cell sticky-apply-col">${buildApplicationButtonHtml(row)}</td>
      </tr>
    `;
  }).join("");

  qs("planningTableMeta").textContent = planningTableState.metaLabel;
  updatePlanningStats(displayRows.length);
  renderSortableHeaders("planningTable", PLANNING_SORT_COLUMNS, planningTableState.sort);
}

async function loadPlanningTable() {
  const tbody = qs("planningTableBody");
  tbody.innerHTML = renderTableLoading(20, "Loading planning rows...");
  qs("planningTableMeta").textContent = "Loading...";

  const url = buildPlanningUrl();
  const data = await fetchJson(url);
  const count = data.count ?? 0;

  renderPlanningRows(
    data.rows || [],
    `Planning detail view · ${count} row${count === 1 ? "" : "s"}`
  );
}

function clearPlanningFilters() {
  clearMultiSelect("planningActionFilter");
  clearMultiSelect("planningWinnerBucket");

  const defaultUndecided = document.querySelector("input[name='planningUndecidedOnlyToggle'][value='no']");
  if (defaultUndecided) {
    defaultUndecided.checked = true;
  }

  qs("planningLimitInput").value = "50";
  updatePlanningStats(0);
}

function attachPlanningHandlers() {
  initMultiSelect("planningActionFilter");
  initMultiSelect("planningWinnerBucket");
  qs("planningApplyFiltersBtn").addEventListener("click", async () => {
    try {
      await loadPlanningTable();
    } catch (err) {
      showAppError("Failed to load planning table", err);
    }
  });

  qs("planningClearFiltersBtn").addEventListener("click", async () => {
    clearPlanningFilters();
    try {
      await loadPlanningTable();
    } catch (err) {
      showAppError("Failed to reload planning table", err);
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
    setResumeChoicePreview(choiceButton.dataset.resumeName || "");
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

  window.addEventListener("focus", () => {
    const pending = loadPendingApplicationFromStorage();
    if (!pending || !getApplicationModal().classList.contains("hidden")) return;
    openApplicationModal(pending);
  });
}

window.addEventListener("DOMContentLoaded", async () => {
  const isPlanningPage = Boolean(qs("planningTable"));
  const isTailoringWorkspacePage = Boolean(document.querySelector(".tailoring-workspace-page"));

  if (isPlanningPage) {
    bindAppErrorModal();
    attachPlanningHandlers();
    bindTableSorting("planningTable", PLANNING_SORT_COLUMNS, planningTableState.sort, () => {
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
    await initTailoringWorkspacePage();
  }
});