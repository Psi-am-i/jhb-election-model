// "Your forecast", section 2 ("Break the model"): the page. The reader calls
// every ward, sets each party's share of the combined vote and picks who
// governs; the seats come from the project's own seat code, run in the
// browser (js/make-worker.js). "Analyse my forecast" asks section 1's engine
// what the published forecast gives the reader's (page.py analyse).
//
// ⛔ A LIVE WRITER (stats.LIVE_WRITERS["your-forecast/js/make.js"]) for the
// regions "b-status", "b-map", "b-vote", "b-govern", "b-council",
// "b-actions", "b-analysis" and "b-wardtip". The build refuses the page
// (stats.script_writes) unless this file keeps the writer contract:
//   * it reaches the page ONLY through literal '[data-live="<name>"] …'
//     selectors, each for a region listed for it, all taken once, below;
//   * it writes with textContent, createElement and append; never markup;
//   * it does not walk out of a region and writes nothing through an event's
//     target.
// Its imports: builder-state.js, make-state.js, yf-url.js, map.js, seat-table.js and tip.js are
// scanned as NON-writers; make-share.js (region "b-share") and model.js
// (section 1) are writers in their own right.
//
// DESIGN-decided §8: every control applies to every party identically. Parties
// are listed alphabetically wherever a reader chooses; nothing is preselected.
// The vote list is two alphabetical lists, the parties seated at the
// published start and then the rest, collapsed: an order fixed by the page,
// not a ranking. §14: the builder can only hold a valid forecast
// (js/builder-state.js); seats are recomputed after every edit by the seat
// code the server would run.
//
// WHERE IT STARTS (owner, 2026-10-03: section 2 "continues the same
// forecast"). Untouched, section 1 is the published forecast and section 2
// opens at the published start (src/build_make.py, your-forecast/forecast.json:
// each ward's modal winner, and shares that seat each named party at its
// published middle). Once section 1 moves, its engine hands section 2 the same
// rule on the reader's weighted draws (page.py handoff, src/start_rule.py):
// each ward's most likely winner under the reader's changes, and shares that
// seat each named party at its middle under them.
//   * While the reader has not edited section 2, it follows section 1: each
//     new setting there re-opens section 2 at its hand-off.
//   * Once the reader has edited section 2, a new setting in section 1 does
//     not overwrite the edits. The status line says section 1 has changed and
//     offers to start again from it (undo restores the edits).
// The reader's forecast lives only in the address (js/make-state.js, its part
// written through js/yf-url.js beside section 1's).
//
// LAZY: section 2 loads its data, its map and its seat Worker (a second
// Pyodide) only when the reader comes near it, or at once when the address
// carries a section 2 forecast or the #break anchor.
//
// THE WALKTHROUGH (owner, 2026-10-03): four numbered steps, one highlighted at
// a time (data-step="now"); "Next" marks a step done and highlights the next.
// Every step stays usable whichever is highlighted.

import * as B from "./builder-state.js";
import * as MS from "./make-state.js";
import * as YU from "./yf-url.js";
import { WardMap } from "./map.js";
import { setShareable, onNameChange } from "./make-share.js";
import { seatTable } from "./seat-table.js";
import { placeTip } from "./tip.js";
import { engineCall, onForecast } from "./model.js";

