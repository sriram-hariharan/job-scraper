import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { SchedulerHealthDashboard } from "./SchedulerHealthDashboard";
import {
  formatDateTime,
  formatExpectedRunDateTime,
  runAgentDiscoveryNow,
  type SchedulerSummaryPayload,
} from "./schedulerModel";

const READY_PAYLOAD: SchedulerSummaryPayload = {
  ok: true,
  limit: 25,
  contract_health: {
    ok: true,
    checks: { seed_sql_matches_artifact: true, init_sql_matches_artifact: true },
    all_checks_pass: true,
  },
  history: {
    jsonl_path: "outputs/scheduler_history.jsonl",
    jsonl_row_count: 3,
    postgres_row_count: 3,
    count_matches: true,
  },
  latest_runs_by_job: [
    {
      run_id: "run-live-1",
      job_name: "live_pipeline",
      status: "succeeded",
      return_code: 0,
      started_at: "2026-07-20T01:00:00Z",
      finished_at: "2026-07-20T01:05:00Z",
      trigger_source: "external_scheduler_wrapper",
    },
    {
      run_id: "run-report-1",
      job_name: "scheduler_report",
      status: "failed",
      return_code: 1,
      started_at: "2026-07-19T23:00:00Z",
      finished_at: "2026-07-19T23:01:00Z",
      trigger_source: "manual_admin",
    },
  ],
  recent_postgres_runs: [
    {
      run_id: "run-live-1",
      job_name: "live_pipeline",
      status: "succeeded",
      return_code: 0,
      started_at: "2026-07-20T01:00:00Z",
      finished_at: "2026-07-20T01:05:00Z",
      trigger_source: "external_scheduler_wrapper",
    },
    {
      run_id: "run-report-1",
      job_name: "scheduler_report",
      status: "failed",
      return_code: 1,
      started_at: "2026-07-19T23:00:00Z",
      finished_at: "2026-07-19T23:01:00Z",
      trigger_source: "manual_admin",
    },
  ],
  recent_jsonl_runs: [
    {
      run_id: "run-live-1",
      job_name: "live_pipeline",
      status: "succeeded",
      return_code: 0,
      started_at: "2026-07-20T01:00:00Z",
      finished_at: "2026-07-20T01:05:00Z",
    },
  ],
  runtime_jobs: [
    {
      job_name: "agent_discovery",
      description: "Run standalone company discovery agent.",
      cadence_seconds: 86400,
      installed: true,
      loaded: true,
      enabled: true,
      armed: true,
      running: false,
      runtime_state: "idle",
      expected_next_run_at: null,
      manual_run_active: false,
      manual_run_started_at: null,
      last_run: {
        run_id: "run-agent-1",
        job_name: "agent_discovery",
        status: "succeeded",
        return_code: 0,
        started_at: "2026-07-20T00:00:00Z",
        finished_at: "2026-07-20T00:05:00Z",
      },
    },
    {
      job_name: "live_pipeline",
      description: "Run main pipeline and optionally downstream application planning.",
      cadence_seconds: 21600,
      installed: true,
      loaded: true,
      enabled: true,
      armed: true,
      running: true,
      runtime_state: "running",
      expected_next_run_at: "2026-07-20T07:00:00Z",
      manual_run_active: false,
      manual_run_started_at: null,
      last_run: {
        run_id: "run-live-1",
        job_name: "live_pipeline",
        status: "succeeded",
        return_code: 0,
        started_at: "2026-07-20T01:00:00Z",
        finished_at: "2026-07-20T01:05:00Z",
      },
    },
  ],
  postgres_summary: {
    job_definition_count: 2,
    active_job_count: 2,
    run_history_count: 2,
    success_count: 1,
    failure_count: 1,
  },
  postgres_command_text: "SELECT 1",
};

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("SchedulerHealthDashboard", () => {
  it("POSTs only the narrow manual Agent Discovery endpoint", async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      status: 202,
      json: async () => ({
        ok: true,
        accepted: true,
        job_name: "agent_discovery",
        trigger_source: "manual_admin",
      }),
    }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(runAgentDiscoveryNow()).resolves.toMatchObject({ accepted: true });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledWith(
      "/scheduler/jobs/agent_discovery/run-now",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("renders a loading state without a fake healthy default", () => {
    const neverResolves = () => new Promise<never>(() => undefined);
    render(<SchedulerHealthDashboard readSummary={neverResolves} />);
    expect(screen.getByText("Checking...")).toBeInTheDocument();
    expect(screen.queryByText("Healthy")).not.toBeInTheDocument();
  });

  it("renders the overview panel, Job Status table, and admin badge once loaded", async () => {
    render(<SchedulerHealthDashboard readSummary={async () => READY_PAYLOAD} />);
    expect(await screen.findByText("Healthy")).toBeInTheDocument();
    expect(screen.getByText("Admin only")).toBeInTheDocument();
    expect(screen.getAllByText("live_pipeline").length).toBeGreaterThan(0);
    const activeJobsMetric = screen.getByText("Active jobs").closest(".scheduler-overview-metric");
    expect(activeJobsMetric).not.toBeNull();
    expect(within(activeJobsMetric as HTMLElement).getByText("2")).toBeInTheDocument();
  });

  it("renders exactly two truthful runtime cards with definition-owned cadences", async () => {
    const { container } = render(<SchedulerHealthDashboard readSummary={async () => READY_PAYLOAD} />);
    await screen.findByText("Healthy");
    const cards = container.querySelectorAll(".scheduler-runtime-card");
    expect(cards).toHaveLength(2);

    const discovery = container.querySelector('[data-job-name="agent_discovery"]') as HTMLElement;
    const live = container.querySelector('[data-job-name="live_pipeline"]') as HTMLElement;
    expect(within(discovery).getByText("Every 24 hours")).toBeInTheDocument();
    expect(within(discovery).getByText("Idle")).toBeInTheDocument();
    expect(within(discovery).getByText("Armed")).toBeInTheDocument();
    expect(within(live).getByText("Every 6 hours")).toBeInTheDocument();
    expect(within(live).getByText("Running")).toBeInTheDocument();
    const lastRun = within(live).getByText(formatDateTime("2026-07-20T01:00:00Z"));
    expect(lastRun).toBeInTheDocument();
    expect(lastRun).toHaveAttribute("title", formatDateTime("2026-07-20T01:00:00Z"));
    expect(within(live).getByText("0")).toBeInTheDocument();
  });

  it("renders a healthy future projection with a visible local date and time", async () => {
    vi.spyOn(Date, "now").mockReturnValue(new Date("2026-08-16T06:00:00Z").getTime());
    const expectedAt = "2026-08-16T07:54:00Z";
    const payload: SchedulerSummaryPayload = {
      ...READY_PAYLOAD,
      runtime_jobs: READY_PAYLOAD.runtime_jobs?.map((job) => (
        job.job_name === "agent_discovery"
          ? {
              ...job,
              expected_next_run_at: expectedAt,
              last_run: {
                ...job.last_run,
                started_at: "2026-08-16T05:00:00Z",
                trigger_source: "manual_admin",
              },
            }
          : job
      )),
    };

    const { container } = render(<SchedulerHealthDashboard readSummary={async () => payload} />);
    await screen.findByText("Healthy");
    const discovery = container.querySelector('[data-job-name="agent_discovery"]') as HTMLElement;
    const pill = within(discovery).getByText(
      `EXPECTED NEXT · ${formatExpectedRunDateTime(expectedAt)}`,
    );
    expect(pill).toHaveClass("is-scheduled");
    expect(pill).toHaveTextContent("2026");
    expect(pill).toHaveTextContent(/\d{1,2}:\d{2}/);
  });

  it("shows RUNNING NOW instead of an expected timestamp for a running job", async () => {
    const { container } = render(<SchedulerHealthDashboard readSummary={async () => READY_PAYLOAD} />);
    await screen.findByText("Healthy");
    const live = container.querySelector('[data-job-name="live_pipeline"]') as HTMLElement;
    expect(within(live).getByText("RUNNING NOW")).toHaveClass("is-running");
    expect(within(live).queryByText(/EXPECTED NEXT/)).not.toBeInTheDocument();
  });

  it("shows the scheduled first-run wording when a healthy job has no scheduled anchor", async () => {
    const payload: SchedulerSummaryPayload = {
      ...READY_PAYLOAD,
      runtime_jobs: READY_PAYLOAD.runtime_jobs?.map((job) => (
        job.job_name === "agent_discovery"
          ? { ...job, last_run: null, expected_next_run_at: null }
          : job
      )),
    };
    const { container } = render(<SchedulerHealthDashboard readSummary={async () => payload} />);
    await screen.findByText("Healthy");
    const discovery = container.querySelector('[data-job-name="agent_discovery"]') as HTMLElement;
    const pill = within(discovery).getByText("SCHEDULED · AWAITING FIRST RUN");
    expect(pill).toHaveClass("is-awaiting");
    expect(pill).toHaveAttribute("title", "No scheduled run has been recorded yet.");
  });

  it("offers one Agent Discovery action and requires explicit confirmation", async () => {
    const runDiscoveryNow = vi.fn(async () => ({
      ok: true as const,
      accepted: true as const,
      job_name: "agent_discovery" as const,
      trigger_source: "manual_admin" as const,
    }));
    const { container } = render(
      <SchedulerHealthDashboard
        readSummary={async () => READY_PAYLOAD}
        runDiscoveryNow={runDiscoveryNow}
      />,
    );
    await screen.findByText("Healthy");
    const discovery = container.querySelector('[data-job-name="agent_discovery"]') as HTMLElement;
    const live = container.querySelector('[data-job-name="live_pipeline"]') as HTMLElement;
    const trigger = within(discovery).getByRole("button", { name: "Run discovery now" });
    expect(screen.getAllByRole("button", { name: "Run discovery now" })).toHaveLength(1);
    expect(trigger).toHaveClass("scheduler-manual-discovery-btn");
    expect(trigger.closest(".scheduler-runtime-card-title-row")).not.toBeNull();
    expect(discovery.querySelector(".scheduler-runtime-card-footer button")).toBeNull();
    expect(within(live).queryByRole("button", { name: /discovery/i })).not.toBeInTheDocument();

    fireEvent.click(trigger);
    expect(runDiscoveryNow).not.toHaveBeenCalled();
    const dialog = screen.getByRole("dialog", { name: "Run discovery now?" });
    expect(dialog).toHaveAttribute("aria-modal", "true");
    expect(within(dialog).getByText(/does not change the existing 24-hour schedule/i)).toBeInTheDocument();

    fireEvent.click(within(dialog).getByRole("button", { name: "Cancel" }));
    expect(runDiscoveryNow).not.toHaveBeenCalled();
    await waitFor(() => expect(trigger).toHaveFocus());
  });

  it("confirms the manual endpoint action and composes an effective running state", async () => {
    const runDiscoveryNow = vi.fn(async () => ({
      ok: true as const,
      accepted: true as const,
      job_name: "agent_discovery" as const,
      trigger_source: "manual_admin" as const,
    }));
    const { container } = render(
      <SchedulerHealthDashboard
        readSummary={async () => READY_PAYLOAD}
        runDiscoveryNow={runDiscoveryNow}
      />,
    );
    await screen.findByText("Healthy");
    const discovery = container.querySelector('[data-job-name="agent_discovery"]') as HTMLElement;
    fireEvent.click(within(discovery).getByRole("button", { name: "Run discovery now" }));
    fireEvent.click(screen.getByRole("button", { name: "Run discovery" }));

    await waitFor(() => expect(runDiscoveryNow).toHaveBeenCalledTimes(1));
    expect(await within(discovery).findByRole("button", { name: "Discovery running…" })).toBeDisabled();
    expect(within(discovery).getByText("Running")).toBeInTheDocument();
    expect(within(discovery).getByText("RUNNING NOW")).toHaveClass("is-running");
    expect(within(discovery).queryByText("Idle")).not.toBeInTheDocument();
  });

  it("renders backend-reconciled manual activity as running without changing launchd truth", async () => {
    const payload: SchedulerSummaryPayload = {
      ...READY_PAYLOAD,
      runtime_jobs: READY_PAYLOAD.runtime_jobs?.map((job) => (
        job.job_name === "agent_discovery"
          ? { ...job, manual_run_active: true, manual_run_started_at: "2026-08-16T08:00:00Z" }
          : job
      )),
    };
    const { container } = render(<SchedulerHealthDashboard readSummary={async () => payload} />);
    await screen.findByText("Healthy");
    const discovery = container.querySelector('[data-job-name="agent_discovery"]') as HTMLElement;
    expect(within(discovery).getByText("Running")).toBeInTheDocument();
    expect(within(discovery).getByText("RUNNING NOW")).toBeInTheDocument();
    expect(within(discovery).getByRole("button", { name: "Discovery running…" })).toBeDisabled();
  });

  it.each([
    { loaded: false, armed: false, runtime_state: "unloaded" as const },
    { enabled: false, armed: false, runtime_state: "idle" as const },
    { running: true, runtime_state: "running" as const },
  ])("disables manual discovery when launchd is unhealthy or active", async (override) => {
    const payload: SchedulerSummaryPayload = {
      ...READY_PAYLOAD,
      runtime_jobs: READY_PAYLOAD.runtime_jobs?.map((job) => (
        job.job_name === "agent_discovery" ? { ...job, ...override } : job
      )),
    };
    const { container } = render(<SchedulerHealthDashboard readSummary={async () => payload} />);
    await screen.findByText(override.runtime_state === "running" ? "Healthy" : "Attention");
    const discovery = container.querySelector('[data-job-name="agent_discovery"]') as HTMLElement;
    expect(within(discovery).getByRole("button", { name: "Run discovery now" })).toBeDisabled();
  });

  it("closes manual confirmation with Escape and restores trigger focus", async () => {
    const { container } = render(<SchedulerHealthDashboard readSummary={async () => READY_PAYLOAD} />);
    await screen.findByText("Healthy");
    const discovery = container.querySelector('[data-job-name="agent_discovery"]') as HTMLElement;
    const trigger = within(discovery).getByRole("button", { name: "Run discovery now" });
    fireEvent.click(trigger);
    expect(screen.getByRole("dialog", { name: "Run discovery now?" })).toBeInTheDocument();
    fireEvent.keyDown(document, { key: "Escape" });
    await waitFor(() => expect(screen.queryByRole("dialog", { name: "Run discovery now?" })).not.toBeInTheDocument());
    expect(trigger).toHaveFocus();
  });

  it.each([
    { installed: false, runtime_state: "not_installed" as const },
    { loaded: false, runtime_state: "unloaded" as const },
    { enabled: false, armed: false, runtime_state: "idle" as const },
    { armed: false, runtime_state: "idle" as const },
  ])("shows NEXT RUN UNAVAILABLE for a non-executable runtime state", async (override) => {
    const payload: SchedulerSummaryPayload = {
      ...READY_PAYLOAD,
      runtime_jobs: READY_PAYLOAD.runtime_jobs?.map((job) => (
        job.job_name === "agent_discovery" ? { ...job, ...override } : job
      )),
    };
    const { container } = render(<SchedulerHealthDashboard readSummary={async () => payload} />);
    await screen.findByText("Attention");
    const discovery = container.querySelector('[data-job-name="agent_discovery"]') as HTMLElement;
    expect(within(discovery).getByText("NEXT RUN UNAVAILABLE")).toHaveClass("is-unavailable");
  });

  it("shows SCHEDULE UNKNOWN when runtime inspection is unavailable", async () => {
    const payload: SchedulerSummaryPayload = {
      ...READY_PAYLOAD,
      runtime_jobs: READY_PAYLOAD.runtime_jobs?.map((job) => (
        job.job_name === "agent_discovery"
          ? {
              ...job,
              installed: null,
              loaded: null,
              enabled: null,
              armed: null,
              running: null,
              runtime_state: "unavailable",
            }
          : job
      )),
    };
    const { container } = render(<SchedulerHealthDashboard readSummary={async () => payload} />);
    await screen.findByText("Unavailable", { selector: ".scheduler-overview-primary h2" });
    const discovery = container.querySelector('[data-job-name="agent_discovery"]') as HTMLElement;
    expect(within(discovery).getByText("SCHEDULE UNKNOWN")).toHaveClass("is-unknown");
  });

  it("renders an overdue projection without changing overall scheduler health", async () => {
    vi.spyOn(Date, "now").mockReturnValue(new Date("2026-08-16T08:00:00Z").getTime());
    const expectedAt = "2026-08-16T07:54:00Z";
    const payload: SchedulerSummaryPayload = {
      ...READY_PAYLOAD,
      runtime_jobs: READY_PAYLOAD.runtime_jobs?.map((job) => (
        job.job_name === "agent_discovery"
          ? { ...job, expected_next_run_at: expectedAt }
          : job
      )),
    };

    const { container } = render(<SchedulerHealthDashboard readSummary={async () => payload} />);
    expect(await screen.findByText("Healthy")).toBeInTheDocument();
    const discovery = container.querySelector('[data-job-name="agent_discovery"]') as HTMLElement;
    const pill = within(discovery).getByText(
      `EXPECTED RUN OVERDUE · ${formatExpectedRunDateTime(expectedAt)}`,
    );
    expect(pill).toHaveClass("is-overdue");
    expect(pill).toHaveTextContent("2026");
    expect(pill).toHaveTextContent(/\d{1,2}:\d{2}/);
    for (const forbidden of ["Run now", "Stop", "Retry", "Enable", "Disable"]) {
      expect(screen.queryByRole("button", { name: forbidden })).not.toBeInTheDocument();
    }
  });

  it("renders disabled and unloaded runtime as attention", async () => {
    const attentionPayload: SchedulerSummaryPayload = {
      ...READY_PAYLOAD,
      runtime_jobs: READY_PAYLOAD.runtime_jobs?.map((job) => (
        job.job_name === "live_pipeline"
          ? { ...job, loaded: false, enabled: false, armed: false, running: false, runtime_state: "unloaded" }
          : job
      )),
    };
    const { container } = render(<SchedulerHealthDashboard readSummary={async () => attentionPayload} />);
    expect(await screen.findByText("Attention")).toBeInTheDocument();
    const live = container.querySelector('[data-job-name="live_pipeline"]') as HTMLElement;
    expect(live).toHaveClass("is-attention");
    expect(within(live).getAllByText("Unloaded")).toHaveLength(2);
    expect(within(live).getByText("Disabled")).toBeInTheDocument();
  });

  it("does not fabricate Healthy when launchd runtime is unavailable", async () => {
    const unavailablePayload: SchedulerSummaryPayload = {
      ...READY_PAYLOAD,
      runtime_jobs: READY_PAYLOAD.runtime_jobs?.map((job) => ({
        ...job,
        loaded: null,
        enabled: null,
        armed: null,
        running: null,
        runtime_state: "unavailable",
      })),
    };
    render(<SchedulerHealthDashboard readSummary={async () => unavailablePayload} />);
    expect(await screen.findByText("Unavailable", { selector: ".scheduler-overview-primary h2" })).toBeInTheDocument();
    expect(screen.getByText("Launchd runtime inspection is unavailable.")).toBeInTheDocument();
    expect(screen.queryByText("Healthy")).not.toBeInTheDocument();
  });

  it("uses the shared app-page-header contract while keeping the Admin only badge and last-refreshed text", async () => {
    const { container } = render(<SchedulerHealthDashboard readSummary={async () => READY_PAYLOAD} />);
    await screen.findByText("Healthy");
    const header = container.querySelector("header.scheduler-health-header") as HTMLElement;
    expect(header).not.toBeNull();
    expect(header).toHaveClass("scheduler-health-header");
    expect(header).toHaveClass("app-page-header");
    expect(within(header).getByRole("heading", { level: 1 })).toHaveClass("app-page-header__title");
    expect(within(header).getByRole("heading", { level: 1 })).toHaveTextContent("Scheduler Health");
    expect(within(header).getByText("Admin only")).toHaveClass("app-page-header__badge");
    expect(
      within(header).getByText(
        "Monitor scheduled jobs, run outcomes, persistence consistency, and configuration integrity.",
      ),
    ).toHaveClass("app-page-header__description");
    expect(within(header).getByText(/Last refreshed at/)).toBeInTheDocument();
    expect(within(header).getByRole("button", { name: /Refresh/ })).toBeInTheDocument();
  });

  it("shows a Recorded runs metric backed by postgres_summary.run_history_count, and no Storage sync metric", async () => {
    render(<SchedulerHealthDashboard readSummary={async () => READY_PAYLOAD} />);
    await screen.findByText("Healthy");
    const recordedRunsMetric = screen.getByText("Recorded runs").closest(".scheduler-overview-metric");
    expect(recordedRunsMetric).not.toBeNull();
    expect(within(recordedRunsMetric as HTMLElement).getByText("2")).toBeInTheDocument();
    expect(screen.queryByText("Storage sync")).not.toBeInTheDocument();
  });

  it("does not render a fake healthy state when contract checks fail", async () => {
    const mismatched: SchedulerSummaryPayload = {
      ...READY_PAYLOAD,
      contract_health: { ...READY_PAYLOAD.contract_health, all_checks_pass: false },
    };
    render(<SchedulerHealthDashboard readSummary={async () => mismatched} />);
    expect(await screen.findByText("Attention")).toBeInTheDocument();
    expect(screen.getByText("Needs attention: configuration integrity.")).toBeInTheDocument();
  });

  it("stays healthy when history.count_matches is false and JSONL data is missing", async () => {
    const jsonlMissing: SchedulerSummaryPayload = {
      ...READY_PAYLOAD,
      history: { ...READY_PAYLOAD.history, count_matches: false, jsonl_row_count: 0 },
      recent_jsonl_runs: [],
    };
    render(<SchedulerHealthDashboard readSummary={async () => jsonlMissing} />);
    expect(await screen.findByText("Healthy")).toBeInTheDocument();
    expect(screen.getByText("Configuration and launchd runtime are healthy.")).toBeInTheDocument();
  });

  it("renders a real error state on fetch failure, not a silent healthy default", async () => {
    render(<SchedulerHealthDashboard readSummary={async () => { throw new Error("boom"); }} />);
    expect(await screen.findByText("boom", { selector: ".scheduler-error-banner" })).toBeInTheDocument();
    expect(screen.getByText("Unavailable")).toBeInTheDocument();
    expect(screen.queryByText("Healthy")).not.toBeInTheDocument();
  });

  it("switches between Job Status and Run History without refetching", async () => {
    const readSummary = vi.fn(async () => READY_PAYLOAD);
    render(<SchedulerHealthDashboard readSummary={readSummary} />);
    await screen.findByText("Healthy");
    expect(readSummary).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole("tab", { name: "Run History" }));
    expect(await screen.findByText("Persisted scheduler run history from Postgres.")).toBeInTheDocument();
    expect(readSummary).toHaveBeenCalledTimes(1);
  });

  it("distinguishes scheduled and manual provenance in Run History", async () => {
    render(<SchedulerHealthDashboard readSummary={async () => READY_PAYLOAD} />);
    await screen.findByText("Healthy");
    fireEvent.click(screen.getByRole("tab", { name: "Run History" }));
    const region = screen.getByRole("region", { name: "Run history table" });
    expect(within(region).getByText("Scheduled")).toHaveClass("is-scheduled");
    expect(within(region).getByText("Manual")).toHaveClass("is-manual");
    expect(within(region).getByText("Trigger")).toBeInTheDocument();
  });

  it("has exactly one refresh request owner", async () => {
    const readSummary = vi.fn(async () => READY_PAYLOAD);
    render(<SchedulerHealthDashboard readSummary={readSummary} />);
    await screen.findByText("Healthy");
    fireEvent.click(screen.getByRole("button", { name: "Refresh scheduler health" }));
    await waitFor(() => expect(readSummary).toHaveBeenCalledTimes(2));
  });

  it("orders Job Status with failed jobs first, then latest", async () => {
    render(<SchedulerHealthDashboard readSummary={async () => READY_PAYLOAD} />);
    await screen.findByText("Healthy");
    const region = screen.getByRole("region", { name: "Job status table" });
    const table = within(region).getByRole("table");
    const rows = within(table).getAllByRole("row").slice(1); // drop header row
    expect(within(rows[0]).getByText("scheduler_report")).toBeInTheDocument();
    expect(within(rows[1]).getByText("live_pipeline")).toBeInTheDocument();
  });

  it("exposes the complete Run ID on hover in the Job Status table", async () => {
    render(<SchedulerHealthDashboard readSummary={async () => READY_PAYLOAD} />);
    await screen.findByText("Healthy");
    const region = screen.getByRole("region", { name: "Job status table" });
    const runId = within(region).getByText("run-live-1");
    expect(runId).toHaveAttribute("title", "run-live-1");
  });

  it("does not permanently render the diagnostics content in the page flow", async () => {
    render(<SchedulerHealthDashboard readSummary={async () => READY_PAYLOAD} />);
    await screen.findByText("Healthy");
    expect(screen.queryByText("Seed SQL artifact match")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "View diagnostics" }));
    const dialog = await screen.findByRole("dialog");
    fireEvent.click(within(dialog).getByRole("tab", { name: "Configuration Integrity" }));
    expect(await screen.findByText("Seed SQL artifact match")).toBeInTheDocument();
  });

  it("opens and closes the diagnostics modal accessibly, restoring focus to the trigger", async () => {
    render(<SchedulerHealthDashboard readSummary={async () => READY_PAYLOAD} />);
    await screen.findByText("Healthy");
    const trigger = screen.getByRole("button", { name: "View diagnostics" });
    fireEvent.click(trigger);

    const dialog = await screen.findByRole("dialog", { name: "Scheduler diagnostics" });
    expect(dialog).toHaveAttribute("aria-modal", "true");

    fireEvent.keyDown(document, { key: "Escape" });
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    expect(trigger).toHaveFocus();
  });

  it("closes the diagnostics modal on backdrop click", async () => {
    render(<SchedulerHealthDashboard readSummary={async () => READY_PAYLOAD} />);
    await screen.findByText("Healthy");
    fireEvent.click(screen.getByRole("button", { name: "View diagnostics" }));
    const dialog = await screen.findByRole("dialog", { name: "Scheduler diagnostics" });
    fireEvent.click(dialog.parentElement as HTMLElement);
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
  });

  it("renders configuration checks as status rows rather than a legacy table", async () => {
    render(<SchedulerHealthDashboard readSummary={async () => READY_PAYLOAD} />);
    await screen.findByText("Healthy");
    fireEvent.click(screen.getByRole("button", { name: "View diagnostics" }));
    const dialog = await screen.findByRole("dialog");
    fireEvent.click(within(dialog).getByRole("tab", { name: "Configuration Integrity" }));
    expect(screen.getByText("Overall configuration integrity")).toBeInTheDocument();
    expect(screen.getByText("Seed SQL artifact match")).toBeInTheDocument();
    expect(screen.getByText("Init SQL artifact match")).toBeInTheDocument();
    expect(screen.queryByRole("table", { name: /configuration/i })).not.toBeInTheDocument();
  });

  it("makes Configuration Integrity and Database History reachable, with no File Audit tab", async () => {
    render(<SchedulerHealthDashboard readSummary={async () => READY_PAYLOAD} />);
    await screen.findByText("Healthy");
    fireEvent.click(screen.getByRole("button", { name: "View diagnostics" }));
    const dialog = await screen.findByRole("dialog");

    expect(within(dialog).queryByRole("tab", { name: "File Audit" })).not.toBeInTheDocument();
    expect(within(dialog).getByRole("tab", { name: "Runtime" })).toBeInTheDocument();
    expect(within(dialog).getByRole("tab", { name: "Configuration Integrity" })).toBeInTheDocument();

    fireEvent.click(within(dialog).getByRole("tab", { name: "Database History" }));
    expect(screen.getByText(/mirrored into Postgres/)).toBeInTheDocument();
  });

  it("shows bounded runtime details in diagnostics", async () => {
    render(<SchedulerHealthDashboard readSummary={async () => READY_PAYLOAD} />);
    await screen.findByText("Healthy");
    fireEvent.click(screen.getByRole("button", { name: "View diagnostics" }));
    const dialog = await screen.findByRole("dialog");
    expect(within(dialog).getAllByText("Agent Discovery")).toHaveLength(1);
    expect(within(dialog).getAllByText("Live Pipeline")).toHaveLength(1);
    expect(within(dialog).getByText("Every 24 hours")).toBeInTheDocument();
    expect(within(dialog).getByText("Every 6 hours")).toBeInTheDocument();
    expect(within(dialog).getAllByText("Yes").length).toBeGreaterThan(0);
  });

  it("does not introduce a scheduler write/control action", async () => {
    render(<SchedulerHealthDashboard readSummary={async () => READY_PAYLOAD} />);
    await screen.findByText("Healthy");
    for (const forbidden of [
      "Run job", "Run now", "Stop job", "Stop", "Restart", "Trigger run",
      "Disable job", "Enable job", "Install", "Uninstall",
    ]) {
      expect(screen.queryByRole("button", { name: forbidden })).not.toBeInTheDocument();
    }
  });

  it("keeps the scheduler Refresh action inside the scheduler page header, not duplicated", async () => {
    render(<SchedulerHealthDashboard readSummary={async () => READY_PAYLOAD} />);
    await screen.findByText("Healthy");
    const refreshButtons = screen.getAllByRole("button", { name: "Refresh scheduler health" });
    expect(refreshButtons).toHaveLength(1);
    expect(refreshButtons[0].closest("header.scheduler-health-header")).not.toBeNull();
  });

  it("shows Run History filters only on the Run History view", async () => {
    render(<SchedulerHealthDashboard readSummary={async () => READY_PAYLOAD} />);
    await screen.findByText("Healthy");

    // Job Status is the default view; its filters must not be present.
    expect(screen.queryByText("All jobs")).not.toBeInTheDocument();
    expect(screen.queryByText("All statuses")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: "Run History" }));
    expect(await screen.findByText("All jobs")).toBeInTheDocument();
    expect(screen.getByText("All statuses")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: "Job Status" }));
    expect(screen.queryByText("All jobs")).not.toBeInTheDocument();
    expect(screen.queryByText("All statuses")).not.toBeInTheDocument();
  });

  it("does not assign arbitrary job-based row color classes, only semantic failed-state styling", async () => {
    render(<SchedulerHealthDashboard readSummary={async () => READY_PAYLOAD} />);
    await screen.findByText("Healthy");

    const region = screen.getByRole("region", { name: "Job status table" });
    const table = within(region).getByRole("table");
    const rows = within(table).getAllByRole("row").slice(1);

    // scheduler_report is failed -> "is-attention"; live_pipeline is succeeded -> no attention class.
    const failedRow = rows.find((row) => within(row).queryByText("scheduler_report"));
    const succeededRow = rows.find((row) => within(row).queryByText("live_pipeline"));
    expect(failedRow?.className).toContain("is-attention");
    expect(succeededRow?.className).not.toContain("is-attention");

    // Both rows otherwise share the identical base class (no per-job/company variant classes).
    const baseClass = (className: string) => className.replace(/\s*is-attention\s*/, " ").trim();
    expect(baseClass(failedRow?.className || "")).toBe(baseClass(succeededRow?.className || ""));
  });

  it("keeps the Run ID accessible via a title attribute when visually truncated in diagnostics", async () => {
    render(<SchedulerHealthDashboard readSummary={async () => READY_PAYLOAD} />);
    await screen.findByText("Healthy");
    fireEvent.click(screen.getByRole("button", { name: "View diagnostics" }));
    const dialog = await screen.findByRole("dialog");
    fireEvent.click(within(dialog).getByRole("tab", { name: "Database History" }));

    const runIdCell = within(dialog).getByText("run-live-1");
    expect(runIdCell).toHaveAttribute("title", "run-live-1");
  });
});
