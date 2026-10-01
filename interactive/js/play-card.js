// "Play with the model": the share image of a reader's settings, and the words
// and figures the page and the image share.
//
// ⛔ A LIVE WRITER WITH NO REGION (stats.LIVE_WRITERS["play/js/play-card.js"]).
// It turns the compute result the page is showing into an SVG, so it builds
// figures, and it reaches no element of the page: play-share.js puts the
// image into the share sheet. Listed so that stats.script_writes holds it to
// the writer contract (no lookup outside a LIVE selector, no markup injection)
// instead of refusing its template strings.
//
// ONE RESULT, TWO VIEWS. Every figure on the card is read from the result
// object js/model.js rendered into the seat table (pyboot/page.py's compute,
// through src/reweight.py); nothing here computes a seat. The party order
// (order), the seat format (seatText) and the words for each setting
// (LAW_TEXT, cellName, settingsLines) are defined here once and used by the
// page's table as well, so the card cannot disagree with the page.
//
// NEUTRAL (DESIGN-decided §8): the parties appear in the page's order (middle
// seat count, highest first, ties by name), every one drawn the same way in
// its own colour; none is marked out. When the card has no room for every
// party the page shows, it cuts at a position and says how many it left out.
//
// Two sizes, as the builder's card (card.js): "link" 1200 x 630 for link
// previews, "story" 1080 x 1920 for phone stories, content inside the middle
// band clear of the story apps' chrome. The site's dark palette as literal hex
// and system font stacks: the image leaves the page, and an SVG drawn into a
// canvas cannot load web fonts.

import { textWidth, fitText } from "./card-text.js";
import { TRUST, MV_CHARS } from "./play-state.js";

export const SIZES = { link: [1200, 630], story: [1080, 1920] };
export const SITE = "joburg.whysoserious.city";
export const STAMP = "The model's simulations under your settings. Not the model's forecast.";
export const INVITE = "Try your own at " + SITE + "/play";
// In the header, beside the site's name, so a crop of the card's foot cannot
// leave the figures reading as the forecast (critic S3, 2026-10-01).
export const BANNER = "NOT THE FORECAST: a reader's settings";

const C = {
  paper: "#141715", paper2: "#1c201d", rule: "#333833", ink: "#eceee9",
  ink2: "#b6bcb6", ink3: "#868d86", accent: "#d9954f", reader: "#b98ad6",
};
const SERIF = `'Iowan Old Style','Palatino Linotype',Palatino,Georgia,serif`;
const SANS = `ui-sans-serif,system-ui,-apple-system,'Segoe UI',Roboto,Arial,sans-serif`;
const MONO = `ui-monospace,'SF Mono',Menlo,Consolas,monospace`;

// The seat law's four settings, in words. The page's radio labels use these.
export const LAW_TEXT = {
  deduct: "The law: the surplus is deducted from every other party",
  expand: "Not the law: the council grows by the excess",
  level: "Not the law: the council grows until every party is covered",
  cap: "Not the law: excess ward winners are not seated",
};

// A by-election cell's name, from its weight (index.json's w_bye).
export function cellName(c) {
  return c.w_bye === 0 ? "None" : c.w_bye === 1 ? "Full" : "As published (" + c.w_bye.toFixed(2) + ")";
}

// One seat figure as the page and the card print it.
export function seatText(f) {
  return f.withheld ? "withheld" : String(Math.round(f.value * 10) / 10);
}

// The parties the result shows, in the page's order.
export function order(r, name) {
  const val = f => (f.withheld ? Infinity : f.value);
  return r.shown.slice().sort((a, b) => val(r.seats[b].median) - val(r.seats[a].median) || name(a).localeCompare(name(b)));
}

const signedPoints = x => (x > 0 ? "+" : "") + x + (Math.abs(x) === 1 ? " point" : " points");

