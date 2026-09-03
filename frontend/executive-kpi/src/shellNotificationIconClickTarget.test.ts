/**
 * Regression proof for the actual reported "Mark read/unread sometimes does
 * nothing" defect.
 *
 * Root cause: the delegated notification-list click listener gated on
 * `event.target instanceof HTMLElement`. Every row action button's visible
 * surface is almost entirely its nested 14x14 <svg> icon, and SVG elements
 * (and their <path>/<rect> children) are instances of SVGElement, not
 * HTMLElement, even though .closest() resolves identically on both. A click
 * landing on the icon itself - which is most of what a user can see and aim
 * at - was silently dropped before ever reaching target.closest(...). A click
 * landing on the button's own padding (HTMLElement) worked. That produced
 * exactly the reported symptom: seemingly random dead clicks that "worked
 * later" once the user's pointer happened to land outside the icon.
 *
 * This test dispatches clicks directly on the nested <svg>/<path> targets,
 * the way a real pointer click on the icon does, and must fail against the
 * pre-fix `instanceof HTMLElement` guard and pass against the fixed
 * `instanceof Element` guard.
 *
 * One boot per file keeps the script's MutationObserver and delegated
 * listeners from outliving the test environment / leaking into other tests.
 */
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { expect, it, vi } from "vitest";

const REPO = resolve(__dirname, "../../..");
const PYTHON = "/Users/sriramhariharanneelakantan/.venvs/job_scrap314/bin/python3";
const flush = () => new Promise((done) => setTimeout(done, 0));

const ROW = {
  notification_id: "scheduled_run_email::sched_agent_discovery_icon::agent_discovery",
  title: "Scheduled job SUCCEEDED | agent_discovery | discovered=42",
  job_name: "agent_discovery",
  run_status: "succeeded",
  delivery_status: "recorded_outbox_only",
  notification_kind: "scheduled_run_email_delivery",
  created_at: "2026-09-03T02:00:00Z",
  is_read: false,
};

it("delivers icon-target clicks to mark-read, delete, and the Bulk guard identically to button clicks", async () => {
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
  let deleted = false;
  let bulkStatus: "none" | "running" = "running";
  const readStateCalls: string[] = [];
  const deleteCalls: string[] = [];

  const fetchMock = vi.fn(async (url: string) => {
    const target = String(url);
    if (target.includes("/planning/bulk-generation/status")) {
      return { ok: true, status: 200, json: async () => ({ ok: true, status: bulkStatus }) };
    }
    if (target.includes("/notifications/read-state")) {
      readStateCalls.push(target);
      isRead = !isRead;
      return {
        ok: true,
        status: 200,
        json: async () => ({ ok: true, notification: { ...ROW, is_read: isRead } }),
      };
    }
    if (target.includes("/notifications/delete-all")) {
      deleted = true;
      return {
        ok: true,
        status: 200,
        json: async () => ({ deleted: true, state_row: { state_timestamp: new Date().toISOString() } }),
      };
    }
    if (target.includes("/notifications/delete")) {
      deleteCalls.push(target);
      deleted = true;
      return {
        ok: true,
        status: 200,
        json: async () => ({ deleted: true, notification_id: ROW.notification_id }),
      };
    }
    if (target.includes("/notifications/unread-count")) {
      return { ok: true, status: 200, json: async () => ({ unread_count: deleted || isRead ? 0 : 1 }) };
    }
    if (target.includes("/notifications")) {
      return {
        ok: true,
        status: 200,
        json: async () => ({ ok: true, rows: deleted ? [] : [{ ...ROW, is_read: isRead }] }),
      };
    }
    return { ok: true, status: 200, json: async () => ({ ok: true }) };
  });
  vi.stubGlobal("fetch", fetchMock);
  window.fetch = fetchMock as unknown as typeof window.fetch;

  // eslint-disable-next-line no-new-func
  new Function(shellSource)();
  document.dispatchEvent(new Event("DOMContentLoaded", { bubbles: true }));
  await flush();

  const bell = document.getElementById("notificationButton") as HTMLButtonElement;
  bell.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  await flush();
  await flush();

  const toggleIcon = () =>
    (document.querySelector("[data-notification-toggle]") as HTMLButtonElement).querySelector(
      "svg",
    ) as unknown as Element;

  // --- 1. While Bulk is active, an icon-target click must still be blocked. ---
  expect(bulkStatus).toBe("running");
  toggleIcon().dispatchEvent(new MouseEvent("click", { bubbles: true }));
  await flush();
  expect(readStateCalls).toHaveLength(0);

  // --- 2. Once Bulk clears, the same icon-target click reaches the mutation. ---
  bulkStatus = "none";
  await (window as unknown as { ApplyLensBulkGeneration: { refresh: () => Promise<unknown> } })
    .ApplyLensBulkGeneration.refresh();
  await flush();

  const icon = toggleIcon();
  expect(icon).not.toBeNull();
  expect(icon instanceof HTMLElement).toBe(false);
  expect(icon instanceof SVGElement).toBe(true);

  icon.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  await flush();
  expect(readStateCalls).toHaveLength(1);

  // --- 3. A click on the SVG's nested <path> works identically. ---
  const path = (document.querySelector("[data-notification-toggle]") as HTMLButtonElement).querySelector(
    "svg path",
  ) as unknown as Element;
  expect(path).not.toBeNull();
  expect(path instanceof HTMLElement).toBe(false);
  path.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  await flush();
  expect(readStateCalls).toHaveLength(2);

  // --- 4. Still exactly one mutation per icon click after a feed rerender. ---
  document.querySelector<HTMLElement>("[data-notification-filter='discovery']")?.click();
  document.querySelector<HTMLElement>("[data-notification-filter='all']")?.click();
  toggleIcon().dispatchEvent(new MouseEvent("click", { bubbles: true }));
  await flush();
  expect(readStateCalls).toHaveLength(3);

  // --- 5. Delete: an icon-target click opens confirmation, not a silent no-op. ---
  const deleteIcon = (document.querySelector("[data-notification-delete]") as HTMLButtonElement).querySelector(
    "svg path",
  ) as unknown as Element;
  expect(deleteIcon).not.toBeNull();
  deleteIcon.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  await flush();

  const confirmModal = document.getElementById("notificationDeleteConfirmModal");
  expect(confirmModal?.classList.contains("hidden")).toBe(false);
  expect(deleteCalls).toHaveLength(0);

  const confirmBtn = document.getElementById("notificationDeleteConfirmBtn") as HTMLButtonElement;
  confirmBtn.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  await flush();
  await flush();

  expect(deleteCalls).toHaveLength(1);
  expect(document.querySelector(".notification-row")).toBeNull();

  vi.unstubAllGlobals();
});
