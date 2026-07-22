import {
  type ColumnDef,
  type Header,
  type Row,
  type Table,
  flexRender,
} from "@tanstack/react-table";
import {
  ArrowUpDown,
  ChevronDown,
  ChevronRight,
  ChevronUp,
  Info,
} from "lucide-react";
import {
  type ReactNode,
  useEffect,
  useId,
  useRef,
  useState,
} from "react";

// Interaction patterns adapted from Origin UI's TanStack table and compact
// popover references: https://21st.dev/community/components/originui/table/default
// and https://21st.dev/community/components/originui/popover/tooltip-like-popover

export const SHARED_NEUTRAL_CONTROL_CLASS = "preferences-secondary-action";

export type SharedPaginationState = {
  page: number;
  pageSize: number;
  totalCount: number;
  totalPages: number;
  hasPrevPage: boolean;
  hasNextPage: boolean;
};

export function SharedExpansionButton({
  expanded,
  label,
  controls,
  className = "",
  onClick,
}: {
  expanded: boolean;
  label: string;
  controls?: string;
  className?: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      className={`${SHARED_NEUTRAL_CONTROL_CLASS} shared-table-expand-btn ${className}`.trim()}
      aria-label={label}
      aria-expanded={expanded}
      aria-controls={expanded ? controls : undefined}
      onClick={onClick}
    >
      {expanded
        ? <ChevronDown size={15} aria-hidden="true" />
        : <ChevronRight size={15} aria-hidden="true" />}
    </button>
  );
}

export function SharedMatchMeter({
  value,
  strength,
  label = "Match score",
  unavailableLabel = "Unavailable",
  className = "",
}: {
  value: unknown;
  strength?: string;
  label?: string;
  unavailableLabel?: string;
  className?: string;
}) {
  if (value === null || value === undefined || String(value).trim() === "") {
    return <span className="shared-table-muted">{unavailableLabel}</span>;
  }
  const parsed = Number(String(value).replace(/,/g, ""));
  if (!Number.isFinite(parsed)) return <span className="shared-table-muted">{unavailableLabel}</span>;
  const score = Math.abs(parsed) <= 1 ? parsed * 100 : parsed;
  const bounded = Math.max(0, Math.min(100, score));
  const formatted = score.toFixed(2);
  return (
    <div className={`shared-match-meter ${className}`.trim()}>
      <span className="shared-match-meter__value">{formatted}</span>
      {strength ? <span className="shared-match-meter__strength">{strength}</span> : null}
      <span
        className="shared-match-meter__track"
        role="progressbar"
        aria-label={`${label} ${formatted} out of 100${strength ? `, ${strength}` : ""}`}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Number(bounded.toFixed(2))}
      >
        <span style={{ width: `${bounded}%` }} />
      </span>
    </div>
  );
}

export function SharedInfoPopover({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLSpanElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const contentId = useId();

  useEffect(() => {
    if (!open) return;
    const closeOutside = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
    };
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      setOpen(false);
      buttonRef.current?.focus();
    };
    document.addEventListener("mousedown", closeOutside);
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("mousedown", closeOutside);
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, [open]);

  return (
    <span
      className="shared-info-popover"
      ref={rootRef}
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
      onFocus={() => setOpen(true)}
      onBlur={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget as Node | null)) setOpen(false);
      }}
    >
      <button
        ref={buttonRef}
        type="button"
        className={`${SHARED_NEUTRAL_CONTROL_CLASS} shared-info-popover__trigger`}
        aria-label={label}
        aria-expanded={open}
        aria-controls={contentId}
        onClick={() => setOpen((current) => !current)}
      >
        <Info size={13} aria-hidden="true" />
      </button>
      <span
        className="shared-info-popover__content"
        id={contentId}
        role="tooltip"
        hidden={!open}
      >{children}</span>
    </span>
  );
}

export function SharedJobPreview({
  title,
  location,
  children,
}: {
  title: string;
  location: string;
  children: ReactNode;
}) {
  const previewId = useId();
  return (
    <span className="shared-job-preview" tabIndex={0} aria-describedby={previewId}>
      {children}
      <span className="shared-job-preview__popover" role="tooltip" id={previewId}>
        <strong>{title || "Untitled job"}</strong>
        <span>{location || "Location unavailable"}</span>
      </span>
    </span>
  );
}

