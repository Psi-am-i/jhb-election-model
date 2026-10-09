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
  const atWard = states.filter(s => { const b = B.wardLimits(s.calls, ctx, B.totalOf(s, "ward"));
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
  const b = B.wardLimits(start.calls, ctx, B.totalOf(start, "ward"));
  assert.equal(lo.state.ward[c], b.floor[c]);
  assert.equal(lo.by, b.bind[c].floor);
  const hi = B.setWardPercent(start, ctx, c, 100);
  assert.equal(hi.clamped, "ceiling");
  assert.equal(hi.state.ward[c], b.ceil[c]);
  assert.equal(hi.by, b.bind[c].ceil);
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
// shares, votes or points. A number in it other than 0, 1 (a vote; the whole
// ward; the rest of the wards) and 100 (points) is a bound typed rather than
// read; wardRange alone may also hold 2, because its closed form takes the
// midpoint of an interval, (1 - Lp) / 2 (SPEC-B2 §3), which is geometry and
// not a bound. Anywhere else a 2 is found. The closed form's float tolerance is the module constant EPS,
// outside every function, so it is not a literal here.
const BOUND_FUNCTIONS = ["sigmaMin", "wardRange", "wardCell", "boxOf", "limits", "wardLimits",
  "gapOf", "listBounds", "contextOf"];
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
      if (!["0", "1", "100", ...(fn === "wardRange" ? ["2"] : [])].includes(m[0])) out.push(fn + ": " + m[0]);
  }
  return out;
}
test("the bounds are read from the schema, not typed", () => {
  const src = readFileSync(resolve(repo, "interactive/js/builder-state.js"), "utf8");
  assert.deepEqual(typedBounds(src), []);
  // it can see: a typed bound anywhere in the arithmetic is found, and the
  // scan is quiet again on the real source
  assert.deepEqual(typedBounds(src.replace("Math.max(lo[W], q_win)", "Math.max(lo[W], 0.186)")), ["wardCell: 0.186"]);
  assert.deepEqual(typedBounds(src.replace("Math.max(gap_max, g)", "Math.max(11.16, g)")), ["listBounds: 11.16"]);
  assert.deepEqual(typedBounds(src.replace("smin > smax + EPS", "smin > smax + 1e-9")), ["wardRange: 1e-9"]);
  // the 2 is allowed in wardRange only: typed into limits, it is found
  assert.deepEqual(typedBounds(src.replace("cl = city.lo[k]", "cl = city.lo[k] / 2")), ["limits: 2"]);
  assert.deepEqual(typedBounds(src.replace("cl = city.lo[k]", "cl = 0.05")), ["limits: 0.05"]);
  assert.ok(typedBounds(src.replace("function wardRange(", "function wardRangeX(")).length, "a renamed function is not scanned in silence");
  assert.deepEqual(typedBounds(src), []);
});

// ---- the ward-by-ward bounds (slice B2a, SPEC-B2r2 §4-§5) ----

