/** Actual classic Profile markup and JavaScript; no production APIs or database. */
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { beforeEach, afterEach, expect, it, vi } from "vitest";

const repo = resolve(__dirname, "../../..");
const python = process.env.PROFILE_TEST_PYTHON || "/Users/sriramhariharanneelakantan/.venvs/job_scrap314/bin/python";
const markup = execFileSync(python, ["-c", `from starlette.requests import Request
from src.app.profile_ui import profile_page
r = Request({"type":"http","method":"GET","path":"/profile","headers":[],"query_string":b""})
r.state.auth_user = {"user_id":"actor","is_admin":True,"access_level":"admin"}
print(profile_page(r))`], { cwd: repo, encoding: "utf8" });
const source = readFileSync(resolve(repo, "src/app/static/profile.js"), "utf8")
  .replace('window.addEventListener("DOMContentLoaded", initProfilePage);', "");
const users = [
  { user_id: "private-id-1", display_name: "Maya Chen", email: "maya@example.test", access_level: "user", is_active: true },
  { user_id: "private-id-2", display_name: "John Davis", email: "john@example.test", access_level: "user", is_active: false },
  { user_id: "private-id-3", display_name: "Aisha Patel", email: "aisha@example.test", access_level: "super_user", is_active: true },
  { user_id: "private-id-4", display_name: "Admin Legacy", email: "admin@example.test", access_level: "super_user", is_admin: true, is_active: true },
  { user_id: "private-id-5", display_name: "Admin Role", email: "admin2@example.test", access_level: " ADMIN ", is_active: true },
];
const el = (id: string) => document.getElementById(id)!;
const roleButton = (id: string) => document.querySelector<HTMLButtonElement>(`[data-admin-user-role="${id}"]`)!;
const flush = () => new Promise((done) => setTimeout(done, 0));
const hasInertAncestor = (element: HTMLElement): boolean => Boolean(element.inert || (element.parentElement && hasInertAncestor(element.parentElement)));
let app: any;
let fetchMock: ReturnType<typeof vi.fn>;

beforeEach(() => {
  document.documentElement.innerHTML = markup;
  fetchMock = vi.fn();
  vi.stubGlobal("fetch", fetchMock);
  app = new Function(`${source}; return {profileState,renderAdminUsers,bindAdminUsersInteractions,openAdminUserRoleModal,confirmAdminUserRoleChange,openAdminUserAccessModal,openAdminUserDeleteModal};`)();
  app.profileState.currentUser = { access_level: "admin" };
  app.renderAdminUsers(structuredClone(users));
  app.bindAdminUsersInteractions();
  el("profileAdminUsersSection").classList.remove("hidden");
});
afterEach(() => vi.unstubAllGlobals());

it("describes the active Super User read-only access contract", () => {
  expect(markup).toContain("Super Users have additional operational visibility and read-only access");
  expect(markup).toContain("Gets access to");
  expect(markup).toContain("Scheduler Health (view only)");
  expect(markup).toContain("Agentic Review (read only)");
  expect(markup).not.toContain("Not enabled yet");
});

it("renders dynamic roles, status and protected Admin rows without visible raw IDs", () => {
  expect(el("adminUsersRoleSummary").textContent).toContain("2 Users");
  expect(el("adminUsersRoleSummary").textContent).toContain("1 Super User");
  expect(el("adminUsersRoleSummary").textContent).toContain("2 Admins");
  expect(el("adminUsersList").textContent).not.toContain("private-id");
  expect(el("adminUsersList").textContent).toContain("Revoked");
  expect(document.querySelectorAll(".is-protected")).toHaveLength(2);
  for (const id of ["private-id-4", "private-id-5"]) {
    expect(roleButton(id)).toBeNull();
    app.openAdminUserRoleModal(id);
    app.openAdminUserAccessModal(id, false);
    app.openAdminUserDeleteModal(id);
    for (const modal of ["adminUserRoleModal", "adminUserAccessModal", "adminUserDeleteModal"]) {
      expect(el(modal).classList.contains("hidden")).toBe(true);
    }
  }
  expect(fetchMock).not.toHaveBeenCalled();
});