// JUDGEMENT-CALLS §N2: polls switched on together multiply as independent
// readings, which two waves of one house are not. One entry per house with
// more than one poll switched on, from the poll rows' own `house`, the same
// rule for every house. The page (model.js) prints `sameHouse`, which names
// the polls; the card prints `sameHouseShort`, because its settings line has
// already listed them (owner's style sweep, 2026-10-01).
function housesTwice(ids, pollRows) {
  const by = {};
  for (const p of pollRows) if (ids.includes(p.id) && p.house) (by[p.house] ??= []).push(p.label || p.id);
  return Object.entries(by).filter(([, ls]) => ls.length > 1);
}
export function sameHouse(ids, pollRows) {
  return housesTwice(ids, pollRows)
    .map(([h, ls]) => `${ls.join(" and ")} are from one polling house (${h}) and are counted as independent, so that house's error counts once for each.`);
}
export function sameHouseShort(ids, pollRows) {
  return housesTwice(ids, pollRows).map(([h]) => `Counted as independent: polls from one house, ${h}`);
}

// When the card was made and against which model: a card outlives the
// forecast it was drawn from (critic S1). `made` is the date the page passes
// in, ISO 8601; the version is the link's own `mv`.
export function madeLine(made, ctx) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(String(made))) throw new Error("the card needs the date it was made, YYYY-MM-DD");
  return "Made " + made + " · model " + String(ctx.modelVersion).slice(0, MV_CHARS);
}

// The reader's settings in words, one line each, every setting named whether
// or not it was moved. `st` is play-state.js's state; `ctx` the page's.
export function settingsLines(st, ctx) {
  const moved = ctx.pools.map((p, i) => [p, st.shift[i]]).filter(([, x]) => x !== 0);
  const lines = [moved.length ? "Turnout: " + moved.map(([p, x]) => p + " " + signedPoints(x)).join(", ")
    : "Turnout: as published"];
  const on = ctx.pollRows.filter(p => st.polls.includes(p.id)).map(p => p.label || p.id);
  lines.push(st.trust > 0 && on.length ? "Polls at trust " + st.trust + " of " + TRUST.max + ": " + on.join("; ") : "Polls: none trusted, as published");
    if (st.trust > 0) lines.push(...sameHouseShort(st.polls, ctx.pollRows));
  const cell = ctx.cellRows.find(c => c.path === st.cell);
  lines.push("Weight of recent by-elections: " + (cell ? cellName(cell) : st.cell));
  lines.push(LAW_TEXT[st.law] || "Seat law: " + st.law);
  return lines;
}

const esc = s => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

// Wrap on spaces into lines no wider than maxW; a word wider than maxW is cut.
function wrap(s, maxW, fs, face = "sans") {
  const out = [];
  let cur = "";
  for (const w of String(s).split(" ")) {
    const next = (cur + " " + w).trim();
    if (cur && textWidth(next, fs, face) > maxW) { out.push(cur); cur = w; }
    else cur = next;
  }
  if (cur) out.push(cur);
  return out.map(l => fitText(l, maxW, fs, face, fs).text);
}

