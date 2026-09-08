import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import {
  CompanyLogo,
  PLANNING_ACTION_EVENT,
  bulkResultMatchScore,
  formatBulkMatchScore,
  type BulkResultItem,
  PLANNING_COLUMN_WIDTH_STORAGE_KEY,
  PlanningFiltersToolbar,
  PlanningSummary,
  PlanningWorklist,
  resumeSelectionLabel,
  type PlanningWorklistAction,
  type PlanningWorklistState,
} from "./PlanningWorklist";

const rows = [
  {
    job_doc_id: "job-one",
    queue_rank: 1,
    job_url: "https://example.test/one",
    job_title: "Senior Applied AI Engineer with a deliberately long title",
    job_company: "Example AI",
    job_location: "New York City, New York, United States",
    posted_at: "2026-07-12T00:00:00Z",
    action: "APPLY",
    winner_score: 0.82,
    winner_bucket: "strong_match",
    winner_resume: "Sriram_AI2.pdf",
    runner_up_resume: "Sriram_AI1.pdf",
    runner_up_score: 0.76,
    score_gap: 0.06,
    packet_generation_allowed: true,
    tailoring_workspace_state: "ready",
    missing_requirement_count: 1,
    operator_decision: "pending",
    queue_priority_reason: "Strong applied AI evidence",
    llm_adjudicator_readback_enabled: true,
    llm_adjudicator_readback_status: "ok",
    llm_adjudicator_readback: { status: "ok", provider_used: "fake", adjudicator_summary: "Close evidence review." },
    __planning_action: { kind: "generate_suggestions" as const, label: "Generate Suggestions", disabled: false, title: "Generate suggestions." },
  },
  {
    job_doc_id: "job-two",
    queue_rank: 2,
    job_title: "Data Engineer",
    job_company: "Example Data",
    job_location: "Boston, Massachusetts",
    posted_at: "2026-07-11T00:00:00Z",
    action: "APPLY_REVIEW_VARIANTS",
    winner_score: 0,
    winner_bucket: "borderline_match",
    selected_resume: "Sriram_Data_Engineer.pdf",
    packet_generation_allowed: false,
    tailoring_workspace_state: "unavailable",
    __planning_action: { kind: "unavailable" as const, label: "Unavailable", disabled: true, title: "No action available." },
  },
];

function planningState(overrides: Partial<PlanningWorklistState> = {}): PlanningWorklistState {
  return {
    status: "ready",
    rows,
    metaLabel: "Planning view · 31 total jobs",
    pagination: { page: 1, pageSize: 15, totalCount: 31, totalPages: 3, hasPrevPage: false, hasNextPage: true },
    sort: { key: "queue_rank", direction: "asc" },
    resultKey: "result-one",
    metrics: { total: 31, readyForReview: 1, packetReady: 1, needsDecision: 2 },
    filters: {
      actions: [],
      winnerBuckets: [],
      tailoringStates: [],
      preferenceIds: [],
      undecidedOnly: false,
      limit: 15,
    },
    preferenceOptions: [
      { role_family_id: "applied_ai", display_name: "Applied AI" },
      { role_family_id: "data_engineering", display_name: "Data Engineering" },
    ],
    bulkSuggestions: { eligibleCount: 12, available: true, isRunning: false },
    ...overrides,
  };
}

function listenForActions() {
  const actions: PlanningWorklistAction[] = [];
  const handler = (event: Event) => actions.push((event as CustomEvent<PlanningWorklistAction>).detail);
  window.addEventListener(PLANNING_ACTION_EVENT, handler);
  return { actions, stop: () => window.removeEventListener(PLANNING_ACTION_EVENT, handler) };
}

function lastAction(actions: PlanningWorklistAction[]) {
  return actions[actions.length - 1];
}

beforeEach(() => localStorage.clear());
afterEach(() => vi.restoreAllMocks());

it("renders the exact Planning column contract through the shared table primitives", () => {
  const { container } = render(<PlanningWorklist state={planningState()} />);
  const headerIds = Array.from(container.querySelectorAll("thead th")).map((header) => (
    Array.from(header.classList).find((name) => name.startsWith("shared-table-column--"))?.replace("shared-table-column--", "")
  ));
  expect(headerIds).toEqual(["expand", "queue_rank", "job_title", "posted_at", "recommendation", "winner_score", "selected_resume", "packet_status", "next_step"]);
  for (const label of ["Rank", "Job", "Posted at", "Review readiness", "Match score", "Resume selection", "Packet / workspace", "Next step"]) {
    expect(screen.getByText(label, { selector: "thead *" })).toBeInTheDocument();
  }
  expect(container.querySelector(".shared-table-card.planning-react-table-card")).toBeInTheDocument();
  expect(container.querySelectorAll(".shared-table-pagination")).toHaveLength(2);
  expect(container.querySelectorAll(".shared-table-expand-btn")).toHaveLength(2);
  expect(container.querySelector(".shared-match-meter")).toBeInTheDocument();
  expect(container.querySelector(".shared-job-preview")).toBeInTheDocument();
  expect(container.querySelector(".planning-table-body")).not.toBeInTheDocument();
  expect(screen.getByText("Planning view · 31 total jobs")).toBeInTheDocument();
  expect(screen.getByText("31", { selector: ".shared-table-title-line > span" })).toBeInTheDocument();
});

it("keeps rows collapsed, expands only one shared detail row, and exposes existing details", () => {
  const { container } = render(<PlanningWorklist state={planningState()} />);
  expect(container.querySelector(".shared-table-detail-row")).not.toBeInTheDocument();

  const first = screen.getByRole("button", { name: /expand planning details for senior applied ai engineer/i });
  fireEvent.click(first);
  expect(first).toHaveAttribute("aria-expanded", "true");
  expect(container.querySelectorAll(".shared-table-detail-row")).toHaveLength(1);
  expect(screen.getByText("Sriram AI1")).toBeInTheDocument();
  expect(screen.getByText("Strong applied AI evidence")).toBeInTheDocument();
  expect(screen.getByText("View AI Review")).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: /expand planning details for data engineer/i }));
  expect(container.querySelectorAll(".shared-table-detail-row")).toHaveLength(1);
  expect(screen.queryByText("Strong applied AI evidence")).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: /collapse planning details for data engineer/i }));
  expect(container.querySelector(".shared-table-detail-row")).not.toBeInTheDocument();
});

it("publishes one existing bridge action from top and bottom pagination, sorting, and next step", () => {
  const listener = listenForActions();
  render(<PlanningWorklist state={planningState()} />);

  fireEvent.click(screen.getByRole("button", { name: "Next planning worklist top pagination" }));
  expect(lastAction(listener.actions)).toEqual({ type: "page_change", page: 2 });
  fireEvent.click(screen.getByRole("button", { name: "Next planning worklist bottom pagination" }));
  expect(lastAction(listener.actions)).toEqual({ type: "page_change", page: 2 });
  fireEvent.click(screen.getByRole("button", { name: "Posted at" }));
  expect(lastAction(listener.actions)).toEqual({ type: "sort_change", key: "posted_at", direction: "desc" });
  fireEvent.click(screen.getByRole("button", { name: "Generate Suggestions" }));
  expect(lastAction(listener.actions)).toEqual({ type: "next_step", row: rows[0] });
  listener.stop();
});

