// "Make your own forecast". §8 of DESIGN-decided: every control applies to
// every party identically; nothing is pre-selected for one party.
//
// §14 (owner, 2026-09-29): the builder can only hold a valid forecast, so an
// honest save never fails. The state lives in js/builder-state.js (whole votes
// summing to the combined total, every ward called, a ward-holder never below
// one vote); seats come from the project's own seat code under Pyodide
// (js/seat-engine.js), the same code and the same request the server runs at
// save. The page paints first; the edit controls unlock when the seat law has
// loaded.

import { loadAll, loadSchema, esc, wireTheme, loadDraft, saveDraft, topN, announce, pageURL, possessive } from "./common.js";
import { handleLabel } from "./labels.js";
import { WardMap } from "./map.js";
import * as B from "./builder-state.js";
import { loadSeatEngine, SeatCodeMissing } from "./seat-engine.js";
import { validateForecast, cleanDisplayName } from "../../worker-api/src/validate.js";
import { ensureConsent } from "./auth-ui.js";
import { saveForecast, deleteForecast, mode } from "./api.js";
import { openShare } from "./share.js";
import { buildCardSVG, cardAlt } from "./card.js";

wireTheme();
const $ = s => document.querySelector(s);
const [{ geom, model, parties, byCode }, schema] = await Promise.all([loadAll(), loadSchema()]);
const ctx = B.contextOf(schema);
const N = ctx.wards.length;
const codes = parties.map(p => p.code);          // alphabetical, from the fixture
if (codes.join() !== ctx.codes.join() || geom.wards.map(w => String(w.id)).join() !== ctx.wards.join())
  throw new Error("the fixtures and the forecast schema disagree about the roster or the wards; regenerate the schema");
const likely = ctx.wards.map(w => model.likely_ward_winner[w]);
const name = c => byCode[c].name;
const pct = (v, dp = 1) => {
  const p = v / ctx.T * 100;
  return p > 0 && p < 0.05 ? "<0.1" : p.toFixed(dp);
};

document.querySelectorAll("[data-n-wards]").forEach(e => { e.textContent = N; });

// ---------- state ----------
let from = null;
try { from = JSON.parse(sessionStorage.getItem("jhb-start-from") || "null"); sessionStorage.removeItem("jhb-start-from"); } catch (e) {}
const draft = from ? null : loadDraft();
function initialState() {
  if (from) return B.startState(ctx, { calls: from.calls, share: from.share }, likely).state;
  if (draft?.calls && draft?.votes) {
    const s = { calls: draft.calls, votes: draft.votes };
    if (!B.invariantErrors(s, ctx).length) return s;
    return B.startState(ctx, { calls: draft.calls, share: draft.votes }, likely).state;
  }
  return B.startState(ctx, { calls: likely, share: model.combined_share }, likely).state;
}
let state = initialState();
const S = {
  coalition: (from?.coalition || draft?.coalition || []).filter(c => codes.includes(c)),
  mayor: from ? (from.mayor || "") : (draft?.mayor || ""),
  brush: null,
  id: from ? null : (draft?.id || null),
};
if (!S.coalition.includes(S.mayor)) S.mayor = "";
$("#flabel").value = draft?.label || "";
const history = new B.History();

// ---------- the seat law, loaded behind the first paint ----------
let engine = null, result = null, engineError = null;
const STAGES = { start: 1, pyodide: 2, numpy: 3, import: 4 };
function stage(k, label, ms) {
  const n = STAGES[k] || 0;
  $("#enginebar").style.setProperty("--done", `${n / 4 * 100}%`);
  $("#enginemsg").textContent = k === "import" ? "" : `Loading the seat law: ${label.toLowerCase()}…`;
  // The map is the first control a phone reader reaches, far above the
  // results; say there why it does not answer yet.
  if (k !== "import") $("#maphint").textContent = `Loading the seat law in your browser (step ${n} of 3). The controls unlock when it is ready.`;
}
function lock(on) {
  document.querySelector(".builder").classList.toggle("locked", on);
  document.querySelectorAll(".builder [data-edit]").forEach(el => { el.disabled = on; });
}

