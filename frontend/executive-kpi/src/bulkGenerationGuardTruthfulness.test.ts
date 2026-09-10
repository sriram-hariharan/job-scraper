import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { expect, it, vi } from "vitest";

const REPO = resolve(__dirname, "../../..");
const PYTHON = "/Users/sriramhariharanneelakantan/.venvs/job_scrap314/bin/python3";
const flush = () => new Promise((done) => setTimeout(done, 0));

it("keeps scan drafts editable and reports a failed Bulk status check truthfully", async () => {
  const shellSource = readFileSync(resolve(REPO, "src/app/static/shell.js"), "utf8");
  const shellMarkup = execFileSync(
    PYTHON,
    ["-c", "import sys; sys.path.insert(0, '.'); from src.app.ui_shell import render_top_shell; print(render_top_shell('/scan-workspace'))"],
    { cwd: REPO, encoding: "utf8" },
  );

  document.body.innerHTML = `${shellMarkup}
    <main id="scanWorkspacePage">
      <input id="scanWorkspaceCompanyInput" data-bulk-safe="true" />
      <textarea id="scanWorkspaceJobDescriptionInput" data-bulk-safe="true"></textarea>
      <button id="scanWorkspaceStartScanBtn" type="button">Start scan</button>
    </main>`;

  const fetchMock = vi.fn(async (url: string) => {
    if (String(url).includes("/planning/bulk-generation/status")) {
      throw new Error("status endpoint unavailable");
    }
    return { ok: true, json: async () => ({}) };
  });
  vi.stubGlobal("fetch", fetchMock);
  window.fetch = fetchMock as unknown as typeof window.fetch;

  // eslint-disable-next-line no-new-func
  new Function(shellSource)();
  document.dispatchEvent(new Event("DOMContentLoaded", { bubbles: true }));
  await flush();
  await flush();

  const company = document.getElementById("scanWorkspaceCompanyInput") as HTMLInputElement;
  const jobDescription = document.getElementById("scanWorkspaceJobDescriptionInput") as HTMLTextAreaElement;
  const start = document.getElementById("scanWorkspaceStartScanBtn") as HTMLButtonElement;
  expect(company.getAttribute("data-bulk-guarded")).toBeNull();
  expect(jobDescription.getAttribute("data-bulk-guarded")).toBeNull();
  expect(start.getAttribute("data-bulk-guarded")).toBe("true");

  start.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  expect(document.getElementById("bulkGenerationGuardTooltip")?.textContent).toBe(
    "Bulk Generate status could not be verified. Retry before starting this action.",
  );
  const bulkApi = (window as unknown as {
    ApplyLensBulkGeneration: { getState: () => Record<string, unknown>; isActive: () => boolean };
  }).ApplyLensBulkGeneration;
  expect(bulkApi.getState()).toMatchObject({
    verified: false,
    verification: "failed",
    active: false,
  });
  expect(bulkApi.isActive()).toBe(false);

  vi.unstubAllGlobals();
});
