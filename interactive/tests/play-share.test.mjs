// "Your forecast", section 1: anonymous save, and the model's share card.
//
//   node --test interactive/tests/
//
// 1. A link round-trips: every case the native harness computes
//    (play-settings.json), written to a link and read back, asks the engine
//    for exactly the settings it started from. page.py's compute is a pure
//    function of those settings (page.test.mjs holds native and Pyodide to one
//    fixture), so the link reproduces the same figures.
// 2. A broken link falls back to the published setting and says so.
// 3. The model's card (the untouched page's: a moved setting is shared as the
//    reader's forecast, drawn by share-card.js like section 2's, owner
//    2026-10-06) is drawn from the compute result the page shows: each
//    party's row carries that party's middle seat count and no range (review
//    2026-10-02), every other digit comes from the result's totals, its
//    largest-party shares, its ward count, the election day, the date the
//    card was made or the reader's name (drawn as text, never markup), every
//    ward is drawn in the result's colour, the parties are in the page's
//    order, and a figure typed into the card, or a result the card ignored,
//    is caught (and the check goes quiet again).
// 4. The card says whose figures these are: "Our Johannesburg Forecast",
//    the name only on a "Shared by" line (critic G1), the published stamp in
//    the foot; it is black and white, carries the site's logo, no photograph
//    and no canvas-drawn site name (owner, 2026-10-06).
// 5. It uses the canvas: at both sizes the map is drawn at least the stated
//    share of the card's width, and on the story card the words reach to
//    within STORY_FILL_SLACK of STORY_TEXT_BOTTOM and never past it; a card
//    shrunk or cut short is caught.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import * as PS from "../js/play-state.js";
import * as SC from "../js/share-card.js";
import { buildPlayCardSVG, order, seatText, settingsWords, playCardAlt, madeLine, headline, sharedBy, largestLine,
         rangeText, councilLine, chamberOf, PUBLISHED_STAMP, CHAMBER_NOTE, MODEL_TITLE, STORY_TEXT_BOTTOM, SIZES, SITE } from "../js/play-card.js";

const here = dirname(fileURLToPath(import.meta.url));
const FIXTURE = JSON.parse(readFileSync(resolve(here, "native-play.json"), "utf8"));
const CASES = JSON.parse(readFileSync(resolve(here, "play-settings.json"), "utf8")).cases;
const INDEX = JSON.parse(readFileSync(resolve(here, "../../site/draws/index.json"), "utf8"));

const ctx = {
  pools: ["Black African", "Coloured", "Indian/Asian", "White"],
  polls: INDEX.polls.map(p => p.id), pollRows: INDEX.polls,
  laws: ["deduct", "expand", "level", "cap"],
  cells: INDEX.cells.map(c => c.path), cellRows: INDEX.cells,
  modelVersion: INDEX.cells[0].model_sha256,
};
const toState = s => ({ shift: s.shift.slice(), polls: s.polls === "*" ? ctx.polls.slice() : s.polls.slice(),
                        trust: Math.round(s.trust * 100), law: s.law, cell: s.cell });
const engine = s => ({ ...s, polls: s.polls === "*" ? ctx.polls.slice() : s.polls });

test("every harness case survives a link, and the engine is asked for the same settings", () => {
  assert.ok(CASES.length >= 5, "the harness has cases");
  let touched = 0;
  for (const c of CASES) {
    const st = toState(c.settings);
    if (st.polls.length > 1) {
      // a harness case with two polls: no control can make it (one poll at a
      // time), and a link to it is refused back to no poll
      assert.equal(PS.parse(PS.serialize(st, ctx), ctx).dropped.length, 1, c.name);
      continue;
    }
    if (st.shift.some(x => x < PS.TURNOUT.min || x > PS.TURNOUT.max)) {
      // a harness case past the controls' bounds: no control can make it, and a
      // link to it is refused back to the published turnout
      assert.equal(PS.parse(PS.serialize(st, ctx), ctx).dropped.length, 1, c.name);
      continue;
    }
    const link = PS.serialize(st, ctx);
    const back = PS.parse(link, ctx);
    assert.deepEqual(back.dropped, [], c.name);
    assert.equal(back.otherVersion, null, c.name);
    assert.deepEqual(PS.engineSettings(back.state), engine(c.settings), c.name);
    if (link) { touched++; assert.ok(link.length < 120, `${c.name}: ${link}`); assert.ok(!link.includes("%2C"), link); }
  }
  assert.ok(touched >= 3);
});

