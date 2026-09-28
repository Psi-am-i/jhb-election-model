// "Play with the model", against the synthetic draws fixture.
//
// ⛔ STAND-IN. The re-weighting below is a JavaScript sketch of what
// src/reweight.py will do under Pyodide (audits/2026-09-28-interactive-
// architecture/PLAN.md S4). It exists to design the page, not to be shipped:
// the one-definition rule puts the arithmetic in Python, and this file is
// deleted when the page loads reweight.py.
//
//  * Turnout: an exponential tilt on all four pool turnouts at once (PLAN §3:
//    one pool alone is the wrong control, because pools move together).
//    For a normal marginal, weight exp(λ·t) with λ = shift / variance moves
//    that pool's mean by `shift`.
//  * Polls: each draw weighted by closeness of its list-vote shares, renormalised
//    to the polled parties, to the average of the polls switched on (PLAN §5).
//    Trust 0 = uniform weights = the published forecast exactly.
//  * Grid cells and seat laws select a different recorded run (PLAN §6, §7).
//  * Effective draws (Kish) shown beside the result; below the floor the page
//    refuses to show a figure.

import { loadAll, loadJSON, esc, wireTheme, announce } from "./common.js";

wireTheme();
const $ = s => document.querySelector(s);
const [{ model, byCode }, D] = await Promise.all([loadAll(), loadJSON("placeholder-draws.json")]);
const P = D.parties;

const st = {
  shift: Object.fromEntries(D.pools.map(p => [p, 0])),
  polls: Object.fromEntries(D.polls.map(p => [p.id, true])),
  trust: 0,
  ds: D.grid_default.dirichlet_scale,
  wb: D.grid_default.w_bye,
  law: "deduct",
};
const cell = () => D.cells[`ds${st.ds}_wb${st.wb}`];

// ---------- controls ----------
$("#turnout").innerHTML = D.pools.map(p => `<div class="slider">
  <label for="t-${p}">${esc(D.pool_labels[p])}</label>
  <input type="range" id="t-${p}" data-pool="${p}" min="-5" max="5" step="0.5" value="0">
  <output for="t-${p}" id="to-${p}">0</output></div>`).join("");
$("#turnout").addEventListener("input", e => {
  const p = e.target.dataset.pool; if (!p) return;
  st.shift[p] = +e.target.value;
  $("#to-" + p).textContent = (st.shift[p] > 0 ? "+" : "") + st.shift[p];
  update();
});

const polled = [...new Set(D.polls.flatMap(p => Object.keys(p.shares)))];
$("#polls").innerHTML = `<thead><tr><th scope="col">Use</th><th scope="col">Poll</th>` +
  polled.map(c => `<th scope="col">${esc(byCode[c].name)}</th>`).join("") + `</tr></thead><tbody>` +
  D.polls.map(p => `<tr><td><input type="checkbox" data-poll="${p.id}" checked aria-label="Use ${esc(p.house)}"></td>
    <td>${esc(p.house)}<br><span class="cav">${esc(p.date)}, ${p.n.toLocaleString("en-ZA")} people. ${esc(p.caveat)}</span></td>` +
    polled.map(c => `<td>${p.shares[c] ?? "—"}</td>`).join("") + `</tr>`).join("") +
  `<tr><td></td><td><b>Spread across the polls switched on</b></td>` + polled.map(c => `<td id="spr-${c}"></td>`).join("") + `</tr></tbody>`;
$("#polls").addEventListener("change", e => {
  const id = e.target.dataset.poll; if (!id) return;
  st.polls[id] = e.target.checked; update();
});
$("#trust").addEventListener("input", e => { st.trust = +e.target.value; $("#trustv").textContent = st.trust; update(); });

function seg(el, key, vals, labels) {
  $(el).innerHTML = vals.map((v, i) => `<button type="button" data-v="${v}" aria-pressed="${v === st[key]}">${labels[i]}</button>`).join("");
  $(el).addEventListener("click", e => {
    const b = e.target.closest("[data-v]"); if (!b) return;
    st[key] = +b.dataset.v;
    $(el).querySelectorAll("button").forEach(x => x.setAttribute("aria-pressed", String(x === b)));
    update();
  });
}
const lab = (vals, def, names) => vals.map((v, i) => v === def ? names[i] + " (model)" : names[i]);
seg("#ds", "ds", D.grid.dirichlet_scale, lab(D.grid.dirichlet_scale, D.grid_default.dirichlet_scale, ["Less", "Middle", "More"]));
seg("#wb", "wb", D.grid.w_bye, lab(D.grid.w_bye, D.grid_default.w_bye, ["None", "Some", "Full"]));

$("#laws").innerHTML = Object.entries(D.laws).map(([k, l]) => `<label style="display:flex;gap:8px;align-items:flex-start;margin:6px 0;font-size:13.5px">
  <input type="radio" name="law" value="${k}"${k === st.law ? " checked" : ""} style="margin-top:4px;accent-color:var(--accent)"><span>${esc(l)}</span></label>`).join("");
$("#laws").addEventListener("change", e => { st.law = e.target.value; update(); });

