import {
  Activity,
  Bot,
  Clock3,
  RefreshCw,
  ShieldCheck,
  TriangleAlert,
  Workflow,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import {
  readAgenticOperationsOverview,
  type AgenticOperationsCurrentPipeline,
  type AgenticOperationsOverviewPayload,
  type AgenticOperationsRecentRun,
  type AgenticOperationsSafetyMetadata,
} from "./agenticOperationsModel";

type LoadState =
  | { kind: "loading" }
  | { kind: "ready"; payload: AgenticOperationsOverviewPayload }
  | { kind: "error"; message: string };

type AgenticOperationsDashboardProps = {
  readOverview?: () => Promise<AgenticOperationsOverviewPayload>;
};

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

function RecentRunsPanel({ payload }: { payload: AgenticOperationsOverviewPayload }) {
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
          {runs.map((run, index) => (
            <article className="agentic-operations-run-row" role="listitem" key={`${clean(run.run_id) || "run"}-${index}`}>
              <div className="agentic-operations-run-primary">
                <span className={`agentic-operations-status agentic-operations-status--${statusTone(run.status)}`}>{label(run.status, "Unknown")}</span>
                <strong title={clean(run.run_id)}>{clean(run.run_id) || "Run ID unavailable"}</strong>
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
            </article>
          ))}
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

  const readOnlyConfirmed = state.kind === "ready" && safetyContractConfirmed(state.payload);

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
      {state.kind === "ready" ? (
        <>
          <SummaryGrid payload={state.payload} />
          <div className="agentic-operations-primary-grid">
            <CurrentPipelinePanel pipeline={state.payload.current_pipeline} />
            <RecentRunsPanel payload={state.payload} />
          </div>
          <SafetyOverview payload={state.payload} confirmed={readOnlyConfirmed} />
        </>
      ) : null}
    </div>
  );
}
