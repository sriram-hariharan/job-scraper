function onboardingQs(id) {
  return document.getElementById(id);
}

function splitPreferenceList(value) {
  return String(value || "")
    .split(/[\n,]/)
    .map((item) => item.trim())
    .filter(Boolean)
    .filter((item, index, items) => items.indexOf(item) === index);
}

function checkedValues(name) {
  return Array.from(document.querySelectorAll(`input[name="${name}"]:checked`))
    .map((input) => String(input.value || "").trim())
    .filter(Boolean);
}

let onboardingRequirementState = {};
let onboardingLocationSelector = null;
let onboardingPreferencesWorkflow = null;
let onboardingPreferencesSaving = false;
const onboardingAiState = {
  settings: null,
  settingsAvailable: false,
  catalog: null,
  credentialProvider: null,
  modalTrigger: null,
  connectionTesting: false,
  preferenceSaving: false,
};

const onboardingAiSafeFailures = {
  credential_not_configured: "No API key is configured for this provider.",
  unsupported_provider: "This provider is not available.",
  unsupported_provider_model: "This model is not available for this provider.",
  invalid_credential: "Enter a valid API key and try again.",
  credential_write_failed: "The API key could not be saved. Try again.",
  settings_write_failed: "The provider preference could not be saved. Try again.",
  connection_test_failed: "Connection test failed. Check the key and provider access.",
};

function setCheckedValues(name, values) {
  const selected = new Set(Array.isArray(values) ? values.map(String) : []);
  document.querySelectorAll(`input[name="${name}"]`).forEach((input) => {
    input.checked = selected.has(String(input.value || ""));
  });
}

function setOnboardingCheckboxGroup(name, checked) {
  document.querySelectorAll(`#onboardingForm input[name="${name}"]`).forEach((input) => {
    input.checked = Boolean(checked);
  });
}

function syncOnboardingSeniorityStrictToggle() {
  const strictToggle = document.querySelector('#onboardingForm input[name="seniority_strict_match"]');
  if (!strictToggle) return;
  const hasSeniority = checkedValues("target_seniority").length > 0;
  strictToggle.disabled = !hasSeniority;
  if (!hasSeniority) strictToggle.checked = false;
}

function updateOnboardingConfigurationSummary() {
  const summary = onboardingQs("onboardingConfigurationSummary");
  if (!summary) return;
  const roleCount = checkedValues("selected_role_families").length;
  const locationCount = onboardingLocationSelector?.serialize().preferred_location_specs.length || 0;
  summary.textContent = `${roleCount} role ${roleCount === 1 ? "family" : "families"} · ${locationCount} preferred location${locationCount === 1 ? "" : "s"}`;
  onboardingPreferencesWorkflow?.update();
}

function setOnboardingChangeState(label, state = "saved") {
  const indicator = onboardingQs("onboardingChangeState");
  if (!indicator) return;
  indicator.textContent = label;
  indicator.className = `preferences-save-state is-${state}`;
  onboardingPreferencesWorkflow?.update();
}

function markOnboardingPreferencesDirty() {
  if (checkedValues("selected_role_families").length) onboardingPreferencesWorkflow?.clearValidationError();
  updateOnboardingConfigurationSummary();
  setOnboardingChangeState("Unsaved changes", "dirty");
}

function setTextareaList(id, values) {
  const input = onboardingQs(id);
  if (!input) return;
  input.value = Array.isArray(values) ? values.join(", ") : "";
}

