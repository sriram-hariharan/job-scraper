import {
  Activity,
  Bot,
  Check,
  Clock3,
  ExternalLink,
  Minus,
  RefreshCw,
  ShieldCheck,
  TriangleAlert,
  Workflow,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import {
  readAgenticOperationsOverview,
  type AgenticOperationsCanonicalAgent,
  type AgenticOperationsCurrentPipeline,
  type AgenticOperationsOverviewPayload,
  type AgenticOperationsRecentRun,
  type AgenticOperationsSafetyMetadata,
  type AgenticOperationsSafetySummary,
} from "./agenticOperationsModel";

type LoadState =
  | { kind: "loading" }
  | { kind: "ready"; payload: AgenticOperationsOverviewPayload }
  | { kind: "error"; message: string };

type AgenticOperationsDashboardProps = {
  readOverview?: () => Promise<AgenticOperationsOverviewPayload>;
};

type CanonicalRegistryState = {
  agents: AgenticOperationsCanonicalAgent[];
  invalidCount: number;
  state: "available" | "empty" | "unavailable";
};

type MutationField = keyof Pick<
  AgenticOperationsCanonicalAgent,
  | "score_mutation"
  | "rank_mutation"
  | "queue_mutation"
  | "resume_text_mutation"
  | "operator_state_persistence"
  | "application_action_capability"
>;

const MUTATION_COLUMNS: {
  field: MutationField;
  label: string;
  summaryField: keyof AgenticOperationsSafetySummary;
}[] = [
  { field: "score_mutation", label: "Score", summaryField: "score_mutation_capable_count" },
  { field: "rank_mutation", label: "Rank", summaryField: "rank_mutation_capable_count" },
  { field: "queue_mutation", label: "Queue", summaryField: "queue_mutation_capable_count" },
  { field: "resume_text_mutation", label: "Resume text", summaryField: "resume_text_mutation_capable_count" },
  { field: "operator_state_persistence", label: "Operator state", summaryField: "operator_state_persistence_capable_count" },
  { field: "application_action_capability", label: "Application action", summaryField: "application_action_capable_count" },
];

const REQUIRED_FALSE_SAFETY_FIELDS: (keyof AgenticOperationsSafetyMetadata)[] = [
  "cross_user_access",
  "database_write_performed",
  "schema_write_performed",
  "provider_call_performed",
  "pipeline_execution_performed",
  "scheduler_mutation_performed",
  "scoring_changed",
  "ranking_changed",
  "queue_mutation_performed",
  "resume_mutation_performed",
  "application_execution_performed",
  "ats_submission_performed",
];

function clean(value: unknown): string {
  return String(value ?? "").trim();
}

function label(value: unknown, fallback = "Unavailable"): string {
  const raw = clean(value);
  if (!raw) return fallback;
  return raw
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase())
    .replace(/\bAi\b/g, "AI");
}

function countValue(value: unknown): string {
  return typeof value === "number" && Number.isFinite(value) ? String(value) : "Unavailable";
}

function canonicalRegistryState(value: unknown): CanonicalRegistryState {
  if (!Array.isArray(value)) return { agents: [], invalidCount: 0, state: "unavailable" };
  if (value.length === 0) return { agents: [], invalidCount: 0, state: "empty" };
  const agents = value.filter((entry): entry is AgenticOperationsCanonicalAgent => {
    if (!entry || typeof entry !== "object" || Array.isArray(entry)) return false;
    const agent = entry as AgenticOperationsCanonicalAgent;
    return Boolean(clean(agent.key) && clean(agent.display_name) && clean(agent.responsibility));
  });
  return {
    agents,
    invalidCount: value.length - agents.length,
    state: agents.length > 0 ? "available" : "unavailable",
  };
}

function registrySummaryMismatch(
  agents: AgenticOperationsCanonicalAgent[],
  summary: AgenticOperationsSafetySummary | undefined,
): boolean {
  if (!summary || agents.length === 0) return false;
  if (typeof summary.canonical_agent_count !== "number") return false;
  if (agents.some((agent) => MUTATION_COLUMNS.some(({ field }) => typeof agent[field] !== "boolean"))) return false;
  if (MUTATION_COLUMNS.some(({ summaryField }) => typeof summary[summaryField] !== "number")) return false;
  if (summary.canonical_agent_count !== agents.length) return true;
  return MUTATION_COLUMNS.some(({ field, summaryField }) => (
    summary[summaryField] !== agents.filter((agent) => agent[field] === true).length
  ));
}

