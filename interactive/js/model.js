// "Play with the model": the page. It holds the controls and writes the figures
// the model's Python returns; it computes none of them.
//
// Every figure a control produces is computed by src/reweight.py, through
// pyboot/page.py, under Pyodide, in a Web Worker (js/model-worker.js; SPEC-v2
// Lane P, F11). There is no re-weighting in JavaScript: one definition, in
// Python (INTEGRATION §3b).
//
// ⛔ THE ONE MODULE THAT WRITES FIGURES, and the path listed for it in
// stats.LIVE_WRITERS ("play/js/model.js"), with the LIVE regions it may write.
// The build refuses the page (stats.script_writes) unless this file keeps the
// writer contract:
//   * it reaches the page ONLY through literal '[data-live="<name>"] …'
//     selectors, each for a region listed for it, all taken once, below;
//   * it writes with textContent, createElement and append; never markup;
//   * it does not walk out of a region (no parent, sibling or document-level
//     handles), and writes nothing through an event's target.
// Each region holds no digits at build time and carries the visible label
// "Computed in your browser from your settings" (SPEC-v2 decision 1).
// The only module it imports, play-state.js, is scanned as a NON-writer.
//
// First paint (F6): the published forecast's panels, rendered by build_site as
// ledgered tokens, and no Python. The seat table fills in only once a control
// moves away from the published setting; setting data-touched on the seats
// region then hides the published seat panel and shows the note that the other
// panels are of the published forecast (F14), by CSS (css/interactive.css),
// because those panels hold tokens and are not regions this module may reach.
//
// Precision (DESIGN-decided §15): every range shows its ± seats, and a move that
// would leave any figure shown known to worse than reweight.MAX_FIGURE_SE_SEATS
// stops: the control returns to the last setting for which page.py's
// reweight.within_precision held.

import * as PS from "./play-state.js";

const DEBOUNCE_MS = 200;

// Every element this module touches, each by a literal LIVE selector.
const R = {
  engine: document.querySelector('[data-live="engine"] .ess'),
  linknote: document.querySelector('[data-live="engine"] .linknote'),
  turnrange: document.querySelector('[data-live="turnout"] .turnrange'),
  sliders: document.querySelector('[data-live="turnout"] .sliders'),
  turnpin: document.querySelector('[data-live="turnout"] .turnpin'),
  polls: document.querySelector('[data-live="polls"] table'),
  trustGroup: document.querySelector('[data-live="trust"] .slider'),
  trust: document.querySelector('[data-live="trust"] input'),
  trustv: document.querySelector('[data-live="trust"] output'),
  pollavg: document.querySelector('[data-live="poll-average"] .pollavg'),
  cells: document.querySelector('[data-live="cells"] .seg'),
  bye: document.querySelector('[data-live="byelection"] table'),
  law: document.querySelector('[data-live="law"]'),
  ess: document.querySelector('[data-live="effective-draws"] .ess'),
  seatsRegion: document.querySelector('[data-live="seats"]'),
  seats: document.querySelector('[data-live="seats"] table'),
  bandnote: document.querySelector('[data-live="seats"] .bandnote'),
  announce: document.querySelector('[data-live="seats"] .announce'),
  tomake: document.querySelector('[data-live="actions"] .tomake'),
  reset: document.querySelector('[data-live="actions"] .reset'),
  copylink: document.querySelector('[data-live="actions"] .copylink'),
  tomakenote: document.querySelector('[data-live="actions"] .tomakenote'),
  summary: document.querySelector('[data-live="summary"] .sumrow'),
};

// A new element: properties, attributes (keys with a dash) and children.
function el(tag, props = {}, ...kids) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (v == null || v === false) continue;
    if (k === "style") e.style.cssText = v;
    else if (k.includes("-") || k === "role" || k === "scope" || k === "colspan") e.setAttribute(k, v === true ? "" : String(v));
    else e[k] = v;
  }
  e.append(...kids.filter(k => k != null && k !== false));
  return e;
}
const clear = node => node.replaceChildren();

// Party names and colours arrive with the engine (model-worker.js roster()).
let roster = {};
const party = c => roster[c] ?? { code: c, name: c.replace(/_/g, " ").toLowerCase().replace(/(^|\s)\S/g, m => m.toUpperCase()), colour: "var(--ink-3)" };
const swatch = c => el("span", { style: `display:inline-block;width:10px;height:10px;border-radius:50%;background:${party(c).colour};margin-right:6px` });