export function SharedExpandedDetail({ children }: { children: ReactNode }) {
  return <div className="shared-table-details">{children}</div>;
}

export function SharedPagination({
  pagination,
  visibleCount,
  noun = "jobs",
  ariaLabel,
  onPageChange,
}: {
  pagination: SharedPaginationState;
  visibleCount: number;
  noun?: string;
  ariaLabel: string;
  onPageChange: (page: number) => void;
}) {
  const { page, pageSize, totalCount, totalPages, hasPrevPage, hasNextPage } = pagination;
  const start = totalCount ? (page - 1) * pageSize + 1 : 0;
  const end = totalCount ? Math.min(start + Math.max(visibleCount - 1, 0), totalCount) : 0;
  return (
    <nav className="shared-table-pagination" aria-label={ariaLabel}>
      <span>{totalCount ? `Showing ${start}-${end} of ${totalCount} ${noun}` : `0 ${noun}`}</span>
      <div>
        <button
          type="button"
          className={SHARED_NEUTRAL_CONTROL_CLASS}
          disabled={!hasPrevPage}
          aria-label={`Previous ${ariaLabel.toLowerCase()}`}
          onClick={() => onPageChange(page - 1)}
        >Previous</button>
        <span aria-current="page">{page} / {Math.max(totalPages, 1)}</span>
        <button
          type="button"
          className={SHARED_NEUTRAL_CONTROL_CLASS}
          disabled={!hasNextPage}
          aria-label={`Next ${ariaLabel.toLowerCase()}`}
          onClick={() => onPageChange(page + 1)}
        >Next</button>
      </div>
    </nav>
  );
}

function resizeLabel<T>(header: Header<T, unknown>): string {
  const definition = header.column.columnDef.header;
  return typeof definition === "string" ? definition : header.column.id.replace(/_/g, " ");
}

export function SharedResizableHeader<T>({
  header,
  sticky,
}: {
  header: Header<T, unknown>;
  sticky: boolean;
}) {
  const sorted = header.column.getIsSorted();
  const label = resizeLabel(header);
  return (
    <th
      key={header.id}
      style={{ width: header.getSize() }}
      className={`shared-table-column--${header.column.id} ${sticky ? "is-sticky-action" : ""} ${sorted ? "is-sorted" : ""}`.trim()}
      aria-sort={sorted === "asc" ? "ascending" : sorted === "desc" ? "descending" : header.column.getCanSort() ? "none" : undefined}
    >
      {header.isPlaceholder ? null : (
        <div className="shared-table-header-content">
          {flexRender(header.column.columnDef.header, header.getContext())}
          {header.column.getCanSort() ? (
            <button
              type="button"
              className={`${SHARED_NEUTRAL_CONTROL_CLASS} shared-table-sort-btn ${sorted ? "is-sorted" : ""}`}
              aria-label={label}
              onClick={header.column.getToggleSortingHandler()}
            >
              {sorted === "asc" ? <ChevronUp size={14} aria-hidden="true" /> : sorted === "desc" ? <ChevronDown size={14} aria-hidden="true" /> : <ArrowUpDown className="shared-table-sort-placeholder" size={13} aria-hidden="true" />}
            </button>
          ) : null}
        </div>
      )}
      {header.column.getCanResize() ? (
        <span
          className={`shared-table-resize-handle ${header.column.getIsResizing() ? "is-resizing" : ""}`}
          onMouseDown={(event) => {
            event.stopPropagation();
            header.getResizeHandler()(event);
          }}
          onTouchStart={(event) => {
            event.stopPropagation();
            header.getResizeHandler()(event);
          }}
          role="separator"
          aria-orientation="vertical"
          aria-label={`Resize ${resizeLabel(header)} column`}
        />
      ) : null}
    </th>
  );
}

