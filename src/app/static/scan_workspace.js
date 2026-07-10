
function phase71bDeriveRunScopedPlanningOutputDir(path) {
  const raw = String(path || "").replace(/\\/g, "/");
  const marker = "/application_planning/job_packets/";
  const idx = raw.indexOf(marker);
  if (idx < 0) {
    return "";
  }
  return raw.slice(0, idx + "/application_planning".length);
}


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
  jobUrl: "",
  savedResumeName: "",
  resumeText: "",
  resumeFileName: "",
  jobDescriptionText: "",
};

const scanWorkspaceSavedResumeState = {
  resumes: [],
  isLoading: false,
  lastError: "",
};

const scanWorkspaceProcessingState = {
  status: "idle",
  currentStageKey: "prepare",
  note: "",
  intakeDraft: null,
  pendingReviewPayload: null,
};

const scanWorkspacePreviewState = {
  documentPreviewPayload: null,
  scorePreviewPayload: null,
  draftFragmentsPayload: null,
  draftFragmentsByBulletKey: {},
  activeSurface: "resume",
  isDocumentPreviewLoading: false,
  isScorePreviewLoading: false,
  documentPreviewRequestSeq: 0,
  scorePreviewRequestSeq: 0,
  candidateSignature: "",
};

const scanWorkspaceAnnotationState = {
  markers: [],
  activeMarkerId: "",
  undoStack: [],
  redoStack: [],
};

const scanWorkspaceCompareState = {
  beforePayload: null,
  afterPayload: null,
  isLoading: false,
  requestSeq: 0,
  acceptedSignature: "",
};

const scanWorkspacePersistenceState = {
  loadResponse: null,
  isLoading: false,
  isSaving: false,
  isExporting: false,
  lastError: "",
  hydratedSignature: "",
  manualBulletEdits: {},
};

