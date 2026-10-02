// "Make your own forecast": the page. The reader calls every ward, sets each
// party's share of the combined vote and picks who governs; the seats come
// from the project's own seat code, run in the browser (js/make-worker.js).
//
// ⛔ A LIVE WRITER (stats.LIVE_WRITERS["make/js/make.js"]) for the regions
// "status", "map", "vote", "govern" and "council". The build refuses the page
// (stats.script_writes) unless this file keeps the writer contract:
//   * it reaches the page ONLY through literal '[data-live="<name>"] …'
//     selectors, each for a region listed for it, all taken once, below;
//   * it writes with textContent, createElement and append; never markup;
//   * it does not walk out of a region and writes nothing through an event's
//     target.
// Its imports: builder-state.js, make-state.js and map.js are scanned as
// NON-writers; make-share.js (region "share") is a writer in its own right.
//
// DESIGN-decided §8: every control applies to every party identically. Parties
// are listed alphabetically wherever a reader chooses; nothing is preselected.
// §14: the builder can only hold a valid forecast (js/builder-state.js); seats
// are recomputed after every edit by the seat code the server would run.
//
// The start (src/build_make.py, make/forecast.json): each ward's modal winner
// over the published draws, and each party's median LIST-ballot share,
// renormalised; the model publishes no combined share. The reader's forecast
// lives only in the address (js/make-state.js).

import * as B from "./builder-state.js";
import * as MS from "./make-state.js";
import { WardMap } from "./map.js";
import { setShareable, onNameChange } from "./make-share.js";

const one = {
  status: document.querySelector('[data-live="status"] .ess'),
  linknote: document.querySelector('[data-live="status"] .linknote'),
  mapRegion: document.querySelector('[data-live="map"]'),
  svg: document.querySelector('[data-live="map"] svg'),
  mapscroll: document.querySelector('[data-live="map"] .mapscroll'),
  listview: document.querySelector('[data-live="map"] .listview'),
  nchanged: document.querySelector('[data-live="map"] .nchanged'),
  hint: document.querySelector('[data-live="map"] .painthint'),
  brush: document.querySelector('[data-live="map"] .brushscroll'),
  brushselect: document.querySelector('[data-live="map"] .brushselect'),
  area: document.querySelector('[data-live="map"] .area'),
  fillarea: document.querySelector('[data-live="map"] .fillarea'),
  copymodel: document.querySelector('[data-live="map"] .copymodel'),
  undo: document.querySelector('[data-live="map"] .undo'),
  voteRegion: document.querySelector('[data-live="vote"]'),
  prmodel: document.querySelector('[data-live="vote"] .prmodel'),
  prfind: document.querySelector('[data-live="vote"] .prfind'),
  floornote: document.querySelector('[data-live="vote"] .floornote'),
  prlist: document.querySelector('[data-live="vote"] .prlist'),
  govRegion: document.querySelector('[data-live="govern"]'),
  coal: document.querySelector('[data-live="govern"] .coal'),
  coalstat: document.querySelector('[data-live="govern"] .coalstat'),
  restate: document.querySelector('[data-live="council"] .restate'),
  bars: document.querySelector('[data-live="council"] .bars'),
  strip: document.querySelector('[data-live="council"] .strip'),
  capseats: document.querySelector('[data-live="council"] .capseats'),
  capmaj: document.querySelector('[data-live="council"] .capmaj'),
  excess: document.querySelector('[data-live="council"] .excess'),
  announce: document.querySelector('[data-live="council"] .announce'),
};
const views = document.querySelectorAll('[data-live="map"] .views button');

// A new element: properties, attributes (keys with a dash) and children.
function el(tag, props = {}, ...kids) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (v == null || v === false) continue;
    if (k === "style") e.style.cssText = v;
    else if (k.includes("-") || k === "role") e.setAttribute(k, v === true ? "" : String(v));
    else e[k] = v;
  }
  e.append(...kids.filter(k => k != null && k !== false));
  return e;
}
const sw = colour => el("span", { className: "sw", style: "background:" + colour, "aria-hidden": "true" });

// ---------- the published start ----------
let D;
try {
  const r = await fetch(new URL("../forecast.json", import.meta.url));
  if (!r.ok) throw new Error("HTTP " + r.status);
  D = await r.json();
} catch (e) {
  one.status.textContent = "The published start could not be loaded (" + (e.message || e) + "). Reload to try again.";
  throw e;
}
const schema = D.schema, geom = D.geometry;
const ctx = B.contextOf(schema);
const byCode = Object.fromEntries(schema["x-parties"].map(p => [p.code, p]));
const name = c => byCode[c].name;
const alpha = ctx.codes.slice().sort((a, b) => name(a).localeCompare(name(b)));
const startCalls = D.start.ward_calls;
const start = B.startState(ctx, { calls: startCalls, share: D.start.combined_share }, startCalls).state;
if (geom.wards.map(w => String(w.id)).join() !== ctx.wards.join()) throw new Error("the geometry and the schema disagree about the wards");