export function SharedTableCard<T>({
  className,
  ariaLabel,
  title,
  subtitle,
  count,
  table,
  columns,
  status,
  error,
  headerActions,
  pagination,
  paginationNoun = "jobs",
  paginationLabel,
  stickyColumnId,
  rowClassName,
  detailId,
  renderDetails,
  empty,
  onPageChange,
  onRetry,
  fillAvailableWidth = false,
  deferPaginationWhileLoading = false,
}: {
  className: string;
  ariaLabel: string;
  title: string;
  subtitle: string;
  count: number;
  table: Table<T>;
  columns: ColumnDef<T>[];
  status: "loading" | "ready" | "error";
  error?: string;
  headerActions?: ReactNode;
  pagination: SharedPaginationState;
  paginationNoun?: string;
  paginationLabel: string;
  stickyColumnId: string;
  rowClassName: (row: Row<T>, index: number) => string;
  detailId: (row: Row<T>) => string;
  renderDetails: (row: Row<T>) => ReactNode;
  empty: ReactNode;
  onPageChange: (page: number) => void;
  onRetry: () => void;
  fillAvailableWidth?: boolean;
  deferPaginationWhileLoading?: boolean;
}) {
  const pageControls = (placement: "top" | "bottom") => deferPaginationWhileLoading && status === "loading" ? (
    <div className="shared-table-pagination shared-table-pagination--loading" role="status">
      <span>Loading {paginationNoun}...</span>
    </div>
  ) : (
    <SharedPagination
      pagination={pagination}
      visibleCount={table.getRowModel().rows.length}
      noun={paginationNoun}
      ariaLabel={`${paginationLabel} ${placement} pagination`}
      onPageChange={onPageChange}
    />
  );

  return (
    <section className={`shared-table-card ${className}`} aria-label={ariaLabel}>
      <header className="shared-table-header">
        <div className="shared-table-heading">
          <div className="shared-table-title-line"><h2>{title}</h2><span>{deferPaginationWhileLoading && status === "loading" ? "-" : count}</span></div>
          <p>{deferPaginationWhileLoading && status === "loading" ? `Loading ${paginationNoun}...` : subtitle}</p>
        </div>
        <div className="shared-table-header-actions">
          {headerActions}
          {pageControls("top")}
        </div>
      </header>
      {status === "error" ? (
        <div className="shared-table-error" role="alert">
          <div><strong>Table data is unavailable</strong><span>{error || "Try the request again."}</span></div>
          <button type="button" className={SHARED_NEUTRAL_CONTROL_CLASS} onClick={onRetry}>Retry</button>
        </div>
      ) : (
        <div className="shared-table-viewport" aria-busy={status === "loading"}>
          <table style={{ width: fillAvailableWidth ? "100%" : table.getTotalSize(), minWidth: table.getTotalSize() }}>
            <thead>
              {table.getHeaderGroups().map((headerGroup) => (
                <tr key={headerGroup.id}>
                  {headerGroup.headers.map((header) => (
                    <SharedResizableHeader
                      key={header.id}
                      header={header}
                      sticky={header.column.id === stickyColumnId}
                    />
                  ))}
                </tr>
              ))}
            </thead>
            <tbody>
              {status === "loading" ? Array.from({ length: 5 }, (_, index) => (
                <tr className="shared-table-skeleton-row" key={`skeleton-${index}`}>
                  <td colSpan={columns.length}><span /></td>
                </tr>
              )) : table.getRowModel().rows.length ? table.getRowModel().rows.flatMap((row, index) => [
                <tr key={row.id} className={rowClassName(row, index)}>
                  {row.getVisibleCells().map((cell) => (
                    <td
                      key={cell.id}
                      style={{ width: cell.column.getSize() }}
                      className={`shared-table-column--${cell.column.id} ${cell.column.id === stickyColumnId ? "is-sticky-action" : ""}`.trim()}
                    >{flexRender(cell.column.columnDef.cell, cell.getContext())}</td>
                  ))}
                </tr>,
                row.getIsExpanded() ? (
                  <tr className="shared-table-detail-row" key={`${row.id}-details`} id={detailId(row)}>
                    <td colSpan={row.getVisibleCells().length}>{renderDetails(row)}</td>
                  </tr>
                ) : null,
              ]) : (
                <tr><td colSpan={columns.length}>{empty}</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
      {pageControls("bottom")}
    </section>
  );
}