const scanWorkspacePhraseState = {
  isLoading: false,
  lastError: "",
  lastNote: "",
  markerId: "",
  options: [],
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

function getScanWorkspacePreloadPayloadForSurface() {
  if (
    typeof scanWorkspaceState !== "undefined" &&
    scanWorkspaceState.preloadPayload &&
    typeof scanWorkspaceState.preloadPayload === "object"
  ) {
    return scanWorkspaceState.preloadPayload;
  }

  return null;
}

function getScanWorkspaceInlineDocumentPreview() {
  const payload = getScanWorkspacePreloadPayloadForSurface();
  const preview = payload && typeof payload === "object"
    ? payload.document_preview
    : null;
  if (!preview || typeof preview !== "object") return null;

  const pages = Array.isArray(preview.pages) ? preview.pages : [];
  return pages.length || preview.error_message ? preview : null;
}

function getScanWorkspaceJdLlmReadbackPayload(payload = getScanWorkspacePreloadPayloadForSurface()) {
  if (!payload || typeof payload !== "object") return null;

  const explicitReadback = payload.jd_llm_extraction_readback;
  if (explicitReadback && typeof explicitReadback === "object") return explicitReadback;

  const metadata = payload.jd_llm_extraction;
  if (!metadata || typeof metadata !== "object") return null;

  return {
    live_jd_llm_readback: true,
    llm_enabled: metadata.llm_enabled === true,
    llm_call_attempted: metadata.llm_call_attempted === true,
    llm_call_performed: metadata.llm_call_performed === true,
    fallback_used: metadata.fallback_used !== false,
    validation_status: String(metadata.validation_status || "missing").trim() || "missing",
    provider: String(metadata.provider || "").trim(),
    model: String(metadata.model || "").trim(),
    prompt_version: String(metadata.prompt_version || "").trim(),
    token_usage: metadata.token_usage && typeof metadata.token_usage === "object"
      ? metadata.token_usage
      : {},
    cost: metadata.cost && typeof metadata.cost === "object" ? metadata.cost : {},
    latency_ms: metadata.latency_ms || 0,
    structured_jd_signals: metadata.structured_jd_signals && typeof metadata.structured_jd_signals === "object"
      ? metadata.structured_jd_signals
      : {},
  };
}

function summarizeScanWorkspaceJdSignalList(signals, key, label) {
  const values = Array.isArray(signals?.[key])
    ? signals[key].map((value) => String(value || "").trim()).filter(Boolean)
    : [];
  if (!values.length) return "";
  return `${label}: ${values.slice(0, 4).join(", ")}${values.length > 4 ? ` +${values.length - 4}` : ""}`;
}

function renderScanWorkspaceJdLlmReadback() {
  const root = getScanWorkspaceInput("scanWorkspaceJdLlmReadback");
  if (!root) return;

  const readback = getScanWorkspaceJdLlmReadbackPayload();
  if (!readback) {
    root.textContent = "Live JD LLM: default-off";
    root.dataset.llmEnabled = "false";
    root.dataset.llmCallAttempted = "false";
    return;
  }

  const enabled = readback.llm_enabled === true;
  const attempted = readback.llm_call_attempted === true;
  const performed = readback.llm_call_performed === true;
  const fallback = readback.fallback_used !== false;
  const validation = String(readback.validation_status || "missing").trim() || "missing";
  const providerModel = [
    String(readback.provider || "").trim(),
    String(readback.model || "").trim(),
  ].filter(Boolean).join("/");
  const promptVersion = String(readback.prompt_version || "").trim();
  const latency = Number(readback.latency_ms);
  const tokenUsage = readback.token_usage && typeof readback.token_usage === "object"
    ? readback.token_usage
    : {};
  const cost = readback.cost && typeof readback.cost === "object" ? readback.cost : {};
  const tokenValue = tokenUsage.total_token_count ?? tokenUsage.total_tokens ?? "";
  const costValue = cost.estimated_cost ?? cost.total_cost ?? "";
  const signals = readback.structured_jd_signals && typeof readback.structured_jd_signals === "object"
    ? readback.structured_jd_signals
    : {};
  const signalSnippets = [
    summarizeScanWorkspaceJdSignalList(signals, "required_skills", "skills"),
    summarizeScanWorkspaceJdSignalList(signals, "tools", "tools"),
    summarizeScanWorkspaceJdSignalList(signals, "responsibilities", "signals"),
  ].filter(Boolean);

  root.dataset.llmEnabled = enabled ? "true" : "false";
  root.dataset.llmCallAttempted = attempted ? "true" : "false";
  root.dataset.llmCallPerformed = performed ? "true" : "false";
  root.dataset.llmFallbackUsed = fallback ? "true" : "false";
  root.dataset.llmValidationStatus = validation;

  const parts = [
    `Live JD LLM: ${enabled ? "enabled" : "default-off"}`,
    `attempted ${attempted ? "yes" : "no"}`,
    `performed ${performed ? "yes" : "no"}`,
    `fallback ${fallback ? "yes" : "no"}`,
    `validation ${validation}`,
    providerModel ? `provider ${providerModel}` : "",
    promptVersion ? `prompt ${promptVersion}` : "",
    Number.isFinite(latency) && latency > 0 ? `${latency}ms` : "",
    tokenValue !== "" ? `tokens ${tokenValue}` : "",
    costValue !== "" ? `cost ${costValue}` : "",
    signalSnippets.length ? signalSnippets.join(" · ") : "",
  ].filter(Boolean);

  root.textContent = parts.join(" · ");
}

function getScanWorkspaceLiveTailoringSuggestionEnabled() {
  return getScanWorkspaceInput("scanWorkspaceLiveTailoringSuggestionToggle")?.checked === true;
}

function getScanWorkspaceTailoringLlmReadbackPayload(payload = null) {
  const source = payload && typeof payload === "object"
    ? payload
    : getScanWorkspacePreloadPayloadForSurface();
  if (!source || typeof source !== "object") return null;

  const readback = source.live_tailoring_suggestion_readback;
  return readback && typeof readback === "object" ? readback : null;
}

function renderScanWorkspaceTailoringLlmReadback(readbackPayload = null) {
  const root = getScanWorkspaceInput("scanWorkspaceTailoringLlmReadback");
  if (!root) return;

  const readback = getScanWorkspaceTailoringLlmReadbackPayload(readbackPayload);
  if (!readback) {
    root.textContent = "Live tailoring LLM: default-off";
    root.dataset.tailoringLlmEnabled = "false";
    root.dataset.tailoringLlmCallAttempted = "false";
    return;
  }

  const enabled = readback.tailoring_llm_enabled === true;
  const attempted = readback.tailoring_llm_call_attempted === true;
  const performed = readback.tailoring_llm_call_performed === true;
  const fallback = readback.fallback_used !== false;
  const validation = String(readback.validation_status || "missing").trim() || "missing";
  const fallbackReason = String(readback.fallback_reason || "").trim();
  const fallbackErrorClass = String(readback.fallback_error_class || "").trim();
  const providerModel = [
    String(readback.provider || "").trim(),
    String(readback.model || "").trim(),
  ].filter(Boolean).join("/");
  const promptVersion = String(readback.prompt_version || "").trim();
  const latency = Number(readback.latency_ms);
  const tokenUsage = readback.token_usage && typeof readback.token_usage === "object"
    ? readback.token_usage
    : {};
  const cost = readback.cost && typeof readback.cost === "object" ? readback.cost : {};
  const tokenValue = tokenUsage.total_token_count ?? tokenUsage.total_tokens ?? "";
  const costValue = cost.estimated_cost ?? cost.total_cost ?? "";
  const suggestionIds = Array.isArray(readback.suggestion_ids)
    ? readback.suggestion_ids.map((value) => String(value || "").trim()).filter(Boolean)
    : [];
  const suggestionCount = Number(readback.suggestion_count);

  root.dataset.tailoringLlmEnabled = enabled ? "true" : "false";
  root.dataset.tailoringLlmCallAttempted = attempted ? "true" : "false";
  root.dataset.tailoringLlmCallPerformed = performed ? "true" : "false";
  root.dataset.tailoringLlmFallbackUsed = fallback ? "true" : "false";
  root.dataset.tailoringLlmValidationStatus = validation;
  root.dataset.tailoringLlmFallbackReason = fallbackReason;
  root.dataset.tailoringLlmFallbackErrorClass = fallbackErrorClass;

  const parts = [
    `Live tailoring LLM: ${enabled ? "enabled" : "default-off"}`,
    `attempted ${attempted ? "yes" : "no"}`,
    `performed ${performed ? "yes" : "no"}`,
    `fallback ${fallback ? "yes" : "no"}`,
    `validation ${validation}`,
    fallbackReason ? `reason ${fallbackReason}` : "",
    fallbackErrorClass ? `error ${fallbackErrorClass}` : "",
    Number.isFinite(suggestionCount) ? `suggestions ${suggestionCount}` : "",
    suggestionIds.length ? `ids ${suggestionIds.slice(0, 4).join(", ")}` : "",
    providerModel ? `provider ${providerModel}` : "",
    promptVersion ? `prompt ${promptVersion}` : "",
    Number.isFinite(latency) && latency > 0 ? `${latency}ms` : "",
    tokenValue !== "" ? `tokens ${tokenValue}` : "",
    costValue !== "" ? `cost ${costValue}` : "",
  ].filter(Boolean);

  root.textContent = parts.join(" · ");
}

function getScanWorkspaceLiveExactChangeProposalEnabled() {
  return getScanWorkspaceInput("scanWorkspaceLiveExactChangeProposalToggle")?.checked === true;
}

function getScanWorkspaceExactChangeLlmReadbackPayload(payload = null) {
  const source = payload && typeof payload === "object"
    ? payload
    : getScanWorkspacePreloadPayloadForSurface();
  if (!source || typeof source !== "object") return null;

  const readback = source.live_exact_resume_change_proposal_readback;
  return readback && typeof readback === "object" ? readback : null;
}

function renderScanWorkspaceExactChangeLlmReadback(readbackPayload = null) {
  const root = getScanWorkspaceInput("scanWorkspaceExactChangeLlmReadback");
  if (!root) return;

  const readback = getScanWorkspaceExactChangeLlmReadbackPayload(readbackPayload);
  if (!readback) {
    root.textContent = "Live exact change LLM: default-off";
    root.dataset.exactChangeLlmEnabled = "false";
    root.dataset.exactChangeLlmCallAttempted = "false";
    return;
  }

  const enabled = readback.exact_change_llm_enabled === true;
  const attempted = readback.exact_change_llm_call_attempted === true;
  const performed = readback.exact_change_llm_call_performed === true;
  const fallback = readback.fallback_used !== false;
  const validation = String(readback.validation_status || "missing").trim() || "missing";
  const fallbackReason = String(readback.fallback_reason || "").trim();
  const fallbackErrorClass = String(readback.fallback_error_class || "").trim();
  const providerModel = [
    String(readback.provider || "").trim(),
    String(readback.model || "").trim(),
  ].filter(Boolean).join("/");
  const promptVersion = String(readback.prompt_version || "").trim();
  const latency = Number(readback.latency_ms);
  const tokenUsage = readback.token_usage && typeof readback.token_usage === "object"
    ? readback.token_usage
    : {};
  const cost = readback.cost && typeof readback.cost === "object" ? readback.cost : {};
  const tokenValue = tokenUsage.total_token_count ?? tokenUsage.total_tokens ?? "";
  const costValue = cost.estimated_cost ?? cost.total_cost ?? "";
  const proposalIds = Array.isArray(readback.proposed_change_ids) && readback.proposed_change_ids.length
    ? readback.proposed_change_ids.map((value) => String(value || "").trim()).filter(Boolean)
    : Array.isArray(readback.stable_proposed_change_keys)
      ? readback.stable_proposed_change_keys.map((value) => String(value || "").trim()).filter(Boolean)
      : [];
  const stableProposalKeys = Array.isArray(readback.stable_proposed_change_keys)
    ? readback.stable_proposed_change_keys.map((value) => String(value || "").trim()).filter(Boolean)
    : [];
  const proposalCount = Number(readback.proposed_change_count);

  root.dataset.exactChangeLlmEnabled = enabled ? "true" : "false";
  root.dataset.exactChangeLlmCallAttempted = attempted ? "true" : "false";
  root.dataset.exactChangeLlmCallPerformed = performed ? "true" : "false";
  root.dataset.exactChangeLlmFallbackUsed = fallback ? "true" : "false";
  root.dataset.exactChangeLlmValidationStatus = validation;
  root.dataset.exactChangeLlmFallbackReason = fallbackReason;
  root.dataset.exactChangeLlmFallbackErrorClass = fallbackErrorClass;
  root.dataset.exactChangeLlmProposedChangeCount = Number.isFinite(proposalCount)
    ? String(proposalCount)
    : "";
  root.dataset.exactChangeLlmStableProposedChangeKeys = stableProposalKeys.join(",");

  const parts = [
    `Live exact change LLM: ${enabled ? "enabled" : "default-off"}`,
    `attempted ${attempted ? "yes" : "no"}`,
    `performed ${performed ? "yes" : "no"}`,
    `fallback ${fallback ? "yes" : "no"}`,
    `validation ${validation}`,
    fallbackReason ? `reason ${fallbackReason}` : "",
    fallbackErrorClass ? `error ${fallbackErrorClass}` : "",
    Number.isFinite(proposalCount) ? `proposals ${proposalCount}` : "",
    proposalIds.length ? `ids ${proposalIds.slice(0, 4).join(", ")}` : "",
    providerModel ? `provider ${providerModel}` : "",
    promptVersion ? `prompt ${promptVersion}` : "",
    Number.isFinite(latency) && latency > 0 ? `${latency}ms` : "",
    tokenValue !== "" ? `tokens ${tokenValue}` : "",
    costValue !== "" ? `cost ${costValue}` : "",
  ].filter(Boolean);

  root.textContent = parts.join(" · ");
}

function getScanWorkspaceManualExactChangeAcceptanceEnabled() {
  return getScanWorkspaceInput("scanWorkspaceManualExactChangeAcceptanceToggle")?.checked === true;
}

function getScanWorkspaceAcceptedExactChangeProposalIds() {
  const input = getScanWorkspaceInput("scanWorkspaceAcceptedExactChangeProposalIds");
  const raw = String(input?.value || "").trim();
  if (!raw) return [];
  return raw.split(",").map((value) => value.trim()).filter(Boolean);
}

function getScanWorkspaceManualExactChangeAcceptancePayload(payload = null) {
  const source = payload && typeof payload === "object"
    ? payload
    : getScanWorkspacePreloadPayloadForSurface();
  if (!source || typeof source !== "object") return null;

  const readback = source.manual_exact_change_acceptance_readback;
  return readback && typeof readback === "object" ? readback : null;
}

function renderScanWorkspaceManualExactChangeAcceptanceReadback(readbackPayload = null) {
  const root = getScanWorkspaceInput("scanWorkspaceManualExactChangeAcceptanceReadback");
  if (!root) return;

  const readback = getScanWorkspaceManualExactChangeAcceptancePayload(readbackPayload);
  if (!readback) {
    root.textContent = "Manual exact change acceptance: default-off";
    root.dataset.manualAcceptanceEnabled = "false";
    root.dataset.approvedChangePlanCreated = "false";
    return;
  }

  const enabled = readback.manual_acceptance_enabled === true;
  const performed = readback.manual_acceptance_performed === true;
  const planCreated = readback.approved_change_plan_created === true;
  const fallback = readback.fallback_used !== false;
  const validation = String(readback.validation_status || "missing").trim() || "missing";
  const fallbackReason = String(readback.fallback_reason || "").trim();
  const fallbackErrorClass = String(readback.fallback_error_class || "").trim();
  const acceptedIds = Array.isArray(readback.accepted_proposal_ids)
    ? readback.accepted_proposal_ids.map((value) => String(value || "").trim()).filter(Boolean)
    : Array.isArray(readback.stable_accepted_proposal_keys)
      ? readback.stable_accepted_proposal_keys.map((value) => String(value || "").trim()).filter(Boolean)
      : [];
  const acceptedCount = Number(readback.accepted_proposal_count);
  const skippedCount = Number(readback.skipped_proposal_count);
  const rejectedCount = Number(readback.rejected_proposal_count);
  const invalidCount = Number(readback.invalid_proposal_count);
  const planKey = String(readback.approved_change_plan_id || readback.stable_plan_key || "").trim();

  root.dataset.manualAcceptanceEnabled = enabled ? "true" : "false";
  root.dataset.manualAcceptancePerformed = performed ? "true" : "false";
  root.dataset.approvedChangePlanCreated = planCreated ? "true" : "false";
  root.dataset.manualAcceptanceValidationStatus = validation;
  root.dataset.manualAcceptanceFallbackReason = fallbackReason;
  root.dataset.manualAcceptanceFallbackErrorClass = fallbackErrorClass;
  root.dataset.acceptedExactChangeProposalIds = acceptedIds.join(",");
  root.dataset.approvedChangePlanKey = planKey;
  root.dataset.manualAcceptanceRejectedCount = Number.isFinite(rejectedCount) ? String(rejectedCount) : "";
  root.dataset.manualAcceptanceSkippedCount = Number.isFinite(skippedCount) ? String(skippedCount) : "";
  root.dataset.manualAcceptanceInvalidCount = Number.isFinite(invalidCount) ? String(invalidCount) : "";
  root.dataset.phase58bReadbackHardened = readback.phase58b_readback_hardened === true ? "true" : "false";

  const parts = [
    `Manual exact change acceptance: ${enabled ? "enabled" : "default-off"}`,
    `performed ${performed ? "yes" : "no"}`,
    `plan ${planCreated ? "created" : "not created"}`,
    `fallback ${fallback ? "yes" : "no"}`,
    `validation ${validation}`,
    Number.isFinite(acceptedCount) ? `accepted ${acceptedCount}` : "",
    Number.isFinite(rejectedCount) ? `rejected ${rejectedCount}` : "",
    Number.isFinite(skippedCount) ? `skipped ${skippedCount}` : "",
    Number.isFinite(invalidCount) ? `invalid ${invalidCount}` : "",
    acceptedIds.length ? `ids ${acceptedIds.slice(0, 4).join(", ")}` : "",
    planKey ? `plan ${planKey}` : "",
    fallbackReason ? `reason ${fallbackReason}` : "",
    fallbackErrorClass ? `error ${fallbackErrorClass}` : "",
  ].filter(Boolean);

  root.textContent = parts.join(" · ");
}

function getScanWorkspaceGuardedResumeCopyArtifactEnabled() {
  return getScanWorkspaceInput("scanWorkspaceGuardedResumeCopyArtifactToggle")?.checked === true;
}

function getScanWorkspaceApprovedChangePlanId() {
  return String(getScanWorkspaceInput("scanWorkspaceApprovedChangePlanId")?.value || "").trim();
}

function getScanWorkspaceGuardedResumeCopyArtifactPayload(payload = null) {
  const source = payload && typeof payload === "object"
    ? payload
    : getScanWorkspacePreloadPayloadForSurface();
  if (!source || typeof source !== "object") return null;

  const readback = source.guarded_resume_copy_artifact_readback;
  return readback && typeof readback === "object" ? readback : null;
}

function renderScanWorkspaceGuardedResumeCopyArtifactReadback(readbackPayload = null) {
  const root = getScanWorkspaceInput("scanWorkspaceGuardedResumeCopyArtifactReadback");
  if (!root) return;

  const readback = getScanWorkspaceGuardedResumeCopyArtifactPayload(readbackPayload);
  if (!readback) {
    root.textContent = "Guarded resume copy artifact: default-off";
    root.dataset.artifactCreationEnabled = "false";
    root.dataset.artifactCreated = "false";
    return;
  }

  const enabled = readback.artifact_creation_enabled === true;
  const requested = readback.artifact_creation_requested === true;
  const created = readback.artifact_created === true;
  const sourceUnchanged = readback.source_resume_unchanged !== false;
  const sourceOverwritten = readback.source_resume_overwritten === true;
  const fallback = readback.fallback_used !== false;
  const validation = String(readback.validation_status || "missing").trim() || "missing";
  const fallbackReason = String(readback.fallback_reason || "").trim();
  const fallbackErrorClass = String(readback.fallback_error_class || "").trim();
  const artifactKey = String(readback.artifact_id || readback.stable_artifact_key || "").trim();
  const planKey = String(readback.approved_change_plan_id || readback.stable_plan_key || "").trim();
  const artifactKind = String(readback.artifact_kind || readback.output_kind || "").trim();
  const appliedCount = Number(readback.applied_approved_change_count);
  const rejectedCount = Number(readback.rejected_change_count);
  const skippedCount = Number(readback.skipped_change_count);
  const invalidCount = Number(readback.invalid_change_count);

  root.dataset.artifactCreationEnabled = enabled ? "true" : "false";
  root.dataset.artifactCreationRequested = requested ? "true" : "false";
  root.dataset.artifactCreated = created ? "true" : "false";
  root.dataset.sourceResumeUnchanged = sourceUnchanged ? "true" : "false";
  root.dataset.sourceResumeOverwritten = sourceOverwritten ? "true" : "false";
  root.dataset.guardedResumeCopyArtifactKey = artifactKey;
  root.dataset.approvedChangePlanKey = planKey;
  root.dataset.guardArtifactValidationStatus = validation;
  root.dataset.guardArtifactFallbackReason = fallbackReason;
  root.dataset.guardArtifactFallbackErrorClass = fallbackErrorClass;
  root.dataset.appliedApprovedChangeCount = Number.isFinite(appliedCount) ? String(appliedCount) : "";
  root.dataset.rejectedChangeCount = Number.isFinite(rejectedCount) ? String(rejectedCount) : "";
  root.dataset.skippedChangeCount = Number.isFinite(skippedCount) ? String(skippedCount) : "";
  root.dataset.invalidChangeCount = Number.isFinite(invalidCount) ? String(invalidCount) : "";
  root.dataset.phase59bReadbackHardened = readback.phase59b_readback_hardened === true ? "true" : "false";

  const parts = [
    `Guarded resume copy artifact: ${enabled ? "enabled" : "default-off"}`,
    `requested ${requested ? "yes" : "no"}`,
    `artifact ${created ? "created" : "not created"}`,
    `source ${sourceUnchanged && !sourceOverwritten ? "unchanged" : "changed"}`,
    `fallback ${fallback ? "yes" : "no"}`,
    `validation ${validation}`,
    Number.isFinite(appliedCount) ? `approved changes ${appliedCount}` : "",
    Number.isFinite(rejectedCount) ? `rejected ${rejectedCount}` : "",
    Number.isFinite(skippedCount) ? `skipped ${skippedCount}` : "",
    Number.isFinite(invalidCount) ? `invalid ${invalidCount}` : "",
    artifactKey ? `artifact ${artifactKey}` : "",
    planKey ? `plan ${planKey}` : "",
    artifactKind ? `kind ${artifactKind}` : "",
    fallbackReason ? `reason ${fallbackReason}` : "",
    fallbackErrorClass ? `error ${fallbackErrorClass}` : "",
  ].filter(Boolean);

  root.textContent = parts.join(" · ");
}

function getScanWorkspaceGuardedResumeCopyArtifactVerificationEnabled() {
  return getScanWorkspaceInput("scanWorkspaceGuardedResumeCopyArtifactVerificationToggle")?.checked === true;
}

function getScanWorkspaceGuardedResumeCopyArtifactId() {
  return String(getScanWorkspaceInput("scanWorkspaceGuardedResumeCopyArtifactId")?.value || "").trim();
}

function getScanWorkspaceGuardedResumeCopyArtifactVerificationPayload(payload = null) {
  const source = payload && typeof payload === "object"
    ? payload
    : getScanWorkspacePreloadPayloadForSurface();
  if (!source || typeof source !== "object") return null;

  const readback = source.guarded_resume_copy_artifact_verification_readback;
  return readback && typeof readback === "object" ? readback : null;
}

function renderScanWorkspaceGuardedResumeCopyArtifactVerificationReadback(readbackPayload = null) {
  const root = getScanWorkspaceInput("scanWorkspaceGuardedResumeCopyArtifactVerificationReadback");
  if (!root) return;

  const readback = getScanWorkspaceGuardedResumeCopyArtifactVerificationPayload(readbackPayload);
  if (!readback) {
    root.textContent = "Guarded artifact verification: default-off";
    root.dataset.artifactVerificationEnabled = "false";
    root.dataset.artifactVerificationPerformed = "false";
    return;
  }

  const enabled = readback.artifact_verification_enabled === true;
  const requested = readback.artifact_verification_requested === true;
  const performed = readback.artifact_verification_performed === true;
  const passed = readback.artifact_verification_passed === true;
  const readable = readback.artifact_readable === true;
  const sourceUnchanged = readback.source_resume_unchanged !== false;
  const sourceOverwritten = readback.source_resume_overwritten === true;
  const fallback = readback.fallback_used !== false;
  const validation = String(readback.validation_status || "missing").trim() || "missing";
  const fallbackReason = String(readback.fallback_reason || "").trim();
  const fallbackErrorClass = String(readback.fallback_error_class || "").trim();
  const phase60bReadbackHardened = readback.phase60b_readback_hardened === true;
  const artifactKey = String(readback.artifact_id || readback.stable_artifact_key || "").trim();
  const planKey = String(readback.approved_change_plan_id || readback.stable_plan_key || "").trim();
  const appliedCount = Number(readback.applied_approved_change_count);
  const mismatchCount = Number(readback.mismatch_count);

  root.dataset.artifactVerificationEnabled = enabled ? "true" : "false";
  root.dataset.artifactVerificationRequested = requested ? "true" : "false";
  root.dataset.artifactVerificationPerformed = performed ? "true" : "false";
  root.dataset.artifactVerificationPassed = passed ? "true" : "false";
  root.dataset.artifactReadable = readable ? "true" : "false";
  root.dataset.sourceResumeUnchanged = sourceUnchanged ? "true" : "false";
  root.dataset.sourceResumeOverwritten = sourceOverwritten ? "true" : "false";
  root.dataset.guardedResumeCopyArtifactVerificationKey = artifactKey;
  root.dataset.approvedChangePlanKey = planKey;
  root.dataset.artifactVerificationValidationStatus = validation;
  root.dataset.artifactVerificationFallbackReason = fallbackReason;
  root.dataset.artifactVerificationFallbackErrorClass = fallbackErrorClass;
  root.dataset.phase60bReadbackHardened = phase60bReadbackHardened ? "true" : "false";

  const parts = [
    `Guarded artifact verification: ${enabled ? "enabled" : "default-off"}`,
    phase60bReadbackHardened ? "readback hardened" : "",
    `requested ${requested ? "yes" : "no"}`,
    `performed ${performed ? "yes" : "no"}`,
    `passed ${passed ? "yes" : "no"}`,
    `readable ${readable ? "yes" : "no"}`,
    `source ${sourceUnchanged && !sourceOverwritten ? "unchanged" : "changed"}`,
    `fallback ${fallback ? "yes" : "no"}`,
    `validation ${validation}`,
    Number.isFinite(appliedCount) ? `approved changes ${appliedCount}` : "",
    Number.isFinite(mismatchCount) ? `mismatches ${mismatchCount}` : "",
    artifactKey ? `artifact ${artifactKey}` : "",
    planKey ? `plan ${planKey}` : "",
    fallbackReason ? `reason ${fallbackReason}` : "",
    fallbackErrorClass ? `error ${fallbackErrorClass}` : "",
  ].filter(Boolean);

  root.textContent = parts.join(" · ");
}

function getScanWorkspaceVerifiedArtifactOperatorReviewPacketEnabled() {
  return getScanWorkspaceInput("scanWorkspaceVerifiedArtifactOperatorReviewPacketToggle")?.checked === true;
}

function getScanWorkspaceVerifiedArtifactOperatorReviewArtifactId() {
  return String(getScanWorkspaceInput("scanWorkspaceVerifiedArtifactOperatorReviewArtifactId")?.value || "").trim();
}

function getScanWorkspaceVerifiedArtifactOperatorReviewPacketPayload(payload = null) {
  const source = payload && typeof payload === "object"
    ? payload
    : getScanWorkspacePreloadPayloadForSurface();
  if (!source || typeof source !== "object") return null;

  const readback = source.verified_artifact_operator_review_packet_readback;
  return readback && typeof readback === "object" ? readback : null;
}

function renderScanWorkspaceVerifiedArtifactOperatorReviewPacketReadback(readbackPayload = null) {
  const root = getScanWorkspaceInput("scanWorkspaceVerifiedArtifactOperatorReviewPacketReadback");
  if (!root) return;

  const readback = getScanWorkspaceVerifiedArtifactOperatorReviewPacketPayload(readbackPayload);
  if (!readback) {
    root.textContent = "Verified artifact operator review packet: default-off";
    root.dataset.operatorReviewPacketEnabled = "false";
    root.dataset.operatorReviewPacketCreated = "false";
    return;
  }

  const enabled = readback.operator_review_packet_enabled === true;
  const requested = readback.operator_review_packet_requested === true;
  const created = readback.operator_review_packet_created === true;
  const verificationPassed = readback.artifact_verification_passed === true;
  const sourceUnchanged = readback.source_resume_unchanged !== false;
  const sourceOverwritten = readback.source_resume_overwritten === true;
  const fallback = readback.fallback_used !== false;
  const validation = String(readback.validation_status || "missing").trim() || "missing";
  const fallbackReason = String(readback.fallback_reason || "").trim();
  const fallbackErrorClass = String(readback.fallback_error_class || "").trim();
  const phase61bReadbackHardened = readback.phase61b_readback_hardened === true;
  const packetKey = String(readback.operator_review_packet_id || readback.stable_packet_key || "").trim();
  const artifactKey = String(readback.artifact_id || readback.stable_artifact_key || "").trim();
  const planKey = String(readback.approved_change_plan_id || readback.stable_plan_key || "").trim();
  const reviewItemCount = Number(readback.review_item_count);

  root.dataset.operatorReviewPacketEnabled = enabled ? "true" : "false";
  root.dataset.operatorReviewPacketRequested = requested ? "true" : "false";
  root.dataset.operatorReviewPacketCreated = created ? "true" : "false";
  root.dataset.artifactVerificationPassed = verificationPassed ? "true" : "false";
  root.dataset.sourceResumeUnchanged = sourceUnchanged ? "true" : "false";
  root.dataset.sourceResumeOverwritten = sourceOverwritten ? "true" : "false";
  root.dataset.operatorReviewPacketKey = packetKey;
  root.dataset.guardedResumeCopyArtifactKey = artifactKey;
  root.dataset.approvedChangePlanKey = planKey;
  root.dataset.operatorReviewPacketValidationStatus = validation;
  root.dataset.operatorReviewPacketFallbackReason = fallbackReason;
  root.dataset.operatorReviewPacketFallbackErrorClass = fallbackErrorClass;
  root.dataset.phase61bReadbackHardened = phase61bReadbackHardened ? "true" : "false";

  const parts = [
    `Verified artifact operator review packet: ${enabled ? "enabled" : "default-off"}`,
    phase61bReadbackHardened ? "readback hardened" : "",
    `requested ${requested ? "yes" : "no"}`,
    `created ${created ? "yes" : "no"}`,
    `verification ${verificationPassed ? "passed" : "not passed"}`,
    `source ${sourceUnchanged && !sourceOverwritten ? "unchanged" : "changed"}`,
    `fallback ${fallback ? "yes" : "no"}`,
    `validation ${validation}`,
    Number.isFinite(reviewItemCount) ? `review items ${reviewItemCount}` : "",
    packetKey ? `packet ${packetKey}` : "",
    artifactKey ? `artifact ${artifactKey}` : "",
    planKey ? `plan ${planKey}` : "",
    fallbackReason ? `reason ${fallbackReason}` : "",
    fallbackErrorClass ? `error ${fallbackErrorClass}` : "",
  ].filter(Boolean);

  root.textContent = parts.join(" · ");
}

function getScanWorkspaceVerifiedArtifactOperatorDecisionEnabled() {
  return getScanWorkspaceInput("scanWorkspaceVerifiedArtifactOperatorDecisionToggle")?.checked === true;
}

function getScanWorkspaceVerifiedArtifactOperatorDecisionPacketId() {
  return String(getScanWorkspaceInput("scanWorkspaceVerifiedArtifactOperatorDecisionPacketId")?.value || "").trim();
}

function getScanWorkspaceVerifiedArtifactOperatorDecisionArtifactId() {
  return String(getScanWorkspaceInput("scanWorkspaceVerifiedArtifactOperatorDecisionArtifactId")?.value || "").trim();
}

function getScanWorkspaceVerifiedArtifactOperatorDecisionValue() {
  return String(getScanWorkspaceInput("scanWorkspaceVerifiedArtifactOperatorDecisionValue")?.value || "").trim();
}

function getScanWorkspaceVerifiedArtifactOperatorDecisionPayload(payload = null) {
  const source = payload && typeof payload === "object"
    ? payload
    : getScanWorkspacePreloadPayloadForSurface();
  if (!source || typeof source !== "object") return null;

  const readback = source.verified_artifact_operator_decision_readback;
  return readback && typeof readback === "object" ? readback : null;
}

function renderScanWorkspaceVerifiedArtifactOperatorDecisionReadback(readbackPayload = null) {
  const root = getScanWorkspaceInput("scanWorkspaceVerifiedArtifactOperatorDecisionReadback");
  if (!root) return;

  const readback = getScanWorkspaceVerifiedArtifactOperatorDecisionPayload(readbackPayload);
  if (!readback) {
    root.textContent = "Verified artifact operator decision: default-off";
    root.dataset.operatorDecisionEnabled = "false";
    root.dataset.operatorDecisionCaptured = "false";
    return;
  }

  const enabled = readback.operator_decision_enabled === true;
  const requested = readback.operator_decision_requested === true;
  const captured = readback.operator_decision_captured === true;
  const verificationPassed = readback.artifact_verification_passed === true;
  const sourceUnchanged = readback.source_resume_unchanged !== false;
  const sourceOverwritten = readback.source_resume_overwritten === true;
  const fallback = readback.fallback_used !== false;
  const validation = String(readback.validation_status || "missing").trim() || "missing";
  const fallbackReason = String(readback.fallback_reason || "").trim();
  const fallbackErrorClass = String(readback.fallback_error_class || "").trim();
  const phase62bReadbackHardened = readback.phase62b_readback_hardened === true;
  const decisionKey = String(readback.operator_decision_id || readback.stable_decision_key || "").trim();
  const packetKey = String(readback.operator_review_packet_id || readback.stable_packet_key || "").trim();
  const artifactKey = String(readback.artifact_id || readback.stable_artifact_key || "").trim();
  const decisionValue = String(readback.operator_decision_value || "").trim();

  root.dataset.operatorDecisionEnabled = enabled ? "true" : "false";
  root.dataset.operatorDecisionRequested = requested ? "true" : "false";
  root.dataset.operatorDecisionCaptured = captured ? "true" : "false";
  root.dataset.operatorDecisionValue = decisionValue;
  root.dataset.operatorDecisionKey = decisionKey;
  root.dataset.operatorReviewPacketKey = packetKey;
  root.dataset.guardedResumeCopyArtifactKey = artifactKey;
  root.dataset.artifactVerificationPassed = verificationPassed ? "true" : "false";
  root.dataset.sourceResumeUnchanged = sourceUnchanged ? "true" : "false";
  root.dataset.sourceResumeOverwritten = sourceOverwritten ? "true" : "false";
  root.dataset.operatorDecisionValidationStatus = validation;
  root.dataset.operatorDecisionFallbackReason = fallbackReason;
  root.dataset.operatorDecisionFallbackErrorClass = fallbackErrorClass;
  root.dataset.phase62bReadbackHardened = phase62bReadbackHardened ? "true" : "false";

  const parts = [
    `Verified artifact operator decision: ${enabled ? "enabled" : "default-off"}`,
    phase62bReadbackHardened ? "readback hardened" : "",
    `requested ${requested ? "yes" : "no"}`,
    `captured ${captured ? "yes" : "no"}`,
    decisionValue ? `decision ${decisionValue}` : "",
    `verification ${verificationPassed ? "passed" : "not passed"}`,
    `source ${sourceUnchanged && !sourceOverwritten ? "unchanged" : "changed"}`,
    `fallback ${fallback ? "yes" : "no"}`,
    `validation ${validation}`,
    decisionKey ? `decision id ${decisionKey}` : "",
    packetKey ? `packet ${packetKey}` : "",
    artifactKey ? `artifact ${artifactKey}` : "",
    fallbackReason ? `reason ${fallbackReason}` : "",
    fallbackErrorClass ? `error ${fallbackErrorClass}` : "",
  ].filter(Boolean);

  root.textContent = parts.join(" · ");
}

function getScanWorkspaceApplicationReadinessPacketEnabled() {
  return getScanWorkspaceInput("scanWorkspaceApplicationReadinessPacketToggle")?.checked === true;
}

function getScanWorkspaceApplicationReadinessDecisionId() {
  return String(getScanWorkspaceInput("scanWorkspaceApplicationReadinessDecisionId")?.value || "").trim();
}

function getScanWorkspaceApplicationReadinessReviewPacketId() {
  return String(getScanWorkspaceInput("scanWorkspaceApplicationReadinessReviewPacketId")?.value || "").trim();
}

function getScanWorkspaceApplicationReadinessArtifactId() {
  return String(getScanWorkspaceInput("scanWorkspaceApplicationReadinessArtifactId")?.value || "").trim();
}

function getScanWorkspaceApplicationReadinessPacketPayload(payload = null) {
  const source = payload && typeof payload === "object"
    ? payload
    : getScanWorkspacePreloadPayloadForSurface();
  if (!source || typeof source !== "object") return null;

  const readback = source.operator_approved_artifact_application_readiness_packet_readback;
  return readback && typeof readback === "object" ? readback : null;
}

function renderScanWorkspaceApplicationReadinessPacketReadback(readbackPayload = null) {
  const root = getScanWorkspaceInput("scanWorkspaceApplicationReadinessPacketReadback");
  if (!root) return;

  const readback = getScanWorkspaceApplicationReadinessPacketPayload(readbackPayload);
  if (!readback) {
    root.textContent = "Application readiness packet: default-off";
    root.dataset.applicationReadinessPacketEnabled = "false";
    root.dataset.applicationReadinessPacketCreated = "false";
    return;
  }

  const enabled = readback.application_readiness_packet_enabled === true;
  const requested = readback.application_readiness_packet_requested === true;
  const created = readback.application_readiness_packet_created === true;
  const verificationPassed = readback.artifact_verification_passed === true;
  const execution = readback.application_execution_performed === true;
  const submission = readback.application_submission_performed === true;
  const enqueued = readback.application_execution_enqueued === true;
  const sourceUnchanged = readback.source_resume_unchanged !== false;
  const sourceOverwritten = readback.source_resume_overwritten === true;
  const fallback = readback.fallback_used !== false;
  const validation = String(readback.validation_status || "missing").trim() || "missing";
  const fallbackReason = String(readback.fallback_reason || "").trim();
  const fallbackErrorClass = String(readback.fallback_error_class || "").trim();
  const phase63bReadbackHardened = readback.phase63b_readback_hardened === true;
  const readinessKey = String(readback.application_readiness_packet_id || readback.stable_packet_key || "").trim();
  const decisionKey = String(readback.operator_decision_id || readback.stable_decision_key || "").trim();
  const reviewPacketKey = String(readback.operator_review_packet_id || readback.stable_review_packet_key || "").trim();
  const artifactKey = String(readback.artifact_id || readback.stable_artifact_key || "").trim();
  const decisionValue = String(readback.operator_decision_value || "").trim();
  const readinessItemCount = Number(readback.readiness_item_count);

  root.dataset.applicationReadinessPacketEnabled = enabled ? "true" : "false";
  root.dataset.applicationReadinessPacketRequested = requested ? "true" : "false";
  root.dataset.applicationReadinessPacketCreated = created ? "true" : "false";
  root.dataset.applicationReadinessPacketKey = readinessKey;
  root.dataset.operatorDecisionKey = decisionKey;
  root.dataset.operatorReviewPacketKey = reviewPacketKey;
  root.dataset.guardedResumeCopyArtifactKey = artifactKey;
  root.dataset.operatorDecisionValue = decisionValue;
  root.dataset.artifactVerificationPassed = verificationPassed ? "true" : "false";
  root.dataset.applicationExecutionEnqueued = enqueued ? "true" : "false";
  root.dataset.applicationExecutionPerformed = execution ? "true" : "false";
  root.dataset.applicationSubmissionPerformed = submission ? "true" : "false";
  root.dataset.sourceResumeUnchanged = sourceUnchanged ? "true" : "false";
  root.dataset.sourceResumeOverwritten = sourceOverwritten ? "true" : "false";
  root.dataset.applicationReadinessValidationStatus = validation;
  root.dataset.applicationReadinessFallbackReason = fallbackReason;
  root.dataset.applicationReadinessFallbackErrorClass = fallbackErrorClass;
  root.dataset.phase63bReadbackHardened = phase63bReadbackHardened ? "true" : "false";

  const parts = [
    `Application readiness packet: ${enabled ? "enabled" : "default-off"}`,
    phase63bReadbackHardened ? "readback hardened" : "",
    `requested ${requested ? "yes" : "no"}`,
    `created ${created ? "yes" : "no"}`,
    decisionValue ? `decision ${decisionValue}` : "",
    `verification ${verificationPassed ? "passed" : "not passed"}`,
    `execution ${execution || enqueued ? "started" : "not started"}`,
    `submission ${submission ? "performed" : "not performed"}`,
    `source ${sourceUnchanged && !sourceOverwritten ? "unchanged" : "changed"}`,
    `fallback ${fallback ? "yes" : "no"}`,
    `validation ${validation}`,
    Number.isFinite(readinessItemCount) ? `items ${readinessItemCount}` : "",
    readinessKey ? `packet ${readinessKey}` : "",
    decisionKey ? `decision id ${decisionKey}` : "",
    reviewPacketKey ? `review packet ${reviewPacketKey}` : "",
    artifactKey ? `artifact ${artifactKey}` : "",
    fallbackReason ? `reason ${fallbackReason}` : "",
    fallbackErrorClass ? `error ${fallbackErrorClass}` : "",
  ].filter(Boolean);

  root.textContent = parts.join(" · ");
}

function getScanWorkspaceManualApplicationHandoffPacketEnabled() {
  return getScanWorkspaceInput("scanWorkspaceManualApplicationHandoffPacketToggle")?.checked === true;
}

function getScanWorkspaceManualHandoffReadinessPacketId() {
  return String(getScanWorkspaceInput("scanWorkspaceManualHandoffReadinessPacketId")?.value || "").trim();
}

function getScanWorkspaceManualHandoffArtifactId() {
  return String(getScanWorkspaceInput("scanWorkspaceManualHandoffArtifactId")?.value || "").trim();
}

function getScanWorkspaceManualApplicationHandoffPacketPayload(payload = null) {
  const source = payload && typeof payload === "object"
    ? payload
    : getScanWorkspacePreloadPayloadForSurface();
  if (!source || typeof source !== "object") return null;

  const readback = source.human_only_manual_application_handoff_packet_readback;
  return readback && typeof readback === "object" ? readback : null;
}

function renderScanWorkspaceManualApplicationHandoffPacketReadback(readbackPayload = null) {
  const root = getScanWorkspaceInput("scanWorkspaceManualApplicationHandoffPacketReadback");
  if (!root) return;

  const readback = getScanWorkspaceManualApplicationHandoffPacketPayload(readbackPayload);
  if (!readback) {
    root.textContent = "Manual application handoff packet: default-off";
    root.dataset.manualHandoffPacketEnabled = "false";
    root.dataset.manualHandoffPacketCreated = "false";
    return;
  }

  const enabled = readback.manual_handoff_packet_enabled === true;
  const requested = readback.manual_handoff_packet_requested === true;
  const created = readback.manual_handoff_packet_created === true;
  const humanOnly = readback.human_only_application_boundary === true;
  const atsAutomation = readback.ats_automation_performed === true;
  const submission = readback.application_submission_performed === true;
  const queued = readback.apply_queue_enqueued === true;
  const sourceUnchanged = readback.source_resume_unchanged !== false;
  const sourceOverwritten = readback.source_resume_overwritten === true;
  const fallback = readback.fallback_used !== false;
  const validation = String(readback.validation_status || "missing").trim() || "missing";
  const fallbackReason = String(readback.fallback_reason || "").trim();
  const fallbackErrorClass = String(readback.fallback_error_class || "").trim();
  const phase64bReadbackHardened = readback.phase64b_readback_hardened === true;
  const handoffKey = String(readback.manual_handoff_packet_id || readback.stable_packet_key || "").trim();
  const readinessKey = String(readback.application_readiness_packet_id || readback.stable_readiness_packet_key || "").trim();
  const artifactKey = String(readback.artifact_id || readback.stable_artifact_key || "").trim();
  const decisionValue = String(readback.operator_decision_value || "").trim();

  root.dataset.manualHandoffPacketEnabled = enabled ? "true" : "false";
  root.dataset.manualHandoffPacketRequested = requested ? "true" : "false";
  root.dataset.manualHandoffPacketCreated = created ? "true" : "false";
  root.dataset.manualHandoffPacketKey = handoffKey;
  root.dataset.applicationReadinessPacketKey = readinessKey;
  root.dataset.guardedResumeCopyArtifactKey = artifactKey;
  root.dataset.operatorDecisionValue = decisionValue;
  root.dataset.humanOnlyApplicationBoundary = humanOnly ? "true" : "false";
  root.dataset.atsAutomationPerformed = atsAutomation ? "true" : "false";
  root.dataset.applicationSubmissionPerformed = submission ? "true" : "false";
  root.dataset.applyQueueEnqueued = queued ? "true" : "false";
  root.dataset.sourceResumeUnchanged = sourceUnchanged ? "true" : "false";
  root.dataset.sourceResumeOverwritten = sourceOverwritten ? "true" : "false";
  root.dataset.manualHandoffValidationStatus = validation;
  root.dataset.manualHandoffFallbackReason = fallbackReason;
  root.dataset.manualHandoffFallbackErrorClass = fallbackErrorClass;
  root.dataset.phase64bReadbackHardened = phase64bReadbackHardened ? "true" : "false";

  const parts = [
    `Manual application handoff packet: ${enabled ? "enabled" : "default-off"}`,
    phase64bReadbackHardened ? "readback hardened" : "",
    `requested ${requested ? "yes" : "no"}`,
    `created ${created ? "yes" : "no"}`,
    humanOnly ? "human-only boundary" : "",
    decisionValue ? `decision ${decisionValue}` : "",
    `ATS automation ${atsAutomation ? "performed" : "not performed"}`,
    `submission ${submission ? "performed" : "not performed"}`,
    `queue ${queued ? "enqueued" : "not enqueued"}`,
    `source ${sourceUnchanged && !sourceOverwritten ? "unchanged" : "changed"}`,
    `fallback ${fallback ? "yes" : "no"}`,
    `validation ${validation}`,
    handoffKey ? `packet ${handoffKey}` : "",
    readinessKey ? `readiness ${readinessKey}` : "",
    artifactKey ? `artifact ${artifactKey}` : "",
    fallbackReason ? `reason ${fallbackReason}` : "",
    fallbackErrorClass ? `error ${fallbackErrorClass}` : "",
  ].filter(Boolean);

  root.textContent = parts.join(" · ");
}

function getScanWorkspaceHandoffAuditTrailEnabled() {
  return getScanWorkspaceInput("scanWorkspaceHandoffAuditTrailToggle")?.checked === true;
}

function getScanWorkspaceHandoffAuditHandoffPacketId() {
  return String(getScanWorkspaceInput("scanWorkspaceHandoffAuditHandoffPacketId")?.value || "").trim();
}

function getScanWorkspaceHandoffAuditReadinessPacketId() {
  return String(getScanWorkspaceInput("scanWorkspaceHandoffAuditReadinessPacketId")?.value || "").trim();
}

function getScanWorkspaceHandoffAuditArtifactId() {
  return String(getScanWorkspaceInput("scanWorkspaceHandoffAuditArtifactId")?.value || "").trim();
}

function getScanWorkspaceHandoffAuditTrailPayload(payload = null) {
  const source = payload && typeof payload === "object"
    ? payload
    : getScanWorkspacePreloadPayloadForSurface();
  if (!source || typeof source !== "object") return null;

  const readback = source.human_only_handoff_audit_trail_readback;
  return readback && typeof readback === "object" ? readback : null;
}

function renderScanWorkspaceHandoffAuditTrailReadback(readbackPayload = null) {
  const root = getScanWorkspaceInput("scanWorkspaceHandoffAuditTrailReadback");
  if (!root) return;

  const readback = getScanWorkspaceHandoffAuditTrailPayload(readbackPayload);
  if (!readback) {
    root.textContent = "Handoff audit trail: default-off";
    root.dataset.handoffAuditTrailEnabled = "false";
    root.dataset.handoffAuditTrailCreated = "false";
    return;
  }

  const enabled = readback.handoff_audit_trail_enabled === true;
  const requested = readback.handoff_audit_trail_requested === true;
  const created = readback.handoff_audit_trail_created === true;
  const humanOnly = readback.human_only_application_boundary === true;
  const atsAutomation = readback.ats_automation_performed === true;
  const submission = readback.application_submission_performed === true;
  const queued = readback.apply_queue_enqueued === true;
  const sourceUnchanged = readback.source_resume_unchanged !== false;
  const sourceOverwritten = readback.source_resume_overwritten === true;
  const fallback = readback.fallback_used !== false;
  const validation = String(readback.validation_status || "missing").trim() || "missing";
  const fallbackReason = String(readback.fallback_reason || "").trim();
  const fallbackErrorClass = String(readback.fallback_error_class || "").trim();
  const auditKey = String(readback.handoff_audit_trail_id || readback.stable_audit_key || "").trim();
  const handoffKey = String(readback.manual_handoff_packet_id || readback.stable_handoff_packet_key || "").trim();
  const readinessKey = String(readback.application_readiness_packet_id || readback.stable_readiness_packet_key || "").trim();
  const artifactKey = String(readback.artifact_id || readback.stable_artifact_key || "").trim();
  const auditEventCount = Number(readback.audit_event_count);

  root.dataset.handoffAuditTrailEnabled = enabled ? "true" : "false";
  root.dataset.handoffAuditTrailRequested = requested ? "true" : "false";
  root.dataset.handoffAuditTrailCreated = created ? "true" : "false";
  root.dataset.handoffAuditTrailKey = auditKey;
  root.dataset.manualHandoffPacketKey = handoffKey;
  root.dataset.applicationReadinessPacketKey = readinessKey;
  root.dataset.guardedResumeCopyArtifactKey = artifactKey;
  root.dataset.humanOnlyApplicationBoundary = humanOnly ? "true" : "false";
  root.dataset.atsAutomationPerformed = atsAutomation ? "true" : "false";
  root.dataset.applicationSubmissionPerformed = submission ? "true" : "false";
  root.dataset.applyQueueEnqueued = queued ? "true" : "false";
  root.dataset.sourceResumeUnchanged = sourceUnchanged ? "true" : "false";
  root.dataset.sourceResumeOverwritten = sourceOverwritten ? "true" : "false";
  root.dataset.handoffAuditValidationStatus = validation;
  root.dataset.handoffAuditFallbackReason = fallbackReason;
  root.dataset.handoffAuditFallbackErrorClass = fallbackErrorClass;

  const parts = [
    `Handoff audit trail: ${enabled ? "enabled" : "default-off"}`,
    `requested ${requested ? "yes" : "no"}`,
    `created ${created ? "yes" : "no"}`,
    humanOnly ? "human-only boundary" : "",
    `ATS automation ${atsAutomation ? "performed" : "not performed"}`,
    `submission ${submission ? "performed" : "not performed"}`,
    `queue ${queued ? "enqueued" : "not enqueued"}`,
    `source ${sourceUnchanged && !sourceOverwritten ? "unchanged" : "changed"}`,
    `fallback ${fallback ? "yes" : "no"}`,
    `validation ${validation}`,
    Number.isFinite(auditEventCount) ? `events ${auditEventCount}` : "",
    auditKey ? `audit ${auditKey}` : "",
    handoffKey ? `handoff ${handoffKey}` : "",
    readinessKey ? `readiness ${readinessKey}` : "",
    artifactKey ? `artifact ${artifactKey}` : "",
    fallbackReason ? `reason ${fallbackReason}` : "",
    fallbackErrorClass ? `error ${fallbackErrorClass}` : "",
  ].filter(Boolean);

  root.textContent = parts.join(" · ");
}

function getScanWorkspaceSafetyBoundarySummaryEnabled() {
  return getScanWorkspaceInput("scanWorkspaceSafetyBoundarySummaryToggle")?.checked === true;
}

function getScanWorkspaceSafetyBoundaryAuditTrailId() {
  return String(getScanWorkspaceInput("scanWorkspaceSafetyBoundaryAuditTrailId")?.value || "").trim();
}

function getScanWorkspaceSafetyBoundaryHandoffPacketId() {
  return String(getScanWorkspaceInput("scanWorkspaceSafetyBoundaryHandoffPacketId")?.value || "").trim();
}

function getScanWorkspaceSafetyBoundaryReadinessPacketId() {
  return String(getScanWorkspaceInput("scanWorkspaceSafetyBoundaryReadinessPacketId")?.value || "").trim();
}

function getScanWorkspaceSafetyBoundaryArtifactId() {
  return String(getScanWorkspaceInput("scanWorkspaceSafetyBoundaryArtifactId")?.value || "").trim();
}

function getScanWorkspaceSafetyBoundarySummaryPayload(payload = null) {
  const source = payload && typeof payload === "object"
    ? payload
    : getScanWorkspacePreloadPayloadForSurface();
  if (!source || typeof source !== "object") return null;

  const readback = source.human_only_safety_boundary_summary_readback;
  return readback && typeof readback === "object" ? readback : null;
}

function renderScanWorkspaceSafetyBoundarySummaryReadback(readbackPayload = null) {
  const root = getScanWorkspaceInput("scanWorkspaceSafetyBoundarySummaryReadback");
  if (!root) return;

  const readback = getScanWorkspaceSafetyBoundarySummaryPayload(readbackPayload);
  if (!readback) {
    root.textContent = "Safety boundary summary: default-off";
    root.dataset.safetyBoundarySummaryEnabled = "false";
    root.dataset.safetyBoundarySummaryCreated = "false";
    return;
  }

  const enabled = readback.safety_boundary_summary_enabled === true;
  const requested = readback.safety_boundary_summary_requested === true;
  const created = readback.safety_boundary_summary_created === true;
  const humanOnly = readback.human_only_application_boundary === true;
  const coreLlmWorkflowAutomatic = readback.core_llm_inference_workflow_automatic === true;
  const manualMutationGated = readback.manual_mutation_requires_operator_action === true;
  const atsAutomation = readback.ats_automation_performed === true;
  const submission = readback.application_submission_performed === true;
  const queued = readback.apply_queue_enqueued === true;
  const sourceUnchanged = readback.source_resume_unchanged !== false;
  const sourceOverwritten = readback.source_resume_overwritten === true;
  const fallback = readback.fallback_used !== false;
  const validation = String(readback.validation_status || "missing").trim() || "missing";
  const fallbackReason = String(readback.fallback_reason || "").trim();
  const fallbackErrorClass = String(readback.fallback_error_class || "").trim();
  const summaryKey = String(readback.safety_boundary_summary_id || readback.stable_summary_key || "").trim();
  const auditKey = String(readback.handoff_audit_trail_id || readback.stable_audit_key || "").trim();
  const handoffKey = String(readback.manual_handoff_packet_id || readback.stable_handoff_packet_key || "").trim();
  const readinessKey = String(readback.application_readiness_packet_id || readback.stable_readiness_packet_key || "").trim();
  const artifactKey = String(readback.artifact_id || readback.stable_artifact_key || "").trim();
  const llmCapableCount = Number(readback.llm_capable_action_count);
  const mutationCapableCount = Number(readback.mutation_capable_action_count);
  const forbiddenPathCount = Number(readback.forbidden_path_count);

  root.dataset.safetyBoundarySummaryEnabled = enabled ? "true" : "false";
  root.dataset.safetyBoundarySummaryRequested = requested ? "true" : "false";
  root.dataset.safetyBoundarySummaryCreated = created ? "true" : "false";
  root.dataset.safetyBoundarySummaryKey = summaryKey;
  root.dataset.handoffAuditTrailKey = auditKey;
  root.dataset.manualHandoffPacketKey = handoffKey;
  root.dataset.applicationReadinessPacketKey = readinessKey;
  root.dataset.guardedResumeCopyArtifactKey = artifactKey;
  root.dataset.humanOnlyApplicationBoundary = humanOnly ? "true" : "false";
  root.dataset.coreLlmInferenceWorkflowAutomatic = coreLlmWorkflowAutomatic ? "true" : "false";
  root.dataset.manualMutationRequiresOperatorAction = manualMutationGated ? "true" : "false";
  root.dataset.atsAutomationPerformed = atsAutomation ? "true" : "false";
  root.dataset.applicationSubmissionPerformed = submission ? "true" : "false";
  root.dataset.applyQueueEnqueued = queued ? "true" : "false";
  root.dataset.sourceResumeUnchanged = sourceUnchanged ? "true" : "false";
  root.dataset.sourceResumeOverwritten = sourceOverwritten ? "true" : "false";
  root.dataset.safetyBoundaryValidationStatus = validation;
  root.dataset.safetyBoundaryFallbackReason = fallbackReason;
  root.dataset.safetyBoundaryFallbackErrorClass = fallbackErrorClass;

  const parts = [
    `Safety boundary summary: ${enabled ? "enabled" : "default-off"}`,
    `requested ${requested ? "yes" : "no"}`,
    `created ${created ? "yes" : "no"}`,
    humanOnly ? "human-only boundary" : "",
    coreLlmWorkflowAutomatic ? "core LLM workflow-automatic" : "",
    manualMutationGated ? "manual mutation operator-gated" : "",
    `ATS automation ${atsAutomation ? "performed" : "not performed"}`,
    `submission ${submission ? "performed" : "not performed"}`,
    `queue ${queued ? "enqueued" : "not enqueued"}`,
    `source ${sourceUnchanged && !sourceOverwritten ? "unchanged" : "changed"}`,
    `fallback ${fallback ? "yes" : "no"}`,
    `validation ${validation}`,
    Number.isFinite(llmCapableCount) ? `llm-capable ${llmCapableCount}` : "",
    Number.isFinite(mutationCapableCount) ? `mutation-capable ${mutationCapableCount}` : "",
    Number.isFinite(forbiddenPathCount) ? `forbidden paths ${forbiddenPathCount}` : "",
    summaryKey ? `summary ${summaryKey}` : "",
    auditKey ? `audit ${auditKey}` : "",
    handoffKey ? `handoff ${handoffKey}` : "",
    readinessKey ? `readiness ${readinessKey}` : "",
    artifactKey ? `artifact ${artifactKey}` : "",
    fallbackReason ? `reason ${fallbackReason}` : "",
    fallbackErrorClass ? `error ${fallbackErrorClass}` : "",
  ].filter(Boolean);

  root.textContent = parts.join(" · ");
}

function getScanWorkspaceWorkflowReadinessCheckpointEnabled() {
  return getScanWorkspaceInput("scanWorkspaceWorkflowReadinessCheckpointToggle")?.checked === true;
}

function getScanWorkspaceWorkflowReadinessSummaryId() {
  return String(getScanWorkspaceInput("scanWorkspaceWorkflowReadinessSummaryId")?.value || "").trim();
}

function getScanWorkspaceWorkflowReadinessAuditTrailId() {
  return String(getScanWorkspaceInput("scanWorkspaceWorkflowReadinessAuditTrailId")?.value || "").trim();
}

function getScanWorkspaceWorkflowReadinessHandoffPacketId() {
  return String(getScanWorkspaceInput("scanWorkspaceWorkflowReadinessHandoffPacketId")?.value || "").trim();
}

function getScanWorkspaceWorkflowReadinessReadinessPacketId() {
  return String(getScanWorkspaceInput("scanWorkspaceWorkflowReadinessReadinessPacketId")?.value || "").trim();
}

function getScanWorkspaceWorkflowReadinessArtifactId() {
  return String(getScanWorkspaceInput("scanWorkspaceWorkflowReadinessArtifactId")?.value || "").trim();
}

function getScanWorkspaceWorkflowReadinessCheckpointPayload(payload = null) {
  const source = payload && typeof payload === "object"
    ? payload
    : getScanWorkspacePreloadPayloadForSurface();
  if (!source || typeof source !== "object") return null;

  const readback = source.human_only_workflow_readiness_checkpoint_readback;
  return readback && typeof readback === "object" ? readback : null;
}

function renderScanWorkspaceWorkflowReadinessCheckpointReadback(readbackPayload = null) {
  const root = getScanWorkspaceInput("scanWorkspaceWorkflowReadinessCheckpointReadback");
  if (!root) return;

  const readback = getScanWorkspaceWorkflowReadinessCheckpointPayload(readbackPayload);
  if (!readback) {
    root.textContent = "Workflow readiness checkpoint: default-off";
    root.dataset.workflowReadinessCheckpointEnabled = "false";
    root.dataset.workflowReadinessCheckpointCreated = "false";
    return;
  }

  const enabled = readback.workflow_readiness_checkpoint_enabled === true;
  const requested = readback.workflow_readiness_checkpoint_requested === true;
  const created = readback.workflow_readiness_checkpoint_created === true;
  const ready = readback.workflow_ready_for_human_handoff === true;
  const humanOnly = readback.human_only_application_boundary === true;
  const coreLlmWorkflowAutomatic = readback.core_llm_inference_workflow_automatic === true;
  const manualMutationGated = readback.manual_mutation_requires_operator_action === true;
  const atsAutomation = readback.ats_automation_performed === true;
  const submission = readback.application_submission_performed === true;
  const queued = readback.apply_queue_enqueued === true;
  const sourceUnchanged = readback.source_resume_unchanged !== false;
  const sourceOverwritten = readback.source_resume_overwritten === true;
  const fallback = readback.fallback_used !== false;
  const validation = String(readback.validation_status || "missing").trim() || "missing";
  const fallbackReason = String(readback.fallback_reason || "").trim();
  const fallbackErrorClass = String(readback.fallback_error_class || "").trim();
  const checkpointKey = String(readback.workflow_readiness_checkpoint_id || readback.stable_checkpoint_key || "").trim();
  const summaryKey = String(readback.safety_boundary_summary_id || readback.stable_summary_key || "").trim();
  const auditKey = String(readback.handoff_audit_trail_id || readback.stable_audit_key || "").trim();
  const handoffKey = String(readback.manual_handoff_packet_id || readback.stable_handoff_packet_key || "").trim();
  const readinessKey = String(readback.application_readiness_packet_id || readback.stable_readiness_packet_key || "").trim();
  const artifactKey = String(readback.artifact_id || readback.stable_artifact_key || "").trim();
  const llmCapableCount = Number(readback.llm_capable_action_count);
  const mutationCapableCount = Number(readback.mutation_capable_action_count);
  const forbiddenPathCount = Number(readback.forbidden_path_count);

  root.dataset.workflowReadinessCheckpointEnabled = enabled ? "true" : "false";
  root.dataset.workflowReadinessCheckpointRequested = requested ? "true" : "false";
  root.dataset.workflowReadinessCheckpointCreated = created ? "true" : "false";
  root.dataset.workflowReadinessCheckpointKey = checkpointKey;
  root.dataset.safetyBoundarySummaryKey = summaryKey;
  root.dataset.handoffAuditTrailKey = auditKey;
  root.dataset.manualHandoffPacketKey = handoffKey;
  root.dataset.applicationReadinessPacketKey = readinessKey;
  root.dataset.guardedResumeCopyArtifactKey = artifactKey;
  root.dataset.humanOnlyApplicationBoundary = humanOnly ? "true" : "false";
  root.dataset.coreLlmInferenceWorkflowAutomatic = coreLlmWorkflowAutomatic ? "true" : "false";
  root.dataset.manualMutationRequiresOperatorAction = manualMutationGated ? "true" : "false";
  root.dataset.workflowReadyForHumanHandoff = ready ? "true" : "false";
  root.dataset.atsAutomationPerformed = atsAutomation ? "true" : "false";
  root.dataset.applicationSubmissionPerformed = submission ? "true" : "false";
  root.dataset.applyQueueEnqueued = queued ? "true" : "false";
  root.dataset.sourceResumeUnchanged = sourceUnchanged ? "true" : "false";
  root.dataset.sourceResumeOverwritten = sourceOverwritten ? "true" : "false";
  root.dataset.workflowReadinessValidationStatus = validation;
  root.dataset.workflowReadinessFallbackReason = fallbackReason;
  root.dataset.workflowReadinessFallbackErrorClass = fallbackErrorClass;

  const parts = [
    `Workflow readiness checkpoint: ${enabled ? "enabled" : "default-off"}`,
    `requested ${requested ? "yes" : "no"}`,
    `created ${created ? "yes" : "no"}`,
    `ready ${ready ? "yes" : "no"}`,
    humanOnly ? "human-only boundary" : "",
    coreLlmWorkflowAutomatic ? "core LLM workflow-automatic" : "",
    manualMutationGated ? "manual mutation operator-gated" : "",
    `ATS automation ${atsAutomation ? "performed" : "not performed"}`,
    `submission ${submission ? "performed" : "not performed"}`,
    `queue ${queued ? "enqueued" : "not enqueued"}`,
    `source ${sourceUnchanged && !sourceOverwritten ? "unchanged" : "changed"}`,
    `fallback ${fallback ? "yes" : "no"}`,
    `validation ${validation}`,
    Number.isFinite(llmCapableCount) ? `llm-capable ${llmCapableCount}` : "",
    Number.isFinite(mutationCapableCount) ? `mutation-capable ${mutationCapableCount}` : "",
    Number.isFinite(forbiddenPathCount) ? `forbidden paths ${forbiddenPathCount}` : "",
    checkpointKey ? `checkpoint ${checkpointKey}` : "",
    summaryKey ? `summary ${summaryKey}` : "",
    auditKey ? `audit ${auditKey}` : "",
    handoffKey ? `handoff ${handoffKey}` : "",
    readinessKey ? `readiness ${readinessKey}` : "",
    artifactKey ? `artifact ${artifactKey}` : "",
    fallbackReason ? `reason ${fallbackReason}` : "",
    fallbackErrorClass ? `error ${fallbackErrorClass}` : "",
  ].filter(Boolean);

  root.textContent = parts.join(" · ");
}

function getScanWorkspaceAgenticWorkflowIntegrationPayload(payload = null) {
  const source = payload && typeof payload === "object"
    ? payload
    : getScanWorkspacePreloadPayloadForSurface();
  if (!source || typeof source !== "object") return null;

  const readback = source.agentic_workflow_integration_readback;
  return readback && typeof readback === "object" ? readback : null;
}

function renderScanWorkspaceAgenticWorkflowIntegrationReadback(readbackPayload = null) {
  const root = getScanWorkspaceInput("scanWorkspaceAgenticWorkflowIntegrationReadback");
  if (!root) return;

  const readback = getScanWorkspaceAgenticWorkflowIntegrationPayload(readbackPayload);
  if (!readback) {
    root.textContent = "Agentic workflow demo readiness: waiting for existing scan/evaluation readback";
    root.dataset.agenticWorkflowIntegrationEnabled = "false";
    root.dataset.agenticWorkflowIntegrationPerformed = "false";
    return;
  }

  const enabled = readback.agentic_workflow_integration_enabled === true;
  const requested = readback.agentic_workflow_integration_requested === true;
  const performed = readback.agentic_workflow_integration_performed === true;
  const userStarted = readback.user_started_scan_or_evaluation === true;
  const coreLlmWorkflowAutomatic = readback.core_llm_inference_workflow_automatic === true;
  const jdSignals = readback.jd_signal_extraction_available === true;
  const skills = readback.skills_extraction_available === true;
  const requirements = readback.requirements_extraction_available === true;
  const evidence = readback.resume_evidence_available === true;
  const scoring = readback.scoring_ranking_available === true;
  const nextActions = readback.planning_workspace_next_actions_available === true;
  const tailoringAction = readback.tailoring_suggestion_action_available === true;
  const exactChangeAction = readback.exact_change_proposal_action_available === true;
  const manualMutationGated = readback.manual_mutation_requires_operator_action === true;
  const humanOnly = readback.human_only_application_boundary === true;
  const atsAutomation = readback.ats_automation_performed === true;
  const submission = readback.application_submission_performed === true;
  const queued = readback.apply_queue_enqueued === true;
  const sourceUnchanged = readback.source_resume_unchanged !== false;
  const sourceOverwritten = readback.source_resume_overwritten === true;
  const fallback = readback.fallback_used !== false;
  const validation = String(readback.validation_status || "missing").trim() || "missing";
  const jdSignalStatus = String(readback.jd_signal_extraction_status || "").trim();
  const skillsStatus = String(readback.skills_extraction_status || "").trim();
  const requirementsStatus = String(readback.requirements_extraction_status || "").trim();
  const evidenceStatus = String(readback.resume_evidence_status || "").trim();
  const llmEvaluationStatus = String(readback.llm_evaluation_status || "").trim();
  const scoringStatus = String(readback.scoring_ranking_status || "").trim();
  const nextActionsStatus = String(readback.planning_workspace_next_actions_status || "").trim();
  const fallbackReason = String(readback.fallback_reason || "").trim();
  const fallbackErrorClass = String(readback.fallback_error_class || "").trim();

  root.dataset.agenticWorkflowIntegrationEnabled = enabled ? "true" : "false";
  root.dataset.agenticWorkflowIntegrationRequested = requested ? "true" : "false";
  root.dataset.agenticWorkflowIntegrationPerformed = performed ? "true" : "false";
  root.dataset.userStartedScanOrEvaluation = userStarted ? "true" : "false";
  root.dataset.coreLlmInferenceWorkflowAutomatic = coreLlmWorkflowAutomatic ? "true" : "false";
  root.dataset.jdSignalExtractionAvailable = jdSignals ? "true" : "false";
  root.dataset.jdSignalExtractionStatus = jdSignalStatus;
  root.dataset.skillsExtractionAvailable = skills ? "true" : "false";
  root.dataset.skillsExtractionStatus = skillsStatus;
  root.dataset.requirementsExtractionAvailable = requirements ? "true" : "false";
  root.dataset.requirementsExtractionStatus = requirementsStatus;
  root.dataset.resumeEvidenceAvailable = evidence ? "true" : "false";
  root.dataset.resumeEvidenceStatus = evidenceStatus;
  root.dataset.llmEvaluationStatus = llmEvaluationStatus;
  root.dataset.scoringRankingAvailable = scoring ? "true" : "false";
  root.dataset.scoringRankingStatus = scoringStatus;
  root.dataset.planningWorkspaceNextActionsAvailable = nextActions ? "true" : "false";
  root.dataset.planningWorkspaceNextActionsStatus = nextActionsStatus;
  root.dataset.tailoringSuggestionActionAvailable = tailoringAction ? "true" : "false";
  root.dataset.exactChangeProposalActionAvailable = exactChangeAction ? "true" : "false";
  root.dataset.manualMutationRequiresOperatorAction = manualMutationGated ? "true" : "false";
  root.dataset.humanOnlyApplicationBoundary = humanOnly ? "true" : "false";
  root.dataset.atsAutomationPerformed = atsAutomation ? "true" : "false";
  root.dataset.applicationSubmissionPerformed = submission ? "true" : "false";
  root.dataset.applyQueueEnqueued = queued ? "true" : "false";
  root.dataset.sourceResumeUnchanged = sourceUnchanged ? "true" : "false";
  root.dataset.sourceResumeOverwritten = sourceOverwritten ? "true" : "false";
  root.dataset.agenticWorkflowValidationStatus = validation;
  root.dataset.agenticWorkflowFallbackReason = fallbackReason;
  root.dataset.agenticWorkflowFallbackErrorClass = fallbackErrorClass;

  const parts = [
    `Agentic workflow demo readiness: ${performed ? "demo-ready scan/evaluation connected" : "waiting for readback"}`,
    `integration ${enabled ? "enabled" : "default-off"}`,
    requested ? "existing readback requested" : "existing readback not requested",
    userStarted ? "user-started scan/evaluation" : "waiting for user-started scan/evaluation",
    coreLlmWorkflowAutomatic ? "analysis automation: workflow-automatic core LLM inference" : "",
    jdSignals ? `JD signal extraction ${jdSignalStatus || "available"}` : "",
    skills ? `skills extraction ${skillsStatus || "available"}` : "",
    requirements ? `requirements extraction ${requirementsStatus || "available"}` : "",
    evidence ? `resume evidence ${evidenceStatus || "available"}` : "",
    llmEvaluationStatus ? `LLM evaluation ${llmEvaluationStatus}` : "",
    scoring ? `scoring/ranking readback ${scoringStatus || "available"}` : "",
    nextActions ? `planning workspace next actions ${nextActionsStatus || "available"}` : "",
    tailoringAction ? "tailoring suggestion action: explicit manual next action" : "",
    exactChangeAction ? "exact change proposal action: explicit manual next action" : "",
    manualMutationGated ? "manual-only mutation: operator action required before any resume change" : "",
    humanOnly ? "human-only handoff/application boundary" : "",
    atsAutomation ? "attention: ATS automation reported" : "safe: no ATS automation",
    submission ? "attention: application submission reported" : "safe: no application submission",
    queued ? "attention: apply queue enqueue reported" : "safe: no apply queue enqueue",
    `source resume ${sourceUnchanged && !sourceOverwritten ? "unchanged" : "changed"}`,
    `fallback ${fallback ? "yes" : "no"}`,
    `validation ${validation}`,
    fallbackReason ? `reason ${fallbackReason}` : "",
    fallbackErrorClass ? `error ${fallbackErrorClass}` : "",
  ].filter(Boolean);

  root.textContent = parts.join(" · ");
}

function getScanWorkspaceProductionReadinessCheckpointPayload(payload = null) {
  const source = payload && typeof payload === "object"
    ? payload
    : getScanWorkspacePreloadPayloadForSurface();
  if (!source || typeof source !== "object") return null;

  const readback = source.agentic_workflow_production_readiness_checkpoint;
  return readback && typeof readback === "object" ? readback : null;
}

function renderScanWorkspaceProductionReadinessCheckpoint(readbackPayload = null) {
  const root = getScanWorkspaceInput("scanWorkspaceProductionReadinessCheckpointReadback");
  if (!root) return;

  const checkpoint = getScanWorkspaceProductionReadinessCheckpointPayload(readbackPayload);
  if (!checkpoint) {
    root.textContent = "Demo readiness: backend checkpoint readback waiting for existing data";
    root.dataset.productionReadinessCheckpointEnabled = "false";
    root.dataset.productionReadinessCheckpointPerformed = "false";
    return;
  }

  const enabled = checkpoint.production_readiness_checkpoint_enabled === true;
  const requested = checkpoint.production_readiness_checkpoint_requested === true;
  const performed = checkpoint.production_readiness_checkpoint_performed === true;
  const integrationAvailable = checkpoint.agentic_workflow_integration_available === true;
  const userStarted = checkpoint.user_started_scan_or_evaluation === true;
  const coreLlmWorkflowAutomatic = checkpoint.core_llm_inference_workflow_automatic === true;
  const planningActions = checkpoint.planning_workspace_next_actions_available === true;
  const guardedArtifact = checkpoint.guarded_resume_artifact_path_available === true;
  const artifactVerification = checkpoint.artifact_verification_path_available === true;
  const humanHandoff = checkpoint.human_only_handoff_path_available === true;
  const readyForUxPolish = checkpoint.workflow_ready_for_ux_polish === true;
  const backendComplete = checkpoint.backend_agentic_workflow_complete === true;
  const manualMutationGated = checkpoint.manual_mutation_requires_operator_action === true;
  const humanOnly = checkpoint.human_only_application_boundary === true;
  const atsAutomation = checkpoint.ats_automation_performed === true;
  const submission = checkpoint.application_submission_performed === true;
  const queued = checkpoint.apply_queue_enqueued === true;
  const sourceUnchanged = checkpoint.source_resume_unchanged !== false;
  const sourceOverwritten = checkpoint.source_resume_overwritten === true;
  const validation = String(checkpoint.validation_status || "missing").trim() || "missing";
  const fallback = checkpoint.fallback_used !== false;
  const fallbackReason = String(checkpoint.fallback_reason || "").trim();
  const fallbackErrorClass = String(checkpoint.fallback_error_class || "").trim();

  root.dataset.productionReadinessCheckpointEnabled = enabled ? "true" : "false";
  root.dataset.productionReadinessCheckpointRequested = requested ? "true" : "false";
  root.dataset.productionReadinessCheckpointPerformed = performed ? "true" : "false";
  root.dataset.agenticWorkflowIntegrationAvailable = integrationAvailable ? "true" : "false";
  root.dataset.userStartedScanOrEvaluation = userStarted ? "true" : "false";
  root.dataset.coreLlmInferenceWorkflowAutomatic = coreLlmWorkflowAutomatic ? "true" : "false";
  root.dataset.planningWorkspaceNextActionsAvailable = planningActions ? "true" : "false";
  root.dataset.guardedResumeArtifactPathAvailable = guardedArtifact ? "true" : "false";
  root.dataset.artifactVerificationPathAvailable = artifactVerification ? "true" : "false";
  root.dataset.humanOnlyHandoffPathAvailable = humanHandoff ? "true" : "false";
  root.dataset.workflowReadyForUxPolish = readyForUxPolish ? "true" : "false";
  root.dataset.backendAgenticWorkflowComplete = backendComplete ? "true" : "false";
  root.dataset.manualMutationRequiresOperatorAction = manualMutationGated ? "true" : "false";
  root.dataset.humanOnlyApplicationBoundary = humanOnly ? "true" : "false";
  root.dataset.atsAutomationPerformed = atsAutomation ? "true" : "false";
  root.dataset.applicationSubmissionPerformed = submission ? "true" : "false";
  root.dataset.applyQueueEnqueued = queued ? "true" : "false";
  root.dataset.sourceResumeUnchanged = sourceUnchanged ? "true" : "false";
  root.dataset.sourceResumeOverwritten = sourceOverwritten ? "true" : "false";
  root.dataset.productionReadinessValidationStatus = validation;
  root.dataset.productionReadinessFallbackReason = fallbackReason;
  root.dataset.productionReadinessFallbackErrorClass = fallbackErrorClass;

  const parts = [
    `Demo readiness: ${backendComplete ? "backend agentic workflow complete" : "backend readback pending"}`,
    `production checkpoint ${enabled ? "enabled" : "default-off"}`,
    requested ? "existing readback requested" : "existing readback not requested",
    performed ? "checkpoint performed" : "checkpoint pending",
    integrationAvailable ? "end-to-end agentic workflow integration" : "",
    userStarted ? "user-started scan/evaluation" : "",
    coreLlmWorkflowAutomatic ? "analysis automation: workflow-automatic core LLM inference" : "",
    planningActions ? "planning workspace next actions" : "",
    guardedArtifact ? "guarded resume artifact path: explicit manual/operator path" : "",
    artifactVerification ? "artifact verification path: explicit manual/operator path" : "",
    humanHandoff ? "human-only handoff path" : "",
    readyForUxPolish ? "ready for UX polish / demo readiness" : "not ready for UX polish yet",
    backendComplete ? "backend agentic workflow complete" : "backend agentic workflow incomplete",
    manualMutationGated ? "manual-only mutation: operator action required before any resume change" : "",
    humanOnly ? "human-only handoff/application boundary" : "",
    "ApplyLens never applies for jobs",
    atsAutomation ? "attention: ATS automation reported" : "safe: no ATS automation",
    submission ? "attention: application submission reported" : "safe: no application submission",
    queued ? "attention: apply queue enqueue reported" : "safe: no apply queue enqueue",
    `source resume ${sourceUnchanged && !sourceOverwritten ? "unchanged" : "changed"}`,
    `fallback ${fallback ? "yes" : "no"}`,
    `validation ${validation}`,
    fallbackReason ? `reason ${fallbackReason}` : "",
    fallbackErrorClass ? `error ${fallbackErrorClass}` : "",
  ].filter(Boolean);

  root.textContent = parts.join(" · ");
}

function getScanWorkspaceHasTailoringPreviewContext() {
  const context = getScanWorkspaceContext();
  return Boolean(getScanWorkspaceArtifactKey(context) && context?.resumeName);
}

function firstNonEmptyScanWorkspaceText(...values) {
  for (const value of values) {
    const text = String(value || "").trim();
    if (text && text !== "-") return text;
  }

  return "";
}

function getScanWorkspaceJobRecordCandidates() {
  const payload = getScanWorkspacePreloadPayloadForSurface();
  return [
    payload?.selected_jd_record,
    payload?.job_snapshot,
    payload?.job,
  ].filter((record) => record && typeof record === "object");
}

function getScanWorkspaceLoadedJobDescriptionText() {
  const intakeDescription = String(
    getScanWorkspaceInput("scanWorkspaceJobDescriptionInput")?.value || ""
  ).trim();
  if (intakeDescription) return intakeDescription;

  for (const record of getScanWorkspaceJobRecordCandidates()) {
    const text = firstNonEmptyScanWorkspaceText(
      record.description_text,
      record.description,
      record.job_description,
      record.raw_description,
      Array.isArray(record.requirements) ? record.requirements.join("\n") : record.requirements,
      Array.isArray(record.responsibilities) ? record.responsibilities.join("\n") : record.responsibilities,
      Array.isArray(record.qualifications) ? record.qualifications.join("\n") : record.qualifications
    );
    if (text) return text;
  }

  return "";
}

function getScanWorkspaceLoadedJobLabel() {
  const company = firstNonEmptyScanWorkspaceText(
    getScanWorkspaceInput("scanWorkspaceCompanyInput")?.value,
    ...getScanWorkspaceJobRecordCandidates().map((record) => record.company || record.job_company)
  );
  const title = firstNonEmptyScanWorkspaceText(
    getScanWorkspaceInput("scanWorkspaceRoleInput")?.value,
    ...getScanWorkspaceJobRecordCandidates().map((record) => record.title || record.job_title)
  );

  return [company, title].filter(Boolean).join(" / ") || "Loaded job";
}

function normalizeScanWorkspaceSurface(surface) {
  const safeSurface = String(surface || "").trim().toLowerCase();
  if (safeSurface === "job_description") return "job_description";
  if (safeSurface === "cover_letter") return "cover_letter";
  return "resume";
}

function updateScanWorkspaceSurfaceTabs() {
  document.querySelectorAll("[data-scan-surface]").forEach((button) => {
    const surface = normalizeScanWorkspaceSurface(button.dataset.scanSurface || "");
    const isDisabled = button.disabled || button.getAttribute("aria-disabled") === "true";
    const isActive = !isDisabled && surface === scanWorkspacePreviewState.activeSurface;
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-pressed", isActive ? "true" : "false");
  });
}

function renderScanWorkspaceJobDescriptionSurfaceInto() {
  const root = getScanWorkspaceInput("scanWorkspaceLiveDraftPreview");
  const previewStatus = getScanWorkspaceInput("scanWorkspacePreviewStatus");
  const previewMeta = getScanWorkspaceInput("scanWorkspacePreviewMeta");
  if (!root) return;

  const descriptionText = getScanWorkspaceLoadedJobDescriptionText();
  const jobLabel = getScanWorkspaceLoadedJobLabel();
  if (previewStatus) previewStatus.textContent = "Job description";
  if (previewMeta) previewMeta.textContent = jobLabel;

  root.innerHTML = descriptionText
    ? `
      <article class="scan-workspace-job-description-panel">
        <div class="scan-workspace-job-description-kicker">Job Description</div>
        <h3>${scanWorkspaceEscapeHtml(jobLabel)}</h3>
        <pre>${scanWorkspaceEscapeHtml(descriptionText)}</pre>
      </article>
    `
    : `
      <div class="tailoring-empty-state">
        No loaded job description is available for this scan.
      </div>
    `;
}

function getScanWorkspaceContext() {
  const root = getScanWorkspacePageRoot();
  if (!root) return null;

  return {
    tailoringJsonPath: String(root.dataset.tailoringJsonPath || "").trim(),
    tailoringJsonKey: String(root.dataset.tailoringJsonKey || "").trim(),
    resumeName: String(root.dataset.resumeName || "").trim(),
    packetJsonPath: String(root.dataset.packetJsonPath || "").trim(),
    packetJsonKey: String(root.dataset.packetJsonKey || "").trim(),
    planningOutputDir: String(root.dataset.planningOutputDir || "").trim(),
  };
}

function getScanWorkspaceArtifactKey(context) {
  return String(context?.tailoringJsonKey || context?.tailoringJsonPath || "").trim();
}

function getScanWorkspaceBasePacketKey(context) {
  return String(context?.packetJsonKey || context?.packetJsonPath || "").trim();
}

function isScanWorkspaceOptionalTailoringArtifactPath(value) {
  const name = String(value || "")
    .trim()
    .replace(/\\/g, "/")
    .split("/")
    .pop()
    .toLowerCase();
  return name.endsWith("__tailoring.json") || name.endsWith("_tailoring.json");
}

function normalizeScanWorkspaceResumePreviewName(value) {
  const safeName = String(value || "")
    .trim()
    .replace(/\\/g, "/")
    .split("/")
    .pop()
    .trim();
  if (!safeName || safeName.toLowerCase().endsWith(".json") || isScanWorkspaceOptionalTailoringArtifactPath(safeName)) {
    return "";
  }
  return safeName;
}

function buildScanWorkspacePlanningEndpoint(path, outputDir = "") {
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

function getScanWorkspaceHasPreselectedResume() {
  const root = getScanWorkspacePageRoot();
  if (!root) return false;
  return Boolean(String(root.dataset.resumeName || "").trim());
}

function getScanWorkspaceSelectedResumeName() {
  const select = getScanWorkspaceInput("scanWorkspaceResumeSelect");
  const selected = String(select?.value || "").trim();
  if (selected) return selected;

  const root = getScanWorkspacePageRoot();
  return String(root?.dataset?.resumeName || "").trim();
}

function setScanWorkspaceResumeSelection(resumeName = "") {
  const select = getScanWorkspaceInput("scanWorkspaceResumeSelect");
  const safeName = String(resumeName || "").trim();
  if (!select) return;
  if (safeName) {
    select.dataset.initialResume = safeName;
  }
  renderScanWorkspaceSavedResumeOptions();
  if (safeName) {
    select.value = safeName;
  }
  scanWorkspaceIntakeState.savedResumeName = String(select.value || safeName || "").trim();
  updateScanWorkspaceIntakeActions();
}

function renderScanWorkspaceSavedResumeOptions() {
  const select = getScanWorkspaceInput("scanWorkspaceResumeSelect");
  if (!select) return;

  const root = getScanWorkspacePageRoot();
  const initialResume = String(
    select.dataset.initialResume ||
    root?.dataset?.resumeName ||
    ""
  ).trim();
  const selectedResume = String(select.value || initialResume || "").trim();
  const resumes = Array.isArray(scanWorkspaceSavedResumeState.resumes)
    ? scanWorkspaceSavedResumeState.resumes
    : [];

  if (scanWorkspaceSavedResumeState.isLoading) {
    select.innerHTML = `<option value="">Loading saved resumes...</option>`;
    select.disabled = true;
    return;
  }

  if (scanWorkspaceSavedResumeState.lastError) {
    select.innerHTML = `<option value="">Could not load saved resumes</option>`;
    select.disabled = true;
    return;
  }

  if (!resumes.length) {
    if (initialResume) {
      select.disabled = false;
      select.innerHTML = `<option value="${scanWorkspaceEscapeHtml(initialResume)}" selected>${scanWorkspaceEscapeHtml(initialResume)}</option>`;
      scanWorkspaceIntakeState.savedResumeName = initialResume;
      return;
    }
    select.innerHTML = `<option value="">No saved resumes in profile</option>`;
    select.disabled = true;
    return;
  }

  const hasSelectedResume = resumes.some((resume) => {
    return String(resume?.resume_name || "").trim() === selectedResume;
  });
  const effectiveSelected = hasSelectedResume || initialResume === selectedResume ? selectedResume : "";

  select.disabled = false;
  select.innerHTML = [
    `<option value="">Select a saved resume</option>`,
    effectiveSelected && !hasSelectedResume
      ? `<option value="${scanWorkspaceEscapeHtml(effectiveSelected)}" selected>${scanWorkspaceEscapeHtml(effectiveSelected)}</option>`
      : "",
    ...resumes.map((resume) => {
      const resumeName = String(resume?.resume_name || "").trim();
      const selected = resumeName && resumeName === effectiveSelected ? " selected" : "";
      return `<option value="${scanWorkspaceEscapeHtml(resumeName)}"${selected}>${scanWorkspaceEscapeHtml(resumeName)}</option>`;
    }),
  ].join("");

  scanWorkspaceIntakeState.savedResumeName = effectiveSelected;
}

async function loadScanWorkspaceSavedResumes() {
  const select = getScanWorkspaceInput("scanWorkspaceResumeSelect");
  if (!select || select.dataset.loaded === "true" || scanWorkspaceSavedResumeState.isLoading) {
    return;
  }

  scanWorkspaceSavedResumeState.isLoading = true;
  scanWorkspaceSavedResumeState.lastError = "";
  renderScanWorkspaceSavedResumeOptions();

  try {
    const response = await fetch("/profile/resumes", {
      headers: { Accept: "application/json" },
    });
    if (!response.ok) {
      throw new Error(`Saved resumes failed to load (${response.status})`);
    }

    const data = await response.json();
    scanWorkspaceSavedResumeState.resumes = Array.isArray(data?.resumes) ? data.resumes : [];
    select.dataset.loaded = "true";
  } catch (err) {
    scanWorkspaceSavedResumeState.resumes = [];
    scanWorkspaceSavedResumeState.lastError =
      err instanceof Error ? err.message : "Saved resumes failed to load.";
  } finally {
    scanWorkspaceSavedResumeState.isLoading = false;
    renderScanWorkspaceSavedResumeOptions();
    updateScanWorkspaceIntakeActions();
  }
}

function setScanWorkspaceResumeFileUi(fileName = "", message = "", tone = "") {
  const fileNameNode = getScanWorkspaceInput("scanWorkspaceResumeFileName");
  const statusNode = getScanWorkspaceInput("scanWorkspaceResumeFileStatus");

  if (fileNameNode) {
    fileNameNode.textContent = fileName || "No file selected";
  }

  if (statusNode) {
    statusNode.textContent = message || "";
    statusNode.classList.toggle("is-error", tone === "error");
    statusNode.classList.toggle("is-success", tone === "success");
  }
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
    if (scanWorkspacePreviewState.activeSurface === "job_description") {
      renderScanWorkspaceJobDescriptionSurfaceInto();
    } else {
      ensureScanWorkspaceDocumentPreviewLoaded();
    }
  }

  if (normalizedMode === "compare") {
    renderScanWorkspaceCompareShell();
    ensureScanWorkspaceCompareLoaded();
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
  const jobUrlInput = getScanWorkspaceInput("scanWorkspaceJobUrlInput");
  const resumeFileInput = getScanWorkspaceInput("scanWorkspaceResumeFileInput");
  const resumeTextInput = getScanWorkspaceInput("scanWorkspaceResumeTextInput");
  const jobDescriptionInput = getScanWorkspaceInput("scanWorkspaceJobDescriptionInput");

  scanWorkspaceIntakeState.company = String(companyInput?.value || "").trim();
  scanWorkspaceIntakeState.role = String(roleInput?.value || "").trim();
  scanWorkspaceIntakeState.jobUrl = String(jobUrlInput?.value || "").trim();
  scanWorkspaceIntakeState.savedResumeName = getScanWorkspaceSelectedResumeName();
  scanWorkspaceIntakeState.resumeFileName = String(resumeFileInput?.files?.[0]?.name || "").trim();
  scanWorkspaceIntakeState.resumeText = String(resumeTextInput?.value || "").trim();
  scanWorkspaceIntakeState.jobDescriptionText = String(jobDescriptionInput?.value || "").trim();

  return { ...scanWorkspaceIntakeState };
}

function getScanWorkspaceIntakeValidation(draft = readScanWorkspaceIntakeDraft()) {
  const missing = [];
  const hasResume = Boolean(draft.savedResumeName);
  if (!hasResume) missing.push({ key: "resume", message: "Select a saved resume from your profile." });
  if (!draft.company) missing.push({ key: "company", message: "Company is required." });
  if (!draft.role) missing.push({ key: "role", message: "Role is required." });
  if (!draft.jobUrl) missing.push({ key: "jobUrl", message: "Job posting URL is required." });
  if (!draft.jobDescriptionText) missing.push({ key: "jobDescription", message: "Job description is required." });
  return {
    ok: missing.length === 0,
    missing,
  };
}

function setScanWorkspaceFieldError(inputId, errorId, message = "") {
  const input = getScanWorkspaceInput(inputId);
  const error = getScanWorkspaceInput(errorId);
  if (input) {
    input.classList.toggle("is-invalid", Boolean(message));
    input.setAttribute("aria-invalid", message ? "true" : "false");
  }
  if (error) {
    error.textContent = message;
    error.hidden = !message;
  }
}

function renderScanWorkspaceIntakeValidation(validation) {
  const banner = getScanWorkspaceInput("scanWorkspaceIntakeValidation");
  const messages = Array.isArray(validation?.missing) ? validation.missing : [];
  const messageByKey = new Map(messages.map((item) => [item.key, item.message]));

  setScanWorkspaceFieldError("scanWorkspaceCompanyInput", "scanWorkspaceCompanyError", messageByKey.get("company") || "");
  setScanWorkspaceFieldError("scanWorkspaceRoleInput", "scanWorkspaceRoleError", messageByKey.get("role") || "");
  setScanWorkspaceFieldError("scanWorkspaceJobUrlInput", "scanWorkspaceJobUrlError", messageByKey.get("jobUrl") || "");
  setScanWorkspaceFieldError("scanWorkspaceJobDescriptionInput", "scanWorkspaceJobDescriptionError", messageByKey.get("jobDescription") || "");
  setScanWorkspaceFieldError("scanWorkspaceResumeSelect", "scanWorkspaceResumeError", messageByKey.get("resume") || "");

  if (!banner) return;
  if (!messages.length) {
    banner.textContent = "";
    banner.classList.remove("is-visible");
    return;
  }

  banner.textContent = messages.map((item) => item.message).join(" ");
  banner.classList.add("is-visible");
}

function updateScanWorkspaceIntakeActions() {
  const startBtn = getScanWorkspaceInput("scanWorkspaceStartScanBtn");
  if (!startBtn) return;

  const draft = readScanWorkspaceIntakeDraft();
  const validation = getScanWorkspaceIntakeValidation(draft);
  renderScanWorkspaceIntakeValidation(validation);

  startBtn.disabled = !validation.ok;
  startBtn.textContent = String(getScanWorkspacePageRoot()?.dataset?.rescanScanId || "").trim()
    ? "Update scan"
    : "Start scan";
}

function clearScanWorkspaceIntakeForm() {
  const root = getScanWorkspacePageRoot();
  const companyInput = getScanWorkspaceInput("scanWorkspaceCompanyInput");
  const roleInput = getScanWorkspaceInput("scanWorkspaceRoleInput");
  const jobUrlInput = getScanWorkspaceInput("scanWorkspaceJobUrlInput");
  const resumeSelect = getScanWorkspaceInput("scanWorkspaceResumeSelect");
  const resumeFileInput = getScanWorkspaceInput("scanWorkspaceResumeFileInput");
  const resumeTextInput = getScanWorkspaceInput("scanWorkspaceResumeTextInput");
  const jobDescriptionInput = getScanWorkspaceInput("scanWorkspaceJobDescriptionInput");

  if (companyInput) companyInput.value = "";
  if (roleInput) roleInput.value = "";
  if (jobUrlInput) jobUrlInput.value = "";
  if (resumeSelect) resumeSelect.value = "";
  if (resumeFileInput) resumeFileInput.value = "";
  if (resumeTextInput) resumeTextInput.value = "";
  if (jobDescriptionInput) jobDescriptionInput.value = "";
  setScanWorkspaceResumeFileUi();

  scanWorkspaceIntakeState.company = "";
  scanWorkspaceIntakeState.role = "";
  scanWorkspaceIntakeState.jobUrl = "";
  scanWorkspaceIntakeState.savedResumeName = "";
  scanWorkspaceIntakeState.resumeFileName = "";
  scanWorkspaceIntakeState.resumeText = "";
  scanWorkspaceIntakeState.jobDescriptionText = "";
  if (root) {
    root.dataset.rescanScanId = "";
  }

  updateScanWorkspaceIntakeActions();
}

function bindScanWorkspaceIntakeForm() {
  const watchedIds = [
    "scanWorkspaceCompanyInput",
    "scanWorkspaceRoleInput",
    "scanWorkspaceJobUrlInput",
    "scanWorkspaceResumeSelect",
    "scanWorkspaceResumeFileInput",
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
    input.addEventListener("change", () => {
      updateScanWorkspaceIntakeActions();
    });
  });

  const browseBtn = getScanWorkspaceInput("scanWorkspaceResumeBrowseBtn");
  const resumeFileInput = getScanWorkspaceInput("scanWorkspaceResumeFileInput");
  if (browseBtn && resumeFileInput && browseBtn.dataset.bound !== "true") {
    browseBtn.dataset.bound = "true";
    browseBtn.addEventListener("click", () => {
      resumeFileInput.click();
    });
  }

  if (resumeFileInput && resumeFileInput.dataset.extractBound !== "true") {
    resumeFileInput.dataset.extractBound = "true";
    resumeFileInput.addEventListener("change", async () => {
      updateScanWorkspaceIntakeActions();
      await handleScanWorkspaceResumeFileSelected();
    });
  }

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
    startBtn.addEventListener("click", async () => {
      const validation = getScanWorkspaceIntakeValidation();
      renderScanWorkspaceIntakeValidation(validation);
      updateScanWorkspaceIntakeActions();
      if (!validation.ok) return;
      await beginScanWorkspaceProcessing();
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

  const resumeSource = draft.savedResumeName
    ? `Saved resume: ${draft.savedResumeName}`
    : "Missing";

  const jobDescriptionValue = draft.jobDescriptionText
    ? `${draft.jobDescriptionText.length} chars`
    : "Missing";

  const companyValue = draft.company || "Not set";
  const roleValue = draft.role || "Not set";
  const jobUrlValue = draft.jobUrl ? "Provided" : "Not provided";

  const cards = [
    { label: "Resume source", value: resumeSource },
    { label: "Job description", value: jobDescriptionValue },
    { label: "Company", value: companyValue },
    { label: "Role", value: roleValue },
    { label: "Posting URL", value: jobUrlValue },
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
  const isFinished = scanWorkspaceProcessingState.status === "complete";

  return SCAN_WORKSPACE_PROCESSING_STAGES.map((stage, index) => {
    let stateClass = "";
    let stateLabel = "Pending";

    if (isFinished || index < currentIndex) {
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
  const complete = getScanWorkspaceInput("scanWorkspaceProcessingComplete");

  const stage = getScanWorkspaceProcessingStage(scanWorkspaceProcessingState.currentStageKey);
  const draft = scanWorkspaceProcessingState.intakeDraft;
  const isComplete = scanWorkspaceProcessingState.status === "complete";

  if (badge) badge.textContent = isComplete ? "Complete" : stage.title;
  if (title) title.textContent = isComplete ? "Scan report ready" : "Structuring your content with AI";
  if (subtitle) subtitle.textContent = isComplete ? "Review the generated match report when you are ready." : stage.description;
  if (summary) summary.innerHTML = buildScanWorkspaceProcessingSummaryHtml(draft);
  if (stepList) stepList.innerHTML = buildScanWorkspaceProcessingStepsHtml(stage.key);
  if (complete) complete.hidden = !isComplete;

  if (note) {
    note.textContent =
      scanWorkspaceProcessingState.note ||
      "Waiting for the real scan runner. This phase adds the processing shell and stage model only.";
  }
}

function readScanWorkspaceFileAsBase64(file) {
  return new Promise((resolve, reject) => {
    if (!file) {
      resolve("");
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      const result = String(reader.result || "");
      const base64 = result.includes(",") ? result.split(",").pop() : result;
      resolve(base64 || "");
    };
    reader.onerror = () => reject(new Error("Failed to read uploaded resume file."));
    reader.readAsDataURL(file);
  });
}

async function handleScanWorkspaceResumeFileSelected() {
  const resumeFileInput = getScanWorkspaceInput("scanWorkspaceResumeFileInput");
  const resumeTextInput = getScanWorkspaceInput("scanWorkspaceResumeTextInput");
  const file = resumeFileInput?.files?.[0] || null;

  if (!file) {
    setScanWorkspaceResumeFileUi();
    updateScanWorkspaceIntakeActions();
    return;
  }

  setScanWorkspaceResumeFileUi(file.name, "Extracting resume text...");

  try {
    const response = await fetch("/planning/extract-resume-upload", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        filename: file.name || "",
        content_type: file.type || "",
        upload_base64: await readScanWorkspaceFileAsBase64(file),
      }),
    });

    if (!response.ok) {
      let message = `Resume extraction failed (${response.status})`;
      try {
        const data = await response.json();
        message = String(data?.detail || data?.error || message);
      } catch {
        // keep status message
      }
      throw new Error(message);
    }

    const data = await response.json();
    const text = String(data?.text || "").trim();
    if (resumeTextInput && text) {
      resumeTextInput.value = text;
    }

    setScanWorkspaceResumeFileUi(
      file.name,
      text ? `Extracted ${text.length} characters into Resume text.` : "File selected.",
      text ? "success" : ""
    );
  } catch (err) {
    setScanWorkspaceResumeFileUi(
      file.name,
      err instanceof Error ? err.message : "Could not extract resume text.",
      "error"
    );
  } finally {
    updateScanWorkspaceIntakeActions();
  }
}

async function buildScanWorkspaceStartScanPayload(draft) {
  const root = getScanWorkspacePageRoot();
  const resumeName = String(draft.savedResumeName || root?.dataset?.resumeName || "").trim();
  const context = getScanWorkspaceContext();
  const suggestionArtifactPath = getScanWorkspaceArtifactKey(context);
  const jobDocId = String(root?.dataset?.jobDocId || "").trim();
  const scanId = String(root?.dataset?.rescanScanId || "").trim();

  return {
    scan_id: scanId,
    company: draft.company || "",
    role: draft.role || "",
    job_url: draft.jobUrl || "",
    job_doc_id: jobDocId || "",
    job_description_text: draft.jobDescriptionText || "",
    tailoring_json_path: suggestionArtifactPath || "",
    saved_resume_name: resumeName || "",
    resume_text: "",
    upload_filename: "",
    upload_content_type: "",
    upload_base64: "",
  };
}

async function beginScanWorkspaceProcessing() {
  const draft = readScanWorkspaceIntakeDraft();

  scanWorkspaceProcessingState.status = "running";
  scanWorkspaceProcessingState.currentStageKey = "prepare";
  scanWorkspaceProcessingState.intakeDraft = { ...draft };
  scanWorkspaceProcessingState.note =
    "Generating the scan report and saving it to Postgres...";

  setScanWorkspaceMode("processing");

  try {
    scanWorkspaceProcessingState.currentStageKey = "resume";
    updateScanWorkspaceProcessingView();

    const response = await fetch("/planning/start-scan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(await buildScanWorkspaceStartScanPayload(draft)),
    });

    if (!response.ok) {
      let message = `Start scan failed (${response.status})`;
      try {
        const data = await response.json();
        message = String(data?.detail || data?.error || message);
      } catch {
        // keep status message
      }
      throw new Error(message);
    }

    const data = await response.json();
    const scanId = String(data?.scan?.scan_id || "").trim();
    const root = getScanWorkspacePageRoot();
    const writeOk = data?.postgres_write?.ok === true;
    if (!writeOk) {
      const writeError = String(data?.postgres_write?.error || data?.postgres_write?.skipped || "").trim();
      throw new Error(writeError || "Saved scan could not be written to Postgres.");
    }
    if (root) {
      root.dataset.rescanScanId = "";
      if (scanId) root.dataset.savedScanId = scanId;
    }

    scanWorkspaceProcessingState.status = "complete";
    scanWorkspaceProcessingState.currentStageKey = "review_payload";
    scanWorkspaceProcessingState.note = scanId
      ? `Saved scan ${scanId.slice(0, 10)}. Match report ready.`
      : "Saved scan. Match report ready.";
    const pendingPayload = data?.scan_review_payload || data?.preload_payload || null;
    scanWorkspaceProcessingState.pendingReviewPayload =
      pendingPayload && typeof pendingPayload === "object"
        ? {
            ...pendingPayload,
            resume_name: firstNonEmptyScanWorkspaceText(
              pendingPayload.resume_name,
              pendingPayload.selected_resume,
              data?.scan?.resume_name,
              data?.scan?.resume_filename,
              draft.savedResumeName
            ),
            selected_resume: firstNonEmptyScanWorkspaceText(
              pendingPayload.selected_resume,
              pendingPayload.resume_name,
              data?.scan?.resume_name,
              data?.scan?.resume_filename,
              draft.savedResumeName
            ),
          }
        : null;
    updateScanWorkspaceProcessingView();
  } catch (err) {
    scanWorkspaceProcessingState.status = "error";
    scanWorkspaceProcessingState.pendingReviewPayload = null;
    scanWorkspaceProcessingState.note =
      err instanceof Error ? err.message : "Failed to save scan intake.";
    updateScanWorkspaceProcessingView();
  }
}

function buildSavedScanRescanDraft() {
  const payload = getScanWorkspacePreloadPayloadForSurface();
  const jobRecord = payload?.selected_jd_record || payload?.job_snapshot || payload?.job || {};
  return {
    company: firstNonEmptyScanWorkspaceText(
      payload?.job_company,
      jobRecord?.company,
      jobRecord?.job_company,
      payload?.selection?.company
    ),
    role: firstNonEmptyScanWorkspaceText(
      payload?.job_title,
      jobRecord?.title,
      jobRecord?.job_title,
      payload?.selection?.title
    ),
    jobUrl: firstNonEmptyScanWorkspaceText(jobRecord?.job_url, jobRecord?.url, jobRecord?.link),
    savedResumeName: firstNonEmptyScanWorkspaceText(
      payload?.resume_name,
      payload?.selected_resume,
      payload?.selection?.selected_resume,
      getScanWorkspacePageRoot()?.dataset?.resumeName
    ),
    jobDescriptionText: getScanWorkspaceLoadedJobDescriptionText(),
  };
}

async function openSavedScanRescanDraft() {
  const root = getScanWorkspacePageRoot();
  const scanId = String(root?.dataset?.savedScanId || "").trim();
  const rescanBtn = getScanWorkspaceInput("scanWorkspaceRescanBtn");
  if (!scanId) return;

  flashScanWorkspaceActionButton(rescanBtn);
  const draft = buildSavedScanRescanDraft();
  if (root) {
    root.dataset.rescanScanId = scanId;
  }
  setScanWorkspaceMode("new_scan");
  await loadScanWorkspaceSavedResumes();

  const companyInput = getScanWorkspaceInput("scanWorkspaceCompanyInput");
  const roleInput = getScanWorkspaceInput("scanWorkspaceRoleInput");
  const jobUrlInput = getScanWorkspaceInput("scanWorkspaceJobUrlInput");
  const jdInput = getScanWorkspaceInput("scanWorkspaceJobDescriptionInput");

  if (companyInput) companyInput.value = draft.company || "";
  if (roleInput) roleInput.value = draft.role || "";
  if (jobUrlInput) jobUrlInput.value = draft.jobUrl || "";
  if (jdInput) jdInput.value = draft.jobDescriptionText || "";
  setScanWorkspaceResumeSelection(draft.savedResumeName || "");
  updateScanWorkspaceIntakeActions();
}

function applyNewScanWorkspaceReviewPayload(payload) {
  if (!payload || typeof payload !== "object") {
    throw new Error("New Scan did not return a review payload.");
  }

  scanWorkspaceState.preloadPayload = payload;
  const root = getScanWorkspacePageRoot();
  if (root) {
    const company = firstNonEmptyScanWorkspaceText(
      payload.job_company,
      payload?.selected_jd_record?.company,
      payload?.selected_jd_record?.job_company,
      payload?.job?.company,
      payload?.job?.job_company,
      payload?.selection?.company
    );
    const title = firstNonEmptyScanWorkspaceText(
      payload.job_title,
      payload?.selected_jd_record?.title,
      payload?.selected_jd_record?.job_title,
      payload?.job?.title,
      payload?.job?.job_title,
      payload?.selection?.title
    );
    const resumeName = firstNonEmptyScanWorkspaceText(
      payload.resume_name,
      payload.selected_resume,
      payload?.selection?.selected_resume,
      payload?.draft?.selected_resume,
      payload?.scan_session?.selected_resume,
      root.dataset.resumeName
    );
    if (company) root.dataset.jobCompany = company;
    if (title) root.dataset.jobTitle = title;
    if (resumeName) root.dataset.resumeName = resumeName;
    syncScanWorkspacePreviewName();
  }

  if (typeof updateScanWorkspaceContextLine === "function") {
    updateScanWorkspaceContextLine(payload);
  }
  renderScanWorkspaceJdLlmReadback();
  renderScanWorkspaceTailoringLlmReadback();
  renderScanWorkspaceExactChangeLlmReadback();
  renderScanWorkspaceManualExactChangeAcceptanceReadback();
  renderScanWorkspaceGuardedResumeCopyArtifactReadback();
  renderScanWorkspaceGuardedResumeCopyArtifactVerificationReadback();
  renderScanWorkspaceVerifiedArtifactOperatorReviewPacketReadback();
  renderScanWorkspaceVerifiedArtifactOperatorDecisionReadback();
  renderScanWorkspaceApplicationReadinessPacketReadback();
  renderScanWorkspaceManualApplicationHandoffPacketReadback();
  renderScanWorkspaceHandoffAuditTrailReadback();
  renderScanWorkspaceSafetyBoundarySummaryReadback();
  renderScanWorkspaceWorkflowReadinessCheckpointReadback();
  renderScanWorkspaceAgenticWorkflowIntegrationReadback();
  renderScanWorkspaceProductionReadinessCheckpoint();

  const savedDraft = payload && payload.draft && typeof payload.draft === "object"
    ? payload.draft
    : {};
  scanWorkspaceState.selectedCandidateIds = typeof normalizeScanWorkspaceSelectedCandidateIds === "function"
    ? normalizeScanWorkspaceSelectedCandidateIds(payload, savedDraft.selected_patch_candidate_ids || [])
    : [];
  scanWorkspaceState.rewriteReviewDecisions = typeof normalizeTailoringWorkspaceReviewDecisionMap === "function"
    ? normalizeTailoringWorkspaceReviewDecisionMap(savedDraft.rewrite_review_decisions || {})
    : {};
  scanWorkspaceState.excludedScanIssueIds = typeof normalizeScanWorkspaceExcludedIssueIds === "function"
    ? normalizeScanWorkspaceExcludedIssueIds(savedDraft.excluded_scan_issue_ids || [])
    : [];
  const sourcePersonalDetails = getSourceScanWorkspacePersonalDetails();
  const savedPersonalDetails = normalizeScanWorkspacePersistencePersonalDetails(
    savedDraft.personal_details || {}
  );
  scanWorkspaceState.personalDetails = mergeScanWorkspacePersonalDetails(
    sourcePersonalDetails,
    savedPersonalDetails
  );
  scanWorkspaceState.suggestionDecisionOverrides = {};
  scanWorkspaceState.previewPayload = null;
  scanWorkspaceState.selectedTab = "personal_details";

  scanWorkspacePreviewState.documentPreviewPayload = payload.document_preview || null;
  scanWorkspacePreviewState.isDocumentPreviewLoading = false;
  scanWorkspacePreviewState.candidateSignature = getScanWorkspaceDraftPreviewSignature();

  setScanWorkspaceMode("review");
  if (typeof renderScanWorkspaceView === "function") {
    renderScanWorkspaceView();
  }
  renderScanWorkspaceJdLlmReadback();
  renderScanWorkspaceTailoringLlmReadback();
  renderScanWorkspaceExactChangeLlmReadback();
  renderScanWorkspaceManualExactChangeAcceptanceReadback();
  renderScanWorkspaceGuardedResumeCopyArtifactReadback();
  renderScanWorkspaceGuardedResumeCopyArtifactVerificationReadback();
  renderScanWorkspaceVerifiedArtifactOperatorReviewPacketReadback();
  renderScanWorkspaceVerifiedArtifactOperatorDecisionReadback();
  renderScanWorkspaceApplicationReadinessPacketReadback();
  renderScanWorkspaceManualApplicationHandoffPacketReadback();
  renderScanWorkspaceHandoffAuditTrailReadback();
  renderScanWorkspaceSafetyBoundarySummaryReadback();
  renderScanWorkspaceWorkflowReadinessCheckpointReadback();
  renderScanWorkspaceAgenticWorkflowIntegrationReadback();
  renderScanWorkspaceProductionReadinessCheckpoint();
  renderScanWorkspaceLiveDraftPreviewInto();

  window.setTimeout(() => {
    try {
      if (typeof syncScanWorkspaceAnnotationMarkers === "function") {
        syncScanWorkspaceAnnotationMarkers(scanWorkspaceState.preloadPayload);
      }
    } catch (markerErr) {
      console.error("Failed to sync scan annotation markers", markerErr);
    }
  }, 0);

  loadScanWorkspaceDraftState();
}

async function loadSavedScanWorkspaceReviewPayload() {
  const root = getScanWorkspacePageRoot();
  const scanId = String(root?.dataset?.savedScanId || "").trim();
  if (!scanId) return false;

  try {
    const response = await fetch(`/planning/saved-scan/${encodeURIComponent(scanId)}`);
    if (!response.ok) {
      let message = `Saved scan load failed (${response.status})`;
      try {
        const data = await response.json();
        message = String(data?.detail || data?.error || message);
      } catch {
        // keep status message
      }
      throw new Error(message);
    }
    const data = await response.json();
    const reviewPayload = data?.scan_review_payload || null;
    const scanRow = data?.scan || {};
    applyNewScanWorkspaceReviewPayload(
      reviewPayload && typeof reviewPayload === "object"
        ? {
            ...reviewPayload,
            resume_name: firstNonEmptyScanWorkspaceText(
              reviewPayload.resume_name,
              reviewPayload.selected_resume,
              scanRow.resume_name,
              scanRow.resume_filename
            ),
            selected_resume: firstNonEmptyScanWorkspaceText(
              reviewPayload.selected_resume,
              reviewPayload.resume_name,
              scanRow.resume_name,
              scanRow.resume_filename
            ),
          }
        : null
    );
    return true;
  } catch (err) {
    const summary = document.getElementById("scanWorkspaceInteractiveSummary");
    if (summary) {
      summary.innerHTML = `
        <div class="tailoring-empty-state">
          ${scanWorkspaceEscapeHtml(err instanceof Error ? err.message : "Could not load saved scan.")}
        </div>
      `;
    }
    return true;
  }
}

function bindScanWorkspaceProcessingShell() {
  const backBtn = getScanWorkspaceInput("scanWorkspaceProcessingBackBtn");
  if (backBtn && backBtn.dataset.bound !== "true") {
    backBtn.dataset.bound = "true";
    backBtn.addEventListener("click", () => {
      setScanWorkspaceMode("new_scan");
    });
  }

  const okBtn = getScanWorkspaceInput("scanWorkspaceProcessingOkBtn");
  if (okBtn && okBtn.dataset.bound !== "true") {
    okBtn.dataset.bound = "true";
    okBtn.addEventListener("click", () => {
      applyNewScanWorkspaceReviewPayload(scanWorkspaceProcessingState.pendingReviewPayload);
    });
  }
}

function normalizeScanWorkspaceAnnotationDecision(decision) {
  const safeDecision = String(decision || "").trim().toLowerCase();
  return safeDecision === "accepted" || safeDecision === "rejected" ? safeDecision : "pending";
}

function normalizeScanWorkspacePersistenceDecisionState(state) {
  const safeState = String(state || "").trim().toLowerCase();
  if (safeState === "accepted" || safeState === "edited_after_accept") return "accepted";
  if (safeState === "rejected") return "rejected";
  return "pending";
}

function collectScanWorkspaceMarkerCandidateIds(marker) {
  const directValues = [
    marker?.candidateId,
    marker?.patchCandidateId,
    marker?.candidate_id,
    marker?.patch_candidate_id,
  ];

  const listValues = [
    marker?.candidateIds,
    marker?.patchCandidateIds,
    marker?.candidate_ids,
    marker?.patch_candidate_ids,
  ];

  const ids = [];

  directValues.forEach((value) => {
    const safeValue = String(value || "").trim();
    if (safeValue) ids.push(safeValue);
  });

  listValues.forEach((list) => {
    if (!Array.isArray(list)) return;
    list.forEach((value) => {
      const safeValue = String(value || "").trim();
      if (safeValue) ids.push(safeValue);
    });
  });

  return Array.from(new Set(ids));
}

function normalizeScanWorkspaceAnnotationMarker(marker, index) {
  const tone = String(marker?.tone || "replace").trim().toLowerCase();
  const safeTone =
    tone === "add" || tone === "replace" || tone === "focus" ? tone : "replace";

  const id = String(marker?.id || `marker_${index + 1}`).trim();
  const topPercent = Number(marker?.topPercent);
  const leftPercent = Number(marker?.leftPercent);

  const previewRowIndex = Number(
    marker?.previewRowIndex ?? marker?.preview_row_index ?? index
  );

  return {
    id,
    tone: safeTone,
    decision: normalizeScanWorkspaceAnnotationDecision(marker?.decision),
    title: String(marker?.title || "AI suggested change").trim(),
    copy: String(marker?.copy || "Review this anchored suggestion.").trim(),
    topPercent: Number.isFinite(topPercent) ? Math.max(2, Math.min(98, topPercent)) : 50,
    leftPercent: Number.isFinite(leftPercent) ? Math.max(2, Math.min(98, leftPercent)) : 50,
    previewRowIndex: Number.isFinite(previewRowIndex)
      ? Math.max(0, Math.floor(previewRowIndex))
      : index,
    candidateIds: collectScanWorkspaceMarkerCandidateIds(marker),
    bulletKey: String(marker?.bulletKey || marker?.bullet_key || "").trim(),
    originalText: String(marker?.originalText || marker?.original_text || "").trim(),
    suggestedText: String(marker?.suggestedText || marker?.suggested_text || "").trim(),
    reasonText: String(marker?.reasonText || marker?.reason_text || "").trim(),
    sourceLabel: String(marker?.sourceLabel || marker?.source_label || "AI suggested").trim(),
    canFocusPreview: marker?.canFocusPreview !== false && marker?.can_focus_preview !== false,
    anchorStrategy: String(marker?.anchorStrategy || marker?.anchor_strategy || "").trim(),
    anchorText: String(marker?.anchorText || marker?.anchor_text || "").trim(),
    isExactReplacement:
      marker?.isExactReplacement === true ||
      marker?.scan_issue_exact_replacement === true ||
      marker?.renderMode === "diff" ||
      marker?.scan_issue_render_mode === "diff",
    renderMode:
      marker?.renderMode === "diff" ||
      marker?.scan_issue_render_mode === "diff" ||
      marker?.isExactReplacement === true
        ? "diff"
        : "guidance",
  };
}

function getScanWorkspaceAnnotationMarkerById(markerId) {
  return scanWorkspaceAnnotationState.markers.find((marker) => marker.id === markerId) || null;
}

function getScanWorkspaceAnnotationDecisionCounts() {
  return scanWorkspaceAnnotationState.markers.reduce(
    (acc, marker) => {
      if (!isScanWorkspaceReplacementMarker(marker)) {
        acc.total += 1;
        acc.guidance += 1;
        return acc;
      }

      const decision = normalizeScanWorkspaceAnnotationDecision(marker?.decision);
      acc.total += 1;
      acc.actionableTotal += 1;
      if (decision === "accepted") acc.accepted += 1;
      else if (decision === "rejected") acc.rejected += 1;
      else acc.pending += 1;
      return acc;
    },
    { total: 0, actionableTotal: 0, guidance: 0, accepted: 0, rejected: 0, pending: 0 }
  );
}

function getScanWorkspaceDecisionSnapshot() {
  return {
    markerDecisions: scanWorkspaceAnnotationState.markers.map((marker) => ({
      id: marker.id,
      decision: normalizeScanWorkspaceAnnotationDecision(marker?.decision),
    })),
    manualBulletEdits: getScanWorkspaceManualBulletEdits(),
  };
}

function getScanWorkspaceDecisionSnapshotSignature(snapshot) {
  const markerDecisions = Array.isArray(snapshot)
    ? snapshot
    : Array.isArray(snapshot?.markerDecisions)
      ? snapshot.markerDecisions
      : [];

  const normalizedDecisions = markerDecisions
      .map((row) => [
        String(row?.id || "").trim(),
        normalizeScanWorkspaceAnnotationDecision(row?.decision),
      ])
      .filter((row) => row[0])
      .sort((a, b) => String(a[0]).localeCompare(String(b[0])));

  const normalizedManualEdits = Object.entries(
    snapshot?.manualBulletEdits && typeof snapshot.manualBulletEdits === "object"
      ? snapshot.manualBulletEdits
      : {}
  )
    .map(([key, value]) => {
      const safeKey = String(key || "").trim();
      const safeValue = String(value || "").trim();
      return safeKey && safeValue ? [safeKey, safeValue] : null;
    })
    .filter(Boolean)
    .sort((a, b) => String(a[0]).localeCompare(String(b[0])));

  return JSON.stringify({
    markerDecisions: normalizedDecisions,
    manualBulletEdits: normalizedManualEdits,
  });
}

function pushScanWorkspaceDecisionHistory() {
  const snapshot = getScanWorkspaceDecisionSnapshot();
  const currentSignature = getScanWorkspaceDecisionSnapshotSignature(snapshot);
  const lastSnapshot =
    scanWorkspaceAnnotationState.undoStack[scanWorkspaceAnnotationState.undoStack.length - 1];
  const lastSignature = getScanWorkspaceDecisionSnapshotSignature(lastSnapshot);

  if (currentSignature === lastSignature) return;

  scanWorkspaceAnnotationState.undoStack.push(snapshot);
  scanWorkspaceAnnotationState.redoStack = [];
}

function restoreScanWorkspaceDecisionSnapshot(snapshot) {
  const markerDecisions = Array.isArray(snapshot)
    ? snapshot
    : Array.isArray(snapshot?.markerDecisions)
      ? snapshot.markerDecisions
      : [];

  const decisionById = new Map(
    markerDecisions
      .map((row) => [
        String(row?.id || "").trim(),
        normalizeScanWorkspaceAnnotationDecision(row?.decision),
      ])
      .filter((row) => row[0])
  );

  scanWorkspaceAnnotationState.markers = scanWorkspaceAnnotationState.markers.map((marker) => ({
    ...marker,
    decision: decisionById.get(marker.id) || "pending",
  }));

  scanWorkspacePersistenceState.manualBulletEdits = {
    ...(
      snapshot?.manualBulletEdits && typeof snapshot.manualBulletEdits === "object"
        ? snapshot.manualBulletEdits
        : {}
    ),
  };
}

function refreshScanWorkspaceDecisionOutputs({ forcePreview = false } = {}) {
  if (forcePreview) {
    scanWorkspacePreviewState.documentPreviewPayload = null;
  }
  scanWorkspacePreviewState.scorePreviewPayload = null;
  scanWorkspaceCompareState.beforePayload = null;
  scanWorkspaceCompareState.afterPayload = null;

  renderScanWorkspaceAnnotationShell();
  decorateScanWorkspacePreviewSuggestionTargets();
  refreshScanWorkspaceScorePreview();

  if (forcePreview) {
    ensureScanWorkspaceDocumentPreviewLoaded({ force: true });
  }

  if (normalizeScanWorkspaceMode(getScanWorkspacePageRoot()?.dataset.scanMode || "") === "compare") {
    ensureScanWorkspaceCompareLoaded({ force: true });
  }
}

function undoScanWorkspaceDecisionChange() {
  if (!scanWorkspaceAnnotationState.undoStack.length) return;

  const currentSnapshot = getScanWorkspaceDecisionSnapshot();
  const previousSnapshot = scanWorkspaceAnnotationState.undoStack.pop();
  scanWorkspaceAnnotationState.redoStack.push(currentSnapshot);
  restoreScanWorkspaceDecisionSnapshot(previousSnapshot);
  refreshScanWorkspaceDecisionOutputs({ forcePreview: false });
}

function redoScanWorkspaceDecisionChange() {
  if (!scanWorkspaceAnnotationState.redoStack.length) return;

  const currentSnapshot = getScanWorkspaceDecisionSnapshot();
  const nextSnapshot = scanWorkspaceAnnotationState.redoStack.pop();
  scanWorkspaceAnnotationState.undoStack.push(currentSnapshot);
  restoreScanWorkspaceDecisionSnapshot(nextSnapshot);
  refreshScanWorkspaceDecisionOutputs({ forcePreview: false });
}

function flashScanWorkspaceActionButton(button, className = "is-clicked") {
  if (!button) return;
  button.classList.remove(className);
  void button.offsetWidth;
  button.classList.add(className);
  window.setTimeout(() => {
    button.classList.remove(className);
  }, 650);
}

function getAcceptedCompareCandidateIds() {
  const ids = [];

  scanWorkspaceAnnotationState.markers.forEach((marker) => {
    if (normalizeScanWorkspaceAnnotationDecision(marker?.decision) !== "accepted") return;
    const markerIds = Array.isArray(marker?.candidateIds) ? marker.candidateIds : [];
    markerIds.forEach((value) => {
      const safeValue = String(value || "").trim();
      if (safeValue) ids.push(safeValue);
    });
  });

  return Array.from(new Set(ids));
}

function getSavedSelectedPatchCandidateIds() {
  const draft = scanWorkspacePersistenceState.loadResponse?.draft || {};
  return Array.from(
    new Set(
      (Array.isArray(draft.selected_patch_candidate_ids)
        ? draft.selected_patch_candidate_ids
        : []
      )
        .map((value) => String(value || "").trim())
        .filter(Boolean)
    )
  );
}

function getEffectiveAcceptedCompareCandidateIds() {
  const liveIds = getAcceptedCompareCandidateIds();
  if (scanWorkspaceAnnotationState.markers.length > 0) {
    return liveIds;
  }
  return getSavedSelectedPatchCandidateIds();
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

function buildScanWorkspaceRewriteReviewDecisionsPayload() {
  const decisionMap = {};

  scanWorkspaceAnnotationState.markers.forEach((marker) => {
    const decision = normalizeScanWorkspaceAnnotationDecision(marker?.decision);
    if (decision === "pending") return;

    const candidateIds = Array.isArray(marker?.candidateIds) ? marker.candidateIds : [];
    candidateIds.forEach((candidateId) => {
      const safeCandidateId = String(candidateId || "").trim();
      if (!safeCandidateId) return;

      decisionMap[safeCandidateId] = {
        state: decision,
        note:
          decision === "accepted"
            ? "Accepted in AI Optimize scan."
            : "Rejected in AI Optimize scan.",
      };
    });
  });

  return decisionMap;
}

function buildScanWorkspacePersistencePayload() {
  const context = getScanWorkspaceContext();
  const savedScanId = String(getScanWorkspacePageRoot()?.dataset?.savedScanId || "").trim();
  if (savedScanId) {
    return {
      saved_scan_id: savedScanId,
      selected_patch_candidate_ids: getEffectiveAcceptedCompareCandidateIds(),
      manual_bullet_edits: getScanWorkspaceManualBulletEdits(),
      rewrite_review_decisions: buildScanWorkspaceRewriteReviewDecisionsPayload(),
      excluded_scan_issue_ids: getCurrentScanWorkspaceExcludedIssueIds(),
      personal_details: getCurrentScanWorkspacePersonalDetails(),
      note: "Saved from restored AI Optimize scan.",
    };
  }

  if (!context || !getScanWorkspaceArtifactKey(context) || !context.resumeName) {
    return null;
  }

  return {
    tailoring_json_path: getScanWorkspaceArtifactKey(context),
    selected_resume: context.resumeName,
    selected_patch_candidate_ids: getEffectiveAcceptedCompareCandidateIds(),
    manual_bullet_edits: getScanWorkspaceManualBulletEdits(),
    rewrite_review_decisions: buildScanWorkspaceRewriteReviewDecisionsPayload(),
    excluded_scan_issue_ids: getCurrentScanWorkspaceExcludedIssueIds(),
    personal_details: getCurrentScanWorkspacePersonalDetails(),
    note: "Saved from AI Optimize scan.",
  };
}

function normalizeScanWorkspacePersistencePersonalDetails(value) {
  if (typeof normalizeScanWorkspacePersonalDetails === "function") {
    return normalizeScanWorkspacePersonalDetails(value);
  }

  const raw = value && typeof value === "object" ? value : {};
  const fields = ["name", "city", "state", "contact", "email", "linkedin", "github"];
  const normalized = {};
  fields.forEach((field) => {
    normalized[field] = String(raw[field] || "").trim();
  });
  normalized.state = normalized.state.toUpperCase().slice(0, 2);
  return normalized;
}

function getCurrentScanWorkspacePersonalDetails() {
  const rawDetails = typeof getScanWorkspacePersonalDetailsForSave === "function"
    ? getScanWorkspacePersonalDetailsForSave()
    : getSavedScanWorkspacePersonalDetails();

  const normalizedDetails = normalizeScanWorkspacePersistencePersonalDetails(rawDetails);
  normalizedDetails.linkedin = normalizeValidScanWorkspaceLinkedInProfileUrl(normalizedDetails.linkedin);
  normalizedDetails.github = normalizeValidScanWorkspaceGitHubProfileUrl(normalizedDetails.github);
  return normalizedDetails;
}





function getSavedScanWorkspacePersonalDetails() {
  const draft = scanWorkspacePersistenceState.loadResponse?.draft || {};
  return normalizeScanWorkspacePersistencePersonalDetails(draft.personal_details || {});
}

function getSourceScanWorkspacePersonalDetails() {
  const details = scanWorkspaceState.preloadPayload?.personal_details;
  const envelope = details && typeof details === "object" ? details : {};
  const current = envelope.current && typeof envelope.current === "object"
    ? envelope.current
    : {};
  const extracted = envelope.extracted && typeof envelope.extracted === "object"
    ? envelope.extracted
    : {};
  return mergeScanWorkspacePersonalDetails(extracted, current);
}

function mergeScanWorkspacePersonalDetails(baseDetails = {}, overrideDetails = {}) {
  const base = normalizeScanWorkspacePersistencePersonalDetails(baseDetails);
  const override = normalizeScanWorkspacePersistencePersonalDetails(overrideDetails);
  const merged = { ...base };
  Object.entries(override).forEach(([field, value]) => {
    if (String(value || "").trim()) merged[field] = value;
  });
  return normalizeScanWorkspacePersistencePersonalDetails(merged);
}

function getEffectiveScanWorkspacePersonalDetails() {
  const source = getSourceScanWorkspacePersonalDetails();
  const current = typeof getCurrentScanWorkspacePersonalDetails === "function"
    ? normalizeScanWorkspacePersistencePersonalDetails(getCurrentScanWorkspacePersonalDetails())
    : getSavedScanWorkspacePersonalDetails();

  const merged = mergeScanWorkspacePersonalDetails(source, current);

  /*
   * Link fields are editable. Empty/invalid current values must clear preview
   * labels instead of being repopulated from source metadata.
   */
  ["linkedin", "github"].forEach((field) => {
    if (Object.prototype.hasOwnProperty.call(current, field)) {
      merged[field] = String(current[field] || "").trim();
    }
  });

  return normalizeScanWorkspacePersistencePersonalDetails(merged);
}




function hasScanWorkspacePersonalDetailsValue(details) {
  return Object.values(normalizeScanWorkspacePersistencePersonalDetails(details)).some(Boolean);
}

function getCurrentScanWorkspaceExcludedIssueIds() {
  if (typeof getScanWorkspaceExcludedIssueIds === "function") {
    return getScanWorkspaceExcludedIssueIds();
  }

  return getSavedScanWorkspaceExcludedIssueIds();
}

function getSavedScanWorkspaceExcludedIssueIds() {
  const draft = scanWorkspacePersistenceState.loadResponse?.draft || {};
  return Array.isArray(draft.excluded_scan_issue_ids)
    ? draft.excluded_scan_issue_ids
        .map((value) => String(value || "").trim())
        .filter(Boolean)
    : [];
}

function getScanWorkspacePersistenceExcludedIssueIds() {
  if (typeof getScanWorkspaceExcludedIssueIds === "function") {
    return getScanWorkspaceExcludedIssueIds();
  }

  return getSavedScanWorkspaceExcludedIssueIds();
}

function buildScanWorkspacePersistenceSignature(
  selectedPatchCandidateIds,
  rewriteReviewDecisions,
  manualBulletEdits = {},
  excludedScanIssueIds = [],
  personalDetails = {}
) {
  const normalizedIds = Array.from(
    new Set(
      (Array.isArray(selectedPatchCandidateIds) ? selectedPatchCandidateIds : [])
        .map((value) => String(value || "").trim())
        .filter(Boolean)
    )
  ).sort();

  const normalizedDecisions = Object.entries(
    rewriteReviewDecisions && typeof rewriteReviewDecisions === "object"
      ? rewriteReviewDecisions
      : {}
  )
    .map(([candidateId, row]) => {
      const safeCandidateId = String(candidateId || "").trim();
      if (!safeCandidateId) return null;

      const rawState = row && typeof row === "object" ? row.state : row;
      const state = normalizeScanWorkspacePersistenceDecisionState(rawState);
      if (state === "pending") return null;

      return [safeCandidateId, state];
    })
    .filter(Boolean)
    .sort((a, b) => String(a[0]).localeCompare(String(b[0])));

  const normalizedManualEdits = Object.entries(
    manualBulletEdits && typeof manualBulletEdits === "object" ? manualBulletEdits : {}
  )
    .map(([key, value]) => {
      const safeKey = String(key || "").trim();
      const safeValue = String(value || "").trim();
      return safeKey && safeValue ? [safeKey, safeValue] : null;
    })
    .filter(Boolean)
    .sort((a, b) => String(a[0]).localeCompare(String(b[0])));

  const normalizedExcludedIssues = Array.from(
    new Set(
      (Array.isArray(excludedScanIssueIds) ? excludedScanIssueIds : [])
        .map((value) => String(value || "").trim())
        .filter(Boolean)
    )
  ).sort();
  const normalizedPersonalDetails = Object.entries(
    normalizeScanWorkspacePersistencePersonalDetails(personalDetails)
  ).sort((a, b) => String(a[0]).localeCompare(String(b[0])));

  return JSON.stringify({
    selected_patch_candidate_ids: normalizedIds,
    rewrite_review_decisions: normalizedDecisions,
    manual_bullet_edits: normalizedManualEdits,
    excluded_scan_issue_ids: normalizedExcludedIssues,
    personal_details: normalizedPersonalDetails,
  });
}

function getCurrentScanWorkspacePersistenceSignature() {
  const payload = buildScanWorkspacePersistencePayload();
  if (!payload) return "";

  return buildScanWorkspacePersistenceSignature(
    payload.selected_patch_candidate_ids,
    payload.rewrite_review_decisions,
    payload.manual_bullet_edits,
    payload.excluded_scan_issue_ids,
    payload.personal_details
  );
}

function getSavedScanWorkspacePersistenceSignature() {
  const draft = scanWorkspacePersistenceState.loadResponse?.draft || {};
  return buildScanWorkspacePersistenceSignature(
    draft.selected_patch_candidate_ids || [],
    draft.rewrite_review_decisions || {},
    draft.manual_bullet_edits || {},
    draft.excluded_scan_issue_ids || [],
    draft.personal_details || {}
  );
}

function applySavedDraftStateToScanMarkers() {
  const draft = scanWorkspacePersistenceState.loadResponse?.draft || {};
  const selectedSet = new Set(
    Array.isArray(draft.selected_patch_candidate_ids)
      ? draft.selected_patch_candidate_ids.map((value) => String(value || "").trim()).filter(Boolean)
      : []
  );

  const decisionMap =
    draft.rewrite_review_decisions && typeof draft.rewrite_review_decisions === "object"
      ? draft.rewrite_review_decisions
      : {};

  if (!scanWorkspaceAnnotationState.markers.length) return;

  scanWorkspaceAnnotationState.markers = scanWorkspaceAnnotationState.markers.map((marker) => {
    const candidateIds = Array.isArray(marker?.candidateIds) ? marker.candidateIds : [];
    if (!candidateIds.length) return marker;

    const hasSelected = candidateIds.some((candidateId) => selectedSet.has(String(candidateId || "").trim()));
    if (hasSelected) {
      return { ...marker, decision: "accepted" };
    }

    let nextDecision = "pending";
    for (const candidateId of candidateIds) {
      const safeCandidateId = String(candidateId || "").trim();
      if (!safeCandidateId) continue;

      const savedRow = decisionMap[safeCandidateId];
      const savedState = normalizeScanWorkspacePersistenceDecisionState(
        savedRow && typeof savedRow === "object" ? savedRow.state : savedRow
      );

      if (savedState === "rejected") {
        nextDecision = "rejected";
        break;
      }

      if (savedState === "accepted") {
        nextDecision = "accepted";
      }
    }

    return { ...marker, decision: nextDecision };
  });
}

function renderScanWorkspacePersistenceStatus() {
  const statusNode = getScanWorkspaceInput("scanWorkspacePersistStatus");
  const saveBtn = getScanWorkspaceInput("scanWorkspaceSaveBtn");
  const compareBtn = getScanWorkspaceInput("scanWorkspaceCompareBtn");
  const exportBtn = getScanWorkspaceInput("scanWorkspaceExportBtn");
  const rescanBtn = getScanWorkspaceInput("scanWorkspaceRescanBtn");

  const context = getScanWorkspaceContext();
  const hasContext = Boolean(getScanWorkspaceArtifactKey(context) && context?.resumeName);
  const savedScanId = String(getScanWorkspacePageRoot()?.dataset?.savedScanId || "").trim();
  const entrySource = String(scanWorkspaceState.preloadPayload?.scan_entry_source || "").trim();
  const isSavedNewScan = Boolean(savedScanId && entrySource === "scan_workspace_new_scan");
  const currentSignature = getCurrentScanWorkspacePersistenceSignature();
  const savedSignature = scanWorkspacePersistenceState.hydratedSignature || "";
  const canPersist = hasContext || isSavedNewScan;
  const isDirty = Boolean(canPersist && currentSignature !== savedSignature);
  const noChangesLabel = "No changes made";
  const syncDisabledHelp = (button, disabled, enabledLabel) => {
    if (!button) return;
    const wrapper = button.closest(".scan-workspace-disabled-action-wrap");
    button.setAttribute("aria-disabled", disabled ? "true" : "false");
    button.title = disabled ? noChangesLabel : enabledLabel;
    button.dataset.disabledReason = disabled ? noChangesLabel : "";
    if (wrapper) {
      wrapper.title = disabled ? noChangesLabel : "";
      wrapper.setAttribute("aria-label", disabled ? noChangesLabel : enabledLabel);
      if (disabled) {
        wrapper.setAttribute("tabindex", "0");
      } else {
        wrapper.removeAttribute("tabindex");
      }
    }
  };

  if (statusNode) {
    statusNode.classList.remove("is-warning", "is-success", "is-danger");

    if (!canPersist) {
      statusNode.textContent = "Workspace-draft persistence is unavailable for this scan.";
      statusNode.classList.add("is-danger");
    } else if (scanWorkspacePersistenceState.isLoading) {
      statusNode.textContent = "Loading saved scan decisions from the workspace draft...";
    } else if (scanWorkspacePersistenceState.isSaving) {
      statusNode.textContent = "Saving scan decisions into the workspace draft...";
    } else if (scanWorkspacePersistenceState.isExporting) {
      statusNode.textContent = "Exporting optimized draft...";
    } else if (scanWorkspacePersistenceState.lastError) {
      statusNode.textContent = scanWorkspacePersistenceState.lastError;
      statusNode.classList.add(
        scanWorkspacePersistenceState.lastError.startsWith("Export completed with warnings")
          ? "is-warning"
          : "is-danger"
      );
    } else if (isDirty) {
      statusNode.textContent = "You have unsaved scan decisions.";
      statusNode.classList.add("is-warning");
    } else if (scanWorkspacePersistenceState.loadResponse?.has_saved_draft) {
      const savedAt = String(scanWorkspacePersistenceState.loadResponse?.draft?.saved_at || "").trim();
      const savedAtLabel = formatScanWorkspaceSavedAt(savedAt);
      statusNode.textContent = savedAt
        ? `Scan decisions saved. Saved ${savedAtLabel}.`
        : "Scan decisions are saved into the workspace draft.";
      statusNode.classList.add("is-success");
    } else {
      statusNode.textContent = "Scan decisions are not saved yet.";
    }
  }

  if (compareBtn) {
    compareBtn.disabled =
      !isDirty ||
      scanWorkspacePersistenceState.isLoading ||
      scanWorkspacePersistenceState.isSaving ||
      scanWorkspacePersistenceState.isExporting;
    syncDisabledHelp(compareBtn, compareBtn.disabled, "Compare draft changes");
  }

  if (saveBtn) {
    saveBtn.disabled =
      !canPersist ||
      !isDirty ||
      scanWorkspacePersistenceState.isLoading ||
      scanWorkspacePersistenceState.isSaving ||
      scanWorkspacePersistenceState.isExporting;
    syncDisabledHelp(saveBtn, saveBtn.disabled, "Continue");
    saveBtn.textContent = scanWorkspacePersistenceState.isSaving
      ? "Saving..."
      : "Continue";
    saveBtn.classList.toggle("has-unsaved-changes", isDirty);
  }

  if (rescanBtn) {
    rescanBtn.hidden = !isSavedNewScan;
    rescanBtn.disabled =
      !isSavedNewScan ||
      scanWorkspacePersistenceState.isLoading ||
      scanWorkspacePersistenceState.isSaving ||
      scanWorkspacePersistenceState.isExporting;
    rescanBtn.setAttribute("aria-busy", "false");
  }

  if (exportBtn) {
    exportBtn.disabled =
      !hasContext ||
      scanWorkspacePersistenceState.isLoading ||
      scanWorkspacePersistenceState.isSaving ||
      scanWorkspacePersistenceState.isExporting;
  }
}

function formatScanWorkspaceSavedAt(value) {
  if (!value) return "";

  const savedAt = new Date(value);
  if (Number.isNaN(savedAt.getTime())) return value;

  return savedAt.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function updateScanWorkspaceDecisionSummaryUi() {
  const counts = getScanWorkspaceAnnotationDecisionCounts();
  const selectionStatus = getScanWorkspaceInput("scanWorkspaceSelectionStatus");
  const previewStatus = getScanWorkspaceInput("scanWorkspacePreviewStatus");
  const acceptAllBtn = getScanWorkspaceInput("scanWorkspaceAcceptAllAiBtn");
  const undoBtn = getScanWorkspaceInput("scanWorkspaceUndoBtn");
  const redoBtn = getScanWorkspaceInput("scanWorkspaceRedoBtn");
  const aiSuggestionStepLabel = getScanWorkspaceInput("scanWorkspaceAiSuggestionStepLabel");
  const editStep = getScanWorkspaceInput("scanWorkspaceEditStep");
  const scoreValue = getScanWorkspaceInput("scanWorkspaceScoreValue");

  const hasMarkers = scanWorkspaceAnnotationState.markers.length > 0;
  const savedAcceptedIds = getSavedSelectedPatchCandidateIds();

  if (selectionStatus) {
    if (counts.actionableTotal > 0 || counts.guidance > 0) {
      const parts = [];
      if (counts.actionableTotal > 0) {
        parts.push(`${counts.accepted} accepted`);
        parts.push(`${counts.rejected} rejected`);
        parts.push(`${counts.pending} pending`);
      }
      if (counts.guidance > 0) {
        parts.push(`${counts.guidance} guidance`);
      }
      selectionStatus.textContent = parts.join(" · ");
    } else if (savedAcceptedIds.length > 0) {
      selectionStatus.textContent =
        `${savedAcceptedIds.length} saved accepted linked suggestion(s) loaded. Waiting for scan markers.`;
    } else {
      selectionStatus.textContent = "No scan actions selected yet.";
    }
  }

  if (previewStatus) {
    if (counts.accepted > 0) {
      previewStatus.textContent = `${counts.accepted} accepted replacement`;
    } else if (!hasMarkers && savedAcceptedIds.length > 0) {
      previewStatus.textContent = `${savedAcceptedIds.length} saved accepted`;
    } else {
      previewStatus.textContent = "Resume preview";
    }
  }

  if (acceptAllBtn) {
    const canAcceptAll = counts.actionableTotal > 0 && counts.pending > 0;
    acceptAllBtn.classList.toggle("is-unavailable", !canAcceptAll);
    acceptAllBtn.classList.toggle("is-complete", counts.actionableTotal > 0 && counts.pending === 0);
    acceptAllBtn.setAttribute("aria-disabled", canAcceptAll ? "false" : "true");
    acceptAllBtn.title = canAcceptAll
      ? "Accept all pending scan suggestions"
      : counts.actionableTotal > 0
        ? "All scan suggestions already have decisions"
        : "No actionable scan suggestions are available";
  }

  if (undoBtn) {
    const canUndo = scanWorkspaceAnnotationState.undoStack.length > 0;
    undoBtn.classList.toggle("is-unavailable", !canUndo);
    undoBtn.classList.toggle("is-available", canUndo);
    undoBtn.setAttribute("aria-disabled", canUndo ? "false" : "true");
    undoBtn.title = canUndo ? "Undo last scan decision" : "No scan decision to undo";
  }

  if (redoBtn) {
    const canRedo = scanWorkspaceAnnotationState.redoStack.length > 0;
    redoBtn.classList.toggle("is-unavailable", !canRedo);
    redoBtn.classList.toggle("is-available", canRedo);
    redoBtn.setAttribute("aria-disabled", canRedo ? "false" : "true");
    redoBtn.title = canRedo ? "Redo last scan decision" : "No scan decision to redo";
  }

  if (aiSuggestionStepLabel) {
    const guidanceSuffix = counts.guidance > 0 ? ` + ${counts.guidance} guidance` : "";
    aiSuggestionStepLabel.textContent =
      `AI Suggestions (${counts.accepted}/${counts.actionableTotal}${guidanceSuffix})`;
  }

  if (editStep) {
    const hasGuidance = counts.guidance > 0;
    editStep.classList.toggle("is-disabled", !hasGuidance);
    editStep.setAttribute("aria-disabled", hasGuidance ? "false" : "true");
    editStep.title = hasGuidance
      ? "Open an orange guidance item to edit the surfaced bullet and preview the score."
      : "Edit unlocks when manual guidance rows are available.";
  }

  if (scoreValue) {
    const scoreSource = String(scoreValue.dataset.scanScoreSource || "").trim();
    if (scoreSource !== "backend" && counts.actionableTotal > 0) {
      scoreValue.textContent = String(Math.round((counts.accepted / counts.actionableTotal) * 100));
      scoreValue.setAttribute(
        "aria-label",
        `${counts.accepted} of ${counts.actionableTotal} replacement suggestions accepted`
      );
    }
  }

  renderScanWorkspacePersistenceStatus();
}

function getAcceptedCandidateSignature() {
  return getEffectiveAcceptedCompareCandidateIds().join("|");
}

function getScanWorkspaceUnresolvedGuidanceCount() {
  const manualEdits = getScanWorkspaceManualBulletEdits();
  return scanWorkspaceAnnotationState.markers.reduce((count, marker) => {
    if (isScanWorkspaceReplacementMarker(marker)) return count;
    const bulletKey = getScanWorkspaceMarkerBulletKey(marker);
    return bulletKey && manualEdits[bulletKey] ? count : count + 1;
  }, 0);
}

function hasScanWorkspaceCurrentDraftChanges() {
  const currentSignature = getCurrentScanWorkspacePersistenceSignature();
  const savedSignature = scanWorkspacePersistenceState.hydratedSignature || "";
  return Boolean(currentSignature && currentSignature !== savedSignature);
}

function getScanWorkspaceDraftPreviewSignature(selectedPatchCandidateIds = getEffectiveAcceptedCompareCandidateIds()) {
  const normalizedIds = Array.from(
    new Set(
      (Array.isArray(selectedPatchCandidateIds) ? selectedPatchCandidateIds : [])
        .map((value) => String(value || "").trim())
        .filter(Boolean)
    )
  ).sort();
  const normalizedManualEdits = Object.entries(getScanWorkspaceManualBulletEdits())
    .map(([key, value]) => [String(key || "").trim(), String(value || "").trim()])
    .filter((row) => row[0] && row[1])
    .sort((a, b) => String(a[0]).localeCompare(String(b[0])));

  return JSON.stringify({
    selected_patch_candidate_ids: normalizedIds,
    manual_bullet_edits: normalizedManualEdits,
  });
}

function buildScanWorkspaceDocumentPreviewRequest(
  selectedPatchCandidateIds = [],
  { manualBulletEdits = getScanWorkspaceManualBulletEdits() } = {}
) {
  const context = getScanWorkspaceContext();
  if (!context || !getScanWorkspaceArtifactKey(context) || !context.resumeName) {
    return null;
  }

  return {
    tailoring_json_path: getScanWorkspaceArtifactKey(context),
    selected_resume: context.resumeName,
    selected_patch_candidate_ids: Array.from(
      new Set(
        (Array.isArray(selectedPatchCandidateIds) ? selectedPatchCandidateIds : [])
          .map((value) => String(value || "").trim())
          .filter(Boolean)
      )
    ),
    manual_bullet_edits: manualBulletEdits && typeof manualBulletEdits === "object"
      ? manualBulletEdits
      : {},
    excluded_scan_issue_ids: getScanWorkspacePersistenceExcludedIssueIds(),
  };
}

function getCurrentScanWorkspaceExclusionAdjustedScore() {
  if (typeof getScanWorkspaceExclusionAdjustedScore !== "function") return null;
  if (typeof getScanWorkspacePayload !== "function") return null;

  const excludedIssueIds = getScanWorkspacePersistenceExcludedIssueIds();
  if (!excludedIssueIds.length) return null;

  return getScanWorkspaceExclusionAdjustedScore(getScanWorkspacePayload(), {
    excludedIssueIds,
  });
}

function coerceScanWorkspaceScore100(value) {
  const score = Number(value);
  if (!Number.isFinite(score)) return null;
  const displayScore = score >= 0 && score <= 1 ? score * 100 : score;
  return Math.max(0, Math.min(100, Math.round(displayScore)));
}

function getScanWorkspaceLoadedScanScorePoints() {
  const preload = getScanWorkspacePreloadPayloadForSurface() || {};
  const scanScore = preload?.scan_score && typeof preload.scan_score === "object"
    ? preload.scan_score
    : {};
  const preloadScorePreview = preload?.score_preview && typeof preload.score_preview === "object"
    ? preload.score_preview
    : {};

  const values = [
    scanScore.score,
    preloadScorePreview.projected_score_points,
    preloadScorePreview.projected_score,
    preloadScorePreview.original_score_points,
    preloadScorePreview.original_score,
  ];

  for (const value of values) {
    const points = coerceScanWorkspaceScore100(value);
    if (points !== null) return points;
  }

  return null;
}

function getScanWorkspaceDisplayedScorePoints() {
  const scoreValue = getScanWorkspaceInput("scanWorkspaceScoreValue");
  const displayed = coerceScanWorkspaceScore100(scoreValue?.textContent);
  return displayed ?? getScanWorkspaceLoadedScanScorePoints();
}

function updateScanWorkspaceScoreValue(score, { label = "Optimization score", source = "backend" } = {}) {
  const scoreValue = getScanWorkspaceInput("scanWorkspaceScoreValue");
  const displayScore = coerceScanWorkspaceScore100(score);
  if (!scoreValue || displayScore === null) return false;

  scoreValue.textContent = String(displayScore);
  scoreValue.dataset.scanScoreSource = source;
  scoreValue.setAttribute("aria-label", label);
  scoreValue.classList.remove("is-loading");
  scoreValue.removeAttribute("aria-busy");
  return true;
}

function setScanWorkspaceScoreLoading(isLoading) {
  scanWorkspacePreviewState.isScorePreviewLoading = Boolean(isLoading);

  const scoreValue = getScanWorkspaceInput("scanWorkspaceScoreValue");
  if (!scoreValue) return;

  scoreValue.classList.toggle("is-loading", scanWorkspacePreviewState.isScorePreviewLoading);
  if (scanWorkspacePreviewState.isScorePreviewLoading) {
    scoreValue.setAttribute("aria-busy", "true");
    scoreValue.setAttribute("aria-label", "Rescoring accepted scan decisions");
  } else {
    scoreValue.removeAttribute("aria-busy");
  }
}

async function requestScanWorkspaceDocumentPreview(selectedPatchCandidateIds = [], options = {}) {
  const requestBody = buildScanWorkspaceDocumentPreviewRequest(selectedPatchCandidateIds, options);
  const context = getScanWorkspaceContext();

  if (!requestBody) {
    const inlinePreview = getScanWorkspaceInlineDocumentPreview();
    if (inlinePreview) {
      return inlinePreview;
    }

    return {
      ok: false,
      error_message: "Scan preload is not available for this route.",
      pages: [],
    };
  }

  try {
    const response =
      typeof postJsonWithTimeout === "function"
        ? await postJsonWithTimeout(
            buildScanWorkspacePlanningEndpoint(
              "/planning/render-workspace-draft-preview",
              context?.planningOutputDir
            ),
            requestBody,
            20000
          )
        : await fetch(buildScanWorkspacePlanningEndpoint(
            "/planning/render-workspace-draft-preview",
            context?.planningOutputDir
          ), {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(requestBody),
          }).then(async (res) => {
            if (!res.ok) {
              let message = `Request failed (${res.status})`;
              try {
                const data = await res.json();
                message = String(data?.detail || data?.error_message || message);
              } catch {
                // ignore secondary parse error
              }
              throw new Error(message);
            }
            return res.json();
          });

    return response;
  } catch (err) {
    return {
      ok: false,
      error_message:
        err instanceof Error ? err.message : "Failed to render draft preview.",
      pages: [],
    };
  }
}

async function requestScanWorkspaceScorePreview(selectedPatchCandidateIds = []) {
  const requestBody = buildScanWorkspaceDocumentPreviewRequest(selectedPatchCandidateIds);
  const context = getScanWorkspaceContext();

  if (!requestBody) {
    return {
      ok: false,
      error_message: "Scan preload is not available for this route.",
    };
  }

  try {
    const response =
      typeof postJsonWithTimeout === "function"
        ? await postJsonWithTimeout(
            buildScanWorkspacePlanningEndpoint(
              "/planning/preview-workspace-draft",
              context?.planningOutputDir
            ),
            requestBody,
            20000
          )
        : await fetch(buildScanWorkspacePlanningEndpoint(
            "/planning/preview-workspace-draft",
            context?.planningOutputDir
          ), {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(requestBody),
          }).then(async (res) => {
            if (!res.ok) {
              let message = `Request failed (${res.status})`;
              try {
                const data = await res.json();
                message = String(data?.detail || data?.error_message || message);
              } catch {
                // ignore secondary parse error
              }
              throw new Error(message);
            }
            return res.json();
          });

    return response;
  } catch (err) {
    return {
      ok: false,
      error_message:
        err instanceof Error ? err.message : "Failed to preview scan score.",
    };
  }
}

async function refreshScanWorkspaceScorePreview() {
  const acceptedIds = getEffectiveAcceptedCompareCandidateIds();
  const requestSeq = ++scanWorkspacePreviewState.scorePreviewRequestSeq;
  setScanWorkspaceScoreLoading(true);

  let response = null;
  try {
    response = await requestScanWorkspaceScorePreview(acceptedIds);
  } finally {
    if (requestSeq === scanWorkspacePreviewState.scorePreviewRequestSeq) {
      setScanWorkspaceScoreLoading(false);
    }
  }

  if (requestSeq !== scanWorkspacePreviewState.scorePreviewRequestSeq) return;

  scanWorkspacePreviewState.scorePreviewPayload =
    response?.score_preview && typeof response.score_preview === "object"
      ? response.score_preview
      : response || null;
  applyScanWorkspaceDraftFragments(response?.draft_fragments || null);

  const scorePreview = scanWorkspacePreviewState.scorePreviewPayload || {};
  const hasAcceptedRewrites = acceptedIds.length > 0;
  const hasManualEdits = Object.keys(getScanWorkspaceManualBulletEdits()).length > 0;
  const exclusionAdjustedScore =
    !hasAcceptedRewrites && !hasManualEdits
      ? getCurrentScanWorkspaceExclusionAdjustedScore()
      : null;
  if (exclusionAdjustedScore) {
    updateScanWorkspaceScoreValue(exclusionAdjustedScore.score, {
      label: exclusionAdjustedScore.label,
      source: exclusionAdjustedScore.source || "backend",
    });
    return;
  }

  const projectedScore =
    scorePreview?.projected_score_points ??
    scorePreview?.projected_score ??
    response?.projected_score ??
    response?.projected_final_score ??
    null;
  const originalScore =
    scorePreview?.original_score_points ??
    scorePreview?.original_score ??
    response?.original_score ??
    response?.original_final_score ??
    null;
  const loadedScanScore = getScanWorkspaceLoadedScanScorePoints();
  const displayedScore = getScanWorkspaceDisplayedScorePoints();
  const nextScore = projectedScore ?? (
    hasAcceptedRewrites || hasManualEdits
      ? (displayedScore ?? loadedScanScore ?? originalScore)
      : (loadedScanScore ?? originalScore)
  );

  if (nextScore === null || nextScore === undefined) return;

  const deltaPoints = Number(scorePreview?.delta_points);
  const deltaLabel = Number.isFinite(deltaPoints) && deltaPoints !== 0
    ? ` (${deltaPoints > 0 ? "+" : ""}${Math.round(deltaPoints)} pts)`
    : "";

  updateScanWorkspaceScoreValue(nextScore, {
    label: hasAcceptedRewrites || hasManualEdits
      ? `Projected score after current scan decisions${deltaLabel}`
      : "Original optimization score",
    source: "backend",
  });
}

function fallbackRenderScanWorkspaceStructuredRow(row) {
  const rawText = String(row?.text || "").trim();
  const gapBefore = Number(row?.gap_before || 0);
  const indent = Math.max(0, Number(row?.left_indent_pt || 0));
  const isBullet = Boolean(row?.is_bullet);
  const isHeading = Boolean(row?.is_heading || row?.is_section_heading);
  const patched = Boolean(row?.patched);
  const patchSource = String(row?.patch_source || "").trim();
  const decision = normalizeScanWorkspaceAnnotationDecision(
    row?.decision || row?.scan_decision || row?.review_state || row?.state
  );
  const isManualEdit = patchSource === "manual_edit";
  const isRejected = decision === "rejected" || patchSource === "rejected";
  const isDirectReplacement =
    patchSource === "selected_patch" ||
    patchSource === "direct_replacement" ||
    String(row?.row_action_type || row?.action_type || "").trim() === "direct_replacement";

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
    isManualEdit ? "tailoring-workspace-doc-line--manual" : "",
    isRejected ? "tailoring-workspace-doc-line--rejected" : "",
    isDirectReplacement ? "tailoring-workspace-doc-line--selected" : "",
  ].filter(Boolean).join(" ");

  if (isBullet) {
    const bulletText = rawText.replace(/^\s*(?:[-*•]|\d+[.)])\s*/, "");
    return `
      <div class="${extraClasses}" style="margin-top:${gapBefore}px;">
        <div class="tailoring-workspace-doc-bullet-row" style="padding-left:${indent}px;">
          <div class="tailoring-workspace-doc-bullet-marker">•</div>
          <div class="tailoring-workspace-doc-line-copy tailoring-workspace-doc-bullet-copy">
            <span class="scan-workspace-preview-line-text">${scanWorkspaceEscapeHtml(bulletText)}</span>
          </div>
        </div>
      </div>
    `;
  }

  return `
    <div class="${extraClasses}" style="margin-top:${gapBefore}px;">
          <div class="tailoring-workspace-doc-line-copy" style="padding-left:${indent}px;">
            <span class="scan-workspace-preview-line-text">${renderScanWorkspaceLinkedText(rawText, row?.link_items || [])}</span>
          </div>
      ${isHeading ? `<div class="tailoring-workspace-doc-section-rule"></div>` : ""}
    </div>
  `;
}

function buildScanWorkspacePersonalDetailsContactLine(details) {
  const safeDetails = normalizeScanWorkspacePersistencePersonalDetails(details);
  const location = [safeDetails.city, safeDetails.state].filter(Boolean).join(", ");
  const validLinkedIn = normalizeValidScanWorkspaceLinkedInProfileUrl(safeDetails.linkedin);
  const validGitHub = normalizeValidScanWorkspaceGitHubProfileUrl(safeDetails.github);

  return [
    location,
    safeDetails.contact,
    safeDetails.email,
    validLinkedIn ? "LinkedIn" : "",
    validGitHub ? "GitHub" : "",
  ].filter(Boolean).join(" | ");
}



function isValidScanWorkspaceLinkedInProfileUrl(value) {
  const raw = String(value || "").trim();
  if (!raw) return false;

  let url;
  try {
    url = new URL(raw);
  } catch {
    return false;
  }

  const protocol = url.protocol.toLowerCase();
  const host = url.hostname.toLowerCase().replace(/^www\./, "");
  const pathname = url.pathname.replace(/\/+$/g, "");

  if (protocol !== "https:" && protocol !== "http:") return false;
  if (host !== "linkedin.com") return false;

  /*
   * Require a real personal profile path.
   * Examples allowed:
   *   https://www.linkedin.com/in/sriram-hariharan-neelakantan/
   *   https://linkedin.com/in/sriram-hariharan-neelakantan
   *
   * Examples rejected:
   *   https://www.linkedin.com/
   *   https://www.linkedin.com/in/
   *   linkedin
   */
  return /^\/in\/[A-Za-z0-9][A-Za-z0-9._%-]+$/.test(pathname);
}

function normalizeValidScanWorkspaceLinkedInProfileUrl(value) {
  const raw = String(value || "").trim();
  if (!isValidScanWorkspaceLinkedInProfileUrl(raw)) return "";

  try {
    const url = new URL(raw);
    url.protocol = "https:";
    url.hash = "";
    return url.toString();
  } catch {
    return "";
  }
}

function getScanWorkspaceLinkedInValidationMessage(value) {
  const raw = String(value || "").trim();
  if (!raw) return "";
  return isValidScanWorkspaceLinkedInProfileUrl(raw) ? "" : "Invalid LinkedIn link";
}


function isValidScanWorkspaceGitHubProfileUrl(value) {
  const raw = String(value || "").trim();
  if (!raw) return false;

  let url;
  try {
    url = new URL(raw);
  } catch {
    return false;
  }

  const protocol = url.protocol.toLowerCase();
  const host = url.hostname.toLowerCase().replace(/^www\./, "");
  const pathname = url.pathname.replace(/\/+$/g, "");

  if (protocol !== "https:" && protocol !== "http:") return false;
  if (host !== "github.com") return false;

  return /^\/[A-Za-z0-9][A-Za-z0-9-]{0,38}$/.test(pathname);
}

function normalizeValidScanWorkspaceGitHubProfileUrl(value) {
  const raw = String(value || "").trim();
  if (!isValidScanWorkspaceGitHubProfileUrl(raw)) return "";

  try {
    const url = new URL(raw);
    url.protocol = "https:";
    url.hash = "";
    return url.toString();
  } catch {
    return "";
  }
}

function buildScanWorkspacePersonalDetailsLinkItems(details) {
  const safeDetails = details && typeof details === "object" ? details : {};
  const validLinkedIn = normalizeValidScanWorkspaceLinkedInProfileUrl(safeDetails.linkedin);
  const validGitHub = normalizeValidScanWorkspaceGitHubProfileUrl(safeDetails.github);

  return [
    validLinkedIn ? { label: "LinkedIn", uri: validLinkedIn } : null,
    validGitHub ? { label: "GitHub", uri: validGitHub } : null,
  ].filter(Boolean);
}




function renderScanWorkspaceLinkedText(text, linkItems = []) {
  if (typeof renderTailoringWorkspaceLinkedText === "function") {
    return renderTailoringWorkspaceLinkedText(text, linkItems);
  }

  const rawText = String(text || "");
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

  if (!links.length) return scanWorkspaceEscapeHtml(rawText);

  let html = "";
  let lastEnd = 0;
  links.forEach((item) => {
    if (item.pos < lastEnd) return;
    html += scanWorkspaceEscapeHtml(rawText.slice(lastEnd, item.pos));
    html += `
      <a
        class="tailoring-workspace-doc-link"
        href="${scanWorkspaceEscapeHtml(item.uri)}"
        title="${scanWorkspaceEscapeHtml(item.uri)}"
        target="_blank"
        rel="noopener noreferrer"
      >${scanWorkspaceEscapeHtml(item.label)}</a>
    `;
    lastEnd = item.pos + item.label.length;
  });
  html += scanWorkspaceEscapeHtml(rawText.slice(lastEnd));
  return html;
}

function applySavedScanWorkspacePersonalDetailsToRows(rows) {
  const savedDetails = getEffectiveScanWorkspacePersonalDetails();
  if (!Object.values(savedDetails).some(Boolean)) {
    return rows;
  }

  const nextRows = Array.isArray(rows) ? rows.map((row) => ({ ...row })) : [];
  const name = savedDetails.name;
  const contactLine = buildScanWorkspacePersonalDetailsContactLine(savedDetails);
  const contactLinkItems = buildScanWorkspacePersonalDetailsLinkItems(savedDetails);
  let patchedName = false;
  let patchedContact = false;

  const isHeaderContactCandidate = (row, index) => {
    const role = String(row?.presentation_role || "").trim();
    const text = String(row?.display_text || row?.text || "");
    if (role === "header_contact") return true;
    if (patchedContact || index > 8) return false;
    return (
      /@/.test(text) ||
      /\+?\s*\(?\d{3}\)?[\s.-]?\d{3}/.test(text) ||
      /linkedin|github/i.test(text)
    );
  };

  return nextRows.map((row, index) => {
    const role = String(row?.presentation_role || "").trim();

    if (!patchedName && name && role === "header_name") {
      patchedName = true;
      return {
        ...row,
        text: name,
        display_text: name,
        patched: true,
        patch_source: "personal_details",
      };
    }

    if (!patchedContact && contactLine && isHeaderContactCandidate(row, index)) {
      patchedContact = true;
      return {
        ...row,
        text: contactLine,
        display_text: contactLine,
        patched: true,
        patch_source: "personal_details",
        link_items: contactLinkItems,
      };
    }

    return row;
  });
}


function normalizeScanWorkspacePreviewPages(preview) {
  const pages = Array.isArray(preview?.pages) ? preview.pages : [];
  const buildPresentationRowsFn =
    typeof buildTailoringWorkspacePreviewPresentationRows === "function"
      ? buildTailoringWorkspacePreviewPresentationRows
      : (rows) => (Array.isArray(rows) ? rows : []);

  const getSectionKeyFn =
    typeof getTailoringWorkspaceSectionKeyFromRow === "function"
      ? getTailoringWorkspaceSectionKeyFromRow
      : () => "";

  let carrySection = "";

  return pages.map((page, pageIndex) => {
    const presentationRows = buildPresentationRowsFn(page.rows, {
      initialSection: carrySection,
      allowDocumentHeaderRoles: pageIndex === 0,
    });
    const rowsWithPersonalDetails =
      pageIndex === 0
        ? applySavedScanWorkspacePersonalDetailsToRows(presentationRows)
        : presentationRows;

    rowsWithPersonalDetails.forEach((row) => {
      const sectionKey = getSectionKeyFn(row);
      if (sectionKey) carrySection = sectionKey;
    });

    return {
      ...page,
      presentation_rows: rowsWithPersonalDetails,
    };
  });
}

function normalizeScanWorkspacePreviewText(value) {
  return String(value || "")
    .replace(/^•\s*/, "")
    .replace(/\s+/g, " ")
    .trim()
    .toLowerCase();
}

function renderScanWorkspaceDocumentMirrorFromPayload(
  preview,
  {
    isLoading = false,
    emptyMessage = "Draft preview is not available.",
    noteText = "",
    compareSide = "",
    removedTexts = [],
    removedPositions = [],
  } = {}
) {
  if (isLoading && !preview) {
    return `
      <div class="tailoring-empty-state">
        Loading reconstructed draft preview...
      </div>
    `;
  }

  const pages = normalizeScanWorkspacePreviewPages(preview);
  if (!pages.length) {
    const errorMessage = String(preview?.error_message || "").trim();
    return `
      <div class="tailoring-empty-state">
        ${scanWorkspaceEscapeHtml(errorMessage || emptyMessage)}
      </div>
    `;
  }

  const escapeFn =
    typeof escapeHtml === "function" ? escapeHtml : scanWorkspaceEscapeHtml;

  const renderRowFn =
    typeof renderTailoringWorkspaceStructuredRow === "function"
      ? renderTailoringWorkspaceStructuredRow
      : fallbackRenderScanWorkspaceStructuredRow;

  const removedTextKeys = new Set(
    (Array.isArray(removedTexts) ? removedTexts : [])
      .map((value) => normalizeScanWorkspacePreviewText(value))
      .filter(Boolean)
  );
  const removedPositionKeys = new Set(
    (Array.isArray(removedPositions) ? removedPositions : [])
      .map((value) => String(value || "").trim())
      .filter(Boolean)
  );

  const getCompareRenderRow = (row) => {
    const safeSide = String(compareSide || "").trim();
    if (!safeSide || !row || typeof row !== "object") return row;

    const rawIndent = Number(row.left_indent_pt || 0);
    if (!Number.isFinite(rawIndent) || rawIndent <= 0) return row;

    return {
      ...row,
      left_indent_pt: Math.round(Math.max(0, rawIndent * 0.06)),
    };
  };

  const addCompareClassToRowHtml = (html, row, pageIndex, rowIndex) => {
    const safeSide = String(compareSide || "").trim();
    if (!safeSide || !html) return html;

    const rowText = normalizeScanWorkspacePreviewText(row?.text || row?.current_text || row?.original_text || "");
    const rowPositionKey = `${pageIndex}:${rowIndex}`;
    const isRemoved =
      safeSide === "before" &&
      (
        removedPositionKeys.has(rowPositionKey) ||
        (
          rowText &&
          Array.from(removedTextKeys).some((text) => text && (rowText === text || rowText.includes(text) || text.includes(rowText)))
        )
      );
    const isAdded = safeSide === "after" && Boolean(row?.patched);
    const diffClass = isRemoved
      ? "tailoring-workspace-doc-line--compare-removed"
      : isAdded
        ? "tailoring-workspace-doc-line--compare-added"
        : "";

    if (!diffClass) return html;
    return html.replace(
      "tailoring-workspace-doc-line",
      `tailoring-workspace-doc-line ${diffClass}`
    );
  };

  const changedCount = pages.reduce(
    (count, page) =>
      count +
      (Array.isArray(page.presentation_rows)
        ? page.presentation_rows.filter((row) => row && row.patched).length
        : 0),
    0
  );

  return `
    <div class="tailoring-workspace-doc-mirror">
      ${noteText ? `
        <div class="tailoring-workspace-doc-mirror-note" style="white-space:normal; overflow-wrap:anywhere; line-height:1.35;">
          ${scanWorkspaceEscapeHtml(noteText)}
          ${changedCount ? ` ${changedCount} changed line${changedCount === 1 ? "" : "s"} currently reflected.` : ""}
        </div>
      ` : ""}

      ${pages
        .map(
          (page, pageIndex) => `
        <section class="tailoring-workspace-doc-page">
          ${pages.length > 1 ? `
            <div class="tailoring-workspace-doc-page-header">
              <span class="tailoring-workspace-doc-page-number">
                Page ${escapeFn(String(page.page_number || ""))}
              </span>
            </div>
          ` : ""}

          <div class="tailoring-workspace-doc-page-body">
            ${(Array.isArray(page.presentation_rows) ? page.presentation_rows : [])
              .map((row, rowIndex) => {
                const renderRow = getCompareRenderRow(row);
                return addCompareClassToRowHtml(
                  renderRowFn(renderRow),
                  renderRow,
                  page.page_index ?? pageIndex,
                  rowIndex
                );
              })
              .join("")}
          </div>
        </section>
      `
        )
        .join("")}
    </div>
  `;
}

function getScanWorkspacePdfResumeName() {
  const payload = getScanWorkspacePreloadPayloadForSurface();
  const resumeName = firstNonEmptyScanWorkspaceText(
    payload?.resume_name,
    payload?.selected_resume,
    payload?.selection?.selected_resume,
    getScanWorkspacePageRoot()?.dataset?.resumeName
  );
  return resumeName.toLowerCase().endsWith(".pdf") ? resumeName : "";
}

function getScanWorkspacePreviewDisplayResumeName() {
  const payload = getScanWorkspacePreloadPayloadForSurface();
  const preview = scanWorkspacePreviewState.documentPreviewPayload || payload?.document_preview || {};
  return firstNonEmptyScanWorkspaceText(
    payload?.resume_name,
    payload?.selected_resume,
    payload?.selection?.selected_resume,
    payload?.draft?.selected_resume,
    payload?.scan_session?.selected_resume,
    preview?.resume_name,
    preview?.selected_resume,
    getScanWorkspaceSelectedResumeName(),
    scanWorkspaceIntakeState.savedResumeName,
    getScanWorkspacePageRoot()?.dataset?.resumeName
  );
}

function syncScanWorkspacePreviewName() {
  const previewName = getScanWorkspaceInput("scanWorkspacePreviewName");
  const toolbarName = getScanWorkspaceInput("scanWorkspaceToolbarResumeName");
  if (!previewName && !toolbarName) return;

  const resumeName = getScanWorkspacePreviewDisplayResumeName();
  const displayName =
    typeof humanizeResumeDisplayName === "function"
      ? humanizeResumeDisplayName(resumeName || "")
      : String(resumeName || "").replace(/\.[^.]+$/, "").replace(/[_-]+/g, " ");
  const label = displayName || "Generated resume preview";
  if (previewName) previewName.textContent = label;
  if (toolbarName) toolbarName.textContent = label;
}

function renderScanWorkspacePdfPreviewShell() {
  return `
    <div class="scan-workspace-pdf-toolbar" aria-label="Resume PDF preview controls">
      <button type="button" class="ghost-btn btn-sm" id="scanWorkspaceZoomOutBtn">-</button>
      <button type="button" class="ghost-btn btn-sm" id="scanWorkspaceZoomResetBtn">100%</button>
      <button type="button" class="ghost-btn btn-sm" id="scanWorkspaceZoomInBtn">+</button>
    </div>
    <div class="scan-workspace-pdf-preview-shell">
      <div class="tailoring-workspace-pdf-scroller" id="scanWorkspacePdfScroller">
        <div class="tailoring-empty-state" id="scanWorkspacePreviewEmpty">
          Loading PDF preview...
        </div>
        <div class="tailoring-workspace-pdf-pages hidden" id="scanWorkspacePdfPages"></div>
      </div>
    </div>
  `;
}

function renderScanWorkspaceLiveDraftPreviewInto() {
  const root = getScanWorkspaceInput("scanWorkspaceLiveDraftPreview");
  if (!root) return;

  syncScanWorkspacePreviewName();

  if (scanWorkspacePreviewState.activeSurface === "job_description") {
    renderScanWorkspaceJobDescriptionSurfaceInto();
    return;
  }

  const acceptedIds = getEffectiveAcceptedCompareCandidateIds();

  const noteText = acceptedIds.length
    ? `Read-only reconstructed draft from the export model using ${acceptedIds.length} accepted linked suggestion(s).`
    : "Read-only reconstructed draft from the export model. Accepted scan changes will appear here first.";

  root.innerHTML = renderScanWorkspaceDocumentMirrorFromPayload(
    scanWorkspacePreviewState.documentPreviewPayload,
    {
      isLoading: scanWorkspacePreviewState.isDocumentPreviewLoading,
      emptyMessage: "Live draft preview is not available for this scan.",
      noteText,
    }
  );

  decorateScanWorkspacePreviewSuggestionTargets();
}

async function fetchScanWorkspaceDocumentPreview() {
  const previewMeta = getScanWorkspaceInput("scanWorkspacePreviewMeta");
  const acceptedIds = getEffectiveAcceptedCompareCandidateIds();
  const currentSignature = getScanWorkspaceDraftPreviewSignature(acceptedIds);
  const requestSeq = ++scanWorkspacePreviewState.documentPreviewRequestSeq;

  scanWorkspacePreviewState.isDocumentPreviewLoading = true;
  scanWorkspacePreviewState.candidateSignature = currentSignature;

  if (previewMeta) {
    previewMeta.textContent = "Loading live draft preview...";
  }

  renderScanWorkspaceLiveDraftPreviewInto();

  const response = await requestScanWorkspaceDocumentPreview(acceptedIds);
  if (requestSeq !== scanWorkspacePreviewState.documentPreviewRequestSeq) return;

  scanWorkspacePreviewState.documentPreviewPayload = response;
  scanWorkspacePreviewState.isDocumentPreviewLoading = false;

  if (previewMeta) {
    previewMeta.textContent = response?.pages?.length
      ? "Live draft preview"
      : "Live draft preview unavailable";
  }

  renderScanWorkspaceLiveDraftPreviewInto();
}

function ensureScanWorkspaceDocumentPreviewLoaded({ force = false } = {}) {
  if (scanWorkspacePreviewState.activeSurface === "job_description") {
    renderScanWorkspaceJobDescriptionSurfaceInto();
    return;
  }

  const acceptedSignature = getScanWorkspaceDraftPreviewSignature();
  const hasRenderableContext = getScanWorkspaceHasTailoringPreviewContext();

  if (!hasRenderableContext && scanWorkspacePreviewState.documentPreviewPayload) {
    scanWorkspacePreviewState.candidateSignature = acceptedSignature;
    renderScanWorkspaceLiveDraftPreviewInto();
    return;
  }

  if (!hasRenderableContext) {
    const inlinePreview = getScanWorkspaceInlineDocumentPreview();
    if (inlinePreview) {
      scanWorkspacePreviewState.documentPreviewPayload = inlinePreview;
      scanWorkspacePreviewState.isDocumentPreviewLoading = false;
      scanWorkspacePreviewState.candidateSignature = acceptedSignature;
      renderScanWorkspaceLiveDraftPreviewInto();
      return;
    }
  }

  if (
    !force &&
    scanWorkspacePreviewState.documentPreviewPayload &&
    scanWorkspacePreviewState.candidateSignature === acceptedSignature
  ) {
    renderScanWorkspaceLiveDraftPreviewInto();
    return;
  }

  fetchScanWorkspaceDocumentPreview();
}

async function loadScanWorkspaceDraftState() {
  const payload = buildScanWorkspacePersistencePayload();
  if (!payload) {
    renderScanWorkspacePersistenceStatus();
    return;
  }

  if (payload.saved_scan_id) {
    const draft = scanWorkspaceState.preloadPayload?.draft || {};
    scanWorkspacePersistenceState.loadResponse = {
      ok: true,
      has_saved_draft: Boolean(draft && Object.keys(draft).length),
      draft,
      score_preview: scanWorkspaceState.preloadPayload?.score_preview || {},
    };
    scanWorkspacePersistenceState.manualBulletEdits = {
      ...(draft?.manual_bullet_edits && typeof draft.manual_bullet_edits === "object"
        ? draft.manual_bullet_edits
        : {}),
    };
    scanWorkspacePersistenceState.hydratedSignature = getSavedScanWorkspacePersistenceSignature();
    renderScanWorkspacePersistenceStatus();
    return;
  }

  scanWorkspacePersistenceState.isLoading = true;
  scanWorkspacePersistenceState.lastError = "";
  renderScanWorkspacePersistenceStatus();

  try {
    const context = getScanWorkspaceContext();
    const loadUrl = buildScanWorkspacePlanningEndpoint(
      "/planning/load-workspace-draft",
      context?.planningOutputDir
    );
    const response =
      typeof postJsonWithTimeout === "function"
        ? await postJsonWithTimeout(
            loadUrl,
            {
              tailoring_json_path: payload.tailoring_json_key || payload.tailoring_json_path,
              selected_resume: payload.selected_resume,
            },
            15000
          )
        : await fetch(loadUrl, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              tailoring_json_path: payload.tailoring_json_key || payload.tailoring_json_path,
              selected_resume: payload.selected_resume,
            }),
          }).then(async (res) => {
            if (!res.ok) {
              let message = `Request failed (${res.status})`;
              try {
                const data = await res.json();
                message = String(data?.detail || data?.error_message || message);
              } catch {
                // ignore secondary parse error
              }
              throw new Error(message);
            }
            return res.json();
          });

    scanWorkspacePersistenceState.loadResponse = response;
    if (payload.saved_scan_id && scanWorkspaceState.preloadPayload && response?.draft) {
      scanWorkspaceState.preloadPayload = {
        ...scanWorkspaceState.preloadPayload,
        draft: response.draft,
        personal_details: {
          ...(scanWorkspaceState.preloadPayload.personal_details || {}),
          saved: response.draft.personal_details || {},
          current: response.draft.personal_details || scanWorkspaceState.preloadPayload?.personal_details?.current || {},
        },
      };
    }
    scanWorkspacePersistenceState.manualBulletEdits = {
      ...(
        response?.draft?.manual_bullet_edits &&
        typeof response.draft.manual_bullet_edits === "object"
          ? response.draft.manual_bullet_edits
          : {}
      ),
    };
    scanWorkspacePersistenceState.hydratedSignature = getSavedScanWorkspacePersistenceSignature();

    if (typeof setScanWorkspaceExcludedIssueIds === "function") {
      setScanWorkspaceExcludedIssueIds(response?.draft?.excluded_scan_issue_ids || []);
    }
    const savedPersonalDetails = response?.draft?.personal_details || {};
    if (
      typeof setScanWorkspacePersonalDetails === "function" &&
      hasScanWorkspacePersonalDetailsValue(savedPersonalDetails)
    ) {
      setScanWorkspacePersonalDetails(savedPersonalDetails);
    }
    applySavedDraftStateToScanMarkers();

    scanWorkspacePreviewState.documentPreviewPayload = null;
    scanWorkspacePreviewState.scorePreviewPayload = response?.score_preview || null;
    scanWorkspaceCompareState.beforePayload = null;
    scanWorkspaceCompareState.afterPayload = null;

    renderScanWorkspaceAnnotationShell();
    renderScanWorkspaceCompareShell();

    if (normalizeScanWorkspaceMode(getScanWorkspacePageRoot()?.dataset.scanMode || "") === "review") {
      ensureScanWorkspaceDocumentPreviewLoaded({ force: true });
    }

    if (normalizeScanWorkspaceMode(getScanWorkspacePageRoot()?.dataset.scanMode || "") === "compare") {
      ensureScanWorkspaceCompareLoaded({ force: true });
    }
  } catch (err) {
    scanWorkspacePersistenceState.lastError =
      err instanceof Error ? err.message : "Failed to load saved scan decisions.";
  } finally {
    scanWorkspacePersistenceState.isLoading = false;
    renderScanWorkspacePersistenceStatus();
  }
}

