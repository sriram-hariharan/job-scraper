import {
  type ColumnDef,
  type ColumnSizingState,
  type ExpandedState,
  type SortingState,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { AlertCircle, CheckCircle2, ClipboardList, FileText, RotateCcw, Search, Sparkles, UserRoundCheck, X } from "lucide-react";
import { useEffect, useId, useMemo, useRef, useState } from "react";
import { SharedFilterSelect, type SharedFilterOption } from "./filter/FilterSelect";
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

export type PlanningFilters = {
  actions: string[];
  winnerBuckets: string[];
  tailoringStates: string[];
  preferenceIds: string[];
  undecidedOnly: boolean;
  limit: number;
};

export type PlanningPreferenceOption = {
  role_family_id: string;
  display_name: string;
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
  filters: PlanningFilters;
  preferenceOptions: PlanningPreferenceOption[];
  bulkSuggestions: {
    eligibleCount: number;
    available: boolean;
    isRunning: boolean;
    /** Presentation mirror of the canonical server progress. */
    total?: number;
    completed?: number;
    needsAttention?: number;
    remaining?: number;
    currentLabel?: string;
    stopRequested?: boolean;
    verified?: boolean;
    items?: { label: string; status: string; outcome?: string }[];
    /**
     * Terminal Bulk result history for the CURRENT Live Pipeline run. The
     * bridge publishes both pipeline ids so presentation can tell a result
     * that belongs to this job set from a stale one without guessing.
     */
    currentPipelineRunId?: string;
    resultPipelineRunId?: string;
    hasResults?: boolean;
    latestRunId?: string;
    latestStatus?: string;
    lastFinishedAt?: string;
    processedCount?: number;
    generatedCount?: number;
    rerunnableCount?: number;
    resultLoadStatus?: "idle" | "loading" | "ready" | "error";
    resultItems?: BulkResultItem[];
    brandfetchClientId?: string;
  };
};

/**
 * One job's latest Bulk Generate attempt for the current pipeline run, already
 * joined by the bridge against current Planning row metadata on stable
 * identity. Bulk history owns the attempt fields; Planning owns the job fields.
 */
export type BulkResultItem = {
  job_identity: string;
  job_doc_id?: string;
  queue_rank?: string;
  job_label?: string;
  selected_resume?: string;
  status?: string;
  outcome?: string;
  error_category?: string;
  error_message?: string;
  finished_at?: string;
  attempt_count?: number;
  rerunnable?: boolean;
  /** Merged from the current Planning row. */
  job_title?: string;
  job_company?: string;
  job_location?: string;
  company_domain?: string;
  winner_resume?: string;
  winner_score?: number | string | null;
  runner_up_resume?: string;
  runnerup_resume?: string;
  runner_up_score?: number | string | null;
  runnerup_score?: number | string | null;
  match_score?: number | string | null;
};

export type PlanningWorklistAction =
  | { type: "page_change"; page: number }
  | { type: "sort_change"; key: string; direction: "asc" | "desc" }
  | { type: "retry" }
  | { type: "filters_change"; filters: PlanningFilters }
  | { type: "apply_filters"; filters: PlanningFilters }
  | { type: "clear_filters" }
  | { type: "bulk_generate_suggestions" }
  | { type: "bulk_stop_after_current" }
  | { type: "bulk_view_results" }
  | { type: "bulk_rerun"; scope: "selected" | "eligible"; jobIdentities: string[] }
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
  filters: {
    actions: [],
    winnerBuckets: [],
    tailoringStates: [],
    preferenceIds: [],
    undecidedOnly: false,
    limit: 15,
  },
  preferenceOptions: [],
  bulkSuggestions: { eligibleCount: 0, available: false, isRunning: false },
};

export const PLANNING_BULK_RUN_TOOLTIP = "Bulk Generate running. Click to view.";

function boundedBulkJobLabel(label: string): string {
  const clean = String(label || "").trim();
  if (clean.length <= 80) return clean;
  return `${clean.slice(0, 79)}…`;
}

const BULK_ITEM_PRESENTATION: Record<string, { icon: string; label: string; tone: string }> = {
  success: { icon: "✓", label: "Completed", tone: "done" },
  succeeded: { icon: "✓", label: "Completed", tone: "done" },
  needs_attention: { icon: "!", label: "Needs attention", tone: "attention" },
  running: { icon: "◌", label: "Running", tone: "running" },
  pending: { icon: "○", label: "Pending", tone: "pending" },
};

function bulkItemPresentation(status: string) {
  return BULK_ITEM_PRESENTATION[status] || BULK_ITEM_PRESENTATION.pending;
}

/* ------------------------------------------------------------------ *
 * Bulk generation results + re-run center
 *
 * Composition references (visual/interaction only, no dependencies added):
 *  - 21st.dev "Contacts Table With Modal" by Isaiah — table workspace, search,
 *    filter pills, row composition, scroll treatment.
 *  - 21st.dev "Leads Data Table" by Isaiah — checkbox selection, selected-row
 *    highlight, sticky bulk action bar, selected-count feedback.
 *  - 21st.dev "Dialog" (ReUI) by Sean Hello — large dialog shell, header
 *    hierarchy, scroll boundaries, close + focus treatment, footer separation.
 * ------------------------------------------------------------------ */

