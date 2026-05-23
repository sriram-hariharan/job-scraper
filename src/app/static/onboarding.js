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

function setCheckedValues(name, values) {
  const selected = new Set(Array.isArray(values) ? values.map(String) : []);
  document.querySelectorAll(`input[name="${name}"]`).forEach((input) => {
    input.checked = selected.has(String(input.value || ""));
  });
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
  return {
    onboarding_completed: Boolean(onboardingCompleted),
    selected_role_families: checkedValues("selected_role_families"),
    target_seniority: checkedValues("target_seniority"),
    preferred_locations: splitPreferenceList(onboardingQs("preferredLocationsInput")?.value),
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
  const resumeCallout = onboardingQs("onboardingResumeCallout");
  const saveStatus = onboardingQs("onboardingSaveStatus");
  const completeBtn = onboardingQs("onboardingCompleteBtn");

  const profileResumeCount = Number(onboardingRequirementState.profile_resume_count || 0);
  const hasResume = Boolean(onboardingRequirementState.has_profile_resume);
  const selectedRoleCount = checkedValues("selected_role_families").length;
  const canComplete = hasResume && selectedRoleCount > 0;

  if (resumeStatus) {
    resumeStatus.textContent = hasResume
      ? `${profileResumeCount} profile resume${profileResumeCount === 1 ? "" : "s"} ready.`
      : "No profile resume found yet.";
  }

  if (resumePanel) {
    resumePanel.classList.toggle("is-complete", hasResume);
  }

  if (resumeCallout) {
    const strong = resumeCallout.querySelector("strong");
    const detail = resumeCallout.querySelector("span");
    if (strong) {
      strong.textContent = hasResume ? "Resume requirement satisfied." : "Upload at least one profile resume.";
    }
    if (detail) {
      detail.textContent = hasResume
        ? "You can still open your profile to manage or replace resumes."
        : "Resume files stay in the existing profile resume storage and are not stored locally by onboarding.";
    }
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
  setTextareaList("preferredLocationsInput", preferences?.preferred_locations || []);
  setTextareaList("preferredSkillsInput", preferences?.preferred_skills || []);
  setTextareaList("excludedKeywordsInput", preferences?.excluded_keywords || []);
}

async function loadOnboardingPreferences() {
  const saveStatus = onboardingQs("onboardingSaveStatus");
  try {
    const payload = await onboardingFetchJson("/onboarding/preferences");
    hydrateOnboardingForm(payload.preferences || {});
    renderRequirementStatus(payload.requirements || {});
  } catch (error) {
    if (saveStatus) {
      saveStatus.textContent = `Could not load onboarding preferences. ${error.message}`;
    }
  }
}

async function saveOnboardingPreferences(onboardingCompleted) {
  const saveStatus = onboardingQs("onboardingSaveStatus");
  const completeBtn = onboardingQs("onboardingCompleteBtn");
  const draftBtn = onboardingQs("onboardingSaveDraftBtn");

  const preferences = collectOnboardingPreferences(onboardingCompleted);
  if (onboardingCompleted && preferences.selected_role_families.length === 0) {
    renderRequirementStatus({});
    return;
  }

  if (completeBtn) completeBtn.disabled = true;
  if (draftBtn) draftBtn.disabled = true;
  if (saveStatus) saveStatus.textContent = onboardingCompleted ? "Completing onboarding..." : "Saving preferences...";

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
    if (onboardingCompleted) {
      window.location.href = "/";
    }
  } catch (error) {
    if (saveStatus) saveStatus.textContent = error.message;
    renderRequirementStatus({});
  } finally {
    if (draftBtn) draftBtn.disabled = false;
    renderRequirementStatus({});
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const form = onboardingQs("onboardingForm");
  const draftBtn = onboardingQs("onboardingSaveDraftBtn");

  document.querySelectorAll("#onboardingForm input, #onboardingForm textarea").forEach((field) => {
    field.addEventListener("change", () => {
      renderRequirementStatus({});
    });
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

  loadOnboardingPreferences();
});
