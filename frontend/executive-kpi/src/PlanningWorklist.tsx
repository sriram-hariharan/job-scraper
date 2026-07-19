import {
  type ColumnDef,
  type ColumnSizingState,
  type ExpandedState,
  type SortingState,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { CheckCircle2, ClipboardList, FileText, UserRoundCheck } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  SHARED_NEUTRAL_CONTROL_CLASS,
  SharedExpandedDetail,
  SharedExpansionButton,
  SharedInfoPopover,
  SharedJobPreview,
  SharedMatchMeter,
  SharedTableCard,
  type SharedPaginationState,
} from "./table/TablePrimitives";

/**
 * Planning uses the same extracted Origin UI/TanStack primitives as Executive Queue.
 * References:
 * https://21st.dev/community/components/originui/table/default
 * https://21st.dev/community/components/originui/table/data-table-with-filters-made-with-tan-stack-table
 * https://21st.dev/community/components/originui/popover/tooltip-like-popover
 */
export const PLANNING_STATE_EVENT = "applylens:planning-worklist-state";
export const PLANNING_ACTION_EVENT = "applylens:planning-worklist-action";
export const PLANNING_COLUMN_WIDTH_STORAGE_KEY = "applylens.planning.columnWidths.v1";
export const PLANNING_NEXT_STEP_COLUMN_WIDTH = 190;

export type PlanningRow = Record<string, unknown> & {
  queue_rank?: number | string;
  job_doc_id?: string;
  job_url?: string;
  job_title?: string;
  job_company?: string;
  job_location?: string;
  posted_at?: string;
  action?: string;
  winner_score?: number | string | null;
  winner_bucket?: string;
  winner_resume?: string;
  operator_selected_resume?: string;
  selected_resume?: string;
  runner_up_resume?: string;
  runnerup_resume?: string;
  runner_up_score?: number | string | null;
  score_gap?: number | string | null;
  packet_generation_allowed?: boolean | string;
  tailoring_workspace_state?: string;
  missing_requirement_count?: number | string | null;
  operator_decision?: string;
  queue_priority_reason?: string;
  selection_signal?: string;
  llm_adjudicator_readback_enabled?: boolean | string;
  llm_adjudicator_readback_status?: string;
  llm_adjudicator_readback?: unknown;
  __planning_action?: {
    kind: "open_workspace" | "generate_suggestions" | "unavailable";
    label: string;
    disabled: boolean;
    title: string;
  };
};

export type PlanningMetrics = {
  total: number;
  readyForReview: number;
  packetReady: number;
  needsDecision: number;
};

export type PlanningWorklistState = {
  status: "loading" | "ready" | "error";
  rows: PlanningRow[];
  metaLabel: string;
  message?: string;
  pagination: SharedPaginationState;
  sort: { key: string; direction: "asc" | "desc" };
  resultKey: string;
  metrics: PlanningMetrics;
};

export type PlanningWorklistAction =
  | { type: "page_change"; page: number }
  | { type: "sort_change"; key: string; direction: "asc" | "desc" }
  | { type: "retry" }
  | { type: "clear_filters" }
  | { type: "next_step"; row: PlanningRow };

export const DEFAULT_PLANNING_STATE: PlanningWorklistState = {
  status: "loading",
  rows: [],
  metaLabel: "Planning view · loading",
  pagination: {
    page: 1,
    pageSize: 15,
    totalCount: 0,
    totalPages: 1,
    hasPrevPage: false,
    hasNextPage: false,
  },
  sort: { key: "", direction: "asc" },
  resultKey: "initial",
  metrics: { total: 0, readyForReview: 0, packetReady: 0, needsDecision: 0 },
};

const WIDTH_BOUNDS: Record<string, { min: number; max: number }> = {
  queue_rank: { min: 72, max: 110 },
  job_title: { min: 210, max: 420 },
  posted_at: { min: 112, max: 180 },
  recommendation: { min: 150, max: 260 },
  winner_score: { min: 112, max: 180 },
  selected_resume: { min: 200, max: 360 },
  packet_status: { min: 160, max: 280 },
};