const one = {
  statusRegion: document.querySelector('[data-live="b-status"]'),
  status: document.querySelector('[data-live="b-status"] .ess'),
  linknote: document.querySelector('[data-live="b-status"] .linknote'),
  follow: document.querySelector('[data-live="b-status"] .yf-follow'),
  followText: document.querySelector('[data-live="b-status"] .yf-followtext'),
  reseed: document.querySelector('[data-live="b-status"] .yf-reseed'),
  mapRegion: document.querySelector('[data-live="b-map"]'),
  svg: document.querySelector('[data-live="b-map"] svg'),
  mapscroll: document.querySelector('[data-live="b-map"] .mapscroll'),
  listview: document.querySelector('[data-live="b-map"] .listview'),
  nchanged: document.querySelector('[data-live="b-map"] .nchanged'),
  hint: document.querySelector('[data-live="b-map"] .painthint'),
  brush: document.querySelector('[data-live="b-map"] .brushscroll'),
  brushselect: document.querySelector('[data-live="b-map"] .brushselect'),
  area: document.querySelector('[data-live="b-map"] .area'),
  fillarea: document.querySelector('[data-live="b-map"] .fillarea'),
  copymodel: document.querySelector('[data-live="b-map"] .copymodel'),
  undo: document.querySelector('[data-live="b-map"] .undo'),
  next1: document.querySelector('[data-live="b-map"] .yf-next'),
  voteRegion: document.querySelector('[data-live="b-vote"]'),
  prmodel: document.querySelector('[data-live="b-vote"] .prmodel'),
  prfind: document.querySelector('[data-live="b-vote"] .prfind'),
  floornote: document.querySelector('[data-live="b-vote"] .floornote'),
  prlist: document.querySelector('[data-live="b-vote"] .prlist'),
  next2: document.querySelector('[data-live="b-vote"] .yf-next'),
  govRegion: document.querySelector('[data-live="b-govern"]'),
  coal: document.querySelector('[data-live="b-govern"] .coal'),
  coalstat: document.querySelector('[data-live="b-govern"] .coalstat'),
  next3: document.querySelector('[data-live="b-govern"] .yf-next'),
  councilRegion: document.querySelector('[data-live="b-council"]'),
  restate: document.querySelector('[data-live="b-council"] .restate'),
  bars: document.querySelector('[data-live="b-council"] .bars'),
  strip: document.querySelector('[data-live="b-council"] .strip'),
  capseats: document.querySelector('[data-live="b-council"] .capseats'),
  capmaj: document.querySelector('[data-live="b-council"] .capmaj'),
  excess: document.querySelector('[data-live="b-council"] .excess'),
  startnote: document.querySelector('[data-live="b-council"] .yf-startnote'),
  announce: document.querySelector('[data-live="b-council"] .announce'),
  actions: document.querySelector('[data-live="b-actions"]'),
  analyse: document.querySelector('[data-live="b-actions"] .yf-analyse'),
  analysis: document.querySelector('[data-live="b-analysis"]'),
  verdict: document.querySelector('[data-live="b-analysis"] .yf-verdict'),
  sseats: document.querySelector('[data-live="b-analysis"] .yf-sseats'),
  swards: document.querySelector('[data-live="b-analysis"] .yf-swards'),
  svote: document.querySelector('[data-live="b-analysis"] .yf-svote'),
  outcome: document.querySelector('[data-live="b-analysis"] .yf-outcome'),
  expected: document.querySelector('[data-live="b-analysis"] .yf-expected'),
  atable: document.querySelector('[data-live="b-analysis"] .yf-atable'),
  anote: document.querySelector('[data-live="b-analysis"] .yf-anote'),
  wardtip: document.querySelector('[data-live="b-wardtip"]'),
};
const views = document.querySelectorAll('[data-live="b-map"] .views button');

// A new element: properties, attributes (keys with a dash) and children.
function el(tag, props = {}, ...kids) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (v == null || v === false) continue;
    if (k.includes("-") || k === "role" || k === "scope") e.setAttribute(k, v === true ? "" : String(v));
    else e[k] = v;
  }
  e.append(...kids.filter(k => k != null && k !== false));
  return e;
}
// A party's colour swatch: its colour class (site.css, from render_sheet.CHIPS).
const sw = code => el("span", { className: "sw pc-" + code, "aria-hidden": "true" });
const SVG = "http://www.w3.org/2000/svg";
function sv(tag, attrs = {}, ...kids) {
  const e = document.createElementNS(SVG, tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, String(v));
  e.append(...kids);
  return e;
}

