import {
  type ColumnDef,
  type SortingState,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import {
  AlertTriangle,
  Activity,
  CheckCircle2,
  CircleCheck,
  Clock,
  Database,
  FileSearch,
  Play,
  Power,
  RefreshCw,
  ShieldCheck,
  X,
  XCircle,
} from "lucide-react";
import {
  type KeyboardEvent,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { SharedFilterSelect, type SharedFilterOption } from "../filter/FilterSelect";
import {
  SHARED_NEUTRAL_CONTROL_CLASS,
  SharedTableCard,
  type SharedPaginationState,
} from "../table/TablePrimitives";
import {
  clean,
  formatCadence,
  formatClockTime,
  formatDateTime,
  isFailedStatus,
  readAgentDiscoveryRunSummary,
  readSchedulerSummary,
  runAgentDiscoveryNow,
  runRowKey,
  schedulerNextRunPresentation,
  schedulerTriggerLabel,
  shown,
  sortJobStatusRows,
  statusSlug,
  type SchedulerRun,
  type SchedulerRuntimeJob,
  type SchedulerSummaryPayload,
  type ManualAgentDiscoveryResponse,
  type AgentDiscoveryRunSummary,
  AgentDiscoverySummaryUnavailableError,
} from "./schedulerModel";

/**
 * Layout inspired by reui's card-container data-grid table, hextaui's system
 * status block, and isaiahbjork's dashboard-card-with-modal (21st.dev). This
 * component is the sole owner of the /scheduler/summary request — it fetches
 * its own data (mirroring PipelineDashboard's self-fetch pattern) rather than
 * relying on a classic-JS controller, so there is exactly one request owner.
 */

type LoadState =
  | { kind: "loading" }
  | { kind: "ready"; payload: SchedulerSummaryPayload; checkedAt: number }
  | { kind: "error"; message: string };

type RunsTab = "job_status" | "run_history";

type SchedulerHealthDashboardProps = {
  readSummary?: () => Promise<SchedulerSummaryPayload>;
  runDiscoveryNow?: () => Promise<ManualAgentDiscoveryResponse>;
  readDiscoverySummary?: (runId: string) => Promise<AgentDiscoveryRunSummary>;
};

type DiscoverySummaryLoadState =
  | { kind: "loading" }
  | { kind: "ready"; summary: AgentDiscoveryRunSummary }
  | { kind: "unavailable" }
  | { kind: "error"; message: string };

function schedulerBadge(status: unknown) {
  const label = shown(status, "Unknown");
  const tone = statusSlug(status);
  return <span className={`scheduler-badge scheduler-badge--${tone}`}>{label}</span>;
}

function jobDisplayName(jobName: unknown) {
  return clean(jobName)
    .split("_")
    .filter(Boolean)
    .map((part) => `${part.charAt(0).toUpperCase()}${part.slice(1)}`)
    .join(" ") || "Unnamed job";
}

function runtimeLabel(job: SchedulerRuntimeJob) {
  if (job.manual_run_active === true) return "Running";
  if (job.runtime_state === "not_installed") return "Not installed";
  if (job.runtime_state === "unloaded") return "Unloaded";
  if (job.runtime_state === "unavailable") return "Unavailable";
  if (job.runtime_state === "running") return "Running";
  return "Idle";
}

function armedLabel(job: SchedulerRuntimeJob) {
  if (job.armed === true) return "Armed";
  if (job.enabled === false) return "Disabled";
  if (job.loaded === false) return "Unloaded";
  return "Armed unknown";
}

function runtimeTone(job: SchedulerRuntimeJob) {
  if (job.manual_run_active === true) return "running";
  if (job.runtime_state === "running") return "running";
  if (job.runtime_state === "idle" && job.armed === true) return "succeeded";
  if (job.runtime_state === "unavailable" || job.armed === null) return "unknown";
  return "failed";
}

function truthLabel(value: boolean | null) {
  if (value === true) return "Yes";
  if (value === false) return "No";
  return "Unknown";
}

function manualDiscoveryEligibility(job: SchedulerRuntimeJob) {
  if (job.manual_run_active === true) {
    return { enabled: false, reason: "Agent Discovery is already running." };
  }
  if (job.running === true || job.runtime_state === "running") {
    return { enabled: false, reason: "Scheduled Agent Discovery is already running." };
  }
  const enabled = (
    job.installed === true
    && job.loaded === true
    && job.enabled === true
    && job.armed === true
    && job.running === false
    && job.runtime_state === "idle"
  );
  return {
    enabled,
    reason: enabled
      ? "Run Agent Discovery once without changing its schedule."
      : "Agent Discovery is unavailable until its scheduler is installed, loaded, enabled, armed, and idle.",
  };
}

function DashboardHeader({
  onRefresh,
  refreshing,
  lastRefreshedAt,
}: {
  onRefresh: () => void;
  refreshing: boolean;
  lastRefreshedAt: number | null;
}) {
  return (
    <header className="scheduler-health-header app-page-header">
      <div className="scheduler-health-header-copy app-page-header__main">
        <div className="scheduler-health-title-row app-page-header__title-row">
          <h1 className="app-page-header__title">Scheduler Health</h1>
          <span className="scheduler-badge scheduler-badge--muted scheduler-admin-badge app-page-header__badge">Admin only</span>
        </div>
        <p className="app-page-header__description">Monitor scheduled jobs, run outcomes, persistence consistency, and configuration integrity.</p>
      </div>
      <div className="scheduler-health-header-actions app-page-header__actions">
        <span className="scheduler-last-refreshed">
          {lastRefreshedAt ? `Last refreshed at ${formatClockTime(new Date(lastRefreshedAt))}` : "Not refreshed yet"}
        </span>
        <button
          type="button"
          className="scheduler-refresh-btn"
          onClick={onRefresh}
          disabled={refreshing}
          aria-label="Refresh scheduler health"
        >
          <RefreshCw size={15} aria-hidden="true" className={refreshing ? "is-spinning" : ""} />
          Refresh
        </button>
      </div>
    </header>
  );
}

function OverviewPanel({
  payload,
  loading,
  onOpenDiagnostics,
  diagnosticsTriggerRef,
}: {
  payload: SchedulerSummaryPayload | null;
  loading: boolean;
  onOpenDiagnostics: () => void;
  diagnosticsTriggerRef: React.RefObject<HTMLButtonElement>;
}) {
  const contractOk = Boolean(payload?.contract_health?.all_checks_pass);
  const runtimeJobs = payload?.runtime_jobs || [];
  const runtimeTruthKnown = runtimeJobs.length === 2 && runtimeJobs.every((job) => (
    job.installed !== null
    && job.loaded !== null
    && job.armed !== null
    && job.running !== null
    && job.runtime_state !== "unavailable"
  ));
  const runtimeHealthy = runtimeTruthKnown && runtimeJobs.every((job) => (
    job.installed === true
    && job.loaded === true
    && job.armed === true
    && (job.runtime_state === "idle" || job.runtime_state === "running")
  ));
  const overallHealthy = Boolean(payload) && contractOk && runtimeHealthy;
  const overallUnavailable = Boolean(payload) && contractOk && !runtimeTruthKnown;
  const issues: string[] = [];
  if (payload && !contractOk) issues.push("configuration integrity");
  if (payload && runtimeTruthKnown && !runtimeHealthy) issues.push("scheduler runtime");

  const explanation = loading
    ? "Loading scheduler status..."
    : !payload
      ? "Scheduler status is unavailable."
      : overallHealthy
        ? "Configuration and launchd runtime are healthy."
        : overallUnavailable
          ? "Launchd runtime inspection is unavailable."
          : `Needs attention: ${issues.join(" and ")}.`;

  const metrics = [
    { label: "Active jobs", value: loading || !payload ? "-" : String(payload.postgres_summary?.active_job_count ?? 0) },
    { label: "Successful runs", value: loading || !payload ? "-" : String(payload.postgres_summary?.success_count ?? 0) },
    { label: "Failed runs", value: loading || !payload ? "-" : String(payload.postgres_summary?.failure_count ?? 0) },
    { label: "Recorded runs", value: loading || !payload ? "-" : String(payload.postgres_summary?.run_history_count ?? 0) },
  ];

  return (
    <section className="scheduler-overview-panel" aria-label="Operations overview">
      <div className="scheduler-overview-primary">
        <span
          className={`scheduler-overview-icon ${overallHealthy ? "is-success" : overallUnavailable || !payload ? "is-muted" : "is-danger"}`}
          aria-hidden="true"
        >
          {loading ? <ShieldCheck size={22} /> : overallHealthy ? <CheckCircle2 size={22} /> : overallUnavailable ? <Activity size={22} /> : <AlertTriangle size={22} />}
        </span>
        <div>
          <p className="scheduler-overview-kicker">Overall scheduler state</p>
          <h2>{loading ? "Checking..." : overallHealthy ? "Healthy" : overallUnavailable || !payload ? "Unavailable" : "Attention"}</h2>
          <p className="scheduler-overview-explanation">{explanation}</p>
        </div>
      </div>
      <div className="scheduler-overview-divider" aria-hidden="true" />
      <div className="scheduler-overview-metrics">
        {metrics.map((metric) => (
          <div className="scheduler-overview-metric" key={metric.label}>
            <span>{metric.label}</span>
            <strong>{metric.value}</strong>
          </div>
        ))}
      </div>
      <button
        type="button"
        className="scheduler-diagnostics-link"
        onClick={onOpenDiagnostics}
        ref={diagnosticsTriggerRef}
      >
        <FileSearch size={14} aria-hidden="true" />
        View diagnostics
      </button>
    </section>
  );
}

function RuntimeJobsPanel({
  payload,
  loading,
  manualSubmitting,
  onRequestManualDiscovery,
  manualDiscoveryTriggerRef,
}: {
  payload: SchedulerSummaryPayload | null;
  loading: boolean;
  manualSubmitting: boolean;
  onRequestManualDiscovery: () => void;
  manualDiscoveryTriggerRef: React.RefObject<HTMLButtonElement>;
}) {
  const jobs = payload?.runtime_jobs || [];
  return (
    <section className="scheduler-runtime-section" aria-label="Scheduler runtime jobs">
      <div className="scheduler-runtime-section-heading">
        <div>
          <p className="scheduler-overview-kicker">Launchd runtime</p>
          <h2>Scheduled jobs</h2>
        </div>
        <span>{loading ? "Inspecting runtime..." : `${jobs.length} external jobs`}</span>
      </div>
      {jobs.length ? (
        <div className="scheduler-runtime-grid">
          {jobs.map((job) => {
            const lastRun = job.last_run;
            const lastStatus = clean(lastRun?.status) || "Never run";
            const tone = runtimeTone(job);
            const nextRun = schedulerNextRunPresentation(job, new Date(Date.now()));
            const manualEligibility = manualDiscoveryEligibility(job);
            return (
              <article
                className={`scheduler-runtime-card ${tone === "failed" || isFailedStatus(lastStatus) ? "is-attention" : ""}`}
                data-job-name={job.job_name}
                key={job.job_name}
              >
                <div className="scheduler-runtime-card-heading">
                  <div>
                    <div className="scheduler-runtime-card-title-row">
                      <h3>{jobDisplayName(job.job_name)}</h3>
                      {job.job_name === "agent_discovery" ? (
                        <button
                          type="button"
                          className="scheduler-manual-discovery-btn"
                          disabled={!manualEligibility.enabled || manualSubmitting}
                          onClick={onRequestManualDiscovery}
                          ref={manualDiscoveryTriggerRef}
                          title={manualEligibility.reason}
                        >
                          <Play size={12} aria-hidden="true" />
                          {job.manual_run_active === true || manualSubmitting
                            ? "Discovery running…"
                            : "Run discovery now"}
                        </button>
                      ) : null}
                    </div>
                    <p>{job.description}</p>
                  </div>
                  <div className="scheduler-runtime-card-badges">
                    <span className={`scheduler-badge scheduler-badge--${tone}`}>{runtimeLabel(job)}</span>
                    <span className={`scheduler-badge scheduler-badge--${job.armed === true ? "succeeded" : job.armed === null ? "unknown" : "failed"}`}>
                      {armedLabel(job)}
                    </span>
                  </div>
                </div>
                <dl className="scheduler-runtime-details">
                  <div><dt>Schedule</dt><dd>{formatCadence(job.cadence_seconds)}</dd></div>
                  <div>
                    <dt>Last run</dt>
                    <dd
                      className="scheduler-runtime-last-run"
                      title={lastRun ? formatDateTime(lastRun.started_at) : undefined}
                    >
                      {lastRun ? formatDateTime(lastRun.started_at) : "Never run"}
                    </dd>
                  </div>
                  <div><dt>Last result</dt><dd>{schedulerBadge(lastStatus)}</dd></div>
                  <div><dt>Return code</dt><dd>{lastRun ? shown(lastRun.return_code, "-") : "-"}</dd></div>
                </dl>
                <div className="scheduler-runtime-card-footer">
                  <div className="scheduler-runtime-card-footer-state">
                    <span><CheckCircle2 size={13} aria-hidden="true" />{job.installed === true ? "Installed" : job.installed === false ? "Not installed" : "Install unknown"}</span>
                    <span><Power size={13} aria-hidden="true" />{job.loaded === true ? "Loaded" : job.loaded === false ? "Unloaded" : "Load unknown"}</span>
                  </div>
                  <span
                    className={`scheduler-next-run-pill is-${nextRun.tone}`}
                    aria-label={nextRun.tone === "awaiting" ? "No scheduled run has been recorded yet." : undefined}
                    title={nextRun.tone === "awaiting" ? "No scheduled run has been recorded yet." : undefined}
                  >
                    <Clock size={13} aria-hidden="true" />
                    {nextRun.label}
                  </span>
                </div>
              </article>
            );
          })}
        </div>
      ) : (
        <div className="scheduler-runtime-empty">{loading ? "Loading scheduler runtime..." : "Scheduler runtime is unavailable."}</div>
      )}
    </section>
  );
}

function schedulerRunJobCell(
  run: SchedulerRun,
  onViewDiscoverySummary: (run: SchedulerRun, trigger: HTMLButtonElement) => void,
) {
  return (
    <div className="scheduler-run-history-job">
      <strong>{shown(run.job_name, "Unnamed job")}</strong>
      {clean(run.job_name) === "agent_discovery" && clean(run.run_id) ? (
        <button
          type="button"
          className="scheduler-run-summary-view-btn"
          onClick={(event) => onViewDiscoverySummary(run, event.currentTarget)}
          aria-label={`View discovery summary for ${clean(run.run_id)}`}
        >
          <FileSearch size={13} aria-hidden="true" />
          View
        </button>
      ) : null}
    </div>
  );
}

function jobStatusColumns(
  onViewDiscoverySummary: (run: SchedulerRun, trigger: HTMLButtonElement) => void,
): ColumnDef<SchedulerRun>[] {
  return [
    {
      id: "job_name",
      header: "Job",
      accessorFn: (row) => clean(row.job_name),
      size: 220,
      enableSorting: false,
      cell: ({ row }) => schedulerRunJobCell(row.original, onViewDiscoverySummary),
    },
    {
      id: "status",
      header: "Status",
      accessorFn: (row) => clean(row.status),
      size: 130,
      enableSorting: false,
      cell: ({ row }) => schedulerBadge(row.original.status),
    },
    {
      id: "started_at",
      header: "Last run",
      accessorFn: (row) => clean(row.started_at),
      size: 190,
      enableSorting: false,
      cell: ({ row }) => <span>{formatDateTime(row.original.started_at)}</span>,
    },
    {
      id: "finished_at",
      header: "Finished",
      accessorFn: (row) => clean(row.finished_at),
      size: 190,
      enableSorting: false,
      cell: ({ row }) => <span>{formatDateTime(row.original.finished_at)}</span>,
    },
    {
      id: "return_code",
      header: "Return code",
      accessorFn: (row) => clean(row.return_code),
      size: 110,
      enableSorting: false,
      cell: ({ row }) => <span>{shown(row.original.return_code, "-")}</span>,
    },
    {
      id: "run_id",
      header: "Run ID",
      accessorFn: (row) => clean(row.run_id),
      size: 160,
      enableSorting: false,
      cell: ({ row }) => {
        const runId = shown(row.original.run_id, "-");
        return <span className="scheduler-run-id-cell" title={runId}>{runId}</span>;
      },
    },
  ];
}

function runHistoryColumns(
  onViewDiscoverySummary: (run: SchedulerRun, trigger: HTMLButtonElement) => void,
): ColumnDef<SchedulerRun>[] {
  return [
    {
      id: "job_name",
      header: "Job",
      accessorFn: (row) => clean(row.job_name),
      size: 200,
      enableSorting: false,
      cell: ({ row }) => schedulerRunJobCell(row.original, onViewDiscoverySummary),
    },
    {
      id: "status",
      header: "Status",
      accessorFn: (row) => clean(row.status),
      size: 130,
      enableSorting: false,
      cell: ({ row }) => schedulerBadge(row.original.status),
    },
    {
      id: "trigger_source",
      header: "Trigger",
      accessorFn: (row) => clean(row.trigger_source),
      size: 110,
      enableSorting: false,
      cell: ({ row }) => {
        const label = schedulerTriggerLabel(row.original.trigger_source);
        return <span className={`scheduler-trigger-badge is-${label.toLowerCase()}`}>{label}</span>;
      },
    },
    {
      id: "started_at",
      header: "Started",
      accessorFn: (row) => clean(row.started_at),
      size: 190,
      enableSorting: true,
      cell: ({ row }) => <span>{formatDateTime(row.original.started_at)}</span>,
    },
    {
      id: "finished_at",
      header: "Finished",
      accessorFn: (row) => clean(row.finished_at),
      size: 190,
      enableSorting: false,
      cell: ({ row }) => <span>{formatDateTime(row.original.finished_at)}</span>,
    },
    {
      id: "return_code",
      header: "Return code",
      accessorFn: (row) => clean(row.return_code),
      size: 110,
      enableSorting: false,
      cell: ({ row }) => <span>{shown(row.original.return_code, "-")}</span>,
    },
    {
      id: "run_id",
      header: "Run ID",
      accessorFn: (row) => clean(row.run_id),
      size: 160,
      enableSorting: false,
      cell: ({ row }) => {
        const runId = shown(row.original.run_id, "-");
        return <span className="scheduler-run-id-cell" title={runId}>{runId}</span>;
      },
    },
  ];
}

function SchedulerRunsCard({
  status,
  errorMessage,
  payload,
  onRetry,
  readDiscoverySummary,
}: {
  status: "loading" | "ready" | "error";
  errorMessage?: string;
  payload: SchedulerSummaryPayload | null;
  onRetry: () => void;
  readDiscoverySummary: (runId: string) => Promise<AgentDiscoveryRunSummary>;
}) {
  const [activeTab, setActiveTab] = useState<RunsTab>("job_status");
  const [jobFilter, setJobFilter] = useState<string[]>([]);
  const [statusFilter, setStatusFilter] = useState<string[]>([]);
  const [selectedDiscoveryRun, setSelectedDiscoveryRun] = useState<SchedulerRun | null>(null);
  const [discoverySummaryState, setDiscoverySummaryState] = useState<DiscoverySummaryLoadState | null>(null);
  const discoverySummaryTriggerRef = useRef<HTMLButtonElement | null>(null);
  const discoverySummaryRequestRef = useRef(0);

  const jobStatusRows = useMemo(
    () => sortJobStatusRows(payload?.latest_runs_by_job || []),
    [payload],
  );
  const allRunHistoryRows = useMemo(() => payload?.recent_postgres_runs || [], [payload]);

  const jobOptions: SharedFilterOption[] = useMemo(
    () => Array.from(new Set(allRunHistoryRows.map((row) => clean(row.job_name)).filter(Boolean)))
      .sort()
      .map((value) => ({ value, label: value })),
    [allRunHistoryRows],
  );
  const statusOptions: SharedFilterOption[] = useMemo(
    () => Array.from(new Set(allRunHistoryRows.map((row) => clean(row.status)).filter(Boolean)))
      .sort()
      .map((value) => ({ value, label: value })),
    [allRunHistoryRows],
  );

  const runHistoryRows = useMemo(() => allRunHistoryRows.filter((row) => {
    if (jobFilter.length && !jobFilter.includes(clean(row.job_name))) return false;
    if (statusFilter.length && !statusFilter.includes(clean(row.status))) return false;
    return true;
  }), [allRunHistoryRows, jobFilter, statusFilter]);

  const openDiscoverySummary = useCallback((run: SchedulerRun, trigger: HTMLButtonElement) => {
    const runId = clean(run.run_id);
    if (!runId) return;
    discoverySummaryTriggerRef.current = trigger;
    setSelectedDiscoveryRun(run);
    setDiscoverySummaryState({ kind: "loading" });
    const requestId = discoverySummaryRequestRef.current + 1;
    discoverySummaryRequestRef.current = requestId;
    void readDiscoverySummary(runId).then((summary) => {
      if (discoverySummaryRequestRef.current === requestId) {
        setDiscoverySummaryState({ kind: "ready", summary });
      }
    }).catch((error) => {
      if (discoverySummaryRequestRef.current !== requestId) return;
      if (error instanceof AgentDiscoverySummaryUnavailableError) {
        setDiscoverySummaryState({ kind: "unavailable" });
      } else {
        setDiscoverySummaryState({
          kind: "error",
          message: error instanceof Error ? error.message : "Discovery summary could not be loaded.",
        });
      }
    });
  }, [readDiscoverySummary]);
  const closeDiscoverySummary = useCallback(() => {
    discoverySummaryRequestRef.current += 1;
    setSelectedDiscoveryRun(null);
    setDiscoverySummaryState(null);
  }, []);

  const jobStatusColumnsMemo = useMemo(
    () => jobStatusColumns(openDiscoverySummary),
    [openDiscoverySummary],
  );
  const runHistoryColumnsMemo = useMemo(
    () => runHistoryColumns(openDiscoverySummary),
    [openDiscoverySummary],
  );

  const [sorting, setSorting] = useState<SortingState>([{ id: "started_at", desc: true }]);

  const jobStatusTable = useReactTable({
    data: jobStatusRows,
    columns: jobStatusColumnsMemo,
    getRowId: runRowKey,
    getCoreRowModel: getCoreRowModel(),
  });

  const runHistoryTable = useReactTable({
    data: runHistoryRows,
    columns: runHistoryColumnsMemo,
    state: { sorting },
    getRowId: runRowKey,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    enableSortingRemoval: false,
    onSortingChange: setSorting,
  });

  const selectTab = (tab: RunsTab) => setActiveTab(tab);
  const handleTabKeyDown = (event: KeyboardEvent<HTMLButtonElement>, tab: RunsTab) => {
    if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
    event.preventDefault();
    selectTab(tab === "job_status" ? "run_history" : "job_status");
  };
  const tabClass = (active: boolean) => `${SHARED_NEUTRAL_CONTROL_CLASS} scheduler-runs-tab ${active ? "is-active" : "is-inactive"}`;

  const jobStatusPagination: SharedPaginationState = {
    page: 1,
    pageSize: Math.max(jobStatusRows.length, 1),
    totalCount: jobStatusRows.length,
    totalPages: 1,
    hasPrevPage: false,
    hasNextPage: false,
  };
  const runHistoryPagination: SharedPaginationState = {
    page: 1,
    pageSize: Math.max(runHistoryRows.length, 1),
    totalCount: runHistoryRows.length,
    totalPages: 1,
    hasPrevPage: false,
    hasNextPage: false,
  };

  const tabsNode = (
    <div className="scheduler-runs-tabs" role="tablist" aria-label="Scheduler runs view">
      <button
        role="tab"
        aria-selected={activeTab === "job_status"}
        tabIndex={activeTab === "job_status" ? 0 : -1}
        className={tabClass(activeTab === "job_status")}
        onKeyDown={(event) => handleTabKeyDown(event, "job_status")}
        onClick={() => selectTab("job_status")}
      >
        Job Status
      </button>
      <button
        role="tab"
        aria-selected={activeTab === "run_history"}
        tabIndex={activeTab === "run_history" ? 0 : -1}
        className={tabClass(activeTab === "run_history")}
        onKeyDown={(event) => handleTabKeyDown(event, "run_history")}
        onClick={() => selectTab("run_history")}
      >
        Run History
      </button>
    </div>
  );

  if (activeTab === "job_status") {
    return (
      <>
        <SharedTableCard
          className="scheduler-shared-table-card"
          ariaLabel="Job status table"
          title="Scheduler Runs"
          subtitle="Latest recorded result for each scheduled job."
          count={jobStatusRows.length}
          table={jobStatusTable}
          columns={jobStatusColumnsMemo}
          status={status}
          error={errorMessage}
          headerActions={tabsNode}
          pagination={jobStatusPagination}
          paginationNoun="jobs"
          paginationLabel="Job status"
          stickyColumnId="run_id"
          rowClassName={(row) => `scheduler-run-row ${isFailedStatus(row.original.status) ? "is-attention" : ""}`}
          detailId={() => ""}
          renderDetails={() => null}
          empty={<div className="scheduler-empty"><strong>No scheduler jobs recorded yet.</strong></div>}
          onPageChange={() => undefined}
          onRetry={onRetry}
          fillAvailableWidth
        />
        <DiscoveryRunSummaryModal
          run={selectedDiscoveryRun}
          state={discoverySummaryState}
          onClose={closeDiscoverySummary}
          triggerRef={discoverySummaryTriggerRef}
        />
      </>
    );
  }

  return (
    <>
      <SharedTableCard
      className="scheduler-shared-table-card"
      ariaLabel="Run history table"
      title="Scheduler Runs"
      subtitle="Persisted scheduler run history from Postgres."
      count={runHistoryRows.length}
      table={runHistoryTable}
      columns={runHistoryColumnsMemo}
      status={status}
      error={errorMessage}
      headingActions={(
        <div className="scheduler-runs-filters">
            <SharedFilterSelect
              id="schedulerRunHistoryJobFilter"
              label="Job"
              options={jobOptions}
              values={jobFilter}
              onChange={setJobFilter}
              placeholder="All jobs"
              allLabel="All jobs"
              mode="single"
            />
            <SharedFilterSelect
              id="schedulerRunHistoryStatusFilter"
              label="Status"
              options={statusOptions}
              values={statusFilter}
              onChange={setStatusFilter}
              placeholder="All statuses"
              allLabel="All statuses"
              mode="single"
            />
        </div>
      )}
      headerActions={tabsNode}
      pagination={runHistoryPagination}
      paginationNoun="runs"
      paginationLabel="Run history"
      stickyColumnId="run_id"
      rowClassName={(row) => `scheduler-run-row ${isFailedStatus(row.original.status) ? "is-attention" : ""}`}
      detailId={() => ""}
      renderDetails={() => null}
      empty={<div className="scheduler-empty"><strong>{allRunHistoryRows.length ? "No runs match the selected filters." : "No run history recorded yet."}</strong></div>}
      onPageChange={() => undefined}
      onRetry={onRetry}
      fillAvailableWidth
      />
      <DiscoveryRunSummaryModal
        run={selectedDiscoveryRun}
        state={discoverySummaryState}
        onClose={closeDiscoverySummary}
        triggerRef={discoverySummaryTriggerRef}
      />
    </>
  );
}

const DISCOVERY_SOURCE_LABELS: Record<string, string> = {
  domain_discovered: "Domain detection",
  career_discovered: "Career pages",
  network_discovered: "ATS network",
  greenhouse_embed_discovered: "Greenhouse embed",
  smartrecruiters_global_discovered: "SmartRecruiters global",
  github_discovered: "GitHub",
  sitemap_discovered: "Sitemap",
};

function summaryDateTime(value: unknown) {
  const raw = clean(value);
  if (!raw || Number.isNaN(new Date(raw).getTime())) return "—";
  return formatDateTime(raw);
}

function summaryDuration(startedAt: unknown, finishedAt: unknown) {
  const started = new Date(clean(startedAt));
  const finished = new Date(clean(finishedAt));
  const milliseconds = finished.getTime() - started.getTime();
  if (!Number.isFinite(milliseconds) || milliseconds < 0) return "—";
  const totalSeconds = Math.floor(milliseconds / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return minutes ? `${minutes}m ${seconds}s` : `${seconds}s`;
}

function summaryMetric(value: number | null | undefined) {
  return typeof value === "number" && Number.isFinite(value) ? value.toLocaleString() : "—";
}

function DiscoveryRunSummaryModal({
  run,
  state,
  onClose,
  triggerRef,
}: {
  run: SchedulerRun | null;
  state: DiscoverySummaryLoadState | null;
  onClose: () => void;
  triggerRef: React.RefObject<HTMLButtonElement | null>;
}) {
  const cardRef = useRef<HTMLDivElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!run) return undefined;
    const previousBodyOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    window.requestAnimationFrame(() => closeButtonRef.current?.focus());
    const handleKeydown = (event: globalThis.KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
        return;
      }
      if (event.key !== "Tab" || !cardRef.current) return;
      const controls = Array.from(
        cardRef.current.querySelectorAll<HTMLElement>("button:not([disabled]), [href], [tabindex]:not([tabindex='-1'])"),
      );
      if (!controls.length) return;
      const first = controls[0];
      const last = controls[controls.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", handleKeydown);
    return () => {
      document.removeEventListener("keydown", handleKeydown);
      document.body.style.overflow = previousBodyOverflow;
      triggerRef.current?.focus();
    };
  }, [onClose, run, triggerRef]);

  if (!run || !state) return null;
  const summary = state.kind === "ready" ? state.summary : null;
  const uniqueAts = Object.entries(summary?.discovery.run_unique_discovered_by_ats || {});
  const candidateAts = Object.entries(summary?.company_discovery.candidate_counts_by_ats || {});
  const sourceEntries = Object.entries(summary?.discovery.sources || {});
  const uniqueTotal = uniqueAts.length
    ? uniqueAts.reduce((total, [, count]) => total + count, 0)
    : null;
  const failedQueries = summary?.company_discovery.queries_failed;
  const triggerLabel = summary?.trigger === "manual"
    ? "Manual"
    : summary?.trigger === "scheduled"
      ? "Scheduled"
      : "Unknown";
  const startedLabel = summaryDateTime(summary?.started_at);
  const finishedLabel = summaryDateTime(summary?.finished_at);

  return (
    <div
      className="modal-backdrop scheduler-discovery-summary-backdrop"
      onClick={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div
        className="modal-card scheduler-discovery-summary-modal"
        ref={cardRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="schedulerDiscoverySummaryTitle"
      >
        <header className="scheduler-discovery-summary-header">
          <div>
            <div className="scheduler-discovery-summary-kicker"><FileSearch size={15} aria-hidden="true" /> Run analytics</div>
            <h3 id="schedulerDiscoverySummaryTitle">Discovery Run Summary</h3>
            <div className="scheduler-discovery-summary-subtitle">
              <span>{triggerLabel}</span>
              <span aria-hidden="true">•</span>
              <span>{summaryDateTime(summary?.started_at || run.started_at)}</span>
            </div>
          </div>
          <div className="scheduler-discovery-summary-header-actions">
            {summary ? schedulerBadge(summary.status) : null}
            <button
              type="button"
              className="scheduler-discovery-summary-close"
              onClick={onClose}
              ref={closeButtonRef}
              aria-label="Close discovery run summary"
            >
              <X
                size={20}
                strokeWidth={3}
                color="#ffffff"
                className="scheduler-discovery-summary-close-icon"
                style={{ width: 20, height: 20, color: "#ffffff", stroke: "#ffffff", display: "block", visibility: "visible", opacity: 1 }}
                aria-hidden="true"
              />
            </button>
          </div>
        </header>

        <div className="scheduler-discovery-summary-body">
          {state.kind === "loading" ? (
            <div className="scheduler-discovery-summary-state" role="status">
              <RefreshCw size={24} className="is-spinning" aria-hidden="true" />
              <strong>Loading discovery summary…</strong>
              <span>Reading the persisted artifact for this exact run.</span>
            </div>
          ) : null}
          {state.kind === "unavailable" ? (
            <div className="scheduler-discovery-summary-state is-unavailable">
              <FileSearch size={28} aria-hidden="true" />
              <strong>Discovery summary unavailable</strong>
              <span>This run does not have a persisted discovery summary.</span>
            </div>
          ) : null}
          {state.kind === "error" ? (
            <div className="scheduler-discovery-summary-state is-error" role="alert">
              <AlertTriangle size={28} aria-hidden="true" />
              <strong>Discovery summary could not be loaded</strong>
              <span>{state.message}</span>
            </div>
          ) : null}
          {summary ? (
            <>
              <div className="scheduler-discovery-kpi-grid">
                {([
                  ["Agent candidates", summary.company_discovery.total_candidate_count, "blue", Database],
                  ["Unique ATS discoveries", uniqueTotal, "violet", Activity],
                  ["Search queries", summary.company_discovery.queries_attempted, "cyan", FileSearch],
                  ["Failed queries", failedQueries, failedQueries == null ? "neutral" : failedQueries === 0 ? "emerald" : "amber", AlertTriangle],
                ] as const).map(([label, value, tone, Icon]) => (
                  <div className={`scheduler-discovery-kpi is-${tone}`} key={label}>
                    <span className="scheduler-discovery-kpi-icon"><Icon size={16} aria-hidden="true" /></span>
                    <span>{label}</span>
                    <strong>{summaryMetric(value)}</strong>
                  </div>
                ))}
              </div>

              <div className="scheduler-discovery-summary-columns">
                <section className="scheduler-discovery-section" aria-labelledby="schedulerDiscoveryAtsTitle">
                  <div className="scheduler-discovery-section-heading">
                    <h4 id="schedulerDiscoveryAtsTitle">Discovery by ATS</h4>
                    <span>Run-unique discoveries</span>
                  </div>
                  {uniqueAts.length ? (
                    <div className="scheduler-discovery-ats-grid">
                      {uniqueAts.map(([ats, count], index) => (
                        <div className={`scheduler-discovery-ats-tile is-accent-${index % 4}`} key={ats}>
                          <span className="scheduler-discovery-dot" aria-hidden="true" />
                          <span>{jobDisplayName(ats)}</span>
                          <strong>{count.toLocaleString()}</strong>
                        </div>
                      ))}
                    </div>
                  ) : <div className="scheduler-discovery-inline-empty">—</div>}
                </section>

                <section className="scheduler-discovery-section" aria-labelledby="schedulerDiscoverySourcesTitle">
                  <div className="scheduler-discovery-section-heading">
                    <h4 id="schedulerDiscoverySourcesTitle">Discovery sources</h4>
                    <span>Candidate origins</span>
                  </div>
                  {sourceEntries.length ? (
                    <div className="scheduler-discovery-source-list">
                      {sourceEntries.map(([source, counts], index) => {
                        const breakdown = Object.entries(counts)
                          .map(([ats, count]) => `${jobDisplayName(ats)} ${count}`)
                          .join(" · ");
                        return (
                          <div className={`scheduler-discovery-source-row is-accent-${index % 4}`} key={source}>
                            <span>{DISCOVERY_SOURCE_LABELS[source] || "Discovery source"}</span>
                            <small title={breakdown}>{breakdown}</small>
                            <strong>{Object.values(counts).reduce((total, count) => total + count, 0).toLocaleString()}</strong>
                          </div>
                        );
                      })}
                    </div>
                  ) : <div className="scheduler-discovery-inline-empty">—</div>}
                </section>
              </div>

              {candidateAts.length ? (
                <section className="scheduler-discovery-section scheduler-discovery-candidates" aria-labelledby="schedulerDiscoveryCandidatesTitle">
                  <div className="scheduler-discovery-section-heading">
                    <h4 id="schedulerDiscoveryCandidatesTitle">Agent search candidates</h4>
                    <span>Candidate pool by ATS</span>
                  </div>
                  <div className="scheduler-discovery-candidate-chips">
                    {candidateAts.map(([ats, count], index) => (
                      <span className={`is-accent-${index % 5}`} key={ats}><span>{jobDisplayName(ats)}</span><strong>{count.toLocaleString()}</strong></span>
                    ))}
                  </div>
                </section>
              ) : null}

              <section className="scheduler-discovery-section" aria-labelledby="schedulerDiscoveryExecutionTitle">
                <div className="scheduler-discovery-section-heading">
                  <h4 id="schedulerDiscoveryExecutionTitle">Execution</h4>
                  <span>Component outcomes</span>
                </div>
                <div className="scheduler-discovery-execution-grid">
                  {Object.entries(summary.components).map(([component, componentStatus]) => {
                    const label = component === "company_discovery_agent" ? "Company Discovery Agent" : "ATS Discovery Stage";
                    const Icon = componentStatus === "succeeded" ? CheckCircle2 : componentStatus === "failed" ? XCircle : Clock;
                    return (
                      <div className={`scheduler-discovery-execution-item is-${componentStatus}`} key={component}>
                        <Icon size={17} aria-hidden="true" />
                        <span>{label}</span>
                        <strong>{jobDisplayName(componentStatus)}</strong>
                      </div>
                    );
                  })}
                </div>
                {summary.failure_components.length ? (
                  <div className="scheduler-discovery-failure-note">
                    <AlertTriangle size={14} aria-hidden="true" />
                    {summary.failure_components.length} execution component{summary.failure_components.length === 1 ? "" : "s"} reported failure.
                  </div>
                ) : null}
              </section>

              <footer className="scheduler-discovery-metadata">
                <div><span>Started</span><strong title={startedLabel === "—" ? undefined : startedLabel}>{startedLabel}</strong></div>
                <div><span>Finished</span><strong title={finishedLabel === "—" ? undefined : finishedLabel}>{finishedLabel}</strong></div>
                <div><span>Duration</span><strong>{summaryDuration(summary.started_at, summary.finished_at)}</strong></div>
                <div><span>Return code</span><strong>{summary.return_code ?? "—"}</strong></div>
                <div><span>Run ID</span><strong className="scheduler-run-id-cell" title={summary.run_id}>{summary.run_id}</strong></div>
              </footer>
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
}

type DiagnosticsTab = "runtime" | "configuration" | "database_history";

function ManualDiscoveryConfirmDialog({
  open,
  confirming,
  onClose,
  onConfirm,
  triggerRef,
}: {
  open: boolean;
  confirming: boolean;
  onClose: () => void;
  onConfirm: () => void;
  triggerRef: React.RefObject<HTMLButtonElement>;
}) {
  const cardRef = useRef<HTMLDivElement>(null);
  const cancelRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return undefined;
    window.requestAnimationFrame(() => cancelRef.current?.focus());
    const handleKeydown = (event: globalThis.KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
        return;
      }
      if (event.key !== "Tab" || !cardRef.current) return;
      const buttons = Array.from(
        cardRef.current.querySelectorAll<HTMLButtonElement>("button:not([disabled])"),
      );
      if (!buttons.length) return;
      const first = buttons[0];
      const last = buttons[buttons.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", handleKeydown);
    return () => {
      document.removeEventListener("keydown", handleKeydown);
      triggerRef.current?.focus();
    };
  }, [onClose, open, triggerRef]);

  if (!open) return null;
  return (
    <div
      className="modal-backdrop"
      onClick={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div
        className="modal-card scheduler-manual-discovery-modal"
        ref={cardRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="schedulerManualDiscoveryTitle"
        aria-describedby="schedulerManualDiscoveryDescription"
      >
        <div className="modal-header">
          <div>
            <h3 id="schedulerManualDiscoveryTitle">Run discovery now?</h3>
            <div className="subtext" id="schedulerManualDiscoveryDescription">
              Runs the global discovery job once immediately. This does not change the existing 24-hour schedule.
            </div>
          </div>
        </div>
        <div className="scheduler-manual-discovery-actions">
          <button
            type="button"
            className="scheduler-confirm-secondary"
            disabled={confirming}
            onClick={onClose}
            ref={cancelRef}
          >
            Cancel
          </button>
          <button
            type="button"
            className="scheduler-confirm-primary"
            disabled={confirming}
            onClick={onConfirm}
          >
            {confirming ? "Starting discovery…" : "Run discovery"}
          </button>
        </div>
      </div>
    </div>
  );
}

function ConfigStatusRow({
  icon: Icon,
  label,
  ok,
  explanation,
}: {
  icon: typeof ShieldCheck;
  label: string;
  ok: boolean;
  explanation: string;
}) {
  return (
    <li className={`scheduler-config-row ${ok ? "is-ok" : "is-issue"}`}>
      <Icon size={16} aria-hidden="true" />
      <span className="scheduler-config-row-label">{label}</span>
      <span className={`scheduler-badge ${ok ? "scheduler-badge--succeeded" : "scheduler-badge--failed"}`}>
        {ok ? "OK" : "Issue"}
      </span>
      <span className="scheduler-config-row-explanation">{explanation}</span>
    </li>
  );
}

function CompactRunsTable({ rows, emptyMessage }: { rows: SchedulerRun[]; emptyMessage: string }) {
  if (!rows.length) {
    return <div className="scheduler-empty scheduler-empty--compact">{emptyMessage}</div>;
  }
  return (
    <div className="scheduler-diagnostics-table-viewport">
      <table>
        <thead>
          <tr>
            <th>Job</th>
            <th>Status</th>
            <th>Trigger</th>
            <th>Started</th>
            <th>Finished</th>
            <th>Return code</th>
            <th>Run ID</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => {
            const jobName = shown(row.job_name, "Unnamed job");
            const started = formatDateTime(row.started_at);
            const finished = formatDateTime(row.finished_at);
            const runId = shown(row.run_id, "-");
            return (
              <tr key={runRowKey(row, index)}>
                <td title={jobName}>{jobName}</td>
                <td>{schedulerBadge(row.status)}</td>
                <td>{schedulerTriggerLabel(row.trigger_source)}</td>
                <td title={started}>{started}</td>
                <td title={finished}>{finished}</td>
                <td>{shown(row.return_code, "-")}</td>
                <td className="scheduler-run-id-cell" title={runId}>{runId}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function DiagnosticsModal({
  open,
  payload,
  onClose,
  triggerRef,
}: {
  open: boolean;
  payload: SchedulerSummaryPayload | null;
  onClose: () => void;
  triggerRef: React.RefObject<HTMLButtonElement>;
}) {
  const [tab, setTab] = useState<DiagnosticsTab>("runtime");
  const cardRef = useRef<HTMLDivElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return undefined;
    setTab("runtime");
    window.requestAnimationFrame(() => closeButtonRef.current?.focus());

    const previousBodyOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const handleKeydown = (event: globalThis.KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
        return;
      }
      if (event.key !== "Tab" || !cardRef.current) return;
      const focusable = Array.from(
        cardRef.current.querySelectorAll<HTMLElement>(
          "button:not([disabled]), a[href], input:not([disabled]), [tabindex]:not([tabindex='-1'])",
        ),
      );
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

    document.addEventListener("keydown", handleKeydown);
    return () => {
      document.removeEventListener("keydown", handleKeydown);
      document.body.style.overflow = previousBodyOverflow;
      triggerRef.current?.focus();
    };
  }, [open, onClose, triggerRef]);

  if (!open) return null;

  const checks = payload?.contract_health?.checks || {};
  const contractOk = Boolean(payload?.contract_health?.all_checks_pass);

  return (
    <div
      className="modal-backdrop"
      onClick={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div
        className="modal-card scheduler-diagnostics-modal-card"
        ref={cardRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="schedulerDiagnosticsModalTitle"
        aria-describedby="schedulerDiagnosticsModalDescription"
      >
        <div className="modal-header">
          <div>
            <h3 id="schedulerDiagnosticsModalTitle">Scheduler diagnostics</h3>
            <div className="subtext" id="schedulerDiagnosticsModalDescription">
              Read-only launchd runtime, configuration integrity, and Postgres history.
            </div>
          </div>
          <button
            type="button"
            className="ghost-btn scheduler-diagnostics-close-btn"
            onClick={onClose}
            ref={closeButtonRef}
            aria-label="Close diagnostics"
          >
            <X size={16} aria-hidden="true" />
          </button>
        </div>

        <div className="scheduler-diagnostics-tabs" role="tablist" aria-label="Diagnostics views">
          {([
            ["runtime", "Runtime"],
            ["configuration", "Configuration Integrity"],
            ["database_history", "Database History"],
          ] as const).map(([value, label]) => (
            <button
              key={value}
              role="tab"
              aria-selected={tab === value}
              className={`${SHARED_NEUTRAL_CONTROL_CLASS} scheduler-diagnostics-tab ${tab === value ? "is-active" : "is-inactive"}`}
              onClick={() => setTab(value)}
            >
              {label}
            </button>
          ))}
        </div>

        <div className="modal-body scheduler-diagnostics-body">
          {tab === "runtime" ? (
            <div className="scheduler-runtime-diagnostics-grid">
              {(payload?.runtime_jobs || []).map((job) => (
                <section className="scheduler-runtime-diagnostic-card" key={job.job_name}>
                  <div className="scheduler-runtime-diagnostic-heading">
                    <div><h4>{jobDisplayName(job.job_name)}</h4><span>{formatCadence(job.cadence_seconds)}</span></div>
                    <span className={`scheduler-badge scheduler-badge--${runtimeTone(job)}`}>{runtimeLabel(job)}</span>
                  </div>
                  <dl>
                    <div><dt>Installed</dt><dd>{truthLabel(job.installed)}</dd></div>
                    <div><dt>Loaded</dt><dd>{truthLabel(job.loaded)}</dd></div>
                    <div><dt>Armed</dt><dd>{truthLabel(job.armed)}</dd></div>
                    <div><dt>Running</dt><dd>{truthLabel(job.running)}</dd></div>
                    {job.job_name === "agent_discovery" ? (
                      <div><dt>Manual run</dt><dd>{job.manual_run_active === true ? "Active" : "Inactive"}</dd></div>
                    ) : null}
                  </dl>
                </section>
              ))}
            </div>
          ) : null}
          {tab === "configuration" ? (
            <ul className="scheduler-config-list">
              <ConfigStatusRow
                icon={contractOk ? ShieldCheck : AlertTriangle}
                label="Overall configuration integrity"
                ok={contractOk}
                explanation={contractOk ? "All configuration checks pass." : "One or more configuration checks failed."}
              />
              <ConfigStatusRow
                icon={checks.seed_sql_matches_artifact ? CircleCheck : XCircle}
                label="Seed SQL artifact match"
                ok={Boolean(checks.seed_sql_matches_artifact)}
                explanation="Generated seed SQL matches the committed artifact."
              />
              <ConfigStatusRow
                icon={checks.init_sql_matches_artifact ? CircleCheck : XCircle}
                label="Init SQL artifact match"
                ok={Boolean(checks.init_sql_matches_artifact)}
                explanation="Generated init SQL matches the committed artifact."
              />
            </ul>
          ) : null}
          {tab === "database_history" ? (
            <>
              <p className="scheduler-diagnostics-tab-subtitle">
                <Database size={13} aria-hidden="true" /> Recent scheduler runs currently mirrored into Postgres.
              </p>
              <CompactRunsTable rows={payload?.recent_postgres_runs || []} emptyMessage="No Postgres run rows recorded yet." />
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
}

export function SchedulerHealthDashboard({
  readSummary = readSchedulerSummary,
  runDiscoveryNow = runAgentDiscoveryNow,
  readDiscoverySummary = readAgentDiscoveryRunSummary,
}: SchedulerHealthDashboardProps) {
  const [state, setState] = useState<LoadState>({ kind: "loading" });
  const [refreshing, setRefreshing] = useState(false);
  const [diagnosticsOpen, setDiagnosticsOpen] = useState(false);
  const [manualConfirmOpen, setManualConfirmOpen] = useState(false);
  const [manualSubmitting, setManualSubmitting] = useState(false);
  const [manualActionError, setManualActionError] = useState("");
  const diagnosticsTriggerRef = useRef<HTMLButtonElement>(null);
  const manualDiscoveryTriggerRef = useRef<HTMLButtonElement>(null);

  const refresh = useCallback(async (showSpinner = false) => {
    if (showSpinner) setRefreshing(true);
    try {
      const payload = await readSummary();
      setState({ kind: "ready", payload, checkedAt: Date.now() });
    } catch (error) {
      setState({ kind: "error", message: error instanceof Error ? error.message : "Scheduler summary is unavailable." });
    } finally {
      if (showSpinner) setRefreshing(false);
    }
  }, [readSummary]);

  const confirmManualDiscovery = useCallback(async () => {
    setManualSubmitting(true);
    setManualActionError("");
    try {
      const result = await runDiscoveryNow();
      if (!result.accepted || result.job_name !== "agent_discovery") {
        throw new Error("Manual Agent Discovery was not accepted.");
      }
      setState((current) => {
        if (current.kind !== "ready") return current;
        return {
          ...current,
          payload: {
            ...current.payload,
            runtime_jobs: current.payload.runtime_jobs?.map((job) => (
              job.job_name === "agent_discovery"
                ? {
                    ...job,
                    manual_run_active: true,
                    manual_run_started_at: new Date(Date.now()).toISOString(),
                  }
                : job
            )),
          },
        };
      });
      setManualConfirmOpen(false);
    } catch (error) {
      setManualActionError(
        error instanceof Error
          ? error.message
          : "Manual Agent Discovery could not be started.",
      );
    } finally {
      setManualSubmitting(false);
    }
  }, [runDiscoveryNow]);
  const closeManualDiscoveryConfirm = useCallback(() => {
    setManualConfirmOpen(false);
  }, []);
  const openManualDiscoveryConfirm = useCallback(() => {
    setManualActionError("");
    setManualConfirmOpen(true);
  }, []);

  useEffect(() => {
    void refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const payload = state.kind === "ready" ? state.payload : null;
  const status: "loading" | "ready" | "error" = state.kind;
  const errorMessage = state.kind === "error" ? state.message : undefined;
  const lastRefreshedAt = state.kind === "ready" ? state.checkedAt : null;

  return (
    <div className="scheduler-health-dashboard" aria-busy={state.kind === "loading"}>
      <DashboardHeader onRefresh={() => void refresh(true)} refreshing={refreshing} lastRefreshedAt={lastRefreshedAt} />
      {state.kind === "error" ? (
        <div className="scheduler-error-banner" role="alert">{state.message}</div>
      ) : null}
      {manualActionError ? (
        <div className="scheduler-error-banner" role="alert">{manualActionError}</div>
      ) : null}
      <OverviewPanel
        payload={payload}
        loading={state.kind === "loading"}
        onOpenDiagnostics={() => setDiagnosticsOpen(true)}
        diagnosticsTriggerRef={diagnosticsTriggerRef}
      />
      <RuntimeJobsPanel
        payload={payload}
        loading={state.kind === "loading"}
        manualSubmitting={manualSubmitting}
        onRequestManualDiscovery={openManualDiscoveryConfirm}
        manualDiscoveryTriggerRef={manualDiscoveryTriggerRef}
      />
      <SchedulerRunsCard
        status={status}
        errorMessage={errorMessage}
        payload={payload}
        onRetry={() => void refresh(true)}
        readDiscoverySummary={readDiscoverySummary}
      />
      <DiagnosticsModal
        open={diagnosticsOpen}
        payload={payload}
        onClose={() => setDiagnosticsOpen(false)}
        triggerRef={diagnosticsTriggerRef}
      />
      <ManualDiscoveryConfirmDialog
        open={manualConfirmOpen}
        confirming={manualSubmitting}
        onClose={closeManualDiscoveryConfirm}
        onConfirm={() => void confirmManualDiscovery()}
        triggerRef={manualDiscoveryTriggerRef}
      />
    </div>
  );
}
