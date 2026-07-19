import {
  Activity,
  AlertTriangle,
  Check,
  Circle,
  Clock3,
  Database,
  Play,
  RefreshCw,
  Settings2,
  ShieldCheck,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  COUNT_GROUPS,
  displayStatus,
  elapsedLabel,
  explicitUpdatedAt,
  FLOW_STAGES,
  formatCount,
  formatDateTime,
  isStatusStale,
  numericCount,
  PIPELINE_POLL_INTERVAL_MS,
  type PipelineRecord,
  type PipelineStatusResponse,
  stageOrder,
  STAGE_LABELS,
} from "./pipelineModel";

/**
 * Adapted from Live Sales Dashboard by vaib215.
 * Source: https://21st.dev/community/components/vaib215/live-sales-dashboard/default
 * Adopted 2026-07-18. ApplyLens adaptations replace sales KPIs and demo series
 * with owner-scoped pipeline status, canonical stages, real run counts, safe
 * configuration readback, and an honest source-health unavailable state.
 */

type PipelineDashboardProps = {
  readStatus?: () => Promise<PipelineStatusResponse>;
  launchPipeline?: () => void;
  pollIntervalMs?: number;
};

type LoadState =
  | { kind: "loading" }
  | { kind: "ready"; payload: PipelineStatusResponse; checkedAt: number }
  | { kind: "error"; message: string };

type StageState = "complete" | "active" | "pending" | "failed";

export const PIPELINE_ACCEPTED_RUN_EVENT_NAME = "applylens:pipeline-run-accepted";
export const PIPELINE_ACCEPTED_RUN_STORAGE_KEY = "applylens_pipeline_accepted_run_id";

declare global {
  interface Window {
    openApplyLensPipelineConfig?: () => void;
  }
}

const SAFE_CONFIG_FIELDS = [
  ["job_limit", "Job limit"],
  ["job_packet_limit", "Packet limit"],
  ["planning_only", "Planning only"],
  ["generate_tailoring", "Generate tailoring"],
  ["generate_llm_tailoring", "AI tailoring"],
  ["refresh_llm_tailoring", "Refresh AI cache"],
  ["generate_llm_fallback", "Backup ranking"],
  ["generate_llm_adjudication", "AI review"],
  ["delete_seen_data", "Rerun seen jobs"],
] as const;

function titleForStage(stage: string): string {
  return STAGE_LABELS[stage] || stage.replace(/_/g, " ").replace(/\b\w/g, (character: string) => character.toUpperCase());
}

function statusLabel(status: ReturnType<typeof displayStatus>): string {
  return status === "unavailable" ? "Unavailable" : status.charAt(0).toUpperCase() + status.slice(1);
}

function stageState(pipeline: PipelineRecord, stage: string, status: ReturnType<typeof displayStatus>): StageState {
  const completed = new Set(Array.isArray(pipeline.completed_stages) ? pipeline.completed_stages : []);
  if (completed.has(stage)) return "complete";
  if (stage === pipeline.current_stage && status === "failed") return "failed";
  if (stage === pipeline.current_stage && (status === "running" || status === "starting")) return "active";
  return "pending";
}

function safeConfigValue(value: unknown): string {
  if (typeof value === "boolean") return value ? "Enabled" : "Disabled";
  if (typeof value === "number" && Number.isFinite(value)) return formatCount(value);
  if (typeof value === "string") {
    const normalized = value.trim();
    if (!normalized) return "";
    if (normalized.toLowerCase() === "yes") return "Enabled";
    if (normalized.toLowerCase() === "no") return "Disabled";
    return normalized;
  }
  return "";
}

export async function readPipelineStatus(): Promise<PipelineStatusResponse> {
  const response = await fetch("/pipeline/status", {
    method: "GET",
    credentials: "same-origin",
    headers: { Accept: "application/json" },
  });
  if (!response.ok) throw new Error(`Pipeline status request failed (${response.status})`);
  return response.json() as Promise<PipelineStatusResponse>;
}

