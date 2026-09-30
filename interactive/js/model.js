// "Play with the model": the page. It holds the controls and writes the figures
// the model's Python returns; it computes none of them.
//
// Every figure a control produces is computed by src/reweight.py, through
// pyboot/page.py, under Pyodide, in a Web Worker (js/model-worker.js; SPEC-v2
// Lane P, F11). The JavaScript re-weighting this file used to hold is deleted:
// one definition, in Python (INTEGRATION §3b).
//
// ⛔ THE ONE MODULE THAT WRITES FIGURES. Every figure is written by this file,
// and only into an element carrying `data-live="<name>"`, which holds no
// build-time digits and carries the visible label LIVE_LABEL (SPEC-v2
// decision 1). It is the path for `stats.LIVE_WRITERS`.
//
// First paint (F6): the published forecast's panels (js/published.js, a
// prototype shim build_site replaces) and no Python. The seat table switches to
// the computed one only once a control moves away from the published setting;
// the published panels then say they are of the published forecast (F14).

import { loadAll, esc, wireTheme, announce } from "./common.js";
import * as PS from "./play-state.js";
import { paintPublished } from "./published.js";

wireTheme();
const $ = s => document.querySelector(s);
const LIVE_LABEL = "Computed in your browser from your settings.";
const DEBOUNCE_MS = 200;
const published = paintPublished();

// Party names and colours. ⚠ ADAPTER until Lane E's manifest carries the
// roster: the site's names and colours for the parties the prototype fixture
// lists, and the IEC code, spaced, for every other party.
const { byCode } = await loadAll();
const party = c => byCode[c] ?? { code: c, name: c.replace(/_/g, " ").toLowerCase().replace(/(^|\s)\S/g, m => m.toUpperCase()), colour: "var(--ink-3)" };

// The by-election evidence (DESIGN-decided §11), served in site/draws/index.json
// by export_draws --index from the model's own input file.
async function loadByelectionEvidence() {
  try {
    const r = await fetch(new URL("../../site/draws/index.json", import.meta.url));
    if (!r.ok) return null;
    return (await r.json()).byelection ?? null;
  } catch (e) { return null; }
}
const evidenceP = loadByelectionEvidence();

// ---------- the engine ----------
const worker = new Worker(new URL("./model-worker.js", import.meta.url), { type: "module" });
let ctx = null, st = null, seq = 0, lastMoved = null, baseline = null, timer = null, lastResult = null;
const pending = new Map();

function ask(settings) {
  const id = ++seq;
  worker.postMessage({ type: "compute", seq: id, settings });
  return new Promise((ok, no) => pending.set(id, { ok, no }));
}