function publishPlanningAction(action: PlanningWorklistAction) {
  window.dispatchEvent(new CustomEvent(PLANNING_ACTION_EVENT, { detail: action }));
}

function cleanText(value: unknown): string {
  return String(value ?? "").trim();
}

function humanize(value: unknown): string {
  const text = cleanText(value).replace(/_/g, " ");
  return text ? text.charAt(0).toUpperCase() + text.slice(1) : "Unavailable";
}

function formatResume(value: unknown): string {
  const text = cleanText(value);
  return text ? text.replace(/\.pdf$/i, "").replace(/_/g, " ") : "Not selected";
}

function selectedResume(row: PlanningRow): string {
  return cleanText(row.operator_selected_resume || row.selected_resume || row.winner_resume);
}

function formatDate(value: unknown): string {
  const raw = cleanText(value);
  if (!raw) return "Unavailable";
  const date = new Date(raw);
  if (Number.isNaN(date.getTime())) return raw;
  return new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", year: "numeric" }).format(date);
}

function recommendation(row: PlanningRow): { label: string; tone: string } {
  const normalized = cleanText(row.action).toUpperCase();
  return {
    APPLY: { label: "Ready for review", tone: "ready" },
    APPLY_REVIEW_VARIANTS: { label: "Review resume choice", tone: "choice" },
    MAYBE_TAILOR: { label: "Tailor first", tone: "tailor" },
    SKIP_FOR_NOW: { label: "Review later", tone: "later" },
  }[normalized] || { label: cleanText(row.action) || "Unavailable", tone: "unavailable" };
}

function packetLabel(value: unknown): string {
  const normalized = cleanText(value).toLowerCase();
  if (["true", "1", "yes", "y", "on"].includes(normalized)) return "Packet ready";
  if (["false", "0", "no", "n", "off"].includes(normalized)) return "No packet";
  return "Packet unavailable";
}

function readPlanningColumnSizing(): ColumnSizingState {
  try {
    const parsed = JSON.parse(localStorage.getItem(PLANNING_COLUMN_WIDTH_STORAGE_KEY) || "{}");
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return {};
    const widths = "version" in parsed && (parsed as { version?: unknown }).version === 1
      ? (parsed as { widths?: unknown }).widths
      : parsed;
    if (!widths || typeof widths !== "object" || Array.isArray(widths)) return {};
    return Object.fromEntries(Object.entries(widths).flatMap(([key, raw]) => {
      const bounds = WIDTH_BOUNDS[key];
      const numeric = Number(raw);
      if (!bounds || !Number.isFinite(numeric)) return [];
      return [[key, Math.min(bounds.max, Math.max(bounds.min, numeric))]];
    }));
  } catch {
    return {};
  }
}

function savePlanningColumnSizing(widths: ColumnSizingState) {
  localStorage.setItem(PLANNING_COLUMN_WIDTH_STORAGE_KEY, JSON.stringify({ version: 1, widths }));
}

function planningRowKey(row: PlanningRow, index: number): string {
  return cleanText(row.job_doc_id || row.job_url || row.queue_rank) || `planning-row-${index}`;
}

function parseAdvisoryReadback(value: unknown): Record<string, unknown> | null {
  if (value && typeof value === "object" && !Array.isArray(value)) return value as Record<string, unknown>;
  const raw = cleanText(value);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed as Record<string, unknown> : null;
  } catch {
    return null;
  }
}

