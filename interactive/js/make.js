// "Make your own forecast". §8 of DESIGN-decided: every control applies to
// every party identically; nothing is pre-selected for one party.

import { loadAll, esc, wireTheme, loadDraft, saveDraft, topN, announce, pageURL, possessive } from "./common.js";
import { WardMap } from "./map.js";
import { allocate } from "./allocator-stub.js";
import { ensureConsent } from "./auth-ui.js";
import { saveForecast, session, deleteForecast } from "./api-stub.js";
import { openShare } from "./share.js";
import { buildCardSVG, cardAlt } from "./card.js";

wireTheme();
const $ = s => document.querySelector(s);
const { geom, model, parties, byCode } = await loadAll();
const N = geom.wards.length;
const codes = parties.map(p => p.code);          // alphabetical, from the fixture

// ---------- state ----------
let from = null;
try { from = JSON.parse(sessionStorage.getItem("jhb-start-from") || "null"); sessionStorage.removeItem("jhb-start-from"); } catch (e) {}
const draft = loadDraft();
const S = {
  calls: draft?.calls?.length === N ? draft.calls : new Array(N).fill(null),
  share: from?.share || draft?.share || { ...model.combined_share },
  coalition: from?.coalition || draft?.coalition || [],
  mayor: from ? (from.mayor || "") : (draft?.mayor || ""),
  brush: null,
  id: from ? null : (draft?.id || null),
};
if (from?.calls) S.calls = from.calls.slice();
const undo = [];

// ---------- map ----------
const map = new WardMap($("#map"), geom, { byCode, onPaint: paintWard });
map.onClear = i => setCall(i, null);
map.setCalls(S.calls);

function pushUndo() {
  undo.push(S.calls.slice()); if (undo.length > 60) undo.shift();
  $("#undo").disabled = false;
}
let strokeOpen = false;
function paintWard(i) {
  if (!S.brush) {
    $("#maphint").textContent = "Choose a party below first, then tap the ward.";
    $("#brush").querySelector("button")?.focus();
    return;
  }
  const v = S.brush === "__erase" ? null : S.brush;
  if (S.calls[i] === v) return;
  if (!strokeOpen) { pushUndo(); strokeOpen = true; }
  S.calls[i] = v; afterCalls();
}
window.addEventListener("pointerup", () => { strokeOpen = false; });
$("#map").addEventListener("keyup", () => { strokeOpen = false; });

function setCall(i, v) { pushUndo(); S.calls[i] = v; afterCalls(); }
function setAll(calls) { pushUndo(); S.calls = calls; afterCalls(); }

