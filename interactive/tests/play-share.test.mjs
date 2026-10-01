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
// 3. The share image is drawn from the compute result the page shows: every
//    digit on it comes from that result or the reader's settings, the
//    parties are in the page's order, and a figure typed into the card, or a
//    result the card ignored, is caught (and the check goes quiet again).
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import * as PS from "../js/play-state.js";
import { buildPlayCardSVG, order, seatText, settingsLines, playCardAlt, SIZES } from "../js/play-card.js";

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
const ROSTER = new Proxy({}, { get: (_, c) => ({ code: c, name: String(c).replace(/_/g, " "), colour: "#888888" }) });
const party = c => ROSTER[c];
const textOf = svg => [...svg.matchAll(/<text\b[^>]*>([^<]*)<\/text>/g)].map(m => m[1]);
const runs = s => (s.replace(/[   ]/g, "").match(/\d+(?:\.\d+)?/g) || []);

// Every digit run the card may print: the result's figures and the settings.
function allowed(r, st) {
  const out = new Set();
  const add = x => runs(String(x)).forEach(d => out.add(d));
  for (const c of r.shown) for (const k of ["median", "p5", "p95"]) add(seatText(r.seats[c][k]));
  add(Math.round(r.effective_draws).toLocaleString("en-ZA")); add(r.draws.toLocaleString("en-ZA"));
  add(seatText({ value: r.majority })); add(seatText({ value: r.council }));
  add(r.shown.length);
  for (let k = 0; k <= r.shown.length; k++) add(k);                // "N more parties"
  settingsLines(st, ctx).forEach(add);                            // the reader's own settings, in words
  return out;
}
function typed(svg, r, st) {
  const ok = allowed(r, st);
  return textOf(svg).flatMap(t => runs(t).filter(d => !ok.has(d)).map(d => `${d} in "${t}"`));
}

const moved = FIXTURE.cases.filter(c => c.result && !c.result.refused && c.name !== "untouched");
const settingsOf = name => toState(CASES.find(c => c.name === name).settings);

test("the card's figures are the result's, in the page's order, at both sizes", () => {
  assert.ok(moved.length >= 3, "the fixture has computed cases");
  for (const c of moved) {
    const r = c.result, st = settingsOf(c.name);
    for (const size of Object.keys(SIZES)) {
      const svg = buildPlayCardSVG({ r, st, ctx, party, size });
      assert.match(svg, new RegExp(`width="${SIZES[size][0]}" height="${SIZES[size][1]}"`));
      assert.deepEqual(typed(svg, r, st), [], `${c.name} ${size}`);
      const names = textOf(svg).filter(t => r.shown.some(p => party(p).name === t));
      const want = order(r, p => party(p).name).map(p => party(p).name).slice(0, names.length);
      assert.ok(names.length >= 5, `${c.name}: ${names.length} parties drawn`);
      assert.deepEqual(names, want, `${c.name} ${size}: party order`);
      const top = order(r, p => party(p).name)[0];
      assert.ok(textOf(svg).some(t => t.startsWith(seatText(r.seats[top].median) + " (")), `${c.name}: top median`);
      assert.match(textOf(svg).join(" "), /Not the model's forecast/);
    }
    assert.match(playCardAlt({ r, st, ctx, party }), /Not the model's forecast/);
  }
});

test("a typed figure, or a result the card did not read, is caught; reverted, quiet", () => {
  const c = moved[0], st = settingsOf(c.name);
  const r = JSON.parse(JSON.stringify(c.result));
  const svg = buildPlayCardSVG({ r, st, ctx, party });
  assert.deepEqual(typed(svg, r, st), []);
  const forged = svg.replace("</svg>", "<text x=\"1\" y=\"1\">The DA wins 4321 seats</text></svg>");
  assert.deepEqual(typed(forged, r, st), ['4321 in "The DA wins 4321 seats"']);
  // the card reads the result: change the top party's middle and the card moves with it
  const top = order(r, p => party(p).name)[0];
  r.seats[top].median.value = 987.6;
  const moved2 = buildPlayCardSVG({ r, st, ctx, party });
  assert.ok(textOf(moved2).some(t => t.startsWith("987.6 (")));
  assert.deepEqual(typed(moved2, c.result, st).length > 0, true);
  assert.deepEqual(typed(moved2, r, st), []);
});

test("a withheld figure is printed as withheld, never as a number", () => {
  const c = moved[0], st = settingsOf(c.name);
  const r = JSON.parse(JSON.stringify(c.result));
  const top = order(r, p => party(p).name)[0];
  r.seats[top].p95 = { ...r.seats[top].p95, withheld: true };
  const svg = buildPlayCardSVG({ r, st, ctx, party });
  assert.ok(textOf(svg).some(t => t.includes("–withheld)")));
  assert.throws(() => buildPlayCardSVG({ r: { refused: "too few" }, st, ctx, party }));
});
