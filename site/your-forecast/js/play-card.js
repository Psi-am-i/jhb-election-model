// "Your forecast", section 1: the words the page and its share image share,
// and what the share image of the model's own forecast says. The image is
// drawn by share-card.js, the one card module of both sections
// (modelCardSVG, from playCardSpec). Once the reader moves a setting, the
// share is section 1's hand-off as a reader's forecast, drawn like section
// 2's (share-card.js forecastSpec, linkCardSVG, storyCardSVG; owner,
// 2026-10-06: a reader who alters the settings gets the reader treatment,
// their name on the card and the forecast sealed), so this module draws the
// untouched page's card only.
//
// ⛔ A LIVE WRITER WITH NO REGION (stats.LIVE_WRITERS["your-forecast/js/play-card.js"]).
// It turns the compute result the page is showing into the card's figures,
// and it reaches no element of the page: play-share.js puts the image into
// the share sheet. Listed so that stats.script_writes holds it to the writer
// contract (no lookup outside a LIVE selector, no markup injection, no data
// block, no data source).
//
// ONE RESULT, TWO VIEWS. Every figure in the card's table, lines and map is
// read from the result object js/model.js rendered (pyboot/page.py's
// compute, through src/reweight.py and render_map.ward_call); nothing here
// computes a seat or colours a ward by its own rule. The party order (order),
// the seat format (seatText) and the words for each setting (cellName,
// settingsWords; the seat laws' names are laws.json's, render_sheet.SEAT_LAWS)
// are defined here once and used by the page as well, so the card cannot
// disagree with the page. The council graphic draws the same middles, with
// the seats they leave over in grey (chamberOf, CHAMBER_NOTE).
//
// NEUTRAL (DESIGN-decided §8): the parties appear in the page's order (middle
// seat count, highest first, ties by name), every one drawn the same way;
// none is marked out, and the card is black and white but for each party's
// chip, its wards and its seats (owner, 2026-10-06).
//
// What the card says (DESIGN §2, "Share card", amended after the critic's
// G1-G3, 2026-10-02, and by the owner, 2026-10-06): "Our Johannesburg
// Forecast", never a reader's name over the model's own forecast (critic G1:
// a name is anyone's text); the name on a "Shared by" line; the council; the
// largest-party line, ties apart; the ward map, which holds the ward seats
// only; the council graphic; and each party's middle seat count, as a bar
// (no range: review 2026-10-02).

import { modelCardSVG, seatOrder, SIZES as CARD_SIZES, SITE, STORY_TEXT_BOTTOM, OTHERS_COLOUR } from "./share-card.js";
import { TRUST, PUBLISHED_CELL, PUBLISHED_LAW, engineSettings, serialize } from "./play-state.js";
import { compose } from "./yf-url.js";

// The two sizes section 1 shares (share-card.js's third is the return card).
export const SIZES = { link: CARD_SIZES.link, story: CARD_SIZES.story };
export { SITE, STORY_TEXT_BOTTOM };
export const INVITE = "Try your own at " + SITE + "/your-forecast";
export const PUBLISHED_STAMP = "The model's published forecast.";
export const HOW = "Wards in the colour of their most likely winner, striped where contested.";
export const MAP_NOTE = "ward seats; the council's other seats are filled from party lists.";
export const BARS_NOTE = "Each party's middle seat count across the simulations. The middles need not add up to the council's size.";
export const CHAMBER_NOTE = "Each party at its middle seat count; grey seats are too close to call.";
export const MODEL_TITLE = "Our Johannesburg Forecast";

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
  // the law's name as /forecast prints it (laws.json, render_sheet.SEAT_LAWS)
  if (st.law !== PUBLISHED_LAW) out.push("seated under " + ((ctx.laws_text || {})[st.law]?.label || st.law));
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

// The headline of the model's own card (owner, 2026-10-06). A reader's name
// goes on a "Shared by" line under it, never into it (critic G1).
export const headline = () => MODEL_TITLE;
export const sharedBy = name => "Shared by " + name;

