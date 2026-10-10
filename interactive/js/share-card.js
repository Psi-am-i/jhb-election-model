// The share cards of /your-forecast/, both sections, in ONE design (owner,
// 2026-10-06: "one design"). A reader's forecast (section 2, "Break the
// model", and section 1 once its settings are moved, which shares section 1's
// hand-off as a reader's forecast): the link preview (1200 x 630), the story
// card (1080 x 1920) and the return card that sets two forecasts side by side
// (1200 x 630). The model's own forecast (section 1 untouched): modelCardSVG,
// at the same two sizes, in black and white (owner, 2026-10-06: "In our model
// sharing sheet we should stick with black and white"). Every card but the
// return card carries the council graphic, the party table and the ward map
// (owner, 2026-10-06: "They are all cool."). ONE MODULE for the page's
// download (share-sheet.js, drawn to a canvas by card-text.js's svgToPNG) and
// the edge's link preview (src/worker.js, rasterised by resvg in
// src/og-render.js). The design is audits/2026-10-03-share-design/DESIGN.md
// §2; its decisions DECISIONS.md.
//
// PURE: no DOM, no fetch, no figure of its own. The caller hands it the seats
// the seat law gave the reader's picks, the chance the published forecast
// gives the reader's outcome and the badge of the forecast's boldest call
// (reweight.outcome_chance, in Python), the owner's badge as a stamp,
// the reader's vote shares, the previous election's figures (forecast.json
// `baseline`), each party's name, article, colour and logo flag, and every
// image as a data: URI. It names no party and holds no colour of one (DESIGN
// §2 "Neutrality"): rows go in the reader's seat order, ties by name; on a
// reader's card the largest party's colour, whoever it is, fills the band
// behind the headline, the bar over the council graphic and that party's row,
// and a tie for the most seats splits each band equally and colours every
// tied row. A party whose colour has no hue (markColour) is marked in the
// card's ink instead, so the winner's band always reads as a highlight.
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
// The least a card's ward map may be drawn, as a share of the card's width
// (owner, 2026-10-06: "in tall version map should be bigger too"). Every
// layout below is held to these by the tests.
export const LINK_MAP_MIN_SHARE = 0.3;
export const STORY_MAP_MIN_SHARE = 0.55;
// How near STORY_TEXT_BOTTOM a story card's lowest words must reach, in px:
// the space between the blocks is spread evenly until the foot sits there.
export const STORY_FILL_SLACK = 24;
export const C = { paper: "#141715", paper2: "#1c201d", rule: "#333833", ink: "#eceee9", ink2: "#b6bcb6", ink3: "#868d86", chip: "#ffffff" };
const MONTHS = "January February March April May June July August September October November December".split(" ");
const DAY_MS = 864e5;

// ---------- words ----------