// ---------- brush: every party, same chip ----------
$("#brush").innerHTML = parties.map(p =>
  `<button type="button" class="chip" data-c="${p.code}" aria-pressed="false"><span class="sw" style="background:${p.colour}"></span>${esc(p.name)}</button>`
).join("") + `<button type="button" class="chip" data-c="__erase" aria-pressed="false"><span class="sw" style="background:transparent;border:1px dashed var(--ink-3)"></span>Eraser</button>`;
$("#brush").addEventListener("click", e => {
  const b = e.target.closest("[data-c]"); if (!b) return;
  S.brush = S.brush === b.dataset.c ? null : b.dataset.c;
  $("#brush").querySelectorAll("[data-c]").forEach(x => x.setAttribute("aria-pressed", String(x.dataset.c === S.brush)));
  $("#maphint").textContent = S.brush
    ? `Painting with ${S.brush === "__erase" ? "the eraser" : byCode[S.brush].name}. Tap or drag across wards.`
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
  const opts = `<option value="">Not called</option>` + parties.map(p => `<option value="${p.code}">${esc(p.name)}</option>`).join("");
  $("#listview").innerHTML = `<div class="wardlist">` + order.map(sec =>
    `<fieldset><legend>${sec}</legend>` + geom.wards.map((w, i) => w.sector !== sec ? "" :
      `<div class="wl"><label for="wl${i}">Ward ${w.id}</label><select id="wl${i}" data-i="${i}">${opts}</select></div>`).join("") +
    `</fieldset>`).join("") + `</div>`;
  $("#listview").querySelectorAll("select").forEach(s => { s.value = S.calls[+s.dataset.i] || ""; });
}
$("#listview").addEventListener("change", e => {
  const s = e.target.closest("select"); if (s) setCall(+s.dataset.i, s.value || null);
});

// ---------- tools ----------
$("#fillarea").addEventListener("click", () => {
  if (!S.brush) { $("#maphint").textContent = "Choose a party below first, then fill the area."; return; }
  const sec = $("#area").value, v = S.brush === "__erase" ? null : S.brush;
  setAll(S.calls.map((c, i) => geom.wards[i].sector === sec ? v : c));
});
$("#fillempty").addEventListener("click", () =>
  setAll(S.calls.map((c, i) => c || model.likely_ward_winner[geom.wards[i].id])));
$("#copymodel").addEventListener("click", () =>
  setAll(geom.wards.map(w => model.likely_ward_winner[w.id])));
$("#clear").addEventListener("click", () => setAll(new Array(N).fill(null)));
$("#undo").addEventListener("click", () => {
  if (!undo.length) return;
  S.calls = undo.pop(); $("#undo").disabled = !undo.length; afterCalls();
});

// ---------- the vote: one identical row per party ----------
// Each party's share of ALL votes, ward and list ballots together: the combined
// vote the statute seats (DESIGN-decided §10), shown with no conversion.
$("#prlist").innerHTML = parties.map(p => `
  <div class="prrow">
    <span class="sw" style="background:${p.colour}" aria-hidden="true"></span>
    <label for="pr-n-${p.code}">${esc(p.name)}</label>
    <input type="number" id="pr-n-${p.code}" data-c="${p.code}" min="0" max="100" step="0.1" inputmode="decimal">
    <span></span>
    <input type="range" data-c="${p.code}" min="0" max="60" step="0.1" aria-label="${esc(p.name)}, share of all votes, percent">
  </div>`).join("");
function paintShares() {
  $("#prlist").querySelectorAll("input").forEach(i => { i.value = (+S.share[i.dataset.c] || 0).toFixed(1); });
}
$("#prlist").addEventListener("input", e => {
  const i = e.target.closest("input"); if (!i) return;
  const v = Math.max(0, Math.min(100, parseFloat(i.value) || 0));
  S.share[i.dataset.c] = v;
  $("#prlist").querySelectorAll(`input[data-c="${i.dataset.c}"]`).forEach(x => { if (x !== i) x.value = v.toFixed(1); });
  afterShares();
});
$("#prmodel").addEventListener("click", () => { S.share = { ...model.combined_share }; paintShares(); afterShares(); });
$("#przero").addEventListener("click", () => { S.share = Object.fromEntries(codes.map(c => [c, 0])); paintShares(); afterShares(); });
$("#prscale").addEventListener("click", () => {
  const t = shareSum(); if (!t) return;
  S.share = Object.fromEntries(codes.map(c => [c, Math.round((+S.share[c] || 0) / t * 1000) / 10]));
  paintShares(); afterShares();
});
const shareSum = () => codes.reduce((s, c) => s + (+S.share[c] || 0), 0);

// ---------- coalition ----------
$("#coal").addEventListener("click", e => {
  const b = e.target.closest("[data-c]"); if (!b) return;
  const c = b.dataset.c;
  S.coalition = S.coalition.includes(c) ? S.coalition.filter(x => x !== c) : [...S.coalition, c];
  if (!S.coalition.includes(S.mayor)) S.mayor = "";
  recompute();
});
$("#mayor").addEventListener("change", e => { S.mayor = e.target.value; recompute(); });

// ---------- results ----------
let result;
function afterCalls() { map.setCalls(S.calls); if (!$("#listview").hidden) buildList(); recompute(); }
function afterShares() { recompute(); }

function recompute() {
  result = allocate({ wardCalls: S.calls, combinedShare: S.share, parties,
    councilSeats: model.council_seats, wardSeats: model.ward_seats });
  const seats = result.seats;
  const called = S.calls.filter(Boolean).length;
  $("#ncalled").textContent = called;
  $("#nleft").textContent = called < N ? ` ${N - called} to go` : " all called";
  const sum = shareSum();
  $("#prsum").textContent = sum.toFixed(1);
  $("#prwarn").textContent = Math.abs(sum - 100) > 0.5 ? (sum > 100 ? "over 100%" : "under 100%") + " — scale it to save" : "";
  $("#prstate").textContent = `${sum.toFixed(1)}%`;

  // coalition chips: every party, alphabetical like every other control here.
  // Built once and updated in place, so a keyboard user's focus survives a click.
  if (!$("#coal").children.length) {
    $("#coal").innerHTML = codes.map(c => `<button type="button" class="chip" data-c="${c}" aria-pressed="false">
      <span class="sw" style="background:${byCode[c].colour}"></span>${esc(byCode[c].name)} <span class="n" style="color:var(--ink-3)"></span></button>`).join("");
  }
  $("#coal").querySelectorAll("[data-c]").forEach(b => {
    b.setAttribute("aria-pressed", String(S.coalition.includes(b.dataset.c)));
    b.querySelector(".n").textContent = seats[b.dataset.c];
  });
  const order = codes.slice().sort((a, b) => seats[b] - seats[a] || byCode[a].name.localeCompare(byCode[b].name));
  $("#mayor").innerHTML = `<option value="">Not chosen</option>` + S.coalition.map(c =>
    `<option value="${c}"${c === S.mayor ? " selected" : ""}>${esc(byCode[c].name)}</option>`).join("");
  const cs = S.coalition.reduce((a, c) => a + seats[c], 0);
  $("#coalstat").innerHTML = !S.coalition.length ? "No parties chosen yet."
    : `${cs} of ${result.council} seats. ` + (cs >= result.majority ? `<span class="ok">Enough to govern.</span>` : `<span class="no">${result.majority - cs} short of the ${result.majority} needed.</span>`);
  $("#costate").textContent = S.coalition.length ? `${S.coalition.length} ${S.coalition.length === 1 ? "party" : "parties"}, ${cs} seats` : "";

  const top = topN(seats, 5, byCode);
  const max = Math.max(1, ...top.map(t => t[1]));
  $("#bars").innerHTML = top.length ? top.map(([c, n]) => `<div class="bar"><span class="nm">${esc(byCode[c].name)}</span>
    <span class="tr"><span class="fl" style="width:${n / max * 100}%;background:${byCode[c].colour}"></span></span><span class="v">${n}</span></div>`).join("")
    : `<p style="font-size:13.5px">Call some wards or set the vote shares to see seats.</p>`;
  $("#restate").textContent = `Top five of ${result.total} seats` + (called < N ? `, with ${N - called} wards still to call` : "");
  $("#strip").innerHTML = order.filter(c => seats[c]).map(c =>
    `<span style="width:${seats[c] / result.council * 100}%;background:${byCode[c].colour}"></span>`).join("") +
    `<span class="maj" style="left:calc(${(result.majority - 0.5) / result.council} * 100%)"></span>`;
  $("#capseats").textContent = `${result.council} seats`;
  $("#capmaj").textContent = `${result.majority} to govern`;
  $("#coalneed").textContent = `A council of ${result.council} needs ${result.majority} votes`;

  // distance from the model's forecast: seats moved per party, small and factual
  const pub = model.published_seats_median;
  const moved = top.map(([c, n]) => { const d = n - (pub[c] || 0); return `${esc(byCode[c].name)} <b>${d > 0 ? "+" : ""}${d}</b>`; });
  $("#delta").innerHTML = top.length ? `Against the model's forecast (placeholder median): ${moved.join(", ")}.` : "";
  announce($("#live"), top.map(([c, n]) => `${byCode[c].name} ${n}`).join(", "));
  saveDraft({ calls: S.calls, share: S.share, coalition: S.coalition, mayor: S.mayor, id: S.id });
}

// ---------- save and share ----------
function problems() {
  const out = [];
  const left = S.calls.filter(c => !c).length;
  if (left) out.push(`call the last ${left} ward${left === 1 ? "" : "s"}`);
  if (Math.abs(shareSum() - 100) > 0.5) out.push("make the vote shares add up to 100%");
  if (!S.coalition.length) out.push("pick at least one party to govern");
  return out;
}
$("#save").addEventListener("click", async () => {
  const p = problems();
  if (p.length) { $("#saveerr").textContent = "Before saving, " + p.join(", ") + "."; return; }
  $("#saveerr").textContent = "";
  const s = await ensureConsent();
  if (!s) { $("#saveerr").textContent = "Not saved. Your forecast is still here."; return; }
  const forecast = { id: S.id, model_ref: model.model_ref, ward_calls: S.calls.slice(),
    combined_share: { ...S.share }, coalition: S.coalition.slice(), mayor: S.mayor || null };
  const { id, path } = await saveForecast(forecast);
  S.id = id; recompute();
  const url = pageURL(path);
  $("#savedline").innerHTML = `Saved. <a href="${esc(path)}">Open your forecast's page</a> — <button class="linkbtn" type="button" id="del">Delete it</button>`;
  $("#del").addEventListener("click", async () => {
    await deleteForecast(id); S.id = null; recompute();
    $("#savedline").textContent = "Deleted. The link no longer works.";
  });
  const f = { ...forecast, display_name: s.consent.show_name ? s.display_name : "" };
  const council = { council: result.council, majority: result.majority };
  const svgFor = size => buildCardSVG({ forecast: f, seats: result.seats, geom, byCode, model: council, size, placeholder: true });
  openShare({ url, title: possessive(f.display_name) + " — Johannesburg 2026",
    text: `${possessive(f.display_name)} for Johannesburg's council on 4 November. Make yours:`,
    svgFor, alt: cardAlt({ forecast: f, seats: result.seats, byCode, model: council }), fileBase: "joburg-forecast-" + id });
});

paintShares();
recompute();