it("uses the existing lightweight Profile refresh icon", () => {
  const refresh = el("refreshAdminUsersBtn");
  const icon = refresh.querySelector("svg.user-access-refresh-icon")!;
  const adjacent = el("refreshPipelineRunsBtn").querySelector("svg")!;
  expect(refresh.textContent).toContain("Refresh");
  expect(icon.getAttribute("viewBox")).toBe("0 0 24 24");
  expect(Array.from(icon.querySelectorAll("path"), (path) => path.getAttribute("d"))).toEqual(
    Array.from(adjacent.querySelectorAll("path"), (path) => path.getAttribute("d")),
  );
  expect(icon.querySelectorAll('[stroke-width="1.8"]')).toHaveLength(2);
});

it("offers promotion only to authorized ordinary users", () => {
  expect(roleButton("private-id-1").textContent).toBe("Make Super User");
  expect(roleButton("private-id-2")).toBeNull();
  const revokedRow = document.querySelector('[data-admin-user-id="private-id-2"]')!;
  expect(revokedRow.textContent).toContain("Authorize user first");
  expect(revokedRow.querySelector('[data-admin-user-access="private-id-2"]')).not.toBeNull();
  app.openAdminUserRoleModal("private-id-2");
  expect(el("adminUserRoleModal").classList.contains("hidden")).toBe(true);
  expect(fetchMock).not.toHaveBeenCalled();
});

it("keeps authorization and deauthorization in the existing access confirmation", () => {
  document.querySelector<HTMLButtonElement>('[data-admin-user-access="private-id-2"]')!.click();
  expect(el("adminUserAccessTitle").textContent).toBe("Authorize user access");
  expect(el("adminUserAccessModal").classList.contains("hidden")).toBe(false);
  expect(el("adminUserRoleModal").classList.contains("hidden")).toBe(true);
  el("adminUserAccessCloseBtn").click();
  document.querySelector<HTMLButtonElement>('[data-admin-user-access="private-id-1"]')!.click();
  expect(el("adminUserAccessTitle").textContent).toBe("Revoke user access");
  expect(el("adminUserAccessMessage").textContent).toContain("revoke their active sessions");
  expect(fetchMock).not.toHaveBeenCalled();
});

it("allows an inactive Super User to open the removal confirmation", () => {
  app.renderAdminUsers([{ ...users[2], is_active: false }]);
  expect(roleButton("private-id-3").textContent).toBe("Remove Super User");
  roleButton("private-id-3").click();
  expect(el("adminUserRoleTitle").textContent).toBe("Remove Super User access?");
  expect(fetchMock).not.toHaveBeenCalled();
});

it("opens before mutation, traps focus, cancels and restores focus", () => {
  const trigger = roleButton("private-id-1");
  trigger.focus(); trigger.click();
  expect(el("adminUserRoleModal").classList.contains("hidden")).toBe(false);
  expect(document.activeElement).toBe(el("adminUserRoleCancelBtn"));
  expect(hasInertAncestor(el("profileAdminUsersSection"))).toBe(true);
  el("adminUserRoleConfirmBtn").focus();
  el("adminUserRoleConfirmBtn").dispatchEvent(new KeyboardEvent("keydown", { key: "Tab", bubbles: true, cancelable: true }));
  expect(document.activeElement).toBe(el("adminUserRoleCloseBtn"));
  el("adminUserRoleCloseBtn").dispatchEvent(new KeyboardEvent("keydown", { key: "Tab", shiftKey: true, bubbles: true, cancelable: true }));
  expect(document.activeElement).toBe(el("adminUserRoleConfirmBtn"));
  el("adminUserRoleCancelBtn").click();
  expect(document.activeElement).toBe(trigger);
  expect(hasInertAncestor(el("profileAdminUsersSection"))).toBe(false);
  expect(fetchMock).not.toHaveBeenCalled();
  trigger.click();
  el("adminUserRoleModal").dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
  expect(el("adminUserRoleModal").classList.contains("hidden")).toBe(true);
  expect(fetchMock).not.toHaveBeenCalled();
});