// ---------- map ----------
const map = new WardMap($("#map"), geom, { byCode, onPaint: paintWard });
map.onClear = () => { $("#maphint").textContent = "Every ward needs a winner. Choose a party, then tap the ward to change it."; };
map.setCalls(state.calls);

function commit(next, note = "") {
  state = next;
  $("#floornote").textContent = note;
  afterEdit();
}
function snapshot() { history.push(state); $("#undo").disabled = !engine; }

let strokeOpen = false;
function paintWard(i) {
  if (!engine) return;
  if (!S.brush) {
    $("#maphint").textContent = "Choose a party below first, then tap the ward.";
    $("#brush").querySelector("button")?.focus();
    return;
  }
  if (state.calls[i] === S.brush) return;
  if (!strokeOpen) { snapshot(); strokeOpen = true; }
  const r = B.assignWards(state, ctx, [i], S.brush);
  commit(r.state, raisedNote(r.raised));
}
window.addEventListener("pointerup", () => { strokeOpen = false; });
$("#map").addEventListener("keyup", () => { strokeOpen = false; });

function raisedNote(raised) {
  if (!raised.length) return "";
  const who = raised.map(name).join(", ");
  return `${who} had no votes and now ${raised.length === 1 ? "wins a ward, so it was" : "win wards, so each was"} given one vote (under 0.1%). A party that wins a ward must have votes.`;
}
function setCallsFrom(calls) {
  snapshot();
  const r = B.setCalls(state, ctx, calls);
  commit(r.state, raisedNote(r.raised));
}

// ---------- brush: every party, same chip ----------
$("#brush").innerHTML = parties.map(p =>
  `<button type="button" class="chip" data-c="${p.code}" data-edit aria-pressed="false"><span class="sw" style="background:${p.colour}"></span>${esc(p.name)}</button>`).join("");
$("#brush").addEventListener("click", e => {
  const b = e.target.closest("[data-c]"); if (!b) return;
  S.brush = S.brush === b.dataset.c ? null : b.dataset.c;
  $("#brush").querySelectorAll("[data-c]").forEach(x => x.setAttribute("aria-pressed", String(x.dataset.c === S.brush)));
  $("#maphint").textContent = S.brush
    ? `Painting with ${name(S.brush)}. Tap or drag across wards.`
    : "Choose a party below, then tap or drag across wards to give them to it.";
});

// ---------- views ----------
document.querySelectorAll("[data-view]").forEach(b => b.addEventListener("click", () => {
  const v = b.dataset.view;
  document.querySelectorAll("[data-view]").forEach(x => x.setAttribute("aria-pressed", String(x === b)));
  $("#mapscroll").hidden = v === "list";
  $("#listview").hidden = v !== "list";
  if (v === "list") buildList(); else map.setMode(v);
}));

function buildList() {
  const order = ["north", "east", "south", "west", "central"];
  const opts = parties.map(p => `<option value="${p.code}">${esc(p.name)}</option>`).join("");
  $("#listview").innerHTML = `<div class="wardlist">` + order.map(sec =>
    `<fieldset><legend>${sec}</legend>` + geom.wards.map((w, i) => w.sector !== sec ? "" :
      `<div class="wl"><label for="wl${i}">Ward ${w.id}</label><select id="wl${i}" data-i="${i}" data-edit${engine ? "" : " disabled"}>${opts}</select></div>`).join("") +
    `</fieldset>`).join("") + `</div>`;
  $("#listview").querySelectorAll("select").forEach(s => { s.value = state.calls[+s.dataset.i]; });
}
$("#listview").addEventListener("change", e => {
  const s = e.target.closest("select"); if (!s || !engine) return;
  snapshot();
  const r = B.assignWards(state, ctx, [+s.dataset.i], s.value);
  commit(r.state, raisedNote(r.raised));
});

