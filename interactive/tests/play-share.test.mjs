// "Play with the model": anonymous save and share.
//
//   node --test interactive/tests/
//
// 1. A link round-trips: every case the native harness computes
//    (play-settings.json), written to a link and read back, asks the engine
//    for exactly the settings it started from. page.py's compute is a pure
//    function of those settings (page.test.mjs holds native and Pyodide to one
//    fixture), so the link reproduces the same figures.
// 2. A broken link falls back to the published setting and says so.
// 3. The share image is drawn from the compute result the page shows: each
//    party's row carries that party's middle seat count and no range (review
//    2026-10-02), every other digit comes from the result's totals, its
//    largest-party shares, its ward count, the reader's settings, the election
//    day, the date the card was made or the reader's name (drawn as text, never
//    markup), every ward is drawn in the result's colour, the parties are in
//    the page's order, and a figure typed into the card, or a result the card
//    ignored, is caught (and the check goes quiet again).
// 4. The card says whose figures these are: untouched, the model's forecast,
//    with the name only on a "Shared by" line; touched, the reader's settings,
//    with "Not the model's forecast" in the foot (critic G1/G2, code review 5,
//    review 2026-10-02: in the small type, not under the headline).
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import * as PS from "../js/play-state.js";
import { buildPlayCardSVG, order, seatText, settingsWords, playCardAlt, madeLine, headline, sharedBy, largestLine,
         rangeText, subLine, READER_STAMP, PUBLISHED_STAMP, STORY_TEXT_BOTTOM, SIZES } from "../js/play-card.js";

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
const ROSTER = new Proxy({}, { get: (_, c) => ({ code: c, name: String(c).replace(/_/g, " "), colour: "#888888", article: "" }) });
// the fixture predates no field the card reads: every share carries its text
const party = c => ROSTER[c];
const textOf = svg => [...svg.matchAll(/<text\b[^>]*>([^<]*)<\/text>/g)].map(m => m[1]);
const runs = s => (s.replace(/[   ]/g, "").match(/\d+(?:\.\d+)?/g) || []);
const unesc = s => s.replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&amp;/g, "&");

const MADE = "2026-10-01";
const WHEN = "4 November 2026";
// Constructed boundaries, one square per ward the result carries: the card's
// map is checked against the result, not against a file on this machine.
const geometryFor = r => ({ W: 100, H: 50, step: 7, rotate: 45, places: [],
  paths: Object.fromEntries(r.wards.map((w, i) => [w.ward, `M${i} 0L${i + 1} 0L${i + 1} 1Z`])) });
const card = (c, extra = {}) => {
  const r = extra.r ?? c.result;
  const st = { ...settingsOf(c.name), name: "" };
  return { r, st, ctx, party, made: MADE, when: WHEN, name: "reader-7", touched: PS.isTouched(st),
           geometry: geometryFor(r), photoSrc: null, ...extra };
};