export function openExistingPipelineLaunch(): void {
  if (typeof window.openApplyLensPipelineConfig === "function") {
    window.openApplyLensPipelineConfig();
    return;
  }
  console.error("The reviewed Pipeline launch flow is unavailable on this page.");
}

function acceptedRunIdFromStorage(): string {
  try {
    return String(window.sessionStorage.getItem(PIPELINE_ACCEPTED_RUN_STORAGE_KEY) || "").trim();
  } catch {
    return "";
  }
}

function clearAcceptedRunId(runId: string): void {
  try {
    if (window.sessionStorage.getItem(PIPELINE_ACCEPTED_RUN_STORAGE_KEY) === runId) {
      window.sessionStorage.removeItem(PIPELINE_ACCEPTED_RUN_STORAGE_KEY);
    }
  } catch {
    // Storage is only a navigation handoff; the owner-scoped status remains canonical.
  }
}

function acceptedRunPlaceholder(runId: string, pipeline: PipelineRecord = {}): PipelineStatusResponse {
  return {
    pipeline: {
      ...pipeline,
      status: pipeline.status || "starting",
      run_id: runId || pipeline.run_id,
      current_stage: pipeline.current_stage || "startup",
      stage_message: pipeline.stage_message || "Synchronizing the accepted pipeline run.",
    },
  };
}

function LoadingDashboard() {
  return (
    <div className="pipeline-dashboard pipeline-dashboard--loading" aria-busy="true" aria-label="Loading pipeline status">
      <div className="pipeline-dashboard-skeleton pipeline-dashboard-skeleton--header" />
      <div className="pipeline-dashboard-top-grid">
        <div className="pipeline-dashboard-skeleton pipeline-dashboard-skeleton--summary" />
        <div className="pipeline-dashboard-skeleton pipeline-dashboard-skeleton--stage" />
      </div>
      <div className="pipeline-dashboard-skeleton pipeline-dashboard-skeleton--counts" />
    </div>
  );
}

function DashboardHeader({
  onRefresh,
  onRun,
  refreshing,
  runActive,
}: {
  onRefresh: () => void;
  onRun: () => void;
  refreshing: boolean;
  runActive: boolean;
}) {
  return (
    <header className="pipeline-dashboard-header">
      <div>
        <p className="pipeline-dashboard-eyebrow">Operations</p>
        <h1>Pipeline</h1>
        <p>Monitor job collection, filtering, evaluation, resume matching, and planning.</p>
      </div>
      <div className="pipeline-dashboard-actions">
        <button className="pipeline-dashboard-btn pipeline-dashboard-btn--secondary" type="button" onClick={onRefresh} disabled={refreshing}>
          <RefreshCw size={17} aria-hidden="true" />
          {refreshing ? "Refreshing" : "Refresh Status"}
        </button>
        <button className="pipeline-dashboard-btn pipeline-dashboard-btn--primary" type="button" onClick={onRun} disabled={runActive}>
          {runActive ? <Activity size={17} aria-hidden="true" /> : <Play size={17} aria-hidden="true" />}
          {runActive ? "Pipeline Running..." : "Run Pipeline"}
        </button>
      </div>
    </header>
  );
}

