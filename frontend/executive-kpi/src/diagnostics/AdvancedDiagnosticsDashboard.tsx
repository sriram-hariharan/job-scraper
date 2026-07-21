import {
  ClipboardCheck,
  ClipboardList,
  FileQuestion,
  FileSearch,
  Inbox,
  ShieldCheck,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { SharedFilterSelect, type SharedFilterOption } from "../filter/FilterSelect";

/**
 * Advanced Diagnostics Command Center.
 *
 * Layout patterns (bento card hierarchy, status badges, empty state, safety
 * alert, select affordances) are adapted from 21st.dev references into this
 * project's existing local React/CSS conventions:
 *   https://21st.dev/@kokonutd/components/bento-grid
 *   https://21st.dev/@uniquesonu/components/status-badge-beautiful-accessible-status-indicators
 *   https://21st.dev/@serafimcloud/components/empty-state
 *   https://21st.dev/community/components/coss.com/alert/warning
 *   https://21st.dev/community/components/originui/select/options-with-icon
 *   https://21st.dev/community/components/originui/select/status-select
 * No 21st.dev packages, demo content, or dependencies were installed; the
 * saved-scan selector reuses SharedFilterSelect rather than an Origin UI
 * import. This page performs no fetch and no diagnostic control mutates
 * state or triggers a backend request — Run selected diagnostics stays
 * permanently disabled by design.
 */

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

export type AdvancedDiagnosticsHrefs = {
  advancedDiagnostics: string;
  scanWorkspace: string;
};

export type AdvancedDiagnosticsMode = "hub" | "context" | "empty" | "invalid";

export type AdvancedDiagnosticsState = {
  mode: AdvancedDiagnosticsMode;
  savedScanOptions: AdvancedDiagnosticsSavedScanOption[];
  selectedScanId: string;
  context: AdvancedDiagnosticsContext | null;
  hrefs: AdvancedDiagnosticsHrefs;
};

export const DEFAULT_ADVANCED_DIAGNOSTICS_STATE: AdvancedDiagnosticsState = {
  mode: "empty",
  savedScanOptions: [],
  selectedScanId: "",
  context: null,
  hrefs: { advancedDiagnostics: "/advanced-diagnostics", scanWorkspace: "/scan-workspace" },
};

declare global {
  interface Window {
    __APPLYLENS_ADVANCED_DIAGNOSTICS_STATE__?: AdvancedDiagnosticsState;
  }
}

type TextFieldConfig = { id: string; placeholder: string; ariaLabel: string };
type SelectOptionConfig = { value: string; label: string };
type SelectFieldConfig = { id: string; ariaLabel: string; options: SelectOptionConfig[] };
type CheckboxGroupConfig = {
  checkbox: { id: string; label: string };
  texts?: TextFieldConfig[];
  selects?: SelectFieldConfig[];
};

type DiagnosticGroupConfig = {
  sectionId: string;
  navLabel: string;
  tone: "blue" | "teal" | "violet" | "amber";
  icon: typeof ClipboardList;
  title: string;
  description: string;
  standaloneCheckboxes?: { id: string; label: string }[];
  checkboxGroups: CheckboxGroupConfig[];
};

const GENERATION_GROUP: DiagnosticGroupConfig = {
  sectionId: "advancedDiagnosticsSectionGeneration",
  navLabel: "Generation",
  tone: "blue",
  icon: ClipboardList,
  title: "Generation diagnostics",
  description: "Controls for suggestion and exact-change generation checks.",
  standaloneCheckboxes: [
    { id: "scanWorkspaceLiveTailoringSuggestionToggle", label: "Live tailoring suggestions" },
    { id: "scanWorkspaceLiveExactChangeProposalToggle", label: "Live exact change proposals" },
  ],
  checkboxGroups: [
    {
      checkbox: { id: "scanWorkspaceManualExactChangeAcceptanceToggle", label: "Accept selected exact changes" },
      texts: [
        {
          id: "scanWorkspaceAcceptedExactChangeProposalIds",
          placeholder: "Accepted proposal IDs",
          ariaLabel: "Accepted exact change proposal IDs",
        },
      ],
    },
  ],
};

const ARTIFACT_SAFETY_GROUP: DiagnosticGroupConfig = {
  sectionId: "advancedDiagnosticsSectionArtifactSafety",
  navLabel: "Artifact safety",
  tone: "teal",
  icon: ShieldCheck,
  title: "Resume artifact safety",
  description: "Checks protected resume-copy and artifact verification workflow.",
  checkboxGroups: [
    {
      checkbox: { id: "scanWorkspaceGuardedResumeCopyArtifactToggle", label: "Create guarded resume copy" },
      texts: [
        { id: "scanWorkspaceApprovedChangePlanId", placeholder: "Approved change plan ID", ariaLabel: "Approved change plan ID" },
      ],
    },
    {
      checkbox: {
        id: "scanWorkspaceGuardedResumeCopyArtifactVerificationToggle",
        label: "Verify guarded resume copy",
      },
      texts: [
        { id: "scanWorkspaceGuardedResumeCopyArtifactId", placeholder: "Guarded artifact ID", ariaLabel: "Guarded resume copy artifact ID" },
      ],
    },
  ],
};

const REVIEW_DECISION_GROUP: DiagnosticGroupConfig = {
  sectionId: "advancedDiagnosticsSectionReviewDecision",
  navLabel: "Review and decision",
  tone: "violet",
  icon: FileSearch,
  title: "Review packet/operator decision",
  description: "Checks review-packet creation and human decision capture.",
  checkboxGroups: [
    {
      checkbox: {
        id: "scanWorkspaceVerifiedArtifactOperatorReviewPacketToggle",
        label: "Create verified artifact review packet",
      },
      texts: [
        {
          id: "scanWorkspaceVerifiedArtifactOperatorReviewArtifactId",
          placeholder: "Verified artifact ID",
          ariaLabel: "Verified artifact operator review artifact ID",
        },
      ],
    },
    {
      checkbox: {
        id: "scanWorkspaceVerifiedArtifactOperatorDecisionToggle",
        label: "Capture verified artifact operator decision",
      },
      texts: [
        {
          id: "scanWorkspaceVerifiedArtifactOperatorDecisionPacketId",
          placeholder: "Operator review packet ID",
          ariaLabel: "Verified artifact operator decision packet ID",
        },
        {
          id: "scanWorkspaceVerifiedArtifactOperatorDecisionArtifactId",
          placeholder: "Verified artifact ID",
          ariaLabel: "Verified artifact operator decision artifact ID",
        },
      ],
      selects: [
        {
          id: "scanWorkspaceVerifiedArtifactOperatorDecisionValue",
          ariaLabel: "Verified artifact operator decision value",
          options: [
            { value: "", label: "Decision" },
            { value: "accepted", label: "Accepted" },
            { value: "rejected", label: "Rejected" },
            { value: "needs_changes", label: "Needs changes" },
          ],
        },
      ],
    },
  ],
};

const MANUAL_HANDOFF_GROUP: DiagnosticGroupConfig = {
  sectionId: "advancedDiagnosticsSectionManualHandoff",
  navLabel: "Manual handoff",
  tone: "amber",
  icon: Inbox,
  title: "Manual handoff/readiness",
  description: "Checks manual-only application handoff, readiness, audit, and safety summaries.",
  checkboxGroups: [
    {
      checkbox: { id: "scanWorkspaceApplicationReadinessPacketToggle", label: "Create application-readiness packet" },
      texts: [
        { id: "scanWorkspaceApplicationReadinessDecisionId", placeholder: "Operator decision ID", ariaLabel: "Application readiness operator decision ID" },
        { id: "scanWorkspaceApplicationReadinessReviewPacketId", placeholder: "Operator review packet ID", ariaLabel: "Application readiness operator review packet ID" },
        { id: "scanWorkspaceApplicationReadinessArtifactId", placeholder: "Verified artifact ID", ariaLabel: "Application readiness artifact ID" },
      ],
    },
    {
      checkbox: {
        id: "scanWorkspaceManualApplicationHandoffPacketToggle",
        label: "Create human-only manual application handoff packet",
      },
      texts: [
        { id: "scanWorkspaceManualHandoffReadinessPacketId", placeholder: "Application readiness packet ID", ariaLabel: "Manual handoff application readiness packet ID" },
        { id: "scanWorkspaceManualHandoffArtifactId", placeholder: "Verified artifact ID", ariaLabel: "Manual handoff verified artifact ID" },
      ],
    },
    {
      checkbox: { id: "scanWorkspaceHandoffAuditTrailToggle", label: "Create human-only handoff audit trail" },
      texts: [
        { id: "scanWorkspaceHandoffAuditHandoffPacketId", placeholder: "Manual handoff packet ID", ariaLabel: "Handoff audit manual handoff packet ID" },
        { id: "scanWorkspaceHandoffAuditReadinessPacketId", placeholder: "Application readiness packet ID", ariaLabel: "Handoff audit application readiness packet ID" },
        { id: "scanWorkspaceHandoffAuditArtifactId", placeholder: "Verified artifact ID", ariaLabel: "Handoff audit verified artifact ID" },
      ],
    },
    {
      checkbox: { id: "scanWorkspaceSafetyBoundarySummaryToggle", label: "Create human-only safety boundary summary" },
      texts: [
        { id: "scanWorkspaceSafetyBoundaryAuditTrailId", placeholder: "Handoff audit trail ID", ariaLabel: "Safety boundary handoff audit trail ID" },
        { id: "scanWorkspaceSafetyBoundaryHandoffPacketId", placeholder: "Manual handoff packet ID", ariaLabel: "Safety boundary manual handoff packet ID" },
        { id: "scanWorkspaceSafetyBoundaryReadinessPacketId", placeholder: "Application readiness packet ID", ariaLabel: "Safety boundary application readiness packet ID" },
        { id: "scanWorkspaceSafetyBoundaryArtifactId", placeholder: "Verified artifact ID", ariaLabel: "Safety boundary verified artifact ID" },
      ],
    },
    {
      checkbox: { id: "scanWorkspaceWorkflowReadinessCheckpointToggle", label: "Create human-only workflow readiness checkpoint" },
      texts: [
        { id: "scanWorkspaceWorkflowReadinessSummaryId", placeholder: "Safety boundary summary ID", ariaLabel: "Workflow readiness safety boundary summary ID" },
        { id: "scanWorkspaceWorkflowReadinessAuditTrailId", placeholder: "Handoff audit trail ID", ariaLabel: "Workflow readiness handoff audit trail ID" },
        { id: "scanWorkspaceWorkflowReadinessHandoffPacketId", placeholder: "Manual handoff packet ID", ariaLabel: "Workflow readiness manual handoff packet ID" },
        { id: "scanWorkspaceWorkflowReadinessReadinessPacketId", placeholder: "Application readiness packet ID", ariaLabel: "Workflow readiness application readiness packet ID" },
        { id: "scanWorkspaceWorkflowReadinessArtifactId", placeholder: "Verified artifact ID", ariaLabel: "Workflow readiness verified artifact ID" },
      ],
    },
  ],
};

const DIAGNOSTIC_GROUPS: DiagnosticGroupConfig[] = [
  GENERATION_GROUP,
  ARTIFACT_SAFETY_GROUP,
  REVIEW_DECISION_GROUP,
  MANUAL_HANDOFF_GROUP,
];

type ReadbackRowConfig = { id: string; label: string; tone: "default" | "waiting"; ariaLabel?: string };

const READBACK_SECTION_ID = "advancedDiagnosticsSectionReadbacks";

const READBACK_ROWS: ReadbackRowConfig[] = [
  { id: "scanWorkspaceJdLlmReadback", label: "Live JD LLM", tone: "default" },
  { id: "scanWorkspaceTailoringLlmReadback", label: "Live tailoring LLM", tone: "default" },
  { id: "scanWorkspaceExactChangeLlmReadback", label: "Live exact change LLM", tone: "default" },
  { id: "scanWorkspaceManualExactChangeAcceptanceReadback", label: "Manual exact change acceptance", tone: "default" },
  { id: "scanWorkspaceGuardedResumeCopyArtifactReadback", label: "Guarded resume copy artifact", tone: "default" },
  { id: "scanWorkspaceGuardedResumeCopyArtifactVerificationReadback", label: "Guarded artifact verification", tone: "default" },
  { id: "scanWorkspaceVerifiedArtifactOperatorReviewPacketReadback", label: "Verified artifact operator review packet", tone: "default" },
  { id: "scanWorkspaceVerifiedArtifactOperatorDecisionReadback", label: "Verified artifact operator decision", tone: "default" },
  { id: "scanWorkspaceApplicationReadinessPacketReadback", label: "Application readiness packet", tone: "default" },
  { id: "scanWorkspaceManualApplicationHandoffPacketReadback", label: "Manual application handoff packet", tone: "default" },
  { id: "scanWorkspaceHandoffAuditTrailReadback", label: "Handoff audit trail", tone: "default" },
  { id: "scanWorkspaceSafetyBoundarySummaryReadback", label: "Safety boundary summary", tone: "default" },
  { id: "scanWorkspaceWorkflowReadinessCheckpointReadback", label: "Workflow readiness checkpoint", tone: "default" },
  {
    id: "scanWorkspaceAgenticWorkflowIntegrationReadback",
    label: "Agentic workflow demo readiness",
    tone: "waiting",
    ariaLabel: "Agentic workflow demo readiness: waiting for existing scan/evaluation readback",
  },
  {
    id: "scanWorkspaceProductionReadinessCheckpointReadback",
    label: "Demo readiness",
    tone: "waiting",
    ariaLabel: "Demo readiness: backend checkpoint readback waiting for existing data",
  },
];

const READBACK_DEFAULT_OFF_COUNT = READBACK_ROWS.filter((row) => row.tone === "default").length;
const READBACK_WAITING_COUNT = READBACK_ROWS.filter((row) => row.tone === "waiting").length;

const SECTION_NAV_ITEMS = [
  ...DIAGNOSTIC_GROUPS.map((group) => ({ sectionId: group.sectionId, label: group.navLabel })),
  { sectionId: READBACK_SECTION_ID, label: "Readback status" },
];

type ControlsState = {
  checkboxes: Record<string, boolean>;
  texts: Record<string, string>;
  selects: Record<string, string>;
};

function buildInitialControlsState(): ControlsState {
  const checkboxes: Record<string, boolean> = {};
  const texts: Record<string, string> = {};
  const selects: Record<string, string> = {};
  for (const group of DIAGNOSTIC_GROUPS) {
    for (const checkbox of group.standaloneCheckboxes || []) {
      checkboxes[checkbox.id] = false;
    }
    for (const checkboxGroup of group.checkboxGroups) {
      checkboxes[checkboxGroup.checkbox.id] = false;
      for (const text of checkboxGroup.texts || []) {
        texts[text.id] = "";
      }
      for (const select of checkboxGroup.selects || []) {
        selects[select.id] = "";
      }
    }
  }
  return { checkboxes, texts, selects };
}

function CheckboxField({
  id,
  label,
  checked,
  onChange,
}: {
  id: string;
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}) {
  return (
    <label className="advanced-diagnostics-checkbox-field" htmlFor={id}>
      <input id={id} type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} />
      <span>{label}</span>
    </label>
  );
}

