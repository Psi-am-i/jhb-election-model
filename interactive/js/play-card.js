// "Play with the model": the share image of a reader's settings, and the words
// the page and the image share.
//
// ⛔ A LIVE WRITER WITH NO REGION (stats.LIVE_WRITERS["play/js/play-card.js"]).
// It turns the compute result the page is showing into an SVG, so it builds
// figures, and it reaches no element of the page: play-share.js puts the
// image into the share sheet. Listed so that stats.script_writes holds it to
// the writer contract (no lookup outside a LIVE selector, no markup injection,
// no data block, no data source) instead of refusing its template strings.
//
// ONE RESULT, TWO VIEWS. Every figure on the card is read from the result
// object js/model.js rendered (pyboot/page.py's compute, through
// src/reweight.py and render_map.ward_call); nothing here computes a seat or
// colours a ward by its own rule. The party order (order), the seat format
// (seatText) and the words for each setting (LAW_TEXT, cellName,
// settingsWords) are defined here once and used by the page as well, so the
// card cannot disagree with the page.
//
// NEUTRAL (DESIGN-decided §8): the parties appear in the page's order (middle
// seat count, highest first, ties by name), every one drawn the same way in
// its own colour; none is marked out.
//
// The layout (DESIGN §2, "Share card", amended after the critic's G1-G3,
// 2026-10-02): the Hillbrow Tower strip from the site's share.jpg (handed in
// as a data URL by play-share.js, which fetches it); a headline that says
// whose figures these are (the model's published forecast, or a reader's
// settings on the model, never "{name}'s Election Forecast": a name is anyone's
// text, and the site would print it over its own forecast); "Not the model's
// forecast" in the line under it when the reader moved anything; the
// largest-party line, ties apart; the ward map with north marked and a line
// saying it holds the ward seats only; and each party's middle seat count with
// the range holding nine in ten. Two sizes: "link" 1200 x 630 for link
// previews, "story" 1080 x 1920 for phone stories, whose words stay above the
// bottom band story apps cover. The site's dark palette as literal hex and
// system font stacks: the image leaves the page, and an SVG drawn into a
// canvas cannot load web fonts.

import { fitText } from "./card-text.js";
import { TRUST, MV_CHARS, PUBLISHED_CELL, PUBLISHED_LAW } from "./play-state.js";

export const SIZES = { link: [1200, 630], story: [1080, 1920] };
export const SITE = "joburg.whysoserious.city";
export const INVITE = "Try your own at " + SITE + "/play";
export const READER_STAMP = "Not the model's forecast: a reader's settings on its simulations.";
export const PUBLISHED_STAMP = "The model's published forecast.";
export const HOW = "Wards in the colour of their most likely winner, striped where contested.";
export const MAP_NOTE = "ward seats; the council's other seats are filled from party lists.";
export const BARS_NOTE = "Middle of each party's simulations, and the range holding nine in ten. The middles need not add up to the council's size.";
// The lowest a story card's words may sit: story apps lay their reply bar
// over the band below it.
export const STORY_TEXT_BOTTOM = 1660;

const C = {
  paper: "#141715", paper2: "#1c201d", rule: "#333833", ink: "#eceee9",
  ink2: "#b6bcb6", ink3: "#868d86", accent: "#d9954f", reader: "#b98ad6", others: "#464d47",
};
const SERIF = `'Iowan Old Style','Palatino Linotype',Palatino,Georgia,serif`;
const SANS = `ui-sans-serif,system-ui,-apple-system,'Segoe UI',Roboto,Arial,sans-serif`;
const MONO = `ui-monospace,'SF Mono',Menlo,Consolas,monospace`;
// The share.jpg strip: the tower's column in the 1200 x 630 photograph.
const PHOTO = { w: 1200, h: 630, towerX: 613 };

// The seat law's four settings: a short name and what it does.
export const LAW_TEXT = {
  deduct: ["Deduct", "The law: the surplus comes off every other party"],
  expand: ["Expand", "Not the law: the council grows by the surplus"],
  level: ["Level", "Not the law: the council grows until every party is covered"],
  cap: ["Cap", "Not the law: surplus ward winners are not seated"],
};

// A by-election cell's name: the published weight, none, or full.
export function cellName(c) {
  if (c.path === PUBLISHED_CELL) return "Partly, as the forecast does";
  return c.w_bye === 0 ? "Not at all" : c.w_bye === 1 ? "Fully" : "Weight " + c.w_bye;
}