async function onboardingFetchJson(url, options = {}) {
  const response = await window.fetch(url, {
    credentials: "same-origin",
    headers: {
      Accept: "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(String(payload.detail || `Request failed: ${response.status}`));
  }
  return payload;
}

function collectOnboardingPreferences(onboardingCompleted) {
  syncOnboardingSeniorityStrictToggle();
  const locationPreferences = onboardingLocationSelector?.serialize() || {
    preferred_locations: [],
    preferred_location_specs: [],
    location_strict_match: false,
    location_show_others_if_unmatched: false,
  };
  return {
    onboarding_completed: Boolean(onboardingCompleted),
    selected_role_families: checkedValues("selected_role_families"),
    target_seniority: checkedValues("target_seniority"),
    seniority_strict_match: Boolean(
      document.querySelector('#onboardingForm input[name="seniority_strict_match"]')?.checked
    ),
    ...locationPreferences,
    preferred_skills: splitPreferenceList(onboardingQs("preferredSkillsInput")?.value),
    excluded_keywords: splitPreferenceList(onboardingQs("excludedKeywordsInput")?.value),
  };
}

function renderRequirementStatus(requirements) {
  onboardingRequirementState = {
    ...onboardingRequirementState,
    ...(requirements || {}),
  };
  const resumeStatus = onboardingQs("onboardingResumeStatus");
  const resumePanel = onboardingQs("onboardingResumePanel");
  const saveStatus = onboardingQs("onboardingSaveStatus");
  const completeBtn = onboardingQs("onboardingCompleteBtn");

  const profileResumeCount = Number(onboardingRequirementState.profile_resume_count || 0);
  const hasResume = Boolean(onboardingRequirementState.has_profile_resume);
  const selectedRoleCount = checkedValues("selected_role_families").length;
  const canComplete = hasResume && selectedRoleCount > 0;

  if (resumeStatus) {
    resumeStatus.textContent = hasResume
      ? (profileResumeCount > 0
        ? `${profileResumeCount} resume${profileResumeCount === 1 ? "" : "s"} ready`
        : "Ready")
      : "Resume required";
  }

  if (resumePanel) {
    resumePanel.classList.toggle("is-complete", hasResume);
  }

  if (saveStatus) {
    if (canComplete) {
      saveStatus.textContent = "Ready to complete onboarding.";
    } else if (!selectedRoleCount && !hasResume) {
      saveStatus.textContent = "Select at least one role family and add a profile resume.";
    } else if (!selectedRoleCount) {
      saveStatus.textContent = "Select at least one role family.";
    } else {
      saveStatus.textContent = "Add at least one profile resume before completing onboarding.";
    }
  }

  if (completeBtn) {
    completeBtn.disabled = !canComplete;
  }
}

function hydrateOnboardingForm(preferences) {
  setCheckedValues("selected_role_families", preferences?.selected_role_families || []);
  setCheckedValues("target_seniority", preferences?.target_seniority || []);
  const strictToggle = document.querySelector('#onboardingForm input[name="seniority_strict_match"]');
  if (strictToggle) strictToggle.checked = preferences?.seniority_strict_match === true;
  syncOnboardingSeniorityStrictToggle();
  onboardingLocationSelector?.setPreferences(preferences || {});
  setTextareaList("preferredSkillsInput", preferences?.preferred_skills || []);
  setTextareaList("excludedKeywordsInput", preferences?.excluded_keywords || []);
}

async function loadOnboardingPreferences() {
  const saveStatus = onboardingQs("onboardingSaveStatus");
  try {
    const payload = await onboardingFetchJson("/onboarding/preferences");
    hydrateOnboardingForm(payload.preferences || {});
    renderRequirementStatus(payload.requirements || {});
    updateOnboardingConfigurationSummary();
    setOnboardingChangeState("All changes saved", "saved");
  } catch (error) {
    if (saveStatus) {
      saveStatus.textContent = `Could not load onboarding preferences. ${error.message}`;
    }
    setOnboardingChangeState("Load failed", "error");
  }
}

async function saveOnboardingPreferences(onboardingCompleted) {
  const saveStatus = onboardingQs("onboardingSaveStatus");
  const completeBtn = onboardingQs("onboardingCompleteBtn");
  const draftBtn = onboardingQs("onboardingSaveDraftBtn");

  if (onboardingPreferencesSaving) return;
  const preferences = collectOnboardingPreferences(onboardingCompleted);
  if (onboardingCompleted && preferences.selected_role_families.length === 0) {
    onboardingPreferencesWorkflow?.showValidationError("Select at least one role family before completing onboarding.", 0);
    renderRequirementStatus({});
    return;
  }
  onboardingPreferencesWorkflow?.clearValidationError();
  onboardingPreferencesSaving = true;

  if (completeBtn) completeBtn.disabled = true;
  if (draftBtn) draftBtn.disabled = true;
  if (saveStatus) saveStatus.textContent = onboardingCompleted ? "Completing onboarding..." : "Saving preferences...";
  setOnboardingChangeState("Saving...", "saving");

  try {
    const payload = await onboardingFetchJson("/onboarding/preferences", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(preferences),
    });
    renderRequirementStatus(payload.requirements || {});
    if (saveStatus) {
      saveStatus.textContent = onboardingCompleted ? "Onboarding complete. Opening dashboard..." : "Preferences saved.";
    }
    setOnboardingChangeState("All changes saved", "saved");
    if (onboardingCompleted) {
      window.location.href = "/";
    }
  } catch (error) {
    if (saveStatus) saveStatus.textContent = error.message;
    setOnboardingChangeState("Save failed", "error");
    renderRequirementStatus({});
  } finally {
    onboardingPreferencesSaving = false;
    if (draftBtn) draftBtn.disabled = false;
    renderRequirementStatus({});
  }
}

function setOnboardingAiHidden(element, hidden) {
  if (element) element.classList.toggle("hidden", hidden);
}

function setOnboardingAiMessage(element, message, tone = "") {
  if (!element) return;
  element.textContent = String(message || "");
  element.className = "onboarding-ai-inline-status";
  if (tone) element.classList.add(`is-${tone}`);
  element.classList.toggle("hidden", !message);
}

function displayOnboardingAiProvider(provider) {
  const normalized = String(provider || "").trim().toLowerCase();
  if (normalized === "openai") return "OpenAI";
  if (normalized === "groq") return "Groq";
  return normalized;
}

function onboardingAiSafeProjection() {
  if (!onboardingAiState.settingsAvailable || !onboardingAiState.settings) {
    return {
      available: false,
      reviewStatus: "AI status unavailable",
      preferred: "None",
      configured: "None",
      summary: "AI status unavailable",
    };
  }

  const preferred = onboardingAiState.settings.preferredProvider;
  const configuredProviders = Object.entries(onboardingAiState.settings.providers)
    .filter(([, providerState]) => providerState.configured)
    .map(([provider]) => displayOnboardingAiProvider(provider));
  const preferredLabel = preferred ? displayOnboardingAiProvider(preferred) : "None";
  const configuredLabel = configuredProviders.length ? configuredProviders.join(", ") : "None";
  const hasConfiguration = Boolean(preferred || configuredProviders.length);
  let summary = "AI not configured";
  if (hasConfiguration) {
    summary = preferred
      ? `Preferred: ${preferredLabel} · Configured: ${configuredLabel}`
      : `No preferred provider · Configured: ${configuredLabel}`;
  }
  return {
    available: true,
    reviewStatus: hasConfiguration ? "AI settings ready" : "AI not configured",
    preferred: preferredLabel,
    configured: configuredLabel,
    summary,
  };
}

function updateOnboardingAiSafeProjection() {
  const projection = onboardingAiSafeProjection();
  document.querySelectorAll("[data-onboarding-ai-summary]").forEach((node) => {
    node.textContent = projection.summary;
  });
  document.querySelectorAll("[data-onboarding-ai-review-status]").forEach((node) => {
    node.textContent = projection.reviewStatus;
  });
  document.querySelectorAll("[data-onboarding-ai-review-details]").forEach((node) => {
    node.hidden = !projection.available;
  });
  document.querySelectorAll("[data-onboarding-ai-review-preferred]").forEach((node) => {
    node.textContent = projection.preferred;
  });
  document.querySelectorAll("[data-onboarding-ai-review-configured]").forEach((node) => {
    node.textContent = projection.configured;
  });
}

function extractOnboardingAiErrorCategory(payload) {
  const detail = payload && typeof payload.detail === "object" ? payload.detail : null;
  return detail && typeof detail.error_category === "string"
    ? detail.error_category
    : "request_failed";
}

async function onboardingAiRequestJson(url, options = {}) {
  const response = await window.fetch(url, {
    ...options,
    credentials: "same-origin",
    headers: {
      Accept: "application/json",
      ...(options.headers || {}),
    },
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error("AI settings request failed");
    error.category = extractOnboardingAiErrorCategory(payload);
    throw error;
  }
  return payload;
}

function validateOnboardingAiSettings(payload) {
  if (!payload || payload.ok !== true || !payload.providers || Array.isArray(payload.providers)) {
    throw new Error("Invalid AI settings response");
  }
  const preferredProvider = payload.preferred_provider;
  if (preferredProvider !== null && typeof preferredProvider !== "string") {
    throw new Error("Invalid preferred provider response");
  }
  const providers = {};
  Object.entries(payload.providers).forEach(([provider, value]) => {
    if (!provider || !value || typeof value !== "object") {
      throw new Error("Invalid provider settings response");
    }
    providers[provider] = {
      configured: value.configured === true,
      credentialHint: typeof value.credential_hint === "string" ? value.credential_hint : "",
    };
  });
  return { preferredProvider, providers };
}

function validateOnboardingAiCatalog(payload) {
  if (!payload || payload.ok !== true || !Array.isArray(payload.providers)) {
    throw new Error("Invalid AI provider catalog response");
  }
  const providers = payload.providers.map((entry) => {
    if (!entry || typeof entry.provider !== "string" || !entry.provider || !Array.isArray(entry.models)) {
      throw new Error("Invalid AI provider catalog entry");
    }
    return {
      provider: entry.provider,
      models: entry.models.map((model) => {
        if (!model || typeof model.model_id !== "string" || !model.model_id) {
          throw new Error("Invalid AI model catalog entry");
        }
        return { modelId: model.model_id };
      }),
    };
  });
  if (!providers.length) throw new Error("Empty AI provider catalog response");
  return { providers };
}

function onboardingAiProviderSettings(provider) {
  return onboardingAiState.settings?.providers?.[provider] || {
    configured: false,
    credentialHint: "",
  };
}

function onboardingAiCatalogProvider(provider) {
  return onboardingAiState.catalog?.providers?.find((entry) => entry.provider === provider) || null;
}

function onboardingAiElement(tagName, className, text) {
  const element = document.createElement(tagName);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}

function onboardingAiProviderMark(provider) {
  const mark = onboardingAiElement("span", "onboarding-ai-provider-mark");
  mark.setAttribute("aria-hidden", "true");
  if (provider === "openai") {
    const logo = onboardingAiElement("img", "onboarding-ai-provider-logo");
    logo.src = "/static/media/openai_provider_logo.svg";
    logo.alt = "";
    mark.appendChild(logo);
  } else {
    mark.appendChild(onboardingAiElement("span", "onboarding-ai-provider-wordmark", displayOnboardingAiProvider(provider)));
  }
  return mark;
}

function onboardingAiGuidance(provider) {
  const template = onboardingQs(`providerKeyGuidanceTemplate-${provider}`);
  return template instanceof HTMLTemplateElement
    ? template.content.cloneNode(true)
    : document.createDocumentFragment();
}

function renderOnboardingAiProviderCards() {
  const grid = onboardingQs("onboardingAiProviderGrid");
  if (!grid || !onboardingAiState.catalog || !onboardingAiState.settings) return;
  grid.replaceChildren();
  onboardingAiState.catalog.providers.forEach((catalogEntry) => {
    const provider = catalogEntry.provider;
    const providerState = onboardingAiProviderSettings(provider);
    const card = onboardingAiElement("article", "onboarding-ai-provider-card");
    card.dataset.provider = provider;

    const heading = onboardingAiElement("div", "onboarding-ai-provider-heading");
    const identity = onboardingAiElement("div", "onboarding-ai-provider-identity");
    const identityText = onboardingAiElement("div");
    identityText.appendChild(onboardingAiElement("h3", "", displayOnboardingAiProvider(provider)));
    identityText.appendChild(onboardingAiElement(
      "span",
      "onboarding-ai-model-count",
      `${catalogEntry.models.length} available ${catalogEntry.models.length === 1 ? "model" : "models"}`
    ));
    identity.append(onboardingAiProviderMark(provider), identityText);

    const badges = onboardingAiElement("div", "onboarding-ai-provider-badges");
    badges.appendChild(onboardingAiElement(
      "span",
      `onboarding-ai-status-badge ${providerState.configured ? "is-configured" : "is-unconfigured"}`,
      providerState.configured ? "Configured" : "Not configured"
    ));
    if (onboardingAiState.settings.preferredProvider === provider) {
      badges.appendChild(onboardingAiElement("span", "onboarding-ai-preferred-badge", "Preferred"));
    }
    heading.append(identity, badges);

    const detail = onboardingAiElement("div", "onboarding-ai-provider-detail");
    if (providerState.configured) {
      const hint = onboardingAiElement("span", "onboarding-ai-credential-hint", providerState.credentialHint);
      hint.setAttribute("aria-label", "Stored credential hint");
      detail.appendChild(hint);
    } else {
      detail.appendChild(onboardingAiElement("span", "", "Add an API key when you are ready."));
    }

    const actions = onboardingAiElement("div", "onboarding-ai-provider-actions");
    const credentialButton = onboardingAiElement(
      "button",
      "preferences-utility-button onboarding-ai-primary-button",
      providerState.configured ? "Replace key" : "Add API key"
    );
    credentialButton.type = "button";
    credentialButton.dataset.onboardingAiCredential = provider;
    actions.appendChild(credentialButton);

    const preferredButton = onboardingAiElement(
      "button",
      "preferences-utility-button",
      onboardingAiState.settings.preferredProvider === provider ? "Preferred" : "Set as preferred"
    );
    preferredButton.type = "button";
    preferredButton.dataset.onboardingAiPreferred = provider;
    preferredButton.disabled = onboardingAiState.settings.preferredProvider === provider;
    actions.appendChild(preferredButton);
    if (onboardingAiState.settings.preferredProvider === provider) {
      const clearButton = onboardingAiElement(
        "button",
        "preferences-utility-button onboarding-ai-clear-preference",
        "Clear preference"
      );
      clearButton.type = "button";
      clearButton.dataset.onboardingAiClearPreferred = provider;
      actions.appendChild(clearButton);
    }

    const status = onboardingAiElement("p", "onboarding-ai-inline-status hidden");
    status.dataset.onboardingAiProviderStatus = provider;
    status.setAttribute("role", "status");
    status.setAttribute("aria-live", "polite");

    card.append(heading, detail, onboardingAiGuidance(provider), actions, status);
    grid.appendChild(card);
  });
}

function renderOnboardingAiConnectionSelectors() {
  const providerSelect = onboardingQs("onboardingAiTestProvider");
  if (!providerSelect || !onboardingAiState.catalog) return;
  const previousProvider = providerSelect.value;
  providerSelect.replaceChildren();
  onboardingAiState.catalog.providers.forEach((entry) => {
    const option = onboardingAiElement("option", "", displayOnboardingAiProvider(entry.provider));
    option.value = entry.provider;
    providerSelect.appendChild(option);
  });
  const preferred = onboardingAiState.settings?.preferredProvider;
  if (onboardingAiCatalogProvider(previousProvider)) providerSelect.value = previousProvider;
  else if (onboardingAiCatalogProvider(preferred)) providerSelect.value = preferred;
  renderOnboardingAiConnectionModels();
}

function renderOnboardingAiConnectionModels() {
  const provider = onboardingQs("onboardingAiTestProvider")?.value;
  const modelSelect = onboardingQs("onboardingAiTestModel");
  if (!modelSelect) return;
  const previousModel = modelSelect.value;
  const catalogEntry = onboardingAiCatalogProvider(provider);
  modelSelect.replaceChildren();
  (catalogEntry?.models || []).forEach((model) => {
    const option = onboardingAiElement("option", "", model.modelId);
    option.value = model.modelId;
    modelSelect.appendChild(option);
  });
  if (catalogEntry?.models.some((model) => model.modelId === previousModel)) {
    modelSelect.value = previousModel;
  }
  updateOnboardingAiTestButton();
}

function updateOnboardingAiTestButton() {
  const provider = onboardingQs("onboardingAiTestProvider")?.value;
  const model = onboardingQs("onboardingAiTestModel")?.value;
  const button = onboardingQs("onboardingAiTestBtn");
  if (!button) return;
  button.disabled = !onboardingAiProviderSettings(provider).configured
    || !model
    || onboardingAiState.connectionTesting;
  button.textContent = onboardingAiState.connectionTesting ? "Testing…" : "Test connection";
}

function renderOnboardingAi() {
  renderOnboardingAiProviderCards();
  renderOnboardingAiConnectionSelectors();
  updateOnboardingAiSafeProjection();
}

async function loadOnboardingAiSettings() {
  onboardingAiState.settingsAvailable = false;
  onboardingAiState.settings = null;
  updateOnboardingAiSafeProjection();
  setOnboardingAiHidden(onboardingQs("onboardingAiLoading"), false);
  setOnboardingAiHidden(onboardingQs("onboardingAiLoadError"), true);
  setOnboardingAiHidden(onboardingQs("onboardingAiContent"), true);
  try {
    const [settingsPayload, catalogPayload] = await Promise.all([
      onboardingAiRequestJson("/ai/settings"),
      onboardingAiRequestJson("/ai/settings/catalog"),
    ]);
    onboardingAiState.settings = validateOnboardingAiSettings(settingsPayload);
    onboardingAiState.settingsAvailable = true;
    onboardingAiState.catalog = validateOnboardingAiCatalog(catalogPayload);
    onboardingAiState.catalog.providers.forEach((entry) => {
      if (!Object.prototype.hasOwnProperty.call(onboardingAiState.settings.providers, entry.provider)) {
        throw new Error("Provider settings do not match catalog");
      }
    });
    renderOnboardingAi();
    setOnboardingAiHidden(onboardingQs("onboardingAiContent"), false);
  } catch (_error) {
    onboardingAiState.settings = null;
    onboardingAiState.settingsAvailable = false;
    updateOnboardingAiSafeProjection();
    setOnboardingAiHidden(onboardingQs("onboardingAiLoadError"), false);
  } finally {
    setOnboardingAiHidden(onboardingQs("onboardingAiLoading"), true);
  }
}

async function refreshOnboardingAiSettings() {
  try {
    onboardingAiState.settings = validateOnboardingAiSettings(
      await onboardingAiRequestJson("/ai/settings")
    );
    onboardingAiState.settingsAvailable = true;
    renderOnboardingAi();
  } catch (error) {
    onboardingAiState.settings = null;
    onboardingAiState.settingsAvailable = false;
    updateOnboardingAiSafeProjection();
    throw error;
  }
}

function setOnboardingAiCredentialVisibility(reveal) {
  const input = onboardingQs("onboardingAiCredentialInput");
  const button = onboardingQs("onboardingAiCredentialVisibilityBtn");
  const showIcon = onboardingQs("onboardingAiCredentialShowIcon");
  const hideIcon = onboardingQs("onboardingAiCredentialHideIcon");
  const label = reveal ? "Hide API key" : "Show API key";
  input.type = reveal ? "text" : "password";
  showIcon.hidden = reveal;
  hideIcon.hidden = !reveal;
  button.setAttribute("aria-label", label);
  button.setAttribute("title", label);
  button.setAttribute("aria-pressed", reveal ? "true" : "false");
}

function openOnboardingAiCredentialModal(provider, trigger) {
  const providerState = onboardingAiProviderSettings(provider);
  onboardingAiState.credentialProvider = provider;
  onboardingAiState.modalTrigger = trigger;
  onboardingQs("onboardingAiCredentialTitle").textContent = providerState.configured
    ? "Replace API key"
    : "Add API key";
  onboardingQs("onboardingAiCredentialSubtitle").textContent = displayOnboardingAiProvider(provider);
  onboardingQs("onboardingAiCredentialInput").value = "";
  setOnboardingAiCredentialVisibility(false);
  setOnboardingAiMessage(onboardingQs("onboardingAiCredentialStatus"), "");
  setOnboardingAiHidden(onboardingQs("onboardingAiCredentialModal"), false);
  onboardingQs("onboardingAiCredentialInput").focus();
}

function closeOnboardingAiCredentialModal({ restoreFocus = true } = {}) {
  onboardingQs("onboardingAiCredentialInput").value = "";
  setOnboardingAiCredentialVisibility(false);
  setOnboardingAiMessage(onboardingQs("onboardingAiCredentialStatus"), "");
  setOnboardingAiHidden(onboardingQs("onboardingAiCredentialModal"), true);
  onboardingAiState.credentialProvider = null;
  const trigger = onboardingAiState.modalTrigger;
  onboardingAiState.modalTrigger = null;
  if (restoreFocus && trigger) trigger.focus();
}

async function saveOnboardingAiCredential(event) {
  event.preventDefault();
  const provider = onboardingAiState.credentialProvider;
  const input = onboardingQs("onboardingAiCredentialInput");
  let submittedCredential = input.value;
  if (!provider || !submittedCredential.trim()) {
    setOnboardingAiMessage(onboardingQs("onboardingAiCredentialStatus"), "Enter an API key to continue.", "error");
    return;
  }
  const requestBody = { api_key: submittedCredential };
  const saveButton = onboardingQs("onboardingAiCredentialSaveBtn");
  saveButton.disabled = true;
  saveButton.textContent = "Saving…";
  try {
    await onboardingAiRequestJson(`/ai/settings/credentials/${encodeURIComponent(provider)}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(requestBody),
    });
    input.value = "";
    requestBody.api_key = "";
    submittedCredential = "";
    closeOnboardingAiCredentialModal({ restoreFocus: false });
    try {
      await refreshOnboardingAiSettings();
    } catch (_refreshError) {
      setOnboardingAiHidden(onboardingQs("onboardingAiContent"), true);
      setOnboardingAiHidden(onboardingQs("onboardingAiLoadError"), false);
    }
  } catch (error) {
    requestBody.api_key = "";
    submittedCredential = "";
    const category = error?.category || "request_failed";
    setOnboardingAiMessage(
      onboardingQs("onboardingAiCredentialStatus"),
      onboardingAiSafeFailures[category] || "The API key could not be saved. Try again.",
      "error"
    );
  } finally {
    saveButton.disabled = false;
    saveButton.textContent = "Save key";
  }
}

async function setOnboardingAiPreferredProvider(provider) {
  if (onboardingAiState.preferenceSaving) return;
  onboardingAiState.preferenceSaving = true;
  const status = document.querySelector(`[data-onboarding-ai-provider-status="${provider}"]`);
  setOnboardingAiMessage(status, "Saving preference…");
  try {
    await onboardingAiRequestJson("/ai/settings/preferred-provider", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ provider }),
    });
    await refreshOnboardingAiSettings();
  } catch (error) {
    const category = error?.category || "request_failed";
    setOnboardingAiMessage(
      status,
      onboardingAiSafeFailures[category] || "The provider preference could not be saved. Try again.",
      "error"
    );
  } finally {
    onboardingAiState.preferenceSaving = false;
  }
}

async function clearOnboardingAiPreferredProvider(provider) {
  if (onboardingAiState.preferenceSaving) return;
  onboardingAiState.preferenceSaving = true;
  const status = document.querySelector(`[data-onboarding-ai-provider-status="${provider}"]`);
  setOnboardingAiMessage(status, "Clearing preference…");
  try {
    await onboardingAiRequestJson("/ai/settings/preferred-provider", { method: "DELETE" });
    await refreshOnboardingAiSettings();
  } catch (error) {
    const category = error?.category || "request_failed";
    setOnboardingAiMessage(
      status,
      onboardingAiSafeFailures[category] || "The provider preference could not be cleared. Try again.",
      "error"
    );
  } finally {
    onboardingAiState.preferenceSaving = false;
  }
}

async function testOnboardingAiConnection() {
  if (onboardingAiState.connectionTesting) return;
  const provider = onboardingQs("onboardingAiTestProvider").value;
  const model = onboardingQs("onboardingAiTestModel").value;
  if (!provider || !model || !onboardingAiProviderSettings(provider).configured) return;
  onboardingAiState.connectionTesting = true;
  updateOnboardingAiTestButton();
  setOnboardingAiMessage(onboardingQs("onboardingAiTestStatus"), "Testing provider access…");
  try {
    const payload = await onboardingAiRequestJson("/ai/settings/test-connection", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ provider, model }),
    });
    if (!payload || payload.status !== "connected") throw new Error("Invalid connection response");
    setOnboardingAiMessage(
      onboardingQs("onboardingAiTestStatus"),
      `Connected · ${displayOnboardingAiProvider(provider)} · ${model}`,
      "success"
    );
  } catch (error) {
    const category = error?.category || "connection_test_failed";
    setOnboardingAiMessage(
      onboardingQs("onboardingAiTestStatus"),
      onboardingAiSafeFailures[category] || onboardingAiSafeFailures.connection_test_failed,
      "error"
    );
  } finally {
    onboardingAiState.connectionTesting = false;
    updateOnboardingAiTestButton();
  }
}

function skipOnboardingAiSetup() {
  onboardingPreferencesWorkflow?.showStep(5);
}

function bindOnboardingAiEvents() {
  onboardingQs("onboardingAiRetryBtn")?.addEventListener("click", loadOnboardingAiSettings);
  onboardingQs("onboardingAiSkipBtn")?.addEventListener("click", skipOnboardingAiSetup);
  onboardingQs("onboardingAiProviderGrid")?.addEventListener("click", (event) => {
    const credential = event.target.closest("[data-onboarding-ai-credential]");
    if (credential && onboardingAiCatalogProvider(credential.dataset.onboardingAiCredential)) {
      openOnboardingAiCredentialModal(credential.dataset.onboardingAiCredential, credential);
      return;
    }
    const clearPreferred = event.target.closest("[data-onboarding-ai-clear-preferred]");
    if (clearPreferred && onboardingAiCatalogProvider(clearPreferred.dataset.onboardingAiClearPreferred)) {
      clearOnboardingAiPreferredProvider(clearPreferred.dataset.onboardingAiClearPreferred);
      return;
    }
    const preferred = event.target.closest("[data-onboarding-ai-preferred]");
    if (preferred && onboardingAiCatalogProvider(preferred.dataset.onboardingAiPreferred)) {
      setOnboardingAiPreferredProvider(preferred.dataset.onboardingAiPreferred);
    }
  });
  onboardingQs("onboardingAiTestProvider")?.addEventListener("change", renderOnboardingAiConnectionModels);
  onboardingQs("onboardingAiTestModel")?.addEventListener("change", updateOnboardingAiTestButton);
  onboardingQs("onboardingAiTestBtn")?.addEventListener("click", testOnboardingAiConnection);
  onboardingQs("onboardingAiCredentialForm")?.addEventListener("submit", saveOnboardingAiCredential);
  onboardingQs("onboardingAiCredentialCancelBtn")?.addEventListener("click", () => closeOnboardingAiCredentialModal());
  onboardingQs("onboardingAiCredentialVisibilityBtn")?.addEventListener("click", () => {
    const input = onboardingQs("onboardingAiCredentialInput");
    setOnboardingAiCredentialVisibility(input.type === "password");
    input.focus();
  });
  onboardingQs("onboardingAiCredentialModal")?.addEventListener("click", (event) => {
    if (event.target === onboardingQs("onboardingAiCredentialModal")) closeOnboardingAiCredentialModal();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !onboardingQs("onboardingAiCredentialModal")?.classList.contains("hidden")) {
      closeOnboardingAiCredentialModal();
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const form = onboardingQs("onboardingForm");
  const draftBtn = onboardingQs("onboardingSaveDraftBtn");

  onboardingLocationSelector = window.ApplyLensLocationSelector?.create(
    onboardingQs("onboardingLocationSelector"),
    { onChange: markOnboardingPreferencesDirty }
  );
  onboardingPreferencesWorkflow = window.ApplyLensPreferencesWorkflow?.create(
    onboardingQs("onboardingPage"),
    { getValues: () => collectOnboardingPreferences(false) }
  );

  document.querySelectorAll("#onboardingForm input, #onboardingForm textarea").forEach((field) => {
    if (field.closest("[data-location-selector]")) return;
    field.addEventListener("change", () => {
      syncOnboardingSeniorityStrictToggle();
      renderRequirementStatus({});
      markOnboardingPreferencesDirty();
    });
  });
  document.querySelectorAll("#onboardingForm textarea").forEach((field) => {
    field.addEventListener("input", markOnboardingPreferencesDirty);
  });

  onboardingQs("onboardingSelectAllRolesBtn")?.addEventListener("click", () => {
    setOnboardingCheckboxGroup("selected_role_families", true);
    renderRequirementStatus({});
    markOnboardingPreferencesDirty();
  });
  onboardingQs("onboardingClearAllRolesBtn")?.addEventListener("click", () => {
    setOnboardingCheckboxGroup("selected_role_families", false);
    renderRequirementStatus({});
    markOnboardingPreferencesDirty();
  });

  if (form) {
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      saveOnboardingPreferences(true);
    });
  }

  if (draftBtn) {
    draftBtn.addEventListener("click", () => {
      saveOnboardingPreferences(false);
    });
  }

  bindOnboardingAiEvents();
  loadOnboardingPreferences();
  loadOnboardingAiSettings();
});