it("renders the all-result bulk heading action and publishes only an explicit bulk event", () => {
  const listener = listenForActions();
  const { container } = render(<PlanningWorklist state={planningState()} />);

  const action = screen.getByRole("button", { name: /bulk generate suggestions.*12 eligible/i });
  expect(action).toBeEnabled();
  expect(action).toHaveTextContent("Bulk generate suggestions");
  expect(action).toHaveTextContent("12 eligible");
  expect(container.querySelector(".shared-table-heading-actions")).toContainElement(action);
  expect(listener.actions).toEqual([]);

  fireEvent.click(action);
  expect(lastAction(listener.actions)).toEqual({ type: "bulk_generate_suggestions" });
  expect(screen.getByRole("button", { name: "Generate Suggestions" })).toBeInTheDocument();
  listener.stop();
});

it("disables bulk generation when no jobs are eligible", () => {
  render(<PlanningWorklist state={planningState({
    bulkSuggestions: { eligibleCount: 0, available: false, isRunning: false },
  })} />);
  const emptyAction = screen.getByRole("button", { name: /bulk generate suggestions.*0 eligible/i });
  expect(emptyAction).toBeDisabled();
  expect(emptyAction).toHaveAttribute("title", "No Planning jobs currently need suggestions.");
});

it("uses Planning-specific validated column sizing and a real Posted at resize boundary", () => {
  localStorage.setItem(PLANNING_COLUMN_WIDTH_STORAGE_KEY, JSON.stringify({ version: 1, widths: { posted_at: 164, unknown: 999 } }));
  const { container, unmount } = render(<PlanningWorklist state={planningState()} />);
  const postedHeader = screen.getByRole("columnheader", { name: /posted at/i });
  expect(postedHeader).toHaveStyle({ width: "164px" });
  expect(within(postedHeader).getByRole("separator", { name: "Resize Posted at column" })).toBeInTheDocument();
  expect(screen.getByRole("columnheader", { name: "Next step" })).not.toContainElement(container.querySelector("th.shared-table-column--next_step [role='separator']"));
  unmount();

  localStorage.setItem(PLANNING_COLUMN_WIDTH_STORAGE_KEY, "not-json");
  render(<PlanningWorklist state={planningState()} />);
  expect(screen.getByRole("columnheader", { name: /posted at/i })).toHaveStyle({ width: "128px" });
});

it("renders compact summary information popovers without changing metric values", () => {
  const { container } = render(<PlanningSummary state={planningState()} />);
  expect(screen.getByText("31")).toBeInTheDocument();
  expect(screen.getAllByRole("button", { name: /^about /i })).toHaveLength(4);
  expect(container.querySelectorAll(".shared-info-popover__trigger")).toHaveLength(4);
  const help = screen.getByRole("button", { name: "About total results" });
  fireEvent.click(help);
  expect(screen.getByRole("tooltip")).toHaveTextContent("All planning rows matching the applied filters.");
});

it("uses the shared controlled filters without requesting until Apply", () => {
  const listener = listenForActions();
  render(<PlanningFiltersToolbar state={planningState()} />);

  fireEvent.click(screen.getByRole("button", { name: /action all$/i }));
  fireEvent.click(screen.getByRole("option", { name: "Ready for review" }));
  expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
  expect(lastAction(listener.actions)).toEqual(expect.objectContaining({
    type: "filters_change",
    filters: expect.objectContaining({ actions: ["APPLY"] }),
  }));
  expect(listener.actions.some((action) => action.type === "apply_filters")).toBe(false);

  fireEvent.click(screen.getByRole("button", { name: /preferences all preferences/i }));
  fireEvent.click(screen.getByRole("option", { name: "Applied AI" }));
  expect(screen.getByRole("listbox")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("option", { name: "Data Engineering" }));
  expect(screen.getByRole("button", { name: "Preferences 2 selected" })).toHaveAttribute("aria-expanded", "true");
  expect(listener.actions.some((action) => action.type === "apply_filters")).toBe(false);

  const limit = screen.getByRole("spinbutton", { name: "Limit" });
  expect(limit).not.toHaveAttribute("max");
  fireEvent.change(limit, { target: { value: "1000" } });

  fireEvent.click(screen.getByRole("button", { name: "Apply Filters" }));
  expect(lastAction(listener.actions)).toEqual(expect.objectContaining({
    type: "apply_filters",
    filters: expect.objectContaining({ actions: ["APPLY"], preferenceIds: ["applied_ai", "data_engineering"], limit: 1000 }),
  }));

  fireEvent.click(screen.getByRole("button", { name: "Clear" }));
  expect(lastAction(listener.actions)).toEqual({ type: "clear_filters" });
  listener.stop();
});

it("keeps exactly one truthful Undecided only segment active", () => {
  const listener = listenForActions();
  const initialState = planningState();
  const { container, rerender } = render(<PlanningFiltersToolbar state={initialState} />);

  expect(screen.getByRole("button", { name: "No" })).toHaveAttribute("aria-pressed", "true");
  expect(screen.getByRole("button", { name: "Yes" })).toHaveAttribute("aria-pressed", "false");
  expect(container.querySelectorAll(".planning-react-segmented .is-active")).toHaveLength(1);

  fireEvent.click(screen.getByRole("button", { name: "Yes" }));
  expect(lastAction(listener.actions)).toEqual(expect.objectContaining({
    type: "filters_change",
    filters: expect.objectContaining({ undecidedOnly: true }),
  }));

  rerender(<PlanningFiltersToolbar state={planningState({
    filters: { ...initialState.filters, undecidedOnly: true },
  })} />);
  expect(screen.getByRole("button", { name: "No" })).toHaveAttribute("aria-pressed", "false");
  expect(screen.getByRole("button", { name: "Yes" })).toHaveAttribute("aria-pressed", "true");
  expect(container.querySelectorAll(".planning-react-segmented .is-active")).toHaveLength(1);

  fireEvent.click(screen.getByRole("button", { name: "No" }));
  expect(lastAction(listener.actions)).toEqual(expect.objectContaining({
    type: "filters_change",
    filters: expect.objectContaining({ undecidedOnly: false }),
  }));
  listener.stop();
});

const runningBulk = {
  eligibleCount: 10,
  available: false,
  isRunning: true,
  total: 10,
  completed: 2,
  needsAttention: 1,
  remaining: 8,
  currentLabel: "SpaceX — Lead Supply Chain Reliability Engineer",
  stopRequested: false,
  verified: true,
  items: [
    { label: "Acme / Data Engineer", status: "success", outcome: "generated" },
    { label: "Globex / ML Engineer", status: "needs_attention", outcome: "" },
    { label: "SpaceX — Lead Supply Chain Reliability Engineer", status: "running", outcome: "" },
    { label: "Initech / Platform Engineer", status: "pending", outcome: "" },
  ],
};

