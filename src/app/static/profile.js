const profileState = {
  pendingDeleteResumeName: null,
  pendingDeleteScanId: null,
};

function qs(id) {
  return document.getElementById(id);
}

function escapeHtml(value) {
  if (value === null || value === undefined) return "";
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);

  if (!response.ok) {
    let message = `HTTP ${response.status}`;
    try {
      const data = await response.json();
      message = data.detail || data.message || message;
    } catch {
      const text = await response.text();
      if (text) message = text;
    }
    throw new Error(message);
  }

  return response.json();
}

function formatBytes(bytes) {
  const value = Number(bytes || 0);
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(2)} MB`;
}

function formatDateTime(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

function formatPercent(value) {
  if (value === null || value === undefined || value === "") return "-";
  const number = Number(value);
  if (!Number.isFinite(number)) return "-";
  return `${Math.round(number)}%`;
}

function setStatus(message, tone = "info") {
  const banner = qs("resumeStatusBanner");
  banner.textContent = message || "";
  banner.className = `profile-inline-status ${tone}`;
  if (!message) {
    banner.classList.add("hidden");
  }
}

function clearStatus() {
  const banner = qs("resumeStatusBanner");
  banner.textContent = "";
  banner.className = "profile-inline-status hidden";
}

function getResumeDeleteModal() {
  return qs("resumeDeleteModal");
}

function openResumeDeleteModal(resumeName) {
  profileState.pendingDeleteResumeName = resumeName || "";
  qs("resumeDeleteModalName").textContent = resumeName || "-";
  getResumeDeleteModal().classList.remove("hidden");
}

function closeResumeDeleteModal() {
  profileState.pendingDeleteResumeName = null;
  qs("resumeDeleteModalName").textContent = "-";
  getResumeDeleteModal().classList.add("hidden");
}

function renderResumeList(items) {
  const listEl = qs("resumeList");
  const metaEl = qs("resumeListMeta");
  const resumes = Array.isArray(items) ? items : [];

  metaEl.textContent = `${resumes.length} resume${resumes.length === 1 ? "" : "s"} available`;

  if (!resumes.length) {
    listEl.innerHTML = `
      <div class="resume-empty-state">
        No resumes uploaded yet.
      </div>
    `;
    return;
  }

  listEl.innerHTML = resumes.map((resume) => `
    <article class="resume-row">
      <div class="resume-row-main">
        <div class="resume-name">${escapeHtml(resume.resume_name || "")}</div>
        <div class="resume-meta">
          <span>${escapeHtml(formatBytes(resume.size_bytes || 0))}</span>
          <span>•</span>
          <span>${escapeHtml(formatDateTime(resume.modified_at || ""))}</span>
        </div>
      </div>

      <div class="resume-row-actions">
        <button
          type="button"
          class="ghost-btn resume-delete-btn"
          data-resume-delete="${escapeHtml(resume.resume_name || "")}"
        >
          Delete
        </button>
      </div>
    </article>
  `).join("");
}

async function loadResumes() {
  const listEl = qs("resumeList");
  const metaEl = qs("resumeListMeta");

  metaEl.textContent = "Loading resumes...";
  listEl.innerHTML = `<div class="resume-empty-state">Loading...</div>`;

  const data = await fetchJson("/profile/resumes");
  renderResumeList(data.resumes || []);
}

function normalizeSavedScanSource(value) {
  const source = String(value || "").trim();
  if (source === "saved_resume") return "Saved resume";
  if (source === "uploaded_file") return "Uploaded file";
  if (source === "pasted_text") return "Pasted text";
  return source || "-";
}

function savedScanStatusMeta(value) {
  const rawStatus = String(value || "").trim();
  const status = rawStatus.toLowerCase();

  if (status === "report_pending" || status === "intake_saved") {
    return {
      label: "Report pending",
      tone: "pending",
      action: "Saved intake only",
    };
  }

  if (status === "processing") {
    return {
      label: "Processing",
      tone: "processing",
      action: "Processing",
    };
  }

  if (status === "ready" || status === "complete") {
    return {
      label: "Ready",
      tone: "ready",
      action: "Report generated",
    };
  }

  if (status === "failed") {
    return {
      label: "Failed",
      tone: "failed",
      action: "Unavailable",
    };
  }

  return {
    label: rawStatus || "-",
    tone: "muted",
    action: "Not openable",
  };
}

function getSavedScanOpenHref(scan) {
  const status = String(scan?.scan_status || "").trim().toLowerCase();
  const scanId = String(scan?.scan_id || "").trim();
  if (!scanId || (status !== "ready" && status !== "complete")) return "";
  return `/scan-workspace?saved_scan_id=${encodeURIComponent(scanId)}`;
}

function openSavedScanDeleteModal(scan) {
  profileState.pendingDeleteScanId = String(scan?.scan_id || "").trim();
  const label = [
    scan?.job_company || "",
    scan?.job_title || "",
    scan?.resume_name || scan?.resume_filename || "",
  ].filter(Boolean).join(" / ") || "this saved scan";
  qs("savedScanDeleteName").textContent = label;
  qs("savedScanDeleteModal").classList.remove("hidden");
}

function closeSavedScanDeleteModal() {
  profileState.pendingDeleteScanId = null;
  const name = qs("savedScanDeleteName");
  if (name) name.textContent = "this saved scan";
  qs("savedScanDeleteModal")?.classList.add("hidden");
}

function renderSavedScans(items, { ok = true, error = "" } = {}) {
  const tbody = qs("savedScansTableBody");
  const metaEl = qs("savedScansMeta");
  const scans = Array.isArray(items) ? items : [];

  if (!ok) {
    metaEl.textContent = "Saved scans unavailable";
    tbody.innerHTML = `
      <tr>
        <td colspan="9" class="saved-scans-empty-cell">
          ${escapeHtml(error || "Could not load saved scans from Postgres.")}
        </td>
      </tr>
    `;
    return;
  }

  metaEl.textContent = `${scans.length} saved scan${scans.length === 1 ? "" : "s"} shown`;

  if (!scans.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="9" class="saved-scans-empty-cell">
          No saved scans yet.
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = scans.map((scan) => {
    const statusMeta = savedScanStatusMeta(scan.scan_status);

    return `
      <tr class="saved-scan-row saved-scan-row-${escapeHtml(statusMeta.tone)}" data-saved-scan-id="${escapeHtml(scan.scan_id || "")}">
        <td>${escapeHtml(formatDateTime(scan.scan_timestamp || ""))}</td>
        <td>${escapeHtml(scan.job_company || "-")}</td>
        <td>${escapeHtml(scan.job_title || "-")}</td>
        <td>${escapeHtml(scan.resume_name || scan.resume_filename || "-")}</td>
        <td>${escapeHtml(normalizeSavedScanSource(scan.resume_source))}</td>
        <td>
          <span class="saved-scan-status-badge ${escapeHtml(statusMeta.tone)}">
            ${escapeHtml(statusMeta.label)}
          </span>
        </td>
        <td>${escapeHtml(formatPercent(scan.match_rate))}</td>
        <td>
          ${getSavedScanOpenHref(scan)
            ? `<a class="saved-scan-action-badge ${escapeHtml(statusMeta.tone)} saved-scan-open-link" href="${escapeHtml(getSavedScanOpenHref(scan))}">${escapeHtml(statusMeta.action)}</a>`
            : `<span class="saved-scan-action-badge ${escapeHtml(statusMeta.tone)}">${escapeHtml(statusMeta.action)}</span>`}
        </td>
        <td class="saved-scan-row-delete-cell">
          <button
            type="button"
            class="saved-scan-delete-btn"
            aria-label="Delete saved scan"
            title="Delete saved scan"
            data-saved-scan-delete="${escapeHtml(scan.scan_id || "")}"
            data-saved-scan-name="${escapeHtml(scan.resume_name || scan.resume_filename || "saved scan")}"
          ></button>
        </td>
      </tr>
    `;
  }).join("");
}

async function loadSavedScans() {
  const tbody = qs("savedScansTableBody");
  const metaEl = qs("savedScansMeta");
  if (!tbody || !metaEl) return;

  metaEl.textContent = "Loading saved scans...";
  tbody.innerHTML = `
    <tr>
      <td colspan="9" class="saved-scans-empty-cell">Loading saved scans...</td>
    </tr>
  `;

  const data = await fetchJson("/profile/saved-scans/data?limit=50");
  renderSavedScans(data.saved_scans || [], {
    ok: data.ok !== false,
    error: data.error || "",
  });
}

async function deleteSavedScan() {
  const scanId = String(profileState.pendingDeleteScanId || "").trim();
  if (!scanId) return;

  await fetchJson(`/profile/saved-scans/${encodeURIComponent(scanId)}`, {
    method: "DELETE",
  });
  closeSavedScanDeleteModal();
  await loadSavedScans();
}

function validateResumeFile(file) {
  if (!file) {
    throw new Error("No file selected.");
  }

  const name = String(file.name || "").trim();
  if (!name) {
    throw new Error("File name is missing.");
  }

  if (!name.toLowerCase().endsWith(".pdf")) {
    throw new Error("Only PDF resumes are supported.");
  }
}

async function uploadResumeFile(file) {
  validateResumeFile(file);

  await fetchJson(`/profile/resumes/upload?filename=${encodeURIComponent(file.name)}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/pdf",
    },
    body: file,
  });

  return file.name;
}

