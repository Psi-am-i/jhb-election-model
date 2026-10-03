// The published map's tooltip on "play with the model": it copies the ward's
// data-tip attribute, which the number scan has read (the MAP generated
// region), and writes no figure of its own. The map under a reader's settings
// has its own, in js/model.js (region "wardtip").
(function () {
  var tip = document.querySelector(".pl-pubtip");
  if (!tip) return;
  function show(e) {
    var t = e.target.getAttribute && e.target.getAttribute("data-tip");
    if (!t) { tip.hidden = true; return; }
    tip.textContent = t; tip.hidden = false;
    tip.style.left = Math.min(e.clientX + 14, window.innerWidth - 290) + "px";
    tip.style.top = (e.clientY + 14) + "px";
  }
  document.addEventListener("mousemove", show);
  document.addEventListener("click", show);
})();
