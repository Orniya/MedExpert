(function () {
  const root = document.documentElement;
  const toggleBtn = document.getElementById("theme-toggle");

  function setTheme(theme) {
    root.setAttribute("data-theme", theme);
    localStorage.setItem("medexpert-theme", theme);
    if (toggleBtn) {
      toggleBtn.textContent = theme === "dark" ? "Light Mode" : "Dark Mode";
    }
  }

  if (toggleBtn) {
    const currentTheme = root.getAttribute("data-theme") || "light";
    setTheme(currentTheme);
    toggleBtn.addEventListener("click", function () {
      const now = root.getAttribute("data-theme") || "light";
      setTheme(now === "dark" ? "light" : "dark");
    });
  }

  const input = document.getElementById("symptom-filter");
  if (!input) return;

  const items = Array.from(document.querySelectorAll(".symptom-item"));
  const groups = Array.from(document.querySelectorAll(".symptom-group"));

  function applyFilter() {
    const q = input.value.trim().toLowerCase();
    items.forEach((item) => {
      const text = item.getAttribute("data-label") || "";
      item.style.display = !q || text.includes(q) ? "" : "none";
    });

    groups.forEach((group) => {
      const visibleCount = group.querySelectorAll('.symptom-item:not([style*="display: none"])').length;
      group.style.display = visibleCount > 0 ? "" : "none";
    });
  }

  input.addEventListener("input", applyFilter);
})();
