// "Make your own forecast" (/make/): the address form, its validity rules, the
// share image, and the seats under Pyodide against the project's CPython.
//
//   node --test interactive/tests/
//
// Runs on the REAL start state: src/build_make.py's forecast_data(), the
// data file the build serves as make/forecast.json, computed here by the
// project's own Python. Set PYODIDE_NODE to a directory holding
// node_modules/pyodide to also run the page's seat engine under Pyodide.
import { test } from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { createRequire } from "node:module";

import * as B from "../js/builder-state.js";
import * as MS from "../js/make-state.js";
import { buildForecastCardSVG, forecastCardAlt, cardTitle } from "../js/forecast-card.js";
import { seatRequest, checkSeatAnswer } from "../../worker-api/src/seats.js";
import { check as checkServedCopy, DST as PY_DIR } from "../tools/sync_py.mjs";

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, "../..");
const PYTHON = resolve(repo, ".venv/bin/python");
const D = JSON.parse(execFileSync(PYTHON, ["-c",
  "import json, sys; sys.path.insert(0, 'src'); import build_make; print(json.dumps(build_make.forecast_data()))"],
  { cwd: repo, maxBuffer: 1 << 28 }));
const schema = D.schema;
const ctx = B.contextOf(schema);
const REF = D.context_ref;
const start = B.startState(ctx, { calls: D.start.ward_calls, share: D.start.combined_share }, D.start.ward_calls).state;

function rng(seed) {
  return () => {
    seed |= 0; seed = seed + 0x6D2B79F5 | 0;
    let t = Math.imul(seed ^ seed >>> 15, 1 | seed);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  };
}

// Random reader edits through the builder's own functions.
function walk(seed, steps) {
  const r = rng(seed);
  const pick = a => a[Math.floor(r() * a.length)];
  let s = start;
  const seen = [];
  for (let k = 0; k < steps; k++) {
    const x = r();
    if (x < 0.4) s = B.assignWards(s, ctx, [Math.floor(r() * ctx.wards.length)], pick(ctx.codes)).state;
    else if (x < 0.8) s = B.setPercent(s, ctx, pick(ctx.codes), r() < 0.2 ? r() * 0.01 : r() * 60).state;
    else if (x < 0.9) s = B.setCalls(s, ctx, s.calls.map(() => pick(ctx.codes.slice(0, 20)))).state;
    else s = B.setCalls(s, ctx, D.start.ward_calls).state;
    seen.push(s);
  }
  return seen;
}

test("the start is valid, every ward called and the vote whole", () => {
  assert.deepEqual(B.invariantErrors(start, ctx), []);
  assert.deepEqual(start.calls, D.start.ward_calls);
  assert.equal(Object.values(start.votes).reduce((a, b) => a + b, 0), ctx.T);
  assert.equal(schema["x-placeholder"], false);
});

test("an untouched forecast has no query and an empty query opens the start", () => {
  assert.equal(MS.serialize({ state: start, coalition: [], name: null }, ctx, REF, start), "");
  const p = MS.parse("", ctx, REF, start);
  assert.equal(p.state, start);
  assert.equal(p.note, null);
});

test("every state a reader can reach survives the address exactly", () => {
  const r = rng(7);
  const names = [null, "Thandi", "Nomvula Dlamini-Khumalo", "José", "O'Neill", "Ntombi 2026"];
  let longest = 0;
  for (const seed of [1, 2, 3]) {
    for (const s of walk(seed, 120)) {
      const coalition = ctx.codes.filter(() => r() < 0.04);
      const name = names[Math.floor(r() * names.length)];
      const q = MS.serialize({ state: s, coalition, name }, ctx, REF, start);
      longest = Math.max(longest, q.length);
      const back = MS.parse(q, ctx, REF, start);
      assert.equal(back.note, null, q);
      assert.deepEqual(back.state.calls, s.calls);
      assert.deepEqual(back.state.votes, s.votes);
      assert.deepEqual(back.coalition, coalition);
      assert.equal(back.name, name);
    }
  }
  console.log("# longest address query: " + longest + " characters");
  assert.ok(longest < 600, longest);
});

