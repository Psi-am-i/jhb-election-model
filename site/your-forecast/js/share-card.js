// The share cards of a reader's own forecast (/your-forecast/ section 2,
// "Break the model"): the link preview (1200 x 630), the story card
// (1080 x 1920) and the return card that sets two forecasts side by side
// (1200 x 630). ONE MODULE for the page's download (make-share.js, drawn to a
// canvas by card-text.js's svgToPNG) and the edge's link preview
// (src/worker.js, rasterised by resvg in src/og-render.js). The design is
// audits/2026-10-03-share-design/DESIGN.md §2; its decisions DECISIONS.md.
//
// PURE: no DOM, no fetch, no figure of its own. The caller hands it the seats
// the seat law gave the reader's picks, the chance and badge the published
// forecast gives the reader's outcome (reweight.outcome_chance, in Python),
// the reader's vote shares, the previous election's figures (forecast.json
// `baseline`), each party's name, article, colour and logo flag, and every
// image as a data: URI. It names no party and holds no colour of one (DESIGN
// §2 "Neutrality"): rows go in the reader's seat order, ties by name; the
// band across the top follows the largest party, whoever it is, and a tie
// for the most seats splits it equally.
//
// ⛔ A LIVE WRITER WITH NO REGION (stats.LIVE_WRITERS["your-forecast/js/share-card.js"]):
// it turns what it is handed into SVG text, and reaches no element of a page.
//
// Text is laid out by measured width in the faces that draw it
// (card-fonts.js, IBM Plex). resvg has those fonts at the edge; a browser
// drawing an SVG as an image cannot fetch web fonts, so the page passes the
// same faces as data: URIs in `fontCSS`.
//
// THE COUNCIL GRAPHIC. Every seat a square, ten to a column, filled column by
// column: the governing parties first, in seat order, then the rest; within
// a party its ward seats solid, then its PR seats tinted. A stepped line
// encloses the first (majority - 1) seats, so a block that crosses it holds a
// majority (councilLayout, which the arrival view draws too).

import { FACES } from "./card-fonts.js";

export const SIZES = { link: [1200, 630], story: [1080, 1920], duel: [1200, 630] };
export const SITE = "joburg.whysoserious.city";
// How many party rows each card lists before "Others".
export const ROWS = { link: 6, story: 6, duel: 7, page: 9, phone: 7 };
// The colour of the "Others" row: a neutral grey, no party's.
export const OTHERS_COLOUR = "#464d47";
// A PR seat's square, against a ward seat's.
export const PR_OPACITY = 0.42;
// The lowest a story card's words may sit: story apps lay their reply bar
// over the band below it.
export const STORY_TEXT_BOTTOM = 1660;
const C = { paper: "#141715", paper2: "#1c201d", rule: "#333833", ink: "#eceee9", ink2: "#b6bcb6", ink3: "#868d86", chip: "#ffffff" };
const MONTHS = "January February March April May June July August September October November December".split(" ");
const DAY_MS = 864e5;

// ---------- words ----------

// "Thandi's Election Forecast" (owner, 2026-10-03: Title Case).
export function cardTitle(name) {
  if (!name) return "My Election Forecast";
  return name + (/s$/i.test(name) ? "'" : "'s") + " Election Forecast";
}

// "We give this outcome a 26% chance." The owner's wording (2026-10-03); a
// chance printed as "under 0.1%" or "over 99%" reads "a chance of under 0.1%".
export function aChance(text) {
  if (!/^\d/.test(text)) return "a chance of " + text;
  return (/^(8|11|18)(\D|$)|^8\d/.test(text) ? "an " : "a ") + text + " chance";
}
export function chanceSentence(text) {
  return "We give this outcome " + aChance(text) + ".";
}

const cap = s => s.charAt(0).toUpperCase() + s.slice(1);
const listAnd = xs => (xs.length < 2 ? xs.join("") : xs.slice(0, -1).join(", ") + " and " + xs[xs.length - 1]);
// "−19", "+15", "±0": the sign is always printed.
export function signed(x, dp = 0) {
  const v = Number(x.toFixed(dp));
  return (v > 0 ? "+" : v < 0 ? "−" : "±") + Math.abs(v).toFixed(dp);
}