it("morphs the existing bulk control into a progress button without a second indicator", () => {
  const { container, rerender } = render(<PlanningWorklist state={planningState({ bulkSuggestions: runningBulk })} />);

  const control = screen.getByRole("button", { name: /bulk suggestions generating/i });
  expect(control).toHaveTextContent("Bulk suggestions generating…");
  expect(control).toHaveTextContent("2 / 10");
  expect(control).toBeEnabled();
  expect(control.className).toContain("planning-react-bulk-generate");
  expect(control.className).toContain("is-running");

  // Exactly one bulk control; no adjacent "Bulk running · X / Y" trigger.
  expect(screen.queryByRole("button", { name: /bulk running/i })).toBeNull();
  expect(container.querySelectorAll(".planning-react-bulk-generate")).toHaveLength(1);
  expect(container.querySelector(".planning-bulk-run__trigger")).toBeNull();
  // No viewport-floating bulk modal.
  expect(container.querySelector("#bulkGenerationShell")).toBeNull();
  expect(container.querySelector(".shared-table-heading-actions")).toContainElement(control);

  // Loader + real progress bar bound to canonical server counts.
  expect(control.querySelector(".planning-bulk-spinner")).not.toBeNull();
  const progress = within(control).getByRole("progressbar", { name: "Bulk Generate progress" });
  expect(progress).toHaveAttribute("aria-valuenow", "2");
  expect(progress).toHaveAttribute("aria-valuemax", "10");
  expect((progress.querySelector(".planning-bulk-progress__fill") as HTMLElement).style.width).toEqual("20%");

  rerender(<PlanningWorklist state={planningState({
    bulkSuggestions: { eligibleCount: 12, available: true, isRunning: false },
  })} />);
  const idle = screen.getByRole("button", { name: /bulk generate suggestions.*12 eligible/i });
  expect(idle).toHaveTextContent("Bulk generate suggestions");
  expect(idle).toHaveTextContent("12 eligible");
  expect(idle.className).not.toContain("is-running");
  expect(idle.querySelector(".planning-bulk-progress")).toBeNull();
  expect(idle.querySelector(".planning-bulk-spinner")).toBeNull();
});

it("exposes the bulk running tooltip on hover and on keyboard focus", () => {
  render(<PlanningWorklist state={planningState({ bulkSuggestions: runningBulk })} />);
  const control = screen.getByRole("button", { name: /bulk suggestions generating/i });

  const tooltipId = control.getAttribute("aria-describedby") || "";
  expect(tooltipId).not.toEqual("");
  const tooltip = document.getElementById(tooltipId) as HTMLElement;
  expect(tooltip).toHaveTextContent("Bulk Generate running. Click to view.");
  expect(tooltip.className).toContain("hidden");

  fireEvent.mouseEnter(control);
  expect(tooltip.className).not.toContain("hidden");
  fireEvent.mouseLeave(control);
  expect(tooltip.className).toContain("hidden");

  fireEvent.focus(control);
  expect(tooltip.className).not.toContain("hidden");
  fireEvent.blur(control);
  expect(tooltip.className).toContain("hidden");
});

it("opens an anchored popover listing the bounded per-item job statuses", () => {
  const listener = listenForActions();
  const { container } = render(<PlanningWorklist state={planningState({ bulkSuggestions: runningBulk })} />);
  const control = screen.getByRole("button", { name: /bulk suggestions generating/i });
  expect(control).toHaveAttribute("aria-expanded", "false");

  fireEvent.click(control);
  // Clicking the running control views progress; it never restarts a batch.
  expect(listener.actions).toEqual([]);
  const panel = screen.getByRole("dialog", { name: "Bulk Generate progress" });
  expect(control).toHaveAttribute("aria-expanded", "true");
  expect(container.querySelector(".planning-react-bulk-actions")).toContainElement(panel);

  expect(panel).toHaveTextContent("Running");
  expect(panel).toHaveTextContent("2 / 10");
  expect(panel).toHaveTextContent("2 Completed");
  expect(panel).toHaveTextContent("1 Attention");
  expect(panel).toHaveTextContent("8 Remaining");
  expect(panel).toHaveTextContent("SpaceX — Lead Supply Chain Reliability Engineer");

  const jobs = panel.querySelectorAll(".planning-bulk-run__job");
  expect(jobs).toHaveLength(4);
  expect(jobs[0]).toHaveTextContent("Acme / Data Engineer");
  expect(jobs[0]).toHaveTextContent("Completed");
  expect(jobs[1]).toHaveTextContent("Needs attention");
  expect(jobs[2]).toHaveTextContent("Running");
  expect(jobs[3]).toHaveTextContent("Pending");
  // Status is not conveyed by colour alone.
  expect(jobs[0].querySelector(".planning-bulk-run__job-icon")).toHaveTextContent("✓");
  listener.stop();
});

it("closes and reopens the bulk popover without affecting the run", () => {
  render(<PlanningWorklist state={planningState({ bulkSuggestions: runningBulk })} />);
  const control = screen.getByRole("button", { name: /bulk suggestions generating/i });

  fireEvent.click(control);
  fireEvent.click(screen.getByRole("button", { name: "Close Bulk Generate progress" }));

  expect(screen.queryByRole("dialog", { name: "Bulk Generate progress" })).toBeNull();
  const stillRunning = screen.getByRole("button", { name: /bulk suggestions generating/i });
  expect(stillRunning).toHaveTextContent("2 / 10");
  expect(stillRunning).toHaveAttribute("aria-expanded", "false");

  fireEvent.click(stillRunning);
  expect(screen.getByRole("dialog", { name: "Bulk Generate progress" })).toBeInTheDocument();
});

it("publishes the existing stop-after-current action from the bulk popover", () => {
  const listener = listenForActions();
  const { rerender } = render(<PlanningWorklist state={planningState({ bulkSuggestions: runningBulk })} />);

  fireEvent.click(screen.getByRole("button", { name: /bulk suggestions generating/i }));
  const stop = screen.getByRole("button", { name: "Stop after current" });
  expect(stop).toBeEnabled();
  fireEvent.click(stop);
  expect(lastAction(listener.actions)).toEqual({ type: "bulk_stop_after_current" });

  rerender(<PlanningWorklist state={planningState({
    bulkSuggestions: { ...runningBulk, stopRequested: true },
  })} />);
  expect(screen.getByRole("button", { name: "Stop requested" })).toBeDisabled();
  listener.stop();
});

it("starts a batch from the idle control and keeps filters and pagination intact", () => {
  const listener = listenForActions();
  const { container } = render(<PlanningWorklist state={planningState()} />);
  const idle = screen.getByRole("button", { name: /bulk generate suggestions.*12 eligible/i });

  fireEvent.click(idle);
  expect(lastAction(listener.actions)).toEqual({ type: "bulk_generate_suggestions" });
  expect(screen.queryByRole("dialog", { name: "Bulk Generate progress" })).toBeNull();
  expect(container.querySelectorAll(".planning-react-row").length).toBeGreaterThan(0);
  listener.stop();
});

it("marks the active bulk control safe so the shell guard never blocks it", () => {
  const { container } = render(<PlanningWorklist state={planningState({ bulkSuggestions: runningBulk })} />);
  const control = screen.getByRole("button", { name: /bulk suggestions generating/i });
  const actions = container.querySelector(".planning-react-bulk-actions") as HTMLElement;

  // The shell guard exempts anything inside [data-bulk-safe='true'].
  expect(actions).toHaveAttribute("data-bulk-safe", "true");
  expect(control.closest("[data-bulk-safe='true']")).toBe(actions);

  // It must never look or behave like a blocked mutation control.
  expect(control).toBeEnabled();
  expect(control).not.toHaveAttribute("disabled");
  expect(control.getAttribute("aria-disabled")).toBeNull();
  expect(control.getAttribute("title")).toBeNull();
  expect(control.className).not.toContain("is-blocked");

  const describedBy = control.getAttribute("aria-describedby") || "";
  expect(describedBy).not.toEqual("bulkGenerationGuardDescription");
  const tooltip = document.getElementById(describedBy) as HTMLElement;
  expect(tooltip).toHaveTextContent("Bulk Generate running. Click to view.");
  expect(tooltip.textContent || "").not.toContain("must finish or be stopped");

  // The popover's own controls sit inside the same exempt container.
  fireEvent.click(control);
  expect(screen.getByRole("button", { name: "Close Bulk Generate progress" }).closest("[data-bulk-safe='true']")).toBe(actions);
  expect(screen.getByRole("button", { name: "Stop after current" }).closest("[data-bulk-safe='true']")).toBe(actions);
});

