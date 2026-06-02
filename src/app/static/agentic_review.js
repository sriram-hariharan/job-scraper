function getAgenticReviewRunId() {
  return document.querySelector("[data-agentic-review-run-id]")?.dataset?.agenticReviewRunId || "";
}

function getWorkflowSummary(payload = {}) {
  const summary = payload?.agentic_workflow_summary?.summary_json;
  return summary && typeof summary === "object" ? summary : {};
}

function getWorkflowVerification(payload = {}) {
  const verification = payload?.agentic_workflow_verification?.verification_json;
  return verification && typeof verification === "object" ? verification : {};
}

function getWorkflowManifest(payload = {}) {
  const manifest = payload?.agentic_workflow_manifest?.manifest_json;
  return manifest && typeof manifest === "object" ? manifest : {};
}

function getWorkflowExecutionPlan(payload = {}) {
  const plan = payload?.agentic_workflow_execution_plan?.plan_json;
  return plan && typeof plan === "object" ? plan : {};
}

function getWorkflowDryRun(payload = {}) {
  const result = payload?.agentic_workflow_dry_run?.result_json;
  return result && typeof result === "object" ? result : {};
}

function formatReviewLabel(value) {
  const raw = String(value || "").trim();
  if (!raw) return "-";
  return raw.replaceAll("_", " ");
}

function statusToneForValue(value) {
  const normalized = String(value || "").trim().toLowerCase();
  if (["passed", "succeeded", "ready_to_apply", "apply_now", "no_tailoring_needed"].includes(normalized)) {
    return "ready";
  }
  if (["warning", "review", "manual_review", "tailor_first", "tailor_then_apply", "tailor_before_apply", "light_tailoring", "manual_review_before_tailoring"].includes(normalized)) {
    return "review";
  }
  if (["failed", "blocked", "hold_or_skip", "skip_for_now", "do_not_tailor", "reject"].includes(normalized)) {
    return "blocked";
  }
  if (["source_watch", "watch_source", "monitor"].includes(normalized)) {
    return "watch";
  }
  return "info";
}

function renderReviewPill(value, extraClass = "") {
  const clean = String(value || "").trim();
  if (!clean) return `<span class="agentic-review-muted">-</span>`;
  return `
    <span class="agentic-review-pill is-${escapeHtml(statusToneForValue(clean))} ${escapeHtml(extraClass)}">
      ${escapeHtml(formatReviewLabel(clean))}
    </span>
  `;
}

function renderReasonChips(value) {
  const values = Array.isArray(value)
    ? value
    : String(value || "")
      .split(/[;,]/)
      .map((item) => item.trim())
      .filter(Boolean);
  if (!values.length) return `<span class="agentic-review-muted">none</span>`;
  return `
    <div class="agentic-review-chip-list">
      ${values.slice(0, 5).map((item) => `<span>${escapeHtml(formatReviewLabel(item))}</span>`).join("")}
    </div>
  `;
}

