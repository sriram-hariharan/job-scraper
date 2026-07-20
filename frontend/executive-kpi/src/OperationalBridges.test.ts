import { beforeEach, expect, it, vi } from "vitest";
import { waitFor } from "@testing-library/react";

function response(payload: unknown) {
  return Promise.resolve(new Response(JSON.stringify(payload), { status: 200 }));
}

beforeEach(() => {
  vi.resetModules();
  vi.restoreAllMocks();
  document.body.innerHTML = "";
  delete window.__APPLYLENS_DECISIONS_STATE__;
  delete window.__APPLYLENS_APPLICATIONS_STATE__;
  delete window.__APPLYLENS_DECISIONS_REACT_READY__;
  delete window.__APPLYLENS_APPLICATIONS_REACT_READY__;
  vi.spyOn(document, "readyState", "get").mockReturnValue("complete");
});

it("initializes Decisions once, maps the current payload, and replays readiness without refetching", async () => {
  document.body.innerHTML = `
    <button id="closeAppErrorModalBtn"></button><button id="appErrorOkBtn"></button>
    <button id="closeApplicationModalBtn"></button><section id="appErrorModal" class="hidden"></section>
    <span id="appErrorTitle"></span><span id="appErrorSubtitle"></span><span id="appErrorMessage"></span>
    <section id="applicationActionModal" class="hidden"></section><span id="applicationModalCompany"></span><span id="applicationModalTitle"></span>
    <button data-status-action="APPLIED"></button>`;
  const fetchMock = vi.spyOn(window, "fetch").mockImplementation(() => response({
    rows: [{ job_doc_id: "decision-one", job_title: "Decision Bridge Job", decision: "APPLY" }],
    total_count: 1, page: 1, page_size: 15, total_pages: 1, has_prev_page: false, has_next_page: false,
  }));
  window.__APPLYLENS_DECISIONS_REACT_READY__ = true;

  // @ts-expect-error The browser bridge is intentionally a classic static module.
  await import("../../../src/app/static/decisions.js");
  await waitFor(() => expect(window.__APPLYLENS_DECISIONS_STATE__?.status).toBe("ready"));
  expect(fetchMock).toHaveBeenCalledTimes(1);
  expect(fetchMock.mock.calls[0][0]).toContain("/decisions?");
  expect(window.__APPLYLENS_DECISIONS_STATE__?.rows[0].job_title).toBe("Decision Bridge Job");
  expect(window.__APPLYLENS_DECISIONS_STATE__?.pagination.totalCount).toBe(1);

  window.dispatchEvent(new CustomEvent("applylens:decisions-dashboard-ready"));
  window.dispatchEvent(new CustomEvent("applylens:decisions-dashboard-ready"));
  expect(fetchMock).toHaveBeenCalledTimes(1);
});

it("finalizes APPLIED rows, switches once to SAVED, and replays readiness without refetching", async () => {
  document.body.innerHTML = `
    <button id="closeAppErrorModalBtn"></button><button id="appErrorOkBtn"></button>
    <section id="appErrorModal" class="hidden"></section>
    <span id="appErrorTitle"></span><span id="appErrorSubtitle"></span><span id="appErrorMessage"></span>`;
  const fetchMock = vi.spyOn(window, "fetch").mockImplementation((input) => {
    const url = String(input);
    if (url.includes("company_contains=error")) return Promise.resolve(new Response("backend unavailable", { status: 503 }));
    if (url.includes("title_contains=none")) return response({
      rows: [], total_count: 0, page: 1, page_size: 15, total_pages: 1, has_prev_page: false, has_next_page: false,
    });
    if (url.startsWith("/saved-jobs?")) return response({
      rows: [{ action_key: "saved-one", job_title: "Saved Bridge Job", application_status: "SAVED" }],
      total_count: 1, page: 1, page_size: 15, total_pages: 1, has_prev_page: false, has_next_page: false,
    });
    return response({
      rows: [{ action_key: "applied-one", job_title: "Applied Bridge Job", application_status: "APPLIED", note: "" }],
      total_count: 1, page: 1, page_size: 15, total_pages: 1, has_prev_page: false, has_next_page: false,
    });
  });
  window.__APPLYLENS_APPLICATIONS_REACT_READY__ = true;

  // @ts-expect-error The browser bridge is intentionally a classic static module.
  await import("../../../src/app/static/application_views.js");
  await waitFor(() => expect(window.__APPLYLENS_APPLICATIONS_STATE__?.status).toBe("ready"));
  expect(fetchMock).toHaveBeenCalledTimes(1);
  expect(fetchMock.mock.calls[0][0]).toContain("/applied-jobs?");
  expect(window.__APPLYLENS_APPLICATIONS_STATE__?.activeTab).toBe("APPLIED");
  expect(window.__APPLYLENS_APPLICATIONS_STATE__?.rows[0].job_title).toBe("Applied Bridge Job");
  expect(window.__APPLYLENS_APPLICATIONS_STATE__?.pagination.totalCount).toBe(1);

  window.dispatchEvent(new CustomEvent("applylens:applications-dashboard-action", { detail: { type: "tab_change", tab: "SAVED" } }));
  await waitFor(() => expect(window.__APPLYLENS_APPLICATIONS_STATE__?.activeTab).toBe("SAVED"));
  await waitFor(() => expect(window.__APPLYLENS_APPLICATIONS_STATE__?.status).toBe("ready"));
  expect(fetchMock).toHaveBeenCalledTimes(2);
  expect(fetchMock.mock.calls[1][0]).toContain("/saved-jobs?");
  expect(fetchMock.mock.calls[1][0]).not.toContain("application_status");
  expect(window.__APPLYLENS_APPLICATIONS_STATE__?.rows[0].job_title).toBe("Saved Bridge Job");
  expect(window.__APPLYLENS_APPLICATIONS_STATE__?.pagination.totalCount).toBe(1);

  window.dispatchEvent(new CustomEvent("applylens:applications-dashboard-action", { detail: {
    type: "apply_filters", filters: { companyContains: "", titleContains: "none", limit: 15 },
  } }));
  await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
  await waitFor(() => expect(window.__APPLYLENS_APPLICATIONS_STATE__?.status).toBe("ready"));
  expect(window.__APPLYLENS_APPLICATIONS_STATE__?.rows).toEqual([]);
  expect(window.__APPLYLENS_APPLICATIONS_STATE__?.pagination.totalCount).toBe(0);

  window.dispatchEvent(new CustomEvent("applylens:applications-dashboard-action", { detail: {
    type: "apply_filters", filters: { companyContains: "error", titleContains: "", limit: 15 },
  } }));
  await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(4));
  await waitFor(() => expect(window.__APPLYLENS_APPLICATIONS_STATE__?.status).toBe("error"));
  expect(window.__APPLYLENS_APPLICATIONS_STATE__?.message).toContain("backend unavailable");

  window.dispatchEvent(new CustomEvent("applylens:applications-dashboard-ready"));
  window.dispatchEvent(new CustomEvent("applylens:applications-dashboard-ready"));
  expect(fetchMock).toHaveBeenCalledTimes(4);
});