async function saveScanWorkspaceDraftState({ navigateAfterSave = false } = {}) {
  const payload = buildScanWorkspacePersistencePayload();
  if (!payload) {
    scanWorkspacePersistenceState.lastError =
      "Workspace-draft persistence is unavailable for this scan.";
    renderScanWorkspacePersistenceStatus();
    return false;
  }

  scanWorkspacePersistenceState.isSaving = true;
  scanWorkspacePersistenceState.lastError = "";
  renderScanWorkspacePersistenceStatus();

  try {
    const saveUrl = payload.saved_scan_id
      ? `/planning/saved-scan/${encodeURIComponent(payload.saved_scan_id)}/state`
      : buildScanWorkspacePlanningEndpoint(
          "/planning/save-workspace-draft",
          getScanWorkspaceContext()?.planningOutputDir
        );
    const requestPayload = payload.saved_scan_id
      ? {
          selected_patch_candidate_ids: payload.selected_patch_candidate_ids || [],
          manual_bullet_edits: payload.manual_bullet_edits || {},
          rewrite_review_decisions: payload.rewrite_review_decisions || {},
          excluded_scan_issue_ids: payload.excluded_scan_issue_ids || [],
          personal_details: payload.personal_details || {},
          enable_live_tailoring_suggestion: getScanWorkspaceLiveTailoringSuggestionEnabled(),
          enable_live_exact_resume_change_proposal: getScanWorkspaceLiveExactChangeProposalEnabled(),
          enable_manual_exact_change_acceptance: getScanWorkspaceManualExactChangeAcceptanceEnabled(),
          accepted_exact_change_proposal_ids: getScanWorkspaceAcceptedExactChangeProposalIds(),
          enable_guarded_resume_copy_artifact_creation: getScanWorkspaceGuardedResumeCopyArtifactEnabled(),
          approved_change_plan_id: getScanWorkspaceApprovedChangePlanId(),
          enable_guarded_resume_copy_artifact_verification: getScanWorkspaceGuardedResumeCopyArtifactVerificationEnabled(),
          guarded_resume_copy_artifact_id: getScanWorkspaceGuardedResumeCopyArtifactId(),
          enable_verified_artifact_operator_review_packet: getScanWorkspaceVerifiedArtifactOperatorReviewPacketEnabled(),
          verified_artifact_operator_review_artifact_id: getScanWorkspaceVerifiedArtifactOperatorReviewArtifactId(),
          enable_verified_artifact_operator_decision_capture: getScanWorkspaceVerifiedArtifactOperatorDecisionEnabled(),
          verified_artifact_operator_decision_packet_id: getScanWorkspaceVerifiedArtifactOperatorDecisionPacketId(),
          verified_artifact_operator_decision_artifact_id: getScanWorkspaceVerifiedArtifactOperatorDecisionArtifactId(),
          verified_artifact_operator_decision_value: getScanWorkspaceVerifiedArtifactOperatorDecisionValue(),
          enable_operator_approved_artifact_application_readiness_packet: getScanWorkspaceApplicationReadinessPacketEnabled(),
          application_readiness_operator_decision_id: getScanWorkspaceApplicationReadinessDecisionId(),
          application_readiness_operator_review_packet_id: getScanWorkspaceApplicationReadinessReviewPacketId(),
          application_readiness_artifact_id: getScanWorkspaceApplicationReadinessArtifactId(),
          enable_human_only_manual_application_handoff_packet: getScanWorkspaceManualApplicationHandoffPacketEnabled(),
          manual_handoff_application_readiness_packet_id: getScanWorkspaceManualHandoffReadinessPacketId(),
          manual_handoff_artifact_id: getScanWorkspaceManualHandoffArtifactId(),
          enable_human_only_handoff_audit_trail: getScanWorkspaceHandoffAuditTrailEnabled(),
          handoff_audit_manual_handoff_packet_id: getScanWorkspaceHandoffAuditHandoffPacketId(),
          handoff_audit_application_readiness_packet_id: getScanWorkspaceHandoffAuditReadinessPacketId(),
          handoff_audit_artifact_id: getScanWorkspaceHandoffAuditArtifactId(),
          enable_human_only_safety_boundary_summary: getScanWorkspaceSafetyBoundarySummaryEnabled(),
          safety_boundary_handoff_audit_trail_id: getScanWorkspaceSafetyBoundaryAuditTrailId(),
          safety_boundary_manual_handoff_packet_id: getScanWorkspaceSafetyBoundaryHandoffPacketId(),
          safety_boundary_application_readiness_packet_id: getScanWorkspaceSafetyBoundaryReadinessPacketId(),
          safety_boundary_artifact_id: getScanWorkspaceSafetyBoundaryArtifactId(),
          enable_human_only_workflow_readiness_checkpoint: getScanWorkspaceWorkflowReadinessCheckpointEnabled(),
          workflow_readiness_safety_boundary_summary_id: getScanWorkspaceWorkflowReadinessSummaryId(),
          workflow_readiness_handoff_audit_trail_id: getScanWorkspaceWorkflowReadinessAuditTrailId(),
          workflow_readiness_manual_handoff_packet_id: getScanWorkspaceWorkflowReadinessHandoffPacketId(),
          workflow_readiness_application_readiness_packet_id: getScanWorkspaceWorkflowReadinessReadinessPacketId(),
          workflow_readiness_artifact_id: getScanWorkspaceWorkflowReadinessArtifactId(),
        }
      : payload;
    const response =
      typeof postJsonWithTimeout === "function"
        ? await postJsonWithTimeout(saveUrl, requestPayload, 20000)
        : await fetch(saveUrl, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(requestPayload),
          }).then(async (res) => {
            if (!res.ok) {
              let message = `Request failed (${res.status})`;
              try {
                const data = await res.json();
                message = String(data?.detail || data?.error_message || message);
              } catch {
                // ignore secondary parse error
              }
              throw new Error(message);
            }
            return res.json();
          });

    scanWorkspacePersistenceState.loadResponse = response;
    renderScanWorkspaceTailoringLlmReadback(response);
    renderScanWorkspaceExactChangeLlmReadback(response);
    renderScanWorkspaceManualExactChangeAcceptanceReadback(response);
    renderScanWorkspaceGuardedResumeCopyArtifactReadback(response);
    renderScanWorkspaceGuardedResumeCopyArtifactVerificationReadback(response);
    renderScanWorkspaceVerifiedArtifactOperatorReviewPacketReadback(response);
    renderScanWorkspaceVerifiedArtifactOperatorDecisionReadback(response);
    renderScanWorkspaceApplicationReadinessPacketReadback(response);
    renderScanWorkspaceManualApplicationHandoffPacketReadback(response);
    renderScanWorkspaceHandoffAuditTrailReadback(response);
    renderScanWorkspaceSafetyBoundarySummaryReadback(response);
    renderScanWorkspaceWorkflowReadinessCheckpointReadback(response);
    renderScanWorkspaceAgenticWorkflowIntegrationReadback(response);
    renderScanWorkspaceProductionReadinessCheckpoint(response);
    scanWorkspacePersistenceState.manualBulletEdits = {
      ...getScanWorkspaceManualBulletEdits(),
      ...(
        response?.draft?.manual_bullet_edits &&
        typeof response.draft.manual_bullet_edits === "object"
          ? response.draft.manual_bullet_edits
          : {}
      ),
    };
    if (typeof setScanWorkspaceExcludedIssueIds === "function") {
      setScanWorkspaceExcludedIssueIds(response?.draft?.excluded_scan_issue_ids || []);
    }
    const savedPersonalDetails = response?.draft?.personal_details || {};
    if (
      typeof setScanWorkspacePersonalDetails === "function" &&
      hasScanWorkspacePersonalDetailsValue(savedPersonalDetails)
    ) {
      setScanWorkspacePersonalDetails(savedPersonalDetails);
    }
    scanWorkspacePersistenceState.hydratedSignature = getCurrentScanWorkspacePersistenceSignature();
    scanWorkspacePersistenceState.lastError = "";
    renderScanWorkspacePersistenceStatus();

    if (typeof renderScanWorkspaceView === "function") {
      renderScanWorkspaceView();
    }
    await refreshScanWorkspaceScorePreview();
    const currentMode = normalizeScanWorkspaceMode(getScanWorkspacePageRoot()?.dataset.scanMode || "");
    if (currentMode === "review") {
      ensureScanWorkspaceDocumentPreviewLoaded({ force: true });
    }
    if (currentMode === "compare") {
      ensureScanWorkspaceCompareLoaded({ force: true });
    }

    return true;
  } catch (err) {
    scanWorkspacePersistenceState.lastError =
      err instanceof Error ? err.message : "Failed to save scan decisions.";
    renderScanWorkspacePersistenceStatus();
    return false;
  } finally {
    scanWorkspacePersistenceState.isSaving = false;
    renderScanWorkspacePersistenceStatus();
  }
}

