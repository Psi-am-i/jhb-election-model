// A figure's provenance pop-over (src/css/stat.css) near the right or bottom
// edge of the window flips so it stays visible. It only toggles a class; it
// writes no text or figure.
document.addEventListener("mouseover", function (e) {
  var s = e.target.closest && e.target.closest(".mstat");
  if (!s) return;
  var r = s.getBoundingClientRect();
  var w = document.documentElement.clientWidth, h = document.documentElement.clientHeight;
  s.classList.toggle("tip-left", r.left + 316 > w);
  s.classList.toggle("tip-up", r.bottom + 96 > h);
});