// The seat rows: name, a bar from the range's low end to its high end with a
// mark at the middle, and the figures. Withheld figures are drawn as words.
function rows(list, r, party, x, y, w, rowH, fs) {
  const top = Math.max(1, ...list.map(c => (r.seats[c].p95.withheld ? 0 : r.seats[c].p95.value)));
  const fig = c => {
    const s = r.seats[c];
    return seatText(s.median) + " (" + seatText(s.p5) + "–" + seatText(s.p95) + ")";
  };
  const gap = fs * 0.6;
  const figW = Math.max(...list.map(c => textWidth(fig(c), fs, "sansBold"))) + gap;
  const nameW = Math.min((w - figW) * 0.45, Math.max(...list.map(c => textWidth(party(c).name, fs)))) + gap;
  const barW = w - nameW - figW;
  const at = v => x + nameW + barW * v / top;
  return list.map((c, k) => {
    const s = r.seats[c], yy = y + k * rowH, p = party(c);
    const nm = fitText(p.name, nameW - gap, fs);
    let bar = "";
    if (!s.p5.withheld && !s.p95.withheld) {
      const x0 = at(s.p5.value), x1 = Math.max(at(s.p95.value), x0 + 3);
      bar += `<rect x="${x0.toFixed(1)}" y="${(yy + fs * 0.2).toFixed(1)}" width="${(x1 - x0).toFixed(1)}" height="${(fs * 0.8).toFixed(1)}" rx="2" fill="${p.colour}" fill-opacity="0.45"/>`;
    }
    if (!s.median.withheld) {
      bar += `<rect x="${(at(s.median.value) - 2).toFixed(1)}" y="${(yy - fs * 0.05).toFixed(1)}" width="4" height="${(fs * 1.3).toFixed(1)}" fill="${p.colour}"/>`;
    }
    return `<text x="${x}" y="${(yy + fs * 0.9).toFixed(1)}" font-family="${SANS}" font-size="${nm.fs}" fill="${C.ink}">${esc(nm.text)}</text>` + bar +
      `<text x="${x + w}" y="${(yy + fs * 0.9).toFixed(1)}" text-anchor="end" font-family="${SANS}" font-weight="700" font-size="${fs}" fill="${C.ink}">${esc(fig(c))}</text>`;
  }).join("");
}

function text(x, y, s, { fs, family = SANS, fill = C.ink2, weight = "", anchor = "" }) {
  return `<text x="${x}" y="${y}" font-family="${family}" font-size="${fs}"${weight ? ` font-weight="${weight}"` : ""}${anchor ? ` text-anchor="${anchor}"` : ""} fill="${fill}">${esc(s)}</text>`;
}

// The line under the seat rows: the council and the majority the seat law
// returned for these settings, the parties left out, and the simulations used.
function councilLine(r, left) {
  const more = left > 0 ? left + (left === 1 ? " more party" : " more parties") + " not shown. " : "";
  return more + "Middle seats, with the range covering nine in ten of the re-weighted simulations. They count as " +
    Math.round(r.effective_draws).toLocaleString("en-ZA") + " of " + r.draws.toLocaleString("en-ZA") +
    " equally weighted ones. A majority is " + seatText({ value: r.majority }) +
    " of " + seatText({ value: r.council }) + " seats.";
}

// At most `n` wrapped lines; when some are cut, the last says so.
function capLines(ls, n) {
  return ls.length <= n ? ls : [...ls.slice(0, n - 1), "… more settings: the link carries every one."];
}

