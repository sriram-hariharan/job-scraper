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

const APPLICATION_TAB_CONFIG = {
  APPLIED: {
    endpoint: "/applied-jobs",
    pageLabel: "Applied Jobs",
    emptyLabel: "No applied jobs yet.",
    statLabel: "Applied",
  },
  SAVED: {
    endpoint: "/application-actions",
    pageLabel: "Saved for Later",
    emptyLabel: "No saved jobs yet.",
    statLabel: "Saved",
    applicationStatus: "SAVED",
  },
};

const APPLICATION_SORT_COLUMNS = [
  { key: "action_timestamp", label: "Date / Time", type: "date" },
  { key: "job_company", label: "Company", type: "text" },
  { key: "job_title", label: "Title", type: "text" },
  { key: "application_status", label: "Status", type: "text" },
  { key: "source_view", label: "Source View", type: "text" },
  { key: "note", label: "Note", type: "text" },
  { key: "open", label: "Open", sortable: false },
];

let currentApplicationTab = "APPLIED";

const applicationTableState = {
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
};

function getCurrentApplicationConfig() {
  return APPLICATION_TAB_CONFIG[currentApplicationTab];
}

function buildApplicationListUrl() {
  const config = getCurrentApplicationConfig();
  const companyContains = qs("applicationCompanyFilter").value.trim();
  const titleContains = qs("applicationTitleFilter").value.trim();
  const limit = qs("applicationLimitInput").value || "15";
  const page = applicationTableState.pagination.page || 1;

  const params = new URLSearchParams();
  if (config.applicationStatus) params.set("application_status", config.applicationStatus);
  if (companyContains) params.set("company_contains", companyContains);
  if (titleContains) params.set("title_contains", titleContains);
  params.set("limit", limit);
  params.set("page", String(page));

  return `${config.endpoint}?${params.toString()}`;
}

function updateApplicationViewStats(rowCount) {
  const config = getCurrentApplicationConfig();
  qs("applicationJobsShown").textContent = String(rowCount ?? 0);
  qs("applicationViewLabel").textContent = config.statLabel;
  qs("applicationTableTitle").textContent = config.pageLabel;
}

function setApplicationRequestedPage(page) {
  const parsed = Number(page);
  applicationTableState.pagination.page = Number.isFinite(parsed) && parsed > 0 ? Math.floor(parsed) : 1;
}

