/**
 * Runtime interaction proof for the shared-shell Notification Center.
 *
 * Static markup assertions did not catch a real bell regression, so this test
 * evaluates the actual classic shell script against the actual rendered shell
 * markup and drives the bell the way a browser does. One boot per file keeps
 * the script's MutationObserver from outliving the test environment.
 */
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { expect, it, vi } from "vitest";

const REPO = resolve(__dirname, "../../..");
const PYTHON = "/Users/sriramhariharanneelakantan/.venvs/job_scrap314/bin/python3";

const flush = () => new Promise((done) => setTimeout(done, 0));

it("fetches fresh bounded rows on every closed-to-open transition without weakening the Bulk guard", async () => {
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
  let serverRows: Array<Record<string, unknown>> = [{
    notification_id: "scheduled_run_email::initial::agent_discovery",
    title: "Scheduled job SUCCEEDED | agent_discovery | discovered=42",
    job_name: "agent_discovery",
    run_status: "succeeded",
    created_at: "2026-09-03T01:50:35Z",
    is_read: false,
  }];
  let bulkStatus = "running";
  let firstBulkStatus = true;
  let releaseBulkStatus: (() => void) | null = null;
  let mutationCalls = 0;
  const fetchMock = vi.fn(async (url: string, _options?: RequestInit) => {
    const target = String(url);
    if (target.includes("/planning/bulk-generation/status")) {
      if (firstBulkStatus) {
        firstBulkStatus = false;
        await new Promise<void>((done) => {
          releaseBulkStatus = done;
        });
      }
      return {
        ok: true,
        json: async () => ({ ok: true, status: bulkStatus }),
      };
    }
    if (
      target.includes("/notifications/read-state")
      || target.includes("/notifications/delete")
    ) {
      mutationCalls += 1;
    }
    return {
      url,
      ok: true,
      json: async () => ({
        ok: true,
        rows: target.includes("/notifications?") ? [...serverRows] : [],
        unread_count: serverRows.filter((row) => !row.is_read).length,
      }),
    };
  });
  vi.stubGlobal("fetch", fetchMock);
  window.fetch = fetchMock as unknown as typeof window.fetch;

  // eslint-disable-next-line no-new-func
  new Function(shellSource)();
  document.dispatchEvent(new Event("DOMContentLoaded", { bubbles: true }));

  const bell = document.getElementById("notificationButton") as HTMLButtonElement;
  const panel = document.getElementById("notificationDropdown") as HTMLElement;

  // 1-2. Bell exists; centre starts closed.
  expect(bell).not.toBeNull();
  expect(panel).not.toBeNull();
  expect(panel.classList.contains("hidden")).toBe(true);
  expect(bell.getAttribute("aria-expanded")).toBe("false");

  // 8. Shell state starts fail-closed, the strictest guard state the bell faces.
  expect(document.body.classList.contains("bulk-generation-guard-active")).toBe(true);
  expect(bell.getAttribute("data-bulk-guarded")).toBeNull();
  expect(bell.closest("[data-bulk-guarded='true']")).toBeNull();
  const chip = document.querySelector("[data-notification-filter='discovery']") as HTMLElement;
  expect(chip).not.toBeNull();
  expect(chip.closest("[data-bulk-guarded='true']")).toBeNull();
  const markAll = document.getElementById("notificationMarkAllReadBtn") as HTMLElement;
  expect(markAll.getAttribute("data-bulk-guarded")).toBe("true");
  expect(markAll.getAttribute("aria-describedby")).toBe("bulkGenerationGuardDescription");

  // 3-4. Clicking opens it.
  bell.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  expect(panel.classList.contains("hidden")).toBe(false);
  expect(bell.getAttribute("aria-expanded")).toBe("true");
  await flush();

  // While the initial Bulk status read is unresolved, browsing/filtering stays
  // available but every notification mutation is visibly fail-closed.
  const guardedToggle = document.querySelector("[data-notification-toggle]") as HTMLElement;
  const guardedDelete = document.querySelector("[data-notification-delete]") as HTMLElement;
  const deleteAll = document.getElementById("notificationDeleteAllBtn") as HTMLElement;
  for (const control of [guardedToggle, guardedDelete, markAll, deleteAll]) {
    expect(control.getAttribute("data-bulk-guarded")).toBe("true");
    expect(control.getAttribute("aria-disabled")).toBe("true");
    expect(control.getAttribute("aria-describedby")).toBe("bulkGenerationGuardDescription");
  }
  guardedToggle.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  expect(mutationCalls).toBe(0);
  expect(document.getElementById("bulkGenerationGuardTooltip")?.textContent).toBe(
    "Bulk Generate must finish or be stopped before this action is available.",
  );
  chip.click();
  expect(chip.classList.contains("is-active")).toBe(true);

  // Verification to ACTIVE preserves the explicit unavailable state.
  (releaseBulkStatus as unknown as () => void)();
  await flush();
  await flush();
  expect(guardedToggle.getAttribute("data-bulk-guarded")).toBe("true");

  // A later canonical INACTIVE result enables the controls in-place; the
  // panel does not need to close/reopen.
  bulkStatus = "none";
  Object.defineProperty(document, "hidden", { configurable: true, value: false });
  document.dispatchEvent(new Event("visibilitychange"));
  await flush();
  await flush();
  expect(fetchMock.mock.calls.filter((call) =>
    String(call[0]).includes("/planning/bulk-generation/status")
  )).toHaveLength(2);
  expect(document.body.classList.contains("bulk-generation-guard-active")).toBe(false);
  const enabledToggle = document.querySelector("[data-notification-toggle]") as HTMLElement;
  const enabledDelete = document.querySelector("[data-notification-delete]") as HTMLElement;
  for (const control of [enabledToggle, enabledDelete, markAll, deleteAll]) {
    expect(control.getAttribute("data-bulk-guarded")).toBeNull();
    expect(control.getAttribute("aria-disabled")).toBeNull();
  }

  // 9. Viewing never mutates read state.
  const urls = fetchMock.mock.calls.map((call) => String(call[0]));
  expect(urls.some((url) => url.includes("/notifications/read-state"))).toBe(false);

  // 10. Browsing controls stay reachable; mutation stays guarded.
  expect(chip.closest("[data-bulk-guarded='true']")).toBeNull();

  // 5. Clicking the bell again toggles it closed.
  bell.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  expect(panel.classList.contains("hidden")).toBe(true);
  expect(bell.getAttribute("aria-expanded")).toBe("false");

  // The server changes while the panel is closed. Reopening owns a new
  // no-store bounded GET and renders the new row without a manual Refresh.
  serverRows = [{
    notification_id: "scheduled_run_email::fresh::agent_discovery",
    title: "Scheduled job SUCCEEDED | agent_discovery | discovered=555",
    job_name: "agent_discovery",
    run_status: "succeeded",
    created_at: "2026-09-03T01:51:35Z",
    is_read: false,
  }];
  bell.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  await flush();
  await flush();
  expect(document.body.textContent).toContain("555 discovered");
  const feedCalls = fetchMock.mock.calls.filter((call) =>
    String(call[0]).includes("/notifications?limit=50"),
  );
  expect(feedCalls).toHaveLength(2);
  expect(feedCalls.every((call) => (call[1] as RequestInit | undefined)?.cache === "no-store")).toBe(true);

  // Close again before exercising the independent close paths below.
  bell.dispatchEvent(new MouseEvent("click", { bubbles: true }));

  // 6. Escape closes it.
  bell.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  expect(panel.classList.contains("hidden")).toBe(false);
  document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
  expect(panel.classList.contains("hidden")).toBe(true);

  // 7. Outside click closes it.
  bell.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  expect(panel.classList.contains("hidden")).toBe(false);
  document.body.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  expect(panel.classList.contains("hidden")).toBe(true);
  expect(bell.getAttribute("aria-expanded")).toBe("false");

  vi.unstubAllGlobals();
});