// The card for one result. `r` is the compute result the page rendered;
// `st`/`ctx` the settings that produced it; `party(code)` -> {name, colour};
// `made` the date it was made (madeLine).
export function buildPlayCardSVG({ r, st, ctx, party, made, size = "link" }) {
  if (!r || r.refused) throw new Error("the card needs a computed result, not a refusal");
  const [W, H] = SIZES[size];
  const all = order(r, c => party(c).name);
  const lines = settingsLines(st, ctx);
  const when = madeLine(made, ctx);
  let body;
  if (size === "link") {
    const list = all.slice(0, 7);
    const sx = 36, sw = 470, rx = 548, rw = W - 36 - rx;
    const set = capLines(lines.flatMap(l => wrap(l, sw, 18)), 13);
    const note = wrap(councilLine(r, all.length - list.length), rw, 15);
    body =
      `<rect x="0" y="0" width="${W}" height="8" fill="${C.reader}"/>` +
      text(36, 58, SITE, { fs: 22, family: MONO, fill: C.accent, weight: "700" }) +
      text(W - 36, 58, BANNER, { fs: 20, fill: C.reader, weight: "700", anchor: "end" }) +
      text(36, 90, "Play with the model: seats on the Johannesburg council", { fs: 19 }) +
      text(W - 36, 90, when, { fs: 15, fill: C.ink3, anchor: "end" }) +
      text(sx, 150, "Your settings", { fs: 36, family: SERIF, fill: C.ink, weight: "600" }) +
      set.map((l, k) => text(sx, 188 + k * 26, l, { fs: 18 })).join("") +
      text(rx, 140, "Seats: middle (range)", { fs: 16, fill: C.ink3 }) +
      rows(list, r, party, rx, 156, rw, 44, 21) +
      note.map((l, k) => text(rx, 156 + list.length * 44 + 18 + k * 20, l, { fs: 15, fill: C.ink3 })).join("") +
      `<rect x="0" y="${H - 64}" width="${W}" height="64" fill="${C.paper2}"/>` +
      text(36, H - 26, STAMP, { fs: 18, fill: C.reader }) +
      text(W - 36, H - 26, INVITE, { fs: 18, anchor: "end" });
  } else {
    // Everything ends by FOOT_MAX, clear of the story apps' lower chrome: the
    // settings are capped, and the party rows are as many as then fit (at
    // least MIN_ROWS), the rest counted in the note.
    const FOOT_MAX = 1800, MIN_ROWS = 5, MAX_ROWS = 10;
    const x = 60, w = W - 120;
    const set = capLines(lines.flatMap(l => wrap(l, w, 30)), 10);
    const setY = 330;
    const rowsY = setY + set.length * 42 + 90;
    const tail = 30 + 3 * 32 + 80 + 150;          // note (up to three lines), stamp, invite, date
    const fit = Math.floor((FOOT_MAX - tail - rowsY) / 66);
    const list = all.slice(0, Math.max(MIN_ROWS, Math.min(MAX_ROWS, fit)));
    const note = wrap(councilLine(r, all.length - list.length), w, 24);
    const noteY = rowsY + list.length * 66 + 30;
    const footY = Math.max(noteY + note.length * 32 + 80, 1560);
    body =
      `<rect x="0" y="0" width="${W}" height="14" fill="${C.reader}"/>` +
      text(x, 120, BANNER, { fs: 34, fill: C.reader, weight: "700" }) +
      text(x, 170, SITE, { fs: 36, family: MONO, fill: C.accent, weight: "700" }) +
      text(x, 216, "Play with the model: seats on the Johannesburg council", { fs: 28 }) +
      text(x, 290, "Your settings", { fs: 64, family: SERIF, fill: C.ink, weight: "600" }) +
      set.map((l, k) => text(x, setY + 20 + k * 42, l, { fs: 30 })).join("") +
      text(x, rowsY - 22, "Seats: middle (range)", { fs: 26, fill: C.ink3 }) +
      rows(list, r, party, x, rowsY, w, 66, 32) +
      note.map((l, k) => text(x, noteY + k * 32, l, { fs: 24, fill: C.ink3 })).join("") +
      wrap(STAMP, w, 32).map((l, k) => text(x, footY + k * 42, l, { fs: 32, fill: C.reader })).join("") +
      text(x, footY + 100, INVITE, { fs: 32 }) +
      text(x, footY + 150, when, { fs: 24, fill: C.ink3 });
  }
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">` +
    `<rect width="${W}" height="${H}" fill="${C.paper}"/>${body}</svg>`;
}

// The image's text alternative: the same figures, in the same order.
export function playCardAlt({ r, st, ctx, party, made }) {
  const all = order(r, c => party(c).name);
  const seats = all.map(c => party(c).name + " " + seatText(r.seats[c].median) + " (" + seatText(r.seats[c].p5) + " to " + seatText(r.seats[c].p95) + ")");
  return "Not the forecast: seats on the Johannesburg council under a reader's settings. " + settingsLines(st, ctx).map(l => l.replace(/\.$/, "")).join(". ") + ". Middle seats (range): " +
    seats.join(", ") + ". " + STAMP + " " + madeLine(made, ctx) + ".";
}
