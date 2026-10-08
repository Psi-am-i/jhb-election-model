// The builder can only hold a valid prediction (DESIGN-decided §14; entry
// version 2, BRIEF change 13: whole votes on the ward and list ballots).
//
//   node --test interactive/tests/
//
// Random reader edits are driven through js/builder-state.js, the module the
// page edits with, from our prediction (decode(start.f) of the data file the
// build writes). Every state reached must be valid, stay inside the editor's
// bounds (the walk starts inside them), pass the server's validator
// (worker-api/src/validate.js) AND be seated by the project's seat code: the
// seat Worker's own handler (entry.answer) over the served copy in
// interactive/py/, run here under the project's CPython, with the request
// built and the answer checked by the Worker's own seatRequest /
// checkSeatAnswer. reader_seats must pool exactly the whole votes the page
// holds, which is what makes "what is on screen is what is saved" true.
//
// The data file is site/your-forecast/forecast.json, or the file
// YF_FORECAST_JSON names (one built to a temporary directory).
//
// Set PYODIDE_NODE to a directory holding node_modules/pyodide to also run the
// page's engine module (js/seat-engine.js) under Pyodide and compare.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { resolve, dirname } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { createRequire } from "node:module";

import * as B from "../js/builder-state.js";
import * as MS from "../js/make-state.js";
import { validateForecast } from "../../worker-api/src/validate.js";
import { seatRequest, checkSeatAnswer } from "../../worker-api/src/seats.js";
import { check as checkServedCopy, DST as PY_DIR } from "../tools/sync_py.mjs";

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, "../..");
const D = JSON.parse(readFileSync(process.env.YF_FORECAST_JSON || resolve(repo, "site/your-forecast/forecast.json"), "utf8"));
const schema = D.schema;
const geom = D.geometry;
const ctx = B.contextOf(schema);
const start = MS.decode(D.start.f, ctx).state;
const likely = start.calls;
const PYTHON = resolve(repo, ".venv/bin/python");

// mulberry32: a seeded generator, so a failure is reproducible from its seed.
function rng(seed) {
  return () => {
    seed |= 0; seed = seed + 0x6D2B79F5 | 0;
    let t = Math.imul(seed ^ seed >>> 15, 1 | seed);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  };
}

// Seats for many bodies at once, through the CPython the project runs. Returns
// [{status, payload, ok, pool, errors}], ok/pool/errors reader_seats' own.
function seatBatch(bodies) {
  const reqs = bodies.map(b => seatRequest(b, schema));
  const script = `
import json, sys
sys.path.insert(0, ${JSON.stringify(PY_DIR)})
exec(open(${JSON.stringify(resolve(repo, "interactive/pyboot/boot.py"))}).read())
import reader_seats
out = []
for r in json.load(sys.stdin):
    status, payload = json.loads(seat_answer(json.dumps(r)))
    rs = reader_seats.reader_seats(r["ward_votes"], r["list_votes"], r["ward_winners"], r["context"])
    out.append({"status": status, "payload": payload, "ok": rs["ok"], "pool": rs["pool"], "errors": rs["errors"]})
print(json.dumps(out))
`;
  const text = execFileSync(PYTHON, ["-c", script], { input: JSON.stringify(reqs), maxBuffer: 1 << 28, cwd: repo });
  return JSON.parse(text);
}

// The pool the statute forms from a state: ward plus list votes of every
// party with a list vote, as reader_seats reports it.
function poolOf(s) {
  return Object.fromEntries(ctx.codes.filter(c => s.list[c] > 0).map(c => [c, s.ward[c] + s.list[c]]));
}

test("the served seat code is a current copy of src/ and the seat Worker's handler", () => {
  assert.deepEqual(checkServedCopy(), []);
});

test("the schema, the geometry and our prediction agree on the wards", () => {
  assert.deepEqual(ctx.wards, geom.wards.map(w => String(w.id)));
  assert.equal(ctx.wards.length, schema.properties.ward_calls.minItems);
  assert.equal(likely.length, ctx.wards.length);
  assert.equal(ctx.v, MS.FORMAT, "the schema's entry version is the page's");
});

