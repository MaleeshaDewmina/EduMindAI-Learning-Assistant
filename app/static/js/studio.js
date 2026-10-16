/* Mobile-first navigation, focus management and progressive enhancement. */
(() => {
  "use strict";
  const open = document.querySelector("[data-open-sidebar]");
  const overlay = document.querySelector(".sidebar-overlay");
  const sidebar = document.querySelector("#app-sidebar");
  if (!open || !overlay || !sidebar) return;
  const close = () => {
    document.body.classList.remove("sidebar-open");
    open.setAttribute("aria-expanded", "false");
    overlay.hidden = true;
    open.focus();
  };
  open.addEventListener("click", () => {
    document.body.classList.add("sidebar-open");
    overlay.hidden = false;
    open.setAttribute("aria-expanded", "true");
    sidebar.querySelector("a")?.focus();
  });
  document.querySelectorAll("[data-close-sidebar]").forEach(button => button.addEventListener("click", close));
  document.addEventListener("keydown", event => {
    if (event.key === "Escape" && document.body.classList.contains("sidebar-open")) close();
  });
  sidebar.querySelectorAll("nav a").forEach(link => link.addEventListener("click", () => {
    document.body.classList.remove("sidebar-open");
    overlay.hidden = true;
    open.setAttribute("aria-expanded", "false");
  }));
})();
