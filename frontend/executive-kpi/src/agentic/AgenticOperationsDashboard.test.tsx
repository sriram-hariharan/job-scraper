import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AgenticOperationsDashboard } from "./AgenticOperationsDashboard";
import {
  readAgenticOperationsOverview,
  type AgenticOperationsOverviewPayload,
} from "./agenticOperationsModel";

const SAFETY_METADATA = {
  read_only: true,
  admin_only: true,
  cross_user_access: false,
  database_write_performed: false,
  schema_write_performed: false,
  provider_call_performed: false,
  pipeline_execution_performed: false,
  scheduler_mutation_performed: false,
  scoring_changed: false,
  ranking_changed: false,
  queue_mutation_performed: false,
  resume_mutation_performed: false,
  application_execution_performed: false,
  ats_submission_performed: false,
};

const READY_PAYLOAD: AgenticOperationsOverviewPayload = {
  ok: true,
  read_only: true,
  admin_only: true,
  owner_user_id: "admin-owner",
  current_pipeline: {
    available: true,
    state: "available",
    run_id: "run-current-61e",
    status: "running",
    current_stage: "ai_evaluation",
    stage_message: "Evaluating owner-scoped jobs",
    completed_stages: ["startup", "scraping"],
    stage_order: ["startup", "scraping", "ai_evaluation", "finalize"],
    stage_started_at: "2026-08-22T12:00:00Z",
    updated_at_utc: "2026-08-22T12:01:00Z",
    final_job_count: 12,
    return_code: null,
  },
  recent_runs: [
    {
      run_id: "run-recent-1",
      status: "succeeded",
      current_stage: "complete",
      summary_message: "Pipeline completed",
      completed_at: "2026-08-22T11:30:00Z",
      final_job_count: 9,
    },
    {
      run_id: "run-recent-2",
      status: "failed",
      current_stage: "ai_evaluation",
      stage_message: "Evaluation stopped",
      updated_at: "2026-08-22T10:30:00Z",
      final_job_count: null,
    },
  ],
  recent_runs_state: { available: true, state: "available", count: 2, bound: 10 },
  canonical_agents: [{ key: "critic" }],
  safety_summary: {
    canonical_agent_count: 8,
    score_mutation_capable_count: 0,
    rank_mutation_capable_count: 0,
    queue_mutation_capable_count: 3,
    resume_text_mutation_capable_count: 2,
    operator_state_persistence_capable_count: 0,
    application_action_capable_count: 1,
  },
  safety_metadata: SAFETY_METADATA,
};

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  document.body.innerHTML = "";
});

function installAgenticOperationsHeader() {
  document.body.insertAdjacentHTML("afterbegin", `
    <header class="page-header app-page-header">
      <div class="app-page-header__title-row">
        <h1 class="app-page-header__title">Agentic Operations</h1>
        <span class="agentic-operations-header-badge app-page-header__badge">Admin only</span>
        <span id="agenticOperationsHeaderReadOnlyBadge" class="agentic-operations-header-badge-slot"></span>
      </div>
    </header>
  `);
  return screen.getByRole("banner");
}

