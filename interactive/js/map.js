// The ward map: the geographic map the live site draws (rotated north to the
// right) and the equal-sized-ward hex cartogram, from the same geometry.
//
// Accessible as one composite widget: a single tab stop, arrow keys move
// between neighbouring wards (by cartogram position, in both views), Enter or
// Space paints the current ward with the chosen party, Delete clears it.
// Mouse and pen paint by dragging; touch paints by tapping, so a finger can
// still scroll and pinch the map.

const NS = "http://www.w3.org/2000/svg";

export function hexPoints([cx, cy], r) {
  const pts = [];
  for (let k = 0; k < 6; k++) {
    const a = Math.PI / 180 * (60 * k - 90);
    pts.push((cx + r * Math.cos(a)).toFixed(1) + "," + (cy + r * Math.sin(a)).toFixed(1));
  }
  return pts.join(" ");
}

export class WardMap {
  constructor(svg, geom, { byCode, readonly = false, onPaint = null, onFocusWard = null } = {}) {
    this.svg = svg; this.geom = geom; this.byCode = byCode;
    this.readonly = readonly; this.onPaint = onPaint; this.onFocusWard = onFocusWard;
    this.mode = "geo"; this.calls = new Array(geom.wards.length).fill(null);
    this.cur = 0; this.painting = false;
    svg.setAttribute("viewBox", "0 0 " + geom.W + " " + Math.ceil(geom.H));
    svg.classList.toggle("readonly", readonly);
    this.draw();
    if (!readonly) this.wire();
  }

  setMode(mode) { this.mode = mode; this.draw(); }
  setCalls(calls) { this.calls = calls.slice(); this.refresh(); }
  // Each ward's strength, 0 to 1, as its fill-opacity, in ward order; null
  // draws every ward at full strength. The analysis map (js/make.js) passes
  // our chance for the reader's call in each ward.
  setShade(shade) { this.shade = shade ? shade.slice() : null; this.refresh(); }

  label(i) {
    const c = this.calls[i];
    return "Ward " + this.geom.wards[i].id + ", " + this.geom.wards[i].sector + ": " +
      (c ? this.byCode[c].name : "not called yet");
  }

  draw() {
    const { svg, geom } = this;
    svg.textContent = "";
    const g = document.createElementNS(NS, "g");
    this.els = geom.wards.map((w, i) => {
      let el;
      if (this.mode === "hex") {
        el = document.createElementNS(NS, "polygon");
        el.setAttribute("points", hexPoints(w.hex, geom.hex_radius * 0.96));
      } else {
        el = document.createElementNS(NS, "path");
        el.setAttribute("d", w.path);
      }
      el.setAttribute("class", "w");
      el.dataset.i = i;
      if (!this.readonly) {
        el.setAttribute("tabindex", i === this.cur ? "0" : "-1");
        el.setAttribute("role", "button");
      }
      g.appendChild(el);
      return el;
    });
    svg.appendChild(g);
    if (this.mode === "geo") {
      const lg = document.createElementNS(NS, "g");
      lg.setAttribute("aria-hidden", "true");
      for (const l of geom.labels) {
        const t = document.createElementNS(NS, "text");
        t.setAttribute("x", l.x); t.setAttribute("y", l.y);
        t.setAttribute("text-anchor", "middle"); t.setAttribute("class", "lbl");
        t.textContent = l.t; lg.appendChild(t);
      }
      svg.appendChild(lg);
    }
    this.refresh();
  }

  refresh() {
    this.els.forEach((el, i) => {
      const c = this.calls[i];
      el.classList.toggle("empty", !c);
      // the party's colour as a presentation attribute; an empty ward takes
      // css/interactive.css's .w.empty fill
      if (c) el.setAttribute("fill", this.byCode[c].colour);
      else el.removeAttribute("fill");
      if (this.shade && this.shade[i] != null) el.setAttribute("fill-opacity", String(this.shade[i]));
      else el.removeAttribute("fill-opacity");
      if (!this.readonly) el.setAttribute("aria-label", this.label(i));
      else {
        let t = el.querySelector("title");
        if (!t) { t = document.createElementNS(NS, "title"); el.appendChild(t); }
        t.textContent = this.label(i);
      }
    });
  }

  paint(i) {
    if (this.readonly || !this.onPaint) return;
    this.onPaint(i);
  }

  focus(i) {
    this.els[this.cur].setAttribute("tabindex", "-1");
    this.els[this.cur].classList.remove("cur");
    this.cur = i;
    const el = this.els[i];
    el.setAttribute("tabindex", "0");
    el.classList.add("cur");
    el.focus({ preventScroll: false });
    this.onFocusWard?.(i);
  }

  neighbour(i, dx, dy) {
    const [x0, y0] = this.geom.wards[i].hex;
    let best = -1, bestScore = Infinity;
    this.geom.wards.forEach((w, j) => {
      if (j === i) return;
      const vx = w.hex[0] - x0, vy = w.hex[1] - y0;
      const along = vx * dx + vy * dy;
      if (along <= 1) return;
      const across = Math.abs(vx * dy - vy * dx);
      const score = along + across * 2.2;
      if (score < bestScore) { bestScore = score; best = j; }
    });
    return best < 0 ? i : best;
  }

  wire() {
    const svg = this.svg;
    const idx = e => {
      const t = e.target.closest?.(".w");
      return t ? +t.dataset.i : -1;
    };
    svg.addEventListener("pointerdown", e => {
      const i = idx(e); if (i < 0) return;
      if (e.pointerType === "touch") { this.touchStart = [e.clientX, e.clientY, i]; return; }
      this.painting = true; this.focus(i); this.paint(i);
      e.preventDefault();
    });
    svg.addEventListener("pointerover", e => {
      if (!this.painting) return;
      const i = idx(e); if (i >= 0) this.paint(i);
    });
    window.addEventListener("pointerup", e => {
      this.painting = false;
      if (e.pointerType === "touch" && this.touchStart) {
        const [x, y, i] = this.touchStart; this.touchStart = null;
        if (Math.hypot(e.clientX - x, e.clientY - y) < 10 && idx(e) === i) { this.focus(i); this.paint(i); }
      }
    });
    svg.addEventListener("pointercancel", () => { this.touchStart = null; this.painting = false; });
    svg.addEventListener("keydown", e => {
      const i = this.cur;
      const dirs = { ArrowRight: [1, 0], ArrowLeft: [-1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] };
      if (dirs[e.key]) { e.preventDefault(); this.focus(this.neighbour(i, ...dirs[e.key])); }
      else if (e.key === "Home") { e.preventDefault(); this.focus(0); }
      else if (e.key === "End") { e.preventDefault(); this.focus(this.els.length - 1); }
      else if (e.key === "Enter" || e.key === " ") { e.preventDefault(); this.paint(i); }
      else if (e.key === "Delete" || e.key === "Backspace") {
        e.preventDefault(); this.onClear?.(i);
      }
    });
    svg.addEventListener("focusin", e => {
      const i = idx(e); if (i >= 0 && i !== this.cur) this.focus(i);
      else if (i >= 0) this.els[i].classList.add("cur");
    });
    svg.addEventListener("focusout", () => this.els[this.cur]?.classList.remove("cur"));
  }
}
