// "Your forecast", section 1 ("Adjust the model"): the page. It holds the
// controls and writes the figures the model's Python returns; it computes
// none of them.
//
// Every figure a control produces is computed by src/reweight.py, through
// pyboot/page.py, under Pyodide, in a Web Worker (js/model-worker.js; SPEC-v2
// Lane P, F11), and every ward is coloured by src/render_map.py's ward_call
// there too. There is no re-weighting and no drawing rule in JavaScript: one
// definition, in Python (INTEGRATION §3b). What is here is presentation:
// rounding a figure for print, placing a bar, and an arrow for a change
// page.py has already computed.
//
// The same Worker answers section 2 ("Break the model", js/make.js): where it
// opens from these settings (page.py handoff) and what the model gives the
// reader's own forecast (page.py analyse). make.js asks through engineCall and
// hears of each new setting through onForecast; this module owns the Worker.
//
// ⛔ THE ONE MODULE THAT WRITES SECTION 1'S FIGURES, and the path listed for
// it in stats.LIVE_WRITERS ("your-forecast/js/model.js"), with the LIVE
// regions it may write. The build refuses the page (stats.script_writes)
// unless this file keeps the writer contract:
//   * it reaches the page ONLY through literal '[data-live="<name>"] …'
//     selectors, each for a region listed for it, all taken once, below;
//   * it writes with textContent, createElement(NS) and append; never markup;
//   * it does not walk out of a region (no parent, sibling or document-level
//     handles), and writes nothing through an event's target.
// Its imports: play-state.js, yf-url.js, seat-table.js and tip.js are scanned as NON-writers;
// play-card.js (the party order, seat format and setting names it shares with
// the share image) and play-share.js (region "share") are writers in their
// own right.
//
// First paint (F6, DESIGN §4): the published forecast's figures, rendered by
// build_site as ledgered tokens in each element's build twin, and no Python.
// When a control moves away from the published setting this module sets
// data-touched on the "result" region; css/play.css then hides every twin and
// shows the LIVE regions this module has filled. "Back to the forecast"
// removes it, and the twins show again.
//
// Precision (DESIGN-decided §15): a move that would leave any figure shown
// known to worse than reweight.MAX_FIGURE_SE_SEATS stops: the control returns
// to the furthest setting for which page.py's reweight.within_precision held.
// Never silently (owner, 2026-10-05): a slider that stops shows a shaded zone
// beyond the furthest setting it reaches and one line saying why, under the
// slider; an option of a discrete control (a poll, a by-election weight, a
// seat law) that cannot be shown at the other settings is marked, and the
// line beside that control names it and says why. Both are forgotten when
// another control moves, because the stop depends on every other setting.
//
// Change cues (owner, 2026-10-03): a seat row or banner entry whose middle
// moved since the last figures shown pulses, with a ▲/▼ for the direction;
// on a narrow screen with the seat table out of view, a toast names the
// parties that moved. css/your-forecast.css drops the motion under
// prefers-reduced-motion. The computing indicator floats over the page and
// moves nothing ("busy").

import * as PS from "./play-state.js";
import * as YU from "./yf-url.js";
import { order, seatText, rangeText, cellName, pollName, settingsWords, largestTop, theName } from "./play-card.js";
import { setShareable } from "./play-share.js";
import { seatTable } from "./seat-table.js";
import { placeTip } from "./tip.js";

const DEBOUNCE_MS = 200;
const SVG = "http://www.w3.org/2000/svg";

// Every element this module touches, each by a literal LIVE selector.
const R = {
  engineRegion: document.querySelector('[data-live="engine"]'),
  engine: document.querySelector('[data-live="engine"] .pl-engine'),
  busy: document.querySelector('[data-live="busy"]'),
  toast: document.querySelector('[data-live="toast"]'),
  linknote: document.querySelector('[data-live="engine"] .pl-linknote'),
  banner: document.querySelector('[data-live="banner"]'),
  result: document.querySelector('[data-live="result"]'),
  status: document.querySelector('[data-live="result"] .pl-status'),
  settings: document.querySelector('[data-live="result"] .pl-settings'),
  back: document.querySelector('[data-live="result"] .pl-back'),
  oneline: document.querySelector('[data-live="result"] .pl-oneline'),
  announce: document.querySelector('[data-live="result"] .pl-announce'),
  map: document.querySelector('[data-live="map"]'),
  wardtip: document.querySelector('[data-live="wardtip"]'),
  flips: document.querySelector('[data-live="flips"]'),
  seats: document.querySelector('[data-live="seats"]'),
  turnout: document.querySelector('[data-live="turnout"]'),
  polls: document.querySelector('[data-live="polls"]'),
  trust: document.querySelector('[data-live="trust"]'),
  cells: document.querySelector('[data-live="cells"]'),
  bye: document.querySelector('[data-live="byelection"]'),
  law: document.querySelector('[data-live="law"]'),
  lawnow: document.querySelector('[data-live="lawnow"]'),
  ess: document.querySelector('[data-live="ess"]'),
};

