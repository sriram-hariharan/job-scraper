function qs(id) {
  return document.getElementById(id);
}

window.addEventListener("DOMContentLoaded", () => {
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