// ---------- tools ----------
$("#fillarea").addEventListener("click", () => {
  if (!S.brush) { $("#maphint").textContent = "Choose a party below first, then fill the area."; return; }
  const sec = $("#area").value;
  setCallsFrom(state.calls.map((c, i) => geom.wards[i].sector === sec ? S.brush : c));
});
$("#copymodel").addEventListener("click", () => setCallsFrom(likely));
$("#undo").addEventListener("click", () => {
  const prev = history.pop(); if (!prev) return;
  commit(prev);
});

// ---------- the vote: one identical row per party ----------
// Each party's share of ALL votes, ward and list ballots together: the combined
// vote the statute seats (DESIGN-decided §10), shown with no conversion. It
// always sums to 100%: moving one party rescales the others in proportion.
$("#prlist").innerHTML = parties.map(p => `
  <div class="prrow">
    <span class="sw" style="background:${p.colour}" aria-hidden="true"></span>
    <label for="pr-n-${p.code}">${esc(p.name)}</label>
    <input type="number" id="pr-n-${p.code}" data-c="${p.code}" data-edit min="0" max="100" step="0.1" inputmode="decimal" aria-describedby="pr-f-${p.code}">
    <span class="fl" id="pr-f-${p.code}"></span>
    <input type="range" data-c="${p.code}" data-edit min="0" max="100" step="0.1" aria-label="${esc(p.name)}, share of all votes, percent">
  </div>`).join("");
function paintShares(except = null) {
  const floors = B.floorsOf(state.calls, ctx);
  $("#prlist").querySelectorAll("input").forEach(i => {
    if (i === except) return;
    const v = state.votes[i.dataset.c];
    i.value = i.type === "range" ? (v / ctx.T * 100).toFixed(1) : pct(v) === "<0.1" ? "0.0" : pct(v);
    if (i.type === "range") i.setAttribute("aria-valuetext", `${pct(v)} percent`);
  });
  for (const c of codes) {
    const held = state.calls.filter(x => x === c).length;
    $(`#pr-f-${c}`).textContent = floors[c] && state.votes[c] === floors[c] ? "1 vote, the least a ward winner may have" : "";
    $(`#pr-f-${c}`).dataset.held = held;
  }
}
function editShare(input, final) {
  if (!engine) return;
  const c = input.dataset.c;
  const want = parseFloat(input.value);
  if (!Number.isFinite(want)) { if (final) paintShares(); return; }
  if (!input.dataset.open) { snapshot(); input.dataset.open = "1"; }
  if (final) delete input.dataset.open;
  const r = B.setPercent(state, ctx, c, want);
  let note = "";
  if (r.clamped === "floor") {
    const held = state.calls.filter(x => x === c).length;
    note = `${name(c)} wins ${held} ward${held === 1 ? "" : "s"} on your map, so it keeps at least one vote. Give its wards to other parties to take it to zero.`;
  } else if (r.clamped === "ceiling") {
    note = `${name(c)} is at the most it can have: every other party that wins a ward keeps at least one vote.`;
  }
  state = r.state;
  $("#floornote").textContent = note;
  afterEdit(final ? null : input);
}
$("#prlist").addEventListener("input", e => {
  const i = e.target.closest("input"); if (!i) return;
  if (i.type === "range") editShare(i, false);
});
$("#prlist").addEventListener("change", e => {
  const i = e.target.closest("input"); if (i) editShare(i, true);
});
$("#prmodel").addEventListener("click", () => {
  snapshot();
  const r = B.setCalls({ calls: state.calls, votes: B.votesFromPercent(model.combined_share, ctx) }, ctx, state.calls);
  commit(r.state, raisedNote(r.raised));
});

