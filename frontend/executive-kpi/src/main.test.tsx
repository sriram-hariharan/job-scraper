import { act, screen, waitFor } from "@testing-library/react";
import { beforeEach, expect, it, vi } from "vitest";

beforeEach(() => {
  vi.resetModules();
  document.body.innerHTML = '<section id="executiveKpiRoot"></section>';
  delete window.__APPLYLENS_EXECUTIVE_KPI_STATE__;
  delete window.__APPLYLENS_EXECUTIVE_QUEUE_STATE__;
  delete window.__APPLYLENS_PLANNING_WORKLIST_STATE__;
});

it("updates the mounted KPI island when the existing status owner publishes refresh states", async () => {
  await act(async () => {
    await import("./main");
  });

  expect(screen.getByLabelText("Loading executive queue metrics")).toBeInTheDocument();

  await act(async () => {
    window.dispatchEvent(new CustomEvent("applylens:executive-kpi-state", {
      detail: {
        status: "ready",
        metrics: {
          queueRows: 250,
          nextSteps: 31,
          undecidedJobReviews: 12,
          undecidedMaybeTailor: 8,
        },
      },
    }));
  });

  await waitFor(() => expect(screen.getByText("250")).toBeInTheDocument());

  await act(async () => {
    window.dispatchEvent(new CustomEvent("applylens:executive-kpi-state", {
      detail: { status: "error", message: "refresh failed" },
    }));
  });

  await waitFor(() => expect(screen.getAllByText("Unavailable")).toHaveLength(4));
});

it("hydrates from the latest state when status was published before the island mounts", async () => {
  window.__APPLYLENS_EXECUTIVE_KPI_STATE__ = {
    status: "ready",
    metrics: {
      queueRows: 77,
      nextSteps: 0,
      undecidedJobReviews: 3,
      undecidedMaybeTailor: 1,
    },
  };

  await act(async () => {
    await import("./main");
  });

  await waitFor(() => expect(screen.getByText("77")).toBeInTheDocument());
  expect(screen.getByText("0")).toBeInTheDocument();
  expect(screen.queryByLabelText("Loading executive queue metrics")).not.toBeInTheDocument();
});

it("hydrates and updates the queue island from the existing bridge state", async () => {
  document.body.innerHTML = '<section id="executiveQueueRoot"></section>';
  window.__APPLYLENS_EXECUTIVE_QUEUE_STATE__ = {
    status: "ready",
    rows: [{ job_doc_id: "job-one", job_title: "Initial Queue Job" }],
    metaLabel: "Browse view · 1 total job",
    viewMode: "simple",
    filters: { actions: [], preferenceIds: [], undecidedOnly: false, limit: 15 },
    preferenceOptions: [],
    pagination: {
      page: 1,
      pageSize: 15,
      totalCount: 1,
      totalPages: 1,
      hasPrevPage: false,
      hasNextPage: false,
    },
  };

  await act(async () => {
    await import("./main");
  });

  await waitFor(() => expect(screen.getByText("Initial Queue Job")).toBeInTheDocument());

  await act(async () => {
    window.dispatchEvent(new CustomEvent("applylens:executive-queue-state", {
      detail: {
        ...window.__APPLYLENS_EXECUTIVE_QUEUE_STATE__,
        rows: [{ job_doc_id: "job-two", job_title: "Refreshed Queue Job" }],
      },
    }));
  });

  await waitFor(() => expect(screen.getByText("Refreshed Queue Job")).toBeInTheDocument());
  expect(screen.queryByText("Initial Queue Job")).not.toBeInTheDocument();
});

it("mounts the Pipeline dashboard only when its dedicated server root exists", async () => {
  document.body.innerHTML = '<section id="pipelineDashboardRoot"></section>';
  const fetchMock = vi.spyOn(window, "fetch").mockResolvedValue(
    new Response(JSON.stringify({ pipeline: { status: "idle" } }), { status: 200 }),
  );

  await act(async () => {
    await import("./main");
  });

  await waitFor(() => expect(screen.getByText("Pipeline is idle")).toBeInTheDocument());
  expect(fetchMock).toHaveBeenCalledWith("/pipeline/status", expect.objectContaining({ method: "GET" }));
  expect(document.querySelectorAll("#pipelineDashboardRoot")).toHaveLength(1);
});

it("hydrates and updates both Planning islands from the existing Planning bridge state", async () => {
  document.body.innerHTML = '<section id="planningSummaryRoot"></section><section id="planningWorklistRoot"></section>';
  window.__APPLYLENS_PLANNING_WORKLIST_STATE__ = {
    status: "ready",
    rows: [{ job_doc_id: "planning-one", queue_rank: 1, job_title: "Initial Planning Job" }],
    metaLabel: "Planning view · 1 total job",
    pagination: { page: 1, pageSize: 15, totalCount: 1, totalPages: 1, hasPrevPage: false, hasNextPage: false },
    sort: { key: "queue_rank", direction: "asc" },
    resultKey: "planning-one",
    metrics: { total: 1, readyForReview: 0, packetReady: 0, needsDecision: 1 },
  };

  await act(async () => {
    await import("./main");
  });
  await waitFor(() => expect(screen.getByRole("link", { name: "Initial Planning Job" })).toBeInTheDocument());
  expect(screen.getByLabelText("Planning summary")).toBeInTheDocument();

  await act(async () => {
    window.dispatchEvent(new CustomEvent("applylens:planning-worklist-state", {
      detail: {
        ...window.__APPLYLENS_PLANNING_WORKLIST_STATE__,
        rows: [{ job_doc_id: "planning-two", queue_rank: 1, job_title: "Refreshed Planning Job" }],
        resultKey: "planning-two",
      },
    }));
  });

  await waitFor(() => expect(screen.getByRole("link", { name: "Refreshed Planning Job" })).toBeInTheDocument());
  expect(screen.queryByRole("link", { name: "Initial Planning Job" })).not.toBeInTheDocument();
});