function getScanWorkspaceExportFilename(response, fallbackName) {
  const disposition = String(response?.headers?.get?.("Content-Disposition") || "").trim();
  const filenameMatch = disposition.match(/filename\*?=(?:UTF-8''|")?([^";]+)"?/i);
  if (!filenameMatch) return fallbackName;

  try {
    return decodeURIComponent(filenameMatch[1]);
  } catch {
    return filenameMatch[1] || fallbackName;
  }
}

function downloadScanWorkspaceBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

async function exportScanWorkspaceDraft(format = "pdf") {
  const payload = buildScanWorkspacePersistencePayload();
  if (!payload) {
    scanWorkspacePersistenceState.lastError =
      "Workspace-draft export is unavailable for this scan.";
    renderScanWorkspacePersistenceStatus();
    return false;
  }

  const safeFormat = String(format || "").trim().toLowerCase() === "word" ? "word" : "pdf";
  const currentSignature = getCurrentScanWorkspacePersistenceSignature();
  const savedSignature = scanWorkspacePersistenceState.hydratedSignature || "";
  const isDirty = currentSignature !== savedSignature;

  scanWorkspacePersistenceState.isExporting = true;
  scanWorkspacePersistenceState.lastError = "";
  renderScanWorkspacePersistenceStatus();

  try {
    if (isDirty) {
      scanWorkspacePersistenceState.lastError = "Click Continue to save scan decisions before exporting.";
      renderScanWorkspacePersistenceStatus();
      return false;
    }

    const response = await fetch(buildScanWorkspacePlanningEndpoint(
      "/planning/export-workspace-draft",
      getScanWorkspaceContext()?.planningOutputDir
    ), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        tailoring_json_path: payload.tailoring_json_key || payload.tailoring_json_path,
        selected_resume: payload.selected_resume,
        format: safeFormat,
      }),
    });

    if (!response.ok) {
      let message = `Export failed (${response.status})`;
      try {
        const data = await response.json();
        message = String(data?.detail || data?.error_message || message);
      } catch {
        // keep response status message
      }
      throw new Error(message);
    }

    const blob = await response.blob();
    const fallbackName = safeFormat === "word"
      ? "optimized_resume.docx"
      : "optimized_resume.pdf";
    downloadScanWorkspaceBlob(blob, getScanWorkspaceExportFilename(response, fallbackName));

    const warningMessage = String(response.headers.get("X-Tailoring-Export-Warning-Message") || "").trim();
    scanWorkspacePersistenceState.lastError = warningMessage || "";
    renderScanWorkspacePersistenceStatus();
    return true;
  } catch (err) {
    scanWorkspacePersistenceState.lastError =
      err instanceof Error ? err.message : "Failed to export optimized draft.";
    renderScanWorkspacePersistenceStatus();
    return false;
  } finally {
    scanWorkspacePersistenceState.isExporting = false;
    renderScanWorkspacePersistenceStatus();
  }
}