describe("AgenticOperationsDashboard", () => {
  it("shows a neutral loading state without fake zero metrics", () => {
    const header = installAgenticOperationsHeader();
    const readOverview = vi.fn(() => new Promise<AgenticOperationsOverviewPayload>(() => undefined));
    render(<AgenticOperationsDashboard readOverview={readOverview} />);

    expect(screen.getByText("Loading operations overview…")).toBeInTheDocument();
    expect(screen.queryByText("0")).not.toBeInTheDocument();
    expect(within(header).getByText("Admin only")).toBeInTheDocument();
    expect(within(header).queryByText("Read-only")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Refresh overview" })).toBeDisabled();
  });

  it("renders the approved overview projection and payload-derived nonzero safety values", async () => {
    const readOverview = vi.fn(async () => READY_PAYLOAD);
    render(<AgenticOperationsDashboard readOverview={readOverview} />);

    expect((await screen.findAllByText("Running")).length).toBeGreaterThan(0);
    expect(screen.getAllByText("AI Evaluation").length).toBeGreaterThan(0);
    expect(screen.getByText("run-current-61e")).toBeInTheDocument();
    expect(screen.getByText("run-recent-1")).toBeInTheDocument();
    expect(screen.getByText("run-recent-2")).toBeInTheDocument();
    expect(screen.getAllByText("8").length).toBeGreaterThan(0);
    const safety = screen.getByRole("region", { name: "Safety overview" });
    expect(within(safety).getByText("Queue mutation capable").nextSibling).toHaveTextContent("3");
    expect(within(safety).getByText("Resume mutation capable").nextSibling).toHaveTextContent("2");
    expect(within(safety).getByText("Application-action capable").nextSibling).toHaveTextContent("1");
    expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/owner/i)).not.toBeInTheDocument();
  });

  it("keeps the title dominant and renders the ordered header badges without another request", async () => {
    const header = installAgenticOperationsHeader();
    const readOverview = vi.fn(async () => READY_PAYLOAD);
    render(<AgenticOperationsDashboard readOverview={readOverview} />);

    expect(within(header).getByRole("heading", { level: 1 })).toHaveTextContent("Agentic Operations");
    expect(within(header).getAllByText("Admin only")).toHaveLength(1);
    expect(await within(header).findByText("Read-only")).toBeInTheDocument();
    const badges = Array.from(header.querySelectorAll(".app-page-header__badge"));
    expect(badges.map((badge) => badge.textContent)).toEqual(["Admin only", "Read-only"]);
    expect(screen.getAllByText("Read-only")).toHaveLength(1);
    expect(readOverview).toHaveBeenCalledTimes(1);
    expect(screen.getAllByRole("button")).toHaveLength(1);
    expect(screen.getByRole("button", { name: "Refresh overview" })).toBeInTheDocument();
  });

  it.each(["not_found", "not_configured", "malformed", "unavailable"])(
    "preserves the truthful %s current-pipeline state",
    async (state) => {
      const readOverview = vi.fn(async () => ({
        ...READY_PAYLOAD,
        current_pipeline: { available: false, state },
      }));
      render(<AgenticOperationsDashboard readOverview={readOverview} />);

      const current = await screen.findByRole("region", { name: "Current pipeline" });
      expect(within(current).getAllByText(state.replace(/_/g, " "), { exact: false }).length).toBeGreaterThan(0);
      expect(within(current).queryByText("Healthy")).not.toBeInTheDocument();
      expect(within(current).queryByText("Idle")).not.toBeInTheDocument();
      expect(within(current).queryByText("Succeeded")).not.toBeInTheDocument();
    },
  );

  it("keeps unavailable recent-run truth distinct from an authoritative zero", async () => {
    const readOverview = vi.fn(async () => ({
      ...READY_PAYLOAD,
      recent_runs: [],
      recent_runs_state: { available: false, state: "unavailable", count: 0, bound: 10 },
    }));
    render(<AgenticOperationsDashboard readOverview={readOverview} />);

    const runs = await screen.findByRole("region", { name: "Recent pipeline runs" });
    expect(within(runs).getByText("Recent runs unavailable")).toBeInTheDocument();
    expect(within(runs).queryByText("0 recorded")).not.toBeInTheDocument();
  });

  it("shows a bounded error and retries only through manual refresh", async () => {
    const readOverview = vi.fn()
      .mockRejectedValueOnce(new Error("Overview read failed"))
      .mockResolvedValueOnce(READY_PAYLOAD);
    render(<AgenticOperationsDashboard readOverview={readOverview} />);

    expect(await screen.findByRole("alert")).toHaveTextContent("Overview read failed");
    expect(readOverview).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole("button", { name: "Refresh overview" }));
    await screen.findByText("run-current-61e");
    expect(readOverview).toHaveBeenCalledTimes(2);
  });

  it("makes one initial read and exactly one non-overlapping read per manual refresh", async () => {
    let resolveRefresh!: (payload: AgenticOperationsOverviewPayload) => void;
    const readOverview = vi.fn()
      .mockResolvedValueOnce(READY_PAYLOAD)
      .mockImplementationOnce(() => new Promise<AgenticOperationsOverviewPayload>((resolve) => {
        resolveRefresh = resolve;
      }));
    render(<AgenticOperationsDashboard readOverview={readOverview} />);

    await screen.findByText("run-current-61e");
    const refresh = screen.getByRole("button", { name: "Refresh overview" });
    fireEvent.click(refresh);
    fireEvent.click(refresh);
    expect(readOverview).toHaveBeenCalledTimes(2);
    resolveRefresh(READY_PAYLOAD);
    await waitFor(() => expect(screen.getByRole("button", { name: "Refresh overview" })).toBeEnabled());
    expect(readOverview).toHaveBeenCalledTimes(2);
  });

  it("shows the read-only badge only when the complete returned safety contract supports it", async () => {
    const header = installAgenticOperationsHeader();
    const contradictoryPayload = {
      ...READY_PAYLOAD,
      read_only: false,
      safety_metadata: { ...SAFETY_METADATA, queue_mutation_performed: true },
    };
    const readOverview = vi.fn(async () => contradictoryPayload);
    render(<AgenticOperationsDashboard readOverview={readOverview} />);

    expect(await screen.findByText("Safety overview")).toBeInTheDocument();
    expect(within(header).queryByText("Read-only")).not.toBeInTheDocument();
    expect(within(header).getByText("Admin only")).toBeInTheDocument();
    expect(screen.getByText(/Safety metadata is inconsistent/)).toBeInTheDocument();
  });

  it("does not claim read-only when required safety metadata is omitted", async () => {
    const header = installAgenticOperationsHeader();
    const readOverview = vi.fn(async () => ({ ...READY_PAYLOAD, safety_metadata: undefined }));
    render(<AgenticOperationsDashboard readOverview={readOverview} />);

    expect(await screen.findByText("Safety overview")).toBeInTheDocument();
    expect(within(header).queryByText("Read-only")).not.toBeInTheDocument();
    expect(screen.getByText(/Safety metadata is unavailable/)).toBeInTheDocument();
  });
});

describe("readAgenticOperationsOverview", () => {
  it("owns the exact GET-only same-origin fetch contract without a body", async () => {
    const fetchMock = vi.fn(async (_input: RequestInfo | URL, _init?: RequestInit) => ({
      ok: true,
      status: 200,
      json: async () => READY_PAYLOAD,
    }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(readAgenticOperationsOverview()).resolves.toEqual(READY_PAYLOAD);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledWith(
      "/profile/admin/agentic-operations/overview",
      {
        method: "GET",
        credentials: "same-origin",
        headers: { Accept: "application/json" },
      },
    );
    expect(fetchMock.mock.calls[0]?.[1]).not.toHaveProperty("body");
  });

  it("throws a useful bounded read error for a non-2xx response", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => ({
      ok: false,
      status: 503,
      json: async () => ({ detail: "Overview temporarily unavailable" }),
    })));

    await expect(readAgenticOperationsOverview()).rejects.toThrow("Overview temporarily unavailable");
  });
});
