import {
  AlertTriangle,
  ArrowDown,
  Check,
  CheckCircle2,
  ChevronDown,
  ClipboardCheck,
  Circle,
  Eye,
  FileQuestion,
  FileSearch,
  Inbox,
  LoaderCircle,
  LockKeyhole,
  ShieldCheck,
  Sparkles,
  X,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { SharedFilterSelect, type SharedFilterOption } from "../filter/FilterSelect";

export type AdvancedDiagnosticsSavedScanOption = {
  scanId: string;
  company: string;
  title: string;
  resume: string;
  status: string;
  primary: string;
  secondary: string;
};

export type AdvancedDiagnosticsContext = {
  company: string;
  title: string;
  resume: string;
  status: string;
  contextId: string;
  backToScanHref: string;
};

export type AdvancedDiagnosticsReadback = Record<string, unknown>;

export type AdvancedDiagnosticsDiagnosticState = {
  version?: number;
  scan_id?: string;
  updated_at?: string;
  readbacks?: Record<string, AdvancedDiagnosticsReadback>;
  validated_readbacks?: Record<string, AdvancedDiagnosticsReadback>;
  ambient_readbacks?: Record<string, AdvancedDiagnosticsReadback>;
  human_inputs?: Record<string, unknown>;
  last_execution?: Record<string, unknown>;
};

export type AdvancedDiagnosticsState = {
  mode: "hub" | "context" | "empty" | "invalid";
  savedScanOptions: AdvancedDiagnosticsSavedScanOption[];
  selectedScanId: string;
  context: AdvancedDiagnosticsContext | null;
  hrefs: { advancedDiagnostics: string; scanWorkspace: string };
  diagnosticState?: AdvancedDiagnosticsDiagnosticState;
};

export const DEFAULT_ADVANCED_DIAGNOSTICS_STATE: AdvancedDiagnosticsState = {
  mode: "empty",
  savedScanOptions: [],
  selectedScanId: "",
  context: null,
  hrefs: { advancedDiagnostics: "/advanced-diagnostics", scanWorkspace: "/scan-workspace" },
  diagnosticState: {},
};

declare global {
  interface Window {
    __APPLYLENS_ADVANCED_DIAGNOSTICS_STATE__?: AdvancedDiagnosticsState;
  }
}

export const DIAGNOSTIC_STAGE_ORDER = [
  "live_tailoring_suggestion",
  "live_exact_resume_change_proposal",
  "manual_exact_change_acceptance",
  "guarded_resume_copy_artifact",
  "guarded_resume_copy_artifact_verification",
  "verified_artifact_operator_review_packet",
  "verified_artifact_operator_decision",
  "application_readiness_packet",
  "manual_application_handoff_packet",
  "handoff_audit_trail",
  "safety_boundary_summary",
  "workflow_readiness_checkpoint",
] as const;

type DiagnosticStage = (typeof DIAGNOSTIC_STAGE_ORDER)[number];
type StageTone = "accent" | "success" | "warning";

type StageConfig = {
  stage: DiagnosticStage;
  id: string;
  label: string;
  description: string;
  readbackKey: string;
};

type StageGroup = {
  id: string;
  title: string;
  description: string;
  tone: StageTone;
  icon: typeof Sparkles;
  stages: StageConfig[];
};

const STAGE_GROUPS: StageGroup[] = [
  {
    id: "advancedDiagnosticsSectionGeneration",
    title: "Generation diagnostics",
    description: "Generate tailoring guidance and exact resume change proposals on demand.",
    tone: "accent",
    icon: Sparkles,
    stages: [
      {
        stage: "live_tailoring_suggestion",
        id: "scanWorkspaceLiveTailoringSuggestionToggle",
        label: "Live tailoring suggestions",
        description: "Ask the configured provider for saved-scan tailoring guidance.",
        readbackKey: "live_tailoring_suggestion_readback",
      },
      {
        stage: "live_exact_resume_change_proposal",
        id: "scanWorkspaceLiveExactChangeProposalToggle",
        label: "Live exact change proposals",
        description: "Generate exact, reviewable changes without editing the source resume.",
        readbackKey: "live_exact_resume_change_proposal_readback",
      },
    ],
  },
  {
    id: "advancedDiagnosticsSectionArtifactSafety",
    title: "Resume artifact safety",
    description: "Accept exact proposals, create a protected copy, and verify that artifact.",
    tone: "success",
    icon: ShieldCheck,
    stages: [
      {
        stage: "manual_exact_change_acceptance",
        id: "scanWorkspaceManualExactChangeAcceptanceToggle",
        label: "Accept selected exact changes",
        description: "Record only the proposal IDs explicitly selected below.",
        readbackKey: "manual_exact_change_acceptance_readback",
      },
      {
        stage: "guarded_resume_copy_artifact",
        id: "scanWorkspaceGuardedResumeCopyArtifactToggle",
        label: "Create guarded resume copy",
        description: "Create a protected copy from the validated change plan.",
        readbackKey: "guarded_resume_copy_artifact_readback",
      },
      {
        stage: "guarded_resume_copy_artifact_verification",
        id: "scanWorkspaceGuardedResumeCopyArtifactVerificationToggle",
        label: "Verify guarded resume copy",
        description: "Verify the guarded copy before it can enter operator review.",
        readbackKey: "guarded_resume_copy_artifact_verification_readback",
      },
    ],
  },
  {
    id: "advancedDiagnosticsSectionReviewDecision",
    title: "Review and decision",
    description: "Prepare a review packet, then capture an explicit operator decision.",
    tone: "accent",
    icon: FileSearch,
    stages: [
      {
        stage: "verified_artifact_operator_review_packet",
        id: "scanWorkspaceVerifiedArtifactOperatorReviewPacketToggle",
        label: "Create verified artifact review packet",
        description: "Package the verified artifact for human review.",
        readbackKey: "verified_artifact_operator_review_packet_readback",
      },
      {
        stage: "verified_artifact_operator_decision",
        id: "scanWorkspaceVerifiedArtifactOperatorDecisionToggle",
        label: "Capture verified artifact operator decision",
        description: "Persist the explicit decision selected below. No decision is preselected.",
        readbackKey: "verified_artifact_operator_decision_readback",
      },
    ],
  },
  {
    id: "advancedDiagnosticsSectionManualHandoff",
    title: "Manual handoff and readiness",
    description: "Build the remaining human-only readiness and audit chain.",
    tone: "warning",
    icon: Inbox,
    stages: [
      {
        stage: "application_readiness_packet",
        id: "scanWorkspaceApplicationReadinessPacketToggle",
        label: "Create application-readiness packet",
        description: "Requires a validated accepted operator decision.",
        readbackKey: "operator_approved_artifact_application_readiness_packet_readback",
      },
      {
        stage: "manual_application_handoff_packet",
        id: "scanWorkspaceManualApplicationHandoffPacketToggle",
        label: "Create human-only manual application handoff packet",
        description: "Prepare a packet for manual application handling only.",
        readbackKey: "human_only_manual_application_handoff_packet_readback",
      },
      {
        stage: "handoff_audit_trail",
        id: "scanWorkspaceHandoffAuditTrailToggle",
        label: "Create human-only handoff audit trail",
        description: "Record the manual handoff chain without submitting anything.",
        readbackKey: "human_only_handoff_audit_trail_readback",
      },
      {
        stage: "safety_boundary_summary",
        id: "scanWorkspaceSafetyBoundarySummaryToggle",
        label: "Create human-only safety boundary summary",
        description: "Summarize the preserved manual-only boundaries.",
        readbackKey: "human_only_safety_boundary_summary_readback",
      },
      {
        stage: "workflow_readiness_checkpoint",
        id: "scanWorkspaceWorkflowReadinessCheckpointToggle",
        label: "Create human-only workflow readiness checkpoint",
        description: "Produce the final non-mutating readiness checkpoint.",
        readbackKey: "human_only_workflow_readiness_checkpoint_readback",
      },
    ],
  },
];

const STAGE_BY_NAME = Object.fromEntries(
  STAGE_GROUPS.flatMap((group) => group.stages).map((stage) => [stage.stage, stage]),
) as Record<DiagnosticStage, StageConfig>;

const AMBIENT_READBACKS = [
  { id: "scanWorkspaceJdLlmReadback", key: "jd_llm_extraction_readback", label: "Live JD LLM" },
  { id: "scanWorkspaceAgenticWorkflowIntegrationReadback", key: "agentic_workflow_integration_readback", label: "Agentic workflow readiness" },
  { id: "scanWorkspaceProductionReadinessCheckpointReadback", key: "agentic_workflow_production_readiness_checkpoint", label: "Production readiness checkpoint" },
] as const;

type RequestFunction = (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>;

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function textValue(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

function textValues(value: unknown): string[] {
  return Array.isArray(value) ? value.map(textValue).filter(Boolean) : [];
}

function isValidReadback(value: unknown): boolean {
  const row = asRecord(value);
  return row.validation_status === "valid" && row.fallback_used === false;
}

function humanLabel(value: string): string {
  return value.replace(/_/g, " ").replace(/\b\w/g, (character) => character.toUpperCase());
}

function diagnosticTimestampParts(value: unknown): string[] {
  const raw = textValue(value);
  if (!raw) return ["Not recorded"];
  const parsed = new Date(raw);
  if (Number.isNaN(parsed.getTime())) return [raw];
  const iso = parsed.toISOString();
  return [iso.slice(0, 10), `${iso.slice(11, 19)} UTC`];
}

function readbackSummary(value: AdvancedDiagnosticsReadback): string {
  const safeErrorSummary = textValue(value.safe_error_summary);
  if (safeErrorSummary) return safeErrorSummary.slice(0, 240);
  const errors = Array.isArray(value.validation_errors)
    ? value.validation_errors.filter((item): item is string => typeof item === "string")
    : [];
  if (errors[0]) return errors[0].slice(0, 180);
  const fields = [
    "proposal_count",
    "accepted_proposal_count",
    "approved_change_plan_id",
    "artifact_id",
    "operator_review_packet_id",
    "operator_decision_id",
    "application_readiness_packet_id",
    "manual_handoff_packet_id",
    "handoff_audit_trail_id",
    "safety_boundary_summary_id",
    "workflow_readiness_checkpoint_id",
  ];
  for (const field of fields) {
    const valueText = textValue(value[field]);
    if (valueText) return `${humanLabel(field)}: ${valueText}`;
    if (typeof value[field] === "number") return `${humanLabel(field)}: ${String(value[field])}`;
  }
  return isValidReadback(value) ? "Validated readback recorded." : "A bounded diagnostic result was recorded.";
}

function readbackDiagnostics(value: AdvancedDiagnosticsReadback): { label: string; value: string }[] {
  const rows: { label: string; value: string }[] = [];
  const addText = (key: string, label: string, transform: (value: string) => string = (value) => value) => {
    const bounded = textValue(value[key]).slice(0, 240);
    if (bounded) rows.push({ label, value: transform(bounded) });
  };
  const addBoolean = (key: string, label: string) => {
    if (typeof value[key] === "boolean") rows.push({ label, value: value[key] ? "Yes" : "No" });
  };

  addText("provider", "Provider", humanLabel);
  addText("model", "Model");
  addText("failure_category", "Failure", humanLabel);
  addText("exception_class", "Exception");
  if (typeof value.http_status === "number" && Number.isInteger(value.http_status)) {
    rows.push({ label: "HTTP", value: String(value.http_status) });
  }
  addText("provider_error_type", "Error type", humanLabel);
  addText("provider_error_code", "Error code", humanLabel);
  addText("provider_error_param", "Parameter");
  addText("invalid_request_reason", "Invalid request", humanLabel);
  addText("schema_keyword", "Schema keyword");
  addBoolean("provider_call_attempted", "Provider call attempted");
  addBoolean("retry_performed", "Retry performed");
  addBoolean("provider_fallback_performed", "Provider fallback performed");
  return rows;
}

function readbackDisplay(value: AdvancedDiagnosticsReadback): {
  status: string;
  tone: "success" | "error" | "waiting" | "muted";
} {
  if (isValidReadback(value)) return { status: "Completed", tone: "success" };
  if (!Object.keys(value).length) return { status: "Waiting", tone: "waiting" };
  const errors = textValues(value.validation_errors);
  if (textValue(value.validation_status) === "disabled" || textValue(value.fallback_reason) === "feature_flag_disabled" || errors.includes("feature_flag_disabled")) {
    return { status: "Disabled", tone: "muted" };
  }
  if (textValue(value.fallback_reason) === "provider_response_invalid") {
    return { status: "Failed", tone: "error" };
  }
  if (value.fallback_used === true || textValue(value.fallback_error_class)) {
    return { status: "Failed", tone: "error" };
  }
  if (textValue(value.validation_status) && value.validation_status !== "valid") {
    return { status: "Failed", tone: "error" };
  }
  return { status: "Needs attention", tone: "error" };
}

function authoritativeStageReadback(
  state: AdvancedDiagnosticsDiagnosticState,
  stage: DiagnosticStage,
): AdvancedDiagnosticsReadback {
  const key = STAGE_BY_NAME[stage].readbackKey;
  const latest = asRecord(asRecord(state.readbacks)[key]);
  if (Object.keys(latest).length) return latest;
  return asRecord(asRecord(state.validated_readbacks)[key]);
}

function tailoringRows(state: AdvancedDiagnosticsDiagnosticState): AdvancedDiagnosticsReadback[] {
  const tailoring = authoritativeStageReadback(state, "live_tailoring_suggestion");
  if (!isValidReadback(tailoring)) return [];
  return Array.isArray(tailoring.suggestions_preview) ? tailoring.suggestions_preview.map(asRecord) : [];
}

function proposalRows(state: AdvancedDiagnosticsDiagnosticState): AdvancedDiagnosticsReadback[] {
  const exact = authoritativeStageReadback(state, "live_exact_resume_change_proposal");
  if (!isValidReadback(exact)) return [];
  const values = exact.proposed_changes_preview;
  return Array.isArray(values)
    ? values.map(asRecord).filter((row) => textValue(row.proposal_id))
    : [];
}

function stageIsValid(state: AdvancedDiagnosticsDiagnosticState, stage: DiagnosticStage): boolean {
  return isValidReadback(authoritativeStageReadback(state, stage));
}

function acceptedDecision(state: AdvancedDiagnosticsDiagnosticState): boolean {
  const value = authoritativeStageReadback(state, "verified_artifact_operator_decision");
  return textValue(value.operator_decision_value) === "accepted";
}

const STAGE_READBACK_IDS: Record<DiagnosticStage, string> = {
  live_tailoring_suggestion: "scanWorkspaceTailoringLlmReadback",
  live_exact_resume_change_proposal: "scanWorkspaceExactChangeLlmReadback",
  manual_exact_change_acceptance: "scanWorkspaceManualExactChangeAcceptanceReadback",
  guarded_resume_copy_artifact: "scanWorkspaceGuardedResumeCopyArtifactReadback",
  guarded_resume_copy_artifact_verification: "scanWorkspaceGuardedResumeCopyArtifactVerificationReadback",
  verified_artifact_operator_review_packet: "scanWorkspaceVerifiedArtifactOperatorReviewPacketReadback",
  verified_artifact_operator_decision: "scanWorkspaceVerifiedArtifactOperatorDecisionReadback",
  application_readiness_packet: "scanWorkspaceApplicationReadinessPacketReadback",
  manual_application_handoff_packet: "scanWorkspaceManualApplicationHandoffPacketReadback",
  handoff_audit_trail: "scanWorkspaceHandoffAuditTrailReadback",
  safety_boundary_summary: "scanWorkspaceSafetyBoundarySummaryReadback",
  workflow_readiness_checkpoint: "scanWorkspaceWorkflowReadinessCheckpointReadback",
};

function dependencyFor(
  stage: DiagnosticStage,
  state: AdvancedDiagnosticsDiagnosticState,
  selected: DiagnosticStage[],
  proposalIds: string[],
  decision: string,
  overrides: Record<string, string>,
): string {
  const has = (name: DiagnosticStage) => stageIsValid(state, name) || selected.includes(name);
  if (stage === "manual_exact_change_acceptance" && !stageIsValid(state, "live_exact_resume_change_proposal")) {
    return "Generate and validate exact proposals first.";
  }
  if (stage === "manual_exact_change_acceptance" && proposalIds.length === 0) return "Select at least one proposal below.";
  if (stage === "guarded_resume_copy_artifact" && !has("manual_exact_change_acceptance") && !overrides.approved_change_plan_id) {
    return "Complete exact-change acceptance first.";
  }
  if (stage === "guarded_resume_copy_artifact_verification" && !has("guarded_resume_copy_artifact") && !overrides.guarded_resume_copy_artifact_id) {
    return "Create a guarded artifact first.";
  }
  if (stage === "verified_artifact_operator_review_packet" && !has("guarded_resume_copy_artifact_verification") && !overrides.verified_artifact_operator_review_artifact_id) {
    return "Verify the guarded artifact first.";
  }
  if (stage === "verified_artifact_operator_decision") {
    if (!stageIsValid(state, "verified_artifact_operator_review_packet") && !overrides.verified_artifact_operator_decision_packet_id) {
      return "Create and validate the review packet first.";
    }
    if (!decision) return "Choose an explicit operator decision below.";
  }
  if (stage === "application_readiness_packet" && !acceptedDecision(state)) {
    return "A validated accepted operator decision is required.";
  }
  const index = DIAGNOSTIC_STAGE_ORDER.indexOf(stage);
  if (index >= 8) {
    const previous = DIAGNOSTIC_STAGE_ORDER[index - 1];
    if (!has(previous)) return `Complete ${humanLabel(previous)} first.`;
  }
  return "";
}

function AdvancedDiagnosticsHeader() {
  return (
    <header className="advanced-diagnostics-header app-page-header">
      <div className="advanced-diagnostics-header-primary app-page-header__main app-page-header__main--with-icon">
        <span className="advanced-diagnostics-header-icon-tile" aria-hidden="true"><ShieldCheck size={22} /></span>
        <div className="app-page-header__copy">
          <div className="advanced-diagnostics-header-title-row app-page-header__title-row">
            <h1 className="app-page-header__title">Scan Diagnostics</h1>
            <span className="advanced-diagnostics-badge advanced-diagnostics-badge--muted app-page-header__badge">Admin only</span>
            <span className="advanced-diagnostics-badge advanced-diagnostics-badge--ready app-page-header__badge">Manual execution</span>
          </div>
          <p className="app-page-header__description">Run bounded diagnostics for one saved scan and inspect persisted readbacks.</p>
        </div>
      </div>
    </header>
  );
}

function HubModeCard({ options, hrefs, navigate }: {
  options: AdvancedDiagnosticsSavedScanOption[];
  hrefs: AdvancedDiagnosticsState["hrefs"];
  navigate: (href: string) => void;
}) {
  const [selected, setSelected] = useState<string[]>([]);
  const filterOptions: SharedFilterOption[] = useMemo(() => options.map((option) => ({
    value: option.scanId,
    label: option.secondary ? `${option.primary} — ${option.secondary}` : option.primary,
  })), [options]);
  return (
    <section className="advanced-diagnostics-card advanced-diagnostics-hub-card">
      <h2>Choose a saved scan</h2>
      <p className="advanced-diagnostics-card-description">Select a saved scan to open its persisted diagnostic workspace.</p>
      <div className="advanced-diagnostics-hub-controls">
        <SharedFilterSelect id="advancedDiagnosticsScanSelect" label="Saved scan" options={filterOptions} values={selected}
          onChange={setSelected} placeholder="Choose a saved scan..." mode="single" searchable portalClassName="advanced-diagnostics-scan-menu" />
        <button type="button" className="ghost-btn btn-sm advanced-diagnostics-open-btn" disabled={!selected[0]}
          onClick={() => selected[0] && navigate(`${hrefs.advancedDiagnostics}?saved_scan_id=${encodeURIComponent(selected[0])}`)}>
          Open diagnostics
        </button>
      </div>
    </section>
  );
}

function EmptyModeCard({ hrefs }: { hrefs: AdvancedDiagnosticsState["hrefs"] }) {
  return (
    <section className="advanced-diagnostics-card advanced-diagnostics-empty-card">
      <span className="advanced-diagnostics-empty-icon-cluster" aria-hidden="true"><FileSearch size={26} /></span>
      <h2>No saved scans available</h2>
      <p className="advanced-diagnostics-card-description">Save or load an AI Optimize Scan before opening scan-specific diagnostics.</p>
      <a className="ghost-btn btn-sm" href={hrefs.scanWorkspace}>Open New Scan</a>
    </section>
  );
}

function InvalidModeCard({ hrefs }: { hrefs: AdvancedDiagnosticsState["hrefs"] }) {
  return (
    <section className="advanced-diagnostics-card advanced-diagnostics-invalid-card">
      <span className="advanced-diagnostics-invalid-icon-tile" aria-hidden="true"><FileQuestion size={26} /></span>
      <h2>Scan context unavailable</h2>
      <p className="advanced-diagnostics-card-description">This scan could not be found or is not available to this account.</p>
      <a className="ghost-btn btn-sm" href={hrefs.advancedDiagnostics}>Choose another saved scan</a>
    </section>
  );
}

const WORKFLOW_STEPS = [
  { label: "Analyze", stages: ["live_tailoring_suggestion", "live_exact_resume_change_proposal"] },
  { label: "Review changes", stages: ["manual_exact_change_acceptance"] },
  { label: "Verify copy", stages: ["guarded_resume_copy_artifact_verification"] },
  { label: "Ready", stages: ["workflow_readiness_checkpoint"] },
] as const;

type WizardStepIndex = 0 | 1 | 2 | 3;

function wizardStepComplete(state: AdvancedDiagnosticsDiagnosticState, index: WizardStepIndex): boolean {
  if (index === 0) return stageIsValid(state, "live_exact_resume_change_proposal");
  return WORKFLOW_STEPS[index].stages.every((stage) => stageIsValid(state, stage));
}

function tailoringNeedsAttention(state: AdvancedDiagnosticsDiagnosticState): boolean {
  const readback = authoritativeStageReadback(state, "live_tailoring_suggestion");
  if (stageIsValid(state, "live_tailoring_suggestion") || !Object.keys(readback).length) return false;
  const display = readbackDisplay(readback);
  return display.status !== "Waiting" && display.status !== "Disabled";
}

function wizardStepAttention(state: AdvancedDiagnosticsDiagnosticState, index: WizardStepIndex): boolean {
  return index === 0 && wizardStepComplete(state, 0) && tailoringNeedsAttention(state);
}

function wizardStepUnlocked(state: AdvancedDiagnosticsDiagnosticState, index: WizardStepIndex): boolean {
  if (index === 0) return true;
  if (index === 1) return stageIsValid(state, "live_exact_resume_change_proposal");
  if (index === 2) return stageIsValid(state, "manual_exact_change_acceptance");
  return stageIsValid(state, "guarded_resume_copy_artifact_verification");
}

function deriveInitialWizardStep(state: AdvancedDiagnosticsDiagnosticState): WizardStepIndex {
  if (!wizardStepComplete(state, 0)) return 0;
  if (!wizardStepComplete(state, 1)) return 1;
  if (!wizardStepComplete(state, 2)) return 2;
  return 3;
}

function WizardHeader({ context, hrefs, state, activeStep, onStepChange, onTechnicalDetails }: {
  context: AdvancedDiagnosticsContext;
  hrefs: AdvancedDiagnosticsState["hrefs"];
  state: AdvancedDiagnosticsDiagnosticState;
  activeStep: WizardStepIndex;
  onStepChange: (step: WizardStepIndex) => void;
  onTechnicalDetails: () => void;
}) {
  const completedStages = WORKFLOW_STEPS.filter((_, index) => wizardStepComplete(state, index as WizardStepIndex)).length;
  const progressionStep = deriveInitialWizardStep(state);
  const isRevisiting = activeStep < progressionStep;
  const workflowComplete = wizardStepComplete(state, 3);
  return (
    <section className="advanced-diagnostics-wizard-header" aria-label="Scan diagnostic workflow">
      <div className="advanced-diagnostics-wizard-context">
        <div>
          <h2>{context.company} <span aria-hidden="true">·</span> {context.title}</h2>
          <p><strong>Resume</strong> {context.resume}</p>
        </div>
        <div className="advanced-diagnostics-wizard-actions">
          <button className="ghost-btn btn-sm" type="button" onClick={onTechnicalDetails}><Eye size={15} aria-hidden="true" />Technical details</button>
          <a className="ghost-btn btn-sm advanced-diagnostics-change-scan-btn" href={hrefs.advancedDiagnostics}>Change scan</a>
          <a className="advanced-diagnostics-back-btn" href={context.backToScanHref}>Back to scan</a>
        </div>
      </div>
      <div className="advanced-diagnostics-wizard-progress">
        <strong>{isRevisiting ? `Viewing: ${WORKFLOW_STEPS[activeStep].label}` : workflowComplete ? "Workflow complete" : `Stage ${activeStep + 1} of 4`}</strong>
        <span>{completedStages} of 4 workflow stages complete</span>
      </div>
      <nav aria-label="Workflow stages">
        <ol className="advanced-diagnostics-stepper">
        {WORKFLOW_STEPS.map((step, index) => {
          const stepIndex = index as WizardStepIndex;
          const isComplete = wizardStepComplete(state, stepIndex);
          const isActive = activeStep === stepIndex;
          const unlocked = wizardStepUnlocked(state, stepIndex);
          const attention = wizardStepAttention(state, stepIndex);
          const isViewing = isActive && isComplete;
          const stateLabel = attention ? "Needs attention" : !unlocked ? "Locked" : isComplete ? "Completed" : isActive ? "Current stage" : "Available";
          return (
            <li key={step.label} data-state={attention ? "attention" : !unlocked ? "locked" : isComplete ? "completed" : isActive ? "active" : "available"} data-viewing={isViewing ? "true" : undefined} className={`${isComplete ? "is-complete" : ""} ${isActive ? "is-current" : ""} ${isViewing ? "is-viewing" : ""} ${!unlocked ? "is-locked" : ""} ${attention ? "is-attention" : ""}`}>
              <button type="button" disabled={!unlocked} aria-current={isActive ? "step" : undefined} aria-label={`${step.label}${!unlocked ? " — locked" : ""}`} onClick={() => onStepChange(stepIndex)}>
                <span className="advanced-diagnostics-step-indicator" aria-hidden="true">{isComplete ? <Check size={15} /> : !unlocked ? <LockKeyhole size={13} /> : index + 1}</span>
                <span className="advanced-diagnostics-step-copy"><strong>{step.label}</strong><small>{attention ? <AlertTriangle size={11} aria-hidden="true" /> : null}{stateLabel}</small>{isViewing ? <em className="advanced-diagnostics-step-viewing">Viewing</em> : null}</span>
              </button>
            </li>
          );
        })}
        </ol>
      </nav>
    </section>
  );
}

function StageStatus({ state, stage }: { state: AdvancedDiagnosticsDiagnosticState; stage: DiagnosticStage }) {
  const readback = authoritativeStageReadback(state, stage);
  if (stage === "live_tailoring_suggestion" && tailoringNeedsAttention(state)) {
    return <span className="advanced-diagnostics-badge advanced-diagnostics-badge--attention">Needs attention</span>;
  }
  const display = stageIsValid(state, stage) ? { status: "Completed", tone: "success" as const } : readbackDisplay(readback);
  return <span className={`advanced-diagnostics-badge advanced-diagnostics-badge--${display.tone}`}>{display.status}</span>;
}

function TailoringRecommendations({ state }: { state: AdvancedDiagnosticsDiagnosticState }) {
  const rows = tailoringRows(state);
  const readback = asRecord(asRecord(state.readbacks).live_tailoring_suggestion_readback);
  const authoritative = authoritativeStageReadback(state, "live_tailoring_suggestion");
  const unsupportedRisks = Array.isArray(authoritative.unsupported_claim_risks) ? authoritative.unsupported_claim_risks.map(asRecord) : [];
  const valid = stageIsValid(state, "live_tailoring_suggestion");
  if (!valid) {
    const display = readbackDisplay(readback);
    return <p className={`advanced-diagnostics-analysis-empty ${display.status === "Failed" || display.status === "Needs attention" ? "is-attention" : `is-${display.tone}`}`}>{display.status === "Failed" || display.status === "Needs attention" ? "The AI provider could not return a valid structured result for the latest analysis." : "Run tailoring analysis to see recommendations."}</p>;
  }
  if (!rows.length) return <p className="advanced-diagnostics-analysis-empty">No supported tailoring recommendations were produced for this scan.</p>;
  return (<>
    <div className="advanced-diagnostics-recommendation-list">
      {rows.map((row, index) => {
        const type = textValue(row.suggestion_type) || (row.patch_ready ? "patch_ready" : "guidance_only");
        const links = Array.isArray(row.jd_signal_links) ? row.jd_signal_links.map(asRecord) : [];
        const evidence = textValues(row.evidence_spans);
        const risks = textValues(row.risk_flags);
        return (
          <article key={textValue(row.suggestion_id) || index} className="advanced-diagnostics-recommendation" data-kind={type}>
            <div className="advanced-diagnostics-recommendation-heading">
              <span>{type === "patch_ready" ? "Patch-ready" : type === "rejected" ? "Rejected / unsupported" : "Guidance"}</span>
              {textValue(row.target_section) ? <small>{humanLabel(textValue(row.target_section))}</small> : null}
            </div>
            {textValue(row.suggested_text) ? <h4>{textValue(row.suggested_text)}</h4> : <h4>{textValue(row.source_bullet_id) || "Tailoring recommendation"}</h4>}
            {textValue(row.reason) ? <div className="advanced-diagnostics-recommendation-detail"><b>Reason</b><p>{textValue(row.reason)}</p></div> : null}
            {links.length ? <div className="advanced-diagnostics-recommendation-detail"><b>JD signal</b><div className="advanced-diagnostics-chip-row">{links.map((link, linkIndex) => <span key={linkIndex}>{[textValue(link.field), textValue(link.signal)].filter(Boolean).join(" · ")}</span>)}</div></div> : null}
            {evidence.length ? <div className="advanced-diagnostics-recommendation-detail"><b>Resume evidence</b><p>{evidence.slice(0, 4).join(" · ")}</p></div> : null}
            {risks.length ? <div className="advanced-diagnostics-recommendation-detail is-warning"><b>Risk</b><p>{risks.join(" · ")}</p></div> : null}
          </article>
        );
      })}
    </div>
    {unsupportedRisks.length ? <aside className="advanced-diagnostics-unsupported-risks"><strong>Unsupported claim risks</strong>{unsupportedRisks.map((risk, index) => <p key={index}>{[textValue(risk.field), textValue(risk.signal), textValue(risk.risk)].filter(Boolean).join(" · ")}</p>)}</aside> : null}
  </>);
}

function TechnicalDrawer({ open, onClose, children }: {
  open: boolean;
  onClose: () => void;
  children: React.ReactNode;
}) {
  const drawerRef = useRef<HTMLElement>(null);
  const closeRef = useRef<HTMLButtonElement>(null);
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;
  useEffect(() => {
    if (!open) return;
    const previouslyFocused = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const previousBodyOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    closeRef.current?.focus();
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        onCloseRef.current();
        return;
      }
      if (event.key !== "Tab" || !drawerRef.current) return;
      const focusable = Array.from(drawerRef.current.querySelectorAll<HTMLElement>(
        'button:not(:disabled), a[href], input:not(:disabled), select:not(:disabled), textarea:not(:disabled), [tabindex]:not([tabindex="-1"])',
      ));
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
    };
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = previousBodyOverflow;
      previouslyFocused?.focus();
    };
  }, [open]);
  if (!open) return null;
  return createPortal(
    <div className="advanced-diagnostics-drawer-backdrop" data-overlay-layer="diagnostics" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
      <aside ref={drawerRef} className="advanced-diagnostics-technical-drawer" id="advancedDiagnosticsSectionReadbacks" role="dialog" aria-modal="true" aria-labelledby="advancedDiagnosticsTechnicalTitle" aria-describedby="advancedDiagnosticsTechnicalDescription">
        <header className="advanced-diagnostics-technical-drawer-header">
          <div><p>Advanced diagnostics</p><h2 id="advancedDiagnosticsTechnicalTitle">Technical details</h2><span id="advancedDiagnosticsTechnicalDescription">Persisted readbacks, internal IDs, provider metadata, and diagnostic reasons.</span></div>
          <button ref={closeRef} className="advanced-diagnostics-close-control" type="button" aria-label="Close technical details" onClick={onClose}><X size={20} strokeWidth={2} aria-hidden="true" /></button>
        </header>
        <div className="advanced-diagnostics-technical-body">{children}</div>
      </aside>
    </div>,
    document.body,
  );
}