it("renders the progress track at zero completed without faking progress", () => {
  const { container } = render(<PlanningWorklist state={planningState({
    bulkSuggestions: { ...runningBulk, completed: 0, total: 2, remaining: 2, needsAttention: 0 },
  })} />);
  const control = screen.getByRole("button", { name: /bulk suggestions generating/i });
  expect(control).toHaveTextContent("0 / 2");

  const progress = within(control).getByRole("progressbar", { name: "Bulk Generate progress" });
  expect(progress).toHaveAttribute("aria-valuenow", "0");
  expect(progress).toHaveAttribute("aria-valuemax", "2");
  // Track is present (activity is visible) but the fill claims no progress.
  const fill = progress.querySelector(".planning-bulk-progress__fill") as HTMLElement;
  expect(fill).not.toBeNull();
  expect(fill.style.width).toEqual("0%");
  expect(control.querySelector(".planning-bulk-spinner")).not.toBeNull();

  // The idle control carries neither affordance.
  container.querySelectorAll(".planning-bulk-progress").forEach((node) => expect(node).toBeInTheDocument());
});

it("keeps the fill width mathematically tied to canonical server counts", () => {
  const { rerender } = render(<PlanningWorklist state={planningState({
    bulkSuggestions: { ...runningBulk, completed: 5, total: 10 },
  })} />);
  const widthFor = () => (
    (screen.getByRole("progressbar", { name: "Bulk Generate progress" })
      .querySelector(".planning-bulk-progress__fill") as HTMLElement).style.width
  );
  expect(widthFor()).toEqual("50%");

  rerender(<PlanningWorklist state={planningState({
    bulkSuggestions: { ...runningBulk, completed: 10, total: 10 },
  })} />);
  expect(widthFor()).toEqual("100%");
});

it("keeps the popover a fixed-size panel with only the jobs list scrolling", () => {
  render(<PlanningWorklist state={planningState({ bulkSuggestions: runningBulk })} />);
  fireEvent.click(screen.getByRole("button", { name: /bulk suggestions generating/i }));
  const panel = screen.getByRole("dialog", { name: "Bulk Generate progress" });

  const jobList = panel.querySelector(".planning-bulk-run__job-list") as HTMLElement;
  const footer = panel.querySelector(".planning-bulk-run__footer") as HTMLElement;
  const current = panel.querySelector(".planning-bulk-run__current-card") as HTMLElement;
  const stop = screen.getByRole("button", { name: "Stop after current" });

  expect(jobList).not.toBeNull();
  // Stop and Current must never be inside the scrolling region.
  expect(jobList.contains(stop)).toBe(false);
  expect(jobList.contains(current)).toBe(false);
  expect(footer.contains(stop)).toBe(true);
  // Header, metrics, current and footer are siblings of the scroll area.
  expect(panel.querySelector(".planning-bulk-run__panel-head")).not.toBeNull();
  expect(panel.querySelector(".planning-bulk-run__metrics")).not.toBeNull();
  expect(jobList.getAttribute("tabindex")).toEqual("0");
});

it("renders a bounded panel structure for a large batch", () => {
  // Frontend test data only — proves layout structure, not production behaviour.
  const many = Array.from({ length: 100 }, (_, index) => ({
    label: `Company ${index} · A deliberately long engineering role title ${"y".repeat(60)}`,
    status: index < 27 ? "success" : index < 30 ? "needs_attention" : index === 30 ? "running" : "pending",
    outcome: "",
  }));
  render(<PlanningWorklist state={planningState({
    bulkSuggestions: {
      ...runningBulk,
      total: 100,
      completed: 27,
      needsAttention: 3,
      remaining: 70,
      items: many,
    },
  })} />);
  fireEvent.click(screen.getByRole("button", { name: /bulk suggestions generating/i }));
  const panel = screen.getByRole("dialog", { name: "Bulk Generate progress" });

  expect(panel).toHaveTextContent("27 / 100");
  expect(panel).toHaveTextContent("27 Completed");
  expect(panel).toHaveTextContent("3 Attention");
  expect(panel).toHaveTextContent("70 Remaining");

  // All rows live inside the single scroll container, not the outer panel.
  const jobList = panel.querySelector(".planning-bulk-run__job-list") as HTMLElement;
  expect(jobList.querySelectorAll(".planning-bulk-run__job")).toHaveLength(100);
  expect(panel.querySelectorAll(".planning-bulk-run__job-list")).toHaveLength(1);
  // Stop stays pinned outside the list even with 100 items.
  expect(jobList.contains(screen.getByRole("button", { name: "Stop after current" }))).toBe(false);

  // Every row keeps the truncatable three-column shape.
  const first = jobList.querySelector(".planning-bulk-run__job") as HTMLElement;
  expect(first.querySelector(".planning-bulk-run__job-label")).not.toBeNull();
  expect(first.querySelector(".planning-bulk-chip")).not.toBeNull();
});

it("renders a status pill for every supported item state and marks the running row", () => {
  render(<PlanningWorklist state={planningState({ bulkSuggestions: runningBulk })} />);
  fireEvent.click(screen.getByRole("button", { name: /bulk suggestions generating/i }));
  const rows = document.querySelectorAll(".planning-bulk-run__job");

  expect(rows[0].className).toContain("is-done");
  expect(rows[0].querySelector(".planning-bulk-chip.is-done")).toHaveTextContent("Completed");
  expect(rows[1].className).toContain("is-attention");
  expect(rows[1].querySelector(".planning-bulk-chip.is-attention")).toHaveTextContent("Needs attention");
  expect(rows[2].className).toContain("is-running");
  expect(rows[2].querySelector(".planning-bulk-chip.is-running")).toHaveTextContent("Running");
  expect(rows[3].className).toContain("is-pending");
  expect(rows[3].querySelector(".planning-bulk-chip.is-pending")).toHaveTextContent("Pending");

  // Header status chip carries icon + text, not colour alone.
  const panel = screen.getByRole("dialog", { name: "Bulk Generate progress" });
  expect(panel.querySelector(".planning-bulk-run__panel-title .planning-bulk-chip")).toHaveTextContent("Running");
});

it("filters the jobs list to attention rows client-side without new requests", () => {
  const listener = listenForActions();
  const fetchSpy = vi.fn();
  vi.stubGlobal("fetch", fetchSpy);
  render(<PlanningWorklist state={planningState({ bulkSuggestions: runningBulk })} />);
  fireEvent.click(screen.getByRole("button", { name: /bulk suggestions generating/i }));

  expect(document.querySelectorAll(".planning-bulk-run__job")).toHaveLength(4);
  fireEvent.click(screen.getByRole("button", { name: "Attention 1" }));
  const filtered = document.querySelectorAll(".planning-bulk-run__job");
  expect(filtered).toHaveLength(1);
  expect(filtered[0].className).toContain("is-attention");

  fireEvent.click(screen.getByRole("button", { name: "All 4" }));
  expect(document.querySelectorAll(".planning-bulk-run__job")).toHaveLength(4);

  // Presentation only: no server calls, no published actions.
  expect(fetchSpy).not.toHaveBeenCalled();
  expect(listener.actions).toEqual([]);
  vi.unstubAllGlobals();
  listener.stop();
});

