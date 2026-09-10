import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AgenticOperationsDashboard } from "./AgenticOperationsDashboard";
import {
  readAgenticOperationsOverview,
  type AgenticOperationsCanonicalAgent,
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

const CANONICAL_AGENTS: AgenticOperationsCanonicalAgent[] = [
  {
    key: "critic",
    display_name: "Critic Agent",
    responsibility: "Review evidence for unsupported claims and contradictions.",
    deterministic_core: true,
    llm_capable: true,
    optional_controlled_llm_guardrail: true,
    advisory_only: true,
    human_approval_required: false,
    score_mutation: true,
    rank_mutation: false,
    queue_mutation: true,
    resume_text_mutation: false,
    operator_state_persistence: false,
    application_action_capability: false,
  },
  {
    key: "job_prioritization",
    display_name: "Job Prioritization Agent",
    responsibility: "Recommend an advisory priority posture from existing evidence.",
    deterministic_core: true,
    llm_capable: false,
    optional_controlled_llm_guardrail: false,
    advisory_only: true,
    human_approval_required: false,
    score_mutation: false,
    rank_mutation: false,
    queue_mutation: true,
    resume_text_mutation: false,
    operator_state_persistence: false,
    application_action_capability: false,
  },
  {
    key: "tailoring_decision",
    display_name: "Tailoring Decision Agent",
    responsibility: "Recommend whether and how strongly to tailor.",
    deterministic_core: true,
    llm_capable: false,
    optional_controlled_llm_guardrail: false,
    advisory_only: true,
    human_approval_required: false,
    score_mutation: false,
    rank_mutation: false,
    queue_mutation: true,
    resume_text_mutation: true,
    operator_state_persistence: false,
    application_action_capability: false,
  },
  {
    key: "operator_review",
    display_name: "Operator Review Agent",
    responsibility: "Assign a human-review lane from existing advisory evidence.",
    deterministic_core: true,
    llm_capable: false,
    optional_controlled_llm_guardrail: false,
    advisory_only: true,
    human_approval_required: true,
    score_mutation: false,
    rank_mutation: false,
    queue_mutation: false,
    resume_text_mutation: true,
    operator_state_persistence: false,
    application_action_capability: true,
  },
];

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
  canonical_agents: CANONICAL_AGENTS,
  safety_summary: {
    canonical_agent_count: 4,
    score_mutation_capable_count: 1,
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
    expect(screen.getAllByText("4").length).toBeGreaterThan(0);
    const safety = screen.getByRole("region", { name: "Safety overview" });
    expect(within(safety).getByText("Queue mutation capable").nextSibling).toHaveTextContent("3");
    expect(within(safety).getByText("Resume mutation capable").nextSibling).toHaveTextContent("2");
    expect(within(safety).getByText("Application-action capable").nextSibling).toHaveTextContent("1");
    expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/owner/i)).not.toBeInTheDocument();
  });

  it("renders every returned canonical definition and its declared capabilities", async () => {
    const readOverview = vi.fn(async () => READY_PAYLOAD);
    render(<AgenticOperationsDashboard readOverview={readOverview} />);

    const registry = await screen.findByRole("region", { name: "Canonical Agent Registry" });
    for (const agent of CANONICAL_AGENTS) {
      expect(within(registry).getByText(agent.display_name || "")).toBeInTheDocument();
      expect(within(registry).getByText(agent.responsibility || "")).toBeInTheDocument();
    }
    expect(within(registry).getAllByText("Deterministic core")).toHaveLength(4);
    expect(within(registry).getByText("LLM capable")).toBeInTheDocument();
    expect(within(registry).getByText("Controlled LLM guardrail available")).toBeInTheDocument();
    expect(within(registry).getAllByText("Advisory only")).toHaveLength(4);
    expect(within(registry).getByText("Human approval required")).toBeInTheDocument();
    expect(within(registry).getAllByText("Human approval not required by definition")).toHaveLength(3);
    expect(readOverview).toHaveBeenCalledTimes(1);
  });

  it("renders changed registry values from payload rather than agent-name assumptions", async () => {
    const changedAgent: AgenticOperationsCanonicalAgent = {
      ...CANONICAL_AGENTS[0],
      display_name: "Payload Defined Reviewer",
      responsibility: "Responsibility supplied only by this payload.",
      deterministic_core: false,
      llm_capable: false,
      optional_controlled_llm_guardrail: false,
      advisory_only: false,
      human_approval_required: true,
      score_mutation: false,
      queue_mutation: false,
    };
    const readOverview = vi.fn(async () => ({
      ...READY_PAYLOAD,
      canonical_agents: [changedAgent],
      safety_summary: {
        canonical_agent_count: 1,
        score_mutation_capable_count: 0,
        rank_mutation_capable_count: 0,
        queue_mutation_capable_count: 0,
        resume_text_mutation_capable_count: 0,
        operator_state_persistence_capable_count: 0,
        application_action_capable_count: 0,
      },
    }));
    render(<AgenticOperationsDashboard readOverview={readOverview} />);

    const registry = await screen.findByRole("region", { name: "Canonical Agent Registry" });
    expect(within(registry).getByText("Payload Defined Reviewer")).toBeInTheDocument();
    expect(within(registry).getByText("Responsibility supplied only by this payload.")).toBeInTheDocument();
    expect(within(registry).getByText("Non-deterministic core")).toBeInTheDocument();
    expect(within(registry).getByText("Not LLM capable")).toBeInTheDocument();
    expect(within(registry).getByText("Controlled LLM guardrail not available")).toBeInTheDocument();
    expect(within(registry).getByText("Not advisory-only")).toBeInTheDocument();
    expect(within(registry).getByText("Human approval required")).toBeInTheDocument();
  });

  it("renders all six per-agent mutation columns including true authority", async () => {
    render(<AgenticOperationsDashboard readOverview={vi.fn(async () => READY_PAYLOAD)} />);

    const table = await screen.findByRole("table", { name: "Declared mutation authority by canonical agent" });
    for (const column of ["Score", "Rank", "Queue", "Resume text", "Operator state", "Application action"]) {
      expect(within(table).getByRole("columnheader", { name: column })).toBeInTheDocument();
    }
    expect(within(table).getAllByRole("row")).toHaveLength(CANONICAL_AGENTS.length + 1);
    const criticRow = within(table).getByRole("row", { name: /Critic Agent/ });
    expect(within(criticRow).getByLabelText("Score: Yes")).toBeInTheDocument();
    expect(within(criticRow).getByLabelText("Queue: Yes")).toBeInTheDocument();
    expect(within(criticRow).getByLabelText("Rank: No")).toBeInTheDocument();
    const operatorRow = within(table).getByRole("row", { name: /Operator Review Agent/ });
    expect(within(operatorRow).getByLabelText("Application action: Yes")).toBeInTheDocument();
  });

  it("does not fabricate agents when the returned registry is empty", async () => {
    const readOverview = vi.fn(async () => ({
      ...READY_PAYLOAD,
      canonical_agents: [],
      safety_summary: { ...READY_PAYLOAD.safety_summary, canonical_agent_count: 0 },
    }));
    render(<AgenticOperationsDashboard readOverview={readOverview} />);

    expect(await screen.findByText("No canonical agent definitions returned")).toBeInTheDocument();
    expect(screen.getByText("Mutation authority unavailable")).toBeInTheDocument();
    expect(screen.queryByText("Critic Agent")).not.toBeInTheDocument();
  });

  it("keeps valid rows truthful while surfacing malformed definitions and missing values", async () => {
    const incomplete = { ...CANONICAL_AGENTS[0], llm_capable: undefined };
    const readOverview = vi.fn(async () => ({
      ...READY_PAYLOAD,
      canonical_agents: [incomplete, { key: "malformed" } as AgenticOperationsCanonicalAgent],
    }));
    render(<AgenticOperationsDashboard readOverview={readOverview} />);

    expect((await screen.findAllByText("Critic Agent")).length).toBeGreaterThan(0);
    expect(screen.getByText("LLM capability unavailable")).toBeInTheDocument();
    expect(screen.getByText("1 malformed canonical definition was not rendered.")).toBeInTheDocument();
    expect(screen.getByLabelText("Score: Yes")).toBeInTheDocument();
  });

  it("warns without rewriting rows when registry totals disagree with safety summary", async () => {
    const readOverview = vi.fn(async () => ({
      ...READY_PAYLOAD,
      safety_summary: { ...READY_PAYLOAD.safety_summary, queue_mutation_capable_count: 0 },
    }));
    render(<AgenticOperationsDashboard readOverview={readOverview} />);

    expect(await screen.findByText("Registry capability totals do not match the returned safety summary.")).toBeInTheDocument();
    expect(screen.getAllByLabelText("Queue: Yes")).toHaveLength(3);
  });

  it("starts with no selected run, a neutral inspector prompt, and no review link", async () => {
    const readOverview = vi.fn(async () => READY_PAYLOAD);
    render(<AgenticOperationsDashboard readOverview={readOverview} />);

    const inspector = await screen.findByRole("region", { name: "Run Inspector" });
    expect(within(inspector).getByText("Select a recent pipeline run to inspect its recorded summary.")).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: /Inspect pipeline run/ })).toHaveLength(2);
    expect(screen.queryByRole("link", { name: "Open Agentic Review" })).not.toBeInTheDocument();
    expect(readOverview).toHaveBeenCalledTimes(1);
  });

  it("selects and changes exact recent-run rows locally without another overview read", async () => {
    const readOverview = vi.fn(async () => READY_PAYLOAD);
    render(<AgenticOperationsDashboard readOverview={readOverview} />);

    fireEvent.click(await screen.findByRole("button", { name: "Inspect pipeline run run-recent-1" }));
    const firstSelection = screen.getByRole("button", { name: "Selected pipeline run run-recent-1" });
    expect(firstSelection).toHaveAttribute("aria-pressed", "true");
    expect(firstSelection.closest(".agentic-operations-run-row")).toHaveClass("is-selected");
    let inspector = screen.getByRole("region", { name: "Run Inspector" });
    expect(within(inspector).getByText("run-recent-1")).toBeInTheDocument();
    expect(within(inspector).getByText("Pipeline completed")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Inspect pipeline run run-recent-2" }));
    inspector = screen.getByRole("region", { name: "Run Inspector" });
    expect(within(inspector).getByText("run-recent-2")).toBeInTheDocument();
    expect(within(inspector).getByText("Evaluation stopped")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Inspect pipeline run run-recent-1" })).toHaveAttribute("aria-pressed", "false");
    expect(readOverview).toHaveBeenCalledTimes(1);
  });

  it("keeps missing-ID metadata visible without selection or deep-link actions", async () => {
    const payload = {
      ...READY_PAYLOAD,
      recent_runs: [{ status: "failed", current_stage: "finalize", stage_message: "Missing identifier row" }],
      recent_runs_state: { available: true, state: "available", count: 1, bound: 10 },
    };
    render(<AgenticOperationsDashboard readOverview={vi.fn(async () => payload)} />);

    const runs = await screen.findByRole("region", { name: "Recent pipeline runs" });
    expect(within(runs).getByText("Run ID unavailable")).toBeInTheDocument();
    expect(within(runs).getByText("Missing identifier row")).toBeInTheDocument();
    expect(within(runs).getByText("Inspection unavailable")).toBeInTheDocument();
    expect(within(runs).queryByRole("button", { name: /inspect/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Open Agentic Review" })).not.toBeInTheDocument();
  });

  it("encodes the selected run ID and adds only the finite Agentic Operations source context", async () => {
    const payload = {
      ...READY_PAYLOAD,
      recent_runs: [{ ...READY_PAYLOAD.recent_runs?.[0], run_id: "run/review abc" }],
      recent_runs_state: { available: true, state: "available", count: 1, bound: 10 },
    };
    const readOverview = vi.fn(async () => payload);
    render(<AgenticOperationsDashboard readOverview={readOverview} />);

    fireEvent.click(await screen.findByRole("button", { name: "Inspect pipeline run run/review abc" }));
    const link = screen.getByRole("link", { name: "Open Agentic Review" });
    expect(link).toHaveAttribute(
      "href",
      "/profile/pipeline-runs/run%2Freview%20abc/agentic-review?source=agentic-operations",
    );
    expect(link.getAttribute("href")).not.toContain("owner");
    expect(link.getAttribute("href")).not.toContain("return");
    expect(readOverview).toHaveBeenCalledTimes(1);
  });

  it("preserves a selected run across refresh and clears it when a later payload removes it", async () => {
    const readOverview = vi.fn()
      .mockResolvedValueOnce(READY_PAYLOAD)
      .mockResolvedValueOnce({
        ...READY_PAYLOAD,
        recent_runs: READY_PAYLOAD.recent_runs?.map((run) => ({
          ...run,
          stage_message: run.run_id === "run-recent-1" ? "Refreshed selected run" : run.stage_message,
        })),
      })
      .mockResolvedValueOnce({ ...READY_PAYLOAD, recent_runs: [READY_PAYLOAD.recent_runs?.[1] || {}], recent_runs_state: { available: true, state: "available", count: 1, bound: 10 } });
    render(<AgenticOperationsDashboard readOverview={readOverview} />);

    fireEvent.click(await screen.findByRole("button", { name: "Inspect pipeline run run-recent-1" }));
    fireEvent.click(screen.getByRole("button", { name: "Refresh overview" }));
    expect((await screen.findAllByText("Refreshed selected run")).length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "Selected pipeline run run-recent-1" })).toHaveAttribute("aria-pressed", "true");

    fireEvent.click(screen.getByRole("button", { name: "Refresh overview" }));
    await waitFor(() => expect(screen.queryByText("run-recent-1")).not.toBeInTheDocument());
    expect(screen.getByText("Select a recent pipeline run to inspect its recorded summary.")).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Open Agentic Review" })).not.toBeInTheDocument();
    expect(readOverview).toHaveBeenCalledTimes(3);
  });

  it("adds no trace, evidence, execution, retry, or approval controls", async () => {
    render(<AgenticOperationsDashboard readOverview={vi.fn(async () => READY_PAYLOAD)} />);

    await screen.findByRole("region", { name: "Canonical Agent Registry" });
    expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /execute|approve|reject|retry|trace|evidence/i })).not.toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: /Inspect pipeline run/ })).toHaveLength(2);
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
    expect(screen.getAllByRole("button")).toHaveLength(3);
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