// ---------- coalition ----------
$("#coal").innerHTML = codes.map(c => `<button type="button" class="chip" data-c="${c}" data-edit aria-pressed="false">
  <span class="sw" style="background:${byCode[c].colour}"></span>${esc(name(c))} <span class="n" style="color:var(--ink-3)"></span></button>`).join("");
$("#coal").addEventListener("click", e => {
  const b = e.target.closest("[data-c]"); if (!b || !engine) return;
  const c = b.dataset.c;
  S.coalition = S.coalition.includes(c) ? S.coalition.filter(x => x !== c) : [...S.coalition, c];
  if (!S.coalition.includes(S.mayor)) S.mayor = "";
  render();
});
$("#mayor").addEventListener("change", e => { S.mayor = e.target.value; render(); });

// ---------- label ----------
function labelCheck() {
  const raw = $("#flabel").value;
  if (!raw.trim()) return { ok: true, value: null };
  return cleanDisplayName(raw, schema);
}
$("#flabel").addEventListener("input", () => render());
$("#flabelclear").addEventListener("click", () => { $("#flabel").value = ""; $("#flabel").focus(); render(); });

// ---------- recompute ----------
function afterEdit(activeInput = null) {
  map.setCalls(state.calls);
  if (!$("#listview").hidden) buildList();
  paintShares(activeInput);
  $("#undo").disabled = !engine || !history.size;
  const bad = B.invariantErrors(state, ctx);
  if (bad.length) throw new Error("the builder reached an invalid state: " + bad.join("; "));
  if (engine) {
    const r = engine.seats(B.forecastBody(state, ctx), schema);
    result = r.ok ? r.answer : null;
    if (!r.ok) engineError = `The seat law refused this forecast (${r.errors.join("; ")}). The page should not be able to build it; please report it.`;
  }
  render();
}