// A new element: properties, attributes (keys with a dash) and children.
function el(tag, props = {}, ...kids) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (v == null || v === false) continue;
    if (k.includes("-") || k === "role" || k === "for") e.setAttribute(k, v === true ? "" : String(v));
    else e[k] = v;
  }
  e.append(...kids.filter(k => k != null && k !== false));
  return e;
}
// An SVG element, attributes only.
function sv(tag, attrs = {}, ...kids) {
  const e = document.createElementNS(SVG, tag);
  for (const [k, v] of Object.entries(attrs)) if (v != null) e.setAttribute(k, String(v));
  e.append(...kids);
  return e;
}
const clear = node => node.replaceChildren();

// Party names, colours and articles arrive with the engine (parties.json).
let roster = {};
const party = c => roster[c] ?? { code: c, name: c.replace(/_/g, " ").toLowerCase().replace(/(^|\s)\S/g, m => m.toUpperCase()), colour: "#8b918b", article: "" };
const nameOf = c => (c === "OTHERS" ? "Others" : party(c).name);

// The seat table's axis, ticks and header words, set by the build on the
// "seats" region from src/seat_table.py (the one definition).
const TABLE = {
  scale: Number(R.seats.dataset.scale),
  ticks: String(R.seats.dataset.ticks || "").split(" ").filter(Boolean).map(Number),
  head: String(R.seats.dataset.head || "").split("|"),
  label: "Seats under your settings",
};
// The election day, set by the build on the "engine" region.
const WHEN = (() => {
  const d = new Date(String(R.engineRegion.dataset.election || "") + "T12:00:00");
  return isNaN(d) ? "" : d.toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" });
})();

// ---------- the engine ----------
const worker = new Worker(new URL("./model-worker.js", import.meta.url), { type: "module" });
let ctx = null, st = null, seq = 0, lastMoved = null, baseline = null, timer = null;
let accepted = null;          // { state, result }: the last setting every shown figure passed
let geometry = null;          // the ward boundaries (play/ward_paths.json)
let pubOrder = [];            // the published rows' order: the banner keeps it
const pending = new Map();
const groups = {};            // control group -> the element that greys
const inputs = { turnout: [], tlabel: [], tscale: [], tzone: [], poll: [], pollRow: [], law: [], lawRow: [], cells: [] };
// Where each slider stops at the other settings now ({ group: { up, down } },
// play-state.js withStop) and why; and the one option of each discrete
// control refused at them ({ group: { group, value, why } }).
const limits = {}, limitWhy = {}, unavailable = {};

const geometryP = fetch(new URL("../ward_paths.json", import.meta.url))
  .then(r => (r.ok ? r.json() : null)).catch(() => null)
  .then(g => { geometry = g; return g; });
// The seat laws' names, as /forecast prints them (render_sheet.SEAT_LAWS).
const lawsP = fetch(new URL("../laws.json", import.meta.url))
  .then(r => (r.ok ? r.json() : {})).catch(() => ({}));

function ask(settings) {
  const id = ++seq;
  worker.postMessage({ type: "compute", seq: id, settings });
  return new Promise((ok, no) => pending.set(id, { ok, no }));
}

// ---------- what section 2 (js/make.js) reaches through this module ----------
// A call to page.py's handoff or analyse, answered in order and never
// superseded; rejected if the engine did not load.
const calls = new Map();
let callSeq = 0, engineFailed = null;
let readyResolve;
const engineReady = new Promise(ok => { readyResolve = ok; });
export async function engineCall(fn, payload) {
  await engineReady;
  if (engineFailed) throw new Error(engineFailed);
  const id = ++callSeq;
  worker.postMessage({ type: "call", id, fn, payload });
  return new Promise((ok, no) => calls.set(id, { ok, no }));
}
// Each setting section 1 shows, as it is shown: { settings, touched }. A
// listener added late hears the current one at once.
const listeners = [];
let shownNow = null;
export function onForecast(cb) {
  listeners.push(cb);
  if (shownNow) cb(shownNow);
}
function told(state) {
  shownNow = { settings: PS.engineSettings(state), touched: PS.isTouched(state) };
  for (const cb of listeners) cb(shownNow);
}

worker.onmessage = e => {
  const m = e.data;
  if (m.type === "stage") R.engine.textContent = m.label + "…";
  else if (m.type === "failed") {
    R.engine.textContent = m.missing ? m.message : "The re-weighting code did not load: " + m.message + ". The published forecast is shown.";
    R.engine.classList.add("pl-low");
    engineFailed = "the re-weighting code did not load";
    readyResolve();
  } else if (m.type === "ready") ready(m);
  else if (m.type === "answer" || m.type === "callerror") {
    const c = calls.get(m.id);
    calls.delete(m.id);
    if (c) m.type === "answer" ? c.ok(m.result) : c.no(new Error(m.message));
  } else if (m.type === "result" || m.type === "error") {
    const p = pending.get(m.seq);
    pending.delete(m.seq);
    // an older request superseded by a newer one is dropped, not shown
    for (const k of [...pending.keys()]) if (k < m.seq) { pending.get(k).no(new Error("superseded")); pending.delete(k); }
    if (p) m.type === "result" ? p.ok(m) : p.no(new Error(m.message));
  }
};