// A poll's short name, from its register label: "SRF, July 2026". When the
// register says only when the poll was reported (its fieldwork dates were not
// published), the date is called that: "Ipsos Khayabus, reported September
// 2026" (critic, 2026-10-02).
export function pollName(p) {
  const parts = String(p.label || p.id).split(" · ");
  const reported = /^reported\b/i.test(String(p.fieldwork || "")) ? "reported " : "";
  return parts.length > 1 ? parts[0] + ", " + reported + parts[parts.length - 1] : parts[0];
}

// One seat figure as the page and the card print it.
export function seatText(f) {
  return f.withheld ? "withheld" : String(Math.round(f.value * 10) / 10);
}

// The parties the result shows, in the page's order; "Others" is not among them.
export function order(r, name) {
  const val = f => (f.withheld ? Infinity : f.value);
  return r.shown.slice().sort((a, b) => val(r.seats[b].median) - val(r.seats[a].median) || name(a).localeCompare(name(b)));
}

const signedPoints = x => (x > 0 ? "+" : "") + x + (Math.abs(x) === 1 ? " point" : " points");

// The reader's settings in words, one per setting moved from the published
// forecast. `st` is play-state.js's state; `ctx` the page's.
export function settingsWords(st, ctx) {
  const out = ctx.pools.map((p, i) => [p, st.shift[i]]).filter(([, x]) => x !== 0)
    .map(([p, x]) => p + " turnout " + signedPoints(x));
  const poll = ctx.pollRows.find(p => st.polls.includes(p.id));
  if (poll && st.trust > 0) out.push(pollName(poll) + " poll, believed at " + st.trust + " of " + TRUST.max);
  const cell = ctx.cellRows.find(c => c.path === st.cell);
  if (st.cell !== PUBLISHED_CELL)
    out.push(!cell ? "by-elections: " + st.cell : cell.w_bye === 0 ? "by-elections not counted"
      : cell.w_bye === 1 ? "by-elections counted fully" : "by-elections at weight " + cell.w_bye);
  if (st.law !== PUBLISHED_LAW) {
    const [short, long] = LAW_TEXT[st.law] || [st.law, ""];
    out.push("seat law: " + (long.replace(/^Not the law: /, "") || short.toLowerCase()) + " (not the law)");
  }
  return out;
}

// When the card was made and against which model: a card outlives the
// forecast it was drawn from (critic S1). `made` is the date the page passes
// in, ISO 8601; the version is the link's own `mv`.
export function madeLine(made, ctx) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(String(made))) throw new Error("the card needs the date it was made, YYYY-MM-DD");
  return "Made " + made + " · model " + String(ctx.modelVersion).slice(0, MV_CHARS);
}

// The headline. Untouched, the card is the model's forecast and says so; the
// name goes on a "Shared by" line under it. Touched, it is the reader's
// settings on the model, under the reader's name. The name is the reader's
// text and is escaped where drawn.
export function headline(name, touched) {
  return touched ? name + "'s settings on the model" : "The model's Johannesburg forecast";
}
export const sharedBy = name => "Shared by " + name;

// The two parties most often alone with the most seats, in alphabetical
// order, as the page's one-line result names them.
export function largestTop(r, party) {
  return Object.keys(r.largest).sort((a, b) => r.largest[b].p - r.largest[a].p).slice(0, 2)
    .sort((a, b) => party(a).name.toLowerCase().localeCompare(party(b).name.toLowerCase()));
}
// The largest-party line, in the shares' own text (page.py, reweight.chance_text).
export function largestLine(r, party) {
  const [a, b] = largestTop(r, party);
  const nm = c => party(c).article + party(c).name;
  return "Largest party: " + nm(a) + " in " + r.largest[a].text + " of simulations, " + nm(b) + " in " +
    r.largest[b].text + ". Tied for the most seats in " + r.tied.text + ".";
}

// The line under the headline: whose figures these are, then the council.
export function councilLine({ r, when }) {
  return "Johannesburg council" + (when ? ", " + when : "") + " · " + seatText({ value: r.council }) +
    " seats, " + seatText({ value: r.majority }) + " for a majority";
}
export function subLine({ r, touched, when }) {
  return touched ? READER_STAMP + " " + councilLine({ r, when }) : councilLine({ r, when });
}

