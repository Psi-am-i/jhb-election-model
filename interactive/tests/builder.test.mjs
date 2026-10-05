// The builder can only hold a valid forecast (DESIGN-decided §14).
//
//   node --test interactive/tests/
//
// Random reader edits are driven through js/builder-state.js, the module the
// page edits with. Every state reached must pass the server's validator
// (worker-api/src/validate.js) AND be seated by the project's seat code: the
// seat Worker's own handler (entry.answer) over the served copy in
// interactive/py/, run here under the project's CPython, with the request built
// and the answer checked by the Worker's own seatRequest / checkSeatAnswer.
// reader_seats must also count exactly the whole votes the page holds, which is
// what makes "what is on screen is what is saved" true.
//
// Set PYODIDE_NODE to a directory holding node_modules/pyodide to also run the
// page's engine module (js/seat-engine.js) under Pyodide and compare.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, existsSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { resolve, dirname } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { createRequire } from "node:module";

import * as B from "../js/builder-state.js";
import { validateForecast } from "../../worker-api/src/validate.js";
import { seatRequest, checkSeatAnswer } from "../../worker-api/src/seats.js";
import { check as checkServedCopy, DST as PY_DIR } from "../tools/sync_py.mjs";

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, "../..");
const schema = JSON.parse(readFileSync(resolve(repo, "worker-api/generated/forecast.schema.json"), "utf8"));
const model = JSON.parse(readFileSync(resolve(repo, "interactive/fixtures/placeholder-model.json"), "utf8"));
const geom = JSON.parse(readFileSync(resolve(repo, "interactive/fixtures/geometry.json"), "utf8"));
const ctx = B.contextOf(schema);
const likely = ctx.wards.map(w => model.likely_ward_winner[w]);
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
// [{status, payload, votes, ok}] where votes/ok are reader_seats' own.
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
    rs = reader_seats.reader_seats(r["combined_shares"], r["ward_winners"], r["context"], r["total_votes"])
    out.append({"status": status, "payload": payload, "ok": rs["ok"], "votes": rs["votes"], "errors": rs["errors"]})