// ---------- controls ----------
async function ready(m) {
  const cells = [...m.cells].sort((a, b) => a.w_bye - b.w_bye);
  roster = m.parties || {};
  const lawsText = await lawsP;
  ctx = { pools: m.pools, polls: m.polls.map(p => p.id), pollRows: m.polls,
          laws: m.laws.filter(k => k === PS.PUBLISHED_LAW || lawsText[k]), laws_text: lawsText,
          cells: cells.map(c => c.path), cellRows: cells, modelVersion: m.modelVersion };
  window.__playEngineTimes = m.times;
  readyResolve();
  const parsed = PS.parse(location.search, ctx);
  st = { ...parsed.state, name: YU.nameOf(location.search) };
  const notes = [];
  if (YU.nameRefused(location.search)) parsed.dropped.push("name: at most " + PS.NAME_MAX + " characters");
  if (parsed.dropped.length) notes.push("Some settings in this link were not applied: " + parsed.dropped.join("; ") + ".");
  if (parsed.otherVersion) notes.push("This link was made against a different version of the model; its settings are applied to the current one.");
  if (notes.length) { R.linknote.textContent = notes.join(" "); R.linknote.hidden = false; }
  R.engine.textContent = "";
  ask(PS.engineSettings(PS.defaults(ctx))).then(async r => {
    baseline = r.result;
    pubOrder = order(baseline, c => party(c).name);
    accepted = { state: PS.defaults(ctx), result: baseline };
    await geometryP;
    buildControls();
    R.engineRegion.setAttribute("data-ready", "");
    update();
  }, e => { R.engine.textContent = "The re-weighting code refused the published setting: " + e.message; });
}

const pct = x => Math.round(x * 100) + "%";
const signed = (x, unit = "") => (x > 0 ? "+" : x < 0 ? "−" : "") + Math.abs(x) + unit;

function buildControls() {
  // turnout: one slider per group, the published turnout beside it
  clear(R.turnout);
  ctx.pools.forEach((p, i) => {
    const input = el("input", { type: "range", id: "t-" + i, min: PS.TURNOUT.min, max: PS.TURNOUT.max, step: PS.TURNOUT.step,
      "aria-describedby": "ts-" + i + " turnout-why" });
    // a known stop holds the thumb at it: the zone beyond it is shaded
    input.addEventListener("input", () => {
      const g = "turnout:" + i, v = PS.heldAtStop(+input.value, limits[g]);
      if (v !== +input.value) input.value = v;
      if (v === st.shift[i]) { paintLimits(); return; }
      st.shift[i] = v;
      moved(g, true);
    });
    const value = el("span", { className: "pl-tval" });
    const scale = el("span", { className: "pl-cur", id: "ts-" + i });
    const zone = sv("svg", { class: "pl-zone", "aria-hidden": "true" });
    const row = el("div", { className: "pl-tslider" },
      el("label", { className: "pl-tlab", htmlFor: "t-" + i }, el("span", {}, p), value),
      el("div", { className: "pl-track" }, input, zone),
      el("div", { className: "pl-tscale" }, el("span", {}, signed(PS.TURNOUT.min)), scale, el("span", {}, signed(PS.TURNOUT.max))));
    groups["turnout:" + i] = row;
    inputs.turnout[i] = input;
    inputs.tlabel[i] = value;
    inputs.tscale[i] = scale;
    inputs.tzone[i] = zone;
    R.turnout.append(row);
  });
  // why a turnout slider stops, one line under the four (a reserved slot)
  inputs.twhy = el("p", { className: "pl-note pl-zonewhy yf-slot", id: "turnout-why" });
  R.turnout.append(inputs.twhy);
  R.turnout.setAttribute("data-ready", "");

  // the poll: none, or one of those the model's rules admit
  clear(R.polls);
  const option = (id, title, sub, caveat) => {
    const radio = el("input", { type: "radio", name: "poll", value: id });
    radio.addEventListener("change", () => {
      // a poll refused at the other settings stays unchosen, and its line says why
      if (unavailable.poll && unavailable.poll.value === id) { syncControls(); return; }
      st.polls = id ? [id] : [];
      if (!id) st.trust = 0;
      moved("poll", false);
    });
    inputs.poll.push(radio);
    const row = el("label", { className: "pl-popt" }, radio,
      el("span", { className: "pl-pmain" }, el("b", {}, title), el("span", { className: "pl-pnums" }, sub),
        caveat ? el("span", { className: "pl-pcav" }, caveat) : null));
    inputs.pollRow.push([row, radio, id]);
    return row;
  };
  R.polls.append(option("", "None", "As the forecast does"));
  for (const p of [...ctx.pollRows].sort((a, b) => String(b.fieldwork_end).localeCompare(String(a.fieldwork_end)))) {
    const nums = Object.entries(p.numbers || {}).sort((a, b) => party(a[0]).name.localeCompare(party(b[0]).name))
      .map(([c, v]) => party(c).name + " " + Math.round(v * 100)).join(" · ");
    R.polls.append(option(p.id, pollName(p), nums, p.caveat));
  }
  groups.poll = R.polls;

  clear(R.trust);
  const trust = el("input", { type: "range", id: "trust", min: PS.TRUST.min, max: PS.TRUST.max, step: PS.TRUST.step,
    "aria-describedby": "trust-why" });
  trust.addEventListener("input", () => {
    const v = PS.heldAtStop(+trust.value, limits.trust);
    if (v !== +trust.value) trust.value = v;
    if (v === st.trust) { paintLimits(); return; }
    st.trust = v;
    moved("trust", true);
  });
  inputs.trust = trust;
  inputs.trustv = el("output", { htmlFor: "trust", className: "pl-tval" });
  inputs.trustzone = sv("svg", { class: "pl-zone", "aria-hidden": "true" });
  // why the slider stops, or why a poll cannot be chosen (a reserved slot)
  inputs.trustwhy = el("p", { className: "pl-note pl-zonewhy yf-slot", id: "trust-why" });
  R.trust.append(el("label", { className: "pl-tlab", htmlFor: "trust" }, el("span", {}, "How much to believe it"), inputs.trustv),
    el("div", { className: "pl-track" }, trust, inputs.trustzone),
    el("div", { className: "pl-tscale" }, el("span", {}, PS.TRUST.min + ": ignore it"), el("span", {}, PS.TRUST.max + ": the model's error for this poll")),
    inputs.trustwhy);
  groups.trust = R.trust;

  // by-elections: three positions, the published one in the middle
  clear(R.cells);
  for (const c of ctx.cellRows) {
    const b = el("button", { type: "button", role: "radio" }, cellName(c));
    b.addEventListener("click", () => {
      if (unavailable.cell && unavailable.cell.value === c.path) { paintLimits(); return; }
      st.cell = c.path;
      moved("cell", false);
    });
    inputs.cells.push([b, c.path]);
    R.cells.append(b);
  }
  groups.cell = R.cells;

  clear(R.law);
  for (const k of ctx.laws) {
    const radio = el("input", { type: "radio", name: "law", value: k });
    radio.addEventListener("change", () => {
      if (unavailable.law && unavailable.law.value === k) { syncControls(); return; }
      st.law = k;
      moved("law", false);
    });
    inputs.law.push(radio);
    const t = lawText(k);
    const row = el("label", { className: "pl-popt" }, radio, el("span", { className: "pl-pmain" }, el("b", {}, t.label), el("span", { className: "pl-pnums" }, t.note)));
    inputs.lawRow.push([row, radio, k]);
    R.law.append(row);
  }
  groups.law = R.law;
  syncControls();
}