// ---------- the walkthrough ----------
const STEPS = [one.mapRegion, one.voteRegion, one.govRegion, one.actions];
let step = 0;
function paintSteps() {
  STEPS.forEach((r, i) => r.setAttribute("data-step", i < step ? "done" : i === step ? "now" : "next"));
}
[one.next1, one.next2, one.next3].forEach((b, i) => b.addEventListener("click", () => {
  step = Math.max(step, i + 1);
  paintSteps();
  STEPS[i + 1].scrollIntoView({ block: "nearest", behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
}));
paintSteps();

// ---------- locking: the controls answer once the seat law has loaded ----------
const editables = [one.brushselect, one.area, one.fillarea, one.copymodel, one.prmodel, one.analyse];
let engineReady = false;
function lock(on) {
  for (const r of [one.mapRegion, one.voteRegion, one.govRegion]) r.classList.toggle("locked", on);
  for (const e of editables) e.disabled = on;
}
lock(true);

// ---------- state, set when the section starts ----------
let D, schema, geom, ctx, byCode, name, alpha;
let pubStart;              // the published start (forecast.json)
let from;                  // the start section 2 is open at: pubStart or a hand-off
let adjusted = false;      // is `from` section 1's hand-off?
let fromMiddle = {};       // `from`'s middle seat count per named party (start_rule "published")
let state, S, history, map, worker;
let result = null, seq = 0;
let started = false;
let fromLink = false;      // opened from a link's forecast, not yet measured against section 1

const pct = (v, dp = 1) => {
  const p = v / ctx.T * 100;
  return p > 0 && p < 0.05 ? "under 0.1" : p.toFixed(dp);
};

// ---------- following section 1 ----------
let section1 = null;       // { settings, touched }, the newest setting section 1 shows
let handSeq = 0, waiting = null;
onForecast(f => { section1 = f; if (started) follow(); });

async function follow() {
  const f = section1, ticket = ++handSeq;
  // before start() has its data, there is nothing to follow with: start()
  // follows once it has
  if (!f || !ctx || !from) return;
  let next;
  if (!f.touched) next = { state: pubStart, adjusted: false, middle: D.start.published_middle };
  else {
    let h;
    try { h = await engineCall("handoff", { settings: f.settings, total: ctx.T }); }
    catch (e) { return; }                        // section 2 stays where it is
    if (ticket !== handSeq) return;              // a newer setting is on its way
    if (h.refused) return;
    const calls = ctx.wards.map(w => h.ward_calls[w]);
    next = { state: B.startState(ctx, { calls, share: h.share }, pubStart.calls).state, adjusted: true, middle: h.middle };
  }
  if (fromLink) {
    // a forecast opened from a link is the reader's: its start becomes
    // section 1's hand-off without a note, and nothing is overwritten
    fromLink = false;
    ({ state: from, adjusted, middle: fromMiddle } = next);
    afterEdit();
    return;
  }
  if (MS.sameState(next.state, from, ctx)) { waiting = null; one.follow.hidden = true; return; }
  if (MS.sameState(state, from, ctx)) {
    // unedited: section 2 follows section 1
    ({ state: from, adjusted, middle: fromMiddle } = next);
    waiting = null;
    one.follow.hidden = true;
    state = from;
    afterEdit();
  } else {
    waiting = next;
    one.followText.textContent = next.adjusted
      ? "Your changes to the model have moved since this section opened from them."
      : "Your changes to the model are undone since this section opened from them.";
    one.follow.hidden = false;
  }
}
one.reseed.addEventListener("click", () => {
  if (!waiting) return;
  snapshot();
  ({ state: from, adjusted, middle: fromMiddle } = waiting);
  waiting = null;
  one.follow.hidden = true;
  commit(from);
});

// ---------- start when the reader comes near ----------
async function start() {
  if (started) return;
  started = true;
  one.status.textContent = "Loading the start and the seat law.";
  try {
    const r = await fetch(new URL("../forecast.json", import.meta.url));
    if (!r.ok) throw new Error("HTTP " + r.status);
    D = await r.json();
  } catch (e) {
    one.status.textContent = "The start could not be loaded (" + (e.message || e) + "). Reload to try again.";
    started = false;
    return;
  }
  schema = D.schema; geom = D.geometry;
  ctx = B.contextOf(schema);
  byCode = Object.fromEntries(schema["x-parties"].map(p => [p.code, p]));
  name = c => byCode[c].name;
  alpha = ctx.codes.slice().sort((a, b) => name(a).localeCompare(name(b)));
  pubStart = B.startState(ctx, { calls: D.start.ward_calls, share: D.start.combined_share }, D.start.ward_calls).state;
  if (geom.wards.map(w => String(w.id)).join() !== ctx.wards.join()) throw new Error("the geometry and the schema disagree about the wards");
  from = pubStart;
  fromMiddle = D.start.published_middle;
  const opened = MS.parse(YU.partOf(location.search, YU.BREAK_KEYS), ctx, D.context_ref, pubStart,
                          "Break the model opens at its start instead.");
  state = opened.state;
  S = { coalition: opened.coalition.slice(), brush: null };
  if (opened.note) { one.linknote.textContent = opened.note; one.linknote.hidden = false; }
  history = new B.History();
  map = new WardMap(one.svg, geom, { byCode, onPaint: paintWard, onFocusWard: focusTip });
  map.onClear = () => { one.hint.textContent = "Every ward needs a winner. Choose a party, then tap the ward to change it."; };
  buildBrush();
  buildVote();
  fromLink = !MS.sameState(state, pubStart, ctx);
  afterEdit();
  if (section1) follow();          // section 1 may have spoken while the data loaded
  worker = new Worker(new URL("./make-worker.js", import.meta.url), { type: "module" });
  worker.onmessage = onWorker;
  worker.postMessage({ type: "init", schema });
}
const wantsNow = /(^|[?&])f=/.test(location.search) || location.hash === "#break";
if (wantsNow) start();
else new IntersectionObserver((es, io) => {
  if (es.some(e => e.isIntersecting)) { io.disconnect(); start(); }
}, { rootMargin: "600px 0px" }).observe(one.statusRegion);

// ---------- map ----------
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
function buildBrush() {
  one.brushselect.append(el("option", { value: "" }, "Choose…"), ...alpha.map(c => el("option", { value: c }, name(c))));
}
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
    const b = el("button", { type: "button", className: "chip", value: c, "aria-pressed": String(c === S.brush), disabled: !engineReady }, sw(c), name(c));
    b.addEventListener("click", () => chooseBrush(S.brush === c ? null : c));
    return b;
  }));
}

