import {
  type ColumnDef,
  type ColumnSizingState,
  type SortingState,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import {
  Check,
  ChevronDown,
  Info,
  LoaderCircle,
  RotateCcw,
  Search,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  SHARED_NEUTRAL_CONTROL_CLASS,
  SharedExpandedDetail,
  SharedExpansionButton,
  SharedInfoPopover,
  SharedMatchMeter,
  SharedTableCard,
} from "./table/TablePrimitives";

/**
 * Adapted from Origin UI Table by Origin UI.
 * Sources:
 * - https://21st.dev/community/components/originui/table/card-table
 * - https://21st.dev/@originui/components/table/data-table-with-filters-made-with-tan-stack-table
 * - https://21st.dev/community/components/originui/table/example-of-a-more-complex-table-made-with-tan-stack-table
 * Adopted 2026-07-17. ApplyLens adaptations replace all sample data and actions
 * with the existing Executive queue bridge, filters, review flow, and row fields.
 */

export const QUEUE_STATE_EVENT = "applylens:executive-queue-state";
export const QUEUE_ACTION_EVENT = "applylens:executive-queue-action";
export const QUEUE_VIEW_MODE_STORAGE_KEY = "job_operator_executive_view_mode";
export const QUEUE_COLUMN_WIDTH_STORAGE_KEY = "queueTableColumnWidths";
export const QUEUE_REVIEW_COLUMN_WIDTH = 128;
export const QUEUE_SELECTED_RESUME_MIN_WIDTH = 220;

const NEUTRAL_CONTROL_CLASS = SHARED_NEUTRAL_CONTROL_CLASS;

export type QueueViewMode = "detailed" | "simple";

export type QueueRow = Record<string, unknown> & {
  queue_rank?: number | string;
  job_doc_id?: string;
  job_url?: string;
  job_title?: string;
  job_company?: string;
  job_location?: string;
  posted_at?: string;
  freshness_status?: string;
  action?: string;
  packet_generation_allowed?: boolean | string;
  winner_score?: number | string | null;
  operator_selected_resume?: string;
  winner_resume?: string;
  runner_up_resume?: string;
  score_gap?: number | string | null;
  missing_requirement_count?: number | string | null;
  operator_decision?: string;
  operator_review_lane?: string;
  queue_priority_reason?: string;
  application_label?: string;
  is_applied?: boolean;
  advisory_reason_codes?: string;
  tailoring_decision?: string;
  tailoring_reason_codes?: string;
  operator_review_reason_codes?: string;
};

export type PreferenceOption = {
  role_family_id: string;
  display_name: string;
};

export type QueueFilters = {
  actions: string[];
  preferenceIds: string[];
  undecidedOnly: boolean;
  limit: number;
};

export type QueuePagination = {
  page: number;
  pageSize: number;
  totalCount: number;
  totalPages: number;
  hasPrevPage: boolean;
  hasNextPage: boolean;
};

export type ExecutiveQueueState = {
  status: "loading" | "ready" | "error";
  rows: QueueRow[];
  metaLabel: string;
  message?: string;
  viewMode: QueueViewMode;
  filters: QueueFilters;
  preferenceOptions: PreferenceOption[];
  pagination: QueuePagination;
};

export type ExecutiveQueueAction =
  | { type: "apply_filters"; filters: QueueFilters }
  | { type: "clear_filters" }
  | { type: "page_change"; page: number }
  | { type: "retry" }
  | { type: "view_mode_change"; viewMode: QueueViewMode }
  | { type: "review"; row: QueueRow };

const DEFAULT_FILTERS: QueueFilters = {
  actions: [],
  preferenceIds: [],
  undecidedOnly: false,
  limit: 15,
};

export const DEFAULT_QUEUE_STATE: ExecutiveQueueState = {
  status: "loading",
  rows: [],
  metaLabel: "Loading...",
  viewMode: "detailed",
  filters: DEFAULT_FILTERS,
  preferenceOptions: [],
  pagination: {
    page: 1,
    pageSize: 15,
    totalCount: 0,
    totalPages: 1,
    hasPrevPage: false,
    hasNextPage: false,
  },
};

const ACTION_OPTIONS = [
  { value: "APPLY", label: "Ready for review" },
  { value: "APPLY_REVIEW_VARIANTS", label: "Review resume choice" },
  { value: "MAYBE_TAILOR", label: "Tailor first" },
  { value: "SKIP_FOR_NOW", label: "Review later" },
];

const PACKET_HELP = "A packet is a review bundle for this job. It includes the job, selected resume, match signals, gaps, and tailoring guidance. It does not apply to the job.";

function publishQueueAction(action: ExecutiveQueueAction) {
  window.dispatchEvent(new CustomEvent(QUEUE_ACTION_EVENT, { detail: action }));
}

function cleanText(value: unknown): string {
  return String(value ?? "").trim();
}

function formatAction(value: unknown): string {
  const normalized = cleanText(value).toUpperCase();
  return {
    APPLY: "Ready for review",
    APPLY_REVIEW_VARIANTS: "Review resume choice",
    MAYBE_TAILOR: "Tailor first",
    SKIP_FOR_NOW: "Review later",
  }[normalized] || cleanText(value) || "Unavailable";
}

function recommendationTone(value: unknown): string {
  return {
    APPLY: "ready",
    APPLY_REVIEW_VARIANTS: "choice",
    MAYBE_TAILOR: "tailor",
    SKIP_FOR_NOW: "later",
  }[cleanText(value).toUpperCase()] || "unavailable";
}

function formatPacket(value: unknown): string {
  const normalized = cleanText(value).toLowerCase();
  if (["true", "1", "yes", "y", "on"].includes(normalized)) return "Packet ready";
  if (["false", "0", "no", "n", "off"].includes(normalized)) return "No packet";
  return "Unavailable";
}

function formatDiagnostic(value: unknown): string {
  const normalized = cleanText(value).toLowerCase();
  return {
    no_deterministic_winner: "No clear resume match",
    borderline_deterministic_score: "Borderline match",
    tailoring_signal: "Tailoring may improve fit",
    tailoring_likely_worthwhile: "Tailoring may improve fit",
    packet_generation_blocked: "Packet unavailable",
    deterministic_equivalent_variants: "Close resume match",
    fallback_only_no_deterministic_match: "No credible resume match",
  }[normalized] || cleanText(value).replace(/_/g, " ");
}

function formatNextStep(row: QueueRow): string {
  const decision = cleanText(row.operator_decision).toUpperCase();
  const decisionLabel = {
    SELECT_RESUME: "Choose resume",
    MAYBE_TAILOR: "Tailor first",
    SKIP_FOR_NOW: "Review later",
    APPLY: "Ready for review",
    APPLY_REVIEW_VARIANTS: "Review resume choice",
  }[decision];
  if (decisionLabel) return decisionLabel;
  return {
    ready_to_apply: "Ready for review",
    tailor_then_apply: "Tailor then apply",
    review_before_action: "Review first",
    hold_or_skip: "Skip for now",
    source_watch: "Source watch",
  }[cleanText(row.operator_review_lane).toLowerCase()] || "—";
}

function formatResume(value: unknown): string {
  const raw = cleanText(value);
  return raw ? raw.replace(/\.pdf$/i, "").replace(/_/g, " ") : "—";
}

function numericScore(value: unknown): number | null {
  if (value === null || value === undefined || cleanText(value) === "") return null;
  const parsed = Number(cleanText(value).replace(/,/g, ""));
  if (!Number.isFinite(parsed)) return null;
  return Math.abs(parsed) <= 1 ? parsed * 100 : parsed;
}

function formatScore(value: unknown): string {
  const score = numericScore(value);
  return score === null ? "—" : score.toFixed(2);
}

function formatDate(value: unknown, freshnessStatus?: unknown): string {
  const raw = cleanText(value);
  if (!raw) return freshnessStatus === "unknown_timestamp_allowed" ? "Timestamp unavailable" : "—";
  const date = new Date(raw);
  if (Number.isNaN(date.getTime())) return raw;
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(date);
}

function rowKey(row: QueueRow, index: number): string {
  return cleanText(row.job_doc_id) || `${cleanText(row.queue_rank) || "row"}-${index}`;
}

function readColumnSizing(): ColumnSizingState {
  try {
    const parsed = JSON.parse(localStorage.getItem(QUEUE_COLUMN_WIDTH_STORAGE_KEY) || "{}");
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch {
    return {};
  }
}

function MultiSelect({
  label,
  options,
  values,
  onChange,
  placeholder,
  searchable = false,
  allLabel,
}: {
  label: string;
  options: Array<{ value: string; label: string }>;
  values: string[];
  onChange: (values: string[]) => void;
  placeholder: string;
  searchable?: boolean;
  allLabel?: string;
}) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const close = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, []);

  const normalized = query.trim().toLowerCase().replace(/[\/_-]+/g, " ").replace(/\s+/g, " ");
  const visible = options.filter((option) =>
    option.label.toLowerCase().replace(/[\/_-]+/g, " ").replace(/\s+/g, " ").includes(normalized),
  );
  const triggerLabel = values.length === 0 ? placeholder : values.length === 1
    ? options.find((option) => option.value === values[0])?.label || placeholder
    : `${values.length} selected`;

  return (
    <div className="executive-queue-multiselect" ref={rootRef}>
      <span className="executive-queue-field-label">{label}</span>
      <button
        type="button"
        className={`${NEUTRAL_CONTROL_CLASS} executive-queue-select-trigger`}
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
      >
        <span>{triggerLabel}</span>
        <ChevronDown size={15} aria-hidden="true" />
      </button>
      {open ? (
        <div className="executive-queue-select-menu" role="menu">
          {searchable ? (
            <label className="executive-queue-select-search">
              <span className="sr-only">Search {label.toLowerCase()}</span>
              <Search size={15} aria-hidden="true" />
              <input
                type="search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder={`Search ${label.toLowerCase()}`}
              />
            </label>
          ) : null}
          {allLabel && !normalized ? (
            <button
              type="button"
              className={`${NEUTRAL_CONTROL_CLASS} executive-queue-select-option ${values.length === 0 ? "is-selected" : ""}`}
              role="menuitemcheckbox"
              aria-checked={values.length === 0}
              onClick={() => onChange([])}
            >
              <Check size={15} aria-hidden="true" />
              <span>{allLabel}</span>
            </button>
          ) : null}
          {visible.map((option) => {
            const selected = values.includes(option.value);
            return (
              <button
                type="button"
                className={`${NEUTRAL_CONTROL_CLASS} executive-queue-select-option ${selected ? "is-selected" : ""}`}
                key={option.value}
                role="menuitemcheckbox"
                aria-checked={selected}
                onClick={() => onChange(
                  selected ? values.filter((value) => value !== option.value) : [...values, option.value],
                )}
              >
                <Check size={15} aria-hidden="true" />
                <span>{option.label}</span>
              </button>
            );
          })}
          {!visible.length ? <div className="executive-queue-select-empty">No preferences found</div> : null}
        </div>
      ) : null}
    </div>
  );
}