// Put every control and its echo in line with `st` (after a reset, a link, or a stop).
function syncControls() {
  const pub = baseline.turnout;
  ctx.pools.forEach((g, i) => {
    const x = st.shift[i];
    inputs.turnout[i].value = x;
    inputs.turnout[i].classList.toggle("pl-moved", x !== 0);
    clear(inputs.tlabel[i]);
    inputs.tlabel[i].append(pct(pub[g].published), ...(x ? [" → ", el("b", {}, pct(pub[g].published + x / 100))] : []));
    inputs.tscale[i].textContent = x ? signed(x, x === 1 || x === -1 ? " point" : " points") : "as forecast";
  });
  for (const r of inputs.poll) r.checked = r.value === (st.polls[0] || "");
  inputs.trust.value = st.trust;
  inputs.trust.disabled = !st.polls.length;
  R.trust.classList.toggle("pl-off", !st.polls.length);
  inputs.trustv.textContent = String(st.trust);
  for (const [b, path] of inputs.cells) b.setAttribute("aria-checked", String(path === st.cell));
  for (const r of inputs.law) r.checked = r.value === st.law;
  R.lawnow.textContent = lawText(st.law).label + (st.law === PS.PUBLISHED_LAW ? ", the law that seats the council" : ", for comparison");
  for (const [row, radio, id] of inputs.pollRow) markRefused(unavailable.poll, id, row, radio);
  for (const [b, path] of inputs.cells) markRefused(unavailable.cell, path, b, b);
  for (const [row, radio, k] of inputs.lawRow) markRefused(unavailable.law, k, row, radio);
  paintLimits();
}

// An option refused at the other settings: marked, and its reason as its title.
function markRefused(u, value, row, control) {
  const off = !!u && u.value === value;
  row.classList.toggle("pl-unavail", off);
  if (off) { control.setAttribute("aria-disabled", "true"); row.title = refusedWords(u); }
  else { control.removeAttribute("aria-disabled"); row.removeAttribute("title"); }
}

