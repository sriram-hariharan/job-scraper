(function () {
  "use strict";

  const byId = (id) => document.getElementById(id);
  const state = {
    settings: null,
    catalog: null,
    routing: null,
    credentialProvider: null,
    removeProvider: null,
    activeModalTrigger: null,
    preferenceSaving: false,
    connectionTesting: false,
    routeSavingWorkload: null,
    routeSavedWorkload: null,
    routeSavePresentationVersion: 0,
    routeMessages: new Map(),
  };

  const applyLensRecommendedRouteValue = "applylens-recommended";

  const safeFailureMessages = {
    credential_not_configured: "No API key is configured for this provider.",
    unsupported_provider: "This provider is not available.",
    unsupported_provider_model: "This model is not available for this provider.",
    invalid_credential: "Enter a valid API key and try again.",
    credential_write_failed: "The API key could not be saved. Try again.",
    credential_delete_failed: "The API key could not be removed. Try again.",
    settings_write_failed: "The provider preference could not be saved. Try again.",
    connection_test_failed: "Connection test failed. Check the key and provider access.",
    task_route_not_qualified: "That route is no longer currently qualified. Choose from the current routing options and try again.",
    task_route_write_failed: "The task route could not be saved. Try again.",
    task_route_delete_failed: "The task route could not be returned to ApplyLens Recommended. Try again.",
    task_route_state_unavailable: "Current task routing is unavailable. Retry the page before saving.",
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

  function displayTaskName(workloadId) {
    return String(workloadId || "")
      .trim()
      .split(/[_-]+/)
      .filter(Boolean)
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(" ");
  }

  function displayTaskDescription(workloadId) {
    const descriptions = {
      skill_extraction: "Finds the important skills and requirements mentioned in a job posting.",
      job_fit_evaluation: "Compares your profile with a job and explains how well they match.",
      jd_intelligence: "Breaks a job description into structured requirements and useful signals.",
      grounded_rag_answer: "Answers questions using only the relevant evidence available to ApplyLens.",
      resume_fallback_ranking: "Ranks resume options when ApplyLens needs a fallback comparison.",
      ambiguous_resume_adjudication: "Reviews closely matched resume choices and recommends the best-supported option.",
      critic_evaluation: "Checks whether an AI suggestion is actually supported by the available evidence.",
      tailoring_generation: "Creates evidence-based resume tailoring suggestions for your review.",
      tailoring_refinement: "Improves a proposed resume edit while keeping it grounded in your evidence.",
      tailoring_judge: "Compares tailoring options and identifies the strongest supported version.",
      manual_scan_phrase: "Suggests phrases you can manually review and use while improving a resume.",
      manual_provider_preview: "Generates a manual AI preview for review before anything is applied.",
    };
    return descriptions[String(workloadId || "").trim()]
      || "Controls how ApplyLens handles this task.";
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

  function validateProviderModelPair(value, label) {
    if (!value || typeof value !== "object" || Array.isArray(value)) {
      throw new Error(`Invalid ${label}`);
    }
    const keys = Object.keys(value).sort();
    if (keys.length !== 2 || keys[0] !== "model" || keys[1] !== "provider") {
      throw new Error(`Invalid ${label}`);
    }
    const provider = typeof value.provider === "string" ? value.provider.trim() : "";
    const model = typeof value.model === "string" ? value.model.trim() : "";
    if (!provider || !model) throw new Error(`Invalid ${label}`);
    return { provider, model };
  }

  function sameProviderModelPair(left, right) {
    return Boolean(left && right && left.provider === right.provider && left.model === right.model);
  }

  function validateRoutingRow(row) {
    if (!row || typeof row !== "object" || Array.isArray(row)) {
      throw new Error("Invalid AI task routing row");
    }
    const allowedRecommendationStatuses = new Set([
      "recommended",
      "fail_closed_zero_qualified",
      "blocked_non_live",
    ]);
    const allowedExecutionModes = new Set([
      "qualified_provider_model",
      "deterministic",
      "blocked_non_live",
    ]);
    const allowedRequestedStatuses = new Set([
      "none",
      "qualified",
      "no_longer_qualified",
    ]);
    const allowedEffectiveSources = new Set([
      "user_override",
      "applylens_recommended",
      "deterministic",
      "blocked_non_live",
    ]);
    const workloadId = typeof row.workload_id === "string" ? row.workload_id.trim() : "";
    if (!workloadId) throw new Error("Invalid AI task routing workload");
    if (!allowedRecommendationStatuses.has(row.recommendation_status)) {
      throw new Error("Invalid AI task routing status");
    }
    if (!allowedExecutionModes.has(row.execution_mode)) {
      throw new Error("Invalid AI task execution mode");
    }
    if (!allowedRequestedStatuses.has(row.requested_selection_status)) {
      throw new Error("Invalid requested task route status");
    }
    if (!allowedEffectiveSources.has(row.effective_selection_source)) {
      throw new Error("Invalid effective task route source");
    }
    if (!Array.isArray(row.qualified_options)) {
      throw new Error("Invalid qualified task route options");
    }
    const qualifiedOptions = row.qualified_options.map((option) => (
      validateProviderModelPair(option, "qualified task route option")
    ));
    const optionKeys = qualifiedOptions.map((option) => JSON.stringify([option.provider, option.model]));
    if (new Set(optionKeys).size !== optionKeys.length) {
      throw new Error("Duplicate qualified task route option");
    }
    const requestedSelection = row.requested_selection === null
      ? null
      : validateProviderModelPair(row.requested_selection, "requested task route");
    const effectiveSelection = row.effective_selection === null
      ? null
      : validateProviderModelPair(row.effective_selection, "effective task route");
    const recommendedOption = row.recommended_option === null
      ? null
      : validateProviderModelPair(row.recommended_option, "recommended task route");
    const provider = typeof row.provider === "string" ? row.provider.trim() : "";
    const model = typeof row.model === "string" ? row.model.trim() : "";

    if (row.requested_selection_status === "none" && requestedSelection !== null) {
      throw new Error("Unrequested task route contains a saved selection");
    }
    if (row.requested_selection_status !== "none" && requestedSelection === null) {
      throw new Error("Requested task route lacks a saved selection");
    }

    if (row.execution_mode === "qualified_provider_model") {
      if (row.recommendation_status !== "recommended"
        || typeof row.provider !== "string" || typeof row.model !== "string"
        || !provider || !model) {
        throw new Error("Qualified task route lacks its recommendation");
      }
      if (!recommendedOption || !qualifiedOptions.some((option) => sameProviderModelPair(option, recommendedOption))) {
        throw new Error("Recommended task route is not currently qualified");
      }
      if (!sameProviderModelPair({ provider, model }, recommendedOption) || !effectiveSelection) {
        throw new Error("Qualified task route recommendation is inconsistent");
      }
      if (row.requested_selection_status === "qualified") {
        if (!qualifiedOptions.some((option) => sameProviderModelPair(option, requestedSelection))) {
          throw new Error("Saved task route is not currently qualified");
        }
        if (!sameProviderModelPair(effectiveSelection, requestedSelection)
          || row.effective_selection_source !== "user_override") {
          throw new Error("Saved task route is not effective");
        }
      } else if (row.requested_selection_status === "none") {
        if (!sameProviderModelPair(effectiveSelection, recommendedOption)
          || row.effective_selection_source !== "applylens_recommended") {
          throw new Error("Default task route is inconsistent");
        }
      } else {
        if (qualifiedOptions.some((option) => sameProviderModelPair(option, requestedSelection))) {
          throw new Error("Stale task route remains selectable");
        }
        if (!sameProviderModelPair(effectiveSelection, recommendedOption)
          || row.effective_selection_source !== "applylens_recommended") {
          throw new Error("Stale task route fallback is inconsistent");
        }
      }
    } else {
      const expectedStatus = row.execution_mode === "deterministic"
        ? "fail_closed_zero_qualified"
        : "blocked_non_live";
      if (row.recommendation_status !== expectedStatus
        || row.provider !== null || row.model !== null || provider || model
        || recommendedOption !== null || qualifiedOptions.length !== 0
        || effectiveSelection !== null
        || row.effective_selection_source !== row.execution_mode
        || row.requested_selection_status === "qualified") {
        throw new Error("Non-selectable task route is inconsistent");
      }
    }

    return {
      workloadId,
      recommendationStatus: row.recommendation_status,
      executionMode: row.execution_mode,
      provider: provider || null,
      model: model || null,
      recommendedOption,
      qualifiedOptions,
      requestedSelection,
      requestedSelectionStatus: row.requested_selection_status,
      effectiveSelection,
      effectiveSelectionSource: row.effective_selection_source,
    };
  }

  function validateRecommendedRoutes(payload) {
    if (!payload || payload.ok !== true || !Array.isArray(payload.workloads)) {
      throw new Error("Invalid AI task routing response");
    }
    const seenWorkloads = new Set();
    const workloads = payload.workloads.map((row) => {
      const route = validateRoutingRow(row);
      if (seenWorkloads.has(route.workloadId)) {
        throw new Error("Duplicate AI task routing workload");
      }
      seenWorkloads.add(route.workloadId);
      return route;
    });
    return { workloads };
  }

  function validateTaskRouteWriteResponse(payload, workloadId) {
    if (!payload || payload.ok !== true) throw new Error("Invalid task route write response");
    const route = validateRoutingRow(payload);
    if (route.workloadId !== workloadId) throw new Error("Task route write response mismatch");
    return route;
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

  function providerGuidance(provider) {
    const template = byId(`providerKeyGuidanceTemplate-${provider}`);
    return template instanceof HTMLTemplateElement
      ? template.content.cloneNode(true)
      : document.createDocumentFragment();
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

      card.append(heading, detail, providerGuidance(provider), actions);
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
    setHidden(byId("aiPreferredProviderClearBtn"), !state.settings.preferredProvider);
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

  function renderRouting() {
    const summary = byId("aiTaskRoutingSummary");
    const list = byId("aiTaskRoutingList");
    summary.replaceChildren();
    list.replaceChildren();

    const counts = state.routing.workloads.reduce(
      (result, row) => {
        result.total += 1;
        if (row.executionMode === "qualified_provider_model") result.qualified += 1;
        if (row.executionMode === "deterministic") result.deterministic += 1;
        if (row.executionMode === "blocked_non_live") result.notLive += 1;
        return result;
      },
      { total: 0, qualified: 0, deterministic: 0, notLive: 0 }
    );
    [
      ["Total tasks", counts.total],
      ["Model-routed", counts.qualified],
      ["Deterministic", counts.deterministic],
      ["Not live", counts.notLive],
    ].forEach(([label, value]) => {
      const item = makeElement("div", "profile-ai-settings-routing-summary-item");
      item.append(
        makeElement("span", "profile-ai-settings-routing-summary-label", label),
        makeElement("strong", "profile-ai-settings-routing-summary-value", String(value))
      );
      summary.appendChild(item);
    });

    state.routing.workloads.forEach((route) => {
      const statusDetails = route.executionMode === "qualified_provider_model"
        ? { label: "Qualified choices", className: "is-recommended", note: "" }
        : route.executionMode === "deterministic"
          ? { label: "Deterministic", className: "is-deterministic", note: "No provider call is used" }
          : { label: "Not live", className: "is-not-live", note: "" };
      const row = makeElement(
        "article",
        `profile-ai-settings-routing-row ${statusDetails.className}`
      );
      row.dataset.workloadId = route.workloadId;

      const taskField = makeElement("div", "profile-ai-settings-routing-field is-task");
      taskField.append(
        makeElement("span", "profile-ai-settings-routing-field-label", "Task"),
        makeElement("strong", "profile-ai-settings-routing-task", displayTaskName(route.workloadId)),
        makeElement(
          "span",
          "profile-ai-settings-routing-description",
          displayTaskDescription(route.workloadId)
        )
      );

      const statusField = makeElement("div", "profile-ai-settings-routing-field is-status");
      statusField.append(
        makeElement("span", "profile-ai-settings-routing-field-label", "Routing status"),
        makeElement(
          "span",
          `profile-ai-settings-routing-status ${statusDetails.className}`,
          statusDetails.label
        )
      );
      if (statusDetails.note) {
        statusField.appendChild(
          makeElement("span", "profile-ai-settings-routing-note", statusDetails.note)
        );
      }

      const effectiveField = makeElement("div", "profile-ai-settings-routing-field is-effective");
      effectiveField.appendChild(
        makeElement("span", "profile-ai-settings-routing-field-label", "Effective route")
      );
      if (route.effectiveSelection) {
        effectiveField.append(
          makeElement(
            "span",
            "profile-ai-settings-routing-value",
            `${displayProviderName(route.effectiveSelection.provider)} · ${route.effectiveSelection.model}`
          ),
          makeElement(
            "span",
            "profile-ai-settings-routing-source",
            route.effectiveSelectionSource === "user_override"
              ? "Explicit override"
              : "ApplyLens Recommended"
          )
        );
      } else {
        effectiveField.appendChild(
          makeElement(
            "span",
            "profile-ai-settings-routing-value",
            route.executionMode === "deterministic" ? "No provider/model route" : "Unavailable"
          )
        );
      }

      const controls = makeElement("div", "profile-ai-settings-routing-controls");
      if (route.executionMode === "qualified_provider_model") {
        const selectLabel = makeElement(
          "label",
          "profile-ai-settings-routing-field-label",
          "Routing preference"
        );
        const select = makeElement("select", "profile-ai-settings-routing-select");
        select.dataset.routeSelect = "true";
        selectLabel.appendChild(select);

        const recommendedChoice = makeElement("option", "", "ApplyLens Recommended");
        recommendedChoice.value = applyLensRecommendedRouteValue;
        select.appendChild(recommendedChoice);
        route.qualifiedOptions.forEach((option, index) => {
          const explicitChoice = makeElement(
            "option",
            "",
            `${displayProviderName(option.provider)} · ${option.model}`
          );
          explicitChoice.value = `qualified:${index}`;
          select.appendChild(explicitChoice);
        });

        if (route.requestedSelectionStatus === "qualified") {
          const requestedIndex = route.qualifiedOptions.findIndex((option) => (
            sameProviderModelPair(option, route.requestedSelection)
          ));
          select.value = `qualified:${requestedIndex}`;
        } else {
          select.value = applyLensRecommendedRouteValue;
        }

        const saveButton = makeElement("button", "", "Save route");
        saveButton.type = "button";
        saveButton.dataset.routeSave = "true";
        saveButton.dataset.workloadId = route.workloadId;
        const routeSaving = Boolean(state.routeSavingWorkload);
        select.disabled = routeSaving;
        saveButton.disabled = routeSaving;
        if (state.routeSavingWorkload === route.workloadId) {
          saveButton.textContent = "Saving…";
          saveButton.classList.add("is-saving");
          saveButton.setAttribute("aria-busy", "true");
        } else if (state.routeSavedWorkload === route.workloadId) {
          saveButton.textContent = "✓ Saved";
          saveButton.classList.add("is-saved");
        }
        controls.append(selectLabel, saveButton);

        if (route.requestedSelectionStatus === "no_longer_qualified") {
          controls.appendChild(
            makeElement(
              "p",
              "profile-ai-settings-routing-stale-note",
              `Previously saved ${displayProviderName(route.requestedSelection.provider)} · ${route.requestedSelection.model} is no longer qualified. ApplyLens Recommended is currently effective.`
            )
          );
        } else {
          controls.appendChild(
            makeElement(
              "p",
              "profile-ai-settings-routing-help",
              "ApplyLens Recommended stores no explicit override. Alternatives shown here are currently qualified."
            )
          );
        }
      } else {
        controls.appendChild(
          makeElement(
            "p",
            "profile-ai-settings-routing-static-note",
            route.executionMode === "deterministic"
              ? "This task runs without a provider/model route and cannot be configured here."
              : "This task is not live and cannot be configured."
          )
        );
      }

      const routeMessage = makeElement("div", "profile-ai-settings-inline-message hidden");
      routeMessage.dataset.routeMessage = route.workloadId;
      routeMessage.setAttribute("role", "status");
      routeMessage.setAttribute("aria-live", "polite");
      const messageState = state.routeMessages.get(route.workloadId);
      if (messageState) setMessage(routeMessage, messageState.message, messageState.tone);
      controls.appendChild(routeMessage);

      row.append(taskField, statusField, effectiveField, controls);
      list.appendChild(row);
    });
  }

  function renderAll() {
    renderProviderCards();
    renderPreferredProvider();
    renderConnectionSelectors();
    renderModels();
    renderRouting();
  }

  async function loadPage() {
    setHidden(byId("aiSettingsLoading"), false);
    setHidden(byId("aiSettingsLoadError"), true);
    setHidden(byId("aiSettingsContent"), true);
    try {
      const [settingsPayload, catalogPayload, routingPayload] = await Promise.all([
        requestJson("/ai/settings"),
        requestJson("/ai/settings/catalog"),
        requestJson("/ai/settings/recommended-routes"),
      ]);
      const settings = validateSettings(settingsPayload);
      const catalog = validateCatalog(catalogPayload);
      const routing = validateRecommendedRoutes(routingPayload);
      catalog.providers.forEach((entry) => {
        if (!Object.prototype.hasOwnProperty.call(settings.providers, entry.provider)) {
          throw new Error("Provider settings do not match catalog");
        }
      });
      state.settings = settings;
      state.catalog = catalog;
      state.routing = routing;
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

  async function clearPreferredProvider() {
    if (state.preferenceSaving || !state.settings.preferredProvider) return;
    state.preferenceSaving = true;
    const button = byId("aiPreferredProviderClearBtn");
    const saveButton = byId("aiPreferredProviderSaveBtn");
    button.disabled = true;
    saveButton.disabled = true;
    button.textContent = "Clearing…";
    setMessage(byId("aiPreferredProviderStatus"), "", "");
    try {
      await requestJson("/ai/settings/preferred-provider", { method: "DELETE" });
      await refreshSettings();
      setMessage(byId("aiPreferredProviderStatus"), "Provider preference cleared.", "success");
    } catch (error) {
      const category = error && error.category ? error.category : "request_failed";
      setMessage(
        byId("aiPreferredProviderStatus"),
        safeFailureMessages[category] || "The provider preference could not be cleared. Try again.",
        "error"
      );
    } finally {
      state.preferenceSaving = false;
      button.disabled = false;
      saveButton.disabled = false;
      button.textContent = "Clear preference";
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

  async function saveTaskRoute(workloadId, selectedValue) {
    if (state.routeSavingWorkload) return;
    const routeIndex = state.routing.workloads.findIndex((route) => (
      route.workloadId === workloadId
    ));
    if (routeIndex < 0) return;
    const route = state.routing.workloads[routeIndex];
    if (route.executionMode !== "qualified_provider_model") return;

    let selectedOption = null;
    let useRecommended = false;
    if (selectedValue === applyLensRecommendedRouteValue) {
      useRecommended = true;
    } else {
      const match = /^qualified:(0|[1-9]\d*)$/.exec(String(selectedValue || ""));
      const selectedIndex = match ? Number(match[1]) : -1;
      selectedOption = Number.isSafeInteger(selectedIndex)
        ? route.qualifiedOptions[selectedIndex]
        : null;
      if (!selectedOption) {
        state.routeMessages.set(workloadId, {
          message: "Choose a current qualified route and try again.",
          tone: "error",
        });
        renderRouting();
        return;
      }
    }

    state.routeSavePresentationVersion += 1;
    const presentationVersion = state.routeSavePresentationVersion;
    state.routeSavedWorkload = null;
    state.routeSavingWorkload = workloadId;
    state.routeMessages.delete(workloadId);
    renderRouting();
    try {
      const path = `/ai/settings/task-routes/${encodeURIComponent(workloadId)}`;
      const result = useRecommended
        ? await requestJson(path, { method: "DELETE" })
        : await requestJson(path, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            provider: selectedOption.provider,
            model: selectedOption.model,
          }),
        });
      const updatedRoute = validateTaskRouteWriteResponse(result, workloadId);
      state.routing = {
        workloads: state.routing.workloads.map((existingRoute, index) => (
          index === routeIndex ? updatedRoute : existingRoute
        )),
      };
      state.routeMessages.set(workloadId, {
        message: useRecommended
          ? "ApplyLens Recommended is now effective."
          : "Explicit qualified route saved.",
        tone: "success",
      });
      state.routeSavedWorkload = workloadId;
      window.setTimeout(() => {
        if (state.routeSavePresentationVersion !== presentationVersion
          || state.routeSavedWorkload !== workloadId) return;
        state.routeSavedWorkload = null;
        renderRouting();
      }, 1800);
    } catch (error) {
      state.routeSavedWorkload = null;
      const category = error && error.category ? error.category : "request_failed";
      state.routeMessages.set(workloadId, {
        message: safeFailureMessages[category] || "The task route could not be saved. Try again.",
        tone: "error",
      });
    } finally {
      state.routeSavingWorkload = null;
      renderRouting();
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
    byId("aiPreferredProviderClearBtn").addEventListener("click", clearPreferredProvider);
    byId("aiTestProviderSelect").addEventListener("change", renderConnectionModels);
    byId("aiTestModelSelect").addEventListener("change", updateConnectionButton);
    byId("aiConnectionTestBtn").addEventListener("click", testConnection);
    byId("aiTaskRoutingList").addEventListener("click", (event) => {
      const trigger = event.target.closest("[data-route-save]");
      if (!trigger) return;
      const row = trigger.closest(
        ".profile-ai-settings-routing-row[data-workload-id]"
      );
      const select = row ? row.querySelector("[data-route-select]") : null;
      const workloadId = trigger.dataset.workloadId;
      if (!row || !select || row.dataset.workloadId !== workloadId) return;
      saveTaskRoute(workloadId, select.value);
    });
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
