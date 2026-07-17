import { act, screen, waitFor } from "@testing-library/react";
import { beforeEach, expect, it, vi } from "vitest";

beforeEach(() => {
  vi.resetModules();
  document.body.innerHTML = '<section id="executiveKpiRoot"></section>';
  delete window.__APPLYLENS_EXECUTIVE_KPI_STATE__;
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
