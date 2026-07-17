(function initializePreferenceLocationSelector(global) {
  "use strict";

  const SEARCH_DELAY_MS = 140;

  function normalizeText(value) {
    return String(value || "").trim().replace(/\s+/g, " ").toLowerCase();
  }

  function legacySpec(displayName) {
    const cleaned = String(displayName || "").trim().replace(/\s+/g, " ");
    const slug = normalizeText(cleaned)
      .normalize("NFKD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "");
    if (!cleaned || !slug) return null;
    return {
      id: `legacy:${slug}`,
      type: "legacy_text",
      display_name: cleaned,
      legacy_text: normalizeText(cleaned),
      country_code: "US",
    };
  }

  function create(root, options = {}) {
    if (!root) return null;
    const input = root.querySelector("[data-location-search]");
    const results = root.querySelector("[data-location-results]");
    const chips = root.querySelector("[data-location-chips]");
    const selectionEmpty = root.querySelector("[data-location-selection-empty]");
    const status = root.querySelector("[data-location-status]");
    const count = root.querySelector("[data-location-count]");
    const strict = root.querySelector("[data-location-strict]");
    const fallback = root.querySelector("[data-location-fallback]");
    const fallbackRow = root.querySelector("[data-location-fallback-row]");
    if (!input || !results || !chips || !status || !strict || !fallback) return null;

    let selected = [];
    let suggestions = [];
    let activeIndex = -1;
    let searchTimer = null;
    let searchRequest = null;
    let placementListenersActive = false;

    function updateResultsPlacement() {
      if (results.classList.contains("hidden")) return;
      const inputRect = input.getBoundingClientRect();
      const viewportHeight = global.innerHeight || document.documentElement.clientHeight;
      const spaceBelow = Math.max(0, viewportHeight - inputRect.bottom - 16);
      const spaceAbove = Math.max(0, inputRect.top - 16);
      const opensUpward = spaceBelow < 180 && spaceAbove > spaceBelow;
      const availableSpace = opensUpward ? spaceAbove : spaceBelow;
      const boundedHeight = Math.max(120, Math.min(320, availableSpace - 8));
      results.classList.toggle("opens-upward", opensUpward);
      results.style.setProperty(
        "--preference-location-results-max-height",
        `${Math.floor(boundedHeight)}px`
      );
    }

    function startPlacementTracking() {
      if (placementListenersActive) return;
      global.addEventListener("resize", updateResultsPlacement);
      global.addEventListener("scroll", updateResultsPlacement, true);
      placementListenersActive = true;
    }

    function stopPlacementTracking() {
      if (!placementListenersActive) return;
      global.removeEventListener("resize", updateResultsPlacement);
      global.removeEventListener("scroll", updateResultsPlacement, true);
      placementListenersActive = false;
    }

    function announce(message) {
      status.textContent = message;
    }

    function notifyChange() {
      if (typeof options.onChange === "function") options.onChange(serialize());
    }

    function closeResults() {
      stopPlacementTracking();
      results.classList.add("hidden");
      results.classList.remove("opens-upward");
      results.style.removeProperty("--preference-location-results-max-height");
      results.replaceChildren();
      input.setAttribute("aria-expanded", "false");
      input.removeAttribute("aria-activedescendant");
      suggestions = [];
      activeIndex = -1;
    }

    function updateActiveOption() {
      const optionNodes = Array.from(results.querySelectorAll('[role="option"]'));
      optionNodes.forEach((node, index) => {
        const active = index === activeIndex;
        node.classList.toggle("is-active", active);
        node.setAttribute("aria-selected", node.dataset.locationSelected === "true" ? "true" : "false");
      });
      const activeNode = optionNodes[activeIndex];
      if (activeNode) {
        input.setAttribute("aria-activedescendant", activeNode.id);
        activeNode.scrollIntoView({ block: "nearest" });
      } else {
        input.removeAttribute("aria-activedescendant");
      }
    }

    function renderSuggestions(items) {
      const selectedIds = new Set(selected.map((item) => item.id));
      suggestions = items.filter(Boolean);
      results.replaceChildren();
      activeIndex = suggestions.length ? 0 : -1;

      if (!suggestions.length) {
        const empty = document.createElement("div");
        empty.className = "preference-location-empty";
        empty.textContent = "No locations found. Try a city, state, Remote, or United States.";
        results.appendChild(empty);
        announce("No matching locations found.");
      } else {
        suggestions.forEach((item, index) => {
          const isSelected = selectedIds.has(String(item.id || ""));
          const optionNode = document.createElement("button");
          optionNode.type = "button";
          optionNode.id = `${results.id}-option-${index}`;
          optionNode.className = `preference-location-option${isSelected ? " is-selected" : ""}`;
          optionNode.setAttribute("role", "option");
          optionNode.setAttribute("aria-selected", isSelected ? "true" : "false");
          optionNode.dataset.locationOptionIndex = String(index);
          optionNode.dataset.locationSelected = isSelected ? "true" : "false";

          const check = document.createElement("span");
          check.className = "preference-location-option-check";
          check.setAttribute("aria-hidden", "true");
          check.textContent = "✓";
          const label = document.createElement("span");
          label.className = "preference-location-option-label";
          label.textContent = String(item.display_name || "");
          const type = document.createElement("span");
          type.className = "preference-location-option-type";
          type.textContent = item.type === "city" ? "City" : item.type === "state" ? "State" : "US";
          optionNode.append(check, label, type);
          results.appendChild(optionNode);
        });
        announce(`${suggestions.length} location suggestion${suggestions.length === 1 ? "" : "s"} available.`);
      }

      results.classList.remove("hidden");
      input.setAttribute("aria-expanded", "true");
      startPlacementTracking();
      updateResultsPlacement();
      updateActiveOption();
    }

    function renderSelected() {
      chips.replaceChildren();
      selected.forEach((item) => {
        const chip = document.createElement("span");
        chip.className = `preference-location-chip${item.type === "legacy_text" ? " is-legacy" : ""}`;
        const label = document.createElement("span");
        label.textContent = String(item.display_name || "");
        const remove = document.createElement("button");
        remove.type = "button";
        remove.className = "preference-location-chip-remove";
        remove.dataset.locationRemoveId = String(item.id || "");
        remove.setAttribute("aria-label", `Remove ${String(item.display_name || "location")}`);
        remove.textContent = "×";
        chip.append(label, remove);
        chips.appendChild(chip);
      });
      selectionEmpty?.classList.toggle("hidden", selected.length > 0);
      count.textContent = `${selected.length} selected`;
      if (!input.value.trim()) {
        announce(
          selected.length
            ? `${selected.length} preferred location${selected.length === 1 ? "" : "s"} selected.`
            : "No preferred locations selected."
        );
      }
    }

    function updatePolicyState({ notify = false } = {}) {
      const strictEnabled = Boolean(strict.checked);
      fallback.disabled = !strictEnabled;
      fallbackRow?.classList.toggle("is-disabled", !strictEnabled);
      if (!strictEnabled) fallback.checked = false;
      if (notify) notifyChange();
    }

    function addSelection(item) {
      const id = String(item?.id || "");
      if (!id) return;
      if (selected.some((existing) => existing.id === id)) {
        announce(`${String(item.display_name || "Location")} is already selected.`);
        return;
      }
      selected.push({ ...item });
      input.value = "";
      closeResults();
      renderSelected();
      announce(`${String(item.display_name || "Location")} selected.`);
      notifyChange();
      input.focus();
    }

    function removeSelection(id) {
      const index = selected.findIndex((item) => item.id === id);
      if (index < 0) return;
      const [removed] = selected.splice(index, 1);
      renderSelected();
      announce(`${String(removed.display_name || "Location")} removed.`);
      notifyChange();
    }

    async function search(query) {
      if (searchRequest) searchRequest.abort();
      searchRequest = new AbortController();
      root.classList.add("is-searching");
      announce("Searching locations...");
      try {
        const params = new URLSearchParams({ q: query, limit: "15" });
        const response = await fetch(`/onboarding/location-search?${params.toString()}`, {
          credentials: "same-origin",
          headers: { Accept: "application/json" },
          signal: searchRequest.signal,
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(String(payload.detail || `Search failed: ${response.status}`));
        if (input.value.trim() !== query) return;
        renderSuggestions(Array.isArray(payload.results) ? payload.results : []);
      } catch (error) {
        if (error.name === "AbortError") return;
        closeResults();
        announce("Location search is unavailable. Your current selections are unchanged.");
      } finally {
        root.classList.remove("is-searching");
      }
    }

    function scheduleSearch() {
      window.clearTimeout(searchTimer);
      const query = input.value.trim();
      if (!query) {
        if (searchRequest) searchRequest.abort();
        closeResults();
        renderSelected();
        return;
      }
      searchTimer = window.setTimeout(() => search(query), SEARCH_DELAY_MS);
    }

    function setPreferences(preferences = {}) {
      const specs = Array.isArray(preferences.preferred_location_specs)
        ? preferences.preferred_location_specs.filter((item) => item && item.id && item.display_name)
        : [];
      const next = specs.map((item) => ({ ...item }));
      const seenIds = new Set(next.map((item) => String(item.id)));
      const seenLabels = new Set(next.map((item) => normalizeText(item.display_name)));
      (Array.isArray(preferences.preferred_locations) ? preferences.preferred_locations : []).forEach((value) => {
        if (seenLabels.has(normalizeText(value))) return;
        const legacy = legacySpec(value);
        if (!legacy || seenIds.has(legacy.id)) return;
        seenIds.add(legacy.id);
        seenLabels.add(normalizeText(legacy.display_name));
        next.push(legacy);
      });
      selected = next;
      strict.checked = preferences.location_strict_match === true;
      fallback.checked = strict.checked && preferences.location_show_others_if_unmatched === true;
      updatePolicyState();
      renderSelected();
    }

    function serialize() {
      const specs = selected.map((item) => ({ ...item }));
      return {
        preferred_locations: specs.map((item) => String(item.display_name || "")),
        preferred_location_specs: specs,
        location_strict_match: Boolean(strict.checked),
        location_show_others_if_unmatched: Boolean(strict.checked && fallback.checked),
      };
    }

    input.addEventListener("input", scheduleSearch);
    input.addEventListener("keydown", (event) => {
      if (event.key === "ArrowDown" && suggestions.length) {
        event.preventDefault();
        activeIndex = (activeIndex + 1) % suggestions.length;
        updateActiveOption();
      } else if (event.key === "ArrowUp" && suggestions.length) {
        event.preventDefault();
        activeIndex = (activeIndex - 1 + suggestions.length) % suggestions.length;
        updateActiveOption();
      } else if (event.key === "Enter" && activeIndex >= 0 && suggestions[activeIndex]) {
        event.preventDefault();
        addSelection(suggestions[activeIndex]);
      } else if (event.key === "Escape") {
        closeResults();
      } else if (event.key === "Backspace" && !input.value && selected.length) {
        removeSelection(selected[selected.length - 1].id);
      }
    });
    results.addEventListener("click", (event) => {
      const optionNode = event.target.closest("[data-location-option-index]");
      if (!optionNode || !results.contains(optionNode)) return;
      addSelection(suggestions[Number(optionNode.dataset.locationOptionIndex)]);
    });
    chips.addEventListener("click", (event) => {
      const remove = event.target.closest("[data-location-remove-id]");
      if (remove) removeSelection(String(remove.dataset.locationRemoveId || ""));
    });
    strict.addEventListener("change", () => updatePolicyState({ notify: true }));
    fallback.addEventListener("change", notifyChange);
    function handleDocumentPointerDown(event) {
      if (!root.contains(event.target)) closeResults();
    }

    document.addEventListener("pointerdown", handleDocumentPointerDown);

    updatePolicyState();
    renderSelected();
    function destroy() {
      global.clearTimeout(searchTimer);
      searchRequest?.abort();
      stopPlacementTracking();
      document.removeEventListener("pointerdown", handleDocumentPointerDown);
      closeResults();
    }

    return { setPreferences, serialize, destroy };
  }

  global.ApplyLensLocationSelector = { create };
})(window);
