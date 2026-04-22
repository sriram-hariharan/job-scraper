const SCAN_WORKSPACE_MODES = ["new_scan", "processing", "review", "compare"];

const SCAN_WORKSPACE_PROCESSING_STAGES = [
  {
    key: "prepare",
    title: "Prepare request",
    description: "Validate the scan inputs and package the request payload.",
  },
  {
    key: "resume",
    title: "Load resume",
    description: "Resolve the saved resume or pasted resume content for scan processing.",
  },
  {
    key: "job_description",
    title: "Parse job description",
    description: "Normalize the pasted job description and extract scan-ready signals.",
  },
  {
    key: "review_payload",
    title: "Build review payload",
    description: "Generate the optimization review structure for the next screen.",
  },
];

const scanWorkspaceIntakeState = {
  company: "",
  role: "",
  resumeText: "",
  jobDescriptionText: "",
};

const scanWorkspaceProcessingState = {
  status: "idle",
  currentStageKey: "prepare",
  note: "",
  intakeDraft: null,
};

const scanWorkspacePreviewState = {
  documentPreviewPayload: null,
  isDocumentPreviewLoading: false,
  documentPreviewRequestSeq: 0,
};

const scanWorkspaceAnnotationState = {
  markers: [],
  activeMarkerId: "",
};

function getScanWorkspacePageRoot() {
  return document.querySelector(".scan-workspace-page");
}

function getScanWorkspaceModePanels() {
  return Array.from(document.querySelectorAll("[data-scan-mode-panel]"));
}

function getScanWorkspaceInput(id) {
  return document.getElementById(id);
}

function normalizeScanWorkspaceMode(mode) {
  const safeMode = String(mode || "").trim().toLowerCase();
  return SCAN_WORKSPACE_MODES.includes(safeMode) ? safeMode : "new_scan";
}

function getScanWorkspaceInitialMode() {
  const root = getScanWorkspacePageRoot();
  if (!root) return "new_scan";
  return normalizeScanWorkspaceMode(root.dataset.scanInitialMode || "new_scan");
}

function scanWorkspaceEscapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function getScanWorkspaceContext() {
  const root = getScanWorkspacePageRoot();
  if (!root) return null;

  return {
    tailoringJsonPath: String(root.dataset.tailoringJsonPath || "").trim(),
    resumeName: String(root.dataset.resumeName || "").trim(),
  };
}

function getScanWorkspaceHasPreselectedResume() {
  const root = getScanWorkspacePageRoot();
  if (!root) return false;
  return Boolean(String(root.dataset.resumeName || "").trim());
}

function setScanWorkspaceMode(nextMode) {
  const root = getScanWorkspacePageRoot();
  if (!root) return;

  const normalizedMode = normalizeScanWorkspaceMode(nextMode);
  root.dataset.scanMode = normalizedMode;

  getScanWorkspaceModePanels().forEach((panel) => {
    const panelMode = normalizeScanWorkspaceMode(panel.dataset.scanModePanel || "");
    const isActive = panelMode === normalizedMode;
    panel.hidden = !isActive;
    panel.classList.toggle("is-active", isActive);
  });

  if (normalizedMode === "processing") {
    updateScanWorkspaceProcessingView();
  }

  if (normalizedMode === "review") {
    renderScanWorkspaceAnnotationShell();
    ensureScanWorkspaceDocumentPreviewLoaded();
  }
}

function bindScanWorkspaceModeButtons() {
  document.querySelectorAll("[data-scan-switch-mode]").forEach((button) => {
    if (button.dataset.bound === "true") return;
    button.dataset.bound = "true";

    button.addEventListener("click", () => {
      const nextMode = button.dataset.scanSwitchMode || "new_scan";
      setScanWorkspaceMode(nextMode);
    });
  });
}

function readScanWorkspaceIntakeDraft() {
  const companyInput = getScanWorkspaceInput("scanWorkspaceCompanyInput");
  const roleInput = getScanWorkspaceInput("scanWorkspaceRoleInput");
  const resumeTextInput = getScanWorkspaceInput("scanWorkspaceResumeTextInput");
  const jobDescriptionInput = getScanWorkspaceInput("scanWorkspaceJobDescriptionInput");

  scanWorkspaceIntakeState.company = String(companyInput?.value || "").trim();
  scanWorkspaceIntakeState.role = String(roleInput?.value || "").trim();
  scanWorkspaceIntakeState.resumeText = String(resumeTextInput?.value || "").trim();
  scanWorkspaceIntakeState.jobDescriptionText = String(jobDescriptionInput?.value || "").trim();

  return { ...scanWorkspaceIntakeState };
}