function PremiumDialog({ open, eyebrow = "Human approval required", title, description, children, footer, onClose }: {
  open: boolean;
  eyebrow?: string;
  title: string;
  description: string;
  children: React.ReactNode;
  footer: React.ReactNode;
  onClose: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      if (typeof dialog.showModal === "function") dialog.showModal();
      else dialog.setAttribute("open", "");
    } else if (!open && dialog.open) {
      if (typeof dialog.close === "function") dialog.close();
      else dialog.removeAttribute("open");
    }
  }, [open]);
  if (!open) return null;
  return (
    <dialog ref={ref} className="advanced-diagnostics-dialog" id="advancedDiagnosticsReviewDialog" aria-labelledby="advancedDiagnosticsDialogTitle" aria-describedby="advancedDiagnosticsDialogDescription" onCancel={(event) => { event.preventDefault(); onClose(); }}>
      <div className="advanced-diagnostics-dialog-shell">
        <header><div><p>{eyebrow}</p><h2 id="advancedDiagnosticsDialogTitle">{title}</h2><span id="advancedDiagnosticsDialogDescription">{description}</span></div><button className="advanced-diagnostics-close-control advanced-diagnostics-dialog-close" type="button" aria-label="Close" onClick={onClose}><X size={20} strokeWidth={2} aria-hidden="true" /></button></header>
        <div className="advanced-diagnostics-dialog-body">{children}</div>
        <footer>{footer}</footer>
      </div>
    </dialog>
  );
}

