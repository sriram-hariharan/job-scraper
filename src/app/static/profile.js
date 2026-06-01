const profileState = {
  pendingDeleteResumeName: null,
  pendingDeleteScanId: null,
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
  banner.className = `profile-inline-status ${tone}`;
  if (!message) {
    banner.classList.add("hidden");
  }
}

function hydrateProfilePreferencesForm(preferences) {
  setProfilePreferenceCheckedValues("selected_role_families", preferences?.selected_role_families || []);
  setProfilePreferenceCheckedValues("target_seniority", preferences?.target_seniority || []);
  setProfilePreferenceTextareaList("profilePreferredLocationsInput", preferences?.preferred_locations || []);
  setProfilePreferenceTextareaList("profilePreferredSkillsInput", preferences?.preferred_skills || []);
  setProfilePreferenceTextareaList("profileExcludedKeywordsInput", preferences?.excluded_keywords || []);
}

function collectProfilePreferences() {
  const current = profileState.onboardingPreferences || {};
  return {
    onboarding_completed: Boolean(current.onboarding_completed),
    selected_role_families: profilePreferenceCheckedValues("selected_role_families"),
    target_seniority: profilePreferenceCheckedValues("target_seniority"),
    preferred_locations: splitProfilePreferenceList(qs("profilePreferredLocationsInput")?.value),
    preferred_skills: splitProfilePreferenceList(qs("profilePreferredSkillsInput")?.value),
    excluded_keywords: splitProfilePreferenceList(qs("profileExcludedKeywordsInput")?.value),
  };
}

async function loadProfilePreferences() {
  const form = qs("profilePreferencesForm");
  if (!form) return;
  setProfilePreferencesStatus("Loading preferences...");
  const payload = await fetchJson("/onboarding/preferences");
  profileState.onboardingPreferences = payload.preferences || {};
  profileState.onboardingRequirements = payload.requirements || {};
  hydrateProfilePreferencesForm(profileState.onboardingPreferences);
  profileState.preferencesLoaded = true;
  setProfilePreferencesStatus("");
}