worker.onmessage = e => {
  const m = e.data;
  if (m.type === "stage") $("#engine").textContent = `${m.label}…`;
  else if (m.type === "failed") {
    $("#engine").textContent = m.missing ? m.message : `The model's Python did not load: ${m.message}. The published forecast is shown.`;
    $("#engine").classList.add("low");
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
  ctx = { pools: m.pools, polls: m.polls.map(p => p.id), pollRows: m.polls, laws: m.laws,
          cells: cells.map(c => c.path), cellRows: cells, modelVersion: m.modelVersion };
  window.__playEngineTimes = m.times;
  console.log("play engine load (ms)", m.times);
  const parsed = PS.parse(location.search, ctx);
  st = parsed.state;
  const notes = [];
  if (parsed.dropped.length) notes.push(`Some settings in this link were not applied: ${parsed.dropped.join("; ")}.`);
  if (parsed.otherVersion) notes.push("This link was made against a different version of the model; its settings are applied to the current one.");
  if (notes.length) { $("#linknote").textContent = notes.join(" "); $("#linknote").hidden = false; }
  buildControls();
  $("#controls").setAttribute("aria-busy", "false");
  $("#engine").textContent = "The model's Python is ready. Move a control.";
  ask(PS.engineSettings(PS.defaults(ctx))).then(r => { baseline = r.result; update(true); }, () => {});
}

function buildControls() {
  $("#turnrange").textContent = `Range offered: ${PS.TURNOUT.min} to +${PS.TURNOUT.max} points. Tested against a re-run of the model for ${PS.TESTED_POOL} turnout; argued, not tested, for the others.`;
  $("#turnout").innerHTML = `<p class="livelabel">${LIVE_LABEL}</p>` + ctx.pools.map((p, i) => `<div class="slider" data-group="turnout:${i}">
    <label for="t-${i}">${esc(p)}<br><span class="cav">${p === PS.TESTED_POOL ? "tested" : "argued, not tested"}</span></label>
    <input type="range" id="t-${i}" data-pool="${i}" min="${PS.TURNOUT.min}" max="${PS.TURNOUT.max}" step="${PS.TURNOUT.step}" value="${st.shift[i]}">
    <output for="t-${i}" id="to-${i}"></output></div>`).join("");
  $("#turnout").addEventListener("input", e => {
    const i = e.target.dataset.pool; if (i == null) return;
    st.shift[+i] = +e.target.value; moved(`turnout:${i}`, true);
  });

  const polled = [...new Set(ctx.pollRows.flatMap(p => Object.keys(p.numbers || {})))].sort((a, b) => party(a).name.localeCompare(party(b).name));
  $("#polls").innerHTML = `<thead><tr><th scope="col">Use</th><th scope="col">Poll</th>` +
    polled.map(c => `<th scope="col">${esc(party(c).name)}</th>`).join("") + `</tr></thead><tbody>` +
    ctx.pollRows.map(p => `<tr><td><input type="checkbox" data-poll="${esc(p.id)}"${st.polls.includes(p.id) ? " checked" : ""} aria-label="Use ${esc(p.label || p.id)}"></td>
      <td>${esc(p.label || p.id)}<br><span class="cav">${esc(p.pollster || p.house || "")}, fieldwork ended ${esc(p.fieldwork_end || "undated")}, ${p.n ? `${Number(p.n).toLocaleString("en-ZA")} people` : "sample size not published"}. ${esc(p.caveat || "")}</span></td>` +
      polled.map(c => `<td>${p.numbers?.[c] != null ? Math.round(p.numbers[c] * 1000) / 10 + "%" : "—"}</td>`).join("") + `</tr>`).join("") + `</tbody>`;
  $("#polls").addEventListener("change", e => {
    const id = e.target.dataset.poll; if (!id) return;
    st.polls = e.target.checked ? [...new Set([...st.polls, id])] : st.polls.filter(x => x !== id);
    moved("polls", false);
  });
  const tr = $("#trust");
  Object.assign(tr, { min: PS.TRUST.min, max: PS.TRUST.max, step: PS.TRUST.step, value: st.trust, disabled: false });
  tr.closest(".slider").dataset.group = "trust";
  tr.addEventListener("input", () => { st.trust = +tr.value; moved("trust", true); });

  const cellName = c => c.w_bye === 0 ? "None" : c.w_bye === 1 ? "Full" : `As published (${c.w_bye.toFixed(2)})`;
  $("#cells").innerHTML = ctx.cellRows.map(c => `<button type="button" data-cell="${esc(c.path)}" aria-pressed="${c.path === st.cell}">${esc(cellName(c))}</button>`).join("");
  $("#cells").dataset.group = "cell";
  $("#cells").addEventListener("click", e => {
    const b = e.target.closest("[data-cell]"); if (!b) return;
    st.cell = b.dataset.cell; moved("cell", false);
  });

  const LAW = { deduct: "The law: the surplus is deducted from every other party", expand: "Not the law: the council grows by the excess",
                level: "Not the law: the council grows until every party is covered", cap: "Not the law: excess ward winners are not seated" };
  $("#laws").innerHTML = ctx.laws.map(k => `<label style="display:flex;gap:8px;align-items:flex-start;margin:6px 0;font-size:13.5px">
    <input type="radio" name="law" value="${esc(k)}"${k === st.law ? " checked" : ""} style="margin-top:4px;accent-color:var(--accent)"><span>${esc(LAW[k] || k)}</span></label>`).join("");
  $("#laws").dataset.group = "law";
  $("#laws").addEventListener("change", e => { st.law = e.target.value; moved("law", false); });
  syncControls();
}

// Put every control and its echo in line with `st` (after a reset or a link).
function syncControls() {
  ctx.pools.forEach((_, i) => {
    $(`#t-${i}`).value = st.shift[i];
    $(`#to-${i}`).textContent = (st.shift[i] > 0 ? "+" : "") + st.shift[i];
  });
  document.querySelectorAll("[data-poll]").forEach(b => { b.checked = st.polls.includes(b.dataset.poll); });
  $("#trust").value = st.trust;
  $("#trustv").textContent = String(st.trust);
  document.querySelectorAll("[data-cell]").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.cell === st.cell)));
  document.querySelectorAll('input[name="law"]').forEach(r => { r.checked = r.value === st.law; });
}