function closeScanWorkspaceExportMenu() {
  const menu = getScanWorkspaceInput("scanWorkspaceExportMenu");
  const button = getScanWorkspaceInput("scanWorkspaceExportBtn");
  if (menu) menu.classList.add("hidden");
  if (button) button.setAttribute("aria-expanded", "false");
}

function toggleScanWorkspaceExportMenu() {
  const menu = getScanWorkspaceInput("scanWorkspaceExportMenu");
  const button = getScanWorkspaceInput("scanWorkspaceExportBtn");
  if (!menu || !button || button.disabled) return;

  const isOpen = !menu.classList.contains("hidden");
  menu.classList.toggle("hidden", isOpen);
  button.setAttribute("aria-expanded", isOpen ? "false" : "true");
}

function closeScanWorkspaceSuggestionPopover() {
  scanWorkspaceAnnotationState.activeMarkerId = "";
  renderScanWorkspaceAnnotationShell();
}

function openScanWorkspaceSuggestionPopover(markerId) {
  const marker = getScanWorkspaceAnnotationMarkerById(markerId);
  if (!marker) return false;

  const targetRow =
    getScanWorkspacePreviewMarkerTargetById(marker.id) ||
    findScanWorkspacePreviewTargetForMarker(marker, new Set());

  if (!targetRow) return false;

  scanWorkspaceAnnotationState.activeMarkerId = marker.id;
  resetScanWorkspacePhraseState(marker.id);
  renderScanWorkspaceAnnotationShell();

  window.requestAnimationFrame(() => {
    scrollScanWorkspacePreviewToMarker(marker);
    renderScanWorkspaceSuggestionPopover();
  });

  return true;
}