// Every vertex of one ward's set {lo <= x <= hi, sum x = 1, x_W >= x_q}, by
// brute force: each choice of n - 1 inequalities held tight with the sum,
// solved by Gaussian elimination and kept if it satisfies every inequality.
// No LP library; the population is small (2 to 5 parties).
function vertices(lo, hi, W, { winner = true } = {}) {
  const n = lo.length, rows = [];
  for (let k = 0; k < n; k++) {
    rows.push({ a: Array.from({ length: n }, (_, j) => (j === k ? 1 : 0)), b: lo[k], ge: true });
    rows.push({ a: Array.from({ length: n }, (_, j) => (j === k ? 1 : 0)), b: hi[k], ge: false });
    if (winner && k !== W) rows.push({ a: Array.from({ length: n }, (_, j) => (j === W ? 1 : j === k ? -1 : 0)), b: 0, ge: true });
  }
  const out = [];
  const pick = (from, need, chosen) => {
    if (need === 0) {
      const A = [Array(n).fill(1), ...chosen.map(i => rows[i].a)], y = [1, ...chosen.map(i => rows[i].b)];
      const M = A.map((r, i) => [...r, y[i]]);
      for (let c = 0; c < n; c++) {
        let piv = c;
        for (let r = c + 1; r < n; r++) if (Math.abs(M[r][c]) > Math.abs(M[piv][c])) piv = r;
        if (Math.abs(M[piv][c]) < 1e-12) return;
        [M[c], M[piv]] = [M[piv], M[c]];
        for (let r = 0; r < n; r++) if (r !== c) { const f = M[r][c] / M[c][c]; for (let k = c; k <= n; k++) M[r][k] -= f * M[c][k]; }
      }
      const x = M.map((r, i) => r[n] / r[i]);
      if (rows.every(r => { const v = r.a.reduce((t, a, j) => t + a * x[j], 0); return r.ge ? v >= r.b - 1e-9 : v <= r.b + 1e-9; }))
        out.push(x);
      return;
    }
    for (let i = from; i <= rows.length - need; i++) pick(i + 1, need - 1, [...chosen, i]);
  };
  pick(0, n - 1, []);
  return out;
}
function projection(lo, hi, W, opts) {
  const vs = vertices(lo, hi, W, opts);
  if (!vs.length) return { ok: false };
  return { ok: true, min: lo.map((_, k) => Math.min(...vs.map(v => v[k]))), max: lo.map((_, k) => Math.max(...vs.map(v => v[k]))) };
}
function randomWard(r) {
  const n = 2 + Math.floor(r() * 4), lo = [], hi = [];
  for (let k = 0; k < n; k++) {
    const a = r() * [0.05, 0.3, 0.6][Math.floor(r() * 3)];
    lo.push(a); hi.push(Math.min(1, a + r() * [0.1, 0.5, 1][Math.floor(r() * 3)]));
  }
  return { lo, hi, W: Math.floor(r() * n) };
}
function disagreements(closed, wards) {
  let bad = 0;
  for (const { lo, hi, W } of wards) {
    const a = closed(lo, hi, W), b = projection(lo, hi, W);
    if (a.ok !== b.ok) { bad++; continue; }
    if (a.ok && lo.some((_, k) => Math.abs(a.min[k] - b.min[k]) > 1e-9 || Math.abs(a.max[k] - b.max[k]) > 1e-9)) bad++;
  }
  return bad;
}
test("the ward range is the set's projection", () => {
  const r = rng(2026), wards = Array.from({ length: 400 }, () => randomWard(r));
  const feasible = wards.filter(w => projection(w.lo, w.hi, w.W).ok).length;
  // it looked: both feasible and infeasible wards are in the population
  assert.ok(feasible > wards.length / 10 && feasible < wards.length, `feasible wards: ${feasible} of ${wards.length}`);
  assert.equal(disagreements(B.wardRange, wards), 0);
  // it can see: a closed form with the winner condition dropped is caught,
  // and the comparison is quiet again on the real one
  const noWinner = (lo, hi) => {
    const L = lo.reduce((a, b) => a + b, 0), H = hi.reduce((a, b) => a + b, 0);
    if (L > 1 || H < 1) return { ok: false };
    return { ok: true, min: lo.map((l, k) => Math.max(l, 1 - (H - hi[k]))), max: hi.map((h, k) => Math.min(h, 1 - (L - lo[k]))) };
  };
  assert.ok(disagreements(noWinner, wards) > 0, "a closed form without the winner condition passed");
  assert.equal(disagreements(B.wardRange, wards), 0);
});