const DATE_TIME_FORMATTER = new Intl.DateTimeFormat(undefined, {
  month: "short",
  day: "numeric",
  year: "numeric",
  hour: "numeric",
  minute: "2-digit",
});

function formatDateTime(value: unknown): string {
  const raw = clean(value);
  if (!raw) return "Unavailable";
  const parsed = new Date(raw);
  return Number.isNaN(parsed.getTime()) ? raw : DATE_TIME_FORMATTER.format(parsed);
}

function pipelineUnavailableCopy(state: unknown): string {
  if (state === "not_configured") return "No current pipeline status path is configured for the latest owner-scoped run.";
  if (state === "not_found") return "The current pipeline status artifact was not found.";
  if (state === "malformed") return "The current pipeline status artifact could not be read as valid status data.";
  return "Current pipeline status is unavailable.";
}

function pipelineStateLabel(pipeline: AgenticOperationsCurrentPipeline | undefined): string {
  if (!pipeline) return "Unavailable";
  return pipeline.available === true ? label(pipeline.status, "Unknown") : label(pipeline.state);
}

function safetyContractConfirmed(payload: AgenticOperationsOverviewPayload): boolean {
  const metadata = payload.safety_metadata;
  return Boolean(
    payload.read_only === true
      && payload.admin_only === true
      && metadata?.read_only === true
      && metadata.admin_only === true
      && REQUIRED_FALSE_SAFETY_FIELDS.every((field) => metadata[field] === false),
  );
}

function HeaderReadOnlyBadge({ confirmed }: { confirmed: boolean }) {
  const mount = document.getElementById("agenticOperationsHeaderReadOnlyBadge");
  if (!confirmed || !mount) return null;
  return createPortal(
    <span className="agentic-operations-header-badge app-page-header__badge">Read-only</span>,
    mount,
  );
}

function statusTone(status: unknown): string {
  const normalized = clean(status).toLowerCase();
  if (["succeeded", "complete", "completed", "available"].includes(normalized)) return "success";
  if (["failed", "error", "malformed"].includes(normalized)) return "danger";
  if (["running", "in_progress", "processing"].includes(normalized)) return "active";
  return "neutral";
}

function LoadingOverview() {
  return (
    <div className="agentic-operations-loading" role="status">
      <span className="agentic-operations-loading-icon" aria-hidden="true"><Activity size={20} /></span>
      <div>
        <strong>Loading operations overview…</strong>
        <span>Reading current pipeline, recent runs, and safety metadata.</span>
      </div>
    </div>
  );
}

function SummaryGrid({ payload }: { payload: AgenticOperationsOverviewPayload }) {
  const pipeline = payload.current_pipeline;
  const recentState = payload.recent_runs_state;
  const canonicalCount = payload.safety_summary?.canonical_agent_count;
  const metrics = [
    {
      icon: Activity,
      label: "Pipeline status",
      value: pipelineStateLabel(pipeline),
      detail: pipeline?.available === true ? "Current owner-scoped run" : "Status readback",
    },
    {
      icon: Workflow,
      label: "Current stage",
      value: pipeline?.available === true ? label(pipeline.current_stage) : "Unavailable",
      detail: pipeline?.available === true ? clean(pipeline.stage_message) || "No stage message recorded" : "No available current stage",
    },
    {
      icon: Clock3,
      label: "Recent runs",
      value: recentState?.available === true ? countValue(recentState.count) : "Unavailable",
      detail: recentState?.available === true ? `Bounded to ${countValue(recentState.bound)}` : "Owner-scoped history unavailable",
    },
    {
      icon: Bot,
      label: "Canonical agents",
      value: countValue(canonicalCount),
      detail: "Current registry count",
    },
  ];

  return (
    <section className="agentic-operations-summary-grid" aria-label="Agentic Operations summary">
      {metrics.map((metric) => {
        const Icon = metric.icon;
        return (
          <article className="agentic-operations-summary-card" key={metric.label}>
            <span className="agentic-operations-summary-icon" aria-hidden="true"><Icon size={17} /></span>
            <span className="agentic-operations-summary-label">{metric.label}</span>
            <strong>{metric.value}</strong>
            <span className="agentic-operations-summary-detail">{metric.detail}</span>
          </article>
        );
      })}
    </section>
  );
}

