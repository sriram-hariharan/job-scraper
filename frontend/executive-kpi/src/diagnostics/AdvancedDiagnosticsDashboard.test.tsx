import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { AdvancedDiagnosticsDashboard, type AdvancedDiagnosticsDiagnosticState, type AdvancedDiagnosticsState } from "./AdvancedDiagnosticsDashboard";

const HREFS = { advancedDiagnostics: "/advanced-diagnostics", scanWorkspace: "/scan-workspace" };
const OPTIONS = [{ scanId: "scan id/42", company: "Acme Corp", title: "Staff Engineer", resume: "resume_v2", status: "Reviewed", primary: "Acme Corp / Staff Engineer", secondary: "Resume: resume_v2 · Reviewed" }];
const valid = (extra: Record<string, unknown> = {}) => ({ validation_status: "valid", fallback_used: false, ...extra });
const VALID_TAILORING = valid({
  suggestion_count: 3,
  suggestions_preview: [
    { suggestion_id: "tailor-1", suggestion_type: "patch_ready", target_section: "experience", suggested_text: "Emphasize production orchestration", reason: "The existing evidence supports clearer alignment.", jd_signal_links: [{ field: "required_skills", signal: "orchestration" }], evidence_spans: ["Built Python pipelines."], risk_flags: [] },
    { suggestion_id: "tailor-2", suggestion_type: "guidance_only", suggested_text: "Consider platform language", reason: "Evidence is indirect.", jd_signal_links: [{ field: "preferred_skills", signal: "platform" }], evidence_spans: [] },
    { suggestion_id: "tailor-3", suggestion_type: "rejected", suggested_text: "Add unsupported scale metric", reason: "No resume evidence supports the metric.", risk_flags: ["unsupported_claim"] },
  ],
});
const VALID_EXACT = valid({
  proposed_change_count: 2,
  proposed_changes_preview: [
    { proposal_id: "proposal-1", change_type: "rewrite", target_section: "Experience", target_identifier: "role-1", current_text: "Built Python pipelines.", proposed_text: "Built reliable Python pipelines for production analytics.", change_reason: "Clarifies the production scope supported by the resume evidence.", jd_terms_supported: ["Python", "production analytics"], resume_evidence_used: ["Built Python pipelines."], risk_flags: [] },
    { proposal_id: "proposal-2", change_type: "keyword", target_section: "Skills", target_identifier: "skills" },
  ],
});
const VALID_ACCEPTANCE = valid({ approved_change_plan_id: "plan-1", accepted_proposal_count: 1, accepted_proposal_ids: ["proposal-1"] });
const VALID_COPY = valid({ guarded_resume_copy_artifact_id: "copy-1" });
const VALID_VERIFICATION = valid({ verified_artifact_id: "verified-1" });
const TAILORING_FAILURE = {
  validation_status: "fallback",
  fallback_used: true,
  fallback_error_class: "RuntimeError",
  provider: "groq",
  model: "openai/gpt-oss-120b",
  failure_category: "invalid_request",
  exception_class: "RuntimeError",
  http_status: 400,
  provider_error_type: "invalid_request_error",
  provider_error_code: "json_validate_failed",
  invalid_request_reason: "generated_schema_mismatch",
  provider_call_attempted: true,
  retry_performed: false,
  provider_fallback_performed: false,
};
const ANALYSES = { live_tailoring_suggestion_readback: VALID_TAILORING, live_exact_resume_change_proposal_readback: VALID_EXACT };
const READY_CHAIN = {
  verified_artifact_operator_review_packet_readback: valid({ operator_review_packet_id: "packet-1" }),
  verified_artifact_operator_decision_readback: valid({ operator_decision_value: "accepted" }),
  operator_approved_artifact_application_readiness_packet_readback: valid(),
  human_only_manual_application_handoff_packet_readback: valid(),
  human_only_handoff_audit_trail_readback: valid(),
  human_only_safety_boundary_summary_readback: valid(),
  human_only_workflow_readiness_checkpoint_readback: valid(),
};
const COMPLETE_ROWS = { ...ANALYSES, manual_exact_change_acceptance_readback: VALID_ACCEPTANCE, guarded_resume_copy_artifact_readback: VALID_COPY, guarded_resume_copy_artifact_verification_readback: VALID_VERIFICATION, ...READY_CHAIN };

function contextState(diagnosticState: AdvancedDiagnosticsDiagnosticState = {}): AdvancedDiagnosticsState {
  return { mode: "context", savedScanOptions: OPTIONS, selectedScanId: "scan id/42", context: { company: "Acme Corp", title: "Staff Engineer", resume: "resume v2", status: "Reviewed", contextId: "scan id/42", backToScanHref: "/scan-workspace?saved_scan_id=scan+id%2F42" }, hrefs: HREFS, diagnosticState };
}