function StatusSummary({ pipeline, checkedAt }: { pipeline: PipelineRecord; checkedAt: number }) {
  const status = displayStatus(pipeline.status);
  const runActive = status === "starting" || status === "running";
  const order = stageOrder(pipeline);
  const completed = new Set(Array.isArray(pipeline.completed_stages) ? pipeline.completed_stages : []);
  const completedCount = order.filter((stage) => completed.has(stage)).length;
  const progressValue = order.length ? Math.min(completedCount, order.length) : 0;
  const rawStage = String(pipeline.current_stage || "").trim();
  const hasKnownStage = Boolean(rawStage) && rawStage.toLowerCase() !== "unknown";
  const currentStage = hasKnownStage
    ? titleForStage(rawStage)
    : status === "failed" ? "Pipeline failed" : "Not active";
  const elapsed = elapsedLabel(pipeline.started_at, pipeline.finished_at, checkedAt);
  const updatedAt = explicitUpdatedAt(pipeline);
  const stale = isStatusStale(pipeline, checkedAt);
  const summary = status === "failed"
    ? (pipeline.error || pipeline.summary_message || pipeline.stage_message || "The latest pipeline run did not complete.")
    : pipeline.summary_message || pipeline.stage_message || (
      status === "idle" ? "No pipeline run is active." :
        status === "succeeded" ? "The latest pipeline run completed successfully." :
          "Waiting for pipeline status details."
    );
  const details = [
    ["Run ID", pipeline.run_id],
    ["Started", formatDateTime(pipeline.started_at)],
    ["Last updated", formatDateTime(updatedAt)],
    ["Completed", formatDateTime(pipeline.finished_at)],
    ["Elapsed", elapsed],
    ["Return code", pipeline.return_code === null || pipeline.return_code === undefined ? "" : String(pipeline.return_code)],
  ].filter((entry): entry is [string, string] => Boolean(entry[1]));

  return (
    <section
      className={`pipeline-panel pipeline-run-summary pipeline-run-summary--${status}`}
      aria-labelledby="pipeline-current-run-title"
      aria-busy={runActive}
    >
      <div className="pipeline-panel-heading">
        <div>
          <p className="pipeline-panel-kicker">Current run</p>
          <h2 id="pipeline-current-run-title">{currentStage}</h2>
        </div>
        <span className={`pipeline-status-badge pipeline-status-badge--${status}`} role="status">
          <span aria-hidden="true" />{statusLabel(status)}
        </span>
      </div>
      <p className="pipeline-run-message">{summary}</p>
      {runActive ? (
        <div className="pipeline-running-indicator" role="status">
          <span className="pipeline-running-indicator__spinner" aria-hidden="true" />
          <span><strong>Live run in progress</strong>{pipeline.stage_message || "Waiting for the next pipeline update."}</span>
        </div>
      ) : null}
      {stale ? (
        <div className="pipeline-stale-notice" role="status">
          <AlertTriangle size={16} aria-hidden="true" /> Status may be stale. The backend still reports this run as running.
        </div>
      ) : null}
      <div className="pipeline-stage-progress-copy">
        <span>{completedCount} of {order.length} stages complete</span>
        {pipeline.stage_message ? <strong>{pipeline.stage_message}</strong> : null}
      </div>
      <progress className="pipeline-stage-progress" max={order.length || 1} value={progressValue} aria-label={`${completedCount} of ${order.length} pipeline stages complete`} />
      {runActive ? <div className="pipeline-running-strip" aria-hidden="true"><span /></div> : null}
      {details.length ? (
        <dl className="pipeline-run-details">
          {details.map(([label, value]) => (
            <div key={label}><dt>{label}</dt><dd>{value}</dd></div>
          ))}
        </dl>
      ) : null}
      {pipeline.final_job_count !== null && pipeline.final_job_count !== undefined ? (
        <div className="pipeline-final-count">
          <Database size={18} aria-hidden="true" />
          <span>Final jobs</span>
          <strong>{formatCount(Number(pipeline.final_job_count))}</strong>
        </div>
      ) : null}
    </section>
  );
}