function AdvisoryDetails({ row }: { row: PlanningRow }) {
  const readback = parseAdvisoryReadback(row.llm_adjudicator_readback);
  const status = cleanText(readback?.status || row.llm_adjudicator_readback_status || "Unavailable");
  const candidateNames = Array.isArray(readback?.candidate_resume_names)
    ? readback.candidate_resume_names.map(cleanText).filter(Boolean).join(", ")
    : "";
  const fields = [
    ["Status", humanize(status)],
    ["Provider", cleanText(readback?.provider_used || readback?.provider_requested)],
    ["Model", cleanText(readback?.model_used || readback?.model_requested)],
    ["Candidates", candidateNames],
    ["Recommendation", cleanText(readback?.adjudicator_recommendation_label)],
    ["Summary", cleanText(readback?.adjudicator_summary)],
  ].filter((field) => field[1]);

  return (
    <details className="planning-react-ai-review">
      <summary>View AI Review</summary>
      <dl>
        {fields.map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}
      </dl>
      <p>Advisory only. Does not override the selected resume or score.</p>
    </details>
  );
}

function PlanningDetails({ row }: { row: PlanningRow }) {
  const advisoryEnabled = ["true", "1", "yes", "on"].includes(cleanText(row.llm_adjudicator_readback_enabled).toLowerCase());
  return (
    <SharedExpandedDetail>
      <div className="planning-react-details-grid">
        <div><span>Full location</span><strong>{cleanText(row.job_location) || "Unavailable"}</strong></div>
        <div><span>Prefilter relevance</span><strong>{humanize(row.selection_signal)}</strong></div>
        <div><span>AI evaluation</span><strong>{humanize(row.llm_adjudicator_readback_status)}</strong></div>
        <div><span>Runner-up resume</span><strong>{formatResume(row.runner_up_resume || row.runnerup_resume)}</strong></div>
        <div><span>Runner-up score</span><strong>{cleanText(row.runner_up_score) || "Unavailable"}</strong></div>
        <div><span>Score gap</span><strong>{cleanText(row.score_gap) || "Unavailable"}</strong></div>
        <div><span>Operator decision</span><strong>{humanize(row.operator_decision || "Not decided")}</strong></div>
        <div><span>Priority reason</span><strong>{cleanText(row.queue_priority_reason) || "Unavailable"}</strong></div>
        <div><span>Missing requirements</span><strong>{cleanText(row.missing_requirement_count) || "0"}</strong></div>
      </div>
      {advisoryEnabled ? <AdvisoryDetails row={row} /> : null}
    </SharedExpandedDetail>
  );
}