function renderAgenticReviewStatus(payload = {}) {
  const run = payload.run || {};
  const summary = getWorkflowSummary(payload);
  const verification = getWorkflowVerification(payload);
  const counts = run?.counts && typeof run.counts === "object" ? run.counts : {};
  const missingArtifacts = Array.isArray(verification.missing_artifacts)
    ? verification.missing_artifacts
    : Array.isArray(summary.missing_artifacts) ? summary.missing_artifacts : [];
  const verificationStatus = String(verification.validation_status || "unknown").trim().toLowerCase();
  const panel = qs("agenticReviewStatusCard");
  if (!panel) return;
  panel.innerHTML = `
    <div class="agentic-review-status-content">
      <div>
        <div class="agentic-review-kicker">Pipeline run</div>
        <h2>${escapeHtml(run?.run_id || "Unknown run")}</h2>
        <p>${escapeHtml(run?.summary_message || run?.stage_message || run?.error || "No run summary available.")}</p>
      </div>
      <div class="agentic-review-run-pills">
        ${renderReviewPill(pipelineRunStatusLabel(run?.status), "agentic-review-run-status")}
        ${renderReviewPill(formatWorkflowVerificationStatus(verificationStatus), "agentic-review-verification-pill")}
      </div>
    </div>
    <div class="agentic-review-health-strip">
      ${renderWorkflowSummaryMetric("Ready to apply", summary.ready_to_apply_count ?? 0)}
      ${renderWorkflowSummaryMetric("Tailor then apply", summary.tailor_then_apply_count ?? 0)}
      ${renderWorkflowSummaryMetric("Hold / skip", summary.hold_or_skip_count ?? 0)}
      ${renderWorkflowSummaryMetric("Source watch", summary.source_watch_count ?? 0)}
      ${renderWorkflowSummaryMetric("Verification", formatWorkflowVerificationStatus(verificationStatus))}
      ${renderWorkflowSummaryMetric("Missing artifacts", missingArtifacts.length)}
      ${renderWorkflowSummaryMetric("Final jobs", run?.final_job_count ?? counts.final_jobs ?? "-")}
      ${renderWorkflowSummaryMetric("Scraped / filtered", `${counts.scraped_jobs ?? counts.scraped ?? "-"} / ${counts.filtered_jobs ?? counts.filtered ?? "-"}`)}
    </div>
  `;
}

function countBy(rows, field) {
  return rows.reduce((acc, row) => {
    const key = String(row?.[field] || "<empty>").trim() || "<empty>";
    acc[key] = (acc[key] || 0) + 1;
    return acc;
  }, {});
}

function renderAgenticReviewCell(row, column) {
  const value = row?.[column.key];
  if (column.type === "pill") return renderReviewPill(value);
  if (column.type === "reasons") return renderReasonChips(value);
  if (column.type === "boolean") return renderReviewPill(String(value || "").toLowerCase() === "true" || value === true ? "yes" : "no");
  return escapeHtml(value || "-");
}

