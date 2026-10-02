// "Play with the model": what the share image of a reader's settings says,
// and the words the page and the image share. The image itself is drawn by
// forecast-card.js, the one card module /play/ and /make/ share
// (playCardSpec hands it this page's headline, lines, map and rows).
//
// ⛔ A LIVE WRITER WITH NO REGION (stats.LIVE_WRITERS["play/js/play-card.js"]).
// It turns the compute result the page is showing into the card's figures,
// and it reaches no element of the page: play-share.js puts the image into
// the share sheet. Listed so that stats.script_writes holds it to the writer
// contract (no lookup outside a LIVE selector, no markup injection, no data
// block, no data source).
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
// What the card says (DESIGN §2, "Share card", amended after the critic's
// G1-G3, 2026-10-02): a headline that says whose figures these are (the
// model's published forecast, or a reader's settings on the model, never
// "{name}'s Election Forecast": a name is anyone's text, and the site would
// print it over its own forecast); the largest-party line, ties apart;
// a line saying the map holds the ward seats only; and each party's middle
// seat count, as a bar (no range: review 2026-10-02). "Not the model's
// forecast" sits in the foot, in the small type, as on /make/'s card.

import { buildForecastCardSVG, SIZES, SITE, STORY_TEXT_BOTTOM, OTHERS_COLOUR } from "./forecast-card.js";
import { TRUST, PUBLISHED_CELL, PUBLISHED_LAW } from "./play-state.js";

export { SIZES, SITE, STORY_TEXT_BOTTOM };
export const INVITE = "Try your own at " + SITE + "/play";
export const READER_STAMP = "Not the model's forecast: a reader's settings on its simulations.";
export const PUBLISHED_STAMP = "The model's published forecast.";
export const HOW = "Wards in the colour of their most likely winner, striped where contested.";
export const MAP_NOTE = "ward seats; the council's other seats are filled from party lists.";
export const BARS_NOTE = "Each party's middle seat count across the simulations. The middles need not add up to the council's size.";

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

// The range holding nine in ten of a party's simulations, as printed.
export const rangeText = s => (s.p5.withheld || s.p95.withheld ? "withheld" : seatText(s.p5) + "–" + seatText(s.p95));

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

// When the card was made: a card outlives the forecast it was drawn from
// (critic S1). `made` is the date the page passes in, ISO 8601, printed as
// the pages print dates ("2 October 2026"). The model version stays in the
// link (`mv`), not on the image: it is an internal identifier (review
// 2026-10-02).
const MONTHS = "January February March April May June July August September October November December".split(" ");
export function madeLine(made) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(String(made))) throw new Error("the card needs the date it was made, YYYY-MM-DD");
  const [y, m, d] = made.split("-").map(Number);
  return "Made " + d + " " + MONTHS[m - 1] + " " + y;
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
// The largest-party line, in the shares' own text (page.py, reweight.chance_text),
// in the site's one wording for it (/forecast, home, /play/): "X alone has the
// most seats in …". `cap` starts it with a capital, as a sentence.
export const theName = (c, party, cap = false) => {
  const s = party(c).article + party(c).name;
  return cap ? s.charAt(0).toUpperCase() + s.slice(1) : s;
};
export function largestLine(r, party) {
  const [a, b] = largestTop(r, party);
  return theName(a, party, true) + " alone has the most seats in " + r.largest[a].text + " of simulations, " +
    theName(b, party) + " alone in " + r.largest[b].text + ". Two or more parties tie for the most seats in " + r.tied.text + ".";
}

// The line under the headline: whose figures these are, then the council.
export function councilLine({ r, when }) {
  return "Johannesburg council" + (when ? ", " + when : "") + " · " + seatText({ value: r.council }) +
    " seats, " + seatText({ value: r.majority }) + " for a majority";
}
export function subLine({ r, when }) {
  return councilLine({ r, when });
}

// The foot under the card, in sentences: whose figures these are first.
export function footText({ st, ctx, made }) {
  const words = st && isMoved(st) ? settingsWords(st, ctx) : [];
  const said = words.length ? READER_STAMP + " Settings: " + words.join("; ") + "; everything else as published." : PUBLISHED_STAMP;
  return said + " " + HOW + " " + INVITE + ". " + madeLine(made) + ".";
}
const isMoved = st => st.shift.some(x => x !== 0) || (st.trust > 0 && st.polls.length > 0) || st.law !== PUBLISHED_LAW || st.cell !== PUBLISHED_CELL;

// The card for one result, drawn by forecast-card.js (the one card module,
// shared with /make/). `r` is the compute result the page shows (the
// published one when nothing is moved); `st`/`ctx` the settings that produced
// it; `party(code)` -> {name, colour}; `made` the date it was made; `name` the
// reader's name or label; `geometry` the ward boundaries with the stripe tile
// (`step`, `rotate`); `when` the election day in words; `photo` false when
// share.jpg will not be drawn under it.
export function playCardSpec({ r, st, ctx, party, made, name, geometry, when, touched, size = "link", photo = true }) {
  if (!r || r.refused) throw new Error("the card needs a computed result, not a refusal");
  if (!geometry) throw new Error("the card needs the ward boundaries");
  const codes = [...order(r, c => party(c).name), "OTHERS"];
  // exact rows, the middle only: a bar from zero to it (none when withheld)
  const rows = codes.map(c => {
    const s = r.seats[c];
    return { label: c === "OTHERS" ? "Others" : party(c).name, colour: c === "OTHERS" ? OTHERS_COLOUR : party(c).colour,
             value: seatText(s.median), n: s.median.withheld ? null : s.median.value };
  });
  const wards = r.wards.filter(w => geometry.paths[w.ward])
    .map(w => ({ path: geometry.paths[w.ward], fill: w.fill, bands: w.bands }));
  return {
    size, photo,
    title: headline(name, touched),
    lines: [...(touched ? [] : [{ text: sharedBy(name), tone: "muted" }]),
            { text: councilLine({ r, when }), tone: "muted" },
            { text: largestLine(r, party), tone: "plain" }],
    map: { W: geometry.W, H: geometry.H, step: geometry.step, rotate: geometry.rotate, wards },
    mapNote: r.wards.length + " " + MAP_NOTE,
    rows, rowsNote: BARS_NOTE,
    foot: [footText({ r, st, ctx, made })],
  };
}
export const buildPlayCardSVG = info => buildForecastCardSVG(playCardSpec(info));

// The image's text alternative: the same figures, in the same order.
export function playCardAlt({ r, st, ctx, party, made, name, when, touched }) {
  const codes = [...order(r, c => party(c).name), "OTHERS"];
  const seats = codes.map(c => (c === "OTHERS" ? "Others" : party(c).name) + " " + seatText(r.seats[c].median));
  return headline(name, touched) + ". " + (touched ? "" : sharedBy(name) + ". ") + subLine({ r, when }) + ". " +
    largestLine(r, party) + " Middle seats: " + seats.join(", ") + ". " + footText({ st, ctx, made });
}
