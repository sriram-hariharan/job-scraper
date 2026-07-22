import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  PIPELINE_ACCEPTED_RUN_EVENT_NAME,
  PIPELINE_ACCEPTED_RUN_STORAGE_KEY,
  PipelineDashboard,
  readPipelineStatus,
} from "./PipelineDashboard";
import { DEFAULT_STAGE_ORDER, PIPELINE_POLL_INTERVAL_MS, STAGE_LABELS } from "./pipelineModel";

const runningPipeline = {
  status: "running",
  run_id: "run-real-42",
  started_at: "2026-07-18T12:00:00Z",
  updated_at_utc: "2026-07-18T12:00:02Z",
  current_stage: "ai_evaluation",
  completed_stages: ["startup", "scraping", "filtering", "dedupe", "ranking"],
  stage_order: [...DEFAULT_STAGE_ORDER],
  stage_message: "Evaluating supported jobs",
  counts: {
    scraped_jobs: 120,
    filtered_jobs: 72,
    deduped_jobs: 68,
    ranked_jobs: 60,
    ai_jobs: 0,
    resume_matched_jobs: 12,
    malformed_metric: "not-a-count",
  },
  config: {
    job_limit: 120,
    planning_only: false,
    generate_llm_adjudication: true,
    output_dir: "/private/sensitive/output",
    api_key: "secret-value",
  },
};

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
  window.sessionStorage.clear();
  delete window.openApplyLensPipelineConfig;
  window.history.replaceState({}, "", "/");
});