async function uploadResumeFiles(files) {
  const fileList = Array.from(files || []);
  if (!fileList.length) {
    throw new Error("No files selected.");
  }

  const results = {
    uploaded: [],
    failed: [],
  };

  setStatus(`Uploading ${fileList.length} file${fileList.length === 1 ? "" : "s"}...`, "info");

  for (const file of fileList) {
    try {
      validateResumeFile(file);
      await uploadResumeFile(file);
      results.uploaded.push(file.name);
    } catch (err) {
      results.failed.push({
        name: file?.name || "unknown file",
        error: err.message,
      });
    }
  }

  await loadResumes();

  if (results.uploaded.length && !results.failed.length) {
    setStatus(
      `Uploaded ${results.uploaded.length} file${results.uploaded.length === 1 ? "" : "s"} successfully.`,
      "success"
    );
    return;
  }

  if (results.uploaded.length && results.failed.length) {
    setStatus(
      `Uploaded ${results.uploaded.length} file${results.uploaded.length === 1 ? "" : "s"}, failed ${results.failed.length}.`,
      "error"
    );
    return;
  }

  const firstError = results.failed[0]?.error || "Upload failed.";
  throw new Error(firstError);
}

async function deleteResume(resumeName) {
  if (!resumeName) return;

  setStatus(`Deleting ${resumeName}...`, "info");

  await fetchJson(`/profile/resumes/${encodeURIComponent(resumeName)}`, {
    method: "DELETE",
  });

  setStatus(`Deleted ${resumeName}.`, "success");
  await loadResumes();
}