// The reader's council-level outcome in words, exactly as the chance reads it
// (reweight.council_outcome): the largest party, or a tie for the most seats;
// a majority alone or not; the chosen coalition governing.
export function outcomeWords(o, party) {
  const the = c => (party(c).article || "") + party(c).name;
  const lead = o.largest ? cap(the(o.largest)) + (o.majority_alone ? " wins a majority of its own" : " is the largest party")
    : "Two or more parties tie for the most seats";
  const maj = o.majority_alone ? "" : ", no party has a majority";
  const gov = o.coalition.length ? ", and " + listAnd(o.coalition.map(the)) + (o.coalition.length === 1 ? " governs" : " govern") : "";
  return lead + maj + gov + ".";
}

// "4 November 2026" from "2026-11-04".
export function dateText(iso) {
  const [y, m, d] = iso.slice(0, 10).split("-").map(Number);
  return d + " " + MONTHS[m - 1] + " " + y;
}

// The election's own clock: polls_open carries the offset ("+02:00").
function offsetMs(election) {
  const m = /([+-])(\d\d):(\d\d)$/.exec(election.polls_open);
  return m ? (m[1] === "-" ? -1 : 1) * (Number(m[2]) * 60 + Number(m[3])) * 60000 : 0;
}
// An instant as the election's local date and time: "3 October 2026, 14:05 SAST".
export function localStamp(ms, election) {
  const d = new Date(ms + offsetMs(election));
  const iso = d.toISOString();
  return dateText(iso) + ", " + iso.slice(11, 16) + " " + election.zone;
}
// Whole local days from the instant `ms` to polling day.
export function daysToVote(ms, election) {
  const local = Math.floor((ms + offsetMs(election)) / DAY_MS);
  const vote = Math.floor(Date.parse(election.date + "T00:00:00Z") / DAY_MS);
  return vote - local;
}
export function daysText(n, before = true) {
  if (n === 0) return "polling day";
  if (n < 0) return "after the vote";
  return n + (n === 1 ? " day" : " days") + (before ? " before the vote" : " to the vote");
}

// ---------- the forecast, as every card reads it ----------

// Every party with a seat, most seats first, ties by name.
export function seatOrder(seats, party) {
  return Object.keys(seats).filter(c => seats[c] > 0)
    .sort((a, b) => seats[b] - seats[a] || party(a).name.localeCompare(party(b).name));
}

// The first `n` of `list`, where the cut never falls between two parties with
// the same seats (review 2026-10-02): a tie at the cut takes the whole group
// if it ends by n + 1, else leaves it all to Others.
export function cutAt(list, seats, n) {
  let cut = list.length > n + 1 ? n : list.length;
  if (cut < list.length && seats[list[cut - 1]] === seats[list[cut]]) {
    let end = cut;
    while (end < list.length && seats[list[end]] === seats[list[cut - 1]]) end++;
    if (end <= n + 1) cut = end;
    else while (cut > 0 && seats[list[cut - 1]] === seats[list[cut]]) cut--;
  }
  return list.slice(0, cut);
}

// The forecast every card and the arrival view draw: { name, title, council,
// majority, rows: [{ code, name, colour, logo, seats, ward, pr, vote,
// seatsVs, voteVs }] in seat order, coalition (in seat order), coalitionSeats,
// outcome, words, chance, badge, excess: [sentences], calls, made }.
//   answer   the seat law's { seats, ward, pr, council_total, majority, excessive }
//   outcome  { largest, majority_alone, coalition, text, badge } (Python)
//   vote     { code: percent of the combined vote }
//   baseline forecast.json `baseline` ({ year, seats, wards, vote }), or null
//   made     { at: ms, sealed: bool } or null: when the card says it was made
export function forecastSpec({ name, answer, outcome, vote, calls, party, baseline, election, made = null }) {
  const { seats, ward = {}, pr = {}, council_total: council, majority, excessive = {} } = answer;
  const base = baseline || { seats: {}, vote: {} };
  const order = seatOrder(seats, party);
  const rows = order.map(c => ({
    code: c, name: party(c).name, colour: party(c).colour, logo: !!party(c).logo,
    seats: seats[c], ward: ward[c] || 0, pr: pr[c] || 0, vote: vote[c] || 0,
    seatsVs: c in base.vote ? signed(seats[c] - (base.seats[c] || 0)) : "new",
    voteVs: c in base.vote ? signed((vote[c] || 0) - base.vote[c], 1) : "new",
  }));
  const coalition = order.filter(c => outcome.coalition.includes(c));
  const the = c => (party(c).article || "") + party(c).name;
  return {
    name, title: cardTitle(name), council, majority, election, rows, calls, made,
    coalition, coalitionNames: coalition.map(c => party(c).name),
    coalitionSeats: coalition.reduce((a, c) => a + seats[c], 0),
    outcome, words: outcomeWords(outcome, party), chance: chanceSentence(outcome.text), badge: outcome.badge,
    // the most seats: one party, or every party tied for them (the band splits)
    top: order.filter(c => seats[c] === seats[order[0]]),
    excess: Object.entries(excessive).filter(([, v]) => v > 0).map(([c, v]) =>
      cap(the(c)) + " wins " + v + (v === 1 ? " more ward" : " more wards") + " than its vote entitles it to seats. It keeps them, and gets no PR seats."),
    baseYear: base.year || null,
  };
}