function buildApplicationPaginationSequence(currentPage, totalPages) {
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

function renderApplicationPagination() {
  const metaEl = qs("applicationPaginationMeta");
  const actionsEl = qs("applicationPaginationActions");
  if (!metaEl || !actionsEl) return;

  const {
    page,
    pageSize,
    totalCount,
    totalPages,
    hasPrevPage,
    hasNextPage,
  } = applicationTableState.pagination;

  if (!totalCount) {
    metaEl.textContent = "Page 1 of 1 · 0 jobs";
    actionsEl.innerHTML = "";
    return;
  }

  const startRow = (page - 1) * pageSize + 1;
  const endRow = Math.min(page * pageSize, totalCount);

  metaEl.textContent = `Page ${page} of ${totalPages} · Showing ${startRow}-${endRow} of ${totalCount} jobs`;

  const sequence = buildApplicationPaginationSequence(page, totalPages);

  actionsEl.innerHTML = `
    <button
      type="button"
      class="ghost-btn application-pagination-btn"
      data-application-page="${page - 1}"
      ${hasPrevPage ? "" : "disabled"}
    >
      Prev
    </button>

    ${sequence.map((item) => {
      if (typeof item !== "number") {
        return `<span class="application-pagination-ellipsis">…</span>`;
      }

      return `
        <button
          type="button"
          class="ghost-btn application-pagination-btn ${item === page ? "is-active" : ""}"
          data-application-page="${item}"
          ${item === page ? "disabled" : ""}
        >
          ${item}
        </button>
      `;
    }).join("")}

    <button
      type="button"
      class="ghost-btn application-pagination-btn"
      data-application-page="${page + 1}"
      ${hasNextPage ? "" : "disabled"}
    >
      Next
    </button>
  `;
}

function setActiveApplicationTab(tabKey) {
  currentApplicationTab = tabKey;
  setApplicationRequestedPage(1);

  document.querySelectorAll("[data-app-tab]").forEach((btn) => {
    const isActive = btn.dataset.appTab === tabKey;
    btn.classList.toggle("active", isActive);
  });

  updateApplicationViewStats(0);
}

function renderApplicationRows(rows, metaLabel, emptyLabel) {
  applicationTableState.rows = Array.isArray(rows) ? rows.slice() : [];
  applicationTableState.metaLabel = metaLabel;

  const tbody = qs("applicationTableBody");
  const displayRows = sortRows(applicationTableState.rows, APPLICATION_SORT_COLUMNS, applicationTableState.sort);

  const table = tbody ? tbody.closest("table") : null;

  if (!displayRows.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="7" class="empty-state">${escapeHtml(emptyLabel)}</td>
      </tr>
    `;
    qs("applicationTableMeta").textContent = applicationTableState.metaLabel;
    updateApplicationViewStats(0);
    renderApplicationPagination();
    if (table) {
      renderSortableHeaders(table.id, APPLICATION_SORT_COLUMNS, applicationTableState.sort);
    }
    return;
  }

  tbody.innerHTML = displayRows.map((row) => {
    const title = escapeHtml(row.job_title || "");
    const jobUrl = escapeHtml(row.job_url || row.job_doc_id || "");
    const titleHtml = jobUrl
      ? `<a class="job-link" href="${jobUrl}" target="_blank" rel="noopener noreferrer">${title}</a>`
      : title;

    return `
      <tr>
        <td>${buildDateTimeCellHtml(row.action_timestamp)}</td>
        <td>${escapeHtml(row.job_company || "")}</td>
        <td class="title-cell">${titleHtml}</td>
        <td><span class="pill">${escapeHtml(row.application_status || "")}</span></td>
        <td>${escapeHtml(row.source_view || "")}</td>
        <td class="reason-cell">${escapeHtml(row.note || "")}</td>
        <td>${jobUrl ? `<a class="ghost-link-btn inline-open-link" href="${jobUrl}" target="_blank" rel="noopener noreferrer">Open</a>` : "-"}</td>
      </tr>
    `;
  }).join("");

  qs("applicationTableMeta").textContent = applicationTableState.metaLabel;
  updateApplicationViewStats(displayRows.length);
  renderApplicationPagination();
  if (table) {
    renderSortableHeaders(table.id, APPLICATION_SORT_COLUMNS, applicationTableState.sort);
  }
}

async function loadApplicationView() {
  const config = getCurrentApplicationConfig();
  const tbody = qs("applicationTableBody");

  tbody.innerHTML = renderTableLoading(7, `Loading ${config.pageLabel.toLowerCase()}...`);
  qs("applicationTableMeta").textContent = "Loading...";
  qs("applicationTableTitle").textContent = config.pageLabel;

  const url = buildApplicationListUrl();
  const data = await fetchJson(url);

  const rawPageSize = data.page_size ?? 15;
  const parsedPageSize = Number(rawPageSize);
  const pageSize = Number.isFinite(parsedPageSize) && parsedPageSize > 0 ? parsedPageSize : 15;

  const totalCount = Number(data.total_count ?? data.count ?? 0);
  const totalPages = Number(data.total_pages ?? 1);
  const currentPage = Number(data.page ?? applicationTableState.pagination.page ?? 1);

  applicationTableState.pagination = {
    page: currentPage,
    pageSize,
    totalCount: Number.isFinite(totalCount) ? totalCount : 0,
    totalPages: Number.isFinite(totalPages) && totalPages > 0 ? totalPages : 1,
    hasPrevPage: Boolean(data.has_prev_page),
    hasNextPage: Boolean(data.has_next_page),
  };

  renderApplicationRows(
    data.rows || [],
    `${config.pageLabel} · ${totalCount} total job${totalCount === 1 ? "" : "s"}`,
    config.emptyLabel
  );
}

function clearApplicationFilters() {
  qs("applicationCompanyFilter").value = "";
  qs("applicationTitleFilter").value = "";
  qs("applicationLimitInput").value = "15";
  setApplicationRequestedPage(1);
}

window.addEventListener("DOMContentLoaded", async () => {
  bindAppErrorModal();

  const applicationTable = qs("applicationTableBody")?.closest("table");
  if (applicationTable && applicationTable.id) {
    bindTableSorting(applicationTable.id, APPLICATION_SORT_COLUMNS, applicationTableState.sort, () => {
      renderApplicationRows(
        applicationTableState.rows,
        applicationTableState.metaLabel,
        getCurrentApplicationConfig().emptyLabel
      );
    });
  }

  document.querySelectorAll("[data-app-tab]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const tabKey = btn.dataset.appTab;
      if (!tabKey || !APPLICATION_TAB_CONFIG[tabKey]) return;

      setActiveApplicationTab(tabKey);

      try {
        await loadApplicationView();
      } catch (err) {
        showAppError("Failed to load application view", err);
      }
    });
  });

  qs("applicationPaginationActions").addEventListener("click", async (event) => {
    const button = event.target.closest("[data-application-page]");
    if (!button || button.disabled) return;

    const nextPage = Number(button.dataset.applicationPage || "");
    if (!Number.isFinite(nextPage) || nextPage < 1) return;

    setApplicationRequestedPage(nextPage);

    try {
      await loadApplicationView();
    } catch (err) {
      showAppError("Failed to change application page", err);
    }
  });

  qs("applicationApplyFiltersBtn").addEventListener("click", async () => {
    setApplicationRequestedPage(1);
    try {
      await loadApplicationView();
    } catch (err) {
      showAppError("Failed to load application view", err);
    }
  });

  qs("applicationClearFiltersBtn").addEventListener("click", async () => {
    clearApplicationFilters();
    try {
      await loadApplicationView();
    } catch (err) {
      showAppError("Failed to reload application view", err);
    }
  });

  setActiveApplicationTab("APPLIED");

  try {
    await loadApplicationView();
  } catch (err) {
    showAppError("Failed to initialize application view", err);
  }
});