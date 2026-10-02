// "Play with the model": the page. It holds the controls and writes the figures
// the model's Python returns; it computes none of them.
//
// Every figure a control produces is computed by src/reweight.py, through
// pyboot/page.py, under Pyodide, in a Web Worker (js/model-worker.js; SPEC-v2
// Lane P, F11), and every ward is coloured by src/render_map.py's ward_call
// there too. There is no re-weighting and no drawing rule in JavaScript: one
// definition, in Python (INTEGRATION §3b). What is here is presentation:
// rounding a figure for print, placing a bar, and an arrow for a change
// page.py has already computed.
//
// ⛔ THE ONE MODULE THAT WRITES THE PAGE'S FIGURES, and the path listed for it
// in stats.LIVE_WRITERS ("play/js/model.js"), with the LIVE regions it may
// write. The build refuses the page (stats.script_writes) unless this file
// keeps the writer contract:
//   * it reaches the page ONLY through literal '[data-live="<name>"] …'
//     selectors, each for a region listed for it, all taken once, below;
//   * it writes with textContent, createElement(NS) and append; never markup;
//   * it does not walk out of a region (no parent, sibling or document-level
//     handles), and writes nothing through an event's target.
// Its imports: play-state.js is scanned as a NON-writer; play-card.js (the
// party order, seat format and setting names it shares with the share image)
// and play-share.js (region "share") are writers in their own right.
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

import * as PS from "./play-state.js";
import { order, seatText, LAW_TEXT, cellName, pollName, settingsWords, largestTop } from "./play-card.js";
import { setShareable } from "./play-share.js";

const DEBOUNCE_MS = 200;
const SVG = "http://www.w3.org/2000/svg";