test("a link from another model version is applied and flagged; the same version is not", () => {
  const link = PS.serialize({ ...PS.defaults(ctx), shift: [1, 0, 0, 0] }, ctx);
  assert.equal(PS.parse(link, ctx).otherVersion, null);
  assert.equal(PS.parse(link.replace(/mv=[0-9a-f]+/, "mv=000000000000"), ctx).otherVersion, "000000000000");
});

test("a broken link falls back to the published setting, field by field, and says why", () => {
  const r = PS.parse("?t=9,0,0,0&k=7&l=nope&b=zz&p=" + ctx.polls[0], ctx);
  assert.deepEqual(r.state.shift, [0, 0, 0, 0]);
  assert.equal(r.state.trust, 0);
  assert.equal(r.state.law, "deduct");
  assert.equal(r.state.cell, ".");
  assert.deepEqual(r.state.polls, [ctx.polls[0]]);
  assert.equal(r.dropped.length, 4);
  assert.equal(PS.isTouched(r.state), false);
});

// ---------- 3. the card ----------
const ROSTER = new Proxy({}, { get: (_, c) => ({ code: c, name: String(c).replace(/_/g, " "), colour: "#888888", article: "", logo: false }) });
// the fixture predates no field the card reads: every share carries its text
const party = c => ROSTER[c];
const textOf = svg => [...svg.matchAll(/<text\b[^>]*>([^<]*)<\/text>/g)].map(m => m[1]);
const runs = s => (s.replace(/[   ]/g, "").match(/\d+(?:\.\d+)?/g) || []);
const unesc = s => s.replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&amp;/g, "&");
const BRAND = SC.brandOf(readFileSync(resolve(here, "../../site/logo.svg"), "utf8"));
const ASSETS = { logos: {}, brand: BRAND };

const MADE = "2026-10-01";
const WHEN = "4 November 2026";
// Constructed boundaries, one square per ward the result carries: the card's
// map is checked against the result, not against a file on this machine.
const geometryFor = r => ({ W: 100, H: 50, step: 7, rotate: 45, places: [],
  paths: Object.fromEntries(r.wards.map((w, i) => [w.ward, `M${i} 0L${i + 1} 0L${i + 1} 1Z`])) });
// A constructed start for the council graphic: each ward to the result's
// winner, and the council's other seats to the parties in the page's order,
// one at a time, so the seats are the council's and no party has fewer seats
// than wards.
function startFor(r) {
  const ward_calls = r.wards.map(w => w.winner), seats = {};
  for (const c of ward_calls) seats[c] = (seats[c] || 0) + 1;
  const codes = order(r, c => party(c).name);
  for (let k = ward_calls.length; k < r.council; k++) { const c = codes[k % codes.length]; seats[c] = (seats[c] || 0) + 1; }
  return { ward_calls, seats };
}
const card = (c, extra = {}) => {
  const r = extra.r ?? c.result;
  return { r, party, made: MADE, when: WHEN, name: "reader-7", geometry: geometryFor(r), start: startFor(r), assets: ASSETS, ...extra };
};

