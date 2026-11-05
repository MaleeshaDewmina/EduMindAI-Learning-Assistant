document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-toggle-password]").forEach((button) => {
    const field = document.getElementById(button.dataset.togglePassword);
    if (!field) return;
    button.addEventListener("click", () => {
      const visible = field.type === "password";
      field.type = visible ? "text" : "password";
      button.textContent = visible ? "Hide" : "Show";
      button.setAttribute("aria-label", visible ? "Hide password" : "Show password");
      button.setAttribute("aria-pressed", visible ? "true" : "false");
    });
  });
});