const opened = MS.parse(location.search, ctx, D.context_ref, start);
let state = opened.state;
const S = { coalition: opened.coalition.slice(), name: opened.name, brush: null };
if (opened.note) { one.linknote.textContent = opened.note; one.linknote.hidden = false; }
const history = new B.History();

const pct = (v, dp = 1) => {
  const p = v / ctx.T * 100;
  return p > 0 && p < 0.05 ? "under 0.1" : p.toFixed(dp);
};

// ---------- locking: the controls answer once the seat law has loaded ----------
const editables = [one.brushselect, one.area, one.fillarea, one.copymodel, one.prmodel];
let engineReady = false;
function lock(on) {
  for (const r of [one.mapRegion, one.voteRegion, one.govRegion]) r.classList.toggle("locked", on);
  for (const e of editables) e.disabled = on;
}

// ---------- map ----------
const map = new WardMap(one.svg, geom, { byCode, onPaint: paintWard });
map.onClear = () => { one.hint.textContent = "Every ward needs a winner. Choose a party, then tap the ward to change it."; };

function snapshot() { history.push(state); one.undo.disabled = false; }
let strokeOpen = false;
function paintWard(i) {
  if (!engineReady) return;
  if (!S.brush) { one.hint.textContent = "Choose a party first, then tap the ward."; return; }
  if (state.calls[i] === S.brush) return;
  if (!strokeOpen) { snapshot(); strokeOpen = true; }
  const r = B.assignWards(state, ctx, [i], S.brush);
  commit(r.state, raisedNote(r.raised));
}
window.addEventListener("pointerup", () => { strokeOpen = false; });
one.svg.addEventListener("keyup", () => { strokeOpen = false; });

function raisedNote(raised) {
  if (!raised.length) return "";
  return raised.map(name).join(", ") + (raised.length === 1 ? " had no votes and now wins a ward, so it was" : " had no votes and now win wards, so each was") +
    " given one vote. A party that wins a ward must have votes.";
}
function setCallsFrom(calls) {
  snapshot();
  const r = B.setCalls(state, ctx, calls);
  commit(r.state, raisedNote(r.raised));
}

// The brush: a chip for each party that wins a ward on the reader's map, the
// same rule for every party, and every party in the select.
one.brushselect.append(el("option", { value: "" }, "Choose…"), ...alpha.map(c => el("option", { value: c }, name(c))));
one.brushselect.addEventListener("change", () => chooseBrush(one.brushselect.value || null));
function chooseBrush(c) {
  S.brush = c;
  one.brushselect.value = c || "";
  for (const b of one.brush.children) b.setAttribute("aria-pressed", String(b.value === c));
  one.hint.textContent = c ? "Giving wards to " + name(c) + ". Tap or drag across wards." : "Choose a party, then tap or drag across wards to give them to it.";
}
function paintBrush() {
  const held = new Set(state.calls);
  if (S.brush) held.add(S.brush);
  one.brush.replaceChildren(...alpha.filter(c => held.has(c)).map(c => {
    const b = el("button", { type: "button", className: "chip", value: c, "aria-pressed": String(c === S.brush), disabled: !engineReady }, sw(byCode[c].colour), name(c));
    b.addEventListener("click", () => chooseBrush(S.brush === c ? null : c));
    return b;
  }));
}

for (const b of views) b.addEventListener("click", () => {
  const v = b.dataset.view;
  for (const x of views) x.setAttribute("aria-pressed", String(x === b));
  one.mapscroll.hidden = v === "list";
  one.listview.hidden = v !== "list";
  if (v === "list") buildList(); else map.setMode(v);
});

function buildList() {
  const opts = () => alpha.map(c => el("option", { value: c }, name(c)));
  const sets = ["north", "east", "south", "west", "central"].map(sec => {
    const fs = el("fieldset", {}, el("legend", {}, sec));
    geom.wards.forEach((w, i) => {
      if (w.sector !== sec) return;
      const s = el("select", { id: "wl" + i, disabled: !engineReady }, ...opts());
      s.value = state.calls[i];
      s.addEventListener("change", () => {
        snapshot();
        const r = B.assignWards(state, ctx, [i], s.value);
        commit(r.state, raisedNote(r.raised));
      });
      fs.append(el("div", { className: "wl" }, el("label", { htmlFor: "wl" + i }, "Ward " + w.id), s));
    });
    return fs;
  });
  one.listview.replaceChildren(el("div", { className: "wardlist" }, ...sets));
}

