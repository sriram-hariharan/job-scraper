import {
  type ColumnDef,
  type ColumnSizingState,
  type ExpandedState,
  type SortingState,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { BriefcaseBusiness, CheckCircle2, ClipboardCheck, FileText, FolderHeart, UsersRound } from "lucide-react";
import { type KeyboardEvent, useEffect, useMemo, useState } from "react";
import { SharedFilterSelect, type SharedFilterOption } from "./filter/FilterSelect";
import {
  SHARED_NEUTRAL_CONTROL_CLASS,
  SharedExpandedDetail,
  SharedExpansionButton,
  SharedInfoPopover,
  SharedTableCard,
  type SharedPaginationState,
} from "./table/TablePrimitives";

export const DECISIONS_STATE_EVENT = "applylens:decisions-dashboard-state";
export const DECISIONS_ACTION_EVENT = "applylens:decisions-dashboard-action";
export const DECISIONS_READY_EVENT = "applylens:decisions-dashboard-ready";
export const APPLICATIONS_STATE_EVENT = "applylens:applications-dashboard-state";
export const APPLICATIONS_ACTION_EVENT = "applylens:applications-dashboard-action";
export const APPLICATIONS_READY_EVENT = "applylens:applications-dashboard-ready";
export const DECISIONS_WIDTH_KEY = "applylens.decisions.columnWidths.v1";
export const APPLICATIONS_WIDTH_KEY = "applylens.applications.columnWidths.v1";

type Status = "loading" | "ready" | "error";
type Sort = { key: string; direction: "asc" | "desc" };
type RowData = Record<string, unknown>;
type DecisionsFilters = { decisions: string[]; companyContains: string; limit: number };
type ApplicationsFilters = { companyContains: string; titleContains: string; limit: number };

export type DecisionsState = {
  status: Status; rows: RowData[]; message?: string; metaLabel: string;
  pagination: SharedPaginationState; sort: Sort; filters: DecisionsFilters; resultKey: string;
};
export type ApplicationsState = {
  status: Status; rows: RowData[]; message?: string; metaLabel: string;
  pagination: SharedPaginationState; sort: Sort; filters: ApplicationsFilters; resultKey: string;
  activeTab: "APPLIED" | "SAVED";
};

export const DEFAULT_DECISIONS_STATE: DecisionsState = {
  status: "loading", rows: [], metaLabel: "Loading...", resultKey: "initial",
  pagination: { page: 1, pageSize: 15, totalCount: 0, totalPages: 1, hasPrevPage: false, hasNextPage: false },
  sort: { key: "", direction: "asc" }, filters: { decisions: [], companyContains: "", limit: 15 },
};
export const DEFAULT_APPLICATIONS_STATE: ApplicationsState = {
  status: "loading", rows: [], metaLabel: "Loading...", resultKey: "initial", activeTab: "APPLIED",
  pagination: { page: 1, pageSize: 15, totalCount: 0, totalPages: 1, hasPrevPage: false, hasNextPage: false },
  sort: { key: "", direction: "asc" }, filters: { companyContains: "", titleContains: "", limit: 15 },
};

const DECISION_OPTIONS: SharedFilterOption[] = ["APPLY", "TAILOR", "SKIP", "HOLD"].map((value) => ({ value, label: value }));
const clean = (value: unknown) => String(value ?? "").trim();
const shown = (value: unknown, fallback = "Unavailable") => clean(value) || fallback;
const date = (value: unknown) => {
  const raw = clean(value); if (!raw) return "Unavailable";
  const parsed = new Date(raw); return Number.isNaN(parsed.getTime()) ? raw : new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", year: "numeric", hour: "numeric", minute: "2-digit" }).format(parsed);
};
const rowKey = (row: RowData, index: number) => clean(row.action_key) || [
  clean(row.decision_timestamp || row.action_timestamp),
  clean(row.job_doc_id || row.job_url),
  clean(row.decision || row.application_status),
  index,
].join("|");
const sortState = (sort: Sort): SortingState => sort.key ? [{ id: sort.key, desc: sort.direction === "desc" }] : [];

function publish(name: string, detail: unknown) { window.dispatchEvent(new CustomEvent(name, { detail })); }
function readWidths(key: string): ColumnSizingState {
  try {
    const parsed = JSON.parse(localStorage.getItem(key) || "{}");
    const widths = parsed?.version === 1 ? parsed.widths : parsed;
    return widths && typeof widths === "object" && !Array.isArray(widths) ? widths : {};
  } catch { return {}; }
}
function saveWidths(key: string, widths: ColumnSizingState) { localStorage.setItem(key, JSON.stringify({ version: 1, widths })); }
function badge(value: unknown, prefix: string) {
  const raw = shown(value); const tone = clean(value).toLowerCase().replace(/[^a-z0-9]+/g, "-") || "unknown";
  return <span className={`${prefix}-badge ${prefix}-badge--${tone}`}>{raw}</span>;
}

function MetricGrid({ cards, label, loading = false }: { cards: Array<{ label: string; value: string | number; caption: string; help: string; icon: typeof ClipboardCheck }>; label: string; loading?: boolean }) {
  return <section className="operational-summary-grid" aria-label={label}>{cards.map(({ label: title, value, caption, help, icon: Icon }) => (
    <article className="operational-summary-card" key={title}>
      <div><span><Icon size={17} aria-hidden="true" />{title}</span><SharedInfoPopover label={`About ${title.toLowerCase()}`}>{help}</SharedInfoPopover></div>
      <strong>{loading ? "-" : value}</strong><small>{loading ? "Loading snapshot" : caption}</small>
    </article>
  ))}</section>;
}

function DecisionsFilters({ state }: { state: DecisionsState }) {
  const [filters, setFilters] = useState(state.filters);
  useEffect(() => setFilters(state.filters), [state.filters]);
  return <section className="operational-filter-card" aria-label="Decision filters"><div className="operational-filter-grid decisions-filter-grid">
    <SharedFilterSelect id="decisionFilter" label="Decision" options={DECISION_OPTIONS} values={filters.decisions} onChange={(decisions) => setFilters({ ...filters, decisions })} placeholder="All" allLabel="All" mode="multiple" />
    <label><span>Company contains</span><input id="decisionCompanyFilter" value={filters.companyContains} placeholder="e.g. Waymo" onChange={(event) => setFilters({ ...filters, companyContains: event.target.value })} /></label>
    <label><span>Limit</span><input id="decisionLimitInput" type="number" min={1} max={300} value={filters.limit} onChange={(event) => setFilters({ ...filters, limit: Math.min(300, Math.max(1, Number(event.target.value) || 15)) })} /></label>
    <div className="operational-filter-actions"><button id="decisionApplyFiltersBtn" className="operational-primary-action" onClick={() => publish(DECISIONS_ACTION_EVENT, { type: "apply_filters", filters })}>Apply Filters</button><button id="decisionClearFiltersBtn" className={`${SHARED_NEUTRAL_CONTROL_CLASS} operational-secondary-action`} onClick={() => publish(DECISIONS_ACTION_EVENT, { type: "clear_filters" })}>Clear</button></div>
  </div></section>;
}

function DecisionDetails({ row }: { row: RowData }) {
  return <SharedExpandedDetail><div className="operational-detail-grid">
    <div><span>Queue rank</span><strong>{shown(row.queue_rank)}</strong></div><div><span>Posted at</span><strong>{date(row.posted_at)}</strong></div>
    <div><span>Winner resume</span><strong title={clean(row.winner_resume)}>{shown(row.winner_resume)}</strong></div><div><span>Runner-up resume</span><strong title={clean(row.runner_up_resume)}>{shown(row.runner_up_resume)}</strong></div>
    <div><span>Selected resume</span><strong title={clean(row.selected_resume)}>{shown(row.selected_resume)}</strong></div><div><span>Note</span><strong>{shown(row.note, "No note recorded")}</strong></div>
  </div></SharedExpandedDetail>;
}

function decisionColumns(): ColumnDef<RowData>[] { return [
  { id: "expand", header: "", size: 42, minSize: 42, maxSize: 42, enableSorting: false, enableResizing: false, cell: ({ row }) => <SharedExpansionButton expanded={row.getIsExpanded()} label={`${row.getIsExpanded() ? "Collapse" : "Expand"} decision details for ${shown(row.original.job_title, "job")}`} controls={`decision-detail-${row.id}`} onClick={row.getToggleExpandedHandler()} /> },
  { id: "decision_timestamp", header: "Date / time", accessorFn: (row) => clean(row.decision_timestamp), size: 156, cell: ({ row }) => <time dateTime={clean(row.original.decision_timestamp)}>{date(row.original.decision_timestamp)}</time> },
  { id: "decision", header: "Decision", accessorFn: (row) => clean(row.decision), size: 118, cell: ({ row }) => badge(row.original.decision, "operational") },
  { id: "job", header: "Job", accessorFn: (row) => clean(row.job_title), size: 270, cell: ({ row }) => <span className="operational-job-cell"><strong>{shown(row.original.job_title, "Untitled job")}</strong><span>{shown(row.original.job_company, "Company unavailable")}</span></span> },
  { id: "planning_action", header: "Planning action", accessorFn: (row) => clean(row.planning_action), size: 150, cell: ({ row }) => shown(row.original.planning_action) },
  { id: "selected_resume", header: "Selected resume", accessorFn: (row) => clean(row.selected_resume), size: 220, cell: ({ row }) => <span className="operational-truncate" title={clean(row.original.selected_resume)}>{shown(row.original.selected_resume)}</span> },
  { id: "application_action", header: "Manual action", size: 150, minSize: 150, maxSize: 150, enableSorting: false, enableResizing: false, cell: ({ row }) => row.original.is_applied ? <button disabled className="operational-row-action is-complete">Applied</button> : <button className="operational-row-action" onClick={() => publish(DECISIONS_ACTION_EVENT, { type: "open_application", row: row.original })}>Open job</button> },
]; }

function DecisionsTable({ state }: { state: DecisionsState }) {
  const [columnSizing, setColumnSizing] = useState(() => readWidths(DECISIONS_WIDTH_KEY)); const [expandedId, setExpandedId] = useState("");
  const columns = useMemo(decisionColumns, []); const sorting = useMemo(() => sortState(state.sort), [state.sort]);
  useEffect(() => setExpandedId(""), [state.resultKey, state.pagination.page, state.sort]);
  const table = useReactTable({ data: state.rows, columns, state: { sorting, columnSizing, expanded: expandedId ? { [expandedId]: true } : {} }, getRowId: rowKey, getCoreRowModel: getCoreRowModel(), getSortedRowModel: getSortedRowModel(), getRowCanExpand: () => true, enableSortingRemoval: false, columnResizeMode: "onChange", onSortingChange: (updater) => { const next = typeof updater === "function" ? updater(sorting) : updater; const value = next[0]; if (value) publish(DECISIONS_ACTION_EVENT, { type: "sort_change", key: value.id, direction: value.desc ? "desc" : "asc" }); }, onColumnSizingChange: (updater) => setColumnSizing((current) => { const next = typeof updater === "function" ? updater(current) : updater; saveWidths(DECISIONS_WIDTH_KEY, next); return next; }), onExpandedChange: (updater) => { const current: ExpandedState = expandedId ? { [expandedId]: true } : {}; const next = typeof updater === "function" ? updater(current) : updater; const map = next === true ? current : next; setExpandedId(Object.keys(map).find((key) => map[key] && key !== expandedId) || Object.keys(map).find((key) => map[key]) || ""); } });
  return <SharedTableCard className="operational-table-card decisions-table-card" ariaLabel="Operator decisions table" title="Operator decisions" subtitle={`Decision history · ${state.pagination.totalCount} total records`} count={state.pagination.totalCount} table={table} columns={columns} status={state.status} error={state.message} pagination={state.pagination} paginationNoun="records" paginationLabel="Operator decisions" stickyColumnId="application_action" rowClassName={(_, index) => `operational-row ${index % 2 ? "is-alternate" : ""}`} detailId={(row) => `decision-detail-${row.id}`} renderDetails={(row) => <DecisionDetails row={row.original} />} empty={<div className="operational-empty"><strong>No operator decisions match the current filters.</strong><button className={SHARED_NEUTRAL_CONTROL_CLASS} onClick={() => publish(DECISIONS_ACTION_EVENT, { type: "clear_filters" })}>Clear filters</button></div>} onPageChange={(page) => publish(DECISIONS_ACTION_EVENT, { type: "page_change", page })} onRetry={() => publish(DECISIONS_ACTION_EVENT, { type: "retry" })} fillAvailableWidth deferPaginationWhileLoading />;
}

export function DecisionsDashboard({ state }: { state: DecisionsState }) {
  const pageRows = state.rows; const jobKeys = new Set(pageRows.map((row) => clean(row.job_doc_id || row.job_url || `${row.job_company}|${row.job_title}`)).filter(Boolean));
  const cards = [
    { label: "Total decisions", value: state.pagination.totalCount, caption: "Across filtered results", help: "All recorded decisions matching the applied filters.", icon: ClipboardCheck },
    { label: "Jobs touched", value: jobKeys.size, caption: "On this page", help: "Distinct jobs represented on the current page.", icon: BriefcaseBusiness },
    { label: "Apply decisions", value: pageRows.filter((row) => clean(row.decision).toUpperCase() === "APPLY").length, caption: "On this page", help: "Current-page decisions recorded as APPLY.", icon: CheckCircle2 },
    { label: "Tailor decisions", value: pageRows.filter((row) => clean(row.decision).toUpperCase() === "TAILOR").length, caption: "On this page", help: "Current-page decisions recorded as TAILOR.", icon: FileText },
  ];
  return <div className="operational-dashboard"><MetricGrid cards={cards} label="Decision summary" loading={state.status === "loading"} /><DecisionsFilters state={state} /><DecisionsTable state={state} /></div>;
}

function ApplicationsFilters({ state }: { state: ApplicationsState }) {
  const [filters, setFilters] = useState(state.filters); useEffect(() => setFilters(state.filters), [state.filters]);
  const selectTab = (tab: "APPLIED" | "SAVED") => { if (tab !== state.activeTab) publish(APPLICATIONS_ACTION_EVENT, { type: "tab_change", tab }); };
  const handleTabKeyDown = (event: KeyboardEvent<HTMLButtonElement>, tab: "APPLIED" | "SAVED") => {
    if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
    event.preventDefault(); selectTab(tab === "APPLIED" ? "SAVED" : "APPLIED");
  };
  const tabClass = (active: boolean) => `${SHARED_NEUTRAL_CONTROL_CLASS} applications-tab ${active ? "is-active" : "is-inactive"}`;
  return <section className="operational-filter-card applications-filter-card"><div className="applications-tabs" role="tablist" aria-label="Application view"><button role="tab" aria-selected={state.activeTab === "APPLIED"} tabIndex={state.activeTab === "APPLIED" ? 0 : -1} className={tabClass(state.activeTab === "APPLIED")} onKeyDown={(event) => handleTabKeyDown(event, "APPLIED")} onClick={() => selectTab("APPLIED")}>Applied Jobs</button><button role="tab" aria-selected={state.activeTab === "SAVED"} tabIndex={state.activeTab === "SAVED" ? 0 : -1} className={tabClass(state.activeTab === "SAVED")} onKeyDown={(event) => handleTabKeyDown(event, "SAVED")} onClick={() => selectTab("SAVED")}>Saved for Later</button></div><div className="operational-filter-grid applications-filter-grid">
    <label><span>Company contains</span><input id="applicationCompanyFilter" value={filters.companyContains} onChange={(event) => setFilters({ ...filters, companyContains: event.target.value })} /></label><label><span>Title contains</span><input id="applicationTitleFilter" value={filters.titleContains} onChange={(event) => setFilters({ ...filters, titleContains: event.target.value })} /></label><label><span>Limit</span><input id="applicationLimitInput" type="number" min={1} max={100} value={filters.limit} onChange={(event) => setFilters({ ...filters, limit: Math.min(100, Math.max(1, Number(event.target.value) || 15)) })} /></label><div className="operational-filter-actions"><button id="applicationApplyFiltersBtn" className="operational-primary-action" onClick={() => publish(APPLICATIONS_ACTION_EVENT, { type: "apply_filters", filters })}>Apply Filters</button><button id="applicationClearFiltersBtn" className={`${SHARED_NEUTRAL_CONTROL_CLASS} operational-secondary-action`} onClick={() => publish(APPLICATIONS_ACTION_EVENT, { type: "clear_filters" })}>Clear</button></div>
  </div></section>;
}

function ApplicationDetails({ row }: { row: RowData }) { return <SharedExpandedDetail><div className="operational-detail-grid"><div><span>Complete timestamp</span><strong>{date(row.action_timestamp)}</strong></div><div><span>Source view</span><strong>{shown(row.source_view)}</strong></div><div className="is-wide"><span>Note</span><strong>{shown(row.note, "No note recorded")}</strong></div></div></SharedExpandedDetail>; }
function applicationColumns(): ColumnDef<RowData>[] { return [
  { id: "expand", header: "", size: 42, minSize: 42, maxSize: 42, enableSorting: false, enableResizing: false, cell: ({ row }) => row.getCanExpand() ? <SharedExpansionButton expanded={row.getIsExpanded()} label={`${row.getIsExpanded() ? "Collapse" : "Expand"} application details for ${shown(row.original.job_title, "job")}`} controls={`application-detail-${row.id}`} onClick={row.getToggleExpandedHandler()} /> : null },
  { id: "action_timestamp", header: "Date / time", accessorFn: (row) => clean(row.action_timestamp), size: 156, cell: ({ row }) => <time>{date(row.original.action_timestamp)}</time> },
  { id: "job", header: "Job", accessorFn: (row) => clean(row.job_title), size: 300, cell: ({ row }) => <span className="operational-job-cell"><strong>{shown(row.original.job_title, "Untitled job")}</strong><span>{shown(row.original.job_company, "Company unavailable")}</span></span> },
  { id: "application_status", header: "Status", accessorFn: (row) => clean(row.application_status), size: 130, cell: ({ row }) => badge(row.original.application_status, "application") },
  { id: "source_view", header: "Source view", accessorFn: (row) => clean(row.source_view), size: 140, cell: ({ row }) => shown(row.original.source_view) },
  { id: "note", header: "Note", accessorFn: (row) => clean(row.note), size: 230, cell: ({ row }) => <span className="operational-truncate" title={clean(row.original.note)}>{shown(row.original.note, "No note")}</span> },
  { id: "open", header: "Open", size: 112, minSize: 112, maxSize: 112, enableSorting: false, enableResizing: false, cell: ({ row }) => { const href = clean(row.original.job_url || row.original.job_doc_id); return href ? <a className="operational-row-action" href={href} target="_blank" rel="noopener noreferrer">Open job</a> : <button className="operational-row-action" disabled>Unavailable</button>; } },
]; }

function ApplicationsTable({ state }: { state: ApplicationsState }) {
  const [columnSizing, setColumnSizing] = useState(() => readWidths(APPLICATIONS_WIDTH_KEY)); const [expandedId, setExpandedId] = useState(""); const columns = useMemo(applicationColumns, []); const sorting = useMemo(() => sortState(state.sort), [state.sort]);
  useEffect(() => setExpandedId(""), [state.resultKey, state.activeTab, state.pagination.page, state.sort]);
  const table = useReactTable({ data: state.rows, columns, state: { sorting, columnSizing, expanded: expandedId ? { [expandedId]: true } : {} }, getRowId: rowKey, getCoreRowModel: getCoreRowModel(), getSortedRowModel: getSortedRowModel(), getRowCanExpand: (row) => Boolean(clean(row.original.note)), enableSortingRemoval: false, columnResizeMode: "onChange", onSortingChange: (updater) => { const next = typeof updater === "function" ? updater(sorting) : updater; const value = next[0]; if (value) publish(APPLICATIONS_ACTION_EVENT, { type: "sort_change", key: value.id, direction: value.desc ? "desc" : "asc" }); }, onColumnSizingChange: (updater) => setColumnSizing((current) => { const next = typeof updater === "function" ? updater(current) : updater; saveWidths(APPLICATIONS_WIDTH_KEY, next); return next; }), onExpandedChange: (updater) => { const current: ExpandedState = expandedId ? { [expandedId]: true } : {}; const next = typeof updater === "function" ? updater(current) : updater; const map = next === true ? current : next; setExpandedId(Object.keys(map).find((key) => map[key] && key !== expandedId) || Object.keys(map).find((key) => map[key]) || ""); } });
  const label = state.activeTab === "APPLIED" ? "Applied Jobs" : "Saved for Later"; const empty = state.activeTab === "APPLIED" ? "No applied jobs yet." : "No jobs have been saved for later.";
  return <SharedTableCard className="operational-table-card applications-table-card" ariaLabel={`${label} table`} title={label} subtitle={`Application tracking · ${state.pagination.totalCount} total jobs`} count={state.pagination.totalCount} table={table} columns={columns} status={state.status} error={state.message} pagination={state.pagination} paginationLabel={label} stickyColumnId="open" rowClassName={(_, index) => `operational-row ${index % 2 ? "is-alternate" : ""}`} detailId={(row) => `application-detail-${row.id}`} renderDetails={(row) => <ApplicationDetails row={row.original} />} empty={<div className="operational-empty"><strong>{empty}</strong><span>{state.activeTab === "APPLIED" ? "Applied jobs will appear after an explicit manual status update." : "Jobs explicitly saved for later will appear here."}</span></div>} onPageChange={(page) => publish(APPLICATIONS_ACTION_EVENT, { type: "page_change", page })} onRetry={() => publish(APPLICATIONS_ACTION_EVENT, { type: "retry" })} fillAvailableWidth deferPaginationWhileLoading />;
}

export function ApplicationsDashboard({ state }: { state: ApplicationsState }) {
  const cards = [
    { label: "Current view", value: state.pagination.totalCount, caption: state.activeTab === "APPLIED" ? "Applied jobs" : "Saved jobs", help: "All jobs in the active view matching the applied filters.", icon: FolderHeart },
    { label: "Current page", value: state.rows.length, caption: "Visible jobs", help: "Jobs returned on the current server page.", icon: BriefcaseBusiness },
    { label: "With notes", value: state.rows.filter((row) => clean(row.note)).length, caption: "On this page", help: "Current-page jobs with a recorded operator note.", icon: FileText },
    { label: "Companies", value: new Set(state.rows.map((row) => clean(row.job_company)).filter(Boolean)).size, caption: "On this page", help: "Distinct companies represented on the current page.", icon: UsersRound },
  ];
  return <div className="operational-dashboard"><MetricGrid cards={cards} label="Application summary" loading={state.status === "loading"} /><ApplicationsFilters state={state} /><ApplicationsTable state={state} /></div>;
}

declare global { interface Window { __APPLYLENS_DECISIONS_STATE__?: DecisionsState; __APPLYLENS_APPLICATIONS_STATE__?: ApplicationsState; __APPLYLENS_DECISIONS_REACT_READY__?: boolean; __APPLYLENS_APPLICATIONS_REACT_READY__?: boolean; } }