function CurrentPipelinePanel({ pipeline }: { pipeline: AgenticOperationsCurrentPipeline | undefined }) {
  if (pipeline?.available !== true) {
    const state = pipeline?.state || "unavailable";
    return (
      <section className="agentic-operations-card agentic-operations-current" aria-labelledby="agenticOperationsCurrentTitle">
        <div className="agentic-operations-section-heading">
          <div>
            <span className="agentic-operations-eyebrow">Runtime readback</span>
            <h2 id="agenticOperationsCurrentTitle">Current pipeline</h2>
          </div>
          <span className={`agentic-operations-status agentic-operations-status--${statusTone(state)}`}>{label(state)}</span>
        </div>
        <div className="agentic-operations-unavailable">
          <TriangleAlert size={20} aria-hidden="true" />
          <div><strong>{label(state)}</strong><p>{pipelineUnavailableCopy(state)}</p></div>
        </div>
      </section>
    );
  }

  const completed = Array.isArray(pipeline.completed_stages) ? pipeline.completed_stages.length : null;
  const total = Array.isArray(pipeline.stage_order) ? pipeline.stage_order.length : null;
  const hasProgress = completed !== null && total !== null && total > 0;
  const progress = hasProgress ? Math.min(100, Math.max(0, (completed / total) * 100)) : 0;
  const updatedAt = pipeline.updated_at_utc || pipeline.updated_at;

  return (
    <section className="agentic-operations-card agentic-operations-current" aria-labelledby="agenticOperationsCurrentTitle">
      <div className="agentic-operations-section-heading">
        <div>
          <span className="agentic-operations-eyebrow">Runtime readback</span>
          <h2 id="agenticOperationsCurrentTitle">Current pipeline</h2>
        </div>
        <span className={`agentic-operations-status agentic-operations-status--${statusTone(pipeline.status)}`}>{label(pipeline.status, "Unknown")}</span>
      </div>
      <div className="agentic-operations-stage-hero">
        <span className="agentic-operations-stage-icon" aria-hidden="true"><Workflow size={21} /></span>
        <div>
          <span>Current stage</span>
          <h3>{label(pipeline.current_stage)}</h3>
          <p>{clean(pipeline.stage_message) || "No stage message recorded."}</p>
        </div>
      </div>
      {hasProgress ? (
        <div className="agentic-operations-progress-block">
          <div><span>Recorded stage progress</span><strong>{completed} of {total}</strong></div>
          <div className="agentic-operations-progress-track" role="progressbar" aria-valuemin={0} aria-valuemax={total} aria-valuenow={completed}>
            <span style={{ width: `${progress}%` }} />
          </div>
        </div>
      ) : null}
      <dl className="agentic-operations-detail-grid">
        <div><dt>Run ID</dt><dd title={clean(pipeline.run_id)}>{clean(pipeline.run_id) || "Unavailable"}</dd></div>
        <div><dt>Stage started</dt><dd>{formatDateTime(pipeline.stage_started_at)}</dd></div>
        <div><dt>Updated</dt><dd>{formatDateTime(updatedAt)}</dd></div>
        <div><dt>Final job count</dt><dd>{countValue(pipeline.final_job_count)}</dd></div>
        <div><dt>Return code</dt><dd>{pipeline.return_code === null || pipeline.return_code === undefined || pipeline.return_code === "" ? "Unavailable" : String(pipeline.return_code)}</dd></div>
      </dl>
    </section>
  );
}

function runTime(run: AgenticOperationsRecentRun): string {
  return formatDateTime(run.completed_at || run.updated_at || run.started_at);
}

