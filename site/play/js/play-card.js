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
// The layout (DESIGN §2, "Share card"): the Hillbrow Tower strip from the
// site's share.jpg (handed in as a data URL by play-share.js, which fetches
// it), the reader's name as the headline, the ward map, and the middle seat
// count as bars. Two sizes: "link" 1200 x 630 for link previews, "story"
// 1080 x 1920 for phone stories. The site's dark palette as literal hex and
// system font stacks: the image leaves the page, and an SVG drawn into a
// canvas cannot load web fonts.

import { fitText } from "./card-text.js";
import { TRUST, MV_CHARS, PUBLISHED_CELL, PUBLISHED_LAW } from "./play-state.js";

export const SIZES = { link: [1200, 630], story: [1080, 1920] };
export const SITE = "joburg.whysoserious.city";
export const INVITE = "Try your own at " + SITE + "/play";
export const READER_STAMP = "A reader's settings on the model's simulations, not the model's forecast.";
export const PUBLISHED_STAMP = "The model's published forecast.";
export const HOW = "Middle seat count of the simulations; wards in the party's colour, striped where contested.";

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

// A poll's short name, from its register label: "SRF, July 2026".
export function pollName(p) {
  const parts = String(p.label || p.id).split(" · ");
  return parts.length > 1 ? parts[0] + ", " + parts[parts.length - 1] : parts[0];
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

// The headline: the reader's name, which is their text and is escaped where drawn.
export function headline(name) {
  return name + "'s Election Forecast";
}

// The foot under the card, in sentences.
export function footText({ r, st, ctx, made }) {
  const words = st && isMoved(st) ? settingsWords(st, ctx) : [];
  const said = words.length ? READER_STAMP + " " + cap(words.join("; ")) + "; everything else as published." : PUBLISHED_STAMP;
  return said + " " + HOW + " " + INVITE + ". " + madeLine(made, ctx) + ".";
}
const cap = s => s.charAt(0).toUpperCase() + s.slice(1);
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
// page's map. No labels and no outlines.
function map({ r, geometry, x, y, w, prefix }) {
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
  return { h, svg: `<g transform="translate(${x} ${y}) scale(${s.toFixed(4)})"><defs>${defs.join("")}</defs>${fills.join("")}${hatches.join("")}</g>` };
}

// The median bars: every row the page shows, then Others.
function bars({ r, party, x, y, w, rowH, fs }) {
  const codes = [...order(r, c => party(c).name), "OTHERS"];
  const val = c => (r.seats[c].median.withheld ? 0 : r.seats[c].median.value);
  const top = Math.max(1, ...codes.map(val));
  const nameW = fs * 6.4, figW = fs * 2.4, barW = w - nameW - figW;
  return codes.map((c, k) => {
    const yy = y + k * rowH, nm = c === "OTHERS" ? "Others" : party(c).name;
    const colour = c === "OTHERS" ? C.others : party(c).colour;
    const fitted = fitText(nm, nameW - 8, fs);
    const len = Math.max(3, barW * val(c) / top * 0.96);
    return text(x, yy + fs * 0.85, fitted.text, { fs: fitted.fs, fill: C.ink, weight: "600" }) +
      (r.seats[c].median.withheld ? "" : `<rect x="${(x + nameW).toFixed(1)}" y="${(yy + fs * 0.15).toFixed(1)}" width="${len.toFixed(1)}" height="${(fs * 0.8).toFixed(1)}" rx="2" fill="${colour}"/>`) +
      text(x + w, yy + fs * 0.9, seatText(r.seats[c].median), { fs: fs * 1.2, fill: C.ink, weight: "700", anchor: "end" });
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
export function buildPlayCardSVG({ r, st, ctx, party, made, name, geometry, photoSrc, when, size = "link" }) {
  if (!r || r.refused) throw new Error("the card needs a computed result, not a refusal");
  if (!geometry) throw new Error("the card needs the ward boundaries");
  const [W, H] = SIZES[size];
  const sub = "Johannesburg council" + (when ? ", " + when : "") + " · " + seatText({ value: r.council }) +
    " seats, " + seatText({ value: r.majority }) + " for a majority";
  const foot = footText({ r, st, ctx, made });
  let body;
  if (size === "link") {
    const sx = 268, sw = W - sx - 34;
    const head = fitText(headline(name), sw, 44, "serifBold", 30);
    const m = map({ r, geometry, x: sx, y: 128, w: 520, prefix: "cl" });
    const feet = wrap(foot, sw, 12);
    const rowH = Math.min(29, (H - 150 - feet.length * 16 - 30) / (r.shown.length + 1));
    body = photo({ src: photoSrc, w: 250, h: H, fade: "right" }) +
      text(30, H - 22, SITE, { fs: 15, family: MONO, fill: C.ink, weight: "700", transform: `rotate(-90 30 ${H - 22})` }) +
      text(sx, 74, head.text, { fs: head.fs, family: SERIF, fill: C.ink, weight: "600" }) +
      text(sx, 104, sub, { fs: 16 }) +
      m.svg +
      bars({ r, party, x: sx + 546, y: 140, w: sw - 546, rowH, fs: 15 }) +
      `<rect x="${sx}" y="${H - 18 - feet.length * 16 - 8}" width="${sw}" height="1" fill="${C.rule}"/>` +
      feet.map((l, k) => text(sx, H - 14 - (feet.length - 1 - k) * 16, l, { fs: 12, fill: C.ink3 })).join("");
  } else {
    const x = 60, w = W - 120;
    const head = fitText(headline(name), w, 72, "serifBold", 44);
    // the rows get a readable height first; the map takes the room left
    const feet = wrap(foot, w, 24);
    const rowH = 46, rows = (r.shown.length + 1) * rowH;
    const mapY = 620, room = 1800 - feet.length * 32 - 60 - rows - 40 - mapY;
    const mw = Math.min(w, room * geometry.W / geometry.H);
    const m = map({ r, geometry, x: x + (w - mw) / 2, y: mapY, w: mw, prefix: "cs" });
    const rowsY = mapY + m.h + 40;
    body = photo({ src: photoSrc, w: W, h: H, fade: "down" }) +
      text(x, 120, SITE, { fs: 30, family: MONO, fill: C.ink, weight: "700" }) +
      text(x, 470, head.text, { fs: head.fs, family: SERIF, fill: C.ink, weight: "600" }) +
      wrap(sub, w, 30).map((l, k) => text(x, 530 + k * 38, l, { fs: 30 })).join("") +
      m.svg +
      bars({ r, party, x, y: rowsY, w, rowH, fs: 26 }) +
      feet.map((l, k) => text(x, 1800 - (feet.length - 1 - k) * 32, l, { fs: 24, fill: C.ink3 })).join("");
  }
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">` +
    `<rect width="${W}" height="${H}" fill="${C.paper}"/>${body}</svg>`;
}

// The image's text alternative: the same figures, in the same order.
export function playCardAlt({ r, st, ctx, party, made, name }) {
  const codes = [...order(r, c => party(c).name), "OTHERS"];
  const seats = codes.map(c => (c === "OTHERS" ? "Others" : party(c).name) + " " + seatText(r.seats[c].median));
  return headline(name) + ". Middle seats on the Johannesburg council: " + seats.join(", ") + ". " +
    footText({ r, st, ctx, made });
}
