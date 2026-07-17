(function initializePreferencesWorkflow(global) {
  "use strict";

  const STEP_COUNT = 5;
  const SENIORITY_LABELS = {
    entry: "Entry",
    mid: "Mid",
    senior: "Senior",
    staff: "Staff",
  };

  function uniqueStrings(values) {
    return (Array.isArray(values) ? values : [])
      .map((value) => String(value || "").trim())
      .filter(Boolean)
      .filter((value, index, items) => items.indexOf(value) === index);
  }

  function summaryText(values, emptyText, limit = 3) {
    const items = uniqueStrings(values);
    if (!items.length) return emptyText;
    if (items.length <= limit) return items.join(", ");
    return `${items.slice(0, limit).join(", ")} +${items.length - limit} more`;
  }

  function stepVisualState(step, currentStep) {
    const stepIndex = Number(step);
    const activeIndex = Number(currentStep);
    if (stepIndex === activeIndex) return "is-active";
    if (stepIndex < activeIndex) return "is-complete";
    return "is-upcoming";
  }

  function create(root, options = {}) {
    if (!root) return null;
    const form = root.querySelector("[data-preferences-form]");
    if (!form) return null;

    const panels = Array.from(form.querySelectorAll("[data-preferences-step]"));
    const stepButtons = Array.from(form.querySelectorAll("[data-preferences-step-target]"));
    const backButton = form.querySelector("[data-preferences-back]");
    const nextButton = form.querySelector("[data-preferences-next]");
    const finalActions = form.querySelector("[data-preferences-final-actions]");
    const mobileCompletion = form.querySelector("[data-preferences-mobile-completion]");
    const roleError = form.querySelector("[data-preferences-role-error]");
    let currentStep = 0;
    let maximumVisitedStep = 0;

    function values() {
      if (typeof options.getValues !== "function") return {};
      return options.getValues() || {};
    }

    function selectedRoleNames() {
      return Array.from(form.querySelectorAll('input[name="selected_role_families"]:checked'))
        .map((input) => input.closest(".onboarding-role-card")?.querySelector(".onboarding-role-card-title")?.textContent)
        .map((value) => String(value || "").trim())
        .filter(Boolean);
    }

    function selectedSeniorityNames(payload) {
      return uniqueStrings(payload.target_seniority).map((value) => SENIORITY_LABELS[value] || value);
    }

    function summaryModel() {
      const payload = values();
      const roleNames = selectedRoleNames();
      const seniorityNames = selectedSeniorityNames(payload);
      const locationNames = uniqueStrings(
        Array.isArray(payload.preferred_location_specs) && payload.preferred_location_specs.length
          ? payload.preferred_location_specs.map((item) => item?.display_name)
          : payload.preferred_locations
      );
      const strict = payload.location_strict_match === true;
      const fallback = strict && payload.location_show_others_if_unmatched === true;
      const skills = uniqueStrings(payload.preferred_skills);
      const excluded = uniqueStrings(payload.excluded_keywords);
      const completionPercent = (
        (roleNames.length ? 30 : 0)
        + (seniorityNames.length ? 20 : 0)
        + (locationNames.length ? 25 : 0)
        + (skills.length ? 15 : 0)
        + (excluded.length ? 10 : 0)
      );

      return {
        roles: summaryText(roleNames, "None selected", 3),
        seniority: summaryText(seniorityNames, "Not selected", 4),
        locations: summaryText(locationNames, "No preferred locations", 3),
        policy: strict
          ? (fallback ? "Strict locations with US fallback" : "Strict preferred locations only")
          : "Flexible matching",
        skills: summaryText(skills, "None added", 3),
        excluded: summaryText(excluded, "None added", 3),
        completionPercent,
      };
    }

    function setSummaryValue(name, value) {
      root.querySelectorAll(`[data-preferences-summary="${name}"], [data-preferences-review="${name}"]`)
        .forEach((node) => { node.textContent = value; });
    }

    function updateStepSummaries() {
      const summaries = Array.from({ length: STEP_COUNT }, (_, index) => {
        const state = stepVisualState(index, currentStep);
        if (state === "is-active") return "In progress";
        if (state === "is-complete") return "Complete";
        return "Not started";
      });
      summaries.forEach((value, index) => {
        root.querySelectorAll(`[data-preferences-step-summary="${index}"]`)
          .forEach((node) => { node.textContent = value; });
      });
    }

    function update() {
      const model = summaryModel();
      ["roles", "seniority", "locations", "policy", "skills", "excluded"].forEach((name) => {
        setSummaryValue(name, model[name]);
      });
      root.querySelectorAll("[data-preferences-summary-completion]")
        .forEach((node) => { node.textContent = `${model.completionPercent}%`; });
      root.querySelectorAll("[data-preferences-completion-bar]")
        .forEach((node) => { node.style.width = `${model.completionPercent}%`; });
      updateStepSummaries();
    }

    function showStep(step, { focus = true } = {}) {
      const nextStep = Math.max(0, Math.min(STEP_COUNT - 1, Number(step) || 0));
      currentStep = nextStep;
      maximumVisitedStep = Math.max(maximumVisitedStep, nextStep);

      panels.forEach((panel) => {
        const isActive = Number(panel.dataset.preferencesStep) === nextStep;
        panel.hidden = !isActive;
        panel.classList.toggle("is-active", isActive);
      });

      stepButtons.forEach((button) => {
        const buttonStep = Number(button.dataset.preferencesStepTarget);
        const state = stepVisualState(buttonStep, nextStep);
        button.classList.toggle("is-active", state === "is-active");
        button.classList.toggle("is-complete", state === "is-complete");
        button.classList.toggle("is-upcoming", state === "is-upcoming");
        button.setAttribute("aria-current", state === "is-active" ? "step" : "false");
      });

      if (backButton) backButton.disabled = nextStep === 0;
      if (nextButton) nextButton.classList.toggle("hidden", nextStep === STEP_COUNT - 1);
      finalActions?.classList.toggle("hidden", nextStep !== STEP_COUNT - 1);
      if (mobileCompletion) mobileCompletion.textContent = `Step ${nextStep + 1} of ${STEP_COUNT}`;
      update();

      if (focus) {
        panels[nextStep]?.querySelector("h2")?.focus({ preventScroll: true });
        const reducedMotion = global.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches;
        panels[nextStep]?.scrollIntoView({ block: "start", behavior: reducedMotion ? "auto" : "smooth" });
      }
    }

    function showValidationError(message, step = 0) {
      if (roleError) {
        roleError.textContent = String(message || "Select at least one role family before saving.");
        roleError.classList.remove("hidden");
      }
      showStep(step, { focus: false });
      roleError?.focus();
    }

    function clearValidationError() {
      roleError?.classList.add("hidden");
    }

    form.addEventListener("click", (event) => {
      const stepTarget = event.target.closest("[data-preferences-step-target]");
      if (stepTarget && form.contains(stepTarget)) {
        showStep(Number(stepTarget.dataset.preferencesStepTarget));
        return;
      }
      const editTarget = event.target.closest("[data-preferences-edit-step]");
      if (editTarget && form.contains(editTarget)) {
        showStep(Number(editTarget.dataset.preferencesEditStep));
      }
    });

    backButton?.addEventListener("click", () => showStep(currentStep - 1));
    nextButton?.addEventListener("click", () => showStep(currentStep + 1));
    form.addEventListener("input", update);
    form.addEventListener("change", update);
    showStep(0, { focus: false });

    return {
      showStep,
      update,
      showValidationError,
      clearValidationError,
      getCurrentStep: () => currentStep,
      getMaximumVisitedStep: () => maximumVisitedStep,
    };
  }

  global.ApplyLensPreferencesWorkflow = { create, stepVisualState };
})(window);