// The rows a card lists: the first n by seats, the rest summed as Others.
export function listedRows(spec, n) {
  const seats = Object.fromEntries(spec.rows.map(r => [r.code, r.seats]));
  const shown = cutAt(spec.rows.map(r => r.code), seats, n);
  const rows = spec.rows.slice(0, shown.length);
  const rest = spec.rows.slice(shown.length);
  if (!rest.length) return rows;
  const sum = k => rest.reduce((a, r) => a + r[k], 0);
  return [...rows, { code: null, name: "Others", colour: OTHERS_COLOUR, logo: false, others: true,
    seats: sum("seats"), ward: sum("ward"), pr: sum("pr"), vote: sum("vote"), seatsVs: "", voteVs: "" }];
}

// "Sealed 3 October 2026, 14:05 SAST" or "Made 3 October 2026", or "" when
// the card has no trustworthy date (an unsealed link at the edge).
export function madeText(spec) {
  if (!spec.made) return "";
  return spec.made.sealed ? "Sealed " + localStamp(spec.made.at, spec.election)
    : "Made " + dateText(new Date(spec.made.at + offsetMs(spec.election)).toISOString());
}

// ---------- the council graphic's geometry ----------

// { cells: [{ i, code, colour, pr, col, row }], cols, rows, step: { col, row } }:
// the order the seats fill and where the majority line steps. The line
// encloses cells 0 .. majority - 2. ONE DEFINITION for the cards and the
// arrival view (arrival.js draws it into the page).
export function councilLayout(spec, perCol = 10) {
  const first = spec.rows.filter(r => spec.coalition.includes(r.code));
  const rest = spec.rows.filter(r => !spec.coalition.includes(r.code));
  const cells = [];
  for (const r of [...first, ...rest]) {
    for (let k = 0; k < r.ward; k++) cells.push({ code: r.code, colour: r.colour, pr: false });
    for (let k = 0; k < r.pr; k++) cells.push({ code: r.code, colour: r.colour, pr: true });
  }
  cells.forEach((c, i) => { c.i = i; c.col = Math.floor(i / perCol); c.row = i % perCol; });
  const k = spec.majority - 1;
  return { cells, cols: Math.ceil(spec.council / perCol), rows: perCol, step: { col: Math.floor(k / perCol), row: k % perCol } };
}

// The majority line as an SVG path in a grid of `cell` squares `gap` apart,
// from `over` above the grid to `over` below it.
export function stepPath(layout, cell, gap, over = 4) {
  const s = cell + gap, { col, row } = layout.step;
  const xa = col * s - gap / 2, xb = (col + 1) * s - gap / 2, ym = row * s - gap / 2;
  const y0 = -over, y1 = layout.rows * s - gap + over;
  return row === 0 ? `M${xa} ${y0}V${y1}` : `M${xb} ${y0}V${ym}H${xa}V${y1}`;
}

// ---------- text, measured ----------

const WIDEST = Object.fromEntries(Object.entries(FACES).map(([k, f]) => [k, Math.max(...Object.values(f.w))]));
export function textWidth(s, fs, face = "sans") {
  const f = FACES[face];
  let u = 0;
  for (const ch of String(s)) u += f.w[ch.codePointAt(0)] ?? WIDEST[face];
  return u * fs / f.em;
}
// `s` at the largest size from fs down to minFs that fits maxW; below that,
// cut with an ellipsis until it fits.
export function fitText(s, maxW, fs, face = "sans", minFs = fs * 0.75) {
  const w = textWidth(s, fs, face);
  if (w <= maxW) return { text: s, fs };
  const f = Math.max(minFs, Math.floor(fs * maxW / w * 10) / 10);
  if (textWidth(s, f, face) <= maxW) return { text: s, fs: f };
  const chars = [...String(s)];
  while (chars.length > 1 && textWidth(chars.join("") + "…", f, face) > maxW) chars.pop();
  return { text: chars.join("").trimEnd() + "…", fs: f };
}
export function wrapText(s, maxW, fs, face = "sans") {
  const out = [];
  let cur = "";
  for (const w of String(s).split(" ")) {
    const next = cur ? cur + " " + w : w;
    if (cur && textWidth(next, fs, face) > maxW) { out.push(cur); cur = w; } else cur = next;
  }
  if (cur) out.push(cur);
  return out;
}