test("an invalid link opens the published start with a note saying why", () => {
  const s = walk(11, 30).at(-1);
  const good = MS.serialize({ state: s, coalition: [ctx.codes[3]], name: "Sipho" }, ctx, REF, start);
  const q = new URLSearchParams(good);
  const f = q.get("f");
  const with_ = (k, v) => { const c = new URLSearchParams(q); c.set(k, v); return "?" + c; };
  const bytes = Uint8Array.from(atob(f.replace(/-/g, "+").replace(/_/g, "/") + "===".slice((f.length + 3) % 4)), c => c.charCodeAt(0));
  const enc = b => btoa(String.fromCharCode(...b)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
  const tweak = fn => { const b = bytes.slice(); fn(b); return enc(b); };
  const k = bytes[0];
  // a state the builder cannot hold: a ward winner with no votes
  const voteless = { calls: s.calls.slice(), votes: { ...s.votes } };
  const loser = ctx.codes.find(c => !s.calls.includes(c) && s.votes[c] > 0);
  const donor = ctx.codes.find(c => c !== loser && s.votes[c] > 1);
  voteless.calls[0] = loser;
  voteless.votes[donor] += voteless.votes[loser];
  voteless.votes[loser] = 0;
  const cases = {
    "another version of this page": with_("v", "2"),
    "another version of the model's roster": with_("c", "000000000000"),
    "cut short": with_("f", f.slice(0, 40)),
    "extra data": with_("f", f + "AA"),
    "not in the expected letters": with_("f", f.slice(0, -2) + "!*"),
    "a ward winner is not on the roster": with_("f", tweak(b => { b[1] = 250; })),
    "a party is listed twice": with_("f", k > 1 ? tweak(b => { b[2] = b[1]; }) : f + "!"),
    "not one the seat law can seat (votes sum": with_("f", tweak(b => { b[b.length - 3] ^= 1; })),
    "holds a ward with fewer than": with_("f", MS.encode(voteless, [], ctx)),
    "its name cannot be used": with_("n", "<b>x</b>"),
    "longer than": with_("n", "x".repeat(MS.NAME_MAX + 1)),
  };
  for (const [why, link] of Object.entries(cases)) {
    const p = MS.parse(link, ctx, REF, start);
    assert.equal(p.state, start, why);
    assert.deepEqual([p.coalition, p.name], [[], null], why);
    assert.ok(p.note && p.note.includes(why), why + " -> " + p.note);
  }
  assert.equal(MS.parse(with_("n", "x".repeat(MS.NAME_MAX)), ctx, REF, start).note, null);
});

test("the name rule: text only, at most the limit", () => {
  for (const ok of ["Thandi", "Nomvula Dlamini-Khumalo", "O'Neill", "Zoë", "  two   spaces  "]) assert.ok(MS.nameRule(ok).ok, ok);
  assert.equal(MS.nameRule("  two   spaces  ").value, "two spaces");
  assert.equal(MS.nameRule("").value, null);
  for (const bad of ["<script>", "a/b", "@handle", "https://x.co", "x".repeat(25), "tab\there\u0000"]) assert.ok(!MS.nameRule(bad).ok, bad);
});

test("the share image carries the name, the map and every row, escaped", () => {
  const rows = [{ label: "DA", colour: "#1B5EA8", value: "77", n: 77 }, { label: "Others", colour: "#555", value: "6", n: 6 }];
  const map = { W: D.geometry.W, H: D.geometry.H, wards: D.geometry.wards.map(w => ({ path: w.path, fill: "#123456" })) };
  const svg = buildForecastCardSVG({ title: cardTitle("A & B"), lines: [{ text: "s" }], map, rows, rowsNote: "n", foot: ["f"] });
  assert.ok(svg.includes("A &amp; B's Election Forecast"));
  assert.equal((svg.match(/<path /g) || []).length, ctx.wards.length);
  for (const r of rows) assert.ok(svg.includes(">" + r.value + "<"), r.label);
  assert.equal(cardTitle(null), "My Election Forecast");
  assert.equal(cardTitle("James"), "James' Election Forecast");
  assert.match(forecastCardAlt({ title: cardTitle("Thandi"), lines: [{ text: "s" }], rows, foot: ["Not the model's forecast."] }), /^Thandi's Election Forecast\. s\. Seats: DA 77, Others 6\. Not the model's forecast\.$/);
});

// Seats for many bodies at once through the CPython the project runs: the
// seat Worker's handler over the served copy, and reader_seats from src/.
function seatBatch(bodies) {
  const reqs = bodies.map(b => seatRequest(b, schema));
  const script = [
    "import json, sys",
    "sys.path.insert(0, " + JSON.stringify(PY_DIR) + ")",
    "exec(open(" + JSON.stringify(resolve(repo, "interactive/pyboot/boot.py")) + ").read())",
    "out = []",
    "for r in json.load(sys.stdin):",
    "    status, payload = json.loads(seat_answer(json.dumps(r)))",
    "    out.append({'status': status, 'payload': payload})",
    "print(json.dumps(out))"].join("\n");
  return JSON.parse(execFileSync(PYTHON, ["-c", script], { input: JSON.stringify(reqs), maxBuffer: 1 << 28, cwd: repo }));
}
const bodiesOf = seen => seen.map(s => B.forecastBody(s, ctx, { coalition: [ctx.codes[0]] }));

test("CPython seats every reachable state, and the seats match the scorer's", () => {
  assert.deepEqual(checkServedCopy(), []);
  const seen = [start, ...walk(5, 40)];
  const cp = seatBatch(bodiesOf(seen));
  cp.forEach((r, i) => {
    assert.equal(r.status, 200, JSON.stringify(r.payload));
    checkSeatAnswer(r.payload, bodiesOf([seen[i]])[0], schema);
  });
  // the start seated by score_forecasts.seat_forecast (src/, not the copy)
  const native = JSON.parse(execFileSync(PYTHON, ["-c",
    "import json, sys; sys.path.insert(0, 'src'); import score_forecasts as S; d = json.load(sys.stdin); " +
    "r = S.seat_forecast(d['f'], d['schema']); print(json.dumps({k: v['total'] for k, v in r['seats'].items()}))"],
    { cwd: repo, input: JSON.stringify({ f: { ward_calls: D.start.ward_calls, combined_share: D.start.combined_share }, schema }), maxBuffer: 1 << 26 }));
  assert.deepEqual(Object.fromEntries(Object.entries(cp[0].payload.seats).filter(([, v]) => v > 0)), native);
  // the untouched page, through its own percent-to-votes step, seats exactly
  // the start the build planned (src/build_make.py start_seats)
  assert.deepEqual(native, D.start.seats);
});

test("the page's seat engine under Pyodide gives the CPython answer", { skip: !process.env.PYODIDE_NODE && "PYODIDE_NODE not set" }, async () => {
  const req = createRequire(resolve(process.env.PYODIDE_NODE, "package.json"));
  const mod = await import(pathToFileURL(req.resolve("pyodide")).href);
  const loadPyodide = mod.loadPyodide ?? mod.default.loadPyodide;
  const { loadSeatEngine } = await import("../js/seat-engine.js");
  const engine = await loadSeatEngine({
    loadPyodide: ({ indexURL, ...opts }) => loadPyodide({ ...opts, packageBaseUrl: indexURL,
      packageCacheDir: dirname(req.resolve("pyodide")) }),
    readText: async rel => readFileSync(resolve(repo, "interactive", rel), "utf8"),
  });
  const seen = [start, ...walk(9, 60)];
  const bodies = bodiesOf(seen);
  const cp = seatBatch(bodies);
  let n = 0;
  bodies.forEach((b, i) => {
    const r = engine.seats(b, schema);
    assert.ok(r.ok, JSON.stringify(r.errors));
    assert.deepEqual(r.answer, checkSeatAnswer(cp[i].payload, b, schema));
    n++;
  });
  console.log("# Pyodide = CPython on " + n + " forecasts");
});