it("retires the user-facing Tailoring 'Review' filter option", () => {
  const listener = listenForActions();
  render(<PlanningFiltersToolbar state={planningState()} />);

  fireEvent.click(screen.getByRole("button", { name: /tailoring all$/i }));
  const listbox = screen.getByRole("listbox");
  const optionLabels = within(listbox).getAllByRole("option").map((option) => option.textContent);

  expect(optionLabels).toEqual(["Ready", "No safe rewrites", "Unavailable"]);
  expect(optionLabels).not.toContain("Review");
  expect(within(listbox).queryByRole("option", { name: "Review" })).not.toBeInTheDocument();

  fireEvent.click(within(listbox).getByRole("option", { name: "No safe rewrites" }));
  expect(lastAction(listener.actions)).toEqual(
    expect.objectContaining({
      type: "filters_change",
      filters: expect.objectContaining({ tailoringStates: ["no_safe_rewrites"] }),
    }),
  );
  listener.stop();
});

it("presents a legacy 'review' row status as 'No safe rewrites' without touching Open Workspace availability", () => {
  const legacyReviewRow = {
    ...rows[0],
    job_doc_id: "job-legacy-review",
    tailoring_workspace_state: "review",
    // Open Workspace availability is computed upstream (planning.js) and
    // handed to React as this pre-resolved field; retiring the "review"
    // status label must not change what was already decided here.
    __planning_action: { kind: "open_workspace" as const, label: "Open Workspace", disabled: true, title: "No safe bullet-level rewrites were found for this row." },
  };
  render(<PlanningWorklist state={planningState({ rows: [legacyReviewRow] })} />);

  expect(screen.getByText("No safe rewrites")).toBeInTheDocument();
  expect(screen.queryByText("Review")).not.toBeInTheDocument();

  const workspaceButton = screen.getByRole("button", { name: "Open Workspace" });
  expect(workspaceButton).toBeDisabled();
});

it("does not change Open Workspace availability for ready/unavailable rows (review retirement is presentation-only)", () => {
  const openableRow = {
    ...rows[0],
    job_doc_id: "job-openable",
    tailoring_workspace_state: "no_safe_rewrites",
    __planning_action: { kind: "open_workspace" as const, label: "Open Workspace", disabled: false, title: "Review-only guidance is available." },
  };
  render(<PlanningWorklist state={planningState({ rows: [openableRow] })} />);

  expect(screen.getByText("No safe rewrites")).toBeInTheDocument();
  const workspaceButton = screen.getByRole("button", { name: "Open Workspace" });
  expect(workspaceButton).not.toBeDisabled();
});


// --- P1S40 selection provenance -------------------------------------------
//
// `winner_resume` is the selector's nominal top-ranked candidate and is
// populated on unresolved rows by contract. These pin the four representative
// P1S39 rows plus the operator override and the effective-tie flag trap.

it("shows the resume as selected only when the selector genuinely resolved it", () => {
  // A. Decisive winner (Life Sciences shape): resolved, no review.
  expect(
    resumeSelectionLabel({
      winner_resume: "Sriram_Neelakantan_AI1.pdf",
      action: "APPLY",
      resolved_selection_status: "resolved",
      variant_review_required: "False",
      needs_variant_review: "False",
      selection_signal: "decisive_winner",
    }),
  ).toBe("Sriram Neelakantan AI1");
});

it("never labels an unresolved nominal winner as selected", () => {
  // B. Exact substantive tie (Knowledge Team shape).
  const exactTie = resumeSelectionLabel({
    winner_resume: "Sriram_Neelakantan_AIML_resume_no_syn_v1.pdf",
    action: "APPLY_REVIEW_VARIANTS",
    resolved_selection_status: "unresolved",
    variant_review_required: "True",
    needs_variant_review: "True",
    selection_signal: "effective_tie",
  });
  expect(exactTie).toContain("Top candidate");
  expect(exactTie).not.toBe("Sriram Neelakantan AIML resume no syn v1");

  // C. Semantic reversal (MongoDB shape): nominal winner is not even the
  // substantive winner, so it must not be presented as chosen.
  const reversal = resumeSelectionLabel({
    winner_resume: "Sriram_Neelakantan_Product_Data_Scientist.pdf",
    action: "APPLY_REVIEW_VARIANTS",
    resolved_selection_status: "unresolved",
    variant_review_required: "True",
    selection_signal: "effective_tie",
  });
  expect(reversal).toContain("Top candidate");

  // D. Manual-review close call (Frontier Red Team shape).
  const closeCall = resumeSelectionLabel({
    winner_resume: "Sriram_Neelakantan_AI1.pdf",
    action: "APPLY_REVIEW_VARIANTS",
    resolved_selection_status: "unresolved",
    variant_review_required: "True",
    selection_signal: "manual_review_close_call",
  });
  expect(closeCall).toContain("Top candidate");
});

it("keeps the operator selection authoritative on review-required rows", () => {
  // E. Operator override must win over both the review state and the nominal winner.
  expect(
    resumeSelectionLabel({
      operator_selected_resume: "Sriram_Neelakantan_AI2.pdf",
      winner_resume: "Sriram_Neelakantan_AIML_resume_no_syn_v1.pdf",
      action: "APPLY_REVIEW_VARIANTS",
      resolved_selection_status: "unresolved",
      variant_review_required: "True",
      selection_signal: "effective_tie",
    }),
  ).toBe("Sriram Neelakantan AI2");
});

it("guards effective ties even when requires_manual_review is false", () => {
  // requires_manual_review is a close-call diagnostic and is false on effective
  // ties, so it must never be the sole guard.
  const label = resumeSelectionLabel({
    winner_resume: "Sriram_Neelakantan_AIML_resume_no_syn_v2.pdf",
    action: "MAYBE_TAILOR",
    requires_manual_review: "False",
    variant_review_required: "True",
    selection_signal: "effective_tie",
  });
  expect(label).toContain("Top candidate");
});

it("allows a genuinely resolved tie (equivalent variants / adjudication) to be selected", () => {
  expect(
    resumeSelectionLabel({
      winner_resume: "Sriram_Neelakantan_AIML_resume_no_syn_v2.pdf",
      action: "APPLY",
      resolved_selection_status: "resolved",
      resolved_resume_source: "deterministic_equivalent_variants",
      variant_review_required: "False",
      selection_signal: "effective_tie",
    }),
  ).toBe("Sriram Neelakantan AIML resume no syn v2");
});

it("falls back conservatively when older rows omit the review fields", () => {
  // No authority fields at all: a bare nominal winner is NOT treated as selected.
  expect(resumeSelectionLabel({ winner_resume: "Sriram_AI1.pdf" })).toBe("Top candidate: Sriram AI1");
  // A historical row carrying only action=APPLY is genuinely resolved.
  expect(resumeSelectionLabel({ winner_resume: "Sriram_AI1.pdf", action: "APPLY" })).toBe("Sriram AI1");
  expect(resumeSelectionLabel({})).toBe("Not selected");
});

// --- Bulk generation results + re-run center --------------------------------