const esc = s => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const n1 = v => Number(v.toFixed(1));
function text(x, y, s, fs, face = "sans", { fill = C.ink, anchor = "", opacity = null } = {}) {
  const f = FACES[face];
  return `<text x="${n1(x)}" y="${n1(y)}" font-family="${f.family}" font-weight="${f.weight}" font-size="${n1(fs)}"` +
    `${anchor ? ` text-anchor="${anchor}"` : ""}${opacity == null ? "" : ` fill-opacity="${opacity}"`} fill="${fill}">${esc(s)}</text>`;
}
const rect = (x, y, w, h, fill, extra = "") => `<rect x="${n1(x)}" y="${n1(y)}" width="${n1(w)}" height="${n1(h)}" fill="${fill}"${extra}/>`;

// ---------- pieces ----------

// The band across the top, in the largest party's colour; split for a tie.
function band(spec, W, h, party) {
  const tops = spec.top.length ? spec.top : [null];
  const w = W / tops.length;
  return tops.map((c, k) => rect(k * w, 0, w + 0.5, h, c ? spec.rows.find(r => r.code === c).colour : OTHERS_COLOUR)).join("");
}

// The site's logo (site/logo.svg, the tower J and lettering), `h` tall, in ink.
function brand(assets, x, y, h) {
  const b = assets.brand;
  if (!b) return "";
  const [, , vw, vh] = b.viewBox.split(/\s+/).map(Number);
  return `<svg x="${n1(x)}" y="${n1(y)}" width="${n1(h * vw / vh)}" height="${n1(h)}" viewBox="${b.viewBox}" fill="${C.ink}">${b.body}</svg>`;
}
export function brandWidth(assets, h) {
  if (!assets.brand) return 0;
  const [, , vw, vh] = assets.brand.viewBox.split(/\s+/).map(Number);
  return h * vw / vh;
}

// A party's chip: its logo on white where it has one, else its colour.
function chip(r, x, y, s, assets) {
  const src = r.logo && r.code ? (assets.logos || {})[r.code] : null;
  const rx = Math.max(2, s / 6.5);
  if (!src) return rect(x, y, s, s, r.colour, ` rx="${n1(rx)}"`);
  return rect(x, y, s, s, C.chip, ` rx="${n1(rx)}"`) +
    `<image x="${n1(x + 1)}" y="${n1(y + 1)}" width="${n1(s - 2)}" height="${n1(s - 2)}" href="${src}" preserveAspectRatio="xMidYMid meet"/>`;
}

// The council at (x, y): its label, the squares and the majority line.
// Returns { svg, w, h } (h includes the label).
function council(spec, x, y, { width, cell: want, gap, fs = 15, label = true }) {
  const L = councilLayout(spec);
  const step = Math.min(want + gap, Math.floor((width + gap) / L.cols * 10) / 10);
  const cell = step - gap;
  const top = label ? fs + 10 : 0;
  const ox = x, oy = y + top;
  let s = L.cells.map(c => rect(ox + c.col * step, oy + c.row * step, cell, cell, c.colour,
    ` rx="${n1(Math.max(1, cell / 6))}"${c.pr ? ` fill-opacity="${PR_OPACITY}"` : ""}`)).join("");
  s += `<path transform="translate(${n1(ox)} ${n1(oy)})" d="${stepPath(L, cell, gap)}" fill="none" stroke="${C.ink}" stroke-width="${Math.max(2, gap)}"/>`;
  if (label) {
    const lx = ox + (L.step.col + 1) * step - gap / 2 + 6;
    const words = spec.majority + " for a majority";
    const anchor = lx + textWidth(words, fs) > x + width ? "end" : "";
    s += text(anchor ? ox + L.step.col * step - 6 : lx, y + fs, words, fs, "sans", { fill: C.ink2, anchor });
  }
  return { svg: s, w: L.cols * step - gap, h: top + L.rows * step - gap };
}