// A copy of the context with other citywide limits or ward ranges: a
// constructed input, so the case is present whatever the data say.
const withCity = (lo, hi) => ({ ...ctx, bounds: { ...ctx.bounds, city: { lo, hi } } });
test("the limits are the box inside the citywide limit, and the map wins where they do not meet", () => {
  const L = B.limits(start.calls, ctx);
  for (const [k, c] of ctx.codes.entries()) {
    assert.equal(L.lo[c], Math.max(L.box.floor[c], ctx.bounds.city.lo[k]), c);
    assert.equal(L.hi[c], Math.min(L.box.ceil[c], ctx.bounds.city.hi[k]), c);
  }
  assert.deepEqual(L.conflict, []);
  // a map whose box floor passes a party's citywide ceiling: the conflict is
  // named and the ceiling is raised to the floor
  const c = start.calls[0], k = ctx.codes.indexOf(c);
  const hi = ctx.bounds.city.hi.slice(); hi[k] = L.box.floor[c] / 2;
  const bad = withCity(ctx.bounds.city.lo, hi);
  const C = B.limits(start.calls, bad);
  assert.deepEqual(C.conflict, [{ code: c, side: "floor" }]);
  assert.equal(C.lo[c], L.box.floor[c]);
  assert.equal(C.hi[c], L.box.floor[c]);
  const r = B.setCalls(start, bad, start.calls);
  assert.deepEqual(r.conflict, [{ code: c, side: "floor" }]);
  assert.deepEqual(B.invariantErrors(r.state, bad), []);
  assert.deepEqual(B.outOfBounds(r.state, bad).filter(o => o.ballot === "ward"), []);
  // and the other way: a citywide floor above what the map allows
  const lo2 = ctx.bounds.city.lo.slice(); lo2[k] = Math.min(1, L.box.ceil[c] * 2);
  assert.deepEqual(B.limits(start.calls, withCity(lo2, ctx.bounds.city.hi)).conflict, [{ code: c, side: "ceiling" }]);
  // reverted: quiet
  assert.deepEqual(B.limits(start.calls, withCity(ctx.bounds.city.lo, ctx.bounds.city.hi)).conflict, []);
});

test("floors that sum past the ballot, or ceilings short of it, are eased until the votes fit", () => {
  const n = ctx.codes.length;
  const high = withCity(Array(n).fill(0.5), ctx.bounds.city.hi.map(h => Math.max(h, 0.5)));
  const H = B.limits(start.calls, high);
  assert.equal(H.eased, "floors");
  assert.equal(B.setCalls(start, high, start.calls).eased, "floors", "a change of calls passes the easing to the page");
  assert.ok(ctx.codes.reduce((t, c) => t + H.lo[c], 0) <= 1 + 1e-9);
  const low = withCity(Array(n).fill(0), Array(n).fill(0.001));
  const W = B.limits(start.calls, low);
  assert.ok(W.eased === "ceilings" || W.eased === "both", W.eased);
  assert.ok(ctx.codes.reduce((t, c) => t + W.hi[c], 0) >= 1 - 1e-9);
  for (const x of [high, low]) {
    const Tw = B.totalOf(start, "ward"), v = B.wardLimits(start.calls, x, Tw);
    assert.ok(ctx.codes.reduce((t, c) => t + v.floor[c], 0) <= Tw);
    assert.ok(ctx.codes.reduce((t, c) => t + v.ceil[c], 0) >= Tw);
    const s = B.setWardPercent(start, x, start.calls[0], 30).state;
    assert.deepEqual(B.invariantErrors(s, x), []);
  }
  assert.equal(B.limits(start.calls, ctx).eased, null);
});

test("a painted ward no past result fits uses the shape alone, and is named", () => {
  const i = 0, W = ctx.codes.indexOf(start.calls[i]);
  const base = ctx.bounds.base.slice();
  base[i] = { lo: base[i].lo.slice(), hi: base[i].hi.slice() };
  base[i].hi[W] = ctx.bounds.q_win / 2;               // the winner cannot reach q_win here
  const bad = { ...ctx, bounds: { ...ctx.bounds, base } };
  const box = B.boxOf(start.calls, bad);
  assert.deepEqual(box.fallback, [{ ward: ctx.wards[i], code: start.calls[i] }]);
  // the ward's own ranges with the shape applied hold no share vector
  const lo = base[i].lo.slice(); lo[W] = Math.max(lo[W], ctx.bounds.q_win);
  assert.equal(B.wardRange(lo, base[i].hi.map((h, k) => (k === W ? h : Math.min(h, ctx.bounds.q_run))), W).ok, false);
  assert.deepEqual(B.boxOf(start.calls, ctx).fallback, []);
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
