// The shared forecast page, /f/<id>. In the prototype the id comes from
// ?id=; in production from the path, and the Worker has already rendered the
// same content server-side (see the comment at the top of f/index.html).

import { loadAll, loadSchema, esc, wireTheme, topN, fmtDate, possessive, pageURL } from "./common.js";
import { WardMap } from "./map.js";
import { getForecast } from "./api.js";
import { openShare } from "./share.js";
import { buildCardSVG, cardAlt } from "./card.js";

wireTheme();
const $ = s => document.querySelector(s);
const { geom, model, parties, byCode } = await loadAll();
const id = new URLSearchParams(location.search).get("id") || "demo7Qx2Lp";
const f = /^[A-Za-z0-9]{6,16}$/.test(id) ? await getForecast(id) : null;

if (!f || f.gone) {
  document.title = f?.gone ? "Forecast deleted" : "Forecast not found";
  $("#main").innerHTML = `<header class="lede"><h1>${f?.gone ? "This forecast was deleted" : "We can't find that forecast"}</h1>
    <p>${f?.gone ? "Its maker deleted it, so the link no longer works." : "The link may be mistyped, or the forecast was never saved."}
    You can <a href="../make.html">make your own forecast</a> or see <a href="../../site/forecast.html">the model's</a>.</p></header>`;
} else {
  const title = possessive(f.display_name);
  document.title = `${title} · Johannesburg 2026`;
  $("#title").textContent = title;
  $("#made").textContent = `Made ${fmtDate(f.created_at)}` + (f.model_ref ? `. Compared with model run ${f.model_ref}.` : ".");

  const map = new WardMap($("#map"), geom, { byCode, readonly: true });
  map.setCalls(f.ward_calls);
  $("#map").setAttribute("aria-label", `${title}: ward map of Johannesburg, north to the right, each ward coloured by the party they expect to win it`);
  document.querySelectorAll("[data-view]").forEach(b => b.addEventListener("click", () => {
    document.querySelectorAll("[data-view]").forEach(x => x.setAttribute("aria-pressed", String(x === b)));
    map.setMode(b.dataset.view);
  }));

  // The seats stored with the forecast: the server's own recomputation at
  // save (worker-api/src/seats.js), or in the stub the page's, from the same
  // code. A forecast stored without them (the demo fixture) is seated here by
  // the same engine the builder runs.
  let stored = f.seats;
  if (!stored) {
    $("#restate").textContent = "Working out the seats…";
    const [{ loadSeatEngine }, schema] = await Promise.all([import("./seat-engine.js"), loadSchema()]);
    const out = (await loadSeatEngine()).seats(f, schema);
    if (!out.ok) throw new Error("the seat law refused this forecast: " + out.errors.join("; "));
    stored = out.answer;
  }
  const seats = stored.seats;
  const wins = {};
  for (const c of f.ward_calls) wins[c] = (wins[c] || 0) + 1;
  const r = { council: stored.council_total, majority: stored.majority };
  const council = { council: r.council, majority: r.majority };   // as seated, for the card
  $("#legend").innerHTML = Object.entries(wins).filter(([, n]) => n).sort((a, b) => b[1] - a[1])
    .map(([c, n]) => `<span style="white-space:nowrap"><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${byCode[c].colour};margin-right:4px"></span>${esc(byCode[c].name)} ${n}</span>`)
    .join("&ensp; ") + " wards";

  const top = topN(seats, 5, byCode);
  const max = Math.max(1, ...top.map(t => t[1]));
  $("#restate").textContent = `Top five of ${r.council} seats`;
  $("#bars").innerHTML = top.map(([c, n]) => `<div class="bar"><span class="nm">${esc(byCode[c].name)}</span>
    <span class="tr"><span class="fl" style="width:${n / max * 100}%;background:${byCode[c].colour}"></span></span><span class="v">${n}</span></div>`).join("");
  const order = Object.keys(seats).filter(c => seats[c]).sort((a, b) => seats[b] - seats[a]);
  $("#strip").innerHTML = order.map(c => `<span style="width:${seats[c] / r.council * 100}%;background:${byCode[c].colour}"></span>`).join("") +
    `<span class="maj" style="left:calc(${(r.majority - 0.5) / r.council} * 100%)"></span>`;
  $("#capseats").textContent = `${r.council} seats`;
  $("#capmaj").textContent = `${r.majority} to govern`;
  const cs = f.coalition.reduce((a, c) => a + (seats[c] || 0), 0);
  $("#coal").innerHTML = f.coalition.map(c => `<b>${esc(byCode[c].name)}</b>`).join(", ") +
    ` — ${cs} of ${r.council} seats, ` + (cs >= r.majority ? "a majority." : `${r.majority - cs} short of the ${r.majority} needed.`) +
    (f.mayor ? ` Mayor from ${esc(byCode[f.mayor].name)}.` : "");
  const pub = model.published_seats_median;
  $("#delta").innerHTML = "Against the model's forecast (placeholder median): " +
    top.map(([c, n]) => { const d = n - (pub[c] || 0); return `${esc(byCode[c].name)} <b>${d > 0 ? "+" : ""}${d}</b>`; }).join(", ") + ".";

  $("#mk").addEventListener("click", () => {
    try { sessionStorage.setItem("jhb-start-from", JSON.stringify({ calls: f.ward_calls, share: f.combined_share, coalition: f.coalition, mayor: f.mayor })); } catch (e) {}
  });
  $("#mk").querySelector(".t").textContent = "Make your own, starting from this one";

  $("#share").addEventListener("click", () => openShare({
    url: pageURL("f/?id=" + id), title: `${title} · Johannesburg 2026`,
    text: `${title} for Johannesburg's council on 4 November. Make yours:`,
    svgFor: size => buildCardSVG({ forecast: f, seats, geom, byCode, model: council, size, placeholder: true }),
    alt: cardAlt({ forecast: f, seats, byCode, model: council }), fileBase: "joburg-forecast-" + id,
  }));
}