function updateScanWorkspaceIntakeActions() {
  const startBtn = getScanWorkspaceInput("scanWorkspaceStartScanBtn");
  if (!startBtn) return;

  const draft = readScanWorkspaceIntakeDraft();
  const hasResume = getScanWorkspaceHasPreselectedResume() || Boolean(draft.resumeText);
  const hasJobDescription = Boolean(draft.jobDescriptionText);

  startBtn.disabled = !(hasResume && hasJobDescription);
}

function clearScanWorkspaceIntakeForm() {
  const companyInput = getScanWorkspaceInput("scanWorkspaceCompanyInput");
  const roleInput = getScanWorkspaceInput("scanWorkspaceRoleInput");
  const resumeTextInput = getScanWorkspaceInput("scanWorkspaceResumeTextInput");
  const jobDescriptionInput = getScanWorkspaceInput("scanWorkspaceJobDescriptionInput");

  if (companyInput) companyInput.value = "";
  if (roleInput) roleInput.value = "";
  if (resumeTextInput) resumeTextInput.value = "";
  if (jobDescriptionInput) jobDescriptionInput.value = "";

  scanWorkspaceIntakeState.company = "";
  scanWorkspaceIntakeState.role = "";
  scanWorkspaceIntakeState.resumeText = "";
  scanWorkspaceIntakeState.jobDescriptionText = "";

  updateScanWorkspaceIntakeActions();
}

function bindScanWorkspaceIntakeForm() {
  const watchedIds = [
    "scanWorkspaceCompanyInput",
    "scanWorkspaceRoleInput",
    "scanWorkspaceResumeTextInput",
    "scanWorkspaceJobDescriptionInput",
  ];

  watchedIds.forEach((id) => {
    const input = getScanWorkspaceInput(id);
    if (!input || input.dataset.bound === "true") return;

    input.dataset.bound = "true";
    input.addEventListener("input", () => {
      updateScanWorkspaceIntakeActions();
    });
  });

  const clearBtn = getScanWorkspaceInput("scanWorkspaceClearIntakeBtn");
  if (clearBtn && clearBtn.dataset.bound !== "true") {
    clearBtn.dataset.bound = "true";
    clearBtn.addEventListener("click", () => {
      clearScanWorkspaceIntakeForm();
    });
  }

  const startBtn = getScanWorkspaceInput("scanWorkspaceStartScanBtn");
  if (startBtn && startBtn.dataset.bound !== "true") {
    startBtn.dataset.bound = "true";
    startBtn.addEventListener("click", () => {
      updateScanWorkspaceIntakeActions();
      if (startBtn.disabled) return;
      beginScanWorkspaceProcessing();
    });
  }

  updateScanWorkspaceIntakeActions();
}

function getScanWorkspaceProcessingStage(stageKey) {
  return (
    SCAN_WORKSPACE_PROCESSING_STAGES.find((stage) => stage.key === stageKey) ||
    SCAN_WORKSPACE_PROCESSING_STAGES[0]
  );
}

function getScanWorkspaceProcessingStageIndex(stageKey) {
  return SCAN_WORKSPACE_PROCESSING_STAGES.findIndex((stage) => stage.key === stageKey);
}

function buildScanWorkspaceProcessingSummaryHtml(draft) {
  if (!draft) return "";

  const hasSavedResume = getScanWorkspaceHasPreselectedResume();
  const resumeSource = hasSavedResume
    ? "Saved resume variant"
    : draft.resumeText
      ? "Pasted resume text"
      : "Missing";

  const jobDescriptionValue = draft.jobDescriptionText
    ? `${draft.jobDescriptionText.length} chars`
    : "Missing";

  const companyValue = draft.company || "Not set";
  const roleValue = draft.role || "Not set";

  const cards = [
    { label: "Resume source", value: resumeSource },
    { label: "Job description", value: jobDescriptionValue },
    { label: "Company", value: companyValue },
    { label: "Role", value: roleValue },
  ];

  return cards
    .map(
      (item) => `
        <div class="scan-workspace-processing-summary-card">
          <div class="scan-workspace-processing-summary-label">${scanWorkspaceEscapeHtml(item.label)}</div>
          <div class="scan-workspace-processing-summary-value">${scanWorkspaceEscapeHtml(item.value)}</div>
        </div>
      `
    )
    .join("");
}