function openScanWorkspaceSuggestionPopoverForCandidateId(candidateId) {
  const safeCandidateId = String(candidateId || "").trim();
  if (!safeCandidateId) return false;

  const marker = scanWorkspaceAnnotationState.markers.find((item) =>
    Array.isArray(item?.candidateIds) &&
    item.candidateIds.some((value) => String(value || "").trim() === safeCandidateId)
  );

  if (!marker) return false;

  return openScanWorkspaceSuggestionPopover(marker.id);
}

function focusScanWorkspacePreviewTargetForCandidateId(candidateId) {
  const safeCandidateId = String(candidateId || "").trim();
  if (!safeCandidateId) return false;

  const marker = scanWorkspaceAnnotationState.markers.find((item) =>
    Array.isArray(item?.candidateIds) &&
    item.candidateIds.some((value) => String(value || "").trim() === safeCandidateId)
  );

  if (!marker) return false;

  scanWorkspaceAnnotationState.activeMarkerId = marker.id;
  closeScanWorkspaceSuggestionPopover();

  window.requestAnimationFrame(() => {
    scrollScanWorkspacePreviewToMarker(marker);
    decorateScanWorkspacePreviewSuggestionTargets();
    renderScanWorkspaceAnnotationOverlay();
    updateScanWorkspaceDecisionSummaryUi();
  });

  return true;
}

