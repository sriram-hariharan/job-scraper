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

const scanWorkspaceAnnotationState = {
  markers: [],
  activeMarkerId: "",
};

function scanWorkspaceEscapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
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
    title: String(marker?.title || "AI suggested change").trim(),
    copy: String(marker?.copy || "Review this anchored suggestion.").trim(),
    topPercent: Number.isFinite(topPercent) ? Math.max(2, Math.min(98, topPercent)) : 50,
    leftPercent: Number.isFinite(leftPercent) ? Math.max(2, Math.min(98, leftPercent)) : 50,
  };
}

function getScanWorkspaceAnnotationMarkerById(markerId) {
  return scanWorkspaceAnnotationState.markers.find((marker) => marker.id === markerId) || null;
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

      return `
        <button
          type="button"
          class="scan-workspace-annotation-marker ${toneClass}"
          data-scan-annotation-marker="${scanWorkspaceEscapeHtml(marker.id)}"
          aria-label="${scanWorkspaceEscapeHtml(marker.title)}"
          aria-pressed="${isActive ? "true" : "false"}"
          style="top: ${marker.topPercent}%; left: ${marker.leftPercent}%;"
        ></button>
      `;
    })
    .join("");

  status.textContent = `${scanWorkspaceAnnotationState.markers.length} suggestion anchor(s) loaded.`;
}

function renderScanWorkspaceSuggestionPopover() {
  const popover = getScanWorkspaceInput("scanWorkspaceSuggestionPopover");
  const title = getScanWorkspaceInput("scanWorkspaceSuggestionPopoverTitle");
  const copy = getScanWorkspaceInput("scanWorkspaceSuggestionPopoverCopy");
  const acceptBtn = getScanWorkspaceInput("scanWorkspaceSuggestionAcceptBtn");
  const rejectBtn = getScanWorkspaceInput("scanWorkspaceSuggestionRejectBtn");

  if (!popover || !title || !copy || !acceptBtn || !rejectBtn) return;

  const marker = getScanWorkspaceAnnotationMarkerById(scanWorkspaceAnnotationState.activeMarkerId);

  if (!marker) {
    popover.classList.add("hidden");
    title.textContent = "Select a suggestion anchor to inspect it here.";
    copy.textContent =
      "This shell is now ready for anchored AI suggestion details. Real suggestion positioning and accept/reject state wiring come in the next phase.";
    acceptBtn.disabled = true;
    rejectBtn.disabled = true;
    return;
  }

  popover.classList.remove("hidden");
  title.textContent = marker.title;
  copy.textContent = marker.copy;
  acceptBtn.disabled = false;
  rejectBtn.disabled = false;
}

function renderScanWorkspaceAnnotationShell() {
  renderScanWorkspaceAnnotationOverlay();
  renderScanWorkspaceSuggestionPopover();
}

function setScanWorkspaceAnnotationMarkers(markers) {
  scanWorkspaceAnnotationState.markers = (Array.isArray(markers) ? markers : [])
    .map((marker, index) => normalizeScanWorkspaceAnnotationMarker(marker, index))
    .filter((marker) => marker.id);

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
      const marker = getScanWorkspaceAnnotationMarkerById(scanWorkspaceAnnotationState.activeMarkerId);
      if (!marker) return;
      const status = getScanWorkspaceInput("scanWorkspaceAnnotationStatus");
      if (status) {
        status.textContent = `Accepted anchor: ${marker.title}`;
      }
    });
  }

  const rejectBtn = getScanWorkspaceInput("scanWorkspaceSuggestionRejectBtn");
  if (rejectBtn && rejectBtn.dataset.bound !== "true") {
    rejectBtn.dataset.bound = "true";
    rejectBtn.addEventListener("click", () => {
      const marker = getScanWorkspaceAnnotationMarkerById(scanWorkspaceAnnotationState.activeMarkerId);
      if (!marker) return;
      const status = getScanWorkspaceInput("scanWorkspaceAnnotationStatus");
      if (status) {
        status.textContent = `Rejected anchor: ${marker.title}`;
      }
    });
  }

  renderScanWorkspaceAnnotationShell();
}

const scanWorkspaceProcessingState = {
  status: "idle",
  currentStageKey: "prepare",
  note: "",
  intakeDraft: null,
};

function getScanWorkspacePageRoot() {
  return document.querySelector(".scan-workspace-page");
}

function getScanWorkspaceModePanels() {
  return Array.from(document.querySelectorAll("[data-scan-mode-panel]"));
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

  if (normalizedMode === "review") {
    renderScanWorkspaceAnnotationShell();
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

function getScanWorkspaceInput(id) {
  return document.getElementById(id);
}

function getScanWorkspaceHasPreselectedResume() {
  const root = getScanWorkspacePageRoot();
  if (!root) return false;
  return Boolean(String(root.dataset.resumeName || "").trim());
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
  if (!draft) {
    return "";
  }

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
          <div class="scan-workspace-processing-summary-label">${item.label}</div>
          <div class="scan-workspace-processing-summary-value">${escapeHtml(item.value)}</div>
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
          <div class="scan-workspace-processing-step-title">${escapeHtml(stage.title)}</div>
          <div class="scan-workspace-processing-step-text">${escapeHtml(stage.description)}</div>
        </div>

        <div class="scan-workspace-processing-step-pill">${escapeHtml(stateLabel)}</div>
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
    "The backend scan runner is not wired yet. Phase 4 will attach the real start-scan request and polling flow.";

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

window.addEventListener("DOMContentLoaded", () => {
  const root = getScanWorkspacePageRoot();
  if (!root) return;

  setScanWorkspaceMode(getScanWorkspaceInitialMode());
  bindScanWorkspaceModeButtons();
  bindScanWorkspaceIntakeForm();
  bindScanWorkspaceAnnotationShell();

  window.scanWorkspacePhase1 = {
    setMode: setScanWorkspaceMode,
    getMode: () => normalizeScanWorkspaceMode(root.dataset.scanMode || ""),
    getIntakeDraft: () => ({ ...scanWorkspaceIntakeState }),
    setAnnotationMarkers: (markers) => {
      setScanWorkspaceAnnotationMarkers(markers);
    },
    clearAnnotationMarkers: () => {
      setScanWorkspaceAnnotationMarkers([]);
    },
  };
});