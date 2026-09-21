import { render, screen } from "@testing-library/react";
import { AnalyticsDashboard, SnapshotTooltip } from "./AnalyticsDashboard";

const metrics = {
  queueRows: 128,
  nextSteps: 42,
  undecidedJobReviews: 9,
  undecidedMaybeTailor: 6,
};

describe("AnalyticsDashboard", () => {
  it("renders four premium loading cards without fake values", () => {
    const { container } = render(<AnalyticsDashboard state={{ status: "loading" }} />);
    expect(container.querySelectorAll("[aria-busy='true']")).toHaveLength(4);
    expect(screen.getByText("Queue Rows")).toBeInTheDocument();
    expect(screen.queryByText("128")).not.toBeInTheDocument();
  });

  it("renders the four existing KPI meanings from supplied status data", () => {
    render(<AnalyticsDashboard state={{ status: "ready", metrics }} />);
    expect(screen.getByText("Queue Rows")).toBeInTheDocument();
    expect(screen.getByText("Next Steps")).toBeInTheDocument();
    expect(screen.getByText("Undecided Job Reviews")).toBeInTheDocument();
    expect(screen.getByText("Undecided Maybe Tailor")).toBeInTheDocument();
    for (const value of ["128", "42", "9", "6"]) {
      expect(screen.getByText(value)).toBeInTheDocument();
    }
    expect(screen.getAllByText("Current personalized snapshot")).toHaveLength(4);
    expect(screen.queryByText("Stale snapshot")).not.toBeInTheDocument();
    expect(screen.queryByText("Aging snapshot")).not.toBeInTheDocument();
  });

  it("preserves real zero values instead of treating them as missing", () => {
    render(<AnalyticsDashboard state={{
      status: "ready",
      metrics: {
        queueRows: 0,
        nextSteps: 0,
        undecidedJobReviews: 0,
        undecidedMaybeTailor: 0,
      },
      snapshot: { status: "stale", runId: "run-zero", completedAt: "2026-05-17T12:00:00Z", totalJobs: 0 },
    }} />);

    expect(screen.getAllByText("0")).toHaveLength(4);
    expect(screen.queryByText("—")).not.toBeInTheDocument();
    expect(screen.getAllByText("Stale snapshot")).toHaveLength(4);
    expect(screen.getByText("Personalized recommendations are out of date")).toBeInTheDocument();
    expect(screen.getByText(/Last personalized refresh: May 17, 2026/)).toBeInTheDocument();
    expect(screen.getByText(/No matching jobs were found/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /refresh my jobs|view pipeline/i })).not.toBeInTheDocument();
  });

  it("renders one cohesive not-generated state without four misleading zeroes", () => {
    render(<AnalyticsDashboard state={{
      status: "ready",
      metrics: { queueRows: 0, nextSteps: 0, undecidedJobReviews: 0, undecidedMaybeTailor: 0 },
      snapshot: { status: "not_generated", runId: "", completedAt: "", totalJobs: 0 },
    }} />);
    expect(screen.getByText("Your personalized job recommendations are not ready yet.")).toBeInTheDocument();
    expect(screen.queryByText("0")).not.toBeInTheDocument();
  });

  it("labels aging snapshots and keeps their timestamped values visible", () => {
    render(<AnalyticsDashboard state={{
      status: "ready", metrics,
      snapshot: { status: "aging", runId: "run-aging", completedAt: "2026-09-15T12:00:00Z", totalJobs: 128 },
    }} />);
    expect(screen.getAllByText("Aging snapshot")).toHaveLength(4);
    expect(screen.getAllByText(/Sep 15, 2026 personalized refresh/)).toHaveLength(4);
    expect(screen.getByText("Personalized recommendations are getting older")).toBeInTheDocument();
    expect(screen.getByText("128")).toBeInTheDocument();
  });

  it("renders the current tooltip only while active and preserves a zero value", () => {
    const { rerender } = render(
      <SnapshotTooltip active payload={[{ payload: { current: 0, baseline: 0 } }]} />,
    );

    expect(screen.getByText("Current")).toBeInTheDocument();
    expect(screen.getByText("0")).toBeInTheDocument();
    expect(screen.queryByText(/queue baseline/i)).not.toBeInTheDocument();

    rerender(<SnapshotTooltip active={false} payload={[{ payload: { current: 22, baseline: 128 } }]} />);
    expect(screen.queryByText("Current")).not.toBeInTheDocument();
    expect(screen.queryByText("22")).not.toBeInTheDocument();
  });

  it("renders a restrained unavailable state without crashing", () => {
    render(<AnalyticsDashboard state={{ status: "error", message: "network unavailable" }} />);
    expect(screen.getAllByText("Unavailable")).toHaveLength(4);
    expect(screen.getAllByText("Reload the page to try again.")).toHaveLength(4);
  });
});