// ---------- the stand-in re-weighting ----------
function weights(draws) {
  const n = draws.length;
  const w = new Array(n).fill(1);
  D.pools.forEach((p, k) => {
    const s = st.shift[p] / 100; if (!s) return;
    const xs = draws.map(d => d.t[k]);
    const m = xs.reduce((a, b) => a + b, 0) / n;
    const v = xs.reduce((a, b) => a + (b - m) ** 2, 0) / n;
    const lam = s / v;
    xs.forEach((x, i) => { w[i] *= Math.exp(lam * (x - m)); });
  });
  const on = D.polls.filter(p => st.polls[p.id]);
  if (st.trust > 0 && on.length) {
    const avg = {};
    for (const c of polled) {
      const v = on.map(p => p.shares[c]).filter(x => x != null);
      avg[c] = v.reduce((a, b) => a + b, 0) / v.length;
    }
    const at = polled.reduce((a, c) => a + avg[c], 0);
    const sigma = 3 + 27 * (1 - st.trust / 100) ** 2;   // stand-in: 30pp near 0, 3pp at 100 (PLAN §5 measured 3pp). The real mapping is a design decision.
    const idx = polled.map(c => P.indexOf(c));
    draws.forEach((d, i) => {
      const tot = idx.reduce((a, j) => a + d.pr[j], 0);
      let q = 0;
      polled.forEach((c, k) => { q += (d.pr[idx[k]] / tot * 100 - avg[c] / at * 100) ** 2; });
      w[i] *= Math.exp(-q / (2 * sigma * sigma));
    });
  }
  return w;
}

function wquant(vals, w, q) {
  const o = vals.map((v, i) => [v, w[i]]).sort((a, b) => a[0] - b[0]);
  const tot = o.reduce((a, b) => a + b[1], 0);
  let acc = 0;
  for (const [v, wi] of o) { acc += wi; if (acc >= q * tot) return v; }
  return o.at(-1)[0];
}

function summary(draws, w) {
  const out = {};
  P.forEach((c, k) => {
    const v = draws.map(d => d.seats[st.law][k]);
    out[c] = [wquant(v, w, 0.05), wquant(v, w, 0.5), wquant(v, w, 0.95)];
  });
  return out;
}

const base = (() => { const d = D.cells[`ds${D.grid_default.dirichlet_scale}_wb${D.grid_default.w_bye}`];
  const save = st.law; st.law = "deduct"; const s = summary(d, d.map(() => 1)); st.law = save; return s; })();
let lastPR = null;

function update() {
  const draws = cell();
  const w = weights(draws);
  const sw = w.reduce((a, b) => a + b, 0), sw2 = w.reduce((a, b) => a + b * b, 0);
  const ess = sw * sw / sw2;
  const floor = D.refusal_floor_fraction * draws.length;
  const touched = Object.values(st.shift).some(Boolean) || st.trust > 0 ||
    st.ds !== D.grid_default.dirichlet_scale || st.wb !== D.grid_default.w_bye || st.law !== "deduct";

  // spread across enabled polls
  const on = D.polls.filter(p => st.polls[p.id]);
  polled.forEach(c => {
    const v = on.map(p => p.shares[c]).filter(x => x != null);
    $("#spr-" + c).textContent = v.length ? `${Math.min(...v)}–${Math.max(...v)}` : "—";
  });

  $("#ess").textContent = `${Math.round(ess)} effective simulations of ${draws.length}` + (touched ? "" : " — the published forecast");
  $("#ess").classList.toggle("low", ess < floor);
  if (ess < floor) {
    $("#seats").innerHTML = `<tbody><tr><td>Too few simulations match these settings to say anything. Move a control back towards the middle.</td></tr></tbody>`;
    $("#seats").classList.add("greyed");
    $("#tomake").disabled = true;
    return;
  }
  $("#seats").classList.remove("greyed"); $("#tomake").disabled = false;
  const s = summary(draws, w);
  const rows = P.filter(c => s[c][2] > 0).sort((a, b) => s[b][1] - s[a][1] || byCode[a].name.localeCompare(byCode[b].name));
  $("#seats").innerHTML = `<thead><tr><th scope="col">Party</th><th scope="col">Middle</th><th scope="col">Range</th><th scope="col">Change</th></tr></thead><tbody>` +
    rows.map(c => { const d = s[c][1] - base[c][1];
      return `<tr><td><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${byCode[c].colour};margin-right:6px"></span>${esc(byCode[c].name)}</td>
      <td><b>${s[c][1]}</b></td><td>${s[c][0]}–${s[c][2]}</td><td class="chg">${d ? (d > 0 ? "+" : "") + d : "—"}</td></tr>`; }).join("") + `</tbody>`;
  $("#bandnote").textContent = "Middle is the median seat count; range covers nine in ten of the weighted simulations. " +
    (touched ? "Fewer effective simulations make the range less certain than the published one." : "");
  // on a phone the results sit below every control, so the top of them rides along
  $("#msum").innerHTML = rows.slice(0, 4).map(c => `<span><span class="sw" style="background:${byCode[c].colour}"></span>${esc(byCode[c].name)} <b>${s[c][1]}</b></span>`).join("") +
    `<span class="ess">${Math.round(ess)} eff.</span>`;
  announce($("#live"), rows.slice(0, 5).map(c => `${byCode[c].name} ${s[c][1]}`).join(", "));

  lastPR = Object.fromEntries(P.map((c, k) => [c,
    Math.round(draws.reduce((a, d, i) => a + d.pr[k] * w[i], 0) / sw * 10) / 10]));
}

$("#reset").addEventListener("click", () => { location.reload(); });
$("#tomake").addEventListener("click", () => {
  try {
    sessionStorage.setItem("jhb-start-from", JSON.stringify({
      calls: null, pr: lastPR, coalition: [], mayor: "" }));
  } catch (e) {}
  location.href = "make.html";
});

update();
