const profileState = {
  pendingDeleteResumeName: null,
  pendingDeleteScanId: null,
  savedScans: [],
  savedScansQuery: "",
  currentUser: null,
  adminUsers: [],
  pipelineRuns: [],
  pipelineRunsPage: 1,
  pipelineRunsPageSize: 15,
  pipelineRunsTotalCount: 0,
  pipelineRunsTotalPages: 1,
  pipelineRunsHasPrevious: false,
  pipelineRunsHasNext: false,
  resumeRoleFamilies: [],
  resumeRoleMappings: [],
  activeRoleResumeName: null,
  onboardingPreferences: null,
  onboardingRequirements: {},
  preferencesLoaded: false,
  pendingAccessUserId: null,
  pendingAccessValue: null,
  pendingDeleteUserId: null,
  pendingRerunRunId: null,
};

const PROFILE_PLANNING_OUTPUT_DIR = "outputs/application_planning";
const PROFILE_PLANNING_LOG_PATH = `${PROFILE_PLANNING_OUTPUT_DIR}/live_pipeline_run.log`;
let profileLocationSelector = null;
let profilePreferencesWorkflow = null;
let profilePreferencesSaving = false;

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

async function postJson(url, payload = {}) {
  return fetchJson(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}

function splitProfilePreferenceList(value) {
  return String(value || "")
    .split(/[\n,]/)
    .map((item) => item.trim())
    .filter(Boolean)
    .filter((item, index, items) => items.indexOf(item) === index);
}

function profilePreferenceCheckedValues(name) {
  const form = qs("profilePreferencesForm");
  if (!form) return [];
  return Array.from(form.querySelectorAll(`input[name="${name}"]:checked`))
    .map((input) => String(input.value || "").trim())
    .filter(Boolean);
}

function setProfilePreferenceCheckedValues(name, values) {
  const form = qs("profilePreferencesForm");
  if (!form) return;
  const selected = new Set(Array.isArray(values) ? values.map(String) : []);
  form.querySelectorAll(`input[name="${name}"]`).forEach((input) => {
    input.checked = selected.has(String(input.value || ""));
  });
}

function setProfilePreferenceCheckboxGroup(name, checked) {
  const form = qs("profilePreferencesForm");
  if (!form) return;
  form.querySelectorAll(`input[name="${name}"]`).forEach((input) => {
    input.checked = Boolean(checked);
  });
}

function setProfilePreferenceTextareaList(id, values) {
  const input = qs(id);
  if (!input) return;
  input.value = Array.isArray(values) ? values.join(", ") : "";
}

function getBinaryToggleBool(name) {
  return document.querySelector(`input[name='${name}']:checked`)?.value === "yes";
}

function showProfilePlanningUploadCallout() {
  qs("profilePlanningUploadCallout")?.classList.remove("hidden");
}

function getProfilePlanningOptionsModal() {
  return qs("profilePlanningOptionsModal");
}

function openProfilePlanningOptionsModal() {
  getProfilePlanningOptionsModal()?.classList.remove("hidden");
}

function closeProfilePlanningOptionsModal() {
  getProfilePlanningOptionsModal()?.classList.add("hidden");
}

function setProfilePlanningOptions(value) {
  [
    "profilePlanningOnly",
    "profileGenerateTailoring",
    "profileGenerateLlmTailoring",
    "profileRefreshLlmTailoring",
    "profileGenerateLlmFallback",
    "profileGenerateLlmAdjudication",
  ].forEach((name) => {
    const input = document.querySelector(`input[name='${name}'][value='${value ? "yes" : "no"}']`);
    if (input) input.checked = true;
  });
}

function collectProfilePlanningUpdatePayload() {
  return {
    planning_only: getBinaryToggleBool("profilePlanningOnly"),
    generate_tailoring: getBinaryToggleBool("profileGenerateTailoring"),
    generate_llm_tailoring: getBinaryToggleBool("profileGenerateLlmTailoring"),
    refresh_llm_tailoring: getBinaryToggleBool("profileRefreshLlmTailoring"),
    generate_llm_fallback: getBinaryToggleBool("profileGenerateLlmFallback"),
    generate_llm_adjudication: getBinaryToggleBool("profileGenerateLlmAdjudication"),
    delete_seen_data: "no",
    output_dir: PROFILE_PLANNING_OUTPUT_DIR,
    log_path: PROFILE_PLANNING_LOG_PATH,
    job_limit: 50,
    job_packet_limit: 0,
    llm_actions: ["APPLY", "APPLY_REVIEW_VARIANTS", "MAYBE_TAILOR"],
  };
}

async function runProfilePlanningUpdate() {
  const button = qs("runProfilePlanningUpdateBtn");
  if (button) button.disabled = true;
  setStatus("Starting planning update...", "info");
  try {
    await postJson("/pipeline/run", collectProfilePlanningUpdatePayload());
    closeProfilePlanningOptionsModal();
    setStatus("Planning update started. Open Executive Queue to watch progress.", "success");
  } catch (err) {
    setStatus(err.message, "error");
  } finally {
    if (button) button.disabled = false;
  }
}

function setProfilePreferencesStatus(message, tone = "info") {
  const banner = qs("profilePreferencesStatusBanner");
  if (!banner) return;
  banner.textContent = message || "";
  banner.className = `preferences-save-confirmation ${tone}`;
  if (!message) {
    banner.classList.add("hidden");
  }
}

function updateProfilePreferencesSummary() {
  const summary = qs("profilePreferencesConfigurationSummary");
  if (!summary) return;
  const roleCount = profilePreferenceCheckedValues("selected_role_families").length;
  const locationCount = profileLocationSelector?.serialize().preferred_location_specs.length || 0;
  summary.textContent = `${roleCount} role ${roleCount === 1 ? "family" : "families"} · ${locationCount} preferred location${locationCount === 1 ? "" : "s"}`;
  profilePreferencesWorkflow?.update();
}

function setProfilePreferencesChangeState(label, state = "saved") {
  const indicator = qs("profilePreferencesChangeState");
  if (!indicator) return;
  indicator.textContent = label;
  indicator.className = `preferences-save-state is-${state}`;
  profilePreferencesWorkflow?.update();
}

function markProfilePreferencesDirty() {
  if (profilePreferenceCheckedValues("selected_role_families").length) profilePreferencesWorkflow?.clearValidationError();
  profilePreferencesWorkflow?.setCompleted(false);
  setProfilePreferencesStatus("");
  updateProfilePreferencesSummary();
  setProfilePreferencesChangeState("Unsaved changes", "dirty");
}

function syncProfileSeniorityStrictToggle() {
  const strictToggle = qs("profilePreferencesForm")?.querySelector(
    'input[name="seniority_strict_match"]'
  );
  if (!strictToggle) return;
  const hasSeniority = profilePreferenceCheckedValues("target_seniority").length > 0;
  strictToggle.disabled = !hasSeniority;
  if (!hasSeniority) strictToggle.checked = false;
}

function hydrateProfilePreferencesForm(preferences) {
  setProfilePreferenceCheckedValues("selected_role_families", preferences?.selected_role_families || []);
  setProfilePreferenceCheckedValues("target_seniority", preferences?.target_seniority || []);
  const strictToggle = qs("profilePreferencesForm")?.querySelector(
    'input[name="seniority_strict_match"]'
  );
  if (strictToggle) strictToggle.checked = preferences?.seniority_strict_match === true;
  syncProfileSeniorityStrictToggle();
  profileLocationSelector?.setPreferences(preferences || {});
  setProfilePreferenceTextareaList("profilePreferredSkillsInput", preferences?.preferred_skills || []);
  setProfilePreferenceTextareaList("profileExcludedKeywordsInput", preferences?.excluded_keywords || []);
}

function collectProfilePreferences() {
  syncProfileSeniorityStrictToggle();
  const current = profileState.onboardingPreferences || {};
  const locationPreferences = profileLocationSelector?.serialize() || {
    preferred_locations: [],
    preferred_location_specs: [],
    location_strict_match: false,
    location_show_others_if_unmatched: false,
  };
  return {
    onboarding_completed: Boolean(current.onboarding_completed),
    selected_role_families: profilePreferenceCheckedValues("selected_role_families"),
    target_seniority: profilePreferenceCheckedValues("target_seniority"),
    seniority_strict_match: Boolean(
      qs("profilePreferencesForm")?.querySelector('input[name="seniority_strict_match"]')?.checked
    ),
    ...locationPreferences,
    preferred_skills: splitProfilePreferenceList(qs("profilePreferredSkillsInput")?.value),
    excluded_keywords: splitProfilePreferenceList(qs("profileExcludedKeywordsInput")?.value),
  };
}

async function loadProfilePreferences() {
  const form = qs("profilePreferencesForm");
  if (!form) return;
  const payload = await fetchJson("/onboarding/preferences");
  profileState.onboardingPreferences = payload.preferences || {};
  profileState.onboardingRequirements = payload.requirements || {};
  hydrateProfilePreferencesForm(profileState.onboardingPreferences);
  profileState.preferencesLoaded = true;
  profilePreferencesWorkflow?.setCompleted(true);
  updateProfilePreferencesSummary();
  setProfilePreferencesChangeState("All changes saved", "saved");
  setProfilePreferencesStatus("");
}

async function saveProfilePreferences() {
  const saveBtn = qs("profilePreferencesSaveBtn");
  if (profilePreferencesSaving) return;
  const preferences = collectProfilePreferences();
  if (!preferences.selected_role_families.length) {
    setProfilePreferencesStatus("Select at least one role family before saving.", "error");
    profilePreferencesWorkflow?.showValidationError("Select at least one role family before saving.", 0);
    return;
  }
  profilePreferencesWorkflow?.clearValidationError();
  profilePreferencesSaving = true;

  if (saveBtn) saveBtn.disabled = true;
  setProfilePreferencesStatus("");
  setProfilePreferencesChangeState("Saving...", "saving");
  try {
    const payload = await postJson("/onboarding/preferences", preferences);
    profileState.onboardingPreferences = payload.preferences || preferences;
    profileState.onboardingRequirements = payload.requirements || profileState.onboardingRequirements || {};
    hydrateProfilePreferencesForm(profileState.onboardingPreferences);
    profilePreferencesWorkflow?.setCompleted(true);
    updateProfilePreferencesSummary();
    setProfilePreferencesChangeState("All changes saved", "saved");
    setProfilePreferencesStatus("Preferences saved.", "success");
  } catch (err) {
    setProfilePreferencesStatus(err.message, "error");
    setProfilePreferencesChangeState("Save failed", "error");
  } finally {
    profilePreferencesSaving = false;
    if (saveBtn) saveBtn.disabled = false;
  }
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

function formatPipelineRunHeaderDate(value) {
  if (!value) return "Date unavailable";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function formatPipelineRunDuration(startedAt, completedAt) {
  const started = new Date(startedAt || "");
  const completed = new Date(completedAt || "");
  if (Number.isNaN(started.getTime()) || Number.isNaN(completed.getTime()) || completed < started) {
    return "Not available";
  }
  const totalMinutes = Math.max(0, Math.round((completed.getTime() - started.getTime()) / 60000));
  if (totalMinutes < 1) return "<1m";
  const days = Math.floor(totalMinutes / 1440);
  const hours = Math.floor((totalMinutes % 1440) / 60);
  const minutes = totalMinutes % 60;
  return [
    days ? `${days}d` : "",
    hours ? `${hours}h` : "",
    minutes ? `${minutes}m` : "",
  ].filter(Boolean).join(" ");
}

function formatPipelineRunMetricValue(value) {
  const number = Number(String(value ?? "").trim());
  return Number.isFinite(number) ? number.toLocaleString() : String(value ?? "-");
}

function formatResumeDate(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function formatPercent(value) {
  if (value === null || value === undefined || value === "") return "-";
  const number = Number(value);
  if (!Number.isFinite(number)) return "-";
  return `${Math.round(number)}%`;
}

function setStatus(message, tone = "info") {
  const banner = qs("resumeStatusBanner");
  if (!banner) return;
  banner.textContent = message || "";
  banner.className = `profile-inline-status ${tone}`;
  if (!message) {
    banner.classList.add("hidden");
  }
}

function clearStatus() {
  const banner = qs("resumeStatusBanner");
  if (!banner) return;
  banner.textContent = "";
  banner.className = "profile-inline-status hidden";
}

function setResumeUploadFeedback(message, tone = "info") {
  const feedback = qs("resumeUploadFeedback");
  if (!feedback) return;
  feedback.textContent = message || "";
  feedback.className = `profile-resume-modal-feedback ${tone}`;
  feedback.classList.toggle("hidden", !message);
}

function profileResumeFocusableElements(modal) {
  if (!modal) return [];
  return Array.from(modal.querySelectorAll(
    'button:not([disabled]), input:not([disabled]), [href], [tabindex]:not([tabindex="-1"])'
  )).filter((element) => !element.closest(".hidden"));
}

function openProfileResumeModal(modal, trigger, initialFocus) {
  if (!modal) return;
  if (modal._closeTimer) window.clearTimeout(modal._closeTimer);
  modal.classList.remove("is-closing");
  modal._returnFocus = trigger || document.activeElement;
  modal.classList.remove("hidden");
  document.body.classList.add("profile-resume-modal-open");
  window.requestAnimationFrame(() => {
    (initialFocus || profileResumeFocusableElements(modal)[0] || modal.querySelector(".modal-card"))?.focus();
  });
}

function closeProfileResumeModal(modal) {
  if (!modal || modal.classList.contains("hidden") || modal.classList.contains("is-closing")) return;
  const returnFocus = modal._returnFocus;
  const returnResumeName = modal.dataset.returnResumeName || "";
  const returnResumeAction = modal.dataset.returnResumeAction || "manage";
  delete modal.dataset.returnResumeName;
  delete modal.dataset.returnResumeAction;
  const finishClose = () => {
    modal.classList.remove("is-closing");
    modal.classList.add("hidden");
    modal._closeTimer = null;
    if (!document.querySelector(".profile-resume-modal:not(.hidden)")) {
      document.body.classList.remove("profile-resume-modal-open");
    }
    if (returnFocus && document.body.contains(returnFocus)) {
      returnFocus.focus();
    } else if (returnResumeName) {
      const selector = returnResumeAction === "delete"
        ? "[data-resume-delete]"
        : "[data-manage-resume-roles]";
      const replacement = Array.from(document.querySelectorAll(selector)).find((button) => {
        const resumeName = returnResumeAction === "delete"
          ? button.dataset.resumeDelete
          : button.dataset.manageResumeRoles;
        return resumeName === returnResumeName;
      });
      (replacement || qs("openResumeUploadModalBtn"))?.focus();
    } else {
      qs("openResumeUploadModalBtn")?.focus();
    }
  };
  modal.classList.add("is-closing");
  const reducedMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
  modal._closeTimer = window.setTimeout(finishClose, reducedMotion ? 0 : 110);
}

function trapProfileResumeModalFocus(event, modal) {
  const focusable = profileResumeFocusableElements(modal);
  if (!focusable.length) return;
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
}

function setAdminUsersStatus(message, tone = "info") {
  const banner = qs("adminUsersStatusBanner");
  if (!banner) return;
  banner.textContent = message || "";
  banner.className = `profile-inline-status ${tone}`;
  if (!message) {
    banner.classList.add("hidden");
  }
}

function setPipelineRunsStatus(message, tone = "info") {
  const banner = qs("pipelineRunsStatusBanner");
  if (!banner) return;
  banner.textContent = message || "";
  banner.className = `profile-inline-status ${tone}`;
  if (!message) {
    banner.classList.add("hidden");
  }
}

function isCurrentUserAdmin(user) {
  const accessLevel = String(user?.access_level || "").trim().toLowerCase();
  return Boolean(user?.is_admin) || accessLevel === "admin";
}

async function loadCurrentUser() {
  const data = await fetchJson("/auth/me");
  const user = data.user || null;
  profileState.currentUser = user;
  return user;
}

function adminUserDisplayName(user) {
  return String(user?.display_name || user?.email || "User").trim();
}

function getAdminUserById(userId) {
  return profileState.adminUsers.find((user) => String(user.user_id || "") === String(userId || ""));
}

function renderAccessSwitch(user) {
  const userId = escapeHtml(user.user_id || "");
  const active = Boolean(user.is_active);
  return `
    <button
      type="button"
      class="admin-user-access-switch ${active ? "is-authorized" : "is-revoked"}"
      role="switch"
      aria-checked="${active ? "true" : "false"}"
      data-admin-user-access="${userId}"
      data-next-active="${active ? "false" : "true"}"
    >
      <span class="admin-user-access-knob"></span>
      <span class="admin-user-access-label">${active ? "Authorized" : "Revoked"}</span>
    </button>
  `;
}

function renderAdminUsers(users) {
  const section = qs("profileAdminUsersSection");
  const tabs = qs("profileAdminTabs");
  const tbody = qs("adminUsersTableBody");
  const meta = qs("adminUsersMeta");
  if (!section || !tbody || !meta) return;

  const items = Array.isArray(users) ? users : [];
  profileState.adminUsers = items;
  if (tabs) tabs.classList.remove("hidden");
  meta.textContent = `${items.length} non-admin user${items.length === 1 ? "" : "s"} shown`;

  if (!items.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="8" class="admin-users-empty-cell">No non-admin users found.</td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = items.map((user) => {
    const active = Boolean(user.is_active);
    return `
      <tr data-admin-user-id="${escapeHtml(user.user_id || "")}">
        <td>
          <div class="admin-user-name">${escapeHtml(adminUserDisplayName(user))}</div>
          <div class="admin-user-id">${escapeHtml(user.user_id || "")}</div>
        </td>
        <td>${escapeHtml(user.email || "-")}</td>
        <td>${escapeHtml(user.access_level || "user")}</td>
        <td>
          <span class="admin-user-status ${active ? "is-active" : "is-revoked"}">
            ${active ? "Active" : "Revoked"}
          </span>
        </td>
        <td>${escapeHtml(formatDateTime(user.created_at || ""))}</td>
        <td>${escapeHtml(formatDateTime(user.last_login_at || "")) || "-"}</td>
        <td>${renderAccessSwitch(user)}</td>
        <td>
          <button
            type="button"
            class="admin-user-delete-btn"
            data-admin-user-delete="${escapeHtml(user.user_id || "")}"
          >
            Delete
          </button>
        </td>
      </tr>
    `;
  }).join("");
}

async function loadAdminUsers() {
  const section = qs("profileAdminUsersSection");
  if (!section) return;

  let user = profileState.currentUser;
  if (!user) {
    try {
      user = await loadCurrentUser();
    } catch {
      qs("profileAdminTabs")?.remove();
      section.remove();
      return;
    }
  }
  if (!isCurrentUserAdmin(user)) {
    qs("profileAdminTabs")?.remove();
    section.remove();
    return;
  }

  const meta = qs("adminUsersMeta");
  const tbody = qs("adminUsersTableBody");
  if (meta) meta.textContent = "Loading users...";
  if (tbody) {
    tbody.innerHTML = `<tr><td colspan="8" class="admin-users-empty-cell">Loading users...</td></tr>`;
  }
  setAdminUsersStatus("");

  const data = await fetchJson("/profile/admin/users?limit=100");
  renderAdminUsers(data.users || []);
}

function openAdminUserAccessModal(userId, nextActive) {
  const user = getAdminUserById(userId);
  if (!user) return;

  profileState.pendingAccessUserId = String(userId || "");
  profileState.pendingAccessValue = Boolean(nextActive);

  const action = nextActive ? "authorize" : "revoke";
  qs("adminUserAccessTitle").textContent = `${nextActive ? "Authorize" : "Revoke"} user access`;
  qs("adminUserAccessSubtitle").textContent = "Confirm before changing this account.";
  qs("adminUserAccessMessage").innerHTML = `
    ${action === "revoke"
      ? "Revoking access will disable this user and revoke their active sessions."
      : "Authorizing access will reactivate this user account."}
    <br />
    <strong>${escapeHtml(adminUserDisplayName(user))}</strong>
    <span>${escapeHtml(user.email || "")}</span>
  `;
  qs("adminUserAccessConfirmBtn").textContent = nextActive ? "Authorize" : "Revoke";
  qs("adminUserAccessConfirmBtn").classList.toggle("admin-user-revoke-confirm-btn", !nextActive);
  qs("adminUserAccessConfirmBtn").classList.toggle("admin-user-authorize-confirm-btn", nextActive);
  qs("adminUserAccessModal").classList.remove("hidden");
}

function closeAdminUserAccessModal() {
  profileState.pendingAccessUserId = null;
  profileState.pendingAccessValue = null;
  qs("adminUserAccessModal")?.classList.add("hidden");
}

function openAdminUserDeleteModal(userId) {
  const user = getAdminUserById(userId);
  if (!user) return;

  profileState.pendingDeleteUserId = String(userId || "");
  qs("adminUserDeleteMessage").innerHTML = `
    You are about to permanently delete
    <strong>${escapeHtml(adminUserDisplayName(user))}</strong>
    <span>${escapeHtml(user.email || "")}</span>
    from the backend users table.
  `;
  qs("adminUserDeleteModal").classList.remove("hidden");
}

function closeAdminUserDeleteModal() {
  profileState.pendingDeleteUserId = null;
  qs("adminUserDeleteModal")?.classList.add("hidden");
}

async function confirmAdminUserAccessChange() {
  const userId = profileState.pendingAccessUserId;
  const isActive = Boolean(profileState.pendingAccessValue);
  if (!userId) return;

  await fetchJson(`/profile/admin/users/${encodeURIComponent(userId)}/access`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ is_active: isActive }),
  });
  closeAdminUserAccessModal();
  await loadAdminUsers();
  setAdminUsersStatus(`User access ${isActive ? "authorized" : "revoked"}.`, "success");
}

async function confirmAdminUserDelete() {
  const userId = profileState.pendingDeleteUserId;
  if (!userId) return;

  await fetchJson(`/profile/admin/users/${encodeURIComponent(userId)}`, {
    method: "DELETE",
  });
  closeAdminUserDeleteModal();
  await loadAdminUsers();
  setAdminUsersStatus("User deleted.", "success");
}


function getPipelineRunById(runId) {
  return profileState.pipelineRuns.find((run) => String(run.run_id || "") === String(runId || ""));
}

function pipelineRunStatusLabel(status) {
  const value = String(status || "unknown").trim().toLowerCase();
  if (value === "succeeded") return "Succeeded";
  if (value === "failed") return "Failed";
  if (value === "cancelled") return "Cancelled";
  if (value === "running") return "Running";
  if (value === "queued") return "Queued";
  if (value === "starting") return "Starting";
  return value ? value.charAt(0).toUpperCase() + value.slice(1) : "Unknown";
}

function pipelineRunStatusTone(status) {
  const value = String(status || "").trim().toLowerCase();
  if (value === "succeeded") return "success";
  if (value === "failed" || value === "cancelled") return "danger";
  if (value === "running" || value === "queued" || value === "starting") return "running";
  return "muted";
}

const PIPELINE_RUN_OUTCOME_METRICS = [
  { keys: ["scraped_jobs", "scraped"], label: "Scraped Jobs", tone: "blue" },
  { keys: ["filtered_jobs", "filtered"], label: "Filtered Jobs", tone: "cyan" },
  { keys: ["deduped_jobs", "deduped"], label: "Unique Jobs", tone: "violet" },
  { keys: ["ranked_jobs", "ranked"], label: "Ranked Jobs", tone: "indigo" },
  { keys: ["new_jobs", "new"], label: "New Jobs", tone: "emerald" },
  { keys: ["detailed_jobs", "detailed"], label: "Detailed Jobs", tone: "sky" },
  { keys: ["intelligent_jobs", "intelligence"], label: "Intelligence Reviews", tone: "purple" },
  { keys: ["ai_jobs", "evaluable_jobs", "ai_eligible"], label: "AI Eligible Jobs", tone: "teal" },
  { keys: ["prefilter_jobs", "prefilter"], label: "Prefiltered Jobs", tone: "amber" },
  { keys: ["resume_matched_jobs", "resume_matched"], label: "Resume Matched Jobs", tone: "pink" },
  { keys: ["scored_jobs", "scored"], label: "Scored Jobs", tone: "lime" },
  { keys: ["rag_export_count", "rag_exported"], label: "RAG Exports", tone: "orange" },
  { keys: ["planning_packets_total"], label: "Planning Packets", tone: "slate" },
  { keys: ["planning_packets_generated"], label: "Generated Packets", tone: "green" },
  { keys: ["planning_packets_completed"], label: "Completed Packets", tone: "emerald" },
  { keys: ["planning_llm_generated"], label: "Generated Plans", tone: "blue" },
  { keys: ["planning_llm_failed"], label: "Failed Plans", tone: "rose" },
  { keys: ["planning_pending_variants"], label: "Pending Variants", tone: "amber" },
  { keys: ["planning_unresolved_missing_resume"], label: "Missing Resume Matches", tone: "rose" },
  { keys: ["planning_unresolved_no_credible_match"], label: "No Credible Match", tone: "rose" },
];

function getFirstMetricValue(counts, keys) {
  const source = counts && typeof counts === "object" ? counts : {};
  for (const key of keys) {
    if (source[key] !== undefined && source[key] !== null && source[key] !== "") {
      return source[key];
    }
  }
  return undefined;
}

function isDisplayableMetricValue(value) {
  if (typeof value === "boolean") return false;
  if (value === undefined || value === null || value === "") return false;
  if (typeof value === "number") return Number.isFinite(value);
  const text = String(value).trim();
  return /^-?\d+(\.\d+)?$/.test(text);
}

function formatMetricValue(value) {
  if (typeof value === "number") return String(value);
  const number = Number(String(value || "").trim());
  return Number.isFinite(number) ? String(number) : String(value || "-");
}

function getPipelineRunOutcomeMetrics(counts) {
  return PIPELINE_RUN_OUTCOME_METRICS
    .map((metric) => ({
      ...metric,
      value: getFirstMetricValue(counts, metric.keys),
    }))
    .filter((metric) => isDisplayableMetricValue(metric.value));
}

// The four highlighted outcome metrics, named by their existing config
// labels. These are chosen from PIPELINE_RUN_OUTCOME_METRICS only - never
// invented - and every metric not selected here still renders in the
// secondary list below the cards.
const PIPELINE_RUN_PRIMARY_METRIC_LABELS = [
  "Scraped Jobs",
  "Filtered Jobs",
  "Unique Jobs",
  "New Jobs",
];

function selectPipelineRunPrimaryMetrics(outcomeMetrics) {
  const byLabel = new Map(outcomeMetrics.map((metric) => [metric.label, metric]));
  const selected = PIPELINE_RUN_PRIMARY_METRIC_LABELS
    .map((label) => byLabel.get(label))
    .filter(Boolean);
  if (selected.length === PIPELINE_RUN_PRIMARY_METRIC_LABELS.length) return selected;
  // Preserve four cards for runs that did not persist one of the preferred
  // metrics by topping up in the existing configured order.
  const chosen = new Set(selected.map((metric) => metric.label));
  for (const metric of outcomeMetrics) {
    if (selected.length >= PIPELINE_RUN_PRIMARY_METRIC_LABELS.length) break;
    if (chosen.has(metric.label)) continue;
    chosen.add(metric.label);
    selected.push(metric);
  }
  return selected;
}

// Groups the current persisted stage_order into the compact family labels
// shown under the hero ribbon. This never invents a stage: it only relabels
// whatever raw stage names the run payload actually contains. Any stage name
// that doesn't match a known family still renders (as its own humanized
// name), so an unexpected/future stage is never dropped or misrepresented.
const PIPELINE_STAGE_FAMILY_RULES = [
  { family: "Scrape", test: /^startup$|scrap/ },
  { family: "AI", test: /intelligence|ai_evaluation|embedding|^details$/ },
  { family: "Filter", test: /filter|dedupe/ },
  { family: "Rank", test: /rank/ },
  { family: "Match", test: /resume_matching|match|priority/ },
  { family: "Plan", test: /planning|rag_export|plan/ },
  { family: "Final", test: /final/ },
];

// Minimal inline SVG icons, matching the existing profileResumeFileIcon /
// profileResumeManageRoleIcon pattern already used in this file. No new icon
// dependency is introduced.
const PIPELINE_RUN_ICON_PATHS = {
  check: '<path d="M5 12.5l4.5 4.5L19 7.5" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>',
  alert: '<path d="M12 8v5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><circle cx="12" cy="16.6" r="1.2" fill="currentColor"/><circle cx="12" cy="12" r="8.25" stroke="currentColor" stroke-width="1.8"/>',
  spinner: '<circle cx="12" cy="12" r="8.25" stroke="currentColor" stroke-width="1.8" opacity="0.35"/><path d="M12 3.75a8.25 8.25 0 018.25 8.25" stroke="currentColor" stroke-width="2.1" stroke-linecap="round"/>',
  clock: '<circle cx="12" cy="12" r="8.25" stroke="currentColor" stroke-width="1.7"/><path d="M12 7.5V12l3 1.75" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/>',
  document: '<path d="M7 3.75h6l4 4v12.5H7z" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/><path d="M13 3.75v4h4" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/>',
  layers: '<path d="M12 3.75l8 4-8 4-8-4z" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/><path d="M4 12l8 4 8-4M4 16.25l8 4 8-4" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/>',
  database: '<ellipse cx="12" cy="6.5" rx="7.25" ry="2.75" stroke="currentColor" stroke-width="1.7"/><path d="M4.75 6.5v11c0 1.52 3.25 2.75 7.25 2.75s7.25-1.23 7.25-2.75v-11" stroke="currentColor" stroke-width="1.7"/><path d="M19.25 12c0 1.52-3.25 2.75-7.25 2.75S4.75 13.52 4.75 12" stroke="currentColor" stroke-width="1.7"/>',
  funnel: '<path d="M4.25 5.25h15.5l-6 7v6.5l-3.5 2v-8.5z" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/>',
  sparkle: '<path d="M12 3.75l1.9 4.85 4.85 1.9-4.85 1.9-1.9 4.85-1.9-4.85-4.85-1.9 4.85-1.9z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/><path d="M18.5 16.25l.75 1.9 1.9.75-1.9.75-.75 1.9-.75-1.9-1.9-.75 1.9-.75z" fill="currentColor"/>',
  chart: '<path d="M4.75 19.25h14.5" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/><path d="M7.5 16.5V10M12 16.5V5.5M16.5 16.5v-4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
  list: '<path d="M9 6.75h10.25M9 12h10.25M9 17.25h10.25" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/><circle cx="5.25" cy="6.75" r="1.2" fill="currentColor"/><circle cx="5.25" cy="12" r="1.2" fill="currentColor"/><circle cx="5.25" cy="17.25" r="1.2" fill="currentColor"/>',
  info: '<circle cx="12" cy="12" r="8.25" stroke="currentColor" stroke-width="1.7"/><path d="M12 11v5.25" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><circle cx="12" cy="7.9" r="1.15" fill="currentColor"/>',
  copy: '<rect x="9" y="9" width="10.25" height="10.25" rx="2.4" stroke="currentColor" stroke-width="1.6"/><path d="M15 6.4A2.4 2.4 0 0012.6 4H7.4A2.4 2.4 0 005 6.4v5.2A2.4 2.4 0 007.4 14" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>',
  chevron: '<path d="M9.5 5.75L16 12l-6.5 6.25" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/>',
  chevronLeft: '<path d="M14.5 5.75L8 12l6.5 6.25" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/>',
  rotate: '<path d="M19.75 11.5a7.75 7.75 0 1 0-.6 3.55" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><path d="M19.75 5v5h-5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>',
  eye: '<path d="M2.75 12S6.25 5.75 12 5.75 21.25 12 21.25 12 17.75 18.25 12 18.25 2.75 12 2.75 12z" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/><circle cx="12" cy="12" r="2.9" stroke="currentColor" stroke-width="1.7"/>',
  trash: '<path d="M4.75 7h14.5" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/><path d="M9.5 7V5.4A1.4 1.4 0 0110.9 4h2.2a1.4 1.4 0 011.4 1.4V7" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/><path d="M6.75 7l.8 11.1A1.9 1.9 0 009.45 20h5.1a1.9 1.9 0 001.9-1.8L17.25 7" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/><path d="M10.6 10.75v5.5M13.4 10.75v5.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>',
};

function pipelineRunIcon(name, className = "") {
  const paths = PIPELINE_RUN_ICON_PATHS[name] || "";
  if (!paths) return "";
  return `<svg class="${className}" viewBox="0 0 24 24" fill="none" aria-hidden="true" focusable="false">${paths}</svg>`;
}

function pipelineRunStatusIconName(statusTone) {
  if (statusTone === "success") return "check";
  if (statusTone === "danger") return "alert";
  if (statusTone === "running") return "spinner";
  return "info";
}

function pipelineRunStatusCaption(statusTone, statusLabel) {
  if (statusTone === "success") return "Pipeline completed successfully";
  if (statusTone === "danger") return "Pipeline did not complete";
  if (statusTone === "running") return "Pipeline run in progress";
  return `Pipeline run ${String(statusLabel || "state").toLowerCase()}`;
}

function pipelineRunStageDisplayName(stage) {
  const text = String(stage || "").trim().replaceAll("_", " ");
  return text.replace(/\b\w/g, (char) => char.toUpperCase());
}

function pipelineRunStageFamily(stage) {
  const normalized = String(stage || "").trim().toLowerCase();
  const rule = PIPELINE_STAGE_FAMILY_RULES.find((candidate) => candidate.test.test(normalized));
  return rule ? rule.family : pipelineRunStageDisplayName(stage);
}

// One state per ribbon/chip segment, derived only from data the modal
// already loads (stage_order, completed_stages, current_stage, status) -
// no new fields, no invented progress.
function pipelineRunStageSegmentState(stage, { completedStages, currentStage, statusTone }) {
  if (completedStages.has(stage)) return "complete";
  if (stage === currentStage) {
    if (statusTone === "danger") return "failed";
    if (statusTone === "running") return "running";
  }
  return "pending";
}

// Completed segments walk a fixed premium teal -> jade -> mint -> gold
// progression so the ribbon reads as a deliberate journey rather than one
// flat colour. The step is chosen from the segment's own position in the
// run's real stage_order; the palette itself lives in the stylesheet.
const PIPELINE_RIBBON_PROGRESSION_STEPS = 8;

function pipelineRunStageProgressionStep(index, total) {
  const span = Math.max(Number(total) || 0, 1);
  const position = Math.min(Math.max(Number(index) || 0, 0), span - 1);
  const ratio = span === 1 ? 0 : position / (span - 1);
  return Math.round(ratio * (PIPELINE_RIBBON_PROGRESSION_STEPS - 1));
}

function pipelineRunStageSegmentStatusText(state) {
  if (state === "complete") return "Completed";
  if (state === "running") return "In progress";
  if (state === "failed") return "Failed";
  return "Pending";
}

// "Planned jobs" and "Packet jobs" are NOT persisted in status_json.counts.
// main.py::_application_planning_status_counts computes them per run as
// planning_total_jobs (rows in application_shortlist_by_job.csv) and
// planning_packet_jobs (rows in job_packet_manifest.csv), then embeds them in
// the authoritative summary_message. They are deliberately different concepts
// from planning_packets_total / planning_packets_generated /
// planning_packets_completed / planning_llm_generated, which ARE persisted and
// keep their own labels under Pipeline outcomes. Parsing the authoritative
// persisted sentence is the only correct source for these two fields; falling
// back to a packet-artifact count would relabel a different metric.
const PIPELINE_SUMMARY_PLANNED_JOBS_PATTERN = /(\d[\d,]*)\s+planned\s+jobs?\b/i;
const PIPELINE_SUMMARY_PACKET_JOBS_PATTERN = /(\d[\d,]*)\s+packet\s+jobs?\b/i;

function pipelineRunSummaryMetric(summaryMessage, pattern) {
  const match = String(summaryMessage || "").match(pattern);
  if (!match) return undefined;
  const numeric = Number(match[1].replaceAll(",", ""));
  return Number.isFinite(numeric) ? numeric : undefined;
}

function pipelineRunPlannedJobCount(summaryMessage) {
  return pipelineRunSummaryMetric(summaryMessage, PIPELINE_SUMMARY_PLANNED_JOBS_PATTERN);
}

function pipelineRunPacketJobCount(summaryMessage) {
  return pipelineRunSummaryMetric(summaryMessage, PIPELINE_SUMMARY_PACKET_JOBS_PATTERN);
}

function pipelineRunCountsSummary(counts) {
  const source = counts && typeof counts === "object" ? counts : {};
  const parts = [
    { keys: ["scraped_jobs", "scraped"], label: "Scraped" },
    { keys: ["filtered_jobs", "filtered"], label: "Filtered" },
    { keys: ["new_jobs", "new"], label: "New" },
    { keys: ["planning_llm_generated", "planning_packets_completed"], label: "Plans" },
  ]
    .map((metric) => ({
      label: metric.label,
      value: getFirstMetricValue(source, metric.keys),
    }))
    .filter((metric) => isDisplayableMetricValue(metric.value))
    .map((metric) => `${metric.label}: ${formatMetricValue(metric.value)}`);
  return parts.length ? parts.join(" · ") : "-";
}

function pipelineRunSettingsSummary(config) {
  const source = config && typeof config === "object" ? config : {};
  const actions = Array.isArray(source.llm_actions) ? source.llm_actions.join(", ") : String(source.llm_actions || "");
  return [
    `jobs ${source.job_limit ?? 50}`,
    `packets ${source.job_packet_limit ?? 0}`,
    actions ? `actions ${actions}` : "",
  ].filter(Boolean).join(" · ");
}

// One compact inline flow step. Absent metrics render an em dash rather than
// borrowing a different metric.
function pipelineRunFlowStep(label, value) {
  const text = isDisplayableMetricValue(value)
    ? formatPipelineRunMetricValue(value)
    : "—";
  return `
    <span class="pipeline-run-flow-step">
      <span class="pipeline-run-flow-label">${escapeHtml(label)}</span>
      <strong class="pipeline-run-flow-value">${escapeHtml(text)}</strong>
    </span>
  `;
}

function renderPipelineRuns(runs) {
  const tbody = qs("pipelineRunsTableBody");
  const meta = qs("pipelineRunsMeta");
  if (!tbody || !meta) return;

  const items = Array.isArray(runs) ? runs : [];
  profileState.pipelineRuns = items;
  const totalCount = Number(profileState.pipelineRunsTotalCount || 0);
  const historicalCount = totalCount > 0 ? totalCount : items.length;
  meta.textContent = `${formatPipelineRunMetricValue(historicalCount)} historical run${historicalCount === 1 ? "" : "s"}`;

  if (!items.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="5" class="pipeline-runs-empty-cell">No pipeline runs yet.</td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = items.map((run) => {
    const rawRunId = run.run_id || "";
    const runId = escapeHtml(rawRunId);
    const tone = pipelineRunStatusTone(run.status);
    const counts = run.counts && typeof run.counts === "object" ? run.counts : {};
    const finalJobs = run.final_job_count ?? counts.final_jobs;
    // Same authoritative semantics as the Pipeline Run Stats modal: planned
    // and packet jobs come from the persisted summary sentence, never from
    // the separate planning_packets_* artifact metrics.
    const plannedJobs = pipelineRunPlannedJobCount(run.summary_message || "");
    const packetJobs = pipelineRunPacketJobCount(run.summary_message || "");
    const outputParts = [];
    if (isDisplayableMetricValue(plannedJobs)) {
      outputParts.push(`${formatPipelineRunMetricValue(plannedJobs)} planned`);
    }
    if (isDisplayableMetricValue(packetJobs)) {
      outputParts.push(`${formatPipelineRunMetricValue(packetJobs)} packet`);
    }
    const agenticReviewAction = isCurrentUserAdmin(profileState.currentUser)
      ? `
            <a
              class="pipeline-run-icon-btn pipeline-run-agentic-review-btn"
              href="/profile/pipeline-runs/${encodeURIComponent(rawRunId)}/agentic-review"
              data-tooltip="Agentic review"
              aria-label="Open agentic review for ${runId}"
            >${pipelineRunIcon("sparkle", "pipeline-run-icon-btn-glyph")}</a>`
      : "";
    return `
      <tr data-pipeline-run-id="${runId}">
        <td class="pipeline-run-cell-run">
          <div class="pipeline-run-date">${escapeHtml(formatPipelineRunHeaderDate(run.started_at || ""))}</div>
          <div class="pipeline-run-id" title="${runId}">${runId}</div>
        </td>
        <td>
          <span class="pipeline-run-status is-${escapeHtml(tone)}">
            <span class="pipeline-run-status-dot" aria-hidden="true"></span>
            ${escapeHtml(pipelineRunStatusLabel(run.status))}
          </span>
        </td>
        <td class="pipeline-run-cell-output">
          <div class="pipeline-run-output-primary">
            ${escapeHtml(isDisplayableMetricValue(finalJobs) ? formatPipelineRunMetricValue(finalJobs) : "—")}
            <span>final</span>
          </div>
          ${outputParts.length
            ? `<div class="pipeline-run-output-secondary">${escapeHtml(outputParts.join(" · "))}</div>`
            : ""}
        </td>
        <td class="pipeline-run-cell-flow">
          <div class="pipeline-run-flow">
            ${pipelineRunFlowStep("Scraped", getFirstMetricValue(counts, ["scraped_jobs", "scraped"]))}
            <span class="pipeline-run-flow-arrow" aria-hidden="true">→</span>
            ${pipelineRunFlowStep("Filtered", getFirstMetricValue(counts, ["filtered_jobs", "filtered"]))}
            <span class="pipeline-run-flow-arrow" aria-hidden="true">→</span>
            ${pipelineRunFlowStep("New", getFirstMetricValue(counts, ["new_jobs", "new"]))}
            <span class="pipeline-run-flow-arrow" aria-hidden="true">→</span>
            ${pipelineRunFlowStep("Final", finalJobs)}
          </div>
        </td>
        <td class="pipeline-run-cell-actions">
          <div class="pipeline-run-actions-cell" aria-label="Pipeline run actions">
            <button
              type="button"
              class="pipeline-run-icon-btn pipeline-run-view-btn"
              data-pipeline-run-view="${runId}"
              data-tooltip="View stats"
              aria-label="View stats for ${runId}"
            >${pipelineRunIcon("chart", "pipeline-run-icon-btn-glyph")}</button>
            ${agenticReviewAction}
            <button
              type="button"
              class="pipeline-run-icon-btn pipeline-run-rerun-btn"
              data-pipeline-run-rerun="${runId}"
              data-tooltip="Re-run"
              aria-label="Re-run ${runId}"
            >${pipelineRunIcon("rotate", "pipeline-run-icon-btn-glyph")}</button>
          </div>
        </td>
      </tr>
    `;
  }).join("");
}

function renderPipelineRunsPagination() {
  const metaEl = qs("pipelineRunsPaginationMeta");
  const actionsEl = qs("pipelineRunsPaginationActions");
  if (!metaEl || !actionsEl) return;

  const totalCount = profileState.pipelineRunsTotalCount || 0;
  const totalPages = Math.max(profileState.pipelineRunsTotalPages || 1, 1);
  const currentPage = Math.min(Math.max(profileState.pipelineRunsPage || 1, 1), totalPages);
  const pageSize = Math.max(profileState.pipelineRunsPageSize || 15, 1);

  if (totalCount === 0) {
    metaEl.textContent = "No pages";
    actionsEl.innerHTML = "";
    return;
  }

  const startRow = (currentPage - 1) * pageSize + 1;
  const endRow = Math.min(startRow + (profileState.pipelineRuns.length || 0) - 1, totalCount);
  // Page position lives in the compact "n / total" control beside the arrows,
  // so the meta line stays a single quiet range statement.
  metaEl.textContent = `Showing ${startRow}-${endRow} of ${totalCount}`;

  actionsEl.innerHTML = `
    <button
      type="button"
      class="application-pagination-btn pipeline-runs-page-btn"
      data-pipeline-runs-page="${currentPage - 1}"
      aria-label="Previous pipeline runs page"
      title="Previous page"
      ${profileState.pipelineRunsHasPrevious ? "" : "disabled"}
    >${pipelineRunIcon("chevronLeft", "pipeline-runs-page-glyph")}</button>
    <span class="pipeline-runs-page-indicator" aria-current="page">${currentPage} / ${totalPages}</span>
    <button
      type="button"
      class="application-pagination-btn pipeline-runs-page-btn"
      data-pipeline-runs-page="${currentPage + 1}"
      aria-label="Next pipeline runs page"
      title="Next page"
      ${profileState.pipelineRunsHasNext ? "" : "disabled"}
    >${pipelineRunIcon("chevron", "pipeline-runs-page-glyph")}</button>
  `;
}

function applyPipelineRunsPaginationPayload(data) {
  profileState.pipelineRunsPage = Number(data.page || 1);
  profileState.pipelineRunsPageSize = Number(data.page_size || 15);
  profileState.pipelineRunsTotalCount = Number(data.total_row_count || 0);
  profileState.pipelineRunsTotalPages = Math.max(Number(data.total_pages || 1), 1);
  profileState.pipelineRunsHasPrevious = Boolean(data.has_previous);
  profileState.pipelineRunsHasNext = Boolean(data.has_next);
}

async function loadPipelineRuns(page = profileState.pipelineRunsPage || 1) {
  const tbody = qs("pipelineRunsTableBody");
  const meta = qs("pipelineRunsMeta");
  if (!tbody || !meta) return;

  meta.textContent = "Loading pipeline runs...";
  tbody.innerHTML = `<tr><td colspan="5" class="pipeline-runs-empty-cell">Loading pipeline runs...</td></tr>`;
  const paginationMeta = qs("pipelineRunsPaginationMeta");
  const paginationActions = qs("pipelineRunsPaginationActions");
  if (paginationMeta) paginationMeta.textContent = "Loading...";
  if (paginationActions) paginationActions.innerHTML = "";
  setPipelineRunsStatus("");

  const targetPage = Math.max(1, Number(page || 1));
  const pageSize = Math.max(1, Number(profileState.pipelineRunsPageSize || 15));
  const data = await fetchJson(`/profile/pipeline-runs?page=${encodeURIComponent(targetPage)}&page_size=${encodeURIComponent(pageSize)}`);
  applyPipelineRunsPaginationPayload(data);
  renderPipelineRuns(data.runs || []);
  renderPipelineRunsPagination();
}

function renderKeyValueList(items) {
  return items.map(([label, value]) => `
    <div class="pipeline-run-detail-row">
      <div class="pipeline-run-detail-label">${escapeHtml(label)}</div>
      <div class="pipeline-run-detail-value">${escapeHtml(value === undefined || value === null || value === "" ? "-" : String(value))}</div>
    </div>
  `).join("");
}

// Same label/value pairs as renderKeyValueList, with a restrained semantic
// treatment for the boolean Yes/No settings so they stop reading as raw debug
// text. Values themselves are unchanged.
function renderPipelineRunSettingsList(items) {
  return items.map(([label, value]) => {
    const text = value === undefined || value === null || value === "" ? "-" : String(value);
    const normalized = text.trim().toLowerCase();
    const booleanClass = normalized === "yes" ? " is-yes" : normalized === "no" ? " is-no" : "";
    return `
      <div class="pipeline-run-detail-row">
        <div class="pipeline-run-detail-label">${escapeHtml(label)}</div>
        <div class="pipeline-run-detail-value${booleanClass}">
          ${booleanClass ? '<span class="pipeline-run-detail-dot" aria-hidden="true"></span>' : ""}
          <span>${escapeHtml(text)}</span>
        </div>
      </div>
    `;
  }).join("");
}

function renderJsonDetails(label, value) {
  const payload = value && typeof value === "object" && Object.keys(value).length
    ? JSON.stringify(value, null, 2)
    : "";
  if (!payload) return "";
  return `
    <details class="agent-trace-json-detail">
      <summary>${escapeHtml(label)}</summary>
      <pre>${escapeHtml(payload)}</pre>
    </details>
  `;
}

function renderAgentTraceStep(step) {
  const status = pipelineRunStatusLabel(step?.status || "");
  const tone = pipelineRunStatusTone(step?.status || "");
  const modelText = [step?.model_provider, step?.model_name].filter(Boolean).join(" / ");
  const latency = Number(step?.latency_ms || 0);
  const validationStatus = step?.validation_json?.validation_status || step?.validation_json?.status || "";
  return `
    <article class="agent-trace-step">
      <div class="agent-trace-step-header">
        <div>
          <div class="agent-trace-step-name">${escapeHtml(step?.agent_name || "Agent step")}</div>
          <div class="agent-trace-step-meta">
            ${escapeHtml(step?.agent_version || "")}
            ${modelText ? ` · ${escapeHtml(modelText)}` : ""}
            ${latency ? ` · ${escapeHtml(`${latency} ms`)}` : ""}
          </div>
        </div>
        <span class="pipeline-run-status agent-trace-step-status is-${escapeHtml(tone)}">${escapeHtml(status)}</span>
      </div>
      <div class="agent-trace-step-summary">
        ${modelText ? `<span>${escapeHtml(modelText)}</span>` : ""}
        ${validationStatus ? `<span>Validation: ${escapeHtml(String(validationStatus).replaceAll("_", " "))}</span>` : ""}
        ${latency ? `<span>${escapeHtml(`${latency} ms`)}</span>` : ""}
      </div>
      <div class="agent-trace-step-times">
        ${escapeHtml(formatDateTime(step?.started_at || "") || "Start unavailable")}
        ${step?.completed_at ? ` → ${escapeHtml(formatDateTime(step.completed_at))}` : ""}
      </div>
      ${step?.error ? `<div class="agent-trace-error">${escapeHtml(step.error)}</div>` : ""}
      <div class="agent-trace-json-grid">
        ${renderJsonDetails("Input", step?.input_json)}
        ${renderJsonDetails("Output", step?.output_json)}
        ${renderJsonDetails("Validation", step?.validation_json)}
        ${renderJsonDetails("Token usage", step?.token_usage_json)}
        ${renderJsonDetails("Cost", step?.cost_json)}
      </div>
    </article>
  `;
}

function renderAgentTraceRun(run) {
  const steps = Array.isArray(run?.steps) ? run.steps : [];
  return `
    <article class="agent-trace-run">
      <div class="agent-trace-run-header">
        <div>
          <div class="agent-trace-run-id">${escapeHtml(run?.agent_run_id || "Agent run")}</div>
          <div class="agent-trace-step-meta">${escapeHtml(run?.context_id || "")}</div>
        </div>
        <span class="pipeline-run-status agent-trace-step-status is-${escapeHtml(pipelineRunStatusTone(run?.status || ""))}">
          ${escapeHtml(pipelineRunStatusLabel(run?.status || ""))}
        </span>
      </div>
      ${renderJsonDetails("Run summary", run?.summary_json)}
      ${run?.error ? `<div class="agent-trace-error">${escapeHtml(run.error)}</div>` : ""}
      <div class="agent-trace-step-list">
        ${steps.length
          ? steps.map(renderAgentTraceStep).join("")
          : `<div class="pipeline-runs-empty-cell">No agent steps recorded for this agent run.</div>`}
      </div>
    </article>
  `;
}

function renderAgentTracePanel(tracePayload, traceError = "") {
  const runs = Array.isArray(tracePayload?.agent_runs) ? tracePayload.agent_runs : [];
  const counts = tracePayload?.counts && typeof tracePayload.counts === "object" ? tracePayload.counts : {};
  const hasSteps = runs.some((run) => Array.isArray(run?.steps) && run.steps.length);
  return `
    <section class="pipeline-run-detail-panel agent-trace-panel">
      <h4>Agent trace</h4>
      ${traceError ? `<div class="agent-trace-error">${escapeHtml(traceError)}</div>` : ""}
      ${runs.length || hasSteps
        ? `
          <div class="agent-trace-counts">
            ${renderKeyValueList([
              ["Agent runs", counts.agent_runs ?? runs.length],
              ["Agent steps", counts.agent_steps ?? 0],
              ["Succeeded steps", counts.succeeded_steps ?? 0],
              ["Warning steps", counts.warning_steps ?? 0],
              ["Failed steps", counts.failed_steps ?? 0],
            ])}
          </div>
          <div class="agent-trace-run-list">
            ${runs.map(renderAgentTraceRun).join("")}
          </div>
        `
        : `<div class="pipeline-run-inline-empty">${pipelineRunIcon("list", "")}<span>No agent trace recorded for this run.</span></div>`}
    </section>
  `;
}

function formatWorkflowSummaryCounts(counts = {}) {
  const entries = Object.entries(counts || {}).filter(([, value]) => Number(value || 0) > 0);
  if (!entries.length) return "none";
  return entries
    .map(([key, value]) => `${key.replaceAll("_", " ")}=${value}`)
    .join(", ");
}

function renderWorkflowSummaryMetric(label, value) {
  return `
    <div class="agentic-workflow-metric">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(value ?? 0)}</strong>
    </div>
  `;
}

function renderAgenticWorkflowSummaryPanel(workflowSummary = {}) {
  const available = Boolean(workflowSummary?.available);
  const summary = workflowSummary?.summary_json && typeof workflowSummary.summary_json === "object"
    ? workflowSummary.summary_json
    : {};
  const markdown = String(workflowSummary?.summary_markdown || "").trim();

  if (!available && !Object.keys(summary).length && !markdown) {
    return `
      <section class="pipeline-run-detail-panel agentic-workflow-summary-card">
        <h4>Agentic Workflow Summary</h4>
        <div class="pipeline-runs-empty-cell">No agentic workflow summary recorded for this run.</div>
      </section>
    `;
  }

  const missingArtifacts = Array.isArray(summary.missing_artifacts) ? summary.missing_artifacts : [];
  return `
    <section class="pipeline-run-detail-panel agentic-workflow-summary-card">
      <div class="agentic-workflow-header">
        <div>
          <h4>Agentic Workflow Summary</h4>
          <p>Read-only advisory rollup from this run's artifacts.</p>
        </div>
        <span class="agentic-workflow-badge">Advisory</span>
      </div>
      <div class="agentic-workflow-grid">
        ${renderWorkflowSummaryMetric("Queue jobs", summary.total_queue_jobs)}
        ${renderWorkflowSummaryMetric("Packet jobs", summary.total_packet_jobs)}
        ${renderWorkflowSummaryMetric("Ready to apply", summary.ready_to_apply_count)}
        ${renderWorkflowSummaryMetric("Tailor then apply", summary.tailor_then_apply_count)}
        ${renderWorkflowSummaryMetric("Hold / skip", summary.hold_or_skip_count)}
        ${renderWorkflowSummaryMetric("Source watch", summary.source_watch_count)}
        ${renderWorkflowSummaryMetric("Fallback only", summary.fallback_only_count)}
        ${renderWorkflowSummaryMetric("Packet blocked", summary.packet_blocked_count)}
      </div>
      <div class="agentic-workflow-counts">
        <div><strong>Priority</strong><span>${escapeHtml(formatWorkflowSummaryCounts(summary.advisory_priority_counts))}</span></div>
        <div><strong>Tailoring</strong><span>${escapeHtml(formatWorkflowSummaryCounts(summary.tailoring_decision_counts))}</span></div>
        <div><strong>Operator lanes</strong><span>${escapeHtml(formatWorkflowSummaryCounts(summary.operator_review_lane_counts))}</span></div>
      </div>
      <div class="agentic-workflow-missing">
        <strong>Missing artifacts</strong>
        <span>${escapeHtml(missingArtifacts.length ? missingArtifacts.join(", ") : "none")}</span>
      </div>
      ${markdown ? `<details class="agentic-workflow-markdown"><summary>Markdown summary</summary><pre>${escapeHtml(markdown)}</pre></details>` : ""}
    </section>
  `;
}

function formatWorkflowVerificationStatus(status) {
  const value = String(status || "unknown").trim().toLowerCase();
  if (value === "passed") return "Passed";
  if (value === "warning") return "Warning";
  if (value === "failed") return "Failed";
  return "Unknown";
}

function renderWorkflowVerificationList(values, emptyLabel = "none") {
  const entries = Array.isArray(values)
    ? values
    : Object.entries(values || {}).map(([key, value]) => `${key}: ${value}`);
  const cleanEntries = entries.map((value) => String(value || "").trim()).filter(Boolean);
  if (!cleanEntries.length) {
    return `<span class="agentic-workflow-verification-empty">${escapeHtml(emptyLabel)}</span>`;
  }
  return `
    <ul class="agentic-workflow-verification-list">
      ${cleanEntries.map((value) => `<li>${escapeHtml(value)}</li>`).join("")}
    </ul>
  `;
}

function renderWorkflowVerificationChecks(checks = {}) {
  const entries = Array.isArray(checks)
    ? checks.map((value, index) => [`check_${index + 1}`, value])
    : Object.entries(checks || {});
  if (!entries.length) {
    return `<span class="agentic-workflow-verification-empty">none</span>`;
  }
  return `
    <div class="agentic-workflow-verification-checks">
      ${entries.map(([key, value]) => `
        <div class="agentic-workflow-verification-check">
          <strong>${escapeHtml(String(key).replaceAll("_", " "))}</strong>
          <span>${escapeHtml(typeof value === "object" ? JSON.stringify(value) : value)}</span>
        </div>
      `).join("")}
    </div>
  `;
}

function renderAgenticWorkflowVerificationPanel(workflowVerification = {}) {
  const available = Boolean(workflowVerification?.available);
  const verification = workflowVerification?.verification_json && typeof workflowVerification.verification_json === "object"
    ? workflowVerification.verification_json
    : {};

  if (!available && !Object.keys(verification).length) {
    return `
      <section class="pipeline-run-detail-panel agentic-workflow-verification-card">
        <h4>Agentic Workflow Verification</h4>
        <div class="pipeline-runs-empty-cell">No agentic workflow verification recorded for this run.</div>
      </section>
    `;
  }

  const status = String(verification.validation_status || "unknown").trim().toLowerCase();
  const checkedArtifacts = Array.isArray(verification.checked_artifacts) ? verification.checked_artifacts : [];
  const missingArtifacts = Array.isArray(verification.missing_artifacts) ? verification.missing_artifacts : [];
  const reasonCodes = Array.isArray(verification.reason_codes) ? verification.reason_codes : [];
  const rowCounts = verification.row_counts && typeof verification.row_counts === "object" ? verification.row_counts : {};
  const consistencyChecks = verification.consistency_checks && typeof verification.consistency_checks === "object"
    ? verification.consistency_checks
    : {};
  const summary = verification.summary && typeof verification.summary === "object" ? verification.summary : {};

  return `
    <section class="pipeline-run-detail-panel agentic-workflow-verification-card">
      <div class="agentic-workflow-header">
        <div>
          <h4>Agentic Workflow Verification</h4>
          <p>Read-only diagnostic checks for this run's artifacts.</p>
        </div>
        <span class="agentic-workflow-verification-status agentic-workflow-verification-status--${escapeHtml(status)}">
          ${escapeHtml(formatWorkflowVerificationStatus(status))}
        </span>
      </div>
      <div class="agentic-workflow-grid">
        ${renderWorkflowSummaryMetric("Strict mode", verification.strict ? "Yes" : "No")}
        ${renderWorkflowSummaryMetric("Checked artifacts", checkedArtifacts.length)}
        ${renderWorkflowSummaryMetric("Missing artifacts", missingArtifacts.length)}
        ${renderWorkflowSummaryMetric("Reason codes", reasonCodes.length)}
      </div>
      <div class="agentic-workflow-verification-sections">
        <div>
          <strong>Summary</strong>
          ${renderWorkflowVerificationList(summary)}
        </div>
        <div>
          <strong>Row counts</strong>
          ${renderWorkflowVerificationList(rowCounts)}
        </div>
        <div>
          <strong>Missing artifacts</strong>
          ${renderWorkflowVerificationList(missingArtifacts)}
        </div>
        <div>
          <strong>Reason codes</strong>
          ${renderWorkflowVerificationList(reasonCodes)}
        </div>
      </div>
      <details class="agentic-workflow-verification-details">
        <summary>Consistency checks</summary>
        ${renderWorkflowVerificationChecks(consistencyChecks)}
      </details>
    </section>
  `;
}

function renderPipelineRunDetail(data, tracePayload = {}, traceError = "") {
  const run = data.run || {};
  const statusJson = data.status_json || {};
  const configJson = data.config_json || {};
  const config = run.config || statusJson.config || configJson.config || {};
  const counts = run.counts || statusJson.counts || {};
  const outcomeMetrics = getPipelineRunOutcomeMetrics(counts);
  const stageOrder = Array.isArray(statusJson.stage_order) ? statusJson.stage_order : [];
  const completedStages = new Set(Array.isArray(statusJson.completed_stages) ? statusJson.completed_stages : []);
  const statusLabel = pipelineRunStatusLabel(run.status || statusJson.status);
  const statusTone = pipelineRunStatusTone(run.status || statusJson.status);
  const startedAt = run.started_at || statusJson.started_at || "";
  const completedAt = run.completed_at || statusJson.completed_at || statusJson.finished_at || "";
  const duration = completedAt
    ? formatPipelineRunDuration(startedAt, completedAt)
    : statusTone === "running" ? "In progress" : "Not available";
  const finalJobCount = run.final_job_count ?? statusJson.final_job_count ?? counts.final_jobs ?? "-";
  const summaryMessage = run.summary_message || statusJson.summary_message || run.stage_message || statusJson.stage_message || "";
  // Authoritative source for these two: the persisted summary sentence (see
  // pipelineRunPlannedJobCount). Never substituted from planning_packets_*.
  const plannedJobCount = pipelineRunPlannedJobCount(summaryMessage);
  const packetJobCount = pipelineRunPacketJobCount(summaryMessage);
  // Distinct, separately persisted planning-stage packet artifact count.
  const planningPacketsTotal = getFirstMetricValue(counts, ["planning_packets_total"]);
  const scrapedTotal = getFirstMetricValue(counts, ["scraped_jobs", "scraped"]);
  const errorMessage = run.error || statusJson.error || "";
  const currentStage = run.current_stage || statusJson.current_stage || "-";

  // Same outcomeMetrics data as before, split into a primary and secondary
  // presentation tier. The four highlighted metrics are selected out of the
  // existing PIPELINE_RUN_OUTCOME_METRICS config by label - no new metric, no
  // new derivation - and anything not highlighted stays fully visible in the
  // secondary list. Runs missing one of the four fall back to config order so
  // four cards always render when four metrics exist.
  const primaryMetrics = selectPipelineRunPrimaryMetrics(outcomeMetrics);
  const primaryLabels = new Set(primaryMetrics.map((metric) => metric.label));
  const secondaryMetrics = outcomeMetrics.filter((metric) => !primaryLabels.has(metric.label));
  const primaryMetricIcons = ["database", "funnel", "layers", "sparkle"];

  const stageSegmentState = (stage) => pipelineRunStageSegmentState(stage, {
    completedStages,
    currentStage,
    statusTone,
  });
  const stageFamilies = [];
  for (const stage of stageOrder) {
    const family = pipelineRunStageFamily(stage);
    if (!stageFamilies.includes(family)) stageFamilies.push(family);
  }
  const completedStageCount = stageOrder.filter((stage) => completedStages.has(stage)).length;

  const metricRow = (label, value) => `
    <div class="pipeline-run-summary-item">
      <dt>${escapeHtml(label)}</dt>
      <dd>${escapeHtml(value)}</dd>
    </div>
  `;
  const optionalMetricText = (value) => (
    isDisplayableMetricValue(value) ? formatPipelineRunMetricValue(value) : "-"
  );

  qs("pipelineRunStatsTitle").textContent = "Pipeline run";
  qs("pipelineRunStatsSubtitle").textContent = formatPipelineRunHeaderDate(startedAt);
  qs("pipelineRunStatsRunId").textContent = run.run_id || "Run ID unavailable";
  qs("pipelineRunStatsBody").innerHTML = `
    <section class="pipeline-run-hero is-${escapeHtml(statusTone)}" aria-label="Pipeline run overview">
      <div class="pipeline-run-hero-facts">
        <div class="pipeline-run-hero-status">
          <span class="pipeline-run-hero-status-badge" aria-hidden="true">
            ${pipelineRunIcon(pipelineRunStatusIconName(statusTone), "pipeline-run-hero-status-icon")}
          </span>
          <div class="pipeline-run-hero-status-copy">
            <strong>${escapeHtml(statusLabel)}</strong>
            <span>${escapeHtml(pipelineRunStatusCaption(statusTone, statusLabel))}</span>
          </div>
        </div>
        <div class="pipeline-run-hero-stat">
          ${pipelineRunIcon("clock", "pipeline-run-hero-stat-icon")}
          <div>
            <strong>${escapeHtml(duration)}</strong>
            <span>Duration</span>
          </div>
        </div>
        <div class="pipeline-run-hero-stat">
          ${pipelineRunIcon("document", "pipeline-run-hero-stat-icon")}
          <div>
            <strong>${escapeHtml(formatPipelineRunMetricValue(finalJobCount))}</strong>
            <span>Final jobs</span>
          </div>
        </div>
        <div class="pipeline-run-hero-stat">
          ${pipelineRunIcon("layers", "pipeline-run-hero-stat-icon")}
          <div>
            <strong>${escapeHtml(optionalMetricText(planningPacketsTotal))}</strong>
            <span>Planning packets</span>
          </div>
        </div>
      </div>
      ${stageOrder.length ? `
        <div class="pipeline-run-hero-ribbon">
          <div class="pipeline-run-hero-ribbon-main">
            <ul class="pipeline-run-hero-ribbon-bars" role="list" aria-label="Pipeline stage progress">
              ${stageOrder.map((stage, index) => {
                const state = stageSegmentState(stage);
                const raw = pipelineRunStageDisplayName(stage);
                const step = pipelineRunStageProgressionStep(index, stageOrder.length);
                const stepClass = state === "complete" ? ` is-step-${step}` : "";
                return `
                  <li
                    class="pipeline-run-hero-bar is-${escapeHtml(state)}${stepClass}"
                    role="listitem"
                    title="${escapeHtml(raw)} — ${escapeHtml(pipelineRunStageSegmentStatusText(state))}"
                    aria-label="${escapeHtml(raw)}: ${escapeHtml(pipelineRunStageSegmentStatusText(state))}"
                  ></li>
                `;
              }).join("")}
            </ul>
            <div class="pipeline-run-hero-ribbon-labels" aria-hidden="true">
              ${stageFamilies.map((family) => `<span>${escapeHtml(family)}</span>`).join("")}
            </div>
          </div>
          <div class="pipeline-run-hero-ribbon-progress">
            ${pipelineRunIcon(completedStageCount === stageOrder.length ? "check" : "spinner", "pipeline-run-hero-progress-icon")}
            <div>
              <strong>${escapeHtml(`${completedStageCount} / ${stageOrder.length} stages`)}</strong>
              <span>${escapeHtml(completedStageCount === stageOrder.length ? "All stages completed" : `${stageOrder.length - completedStageCount} not reached`)}</span>
            </div>
          </div>
        </div>
      ` : ""}
    </section>

    <section class="pipeline-run-panel pipeline-run-stats-section pipeline-run-summary-section">
      <div class="pipeline-run-panel-head">
        <h4>${pipelineRunIcon("document", "pipeline-run-panel-icon")}<span>Run summary</span></h4>
      </div>
      <dl class="pipeline-run-summary-grid">
        ${metricRow("Started", formatDateTime(startedAt) || "-")}
        ${metricRow("Completed", formatDateTime(completedAt) || "-")}
        ${metricRow("Current stage", currentStage)}
        ${metricRow("Final jobs", formatPipelineRunMetricValue(finalJobCount))}
        ${metricRow("Planned jobs", optionalMetricText(plannedJobCount))}
        ${metricRow("Packet jobs", optionalMetricText(packetJobCount))}
      </dl>
      <div class="pipeline-run-summary-copy">
        ${pipelineRunIcon("info", "pipeline-run-summary-copy-icon")}
        <span class="pipeline-run-summary-copy-label">Summary</span>
        <p>${escapeHtml(summaryMessage || "No summary persisted for this run.")}</p>
      </div>
      ${errorMessage ? `
        <div class="pipeline-run-failure-summary" role="alert">
          <strong>Run error</strong>
          <span>${escapeHtml(errorMessage)}</span>
        </div>
      ` : ""}
    </section>

    <section class="pipeline-run-panel pipeline-run-stats-section pipeline-run-outcomes-section">
      <div class="pipeline-run-panel-head">
        <h4>${pipelineRunIcon("chart", "pipeline-run-panel-icon")}<span>Pipeline outcomes</span></h4>
        ${isDisplayableMetricValue(scrapedTotal) ? `
          <span class="pipeline-run-panel-meta">Total processed: ${escapeHtml(formatPipelineRunMetricValue(scrapedTotal))} jobs</span>
        ` : ""}
      </div>
      ${primaryMetrics.length ? `
        <div class="pipeline-run-outcome-primary">
          ${primaryMetrics.map((metric, index) => `
            <div class="pipeline-run-outcome-primary-metric is-tone-${index}">
              <span class="pipeline-run-outcome-primary-icon" aria-hidden="true">
                ${pipelineRunIcon(primaryMetricIcons[index] || "layers", "")}
              </span>
              <span class="pipeline-run-outcome-primary-body">
                <strong>${escapeHtml(formatPipelineRunMetricValue(metric.value))}</strong>
                <span class="pipeline-run-outcome-primary-label">${escapeHtml(metric.label)}</span>
              </span>
            </div>
          `).join("")}
        </div>
      ` : `<div class="pipeline-runs-empty-cell">No user-facing outcome metrics were persisted for this run.</div>`}
      ${secondaryMetrics.length ? `
        <dl class="pipeline-run-outcome-secondary">
          ${secondaryMetrics.map((metric) => `
            <div class="pipeline-run-outcome-secondary-row">
              <dt>${escapeHtml(metric.label)}</dt>
              <dd>${escapeHtml(formatPipelineRunMetricValue(metric.value))}</dd>
            </div>
          `).join("")}
        </dl>
      ` : ""}
    </section>

    <details class="pipeline-run-technical-disclosure pipeline-run-disclosure">
      <summary>
        <span class="pipeline-run-disclosure-icon" aria-hidden="true">${pipelineRunIcon("list", "")}</span>
        <span class="pipeline-run-disclosure-copy">
          <strong>Agent trace &amp; stage details</strong>
          <small>Settings, persisted stages, and technical trace</small>
        </span>
        <span class="pipeline-run-disclosure-chevron" aria-hidden="true">${pipelineRunIcon("chevron", "")}</span>
      </summary>
      <div class="pipeline-run-technical-content">
        <section class="pipeline-run-technical-section">
          <h4>Settings</h4>
          <div class="pipeline-run-technical-grid">
            ${renderPipelineRunSettingsList([
              ["Job limit", config.job_limit ?? 50],
              ["Packet limit", config.job_packet_limit ?? 0],
              ["LLM actions", Array.isArray(config.llm_actions) ? config.llm_actions.join(", ") : config.llm_actions],
              ["Planning only", config.planning_only ? "Yes" : "No"],
              ["Generate tailoring", config.generate_tailoring ? "Yes" : "No"],
              ["Generate LLM tailoring", config.generate_llm_tailoring ? "Yes" : "No"],
              ["Refresh LLM tailoring", config.refresh_llm_tailoring ? "Yes" : "No"],
              ["Generate LLM fallback", config.generate_llm_fallback ? "Yes" : "No"],
              ["Generate LLM adjudication", config.generate_llm_adjudication ? "Yes" : "No"],
              ["Delete seen data", config.delete_seen_data || "no"],
            ])}
          </div>
        </section>
        <section class="pipeline-run-technical-section">
          <h4>Stages</h4>
          <div class="pipeline-run-stage-list">
            ${stageOrder.length
              ? stageOrder.map((stage) => {
                  const state = stageSegmentState(stage);
                  const marker = state === "complete" ? "✓" : state === "failed" ? "✕" : state === "running" ? "●" : "○";
                  return `
                    <span class="pipeline-run-stage-chip is-${escapeHtml(state)}" title="${escapeHtml(pipelineRunStageSegmentStatusText(state))}">
                      ${marker} ${escapeHtml(stage)}
                    </span>
                  `;
                }).join("")
              : `<span class="pipeline-runs-empty-cell">No stage list persisted for this run.</span>`}
          </div>
        </section>
        ${renderAgentTracePanel(tracePayload, traceError)}
      </div>
    </details>

    <details class="pipeline-run-disclosure pipeline-run-error-disclosure">
      <summary>
        <span class="pipeline-run-disclosure-icon${errorMessage ? " is-danger" : ""}" aria-hidden="true">${pipelineRunIcon("alert", "")}</span>
        <span class="pipeline-run-disclosure-copy">
          <strong>Error details</strong>
          <small>${escapeHtml(errorMessage ? "Persisted run error is available" : "No error recorded for this run")}</small>
        </span>
        <span class="pipeline-run-disclosure-chevron" aria-hidden="true">${pipelineRunIcon("chevron", "")}</span>
      </summary>
      <div class="pipeline-run-technical-content">
        ${errorMessage
          ? `<div class="pipeline-run-failure-summary" role="alert"><strong>Run error</strong><span>${escapeHtml(errorMessage)}</span></div>`
          : `<div class="pipeline-run-inline-empty">${pipelineRunIcon("info", "")}<span>No error recorded for this run.</span></div>`}
      </div>
    </details>
  `;
}

function pipelineRunStatsFocusableElements(modal) {
  if (!modal) return [];
  return Array.from(modal.querySelectorAll(
    'button:not([disabled]), summary, [href], input:not([disabled]), [tabindex]:not([tabindex="-1"])'
  )).filter((element) => {
    if (element.closest(".hidden")) return false;
    const closedDetails = Array.from(modal.querySelectorAll("details:not([open])"));
    return closedDetails.every(
      (details) => !details.contains(element) || element === details.querySelector(":scope > summary")
    );
  });
}

function renderPipelineRunStatsFetchError(runId, error) {
  qs("pipelineRunStatsTitle").textContent = "Pipeline run";
  qs("pipelineRunStatsSubtitle").textContent = "Run details unavailable";
  qs("pipelineRunStatsRunId").textContent = runId || "Run ID unavailable";
  qs("pipelineRunStatsBody").innerHTML = `
    <div class="pipeline-run-stats-fetch-error" role="alert">
      <strong>Could not load pipeline run details</strong>
      <span>${escapeHtml(error?.message || "The persisted run details could not be loaded.")}</span>
    </div>
  `;
}

async function openPipelineRunStatsModal(runId) {
  const modal = qs("pipelineRunStatsModal");
  if (!modal) return;
  if (modal._closeTimer) window.clearTimeout(modal._closeTimer);
  modal._returnFocus = document.activeElement;
  modal.classList.remove("hidden", "is-closing");
  document.body.classList.add("pipeline-run-stats-modal-open");
  qs("pipelineRunStatsTitle").textContent = "Pipeline run";
  qs("pipelineRunStatsSubtitle").textContent = "Loading persisted run details.";
  qs("pipelineRunStatsRunId").textContent = runId || "Pipeline run ID pending";
  qs("pipelineRunStatsBody").innerHTML = `
    <div class="pipeline-run-stats-loading" role="status">
      <span class="pipeline-run-stats-loading-dot" aria-hidden="true"></span>
      Loading run details...
    </div>
  `;
  window.requestAnimationFrame(() => qs("pipelineRunStatsCloseBtn")?.focus());
  try {
    const data = await fetchJson(`/profile/pipeline-runs/${encodeURIComponent(runId)}`);
    renderPipelineRunDetail(data);
  } catch (error) {
    setPipelineRunsStatus(error?.message || "Could not load pipeline run details.", "error");
    renderPipelineRunStatsFetchError(runId, error);
  }
}

function closePipelineRunStatsModal() {
  const modal = qs("pipelineRunStatsModal");
  if (!modal || modal.classList.contains("hidden") || modal.classList.contains("is-closing")) return;
  const returnFocus = modal._returnFocus;
  const finishClose = () => {
    modal.classList.remove("is-closing");
    modal.classList.add("hidden");
    modal._closeTimer = null;
    document.body.classList.remove("pipeline-run-stats-modal-open");
    if (returnFocus && document.body.contains(returnFocus)) returnFocus.focus();
  };
  modal.classList.add("is-closing");
  const reducedMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
  modal._closeTimer = window.setTimeout(finishClose, reducedMotion ? 0 : 110);
}

function renderPipelineRunRerunSummary(run) {
  const config = run?.config && typeof run.config === "object" ? run.config : {};
  const llmActions = Array.isArray(config.llm_actions)
    ? config.llm_actions.join(", ")
    : config.llm_actions;
  qs("pipelineRunRerunTitle").textContent = "Re-run pipeline";
  qs("pipelineRunRerunSubtitle").textContent = formatPipelineRunHeaderDate(run?.started_at || "");
  const runIdEl = qs("pipelineRunRerunRunId");
  if (runIdEl) runIdEl.textContent = run?.run_id || "Persisted run";
  // Same saved configuration values as before - only the presentation is an
  // inset panel now. No field is added that the stored config does not have.
  qs("pipelineRunRerunBody").innerHTML = `
    <section class="pipeline-run-rerun-panel" aria-label="Saved configuration">
      <h4>Saved configuration</h4>
      <div class="pipeline-run-rerun-grid">
        ${renderPipelineRunSettingsList([
          ["Job limit", config.job_limit ?? 50],
          ["Packet limit", config.job_packet_limit ?? 0],
          ["Actions", llmActions],
          ["Planning only", config.planning_only ? "Yes" : "No"],
          ["Generate suggestions", config.generate_tailoring ? "Yes" : "No"],
          ["Generate LLM suggestions", config.generate_llm_tailoring ? "Yes" : "No"],
          ["Refresh LLM suggestions", config.refresh_llm_tailoring ? "Yes" : "No"],
          ["LLM fallback ranking", config.generate_llm_fallback ? "Yes" : "No"],
          ["LLM judging", config.generate_llm_adjudication ? "Yes" : "No"],
        ])}
      </div>
    </section>
    <p class="pipeline-run-rerun-note">
      This starts a new pipeline run using the saved configuration. The existing run remains unchanged.
    </p>
  `;
}

function openPipelineRunRerunModal(runId) {
  const run = getPipelineRunById(runId);
  if (!run) {
    throw new Error("Pipeline run was not found on this page.");
  }

  const modal = qs("pipelineRunRerunModal");
  profileState.pendingRerunRunId = runId;
  if (modal) modal._returnFocus = document.activeElement;
  renderPipelineRunRerunSummary(run);
  qs("pipelineRunRerunConfirmBtn").disabled = false;
  qs("pipelineRunRerunConfirmBtn").textContent = "Re-run pipeline";
  modal?.classList.remove("hidden");
  window.requestAnimationFrame(() => qs("pipelineRunRerunCancelBtn")?.focus());
}

function closePipelineRunRerunModal() {
  const modal = qs("pipelineRunRerunModal");
  const returnFocus = modal?._returnFocus;
  profileState.pendingRerunRunId = null;
  modal?.classList.add("hidden");
  if (modal) modal._returnFocus = null;
  if (returnFocus && document.body && document.body.contains(returnFocus)) {
    returnFocus.focus();
  }
}

async function rerunPipelineRun(runId) {
  const run = getPipelineRunById(runId);
  const label = run?.started_at ? formatDateTime(run.started_at) : runId;
  setPipelineRunsStatus(`Starting re-run from ${label}...`, "info");
  const data = await postJson(`/profile/pipeline-runs/${encodeURIComponent(runId)}/rerun`, {});
  const newRunId = data?.pipeline?.run_id || "new run";
  await loadPipelineRuns();
  setPipelineRunsStatus(`Pipeline re-run started (${newRunId}). Open Executive Queue to watch live progress.`, "success");
}

async function confirmPipelineRunRerun() {
  const runId = profileState.pendingRerunRunId;
  if (!runId) return;

  const confirmBtn = qs("pipelineRunRerunConfirmBtn");
  if (confirmBtn) {
    confirmBtn.disabled = true;
    confirmBtn.textContent = "Starting...";
  }

  try {
    await rerunPipelineRun(runId);
    closePipelineRunRerunModal();
  } catch (err) {
    if (confirmBtn) {
      confirmBtn.disabled = false;
      confirmBtn.textContent = "Re-run pipeline";
    }
    throw err;
  }
}


function normalizeResumeOnboardingQuery(value) {
  return String(value || "").trim().replace(/[\\/]+$/, "");
}

function isResumeOnboardingMode() {
  const params = new URLSearchParams(window.location.search);
  return normalizeResumeOnboardingQuery(params.get("onboarding")) === "resume_upload";
}

function getProfileTabTargetFromUrl() {
  const params = new URLSearchParams(window.location.search);
  const tab = (params.get("tab") || "").trim().toLowerCase();
  if (tab === "pipeline-runs" || tab === "pipeline_runs" || tab === "runs") {
    return "profilePipelineRunsSection";
  }
  if (tab === "user-access" || tab === "admin-users" || tab === "users") {
    return "profileAdminUsersSection";
  }
  return "resumeSection";
}

function activateProfileTab(targetId) {
  const target = qs(targetId);
  if (!target) return false;

  document.querySelectorAll(".profile-tab-btn").forEach((tab) => {
    tab.classList.toggle("is-active", tab.dataset.profileTabTarget === targetId);
  });
  document.querySelectorAll("[data-profile-tab-panel]").forEach((panel) => {
    panel.classList.toggle("hidden", panel.id !== targetId);
  });

  if (targetId === "profilePipelineRunsSection" && !profileState.pipelineRuns.length) {
    loadPipelineRuns().catch((err) => {
      setPipelineRunsStatus(err.message, "error");
    });
  }

  if (targetId === "profilePreferencesSection" && !profileState.preferencesLoaded) {
    loadProfilePreferences().catch((err) => {
      setProfilePreferencesStatus(err.message, "error");
    });
  }

  if (targetId === "profileAdminUsersSection" && !profileState.adminUsers.length) {
    loadAdminUsers().catch((err) => {
      setAdminUsersStatus(err.message, "error");
    });
  }

  return true;
}

function ensureResumeOnboardingBanner() {
  let banner = qs("resumeOnboardingBanner");
  if (banner) return banner;

  const sectionCard = document.querySelector(".profile-section-card");
  if (!sectionCard) return null;

  banner = document.createElement("div");
  banner.id = "resumeOnboardingBanner";
  banner.className = "profile-inline-status hidden";
  sectionCard.insertBefore(banner, qs("resumeStatusBanner") || sectionCard.firstChild);
  return banner;
}

function renderResumeOnboardingState(resumes) {
  const banner = ensureResumeOnboardingBanner();
  if (!banner) return;

  const resumeCount = Array.isArray(resumes) ? resumes.length : 0;
  const isOnboarding = isResumeOnboardingMode();

  if (!isOnboarding && resumeCount > 0) {
    banner.className = "profile-inline-status hidden";
    banner.innerHTML = "";
    return;
  }

  if (resumeCount <= 0) {
    banner.className = "profile-inline-status info";
    banner.innerHTML = `
      <strong>Resume required.</strong>
      ${isOnboarding
        ? "Upload at least one PDF resume to continue to preference setup."
        : "Upload at least one PDF resume to unlock Live Pipeline."}
    `;
    return;
  }

  banner.className = "profile-inline-status success";
  banner.innerHTML = `
    <strong>Resume ready.</strong>
    Your profile has ${resumeCount} resume${resumeCount === 1 ? "" : "s"} available.
    <a class="profile-onboarding-continue-btn" href="/onboarding">Continue to onboarding</a>
  `;
}

function getResumeDeleteModal() {
  return qs("resumeDeleteModal");
}

function openResumeDeleteModal(resumeName, trigger = document.activeElement) {
  profileState.pendingDeleteResumeName = resumeName || "";
  qs("resumeDeleteModalName").textContent = resumeName || "-";
  const modal = getResumeDeleteModal();
  if (modal) {
    modal.dataset.returnResumeName = profileState.pendingDeleteResumeName;
    modal.dataset.returnResumeAction = "delete";
  }
  openProfileResumeModal(modal, trigger, qs("resumeDeleteCancelBtn"));
}

function closeResumeDeleteModal() {
  profileState.pendingDeleteResumeName = null;
  qs("resumeDeleteModalName").textContent = "-";
  closeProfileResumeModal(getResumeDeleteModal());
}

function resumeRoleMappingsFor(resumeName) {
  const safeName = String(resumeName || "");
  return profileState.resumeRoleMappings.filter((mapping) => mapping.resume_name === safeName);
}

function resumeRoleMappingFor(resumeName, roleFamilyId) {
  const safeName = String(resumeName || "");
  const safeRole = String(roleFamilyId || "");
  return profileState.resumeRoleMappings.find(
    (mapping) => mapping.resume_name === safeName && mapping.role_family_id === safeRole
  );
}

function resumeRoleFamilyName(roleFamilyId) {
  const family = profileState.resumeRoleFamilies.find(
    (item) => String(item.role_family_id || "") === String(roleFamilyId || "")
  );
  return family?.display_name || roleFamilyId;
}

function renderResumeRoleLabels(resume) {
  const mappings = resumeRoleMappingsFor(String(resume?.resume_name || ""));
  if (!mappings.length) {
    return '<span class="profile-resume-no-roles">No role families</span>';
  }
  return mappings.map((mapping) => `
    <span class="profile-resume-role-chip${mapping.is_default_for_role ? " is-default" : ""}">
      ${escapeHtml(resumeRoleFamilyName(mapping.role_family_id))}
      ${mapping.is_default_for_role ? '<span class="profile-resume-default-dot" aria-label="Default for this role"></span>' : ""}
    </span>
  `).join("");
}

function renderResumeRoleModalOptions() {
  const optionsEl = qs("resumeRoleModalOptions");
  const resumeName = String(profileState.activeRoleResumeName || "");
  if (!optionsEl || !resumeName) return;
  const nameEl = qs("resumeRoleModalName");
  if (nameEl) {
    nameEl.textContent = resumeName;
    nameEl.parentElement?.setAttribute("title", resumeName);
  }
  const families = Array.isArray(profileState.resumeRoleFamilies) ? profileState.resumeRoleFamilies : [];
  if (!families.length) {
    optionsEl.innerHTML = '<div class="profile-resume-role-empty">No role families are available.</div>';
    return;
  }

  optionsEl.innerHTML = families.map((family) => {
    const roleFamilyId = String(family.role_family_id || "");
    const mapping = resumeRoleMappingFor(resumeName, roleFamilyId);
    const checked = Boolean(mapping);
    const isDefault = Boolean(mapping?.is_default_for_role);
    const displayName = family.display_name || roleFamilyId;
    return `
      <div class="profile-resume-role-option${checked ? " is-selected" : ""}">
        <label class="profile-resume-role-toggle">
          <input
            type="checkbox"
            data-resume-role-toggle
            data-resume-name="${escapeHtml(resumeName)}"
            data-role-family-id="${escapeHtml(roleFamilyId)}"
            ${checked ? "checked" : ""}
          />
          <span>${escapeHtml(displayName)}</span>
        </label>
        <label class="profile-resume-role-default">
          <input
            type="radio"
            name="resume-role-default-${escapeHtml(roleFamilyId)}"
            data-resume-role-default
            data-resume-name="${escapeHtml(resumeName)}"
            data-role-family-id="${escapeHtml(roleFamilyId)}"
            ${isDefault ? "checked" : ""}
            ${checked ? "" : "disabled"}
            aria-label="Use ${escapeHtml(resumeName)} as the default for ${escapeHtml(displayName)}"
          />
          <span>Default</span>
        </label>
      </div>
    `;
  }).join("");
}

function openResumeRoleModal(resumeName, trigger) {
  profileState.activeRoleResumeName = resumeName || "";
  renderResumeRoleModalOptions();
  const modal = qs("profileResumeRoleModal");
  if (modal) {
    modal.dataset.returnResumeName = profileState.activeRoleResumeName;
    modal.dataset.returnResumeAction = "manage";
  }
  openProfileResumeModal(modal, trigger, qs("closeResumeRoleModalBtn"));
}

function closeResumeRoleModal() {
  profileState.activeRoleResumeName = null;
  closeProfileResumeModal(qs("profileResumeRoleModal"));
}

function openResumeUploadModal(trigger) {
  setResumeUploadFeedback("");
  qs("resumeDropzone")?.classList.remove("drag-active");
  openProfileResumeModal(qs("profileResumeUploadModal"), trigger, qs("resumeDropzone"));
}

function closeResumeUploadModal() {
  qs("resumeDropzone")?.classList.remove("drag-active");
  closeProfileResumeModal(qs("profileResumeUploadModal"));
}

function profileResumeFileIcon() {
  return `
    <span class="profile-resume-file-icon" aria-hidden="true">
      <svg viewBox="0 0 24 24" fill="none">
        <path d="M7.25 3.75h6l3.5 3.5v13H7.25z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round" />
        <path d="M13.25 3.75v3.5h3.5" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round" />
      </svg>
      <span>PDF</span>
    </span>
  `;
}

function profileResumeManageRoleIcon() {
  return `
    <svg class="profile-resume-row-action-icon" viewBox="0 0 24 24" fill="none" aria-hidden="true" focusable="false">
      <path d="M5 7.25h14M5 12h14M5 16.75h14" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
      <circle cx="8" cy="7.25" r="1.35" fill="currentColor" />
      <circle cx="15.5" cy="12" r="1.35" fill="currentColor" />
      <circle cx="10.5" cy="16.75" r="1.35" fill="currentColor" />
    </svg>
  `;
}

function renderResumeList(items) {
  const listEl = qs("resumeList");
  const metaEl = qs("resumeListMeta");
  const resumes = Array.isArray(items) ? items : [];

  metaEl.textContent = `${resumes.length} resume${resumes.length === 1 ? "" : "s"}`;

  if (!resumes.length) {
    listEl.innerHTML = `
      <div class="resume-empty-state">
        <strong>No resumes yet</strong>
        <span>Add a PDF to begin your library.</span>
      </div>
    `;
    return;
  }


  if (isResumeOnboardingMode()) {
    listEl.innerHTML = resumes.map((resume) => `
      <article class="resume-row profile-onboarding-resume-ready">
        <div class="resume-row-main">
          <div class="resume-name">${escapeHtml(resume.resume_name || "")}</div>
          <div class="resume-meta">
            <span>Resume ready</span>
            <span>${escapeHtml(formatBytes(resume.size_bytes || 0))}</span>
          </div>
        </div>
      </article>
    `).join("");
    return;
  }

  listEl.innerHTML = resumes.map((resume) => `
    <article class="profile-resume-document-row">
      ${profileResumeFileIcon()}
      <div class="profile-resume-file-copy">
        <div class="profile-resume-file-name" title="${escapeHtml(resume.resume_name || "")}">${escapeHtml(resume.resume_name || "")}</div>
        <div class="profile-resume-file-meta">
          ${escapeHtml(formatBytes(resume.size_bytes || 0))}<span aria-hidden="true">·</span>${escapeHtml(formatResumeDate(resume.modified_at || ""))}
        </div>
      </div>

      <div class="profile-resume-role-chips" aria-label="Assigned role families">
        ${renderResumeRoleLabels(resume)}
      </div>

      <div class="profile-resume-row-actions">
        <button
          type="button"
          class="profile-resume-row-action profile-resume-manage-role-action"
          data-manage-resume-roles="${escapeHtml(resume.resume_name || "")}"
          aria-label="Manage role families for ${escapeHtml(resume.resume_name || "resume")}"
          title="Manage role families for ${escapeHtml(resume.resume_name || "resume")}"
        >${profileResumeManageRoleIcon()}</button>
        <button
          type="button"
          class="profile-resume-row-action profile-resume-delete-row-action"
          data-resume-delete="${escapeHtml(resume.resume_name || "")}"
          aria-label="Delete ${escapeHtml(resume.resume_name || "resume")}"
          title="Delete ${escapeHtml(resume.resume_name || "resume")}"
        ><span class="profile-resume-row-action-icon profile-resume-delete-icon" aria-hidden="true"></span></button>
      </div>
    </article>
  `).join("");

  if (profileState.activeRoleResumeName && !qs("profileResumeRoleModal")?.classList.contains("hidden")) {
    renderResumeRoleModalOptions();
  }
}

async function loadResumeRoleMappings() {
  const data = await fetchJson("/profile/resume-role-mappings");
  profileState.resumeRoleMappings = Array.isArray(data.mappings) ? data.mappings : [];
  profileState.resumeRoleFamilies = Array.isArray(data.role_families) ? data.role_families : [];
}

async function loadResumes() {
  const listEl = qs("resumeList");
  const metaEl = qs("resumeListMeta");

  metaEl.textContent = "Loading resumes...";
  listEl.innerHTML = `<div class="resume-empty-state">Loading...</div>`;

  const data = await fetchJson("/profile/resumes");
  const resumes = data.resumes || [];
  if (!isResumeOnboardingMode()) await loadResumeRoleMappings();
  renderResumeList(resumes);
  renderResumeOnboardingState(resumes);
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
  const company = String(scan?.job_company || "").trim();
  const role = String(scan?.job_title || "").trim();
  const resume = String(scan?.resume_name || scan?.resume_filename || "").trim();
  const label = [company, role, resume].filter(Boolean).join(" / ") || "this saved scan";

  // Same values, shown as a structured summary instead of one run-on sentence.
  const setField = (id, value) => {
    const el = qs(id);
    if (el) el.textContent = value || "-";
  };
  setField("savedScanDeleteCompany", company);
  setField("savedScanDeleteRole", role);
  setField("savedScanDeleteResume", resume);
  qs("savedScanDeleteName").textContent = label;

  const modal = qs("savedScanDeleteModal");
  if (modal) modal._returnFocus = document.activeElement;
  modal?.classList.remove("hidden");
  window.requestAnimationFrame(() => qs("savedScanDeleteCancelBtn")?.focus());
}

function closeSavedScanDeleteModal() {
  const modal = qs("savedScanDeleteModal");
  const returnFocus = modal?._returnFocus;
  profileState.pendingDeleteScanId = null;
  const name = qs("savedScanDeleteName");
  if (name) name.textContent = "this saved scan";
  ["savedScanDeleteCompany", "savedScanDeleteRole", "savedScanDeleteResume"].forEach((id) => {
    const el = qs(id);
    if (el) el.textContent = "-";
  });
  modal?.classList.add("hidden");
  if (modal) modal._returnFocus = null;
  if (returnFocus && document.body && document.body.contains(returnFocus)) {
    returnFocus.focus();
  }
}

function savedScanMatchBarWidth(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return null;
  return Math.max(0, Math.min(100, number));
}

function savedScanSearchHaystack(scan) {
  return [
    scan?.job_company,
    scan?.job_title,
    scan?.resume_name,
    scan?.resume_filename,
    normalizeSavedScanSource(scan?.resume_source),
    savedScanStatusMeta(scan?.scan_status).label,
    scan?.scan_id,
  ]
    .map((value) => String(value || ""))
    .join(" ")
    .toLowerCase();
}

function filterSavedScans(scans, query) {
  const needle = String(query || "").trim().toLowerCase();
  if (!needle) return scans;
  return scans.filter((scan) => savedScanSearchHaystack(scan).includes(needle));
}

function savedScansMetaText(totalCount, visibleCount, query) {
  const label = `${totalCount} saved scan${totalCount === 1 ? "" : "s"}`;
  return String(query || "").trim() ? `${visibleCount} of ${label}` : label;
}

function savedScanRowHtml(scan) {
  const statusMeta = savedScanStatusMeta(scan.scan_status);
  const openHref = getSavedScanOpenHref(scan);
  const role = scan.job_title || "-";
  const resume = scan.resume_name || scan.resume_filename || "-";
  const scoreText = formatPercent(scan.match_rate);
  const barWidth = savedScanMatchBarWidth(scan.match_rate);
  const matchLabel = barWidth === null ? "Match rate unavailable" : `Match rate ${scoreText}`;

  const openAction = openHref
    ? `<a
        class="saved-scan-action-btn saved-scan-action-btn--open"
        href="${escapeHtml(openHref)}"
        aria-label="Open saved scan report"
        title="Open report"
      >${pipelineRunIcon("eye", "saved-scan-action-icon")}</a>`
    : `<button
        type="button"
        class="saved-scan-action-btn saved-scan-action-btn--open"
        disabled
        aria-disabled="true"
        aria-label="Report unavailable"
        title="Report unavailable"
      >${pipelineRunIcon("eye", "saved-scan-action-icon")}</button>`;

  return `
      <tr class="saved-scan-row" data-saved-scan-id="${escapeHtml(scan.scan_id || "")}">
        <td class="saved-scan-cell-scanned">${escapeHtml(formatDateTime(scan.scan_timestamp || ""))}</td>
        <td class="saved-scan-cell-company">${escapeHtml(scan.job_company || "-")}</td>
        <td class="saved-scan-cell-role"><span class="saved-scan-truncate" title="${escapeHtml(role)}">${escapeHtml(role)}</span></td>
        <td class="saved-scan-cell-resume"><span class="saved-scan-truncate" title="${escapeHtml(resume)}">${escapeHtml(resume)}</span></td>
        <td class="saved-scan-cell-source"><span class="saved-scan-source-tag">${escapeHtml(normalizeSavedScanSource(scan.resume_source))}</span></td>
        <td class="saved-scan-cell-status">
          <span class="saved-scan-status is-${escapeHtml(statusMeta.tone)}">
            <span class="saved-scan-status-dot" aria-hidden="true"></span>
            ${escapeHtml(statusMeta.label)}
          </span>
        </td>
        <td class="saved-scan-cell-match">
          <div class="saved-scan-match">
            <span class="saved-scan-match-value">${escapeHtml(scoreText)}</span>
            <span
              class="saved-scan-match-track"
              role="img"
              aria-label="${escapeHtml(matchLabel)}"
            ><span class="saved-scan-match-fill" style="width: ${barWidth === null ? 0 : barWidth}%"></span></span>
          </div>
        </td>
        <td class="saved-scan-cell-actions">
          <div class="saved-scan-actions">
            ${openAction}
            <button
              type="button"
              class="saved-scan-action-btn saved-scan-action-btn--delete"
              aria-label="Delete saved scan"
              title="Delete saved scan"
              data-saved-scan-delete="${escapeHtml(scan.scan_id || "")}"
              data-saved-scan-name="${escapeHtml(scan.resume_name || scan.resume_filename || "saved scan")}"
            >${pipelineRunIcon("trash", "saved-scan-action-icon")}</button>
          </div>
        </td>
      </tr>
    `;
}

function paintSavedScans({ ok = true, error = "" } = {}) {
  const tbody = qs("savedScansTableBody");
  const metaEl = qs("savedScansMeta");
  const countEl = qs("savedScansCountBadge");
  if (!tbody || !metaEl) return;

  const scans = Array.isArray(profileState.savedScans) ? profileState.savedScans : [];
  const query = String(profileState.savedScansQuery || "");

  if (!ok) {
    metaEl.textContent = "Saved scans unavailable";
    if (countEl) countEl.textContent = "0";
    tbody.innerHTML = `
      <tr>
        <td colspan="8" class="saved-scans-empty-cell">
          ${escapeHtml(error || "Could not load saved scans from Postgres.")}
        </td>
      </tr>
    `;
    return;
  }

  const visible = filterSavedScans(scans, query);
  if (countEl) countEl.textContent = String(scans.length);
  metaEl.textContent = savedScansMetaText(scans.length, visible.length, query);

  if (!scans.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="8" class="saved-scans-empty-cell">
          No saved scans yet.
        </td>
      </tr>
    `;
    return;
  }

  if (!visible.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="8" class="saved-scans-empty-cell">
          No saved scans match this search.
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = visible.map(savedScanRowHtml).join("");
}

function renderSavedScans(items, { ok = true, error = "" } = {}) {
  profileState.savedScans = ok && Array.isArray(items) ? items : [];
  paintSavedScans({ ok, error });
}

async function loadSavedScans() {
  const tbody = qs("savedScansTableBody");
  const metaEl = qs("savedScansMeta");
  if (!tbody || !metaEl) return;

  metaEl.textContent = "Loading saved scans...";
  tbody.innerHTML = `
    <tr>
      <td colspan="8" class="saved-scans-empty-cell">Loading saved scans...</td>
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
  setResumeUploadFeedback(
    `Uploading ${fileList.length} file${fileList.length === 1 ? "" : "s"}...`,
    "info"
  );

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
    setResumeUploadFeedback(
      `Uploaded ${results.uploaded.length} file${results.uploaded.length === 1 ? "" : "s"} successfully.`,
      "success"
    );
    if (isResumeOnboardingMode()) {
      window.location.href = "/onboarding";
      return results;
    }
    showProfilePlanningUploadCallout();
    closeResumeUploadModal();
    return results;
  }

  if (results.uploaded.length && results.failed.length) {
    setStatus(
      `Uploaded ${results.uploaded.length} file${results.uploaded.length === 1 ? "" : "s"}, failed ${results.failed.length}.`,
      "error"
    );
    setResumeUploadFeedback(
      `Uploaded ${results.uploaded.length}; ${results.failed.length} failed. ${results.failed[0]?.error || ""}`,
      "error"
    );
    if (!isResumeOnboardingMode()) showProfilePlanningUploadCallout();
    return results;
  }

  const firstError = results.failed[0]?.error || "Upload failed.";
  setResumeUploadFeedback(firstError, "error");
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

async function saveResumeRoleMapping(resumeName, roleFamilyId, isDefaultForRole = false) {
  await postJson("/profile/resume-role-mappings", {
    resume_name: resumeName,
    role_family_id: roleFamilyId,
    is_default_for_role: Boolean(isDefaultForRole),
  });
  await loadResumes();
}

async function deleteResumeRoleMapping(resumeName, roleFamilyId) {
  const params = new URLSearchParams({
    resume_name: resumeName,
    role_family_id: roleFamilyId,
  });
  await fetchJson(`/profile/resume-role-mappings?${params.toString()}`, {
    method: "DELETE",
  });
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

  qs("openResumeUploadModalBtn")?.addEventListener("click", (event) => {
    openResumeUploadModal(event.currentTarget);
  });
  qs("closeResumeUploadModalBtn")?.addEventListener("click", closeResumeUploadModal);
  qs("profileResumeUploadModal")?.addEventListener("click", (event) => {
    if (event.target === qs("profileResumeUploadModal")) closeResumeUploadModal();
  });
}

function bindDeleteInteractions() {
  qs("resumeList").addEventListener("click", (event) => {
    const manageButton = event.target.closest("[data-manage-resume-roles]");
    if (manageButton) {
      openResumeRoleModal(manageButton.dataset.manageResumeRoles || "", manageButton);
      return;
    }

    const button = event.target.closest("[data-resume-delete]");
    if (!button) return;

    const resumeName = button.dataset.resumeDelete || "";
    openResumeDeleteModal(resumeName, button);
  });

  qs("closeResumeDeleteModalBtn").addEventListener("click", closeResumeDeleteModal);
  qs("resumeDeleteCancelBtn")?.addEventListener("click", closeResumeDeleteModal);

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

function bindResumeRoleMappingInteractions() {
  qs("profileResumeRoleModal")?.addEventListener("change", async (event) => {
    const toggle = event.target.closest("[data-resume-role-toggle]");
    const defaultInput = event.target.closest("[data-resume-role-default]");
    const input = toggle || defaultInput;
    if (!input) return;

    const resumeName = input.dataset.resumeName || "";
    const roleFamilyId = input.dataset.roleFamilyId || "";
    if (!resumeName || !roleFamilyId) return;

    input.disabled = true;
    try {
      if (toggle) {
        if (toggle.checked) {
          await saveResumeRoleMapping(resumeName, roleFamilyId, false);
          setStatus("Role family assigned.", "success");
        } else {
          await deleteResumeRoleMapping(resumeName, roleFamilyId);
          setStatus("Role family assignment removed.", "success");
        }
        return;
      }

      if (defaultInput.checked) {
        await saveResumeRoleMapping(resumeName, roleFamilyId, true);
        setStatus("Default resume updated for role family.", "success");
      }
    } catch (err) {
      setStatus(err.message, "error");
      await loadResumes();
    }
  });

  qs("closeResumeRoleModalBtn")?.addEventListener("click", closeResumeRoleModal);
  qs("profileResumeRoleModal")?.addEventListener("click", (event) => {
    if (event.target === qs("profileResumeRoleModal")) closeResumeRoleModal();
  });
}

function bindProfileResumeKeyboardInteractions() {
  document.addEventListener("keydown", (event) => {
    const openModal = Array.from(document.querySelectorAll(".profile-resume-modal:not(.hidden)")).pop();
    if (event.key === "Escape" && openModal) {
      event.preventDefault();
      if (openModal.id === "profileResumeUploadModal") closeResumeUploadModal();
      if (openModal.id === "profileResumeRoleModal") closeResumeRoleModal();
      if (openModal.id === "resumeDeleteModal") closeResumeDeleteModal();
      return;
    }
    if (event.key === "Tab" && openModal) trapProfileResumeModalFocus(event, openModal);
  });
}

function bindProfilePlanningOptionsInteractions() {
  qs("openProfilePlanningOptionsBtn")?.addEventListener("click", openProfilePlanningOptionsModal);
  qs("closeProfilePlanningOptionsModalBtn")?.addEventListener("click", closeProfilePlanningOptionsModal);
  qs("cancelProfilePlanningOptionsBtn")?.addEventListener("click", closeProfilePlanningOptionsModal);
  qs("runProfilePlanningUpdateBtn")?.addEventListener("click", runProfilePlanningUpdate);
  qs("profilePlanningSelectAllOptionsBtn")?.addEventListener("click", () => {
    setProfilePlanningOptions(true);
  });
  qs("profilePlanningClearAllOptionsBtn")?.addEventListener("click", () => {
    setProfilePlanningOptions(false);
  });
  getProfilePlanningOptionsModal()?.addEventListener("click", (event) => {
    if (event.target === getProfilePlanningOptionsModal()) {
      closeProfilePlanningOptionsModal();
    }
  });
}

function bindProfileTabs() {
  qs("profileTabs")?.addEventListener("click", (event) => {
    const button = event.target.closest("[data-profile-tab-target]");
    if (!button) return;

    const targetId = button.dataset.profileTabTarget || "";
    activateProfileTab(targetId);
  });
}

function bindProfilePreferencesInteractions() {
  const form = qs("profilePreferencesForm");
  if (!form) return;

  profileLocationSelector = window.ApplyLensLocationSelector?.create(
    qs("profilePreferencesLocationSelector"),
    { onChange: markProfilePreferencesDirty }
  );
  profilePreferencesWorkflow = window.ApplyLensPreferencesWorkflow?.create(
    qs("profilePreferencesSection"),
    { getValues: collectProfilePreferences }
  );

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    saveProfilePreferences();
  });
  qs("profilePreferencesSelectAllRolesBtn")?.addEventListener("click", () => {
    setProfilePreferenceCheckboxGroup("selected_role_families", true);
    markProfilePreferencesDirty();
  });
  qs("profilePreferencesClearAllRolesBtn")?.addEventListener("click", () => {
    setProfilePreferenceCheckboxGroup("selected_role_families", false);
    markProfilePreferencesDirty();
  });
  form.querySelectorAll("input, textarea").forEach((field) => {
    if (field.closest("[data-location-selector]")) return;
    field.addEventListener("change", () => {
      syncProfileSeniorityStrictToggle();
      markProfilePreferencesDirty();
    });
  });
  form.querySelectorAll("textarea").forEach((field) => {
    field.addEventListener("input", markProfilePreferencesDirty);
  });
}

function bindPipelineRunsInteractions() {
  const section = qs("profilePipelineRunsSection");
  if (!section) return;

  qs("refreshPipelineRunsBtn")?.addEventListener("click", () => {
    loadPipelineRuns(profileState.pipelineRunsPage).catch((err) => {
      setPipelineRunsStatus(err.message, "error");
    });
  });

  qs("pipelineRunsPaginationActions")?.addEventListener("click", (event) => {
    const button = event.target.closest("[data-pipeline-runs-page]");
    if (!button || button.disabled) return;

    const targetPage = Number(button.dataset.pipelineRunsPage || 1);
    if (!Number.isFinite(targetPage) || targetPage < 1) return;

    loadPipelineRuns(targetPage).catch((err) => {
      setPipelineRunsStatus(err.message, "error");
    });
  });

  qs("pipelineRunsTableBody")?.addEventListener("click", (event) => {
    const viewBtn = event.target.closest("[data-pipeline-run-view]");
    if (viewBtn) {
      openPipelineRunStatsModal(viewBtn.dataset.pipelineRunView || "").catch((err) => {
        setPipelineRunsStatus(err.message, "error");
        renderPipelineRunStatsFetchError(viewBtn.dataset.pipelineRunView || "", err);
      });
      return;
    }

    const rerunBtn = event.target.closest("[data-pipeline-run-rerun]");
    if (rerunBtn) {
      try {
        openPipelineRunRerunModal(rerunBtn.dataset.pipelineRunRerun || "");
      } catch (err) {
        setPipelineRunsStatus(err.message, "error");
      }
    }
  });

  qs("pipelineRunStatsCloseBtn")?.addEventListener("click", closePipelineRunStatsModal);

  qs("pipelineRunStatsCopyIdBtn")?.addEventListener("click", async () => {
    const runId = qs("pipelineRunStatsRunId")?.textContent?.trim() || "";
    if (!runId) return;
    try {
      await navigator.clipboard?.writeText(runId);
      const button = qs("pipelineRunStatsCopyIdBtn");
      button?.classList.add("is-copied");
      window.setTimeout(() => button?.classList.remove("is-copied"), 1200);
    } catch (_) {
      /* Clipboard is unavailable or denied; the run id stays selectable. */
    }
  });
  qs("pipelineRunStatsModal")?.addEventListener("click", (event) => {
    if (event.target === qs("pipelineRunStatsModal")) {
      closePipelineRunStatsModal();
    }
  });
  qs("pipelineRunStatsModal")?.addEventListener("keydown", (event) => {
    const modal = qs("pipelineRunStatsModal");
    if (!modal || modal.classList.contains("hidden")) return;
    if (event.key === "Escape") {
      event.preventDefault();
      closePipelineRunStatsModal();
      return;
    }
    if (event.key !== "Tab") return;
    const focusable = pipelineRunStatsFocusableElements(modal);
    if (!focusable.length) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  });
  qs("pipelineRunRerunCloseBtn")?.addEventListener("click", closePipelineRunRerunModal);
  qs("pipelineRunRerunCancelBtn")?.addEventListener("click", closePipelineRunRerunModal);

  qs("pipelineRunRerunModal")?.addEventListener("keydown", (event) => {
    const modal = qs("pipelineRunRerunModal");
    if (!modal || modal.classList.contains("hidden")) return;
    if (event.key === "Escape") {
      event.preventDefault();
      closePipelineRunRerunModal();
    }
  });
  qs("pipelineRunRerunConfirmBtn")?.addEventListener("click", () => {
    confirmPipelineRunRerun().catch((err) => {
      setPipelineRunsStatus(err.message, "error");
    });
  });
  qs("pipelineRunRerunModal")?.addEventListener("click", (event) => {
    if (event.target === qs("pipelineRunRerunModal")) {
      closePipelineRunRerunModal();
    }
  });
}

function bindAdminUsersInteractions() {
  const section = qs("profileAdminUsersSection");
  if (!section) return;

  qs("refreshAdminUsersBtn")?.addEventListener("click", () => {
    loadAdminUsers().catch((err) => {
      setAdminUsersStatus(err.message, "error");
    });
  });

  qs("adminUsersTableBody")?.addEventListener("click", (event) => {
    const accessBtn = event.target.closest("[data-admin-user-access]");
    if (accessBtn) {
      const userId = accessBtn.dataset.adminUserAccess || "";
      const nextActive = accessBtn.dataset.nextActive === "true";
      openAdminUserAccessModal(userId, nextActive);
      return;
    }

    const deleteBtn = event.target.closest("[data-admin-user-delete]");
    if (deleteBtn) {
      openAdminUserDeleteModal(deleteBtn.dataset.adminUserDelete || "");
    }
  });

  qs("adminUserAccessCloseBtn")?.addEventListener("click", closeAdminUserAccessModal);
  qs("adminUserAccessConfirmBtn")?.addEventListener("click", async () => {
    try {
      await confirmAdminUserAccessChange();
    } catch (err) {
      setAdminUsersStatus(err.message, "error");
      closeAdminUserAccessModal();
    }
  });
  qs("adminUserAccessModal")?.addEventListener("click", (event) => {
    if (event.target === qs("adminUserAccessModal")) {
      closeAdminUserAccessModal();
    }
  });

  qs("adminUserDeleteCloseBtn")?.addEventListener("click", closeAdminUserDeleteModal);
  qs("adminUserDeleteConfirmBtn")?.addEventListener("click", async () => {
    try {
      await confirmAdminUserDelete();
    } catch (err) {
      setAdminUsersStatus(err.message, "error");
      closeAdminUserDeleteModal();
    }
  });
  qs("adminUserDeleteModal")?.addEventListener("click", (event) => {
    if (event.target === qs("adminUserDeleteModal")) {
      closeAdminUserDeleteModal();
    }
  });
}

function bindSavedScansPage() {
  const searchInput = qs("savedScansSearchInput");
  if (searchInput) {
    profileState.savedScansQuery = searchInput.value || "";
    // Client-side only: filters the already-loaded rows, never re-queries the API.
    searchInput.addEventListener("input", () => {
      profileState.savedScansQuery = searchInput.value || "";
      paintSavedScans({ ok: true });
    });
  }

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
  qs("savedScanDeleteModal")?.addEventListener("keydown", (event) => {
    const modal = qs("savedScanDeleteModal");
    if (!modal || modal.classList.contains("hidden")) return;
    if (event.key === "Escape") {
      event.preventDefault();
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

function isProfilePreferencesPage() {
  return Boolean(qs("profilePreferencesForm")) && !isProfileResumePage();
}

async function initProfilePage() {
  try {
    if (isSavedScansPage()) {
      await bindSavedScansPage();
      return;
    }

    if (isProfilePreferencesPage()) {
      bindProfilePreferencesInteractions();
      await loadProfilePreferences();
      return;
    }

    if (isProfileResumePage()) {
      clearStatus();
      try {
        await loadCurrentUser();
      } catch {
        profileState.currentUser = null;
      }
      bindUploadInteractions();
      if (isResumeOnboardingMode()) {
        await loadResumes();
        return;
      }
      bindDeleteInteractions();
      bindResumeRoleMappingInteractions();
      bindProfileResumeKeyboardInteractions();
      bindProfilePlanningOptionsInteractions();
      bindProfileTabs();
      bindPipelineRunsInteractions();
      bindAdminUsersInteractions();
      qs("resumeSection")?.setAttribute("data-profile-tab-panel", "");
      qs("profilePipelineRunsSection")?.setAttribute("data-profile-tab-panel", "");
      qs("profileAdminUsersSection")?.setAttribute("data-profile-tab-panel", "");
      await loadResumes();
      activateProfileTab(getProfileTabTargetFromUrl());
      if (qs("profileAdminUsersSection")) {
        await loadAdminUsers();
      }
    }
  } catch (err) {
    if (isSavedScansPage()) {
      renderSavedScans([], { ok: false, error: err.message });
    } else if (isProfilePreferencesPage()) {
      setProfilePreferencesStatus(`Failed to load preferences: ${err.message}`, "error");
    } else {
      setStatus(`Failed to load resumes: ${err.message}`, "error");
    }
  }
}

window.addEventListener("DOMContentLoaded", initProfilePage);
