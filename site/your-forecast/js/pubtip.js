// The published map's tooltip on "Your forecast": it copies the ward's
// data-tip attribute, which the number scan has read (the MAP generated
// region), and writes no figure of its own. The map under a reader's settings
// has its own, in js/model.js (region "wardtip").
import { placeTip } from "./tip.js";

const tip = document.querySelector(".pl-pubtip");
function show(e) {
  const t = e.target.getAttribute && e.target.getAttribute("data-tip");
  if (!t) { tip.hidden = true; return; }
  tip.textContent = t;
  tip.hidden = false;
  placeTip(tip, e.clientX, e.clientY);
}
if (tip) {
  document.addEventListener("mousemove", show);
  document.addEventListener("click", show);
}