// The two parties most often alone with the most seats, in alphabetical
// order, as the page's one-line result names them.
export function largestTop(r, party) {
  return Object.keys(r.largest).sort((a, b) => r.largest[b].p - r.largest[a].p).slice(0, 2)
    .sort((a, b) => party(a).name.toLowerCase().localeCompare(party(b).name.toLowerCase()));
}
// The largest-party line, in the shares' own text (page.py, reweight.chance_text),
// in the site's one wording for it (section 1's line and its published twin):
// "Most seats: 47% chance it's the ANC, …" (STYLE rule 10: a chance,
// never "of simulations"). `cap` starts a name with a capital, as a sentence.
export const theName = (c, party, cap = false) => {
  const s = party(c).article + party(c).name;
  return cap ? s.charAt(0).toUpperCase() + s.slice(1) : s;
};
export function largestLine(r, party) {
  const [a, b] = largestTop(r, party);
  return "Most seats: " + r.largest[a].text + " chance it's " + theName(a, party) + ", " +
    r.largest[b].text + " chance it's " + theName(b, party) + ". Two or more parties tie for the most seats: " +
    r.tied.text + " chance.";
}

// The council line: the council, the day, its size and its majority.
export function councilLine({ r, when }) {
  return "Johannesburg council" + (when ? ", " + when : "") + " · " + seatText({ value: r.council }) +
    " seats, " + seatText({ value: r.majority }) + " for a majority";
}

// The foot under the card: whose figures these are, how the map reads, where
// to try one's own, and when the card was made.
export function footText({ made }) {
  return PUBLISHED_STAMP + " " + HOW + " " + INVITE + ". " + madeLine(made) + ".";
}

// The council graphic of the model's card, as share-card.js's council
// graphic takes it: each party at its middle seat count, the figure the table
// beside it shows, and the seats the middles leave over as one grey block,
// "too close to call" (owner, 2026-10-06: the graphic must not disagree with
// the forecast). The middles come from different simulations, so they need
// not fill the council; a withheld middle seats nothing, and a middle that
// falls between two seat counts is drawn at the nearer whole seat. Every seat
// is drawn solid: a middle has no ward and list split. Refuses middles that
// add up to more than the council.
export const UNCALLED_COLOUR = "#b4b9b4";
export function chamberOf(r, party, { council, majority }) {
  const codes = [...order(r, c => party(c).name), "OTHERS"];
  const rows = codes.map(c => {
    const m = r.seats[c].median;
    return { code: c, colour: c === "OTHERS" ? OTHERS_COLOUR : party(c).colour, ward: m.withheld ? 0 : Math.round(m.value), pr: 0 };
  }).filter(x => x.ward > 0);
  const seated = rows.reduce((a, x) => a + x.ward, 0);
  if (seated > council) throw new Error("the middles seat " + seated + " of the council's " + council);
  if (seated < council) rows.push({ code: "UNCALLED", colour: UNCALLED_COLOUR, ward: council - seated, pr: 0 });
  return { rows, council, majority, coalition: [], top: [] };
}

// The model's card for one result: the untouched page's. `r` is the compute
// result the page shows; `party(code)` -> {name, colour, logo}; `made` the
// date it was made; `name` the reader's name or label; `geometry` the ward
// boundaries with the stripe tile (`step`, `rotate`); `when` the election day
// in words. Every card carries the council graphic (owner, 2026-10-06),
// drawn from the result's own middles (chamberOf).
export function playCardSpec({ r, party, made, name, geometry, when, touched = false }) {
  if (touched) throw new Error("a moved setting is shared as the reader's forecast, not on the model's card");
  if (!r || r.refused) throw new Error("the card needs a computed result, not a refusal");
  if (!geometry) throw new Error("the card needs the ward boundaries");
  const codes = [...order(r, c => party(c).name), "OTHERS"];
  // exact rows, the middle only: a bar from zero to it (none when withheld)
  const rows = codes.map(c => {
    const s = r.seats[c], other = c === "OTHERS";
    return { code: other ? null : c, others: other, name: other ? "Others" : party(c).name, colour: other ? OTHERS_COLOUR : party(c).colour,
             logo: !other && !!party(c).logo, value: seatText(s.median), n: s.median.withheld ? null : s.median.value };
  });
  const wards = r.wards.filter(w => geometry.paths[w.ward])
    .map(w => ({ path: geometry.paths[w.ward], fill: w.fill, bands: w.bands }));
  return {
    title: MODEL_TITLE,
    lines: [{ text: sharedBy(name), tone: "muted" }, { text: councilLine({ r, when }), tone: "muted" },
            { text: largestLine(r, party), tone: "plain" }],
    map: { W: geometry.W, H: geometry.H, step: geometry.step, rotate: geometry.rotate, wards },
    mapNote: r.wards.length + " " + MAP_NOTE,
    chamber: chamberOf(r, party, r), chamberNote: CHAMBER_NOTE,
    rows, rowsNote: BARS_NOTE,
    foot: [footText({ made })],
  };
}
// The card at `size` ("link" or "story"); `assets` as share-card.js takes
// them (fonts, the site's logo, the parties' logos).
export const buildPlayCardSVG = info => modelCardSVG(playCardSpec(info), info.assets || {}, info.size || "link");