// The random walk. Every edit a reader can make, including hostile values
// (negative, over 100, NaN) that the controls would never send.
const OPS = 7;
function walk(seed, steps) {
  const r = rng(seed);
  const pick = a => a[Math.floor(r() * a.length)];
  const sectors = [...new Set(geom.wards.map(w => w.sector))];
  let state = start;
  const hist = new B.History();
  const seen = [state];
  const ops = [];
  for (let k = 0; k < steps; k++) {
    const op = Math.floor(r() * OPS);
    const c = pick(ctx.codes);
    if (op === 0) {
      const pct = pick([0, 100, -5, 250, NaN, 1e-7, r() * 100, r() * 3, r() * 60]);
      hist.push(state); state = B.setWardPercent(state, ctx, c, pct).state; ops.push(`ward ${c} ${pct}`);
    } else if (op === 1) {
      const n = 1 + Math.floor(r() * 5);
      const idx = Array.from({ length: n }, () => Math.floor(r() * ctx.wards.length));
      hist.push(state); state = B.assignWards(state, ctx, idx, c).state; ops.push(`give ${idx} to ${c}`);
    } else if (op === 2) {
      const sec = pick(sectors);
      const idx = geom.wards.map((w, i) => (w.sector === sec ? i : -1)).filter(i => i >= 0);
      hist.push(state); state = B.assignWards(state, ctx, idx, c).state; ops.push(`area ${sec} to ${c}`);
    } else if (op === 3) {
      hist.push(state); state = B.setCalls(state, ctx, likely).state; ops.push("model map");
    } else if (op === 4) {
      if (ctx.noList.has(c)) continue;
      const pts = pick([-50, 50, NaN, 0, r() * 30 - 15, r() * 4 - 2]);
      hist.push(state); state = B.setListGap(state, ctx, c, pts).state; ops.push(`gap ${c} ${pts}`);
    } else if (op === 5) {
      const prev = hist.pop(); if (prev) { state = prev; ops.push("undo"); }
    } else {
      hist.push(state);
      state = B.setCalls({ calls: state.calls, ward: { ...start.ward }, list: { ...start.list } }, ctx, state.calls).state;
      ops.push("start votes");
    }
    seen.push(state);
  }
  return { seen, ops };
}

test("random edits: every state is valid, inside the editor's bounds, passes validate.js, and is seated by the seat law", () => {
  assert.deepEqual(B.outOfBounds(start, ctx), [], "the walk must start inside the bounds");
  const bodies = [];
  const states = [];
  for (let seed = 1; seed <= 12; seed++) {
    const r = rng(seed * 7919);
    const { seen, ops } = walk(seed, 150);
    seen.forEach((s, k) => {
      const at = `seed ${seed} after: ${ops.slice(0, k).slice(-3).join("; ")}`;
      assert.deepEqual(B.invariantErrors(s, ctx), [], at);
      assert.deepEqual(B.outOfBounds(s, ctx), [], at);
      const coalition = ctx.codes.filter(() => r() < 0.3);
      const body = B.entryBody(s, ctx, { coalition, mayor: coalition.length && r() < 0.5 ? coalition[0] : null });
      const v = validateForecast(body, schema);
      assert.ok(v.ok, `seed ${seed} step ${k}: validate.js refused ${v.field}: ${v.reason}`);
      bodies.push(v.value);
      states.push(s);
    });
  }
  const answers = seatBatch(bodies);
  assert.equal(answers.length, bodies.length);
  answers.forEach((a, i) => {
    assert.equal(a.status, 200, `state ${i}: the seat Worker's handler answered ${a.status}: ${JSON.stringify(a.payload)}`);
    assert.ok(a.ok, `state ${i}: reader_seats refused: ${a.errors}`);
    assert.doesNotThrow(() => checkSeatAnswer(a.payload, bodies[i], schema));
    assert.deepEqual(a.pool, poolOf(states[i]), `state ${i}: reader_seats pooled different votes from the page's`);
  });
  // The population: every state of every walk (an op skipped for a list-less
  // party adds none), and it must be the whole of it.
  assert.equal(answers.length, states.length);
  assert.ok(states.length > 12 * 140, states.length);
  // It looked where it matters: a party at its ward floor or ceiling, a gap
  // at its bound, and a party with no vote at all.
  const atWard = states.filter(s => { const b = B.wardBounds(s.calls, ctx, B.totalOf(s, "ward"));
    return ctx.codes.some(c => s.ward[c] === b.floor[c] && b.floor[c] > 1 || s.ward[c] === b.ceil[c]); }).length;
  const atGap = states.filter(s => ctx.codes.some(c => !ctx.noList.has(c) &&
    Math.min(Math.abs(B.gapOf(s, ctx, c) - ctx.bounds.gap_min), Math.abs(B.gapOf(s, ctx, c) - ctx.bounds.gap_max)) < 0.01)).length;
  const empty = states.filter(s => ctx.codes.some(c => s.ward[c] === 0 && s.list[c] === 0)).length;
  assert.ok(atWard > 0 && atWard < states.length, `states with a party at a ward bound: ${atWard}`);
  assert.ok(atGap > 0, `states with a gap at its bound: ${atGap}`);
  assert.ok(empty > 0, `states with a party holding no vote: ${empty}`);
  console.log(`# ${atWard} with a party at a ward bound, ${atGap} with a gap at its bound, ${empty} with a voteless party`);
  console.log(`# ${answers.length} states seated, all valid`);
});

