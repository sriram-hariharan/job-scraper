/** Runtime proof for Notification Center delete confirmation and mutation locks. */
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { expect, it, vi } from "vitest";

const REPO = resolve(__dirname, "../../..");
const PYTHON = "/Users/sriramhariharanneelakantan/.venvs/job_scrap314/bin/python3";

const rows = [
  {
    notification_id: "scheduled_run_email::discovery-1::agent_discovery",
    title: "Scheduled job SUCCEEDED | agent_discovery | discovered=42",
    job_name: "agent_discovery",
    run_status: "succeeded",
    created_at: "2026-09-02T12:00:00Z",
    is_read: false,
  },
  {
    notification_id: "scheduled_run_email::pipeline-1::live_pipeline",
    title: "Scheduled job SUCCEEDED | live_pipeline | display_jobs=8",
    job_name: "live_pipeline",
    run_status: "succeeded",
    created_at: "2026-09-02T11:00:00Z",
    is_read: true,
  },
];

const flush = () => new Promise((done) => setTimeout(done, 0));

it("confirms owner deletion, blocks duplicate row mutations, and supports Delete all", async () => {
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

  const deleted = new Set<string>();
  let deleteCalls = 0;
  let deleteAllCalls = 0;
  let firstDeleteFails = true;
  let releaseDelete: (() => void) | null = null;
  let releaseDeleteReconciliation: (() => void) | null = null;
  let holdReconciliation = false;
  const alertSpy = vi.spyOn(window, "alert").mockImplementation(() => undefined);

  const fetchMock = vi.fn(async (url: string, options?: RequestInit) => {
    const target = String(url);
    if (target.includes("/planning/bulk-generation/status")) {
      return { ok: true, status: 200, json: async () => ({ ok: true, status: "none" }) };
    }
    if (target.endsWith("/notifications/delete")) {
      deleteCalls += 1;
      if (firstDeleteFails) {
        firstDeleteFails = false;
        return {
          ok: false,
          status: 409,
          json: async () => ({
            detail: {
              error_category: "bulk_generation_in_progress",
              message: "Bulk Generate must finish or be stopped before this action is available.",
            },
          }),
        };
      }
      await new Promise<void>((done) => {
        releaseDelete = done;
      });
      const body = JSON.parse(String(options?.body || "{}"));
      deleted.add(String(body.notification_id));
      holdReconciliation = true;
      return {
        ok: true,
        status: 200,
        json: async () => ({
          ok: true,
          notification_id: String(body.notification_id),
          deleted: true,
        }),
      };
    }
    if (target.endsWith("/notifications/delete-all")) {
      deleteAllCalls += 1;
      rows.forEach((row) => deleted.add(row.notification_id));
      holdReconciliation = true;
      return {
        ok: true,
        status: 200,
        json: async () => ({
          ok: true,
          deleted: true,
          state_row: { state_timestamp: "2026-09-02T12:01:00Z" },
        }),
      };
    }
    if (target.includes("/notifications/unread-count")) {
      const visible = rows.filter((row) => !deleted.has(row.notification_id));
      return {
        ok: true,
        status: 200,
        json: async () => ({ unread_count: visible.filter((row) => !row.is_read).length }),
      };
    }
    if (target.includes("/notifications")) {
      if (holdReconciliation) {
        holdReconciliation = false;
        await new Promise<void>((done) => {
          releaseDeleteReconciliation = done;
        });
        // Return the pre-delete snapshot to prove a stale feed cannot
        // resurrect a locally confirmed deletion.
        return { ok: true, status: 200, json: async () => ({ rows: [...rows] }) };
      }
      return {
        ok: true,
        status: 200,
        json: async () => ({ rows: rows.filter((row) => !deleted.has(row.notification_id)) }),
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

  document.getElementById("notificationButton")?.dispatchEvent(
    new MouseEvent("click", { bubbles: true }),
  );
  await flush();
  await flush();

  const discoveryRow = document.querySelector(
    '[data-notification-id="scheduled_run_email::discovery-1::agent_discovery"]',
  ) as HTMLElement;
  const deleteButton = discoveryRow.querySelector(
    '[data-notification-delete]',
  ) as HTMLButtonElement;
  expect(deleteButton.getAttribute("aria-label")).toBe("Delete notification");

  deleteButton.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  const modal = document.getElementById("notificationDeleteConfirmModal") as HTMLElement;
  expect(modal.parentElement).toBe(document.body);
  expect(modal.classList.contains("hidden")).toBe(false);
  expect(document.getElementById("notificationDeleteConfirmTitle")?.textContent).toBe(
    "Delete notification?",
  );
  expect(deleteCalls).toBe(0);
  expect(discoveryRow.isConnected).toBe(true);

  document.getElementById("notificationDeleteCancelBtn")?.dispatchEvent(
    new MouseEvent("click", { bubbles: true }),
  );
  expect(modal.classList.contains("hidden")).toBe(true);
  expect(deleteCalls).toBe(0);

  deleteButton.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  const confirm = document.getElementById("notificationDeleteConfirmBtn") as HTMLButtonElement;
  confirm.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  await flush();
  expect(alertSpy).toHaveBeenCalledWith(
    expect.stringContaining("Bulk Generate must finish or be stopped"),
  );
  expect(confirm.disabled).toBe(false);
  expect(deleteButton.disabled).toBe(false);

  // Retry and double-click while the successful mutation is held open.
  confirm.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  await flush();
  confirm.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  await flush();
  expect(deleteCalls).toBe(2);
  expect(deleteButton.disabled).toBe(true);
  (releaseDelete as unknown as () => void)();
  await flush();
  await flush();
  expect(document.body.textContent).not.toContain("42 discovered");
  expect(modal.classList.contains("hidden")).toBe(true);
  // The authoritative tombstone releases the interaction lock even though
  // canonical feed reconciliation is still deliberately unresolved.
  expect(document.getElementById("notificationDeleteAllBtn")?.hasAttribute("disabled")).toBe(false);
  const remainingDelete = document.querySelector(
    '[data-notification-id="scheduled_run_email::pipeline-1::live_pipeline"] [data-notification-delete]',
  ) as HTMLButtonElement;
  expect(remainingDelete.disabled).toBe(false);
  (releaseDeleteReconciliation as unknown as () => void)();
  await flush();
  await flush();
  expect(document.body.textContent).not.toContain("42 discovered");

  const deleteAll = document.getElementById("notificationDeleteAllBtn") as HTMLButtonElement;
  deleteAll.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  expect(document.getElementById("notificationDeleteConfirmTitle")?.textContent).toBe(
    "Delete all notifications?",
  );
  expect(document.getElementById("notificationDeleteConfirmBody")?.textContent).toContain(
    "all notifications from your inbox",
  );
  confirm.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  await flush();
  expect(document.querySelectorAll(".notification-row")).toHaveLength(0);
  expect(deleteAll.disabled).toBe(false);
  expect(confirm.disabled).toBe(false);
  (releaseDeleteReconciliation as unknown as () => void)();
  await flush();
  await flush();
  expect(deleteAllCalls).toBe(1);
  expect(document.querySelectorAll(".notification-row")).toHaveLength(0);

  vi.unstubAllGlobals();
  alertSpy.mockRestore();
});