print(json.dumps(out))
`;
  const text = execFileSync(PYTHON, ["-c", script], { input: JSON.stringify(reqs), maxBuffer: 1 << 28, cwd: repo });
  return JSON.parse(text);
}

function nonZero(votes) { return Object.fromEntries(Object.entries(votes).filter(([, v]) => v > 0)); }

test("the served seat code is a current copy of src/ and the seat Worker's handler", () => {
  assert.deepEqual(checkServedCopy(), []);
});

test("the schema, the geometry and the model fixture agree on the wards", () => {
  assert.deepEqual(ctx.wards, geom.wards.map(w => String(w.id)));
  assert.equal(ctx.wards.length, schema.properties.ward_calls.minItems);
});

// The random walk. Every edit a reader can make, including hostile values
// (negative, over 100, NaN) that the controls would never send.
function walk(seed, steps) {
  const r = rng(seed);
  const pick = a => a[Math.floor(r() * a.length)];
  const sectors = [...new Set(geom.wards.map(w => w.sector))];
  const starts = [
    { calls: null, share: model.combined_share },                                 // the model page's hand-off
    { calls: likely, share: Object.fromEntries(ctx.codes.map(c => [c, r() < 0.4 ? 0 : r() * 30])) },
    { calls: ctx.wards.map(() => (r() < 0.2 ? null : pick(ctx.codes))), share: {} }, // a torn draft
  ];
  let { state } = B.startState(ctx, pick(starts), likely);
  const hist = new B.History();
  const seen = [state];
  const ops = [];
  for (let k = 0; k < steps; k++) {
    const op = Math.floor(r() * 7);
    const c = pick(ctx.codes);
    if (op === 0) {
      const pct = pick([0, 100, -5, 250, NaN, 1e-7, r() * 100, r() * 3, r() * 60]);
      hist.push(state); state = B.setPercent(state, ctx, c, pct).state; ops.push(`set ${c} ${pct}`);
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
      hist.push(state); state = B.setVotes(state, ctx, c, B.floorsOf(state.calls, ctx)[c]).state; ops.push(`floor ${c}`);
    } else if (op === 5) {
      const prev = hist.pop(); if (prev) { state = prev; ops.push("undo"); }
    } else {
      hist.push(state); state = { calls: state.calls, votes: B.votesFromPercent(model.combined_share, ctx) };
      state = B.setCalls(state, ctx, state.calls).state; ops.push("model shares");
    }
    seen.push(state);
  }
  return { seen, ops };
}

test("random edits: every state is valid, passes validate.js, and is seated by the seat law", () => {
  const bodies = [];
  const states = [];
  for (let seed = 1; seed <= 12; seed++) {
    const r = rng(seed * 7919);
    const { seen, ops } = walk(seed, 150);
    seen.forEach((s, k) => {
      assert.deepEqual(B.invariantErrors(s, ctx), [], `seed ${seed} after: ${ops.slice(0, k).slice(-3).join("; ")}`);
      const coalition = ctx.codes.filter(() => r() < 0.3);
      if (!coalition.length) coalition.push(ctx.codes[Math.floor(r() * ctx.codes.length)]);
      const body = B.forecastBody(s, ctx, { coalition, mayor: r() < 0.5 ? coalition[0] : null });
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
    assert.deepEqual(a.votes, nonZero(states[i].votes), `state ${i}: reader_seats counted different votes from the page's`);
  });
  // The population: every state of every walk, and it must be the whole of it.
  assert.equal(answers.length, 12 * 151);
  // It looked where it matters: states with a ward-holder sitting on the floor,
  // and states where a party holds no ward and no votes.
  const atFloor = states.filter(s => { const f = B.floorsOf(s.calls, ctx); return ctx.codes.some(c => f[c] && s.votes[c] === f[c]); }).length;
  const empty = states.filter(s => ctx.codes.some(c => s.votes[c] === 0)).length;
  assert.ok(atFloor > states.length / 20 && atFloor < states.length, `states with a ward-holder at the floor: ${atFloor}`);
  assert.ok(empty > states.length / 20, `states with a zero-vote party: ${empty}`);
  console.log(`# ${atFloor} with a ward-holder at the floor, ${empty} with a zero-vote party`);
  console.log(`# ${answers.length} states seated, all valid`);
});

test("the floor is the seat law's: one vote seats a ward-holder, zero is refused", () => {
  let { state } = B.startState(ctx, { calls: likely, share: model.combined_share }, likely);
  // A party that holds a ward.
  const holder = ctx.codes.find(c => state.calls.includes(c));
  const atFloor = B.setVotes(state, ctx, holder, 0);
  assert.equal(atFloor.clamped, "floor");
  assert.equal(atFloor.state.votes[holder], B.FLOOR_VOTES);
  // Constructed violation: the same state with the holder's vote given away.
  const other = ctx.codes.find(c => c !== holder);
  const broken = { calls: atFloor.state.calls, votes: { ...atFloor.state.votes, [holder]: 0, [other]: atFloor.state.votes[other] + B.FLOOR_VOTES } };
  assert.notDeepEqual(B.invariantErrors(broken, ctx), []);
  const bodies = [atFloor.state, broken].map(s => B.forecastBody(s, ctx, { coalition: [other] }));
  // validate.js does not look at this; the seat law does.
  for (const b of bodies) assert.ok(validateForecast(b, schema).ok);
  const [ok, refused] = seatBatch(bodies);
  assert.equal(ok.status, 200);
  assert.equal(ok.votes[holder], B.FLOOR_VOTES);
  assert.equal(refused.status, 422, "a ward-holder with no votes must be refused by the seat law");
  assert.match(refused.payload.errors.join(" "), /zero share/);
});