// Every element this module touches, each by a literal LIVE selector.
const R = {
  engineRegion: document.querySelector('[data-live="engine"]'),
  engine: document.querySelector('[data-live="engine"] .pl-engine'),
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
    if (k === "style") e.style.cssText = v;
    else if (k.includes("-") || k === "role" || k === "for") e.setAttribute(k, v === true ? "" : String(v));
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

// The seat axis, set by the build on the "seats" region (build_play.SEAT_SCALE).
const SCALE = Number(R.seats.dataset.scale) || 125;
const TICKS = [0, 0.2, 0.4, 0.6, 0.8, 1].map(f => Math.round(SCALE * f));
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
const inputs = { turnout: [], tlabel: [], tscale: [], poll: [], law: [], cells: [] };

const geometryP = fetch(new URL("../ward_paths.json", import.meta.url))
  .then(r => (r.ok ? r.json() : null)).catch(() => null)
  .then(g => { geometry = g; return g; });

function ask(settings) {
  const id = ++seq;
  worker.postMessage({ type: "compute", seq: id, settings });
  return new Promise((ok, no) => pending.set(id, { ok, no }));
}

worker.onmessage = e => {
  const m = e.data;
  if (m.type === "stage") R.engine.textContent = m.label + "…";
  else if (m.type === "failed") {
    R.engine.textContent = m.missing ? m.message : "The re-weighting code did not load: " + m.message + ". The published forecast is shown.";
    R.engine.classList.add("pl-low");
  } else if (m.type === "ready") ready(m);
  else if (m.type === "result" || m.type === "error") {
    const p = pending.get(m.seq);
    pending.delete(m.seq);
    // an older request superseded by a newer one is dropped, not shown
    for (const k of [...pending.keys()]) if (k < m.seq) { pending.get(k).no(new Error("superseded")); pending.delete(k); }
    if (p) m.type === "result" ? p.ok(m) : p.no(new Error(m.message));
  }
};

// ---------- controls ----------
function ready(m) {
  const cells = [...m.cells].sort((a, b) => a.w_bye - b.w_bye);
  roster = m.parties || {};
  ctx = { pools: m.pools, polls: m.polls.map(p => p.id), pollRows: m.polls, laws: m.laws,
          cells: cells.map(c => c.path), cellRows: cells, modelVersion: m.modelVersion };
  window.__playEngineTimes = m.times;
  const parsed = PS.parse(location.search, ctx);
  st = parsed.state;
  const notes = [];
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
      "aria-describedby": "ts-" + i });
    input.addEventListener("input", () => { st.shift[i] = +input.value; moved("turnout:" + i, true); });
    const value = el("span", { className: "pl-tval" });
    const scale = el("span", { className: "pl-cur", id: "ts-" + i });
    const row = el("div", { className: "pl-tslider" },
      el("label", { className: "pl-tlab", htmlFor: "t-" + i }, el("span", {}, p), value),
      input,
      el("div", { className: "pl-tscale" }, el("span", {}, signed(PS.TURNOUT.min)), scale, el("span", {}, signed(PS.TURNOUT.max))));
    groups["turnout:" + i] = row;
    inputs.turnout[i] = input;
    inputs.tlabel[i] = value;
    inputs.tscale[i] = scale;
    R.turnout.append(row);
  });
  R.turnout.setAttribute("data-ready", "");

  // the poll: none, or one of those the model's rules admit
  clear(R.polls);
  const option = (id, title, sub, caveat) => {
    const radio = el("input", { type: "radio", name: "poll", value: id });
    radio.addEventListener("change", () => {
      st.polls = id ? [id] : [];
      if (!id) st.trust = 0;
      moved("poll", false);
    });
    inputs.poll.push(radio);
    return el("label", { className: "pl-popt" }, radio,
      el("span", { className: "pl-pmain" }, el("b", {}, title), el("span", { className: "pl-pnums" }, sub),
        caveat ? el("span", { className: "pl-pcav" }, caveat) : null));
  };
  R.polls.append(option("", "None", "As the forecast does"));
  for (const p of [...ctx.pollRows].sort((a, b) => String(b.fieldwork_end).localeCompare(String(a.fieldwork_end)))) {
    const nums = Object.entries(p.numbers || {}).sort((a, b) => party(a[0]).name.localeCompare(party(b[0]).name))
      .map(([c, v]) => party(c).name + " " + Math.round(v * 100)).join(" · ");
    R.polls.append(option(p.id, pollName(p), nums, p.caveat));
  }
  groups.poll = R.polls;

  clear(R.trust);
  const trust = el("input", { type: "range", id: "trust", min: PS.TRUST.min, max: PS.TRUST.max, step: PS.TRUST.step });
  trust.addEventListener("input", () => { st.trust = +trust.value; moved("trust", true); });
  inputs.trust = trust;
  inputs.trustv = el("output", { htmlFor: "trust", className: "pl-tval" });
  R.trust.append(el("label", { className: "pl-tlab", htmlFor: "trust" }, el("span", {}, "How much to believe it"), inputs.trustv), trust,
    el("div", { className: "pl-tscale" }, el("span", {}, PS.TRUST.min + ": ignore it"), el("span", {}, PS.TRUST.max + ": the model's error for this poll")));
  groups.trust = R.trust;

  // by-elections: three positions, the published one in the middle
  clear(R.cells);
  for (const c of ctx.cellRows) {
    const b = el("button", { type: "button", role: "radio" }, cellName(c));
    b.addEventListener("click", () => { st.cell = c.path; moved("cell", false); });
    inputs.cells.push([b, c.path]);
    R.cells.append(b);
  }
  groups.cell = R.cells;

  clear(R.law);
  for (const k of ctx.laws) {
    const radio = el("input", { type: "radio", name: "law", value: k });
    radio.addEventListener("change", () => { st.law = k; moved("law", false); });
    inputs.law.push(radio);
    const [short, long] = LAW_TEXT[k] || [k, ""];
    R.law.append(el("label", { className: "pl-popt" }, radio, el("span", { className: "pl-pmain" }, el("b", {}, short), el("span", { className: "pl-pnums" }, long))));
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
  const [short] = LAW_TEXT[st.law] || [st.law];
  R.lawnow.textContent = st.law === PS.PUBLISHED_LAW ? short + ", as the law says" : short + ", not the law";
}

const copyState = s => ({ ...s, shift: s.shift.slice(), polls: s.polls.slice() });
function writeURL() { history.replaceState(null, "", location.pathname + PS.serialize(st, ctx) + location.hash); }

function moved(group, debounce) {
  lastMoved = group;
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

async function update() {
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
  R.engine.textContent = "Computing…";
  // The settings this result is FOR. A control moved during the await changes
  // `st`, and that move schedules its own update: this result is then stale,
  // and is dropped rather than shown (or shared) beside the newer settings.
  const asked = copyState(st);
  let m;
  try { m = await ask(PS.engineSettings(asked)); }
  catch (e) { if (e.message !== "superseded") R.engine.textContent = "The re-weighting code refused: " + e.message; return; }
  if (PS.serialize(st, ctx) !== PS.serialize(asked, ctx)) return;
  const r = m.result;
  const bad = r.refused ? tooFew(r)
    : r.within_precision === false ? "a figure on this page would be known to worse than ±" + r.max_figure_se + " seats" : null;
  if (bad && lastMoved && accepted) {
    // The control stops at the FURTHEST setting every shown figure passes, not
    // back at the last accepted one (owner, 2026-09-30): a slider is bisected
    // between its accepted and requested positions, on its own step. A
    // discrete control (seat law, the poll, a by-election cell) reverts.
    const which = lastMoved;
    let stop = { state: copyState(accepted.state), result: accepted.result };
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
        if (!tr.refused && tr.within_precision !== false) { lo = mid; stop = { state: trial, result: tr }; }
        else hi = mid;
      }
      if (lo > 0) accepted = { state: copyState(stop.state), result: stop.result };
    }
    st = copyState(stop.state);
    syncControls();
    writeURL();
    render(stop.result, PS.isTouched(st), stop.state);
    greyOnly([which]);
    R.engine.textContent = "The greyed control stops here: one step further and " + bad + "." +
      (which === "trust" ? " That says where the simulations lie, not how good the poll is." : "");
    R.engine.classList.add("pl-low");
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
                 onName: name => { st.name = name; writeURL(); } });
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
const arrow = d => (d ? el("span", { className: "pl-delta" }, (d > 0 ? "▲" : "▼") + Math.abs(d)) : null);