function StageTimeline({ pipeline }: { pipeline: PipelineRecord }) {
  const status = displayStatus(pipeline.status);
  return (
    <section className="pipeline-panel pipeline-stage-panel" aria-labelledby="pipeline-stage-title">
      <div className="pipeline-panel-heading">
        <div>
          <p className="pipeline-panel-kicker">Stage progress</p>
          <h2 id="pipeline-stage-title">Execution timeline</h2>
        </div>
        <Activity size={20} aria-hidden="true" />
      </div>
      <ol className="pipeline-stage-list" aria-label="Pipeline stages">
        {stageOrder(pipeline).map((stage, index) => {
          const state = stageState(pipeline, stage, status);
          return (
            <li
              className={`pipeline-stage pipeline-stage--${state}`}
              key={stage}
              aria-current={state === "active" ? "step" : undefined}
              data-stage-index={index + 1}
            >
              <span className="pipeline-stage-marker" aria-hidden="true">
                {state === "complete" ? <Check size={13} /> : state === "failed" ? <AlertTriangle size={13} /> : <Circle size={9} />}
              </span>
              <span className="pipeline-stage-name" title={titleForStage(stage)}><span aria-hidden="true">{String(index + 1).padStart(2, "0")}</span>{titleForStage(stage)}</span>
              <small>{state === "complete" ? "Complete" : state === "active" ? "Active" : state === "failed" ? "Failed" : "Pending"}</small>
            </li>
          );
        })}
      </ol>
    </section>
  );
}

function LiveCounts({ pipeline }: { pipeline: PipelineRecord }) {
  const counts = pipeline.counts || {};
  const renderedGroups = COUNT_GROUPS.map((group) => ({
    label: group.label,
    values: group.keys.flatMap(([key, label]) => {
      const value = numericCount(counts[key]);
      if (value === null) {
        if (counts[key] !== undefined && counts[key] !== null) console.warn(`Ignoring malformed pipeline count: ${key}`);
        return [];
      }
      return [{ key, label, value }];
    }),
  })).filter((group) => group.values.length);

  return (
    <section className="pipeline-section" aria-labelledby="pipeline-counts-title">
      <div className="pipeline-section-heading">
        <div><p className="pipeline-panel-kicker">Live counts</p><h2 id="pipeline-counts-title">Jobs through the pipeline</h2></div>
        <span>Only recorded values are shown</span>
      </div>
      {renderedGroups.length ? (
        <div className="pipeline-count-groups">
          {renderedGroups.map((group) => (
            <section className="pipeline-count-group" key={group.label} aria-label={group.label}>
              <h3>{group.label}</h3>
              <div className="pipeline-count-grid">
                {group.values.map((item) => (
                  <article className="pipeline-count-card" key={item.key}>
                    <span>{item.label}</span><strong>{formatCount(item.value)}</strong>
                  </article>
                ))}
              </div>
            </section>
          ))}
        </div>
      ) : <div className="pipeline-empty-panel pipeline-empty-panel--compact">Stage counts are not available for this run yet.</div>}
    </section>
  );
}

function PipelineFlow({ pipeline }: { pipeline: PipelineRecord }) {
  const counts = pipeline.counts || {};
  const points = FLOW_STAGES.flatMap(([key, label]) => {
    const fallback = key === "final_jobs" ? pipeline.final_job_count : undefined;
    const value = numericCount(counts[key] ?? fallback);
    return value === null ? [] : [{ key, label, value }];
  });
  const maximum = Math.max(...points.map((point) => point.value), 0);

  return (
    <section className={`pipeline-panel pipeline-flow-panel${points.length ? "" : " pipeline-flow-panel--empty"}`} aria-labelledby="pipeline-flow-title">
      <div className="pipeline-panel-heading">
        <div><p className="pipeline-panel-kicker">Pipeline flow</p><h2 id="pipeline-flow-title">Current-run volume</h2></div>
        <span className="pipeline-panel-note">Relative to the largest recorded stage</span>
      </div>
      {points.length ? (
        <div className="pipeline-flow" role="img" aria-label={points.map((point) => `${point.label}: ${formatCount(point.value)}`).join(", ")}>
          {points.map((point, index) => {
            const width = maximum > 0 ? Math.max((point.value / maximum) * 100, point.value > 0 ? 3 : 0) : 0;
            return (
              <div className="pipeline-flow-step" key={point.key}>
                <div className="pipeline-flow-meta"><span>{point.label}</span><strong>{formatCount(point.value)}</strong></div>
                <div className="pipeline-flow-track" aria-hidden="true"><span style={{ width: `${width}%` }} /></div>
                {index < points.length - 1 ? <span className="pipeline-flow-connector" aria-hidden="true" /> : null}
              </div>
            );
          })}
        </div>
      ) : <div className="pipeline-empty-panel pipeline-empty-panel--compact">Flow data will appear when the run records stage counts.</div>}
    </section>
  );
}