describe("PipelineDashboard", () => {
  it("uses the shared app-page-header contract and keeps eyebrow/title/description unchanged", async () => {
    render(<PipelineDashboard readStatus={async () => ({ pipeline: { status: "idle" } })} launchPipeline={vi.fn()} />);
    await screen.findByText("Pipeline is idle");
    const header = screen.getByRole("banner");
    expect(header).toHaveClass("pipeline-dashboard-header");
    expect(header).toHaveClass("app-page-header");
    expect(within(header).getByText("Operations")).toHaveClass("app-page-header__eyebrow");
    expect(within(header).getByRole("heading", { level: 1 })).toHaveClass("app-page-header__title");
    expect(within(header).getByRole("heading", { level: 1 })).toHaveTextContent("Pipeline");
    expect(
      within(header).getByText("Monitor job collection, filtering, evaluation, resume matching, and planning."),
    ).toHaveClass("app-page-header__description");
    expect(within(header).getByRole("button", { name: "Refresh Status" })).toBeInTheDocument();
    expect(within(header).getByRole("button", { name: "Run Pipeline" })).toBeInTheDocument();
  });

  it("renders a premium loading state without fake counts or stages", () => {
    const neverResolves = () => new Promise<never>(() => undefined);
    render(<PipelineDashboard readStatus={neverResolves} launchPipeline={vi.fn()} />);
    expect(screen.getByLabelText("Loading pipeline status")).toHaveAttribute("aria-busy", "true");
    expect(screen.queryByText("Revenue")).not.toBeInTheDocument();
    expect(screen.queryByText("Scraped")).not.toBeInTheDocument();
  });

  it("renders the idle state and honest source-health unavailable state", async () => {
    render(<PipelineDashboard readStatus={async () => ({ pipeline: { status: "idle" } })} launchPipeline={vi.fn()} />);
    expect(await screen.findByText("Pipeline is idle")).toBeInTheDocument();
    expect(screen.getByText("Source health data is not available yet")).toBeInTheDocument();
    expect(screen.getByText("No source status is inferred from missing job counts.")).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "Run Pipeline" })).toHaveLength(1);
    expect(screen.getByText("Stage counts are not available for this run yet.")).toHaveClass("pipeline-empty-panel--compact");
    expect(screen.getByText("Flow data will appear when the run records stage counts.")).toHaveClass("pipeline-empty-panel--compact");
    expect(screen.getByText("Flow data will appear when the run records stage counts.").closest("section")).toHaveClass("pipeline-flow-panel--empty");
  });

  it("preserves canonical order and distinguishes completed, active, and pending stages", async () => {
    render(<PipelineDashboard readStatus={async () => ({ pipeline: runningPipeline })} launchPipeline={vi.fn()} />);
    const timeline = await screen.findByRole("list", { name: "Pipeline stages" });
    const stages = within(timeline).getAllByRole("listitem");
    expect(stages).toHaveLength(DEFAULT_STAGE_ORDER.length);
    expect(stages.map((stage) => stage.getAttribute("data-stage-index"))).toEqual(
      DEFAULT_STAGE_ORDER.map((_, index) => String(index + 1)),
    );
    expect(stages.map((stage) => stage.querySelector(".pipeline-stage-name")?.lastChild?.textContent)).toEqual(
      DEFAULT_STAGE_ORDER.map((stage) => STAGE_LABELS[stage]),
    );
    expect(within(stages[0]).getByText("Complete")).toBeInTheDocument();
    expect(within(stages[10]).getByText("Active")).toBeInTheDocument();
    expect(within(stages[15]).getByText("Pending")).toBeInTheDocument();
  });

  it("renders real counts including zero, omits missing counts, and uses real flow values", async () => {
    render(<PipelineDashboard readStatus={async () => ({ pipeline: runningPipeline })} launchPipeline={vi.fn()} />);
    expect((await screen.findAllByText("120")).length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText("AI Evaluated").parentElement).toHaveTextContent("0");
    expect(screen.queryByText("Detailed")).not.toBeInTheDocument();
    expect(screen.getByRole("img", { name: /Collected: 120.*Evaluated: 0.*Resume matched: 12/ })).toBeInTheDocument();
    expect(screen.queryByText("conversion")).not.toBeInTheDocument();
  });

  it("renders only safe configuration fields and supplied source-health evidence", async () => {
    const payload = {
      pipeline: {
        ...runningPipeline,
        source_health: [{ source: "Lever", status: "healthy", jobs_returned: 8 }],
      },
    };
    render(<PipelineDashboard readStatus={async () => payload} launchPipeline={vi.fn()} />);
    expect(await screen.findByText("Job limit")).toBeInTheDocument();
    expect(screen.getByText("Lever")).toBeInTheDocument();
    expect(screen.getByText("8 jobs")).toBeInTheDocument();
    expect(screen.queryByText("/private/sensitive/output")).not.toBeInTheDocument();
    expect(screen.queryByText("secret-value")).not.toBeInTheDocument();
  });

  it("renders succeeded and failed terminal states without changing run data", async () => {
    const { rerender } = render(
      <PipelineDashboard
        readStatus={async () => ({ pipeline: { ...runningPipeline, status: "succeeded", final_job_count: 7, finished_at: "2026-07-18T12:04:00Z" } })}
        launchPipeline={vi.fn()}
      />,
    );
    expect(await screen.findByText("Succeeded")).toBeInTheDocument();
    expect(screen.getByText("Final jobs").parentElement).toHaveTextContent("7");

    rerender(
      <PipelineDashboard
        readStatus={async () => ({ pipeline: { ...runningPipeline, status: "failed", return_code: 2, error: "Existing failure message" } })}
        launchPipeline={vi.fn()}
      />,
    );
    expect((await screen.findAllByText("Failed")).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Existing failure message")).toBeInTheDocument();
    expect(screen.getByText("Return code").parentElement).toHaveTextContent("2");
  });

  it("uses the existing launch callback and status reader for Run and Refresh", async () => {
    const launchPipeline = vi.fn();
    const readStatus = vi.fn().mockResolvedValue({ pipeline: { status: "idle" } });
    render(<PipelineDashboard readStatus={readStatus} launchPipeline={launchPipeline} />);
    await screen.findByText("Pipeline is idle");
    fireEvent.click(screen.getByRole("button", { name: "Run Pipeline" }));
    expect(launchPipeline).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole("button", { name: "Refresh Status" }));
    await waitFor(() => expect(readStatus).toHaveBeenCalledTimes(2));
  });

  it("disables launch while a run is active and keeps Refresh Status available", async () => {
    const launchPipeline = vi.fn();
    const readStatus = vi.fn().mockResolvedValue({ pipeline: runningPipeline });
    render(<PipelineDashboard readStatus={readStatus} launchPipeline={launchPipeline} />);

    const activeRunButton = await screen.findByRole("button", { name: "Pipeline Running..." });
    expect(activeRunButton).toBeDisabled();
    fireEvent.click(activeRunButton);
    expect(launchPipeline).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "Refresh Status" })).toBeEnabled();
    expect(document.querySelector(".pipeline-running-indicator")).toHaveAttribute("role", "status");
    expect(screen.getByText("Live run in progress")).toBeInTheDocument();
    expect(document.querySelector(".pipeline-run-summary")).toHaveAttribute("aria-busy", "true");
    expect(document.querySelector(".pipeline-stage-progress")).toBeInTheDocument();
    expect(document.querySelector(".pipeline-running-strip")).toBeInTheDocument();
  });

  it.each(["idle", "succeeded", "failed"])("does not render the active indicator for %s", async (status) => {
    render(
      <PipelineDashboard
        readStatus={async () => ({ pipeline: { ...runningPipeline, status } })}
        launchPipeline={vi.fn()}
      />,
    );
    await waitFor(() => expect(document.querySelector(`.pipeline-run-summary--${status}`)).toBeInTheDocument());
    expect(screen.queryByText("Live run in progress")).not.toBeInTheDocument();
    expect(document.querySelector(".pipeline-running-strip")).not.toBeInTheDocument();
    expect(document.querySelector(".pipeline-run-summary")).toHaveAttribute("aria-busy", "false");
  });

  it("renders the same accessible running indicator while a run is starting", async () => {
    render(
      <PipelineDashboard
        readStatus={async () => ({ pipeline: { ...runningPipeline, status: "starting" } })}
        launchPipeline={vi.fn()}
      />,
    );
    expect(await screen.findByText("Live run in progress")).toBeInTheDocument();
    expect(document.querySelector(".pipeline-run-summary")).toHaveAttribute("aria-busy", "true");
  });

  it("uses a truthful generic failure title when no real stage was recorded", async () => {
    render(
      <PipelineDashboard
        readStatus={async () => ({
          pipeline: {
            ...runningPipeline,
            status: "failed",
            current_stage: "unknown",
            error: "OSError(7, 'Argument list too long')",
            return_code: 1,
          },
        })}
        launchPipeline={vi.fn()}
      />,
    );

    expect(await screen.findByRole("heading", { name: "Pipeline failed" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Unknown" })).not.toBeInTheDocument();
    expect(screen.getByText("OSError(7, 'Argument list too long')")).toBeInTheDocument();
    expect(screen.getByText("Return code").parentElement).toHaveTextContent("1");
  });

  it("opens the reviewed launch flow in place without navigating away from Pipeline", async () => {
    window.history.replaceState({}, "", "/pipeline");
    window.openApplyLensPipelineConfig = vi.fn();
    render(<PipelineDashboard readStatus={async () => ({ pipeline: { status: "idle" } })} />);
    await screen.findByText("Pipeline is idle");
    fireEvent.click(screen.getByRole("button", { name: "Run Pipeline" }));
    expect(window.openApplyLensPipelineConfig).toHaveBeenCalledTimes(1);
    expect(window.location.pathname).toBe("/pipeline");
  });

  it("immediately refreshes the canonical status owner for an accepted run", async () => {
    const readStatus = vi.fn()
      .mockResolvedValueOnce({ pipeline: { status: "idle" } })
      .mockResolvedValueOnce({ pipeline: { ...runningPipeline, run_id: "accepted-run-7" } });
    render(<PipelineDashboard readStatus={readStatus} launchPipeline={vi.fn()} />);
    await screen.findByText("Pipeline is idle");

    await act(async () => {
      window.dispatchEvent(new CustomEvent(PIPELINE_ACCEPTED_RUN_EVENT_NAME, {
        detail: {
          runId: "accepted-run-7",
          pipeline: { status: "starting", run_id: "accepted-run-7", current_stage: "startup" },
        },
      }));
    });

    await waitFor(() => expect(readStatus).toHaveBeenCalledTimes(2));
    expect(screen.queryByText("run-real-42")).not.toBeInTheDocument();
    expect(screen.getByText("accepted-run-7")).toBeInTheDocument();
    expect(screen.getByText("Running")).toBeInTheDocument();
    expect(window.sessionStorage.getItem(PIPELINE_ACCEPTED_RUN_STORAGE_KEY)).toBeNull();
  });

  it("renders a fast-completing accepted run as Succeeded rather than Idle", async () => {
    window.sessionStorage.setItem(PIPELINE_ACCEPTED_RUN_STORAGE_KEY, "fast-run-9");
    const readStatus = vi.fn().mockResolvedValue({
      pipeline: {
        ...runningPipeline,
        status: "succeeded",
        run_id: "fast-run-9",
        final_job_count: 4,
        finished_at: "2026-07-18T12:00:08Z",
      },
    });
    render(<PipelineDashboard readStatus={readStatus} launchPipeline={vi.fn()} />);
    expect(await screen.findByText("Succeeded")).toBeInTheDocument();
    expect(screen.queryByText("Pipeline is idle")).not.toBeInTheDocument();
    expect(readStatus).toHaveBeenCalledTimes(1);
  });

  it("does not fall back to Idle while an accepted run is still reconciling", async () => {
    window.sessionStorage.setItem(PIPELINE_ACCEPTED_RUN_STORAGE_KEY, "pending-run-3");
    const readStatus = vi.fn().mockResolvedValue({ pipeline: { status: "idle", run_id: "older-run" } });
    render(<PipelineDashboard readStatus={readStatus} launchPipeline={vi.fn()} />);
    expect(await screen.findByText("Starting")).toBeInTheDocument();
    expect(screen.getByText("pending-run-3")).toBeInTheDocument();
    expect(screen.queryByText("Pipeline is idle")).not.toBeInTheDocument();
  });

  it("creates one polling timer only while status is running", async () => {
    vi.useFakeTimers();
    const readStatus = vi.fn().mockResolvedValue({ pipeline: runningPipeline });
    const { unmount } = render(
      <PipelineDashboard readStatus={readStatus} launchPipeline={vi.fn()} pollIntervalMs={PIPELINE_POLL_INTERVAL_MS} />,
    );
    await act(async () => { await Promise.resolve(); });
    expect(readStatus).toHaveBeenCalledTimes(1);
    await act(async () => {
      vi.advanceTimersByTime(PIPELINE_POLL_INTERVAL_MS);
      await Promise.resolve();
    });
    expect(readStatus).toHaveBeenCalledTimes(2);
    unmount();
    vi.advanceTimersByTime(PIPELINE_POLL_INTERVAL_MS * 2);
    expect(readStatus).toHaveBeenCalledTimes(2);
  });

  it("reads status with one same-origin GET and never posts from the monitoring client", async () => {
    const fetchMock = vi.spyOn(window, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ pipeline: { status: "idle" } }), { status: 200 }),
    );
    await readPipelineStatus();
    expect(fetchMock).toHaveBeenCalledWith("/pipeline/status", expect.objectContaining({ method: "GET", credentials: "same-origin" }));
    expect(fetchMock).not.toHaveBeenCalledWith("/pipeline/run", expect.anything());
  });
});
