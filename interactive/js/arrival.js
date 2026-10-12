// "Your forecast": the view a shared link opens (audits/2026-10-03-share-design
// DESIGN.md §4). A link the share sheet sends goes out as /s/?…, which the
// server answers with this page and `from=1`: the friend's forecast,
// read-only, at the top; the outcome and the chance we give it; three ways on;
// the days to the vote and what happens after the count.
//
// ⛔ A LIVE WRITER (stats.LIVE_WRITERS["your-forecast/js/arrival.js"]) for the
// one region "arrival", reached through the literal selector below, written
// with createElement, textContent and attributes, never markup.
//
// It computes nothing of the model's: make.js hands it the friend's seats
// (the seat law, in the page's seat Worker), the chance and badge
// (page.py analyse, the published forecast), the seal check (the server), and
// the card module's spec (share-card.js forecastSpec), from which the council
// graphic's geometry (councilLayout) is drawn as on the cards, and the number
// of forecasts sealed so far (entries.js, the server's count).

import { entryCount, countLine } from "./entries.js";
import { councilLayout, stepPath, listedRows, cardTitle, chanceSentence, dateText, daysToVote, localStamp, ROWS, PR_OPACITY,
  boldestLine, badgeFile, STAMP_DIR } from "./share-card.js";

const R = document.querySelector('[data-live="arrival"]');
const SVG = "http://www.w3.org/2000/svg";

let chooseCb = () => {};
// cb("friend" | "ours"): the reader picked where section 2 starts.
export function onChoose(cb) { chooseCb = cb; }

function el(tag, props = {}, ...kids) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (v == null || v === false) continue;
    if (k.includes("-") || k === "role") e.setAttribute(k, v === true ? "" : String(v));
    else e[k] = v;
  }
  e.append(...kids.filter(k => k != null && k !== false));
  return e;
}
function sv(tag, attrs = {}, ...kids) {
  const e = document.createElementNS(SVG, tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, String(v));
  e.append(...kids);
  return e;
}
const sw = code => el("span", { className: "sw pc-" + (code || "OTHERS"), "aria-hidden": "true" });
const poss = n => n + (/s$/i.test(n) ? "'" : "'s");
const listAnd = xs => (xs.length < 2 ? xs.join("") : xs.slice(0, -1).join(", ") + " and " + xs[xs.length - 1]);

// The council: one square per seat, the majority line, as on the cards.
function council(spec) {
  const L = councilLayout(spec);
  const cell = 10, gap = 2, s = cell + gap, top = 18;
  const W = L.cols * s - gap, H = top + L.rows * s - gap + 4;
  const g = sv("g", { transform: "translate(0 " + top + ")" });
  for (const c of L.cells) {
    const r = sv("rect", { x: c.col * s, y: c.row * s, width: cell, height: cell, rx: 2, class: "pc-" + c.code });
    if (c.pr) r.setAttribute("fill-opacity", String(PR_OPACITY));
    g.append(r);
  }
  g.append(sv("path", { d: stepPath(L, cell, gap), class: "yf-arr-step" }));
  const label = sv("text", { x: (L.step.col + 1) * s + 4, y: 12, class: "yf-arr-maj" });
  label.textContent = spec.majority + " for a majority";
  return sv("svg", { viewBox: "0 0 " + W + " " + H, class: "yf-arr-council", role: "img",
    "aria-label": spec.council + " seats, each a square; the line marks the " + spec.majority + " needed for a majority" }, g, label);
}

// The ward map, each ward in the colour of the party the friend called.
function wardMap(spec, geom) {
  const paths = geom.wards.map((w, i) => sv("path", { d: w.path, class: "pc-" + spec.calls[i] }));
  return sv("svg", { viewBox: "0 0 " + geom.W + " " + geom.H, class: "yf-arr-map", role: "img",
    "aria-label": "Ward map: each ward in the colour of the party " + spec.name + " called it for" }, ...paths);
}

function table(spec, logo) {
  const head = el("tr", {}, el("th", { scope: "col" }, el("span", { className: "visually-hidden" }, "Party")),
    el("th", { scope: "col", className: "num" }, "Seats"), el("th", { scope: "col", className: "num" }, "Wards"),
    el("th", { scope: "col", className: "num yf-arr-wide" }, "PR"), el("th", { scope: "col", className: "num" }, "Vote"),
    el("th", { scope: "col", className: "num" }, "Seats vs " + spec.baseYear),
    el("th", { scope: "col", className: "num yf-arr-wide" }, "Vote vs " + spec.baseYear + ", points"));
  const rows = listedRows(spec, ROWS.page).map(r => el("tr", {},
    el("th", { scope: "row" }, el("span", { className: "yf-arr-party" },
      r.logo && r.code ? el("img", { src: logo(r.code), alt: "", className: "yf-arr-logo" }) : sw(r.code), r.name)),
    el("td", { className: "num yf-arr-n" }, String(r.seats)), el("td", { className: "num" }, String(r.ward)),
    el("td", { className: "num yf-arr-wide" }, String(r.pr)), el("td", { className: "num" }, r.vote.toFixed(1) + "%"),
    el("td", { className: "num yf-arr-d" }, r.seatsVs), el("td", { className: "num yf-arr-d yf-arr-wide" }, r.voteVs)));
  return el("table", { className: "yf-arr-table" }, el("thead", {}, head), el("tbody", {}, ...rows));
}

