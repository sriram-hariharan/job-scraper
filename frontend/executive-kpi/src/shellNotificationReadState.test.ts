/**
 * Runtime proof for the Notification Center row presentation and the
 * read/unread mutation lifecycle.
 *
 * The read/unread control was flaky because its only in-flight guard lived on
 * the button element, and every refresh re-rendered the feed and destroyed that
 * element. This test boots the real classic shell script against the real
 * rendered shell markup and drives the row the way a browser does.
 * One boot per file keeps the script's MutationObserver from outliving the
 * test environment.
 */
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { expect, it, vi } from "vitest";

const REPO = resolve(__dirname, "../../..");
const PYTHON = "/Users/sriramhariharanneelakantan/.venvs/job_scrap314/bin/python3";

const ROW = {
  notification_id: "scheduled_run_email::sched_live_pipeline_1::live_pipeline",
  title: "Scheduled job SUCCEEDED | live_pipeline | display_jobs=102775",
  job_name: "live_pipeline",
  level: "success",
  run_status: "success",
  delivery_status: "recorded_outbox_only",
  notification_kind: "scheduled_run_email_delivery",
  created_at: "2026-09-01T23:34:05Z",
  is_read: false,
};

const flush = () => new Promise((done) => setTimeout(done, 0));

it("presents a structured title and runs exactly one read-state mutation per click", async () => {
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
  let releaseMutation: (() => void) | null = null;
  let releaseFeedReconciliation: (() => void) | null = null;
  let releaseCountReconciliation: (() => void) | null = null;
  let holdFirstReconciliation = false;
  let firstFeedReconciliationStarted = false;
  let firstCountReconciliationStarted = false;
  let failNextFeedReconciliation = false;
  const readStateCalls: string[] = [];
  let unreadCountCalls = 0;
  const alertSpy = vi.spyOn(window, "alert").mockImplementation(() => undefined);

  const fetchMock = vi.fn(async (url: string) => {
    const target = String(url);
    if (target.includes("/notifications/read-state")) {
      readStateCalls.push(target);
      if (readStateCalls.length > 3) {
        return {
          ok: false,
          status: 503,
          json: async () => ({ detail: "temporary read-state failure" }),
        };
      }
      if (readStateCalls.length === 2) {
        isRead = false;
        return {
          ok: true,
          status: 200,
          json: async () => ({ ok: true, notification: { ...ROW, is_read: false } }),
        };
      }
      if (readStateCalls.length === 3) {
        isRead = true;
        failNextFeedReconciliation = true;
        return {
          ok: true,
          status: 200,
          json: async () => ({ ok: true, notification: { ...ROW, is_read: true } }),
        };
      }
      // Hold the mutation open so a second click lands mid-flight.
      await new Promise<void>((done) => {
        releaseMutation = done;
      });
      isRead = true;
      holdFirstReconciliation = true;
      return {
        ok: true,
        json: async () => ({ ok: true, notification: { ...ROW, is_read: true } }),
      };
    }
    if (target.includes("/notifications/unread-count")) {
      unreadCountCalls += 1;
      if (holdFirstReconciliation && !firstCountReconciliationStarted) {
        firstCountReconciliationStarted = true;
        const staleUnreadCount = 0;
        await new Promise<void>((done) => {
          releaseCountReconciliation = done;
        });
        return { ok: true, json: async () => ({ unread_count: staleUnreadCount }) };
      }
      return { ok: true, json: async () => ({ unread_count: isRead ? 0 : 1 }) };
    }
    if (target.includes("/notifications")) {
      if (failNextFeedReconciliation) {
        failNextFeedReconciliation = false;
        return {
          ok: false,
          status: 503,
          json: async () => ({ detail: "temporary reconciliation failure" }),
        };
      }
      if (holdFirstReconciliation && !firstFeedReconciliationStarted) {
        firstFeedReconciliationStarted = true;
        await new Promise<void>((done) => {
          releaseFeedReconciliation = done;
        });
        return {
          ok: true,
          // Snapshot from the first confirmed mutation. It must not overwrite
          // the newer reverse mutation when this old request finally resolves.
          json: async () => ({ ok: true, rows: [{ ...ROW, is_read: true }] }),
        };
      }
      return {
        ok: true,
        json: async () => ({ ok: true, rows: [{ ...ROW, is_read: isRead }] }),
      };
    }
    return { ok: true, json: async () => ({ ok: true }) };
  });
  vi.stubGlobal("fetch", fetchMock);
  window.fetch = fetchMock as unknown as typeof window.fetch;

  // eslint-disable-next-line no-new-func
  new Function(shellSource)();
  document.dispatchEvent(new Event("DOMContentLoaded", { bubbles: true }));

  const bell = document.getElementById("notificationButton") as HTMLButtonElement;
  bell.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  await flush();
  await flush();

  // Reopening the panel must not register another delegated row handler.
  bell.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  bell.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  await flush();
  await flush();

  let row = document.querySelector(".notification-row") as HTMLElement;
  expect(row).not.toBeNull();

  // Exercise the production Unread-filter behavior: a successfully read row
  // should disappear as soon as the authoritative POST resolves.
  document.querySelector<HTMLElement>("[data-notification-filter='unread']")?.click();
  row = document.querySelector(".notification-row") as HTMLElement;

  // Task C: structured headline, metric pill, full subject in the tooltip.
  const title = row.querySelector(".notification-row__title") as HTMLElement;
  expect(title.textContent?.trim()).toBe("Live Pipeline completed");
  expect(title.getAttribute("data-tooltip")).toBe(ROW.title);
  expect(title.getAttribute("tabindex")).toBe("0");
  const pills = Array.from(row.querySelectorAll(".notification-pill")).map(
    (pill) => pill.textContent?.trim(),
  );
  expect(pills).toContain("102,775 jobs");
  expect(pills).toContain("Pipeline");
  expect(pills).toContain("SUCCESS");

  // Task D: no email summary text anywhere in the visible row.
  expect(row.textContent).not.toContain("Email summary");
  expect(row.querySelector(".notification-row__message")).toBeNull();

  // Task F: one click sends exactly one mutation and disables only that row.
  const toggle = row.querySelector("[data-notification-toggle]") as HTMLButtonElement;
  expect(toggle.getAttribute("data-next-read")).toBe("true");
  toggle.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  await flush();

  expect(readStateCalls).toHaveLength(1);
  const pending = document.querySelector(
    "[data-notification-toggle]",
  ) as HTMLButtonElement;
  expect(pending.hasAttribute("disabled")).toBe(true);
  expect(pending.getAttribute("aria-busy")).toBe("true");

  // A second click for the same notification while in flight is dropped, not raced.
  pending.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  await flush();
  expect(readStateCalls).toHaveLength(1);

  // The refresh must not blank the feed to the loading placeholder.
  const list = document.getElementById("notificationList") as HTMLElement;
  expect(list.textContent).not.toContain("Loading notifications");

  // Release the mutation. The authoritative POST response must update the row
  // and unread count before the deliberately slow reconciliation finishes.
  (releaseMutation as unknown as () => void)();
  await flush();
  await flush();

  expect(firstFeedReconciliationStarted).toBe(true);
  expect(firstCountReconciliationStarted).toBe(true);
  expect(document.querySelector(".notification-row")).toBeNull();
  expect(document.getElementById("notificationBadge")?.classList.contains("hidden")).toBe(true);

  // The authoritative response releases the per-notification lock before
  // either reconciliation request resolves, so the reverse action is usable.
  document.querySelector<HTMLElement>("[data-notification-filter='all']")?.click();
  expect(readStateCalls).toHaveLength(1);
  const settled = document.querySelector(
    "[data-notification-toggle]",
  ) as HTMLButtonElement;
  expect(settled.hasAttribute("disabled")).toBe(false);
  expect(settled.getAttribute("aria-busy")).toBeNull();
  expect(settled.getAttribute("data-next-read")).toBe("false");
  expect(
    (document.querySelector(".notification-row") as HTMLElement).classList.contains("is-read"),
  ).toBe(true);

  // The reverse action also completes normally from the confirmed response.
  settled.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  await flush();
  await flush();
  expect(readStateCalls).toHaveLength(2);
  const reversed = document.querySelector(
    "[data-notification-toggle]",
  ) as HTMLButtonElement;
  expect(reversed.getAttribute("data-next-read")).toBe("true");
  expect(
    (document.querySelector(".notification-row") as HTMLElement).classList.contains("is-unread"),
  ).toBe(true);

  // The older feed/count reconciliation resolves after the reverse mutation.
  // Newest-request-wins plus the confirmed overlay must preserve unread.
  (releaseFeedReconciliation as unknown as () => void)();
  (releaseCountReconciliation as unknown as () => void)();
  await flush();
  await flush();
  expect(unreadCountCalls).toBeGreaterThan(0);
  expect(
    (document.querySelector(".notification-row") as HTMLElement).classList.contains("is-unread"),
  ).toBe(true);
  expect(document.getElementById("notificationBadge")?.textContent).toBe("1");

  // A successful third mutation followed by failed background reconciliation
  // keeps its confirmed state usable and does not masquerade as POST failure.
  reversed.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  await flush();
  await flush();
  expect(readStateCalls).toHaveLength(3);
  expect(alertSpy).not.toHaveBeenCalled();
  const afterReconciliationFailure = document.querySelector(
    "[data-notification-toggle]",
  ) as HTMLButtonElement;
  expect(afterReconciliationFailure.disabled).toBe(false);
  expect(afterReconciliationFailure.getAttribute("data-next-read")).toBe("false");
  expect(
    (document.querySelector(".notification-row") as HTMLElement).classList.contains("is-read"),
  ).toBe(true);

  // A later failed POST still clears the state-based lock, reports the actual
  // mutation failure, and leaves the last confirmed row model intact.
  afterReconciliationFailure.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  await flush();
  await flush();
  expect(readStateCalls).toHaveLength(4);
  expect(alertSpy).toHaveBeenCalledWith(expect.stringContaining("temporary read-state failure"));
  const afterFailure = document.querySelector(
    "[data-notification-toggle]",
  ) as HTMLButtonElement;
  expect(afterFailure.disabled).toBe(false);
  expect(afterFailure.getAttribute("aria-busy")).toBeNull();
  expect(afterFailure.getAttribute("data-next-read")).toBe("false");

  // The row action stays inside the Bulk mutation guard; nothing bypasses it.
  expect(settled.closest("[data-bulk-safe]")).toBeNull();

  vi.unstubAllGlobals();
  alertSpy.mockRestore();
});