// ---------- stops and refusals, said where they happen ----------
// Each slider's shaded zones (play-state.js stopZones), as SVG rects over its
// track; the line under the turnout sliders and under the poll's slider; the
// seat law's line and the by-election line when an option there is refused.
function paintLimits() {
  if (!inputs.twhy) return;
  ctx.pools.forEach((p, i) => paintZone(inputs.tzone[i], PS.TURNOUT, limits["turnout:" + i]));
  paintZone(inputs.trustzone, PS.TRUST, limits.trust);
  inputs.twhy.textContent = ctx.pools.map((p, i) => (limitWhy["turnout:" + i] ? p + " turnout " + limitWhy["turnout:" + i] : null))
    .filter(Boolean).join(" ");
  inputs.trustwhy.textContent = [limitWhy.trust ? "Belief " + limitWhy.trust : null,
    unavailable.poll ? refusedWords(unavailable.poll) : null].filter(Boolean).join(" ");
  if (unavailable.law) R.lawnow.textContent = refusedWords(unavailable.law);
  if (unavailable.cell) R.bye.replaceChildren(el("p", { className: "pl-note" }, refusedWords(unavailable.cell)));
}
function paintZone(svg, bounds, limit) {
  svg.replaceChildren(...PS.stopZones(bounds, limit).map(z => sv("rect", { class: "pl-zrect",
    x: (z.from * 100).toFixed(2) + "%", y: 0, width: ((z.to - z.from) * 100).toFixed(2) + "%", height: "100%" })));
}
// "Germany 2015 is not available at these settings: <why>."
function refusedWords(u) {
  return optionName(u.group, u.value) + " is not available at these settings: " + u.why + ".";
}
function optionName(group, v) {
  if (group === "law") return lawText(v).label;
  if (group === "cell") {
    const c = ctx.cellRows.find(x => x.path === v);
    return "Counting by-elections \u201c" + (c ? cellName(c) : v) + "\u201d";
  }
  const p = ctx.pollRows.find(x => x.id === v);
  return "The poll " + (p ? pollName(p) : v);
}
// The value a discrete control was moved to, in a state.
const discreteValue = (group, s) => (group === "cell" ? s.cell : group === "law" ? s.law : s.polls[0] || "");
// A move of `group` leaves every other control's stop and refusal unknown.
function forgetOthers(group) {
  for (const m of [limits, limitWhy, unavailable]) for (const g of Object.keys(m)) if (g !== group) delete m[g];
}

// A seat law's name and what it does, as /forecast prints them (laws.json).
const lawText = k => ctx.laws_text[k] || { label: k, note: "" };

const copyState = s => ({ ...s, shift: s.shift.slice(), polls: s.polls.slice() });
// Section 1's part of the page's one address (yf-url.js).
function writeURL() { YU.write("adjust", PS.serialize(st, ctx)); }

function moved(group, debounce) {
  lastMoved = group;
  forgetOthers(group);
  syncControls();
  writeURL();
  clearTimeout(timer);
  if (debounce) timer = setTimeout(() => update(), DEBOUNCE_MS);
  else update();
}

function greyOnly(names) {
  for (const g of Object.values(groups)) g.classList.remove("pl-greyed");
  for (const n of names) groups[n]?.classList.add("pl-greyed");
}

// The floating indicator: shown while any computation is in flight. It is
// position: fixed (css/your-forecast.css), so it reserves no space and moves
// nothing.
let busyN = 0;
function busy(on) {
  busyN = Math.max(0, busyN + (on ? 1 : -1));
  R.busy.hidden = busyN === 0;
}
async function update() {
  busy(true);
  try { await compute(); } finally { busy(false); }
}

async function compute() {
  if (!ctx || !baseline) return;
  const touched = PS.isTouched(st);
  greyOnly([]);
  R.engine.classList.remove("pl-low");
  if (!touched) {
    accepted = { state: copyState(st), result: baseline };
    R.engine.textContent = "";
    render(baseline, false);
    return;
  }
  R.engine.textContent = "";
  // The settings this result is FOR. A control moved during the await changes
  // `st`, and that move schedules its own update: this result is then stale,
  // and is dropped rather than shown (or shared) beside the newer settings.
  const asked = copyState(st);
  let m;
  try { m = await ask(PS.engineSettings(asked)); }
  catch (e) { if (e.message !== "superseded") R.engine.textContent = "The re-weighting code refused: " + e.message; return; }
  if (PS.serialize(st, ctx) !== PS.serialize(asked, ctx)) return;
  const r = m.result;
  const bad = whyNot(r);
  if (bad && lastMoved && accepted) {
    // The control stops at the FURTHEST setting every shown figure passes, not
    // back at the last accepted one (owner, 2026-09-30): a slider is bisected
    // between its accepted and requested positions, on its own step, and the
    // zone beyond the setting it reaches is shaded with the reason under it.
    // A discrete control (seat law, the poll, a by-election cell) returns to
    // its last option, and the option refused is marked with the reason
    // beside the control (owner, 2026-10-05: never a silent stop). The
    // reason is the one for the setting just past the stop.
    const which = lastMoved;
    let stop = { state: copyState(accepted.state), result: accepted.result }, why = bad;
    const slider = which === "trust" ? { get: s => s.trust, set: (s, v) => { s.trust = v; }, step: PS.TRUST.step }
      : which.startsWith("turnout:") ? (i => ({ get: s => s.shift[i], set: (s, v) => { s.shift[i] = v; }, step: PS.TURNOUT.step }))(Number(which.split(":")[1]))
      : null;
    if (slider) {
      const from = slider.get(accepted.state), to = slider.get(st);
      const dir = Math.sign(to - from), n = Math.round(Math.abs(to - from) / slider.step);
      let lo = 0, hi = n;
      while (hi - lo > 1) {
        const mid = (lo + hi) >> 1;
        const trial = copyState(accepted.state);
        slider.set(trial, from + dir * mid * slider.step);
        let tr;
        try { tr = (await ask(PS.engineSettings(trial))).result; }
        catch (e) { if (e.message === "superseded") return; throw e; }
        if (PS.serialize(st, ctx) !== PS.serialize(asked, ctx)) return;   // moved meanwhile
        if (!whyNot(tr)) { lo = mid; stop = { state: trial, result: tr }; }
        else { hi = mid; why = whyNot(tr); }
      }
      if (lo > 0) accepted = { state: copyState(stop.state), result: stop.result };
      const reach = slider.get(stop.state);
      limits[which] = PS.withStop(limits[which], dir, reach);
      limitWhy[which] = "stops at " + (which === "trust" ? String(reach) : signed(reach, Math.abs(reach) === 1 ? " point" : " points")) +
        ": past it, " + why + ".";
    } else {
      unavailable[which] = { group: which, value: discreteValue(which, asked), why };
    }
    st = copyState(stop.state);
    syncControls();
    writeURL();
    render(stop.result, PS.isTouched(st), stop.state);
    return;
  }
  if (r.refused) {
    // A link opened past the floor has no last move: every control away from
    // the published setting greys, and the published forecast stays shown.
    greyOnly([...st.shift.map((x, i) => x !== 0 ? "turnout:" + i : null),
      st.trust && st.polls.length ? "trust" : null,
      st.cell !== PS.PUBLISHED_CELL ? "cell" : null, st.law !== PS.PUBLISHED_LAW ? "law" : null].filter(Boolean));
    R.engine.textContent = "At these settings " + tooFew(r) +
      ". Move the greyed control back towards the published setting.";
    R.engine.classList.add("pl-low");
    render(baseline, false, asked);
    return;
  }
  if (r.within_precision) accepted = { state: copyState(asked), result: r };
  R.engine.textContent = "";
  render(r, true, asked);
}