function buildScanWorkspaceProcessingStepsHtml(currentStageKey) {
  const currentIndex = getScanWorkspaceProcessingStageIndex(currentStageKey);

  return SCAN_WORKSPACE_PROCESSING_STAGES.map((stage, index) => {
    let stateClass = "";
    let stateLabel = "Pending";

    if (index < currentIndex) {
      stateClass = "is-complete";
      stateLabel = "Complete";
    } else if (index === currentIndex) {
      stateClass = "is-current";
      stateLabel = "Current";
    }

    return `
      <div class="scan-workspace-processing-step ${stateClass}">
        <div class="scan-workspace-processing-step-copy">
          <div class="scan-workspace-processing-step-title">${scanWorkspaceEscapeHtml(stage.title)}</div>
          <div class="scan-workspace-processing-step-text">${scanWorkspaceEscapeHtml(stage.description)}</div>
        </div>
        <div class="scan-workspace-processing-step-pill">${scanWorkspaceEscapeHtml(stateLabel)}</div>
      </div>
    `;
  }).join("");
}

function updateScanWorkspaceProcessingView() {
  const badge = getScanWorkspaceInput("scanWorkspaceProcessingBadge");
  const title = getScanWorkspaceInput("scanWorkspaceProcessingTitle");
  const subtitle = getScanWorkspaceInput("scanWorkspaceProcessingSubtitle");
  const summary = getScanWorkspaceInput("scanWorkspaceProcessingSummary");
  const stepList = getScanWorkspaceInput("scanWorkspaceProcessingStepList");
  const note = getScanWorkspaceInput("scanWorkspaceProcessingNote");

  const stage = getScanWorkspaceProcessingStage(scanWorkspaceProcessingState.currentStageKey);
  const draft = scanWorkspaceProcessingState.intakeDraft;

  if (badge) {
    badge.textContent = stage.title;
  }

  if (title) {
    title.textContent = "Structuring your content with AI";
  }

  if (subtitle) {
    subtitle.textContent = stage.description;
  }

  if (summary) {
    summary.innerHTML = buildScanWorkspaceProcessingSummaryHtml(draft);
  }

  if (stepList) {
    stepList.innerHTML = buildScanWorkspaceProcessingStepsHtml(stage.key);
  }

  if (note) {
    note.textContent =
      scanWorkspaceProcessingState.note ||
      "Waiting for the real scan runner. This phase adds the processing shell and stage model only.";
  }
}

function beginScanWorkspaceProcessing() {
  const draft = readScanWorkspaceIntakeDraft();

  scanWorkspaceProcessingState.status = "running";
  scanWorkspaceProcessingState.currentStageKey = "prepare";
  scanWorkspaceProcessingState.intakeDraft = { ...draft };
  scanWorkspaceProcessingState.note =
    "The backend scan runner is not wired yet. The next phase will attach the real start-scan request and polling flow.";

  setScanWorkspaceMode("processing");
}

function bindScanWorkspaceProcessingShell() {
  const backBtn = getScanWorkspaceInput("scanWorkspaceProcessingBackBtn");
  if (backBtn && backBtn.dataset.bound !== "true") {
    backBtn.dataset.bound = "true";
    backBtn.addEventListener("click", () => {
      setScanWorkspaceMode("new_scan");
    });
  }
}

function buildScanWorkspaceDocumentPreviewRequest() {
  const context = getScanWorkspaceContext();
  if (!context || !context.tailoringJsonPath || !context.resumeName) {
    return null;
  }

  return {
    tailoring_json_path: context.tailoringJsonPath,
    selected_resume: context.resumeName,
    selected_patch_candidate_ids: [],
    manual_bullet_edits: {},
  };
}

