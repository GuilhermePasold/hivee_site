window.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".alert").forEach((alert) => {
    window.setTimeout(() => {
      alert.classList.add("is-hiding");
      window.setTimeout(() => alert.remove(), 250);
    }, 4000);
  });

  document.querySelectorAll("[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      const message = form.getAttribute("data-confirm");
      if (message && !window.confirm(message)) {
        event.preventDefault();
      }
    });
  });
});