const resultItems = [
  {
    job_identity: "job-1",
    job_doc_id: "doc-1",
    queue_rank: "1",
    job_label: "Example AI · Senior Applied AI Engineer",
    job_title: "Senior Applied AI Engineer",
    job_company: "Example AI",
    job_location: "New York City",
    selected_resume: "Resume_A.pdf",
    winner_resume: "/saved/resumes/Resume_A.pdf",
    winner_score: 0.91,
    status: "succeeded",
    outcome: "generated",
    finished_at: "2026-09-07T23:42:00Z",
    rerunnable: false,
    match_score: 0.91,
  },
  {
    job_identity: "job-2",
    job_doc_id: "doc-2",
    queue_rank: "2",
    job_label: "Northwind · Staff Data Scientist",
    job_title: "Staff Data Scientist",
    job_company: "Northwind",
    selected_resume: "Resume_B.pdf",
    winner_resume: "Resume_A.pdf",
    winner_score: 0.88,
    runner_up_resume: "C:\\saved\\Resume_B.pdf",
    runner_up_score: 0.764,
    status: "succeeded",
    outcome: "no_safe_rewrites",
    finished_at: "2026-09-07T23:08:00Z",
    rerunnable: true,
    match_score: 0.76,
  },
  {
    job_identity: "job-3",
    job_doc_id: "doc-3",
    queue_rank: "3",
    job_label: "Northwind · ML Platform Engineer",
    job_title: "ML Platform Engineer",
    job_company: "Northwind",
    selected_resume: "Resume_C.pdf",
    winner_resume: "Resume_A.pdf",
    winner_score: 0.9,
    runner_up_resume: "Resume_B.pdf",
    runner_up_score: 0.8,
    status: "needs_attention",
    outcome: "failed",
    error_category: "provider_failure",
    finished_at: "2026-09-07T23:20:00Z",
    rerunnable: true,
    match_score: null,
  },
];

const terminalBulk: PlanningWorklistState["bulkSuggestions"] = {
  eligibleCount: 0,
  available: false,
  isRunning: false,
  hasResults: true,
  currentPipelineRunId: "pipeline-a",
  resultPipelineRunId: "pipeline-a",
  latestRunId: "bulk-2",
  latestStatus: "completed",
  lastFinishedAt: "2026-09-07T23:42:00Z",
  processedCount: 3,
  rerunnableCount: 2,
  resultLoadStatus: "ready" as const,
  resultItems,
};

function openResults(bulk: PlanningWorklistState["bulkSuggestions"] = terminalBulk) {
  render(<PlanningWorklist state={planningState({ bulkSuggestions: bulk })} />);
  const trigger = screen.getByRole("button", { name: /view bulk results/i });
  fireEvent.click(trigger);
  return { trigger, dialog: screen.getByRole("dialog", { name: /bulk generation results/i }) };
}

it("keeps the fresh bulk control when no terminal run matches the current pipeline", () => {
  render(<PlanningWorklist state={planningState({
    bulkSuggestions: { eligibleCount: 12, available: true, isRunning: false, currentPipelineRunId: "pipeline-a" },
  })} />);
  const action = screen.getByRole("button", { name: /bulk generate suggestions.*12 eligible/i });
  expect(action).toHaveTextContent("Bulk generate suggestions");
  expect(screen.queryByRole("button", { name: /view bulk results/i })).toBeNull();
});

it("keeps the running state unchanged even when a terminal result exists", () => {
  render(<PlanningWorklist state={planningState({
    bulkSuggestions: { ...terminalBulk, ...runningBulk, isRunning: true },
  })} />);
  expect(screen.getByRole("button", { name: /bulk suggestions generating/i })).toBeTruthy();
  expect(screen.queryByRole("button", { name: /view bulk results/i })).toBeNull();
});

it("morphs to View bulk results and stays enabled with zero fresh eligible jobs", () => {
  render(<PlanningWorklist state={planningState({ bulkSuggestions: terminalBulk })} />);
  const control = screen.getByRole("button", { name: /view bulk results/i });
  expect(control).toHaveTextContent("View bulk results");
  expect(control).toHaveTextContent("3 processed");
  expect(control).not.toBeDisabled();
});

it("reverts to the fresh control when the Live Pipeline run changes", () => {
  render(<PlanningWorklist state={planningState({
    bulkSuggestions: { ...terminalBulk, currentPipelineRunId: "pipeline-b", eligibleCount: 9 },
  })} />);
  expect(screen.queryByRole("button", { name: /view bulk results/i })).toBeNull();
  expect(screen.getByRole("button", { name: /bulk generate suggestions.*9 eligible/i })).toBeTruthy();
});

it("opens the results dialog with three summary cards and publishes the view action", () => {
  const listener = listenForActions();
  const { dialog } = openResults();
  expect(dialog.getAttribute("aria-modal")).toEqual("true");
  // Each card puts its number and its primary label on ONE metric line.
  const metrics = Array.from(
    dialog.querySelectorAll(".planning-bulk-results__card-metric"),
  ).map((node) => node.textContent);
  expect(metrics).toEqual(["1Generated", "1Failed", "2Eligible to re-run"]);
  dialog.querySelectorAll(".planning-bulk-results__card-metric").forEach((metric) => {
    expect(metric.querySelector("strong")).not.toBeNull();
    expect(metric.querySelector(".planning-bulk-results__card-label")).not.toBeNull();
  });
  expect(lastAction(listener.actions)).toEqual({ type: "bulk_view_results" });
  listener.stop();
});

it("does not mislabel a safe/no-rewrite result as ready", () => {
  const { dialog } = openResults();
  const badgeFor = (title: string) => {
    const row = within(dialog).getByText(title).closest("tr") as HTMLElement;
    return row.querySelector(".planning-bulk-results__badge")?.textContent;
  };
  expect(badgeFor("Senior Applied AI Engineer")).toEqual("Ready rewrites");
  // no_safe_rewrites must never be relabelled as ready.
  expect(badgeFor("Staff Data Scientist")).toEqual("Safe / no rewrite");
  expect(
    within(dialog).getByText("Staff Data Scientist").closest("tr")
      ?.querySelector(".planning-bulk-results__badge")?.className,
  ).toContain("is-neutral");
  expect(badgeFor("ML Platform Engineer")).toEqual("Failed");
});

it("searches by job title and by company", () => {
  const { dialog } = openResults();
  const search = within(dialog).getByRole("searchbox", { name: /search jobs or companies/i });
  fireEvent.change(search, { target: { value: "northwind" } });
  expect(within(dialog).queryByText("Senior Applied AI Engineer")).toBeNull();
  expect(within(dialog).getByText("Staff Data Scientist")).toBeTruthy();
  fireEvent.change(search, { target: { value: "senior applied" } });
  expect(within(dialog).getByText("Senior Applied AI Engineer")).toBeTruthy();
  expect(within(dialog).queryByText("Staff Data Scientist")).toBeNull();
});

it("filters by status pill", () => {
  const { dialog } = openResults();
  fireEvent.click(within(dialog).getByRole("button", { name: /failed \/ attention/i }));
  expect(within(dialog).getByText("ML Platform Engineer")).toBeTruthy();
  expect(within(dialog).queryByText("Senior Applied AI Engineer")).toBeNull();
});

it("selects only eligible rows and keeps non-rerunnable checkboxes disabled", () => {
  const { dialog } = openResults();
  const generatedRow = within(dialog).getByRole("checkbox", { name: /select senior applied ai engineer/i });
  expect(generatedRow).toBeDisabled();
  fireEvent.click(within(dialog).getByRole("checkbox", { name: /select all eligible/i }));
  expect(within(dialog).getByText("2 jobs selected")).toBeTruthy();
  expect(generatedRow).not.toBeChecked();
});

