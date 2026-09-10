/** Runtime proof that hung notification reconciliation is bounded and non-blocking. */
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { expect, it, vi } from "vitest";

const REPO = resolve(__dirname, "../../..");
const PYTHON = "/Users/sriramhariharanneelakantan/.venvs/job_scrap314/bin/python3";

const ROW = {
  notification_id: "scheduled_run_email::hung-reconciliation::live_pipeline",
  title: "Scheduled job SUCCEEDED | live_pipeline | display_jobs=12",
  job_name: "live_pipeline",
  run_status: "succeeded",
  created_at: "2026-09-03T02:10:00Z",
  is_read: false,
};

const flushMicrotasks = async () => {
  for (let index = 0; index < 8; index += 1) await Promise.resolve();
};

it("aborts hung background reconciliation without relocking or reporting mutation failure", async () => {
  vi.useFakeTimers();
  const shellSource = readFileSync(resolve(REPO, "src/app/static/shell.js"), "utf8");
  const shellMarkup = execFileSync(
    PYTHON,
    [
      "-c",
      "import sys; sys.path.insert(0, '.'); from src.app.ui_shell import render_top_shell; print(render_top_shell('/planning'))",
    ],
    { cwd: REPO, encoding: "utf8" },
  );
  document.body.innerHTML = shellMarkup;

  let isRead = false;
  let hangReconciliation = false;
  let mutationCalls = 0;
  let reconciliationAborts = 0;
  let feedCalls = 0;
  const alertSpy = vi.spyOn(window, "alert").mockImplementation(() => undefined);

  const fetchMock = vi.fn(async (url: string, options?: RequestInit) => {
    const target = String(url);
    if (target.includes("/planning/bulk-generation/status")) {
      return { ok: true, status: 200, json: async () => ({ ok: true, status: "none" }) };
    }
    if (target.includes("/notifications/read-state")) {
      mutationCalls += 1;
      isRead = true;
      hangReconciliation = true;
      return {
        ok: true,
        status: 200,
        json: async () => ({ ok: true, notification: { ...ROW, is_read: true } }),
      };
    }
    if (target.includes("/notifications/unread-count")) {
      if (hangReconciliation) {
        return await new Promise((_resolve, reject) => {
          options?.signal?.addEventListener("abort", () => {
            reconciliationAborts += 1;
            hangReconciliation = false;
            reject(new DOMException("Aborted", "AbortError"));
          }, { once: true });
        });
      }
      return { ok: true, status: 200, json: async () => ({ unread_count: isRead ? 0 : 1 }) };
    }
    if (target.includes("/notifications")) {
      feedCalls += 1;
      if (hangReconciliation) {
        return await new Promise((_resolve, reject) => {
          options?.signal?.addEventListener("abort", () => {
            reconciliationAborts += 1;
            hangReconciliation = false;
            reject(new DOMException("Aborted", "AbortError"));
          }, { once: true });
        });
      }
      return {
        ok: true,
        status: 200,
        json: async () => ({ rows: [{ ...ROW, is_read: isRead }] }),
      };
    }
    return { ok: true, status: 200, json: async () => ({ ok: true }) };
  });
  vi.stubGlobal("fetch", fetchMock);
  window.fetch = fetchMock as unknown as typeof window.fetch;

  // eslint-disable-next-line no-new-func
  new Function(shellSource)();
  document.dispatchEvent(new Event("DOMContentLoaded", { bubbles: true }));
  await flushMicrotasks();

  document.getElementById("notificationButton")?.dispatchEvent(
    new MouseEvent("click", { bubbles: true }),
  );
  await flushMicrotasks();

  const toggle = document.querySelector("[data-notification-toggle]") as HTMLButtonElement;
  toggle.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  await flushMicrotasks();

  expect(mutationCalls).toBe(1);
  expect((document.querySelector(".notification-row") as HTMLElement).classList.contains("is-read")).toBe(true);
  const confirmedToggle = document.querySelector("[data-notification-toggle]") as HTMLButtonElement;
  expect(confirmedToggle.disabled).toBe(false);
  expect(confirmedToggle.getAttribute("aria-busy")).toBeNull();
  expect(alertSpy).not.toHaveBeenCalled();

  await vi.advanceTimersByTimeAsync(12000);
  await flushMicrotasks();

  expect(reconciliationAborts).toBeGreaterThanOrEqual(1);
  expect((document.querySelector(".notification-row") as HTMLElement).classList.contains("is-read")).toBe(true);
  expect((document.querySelector("[data-notification-toggle]") as HTMLButtonElement).disabled).toBe(false);
  expect(alertSpy).not.toHaveBeenCalled();

  const feedCallsBeforeRefresh = feedCalls;
  document.getElementById("notificationRefreshBtn")?.dispatchEvent(
    new MouseEvent("click", { bubbles: true }),
  );
  await flushMicrotasks();
  expect(feedCalls).toBeGreaterThan(feedCallsBeforeRefresh);
  expect((document.querySelector(".notification-row") as HTMLElement).classList.contains("is-read")).toBe(true);

  vi.clearAllTimers();
  vi.useRealTimers();
  vi.unstubAllGlobals();
  alertSpy.mockRestore();
});