// The foot under the card, in sentences.
export function footText({ r, st, ctx, made }) {
  const words = st && isMoved(st) ? settingsWords(st, ctx) : [];
  const said = words.length ? "Settings: " + words.join("; ") + "; everything else as published." : PUBLISHED_STAMP;
  return said + " " + HOW + " " + INVITE + ". " + madeLine(made, ctx) + ".";
}
const isMoved = st => st.shift.some(x => x !== 0) || (st.trust > 0 && st.polls.length > 0) || st.law !== PUBLISHED_LAW || st.cell !== PUBLISHED_CELL;

const esc = s => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

function text(x, y, s, { fs, family = SANS, fill = C.ink2, weight = "", anchor = "", transform = "" }) {
  return `<text x="${x}" y="${y}" font-family="${family}" font-size="${fs}"${weight ? ` font-weight="${weight}"` : ""}${anchor ? ` text-anchor="${anchor}"` : ""}${transform ? ` transform="${transform}"` : ""} fill="${fill}">${esc(s)}</text>`;
}

// Wrap on spaces into lines whose estimated width fits maxW.
function wrap(s, maxW, fs) {
  const out = [];
  let cur = "";
  for (const w of String(s).split(" ")) {
    const next = (cur + " " + w).trim();
    if (cur && fitText(next, maxW, fs, "sans", fs).text !== next) { out.push(cur); cur = w; }
    else cur = next;
  }
  if (cur) out.push(cur);
  return out;
}

// The ward map, from the result's wards (render_map.ward_call through
// page.py) and the boundaries the page draws: fills, then the stripes, as the
// page's map, and north marked as the page marks it. No outlines.
function map({ r, geometry, x, y, w, prefix, fs }) {
  const s = w / geometry.W, h = geometry.H * s;
  const defs = [], fills = [], hatches = [];
  for (const ward of r.wards) {
    const d = geometry.paths[ward.ward];
    if (!d) continue;
    fills.push(`<path d="${d}" fill="${ward.fill}" stroke="${C.paper}" stroke-width="0.8"/>`);
    if (ward.bands) {
      const id = prefix + ward.ward;
      defs.push(`<pattern id="${id}" width="${geometry.step}" height="${geometry.step}" patternTransform="rotate(${geometry.rotate})" patternUnits="userSpaceOnUse">` +
        ward.bands.map(b => `<line x1="${b.x.toFixed(2)}" y1="0" x2="${b.x.toFixed(2)}" y2="${geometry.step}" stroke="${b.colour}" stroke-width="${b.w.toFixed(2)}"/>`).join("") + "</pattern>");
      hatches.push(`<path d="${d}" fill="url(#${id})"/>`);
    }
  }
  const north = text(x + w - 4, y + fs, "N ↗", { fs, family: MONO, fill: C.ink2, anchor: "end" });
  return { h, svg: `<g transform="translate(${x} ${y}) scale(${s.toFixed(4)})"><defs>${defs.join("")}</defs>${fills.join("")}${hatches.join("")}</g>` + north };
}

// The seat rows: every row the page shows, then Others. Each is the range
// holding nine in ten of the party's simulations, its middle marked, the
// middle in figures and the range beside it, on one scale for every row.
export const rangeText = s => (s.p5.withheld || s.p95.withheld ? "withheld" : seatText(s.p5) + "–" + seatText(s.p95));
function bars({ r, party, x, y, w, rowH, fs }) {
  const codes = [...order(r, c => party(c).name), "OTHERS"];
  const hi = c => (r.seats[c].p95.withheld ? (r.seats[c].median.withheld ? 0 : r.seats[c].median.value) : r.seats[c].p95.value);
  const top = Math.max(1, ...codes.map(hi));
  const nameW = fs * 6.2, figW = fs * 2.2, rngW = fs * 3.6, barW = w - nameW - figW - rngW - 8;
  const at = v => x + nameW + barW * v / top;
  return codes.map((c, k) => {
    const s = r.seats[c], yy = y + k * rowH, nm = c === "OTHERS" ? "Others" : party(c).name;
    const colour = c === "OTHERS" ? C.others : party(c).colour;
    const fitted = fitText(nm, nameW - 8, fs);
    const band = s.p5.withheld || s.p95.withheld ? ""
      : `<rect x="${at(s.p5.value).toFixed(1)}" y="${(yy + fs * 0.2).toFixed(1)}" width="${Math.max(2, at(s.p95.value) - at(s.p5.value)).toFixed(1)}" height="${(fs * 0.7).toFixed(1)}" rx="2" fill="${colour}" fill-opacity="0.6"/>`;
    const tick = s.median.withheld ? ""
      : `<rect x="${(at(s.median.value) - 1.5).toFixed(1)}" y="${(yy).toFixed(1)}" width="3" height="${(fs * 1.1).toFixed(1)}" rx="1" fill="${C.ink}"/>`;
    return text(x, yy + fs * 0.85, fitted.text, { fs: fitted.fs, fill: C.ink, weight: "600" }) + band + tick +
      text(x + w - rngW, yy + fs * 0.9, seatText(s.median), { fs: fs * 1.15, fill: C.ink, weight: "700", anchor: "end" }) +
      text(x + w, yy + fs * 0.9, rangeText(s), { fs: fs * 0.85, fill: C.ink3, anchor: "end" });
  }).join("");
}

