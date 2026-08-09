(function () {
  "use strict";

  const byId = (id) => document.getElementById(id);
  const state = {
    settings: null,
    catalog: null,
    credentialProvider: null,
    removeProvider: null,
    activeModalTrigger: null,
    preferenceSaving: false,
    connectionTesting: false,
  };

  const safeFailureMessages = {
    credential_not_configured: "No API key is configured for this provider.",
    unsupported_provider: "This provider is not available.",
    unsupported_provider_model: "This model is not available for this provider.",
    invalid_credential: "Enter a valid API key and try again.",
    credential_write_failed: "The API key could not be saved. Try again.",
    credential_delete_failed: "The API key could not be removed. Try again.",
    settings_write_failed: "The provider preference could not be saved. Try again.",
    connection_test_failed: "Connection test failed. Check the key and provider access.",
  };

  function setHidden(element, hidden) {
    if (element) element.classList.toggle("hidden", hidden);
  }

  function setMessage(element, message, tone) {
    if (!element) return;
    element.textContent = message || "";
    element.className = element.id === "aiSettingsPageStatus"
      ? "profile-ai-settings-page-status"
      : "profile-ai-settings-inline-message";
    if (tone) element.classList.add(`is-${tone}`);
    element.classList.toggle("hidden", !message);
  }

  function displayProviderName(provider) {
    const normalizedProvider = String(provider || "").trim().toLowerCase();
    if (normalizedProvider === "openai") return "OpenAI";
    if (normalizedProvider === "groq") return "Groq";
    return normalizedProvider
      .split(/[-_]/)
      .filter(Boolean)
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(" ");
  }

  function createProviderMark(provider) {
    const normalizedProvider = String(provider || "").trim().toLowerCase();
    const mark = makeElement("span", "profile-ai-settings-provider-mark");
    mark.setAttribute("aria-hidden", "true");
    if (normalizedProvider === "openai") {
      const logo = makeElement("img", "profile-ai-settings-provider-logo");
      logo.src = "/static/media/openai_provider_logo.svg";
      logo.alt = "";
      mark.appendChild(logo);
      return mark;
    }
    if (normalizedProvider === "groq") {
      mark.appendChild(makeElement("span", "profile-ai-settings-provider-wordmark", "Groq"));
      return mark;
    }
    mark.appendChild(makeElement("span", "profile-ai-settings-provider-wordmark", displayProviderName(provider)));
    return mark;
  }

  function extractErrorCategory(payload) {
    const detail = payload && typeof payload.detail === "object" ? payload.detail : null;
    return detail && typeof detail.error_category === "string"
      ? detail.error_category
      : "request_failed";
  }

  async function requestJson(url, options) {
    const response = await window.fetch(url, options || {});
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      const requestError = new Error("AI settings request failed");
      requestError.category = extractErrorCategory(payload);
      throw requestError;
    }
    return payload;
  }

  function validateSettings(payload) {
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

  function validateCatalog(payload) {
    if (!payload || payload.ok !== true || !Array.isArray(payload.providers)) {
      throw new Error("Invalid AI provider catalog response");
    }
    const seenProviders = new Set();
    const providers = payload.providers.map((entry) => {
      if (!entry || typeof entry.provider !== "string" || !entry.provider || !Array.isArray(entry.models)) {
        throw new Error("Invalid AI provider catalog entry");
      }
      if (seenProviders.has(entry.provider)) {
        throw new Error("Duplicate AI provider catalog entry");
      }
      seenProviders.add(entry.provider);
      const models = entry.models.map((model) => {
        if (!model || typeof model.model_id !== "string" || !model.model_id) {
          throw new Error("Invalid AI model catalog entry");
        }
        return {
          provider: entry.provider,
          modelId: model.model_id,
          configurationStatus: typeof model.configuration_status === "string"
            ? model.configuration_status
            : "",
          liveQualificationStatus: typeof model.live_qualification_status === "string"
            ? model.live_qualification_status
            : "",
        };
      });
      return { provider: entry.provider, models };
    });
    if (!providers.length) throw new Error("Empty AI provider catalog response");
    return { providers };
  }

  function catalogProvider(provider) {
    return state.catalog.providers.find((entry) => entry.provider === provider) || null;
  }

  function providerSettings(provider) {
    return state.settings.providers[provider] || { configured: false, credentialHint: "" };
  }

  function makeElement(tagName, className, textValue) {
    const element = document.createElement(tagName);
    if (className) element.className = className;
    if (textValue !== undefined) element.textContent = textValue;
    return element;
  }

  function renderProviderCards() {
    const providerGrid = byId("aiSettingsProviderGrid");
    providerGrid.replaceChildren();
    state.catalog.providers.forEach((catalogEntry) => {
      const provider = catalogEntry.provider;
      const providerState = providerSettings(provider);
      const card = makeElement("article", "profile-ai-settings-provider-card");
      card.dataset.provider = provider;

      const heading = makeElement("div", "profile-ai-settings-provider-heading");
      const identity = makeElement("div", "profile-ai-settings-provider-identity");
      const providerMark = createProviderMark(provider);
      const identityCopy = makeElement("div");
      identityCopy.appendChild(makeElement("h3", "", displayProviderName(provider)));
      identityCopy.appendChild(
        makeElement(
          "span",
          "profile-ai-settings-provider-model-count",
          `${catalogEntry.models.length} available ${catalogEntry.models.length === 1 ? "model" : "models"}`
        )
      );
      identity.append(providerMark, identityCopy);

      const badges = makeElement("div", "profile-ai-settings-provider-badges");
      const statusBadge = makeElement(
        "span",
        `profile-ai-settings-status-badge ${providerState.configured ? "is-configured" : "is-unconfigured"}`,
        providerState.configured ? "Configured" : "Not configured"
      );
      badges.appendChild(statusBadge);
      if (state.settings.preferredProvider === provider) {
        badges.appendChild(makeElement("span", "profile-ai-settings-preferred-badge", "Preferred"));
      }
      heading.append(identity, badges);

      const detail = makeElement("div", "profile-ai-settings-provider-detail");
      if (providerState.configured) {
        const hint = makeElement("span", "profile-ai-settings-credential-hint", providerState.credentialHint);
        hint.setAttribute("aria-label", "Stored credential hint");
        detail.appendChild(hint);
      } else {
        detail.appendChild(
          makeElement("span", "profile-ai-settings-provider-help", "Add an API key to enable connection testing.")
        );
      }

      const actions = makeElement("div", "profile-ai-settings-provider-actions");
      const saveButton = makeElement(
        "button",
        providerState.configured ? "ghost-btn" : "",
        providerState.configured ? "Replace key" : "Add API key"
      );
      saveButton.type = "button";
      saveButton.dataset.credentialAction = "save";
      saveButton.dataset.provider = provider;
      actions.appendChild(saveButton);
      if (providerState.configured) {
        const removeButton = makeElement("button", "ghost-btn profile-ai-settings-remove-btn", "Remove");
        removeButton.type = "button";
        removeButton.dataset.credentialAction = "remove";
        removeButton.dataset.provider = provider;
        actions.appendChild(removeButton);
      }

      card.append(heading, detail, actions);
      providerGrid.appendChild(card);
    });
  }

  function appendProviderOptions(select, includeNoPreference) {
    select.replaceChildren();
    if (includeNoPreference) {
      const noPreference = makeElement("option", "", "No preference");
      noPreference.value = "";
      select.appendChild(noPreference);
    }
    state.catalog.providers.forEach((entry) => {
      const option = makeElement("option", "", displayProviderName(entry.provider));
      option.value = entry.provider;
      select.appendChild(option);
    });
  }

  function renderPreferredProvider() {
    const select = byId("aiPreferredProviderSelect");
    appendProviderOptions(select, true);
    select.value = state.settings.preferredProvider || "";
    renderPreferredWarning();
  }

  function renderPreferredWarning() {
    const warning = byId("aiPreferredProviderWarning");
    const preferred = state.settings.preferredProvider;
    const isConfigured = preferred ? providerSettings(preferred).configured : true;
    if (preferred && !isConfigured) {
      warning.textContent = `${displayProviderName(preferred)} is preferred but does not have an API key configured.`;
      setHidden(warning, false);
    } else {
      warning.textContent = "";
      setHidden(warning, true);
    }
  }

  function renderConnectionSelectors() {
    const providerSelect = byId("aiTestProviderSelect");
    const previousProvider = providerSelect.value;
    appendProviderOptions(providerSelect, false);
    const availableProvider = catalogProvider(previousProvider)
      ? previousProvider
      : state.settings.preferredProvider;
    if (availableProvider && catalogProvider(availableProvider)) {
      providerSelect.value = availableProvider;
    }
    renderConnectionModels();
  }

  function renderConnectionModels() {
    const providerSelect = byId("aiTestProviderSelect");
    const modelSelect = byId("aiTestModelSelect");
    const previousModel = modelSelect.value;
    const selectedCatalog = catalogProvider(providerSelect.value);
    modelSelect.replaceChildren();
    (selectedCatalog ? selectedCatalog.models : []).forEach((model) => {
      const option = makeElement("option", "", model.modelId);
      option.value = model.modelId;
      modelSelect.appendChild(option);
    });
    if (selectedCatalog && selectedCatalog.models.some((model) => model.modelId === previousModel)) {
      modelSelect.value = previousModel;
    }
    updateConnectionButton();
  }

  function updateConnectionButton() {
    const provider = byId("aiTestProviderSelect").value;
    const model = byId("aiTestModelSelect").value;
    const configured = provider ? providerSettings(provider).configured : false;
    const button = byId("aiConnectionTestBtn");
    button.disabled = !configured || !model || state.connectionTesting;
    button.textContent = state.connectionTesting ? "Testing…" : "Test connection";
    if (!state.connectionTesting && provider && !configured) {
      setMessage(byId("aiConnectionTestStatus"), "Add an API key for this provider before testing.", "neutral");
    } else if (!state.connectionTesting) {
      setMessage(byId("aiConnectionTestStatus"), "", "");
    }
  }

  function statusLabel(value, fallback) {
    if (value === "configuration_eligible") return "Configuration candidate";
    if (value === "live_qualification_required") return "Needs live qualification";
    return value ? value.replaceAll("_", " ") : fallback;
  }

  function renderModels() {
    const modelGroups = byId("aiSettingsModelGroups");
    modelGroups.replaceChildren();
    state.catalog.providers.forEach((entry) => {
      const group = makeElement("section", "profile-ai-settings-model-group");
      const heading = makeElement("div", "profile-ai-settings-model-group-heading");
      heading.appendChild(makeElement("h3", "", displayProviderName(entry.provider)));
      heading.appendChild(
        makeElement("span", "", `${entry.models.length} ${entry.models.length === 1 ? "model" : "models"}`)
      );
      group.appendChild(heading);
      const list = makeElement("div", "profile-ai-settings-model-list");
      entry.models.forEach((model) => {
        const row = makeElement("div", "profile-ai-settings-model-row");
        const identity = makeElement("div", "profile-ai-settings-model-identity");
        identity.appendChild(makeElement("strong", "", model.modelId));
        identity.appendChild(makeElement("span", "", displayProviderName(model.provider)));
        const statuses = makeElement("div", "profile-ai-settings-model-statuses");
        statuses.appendChild(
          makeElement(
            "span",
            "profile-ai-settings-model-badge",
            statusLabel(model.configurationStatus, "Configuration candidate")
          )
        );
        if (model.liveQualificationStatus) {
          statuses.appendChild(
            makeElement(
              "span",
              "profile-ai-settings-model-badge is-muted",
              statusLabel(model.liveQualificationStatus, "Qualification status unavailable")
            )
          );
        }
        row.append(identity, statuses);
        list.appendChild(row);
      });
      group.appendChild(list);
      modelGroups.appendChild(group);
    });
  }

  function renderAll() {
    renderProviderCards();
    renderPreferredProvider();
    renderConnectionSelectors();
    renderModels();
  }

  async function loadPage() {
    setHidden(byId("aiSettingsLoading"), false);
    setHidden(byId("aiSettingsLoadError"), true);
    setHidden(byId("aiSettingsContent"), true);
    try {
      const [settingsPayload, catalogPayload] = await Promise.all([
        requestJson("/ai/settings"),
        requestJson("/ai/settings/catalog"),
      ]);
      const settings = validateSettings(settingsPayload);
      const catalog = validateCatalog(catalogPayload);
      catalog.providers.forEach((entry) => {
        if (!Object.prototype.hasOwnProperty.call(settings.providers, entry.provider)) {
          throw new Error("Provider settings do not match catalog");
        }
      });
      state.settings = settings;
      state.catalog = catalog;
      renderAll();
      setHidden(byId("aiSettingsContent"), false);
    } catch (_error) {
      setHidden(byId("aiSettingsLoadError"), false);
    } finally {
      setHidden(byId("aiSettingsLoading"), true);
    }
  }

  async function refreshSettings() {
    state.settings = validateSettings(await requestJson("/ai/settings"));
    renderProviderCards();
    renderPreferredProvider();
    renderConnectionSelectors();
  }

  function setCredentialVisibility(reveal) {
    const input = byId("aiCredentialInput");
    const button = byId("aiCredentialVisibilityBtn");
    const showIcon = byId("aiCredentialVisibilityShowIcon");
    const hideIcon = byId("aiCredentialVisibilityHideIcon");
    const label = reveal ? "Hide API key" : "Show API key";
    input.type = reveal ? "text" : "password";
    showIcon.hidden = reveal;
    hideIcon.hidden = !reveal;
    button.setAttribute("aria-label", label);
    button.setAttribute("title", label);
    button.setAttribute("aria-pressed", reveal ? "true" : "false");
  }

  function openCredentialModal(provider, trigger) {
    const providerState = providerSettings(provider);
    state.credentialProvider = provider;
    state.activeModalTrigger = trigger;
    byId("aiCredentialModalTitle").textContent = providerState.configured ? "Replace API key" : "Add API key";
    byId("aiCredentialModalSubtitle").textContent = displayProviderName(provider);
    byId("aiCredentialInput").value = "";
    setCredentialVisibility(false);
    setMessage(byId("aiCredentialModalStatus"), "", "");
    setHidden(byId("aiCredentialModal"), false);
    byId("aiCredentialInput").focus();
  }

  function closeCredentialModal(options) {
    const restoreFocus = !options || options.restoreFocus !== false;
    byId("aiCredentialInput").value = "";
    setCredentialVisibility(false);
    setMessage(byId("aiCredentialModalStatus"), "", "");
    setHidden(byId("aiCredentialModal"), true);
    state.credentialProvider = null;
    const trigger = state.activeModalTrigger;
    state.activeModalTrigger = null;
    if (restoreFocus && trigger) trigger.focus();
  }

  function openRemoveModal(provider, trigger) {
    state.removeProvider = provider;
    state.activeModalTrigger = trigger;
    byId("aiCredentialRemoveSubtitle").textContent = displayProviderName(provider);
    setMessage(byId("aiCredentialRemoveStatus"), "", "");
    setHidden(byId("aiCredentialRemoveModal"), false);
    byId("aiCredentialRemoveCancelBtn").focus();
  }

  function closeRemoveModal(options) {
    const restoreFocus = !options || options.restoreFocus !== false;
    setHidden(byId("aiCredentialRemoveModal"), true);
    setMessage(byId("aiCredentialRemoveStatus"), "", "");
    state.removeProvider = null;
    const trigger = state.activeModalTrigger;
    state.activeModalTrigger = null;
    if (restoreFocus && trigger) trigger.focus();
  }

  async function submitCredential(event) {
    event.preventDefault();
    if (!state.credentialProvider) return;
    const input = byId("aiCredentialInput");
    let submittedCredential = input.value;
    if (!submittedCredential.trim()) {
      setMessage(byId("aiCredentialModalStatus"), "Enter an API key to continue.", "error");
      return;
    }
    const provider = state.credentialProvider;
    const requestBody = { api_key: submittedCredential };
    const saveButton = byId("aiCredentialSaveBtn");
    saveButton.disabled = true;
    saveButton.textContent = "Saving…";
    try {
      await requestJson(`/ai/settings/credentials/${encodeURIComponent(provider)}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
      });
      input.value = "";
      requestBody.api_key = "";
      submittedCredential = "";
      closeCredentialModal({ restoreFocus: false });
      try {
        await refreshSettings();
        setMessage(
          byId("aiSettingsPageStatus"),
          `API key saved for ${displayProviderName(provider)}.`,
          "success"
        );
      } catch (_refreshError) {
        setMessage(
          byId("aiSettingsPageStatus"),
          "The API key was saved, but the latest settings could not be loaded. Use Retry to refresh.",
          "error"
        );
      }
      setHidden(byId("aiSettingsPageStatus"), false);
    } catch (error) {
      requestBody.api_key = "";
      submittedCredential = "";
      const category = error && error.category ? error.category : "request_failed";
      setMessage(
        byId("aiCredentialModalStatus"),
        safeFailureMessages[category] || "The API key could not be saved. Try again.",
        "error"
      );
    } finally {
      saveButton.disabled = false;
      saveButton.textContent = "Save key";
    }
  }

  async function removeCredential() {
    if (!state.removeProvider) return;
    const provider = state.removeProvider;
    const removeButton = byId("aiCredentialRemoveConfirmBtn");
    removeButton.disabled = true;
    removeButton.textContent = "Removing…";
    try {
      await requestJson(`/ai/settings/credentials/${encodeURIComponent(provider)}`, {
        method: "DELETE",
      });
      closeRemoveModal({ restoreFocus: false });
      try {
        await refreshSettings();
        setMessage(
          byId("aiSettingsPageStatus"),
          `Stored API key removed for ${displayProviderName(provider)}.`,
          "success"
        );
      } catch (_refreshError) {
        setMessage(
          byId("aiSettingsPageStatus"),
          "The API key was removed, but the latest settings could not be loaded. Use Retry to refresh.",
          "error"
        );
      }
      setHidden(byId("aiSettingsPageStatus"), false);
    } catch (error) {
      const category = error && error.category ? error.category : "request_failed";
      setMessage(
        byId("aiCredentialRemoveStatus"),
        safeFailureMessages[category] || "The API key could not be removed. Try again.",
        "error"
      );
    } finally {
      removeButton.disabled = false;
      removeButton.textContent = "Remove key";
    }
  }

  async function savePreferredProvider() {
    if (state.preferenceSaving) return;
    state.preferenceSaving = true;
    const button = byId("aiPreferredProviderSaveBtn");
    const selectedProvider = byId("aiPreferredProviderSelect").value;
    button.disabled = true;
    button.textContent = "Saving…";
    setMessage(byId("aiPreferredProviderStatus"), "", "");
    try {
      if (selectedProvider) {
        await requestJson("/ai/settings/preferred-provider", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ provider: selectedProvider }),
        });
      } else {
        await requestJson("/ai/settings/preferred-provider", { method: "DELETE" });
      }
      await refreshSettings();
      setMessage(byId("aiPreferredProviderStatus"), "Provider preference saved.", "success");
    } catch (error) {
      const category = error && error.category ? error.category : "request_failed";
      setMessage(
        byId("aiPreferredProviderStatus"),
        safeFailureMessages[category] || "The provider preference could not be saved. Try again.",
        "error"
      );
    } finally {
      state.preferenceSaving = false;
      button.disabled = false;
      button.textContent = "Save preference";
    }
  }

  async function testConnection() {
    if (state.connectionTesting) return;
    const provider = byId("aiTestProviderSelect").value;
    const model = byId("aiTestModelSelect").value;
    if (!provider || !model || !providerSettings(provider).configured) {
      updateConnectionButton();
      return;
    }
    state.connectionTesting = true;
    updateConnectionButton();
    setMessage(byId("aiConnectionTestStatus"), "Testing provider access…", "neutral");
    try {
      const result = await requestJson("/ai/settings/test-connection", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ provider, model }),
      });
      if (!result || result.status !== "connected") throw new Error("Invalid connection response");
      setMessage(
        byId("aiConnectionTestStatus"),
        `Connected · ${displayProviderName(provider)} · ${model}`,
        "success"
      );
    } catch (error) {
      const category = error && error.category ? error.category : "connection_test_failed";
      setMessage(
        byId("aiConnectionTestStatus"),
        safeFailureMessages[category] || safeFailureMessages.connection_test_failed,
        "error"
      );
    } finally {
      state.connectionTesting = false;
      const button = byId("aiConnectionTestBtn");
      button.disabled = !providerSettings(byId("aiTestProviderSelect").value).configured
        || !byId("aiTestModelSelect").value;
      button.textContent = "Test connection";
    }
  }

  function bindEvents() {
    byId("aiSettingsRetryBtn").addEventListener("click", loadPage);
    byId("aiSettingsProviderGrid").addEventListener("click", (event) => {
      const trigger = event.target.closest("[data-credential-action]");
      if (!trigger) return;
      const provider = trigger.dataset.provider;
      if (!catalogProvider(provider)) return;
      if (trigger.dataset.credentialAction === "save") openCredentialModal(provider, trigger);
      if (trigger.dataset.credentialAction === "remove") openRemoveModal(provider, trigger);
    });
    byId("aiCredentialForm").addEventListener("submit", submitCredential);
    byId("aiCredentialCancelBtn").addEventListener("click", () => closeCredentialModal());
    byId("aiCredentialVisibilityBtn").addEventListener("click", () => {
      const input = byId("aiCredentialInput");
      setCredentialVisibility(input.type === "password");
      input.focus();
    });
    byId("aiCredentialRemoveCloseBtn").addEventListener("click", () => closeRemoveModal());
    byId("aiCredentialRemoveCancelBtn").addEventListener("click", () => closeRemoveModal());
    byId("aiCredentialRemoveConfirmBtn").addEventListener("click", removeCredential);
    byId("aiPreferredProviderSaveBtn").addEventListener("click", savePreferredProvider);
    byId("aiTestProviderSelect").addEventListener("change", renderConnectionModels);
    byId("aiTestModelSelect").addEventListener("change", updateConnectionButton);
    byId("aiConnectionTestBtn").addEventListener("click", testConnection);
    byId("aiCredentialModal").addEventListener("click", (event) => {
      if (event.target === byId("aiCredentialModal")) closeCredentialModal();
    });
    byId("aiCredentialRemoveModal").addEventListener("click", (event) => {
      if (event.target === byId("aiCredentialRemoveModal")) closeRemoveModal();
    });
    document.addEventListener("keydown", (event) => {
      if (event.key !== "Escape") return;
      if (!byId("aiCredentialModal").classList.contains("hidden")) closeCredentialModal();
      if (!byId("aiCredentialRemoveModal").classList.contains("hidden")) closeRemoveModal();
    });
  }

  function init() {
    bindEvents();
    loadPage();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }
})();
