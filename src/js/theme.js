// The light/dark theme, loaded in <head> WITHOUT defer so the palette is set
// before first paint (src/css/tokens.css says which case wins).
//
//   1. a reader who has chosen: data-theme from localStorage;
//   2. a reader who has not: the operating system's preference, written onto
//      the element so the toggle and every [data-theme] rule read one thing
//      (without it the icon offers to switch to the theme already showing).
//
// The toggle (build_site.nav_for's .themetoggle) is wired by delegation,
// because this runs before the nav exists. It always writes an explicit value:
// an absent attribute means "ask the OS".
(function () {
  var t = null;
  try { t = localStorage.getItem("theme"); } catch (e) {}
  if (t !== "light" && t !== "dark") {
    t = (window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches)
      ? "light" : "dark";
  }
  document.documentElement.setAttribute("data-theme", t);
  document.addEventListener("click", function (e) {
    var b = e.target.closest && e.target.closest(".themetoggle");
    if (!b) return;
    var root = document.documentElement;
    var light = root.getAttribute("data-theme") !== "light";
    root.setAttribute("data-theme", light ? "light" : "dark");
    try { localStorage.setItem("theme", light ? "light" : "dark"); } catch (e2) {}
  });
})();
