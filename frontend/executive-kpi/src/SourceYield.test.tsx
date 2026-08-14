import { fireEvent, render, screen } from "@testing-library/react";
import { SourceYield, sourceYieldHealth, type SourceYieldData, type SourceYieldRow } from "./SourceYield";

const row: SourceYieldRow = {
  source: "usajobs",
  accounts_queried: 2,
  scraped_jobs: 120,
  title_pass_jobs: 80,
  title_reject_jobs: 40,
  location_pass_jobs: 62,
  location_reject_jobs: 18,
  freshness_pass_jobs: 48,
  not_recent_jobs: 11,
  missing_timestamp_jobs: 3,
  final_corpus_jobs: 15,
  final_display_jobs: 15,
  yield_percent: 12.5,
  raw_job_count: 120,
  normalized_job_count: 116,
  page_count: 4,
  request_count: 5,
  retry_count: 1,
  partial_result_count: 1,
  acquisition_status_counts: { SUCCESS: 1, PARTIAL: 1, EMPTY: 0, FAILED: 0 },
  timestamp_present_count: 112,
  timestamp_missing_count: 4,
  description_present_count: 110,
  description_missing_count: 6,
  canonical_url_present_count: 116,
  canonical_url_missing_count: 0,
};

const data: SourceYieldData = {
  available: true,
  run_id: "run-13j",
  generated_from: {
    source_health_report: true,
    source_acquisition_metrics: true,
    current_run_job_corpus: false,
  },
  totals: {
    source_count: 1,
    accounts_queried: 2,
    scraped_jobs: 120,
    title_pass_jobs: 80,
    location_pass_jobs: 62,
    freshness_pass_jobs: 48,
    final_corpus_jobs: 15,
    final_display_jobs: 15,
  },
  sources: [row],
};

describe("SourceYield", () => {
  it("renders the compact source funnel contract and accessible details", () => {
    render(<SourceYield state={{ status: "ready", data }} />);

    expect(screen.getByRole("heading", { name: "Source Yield" })).toBeInTheDocument();
    for (const heading of ["Source", "Targets queried", "Acquired", "Title pass", "U.S. pass", "Fresh 24h", "Final jobs", "Yield", "Health"]) {
      expect(screen.getByRole("columnheader", { name: heading })).toBeInTheDocument();
    }
    expect(screen.getByText("12.5%")).toBeInTheDocument();
    expect(screen.getByText("Degraded")).toHaveAttribute(
      "title",
      "Successful targets: 1; partial targets: 1; empty targets: 0; failed targets: 0.",
    );
    const targetChip = screen.getByLabelText("Source yield summary").querySelector("[title]");
    expect(targetChip).toHaveTextContent("2 targets queried");
    expect(targetChip).toHaveAttribute(
      "title",
      "Company boards, ATS tenants, global feeds, or configured query profiles contacted during this run.",
    );
    expect(screen.getByText("Targets queried")).toHaveAccessibleDescription(
      "Company boards, ATS tenants, global feeds, or configured query profiles contacted during this run.",
    );
    expect(screen.getByText("Sources shown reflect the latest completed pipeline run.")).toBeInTheDocument();

    const expand = screen.getByRole("button", { name: "Usajobs" });
    expect(expand).toHaveAttribute("aria-expanded", "false");
    fireEvent.click(expand);
    expect(expand).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByText("Conversion funnel")).toBeInTheDocument();
    expect(screen.getByText(/timestamp 112 present \/ 4 missing/i)).toBeInTheDocument();
  });

  it.each([
    [28, 0, 0, 1, "Degraded"],
    [89, 0, 0, 1, "Degraded"],
    [159, 0, 0, 1, "Degraded"],
    [0, 0, 0, 1, "Failed"],
    [0, 1, 0, 0, "Partial"],
    [12, 0, 0, 0, "Healthy"],
    [0, 0, 7, 0, "Empty"],
    [0, 0, 0, 0, "Unavailable"],
  ])(
    "derives aggregate health from %i success, %i partial, %i empty, and %i failed targets",
    (success, partial, empty, failed, expected) => {
      expect(sourceYieldHealth({
        acquisition_status_counts: {
          SUCCESS: success,
          PARTIAL: partial,
          EMPTY: empty,
          FAILED: failed,
        },
      }).label).toBe(expected);
    },
  );

  it("keeps loading, unavailable, zero, and error states truthful", () => {
    const { rerender } = render(<SourceYield state={{ status: "loading" }} />);
    expect(screen.getByLabelText("Loading source yield")).toBeInTheDocument();

    rerender(<SourceYield state={{ status: "ready", data: { ...data, available: false } }} />);
    expect(screen.getByText("Source evidence unavailable")).toBeInTheDocument();

    rerender(<SourceYield state={{ status: "ready", data: { ...data, sources: [], totals: { ...data.totals, source_count: 0 } } }} />);
    expect(screen.getByText("No source activity")).toBeInTheDocument();

    rerender(<SourceYield state={{ status: "error", message: "refresh failed" }} />);
    expect(screen.getByText("Source yield unavailable")).toBeInTheDocument();
    expect(screen.getByText("refresh failed")).toBeInTheDocument();
  });
});
