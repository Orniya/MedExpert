(function () {
  const root = document.documentElement;
  const toggleBtn = document.getElementById("theme-toggle");
  function debugLog(payload) {
    // #region agent log
    fetch("/_debug/client-log", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).catch(() => {});
    fetch("http://127.0.0.1:7259/ingest/57fa0c5d-e67f-4a5e-9280-52ed5e7082e8", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "42d9a8" },
      body: JSON.stringify(payload),
    })
      .catch(() => {});
    // #endregion
  }

  function setTheme(theme) {
    // #region agent log
    debugLog({sessionId:'42d9a8',runId:'run1',hypothesisId:'H2',location:'static/js/app.js:22',message:'setTheme called',data:{theme:theme,path:window.location.pathname},timestamp:Date.now()});
    // #endregion
    root.setAttribute("data-theme", theme);
    localStorage.setItem("medexpert-theme", theme);
    if (toggleBtn) {
      toggleBtn.textContent = theme === "dark" ? "Light Mode" : "Dark Mode";
    }
  }

  if (toggleBtn) {
    const currentTheme = root.getAttribute("data-theme") || "light";
    // #region agent log
    debugLog({sessionId:'42d9a8',runId:'run1',hypothesisId:'H3',location:'static/js/app.js:33',message:'toggle present init',data:{currentTheme:currentTheme,path:window.location.pathname,hasReportClass:document.body.classList.contains('report-page')},timestamp:Date.now()});
    // #endregion
    setTheme(currentTheme);
    toggleBtn.addEventListener("click", function () {
      const now = root.getAttribute("data-theme") || "light";
      setTheme(now === "dark" ? "light" : "dark");
    });
  }

  const input = document.getElementById("symptom-filter");
  // #region agent log
  if (document.body.classList.contains("report-page")) {
    const cs = getComputedStyle(document.body);
    debugLog({sessionId:'42d9a8',runId:'run1',hypothesisId:'H4',location:'static/js/app.js:47',message:'report page computed theme sample',data:{rootTheme:root.getAttribute('data-theme'),bodyClass:document.body.className,bgVar:cs.getPropertyValue('--bg').trim(),cardVar:cs.getPropertyValue('--bg-elevated').trim()},timestamp:Date.now()});
  }
  // #endregion
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