it("updates the selected count and clears the selection", () => {
  const { dialog } = openResults();
  const checkbox = within(dialog).getByRole("checkbox", { name: /select staff data scientist/i });
  const clearSelection = within(dialog).getByRole("button", { name: /clear selection/i });
  expect(clearSelection.tagName).toBe("BUTTON");
  expect(clearSelection.className).toContain("planning-bulk-results__clear");
  const row = checkbox.closest("tr") as HTMLElement;
  expect(row.className).not.toContain("is-selected");
  fireEvent.click(checkbox);
  expect(checkbox).toBeChecked();
  expect(row.className).toContain("is-selected");
  expect(within(dialog).getByText("1 job selected")).toBeTruthy();
  fireEvent.click(clearSelection);
  expect(checkbox).not.toBeChecked();
  expect(row.className).not.toContain("is-selected");
  expect(within(dialog).getByText("0 jobs selected")).toBeTruthy();
});

it("re-run selected publishes the exact stable job identities", () => {
  const listener = listenForActions();
  const { dialog } = openResults();
  fireEvent.click(within(dialog).getByRole("checkbox", { name: /select staff data scientist/i }));
  fireEvent.click(within(dialog).getByRole("button", { name: /re-run selected \(1\)/i }));
  expect(lastAction(listener.actions)).toEqual({
    type: "bulk_rerun",
    scope: "selected",
    jobIdentities: ["job-2"],
  });
  listener.stop();
});

it("re-run all eligible publishes the full eligible scope and stays enabled at zero selection", () => {
  const listener = listenForActions();
  const { dialog } = openResults();
  const runAll = within(dialog).getByRole("button", { name: /re-run all eligible \(2\)/i });
  expect(runAll).not.toBeDisabled();
  expect(within(dialog).getByRole("button", { name: /re-run selected \(0\)/i })).toBeDisabled();
  fireEvent.click(runAll);
  expect(lastAction(listener.actions)).toEqual({
    type: "bulk_rerun",
    scope: "eligible",
    jobIdentities: ["job-2", "job-3"],
  });
  listener.stop();
});

it("closes on Escape and returns focus to the trigger", () => {
  const { trigger } = openResults();
  fireEvent.keyDown(document, { key: "Escape" });
  expect(screen.queryByRole("dialog", { name: /bulk generation results/i })).toBeNull();
  expect(document.activeElement).toEqual(trigger);
});

it("closes from the close button and returns focus to the trigger", () => {
  const { trigger, dialog } = openResults();
  fireEvent.click(within(dialog).getByRole("button", { name: /close bulk generation results/i }));
  expect(screen.queryByRole("dialog", { name: /bulk generation results/i })).toBeNull();
  expect(document.activeElement).toEqual(trigger);
});

it("shows the winner score when Bulk selected the winner resume", () => {
  const { dialog } = openResults();
  const row = within(dialog).getByText("Resume_A.pdf").closest("tr") as HTMLElement;
  expect(within(row).getByText("91.00%")).toBeTruthy();
});

it("shows the runner-up score when Bulk selected the runner-up resume", () => {
  const { dialog } = openResults();
  const row = within(dialog).getByText("Resume_B.pdf").closest("tr") as HTMLElement;
  expect(within(row).getByText("76.40%")).toBeTruthy();
});

it("shows a dash for an unknown selected resume even when candidate scores exist", () => {
  const { dialog } = openResults();
  const failedRow = within(dialog).getByText("ML Platform Engineer").closest("tr") as HTMLElement;
  expect(within(failedRow).getByText("—")).toBeTruthy();
});

it("shows a dash when the selected candidate has no numeric score", () => {
  const { dialog } = openResults({
    ...terminalBulk,
    resultItems: [{
      ...resultItems[0],
      selected_resume: "Resume_A.pdf",
      winner_resume: "Resume_A.pdf",
      winner_score: "not-scored",
      match_score: 0.99,
    }],
  });
  const row = within(dialog).getByText("Resume_A.pdf").closest("tr") as HTMLElement;
  expect(within(row).getByText("—")).toBeTruthy();
});

// --- Brandfetch company logos (presentation only, never a network call) -----

it("renders the local lettermark and no image when no logo domain is resolved", () => {
  const fetchMock = vi.fn();
  vi.stubGlobal("fetch", fetchMock);
  const { container } = render(<CompanyLogo company="Northwind" clientId="client-123" />);
  expect(fetchMock).not.toHaveBeenCalled();
  expect(container.querySelector("img")).toBeNull();
  expect(container.querySelector(".planning-bulk-results__lettermark")?.textContent).toEqual("NO");
});

it("makes no request and shows no image when no client id is configured", () => {
  const fetchMock = vi.fn();
  vi.stubGlobal("fetch", fetchMock);
  const { container } = render(<CompanyLogo company="Northwind" domain="northwind.com" />);
  expect(fetchMock).not.toHaveBeenCalled();
  expect(container.querySelector("img")).toBeNull();
});

it("renders the Brandfetch CDN icon for a resolved domain without any request", () => {
  const fetchMock = vi.fn();
  vi.stubGlobal("fetch", fetchMock);
  const { container } = render(
    <CompanyLogo company="Northwind" domain="northwind.com" clientId="client-123" />,
  );
  expect(fetchMock).not.toHaveBeenCalled();
  const img = container.querySelector("img") as HTMLImageElement;
  expect(img.getAttribute("loading")).toEqual("lazy");
  expect(img.getAttribute("width")).toEqual("32");
  // Explicit documented Logo API domain route.
  expect(img.getAttribute("src")).toContain("cdn.brandfetch.io/domain/northwind.com");
  expect(img.getAttribute("src")).toContain("type/icon");
  expect(img.getAttribute("src")).toContain("w/64/h/64");
  expect(img.getAttribute("src")).toContain("fallback/lettermark");
});

it("falls back to the lettermark when the Brandfetch image fails to load", () => {
  vi.stubGlobal("fetch", vi.fn());
  const { container } = render(
    <CompanyLogo company="Northwind" domain="northwind.com" clientId="client-123" />,
  );
  fireEvent.error(container.querySelector("img") as HTMLImageElement);
  expect(container.querySelector("img")).toBeNull();
  expect(container.querySelector(".planning-bulk-results__lettermark")?.textContent).toEqual("NO");
});

it("renders logos inside the results table without any network call", () => {
  const fetchMock = vi.fn();
  vi.stubGlobal("fetch", fetchMock);
  const { dialog } = openResults({
    ...terminalBulk,
    brandfetchClientId: "client-123",
    resultItems: resultItems.map((item) => ({ ...item, company_domain: "northwind.com" })),
  });
  expect(dialog.querySelectorAll(".planning-bulk-results__logo").length).toEqual(3);
  expect(fetchMock).not.toHaveBeenCalled();
});

// --- Visual/structural contracts for the approved dark workspace ------------

it("uses a theme-neutral modal root so the page theme can select its palette", () => {
  const { dialog } = openResults();
  expect(dialog.className).toEqual("planning-bulk-results");
});

it("exposes exactly one search control shell with no nested duplicate shell", () => {
  const { dialog } = openResults();
  const shells = dialog.querySelectorAll(".planning-bulk-results__search");
  expect(shells).toHaveLength(1);
  const inputs = shells[0].querySelectorAll("input");
  expect(inputs).toHaveLength(1);
  // The input carries the opt-out class so the global `input { ... !important }`
  // page skin cannot repaint it with a second border.
  expect(inputs[0].className).toContain("planning-bulk-results__search-input");
  expect(shells[0].querySelectorAll(".planning-bulk-results__search")).toHaveLength(0);
});