function RecentRunsPanel({
  payload,
  selectedRunId,
  onSelect,
}: {
  payload: AgenticOperationsOverviewPayload;
  selectedRunId: string | null;
  onSelect: (runId: string) => void;
}) {
  const state = payload.recent_runs_state;
  const runs = Array.isArray(payload.recent_runs) ? payload.recent_runs : [];
  return (
    <section className="agentic-operations-card agentic-operations-runs" aria-labelledby="agenticOperationsRunsTitle">
      <div className="agentic-operations-section-heading">
        <div>
          <span className="agentic-operations-eyebrow">Owner-scoped history</span>
          <h2 id="agenticOperationsRunsTitle">Recent pipeline runs</h2>
        </div>
        <span className="agentic-operations-section-meta">
          {state?.available === true ? `${countValue(state.count)} recorded` : "Unavailable"}
        </span>
      </div>
      {state?.available !== true ? (
        <div className="agentic-operations-unavailable agentic-operations-unavailable--compact">
          <Clock3 size={19} aria-hidden="true" />
          <div><strong>Recent runs unavailable</strong><p>Owner-scoped pipeline history could not be read.</p></div>
        </div>
      ) : runs.length === 0 ? (
        <div className="agentic-operations-empty"><Clock3 size={20} aria-hidden="true" /><strong>No recent runs recorded</strong></div>
      ) : (
        <div className="agentic-operations-run-list" role="list">
          {runs.map((run, index) => {
            const runId = clean(run.run_id);
            const selected = Boolean(runId && runId === selectedRunId);
            return (
              <article className={`agentic-operations-run-row${selected ? " is-selected" : ""}`} role="listitem" key={`${runId || "run"}-${index}`}>
                <div className="agentic-operations-run-primary">
                  <span className={`agentic-operations-status agentic-operations-status--${statusTone(run.status)}`}>{label(run.status, "Unknown")}</span>
                  <strong title={runId}>{runId || "Run ID unavailable"}</strong>
                  <span>{runTime(run)}</span>
                </div>
                <div className="agentic-operations-run-stage">
                  <span>{clean(run.current_stage) ? label(run.current_stage) : "Final stage unavailable"}</span>
                  <small>{clean(run.stage_message) || clean(run.summary_message) || "No run message recorded"}</small>
                </div>
                <div className="agentic-operations-run-count">
                  <span>Final jobs</span>
                  <strong>{countValue(run.final_job_count)}</strong>
                </div>
                <div className="agentic-operations-run-action">
                  {runId ? (
                    <input
                      type="button"
                      className="agentic-operations-inspect"
                      value={selected ? "Selected" : "Inspect"}
                      aria-label={`${selected ? "Selected" : "Inspect"} pipeline run ${runId}`}
                      aria-pressed={selected}
                      onClick={() => onSelect(runId)}
                    />
                  ) : <span>Inspection unavailable</span>}
                </div>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}

function SelectedRunInspector({ run }: { run: AgenticOperationsRecentRun | null }) {
  if (!run) {
    return (
      <section className="agentic-operations-card agentic-operations-inspector" aria-labelledby="agenticOperationsInspectorTitle">
        <div className="agentic-operations-section-heading">
          <div>
            <span className="agentic-operations-eyebrow">Recorded run summary</span>
            <h2 id="agenticOperationsInspectorTitle">Run Inspector</h2>
          </div>
        </div>
        <div className="agentic-operations-inspector-empty">
          <Clock3 size={20} aria-hidden="true" />
          <strong>Select a recent pipeline run to inspect its recorded summary.</strong>
        </div>
      </section>
    );
  }

  const runId = clean(run.run_id);
  const message = clean(run.stage_message) || clean(run.summary_message);
  const error = clean(run.error);
  const timestamp = clean(run.completed_at || run.updated_at || run.started_at);
  const stage = clean(run.current_stage);
  const hasFinalJobCount = typeof run.final_job_count === "number" && Number.isFinite(run.final_job_count);
  const hasReturnCode = run.return_code !== null && run.return_code !== undefined && run.return_code !== "";
  return (
    <section className="agentic-operations-card agentic-operations-inspector" aria-labelledby="agenticOperationsInspectorTitle">
      <div className="agentic-operations-section-heading">
        <div>
          <span className="agentic-operations-eyebrow">Recorded run summary</span>
          <h2 id="agenticOperationsInspectorTitle">Run Inspector</h2>
        </div>
        {clean(run.status) ? <span className={`agentic-operations-status agentic-operations-status--${statusTone(run.status)}`}>{label(run.status)}</span> : null}
      </div>
      <div className="agentic-operations-inspector-content">
        <dl className="agentic-operations-inspector-grid">
          <div><dt>Run ID</dt><dd title={runId}>{runId}</dd></div>
          {timestamp ? <div><dt>Recorded at</dt><dd>{runTime(run)}</dd></div> : null}
          {stage ? <div><dt>Current / final stage</dt><dd>{label(stage)}</dd></div> : null}
          {hasFinalJobCount ? <div><dt>Final job count</dt><dd>{String(run.final_job_count)}</dd></div> : null}
          {hasReturnCode ? <div><dt>Return code</dt><dd>{String(run.return_code)}</dd></div> : null}
        </dl>
        {message ? <p className="agentic-operations-inspector-message"><span>Recorded message</span>{message}</p> : null}
        {error ? <p className="agentic-operations-inspector-error"><span>Recorded error</span>{error}</p> : null}
        <a className="agentic-operations-review-link" href={`/profile/pipeline-runs/${encodeURIComponent(runId)}/agentic-review`}>
          Open Agentic Review <ExternalLink size={14} aria-hidden="true" />
        </a>
      </div>
    </section>
  );
}

function DeclarationChip({
  value,
  trueLabel,
  falseLabel,
  unavailableLabel,
}: {
  value: unknown;
  trueLabel: string;
  falseLabel: string;
  unavailableLabel: string;
}) {
  const state = value === true ? "yes" : value === false ? "no" : "unavailable";
  const text = state === "yes" ? trueLabel : state === "no" ? falseLabel : unavailableLabel;
  return (
    <span className={`agentic-operations-declaration agentic-operations-declaration--${state}`}>
      {state === "yes" ? <Check size={13} aria-hidden="true" /> : <Minus size={13} aria-hidden="true" />}
      <span>{text}</span>
    </span>
  );
}

function CanonicalAgentRegistry({ registry }: { registry: CanonicalRegistryState }) {
  return (
    <section className="agentic-operations-card agentic-operations-registry" aria-labelledby="agenticOperationsRegistryTitle">
      <div className="agentic-operations-section-heading">
        <div>
          <span className="agentic-operations-eyebrow">Declared capabilities</span>
          <h2 id="agenticOperationsRegistryTitle">Canonical Agent Registry</h2>
        </div>
        <span className="agentic-operations-section-meta">
          {registry.state === "available" ? `${registry.agents.length} registered` : "Unavailable"}
        </span>
      </div>
      {registry.state !== "available" ? (
        <div className="agentic-operations-registry-empty">
          <Bot size={20} aria-hidden="true" />
          <div>
            <strong>{registry.state === "empty" ? "No canonical agent definitions returned" : "Canonical registry unavailable"}</strong>
            <p>No canonical agents are fabricated when registry data is absent or malformed.</p>
          </div>
        </div>
      ) : (
        <>
          <div className="agentic-operations-agent-grid">
            {registry.agents.map((agent, index) => (
              <article className="agentic-operations-agent-card" key={`${clean(agent.key)}-${index}`}>
                <div className="agentic-operations-agent-heading">
                  <span className="agentic-operations-agent-icon" aria-hidden="true"><Bot size={17} /></span>
                  <div>
                    <span>Canonical definition</span>
                    <h3>{clean(agent.display_name)}</h3>
                  </div>
                </div>
                <p>{clean(agent.responsibility)}</p>
                <div className="agentic-operations-declarations" aria-label={`${clean(agent.display_name)} declared capabilities`}>
                  <DeclarationChip value={agent.deterministic_core} trueLabel="Deterministic core" falseLabel="Non-deterministic core" unavailableLabel="Deterministic core unavailable" />
                  <DeclarationChip value={agent.llm_capable} trueLabel="LLM capable" falseLabel="Not LLM capable" unavailableLabel="LLM capability unavailable" />
                  <DeclarationChip value={agent.optional_controlled_llm_guardrail} trueLabel="Controlled LLM guardrail available" falseLabel="Controlled LLM guardrail not available" unavailableLabel="Controlled LLM guardrail unavailable" />
                  <DeclarationChip value={agent.advisory_only} trueLabel="Advisory only" falseLabel="Not advisory-only" unavailableLabel="Advisory status unavailable" />
                  <DeclarationChip value={agent.human_approval_required} trueLabel="Human approval required" falseLabel="Human approval not required by definition" unavailableLabel="Human approval requirement unavailable" />
                </div>
              </article>
            ))}
          </div>
          {registry.invalidCount > 0 ? (
            <div className="agentic-operations-registry-note" role="status">
              <TriangleAlert size={16} aria-hidden="true" />
              {registry.invalidCount} malformed canonical {registry.invalidCount === 1 ? "definition was" : "definitions were"} not rendered.
            </div>
          ) : null}
        </>
      )}
    </section>
  );
}

function AuthorityValue({ value, label }: { value: unknown; label: string }) {
  const state = value === true ? "yes" : value === false ? "no" : "unavailable";
  const text = state === "yes" ? "Yes" : state === "no" ? "No" : "Unavailable";
  return (
    <span
      className={`agentic-operations-authority agentic-operations-authority--${state}`}
      aria-label={`${label}: ${text}`}
    >
      {state === "yes" ? <Check size={13} aria-hidden="true" /> : <Minus size={13} aria-hidden="true" />}
      <span>{text}</span>
    </span>
  );
}

function MutationAuthorityMatrix({
  registry,
  summary,
}: {
  registry: CanonicalRegistryState;
  summary: AgenticOperationsSafetySummary | undefined;
}) {
  const mismatch = registrySummaryMismatch(registry.agents, summary);
  return (
    <section className="agentic-operations-card agentic-operations-matrix" aria-labelledby="agenticOperationsMatrixTitle">
      <div className="agentic-operations-section-heading">
        <div>
          <span className="agentic-operations-eyebrow">Declared mutation authority</span>
          <h2 id="agenticOperationsMatrixTitle">Safety / Mutation Authority Matrix</h2>
        </div>
        <span className="agentic-operations-section-meta">Registry definitions</span>
      </div>
      {mismatch ? (
        <div className="agentic-operations-consistency-warning" role="status">
          <TriangleAlert size={17} aria-hidden="true" />
          <span>Registry capability totals do not match the returned safety summary.</span>
        </div>
      ) : null}
      {registry.state !== "available" ? (
        <div className="agentic-operations-registry-empty agentic-operations-registry-empty--compact">
          <ShieldCheck size={20} aria-hidden="true" />
          <div><strong>Mutation authority unavailable</strong><p>No authoritative per-agent rows were returned.</p></div>
        </div>
      ) : (
        <div className="agentic-operations-matrix-scroll">
          <table>
            <caption>Declared mutation authority by canonical agent</caption>
            <thead>
              <tr>
                <th scope="col">Canonical agent</th>
                {MUTATION_COLUMNS.map((column) => <th scope="col" key={column.field}>{column.label}</th>)}
              </tr>
            </thead>
            <tbody>
              {registry.agents.map((agent, index) => (
                <tr key={`${clean(agent.key)}-${index}`}>
                  <th scope="row">{clean(agent.display_name)}</th>
                  {MUTATION_COLUMNS.map((column) => (
                    <td key={column.field}><AuthorityValue value={agent[column.field]} label={column.label} /></td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

function SafetyOverview({
  payload,
  confirmed,
}: {
  payload: AgenticOperationsOverviewPayload;
  confirmed: boolean;
}) {
  const metadataPresent = Boolean(payload.safety_metadata);
  const summary = payload.safety_summary;
  const items = [
    ["Canonical agents", summary?.canonical_agent_count],
    ["Queue mutation capable", summary?.queue_mutation_capable_count],
    ["Resume mutation capable", summary?.resume_text_mutation_capable_count],
    ["Application-action capable", summary?.application_action_capable_count],
  ] as const;
  return (
    <section className={`agentic-operations-safety ${confirmed ? "is-confirmed" : "is-attention"}`} aria-labelledby="agenticOperationsSafetyTitle">
      <div className="agentic-operations-safety-copy">
        <span className="agentic-operations-safety-icon" aria-hidden="true">
          {confirmed ? <ShieldCheck size={21} /> : <TriangleAlert size={21} />}
        </span>
        <div>
          <span className="agentic-operations-eyebrow">Contract boundary</span>
          <div className="agentic-operations-safety-title-row">
            <h2 id="agenticOperationsSafetyTitle">Safety overview</h2>
          </div>
          <p>{confirmed
            ? "The returned contract confirms admin-only readback with no reported operational side effects."
            : metadataPresent
              ? "Safety metadata is inconsistent with the expected read-only contract."
              : "Safety metadata is unavailable; no read-only success claim is shown."}</p>
        </div>
      </div>
      <dl className="agentic-operations-safety-metrics">
        {items.map(([name, value]) => <div key={name}><dt>{name}</dt><dd>{countValue(value)}</dd></div>)}
      </dl>
    </section>
  );
}

export function AgenticOperationsDashboard({
  readOverview = readAgenticOperationsOverview,
}: AgenticOperationsDashboardProps) {
  const [state, setState] = useState<LoadState>({ kind: "loading" });
  const [refreshing, setRefreshing] = useState(false);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const inFlightRef = useRef<Promise<void> | null>(null);

  const refresh = useCallback((manual = false) => {
    if (inFlightRef.current) return inFlightRef.current;
    if (manual) setRefreshing(true);
    const request = readOverview()
      .then((payload) => setState({ kind: "ready", payload }))
      .catch((error) => setState({
        kind: "error",
        message: error instanceof Error ? error.message : "Agentic Operations overview is unavailable.",
      }))
      .finally(() => {
        inFlightRef.current = null;
        if (manual) setRefreshing(false);
      });
    inFlightRef.current = request;
    return request;
  }, [readOverview]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const recentRuns = state.kind === "ready" && Array.isArray(state.payload.recent_runs)
    ? state.payload.recent_runs
    : [];
  const selectedRun = selectedRunId
    ? recentRuns.find((run) => clean(run.run_id) === selectedRunId) || null
    : null;

  useEffect(() => {
    if (state.kind === "ready" && selectedRunId && !selectedRun) setSelectedRunId(null);
  }, [selectedRun, selectedRunId, state.kind]);

  const readOnlyConfirmed = state.kind === "ready" && safetyContractConfirmed(state.payload);
  const registry = state.kind === "ready" ? canonicalRegistryState(state.payload.canonical_agents) : null;

  return (
    <div className="agentic-operations-dashboard" aria-busy={state.kind === "loading" || refreshing}>
      <HeaderReadOnlyBadge confirmed={readOnlyConfirmed} />
      <div className="agentic-operations-toolbar">
        <div>
          <span className="agentic-operations-eyebrow">Operations overview</span>
          <p>Live readback for the current owner-scoped pipeline and canonical agent safety boundary.</p>
        </div>
        <button
          type="button"
          className="agentic-operations-refresh"
          onClick={() => void refresh(true)}
          disabled={refreshing || state.kind === "loading"}
        >
          <RefreshCw size={15} aria-hidden="true" className={refreshing ? "is-spinning" : ""} />
          {refreshing ? "Refreshing…" : "Refresh overview"}
        </button>
      </div>

      {state.kind === "loading" ? <LoadingOverview /> : null}
      {state.kind === "error" ? (
        <div className="agentic-operations-error" role="alert">
          <TriangleAlert size={20} aria-hidden="true" />
          <div><strong>Overview unavailable</strong><p>{state.message}</p></div>
        </div>
      ) : null}
      {state.kind === "ready" && registry ? (
        <>
          <SummaryGrid payload={state.payload} />
          <div className="agentic-operations-primary-grid">
            <CurrentPipelinePanel pipeline={state.payload.current_pipeline} />
            <RecentRunsPanel payload={state.payload} selectedRunId={selectedRunId} onSelect={setSelectedRunId} />
          </div>
          <SelectedRunInspector run={selectedRun} />
          <SafetyOverview payload={state.payload} confirmed={readOnlyConfirmed} />
          <CanonicalAgentRegistry registry={registry} />
          <MutationAuthorityMatrix registry={registry} summary={state.payload.safety_summary} />
        </>
      ) : null}
    </div>
  );
}