function renderScanWorkspaceAnnotationOverlay() {
  const overlay = getScanWorkspaceInput("scanWorkspaceAnnotationOverlay");
  const status = getScanWorkspaceInput("scanWorkspaceAnnotationStatus");
  if (!overlay || !status) return;

  const counts = getScanWorkspaceAnnotationDecisionCounts();

  overlay.innerHTML = "";

  if (!scanWorkspaceAnnotationState.markers.length) {
    status.textContent = "Annotation layer ready. Awaiting suggestion targets.";
    return;
  }

  status.textContent =
    `${counts.total} suggestion target(s) loaded. ` +
    `${counts.accepted} accepted, ${counts.rejected} rejected, ` +
    `${counts.pending} pending, ${counts.guidance} guidance.`;
}

function buildScanWorkspaceSuggestionDiffHtml(marker) {
  const originalText = String(marker?.originalText || "").trim();
  const suggestedText = String(marker?.suggestedText || "").trim();

  if (!originalText && !suggestedText) {
    return "";
  }

  return `
    <div class="scan-workspace-inline-diff">
      ${
        originalText
          ? `
            <div class="scan-workspace-inline-diff-del">
              ${scanWorkspaceEscapeHtml(originalText)}
            </div>
          `
          : ""
      }

      ${
        suggestedText
          ? `
            <div class="scan-workspace-inline-diff-add">
              ${scanWorkspaceEscapeHtml(suggestedText)}
            </div>
          `
          : ""
      }
    </div>
  `;
}

function getScanWorkspaceSuggestionPopoverPosition(marker) {
  const targetRow = getScanWorkspacePreviewMarkerTargetById(marker?.id);
  const popover = getScanWorkspaceInput("scanWorkspaceSuggestionPopover");

  const viewportPadding = 14;
  const gap = 10;
  const scrollerRect = getScanWorkspacePreviewScroller()?.getBoundingClientRect();
  const paneTop = Math.max(
    64,
    Number(scrollerRect?.top || 0) + 12,
    viewportPadding
  );
  const paneBottom = Math.min(
    window.innerHeight - viewportPadding,
    Number(scrollerRect?.bottom || window.innerHeight) - 12
  );

  const measuredRect = popover?.getBoundingClientRect();
  const measuredWidth = Math.max(340, Number(measuredRect?.width || popover?.offsetWidth || 390));
  const measuredHeight = Math.max(300, Number(measuredRect?.height || popover?.offsetHeight || 420));

  const width = Math.min(
    520,
    Math.max(420, Math.min(measuredWidth, 520)),
    window.innerWidth - viewportPadding * 2
  );
  const viewportMaxHeight = Math.max(
    420,
    Math.min(760, window.innerHeight - 80)
  );

  if (targetRow) {
    const targetRect = targetRow.getBoundingClientRect();
    const targetOutOfScroller =
      Boolean(scrollerRect) &&
      (targetRect.bottom <= scrollerRect.top || targetRect.top >= scrollerRect.bottom);
    const targetOutOfViewport =
      targetRect.bottom <= viewportPadding || targetRect.top >= window.innerHeight - viewportPadding;

    if (targetOutOfScroller || targetOutOfViewport) {
      return null;
    }

    const horizontalMin = Math.max(viewportPadding, Number(scrollerRect?.left || 0) + 18);
    const horizontalMax = Math.min(
      window.innerWidth - width - viewportPadding,
      Number(scrollerRect?.right || window.innerWidth) - width - 18
    );

    const preferredLeft = targetRect.left + targetRect.width / 2 - width / 2;

    const left = Math.max(
      horizontalMin,
      Math.min(Math.max(horizontalMin, horizontalMax), preferredLeft)
    );

    const aboveSpace = Math.max(0, targetRect.top - paneTop - gap);
    const belowSpace = Math.max(0, paneBottom - targetRect.bottom - gap);
    const preferAbove = aboveSpace >= 160 || aboveSpace >= belowSpace;
    const placement = preferAbove ? "above" : "below";
    const renderedHeight = Math.min(measuredHeight, viewportMaxHeight);

    const top =
      placement === "above"
        ? Math.max(paneTop, targetRect.top - gap - renderedHeight)
        : Math.min(
            paneBottom - renderedHeight,
            targetRect.bottom + gap
          );

    return {
      top: `${Math.max(paneTop, top)}px`,
      left: `${left}px`,
      width: `${width}px`,
      minWidth: "360px",
      maxHeight: `${viewportMaxHeight}px`,
      placement,
    };
  }

  return {
    top: `${paneTop}px`,
    left: `${Math.max(viewportPadding, window.innerWidth - width - viewportPadding)}px`,
    width: `${width}px`,
    minWidth: "360px",
    maxHeight: `${viewportMaxHeight}px`,
    placement: "floating",
  };
}

function positionScanWorkspaceSuggestionPopover(marker) {
  const popover = getScanWorkspaceInput("scanWorkspaceSuggestionPopover");
  if (!popover || !marker) return;

  const position = getScanWorkspaceSuggestionPopoverPosition(marker);
  if (!position) {
    closeScanWorkspaceSuggestionPopover();
    return;
  }

  popover.style.position = "fixed";
  popover.style.top = position.top;
  popover.style.left = position.left;
  popover.style.right = "auto";
  popover.style.bottom = "auto";
  popover.style.transform = "none";
  popover.style.width = position.width;
  popover.style.minWidth = position.minWidth;
  popover.style.maxWidth = "calc(100vw - 32px)";
  popover.style.maxHeight = position.maxHeight;

  popover.classList.remove("is-above", "is-below", "is-clamped", "is-floating", "is-centered-modal");
  popover.classList.add(`is-${position.placement}`);
}

function getScanWorkspacePreviewScroller() {
  return getScanWorkspaceInput("scanWorkspaceLiveDraftPreview");
}

function getScanWorkspaceChangedPreviewRows() {
  const scroller = getScanWorkspacePreviewScroller();
  if (!scroller) return [];

  return Array.from(
    scroller.querySelectorAll(
      ".tailoring-workspace-doc-line--changed, .tailoring-workspace-doc-line--focused"
    )
  );
}

function normalizeScanWorkspaceAnchorText(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/[•●◦▪]/g, " ")
    .replace(/[^a-z0-9%+.#/&\s-]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function normalizeScanWorkspaceManualEditKeyText(value) {
  return normalizeScanWorkspaceAnchorText(value)
    .replace(/[^a-z0-9%$&.,+/\- ]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function getScanWorkspaceMarkerBulletKey(marker) {
  const explicitKey = String(
    marker?.bulletKey ||
    marker?.bullet_key ||
    marker?.manualBulletKey ||
    marker?.manual_bullet_key ||
    ""
  ).trim();
  if (explicitKey) return explicitKey;

  const candidateIds = Array.isArray(marker?.candidateIds) ? marker.candidateIds : [];
  const candidateId = String(candidateIds[0] || "").trim();
  if (candidateId) return `candidate:${candidateId}`;

  const originalText = String(marker?.originalText || "").trim();
  const textKey = normalizeScanWorkspaceManualEditKeyText(originalText);
  return textKey ? `text:${textKey}` : "";
}

function getScanWorkspaceManualBulletEdits() {
  const normalized = {};
  Object.entries(scanWorkspacePersistenceState.manualBulletEdits || {}).forEach(([key, value]) => {
    const safeKey = String(key || "").trim();
    const safeValue = String(value || "").trim();
    if (safeKey && safeValue) normalized[safeKey] = safeValue;
  });
  return normalized;
}

function getScanWorkspaceManualTextForMarker(marker) {
  const bulletKey = getScanWorkspaceMarkerBulletKey(marker);
  if (!bulletKey) return "";
  return String(getScanWorkspaceManualBulletEdits()[bulletKey] || "").trim();
}

function resetScanWorkspacePhraseState(markerId = "") {
  scanWorkspacePhraseState.isLoading = false;
  scanWorkspacePhraseState.lastError = "";
  scanWorkspacePhraseState.lastNote = "";
  scanWorkspacePhraseState.markerId = String(markerId || "").trim();
  scanWorkspacePhraseState.options = [];
}

function getScanWorkspaceGuidanceSignalTerms(marker) {
  const terms = [];
  const seen = new Set();
  const addTerm = (value) => {
    const safe = String(value || "")
      .replace(/\bthis opening clause\b/gi, "")
      .replace(/\bopening clause\b/gi, "")
      .replace(/\s+/g, " ")
      .trim()
      .replace(/^[,.;:\s]+|[,.;:\s]+$/g, "");
    if (!safe || safe.length > 48) return;
    const key = safe.toLowerCase();
    if (seen.has(key)) return;
    seen.add(key);
    terms.push(safe);
  };

  const guidance = String(marker?.suggestedText || marker?.reasonText || "").trim();
  const leadMatch = guidance.match(/\blead with\s+(.+?)\s+(?:in|within|then|and)\b/i);
  if (leadMatch) addTerm(leadMatch[1]);

  (Array.isArray(marker?.supportedTerms) ? marker.supportedTerms : []).forEach(addTerm);
  return terms.slice(0, 3);
}

function normalizeScanWorkspacePhraseArtifactKey(value) {
  const raw = String(value || "").trim();
  if (!raw) return "";
  if (raw.endsWith("__tailoring.json")) {
    return `${raw.slice(0, -"__tailoring.json".length)}.json`;
  }
  if (raw.endsWith("_tailoring.json")) {
    return `${raw.slice(0, -"_tailoring.json".length)}.json`;
  }
  return raw;
}

function scanWorkspacePhraseErrorMessage(error) {
  const message = error instanceof Error
    ? String(error.message || "").trim()
    : String(error || "").trim();
  if (/artifact not found/i.test(message)) {
    return "Regenerate suggestions first to create the scan artifact.";
  }
  return message || "Failed to generate LLM phrase options.";
}

function buildScanWorkspacePhraseRequest(marker) {
  const baseRequest = buildScanWorkspaceDocumentPreviewRequest([]);
  if (!baseRequest || !marker) return null;

  return {
    tailoring_json_path: normalizeScanWorkspacePhraseArtifactKey(baseRequest.tailoring_json_path),
    selected_resume: baseRequest.selected_resume,
    bullet_key: getScanWorkspaceMarkerBulletKey(marker),
    current_text: getScanWorkspaceManualTextForMarker(marker) || String(marker?.originalText || "").trim(),
    guidance_text: String(marker?.suggestedText || marker?.reasonText || "").trim(),
    supported_terms: Array.isArray(marker?.supportedTerms) ? marker.supportedTerms : [],
  };
}

function renderScanWorkspacePhraseOptionsHtml(marker) {
  if (!marker || isScanWorkspaceReplacementMarker(marker)) return "";

  const isCurrentMarker = scanWorkspacePhraseState.markerId === marker.id;
  const options = isCurrentMarker && Array.isArray(scanWorkspacePhraseState.options)
    ? scanWorkspacePhraseState.options
    : [];
  const errorText = isCurrentMarker ? String(scanWorkspacePhraseState.lastError || "").trim() : "";
  const noteText = isCurrentMarker ? String(scanWorkspacePhraseState.lastNote || "").trim() : "";

  return `
    <div class="scan-workspace-phrase-tools">
      <button
        type="button"
        class="scan-workspace-phrase-generate-btn"
        data-scan-phrase-action="generate"
        ${scanWorkspacePhraseState.isLoading && isCurrentMarker ? "disabled" : ""}
      >
        ${scanWorkspacePhraseState.isLoading && isCurrentMarker ? "Generating..." : "Generate LLM phrase options"}
      </button>

      ${errorText ? `
        <div class="scan-workspace-phrase-status is-error">
          ${scanWorkspaceEscapeHtml(errorText)}
        </div>
      ` : ""}

      ${noteText ? `
        <div class="scan-workspace-phrase-status">
          ${scanWorkspaceEscapeHtml(noteText)}
        </div>
      ` : ""}

      ${options.length ? `
        <div class="scan-workspace-phrase-option-list">
          ${options.map((option, index) => `
            <button
              type="button"
              class="scan-workspace-phrase-option"
              data-scan-phrase-option="${scanWorkspaceEscapeHtml(String(option?.option_id || index))}"
            >
              <span class="scan-workspace-phrase-option-index">${index + 1}</span>
              <span class="scan-workspace-phrase-option-text">
                ${scanWorkspaceEscapeHtml(String(option?.text || "").trim())}
              </span>
            </button>
          `).join("")}
        </div>
      ` : ""}
    </div>
  `;
}

function getScanWorkspaceMarkerAnchorTexts(marker) {
  return [
    marker?.anchorText,
    marker?.originalText,
    marker?.suggestedText,
    marker?.copy,
    marker?.title,
  ]
    .map((value) => normalizeScanWorkspaceAnchorText(value))
    .filter((value) => value && value.length >= 16);
}

function getScanWorkspacePreviewRowsForAnchoring() {
  const scroller = getScanWorkspacePreviewScroller();
  if (!scroller) return [];

  return Array.from(
    scroller.querySelectorAll(
      ".tailoring-workspace-doc-line, .tailoring-workspace-doc-bullet-row, .tailoring-workspace-doc-line-copy, .tailoring-workspace-doc-bullet-copy"
    )
  ).filter((row) => normalizeScanWorkspaceAnchorText(row.textContent).length >= 16);
}

function scoreScanWorkspacePreviewRowForMarker(row, marker) {
  const rowText = normalizeScanWorkspaceAnchorText(row?.textContent || "");
  if (!rowText) return 0;

  const markerTexts = getScanWorkspaceMarkerAnchorTexts(marker);
  let bestScore = 0;

  markerTexts.forEach((markerText) => {
    if (!markerText) return;

    if (rowText === markerText) {
      bestScore = Math.max(bestScore, 1000);
      return;
    }

    if (rowText.includes(markerText)) {
      bestScore = Math.max(bestScore, 800 + Math.min(markerText.length, 160));
      return;
    }

    if (markerText.includes(rowText) && rowText.length >= 32) {
      bestScore = Math.max(bestScore, 600 + Math.min(rowText.length, 120));
      return;
    }

    const markerWords = new Set(markerText.split(" ").filter((word) => word.length >= 4));
    const rowWords = new Set(rowText.split(" ").filter((word) => word.length >= 4));
    const overlap = Array.from(markerWords).filter((word) => rowWords.has(word)).length;

    if (overlap >= 5) {
      bestScore = Math.max(bestScore, 100 + overlap * 20);
    }
  });

  return bestScore;
}

function findScanWorkspacePreviewTargetForMarker(marker, usedRows = new Set()) {
  if (!marker || marker?.canFocusPreview === false) return null;

  const rows = getScanWorkspacePreviewRowsForAnchoring();
  let bestRow = null;
  let bestScore = 0;

  rows.forEach((row) => {
    if (usedRows.has(row)) return;

    const score = scoreScanWorkspacePreviewRowForMarker(row, marker);
    if (score > bestScore) {
      bestScore = score;
      bestRow = row;
    }
  });

  return bestScore >= 180 ? bestRow : null;
}

function getScanWorkspacePreviewMarkerTargetById(markerId) {
  const safeMarkerId = String(markerId || "").trim();
  if (!safeMarkerId) return null;

  const scroller = getScanWorkspacePreviewScroller();
  if (!scroller) return null;

  return (
    Array.from(scroller.querySelectorAll("[data-scan-preview-marker]")).find(
      (row) => String(row.dataset.scanPreviewMarker || "").trim() === safeMarkerId
    ) || null
  );
}

function clearScanWorkspacePreviewSuggestionTargets() {
  const scroller = getScanWorkspacePreviewScroller();
  if (!scroller) return;

  scroller.querySelectorAll("[data-scan-preview-marker]").forEach((row) => {
    row.classList.remove(
      "scan-workspace-preview-suggestion-target",
      "is-scan-preview-active",
      "scan-workspace-preview-suggestion-target--guidance",
      "scan-workspace-preview-suggestion-target--replacement",
      "is-scan-decision-accepted",
      "is-scan-decision-rejected",
      "is-scan-decision-pending"
    );
    row.removeAttribute("data-scan-preview-marker");
    row.removeAttribute("data-scan-preview-mode");
    row.removeAttribute("data-scan-preview-decision");
    row.removeAttribute("role");
    row.removeAttribute("tabindex");
    row.removeAttribute("title");
  });
}

function decorateScanWorkspacePreviewSuggestionTargets() {
  const scroller = getScanWorkspacePreviewScroller();
  if (!scroller) return;

  clearScanWorkspacePreviewSuggestionTargets();

  if (!scanWorkspaceAnnotationState.markers.length) return;

  const usedRows = new Set();

  scanWorkspaceAnnotationState.markers.forEach((marker) => {
    if (marker?.canFocusPreview === false) return;

    const targetRow = findScanWorkspacePreviewTargetForMarker(marker, usedRows);
    if (!targetRow) return;

    usedRows.add(targetRow);

    targetRow.classList.add("scan-workspace-preview-suggestion-target");
    targetRow.classList.add(
      isScanWorkspaceReplacementMarker(marker)
        ? "scan-workspace-preview-suggestion-target--replacement"
        : "scan-workspace-preview-suggestion-target--guidance"
    );

    const decision = normalizeScanWorkspaceAnnotationDecision(marker?.decision);
    targetRow.classList.add(`is-scan-decision-${decision}`);
    targetRow.dataset.scanPreviewMarker = marker.id;
    targetRow.dataset.scanPreviewMode = isScanWorkspaceReplacementMarker(marker)
      ? "replacement"
      : "guidance";
    targetRow.dataset.scanPreviewDecision = decision;
    targetRow.setAttribute("role", "button");
    targetRow.setAttribute("tabindex", "0");
    targetRow.setAttribute("title", "Click to review the suggested change");

    if (scanWorkspaceAnnotationState.activeMarkerId === marker.id) {
      targetRow.classList.add("is-scan-preview-active");
    }

    syncScanWorkspacePreviewMarkerContent(targetRow, marker);
  });
}

function getScanWorkspacePreviewMarkerTextNode(targetRow) {
  return targetRow?.querySelector?.(".scan-workspace-preview-line-text") || null;
}

function applyScanWorkspaceDraftFragments(fragmentsPayload) {
  const rows = Array.isArray(fragmentsPayload?.changed_bullets)
    ? fragmentsPayload.changed_bullets
    : [];
  const byBulletKey = {};

  rows.forEach((fragment) => {
    const bulletKey = String(fragment?.bullet_key || fragment?.bulletKey || "").trim();
    const currentText = String(
      fragment?.current_text || fragment?.patch_text || fragment?.text || ""
    ).trim();
    if (!bulletKey || !currentText) return;
    byBulletKey[bulletKey] = {
      ...fragment,
      bullet_key: bulletKey,
      current_text: currentText,
    };
  });

  scanWorkspacePreviewState.draftFragmentsPayload = fragmentsPayload || null;
  scanWorkspacePreviewState.draftFragmentsByBulletKey = byBulletKey;

  if (!Object.keys(byBulletKey).length) return;

  scanWorkspaceAnnotationState.markers.forEach((marker) => {
    const bulletKey = getScanWorkspaceMarkerBulletKey(marker);
    const fragment = bulletKey ? byBulletKey[bulletKey] : null;
    if (!fragment) return;

    const targetRow = getScanWorkspacePreviewMarkerTargetById(marker.id);
    const textNode = getScanWorkspacePreviewMarkerTextNode(targetRow);
    const nextText = String(fragment.current_text || "").trim();
    if (!targetRow || !textNode || !nextText) return;

    if (textNode.textContent !== nextText) {
      textNode.textContent = nextText;
      targetRow.classList.remove("is-scan-preview-fragment-updated");
      void targetRow.offsetWidth;
      targetRow.classList.add("is-scan-preview-fragment-updated");
    }
  });
}

function syncScanWorkspacePreviewMarkerContent(targetRow, marker) {
  if (!targetRow) return;

  const textNode = getScanWorkspacePreviewMarkerTextNode(targetRow);
  if (!textNode) return;

  const decision = normalizeScanWorkspaceAnnotationDecision(marker?.decision);
  const originalText = String(marker?.originalText || "").trim();
  const suggestedText = String(marker?.suggestedText || "").trim();
  const manualText = getScanWorkspaceManualTextForMarker(marker);
  const bulletKey = getScanWorkspaceMarkerBulletKey(marker);
  const fragmentText = String(
    scanWorkspacePreviewState.draftFragmentsByBulletKey?.[bulletKey]?.current_text || ""
  ).trim();
  const nextText =
    fragmentText ||
    manualText ||
    (decision === "accepted" ? suggestedText : originalText);

  if (!nextText) return;
  if (textNode.textContent !== nextText) {
    textNode.textContent = nextText;
  }
}

function scrollScanWorkspacePreviewToMarker(marker) {
  const scroller = getScanWorkspacePreviewScroller();
  if (!scroller || !marker) return;

  const targetRow =
    getScanWorkspacePreviewMarkerTargetById(marker?.id) ||
    findScanWorkspacePreviewTargetForMarker(marker, new Set());

  if (!targetRow) return;

  targetRow.scrollIntoView({
    behavior: "smooth",
    block: "center",
    inline: "nearest",
  });
}

function shouldRenderScanWorkspacePopoverDiff(marker) {
  return marker?.renderMode === "diff" || marker?.isExactReplacement === true;
}

function isScanWorkspaceReplacementMarker(marker) {
  return shouldRenderScanWorkspacePopoverDiff(marker);
}

function getScanWorkspaceSuggestionActionLabel(marker) {
  if (shouldRenderScanWorkspacePopoverDiff(marker)) {
    return "AI suggested to REPLACE CONTENT";
  }

  const tone = String(marker?.tone || "").trim().toLowerCase();
  if (tone === "add") return "AI suggested to ADD CONTENT";
  if (tone === "focus") return "AI suggested to EMPHASIZE CONTENT";
  return "AI suggested to IMPROVE CONTENT";
}

function renderScanWorkspaceSuggestionPopoverCopyHtml(marker) {
  const originalText = String(marker?.originalText || "").trim();
  const suggestedText = String(marker?.suggestedText || "").trim();
  const reasonText = String(marker?.reasonText || marker?.copy || "").trim();
  const shouldRenderDiff = shouldRenderScanWorkspacePopoverDiff(marker);

  if (shouldRenderDiff && originalText && suggestedText) {
    return `
      <div class="scan-workspace-inline-diff">
        <div class="scan-workspace-inline-diff-del">${scanWorkspaceEscapeHtml(originalText)}</div>
        <div class="scan-workspace-inline-diff-add">${scanWorkspaceEscapeHtml(suggestedText)}</div>
      </div>
      ${reasonText ? `
        <div class="scan-workspace-suggestion-reason">
          ${scanWorkspaceEscapeHtml(reasonText)}
        </div>
      ` : ""}
    `;
  }

  return `
    <div class="scan-workspace-guidance-editor">
      <section class="scan-workspace-best-draft">
        <textarea
          class="scan-workspace-guidance-textarea"
          id="scanWorkspaceGuidanceTextarea"
          data-scan-guidance-textarea="true"
          rows="4"
          aria-label="Edit draft bullet"
          placeholder="Rewrite this bullet using the guidance above."
        >${scanWorkspaceEscapeHtml(getScanWorkspaceManualTextForMarker(marker) || originalText)}</textarea>
      </section>
      ${renderScanWorkspacePhraseOptionsHtml(marker)}
    </div>
    ${reasonText && reasonText !== suggestedText ? `
      <div class="scan-workspace-suggestion-reason">
        ${scanWorkspaceEscapeHtml(reasonText)}
      </div>
    ` : ""}
  `;
}

function refreshScanWorkspaceGuidanceSaveButton(marker) {
  const saveBtn = getScanWorkspaceInput("scanWorkspaceSuggestionResetBtn");
  const textarea = getScanWorkspaceInput("scanWorkspaceGuidanceTextarea");
  if (!saveBtn || !textarea || !marker || isScanWorkspaceReplacementMarker(marker)) return;

  const originalText = String(marker?.originalText || "").trim();
  const nextText = String(textarea.value || "").trim();
  const savedText = getScanWorkspaceManualTextForMarker(marker);
  const hasChanged = Boolean(nextText) && nextText !== originalText && nextText !== savedText;

  saveBtn.disabled = !hasChanged || scanWorkspacePersistenceState.isSaving;
  saveBtn.textContent = scanWorkspacePersistenceState.isSaving ? "Saving..." : "Save edit";
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
  const kicker = popover?.querySelector(".scan-workspace-suggestion-popover-kicker");

  if (!popover || !title || !copy || !decisionPill || !decisionMeta || !acceptBtn || !rejectBtn) {
    return;
  }

  const marker = getScanWorkspaceAnnotationMarkerById(
    scanWorkspaceAnnotationState.activeMarkerId
  );
  const isReplacement = isScanWorkspaceReplacementMarker(marker);
  const hasPhraseOptions =
    Boolean(marker) &&
    scanWorkspacePhraseState.markerId === marker.id &&
    Array.isArray(scanWorkspacePhraseState.options) &&
    scanWorkspacePhraseState.options.length > 0;

  if (!marker) {
    popover.classList.add("hidden");
    popover.style.top = "";
    popover.style.left = "";
    popover.style.right = "";
    popover.style.bottom = "";
    popover.style.transform = "";
    title.textContent = "Select a suggestion anchor to inspect it here.";
    if (kicker) kicker.textContent = "AI suggested change";
    copy.textContent = "";
    decisionPill.textContent = "Pending";
    decisionPill.className =
      "scan-workspace-suggestion-decision-pill scan-workspace-suggestion-decision-pill--pending";
    decisionMeta.textContent = "No decision recorded yet.";
    acceptBtn.disabled = true;
    rejectBtn.disabled = true;
    if (resetBtn) {
      resetBtn.disabled = true;
      resetBtn.hidden = true;
      resetBtn.classList.remove("scan-workspace-suggestion-action-btn--save-guidance");
    }
    acceptBtn.classList.remove("is-active");
    rejectBtn.classList.remove("is-active");
    return;
  }

  const decision = normalizeScanWorkspaceAnnotationDecision(marker.decision);
  const sourceLabel = String(marker.sourceLabel || "AI suggested").trim();
  const reasonText = String(marker.reasonText || "").trim();

  popover.classList.remove("hidden");
  popover.classList.toggle("has-phrase-options", hasPhraseOptions);
  popover.style.visibility = "hidden";
  popover.style.position = "fixed";
  popover.style.top = "0";
  popover.style.left = "0";
  popover.style.right = "auto";
  popover.style.bottom = "auto";
  popover.style.transform = "none";
  popover.style.width = "min(520px, calc(100vw - 32px))";
  popover.style.minWidth = "0";
  popover.style.maxWidth = "calc(100vw - 32px)";
  popover.style.maxHeight = "calc(100vh - 28px)";

  title.textContent = sourceLabel;
  if (kicker) {
    kicker.textContent = getScanWorkspaceSuggestionActionLabel(marker);
  }

  copy.innerHTML = renderScanWorkspaceSuggestionPopoverCopyHtml(marker);
  positionScanWorkspaceSuggestionPopover(marker);
  
  window.requestAnimationFrame(() => {
    positionScanWorkspaceSuggestionPopover(marker);
    popover.style.visibility = "";
  });

  decisionPill.textContent =
    decision === "accepted" ? "Accepted" : decision === "rejected" ? "Rejected" : "Pending";

  decisionPill.className =
    decision === "accepted"
      ? "scan-workspace-suggestion-decision-pill scan-workspace-suggestion-decision-pill--accepted"
      : decision === "rejected"
        ? "scan-workspace-suggestion-decision-pill scan-workspace-suggestion-decision-pill--rejected"
        : "scan-workspace-suggestion-decision-pill scan-workspace-suggestion-decision-pill--pending";

  decisionMeta.textContent = isReplacement
    ? ""
    : "Guidance only. Edit the draft bullet here, then save to rescore.";

  const hasSavedManualEdit = Boolean(getScanWorkspaceManualTextForMarker(marker));

  acceptBtn.hidden = !isReplacement;
  acceptBtn.textContent = decision === "accepted" ? "Accepted" : "Accept";
  acceptBtn.disabled = !isReplacement || decision === "accepted";
  acceptBtn.setAttribute("aria-pressed", decision === "accepted" ? "true" : "false");

  rejectBtn.hidden = false;
  rejectBtn.textContent = isReplacement
    ? decision === "rejected" ? "Rejected" : "Reject"
    : "Revert edit";
  rejectBtn.disabled = isReplacement ? decision === "rejected" : !hasSavedManualEdit;
  rejectBtn.dataset.scanGuidanceAction = isReplacement ? "" : "revert_guidance";
  rejectBtn.setAttribute(
    "aria-pressed",
    isReplacement && decision === "rejected" ? "true" : "false"
  );
  if (resetBtn) {
    resetBtn.hidden = isReplacement;
    resetBtn.disabled = true;
    resetBtn.textContent = isReplacement ? "Reset" : "Save edit";
    resetBtn.dataset.scanGuidanceAction = isReplacement ? "" : "save_guidance";
    resetBtn.classList.toggle("scan-workspace-suggestion-action-btn--save-guidance", !isReplacement);
  }

  acceptBtn.classList.toggle("is-active", decision === "accepted");
  rejectBtn.classList.toggle("is-active", decision === "rejected");
  refreshScanWorkspaceGuidanceSaveButton(marker);
}

function scrollScanWorkspacePhraseOptionsIntoPopoverView() {
  const popover = getScanWorkspaceInput("scanWorkspaceSuggestionPopover");
  if (!popover || popover.classList.contains("hidden")) return;

  const optionsList = popover.querySelector(".scan-workspace-phrase-option-list");
  if (!optionsList) return;

  window.requestAnimationFrame(() => {
    popover.scrollTo({
      top: Math.max(0, optionsList.offsetTop - 14),
      behavior: "smooth",
    });
  });
}

function renderScanWorkspaceAnnotationShell() {
  updateScanWorkspaceSurfaceTabs();
  renderScanWorkspaceAnnotationOverlay();
  renderScanWorkspaceSuggestionPopover();
  updateScanWorkspaceDecisionSummaryUi();
}

function setScanWorkspaceAnnotationMarkers(markers) {
  const inlinePreview = getScanWorkspaceInlineDocumentPreview();
  const hasRenderableContext = getScanWorkspaceHasTailoringPreviewContext();
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

  applySavedDraftStateToScanMarkers();
  scanWorkspaceAnnotationState.undoStack = [];
  scanWorkspaceAnnotationState.redoStack = [];

  scanWorkspacePreviewState.documentPreviewPayload = hasRenderableContext ? null : inlinePreview;
  scanWorkspacePreviewState.isDocumentPreviewLoading = false;
  scanWorkspacePreviewState.scorePreviewPayload = null;
  scanWorkspaceCompareState.beforePayload = null;
  scanWorkspaceCompareState.afterPayload = null;

  renderScanWorkspaceAnnotationShell();
  renderScanWorkspaceCompareShell();
  decorateScanWorkspacePreviewSuggestionTargets();

  if (normalizeScanWorkspaceMode(getScanWorkspacePageRoot()?.dataset.scanMode || "") === "review") {
    ensureScanWorkspaceDocumentPreviewLoaded({ force: true });
  }

  if (normalizeScanWorkspaceMode(getScanWorkspacePageRoot()?.dataset.scanMode || "") === "compare") {
    ensureScanWorkspaceCompareLoaded({ force: true });
  }
}

function applyScanWorkspaceDecisionToActiveMarker(decision) {
  const activeMarker = getScanWorkspaceAnnotationMarkerById(
    scanWorkspaceAnnotationState.activeMarkerId
  );
  if (!activeMarker) return;

  if (!isScanWorkspaceReplacementMarker(activeMarker)) {
    closeScanWorkspaceSuggestionPopover();
    return;
  }

  const nextDecision = normalizeScanWorkspaceAnnotationDecision(decision);
  if (normalizeScanWorkspaceAnnotationDecision(activeMarker.decision) === nextDecision) return;

  pushScanWorkspaceDecisionHistory();
  setScanWorkspaceMarkerDecision(activeMarker.id, decision);
  refreshScanWorkspaceDecisionOutputs({ forcePreview: false });
}

async function saveScanWorkspaceGuidanceEditForActiveMarker() {
  const marker = getScanWorkspaceAnnotationMarkerById(
    scanWorkspaceAnnotationState.activeMarkerId
  );
  const textarea = getScanWorkspaceInput("scanWorkspaceGuidanceTextarea");
  if (!marker || !textarea || isScanWorkspaceReplacementMarker(marker)) return;

  const bulletKey = getScanWorkspaceMarkerBulletKey(marker);
  const nextText = String(textarea.value || "").trim();
  const originalText = String(marker.originalText || "").trim();
  if (!bulletKey || !nextText || nextText === originalText) return;

  pushScanWorkspaceDecisionHistory();
  scanWorkspacePersistenceState.manualBulletEdits = {
    ...getScanWorkspaceManualBulletEdits(),
    [bulletKey]: nextText,
  };

  decorateScanWorkspacePreviewSuggestionTargets();
  refreshScanWorkspaceGuidanceSaveButton(marker);
  await refreshScanWorkspaceScorePreview();
  if (normalizeScanWorkspaceMode(getScanWorkspacePageRoot()?.dataset.scanMode || "") === "review") {
    ensureScanWorkspaceDocumentPreviewLoaded({ force: true });
  }
  if (normalizeScanWorkspaceMode(getScanWorkspacePageRoot()?.dataset.scanMode || "") === "compare") {
    ensureScanWorkspaceCompareLoaded({ force: true });
  }
  renderScanWorkspacePersistenceStatus();
  renderScanWorkspaceSuggestionPopover();
}

async function revertScanWorkspaceGuidanceEditForActiveMarker() {
  const marker = getScanWorkspaceAnnotationMarkerById(
    scanWorkspaceAnnotationState.activeMarkerId
  );
  if (!marker || isScanWorkspaceReplacementMarker(marker)) return;

  const bulletKey = getScanWorkspaceMarkerBulletKey(marker);
  const currentManualEdits = getScanWorkspaceManualBulletEdits();
  if (!bulletKey || !Object.prototype.hasOwnProperty.call(currentManualEdits, bulletKey)) return;

  pushScanWorkspaceDecisionHistory();
  const nextManualEdits = { ...currentManualEdits };
  delete nextManualEdits[bulletKey];
  scanWorkspacePersistenceState.manualBulletEdits = nextManualEdits;

  decorateScanWorkspacePreviewSuggestionTargets();
  renderScanWorkspaceSuggestionPopover();
  await refreshScanWorkspaceScorePreview();
  if (normalizeScanWorkspaceMode(getScanWorkspacePageRoot()?.dataset.scanMode || "") === "review") {
    ensureScanWorkspaceDocumentPreviewLoaded({ force: true });
  }
  if (normalizeScanWorkspaceMode(getScanWorkspacePageRoot()?.dataset.scanMode || "") === "compare") {
    ensureScanWorkspaceCompareLoaded({ force: true });
  }
  renderScanWorkspacePersistenceStatus();
}

async function generateScanWorkspacePhrasesForActiveMarker() {
  const marker = getScanWorkspaceAnnotationMarkerById(
    scanWorkspaceAnnotationState.activeMarkerId
  );
  if (!marker || isScanWorkspaceReplacementMarker(marker)) return;

  const requestBody = buildScanWorkspacePhraseRequest(marker);
  if (!requestBody) {
    scanWorkspacePhraseState.markerId = marker.id;
    scanWorkspacePhraseState.options = [];
    scanWorkspacePhraseState.lastNote = "";
    scanWorkspacePhraseState.lastError = "Cannot generate phrase options for this scan row.";
    renderScanWorkspaceSuggestionPopover();
    return;
  }

  scanWorkspacePhraseState.isLoading = true;
  scanWorkspacePhraseState.lastError = "";
  scanWorkspacePhraseState.lastNote = "";
  scanWorkspacePhraseState.markerId = marker.id;
  scanWorkspacePhraseState.options = [];
  renderScanWorkspaceSuggestionPopover();

  try {
    const context = getScanWorkspaceContext();
    const phraseUrl = buildScanWorkspacePlanningEndpoint(
      "/planning/generate-scan-phrases",
      context?.planningOutputDir
    );
    const response =
      typeof postJsonWithTimeout === "function"
        ? await postJsonWithTimeout(phraseUrl, requestBody, 20000)
        : await fetch(phraseUrl, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(requestBody),
          }).then(async (res) => {
            if (!res.ok) {
              let message = `Request failed (${res.status})`;
              try {
                const data = await res.json();
                message = String(data?.detail || data?.error_message || message);
              } catch {
                // ignore secondary parse error
              }
              throw new Error(message);
            }
            return res.json();
          });

    const responseOptions = Array.isArray(response?.options)
      ? response.options
      : [];
    scanWorkspacePhraseState.options = responseOptions;
    scanWorkspacePhraseState.lastNote = String(response?.note || "").trim();
    scanWorkspacePhraseState.lastError = !responseOptions.length
      ? String(response?.llm_error || "").trim()
      : "";
  } catch (err) {
    scanWorkspacePhraseState.options = [];
    scanWorkspacePhraseState.lastNote = "";
    scanWorkspacePhraseState.lastError = scanWorkspacePhraseErrorMessage(err);
  } finally {
    scanWorkspacePhraseState.isLoading = false;
    renderScanWorkspaceSuggestionPopover();
    if (scanWorkspacePhraseState.options.length) {
      scrollScanWorkspacePhraseOptionsIntoPopoverView();
    }
  }
}

function applyScanWorkspacePhraseOption(optionId) {
  const safeOptionId = String(optionId || "").trim();
  const textarea = getScanWorkspaceInput("scanWorkspaceGuidanceTextarea");
  if (!safeOptionId || !textarea) return;

  const option = (scanWorkspacePhraseState.options || []).find((item, index) => (
    String(item?.option_id || index).trim() === safeOptionId
  ));
  const text = String(option?.text || "").trim();
  if (!text) return;

  textarea.value = text;
  textarea.dispatchEvent(new Event("input", { bubbles: true }));
}

function bindScanWorkspaceAnnotationShell() {
  document.querySelectorAll("[data-scan-surface]").forEach((button) => {
    if (button.dataset.surfaceBound === "true") return;
    button.dataset.surfaceBound = "true";

    button.addEventListener("click", () => {
      if (button.disabled) return;

      const nextSurface = normalizeScanWorkspaceSurface(button.dataset.scanSurface || "");
      if (nextSurface === scanWorkspacePreviewState.activeSurface) return;

      closeScanWorkspaceSuggestionPopover();
      scanWorkspacePreviewState.activeSurface = nextSurface;
      renderScanWorkspaceAnnotationShell();

      if (nextSurface === "job_description") {
        renderScanWorkspaceJobDescriptionSurfaceInto();
      } else {
        ensureScanWorkspaceDocumentPreviewLoaded();
      }
    });
  });

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
      if (rejectBtn.dataset.scanGuidanceAction === "revert_guidance") {
        revertScanWorkspaceGuidanceEditForActiveMarker();
        return;
      }

      applyScanWorkspaceDecisionToActiveMarker("rejected");
    });
  }

  const resetBtn = getScanWorkspaceInput("scanWorkspaceSuggestionResetBtn");
  if (resetBtn && resetBtn.dataset.bound !== "true") {
    resetBtn.dataset.bound = "true";
    resetBtn.addEventListener("click", () => {
      if (resetBtn.dataset.scanGuidanceAction === "save_guidance") {
        saveScanWorkspaceGuidanceEditForActiveMarker();
        return;
      }

      applyScanWorkspaceDecisionToActiveMarker("pending");
    });
  }

  const popover = getScanWorkspaceInput("scanWorkspaceSuggestionPopover");
  if (popover && popover.dataset.guidanceBound !== "true") {
    popover.dataset.guidanceBound = "true";
    popover.addEventListener("click", (event) => {
      event.stopPropagation();
    });
    popover.addEventListener("input", (event) => {
      const textarea = event.target.closest("[data-scan-guidance-textarea]");
      if (!textarea) return;

      const marker = getScanWorkspaceAnnotationMarkerById(
        scanWorkspaceAnnotationState.activeMarkerId
      );
      refreshScanWorkspaceGuidanceSaveButton(marker);
    });
    popover.addEventListener("click", (event) => {
      event.stopPropagation();
      const generateBtn = event.target.closest("[data-scan-phrase-action='generate']");
      if (generateBtn) {
        event.preventDefault();
        generateScanWorkspacePhrasesForActiveMarker();
        return;
      }

      const optionBtn = event.target.closest("[data-scan-phrase-option]");
      if (optionBtn) {
        event.preventDefault();
        applyScanWorkspacePhraseOption(optionBtn.dataset.scanPhraseOption);
      }
    });
  }

  const acceptAllBtn = getScanWorkspaceInput("scanWorkspaceAcceptAllAiBtn");
  if (acceptAllBtn && acceptAllBtn.dataset.bound !== "true") {
    acceptAllBtn.dataset.bound = "true";
    acceptAllBtn.addEventListener("click", () => {
      flashScanWorkspaceActionButton(acceptAllBtn);
      const replacementMarkers = scanWorkspaceAnnotationState.markers.filter((marker) =>
        isScanWorkspaceReplacementMarker(marker)
      );
      if (!replacementMarkers.length) {
        updateScanWorkspaceDecisionSummaryUi();
        return;
      }
      if (!scanWorkspaceAnnotationState.markers.some((marker) => (
        isScanWorkspaceReplacementMarker(marker) &&
        normalizeScanWorkspaceAnnotationDecision(marker?.decision) !== "accepted"
      ))) {
        updateScanWorkspaceDecisionSummaryUi();
        return;
      }

      pushScanWorkspaceDecisionHistory();
      scanWorkspaceAnnotationState.markers = scanWorkspaceAnnotationState.markers.map((marker) => ({
        ...marker,
        decision: isScanWorkspaceReplacementMarker(marker) ? "accepted" : marker.decision,
      }));

      refreshScanWorkspaceDecisionOutputs({ forcePreview: false });
    });
  }

  const undoBtn = getScanWorkspaceInput("scanWorkspaceUndoBtn");
  if (undoBtn && undoBtn.dataset.bound !== "true") {
    undoBtn.dataset.bound = "true";
    undoBtn.addEventListener("click", () => {
      flashScanWorkspaceActionButton(undoBtn);
      undoScanWorkspaceDecisionChange();
      updateScanWorkspaceDecisionSummaryUi();
    });
  }

  const redoBtn = getScanWorkspaceInput("scanWorkspaceRedoBtn");
  if (redoBtn && redoBtn.dataset.bound !== "true") {
    redoBtn.dataset.bound = "true";
    redoBtn.addEventListener("click", () => {
      flashScanWorkspaceActionButton(redoBtn);
      redoScanWorkspaceDecisionChange();
      updateScanWorkspaceDecisionSummaryUi();
    });
  }

  const previewScroller = getScanWorkspaceInput("scanWorkspaceLiveDraftPreview");
  if (previewScroller && previewScroller.dataset.scanPreviewTargetBound !== "true") {
    previewScroller.dataset.scanPreviewTargetBound = "true";

    previewScroller.addEventListener("click", (event) => {
      const target =
        event.target instanceof Element
          ? event.target.closest("[data-scan-preview-marker]")
          : null;

      if (!target) return;

      const markerId = String(target.dataset.scanPreviewMarker || "").trim();
      if (!markerId) return;

      event.preventDefault();
      openScanWorkspaceSuggestionPopover(markerId);
    });

    previewScroller.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" && event.key !== " ") return;

      const target =
        event.target instanceof Element
          ? event.target.closest("[data-scan-preview-marker]")
          : null;

      if (!target) return;

      const markerId = String(target.dataset.scanPreviewMarker || "").trim();
      if (!markerId) return;

      event.preventDefault();
      openScanWorkspaceSuggestionPopover(markerId);
    });

    previewScroller.addEventListener("scroll", () => {
      const marker = getScanWorkspaceAnnotationMarkerById(
        scanWorkspaceAnnotationState.activeMarkerId
      );
      const popover = getScanWorkspaceInput("scanWorkspaceSuggestionPopover");

      if (!marker || !popover || popover.classList.contains("hidden")) return;

      positionScanWorkspaceSuggestionPopover(marker);
    });
  }

  renderScanWorkspaceAnnotationShell();

  if (window.scanWorkspaceViewportBound !== true) {
    window.scanWorkspaceViewportBound = true;

    window.addEventListener("resize", () => {
      const marker = getScanWorkspaceAnnotationMarkerById(
        scanWorkspaceAnnotationState.activeMarkerId
      );
      const popover = getScanWorkspaceInput("scanWorkspaceSuggestionPopover");

      if (!marker || !popover || popover.classList.contains("hidden")) return;

      positionScanWorkspaceSuggestionPopover(marker);
    });

    window.addEventListener("scroll", () => {
      const marker = getScanWorkspaceAnnotationMarkerById(
        scanWorkspaceAnnotationState.activeMarkerId
      );
      const popover = getScanWorkspaceInput("scanWorkspaceSuggestionPopover");

      if (!marker || !popover || popover.classList.contains("hidden")) return;

      positionScanWorkspaceSuggestionPopover(marker);
    }, { passive: true });

    window.addEventListener("scan-workspace-split-resize-start", () => {
      closeScanWorkspaceSuggestionPopover();
    });
  }
}

