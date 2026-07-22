import {
  type ColumnDef,
  type SortingState,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import {
  AlertTriangle,
  CheckCircle2,
  CircleCheck,
  Database,
  FileSearch,
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
  formatClockTime,
  formatDateTime,
  isFailedStatus,
  readSchedulerSummary,
  runRowKey,
  shown,
  sortJobStatusRows,
  statusSlug,
  type SchedulerRun,
  type SchedulerSummaryPayload,
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
};

function schedulerBadge(status: unknown) {
  const label = shown(status, "Unknown");
  const tone = statusSlug(status);
  return <span className={`scheduler-badge scheduler-badge--${tone}`}>{label}</span>;
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
  const overallHealthy = Boolean(payload) && contractOk;
  const issues: string[] = [];
  if (payload && !contractOk) issues.push("configuration integrity");

  const explanation = loading
    ? "Loading scheduler status..."
    : !payload
      ? "Scheduler status is unavailable."
      : overallHealthy
        ? "Configuration integrity is consistent."
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
          className={`scheduler-overview-icon ${overallHealthy ? "is-success" : payload ? "is-danger" : "is-muted"}`}
          aria-hidden="true"
        >
          {loading ? <ShieldCheck size={22} /> : overallHealthy ? <CheckCircle2 size={22} /> : <AlertTriangle size={22} />}
        </span>
        <div>
          <p className="scheduler-overview-kicker">Overall scheduler state</p>
          <h2>{loading ? "Checking..." : overallHealthy ? "Healthy" : payload ? "Attention" : "Unavailable"}</h2>
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

function jobStatusColumns(): ColumnDef<SchedulerRun>[] {
  return [
    {
      id: "job_name",
      header: "Job",
      accessorFn: (row) => clean(row.job_name),
      size: 220,
      enableSorting: false,
      cell: ({ row }) => <strong>{shown(row.original.job_name, "Unnamed job")}</strong>,
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
      cell: ({ row }) => <span className="scheduler-run-id-cell">{shown(row.original.run_id, "-")}</span>,
    },
  ];
}

function runHistoryColumns(): ColumnDef<SchedulerRun>[] {
  return [
    {
      id: "job_name",
      header: "Job",
      accessorFn: (row) => clean(row.job_name),
      size: 200,
      enableSorting: false,
      cell: ({ row }) => <strong>{shown(row.original.job_name, "Unnamed job")}</strong>,
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
      cell: ({ row }) => <span className="scheduler-run-id-cell">{shown(row.original.run_id, "-")}</span>,
    },
  ];
}

function SchedulerRunsCard({
  status,
  errorMessage,
  payload,
  onRetry,
}: {
  status: "loading" | "ready" | "error";
  errorMessage?: string;
  payload: SchedulerSummaryPayload | null;
  onRetry: () => void;
}) {
  const [activeTab, setActiveTab] = useState<RunsTab>("job_status");
  const [jobFilter, setJobFilter] = useState<string[]>([]);
  const [statusFilter, setStatusFilter] = useState<string[]>([]);

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

  const jobStatusColumnsMemo = useMemo(jobStatusColumns, []);
  const runHistoryColumnsMemo = useMemo(runHistoryColumns, []);

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
    );
  }

  return (
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
      headerActions={(
        <div className="scheduler-runs-header-actions">
          {tabsNode}
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
        </div>
      )}
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
  );
}

type DiagnosticsTab = "configuration" | "database_history";

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
  const [tab, setTab] = useState<DiagnosticsTab>("configuration");
  const cardRef = useRef<HTMLDivElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return undefined;
    setTab("configuration");
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
              Configuration integrity and database history.
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
}: SchedulerHealthDashboardProps) {
  const [state, setState] = useState<LoadState>({ kind: "loading" });
  const [refreshing, setRefreshing] = useState(false);
  const [diagnosticsOpen, setDiagnosticsOpen] = useState(false);
  const diagnosticsTriggerRef = useRef<HTMLButtonElement>(null);

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
      <OverviewPanel
        payload={payload}
        loading={state.kind === "loading"}
        onOpenDiagnostics={() => setDiagnosticsOpen(true)}
        diagnosticsTriggerRef={diagnosticsTriggerRef}
      />
      <SchedulerRunsCard
        status={status}
        errorMessage={errorMessage}
        payload={payload}
        onRetry={() => void refresh(true)}
      />
      <DiagnosticsModal
        open={diagnosticsOpen}
        payload={payload}
        onClose={() => setDiagnosticsOpen(false)}
        triggerRef={diagnosticsTriggerRef}
      />
    </div>
  );
}