function bindUploadInteractions() {
  const dropzone = qs("resumeDropzone");
  const input = qs("resumeUploadInput");
  const browseBtn = qs("resumeBrowseBtn");

  browseBtn.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    input.click();
  });

  input.addEventListener("change", async () => {
    const files = Array.from(input.files || []);
    if (!files.length) return;

    try {
      await uploadResumeFiles(files);
    } catch (err) {
      setStatus(err.message, "error");
    } finally {
      input.value = "";
    }
  });

  ["dragenter", "dragover"].forEach((eventName) => {
    dropzone.addEventListener(eventName, (event) => {
      event.preventDefault();
      event.stopPropagation();
      dropzone.classList.add("drag-active");
    });
  });

  ["dragleave", "dragend", "drop"].forEach((eventName) => {
    dropzone.addEventListener(eventName, (event) => {
      event.preventDefault();
      event.stopPropagation();
      dropzone.classList.remove("drag-active");
    });
  });

  dropzone.addEventListener("drop", async (event) => {
  const files = Array.from(event.dataTransfer?.files || []);
  if (!files.length) return;

  try {
    await uploadResumeFiles(files);
  } catch (err) {
    setStatus(err.message, "error");
  }
});

  dropzone.addEventListener("click", (event) => {
    if (event.target.closest("#resumeBrowseBtn")) {
      return;
    }
    input.click();
  });

  dropzone.addEventListener("keydown", (event) => {
    if (event.target !== dropzone) {
      return;
    }

    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      input.click();
    }
  });
}