function withReadbacks(rows: Record<string, Record<string, unknown>>, ambient: Record<string, Record<string, unknown>> = {}): AdvancedDiagnosticsDiagnosticState {
  return { readbacks: rows, validated_readbacks: Object.fromEntries(Object.entries(rows).filter(([, row]) => row.validation_status === "valid" && row.fallback_used === false)), ambient_readbacks: ambient };
}

function responseWith(state: AdvancedDiagnosticsDiagnosticState, stage: string, validResult = true) {
  return new Response(JSON.stringify({ ok: true, diagnostic_state: state, stage_results: [{ stage, valid: validResult, status: validResult ? "valid" : "fallback" }] }), { status: 200, headers: { "Content-Type": "application/json" } });
}

function renderAt(rows: Record<string, Record<string, unknown>> = {}, request = vi.fn()) {
  return render(<AdvancedDiagnosticsDashboard state={contextState(withReadbacks(rows))} request={request} />);
}

describe("AdvancedDiagnosticsDashboard — horizontal guided wizard", () => {
  it("renders real four-step navigation, one active pane, and locked future stages", () => {
    renderAt();
    const workflow = screen.getByRole("region", { name: "Scan diagnostic workflow" });
    expect(within(workflow).getByRole("button", { name: "Analyze" })).toHaveAttribute("aria-current", "step");
    expect(within(workflow).getByRole("button", { name: "Analyze" }).closest("li")).toHaveAttribute("data-state", "active");
    for (const name of ["Review changes — locked", "Verify copy — locked", "Ready — locked"]) expect(within(workflow).getByRole("button", { name })).toBeDisabled();
    expect(within(workflow).getByRole("button", { name: "Review changes — locked" }).closest("li")).toHaveAttribute("data-state", "locked");
    expect(screen.getByRole("heading", { name: "AI analysis" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Proposed resume changes" })).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Protected resume copy" })).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Manual application readiness" })).not.toBeInTheDocument();
  });

  it.each([
    ["Analyze", {}, "AI analysis"],
    ["Review", ANALYSES, "Proposed resume changes"],
    ["Verify", { ...ANALYSES, manual_exact_change_acceptance_readback: VALID_ACCEPTANCE }, "Protected resume copy"],
    ["Ready after verification", { ...ANALYSES, manual_exact_change_acceptance_readback: VALID_ACCEPTANCE, guarded_resume_copy_artifact_readback: VALID_COPY, guarded_resume_copy_artifact_verification_readback: VALID_VERIFICATION }, "Manual application readiness"],
    ["Ready when complete", { ...ANALYSES, manual_exact_change_acceptance_readback: VALID_ACCEPTANCE, guarded_resume_copy_artifact_readback: VALID_COPY, guarded_resume_copy_artifact_verification_readback: VALID_VERIFICATION, ...READY_CHAIN }, "Manual application readiness"],
  ])("derives the deterministic initial step: %s", (_case, rows, heading) => {
    renderAt(rows);
    expect(screen.getByRole("heading", { name: heading })).toBeInTheDocument();
  });

  it("allows unlocked step navigation without a request", () => {
    const request = vi.fn();
    renderAt({ ...ANALYSES, manual_exact_change_acceptance_readback: VALID_ACCEPTANCE }, request);
    fireEvent.click(screen.getByRole("button", { name: "Analyze" }));
    expect(screen.getByRole("heading", { name: "AI analysis" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Review changes" }));
    expect(screen.getByRole("heading", { name: "Proposed resume changes" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Verify copy" }));
    expect(screen.getByRole("heading", { name: "Protected resume copy" })).toBeInTheDocument();
    const lockedReady = screen.getByRole("button", { name: "Ready — locked" });
    fireEvent.click(lockedReady);
    expect(lockedReady).toBeDisabled();
    expect(request).not.toHaveBeenCalled();
  });

  it("keeps context ID in secondary Technical details", () => {
    renderAt();
    const workflow = screen.getByRole("region", { name: "Scan diagnostic workflow" });
    expect(within(workflow).queryByText("scan id/42")).not.toBeInTheDocument();
    expect(document.getElementById("advancedDiagnosticsSectionReadbacks")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Technical details" }));
    const details = screen.getByRole("dialog", { name: "Technical details" });
    expect(details).toHaveClass("advanced-diagnostics-technical-drawer");
    expect(within(details).getByText("scan id/42")).toBeInTheDocument();
    for (const section of ["Scan", "AI providers", "Workflow"]) expect(within(details).getByRole("heading", { name: section })).toBeInTheDocument();
    const tailoringReadback = document.getElementById("scanWorkspaceTailoringLlmReadback");
    expect(tailoringReadback).toHaveClass("advanced-diagnostics-readback-row");
    expect(tailoringReadback?.parentElement).toHaveClass("advanced-diagnostics-technical-list");
  });

  it("distinguishes completed and attention steps while preserving downstream Ready completion", () => {
    renderAt({
      live_tailoring_suggestion_readback: TAILORING_FAILURE,
      live_exact_resume_change_proposal_readback: VALID_EXACT,
      manual_exact_change_acceptance_readback: VALID_ACCEPTANCE,
      guarded_resume_copy_artifact_readback: VALID_COPY,
      guarded_resume_copy_artifact_verification_readback: VALID_VERIFICATION,
      ...READY_CHAIN,
    });
    const workflow = screen.getByRole("region", { name: "Scan diagnostic workflow" });
    expect(within(workflow).getByRole("button", { name: "Analyze" }).closest("li")).toHaveAttribute("data-state", "attention");
    expect(within(workflow).getByRole("button", { name: "Review changes" }).closest("li")).toHaveAttribute("data-state", "completed");
    expect(within(workflow).getByRole("button", { name: "Ready" })).toHaveAttribute("aria-current", "step");
    expect(screen.getByText("Ready for manual application")).toBeInTheDocument();
  });

  it("uses Viewing semantics when a completed workflow pane is revisited", () => {
    renderAt({ ...ANALYSES, manual_exact_change_acceptance_readback: VALID_ACCEPTANCE, guarded_resume_copy_artifact_readback: VALID_COPY, guarded_resume_copy_artifact_verification_readback: VALID_VERIFICATION, ...READY_CHAIN });
    fireEvent.click(screen.getByRole("button", { name: "Analyze" }));
    expect(screen.getByText("Viewing: Analyze")).toBeInTheDocument();
    expect(screen.getByText("4 of 4 workflow stages complete")).toBeInTheDocument();
    expect(screen.queryByText("Stage 1 of 4")).not.toBeInTheDocument();
    const viewedStep = screen.getByRole("button", { name: "Analyze" }).closest("li");
    expect(viewedStep).toHaveAttribute("data-state", "completed");
    expect(viewedStep).toHaveAttribute("data-viewing", "true");
    expect(viewedStep).toHaveClass("is-complete", "is-current", "is-viewing");
    expect(within(viewedStep!).getByText("Completed")).toBeInTheDocument();
    expect(within(viewedStep!).getByText("Viewing")).toBeInTheDocument();
    expect(Array.from(screen.getAllByRole("button", { name: /Analyze|Review changes|Verify copy|Ready/ })).some((button) => Array.from(button.classList).some((name) => /gradient/.test(name)))).toBe(false);
  });

  it("opens and closes the Technical details drawer locally with Escape", () => {
    const request = vi.fn();
    renderAt({}, request);
    fireEvent.click(screen.getByRole("button", { name: "Technical details" }));
    const drawer = screen.getByRole("dialog", { name: "Technical details" });
    expect(drawer).toBeInTheDocument();
    expect(drawer).toHaveAttribute("aria-modal", "true");
    expect(drawer.parentElement).toHaveClass("advanced-diagnostics-drawer-backdrop");
    expect(drawer.parentElement).toHaveAttribute("data-overlay-layer", "diagnostics");
    expect(drawer.closest("#advancedDiagnosticsRoot")).toBeNull();
    expect(document.body.style.overflow).toBe("hidden");
    const close = screen.getByRole("button", { name: "Close technical details" });
    expect(close).toHaveFocus();
    expect(close).toHaveClass("advanced-diagnostics-close-control");
    expect(close.querySelector("svg")).toBeInTheDocument();
    expect(close.querySelector("svg")).toHaveAttribute("width", "20");
    expect(close).not.toHaveClass("advanced-diagnostics-dialog-primary");
    expect(Array.from(close.classList).some((name) => /gradient|filled|accent-tile/.test(name))).toBe(false);
    fireEvent.click(close);
    expect(screen.queryByRole("dialog", { name: "Technical details" })).not.toBeInTheDocument();
    expect(document.body.style.overflow).toBe("");
    fireEvent.click(screen.getByRole("button", { name: "Technical details" }));
    fireEvent.keyDown(document, { key: "Escape" });
    expect(screen.queryByRole("dialog", { name: "Technical details" })).not.toBeInTheDocument();
    expect(request).not.toHaveBeenCalled();
  });
});

describe("AdvancedDiagnosticsDashboard — Analyze and status consistency", () => {
  it("renders real tailoring review fields and distinct classifications", () => {
    renderAt({ live_tailoring_suggestion_readback: VALID_TAILORING });
    expect(screen.getByText("3 recommendations")).toBeInTheDocument();
    for (const label of ["Patch-ready", "Guidance", "Rejected / unsupported"]) expect(screen.getByText(label)).toBeInTheDocument();
    expect(screen.getByText("The existing evidence supports clearer alignment.")).toBeInTheDocument();
    expect(screen.getByText("required_skills · orchestration")).toBeInTheDocument();
  });

  it("shows the newest failed tailoring execution everywhere instead of stale completed content", () => {
    const state: AdvancedDiagnosticsDiagnosticState = { readbacks: { live_tailoring_suggestion_readback: TAILORING_FAILURE }, validated_readbacks: { live_tailoring_suggestion_readback: VALID_TAILORING } };
    render(<AdvancedDiagnosticsDashboard state={contextState(state)} />);
    const analyze = document.getElementById("advancedDiagnosticsSectionGeneration");
    expect(within(analyze!).getByText("The AI provider could not return a valid structured result for the latest analysis.")).toBeInTheDocument();
    expect(within(analyze!).getByText("Needs attention")).toBeInTheDocument();
    expect(within(analyze!).getByRole("button", { name: "Retry tailoring analysis" })).toBeInTheDocument();
    expect(within(analyze!).queryByText("openai/gpt-oss-120b")).not.toBeInTheDocument();
    expect(within(analyze!).queryByText("Generated Schema Mismatch")).not.toBeInTheDocument();
    expect(screen.queryByText("Emphasize production orchestration")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Technical details" }));
    const technicalReadback = document.getElementById("scanWorkspaceTailoringLlmReadback");
    expect(technicalReadback).toHaveTextContent("Failed");
    for (const value of ["Groq", "openai/gpt-oss-120b", "Invalid Request", "400", "Json Validate Failed", "Generated Schema Mismatch", "No"]) {
      expect(technicalReadback).toHaveTextContent(value);
    }
  });

  it("keeps Technical details stable when optional provider failure fields are absent", () => {
    renderAt({ live_tailoring_suggestion_readback: { validation_status: "fallback", fallback_used: true, fallback_error_class: "RuntimeError", provider: "groq", model: "openai/gpt-oss-120b", failure_category: "provider_adapter_error", exception_class: "RuntimeError", provider_call_attempted: true, retry_performed: false, provider_fallback_performed: false } });
    fireEvent.click(screen.getByRole("button", { name: "Technical details" }));
    const technicalReadback = document.getElementById("scanWorkspaceTailoringLlmReadback");
    expect(technicalReadback).toHaveTextContent("Provider Adapter Error");
    expect(technicalReadback).not.toHaveTextContent("HTTP");
    expect(technicalReadback).not.toHaveTextContent("Parameter");
  });

  it("distinguishes valid-zero, failed, and disabled states", () => {
    const state = withReadbacks({
      live_tailoring_suggestion_readback: valid({ suggestion_count: 0, suggestions_preview: [] }),
      live_exact_resume_change_proposal_readback: { validation_status: "fallback", fallback_used: true, fallback_error_class: "RuntimeError" },
    }, { jd_llm_extraction_readback: { validation_status: "disabled", fallback_used: true, fallback_reason: "feature_flag_disabled", validation_errors: ["feature_flag_disabled"] } });
    render(<AdvancedDiagnosticsDashboard state={contextState(state)} />);
    expect(screen.getByText("0 supported recommendations")).toBeInTheDocument();
    expect(screen.getByText("No supported tailoring recommendations were produced for this scan.")).toBeInTheDocument();
    expect(screen.getAllByText("Completed").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Failed").length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole("button", { name: "Technical details" }));
    expect(document.getElementById("scanWorkspaceJdLlmReadback")).toHaveTextContent("feature_flag_disabledDisabled");
    expect(document.getElementById("scanWorkspaceJdLlmReadback")).not.toHaveTextContent("Provider failed");
  });

  it("runs one analysis only after its contextual button is clicked", async () => {
    const request = vi.fn().mockResolvedValue(responseWith(withReadbacks({ live_tailoring_suggestion_readback: VALID_TAILORING }), "live_tailoring_suggestion"));
    renderAt({}, request);
    expect(request).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Run tailoring analysis" }));
    await waitFor(() => expect(request).toHaveBeenCalledTimes(1));
    expect(JSON.parse(String((request.mock.calls[0][1] as RequestInit).body))).toEqual({ diagnostics_execution: true, diagnostic_stages: ["live_tailoring_suggestion"] });
  });

  it("runs exactly one explicit tailoring retry, disables it in flight, and renders the persisted result", async () => {
    let resolveResponse: ((value: Response) => void) | undefined;
    const request = vi.fn().mockImplementation(() => new Promise<Response>((resolve) => { resolveResponse = resolve; }));
    renderAt({ live_tailoring_suggestion_readback: TAILORING_FAILURE, live_exact_resume_change_proposal_readback: VALID_EXACT }, request);
    fireEvent.click(screen.getByRole("button", { name: "Analyze" }));
    const retry = screen.getByRole("button", { name: "Retry tailoring analysis" });
    fireEvent.click(retry);
    expect(request).toHaveBeenCalledTimes(1);
    expect(screen.getByRole("button", { name: "Retry tailoring analysis" })).toBeDisabled();
    expect(JSON.parse(String((request.mock.calls[0][1] as RequestInit).body))).toEqual({ diagnostics_execution: true, diagnostic_stages: ["live_tailoring_suggestion"] });
    resolveResponse?.(responseWith(withReadbacks(ANALYSES), "live_tailoring_suggestion"));
    expect(await screen.findByText("Emphasize production orchestration")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "AI analysis" })).toBeInTheDocument();
    expect(request).toHaveBeenCalledTimes(1);
  });

  it("keeps a failed manual retry available without an automatic retry", async () => {
    const failedState = withReadbacks({ live_tailoring_suggestion_readback: TAILORING_FAILURE, live_exact_resume_change_proposal_readback: VALID_EXACT });
    const request = vi.fn().mockResolvedValue(responseWith(failedState, "live_tailoring_suggestion", false));
    renderAt({ live_tailoring_suggestion_readback: TAILORING_FAILURE, live_exact_resume_change_proposal_readback: VALID_EXACT }, request);
    fireEvent.click(screen.getByRole("button", { name: "Analyze" }));
    fireEvent.click(screen.getByRole("button", { name: "Retry tailoring analysis" }));
    await waitFor(() => expect(screen.getByRole("button", { name: "Retry tailoring analysis" })).toBeEnabled());
    expect(screen.getByText("The AI provider could not return a valid structured result for the latest analysis.")).toBeInTheDocument();
    expect(screen.getAllByText("Needs attention").length).toBeGreaterThan(0);
    expect(request).toHaveBeenCalledTimes(1);
  });

  it("advances to Review only when the final analysis succeeds", async () => {
    const request = vi.fn().mockResolvedValue(responseWith(withReadbacks(ANALYSES), "live_exact_resume_change_proposal"));
    renderAt({ live_tailoring_suggestion_readback: VALID_TAILORING }, request);
    fireEvent.click(screen.getByRole("button", { name: "Live exact change proposals" }));
    expect(await screen.findByRole("heading", { name: "Proposed resume changes" })).toBeInTheDocument();
    expect(request).toHaveBeenCalledTimes(1);
  });
});

describe("AdvancedDiagnosticsDashboard — Review changes", () => {
  it("preserves exact review fields, empty current selection, and separate persisted approval", () => {
    renderAt({ ...ANALYSES, manual_exact_change_acceptance_readback: VALID_ACCEPTANCE });
    fireEvent.click(screen.getByRole("button", { name: "Review changes" }));
    const card = screen.getByText("Proposal ID · proposal-1").closest("label");
    expect(card).not.toBeNull();
    for (const label of ["Current", "Proposed", "Reason", "JD terms", "Evidence", "production analytics"]) expect(within(card!).getByText(label)).toBeInTheDocument();
    expect(card!.querySelector("input")).not.toBeChecked();
    expect(screen.getByText("Current selection · 0 currently selected")).toBeInTheDocument();
    expect(screen.getByText("Previously approved")).toBeInTheDocument();
    expect(screen.getByText("1 exact change previously approved")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Accept selected exact changes" })).toBeDisabled();
  });

  it("opens review locally, submits exact IDs once, and auto-advances to Verify", async () => {
    const next = withReadbacks({ ...ANALYSES, manual_exact_change_acceptance_readback: VALID_ACCEPTANCE });
    const request = vi.fn().mockResolvedValue(responseWith(next, "manual_exact_change_acceptance"));
    renderAt(ANALYSES, request);
    fireEvent.click(screen.getByText("Proposal ID · proposal-1"));
    expect(request).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Accept selected exact changes" }));
    const dialog = screen.getByRole("dialog", { name: "Review resume changes" });
    expect(within(dialog).getByText("Built reliable Python pipelines for production analytics.")).toBeInTheDocument();
    fireEvent.click(within(dialog).getByRole("button", { name: "Accept selected changes" }));
    expect(await screen.findByRole("heading", { name: "Protected resume copy" })).toBeInTheDocument();
    expect(request).toHaveBeenCalledTimes(1);
    expect(JSON.parse(String((request.mock.calls[0][1] as RequestInit).body))).toMatchObject({ diagnostic_stages: ["manual_exact_change_acceptance"], accepted_exact_change_proposal_ids: ["proposal-1"] });
  });

  it("cancels the review modal without a request", () => {
    const request = vi.fn();
    renderAt(ANALYSES, request);
    fireEvent.click(screen.getByText("Proposal ID · proposal-1"));
    fireEvent.click(screen.getByRole("button", { name: "Accept selected exact changes" }));
    const cancel = within(screen.getByRole("dialog")).getByRole("button", { name: "Cancel" });
    expect(cancel).toHaveClass("advanced-diagnostics-dialog-secondary", "advanced-diagnostics-dialog-cancel");
    expect(cancel).not.toHaveClass("advanced-diagnostics-dialog-primary");
    fireEvent.click(cancel);
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(request).not.toHaveBeenCalled();
  });

  it("closes review from the visible neutral X without a request", () => {
    const request = vi.fn();
    renderAt(ANALYSES, request);
    fireEvent.click(screen.getByText("Proposal ID · proposal-1"));
    fireEvent.click(screen.getByRole("button", { name: "Accept selected exact changes" }));
    const close = within(screen.getByRole("dialog", { name: "Review resume changes" })).getByRole("button", { name: "Close" });
    expect(close).toHaveClass("advanced-diagnostics-close-control", "advanced-diagnostics-dialog-close");
    const icon = close.querySelector("svg");
    expect(icon).toBeInTheDocument();
    expect(icon).toHaveAttribute("width", "20");
    expect(icon).toHaveAttribute("height", "20");
    expect(close).not.toHaveClass("advanced-diagnostics-dialog-primary");
    expect(Array.from(close.classList).some((name) => /gradient|filled|accent-tile/.test(name))).toBe(false);
    fireEvent.click(close);
    expect(screen.queryByRole("dialog", { name: "Review resume changes" })).not.toBeInTheDocument();
    expect(request).not.toHaveBeenCalled();
  });
});

describe("AdvancedDiagnosticsDashboard — Verify and Ready", () => {
  it("shows one contextual copy action and auto-advances only after verification", async () => {
    const beforeVerify = { ...ANALYSES, manual_exact_change_acceptance_readback: VALID_ACCEPTANCE, guarded_resume_copy_artifact_readback: VALID_COPY };
    const afterVerify = withReadbacks({ ...beforeVerify, guarded_resume_copy_artifact_verification_readback: VALID_VERIFICATION });
    const request = vi.fn().mockResolvedValue(responseWith(afterVerify, "guarded_resume_copy_artifact_verification"));
    renderAt(beforeVerify, request);
    fireEvent.click(screen.getByRole("button", { name: "Verify guarded resume copy" }));
    expect(await screen.findByRole("heading", { name: "Manual application readiness" })).toBeInTheDocument();
    expect(request).toHaveBeenCalledTimes(1);
  });

  it("renders one next Ready action and preserves explicit operator decision", async () => {
    const readyRows = { ...ANALYSES, manual_exact_change_acceptance_readback: VALID_ACCEPTANCE, guarded_resume_copy_artifact_readback: VALID_COPY, guarded_resume_copy_artifact_verification_readback: VALID_VERIFICATION, verified_artifact_operator_review_packet_readback: valid({ operator_review_packet_id: "packet-1", artifact_id: "artifact-1" }) };
    const request = vi.fn().mockResolvedValue(responseWith(withReadbacks(readyRows), "verified_artifact_operator_decision"));
    renderAt(readyRows, request);
    expect(document.querySelectorAll(".advanced-diagnostics-primary-action")).toHaveLength(1);
    fireEvent.click(screen.getByRole("button", { name: "Capture verified artifact operator decision" }));
    const dialog = screen.getByRole("dialog", { name: "Review protected resume" });
    for (const label of ["Accepted", "Rejected", "Needs Changes"]) expect(within(dialog).getByRole("button", { name: label })).toBeInTheDocument();
    expect(within(dialog).getByRole("button", { name: "Rejected" })).toHaveClass("advanced-diagnostics-dialog-action--danger");
    expect(within(dialog).getByRole("button", { name: "Needs Changes" })).toHaveClass("advanced-diagnostics-dialog-action--warning");
    expect(within(dialog).getByRole("button", { name: "Accepted" })).toHaveClass("advanced-diagnostics-dialog-action--success");
    expect(within(dialog).getByRole("button", { name: "Cancel" })).toHaveClass("advanced-diagnostics-dialog-cancel");
    expect(within(dialog).getByText("Protected resume artifact is ready for review.")).toBeInTheDocument();
    expect(within(dialog).queryByText(/packet-1|operator review packet id/i)).not.toBeInTheDocument();
    expect(within(dialog).getByRole("button", { name: "Close" }).querySelector("svg")).toHaveAttribute("width", "20");
    expect(request).not.toHaveBeenCalled();
    fireEvent.click(within(dialog).getByRole("button", { name: "Rejected" }));
    await waitFor(() => expect(request).toHaveBeenCalledTimes(1));
    expect(JSON.parse(String((request.mock.calls[0][1] as RequestInit).body))).toMatchObject({ diagnostic_stages: ["verified_artifact_operator_decision"], verified_artifact_operator_decision_value: "rejected" });
  });

  it("closes the operator decision modal from its X without a request", () => {
    const readyRows = { ...ANALYSES, manual_exact_change_acceptance_readback: VALID_ACCEPTANCE, guarded_resume_copy_artifact_readback: VALID_COPY, guarded_resume_copy_artifact_verification_readback: VALID_VERIFICATION, verified_artifact_operator_review_packet_readback: valid({ operator_review_packet_id: "packet-1" }) };
    const request = vi.fn();
    renderAt(readyRows, request);
    fireEvent.click(screen.getByRole("button", { name: "Capture verified artifact operator decision" }));
    fireEvent.click(within(screen.getByRole("dialog", { name: "Review protected resume" })).getByRole("button", { name: "Close" }));
    expect(screen.queryByRole("dialog", { name: "Review protected resume" })).not.toBeInTheDocument();
    expect(request).not.toHaveBeenCalled();
  });

  it("offers same-scan rerun only for a terminal completed workflow", () => {
    const request = vi.fn();
    const { unmount } = render(<AdvancedDiagnosticsDashboard state={contextState(withReadbacks(COMPLETE_ROWS))} request={request} />);
    const rerun = screen.getByRole("button", { name: "Run diagnostics again" });
    expect(rerun).toHaveClass("advanced-diagnostics-secondary-action", "advanced-diagnostics-rerun-action");
    expect(request).not.toHaveBeenCalled();

    unmount();
    render(<AdvancedDiagnosticsDashboard state={contextState(withReadbacks({ ...ANALYSES, manual_exact_change_acceptance_readback: VALID_ACCEPTANCE }))} request={request} />);
    expect(screen.queryByRole("button", { name: "Run diagnostics again" })).not.toBeInTheDocument();
    expect(request).not.toHaveBeenCalled();
  });

  it("opens the rerun confirmation and Cancel sends zero requests", () => {
    const request = vi.fn();
    renderAt(COMPLETE_ROWS, request);
    fireEvent.click(screen.getByRole("button", { name: "Run diagnostics again" }));
    const dialog = screen.getByRole("dialog", { name: "Run diagnostics again?" });
    expect(within(dialog).getByText("Start a new diagnostics workflow")).toBeInTheDocument();
    expect(within(dialog).getByText(/saved scan, job details, and original resume will stay unchanged/i)).toBeInTheDocument();
    expect(within(dialog).getByText("Current diagnostics results")).toBeInTheDocument();
    expect(within(dialog).getByText("Original resume")).toBeInTheDocument();
    expect(request).not.toHaveBeenCalled();
    fireEvent.click(within(dialog).getByRole("button", { name: "Cancel" }));
    expect(screen.queryByRole("dialog", { name: "Run diagnostics again?" })).not.toBeInTheDocument();
    expect(request).not.toHaveBeenCalled();
  });

  it("confirms exactly one reset-only request and renders the authoritative fresh state", async () => {
    let resolveResponse: ((value: Response) => void) | undefined;
    const request = vi.fn().mockImplementation(() => new Promise<Response>((resolve) => { resolveResponse = resolve; }));
    renderAt(COMPLETE_ROWS, request);
    fireEvent.click(screen.getByRole("button", { name: "Run diagnostics again" }));
    const dialog = screen.getByRole("dialog", { name: "Run diagnostics again?" });
    const confirm = within(dialog).getByRole("button", { name: "Run diagnostics again" });
    fireEvent.click(confirm);
    expect(request).toHaveBeenCalledTimes(1);
    expect(JSON.parse(String((request.mock.calls[0][1] as RequestInit).body))).toEqual({ diagnostics_reset: true });
    expect(within(dialog).getByRole("button", { name: "Resetting..." })).toBeDisabled();

    const freshState: AdvancedDiagnosticsDiagnosticState = {
      version: 1,
      scan_id: "scan id/42",
      readbacks: {},
      validated_readbacks: {},
      ambient_readbacks: {},
      human_inputs: {},
      last_execution: { requested_stages: [], stage_results: [], diagnostics_reset_performed: true },
    };
    resolveResponse?.(new Response(JSON.stringify({ ok: true, diagnostics_reset: true, diagnostic_state: freshState }), { status: 200, headers: { "Content-Type": "application/json" } }));

    expect(await screen.findByRole("heading", { name: "AI analysis" })).toBeInTheDocument();
    expect(screen.getByText("0 of 4 workflow stages complete")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Run tailoring analysis" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Live exact change proposals" })).toBeEnabled();
    const workflow = screen.getByRole("region", { name: "Scan diagnostic workflow" });
    for (const name of ["Review changes — locked", "Verify copy — locked", "Ready — locked"]) expect(within(workflow).getByRole("button", { name })).toBeDisabled();
    for (const oldContent of ["Emphasize production orchestration", "Proposal ID · proposal-1", "Previously approved", "Ready for manual application"]) expect(screen.queryByText(oldContent)).not.toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("Diagnostics workflow reset");
    expect(request).toHaveBeenCalledTimes(1);
  });

  it("renders a reloaded fresh reset readback without any request", () => {
    const request = vi.fn();
    const freshState: AdvancedDiagnosticsDiagnosticState = { version: 1, scan_id: "scan id/42", readbacks: {}, validated_readbacks: {}, ambient_readbacks: {}, human_inputs: {}, last_execution: { diagnostics_reset_performed: true } };
    render(<AdvancedDiagnosticsDashboard state={contextState(freshState)} request={request} />);
    expect(screen.getByRole("heading", { name: "AI analysis" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Run tailoring analysis" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Live exact change proposals" })).toBeEnabled();
    expect(request).not.toHaveBeenCalled();
  });

  it("does not retry or auto-advance a failed request", async () => {
    const request = vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: "Provider validation failed." }), { status: 400, headers: { "Content-Type": "application/json" } }));
    renderAt({}, request);
    fireEvent.click(screen.getByRole("button", { name: "Live exact change proposals" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Provider validation failed.");
    expect(screen.getByRole("heading", { name: "AI analysis" })).toBeInTheDocument();
    expect(request).toHaveBeenCalledTimes(1);
  });

  it("preserves the manual-only boundary language", () => {
    renderAt({ ...ANALYSES, manual_exact_change_acceptance_readback: VALID_ACCEPTANCE, guarded_resume_copy_artifact_readback: VALID_COPY, guarded_resume_copy_artifact_verification_readback: VALID_VERIFICATION });
    expect(screen.getByText(/does not automatically cross human review gates or submit applications/)).toBeInTheDocument();
    expect(screen.getByText(/has not submitted an application, contacted a recruiter/)).toBeInTheDocument();
  });
});

describe("AdvancedDiagnosticsDashboard — hub and neutral states", () => {
  it("keeps the saved-scan hub and encoded navigation", () => {
    const navigate = vi.fn();
    render(<AdvancedDiagnosticsDashboard state={{ mode: "hub", savedScanOptions: OPTIONS, selectedScanId: "", context: null, hrefs: HREFS }} navigate={navigate} />);
    fireEvent.click(screen.getByRole("button", { name: /saved scan/i }));
    fireEvent.click(screen.getByRole("option", { name: /Acme Corp/ }));
    fireEvent.click(screen.getByRole("button", { name: "Open diagnostics" }));
    expect(navigate).toHaveBeenCalledWith("/advanced-diagnostics?saved_scan_id=scan%20id%2F42");
  });

  it("preserves empty and owner-neutral invalid states", () => {
    const { rerender } = render(<AdvancedDiagnosticsDashboard state={{ mode: "empty", savedScanOptions: [], selectedScanId: "", context: null, hrefs: HREFS }} />);
    expect(screen.getByText("No saved scans available")).toBeInTheDocument();
    rerender(<AdvancedDiagnosticsDashboard state={{ mode: "invalid", savedScanOptions: OPTIONS, selectedScanId: "foreign", context: null, hrefs: HREFS }} />);
    expect(screen.getByText("Scan context unavailable")).toBeInTheDocument();
  });
});
