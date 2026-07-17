import { render, screen } from "@testing-library/react";
import { AnalyticsDashboard } from "./AnalyticsDashboard";

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
    expect(screen.getAllByText("Current snapshot")).toHaveLength(4);
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
    }} />);

    expect(screen.getAllByText("0")).toHaveLength(4);
    expect(screen.queryByText("—")).not.toBeInTheDocument();
  });

  it("renders a restrained unavailable state without crashing", () => {
    render(<AnalyticsDashboard state={{ status: "error", message: "network unavailable" }} />);
    expect(screen.getAllByText("Unavailable")).toHaveLength(4);
    expect(screen.getAllByText("Refresh Status to try again.")).toHaveLength(4);
  });
});