function renderAgenticReviewRows(rows, columns) {
  const items = Array.isArray(rows) ? rows.slice(0, 50) : [];
  if (!items.length) {
    return `<div class="pipeline-runs-empty-cell">No advisory rows recorded for this run.</div>`;
  }
  return `
    <div class="agentic-review-table-wrap">
      <table class="agentic-review-table">
        <thead>
          <tr>${columns.map((column) => `<th>${escapeHtml(column.label)}</th>`).join("")}</tr>
        </thead>
        <tbody>
          ${items.map((row) => `
            <tr>
              ${columns.map((column) => `<td>${renderAgenticReviewCell(row, column)}</td>`).join("")}
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `;
}

function renderAgenticReviewAdvisoryPanel(panelId, title, description, rows, countField, columns) {
  const panel = qs(panelId);
  if (!panel) return;
  const safeRows = Array.isArray(rows) ? rows : [];
  const counts = countBy(safeRows, countField);
  panel.innerHTML = `
    <div class="agentic-workflow-header">
      <div>
        <h2>${escapeHtml(title)}</h2>
        <p>${escapeHtml(description)}</p>
      </div>
      <span class="agentic-workflow-badge">Advisory</span>
    </div>
    <div class="agentic-review-section-counts">
      <strong>${escapeHtml(countField.replaceAll("_", " "))}</strong>
      <span>${renderReasonChips(Object.entries(counts).map(([key, value]) => `${key}:${value}`))}</span>
    </div>
    ${renderAgenticReviewRows(safeRows, columns)}
  `;
}

function renderAgenticReviewDiagnosticsPanel(
  workflowVerification = {},
  workflowManifest = {},
  workflowExecutionPlan = {},
  workflowDryRun = {},
  agentFeedback = {},
) {
  const panel = qs("agenticReviewDiagnosticsPanel");
  if (!panel) return;
  const feedbackSection = renderAgenticReviewFeedbackSection(agentFeedback);
  const available = Boolean(workflowVerification?.available);
  const verification = workflowVerification?.verification_json && typeof workflowVerification.verification_json === "object"
    ? workflowVerification.verification_json
    : {};
  const manifestAvailable = Boolean(workflowManifest?.available);
  const manifest = workflowManifest?.manifest_json && typeof workflowManifest.manifest_json === "object"
    ? workflowManifest.manifest_json
    : {};
  const planAvailable = Boolean(workflowExecutionPlan?.available);
  const executionPlan = workflowExecutionPlan?.plan_json && typeof workflowExecutionPlan.plan_json === "object"
    ? workflowExecutionPlan.plan_json
    : {};
  const dryRunAvailable = Boolean(workflowDryRun?.available);
  const dryRunResult = workflowDryRun?.result_json && typeof workflowDryRun.result_json === "object"
    ? workflowDryRun.result_json
    : {};
  if (
    !available && !Object.keys(verification).length
    && !manifestAvailable && !Object.keys(manifest).length
    && !planAvailable && !Object.keys(executionPlan).length
    && !dryRunAvailable && !Object.keys(dryRunResult).length
  ) {
    panel.innerHTML = `
      <div class="agentic-workflow-header">
        <div>
          <h2>Artifacts / Diagnostics</h2>
          <p>Verifier, manifest, execution plan, and dry-run runner artifacts will appear here after a run produces them.</p>
        </div>
      </div>
      <div class="pipeline-runs-empty-cell">No agentic workflow manifest, execution plan, dry run, or verification recorded for this run.</div>
      ${feedbackSection}
    `;
    return;
  }

  const checkedArtifacts = Array.isArray(verification.checked_artifacts) ? verification.checked_artifacts : [];
  const missingArtifacts = Array.isArray(verification.missing_artifacts) ? verification.missing_artifacts : [];
  const reasonCodes = Array.isArray(verification.reason_codes) ? verification.reason_codes : [];
  const rowCounts = verification.row_counts && typeof verification.row_counts === "object" ? verification.row_counts : {};
  const consistencyChecks = verification.consistency_checks && typeof verification.consistency_checks === "object"
    ? verification.consistency_checks
    : {};
  const summary = verification.summary && typeof verification.summary === "object" ? verification.summary : {};

  panel.innerHTML = `
    <div class="agentic-workflow-header">
      <div>
        <h2>Artifacts / Diagnostics</h2>
        <p>Read-only artifact coverage and consistency checks from the workflow verifier.</p>
      </div>
      <span class="agentic-workflow-verification-status agentic-workflow-verification-status--${escapeHtml(String(verification.validation_status || "unknown").toLowerCase())}">
        ${escapeHtml(formatWorkflowVerificationStatus(verification.validation_status))}
      </span>
    </div>
    <div class="agentic-workflow-verification-sections">
      <div>
        <strong>Checked artifacts</strong>
        ${renderWorkflowVerificationList(checkedArtifacts)}
      </div>
      <div>
        <strong>Missing artifacts</strong>
        ${renderWorkflowVerificationList(missingArtifacts)}
      </div>
      <div>
        <strong>Reason codes</strong>
        ${renderWorkflowVerificationList(reasonCodes)}
      </div>
      <div>
        <strong>Summary</strong>
        ${renderWorkflowVerificationList(summary)}
      </div>
      <div>
        <strong>Row counts</strong>
        ${renderWorkflowVerificationList(rowCounts)}
      </div>
    </div>
    <details class="agentic-workflow-verification-details">
      <summary>Consistency checks</summary>
      ${renderWorkflowVerificationChecks(consistencyChecks)}
    </details>
    ${renderAgenticWorkflowManifestSection(workflowManifest)}
    ${renderAgenticWorkflowExecutionPlanSection(workflowExecutionPlan)}
    ${renderAgenticWorkflowDryRunSection(workflowDryRun)}
    ${feedbackSection}
  `;
}

function getAgentFeedbackSummary(agentFeedback = {}) {
  const summary = agentFeedback?.summary && typeof agentFeedback.summary === "object"
    ? agentFeedback.summary
    : {};
  return {
    total_events: Number(summary.total_events || 0),
    event_type_counts: summary.event_type_counts && typeof summary.event_type_counts === "object"
      ? summary.event_type_counts
      : {},
    target_type_counts: summary.target_type_counts && typeof summary.target_type_counts === "object"
      ? summary.target_type_counts
      : {},
    latest_event_at: String(summary.latest_event_at || ""),
  };
}

function renderAgentFeedbackCountChips(counts = {}) {
  const entries = Object.entries(counts || {})
    .filter(([key, value]) => String(key || "").trim() && Number(value || 0) > 0)
    .slice(0, 6);
  if (!entries.length) return `<span class="agentic-review-muted">none</span>`;
  return `
    <div class="agentic-review-chip-list">
      ${entries.map(([key, value]) => `<span>${escapeHtml(formatReviewLabel(key))}: ${escapeHtml(value)}</span>`).join("")}
    </div>
  `;
}

function renderAgentFeedbackRecentEvents(events = []) {
  const rows = Array.isArray(events) ? events.slice(0, 5) : [];
  if (!rows.length) {
    return `<div class="pipeline-runs-empty-cell">No feedback events recorded for this run yet.</div>`;
  }
  return `
    <div class="agentic-feedback-event-list">
      ${rows.map((event) => `
        <article class="agentic-feedback-event">
          <div>
            <strong>${escapeHtml(formatReviewLabel(event.event_type || "feedback"))}</strong>
            <span>${escapeHtml(formatReviewLabel(event.target_type || "target"))} · ${escapeHtml(event.target_id || "-")}</span>
          </div>
          <div class="agentic-feedback-event-meta">
            ${renderReviewPill(event.source || "feedback")}
            <span>${escapeHtml(event.created_at || "-")}</span>
          </div>
        </article>
      `).join("")}
    </div>
  `;
}

function renderAgenticReviewFeedbackSection(agentFeedback = {}) {
  const summary = getAgentFeedbackSummary(agentFeedback);
  const events = Array.isArray(agentFeedback?.events) ? agentFeedback.events : [];
  return `
    <section class="agentic-feedback-card">
      <div class="agentic-workflow-header">
        <div>
          <h2>Human Feedback</h2>
          <p>Read-only feedback events captured for this pipeline run. These diagnostics do not change scoring, queue order, or tailoring decisions.</p>
        </div>
        <span class="agentic-workflow-badge">Read-only</span>
      </div>
      <div class="agentic-feedback-metrics">
        ${renderWorkflowSummaryMetric("Total events", summary.total_events)}
        ${renderWorkflowSummaryMetric("Latest event", summary.latest_event_at || "-")}
      </div>
      <div class="agentic-feedback-counts">
        <div>
          <strong>Event types</strong>
          ${renderAgentFeedbackCountChips(summary.event_type_counts)}
        </div>
        <div>
          <strong>Target types</strong>
          ${renderAgentFeedbackCountChips(summary.target_type_counts)}
        </div>
      </div>
      ${renderAgentFeedbackRecentEvents(events)}
    </section>
  `;
}

function renderAgenticWorkflowManifestSection(workflowManifest = {}) {
  const available = Boolean(workflowManifest?.available);
  const manifest = workflowManifest?.manifest_json && typeof workflowManifest.manifest_json === "object"
    ? workflowManifest.manifest_json
    : {};
  const markdown = String(workflowManifest?.manifest_markdown || "");
  if (!available && !Object.keys(manifest).length) {
    return `
      <section class="agentic-workflow-manifest-card">
        <div class="agentic-workflow-header">
          <div>
            <h2>Agentic Workflow Manifest</h2>
            <p>The orchestration manifest artifact was not recorded for this run.</p>
          </div>
          <span class="agentic-workflow-verification-status agentic-workflow-verification-status--unknown">Missing</span>
        </div>
        <div class="pipeline-runs-empty-cell">No agentic workflow manifest recorded for this run.</div>
      </section>
    `;
  }

  const validation = manifest.validation && typeof manifest.validation === "object" ? manifest.validation : {};
  const validationStatus = String(validation.validation_status || "unknown").toLowerCase();
  const orderedKeys = Array.isArray(manifest.ordered_agent_keys) ? manifest.ordered_agent_keys : [];
  const agents = manifest.agents && typeof manifest.agents === "object" ? manifest.agents : {};
  const orderedAgents = orderedKeys
    .map((key) => agents[key] ? { key, ...agents[key] } : { key, agent_name: key })
    .filter((agent) => String(agent.key || agent.agent_key || "").trim());
  const generatedKinds = Array.isArray(manifest.generated_artifact_kinds) ? manifest.generated_artifact_kinds : [];
  const artifactFlow = Array.isArray(manifest.artifact_dependency_order) ? manifest.artifact_dependency_order : [];
  const featureFlags = Array.isArray(manifest.feature_flags) ? manifest.feature_flags : [];
  const reasonCodes = Array.isArray(validation.reason_codes) ? validation.reason_codes : [];

  return `
    <section class="agentic-workflow-manifest-card">
      <div class="agentic-workflow-header">
        <div>
          <h2>Agentic Workflow Manifest</h2>
          <p>${escapeHtml(manifest.workflow_name || "ApplyLens Agentic Workflow")} · ${escapeHtml(manifest.workflow_version || "unknown version")}</p>
        </div>
        <span class="agentic-workflow-verification-status agentic-workflow-verification-status--${escapeHtml(validationStatus)}">
          ${escapeHtml(formatWorkflowVerificationStatus(validationStatus))}
        </span>
      </div>
      <div class="agentic-review-manifest-metrics">
        ${renderWorkflowSummaryMetric("Agents", orderedAgents.length)}
        ${renderWorkflowSummaryMetric("Artifact kinds", generatedKinds.length)}
        ${renderWorkflowSummaryMetric("Feature flags", featureFlags.length)}
        ${renderWorkflowSummaryMetric("Validation", formatWorkflowVerificationStatus(validationStatus))}
      </div>
      <div class="agentic-workflow-verification-sections">
        <div>
          <strong>Ordered agent keys</strong>
          ${renderWorkflowVerificationList(orderedKeys)}
        </div>
        <div>
          <strong>Feature flags</strong>
          ${renderWorkflowVerificationList(featureFlags)}
        </div>
        <div>
          <strong>Validation reason codes</strong>
          ${renderWorkflowVerificationList(reasonCodes)}
        </div>
      </div>
      <div class="agentic-review-manifest-agent-list">
        ${orderedAgents.length ? orderedAgents.map(renderAgenticWorkflowManifestAgentRow).join("") : `<div class="pipeline-runs-empty-cell">No agents listed in manifest.</div>`}
      </div>
      <details class="agentic-workflow-verification-details">
        <summary>Generated artifact kinds</summary>
        ${renderWorkflowVerificationList(generatedKinds)}
      </details>
      <details class="agentic-workflow-verification-details">
        <summary>Artifact dependency order</summary>
        ${renderWorkflowVerificationList(artifactFlow)}
      </details>
      ${markdown ? `<details class="agentic-workflow-markdown"><summary>Manifest markdown</summary><pre>${escapeHtml(markdown)}</pre></details>` : ""}
    </section>
  `;
}

function renderAgenticWorkflowManifestAgentRow(agent = {}) {
  const provider = [agent.model_provider, agent.model_name].filter(Boolean).join(" / ") || "-";
  return `
    <article class="agentic-review-manifest-agent">
      <div>
        <strong>${escapeHtml(agent.agent_name || agent.key || agent.agent_key || "Unknown agent")}</strong>
        <span>${escapeHtml(agent.agent_version || "unknown version")} · ${escapeHtml(provider)}</span>
      </div>
      <div class="agentic-review-manifest-agent-pills">
        ${renderReviewPill(agent.advisory_only ? "advisory" : "not advisory")}
        ${agent.diagnostic_only ? renderReviewPill("diagnostic") : ""}
        ${renderReviewPill(agent.mutates_production_decisions ? "mutates decisions" : "no mutation")}
      </div>
    </article>
  `;
}

function renderAgenticWorkflowExecutionPlanSection(workflowExecutionPlan = {}) {
  const available = Boolean(workflowExecutionPlan?.available);
  const plan = workflowExecutionPlan?.plan_json && typeof workflowExecutionPlan.plan_json === "object"
    ? workflowExecutionPlan.plan_json
    : {};
  const markdown = String(workflowExecutionPlan?.plan_markdown || "");
  if (!available && !Object.keys(plan).length) {
    return `
      <section class="agentic-workflow-execution-plan-card">
        <div class="agentic-workflow-header">
          <div>
            <h2>Agentic Workflow Execution Plan</h2>
            <p>The dry-run execution plan artifact was not recorded for this run.</p>
          </div>
          <span class="agentic-workflow-verification-status agentic-workflow-verification-status--unknown">Missing</span>
        </div>
        <div class="pipeline-runs-empty-cell">No agentic workflow execution plan recorded for this run.</div>
      </section>
    `;
  }

  const validation = plan.validation && typeof plan.validation === "object" ? plan.validation : {};
  const validationStatus = String(validation.validation_status || "unknown").toLowerCase();
  const orderedSteps = Array.isArray(plan.ordered_steps) ? plan.ordered_steps : [];

  return `
    <section class="agentic-workflow-execution-plan-card">
      <div class="agentic-workflow-header">
        <div>
          <h2>Agentic Workflow Execution Plan</h2>
          <p>Dry-run diagnostic plan only. These planned steps are not executed from this page or artifact.</p>
        </div>
        <span class="agentic-workflow-verification-status agentic-workflow-verification-status--${escapeHtml(validationStatus)}">
          ${escapeHtml(formatWorkflowVerificationStatus(validationStatus))}
        </span>
      </div>
      <div class="agentic-review-plan-metrics">
        ${renderWorkflowSummaryMetric("Planner version", plan.planner_version || "-")}
        ${renderWorkflowSummaryMetric("Execution mode", plan.execution_mode || "-")}
        ${renderWorkflowSummaryMetric("Validation", formatWorkflowVerificationStatus(validationStatus))}
        ${renderWorkflowSummaryMetric("Steps", orderedSteps.length)}
      </div>
      <div class="agentic-review-plan-step-list">
        ${orderedSteps.length ? orderedSteps.map(renderAgenticWorkflowExecutionPlanStepRow).join("") : `<div class="pipeline-runs-empty-cell">No planned steps listed.</div>`}
      </div>
      ${markdown ? `<details class="agentic-workflow-markdown"><summary>Execution plan markdown</summary><pre>${escapeHtml(markdown)}</pre></details>` : ""}
    </section>
  `;
}

function renderAgenticWorkflowExecutionPlanStepRow(step = {}) {
  const provider = [step.model_provider, step.model_name].filter(Boolean).join(" / ") || "-";
  return `
    <article class="agentic-review-plan-step">
      <div>
        <strong>${escapeHtml(step.step_index || "-")}. ${escapeHtml(step.agent_name || step.agent_key || "Unknown agent")}</strong>
        <span>${escapeHtml(step.agent_version || "unknown version")} · ${escapeHtml(provider)}</span>
      </div>
      <div class="agentic-review-plan-step-pills">
        ${renderReviewPill(step.execution_status || "planned")}
        ${renderReviewPill(step.execution_enabled ? "enabled" : "disabled")}
      </div>
    </article>
  `;
}

function renderAgenticWorkflowDryRunSection(workflowDryRun = {}) {
  const available = Boolean(workflowDryRun?.available);
  const result = workflowDryRun?.result_json && typeof workflowDryRun.result_json === "object"
    ? workflowDryRun.result_json
    : {};
  const markdown = String(workflowDryRun?.report_markdown || "");
  if (!available && !Object.keys(result).length) {
    return `
      <section class="agentic-workflow-dry-run-card">
        <div class="agentic-workflow-header">
          <div>
            <h2>Agentic Workflow Dry Run</h2>
            <p>The dry-run runner result artifact was not recorded for this run.</p>
          </div>
          <span class="agentic-workflow-verification-status agentic-workflow-verification-status--unknown">Missing</span>
        </div>
        <div class="pipeline-runs-empty-cell">No agentic workflow dry run recorded for this run.</div>
      </section>
    `;
  }

  const validation = result.validation && typeof result.validation === "object" ? result.validation : {};
  const summary = result.summary && typeof result.summary === "object" ? result.summary : {};
  const validationStatus = String(validation.validation_status || "unknown").toLowerCase();
  const orderedSteps = Array.isArray(result.ordered_step_results) ? result.ordered_step_results : [];

  return `
    <section class="agentic-workflow-dry-run-card">
      <div class="agentic-workflow-header">
        <div>
          <h2>Agentic Workflow Dry Run</h2>
          <p>Diagnostic simulation only. No agents execute and no production fields are changed.</p>
        </div>
        <span class="agentic-workflow-verification-status agentic-workflow-verification-status--${escapeHtml(validationStatus)}">
          ${escapeHtml(formatWorkflowVerificationStatus(validationStatus))}
        </span>
      </div>
      <div class="agentic-review-dry-run-metrics">
        ${renderWorkflowSummaryMetric("Runner version", result.runner_version || "-")}
        ${renderWorkflowSummaryMetric("Execution mode", result.execution_mode || "-")}
        ${renderWorkflowSummaryMetric("Planned", result.planned_step_count ?? orderedSteps.length)}
        ${renderWorkflowSummaryMetric("Executed", result.executed_step_count ?? 0)}
        ${renderWorkflowSummaryMetric("Skipped", result.skipped_step_count ?? orderedSteps.length)}
        ${renderWorkflowSummaryMetric("Missing inputs", summary.missing_input_artifact_count ?? "-")}
      </div>
      <div class="agentic-review-dry-run-step-list">
        ${orderedSteps.length ? orderedSteps.map(renderAgenticWorkflowDryRunStepRow).join("") : `<div class="pipeline-runs-empty-cell">No dry-run steps listed.</div>`}
      </div>
      ${markdown ? `<details class="agentic-workflow-markdown"><summary>Dry-run report markdown</summary><pre>${escapeHtml(markdown)}</pre></details>` : ""}
    </section>
  `;
}

function renderAgenticWorkflowDryRunStepRow(step = {}) {
  return `
    <article class="agentic-review-dry-run-step">
      <div>
        <strong>${escapeHtml(step.step_index || "-")}. ${escapeHtml(step.agent_name || step.agent_key || "Unknown agent")}</strong>
        <span>${escapeHtml(step.agent_key || "")}</span>
      </div>
      <div class="agentic-review-dry-run-step-pills">
        ${renderReviewPill(step.execution_status || "skipped_dry_run")}
        ${renderReviewPill(step.execution_enabled ? "enabled" : "disabled")}
        ${renderReviewPill(step.did_execute ? "executed" : "not executed")}
        ${renderReviewPill(step.would_trace ? "would trace" : "no trace")}
      </div>
    </article>
  `;
}

function renderAgenticReviewData(payload, tracePayload) {
  renderAgenticReviewStatus(payload || {});

  const summaryNode = qs("agenticWorkflowSummaryPanel");
  if (summaryNode) {
    summaryNode.outerHTML = renderAgenticWorkflowSummaryPanel(payload.agentic_workflow_summary);
  }

  const verificationNode = qs("agenticWorkflowVerificationPanel");
  if (verificationNode) {
    verificationNode.outerHTML = renderAgenticWorkflowVerificationPanel(payload.agentic_workflow_verification);
  }

  renderAgenticReviewAdvisoryPanel(
    "agenticReviewPriorityPanel",
    "Job Prioritization",
    "Advisory priority labels from existing queue rows.",
    payload.job_prioritization_rows || [],
    "advisory_priority",
    [
      { key: "company", label: "Company" },
      { key: "title", label: "Title" },
      { key: "existing_action", label: "Existing action" },
      { key: "advisory_priority", label: "Advisory priority", type: "pill" },
      { key: "advisory_reason_codes", label: "Reasons", type: "reasons" },
      { key: "packet_generation_allowed", label: "Packet", type: "pill" },
    ],
  );

  renderAgenticReviewAdvisoryPanel(
    "agenticReviewTailoringPanel",
    "Tailoring Decision",
    "Advisory tailoring decisions, separate from actual tailoring generation.",
    payload.tailoring_decision_rows || [],
    "tailoring_decision",
    [
      { key: "company", label: "Company" },
      { key: "title", label: "Title" },
      { key: "existing_action", label: "Existing action" },
      { key: "advisory_priority", label: "Priority", type: "pill" },
      { key: "tailoring_decision", label: "Tailoring decision", type: "pill" },
      { key: "tailoring_reason_codes", label: "Reasons", type: "reasons" },
    ],
  );

  renderAgenticReviewAdvisoryPanel(
    "agenticReviewOperatorPanel",
    "Operator Review",
    "Human-review lanes consolidated from advisory signals.",
    payload.operator_review_rows || [],
    "operator_review_lane",
    [
      { key: "company", label: "Company" },
      { key: "title", label: "Title" },
      { key: "existing_action", label: "Existing action" },
      { key: "operator_review_lane", label: "Operator lane", type: "pill" },
      { key: "operator_review_reason_codes", label: "Reasons", type: "reasons" },
      { key: "critic_decision", label: "Critic", type: "pill" },
    ],
  );

  renderAgenticReviewDiagnosticsPanel(
    payload.agentic_workflow_verification,
    payload.agentic_workflow_manifest,
    payload.agentic_workflow_execution_plan,
    payload.agentic_workflow_dry_run,
    payload.agent_feedback,
  );

  const traceNode = qs("agenticReviewTracePanel");
  if (traceNode) {
    traceNode.outerHTML = renderAgentTracePanel(tracePayload || {});
  }
}

function activateAgenticReviewPanel(buttonSelector, panelSelector, activeButton, targetId) {
  if (!activeButton || !targetId) return;
  document.querySelectorAll(buttonSelector).forEach((button) => {
    const isActive = button === activeButton;
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-selected", isActive ? "true" : "false");
  });
  document.querySelectorAll(panelSelector).forEach((panel) => {
    panel.classList.toggle("hidden", panel.id !== targetId);
  });
}

function bindAgenticReviewTabs() {
  document.querySelector(".agentic-review-tabs")?.addEventListener("click", (event) => {
    const button = event.target.closest("[data-agentic-tab-target]");
    if (!button) return;
    activateAgenticReviewPanel(
      ".agentic-review-tab",
      "[data-agentic-tab-panel]",
      button,
      button.dataset.agenticTabTarget || "",
    );
  });

  document.querySelector(".agentic-review-segmented")?.addEventListener("click", (event) => {
    const button = event.target.closest("[data-agentic-advisory-target]");
    if (!button) return;
    activateAgenticReviewPanel(
      ".agentic-review-segment",
      "[data-agentic-advisory-panel]",
      button,
      button.dataset.agenticAdvisoryTarget || "",
    );
  });
}

async function initAgenticReviewPage() {
  bindAgenticReviewTabs();
  const runId = getAgenticReviewRunId();
  if (!runId) return;
  try {
    const [payload, tracePayload, feedbackPayload] = await Promise.all([
      fetchJson(`/profile/pipeline-runs/${encodeURIComponent(runId)}/agentic-review-data`),
      fetchJson(`/profile/pipeline-runs/${encodeURIComponent(runId)}/agent-trace`).catch(() => ({})),
      fetchJson(`/api/agent-feedback/summary?pipeline_run_id=${encodeURIComponent(runId)}&limit=50`).catch(() => ({})),
    ]);
    if (!payload.agent_feedback) payload.agent_feedback = feedbackPayload || {};
    renderAgenticReviewData(payload, tracePayload);
  } catch (err) {
    const panel = qs("agenticReviewStatusCard");
    if (panel) {
      panel.innerHTML = `<div class="agent-trace-error">${escapeHtml(err.message || "Failed to load agentic review.")}</div>`;
    }
  }
}

window.addEventListener("DOMContentLoaded", initAgenticReviewPage);