// ---------- the engine ----------
const worker = new Worker(new URL("./model-worker.js", import.meta.url), { type: "module" });
let ctx = null, st = null, seq = 0, lastMoved = null, baseline = null, timer = null, lastResult = null;
let accepted = null;          // { state, result }: the last setting every shown figure passed
let evidence = null;
const pending = new Map();
const groups = {};            // control group -> the element that greys
const inputs = { turnout: [], echo: [], polls: [], law: [] };   // the controls, as created

function ask(settings) {
  const id = ++seq;
  worker.postMessage({ type: "compute", seq: id, settings });
  return new Promise((ok, no) => pending.set(id, { ok, no }));
}

worker.onmessage = e => {
  const m = e.data;
  if (m.type === "stage") R.engine.textContent = `${m.label}…`;
  else if (m.type === "failed") {
    R.engine.textContent = m.missing ? m.message : `The model's Python did not load: ${m.message}. The published forecast is shown.`;
    R.engine.classList.add("low");
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
  evidence = m.byelection;
  ctx = { pools: m.pools, polls: m.polls.map(p => p.id), pollRows: m.polls, laws: m.laws,
          cells: cells.map(c => c.path), cellRows: cells, modelVersion: m.modelVersion };
  window.__playEngineTimes = m.times;
  console.log("play engine load (ms)", m.times);
  const parsed = PS.parse(location.search, ctx);
  st = parsed.state;
  const notes = [];
  if (parsed.dropped.length) notes.push(`Some settings in this link were not applied: ${parsed.dropped.join("; ")}.`);
  if (parsed.otherVersion) notes.push("This link was made against a different version of the model; its settings are applied to the current one.");
  if (notes.length) { R.linknote.textContent = notes.join(" "); R.linknote.hidden = false; }
  buildControls();
  R.engine.textContent = "The model's Python is ready. Move a control.";
  ask(PS.engineSettings(PS.defaults(ctx))).then(r => {
    baseline = r.result;
    accepted = { state: PS.defaults(ctx), result: baseline };
    update();
  }, () => {});
}

function buildControls() {
  R.turnrange.textContent = `Range offered: ${PS.TURNOUT.min} to +${PS.TURNOUT.max} points. Tested against a re-run of the model for ${PS.TESTED_POOL} turnout; argued, not tested, for the others.`;
  clear(R.sliders);
  ctx.pools.forEach((p, i) => {
    const input = el("input", { type: "range", id: `t-${i}`, min: PS.TURNOUT.min, max: PS.TURNOUT.max, step: PS.TURNOUT.step });
    input.addEventListener("input", () => { st.shift[i] = +input.value; moved(`turnout:${i}`, true); });
    const row = el("div", { className: "slider" },
      el("label", { htmlFor: `t-${i}` }, p, el("br"), el("span", { className: "cav" }, p === PS.TESTED_POOL ? "tested" : "argued, not tested")),
      input, el("output", { htmlFor: `t-${i}` }));
    groups[`turnout:${i}`] = row;
    inputs.turnout[i] = input;
    inputs.echo[i] = row.lastChild;
    R.sliders.append(row);
  });

  const polled = [...new Set(ctx.pollRows.flatMap(p => Object.keys(p.numbers || {})))].sort((a, b) => party(a).name.localeCompare(party(b).name));
  clear(R.polls);
  R.polls.append(el("thead", {}, el("tr", {}, el("th", { scope: "col" }, "Use"), el("th", { scope: "col" }, "Poll"),
    ...polled.map(c => el("th", { scope: "col" }, party(c).name)))));
  const tbody = el("tbody");
  for (const p of ctx.pollRows) {
    const box = el("input", { type: "checkbox", "aria-label": `Use ${p.label || p.id}` });
    box.dataset.poll = p.id;
    inputs.polls.push(box);
    box.addEventListener("change", () => {
      st.polls = box.checked ? [...new Set([...st.polls, p.id])] : st.polls.filter(x => x !== p.id);
      moved("polls", false);
    });
    const about = `${p.pollster || p.house || ""}, fieldwork ended ${p.fieldwork_end || "undated"}, ` +
      `${p.n ? `${Number(p.n).toLocaleString("en-ZA")} people` : "sample size not published"}. ${p.caveat || ""}`;
    tbody.append(el("tr", {}, el("td", {}, box), el("td", {}, p.label || p.id, el("br"), el("span", { className: "cav" }, about)),
      ...polled.map(c => el("td", {}, p.numbers?.[c] != null ? pct(p.numbers[c]) : "—"))));
  }
  R.polls.append(tbody);
  groups.polls = R.polls;

  Object.assign(R.trust, { min: PS.TRUST.min, max: PS.TRUST.max, step: PS.TRUST.step, disabled: false });
  R.trust.addEventListener("input", () => { st.trust = +R.trust.value; moved("trust", true); });
  groups.trust = R.trustGroup;

  const cellName = c => c.w_bye === 0 ? "None" : c.w_bye === 1 ? "Full" : `As published (${c.w_bye.toFixed(2)})`;
  clear(R.cells);
  for (const c of ctx.cellRows) {
    const b = el("button", { type: "button" }, cellName(c));
    b.dataset.cell = c.path;
    b.addEventListener("click", () => { st.cell = c.path; moved("cell", false); });
    R.cells.append(b);
  }
  groups.cell = R.cells;

  const LAW = { deduct: "The law: the surplus is deducted from every other party", expand: "Not the law: the council grows by the excess",
                level: "Not the law: the council grows until every party is covered", cap: "Not the law: excess ward winners are not seated" };
  clear(R.law);
  for (const k of ctx.laws) {
    const radio = el("input", { type: "radio", name: "law", value: k, style: "margin-top:4px;accent-color:var(--accent)" });
    radio.addEventListener("change", () => { st.law = k; moved("law", false); });
    inputs.law.push(radio);
    R.law.append(el("label", { style: "display:flex;gap:8px;align-items:flex-start;margin:6px 0;font-size:13.5px" }, radio, el("span", {}, LAW[k] || k)));
  }
  groups.law = R.law;
  syncControls();
}

// Put every control and its echo in line with `st` (after a reset, a link, or a stop).
function syncControls() {
  ctx.pools.forEach((_, i) => {
    inputs.turnout[i].value = st.shift[i];
    inputs.echo[i].textContent = (st.shift[i] > 0 ? "+" : "") + st.shift[i];
  });
  for (const box of inputs.polls) box.checked = st.polls.includes(box.dataset.poll);
  R.trust.value = st.trust;
  R.trustv.textContent = String(st.trust);
  for (const b of R.cells.children) b.setAttribute("aria-pressed", String(b.dataset.cell === st.cell));
  for (const r of inputs.law) r.checked = r.value === st.law;
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

// ---------- figures ----------
const pct = x => `${Math.round(x * 1000) / 10}%`;
const seatNum = f => String(Math.round(f.value * 10) / 10);
const pm = f => `±${f.sampling_se.toFixed(1)}`;
// One figure with its ± seats, or the refusal in its place.
function fig(f, strong = false) {
  if (f.withheld) return el("abbr", { title: "Withheld: known to worse than the page's precision" }, "withheld");
  return el("span", {}, strong ? el("b", {}, seatNum(f)) : seatNum(f), el("span", { className: "se" }, pm(f)));
}

function greyOnly(names) {
  for (const g of Object.values(groups)) g.classList.remove("greyed");
  for (const n of names) groups[n]?.classList.add("greyed");
}

async function update() {
  if (!ctx || !baseline) return;
  const touched = PS.isTouched(st);
  greyOnly([]);
  if (!touched) {
    accepted = { state: copyState(st), result: baseline };
    render(baseline, false);
    return;
  }
  R.ess.textContent = "Computing…";
  let m;
  try { m = await ask(PS.engineSettings(st)); }
  catch (e) { if (e.message !== "superseded") R.ess.textContent = `The model's Python refused: ${e.message}`; return; }
  const r = m.result;
  const bad = r.refused ? `too few simulations match that setting to say anything (${r.refused})`
    : r.within_precision === false ? `a figure on this page would be known to worse than ±${r.max_figure_se} seats` : null;
  if (bad && lastMoved && accepted) {
    // The control stops: back to the last setting every shown figure passed.
    const which = lastMoved;
    st = copyState(accepted.state);
    syncControls();
    writeURL();
    render(accepted.result, PS.isTouched(st));
    greyOnly([which]);
    R.ess.textContent = `The greyed control stops here: one step further and ${bad}.`;
    R.ess.classList.add("low");
    return;
  }
  if (r.refused) {
    // A link opened past the floor has no last move: every control away from
    // the published setting greys, and no figure is shown.
    greyOnly([...st.shift.map((x, i) => x !== 0 ? `turnout:${i}` : null),
      st.trust ? "trust" : null, st.trust && st.polls.length ? "polls" : null,
      st.cell !== PS.PUBLISHED_CELL ? "cell" : null, st.law !== PS.PUBLISHED_LAW ? "law" : null].filter(Boolean));
    R.ess.textContent = `Too few simulations match these settings to say anything: ${r.refused} Move the greyed control back towards the published setting.`;
    R.ess.classList.add("low");
    clear(R.seats);
    R.bandnote.textContent = "";
    renderBye(baseline);
    return;
  }
  if (r.within_precision) accepted = { state: copyState(st), result: r };
  lastResult = r;
  render(r, true, m.ms);
}

function render(r, touched, ms) {
  if (touched) R.seatsRegion.setAttribute("data-touched", "");
  else R.seatsRegion.removeAttribute("data-touched");
  R.ess.classList.remove("low");
  R.turnpin.hidden = !r.turnout_pinned;
  renderBye(touched ? r : baseline);
  handoff(r);
  if (!touched) {
    R.ess.textContent = "The published forecast: every simulation counts once.";
    clear(R.seats);
    R.bandnote.textContent = "";
    clear(R.summary);
    R.pollavg.textContent = "No poll is switched on with any trust.";
    return;
  }
  R.ess.textContent = `${Math.round(r.effective_draws).toLocaleString("en-ZA")} effective simulations of ${r.draws.toLocaleString("en-ZA")}` +
    (ms != null ? `, computed in ${ms} ms.` : ".");

  const val = f => (f.withheld ? Infinity : f.value);
  const codes = r.shown.slice().sort((a, b) => val(r.seats[b].median) - val(r.seats[a].median) || party(a).name.localeCompare(party(b).name));
  const base = baseline && r.law === baseline.law ? baseline.seats : null;
  clear(R.seats);
  R.seats.append(el("thead", {}, el("tr", {}, ...["Party", "Middle", "Range", "Change"].map(h => el("th", { scope: "col" }, h)))));
  const tbody = el("tbody");
  for (const c of codes) {
    const s = r.seats[c], b = base?.[c];
    const d = b && !s.median.withheld && !b.median.withheld ? Math.round((s.median.value - b.median.value) * 10) / 10 : null;
    tbody.append(el("tr", {},
      el("td", {}, swatch(c), party(c).name),
      el("td", {}, fig(s.median, true)),
      el("td", {}, fig(s.p5), " – ", fig(s.p95)),
      el("td", { className: "chg" }, d ? (d > 0 ? "+" : "") + d : "—")));
  }
  R.seats.append(tbody);
  const label = r.poll ? ` With a poll trusted, these figures are ${r.poll.label}, not what happens if the poll is right.` : "";
  R.bandnote.textContent = "Middle is the median seat count; the range covers nine in ten of the weighted simulations. " +
    `The ± under each figure is its sampling error, in seats: how far it could move if the model were run again; no control goes past ±${r.max_figure_se}. ` +
    (base ? "Change is against the published forecast under this seat law. " : "Change is shown only under the published seat law. ") +
    "Fewer effective simulations make every figure less certain than the published one." + label;

  clear(R.summary);
  R.summary.append(...codes.slice(0, 4).map(c => el("span", {}, el("span", { className: "sw", style: `background:${party(c).colour}` }),
    `${party(c).name} `, el("b", {}, r.seats[c].median.withheld ? "withheld" : seatNum(r.seats[c].median)))),
    el("span", { className: "ess" }, `${Math.round(r.effective_draws)} eff., computed in your browser`));
  const said = codes.slice(0, 5).map(c => `${party(c).name} ${r.seats[c].median.withheld ? "withheld" : seatNum(r.seats[c].median)}`).join(", ");
  if (R.announce.textContent !== said) R.announce.textContent = said;

  if (r.poll) {
    const parts = Object.keys(r.poll.average).sort((a, b) => r.poll.average[b] - r.poll.average[a]);
    R.pollavg.textContent = "Average of the polls switched on, on the parties they all name (lowest to highest poll in brackets): " +
      parts.map(k => `${party(k).name} ${pct(r.poll.average[k])} (${pct(r.poll.spread[k][0])}–${pct(r.poll.spread[k][1])})`).join(", ") + ".";
  } else R.pollavg.textContent = "No poll is switched on with any trust.";
}

// The by-election column (DESIGN-decided §11, review F20). `centres` are the
// model's deterministic LEVELS for each party at this weight, not vote shares
// (they do not sum to one), so each is compared only with the same party's
// level at the published weight: cell against cell, never with a drawn share,
// and never with the swing column, which is measured in contested wards only.
const signed = (x, digits) => (x > 0 ? "+" : "") + x.toFixed(digits);
function renderBye(r) {
  clear(R.bye);
  R.bye.append(el("thead", {}, el("tr", {}, ...["Party", "By-election swing, contested wards only", "Wards contested",
    "Model's central level at this weight", "Level against the published weight", "Middle seats against the published weight"]
    .map(h => el("th", { scope: "col" }, h)))));
  const tbody = el("tbody");
  if (!evidence) {
    tbody.append(el("tr", {}, el("td", { colspan: 6 }, "The by-election evidence is not served with these draws.")));
    R.bye.append(tbody);
    return;
  }
  const atPublished = !r || r.cell === PS.PUBLISHED_CELL;
  const centres = r?.centres;
  const pubCentres = atPublished ? centres : (r?.published_cell?.centres ?? baseline?.centres);
  const cmp = r?.against_published_cell;
  for (const x of evidence.filter(x => x.party !== "UNKNOWN" && x.party !== "IND")) {
    const c = x.party;
    const level = centres && centres[c] != null ? centres[c].toFixed(3) : "not in this export";
    const vsLevel = atPublished ? "the published weight"
      : centres?.[c] != null && pubCentres?.[c] != null ? signed(centres[c] - pubCentres[c], 3) : "—";
    const vsSeats = atPublished ? "the published weight"
      : cmp?.[c] ? (cmp[c].within_noise ? "within sampling noise" : `${signed(Math.round(cmp[c].difference * 10) / 10, 1)}, more than sampling noise`) : "—";
    tbody.append(el("tr", {}, el("td", {}, party(c).name),
      el("td", {}, `${signed(Math.round(+x.weighted_delta * 1000) / 10, 1)} points`), el("td", {}, String(x.contests)),
      el("td", {}, level), el("td", {}, vsLevel), el("td", {}, vsSeats)));
  }
  R.bye.append(tbody);
}

// The start state handed to "make your own": the combined vote the builder
// shows (DESIGN-decided §10). The draws carry only the list vote (the export
// states why), and a list share is not handed over as if it were the combined
// one, so the button stays disabled and says so.
function handoff(r) {
  const ok = !!r?.combined_share;
  R.tomake.disabled = !ok;
  R.tomakenote.hidden = ok;
}

R.reset.addEventListener("click", () => {
  if (!ctx) return;
  st = PS.defaults(ctx); lastMoved = null;
  syncControls();
  history.replaceState(null, "", location.pathname + location.hash);
  update();
});
R.copylink.addEventListener("click", async () => {
  try { await navigator.clipboard.writeText(location.href); R.copylink.textContent = "Link copied"; }
  catch (e) { R.copylink.textContent = "Copy the address bar"; }
  setTimeout(() => { R.copylink.textContent = "Copy a link to these settings"; }, 2000);
});
R.tomake.addEventListener("click", () => {
  const r = st && PS.isTouched(st) ? lastResult : baseline;
  if (!r?.combined_share) return;
  try {
    sessionStorage.setItem("jhb-start-from", JSON.stringify({
      calls: null, share: Object.fromEntries(Object.entries(r.combined_share).map(([k, v]) => [k, Math.round(v * 1000) / 10])),
      coalition: [], mayor: "" }));
  } catch (e) {}
  location.href = "make.html";
});
