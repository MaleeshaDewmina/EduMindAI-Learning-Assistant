/* Global, accessible flash messages for every EduMind AI page. */
(() => {
  "use strict";

  const durationByCategory = {
    success: 5000,
    info: 7000,
    warning: 10000,
    danger: 12000,
    error: 12000
  };
  const prefersReducedMotion = window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const notifications = document.querySelectorAll("[data-flash-notification]");
  if (!notifications.length) return;

  notifications.forEach((notification) => {
    const dismissButton = notification.querySelector("[data-dismiss-flash]");
    const category = notification.dataset.flashCategory || "info";
    let remaining = durationByCategory[category] || 7000;
    let timer = null;
    let started = 0;
    let dismissed = false;
    let hovered = false;
    let focused = false;

    const remove = () => {
      notification.remove();
      const wrapper = document.querySelector(".flash-wrapper");
      if (wrapper && !wrapper.querySelector("[data-flash-notification]")) {
        wrapper.remove();
      }
    };

    const dismiss = () => {
      if (dismissed) return;
      dismissed = true;
      window.clearTimeout(timer);
      document.removeEventListener("visibilitychange", visibilityChanged);
      notification.classList.add("is-dismissing");
      if (prefersReducedMotion) {
        remove();
      } else {
        window.setTimeout(remove, 240);
      }
    };

    const pause = () => {
      if (timer !== null) {
        window.clearTimeout(timer);
        timer = null;
        remaining = Math.max(0, remaining - (Date.now() - started));
      }
    };

    const resume = () => {
      if (dismissed || timer !== null || document.hidden || hovered || focused) return;
      started = Date.now();
      timer = window.setTimeout(() => {
        timer = null;
        dismiss();
      }, remaining);
    };

    const visibilityChanged = () => {
      if (document.hidden) pause();
      else resume();
    };

    notification.addEventListener("mouseenter", () => {
      hovered = true;
      pause();
    });
    notification.addEventListener("mouseleave", () => {
      hovered = false;
      resume();
    });
    notification.addEventListener("focusin", () => {
      focused = true;
      pause();
    });
    notification.addEventListener("focusout", () => {
      focused = notification.contains(document.activeElement);
      resume();
    });
    if (dismissButton) dismissButton.addEventListener("click", dismiss);
    document.addEventListener("visibilitychange", visibilityChanged);
    resume();
  });
})();