it.each([["private-id-1", "super_user"], ["private-id-3", "user"]])("confirms %s once, blocks duplicate submissions and updates the row", async (id, nextRole) => {
  let release!: (value: unknown) => void;
  fetchMock.mockImplementation(() => new Promise((done) => { release = done; }));
  const trigger = roleButton(id); trigger.focus(); trigger.click();
  expect(fetchMock).not.toHaveBeenCalled();
  el("adminUserRoleConfirmBtn").click();
  void app.confirmAdminUserRoleChange();
  el("adminUserRoleCancelBtn").click();
  expect(fetchMock).toHaveBeenCalledTimes(1);
  expect(el("adminUserRoleModal").getAttribute("aria-busy")).toBe("true");
  expect(el("adminUserRoleModal").classList.contains("hidden")).toBe(false);
  expect(fetchMock.mock.calls[0][0]).toBe(`/profile/admin/users/${id}/role`);
  expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({ access_level: nextRole });
  release({ ok: true, json: async () => ({ user: { ...users.find((u) => u.user_id === id), access_level: nextRole } }) });
  await flush();
  expect(el("adminUserRoleModal").classList.contains("hidden")).toBe(true);
  expect(roleButton(id).textContent).toBe(nextRole === "super_user" ? "Remove Super User" : "Make Super User");
  expect(document.activeElement).toBe(roleButton(id));
});

it("keeps failed changes in the dialog and permits retry", async () => {
  fetchMock.mockResolvedValue({ ok: false, status: 400, json: async () => ({ detail: "This account is protected." }) });
  roleButton("private-id-1").click();
  el("adminUserRoleConfirmBtn").click(); await flush();
  expect(el("adminUserRoleError").textContent).toContain("protected");
  expect(el("adminUserRoleModal").classList.contains("hidden")).toBe(false);
  expect((el("adminUserRoleConfirmBtn") as HTMLButtonElement).disabled).toBe(false);
  expect(roleButton("private-id-1").textContent).toBe("Make Super User");
});

it("keeps the heading visible in a scrollable narrow-screen dialog", () => {
  const dialog = document.querySelector<HTMLElement>(".user-role-dialog")!;
  Object.defineProperties(dialog, { scrollHeight: { value: 1100 }, clientHeight: { value: 700 } });
  dialog.scrollTop = 200;
  roleButton("private-id-1").click();
  expect(document.activeElement).toBe(el("adminUserRoleCloseBtn"));
  expect(dialog.scrollTop).toBe(0);
});

it("preserves the legacy Executive label without offering role conversion", () => {
  app.renderAdminUsers([{ ...users[0], access_level: "executive" }]);
  expect(el("adminUsersRoleSummary").textContent).toContain("1 Executive");
  expect(el("adminUsersList").textContent).toContain("Executive");
  expect(roleButton("private-id-1")).toBeNull();
  app.openAdminUserRoleModal("private-id-1");
  expect(el("adminUserRoleModal").classList.contains("hidden")).toBe(true);
  expect(fetchMock).not.toHaveBeenCalled();
});

it("keeps deletion in its separate confirmation and escapes account text", () => {
  document.querySelector<HTMLButtonElement>('[data-admin-user-delete="private-id-1"]')!.click();
  expect(el("adminUserDeleteModal").classList.contains("hidden")).toBe(false);
  expect(el("adminUserRoleModal").classList.contains("hidden")).toBe(true);
  expect(fetchMock).not.toHaveBeenCalled();
  app.renderAdminUsers([{ ...users[0], display_name: '<img src=x onerror="alert(1)">', email: "<unsafe>" }]);
  expect(el("adminUsersList").querySelector("img")).toBeNull();
  expect(el("adminUsersList").textContent).toContain("<unsafe>");
});
