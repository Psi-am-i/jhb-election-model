// "Play with the model": the share URL is bounded and validated on load (F16),
// and the page's JavaScript holds no re-weighting (one definition, in Python).
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
  // polls switched on at zero trust are still the published forecast
  assert.equal(PS.isTouched({ ...d, polls: ["a"] }), false);
});

test("a setting survives the URL both ways, with the model version", () => {
  const st = { shift: [2.5, 0, -1, 0], polls: ["b"], trust: 35, law: "cap", cell: "w_bye-1" };
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
  const p = PS.parse("?p=a,zzz", ctx);
  assert.deepEqual(p.state.polls, ["a"]);
  assert.equal(p.dropped.length, 1);
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