function moved(group, debounce) {
  lastMoved = group;
  syncControls();
  history.replaceState(null, "", location.pathname + PS.serialize(st, ctx) + location.hash);
  clearTimeout(timer);
  if (debounce) timer = setTimeout(() => update(), DEBOUNCE_MS);
  else update();
}

// ---------- figures ----------
const fmtSeats = f => f.withheld ? `<abbr title="Withheld: its tail rests on too few simulations">withheld</abbr>` : String(Math.round(f.value * 10) / 10);
const pct = x => `${Math.round(x * 1000) / 10}%`;

async function update(fromReady = false) {
  if (!ctx) return;
  const touched = PS.isTouched(st);
  $("#pubseats").hidden = touched;
  $("#liveseats").hidden = !touched;
  $("#esslabel").hidden = !touched;
  $("#pubnote").hidden = !touched;
  document.querySelectorAll("[data-group]").forEach(el => el.classList.remove("greyed"));
  if (!touched) {
    $("#ess").textContent = "The published forecast: every simulation counts once.";
    $("#ess").classList.remove("low");
    $("#turnpin").hidden = true;
    $("#pollavg").hidden = true;
    renderBye(baseline);
    handoff(baseline);
    return;
  }
  $("#ess").textContent = "Computing…";
  let m;
  try { m = await ask(PS.engineSettings(st)); }
  catch (e) { if (e.message !== "superseded") $("#ess").textContent = `The model's Python refused: ${e.message}`; return; }
  const r = m.result;
  lastResult = r;
  if (r.refused) {
    // F17: the control that took the draws past the floor greys out, and no figure is shown
    // (a link opened at the floor has no last move: every control away from
    // the published setting greys instead)
    const groups = lastMoved ? [lastMoved] : [
      ...st.shift.map((x, i) => x !== 0 ? `turnout:${i}` : null),
      st.trust ? "trust" : null, st.trust && st.polls.length ? "polls" : null,
      st.cell !== PS.PUBLISHED_CELL ? "cell" : null, st.law !== PS.PUBLISHED_LAW ? "law" : null].filter(Boolean);
    for (const g of groups) document.querySelector(`[data-group="${g}"]`)?.classList.add("greyed");
    $("#ess").textContent = `Too few simulations match these settings to say anything: ${r.refused} Move the greyed control back towards the published setting.`;
    $("#ess").classList.add("low");
    $("#seats").innerHTML = "";
    $("#bandnote").textContent = "";
    $("#tomake").disabled = true;
    renderBye(null);
    return;
  }
  $("#tomake").disabled = false;
  $("#ess").classList.remove("low");
  $("#ess").textContent = `${Math.round(r.effective_draws).toLocaleString("en-ZA")} effective simulations of ${r.draws.toLocaleString("en-ZA")}, computed in ${m.ms} ms.`;
  $("#turnpin").hidden = !r.turnout_pinned;

  const codes = Object.keys(r.seats).filter(c => r.seats[c].p95.value > 0 || r.seats[c].median.value > 0)
    .sort((a, b) => r.seats[b].median.value - r.seats[a].median.value || party(a).name.localeCompare(party(b).name));
  const base = baseline && r.law === baseline.law ? baseline.seats : null;
  $("#seats").innerHTML = `<thead><tr><th scope="col">Party</th><th scope="col">Middle</th><th scope="col">Range</th><th scope="col">Change</th></tr></thead><tbody>` +
    codes.map(c => {
      const s = r.seats[c], b = base?.[c];
      const d = b && !s.median.withheld ? Math.round((s.median.value - b.median.value) * 10) / 10 : null;
      return `<tr><td><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${party(c).colour};margin-right:6px"></span>${esc(party(c).name)}</td>
        <td><b>${fmtSeats(s.median)}</b></td><td>${fmtSeats(s.p5)}–${fmtSeats(s.p95)}</td><td class="chg">${d ? (d > 0 ? "+" : "") + d : "—"}</td></tr>`;
    }).join("") + `</tbody>`;
  const label = r.poll ? ` With a poll trusted, these figures are ${r.poll.label}, not what happens if the poll is right.` : "";
  $("#bandnote").textContent = "Middle is the median seat count; the range covers nine in ten of the weighted simulations. " +
    (base ? "Change is against the published forecast under this seat law. " : "Change is shown only under the published seat law. ") +
    "Fewer effective simulations make every figure less certain than the published one." + label;
  $("#msum").innerHTML = codes.slice(0, 4).map(c => `<span><span class="sw" style="background:${party(c).colour}"></span>${esc(party(c).name)} <b>${fmtSeats(r.seats[c].median)}</b></span>`).join("") +
    `<span class="ess">${Math.round(r.effective_draws)} eff., computed in your browser</span>`;
  announce($("#live"), codes.slice(0, 5).map(c => `${party(c).name} ${fmtSeats(r.seats[c].median)}`).join(", "));

  if (r.poll) {
    const parts = Object.keys(r.poll.average).sort((a, b) => r.poll.average[b] - r.poll.average[a]);
    $("#pollavgtext").textContent = "Average of the polls switched on, on the parties they all name (lowest to highest poll in brackets): " +
      parts.map(k => `${party(k).name} ${pct(r.poll.average[k])} (${pct(r.poll.spread[k][0])}–${pct(r.poll.spread[k][1])})`).join(", ") + ".";
    $("#pollavg").hidden = false;
  } else $("#pollavg").hidden = true;
  renderBye(r);
  handoff(r);
}