// The ward map, `w` wide, each ward in the colour of the party called for it.
function wardMap(spec, geom, party, x, y, w) {
  const s = w / geom.W;
  const paths = geom.wards.map((wd, i) =>
    `<path d="${wd.path}" fill="${party(spec.calls[i]).colour}" stroke="${C.paper}" stroke-width="${n1(0.8 / s)}" stroke-linejoin="round"/>`).join("");
  return { svg: `<g transform="translate(${n1(x)} ${n1(y)}) scale(${s.toFixed(4)})">${paths}</g>`, h: geom.H * s };
}

// The badge: the words in a pill, after `x` on the baseline `y`.
function badge(words, x, y, fs, stroke = 1.5) {
  const w = textWidth(words, fs, "sansSemi") + fs * 1.4;
  const h = fs * 1.55;
  return { w, svg: `<rect x="${n1(x)}" y="${n1(y - fs * 1.12)}" width="${n1(w)}" height="${n1(h)}" rx="${n1(h / 2)}" fill="none" stroke="${C.ink2}" stroke-width="${stroke}"/>` +
    text(x + fs * 0.7, y, words, fs, "sansSemi") };
}

function svgOpen(W, H, assets) {
  const css = assets.fontCSS ? `<style>${assets.fontCSS}</style>` : "";
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">${css}${rect(0, 0, W, H, C.paper)}`;
}

// ---------- the link preview, 1200 x 630 ----------

export function linkCardSVG(spec, assets = {}, party) {
  const [W, H] = SIZES.link;
  const X = 48, R = W - 48;
  let s = svgOpen(W, H, assets) + band(spec, W, 10, party);
  const bh = 118, bw = brandWidth(assets, bh);
  s += brand(assets, R + 4 - bw, 30, bh);
  const head = fitText(spec.title, Math.min(900, R - bw - 24 - X), 56, "serifSemi", 40);
  s += text(X, 124, head.text, head.fs, "serifSemi");
  s += text(X, 162, spec.election.city + " council, " + dateText(spec.election.date) + ", " + spec.council + " seats.", 20, "sans", { fill: C.ink2 });
  const made = madeText(spec);
  if (made) s += text(X, 189, made + ", " + daysText(daysToVote(spec.made.at, spec.election)) + ".", 20, "sans", { fill: C.ink2 });
  const g = council(spec, X, 214, { width: 600, cell: 18, gap: 3, fs: 15 });
  s += g.svg;
  if (spec.coalition.length) {
    const lead = "Governing: ", names = listAnd(spec.coalitionNames), tail = ", " + spec.coalitionSeats + " seats.";
    const y = 214 + g.h + 34;
    s += text(X, y, lead, 22) + text(X + textWidth(lead, 22), y, names, 22, "sansSemi") +
      text(X + textWidth(lead, 22) + textWidth(names, 22, "sansSemi"), y, tail, 22);
  }
  // the table: chip and name, seats, seats vs the previous election
  const tx = 704, nx = tx + 36, seatX = 1070;
  s += text(seatX, 232, "Seats", 16, "sans", { fill: C.ink3, anchor: "end" }) +
    text(R, 232, "vs " + (spec.baseYear || ""), 16, "sans", { fill: C.ink3, anchor: "end" });
  listedRows(spec, ROWS.link).forEach((r, k) => {
    const y = 270 + k * 36;
    s += chip(r, tx, y - 21, 26, assets) + text(nx, y, fitText(r.name, seatX - 64 - nx, 23, "sansSemi", 17).text, 23, "sansSemi") +
      text(seatX, y, String(r.seats), 26, "sansBold", { anchor: "end" }) +
      (r.others ? "" : text(R, y, r.seatsVs, 19, "sans", { fill: C.ink2, anchor: "end" }));
  });
  // the foot: the outcome and its chance; whose forecast; where to make one
  s += rect(X, 522, R - X, 1, C.rule);
  const rightW = 300;
  const words = wrapText(spec.words, R - X - rightW - 20, 17);
  const wy = words.length > 1 ? 548 : 556;
  s += words.map((l, k) => text(X, wy + k * 21, l, 17, "sans", { fill: C.ink2 })).join("");
  const cy = 600;
  const ch = fitText(spec.chance, R - X - rightW - 40 - textWidth(spec.badge, 17, "sansSemi") - 40, 30, "serifSemi", 24);
  s += text(X, cy, ch.text, ch.fs, "serifSemi");
  s += badge(spec.badge, X + textWidth(ch.text, ch.fs, "serifSemi") + 14, cy - 4, 17).svg;
  s += text(R, 550, "A reader's forecast, not the model's.", 15, "sans", { fill: C.ink3, anchor: "end" }) +
    text(R, 576, "Make yours at", 19, "sans", { fill: C.ink2, anchor: "end" }) +
    text(R, 601, SITE, 19, "monoSemi", { anchor: "end" });
  return s + "</svg>";
}

