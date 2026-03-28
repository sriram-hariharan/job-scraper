const APP_SHELL_COLLAPSED_KEY = "job_stack_app_shell_collapsed";

function qs(id) {
  return document.getElementById(id);
}

function setShellCollapsed(isCollapsed, { persist = true } = {}) {
  document.body.classList.toggle("app-shell-collapsed", isCollapsed);

  const menuBtn = qs("appShellMenuBtn");
  if (menuBtn) {
    menuBtn.setAttribute("aria-pressed", isCollapsed ? "true" : "false");
  }

  if (persist) {
    window.localStorage.setItem(APP_SHELL_COLLAPSED_KEY, isCollapsed ? "true" : "false");
  }
}

window.addEventListener("DOMContentLoaded", () => {
  const menuBtn = qs("appShellMenuBtn");

  const saved = window.localStorage.getItem(APP_SHELL_COLLAPSED_KEY);
  const defaultCollapsed = saved === null ? window.innerWidth < 1220 : saved === "true";
  setShellCollapsed(defaultCollapsed, { persist: false });

  if (menuBtn) {
    menuBtn.addEventListener("click", (event) => {
      event.preventDefault();
      const next = !document.body.classList.contains("app-shell-collapsed");
      setShellCollapsed(next);
    });
  }

  const menuShell = qs("profileMenuShell");
  const menuButton = qs("profileMenuButton");
  const dropdown = qs("profileDropdown");

  if (!menuShell || !menuButton || !dropdown) return;

  function closeMenu() {
    dropdown.classList.add("hidden");
    menuButton.setAttribute("aria-expanded", "false");
  }

  function openMenu() {
    dropdown.classList.remove("hidden");
    menuButton.setAttribute("aria-expanded", "true");
  }

  menuButton.addEventListener("click", (event) => {
    event.stopPropagation();
    const isHidden = dropdown.classList.contains("hidden");
    if (isHidden) {
      openMenu();
    } else {
      closeMenu();
    }
  });

  document.addEventListener("click", (event) => {
    if (!menuShell.contains(event.target)) {
      closeMenu();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeMenu();
    }
  });
});