function QueueFiltersToolbar({ state }: { state: ExecutiveQueueState }) {
  const [filters, setFilters] = useState<QueueFilters>(state.filters);

  useEffect(() => setFilters(state.filters), [state.filters]);

  const preferenceOptions = state.preferenceOptions.map((option) => ({
    value: option.role_family_id,
    label: option.display_name || option.role_family_id,
  }));

  return (
    <section className="executive-queue-filter-card" aria-label="Queue filters">
      <div className="executive-queue-filter-grid">
        <MultiSelect
          label="Action"
          options={ACTION_OPTIONS}
          values={filters.actions}
          onChange={(actions) => setFilters((current) => ({ ...current, actions }))}
          placeholder="All actions"
        />
        <MultiSelect
          label="Preferences"
          options={preferenceOptions}
          values={filters.preferenceIds}
          onChange={(preferenceIds) => setFilters((current) => ({ ...current, preferenceIds }))}
          placeholder="All Preferences"
          allLabel="All Preferences"
          searchable
        />
        <label className="executive-queue-limit-field">
          <span className="executive-queue-field-label">Limit</span>
          <input
            type="number"
            min={1}
            max={200}
            value={filters.limit}
            onChange={(event) => setFilters((current) => ({
              ...current,
              limit: Math.min(200, Math.max(1, Number(event.target.value) || 15)),
            }))}
          />
        </label>
        <fieldset className="executive-queue-undecided-field">
          <legend>
            Undecided only
            <span title="Shows only browse rows without an operator decision.">
              <Info size={14} aria-label="Shows only browse rows without an operator decision." />
            </span>
          </legend>
          <div className="executive-queue-segmented">
            <button
              type="button"
              className={`${NEUTRAL_CONTROL_CLASS} ${!filters.undecidedOnly ? "is-active" : ""}`}
              aria-pressed={!filters.undecidedOnly}
              onClick={() => setFilters((current) => ({ ...current, undecidedOnly: false }))}
            >No</button>
            <button
              type="button"
              className={`${NEUTRAL_CONTROL_CLASS} ${filters.undecidedOnly ? "is-active" : ""}`}
              aria-pressed={filters.undecidedOnly}
              onClick={() => setFilters((current) => ({ ...current, undecidedOnly: true }))}
            >Yes</button>
          </div>
        </fieldset>
      </div>
      <div className="executive-queue-filter-actions">
        <button type="button" className={`${NEUTRAL_CONTROL_CLASS} executive-queue-clear-btn`} onClick={() => publishQueueAction({ type: "clear_filters" })}>
          <RotateCcw size={15} aria-hidden="true" /> Clear
        </button>
        <button type="button" className="executive-queue-apply-btn" onClick={() => publishQueueAction({ type: "apply_filters", filters })}>
          Apply Filters
        </button>
      </div>
    </section>
  );
}