// ---------- the story card, 1080 x 1920 ----------

// The table's right edges, in card pixels; the last column ends at the margin.
const STORY_COLUMNS = { seats: 443, wards: 549, pr: 607, vote: 752, seatsVs: 886 };
// The outcome column's type, [words, chance, notes] in px, largest first: the
// first whose foot stays above STORY_TEXT_BOTTOM is used.
const STORY_TYPE = { large: [27, 42, 22], middle: [24, 36, 20], small: [22, 32, 18] };

export function storyCardSVG(spec, assets = {}, party) {
  const [W, H] = SIZES.story;
  const X = 60, R = W - 60;
  let s = svgOpen(W, H, assets) + band(spec, W, 16, party);
  s += brand(assets, X, 56, 130);
  const made = madeText(spec);
  if (made) {
    s += text(R, 92, made, 28, "sans", { fill: C.ink3, anchor: "end" });
    s += text(R, 130, cap(daysText(daysToVote(spec.made.at, spec.election), false)), 28, "sans", { fill: C.ink3, anchor: "end" });
  }
  const head = fitText(spec.title, R - X, 70, "serifSemi", 40);
  s += text(X, 276, head.text, head.fs, "serifSemi");
  s += text(X, 320, spec.election.city + " council, " + dateText(spec.election.date) + ". " + spec.council + " seats.", 30, "sans", { fill: C.ink2 });
  s += text(X, 358, "A reader's forecast, not the model's.", 26, "sans", { fill: C.ink3 });
  const g = council(spec, X, 384, { width: R - X, cell: 25, gap: 4, fs: 22 });
  s += g.svg;
  let y = 384 + g.h + 38;
  const key = (x, op) => rect(x, y - 17, 20, 20, C.ink2, ` rx="3"${op == null ? "" : ` fill-opacity="${op}"`}`);
  s += key(X) + text(X + 28, y, "ward seats", 24, "sans", { fill: C.ink3 });
  s += key(X + 172, PR_OPACITY) + text(X + 200, y, "PR seats", 24, "sans", { fill: C.ink3 });
  if (spec.coalition.length) {
    const a = "Governing first: ", b = listAnd(spec.coalitionNames), c = ", " + spec.coalitionSeats + " seats";
    let x = X + 330;
    s += text(x, y, a, 24, "sans", { fill: C.ink3 }); x += textWidth(a, 24);
    s += text(x, y, b, 24, "sansSemi"); x += textWidth(b, 24, "sansSemi");
    s += text(x, y, c, 24, "sans", { fill: C.ink3 });
  }
  // the table
  const K = STORY_COLUMNS;
  y += 50;
  const colHead = (x, a, b = "") => {
    s += b ? text(x, y, a, 22, "sans", { fill: C.ink3, anchor: "end" }) + text(x, y + 26, b, 22, "sans", { fill: C.ink3, anchor: "end" })
      : text(x, y + 26, a, 22, "sans", { fill: C.ink3, anchor: "end" });
  };
  colHead(K.seats, "Seats"); colHead(K.wards, "Wards"); colHead(K.pr, "PR"); colHead(K.vote, "Vote");
  colHead(K.seatsVs, "Seats", "vs " + spec.baseYear); colHead(R, "Vote", "vs " + spec.baseYear);
  y += 40;
  listedRows(spec, ROWS.story).forEach(r => {
    s += rect(X, y, R - X, 1, C.rule);
    const by = y + 36;
    s += chip(r, X, by - 28, 36, assets) + text(X + 50, by, fitText(r.name, 300, 29, "sansSemi", 22).text, 29, "sansSemi") +
      text(K.seats, by, String(r.seats), 34, "sansBold", { anchor: "end" }) +
      text(K.wards, by, String(r.ward), 29, "sans", { anchor: "end" }) + text(K.pr, by, String(r.pr), 29, "sans", { anchor: "end" }) +
      text(K.vote, by, r.vote.toFixed(1) + "%", 29, "sans", { anchor: "end" }) +
      (r.others ? "" : text(K.seatsVs, by, r.seatsVs, 26, "sans", { fill: C.ink2, anchor: "end" }) + text(R, by, r.voteVs, 26, "sans", { fill: C.ink2, anchor: "end" }));
    y += 48;
  });
  // the map, and beside it the outcome, its chance and badge, and the notes;
  // in smaller type when the foot would otherwise pass STORY_TEXT_BOTTOM
  y += 30;
  const m = assets.geom ? wardMap(spec, assets.geom, party, X, y, 340) : { svg: "", h: 0 };
  s += m.svg;
  const ox = X + 380, ow = R - ox;
  // a seal shows when a forecast was made, not that it was its maker's only
  // one, so no card promises a ranking (review of the share build, 2026-10-03)
  const foot = wrapText("Bring this link back after the count to compare it with the result.", R - X, 27);
  const column = ([fw, fc, fn]) => {
    let out = "", oy = y + fw;
    for (const l of wrapText(spec.words, ow, fw)) { out += text(ox, oy, l, fw, "sans", { fill: C.ink2 }); oy += fw * 1.37; }
    oy += fc * 0.45;
    for (const l of wrapText(spec.chance, ow, fc, "serifSemi")) { out += text(ox, oy, l, fc, "serifSemi"); oy += fc * 1.15; }
    out += badge(spec.badge, ox, oy + 16, 26, 2).svg;
    oy += 64;
    for (const l of wrapText(spec.excess.join(" "), ow, fn)) { out += text(ox, oy, l, fn, "sans", { fill: C.ink3 }); oy += fn * 1.4; }
    return { out, bottom: Math.max(y + m.h, oy - fn) };
  };
  let col;
  for (const z of Object.values(STORY_TYPE)) {
    col = column(z);
    if (col.bottom + 60 + foot.length * 38 <= STORY_TEXT_BOTTOM) break;
  }
  s += col.out;
  const top = col.bottom + 60;
  s += rect(X, top - 40, R - X, 1, C.rule);
  foot.forEach((l, k) => { s += text(X, top + k * 38, l, 27, "sans", { fill: C.ink2 }); });
  const my = top + foot.length * 38, lead = "Make yours at ";
  s += text(X, my, lead, 27, "sans", { fill: C.ink2 }) + text(X + textWidth(lead, 27), my, SITE, 27, "monoSemi");
  return s + "</svg>";
}