function buildScanWorkspaceCompareSummaryHtml() {
  const counts = getScanWorkspaceAnnotationDecisionCounts();
  const linkedAcceptedIds = getEffectiveAcceptedCompareCandidateIds();
  const manualEditCount = Object.keys(getScanWorkspaceManualBulletEdits()).length;
  const unresolvedGuidanceCount = getScanWorkspaceUnresolvedGuidanceCount();
  const scorePreview = scanWorkspacePreviewState.scorePreviewPayload || {};
  const deltaPoints = Number(scorePreview?.delta_points);
  const changedBulletCount = Number(
    scorePreview?.changed_bullet_keys?.length ||
    scanWorkspacePreviewState.draftFragmentsPayload?.changed_bullet_keys?.length ||
    scanWorkspaceCompareState.afterPayload?.workspace_patch_count ||
    0
  );

  const cards = [
    { label: "Accepted", value: String(counts.accepted) },
    { label: "Manual edits", value: String(manualEditCount) },
    { label: "Rejected", value: String(counts.rejected) },
    { label: "Unresolved", value: String(unresolvedGuidanceCount) },
    {
      label: "Score delta",
      value: Number.isFinite(deltaPoints) && deltaPoints !== 0
        ? `${deltaPoints > 0 ? "+" : ""}${Math.round(deltaPoints)}`
        : "0",
    },
    { label: "Changed bullets", value: String(changedBulletCount || linkedAcceptedIds.length + manualEditCount) },
  ];

  return cards
    .map(
      (item) => `
        <div class="scan-workspace-compare-summary-card">
          <div class="scan-workspace-compare-summary-label">${scanWorkspaceEscapeHtml(item.label)}</div>
          <div class="scan-workspace-compare-summary-value">${scanWorkspaceEscapeHtml(item.value)}</div>
        </div>
      `
    )
    .join("");
}

function getScanWorkspaceCompareScorePoints(kind) {
  const scorePreview = scanWorkspacePreviewState.scorePreviewPayload || {};
  const preload = getScanWorkspacePreloadPayloadForSurface() || {};
  const preloadScorePreview = preload?.score_preview && typeof preload.score_preview === "object"
    ? preload.score_preview
    : {};
  const loadedScanScore = getScanWorkspaceLoadedScanScorePoints();
  const displayedScore = getScanWorkspaceDisplayedScorePoints();

  const values =
    kind === "after"
      ? [
          scorePreview.projected_score_points,
          scorePreview.projected_score,
          displayedScore,
          loadedScanScore,
          preloadScorePreview.projected_score_points,
          preloadScorePreview.projected_score,
        ]
      : [
          loadedScanScore,
          preloadScorePreview.original_score_points,
          preloadScorePreview.original_score,
          scorePreview.original_score_points,
          scorePreview.original_score,
        ];

  for (const value of values) {
    const points = coerceScanWorkspaceScore100(value);
    if (points !== null) return points;
  }
  return null;
}

function renderScanWorkspaceCompareScoreBadge(kind, score) {
  const safeKind = kind === "after" ? "after" : "before";
  const safeScore = Number.isFinite(Number(score)) ? Math.round(Number(score)) : null;
  const label = safeKind === "after"
    ? "Score with AI changes"
    : "Baseline score";

  if (safeScore === null) {
    return `
      <span class="scan-workspace-compare-score-badge scan-workspace-compare-score-badge--${safeKind}">
        <span class="scan-workspace-compare-score-value">--</span>
        <span class="scan-workspace-compare-score-label">${scanWorkspaceEscapeHtml(label)}</span>
      </span>
    `;
  }

  return `
    <span class="scan-workspace-compare-score-badge scan-workspace-compare-score-badge--${safeKind}">
      <span class="scan-workspace-compare-score-value">${scanWorkspaceEscapeHtml(String(safeScore))}</span>
      <span class="scan-workspace-compare-score-label">${scanWorkspaceEscapeHtml(label)}: ${safeScore}%</span>
    </span>
  `;
}

function getScanWorkspaceCompareRemovedTexts() {
  const acceptedTexts = scanWorkspaceAnnotationState.markers
    .filter((marker) => normalizeScanWorkspaceAnnotationDecision(marker?.decision) === "accepted")
    .flatMap((marker) => [
      marker?.originalText,
      marker?.anchorText,
    ]);
  const fragmentTexts = Array.isArray(scanWorkspacePreviewState.draftFragmentsPayload?.changed_bullets)
    ? scanWorkspacePreviewState.draftFragmentsPayload.changed_bullets.flatMap((fragment) => [
        fragment?.original_text,
        fragment?.source_raw_text,
      ])
    : [];
  const manualEditTexts = Object.keys(getScanWorkspaceManualBulletEdits())
    .map((key) => key.startsWith("text:") ? key.slice(5) : "");

  return Array.from(new Set([
    ...acceptedTexts,
    ...fragmentTexts,
    ...manualEditTexts,
  ].filter((text) => String(text || "").trim())));
}

function getScanWorkspaceCompareChangedPositions(preview) {
  const pages = normalizeScanWorkspacePreviewPages(preview);
  const positions = [];

  pages.forEach((page, pageIndex) => {
    const rows = Array.isArray(page.presentation_rows) ? page.presentation_rows : [];
    rows.forEach((row, rowIndex) => {
      if (row?.patched) positions.push(`${page.page_index ?? pageIndex}:${rowIndex}`);
    });
  });

  return positions;
}

function renderScanWorkspaceCompareShell() {
  const summary = getScanWorkspaceInput("scanWorkspaceCompareSummary");
  const status = getScanWorkspaceInput("scanWorkspaceCompareStatus");
  const beforeMeta = getScanWorkspaceInput("scanWorkspaceCompareBeforeMeta");
  const afterMeta = getScanWorkspaceInput("scanWorkspaceCompareAfterMeta");
  const beforePane = getScanWorkspaceInput("scanWorkspaceCompareBeforePane");
  const afterPane = getScanWorkspaceInput("scanWorkspaceCompareAfterPane");

  if (!summary || !status || !beforeMeta || !afterMeta || !beforePane || !afterPane) return;

  const acceptedIds = getEffectiveAcceptedCompareCandidateIds();
  const hasDraftChanges = hasScanWorkspaceCurrentDraftChanges();
  const beforeScore = getScanWorkspaceCompareScorePoints("before");
  const afterScore = hasDraftChanges
    ? getScanWorkspaceCompareScorePoints("after")
    : null;
  const removedTexts = getScanWorkspaceCompareRemovedTexts();
  const removedPositions = hasDraftChanges
    ? getScanWorkspaceCompareChangedPositions(scanWorkspaceCompareState.afterPayload)
    : [];
  summary.innerHTML = buildScanWorkspaceCompareSummaryHtml();

  status.textContent = scanWorkspaceCompareState.isLoading
    ? "Refreshing compare surfaces..."
    : hasDraftChanges
      ? "Comparing the baseline draft against the current accepted and manual draft state."
      : "Compare the baseline draft against the current accepted AI decision set.";

  beforeMeta.innerHTML = `
    ${renderScanWorkspaceCompareScoreBadge("before", beforeScore)}
  `;

  beforePane.innerHTML = renderScanWorkspaceDocumentMirrorFromPayload(
    scanWorkspaceCompareState.beforePayload,
    {
      isLoading: scanWorkspaceCompareState.isLoading,
      emptyMessage: "Baseline compare preview is not available for this scan.",
      noteText: "",
      compareSide: "before",
      removedTexts,
      removedPositions,
    }
  );

  if (!hasDraftChanges) {
    afterMeta.innerHTML = `
      ${renderScanWorkspaceCompareScoreBadge("after", afterScore)}
    `;
    afterPane.innerHTML = `
      <div class="tailoring-empty-state">
        Accept a suggestion or save a manual edit to generate the after preview.
      </div>
    `;
    return;
  }

  afterMeta.innerHTML = `
    ${renderScanWorkspaceCompareScoreBadge("after", afterScore)}
  `;

  afterPane.innerHTML = renderScanWorkspaceDocumentMirrorFromPayload(
    scanWorkspaceCompareState.afterPayload,
    {
      isLoading: scanWorkspaceCompareState.isLoading,
      emptyMessage: "After compare preview is not available for this scan.",
      noteText: "",
      compareSide: "after",
    }
  );
}

async function ensureScanWorkspaceCompareLoaded({ force = false } = {}) {
  const acceptedIds = getEffectiveAcceptedCompareCandidateIds();
  const acceptedSignature = getScanWorkspaceDraftPreviewSignature(acceptedIds);
  const hasDraftChanges = hasScanWorkspaceCurrentDraftChanges();

  if (
    !force &&
    scanWorkspaceCompareState.beforePayload &&
    scanWorkspaceCompareState.acceptedSignature === acceptedSignature &&
    (!hasDraftChanges || scanWorkspaceCompareState.afterPayload)
  ) {
    renderScanWorkspaceCompareShell();
    return;
  }

  scanWorkspaceCompareState.isLoading = true;
  scanWorkspaceCompareState.acceptedSignature = acceptedSignature;
  renderScanWorkspaceCompareShell();

  const requestSeq = ++scanWorkspaceCompareState.requestSeq;

  if (force || !scanWorkspacePreviewState.scorePreviewPayload) {
    await refreshScanWorkspaceScorePreview();
    if (requestSeq !== scanWorkspaceCompareState.requestSeq) return;
    renderScanWorkspaceCompareShell();
  }

  const [beforePayload, afterPayload] = await Promise.all([
    requestScanWorkspaceDocumentPreview([], { manualBulletEdits: {} }),
    hasDraftChanges
      ? requestScanWorkspaceDocumentPreview(acceptedIds)
      : Promise.resolve(null),
  ]);

  if (requestSeq !== scanWorkspaceCompareState.requestSeq) return;

  scanWorkspaceCompareState.beforePayload = beforePayload;
  scanWorkspaceCompareState.afterPayload = afterPayload;
  scanWorkspaceCompareState.isLoading = false;
  renderScanWorkspaceCompareShell();
}

function bindScanWorkspaceCompareShell() {
  const refreshBtn = getScanWorkspaceInput("scanWorkspaceCompareRefreshBtn");
  if (refreshBtn && refreshBtn.dataset.bound !== "true") {
    refreshBtn.dataset.bound = "true";
    refreshBtn.addEventListener("click", () => {
      ensureScanWorkspaceCompareLoaded({ force: true });
    });
  }

  const previewBtn = getScanWorkspaceInput("scanWorkspacePreviewBtn");
  if (previewBtn && previewBtn.dataset.bound !== "true") {
    previewBtn.dataset.bound = "true";
    previewBtn.addEventListener("click", async () => {
      setScanWorkspaceMode("compare");
      await ensureScanWorkspaceCompareLoaded({ force: true });
    });
  }

  renderScanWorkspaceCompareShell();
}

function openScanWorkspaceContinueModal() {
  const modal = getScanWorkspaceInput("scanWorkspaceContinueModal");
  if (!modal) return;
  modal.classList.remove("hidden");
  document.body.classList.add("scan-workspace-modal-open");

  const primary = getScanWorkspaceInput("scanWorkspaceContinueToEditBtn");
  if (primary) {
    window.setTimeout(() => primary.focus(), 0);
  }
}

function closeScanWorkspaceContinueModal() {
  const modal = getScanWorkspaceInput("scanWorkspaceContinueModal");
  if (!modal) return;
  modal.classList.add("hidden");
  document.body.classList.remove("scan-workspace-modal-open");
}

async function continueScanWorkspaceAfterReview() {
  const saved = await saveScanWorkspaceDraftState();
  if (saved) {
    openScanWorkspaceContinueModal();
  }
}

function bindScanWorkspacePersistenceControls() {
  const saveBtn = getScanWorkspaceInput("scanWorkspaceSaveBtn");
  if (saveBtn && saveBtn.dataset.bound !== "true") {
    saveBtn.dataset.bound = "true";
    saveBtn.addEventListener("click", async () => {
      await continueScanWorkspaceAfterReview();
    });
  }

  const continueModal = getScanWorkspaceInput("scanWorkspaceContinueModal");
  if (continueModal && continueModal.dataset.bound !== "true") {
    continueModal.dataset.bound = "true";
    continueModal.addEventListener("click", (event) => {
      const closeTarget = event.target instanceof Element
        ? event.target.closest("[data-scan-continue-close]")
        : null;
      if (closeTarget) closeScanWorkspaceContinueModal();
    });
  }

  const continueCloseBtn = getScanWorkspaceInput("scanWorkspaceContinueModalCloseBtn");
  if (continueCloseBtn && continueCloseBtn.dataset.bound !== "true") {
    continueCloseBtn.dataset.bound = "true";
    continueCloseBtn.addEventListener("click", closeScanWorkspaceContinueModal);
  }

  const continueToEditBtn = getScanWorkspaceInput("scanWorkspaceContinueToEditBtn");
  if (continueToEditBtn && continueToEditBtn.dataset.bound !== "true") {
    continueToEditBtn.dataset.bound = "true";
    continueToEditBtn.addEventListener("click", () => {
      closeScanWorkspaceContinueModal();
      setScanWorkspaceMode("review");
      ensureScanWorkspaceDocumentPreviewLoaded({ force: false });
    });
  }

  const continueDownloadBtn = getScanWorkspaceInput("scanWorkspaceContinueDownloadBtn");
  if (continueDownloadBtn && continueDownloadBtn.dataset.bound !== "true") {
    continueDownloadBtn.dataset.bound = "true";
    continueDownloadBtn.addEventListener("click", async () => {
      await exportScanWorkspaceDraft("pdf");
    });
  }

  const exportBtn = getScanWorkspaceInput("scanWorkspaceExportBtn");
  if (exportBtn && exportBtn.dataset.bound !== "true") {
    exportBtn.dataset.bound = "true";
    exportBtn.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      toggleScanWorkspaceExportMenu();
    });
  }

  const exportMenu = getScanWorkspaceInput("scanWorkspaceExportMenu");
  if (exportMenu && exportMenu.dataset.bound !== "true") {
    exportMenu.dataset.bound = "true";
    exportMenu.addEventListener("click", async (event) => {
      event.stopPropagation();
      const option = event.target instanceof Element
        ? event.target.closest("[data-scan-export-format]")
        : null;
      if (!option) return;

      const format = String(option.dataset.scanExportFormat || "pdf").trim();
      closeScanWorkspaceExportMenu();
      await exportScanWorkspaceDraft(format);
    });
  }

  const rescanBtn = getScanWorkspaceInput("scanWorkspaceRescanBtn");
  if (rescanBtn && rescanBtn.dataset.bound !== "true") {
    rescanBtn.dataset.bound = "true";
    rescanBtn.addEventListener("click", async () => {
      await openSavedScanRescanDraft();
    });
  }

  renderScanWorkspacePersistenceStatus();
}

function maybeWarnBeforeUnload(event) {
  const context = getScanWorkspaceContext();
  const hasContext = Boolean(getScanWorkspaceArtifactKey(context) && context?.resumeName);
  const currentSignature = getCurrentScanWorkspacePersistenceSignature();
  const savedSignature = scanWorkspacePersistenceState.hydratedSignature || "";
  const isDirty = Boolean(hasContext && currentSignature !== savedSignature);

  if (!isDirty || scanWorkspacePersistenceState.isSaving) {
    return;
  }

  event.preventDefault();
  event.returnValue = "";
}

function bindScanWorkspaceGlobalShortcuts() {
  if (document.body.dataset.scanWorkspaceGlobalBound === "true") return;
  document.body.dataset.scanWorkspaceGlobalBound = "true";

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeScanWorkspaceSuggestionPopover();
      closeScanWorkspaceExportMenu();
      closeScanWorkspaceContinueModal();
    }
  });

  document.addEventListener("click", (event) => {
    const exportMenu = getScanWorkspaceInput("scanWorkspaceExportMenu");
    const exportWrap =
      event.target instanceof Element &&
      event.target.closest(".scan-workspace-export-menu-wrap");
    if (exportMenu && !exportMenu.classList.contains("hidden") && !exportWrap) {
      closeScanWorkspaceExportMenu();
    }

    const popover = getScanWorkspaceInput("scanWorkspaceSuggestionPopover");
    if (!popover || popover.classList.contains("hidden")) return;

    const eventPath = typeof event.composedPath === "function"
      ? event.composedPath()
      : [];
    const clickedInsidePopover =
      eventPath.includes(popover) ||
      (event.target instanceof Element && event.target.closest("#scanWorkspaceSuggestionPopover"));
    const clickedMarker =
      event.target instanceof Element &&
      event.target.closest("[data-scan-annotation-marker]");

    const clickedPreviewTarget =
      event.target instanceof Element &&
      event.target.closest("[data-scan-preview-marker]");

    if (!clickedInsidePopover && !clickedMarker && !clickedPreviewTarget) {
      closeScanWorkspaceSuggestionPopover();
    }
  });

  window.addEventListener("beforeunload", maybeWarnBeforeUnload);
}

window.addEventListener("DOMContentLoaded", () => {
  const root = getScanWorkspacePageRoot();
  if (!root) return;

  bindScanWorkspaceModeButtons();
  bindScanWorkspaceIntakeForm();
  bindScanWorkspaceProcessingShell();
  bindScanWorkspaceAnnotationShell();
  bindScanWorkspaceCompareShell();
  bindScanWorkspacePersistenceControls();
  bindScanWorkspaceGlobalShortcuts();
  updateScanWorkspaceProcessingView();
  loadScanWorkspaceSavedResumes();

  setScanWorkspaceMode(getScanWorkspaceInitialMode());
  loadSavedScanWorkspaceReviewPayload();
  loadScanWorkspaceDraftState();

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
    renderLiveDraftPreview: () => renderScanWorkspaceLiveDraftPreviewInto(),
    refreshCompare: () => ensureScanWorkspaceCompareLoaded({ force: true }),
    setAnnotationMarkers: (markers) => {
      setScanWorkspaceAnnotationMarkers(markers);
    },
    focusCandidateId: (candidateId) => {
      return focusScanWorkspacePreviewTargetForCandidateId(candidateId);
    },
    clearAnnotationMarkers: () => {
      setScanWorkspaceAnnotationMarkers([]);
    },
    saveDraftState: () => saveScanWorkspaceDraftState(),
    reloadDraftState: () => loadScanWorkspaceDraftState(),
    renderPersistenceStatus: () => renderScanWorkspacePersistenceStatus(),
    getCurrentExcludedIssueIds: () => getScanWorkspacePersistenceExcludedIssueIds(),
    getSavedExcludedIssueIds: () => getSavedScanWorkspaceExcludedIssueIds(),
    getSavedPersonalDetails: () => getSavedScanWorkspacePersonalDetails(),
    getAnnotationState: () => ({
      markers: scanWorkspaceAnnotationState.markers.map((marker) => ({ ...marker })),
      activeMarkerId: scanWorkspaceAnnotationState.activeMarkerId,
      counts: getScanWorkspaceAnnotationDecisionCounts(),
      acceptedCandidateIds: getEffectiveAcceptedCompareCandidateIds(),
    }),
  };
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