function QueueDetails({ row }: { row: QueueRow }) {
  return (
    <SharedExpandedDetail>
      <div className="executive-queue-details executive-queue-details--neutral">
      <div><span>Priority reason</span><strong>{formatDiagnostic(row.queue_priority_reason) || "—"}</strong></div>
      <div><span>Next step</span><strong>{formatNextStep(row)}</strong></div>
      <div><span>Selected resume</span><strong>{formatResume(row.operator_selected_resume || row.winner_resume)}</strong></div>
      <div><span>Runner-up</span><strong>{formatResume(row.runner_up_resume)}</strong></div>
      <div><span>Score gap</span><strong>{cleanText(row.score_gap) || "—"}</strong></div>
      <div><span>Missing requirements</span><strong>{cleanText(row.missing_requirement_count) || "0"}</strong></div>
      <p><Info size={14} aria-hidden="true" /> {PACKET_HELP}</p>
      </div>
    </SharedExpandedDetail>
  );
}

function buildColumns(mode: QueueViewMode): ColumnDef<QueueRow>[] {
  const expand: ColumnDef<QueueRow> = {
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
        label={`${row.getIsExpanded() ? "Collapse" : "Expand"} details for ${cleanText(row.original.job_title) || "job"}`}
        controls={`executive-queue-detail-${row.id}`}
        className="executive-queue-expand-btn"
        onClick={row.getToggleExpandedHandler()}
      />
    ),
  };
  const review: ColumnDef<QueueRow> = {
    id: "review",
    header: "Review",
    size: QUEUE_REVIEW_COLUMN_WIDTH,
    minSize: QUEUE_REVIEW_COLUMN_WIDTH,
    maxSize: QUEUE_REVIEW_COLUMN_WIDTH,
    enableSorting: false,
    enableResizing: false,
    cell: ({ row }) => (
      <button
        type="button"
        className="executive-queue-review-btn"
        disabled={Boolean(row.original.is_applied)}
        aria-label={`Review ${cleanText(row.original.job_title) || "job"}`}
        onClick={() => publishQueueAction({ type: "review", row: row.original })}
      >
        {row.original.is_applied ? "Reviewed" : "Review"}
      </button>
    ),
  };
  const base: ColumnDef<QueueRow>[] = [
    expand,
    { accessorKey: "queue_rank", header: "Rank", size: 86, minSize: 72, sortingFn: "basic" },
    {
      id: "job_title",
      header: mode === "simple" ? "Job title / company" : "Job title",
      size: mode === "simple" ? 300 : 250,
      minSize: 210,
      accessorFn: (row) => `${cleanText(row.job_title)} ${cleanText(row.job_company)}`,
      cell: ({ row }) => (
        <div className="executive-queue-job-cell">
          <a href={cleanText(row.original.job_url || row.original.job_doc_id) || undefined} target="_blank" rel="noreferrer">
            {cleanText(row.original.job_title) || "Untitled job"}
          </a>
          {mode === "simple" ? <span>{cleanText(row.original.job_company) || "—"}</span> : null}
          <small>{cleanText(row.original.job_location) || "Location unavailable"}</small>
        </div>
      ),
    },
    ...(mode === "detailed" ? [
      { accessorKey: "job_company", header: "Company", size: 170, minSize: 130 },
      { accessorKey: "job_location", header: "Location", size: 170, minSize: 130 },
    ] as ColumnDef<QueueRow>[] : []),
    {
      id: "posted_at",
      header: "Posted at",
      size: 142,
      minSize: 120,
      accessorFn: (row) => row.posted_at ? new Date(row.posted_at).getTime() : null,
      sortUndefined: "last",
      cell: ({ row }) => formatDate(row.original.posted_at, row.original.freshness_status),
    },
    {
      id: "recommendation",
      header: "Recommendation",
      size: 180,
      minSize: 150,
      accessorFn: (row) => formatAction(row.action),
      cell: ({ row }) => (
        <span className={`executive-queue-badge executive-queue-badge--${recommendationTone(row.original.action)}`}>
          {formatAction(row.original.action)}
        </span>
      ),
    },
    {
      id: "packet_status",
      header: () => <span className="executive-queue-packet-head">Packet <SharedInfoPopover label="About review packets">{PACKET_HELP}</SharedInfoPopover></span>,
      size: 138,
      minSize: 120,
      accessorFn: (row) => formatPacket(row.packet_generation_allowed),
      cell: ({ row }) => (
        <span className={`executive-queue-badge executive-queue-badge--packet ${formatPacket(row.original.packet_generation_allowed) === "Packet ready" ? "is-ready" : ""}`}>
          {formatPacket(row.original.packet_generation_allowed)}
        </span>
      ),
    },
    {
      id: "winner_score",
      header: "Match",
      size: 132,
      minSize: 112,
      accessorFn: (row) => numericScore(row.winner_score),
      sortUndefined: "last",
      cell: ({ row }) => <SharedMatchMeter value={row.original.winner_score} unavailableLabel="—" className="executive-queue-match" />,
    },
    {
      id: "selected_resume",
      header: "Selected Resume",
      size: 240,
      minSize: QUEUE_SELECTED_RESUME_MIN_WIDTH,
      accessorFn: (row) => cleanText(row.operator_selected_resume || row.winner_resume),
      cell: ({ row }) => (
        <span
          className="executive-queue-selected-resume-value"
          title={cleanText(row.original.operator_selected_resume || row.original.winner_resume)}
        >
          {formatResume(row.original.operator_selected_resume || row.original.winner_resume)}
        </span>
      ),
    },
    ...(mode === "detailed" ? [
      {
        id: "runner_up_resume",
        header: "Runner-up resume",
        size: 210,
        minSize: 170,
        accessorFn: (row: QueueRow) => cleanText(row.runner_up_resume),
        cell: ({ row }: { row: { original: QueueRow } }) => <span title={cleanText(row.original.runner_up_resume)}>{formatResume(row.original.runner_up_resume)}</span>,
      },
      { accessorKey: "score_gap", header: "Score gap", size: 108, minSize: 94, sortUndefined: "last" },
      { accessorKey: "missing_requirement_count", header: "Missing req count", size: 138, minSize: 120, sortUndefined: "last" },
      { id: "next_step", header: "Next step", size: 160, minSize: 130, accessorFn: (row: QueueRow) => formatNextStep(row) },
      { id: "queue_priority_reason", header: "Priority reason", size: 180, minSize: 150, accessorFn: (row: QueueRow) => formatDiagnostic(row.queue_priority_reason) || "—" },
    ] as ColumnDef<QueueRow>[] : []),
    review,
  ];
  return base;
}