it("gives the close control an accessible label and a visible glyph", () => {
  const { dialog } = openResults();
  const close = within(dialog).getByRole("button", { name: /close bulk generation results/i });
  expect(close.className).toContain("planning-bulk-results__close");
  expect(close.querySelector("svg")).not.toBeNull();
});

it("marks every modal checkbox so the global input skin cannot repaint it", () => {
  const { dialog } = openResults();
  const boxes = dialog.querySelectorAll('input[type="checkbox"]');
  expect(boxes.length).toBeGreaterThan(1);
  boxes.forEach((box) => expect(box.className).toContain("planning-bulk-results__checkbox"));
});

it("truncates a long resume filename and keeps the full value on hover", () => {
  const longName = "Sriram_Neelakantan_AIML_resume_no_syn_v2_extended_variant.pdf";
  const { dialog } = openResults({
    ...terminalBulk,
    resultItems: [{ ...resultItems[0], selected_resume: longName }],
  });
  const name = dialog.querySelector(".planning-bulk-results__resume-name") as HTMLElement;
  expect(name.textContent).toEqual(longName);
  expect(name.getAttribute("title")).toEqual(longName);
});

// --- Selected-filter state + toolbar structure ------------------------------

it("marks exactly one filter active via aria-pressed and .is-active", () => {
  const { dialog } = openResults();
  const pills = Array.from(
    dialog.querySelectorAll(".planning-bulk-results__pill"),
  ) as HTMLElement[];
  expect(pills.length).toEqual(4);

  const active = () => pills.filter((p) => p.className.includes("is-active"));
  const pressed = () => pills.filter((p) => p.getAttribute("aria-pressed") === "true");
  expect(active()).toHaveLength(1);
  expect(pressed()).toHaveLength(1);
  expect(active()[0].textContent).toContain("All");

  fireEvent.click(within(dialog).getByRole("button", { name: /failed \/ attention/i }));
  expect(active()).toHaveLength(1);
  expect(pressed()).toHaveLength(1);
  expect(active()[0].textContent).toContain("Failed / attention");
});

it("keeps every filter pill and its count in one toolbar row", () => {
  const { dialog } = openResults();
  const toolbar = dialog.querySelector(".planning-bulk-results__controls") as HTMLElement;
  expect(toolbar.querySelectorAll(".planning-bulk-results__search")).toHaveLength(1);
  const pills = Array.from(toolbar.querySelectorAll(".planning-bulk-results__pill"));
  expect(pills).toHaveLength(4);
  expect(pills.map((pill) => pill.textContent)).toEqual([
    "All3",
    "Generated / Ready1",
    "Safe / no rewrite1",
    "Failed / attention1",
  ]);
  expect(toolbar.querySelectorAll(".planning-bulk-results__select-all")).toHaveLength(1);
  pills.forEach((pill) => {
    expect(pill.querySelector("small")).not.toBeNull();
  });
});

it("omits only the redundant Eligible filter and preserves eligible bulk actions", () => {
  const { dialog } = openResults();
  const filterGroup = within(dialog).getByRole("group", { name: /filter results/i });
  expect(within(filterGroup).queryByRole("button", { name: /^eligible/i })).toBeNull();
  expect(within(dialog).getByRole("checkbox", { name: /select all eligible/i })).toBeTruthy();
  expect(within(dialog).getByRole("button", { name: /re-run all eligible \(2\)/i })).toBeTruthy();
});

it("keeps the footer secondary and primary actions structurally distinct", () => {
  const { dialog } = openResults();
  const secondary = within(dialog).getByRole("button", { name: /re-run all eligible/i });
  const primary = within(dialog).getByRole("button", { name: /re-run selected/i });
  expect(secondary.className).toContain("planning-bulk-results__secondary");
  expect(primary.className).toContain("planning-bulk-results__primary");
  expect(primary).toBeDisabled();
  expect(secondary).not.toBeDisabled();
});

// --- Filter semantic tones + truthful match score ---------------------------

const scoreItem = (over: Partial<BulkResultItem> = {}): BulkResultItem => ({
  job_identity: "j",
  selected_resume: "Sriram_Analytics.pdf",
  winner_resume: "Sriram_Analytics.pdf",
  winner_score: "0.856725",
  runner_up_resume: "Sriram_Quantitative.pdf",
  runner_up_score: "0.824291",
  ...over,
});

it("gives every filter its own semantic tone class", () => {
  const { dialog } = openResults();
  const tones = Array.from(dialog.querySelectorAll(".planning-bulk-results__pill")).map(
    (pill) => Array.from(pill.classList).find((c) => c.startsWith("is-tone-")),
  );
  expect(tones).toEqual(["is-tone-all", "is-tone-generated", "is-tone-safe", "is-tone-attention"]);
});

it("keeps the semantic tone class when a filter becomes active", () => {
  const { dialog } = openResults();
  const safe = within(dialog).getByRole("button", { name: /safe \/ no rewrite/i });
  expect(safe.classList.contains("is-tone-safe")).toBe(true);
  expect(safe.classList.contains("is-active")).toBe(false);

  fireEvent.click(safe);
  // Tone survives selection; selection only adds .is-active.
  expect(safe.classList.contains("is-tone-safe")).toBe(true);
  expect(safe.classList.contains("is-active")).toBe(true);

  const all = within(dialog).getByRole("button", { name: /^All/ });
  expect(all.classList.contains("is-tone-all")).toBe(true);
  expect(all.classList.contains("is-active")).toBe(false);
});

it("pairs the winner resume with the winner score", () => {
  expect(bulkResultMatchScore(scoreItem())).toBeCloseTo(0.856725);
  expect(formatBulkMatchScore(scoreItem())).toEqual("85.67%");
});

it("pairs the runner-up resume with the runner-up score", () => {
  const item = scoreItem({ selected_resume: "Sriram_Quantitative.pdf" });
  expect(bulkResultMatchScore(item)).toBeCloseTo(0.824291);
  expect(formatBulkMatchScore(item)).toEqual("82.43%");
});

it("normalizes path and separator differences when pairing the resume", () => {
  const item = scoreItem({ selected_resume: "outputs\\resumes/Sriram_Analytics.pdf  " });
  expect(formatBulkMatchScore(item)).toEqual("85.67%");
});

it("shows an em dash when the selected resume matches no candidate", () => {
  expect(formatBulkMatchScore(scoreItem({ selected_resume: "SomeoneElse.pdf" }))).toEqual("—");
});

it("shows an em dash when the paired score is missing or non-numeric", () => {
  expect(formatBulkMatchScore(scoreItem({ winner_score: "" }))).toEqual("—");
  expect(formatBulkMatchScore(scoreItem({ winner_score: "n/a" }))).toEqual("—");
  expect(formatBulkMatchScore(scoreItem({ winner_score: null }))).toEqual("—");
});

it("keeps the score visible beside a truncated long resume name", () => {
  const longName = "Sriram_Neelakantan_AIML_resume_no_syn_v2_extended_variant.pdf";
  const { dialog } = openResults({
    ...terminalBulk,
    resultItems: [
      {
        ...resultItems[0],
        selected_resume: longName,
        winner_resume: longName,
        winner_score: "0.5125",
      },
    ],
  });
  const name = dialog.querySelector(".planning-bulk-results__resume-name") as HTMLElement;
  const score = dialog.querySelector(".planning-bulk-results__resume-score") as HTMLElement;
  expect(name.getAttribute("title")).toEqual(longName);
  expect(score.textContent).toEqual("51.25%");
});