// ---------- the return card, 1200 x 630: two forecasts ----------

// The headline's sizes, largest first: the first at which both names fit.
const DUEL_TITLE = { large: 48, middle: 44, small: 40, least: 36 };

export function duelCardSVG(a, b, assets = {}, party) {
  const [W, H] = SIZES.duel;
  const X = 48, R = W - 48;
  let s = svgOpen(W, H, assets);
  const bh = 104, bw = brandWidth(assets, bh);
  s += brand(assets, R + 4 - bw, 26, bh);
  const and = " and ";
  const maxW = R - bw - 24 - X;
  const fs = Object.values(DUEL_TITLE).find(f => textWidth(a.name + and + b.name, f, "serifSemi") <= maxW) || DUEL_TITLE.least;
  const na = fitText(a.name, (maxW - textWidth(and, fs, "serifSemi")) / 2, fs, "serifSemi", fs).text;
  const nb = fitText(b.name, maxW - textWidth(na + and, fs, "serifSemi"), fs, "serifSemi", fs).text;
  // three texts, each placed by measure: SVG drops a text's leading space
  s += text(X, 106, na, fs, "serifSemi") + text(X + textWidth(na + " ", fs, "serifSemi"), 106, and.trim(), fs, "serifSemi", { fill: C.ink3 }) +
    text(X + textWidth(na + and, fs, "serifSemi"), 106, nb, fs, "serifSemi");
  s += text(X, 142, "Two forecasts of the " + a.election.city + " council, " + a.council + " seats.", 21, "sans", { fill: C.ink2 });
  // the date is the first forecast's own: the second's link carries no seal
  const made = madeText(a);
  if (made) {
    const line = a.name + (/s$/i.test(a.name) ? "'" : "'s") + " forecast " + made.charAt(0).toLowerCase() + made.slice(1) + ", " +
      daysText(daysToVote(a.made.at, a.election)) + ".";
    const fit = fitText(line, R - X, 21, "sans", 16);
    s += text(X, 169, fit.text, fit.fs, "sans", { fill: C.ink2 });
  }
  const pair = (F, y) => {
    const who = F.name + " ";
    const rest = "We give it " + aChance(F.outcome.text) + ". " + F.badge + ".";
    return text(X, y, who, 20, "sansSemi") + text(X + textWidth(who, 20, "sansSemi"), y, fitText(rest, 470 - textWidth(who, 20, "sansSemi"), 20, "sans", 15).text, 20, "sans", { fill: C.ink2 }) +
      council(F, X, y + 10, { width: 350, cell: 11, gap: 2, label: false }).svg;
  };
  s += pair(a, 216) + pair(b, 386);
  // the table: each party in either top seven, in the first forecast's seat order
  const seatsA = Object.fromEntries(a.rows.map(r => [r.code, r.seats]));
  const seatsB = Object.fromEntries(b.rows.map(r => [r.code, r.seats]));
  const codes = [...new Set([...cutAt(a.rows.map(r => r.code), seatsA, ROWS.duel), ...cutAt(b.rows.map(r => r.code), seatsB, ROWS.duel)])]
    .sort((x, y) => (seatsA[y] || 0) - (seatsA[x] || 0) || (seatsB[y] || 0) - (seatsB[x] || 0) || party(x).name.localeCompare(party(y).name))
    .slice(0, ROWS.duel);
  const tx = 558, ca = 846, cb = 1025;
  s += text(tx, 214, "Seats", 17, "sansSemi", { fill: C.ink2 }) +
    text(ca, 214, fitText(a.name, 150, 17, "sansSemi", 13).text, 17, "sansSemi", { fill: C.ink2, anchor: "end" }) +
    text(cb, 214, fitText(b.name, 150, 17, "sansSemi", 13).text, 17, "sansSemi", { fill: C.ink2, anchor: "end" }) +
    text(R, 214, "Difference", 17, "sansSemi", { fill: C.ink2, anchor: "end" });
  codes.forEach((c, k) => {
    const y = 252 + k * 39, p = party(c), r = { code: c, colour: p.colour, logo: !!p.logo };
    const va = seatsA[c] || 0, vb = seatsB[c] || 0;
    s += chip(r, tx, y - 20, 24, assets) + text(tx + 34, y, fitText(p.name, ca - 70 - tx - 34, 23, "sansSemi", 17).text, 23, "sansSemi") +
      text(ca, y, String(va), 25, "sansBold", { anchor: "end" }) + text(cb, y, String(vb), 25, "sansBold", { anchor: "end" }) +
      text(R, y, signed(vb - va), 19, "sans", { fill: C.ink3, anchor: "end" });
  });
  s += rect(X, 570, R - X, 1, C.rule);
  s += text(X, 600, "Readers' forecasts, not the model's. Compare both with the result after the count.", 19, "sans", { fill: C.ink2 });
  s += text(R, 600, SITE, 19, "monoSemi", { anchor: "end" });
  return s + "</svg>";
}

