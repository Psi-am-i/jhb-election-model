// Where a floating tooltip goes: beside the pointer (or a focused ward), kept
// inside the window. ONE DEFINITION for the page's three tooltips: the
// published map's (pubtip.js), section 1's (model.js "wardtip") and section
// 2's (make.js "b-wardtip").
//
// A NON-writer (stats.script_writes): it moves the element it is handed and
// writes no text.

const OFFSET = 14, WIDTH = 290;

export function placeTip(tip, x, y) {
  tip.style.left = Math.max(4, Math.min(x + OFFSET, window.innerWidth - WIDTH)) + "px";
  tip.style.top = (y + OFFSET) + "px";
}