// The digit runs the card may print outside the seat rows: the result's
// council and majority, its largest-party shares, its ward count, the made
// line, the election day and the reader's name. No seat figure is here: a
// row's figure is checked against its own party.
function allowed(info) {
  const out = new Set();
  const add = x => runs(String(x)).forEach(d => out.add(d));
  add(councilLine(info)); add(largestLine(info.r, party)); add(info.r.wards.length);
  add(madeLine(MADE)); add(WHEN); add(info.name);
  return out;
}
// What the card prints that it should not: a row whose figure is not that
// party's middle, rows out of the page's order, and any other digit run.
function typed(svg, info) {
  const r = info.r, ts = textOf(svg).map(unesc), ok = allowed(info), bad = [], rowTexts = new Set();
  const want = [...order(r, c => party(c).name), "OTHERS"];
  const label = c => (c === "OTHERS" ? "Others" : party(c).name);
  // a row's name is the party's name, or that name cut to fit and ended "…"
  const isName = (t, nm) => t === nm || (t.endsWith("…") && t.length > 1 && nm.startsWith(t.slice(0, -1)));
  let drawn = 0;
  ts.forEach((t, i) => {
    if (!want.some(c => isName(t, label(c)))) return;
    const c = want[drawn++];
    rowTexts.add(i + 1);
    if (!c || !isName(t, label(c))) bad.push(`row ${drawn} is "${t}", not ${c && label(c)}`);
    else if (ts[i + 1] !== seatText(r.seats[c].median)) bad.push(`${t}'s row reads "${ts[i + 1]}", not "${seatText(r.seats[c].median)}"`);
  });
  if (drawn !== want.length) bad.push(`${drawn} rows drawn, ${want.length} shown`);
  ts.forEach((t, i) => { if (!rowTexts.has(i)) for (const d of runs(t)) if (!ok.has(d)) bad.push(`${d} in "${t}"`); });
  return bad;
}
// The map's group: the paths inside it (one fill per ward, one stripe layer
// per contested ward) and its drawn box. The logo's paths are outside it.
function mapOf(svg, geometry) {
  const m = /<g transform="translate\(([\d.]+) ([\d.]+)\) scale\(([\d.]+)\)">([\s\S]*?)<\/g>/.exec(svg);
  if (!m) return null;
  return { x: +m[1], y: +m[2], w: geometry.W * m[3], h: geometry.H * m[3], paths: (m[4].match(/<path d="M/g) || []).length };
}
const baselines = svg => [...svg.matchAll(/<text x="[\d.-]+" y="([\d.-]+)"/g)].map(m => +m[1]);

// The model's card is drawn for every computed result (the mechanism), and
// shared only for the untouched page's.
const results = FIXTURE.cases.filter(c => c.result && !c.result.refused);
const untouched = FIXTURE.cases.find(c => c.name === "untouched");
const moved = results.filter(c => c.name !== "untouched");

test("the card's figures are the result's, in the page's order, at both sizes", () => {
  assert.ok(moved.length >= 3, "the fixture has computed cases");
  for (const c of results) {
    for (const size of Object.keys(SIZES)) {
      const info = { ...card(c), size };
      const svg = buildPlayCardSVG(info);
      assert.match(svg, new RegExp(`width="${SIZES[size][0]}" height="${SIZES[size][1]}"`));
      assert.deepEqual(typed(svg, info), [], `${c.name} ${size}`);
      // whose figures these are: the model's forecast, the name only as "Shared by"
      const lines = textOf(svg).map(unesc);
      const all = lines.join(" ");
      assert.equal(lines[0], MODEL_TITLE, `${c.name} ${size}: headline`);
      assert.equal(headline("reader-7"), MODEL_TITLE);
      assert.ok(!lines[0].includes("reader-7"), `${c.name} ${size}: the name is not the model's headline`);
      assert.ok(lines.slice(0, 3).includes(sharedBy("reader-7")), `${c.name} ${size}: shared by`);
      assert.ok(all.includes(PUBLISHED_STAMP), `${c.name} ${size}: stamp`);
      assert.ok(!/election forecast/i.test(all), `${c.name} ${size}`);
      // the largest-party line, ties apart, in the result's own text
      assert.ok(all.includes(largestLine(info.r, party)), `${c.name} ${size}: largest`);
      assert.ok(all.includes(info.r.tied.text), `${c.name} ${size}: ties`);
      // every ward the result carries is drawn, in the result's colour, with
      // its stripes where contested
      const map = mapOf(svg, info.geometry);
      for (const w of info.r.wards.slice(0, 20)) assert.ok(svg.includes(`fill="${w.fill}"`), w.ward);
      assert.equal(map.paths, info.r.wards.length + info.r.wards.filter(w => w.bands).length, `${c.name} ${size}: one fill and one stripe layer per ward`);
      // the council graphic: one square per seat of the start
      assert.ok(all.includes(info.r.majority + " for a majority"), `${c.name} ${size}: the council graphic's majority`);
      // nothing runs off the card, and the story stays clear of the apps' lower chrome
      const ys = baselines(svg);
      assert.ok(Math.max(...ys) <= (size === "story" ? STORY_TEXT_BOTTOM : SIZES[size][1] - 10), `${c.name} ${size}: text at y ${Math.max(...ys)}`);
      assert.ok(Math.min(...ys) > 0, `${c.name} ${size}: text above the card`);
    }
    const alt = playCardAlt(card(c));
    assert.ok(alt.startsWith(MODEL_TITLE + ". " + sharedBy("reader-7")));
    assert.ok(alt.includes(largestLine(c.result, party)) && alt.includes(CHAMBER_NOTE));
    for (const p of c.result.shown) assert.ok(!alt.includes(rangeText(c.result.seats[p])), `${c.name}: ${p}'s range in the alt`);
  }
});

test("a name never heads the model's forecast, and a moved setting draws no model's card", () => {
  // critic G1: "The IEC's Election Forecast" printed over the model's own figures
  const lines = textOf(buildPlayCardSVG(card(untouched, { name: "The IEC" }))).map(unesc);
  assert.equal(lines[0], MODEL_TITLE);
  assert.ok(lines.includes(sharedBy("The IEC")));
  assert.ok(!lines.some(l => /IEC's/.test(l)), lines.join(" | "));
  // a moved setting is the reader's forecast, sealed (share-card.js): never this card
  assert.throws(() => buildPlayCardSVG(card(moved[0], { touched: true })), /reader's forecast/);
});

test("the reader's name is drawn as text, never as markup", () => {
  const svg = buildPlayCardSVG(card(untouched, { name: "<image href=x onerror=alert(1)>" }));
  assert.ok(!svg.includes("<image href=x"), "the name was injected as markup");
  assert.ok(svg.includes("&lt;image href=x"));
});

test("a typed figure, or a result the card did not read, is caught; reverted, quiet", () => {
  const c = moved[0];
  const info = card(c, { r: JSON.parse(JSON.stringify(c.result)) });
  const svg = buildPlayCardSVG(info);
  assert.deepEqual(typed(svg, info), []);
  const forged = svg.replace("</svg>", "<text x=\"1\" y=\"1\">The DA wins 4321 seats</text></svg>");
  assert.deepEqual(typed(forged, info), ['4321 in "The DA wins 4321 seats"']);
  // two parties' figures swapped is caught
  const [a, b] = order(info.r, p => party(p).name).filter((p, i, xs) => seatText(info.r.seats[p].median) !== seatText(info.r.seats[xs[0]].median) || i === 0);
  const fa = seatText(info.r.seats[a].median), fb = seatText(info.r.seats[b].median);
  assert.notEqual(fa, fb);
  const swapped = svg.replace(`>${fa}<`, ">@A@<").replace(`>${fb}<`, `>${fa}<`).replace(">@A@<", `>${fb}<`);
  assert.ok(typed(swapped, info).length >= 2, "swapped rows");
  assert.deepEqual(typed(svg, info), []);
  // no range is drawn, and one added is caught as a typed figure
  for (const p of info.r.shown) assert.ok(!textOf(svg).includes(rangeText(info.r.seats[p])), p);
  const ranged = svg.replace("</svg>", `<text x="1" y="1">${rangeText(info.r.seats[a])}</text></svg>`);
  assert.ok(typed(ranged, info).length > 0, "an added range is caught");
  // the card reads the result: change the top party's middle and the card moves with it
  const top = order(info.r, p => party(p).name)[0];
  info.r.seats[top].median.value = 987.6;
  const again = buildPlayCardSVG(info);
  assert.ok(textOf(again).includes("987.6"));
  assert.ok(typed(again, card(c)).length > 0);
  assert.deepEqual(typed(again, info), []);
});

test("a withheld figure is printed as withheld; a refusal, no date or no map draws no card", () => {
  const c = moved[0];
  const info = card(c, { r: JSON.parse(JSON.stringify(c.result)) });
  const top = order(info.r, p => party(p).name)[0];
  info.r.seats[top].median = { ...info.r.seats[top].median, withheld: true };
  assert.ok(textOf(buildPlayCardSVG(info)).includes("withheld"));
  assert.throws(() => buildPlayCardSVG({ ...info, r: { refused: "too few" } }));
  assert.throws(() => buildPlayCardSVG({ ...info, made: undefined }));
  assert.throws(() => buildPlayCardSVG({ ...info, geometry: null }));
});

test("the council graphic is the start's seats, ward seats from its calls; a start that is not the council is refused", () => {
  const r = untouched.result, start = startFor(r);
  const ch = chamberOf(start, party, r);
  assert.equal(ch.rows.reduce((a, x) => a + x.ward + x.pr, 0), r.council);
  for (const x of ch.rows) assert.equal(x.ward, start.ward_calls.filter(c => c === x.code).length, x.code);
  assert.ok(ch.rows.every(x => x.pr >= 0));
  const L = SC.councilLayout(ch);
  assert.equal(L.cells.length, r.council);
  // it can see: one seat short is refused
  const short = { ...start, seats: { ...start.seats, [ch.rows[0].code]: start.seats[ch.rows[0].code] - 1 } };
  assert.throws(() => chamberOf(short, party, r), /seats/);
  // no start, no graphic and no note
  assert.ok(!buildPlayCardSVG(card(untouched, { start: null })).includes(r.majority + " for a majority"));
});

test("the model's card is black and white, carries the logo, and no photograph or canvas-drawn name", () => {
  // a band across the top of the card in some colour: the reader's card has
  // one (the largest party's), the model's has none
  const bands = (svg, W) => [...svg.matchAll(new RegExp(`<rect x="0" y="0" width="([\\d.]+)" height="([\\d.]+)" fill="([^"]+)"`, "g"))]
    .filter(m => Number(m[2]) < SIZES.story[1] && Number(m[2]) < 700 && Number(m[1]) > W / 4);
  for (const size of Object.keys(SIZES)) {
    const [W] = SIZES[size];
    const svg = buildPlayCardSVG({ ...card(untouched), size });
    assert.deepEqual(bands(svg, W).filter(m => Number(m[2]) !== SIZES[size][1]), [], size + ": a coloured band");
    // the bars are in the card's ink, not a party's colour
    const bars = [...svg.matchAll(/fill="([^"]+)" rx="2"\/>/g)].map(m => m[1]);
    assert.ok(bars.length >= untouched.result.shown.length, size + ": the bars");
    assert.equal(new Set(bars).size, 1, size + ": bars in more than one colour");
    assert.ok(!bars.includes(party("ANC").colour), size + ": a bar in a party's colour");
    // the logo, at its own proportions, inside the card
    const m = new RegExp(`<svg x="([\\d.]+)" y="([\\d.]+)" width="([\\d.]+)" height="([\\d.]+)" viewBox="${BRAND.viewBox}"`).exec(svg);
    assert.ok(m, size + ": the logo");
    assert.ok(Number(m[1]) + Number(m[3]) <= W && Number(m[2]) >= 0, size + ": the logo runs off the card");
    // no photograph, no image of the site's name: everything is in the SVG
    assert.ok(!/share\.jpg|mark\.svg/.test(svg), size);
  }
  // it can see: the reader's card's band is caught
  const F = JSON.parse(readFileSync(resolve(here, "share-fixture.json"), "utf8"));
  const fp = c => F.parties[c];
  const A = SC.forecastSpec({ name: "A", answer: F.A.answer, outcome: F.A.answer.outcome, vote: F.A.vote, calls: F.A.calls,
    party: fp, baseline: F.baseline, election: F.election });
  assert.ok(bands(SC.linkCardSVG(A, ASSETS, fp), SIZES.link[0]).some(m => Number(m[2]) === SC.LINK_BAND));
  // the sheet hands svgToPNG nothing to draw under or over the card
  const sheet = readFileSync(resolve(here, "../js/play-share.js"), "utf8") + readFileSync(resolve(here, "../js/share-sheet.js"), "utf8");
  assert.ok(!/photoUnder|siteLabel|PHOTO_FILE|MARK_FILE|share\.jpg/.test(sheet));
  const text = readFileSync(resolve(here, "../js/card-text.js"), "utf8");
  assert.ok(!/drawLabel|under\.src/.test(text), "card-text.js still draws a photograph or a label");
});

// The space a card uses: its map's drawn width and its lowest baseline.
const space = (svg, geometry) => ({ mapW: (mapOf(svg, geometry) || { w: 0 }).w, lowest: Math.max(...baselines(svg)) });
const fills = (sp, size) => {
  const [W] = SIZES[size], out = [];
  const least = (size === "story" ? SC.STORY_MAP_MIN_SHARE : SC.LINK_MAP_MIN_SHARE) * W;
  if (!(sp.mapW >= least)) out.push(`the map is ${sp.mapW.toFixed(0)} px wide, under ${least.toFixed(0)}`);
  if (size === "story" && !(sp.lowest >= STORY_TEXT_BOTTOM - SC.STORY_FILL_SLACK && sp.lowest <= STORY_TEXT_BOTTOM))
    out.push(`the lowest words sit at ${sp.lowest}, not within ${SC.STORY_FILL_SLACK} px above ${STORY_TEXT_BOTTOM}`);
  return out;
};

test("the card uses the canvas: a wide map, and the story's words down to the apps' band", () => {
  for (const c of results) {
    for (const size of Object.keys(SIZES)) {
      const info = { ...card(c), size };
      assert.deepEqual(fills(space(buildPlayCardSVG(info), info.geometry), size), [], `${c.name} ${size}`);
    }
  }
  // it can see: a map drawn at half the scale, and a story cut short
  const info = { ...card(untouched), size: "story" };
  const svg = buildPlayCardSVG(info);
  const small = svg.replace(/(<g transform="translate\([\d.]+ [\d.]+\) scale\()([\d.]+)/, (m, a, k) => a + (k / 2).toFixed(4));
  assert.equal(fills(space(small, info.geometry), "story").length, 1, "a half-size map");
  const cut = svg.replace(/<text x="[\d.]+" y="(1[5-6]\d\d(?:\.\d)?)"[^>]*>[^<]*<\/text>/g, "");
  assert.ok(fills(space(cut, info.geometry), "story").some(w => w.startsWith("the lowest")), "a foot cut short");
  assert.deepEqual(fills(space(svg, info.geometry), "story"), []);
});

test("the reader's settings in words name every moved setting and nothing else", () => {
  const d = { ...PS.defaults(ctx) };
  assert.deepEqual(settingsWords(d, ctx), []);
  const poll = ctx.pollRows[0];
  const words = settingsWords({ ...d, shift: [5, 0, 0, -0.5], polls: [poll.id], trust: 30, cell: ctx.cellRows.find(c => c.w_bye === 1).path, law: "cap" }, ctx);
  assert.equal(words.length, 5, words.join(" | "));
  assert.ok(words[0].startsWith("Black African turnout +5"));
  assert.ok(words[1].startsWith("White turnout -0.5"));
  // a poll chosen but not believed is not a setting
  assert.deepEqual(settingsWords({ ...d, polls: [poll.id], trust: 0 }, ctx), []);
});
