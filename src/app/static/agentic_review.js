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
      ${renderAgentTraceCriticEvaluatorSection(tracePayload)}
      ${renderManualJdIntelligenceDryRunSection(tracePayload)}
      ${renderManualResumeMatchDryRunSection(tracePayload)}
      ${renderManualTailoringSuggestionDryRunSection(tracePayload)}
      ${renderManualCriticGuardrailDryRunSection(tracePayload)}
      ${renderManualStrategyRecommendationDryRunSection(tracePayload)}
      ${renderManualShadowAgenticWorkflowChainDryRunSection(tracePayload)}
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