function render(r, touched, state = st) {
  offerShare(r, state);
  if (touched) R.result.setAttribute("data-touched", "");
  else R.result.removeAttribute("data-touched");
  R.status.hidden = !touched;
  if (!touched) {
    for (const n of [R.banner, R.oneline, R.map, R.flips, R.seats, R.bye, R.ess]) clear(n);
    R.settings.textContent = "";
    return;
  }
  R.settings.textContent = "Your settings: " + settingsWords(state, ctx).join("; ") + ".";
  renderBanner(r);
  renderResult(r);
  renderMap(r);
  renderFlips(r);
  renderSeats(r);
  renderBye(r);
  R.ess.textContent = "At your settings the figures rest on the equivalent of " +
    count(r.effective_draws) + " equally weighted simulations.";
}

function renderBanner(r) {
  clear(R.banner);
  const items = pubOrder.filter(c => r.seats[c]).slice(0, 6).map(c => {
    const s = r.seats[c];
    return el("span", { className: "pl-bi" }, el("i", { style: "background:" + party(c).colour }), party(c).name + " ",
      el("b", {}, seatText(s.median)), arrow(s.vs_published));
  });
  R.banner.append(el("span", { className: "pl-bstate pl-mine" }, "Your settings"), el("span", { className: "pl-bitems" }, ...items),
    el("span", { className: "pl-bmaj" }, "Majority " + seatText({ value: r.majority })));
}

function renderResult(r) {
  clear(R.oneline);
  // every share in the text page.py returns (reweight.chance_text, the
  // format the published twin's tokens use)
  const top = largestTop(r, party);
  const part = c => [party(c).article + party(c).name + " in " + r.largest[c].text, arrow(r.largest[c].vs_published)];
  R.oneline.append(...["Largest party: ", ...part(top[0]), " of simulations, ", ...part(top[1]),
    ". Two or more parties tie for the most seats in " + r.tied.text, arrow(r.tied.vs_published),
    ". One party wins a majority on its own in " + r.alone.text + "."].filter(x => x != null));
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
  R.wardtip.style.left = Math.min(e.clientX + 14, window.innerWidth - 290) + "px";
  R.wardtip.style.top = (e.clientY + 14) + "px";
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
// to the threshold (page.py's `shown`), in the page's order, then Others.
function renderSeats(r) {
  clear(R.seats);
  const at = v => (100 * v / SCALE).toFixed(2) + "%";
  const pub = baseline.seats;
  for (const c of [...order(r, c => party(c).name), "OTHERS"]) {
    const s = r.seats[c], colour = c === "OTHERS" ? "#8b918b" : party(c).colour;
    const track = el("div", { className: "pl-track" });
    if (!s.p5.withheld && !s.p95.withheld)
      track.append(el("span", { className: "pl-band", style: "left:" + at(s.p5.value) + ";width:" + at(s.p95.value - s.p5.value) + ";background:" + colour }));
    if (pub[c] && !pub[c].median.withheld && c !== "OTHERS")
      track.append(el("span", { className: "pl-ghost", style: "left:calc(" + at(pub[c].median.value) + " - 1px)" }));
    if (!s.median.withheld)
      track.append(el("span", { className: "pl-med", style: "left:calc(" + at(s.median.value) + " - 1.5px)" }));
    const label = c === "OTHERS" ? [el("span", { className: "pl-chip", style: "background:" + colour }), "Others ", el("span", { className: "pl-sub" }, "(" + r.others_count + ")")]
      : [el("span", { className: "pl-chip", style: "background:" + colour }), party(c).name];
    R.seats.append(el("div", { className: "pl-srow" }, el("div", { className: "pl-sname" }, ...label), track,
      el("div", { className: "pl-sval" }, el("b", {}, seatText(s.median)), c === "OTHERS" ? null : arrow(s.vs_published),
        el("span", { className: "pl-rng" }, s.p5.withheld || s.p95.withheld ? "withheld" : seatText(s.p5) + "–" + seatText(s.p95)))));
  }
  R.seats.append(el("div", { className: "pl-srow pl-axis" }, el("div"),
    el("div", { className: "ticks pl-ticks" }, ...TICKS.map(t => el("span", { style: "left:" + at(t) }, String(t)))), el("div")));
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
  syncControls();
  writeURL();
  update();
});