/** User-facing status vocabulary. Never collapses distinct outcomes. */
const BULK_RESULT_PRESENTATION: Record<string, { label: string; tone: string }> = {
  generated: { label: "Ready rewrites", tone: "ready" },
  no_safe_rewrites: { label: "Safe / no rewrite", tone: "neutral" },
  empty: { label: "No usable rewrite", tone: "info" },
  failed: { label: "Failed", tone: "attention" },
};

export function bulkResultPresentation(item: BulkResultItem): { label: string; tone: string } {
  const outcome = String(item.outcome || "").trim();
  if (String(item.status || "").trim() === "needs_attention" && outcome !== "failed") {
    return { label: "Needs attention", tone: "attention" };
  }
  return BULK_RESULT_PRESENTATION[outcome] || { label: "Needs attention", tone: "attention" };
}

export function normalizeCompanyName(value: string): string {
  return String(value || "")
    .toLowerCase()
    .replace(/[.,]/g, " ")
    .replace(/\b(inc|llc|ltd|corp|corporation|co|gmbh|plc|sa|bv)\b/g, " ")
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

/** "Today 7:42 PM" / "Sep 7, 11:08 PM". Never manufactured. */
export function formatBulkTimestamp(value?: string): string {
  const raw = String(value || "").trim();
  if (!raw) return "—";
  const parsed = new Date(raw);
  if (Number.isNaN(parsed.getTime())) return "—";
  const time = parsed.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
  const today = new Date();
  const sameDay =
    parsed.getFullYear() === today.getFullYear() &&
    parsed.getMonth() === today.getMonth() &&
    parsed.getDate() === today.getDate();
  if (sameDay) return `Today ${time}`;
  const day = parsed.toLocaleDateString(undefined, { month: "short", day: "numeric" });
  return `${day}, ${time}`;
}

function normalizeBulkResumeName(value: unknown): string {
  return String(value || "")
    .trim()
    .replace(/\\/g, "/")
    .split("/")
    .pop()
    ?.trim() || "";
}

function numericBulkScore(value: unknown): number | null {
  if (value === null || value === undefined || String(value).trim() === "") return null;
  const score = Number(value);
  return Number.isFinite(score) ? score : null;
}

/** Score paired with the resume Bulk actually selected; never a different candidate's score. */
export function bulkResultMatchScore(item: BulkResultItem): number | null {
  const selected = normalizeBulkResumeName(item.selected_resume);
  if (!selected) return null;

  const winner = normalizeBulkResumeName(item.winner_resume);
  if (winner && selected === winner) return numericBulkScore(item.winner_score);

  const runnerUp = normalizeBulkResumeName(item.runner_up_resume || item.runnerup_resume);
  if (runnerUp && selected === runnerUp) {
    return numericBulkScore(item.runner_up_score ?? item.runnerup_score);
  }

  // A score without a matching candidate name is not enough evidence to pair
  // it with the selected resume.
  return null;
}

export function formatBulkMatchScore(item: BulkResultItem): string {
  const score = bulkResultMatchScore(item);
  if (score === null) return "—";
  const percent = Math.abs(score) <= 1 ? score * 100 : score;
  // Two decimals matches the Planning worklist's own match-score convention
  // (SharedMatchMeter formats with toFixed(2)).
  return `${percent.toFixed(2)}%`;
}

function lettermark(company: string): string {
  const clean = String(company || "").trim();
  if (!clean) return "?";
  const words = clean.split(/\s+/).filter(Boolean);
  if (words.length >= 2) return `${words[0][0]}${words[1][0]}`.toUpperCase();
  return clean.slice(0, 2).toUpperCase();
}

/**
 * Company logo presentation only. The React island performs no network calls:
 * planning.js owns every request, resolves company -> employer domain once per
 * company for the page lifetime, and publishes `company_domain` on each result
 * item. Here we only render the Brandfetch CDN image for an already-resolved
 * domain, and fall back to a deterministic local lettermark otherwise, so the
 * layout never breaks when Brandfetch is unavailable or unconfigured.
 */
export function CompanyLogo({
  company,
  domain,
  clientId,
}: {
  company: string;
  domain?: string;
  clientId?: string;
}) {
  const resolved = String(domain || "").trim();
  const client = String(clientId || "").trim();
  const [failed, setFailed] = useState(false);

  useEffect(() => setFailed(false), [resolved, client]);

  const showImage = Boolean(resolved) && Boolean(client) && !failed;
  return (
    <span className="planning-bulk-results__logo" aria-hidden="true">
      {showImage ? (
        <img
          src={`https://cdn.brandfetch.io/domain/${encodeURIComponent(resolved)}/w/64/h/64/fallback/lettermark/type/icon?c=${encodeURIComponent(client)}`}
          alt=""
          width={32}
          height={32}
          loading="lazy"
          onError={() => setFailed(true)}
        />
      ) : (
        <span className="planning-bulk-results__lettermark">{lettermark(company)}</span>
      )}
    </span>
  );
}

type BulkResultFilterId = "all" | "generated" | "no_safe_rewrites" | "attention";

/** Semantic tone; drives each pill's own default background in both themes. */
export type BulkResultFilterTone = "all" | "generated" | "safe" | "attention";

const BULK_RESULT_FILTERS: {
  id: BulkResultFilterId;
  label: string;
  tone: BulkResultFilterTone;
  match: (item: BulkResultItem) => boolean;
}[] = [
  { id: "all", label: "All", tone: "all", match: () => true },
  {
    id: "generated",
    label: "Generated / Ready",
    tone: "generated",
    match: (item) => item.outcome === "generated",
  },
  {
    id: "no_safe_rewrites",
    label: "Safe / no rewrite",
    tone: "safe",
    match: (item) => item.outcome === "no_safe_rewrites",
  },
  {
    id: "attention",
    label: "Failed / attention",
    tone: "attention",
    match: (item) => item.outcome === "failed" || item.status === "needs_attention",
  },
];

/** Large Bulk generation results workspace. Presentation only. */
export function BulkResultsDialog({
  bulk,
  onClose,
  onRerun,
}: {
  bulk: PlanningWorklistState["bulkSuggestions"];
  onClose: () => void;
  onRerun: (scope: "selected" | "eligible", jobIdentities: string[]) => void;
}) {
  const titleId = useId();
  const descriptionId = useId();
  const panelRef = useRef<HTMLDivElement>(null);
  const [query, setQuery] = useState("");
  const [filterId, setFilterId] = useState<BulkResultFilterId>("all");
  const [selected, setSelected] = useState<string[]>([]);

  const items = useMemo(
    () => (Array.isArray(bulk.resultItems) ? bulk.resultItems : []),
    [bulk.resultItems],
  );
  const datasetKey = `${bulk.resultPipelineRunId || ""}|${items.length}|${bulk.latestRunId || ""}`;
  // Selection survives harmless re-renders; it resets only when the pipeline or
  // the result dataset materially changes.
  useEffect(() => {
    setSelected([]);
    setQuery("");
    setFilterId("all");
  }, [datasetKey]);

  useEffect(() => {
    const focusTarget = panelRef.current?.querySelector<HTMLElement>("[data-autofocus]");
    (focusTarget || panelRef.current)?.focus();
  }, []);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.stopPropagation();
        onClose();
        return;
      }
      if (event.key !== "Tab" || !panelRef.current) return;
      const focusables = Array.from(
        panelRef.current.querySelectorAll<HTMLElement>(
          'button:not([disabled]), input:not([disabled]), [href], select, textarea, [tabindex]:not([tabindex="-1"])',
        ),
      ).filter((node) => node.offsetParent !== null || node === document.activeElement);
      if (!focusables.length) return;
      const first = focusables[0];
      const last = focusables[focusables.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", onKeyDown, true);
    return () => document.removeEventListener("keydown", onKeyDown, true);
  }, [onClose]);

  const searched = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return items;
    return items.filter((item) => {
      const title = String(item.job_title || item.job_label || "").toLowerCase();
      const company = String(item.job_company || "").toLowerCase();
      return title.includes(needle) || company.includes(needle);
    });
  }, [items, query]);

  const activeFilter = BULK_RESULT_FILTERS.find((entry) => entry.id === filterId) || BULK_RESULT_FILTERS[0];
  const visible = useMemo(() => searched.filter(activeFilter.match), [searched, activeFilter]);
  const visibleEligible = useMemo(() => visible.filter((item) => item.rerunnable), [visible]);
  const allEligible = useMemo(() => items.filter((item) => item.rerunnable), [items]);

  const generatedCount = items.filter((item) => item.outcome === "generated").length;
  const attentionCount = items.filter(
    (item) => item.outcome === "failed" || item.status === "needs_attention",
  ).length;

  const selectedSet = new Set(selected);
  const selectedVisibleEligible = visibleEligible.filter((item) => selectedSet.has(item.job_identity));
  const allVisibleEligibleSelected =
    visibleEligible.length > 0 && selectedVisibleEligible.length === visibleEligible.length;

  const toggleRow = (identity: string) => {
    setSelected((current) =>
      current.includes(identity) ? current.filter((value) => value !== identity) : [...current, identity],
    );
  };

  const toggleAllEligible = () => {
    if (allVisibleEligibleSelected) {
      const visibleIds = new Set(visibleEligible.map((item) => item.job_identity));
      setSelected((current) => current.filter((value) => !visibleIds.has(value)));
      return;
    }
    setSelected((current) => {
      const merged = new Set(current);
      visibleEligible.forEach((item) => merged.add(item.job_identity));
      return Array.from(merged);
    });
  };

  const pipelineLabel = String(bulk.resultPipelineRunId || bulk.currentPipelineRunId || "");
  const shortPipeline = pipelineLabel.length > 18 ? `${pipelineLabel.slice(0, 17)}…` : pipelineLabel;

  return (
    <div className="planning-bulk-results__backdrop" role="presentation">
      <div
        className="planning-bulk-results"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={descriptionId}
        ref={panelRef}
        tabIndex={-1}
      >
        <header className="planning-bulk-results__head">
          <span className="planning-bulk-results__head-icon" aria-hidden="true">
            <Sparkles size={18} strokeWidth={2} />
          </span>
          <div className="planning-bulk-results__head-text">
            <h2 id={titleId}>Bulk generation results</h2>
            <p id={descriptionId}>
              Review completed jobs, search the current job set, and choose what to re-run.
            </p>
          </div>
          <div className="planning-bulk-results__head-meta">
            <span>{`Last run ${formatBulkTimestamp(bulk.lastFinishedAt)}`}</span>
            {pipelineLabel ? (
              <span title={pipelineLabel}>{`Live Pipeline: ${shortPipeline}`}</span>
            ) : null}
          </div>
          <button
            type="button"
            className="planning-bulk-results__close"
            aria-label="Close bulk generation results"
            onClick={onClose}
          >
            <X size={22} strokeWidth={2} aria-hidden="true" />
          </button>
        </header>

        <section className="planning-bulk-results__cards" aria-label="Bulk generation summary">
          <article className="planning-bulk-results__card is-success">
            <span className="planning-bulk-results__card-icon" aria-hidden="true">
              <CheckCircle2 size={18} strokeWidth={2.2} />
            </span>
            <div className="planning-bulk-results__card-body">
              <p className="planning-bulk-results__card-metric">
                <strong>{generatedCount}</strong>
                <span className="planning-bulk-results__card-label">Generated</span>
              </p>
              <small>Jobs with ready rewrites</small>
            </div>
          </article>
          <article className="planning-bulk-results__card is-attention">
            <span className="planning-bulk-results__card-icon" aria-hidden="true">
              <AlertCircle size={18} strokeWidth={2.2} />
            </span>
            <div className="planning-bulk-results__card-body">
              <p className="planning-bulk-results__card-metric">
                <strong>{attentionCount}</strong>
                <span className="planning-bulk-results__card-label">Failed</span>
              </p>
              <small>Could not generate suggestions</small>
            </div>
          </article>
          <article className="planning-bulk-results__card is-rerun">
            <span className="planning-bulk-results__card-icon" aria-hidden="true">
              <RotateCcw size={18} strokeWidth={2.2} />
            </span>
            <div className="planning-bulk-results__card-body">
              <p className="planning-bulk-results__card-metric">
                <strong>{allEligible.length}</strong>
                <span className="planning-bulk-results__card-label">Eligible to re-run</span>
              </p>
              <small>Can be re-run with current settings</small>
            </div>
          </article>
        </section>

        <section className="planning-bulk-results__controls">
          <label className="planning-bulk-results__search">
            <Search size={14} strokeWidth={2} aria-hidden="true" />
            <input
              type="search"
              className="planning-bulk-results__search-input"
              data-autofocus
              value={query}
              placeholder="Search jobs or companies…"
              aria-label="Search jobs or companies"
              onChange={(event) => setQuery(event.target.value)}
            />
          </label>
          <div className="planning-bulk-results__pills" role="group" aria-label="Filter results">
            {BULK_RESULT_FILTERS.map((entry) => {
              const count = searched.filter(entry.match).length;
              return (
                <button
                  key={entry.id}
                  type="button"
                  className={`planning-bulk-results__pill is-tone-${entry.tone}${entry.id === filterId ? " is-active" : ""}`}
                  aria-pressed={entry.id === filterId}
                  onClick={() => setFilterId(entry.id)}
                >
                  {entry.label}
                  <small>{count}</small>
                </button>
              );
            })}
          </div>
          <label className="planning-bulk-results__select-all">
            <input
              type="checkbox"
              className="planning-bulk-results__checkbox"
              checked={allVisibleEligibleSelected}
              disabled={visibleEligible.length === 0}
              onChange={toggleAllEligible}
            />
            <span>Select all eligible</span>
          </label>
        </section>

        <div className="planning-bulk-results__table-wrap">
          <table className="planning-bulk-results__table">
            <thead>
              <tr>
                <th scope="col" className="planning-bulk-results__col-check">
                  <span className="sr-only">Select</span>
                </th>
                <th scope="col">Job</th>
                <th scope="col">Company</th>
                <th scope="col">Status</th>
                <th scope="col">Last generated</th>
                <th scope="col">Resume / Match</th>
              </tr>
            </thead>
            <tbody>
              {visible.length === 0 ? (
                <tr>
                  <td colSpan={6} className="planning-bulk-results__empty">
                    No jobs match the current search or filter.
                  </td>
                </tr>
              ) : (
                visible.map((item) => {
                  const presentation = bulkResultPresentation(item);
                  const isSelected = selectedSet.has(item.job_identity);
                  const canRerun = Boolean(item.rerunnable);
                  const score = formatBulkMatchScore(item);
                  const resume = String(item.selected_resume || "").trim();
                  const company = String(item.job_company || "").trim();
                  return (
                    <tr
                      key={item.job_identity}
                      className={`planning-bulk-results__row${isSelected ? " is-selected" : ""}`}
                    >
                      <td className="planning-bulk-results__col-check">
                        <input
                          type="checkbox"
                          className="planning-bulk-results__checkbox"
                          checked={isSelected}
                          disabled={!canRerun}
                          aria-label={`Select ${item.job_title || item.job_label || item.job_identity}`}
                          title={canRerun ? undefined : "This job is not eligible to re-run."}
                          onChange={() => toggleRow(item.job_identity)}
                        />
                      </td>
                      <td>
                        <span className="planning-bulk-results__job">
                          {item.job_title || item.job_label || item.job_identity}
                        </span>
                        {item.job_location ? <small>{item.job_location}</small> : null}
                      </td>
                      <td>
                        <span className="planning-bulk-results__company">
                          <CompanyLogo
                            company={company}
                            domain={item.company_domain}
                            clientId={bulk.brandfetchClientId}
                          />
                          <span>{company || "—"}</span>
                        </span>
                      </td>
                      <td>
                        <span className={`planning-bulk-results__badge is-${presentation.tone}`}>
                          {presentation.label}
                        </span>
                      </td>
                      <td>{formatBulkTimestamp(item.finished_at)}</td>
                      <td>
                        <span className="planning-bulk-results__resume">
                          <FileText size={13} strokeWidth={2} aria-hidden="true" />
                          <span
                            className="planning-bulk-results__resume-name"
                            title={resume || undefined}
                          >
                            {resume || "—"}
                          </span>
                          <span aria-hidden="true">·</span>
                          <span className="planning-bulk-results__resume-score">{score}</span>
                        </span>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        <footer className="planning-bulk-results__footer">
          <div className="planning-bulk-results__footer-meta">
            <strong>{`${selected.length} job${selected.length === 1 ? "" : "s"} selected`}</strong>
            <span>{`${items.length} job${items.length === 1 ? "" : "s"} total`}</span>
            <span className="planning-bulk-results__divider" aria-hidden="true" />
            <button
              type="button"
              className="planning-bulk-results__clear"
              disabled={selected.length === 0}
              onClick={() => setSelected([])}
            >
              Clear selection
            </button>
          </div>
          <div className="planning-bulk-results__footer-actions">
            <button
              type="button"
              className="planning-bulk-results__secondary"
              disabled={allEligible.length === 0}
              onClick={() => onRerun("eligible", allEligible.map((item) => item.job_identity))}
            >
              <RotateCcw size={14} strokeWidth={2} aria-hidden="true" />
              {`Re-run all eligible (${allEligible.length})`}
            </button>
            <button
              type="button"
              className="planning-bulk-results__primary"
              disabled={selected.length === 0}
              onClick={() => onRerun("selected", selected)}
            >
              <Sparkles size={14} strokeWidth={2} aria-hidden="true" />
              {`Re-run selected (${selected.length})`}
            </button>
          </div>
        </footer>
      </div>
    </div>
  );
}

/**
 * One Planning Bulk control. Idle it starts a batch; while a run is active the
 * same control morphs into a progress button that opens the anchored details
 * popover. Every value is the canonical server progress published by the shared
 * shell — nothing is derived or timed locally.
 */
function PlanningBulkGenerateControl({
  bulk,
  onStart,
  onStop,
  onViewResults,
  onRerun,
}: {
  bulk: PlanningWorklistState["bulkSuggestions"];
  onStart: () => void;
  onStop: () => void;
  onViewResults: () => void;
  onRerun: (scope: "selected" | "eligible", jobIdentities: string[]) => void;
}) {
  const [open, setOpen] = useState(false);
  const [resultsOpen, setResultsOpen] = useState(false);
  const [hintVisible, setHintVisible] = useState(false);
  const [attentionOnly, setAttentionOnly] = useState(false);
  const rootRef = useRef<HTMLSpanElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const panelId = useId();
  const hintId = useId();
  const running = Boolean(bulk.isRunning);
  // A terminal result only governs this control while it belongs to the SAME
  // Live Pipeline job set. A new pipeline run reverts to the fresh state
  // without deleting any persisted history.
  const currentPipelineRunId = String(bulk.currentPipelineRunId || "").trim();
  const resultPipelineRunId = String(bulk.resultPipelineRunId || "").trim();
  const resultsMatchPipeline =
    Boolean(bulk.hasResults) &&
    currentPipelineRunId.length > 0 &&
    currentPipelineRunId === resultPipelineRunId;
  const showResults = !running && resultsMatchPipeline;
  const processedCount = Number(bulk.processedCount || 0);

  useEffect(() => {
    if (!running && open) setOpen(false);
  }, [running, open]);

  // Close a stale results workspace the moment its pipeline stops matching.
  useEffect(() => {
    if (!resultsMatchPipeline && resultsOpen) setResultsOpen(false);
  }, [resultsMatchPipeline, resultsOpen]);

  useEffect(() => {
    if (running && resultsOpen) setResultsOpen(false);
  }, [running, resultsOpen]);

  useEffect(() => {
    if (!open) return;
    const closeOutside = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
    };
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      setOpen(false);
      triggerRef.current?.focus();
    };
    document.addEventListener("mousedown", closeOutside);
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("mousedown", closeOutside);
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, [open]);

  const total = Number(bulk.total || 0);
  const completed = Number(bulk.completed || 0);
  const needsAttention = Number(bulk.needsAttention || 0);
  const remaining = Number(bulk.remaining || 0);
  const stopRequested = Boolean(bulk.stopRequested);
  const items = Array.isArray(bulk.items) ? bulk.items : [];
  const percent = total > 0 ? Math.min(100, Math.max(0, Math.round((completed / total) * 100))) : 0;
  const statusLabel = bulk.verified === false
    ? "Status unavailable"
    : stopRequested
    ? "Stopping after current"
    : "Running";
  const currentLabel = boundedBulkJobLabel(bulk.currentLabel || "");
  const statusTone = bulk.verified === false ? "pending" : stopRequested ? "attention" : "running";
  const attentionCount = items.filter((item) => item.status === "needs_attention").length;
  const visibleItems = attentionOnly
    ? items.filter((item) => item.status === "needs_attention")
    : items;

  const resultsTitle = `Review the completed Bulk Generate run for this Live Pipeline (${processedCount} processed).`;
  const idleTitle = bulk.eligibleCount > 0
    ? `Generate suggestions for ${bulk.eligibleCount} eligible Planning job${bulk.eligibleCount === 1 ? "" : "s"}.`
    : "No Planning jobs currently need suggestions.";

  return (
    <span
      className="planning-react-bulk-actions"
      ref={rootRef}
      // While a run is active this span holds only Bulk's own progress
      // controls, which the shared-shell guard must never block.
      data-bulk-safe={running ? "true" : undefined}
    >
      <button
        ref={triggerRef}
        type="button"
        className={`planning-react-bulk-generate${running ? " is-running" : ""}`}
        disabled={!running && !showResults && bulk.eligibleCount <= 0}
        title={running ? undefined : showResults ? resultsTitle : idleTitle}
        aria-describedby={running ? hintId : undefined}
        aria-expanded={running ? open : undefined}
        aria-controls={running && open ? panelId : undefined}
        onMouseEnter={running ? () => setHintVisible(true) : undefined}
        onMouseLeave={running ? () => setHintVisible(false) : undefined}
        onFocus={running ? () => setHintVisible(true) : undefined}
        onBlur={running ? () => setHintVisible(false) : undefined}
        onClick={() => {
          if (running) setOpen((value) => !value);
          else if (showResults) {
            setResultsOpen(true);
            onViewResults();
          } else onStart();
        }}
      >
        <span className="planning-react-bulk-generate__icon" aria-hidden="true">
          {running ? (
            <span className="planning-bulk-spinner" />
          ) : showResults ? (
            <ClipboardList size={15} strokeWidth={2} />
          ) : (
            <Sparkles size={15} strokeWidth={2} />
          )}
        </span>
        <span className="planning-react-bulk-generate__label">
          {running
            ? "Bulk suggestions generating…"
            : showResults
            ? "View bulk results"
            : "Bulk generate suggestions"}
        </span>
        <small>
          {running
            ? `${completed} / ${total}`
            : showResults
            ? `${processedCount} processed`
            : `${bulk.eligibleCount} eligible`}
        </small>
        {running ? (
          <span
            className="planning-bulk-progress"
            role="progressbar"
            aria-label="Bulk Generate progress"
            aria-valuenow={completed}
            aria-valuemin={0}
            aria-valuemax={total}
          >
            <span className="planning-bulk-progress__fill" style={{ width: `${percent}%` }} />
          </span>
        ) : null}
      </button>
      {running ? (
        <span
          id={hintId}
          role="tooltip"
          className={`planning-bulk-run__hint${hintVisible ? "" : " hidden"}`}
        >
          {PLANNING_BULK_RUN_TOOLTIP}
        </span>
      ) : null}
      {resultsOpen && showResults ? (
        <BulkResultsDialog
          bulk={bulk}
          onClose={() => {
            setResultsOpen(false);
            triggerRef.current?.focus();
          }}
          onRerun={(scope, jobIdentities) => {
            setResultsOpen(false);
            triggerRef.current?.focus();
            onRerun(scope, jobIdentities);
          }}
        />
      ) : null}
      {running && open ? (
        <div
          id={panelId}
          role="dialog"
          aria-label="Bulk Generate progress"
          className="planning-bulk-run__panel"
        >
          <header className="planning-bulk-run__panel-head">
            <div className="planning-bulk-run__panel-title">
              <strong>Bulk Generate</strong>
              <span className={`planning-bulk-chip is-${statusTone}`}>
                {statusTone === "running"
                  ? <span className="planning-bulk-spinner planning-bulk-spinner--chip" aria-hidden="true" />
                  : <span className="planning-bulk-chip__icon" aria-hidden="true">•</span>}
                {statusLabel}
              </span>
            </div>
            <div className="planning-bulk-run__panel-meta">
              <span className="planning-bulk-run__progress-count">{`${completed} / ${total}`}</span>
              <button
                type="button"
                className="planning-bulk-run__close"
                aria-label="Close Bulk Generate progress"
                onClick={() => {
                  setOpen(false);
                  triggerRef.current?.focus();
                }}
              >
                <X size={14} strokeWidth={2} aria-hidden="true" />
              </button>
            </div>
          </header>

          <div className="planning-bulk-run__metrics">
            <span className="planning-bulk-chip is-done">
              <span className="planning-bulk-chip__icon" aria-hidden="true">✓</span>
              {`${completed} Completed`}
            </span>
            <span className="planning-bulk-chip is-attention">
              <span className="planning-bulk-chip__icon" aria-hidden="true">!</span>
              {`${needsAttention} Attention`}
            </span>
            <span className="planning-bulk-chip is-pending">
              <span className="planning-bulk-chip__icon" aria-hidden="true">○</span>
              {`${remaining} Remaining`}
            </span>
          </div>

          {currentLabel ? (
            <section className="planning-bulk-run__current">
              <span className="planning-bulk-run__section-title">Current</span>
              <div className="planning-bulk-run__current-card">
                <span className="planning-bulk-spinner planning-bulk-spinner--chip" aria-hidden="true" />
                <span className="planning-bulk-run__current-job" title={currentLabel}>{currentLabel}</span>
              </div>
            </section>
          ) : null}

          {items.length ? (
            <section className="planning-bulk-run__jobs">
              <div className="planning-bulk-run__jobs-head">
                <span className="planning-bulk-run__section-title">Jobs</span>
                <span className="planning-bulk-run__jobs-filters">
                  <button
                    type="button"
                    className={`planning-bulk-run__filter${attentionOnly ? "" : " is-active"}`}
                    aria-pressed={!attentionOnly}
                    onClick={() => setAttentionOnly(false)}
                  >
                    {`All ${items.length}`}
                  </button>
                  <button
                    type="button"
                    className={`planning-bulk-run__filter${attentionOnly ? " is-active" : ""}`}
                    aria-pressed={attentionOnly}
                    onClick={() => setAttentionOnly(true)}
                  >
                    {`Attention ${attentionCount}`}
                  </button>
                </span>
              </div>
              {/* Only this region scrolls. The list is never auto-scrolled, so a
                  new current job cannot yank the view away from a row the user
                  is inspecting. */}
              <ul className="planning-bulk-run__job-list" tabIndex={0}>
                {visibleItems.map((item, index) => {
                  const presentation = bulkItemPresentation(item.status);
                  const label = boundedBulkJobLabel(item.label);
                  return (
                    <li
                      key={`${item.label}-${index}`}
                      className={`planning-bulk-run__job is-${presentation.tone}`}
                    >
                      <span className="planning-bulk-run__job-icon" aria-hidden="true">
                        {presentation.tone === "running"
                          ? <span className="planning-bulk-spinner planning-bulk-spinner--row" />
                          : presentation.icon}
                      </span>
                      <span className="planning-bulk-run__job-label" title={label}>{label}</span>
                      <span className={`planning-bulk-chip is-${presentation.tone}`}>{presentation.label}</span>
                    </li>
                  );
                })}
                {visibleItems.length === 0 ? (
                  <li className="planning-bulk-run__job-empty">No jobs need attention.</li>
                ) : null}
              </ul>
            </section>
          ) : null}

          <footer className="planning-bulk-run__footer">
            <button
              type="button"
              className="planning-bulk-run__stop"
              disabled={stopRequested}
              onClick={onStop}
            >
              {stopRequested ? "Stop requested" : "Stop after current"}
            </button>
          </footer>
        </div>
      ) : null}
    </span>
  );
}

const PLANNING_ACTION_OPTIONS: SharedFilterOption[] = [
  { value: "APPLY", label: "Ready for review", tone: "ready" },
  { value: "APPLY_REVIEW_VARIANTS", label: "Review resume choice", tone: "choice" },
  { value: "MAYBE_TAILOR", label: "Tailor first", tone: "tailor" },
  { value: "SKIP_FOR_NOW", label: "Review later", tone: "later" },
];

const PLANNING_MATCH_OPTIONS: SharedFilterOption[] = [
  { value: "strong", label: "Excellent match", tone: "strong" },
  { value: "solid", label: "Strong match", tone: "solid" },
  { value: "moderate", label: "Moderate match", tone: "moderate" },
  { value: "weak", label: "Weak match", tone: "weak" },
  { value: "filtered_out", label: "No credible match", tone: "unavailable" },
];

// "Review" is retired as a user-facing Tailoring state: it overlapped
// conceptually with "no_safe_rewrites" (tailoring/review evidence exists but
// no actionable rewrite survived). The server folds any legacy "review" rows
// into "no_safe_rewrites" for both filtering and display.
const PLANNING_TAILORING_OPTIONS: SharedFilterOption[] = [
  { value: "ready", label: "Ready", tone: "ready" },
  { value: "no_safe_rewrites", label: "No safe rewrites", tone: "later" },
  { value: "unavailable", label: "Unavailable", tone: "unavailable" },
];

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

// Presentation-only: "review" is retired as a user-facing Tailoring status.
// This does not touch row.tailoring_workspace_state itself (Open Workspace
// enable/disable is computed upstream from that raw field and must not
// change), it only relabels the plain status text shown for a legacy row.
function tailoringStatusLabel(value: unknown): string {
  return cleanText(value).toLowerCase() === "review" ? "No safe rewrites" : humanize(value);
}

function formatResume(value: unknown): string {
  const text = cleanText(value);
  return text ? text.replace(/\.pdf$/i, "").replace(/_/g, " ") : "Not selected";
}

// P1S40 selection provenance.
//
// `winner_resume` is the selector's nominal top-ranked candidate and is
// intentionally populated on unresolved rows too. Presenting it as the chosen
// resume made review-required jobs look decided. A resume is now shown as
// selected only when an operator picked it or the selector genuinely resolved;
// otherwise the nominal candidate is still shown, labelled as a candidate.
const REVIEW_SELECTION_SIGNALS = new Set(["effective_tie", "manual_review_close_call"]);

function isTruthyFlag(value: unknown): boolean {
  return ["true", "1", "yes", "y", "on"].includes(cleanText(value).toLowerCase());
}

// Positive evidence only: a row is treated as resolved when an authority field
// says so, never merely because the review flags are absent. Older rows that
// carry no authority fields therefore fall back to "top candidate", not
// "selected".
function selectionIsResolved(row: PlanningRow): boolean {
  if (isTruthyFlag(row.variant_review_required) || isTruthyFlag(row.needs_variant_review)) return false;
  const status = cleanText(row.resolved_selection_status).toLowerCase();
  if (status) return status === "resolved";
  if (REVIEW_SELECTION_SIGNALS.has(cleanText(row.selection_signal).toLowerCase())) return false;
  return cleanText(row.action).toUpperCase() === "APPLY";
}

function operatorSelectedResume(row: PlanningRow): string {
  return cleanText(row.operator_selected_resume || row.selected_resume);
}

function selectedResume(row: PlanningRow): string {
  const operator = operatorSelectedResume(row);
  if (operator) return operator;
  return selectionIsResolved(row) ? cleanText(row.winner_resume) : "";
}

function nominalCandidateResume(row: PlanningRow): string {
  return operatorSelectedResume(row) ? "" : cleanText(row.winner_resume);
}

// Hover text keeps the raw filename for a real selection; an unresolved row
// carries the same qualifier the cell shows.
export function resumeSelectionTitle(row: PlanningRow): string {
  const selected = selectedResume(row);
  if (selected) return selected;
  const nominal = nominalCandidateResume(row);
  return nominal ? `Top candidate: ${nominal}` : "";
}

export function resumeSelectionLabel(row: PlanningRow): string {
  const selected = selectedResume(row);
  if (selected) return formatResume(selected);
  const nominal = nominalCandidateResume(row);
  return nominal ? `Top candidate: ${formatResume(nominal)}` : formatResume("");
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
      accessorFn: resumeSelectionLabel,
      cell: ({ row }) => <span className="planning-react-resume" title={resumeSelectionTitle(row.original)}>{resumeSelectionLabel(row.original)}</span>,
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
      accessorFn: (row) => packetLabel(row.packet_generation_allowed),
      cell: ({ row }) => (
        <span className="planning-react-status-stack">
          <span className={`planning-react-badge ${packetLabel(row.original.packet_generation_allowed) === "Packet ready" ? "is-ready" : ""}`}>
            {packetLabel(row.original.packet_generation_allowed)}
          </span>
          <span>{tailoringStatusLabel(row.original.tailoring_workspace_state || "Workspace unavailable")}</span>
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

export function PlanningFiltersToolbar({ state }: { state: PlanningWorklistState }) {
  const [filters, setFilters] = useState<PlanningFilters>(state.filters);

  useEffect(() => setFilters(state.filters), [state.filters]);

  const updateFilters = (next: PlanningFilters) => {
    setFilters(next);
    publishPlanningAction({ type: "filters_change", filters: next });
  };
  const preferenceOptions = state.preferenceOptions.map((option) => ({
    value: option.role_family_id,
    label: option.display_name || option.role_family_id,
  }));

  return (
    <div className="planning-react-filter-grid" aria-label="Planning filters">
      <SharedFilterSelect
        id="planningActionFilter"
        label="Action"
        options={PLANNING_ACTION_OPTIONS}
        values={filters.actions}
        onChange={(actions) => updateFilters({ ...filters, actions })}
        placeholder="All"
        mode="single"
      />
      <SharedFilterSelect
        id="planningPreferenceFilter"
        label="Preferences"
        options={preferenceOptions}
        values={filters.preferenceIds}
        onChange={(preferenceIds) => updateFilters({ ...filters, preferenceIds })}
        placeholder="All Preferences"
        allLabel="All Preferences"
        searchable
        mode="multiple"
      />
      <SharedFilterSelect
        id="planningWinnerBucket"
        label="Match Strength"
        options={PLANNING_MATCH_OPTIONS}
        values={filters.winnerBuckets}
        onChange={(winnerBuckets) => updateFilters({ ...filters, winnerBuckets })}
        placeholder="All"
        mode="single"
      />
      <SharedFilterSelect
        id="planningTailoringFilter"
        label="Tailoring"
        options={PLANNING_TAILORING_OPTIONS}
        values={filters.tailoringStates}
        onChange={(tailoringStates) => updateFilters({ ...filters, tailoringStates })}
        placeholder="All"
        mode="single"
      />
      <fieldset className="planning-react-undecided-field">
        <legend>Undecided only</legend>
        <div className="planning-react-segmented" role="radiogroup" aria-label="Planning undecided only">
          <button
            type="button"
            aria-pressed={!filters.undecidedOnly}
            className={`${SHARED_NEUTRAL_CONTROL_CLASS} ${!filters.undecidedOnly ? "is-active" : ""}`.trim()}
            onClick={() => updateFilters({ ...filters, undecidedOnly: false })}
          >No</button>
          <button
            type="button"
            aria-pressed={filters.undecidedOnly}
            className={`${SHARED_NEUTRAL_CONTROL_CLASS} ${filters.undecidedOnly ? "is-active" : ""}`.trim()}
            onClick={() => updateFilters({ ...filters, undecidedOnly: true })}
          >Yes</button>
        </div>
      </fieldset>
      <label className="planning-react-limit-field" htmlFor="planningLimitInput">
        <span>Limit</span>
        <input
          id="planningLimitInput"
          type="number"
          min={1}
          value={filters.limit}
          onChange={(event) => updateFilters({
            ...filters,
            limit: Math.max(1, Math.floor(Number(event.target.value) || 15)),
          })}
        />
      </label>
      <div className="planning-react-filter-actions">
        <button
          type="button"
          className="planning-filter-apply"
          id="planningApplyFiltersBtn"
          onClick={() => publishPlanningAction({ type: "apply_filters", filters })}
        >Apply Filters</button>
        <button
          type="button"
          className={`${SHARED_NEUTRAL_CONTROL_CLASS} planning-filter-clear`}
          id="planningClearFiltersBtn"
          onClick={() => publishPlanningAction({ type: "clear_filters" })}
        ><RotateCcw size={15} aria-hidden="true" /> Clear</button>
      </div>
    </div>
  );
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
      setExpandedId("");
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
      headingActions={(
        <PlanningBulkGenerateControl
          bulk={state.bulkSuggestions}
          onStart={() => publishPlanningAction({ type: "bulk_generate_suggestions" })}
          onStop={() => publishPlanningAction({ type: "bulk_stop_after_current" })}
          onViewResults={() => publishPlanningAction({ type: "bulk_view_results" })}
          onRerun={(scope, jobIdentities) =>
            publishPlanningAction({ type: "bulk_rerun", scope, jobIdentities })
          }
        />
      )}
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