function render() {
  const changed = state.calls.filter((c, i) => c !== likely[i]).length;
  $("#nchanged").textContent = changed ? `, ${changed} changed from the model's call` : ", as the model calls them";
  $("#prstate").textContent = "100%";

  const seats = result?.seats || {};
  $("#coal").querySelectorAll("[data-c]").forEach(b => {
    b.setAttribute("aria-pressed", String(S.coalition.includes(b.dataset.c)));
    b.querySelector(".n").textContent = result ? (seats[b.dataset.c] || 0) : "";
  });
  $("#mayor").innerHTML = `<option value="">Not chosen</option>` + S.coalition.map(c =>
    `<option value="${c}"${c === S.mayor ? " selected" : ""}>${esc(name(c))}</option>`).join("");

  const lab = labelCheck();
  $("#flabelerr").textContent = lab.ok ? "" : `This label can't be used: ${lab.reason}.`;
  saveDraft({ calls: state.calls, votes: state.votes, coalition: S.coalition, mayor: S.mayor, id: S.id, label: $("#flabel").value });

  if (engineError) { $("#engineerr").textContent = engineError; }
  if (!result) {
    // First paint, or the seat law still loading: the model's own seats,
    // labelled as the model's, never as the reader's.
    const pub = model.published_seats_median;
    const top = topN(pub, 5, byCode);
    const max = Math.max(1, ...top.map(t => t[1]));
    $("#resh").textContent = "The model's forecast";
    $("#restate").textContent = "Your seats appear here once the seat law has loaded.";
    $("#bars").innerHTML = top.map(([c, n]) => `<div class="bar model"><span class="nm">${esc(name(c))}</span>
      <span class="tr"><span class="fl" style="width:${n / max * 100}%"></span></span><span class="v">${n}</span></div>`).join("");
    $("#strip").innerHTML = ""; $("#capseats").textContent = ""; $("#capmaj").textContent = "";
    $("#coalstat").textContent = ""; $("#costate").textContent = ""; $("#delta").textContent = "";
    saveGate();
    return;
  }
  const council = result.council_total, majority = result.majority;
  const cs = S.coalition.reduce((a, c) => a + (seats[c] || 0), 0);
  $("#coalstat").innerHTML = !S.coalition.length ? "No parties chosen yet."
    : `${cs} of ${council} seats. ` + (cs >= majority ? `<span class="ok">Enough to govern.</span>` : `<span class="no">${majority - cs} short of the ${majority} needed.</span>`);
  $("#costate").textContent = S.coalition.length ? `${S.coalition.length} ${S.coalition.length === 1 ? "party" : "parties"}, ${cs} seats` : "";
  $("#coalneed").textContent = `A council of ${council} needs ${majority} votes`;

  const top = topN(seats, 5, byCode);
  const max = Math.max(1, ...top.map(t => t[1]));
  $("#resh").textContent = "Your council";
  $("#bars").innerHTML = top.map(([c, n]) => `<div class="bar"><span class="nm">${esc(name(c))}</span>
    <span class="tr"><span class="fl" style="width:${n / max * 100}%;background:${byCode[c].colour}"></span></span><span class="v">${n}</span></div>`).join("");
  const over = Object.keys(result.excessive || {});
  $("#restate").textContent = `Top five of ${council} seats` +
    (over.length ? `. ${over.map(name).join(", ")} won at least as many wards as ${over.length === 1 ? "its" : "their"} share of the vote earns, so ${over.length === 1 ? "it keeps its wards" : "they keep their wards"} and the list seats go to the others` : "");
  const order = codes.slice().sort((a, b) => (seats[b] || 0) - (seats[a] || 0) || name(a).localeCompare(name(b)));
  $("#strip").innerHTML = order.filter(c => seats[c]).map(c =>
    `<span style="width:${seats[c] / council * 100}%;background:${byCode[c].colour}"></span>`).join("") +
    `<span class="maj" style="left:calc(${(majority - 0.5) / council} * 100%)"></span>`;
  $("#capseats").textContent = `${council} seats`;
  $("#capmaj").textContent = `${majority} to govern`;

  const pub = model.published_seats_median;
  const moved = top.map(([c, n]) => { const d = n - (pub[c] || 0); return `${esc(name(c))} <b>${d > 0 ? "+" : ""}${d}</b>`; });
  $("#delta").innerHTML = `Against the model's forecast (placeholder median): ${moved.join(", ")}.`;
  announce($("#live"), top.map(([c, n]) => `${name(c)} ${n}`).join(", "));
  saveGate();
}

// What still stands between this forecast and a save. Never a validity
// problem (the state is always valid): only the reader's own choices.
function saveGate() {
  const need = [];
  if (!engine) need.push("wait for the seat law to load");
  if (!S.coalition.length) need.push("pick at least one party to govern");
  if (!labelCheck().ok) need.push("change the label");
  $("#save").disabled = need.length > 0;
  $("#saveneed").textContent = need.length ? "To save, " + need.join(" and ") + "." : "";
}