for (const b of views) b.addEventListener("click", () => {
  if (!started) return;
  const v = b.dataset.view;
  for (const x of views) x.setAttribute("aria-pressed", String(x === b));
  one.mapscroll.hidden = v === "list";
  one.listview.hidden = v !== "list";
  if (v === "list") buildList(); else map.setMode(v);
});

// The list view: one aligned table per area (ward | the party it is called
// for | the chance we give that call, once analysed), filtered by area and by
// party instead of one long scroll. The areas are the area picker's options
// (one definition, in the page).
const AREAS = () => [...one.area.options].map(o => [o.value, o.textContent]);
const LIST = { area: null, party: "" };
function buildList() {
  if (LIST.area === null) LIST.area = AREAS()[0][0];
  const held = alpha.filter(c => state.calls.includes(c));
  if (LIST.party && !held.includes(LIST.party)) LIST.party = "";
  const areaPick = el("select", { className: "wlf-area", disabled: !engineReady },
    el("option", { value: "" }, "Every area"), ...AREAS().map(([v, t]) => el("option", { value: v }, t)));
  areaPick.value = LIST.area;
  areaPick.addEventListener("change", () => { LIST.area = areaPick.value; buildList(); });
  const partyPick = el("select", { className: "wlf-party", disabled: !engineReady },
    el("option", { value: "" }, "Every party"), ...held.map(c => el("option", { value: c }, name(c))));
  partyPick.value = LIST.party;
  partyPick.addEventListener("change", () => { LIST.party = partyPick.value; buildList(); });
  const bar = el("div", { className: "wlfilter" }, el("label", {}, "Area ", areaPick), el("label", {}, "Called for ", partyPick));
  const opts = () => alpha.map(c => el("option", { value: c }, name(c)));
  const tables = AREAS().filter(([v]) => !LIST.area || v === LIST.area).map(([sec, title]) => {
    const rows = [];
    geom.wards.forEach((w, i) => {
      if (w.sector !== sec || (LIST.party && state.calls[i] !== LIST.party)) return;
      const s = el("select", { id: "wl" + i, disabled: !engineReady, "aria-label": "Ward " + w.id + ", called for" }, ...opts());
      s.value = state.calls[i];
      s.addEventListener("change", () => {
        snapshot();
        const r = B.assignWards(state, ctx, [i], s.value);
        commit(r.state, raisedNote(r.raised));
      });
      const got = analysed ? analysed.wards[ctx.wards[i]] : null;
      rows.push(el("tr", {}, el("th", { scope: "row" }, "Ward " + w.id),
        el("td", {}, el("span", { className: "wlpick" }, sw(state.calls[i]), s)),
        el("td", { className: "wln", title: got ? chanceSentence(got.text) : "" }, got ? got.text : "–")));
    });
    if (!rows.length) return [];
    // an area's wards in two halves, side by side where the list is wide
    // (css/interactive.css .wardlist); stacked, the second reads on from the
    // first, its caption and header hidden
    const cut = Math.ceil(rows.length / 2);
    const halves = rows.length > 1 ? [rows.slice(0, cut), rows.slice(cut)] : [rows];
    return halves.map((part, k) => el("table", { className: k ? "wltable wlcont" : "wltable" },
      el("caption", {}, title),
      el("colgroup", {}, el("col", { className: "wlc-ward" }), el("col", { className: "wlc-party" }), el("col", { className: "wlc-chance" })),
      el("thead", {}, el("tr", {}, el("th", { scope: "col" }, "Ward"), el("th", { scope: "col" }, "Called for"),
        el("th", { scope: "col", className: "wln" }, analysed ? "Our chance" : "Our chance, once analysed"))),
      el("tbody", {}, ...part)));
  }).flat();
  one.listview.replaceChildren(bar, el("div", { className: "wardlist" },
    tables.length ? el("div", { className: "wlgrid" }, ...tables)
      : el("p", { className: "stubnote" }, "No ward in this area is called for that party.")));
}