// The photograph, cropped to a window `vw` wide on the tower and stretched
// to fill w x h, with the page's paper fading in on the given side.
function photo({ src, w, h, fade }) {
  if (!src) return `<rect width="${w}" height="${h}" fill="${C.paper2}"/>`;
  const vh = PHOTO.h, vw = Math.min(PHOTO.w, vh * w / h), vx = Math.max(0, Math.min(PHOTO.w - vw, PHOTO.towerX - vw / 2));
  const grad = fade === "right"
    ? `<linearGradient id="pf" x1="0" x2="1" y1="0" y2="0"><stop offset="0.7" stop-color="${C.paper}" stop-opacity="0"/><stop offset="1" stop-color="${C.paper}"/></linearGradient>`
    : `<linearGradient id="pf" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="${C.paper}" stop-opacity="0.2"/><stop offset="0.45" stop-color="${C.paper}" stop-opacity="0.55"/><stop offset="0.62" stop-color="${C.paper}"/></linearGradient>`;
  return `<defs>${grad}</defs><svg x="0" y="0" width="${w}" height="${h}" viewBox="${vx.toFixed(1)} 0 ${vw.toFixed(1)} ${vh}" preserveAspectRatio="xMidYMid slice">` +
    `<image href="${src}" x="0" y="0" width="${PHOTO.w}" height="${PHOTO.h}"/></svg><rect width="${w}" height="${h}" fill="url(#pf)"/>`;
}

