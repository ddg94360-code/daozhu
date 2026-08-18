(function () {
  const KEY = "daozhu.theme";
  const THEMES = ["daoist", "confucian", "legalist", "strategist", "taiji"];
  const DEFAULT = "daoist";

  function read() {
    try {
      const v = localStorage.getItem(KEY);
      return THEMES.includes(v) ? v : DEFAULT;
    } catch (_) {
      return DEFAULT;
    }
  }

  function apply(theme) {
    const next = THEMES.includes(theme) ? theme : DEFAULT;
    document.documentElement.setAttribute("data-theme", next);
    const sel = document.getElementById("theme-select");
    if (sel && sel.value !== next) sel.value = next;
  }

  function save(theme) {
    const next = THEMES.includes(theme) ? theme : DEFAULT;
    try { localStorage.setItem(KEY, next); } catch (_) { /* ignore quota / private */ }
    apply(next);
  }

  apply(read());
  document.addEventListener("DOMContentLoaded", function () {
    apply(read());
    const sel = document.getElementById("theme-select");
    if (!sel) return;
    sel.addEventListener("change", function () { save(sel.value); });
  });
})();