// The digit runs the card may print outside the seat rows: the result's
// council and majority, the reader's settings, the election day, the made line
// and the reader's name. No seat figure is here: a row's figure is checked
// against its own party.
function allowed(info) {
  const out = new Set();
  const add = x => runs(String(x)).forEach(d => out.add(d));
  add(subLine(info)); add(largestLine(info.r, party)); add(info.r.wards.length);
  settingsWords(info.st, ctx).forEach(add);
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

const moved = FIXTURE.cases.filter(c => c.result && !c.result.refused && c.name !== "untouched");
const settingsOf = name => toState(CASES.find(c => c.name === name).settings);
const untouched = FIXTURE.cases.find(c => c.name === "untouched");

test("the card's figures are the result's, in the page's order, at both sizes", () => {
  assert.ok(moved.length >= 3, "the fixture has computed cases");
  for (const c of [untouched, ...moved]) {
    for (const size of Object.keys(SIZES)) {
      const info = card(c);
      const svg = buildPlayCardSVG({ ...info, size });
      assert.match(svg, new RegExp(`width="${SIZES[size][0]}" height="${SIZES[size][1]}"`));
      assert.deepEqual(typed(svg, info), [], `${c.name} ${size}`);
      // whose figures these are: the model's forecast (the name only as
      // "Shared by"), or the reader's settings with "Not the model's
      // forecast" in the foot, not in the first lines
      const lines = textOf(svg).map(unesc);
      const all = lines.join(" ");
      const firstLines = lines.slice(1, 4).join(" ");    // after the site name
      assert.equal(lines[1], headline("reader-7", info.touched), `${c.name} ${size}: headline`);
      assert.ok(!/election forecast/i.test(all), `${c.name} ${size}`);
      if (info.touched) {
        assert.ok(!firstLines.includes(READER_STAMP.split(" ").slice(0, 4).join(" ")), `${c.name} ${size}: ${firstLines}`);
        assert.ok(all.includes(READER_STAMP.split(" ").slice(0, 4).join(" ")), `${c.name} ${size}: the stamp is in the foot`);
      } else {
        assert.ok(!lines[1].includes("reader-7"), `${c.name} ${size}: the name is not the model's headline`);
        assert.ok(firstLines.includes(sharedBy("reader-7")), `${c.name} ${size}: shared by`);
        assert.ok(all.includes(PUBLISHED_STAMP), `${c.name} ${size}: stamp`);
      }
      // the largest-party line, ties apart, in the result's own text
      assert.ok(all.includes(largestLine(info.r, party)), `${c.name} ${size}: largest`);
      assert.ok(all.includes(info.r.tied.text), `${c.name} ${size}: ties`);
      // every ward the result carries is drawn, in the result's colour
      for (const w of info.r.wards.slice(0, 20)) assert.ok(svg.includes(`fill="${w.fill}"`), w.ward);
      assert.equal((svg.match(/<path d="M/g) || []).length,
        info.r.wards.length + info.r.wards.filter(w => w.bands).length, `${c.name} ${size}: one fill and one stripe layer per ward`);
      // nothing runs off the card, and the story stays clear of the apps' lower chrome
      const ys = [...svg.matchAll(/<text x="[^"]*" y="([\d.]+)"/g)].map(m => +m[1]);
      assert.ok(Math.max(...ys) <= (size === "story" ? STORY_TEXT_BOTTOM : SIZES[size][1] - 10), `${c.name} ${size}: text at y ${Math.max(...ys)}`);
    }
    const alt = playCardAlt(card(c));
    assert.ok(alt.startsWith(headline("reader-7", card(c).touched)));
    assert.ok(alt.includes(largestLine(c.result, party)));
    for (const p of c.result.shown) assert.ok(!alt.includes(rangeText(c.result.seats[p])), `${c.name}: ${p}'s range in the alt`);
  }
});

test("a name never heads the model's forecast, and is the reader's own on the reader's settings", () => {
  // critic G1: "The IEC's Election Forecast" printed over the model's own figures
  const svg = buildPlayCardSVG(card(untouched, { name: "The IEC" }));
  const lines = textOf(svg).map(unesc);
  assert.equal(lines[1], "The model's Johannesburg forecast");
  assert.ok(lines.includes(sharedBy("The IEC")));
  assert.ok(!lines.some(l => /IEC's/.test(l)), lines.join(" | "));
  const mine = textOf(buildPlayCardSVG(card(moved[0], { name: "The IEC" }))).map(unesc);
  assert.equal(mine[1], "The IEC's settings on the model");
  assert.ok(!mine.slice(1, 4).some(l => l.startsWith(READER_STAMP)), mine.slice(1, 4).join(" | "));
  assert.ok(mine.join(" ").includes("Not the model's forecast"), "the stamp is in the foot");
});

test("the reader's name is drawn as text, never as markup", () => {
  const info = card(moved[0], { name: "<image href=x onerror=alert(1)>" });
  const svg = buildPlayCardSVG(info);
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