one.fillarea.addEventListener("click", () => {
  if (!S.brush) { one.hint.textContent = "Choose a party first, then fill the area."; return; }
  const sec = one.area.value;
  setCallsFrom(state.calls.map((c, i) => geom.wards[i].sector === sec ? S.brush : c));
});
one.copymodel.addEventListener("click", () => setCallsFrom(from.calls));
one.undo.addEventListener("click", () => {
  const prev = history.pop(); if (!prev) return;
  commit(prev);
});

// ---------- the vote: a table with the seat table's columns ----------
// Party | slider | percent, one identical row per party. The parties that
// hold a seat in the published start come first, most seats first as the
// seat table orders them; every other party, alphabetical, in a collapsed
// "Other parties". The order is the published start's, fixed for the page,
// so a row never moves under the reader's finger; finding a party opens the
// second list. The percent box is text with a decimal keypad: no spinner.
const rows = {};
let rest;
function buildVote() {
  const start = D.start.seats;
  const seatedAtStart = alpha.filter(c => (start[c] || 0) > 0)
    .sort((a, b) => start[b] - start[a] || name(a).localeCompare(name(b)));
  const restList = el("div", { className: "prrest" });
  rest = el("details", { className: "prmore" }, el("summary", {}, "Other parties"), restList);
  const head = el("div", { className: "prrow prhead", "aria-hidden": "true" },
    el("span", {}, "Party"), el("span", {}, "Share of all votes"), el("span", { className: "prpct" }, "%"));
  one.prlist.append(head);
  for (const c of [...seatedAtStart, ...alpha.filter(x => !seatedAtStart.includes(x))]) {
    const num = el("input", { type: "text", id: "pr-n-" + c, inputMode: "decimal", autocomplete: "off", spellcheck: false,
                              disabled: true, className: "prnum" });
    const rng = el("input", { type: "range", min: "0", max: "100", step: "0.1", disabled: true, "aria-label": name(c) + ", share of all votes, percent" });
    const fl = el("span", { className: "fl" });
    const row = el("div", { className: "prrow" }, el("label", { htmlFor: "pr-n-" + c, className: "prname" }, sw(c), name(c)), rng, num, fl);
    num.addEventListener("change", () => editShare(c, num.value, true, null));
    num.addEventListener("keydown", e => { if (e.key === "Enter") editShare(c, num.value, true, null); });
    rng.addEventListener("input", () => editShare(c, rng.value, false, rng));
    rng.addEventListener("change", () => editShare(c, rng.value, true, null));
    rows[c] = { row, num, rng, fl, seated: seatedAtStart.includes(c) };
    editables.push(num, rng);
    (rows[c].seated ? one.prlist : restList).append(row);
  }
  one.prlist.append(rest);
  if (engineReady) lock(false);
}
one.prfind.addEventListener("input", () => {
  if (!started) return;
  const q = one.prfind.value.trim().toLowerCase();
  for (const c of alpha) rows[c].row.hidden = !!q && !name(c).toLowerCase().includes(q);
  if (q && alpha.some(c => !rows[c].seated && !rows[c].row.hidden)) rest.open = true;
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
  const r = B.setCalls({ calls: state.calls, votes: { ...from.votes } }, ctx, state.calls);
  commit(r.state, raisedNote(r.raised));
});

// ---------- recompute ----------
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
  const changed = state.calls.filter((c, i) => c !== from.calls[i]).length;
  const whose = adjusted ? "your adjusted forecast's" : "the model's";
  one.nchanged.textContent = changed ? changed + (changed === 1 ? " changed from " + whose + " call" : " changed from " + whose + " calls")
    : "as " + whose.replace(/'s$/, "") + " calls them";
  paintStartNote();
  writeURL();
  if (engineReady) worker.postMessage({ type: "seats", seq: ++seq, forecast: B.forecastBody(state, ctx) });
}

