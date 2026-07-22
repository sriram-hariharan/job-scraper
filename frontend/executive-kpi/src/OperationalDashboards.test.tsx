import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import {
  APPLICATIONS_ACTION_EVENT,
  ApplicationsDashboard,
  DECISIONS_ACTION_EVENT,
  DecisionsDashboard,
  DEFAULT_APPLICATIONS_STATE,
  DEFAULT_DECISIONS_STATE,
} from "./OperationalDashboards";

describe("operational dashboards", () => {
  const applicationRow = {
    action_key: "one",
    action_timestamp: "2026-07-19T12:00:00Z",
    job_title: "ML Engineer",
    job_company: "Example",
    application_status: "APPLIED",
    source_view: "decisions",
    note: "Submitted manually",
    job_url: "https://example.test/job",
  };

  it("renders decision evidence and emits only a controlled manual open event", () => {
    const listener = vi.fn(); window.addEventListener(DECISIONS_ACTION_EVENT, listener);
    render(<DecisionsDashboard state={{ ...DEFAULT_DECISIONS_STATE, status: "ready", resultKey: "one", pagination: { ...DEFAULT_DECISIONS_STATE.pagination, totalCount: 1 }, rows: [{ job_doc_id: "https://example.test/job", job_title: "Applied AI Engineer", job_company: "Example", decision_timestamp: "2026-07-19T12:00:00Z", decision: "APPLY", planning_action: "APPLY", selected_resume: "AI2.pdf", winner_resume: "AI2.pdf", runner_up_resume: "AI1.pdf", note: "Review manually" }] }} />);
    expect(screen.getByText("Operator decisions")).toBeInTheDocument();
    expect(screen.getAllByText("APPLY")).toHaveLength(2);
    fireEvent.click(screen.getByRole("button", { name: "Open job" }));
    expect(listener).toHaveBeenCalledTimes(1);
    expect((listener.mock.calls[0][0] as CustomEvent).detail.type).toBe("open_application");
    window.removeEventListener(DECISIONS_ACTION_EVENT, listener);
  });

  it("keeps applied and saved views distinct and emits one tab event", () => {
    const listener = vi.fn(); window.addEventListener(APPLICATIONS_ACTION_EVENT, listener);
    const { rerender } = render(<ApplicationsDashboard state={{ ...DEFAULT_APPLICATIONS_STATE, status: "ready", resultKey: "one", rows: [applicationRow], pagination: { ...DEFAULT_APPLICATIONS_STATE.pagination, totalCount: 1 } }} />);
    const applied = screen.getByRole("tab", { name: "Applied Jobs" });
    const saved = screen.getByRole("tab", { name: "Saved for Later" });
    expect(applied).toHaveAttribute("aria-selected", "true");
    expect(applied).toHaveClass("is-active");
    expect(applied).not.toHaveClass("is-inactive");
    expect(saved).toHaveAttribute("aria-selected", "false");
    expect(saved).toHaveClass("is-inactive");
    expect(saved).not.toHaveClass("is-active");
    expect(applied).toHaveClass("preferences-secondary-action", "applications-tab");
    expect(saved).toHaveClass("preferences-secondary-action", "applications-tab");
    expect(screen.getByText("APPLIED")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Open job" })).toHaveAttribute("rel", "noopener noreferrer");
    fireEvent.click(applied);
    expect(listener).not.toHaveBeenCalled();
    fireEvent.click(saved);
    expect(listener).toHaveBeenCalledTimes(1);
    expect((listener.mock.calls[0][0] as CustomEvent).detail).toEqual({ type: "tab_change", tab: "SAVED" });
    rerender(<ApplicationsDashboard state={{ ...DEFAULT_APPLICATIONS_STATE, status: "ready", activeTab: "SAVED", resultKey: "two", rows: [], pagination: { ...DEFAULT_APPLICATIONS_STATE.pagination, totalCount: 0 } }} />);
    expect(screen.getByRole("tab", { name: "Applied Jobs" })).not.toHaveClass("is-active");
    expect(screen.getByRole("tab", { name: "Applied Jobs" })).toHaveClass("is-inactive");
    expect(screen.getByRole("tab", { name: "Saved for Later" })).toHaveClass("is-active");
    expect(screen.getByRole("tab", { name: "Saved for Later" })).not.toHaveClass("is-inactive");
    expect(screen.getByText("No jobs have been saved for later.")).toBeInTheDocument();
    window.removeEventListener(APPLICATIONS_ACTION_EVENT, listener);
  });

  it("uses one keyboard tab transition and preserves the filter action hierarchy", () => {
    const listener = vi.fn(); window.addEventListener(APPLICATIONS_ACTION_EVENT, listener);
    render(<ApplicationsDashboard state={{ ...DEFAULT_APPLICATIONS_STATE, status: "ready", rows: [], resultKey: "empty" }} />);
    fireEvent.keyDown(screen.getByRole("tab", { name: "Applied Jobs" }), { key: "ArrowRight" });
    expect(listener).toHaveBeenCalledTimes(1);
    expect((listener.mock.calls[0][0] as CustomEvent).detail).toEqual({ type: "tab_change", tab: "SAVED" });
    expect(screen.getByRole("button", { name: "Apply Filters" })).toHaveClass("operational-primary-action");
    expect(screen.getByRole("button", { name: "Clear" })).toHaveClass("operational-secondary-action");
    window.removeEventListener(APPLICATIONS_ACTION_EVENT, listener);
  });

  it("renders truthful loading, row, empty, and error states without mixing them", () => {
    const { container, rerender } = render(<ApplicationsDashboard state={DEFAULT_APPLICATIONS_STATE} />);
    expect(container.querySelectorAll(".shared-table-skeleton-row")).toHaveLength(5);
    expect(screen.queryByText("No applied jobs yet.")).not.toBeInTheDocument();
    expect(screen.getAllByText("Loading jobs...")).toHaveLength(3);
    expect(screen.getAllByText("-").length).toBeGreaterThan(0);

    rerender(<ApplicationsDashboard state={{ ...DEFAULT_APPLICATIONS_STATE, status: "ready", rows: [applicationRow], resultKey: "ready", pagination: { ...DEFAULT_APPLICATIONS_STATE.pagination, totalCount: 1 } }} />);
    expect(container.querySelector(".shared-table-skeleton-row")).not.toBeInTheDocument();
    expect(screen.getByText("ML Engineer")).toBeInTheDocument();
    const table = screen.getByRole("table");
    expect(table).toHaveStyle({ width: "100%" });
    expect(within(table).getByRole("columnheader", { name: "Open" })).toHaveClass("is-sticky-action");

    rerender(<ApplicationsDashboard state={{ ...DEFAULT_APPLICATIONS_STATE, status: "ready", rows: [], resultKey: "empty" }} />);
    expect(screen.getByText("No applied jobs yet.")).toBeInTheDocument();
    expect(container.querySelector(".shared-table-skeleton-row")).not.toBeInTheDocument();

    rerender(<ApplicationsDashboard state={{ ...DEFAULT_APPLICATIONS_STATE, status: "error", message: "Network unavailable", resultKey: "error" }} />);
    expect(screen.getByRole("alert")).toHaveTextContent("Network unavailable");
    expect(screen.queryByText("No applied jobs yet.")).not.toBeInTheDocument();
  });

  it("keeps Decisions loading truthful and its manual action pinned", () => {
    const { container, rerender } = render(<DecisionsDashboard state={DEFAULT_DECISIONS_STATE} />);
    expect(container.querySelectorAll(".shared-table-skeleton-row")).toHaveLength(5);
    expect(screen.queryByText("No operator decisions match the current filters.")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Apply Filters" })).toHaveClass("operational-primary-action");
    expect(screen.getByRole("button", { name: "Clear" })).toHaveClass("operational-secondary-action");

    rerender(<DecisionsDashboard state={{ ...DEFAULT_DECISIONS_STATE, status: "ready", rows: [], resultKey: "empty" }} />);
    expect(screen.getByText("No operator decisions match the current filters.")).toBeInTheDocument();
    const table = screen.getByRole("table");
    expect(table).toHaveStyle({ width: "100%" });
    expect(within(table).getByRole("columnheader", { name: "Manual action" })).toHaveClass("is-sticky-action");
  });

  it("uses the shared premium Decisions multi-select without requesting before Apply", () => {
    const listener = vi.fn(); window.addEventListener(DECISIONS_ACTION_EVENT, listener);
    render(<DecisionsDashboard state={{ ...DEFAULT_DECISIONS_STATE, status: "ready", rows: [], resultKey: "filters" }} />);

    const trigger = screen.getByRole("button", { name: "Decision All" });
    expect(trigger).toHaveClass("shared-filter-select__trigger");
    fireEvent.click(trigger);
    fireEvent.click(screen.getByRole("option", { name: "APPLY" }));
    expect(screen.getByRole("listbox", { name: "Decision" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("option", { name: "TAILOR" }));
    expect(listener).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "Decision 2 selected" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "APPLY" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("option", { name: "TAILOR" })).toHaveAttribute("aria-selected", "true");

    fireEvent.click(screen.getByRole("button", { name: "Apply Filters" }));
    expect(listener).toHaveBeenCalledTimes(1);
    expect((listener.mock.calls[0][0] as CustomEvent).detail.filters.decisions).toEqual(["APPLY", "TAILOR"]);
    fireEvent.click(screen.getByRole("button", { name: "Clear" }));
    expect(listener).toHaveBeenCalledTimes(2);
    expect((listener.mock.calls[1][0] as CustomEvent).detail).toEqual({ type: "clear_filters" });
    window.removeEventListener(DECISIONS_ACTION_EVENT, listener);
  });
});