// ---------- save and share ----------
let labelOffered = false;
$("#save").addEventListener("click", async () => {
  $("#saveerr").textContent = "";
  let s;
  try { s = await ensureConsent(); }
  catch (err) { $("#saveerr").textContent = `Not saved: ${err.message || err}. Your forecast is still here.`; return; }
  if (!s) { $("#saveerr").textContent = "Not saved. Your forecast is still here."; return; }
  // Owner, 2026-09-29: an X reader's label starts as their @username. It is
  // filled in here, and the save stops once, so they see it and can change or
  // clear it before anything is shared.
  const xLabel = handleLabel(s.handle);
  if (xLabel && !labelOffered) {
    labelOffered = true;
    if (!$("#flabel").value.trim()) {
      $("#flabel").value = xLabel;
      render();
      $("#saveerr").textContent = `Your shared prediction will show ${xLabel}. Change or clear the label, then press Save and share again.`;
      $("#flabel").focus();
      return;
    }
  }
  const lab = labelCheck();
  const body = B.forecastBody(state, ctx, { coalition: S.coalition, mayor: S.mayor || null, display_name: lab.value });
  const v = validateForecast(body, schema);
  if (!v.ok) { $("#saveerr").textContent = `Not saved: ${v.field} ${v.reason}.`; return; }
  const seatsAtSave = result;
  let saved;
  try { saved = await saveForecast(v.value, { id: S.id, seats: seatsAtSave }); }
  catch (err) { $("#saveerr").textContent = `Not saved: ${err.message}. Your forecast is still here.`; return; }
  const { id, path, label: shown } = saved;
  S.id = id; render();
  const url = pageURL(path);
  $("#savedline").innerHTML = `Saved. <a href="${esc(path)}">Open your forecast's page</a> — <button class="linkbtn" type="button" id="del">Delete it</button>`;
  $("#del").addEventListener("click", async () => {
    await deleteForecast(id); S.id = null; render();
    $("#savedline").textContent = "Deleted. The link no longer works.";
  });
  $("#savedline").insertAdjacentHTML("beforeend", ` Shown as <b>${esc(shown)}</b>.`);
  const f = { ...v.value, display_name: shown };
  const council = { council: seatsAtSave.council_total, majority: seatsAtSave.majority };
  const svgFor = size => buildCardSVG({ forecast: f, seats: seatsAtSave.seats, geom, byCode, model: council, size, placeholder: true });
  openShare({ url, title: possessive(f.display_name) + " — Johannesburg 2026",
    text: `${possessive(f.display_name)} for Johannesburg's council on 4 November. Make yours:`,
    svgFor, alt: cardAlt({ forecast: f, seats: seatsAtSave.seats, byCode, model: council }), fileBase: "joburg-forecast-" + id });
});

// ---------- first paint, then the seat law ----------
lock(true);
paintShares();
render();

// Production: the Worker's sign-in callback returns here with ?consent=1 (or
// ?signin=cancelled). The consent screen then opens at once, from /api/me.
const qs = new URLSearchParams(location.search);
if (mode() === "production" && qs.has("consent")) {
  ensureConsent().then(s => { if (s) $("#saveerr").textContent = "Signed in. Press Save and share to save your forecast."; });
} else if (qs.get("signin") === "cancelled") {
  $("#saveerr").textContent = "Sign-in was cancelled. Your forecast is still here.";
}

const t0 = performance.now();
const slow = setTimeout(() => {
  if (!engine && !engineError) $("#enginemsg").textContent += " This is taking a while; on a slow connection it can take a minute.";
}, 20000);
loadSeatEngine({ onStage: stage }).then(e => {
  clearTimeout(slow);
  engine = e;
  const t1 = performance.now();
  afterEdit();
  const firstSeat = Math.round(performance.now() - t1);
  const total = Math.round(performance.now() - t0);
  console.info("seat engine loaded", { ...e.times, first_seat_ms: firstSeat, total_ms: total, code_ref: e.codeRef });
  window.__seatEngineTimes = { ...e.times, first_seat_ms: firstSeat, total_ms: total };
  $("#engine").classList.add("ready");
  $("#enginemsg").textContent = "";
  $("#engineok").textContent = `Seats are worked out in your browser by the project's own seat code, the same code the server runs when you save (loaded in ${(total / 1000).toFixed(1)} s).`;
  lock(false);
  $("#undo").disabled = !history.size;
  $("#maphint").textContent = "Choose a party below, then tap or drag across wards to give them to it.";
}).catch(err => {
  clearTimeout(slow);
  console.error(err);
  engineError = err instanceof SeatCodeMissing ? err.message
    : `The seat law could not load (${err.message || err}). Your forecast is kept in this browser; reload to try again.`;
  $("#engine").classList.add("failed");
  $("#maphint").textContent = "The seat law could not load, so the controls stay locked. Reload to try again.";
  $("#enginemsg").textContent = "";
  render();
});