async function saveProfilePreferences() {
  const saveBtn = qs("profilePreferencesSaveBtn");
  const preferences = collectProfilePreferences();
  if (!preferences.selected_role_families.length) {
    setProfilePreferencesStatus("Select at least one role family before saving.", "error");
    return;
  }

  if (saveBtn) saveBtn.disabled = true;
  setProfilePreferencesStatus("Saving preferences...");
  try {
    const payload = await postJson("/onboarding/preferences", preferences);
    profileState.onboardingPreferences = payload.preferences || preferences;
    profileState.onboardingRequirements = payload.requirements || profileState.onboardingRequirements || {};
    hydrateProfilePreferencesForm(profileState.onboardingPreferences);
    setProfilePreferencesStatus("Preferences saved.", "success");
  } catch (err) {
    setProfilePreferencesStatus(err.message, "error");
  } finally {
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

function formatPercent(value) {
  if (value === null || value === undefined || value === "") return "-";
  const number = Number(value);
  if (!Number.isFinite(number)) return "-";
  return `${Math.round(number)}%`;
}

function setStatus(message, tone = "info") {
  const banner = qs("resumeStatusBanner");
  banner.textContent = message || "";
  banner.className = `profile-inline-status ${tone}`;
  if (!message) {
    banner.classList.add("hidden");
  }
}

function clearStatus() {
  const banner = qs("resumeStatusBanner");
  banner.textContent = "";
  banner.className = "profile-inline-status hidden";
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

function renderPipelineRuns(runs) {
  const tbody = qs("pipelineRunsTableBody");
  const meta = qs("pipelineRunsMeta");
  if (!tbody || !meta) return;

  const items = Array.isArray(runs) ? runs : [];
  profileState.pipelineRuns = items;
  meta.textContent = `${items.length} pipeline run${items.length === 1 ? "" : "s"} shown`;

  if (!items.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="8" class="pipeline-runs-empty-cell">No pipeline runs yet.</td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = items.map((run) => {
    const runId = escapeHtml(run.run_id || "");
    const tone = pipelineRunStatusTone(run.status);
    const summary = run.summary_message || run.stage_message || run.error || "-";
    const finalJobs = run.final_job_count ?? run.counts?.final_jobs ?? "-";
    return `
      <tr data-pipeline-run-id="${runId}">
        <td>
          <div class="pipeline-run-date">${escapeHtml(formatDateTime(run.started_at || "")) || "-"}</div>
          <div class="pipeline-run-id">${runId}</div>
        </td>
        <td>
          <span class="pipeline-run-status is-${escapeHtml(tone)}">
            ${escapeHtml(pipelineRunStatusLabel(run.status))}
          </span>
        </td>
        <td class="pipeline-run-summary-cell">${escapeHtml(summary)}</td>
        <td>${escapeHtml(String(finalJobs))}</td>
        <td class="pipeline-run-compact-cell">${escapeHtml(pipelineRunCountsSummary(run.counts))}</td>
        <td class="pipeline-run-compact-cell">${escapeHtml(pipelineRunSettingsSummary(run.config))}</td>
        <td>
          <button type="button" class="ghost-btn btn-sm pipeline-run-action-btn pipeline-run-view-btn" data-pipeline-run-view="${runId}">View</button>
        </td>
        <td>
          <button type="button" class="pipeline-run-action-btn pipeline-run-rerun-btn" data-pipeline-run-rerun="${runId}">Re-run</button>
        </td>
      </tr>
    `;
  }).join("");
}

function buildPaginationSequence(currentPage, totalPages) {
  const pages = [];
  if (totalPages <= 7) {
    for (let page = 1; page <= totalPages; page += 1) {
      pages.push(page);
    }
    return pages;
  }

  pages.push(1);

  const start = Math.max(2, currentPage - 1);
  const end = Math.min(totalPages - 1, currentPage + 1);

  if (start > 2) pages.push("ellipsis-left");
  for (let page = start; page <= end; page += 1) {
    pages.push(page);
  }
  if (end < totalPages - 1) pages.push("ellipsis-right");

  pages.push(totalPages);
  return pages;
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
  metaEl.textContent = `Showing ${startRow}-${endRow} of ${totalCount} · Page ${currentPage} of ${totalPages}`;

  const buttons = [];
  buttons.push(`
    <button
      type="button"
      class="application-pagination-btn"
      data-pipeline-runs-page="${currentPage - 1}"
      ${profileState.pipelineRunsHasPrevious ? "" : "disabled"}
    >
      Prev
    </button>
  `);

  buildPaginationSequence(currentPage, totalPages).forEach((item) => {
    if (typeof item === "string" && item.startsWith("ellipsis")) {
      buttons.push(`<span class="application-pagination-ellipsis">…</span>`);
      return;
    }

    buttons.push(`
      <button
        type="button"
        class="application-pagination-btn ${item === currentPage ? "is-active" : ""}"
        data-pipeline-runs-page="${item}"
      >
        ${item}
      </button>
    `);
  });

  buttons.push(`
    <button
      type="button"
      class="application-pagination-btn"
      data-pipeline-runs-page="${currentPage + 1}"
      ${profileState.pipelineRunsHasNext ? "" : "disabled"}
    >
      Next
    </button>
  `);

  actionsEl.innerHTML = buttons.join("");
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
  tbody.innerHTML = `<tr><td colspan="8" class="pipeline-runs-empty-cell">Loading pipeline runs...</td></tr>`;
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
        : `<div class="pipeline-runs-empty-cell">No agent trace recorded for this run.</div>`}
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

function renderPipelineRunDetail(data, tracePayload = {}, traceError = "") {
  const run = data.run || {};
  const statusJson = data.status_json || {};
  const configJson = data.config_json || {};
  const config = run.config || statusJson.config || configJson.config || {};
  const counts = run.counts || statusJson.counts || {};
  const outcomeMetrics = getPipelineRunOutcomeMetrics(counts);
  const stageOrder = Array.isArray(statusJson.stage_order) ? statusJson.stage_order : [];
  const completedStages = new Set(Array.isArray(statusJson.completed_stages) ? statusJson.completed_stages : []);

  qs("pipelineRunStatsTitle").textContent = "Pipeline run stats";
  qs("pipelineRunStatsSubtitle").textContent = run.run_id || "Persisted run details.";
  qs("pipelineRunStatsBody").innerHTML = `
    <section class="pipeline-run-detail-panel">
      <h4>Run</h4>
      ${renderKeyValueList([
        ["Status", pipelineRunStatusLabel(run.status)],
        ["Started", formatDateTime(run.started_at || "")],
        ["Completed", formatDateTime(run.completed_at || "")],
        ["Current stage", run.current_stage || ""],
        ["Summary", run.summary_message || statusJson.summary_message || ""],
        ["Error", run.error || statusJson.error || ""],
      ])}
    </section>

    <section class="pipeline-run-detail-panel">
      <h4>Run outcomes</h4>
      <div class="pipeline-run-count-grid">
        ${outcomeMetrics.length
          ? outcomeMetrics.map((metric) => `
              <div class="pipeline-run-count-tile is-${escapeHtml(metric.tone)}">
                <span>${escapeHtml(metric.label)}</span>
                <strong>${escapeHtml(formatMetricValue(metric.value))}</strong>
              </div>
            `).join("")
          : `<div class="pipeline-runs-empty-cell">No user-facing outcome metrics were persisted for this run.</div>`}
      </div>
    </section>

    <section class="pipeline-run-detail-panel">
      <h4>Settings</h4>
      ${renderKeyValueList([
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
    </section>

    <section class="pipeline-run-detail-panel">
      <h4>Stages</h4>
      <div class="pipeline-run-stage-list">
        ${stageOrder.length
          ? stageOrder.map((stage) => `
              <span class="pipeline-run-stage-chip ${completedStages.has(stage) ? "is-complete" : ""}">
                ${completedStages.has(stage) ? "✓" : "○"} ${escapeHtml(stage)}
              </span>
            `).join("")
          : `<span class="pipeline-runs-empty-cell">No stage list persisted for this run.</span>`}
      </div>
    </section>

    ${renderAgenticWorkflowSummaryPanel(data.agentic_workflow_summary)}

    ${renderAgentTracePanel(tracePayload, traceError)}
  `;
}

async function openPipelineRunStatsModal(runId) {
  qs("pipelineRunStatsBody").innerHTML = `<div class="pipeline-runs-empty-cell">Loading run details...</div>`;
  qs("pipelineRunStatsModal").classList.remove("hidden");
  const detailPromise = fetchJson(`/profile/pipeline-runs/${encodeURIComponent(runId)}`);
  const tracePromise = fetchJson(`/profile/pipeline-runs/${encodeURIComponent(runId)}/agent-trace`)
    .then((payload) => ({ payload, error: "" }))
    .catch((err) => ({ payload: {}, error: err.message || "Agent trace could not be loaded." }));
  const [data, trace] = await Promise.all([detailPromise, tracePromise]);
  renderPipelineRunDetail(data, trace.payload, trace.error);
}

function closePipelineRunStatsModal() {
  qs("pipelineRunStatsModal")?.classList.add("hidden");
}

function renderPipelineRunRerunSummary(run) {
  const config = run?.config && typeof run.config === "object" ? run.config : {};
  const counts = run?.counts && typeof run.counts === "object" ? run.counts : {};
  const started = formatDateTime(run?.started_at || "");
  const summary = run?.summary_message || run?.stage_message || run?.error || "";
  const finalJobs = run?.final_job_count ?? counts.final_jobs ?? "";
  const llmActions = Array.isArray(config.llm_actions)
    ? config.llm_actions.join(", ")
    : config.llm_actions;
  qs("pipelineRunRerunTitle").textContent = "Re-run pipeline";
  qs("pipelineRunRerunSubtitle").textContent = run?.run_id || "Persisted run";
  qs("pipelineRunRerunBody").innerHTML = `
    <section class="pipeline-run-detail-panel pipeline-run-rerun-panel">
      <h4>Run snapshot</h4>
      ${renderKeyValueList([
        ["Status", pipelineRunStatusLabel(run?.status)],
        ["Started", started],
        ["Summary", summary],
        ["Final jobs", finalJobs],
        ["Counts", pipelineRunCountsSummary(counts)],
      ])}
    </section>

    <section class="pipeline-run-detail-panel pipeline-run-rerun-panel">
      <h4>Re-run settings</h4>
      ${renderKeyValueList([
        ["Job limit", config.job_limit ?? 50],
        ["Packet limit", config.job_packet_limit ?? 0],
        ["LLM actions", llmActions],
        ["Planning only", config.planning_only ? "Yes" : "No"],
        ["Generate suggestions", config.generate_tailoring ? "Yes" : "No"],
        ["Generate LLM suggestions", config.generate_llm_tailoring ? "Yes" : "No"],
        ["Refresh LLM suggestions", config.refresh_llm_tailoring ? "Yes" : "No"],
        ["LLM fallback ranking", config.generate_llm_fallback ? "Yes" : "No"],
        ["LLM judging", config.generate_llm_adjudication ? "Yes" : "No"],
      ])}
    </section>
  `;
}

function openPipelineRunRerunModal(runId) {
  const run = getPipelineRunById(runId);
  if (!run) {
    throw new Error("Pipeline run was not found on this page.");
  }

  profileState.pendingRerunRunId = runId;
  renderPipelineRunRerunSummary(run);
  qs("pipelineRunRerunConfirmBtn").disabled = false;
  qs("pipelineRunRerunConfirmBtn").textContent = "Yes";
  qs("pipelineRunRerunModal")?.classList.remove("hidden");
}

function closePipelineRunRerunModal() {
  profileState.pendingRerunRunId = null;
  qs("pipelineRunRerunModal")?.classList.add("hidden");
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
      confirmBtn.textContent = "Yes";
    }
    throw err;
  }
}


function isResumeOnboardingMode() {
  const params = new URLSearchParams(window.location.search);
  return params.get("onboarding") === "resume_upload";
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
      Upload at least one PDF resume to unlock Live Pipeline.
    `;
    return;
  }

  banner.className = "profile-inline-status success";
  banner.innerHTML = `
    <strong>Resume uploaded.</strong>
    Live Pipeline is now unlocked.
    <a class="ghost-btn btn-sm" href="/">Continue to Live Pipeline</a>
  `;
}

function getResumeDeleteModal() {
  return qs("resumeDeleteModal");
}

function openResumeDeleteModal(resumeName) {
  profileState.pendingDeleteResumeName = resumeName || "";
  qs("resumeDeleteModalName").textContent = resumeName || "-";
  getResumeDeleteModal().classList.remove("hidden");
}

function closeResumeDeleteModal() {
  profileState.pendingDeleteResumeName = null;
  qs("resumeDeleteModalName").textContent = "-";
  getResumeDeleteModal().classList.add("hidden");
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

function renderResumeRoleMappingPanel(resume) {
  const resumeName = String(resume?.resume_name || "");
  const families = Array.isArray(profileState.resumeRoleFamilies) ? profileState.resumeRoleFamilies : [];
  if (!families.length) return "";

  const assignedCount = resumeRoleMappingsFor(resumeName).length;
  const summary = assignedCount
    ? `${assignedCount} role famil${assignedCount === 1 ? "y" : "ies"} assigned`
    : "Assign role families";

  const options = families.map((family) => {
    const roleFamilyId = String(family.role_family_id || "");
    const mapping = resumeRoleMappingFor(resumeName, roleFamilyId);
    const checked = Boolean(mapping);
    const isDefault = Boolean(mapping?.is_default_for_role);
    const displayName = family.display_name || roleFamilyId;

    return `
      <label class="resume-role-family-option${checked ? " is-selected" : ""}">
        <span class="resume-role-family-main">
          <input
            type="checkbox"
            data-resume-role-toggle
            data-resume-name="${escapeHtml(resumeName)}"
            data-role-family-id="${escapeHtml(roleFamilyId)}"
            ${checked ? "checked" : ""}
          />
          <span>${escapeHtml(displayName)}</span>
        </span>
        <span class="resume-role-default-wrap">
          <input
            type="radio"
            name="resume-role-default-${escapeHtml(roleFamilyId)}"
            data-resume-role-default
            data-resume-name="${escapeHtml(resumeName)}"
            data-role-family-id="${escapeHtml(roleFamilyId)}"
            ${isDefault ? "checked" : ""}
            ${checked ? "" : "disabled"}
          />
          <span>Default</span>
        </span>
      </label>
    `;
  }).join("");

  return `
    <details class="resume-role-mapping-panel">
      <summary>
        <span class="resume-role-summary-title">
          <span class="resume-role-summary-caret" aria-hidden="true"></span>
          <span>Role family mapping</span>
        </span>
        <span>${escapeHtml(summary)}</span>
      </summary>
      <div class="resume-role-mapping-grid">
        ${options}
      </div>
    </details>
  `;
}

function renderResumeList(items) {
  const listEl = qs("resumeList");
  const metaEl = qs("resumeListMeta");
  const resumes = Array.isArray(items) ? items : [];

  metaEl.textContent = `${resumes.length} resume${resumes.length === 1 ? "" : "s"} available`;

  if (!resumes.length) {
    listEl.innerHTML = `
      <div class="resume-empty-state">
        No resumes uploaded yet.
      </div>
    `;
    return;
  }

  listEl.innerHTML = resumes.map((resume) => `
    <article class="resume-row">
      <div class="resume-row-main">
        <div class="resume-name">${escapeHtml(resume.resume_name || "")}</div>
        <div class="resume-meta">
          <span>${escapeHtml(formatBytes(resume.size_bytes || 0))}</span>
          <span>${escapeHtml(formatDateTime(resume.modified_at || ""))}</span>
        </div>
      </div>

      <div class="resume-row-actions">
        <button
          type="button"
          class="ghost-btn resume-delete-btn"
          data-resume-delete="${escapeHtml(resume.resume_name || "")}"
        >
          Delete
        </button>
      </div>

      ${renderResumeRoleMappingPanel(resume)}
    </article>
  `).join("");
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
  await loadResumeRoleMappings();
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
  const label = [
    scan?.job_company || "",
    scan?.job_title || "",
    scan?.resume_name || scan?.resume_filename || "",
  ].filter(Boolean).join(" / ") || "this saved scan";
  qs("savedScanDeleteName").textContent = label;
  qs("savedScanDeleteModal").classList.remove("hidden");
}

function closeSavedScanDeleteModal() {
  profileState.pendingDeleteScanId = null;
  const name = qs("savedScanDeleteName");
  if (name) name.textContent = "this saved scan";
  qs("savedScanDeleteModal")?.classList.add("hidden");
}

function renderSavedScans(items, { ok = true, error = "" } = {}) {
  const tbody = qs("savedScansTableBody");
  const metaEl = qs("savedScansMeta");
  const scans = Array.isArray(items) ? items : [];

  if (!ok) {
    metaEl.textContent = "Saved scans unavailable";
    tbody.innerHTML = `
      <tr>
        <td colspan="9" class="saved-scans-empty-cell">
          ${escapeHtml(error || "Could not load saved scans from Postgres.")}
        </td>
      </tr>
    `;
    return;
  }

  metaEl.textContent = `${scans.length} saved scan${scans.length === 1 ? "" : "s"} shown`;

  if (!scans.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="9" class="saved-scans-empty-cell">
          No saved scans yet.
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = scans.map((scan) => {
    const statusMeta = savedScanStatusMeta(scan.scan_status);

    return `
      <tr class="saved-scan-row saved-scan-row-${escapeHtml(statusMeta.tone)}" data-saved-scan-id="${escapeHtml(scan.scan_id || "")}">
        <td>${escapeHtml(formatDateTime(scan.scan_timestamp || ""))}</td>
        <td>${escapeHtml(scan.job_company || "-")}</td>
        <td>${escapeHtml(scan.job_title || "-")}</td>
        <td>${escapeHtml(scan.resume_name || scan.resume_filename || "-")}</td>
        <td>${escapeHtml(normalizeSavedScanSource(scan.resume_source))}</td>
        <td>
          <span class="saved-scan-status-badge ${escapeHtml(statusMeta.tone)}">
            ${escapeHtml(statusMeta.label)}
          </span>
        </td>
        <td>${escapeHtml(formatPercent(scan.match_rate))}</td>
        <td>
          ${getSavedScanOpenHref(scan)
            ? `<a class="saved-scan-action-badge ${escapeHtml(statusMeta.tone)} saved-scan-open-link" href="${escapeHtml(getSavedScanOpenHref(scan))}">${escapeHtml(statusMeta.action)}</a>`
            : `<span class="saved-scan-action-badge ${escapeHtml(statusMeta.tone)}">${escapeHtml(statusMeta.action)}</span>`}
        </td>
        <td class="saved-scan-row-delete-cell">
          <button
            type="button"
            class="saved-scan-delete-btn"
            aria-label="Delete saved scan"
            title="Delete saved scan"
            data-saved-scan-delete="${escapeHtml(scan.scan_id || "")}"
            data-saved-scan-name="${escapeHtml(scan.resume_name || scan.resume_filename || "saved scan")}"
          ></button>
        </td>
      </tr>
    `;
  }).join("");
}

async function loadSavedScans() {
  const tbody = qs("savedScansTableBody");
  const metaEl = qs("savedScansMeta");
  if (!tbody || !metaEl) return;

  metaEl.textContent = "Loading saved scans...";
  tbody.innerHTML = `
    <tr>
      <td colspan="9" class="saved-scans-empty-cell">Loading saved scans...</td>
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
    showProfilePlanningUploadCallout();
    return;
  }

  if (results.uploaded.length && results.failed.length) {
    setStatus(
      `Uploaded ${results.uploaded.length} file${results.uploaded.length === 1 ? "" : "s"}, failed ${results.failed.length}.`,
      "error"
    );
    showProfilePlanningUploadCallout();
    return;
  }

  const firstError = results.failed[0]?.error || "Upload failed.";
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
}

function bindDeleteInteractions() {
  qs("resumeList").addEventListener("click", (event) => {
    const button = event.target.closest("[data-resume-delete]");
    if (!button) return;

    const resumeName = button.dataset.resumeDelete || "";
    openResumeDeleteModal(resumeName);
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
  qs("resumeList").addEventListener("change", async (event) => {
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
    const target = qs(targetId);
    if (!target) return;

    document.querySelectorAll(".profile-tab-btn").forEach((tab) => {
      tab.classList.toggle("is-active", tab === button);
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
  });
}

function bindProfilePreferencesInteractions() {
  const form = qs("profilePreferencesForm");
  if (!form) return;

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    saveProfilePreferences();
  });
  qs("profilePreferencesSelectAllRolesBtn")?.addEventListener("click", () => {
    setProfilePreferenceCheckboxGroup("selected_role_families", true);
  });
  qs("profilePreferencesClearAllRolesBtn")?.addEventListener("click", () => {
    setProfilePreferenceCheckboxGroup("selected_role_families", false);
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
        closePipelineRunStatsModal();
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
  qs("pipelineRunStatsModal")?.addEventListener("click", (event) => {
    if (event.target === qs("pipelineRunStatsModal")) {
      closePipelineRunStatsModal();
    }
  });
  qs("pipelineRunRerunCloseBtn")?.addEventListener("click", closePipelineRunRerunModal);
  qs("pipelineRunRerunCancelBtn")?.addEventListener("click", closePipelineRunRerunModal);
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
      bindDeleteInteractions();
      bindResumeRoleMappingInteractions();
      bindProfilePlanningOptionsInteractions();
      bindProfileTabs();
      bindPipelineRunsInteractions();
      bindAdminUsersInteractions();
      qs("resumeSection")?.setAttribute("data-profile-tab-panel", "");
      qs("profilePipelineRunsSection")?.setAttribute("data-profile-tab-panel", "");
      qs("profileAdminUsersSection")?.setAttribute("data-profile-tab-panel", "");
      await loadResumes();
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