function QueueTable({ state }: { state: ExecutiveQueueState }) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnSizing, setColumnSizing] = useState<ColumnSizingState>(readColumnSizing);
  const [expandedId, setExpandedId] = useState<string>("");
  const columns = useMemo(() => buildColumns(state.viewMode), [state.viewMode]);
  const rows = useMemo(() => state.rows.slice(), [state.rows]);

  useEffect(() => setExpandedId(""), [state.rows, state.pagination.page, state.viewMode]);

  const table = useReactTable({
    data: rows,
    columns,
    state: {
      sorting,
      columnSizing,
      expanded: expandedId ? { [expandedId]: true } : {},
    },
    getRowId: (row, index) => rowKey(row, index),
    onSortingChange: setSorting,
    onColumnSizingChange: (updater) => {
      setColumnSizing((current) => {
        const next = typeof updater === "function" ? updater(current) : updater;
        localStorage.setItem(QUEUE_COLUMN_WIDTH_STORAGE_KEY, JSON.stringify(next));
        return next;
      });
    },
    onExpandedChange: (updater) => {
      const current = expandedId ? { [expandedId]: true } : {};
      const next = typeof updater === "function" ? updater(current) : updater;
      const expandedRows = next === true ? current : next;
      const newlyExpanded = Object.keys(expandedRows).find((key) => expandedRows[key] && !current[key]);
      setExpandedId(newlyExpanded || Object.keys(expandedRows).find((key) => expandedRows[key]) || "");
    },
    getRowCanExpand: () => true,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    enableSortingRemoval: false,
    columnResizeMode: "onChange",
  });

  const viewToggle = (
    <div className="executive-queue-view-toggle" role="radiogroup" aria-label="Executive view mode">
      {(["detailed", "simple"] as QueueViewMode[]).map((mode) => (
        <button
          type="button"
          role="radio"
          aria-checked={state.viewMode === mode}
          className={`${NEUTRAL_CONTROL_CLASS} ${state.viewMode === mode ? "is-active" : ""}`}
          key={mode}
          onClick={() => publishQueueAction({ type: "view_mode_change", viewMode: mode })}
        >{mode === "detailed" ? "Detailed" : "Simple"}</button>
      ))}
    </div>
  );

  return (
    <SharedTableCard
      className={`executive-queue-table-card executive-queue-table-card--${state.viewMode}`}
      ariaLabel="Executive queue table"
      title="Queue Table"
      subtitle={state.metaLabel}
      count={state.pagination.totalCount}
      table={table}
      columns={columns}
      status={state.status}
      error={state.message}
      headerActions={viewToggle}
      pagination={state.pagination}
      paginationLabel="Executive queue"
      stickyColumnId="review"
      rowClassName={(row) => `executive-queue-row ${row.getIsExpanded() ? "is-expanded" : ""}`.trim()}
      detailId={(row) => `executive-queue-detail-${row.id}`}
      renderDetails={(row) => <QueueDetails row={row.original} />}
      empty={(
        <div className="executive-queue-empty">
          <strong>No jobs match these filters</strong>
          <span>Clear filters to return to the complete Executive queue.</span>
          <button type="button" className={NEUTRAL_CONTROL_CLASS} onClick={() => publishQueueAction({ type: "clear_filters" })}>Clear Filters</button>
        </div>
      )}
      onPageChange={(page) => publishQueueAction({ type: "page_change", page })}
      onRetry={() => publishQueueAction({ type: "retry" })}
    />
  );
}

export function ExecutiveQueue({ state }: { state: ExecutiveQueueState }) {
  return (
    <div className={`executive-queue-dashboard executive-queue-dashboard--${state.viewMode}`}>
      <QueueFiltersToolbar state={state} />
      <QueueTable state={state} />
    </div>
  );
}

declare global {
  interface Window {
    __APPLYLENS_EXECUTIVE_QUEUE_STATE__?: ExecutiveQueueState;
  }
}