// Why a result cannot be shown, in the page's words, or null when it can:
// below the effective-draw floor, or a figure past the precision ceiling
// (page.py returns reweight.MAX_FIGURE_SE_SEATS beside the result).
// Short, because it is said in the line beside the control (a reserved slot).
function whyNot(r) {
  if (r.refused) return r.effective_draws != null && r.draws
    ? "too few simulations lie near (the equivalent of " + count(r.effective_draws) + "; a figure needs " + count(r.floor) + ")"
    : "the re-weighting refuses it (" + r.refused + ")";
  if (r.within_precision === false) return "a seat figure would be known to worse than ±" + r.max_figure_se + " seats";
  return null;
}

// The local date, YYYY-MM-DD, built by hand: a locale's own format varies.
const two = n => String(n).padStart(2, "0");
const today = (d = new Date()) => d.getFullYear() + "-" + two(d.getMonth() + 1) + "-" + two(d.getDate());

// The share sheet is handed the result the page shows, never a second
// computation, with the settings that result was computed for (not whatever
// `st` holds by then): its image and its link carry the same setting. The
// untouched page shares the published result.
function offerShare(r, state) {
  setShareable({ url: new URL(location.pathname + PS.serialize(state, ctx), location.href).href,
                 r, st: copyState(state), ctx, party, made: today(), when: WHEN,
                 geometry: geometry && { ...geometry, step: geometry.step, rotate: geometry.rotate },
                 touched: PS.isTouched(state),
                 shareable: PS.shareable(state), lawName: lawText(PS.PUBLISHED_LAW).label,
                 onName: name => { st.name = name; YU.write("name", name); } });
}

// ---------- figures ----------

// A count as the site prints counts: "5,000", one format on the page.
const count = n => Math.round(n).toLocaleString("en-US");
// Why a setting is refused, in the page's words (page.py returns the counts
// beside reweight's own reason; a refusal of another kind keeps that reason).
const tooFew = r => (r.effective_draws != null && r.draws
  ? "the figures would rest on the equivalent of " + count(r.effective_draws) + " of the " + count(r.draws) +
    " simulations, fewer than the " + count(r.floor) + " a figure needs"
  : "the re-weighting refuses it (" + r.refused + ")");
// The reader's change against the published forecast: the site's one arrow
// (src/css/stat.css .arrow), in the reader's hue.
const arrowText = d => (d ? (d > 0 ? "▲" : "▼") + Math.abs(d) : null);
const arrow = d => (d ? el("span", { className: "arrow reader" }, arrowText(d)) : null);

function render(r, touched, state = st) {
  offerShare(r, state);
  told(state);
  const moves = changes(r);
  if (touched) R.result.setAttribute("data-touched", "");
  else R.result.removeAttribute("data-touched");
  R.status.hidden = !touched;
  if (!touched) {
    for (const n of [R.banner, R.oneline, R.map, R.flips, R.seats, R.bye, R.ess]) clear(n);
    R.seats.removeAttribute("data-extra");
    R.settings.textContent = "";
    showToast(moves);
    paintLimits();
    return;
  }
  R.settings.textContent = "Your changes: " + settingsWords(state, ctx).join("; ") + ".";
  renderBanner(r, moves);
  renderResult(r);
  renderMap(r);
  renderFlips(r);
  renderSeats(r, moves);
  renderBye(r);
  showToast(moves);
  R.ess.textContent = "At your settings the figures rest on the equivalent of " +
    count(r.effective_draws) + " equally weighted simulations.";
  paintLimits();
}

