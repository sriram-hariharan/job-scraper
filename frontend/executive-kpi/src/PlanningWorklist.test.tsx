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

  fireEvent.click(screen.getByRole("button", { name: "Apply Filters" }));
  expect(lastAction(listener.actions)).toEqual(expect.objectContaining({
    type: "apply_filters",
    filters: expect.objectContaining({ actions: ["APPLY"], preferenceIds: ["applied_ai", "data_engineering"], limit: 15 }),
  }));

  fireEvent.click(screen.getByRole("button", { name: "Clear" }));
  expect(lastAction(listener.actions)).toEqual({ type: "clear_filters" });
  listener.stop();
});