function buildPlanningColumns(): ColumnDef<PlanningRow>[] {
  return [
    {
      id: "expand",
      header: "",
      size: 42,
      minSize: 42,
      maxSize: 42,
      enableSorting: false,
      enableResizing: false,
      cell: ({ row }) => (
        <SharedExpansionButton
          expanded={row.getIsExpanded()}
          label={`${row.getIsExpanded() ? "Collapse" : "Expand"} planning details for ${cleanText(row.original.job_title) || "job"}`}
          controls={`planning-react-detail-${row.id}`}
          onClick={row.getToggleExpandedHandler()}
        />
      ),
    },
    { accessorKey: "queue_rank", header: "Rank", size: 78, minSize: 72, maxSize: 110 },
    {
      id: "job_title",
      header: "Job",
      size: 270,
      minSize: 210,
      maxSize: 420,
      accessorFn: (row) => cleanText(row.job_title),
      cell: ({ row }) => {
        const title = cleanText(row.original.job_title) || "Untitled job";
        const company = cleanText(row.original.job_company) || "Company unavailable";
        const location = cleanText(row.original.job_location) || "Location unavailable";
        const href = cleanText(row.original.job_url || row.original.job_doc_id);
        return (
          <SharedJobPreview title={title} location={location}>
            <span className="planning-react-job-cell">
              {href ? <a href={href} target="_blank" rel="noreferrer">{title}</a> : <strong>{title}</strong>}
              <span>{company} · {location}</span>
            </span>
          </SharedJobPreview>
        );
      },
    },
    {
      id: "posted_at",
      header: "Posted at",
      size: 128,
      minSize: 112,
      maxSize: 180,
      accessorFn: (row) => row.posted_at ? new Date(row.posted_at).getTime() : null,
      sortUndefined: "last",
      cell: ({ row }) => <time dateTime={cleanText(row.original.posted_at)}>{formatDate(row.original.posted_at)}</time>,
    },
    {
      id: "recommendation",
      header: "Review readiness",
      size: 184,
      minSize: 150,
      maxSize: 260,
      accessorFn: (row) => recommendation(row).label,
      cell: ({ row }) => {
        const value = recommendation(row.original);
        const advisory = ["true", "1", "yes", "on"].includes(cleanText(row.original.llm_adjudicator_readback_enabled).toLowerCase());
        return (
          <span className="planning-react-readiness">
            <span className={`planning-react-badge planning-react-badge--${value.tone}`}>{value.label}</span>
            {advisory ? <span className="planning-react-advisory">AI notes · advisory</span> : null}
          </span>
        );
      },
    },
    {
      id: "winner_score",
      header: "Match score",
      size: 132,
      minSize: 112,
      maxSize: 180,
      accessorFn: (row) => row.winner_score,
      sortUndefined: "last",
      cell: ({ row }) => <SharedMatchMeter value={row.original.winner_score} strength={humanize(row.original.winner_bucket)} />,
    },
    {
      id: "selected_resume",
      header: "Resume selection",
      size: 230,
      minSize: 200,
      maxSize: 360,
      accessorFn: selectedResume,
      cell: ({ row }) => <span className="planning-react-resume" title={selectedResume(row.original)}>{formatResume(selectedResume(row.original))}</span>,
    },
    {
      id: "packet_status",
      header: () => (
        <span className="planning-react-packet-header">
          Packet / workspace
          <SharedInfoPopover label="About packet and workspace status">
            A packet is a review bundle for this job. It does not apply to the job.
          </SharedInfoPopover>
        </span>
      ),
      size: 188,
      minSize: 160,
      maxSize: 280,
      enableSorting: false,
      cell: ({ row }) => (
        <span className="planning-react-status-stack">
          <span className={`planning-react-badge ${packetLabel(row.original.packet_generation_allowed) === "Packet ready" ? "is-ready" : ""}`}>
            {packetLabel(row.original.packet_generation_allowed)}
          </span>
          <span>{humanize(row.original.tailoring_workspace_state || "Workspace unavailable")}</span>
        </span>
      ),
    },
    {
      id: "next_step",
      header: "Next step",
      size: PLANNING_NEXT_STEP_COLUMN_WIDTH,
      minSize: PLANNING_NEXT_STEP_COLUMN_WIDTH,
      maxSize: PLANNING_NEXT_STEP_COLUMN_WIDTH,
      enableSorting: false,
      enableResizing: false,
      cell: ({ row }) => {
        const action = row.original.__planning_action || { kind: "unavailable", label: "Unavailable", disabled: true, title: "No action available." };
        return (
          <button
            type="button"
            className={`planning-react-next-step ${action.kind === "generate_suggestions" ? "is-primary" : ""}`}
            disabled={action.disabled}
            title={action.title}
            onClick={() => publishPlanningAction({ type: "next_step", row: row.original })}
          >{action.label}</button>
        );
      },
    },
  ];
}