function renderBanner(r, moves) {
  clear(R.banner);
  const items = pubOrder.filter(c => r.seats[c]).slice(0, 6).map(c => {
    const s = r.seats[c];
    return cue(el("span", { className: "pl-bi" }, el("i", { className: "pc-" + c }), party(c).name + " ",
      el("b", {}, seatText(s.median)), arrow(s.vs_published)), moves.get(c));
  });
  R.banner.append(el("span", { className: "pl-bstate pl-mine" }, "Your changes"), el("span", { className: "pl-bitems" }, ...items),
    el("span", { className: "pl-bmaj" }, "Majority " + seatText({ value: r.majority })));
}

function renderResult(r) {
  clear(R.oneline);
  // every share in the text page.py returns (reweight.chance_text, the
  // format the published twin's tokens use)
  const top = largestTop(r, party);
  // the site's one wording for it (play-card.js largestLine): "Most seats alone: 47% chance it's …"
  const share = c => [r.largest[c].text, arrow(r.largest[c].vs_published)];
  R.oneline.append(...["Most seats alone: ", ...share(top[0]), " chance it's " + theName(top[0], party) + ", ",
    ...share(top[1]), " chance it's " + theName(top[1], party) + ". Two or more parties tie for the most seats: " + r.tied.text,
    arrow(r.tied.vs_published), " chance. One party wins a majority on its own: " + r.alone.text + " chance."].filter(x => x != null));
  const said = order(r, c => party(c).name).slice(0, 5).map(c => party(c).name + " " + seatText(r.seats[c].median)).join(", ");
  if (R.announce.textContent !== said) R.announce.textContent = said;
}

// The map under the reader's weights: every ward's fill and stripes from
// page.py (render_map.ward_call), outlined where its most likely winner
// differs from the published forecast's.
function renderMap(r) {
  clear(R.map);
  if (!geometry) { R.map.append(el("p", { className: "pl-note" }, "The ward boundaries did not load, so the map under your settings cannot be drawn.")); return; }
  const flipped = new Set(r.flips.map(f => f.ward));
  const defs = sv("defs"), fills = [], hatches = [], rings = [];
  for (const w of r.wards) {
    const d = geometry.paths[w.ward];
    if (!d) continue;
    fills.push(sv("path", { d, fill: w.fill, stroke: "var(--paper)", "stroke-width": 0.8, "data-w": w.ward }));
    if (w.bands) {
      const id = "lv-" + w.ward;
      defs.append(sv("pattern", { id, width: geometry.step, height: geometry.step, patternTransform: "rotate(" + geometry.rotate + ")", patternUnits: "userSpaceOnUse" },
        ...w.bands.map(b => sv("line", { x1: b.x, y1: 0, x2: b.x, y2: geometry.step, stroke: b.colour, "stroke-width": b.w }))));
      hatches.push(sv("path", { d, fill: "url(#" + id + ")", "pointer-events": "none" }));
    }
    if (flipped.has(w.ward)) rings.push(sv("path", { d, fill: "none", class: "pl-ring", "pointer-events": "none" }));
  }
  const places = geometry.places.map(l => sv("text", { x: l.x, y: l.y, "text-anchor": "middle", class: "pl-maplabel" }, l.t));
  R.map.append(sv("svg", { class: "pl-wardmap", viewBox: "0 0 " + Math.round(geometry.W) + " " + Math.round(geometry.H), role: "img",
    "aria-label": "Johannesburg wards under your settings, north to the right, coloured by the party that wins each" },
  defs, ...fills, ...hatches, ...rings, ...places,
  sv("text", { x: Math.round(geometry.W) - 14, y: 20, "text-anchor": "end", class: "pl-north" }, "N ↗")));
  tips = Object.fromEntries(r.wards.map(w => [w.ward, w.tip]));
}

let tips = {};
function showTip(e) {
  const w = e.target.getAttribute && e.target.getAttribute("data-w");
  if (!w || !tips[w]) { R.wardtip.hidden = true; return; }
  R.wardtip.textContent = tips[w];
  R.wardtip.hidden = false;
  placeTip(R.wardtip, e.clientX, e.clientY);
}
R.map.addEventListener("mousemove", showTip);
R.map.addEventListener("click", showTip);
R.map.addEventListener("mouseleave", () => { R.wardtip.hidden = true; });

function renderFlips(r) {
  clear(R.flips);
  if (!r.flips.length) return;
  const by = new Map();
  for (const f of r.flips) {
    const k = f.from + ">" + f.to;
    if (!by.has(k)) by.set(k, { from: f.from, to: f.to, wards: [] });
    by.get(k).wards.push(f.ward);
  }
  const parts = [...by.values()]
    .sort((a, b) => party(a.from).name.localeCompare(party(b.from).name) || party(a.to).name.localeCompare(party(b.to).name))
    .map(g => party(g.from).name + " to " + party(g.to).name + " in " + g.wards.length + " (" + g.wards.sort((a, b) => a - b).join(", ") + ")");
  const n = r.flips.length;
  R.flips.append(el("p", { className: "pl-flipline" }, el("span", { className: "pl-kring" }),
    el("b", {}, n + (n === 1 ? " ward changes its" : " wards change their") + " most likely winner."), " " + parts.join("; ") + "."));
}