function ConfigurationSummary({ pipeline }: { pipeline: PipelineRecord }) {
  const config = pipeline.config || {};
  const values = SAFE_CONFIG_FIELDS.flatMap(([key, label]) => {
    const value = safeConfigValue(config[key]);
    return value ? [{ key, label, value }] : [];
  });
  return (
    <section className="pipeline-panel pipeline-compact-panel" aria-labelledby="pipeline-config-title">
      <div className="pipeline-panel-heading">
        <div><p className="pipeline-panel-kicker">Run configuration</p><h2 id="pipeline-config-title">Safe settings snapshot</h2></div>
        <Settings2 size={20} aria-hidden="true" />
      </div>
      {values.length ? (
        <dl className="pipeline-config-list">
          {values.map((item) => <div key={item.key}><dt>{item.label}</dt><dd>{item.value}</dd></div>)}
        </dl>
      ) : <div className="pipeline-empty-panel">No safe configuration fields were recorded for this run.</div>}
    </section>
  );
}

function SourceHealth({ pipeline }: { pipeline: PipelineRecord }) {
  const health = Array.isArray(pipeline.source_health)
    ? pipeline.source_health.filter((item) => item && typeof item.source === "string" && item.source.trim())
    : [];
  return (
    <section className="pipeline-panel pipeline-compact-panel" aria-labelledby="pipeline-health-title">
      <div className="pipeline-panel-heading">
        <div><p className="pipeline-panel-kicker">Source health</p><h2 id="pipeline-health-title">Collection evidence</h2></div>
        <ShieldCheck size={20} aria-hidden="true" />
      </div>
      {health.length ? (
        <ul className="pipeline-health-list">
          {health.map((item) => (
            <li key={item.source}>
              <div><strong>{item.source}</strong><span>{item.status || "Status unavailable"}</span></div>
              {numericCount(item.jobs_returned) !== null ? <span>{formatCount(Number(item.jobs_returned))} jobs</span> : null}
              {item.last_success ? <time dateTime={item.last_success}>{formatDateTime(item.last_success)}</time> : null}
            </li>
          ))}
        </ul>
      ) : (
        <div className="pipeline-source-unavailable" role="status">
          <ShieldCheck size={18} aria-hidden="true" />
          <div><strong>Source health data is not available yet</strong><span>No source status is inferred from missing job counts.</span></div>
        </div>
      )}
    </section>
  );
}

