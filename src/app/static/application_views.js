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

let currentApplicationTab = "APPLIED";

function getCurrentApplicationConfig() {
  return APPLICATION_TAB_CONFIG[currentApplicationTab];
}

function buildApplicationListUrl() {
  const config = getCurrentApplicationConfig();
  const companyContains = qs("applicationCompanyFilter").value.trim();
  const titleContains = qs("applicationTitleFilter").value.trim();
  const limit = qs("applicationLimitInput").value || "50";

  const params = new URLSearchParams();
  if (config.applicationStatus) params.set("application_status", config.applicationStatus);
  if (companyContains) params.set("company_contains", companyContains);
  if (titleContains) params.set("title_contains", titleContains);
  params.set("limit", limit);

  return `${config.endpoint}?${params.toString()}`;
}

function updateApplicationViewStats(rowCount) {
  const config = getCurrentApplicationConfig();
  qs("applicationJobsShown").textContent = String(rowCount ?? 0);
  qs("applicationViewLabel").textContent = config.statLabel;
  qs("applicationTableTitle").textContent = config.pageLabel;
}

function setActiveApplicationTab(tabKey) {
  currentApplicationTab = tabKey;

  document.querySelectorAll("[data-app-tab]").forEach((btn) => {
    const isActive = btn.dataset.appTab === tabKey;
    btn.classList.toggle("active", isActive);
  });

  updateApplicationViewStats(0);
}

function renderApplicationRows(rows, metaLabel, emptyLabel) {
  const tbody = qs("applicationTableBody");
  const safeRows = Array.isArray(rows) ? rows : [];

  if (!safeRows.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="7" class="empty-state">${escapeHtml(emptyLabel)}</td>
      </tr>
    `;
    qs("applicationTableMeta").textContent = metaLabel;
    updateApplicationViewStats(0);
    return;
  }

  tbody.innerHTML = safeRows.map((row) => {
    const title = escapeHtml(row.job_title || "");
    const jobUrl = escapeHtml(row.job_url || row.job_doc_id || "");
    const titleHtml = jobUrl
      ? `<a class="job-link" href="${jobUrl}" target="_blank" rel="noopener noreferrer">${title}</a>`
      : title;

    return `
      <tr>
        <td>${escapeHtml(row.action_timestamp || "")}</td>
        <td>${escapeHtml(row.job_company || "")}</td>
        <td class="title-cell">${titleHtml}</td>
        <td><span class="pill">${escapeHtml(row.application_status || "")}</span></td>
        <td>${escapeHtml(row.source_view || "")}</td>
        <td class="reason-cell">${escapeHtml(row.note || "")}</td>
        <td>${jobUrl ? `<a class="ghost-link-btn inline-open-link" href="${jobUrl}" target="_blank" rel="noopener noreferrer">Open</a>` : "-"}</td>
      </tr>
    `;
  }).join("");

  qs("applicationTableMeta").textContent = metaLabel;
  updateApplicationViewStats(safeRows.length);
}

async function loadApplicationView() {
  const config = getCurrentApplicationConfig();
  const tbody = qs("applicationTableBody");

  tbody.innerHTML = renderTableLoading(7, `Loading ${config.pageLabel.toLowerCase()}...`);
  qs("applicationTableMeta").textContent = "Loading...";
  qs("applicationTableTitle").textContent = config.pageLabel;

  const url = buildApplicationListUrl();
  const data = await fetchJson(url);
  const count = data.count ?? 0;

  renderApplicationRows(
    data.rows || [],
    `${config.pageLabel} · ${count} row${count === 1 ? "" : "s"}`,
    config.emptyLabel
  );
}

function clearApplicationFilters() {
  qs("applicationCompanyFilter").value = "";
  qs("applicationTitleFilter").value = "";
  qs("applicationLimitInput").value = "50";
}

window.addEventListener("DOMContentLoaded", async () => {
  bindAppErrorModal();

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

  qs("applicationApplyFiltersBtn").addEventListener("click", async () => {
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