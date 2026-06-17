// Legacy UI contract marker: markdown rendering must keep using escapeHtml(markdown)
const AGENTIC_REVIEW_LEGACY_MARKDOWN_LABELS = Object.freeze([
  "Manifest markdown",
  "Execution plan markdown",
  "Dry-run report markdown",
  "Preflight report markdown",
  "Chain report markdown",
  "Generator report markdown",
  "Simulation report markdown",
  "Proposal plan report markdown",
]);

function getAgenticReviewRunId() {
  return document.querySelector("[data-agentic-review-run-id]")?.dataset?.agenticReviewRunId || "";
}

const AGENTIC_REVIEW_FEEDBACK_EVENTS = {
  helpful: "agentic_review_helpful",
  not_helpful: "agentic_review_not_helpful",
};

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

function renderAgenticReviewStatus(payload = {}, tracePayload = {}) {
  const run = payload.run || {};
  const summary = getWorkflowSummary(payload);
  const verification = getWorkflowVerification(payload);
  const traceSummary = tracePayload && typeof tracePayload === "object" ? tracePayload : {};
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
    <div class="agentic-review-health-strip agentic-review-health-strip--primary">
      ${renderWorkflowSummaryMetric("Run status", pipelineRunStatusLabel(run?.status))}
      ${renderWorkflowSummaryMetric("Verification", formatWorkflowVerificationStatus(verificationStatus))}
      ${renderWorkflowSummaryMetric("Final jobs", run?.final_job_count ?? counts.final_jobs ?? "-")}
      ${renderWorkflowSummaryMetric("Ready to apply", summary.ready_to_apply_count ?? 0)}
      ${renderWorkflowSummaryMetric("Tailor then apply", summary.tailor_then_apply_count ?? 0)}
      ${renderWorkflowSummaryMetric("Hold / skip", summary.hold_or_skip_count ?? 0)}
      ${renderWorkflowSummaryMetric("Agent trace", traceSummary.found === true ? "available" : traceSummary.found === false ? "not persisted" : "-")}
    </div>
      <details class="agentic-review-secondary-diagnostics" data-collapsed-by-default="true">
      <summary>Secondary diagnostics</summary>
      <div class="agentic-review-health-strip agentic-review-health-strip--secondary">
        ${renderWorkflowSummaryMetric("Source watch", summary.source_watch_count ?? 0)}
        ${renderWorkflowSummaryMetric("Missing artifacts", missingArtifacts.length)}
        ${renderWorkflowSummaryMetric("Trace steps", traceSummary.step_count ?? "-")}
      ${renderWorkflowSummaryMetric("Scraped / filtered", `${counts.scraped_jobs ?? counts.scraped ?? "-"} / ${counts.filtered_jobs ?? counts.filtered ?? "-"}`)}
      </div>
    </details>
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

function recommendationExplainerValues(value) {
  if (Array.isArray(value)) {
    return value.map((item) => String(item || "").trim()).filter(Boolean);
  }
  return String(value || "")
    .split(/[;,]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function buildRecommendationExplainer(row = {}) {
  const sourceFieldsUsed = [];
  const readField = (key) => {
    const value = String(row?.[key] || "").trim();
    if (value && !sourceFieldsUsed.includes(key)) sourceFieldsUsed.push(key);
    return value;
  };
  const recommendationLabel = readField("advisory_priority")
    || readField("tailoring_decision")
    || readField("operator_review_lane")
    || readField("existing_action")
    || "recommendation";
  const primaryReasons = [];
  ["advisory_reason_codes", "tailoring_reason_codes", "operator_review_reason_codes", "critic_reason_codes"].forEach((key) => {
    const values = recommendationExplainerValues(row?.[key]);
    if (values.length && !sourceFieldsUsed.includes(key)) sourceFieldsUsed.push(key);
    values.forEach((value) => {
      if (!primaryReasons.includes(value)) primaryReasons.push(value);
    });
  });
  const supportingSignals = [
    readField("company"),
    readField("title"),
    readField("existing_action"),
    readField("packet_generation_allowed"),
    readField("critic_decision"),
  ].filter(Boolean);
  const scoreBreakdown = {};
  ["deterministic_winner_score", "winner_score", "runner_up_score", "score_gap", "selected_score", "ai_fit_score"].forEach((key) => {
    const value = readField(key);
    if (value) scoreBreakdown[key] = value;
  });
  const riskSignals = primaryReasons.filter((reason) => /block|hold|skip|risk|missing|manual/i.test(reason));
  const missingEvidence = [];
  if (!primaryReasons.length) missingEvidence.push("reason_codes_missing");
  if (!Object.keys(scoreBreakdown).length) missingEvidence.push("score_fields_missing");
  if (!readField("company")) missingEvidence.push("company_missing");
  if (!readField("title")) missingEvidence.push("title_missing");
  return {
    explainer_status: primaryReasons.length || supportingSignals.length || Object.keys(scoreBreakdown).length ? "explained" : "limited_evidence",
    recommendation_label: recommendationLabel,
    primary_reasons: primaryReasons,
    supporting_signals: supportingSignals,
    risk_signals: riskSignals,
    missing_evidence: missingEvidence,
    score_breakdown: scoreBreakdown,
    source_fields_used: sourceFieldsUsed,
    safety_metadata: {
      did_write_database: false,
      did_call_llm: false,
      did_change_ranking: false,
      did_change_scoring: false,
      did_mutate_approval: false,
      did_mutate_queue: false,
      did_execute_application: false,
      did_submit_application: false,
    },
  };
}

function renderRecommendationExplainer(row = {}) {
  const explanation = buildRecommendationExplainer(row);
  return `
    <details class="agentic-review-recommendation-explainer" data-collapsed-by-default="true">
      <summary>Why surfaced</summary>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Explainer", explanation.explainer_status)}
        ${renderWorkflowSummaryMetric("Recommendation", explanation.recommendation_label)}
        ${renderWorkflowSummaryMetric("Read-only", "true")}
      </div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Primary reasons", explanation.primary_reasons, { helper: "Existing recommendation reason codes." })}
        ${renderAgentTraceReadOnlyDetails("Supporting signals", explanation.supporting_signals, { helper: "Existing row fields that support the recommendation." })}
        ${renderAgentTraceReadOnlyDetails("Risk signals", explanation.risk_signals, { helper: "Existing row fields that indicate risk or review needs." })}
        ${renderAgentTraceReadOnlyDetails("Missing evidence", explanation.missing_evidence, { helper: "Expected explanatory fields absent from this row." })}
        ${renderAgentTraceReadOnlyDetails("Score breakdown", explanation.score_breakdown, { helper: "Existing score fields only; no rescoring is performed." })}
        ${renderAgentTraceReadOnlyDetails("Source fields used", explanation.source_fields_used, { helper: "Read-only row fields used by the explainer." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", explanation.safety_metadata, { helper: "Recommendation explainer safety metadata." })}
      </div>
    </details>
  `;
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
            <tr class="agentic-review-explainer-row">
              <td colspan="${escapeHtml(String(columns.length || 1))}">${renderRecommendationExplainer(row)}</td>
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
  readOnlyAdapterPreflight = {},
  manualReadOnlyAdapterChain = {},
  explicitReadOnlyChainArtifactGeneration = {},
  explicitDryRunExecutionSimulation = {},
  proposalOnlyMutationPlan = {},
  operatorApprovalMock = {},
  agentFeedback = {},
  ragEvaluation = {},
) {
  const panel = qs("agenticReviewDiagnosticsPanel");
  if (!panel) return;
  const preflightSection = renderReadOnlyAdapterPreflightSection(readOnlyAdapterPreflight);
  const adapterChainSection = renderManualReadOnlyAdapterChainSection(manualReadOnlyAdapterChain);
  const chainGeneratorSection = renderExplicitReadOnlyChainGeneratorSection(explicitReadOnlyChainArtifactGeneration);
  const dryRunSimulationSection = renderDryRunExecutionSimulationSection(explicitDryRunExecutionSimulation);
  const proposalOnlyMutationPlanSection = renderProposalOnlyMutationPlanSection(proposalOnlyMutationPlan);
  const operatorApprovalMockSection = renderOperatorApprovalMockSection(operatorApprovalMock);
  const feedbackSection = renderAgenticReviewFeedbackSection(agentFeedback);
  const ragEvaluationSection = renderRagEvaluationSection(ragEvaluation);
  const optionalDiagnosticSections = [
    preflightSection,
    adapterChainSection,
    chainGeneratorSection,
    dryRunSimulationSection,
    proposalOnlyMutationPlanSection,
    operatorApprovalMockSection,
    ragEvaluationSection,
    feedbackSection,
  ].join("");
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
  const preflightAvailable = Boolean(readOnlyAdapterPreflight?.available);
  const preflightPlan = readOnlyAdapterPreflight?.plan_json && typeof readOnlyAdapterPreflight.plan_json === "object"
    ? readOnlyAdapterPreflight.plan_json
    : {};
  const chainAvailable = Boolean(manualReadOnlyAdapterChain?.present || manualReadOnlyAdapterChain?.available);
  const chainGeneratorAvailable = Boolean(
    explicitReadOnlyChainArtifactGeneration?.present
    || explicitReadOnlyChainArtifactGeneration?.available
  );
  const dryRunSimulationAvailable = Boolean(
    explicitDryRunExecutionSimulation?.present
    || explicitDryRunExecutionSimulation?.available
  );
  const operatorApprovalMockAvailable = Boolean(operatorApprovalMock?.present);
  const proposalOnlyMutationPlanAvailable = Boolean(
    proposalOnlyMutationPlan?.present
    || proposalOnlyMutationPlan?.available
  );
  if (
    !available && !Object.keys(verification).length
    && !manifestAvailable && !Object.keys(manifest).length
    && !planAvailable && !Object.keys(executionPlan).length
    && !dryRunAvailable && !Object.keys(dryRunResult).length
    && !preflightAvailable && !Object.keys(preflightPlan).length
    && !chainAvailable
    && !chainGeneratorAvailable
    && !dryRunSimulationAvailable
    && !proposalOnlyMutationPlanAvailable
    && !operatorApprovalMockAvailable
  ) {
    panel.innerHTML = `
      <div class="agentic-workflow-header">
        <div>
          <h2>Artifacts / Diagnostics</h2>
          <p>Verifier, manifest, execution plan, and dry-run runner artifacts will appear here after a run produces them.</p>
        </div>
      </div>
      <div class="pipeline-runs-empty-cell">No agentic workflow manifest, execution plan, dry run, or verification recorded for this run.</div>
      <details class="agentic-review-optional-diagnostics" data-collapsed-by-default="true">
        <summary>
          <span>Optional diagnostics not recorded</span>
          <span class="agentic-review-optional-diagnostics-summary">These optional diagnostics do not affect planning results.</span>
        </summary>
        ${optionalDiagnosticSections}
      </details>
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
    <details class="agentic-review-optional-diagnostics" data-collapsed-by-default="true">
      <summary>
        <span>Optional diagnostics not recorded</span>
        <span class="agentic-review-optional-diagnostics-summary">These optional diagnostics do not affect planning results.</span>
      </summary>
      ${optionalDiagnosticSections}
    </details>
  `;
}

function getRagEvaluationSummary(ragEvaluation = {}) {
  const summary = ragEvaluation?.summary_json && typeof ragEvaluation.summary_json === "object"
    ? ragEvaluation.summary_json
    : {};
  return {
    query_count: Number(summary.query_count || 0),
    retrieved_chunk_count: Number(summary.retrieved_chunk_count || 0),
    average_retrieval_score: summary.average_retrieval_score ?? null,
    top_k_hit_rate: summary.top_k_hit_rate ?? null,
    missing_evidence_warning_count: Number(summary.missing_evidence_warning_count || 0),
    validation_status: String(summary.validation_status || "warning"),
    reason_codes: Array.isArray(summary.reason_codes) ? summary.reason_codes : [],
  };
}

function formatRagMetric(value) {
  if (value === null || value === undefined || value === "") return "-";
  if (typeof value === "number") return Number.isInteger(value) ? value : value.toFixed(3).replace(/0+$/, "").replace(/\.$/, "");
  return value;
}

function renderRagEvaluationSection(ragEvaluation = {}) {
  const summary = getRagEvaluationSummary(ragEvaluation);
  const hasRows = summary.retrieved_chunk_count > 0 || summary.query_count > 0;
  return `
    <section class="rag-evaluation-card">
      <div class="agentic-workflow-header">
        <div>
          <h2>RAG Evaluation</h2>
          <p>Read-only retrieval quality diagnostics. These metrics do not change retrieval, scoring, queue order, or tailoring decisions.</p>
        </div>
        ${renderReviewPill(summary.validation_status)}
      </div>
      <div class="rag-evaluation-metrics">
        ${renderWorkflowSummaryMetric("Queries", summary.query_count)}
        ${renderWorkflowSummaryMetric("Retrieved chunks", summary.retrieved_chunk_count)}
        ${renderWorkflowSummaryMetric("Avg score", formatRagMetric(summary.average_retrieval_score))}
        ${renderWorkflowSummaryMetric("Top-k hit rate", formatRagMetric(summary.top_k_hit_rate))}
        ${renderWorkflowSummaryMetric("Missing evidence", summary.missing_evidence_warning_count)}
        ${renderWorkflowSummaryMetric("Validation", formatWorkflowVerificationStatus(summary.validation_status))}
      </div>
      ${hasRows ? `
        <div class="agentic-review-section-counts">
          <strong>Reason codes</strong>
          <span>${renderReasonChips(summary.reason_codes)}</span>
        </div>
      ` : `<div class="pipeline-runs-empty-cell">No RAG evaluation data recorded for this run yet.</div>`}
    </section>
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

function renderAgenticWorkflowMarkdownSummary(label, markdown) {
  const safeMarkdown = String(markdown || "");
  if (!safeMarkdown) return "";
  return `
    <details class="agentic-workflow-markdown agentic-workflow-markdown-summary" data-collapsed-by-default="true">
      <summary>${escapeHtml(label)} Markdown summary</summary>
      <pre>${escapeHtml(safeMarkdown)}</pre>
    </details>
  `;
}

function renderAgenticReviewFeedbackSection(agentFeedback = {}) {
  const summary = getAgentFeedbackSummary(agentFeedback);
  const events = Array.isArray(agentFeedback?.events) ? agentFeedback.events : [];
  const runId = escapeHtml(agentFeedback?.pipeline_run_id || getAgenticReviewRunId());
  return `
    <section class="agentic-feedback-card">
      <div class="agentic-workflow-header">
        <div>
          <h2>Human Feedback</h2>
          <p>Read-only feedback events captured for this pipeline run. These diagnostics do not change scoring, queue order, or tailoring decisions.</p>
        </div>
        <span class="agentic-workflow-badge">Read-only</span>
      </div>
      <div class="agentic-feedback-actions" data-agentic-feedback-run-id="${runId}">
        <button type="button" class="agentic-feedback-action is-helpful" data-agentic-feedback-event="agentic_review_helpful">
          Mark review useful
        </button>
        <button type="button" class="agentic-feedback-action is-not-helpful" data-agentic-feedback-event="agentic_review_not_helpful">
          Mark review not useful
        </button>
        <span class="agentic-feedback-status" data-agentic-feedback-status aria-live="polite"></span>
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

function renderAgentTraceReadOnlyDetails(label, value, options = {}) {
  const hasValue = value && typeof value === "object"
    ? Object.keys(value).length > 0
    : Boolean(value);
  if (!hasValue) return "";
  const payload = typeof value === "object" ? JSON.stringify(value, null, 2) : String(value || "");
  const summary = options.summary || label;
  const helper = options.helper ? `<span class="agentic-review-muted">${escapeHtml(options.helper)}</span>` : "";
  return `
    <details class="agent-trace-json-detail" data-collapsed-by-default="true" aria-label="${escapeHtml(label)}">
      <summary>${escapeHtml(summary)}</summary>
      ${helper}
      <pre>${escapeHtml(payload)}</pre>
    </details>
  `;
}

function agentTraceReadOnlyStepStatus(step = {}) {
  return String(step.step_status || step.status || "unknown").trim() || "unknown";
}

function renderAgentTraceReadOnlyStep(step = {}) {
  const status = agentTraceReadOnlyStepStatus(step);
  const tone = statusToneForValue(status);
  const validation = step.validation_json /* read-only agent trace safety metadata */ || step.output_summary?.validation_json || {};
  const safety = step.safety_metadata || step.metadata?.safety_metadata || {};
  const stepLabel = `${step.agent_name || "Agent step"} ${step.step_index ?? ""}`.trim();
  return `
    <article class="agent-trace-step" aria-label="${escapeHtml(`Agent trace ordered agent steps item: ${stepLabel}`)}">
      <div class="agent-trace-step-header">
        <div>
          <div class="agent-trace-step-name">${escapeHtml(step.agent_name || "Agent step")}</div>
          <div class="agent-trace-step-meta">
            ${escapeHtml(step.step_name || step.agent_step_id || "-")}
          </div>
        </div>
        <span class="pipeline-run-status agent-trace-step-status is-${escapeHtml(tone)}">${escapeHtml(formatReviewLabel(status))}</span>
      </div>
      <div class="agent-trace-step-summary">
        <span>Index: ${escapeHtml(step.step_index ?? "-")}</span>
        <span>Observed: ${escapeHtml(step.observed_at_utc || step.started_at || "-")}</span>
        ${step.completed_at ? `<span>Completed: ${escapeHtml(step.completed_at)}</span>` : ""}
      </div>
      <div class="agentic-review-muted">Collapsed step details keep long trace readability while preserving read-only ordered agent steps.</div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Input summary", step.input_summary || step.input_json, { helper: "Read-only input summary." })}
        ${renderAgentTraceReadOnlyDetails("Output summary", step.output_summary || step.output_json, { helper: "Read-only output summary." })}
        ${renderAgentTraceReadOnlyDetails("validation_json", validation, { helper: "Readable validation_json display." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable safety metadata display." })}
      </div>
    </article>
  `;
}

function renderAgentTraceReadOnlyState(message, tone = "info", label = "Agent trace state") {
  return `
    <div class="pipeline-runs-empty-cell agent-trace-state is-${escapeHtml(tone)}" role="status" aria-label="${escapeHtml(label)}">
      ${escapeHtml(message)}
    </div>
  `;
}

function hasAgentTraceSummaryObject(value) {
  return value && typeof value === "object" && !Array.isArray(value) && Object.keys(value).length > 0;
}

function renderAgentTraceSummaryDetails(label, value) {
  if (!hasAgentTraceSummaryObject(value)) return "";
  return renderAgentTraceReadOnlyDetails(label, value, {
    summary: label,
    helper: "Read-only trace summary detail.",
  });
}

function renderAgentTraceSummarySection(traceSummary = {}) {
  if (!hasAgentTraceSummaryObject(traceSummary)) return "";
  const safety = hasAgentTraceSummaryObject(traceSummary.safety_metadata)
    ? traceSummary.safety_metadata
    : {};
  return `
    <article class="agent-trace-summary" aria-label="Read-only agent trace summary">
      <div class="agentic-workflow-header">
        <div>
          <h4>Trace Summary</h4>
          <p>Opt-in read-only summary from existing trace rows. It does not write storage, call LLMs, execute applications, or submit applications.</p>
        </div>
        <span class="agentic-workflow-badge">Read-only</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Runs", traceSummary.run_count ?? 0)}
        ${renderWorkflowSummaryMetric("Steps", traceSummary.step_count ?? 0)}
        ${renderWorkflowSummaryMetric("Completed steps", traceSummary.completed_step_count ?? 0)}
        ${renderWorkflowSummaryMetric("Error steps", traceSummary.error_step_count ?? 0)}
        ${renderWorkflowSummaryMetric("Warning steps", traceSummary.warning_step_count ?? 0)}
        ${renderWorkflowSummaryMetric("Writes", safety.did_write_database ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("LLM calls", safety.did_call_llm ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Execution", safety.did_execute_application ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Submission", safety.did_submit_application ? "yes" : "no")}
      </div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceSummaryDetails("Agent counts", traceSummary.agent_counts)}
        ${renderAgentTraceSummaryDetails("Step status counts", traceSummary.step_status_counts)}
        ${renderAgentTraceSummaryDetails("Run status counts", traceSummary.run_status_counts)}
        ${renderAgentTraceSummaryDetails("Latency summary", traceSummary.latency_summary)}
        ${renderAgentTraceSummaryDetails("Model usage summary", traceSummary.model_usage_summary)}
        ${renderAgentTraceSummaryDetails("Token usage summary", traceSummary.token_usage_summary)}
        ${renderAgentTraceSummaryDetails("Cost summary", traceSummary.cost_summary)}
        ${renderAgentTraceSummaryDetails("Safety metadata", safety)}
      </div>
    </article>
  `;
}

function renderAgentStageTraceBundleSection(stageTraceBundle = {}) {
  if (!hasAgentTraceSummaryObject(stageTraceBundle)) return "";
  const validation = hasAgentTraceSummaryObject(stageTraceBundle.stage_order_validation)
    ? stageTraceBundle.stage_order_validation
    : {};
  const safety = hasAgentTraceSummaryObject(stageTraceBundle.safety_metadata)
    ? stageTraceBundle.safety_metadata
    : {};
  const stageCount = Number(stageTraceBundle.step_count ?? 0);
  const orderValid = validation.is_valid === true;
  return `
    <article class="agent-trace-summary" aria-label="Read-only stage trace bundle">
      <div class="agentic-workflow-header">
        <div>
          <h4>Stage Trace Bundle</h4>
          <p>Opt-in read-only stage order bundle from existing trace rows. It does not write storage, call LLMs, change ranking or scoring, execute applications, or submit applications.</p>
        </div>
        <span class="agentic-workflow-badge">Read-only</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Stage count", stageCount)}
        ${renderWorkflowSummaryMetric("Stage order valid", orderValid ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Writes", safety.did_write_database ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("LLM calls", safety.did_call_llm ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Ranking changes", safety.did_change_ranking ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Scoring changes", safety.did_change_scoring ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Execution", safety.did_execute_application ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Submission", safety.did_submit_application ? "yes" : "no")}
      </div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Stage names", stageTraceBundle.stage_names, { helper: "Read-only stage names from existing trace rows." })}
        ${renderAgentTraceReadOnlyDetails("Agent names", stageTraceBundle.agent_names, { helper: "Read-only agent names from existing trace rows." })}
        ${renderAgentTraceReadOnlyDetails("Missing expected stages", stageTraceBundle.missing_expected_stages, { helper: "Expected stages absent from the returned trace rows." })}
        ${renderAgentTraceReadOnlyDetails("Unexpected stages", stageTraceBundle.unexpected_stages, { helper: "Returned stages outside the expected read-only order." })}
        ${renderAgentTraceReadOnlyDetails("Duplicate stages", stageTraceBundle.duplicate_stages, { helper: "Duplicate stage names in the returned trace rows." })}
        ${renderAgentTraceReadOnlyDetails("Stage order validation", validation, { helper: "Deterministic stage order validation." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable stage bundle safety metadata." })}
      </div>
    </article>
  `;
}

function renderAgentStageTraceHealthSection(stageTraceHealth = {}) {
  if (!hasAgentTraceSummaryObject(stageTraceHealth)) return "";
  const safety = hasAgentTraceSummaryObject(stageTraceHealth.safety_metadata)
    ? stageTraceHealth.safety_metadata
    : {};
  return `
    <article class="agent-trace-summary" aria-label="Read-only stage trace health">
      <div class="agentic-workflow-header">
        <div>
          <h4>Stage Trace Health</h4>
          <p>Opt-in deterministic health check for the stage trace bundle. It does not write storage, call LLMs, change ranking or scoring, execute applications, or submit applications.</p>
        </div>
        <span class="agentic-workflow-badge">Read-only</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Health", stageTraceHealth.health_status || "unknown")}
        ${renderWorkflowSummaryMetric("Stage order valid", stageTraceHealth.stage_order_valid === true ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Required fields", stageTraceHealth.all_required_fields_present === true ? "present" : "missing")}
        ${renderWorkflowSummaryMetric("Writes", safety.did_write_database ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("LLM calls", safety.did_call_llm ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Execution", safety.did_execute_application ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Submission", safety.did_submit_application ? "yes" : "no")}
      </div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Findings", stageTraceHealth.findings, { helper: "Deterministic stage trace health findings." })}
        ${renderAgentTraceReadOnlyDetails("Warnings", stageTraceHealth.warnings, { helper: "Deterministic stage trace health warnings." })}
        ${renderAgentTraceReadOnlyDetails("Missing expected stages", stageTraceHealth.missing_expected_stages, { helper: "Expected stages absent from the stage trace bundle." })}
        ${renderAgentTraceReadOnlyDetails("Unexpected stages", stageTraceHealth.unexpected_stages, { helper: "Stages outside the expected read-only order." })}
        ${renderAgentTraceReadOnlyDetails("Duplicate stages", stageTraceHealth.duplicate_stages, { helper: "Duplicate stage names detected by the health check." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable stage trace health safety metadata." })}
      </div>
    </article>
  `;
}

function renderAgentStageTraceReadinessSection(stageTraceReadiness = {}) {
  if (!hasAgentTraceSummaryObject(stageTraceReadiness)) return "";
  const safety = hasAgentTraceSummaryObject(stageTraceReadiness.safety_metadata)
    ? stageTraceReadiness.safety_metadata
    : {};
  return `
    <article class="agent-trace-summary" aria-label="Read-only stage trace readiness">
      <div class="agentic-workflow-header">
        <div>
          <h4>Stage Trace Readiness</h4>
          <p>Opt-in deterministic readiness decision from stage trace health. It does not write storage, call LLMs, change ranking or scoring, execute applications, or submit applications.</p>
        </div>
        <span class="agentic-workflow-badge">Read-only</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Readiness", stageTraceReadiness.readiness_status || "unknown")}
        ${renderWorkflowSummaryMetric("Stage order valid", stageTraceReadiness.stage_order_valid === true ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Required fields", stageTraceReadiness.all_required_fields_present === true ? "present" : "missing")}
        ${renderWorkflowSummaryMetric("Writes", safety.did_write_database ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("LLM calls", safety.did_call_llm ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Execution", safety.did_execute_application ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Submission", safety.did_submit_application ? "yes" : "no")}
      </div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Reason codes", stageTraceReadiness.decision_reason_codes, { helper: "Deterministic stage trace readiness reason codes." })}
        ${renderAgentTraceReadOnlyDetails("Blocking findings", stageTraceReadiness.blocking_findings, { helper: "Read-only readiness blockers from stage trace health." })}
        ${renderAgentTraceReadOnlyDetails("Warning findings", stageTraceReadiness.warning_findings, { helper: "Read-only readiness warnings from stage trace health." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable stage trace readiness safety metadata." })}
      </div>
    </article>
  `;
}

function renderAgentTraceEvidencePackSection(traceEvidencePack = {}) {
  if (!hasAgentTraceSummaryObject(traceEvidencePack)) return "";
  const safety = hasAgentTraceSummaryObject(traceEvidencePack.safety_metadata)
    ? traceEvidencePack.safety_metadata
    : {};
  return `
    <article class="agent-trace-summary" aria-label="Read-only agent trace evidence pack">
      <div class="agentic-workflow-header">
        <div>
          <h4>Trace Evidence Pack</h4>
          <p>Opt-in compact read-only evidence pack from existing trace sections. It does not write storage, call LLMs, change ranking or scoring, execute applications, or submit applications.</p>
        </div>
        <span class="agentic-workflow-badge">Read-only</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Evidence", traceEvidencePack.ok === true ? "ready" : "review")}
        ${renderWorkflowSummaryMetric("Readiness", traceEvidencePack.readiness_status || "unknown")}
        ${renderWorkflowSummaryMetric("Health", traceEvidencePack.health_status || "unknown")}
        ${renderWorkflowSummaryMetric("Stage count", Number(traceEvidencePack.stage_count ?? 0))}
        ${renderWorkflowSummaryMetric("Writes", safety.did_write_database ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("LLM calls", safety.did_call_llm ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Execution", safety.did_execute_application ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Submission", safety.did_submit_application ? "yes" : "no")}
      </div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Available sections", traceEvidencePack.available_sections, { helper: "Read-only evidence pack sections available in this response." })}
        ${renderAgentTraceReadOnlyDetails("Missing sections", traceEvidencePack.missing_sections, { helper: "Read-only evidence pack sections absent from this response." })}
        ${renderAgentTraceReadOnlyDetails("Decision reason codes", traceEvidencePack.decision_reason_codes, { helper: "Compact readiness decision reason codes." })}
        ${renderAgentTraceReadOnlyDetails("Blocking findings", traceEvidencePack.blocking_findings, { helper: "Compact evidence pack blocking findings." })}
        ${renderAgentTraceReadOnlyDetails("Warning findings", traceEvidencePack.warning_findings, { helper: "Compact evidence pack warning findings." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable trace evidence pack safety metadata." })}
      </div>
    </article>
  `;
}

function renderShadowSidecarTraceReadbackSection(tracePayload = {}) {
  const result = hasAgentTraceSummaryObject(tracePayload?.shadow_sidecar_trace_readback_result)
    ? tracePayload.shadow_sidecar_trace_readback_result
    : {};
  const safety = hasAgentTraceSummaryObject(result.safety_metadata)
    ? result.safety_metadata
    : {};
  const sourceContext = hasAgentTraceSummaryObject(result.source_trace_context)
    ? result.source_trace_context
    : {};
  const traceReadback = hasAgentTraceSummaryObject(result.trace_readback)
    ? result.trace_readback
    : {};
  const contextId = String(tracePayload?.context_id || tracePayload?.agent_run?.context_id || sourceContext.context_id || "").trim();
  const agentRunId = String(tracePayload?.agent_run_id || tracePayload?.agent_run?.agent_run_id || sourceContext.agent_run_id || "").trim();
  const pipelineRunId = String(tracePayload?.pipeline_run_id || getAgenticReviewRunId() || sourceContext.pipeline_run_id || "").trim();
  const status = result.trace_readback_status || "not run";
  return `
    <article class="agent-trace-summary" aria-label="Shadow sidecar trace readback">
      <div class="agentic-workflow-header">
        <div>
          <h4>Shadow Sidecar Trace Readback</h4>
          <p>Manual read-only shadow trace readback. It uses the default-off readback API only when clicked and does not mutate scoring, ranking, queues, approvals, resumes, execution requests, launch requests, applications, or submissions.</p>
        </div>
        <span class="agentic-workflow-badge">Default-off</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Readback", status)}
        ${renderWorkflowSummaryMetric("Read-only", safety.read_only === true ? "yes" : "unknown")}
        ${renderWorkflowSummaryMetric("Shadow-only", safety.shadow_only === true ? "yes" : "unknown")}
        ${renderWorkflowSummaryMetric("Scoring mutation", safety.did_mutate_scoring ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Ranking mutation", safety.did_change_ranking ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Queue mutation", safety.did_mutate_queue ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Approval mutation", safety.did_mutate_approval ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Resume mutation", safety.did_mutate_resume ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Execution request", safety.did_create_execution_request ? "created" : "no")}
        ${renderWorkflowSummaryMetric("Launch request", safety.did_create_execution_launch_request ? "created" : "no")}
        ${renderWorkflowSummaryMetric("Execution", safety.did_execute_application ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Submission", safety.did_submit_application ? "yes" : "no")}
      </div>
      ${status === "trace_readback_not_enabled" ? renderAgentTraceReadOnlyState("Shadow sidecar trace readback is not enabled. Default-off display is safe.", "info", "Shadow sidecar trace readback not enabled") : ""}
      ${status === "trace_readback_blocked_by_kill_switch" ? renderAgentTraceReadOnlyState("Shadow sidecar trace readback is blocked by the kill switch. No readback mutation is attempted.", "warning", "Shadow sidecar trace readback blocked by kill switch") : ""}
      ${status === "trace_readback_skipped_no_safe_source" ? renderAgentTraceReadOnlyState("No safe shadow sidecar trace source is available yet. The read-only UI remains stable.", "info", "Shadow sidecar trace readback no safe source") : ""}
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Source trace context", sourceContext, { helper: "Read-only source trace context returned by the readback API." })}
        ${renderAgentTraceReadOnlyDetails("Trace readback", traceReadback, { helper: "Read-only shadow sidecar trace readback envelope." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "No-mutation safety metadata for shadow sidecar trace readback." })}
      </div>
      <div class="agentic-feedback-actions">
        <button type="button" class="agentic-feedback-action" data-shadow-sidecar-trace-readback data-pipeline-run-id="${escapeHtml(pipelineRunId)}" data-context-id="${escapeHtml(contextId)}" data-agent-run-id="${escapeHtml(agentRunId)}">
          Read Shadow Trace
        </button>
        <span class="agentic-review-muted" data-shadow-sidecar-trace-readback-status>
          Manual read-only. Safe states include not-enabled, blocked by kill switch, and no safe source.
        </span>
      </div>
    </article>
  `;
}

function shadowScoreComparisonRequestPayload(tracePayload = {}) {
  const deterministicContext = hasAgentTraceSummaryObject(tracePayload?.shadow_score_comparison_deterministic_context)
    ? tracePayload.shadow_score_comparison_deterministic_context
    : hasAgentTraceSummaryObject(tracePayload?.source_deterministic_context)
      ? tracePayload.source_deterministic_context
      : hasAgentTraceSummaryObject(tracePayload?.agent_run?.summary_json)
        ? tracePayload.agent_run.summary_json
        : {};
  const snapshotPayload = hasAgentTraceSummaryObject(tracePayload?.shadow_sidecar_evidence_snapshot_result)
    ? tracePayload.shadow_sidecar_evidence_snapshot_result
    : hasAgentTraceSummaryObject(tracePayload?.shadow_score_comparison_snapshot_payload)
      ? tracePayload.shadow_score_comparison_snapshot_payload
      : {};
  return {
    deterministic_score_context: deterministicContext,
    shadow_evidence_snapshot_payload: snapshotPayload,
  };
}

function renderShadowSidecarScoreComparisonSection(tracePayload = {}) {
  const result = hasAgentTraceSummaryObject(tracePayload?.shadow_sidecar_score_comparison_result)
    ? tracePayload.shadow_sidecar_score_comparison_result
    : {};
  const safety = hasAgentTraceSummaryObject(result.safety_metadata)
    ? result.safety_metadata
    : {};
  const operatorSummary = hasAgentTraceSummaryObject(result.operator_review_summary)
    ? result.operator_review_summary
    : {};
  const findings = Array.isArray(result.comparison_findings)
    ? result.comparison_findings
    : [];
  const status = result.comparison_status || "not run";
  return `
    <article class="agent-trace-summary" aria-label="Shadow score comparison">
      <div class="agentic-workflow-header">
        <div>
          <h4>Shadow Score Comparison</h4>
          <p>Manual read-only comparison between deterministic final scoring context and shadow sidecar evidence. It is operator-review only and never changes scoring, ranking, queues, approvals, resumes, execution requests, launch requests, applications, or submissions.</p>
        </div>
        <span class="agentic-workflow-badge">Default-off</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Comparison", status)}
        ${renderWorkflowSummaryMetric("Deterministic score", result.deterministic_score ?? "-")}
        ${renderWorkflowSummaryMetric("Decision", result.deterministic_decision || "-")}
        ${renderWorkflowSummaryMetric("Shadow snapshot", result.shadow_snapshot_status || "-")}
        ${renderWorkflowSummaryMetric("Agreement", result.agreement_level || "-")}
        ${renderWorkflowSummaryMetric("Read-only", safety.read_only === true ? "yes" : "unknown")}
        ${renderWorkflowSummaryMetric("Shadow-only", safety.shadow_only === true ? "yes" : "unknown")}
        ${renderWorkflowSummaryMetric("Operator review", safety.operator_review_only === true ? "yes" : "unknown")}
        ${renderWorkflowSummaryMetric("Scoring mutation", safety.did_mutate_scoring ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Ranking mutation", safety.did_change_ranking ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Queue mutation", safety.did_mutate_queue ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Approval mutation", safety.did_mutate_approval ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Resume mutation", safety.did_mutate_resume ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Execution request", safety.did_create_execution_request ? "created" : "no")}
        ${renderWorkflowSummaryMetric("Launch request", safety.did_create_execution_launch_request ? "created" : "no")}
        ${renderWorkflowSummaryMetric("Execution", safety.did_execute_application ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Submission", safety.did_submit_application ? "yes" : "no")}
      </div>
      ${status === "comparison_not_enabled" ? renderAgentTraceReadOnlyState("Shadow score comparison is not enabled. Default-off display is safe.", "info", "Shadow score comparison not enabled") : ""}
      ${status === "comparison_blocked_by_kill_switch" ? renderAgentTraceReadOnlyState("Shadow score comparison is blocked by the kill switch. No comparison mutation is attempted.", "warning", "Shadow score comparison blocked by kill switch") : ""}
      ${status === "comparison_blocked_missing_deterministic_context" ? renderAgentTraceReadOnlyState("Deterministic score context is missing. The read-only comparison remains unavailable.", "info", "Shadow score comparison missing deterministic context") : ""}
      ${status === "comparison_blocked_missing_shadow_snapshot" ? renderAgentTraceReadOnlyState("Shadow evidence snapshot is missing. The read-only comparison remains unavailable.", "info", "Shadow score comparison missing shadow snapshot") : ""}
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Comparison findings", findings, { helper: "Read-only advisory findings. They do not change deterministic scoring or ranking." })}
        ${renderAgentTraceReadOnlyDetails("Operator review summary", operatorSummary, { helper: "Operator-review only summary from the default-off comparison API." })}
        ${renderAgentTraceReadOnlyDetails("Source deterministic context", result.source_deterministic_context || {}, { helper: "Read-only deterministic score context used for comparison." })}
        ${renderAgentTraceReadOnlyDetails("Source shadow snapshot context", result.source_shadow_snapshot_context || {}, { helper: "Read-only shadow evidence snapshot context used for comparison." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "No-mutation safety metadata for shadow score comparison." })}
      </div>
      <div class="agentic-feedback-actions">
        <button type="button" class="agentic-feedback-action" data-shadow-sidecar-score-comparison>
          Compare Shadow Score
        </button>
        <span class="agentic-review-muted" data-shadow-sidecar-score-comparison-status>
          Manual read-only. Safe states include not-enabled, blocked by kill switch, missing deterministic context, and missing shadow snapshot.
        </span>
      </div>
    </article>
  `;
}

function humanReviewedInfluencePreviewRequestPayload(tracePayload = {}) {
  const deterministicContext = hasAgentTraceSummaryObject(tracePayload?.shadow_sidecar_score_comparison_result?.source_deterministic_context)
    ? tracePayload.shadow_sidecar_score_comparison_result.source_deterministic_context
    : hasAgentTraceSummaryObject(tracePayload?.shadow_score_comparison_deterministic_context)
      ? tracePayload.shadow_score_comparison_deterministic_context
      : hasAgentTraceSummaryObject(tracePayload?.source_deterministic_context)
        ? tracePayload.source_deterministic_context
        : hasAgentTraceSummaryObject(tracePayload?.agent_run?.summary_json)
          ? tracePayload.agent_run.summary_json
          : {};
  const comparisonContext = hasAgentTraceSummaryObject(tracePayload?.shadow_sidecar_score_comparison_result)
    ? tracePayload.shadow_sidecar_score_comparison_result
    : {};
  return {
    deterministic_score_context: deterministicContext,
    shadow_score_comparison_context: comparisonContext,
  };
}

function humanReviewedInfluenceApprovalRequestPayload(tracePayload = {}, options = {}) {
  const previewResult = hasAgentTraceSummaryObject(tracePayload?.human_reviewed_influence_preview_result)
    ? tracePayload.human_reviewed_influence_preview_result
    : {};
  const previewRequest = humanReviewedInfluencePreviewRequestPayload(tracePayload);
  return {
    human_reviewed_influence_preview_payload: previewResult,
    deterministic_score_context: previewRequest.deterministic_score_context,
    shadow_score_comparison_context: previewRequest.shadow_score_comparison_context,
    preview_config: {},
    reviewer_confirmation: Boolean(options.reviewerConfirmation),
    reviewer_note: "",
    context_id: options.contextId || "",
    job_id: options.jobId || "",
  };
}

function agentRecommendationOverlayRequestPayload(tracePayload = {}) {
  const previewRequest = humanReviewedInfluencePreviewRequestPayload(tracePayload);
  const comparisonContext = hasAgentTraceSummaryObject(tracePayload?.shadow_sidecar_score_comparison_result)
    ? tracePayload.shadow_sidecar_score_comparison_result
    : {};
  return {
    deterministic_score_context: previewRequest.deterministic_score_context,
    shadow_score_comparison_context: comparisonContext,
    human_reviewed_influence_preview_payload: hasAgentTraceSummaryObject(tracePayload?.human_reviewed_influence_preview_result)
      ? tracePayload.human_reviewed_influence_preview_result
      : {},
    influence_approval_request_payload: hasAgentTraceSummaryObject(tracePayload?.human_reviewed_influence_approval_request_result)
      ? tracePayload.human_reviewed_influence_approval_request_result
      : {},
    overlay_config: {},
  };
}

function renderHumanReviewedInfluencePreviewSection(tracePayload = {}) {
  const result = hasAgentTraceSummaryObject(tracePayload?.human_reviewed_influence_preview_result)
    ? tracePayload.human_reviewed_influence_preview_result
    : {};
  const safety = hasAgentTraceSummaryObject(result.safety_metadata)
    ? result.safety_metadata
    : {};
  const operatorSummary = hasAgentTraceSummaryObject(result.operator_review_summary)
    ? result.operator_review_summary
    : {};
  const findings = Array.isArray(result.preview_findings)
    ? result.preview_findings
    : [];
  const status = result.preview_status || "not run";
  return `
    <article class="agent-trace-summary" aria-label="Human-reviewed influence preview">
      <div class="agentic-workflow-header">
        <div>
          <h4>Human-reviewed Influence Preview</h4>
          <p>Manual read-only preview of possible human-reviewed influence from shadow comparison evidence. It is advisory only, requires human review plus an approval gate, and never changes scoring, ranking, queues, approvals, resumes, execution requests, launch requests, applications, or submissions.</p>
        </div>
        <span class="agentic-workflow-badge">Default-off</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Preview", status)}
        ${renderWorkflowSummaryMetric("Human review", result.required_human_review === true || safety.human_review_required === true ? "required" : "unknown")}
        ${renderWorkflowSummaryMetric("Approval gate", result.approval_gate_required === true || safety.approval_gate_required === true ? "required" : "unknown")}
        ${renderWorkflowSummaryMetric("Read-only", safety.read_only === true ? "yes" : "unknown")}
        ${renderWorkflowSummaryMetric("Advisory", safety.advisory_only === true ? "yes" : "unknown")}
        ${renderWorkflowSummaryMetric("Scoring mutation", safety.did_mutate_scoring ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Ranking mutation", safety.did_change_ranking ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Queue mutation", safety.did_mutate_queue ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Approval mutation", safety.did_mutate_approval ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Resume mutation", safety.did_mutate_resume ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Execution request", safety.did_create_execution_request ? "created" : "no")}
        ${renderWorkflowSummaryMetric("Launch request", safety.did_create_execution_launch_request ? "created" : "no")}
        ${renderWorkflowSummaryMetric("Execution", safety.did_execute_application ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Submission", safety.did_submit_application ? "yes" : "no")}
      </div>
      ${status === "preview_not_enabled" ? renderAgentTraceReadOnlyState("Human-reviewed influence preview is not enabled. Default-off display is safe.", "info", "Influence preview not enabled") : ""}
      ${status === "preview_blocked_by_kill_switch" ? renderAgentTraceReadOnlyState("Human-reviewed influence preview is blocked by the kill switch. No influence mutation is attempted.", "warning", "Influence preview blocked by kill switch") : ""}
      ${status === "preview_blocked_missing_deterministic_context" ? renderAgentTraceReadOnlyState("Deterministic score context is missing. The read-only influence preview remains unavailable.", "info", "Influence preview missing deterministic context") : ""}
      ${status === "preview_blocked_missing_shadow_comparison" ? renderAgentTraceReadOnlyState("Shadow score comparison context is missing. Run the read-only comparison first or provide comparison context.", "info", "Influence preview missing shadow comparison") : ""}
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Preview findings", findings, { helper: "Read-only advisory findings. They do not change deterministic scoring or ranking." })}
        ${renderAgentTraceReadOnlyDetails("Deterministic score context", result.deterministic_score_context || {}, { helper: "Read-only deterministic score context used for influence preview." })}
        ${renderAgentTraceReadOnlyDetails("Shadow comparison context", result.shadow_comparison_context || {}, { helper: "Read-only shadow comparison context used for influence preview." })}
        ${renderAgentTraceReadOnlyDetails("Proposed influence summary", result.proposed_influence_summary || {}, { helper: "Advisory summary only; no influence is applied." })}
        ${renderAgentTraceReadOnlyDetails("Proposed score adjustment preview", result.proposed_score_adjustment_preview || {}, { helper: "Preview only; no score mutation is performed." })}
        ${renderAgentTraceReadOnlyDetails("Proposed ranking effect preview", result.proposed_ranking_effect_preview || {}, { helper: "Preview only; no ranking mutation is performed." })}
        ${renderAgentTraceReadOnlyDetails("Operator review summary", operatorSummary, { helper: "Human-review and approval-gate summary from the default-off preview API." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "No-mutation safety metadata for human-reviewed influence preview." })}
      </div>
      <div class="agentic-feedback-actions">
        <button type="button" class="agentic-feedback-action" data-human-reviewed-influence-preview>
          Preview Human-reviewed Influence
        </button>
        <span class="agentic-review-muted" data-human-reviewed-influence-preview-status>
          Manual read-only. Safe states include not-enabled, blocked by kill switch, missing deterministic context, and missing shadow comparison.
        </span>
      </div>
    </article>
  `;
}

function renderAgentRecommendationOverlaySection(tracePayload = {}) {
  const result = hasAgentTraceSummaryObject(tracePayload?.agent_recommendation_overlay_result)
    ? tracePayload.agent_recommendation_overlay_result
    : {};
  const safety = hasAgentTraceSummaryObject(result.safety_metadata)
    ? result.safety_metadata
    : {};
  const status = result.overlay_status || "not run";
  return `
    <article class="agent-trace-summary" aria-label="Agent recommendation overlay">
      <div class="agentic-workflow-header">
        <div>
          <h4>Agent Recommendation Overlay</h4>
          <p>Manual read-only overlay combining deterministic score context, shadow comparison, influence preview, and approval request status. It is advisory only and never changes scoring, ranking, queues, approvals, resumes, execution requests, launch requests, applications, or submissions.</p>
        </div>
        <span class="agentic-workflow-badge">Default-off overlay</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Overlay", status)}
        ${renderWorkflowSummaryMetric("Recommendation", result.recommended_review_action || "-")}
        ${renderWorkflowSummaryMetric("Read-only", safety.read_only === true ? "yes" : "unknown")}
        ${renderWorkflowSummaryMetric("Advisory", safety.advisory_only === true ? "yes" : "unknown")}
        ${renderWorkflowSummaryMetric("Scoring mutation", safety.did_mutate_scoring ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Ranking mutation", safety.did_change_ranking ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Queue mutation", safety.did_mutate_queue ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Approval mutation", safety.did_mutate_approval ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Execution", safety.did_execute_application ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Submission", safety.did_submit_application ? "yes" : "no")}
      </div>
      ${status === "overlay_not_enabled" ? renderAgentTraceReadOnlyState("Agent recommendation overlay is not enabled. Default-off display is safe.", "info", "Agent overlay not enabled") : ""}
      ${status === "overlay_blocked_by_kill_switch" ? renderAgentTraceReadOnlyState("Agent recommendation overlay is blocked by the shadow sidecar kill switch.", "warning", "Agent overlay blocked") : ""}
      ${status === "overlay_blocked_missing_deterministic_context" ? renderAgentTraceReadOnlyState("Deterministic score context is missing. The overlay cannot recommend an advisory action.", "info", "Agent overlay missing deterministic context") : ""}
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Deterministic decision context", result.deterministic_decision_context || {}, { helper: "Read-only deterministic decision context. It is not changed by the overlay." })}
        ${renderAgentTraceReadOnlyDetails("Shadow score comparison", result.shadow_score_comparison || {}, { helper: "Read-only shadow comparison status and agreement." })}
        ${renderAgentTraceReadOnlyDetails("Human-reviewed influence preview", result.human_reviewed_influence_preview || {}, { helper: "Read-only influence preview status." })}
        ${renderAgentTraceReadOnlyDetails("Approval request context", result.approval_request_context || {}, { helper: "Read-only approval request context. Overlay does not create approvals." })}
        ${renderAgentTraceReadOnlyDetails("Recommended review action", result.recommended_review_action || "", { helper: "Advisory label only. It does not alter score, rank, queue, or approvals." })}
        ${renderAgentTraceReadOnlyDetails("Overlay findings", result.overlay_findings || [], { helper: "Read-only findings supporting the advisory overlay." })}
        ${renderAgentTraceReadOnlyDetails("Operator review summary", result.operator_review_summary || {}, { helper: "Operator-facing advisory summary." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "No-mutation safety metadata for the recommendation overlay." })}
      </div>
      <div class="agentic-feedback-actions">
        <button type="button" class="agentic-feedback-action" data-agent-recommendation-overlay>
          Build Agent Recommendation Overlay
        </button>
        <span class="agentic-review-muted" data-agent-recommendation-overlay-status>
          Manual read-only and default-off. Safe states include not-enabled, kill switch blocked, missing deterministic context, and partial context.
        </span>
      </div>
    </article>
  `;
}

function renderHumanReviewedInfluenceApprovalRequestSection(tracePayload = {}) {
  const result = hasAgentTraceSummaryObject(tracePayload?.human_reviewed_influence_approval_request_result)
    ? tracePayload.human_reviewed_influence_approval_request_result
    : {};
  const safety = hasAgentTraceSummaryObject(result.safety_metadata)
    ? result.safety_metadata
    : {};
  const agentRun = tracePayload?.agent_run && typeof tracePayload.agent_run === "object"
    ? tracePayload.agent_run
    : {};
  const metadata = agentRun?.metadata && typeof agentRun.metadata === "object" ? agentRun.metadata : {};
  const contextId = tracePayload?.agent_run_id || agentRun.agent_run_id || "";
  const jobId = metadata.job_id || metadata.merge_key || "";
  const status = result.request_status || "not run";
  return `
    <article class="agent-trace-summary" aria-label="Human-reviewed influence approval request">
      <div class="agentic-workflow-header">
        <div>
          <h4>Human-reviewed Influence Approval Request</h4>
          <p>Manual approval-request creation for a human-reviewed influence preview. It creates no score, ranking, queue, resume, execution, launch, application, or submission changes and never applies influence.</p>
        </div>
        <span class="agentic-workflow-badge">Manual approval gate</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Request", status)}
        ${renderWorkflowSummaryMetric("Created id", result.created_approval_request_id || "-")}
        ${renderWorkflowSummaryMetric("Approval created", safety.did_create_approval ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Influence applied", safety.influence_not_applied === true ? "no" : "unknown")}
        ${renderWorkflowSummaryMetric("Scoring mutation", safety.did_mutate_scoring ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Ranking mutation", safety.did_change_ranking ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Queue mutation", safety.did_mutate_queue ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Execution", safety.did_execute_application ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Submission", safety.did_submit_application ? "yes" : "no")}
      </div>
      ${status === "not_enabled" ? renderAgentTraceReadOnlyState("Human-reviewed influence approval request is not enabled. Default-off state is safe.", "info", "Influence approval request not enabled") : ""}
      ${status === "blocked_by_kill_switch" ? renderAgentTraceReadOnlyState("Influence approval request is blocked by the shadow sidecar kill switch.", "warning", "Influence approval request blocked") : ""}
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Created approval request id", result.created_approval_request_id || "", { helper: "Created approval request identifier when the manual approval-gated path succeeds." })}
        ${renderAgentTraceReadOnlyDetails("Influence preview payload", result.influence_preview_payload || {}, { helper: "Source human-reviewed influence preview used for this approval request." })}
        ${renderAgentTraceReadOnlyDetails("Proposed influence summary", result.proposed_influence_summary || {}, { helper: "Advisory influence summary. Influence is not applied." })}
        ${renderAgentTraceReadOnlyDetails("Proposed score adjustment preview", result.proposed_score_adjustment_preview || {}, { helper: "Preview only; no score mutation is performed." })}
        ${renderAgentTraceReadOnlyDetails("Proposed ranking effect preview", result.proposed_ranking_effect_preview || {}, { helper: "Preview only; no ranking mutation is performed." })}
        ${renderAgentTraceReadOnlyDetails("Blocked actions", result.blocked_actions || [], { helper: "Manual approval request blockers." })}
        ${renderAgentTraceReadOnlyDetails("Next safe step", result.next_safe_step || "", { helper: "Next safe manual step." })}
        ${renderAgentTraceReadOnlyDetails("Rationale", result.rationale || "", { helper: "Manual approval-gated influence request rationale." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "No-influence-application safety metadata." })}
      </div>
      <div class="agentic-review-actions">
        <label class="agentic-review-muted">
          <input type="checkbox" data-human-reviewed-influence-approval-request-confirmation>
          Explicitly create influence approval request
        </label>
        <button type="button" class="agentic-feedback-action" data-human-reviewed-influence-approval-request data-context-id="${escapeHtml(contextId)}" data-job-id="${escapeHtml(jobId)}">
          Request Influence Approval
        </button>
        <span class="agentic-review-muted" data-human-reviewed-influence-approval-request-status>
          Manual only and default-off. Creates only an approval request record when explicitly enabled and confirmed.
        </span>
      </div>
    </article>
  `;
}

function renderAgentTraceDetailedSections(tracePayload = {}) {
  const detailedSections = [
    renderAgentTraceSummarySection(tracePayload?.trace_summary),
    renderAgentStageTraceBundleSection(tracePayload?.stage_trace_bundle),
    renderAgentStageTraceHealthSection(tracePayload?.stage_trace_health),
    renderAgentStageTraceReadinessSection(tracePayload?.stage_trace_readiness),
  ].filter(Boolean).join("");
  if (!detailedSections) return "";
  if (!hasAgentTraceSummaryObject(tracePayload?.trace_evidence_pack)) {
    return detailedSections;
  }
  return `
    <details class="agent-trace-detail-sections" data-collapsed-by-default="true" aria-label="Read-only detailed trace sections">
      <summary>Detailed trace sections</summary>
      <div class="agentic-review-muted">Lower-level trace summary, bundle, health, and readiness details remain read-only and collapsed below the evidence pack.</div>
      ${detailedSections}
    </details>
  `;
}

function renderAgentTraceCriticEvaluatorSection(tracePayload = {}) {
  const approvalRequestId = String(tracePayload?.critic_approval_request_id || tracePayload?.approval_request_id || "").trim();
  const criticResult = hasAgentTraceSummaryObject(tracePayload?.critic_evaluator_result)
    ? tracePayload.critic_evaluator_result
    : {};
  const safety = hasAgentTraceSummaryObject(criticResult.safety_metadata)
    ? criticResult.safety_metadata
    : {};
  const canInvoke = Boolean(approvalRequestId);
  return `
    <article class="agent-trace-summary" aria-label="Read-only critic evaluator">
      <div class="agentic-workflow-header">
        <div>
          <h4>Read-only Critic Evaluator</h4>
          <p>Manual, non-actionable trace review. It does not mutate approvals, write storage, call LLMs, change queues, execute applications, or submit applications.</p>
        </div>
        <span class="agentic-workflow-badge">Manual read-only</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Critic", criticResult.critic_status || criticResult.evaluator_status || "not run")}
        ${renderWorkflowSummaryMetric("Readiness", criticResult.readiness_status || "unknown")}
        ${renderWorkflowSummaryMetric("Evidence pack", criticResult.evidence_pack_available === true ? "available" : "not available")}
        ${renderWorkflowSummaryMetric("Writes", safety.did_write_storage ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("LLM calls", safety.did_call_llm ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Execution", safety.did_execute_application ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Submission", safety.did_submit_application ? "yes" : "no")}
      </div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Reason codes", criticResult.reason_codes, { helper: "Read-only critic reason codes." })}
        ${renderAgentTraceReadOnlyDetails("Warnings", criticResult.warnings || criticResult.evaluator_warnings, { helper: "Read-only critic warnings." })}
        ${renderAgentTraceReadOnlyDetails("Blockers", criticResult.blockers || criticResult.evaluator_findings, { helper: "Read-only critic blockers." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable critic evaluator safety metadata." })}
      </div>
      <div class="agentic-review-actions">
        <button type="button" class="agentic-feedback-action" data-agentic-critic-evaluator-readonly data-approval-request-id="${escapeHtml(approvalRequestId)}" ${canInvoke ? "" : "disabled"}>
          Run read-only critic
        </button>
        <span class="agentic-review-muted" data-agentic-critic-evaluator-status>
          ${escapeHtml(canInvoke ? "Manual only. No approval mutation or execution." : "Approval request unavailable. Critic evaluator is not available.")}
        </span>
      </div>
    </article>
  `;
}

function renderManualJdIntelligenceDryRunSection(tracePayload = {}) {
  const result = hasAgentTraceSummaryObject(tracePayload?.manual_jd_intelligence_dry_run_result)
    ? tracePayload.manual_jd_intelligence_dry_run_result
    : {};
  const safety = hasAgentTraceSummaryObject(result.safety_metadata)
    ? result.safety_metadata
    : {};
  const agentRun = tracePayload?.agent_run && typeof tracePayload.agent_run === "object"
    ? tracePayload.agent_run
    : {};
  const metadata = agentRun?.metadata && typeof agentRun.metadata === "object" ? agentRun.metadata : {};
  const jobTitle = metadata.job_title || metadata.title || "";
  const company = metadata.company || "";
  const location = metadata.location || "";
  const jobId = metadata.job_id || metadata.merge_key || "";
  const contextId = tracePayload?.agent_run_id || agentRun.agent_run_id || "";
  return `
    <article class="agent-trace-summary" aria-label="Manual JD intelligence dry-run">
      <div class="agentic-workflow-header">
        <div>
          <h4>Manual JD Intelligence Dry-run</h4>
          <p>Manual read-only dry-run. The feature flag is off by default, and this panel does not write storage, mutate queues, change scoring or ranking, execute applications, or submit applications.</p>
        </div>
        <span class="agentic-workflow-badge">Dry-run read-only</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Status", result.validation_status || "not run")}
        ${renderWorkflowSummaryMetric("Fallback", result.fallback_used === true ? "yes" : result.fallback_used === false ? "no" : "-")}
        ${renderWorkflowSummaryMetric("Required skills", Array.isArray(result.required_skills) ? result.required_skills.length : 0)}
        ${renderWorkflowSummaryMetric("Preferred tools", Array.isArray(result.preferred_tools) ? result.preferred_tools.length : 0)}
        ${renderWorkflowSummaryMetric("LLM calls", safety.did_call_llm ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Execution", safety.did_execute_application ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Submission", safety.did_submit_application ? "yes" : "no")}
      </div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Required skills", result.required_skills || [], { helper: "Dry-run extracted required skills." })}
        ${renderAgentTraceReadOnlyDetails("Preferred skills", result.preferred_skills || [], { helper: "Dry-run extracted preferred skills." })}
        ${renderAgentTraceReadOnlyDetails("Tools", { required_tools: result.required_tools || [], preferred_tools: result.preferred_tools || [] }, { helper: "Dry-run extracted tools." })}
        ${renderAgentTraceReadOnlyDetails("Risk flags", result.risk_flags || [], { helper: "Dry-run risk flags." })}
        ${renderAgentTraceReadOnlyDetails("Validation errors", result.validation_errors || [], { helper: "Dry-run validation errors." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable JD intelligence dry-run safety metadata." })}
      </div>
      <div class="agentic-review-actions">
        <button type="button" class="agentic-feedback-action" data-manual-jd-intelligence-dry-run data-job-title="${escapeHtml(jobTitle)}" data-company="${escapeHtml(company)}" data-location="${escapeHtml(location)}" data-job-id="${escapeHtml(jobId)}" data-context-id="${escapeHtml(contextId)}">
          Run JD dry-run
        </button>
        <span class="agentic-review-muted" data-manual-jd-intelligence-dry-run-status>
          Manual only. Feature flag defaults off; normal result is a disabled fallback until provider wiring is explicitly enabled later.
        </span>
      </div>
    </article>
  `;
}

function renderManualResumeMatchDryRunSection(tracePayload = {}) {
  const result = hasAgentTraceSummaryObject(tracePayload?.manual_resume_match_dry_run_result)
    ? tracePayload.manual_resume_match_dry_run_result
    : {};
  const safety = hasAgentTraceSummaryObject(result.safety_metadata)
    ? result.safety_metadata
    : {};
  const jdResult = hasAgentTraceSummaryObject(tracePayload?.manual_jd_intelligence_dry_run_result)
    ? tracePayload.manual_jd_intelligence_dry_run_result
    : {};
  const agentRun = tracePayload?.agent_run && typeof tracePayload.agent_run === "object"
    ? tracePayload.agent_run
    : {};
  const contextId = tracePayload?.agent_run_id || agentRun.agent_run_id || "";
  const metadata = agentRun?.metadata && typeof agentRun.metadata === "object" ? agentRun.metadata : {};
  const jobId = metadata.job_id || metadata.merge_key || "";
  return `
    <article class="agent-trace-summary" aria-label="Manual resume match dry-run">
      <div class="agentic-workflow-header">
        <div>
          <h4>Manual Resume Match Dry-run</h4>
          <p>Manual read-only dry-run. It compares submitted JD intelligence and resume evidence in memory only and does not mutate resumes, scoring, ranking, queues, approvals, execution, or submissions.</p>
        </div>
        <span class="agentic-workflow-badge">Dry-run read-only</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Match", result.match_status || "not run")}
        ${renderWorkflowSummaryMetric("Selected resume", result.selected_resume_id || "-")}
        ${renderWorkflowSummaryMetric("Candidates", Array.isArray(result.candidate_resume_scores) ? result.candidate_resume_scores.length : 0)}
        ${renderWorkflowSummaryMetric("Confidence", result.confidence ?? "-")}
        ${renderWorkflowSummaryMetric("LLM calls", safety.did_call_llm ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Resume mutation", safety.did_mutate_resume ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Execution", safety.did_execute_application ? "yes" : "no")}
      </div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Candidate scores", result.candidate_resume_scores || [], { helper: "Dry-run resume candidate ordering only." })}
        ${renderAgentTraceReadOnlyDetails("Dimension scores", result.dimension_scores || {}, { helper: "Dry-run dimension scores." })}
        ${renderAgentTraceReadOnlyDetails("Matched evidence", result.matched_evidence || [], { helper: "Dry-run matched resume evidence." })}
        ${renderAgentTraceReadOnlyDetails("Missing evidence", result.missing_evidence || [], { helper: "Dry-run missing evidence." })}
        ${renderAgentTraceReadOnlyDetails("Risk flags", result.risk_flags || [], { helper: "Dry-run risk flags." })}
        ${renderAgentTraceReadOnlyDetails("Rationale", result.rationale || "", { helper: "Dry-run rationale." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable resume match dry-run safety metadata." })}
      </div>
      <div class="agentic-review-actions">
        <button type="button" class="agentic-feedback-action" data-manual-resume-match-dry-run data-context-id="${escapeHtml(contextId)}" data-job-id="${escapeHtml(jobId)}">
          Run resume match dry-run
        </button>
        <span class="agentic-review-muted" data-manual-resume-match-dry-run-status>
          Manual only. Submitted resume evidence is optional; missing evidence renders as a read-only dry-run finding.
        </span>
      </div>
    </article>
  `;
}

function renderManualTailoringSuggestionDryRunSection(tracePayload = {}) {
  const result = hasAgentTraceSummaryObject(tracePayload?.manual_tailoring_suggestion_dry_run_result)
    ? tracePayload.manual_tailoring_suggestion_dry_run_result
    : {};
  const safety = hasAgentTraceSummaryObject(result.safety_metadata)
    ? result.safety_metadata
    : {};
  const resumeResult = hasAgentTraceSummaryObject(tracePayload?.manual_resume_match_dry_run_result)
    ? tracePayload.manual_resume_match_dry_run_result
    : {};
  const agentRun = tracePayload?.agent_run && typeof tracePayload.agent_run === "object"
    ? tracePayload.agent_run
    : {};
  const metadata = agentRun?.metadata && typeof agentRun.metadata === "object" ? agentRun.metadata : {};
  const contextId = tracePayload?.agent_run_id || agentRun.agent_run_id || "";
  const jobId = metadata.job_id || metadata.merge_key || "";
  const selectedResumeId = result.selected_resume_id || resumeResult.selected_resume_id || "";
  return `
    <article class="agent-trace-summary" aria-label="Manual tailoring suggestion dry-run">
      <div class="agentic-workflow-header">
        <div>
          <h4>Manual Tailoring Suggestion Dry-run</h4>
          <p>Manual read-only dry-run. It proposes tailoring candidates from submitted JD signals, resume match gaps, and resume evidence in memory only and does not mutate resume content, scoring, ranking, queues, approvals, execution, or submissions.</p>
        </div>
        <span class="agentic-workflow-badge">Dry-run read-only</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Status", result.suggestion_status || "not run")}
        ${renderWorkflowSummaryMetric("Selected resume", result.selected_resume_id || "-")}
        ${renderWorkflowSummaryMetric("Patch-ready", Array.isArray(result.patch_ready_suggestions) ? result.patch_ready_suggestions.length : 0)}
        ${renderWorkflowSummaryMetric("Guidance", Array.isArray(result.guidance_only_suggestions) ? result.guidance_only_suggestions.length : 0)}
        ${renderWorkflowSummaryMetric("Rejected", Array.isArray(result.rejected_suggestions) ? result.rejected_suggestions.length : 0)}
        ${renderWorkflowSummaryMetric("Projected delta", result.projected_score_delta ?? "-")}
        ${renderWorkflowSummaryMetric("Resume mutation", safety.did_mutate_resume ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("LLM calls", safety.did_call_llm ? "yes" : "no")}
      </div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Patch-ready suggestions", result.patch_ready_suggestions || [], { helper: "Dry-run patch-ready suggestions with direct resume evidence." })}
        ${renderAgentTraceReadOnlyDetails("Guidance-only suggestions", result.guidance_only_suggestions || [], { helper: "Dry-run guidance when direct evidence is incomplete." })}
        ${renderAgentTraceReadOnlyDetails("Rejected suggestions", result.rejected_suggestions || [], { helper: "Dry-run rejected unsupported tailoring claims." })}
        ${renderAgentTraceReadOnlyDetails("Missing evidence", result.missing_evidence || [], { helper: "Dry-run missing evidence." })}
        ${renderAgentTraceReadOnlyDetails("Unsupported claim risks", result.unsupported_claim_risks || [], { helper: "Dry-run unsupported claim risks." })}
        ${renderAgentTraceReadOnlyDetails("Rationale", result.rationale || "", { helper: "Dry-run rationale." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable tailoring suggestion dry-run safety metadata." })}
      </div>
      <div class="agentic-review-actions">
        <button type="button" class="agentic-feedback-action" data-manual-tailoring-suggestion-dry-run data-context-id="${escapeHtml(contextId)}" data-job-id="${escapeHtml(jobId)}" data-selected-resume-id="${escapeHtml(selectedResumeId)}">
          Run tailoring dry-run
        </button>
        <span class="agentic-review-muted" data-manual-tailoring-suggestion-dry-run-status>
          Manual only. Submitted resume evidence is optional; unsupported claims remain guidance-only or rejected.
        </span>
      </div>
    </article>
  `;
}

function renderManualCriticGuardrailDryRunSection(tracePayload = {}) {
  const result = hasAgentTraceSummaryObject(tracePayload?.manual_critic_guardrail_dry_run_result)
    ? tracePayload.manual_critic_guardrail_dry_run_result
    : {};
  const safety = hasAgentTraceSummaryObject(result.safety_metadata)
    ? result.safety_metadata
    : {};
  const agentRun = tracePayload?.agent_run && typeof tracePayload.agent_run === "object"
    ? tracePayload.agent_run
    : {};
  const metadata = agentRun?.metadata && typeof agentRun.metadata === "object" ? agentRun.metadata : {};
  const contextId = tracePayload?.agent_run_id || agentRun.agent_run_id || "";
  const jobId = metadata.job_id || metadata.merge_key || "";
  return `
    <article class="agent-trace-summary" aria-label="Manual critic guardrail dry-run">
      <div class="agentic-workflow-header">
        <div>
          <h4>Manual Critic Guardrail Dry-run</h4>
          <p>Manual read-only dry-run. It validates tailoring suggestions in memory only and does not mutate resume content, scoring, ranking, queues, approvals, execution, or submissions.</p>
        </div>
        <span class="agentic-workflow-badge">Dry-run read-only</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Critic", result.critic_status || "not run")}
        ${renderWorkflowSummaryMetric("Approved", Array.isArray(result.approved_suggestions) ? result.approved_suggestions.length : 0)}
        ${renderWorkflowSummaryMetric("Downgraded", Array.isArray(result.downgraded_suggestions) ? result.downgraded_suggestions.length : 0)}
        ${renderWorkflowSummaryMetric("Rejected", Array.isArray(result.rejected_suggestions) ? result.rejected_suggestions.length : 0)}
        ${renderWorkflowSummaryMetric("Confidence", result.confidence ?? "-")}
        ${renderWorkflowSummaryMetric("Resume mutation", safety.did_mutate_resume ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("LLM calls", safety.did_call_llm ? "yes" : "no")}
      </div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Approved suggestions", result.approved_suggestions || [], { helper: "Dry-run approved low-risk suggestions." })}
        ${renderAgentTraceReadOnlyDetails("Downgraded suggestions", result.downgraded_suggestions || [], { helper: "Dry-run suggestions downgraded to guidance." })}
        ${renderAgentTraceReadOnlyDetails("Rejected suggestions", result.rejected_suggestions || [], { helper: "Dry-run rejected guardrail findings." })}
        ${renderAgentTraceReadOnlyDetails("Reason codes", result.reason_codes || [], { helper: "Dry-run critic reason codes." })}
        ${renderAgentTraceReadOnlyDetails("Unsupported claim risks", result.unsupported_claim_risks || [], { helper: "Dry-run unsupported claim risks." })}
        ${renderAgentTraceReadOnlyDetails("ATS risks", result.ats_risks || [], { helper: "Dry-run ATS risks." })}
        ${renderAgentTraceReadOnlyDetails("Readability risks", result.readability_risks || [], { helper: "Dry-run readability risks." })}
        ${renderAgentTraceReadOnlyDetails("Evidence gaps", result.evidence_gaps || [], { helper: "Dry-run evidence gaps." })}
        ${renderAgentTraceReadOnlyDetails("Rationale", result.rationale || "", { helper: "Dry-run rationale." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable critic guardrail dry-run safety metadata." })}
      </div>
      <div class="agentic-review-actions">
        <button type="button" class="agentic-feedback-action" data-manual-critic-guardrail-dry-run data-context-id="${escapeHtml(contextId)}" data-job-id="${escapeHtml(jobId)}">
          Run critic dry-run
        </button>
        <span class="agentic-review-muted" data-manual-critic-guardrail-dry-run-status>
          Manual only. Suggestions are validated for review context; no approval, resume, or queue state changes.
        </span>
      </div>
    </article>
  `;
}

function renderManualStrategyRecommendationDryRunSection(tracePayload = {}) {
  const result = hasAgentTraceSummaryObject(tracePayload?.manual_strategy_recommendation_dry_run_result)
    ? tracePayload.manual_strategy_recommendation_dry_run_result
    : {};
  const safety = hasAgentTraceSummaryObject(result.safety_metadata)
    ? result.safety_metadata
    : {};
  const agentRun = tracePayload?.agent_run && typeof tracePayload.agent_run === "object"
    ? tracePayload.agent_run
    : {};
  const metadata = agentRun?.metadata && typeof agentRun.metadata === "object" ? agentRun.metadata : {};
  const contextId = tracePayload?.agent_run_id || agentRun.agent_run_id || "";
  const jobId = metadata.job_id || metadata.merge_key || "";
  return `
    <article class="agent-trace-summary" aria-label="Manual strategy recommendation dry-run">
      <div class="agentic-workflow-header">
        <div>
          <h4>Manual Strategy Recommendation Dry-run</h4>
          <p>Manual read-only dry-run. It combines prior dry-run outputs into an advisory next action and does not mutate resume content, scoring, ranking, queues, approvals, execution, or submissions.</p>
        </div>
        <span class="agentic-workflow-badge">Dry-run read-only</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Strategy", result.strategy_status || "not run")}
        ${renderWorkflowSummaryMetric("Action", result.recommendation_action || "-")}
        ${renderWorkflowSummaryMetric("Priority", result.priority_hint || "-")}
        ${renderWorkflowSummaryMetric("Readiness", result.readiness_level || "-")}
        ${renderWorkflowSummaryMetric("Human review", result.required_human_review === true ? "yes" : result.required_human_review === false ? "no" : "-")}
        ${renderWorkflowSummaryMetric("Confidence", result.confidence ?? "-")}
        ${renderWorkflowSummaryMetric("Advisory", safety.advisory_only ? "yes" : "unknown")}
        ${renderWorkflowSummaryMetric("LLM calls", safety.did_call_llm ? "yes" : "no")}
      </div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Recommendation label", result.recommendation_label || "", { helper: "Dry-run recommendation label." })}
        ${renderAgentTraceReadOnlyDetails("Decision reasons", result.decision_reasons || [], { helper: "Dry-run strategy decision reasons." })}
        ${renderAgentTraceReadOnlyDetails("Blocking risks", result.blocking_risks || [], { helper: "Dry-run blocking risks." })}
        ${renderAgentTraceReadOnlyDetails("Improvement actions", result.improvement_actions || [], { helper: "Dry-run suggested evidence or review improvements." })}
        ${renderAgentTraceReadOnlyDetails("Rationale", result.rationale || "", { helper: "Dry-run rationale." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable strategy recommendation dry-run safety metadata." })}
      </div>
      <div class="agentic-review-actions">
        <button type="button" class="agentic-feedback-action" data-manual-strategy-recommendation-dry-run data-context-id="${escapeHtml(contextId)}" data-job-id="${escapeHtml(jobId)}">
          Run strategy dry-run
        </button>
        <span class="agentic-review-muted" data-manual-strategy-recommendation-dry-run-status>
          Manual only. Recommendation is advisory and does not change queue, approval, scoring, execution, or submission state.
        </span>
      </div>
    </article>
  `;
}

function renderManualShadowAgenticWorkflowChainDryRunSection(tracePayload = {}) {
  const result = hasAgentTraceSummaryObject(tracePayload?.manual_shadow_agentic_workflow_chain_dry_run_result)
    ? tracePayload.manual_shadow_agentic_workflow_chain_dry_run_result
    : {};
  const safety = hasAgentTraceSummaryObject(result.safety_metadata)
    ? result.safety_metadata
    : {};
  const agentRun = tracePayload?.agent_run && typeof tracePayload.agent_run === "object"
    ? tracePayload.agent_run
    : {};
  const metadata = agentRun?.metadata && typeof agentRun.metadata === "object" ? agentRun.metadata : {};
  const contextId = tracePayload?.agent_run_id || agentRun.agent_run_id || "";
  const jobTitle = metadata.job_title || metadata.title || "";
  const company = metadata.company || "";
  const location = metadata.location || "";
  const jobId = metadata.job_id || metadata.merge_key || "";
  return `
    <article class="agent-trace-summary" aria-label="Manual shadow agentic workflow chain dry-run">
      <div class="agentic-workflow-header">
        <div>
          <h4>Manual Shadow Chain Dry-run</h4>
          <p>Manual read-only shadow chain. It composes dry-run stages for advisory review and does not mutate resume content, scoring, ranking, queues, approvals, execution, or submissions.</p>
        </div>
        <span class="agentic-workflow-badge">Shadow dry-run</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Chain", result.shadow_chain_status || "not run")}
        ${renderWorkflowSummaryMetric("Action", result.recommendation_action || "-")}
        ${renderWorkflowSummaryMetric("Human review", result.required_human_review === true ? "yes" : result.required_human_review === false ? "no" : "-")}
        ${renderWorkflowSummaryMetric("Confidence", result.confidence ?? "-")}
        ${renderWorkflowSummaryMetric("Shadow mode", safety.shadow_mode ? "yes" : "unknown")}
        ${renderWorkflowSummaryMetric("LLM calls", safety.did_call_llm ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Execution", safety.did_execute_application ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Submission", safety.did_submit_application ? "yes" : "no")}
      </div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Stage order", result.stage_order || [], { helper: "Shadow dry-run stage order." })}
        ${renderAgentTraceReadOnlyDetails("Stage statuses", result.stage_statuses || {}, { helper: "Compact shadow dry-run stage statuses." })}
        ${renderAgentTraceReadOnlyDetails("Blocking risks", result.blocking_risks || [], { helper: "Shadow dry-run blocking risks." })}
        ${renderAgentTraceReadOnlyDetails("Improvement actions", result.improvement_actions || [], { helper: "Shadow dry-run improvement actions." })}
        ${renderAgentTraceReadOnlyDetails("Rationale", result.rationale || "", { helper: "Shadow dry-run rationale." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable shadow chain dry-run safety metadata." })}
      </div>
      <div class="agentic-review-actions">
        <button type="button" class="agentic-feedback-action" data-manual-shadow-agentic-workflow-chain-dry-run data-job-title="${escapeHtml(jobTitle)}" data-company="${escapeHtml(company)}" data-location="${escapeHtml(location)}" data-context-id="${escapeHtml(contextId)}" data-job-id="${escapeHtml(jobId)}">
          Run Shadow Chain Dry-run
        </button>
        <span class="agentic-review-muted" data-manual-shadow-agentic-workflow-chain-dry-run-status>
          Manual only. The consolidated result is advisory and does not add pipeline wiring or mutate runtime state.
        </span>
      </div>
    </article>
  `;
}

function renderManualShadowRecommendationHandoffDryRunSection(tracePayload = {}) {
  const result = hasAgentTraceSummaryObject(tracePayload?.manual_shadow_recommendation_handoff_dry_run_result)
    ? tracePayload.manual_shadow_recommendation_handoff_dry_run_result
    : {};
  const safety = hasAgentTraceSummaryObject(result.safety_metadata)
    ? result.safety_metadata
    : {};
  const agentRun = tracePayload?.agent_run && typeof tracePayload.agent_run === "object"
    ? tracePayload.agent_run
    : {};
  const metadata = agentRun?.metadata && typeof agentRun.metadata === "object" ? agentRun.metadata : {};
  const contextId = tracePayload?.agent_run_id || agentRun.agent_run_id || "";
  const jobTitle = metadata.job_title || metadata.title || "";
  const company = metadata.company || "";
  const location = metadata.location || "";
  const jobId = metadata.job_id || metadata.merge_key || "";
  return `
    <article class="agent-trace-summary" aria-label="Manual shadow recommendation handoff dry-run">
      <div class="agentic-workflow-header">
        <div>
          <h4>Manual Shadow Recommendation Handoff</h4>
          <p>Review-only handoff. It creates no approval request, changes no queue or approval state, and never executes or submits applications.</p>
        </div>
        <span class="agentic-workflow-badge">Human-gated</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Handoff", result.handoff_status || "not run")}
        ${renderWorkflowSummaryMetric("Action", result.recommendation_action || "-")}
        ${renderWorkflowSummaryMetric("Human gate", safety.human_gate_required ? "required" : "unknown")}
        ${renderWorkflowSummaryMetric("Review", result.required_human_review === true ? "required" : "-")}
        ${renderWorkflowSummaryMetric("Confidence", result.confidence ?? "-")}
        ${renderWorkflowSummaryMetric("Approval created", safety.did_create_approval ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Execution", safety.did_execute_application ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Submission", safety.did_submit_application ? "yes" : "no")}
      </div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Recommendation label", result.recommendation_label || "", { helper: "Review-only handoff recommendation label." })}
        ${renderAgentTraceReadOnlyDetails("Reviewer decision options", result.reviewer_decision_options || [], { helper: "Human-only review choices. These do not mutate approval state." })}
        ${renderAgentTraceReadOnlyDetails("Blocking risks", result.blocking_risks || [], { helper: "Review-only handoff blocking risks." })}
        ${renderAgentTraceReadOnlyDetails("Improvement actions", result.improvement_actions || [], { helper: "Review-only handoff improvement actions." })}
        ${renderAgentTraceReadOnlyDetails("Stage statuses", result.stage_statuses || {}, { helper: "Source shadow-chain stage statuses." })}
        ${renderAgentTraceReadOnlyDetails("Rationale", result.rationale || "", { helper: "Review-only handoff rationale." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable shadow recommendation handoff safety metadata." })}
      </div>
      <div class="agentic-review-actions">
        <button type="button" class="agentic-feedback-action" data-manual-shadow-recommendation-handoff-dry-run data-job-title="${escapeHtml(jobTitle)}" data-company="${escapeHtml(company)}" data-location="${escapeHtml(location)}" data-context-id="${escapeHtml(contextId)}" data-job-id="${escapeHtml(jobId)}">
          Build Shadow Recommendation Handoff
        </button>
        <span class="agentic-review-muted" data-manual-shadow-recommendation-handoff-dry-run-status>
          Manual only. This builds a review card and does not create or update approvals.
        </span>
      </div>
    </article>
  `;
}

function renderManualHumanDecisionCaptureDryRunSection(tracePayload = {}) {
  const result = hasAgentTraceSummaryObject(tracePayload?.manual_human_decision_capture_dry_run_result)
    ? tracePayload.manual_human_decision_capture_dry_run_result
    : {};
  const safety = hasAgentTraceSummaryObject(result.safety_metadata)
    ? result.safety_metadata
    : {};
  const handoff = hasAgentTraceSummaryObject(tracePayload?.manual_shadow_recommendation_handoff_dry_run_result)
    ? tracePayload.manual_shadow_recommendation_handoff_dry_run_result
    : {};
  const agentRun = tracePayload?.agent_run && typeof tracePayload.agent_run === "object"
    ? tracePayload.agent_run
    : {};
  const metadata = agentRun?.metadata && typeof agentRun.metadata === "object" ? agentRun.metadata : {};
  const contextId = tracePayload?.agent_run_id || agentRun.agent_run_id || "";
  const jobTitle = metadata.job_title || metadata.title || "";
  const company = metadata.company || "";
  const location = metadata.location || "";
  const jobId = metadata.job_id || metadata.merge_key || "";
  const options = Array.isArray(handoff.reviewer_decision_options) && handoff.reviewer_decision_options.length
    ? handoff.reviewer_decision_options
    : [
      "accept_recommendation_for_review",
      "request_more_tailoring",
      "save_for_later",
      "dismiss_shadow_recommendation",
    ];
  return `
    <article class="agent-trace-summary" aria-label="Manual human decision capture dry-run">
      <div class="agentic-workflow-header">
        <div>
          <h4>Manual Human Decision Capture Dry-run</h4>
          <p>Simulated reviewer decision capture. It creates no approval request, changes no queue or approval state, and never executes or submits applications.</p>
        </div>
        <span class="agentic-workflow-badge">Decision dry-run</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Capture", result.decision_capture_status || "not run")}
        ${renderWorkflowSummaryMetric("Decision", result.reviewer_decision || "-")}
        ${renderWorkflowSummaryMetric("Accepted", result.accepted_decision === true ? "yes" : result.accepted_decision === false ? "no" : "-")}
        ${renderWorkflowSummaryMetric("Next action", result.next_review_action || "-")}
        ${renderWorkflowSummaryMetric("Approval created", safety.did_create_approval ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Execution", safety.did_execute_application ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Submission", safety.did_submit_application ? "yes" : "no")}
      </div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Reviewer note", result.reviewer_note || "", { helper: "Simulated reviewer note." })}
        ${renderAgentTraceReadOnlyDetails("Source recommendation action", result.source_recommendation_action || "", { helper: "Source handoff recommendation action." })}
        ${renderAgentTraceReadOnlyDetails("Blocking risks", result.blocking_risks || [], { helper: "Decision capture dry-run blocking risks." })}
        ${renderAgentTraceReadOnlyDetails("Improvement actions", result.improvement_actions || [], { helper: "Decision capture dry-run improvement actions." })}
        ${renderAgentTraceReadOnlyDetails("Rationale", result.rationale || "", { helper: "Decision capture dry-run rationale." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable human decision capture safety metadata." })}
      </div>
      <div class="agentic-review-actions">
        <select class="agentic-feedback-action" data-manual-human-decision-capture-dry-run-select aria-label="Shadow recommendation reviewer decision">
          ${options.map((option) => `<option value="${escapeHtml(option)}">${escapeHtml(option)}</option>`).join("")}
        </select>
        <button type="button" class="agentic-feedback-action" data-manual-human-decision-capture-dry-run data-job-title="${escapeHtml(jobTitle)}" data-company="${escapeHtml(company)}" data-location="${escapeHtml(location)}" data-context-id="${escapeHtml(contextId)}" data-job-id="${escapeHtml(jobId)}">
          Capture Decision Dry-run
        </button>
        <span class="agentic-review-muted" data-manual-human-decision-capture-dry-run-status>
          Manual only. This records a simulated decision and does not mutate approval state.
        </span>
      </div>
    </article>
  `;
}

function renderManualHumanApprovedActionPlanDryRunSection(tracePayload = {}) {
  const result = hasAgentTraceSummaryObject(tracePayload?.manual_human_approved_action_plan_dry_run_result)
    ? tracePayload.manual_human_approved_action_plan_dry_run_result
    : {};
  const safety = hasAgentTraceSummaryObject(result.safety_metadata)
    ? result.safety_metadata
    : {};
  const agentRun = tracePayload?.agent_run && typeof tracePayload.agent_run === "object"
    ? tracePayload.agent_run
    : {};
  const metadata = agentRun?.metadata && typeof agentRun.metadata === "object" ? agentRun.metadata : {};
  const contextId = tracePayload?.agent_run_id || agentRun.agent_run_id || "";
  const jobId = metadata.job_id || metadata.merge_key || "";
  return `
    <article class="agent-trace-summary" aria-label="Manual human-approved action plan dry-run">
      <div class="agentic-workflow-header">
        <div>
          <h4>Manual Human-approved Action Plan Dry-run</h4>
          <p>Preview-only action plan. It creates no approval request, mutates no queue or resume content, and never executes or submits applications.</p>
        </div>
        <span class="agentic-workflow-badge">Action plan preview</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Plan", result.action_plan_status || "not run")}
        ${renderWorkflowSummaryMetric("Action", result.planned_action || "-")}
        ${renderWorkflowSummaryMetric("Confirmation", result.required_human_confirmation === true ? "required" : "-")}
        ${renderWorkflowSummaryMetric("Approval created", safety.did_create_approval ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Queue mutation", safety.did_mutate_queue ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Execution", safety.did_execute_application ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Submission", safety.did_submit_application ? "yes" : "no")}
      </div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Planned action label", result.planned_action_label || "", { helper: "Preview-only planned action label." })}
        ${renderAgentTraceReadOnlyDetails("Action steps", result.action_steps || [], { helper: "Preview-only action steps." })}
        ${renderAgentTraceReadOnlyDetails("Blocked actions", result.blocked_actions || [], { helper: "Preview-only blocked actions." })}
        ${renderAgentTraceReadOnlyDetails("Next safe step", result.next_safe_step || "", { helper: "Preview-only next safe step." })}
        ${renderAgentTraceReadOnlyDetails("Rationale", result.rationale || "", { helper: "Action plan dry-run rationale." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable human-approved action plan safety metadata." })}
      </div>
      <div class="agentic-review-actions">
        <button type="button" class="agentic-feedback-action" data-manual-human-approved-action-plan-dry-run data-context-id="${escapeHtml(contextId)}" data-job-id="${escapeHtml(jobId)}">
          Build Action Plan Dry-run
        </button>
        <span class="agentic-review-muted" data-manual-human-approved-action-plan-dry-run-status>
          Manual only. This previews a safe action plan and does not mutate approval, queue, resume, execution, or submission state.
        </span>
      </div>
    </article>
  `;
}

function renderManualReviewPacketPreviewDryRunSection(tracePayload = {}) {
  const result = hasAgentTraceSummaryObject(tracePayload?.manual_review_packet_preview_dry_run_result)
    ? tracePayload.manual_review_packet_preview_dry_run_result
    : {};
  const safety = hasAgentTraceSummaryObject(result.safety_metadata)
    ? result.safety_metadata
    : {};
  const agentRun = tracePayload?.agent_run && typeof tracePayload.agent_run === "object"
    ? tracePayload.agent_run
    : {};
  const metadata = agentRun?.metadata && typeof agentRun.metadata === "object" ? agentRun.metadata : {};
  const contextId = tracePayload?.agent_run_id || agentRun.agent_run_id || "";
  const jobId = metadata.job_id || metadata.merge_key || "";
  return `
    <article class="agent-trace-summary" aria-label="Manual review packet preview dry-run">
      <div class="agentic-workflow-header">
        <div>
          <h4>Manual Review Packet Preview Dry-run</h4>
          <p>Human-readable packet preview only. It creates no approval request, mutates no queue or resume content, and never executes or submits applications.</p>
        </div>
        <span class="agentic-workflow-badge">Packet preview</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Packet", result.review_packet_status || "not run")}
        ${renderWorkflowSummaryMetric("Action", result.source_planned_action || "-")}
        ${renderWorkflowSummaryMetric("Confirmation", result.required_human_confirmation === true ? "required" : "-")}
        ${renderWorkflowSummaryMetric("Approval created", safety.did_create_approval ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Queue mutation", safety.did_mutate_queue ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Execution", safety.did_execute_application ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Submission", safety.did_submit_application ? "yes" : "no")}
      </div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Packet title", result.packet_title || "", { helper: "Preview-only review packet title." })}
        ${renderAgentTraceReadOnlyDetails("Packet sections", result.packet_sections || [], { helper: "Preview-only packet sections." })}
        ${renderAgentTraceReadOnlyDetails("Reviewer checklist", result.reviewer_checklist || [], { helper: "Preview-only reviewer checklist." })}
        ${renderAgentTraceReadOnlyDetails("Included stage summaries", result.included_stage_summaries || {}, { helper: "Preview-only stage summaries." })}
        ${renderAgentTraceReadOnlyDetails("Blocked actions", result.blocked_actions || [], { helper: "Preview-only blocked actions." })}
        ${renderAgentTraceReadOnlyDetails("Next safe step", result.next_safe_step || "", { helper: "Preview-only next safe step." })}
        ${renderAgentTraceReadOnlyDetails("Rationale", result.rationale || "", { helper: "Review packet preview rationale." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable review packet preview safety metadata." })}
      </div>
      <div class="agentic-review-actions">
        <button type="button" class="agentic-feedback-action" data-manual-review-packet-preview-dry-run data-context-id="${escapeHtml(contextId)}" data-job-id="${escapeHtml(jobId)}">
          Build Review Packet Preview
        </button>
        <span class="agentic-review-muted" data-manual-review-packet-preview-dry-run-status>
          Manual only. This previews a review packet and does not mutate approval, queue, resume, execution, or submission state.
        </span>
      </div>
    </article>
  `;
}

function renderManualApprovalRequestPreviewDryRunSection(tracePayload = {}) {
  const result = hasAgentTraceSummaryObject(tracePayload?.manual_approval_request_preview_dry_run_result)
    ? tracePayload.manual_approval_request_preview_dry_run_result
    : {};
  const safety = hasAgentTraceSummaryObject(result.safety_metadata)
    ? result.safety_metadata
    : {};
  const agentRun = tracePayload?.agent_run && typeof tracePayload.agent_run === "object"
    ? tracePayload.agent_run
    : {};
  const metadata = agentRun?.metadata && typeof agentRun.metadata === "object" ? agentRun.metadata : {};
  const contextId = tracePayload?.agent_run_id || agentRun.agent_run_id || "";
  const jobId = metadata.job_id || metadata.merge_key || "";
  return `
    <article class="agent-trace-summary" aria-label="Manual approval request preview dry-run">
      <div class="agentic-workflow-header">
        <div>
          <h4>Manual Approval Request Preview Dry-run</h4>
          <p>Approval request preview only. It creates no approval request, mutates no approval or queue state, and never executes or submits applications.</p>
        </div>
        <span class="agentic-workflow-badge">Approval preview</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Preview", result.approval_preview_status || "not run")}
        ${renderWorkflowSummaryMetric("Type", result.approval_preview_type || "-")}
        ${renderWorkflowSummaryMetric("Confirmation", result.required_reviewer_confirmation === true ? "required" : "-")}
        ${renderWorkflowSummaryMetric("Approval created", safety.did_create_approval ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Approval mutation", safety.did_mutate_approval ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Queue mutation", safety.did_mutate_queue ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Execution", safety.did_execute_application ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Submission", safety.did_submit_application ? "yes" : "no")}
      </div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Approval title", result.approval_title || "", { helper: "Preview-only approval title." })}
        ${renderAgentTraceReadOnlyDetails("Approval summary", result.approval_summary || "", { helper: "Preview-only approval summary." })}
        ${renderAgentTraceReadOnlyDetails("Proposed decision", result.proposed_decision || "", { helper: "Preview-only proposed decision." })}
        ${renderAgentTraceReadOnlyDetails("Proposed next step", result.proposed_next_step || "", { helper: "Preview-only proposed next step." })}
        ${renderAgentTraceReadOnlyDetails("Approval fields preview", result.approval_fields_preview || {}, { helper: "Preview-only approval fields." })}
        ${renderAgentTraceReadOnlyDetails("Blocked actions", result.blocked_actions || [], { helper: "Preview-only blocked actions." })}
        ${renderAgentTraceReadOnlyDetails("Source review packet status", result.source_review_packet_status || "", { helper: "Source review packet preview status." })}
        ${renderAgentTraceReadOnlyDetails("Rationale", result.rationale || "", { helper: "Approval request preview rationale." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable approval request preview safety metadata." })}
      </div>
      <div class="agentic-review-actions">
        <button type="button" class="agentic-feedback-action" data-manual-approval-request-preview-dry-run data-context-id="${escapeHtml(contextId)}" data-job-id="${escapeHtml(jobId)}">
          Preview Approval Request
        </button>
        <span class="agentic-review-muted" data-manual-approval-request-preview-dry-run-status>
          Manual only. This previews approval fields and does not create or mutate approval, queue, resume, execution, or submission state.
        </span>
      </div>
    </article>
  `;
}

function renderManualApprovalCreationGateDryRunSection(tracePayload = {}) {
  const result = hasAgentTraceSummaryObject(tracePayload?.manual_approval_creation_gate_dry_run_result)
    ? tracePayload.manual_approval_creation_gate_dry_run_result
    : {};
  const safety = hasAgentTraceSummaryObject(result.safety_metadata)
    ? result.safety_metadata
    : {};
  const agentRun = tracePayload?.agent_run && typeof tracePayload.agent_run === "object"
    ? tracePayload.agent_run
    : {};
  const metadata = agentRun?.metadata && typeof agentRun.metadata === "object" ? agentRun.metadata : {};
  const contextId = tracePayload?.agent_run_id || agentRun.agent_run_id || "";
  const jobId = metadata.job_id || metadata.merge_key || "";
  return `
    <article class="agent-trace-summary" aria-label="Manual approval creation gate dry-run">
      <div class="agentic-workflow-header">
        <div>
          <h4>Manual Approval Creation Gate Dry-run</h4>
          <p>Readiness check only. It creates no approval request, mutates no approval or queue state, and never executes or submits applications.</p>
        </div>
        <span class="agentic-workflow-badge">Creation gate</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Gate", result.approval_creation_gate_status || "not run")}
        ${renderWorkflowSummaryMetric("Decision", result.gate_decision || "-")}
        ${renderWorkflowSummaryMetric("Can create later", result.can_create_approval_request_later === true ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Approval created", safety.did_create_approval ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Approval mutation", safety.did_mutate_approval ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Queue mutation", safety.did_mutate_queue ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Execution", safety.did_execute_application ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Submission", safety.did_submit_application ? "yes" : "no")}
      </div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Missing requirements", result.missing_requirements || [], { helper: "Preview-only missing requirements." })}
        ${renderAgentTraceReadOnlyDetails("Blocked actions", result.blocked_actions || [], { helper: "Preview-only blocked actions." })}
        ${renderAgentTraceReadOnlyDetails("Source approval preview status", result.source_approval_preview_status || "", { helper: "Source approval preview status." })}
        ${renderAgentTraceReadOnlyDetails("Next safe step", result.next_safe_step || "", { helper: "Preview-only next safe step." })}
        ${renderAgentTraceReadOnlyDetails("Rationale", result.rationale || "", { helper: "Approval creation gate rationale." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable approval creation gate safety metadata." })}
      </div>
      <div class="agentic-review-actions">
        <label class="agentic-review-muted">
          <input type="checkbox" data-manual-approval-creation-gate-confirmation>
          Reviewer confirmation
        </label>
        <button type="button" class="agentic-feedback-action" data-manual-approval-creation-gate-dry-run data-context-id="${escapeHtml(contextId)}" data-job-id="${escapeHtml(jobId)}">
          Check Approval Creation Gate
        </button>
        <span class="agentic-review-muted" data-manual-approval-creation-gate-dry-run-status>
          Manual only. This checks future readiness and does not create or mutate approval, queue, resume, execution, or submission state.
        </span>
      </div>
    </article>
  `;
}

function renderManualGuardedApprovalRequestCreateSection(tracePayload = {}) {
  const result = hasAgentTraceSummaryObject(tracePayload?.manual_guarded_approval_request_create_result)
    ? tracePayload.manual_guarded_approval_request_create_result
    : {};
  const safety = hasAgentTraceSummaryObject(result.safety_metadata)
    ? result.safety_metadata
    : {};
  const agentRun = tracePayload?.agent_run && typeof tracePayload.agent_run === "object"
    ? tracePayload.agent_run
    : {};
  const metadata = agentRun?.metadata && typeof agentRun.metadata === "object" ? agentRun.metadata : {};
  const contextId = tracePayload?.agent_run_id || agentRun.agent_run_id || "";
  const jobId = metadata.job_id || metadata.merge_key || "";
  return `
    <article class="agent-trace-summary" aria-label="Manual guarded approval request creation">
      <div class="agentic-workflow-header">
        <div>
          <h4>Manual Guarded Approval Request Creation</h4>
          <p>Manual-only creation of one approval request record after the gate is ready. It does not mutate queue or resume content, execute, submit, score, rank, or auto-apply.</p>
        </div>
        <span class="agentic-workflow-badge">Manual create</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Creation", result.approval_creation_status || "not run")}
        ${renderWorkflowSummaryMetric("Gate", result.gate_decision || "-")}
        ${renderWorkflowSummaryMetric("Created id", result.created_approval_request_id || "-")}
        ${renderWorkflowSummaryMetric("Approval created", safety.did_create_approval ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Queue mutation", safety.did_mutate_queue ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Execution", safety.did_execute_application ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Submission", safety.did_submit_application ? "yes" : "no")}
      </div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Created approval request id", result.created_approval_request_id || "", { helper: "Created approval request identifier when the guarded manual path succeeds." })}
        ${renderAgentTraceReadOnlyDetails("Approval request preview", result.approval_request_preview || {}, { helper: "Source approval preview used for guarded creation." })}
        ${renderAgentTraceReadOnlyDetails("Source approval preview status", result.source_approval_preview_status || "", { helper: "Source approval preview status." })}
        ${renderAgentTraceReadOnlyDetails("Blocked actions", result.blocked_actions || [], { helper: "Creation blockers." })}
        ${renderAgentTraceReadOnlyDetails("Next safe step", result.next_safe_step || "", { helper: "Next safe manual step." })}
        ${renderAgentTraceReadOnlyDetails("Rationale", result.rationale || "", { helper: "Guarded creation rationale." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable guarded approval creation safety metadata." })}
      </div>
      <div class="agentic-review-actions">
        <label class="agentic-review-muted">
          <input type="checkbox" data-manual-guarded-approval-request-create-confirmation>
          Explicitly create approval request
        </label>
        <button type="button" class="agentic-feedback-action" data-manual-guarded-approval-request-create data-context-id="${escapeHtml(contextId)}" data-job-id="${escapeHtml(jobId)}">
          Create Guarded Approval Request
        </button>
        <span class="agentic-review-muted" data-manual-guarded-approval-request-create-status>
          Manual only. Requires a ready gate plus explicit confirmation and creates no queue, resume, execution, or submission state.
        </span>
      </div>
    </article>
  `;
}

function renderManualGuardedApprovalCreationObservabilitySection(tracePayload = {}) {
  const result = hasAgentTraceSummaryObject(tracePayload?.manual_guarded_approval_creation_observability_result)
    ? tracePayload.manual_guarded_approval_creation_observability_result
    : {};
  const safety = hasAgentTraceSummaryObject(result.safety_metadata)
    ? result.safety_metadata
    : {};
  const agentRun = tracePayload?.agent_run && typeof tracePayload.agent_run === "object"
    ? tracePayload.agent_run
    : {};
  const metadata = agentRun?.metadata && typeof agentRun.metadata === "object" ? agentRun.metadata : {};
  const contextId = tracePayload?.agent_run_id || agentRun.agent_run_id || "";
  const jobId = metadata.job_id || metadata.merge_key || "";
  return `
    <article class="agent-trace-summary" aria-label="Manual guarded approval creation observability">
      <div class="agentic-workflow-header">
        <div>
          <h4>Manual Guarded Approval Creation Audit</h4>
          <p>Read-only audit trace for the guarded approval creation result. It creates no approval request, mutates no queue or approval state, and never executes or submits applications.</p>
        </div>
        <span class="agentic-workflow-badge">Audit trace</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Audit", result.observability_status || "not run")}
        ${renderWorkflowSummaryMetric("Source", result.source_approval_creation_status || "-")}
        ${renderWorkflowSummaryMetric("Created id", result.created_approval_request_id || "-")}
        ${renderWorkflowSummaryMetric("Blocked", result.creation_was_blocked === true ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Successful", result.creation_was_successful === true ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Approval created", safety.did_create_approval ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Queue mutation", safety.did_mutate_queue ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Execution", safety.did_execute_application ? "yes" : "no")}
      </div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Gate decision", result.gate_decision || "", { helper: "Source guarded creation gate decision." })}
        ${renderAgentTraceReadOnlyDetails("Audit summary", result.audit_summary || {}, { helper: "Read-only creation audit summary." })}
        ${renderAgentTraceReadOnlyDetails("Audit events", result.audit_events || [], { helper: "Read-only audit events surfaced from the source payload when present." })}
        ${renderAgentTraceReadOnlyDetails("Safety findings", result.safety_findings || {}, { helper: "Read-only observability safety findings." })}
        ${renderAgentTraceReadOnlyDetails("Blocked actions", result.blocked_actions || [], { helper: "Observed blockers." })}
        ${renderAgentTraceReadOnlyDetails("Next safe step", result.next_safe_step || "", { helper: "Next safe manual step." })}
        ${renderAgentTraceReadOnlyDetails("Operator review notes", result.operator_review_notes || "", { helper: "Read-only operator review notes." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable guarded approval creation observability safety metadata." })}
      </div>
      <div class="agentic-review-actions">
        <button type="button" class="agentic-feedback-action" data-manual-guarded-approval-creation-observability data-context-id="${escapeHtml(contextId)}" data-job-id="${escapeHtml(jobId)}">
          View Approval Creation Audit
        </button>
        <span class="agentic-review-muted" data-manual-guarded-approval-creation-observability-status>
          Manual only. This summarizes the guarded creation result and performs no approval, queue, resume, execution, or submission mutation.
        </span>
      </div>
    </article>
  `;
}

function renderManualApprovalRequestReadbackSection(tracePayload = {}) {
  const result = hasAgentTraceSummaryObject(tracePayload?.manual_approval_request_readback_result)
    ? tracePayload.manual_approval_request_readback_result
    : {};
  const safety = hasAgentTraceSummaryObject(result.safety_metadata)
    ? result.safety_metadata
    : {};
  const creation = hasAgentTraceSummaryObject(tracePayload?.manual_guarded_approval_request_create_result)
    ? tracePayload.manual_guarded_approval_request_create_result
    : {};
  const observability = hasAgentTraceSummaryObject(tracePayload?.manual_guarded_approval_creation_observability_result)
    ? tracePayload.manual_guarded_approval_creation_observability_result
    : {};
  const agentRun = tracePayload?.agent_run && typeof tracePayload.agent_run === "object"
    ? tracePayload.agent_run
    : {};
  const metadata = agentRun?.metadata && typeof agentRun.metadata === "object" ? agentRun.metadata : {};
  const contextId = tracePayload?.agent_run_id || agentRun.agent_run_id || "";
  const jobId = metadata.job_id || metadata.merge_key || "";
  const approvalRequestId = result.approval_request_id || creation.created_approval_request_id || observability.created_approval_request_id || "";
  return `
    <article class="agent-trace-summary" aria-label="Manual approval request readback">
      <div class="agentic-workflow-header">
        <div>
          <h4>Manual Approval Request Readback</h4>
          <p>Read-only approval request detail. It does not approve, reject, update, queue, execute, submit, or edit anything.</p>
        </div>
        <span class="agentic-workflow-badge">Readback</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Readback", result.readback_status || "not run")}
        ${renderWorkflowSummaryMetric("Approval found", result.approval_request_found === true ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Request id", approvalRequestId || "-")}
        ${renderWorkflowSummaryMetric("Approval created", safety.did_create_approval ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Approval mutation", safety.did_mutate_approval ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Queue mutation", safety.did_mutate_queue ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Execution", safety.did_execute_application ? "yes" : "no")}
      </div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Approval request summary", result.approval_request_summary || {}, { helper: "Read-only approval request summary." })}
        ${renderAgentTraceReadOnlyDetails("Approval request fields", result.approval_request_fields || {}, { helper: "Read-only approval request fields." })}
        ${renderAgentTraceReadOnlyDetails("Source creation status", result.source_creation_status || "", { helper: "Source guarded creation status." })}
        ${renderAgentTraceReadOnlyDetails("Source observability status", result.source_observability_status || "", { helper: "Source observability status." })}
        ${renderAgentTraceReadOnlyDetails("Blocked actions", result.blocked_actions || [], { helper: "Readback blockers." })}
        ${renderAgentTraceReadOnlyDetails("Next safe step", result.next_safe_step || "", { helper: "Next safe manual step." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable approval request readback safety metadata." })}
      </div>
      <div class="agentic-review-actions">
        <button type="button" class="agentic-feedback-action" data-manual-approval-request-readback data-approval-request-id="${escapeHtml(approvalRequestId)}" data-context-id="${escapeHtml(contextId)}" data-job-id="${escapeHtml(jobId)}">
          Read Approval Request
        </button>
        <span class="agentic-review-muted" data-manual-approval-request-readback-status>
          Manual only. This reads approval request details and does not mutate approval, queue, resume, execution, or submission state.
        </span>
      </div>
    </article>
  `;
}

function renderManualApprovalStatusTransitionPreviewSection(tracePayload = {}) {
  const result = hasAgentTraceSummaryObject(tracePayload?.manual_approval_status_transition_preview_result)
    ? tracePayload.manual_approval_status_transition_preview_result
    : {};
  const safety = hasAgentTraceSummaryObject(result.safety_metadata)
    ? result.safety_metadata
    : {};
  const readback = hasAgentTraceSummaryObject(tracePayload?.manual_approval_request_readback_result)
    ? tracePayload.manual_approval_request_readback_result
    : {};
  const creation = hasAgentTraceSummaryObject(tracePayload?.manual_guarded_approval_request_create_result)
    ? tracePayload.manual_guarded_approval_request_create_result
    : {};
  const observability = hasAgentTraceSummaryObject(tracePayload?.manual_guarded_approval_creation_observability_result)
    ? tracePayload.manual_guarded_approval_creation_observability_result
    : {};
  const agentRun = tracePayload?.agent_run && typeof tracePayload.agent_run === "object"
    ? tracePayload.agent_run
    : {};
  const metadata = agentRun?.metadata && typeof agentRun.metadata === "object" ? agentRun.metadata : {};
  const contextId = tracePayload?.agent_run_id || agentRun.agent_run_id || "";
  const jobId = metadata.job_id || metadata.merge_key || "";
  const approvalRequestId = result.approval_request_id || readback.approval_request_id || creation.created_approval_request_id || observability.created_approval_request_id || "";
  const options = ["approve", "reject", "needs_changes"];
  return `
    <article class="agent-trace-summary" aria-label="Manual approval status transition preview">
      <div class="agentic-workflow-header">
        <div>
          <h4>Manual Approval Status Transition Preview</h4>
          <p>Dry-run transition preview only. It does not approve, reject, update approval status, queue, execute, submit, or edit anything.</p>
        </div>
        <span class="agentic-workflow-badge">Transition preview</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Preview", result.transition_preview_status || "not run")}
        ${renderWorkflowSummaryMetric("Transition", result.proposed_transition || "-")}
        ${renderWorkflowSummaryMetric("Would change to", result.would_change_status_to || "-")}
        ${renderWorkflowSummaryMetric("Allowed later", result.transition_allowed_later === true ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Status updated", safety.did_update_approval_status ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Queue mutation", safety.did_mutate_queue ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Execution", safety.did_execute_application ? "yes" : "no")}
      </div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Transition label", result.transition_label || "", { helper: "Preview-only transition label." })}
        ${renderAgentTraceReadOnlyDetails("Transition summary", result.transition_summary || "", { helper: "Preview-only transition summary." })}
        ${renderAgentTraceReadOnlyDetails("Blocked actions", result.blocked_actions || [], { helper: "Transition preview blockers." })}
        ${renderAgentTraceReadOnlyDetails("Missing requirements", result.missing_requirements || [], { helper: "Transition preview missing requirements." })}
        ${renderAgentTraceReadOnlyDetails("Source readback status", result.source_readback_status || "", { helper: "Source approval request readback status." })}
        ${renderAgentTraceReadOnlyDetails("Next safe step", result.next_safe_step || "", { helper: "Next safe manual step." })}
        ${renderAgentTraceReadOnlyDetails("Rationale", result.rationale || "", { helper: "Transition preview rationale." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable approval transition preview safety metadata." })}
      </div>
      <div class="agentic-review-actions">
        <select class="agentic-feedback-action" data-manual-approval-status-transition-preview-select aria-label="Approval status transition preview">
          ${options.map((option) => `<option value="${escapeHtml(option)}">${escapeHtml(option)}</option>`).join("")}
        </select>
        <button type="button" class="agentic-feedback-action" data-manual-approval-status-transition-preview data-approval-request-id="${escapeHtml(approvalRequestId)}" data-context-id="${escapeHtml(contextId)}" data-job-id="${escapeHtml(jobId)}">
          Preview Approval Status Transition
        </button>
        <span class="agentic-review-muted" data-manual-approval-status-transition-preview-status>
          Manual only. This previews a future transition and does not update approval state.
        </span>
      </div>
    </article>
  `;
}

function renderManualGuardedApprovalStatusTransitionSection(tracePayload = {}) {
  const result = hasAgentTraceSummaryObject(tracePayload?.manual_guarded_approval_status_transition_result)
    ? tracePayload.manual_guarded_approval_status_transition_result
    : {};
  const safety = hasAgentTraceSummaryObject(result.safety_metadata)
    ? result.safety_metadata
    : {};
  const preview = hasAgentTraceSummaryObject(tracePayload?.manual_approval_status_transition_preview_result)
    ? tracePayload.manual_approval_status_transition_preview_result
    : {};
  const readback = hasAgentTraceSummaryObject(tracePayload?.manual_approval_request_readback_result)
    ? tracePayload.manual_approval_request_readback_result
    : {};
  const creation = hasAgentTraceSummaryObject(tracePayload?.manual_guarded_approval_request_create_result)
    ? tracePayload.manual_guarded_approval_request_create_result
    : {};
  const observability = hasAgentTraceSummaryObject(tracePayload?.manual_guarded_approval_creation_observability_result)
    ? tracePayload.manual_guarded_approval_creation_observability_result
    : {};
  const agentRun = tracePayload?.agent_run && typeof tracePayload.agent_run === "object"
    ? tracePayload.agent_run
    : {};
  const metadata = agentRun?.metadata && typeof agentRun.metadata === "object" ? agentRun.metadata : {};
  const contextId = tracePayload?.agent_run_id || agentRun.agent_run_id || "";
  const jobId = metadata.job_id || metadata.merge_key || "";
  const approvalRequestId = result.approval_request_id || preview.approval_request_id || readback.approval_request_id || creation.created_approval_request_id || observability.created_approval_request_id || "";
  const proposedTransition = result.proposed_transition || preview.proposed_transition || "approve";
  return `
    <article class="agent-trace-summary" aria-label="Manual guarded approval status transition">
      <div class="agentic-workflow-header">
        <div>
          <h4>Manual Guarded Approval Status Transition</h4>
          <p>Manual guarded status update only. It requires a ready preview and explicit confirmation, and does not mutate queue, resume, scoring, ranking, execution, or submission state.</p>
        </div>
        <span class="agentic-workflow-badge">Guarded transition</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Transition status", result.approval_status_transition_status || "not run")}
        ${renderWorkflowSummaryMetric("Request id", approvalRequestId || "-")}
        ${renderWorkflowSummaryMetric("Proposed", proposedTransition || "-")}
        ${renderWorkflowSummaryMetric("Applied", result.transition_applied === true ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Previous status", result.previous_status || "-")}
        ${renderWorkflowSummaryMetric("New status", result.new_status || "-")}
        ${renderWorkflowSummaryMetric("Queue mutation", safety.did_mutate_queue ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Execution", safety.did_execute_application ? "yes" : "no")}
      </div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Applied transition", result.applied_transition || "", { helper: "Applied manual transition, when confirmation and preview permit it." })}
        ${renderAgentTraceReadOnlyDetails("Blocked actions", result.blocked_actions || [], { helper: "Guarded transition blockers." })}
        ${renderAgentTraceReadOnlyDetails("Source transition preview status", result.source_transition_preview_status || "", { helper: "Source transition preview status." })}
        ${renderAgentTraceReadOnlyDetails("Next safe step", result.next_safe_step || "", { helper: "Next safe manual step." })}
        ${renderAgentTraceReadOnlyDetails("Rationale", result.rationale || "", { helper: "Guarded transition rationale." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable guarded approval status transition safety metadata." })}
      </div>
      <div class="agentic-review-actions">
        <label class="agentic-review-muted">
          <input type="checkbox" data-manual-guarded-approval-status-transition-confirmation>
          I explicitly confirm this guarded approval status transition.
        </label>
        <button type="button" class="agentic-feedback-action" data-manual-guarded-approval-status-transition data-approval-request-id="${escapeHtml(approvalRequestId)}" data-proposed-transition="${escapeHtml(proposedTransition)}" data-context-id="${escapeHtml(contextId)}" data-job-id="${escapeHtml(jobId)}">
          Apply Guarded Status Transition
        </button>
        <span class="agentic-review-muted" data-manual-guarded-approval-status-transition-status>
          Manual only. This requires explicit confirmation and does not mutate queue, resume, execution, or submission state.
        </span>
      </div>
    </article>
  `;
}

function renderManualApprovalStatusTransitionObservabilitySection(tracePayload = {}) {
  const result = hasAgentTraceSummaryObject(tracePayload?.manual_approval_status_transition_observability_result)
    ? tracePayload.manual_approval_status_transition_observability_result
    : {};
  const safety = hasAgentTraceSummaryObject(result.safety_metadata)
    ? result.safety_metadata
    : {};
  const transition = hasAgentTraceSummaryObject(tracePayload?.manual_guarded_approval_status_transition_result)
    ? tracePayload.manual_guarded_approval_status_transition_result
    : {};
  const agentRun = tracePayload?.agent_run && typeof tracePayload.agent_run === "object"
    ? tracePayload.agent_run
    : {};
  const metadata = agentRun?.metadata && typeof agentRun.metadata === "object" ? agentRun.metadata : {};
  const contextId = tracePayload?.agent_run_id || agentRun.agent_run_id || "";
  const jobId = metadata.job_id || metadata.merge_key || "";
  const approvalRequestId = result.approval_request_id || transition.approval_request_id || "";
  const proposedTransition = result.proposed_transition || transition.proposed_transition || "";
  return `
    <article class="agent-trace-summary" aria-label="Manual approval status transition observability">
      <div class="agentic-workflow-header">
        <div>
          <h4>Manual Approval Status Transition Audit</h4>
          <p>Read-only audit trace for the guarded status transition result. It does not update approval status, mutate queues or resumes, execute, or submit applications.</p>
        </div>
        <span class="agentic-workflow-badge">Transition audit</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Audit", result.transition_observability_status || "not run")}
        ${renderWorkflowSummaryMetric("Source", result.source_transition_status || "-")}
        ${renderWorkflowSummaryMetric("Request id", approvalRequestId || "-")}
        ${renderWorkflowSummaryMetric("Applied", result.transition_was_applied === true ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Blocked", result.transition_was_blocked === true ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Previous status", result.previous_status || "-")}
        ${renderWorkflowSummaryMetric("New status", result.new_status || "-")}
        ${renderWorkflowSummaryMetric("Status updated", safety.did_update_approval_status ? "yes" : "no")}
      </div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Proposed transition", proposedTransition || "", { helper: "Observed proposed transition." })}
        ${renderAgentTraceReadOnlyDetails("Applied transition", result.applied_transition || "", { helper: "Observed applied transition, if any." })}
        ${renderAgentTraceReadOnlyDetails("Audit summary", result.audit_summary || {}, { helper: "Read-only transition audit summary." })}
        ${renderAgentTraceReadOnlyDetails("Audit events", result.audit_events || [], { helper: "Read-only transition audit events synthesized from the provided source payload." })}
        ${renderAgentTraceReadOnlyDetails("Safety findings", result.safety_findings || {}, { helper: "Read-only transition observability safety findings." })}
        ${renderAgentTraceReadOnlyDetails("Blocked actions", result.blocked_actions || [], { helper: "Observed transition blockers." })}
        ${renderAgentTraceReadOnlyDetails("Next safe step", result.next_safe_step || "", { helper: "Next safe manual step." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable approval transition observability safety metadata." })}
      </div>
      <div class="agentic-review-actions">
        <button type="button" class="agentic-feedback-action" data-manual-approval-status-transition-observability data-approval-request-id="${escapeHtml(approvalRequestId)}" data-proposed-transition="${escapeHtml(proposedTransition)}" data-context-id="${escapeHtml(contextId)}" data-job-id="${escapeHtml(jobId)}">
          View Status Transition Audit
        </button>
        <span class="agentic-review-muted" data-manual-approval-status-transition-observability-status>
          Manual only. This summarizes the guarded transition result and performs no approval, queue, resume, execution, or submission mutation.
        </span>
      </div>
    </article>
  `;
}

function renderManualQueueHandoffReadinessPreviewSection(tracePayload = {}) {
  const result = hasAgentTraceSummaryObject(tracePayload?.manual_queue_handoff_readiness_preview_result)
    ? tracePayload.manual_queue_handoff_readiness_preview_result
    : {};
  const safety = hasAgentTraceSummaryObject(result.safety_metadata)
    ? result.safety_metadata
    : {};
  const readback = hasAgentTraceSummaryObject(tracePayload?.manual_approval_request_readback_result)
    ? tracePayload.manual_approval_request_readback_result
    : {};
  const transitionAudit = hasAgentTraceSummaryObject(tracePayload?.manual_approval_status_transition_observability_result)
    ? tracePayload.manual_approval_status_transition_observability_result
    : {};
  const transition = hasAgentTraceSummaryObject(tracePayload?.manual_guarded_approval_status_transition_result)
    ? tracePayload.manual_guarded_approval_status_transition_result
    : {};
  const agentRun = tracePayload?.agent_run && typeof tracePayload.agent_run === "object"
    ? tracePayload.agent_run
    : {};
  const metadata = agentRun?.metadata && typeof agentRun.metadata === "object" ? agentRun.metadata : {};
  const contextId = tracePayload?.agent_run_id || agentRun.agent_run_id || "";
  const jobId = metadata.job_id || metadata.merge_key || "";
  const approvalRequestId = result.approval_request_id || readback.approval_request_id || transitionAudit.approval_request_id || transition.approval_request_id || "";
  return `
    <article class="agent-trace-summary" aria-label="Manual queue handoff readiness preview">
      <div class="agentic-workflow-header">
        <div>
          <h4>Manual Queue Handoff Readiness Preview</h4>
          <p>Dry-run readiness preview only. It does not create queue rows, write queue files, mutate approval or resume state, execute, or submit applications.</p>
        </div>
        <span class="agentic-workflow-badge">Queue preview</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Readiness", result.queue_handoff_readiness_status || "not run")}
        ${renderWorkflowSummaryMetric("Request id", approvalRequestId || "-")}
        ${renderWorkflowSummaryMetric("Approval status", result.approval_status || "-")}
        ${renderWorkflowSummaryMetric("Ready later", result.ready_for_future_queue_handoff === true ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Allowed later", result.queue_handoff_allowed_later === true ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Queue mutation", safety.did_mutate_queue ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Queue write", safety.did_write_queue ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Execution", safety.did_execute_application ? "yes" : "no")}
      </div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Missing requirements", result.missing_requirements || [], { helper: "Queue handoff readiness missing requirements." })}
        ${renderAgentTraceReadOnlyDetails("Blocked actions", result.blocked_actions || [], { helper: "Queue handoff readiness blockers." })}
        ${renderAgentTraceReadOnlyDetails("Source readback status", result.source_readback_status || "", { helper: "Source approval request readback status." })}
        ${renderAgentTraceReadOnlyDetails("Source transition observability status", result.source_transition_observability_status || "", { helper: "Source transition audit status." })}
        ${renderAgentTraceReadOnlyDetails("Next safe step", result.next_safe_step || "", { helper: "Next safe manual step." })}
        ${renderAgentTraceReadOnlyDetails("Rationale", result.rationale || "", { helper: "Queue handoff preview rationale." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable queue handoff preview safety metadata." })}
      </div>
      <div class="agentic-review-actions">
        <button type="button" class="agentic-feedback-action" data-manual-queue-handoff-readiness-preview data-approval-request-id="${escapeHtml(approvalRequestId)}" data-context-id="${escapeHtml(contextId)}" data-job-id="${escapeHtml(jobId)}">
          Preview Queue Handoff Readiness
        </button>
        <span class="agentic-review-muted" data-manual-queue-handoff-readiness-preview-status>
          Manual only. This previews queue handoff readiness and does not create or mutate queue, approval, resume, execution, or submission state.
        </span>
      </div>
    </article>
  `;
}

function renderManualGuardedQueueHandoffCreateSection(tracePayload = {}) {
  const result = hasAgentTraceSummaryObject(tracePayload?.manual_guarded_queue_handoff_create_result)
    ? tracePayload.manual_guarded_queue_handoff_create_result
    : {};
  const safety = hasAgentTraceSummaryObject(result.safety_metadata)
    ? result.safety_metadata
    : {};
  const readiness = hasAgentTraceSummaryObject(tracePayload?.manual_queue_handoff_readiness_preview_result)
    ? tracePayload.manual_queue_handoff_readiness_preview_result
    : {};
  const readback = hasAgentTraceSummaryObject(tracePayload?.manual_approval_request_readback_result)
    ? tracePayload.manual_approval_request_readback_result
    : {};
  const transitionAudit = hasAgentTraceSummaryObject(tracePayload?.manual_approval_status_transition_observability_result)
    ? tracePayload.manual_approval_status_transition_observability_result
    : {};
  const agentRun = tracePayload?.agent_run && typeof tracePayload.agent_run === "object"
    ? tracePayload.agent_run
    : {};
  const metadata = agentRun?.metadata && typeof agentRun.metadata === "object" ? agentRun.metadata : {};
  const contextId = tracePayload?.agent_run_id || agentRun.agent_run_id || "";
  const jobId = metadata.job_id || metadata.merge_key || "";
  const approvalRequestId = result.approval_request_id || readiness.approval_request_id || readback.approval_request_id || transitionAudit.approval_request_id || "";
  return `
    <article class="agent-trace-summary" aria-label="Manual guarded queue handoff creation">
      <div class="agentic-workflow-header">
        <div>
          <h4>Manual Guarded Queue Handoff Creation</h4>
          <p>Manual-only queue handoff creation after readiness preview and explicit confirmation. It never executes or submits applications and does not mutate approval status, resume content, scoring, or ranking.</p>
        </div>
        <span class="agentic-workflow-badge">Queue handoff</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Creation", result.queue_handoff_creation_status || "not run")}
        ${renderWorkflowSummaryMetric("Request id", approvalRequestId || "-")}
        ${renderWorkflowSummaryMetric("Handoff id", result.queue_handoff_id || "-")}
        ${renderWorkflowSummaryMetric("Queue entry", result.queue_entry_created === true ? "created" : "not created")}
        ${renderWorkflowSummaryMetric("Approval status", result.approval_status || readiness.approval_status || "-")}
        ${renderWorkflowSummaryMetric("Queue mutation", safety.did_mutate_queue ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Queue write", safety.did_write_queue ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Execution", safety.did_execute_application ? "yes" : "no")}
      </div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Source readiness status", result.source_queue_handoff_readiness_status || readiness.queue_handoff_readiness_status || "", { helper: "Source queue handoff readiness status." })}
        ${renderAgentTraceReadOnlyDetails("Blocked actions", result.blocked_actions || [], { helper: "Guarded queue handoff blockers." })}
        ${renderAgentTraceReadOnlyDetails("Next safe step", result.next_safe_step || "", { helper: "Next safe manual step." })}
        ${renderAgentTraceReadOnlyDetails("Rationale", result.rationale || "", { helper: "Guarded queue handoff rationale." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable guarded queue handoff safety metadata." })}
      </div>
      <div class="agentic-review-actions">
        <label class="agentic-review-muted">
          <input type="checkbox" data-manual-guarded-queue-handoff-create-confirmation>
          I explicitly confirm this guarded queue handoff.
        </label>
        <button type="button" class="agentic-feedback-action" data-manual-guarded-queue-handoff-create data-approval-request-id="${escapeHtml(approvalRequestId)}" data-context-id="${escapeHtml(contextId)}" data-job-id="${escapeHtml(jobId)}">
          Create Guarded Queue Handoff
        </button>
        <span class="agentic-review-muted" data-manual-guarded-queue-handoff-create-status>
          Manual only. This requires explicit confirmation and will block unless an existing queue writer is configured.
        </span>
      </div>
    </article>
  `;
}

function renderManualQueueHandoffCreationObservabilitySection(tracePayload = {}) {
  const result = hasAgentTraceSummaryObject(tracePayload?.manual_queue_handoff_creation_observability_result)
    ? tracePayload.manual_queue_handoff_creation_observability_result
    : {};
  const safety = hasAgentTraceSummaryObject(result.safety_metadata)
    ? result.safety_metadata
    : {};
  const creation = hasAgentTraceSummaryObject(tracePayload?.manual_guarded_queue_handoff_create_result)
    ? tracePayload.manual_guarded_queue_handoff_create_result
    : {};
  const agentRun = tracePayload?.agent_run && typeof tracePayload.agent_run === "object"
    ? tracePayload.agent_run
    : {};
  const metadata = agentRun?.metadata && typeof agentRun.metadata === "object" ? agentRun.metadata : {};
  const contextId = tracePayload?.agent_run_id || agentRun.agent_run_id || "";
  const jobId = metadata.job_id || metadata.merge_key || "";
  const approvalRequestId = result.approval_request_id || creation.approval_request_id || "";
  const queueHandoffId = result.queue_handoff_id || creation.queue_handoff_id || "";
  return `
    <article class="agent-trace-summary" aria-label="Manual queue handoff creation observability">
      <div class="agentic-workflow-header">
        <div>
          <h4>Manual Queue Handoff Audit</h4>
          <p>Read-only audit trace for the guarded queue handoff result. It creates no queue entries, writes no queue files, and never executes or submits applications.</p>
        </div>
        <span class="agentic-workflow-badge">Queue audit</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Audit", result.queue_handoff_observability_status || "not run")}
        ${renderWorkflowSummaryMetric("Source", result.source_queue_handoff_creation_status || "-")}
        ${renderWorkflowSummaryMetric("Request id", approvalRequestId || "-")}
        ${renderWorkflowSummaryMetric("Handoff id", queueHandoffId || "-")}
        ${renderWorkflowSummaryMetric("Created", result.queue_handoff_was_created === true ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Blocked", result.queue_handoff_was_blocked === true ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Queue mutation", safety.did_mutate_queue ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Queue write", safety.did_write_queue ? "yes" : "no")}
      </div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Audit summary", result.audit_summary || {}, { helper: "Read-only queue handoff audit summary." })}
        ${renderAgentTraceReadOnlyDetails("Audit events", result.audit_events || [], { helper: "Read-only queue handoff audit events synthesized from the provided source payload." })}
        ${renderAgentTraceReadOnlyDetails("Safety findings", result.safety_findings || {}, { helper: "Read-only queue handoff safety findings." })}
        ${renderAgentTraceReadOnlyDetails("Blocked actions", result.blocked_actions || [], { helper: "Observed queue handoff blockers." })}
        ${renderAgentTraceReadOnlyDetails("Next safe step", result.next_safe_step || "", { helper: "Next safe manual step." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable queue handoff audit safety metadata." })}
      </div>
      <div class="agentic-review-actions">
        <button type="button" class="agentic-feedback-action" data-manual-queue-handoff-creation-observability data-approval-request-id="${escapeHtml(approvalRequestId)}" data-queue-handoff-id="${escapeHtml(queueHandoffId)}" data-context-id="${escapeHtml(contextId)}" data-job-id="${escapeHtml(jobId)}">
          View Queue Handoff Audit
        </button>
        <span class="agentic-review-muted" data-manual-queue-handoff-creation-observability-status>
          Manual only. This summarizes the guarded queue handoff result and performs no queue, approval, resume, execution, or submission mutation.
        </span>
      </div>
    </article>
  `;
}

function renderManualExecutionReadinessPreviewSection(tracePayload = {}) {
  const result = hasAgentTraceSummaryObject(tracePayload?.manual_execution_readiness_preview_result)
    ? tracePayload.manual_execution_readiness_preview_result
    : {};
  const safety = hasAgentTraceSummaryObject(result.safety_metadata)
    ? result.safety_metadata
    : {};
  const queueAudit = hasAgentTraceSummaryObject(tracePayload?.manual_queue_handoff_creation_observability_result)
    ? tracePayload.manual_queue_handoff_creation_observability_result
    : {};
  const queueCreation = hasAgentTraceSummaryObject(tracePayload?.manual_guarded_queue_handoff_create_result)
    ? tracePayload.manual_guarded_queue_handoff_create_result
    : {};
  const agentRun = tracePayload?.agent_run && typeof tracePayload.agent_run === "object"
    ? tracePayload.agent_run
    : {};
  const metadata = agentRun?.metadata && typeof agentRun.metadata === "object" ? agentRun.metadata : {};
  const contextId = tracePayload?.agent_run_id || agentRun.agent_run_id || "";
  const jobId = metadata.job_id || metadata.merge_key || "";
  const approvalRequestId = result.approval_request_id || queueAudit.approval_request_id || queueCreation.approval_request_id || "";
  const queueHandoffId = result.queue_handoff_id || queueAudit.queue_handoff_id || queueCreation.queue_handoff_id || "";
  return `
    <article class="agent-trace-summary" aria-label="Manual execution readiness preview">
      <div class="agentic-workflow-header">
        <div>
          <h4>Manual Execution Readiness Preview</h4>
          <p>Dry-run readiness preview only. It does not execute, submit, mutate queues or approvals, write queue files, or change resume, scoring, or ranking state.</p>
        </div>
        <span class="agentic-workflow-badge">Execution preview</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Readiness", result.execution_readiness_status || "not run")}
        ${renderWorkflowSummaryMetric("Request id", approvalRequestId || "-")}
        ${renderWorkflowSummaryMetric("Handoff id", queueHandoffId || "-")}
        ${renderWorkflowSummaryMetric("Ready later", result.ready_for_future_execution === true ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Allowed later", result.execution_allowed_later === true ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Execution", safety.did_execute_application ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Submission", safety.did_submit_application ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Queue mutation", safety.did_mutate_queue ? "yes" : "no")}
      </div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Missing requirements", result.missing_requirements || [], { helper: "Execution readiness missing requirements." })}
        ${renderAgentTraceReadOnlyDetails("Blocked actions", result.blocked_actions || [], { helper: "Execution readiness blockers." })}
        ${renderAgentTraceReadOnlyDetails("Source queue handoff observability status", result.source_queue_handoff_observability_status || "", { helper: "Source queue handoff audit status." })}
        ${renderAgentTraceReadOnlyDetails("Next safe step", result.next_safe_step || "", { helper: "Next safe manual step." })}
        ${renderAgentTraceReadOnlyDetails("Rationale", result.rationale || "", { helper: "Execution readiness preview rationale." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable execution readiness preview safety metadata." })}
      </div>
      <div class="agentic-review-actions">
        <button type="button" class="agentic-feedback-action" data-manual-execution-readiness-preview data-approval-request-id="${escapeHtml(approvalRequestId)}" data-queue-handoff-id="${escapeHtml(queueHandoffId)}" data-context-id="${escapeHtml(contextId)}" data-job-id="${escapeHtml(jobId)}">
          Preview Execution Readiness
        </button>
        <span class="agentic-review-muted" data-manual-execution-readiness-preview-status>
          Manual only. This previews future execution readiness and does not execute, submit, or mutate queue state.
        </span>
      </div>
    </article>
  `;
}

function renderManualExecutionLaunchGatePreviewSection(tracePayload = {}) {
  const result = hasAgentTraceSummaryObject(tracePayload?.manual_execution_launch_gate_preview_result)
    ? tracePayload.manual_execution_launch_gate_preview_result
    : {};
  const safety = hasAgentTraceSummaryObject(result.safety_metadata)
    ? result.safety_metadata
    : {};
  const executionReadiness = hasAgentTraceSummaryObject(tracePayload?.manual_execution_readiness_preview_result)
    ? tracePayload.manual_execution_readiness_preview_result
    : {};
  const queueAudit = hasAgentTraceSummaryObject(tracePayload?.manual_queue_handoff_creation_observability_result)
    ? tracePayload.manual_queue_handoff_creation_observability_result
    : {};
  const agentRun = tracePayload?.agent_run && typeof tracePayload.agent_run === "object"
    ? tracePayload.agent_run
    : {};
  const metadata = agentRun?.metadata && typeof agentRun.metadata === "object" ? agentRun.metadata : {};
  const contextId = tracePayload?.agent_run_id || agentRun.agent_run_id || "";
  const jobId = metadata.job_id || metadata.merge_key || "";
  const approvalRequestId = result.approval_request_id || executionReadiness.approval_request_id || queueAudit.approval_request_id || "";
  const queueHandoffId = result.queue_handoff_id || executionReadiness.queue_handoff_id || queueAudit.queue_handoff_id || "";
  return `
    <article class="agent-trace-summary" aria-label="Manual execution launch gate preview">
      <div class="agentic-workflow-header">
        <div>
          <h4>Manual Execution Launch Gate Preview</h4>
          <p>Dry-run gate preview only. It does not execute, submit, mutate queues or approvals, write queue files, or change resume, scoring, or ranking state.</p>
        </div>
        <span class="agentic-workflow-badge">Launch gate</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Gate", result.execution_launch_gate_status || "not run")}
        ${renderWorkflowSummaryMetric("Request id", approvalRequestId || "-")}
        ${renderWorkflowSummaryMetric("Handoff id", queueHandoffId || "-")}
        ${renderWorkflowSummaryMetric("Allowed later", result.execution_launch_allowed_later === true ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Ready later", result.ready_for_future_manual_execution === true ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Execution", safety.did_execute_application ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Submission", safety.did_submit_application ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Queue mutation", safety.did_mutate_queue ? "yes" : "no")}
      </div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Missing requirements", result.missing_requirements || [], { helper: "Execution launch gate missing requirements." })}
        ${renderAgentTraceReadOnlyDetails("Blocked actions", result.blocked_actions || [], { helper: "Execution launch gate blockers." })}
        ${renderAgentTraceReadOnlyDetails("Source execution readiness status", result.source_execution_readiness_status || "", { helper: "Source execution readiness status." })}
        ${renderAgentTraceReadOnlyDetails("Source queue handoff observability status", result.source_queue_handoff_observability_status || "", { helper: "Source queue handoff audit status." })}
        ${renderAgentTraceReadOnlyDetails("Next safe step", result.next_safe_step || "", { helper: "Next safe manual step." })}
        ${renderAgentTraceReadOnlyDetails("Rationale", result.rationale || "", { helper: "Execution launch gate preview rationale." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable execution launch gate safety metadata." })}
      </div>
      <div class="agentic-review-actions">
        <button type="button" class="agentic-feedback-action" data-manual-execution-launch-gate-preview data-approval-request-id="${escapeHtml(approvalRequestId)}" data-queue-handoff-id="${escapeHtml(queueHandoffId)}" data-context-id="${escapeHtml(contextId)}" data-job-id="${escapeHtml(jobId)}">
          Preview Execution Launch Gate
        </button>
        <span class="agentic-review-muted" data-manual-execution-launch-gate-preview-status>
          Manual only. This previews a future launch gate and does not execute, submit, or mutate queue state.
        </span>
      </div>
    </article>
  `;
}

function renderManualExecutionLaunchGateObservabilitySection(tracePayload = {}) {
  const result = hasAgentTraceSummaryObject(tracePayload?.manual_execution_launch_gate_observability_result)
    ? tracePayload.manual_execution_launch_gate_observability_result
    : {};
  const safety = hasAgentTraceSummaryObject(result.safety_metadata)
    ? result.safety_metadata
    : {};
  const launchGate = hasAgentTraceSummaryObject(tracePayload?.manual_execution_launch_gate_preview_result)
    ? tracePayload.manual_execution_launch_gate_preview_result
    : {};
  const agentRun = tracePayload?.agent_run && typeof tracePayload.agent_run === "object"
    ? tracePayload.agent_run
    : {};
  const metadata = agentRun?.metadata && typeof agentRun.metadata === "object" ? agentRun.metadata : {};
  const contextId = tracePayload?.agent_run_id || agentRun.agent_run_id || "";
  const jobId = metadata.job_id || metadata.merge_key || "";
  const approvalRequestId = result.approval_request_id || launchGate.approval_request_id || "";
  const queueHandoffId = result.queue_handoff_id || launchGate.queue_handoff_id || "";
  return `
    <article class="agent-trace-summary" aria-label="Manual execution launch gate observability">
      <div class="agentic-workflow-header">
        <div>
          <h4>Manual Execution Launch Gate Audit</h4>
          <p>Read-only audit trace for the launch gate preview. It does not execute, submit, mutate queues or approvals, write queue files, or change resume, scoring, or ranking state.</p>
        </div>
        <span class="agentic-workflow-badge">Launch audit</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Audit", result.execution_launch_gate_observability_status || "not run")}
        ${renderWorkflowSummaryMetric("Source", result.source_execution_launch_gate_status || "-")}
        ${renderWorkflowSummaryMetric("Request id", approvalRequestId || "-")}
        ${renderWorkflowSummaryMetric("Handoff id", queueHandoffId || "-")}
        ${renderWorkflowSummaryMetric("Allowed", result.future_manual_execution_allowed === true ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Blocked", result.execution_launch_was_blocked === true ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Execution", safety.did_execute_application ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Submission", safety.did_submit_application ? "yes" : "no")}
      </div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Audit summary", result.audit_summary || {}, { helper: "Read-only execution launch gate audit summary." })}
        ${renderAgentTraceReadOnlyDetails("Audit events", result.audit_events || [], { helper: "Read-only execution launch gate audit events synthesized from the provided source payload." })}
        ${renderAgentTraceReadOnlyDetails("Safety findings", result.safety_findings || {}, { helper: "Read-only execution launch gate safety findings." })}
        ${renderAgentTraceReadOnlyDetails("Blocked actions", result.blocked_actions || [], { helper: "Observed execution launch gate blockers." })}
        ${renderAgentTraceReadOnlyDetails("Next safe step", result.next_safe_step || "", { helper: "Next safe manual step." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable execution launch gate audit safety metadata." })}
      </div>
      <div class="agentic-review-actions">
        <button type="button" class="agentic-feedback-action" data-manual-execution-launch-gate-observability data-approval-request-id="${escapeHtml(approvalRequestId)}" data-queue-handoff-id="${escapeHtml(queueHandoffId)}" data-context-id="${escapeHtml(contextId)}" data-job-id="${escapeHtml(jobId)}">
          View Execution Launch Gate Audit
        </button>
        <span class="agentic-review-muted" data-manual-execution-launch-gate-observability-status>
          Manual only. This summarizes the launch gate preview and performs no execution, submission, queue, approval, resume, scoring, or ranking mutation.
        </span>
      </div>
    </article>
  `;
}

function renderManualExecutionRequestPacketPreviewSection(tracePayload = {}) {
  const result = hasAgentTraceSummaryObject(tracePayload?.manual_execution_request_packet_preview_result)
    ? tracePayload.manual_execution_request_packet_preview_result
    : {};
  const safety = hasAgentTraceSummaryObject(result.safety_metadata)
    ? result.safety_metadata
    : {};
  const launchGate = hasAgentTraceSummaryObject(tracePayload?.manual_execution_launch_gate_preview_result)
    ? tracePayload.manual_execution_launch_gate_preview_result
    : {};
  const launchAudit = hasAgentTraceSummaryObject(tracePayload?.manual_execution_launch_gate_observability_result)
    ? tracePayload.manual_execution_launch_gate_observability_result
    : {};
  const agentRun = tracePayload?.agent_run && typeof tracePayload.agent_run === "object"
    ? tracePayload.agent_run
    : {};
  const metadata = agentRun?.metadata && typeof agentRun.metadata === "object" ? agentRun.metadata : {};
  const contextId = tracePayload?.agent_run_id || agentRun.agent_run_id || "";
  const jobId = metadata.job_id || metadata.merge_key || "";
  const approvalRequestId = result.approval_request_id || launchAudit.approval_request_id || launchGate.approval_request_id || "";
  const queueHandoffId = result.queue_handoff_id || launchAudit.queue_handoff_id || launchGate.queue_handoff_id || "";
  return `
    <article class="agent-trace-summary" aria-label="Manual execution request packet preview">
      <div class="agentic-workflow-header">
        <div>
          <h4>Manual Execution Request Packet Preview</h4>
          <p>Dry-run packet preview for human review before any future guarded execution action. It does not execute, submit, mutate queues or approvals, write queue files, or change resume, scoring, or ranking state.</p>
        </div>
        <span class="agentic-workflow-badge">Execution packet</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Packet", result.execution_request_packet_status || "not run")}
        ${renderWorkflowSummaryMetric("Request id", approvalRequestId || "-")}
        ${renderWorkflowSummaryMetric("Handoff id", queueHandoffId || "-")}
        ${renderWorkflowSummaryMetric("Ready", result.packet_ready_for_human_review === true ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Gate", result.source_execution_launch_gate_status || "-")}
        ${renderWorkflowSummaryMetric("Audit", result.source_execution_launch_gate_observability_status || "-")}
        ${renderWorkflowSummaryMetric("Execution", safety.did_execute_application ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Submission", safety.did_submit_application ? "yes" : "no")}
      </div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Execution request summary", result.execution_request_summary || {}, { helper: "Read-only execution request packet summary." })}
        ${renderAgentTraceReadOnlyDetails("Packet sections", result.packet_sections || [], { helper: "Deterministic human-review packet sections." })}
        ${renderAgentTraceReadOnlyDetails("Missing requirements", result.missing_requirements || [], { helper: "Execution request packet missing requirements." })}
        ${renderAgentTraceReadOnlyDetails("Blocked actions", result.blocked_actions || [], { helper: "Execution request packet blockers." })}
        ${renderAgentTraceReadOnlyDetails("Next safe step", result.next_safe_step || "", { helper: "Next safe manual step." })}
        ${renderAgentTraceReadOnlyDetails("Rationale", result.rationale || "", { helper: "Execution request packet preview rationale." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable execution request packet safety metadata." })}
      </div>
      <div class="agentic-review-actions">
        <button type="button" class="agentic-feedback-action" data-manual-execution-request-packet-preview data-approval-request-id="${escapeHtml(approvalRequestId)}" data-queue-handoff-id="${escapeHtml(queueHandoffId)}" data-context-id="${escapeHtml(contextId)}" data-job-id="${escapeHtml(jobId)}">
          Preview Execution Request Packet
        </button>
        <span class="agentic-review-muted" data-manual-execution-request-packet-preview-status>
          Manual only. This builds a human-review packet preview and performs no execution, submission, queue, approval, resume, scoring, or ranking mutation.
        </span>
      </div>
    </article>
  `;
}

function renderManualGuardedExecutionRequestCreateSection(tracePayload = {}) {
  const result = hasAgentTraceSummaryObject(tracePayload?.manual_guarded_execution_request_create_result)
    ? tracePayload.manual_guarded_execution_request_create_result
    : {};
  const safety = hasAgentTraceSummaryObject(result.safety_metadata)
    ? result.safety_metadata
    : {};
  const packet = hasAgentTraceSummaryObject(tracePayload?.manual_execution_request_packet_preview_result)
    ? tracePayload.manual_execution_request_packet_preview_result
    : {};
  const launchGate = hasAgentTraceSummaryObject(tracePayload?.manual_execution_launch_gate_preview_result)
    ? tracePayload.manual_execution_launch_gate_preview_result
    : {};
  const launchAudit = hasAgentTraceSummaryObject(tracePayload?.manual_execution_launch_gate_observability_result)
    ? tracePayload.manual_execution_launch_gate_observability_result
    : {};
  const agentRun = tracePayload?.agent_run && typeof tracePayload.agent_run === "object"
    ? tracePayload.agent_run
    : {};
  const metadata = agentRun?.metadata && typeof agentRun.metadata === "object" ? agentRun.metadata : {};
  const contextId = tracePayload?.agent_run_id || agentRun.agent_run_id || "";
  const jobId = metadata.job_id || metadata.merge_key || "";
  const approvalRequestId = result.approval_request_id || packet.approval_request_id || launchGate.approval_request_id || "";
  const queueHandoffId = result.queue_handoff_id || packet.queue_handoff_id || launchAudit.queue_handoff_id || launchGate.queue_handoff_id || "";
  return `
    <article class="agent-trace-summary" aria-label="Manual guarded execution request creation">
      <div class="agentic-workflow-header">
        <div>
          <h4>Manual Guarded Execution Request Creation</h4>
          <p>Manual-only guarded execution request/control artifact creation after packet preview and explicit confirmation. It never executes or submits applications and does not mutate approval status, resume content, scoring, or ranking.</p>
        </div>
        <span class="agentic-workflow-badge">Execution request</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Creation", result.execution_request_creation_status || "not run")}
        ${renderWorkflowSummaryMetric("Request id", approvalRequestId || "-")}
        ${renderWorkflowSummaryMetric("Handoff id", queueHandoffId || "-")}
        ${renderWorkflowSummaryMetric("Execution request id", result.execution_request_id || "-")}
        ${renderWorkflowSummaryMetric("Created", result.execution_request_created === true ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Queue mutation", safety.did_mutate_queue ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Execution", safety.did_execute_application ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Submission", safety.did_submit_application ? "yes" : "no")}
      </div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Source packet status", result.source_execution_request_packet_status || packet.execution_request_packet_status || "", { helper: "Source execution request packet status." })}
        ${renderAgentTraceReadOnlyDetails("Blocked actions", result.blocked_actions || [], { helper: "Guarded execution request blockers." })}
        ${renderAgentTraceReadOnlyDetails("Next safe step", result.next_safe_step || "", { helper: "Next safe manual step." })}
        ${renderAgentTraceReadOnlyDetails("Rationale", result.rationale || "", { helper: "Guarded execution request rationale." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable guarded execution request safety metadata." })}
      </div>
      <div class="agentic-review-actions">
        <label class="agentic-review-muted">
          <input type="checkbox" data-manual-guarded-execution-request-create-confirmation>
          I explicitly confirm this guarded execution request.
        </label>
        <button type="button" class="agentic-feedback-action" data-manual-guarded-execution-request-create data-approval-request-id="${escapeHtml(approvalRequestId)}" data-queue-handoff-id="${escapeHtml(queueHandoffId)}" data-context-id="${escapeHtml(contextId)}" data-job-id="${escapeHtml(jobId)}">
          Create Guarded Execution Request
        </button>
        <span class="agentic-review-muted" data-manual-guarded-execution-request-create-status>
          Manual only. This requires explicit confirmation and will block unless an existing execution-request writer is configured.
        </span>
      </div>
    </article>
  `;
}

function renderManualGuardedExecutionRequestObservabilitySection(tracePayload = {}) {
  const result = hasAgentTraceSummaryObject(tracePayload?.manual_guarded_execution_request_observability_result)
    ? tracePayload.manual_guarded_execution_request_observability_result
    : {};
  const safety = hasAgentTraceSummaryObject(result.safety_metadata)
    ? result.safety_metadata
    : {};
  const creation = hasAgentTraceSummaryObject(tracePayload?.manual_guarded_execution_request_create_result)
    ? tracePayload.manual_guarded_execution_request_create_result
    : {};
  const agentRun = tracePayload?.agent_run && typeof tracePayload.agent_run === "object"
    ? tracePayload.agent_run
    : {};
  const metadata = agentRun?.metadata && typeof agentRun.metadata === "object" ? agentRun.metadata : {};
  const contextId = tracePayload?.agent_run_id || agentRun.agent_run_id || "";
  const jobId = metadata.job_id || metadata.merge_key || "";
  const approvalRequestId = result.approval_request_id || creation.approval_request_id || "";
  const queueHandoffId = result.queue_handoff_id || creation.queue_handoff_id || "";
  const executionRequestId = result.execution_request_id || creation.execution_request_id || "";
  return `
    <article class="agent-trace-summary" aria-label="Manual guarded execution request observability">
      <div class="agentic-workflow-header">
        <div>
          <h4>Manual Execution Request Audit</h4>
          <p>Read-only audit trace for the guarded execution request result. It creates no execution requests, writes no queue files, and never executes or submits applications.</p>
        </div>
        <span class="agentic-workflow-badge">Execution audit</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Audit", result.execution_request_observability_status || "not run")}
        ${renderWorkflowSummaryMetric("Source", result.source_execution_request_creation_status || "-")}
        ${renderWorkflowSummaryMetric("Request id", approvalRequestId || "-")}
        ${renderWorkflowSummaryMetric("Handoff id", queueHandoffId || "-")}
        ${renderWorkflowSummaryMetric("Execution request id", executionRequestId || "-")}
        ${renderWorkflowSummaryMetric("Created", result.execution_request_was_created === true ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Blocked", result.execution_request_was_blocked === true ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Execution", safety.did_execute_application ? "yes" : "no")}
      </div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Audit summary", result.audit_summary || {}, { helper: "Read-only execution request audit summary." })}
        ${renderAgentTraceReadOnlyDetails("Audit events", result.audit_events || [], { helper: "Read-only execution request audit events synthesized from the provided source payload." })}
        ${renderAgentTraceReadOnlyDetails("Safety findings", result.safety_findings || {}, { helper: "Read-only execution request safety findings." })}
        ${renderAgentTraceReadOnlyDetails("Blocked actions", result.blocked_actions || [], { helper: "Observed execution request blockers." })}
        ${renderAgentTraceReadOnlyDetails("Next safe step", result.next_safe_step || "", { helper: "Next safe manual step." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable execution request audit safety metadata." })}
      </div>
      <div class="agentic-review-actions">
        <button type="button" class="agentic-feedback-action" data-manual-guarded-execution-request-observability data-approval-request-id="${escapeHtml(approvalRequestId)}" data-queue-handoff-id="${escapeHtml(queueHandoffId)}" data-execution-request-id="${escapeHtml(executionRequestId)}" data-context-id="${escapeHtml(contextId)}" data-job-id="${escapeHtml(jobId)}">
          View Execution Request Audit
        </button>
        <span class="agentic-review-muted" data-manual-guarded-execution-request-observability-status>
          Manual only. This summarizes the guarded execution request result and performs no request creation, queue, approval, resume, execution, or submission mutation.
        </span>
      </div>
    </article>
  `;
}

function renderManualExecutionRequestReadbackSection(tracePayload = {}) {
  const result = hasAgentTraceSummaryObject(tracePayload?.manual_execution_request_readback_result)
    ? tracePayload.manual_execution_request_readback_result
    : {};
  const safety = hasAgentTraceSummaryObject(result.safety_metadata)
    ? result.safety_metadata
    : {};
  const creation = hasAgentTraceSummaryObject(tracePayload?.manual_guarded_execution_request_create_result)
    ? tracePayload.manual_guarded_execution_request_create_result
    : {};
  const audit = hasAgentTraceSummaryObject(tracePayload?.manual_guarded_execution_request_observability_result)
    ? tracePayload.manual_guarded_execution_request_observability_result
    : {};
  const agentRun = tracePayload?.agent_run && typeof tracePayload.agent_run === "object"
    ? tracePayload.agent_run
    : {};
  const metadata = agentRun?.metadata && typeof agentRun.metadata === "object" ? agentRun.metadata : {};
  const contextId = tracePayload?.agent_run_id || agentRun.agent_run_id || "";
  const jobId = metadata.job_id || metadata.merge_key || "";
  const approvalRequestId = result.approval_request_id || audit.approval_request_id || creation.approval_request_id || "";
  const queueHandoffId = result.queue_handoff_id || audit.queue_handoff_id || creation.queue_handoff_id || "";
  const executionRequestId = result.execution_request_id || audit.execution_request_id || creation.execution_request_id || "";
  return `
    <article class="agent-trace-summary" aria-label="Manual execution request readback">
      <div class="agentic-workflow-header">
        <div>
          <h4>Manual Execution Request Readback</h4>
          <p>Read-only execution request detail. It creates no execution requests, writes no queue files, and never executes or submits applications.</p>
        </div>
        <span class="agentic-workflow-badge">Execution readback</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Readback", result.execution_request_readback_status || "not run")}
        ${renderWorkflowSummaryMetric("Execution request found", result.execution_request_found === true ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Execution request id", executionRequestId || "-")}
        ${renderWorkflowSummaryMetric("Request id", approvalRequestId || "-")}
        ${renderWorkflowSummaryMetric("Handoff id", queueHandoffId || "-")}
        ${renderWorkflowSummaryMetric("Execution", safety.did_execute_application ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Submission", safety.did_submit_application ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Queue write", safety.did_write_queue ? "yes" : "no")}
      </div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Readback summary", result.readback_summary || {}, { helper: "Read-only execution request summary." })}
        ${renderAgentTraceReadOnlyDetails("Detail sections", result.detail_sections || [], { helper: "Read-only execution request detail sections." })}
        ${renderAgentTraceReadOnlyDetails("Missing requirements", result.missing_requirements || [], { helper: "Execution request readback missing requirements." })}
        ${renderAgentTraceReadOnlyDetails("Blocked actions", result.blocked_actions || [], { helper: "Execution request readback blockers." })}
        ${renderAgentTraceReadOnlyDetails("Next safe step", result.next_safe_step || "", { helper: "Next safe manual step." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable execution request readback safety metadata." })}
      </div>
      <div class="agentic-review-actions">
        <button type="button" class="agentic-feedback-action" data-manual-execution-request-readback data-approval-request-id="${escapeHtml(approvalRequestId)}" data-queue-handoff-id="${escapeHtml(queueHandoffId)}" data-execution-request-id="${escapeHtml(executionRequestId)}" data-context-id="${escapeHtml(contextId)}" data-job-id="${escapeHtml(jobId)}">
          Read Execution Request
        </button>
        <span class="agentic-review-muted" data-manual-execution-request-readback-status>
          Manual only. This reads execution request details from supplied evidence and does not create requests, mutate queue or approval state, execute, or submit.
        </span>
      </div>
    </article>
  `;
}

function renderManualExecutionRequestStatusTransitionPreviewSection(tracePayload = {}) {
  const result = hasAgentTraceSummaryObject(tracePayload?.manual_execution_request_status_transition_preview_result)
    ? tracePayload.manual_execution_request_status_transition_preview_result
    : {};
  const safety = hasAgentTraceSummaryObject(result.safety_metadata)
    ? result.safety_metadata
    : {};
  const readback = hasAgentTraceSummaryObject(tracePayload?.manual_execution_request_readback_result)
    ? tracePayload.manual_execution_request_readback_result
    : {};
  const creation = hasAgentTraceSummaryObject(tracePayload?.manual_guarded_execution_request_create_result)
    ? tracePayload.manual_guarded_execution_request_create_result
    : {};
  const audit = hasAgentTraceSummaryObject(tracePayload?.manual_guarded_execution_request_observability_result)
    ? tracePayload.manual_guarded_execution_request_observability_result
    : {};
  const agentRun = tracePayload?.agent_run && typeof tracePayload.agent_run === "object"
    ? tracePayload.agent_run
    : {};
  const metadata = agentRun?.metadata && typeof agentRun.metadata === "object" ? agentRun.metadata : {};
  const contextId = tracePayload?.agent_run_id || agentRun.agent_run_id || "";
  const jobId = metadata.job_id || metadata.merge_key || "";
  const approvalRequestId = result.approval_request_id || readback.approval_request_id || audit.approval_request_id || creation.approval_request_id || "";
  const queueHandoffId = result.queue_handoff_id || readback.queue_handoff_id || audit.queue_handoff_id || creation.queue_handoff_id || "";
  const executionRequestId = result.execution_request_id || readback.execution_request_id || audit.execution_request_id || creation.execution_request_id || "";
  const options = ["ready_for_manual_execution", "needs_changes", "cancelled", "keep_pending_review"];
  return `
    <article class="agent-trace-summary" aria-label="Manual execution request status transition preview">
      <div class="agentic-workflow-header">
        <div>
          <h4>Manual Execution Request Status Transition Preview</h4>
          <p>Dry-run transition preview only. It does not update execution request status, mutate queues or approvals, execute, or submit applications.</p>
        </div>
        <span class="agentic-workflow-badge">Execution transition</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Preview", result.execution_request_status_transition_preview_status || "not run")}
        ${renderWorkflowSummaryMetric("Transition", result.requested_transition || "-")}
        ${renderWorkflowSummaryMetric("Previous", result.previous_execution_request_status || "-")}
        ${renderWorkflowSummaryMetric("Proposed", result.proposed_execution_request_status || "-")}
        ${renderWorkflowSummaryMetric("Allowed later", result.transition_allowed_later === true ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Status updated", safety.did_update_execution_request_status ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Execution", safety.did_execute_application ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Submission", safety.did_submit_application ? "yes" : "no")}
      </div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Missing requirements", result.missing_requirements || [], { helper: "Execution request transition preview missing requirements." })}
        ${renderAgentTraceReadOnlyDetails("Blocked actions", result.blocked_actions || [], { helper: "Execution request transition preview blockers." })}
        ${renderAgentTraceReadOnlyDetails("Source readback status", result.source_execution_request_readback_status || "", { helper: "Source execution request readback status." })}
        ${renderAgentTraceReadOnlyDetails("Next safe step", result.next_safe_step || "", { helper: "Next safe manual step." })}
        ${renderAgentTraceReadOnlyDetails("Rationale", result.rationale || "", { helper: "Execution request transition preview rationale." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable execution request transition preview safety metadata." })}
      </div>
      <div class="agentic-review-actions">
        <select class="agentic-feedback-action" data-manual-execution-request-status-transition-preview-select aria-label="Execution request status transition preview">
          ${options.map((option) => `<option value="${escapeHtml(option)}">${escapeHtml(option)}</option>`).join("")}
        </select>
        <button type="button" class="agentic-feedback-action" data-manual-execution-request-status-transition-preview data-approval-request-id="${escapeHtml(approvalRequestId)}" data-queue-handoff-id="${escapeHtml(queueHandoffId)}" data-execution-request-id="${escapeHtml(executionRequestId)}" data-context-id="${escapeHtml(contextId)}" data-job-id="${escapeHtml(jobId)}">
          Preview Execution Request Status Transition
        </button>
        <span class="agentic-review-muted" data-manual-execution-request-status-transition-preview-status>
          Manual only. This previews a future execution request status transition and does not update request, queue, approval, execution, or submission state.
        </span>
      </div>
    </article>
  `;
}

function renderManualGuardedExecutionRequestStatusTransitionSection(tracePayload = {}) {
  const result = hasAgentTraceSummaryObject(tracePayload?.manual_guarded_execution_request_status_transition_result)
    ? tracePayload.manual_guarded_execution_request_status_transition_result
    : {};
  const safety = hasAgentTraceSummaryObject(result.safety_metadata)
    ? result.safety_metadata
    : {};
  const preview = hasAgentTraceSummaryObject(tracePayload?.manual_execution_request_status_transition_preview_result)
    ? tracePayload.manual_execution_request_status_transition_preview_result
    : {};
  const readback = hasAgentTraceSummaryObject(tracePayload?.manual_execution_request_readback_result)
    ? tracePayload.manual_execution_request_readback_result
    : {};
  const agentRun = tracePayload?.agent_run && typeof tracePayload.agent_run === "object"
    ? tracePayload.agent_run
    : {};
  const metadata = agentRun?.metadata && typeof agentRun.metadata === "object" ? agentRun.metadata : {};
  const contextId = tracePayload?.agent_run_id || agentRun.agent_run_id || "";
  const jobId = metadata.job_id || metadata.merge_key || "";
  const approvalRequestId = result.approval_request_id || preview.approval_request_id || readback.approval_request_id || "";
  const queueHandoffId = result.queue_handoff_id || preview.queue_handoff_id || readback.queue_handoff_id || "";
  const executionRequestId = result.execution_request_id || preview.execution_request_id || readback.execution_request_id || "";
  const requestedTransition = result.requested_transition || preview.requested_transition || "ready_for_manual_execution";
  return `
    <article class="agent-trace-summary" aria-label="Manual guarded execution request status transition">
      <div class="agentic-workflow-header">
        <div>
          <h4>Manual Guarded Execution Request Status Transition</h4>
          <p>Manual guarded status update only. It requires a ready preview and explicit confirmation, and does not execute, submit, mutate approvals, resumes, scoring, or ranking.</p>
        </div>
        <span class="agentic-workflow-badge">Guarded execution status</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Transition status", result.execution_request_status_transition_status || "not run")}
        ${renderWorkflowSummaryMetric("Execution request id", executionRequestId || "-")}
        ${renderWorkflowSummaryMetric("Requested", requestedTransition || "-")}
        ${renderWorkflowSummaryMetric("Updated", result.execution_request_status_updated === true ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Previous", result.previous_execution_request_status || "-")}
        ${renderWorkflowSummaryMetric("New", result.new_execution_request_status || "-")}
        ${renderWorkflowSummaryMetric("Status updated", safety.did_update_execution_request_status ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Execution", safety.did_execute_application ? "yes" : "no")}
      </div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Blocked actions", result.blocked_actions || [], { helper: "Guarded execution request status blockers." })}
        ${renderAgentTraceReadOnlyDetails("Source transition preview status", result.source_transition_preview_status || "", { helper: "Source transition preview status." })}
        ${renderAgentTraceReadOnlyDetails("Next safe step", result.next_safe_step || "", { helper: "Next safe manual step." })}
        ${renderAgentTraceReadOnlyDetails("Rationale", result.rationale || "", { helper: "Guarded execution request status transition rationale." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable guarded execution request status transition safety metadata." })}
      </div>
      <div class="agentic-review-actions">
        <label class="agentic-review-muted">
          <input type="checkbox" data-manual-guarded-execution-request-status-transition-confirmation>
          I explicitly confirm this guarded execution request status transition.
        </label>
        <button type="button" class="agentic-feedback-action" data-manual-guarded-execution-request-status-transition data-approval-request-id="${escapeHtml(approvalRequestId)}" data-queue-handoff-id="${escapeHtml(queueHandoffId)}" data-execution-request-id="${escapeHtml(executionRequestId)}" data-requested-transition="${escapeHtml(requestedTransition)}" data-context-id="${escapeHtml(contextId)}" data-job-id="${escapeHtml(jobId)}">
          Apply Guarded Execution Request Status
        </button>
        <span class="agentic-review-muted" data-manual-guarded-execution-request-status-transition-status>
          Manual only. This requires explicit confirmation and does not execute, submit, or mutate approval, resume, scoring, or ranking state.
        </span>
      </div>
    </article>
  `;
}

function renderManualGuardedExecutionRequestStatusTransitionObservabilitySection(tracePayload = {}) {
  const result = hasAgentTraceSummaryObject(tracePayload?.manual_guarded_execution_request_status_transition_observability_result)
    ? tracePayload.manual_guarded_execution_request_status_transition_observability_result
    : {};
  const safety = hasAgentTraceSummaryObject(result.safety_metadata)
    ? result.safety_metadata
    : {};
  const transition = hasAgentTraceSummaryObject(tracePayload?.manual_guarded_execution_request_status_transition_result)
    ? tracePayload.manual_guarded_execution_request_status_transition_result
    : {};
  const preview = hasAgentTraceSummaryObject(tracePayload?.manual_execution_request_status_transition_preview_result)
    ? tracePayload.manual_execution_request_status_transition_preview_result
    : {};
  const readback = hasAgentTraceSummaryObject(tracePayload?.manual_execution_request_readback_result)
    ? tracePayload.manual_execution_request_readback_result
    : {};
  const agentRun = tracePayload?.agent_run && typeof tracePayload.agent_run === "object"
    ? tracePayload.agent_run
    : {};
  const metadata = agentRun?.metadata && typeof agentRun.metadata === "object" ? agentRun.metadata : {};
  const contextId = tracePayload?.agent_run_id || agentRun.agent_run_id || "";
  const jobId = metadata.job_id || metadata.merge_key || "";
  const approvalRequestId = result.approval_request_id || transition.approval_request_id || preview.approval_request_id || readback.approval_request_id || "";
  const queueHandoffId = result.queue_handoff_id || transition.queue_handoff_id || preview.queue_handoff_id || readback.queue_handoff_id || "";
  const executionRequestId = result.execution_request_id || transition.execution_request_id || preview.execution_request_id || readback.execution_request_id || "";
  const requestedTransition = result.requested_transition || transition.requested_transition || preview.requested_transition || "";
  return `
    <article class="agent-trace-summary" aria-label="Manual guarded execution request status transition observability">
      <div class="agentic-workflow-header">
        <div>
          <h4>Manual Execution Request Status Audit</h4>
          <p>Read-only audit trace for the guarded execution request status transition result. It does not update execution request status, mutate queues or approvals, execute, or submit applications.</p>
        </div>
        <span class="agentic-workflow-badge">Execution status audit</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Audit", result.execution_request_status_transition_observability_status || "not run")}
        ${renderWorkflowSummaryMetric("Source", result.source_execution_request_status_transition_status || "-")}
        ${renderWorkflowSummaryMetric("Execution request id", executionRequestId || "-")}
        ${renderWorkflowSummaryMetric("Requested", requestedTransition || "-")}
        ${renderWorkflowSummaryMetric("Applied", result.execution_request_status_transition_was_applied === true ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Blocked", result.execution_request_status_transition_was_blocked === true ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Previous", result.previous_execution_request_status || "-")}
        ${renderWorkflowSummaryMetric("New", result.new_execution_request_status || "-")}
        ${renderWorkflowSummaryMetric("Status updated", safety.did_update_execution_request_status ? "yes" : "no")}
      </div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Audit summary", result.audit_summary || {}, { helper: "Read-only execution request status transition audit summary." })}
        ${renderAgentTraceReadOnlyDetails("Audit events", result.audit_events || [], { helper: "Read-only execution request status transition audit events synthesized from the provided source payload." })}
        ${renderAgentTraceReadOnlyDetails("Safety findings", result.safety_findings || {}, { helper: "Read-only execution request status transition observability safety findings." })}
        ${renderAgentTraceReadOnlyDetails("Blocked actions", result.blocked_actions || [], { helper: "Observed execution request status transition blockers." })}
        ${renderAgentTraceReadOnlyDetails("Next safe step", result.next_safe_step || "", { helper: "Next safe manual step." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable execution request status transition observability safety metadata." })}
      </div>
      <div class="agentic-review-actions">
        <button type="button" class="agentic-feedback-action" data-manual-guarded-execution-request-status-transition-observability data-approval-request-id="${escapeHtml(approvalRequestId)}" data-queue-handoff-id="${escapeHtml(queueHandoffId)}" data-execution-request-id="${escapeHtml(executionRequestId)}" data-requested-transition="${escapeHtml(requestedTransition)}" data-context-id="${escapeHtml(contextId)}" data-job-id="${escapeHtml(jobId)}">
          View Execution Request Status Audit
        </button>
        <span class="agentic-review-muted" data-manual-guarded-execution-request-status-transition-observability-status>
          Manual only. This summarizes the guarded execution request status transition result and performs no status update, queue write, approval mutation, execution, or submission.
        </span>
      </div>
    </article>
  `;
}

function renderManualApplicationExecutionSimulationPreviewSection(tracePayload = {}) {
  const result = hasAgentTraceSummaryObject(tracePayload?.manual_application_execution_simulation_preview_result)
    ? tracePayload.manual_application_execution_simulation_preview_result
    : {};
  const safety = hasAgentTraceSummaryObject(result.safety_metadata)
    ? result.safety_metadata
    : {};
  const readback = hasAgentTraceSummaryObject(tracePayload?.manual_execution_request_readback_result)
    ? tracePayload.manual_execution_request_readback_result
    : {};
  const transition = hasAgentTraceSummaryObject(tracePayload?.manual_guarded_execution_request_status_transition_result)
    ? tracePayload.manual_guarded_execution_request_status_transition_result
    : {};
  const audit = hasAgentTraceSummaryObject(tracePayload?.manual_guarded_execution_request_status_transition_observability_result)
    ? tracePayload.manual_guarded_execution_request_status_transition_observability_result
    : {};
  const agentRun = tracePayload?.agent_run && typeof tracePayload.agent_run === "object"
    ? tracePayload.agent_run
    : {};
  const metadata = agentRun?.metadata && typeof agentRun.metadata === "object" ? agentRun.metadata : {};
  const contextId = tracePayload?.agent_run_id || agentRun.agent_run_id || "";
  const jobId = metadata.job_id || metadata.merge_key || "";
  const approvalRequestId = result.approval_request_id || audit.approval_request_id || transition.approval_request_id || readback.approval_request_id || "";
  const queueHandoffId = result.queue_handoff_id || audit.queue_handoff_id || transition.queue_handoff_id || readback.queue_handoff_id || "";
  const executionRequestId = result.execution_request_id || audit.execution_request_id || transition.execution_request_id || readback.execution_request_id || "";
  return `
    <article class="agent-trace-summary" aria-label="Manual application execution simulation preview">
      <div class="agentic-workflow-header">
        <div>
          <h4>Manual Application Execution Simulation Preview</h4>
          <p>Dry-run simulation preview only. It does not execute, submit, create requests, update statuses, mutate queues or approvals, write files, or launch pipeline work.</p>
        </div>
        <span class="agentic-workflow-badge">Execution simulation</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Simulation", result.application_execution_simulation_status || "not run")}
        ${renderWorkflowSummaryMetric("Execution request id", executionRequestId || "-")}
        ${renderWorkflowSummaryMetric("Approval id", approvalRequestId || "-")}
        ${renderWorkflowSummaryMetric("Queue handoff id", queueHandoffId || "-")}
        ${renderWorkflowSummaryMetric("Allowed later", result.simulated_execution_allowed_later === true ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Executed", safety.did_execute_application ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Submitted", safety.did_submit_application ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Queue write", safety.did_write_queue ? "yes" : "no")}
      </div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Simulated steps", result.simulated_steps || [], { helper: "Deterministic future execution phases. These are descriptions only." })}
        ${renderAgentTraceReadOnlyDetails("Execution preconditions", result.execution_preconditions || {}, { helper: "Read-only source evidence used for this simulation preview." })}
        ${renderAgentTraceReadOnlyDetails("Missing requirements", result.missing_requirements || [], { helper: "Simulation preview missing requirements." })}
        ${renderAgentTraceReadOnlyDetails("Blocked actions", result.blocked_actions || [], { helper: "Simulation preview blockers." })}
        ${renderAgentTraceReadOnlyDetails("Next safe step", result.next_safe_step || "", { helper: "Next safe manual step." })}
        ${renderAgentTraceReadOnlyDetails("Rationale", result.rationale || "", { helper: "Application execution simulation preview rationale." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable application execution simulation preview safety metadata." })}
      </div>
      <div class="agentic-review-actions">
        <button type="button" class="agentic-feedback-action" data-manual-application-execution-simulation-preview data-approval-request-id="${escapeHtml(approvalRequestId)}" data-queue-handoff-id="${escapeHtml(queueHandoffId)}" data-execution-request-id="${escapeHtml(executionRequestId)}" data-context-id="${escapeHtml(contextId)}" data-job-id="${escapeHtml(jobId)}">
          Preview Application Execution Simulation
        </button>
        <span class="agentic-review-muted" data-manual-application-execution-simulation-preview-status>
          Manual only. This simulates future guarded execution and performs no execution, submission, queue write, status update, or pipeline launch.
        </span>
      </div>
    </article>
  `;
}

function renderManualApplicationExecutionSimulationObservabilitySection(tracePayload = {}) {
  const result = hasAgentTraceSummaryObject(tracePayload?.manual_application_execution_simulation_observability_result)
    ? tracePayload.manual_application_execution_simulation_observability_result
    : {};
  const safety = hasAgentTraceSummaryObject(result.safety_metadata)
    ? result.safety_metadata
    : {};
  const simulation = hasAgentTraceSummaryObject(tracePayload?.manual_application_execution_simulation_preview_result)
    ? tracePayload.manual_application_execution_simulation_preview_result
    : {};
  const readback = hasAgentTraceSummaryObject(tracePayload?.manual_execution_request_readback_result)
    ? tracePayload.manual_execution_request_readback_result
    : {};
  const agentRun = tracePayload?.agent_run && typeof tracePayload.agent_run === "object"
    ? tracePayload.agent_run
    : {};
  const metadata = agentRun?.metadata && typeof agentRun.metadata === "object" ? agentRun.metadata : {};
  const contextId = tracePayload?.agent_run_id || agentRun.agent_run_id || "";
  const jobId = metadata.job_id || metadata.merge_key || "";
  const approvalRequestId = result.approval_request_id || simulation.approval_request_id || readback.approval_request_id || "";
  const queueHandoffId = result.queue_handoff_id || simulation.queue_handoff_id || readback.queue_handoff_id || "";
  const executionRequestId = result.execution_request_id || simulation.execution_request_id || readback.execution_request_id || "";
  return `
    <article class="agent-trace-summary" aria-label="Manual application execution simulation observability">
      <div class="agentic-workflow-header">
        <div>
          <h4>Manual Application Execution Simulation Audit</h4>
          <p>Read-only audit trace for the application execution simulation preview. It does not execute, submit, write queues, update statuses, mutate approvals, or launch pipeline work.</p>
        </div>
        <span class="agentic-workflow-badge">Simulation audit</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Audit", result.application_execution_simulation_observability_status || "not run")}
        ${renderWorkflowSummaryMetric("Source", result.source_application_execution_simulation_status || "-")}
        ${renderWorkflowSummaryMetric("Execution request id", executionRequestId || "-")}
        ${renderWorkflowSummaryMetric("Approval id", approvalRequestId || "-")}
        ${renderWorkflowSummaryMetric("Queue handoff id", queueHandoffId || "-")}
        ${renderWorkflowSummaryMetric("Ready", result.simulation_was_ready === true ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Blocked", result.simulation_was_blocked === true ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Executed", safety.did_execute_application ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Submitted", safety.did_submit_application ? "yes" : "no")}
      </div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Audit summary", result.audit_summary || {}, { helper: "Read-only application execution simulation audit summary." })}
        ${renderAgentTraceReadOnlyDetails("Audit events", result.audit_events || [], { helper: "Read-only simulation audit events synthesized from the provided source payload." })}
        ${renderAgentTraceReadOnlyDetails("Safety findings", result.safety_findings || {}, { helper: "Read-only simulation observability safety findings." })}
        ${renderAgentTraceReadOnlyDetails("Blocked actions", result.blocked_actions || [], { helper: "Observed simulation blockers." })}
        ${renderAgentTraceReadOnlyDetails("Next safe step", result.next_safe_step || "", { helper: "Next safe manual step." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable application execution simulation observability safety metadata." })}
      </div>
      <div class="agentic-review-actions">
        <button type="button" class="agentic-feedback-action" data-manual-application-execution-simulation-observability data-approval-request-id="${escapeHtml(approvalRequestId)}" data-queue-handoff-id="${escapeHtml(queueHandoffId)}" data-execution-request-id="${escapeHtml(executionRequestId)}" data-context-id="${escapeHtml(contextId)}" data-job-id="${escapeHtml(jobId)}">
          View Application Execution Simulation Audit
        </button>
        <span class="agentic-review-muted" data-manual-application-execution-simulation-observability-status>
          Manual only. This summarizes the simulation result and performs no execution, submission, queue write, status update, approval mutation, or pipeline launch.
        </span>
      </div>
    </article>
  `;
}

function renderManualApplicationExecutionPreflightChecklistSection(tracePayload = {}) {
  const result = hasAgentTraceSummaryObject(tracePayload?.manual_application_execution_preflight_checklist_result)
    ? tracePayload.manual_application_execution_preflight_checklist_result
    : {};
  const safety = hasAgentTraceSummaryObject(result.safety_metadata)
    ? result.safety_metadata
    : {};
  const simulation = hasAgentTraceSummaryObject(tracePayload?.manual_application_execution_simulation_preview_result)
    ? tracePayload.manual_application_execution_simulation_preview_result
    : {};
  const simulationAudit = hasAgentTraceSummaryObject(tracePayload?.manual_application_execution_simulation_observability_result)
    ? tracePayload.manual_application_execution_simulation_observability_result
    : {};
  const readback = hasAgentTraceSummaryObject(tracePayload?.manual_execution_request_readback_result)
    ? tracePayload.manual_execution_request_readback_result
    : {};
  const agentRun = tracePayload?.agent_run && typeof tracePayload.agent_run === "object"
    ? tracePayload.agent_run
    : {};
  const metadata = agentRun?.metadata && typeof agentRun.metadata === "object" ? agentRun.metadata : {};
  const contextId = tracePayload?.agent_run_id || agentRun.agent_run_id || "";
  const jobId = metadata.job_id || metadata.merge_key || "";
  const approvalRequestId = result.approval_request_id || simulationAudit.approval_request_id || simulation.approval_request_id || readback.approval_request_id || "";
  const queueHandoffId = result.queue_handoff_id || simulationAudit.queue_handoff_id || simulation.queue_handoff_id || readback.queue_handoff_id || "";
  const executionRequestId = result.execution_request_id || simulationAudit.execution_request_id || simulation.execution_request_id || readback.execution_request_id || "";
  return `
    <article class="agent-trace-summary" aria-label="Manual application execution preflight checklist">
      <div class="agentic-workflow-header">
        <div>
          <h4>Manual Application Execution Preflight Checklist</h4>
          <p>Dry-run checklist only. It verifies simulation evidence before any future human-reviewed guarded execution action and performs no execution, submission, queue write, or pipeline launch.</p>
        </div>
        <span class="agentic-workflow-badge">Execution preflight</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Preflight", result.application_execution_preflight_status || "not run")}
        ${renderWorkflowSummaryMetric("Execution request id", executionRequestId || "-")}
        ${renderWorkflowSummaryMetric("Approval id", approvalRequestId || "-")}
        ${renderWorkflowSummaryMetric("Queue handoff id", queueHandoffId || "-")}
        ${renderWorkflowSummaryMetric("Ready for review", result.preflight_ready_for_human_review === true ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Passed checks", Array.isArray(result.passed_checks) ? String(result.passed_checks.length) : "0")}
        ${renderWorkflowSummaryMetric("Failed checks", Array.isArray(result.failed_checks) ? String(result.failed_checks.length) : "0")}
        ${renderWorkflowSummaryMetric("Executed", safety.did_execute_application ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Submitted", safety.did_submit_application ? "yes" : "no")}
      </div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Preflight checks", result.preflight_checks || [], { helper: "Deterministic final dry-run checks before any future guarded execution action." })}
        ${renderAgentTraceReadOnlyDetails("Passed checks", result.passed_checks || [], { helper: "Checks that passed." })}
        ${renderAgentTraceReadOnlyDetails("Failed checks", result.failed_checks || [], { helper: "Checks that failed." })}
        ${renderAgentTraceReadOnlyDetails("Missing requirements", result.missing_requirements || [], { helper: "Preflight missing requirements." })}
        ${renderAgentTraceReadOnlyDetails("Blocked actions", result.blocked_actions || [], { helper: "Preflight blockers." })}
        ${renderAgentTraceReadOnlyDetails("Next safe step", result.next_safe_step || "", { helper: "Next safe manual step." })}
        ${renderAgentTraceReadOnlyDetails("Rationale", result.rationale || "", { helper: "Application execution preflight checklist rationale." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable application execution preflight checklist safety metadata." })}
      </div>
      <div class="agentic-review-actions">
        <button type="button" class="agentic-feedback-action" data-manual-application-execution-preflight-checklist data-approval-request-id="${escapeHtml(approvalRequestId)}" data-queue-handoff-id="${escapeHtml(queueHandoffId)}" data-execution-request-id="${escapeHtml(executionRequestId)}" data-context-id="${escapeHtml(contextId)}" data-job-id="${escapeHtml(jobId)}">
          Preview Application Execution Preflight
        </button>
        <span class="agentic-review-muted" data-manual-application-execution-preflight-checklist-status>
          Manual only. This checklist is dry-run/read-only and performs no execution, submission, queue write, status update, approval mutation, or pipeline launch.
        </span>
      </div>
    </article>
  `;
}

function renderManualApplicationExecutionPreflightObservabilitySection(tracePayload = {}) {
  const result = hasAgentTraceSummaryObject(tracePayload?.manual_application_execution_preflight_observability_result)
    ? tracePayload.manual_application_execution_preflight_observability_result
    : {};
  const safety = hasAgentTraceSummaryObject(result.safety_metadata)
    ? result.safety_metadata
    : {};
  const preflight = hasAgentTraceSummaryObject(tracePayload?.manual_application_execution_preflight_checklist_result)
    ? tracePayload.manual_application_execution_preflight_checklist_result
    : {};
  const simulation = hasAgentTraceSummaryObject(tracePayload?.manual_application_execution_simulation_preview_result)
    ? tracePayload.manual_application_execution_simulation_preview_result
    : {};
  const readback = hasAgentTraceSummaryObject(tracePayload?.manual_execution_request_readback_result)
    ? tracePayload.manual_execution_request_readback_result
    : {};
  const agentRun = tracePayload?.agent_run && typeof tracePayload.agent_run === "object"
    ? tracePayload.agent_run
    : {};
  const metadata = agentRun?.metadata && typeof agentRun.metadata === "object" ? agentRun.metadata : {};
  const contextId = tracePayload?.agent_run_id || agentRun.agent_run_id || "";
  const jobId = metadata.job_id || metadata.merge_key || "";
  const approvalRequestId = result.approval_request_id || preflight.approval_request_id || simulation.approval_request_id || readback.approval_request_id || "";
  const queueHandoffId = result.queue_handoff_id || preflight.queue_handoff_id || simulation.queue_handoff_id || readback.queue_handoff_id || "";
  const executionRequestId = result.execution_request_id || preflight.execution_request_id || simulation.execution_request_id || readback.execution_request_id || "";
  return `
    <article class="agent-trace-summary" aria-label="Manual application execution preflight observability">
      <div class="agentic-workflow-header">
        <div>
          <h4>Manual Application Execution Preflight Audit</h4>
          <p>Read-only audit trace for the application execution preflight checklist. It does not execute, submit, write queues, update statuses, mutate approvals, or launch pipeline work.</p>
        </div>
        <span class="agentic-workflow-badge">Preflight audit</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Audit", result.application_execution_preflight_observability_status || "not run")}
        ${renderWorkflowSummaryMetric("Source", result.source_application_execution_preflight_status || "-")}
        ${renderWorkflowSummaryMetric("Execution request id", executionRequestId || "-")}
        ${renderWorkflowSummaryMetric("Approval id", approvalRequestId || "-")}
        ${renderWorkflowSummaryMetric("Queue handoff id", queueHandoffId || "-")}
        ${renderWorkflowSummaryMetric("Ready", result.preflight_was_ready === true ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Blocked", result.preflight_was_blocked === true ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Executed", safety.did_execute_application ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Submitted", safety.did_submit_application ? "yes" : "no")}
      </div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Audit summary", result.audit_summary || {}, { helper: "Read-only application execution preflight audit summary." })}
        ${renderAgentTraceReadOnlyDetails("Audit events", result.audit_events || [], { helper: "Read-only preflight audit events synthesized from the provided source payload." })}
        ${renderAgentTraceReadOnlyDetails("Safety findings", result.safety_findings || {}, { helper: "Read-only preflight observability safety findings." })}
        ${renderAgentTraceReadOnlyDetails("Blocked actions", result.blocked_actions || [], { helper: "Observed preflight blockers." })}
        ${renderAgentTraceReadOnlyDetails("Next safe step", result.next_safe_step || "", { helper: "Next safe manual step." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable application execution preflight observability safety metadata." })}
      </div>
      <div class="agentic-review-actions">
        <button type="button" class="agentic-feedback-action" data-manual-application-execution-preflight-observability data-approval-request-id="${escapeHtml(approvalRequestId)}" data-queue-handoff-id="${escapeHtml(queueHandoffId)}" data-execution-request-id="${escapeHtml(executionRequestId)}" data-context-id="${escapeHtml(contextId)}" data-job-id="${escapeHtml(jobId)}">
          View Application Execution Preflight Audit
        </button>
        <span class="agentic-review-muted" data-manual-application-execution-preflight-observability-status>
          Manual only. This summarizes the preflight checklist and performs no execution, submission, queue write, status update, approval mutation, or pipeline launch.
        </span>
      </div>
    </article>
  `;
}

function renderManualGuardedApplicationExecutionLaunchRequestCreateSection(tracePayload = {}) {
  const result = hasAgentTraceSummaryObject(tracePayload?.manual_guarded_application_execution_launch_request_create_result)
    ? tracePayload.manual_guarded_application_execution_launch_request_create_result
    : {};
  const safety = hasAgentTraceSummaryObject(result.safety_metadata)
    ? result.safety_metadata
    : {};
  const preflight = hasAgentTraceSummaryObject(tracePayload?.manual_application_execution_preflight_checklist_result)
    ? tracePayload.manual_application_execution_preflight_checklist_result
    : {};
  const preflightAudit = hasAgentTraceSummaryObject(tracePayload?.manual_application_execution_preflight_observability_result)
    ? tracePayload.manual_application_execution_preflight_observability_result
    : {};
  const simulation = hasAgentTraceSummaryObject(tracePayload?.manual_application_execution_simulation_preview_result)
    ? tracePayload.manual_application_execution_simulation_preview_result
    : {};
  const readback = hasAgentTraceSummaryObject(tracePayload?.manual_execution_request_readback_result)
    ? tracePayload.manual_execution_request_readback_result
    : {};
  const agentRun = tracePayload?.agent_run && typeof tracePayload.agent_run === "object"
    ? tracePayload.agent_run
    : {};
  const metadata = agentRun?.metadata && typeof agentRun.metadata === "object" ? agentRun.metadata : {};
  const contextId = tracePayload?.agent_run_id || agentRun.agent_run_id || "";
  const jobId = metadata.job_id || metadata.merge_key || "";
  const approvalRequestId = result.approval_request_id || preflightAudit.approval_request_id || preflight.approval_request_id || simulation.approval_request_id || readback.approval_request_id || "";
  const queueHandoffId = result.queue_handoff_id || preflightAudit.queue_handoff_id || preflight.queue_handoff_id || simulation.queue_handoff_id || readback.queue_handoff_id || "";
  const executionRequestId = result.execution_request_id || preflightAudit.execution_request_id || preflight.execution_request_id || simulation.execution_request_id || readback.execution_request_id || "";
  return `
    <article class="agent-trace-summary" aria-label="Manual guarded application execution launch request creation">
      <div class="agentic-workflow-header">
        <div>
          <h4>Manual Guarded Execution Launch Request</h4>
          <p>Manual-only guarded launch request/control artifact creation after ready preflight evidence and explicit confirmation. It never executes or submits applications and does not update execution request status, approval status, resume content, scoring, or ranking.</p>
        </div>
        <span class="agentic-workflow-badge">Launch request</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Launch request", result.application_execution_launch_request_status || "not run")}
        ${renderWorkflowSummaryMetric("Execution request id", executionRequestId || "-")}
        ${renderWorkflowSummaryMetric("Approval id", approvalRequestId || "-")}
        ${renderWorkflowSummaryMetric("Queue handoff id", queueHandoffId || "-")}
        ${renderWorkflowSummaryMetric("Launch request id", result.execution_launch_request_id || "-")}
        ${renderWorkflowSummaryMetric("Created", result.execution_launch_request_created === true ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Execution", safety.did_execute_application ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Submission", safety.did_submit_application ? "yes" : "no")}
      </div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Source preflight status", result.source_application_execution_preflight_status || preflight.application_execution_preflight_status || "", { helper: "Source application execution preflight status." })}
        ${renderAgentTraceReadOnlyDetails("Source preflight audit status", result.source_application_execution_preflight_observability_status || preflightAudit.application_execution_preflight_observability_status || "", { helper: "Source application execution preflight audit status." })}
        ${renderAgentTraceReadOnlyDetails("Blocked actions", result.blocked_actions || [], { helper: "Guarded execution launch request blockers." })}
        ${renderAgentTraceReadOnlyDetails("Next safe step", result.next_safe_step || "", { helper: "Next safe manual step." })}
        ${renderAgentTraceReadOnlyDetails("Rationale", result.rationale || "", { helper: "Guarded execution launch request rationale." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable guarded execution launch request safety metadata." })}
      </div>
      <div class="agentic-review-actions">
        <label class="agentic-review-muted">
          <input type="checkbox" data-manual-guarded-application-execution-launch-request-create-confirmation>
          I explicitly confirm this guarded execution launch request.
        </label>
        <button type="button" class="agentic-feedback-action" data-manual-guarded-application-execution-launch-request-create data-approval-request-id="${escapeHtml(approvalRequestId)}" data-queue-handoff-id="${escapeHtml(queueHandoffId)}" data-execution-request-id="${escapeHtml(executionRequestId)}" data-context-id="${escapeHtml(contextId)}" data-job-id="${escapeHtml(jobId)}">
          Create Guarded Execution Launch Request
        </button>
        <span class="agentic-review-muted" data-manual-guarded-application-execution-launch-request-create-status>
          Manual only. This requires explicit confirmation and will block unless an existing execution-launch-request writer is configured.
        </span>
      </div>
    </article>
  `;
}

function renderManualGuardedApplicationExecutionLaunchRequestObservabilitySection(tracePayload = {}) {
  const result = hasAgentTraceSummaryObject(tracePayload?.manual_guarded_application_execution_launch_request_observability_result)
    ? tracePayload.manual_guarded_application_execution_launch_request_observability_result
    : {};
  const launchResult = hasAgentTraceSummaryObject(tracePayload?.manual_guarded_application_execution_launch_request_create_result)
    ? tracePayload.manual_guarded_application_execution_launch_request_create_result
    : {};
  const safety = hasAgentTraceSummaryObject(result.safety_metadata)
    ? result.safety_metadata
    : {};
  const executionLaunchRequestId = result.execution_launch_request_id || launchResult.execution_launch_request_id || "";
  const executionRequestId = result.execution_request_id || launchResult.execution_request_id || "";
  const approvalRequestId = result.approval_request_id || launchResult.approval_request_id || "";
  const queueHandoffId = result.queue_handoff_id || launchResult.queue_handoff_id || "";
  const agentRun = tracePayload?.agent_run && typeof tracePayload.agent_run === "object"
    ? tracePayload.agent_run
    : {};
  const metadata = agentRun?.metadata && typeof agentRun.metadata === "object" ? agentRun.metadata : {};
  const contextId = tracePayload?.agent_run_id || agentRun.agent_run_id || result.context_id || launchResult.context_id || "";
  const jobId = metadata.job_id || metadata.merge_key || result.job_id || launchResult.job_id || "";
  return `
    <article class="agent-trace-summary" aria-label="Manual guarded application execution launch request audit">
      <div class="agentic-workflow-header">
        <div>
          <h4>Manual Execution Launch Request Audit</h4>
          <p>Read-only audit/readback for the guarded execution launch request result. It creates no launch request, writes no queue file, updates no status, and never executes or submits applications.</p>
        </div>
        <span class="agentic-workflow-badge">Audit</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Audit", result.application_execution_launch_request_observability_status || "not run")}
        ${renderWorkflowSummaryMetric("Source", result.source_application_execution_launch_request_status || launchResult.application_execution_launch_request_status || "-")}
        ${renderWorkflowSummaryMetric("Launch request id", executionLaunchRequestId || "-")}
        ${renderWorkflowSummaryMetric("Execution request id", executionRequestId || "-")}
        ${renderWorkflowSummaryMetric("Approval id", approvalRequestId || "-")}
        ${renderWorkflowSummaryMetric("Queue handoff id", queueHandoffId || "-")}
        ${renderWorkflowSummaryMetric("Created", result.execution_launch_request_was_created === true ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Blocked", result.execution_launch_request_was_blocked === true ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Execution", safety.did_execute_application ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Submission", safety.did_submit_application ? "yes" : "no")}
      </div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Audit summary", result.audit_summary || {}, { helper: "Read-only guarded execution launch request audit summary." })}
        ${renderAgentTraceReadOnlyDetails("Audit events", result.audit_events || [], { helper: "In-memory audit observations for the guarded execution launch request result." })}
        ${renderAgentTraceReadOnlyDetails("Safety findings", result.safety_findings || {}, { helper: "Safety findings from read-only launch request audit." })}
        ${renderAgentTraceReadOnlyDetails("Blocked actions", result.blocked_actions || launchResult.blocked_actions || [], { helper: "Observed launch request blockers." })}
        ${renderAgentTraceReadOnlyDetails("Next safe step", result.next_safe_step || launchResult.next_safe_step || "", { helper: "Next safe manual step." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable launch request audit safety metadata." })}
      </div>
      <div class="agentic-review-actions">
        <button type="button" class="agentic-feedback-action" data-manual-guarded-application-execution-launch-request-observability data-execution-launch-request-id="${escapeHtml(executionLaunchRequestId)}" data-approval-request-id="${escapeHtml(approvalRequestId)}" data-queue-handoff-id="${escapeHtml(queueHandoffId)}" data-execution-request-id="${escapeHtml(executionRequestId)}" data-context-id="${escapeHtml(contextId)}" data-job-id="${escapeHtml(jobId)}">
          View Execution Launch Request Audit
        </button>
        <span class="agentic-review-muted" data-manual-guarded-application-execution-launch-request-observability-status>
          Manual read-only audit. This does not create launch requests, update queue/status records, execute, submit, or launch the pipeline.
        </span>
      </div>
    </article>
  `;
}

function renderManualApplicationExecutionLaunchRequestReadbackSection(tracePayload = {}) {
  const result = hasAgentTraceSummaryObject(tracePayload?.manual_application_execution_launch_request_readback_result)
    ? tracePayload.manual_application_execution_launch_request_readback_result
    : {};
  const launchResult = hasAgentTraceSummaryObject(tracePayload?.manual_guarded_application_execution_launch_request_create_result)
    ? tracePayload.manual_guarded_application_execution_launch_request_create_result
    : {};
  const auditResult = hasAgentTraceSummaryObject(tracePayload?.manual_guarded_application_execution_launch_request_observability_result)
    ? tracePayload.manual_guarded_application_execution_launch_request_observability_result
    : {};
  const safety = hasAgentTraceSummaryObject(result.safety_metadata)
    ? result.safety_metadata
    : {};
  const executionLaunchRequestId = result.execution_launch_request_id || auditResult.execution_launch_request_id || launchResult.execution_launch_request_id || "";
  const executionRequestId = result.execution_request_id || auditResult.execution_request_id || launchResult.execution_request_id || "";
  const approvalRequestId = result.approval_request_id || auditResult.approval_request_id || launchResult.approval_request_id || "";
  const queueHandoffId = result.queue_handoff_id || auditResult.queue_handoff_id || launchResult.queue_handoff_id || "";
  const agentRun = tracePayload?.agent_run && typeof tracePayload.agent_run === "object"
    ? tracePayload.agent_run
    : {};
  const metadata = agentRun?.metadata && typeof agentRun.metadata === "object" ? agentRun.metadata : {};
  const contextId = tracePayload?.agent_run_id || agentRun.agent_run_id || result.context_id || auditResult.context_id || launchResult.context_id || "";
  const jobId = metadata.job_id || metadata.merge_key || result.job_id || auditResult.job_id || launchResult.job_id || "";
  return `
    <article class="agent-trace-summary" aria-label="Manual application execution launch request readback">
      <div class="agentic-workflow-header">
        <div>
          <h4>Manual Execution Launch Request Readback</h4>
          <p>Read-only detail view for the guarded execution launch request/control artifact, based only on the provided manual create and audit payloads.</p>
        </div>
        <span class="agentic-workflow-badge">Readback</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Readback", result.application_execution_launch_request_readback_status || "not run")}
        ${renderWorkflowSummaryMetric("Execution launch request found", result.execution_launch_request_found === true ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Launch request id", executionLaunchRequestId || "-")}
        ${renderWorkflowSummaryMetric("Execution request id", executionRequestId || "-")}
        ${renderWorkflowSummaryMetric("Approval id", approvalRequestId || "-")}
        ${renderWorkflowSummaryMetric("Queue handoff id", queueHandoffId || "-")}
        ${renderWorkflowSummaryMetric("Execution", safety.did_execute_application ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Submission", safety.did_submit_application ? "yes" : "no")}
      </div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Source launch request status", result.source_application_execution_launch_request_status || launchResult.application_execution_launch_request_status || "", { helper: "Source guarded application execution launch request status." })}
        ${renderAgentTraceReadOnlyDetails("Source launch request audit status", result.source_application_execution_launch_request_observability_status || auditResult.application_execution_launch_request_observability_status || "", { helper: "Source guarded execution launch request audit status." })}
        ${renderAgentTraceReadOnlyDetails("Readback summary", result.readback_summary || {}, { helper: "Normalized read-only execution launch request detail summary." })}
        ${renderAgentTraceReadOnlyDetails("Detail sections", result.detail_sections || [], { helper: "Compact read-only execution launch request detail sections." })}
        ${renderAgentTraceReadOnlyDetails("Missing requirements", result.missing_requirements || [], { helper: "Missing readback requirements." })}
        ${renderAgentTraceReadOnlyDetails("Blocked actions", result.blocked_actions || [], { helper: "Readback blockers." })}
        ${renderAgentTraceReadOnlyDetails("Next safe step", result.next_safe_step || "", { helper: "Next safe manual step." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable execution launch request readback safety metadata." })}
      </div>
      <div class="agentic-review-actions">
        <button type="button" class="agentic-feedback-action" data-manual-application-execution-launch-request-readback data-execution-launch-request-id="${escapeHtml(executionLaunchRequestId)}" data-approval-request-id="${escapeHtml(approvalRequestId)}" data-queue-handoff-id="${escapeHtml(queueHandoffId)}" data-execution-request-id="${escapeHtml(executionRequestId)}" data-context-id="${escapeHtml(contextId)}" data-job-id="${escapeHtml(jobId)}">
          Read Execution Launch Request
        </button>
        <span class="agentic-review-muted" data-manual-application-execution-launch-request-readback-status>
          Manual read-only detail view. This uses provided source evidence only and does not create, write, execute, submit, or launch the pipeline.
        </span>
      </div>
    </article>
  `;
}

function renderManualExecutionLaunchRequestStatusTransitionPreviewSection(tracePayload = {}) {
  const result = hasAgentTraceSummaryObject(tracePayload?.manual_execution_launch_request_status_transition_preview_result)
    ? tracePayload.manual_execution_launch_request_status_transition_preview_result
    : {};
  const readback = hasAgentTraceSummaryObject(tracePayload?.manual_application_execution_launch_request_readback_result)
    ? tracePayload.manual_application_execution_launch_request_readback_result
    : {};
  const launchResult = hasAgentTraceSummaryObject(tracePayload?.manual_guarded_application_execution_launch_request_create_result)
    ? tracePayload.manual_guarded_application_execution_launch_request_create_result
    : {};
  const auditResult = hasAgentTraceSummaryObject(tracePayload?.manual_guarded_application_execution_launch_request_observability_result)
    ? tracePayload.manual_guarded_application_execution_launch_request_observability_result
    : {};
  const safety = hasAgentTraceSummaryObject(result.safety_metadata)
    ? result.safety_metadata
    : {};
  const executionLaunchRequestId = result.execution_launch_request_id || readback.execution_launch_request_id || auditResult.execution_launch_request_id || launchResult.execution_launch_request_id || "";
  const executionRequestId = result.execution_request_id || readback.execution_request_id || auditResult.execution_request_id || launchResult.execution_request_id || "";
  const approvalRequestId = result.approval_request_id || readback.approval_request_id || auditResult.approval_request_id || launchResult.approval_request_id || "";
  const queueHandoffId = result.queue_handoff_id || readback.queue_handoff_id || auditResult.queue_handoff_id || launchResult.queue_handoff_id || "";
  const selectedTransition = result.requested_transition || "ready_for_manual_execution";
  const agentRun = tracePayload?.agent_run && typeof tracePayload.agent_run === "object"
    ? tracePayload.agent_run
    : {};
  const metadata = agentRun?.metadata && typeof agentRun.metadata === "object" ? agentRun.metadata : {};
  const contextId = tracePayload?.agent_run_id || agentRun.agent_run_id || result.context_id || readback.context_id || "";
  const jobId = metadata.job_id || metadata.merge_key || result.job_id || readback.job_id || "";
  const transitionOptions = [
    ["ready_for_manual_execution", "Ready for manual execution"],
    ["needs_changes", "Needs changes"],
    ["cancelled", "Cancelled"],
    ["keep_pending_review", "Keep pending review"],
  ].map(([value, label]) => `<option value="${escapeHtml(value)}"${selectedTransition === value ? " selected" : ""}>${escapeHtml(label)}</option>`).join("");
  return `
    <article class="agent-trace-summary" aria-label="Manual execution launch request status transition preview">
      <div class="agentic-workflow-header">
        <div>
          <h4>Manual Execution Launch Request Status Preview</h4>
          <p>Dry-run preview for a future guarded status transition on the execution launch request/control artifact. It updates no status and never executes or submits applications.</p>
        </div>
        <span class="agentic-workflow-badge">Preview</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Preview", result.execution_launch_request_status_transition_preview_status || "not run")}
        ${renderWorkflowSummaryMetric("Launch request id", executionLaunchRequestId || "-")}
        ${renderWorkflowSummaryMetric("Requested transition", result.requested_transition || "-")}
        ${renderWorkflowSummaryMetric("Current status", result.current_execution_launch_request_status || readback.execution_launch_request_status || "-")}
        ${renderWorkflowSummaryMetric("Proposed status", result.proposed_execution_launch_request_status || "-")}
        ${renderWorkflowSummaryMetric("Transition allowed", result.transition_allowed === true ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Execution", safety.did_execute_application ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Submission", safety.did_submit_application ? "yes" : "no")}
      </div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Transition reason", result.transition_reason || "", { helper: "Read-only transition preview rationale." })}
        ${renderAgentTraceReadOnlyDetails("Missing requirements", result.missing_requirements || [], { helper: "Missing transition preview requirements." })}
        ${renderAgentTraceReadOnlyDetails("Blocked actions", result.blocked_actions || [], { helper: "Transition preview blockers." })}
        ${renderAgentTraceReadOnlyDetails("Next safe step", result.next_safe_step || "", { helper: "Next safe manual step." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable transition preview safety metadata." })}
      </div>
      <div class="agentic-review-actions">
        <label class="agentic-review-muted">
          Transition
          <select data-manual-execution-launch-request-status-transition-preview-select>
            ${transitionOptions}
          </select>
        </label>
        <button type="button" class="agentic-feedback-action" data-manual-execution-launch-request-status-transition-preview data-execution-launch-request-id="${escapeHtml(executionLaunchRequestId)}" data-approval-request-id="${escapeHtml(approvalRequestId)}" data-queue-handoff-id="${escapeHtml(queueHandoffId)}" data-execution-request-id="${escapeHtml(executionRequestId)}" data-context-id="${escapeHtml(contextId)}" data-job-id="${escapeHtml(jobId)}">
          Preview Execution Launch Request Status Transition
        </button>
        <span class="agentic-review-muted" data-manual-execution-launch-request-status-transition-preview-status>
          Manual dry-run only. This previews a future status change and does not update status, execute, submit, write queue files, or launch the pipeline.
        </span>
      </div>
    </article>
  `;
}

function renderManualGuardedExecutionLaunchRequestStatusTransitionSection(tracePayload = {}) {
  const result = hasAgentTraceSummaryObject(tracePayload?.manual_guarded_execution_launch_request_status_transition_result)
    ? tracePayload.manual_guarded_execution_launch_request_status_transition_result
    : {};
  const preview = hasAgentTraceSummaryObject(tracePayload?.manual_execution_launch_request_status_transition_preview_result)
    ? tracePayload.manual_execution_launch_request_status_transition_preview_result
    : {};
  const readback = hasAgentTraceSummaryObject(tracePayload?.manual_application_execution_launch_request_readback_result)
    ? tracePayload.manual_application_execution_launch_request_readback_result
    : {};
  const safety = hasAgentTraceSummaryObject(result.safety_metadata)
    ? result.safety_metadata
    : {};
  const executionLaunchRequestId = result.execution_launch_request_id || preview.execution_launch_request_id || readback.execution_launch_request_id || "";
  const executionRequestId = result.execution_request_id || preview.execution_request_id || readback.execution_request_id || "";
  const approvalRequestId = result.approval_request_id || preview.approval_request_id || readback.approval_request_id || "";
  const queueHandoffId = result.queue_handoff_id || preview.queue_handoff_id || readback.queue_handoff_id || "";
  const requestedTransition = result.requested_transition || preview.requested_transition || "ready_for_manual_execution";
  const agentRun = tracePayload?.agent_run && typeof tracePayload.agent_run === "object"
    ? tracePayload.agent_run
    : {};
  const metadata = agentRun?.metadata && typeof agentRun.metadata === "object" ? agentRun.metadata : {};
  const contextId = tracePayload?.agent_run_id || agentRun.agent_run_id || result.context_id || preview.context_id || "";
  const jobId = metadata.job_id || metadata.merge_key || result.job_id || preview.job_id || "";
  return `
    <article class="agent-trace-summary" aria-label="Manual guarded execution launch request status transition">
      <div class="agentic-workflow-header">
        <div>
          <h4>Manual Guarded Execution Launch Request Status Transition</h4>
          <p>Manual guarded launch request status update only. It requires a ready preview and explicit confirmation, and never executes, submits, updates execution request status, approval status, resume content, scoring, or ranking.</p>
        </div>
        <span class="agentic-workflow-badge">Guarded launch status</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Transition status", result.execution_launch_request_status_transition_status || "not run")}
        ${renderWorkflowSummaryMetric("Launch request id", executionLaunchRequestId || "-")}
        ${renderWorkflowSummaryMetric("Requested", requestedTransition || "-")}
        ${renderWorkflowSummaryMetric("Updated", result.execution_launch_request_status_updated === true ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Previous", result.previous_execution_launch_request_status || "-")}
        ${renderWorkflowSummaryMetric("New", result.new_execution_launch_request_status || "-")}
        ${renderWorkflowSummaryMetric("Status updated", safety.did_update_execution_launch_request_status ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Execution", safety.did_execute_application ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Submission", safety.did_submit_application ? "yes" : "no")}
      </div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Blocked actions", result.blocked_actions || [], { helper: "Guarded execution launch request status blockers." })}
        ${renderAgentTraceReadOnlyDetails("Source transition preview status", result.source_transition_preview_status || "", { helper: "Source launch request transition preview status." })}
        ${renderAgentTraceReadOnlyDetails("Next safe step", result.next_safe_step || "", { helper: "Next safe manual step." })}
        ${renderAgentTraceReadOnlyDetails("Rationale", result.rationale || "", { helper: "Guarded execution launch request status transition rationale." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable guarded execution launch request status transition safety metadata." })}
      </div>
      <div class="agentic-review-actions">
        <label class="agentic-review-muted">
          <input type="checkbox" data-manual-guarded-execution-launch-request-status-transition-confirmation>
          I explicitly confirm this guarded execution launch request status transition.
        </label>
        <button type="button" class="agentic-feedback-action" data-manual-guarded-execution-launch-request-status-transition data-execution-launch-request-id="${escapeHtml(executionLaunchRequestId)}" data-approval-request-id="${escapeHtml(approvalRequestId)}" data-queue-handoff-id="${escapeHtml(queueHandoffId)}" data-execution-request-id="${escapeHtml(executionRequestId)}" data-requested-transition="${escapeHtml(requestedTransition)}" data-context-id="${escapeHtml(contextId)}" data-job-id="${escapeHtml(jobId)}">
          Apply Guarded Execution Launch Request Status
        </button>
        <span class="agentic-review-muted" data-manual-guarded-execution-launch-request-status-transition-status>
          Manual only. This requires explicit confirmation and will block unless an existing launch-request status writer is configured.
        </span>
      </div>
    </article>
  `;
}

function renderManualGuardedExecutionLaunchRequestStatusTransitionObservabilitySection(tracePayload = {}) {
  const result = hasAgentTraceSummaryObject(tracePayload?.manual_guarded_execution_launch_request_status_transition_observability_result)
    ? tracePayload.manual_guarded_execution_launch_request_status_transition_observability_result
    : {};
  const transition = hasAgentTraceSummaryObject(tracePayload?.manual_guarded_execution_launch_request_status_transition_result)
    ? tracePayload.manual_guarded_execution_launch_request_status_transition_result
    : {};
  const preview = hasAgentTraceSummaryObject(tracePayload?.manual_execution_launch_request_status_transition_preview_result)
    ? tracePayload.manual_execution_launch_request_status_transition_preview_result
    : {};
  const safety = hasAgentTraceSummaryObject(result.safety_metadata)
    ? result.safety_metadata
    : {};
  const executionLaunchRequestId = result.execution_launch_request_id || transition.execution_launch_request_id || preview.execution_launch_request_id || "";
  const executionRequestId = result.execution_request_id || transition.execution_request_id || preview.execution_request_id || "";
  const approvalRequestId = result.approval_request_id || transition.approval_request_id || preview.approval_request_id || "";
  const queueHandoffId = result.queue_handoff_id || transition.queue_handoff_id || preview.queue_handoff_id || "";
  const requestedTransition = result.requested_transition || transition.requested_transition || preview.requested_transition || "";
  const agentRun = tracePayload?.agent_run && typeof tracePayload.agent_run === "object"
    ? tracePayload.agent_run
    : {};
  const metadata = agentRun?.metadata && typeof agentRun.metadata === "object" ? agentRun.metadata : {};
  const contextId = tracePayload?.agent_run_id || agentRun.agent_run_id || result.context_id || transition.context_id || "";
  const jobId = metadata.job_id || metadata.merge_key || result.job_id || transition.job_id || "";
  return `
    <article class="agent-trace-summary" aria-label="Manual guarded execution launch request status audit">
      <div class="agentic-workflow-header">
        <div>
          <h4>Manual Execution Launch Status Audit</h4>
          <p>Read-only audit/readback for the guarded execution launch request status transition result. It updates no status and never executes, submits, writes queue files, or launches the pipeline.</p>
        </div>
        <span class="agentic-workflow-badge">Audit</span>
      </div>
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Audit", result.execution_launch_request_status_transition_observability_status || "not run")}
        ${renderWorkflowSummaryMetric("Launch request id", executionLaunchRequestId || "-")}
        ${renderWorkflowSummaryMetric("Requested", requestedTransition || "-")}
        ${renderWorkflowSummaryMetric("Previous", result.previous_execution_launch_request_status || transition.previous_execution_launch_request_status || "-")}
        ${renderWorkflowSummaryMetric("New", result.new_execution_launch_request_status || transition.new_execution_launch_request_status || "-")}
        ${renderWorkflowSummaryMetric("Status updated", result.execution_launch_request_status_updated === true ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Applied", result.execution_launch_request_status_transition_was_applied === true ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Blocked", result.execution_launch_request_status_transition_was_blocked === true ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Execution", safety.did_execute_application ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Submission", safety.did_submit_application ? "yes" : "no")}
      </div>
      <div class="agent-trace-json-grid">
        ${renderAgentTraceReadOnlyDetails("Audit summary", result.audit_summary || {}, { helper: "Read-only guarded execution launch status audit summary." })}
        ${renderAgentTraceReadOnlyDetails("Audit events", result.audit_events || [], { helper: "In-memory audit observations for guarded execution launch status transition." })}
        ${renderAgentTraceReadOnlyDetails("Safety findings", result.safety_findings || {}, { helper: "Safety findings from read-only launch status audit." })}
        ${renderAgentTraceReadOnlyDetails("Blocked actions", result.blocked_actions || transition.blocked_actions || [], { helper: "Observed launch status transition blockers." })}
        ${renderAgentTraceReadOnlyDetails("Next safe step", result.next_safe_step || transition.next_safe_step || "", { helper: "Next safe manual step." })}
        ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable guarded execution launch status audit safety metadata." })}
      </div>
      <div class="agentic-review-actions">
        <button type="button" class="agentic-feedback-action" data-manual-guarded-execution-launch-request-status-transition-observability data-execution-launch-request-id="${escapeHtml(executionLaunchRequestId)}" data-approval-request-id="${escapeHtml(approvalRequestId)}" data-queue-handoff-id="${escapeHtml(queueHandoffId)}" data-execution-request-id="${escapeHtml(executionRequestId)}" data-context-id="${escapeHtml(contextId)}" data-job-id="${escapeHtml(jobId)}">
          View Execution Launch Status Audit
        </button>
        <span class="agentic-review-muted" data-manual-guarded-execution-launch-request-status-transition-observability-status>
          Manual read-only audit. This does not update status, execute, submit, write queue files, or launch the pipeline.
        </span>
      </div>
    </article>
  `;
}

function renderAgentTraceReadOnlyPanel(tracePayload = {}) {
  const loadingState = Boolean(tracePayload?.loading_state);
  const found = Boolean(tracePayload?.found);
  const steps = Array.isArray(tracePayload?.agent_steps) ? tracePayload.agent_steps : [];
  const stepCount = Number(tracePayload?.step_count ?? steps.length);
  const emptyTrace = Boolean(tracePayload?.empty_trace);
  const agentRun = tracePayload?.agent_run && typeof tracePayload.agent_run === "object"
    ? tracePayload.agent_run
    : {};
  const safety = tracePayload?.safety_metadata && typeof tracePayload.safety_metadata === "object"
    ? tracePayload.safety_metadata
    : {};
  const safeError = String(tracePayload?.read_only_error || "").trim();
  const stateLabel = loadingState
    ? "loading state"
    : safeError
      ? "fetch failure"
      : !found
        ? "not found trace"
        : emptyTrace
          ? "empty trace"
          : "ordered agent steps";
  const notFoundMessage = !found
    ? "No persisted trace found for this run. The trace panel is read-only and will show ordered agent steps when trace records are available."
    : "";
  const emptyMessage = found && emptyTrace
    ? "Empty trace: agent run metadata is available, but no ordered agent steps were returned. The read-only display remains deterministic."
    : "";
  return `
    <section id="agenticReviewTracePanel" class="pipeline-run-detail-panel agent-trace-panel" data-agent-trace-read-only-panel aria-label="Read-only agent trace panel with accessibility labels">
      <div class="agentic-workflow-header">
        <div>
          <h4>Agent Trace</h4>
          <p>Read-only trace panel. Uses GET only and never changes approvals, queues, scoring, execution, or submissions.</p>
          <p class="agentic-review-muted">Accessibility labels, loading state, empty trace, not found trace, fetch failure, collapsed step details, safety metadata, and validation_json are display-only polish.</p>
        </div>
        <span class="agentic-workflow-badge">Read-only</span>
      </div>
      ${loadingState ? renderAgentTraceReadOnlyState("Loading state: fetching read-only agent trace details with GET only.", "info", "Agent trace loading state") : ""}
      ${safeError ? renderAgentTraceReadOnlyState(`Fetch failure: ${safeError} Read-only display preserved.`, "error", "Agent trace fetch failure") : ""}
      <div class="agent-trace-counts">
        ${renderWorkflowSummaryMetric("Trace state", stateLabel)}
        ${stepCount > 0 ? renderWorkflowSummaryMetric("Step count", stepCount) : ""}
      </div>
      ${renderAgentTraceEvidencePackSection(tracePayload?.trace_evidence_pack)}
      ${renderShadowSidecarTraceReadbackSection(tracePayload)}
      ${renderShadowSidecarScoreComparisonSection(tracePayload)}
      ${renderHumanReviewedInfluencePreviewSection(tracePayload)}
      ${renderHumanReviewedInfluenceApprovalRequestSection(tracePayload)}
      ${renderAgentRecommendationOverlaySection(tracePayload)}
      ${renderAgentTraceCriticEvaluatorSection(tracePayload)}
      ${renderManualJdIntelligenceDryRunSection(tracePayload)}
      ${renderManualResumeMatchDryRunSection(tracePayload)}
      ${renderManualTailoringSuggestionDryRunSection(tracePayload)}
      ${renderManualCriticGuardrailDryRunSection(tracePayload)}
      ${renderManualStrategyRecommendationDryRunSection(tracePayload)}
      ${renderManualShadowAgenticWorkflowChainDryRunSection(tracePayload)}
      ${renderManualShadowRecommendationHandoffDryRunSection(tracePayload)}
      ${renderManualHumanDecisionCaptureDryRunSection(tracePayload)}
      ${renderManualHumanApprovedActionPlanDryRunSection(tracePayload)}
      ${renderManualReviewPacketPreviewDryRunSection(tracePayload)}
      ${renderManualApprovalRequestPreviewDryRunSection(tracePayload)}
      ${renderManualApprovalCreationGateDryRunSection(tracePayload)}
      ${renderManualGuardedApprovalRequestCreateSection(tracePayload)}
      ${renderManualGuardedApprovalCreationObservabilitySection(tracePayload)}
      ${renderManualApprovalRequestReadbackSection(tracePayload)}
      ${renderManualApprovalStatusTransitionPreviewSection(tracePayload)}
      ${renderManualGuardedApprovalStatusTransitionSection(tracePayload)}
      ${renderManualApprovalStatusTransitionObservabilitySection(tracePayload)}
      ${renderManualQueueHandoffReadinessPreviewSection(tracePayload)}
      ${renderManualGuardedQueueHandoffCreateSection(tracePayload)}
      ${renderManualQueueHandoffCreationObservabilitySection(tracePayload)}
      ${renderManualExecutionReadinessPreviewSection(tracePayload)}
      ${renderManualExecutionLaunchGatePreviewSection(tracePayload)}
      ${renderManualExecutionLaunchGateObservabilitySection(tracePayload)}
      ${renderManualExecutionRequestPacketPreviewSection(tracePayload)}
      ${renderManualGuardedExecutionRequestCreateSection(tracePayload)}
      ${renderManualGuardedExecutionRequestObservabilitySection(tracePayload)}
      ${renderManualExecutionRequestReadbackSection(tracePayload)}
      ${renderManualExecutionRequestStatusTransitionPreviewSection(tracePayload)}
      ${renderManualGuardedExecutionRequestStatusTransitionSection(tracePayload)}
      ${renderManualGuardedExecutionRequestStatusTransitionObservabilitySection(tracePayload)}
      ${renderManualApplicationExecutionSimulationPreviewSection(tracePayload)}
      ${renderManualApplicationExecutionSimulationObservabilitySection(tracePayload)}
      ${renderManualApplicationExecutionPreflightChecklistSection(tracePayload)}
      ${renderManualApplicationExecutionPreflightObservabilitySection(tracePayload)}
      ${renderManualGuardedApplicationExecutionLaunchRequestCreateSection(tracePayload)}
      ${renderManualGuardedApplicationExecutionLaunchRequestObservabilitySection(tracePayload)}
      ${renderManualApplicationExecutionLaunchRequestReadbackSection(tracePayload)}
      ${renderManualExecutionLaunchRequestStatusTransitionPreviewSection(tracePayload)}
      ${renderManualGuardedExecutionLaunchRequestStatusTransitionSection(tracePayload)}
      ${renderManualGuardedExecutionLaunchRequestStatusTransitionObservabilitySection(tracePayload)}
      ${renderAgentTraceDetailedSections(tracePayload)}
      ${notFoundMessage && !loadingState ? renderAgentTraceReadOnlyState(notFoundMessage, "info", "Agent trace not found trace") : ""}
      ${emptyMessage && !loadingState ? renderAgentTraceReadOnlyState(emptyMessage, "info", "Agent trace empty trace") : ""}
      <details class="agent-trace-debug-details" data-collapsed-by-default="true">
        <summary>Debug details</summary>
        <div class="agent-trace-counts">
          ${renderWorkflowSummaryMetric("Found", found ? "true" : "false")}
          ${renderWorkflowSummaryMetric("Step count", stepCount)}
          ${renderWorkflowSummaryMetric("Empty trace", emptyTrace ? "true" : "false")}
          ${renderWorkflowSummaryMetric("Read-only", safety.read_only === true ? "true" : "unknown")}
        </div>
      </details>
      ${found && !loadingState ? `
        <article class="agent-trace-run" aria-label="Read-only agent trace run metadata">
          <div class="agent-trace-run-header">
            <div>
              <div class="agent-trace-run-id">${escapeHtml(agentRun.agent_run_id || "Agent run")}</div>
              <div class="agent-trace-step-meta">
                ${escapeHtml(agentRun.agent_name || "-")} · ${escapeHtml(agentRun.run_status || agentRun.status || "-")}
              </div>
            </div>
            ${renderReviewPill(agentRun.run_status || agentRun.status || "unknown")}
          </div>
          <div class="agent-trace-step-times">
            ${escapeHtml(agentRun.observed_at_utc || agentRun.started_at || "Timestamp unavailable")}
            ${agentRun.completed_at ? ` -> ${escapeHtml(agentRun.completed_at)}` : ""}
          </div>
          <div class="agentic-review-muted">Long trace readability is supported by collapsed step details and readable metadata summaries.</div>
          <div class="agent-trace-json-grid">
            ${renderAgentTraceReadOnlyDetails("Agent run metadata", agentRun.metadata || agentRun.summary_json, { helper: "Read-only agent run metadata." })}
            ${renderAgentTraceReadOnlyDetails("Safety metadata", safety, { helper: "Readable safety metadata display." })}
          </div>
          <div class="agent-trace-step-list" aria-label="Read-only ordered agent steps list">
            ${steps.length
              ? steps.map(renderAgentTraceReadOnlyStep).join("")
              : renderAgentTraceReadOnlyState("No ordered agent steps returned for this trace. Empty trace: no ordered agent steps returned for this trace.", "info", "Agent trace empty trace")}
          </div>
        </article>
      ` : ""}
    </section>
  `;
}

function renderAgentTracePanel(tracePayload = {}) {
  return renderAgentTraceReadOnlyPanel(tracePayload);
}

function getAgenticReviewApprovalRequestId(payload = {}) {
  return getAgenticApprovalRequestId(payload?.operator_approval_mock || {});
}

async function fetchAgentTraceReadOnlyPayload(payload = {}, runId = getAgenticReviewRunId()) {
  const approvalRequestId = getAgenticReviewApprovalRequestId(payload);
  if (approvalRequestId) {
    return fetchJson(`/api/agentic-approvals/${encodeURIComponent(approvalRequestId)}/agent-trace`);
  }
  if (runId) {
    return fetchJson(`/profile/pipeline-runs/${encodeURIComponent(runId)}/agent-trace?include_trace_summary=1&include_stage_trace_bundle=1&include_stage_trace_health=1&include_stage_trace_readiness=1&include_trace_evidence_pack=1`);
  }
  return {};
}

async function refreshAgenticReviewFeedbackSummary(runId = getAgenticReviewRunId()) {
  const safeRunId = String(runId || "").trim();
  if (!safeRunId) return;
  try {
    const feedbackPayload = await fetchJson(`/api/agent-feedback/summary?pipeline_run_id=${encodeURIComponent(safeRunId)}&limit=50`);
    const card = document.querySelector(".agentic-feedback-card");
    if (card) {
      card.outerHTML = renderAgenticReviewFeedbackSection(feedbackPayload || {});
    }
  } catch {
    // Keep the page responsive; the explicit click already reported success/failure.
  }
}

function setAgenticReviewFeedbackStatus(message, tone = "info") {
  const status = document.querySelector("[data-agentic-feedback-status]");
  if (!status) return;
  status.textContent = message || "";
  status.className = `agentic-feedback-status is-${tone}`;
}

async function recordAgenticReviewFeedback(eventType, button) {
  const runId = getAgenticReviewRunId();
  if (!runId || !eventType) return;
  const previousDisabled = Boolean(button?.disabled);
  if (button) button.disabled = true;
  setAgenticReviewFeedbackStatus("Recording feedback...", "info");
  try {
    await fetchJson("/api/agent-feedback", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        pipeline_run_id: runId,
        target_type: "agentic_review_section",
        target_id: runId,
        event_type: eventType,
        payload_json: {
          action: eventType === AGENTIC_REVIEW_FEEDBACK_EVENTS.helpful ? "mark_review_useful" : "mark_review_not_useful",
          section: "human_feedback",
        },
        source: "agentic_review_ui",
      }),
    });
    setAgenticReviewFeedbackStatus("Feedback recorded.", "success");
    await refreshAgenticReviewFeedbackSummary(runId);
  } catch (err) {
    setAgenticReviewFeedbackStatus(err?.message || "Could not record feedback.", "error");
  } finally {
    if (button) {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  }
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
      ${renderAgenticWorkflowMarkdownSummary("Manifest", markdown)}
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
      ${renderAgenticWorkflowMarkdownSummary("Execution plan", markdown)}
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
      ${renderAgenticWorkflowMarkdownSummary("Dry-run report", markdown)}
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

function renderReadOnlyAdapterPreflightSection(readOnlyAdapterPreflight = {}) {
  const available = Boolean(readOnlyAdapterPreflight?.available);
  const plan = readOnlyAdapterPreflight?.plan_json && typeof readOnlyAdapterPreflight.plan_json === "object"
    ? readOnlyAdapterPreflight.plan_json
    : {};
  const markdown = String(readOnlyAdapterPreflight?.report_markdown || "");
  if (!available && !Object.keys(plan).length) {
    return `
      <section class="read-only-adapter-preflight-card">
        <div class="agentic-workflow-header">
          <div>
            <h2>Read-Only Adapter Preflight</h2>
            <p>The adapter preflight artifact was not recorded for this run. Missing preflight diagnostics do not affect planning results.</p>
          </div>
          <span class="agentic-workflow-verification-status agentic-workflow-verification-status--unknown">Missing</span>
        </div>
        <div class="pipeline-runs-empty-cell">No read-only adapter preflight recorded for this run.</div>
      </section>
    `;
  }

  const validation = plan.validation && typeof plan.validation === "object" ? plan.validation : {};
  const summary = plan.summary && typeof plan.summary === "object" ? plan.summary : {};
  const validationStatus = String(validation.validation_status || "unknown").toLowerCase();
  const results = Array.isArray(plan.adapter_preflight_results) ? plan.adapter_preflight_results : [];

  return `
    <section class="read-only-adapter-preflight-card">
      <div class="agentic-workflow-header">
        <div>
          <h2>Read-Only Adapter Preflight</h2>
          <p>Preflight-only diagnostics. No agents execute, autonomous execution remains disabled, and production decisions are unchanged.</p>
        </div>
        <span class="agentic-workflow-verification-status agentic-workflow-verification-status--${escapeHtml(validationStatus)}">
          ${escapeHtml(formatWorkflowVerificationStatus(validationStatus))}
        </span>
      </div>
      <div class="read-only-adapter-preflight-metrics">
        ${renderWorkflowSummaryMetric("Execution mode", plan.execution_mode || "-")}
        ${renderWorkflowSummaryMetric("Validation", formatWorkflowVerificationStatus(validationStatus))}
        ${renderWorkflowSummaryMetric("Planned", plan.planned_adapter_count ?? results.length)}
        ${renderWorkflowSummaryMetric("Executable", plan.executable_adapter_count ?? 0)}
        ${renderWorkflowSummaryMetric("Ready", summary.ready_read_only_contract_count ?? 0)}
        ${renderWorkflowSummaryMetric("Needs adapter", summary.needs_adapter_count ?? 0)}
        ${renderWorkflowSummaryMetric("Blocked", summary.blocked_count ?? 0)}
      </div>
      <div class="read-only-adapter-preflight-notice">
        ${renderReviewPill(plan.allow_agent_execution ? "agent execution enabled" : "agent execution disabled")}
        ${renderReviewPill((summary.did_execute_count || 0) > 0 ? "agents executed" : "no agents executed")}
      </div>
      <div class="read-only-adapter-preflight-list">
        ${results.length ? results.map(renderReadOnlyAdapterPreflightRow).join("") : `<div class="pipeline-runs-empty-cell">No adapter preflight rows listed.</div>`}
      </div>
      ${renderAgenticWorkflowMarkdownSummary("Preflight report", markdown)}
    </section>
  `;
}

function renderReadOnlyAdapterPreflightRow(result = {}) {
  return `
    <article class="read-only-adapter-preflight-row">
      <div>
        <strong>${escapeHtml(result.step_index || "-")}. ${escapeHtml(result.agent_name || result.agent_key || "Unknown adapter")}</strong>
        <span>${escapeHtml(result.agent_key || "")}</span>
      </div>
      <div class="read-only-adapter-preflight-pills">
        ${renderReviewPill(result.adapter_status || "-")}
        ${renderReviewPill(result.preflight_status || "-")}
        ${renderReviewPill(result.allowed_execution_mode || "-")}
        ${renderReviewPill(result.execution_enabled ? "enabled" : "disabled")}
        ${renderReviewPill(result.did_execute ? "executed" : "not executed")}
      </div>
    </article>
  `;
}

function renderManualReadOnlyAdapterChainSection(chain = {}) {
  const present = Boolean(chain?.present || chain?.available);
  const summary = chain?.summary && typeof chain.summary === "object" ? chain.summary : {};
  const order = Array.isArray(chain?.adapter_execution_order) ? chain.adapter_execution_order : [];
  const validationStatus = String(chain?.validation_status || (present ? "unknown" : "missing")).toLowerCase();
  const markdown = String(chain?.report_markdown || "");
  if (!present) {
    return `
      <section class="manual-read-only-adapter-chain-card">
        <div class="agentic-workflow-header">
          <div>
            <h2>Manual Read-Only Adapter Chain</h2>
            <p>Manual artifact diagnostics only. Missing chain artifacts do not affect planning results.</p>
          </div>
          <span class="agentic-workflow-verification-status agentic-workflow-verification-status--unknown">Missing</span>
        </div>
        <div class="pipeline-runs-empty-cell">No manual read-only adapter chain artifacts recorded for this run yet.</div>
      </section>
    `;
  }

  return `
    <section class="manual-read-only-adapter-chain-card">
      <div class="agentic-workflow-header">
        <div>
          <h2>Manual Read-Only Adapter Chain</h2>
          <p>Manual only, read-only, and not wired into the live pipeline. These diagnostics do not change queue action, scoring, ranking, tailoring, packets, or submissions.</p>
        </div>
        <span class="agentic-workflow-verification-status agentic-workflow-verification-status--${escapeHtml(validationStatus)}">
          ${escapeHtml(formatWorkflowVerificationStatus(validationStatus))}
        </span>
      </div>
      <div class="manual-read-only-adapter-chain-metrics">
        ${renderWorkflowSummaryMetric("Execution mode", chain.execution_mode || "-")}
        ${renderWorkflowSummaryMetric("Validation", formatWorkflowVerificationStatus(validationStatus))}
        ${renderWorkflowSummaryMetric("Did execute", chain.did_execute_chain ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Mutated production", chain.did_mutate_production ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Input rows", summary.input_row_count ?? 0)}
        ${renderWorkflowSummaryMetric("Adapters executed", summary.adapters_executed_count ?? 0)}
        ${renderWorkflowSummaryMetric("Priority recs", summary.job_prioritization_recommendation_count ?? 0)}
        ${renderWorkflowSummaryMetric("Tailoring decisions", summary.tailoring_decision_count ?? 0)}
        ${renderWorkflowSummaryMetric("Operator lanes", summary.operator_review_lane_count ?? 0)}
        ${renderWorkflowSummaryMetric("Warnings", summary.warning_count ?? 0)}
      </div>
      <div class="agentic-review-section-counts">
        <strong>Adapter order</strong>
        <span>${renderReasonChips(order)}</span>
      </div>
      <div class="manual-read-only-adapter-chain-notice">
        ${renderReviewPill("manual only")}
        ${renderReviewPill("read-only")}
        ${renderReviewPill("not live pipeline")}
      </div>
      ${renderAgenticWorkflowMarkdownSummary("Chain report", markdown)}
    </section>
  `;
}

function renderExplicitReadOnlyChainGeneratorSection(generator = {}) {
  const present = Boolean(generator?.present || generator?.available);
  const summary = generator?.chain_result_summary && typeof generator.chain_result_summary === "object"
    ? generator.chain_result_summary
    : {};
  const validationStatus = String(generator?.validation_status || (present ? "unknown" : "missing")).toLowerCase();
  const markdown = String(generator?.report_markdown || "");
  if (!present) {
    return `
      <section class="explicit-read-only-chain-generator-card">
        <div class="agentic-workflow-header">
          <div>
            <h2>Explicit Read-Only Chain Generator</h2>
            <p>Generator artifact diagnostics only. Missing generator artifacts do not affect planning results.</p>
          </div>
          <span class="agentic-workflow-verification-status agentic-workflow-verification-status--unknown">Missing</span>
        </div>
        <div class="pipeline-runs-empty-cell">No explicit read-only chain generator artifacts recorded for this run yet.</div>
      </section>
    `;
  }

  return `
    <section class="explicit-read-only-chain-generator-card">
      <div class="agentic-workflow-header">
        <div>
          <h2>Explicit Read-Only Chain Generator</h2>
          <p>Explicit operator-triggered only, read-only, not automatic, and not wired into the live pipeline. These diagnostics do not change queue action, scoring, ranking, tailoring, packets, or submissions.</p>
        </div>
        <span class="agentic-workflow-verification-status agentic-workflow-verification-status--${escapeHtml(validationStatus)}">
          ${escapeHtml(formatWorkflowVerificationStatus(validationStatus))}
        </span>
      </div>
      <div class="explicit-read-only-chain-generator-metrics">
        ${renderWorkflowSummaryMetric("Execution mode", generator.execution_mode || "-")}
        ${renderWorkflowSummaryMetric("Validation", formatWorkflowVerificationStatus(validationStatus))}
        ${renderWorkflowSummaryMetric("Did run chain", generator.did_run_chain ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Mutated production", generator.did_mutate_production ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Explicit input", generator.require_explicit_input ? "required" : "missing")}
        ${renderWorkflowSummaryMetric("Explicit output", generator.require_explicit_output_dir ? "required" : "missing")}
        ${renderWorkflowSummaryMetric("Input rows", summary.input_row_count ?? 0)}
        ${renderWorkflowSummaryMetric("Adapters executed", summary.adapters_executed_count ?? 0)}
        ${renderWorkflowSummaryMetric("Priority recs", summary.job_prioritization_recommendation_count ?? 0)}
        ${renderWorkflowSummaryMetric("Tailoring decisions", summary.tailoring_decision_count ?? 0)}
        ${renderWorkflowSummaryMetric("Operator lanes", summary.operator_review_lane_count ?? 0)}
        ${renderWorkflowSummaryMetric("Warnings", summary.warning_count ?? 0)}
      </div>
      <div class="agentic-review-section-counts">
        <strong>Generator paths</strong>
        <span>${renderReasonChips([
          generator.queue_input_artifact_path ? `input:${generator.queue_input_artifact_path}` : "input:<empty>",
          generator.output_dir ? `output:${generator.output_dir}` : "output:<empty>",
        ])}</span>
      </div>
      <div class="explicit-read-only-chain-generator-notice">
        ${renderReviewPill("explicit operator-triggered only")}
        ${renderReviewPill("read-only")}
        ${renderReviewPill("not automatic")}
        ${renderReviewPill("not live pipeline")}
      </div>
      ${renderAgenticWorkflowMarkdownSummary("Generator report", markdown)}
    </section>
  `;
}

function renderDryRunExecutionSimulationSection(simulation = {}) {
  const present = Boolean(simulation?.present || simulation?.available);
  const plan = simulation?.simulated_execution_plan && typeof simulation.simulated_execution_plan === "object"
    ? simulation.simulated_execution_plan
    : {};
  const blockedReasons = Array.isArray(simulation?.blocked_live_execution_reasons)
    ? simulation.blocked_live_execution_reasons
    : [];
  const validationStatus = String(simulation?.validation_status || (present ? "unknown" : "missing")).toLowerCase();
  const markdown = String(simulation?.report_markdown || "");
  if (!present) {
    return `
      <section class="dry-run-execution-simulation-card">
        <div class="agentic-workflow-header">
          <div>
            <h2>Dry-Run Execution Simulation</h2>
            <p>Simulation artifact diagnostics only. Missing simulator artifacts do not affect planning results.</p>
          </div>
          <span class="agentic-workflow-verification-status agentic-workflow-verification-status--unknown">Missing</span>
        </div>
        <div class="pipeline-runs-empty-cell">No dry-run execution simulation artifacts recorded for this run yet.</div>
      </section>
    `;
  }

  return `
    <section class="dry-run-execution-simulation-card">
      <div class="agentic-workflow-header">
        <div>
          <h2>Dry-Run Execution Simulation</h2>
          <p>Explicit/manual simulation display only. This page does not run the simulator, execute agents, write to the database, update queues, submit applications, or mutate production.</p>
        </div>
        <span class="agentic-workflow-verification-status agentic-workflow-verification-status--${escapeHtml(validationStatus)}">
          ${escapeHtml(formatWorkflowVerificationStatus(validationStatus))}
        </span>
      </div>
      <div class="dry-run-execution-simulation-metrics">
        ${renderWorkflowSummaryMetric("Execution mode", simulation.execution_mode || "-")}
        ${renderWorkflowSummaryMetric("Validation", formatWorkflowVerificationStatus(validationStatus))}
        ${renderWorkflowSummaryMetric("Did simulate", simulation.did_simulate ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Did execute live", simulation.did_execute_live ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Mutated production", simulation.did_mutate_production ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Can execute live", plan.can_execute_live ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Requires approval", plan.requires_operator_approval ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Requires audit ledger", plan.requires_audit_ledger ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Requires idempotency", plan.requires_idempotency_key ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Requires lock", plan.requires_execution_lock ? "yes" : "no")}
        ${renderWorkflowSummaryMetric("Requires rollback", plan.requires_rollback_plan ? "yes" : "no")}
      </div>
      <div class="agentic-review-section-counts">
        <strong>Blocked live execution reasons</strong>
        <span>${renderReasonChips(blockedReasons)}</span>
      </div>
      <div class="dry-run-execution-simulation-notice">
        ${renderReviewPill("explicit/manual only")}
        ${renderReviewPill("read-only")}
        ${renderReviewPill("not live orchestration")}
        ${renderReviewPill("no mutation")}
      </div>
      ${renderAgenticWorkflowMarkdownSummary("Simulation report", markdown)}
    </section>
  `;
}

function renderProposalOnlyMutationPlanSection(planPayload = {}) {
  const present = Boolean(planPayload?.present || planPayload?.available);
  const proposalPlan = planPayload?.proposal_plan && typeof planPayload.proposal_plan === "object"
    ? planPayload.proposal_plan
    : {};
  const proposalItems = Array.isArray(planPayload?.proposal_only_mutation_items)
    ? planPayload.proposal_only_mutation_items
    : [];
  const blockedReasons = Array.isArray(planPayload?.blocked_execution_reasons)
    ? planPayload.blocked_execution_reasons
    : [];
  const validationStatus = String(planPayload?.validation_status || (present ? "unknown" : "missing")).toLowerCase();
  const markdown = String(planPayload?.report_markdown || "");
  const mutationTypes = [...new Set(proposalItems.map((item) => String(item?.mutation_type || "").trim()).filter(Boolean))];
  if (!present) {
    return `
      <section class="proposal-only-mutation-plan-card">
        <div class="agentic-workflow-header">
          <div>
            <h2>Proposal-Only Mutation Plan</h2>
            <p>Proposal-only planner artifacts are optional diagnostics and do not affect planning results.</p>
          </div>
          <span class="agentic-workflow-verification-status agentic-workflow-verification-status--unknown">Missing</span>
        </div>
        <div class="pipeline-runs-empty-cell">No proposal-only mutation plan artifacts recorded for this run yet.</div>
      </section>
    `;
  }

  return `
    <section class="proposal-only-mutation-plan-card">
      <div class="agentic-workflow-header">
        <div>
          <h2>Proposal-Only Mutation Plan</h2>
          <p>Read-only proposal diagnostics. This section does not approve, reject, store approval, call approval APIs, call mutation APIs, execute anything, write to the database, update queues, submit applications, or mutate production.</p>
        </div>
        <span class="agentic-workflow-verification-status agentic-workflow-verification-status--${escapeHtml(validationStatus)}">
          ${escapeHtml(formatWorkflowVerificationStatus(validationStatus))}
        </span>
      </div>
      <div class="proposal-only-mutation-plan-warning">
        Proposal-only and non-actionable. Future real approval or mutation requires separate reviewed phases.
      </div>
      <div class="proposal-only-mutation-plan-metrics">
        ${renderWorkflowSummaryMetric("execution_mode", planPayload.execution_mode || "-")}
        ${renderWorkflowSummaryMetric("Validation", formatWorkflowVerificationStatus(validationStatus))}
        ${renderWorkflowSummaryMetric("did_plan", planPayload.did_plan ? "true" : "false")}
        ${renderWorkflowSummaryMetric("did_execute_live", planPayload.did_execute_live ? "true" : "false")}
        ${renderWorkflowSummaryMetric("did_mutate_production", planPayload.did_mutate_production ? "true" : "false")}
        ${renderWorkflowSummaryMetric("did_approve", planPayload.did_approve ? "true" : "false")}
        ${renderWorkflowSummaryMetric("did_store_approval", planPayload.did_store_approval ? "true" : "false")}
        ${renderWorkflowSummaryMetric("did_write_db", planPayload.did_write_db ? "true" : "false")}
        ${renderWorkflowSummaryMetric("can_execute_live", proposalPlan.can_execute_live ? "true" : "false")}
        ${renderWorkflowSummaryMetric("can_mutate", proposalPlan.can_mutate ? "true" : "false")}
        ${renderWorkflowSummaryMetric("can_approve", proposalPlan.can_approve ? "true" : "false")}
        ${renderWorkflowSummaryMetric("Proposal items", proposalItems.length)}
      </div>
      <div class="agentic-workflow-verification-sections">
        <div>
          <strong>Proposal mutation types</strong>
          ${renderWorkflowVerificationList(mutationTypes)}
        </div>
        <div>
          <strong>Blocked execution reasons</strong>
          ${renderWorkflowVerificationList(blockedReasons)}
        </div>
        <div>
          <strong>Required future gates</strong>
          ${renderWorkflowVerificationList([
            proposalPlan.requires_operator_approval ? "operator approval" : "",
            proposalPlan.requires_approval_api ? "approval API" : "",
            proposalPlan.requires_approval_storage ? "approval storage" : "",
            proposalPlan.requires_audit_ledger ? "audit ledger" : "",
            proposalPlan.requires_idempotency_key ? "idempotency key" : "",
            proposalPlan.requires_execution_lock ? "execution lock" : "",
            proposalPlan.requires_rollback_plan ? "rollback plan" : "",
          ].filter(Boolean))}
        </div>
      </div>
      <div class="proposal-only-mutation-plan-notice">
        ${renderReviewPill("read-only")}
        ${renderReviewPill("proposal-only")}
        ${renderReviewPill("non-actionable")}
        ${renderReviewPill("no mutation")}
      </div>
      ${renderAgenticWorkflowMarkdownSummary("Proposal plan report", markdown)}
    </section>
  `;
}

function renderOperatorApprovalMockSection(mock = {}) {
  const present = Boolean(mock?.present);
  const requiredGates = Array.isArray(mock?.required_future_gates) ? mock.required_future_gates : [];
  const blockedActions = Array.isArray(mock?.blocked_actions) ? mock.blocked_actions : [];
  const proposalTypes = Array.isArray(mock?.simulated_proposal_types) ? mock.simulated_proposal_types : [];
  const validationStatus = String(mock?.validation_status || (present ? "unknown" : "missing")).toLowerCase();
  const approvalActionSection = renderApprovalDecisionActionSection(mock);
  if (!present) {
    return `
      <section class="operator-approval-mock-card">
        <div class="agentic-workflow-header">
          <div>
            <h2>Operator Approval Mock</h2>
            <p>Read-only approval preview appears after dry-run execution simulation artifacts are recorded.</p>
          </div>
          <span class="agentic-workflow-verification-status agentic-workflow-verification-status--unknown">Missing</span>
        </div>
      <div class="pipeline-runs-empty-cell">No operator approval mock available because no dry-run execution simulation artifacts are recorded for this run yet.</div>
      ${approvalActionSection}
    </section>
  `;
  }

  return `
    <section class="operator-approval-mock-card">
      <div class="agentic-workflow-header">
        <div>
          <h2>Operator Approval Mock</h2>
          <p>Mock-only, read-only, and non-actionable. This section does not approve, reject, store approval, call an API, execute mutations, write to the database, or submit applications.</p>
        </div>
        <span class="agentic-workflow-badge">Mock only</span>
      </div>
      <div class="operator-approval-mock-warning">
        Future approval requires separate reviewed implementation for approval storage, audit ledger, idempotency, locking, rollback, and feature gates.
      </div>
      <div class="operator-approval-mock-metrics">
        ${renderWorkflowSummaryMetric("approval_enabled", mock.approval_enabled ? "true" : "false")}
        ${renderWorkflowSummaryMetric("approval_storage_enabled", mock.approval_storage_enabled ? "true" : "false")}
        ${renderWorkflowSummaryMetric("mutation_execution_enabled", mock.mutation_execution_enabled ? "true" : "false")}
        ${renderWorkflowSummaryMetric("can_execute_live", mock.can_execute_live ? "true" : "false")}
        ${renderWorkflowSummaryMetric("Validation", formatWorkflowVerificationStatus(validationStatus))}
        ${renderWorkflowSummaryMetric("Simulated proposals", mock.simulated_proposal_count ?? 0)}
      </div>
      <div class="agentic-workflow-verification-sections">
        <div>
          <strong>Required future gates</strong>
          ${renderWorkflowVerificationList(requiredGates)}
        </div>
        <div>
          <strong>Blocked actions</strong>
          ${renderWorkflowVerificationList(blockedActions)}
        </div>
        <div>
          <strong>Simulated proposal types</strong>
          ${renderWorkflowVerificationList(proposalTypes)}
        </div>
      </div>
      ${approvalActionSection}
    </section>
  `;
}

function getAgenticApprovalRequestId(mock = {}) {
  return String(
    mock?.approval_request_id
    || mock?.approval_request?.approval_request_id
    || mock?.approvalRequest?.approval_request_id
    || "",
  ).trim();
}

function getAgenticApprovalReviewerId() {
  const user = typeof profileState !== "undefined" && profileState?.currentUser
    ? profileState.currentUser
    : null;
  return String(user?.user_id || "").trim();
}

function getApprovalActionBlockedReasons(approvalRequestId, reviewerId) {
  const reasons = [];
  if (!approvalRequestId) reasons.push("approval_request_id unavailable");
  if (!reviewerId) reasons.push("reviewer identity unavailable");
  return reasons;
}

function renderApprovalDecisionActionSection(mock = {}) {
  const approvalRequestId = getAgenticApprovalRequestId(mock);
  const reviewerId = getAgenticApprovalReviewerId();
  const blockedReasons = getApprovalActionBlockedReasons(approvalRequestId, reviewerId);
  const disabledAttr = blockedReasons.length ? "disabled" : "";
  const statusMessage = blockedReasons.length
    ? `Approval action blocked: ${blockedReasons.join("; ")}.`
    : "Approval action ready.";
  const decisions = [
    ["approved", "Approve"],
    ["denied", "Deny"],
    ["revoked", "Revoke"],
  ];

  return `
    <div class="operator-approval-action-panel" data-agentic-approval-request-id="${escapeHtml(approvalRequestId)}">
      <div class="agentic-workflow-header">
        <div>
          <h3>Approval Decision</h3>
          <p>Route-only decision recording. No queue, execution, mutation, submission, or scheduler action is triggered.</p>
        </div>
        <span class="agentic-workflow-badge">Route only</span>
      </div>
      <div class="agentic-feedback-actions">
        <div class="agentic-approval-button-group agentic-approval-button-group--actions" aria-label="Approval action buttons">
          ${decisions.map(([decision, label]) => `
            <button
              type="button"
              class="agentic-feedback-action"
              data-agentic-approval-decision="${escapeHtml(decision)}"
              ${disabledAttr}
            >
              ${escapeHtml(label)}
            </button>
          `).join("")}
        </div>
        <div class="agentic-approval-button-group agentic-approval-button-group--observability" aria-label="Read-only observability buttons">
          <button
            type="button"
            class="agentic-feedback-action"
            data-agentic-production-scheduler-observability-report
            ${approvalRequestId ? "" : "disabled"}
          >
            Load observability report
          </button>
          <button
            type="button"
            class="agentic-feedback-action"
            data-agentic-production-scheduler-observability-dashboard
            ${approvalRequestId ? "" : "disabled"}
          >
            Load observability dashboard
          </button>
          <button
            type="button"
            class="agentic-feedback-action"
            data-agentic-production-scheduler-observability-export-preview
            ${approvalRequestId ? "" : "disabled"}
          >
            Preview observability export
          </button>
          <button
            type="button"
            class="agentic-feedback-action"
            data-agentic-production-scheduler-observability-writer-status
            ${approvalRequestId ? "" : "disabled"}
          >
            Check writer status
          </button>
          <button
            type="button"
            class="agentic-feedback-action"
            data-agentic-production-scheduler-observability-reporting-job
            ${approvalRequestId ? "" : "disabled"}
          >
            Invoke reporting job
          </button>
        </div>
        <span
          class="agentic-feedback-status ${blockedReasons.length ? "is-error" : "is-info"}"
          data-agentic-approval-status
          aria-live="polite"
        >${escapeHtml(statusMessage)}</span>
        <span
          class="agentic-feedback-status is-info"
          data-agentic-production-scheduler-observability-report-status
          aria-live="polite"
        >Read-only observability reporting, dashboard, and export preview available on demand.</span>
      </div>
    </div>
  `;
}

function setAgenticApprovalStatus(message, tone = "info") {
  const status = document.querySelector("[data-agentic-approval-status]");
  if (!status) return;
  status.textContent = message || "";
  status.className = `agentic-feedback-status is-${tone}`;
}

async function recordAgenticApprovalDecision(reviewDecision, button) {
  const panel = button?.closest("[data-agentic-approval-request-id]");
  const approvalRequestId = String(panel?.dataset?.agenticApprovalRequestId || "").trim();
  const reviewerId = getAgenticApprovalReviewerId();
  const blockedReasons = getApprovalActionBlockedReasons(approvalRequestId, reviewerId);
  if (blockedReasons.length) {
    setAgenticApprovalStatus(`Approval action blocked: ${blockedReasons.join("; ")}.`, "error");
    return;
  }

  const previousDisabled = Boolean(button?.disabled);
  if (button) button.disabled = true;
  setAgenticApprovalStatus("Recording approval decision...", "info");
  try {
    await fetchJson(`/api/agentic-approvals/${encodeURIComponent(approvalRequestId)}/decision`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        reviewer_id: reviewerId,
        review_decision: reviewDecision,
        review_reason: "Recorded from Agentic Review UI route-only action.",
        decided_at: new Date().toISOString(),
      }),
    });
    setAgenticApprovalStatus("Approval decision recorded. Execution remains disabled.", "success");
  } catch (err) {
    setAgenticApprovalStatus(err?.message || "Approval decision was not recorded.", "error");
  } finally {
    if (button) {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  }
}

function formatProductionSchedulerObservabilityReportingJobMessage(payload = {}) {
  const endpointSuffix = "production-scheduler-observability-reporting-job";
  const status = String(payload.reporting_job_status || "blocked").trim();
  const reasonCodes = Array.isArray(payload.reason_codes) ? payload.reason_codes : [];
  const reasons = reasonCodes.join(", ") || "none";
  const safety = "explicit invocation only; persistence disabled; scheduler and background work disabled; file export disabled; metrics/logging/audit writers disabled; execution disabled; submission disabled; production scheduler wiring disabled";
  return `Reporting job ${status}. Endpoint: ${endpointSuffix}. Reasons: ${reasons}. ${safety}.`;
}

async function invokeProductionSchedulerObservabilityReportingJob(button) {
  const panel = button?.closest("[data-agentic-approval-request-id]");
  const approvalRequestId = String(panel?.dataset?.agenticApprovalRequestId || "").trim();
  if (!approvalRequestId) {
    setProductionSchedulerObservabilityReportStatus(
      "Reporting job blocked: approval_request_id unavailable.",
      "error",
    );
    return;
  }

  const previousDisabled = Boolean(button?.disabled);
  if (button) button.disabled = true;
  setProductionSchedulerObservabilityReportStatus("Invoking deterministic reporting job...", "info");
  try {
    const payload = await fetchJson(
      `/api/agentic-approvals/${encodeURIComponent(approvalRequestId)}/production-scheduler-observability-reporting-job`,
      { method: "POST" },
    );
    setProductionSchedulerObservabilityReportStatus(
      formatProductionSchedulerObservabilityReportingJobMessage(payload),
      payload?.blocked_by_production_scheduler_observability_reporting_job_endpoint ? "error" : "success",
    );
  } catch (err) {
    setProductionSchedulerObservabilityReportStatus(
      err?.message || "Reporting job was not invoked.",
      "error",
    );
  } finally {
    if (button) {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  }
}

function setProductionSchedulerObservabilityReportStatus(message, tone = "info") {
  const status = document.querySelector("[data-agentic-production-scheduler-observability-report-status]");
  if (!status) return;
  status.textContent = message || "";
  status.className = `agentic-feedback-status is-${tone}`;
}

function formatProductionSchedulerObservabilityReportMessage(payload = {}) {
  const status = String(
    payload.production_scheduler_observability_reporting_status || "blocked",
  ).trim();
  const reasons = Array.isArray(payload.production_scheduler_observability_reporting_reason_codes)
    ? payload.production_scheduler_observability_reporting_reason_codes.join(", ")
    : "none";
  const safety = "execution disabled; submission disabled; production scheduler wiring disabled; migration disabled; emitters/export/dashboard/reporting jobs disabled";
  return `Report ${status}. Reasons: ${reasons || "none"}. ${safety}.`;
}

async function loadProductionSchedulerObservabilityReport(button) {
  const panel = button?.closest("[data-agentic-approval-request-id]");
  const approvalRequestId = String(panel?.dataset?.agenticApprovalRequestId || "").trim();
  if (!approvalRequestId) {
    setProductionSchedulerObservabilityReportStatus(
      "Observability report blocked: approval_request_id unavailable.",
      "error",
    );
    return;
  }

  const previousDisabled = Boolean(button?.disabled);
  if (button) button.disabled = true;
  setProductionSchedulerObservabilityReportStatus("Loading read-only observability report...", "info");
  try {
    const payload = await fetchJson(
      `/api/agentic-approvals/${encodeURIComponent(approvalRequestId)}/production-scheduler-observability-report`,
    );
    setProductionSchedulerObservabilityReportStatus(
      formatProductionSchedulerObservabilityReportMessage(payload),
      payload?.blocked_by_production_scheduler_observability_reporting_endpoint ? "error" : "success",
    );
  } catch (err) {
    setProductionSchedulerObservabilityReportStatus(
      err?.message || "Read-only observability report was not loaded.",
      "error",
    );
  } finally {
    if (button) {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  }
}

function formatProductionSchedulerObservabilityDashboardExportMessage(payload = {}, surfaceLabel = "Dashboard/export") {
  const dashboardEndpointSuffix = "production-scheduler-observability-dashboard";
  const exportPreviewEndpointSuffix = "production-scheduler-observability-export-preview";
  const status =
    payload.production_scheduler_observability_dashboard_status
    || payload.production_scheduler_observability_export_preview_status
    || "blocked";
  const reasonCodes =
    payload.production_scheduler_observability_dashboard_reason_codes
    || payload.production_scheduler_observability_export_preview_reason_codes
    || [];
  const reasons = Array.isArray(reasonCodes) ? reasonCodes.join(", ") : "none";
  const safety = "execution disabled; submission disabled; production scheduler wiring disabled; scheduler, background, and live scheduler work disabled; migration disabled; metrics/logging/audit writers disabled; export file creation disabled; reporting jobs disabled";
  return `${surfaceLabel} ${String(status).trim()}. Reasons: ${reasons || "none"}. ${safety}.`;
}

async function loadProductionSchedulerObservabilityDashboardExport(button, endpointSuffix, surfaceLabel) {
  const panel = button?.closest("[data-agentic-approval-request-id]");
  const approvalRequestId = String(panel?.dataset?.agenticApprovalRequestId || "").trim();
  if (!approvalRequestId) {
    setProductionSchedulerObservabilityReportStatus(
      `${surfaceLabel} blocked: approval_request_id unavailable.`,
      "error",
    );
    return;
  }

  const previousDisabled = Boolean(button?.disabled);
  if (button) button.disabled = true;
  setProductionSchedulerObservabilityReportStatus(`Loading read-only ${surfaceLabel.toLowerCase()}...`, "info");
  try {
    const payload = await fetchJson(
      `/api/agentic-approvals/${encodeURIComponent(approvalRequestId)}/${endpointSuffix}`,
    );
    const blocked =
      payload?.blocked_by_production_scheduler_observability_dashboard_endpoint
      || payload?.blocked_by_production_scheduler_observability_export_preview_endpoint;
    setProductionSchedulerObservabilityReportStatus(
      formatProductionSchedulerObservabilityDashboardExportMessage(payload, surfaceLabel),
      blocked ? "error" : "success",
    );
  } catch (err) {
    setProductionSchedulerObservabilityReportStatus(
      err?.message || `${surfaceLabel} was not loaded.`,
      "error",
    );
  } finally {
    if (button) {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  }
}

function formatProductionSchedulerObservabilityWriterStatusMessage(payload = {}) {
  const endpointSuffix = "production-scheduler-observability-writer-status";
  const status = String(
    payload.production_scheduler_observability_writer_status || "blocked",
  ).trim();
  const reasonCodes = Array.isArray(payload.production_scheduler_observability_writer_status_reason_codes)
    ? payload.production_scheduler_observability_writer_status_reason_codes
    : [];
  const reasons = reasonCodes.join(", ") || "none";
  const safety = "metrics/logging/audit writers disabled; persistence disabled; scheduler, background, and live scheduler work disabled; migration disabled; export file creation disabled; reporting jobs disabled; execution disabled; submission disabled; production scheduler wiring disabled";
  return `Writer status ${status}. Endpoint: ${endpointSuffix}. Reasons: ${reasons}. ${safety}.`;
}

async function loadProductionSchedulerObservabilityWriterStatus(button) {
  const panel = button?.closest("[data-agentic-approval-request-id]");
  const approvalRequestId = String(panel?.dataset?.agenticApprovalRequestId || "").trim();
  if (!approvalRequestId) {
    setProductionSchedulerObservabilityReportStatus(
      "Writer status blocked: approval_request_id unavailable.",
      "error",
    );
    return;
  }

  const previousDisabled = Boolean(button?.disabled);
  if (button) button.disabled = true;
  setProductionSchedulerObservabilityReportStatus("Loading read-only writer status...", "info");
  try {
    const payload = await fetchJson(
      `/api/agentic-approvals/${encodeURIComponent(approvalRequestId)}/production-scheduler-observability-writer-status`,
    );
    setProductionSchedulerObservabilityReportStatus(
      formatProductionSchedulerObservabilityWriterStatusMessage(payload),
      payload?.blocked_by_production_scheduler_observability_writer_status_endpoint ? "error" : "success",
    );
  } catch (err) {
    setProductionSchedulerObservabilityReportStatus(
      err?.message || "Writer status was not loaded.",
      "error",
    );
  } finally {
    if (button) {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  }
}

function renderAgenticReviewData(payload, tracePayload) {
  renderAgenticReviewStatus(payload || {}, tracePayload || {});

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
    payload.read_only_adapter_preflight,
    payload.manual_read_only_adapter_chain,
    payload.explicit_read_only_chain_artifact_generation,
    payload.explicit_dry_run_execution_simulation,
    payload.proposal_only_mutation_plan,
    payload.operator_approval_mock,
    payload.agent_feedback,
    payload.rag_evaluation,
  );

  const traceNode = qs("agenticReviewTracePanel");
  if (traceNode) {
    const traceWithCriticContext = {
      ...(tracePayload || {}),
      critic_approval_request_id: getAgenticReviewApprovalRequestId(payload || {}),
    };
    window.__agenticReviewTracePayload = traceWithCriticContext;
    traceNode.outerHTML = renderAgentTraceReadOnlyPanel(traceWithCriticContext);
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

  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-agentic-feedback-event]");
    if (!button) return;
    const eventType = String(button.dataset.agenticFeedbackEvent || "").trim();
    if (!Object.values(AGENTIC_REVIEW_FEEDBACK_EVENTS).includes(eventType)) return;
    recordAgenticReviewFeedback(eventType, button);
  });

  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-agentic-approval-decision]");
    if (!button) return;
    const reviewDecision = String(button.dataset.agenticApprovalDecision || "").trim();
    if (!["approved", "denied", "revoked"].includes(reviewDecision)) return;
    recordAgenticApprovalDecision(reviewDecision, button);
  });

  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-agentic-production-scheduler-observability-report]");
    if (!button) return;
    loadProductionSchedulerObservabilityReport(button);
  });

  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-agentic-production-scheduler-observability-dashboard]");
    if (!button) return;
    loadProductionSchedulerObservabilityDashboardExport(
      button,
      "production-scheduler-observability-dashboard",
      "Dashboard",
    );
  });

  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-agentic-production-scheduler-observability-export-preview]");
    if (!button) return;
    loadProductionSchedulerObservabilityDashboardExport(
      button,
      "production-scheduler-observability-export-preview",
      "Export preview",
    );
  });

  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-agentic-production-scheduler-observability-writer-status]");
    if (!button) return;
    loadProductionSchedulerObservabilityWriterStatus(button);
  });

  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-agentic-production-scheduler-observability-reporting-job]");
    if (!button) return;
    invokeProductionSchedulerObservabilityReportingJob(button);
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-agentic-critic-evaluator-readonly]");
    if (!button) return;
    const approvalRequestId = String(button.dataset.approvalRequestId || "").trim();
    const status = button.closest(".agent-trace-summary")?.querySelector("[data-agentic-critic-evaluator-status]");
    if (!approvalRequestId) {
      if (status) status.textContent = "Critic evaluator blocked: approval request unavailable.";
      return;
    }
    const previousDisabled = Boolean(button.disabled);
    button.disabled = true;
    if (status) status.textContent = "Running read-only critic evaluator...";
    try {
      const tracePayload = window.__agenticReviewTracePayload && typeof window.__agenticReviewTracePayload === "object"
        ? window.__agenticReviewTracePayload
        : {};
      const criticResult = await fetchJson(
        `/api/agentic-approvals/${encodeURIComponent(approvalRequestId)}/critic-evaluator-readonly`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            trace_payload: tracePayload,
            trace_payload_source: tracePayload.trace_evidence_pack ? "trace_evidence_pack" : "agent_trace_panel",
          }),
        },
      );
      window.__agenticReviewTracePayload = {
        ...tracePayload,
        critic_approval_request_id: approvalRequestId,
        critic_evaluator_result: criticResult,
      };
      const traceNode = qs("agenticReviewTracePanel");
      if (traceNode) {
        traceNode.outerHTML = renderAgentTraceReadOnlyPanel(window.__agenticReviewTracePayload);
      }
    } catch (err) {
      if (status) status.textContent = err?.message || "Read-only critic evaluator failed.";
    } finally {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-manual-jd-intelligence-dry-run]");
    if (!button) return;
    const status = button.closest(".agent-trace-summary")?.querySelector("[data-manual-jd-intelligence-dry-run-status]");
    const previousDisabled = Boolean(button.disabled);
    button.disabled = true;
    if (status) status.textContent = "Running manual read-only JD intelligence dry-run...";
    try {
      const tracePayload = window.__agenticReviewTracePayload && typeof window.__agenticReviewTracePayload === "object"
        ? window.__agenticReviewTracePayload
        : {};
      const dryRunResult = await fetchJson(
        "/api/manual-jd-intelligence-dry-run",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            job_title: button.dataset.jobTitle || "",
            company: button.dataset.company || "",
            location: button.dataset.location || "",
            job_description: "",
            source_metadata: {
              source: "agent_trace_manual_panel",
            },
            context_id: button.dataset.contextId || "",
            job_id: button.dataset.jobId || "",
          }),
        },
      );
      window.__agenticReviewTracePayload = {
        ...tracePayload,
        manual_jd_intelligence_dry_run_result: dryRunResult,
      };
      const traceNode = qs("agenticReviewTracePanel");
      if (traceNode) {
        traceNode.outerHTML = renderAgentTraceReadOnlyPanel(window.__agenticReviewTracePayload);
      }
    } catch (err) {
      if (status) status.textContent = err?.message || "Manual JD intelligence dry-run failed.";
    } finally {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-manual-resume-match-dry-run]");
    if (!button) return;
    const status = button.closest(".agent-trace-summary")?.querySelector("[data-manual-resume-match-dry-run-status]");
    const previousDisabled = Boolean(button.disabled);
    button.disabled = true;
    if (status) status.textContent = "Running manual read-only resume match dry-run...";
    try {
      const tracePayload = window.__agenticReviewTracePayload && typeof window.__agenticReviewTracePayload === "object"
        ? window.__agenticReviewTracePayload
        : {};
      const resumeMatchResult = await fetchJson(
        "/api/manual-resume-match-dry-run",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            jd_intelligence: tracePayload.manual_jd_intelligence_dry_run_result || {},
            resume_variants: [],
            resume_evidence_rows: [],
            context_id: button.dataset.contextId || "",
            job_id: button.dataset.jobId || "",
          }),
        },
      );
      window.__agenticReviewTracePayload = {
        ...tracePayload,
        manual_resume_match_dry_run_result: resumeMatchResult,
      };
      const traceNode = qs("agenticReviewTracePanel");
      if (traceNode) {
        traceNode.outerHTML = renderAgentTraceReadOnlyPanel(window.__agenticReviewTracePayload);
      }
    } catch (err) {
      if (status) status.textContent = err?.message || "Manual resume match dry-run failed.";
    } finally {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-manual-tailoring-suggestion-dry-run]");
    if (!button) return;
    const status = button.closest(".agent-trace-summary")?.querySelector("[data-manual-tailoring-suggestion-dry-run-status]");
    const previousDisabled = Boolean(button.disabled);
    button.disabled = true;
    if (status) status.textContent = "Running manual read-only tailoring suggestion dry-run...";
    try {
      const tracePayload = window.__agenticReviewTracePayload && typeof window.__agenticReviewTracePayload === "object"
        ? window.__agenticReviewTracePayload
        : {};
      const tailoringSuggestionResult = await fetchJson(
        "/api/manual-tailoring-suggestion-dry-run",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            jd_intelligence: tracePayload.manual_jd_intelligence_dry_run_result || {},
            resume_match_payload: tracePayload.manual_resume_match_dry_run_result || {},
            resume_variants: [],
            resume_evidence_rows: [],
            selected_resume_id: button.dataset.selectedResumeId || "",
            context_id: button.dataset.contextId || "",
            job_id: button.dataset.jobId || "",
          }),
        },
      );
      window.__agenticReviewTracePayload = {
        ...tracePayload,
        manual_tailoring_suggestion_dry_run_result: tailoringSuggestionResult,
      };
      const traceNode = qs("agenticReviewTracePanel");
      if (traceNode) {
        traceNode.outerHTML = renderAgentTraceReadOnlyPanel(window.__agenticReviewTracePayload);
      }
    } catch (err) {
      if (status) status.textContent = err?.message || "Manual tailoring suggestion dry-run failed.";
    } finally {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-manual-critic-guardrail-dry-run]");
    if (!button) return;
    const status = button.closest(".agent-trace-summary")?.querySelector("[data-manual-critic-guardrail-dry-run-status]");
    const previousDisabled = Boolean(button.disabled);
    button.disabled = true;
    if (status) status.textContent = "Running manual read-only critic guardrail dry-run...";
    try {
      const tracePayload = window.__agenticReviewTracePayload && typeof window.__agenticReviewTracePayload === "object"
        ? window.__agenticReviewTracePayload
        : {};
      const criticGuardrailResult = await fetchJson(
        "/api/manual-critic-guardrail-dry-run",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            tailoring_suggestion_payload: tracePayload.manual_tailoring_suggestion_dry_run_result || {},
            jd_intelligence: tracePayload.manual_jd_intelligence_dry_run_result || {},
            resume_variants: [],
            resume_evidence_rows: [],
            context_id: button.dataset.contextId || "",
            job_id: button.dataset.jobId || "",
          }),
        },
      );
      window.__agenticReviewTracePayload = {
        ...tracePayload,
        manual_critic_guardrail_dry_run_result: criticGuardrailResult,
      };
      const traceNode = qs("agenticReviewTracePanel");
      if (traceNode) {
        traceNode.outerHTML = renderAgentTraceReadOnlyPanel(window.__agenticReviewTracePayload);
      }
    } catch (err) {
      if (status) status.textContent = err?.message || "Manual critic guardrail dry-run failed.";
    } finally {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-manual-strategy-recommendation-dry-run]");
    if (!button) return;
    const status = button.closest(".agent-trace-summary")?.querySelector("[data-manual-strategy-recommendation-dry-run-status]");
    const previousDisabled = Boolean(button.disabled);
    button.disabled = true;
    if (status) status.textContent = "Running manual read-only strategy recommendation dry-run...";
    try {
      const tracePayload = window.__agenticReviewTracePayload && typeof window.__agenticReviewTracePayload === "object"
        ? window.__agenticReviewTracePayload
        : {};
      const strategyRecommendationResult = await fetchJson(
        "/api/manual-strategy-recommendation-dry-run",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            jd_intelligence: tracePayload.manual_jd_intelligence_dry_run_result || {},
            resume_match_payload: tracePayload.manual_resume_match_dry_run_result || {},
            tailoring_suggestion_payload: tracePayload.manual_tailoring_suggestion_dry_run_result || {},
            critic_guardrail_payload: tracePayload.manual_critic_guardrail_dry_run_result || {},
            user_preferences: {},
            context_id: button.dataset.contextId || "",
            job_id: button.dataset.jobId || "",
          }),
        },
      );
      window.__agenticReviewTracePayload = {
        ...tracePayload,
        manual_strategy_recommendation_dry_run_result: strategyRecommendationResult,
      };
      const traceNode = qs("agenticReviewTracePanel");
      if (traceNode) {
        traceNode.outerHTML = renderAgentTraceReadOnlyPanel(window.__agenticReviewTracePayload);
      }
    } catch (err) {
      if (status) status.textContent = err?.message || "Manual strategy recommendation dry-run failed.";
    } finally {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-manual-shadow-agentic-workflow-chain-dry-run]");
    if (!button) return;
    const status = button.closest(".agent-trace-summary")?.querySelector("[data-manual-shadow-agentic-workflow-chain-dry-run-status]");
    const previousDisabled = Boolean(button.disabled);
    button.disabled = true;
    if (status) status.textContent = "Running manual read-only shadow chain dry-run...";
    try {
      const tracePayload = window.__agenticReviewTracePayload && typeof window.__agenticReviewTracePayload === "object"
        ? window.__agenticReviewTracePayload
        : {};
      const shadowChainResult = await fetchJson(
        "/api/manual-shadow-agentic-workflow-chain-dry-run",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            job_title: button.dataset.jobTitle || "",
            company: button.dataset.company || "",
            location: button.dataset.location || "",
            job_description: "",
            source_metadata: {
              source: "agent_trace_manual_panel",
            },
            jd_intelligence: tracePayload.manual_jd_intelligence_dry_run_result || {},
            resume_variants: [],
            resume_evidence_rows: [],
            selected_resume_id: tracePayload.manual_resume_match_dry_run_result?.selected_resume_id || "",
            user_preferences: {},
            context_id: button.dataset.contextId || "",
            job_id: button.dataset.jobId || "",
          }),
        },
      );
      window.__agenticReviewTracePayload = {
        ...tracePayload,
        manual_shadow_agentic_workflow_chain_dry_run_result: shadowChainResult,
      };
      const traceNode = qs("agenticReviewTracePanel");
      if (traceNode) {
        traceNode.outerHTML = renderAgentTraceReadOnlyPanel(window.__agenticReviewTracePayload);
      }
    } catch (err) {
      if (status) status.textContent = err?.message || "Manual shadow chain dry-run failed.";
    } finally {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-shadow-sidecar-trace-readback]");
    if (!button) return;
    const status = button.closest(".agent-trace-summary")?.querySelector("[data-shadow-sidecar-trace-readback-status]");
    const previousDisabled = Boolean(button.disabled);
    button.disabled = true;
    if (status) status.textContent = "Reading shadow sidecar trace in read-only mode...";
    try {
      const tracePayload = window.__agenticReviewTracePayload && typeof window.__agenticReviewTracePayload === "object"
        ? window.__agenticReviewTracePayload
        : {};
      const readbackResult = await fetchJson(
        "/api/shadow-sidecar/trace-readback",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            pipeline_run_id: button.dataset.pipelineRunId || getAgenticReviewRunId() || "",
            context_id: button.dataset.contextId || tracePayload.context_id || "",
            agent_run_id: button.dataset.agentRunId || tracePayload.agent_run_id || tracePayload.agent_run?.agent_run_id || "",
          }),
        },
      );
      window.__agenticReviewTracePayload = {
        ...tracePayload,
        shadow_sidecar_trace_readback_result: readbackResult,
      };
      const traceNode = qs("agenticReviewTracePanel");
      if (traceNode) {
        traceNode.outerHTML = renderAgentTraceReadOnlyPanel(window.__agenticReviewTracePayload);
      }
    } catch (err) {
      if (status) status.textContent = err?.message || "Shadow sidecar trace readback failed.";
    } finally {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-shadow-sidecar-score-comparison]");
    if (!button) return;
    const status = button.closest(".agent-trace-summary")?.querySelector("[data-shadow-sidecar-score-comparison-status]");
    const previousDisabled = Boolean(button.disabled);
    button.disabled = true;
    if (status) status.textContent = "Comparing deterministic score and shadow evidence in read-only mode...";
    try {
      const tracePayload = window.__agenticReviewTracePayload && typeof window.__agenticReviewTracePayload === "object"
        ? window.__agenticReviewTracePayload
        : {};
      const comparisonResult = await fetchJson(
        "/api/shadow-sidecar/score-comparison",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(shadowScoreComparisonRequestPayload(tracePayload)),
        },
      );
      window.__agenticReviewTracePayload = {
        ...tracePayload,
        shadow_sidecar_score_comparison_result: comparisonResult,
      };
      const traceNode = qs("agenticReviewTracePanel");
      if (traceNode) {
        traceNode.outerHTML = renderAgentTraceReadOnlyPanel(window.__agenticReviewTracePayload);
      }
    } catch (err) {
      if (status) status.textContent = err?.message || "Shadow score comparison failed.";
    } finally {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-human-reviewed-influence-preview]");
    if (!button) return;
    const status = button.closest(".agent-trace-summary")?.querySelector("[data-human-reviewed-influence-preview-status]");
    const previousDisabled = Boolean(button.disabled);
    button.disabled = true;
    if (status) status.textContent = "Previewing human-reviewed influence in read-only mode...";
    try {
      const tracePayload = window.__agenticReviewTracePayload && typeof window.__agenticReviewTracePayload === "object"
        ? window.__agenticReviewTracePayload
        : {};
      const previewResult = await fetchJson(
        "/api/human-reviewed-influence-preview",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(humanReviewedInfluencePreviewRequestPayload(tracePayload)),
        },
      );
      window.__agenticReviewTracePayload = {
        ...tracePayload,
        human_reviewed_influence_preview_result: previewResult,
      };
      const traceNode = qs("agenticReviewTracePanel");
      if (traceNode) {
        traceNode.outerHTML = renderAgentTraceReadOnlyPanel(window.__agenticReviewTracePayload);
      }
    } catch (err) {
      if (status) status.textContent = err?.message || "Human-reviewed influence preview failed.";
    } finally {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-human-reviewed-influence-approval-request]");
    if (!button) return;
    const section = button.closest(".agent-trace-summary");
    const status = section?.querySelector("[data-human-reviewed-influence-approval-request-status]");
    const confirmation = section?.querySelector("[data-human-reviewed-influence-approval-request-confirmation]");
    const previousDisabled = Boolean(button.disabled);
    button.disabled = true;
    if (status) status.textContent = "Requesting manual influence approval gate...";
    try {
      const tracePayload = window.__agenticReviewTracePayload && typeof window.__agenticReviewTracePayload === "object"
        ? window.__agenticReviewTracePayload
        : {};
      const requestResult = await fetchJson(
        "/api/human-reviewed-influence-approval-request",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(humanReviewedInfluenceApprovalRequestPayload(tracePayload, {
            reviewerConfirmation: Boolean(confirmation?.checked),
            contextId: button.dataset.contextId || "",
            jobId: button.dataset.jobId || "",
          })),
        },
      );
      window.__agenticReviewTracePayload = {
        ...tracePayload,
        human_reviewed_influence_approval_request_result: requestResult,
      };
      const traceNode = qs("agenticReviewTracePanel");
      if (traceNode) {
        traceNode.outerHTML = renderAgentTraceReadOnlyPanel(window.__agenticReviewTracePayload);
      }
    } catch (err) {
      if (status) status.textContent = err?.message || "Human-reviewed influence approval request failed.";
    } finally {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-agent-recommendation-overlay]");
    if (!button) return;
    const status = button.closest(".agent-trace-summary")?.querySelector("[data-agent-recommendation-overlay-status]");
    const previousDisabled = Boolean(button.disabled);
    button.disabled = true;
    if (status) status.textContent = "Building read-only agent recommendation overlay...";
    try {
      const tracePayload = window.__agenticReviewTracePayload && typeof window.__agenticReviewTracePayload === "object"
        ? window.__agenticReviewTracePayload
        : {};
      const overlayResult = await fetchJson(
        "/api/agent-recommendation-overlay",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(agentRecommendationOverlayRequestPayload(tracePayload)),
        },
      );
      window.__agenticReviewTracePayload = {
        ...tracePayload,
        agent_recommendation_overlay_result: overlayResult,
      };
      const traceNode = qs("agenticReviewTracePanel");
      if (traceNode) {
        traceNode.outerHTML = renderAgentTraceReadOnlyPanel(window.__agenticReviewTracePayload);
      }
    } catch (err) {
      if (status) status.textContent = err?.message || "Agent recommendation overlay failed.";
    } finally {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-manual-shadow-recommendation-handoff-dry-run]");
    if (!button) return;
    const status = button.closest(".agent-trace-summary")?.querySelector("[data-manual-shadow-recommendation-handoff-dry-run-status]");
    const previousDisabled = Boolean(button.disabled);
    button.disabled = true;
    if (status) status.textContent = "Building manual review-only shadow recommendation handoff...";
    try {
      const tracePayload = window.__agenticReviewTracePayload && typeof window.__agenticReviewTracePayload === "object"
        ? window.__agenticReviewTracePayload
        : {};
      const handoffResult = await fetchJson(
        "/api/manual-shadow-recommendation-handoff-dry-run",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            shadow_chain_payload: tracePayload.manual_shadow_agentic_workflow_chain_dry_run_result || {},
            job_title: button.dataset.jobTitle || "",
            company: button.dataset.company || "",
            location: button.dataset.location || "",
            job_description: "",
            source_metadata: {
              source: "agent_trace_manual_panel",
            },
            jd_intelligence: tracePayload.manual_jd_intelligence_dry_run_result || {},
            resume_variants: [],
            resume_evidence_rows: [],
            selected_resume_id: tracePayload.manual_resume_match_dry_run_result?.selected_resume_id || "",
            user_preferences: {},
            context_id: button.dataset.contextId || "",
            job_id: button.dataset.jobId || "",
          }),
        },
      );
      window.__agenticReviewTracePayload = {
        ...tracePayload,
        manual_shadow_recommendation_handoff_dry_run_result: handoffResult,
      };
      const traceNode = qs("agenticReviewTracePanel");
      if (traceNode) {
        traceNode.outerHTML = renderAgentTraceReadOnlyPanel(window.__agenticReviewTracePayload);
      }
    } catch (err) {
      if (status) status.textContent = err?.message || "Manual shadow recommendation handoff failed.";
    } finally {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-manual-human-decision-capture-dry-run]");
    if (!button) return;
    const section = button.closest(".agent-trace-summary");
    const select = section?.querySelector("[data-manual-human-decision-capture-dry-run-select]");
    const status = section?.querySelector("[data-manual-human-decision-capture-dry-run-status]");
    const previousDisabled = Boolean(button.disabled);
    button.disabled = true;
    if (status) status.textContent = "Capturing simulated review-only human decision...";
    try {
      const tracePayload = window.__agenticReviewTracePayload && typeof window.__agenticReviewTracePayload === "object"
        ? window.__agenticReviewTracePayload
        : {};
      const decisionCaptureResult = await fetchJson(
        "/api/manual-human-decision-capture-dry-run",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            handoff_payload: tracePayload.manual_shadow_recommendation_handoff_dry_run_result || {},
            shadow_chain_payload: tracePayload.manual_shadow_agentic_workflow_chain_dry_run_result || {},
            reviewer_decision: select?.value || "accept_recommendation_for_review",
            reviewer_note: "",
            job_title: button.dataset.jobTitle || "",
            company: button.dataset.company || "",
            location: button.dataset.location || "",
            job_description: "",
            source_metadata: {
              source: "agent_trace_manual_panel",
            },
            jd_intelligence: tracePayload.manual_jd_intelligence_dry_run_result || {},
            resume_variants: [],
            resume_evidence_rows: [],
            selected_resume_id: tracePayload.manual_resume_match_dry_run_result?.selected_resume_id || "",
            user_preferences: {},
            context_id: button.dataset.contextId || "",
            job_id: button.dataset.jobId || "",
          }),
        },
      );
      window.__agenticReviewTracePayload = {
        ...tracePayload,
        manual_human_decision_capture_dry_run_result: decisionCaptureResult,
      };
      const traceNode = qs("agenticReviewTracePanel");
      if (traceNode) {
        traceNode.outerHTML = renderAgentTraceReadOnlyPanel(window.__agenticReviewTracePayload);
      }
    } catch (err) {
      if (status) status.textContent = err?.message || "Manual human decision capture dry-run failed.";
    } finally {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-manual-human-approved-action-plan-dry-run]");
    if (!button) return;
    const status = button.closest(".agent-trace-summary")?.querySelector("[data-manual-human-approved-action-plan-dry-run-status]");
    const previousDisabled = Boolean(button.disabled);
    button.disabled = true;
    if (status) status.textContent = "Building preview-only human-approved action plan...";
    try {
      const tracePayload = window.__agenticReviewTracePayload && typeof window.__agenticReviewTracePayload === "object"
        ? window.__agenticReviewTracePayload
        : {};
      const actionPlanResult = await fetchJson(
        "/api/manual-human-approved-action-plan-dry-run",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            decision_capture_payload: tracePayload.manual_human_decision_capture_dry_run_result || {},
            handoff_payload: tracePayload.manual_shadow_recommendation_handoff_dry_run_result || {},
            shadow_chain_payload: tracePayload.manual_shadow_agentic_workflow_chain_dry_run_result || {},
            reviewer_decision: tracePayload.manual_human_decision_capture_dry_run_result?.reviewer_decision || "",
            reviewer_note: tracePayload.manual_human_decision_capture_dry_run_result?.reviewer_note || "",
            context_id: button.dataset.contextId || "",
            job_id: button.dataset.jobId || "",
          }),
        },
      );
      window.__agenticReviewTracePayload = {
        ...tracePayload,
        manual_human_approved_action_plan_dry_run_result: actionPlanResult,
      };
      const traceNode = qs("agenticReviewTracePanel");
      if (traceNode) {
        traceNode.outerHTML = renderAgentTraceReadOnlyPanel(window.__agenticReviewTracePayload);
      }
    } catch (err) {
      if (status) status.textContent = err?.message || "Manual action plan dry-run failed.";
    } finally {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-manual-review-packet-preview-dry-run]");
    if (!button) return;
    const status = button.closest(".agent-trace-summary")?.querySelector("[data-manual-review-packet-preview-dry-run-status]");
    const previousDisabled = Boolean(button.disabled);
    button.disabled = true;
    if (status) status.textContent = "Building preview-only review packet...";
    try {
      const tracePayload = window.__agenticReviewTracePayload && typeof window.__agenticReviewTracePayload === "object"
        ? window.__agenticReviewTracePayload
        : {};
      const packetPreviewResult = await fetchJson(
        "/api/manual-review-packet-preview-dry-run",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            action_plan_payload: tracePayload.manual_human_approved_action_plan_dry_run_result || {},
            decision_capture_payload: tracePayload.manual_human_decision_capture_dry_run_result || {},
            handoff_payload: tracePayload.manual_shadow_recommendation_handoff_dry_run_result || {},
            shadow_chain_payload: tracePayload.manual_shadow_agentic_workflow_chain_dry_run_result || {},
            reviewer_decision: tracePayload.manual_human_decision_capture_dry_run_result?.reviewer_decision || "",
            reviewer_note: tracePayload.manual_human_decision_capture_dry_run_result?.reviewer_note || "",
            context_id: button.dataset.contextId || "",
            job_id: button.dataset.jobId || "",
          }),
        },
      );
      window.__agenticReviewTracePayload = {
        ...tracePayload,
        manual_review_packet_preview_dry_run_result: packetPreviewResult,
      };
      const traceNode = qs("agenticReviewTracePanel");
      if (traceNode) {
        traceNode.outerHTML = renderAgentTraceReadOnlyPanel(window.__agenticReviewTracePayload);
      }
    } catch (err) {
      if (status) status.textContent = err?.message || "Manual review packet preview dry-run failed.";
    } finally {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-manual-approval-request-preview-dry-run]");
    if (!button) return;
    const status = button.closest(".agent-trace-summary")?.querySelector("[data-manual-approval-request-preview-dry-run-status]");
    const previousDisabled = Boolean(button.disabled);
    button.disabled = true;
    if (status) status.textContent = "Building preview-only approval request...";
    try {
      const tracePayload = window.__agenticReviewTracePayload && typeof window.__agenticReviewTracePayload === "object"
        ? window.__agenticReviewTracePayload
        : {};
      const approvalPreviewResult = await fetchJson(
        "/api/manual-approval-request-preview-dry-run",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            review_packet_payload: tracePayload.manual_review_packet_preview_dry_run_result || {},
            action_plan_payload: tracePayload.manual_human_approved_action_plan_dry_run_result || {},
            decision_capture_payload: tracePayload.manual_human_decision_capture_dry_run_result || {},
            handoff_payload: tracePayload.manual_shadow_recommendation_handoff_dry_run_result || {},
            shadow_chain_payload: tracePayload.manual_shadow_agentic_workflow_chain_dry_run_result || {},
            reviewer_decision: tracePayload.manual_human_decision_capture_dry_run_result?.reviewer_decision || "",
            reviewer_note: tracePayload.manual_human_decision_capture_dry_run_result?.reviewer_note || "",
            context_id: button.dataset.contextId || "",
            job_id: button.dataset.jobId || "",
          }),
        },
      );
      window.__agenticReviewTracePayload = {
        ...tracePayload,
        manual_approval_request_preview_dry_run_result: approvalPreviewResult,
      };
      const traceNode = qs("agenticReviewTracePanel");
      if (traceNode) {
        traceNode.outerHTML = renderAgentTraceReadOnlyPanel(window.__agenticReviewTracePayload);
      }
    } catch (err) {
      if (status) status.textContent = err?.message || "Manual approval request preview dry-run failed.";
    } finally {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-manual-approval-creation-gate-dry-run]");
    if (!button) return;
    const section = button.closest(".agent-trace-summary");
    const status = section?.querySelector("[data-manual-approval-creation-gate-dry-run-status]");
    const confirmation = section?.querySelector("[data-manual-approval-creation-gate-confirmation]");
    const previousDisabled = Boolean(button.disabled);
    button.disabled = true;
    if (status) status.textContent = "Checking preview-only approval creation gate...";
    try {
      const tracePayload = window.__agenticReviewTracePayload && typeof window.__agenticReviewTracePayload === "object"
        ? window.__agenticReviewTracePayload
        : {};
      const gateResult = await fetchJson(
        "/api/manual-approval-creation-gate-dry-run",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            approval_preview_payload: tracePayload.manual_approval_request_preview_dry_run_result || {},
            review_packet_payload: tracePayload.manual_review_packet_preview_dry_run_result || {},
            action_plan_payload: tracePayload.manual_human_approved_action_plan_dry_run_result || {},
            decision_capture_payload: tracePayload.manual_human_decision_capture_dry_run_result || {},
            handoff_payload: tracePayload.manual_shadow_recommendation_handoff_dry_run_result || {},
            shadow_chain_payload: tracePayload.manual_shadow_agentic_workflow_chain_dry_run_result || {},
            reviewer_confirmation: Boolean(confirmation?.checked),
            reviewer_decision: tracePayload.manual_human_decision_capture_dry_run_result?.reviewer_decision || "",
            reviewer_note: tracePayload.manual_human_decision_capture_dry_run_result?.reviewer_note || "",
            context_id: button.dataset.contextId || "",
            job_id: button.dataset.jobId || "",
          }),
        },
      );
      window.__agenticReviewTracePayload = {
        ...tracePayload,
        manual_approval_creation_gate_dry_run_result: gateResult,
      };
      const traceNode = qs("agenticReviewTracePanel");
      if (traceNode) {
        traceNode.outerHTML = renderAgentTraceReadOnlyPanel(window.__agenticReviewTracePayload);
      }
    } catch (err) {
      if (status) status.textContent = err?.message || "Manual approval creation gate dry-run failed.";
    } finally {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-manual-guarded-approval-request-create]");
    if (!button) return;
    const section = button.closest(".agent-trace-summary");
    const status = section?.querySelector("[data-manual-guarded-approval-request-create-status]");
    const confirmation = section?.querySelector("[data-manual-guarded-approval-request-create-confirmation]");
    const previousDisabled = Boolean(button.disabled);
    button.disabled = true;
    if (status) status.textContent = "Submitting guarded manual approval request creation...";
    try {
      const tracePayload = window.__agenticReviewTracePayload && typeof window.__agenticReviewTracePayload === "object"
        ? window.__agenticReviewTracePayload
        : {};
      const createResult = await fetchJson(
        "/api/manual-guarded-approval-request-create",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            approval_creation_gate_payload: tracePayload.manual_approval_creation_gate_dry_run_result || {},
            approval_preview_payload: tracePayload.manual_approval_request_preview_dry_run_result || {},
            review_packet_payload: tracePayload.manual_review_packet_preview_dry_run_result || {},
            action_plan_payload: tracePayload.manual_human_approved_action_plan_dry_run_result || {},
            decision_capture_payload: tracePayload.manual_human_decision_capture_dry_run_result || {},
            handoff_payload: tracePayload.manual_shadow_recommendation_handoff_dry_run_result || {},
            shadow_chain_payload: tracePayload.manual_shadow_agentic_workflow_chain_dry_run_result || {},
            reviewer_confirmation: Boolean(confirmation?.checked),
            reviewer_decision: tracePayload.manual_human_decision_capture_dry_run_result?.reviewer_decision || "",
            reviewer_note: tracePayload.manual_human_decision_capture_dry_run_result?.reviewer_note || "",
            context_id: button.dataset.contextId || "",
            job_id: button.dataset.jobId || "",
          }),
        },
      );
      window.__agenticReviewTracePayload = {
        ...tracePayload,
        manual_guarded_approval_request_create_result: createResult,
      };
      const traceNode = qs("agenticReviewTracePanel");
      if (traceNode) {
        traceNode.outerHTML = renderAgentTraceReadOnlyPanel(window.__agenticReviewTracePayload);
      }
    } catch (err) {
      if (status) status.textContent = err?.message || "Manual guarded approval request creation failed.";
    } finally {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-manual-guarded-approval-creation-observability]");
    if (!button) return;
    const section = button.closest(".agent-trace-summary");
    const status = section?.querySelector("[data-manual-guarded-approval-creation-observability-status]");
    const previousDisabled = Boolean(button.disabled);
    button.disabled = true;
    if (status) status.textContent = "Loading guarded approval creation audit...";
    try {
      const tracePayload = window.__agenticReviewTracePayload && typeof window.__agenticReviewTracePayload === "object"
        ? window.__agenticReviewTracePayload
        : {};
      const auditResult = await fetchJson(
        "/api/manual-guarded-approval-creation-observability",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            guarded_creation_payload: tracePayload.manual_guarded_approval_request_create_result || {},
            approval_creation_gate_payload: tracePayload.manual_approval_creation_gate_dry_run_result || {},
            approval_preview_payload: tracePayload.manual_approval_request_preview_dry_run_result || {},
            review_packet_payload: tracePayload.manual_review_packet_preview_dry_run_result || {},
            action_plan_payload: tracePayload.manual_human_approved_action_plan_dry_run_result || {},
            decision_capture_payload: tracePayload.manual_human_decision_capture_dry_run_result || {},
            handoff_payload: tracePayload.manual_shadow_recommendation_handoff_dry_run_result || {},
            shadow_chain_payload: tracePayload.manual_shadow_agentic_workflow_chain_dry_run_result || {},
            created_approval_request_id: tracePayload.manual_guarded_approval_request_create_result?.created_approval_request_id || "",
            reviewer_confirmation: false,
            context_id: button.dataset.contextId || "",
            job_id: button.dataset.jobId || "",
          }),
        },
      );
      window.__agenticReviewTracePayload = {
        ...tracePayload,
        manual_guarded_approval_creation_observability_result: auditResult,
      };
      const traceNode = qs("agenticReviewTracePanel");
      if (traceNode) {
        traceNode.outerHTML = renderAgentTraceReadOnlyPanel(window.__agenticReviewTracePayload);
      }
    } catch (err) {
      if (status) status.textContent = err?.message || "Manual guarded approval creation audit failed.";
    } finally {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-manual-approval-request-readback]");
    if (!button) return;
    const section = button.closest(".agent-trace-summary");
    const status = section?.querySelector("[data-manual-approval-request-readback-status]");
    const previousDisabled = Boolean(button.disabled);
    button.disabled = true;
    if (status) status.textContent = "Reading approval request details...";
    try {
      const tracePayload = window.__agenticReviewTracePayload && typeof window.__agenticReviewTracePayload === "object"
        ? window.__agenticReviewTracePayload
        : {};
      const creation = tracePayload.manual_guarded_approval_request_create_result || {};
      const observability = tracePayload.manual_guarded_approval_creation_observability_result || {};
      const readbackResult = await fetchJson(
        "/api/manual-approval-request-readback",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            approval_request_id: button.dataset.approvalRequestId || creation.created_approval_request_id || observability.created_approval_request_id || "",
            guarded_creation_payload: creation,
            observability_payload: observability,
            context_id: button.dataset.contextId || "",
            job_id: button.dataset.jobId || "",
          }),
        },
      );
      window.__agenticReviewTracePayload = {
        ...tracePayload,
        manual_approval_request_readback_result: readbackResult,
      };
      const traceNode = qs("agenticReviewTracePanel");
      if (traceNode) {
        traceNode.outerHTML = renderAgentTraceReadOnlyPanel(window.__agenticReviewTracePayload);
      }
    } catch (err) {
      if (status) status.textContent = err?.message || "Manual approval request readback failed.";
    } finally {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-manual-approval-status-transition-preview]");
    if (!button) return;
    const section = button.closest(".agent-trace-summary");
    const select = section?.querySelector("[data-manual-approval-status-transition-preview-select]");
    const status = section?.querySelector("[data-manual-approval-status-transition-preview-status]");
    const previousDisabled = Boolean(button.disabled);
    button.disabled = true;
    if (status) status.textContent = "Previewing approval status transition...";
    try {
      const tracePayload = window.__agenticReviewTracePayload && typeof window.__agenticReviewTracePayload === "object"
        ? window.__agenticReviewTracePayload
        : {};
      const readback = tracePayload.manual_approval_request_readback_result || {};
      const creation = tracePayload.manual_guarded_approval_request_create_result || {};
      const observability = tracePayload.manual_guarded_approval_creation_observability_result || {};
      const transitionPreviewResult = await fetchJson(
        "/api/manual-approval-status-transition-preview-dry-run",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            approval_request_id: button.dataset.approvalRequestId || readback.approval_request_id || creation.created_approval_request_id || observability.created_approval_request_id || "",
            proposed_transition: select?.value || "approve",
            reviewer_note: "",
            approval_request_readback_payload: readback,
            guarded_creation_payload: creation,
            observability_payload: observability,
            context_id: button.dataset.contextId || "",
            job_id: button.dataset.jobId || "",
          }),
        },
      );
      window.__agenticReviewTracePayload = {
        ...tracePayload,
        manual_approval_status_transition_preview_result: transitionPreviewResult,
      };
      const traceNode = qs("agenticReviewTracePanel");
      if (traceNode) {
        traceNode.outerHTML = renderAgentTraceReadOnlyPanel(window.__agenticReviewTracePayload);
      }
    } catch (err) {
      if (status) status.textContent = err?.message || "Manual approval status transition preview failed.";
    } finally {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-manual-guarded-approval-status-transition]");
    if (!button) return;
    const section = button.closest(".agent-trace-summary");
    const confirmation = section?.querySelector("[data-manual-guarded-approval-status-transition-confirmation]");
    const status = section?.querySelector("[data-manual-guarded-approval-status-transition-status]");
    const previousDisabled = Boolean(button.disabled);
    button.disabled = true;
    if (status) status.textContent = "Applying guarded approval status transition...";
    try {
      const tracePayload = window.__agenticReviewTracePayload && typeof window.__agenticReviewTracePayload === "object"
        ? window.__agenticReviewTracePayload
        : {};
      const preview = tracePayload.manual_approval_status_transition_preview_result || {};
      const readback = tracePayload.manual_approval_request_readback_result || {};
      const creation = tracePayload.manual_guarded_approval_request_create_result || {};
      const observability = tracePayload.manual_guarded_approval_creation_observability_result || {};
      const transitionResult = await fetchJson(
        "/api/manual-guarded-approval-status-transition",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            approval_request_id: button.dataset.approvalRequestId || preview.approval_request_id || readback.approval_request_id || creation.created_approval_request_id || observability.created_approval_request_id || "",
            proposed_transition: button.dataset.proposedTransition || preview.proposed_transition || "approve",
            reviewer_confirmation: Boolean(confirmation?.checked),
            reviewer_note: "",
            transition_preview_payload: preview,
            approval_request_readback_payload: readback,
            guarded_creation_payload: creation,
            observability_payload: observability,
            context_id: button.dataset.contextId || "",
            job_id: button.dataset.jobId || "",
          }),
        },
      );
      window.__agenticReviewTracePayload = {
        ...tracePayload,
        manual_guarded_approval_status_transition_result: transitionResult,
      };
      const traceNode = qs("agenticReviewTracePanel");
      if (traceNode) {
        traceNode.outerHTML = renderAgentTraceReadOnlyPanel(window.__agenticReviewTracePayload);
      }
    } catch (err) {
      if (status) status.textContent = err?.message || "Manual guarded approval status transition failed.";
    } finally {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-manual-approval-status-transition-observability]");
    if (!button) return;
    const section = button.closest(".agent-trace-summary");
    const status = section?.querySelector("[data-manual-approval-status-transition-observability-status]");
    const previousDisabled = Boolean(button.disabled);
    button.disabled = true;
    if (status) status.textContent = "Loading approval status transition audit...";
    try {
      const tracePayload = window.__agenticReviewTracePayload && typeof window.__agenticReviewTracePayload === "object"
        ? window.__agenticReviewTracePayload
        : {};
      const transition = tracePayload.manual_guarded_approval_status_transition_result || {};
      const auditResult = await fetchJson(
        "/api/manual-approval-status-transition-observability",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            guarded_status_transition_payload: transition,
            approval_request_id: button.dataset.approvalRequestId || transition.approval_request_id || "",
            proposed_transition: button.dataset.proposedTransition || transition.proposed_transition || "",
            context_id: button.dataset.contextId || "",
            job_id: button.dataset.jobId || "",
          }),
        },
      );
      window.__agenticReviewTracePayload = {
        ...tracePayload,
        manual_approval_status_transition_observability_result: auditResult,
      };
      const traceNode = qs("agenticReviewTracePanel");
      if (traceNode) {
        traceNode.outerHTML = renderAgentTraceReadOnlyPanel(window.__agenticReviewTracePayload);
      }
    } catch (err) {
      if (status) status.textContent = err?.message || "Manual approval status transition audit failed.";
    } finally {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-manual-queue-handoff-readiness-preview]");
    if (!button) return;
    const section = button.closest(".agent-trace-summary");
    const status = section?.querySelector("[data-manual-queue-handoff-readiness-preview-status]");
    const previousDisabled = Boolean(button.disabled);
    button.disabled = true;
    if (status) status.textContent = "Previewing queue handoff readiness...";
    try {
      const tracePayload = window.__agenticReviewTracePayload && typeof window.__agenticReviewTracePayload === "object"
        ? window.__agenticReviewTracePayload
        : {};
      const readback = tracePayload.manual_approval_request_readback_result || {};
      const transitionAudit = tracePayload.manual_approval_status_transition_observability_result || {};
      const transition = tracePayload.manual_guarded_approval_status_transition_result || {};
      const readinessResult = await fetchJson(
        "/api/manual-queue-handoff-readiness-preview-dry-run",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            approval_request_id: button.dataset.approvalRequestId || readback.approval_request_id || transitionAudit.approval_request_id || transition.approval_request_id || "",
            approval_request_readback_payload: readback,
            approval_status_transition_observability_payload: transitionAudit,
            approval_status_transition_payload: transition,
            context_id: button.dataset.contextId || "",
            job_id: button.dataset.jobId || "",
          }),
        },
      );
      window.__agenticReviewTracePayload = {
        ...tracePayload,
        manual_queue_handoff_readiness_preview_result: readinessResult,
      };
      const traceNode = qs("agenticReviewTracePanel");
      if (traceNode) {
        traceNode.outerHTML = renderAgentTraceReadOnlyPanel(window.__agenticReviewTracePayload);
      }
    } catch (err) {
      if (status) status.textContent = err?.message || "Manual queue handoff readiness preview failed.";
    } finally {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-manual-guarded-queue-handoff-create]");
    if (!button) return;
    const section = button.closest(".agent-trace-summary");
    const confirmation = section?.querySelector("[data-manual-guarded-queue-handoff-create-confirmation]");
    const status = section?.querySelector("[data-manual-guarded-queue-handoff-create-status]");
    const previousDisabled = Boolean(button.disabled);
    button.disabled = true;
    if (status) status.textContent = "Creating guarded queue handoff...";
    try {
      const tracePayload = window.__agenticReviewTracePayload && typeof window.__agenticReviewTracePayload === "object"
        ? window.__agenticReviewTracePayload
        : {};
      const readiness = tracePayload.manual_queue_handoff_readiness_preview_result || {};
      const readback = tracePayload.manual_approval_request_readback_result || {};
      const transitionAudit = tracePayload.manual_approval_status_transition_observability_result || {};
      const createResult = await fetchJson(
        "/api/manual-guarded-queue-handoff-create",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            approval_request_id: button.dataset.approvalRequestId || readiness.approval_request_id || readback.approval_request_id || transitionAudit.approval_request_id || "",
            reviewer_confirmation: Boolean(confirmation?.checked),
            queue_handoff_readiness_payload: readiness,
            approval_request_readback_payload: readback,
            approval_status_transition_observability_payload: transitionAudit,
            context_id: button.dataset.contextId || "",
            job_id: button.dataset.jobId || "",
            reviewer_note: "",
          }),
        },
      );
      window.__agenticReviewTracePayload = {
        ...tracePayload,
        manual_guarded_queue_handoff_create_result: createResult,
      };
      const traceNode = qs("agenticReviewTracePanel");
      if (traceNode) {
        traceNode.outerHTML = renderAgentTraceReadOnlyPanel(window.__agenticReviewTracePayload);
      }
    } catch (err) {
      if (status) status.textContent = err?.message || "Manual guarded queue handoff creation failed.";
    } finally {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-manual-queue-handoff-creation-observability]");
    if (!button) return;
    const section = button.closest(".agent-trace-summary");
    const status = section?.querySelector("[data-manual-queue-handoff-creation-observability-status]");
    const previousDisabled = Boolean(button.disabled);
    button.disabled = true;
    if (status) status.textContent = "Loading queue handoff audit...";
    try {
      const tracePayload = window.__agenticReviewTracePayload && typeof window.__agenticReviewTracePayload === "object"
        ? window.__agenticReviewTracePayload
        : {};
      const creation = tracePayload.manual_guarded_queue_handoff_create_result || {};
      const auditResult = await fetchJson(
        "/api/manual-queue-handoff-creation-observability",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            guarded_queue_handoff_creation_payload: creation,
            approval_request_id: button.dataset.approvalRequestId || creation.approval_request_id || "",
            queue_handoff_id: button.dataset.queueHandoffId || creation.queue_handoff_id || "",
            context_id: button.dataset.contextId || "",
            job_id: button.dataset.jobId || "",
          }),
        },
      );
      window.__agenticReviewTracePayload = {
        ...tracePayload,
        manual_queue_handoff_creation_observability_result: auditResult,
      };
      const traceNode = qs("agenticReviewTracePanel");
      if (traceNode) {
        traceNode.outerHTML = renderAgentTraceReadOnlyPanel(window.__agenticReviewTracePayload);
      }
    } catch (err) {
      if (status) status.textContent = err?.message || "Manual queue handoff audit failed.";
    } finally {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-manual-execution-readiness-preview]");
    if (!button) return;
    const section = button.closest(".agent-trace-summary");
    const status = section?.querySelector("[data-manual-execution-readiness-preview-status]");
    const previousDisabled = Boolean(button.disabled);
    button.disabled = true;
    if (status) status.textContent = "Previewing execution readiness...";
    try {
      const tracePayload = window.__agenticReviewTracePayload && typeof window.__agenticReviewTracePayload === "object"
        ? window.__agenticReviewTracePayload
        : {};
      const queueAudit = tracePayload.manual_queue_handoff_creation_observability_result || {};
      const queueCreation = tracePayload.manual_guarded_queue_handoff_create_result || {};
      const readinessResult = await fetchJson(
        "/api/manual-execution-readiness-preview-dry-run",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            queue_handoff_id: button.dataset.queueHandoffId || queueAudit.queue_handoff_id || queueCreation.queue_handoff_id || "",
            approval_request_id: button.dataset.approvalRequestId || queueAudit.approval_request_id || queueCreation.approval_request_id || "",
            queue_handoff_creation_payload: queueCreation,
            queue_handoff_observability_payload: queueAudit,
            context_id: button.dataset.contextId || "",
            job_id: button.dataset.jobId || "",
          }),
        },
      );
      window.__agenticReviewTracePayload = {
        ...tracePayload,
        manual_execution_readiness_preview_result: readinessResult,
      };
      const traceNode = qs("agenticReviewTracePanel");
      if (traceNode) {
        traceNode.outerHTML = renderAgentTraceReadOnlyPanel(window.__agenticReviewTracePayload);
      }
    } catch (err) {
      if (status) status.textContent = err?.message || "Manual execution readiness preview failed.";
    } finally {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-manual-execution-launch-gate-preview]");
    if (!button) return;
    const section = button.closest(".agent-trace-summary");
    const status = section?.querySelector("[data-manual-execution-launch-gate-preview-status]");
    const previousDisabled = Boolean(button.disabled);
    button.disabled = true;
    if (status) status.textContent = "Previewing execution launch gate...";
    try {
      const tracePayload = window.__agenticReviewTracePayload && typeof window.__agenticReviewTracePayload === "object"
        ? window.__agenticReviewTracePayload
        : {};
      const executionReadiness = tracePayload.manual_execution_readiness_preview_result || {};
      const queueAudit = tracePayload.manual_queue_handoff_creation_observability_result || {};
      const gateResult = await fetchJson(
        "/api/manual-execution-launch-gate-preview-dry-run",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            approval_request_id: button.dataset.approvalRequestId || executionReadiness.approval_request_id || queueAudit.approval_request_id || "",
            queue_handoff_id: button.dataset.queueHandoffId || executionReadiness.queue_handoff_id || queueAudit.queue_handoff_id || "",
            execution_readiness_payload: executionReadiness,
            queue_handoff_observability_payload: queueAudit,
            reviewer_confirmation_preview: false,
            context_id: button.dataset.contextId || "",
            job_id: button.dataset.jobId || "",
          }),
        },
      );
      window.__agenticReviewTracePayload = {
        ...tracePayload,
        manual_execution_launch_gate_preview_result: gateResult,
      };
      const traceNode = qs("agenticReviewTracePanel");
      if (traceNode) {
        traceNode.outerHTML = renderAgentTraceReadOnlyPanel(window.__agenticReviewTracePayload);
      }
    } catch (err) {
      if (status) status.textContent = err?.message || "Manual execution launch gate preview failed.";
    } finally {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-manual-execution-launch-gate-observability]");
    if (!button) return;
    const section = button.closest(".agent-trace-summary");
    const status = section?.querySelector("[data-manual-execution-launch-gate-observability-status]");
    const previousDisabled = Boolean(button.disabled);
    button.disabled = true;
    if (status) status.textContent = "Loading execution launch gate audit...";
    try {
      const tracePayload = window.__agenticReviewTracePayload && typeof window.__agenticReviewTracePayload === "object"
        ? window.__agenticReviewTracePayload
        : {};
      const launchGate = tracePayload.manual_execution_launch_gate_preview_result || {};
      const auditResult = await fetchJson(
        "/api/manual-execution-launch-gate-observability",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            execution_launch_gate_payload: launchGate,
            approval_request_id: button.dataset.approvalRequestId || launchGate.approval_request_id || "",
            queue_handoff_id: button.dataset.queueHandoffId || launchGate.queue_handoff_id || "",
            context_id: button.dataset.contextId || "",
            job_id: button.dataset.jobId || "",
          }),
        },
      );
      window.__agenticReviewTracePayload = {
        ...tracePayload,
        manual_execution_launch_gate_observability_result: auditResult,
      };
      const traceNode = qs("agenticReviewTracePanel");
      if (traceNode) {
        traceNode.outerHTML = renderAgentTraceReadOnlyPanel(window.__agenticReviewTracePayload);
      }
    } catch (err) {
      if (status) status.textContent = err?.message || "Manual execution launch gate audit failed.";
    } finally {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-manual-execution-request-packet-preview]");
    if (!button) return;
    const section = button.closest(".agent-trace-summary");
    const status = section?.querySelector("[data-manual-execution-request-packet-preview-status]");
    const previousDisabled = Boolean(button.disabled);
    button.disabled = true;
    if (status) status.textContent = "Previewing execution request packet...";
    try {
      const tracePayload = window.__agenticReviewTracePayload && typeof window.__agenticReviewTracePayload === "object"
        ? window.__agenticReviewTracePayload
        : {};
      const launchGate = tracePayload.manual_execution_launch_gate_preview_result || {};
      const launchAudit = tracePayload.manual_execution_launch_gate_observability_result || {};
      const executionReadiness = tracePayload.manual_execution_readiness_preview_result || {};
      const queueAudit = tracePayload.manual_queue_handoff_creation_observability_result || {};
      const packetResult = await fetchJson(
        "/api/manual-execution-request-packet-preview-dry-run",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            approval_request_id: button.dataset.approvalRequestId || launchAudit.approval_request_id || launchGate.approval_request_id || "",
            queue_handoff_id: button.dataset.queueHandoffId || launchAudit.queue_handoff_id || launchGate.queue_handoff_id || "",
            execution_launch_gate_payload: launchGate,
            execution_launch_gate_observability_payload: launchAudit,
            execution_readiness_payload: executionReadiness,
            queue_handoff_observability_payload: queueAudit,
            reviewer_note: "",
            context_id: button.dataset.contextId || "",
            job_id: button.dataset.jobId || "",
          }),
        },
      );
      window.__agenticReviewTracePayload = {
        ...tracePayload,
        manual_execution_request_packet_preview_result: packetResult,
      };
      const traceNode = qs("agenticReviewTracePanel");
      if (traceNode) {
        traceNode.outerHTML = renderAgentTraceReadOnlyPanel(window.__agenticReviewTracePayload);
      }
    } catch (err) {
      if (status) status.textContent = err?.message || "Manual execution request packet preview failed.";
    } finally {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-manual-guarded-execution-request-create]");
    if (!button) return;
    const section = button.closest(".agent-trace-summary");
    const confirmation = section?.querySelector("[data-manual-guarded-execution-request-create-confirmation]");
    const status = section?.querySelector("[data-manual-guarded-execution-request-create-status]");
    const previousDisabled = Boolean(button.disabled);
    button.disabled = true;
    if (status) status.textContent = "Creating guarded execution request...";
    try {
      const tracePayload = window.__agenticReviewTracePayload && typeof window.__agenticReviewTracePayload === "object"
        ? window.__agenticReviewTracePayload
        : {};
      const packet = tracePayload.manual_execution_request_packet_preview_result || {};
      const launchGate = tracePayload.manual_execution_launch_gate_preview_result || {};
      const launchAudit = tracePayload.manual_execution_launch_gate_observability_result || {};
      const createResult = await fetchJson(
        "/api/manual-guarded-execution-request-create",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            approval_request_id: button.dataset.approvalRequestId || packet.approval_request_id || launchGate.approval_request_id || "",
            queue_handoff_id: button.dataset.queueHandoffId || packet.queue_handoff_id || launchAudit.queue_handoff_id || launchGate.queue_handoff_id || "",
            reviewer_confirmation: Boolean(confirmation?.checked),
            execution_request_packet_payload: packet,
            execution_launch_gate_payload: launchGate,
            execution_launch_gate_observability_payload: launchAudit,
            reviewer_note: "",
            context_id: button.dataset.contextId || "",
            job_id: button.dataset.jobId || "",
          }),
        },
      );
      window.__agenticReviewTracePayload = {
        ...tracePayload,
        manual_guarded_execution_request_create_result: createResult,
      };
      const traceNode = qs("agenticReviewTracePanel");
      if (traceNode) {
        traceNode.outerHTML = renderAgentTraceReadOnlyPanel(window.__agenticReviewTracePayload);
      }
    } catch (err) {
      if (status) status.textContent = err?.message || "Manual guarded execution request creation failed.";
    } finally {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-manual-guarded-execution-request-observability]");
    if (!button) return;
    const section = button.closest(".agent-trace-summary");
    const status = section?.querySelector("[data-manual-guarded-execution-request-observability-status]");
    const previousDisabled = Boolean(button.disabled);
    button.disabled = true;
    if (status) status.textContent = "Loading execution request audit...";
    try {
      const tracePayload = window.__agenticReviewTracePayload && typeof window.__agenticReviewTracePayload === "object"
        ? window.__agenticReviewTracePayload
        : {};
      const creation = tracePayload.manual_guarded_execution_request_create_result || {};
      const auditResult = await fetchJson(
        "/api/manual-guarded-execution-request-observability",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            guarded_execution_request_creation_payload: creation,
            approval_request_id: button.dataset.approvalRequestId || creation.approval_request_id || "",
            queue_handoff_id: button.dataset.queueHandoffId || creation.queue_handoff_id || "",
            execution_request_id: button.dataset.executionRequestId || creation.execution_request_id || "",
            context_id: button.dataset.contextId || "",
            job_id: button.dataset.jobId || "",
          }),
        },
      );
      window.__agenticReviewTracePayload = {
        ...tracePayload,
        manual_guarded_execution_request_observability_result: auditResult,
      };
      const traceNode = qs("agenticReviewTracePanel");
      if (traceNode) {
        traceNode.outerHTML = renderAgentTraceReadOnlyPanel(window.__agenticReviewTracePayload);
      }
    } catch (err) {
      if (status) status.textContent = err?.message || "Manual execution request audit failed.";
    } finally {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-manual-execution-request-readback]");
    if (!button) return;
    const section = button.closest(".agent-trace-summary");
    const status = section?.querySelector("[data-manual-execution-request-readback-status]");
    const previousDisabled = Boolean(button.disabled);
    button.disabled = true;
    if (status) status.textContent = "Reading execution request details...";
    try {
      const tracePayload = window.__agenticReviewTracePayload && typeof window.__agenticReviewTracePayload === "object"
        ? window.__agenticReviewTracePayload
        : {};
      const creation = tracePayload.manual_guarded_execution_request_create_result || {};
      const audit = tracePayload.manual_guarded_execution_request_observability_result || {};
      const readbackResult = await fetchJson(
        "/api/manual-execution-request-readback",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            execution_request_id: button.dataset.executionRequestId || audit.execution_request_id || creation.execution_request_id || "",
            approval_request_id: button.dataset.approvalRequestId || audit.approval_request_id || creation.approval_request_id || "",
            queue_handoff_id: button.dataset.queueHandoffId || audit.queue_handoff_id || creation.queue_handoff_id || "",
            guarded_execution_request_creation_payload: creation,
            execution_request_creation_observability_payload: audit,
            context_id: button.dataset.contextId || "",
            job_id: button.dataset.jobId || "",
          }),
        },
      );
      window.__agenticReviewTracePayload = {
        ...tracePayload,
        manual_execution_request_readback_result: readbackResult,
      };
      const traceNode = qs("agenticReviewTracePanel");
      if (traceNode) {
        traceNode.outerHTML = renderAgentTraceReadOnlyPanel(window.__agenticReviewTracePayload);
      }
    } catch (err) {
      if (status) status.textContent = err?.message || "Manual execution request readback failed.";
    } finally {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-manual-execution-request-status-transition-preview]");
    if (!button) return;
    const section = button.closest(".agent-trace-summary");
    const select = section?.querySelector("[data-manual-execution-request-status-transition-preview-select]");
    const status = section?.querySelector("[data-manual-execution-request-status-transition-preview-status]");
    const previousDisabled = Boolean(button.disabled);
    button.disabled = true;
    if (status) status.textContent = "Previewing execution request status transition...";
    try {
      const tracePayload = window.__agenticReviewTracePayload && typeof window.__agenticReviewTracePayload === "object"
        ? window.__agenticReviewTracePayload
        : {};
      const readback = tracePayload.manual_execution_request_readback_result || {};
      const creation = tracePayload.manual_guarded_execution_request_create_result || {};
      const audit = tracePayload.manual_guarded_execution_request_observability_result || {};
      const transitionPreviewResult = await fetchJson(
        "/api/manual-execution-request-status-transition-preview-dry-run",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            execution_request_id: button.dataset.executionRequestId || readback.execution_request_id || audit.execution_request_id || creation.execution_request_id || "",
            requested_transition: select?.value || "ready_for_manual_execution",
            execution_request_readback_payload: readback,
            execution_request_creation_payload: creation,
            execution_request_creation_observability_payload: audit,
            approval_request_id: button.dataset.approvalRequestId || readback.approval_request_id || audit.approval_request_id || creation.approval_request_id || "",
            queue_handoff_id: button.dataset.queueHandoffId || readback.queue_handoff_id || audit.queue_handoff_id || creation.queue_handoff_id || "",
            reviewer_note: "",
            context_id: button.dataset.contextId || "",
            job_id: button.dataset.jobId || "",
          }),
        },
      );
      window.__agenticReviewTracePayload = {
        ...tracePayload,
        manual_execution_request_status_transition_preview_result: transitionPreviewResult,
      };
      const traceNode = qs("agenticReviewTracePanel");
      if (traceNode) {
        traceNode.outerHTML = renderAgentTraceReadOnlyPanel(window.__agenticReviewTracePayload);
      }
    } catch (err) {
      if (status) status.textContent = err?.message || "Manual execution request status transition preview failed.";
    } finally {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-manual-guarded-execution-request-status-transition]");
    if (!button) return;
    const section = button.closest(".agent-trace-summary");
    const confirmation = section?.querySelector("[data-manual-guarded-execution-request-status-transition-confirmation]");
    const status = section?.querySelector("[data-manual-guarded-execution-request-status-transition-status]");
    const previousDisabled = Boolean(button.disabled);
    button.disabled = true;
    if (status) status.textContent = "Applying guarded execution request status...";
    try {
      const tracePayload = window.__agenticReviewTracePayload && typeof window.__agenticReviewTracePayload === "object"
        ? window.__agenticReviewTracePayload
        : {};
      const preview = tracePayload.manual_execution_request_status_transition_preview_result || {};
      const readback = tracePayload.manual_execution_request_readback_result || {};
      const transitionResult = await fetchJson(
        "/api/manual-guarded-execution-request-status-transition",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            execution_request_id: button.dataset.executionRequestId || preview.execution_request_id || readback.execution_request_id || "",
            requested_transition: button.dataset.requestedTransition || preview.requested_transition || "ready_for_manual_execution",
            reviewer_confirmation: Boolean(confirmation?.checked),
            execution_request_status_transition_preview_payload: preview,
            execution_request_readback_payload: readback,
            approval_request_id: button.dataset.approvalRequestId || preview.approval_request_id || readback.approval_request_id || "",
            queue_handoff_id: button.dataset.queueHandoffId || preview.queue_handoff_id || readback.queue_handoff_id || "",
            reviewer_note: "",
            context_id: button.dataset.contextId || "",
            job_id: button.dataset.jobId || "",
          }),
        },
      );
      window.__agenticReviewTracePayload = {
        ...tracePayload,
        manual_guarded_execution_request_status_transition_result: transitionResult,
      };
      const traceNode = qs("agenticReviewTracePanel");
      if (traceNode) {
        traceNode.outerHTML = renderAgentTraceReadOnlyPanel(window.__agenticReviewTracePayload);
      }
    } catch (err) {
      if (status) status.textContent = err?.message || "Manual guarded execution request status transition failed.";
    } finally {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-manual-guarded-execution-request-status-transition-observability]");
    if (!button) return;
    const section = button.closest(".agent-trace-summary");
    const status = section?.querySelector("[data-manual-guarded-execution-request-status-transition-observability-status]");
    const previousDisabled = Boolean(button.disabled);
    button.disabled = true;
    if (status) status.textContent = "Loading execution request status audit...";
    try {
      const tracePayload = window.__agenticReviewTracePayload && typeof window.__agenticReviewTracePayload === "object"
        ? window.__agenticReviewTracePayload
        : {};
      const transition = tracePayload.manual_guarded_execution_request_status_transition_result || {};
      const preview = tracePayload.manual_execution_request_status_transition_preview_result || {};
      const readback = tracePayload.manual_execution_request_readback_result || {};
      const auditResult = await fetchJson(
        "/api/manual-guarded-execution-request-status-transition-observability",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            guarded_execution_request_status_transition_payload: transition,
            execution_request_id: button.dataset.executionRequestId || transition.execution_request_id || preview.execution_request_id || readback.execution_request_id || "",
            approval_request_id: button.dataset.approvalRequestId || transition.approval_request_id || preview.approval_request_id || readback.approval_request_id || "",
            queue_handoff_id: button.dataset.queueHandoffId || transition.queue_handoff_id || preview.queue_handoff_id || readback.queue_handoff_id || "",
            context_id: button.dataset.contextId || "",
            job_id: button.dataset.jobId || "",
          }),
        },
      );
      window.__agenticReviewTracePayload = {
        ...tracePayload,
        manual_guarded_execution_request_status_transition_observability_result: auditResult,
      };
      const traceNode = qs("agenticReviewTracePanel");
      if (traceNode) {
        traceNode.outerHTML = renderAgentTraceReadOnlyPanel(window.__agenticReviewTracePayload);
      }
    } catch (err) {
      if (status) status.textContent = err?.message || "Manual execution request status audit failed.";
    } finally {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-manual-application-execution-simulation-preview]");
    if (!button) return;
    const section = button.closest(".agent-trace-summary");
    const status = section?.querySelector("[data-manual-application-execution-simulation-preview-status]");
    const previousDisabled = Boolean(button.disabled);
    button.disabled = true;
    if (status) status.textContent = "Previewing application execution simulation...";
    try {
      const tracePayload = window.__agenticReviewTracePayload && typeof window.__agenticReviewTracePayload === "object"
        ? window.__agenticReviewTracePayload
        : {};
      const readback = tracePayload.manual_execution_request_readback_result || {};
      const transition = tracePayload.manual_guarded_execution_request_status_transition_result || {};
      const audit = tracePayload.manual_guarded_execution_request_status_transition_observability_result || {};
      const simulationResult = await fetchJson(
        "/api/manual-application-execution-simulation-preview-dry-run",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            execution_request_id: button.dataset.executionRequestId || audit.execution_request_id || transition.execution_request_id || readback.execution_request_id || "",
            approval_request_id: button.dataset.approvalRequestId || audit.approval_request_id || transition.approval_request_id || readback.approval_request_id || "",
            queue_handoff_id: button.dataset.queueHandoffId || audit.queue_handoff_id || transition.queue_handoff_id || readback.queue_handoff_id || "",
            execution_request_readback_payload: readback,
            execution_request_status_transition_payload: transition,
            execution_request_status_transition_observability_payload: audit,
            reviewer_note: "",
            context_id: button.dataset.contextId || "",
            job_id: button.dataset.jobId || "",
          }),
        },
      );
      window.__agenticReviewTracePayload = {
        ...tracePayload,
        manual_application_execution_simulation_preview_result: simulationResult,
      };
      const traceNode = qs("agenticReviewTracePanel");
      if (traceNode) {
        traceNode.outerHTML = renderAgentTraceReadOnlyPanel(window.__agenticReviewTracePayload);
      }
    } catch (err) {
      if (status) status.textContent = err?.message || "Manual application execution simulation preview failed.";
    } finally {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-manual-application-execution-simulation-observability]");
    if (!button) return;
    const section = button.closest(".agent-trace-summary");
    const status = section?.querySelector("[data-manual-application-execution-simulation-observability-status]");
    const previousDisabled = Boolean(button.disabled);
    button.disabled = true;
    if (status) status.textContent = "Loading application execution simulation audit...";
    try {
      const tracePayload = window.__agenticReviewTracePayload && typeof window.__agenticReviewTracePayload === "object"
        ? window.__agenticReviewTracePayload
        : {};
      const simulation = tracePayload.manual_application_execution_simulation_preview_result || {};
      const readback = tracePayload.manual_execution_request_readback_result || {};
      const auditResult = await fetchJson(
        "/api/manual-application-execution-simulation-observability",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            application_execution_simulation_payload: simulation,
            execution_request_id: button.dataset.executionRequestId || simulation.execution_request_id || readback.execution_request_id || "",
            approval_request_id: button.dataset.approvalRequestId || simulation.approval_request_id || readback.approval_request_id || "",
            queue_handoff_id: button.dataset.queueHandoffId || simulation.queue_handoff_id || readback.queue_handoff_id || "",
            context_id: button.dataset.contextId || "",
            job_id: button.dataset.jobId || "",
          }),
        },
      );
      window.__agenticReviewTracePayload = {
        ...tracePayload,
        manual_application_execution_simulation_observability_result: auditResult,
      };
      const traceNode = qs("agenticReviewTracePanel");
      if (traceNode) {
        traceNode.outerHTML = renderAgentTraceReadOnlyPanel(window.__agenticReviewTracePayload);
      }
    } catch (err) {
      if (status) status.textContent = err?.message || "Manual application execution simulation audit failed.";
    } finally {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-manual-application-execution-preflight-checklist]");
    if (!button) return;
    const section = button.closest(".agent-trace-summary");
    const status = section?.querySelector("[data-manual-application-execution-preflight-checklist-status]");
    const previousDisabled = Boolean(button.disabled);
    button.disabled = true;
    if (status) status.textContent = "Building application execution preflight checklist...";
    try {
      const tracePayload = window.__agenticReviewTracePayload && typeof window.__agenticReviewTracePayload === "object"
        ? window.__agenticReviewTracePayload
        : {};
      const simulation = tracePayload.manual_application_execution_simulation_preview_result || {};
      const simulationAudit = tracePayload.manual_application_execution_simulation_observability_result || {};
      const readback = tracePayload.manual_execution_request_readback_result || {};
      const transitionAudit = tracePayload.manual_guarded_execution_request_status_transition_observability_result || {};
      const checklistResult = await fetchJson(
        "/api/manual-application-execution-preflight-checklist-dry-run",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            execution_request_id: button.dataset.executionRequestId || simulationAudit.execution_request_id || simulation.execution_request_id || readback.execution_request_id || "",
            approval_request_id: button.dataset.approvalRequestId || simulationAudit.approval_request_id || simulation.approval_request_id || readback.approval_request_id || "",
            queue_handoff_id: button.dataset.queueHandoffId || simulationAudit.queue_handoff_id || simulation.queue_handoff_id || readback.queue_handoff_id || "",
            application_execution_simulation_payload: simulation,
            application_execution_simulation_observability_payload: simulationAudit,
            execution_request_readback_payload: readback,
            execution_request_status_transition_observability_payload: transitionAudit,
            reviewer_note: "",
            context_id: button.dataset.contextId || "",
            job_id: button.dataset.jobId || "",
          }),
        },
      );
      window.__agenticReviewTracePayload = {
        ...tracePayload,
        manual_application_execution_preflight_checklist_result: checklistResult,
      };
      const traceNode = qs("agenticReviewTracePanel");
      if (traceNode) {
        traceNode.outerHTML = renderAgentTraceReadOnlyPanel(window.__agenticReviewTracePayload);
      }
    } catch (err) {
      if (status) status.textContent = err?.message || "Manual application execution preflight checklist failed.";
    } finally {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-manual-application-execution-preflight-observability]");
    if (!button) return;
    const section = button.closest(".agent-trace-summary");
    const status = section?.querySelector("[data-manual-application-execution-preflight-observability-status]");
    const previousDisabled = Boolean(button.disabled);
    button.disabled = true;
    if (status) status.textContent = "Loading application execution preflight audit...";
    try {
      const tracePayload = window.__agenticReviewTracePayload && typeof window.__agenticReviewTracePayload === "object"
        ? window.__agenticReviewTracePayload
        : {};
      const preflight = tracePayload.manual_application_execution_preflight_checklist_result || {};
      const simulation = tracePayload.manual_application_execution_simulation_preview_result || {};
      const readback = tracePayload.manual_execution_request_readback_result || {};
      const auditResult = await fetchJson(
        "/api/manual-application-execution-preflight-observability",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            application_execution_preflight_payload: preflight,
            execution_request_id: button.dataset.executionRequestId || preflight.execution_request_id || simulation.execution_request_id || readback.execution_request_id || "",
            approval_request_id: button.dataset.approvalRequestId || preflight.approval_request_id || simulation.approval_request_id || readback.approval_request_id || "",
            queue_handoff_id: button.dataset.queueHandoffId || preflight.queue_handoff_id || simulation.queue_handoff_id || readback.queue_handoff_id || "",
            context_id: button.dataset.contextId || "",
            job_id: button.dataset.jobId || "",
          }),
        },
      );
      window.__agenticReviewTracePayload = {
        ...tracePayload,
        manual_application_execution_preflight_observability_result: auditResult,
      };
      const traceNode = qs("agenticReviewTracePanel");
      if (traceNode) {
        traceNode.outerHTML = renderAgentTraceReadOnlyPanel(window.__agenticReviewTracePayload);
      }
    } catch (err) {
      if (status) status.textContent = err?.message || "Manual application execution preflight audit failed.";
    } finally {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-manual-guarded-application-execution-launch-request-create]");
    if (!button) return;
    const section = button.closest(".agent-trace-summary");
    const confirmation = section?.querySelector("[data-manual-guarded-application-execution-launch-request-create-confirmation]");
    const status = section?.querySelector("[data-manual-guarded-application-execution-launch-request-create-status]");
    const previousDisabled = Boolean(button.disabled);
    button.disabled = true;
    if (status) status.textContent = "Creating guarded execution launch request...";
    try {
      const tracePayload = window.__agenticReviewTracePayload && typeof window.__agenticReviewTracePayload === "object"
        ? window.__agenticReviewTracePayload
        : {};
      const preflight = tracePayload.manual_application_execution_preflight_checklist_result || {};
      const preflightAudit = tracePayload.manual_application_execution_preflight_observability_result || {};
      const simulation = tracePayload.manual_application_execution_simulation_preview_result || {};
      const simulationAudit = tracePayload.manual_application_execution_simulation_observability_result || {};
      const launchResult = await fetchJson(
        "/api/manual-guarded-application-execution-launch-request-create",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            execution_request_id: button.dataset.executionRequestId || preflightAudit.execution_request_id || preflight.execution_request_id || simulation.execution_request_id || "",
            approval_request_id: button.dataset.approvalRequestId || preflightAudit.approval_request_id || preflight.approval_request_id || simulation.approval_request_id || "",
            queue_handoff_id: button.dataset.queueHandoffId || preflightAudit.queue_handoff_id || preflight.queue_handoff_id || simulation.queue_handoff_id || "",
            reviewer_confirmation: Boolean(confirmation?.checked),
            application_execution_preflight_payload: preflight,
            application_execution_preflight_observability_payload: preflightAudit,
            application_execution_simulation_payload: simulation,
            application_execution_simulation_observability_payload: simulationAudit,
            reviewer_note: "",
            context_id: button.dataset.contextId || "",
            job_id: button.dataset.jobId || "",
          }),
        },
      );
      window.__agenticReviewTracePayload = {
        ...tracePayload,
        manual_guarded_application_execution_launch_request_create_result: launchResult,
      };
      const traceNode = qs("agenticReviewTracePanel");
      if (traceNode) {
        traceNode.outerHTML = renderAgentTraceReadOnlyPanel(window.__agenticReviewTracePayload);
      }
    } catch (err) {
      if (status) status.textContent = err?.message || "Manual guarded execution launch request creation failed.";
    } finally {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-manual-guarded-application-execution-launch-request-observability]");
    if (!button) return;
    const section = button.closest(".agent-trace-summary");
    const status = section?.querySelector("[data-manual-guarded-application-execution-launch-request-observability-status]");
    const previousDisabled = Boolean(button.disabled);
    button.disabled = true;
    if (status) status.textContent = "Reading guarded execution launch request audit...";
    try {
      const tracePayload = window.__agenticReviewTracePayload && typeof window.__agenticReviewTracePayload === "object"
        ? window.__agenticReviewTracePayload
        : {};
      const launchResult = tracePayload.manual_guarded_application_execution_launch_request_create_result || {};
      const auditResult = await fetchJson(
        "/api/manual-guarded-application-execution-launch-request-observability",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            guarded_application_execution_launch_request_payload: launchResult,
            execution_launch_request_id: button.dataset.executionLaunchRequestId || launchResult.execution_launch_request_id || "",
            execution_request_id: button.dataset.executionRequestId || launchResult.execution_request_id || "",
            approval_request_id: button.dataset.approvalRequestId || launchResult.approval_request_id || "",
            queue_handoff_id: button.dataset.queueHandoffId || launchResult.queue_handoff_id || "",
            context_id: button.dataset.contextId || launchResult.context_id || "",
            job_id: button.dataset.jobId || launchResult.job_id || "",
          }),
        },
      );
      window.__agenticReviewTracePayload = {
        ...tracePayload,
        manual_guarded_application_execution_launch_request_observability_result: auditResult,
      };
      const traceNode = qs("agenticReviewTracePanel");
      if (traceNode) {
        traceNode.outerHTML = renderAgentTraceReadOnlyPanel(window.__agenticReviewTracePayload);
      }
    } catch (err) {
      if (status) status.textContent = err?.message || "Manual guarded execution launch request audit failed.";
    } finally {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-manual-application-execution-launch-request-readback]");
    if (!button) return;
    const section = button.closest(".agent-trace-summary");
    const status = section?.querySelector("[data-manual-application-execution-launch-request-readback-status]");
    const previousDisabled = Boolean(button.disabled);
    button.disabled = true;
    if (status) status.textContent = "Reading execution launch request details...";
    try {
      const tracePayload = window.__agenticReviewTracePayload && typeof window.__agenticReviewTracePayload === "object"
        ? window.__agenticReviewTracePayload
        : {};
      const launchResult = tracePayload.manual_guarded_application_execution_launch_request_create_result || {};
      const auditResult = tracePayload.manual_guarded_application_execution_launch_request_observability_result || {};
      const readbackResult = await fetchJson(
        "/api/manual-application-execution-launch-request-readback",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            execution_launch_request_id: button.dataset.executionLaunchRequestId || auditResult.execution_launch_request_id || launchResult.execution_launch_request_id || "",
            execution_request_id: button.dataset.executionRequestId || auditResult.execution_request_id || launchResult.execution_request_id || "",
            approval_request_id: button.dataset.approvalRequestId || auditResult.approval_request_id || launchResult.approval_request_id || "",
            queue_handoff_id: button.dataset.queueHandoffId || auditResult.queue_handoff_id || launchResult.queue_handoff_id || "",
            guarded_application_execution_launch_request_payload: launchResult,
            application_execution_launch_request_observability_payload: auditResult,
            context_id: button.dataset.contextId || auditResult.context_id || launchResult.context_id || "",
            job_id: button.dataset.jobId || auditResult.job_id || launchResult.job_id || "",
          }),
        },
      );
      window.__agenticReviewTracePayload = {
        ...tracePayload,
        manual_application_execution_launch_request_readback_result: readbackResult,
      };
      const traceNode = qs("agenticReviewTracePanel");
      if (traceNode) {
        traceNode.outerHTML = renderAgentTraceReadOnlyPanel(window.__agenticReviewTracePayload);
      }
    } catch (err) {
      if (status) status.textContent = err?.message || "Manual execution launch request readback failed.";
    } finally {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-manual-execution-launch-request-status-transition-preview]");
    if (!button) return;
    const section = button.closest(".agent-trace-summary");
    const selector = section?.querySelector("[data-manual-execution-launch-request-status-transition-preview-select]");
    const status = section?.querySelector("[data-manual-execution-launch-request-status-transition-preview-status]");
    const previousDisabled = Boolean(button.disabled);
    button.disabled = true;
    if (status) status.textContent = "Previewing execution launch request status transition...";
    try {
      const tracePayload = window.__agenticReviewTracePayload && typeof window.__agenticReviewTracePayload === "object"
        ? window.__agenticReviewTracePayload
        : {};
      const readback = tracePayload.manual_application_execution_launch_request_readback_result || {};
      const launchResult = tracePayload.manual_guarded_application_execution_launch_request_create_result || {};
      const auditResult = tracePayload.manual_guarded_application_execution_launch_request_observability_result || {};
      const previewResult = await fetchJson(
        "/api/manual-execution-launch-request-status-transition-preview-dry-run",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            execution_launch_request_id: button.dataset.executionLaunchRequestId || readback.execution_launch_request_id || auditResult.execution_launch_request_id || launchResult.execution_launch_request_id || "",
            requested_transition: selector?.value || "",
            application_execution_launch_request_readback_payload: readback,
            guarded_application_execution_launch_request_payload: launchResult,
            application_execution_launch_request_observability_payload: auditResult,
            execution_request_id: button.dataset.executionRequestId || readback.execution_request_id || auditResult.execution_request_id || launchResult.execution_request_id || "",
            approval_request_id: button.dataset.approvalRequestId || readback.approval_request_id || auditResult.approval_request_id || launchResult.approval_request_id || "",
            queue_handoff_id: button.dataset.queueHandoffId || readback.queue_handoff_id || auditResult.queue_handoff_id || launchResult.queue_handoff_id || "",
            reviewer_note: "",
            context_id: button.dataset.contextId || readback.context_id || auditResult.context_id || launchResult.context_id || "",
            job_id: button.dataset.jobId || readback.job_id || auditResult.job_id || launchResult.job_id || "",
          }),
        },
      );
      window.__agenticReviewTracePayload = {
        ...tracePayload,
        manual_execution_launch_request_status_transition_preview_result: previewResult,
      };
      const traceNode = qs("agenticReviewTracePanel");
      if (traceNode) {
        traceNode.outerHTML = renderAgentTraceReadOnlyPanel(window.__agenticReviewTracePayload);
      }
    } catch (err) {
      if (status) status.textContent = err?.message || "Manual execution launch request status transition preview failed.";
    } finally {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-manual-guarded-execution-launch-request-status-transition]");
    if (!button) return;
    const section = button.closest(".agent-trace-summary");
    const confirmation = section?.querySelector("[data-manual-guarded-execution-launch-request-status-transition-confirmation]");
    const status = section?.querySelector("[data-manual-guarded-execution-launch-request-status-transition-status]");
    const previousDisabled = Boolean(button.disabled);
    button.disabled = true;
    if (status) status.textContent = "Applying guarded execution launch request status...";
    try {
      const tracePayload = window.__agenticReviewTracePayload && typeof window.__agenticReviewTracePayload === "object"
        ? window.__agenticReviewTracePayload
        : {};
      const preview = tracePayload.manual_execution_launch_request_status_transition_preview_result || {};
      const readback = tracePayload.manual_application_execution_launch_request_readback_result || {};
      const launchResult = tracePayload.manual_guarded_application_execution_launch_request_create_result || {};
      const auditResult = tracePayload.manual_guarded_application_execution_launch_request_observability_result || {};
      const transitionResult = await fetchJson(
        "/api/manual-guarded-execution-launch-request-status-transition",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            execution_launch_request_id: button.dataset.executionLaunchRequestId || preview.execution_launch_request_id || readback.execution_launch_request_id || "",
            requested_transition: button.dataset.requestedTransition || preview.requested_transition || "ready_for_manual_execution",
            reviewer_confirmation: Boolean(confirmation?.checked),
            execution_launch_request_status_transition_preview_payload: preview,
            application_execution_launch_request_readback_payload: readback,
            guarded_application_execution_launch_request_payload: launchResult,
            application_execution_launch_request_observability_payload: auditResult,
            execution_request_id: button.dataset.executionRequestId || preview.execution_request_id || readback.execution_request_id || "",
            approval_request_id: button.dataset.approvalRequestId || preview.approval_request_id || readback.approval_request_id || "",
            queue_handoff_id: button.dataset.queueHandoffId || preview.queue_handoff_id || readback.queue_handoff_id || "",
            reviewer_note: "",
            context_id: button.dataset.contextId || preview.context_id || readback.context_id || "",
            job_id: button.dataset.jobId || preview.job_id || readback.job_id || "",
          }),
        },
      );
      window.__agenticReviewTracePayload = {
        ...tracePayload,
        manual_guarded_execution_launch_request_status_transition_result: transitionResult,
      };
      const traceNode = qs("agenticReviewTracePanel");
      if (traceNode) {
        traceNode.outerHTML = renderAgentTraceReadOnlyPanel(window.__agenticReviewTracePayload);
      }
    } catch (err) {
      if (status) status.textContent = err?.message || "Manual guarded execution launch request status transition failed.";
    } finally {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-manual-guarded-execution-launch-request-status-transition-observability]");
    if (!button) return;
    const section = button.closest(".agent-trace-summary");
    const status = section?.querySelector("[data-manual-guarded-execution-launch-request-status-transition-observability-status]");
    const previousDisabled = Boolean(button.disabled);
    button.disabled = true;
    if (status) status.textContent = "Reading execution launch status audit...";
    try {
      const tracePayload = window.__agenticReviewTracePayload && typeof window.__agenticReviewTracePayload === "object"
        ? window.__agenticReviewTracePayload
        : {};
      const transition = tracePayload.manual_guarded_execution_launch_request_status_transition_result || {};
      const auditResult = await fetchJson(
        "/api/manual-guarded-execution-launch-request-status-transition-observability",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            guarded_execution_launch_request_status_transition_payload: transition,
            execution_launch_request_id: button.dataset.executionLaunchRequestId || transition.execution_launch_request_id || "",
            execution_request_id: button.dataset.executionRequestId || transition.execution_request_id || "",
            approval_request_id: button.dataset.approvalRequestId || transition.approval_request_id || "",
            queue_handoff_id: button.dataset.queueHandoffId || transition.queue_handoff_id || "",
            context_id: button.dataset.contextId || transition.context_id || "",
            job_id: button.dataset.jobId || transition.job_id || "",
          }),
        },
      );
      window.__agenticReviewTracePayload = {
        ...tracePayload,
        manual_guarded_execution_launch_request_status_transition_observability_result: auditResult,
      };
      const traceNode = qs("agenticReviewTracePanel");
      if (traceNode) {
        traceNode.outerHTML = renderAgentTraceReadOnlyPanel(window.__agenticReviewTracePayload);
      }
    } catch (err) {
      if (status) status.textContent = err?.message || "Manual execution launch status audit failed.";
    } finally {
      window.setTimeout(() => {
        button.disabled = previousDisabled;
      }, 700);
    }
  });
}

async function initAgenticReviewPage() {
  bindAgenticReviewTabs();
  const runId = getAgenticReviewRunId();
  if (!runId) return;
  try {
    const [payload, feedbackPayload] = await Promise.all([
      fetchJson(`/profile/pipeline-runs/${encodeURIComponent(runId)}/agentic-review-data`),
      fetchJson(`/api/agent-feedback/summary?pipeline_run_id=${encodeURIComponent(runId)}&limit=50`).catch(() => ({})),
    ]);
    const traceNode = qs("agenticReviewTracePanel");
    if (traceNode) {
      traceNode.outerHTML = renderAgentTraceReadOnlyPanel({
        loading_state: true,
        found: false,
        agent_run: {},
        agent_steps: [],
        step_count: 0,
        empty_trace: true,
        safety_metadata: { read_only: true },
      });
    }
    const tracePayload = await fetchAgentTraceReadOnlyPayload(payload, runId).catch((err) => ({
      read_only_error: err?.message || "Agent trace could not be loaded.",
      found: false,
      agent_run: {},
      agent_steps: [],
      step_count: 0,
      empty_trace: true,
      safety_metadata: { read_only: true },
    }));
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

// Read-only Agent Trace panel fetch helper.
// Uses GET only. No approve, no apply, no submit, no run, no retry, no export.
// Displays ordered agent steps, validation_json, and safety metadata from the backend.
async function fetchReadOnlyAgentTrace(approvalRequestId, runId) {
  const traceUrl = `/api/agentic-approvals/${encodeURIComponent(approvalRequestId)}/agent-trace`;
  const response = await fetch(traceUrl, {
    method: "GET",
    headers: {
      "Accept": "application/json"
    }
  });

  if (!response.ok) {
    return {
      found: false,
      agent_run: null,
      agent_steps: [],
      step_count: 0,
      empty_trace: true,
      error: "Unable to load read-only agent trace."
    };
  }

  return response.json();
}