async function renderBye(r) {
  const ev = await evidenceP;
  const cmp = r?.against_published_cell;
  const centres = r?.centres, pubCentres = r?.published_cell?.centres ?? baseline?.centres;
  const rows = ev ? ev.filter(x => x.party !== "UNKNOWN" && x.party !== "IND") : [];
  const head = `<thead><tr><th scope="col">Party</th><th scope="col">By-election swing, contested wards only</th><th scope="col">Wards contested</th>` +
    `<th scope="col">Model's citywide share at this weight</th><th scope="col">Middle seats against the published weight</th></tr></thead>`;
  if (!ev) {
    $("#bye").innerHTML = head + `<tbody><tr><td colspan="5">The by-election evidence is not served with this prototype yet.</td></tr></tbody>`;
    return;
  }
  const centre = c => centres && centres[c] != null
    ? pct(centres[c]) + (pubCentres && pubCentres[c] != null ? ` (published ${pct(pubCentres[c])})` : "")
    : "not in this export yet";
  const noise = c => !cmp ? (r && r.cell !== PS.PUBLISHED_CELL ? "—" : "the published weight")
    : cmp[c] ? (cmp[c].within_noise ? "within sampling noise" : `${cmp[c].difference > 0 ? "+" : ""}${Math.round(cmp[c].difference * 10) / 10}, more than sampling noise`) : "—";
  $("#bye").innerHTML = head + `<tbody>` + rows.map(x => `<tr><td>${esc(party(x.party).name)}</td>
    <td>${(+x.weighted_delta > 0 ? "+" : "") + Math.round(+x.weighted_delta * 1000) / 10} points</td><td>${esc(x.contests)}</td>
    <td>${centre(x.party)}</td><td>${noise(x.party)}</td></tr>`).join("") + `</tbody>`;
}

// The start state handed to "make your own": the combined vote the builder
// shows (DESIGN-decided §10). The draws carry only the list vote until Lane E
// exports the combined share (F13), and a list share is not handed over as if
// it were the combined one.
function handoff(r) {
  const ok = !!r?.combined_share;
  $("#tomakenote").hidden = ok;
  $("#tomakenote").textContent = ok ? "" : "The published draws do not carry the combined vote yet, so the builder starts from its own default.";
}

$("#reset").addEventListener("click", () => {
  if (!ctx) return;
  st = PS.defaults(ctx); lastMoved = null;
  syncControls();
  history.replaceState(null, "", location.pathname + location.hash);
  update();
});
$("#copylink").addEventListener("click", async () => {
  try { await navigator.clipboard.writeText(location.href); $("#copylink").textContent = "Link copied"; }
  catch (e) { $("#copylink").textContent = "Copy the address bar"; }
  setTimeout(() => { $("#copylink").textContent = "Copy a link to these settings"; }, 2000);
});
$("#tomake").addEventListener("click", () => {
  const r = st && PS.isTouched(st) ? lastResult : baseline;
  if (r?.combined_share) {
    try {
      sessionStorage.setItem("jhb-start-from", JSON.stringify({
        calls: null, share: Object.fromEntries(Object.entries(r.combined_share).map(([k, v]) => [k, Math.round(v * 1000) / 10])),
        coalition: [], mayor: "" }));
    } catch (e) {}
  }
  location.href = "make.html";
});

await published;
