/* Open and focus the search with Ctrl+K or Cmd+K. */
(function () {
  if (window.__hbHotkey) return;
  window.__hbHotkey = true;

  document.addEventListener("keydown", function (event) {
    if (event.key.toLowerCase() !== "k" || !(event.ctrlKey || event.metaKey)) return;
    if (event.altKey || event.shiftKey) return;
    var query = document.querySelector('[data-md-component="search-query"]');
    if (!query) return;
    event.preventDefault();
    var toggle = document.querySelector('[data-md-toggle="search"]');
    if (toggle && !toggle.checked) {
      toggle.checked = true;
      toggle.dispatchEvent(new Event("change"));
    }
    query.focus();
    query.select();
  });

  function labelKeys() {
    var isMac = /Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent);
    document.querySelectorAll(".hb-kbd").forEach(function (el) {
      el.textContent = isMac ? "⌘ K" : "Ctrl K";
    });
  }
  if (typeof document$ !== "undefined") document$.subscribe(labelKeys);
  else labelKeys();
})();