// ---------- the text alternative ----------

export function cardAlt(spec) {
  const rows = listedRows(spec, ROWS.link).map(r => r.name + " " + r.seats).join(", ");
  return [spec.title, spec.election.city + " council, " + spec.council + " seats", "Seats: " + rows,
    spec.coalition.length ? "Governing: " + listAnd(spec.coalitionNames) + ", " + spec.coalitionSeats + " seats" : "",
    spec.words, spec.chance, spec.badge, "A reader's forecast, not the model's"]
    .filter(Boolean).map(s => s.replace(/\.$/, "")).join(". ") + ".";
}
export function duelAlt(a, b) {
  return [a.name + " and " + b.name + ": two forecasts of the " + a.election.city + " council",
    a.name + ": " + a.words + " " + a.chance + " " + a.badge,
    b.name + ": " + b.words + " " + b.chance + " " + b.badge]
    .map(s => s.replace(/\.$/, "")).join(". ") + ".";
}

// The brand logo as the cards take it, from site/logo.svg's text.
export function brandOf(svgText) {
  const vb = /viewBox="([^"]+)"/.exec(svgText);
  const body = svgText.replace(/<!--[\s\S]*?-->/g, "").replace(/^[\s\S]*?<svg[^>]*>/, "").replace(/<\/svg>\s*$/, "")
    .replace(/currentColor/g, C.ink);
  return vb ? { viewBox: vb[1], body } : null;
}