function bindDeleteInteractions() {
  qs("resumeList").addEventListener("click", (event) => {
    const button = event.target.closest("[data-resume-delete]");
    if (!button) return;

    const resumeName = button.dataset.resumeDelete || "";
    openResumeDeleteModal(resumeName);
  });

  qs("closeResumeDeleteModalBtn").addEventListener("click", closeResumeDeleteModal);
  qs("resumeDeleteCancelBtn").addEventListener("click", closeResumeDeleteModal);

  qs("resumeDeleteConfirmBtn").addEventListener("click", async () => {
    const resumeName = profileState.pendingDeleteResumeName || "";
    if (!resumeName) {
      closeResumeDeleteModal();
      return;
    }

    try {
      await deleteResume(resumeName);
      closeResumeDeleteModal();
    } catch (err) {
      setStatus(err.message, "error");
      closeResumeDeleteModal();
    }
  });

  getResumeDeleteModal().addEventListener("click", (event) => {
    if (event.target === getResumeDeleteModal()) {
      closeResumeDeleteModal();
    }
  });
}

function bindSavedScansPage() {
  const refreshBtn = qs("refreshSavedScansBtn");
  if (refreshBtn) {
    refreshBtn.addEventListener("click", () => {
      loadSavedScans().catch((err) => {
        renderSavedScans([], { ok: false, error: err.message });
      });
    });
  }

  const tbody = qs("savedScansTableBody");
  if (tbody) {
    tbody.addEventListener("click", (event) => {
      const deleteBtn = event.target.closest("[data-saved-scan-delete]");
      if (!deleteBtn) return;
      event.preventDefault();
      event.stopPropagation();
      const row = deleteBtn.closest("[data-saved-scan-id]");
      const scanId = deleteBtn.dataset.savedScanDelete || row?.dataset?.savedScanId || "";
      const scan = {
        scan_id: scanId,
        resume_name: deleteBtn.dataset.savedScanName || "",
        job_company: row?.children?.[1]?.textContent || "",
        job_title: row?.children?.[2]?.textContent || "",
      };
      openSavedScanDeleteModal(scan);
    });
  }

  qs("savedScanDeleteCloseBtn")?.addEventListener("click", closeSavedScanDeleteModal);
  qs("savedScanDeleteCancelBtn")?.addEventListener("click", closeSavedScanDeleteModal);
  qs("savedScanDeleteConfirmBtn")?.addEventListener("click", async () => {
    try {
      await deleteSavedScan();
    } catch (err) {
      renderSavedScans([], { ok: false, error: err.message });
      closeSavedScanDeleteModal();
    }
  });
  qs("savedScanDeleteModal")?.addEventListener("click", (event) => {
    if (event.target === qs("savedScanDeleteModal")) {
      closeSavedScanDeleteModal();
    }
  });

  return loadSavedScans();
}

function isSavedScansPage() {
  return Boolean(qs("savedScansTableBody"));
}

function isProfileResumePage() {
  return Boolean(qs("resumeList"));
}

async function initProfilePage() {
  try {
    if (isSavedScansPage()) {
      await bindSavedScansPage();
      return;
    }

    if (isProfileResumePage()) {
      clearStatus();
      bindUploadInteractions();
      bindDeleteInteractions();
      await loadResumes();
    }
  } catch (err) {
    if (isSavedScansPage()) {
      renderSavedScans([], { ok: false, error: err.message });
    } else {
      setStatus(`Failed to load resumes: ${err.message}`, "error");
    }
  }
}

window.addEventListener("DOMContentLoaded", initProfilePage);