function sealLine(seal, election) {
  if (seal.state === "sealed") return "Sealed " + localStamp(seal.at, election) + ".";
  if (seal.state === "not") return "Not sealed.";
  if (seal.state === "unknown") return "The seal could not be checked.";
  return "Checking the seal.";
}

// The view. `v`: { spec, geom, party(code) -> { name, article }, logo(code) -> src, seal: { state: "checking" |
// "sealed" | "not" | "unknown", at }, now (ms) }. spec.outcome is null while
// the chance is being worked out.
export function showArrival(v) {
  const { spec, geom, logo, seal, now } = v;
  const name = spec.name || "A reader";
  const lead = spec.rows[0];
  const o = spec.outcome;
  const count = el("p", { className: "yf-arr-count", hidden: true });
  R.replaceChildren(
    el("p", { className: "yf-arr-from" }, sw(lead && lead.code), "A forecast shared with you. ",
      el("span", { className: "yf-arr-seal", "data-seal": seal.state }, sealLine(seal, spec.election))),
    el("h2", { className: "yf-arr-title" }, cardTitle(spec.name || "A Reader")),
    el("p", { className: "yf-arr-sub" }, spec.election.city + " council, " + dateText(spec.election.date) + ". " +
      spec.council + " seats, " + spec.majority + " for a majority."),
    el("div", { className: "yf-arr-verdict", "aria-live": "polite" },
      el("p", { className: "yf-arr-what" }, o ? spec.words : "Working out the chance we give this call."),
      o ? el("div", { className: "yf-arr-badge" },
        el("img", { src: "../" + STAMP_DIR + "/" + badgeFile(spec.badge), alt: spec.badge, className: "yf-stamp" }),
        el("div", {}, el("p", { className: "yf-arr-call" }, boldestLine(spec.boldest, v.party, poss(name) + " boldest call")),
          spec.chance ? el("p", { className: "yf-arr-chance" }, spec.chance) : null)) : null,
      el("p", { className: "yf-arr-how" }, "The chance is ours, from the forecast as published today. The seats are " + poss(name) +
        ": every ward called, the vote set, and the law seating the result.")),
    el("p", { className: "yf-arr-quick" }, chooseButton("friend", "Make your own, starting from " + poss(name), null, "btn primary")),
    el("div", { className: "yf-arr-grid" },
      el("div", {}, council(spec),
        el("p", { className: "yf-arr-key" }, el("i", { className: "yf-key-ward" }), "ward seats ", el("i", { className: "yf-key-pr" }), "PR seats ",
          el("span", {}, "governing parties first")),
        spec.coalition.length ? el("p", { className: "yf-arr-gov" }, "Governing: ", el("b", {}, listAnd(spec.coalitionNames)),
          ", " + spec.coalitionSeats + " of " + spec.council + " seats.") : el("p", { className: "yf-arr-gov" }, "No governing coalition chosen.")),
      el("div", {}, table(spec, logo),
        el("p", { className: "yf-arr-note" }, "new: not on the " + spec.baseYear + " ballot. Vote: share of the list ballot."),
        geom ? el("figure", { className: "yf-arr-fig" }, wardMap(spec, geom),
          el("figcaption", {}, "Each ward in the colour of the party " + name + " called it for.")) : null,
        spec.excess.length ? el("p", { className: "yf-arr-note" }, spec.excess.join(" ")) : null)),
    el("div", { className: "yf-arr-ctas" },
      el("h3", {}, "Make your own"),
      el("p", {}, "Change any ward, the vote or who governs. The seats follow from the law. When you share yours, the link can show both forecasts side by side."),
      el("div", { className: "yf-arr-btns" },
        chooseButton("friend", "Start from " + poss(name), "Every ward and vote as " + name + " set them", "btn primary"),
        chooseButton("ours", "Start from our forecast", "The model's most likely winners", "btn"),
        el("a", { className: "btn", href: "../forecast" }, "See our forecast", el("small", {}, "Chances for every party and ward")))),
    el("div", { className: "yf-arr-later" },
      el("div", {}, el("h3", {}, "The vote"), countdown(spec.election, now)),
      el("div", {}, el("h3", {}, "After the count"),
        el("p", {}, "Every sealed forecast is ranked against the result: seats per party first, then wards called right, then vote per party. The leaderboard lists names after the count."),
        count)));
  R.hidden = false;
  entryCount().then(n => { count.textContent = countLine(n); count.hidden = !count.textContent; });
}

function chooseButton(kind, text, sub, cls) {
  const b = el("button", { type: "button", className: cls }, text, sub ? el("small", {}, sub) : null);
  b.addEventListener("click", () => chooseCb(kind));
  return b;
}

// "32 days" and when polls open, from forecast.json's election.
function countdown(election, now) {
  const n = daysToVote(now, election);
  const opens = election.polls_open.slice(11, 16);
  const big = n > 0 ? n + (n === 1 ? " day" : " days") : n === 0 ? "Today" : "The count";
  const line = n >= 0 ? "Polls open at " + opens + " on " + dateText(election.date) + "."
    : "Polls opened at " + opens + " on " + dateText(election.date) + ".";
  return el("p", {}, el("span", { className: "yf-arr-big" }, big), el("br"), line);
}

export function hideArrival() {
  R.replaceChildren();
  R.hidden = true;
}