test("assigning a ward to a party with no votes raises it to the floor and says so", () => {
  const share = Object.fromEntries(ctx.codes.map(c => [c, 0]));
  const c0 = ctx.codes[0], c1 = ctx.codes[1];
  share[c0] = 100;
  const { state, raised } = B.startState(ctx, { calls: ctx.wards.map(() => c0), share }, likely);
  assert.deepEqual(raised, []);
  assert.equal(state.votes[c1], 0);
  const r = B.assignWards(state, ctx, [0], c1);
  assert.deepEqual(r.raised, [c1]);
  assert.equal(r.state.votes[c1], B.FLOOR_VOTES);
  assert.deepEqual(B.invariantErrors(r.state, ctx), []);
});

test("moving one party rescales the others in proportion", () => {
  const { state } = B.startState(ctx, { calls: likely, share: model.combined_share }, likely);
  const c = ctx.codes[3];
  const next = B.setPercent(state, ctx, c, 40).state;
  const others = ctx.codes.filter(x => x !== c && state.votes[x] > 1000);
  const k = others.map(x => next.votes[x] / state.votes[x]);
  for (const x of k) assert.ok(Math.abs(x - k[0]) < 1e-3, `ratios ${k}`);
  assert.equal(Object.values(next.votes).reduce((a, b) => a + b, 0), ctx.T);
});

test("undo restores calls and votes together", () => {
  const { state: s0 } = B.startState(ctx, { calls: likely, share: model.combined_share }, likely);
  const a = s0.calls[0];
  const b = ctx.codes.find(c => c !== a);
  const h = new B.History();
  h.push(s0);
  let s = B.assignWards(s0, ctx, s0.calls.map((c, i) => (c === a ? i : -1)).filter(i => i >= 0), b).state;
  h.push(s);
  s = B.setVotes(s, ctx, a, 0).state;          // a holds no ward now, so 0 is allowed
  assert.equal(s.votes[a], 0);
  h.pop();                                      // back past the vote edit
  const back = h.pop();                         // back past the ward edit
  assert.deepEqual(back, { calls: s0.calls, votes: s0.votes });
  assert.deepEqual(B.invariantErrors(back, ctx), []);
});

// B4 (owner, 2026-10-05): the one-click chips for painting wards are chosen
// by one seat-based rule for every party: seated in the reader's council or
// at its start, and the party chosen. At the published start every party
// with a seat has a chip, ActionSA among them though the start calls it for
// no ward, and no party without one does.
test("the painting chips are every seated party, by one rule, alphabetical", () => {
  const f = resolve(repo, "site/your-forecast/forecast.json");
  if (!existsSync(f)) return;          // a checkout with no built site
  const D = JSON.parse(readFileSync(f, "utf8"));
  const name = c => D.schema["x-parties"].find(p => p.code === c).name;
  const alpha = D.schema["x-parties"].map(p => p.code).sort((a, b) => name(a).localeCompare(name(b)));
  const seated = B.seatedIn(D.start.seats);
  const chips = B.chipParties(alpha, seated);
  assert.deepEqual(chips, alpha.filter(c => D.start.seats[c] > 0));
  assert.ok(chips.includes("ASA"), "ActionSA has no chip");
  assert.ok(!D.start.ward_calls.includes("ASA"), "the start calls ActionSA for a ward: the case this guards is gone");
  // the old rule, the parties that win a ward, would have left it out
  assert.ok(!alpha.filter(c => D.start.ward_calls.includes(c)).includes("ASA"));
  // every party that wins a ward on the map holds a seat, so has a chip
  for (const c of new Set(D.start.ward_calls)) assert.ok(chips.includes(c), c);
  // the party chosen keeps its chip; an unseated, unchosen party has none
  const spare = alpha.find(c => !seated.includes(c));
  assert.ok(!chips.includes(spare));
  assert.ok(B.chipParties(alpha, seated, spare).includes(spare));
  assert.deepEqual(B.seatedIn({ A: 0, B: 2 }), ["B"]);
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
  const bodies = seen.map(s => B.forecastBody(s, ctx, { coalition: [ctx.codes[0]] }));
  const cp = seatBatch(bodies);
  bodies.forEach((b, i) => {
    const r = engine.seats(b, schema);
    assert.ok(r.ok, JSON.stringify(r.errors));
    assert.deepEqual(r.answer, checkSeatAnswer(cp[i].payload, b, schema));
  });
});