test("R1 and R2: one vote seats a ward winner, zero is refused, on each ballot", () => {
  const holder = ctx.codes.find(c => start.calls.includes(c) && !ctx.noList.has(c));
  const other = ctx.codes.find(c => c !== holder && start.ward[c] > 10 && start.list[c] > 10);
  const at = (ballot, n) => {
    const m = { ...start[ballot] };
    m[other] += m[holder] - n; m[holder] = n;
    return { ...start, [ballot]: m };
  };
  const states = [at("ward", 1), at("ward", 0), at("list", 1), at("list", 0)];
  assert.deepEqual(states.map(s => B.invariantErrors(s, ctx).length > 0), [false, true, false, true]);
  const bodies = states.map(s => B.entryBody(s, ctx));
  // validate.js refuses the two zero states too, naming the ballot
  assert.deepEqual(bodies.map(b => validateForecast(b, schema).ok), [true, false, true, false]);
  assert.equal(validateForecast(bodies[1], schema).field, "ward_votes." + holder);
  assert.equal(validateForecast(bodies[3], schema).field, "list_votes." + holder);
  const got = seatBatch(bodies);
  assert.deepEqual(got.map(a => a.status), [200, 422, 200, 422]);
  assert.match(got[1].payload.errors.join(" "), /no ward vote/);
  assert.match(got[3].payload.errors.join(" "), /no list vote/);
});

test("a ward painted for a party moves its ward vote into range and gives it a list vote", () => {
  const c = ctx.codes.find(x => !ctx.noList.has(x) && !start.calls.includes(x) && start.list[x] === 0)
    ?? ctx.codes.find(x => !ctx.noList.has(x) && !start.calls.includes(x));
  const before = { ...start, list: { ...start.list, [c]: 0 }, ward: { ...start.ward } };
  const shift = ctx.codes.find(x => x !== c && before.list[x] > 1000);
  before.list[shift] += start.list[c];
  const r = B.assignWards(before, ctx, [0], c);
  assert.deepEqual(B.invariantErrors(r.state, ctx), []);
  assert.ok(r.state.ward[c] >= 1 && r.state.list[c] >= 1);
  assert.deepEqual(B.outOfBounds(r.state, ctx).filter(o => o.ballot === "ward"), []);
});

test("setting a ward vote rescales the others' and every list vote follows its party", () => {
  const c = start.calls[0];
  const pct = B.percentOf(start, ctx, "ward")[c] + 1;
  const r = B.setWardPercent(start, ctx, c, pct);
  assert.equal(r.clamped, null);
  const next = r.state;
  assert.equal(B.totalOf(next, "ward"), B.totalOf(start, "ward"));
  assert.equal(B.totalOf(next, "list"), B.totalOf(start, "list"));
  const others = ctx.codes.filter(x => x !== c && start.ward[x] > 1000);
  const k = others.map(x => next.ward[x] / start.ward[x]);
  for (const x of k) assert.ok(Math.abs(x - k[0]) < 1e-3, `ratios ${k}`);
  for (const x of ctx.codes) assert.ok(Math.abs(B.gapOf(next, ctx, x) - B.gapOf(start, ctx, x)) < 0.01, x);
  // the gap is set on its own, to the point asked for
  const g = B.setListGap(next, ctx, c, B.gapOf(next, ctx, c) + 1).state;
  assert.ok(Math.abs(B.gapOf(g, ctx, c) - B.gapOf(next, ctx, c) - 1) < 0.01);
  assert.deepEqual(g.ward, next.ward);
});