function fallbackRenderScanWorkspaceStructuredRow(row) {
  const rawText = String(row?.text || "").trim();
  const gapBefore = Number(row?.gap_before || 0);
  const indent = Math.max(0, Number(row?.left_indent_pt || 0));
  const isBullet = Boolean(row?.is_bullet);
  const isHeading = Boolean(row?.is_heading || row?.is_section_heading);
  const patched = Boolean(row?.patched);
  const patchSource = String(row?.patch_source || "").trim();

  if (String(row?.kind || "").trim() === "paired_row") {
    return `
      <div class="tailoring-workspace-doc-paired-row" style="margin-top:${gapBefore}px; padding-left:${indent}px;">
        <div class="tailoring-workspace-doc-paired-row-left">${scanWorkspaceEscapeHtml(String(row?.left_text || ""))}</div>
        <div class="tailoring-workspace-doc-paired-row-right">${scanWorkspaceEscapeHtml(String(row?.right_text || ""))}</div>
      </div>
    `;
  }

  const extraClasses = [
    "tailoring-workspace-doc-line",
    isHeading ? "tailoring-workspace-doc-line--heading" : "",
    isBullet ? "tailoring-workspace-doc-line--bullet" : "",
    patched ? "tailoring-workspace-doc-line--changed" : "",
    patchSource === "manual_edit" ? "tailoring-workspace-doc-line--manual" : "",
    patchSource === "selected_patch" ? "tailoring-workspace-doc-line--selected" : "",
  ]
    .filter(Boolean)
    .join(" ");

  if (isBullet) {
    return `
      <div class="${extraClasses}" style="margin-top:${gapBefore}px;">
        <div class="tailoring-workspace-doc-bullet-row" style="padding-left:${indent}px;">
          <div class="tailoring-workspace-doc-bullet-marker">•</div>
          <div class="tailoring-workspace-doc-line-copy tailoring-workspace-doc-bullet-copy">${scanWorkspaceEscapeHtml(rawText.replace(/^•\s*/, ""))}</div>
        </div>
      </div>
    `;
  }

  return `
    <div class="${extraClasses}" style="margin-top:${gapBefore}px;">
      <div class="tailoring-workspace-doc-line-copy" style="padding-left:${indent}px;">${scanWorkspaceEscapeHtml(rawText)}</div>
      ${isHeading ? `<div class="tailoring-workspace-doc-section-rule"></div>` : ""}
    </div>
  `;
}