// The image's text alternative: the same figures, in the same order.
export function playCardAlt({ r, party, made, name, when }) {
  const codes = [...order(r, c => party(c).name), "OTHERS"];
  const seats = codes.map(c => (c === "OTHERS" ? "Others" : party(c).name) + " " + seatText(r.seats[c].median));
  return MODEL_TITLE + ". " + sharedBy(name) + ". " + councilLine({ r, when }) + ". " +
    largestLine(r, party) + " Middle seats: " + seats.join(", ") + ". " + CHAMBER_NOTE + " " + footText({ made });
}

// ---------- what section 1's share sheet seals and links ----------

// Why a moved setting's forecast cannot be sealed when "Break the model"
// never loaded, so nothing can work the forecast out.
export const NO_HANDOFF = "this page could not load Make your own prediction, which works your prediction out";

// Section 1's content for the one share sheet (share-sheet.js), apart from
// the page. `get`: { now() (what the page shows: { st, ctx, touched }),
// name() (yf-url.js sealName: the one name source), handoff() (make.js's
// provider, or null), page() ({ pathname, href }), changed() (a forecast
// arrived or failed: redraw) }. Returns:
//   ask()     work out the forecast for the settings shown, once per setting
//   ready()   that forecast's record { key, forecast, failed }, or null
//   fields()  null untouched (the model's forecast is never sealed);
//             undefined while the forecast is being worked out; { failed:
//             reason } when it cannot be; else { v, c, f, n } to seal
//   link()    the page's address: section 1's settings, and once moved the
//             forecast's part and the name, the same name as fields()
//   retry()   forget a failure, so the next ask() tries again
export function section1Share(get) {
  let mine = null;
  const keyNow = () => JSON.stringify(engineSettings(get.now().st));
  function ask() {
    const now = get.now(), h = get.handoff();
    if (!now.touched || !h) return;
    const key = keyNow();
    if (mine && mine.key === key) return;
    const asked = mine = { key, forecast: null, failed: null };
    h.forecast(engineSettings(now.st)).then(F => { if (mine === asked) { asked.forecast = F; get.changed(); } },
      e => { if (mine === asked) { asked.failed = String((e && e.message) || e); get.changed(); } });
  }
  const ready = () => (get.now().touched && mine && mine.key === keyNow() ? mine : null);
  function fields() {
    if (!get.now().touched) return null;
    if (!get.handoff()) return { failed: NO_HANDOFF };
    const m = ready();
    if (!m || (!m.forecast && !m.failed)) return undefined;
    if (m.failed) return { failed: m.failed };
    return { ...m.forecast.fields, n: get.name() };
  }
  function link() {
    const now = get.now(), m = ready(), page = get.page();
    const brk = m && m.forecast ? "?" + new URLSearchParams(m.forecast.fields).toString() : "";
    return new URL(page.pathname + compose(serialize(now.st, now.ctx), brk, brk ? get.name() : "") + (brk ? "#break" : "#adjust"), page.href).href;
  }
  function retry() { if (mine && mine.failed) mine = null; }
  return { ask, ready, fields, link, retry };
}