test("the editor clamps to the bounds and says which", () => {
  const c = start.calls[0];
  const lo = B.setWardPercent(start, ctx, c, 0);
  assert.equal(lo.clamped, "floor");
  const b = B.wardBounds(start.calls, ctx, B.totalOf(start, "ward"));
  assert.equal(lo.state.ward[c], b.floor[c]);
  const hi = B.setWardPercent(start, ctx, c, 100);
  assert.equal(hi.clamped, "ceiling");
  assert.equal(hi.state.ward[c], b.ceil[c]);
  const gap = B.setListGap(start, ctx, c, 1000);
  assert.ok(gap.clamped === "gap_max" || gap.clamped === "others", gap.clamped);
  assert.ok(B.gapOf(gap.state, ctx, c) <= ctx.bounds.gap_max + 0.01);
});

test("a prediction is opened whole or refused by name: no fallback", () => {
  const pred = { ward_calls: D.start.ward_calls, ward_votes: D.start.ward_votes, list_votes: D.start.list_votes };
  assert.ok(MS.sameState(B.stateFromPrediction(ctx, pred), start, ctx));
  const byWard = { ...pred, ward_calls: Object.fromEntries(ctx.wards.map((w, i) => [w, pred.ward_calls[i]])) };
  assert.ok(MS.sameState(B.stateFromPrediction(ctx, byWard), start, ctx));
  assert.throws(() => B.stateFromPrediction(ctx, { ...pred, list_votes: undefined }), /no list_votes/);
  const short = { ...pred.ward_votes }; delete short[ctx.codes[0]];
  assert.throws(() => B.stateFromPrediction(ctx, { ...pred, ward_votes: short }), /lack/);
  const missing = { ...byWard.ward_calls }; delete missing[ctx.wards[0]];
  assert.throws(() => B.stateFromPrediction(ctx, { ...byWard, ward_calls: missing }), /no winner for ward/);
});

// The bounds arithmetic: every function that turns the schema's bounds into
// votes or points. A number in it other than 0, 1 (a vote; the rest of the
// wards) and 100 (points) is a bound typed rather than read.
const BOUND_FUNCTIONS = ["wonE", "wardBounds", "gapOf", "listBounds", "contextOf"];
function bodyOf(src, fn) {
  const at = src.search(new RegExp("(export )?function " + fn + "\\("));
  if (at < 0) return null;
  const next = src.slice(at + 1).search(/\n(export )?(function|class|const) /);
  return src.slice(at, next < 0 ? undefined : at + 1 + next);
}
function typedBounds(src) {
  const out = [];
  for (const fn of BOUND_FUNCTIONS) {
    const body = bodyOf(src, fn);
    if (body === null) { out.push(fn + " not found"); continue; }
    const code = body.replace(/\/\/.*$/gm, "").replace(/"[^"]*"/g, '""');
    for (const m of code.matchAll(/(?<![\w.$])\d+(\.\d+)?(e-?\d+)?\b/g))
      if (!["0", "1", "100"].includes(m[0])) out.push(fn + ": " + m[0]);
  }
  return out;
}
test("the bounds are read from the schema, not typed", () => {
  const src = readFileSync(resolve(repo, "interactive/js/builder-state.js"), "utf8");
  assert.deepEqual(typedBounds(src), []);
  // it can see: a typed bound anywhere in the arithmetic is found, and the
  // scan is quiet again on the real source
  assert.deepEqual(typedBounds(src.replace("q_win * won[c]", "0.186 * won[c]")), ["wardBounds: 0.186"]);
  assert.deepEqual(typedBounds(src.replace("Math.max(gap_max, g)", "Math.max(11.16, g)")), ["listBounds: 11.16"]);
  assert.ok(typedBounds(src.replace("function wonE(", "function wonX(")).length, "a renamed function is not scanned in silence");
  assert.deepEqual(typedBounds(src), []);
});