// The card for one result. `r` is the compute result the page shows (the
// published one when nothing is moved); `st`/`ctx` the settings that produced
// it; `party(code)` -> {name, colour}; `made` the date it was made; `name` the
// reader's name or label; `geometry` the ward boundaries with the stripe
// tile (`step`, `rotate`); `photoSrc` share.jpg as a data URL, or null;
// `when` the election day in words.
export function buildPlayCardSVG({ r, st, ctx, party, made, name, geometry, photoSrc, when, touched, size = "link" }) {
  if (!r || r.refused) throw new Error("the card needs a computed result, not a refusal");
  if (!geometry) throw new Error("the card needs the ward boundaries");
  const [W, H] = SIZES[size];
  // the stamp (touched) or "Shared by" (untouched), each on its own line,
  // then the council
  const second = touched ? READER_STAMP : sharedBy(name);
  const sub = councilLine({ r, when });
  const lead = largestLine(r, party);
  const mapNote = r.wards.length + " " + MAP_NOTE;
  const foot = footText({ r, st, ctx, made });
  let body;
  if (size === "link") {
    const sx = 268, sw = W - sx - 34;
    const head = fitText(headline(name, touched), sw, 40, "serifBold", 26);
    const subs = wrap(sub, sw, 15);
    const feet = wrap(foot, sw, 12);
    let y = 64;
    const top = text(sx, y, head.text, { fs: head.fs, family: SERIF, fill: C.ink, weight: "600" }) +
      wrap(second, sw, 15).map((l, k) => text(sx, (y += k ? 20 : 28), l, { fs: 15, fill: touched ? C.ink : C.ink2, weight: touched ? "600" : "" })).join("") +
      subs.map(l => text(sx, (y += 21), l, { fs: 15, fill: C.ink2 })).join("") +
      wrap(lead, sw, 15).map(l => text(sx, (y += 24), l, { fs: 15, fill: C.ink })).join("");
    const footTop = H - 14 - (feet.length - 1) * 16 - 12;
    const mapY = y + 18, mapW = 470;
    const m = map({ r, geometry, x: sx, y: mapY, w: mapW, prefix: "cl", fs: 12 });
    const notes = wrap(mapNote, mapW, 12);
    const bx = sx + mapW + 22, bw = sw - mapW - 22;
    const bnotes = wrap(BARS_NOTE, bw, 12);
    const rowH = Math.min(28, (footTop - 10 - mapY - bnotes.length * 15 - 6) / (r.shown.length + 1));
    const rowsEnd = mapY + rowH * (r.shown.length + 1);
    body = photo({ src: photoSrc, w: 250, h: H, fade: "right" }) +
      text(30, H - 22, SITE, { fs: 15, family: MONO, fill: C.ink, weight: "700", transform: `rotate(-90 30 ${H - 22})` }) +
      top + m.svg +
      notes.map((l, k) => text(sx, Math.min(mapY + m.h + 14, footTop - 6 - (notes.length - 1) * 15) + k * 15, l, { fs: 12, fill: C.ink3 })).join("") +
      bars({ r, party, x: bx, y: mapY, w: bw, rowH, fs: 14 }) +
      bnotes.map((l, k) => text(bx, rowsEnd + 12 + k * 15, l, { fs: 12, fill: C.ink3 })).join("") +
      `<rect x="${sx}" y="${footTop - 4}" width="${sw}" height="1" fill="${C.rule}"/>` +
      feet.map((l, k) => text(sx, footTop + 12 + k * 16, l, { fs: 12, fill: C.ink3 })).join("");
  } else {
    const x = 60, w = W - 120;
    const head = fitText(headline(name, touched), w, 64, "serifBold", 40);
    let y = 440;
    const top = text(x, y, head.text, { fs: head.fs, family: SERIF, fill: C.ink, weight: "600" }) +
      wrap(second, w, 28).map((l, k) => text(x, (y += k ? 38 : 50), l, { fs: 28, fill: touched ? C.ink : C.ink2, weight: touched ? "600" : "" })).join("") +
      wrap(sub, w, 28).map(l => text(x, (y += 38), l, { fs: 28, fill: C.ink2 })).join("") +
      wrap(lead, w, 28).map(l => text(x, (y += 40), l, { fs: 28, fill: C.ink })).join("");
    const feet = wrap(foot, w, 22);
    const notes = wrap(mapNote, w, 22), bnotes = wrap(BARS_NOTE, w, 22);
    const rowH = 44, rows = (r.shown.length + 1) * rowH;
    const footTop = STORY_TEXT_BOTTOM - (feet.length - 1) * 28;
    const mapY = y + 30;
    const room = footTop - 40 - bnotes.length * 28 - 20 - rows - 30 - notes.length * 28 - 20 - mapY;
    const mw = Math.min(w, room * geometry.W / geometry.H);
    const m = map({ r, geometry, x: x + (w - mw) / 2, y: mapY, w: mw, prefix: "cs", fs: 22 });
    let yy = mapY + m.h + 6;
    const mapText = notes.map(l => text(x, (yy += 28), l, { fs: 22, fill: C.ink3 })).join("");
    const rowsY = yy + 30;
    yy = rowsY + rows;
    const barText = bnotes.map(l => text(x, (yy += 28), l, { fs: 22, fill: C.ink3 })).join("");
    body = photo({ src: photoSrc, w: W, h: H, fade: "down" }) +
      text(x, 120, SITE, { fs: 30, family: MONO, fill: C.ink, weight: "700" }) +
      top + m.svg + mapText +
      bars({ r, party, x, y: rowsY, w, rowH, fs: 26 }) + barText +
      feet.map((l, k) => text(x, footTop + k * 28, l, { fs: 22, fill: C.ink3 })).join("");
  }
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">` +
    `<rect width="${W}" height="${H}" fill="${C.paper}"/>${body}</svg>`;
}

// The image's text alternative: the same figures, in the same order.
export function playCardAlt({ r, st, ctx, party, made, name, when, touched }) {
  const codes = [...order(r, c => party(c).name), "OTHERS"];
  const seats = codes.map(c => (c === "OTHERS" ? "Others" : party(c).name) + " " + seatText(r.seats[c].median) +
    " (" + rangeText(r.seats[c]) + ")");
  return headline(name, touched) + ". " + (touched ? "" : sharedBy(name) + ". ") + subLine({ r, touched, when }) + ". " +
    largestLine(r, party) + " Middle seats, with the range holding nine in ten: " + seats.join(", ") + ". " +
    footText({ r, st, ctx, made });
}