// "Thandi's Election Forecast" (owner, 2026-10-03: Title Case). A name the
// reader already typed as a possessive ("Simon's", "Simon’s", "the Joneses'")
// takes no second one (owner, 2026-10-07: "Simon's' Election Forecast").
export function cardTitle(name) {
  if (!name) return "My Election Forecast";
  if (/['’](s)?$/i.test(name)) return name + " Election Forecast";
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
// A ward on the reader's map: "We give your call in this ward an 18% chance."
export function wardChanceSentence(text) {
  return "We give your call in this ward " + aChance(text) + ".";
}

// The forecast's boldest call (reweight.boldest_call, in Python), named as
// the badge beside it judges it: "Boldest call: the PA at 38 seats." `lead`
// replaces "Boldest call" (the arrival view names whose). A forecast at the
// model's middle has no call. "" while the outcome is still being worked out.
export function boldestLine(boldest, party, lead = "Boldest call") {
  if (!boldest) return "";
  if (!boldest.party) return "Every party at the model's middle forecast.";
  const p = party(boldest.party);
  return lead + ": " + (p.article || "") + p.name + " at " + boldest.seats + (boldest.seats === 1 ? " seat." : " seats.");
}

// The owner's badge for a badge's words (reweight.BOLDNESS): the file
// src/stamps/reader-<words>.svg, which the build serves at /stamps/.
export const STAMP_DIR = "stamps";
export function badgeFile(words) {
  return "reader-" + words.toLowerCase().replace(/ /g, "-") + ".svg";
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
// outcome, words, chance, badge, boldest, boldestLine, excess: [sentences],
// calls, made }.
//   answer   the seat law's { seats, ward, pr, council_total, majority, excessive }
//   outcome  { largest, majority_alone, coalition, text, badge, boldest } (Python)
//   vote     { code: percent of the list ballot } (the column a prediction is scored on)
//   baseline forecast.json `baseline` ({ year, seats, wards, list_vote, ward_vote }), or null;
//            "vs <year>" compares the list vote with list_vote, list with list
//   made     { at: ms, sealed: bool } or null: when the card says it was made
export function forecastSpec({ name, answer, outcome, vote, calls, party, baseline, election, made = null }) {
  const { seats, ward = {}, pr = {}, council_total: council, majority, excessive = {} } = answer;
  const base = baseline || { seats: {}, list_vote: {} };
  const order = seatOrder(seats, party);
  const rows = order.map(c => ({
    code: c, name: party(c).name, colour: party(c).colour, logo: !!party(c).logo,
    seats: seats[c], seatPct: seatShare(seats[c], council), ward: ward[c] || 0, pr: pr[c] || 0, vote: vote[c] || 0,
    seatsVs: c in base.list_vote ? signed(seats[c] - (base.seats[c] || 0)) : "new",
    voteVs: c in base.list_vote ? signed((vote[c] || 0) - base.list_vote[c], 1) : "new",
  }));
  const coalition = order.filter(c => outcome.coalition.includes(c));
  const the = c => (party(c).article || "") + party(c).name;
  return {
    name, title: cardTitle(name), council, majority, election, rows, calls, made,
    coalition, coalitionNames: coalition.map(c => party(c).name),
    coalitionSeats: coalition.reduce((a, c) => a + seats[c], 0),
    outcome, words: outcomeWords(outcome, party), chance: chanceSentence(outcome.text), badge: outcome.badge,
    boldest: outcome.boldest || null, boldestLine: boldestLine(outcome.boldest, party),
    // the most seats: one party, or every party tied for them (the band splits)
    top: order.filter(c => seats[c] === seats[order[0]]),
    excess: Object.entries(excessive).filter(([, v]) => v > 0).map(([c, v]) =>
      cap(the(c)) + " wins " + v + (v === 1 ? " more ward" : " more wards") + " than its vote entitles it to seats. It keeps them, and gets no PR seats."),
    baseYear: base.year || null,
  };
}

// A party's seats as a percentage of the council: ONE DEFINITION for every
// row and for Others, so the column agrees with the seats beside it.
export function seatShare(n, council) {
  return n / council * 100;
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
    seats: sum("seats"), seatPct: seatShare(sum("seats"), spec.council), ward: sum("ward"), pr: sum("pr"), vote: sum("vote"),
    seatsVs: "", voteVs: "" }];
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

export const esc = s => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const n1 = v => Number(v.toFixed(1));
export function text(x, y, s, fs, face = "sans", { fill = C.ink, anchor = "", opacity = null, clip = "" } = {}) {
  const f = FACES[face];
  return `<text x="${n1(x)}" y="${n1(y)}" font-family="${f.family}" font-weight="${f.weight}" font-size="${n1(fs)}"` +
    `${anchor ? ` text-anchor="${anchor}"` : ""}${opacity == null ? "" : ` fill-opacity="${opacity}"`} fill="${fill}"` +
    `${clip ? ` clip-path="url(#${clip})"` : ""}>${esc(s)}</text>`;
}
export const rect = (x, y, w, h, fill, extra = "") => `<rect x="${n1(x)}" y="${n1(y)}" width="${n1(w)}" height="${n1(h)}" fill="${fill}"${extra}/>`;

// ---------- pieces ----------

// The ink that reads on a fill: the card's light ink or its dark paper,
// whichever has the better worst-case contrast (WCAG relative luminance)
// across every fill it sits on.
const luminance = hex => {
  const [r, g, b] = hex.replace("#", "").match(/../g).map(h => parseInt(h, 16) / 255)
    .map(c => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
};
const contrast = (a, b) => {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
};
const worstContrast = (ink, fills) => Math.min(...fills.map(f => contrast(ink, f)));
export function inkOn(fills) {
  return worstContrast(C.ink, fills) >= worstContrast(C.paper, fills) ? C.ink : C.paper;
}
// The least contrast (WCAG, large text) the words on a band may have. Below
// it, as on a band split between two mid-tone colours, the words sit on
// plates of the card's paper inside the band.
export const BAND_MIN_CONTRAST = 3;
// { ink, ratio, plated } for words on a band of `fills`.
export function bandInk(fills) {
  const ink = inkOn(fills), ratio = worstContrast(ink, fills);
  return ratio >= BAND_MIN_CONTRAST ? { ink, ratio, plated: false } : { ink: C.ink, ratio: worstContrast(C.ink, [C.paper]), plated: true };
}

// A colour with no hue of its own, as the roster gives a party it has no
// colour for, marks nothing: a winner's band in it read as grey, like Others
// (owner, 2026-10-06, of a party the roster gives no colour). Such a party is
// marked in the card's ink instead. Chroma is the spread of the colour's
// channels, 0 to 1; below NEUTRAL_CHROMA the colour counts as no hue. A
// colour that is not "#rrggbb" is no colour the card can read: the ink too.
export const NEUTRAL_CHROMA = 0.12;
const HEX6 = /^#[0-9a-f]{6}$/i;
const chroma = hex => {
  const v = hex.replace("#", "").match(/../g).map(h => parseInt(h, 16) / 255);
  return Math.max(...v) - Math.min(...v);
};
export function markColour(hex) {
  return typeof hex !== "string" || !HEX6.test(hex) || chroma(hex) < NEUTRAL_CHROMA ? C.ink : hex;
}

// The colours of the most seats: one party's, or each tied party's, as
// markColour marks them.
const topColours = spec => (spec.top.length ? spec.top : [null])
  .map(c => markColour(c ? spec.rows.find(r => r.code === c).colour : OTHERS_COLOUR));

// A band in the largest party's colour, split equally for a tie: behind a
// headline, or over a council graphic. Returns { svg, ink, plated } (ink:
// what reads on it; plated: each text on it goes on a plate, bandPlate). A
// band given several forecasts splits into one part per forecast. `fills`,
// if given, is the band's colours instead (the model's card: no party's).
function colourBand(specs, x, y, w, h, fills = null) {
  const parts = fills ? [{ fills }] : [].concat(specs);
  const used = [];
  let svg = "";
  parts.forEach((spec, k) => {
    const cs = spec.fills || topColours(spec), pw = w / parts.length, cw = pw / cs.length;
    cs.forEach((c, j) => { svg += rect(x + k * pw + j * cw, y, cw + 0.5, h, c); used.push(c); });
  });
  return { svg, ...bandInk(used) };
}

// The paper plate under what sits on a plated band: the box (x, y, w, h) and
// a margin, or "" on a band that needs none. textPlate: the box of a text
// `w` wide at `fs` px on the baseline `y`.
function bandPlate(band, x, y, w, h) {
  if (!band.plated) return "";
  const p = Math.round(Math.min(10, h * 0.2));
  return rect(x - p, y - p, w + 2 * p, h + 2 * p, C.paper, ` rx="${n1(p)}"`);
}
const textPlate = (band, x, y, w, fs) => bandPlate(band, x, y - fs * 0.92, w, fs * 1.2);

// A row of the table in its party's colour, for the largest party (or each
// tied for it). Returns { svg, ink }, or no band for any other row.
function rowBand(lead, colour, x, y, w, h) {
  if (!lead) return { svg: "", ink: null };
  const fill = markColour(colour);
  return { svg: rect(x, y, w, h, fill, ` rx="${n1(h / 8)}"`), ink: inkOn([fill]) };
}

// A party's name in its column: fitted, cut with an ellipsis if it still
// does not fit, and clipped to the column, so that no face a browser
// substitutes can run it into the figures beside it (owner, 2026-10-06:
// a long name ran into the "% of seats" beside it). `id` is unique in the card.
function nameCell(id, s, x, y, w, fs, face, fill) {
  const t = fitText(s, w, fs, face, fs * 0.75);
  return `<clipPath id="${id}">${rect(x, y - fs * 1.1, w, fs * 1.5, "#000")}</clipPath>` +
    text(x, y, t.text, t.fs, face, { fill, clip: id });
}

// The site's logo (site/logo.svg, the tower J and lettering), `h` tall, in
// `ink` (the card's ink, or the ink that reads on the band it sits on).
export function brand(assets, x, y, h, ink = C.ink) {
  const b = assets.brand;
  if (!b) return "";
  const [, , vw, vh] = b.viewBox.split(/\s+/).map(Number);
  const body = ink === C.ink ? b.body : b.body.split(C.ink).join(ink);
  return `<svg x="${n1(x)}" y="${n1(y)}" width="${n1(h * vw / vh)}" height="${n1(h)}" viewBox="${b.viewBox}" fill="${ink}">${body}</svg>`;
}
export function brandWidth(assets, h) {
  if (!assets.brand) return 0;
  const [, , vw, vh] = assets.brand.viewBox.split(/\s+/).map(Number);
  return h * vw / vh;
}

// An owner's stamp (src/stamps/*.svg: the reader badges, the verdict badges,
// the prediction seal), parsed as brandOf parses the logo: { viewBox, body }.
// The files define their glyphs, masks, clips and filters by ids that repeat
// from file to file (glyph-0-0, filter-remove-color, ...), so a body is never
// placed as it is: stampSVG prefixes them.
export const stampOf = svgText => brandOf(svgText);
// `body` with every id it defines renamed `<prefix>-<id>`, and every
// reference to one (href="#…", xlink:href="#…", url(#…)) renamed with it. A
// reference to an id the body does not define is left alone.
export function prefixIds(body, prefix) {
  const ids = new Set([...body.matchAll(/\bid="([^"]+)"/g)].map(m => m[1]));
  return body.replace(/(\bid=")([^"]+)(")|(href=")#([^"]+)(")|url\(#([^)]+)\)/g, (m, a, id, z, h, ref, hz, u) => {
    if (id !== undefined) return ids.has(id) ? a + prefix + "-" + id + z : m;
    if (ref !== undefined) return ids.has(ref) ? h + "#" + prefix + "-" + ref + hz : m;
    return ids.has(u) ? "url(#" + prefix + "-" + u + ")" : m;
  });
}
// THE ONE WAY A STAMP GOES ON A CARD: `st` (stampOf) `h` tall at (x, y), its
// ids prefixed by `prefix`, which must be unique in the card.
export function stampSVG(st, prefix, x, y, h) {
  const [, , vw, vh] = st.viewBox.split(/\s+/).map(Number);
  return `<svg xmlns:xlink="http://www.w3.org/1999/xlink" x="${n1(x)}" y="${n1(y)}" width="${n1(h * vw / vh)}" height="${n1(h)}" viewBox="${st.viewBox}">${prefixIds(st.body, prefix)}</svg>`;
}
// The reader's badge `h` tall at (x, y): the owner's stamp for the words when
// the card was handed it (assets.badges[words]), else the words in a pill.
function readerBadge(words, assets, prefix, x, y, h) {
  const st = (assets.badges || {})[words];
  if (st) return stampSVG(st, prefix, x, y, h);
  return badge(words, x, y + h / 2 + 6, 17).svg;
}

// A party's chip: its logo on white where it has one, else its colour,
// outlined in `outline` when it sits on a band of that colour.
export function chip(r, x, y, s, assets, outline = null) {
  const src = r.logo && r.code ? (assets.logos || {})[r.code] : null;
  const rx = Math.max(2, s / 6.5);
  if (!src) return rect(x, y, s, s, r.colour, ` rx="${n1(rx)}"${outline ? ` stroke="${outline}" stroke-width="2"` : ""}`);
  return rect(x, y, s, s, C.chip, ` rx="${n1(rx)}"`) +
    `<image x="${n1(x + 1)}" y="${n1(y + 1)}" width="${n1(s - 2)}" height="${n1(s - 2)}" href="${src}" preserveAspectRatio="xMidYMid meet"/>`;
}

// The council at (x, y): a bar carrying the majority label, the squares and
// the majority line. The bar is in the largest party's colour, or in
// `barFills` (the model's card: no party's). It stands clear of the squares
// by BAR_CLEAR so it never runs into a square of its own colour. Returns
// { svg, w, h } (h includes the bar); councilSize gives the same w and h
// without drawing, for a layout that sizes its blocks first.
const BAR_CLEAR = 6;
function councilGeom(spec, { width, cell: want, gap, fs = 15, label = true }) {
  const L = councilLayout(spec);
  const step = Math.min(want + gap, Math.floor((width + gap) / L.cols * 10) / 10);
  const barH = fs + 8;
  const top = label ? barH + BAR_CLEAR : 0;
  return { L, step, cell: step - gap, gridW: L.cols * step - gap, barH, top, h: top + L.rows * step - gap };
}
export function councilSize(spec, opts) {
  const g = councilGeom(spec, opts);
  return { w: g.gridW, h: g.h };
}
function council(spec, x, y, opts) {
  const { gap, fs = 15, label = true, barFills = null } = opts;
  const { L, step, cell, gridW, barH, top, h } = councilGeom(spec, opts);
  const ox = x, oy = y + top;
  let s = "";
  if (label) {
    const bar = colourBand(spec, x, y, gridW, barH, barFills);
    const lx = ox + (L.step.col + 1) * step - gap / 2 + 6;
    const words = spec.majority + " for a majority";
    const anchor = lx + textWidth(words, fs) > x + gridW ? "end" : "";
    const ww = textWidth(words, fs), wx = anchor ? ox + L.step.col * step - 6 : lx;
    s += bar.svg + textPlate(bar, anchor ? wx - ww : wx, y + fs + 1, ww, fs) + text(wx, y + fs + 1, words, fs, "sans", { fill: bar.ink, anchor });
  }
  s += L.cells.map(c => rect(ox + c.col * step, oy + c.row * step, cell, cell, c.colour,
    ` rx="${n1(Math.max(1, cell / 6))}"${c.pr ? ` fill-opacity="${PR_OPACITY}"` : ""}`)).join("");
  s += `<path transform="translate(${n1(ox)} ${n1(oy)})" d="${stepPath(L, cell, gap)}" fill="none" stroke="${C.ink}" stroke-width="${Math.max(2, gap)}"/>`;
  return { svg: s, w: gridW, h };
}

// The party table of a reader's forecast, shared by the link and story
// cards. Columns after the party, left to right: % of seats, % of votes, a
// gap, seats, change since the previous election. `g`: { x, right, cols:
// [four right edges], y (the headers' first baseline), n (rows before
// Others), pitch, chip, rules, fs: { head, name, pct, seats, vs }, id (the
// prefix of its clip ids) }. Returns { svg, bottom }. tableHeight gives the
// height from the headers' first baseline to the bottom without drawing.
const TABLE_HEAD = baseYear => [["% of", "seats"], ["% of", "votes"], ["", "Seats"], ["Change", "vs " + (baseYear || "")]];
const tableTop = g => Math.round(g.y + g.fs.head * 1.2 + Math.round(g.chip / 4));
function tableHeight(spec, g) {
  return tableTop({ ...g, y: 0 }) + listedRows(spec, g.n).length * g.pitch;
}
function partyTable(spec, assets, g) {
  const { x, right: R, cols, pitch, chip: cs, fs } = g;
  let s = "";
  TABLE_HEAD(spec.baseYear).forEach(([a, b], k) => {
    if (a) s += text(cols[k], g.y, a, fs.head, "sans", { fill: C.ink3, anchor: "end" });
    s += text(cols[k], g.y + fs.head * 1.2, b, fs.head, "sans", { fill: C.ink3, anchor: "end" });
  });
  const pad = Math.round(cs / 4);
  let top = tableTop(g);
  // the name's column ends a full pad short of the widest "% of seats"
  const nx = x + cs + Math.round(cs / 3), nameW = cols[0] - textWidth("00.0%", fs.pct) - 2 * pad - nx;
  listedRows(spec, g.n).forEach((r, k) => {
    const band = rowBand(spec.top.includes(r.code), r.colour, x - pad, top + 2, R - x + 2 * pad, pitch - 4);
    if (g.rules && !band.svg) s += rect(x, top, R - x, 1, C.rule);
    const ink = band.ink || C.ink, ink2 = band.ink || C.ink2;
    const by = top + pitch / 2 + fs.name * 0.36;
    s += band.svg + chip(r, x, top + (pitch - cs) / 2, cs, assets, band.ink) +
      nameCell((g.id || "n") + k, r.name, nx, by, nameW, fs.name, "sansSemi", ink) +
      text(cols[0], by, r.seatPct.toFixed(1) + "%", fs.pct, "sans", { fill: ink, anchor: "end" }) +
      text(cols[1], by, r.vote.toFixed(1) + "%", fs.pct, "sans", { fill: ink, anchor: "end" }) +
      text(cols[2], by, String(r.seats), fs.seats, "sansBold", { fill: ink, anchor: "end" }) +
      (r.others ? "" : text(cols[3], by, r.seatsVs, fs.vs, "sans", { fill: ink2, anchor: "end" }));
    top += pitch;
  });
  return { svg: s, bottom: top };
}

// The model's table: each party's middle seat count as a bar in the card's
// ink, all on one scale, and the figure. A row is { code, name, colour,
// logo, value, n } (n: the bar's length, null when withheld). The name's
// column takes what the longest name needs, up to NAME_SHARE of the room
// beside the chip. `g`: { x, right, y (the first row's top), pitch, chip,
// fs, id }. Returns { svg, bottom }.
const NAME_SHARE = 0.55;
function middleTable(rows, assets, g) {
  const { x, right: R, pitch, chip: cs, fs } = g;
  const most = Math.max(1, ...rows.map(r => r.n ?? 0));
  const nx = x + cs + Math.round(cs / 3);
  const figW = textWidth("000.0", fs * 1.1, "sansBold") + Math.round(cs / 3);
  const longest = Math.max(...rows.map(r => textWidth(r.name, fs, "sansSemi")));
  const nameW = Math.min(longest + 8, (R - nx - figW) * NAME_SHARE);
  const bx = nx + nameW + 8, bw = R - figW - bx;
  let s = "", top = g.y;
  rows.forEach((r, k) => {
    const by = top + pitch / 2 + fs * 0.36;
    s += chip(r, x, top + (pitch - cs) / 2, cs, assets) +
      nameCell(g.id + k, r.name, nx, by, nameW, fs, "sansSemi", C.ink) +
      text(R, by, r.value, fs * 1.1, "sansBold", { anchor: "end" }) +
      (r.n == null ? "" : rect(bx, top + pitch * 0.3, Math.max(3, bw * r.n / most), pitch * 0.4, C.ink2, ` rx="2"`));
    top += pitch;
  });
  return { svg: s, bottom: top };
}

// The ward map, `w` wide. `map` is { W, H, wards: [{ path, fill, bands? }],
// step, rotate }: each ward in its fill, and where it has bands (a contested
// ward on the model's card) the stripe tile's lines ({ x, w, colour }) over
// it. `north` puts the north mark at its top right, as the page's map has it.
// mapOf turns a reader's forecast into such a map: each ward in the colour of
// the party called for it.
function wardMap(map, x, y, w, { prefix = "wm", north = false } = {}) {
  const s = w / map.W, h = map.H * s;
  const defs = [], fills = [], hatches = [];
  map.wards.forEach((wd, i) => {
    if (!wd.path) return;
    fills.push(`<path d="${wd.path}" fill="${wd.fill}" stroke="${C.paper}" stroke-width="${n1(0.8 / s)}" stroke-linejoin="round"/>`);
    if (wd.bands) {
      const id = prefix + i;
      defs.push(`<pattern id="${id}" width="${map.step}" height="${map.step}" patternTransform="rotate(${map.rotate})" patternUnits="userSpaceOnUse">` +
        wd.bands.map(b => `<line x1="${b.x.toFixed(2)}" y1="0" x2="${b.x.toFixed(2)}" y2="${map.step}" stroke="${b.colour}" stroke-width="${b.w.toFixed(2)}"/>`).join("") + "</pattern>");
      hatches.push(`<path d="${wd.path}" fill="url(#${id})"/>`);
    }
  });
  const g = `<g transform="translate(${n1(x)} ${n1(y)}) scale(${s.toFixed(4)})">` +
    (defs.length ? `<defs>${defs.join("")}</defs>` : "") + fills.join("") + hatches.join("") + "</g>";
  return { svg: g + (north ? northMark(x + w, y, Math.max(14, Math.round(w / 34))) : ""), h };
}
export function mapOf(spec, geom, party) {
  return { W: geom.W, H: geom.H, wards: geom.wards.map((wd, i) => ({ path: wd.path, fill: party(spec.calls[i]).colour })) };
}
// "N" and an arrow pointing up and to the right, ending at (x, y): north on
// the page's map. The arrow is drawn, not typed: the cards' fonts carry no
// arrow glyph.
function northMark(x, y, fs) {
  const a = fs * 0.8;
  return text(x - a - fs * 0.3, y + fs, "N", fs, "sansSemi", { fill: C.ink2, anchor: "end" }) +
    `<polyline points="${n1(x - a)},${n1(y + a)} ${n1(x)},${n1(y)} ${n1(x - a * 0.55)},${n1(y)} ${n1(x)},${n1(y)} ${n1(x)},${n1(y + a * 0.55)}" fill="none" stroke="${C.ink2}" stroke-width="2"/>`;
}

// "Governing: ANC and DA, 137 seats." on the baseline `y` from `x`, within
// `maxW`: the type shrinks to three quarters of `fs`, and below that the
// names are cut with an ellipsis, so long roster names never run off the
// card. The names are in the card's ink, the words around them in `fill`.
function governing(spec, x, y, maxW, fs, lead, end, fill) {
  const tail = ", " + spec.coalitionSeats + " seats" + end;
  let names = listAnd(spec.coalitionNames);
  const width = f => textWidth(lead, f) + textWidth(names, f, "sansSemi") + textWidth(tail, f);
  let f = fs;
  while (f > fs * 0.75 && width(f) > maxW) f = Math.max(fs * 0.75, f - 1);
  if (width(f) > maxW) {
    const room = maxW - textWidth(lead, f) - textWidth(tail, f);
    names = fitText(names, room, f, "sansSemi", f).text;
  }
  const a = textWidth(lead, f), b = textWidth(names, f, "sansSemi");
  return text(x, y, lead, f, "sans", { fill }) + text(x + a, y, names, f, "sansSemi") + text(x + a + b, y, tail, f, "sans", { fill });
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

// The headline band's height and the headline's baseline.
export const LINK_BAND = 112;
export const LINK_HEAD_Y = 78;
// The party table's row pitch.
export const LINK_PITCH = 30;
// The left column (whose council, the map, the outcome) and the gap after it;
// the council graphic and the table take the rest (owner, 2026-10-06: the
// map on every card, and the table clear of the council graphic).
const LINK_LEFT = 500, LINK_GUTTER = 32;
// The reader's badge on the link preview, its height.
const LINK_STAMP = 108;

export function linkCardSVG(spec, assets = {}, party) {
  const [W, H] = SIZES.link;
  const X = 48, R = W - 48;
  let s = svgOpen(W, H, assets);
  // the headline on a band in the largest party's colour, the logo with it
  const top = colourBand(spec, 0, 0, W, LINK_BAND);
  s += top.svg;
  const bh = 88, bw = brandWidth(assets, bh);
  s += bandPlate(top, R + 4 - bw, 12, bw, bh) + brand(assets, R + 4 - bw, 12, bh, top.ink);
  const head = fitText(spec.title, Math.min(900, R - bw - 24 - X), 52, "serifSemi", 40);
  s += textPlate(top, X, LINK_HEAD_Y, textWidth(head.text, head.fs, "serifSemi"), head.fs) +
    text(X, LINK_HEAD_Y, head.text, head.fs, "serifSemi", { fill: top.ink });
  // the left column, top down: whose council and when ...
  const made = madeText(spec);
  const lines = [spec.election.city + " council, " + dateText(spec.election.date) + ", " + spec.council + " seats.",
    made ? made + ", " + daysText(daysToVote(spec.made.at, spec.election)) + "." : ""].filter(Boolean);
  let y = LINK_BAND + 30;
  for (const l of lines) {
    const f = fitText(l, LINK_LEFT, 18, "sans", 14);
    s += text(X, y, f.text, f.fs, "sans", { fill: C.ink2 });
    y += 23;
  }
  // ... and bottom up: whose forecast and where to make one, the chance and
  // its badge, the outcome; the map takes the height between
  s += text(X, H - 44, "A reader's forecast, not the model's.", 15, "sans", { fill: C.ink3 }) +
    text(X, H - 18, "Make yours at ", 18, "sans", { fill: C.ink2 }) + text(X + textWidth("Make yours at ", 18), H - 18, SITE, 18, "monoSemi");
  // ... the boldest call the badge judges, the chance (never cut: on one
  // line where it fits at 22 px or more, else wrapped), the outcome; the map
  // takes the height between, and the owner's badge stands beside the map
  const bold = fitText(spec.boldestLine, LINK_LEFT, 17, "sans", 14);
  s += text(X, H - 70, bold.text, bold.fs, "sans", { fill: C.ink2 });
  const one = fitText(spec.chance, LINK_LEFT, 28, "serifSemi", 22);
  let cy = H - 100, upper;
  if (one.text === spec.chance) {
    s += text(X, cy, one.text, one.fs, "serifSemi");
    upper = cy;
  } else {
    const lines = wrapText(spec.chance, LINK_LEFT, 22, "serifSemi");
    cy -= (lines.length - 1) * 26;
    s += lines.map((l, k) => text(X, cy + k * 26, l, 22, "serifSemi")).join("");
    upper = cy;
  }
  const words = wrapText(spec.words, LINK_LEFT, 17);
  const wy = upper - 40 - (words.length - 1) * 21;
  s += words.map((l, k) => text(X, wy + k * 21, l, 17, "sans", { fill: C.ink2 })).join("");
  const mt = y - 6, mb = wy - 17 - 14;
  s += readerBadge(spec.badge, assets, "lb", X + LINK_LEFT - LINK_STAMP, mb - LINK_STAMP, LINK_STAMP);
  if (assets.geom) {
    const mw = Math.min(LINK_LEFT - LINK_STAMP - 12, (mb - mt) * assets.geom.W / assets.geom.H);
    s += wardMap(mapOf(spec, assets.geom, party), X, mt, mw).svg;
  }
  // the right column: the council, who governs, then the table, clear of it
  const rx = X + LINK_LEFT + LINK_GUTTER;
  const g = council(spec, rx, LINK_BAND + 14, { width: R - rx, cell: 12, gap: 3, fs: 15 });
  s += g.svg;
  const gy = LINK_BAND + 14 + g.h + 30;
  if (spec.coalition.length) {
    s += governing(spec, rx, gy, R - rx, 20, "Governing: ", ".", C.ink);
  }
  s += partyTable(spec, assets, { x: rx, right: R, cols: [R - 276, R - 192, R - 84, R], y: gy + 32, n: ROWS.link,
    pitch: LINK_PITCH, chip: 24, rules: false, id: "ln", fs: { head: 15, name: 20, pct: 19, seats: 22, vs: 17 } }).svg;
  return s + "</svg>";
}

// ---------- the story card, 1080 x 1920 ----------

// The table's right edges, in card pixels; the change column ends at the
// margin. Named, not a list: the build's live-writer scan refuses a literal
// array of numbers in this module (stats.SCRIPT_FORBIDDEN "a data block").
const STORY_COLUMNS = { seatPct: 560, vote: 700, seats: 900 };
// The headline band's height and the headline's baseline.
export const STORY_BAND = 292;
export const STORY_HEAD_Y = 262;
// The outcome column's type, [words, chance, notes] in px, largest first.
// With the map, the column beside it is laid out at each size and width, and
// the widest map whose row fits above the foot is drawn.
const STORY_TYPE = { large: [27, 42, 22], middle: [24, 36, 20], small: [22, 32, 18] };
// The least gap between two blocks of a story card; what the blocks leave
// above STORY_TEXT_BOTTOM is spread evenly over the gaps (owner, 2026-10-06:
// "use the canvas").
const STORY_GAP = 22;
// The reader's badge on the story card, its height.
const STORY_STAMP = 132;
// Its top edge in the headline band, clear of the headline's baseline.
const STORY_STAMP_TOP = 28;
// The least width the reader's map is tried at, and the step between tries.
const STORY_MAP_LEAST = 300, STORY_MAP_STEP = 10;
// A reader's story card's map, as a share of the card's width, is held to
// READER_STORY_MAP_MIN_SHARE: its outcome column shares the map's row.
export const READER_STORY_MAP_MIN_SHARE = 0.45;

export function storyCardSVG(spec, assets = {}, party) {
  const [W, H] = SIZES.story;
  const X = 60, R = W - 60;
  let s = svgOpen(W, H, assets);
  // the logo, the date and the headline on a band in the largest party's colour
  const top = colourBand(spec, 0, 0, W, STORY_BAND);
  const bh = 130;
  s += top.svg + bandPlate(top, X, 44, brandWidth(assets, bh), bh) + brand(assets, X, 44, bh, top.ink);
  const head = fitText(spec.title, R - X, 70, "serifSemi", 40);
  const made = madeText(spec);
  // the headline is the band's first words, so a reader of the text meets it first
  const headSVG = textPlate(top, X, STORY_HEAD_Y, textWidth(head.text, head.fs, "serifSemi"), head.fs) +
    text(X, STORY_HEAD_Y, head.text, head.fs, "serifSemi", { fill: top.ink });
  s += headSVG;
  // the owner's badge in the band, at its right; the sealed date and the
  // days to the vote right-aligned beside it, clear of the logo
  s += readerBadge(spec.badge, assets, "sb", R - STORY_STAMP, STORY_STAMP_TOP, STORY_STAMP);
  if (made) {
    const right = R - STORY_STAMP - 24, room = right - (X + brandWidth(assets, bh) + 24);
    [made, cap(daysText(daysToVote(spec.made.at, spec.election), false))].forEach((l, k) => {
      const f = fitText(l, room, 28, "sans", 20);
      const w = textWidth(f.text, f.fs);
      s += textPlate(top, right - w, 82 + k * 38, w, f.fs) + text(right, 82 + k * 38, f.text, f.fs, "sans", { fill: top.ink, anchor: "end" });
    });
  }
  s += text(X, 326, spec.election.city + " council, " + dateText(spec.election.date) + ". " + spec.council + " seats.", 30, "sans", { fill: C.ink2 });
  s += text(X, 362, "A reader's forecast, not the model's.", 26, "sans", { fill: C.ink3 });
  // the blocks below, sized first: the council, its key, the table, the map
  // with the outcome beside it, and the foot
  const CO = { width: R - X, cell: 21, gap: 3, fs: 22 };
  const cs = councilSize(spec, CO);
  const TB = { x: X, right: R, cols: [STORY_COLUMNS.seatPct, STORY_COLUMNS.vote, STORY_COLUMNS.seats, R], n: ROWS.story,
    pitch: 48, chip: 40, rules: true, id: "sn", fs: { head: 22, name: 29, pct: 29, seats: 34, vs: 26 } };
  const tableH = tableHeight(spec, TB) + TB.fs.head;          // from the headers' top
  const KEY_H = 26;
  // a seal shows when a forecast was made, not that it was its maker's only
  // one, so no card promises a ranking (review of the share build, 2026-10-03)
  const foot = wrapText("Bring this link back after the count to compare it with the result.", R - X, 27);
  const footH = 40 + foot.length * 38;                        // from the rule to the last baseline
  const start = 388;
  const gaps = 5;                                             // before the council, the key, the table, the row, the foot
  const avail = STORY_TEXT_BOTTOM - start - cs.h - KEY_H - tableH - footH - gaps * STORY_GAP;
  // the map's row: the widest map whose row fits, the outcome column beside it
  const aspect = assets.geom ? assets.geom.H / assets.geom.W : 0;
  const column = ([fw, fc, fn], ow, y0, draw) => {
    let out = "", oy = y0 + fw;
    for (const l of wrapText(spec.words, ow, fw)) { if (draw) out += text(draw.x, oy, l, fw, "sans", { fill: C.ink2 }); oy += fw * 1.37; }
    oy += fc * 0.45;
    for (const l of wrapText(spec.chance, ow, fc, "serifSemi")) { if (draw) out += text(draw.x, oy, l, fc, "serifSemi"); oy += fc * 1.15; }
    // the boldest call the badge in the band judges
    oy += fw * 0.3;
    for (const l of wrapText(spec.boldestLine, ow, fw)) { if (draw) out += text(draw.x, oy, l, fw, "sans", { fill: C.ink2 }); oy += fw * 1.37; }
    oy += fn * 0.6;
    for (const l of wrapText(spec.excess.join(" "), ow, fn)) { if (draw) out += text(draw.x, oy, l, fn, "sans", { fill: C.ink3 }); oy += fn * 1.4; }
    return { out, h: oy - fn - y0 };
  };
  let pick = null;
  for (const z of Object.values(STORY_TYPE)) {
    for (let mw = aspect ? R - X - 300 : 0; mw >= (aspect ? STORY_MAP_LEAST : 0); mw -= STORY_MAP_STEP) {
      const ow = R - X - (mw ? mw + 40 : 0);
      const rowH = Math.max(mw * aspect, column(z, ow, 0, null).h);
      if (rowH <= avail) { if (!pick || mw > pick.mw) pick = { z, mw, ow, rowH }; break; }
      if (!aspect) break;
    }
  }
  if (!pick) {
    const z = STORY_TYPE.small, mw = aspect ? STORY_MAP_LEAST : 0, ow = R - X - (mw ? mw + 40 : 0);
    pick = { z, mw, ow, rowH: Math.max(mw * aspect, column(z, ow, 0, null).h) };
  }
  // what is left is spread evenly over the gaps
  const gap = STORY_GAP + Math.floor(Math.max(0, avail - pick.rowH) / gaps);
  let y = start + gap;
  s += council(spec, X, y, CO).svg;
  y += cs.h + gap;
  const ky = y + 18;
  const key = (x, op) => rect(x, ky - 17, 20, 20, C.ink2, ` rx="3"${op == null ? "" : ` fill-opacity="${op}"`}`);
  s += key(X) + text(X + 28, ky, "ward seats", 24, "sans", { fill: C.ink3 });
  s += key(X + 172, PR_OPACITY) + text(X + 200, ky, "PR seats", 24, "sans", { fill: C.ink3 });
  if (spec.coalition.length) {
    s += governing(spec, X + 330, ky, R - X - 330, 24, "Governing first: ", "", C.ink3);
  }
  y += KEY_H + gap;
  const t = partyTable(spec, assets, { ...TB, y: y + TB.fs.head });
  s += t.svg;
  y = t.bottom + gap;
  // the map, and beside it the outcome, its chance and badge, and the notes
  if (pick.mw) s += wardMap(mapOf(spec, assets.geom, party), X, y + (pick.rowH - pick.mw * aspect) / 2, pick.mw).svg;
  const ox = R - pick.ow;
  s += column(pick.z, pick.ow, y, { x: ox }).out;
  const rule = y + pick.rowH + gap;
  s += rect(X, rule, R - X, 1, C.rule);
  foot.forEach((l, k) => { s += text(X, rule + 40 + k * 38, l, 27, "sans", { fill: C.ink2 }); });
  const my = rule + 40 + foot.length * 38, lead = "Make yours at ";
  s += text(X, my, lead, 27, "sans", { fill: C.ink2 }) + text(X + textWidth(lead, 27), my, SITE, 27, "monoSemi");
  return s + "</svg>";
}

// ---------- the model's own forecast, both sizes ----------

// `card` (play-card.js playCardSpec): { title, lines: [{ text, tone }], map
// (as wardMap takes it, stripes included), mapNote, chamber (a council
// graphic's spec: { rows: [{ code, colour, ward, pr }], council, majority,
// coalition, top }, or null), chamberNote, rows (middleTable's), rowsNote,
// foot: [paragraph] }. Every string is drawn as text. Black and white (owner,
// 2026-10-06): the headline sits on the card's paper above a rule, the bars
// are in the card's ink, and no row is marked; a party shows only as its
// chip, its wards on the map and its seats in the council graphic.
const TONE = { strong: { face: "sansSemi", fill: C.ink }, plain: { face: "sans", fill: C.ink }, muted: { face: "sans", fill: C.ink2 } };
const MONO_BAR = [C.rule];

export function modelCardSVG(card, assets = {}, size = "link") {
  if (!card.map) throw new Error("the card needs the ward map");
  return size === "story" ? modelStory(card, assets) : modelLink(card, assets);
}

// The link preview: the headline and the lines across the top; then the map,
// the council graphic and the table side by side; the foot across the bottom.
const MODEL_LINK_CHAMBER = 280, MODEL_LINK_TABLE = 330, MODEL_LINK_GUTTER = 28;
function modelLink(card, assets) {
  const [W, H] = SIZES.link;
  const X = 48, R = W - 48;
  let s = svgOpen(W, H, assets);
  const head = fitText(card.title, Math.min(900, R - brandWidth(assets, 88) - 24 - X), 52, "serifSemi", 40);
  s += text(X, LINK_HEAD_Y, head.text, head.fs, "serifSemi");
  const bw = brandWidth(assets, 88);
  s += brand(assets, R + 4 - bw, 12, 88) + rect(X, LINK_BAND - 1, R - X, 1, C.rule);
  let y = LINK_BAND + 30;
  for (const l of card.lines) {
    const t = TONE[l.tone || "muted"];
    for (const w of wrapText(l.text, R - X, 18, t.face)) { s += text(X, y, w, 18, t.face, { fill: t.fill }); y += 23; }
  }
  const feet = card.foot.flatMap(f => wrapText(f, R - X, 14));
  const fy = H - 14 - (feet.length - 1) * 18;
  s += rect(X, fy - 22, R - X, 1, C.rule) + feet.map((l, k) => text(X, fy + k * 18, l, 14, "sans", { fill: C.ink3 })).join("");
  const BT = y - 4, BB = fy - 36;
  const cw = card.chamber ? MODEL_LINK_CHAMBER : 0;
  const mapCol = R - X - cw - MODEL_LINK_TABLE - (cw ? 2 : 1) * MODEL_LINK_GUTTER;
  // the map and its note
  const notes = card.mapNote ? wrapText(card.mapNote, mapCol, 14) : [];
  const mh = Math.min(BB - BT - notes.length * 18 - 6, mapCol * card.map.H / card.map.W);
  const mw = mh * card.map.W / card.map.H;
  s += wardMap(card.map, X, BT, mw, { prefix: "ml", north: true }).svg;
  s += notes.map((l, k) => text(X, BT + mh + 20 + k * 18, l, 14, "sans", { fill: C.ink3 })).join("");
  // the council graphic and its note
  const cx = X + mapCol + MODEL_LINK_GUTTER;
  if (card.chamber) {
    const g = council(card.chamber, cx, BT, { width: cw, cell: 12, gap: 2, fs: 14, barFills: MONO_BAR });
    s += g.svg;
    s += wrapText(card.chamberNote || "", cw, 14).map((l, k) => text(cx, BT + g.h + 24 + k * 18, l, 14, "sans", { fill: C.ink3 })).join("");
  }
  // the table and its note
  const tx = cx + cw + (cw ? MODEL_LINK_GUTTER : 0);
  const tnotes = card.rowsNote ? wrapText(card.rowsNote, R - tx, 13) : [];
  const pitch = Math.min(34, (BB - BT - tnotes.length * 16 - 10) / card.rows.length);
  const t = middleTable(card.rows, assets, { x: tx, right: R, y: BT, pitch, chip: Math.round(pitch * 0.72), fs: Math.min(18, pitch * 0.58), id: "mn" });
  s += t.svg + tnotes.map((l, k) => text(tx, t.bottom + 16 + k * 16, l, 13, "sans", { fill: C.ink3 })).join("");
  return s + "</svg>";
}

// The story card: the logo and the headline, the lines, the map as wide as
// the room allows, then the council graphic beside the table, and the foot.
// The map is tried from the full width down until every block fits above
// STORY_TEXT_BOTTOM; what is left is spread evenly over the gaps.
const MODEL_STORY_CHAMBER = 420, MODEL_STORY_GUTTER = 40, MODEL_STORY_PITCH = 34;
function modelStory(card, assets) {
  const [W, H] = SIZES.story;
  const X = 60, R = W - 60;
  let s = svgOpen(W, H, assets);
  const head = fitText(card.title, R - X, 70, "serifSemi", 40);
  s += text(X, STORY_HEAD_Y, head.text, head.fs, "serifSemi");
  s += brand(assets, X, 44, 130) + rect(X, STORY_BAND - 1, R - X, 1, C.rule);
  // the blocks, sized first
  const lines = card.lines.flatMap(l => wrapText(l.text, R - X, 26, TONE[l.tone || "muted"].face).map(w => ({ w, t: TONE[l.tone || "muted"] })));
  const linesH = 44 + (lines.length - 1) * 34;                 // from the band to the last baseline
  const notes = card.mapNote ? wrapText(card.mapNote, R - X, 22) : [];
  const cw = card.chamber ? MODEL_STORY_CHAMBER : 0;
  const tx = X + cw + (cw ? MODEL_STORY_GUTTER : 0);
  const CO = { width: cw, cell: 14, gap: 3, fs: 20, barFills: MONO_BAR };
  const cnotes = card.chamber ? wrapText(card.chamberNote || "", cw, 20) : [];
  const chamberH = card.chamber ? councilSize(card.chamber, CO).h + 14 + cnotes.length * 26 : 0;
  const tnotes = card.rowsNote ? wrapText(card.rowsNote, R - tx, 20) : [];
  const tableH = card.rows.length * MODEL_STORY_PITCH + 14 + tnotes.length * 26;
  const rowH = Math.max(chamberH, tableH);
  const feet = card.foot.flatMap(f => wrapText(f, R - X, 22));
  const footH = 30 + (feet.length - 1) * 28;                   // from the rule to the last baseline
  const gaps = 3;                                              // after the lines, the map, the row
  const room = STORY_TEXT_BOTTOM - STORY_BAND - linesH - notes.length * 28 - rowH - footH - gaps * STORY_GAP;
  const mw = Math.max(0, Math.min(R - X, room * card.map.W / card.map.H));
  const mh = mw * card.map.H / card.map.W;
  const gap = STORY_GAP + Math.floor(Math.max(0, room - mh) / gaps);
  let y = STORY_BAND + 44;
  for (const l of lines) { s += text(X, y, l.w, 26, l.t.face, { fill: l.t.fill }); y += 34; }
  y += gap - 34;
  s += wardMap(card.map, X + (R - X - mw) / 2, y, mw, { prefix: "ms", north: true }).svg;
  y += mh;
  s += notes.map((l, k) => text(X, y + 28 + k * 28, l, 22, "sans", { fill: C.ink3 })).join("");
  y += notes.length * 28 + gap;
  if (card.chamber) {
    const g = council(card.chamber, X, y, CO);
    s += g.svg + cnotes.map((l, k) => text(X, y + g.h + 34 + k * 26, l, 20, "sans", { fill: C.ink3 })).join("");
  }
  const t = middleTable(card.rows, assets, { x: tx, right: R, y, pitch: MODEL_STORY_PITCH, chip: 26, fs: 21, id: "sm" });
  s += t.svg + tnotes.map((l, k) => text(tx, t.bottom + 30 + k * 26, l, 20, "sans", { fill: C.ink3 })).join("");
  y += rowH + gap;
  s += rect(X, y, R - X, 1, C.rule);
  s += feet.map((l, k) => text(X, y + 30 + k * 28, l, 22, "sans", { fill: C.ink3 })).join("");
  return s + "</svg>";
}

// ---------- the return card, 1200 x 630: two forecasts ----------

// The headline's sizes, largest first: the first at which both names fit.
const DUEL_TITLE = { large: 48, middle: 44, small: 40, least: 36 };
// The headline band's height and the headline's baseline. The band's left
// half follows the first forecast's largest party, its right half the
// second's.
export const DUEL_BAND = 120;
export const DUEL_HEAD_Y = 88;
// Each forecast's bar width, its council's cell, and the two bars' baselines:
// a bar, its council and the line naming its boldest call stack in each.
const DUEL_BAR_W = 470, DUEL_CELL = 10;
const DUEL_PAIR_Y = { first: 206, second: 392 };

export function duelCardSVG(a, b, assets = {}, party) {
  const [W, H] = SIZES.duel;
  const X = 48, R = W - 48;
  let s = svgOpen(W, H, assets);
  const top = colourBand([a, b], 0, 0, W, DUEL_BAND);
  s += top.svg;
  const bh = 96, bw = brandWidth(assets, bh);
  s += bandPlate(top, R + 4 - bw, 14, bw, bh) + brand(assets, R + 4 - bw, 14, bh, top.ink);
  const and = " and ";
  const maxW = R - bw - 24 - X;
  const fs = Object.values(DUEL_TITLE).find(f => textWidth(a.name + and + b.name, f, "serifSemi") <= maxW) || DUEL_TITLE.least;
  const na = fitText(a.name, (maxW - textWidth(and, fs, "serifSemi")) / 2, fs, "serifSemi", fs).text;
  const nb = fitText(b.name, maxW - textWidth(na + and, fs, "serifSemi"), fs, "serifSemi", fs).text;
  // three texts, each placed by measure: SVG drops a text's leading space
  s += textPlate(top, X, DUEL_HEAD_Y, textWidth(na + and + nb, fs, "serifSemi"), fs) +
    text(X, DUEL_HEAD_Y, na, fs, "serifSemi", { fill: top.ink }) +
    text(X + textWidth(na + " ", fs, "serifSemi"), DUEL_HEAD_Y, and.trim(), fs, "serifSemi", { fill: top.ink }) +
    text(X + textWidth(na + and, fs, "serifSemi"), DUEL_HEAD_Y, nb, fs, "serifSemi", { fill: top.ink });
  s += text(X, 150, "Two forecasts of the " + a.election.city + " council, " + a.council + " seats.", 21, "sans", { fill: C.ink2 });
  // the date is the first forecast's own: the second's link carries no seal
  const made = madeText(a);
  if (made) {
    const line = a.name + (/s$/i.test(a.name) ? "'" : "'s") + " forecast " + made.charAt(0).toLowerCase() + made.slice(1) + ", " +
      daysText(daysToVote(a.made.at, a.election)) + ".";
    const fit = fitText(line, R - X, 21, "sans", 16);
    s += text(X, 176, fit.text, fit.fs, "sans", { fill: C.ink2 });
  }
  // each forecast's line on a bar in its own largest party's colour, over
  // its council
  // each forecast's line on a bar in its own largest party's colour, with its
  // badge's words, over its council, and under the council the boldest call
  // the badge judges
  const pair = (F, y) => {
    const who = F.name + " ";
    const rest = "We give it " + aChance(F.outcome.text) + ". " + F.badge + ".";
    const bar = colourBand(F, X, y - 22, DUEL_BAR_W, 30);
    const tail = fitText(rest, DUEL_BAR_W - 16 - textWidth(who, 20, "sansSemi"), 20, "sans", 15);
    const g = council(F, X, y + 14, { width: 350, cell: DUEL_CELL, gap: 2, label: false });
    const call = F.boldest ? fitText(boldestLine(F.boldest, party), DUEL_BAR_W, 16, "sans", 13) : null;
    return bar.svg + textPlate(bar, X + 8, y, textWidth(who, 20, "sansSemi") + textWidth(tail.text, tail.fs), 20) +
      text(X + 8, y, who, 20, "sansSemi", { fill: bar.ink }) +
      text(X + 8 + textWidth(who, 20, "sansSemi"), y, tail.text, tail.fs, "sans", { fill: bar.ink }) +
      g.svg + (call ? text(X, y + 14 + g.h + 18, call.text, call.fs, "sans", { fill: C.ink2 }) : "");
  };
  s += pair(a, DUEL_PAIR_Y.first) + pair(b, DUEL_PAIR_Y.second);
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
  // the largest party of either forecast (each tied for it) has its row in its colour
  const lead = new Set([...a.top, ...b.top]);
  codes.forEach((c, k) => {
    const y = 252 + k * 39, p = party(c), r = { code: c, colour: p.colour, logo: !!p.logo };
    const va = seatsA[c] || 0, vb = seatsB[c] || 0;
    const band = rowBand(lead.has(c), p.colour, tx - 6, y - 28, R - tx + 12, 37);
    const ink = band.ink || C.ink;
    s += band.svg + chip(r, tx, y - 24, 30, assets, band.ink) +
      nameCell("dn" + k, p.name, tx + 40, y, ca - 70 - tx - 40, 23, "sansSemi", ink) +
      text(ca, y, String(va), 25, "sansBold", { fill: ink, anchor: "end" }) + text(cb, y, String(vb), 25, "sansBold", { fill: ink, anchor: "end" }) +
      text(R, y, signed(vb - va), 19, "sans", { fill: band.ink || C.ink3, anchor: "end" });
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
    spec.words, spec.chance, spec.badge, spec.boldestLine, "A reader's forecast, not the model's"]
    .filter(Boolean).map(s => s.replace(/\.$/, "")).join(". ") + ".";
}
export function duelAlt(a, b) {
  return [a.name + " and " + b.name + ": two forecasts of the " + a.election.city + " council",
    a.name + ": " + a.words + " " + a.chance + " " + a.badge + ". " + a.boldestLine,
    b.name + ": " + b.words + " " + b.chance + " " + b.badge + ". " + b.boldestLine]
    .map(s => s.replace(/\.$/, "")).join(". ") + ".";
}

// The brand logo as the cards take it, from site/logo.svg's text.
export function brandOf(svgText) {
  const vb = /viewBox="([^"]+)"/.exec(svgText);
  const body = svgText.replace(/<!--[\s\S]*?-->/g, "").replace(/^[\s\S]*?<svg[^>]*>/, "").replace(/<\/svg>\s*$/, "")
    .replace(/var\(--[\w-]+,\s*currentColor\)/g, "currentColor").replace(/currentColor/g, C.ink);   // resvg reads no CSS variable
  return vb ? { viewBox: vb[1], body } : null;
}