test("undo restores calls and both ballots together", () => {
  const a = start.calls[0];
  const b = ctx.codes.find(c => c !== a);
  const h = new B.History();
  h.push(start);
  let s = B.assignWards(start, ctx, start.calls.map((c, i) => (c === a ? i : -1)).filter(i => i >= 0), b).state;
  h.push(s);
  s = B.setWardPercent(s, ctx, a, 0).state;
  h.pop();                                      // back past the vote edit
  const back = h.pop();                         // back past the ward edit
  assert.deepEqual(back, { calls: start.calls, ward: start.ward, list: start.list });
  assert.deepEqual(B.invariantErrors(back, ctx), []);
});

// B4 (owner, 2026-10-05): the one-click chips for painting wards are chosen
// by one seat-based rule for every party: the eight with the most seats in
// the reader's council (at its start, before the seat law has answered), a
// tie for the last chip falling to alphabetical order, shown alphabetically.
// Every other party is in the "More parties" select.
test("the painting chips are the eight parties with the most seats, by one rule, alphabetical", () => {
  const name = c => D.schema["x-parties"].find(p => p.code === c).name;
  const alpha = D.schema["x-parties"].map(p => p.code).sort((a, b) => name(a).localeCompare(name(b)));
  const seats = D.start.seats;
  const chips = B.chipParties(alpha, seats);
  assert.equal(B.CHIP_LIMIT, 8);
  assert.equal(chips.length, B.CHIP_LIMIT);
  assert.deepEqual(chips, alpha.filter(c => chips.includes(c)), "the chips are not alphabetical");
  // no party left in the select holds more seats than a party with a chip
  const least = Math.min(...chips.map(c => seats[c]));
  for (const c of alpha.filter(c => !chips.includes(c))) assert.ok(!((seats[c] || 0) > least), c);
  assert.ok(chips.includes("ASA"), "ActionSA has no chip");
  assert.ok(!D.start.ward_calls.includes("ASA"), "the start calls ActionSA for a ward: the case this guards is gone");
  // a tie for the last chip falls to alphabetical order
  assert.deepEqual(B.chipParties(["A", "B", "C", "D"], { D: 9, C: 1, B: 1, A: 0 }, 2), ["B", "D"]);
  assert.deepEqual(B.seatedIn({ A: 0, B: 2, C: 5 }), ["C", "B"]);
});

test("the page's engine under Pyodide gives the CPython answer", { skip: !process.env.PYODIDE_NODE && "PYODIDE_NODE not set" }, async () => {
  const req = createRequire(resolve(process.env.PYODIDE_NODE, "package.json"));
  const mod = await import(pathToFileURL(req.resolve("pyodide")).href);
  const loadPyodide = mod.loadPyodide ?? mod.default.loadPyodide;
  const { loadSeatEngine } = await import("../js/seat-engine.js");
  const t0 = performance.now();
  const engine = await loadSeatEngine({
    // Pyodide's own directory stays the index (it caches wheels there); the
    // packages come from the CDN the page uses.
    loadPyodide: ({ indexURL, ...opts }) => loadPyodide({ ...opts, packageBaseUrl: indexURL,
      packageCacheDir: dirname(req.resolve("pyodide")) }),
    readText: async rel => readFileSync(resolve(repo, "interactive", rel), "utf8"),
  });
  console.log(`# node Pyodide load: ${Math.round(performance.now() - t0)} ms`, engine.times);
  const { seen } = walk(99, 40);
  const bodies = seen.map(s => B.entryBody(s, ctx, { coalition: [ctx.codes[0]] }));
  const cp = seatBatch(bodies);
  bodies.forEach((b, i) => {
    const r = engine.seats(b, schema);
    assert.ok(r.ok, JSON.stringify(r.errors));
    assert.deepEqual(r.answer, checkSeatAnswer(cp[i].payload, b, schema));
  });
});