one.fillarea.addEventListener("click", () => {
  if (!S.brush) { one.hint.textContent = "Choose a party first, then fill the area."; return; }
  const sec = one.area.value;
  setCallsFrom(state.calls.map((c, i) => geom.wards[i].sector === sec ? S.brush : c));
});
one.copymodel.addEventListener("click", () => setCallsFrom(startCalls));
one.undo.addEventListener("click", () => {
  const prev = history.pop(); if (!prev) return;
  commit(prev);
});

// ---------- the vote: one identical row per party ----------
const rows = {};
for (const c of alpha) {
  const num = el("input", { type: "number", id: "pr-n-" + c, min: "0", max: "100", step: "0.1", inputMode: "decimal", disabled: true });
  const rng = el("input", { type: "range", min: "0", max: "100", step: "0.1", disabled: true, "aria-label": name(c) + ", share of all votes, percent" });
  const fl = el("span", { className: "fl" });
  const row = el("div", { className: "prrow" }, sw(byCode[c].colour), el("label", { htmlFor: "pr-n-" + c }, name(c)), num, fl, rng);
  num.addEventListener("change", () => editShare(c, num.value, true, null));
  rng.addEventListener("input", () => editShare(c, rng.value, false, rng));
  rng.addEventListener("change", () => editShare(c, rng.value, true, null));
  rows[c] = { row, num, rng, fl };
  editables.push(num, rng);
  one.prlist.append(row);
}
one.prfind.addEventListener("input", () => {
  const q = one.prfind.value.trim().toLowerCase();
  for (const c of alpha) rows[c].row.hidden = !!q && !name(c).toLowerCase().includes(q);
});

function paintShares(except = null) {
  const floors = B.floorsOf(state.calls, ctx);
  for (const c of alpha) {
    const v = state.votes[c], r = rows[c], p = v / ctx.T * 100;
    if (r.num !== except) r.num.value = p.toFixed(1);
    if (r.rng !== except) r.rng.value = p.toFixed(1);
    r.rng.setAttribute("aria-valuetext", pct(v) + " percent");
    r.fl.textContent = floors[c] && v === floors[c] ? "One vote: the least a ward winner may have." : "";
  }
}
let openEdit = null;
function editShare(c, raw, final, active) {
  if (!engineReady) return;
  const want = parseFloat(raw);
  if (!Number.isFinite(want)) { if (final) paintShares(); return; }
  if (openEdit !== c) { snapshot(); openEdit = c; }
  if (final) openEdit = null;
  const r = B.setPercent(state, ctx, c, want);
  let note = "";
  if (r.clamped === "floor") {
    const held = state.calls.filter(x => x === c).length;
    note = name(c) + " wins " + held + (held === 1 ? " ward" : " wards") + " on your map, so it keeps at least one vote. Give its wards to other parties to take it to zero.";
  } else if (r.clamped === "ceiling") {
    note = name(c) + " is at the most it can have: every other party that wins a ward keeps at least one vote.";
  }
  state = r.state;
  one.floornote.textContent = note;
  afterEdit(final ? null : active);
}
one.prmodel.addEventListener("click", () => {
  snapshot();
  const r = B.setCalls({ calls: state.calls, votes: B.votesFromPercent(D.start.combined_share, ctx) }, ctx, state.calls);
  commit(r.state, raisedNote(r.raised));
});

// ---------- recompute ----------
const worker = new Worker(new URL("./make-worker.js", import.meta.url), { type: "module" });
let seq = 0, result = null;

function commit(next, note = "") {
  state = next;
  one.floornote.textContent = note;
  afterEdit();
}

function afterEdit(active = null) {
  const bad = B.invariantErrors(state, ctx);
  if (bad.length) throw new Error("the builder reached an invalid state: " + bad.join("; "));
  map.setCalls(state.calls);
  if (!one.listview.hidden) buildList();
  paintShares(active);
  paintBrush();
  one.undo.disabled = !engineReady || !history.size;
  const changed = state.calls.filter((c, i) => c !== startCalls[i]).length;
  one.nchanged.textContent = changed ? changed + (changed === 1 ? " changed from the model's call" : " changed from the model's calls") : "as the model calls them";
  writeURL();
  if (engineReady) worker.postMessage({ type: "seats", seq: ++seq, forecast: B.forecastBody(state, ctx) });
}

function writeURL() {
  const q = MS.serialize({ state, coalition: S.coalition, name: S.name }, ctx, D.context_ref, start);
  window.history.replaceState(null, "", location.pathname + q + location.hash);
  if (result) share();
}

