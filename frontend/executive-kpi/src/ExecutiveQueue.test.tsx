import { fireEvent, render, screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  ExecutiveQueue,
  QUEUE_ACTION_EVENT,
  QUEUE_COLUMN_WIDTH_STORAGE_KEY,
  type ExecutiveQueueAction,
  type ExecutiveQueueState,
} from "./ExecutiveQueue";

const rows = [
  {
    queue_rank: 2,
    job_doc_id: "job-beta",
    job_url: "https://example.test/beta",
    job_title: "Beta ML Engineer",
    job_company: "Beta Labs",
    job_location: "Boston, MA",
    posted_at: "2026-07-16T12:00:00Z",
    action: "APPLY_REVIEW_VARIANTS",
    packet_generation_allowed: true,
    winner_score: 0,
    operator_selected_resume: "Sriram_AI2.pdf",
    runner_up_resume: "Sriram_AI1.pdf",
    score_gap: 0.03,
    missing_requirement_count: 1,
    operator_decision: "SELECT_RESUME",
    queue_priority_reason: "borderline_deterministic_score",
  },
  {
    queue_rank: 1,
    job_doc_id: "job-alpha",
    job_url: "https://example.test/alpha",
    job_title: "Alpha Data Engineer",
    job_company: "Alpha Systems",
    job_location: "New York, NY",
    posted_at: "2026-07-12T12:00:00Z",
    action: "APPLY",
    packet_generation_allowed: false,
    winner_score: null,
    winner_resume: "Sriram_Data_Engineer.pdf",
    runner_up_resume: "",
    score_gap: null,
    missing_requirement_count: 0,
    operator_review_lane: "ready_to_apply",
    queue_priority_reason: "no_deterministic_winner",
  },
];

function queueState(overrides: Partial<ExecutiveQueueState> = {}): ExecutiveQueueState {
  return {
    status: "ready",
    rows,
    metaLabel: "Browse view · 2 total jobs",
    viewMode: "detailed",
    filters: { actions: [], preferenceIds: [], undecidedOnly: false, limit: 15 },
    preferenceOptions: [
      { role_family_id: "applied_ai", display_name: "Applied AI" },
      { role_family_id: "data_engineering", display_name: "Data Engineering" },
    ],
    pagination: {
      page: 1,
      pageSize: 15,
      totalCount: 31,
      totalPages: 3,
      hasPrevPage: false,
      hasNextPage: true,
    },
    sort: { key: "", direction: "asc" },
    ...overrides,
  };
}

function listenForActions() {
  const actions: ExecutiveQueueAction[] = [];
  const listener = (event: Event) => actions.push((event as CustomEvent<ExecutiveQueueAction>).detail);
  window.addEventListener(QUEUE_ACTION_EVENT, listener);
  return {
    actions,
    stop: () => window.removeEventListener(QUEUE_ACTION_EVENT, listener),
  };
}

beforeEach(() => {
  localStorage.clear();
  document.documentElement.removeAttribute("data-theme");
});