// The seat rows: the published rows and any party the reader's settings lift
// to the threshold (page.py's `shown`), in the page's order, then Others. The
// site's one seat table (js/seat-table.js), with the published middle as a
// dotted mark and the change against it as an arrow.
function renderSeats(r, moves) {
  clear(R.seats);
  const pub = baseline.seats;
  const val = f => (f.withheld ? null : f.value);
  const rows = [...order(r, c => party(c).name), "OTHERS"].map(c => {
    const s = r.seats[c], others = c === "OTHERS";
    const range = s.p5.withheld || s.p95.withheld;
    return {
      code: c, name: nameOf(c), sub: others ? "(" + r.others_count + " parties)" : null,
      seats: seatText(s.median), lo: range ? rangeText(s) : seatText(s.p5), hi: range ? null : seatText(s.p95),
      m: val(s.median), p5: range ? null : val(s.p5), p95: range ? null : val(s.p95),
      ghost: !others && pub[c] ? val(pub[c].median) : null,
      arrow: others ? null : arrowText(s.vs_published), title: null,
    };
  });
  const table = seatTable(document, rows, TABLE);
  // the ▲/▼ goes in the seats cell, over its corner: it moves no figure
  for (const row of table.children) if (row.dataset.code) cue(row, moves.get(row.dataset.code), row.children[2]);
  // the rows the reader's settings add to the published forecast's: their
  // room is reserved under the table (css/your-forecast.css), so a row that
  // comes or goes moves nothing below it
  R.seats.setAttribute("data-extra", String(r.shown.filter(c => !baseline.shown.includes(c)).length));
  R.seats.append(table);
}

// ---------- change cues ----------
// Each party's middle seat count, rounded, as last shown (the published
// forecast's until a control moves). `changes` returns the parties whose
// figure moved since then, with the move; nothing on first paint.
let lastShown = null;
function changes(r) {
  const now = new Map(Object.entries(r.seats).filter(([c, s]) => c !== "OTHERS" && !s.median.withheld)
    .map(([c, s]) => [c, Math.round(s.median.value)]));
  const out = new Map();
  if (lastShown) for (const [c, v] of now) if (lastShown.has(c) && v !== lastShown.get(c)) out.set(c, v - lastShown.get(c));
  lastShown = now;
  return out;
}
// An element that moved: it pulses once (css/your-forecast.css .yf-cue), with
// a ▲ or ▼ for the direction of this move.
function cue(node, d, at = node) {
  if (!d) return node;
  node.classList.add("yf-cue", d > 0 ? "yf-up" : "yf-down");
  at.append(el("span", { className: "yf-spark", "aria-hidden": "true" }, d > 0 ? "▲" : "▼"));
  return node;
}
// The phone's toast: when the seat table is out of view on a narrow screen,
// the parties whose seats moved, each with its logo (or colour) and the move.
let seatsInView = true, toastTimer = null;
new IntersectionObserver(es => { seatsInView = es.some(e => e.isIntersecting); }).observe(R.seats);
const narrow = window.matchMedia("(max-width: 1099px)");
function showToast(moves) {
  clearTimeout(toastTimer);
  if (!moves.size || seatsInView || !narrow.matches) { R.toast.hidden = true; return; }
  const items = [...moves].sort((a, b) => party(a[0]).name.localeCompare(party(b[0]).name)).map(([c, d]) =>
    el("span", { className: "yf-ti" },
      party(c).logo ? el("img", { className: "yf-tlogo", src: new URL("../../logos/" + c + ".png", import.meta.url).href, alt: "" })
        : el("i", { className: "pc-" + c }),
      party(c).name + " ", el("span", { className: "arrow reader" }, arrowText(d))));
  R.toast.replaceChildren(el("span", { className: "yf-thead" }, "Since your last change"), ...items);
  R.toast.hidden = false;
  toastTimer = setTimeout(() => { R.toast.hidden = true; }, 3500);
}

// Under a by-election setting other than the forecast's: each party's change
// in middle seats against the forecast's weight AT THESE SETTINGS, where it
// is larger than the two runs' sampling noise (page.py, reweight.beyond_noise).
function renderBye(r) {
  clear(R.bye);
  const cmp = r.against_published_cell;
  if (!cmp) return;
  const moves = Object.entries(cmp).filter(([, d]) => !d.within_noise && Math.round(d.difference))
    .sort((a, b) => party(a[0]).name.localeCompare(party(b[0]).name))
    .map(([c, d]) => party(c).name + " " + signed(Math.round(d.difference)));
  R.bye.append(el("p", { className: "pl-note" }, "At your settings, against the forecast's weight: " +
    (moves.length ? moves.join(", ") : "no change larger than sampling noise") + "."));
}

R.back.addEventListener("click", () => {
  if (!ctx) return;
  const name = st.name;
  st = { ...PS.defaults(ctx), name };
  lastMoved = null;
  forgetOthers(null);
  syncControls();
  writeURL();
  update();
});