function TextInputField({
  field,
  value,
  onChange,
  nested,
}: {
  field: TextFieldConfig;
  value: string;
  onChange: (value: string) => void;
  nested?: boolean;
}) {
  return (
    <input
      type="text"
      id={field.id}
      className={`advanced-diagnostics-text-field ${nested ? "is-nested" : ""}`}
      placeholder={field.placeholder}
      aria-label={field.ariaLabel}
      value={value}
      onChange={(event) => onChange(event.target.value)}
    />
  );
}

function SelectField({
  field,
  value,
  onChange,
  nested,
}: {
  field: SelectFieldConfig;
  value: string;
  onChange: (value: string) => void;
  nested?: boolean;
}) {
  return (
    <select
      id={field.id}
      className={`advanced-diagnostics-select-field ${nested ? "is-nested" : ""}`}
      aria-label={field.ariaLabel}
      value={value}
      onChange={(event) => onChange(event.target.value)}
    >
      {field.options.map((option) => (
        <option key={option.value || "__blank__"} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  );
}

function DiagnosticGroupCard({
  group,
  controls,
  onCheckboxChange,
  onTextChange,
  onSelectChange,
}: {
  group: DiagnosticGroupConfig;
  controls: ControlsState;
  onCheckboxChange: (id: string, checked: boolean) => void;
  onTextChange: (id: string, value: string) => void;
  onSelectChange: (id: string, value: string) => void;
}) {
  const Icon = group.icon;
  return (
    <section
      className="advanced-diagnostics-card"
      data-tone={group.tone}
      id={group.sectionId}
      aria-labelledby={`${group.sectionId}Heading`}
    >
      <div className="advanced-diagnostics-card-heading">
        <span className="advanced-diagnostics-card-icon-tile" aria-hidden="true">
          <Icon size={17} />
        </span>
        <div>
          <h3 id={`${group.sectionId}Heading`}>{group.title}</h3>
          <p className="advanced-diagnostics-card-description">{group.description}</p>
        </div>
        <span className="advanced-diagnostics-badge advanced-diagnostics-badge--review-only">Review only</span>
      </div>
      <div className="advanced-diagnostics-card-fields">
        {(group.standaloneCheckboxes || []).map((checkbox) => (
          <CheckboxField
            key={checkbox.id}
            id={checkbox.id}
            label={checkbox.label}
            checked={Boolean(controls.checkboxes[checkbox.id])}
            onChange={(checked) => onCheckboxChange(checkbox.id, checked)}
          />
        ))}
        {group.checkboxGroups.map((checkboxGroup) => (
          <div className="advanced-diagnostics-field-group" key={checkboxGroup.checkbox.id}>
            <CheckboxField
              id={checkboxGroup.checkbox.id}
              label={checkboxGroup.checkbox.label}
              checked={Boolean(controls.checkboxes[checkboxGroup.checkbox.id])}
              onChange={(checked) => onCheckboxChange(checkboxGroup.checkbox.id, checked)}
            />
            <div className="advanced-diagnostics-field-group-nested">
              {(checkboxGroup.texts || []).map((text) => (
                <TextInputField
                  key={text.id}
                  field={text}
                  value={controls.texts[text.id] || ""}
                  onChange={(value) => onTextChange(text.id, value)}
                  nested
                />
              ))}
              {(checkboxGroup.selects || []).map((select) => (
                <SelectField
                  key={select.id}
                  field={select}
                  value={controls.selects[select.id] || ""}
                  onChange={(value) => onSelectChange(select.id, value)}
                  nested
                />
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function ReadbackRow({ row }: { row: ReadbackRowConfig }) {
  return (
    <div
      className={`advanced-diagnostics-readback-row advanced-diagnostics-readback-row--${row.tone}`}
      id={row.id}
      aria-live="polite"
      {...(row.ariaLabel ? { "aria-label": row.ariaLabel } : {})}
    >
      <span className="advanced-diagnostics-readback-label">{row.label}</span>
      <span className={`advanced-diagnostics-badge advanced-diagnostics-badge--${row.tone}`}>
        {row.tone === "waiting" ? "Waiting" : "Default off"}
      </span>
    </div>
  );
}

function SectionNav({ activeSection }: { activeSection: string }) {
  return (
    <>
      <nav className="advanced-diagnostics-section-rail" aria-label="Diagnostics sections">
        <p className="advanced-diagnostics-section-rail-summary">
          {READBACK_ROWS.length} readbacks · {READBACK_DEFAULT_OFF_COUNT} default-off · {READBACK_WAITING_COUNT} waiting
        </p>
        <ul>
          {SECTION_NAV_ITEMS.map((item) => (
            <li key={item.sectionId}>
              <a
                href={`#${item.sectionId}`}
                className={activeSection === item.sectionId ? "is-active" : ""}
              >
                {item.label}
              </a>
            </li>
          ))}
        </ul>
      </nav>
      <nav className="advanced-diagnostics-section-shortcuts" aria-label="Diagnostics sections">
        {SECTION_NAV_ITEMS.map((item) => (
          <a
            key={item.sectionId}
            href={`#${item.sectionId}`}
            className={activeSection === item.sectionId ? "is-active" : ""}
          >
            {item.label}
          </a>
        ))}
      </nav>
    </>
  );
}

function AdvancedDiagnosticsHeader() {
  return (
    <header className="advanced-diagnostics-header">
      <div className="advanced-diagnostics-header-primary">
        <span className="advanced-diagnostics-header-icon-tile" aria-hidden="true">
          <ShieldCheck size={22} />
        </span>
        <div>
          <div className="advanced-diagnostics-header-title-row">
            <h1>Advanced Diagnostics</h1>
            <span className="advanced-diagnostics-badge advanced-diagnostics-badge--muted">Admin only</span>
            <span className="advanced-diagnostics-badge advanced-diagnostics-badge--muted">Read-only</span>
          </div>
          <p className="advanced-diagnostics-header-description">
            Admin workflow diagnostics for saved scan contexts and scan-specific readbacks.
          </p>
        </div>
      </div>
    </header>
  );
}

function HubModeCard({
  options,
  hrefs,
  navigate,
}: {
  options: AdvancedDiagnosticsSavedScanOption[];
  hrefs: AdvancedDiagnosticsHrefs;
  navigate: (href: string) => void;
}) {
  const [selectedScanId, setSelectedScanId] = useState<string[]>([]);
  const filterOptions: SharedFilterOption[] = useMemo(
    () =>
      options.map((option) => ({
        value: option.scanId,
        label: option.secondary ? `${option.primary} — ${option.secondary}` : option.primary,
      })),
    [options],
  );

  const openDiagnostics = () => {
    const scanId = selectedScanId[0];
    if (!scanId) return;
    navigate(`${hrefs.advancedDiagnostics}?saved_scan_id=${encodeURIComponent(scanId)}`);
  };

  return (
    <section className="advanced-diagnostics-card advanced-diagnostics-hub-card">
      <h2>Choose a saved scan</h2>
      <p className="advanced-diagnostics-card-description">
        Select a saved scan to open scan-specific diagnostics.
      </p>
      <div className="advanced-diagnostics-hub-controls">
        <SharedFilterSelect
          id="advancedDiagnosticsScanSelect"
          label="Saved scan"
          options={filterOptions}
          values={selectedScanId}
          onChange={setSelectedScanId}
          placeholder="Choose a saved scan..."
          mode="single"
          searchable
          portalClassName="advanced-diagnostics-scan-menu"
        />
        <button
          type="button"
          className="ghost-btn btn-sm advanced-diagnostics-open-btn"
          disabled={!selectedScanId[0]}
          onClick={openDiagnostics}
        >
          Open diagnostics
        </button>
      </div>
    </section>
  );
}

function EmptyModeCard({ hrefs }: { hrefs: AdvancedDiagnosticsHrefs }) {
  return (
    <section className="advanced-diagnostics-card advanced-diagnostics-empty-card">
      <span className="advanced-diagnostics-empty-icon-cluster" aria-hidden="true">
        <FileSearch size={26} />
      </span>
      <h2>No saved scans available</h2>
      <p className="advanced-diagnostics-card-description">
        Advanced Diagnostics needs a saved or loaded AI Optimize Scan before scan-specific
        controls and readbacks can be opened.
      </p>
      <a className="ghost-btn btn-sm" href={hrefs.scanWorkspace}>
        Open New Scan
      </a>
    </section>
  );
}

function InvalidModeCard({ hrefs }: { hrefs: AdvancedDiagnosticsHrefs }) {
  return (
    <section className="advanced-diagnostics-card advanced-diagnostics-invalid-card">
      <span className="advanced-diagnostics-invalid-icon-tile" aria-hidden="true">
        <FileQuestion size={26} />
      </span>
      <h2>Scan context unavailable</h2>
      <p className="advanced-diagnostics-card-description">
        This scan could not be found or is not available to this account.
      </p>
      <a className="ghost-btn btn-sm" href={hrefs.advancedDiagnostics}>
        Choose another saved scan
      </a>
    </section>
  );
}

function ContextHero({
  context,
  hrefs,
}: {
  context: AdvancedDiagnosticsContext;
  hrefs: AdvancedDiagnosticsHrefs;
}) {
  return (
    <section className="advanced-diagnostics-card advanced-diagnostics-context-hero">
      <div className="advanced-diagnostics-context-hero-heading">
        <p className="advanced-diagnostics-context-hero-eyebrow">Scan context</p>
        <div className="advanced-diagnostics-context-hero-actions">
          <a className="ghost-btn btn-sm advanced-diagnostics-change-scan-btn" href={hrefs.advancedDiagnostics}>
            Change scan
          </a>
          <a className="advanced-diagnostics-back-btn" href={context.backToScanHref}>
            Back to scan
          </a>
        </div>
      </div>
      <h2 title={`${context.company} / ${context.title}`}>
        {context.company} / {context.title}
      </h2>
      <div className="advanced-diagnostics-context-hero-pills">
        <span className="advanced-diagnostics-pill" title={context.resume}>
          <strong>Resume</strong>
          {context.resume}
        </span>
        <span className="advanced-diagnostics-pill" title={context.status}>
          <strong>Status</strong>
          {context.status}
        </span>
        <span className="advanced-diagnostics-pill" title={context.contextId}>
          <strong>Context</strong>
          <span className="advanced-diagnostics-pill-truncate">{context.contextId}</span>
        </span>
      </div>
    </section>
  );
}

function SafetyCallout() {
  return (
    <div className="advanced-diagnostics-safety-callout" role="note">
      <ShieldCheck size={18} aria-hidden="true" />
      <div>
        <strong>Selections are review-only</strong>
        <p>
          Selecting diagnostics does not run them. These do not apply to jobs automatically.
          Diagnostics never apply to jobs automatically.
        </p>
      </div>
    </div>
  );
}

function ActionBar({ onClear }: { onClear: () => void }) {
  return (
    <div className="advanced-diagnostics-action-bar">
      <p className="advanced-diagnostics-action-bar-note">
        Selections remain local and review-only. Execution is not enabled yet. Selections are
        for admin review only.
      </p>
      <div className="advanced-diagnostics-action-bar-buttons">
        <button type="button" className="advanced-diagnostics-clear-btn" onClick={onClear}>
          Clear selections
        </button>
        <button
          type="button"
          className="advanced-diagnostics-run-btn"
          disabled
          title="Execution is not enabled yet. Selections are for admin review only."
        >
          Run selected diagnostics
        </button>
      </div>
    </div>
  );
}

export function AdvancedDiagnosticsDashboard({
  state = DEFAULT_ADVANCED_DIAGNOSTICS_STATE,
  navigate = (href: string) => {
    window.location.href = href;
  },
}: {
  state?: AdvancedDiagnosticsState;
  navigate?: (href: string) => void;
}) {
  const [controls, setControls] = useState<ControlsState>(() => buildInitialControlsState());
  const [activeSection, setActiveSection] = useState<string>(SECTION_NAV_ITEMS[0].sectionId);

  useEffect(() => {
    if (typeof IntersectionObserver === "undefined") return undefined;
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
        if (visible?.target?.id) setActiveSection(visible.target.id);
      },
      { rootMargin: "-35% 0px -45% 0px" },
    );
    for (const item of SECTION_NAV_ITEMS) {
      const el = document.getElementById(item.sectionId);
      if (el) observer.observe(el);
    }
    return () => observer.disconnect();
  }, [state.mode]);

  const handleCheckboxChange = (id: string, checked: boolean) => {
    setControls((prev) => ({ ...prev, checkboxes: { ...prev.checkboxes, [id]: checked } }));
  };
  const handleTextChange = (id: string, value: string) => {
    setControls((prev) => ({ ...prev, texts: { ...prev.texts, [id]: value } }));
  };
  const handleSelectChange = (id: string, value: string) => {
    setControls((prev) => ({ ...prev, selects: { ...prev.selects, [id]: value } }));
  };
  const handleClearSelections = () => setControls(buildInitialControlsState());

  const showControls = state.mode === "context";

  return (
    <div className="advanced-diagnostics-dashboard">
      <AdvancedDiagnosticsHeader />

      {state.mode === "hub" ? <HubModeCard options={state.savedScanOptions} hrefs={state.hrefs} navigate={navigate} /> : null}
      {state.mode === "empty" ? <EmptyModeCard hrefs={state.hrefs} /> : null}
      {state.mode === "invalid" ? <InvalidModeCard hrefs={state.hrefs} /> : null}
      {state.mode === "context" && state.context ? (
        <ContextHero context={state.context} hrefs={state.hrefs} />
      ) : null}

      {showControls ? (
        <div className="advanced-diagnostics-body" id="scanWorkspaceAdvancedDiagnostics">
          <SafetyCallout />
          <div className="advanced-diagnostics-layout">
            <SectionNav activeSection={activeSection} />
            <div className="advanced-diagnostics-groups">
              {DIAGNOSTIC_GROUPS.map((group) => (
                <DiagnosticGroupCard
                  key={group.sectionId}
                  group={group}
                  controls={controls}
                  onCheckboxChange={handleCheckboxChange}
                  onTextChange={handleTextChange}
                  onSelectChange={handleSelectChange}
                />
              ))}
              <section
                className="advanced-diagnostics-card"
                data-tone="slate"
                id={READBACK_SECTION_ID}
                aria-labelledby={`${READBACK_SECTION_ID}Heading`}
              >
                <div className="advanced-diagnostics-card-heading">
                  <span className="advanced-diagnostics-card-icon-tile" aria-hidden="true">
                    <ClipboardCheck size={17} />
                  </span>
                  <div>
                    <h3 id={`${READBACK_SECTION_ID}Heading`}>Readback status</h3>
                    <p className="advanced-diagnostics-card-description">
                      Default-off feature/readback status for this scan context.
                    </p>
                  </div>
                </div>
                <div className="advanced-diagnostics-readbacks" aria-label="Advanced diagnostic readbacks">
                  {READBACK_ROWS.map((row) => (
                    <ReadbackRow key={row.id} row={row} />
                  ))}
                </div>
              </section>
            </div>
          </div>
          <ActionBar onClear={handleClearSelections} />
        </div>
      ) : null}
    </div>
  );
}