function renderScanWorkspaceDocumentMirror() {
  if (
    scanWorkspacePreviewState.isDocumentPreviewLoading &&
    !scanWorkspacePreviewState.documentPreviewPayload
  ) {
    return `
      <div class="tailoring-empty-state">
        Loading reconstructed draft preview...
      </div>
    `;
  }

  const preview = scanWorkspacePreviewState.documentPreviewPayload;
  const pages = Array.isArray(preview?.pages) ? preview.pages : [];

  if (!pages.length) {
    const errorMessage = String(preview?.error_message || "").trim();
    return `
      <div class="tailoring-empty-state">
        ${scanWorkspaceEscapeHtml(errorMessage || "Live draft preview is not available for this scan.")}
      </div>
    `;
  }

  const escapeFn =
    typeof escapeHtml === "function" ? escapeHtml : scanWorkspaceEscapeHtml;

  const renderRowFn =
    typeof renderTailoringWorkspaceStructuredRow === "function"
      ? renderTailoringWorkspaceStructuredRow
      : fallbackRenderScanWorkspaceStructuredRow;

  const buildPresentationRowsFn =
    typeof buildTailoringWorkspacePreviewPresentationRows === "function"
      ? buildTailoringWorkspacePreviewPresentationRows
      : (rows) => (Array.isArray(rows) ? rows : []);

  const getSectionKeyFn =
    typeof getTailoringWorkspaceSectionKeyFromRow === "function"
      ? getTailoringWorkspaceSectionKeyFromRow
      : () => "";

  const showPageLabel = pages.length > 1;
  let carrySection = "";

  const normalizedPages = pages.map((page, pageIndex) => {
    const presentationRows = buildPresentationRowsFn(page.rows, {
      initialSection: carrySection,
      allowDocumentHeaderRoles: pageIndex === 0,
    });

    presentationRows.forEach((row) => {
      const sectionKey = getSectionKeyFn(row);
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
      <div class="tailoring-workspace-doc-mirror-note" style="white-space:normal; overflow-wrap:anywhere; line-height:1.35;">
        Read-only reconstructed draft from the export model. Accepted scan changes will appear here first.
        ${changedCount ? `${changedCount} changed line${changedCount === 1 ? "" : "s"} currently reflected.` : ""}
      </div>

      ${normalizedPages
        .map(
          (page) => `
        <section class="tailoring-workspace-doc-page">
          ${showPageLabel ? `
            <div class="tailoring-workspace-doc-page-header">
              <span class="tailoring-workspace-doc-page-number">
                Page ${escapeFn(String(page.page_number || ""))}
              </span>
            </div>
          ` : ""}

          <div class="tailoring-workspace-doc-page-body">
            ${(Array.isArray(page.presentation_rows) ? page.presentation_rows : [])
              .map((row) => renderRowFn(row))
              .join("")}
          </div>
        </section>
      `
        )
        .join("")}
    </div>
  `;
}

function renderScanWorkspaceLiveDraftPreviewInto() {
  const root = getScanWorkspaceInput("scanWorkspaceLiveDraftPreview");
  if (!root) return;
  root.innerHTML = renderScanWorkspaceDocumentMirror();
}

async function fetchScanWorkspaceDocumentPreview() {
  const requestBody = buildScanWorkspaceDocumentPreviewRequest();
  const previewStatus = getScanWorkspaceInput("scanWorkspacePreviewStatus");
  const previewMeta = getScanWorkspaceInput("scanWorkspacePreviewMeta");

  if (!requestBody) {
    scanWorkspacePreviewState.documentPreviewPayload = {
      ok: false,
      error_message: "Scan preload is not available for this route.",
      pages: [],
    };
    renderScanWorkspaceLiveDraftPreviewInto();
    if (previewStatus) {
      previewStatus.textContent = "Live draft preview is unavailable for this scan.";
    }
    if (previewMeta) {
      previewMeta.textContent = "Live draft preview unavailable";
    }
    return;
  }

  const requestSeq = ++scanWorkspacePreviewState.documentPreviewRequestSeq;
  scanWorkspacePreviewState.isDocumentPreviewLoading = true;
  renderScanWorkspaceLiveDraftPreviewInto();

  if (previewStatus) {
    previewStatus.textContent = "Loading reconstructed draft preview for this resume.";
  }
  if (previewMeta) {
    previewMeta.textContent = "Loading live draft preview...";
  }

  try {
    const response =
      typeof postJsonWithTimeout === "function"
        ? await postJsonWithTimeout(
            "/planning/render-workspace-draft-preview",
            requestBody,
            20000
          )
        : await fetch("/planning/render-workspace-draft-preview", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(requestBody),
          }).then(async (res) => {
            if (!res.ok) {
              let message = `Request failed (${res.status})`;
              try {
                const data = await res.json();
                message = String(data?.detail || data?.error_message || message);
              } catch {}
              throw new Error(message);
            }
            return res.json();
          });

    if (requestSeq !== scanWorkspacePreviewState.documentPreviewRequestSeq) return;

    scanWorkspacePreviewState.documentPreviewPayload = response;

    if (previewStatus) {
      previewStatus.textContent = "Live draft preview is ready.";
    }
    if (previewMeta) {
      previewMeta.textContent = "Live draft preview";
    }
  } catch (err) {
    if (requestSeq !== scanWorkspacePreviewState.documentPreviewRequestSeq) return;

    scanWorkspacePreviewState.documentPreviewPayload = {
      ok: false,
      error_message:
        err instanceof Error ? err.message : "Failed to render live draft preview.",
      pages: [],
    };

    if (previewStatus) {
      previewStatus.textContent = "Live draft preview failed to load.";
    }
    if (previewMeta) {
      previewMeta.textContent = "Live draft preview failed";
    }
  } finally {
    if (requestSeq === scanWorkspacePreviewState.documentPreviewRequestSeq) {
      scanWorkspacePreviewState.isDocumentPreviewLoading = false;
      renderScanWorkspaceLiveDraftPreviewInto();
    }
  }
}

function ensureScanWorkspaceDocumentPreviewLoaded({ force = false } = {}) {
  if (!force && scanWorkspacePreviewState.documentPreviewPayload) {
    renderScanWorkspaceLiveDraftPreviewInto();
    return;
  }

  fetchScanWorkspaceDocumentPreview();
}

function normalizeScanWorkspaceAnnotationDecision(decision) {
  const safeDecision = String(decision || "").trim().toLowerCase();
  return safeDecision === "accepted" || safeDecision === "rejected" ? safeDecision : "pending";
}

function normalizeScanWorkspaceAnnotationMarker(marker, index) {
  const tone = String(marker?.tone || "replace").trim().toLowerCase();
  const safeTone =
    tone === "add" || tone === "replace" || tone === "focus" ? tone : "replace";

  const id = String(marker?.id || `marker_${index + 1}`).trim();
  const topPercent = Number(marker?.topPercent);
  const leftPercent = Number(marker?.leftPercent);

  return {
    id,
    tone: safeTone,
    decision: normalizeScanWorkspaceAnnotationDecision(marker?.decision),
    title: String(marker?.title || "AI suggested change").trim(),
    copy: String(marker?.copy || "Review this anchored suggestion.").trim(),
    topPercent: Number.isFinite(topPercent) ? Math.max(2, Math.min(98, topPercent)) : 50,
    leftPercent: Number.isFinite(leftPercent) ? Math.max(2, Math.min(98, leftPercent)) : 50,
  };
}

function getScanWorkspaceAnnotationMarkerById(markerId) {
  return scanWorkspaceAnnotationState.markers.find((marker) => marker.id === markerId) || null;
}

function getScanWorkspaceAnnotationDecisionCounts() {
  return scanWorkspaceAnnotationState.markers.reduce(
    (acc, marker) => {
      const decision = normalizeScanWorkspaceAnnotationDecision(marker?.decision);
      acc.total += 1;
      if (decision === "accepted") acc.accepted += 1;
      else if (decision === "rejected") acc.rejected += 1;
      else acc.pending += 1;
      return acc;
    },
    { total: 0, accepted: 0, rejected: 0, pending: 0 }
  );
}

function setScanWorkspaceMarkerDecision(markerId, decision) {
  const safeDecision = normalizeScanWorkspaceAnnotationDecision(decision);
  let updatedMarker = null;

  scanWorkspaceAnnotationState.markers = scanWorkspaceAnnotationState.markers.map((marker) => {
    if (marker.id !== markerId) return marker;
    updatedMarker = { ...marker, decision: safeDecision };
    return updatedMarker;
  });

  return updatedMarker;
}

function updateScanWorkspaceDecisionSummaryUi() {
  const counts = getScanWorkspaceAnnotationDecisionCounts();
  const selectionStatus = getScanWorkspaceInput("scanWorkspaceSelectionStatus");
  const previewStatus = getScanWorkspaceInput("scanWorkspacePreviewStatus");
  const saveBtn = getScanWorkspaceInput("scanWorkspaceSaveBtn");
  const acceptAllBtn = getScanWorkspaceInput("scanWorkspaceAcceptAllAiBtn");

  if (selectionStatus) {
    selectionStatus.textContent =
      counts.total > 0
        ? `${counts.accepted} accepted · ${counts.rejected} rejected · ${counts.pending} pending`
        : "No scan actions selected yet.";
  }

  if (previewStatus && counts.total > 0) {
    previewStatus.textContent =
      counts.accepted > 0
        ? `${counts.accepted} suggestion(s) accepted into the current scan decision set.`
        : "Live draft preview is ready for scan decisions.";
  }

  if (saveBtn) {
    saveBtn.disabled = counts.accepted === 0 && counts.rejected === 0;
  }

  if (acceptAllBtn) {
    acceptAllBtn.disabled = counts.total === 0 || counts.pending === 0;
  }
}

function applyScanWorkspaceDecisionToActiveMarker(decision) {
  const activeMarker = getScanWorkspaceAnnotationMarkerById(
    scanWorkspaceAnnotationState.activeMarkerId
  );
  if (!activeMarker) return;

  setScanWorkspaceMarkerDecision(activeMarker.id, decision);
  renderScanWorkspaceAnnotationShell();
}

function closeScanWorkspaceSuggestionPopover() {
  scanWorkspaceAnnotationState.activeMarkerId = "";
  renderScanWorkspaceAnnotationShell();
}

function openScanWorkspaceSuggestionPopover(markerId) {
  const marker = getScanWorkspaceAnnotationMarkerById(markerId);
  if (!marker) return;

  scanWorkspaceAnnotationState.activeMarkerId = marker.id;
  renderScanWorkspaceAnnotationShell();
}

function renderScanWorkspaceAnnotationOverlay() {
  const overlay = getScanWorkspaceInput("scanWorkspaceAnnotationOverlay");
  const status = getScanWorkspaceInput("scanWorkspaceAnnotationStatus");
  if (!overlay || !status) return;

  const counts = getScanWorkspaceAnnotationDecisionCounts();

  if (!scanWorkspaceAnnotationState.markers.length) {
    overlay.innerHTML = "";
    status.textContent = "Annotation layer ready. Awaiting suggestion anchors.";
    return;
  }

  overlay.innerHTML = scanWorkspaceAnnotationState.markers
    .map((marker) => {
      const isActive = scanWorkspaceAnnotationState.activeMarkerId === marker.id;
      const toneClass =
        marker.tone === "add"
          ? "scan-workspace-annotation-marker--add"
          : marker.tone === "focus"
            ? "scan-workspace-annotation-marker--focus"
            : "scan-workspace-annotation-marker--replace";

      const decisionClass =
        marker.decision === "accepted"
          ? "is-accepted"
          : marker.decision === "rejected"
            ? "is-rejected"
            : "";

      return `
        <button
          type="button"
          class="scan-workspace-annotation-marker ${toneClass} ${decisionClass} ${isActive ? "is-active" : ""}"
          data-scan-annotation-marker="${scanWorkspaceEscapeHtml(marker.id)}"
          aria-label="${scanWorkspaceEscapeHtml(marker.title)}"
          aria-pressed="${isActive ? "true" : "false"}"
          style="top: ${marker.topPercent}%; left: ${marker.leftPercent}%;"
        ></button>
      `;
    })
    .join("");

  status.textContent =
    `${counts.total} suggestion anchor(s) loaded. ` +
    `${counts.accepted} accepted, ${counts.rejected} rejected, ${counts.pending} pending.`;
}

function renderScanWorkspaceSuggestionPopover() {
  const popover = getScanWorkspaceInput("scanWorkspaceSuggestionPopover");
  const title = getScanWorkspaceInput("scanWorkspaceSuggestionPopoverTitle");
  const copy = getScanWorkspaceInput("scanWorkspaceSuggestionPopoverCopy");
  const decisionPill = getScanWorkspaceInput("scanWorkspaceSuggestionDecisionPill");
  const decisionMeta = getScanWorkspaceInput("scanWorkspaceSuggestionDecisionMeta");
  const acceptBtn = getScanWorkspaceInput("scanWorkspaceSuggestionAcceptBtn");
  const rejectBtn = getScanWorkspaceInput("scanWorkspaceSuggestionRejectBtn");
  const resetBtn = getScanWorkspaceInput("scanWorkspaceSuggestionResetBtn");

  if (
    !popover ||
    !title ||
    !copy ||
    !decisionPill ||
    !decisionMeta ||
    !acceptBtn ||
    !rejectBtn ||
    !resetBtn
  ) {
    return;
  }

  const marker = getScanWorkspaceAnnotationMarkerById(
    scanWorkspaceAnnotationState.activeMarkerId
  );

  if (!marker) {
    popover.classList.add("hidden");
    title.textContent = "Select a suggestion anchor to inspect it here.";
    copy.textContent =
      "This shell is now ready for anchored AI suggestion details. Real suggestion positioning and accept/reject state wiring come in the next phase.";
    decisionPill.textContent = "Pending";
    decisionPill.className =
      "scan-workspace-suggestion-decision-pill scan-workspace-suggestion-decision-pill--pending";
    decisionMeta.textContent = "No decision recorded yet.";
    acceptBtn.disabled = true;
    rejectBtn.disabled = true;
    resetBtn.disabled = true;
    acceptBtn.classList.remove("is-active");
    rejectBtn.classList.remove("is-active");
    return;
  }

  popover.classList.remove("hidden");
  title.textContent = marker.title;
  copy.textContent = marker.copy;

  const decision = normalizeScanWorkspaceAnnotationDecision(marker.decision);

  if (decision === "accepted") {
    decisionPill.textContent = "Accepted";
    decisionPill.className =
      "scan-workspace-suggestion-decision-pill scan-workspace-suggestion-decision-pill--accepted";
    decisionMeta.textContent = "This suggestion is currently accepted into the scan decision set.";
  } else if (decision === "rejected") {
    decisionPill.textContent = "Rejected";
    decisionPill.className =
      "scan-workspace-suggestion-decision-pill scan-workspace-suggestion-decision-pill--rejected";
    decisionMeta.textContent = "This suggestion is currently rejected from the scan decision set.";
  } else {
    decisionPill.textContent = "Pending";
    decisionPill.className =
      "scan-workspace-suggestion-decision-pill scan-workspace-suggestion-decision-pill--pending";
    decisionMeta.textContent = "No decision recorded yet.";
  }

  acceptBtn.disabled = false;
  rejectBtn.disabled = false;
  resetBtn.disabled = decision === "pending";

  acceptBtn.classList.toggle("is-active", decision === "accepted");
  rejectBtn.classList.toggle("is-active", decision === "rejected");
}

function renderScanWorkspaceAnnotationShell() {
  renderScanWorkspaceAnnotationOverlay();
  renderScanWorkspaceSuggestionPopover();
  updateScanWorkspaceDecisionSummaryUi();
}

function setScanWorkspaceAnnotationMarkers(markers) {
  const existingDecisionById = new Map(
    scanWorkspaceAnnotationState.markers.map((marker) => [
      marker.id,
      normalizeScanWorkspaceAnnotationDecision(marker.decision),
    ])
  );

  scanWorkspaceAnnotationState.markers = (Array.isArray(markers) ? markers : [])
    .map((marker, index) => {
      const normalized = normalizeScanWorkspaceAnnotationMarker(marker, index);
      if (!normalized.id) return null;

      return {
        ...normalized,
        decision: normalizeScanWorkspaceAnnotationDecision(
          marker?.decision || existingDecisionById.get(normalized.id)
        ),
      };
    })
    .filter((marker) => marker && marker.id);

  if (
    scanWorkspaceAnnotationState.activeMarkerId &&
    !getScanWorkspaceAnnotationMarkerById(scanWorkspaceAnnotationState.activeMarkerId)
  ) {
    scanWorkspaceAnnotationState.activeMarkerId = "";
  }

  renderScanWorkspaceAnnotationShell();
}

function bindScanWorkspaceAnnotationShell() {
  const overlay = getScanWorkspaceInput("scanWorkspaceAnnotationOverlay");
  if (overlay && overlay.dataset.bound !== "true") {
    overlay.dataset.bound = "true";
    overlay.addEventListener("click", (event) => {
      const markerButton = event.target.closest("[data-scan-annotation-marker]");
      if (!markerButton) return;

      const markerId = String(markerButton.dataset.scanAnnotationMarker || "").trim();
      if (!markerId) return;

      openScanWorkspaceSuggestionPopover(markerId);
    });
  }

  const closeBtn = getScanWorkspaceInput("scanWorkspaceSuggestionPopoverCloseBtn");
  if (closeBtn && closeBtn.dataset.bound !== "true") {
    closeBtn.dataset.bound = "true";
    closeBtn.addEventListener("click", () => {
      closeScanWorkspaceSuggestionPopover();
    });
  }

  const acceptBtn = getScanWorkspaceInput("scanWorkspaceSuggestionAcceptBtn");
  if (acceptBtn && acceptBtn.dataset.bound !== "true") {
    acceptBtn.dataset.bound = "true";
    acceptBtn.addEventListener("click", () => {
      applyScanWorkspaceDecisionToActiveMarker("accepted");
    });
  }

  const rejectBtn = getScanWorkspaceInput("scanWorkspaceSuggestionRejectBtn");
  if (rejectBtn && rejectBtn.dataset.bound !== "true") {
    rejectBtn.dataset.bound = "true";
    rejectBtn.addEventListener("click", () => {
      applyScanWorkspaceDecisionToActiveMarker("rejected");
    });
  }

  const resetBtn = getScanWorkspaceInput("scanWorkspaceSuggestionResetBtn");
  if (resetBtn && resetBtn.dataset.bound !== "true") {
    resetBtn.dataset.bound = "true";
    resetBtn.addEventListener("click", () => {
      applyScanWorkspaceDecisionToActiveMarker("pending");
    });
  }

  const acceptAllBtn = getScanWorkspaceInput("scanWorkspaceAcceptAllAiBtn");
  if (acceptAllBtn && acceptAllBtn.dataset.bound !== "true") {
    acceptAllBtn.dataset.bound = "true";
    acceptAllBtn.addEventListener("click", () => {
      if (!scanWorkspaceAnnotationState.markers.length) return;

      scanWorkspaceAnnotationState.markers = scanWorkspaceAnnotationState.markers.map((marker) => ({
        ...marker,
        decision: "accepted",
      }));

      renderScanWorkspaceAnnotationShell();
    });
  }

  renderScanWorkspaceAnnotationShell();
}

window.addEventListener("DOMContentLoaded", () => {
  const root = getScanWorkspacePageRoot();
  if (!root) return;

  bindScanWorkspaceModeButtons();
  bindScanWorkspaceIntakeForm();
  bindScanWorkspaceProcessingShell();
  bindScanWorkspaceAnnotationShell();
  updateScanWorkspaceProcessingView();

  setScanWorkspaceMode(getScanWorkspaceInitialMode());

  window.scanWorkspacePhase1 = {
    setMode: setScanWorkspaceMode,
    getMode: () => normalizeScanWorkspaceMode(root.dataset.scanMode || ""),
    getIntakeDraft: () => ({ ...scanWorkspaceIntakeState }),
    getProcessingState: () => ({ ...scanWorkspaceProcessingState }),
    setProcessingStage: (stageKey, note = "") => {
        scanWorkspaceProcessingState.currentStageKey = stageKey;
        scanWorkspaceProcessingState.note = String(note || "").trim();
        updateScanWorkspaceProcessingView();
    },
    refreshLiveDraftPreview: () => ensureScanWorkspaceDocumentPreviewLoaded({ force: true }),
    setAnnotationMarkers: (markers) => {
        setScanWorkspaceAnnotationMarkers(markers);
    },
    clearAnnotationMarkers: () => {
        setScanWorkspaceAnnotationMarkers([]);
    },
    getAnnotationState: () => ({
        markers: scanWorkspaceAnnotationState.markers.map((marker) => ({ ...marker })),
        activeMarkerId: scanWorkspaceAnnotationState.activeMarkerId,
        counts: getScanWorkspaceAnnotationDecisionCounts(),
    }),
    };
});