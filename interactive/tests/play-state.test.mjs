// "Your forecast", section 1: its part of the address is bounded and validated
// on load (F16), only South African law is shared, and the page's JavaScript
// holds no re-weighting (one definition, in Python). The whole address, both
// sections and the name, is yf.test.mjs's.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import * as PS from "../js/play-state.js";

const here = dirname(fileURLToPath(import.meta.url));
const ctx = { pools: ["Black African", "Coloured", "Indian/Asian", "White"], polls: ["a", "b"],
              laws: ["deduct", "expand", "level", "cap"], cells: [".", "w_bye-0", "w_bye-1"], modelVersion: "abc" };

test("the published setting is untouched and writes no URL", () => {
  const d = PS.defaults(ctx);
  assert.equal(PS.isTouched(d), false);
  assert.equal(PS.serialize(d, ctx), "");
  // a poll chosen at zero belief, or a name, is still the published forecast
  assert.equal(PS.isTouched({ ...d, polls: ["a"] }), false);
  assert.equal(PS.isTouched({ ...d, name: "politico-23" }), false);
});

test("a setting survives the URL both ways, with the model version", () => {
  const st = { shift: [2.5, 0, -1, 0], polls: ["b"], trust: 35, law: "cap", cell: "w_bye-1", name: "" };
  const q = PS.serialize(st, ctx);
  assert.match(q, /mv=abc/);
  const back = PS.parse(q, ctx);
  assert.deepEqual(back.state, st);
  assert.deepEqual(back.dropped, []);
  assert.equal(back.otherVersion, null);
  assert.equal(PS.isTouched(back.state), true);
});

test("out-of-bounds fields are dropped to the published setting, never clamped, and said", () => {
  const cases = [
    ["?t=6,0,0,0", "shift"], ["?t=0.3,0,0,0", "shift"], ["?t=1,2,3", "shift"], ["?t=NaN,0,0,0", "shift"],
    ["?k=101", "trust"], ["?k=7", "trust"], ["?k=-5", "trust"],
    ["?l=proportional", "law"], ["?b=w_bye-9", "cell"],
  ];
  const d = PS.defaults(ctx);
  for (const [q, field] of cases) {
    const r = PS.parse(q, ctx);
    assert.deepEqual(r.state[field], d[field], q);
    assert.equal(r.dropped.length, 1, q);
  }
  // the detector goes quiet on an in-bounds value
  assert.deepEqual(PS.parse("?t=5,-5,0.5,0&k=100", ctx).dropped, []);
  // one poll at a time: two are refused together, and an unknown one too
  for (const q of ["?p=a,b", "?p=zzz"]) {
    const p = PS.parse(q, ctx);
    assert.deepEqual(p.state.polls, [], q);
    assert.equal(p.dropped.length, 1, q);
  }
  assert.deepEqual(PS.parse("?p=b", ctx).state.polls, ["b"]);
  assert.equal(PS.parse("?t=1,0,0,0&mv=other", ctx).otherVersion, "other");
  // a prefix shorter than the version written is not taken as a match
  assert.equal(PS.parse("?t=1,0,0,0&mv=a", ctx).otherVersion, "a");
  assert.equal(PS.parse("?t=1,0,0,0&mv=abc", ctx).otherVersion, null);
});

test("a refused field is named, and the link's own text is never repeated", () => {
  const evil = "ANC wins 99 seats<img src=x onerror=alert(1)>";
  const e = encodeURIComponent(evil);
  const r = PS.parse(`?t=${e}&p=${e}&k=${e}&l=${e}&b=${e}`, ctx);
  assert.equal(r.dropped.length, 5);
  for (const line of r.dropped) {
    assert.ok(!line.includes("99") && !line.includes("<") && !line.includes("ANC"), line);
  }
  assert.deepEqual(r.state, PS.defaults(ctx));
});

test("the name is cleaned by one rule and is not this part's, nor the engine's", () => {
  assert.equal(PS.cleanName("  a\u0000 \n b  "), "a b");
  // direction and width controls and C1 controls are dropped: a name cannot
  // reverse or hide the words drawn after it on the image
  assert.equal(PS.cleanName("a\u202Eb\u2066c\u200Bd\u0085e\u061Cf\uFEFFg"), "abcdefg");
  // one unit for the field and the link: UTF-16 units, as maxlength counts,
  // and a character is never cut in two
  const emoji = "\u{1F600}".repeat(PS.NAME_MAX / 2);
  const cut = PS.cleanName("x" + emoji);
  assert.ok(cut.length <= PS.NAME_MAX && !/[\uD800-\uDBFF]$/.test(cut), JSON.stringify(cut));
  assert.equal(cut, "x" + "\u{1F600}".repeat(PS.NAME_MAX / 2 - 1));
  // markup survives as text: the page never parses it, and the card escapes it
  assert.equal(PS.cleanName("<b>x</b>"), "<b>x</b>");
  // the name is yf-url.js's: section 1's part neither writes nor reads it
  assert.equal(PS.serialize({ ...PS.defaults(ctx), name: "z" }, ctx), "");
  assert.equal(PS.parse("?n=z", ctx).state.name, "");
  assert.deepEqual(PS.parse("?n=" + "x".repeat(99), ctx).dropped, []);
  assert.equal("name" in PS.engineSettings({ ...PS.defaults(ctx), name: "z" }), false);
});

