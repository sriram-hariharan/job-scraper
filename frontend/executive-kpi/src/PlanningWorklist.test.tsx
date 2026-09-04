import { fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import {
  PLANNING_ACTION_EVENT,
  PLANNING_COLUMN_WIDTH_STORAGE_KEY,
  PlanningFiltersToolbar,
  PlanningSummary,
  PlanningWorklist,
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