// While the forecast is still its start: every named party whose start seats
// were raised from its middle seat count to the wards it is called for, so a
// start that differs from section 1's middles says where and why
// (start_rule step 2, the ward floor; review of lane Y, 2026-10-03).
function raisedAtStart() {
  if (!MS.sameState(state, from, ctx)) return [];
  const held = {};
  for (const c of from.calls) held[c] = (held[c] || 0) + 1;
  return Object.keys(fromMiddle || {}).filter(c => byCode[c] && (held[c] || 0) > fromMiddle[c])
    .sort((a, b) => name(a).localeCompare(name(b)))
    .map(c => ({ code: c, wards: held[c], middle: fromMiddle[c] }));
}
function raisedText(raised, whose) {
  if (!raised.length) return "";
  return raised.map(r => name(r.code) + " is called for " + r.wards + " wards, more than its middle seat count of " + r.middle +
    " " + whose).join(". ") + ". " + (raised.length === 1 ? "It starts" : "Each starts") + " at its ward count.";
}
function paintStartNote() {
  one.startnote.textContent = raisedText(raisedAtStart(), adjusted ? "under your changes" : "in the published forecast");
}

function writeURL() {
  YU.write("break", MS.serialize({ state, coalition: S.coalition }, ctx, D.context_ref, from));
  if (result) share();
}