test("only a council under South African law can be shared", () => {
  const d = PS.defaults(ctx);
  assert.equal(PS.shareable(d), true);
  for (const law of ctx.laws) assert.equal(PS.shareable({ ...d, law }), law === PS.PUBLISHED_LAW, law);
  // every other setting may be shared
  assert.equal(PS.shareable({ ...d, shift: [5, 0, 0, 0], polls: ["a"], trust: 50, cell: "w_bye-0" }), true);
});

test("the engine is asked for trust as a fraction", () => {
  const s = PS.engineSettings({ shift: [1, 0, 0, 0], polls: ["a"], trust: 50, law: "deduct", cell: "." });
  assert.equal(s.trust, 0.5);
});

// The page's JavaScript must not re-weight: the marks of the deleted stand-in
// were an exponential weight and a hand-rolled weighted quantile.
const REWEIGHTING = [/Math\.exp\s*\(/, /\bwquant\b/, /\bsigma\s*\*\s*sigma\b/, /effective.*=.*\*\s*sw\s*\/\s*sw2/];
function reweightingIn(text) { return REWEIGHTING.filter(re => re.test(text)).map(String); }

test("no page script re-weights (one definition, in Python)", () => {
  const dir = resolve(here, "../js");
  const files = readdirSync(dir).filter(f => f.endsWith(".js"));
  assert.ok(files.includes("model.js") && files.length >= 10, files.join(","));
  for (const f of files) assert.deepEqual(reweightingIn(readFileSync(resolve(dir, f), "utf8")), [], f);
  // it can see: the deleted stand-in's own line is caught, and a clean one is not
  assert.ok(reweightingIn("w[i] *= Math.exp(lam * (x - m));").length > 0);
  assert.deepEqual(reweightingIn("const x = 1;"), []);
});

// B1 (owner, 2026-10-05): a slider that stops shows a shaded zone beyond the
// furthest setting it reaches; the thumb is held at the stop.
test("a stop shades the track beyond it, each way, and holds the thumb there", () => {
  const T = PS.TRUST;
  assert.deepEqual(PS.stopZones(T, null), []);
  assert.deepEqual(PS.stopZones(T, { up: null, down: null }), []);
  const up = PS.withStop(null, 1, 35);
  assert.deepEqual(up, { up: 35, down: null });
  assert.deepEqual(PS.stopZones(T, up), [{ from: 0.35, to: 1 }]);
  // a stop at the slider's own end shades nothing
  assert.deepEqual(PS.stopZones(T, PS.withStop(null, 1, T.max)), []);
  // turnout runs both ways from zero; a second stop keeps the first
  const U = PS.TURNOUT;
  const both = PS.withStop(PS.withStop(null, 1, 3), -1, -2.5);
  assert.deepEqual(both, { up: 3, down: -2.5 });
  const z = PS.stopZones(U, both);
  assert.equal(z.length, 2);
  assert.ok(Math.abs(z[0].from - (3 - U.min) / (U.max - U.min)) < 1e-12 && z[0].to === 1);
  assert.ok(z[1].from === 0 && Math.abs(z[1].to - (-2.5 - U.min) / (U.max - U.min)) < 1e-12);
  // a new stop the same way replaces the old one
  assert.deepEqual(PS.withStop(both, 1, 4), { up: 4, down: -2.5 });
  // the thumb: held at a stop it is dragged past, free inside
  assert.equal(PS.heldAtStop(50, up), 35);
  assert.equal(PS.heldAtStop(35, up), 35);
  assert.equal(PS.heldAtStop(20, up), 20);
  assert.equal(PS.heldAtStop(-4, both), -2.5);
  assert.equal(PS.heldAtStop(5, both), 3);
  assert.equal(PS.heldAtStop(1, both), 1);
  assert.equal(PS.heldAtStop(90, null), 90);
});

// B2 (diff review, 2026-10-05): a refused discrete option sends back only its
// own control; the controls still moved since the last figures shown are
// named, sliders first, and computed next.
test("movedGroups names each control that differs, sliders first", () => {
  const a = { shift: [0, 0, 0], polls: [], trust: 0, cell: ".", law: "deduct", name: "" };
  assert.deepEqual(PS.movedGroups(a, { ...a, shift: a.shift.slice(), name: "Thandi" }), []);
  const b = { ...a, shift: [0, 1.5, 0], polls: ["p1"], trust: 40, cell: "x", law: "cap" };
  assert.deepEqual(PS.movedGroups(a, b), ["turnout:1", "trust", "poll", "cell", "law"]);
  assert.deepEqual(PS.movedGroups(a, { ...a, shift: [-0.5, 0, 0] }), ["turnout:0"]);
  // no poll is the same as an empty list
  assert.deepEqual(PS.movedGroups(a, { ...a, polls: [""] }), []);
});