// ---------- coalition ----------
function paintCoalition() {
  const seats = result.seats;
  const shown = alpha.filter(c => seats[c] || S.coalition.includes(c));
  one.coal.replaceChildren(...shown.map(c => {
    const b = el("button", { type: "button", className: "chip", "aria-pressed": String(S.coalition.includes(c)) },
      sw(byCode[c].colour), name(c) + " ", el("span", { style: "color:var(--ink-3)" }, String(seats[c] || 0)));
    b.addEventListener("click", () => {
      S.coalition = S.coalition.includes(c) ? S.coalition.filter(x => x !== c) : [...S.coalition, c];
      writeURL();
      paintCoalition();
    });
    return b;
  }));
  const cs = S.coalition.reduce((a, c) => a + (seats[c] || 0), 0);
  const { council_total: council, majority } = result;
  if (!S.coalition.length) one.coalstat.textContent = "No party chosen. A council of " + council + " needs " + majority + " votes to elect a mayor and pass a budget.";
  else if (cs >= majority) one.coalstat.replaceChildren(cs + " of " + council + " seats. ", el("span", { className: "ok" }, "Enough to govern."));
  else one.coalstat.replaceChildren(cs + " of " + council + " seats. ", el("span", { className: "no" }, (majority - cs) + " short of the " + majority + " needed."));
}

// ---------- the council ----------
function order(seats) {
  return Object.keys(seats).filter(c => seats[c] > 0).sort((a, b) => seats[b] - seats[a] || name(a).localeCompare(name(b)));
}
function paintCouncil() {
  const { seats, ward, council_total: council, majority, excessive } = result;
  const list = order(seats);
  const max = Math.max(1, ...list.map(c => seats[c]));
  one.restate.textContent = "Each party's wards plus its list seats, of " + council + ".";
  one.bars.replaceChildren(...list.map(c => el("div", { className: "bar" },
    el("span", { className: "nm" }, name(c)),
    el("span", { className: "tr" }, el("span", { className: "fl", style: "width:" + (seats[c] / max * 100) + "%;background:" + byCode[c].colour })),
    el("span", { className: "v", title: (ward[c] || 0) + " wards, " + (seats[c] - (ward[c] || 0)) + " list" }, String(seats[c])))));
  one.strip.replaceChildren(...list.map(c => el("span", { style: "width:" + (seats[c] / council * 100) + "%;background:" + byCode[c].colour })),
    el("span", { className: "maj", style: "left:calc(" + ((majority - 0.5) / council) + " * 100%)" }));
  one.capseats.textContent = council + " seats";
  one.capmaj.textContent = majority + " to govern";
  const over = Object.keys(excessive || {});
  one.excess.textContent = over.length
    ? over.map(name).join(", ") + (over.length === 1 ? " wins" : " win") + " at least as many wards as " + (over.length === 1 ? "its" : "their") +
      " share of the vote earns, so " + (over.length === 1 ? "it keeps its wards" : "they keep their wards") + " and the list seats go to the others."
    : "";
  const top = list.slice(0, 5).map(c => name(c) + " " + seats[c]).join(", ");
  if (one.announce.textContent !== top) one.announce.textContent = top;
}

function share() {
  setShareable({
    url: location.href, name: S.name, calls: state.calls, seats: result.seats,
    council: result.council_total, majority: result.majority, coalition: S.coalition, geom, party: c => byCode[c],
  });
}
onNameChange(n => { S.name = n; writeURL(); });

worker.onmessage = e => {
  const m = e.data;
  if (m.type === "stage") {
    one.status.textContent = "Loading the seat law in your browser: " + m.label.toLowerCase() + "…";
  } else if (m.type === "failed") {
    one.status.textContent = m.missing ? m.message : "The seat law could not load (" + m.message + "). Reload to try again.";
    one.status.classList.add("low");
  } else if (m.type === "ready") {
    engineReady = true;
    window.__seatEngineTimes = m.times;
    console.info("seat engine loaded", m.times);
    one.status.textContent = "Seats are worked out in your browser by the project's own seat code, the code that seats the model's simulations.";
    lock(false);
    paintBrush();
    afterEdit();
    one.undo.disabled = !history.size;
  } else if (m.type === "result") {
    if (m.seq !== seq) return;
    if (!m.ok) {
      one.status.textContent = "The seat law refused this forecast (" + m.errors.join("; ") + "). The page should not be able to build it; please report it.";
      one.status.classList.add("low");
      return;
    }
    result = m.answer;
    paintCouncil();
    paintCoalition();
    share();
  }
};

// ---------- first paint, then the seat law ----------
lock(true);
afterEdit();
worker.postMessage({ type: "init", schema });