export function PipelineDashboard({
  readStatus = readPipelineStatus,
  launchPipeline = openExistingPipelineLaunch,
  pollIntervalMs = PIPELINE_POLL_INTERVAL_MS,
}: PipelineDashboardProps) {
  const initialAcceptedRunId = acceptedRunIdFromStorage();
  const acceptedRunIdRef = useRef(initialAcceptedRunId);
  const [state, setState] = useState<LoadState>(() => initialAcceptedRunId
    ? { kind: "ready", payload: acceptedRunPlaceholder(initialAcceptedRunId), checkedAt: Date.now() }
    : { kind: "loading" });
  const [refreshing, setRefreshing] = useState(false);

  const refresh = useCallback(async (showLoading = false) => {
    if (showLoading) setRefreshing(true);
    try {
      const payload = await readStatus();
      const acceptedRunId = acceptedRunIdRef.current;
      const statusRunId = String(payload.pipeline?.run_id || "").trim();
      if (acceptedRunId && statusRunId !== acceptedRunId) {
        setState({ kind: "ready", payload: acceptedRunPlaceholder(acceptedRunId), checkedAt: Date.now() });
        return;
      }
      if (acceptedRunId && statusRunId === acceptedRunId) {
        acceptedRunIdRef.current = "";
        clearAcceptedRunId(acceptedRunId);
      }
      setState({ kind: "ready", payload, checkedAt: Date.now() });
      const rawStatus = payload.pipeline?.status;
      if (displayStatus(rawStatus) === "unavailable") console.warn(`Unsupported pipeline status: ${String(rawStatus || "")}`);
    } catch (error) {
      console.error("Failed to read Pipeline page status", error);
      setState({ kind: "error", message: error instanceof Error ? error.message : "Pipeline status is unavailable." });
    } finally {
      if (showLoading) setRefreshing(false);
    }
  }, [readStatus]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  useEffect(() => {
    const handleAcceptedRun = (event: Event) => {
      const detail = (event as CustomEvent<{ runId?: string; pipeline?: PipelineRecord }>).detail || {};
      const runId = String(detail.runId || detail.pipeline?.run_id || "").trim();
      if (!runId) return;
      acceptedRunIdRef.current = runId;
      setState({ kind: "ready", payload: acceptedRunPlaceholder(runId, detail.pipeline), checkedAt: Date.now() });
      void refresh();
    };
    window.addEventListener(PIPELINE_ACCEPTED_RUN_EVENT_NAME, handleAcceptedRun);
    return () => window.removeEventListener(PIPELINE_ACCEPTED_RUN_EVENT_NAME, handleAcceptedRun);
  }, [refresh]);

  const pipeline = state.kind === "ready" ? (state.payload.pipeline || {}) : {};
  const status = displayStatus(pipeline.status);
  const shouldPoll = state.kind === "ready" && (status === "starting" || status === "running");

  useEffect(() => {
    if (!shouldPoll) return undefined;
    const timer = window.setInterval(() => void refresh(), pollIntervalMs);
    return () => window.clearInterval(timer);
  }, [pollIntervalMs, refresh, shouldPoll]);

  const checkedAt = state.kind === "ready" ? state.checkedAt : Date.now();
  const pageClassName = useMemo(() => `pipeline-dashboard pipeline-dashboard--${status}`, [status]);

  if (state.kind === "loading") return <LoadingDashboard />;

  if (state.kind === "error") {
    return (
      <div className="pipeline-dashboard pipeline-dashboard--error">
        <DashboardHeader onRefresh={() => void refresh(true)} onRun={launchPipeline} refreshing={refreshing} runActive={false} />
        <section className="pipeline-status-error" role="alert">
          <AlertTriangle size={22} aria-hidden="true" />
          <div><h2>Pipeline status is unavailable</h2><p>{state.message}</p></div>
          <button type="button" onClick={() => void refresh(true)}>Retry</button>
        </section>
      </div>
    );
  }

  return (
    <div className={pageClassName} data-theme-surface="pipeline" aria-busy={shouldPoll}>
      <DashboardHeader
        onRefresh={() => void refresh(true)}
        onRun={launchPipeline}
        refreshing={refreshing}
        runActive={status === "starting" || status === "running"}
      />
      {status === "idle" ? (
        <section className="pipeline-idle-banner" role="status">
          <Clock3 size={20} aria-hidden="true" />
          <div><strong>Pipeline is idle</strong><span>Start a run through the existing reviewed launch flow.</span></div>
        </section>
      ) : null}
      <div className="pipeline-dashboard-top-grid">
        <StatusSummary pipeline={pipeline} checkedAt={checkedAt} />
        <StageTimeline pipeline={pipeline} />
      </div>
      <LiveCounts pipeline={pipeline} />
      <PipelineFlow pipeline={pipeline} />
      <div className="pipeline-dashboard-bottom-grid">
        <ConfigurationSummary pipeline={pipeline} />
        <SourceHealth pipeline={pipeline} />
      </div>
    </div>
  );
}