// ---------- coalition ----------
function paintCoalition() {
  const seats = result.seats;
  const shown = alpha.filter(c => seats[c] || S.coalition.includes(c));
  one.coal.replaceChildren(...shown.map(c => {
    const b = el("button", { type: "button", className: "chip", "aria-pressed": String(S.coalition.includes(c)) },
      sw(c), name(c) + " ", el("span", { className: "chipn" }, String(seats[c] || 0)));
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
// The seat table's axis, ticks and header words, set by the build on the
// "b-council" region from src/seat_table.py (the one definition).
const TABLE = {
  scale: Number(one.councilRegion.dataset.scale),
  ticks: String(one.councilRegion.dataset.ticks || "").split(" ").filter(Boolean).map(Number),
  head: String(one.councilRegion.dataset.head || "").split("|"),
};
function order(seats) {
  return Object.keys(seats).filter(c => seats[c] > 0).sort((a, b) => seats[b] - seats[a] || name(a).localeCompare(name(b)));
}
function paintCouncil() {
  const { seats, ward, council_total: council, majority, excessive } = result;
  const list = order(seats);
  const max = Math.max(1, ...list.map(c => seats[c]));
  one.restate.textContent = "Each party's wards plus its list seats, of " + council + ".";
  // The site's one seat table (js/seat-table.js). A single council has no
  // range: the mark is the party's seats, and the range column is empty. The
  // axis is the site's, widened in steps of its own tick spacing when a party
  // the reader built holds more seats than it reaches.
  const T = TABLE.ticks, tick = T[1] - T[0];
  const scale = max <= TABLE.scale ? TABLE.scale : Math.ceil(max / tick) * tick;
  const every = tick * Math.ceil(scale / tick / (T.length - 1));
  const ticks = scale === TABLE.scale ? T : Array.from({ length: Math.floor(scale / every) + 1 }, (_, i) => i * every);
  one.bars.replaceChildren(seatTable(document, list.map(c => ({
    code: c, name: name(c), sub: null, seats: String(seats[c]), lo: null, hi: null,
    m: seats[c], p5: null, p95: null, ghost: null, arrow: null,
    title: (ward[c] || 0) + " wards, " + (seats[c] - (ward[c] || 0)) + " list",
  })), { scale, ticks, head: TABLE.head, label: "Your council" }));
  // the whole council in one bar, the majority line across it
  let at = 0;
  const segs = list.map(c => {
    const r = sv("rect", { class: "pc-" + c, x: (at / council * 100).toFixed(2) + "%", y: 0,
      width: (seats[c] / council * 100).toFixed(2) + "%", height: 16 });
    at += seats[c];
    return r;
  });
  const mx = ((majority - 0.5) / council * 100).toFixed(2) + "%";
  one.strip.replaceChildren(sv("svg", { class: "stripbar", width: "100%", height: 16 }, ...segs,
    sv("line", { class: "maj", x1: mx, x2: mx, y1: -4, y2: 20 })));
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
    url: YU.linkTo("break", "#break"), name: YU.currentName(), edited: !MS.sameState(state, from, ctx), adjusted,
    calls: state.calls, seats: result.seats, council: result.council_total, majority: result.majority,
    coalition: S.coalition, geom, party: c => byCode[c], election: D.election,
    raised: raisedText(raisedAtStart(), adjusted ? "under the reader's changes" : "in the published forecast"),
  });
}
onNameChange(n => { YU.write("name", n); if (result) share(); });

// ---------- "Analyse my forecast" ----------
// The reader's forecast, as page.py's analyse reads it: every ward's call, the
// combined shares, the seats the law gives them. The answer is the published
// forecast's chances (page.py says how); shown in "b-analysis", and each
// ward's chance on hover over the map. Once shown, it follows every edit.
let analysed = null, analyseTimer = null, analyseTicket = 0;
one.analyse.addEventListener("click", () => {
  step = Math.max(step, 3);
  paintSteps();
  analyse(true);
});
async function analyse(scroll) {
  if (!result) return;
  const ticket = ++analyseTicket;
  // the first analysis opens the region with a line saying it is working;
  // a re-analysis after an edit keeps the figures in place until the new
  // ones arrive, so nothing on the page changes height while it works
  if (one.analysis.hidden) one.anote.textContent = "Working it out…";
  one.analysis.hidden = false;
  let a;
  try {
    a = await engineCall("analyse", { ward_calls: Object.fromEntries(ctx.wards.map((w, i) => [w, state.calls[i]])),
                                      share: B.percentOf(state, ctx), seats: result.seats,
                                      majority: result.majority, coalition: S.coalition,
                                      keep: analysed ? Object.keys(analysed.seats) : [] });
  } catch (e) {
    if (ticket === analyseTicket) one.anote.textContent = "The analysis could not run: " + (e.message || e) + ".";
    return;
  }
  if (ticket !== analyseTicket) return;
  analysed = a;
  paintAnalysis(a);
  if (!one.listview.hidden) buildList();
  if (scroll) one.analysis.scrollIntoView({ block: "start", behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
}
// "We give this outcome a 3% chance." The owner's wording (2026-10-03), for
// the whole forecast, a ward, a party's seats and its vote alike; a chance
// printed as "under 0.1%" or "over 99%" reads "a chance of under 0.1%".
function aChance(text) {
  if (!/^\d/.test(text)) return "a chance of " + text;
  return (/^(8|11|18)(\D|$)|^8\d/.test(text) ? "an " : "a ") + text + " chance";
}
function chanceSentence(text) {
  return "We give this outcome " + aChance(text) + ".";
}
// the reader's council-level outcome, in words (page.py analyse: reweight.council_outcome)
function outcomeWords(o) {
  const lead = o.largest ? name(o.largest) + " has the most seats" : "two or more parties tie for the most seats";
  const maj = o.majority_alone ? "one party has a majority on its own" : "no party has a majority on its own";
  const gov = o.coalition.length ? ", and " + o.coalition.map(name).join(", ") + " together hold a majority" : "";
  return "The outcome: " + lead + ", " + maj + gov + ".";
}
function paintAnalysis(a) {
  // The headline is the chance of the reader's council-level outcome (the
  // largest party, a majority alone or not, the chosen coalition). Under it,
  // the reader's forecast scored against each simulation as if it were the
  // result, by the competition's rules in its order: seats, ward calls, vote
  // (page.py analyse; JUDGEMENT-CALLS §N4). Then the template's closing line.
  const sc = a.score;
  one.verdict.textContent = chanceSentence(a.outcome.text);
  one.sseats.replaceChildren(el("b", {}, "Seats: "), "we expect your seat counts to be off by " + Math.round(sc.seat_error) +
    " in total across the parties, and give " + aChance(sc.seat_error_within.text) + " that they are off by " + sc.within + " or fewer.");
  one.swards.replaceChildren(el("b", {}, "Wards: "), "we expect " + Math.round(sc.wards_called) + " of your " + a.wards_count +
    " ward calls to be right.");
  one.svote.replaceChildren(el("b", {}, "Vote: "), "we expect your vote shares to be off by " + sc.list_vote_error.toFixed(1) +
    " points in total, on the list ballot.");
  one.outcome.textContent = outcomeWords(a.outcome);
  one.expected.textContent = HOVER.matches
    ? "Hover over a ward, or reach it with the arrow keys, for the chance we give your call there."
    : "Tap a ward with no party chosen for the chance we give your call there.";
  const sb = a.seat_band, pb = a.share_band;
  const head = el("tr", {}, el("th", { scope: "col" }, "Party"), el("th", { scope: "col", className: "num" }, "Your seats"),
    el("th", { scope: "col", className: "num" }, "Chance within " + sb + " seats"),
    el("th", { scope: "col", className: "num" }, "Your vote"),
    el("th", { scope: "col", className: "num" }, "Chance within " + pb + " points, list ballot"));
  const seats = result.seats, share = B.percentOf(state, ctx);
  const codes = Object.keys(a.seats).sort((x, y) => (seats[y] || 0) - (seats[x] || 0) || name(x).localeCompare(name(y)));
  // two layouts of the same cells (css/your-forecast.css): one row per party,
  // or on a phone a party's seats and then its vote, each in its own row
  const yourVote = c => (share[c] ?? 0).toFixed(1) + "%", voteChance = c => (a.share[c] ? a.share[c].text : "");
  const voteTitle = c => (a.share[c] ? chanceSentence(a.share[c].text) : "");
  const body = codes.flatMap(c => [
    el("tr", { className: "yf-wide" },
      el("td", {}, sw(c), name(c)), el("td", { className: "num" }, String(seats[c] || 0)),
      el("td", { className: "num", title: chanceSentence(a.seats[c].text) }, a.seats[c].text),
      el("td", { className: "num" }, yourVote(c)),
      el("td", { className: "num", title: voteTitle(c) }, voteChance(c))),
    el("tr", { className: "yf-narrow" },
      el("td", {}, sw(c), name(c)), el("td", { className: "num" }, String(seats[c] || 0) + " seats"),
      el("td", { className: "num", title: chanceSentence(a.seats[c].text) }, a.seats[c].text)),
    el("tr", { className: "yf-narrow" },
      el("td", {}), el("td", { className: "num" }, yourVote(c) + " vote"),
      el("td", { className: "num", title: voteTitle(c) }, voteChance(c))),
  ]);
  const narrowHead = el("tr", { className: "yf-narrow" }, el("th", { scope: "col" }, "Party"),
    el("th", { scope: "col", className: "num" }, "Yours"),
    el("th", { scope: "col", className: "num" }, "Chance within " + sb + " seats, or " + pb + " points (list ballot)"));
  head.className = "yf-wide";
  one.atable.replaceChildren(el("table", { className: "yf-at" }, el("thead", {}, head, narrowHead), el("tbody", {}, ...body)));
  one.anote.textContent = "Every chance and expectation is the published forecast's: its " + a.draws.toLocaleString("en-US") +
    " simulations, each counted once, seated by the law. Seats, wards and vote score your forecast against each simulation as if it" +
    " were the result, by the competition's rules in its order. Seats: the gap between your seats and the simulation's, party by" +
    " party, added up. Wards: your calls that match its winners. Vote: the gap between your vote and its list-ballot share, party by" +
    " party, added up, in points. The line at " + sc.within + " seats is a judgement, not a measurement. Your vote is your share of" +
    " both ballots together; the simulations carry each party's list-ballot share only, so that is what it is compared with, and the" +
    " parties they do not carry one by one are compared as one group.";
}
// each ward's chance, over the map, once analysed: on hover, and on focus (the
// arrow keys, or a tap, which focuses the ward; with no party chosen a tap
// paints nothing)
const HOVER = matchMedia("(hover: hover)");
function tipFor(i, x, y) {
  const w = i == null ? null : ctx.wards[+i], got = analysed && w != null ? analysed.wards[w] : null;
  if (!got) { one.wardtip.hidden = true; return; }
  one.wardtip.textContent = "Ward " + w + ", " + name(state.calls[+i]) + ". " + chanceSentence(got.text);
  one.wardtip.hidden = false;
  placeTip(one.wardtip, x, y);
}
function focusTip(i) {
  // after the focus has scrolled the ward into view
  requestAnimationFrame(() => {
    const r = map.els[i].getBoundingClientRect();
    tipFor(i, r.left + r.width / 2, r.top + r.height / 2);
  });
}
one.svg.addEventListener("mousemove", e => tipFor(e.target.getAttribute && e.target.getAttribute("data-i"), e.clientX, e.clientY));
one.svg.addEventListener("mouseleave", () => { one.wardtip.hidden = true; });
one.svg.addEventListener("focusout", () => { one.wardtip.hidden = true; });

// ---------- the seat Worker ----------
function onWorker(e) {
  const m = e.data;
  if (m.type === "stage") {
    if (m.label !== "Ready") one.status.textContent = m.label + "…";
  } else if (m.type === "failed") {
    one.status.textContent = m.missing ? m.message : "The seat law could not load (" + m.message + "). Reload to try again.";
    one.status.classList.add("low");
  } else if (m.type === "ready") {
    engineReady = true;
    window.__seatEngineTimes = m.times;
    console.info("seat engine loaded", m.times);
    one.status.textContent = "";
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
    if (analysed) { clearTimeout(analyseTimer); analyseTimer = setTimeout(() => analyse(false), 400); }
  }
}