describe("ExecutiveQueue", () => {
  it("shows one active option in each segmented control and keeps inactive controls neutral", () => {
    const { rerender } = render(<ExecutiveQueue state={queueState()} />);

    const noButton = screen.getByRole("button", { name: "No" });
    const yesButton = screen.getByRole("button", { name: "Yes" });
    expect(noButton).toHaveClass("is-active");
    expect(noButton).toHaveAttribute("aria-pressed", "true");
    expect(yesButton).not.toHaveClass("is-active");
    expect(yesButton).toHaveAttribute("aria-pressed", "false");

    fireEvent.click(yesButton);
    expect(yesButton).toHaveClass("is-active");
    expect(noButton).not.toHaveClass("is-active");

    expect(screen.getByRole("radio", { name: "Detailed" })).toHaveClass("is-active");
    expect(screen.getByRole("radio", { name: "Simple" })).not.toHaveClass("is-active");

    rerender(<ExecutiveQueue state={queueState({ viewMode: "simple" })} />);
    expect(screen.getByRole("radio", { name: "Simple" })).toHaveClass("is-active");
    expect(screen.getByRole("radio", { name: "Detailed" })).not.toHaveClass("is-active");
  });

  it("keeps form controls neutral and Apply Filters as the sole primary toolbar action", () => {
    render(<ExecutiveQueue state={queueState()} />);

    const actionTrigger = screen.getByRole("button", { name: "Action All actions" });
    const preferenceTrigger = screen.getByRole("button", { name: "Preferences All Preferences" });
    const clearButton = screen.getByRole("button", { name: /clear/i });
    const applyButton = screen.getByRole("button", { name: "Apply Filters" });

    expect(actionTrigger).toHaveClass("shared-filter-select__trigger");
    expect(preferenceTrigger).toHaveClass("shared-filter-select__trigger");
    expect(clearButton).toHaveClass("executive-queue-clear-btn", "preferences-secondary-action");
    expect(applyButton).toHaveClass("executive-queue-apply-btn");
    expect(applyButton).not.toHaveClass("preferences-secondary-action");
  });

  it("renders real supplied rows, detailed columns, and honest match values", () => {
    render(<ExecutiveQueue state={queueState()} />);

    expect(screen.getByText("Beta ML Engineer")).toBeInTheDocument();
    expect(screen.getByText("Alpha Data Engineer")).toBeInTheDocument();
    for (const heading of ["Rank", "Company", "Location", "Runner-up resume", "Score gap", "Missing req count"]) {
      expect(screen.getByRole("button", { name: new RegExp(`^${heading}$`, "i") })).toBeInTheDocument();
    }
    expect(screen.queryByRole("button", { name: /^priority reason$/i })).not.toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Review" })).toBeInTheDocument();
    expect(screen.getByRole("progressbar", { name: "Match score 0.00 out of 100" })).toHaveAttribute("aria-valuenow", "0");
    expect(within(screen.getByText("Alpha Data Engineer").closest("tr") as HTMLElement).getAllByText("—").length).toBeGreaterThan(0);
    expect(screen.queryByText(/keyword|cpc|traffic/i)).not.toBeInTheDocument();
  });

  it("renders loading, empty, and inline retryable error states", () => {
    const { rerender } = render(<ExecutiveQueue state={queueState({ status: "loading", rows: [] })} />);
    expect(screen.getByLabelText("Executive queue table").querySelectorAll(".shared-table-skeleton-row")).toHaveLength(5);

    rerender(<ExecutiveQueue state={queueState({ rows: [], pagination: { ...queueState().pagination, totalCount: 0 } })} />);
    expect(screen.getByText("No jobs match these filters")).toBeInTheDocument();

    rerender(<ExecutiveQueue state={queueState({ status: "error", rows: [], message: "browse failed" })} />);
    expect(screen.getByRole("alert")).toHaveTextContent("browse failed");
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
  });

  it("publishes the existing filter semantics and clear defaults without fetching", () => {
    const listener = listenForActions();
    render(<ExecutiveQueue state={queueState()} />);

    fireEvent.click(screen.getByRole("button", { name: /all actions/i }));
    fireEvent.click(screen.getByRole("option", { name: "Ready for review" }));

    fireEvent.click(screen.getByRole("button", { name: /all preferences/i }));
    fireEvent.change(screen.getByRole("searchbox"), { target: { value: "data eng" } });
    expect(screen.queryByRole("option", { name: "Applied AI" })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("option", { name: "Data Engineering" }));
    expect(screen.getByRole("listbox")).toBeInTheDocument();
    expect(listener.actions).toHaveLength(0);
    fireEvent.change(screen.getByRole("spinbutton", { name: "Limit" }), { target: { value: "40" } });
    fireEvent.click(screen.getByRole("button", { name: "Yes" }));
    fireEvent.click(screen.getByRole("button", { name: "Apply Filters" }));

    expect(listener.actions[listener.actions.length - 1]).toEqual({
      type: "apply_filters",
      filters: {
        actions: ["APPLY"],
        preferenceIds: ["data_engineering"],
        undecidedOnly: true,
        limit: 40,
      },
    });

    fireEvent.click(screen.getByRole("button", { name: /clear/i }));
    expect(listener.actions[listener.actions.length - 1]).toEqual({ type: "clear_filters" });
    listener.stop();
  });

  it("publishes server sort state without reordering the current page and expands one row", () => {
    const listener = listenForActions();
    const { container } = render(<ExecutiveQueue state={queueState()} />);
    const rankSort = screen.getByRole("button", { name: /^rank$/i });
    fireEvent.click(rankSort);
    expect(listener.actions).toHaveLength(1);
    expect(listener.actions[0]).toEqual({ type: "sort_change", key: "queue_rank", direction: "desc" });
    const dataRows = screen.getAllByRole("row").filter((row) => row.querySelector(".executive-queue-job-cell"));
    expect(dataRows[0]).toHaveTextContent("Beta ML Engineer");
    expect(dataRows[1]).toHaveTextContent("Alpha Data Engineer");

    const alphaExpand = screen.getByRole("button", { name: "Expand details for Alpha Data Engineer" });
    expect(alphaExpand).toHaveAttribute("aria-expanded", "false");
    expect(alphaExpand.querySelector(".lucide-chevron-right")).toBeInTheDocument();
    fireEvent.click(alphaExpand);
    expect(alphaExpand).toHaveAttribute("aria-expanded", "true");
    expect(alphaExpand.querySelector(".lucide-chevron-down")).toBeInTheDocument();
    expect(container.querySelectorAll(".shared-table-detail-row")).toHaveLength(1);
    const detailRow = container.querySelector(".shared-table-detail-row") as HTMLElement;
    expect(detailRow.querySelector(".executive-queue-details--neutral")).toBeInTheDocument();
    expect(within(detailRow).getByText(/does not apply to the job/i)).toBeInTheDocument();
    for (const label of ["Priority reason", "Next step", "Selected resume", "Runner-up", "Score gap", "Missing requirements"]) {
      expect(within(detailRow).getByText(label)).toBeInTheDocument();
    }

    fireEvent.click(screen.getByRole("button", { name: "Expand details for Beta ML Engineer" }));
    expect(container.querySelectorAll(".shared-table-detail-row")).toHaveLength(1);
    expect(within(container.querySelector(".shared-table-detail-row") as HTMLElement).getByText("Borderline match")).toBeInTheDocument();
    listener.stop();
  });

  it("reflects server sort state accessibly and keeps action-only columns unsortable", () => {
    render(<ExecutiveQueue state={queueState({ sort: { key: "posted_at", direction: "desc" } })} />);
    expect(screen.getByRole("columnheader", { name: /posted at/i })).toHaveAttribute("aria-sort", "descending");
    expect(screen.getByRole("columnheader", { name: "Review" })).not.toHaveAttribute("aria-sort");
    expect(screen.getByRole("columnheader", { name: /next step/i })).not.toHaveAttribute("aria-sort");
  });

  it("publishes view, pagination, and Review actions through the one bridge", () => {
    const listener = listenForActions();
    render(<ExecutiveQueue state={queueState()} />);

    fireEvent.click(screen.getByRole("radio", { name: "Simple" }));
    expect(listener.actions[listener.actions.length - 1]).toEqual({ type: "view_mode_change", viewMode: "simple" });

    fireEvent.click(screen.getByRole("button", { name: "Next executive queue top pagination" }));
    expect(listener.actions[listener.actions.length - 1]).toEqual({ type: "page_change", page: 2 });

    const reviewButton = screen.getByRole("button", { name: "Review Beta ML Engineer" });
    expect(reviewButton).toHaveTextContent(/^Review$/);
    fireEvent.click(reviewButton);
    expect(listener.actions[listener.actions.length - 1]).toEqual({ type: "review", row: rows[0] });
    listener.stop();
  });

  it("reuses the existing persisted column-width schema and respects theme inheritance", () => {
    localStorage.setItem(QUEUE_COLUMN_WIDTH_STORAGE_KEY, JSON.stringify({ queue_rank: 144 }));
    document.documentElement.dataset.theme = "dark";
    render(<ExecutiveQueue state={queueState()} />);

    expect(screen.getByRole("columnheader", { name: /rank/i })).toHaveStyle({ width: "144px" });
    expect(document.documentElement).toHaveAttribute("data-theme", "dark");
  });

  it("pins a fixed Review column after a protected Selected Resume column", () => {
    const { container } = render(<ExecutiveQueue state={queueState()} />);
    const reviewHeader = screen.getByRole("columnheader", { name: "Review" });
    const selectedHeader = container.querySelector("th.shared-table-column--selected_resume") as HTMLElement;

    expect(reviewHeader).toHaveClass("is-sticky-action", "shared-table-column--review");
    expect(reviewHeader).toHaveStyle({ width: "128px" });
    expect(selectedHeader).toHaveClass("shared-table-column--selected_resume");
    expect(selectedHeader).toHaveStyle({ width: "240px" });
    expect(container.querySelectorAll("td.shared-table-column--selected_resume")).toHaveLength(rows.length);
    expect(container.querySelectorAll("td.is-sticky-action")).toHaveLength(rows.length);
    expect(container.querySelector(".executive-queue-selected-resume-value")).toHaveAttribute("title", "Sriram_AI2.pdf");
    expect(container.querySelector(".shared-table-viewport")).toContainElement(reviewHeader.closest("table"));
    expect(reviewHeader.querySelector("[role='separator']")).not.toBeInTheDocument();
    for (const reviewCell of container.querySelectorAll("td.is-sticky-action")) {
      expect(reviewCell).toHaveStyle({ width: "128px" });
    }
  });

  it("uses semantic badges without assigning recommendation colors to full rows", () => {
    const { container } = render(<ExecutiveQueue state={queueState()} />);
    expect(container.querySelector(".executive-queue-badge--ready")).toHaveTextContent("Ready for review");
    expect(container.querySelector(".executive-queue-badge--choice")).toHaveTextContent("Review resume choice");

    const queueRows = Array.from(container.querySelectorAll("tr.executive-queue-row"));
    expect(queueRows).toHaveLength(rows.length);
    for (const row of queueRows) {
      expect(row.className).not.toMatch(/ready|choice|tailor|later|apply|recommendation/);
    }
  });

  it("keeps Packet and pagination available around the horizontally scrollable queue", () => {
    const { container } = render(<ExecutiveQueue state={queueState()} />);
    const packetHeader = container.querySelector("th.shared-table-column--packet_status") as HTMLElement;
    expect(packetHeader).toHaveTextContent("Packet");
    expect(packetHeader).toHaveStyle({ width: "138px" });
    expect(container.querySelectorAll("td.shared-table-column--packet_status .executive-queue-badge--packet")).toHaveLength(rows.length);

    const viewport = container.querySelector(".shared-table-viewport") as HTMLElement;
    const pagination = Array.from(container.querySelectorAll(".shared-table-pagination"));
    expect(pagination).toHaveLength(2);
    expect(pagination.every((control) => !viewport.contains(control))).toBe(true);
    expect(pagination[0]).toHaveTextContent("Showing 1-2 of 31 jobs");
    expect(screen.getByRole("button", { name: "Previous executive queue top pagination" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Next executive queue bottom pagination" })).toBeEnabled();
  });

  it("renders detailed and simple density contracts without changing row meanings", () => {
    const { rerender, container } = render(<ExecutiveQueue state={queueState()} />);
    expect(container.querySelector(".executive-queue-table-card--detailed")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Company$/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Location$/i })).toBeInTheDocument();

    rerender(<ExecutiveQueue state={queueState({ viewMode: "simple" })} />);
    expect(container.querySelector(".executive-queue-table-card--simple")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /^Company$/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /^Location$/i })).not.toBeInTheDocument();
    expect(screen.getByText("Beta ML Engineer")).toBeInTheDocument();
    expect(screen.getByText("Beta Labs")).toBeInTheDocument();
  });
});
