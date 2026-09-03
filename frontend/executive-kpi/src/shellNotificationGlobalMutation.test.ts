/** Runtime proof that global notification locks cover mutations, not reconciliation. */
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { expect, it, vi } from "vitest";

const REPO = resolve(__dirname, "../../..");
const PYTHON = "/Users/sriramhariharanneelakantan/.venvs/job_scrap314/bin/python3";
const flush = () => new Promise((done) => setTimeout(done, 0));

const ROW = {
  notification_id: "scheduled_run_email::mark-all::agent_discovery",
  title: "Scheduled job SUCCEEDED | agent_discovery | discovered=21",
  job_name: "agent_discovery",
  run_status: "succeeded",
  created_at: "2026-09-03T02:20:00Z",
  is_read: false,
};

it("releases Mark-all global controls after confirmed POSTs while reconciliation is pending", async () => {
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
  let readStateCalls = 0;
  let releaseMutation: (() => void) | null = null;
  let releaseFeedReconciliation: (() => void) | null = null;
  let releaseCountReconciliation: (() => void) | null = null;
  let holdReconciliation = false;
  let feedHeld = false;
  let countHeld = false;

  const fetchMock = vi.fn(async (url: string) => {
    const target = String(url);
    if (target.includes("/planning/bulk-generation/status")) {
      return { ok: true, status: 200, json: async () => ({ ok: true, status: "none" }) };
    }
    if (target.includes("/notifications/read-state")) {
      readStateCalls += 1;
      await new Promise<void>((done) => {
        releaseMutation = done;
      });
      isRead = true;
      holdReconciliation = true;
      return {
        ok: true,
        status: 200,
        json: async () => ({ ok: true, notification: { ...ROW, is_read: true } }),
      };
    }
    if (target.includes("/notifications/unread-count")) {
      if (holdReconciliation && !countHeld) {
        countHeld = true;
        await new Promise<void>((done) => {
          releaseCountReconciliation = done;
        });
        return { ok: true, status: 200, json: async () => ({ unread_count: 0 }) };
      }
      return { ok: true, status: 200, json: async () => ({ unread_count: isRead ? 0 : 1 }) };
    }
    if (target.includes("/notifications")) {
      if (holdReconciliation && !feedHeld) {
        feedHeld = true;
        await new Promise<void>((done) => {
          releaseFeedReconciliation = done;
        });
        return { ok: true, status: 200, json: async () => ({ rows: [{ ...ROW, is_read: false }] }) };
      }
      const unreadOnly = target.includes("is_read=false");
      const rows = unreadOnly && isRead ? [] : [{ ...ROW, is_read: isRead }];
      return { ok: true, status: 200, json: async () => ({ rows }) };
    }
    return { ok: true, status: 200, json: async () => ({ ok: true }) };
  });
  vi.stubGlobal("fetch", fetchMock);
  window.fetch = fetchMock as unknown as typeof window.fetch;

  // eslint-disable-next-line no-new-func
  new Function(shellSource)();
  document.dispatchEvent(new Event("DOMContentLoaded", { bubbles: true }));
  await flush();
  document.getElementById("notificationButton")?.dispatchEvent(
    new MouseEvent("click", { bubbles: true }),
  );
  await flush();
  await flush();

  const markAll = document.getElementById("notificationMarkAllReadBtn") as HTMLButtonElement;
  markAll.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  await flush();
  expect(readStateCalls).toBe(1);
  expect(markAll.disabled).toBe(true);

  // A duplicate event during the authoritative POST is suppressed.
  markAll.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  await flush();
  expect(readStateCalls).toBe(1);

  (releaseMutation as unknown as () => void)();
  await flush();
  await flush();

  expect(feedHeld).toBe(true);
  expect(countHeld).toBe(true);
  expect(markAll.disabled).toBe(false);
  expect((document.getElementById("notificationDeleteAllBtn") as HTMLButtonElement).disabled).toBe(false);
  expect((document.querySelector("[data-notification-toggle]") as HTMLButtonElement).disabled).toBe(false);
  expect((document.querySelector(".notification-row") as HTMLElement).classList.contains("is-read")).toBe(true);

  (releaseFeedReconciliation as unknown as () => void)();
  (releaseCountReconciliation as unknown as () => void)();
  await flush();
  await flush();
  expect((document.querySelector(".notification-row") as HTMLElement).classList.contains("is-read")).toBe(true);

  vi.unstubAllGlobals();
});