function SelectedProposalReview({ rows }: { rows: AdvancedDiagnosticsReadback[] }) {
  return <div className="advanced-diagnostics-dialog-proposals">{rows.map((row) => (
    <article key={textValue(row.proposal_id)}>
      <div className="advanced-diagnostics-dialog-comparison"><div><b>Current</b><p>{textValue(row.current_text)}</p></div><ArrowDown size={18} aria-hidden="true" /><div className="is-proposed"><b>Proposed</b><p>{textValue(row.proposed_text)}</p></div></div>
      {textValue(row.change_reason) ? <div className="advanced-diagnostics-dialog-explanation"><b>Why AI recommends this</b><p>{textValue(row.change_reason)}</p></div> : null}
      {textValues(row.jd_terms_supported).length ? <div className="advanced-diagnostics-dialog-explanation"><b>JD signals</b><div className="advanced-diagnostics-chip-row">{textValues(row.jd_terms_supported).map((item) => <span key={item}>{item}</span>)}</div></div> : null}
      {textValues(row.resume_evidence_used).length ? <div className="advanced-diagnostics-dialog-explanation"><b>Resume evidence</b><p>{textValues(row.resume_evidence_used).join(" · ")}</p></div> : null}
    </article>
  ))}</div>;
}

function ProposalSelector({ rows, selected, onChange }: {
  rows: AdvancedDiagnosticsReadback[];
  selected: string[];
  onChange: (ids: string[]) => void;
}) {
  if (!rows.length) return null;
  return (
    <fieldset className="advanced-diagnostics-proposals">
      <legend>Exact proposals</legend>
      <p>Select the exact proposal IDs to accept. Nothing is selected by default.</p>
      <div className="advanced-diagnostics-proposal-list">
        {rows.map((row) => {
          const proposalId = textValue(row.proposal_id);
          const checked = selected.includes(proposalId);
          const currentText = textValue(row.current_text);
          const proposedText = textValue(row.proposed_text);
          const changeReason = textValue(row.change_reason);
          const jdTerms = textValues(row.jd_terms_supported);
          const evidence = textValues(row.resume_evidence_used);
          const target = [textValue(row.target_section), textValue(row.target_identifier)].filter(Boolean).join(" · ");
          return (
            <label key={proposalId} className={`advanced-diagnostics-proposal ${checked ? "is-selected" : ""}`}>
              <input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked
                ? [...selected, proposalId]
                : selected.filter((value) => value !== proposalId))} />
              <span className="advanced-diagnostics-proposal-content">
                <span className="advanced-diagnostics-proposal-heading">
                  <strong>{humanLabel(textValue(row.change_type) || "exact_change")}</strong>
                  {target ? <small title={target}>{target}</small> : null}
                </span>
                {currentText ? (
                  <span className="advanced-diagnostics-proposal-review is-current">
                    <b>Current</b><span>{currentText}</span>
                  </span>
                ) : null}
                {proposedText ? (
                  <span className="advanced-diagnostics-proposal-review is-proposed">
                    <b>Proposed</b><span>{proposedText}</span>
                  </span>
                ) : null}
                {changeReason ? (
                  <span className="advanced-diagnostics-proposal-reason">
                    <b>Reason</b><span>{changeReason}</span>
                  </span>
                ) : null}
                {jdTerms.length || evidence.length ? (
                  <span className="advanced-diagnostics-proposal-context">
                    {jdTerms.length ? <span><b>JD terms</b>{jdTerms.slice(0, 4).map((term, index) => <em key={`${term}-${index}`}>{term}</em>)}</span> : null}
                    {evidence.length ? <span><b>Evidence</b>{evidence.slice(0, 2).map((item, index) => <em key={`${item}-${index}`} title={item}>{item}</em>)}</span> : null}
                  </span>
                ) : null}
                <small className="advanced-diagnostics-proposal-id">Proposal ID · {proposalId}</small>
              </span>
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}

const OVERRIDE_FIELDS = [
  ["approved_change_plan_id", "scanWorkspaceApprovedChangePlanId", "Approved change plan ID"],
  ["guarded_resume_copy_artifact_id", "scanWorkspaceGuardedResumeCopyArtifactId", "Guarded artifact ID"],
  ["verified_artifact_operator_review_artifact_id", "scanWorkspaceVerifiedArtifactOperatorReviewArtifactId", "Verified artifact ID"],
  ["verified_artifact_operator_decision_packet_id", "scanWorkspaceVerifiedArtifactOperatorDecisionPacketId", "Operator review packet ID"],
  ["verified_artifact_operator_decision_artifact_id", "scanWorkspaceVerifiedArtifactOperatorDecisionArtifactId", "Decision artifact ID"],
  ["application_readiness_operator_decision_id", "scanWorkspaceApplicationReadinessDecisionId", "Operator decision ID"],
  ["application_readiness_operator_review_packet_id", "scanWorkspaceApplicationReadinessReviewPacketId", "Readiness review packet ID"],
  ["application_readiness_artifact_id", "scanWorkspaceApplicationReadinessArtifactId", "Readiness artifact ID"],
  ["manual_handoff_application_readiness_packet_id", "scanWorkspaceManualHandoffReadinessPacketId", "Application readiness packet ID"],
  ["manual_handoff_artifact_id", "scanWorkspaceManualHandoffArtifactId", "Manual handoff artifact ID"],
  ["handoff_audit_manual_handoff_packet_id", "scanWorkspaceHandoffAuditHandoffPacketId", "Manual handoff packet ID"],
  ["handoff_audit_application_readiness_packet_id", "scanWorkspaceHandoffAuditReadinessPacketId", "Audit readiness packet ID"],
  ["handoff_audit_artifact_id", "scanWorkspaceHandoffAuditArtifactId", "Audit artifact ID"],
  ["safety_boundary_handoff_audit_trail_id", "scanWorkspaceSafetyBoundaryAuditTrailId", "Handoff audit trail ID"],
  ["safety_boundary_manual_handoff_packet_id", "scanWorkspaceSafetyBoundaryHandoffPacketId", "Safety handoff packet ID"],
  ["safety_boundary_application_readiness_packet_id", "scanWorkspaceSafetyBoundaryReadinessPacketId", "Safety readiness packet ID"],
  ["safety_boundary_artifact_id", "scanWorkspaceSafetyBoundaryArtifactId", "Safety artifact ID"],
  ["workflow_readiness_safety_boundary_summary_id", "scanWorkspaceWorkflowReadinessSummaryId", "Safety boundary summary ID"],
  ["workflow_readiness_handoff_audit_trail_id", "scanWorkspaceWorkflowReadinessAuditTrailId", "Workflow audit trail ID"],
  ["workflow_readiness_manual_handoff_packet_id", "scanWorkspaceWorkflowReadinessHandoffPacketId", "Workflow handoff packet ID"],
  ["workflow_readiness_application_readiness_packet_id", "scanWorkspaceWorkflowReadinessReadinessPacketId", "Workflow readiness packet ID"],
  ["workflow_readiness_artifact_id", "scanWorkspaceWorkflowReadinessArtifactId", "Workflow artifact ID"],
] as const;

function ManualOverrides({ values, onChange }: { values: Record<string, string>; onChange: (key: string, value: string) => void }) {
  return (
    <details className="advanced-diagnostics-overrides">
      <summary><ChevronDown size={16} aria-hidden="true" />Advanced: manual ID override</summary>
      <p>Use only to inspect an existing identifier when the persisted upstream readback is unavailable.</p>
      <div className="advanced-diagnostics-overrides-grid">
        {OVERRIDE_FIELDS.map(([key, id, label]) => (
          <label key={key} htmlFor={id}><span>{label}</span><input id={id} type="text" value={values[key] || ""}
            onChange={(event) => onChange(key, event.target.value)} autoComplete="off" /></label>
        ))}
      </div>
    </details>
  );
}

function ReadbackRow({ id, label, value }: { id: string; label: string; value: AdvancedDiagnosticsReadback }) {
  const exists = Object.keys(value).length > 0;
  const { status, tone } = readbackDisplay(value);
  const diagnostics = readbackDiagnostics(value);
  return (
    <div className="advanced-diagnostics-readback-row" id={id} aria-live="polite">
      <div className="advanced-diagnostics-readback-copy">
        <strong>{label}</strong>
        <small>{exists ? readbackSummary(value) : "No persisted readback yet."}</small>
        {diagnostics.length ? <dl className="advanced-diagnostics-readback-metadata">
          {diagnostics.map((row) => <div key={row.label}><dt>{row.label}</dt><dd>{row.value}</dd></div>)}
        </dl> : null}
      </div>
      <span className={`advanced-diagnostics-badge advanced-diagnostics-badge--${tone}`}>{status}</span>
    </div>
  );
}

const READINESS_STAGES: { stage: DiagnosticStage; label: string; action: string }[] = [
  { stage: "verified_artifact_operator_review_packet", label: "Human review packet", action: "Create review packet" },
  { stage: "verified_artifact_operator_decision", label: "Operator decision", action: "Record decision" },
  { stage: "application_readiness_packet", label: "Application readiness", action: "Prepare readiness packet" },
  { stage: "manual_application_handoff_packet", label: "Manual handoff", action: "Prepare handoff" },
  { stage: "handoff_audit_trail", label: "Audit trail", action: "Create audit" },
  { stage: "safety_boundary_summary", label: "Safety boundary", action: "Verify safety" },
  { stage: "workflow_readiness_checkpoint", label: "Workflow readiness", action: "Confirm workflow readiness" },
];

function WorkflowChecklist({ state, rows, currentStage }: {
  state: AdvancedDiagnosticsDiagnosticState;
  rows: { stage: DiagnosticStage; label: string }[];
  currentStage?: DiagnosticStage;
}) {
  return <ol className="advanced-diagnostics-checklist">{rows.map(({ stage, label }) => {
    const complete = stageIsValid(state, stage);
    const isCurrent = currentStage === stage;
    const decision = stage === "verified_artifact_operator_decision" && complete
      ? textValue(authoritativeStageReadback(state, stage).operator_decision_value)
      : "";
    return <li key={stage} className={`${complete ? "is-complete" : ""} ${isCurrent ? "is-current" : ""}`}><span aria-hidden="true">{complete ? <CheckCircle2 size={17} /> : <Circle size={17} />}</span><strong>{label}{decision ? `: ${humanLabel(decision)}` : ""}</strong><StageStatus state={state} stage={stage} /></li>;
  })}</ol>;
}

export function AdvancedDiagnosticsDashboard({
  state = DEFAULT_ADVANCED_DIAGNOSTICS_STATE,
  navigate = (href: string) => { window.location.href = href; },
  request = window.fetch.bind(window),
}: {
  state?: AdvancedDiagnosticsState;
  navigate?: (href: string) => void;
  request?: RequestFunction;
}) {
  const [diagnosticState, setDiagnosticState] = useState<AdvancedDiagnosticsDiagnosticState>(() => state.diagnosticState || {});
  const [selectedProposalIds, setSelectedProposalIds] = useState<string[]>([]);
  const [overrides, setOverrides] = useState<Record<string, string>>({});
  const [runningStage, setRunningStage] = useState<DiagnosticStage | null>(null);
  const [resetting, setResetting] = useState(false);
  const [reviewOpen, setReviewOpen] = useState(false);
  const [decisionOpen, setDecisionOpen] = useState(false);
  const [resetOpen, setResetOpen] = useState(false);
  const [technicalOpen, setTechnicalOpen] = useState(false);
  const [activeStep, setActiveStep] = useState<WizardStepIndex>(() => deriveInitialWizardStep(state.diagnosticState || {}));
  const [message, setMessage] = useState<{ tone: "success" | "error"; text: string } | null>(null);

  const proposals = proposalRows(diagnosticState);
  const tailoring = authoritativeStageReadback(diagnosticState, "live_tailoring_suggestion");
  const selectedProposals = proposals.filter((row) => selectedProposalIds.includes(textValue(row.proposal_id)));

  const runStage = async (stage: DiagnosticStage, operatorDecision = ""): Promise<boolean> => {
    const dependency = dependencyFor(stage, diagnosticState, [], selectedProposalIds, operatorDecision, overrides);
    if (!state.selectedScanId || runningStage || dependency) return false;
    const revisitingCompletedStage = activeStep < deriveInitialWizardStep(diagnosticState);
    const body: Record<string, unknown> = {
      diagnostics_execution: true,
      diagnostic_stages: [stage],
      ...Object.fromEntries(Object.entries(overrides).filter(([, value]) => value.trim())),
    };
    if (stage === "manual_exact_change_acceptance") body.accepted_exact_change_proposal_ids = selectedProposalIds;
    if (stage === "verified_artifact_operator_decision") body.verified_artifact_operator_decision_value = operatorDecision;
    setRunningStage(stage);
    setMessage(null);
    try {
      const response = await request(`/planning/saved-scan/${encodeURIComponent(state.selectedScanId)}/state`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const payload = asRecord(await response.json());
      if (!response.ok) throw new Error(textValue(payload.detail) || "This workflow check could not be completed.");
      const nextState = asRecord(payload.diagnostic_state) as AdvancedDiagnosticsDiagnosticState;
      setDiagnosticState(nextState);
      const results = Array.isArray(payload.stage_results) ? payload.stage_results.map(asRecord) : [];
      const valid = results.length > 0 && results.every((row) => row.valid === true);
      if (valid) {
        if (stage === "manual_exact_change_acceptance" || stage === "live_exact_resume_change_proposal") setSelectedProposalIds([]);
        if (stage === "live_tailoring_suggestion" && wizardStepComplete(nextState, 0) && !revisitingCompletedStage) setActiveStep(1);
        if (stage === "live_exact_resume_change_proposal" && wizardStepComplete(nextState, 0)) setActiveStep(1);
        if (stage === "manual_exact_change_acceptance") setActiveStep(2);
        if (stage === "guarded_resume_copy_artifact_verification") setActiveStep(3);
        setMessage({ tone: "success", text: `${STAGE_BY_NAME[stage].label} completed.` });
        return true;
      }
      setMessage({ tone: "error", text: `${STAGE_BY_NAME[stage].label} needs attention. Open Technical details for the persisted reason.` });
      return false;
    } catch (error) {
      setMessage({ tone: "error", text: stage === "live_tailoring_suggestion"
        ? "Tailoring analysis needs attention. Open Technical details for the persisted reason."
        : error instanceof Error ? error.message.slice(0, 220) : "This workflow check could not be completed." });
      return false;
    } finally {
      setRunningStage(null);
    }
  };

  const resetDiagnostics = async (): Promise<void> => {
    if (!state.selectedScanId || resetting || runningStage) return;
    setResetting(true);
    setMessage(null);
    try {
      const response = await request(`/planning/saved-scan/${encodeURIComponent(state.selectedScanId)}/state`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ diagnostics_reset: true }),
      });
      const payload = asRecord(await response.json());
      if (!response.ok) throw new Error(textValue(payload.detail) || "The diagnostics workflow could not be reset.");
      const nextState = asRecord(payload.diagnostic_state) as AdvancedDiagnosticsDiagnosticState;
      setDiagnosticState(nextState);
      setSelectedProposalIds([]);
      setOverrides({});
      setReviewOpen(false);
      setDecisionOpen(false);
      setResetOpen(false);
      setActiveStep(deriveInitialWizardStep(nextState));
      setMessage({ tone: "success", text: "Diagnostics workflow reset. Choose an analysis to run." });
    } catch (error) {
      setMessage({ tone: "error", text: error instanceof Error ? error.message.slice(0, 220) : "The diagnostics workflow could not be reset." });
    } finally {
      setResetting(false);
    }
  };

  const readbacks = asRecord(diagnosticState.readbacks);
  const ambient = asRecord(diagnosticState.ambient_readbacks);
  const actionReason = (stage: DiagnosticStage, decision = "") => dependencyFor(stage, diagnosticState, [], selectedProposalIds, decision, overrides);
  const firstReadinessAction = READINESS_STAGES.find(({ stage }) => !stageIsValid(diagnosticState, stage));
  const readyForManualApplication = stageIsValid(diagnosticState, "workflow_readiness_checkpoint");
  const exactValid = stageIsValid(diagnosticState, "live_exact_resume_change_proposal");
  const acceptanceReadback = authoritativeStageReadback(diagnosticState, "manual_exact_change_acceptance");
  const acceptedProposalCount = typeof acceptanceReadback.accepted_proposal_count === "number"
    ? acceptanceReadback.accepted_proposal_count
    : textValues(acceptanceReadback.accepted_proposal_ids).length;
  const tailoringRecommendationCount = Number(tailoring.suggestion_count || tailoringRows(diagnosticState).length);
  const tailoringAttention = tailoringNeedsAttention(diagnosticState);

  return (
    <div className="advanced-diagnostics-dashboard">
      <AdvancedDiagnosticsHeader />
      {state.mode === "hub" ? <HubModeCard options={state.savedScanOptions} hrefs={state.hrefs} navigate={navigate} /> : null}
      {state.mode === "empty" ? <EmptyModeCard hrefs={state.hrefs} /> : null}
      {state.mode === "invalid" ? <InvalidModeCard hrefs={state.hrefs} /> : null}
      {state.mode === "context" && state.context ? (
        <div className="advanced-diagnostics-body" id="scanWorkspaceAdvancedDiagnostics">
          <WizardHeader context={state.context} hrefs={state.hrefs} state={diagnosticState} activeStep={activeStep} onStepChange={setActiveStep} onTechnicalDetails={() => setTechnicalOpen(true)} />
          <div className="advanced-diagnostics-safety-callout" role="note">
            <ShieldCheck size={16} aria-hidden="true" />
            <div><strong>Manual control</strong><p>Every action runs only when you choose it. ApplyLens does not automatically cross human review gates or submit applications.</p></div>
          </div>

          <main className="advanced-diagnostics-guided-flow">
            {activeStep === 0 ? <section className="advanced-diagnostics-workflow-card" id="advancedDiagnosticsSectionGeneration" aria-labelledby="advancedDiagnosticsAnalyzeHeading">
              <div className="advanced-diagnostics-workflow-card-heading"><span>1</span><div><p>Analyze</p><h2 id="advancedDiagnosticsAnalyzeHeading">AI analysis</h2><small>Two distinct, persisted analyses. Each runs only when you choose its action.</small></div></div>
              <div className="advanced-diagnostics-analysis-block">
                <div className="advanced-diagnostics-section-heading"><div><h3>Tailoring recommendations</h3><p>{stageIsValid(diagnosticState, "live_tailoring_suggestion") ? `${tailoringRecommendationCount === 0 ? "0 supported recommendations" : `${tailoringRecommendationCount} recommendations`}${tailoringRecommendationCount > tailoringRows(diagnosticState).length ? ` · showing ${tailoringRows(diagnosticState).length}` : ""}` : "Evidence-backed guidance from the configured AI route."}</p></div><StageStatus state={diagnosticState} stage="live_tailoring_suggestion" /></div>
                <TailoringRecommendations state={diagnosticState} />
                {!stageIsValid(diagnosticState, "live_tailoring_suggestion") ? <button id="scanWorkspaceLiveTailoringSuggestionToggle" aria-label={tailoringAttention ? "Retry tailoring analysis" : "Run tailoring analysis"} className="advanced-diagnostics-primary-action" type="button" disabled={Boolean(runningStage)} onClick={() => void runStage("live_tailoring_suggestion")}>{runningStage === "live_tailoring_suggestion" ? <><LoaderCircle className="advanced-diagnostics-spinner" size={16} />{tailoringAttention ? "Retrying tailoring analysis..." : "Running analysis..."}</> : <><Sparkles size={16} />{tailoringAttention ? "Retry tailoring analysis" : "Run tailoring analysis"}</>}</button> : null}
              </div>
              <div className="advanced-diagnostics-analysis-block is-exact">
                <div className="advanced-diagnostics-section-heading"><div><h3>Exact resume-change analysis</h3><p>{exactValid ? `${proposals.length} evidence-backed proposed changes are ready for review.` : "Generate source-backed proposals for human review."}</p></div><StageStatus state={diagnosticState} stage="live_exact_resume_change_proposal" /></div>
                {exactValid ? <button className="advanced-diagnostics-secondary-action" type="button" onClick={() => setActiveStep(1)}>Go to review changes</button> : <button id="scanWorkspaceLiveExactChangeProposalToggle" aria-label="Live exact change proposals" className="advanced-diagnostics-primary-action" type="button" disabled={Boolean(runningStage)} onClick={() => void runStage("live_exact_resume_change_proposal")}>{runningStage === "live_exact_resume_change_proposal" ? <><LoaderCircle className="advanced-diagnostics-spinner" size={16} />Generating...</> : "Generate proposed changes"}</button>}
              </div>
            </section> : null}

            {activeStep === 1 ? <section className="advanced-diagnostics-workflow-card" id="advancedDiagnosticsSectionArtifactSafety" aria-labelledby="advancedDiagnosticsReviewHeading">
              <div className="advanced-diagnostics-workflow-card-heading"><span>2</span><div><p>Review changes</p><h2 id="advancedDiagnosticsReviewHeading">Proposed resume changes</h2><small>Compare every proposed edit and select only the changes you want to approve.</small></div></div>
              <div className="advanced-diagnostics-selection-summary">
                <div><strong>{proposals.length} proposed changes</strong><span>Current selection · {selectedProposalIds.length} currently selected</span></div>
                {acceptedProposalCount > 0 ? <div className="is-approved"><strong><CheckCircle2 size={16} />Previously approved</strong><span>{acceptedProposalCount} exact change{acceptedProposalCount === 1 ? "" : "s"} previously approved</span></div> : null}
              </div>
              {proposals.length ? <ProposalSelector rows={proposals} selected={selectedProposalIds} onChange={setSelectedProposalIds} /> : <p className="advanced-diagnostics-analysis-empty">Generate proposed changes to begin human review.</p>}
              <button id="scanWorkspaceManualExactChangeAcceptanceToggle" aria-label="Accept selected exact changes" className="advanced-diagnostics-primary-action" type="button" disabled={Boolean(runningStage) || selectedProposalIds.length === 0} onClick={() => setReviewOpen(true)}>Review selected changes</button>
            </section> : null}

            {activeStep === 2 ? <section className="advanced-diagnostics-workflow-card" id="advancedDiagnosticsSectionReviewDecision" aria-labelledby="advancedDiagnosticsVerifyHeading">
              <div className="advanced-diagnostics-workflow-card-heading"><span>3</span><div><p>Verify resume copy</p><h2 id="advancedDiagnosticsVerifyHeading">Protected resume copy</h2><small>The source resume remains unchanged while each guarded step completes separately.</small></div></div>
              <WorkflowChecklist state={diagnosticState} rows={[
                { stage: "manual_exact_change_acceptance", label: "Changes approved" },
                { stage: "guarded_resume_copy_artifact", label: "Protected copy created" },
                { stage: "guarded_resume_copy_artifact_verification", label: stageIsValid(diagnosticState, "guarded_resume_copy_artifact") ? "Protected copy verified" : "Verification required" },
              ]} currentStage={!stageIsValid(diagnosticState, "guarded_resume_copy_artifact") ? "guarded_resume_copy_artifact" : !stageIsValid(diagnosticState, "guarded_resume_copy_artifact_verification") ? "guarded_resume_copy_artifact_verification" : undefined} />
              {!stageIsValid(diagnosticState, "guarded_resume_copy_artifact") ? <button id="scanWorkspaceGuardedResumeCopyArtifactToggle" aria-label="Create guarded resume copy" className="advanced-diagnostics-primary-action" type="button" disabled={Boolean(runningStage) || Boolean(actionReason("guarded_resume_copy_artifact"))} title={actionReason("guarded_resume_copy_artifact")} onClick={() => void runStage("guarded_resume_copy_artifact")}>Create protected copy</button> : null}
              {stageIsValid(diagnosticState, "guarded_resume_copy_artifact") && !stageIsValid(diagnosticState, "guarded_resume_copy_artifact_verification") ? <button id="scanWorkspaceGuardedResumeCopyArtifactVerificationToggle" aria-label="Verify guarded resume copy" className="advanced-diagnostics-primary-action" type="button" disabled={Boolean(runningStage) || Boolean(actionReason("guarded_resume_copy_artifact_verification"))} title={actionReason("guarded_resume_copy_artifact_verification")} onClick={() => void runStage("guarded_resume_copy_artifact_verification")}>Verify protected copy</button> : null}
              {stageIsValid(diagnosticState, "guarded_resume_copy_artifact_verification") ? <button className="advanced-diagnostics-secondary-action advanced-diagnostics-pane-navigation" type="button" onClick={() => setActiveStep(3)}>Continue to Ready</button> : null}
            </section> : null}

            {activeStep === 3 ? <section className="advanced-diagnostics-workflow-card" id="advancedDiagnosticsSectionManualHandoff" aria-labelledby="advancedDiagnosticsReadyHeading">
              <div className="advanced-diagnostics-workflow-card-heading"><span>4</span><div><p>Prepare manual application</p><h2 id="advancedDiagnosticsReadyHeading">Manual application readiness</h2><small>A sequential, human-only preparation chain. This status never submits an application.</small></div></div>
              <WorkflowChecklist state={diagnosticState} rows={READINESS_STAGES} currentStage={firstReadinessAction?.stage} />
              {firstReadinessAction && firstReadinessAction.stage === "verified_artifact_operator_decision" ? <button id="scanWorkspaceVerifiedArtifactOperatorDecisionToggle" aria-label="Capture verified artifact operator decision" className="advanced-diagnostics-primary-action" type="button" disabled={Boolean(runningStage) || Boolean(actionReason("verified_artifact_operator_decision", "accepted").replace("Choose an explicit operator decision below.", ""))} onClick={() => setDecisionOpen(true)}>Record decision</button> : null}
              {firstReadinessAction && firstReadinessAction.stage !== "verified_artifact_operator_decision" ? <button id={STAGE_BY_NAME[firstReadinessAction.stage].id} aria-label={STAGE_BY_NAME[firstReadinessAction.stage].label} className="advanced-diagnostics-primary-action" type="button" disabled={Boolean(runningStage) || Boolean(actionReason(firstReadinessAction.stage))} title={actionReason(firstReadinessAction.stage)} onClick={() => void runStage(firstReadinessAction.stage)}>{runningStage === firstReadinessAction.stage ? <><LoaderCircle className="advanced-diagnostics-spinner" size={16} />Running...</> : firstReadinessAction.action}</button> : null}
              <div className={`advanced-diagnostics-manual-safety ${readyForManualApplication ? "is-ready" : ""}`} role="note"><ShieldCheck size={20} /><div><strong>{readyForManualApplication ? "Ready for manual application" : "Manual application boundary preserved"}</strong><p>{readyForManualApplication ? "ApplyLens has prepared the workflow for manual application. " : ""}ApplyLens has not submitted an application, contacted a recruiter, marked the job applied, or changed the application queue automatically.</p></div></div>
              {readyForManualApplication ? <div className="advanced-diagnostics-rerun-panel"><button className="advanced-diagnostics-secondary-action advanced-diagnostics-rerun-action" type="button" disabled={resetting || Boolean(runningStage)} onClick={() => setResetOpen(true)}>Run diagnostics again</button></div> : null}
            </section> : null}
          </main>

          <TechnicalDrawer open={technicalOpen} onClose={() => setTechnicalOpen(false)}>
              <div className="advanced-diagnostics-readbacks" aria-label="Scan diagnostic readbacks">
                <section className="advanced-diagnostics-technical-section" aria-labelledby="advancedDiagnosticsTechnicalScanHeading">
                  <header><span>01</span><h3 id="advancedDiagnosticsTechnicalScanHeading">Scan</h3></header>
                  <div className="advanced-diagnostics-technical-context"><div><strong>Context ID</strong><span>{state.context.contextId}</span></div><div><strong>Last diagnostic update</strong><span className="advanced-diagnostics-technical-timestamp">{diagnosticTimestampParts(diagnosticState.updated_at).map((part) => <span key={part}>{part}</span>)}</span></div><div><strong>Internal checks complete</strong><span>{DIAGNOSTIC_STAGE_ORDER.filter((stage) => stageIsValid(diagnosticState, stage)).length} of {DIAGNOSTIC_STAGE_ORDER.length}</span></div></div>
                  <div className="advanced-diagnostics-technical-list" aria-label="Internal checks">
                    {AMBIENT_READBACKS.slice(1).map((row) => <ReadbackRow key={row.id} id={row.id} label={row.label} value={asRecord(ambient[row.key])} />)}
                  </div>
                </section>
                <section className="advanced-diagnostics-technical-section" aria-labelledby="advancedDiagnosticsTechnicalAiHeading">
                  <header><span>02</span><h3 id="advancedDiagnosticsTechnicalAiHeading">AI providers</h3></header>
                  <div className="advanced-diagnostics-technical-list">
                    <ReadbackRow id={AMBIENT_READBACKS[0].id} label={AMBIENT_READBACKS[0].label} value={asRecord(ambient[AMBIENT_READBACKS[0].key])} />
                    {DIAGNOSTIC_STAGE_ORDER.slice(0, 2).map((stage) => { const config = STAGE_BY_NAME[stage]; return <ReadbackRow key={config.readbackKey} id={STAGE_READBACK_IDS[stage]} label={config.label} value={asRecord(readbacks[config.readbackKey])} />; })}
                  </div>
                </section>
                <section className="advanced-diagnostics-technical-section" aria-labelledby="advancedDiagnosticsTechnicalWorkflowHeading">
                  <header><span>03</span><h3 id="advancedDiagnosticsTechnicalWorkflowHeading">Workflow</h3></header>
                  <div className="advanced-diagnostics-technical-list">
                    {DIAGNOSTIC_STAGE_ORDER.slice(2).map((stage) => { const config = STAGE_BY_NAME[stage]; return <ReadbackRow key={config.readbackKey} id={STAGE_READBACK_IDS[stage]} label={config.label} value={asRecord(readbacks[config.readbackKey])} />; })}
                  </div>
                </section>
              </div>
              <ManualOverrides values={overrides} onChange={(key, value) => setOverrides((current) => ({ ...current, [key]: value }))} />
          </TechnicalDrawer>

          {message ? <div className={`advanced-diagnostics-request-message is-${message.tone}`} role={message.tone === "error" ? "alert" : "status"}>{message.text}</div> : null}

          <PremiumDialog open={reviewOpen} title="Review resume changes" description={`${selectedProposalIds.length} change${selectedProposalIds.length === 1 ? "" : "s"} selected`} onClose={() => setReviewOpen(false)} footer={<><button className="advanced-diagnostics-dialog-secondary advanced-diagnostics-dialog-cancel" type="button" autoFocus onClick={() => setReviewOpen(false)}>Cancel</button><button className="advanced-diagnostics-dialog-primary" type="button" disabled={Boolean(runningStage)} onClick={() => void runStage("manual_exact_change_acceptance").then((success) => success && setReviewOpen(false))}>{runningStage === "manual_exact_change_acceptance" ? "Accepting..." : "Accept selected changes"}</button></>}>
            <SelectedProposalReview rows={selectedProposals} />
            <div className="advanced-diagnostics-dialog-safety"><ShieldCheck size={18} /><p><strong>What happens next</strong>Accepting these changes does not overwrite the source resume. It authorizes the existing guarded-copy workflow.</p></div>
          </PremiumDialog>

          <PremiumDialog open={decisionOpen} title="Review protected resume" description="Human decision required" onClose={() => setDecisionOpen(false)} footer={<><button className="advanced-diagnostics-dialog-secondary advanced-diagnostics-dialog-cancel" type="button" autoFocus onClick={() => setDecisionOpen(false)}>Cancel</button>{(["rejected", "needs_changes", "accepted"] as const).map((value) => <button key={value} id={value === "accepted" ? "scanWorkspaceVerifiedArtifactOperatorDecisionValue" : undefined} className={`advanced-diagnostics-dialog-secondary advanced-diagnostics-dialog-action--${value === "needs_changes" ? "warning" : value === "rejected" ? "danger" : "success"}`} type="button" disabled={Boolean(runningStage)} onClick={() => void runStage("verified_artifact_operator_decision", value).then((success) => success && setDecisionOpen(false))}>{humanLabel(value)}</button>)}</>}>
            <div className="advanced-diagnostics-decision-summary"><ClipboardCheck size={22} /><div><strong>Verified artifact review packet</strong><p>Protected resume artifact is ready for review.</p></div></div>
            <div className="advanced-diagnostics-dialog-safety"><ShieldCheck size={18} /><p><strong>Your decision is explicit</strong>No option is preselected, and recording it does not submit an application or overwrite the source resume.</p></div>
          </PremiumDialog>

          <PremiumDialog open={resetOpen} eyebrow="Start a new diagnostics workflow" title="Run diagnostics again?" description="Replace the current diagnostics workflow for this saved scan" onClose={() => { if (!resetting) setResetOpen(false); }} footer={<><button className="advanced-diagnostics-dialog-secondary advanced-diagnostics-dialog-cancel" type="button" autoFocus disabled={resetting} onClick={() => setResetOpen(false)}>Cancel</button><button className="advanced-diagnostics-dialog-primary" type="button" disabled={resetting} onClick={() => void resetDiagnostics()}>{resetting ? <><LoaderCircle className="advanced-diagnostics-spinner" size={16} />Resetting...</> : "Run diagnostics again"}</button></>}>
            <div className="advanced-diagnostics-reset-copy">
              <p>This will replace the current diagnostics workflow for this saved scan.</p>
              <p>Your saved scan, job details, and original resume will stay unchanged.</p>
              <div><strong>Will be replaced</strong><ul><li>Current diagnostics results</li><li>Accepted diagnostic changes</li><li>Verification and readiness state</li></ul></div>
              <div><strong>Will not be changed</strong><ul><li>Saved scan and job description</li><li>Original resume</li></ul></div>
            </div>
          </PremiumDialog>
        </div>
      ) : null}
    </div>
  );
}