export function PlanningWorklist({ state }: { state: PlanningWorklistState }) {
  const [columnSizing, setColumnSizing] = useState<ColumnSizingState>(readPlanningColumnSizing);
  const [expandedId, setExpandedId] = useState<string>("");
  const columns = useMemo(buildPlanningColumns, []);
  const rows = useMemo(() => state.rows.slice(), [state.rows]);
  const sorting = useMemo<SortingState>(() => state.sort.key ? [{ id: state.sort.key, desc: state.sort.direction === "desc" }] : [], [state.sort]);

  useEffect(() => setExpandedId(""), [state.resultKey, state.pagination.page, state.sort.key, state.sort.direction]);

  const table = useReactTable({
    data: rows,
    columns,
    state: {
      sorting,
      columnSizing,
      expanded: expandedId ? { [expandedId]: true } : {},
    },
    getRowId: planningRowKey,
    onSortingChange: (updater) => {
      const next = typeof updater === "function" ? updater(sorting) : updater;
      const selected = next[0];
      if (!selected) return;
      publishPlanningAction({ type: "sort_change", key: selected.id, direction: selected.desc ? "desc" : "asc" });
    },
    onColumnSizingChange: (updater) => {
      setColumnSizing((current) => {
        const next = typeof updater === "function" ? updater(current) : updater;
        savePlanningColumnSizing(next);
        return next;
      });
    },
    onExpandedChange: (updater) => {
      const current: ExpandedState = expandedId ? { [expandedId]: true } : {};
      const next = typeof updater === "function" ? updater(current) : updater;
      const expanded = next === true ? current : next;
      const newlyExpanded = Object.keys(expanded).find((key) => expanded[key] && !current[key]);
      setExpandedId(newlyExpanded || Object.keys(expanded).find((key) => expanded[key]) || "");
    },
    getRowCanExpand: () => true,
    getCoreRowModel: getCoreRowModel(),
    manualSorting: true,
    enableSortingRemoval: false,
    columnResizeMode: "onChange",
  });

  return (
    <SharedTableCard
      className="planning-react-table-card"
      ariaLabel="Planning worklist table"
      title="Planning worklist"
      subtitle={`Planning view · ${state.pagination.totalCount} total job${state.pagination.totalCount === 1 ? "" : "s"}`}
      count={state.pagination.totalCount}
      table={table}
      columns={columns}
      status={state.status}
      error={state.message}
      pagination={state.pagination}
      paginationLabel="Planning worklist"
      stickyColumnId="next_step"
      rowClassName={(row, index) => `planning-react-row ${index % 2 ? "is-alternate" : ""} ${row.getIsExpanded() ? "is-expanded" : ""}`.trim()}
      detailId={(row) => `planning-react-detail-${row.id}`}
      renderDetails={(row) => <PlanningDetails row={row.original} />}
      empty={(
        <div className="planning-react-empty">
          <strong>No planning rows match these filters</strong>
          <span>Clear the current filters to return to the complete planning worklist.</span>
          <button type="button" className={SHARED_NEUTRAL_CONTROL_CLASS} onClick={() => publishPlanningAction({ type: "clear_filters" })}>Clear filters</button>
        </div>
      )}
      onPageChange={(page) => publishPlanningAction({ type: "page_change", page })}
      onRetry={() => publishPlanningAction({ type: "retry" })}
    />
  );
}

const SUMMARY_CARDS = [
  { key: "total", label: "Total results", caption: "Across all result pages", help: "All planning rows matching the applied filters.", icon: ClipboardList },
  { key: "readyForReview", label: "Ready for review", caption: "On this page", help: "Rows on this page whose current recommendation is ready for review.", icon: CheckCircle2 },
  { key: "packetReady", label: "Packet ready", caption: "On this page", help: "Rows on this page with an explicitly ready planning packet.", icon: FileText },
  { key: "needsDecision", label: "Needs decision", caption: "Operator attention", help: "Rows on this page that do not yet have an operator decision.", icon: UserRoundCheck },
] as const;

export function PlanningSummary({ state }: { state: PlanningWorklistState }) {
  return (
    <section className="planning-react-summary-grid" aria-label="Planning summary">
      {SUMMARY_CARDS.map((card) => {
        const Icon = card.icon;
        return (
          <article className={`planning-react-summary-card planning-react-summary-card--${card.key}`} key={card.key}>
            <div className="planning-react-summary-topline">
              <span className="planning-react-summary-heading"><Icon size={18} aria-hidden="true" /><span>{card.label}</span></span>
              <SharedInfoPopover label={`About ${card.label.toLowerCase()}`}>{card.help}</SharedInfoPopover>
            </div>
            <strong>{state.metrics[card.key]}</strong>
            <span>{card.caption}</span>
          </article>
        );
      })}
    </section>
  );
}

declare global {
  interface Window {
    __APPLYLENS_PLANNING_WORKLIST_STATE__?: PlanningWorklistState;
  }
}
