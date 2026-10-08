// "Your forecast", section 2 ("Break the model"): its part of the address
// (entry version 2: whole votes on the ward and list ballots), its validity
// rules, our prediction as decode(start.f) (guard G7), the hand-off's
// refusals (G8), the share image, and the seats under Pyodide against the
// project's CPython. The whole address, both sections and the name, is
// yf.test.mjs's.
//
//   node --test interactive/tests/
//
// Runs on the REAL start state: src/build_make.py's forecast_data(), the
// data file the build serves as your-forecast/forecast.json, computed here by the
// project's own Python. Set PYODIDE_NODE to a directory holding
// node_modules/pyodide to also run the page's seat engine under Pyodide.
import { test } from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { readFileSync, readdirSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { createRequire } from "node:module";

import * as B from "../js/builder-state.js";
import * as MS from "../js/make-state.js";
import { modelCardSVG } from "../js/share-card.js";
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
const start = MS.decode(D.start.f, ctx).state;

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
    else if (x < 0.65) s = B.setWardPercent(s, ctx, pick(ctx.codes), r() < 0.2 ? r() * 0.01 : r() * 60).state;
    else if (x < 0.8) s = B.setListGap(s, ctx, pick(ctx.codes.filter(c => !ctx.noList.has(c))), r() * 30 - 12).state;
    else if (x < 0.9) s = B.setCalls(s, ctx, s.calls.map(() => pick(ctx.codes.slice(0, 20)))).state;
    else s = B.setCalls(s, ctx, D.start.ward_calls).state;
    seen.push(s);
  }
  return seen;
}

test("the start is valid, every ward called and both ballots whole", () => {
  assert.deepEqual(B.invariantErrors(start, ctx), []);
  assert.deepEqual(start.calls, D.start.ward_calls);
  // each ballot's total is the prediction's own (rule A's sums), no schema total
  assert.equal(B.totalOf(start, "ward"), Object.values(D.start.ward_votes).reduce((a, b) => a + b, 0));
  assert.equal(B.totalOf(start, "list"), Object.values(D.start.list_votes).reduce((a, b) => a + b, 0));
  assert.equal(schema["x-total-votes"], undefined);
  assert.equal(schema["x-placeholder"], false);
});

// Guard G7, page side: the page opens on decode(start.f), which must be the
// prediction object beside it (make.js start() throws otherwise).
test("the page opens on decode(start.f), which is our prediction", () => {
  const pred = B.stateFromPrediction(ctx, D.start);
  assert.ok(MS.sameState(start, pred, ctx));
  assert.deepEqual(MS.decode(D.start.f, ctx).coalition, []);
  // it can see: a prediction with one list vote moved is not the same state
  const moved = { ...pred, list: { ...pred.list } };
  const [a, b] = ctx.codes.filter(c => moved.list[c] > 0).slice(0, 2);
  moved.list[a] -= 1; moved.list[b] += 1;
  assert.ok(!MS.sameState(start, moved, ctx));
  assert.deepEqual(D.start.out_of_bounds, B.outOfBounds(start, ctx));
});

test("encode(decode(f)) is f, byte for byte, and a flipped vote byte is refused or differs", () => {
  assert.equal(MS.encode(start, [], ctx), D.start.f);
  const r = rng(3);
  for (const s of walk(4, 40)) {
    const coalition = ctx.codes.filter(() => r() < 0.05);
    const f = MS.encode(s, coalition, ctx);
    const back = MS.decode(f, ctx);
    assert.equal(MS.encode(back.state, back.coalition, ctx), f);
  }
  // flip one bit of a vote varint (past the palette and the calls): the
  // decoder refuses the link or reads a different state, never the same one
  const bytes = Uint8Array.from(atob(D.start.f.replace(/-/g, "+").replace(/_/g, "/") + "===".slice((D.start.f.length + 3) % 4)), c => c.charCodeAt(0));
  const enc = b => btoa(String.fromCharCode(...b)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
  let seen = 0;
  for (const at of [bytes.length - 2, bytes.length - 10, bytes.length - 60, bytes.length - 120]) {
    const b = bytes.slice(); b[at] ^= 1;
    let got = null;
    try { got = MS.decode(enc(b), ctx).state; } catch (e) { got = null; }
    assert.ok(got === null || !MS.sameState(got, start, ctx), "a flipped byte read as the same prediction at " + at);
    seen++;
  }
  assert.equal(seen, 4);
});

// Every module that reads our encoded prediction (start.f) or opens a
// prediction object: the declared set (C adds the card and the sealed entry).
// A fifth consumer must join it here, with a reason.
const PREDICTION_CONSUMERS = {
  "interactive/js/builder-state.js": "defines stateFromPrediction, the one entry from a prediction object",
  "interactive/js/make.js": "the page's start (decode(start.f), checked against stateFromPrediction) and the hand-off",
  "interactive/pyboot/page.py": "the hand-off's producer: handoff returns the prediction object stateFromPrediction opens",
  "src/build_make.py": "the build block: encode_start writes start.f and refuses unless decode(f) is the object",
  "interactive/tools/share_screenshots.mjs": "opens the share fixture's prediction for the screenshots",
};
function consumersOf(files) {
  const found = new Set();
  for (const [rel, text] of files)
    if (/\bstart\.f\b|start\["f"\]|\bstateFromPrediction\b|\bencode_start\b/.test(text)) found.add(rel);
  return found;
}
const SCAN_DIRS = ["interactive/js", "interactive/pyboot", "interactive/tools", "src", "worker-api/src"];
function sourceFiles() {
  const out = [];
  for (const dir of SCAN_DIRS)
    for (const f of readdirSync(resolve(repo, dir)))
      if (/\.(m?js|py)$/.test(f)) out.push([dir + "/" + f, readFileSync(resolve(repo, dir, f), "utf8")]);
  return out;
}
test("every consumer of start.f is declared, both ways", () => {
  const files = sourceFiles();
  // it looked: the code files are a two-sided fraction of everything in the
  // scanned directories (a computed denominator, not a typed count)
  const entries = SCAN_DIRS.reduce((a, d) => a + readdirSync(resolve(repo, d)).length, 0);
  assert.ok(files.length >= 0.5 * entries && files.length <= entries, `${files.length} code files of ${entries} entries`);
  assert.deepEqual([...consumersOf(files)].sort(), Object.keys(PREDICTION_CONSUMERS).sort());
  // it can see: an undeclared reader of start.f in a copy is named
  const extra = [...files, ["src/elsewhere.js", "const x = D.start.f;"]];
  assert.ok(consumersOf(extra).has("src/elsewhere.js"));
});

// Guard G8: the hand-off arrives or says why. The decision is
// builder-state.js handoffResult, a pure function, tested here with stubbed
// hand-off results: refused, thrown, and an answer missing its list votes
// each give { ok: false } with a plain sentence naming the cause, and no
// state, so make.js's follow() leaves the reader's state where it was.
test("the hand-off arrives or says why: refused, thrown, missing a ballot", () => {
  const good = { ward_calls: Object.fromEntries(ctx.wards.map((w, i) => [w, start.calls[i]])),
                 ward_votes: D.start.ward_votes, list_votes: D.start.list_votes };
  const ok = B.handoffResult(good, ctx);
  assert.ok(ok.ok && MS.sameState(ok.state, start, ctx));
  const cases = [
    [{ refused: "too few simulations carry these settings" }, /cannot use these settings/],
    [{ threw: new Error("engine stopped") }, /did not answer/],
    [{ ward_calls: good.ward_calls, ward_votes: good.ward_votes }, /no list vote/],
    [{ ward_calls: good.ward_calls, list_votes: good.list_votes }, /no ward vote/],
  ];
  for (const [h, cause] of cases) {
    const before = JSON.stringify(start);
    const r = B.handoffResult(h, ctx);
    assert.equal(r.ok, false);
    assert.equal(r.state, undefined, "a failed hand-off brings no state");
    assert.match(r.text, cause);
    // the page's sentence is plain: the developer's detail goes to the console
    assert.ok(!/_votes|Error|stateFromPrediction/.test(r.text), r.text);
    assert.ok(r.detail.length > 0);
    assert.equal(JSON.stringify(start), before, "the state is unchanged");
  }
});

// A supplement to the test above, on make.js's source: follow() hands every
// non-ok result to followFailed, which writes the sentence; only a newer
// ticket returns in silence.
function followProblems(src) {
  const body = src.slice(src.indexOf("async function follow() {"), src.indexOf("one.reseed.addEventListener"));
  const out = [];
  if (!body.includes("async function follow() {")) return ["follow() not found"];
  if (!/if\s*\(!res\.ok\)\s*\{\s*followFailed\(res\);\s*return;\s*\}/.test(body)) out.push("a failed hand-off is not said");
  if (/catch\s*\(e\)\s*\{\s*return;/.test(body)) out.push("an engine error returns in silence");
  const fail = src.slice(src.indexOf("function followFailed("), src.indexOf("async function follow() {"));
  if (!/one\.followText\.textContent\s*=[^;]*res\.text/.test(fail) || !/one\.follow\.hidden\s*=\s*false/.test(fail))
    out.push("followFailed does not show its sentence");
  const st = src.slice(src.indexOf("async function handoffState("), src.indexOf("function followFailed("));
  if (!/B\.handoffResult\(/.test(st)) out.push("handoffState does not decide through handoffResult");
  return out;
}
test("follow() says every failed hand-off (source supplement)", () => {
  const src = readFileSync(resolve(repo, "interactive/js/make.js"), "utf8");
  assert.deepEqual(followProblems(src), []);
  assert.ok(followProblems(src.replace("if (!res.ok) { followFailed(res); return; }", "if (!res.ok) return;")).length);
  assert.ok(followProblems(src.replace("return B.handoffResult(h, ctx);", "return { ok: true, state: B.stateFromPrediction(ctx, h) };")).length);
});

test("an untouched forecast has no query and an empty query opens the start", () => {
  assert.equal(MS.serialize({ state: start, coalition: [] }, ctx, REF, start), "");
  const p = MS.parse("", ctx, REF, start);
  assert.equal(p.state, start);
  assert.equal(p.note, null);
});

test("every state a reader can reach survives the address exactly", () => {
  const r = rng(7);
  let longest = 0;
  for (const seed of [1, 2, 3]) {
    for (const s of walk(seed, 120)) {
      const coalition = ctx.codes.filter(() => r() < 0.04);
      const q = MS.serialize({ state: s, coalition }, ctx, REF, start);
      longest = Math.max(longest, q.length);
      const back = MS.parse(q, ctx, REF, start);
      assert.equal(back.note, null, q);
      assert.deepEqual(back.state.calls, s.calls);
      assert.deepEqual(back.state.ward, s.ward);
      assert.deepEqual(back.state.list, s.list);
      assert.deepEqual(back.coalition, coalition);
    }
  }
  console.log("# longest address query: " + longest + " characters");
  assert.ok(longest < 600, longest);
});

test("an invalid link opens the section at its start with a note saying why", () => {
  const s = walk(11, 30).at(-1);
  const good = MS.serialize({ state: s, coalition: [ctx.codes[3]] }, ctx, REF, start);
  const q = new URLSearchParams(good);
  const f = q.get("f");
  const with_ = (k, v) => { const c = new URLSearchParams(q); c.set(k, v); return "?" + c; };
  const bytes = Uint8Array.from(atob(f.replace(/-/g, "+").replace(/_/g, "/") + "===".slice((f.length + 3) % 4)), c => c.charCodeAt(0));
  const enc = b => btoa(String.fromCharCode(...b)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
  const tweak = fn => { const b = bytes.slice(); fn(b); return enc(b); };
  const k = bytes[0];
  // states the seat law refuses: a ward winner with no ward vote (R1), and one
  // with no list vote (R2)
  const loser = ctx.codes.find(c => !s.calls.includes(c) && s.ward[c] > 0 && s.list[c] > 0 && !ctx.noList.has(c));
  const donor = ctx.codes.find(c => c !== loser && s.ward[c] > 1 && s.list[c] > 1);
  const without = ballot => {
    const v = { calls: s.calls.slice(), ward: { ...s.ward }, list: { ...s.list } };
    v.calls[0] = loser;
    v[ballot][donor] += v[ballot][loser];
    v[ballot][loser] = 0;
    return v;
  };
  const cases = {
    "another version of this page": with_("v", "1"),
    "another version of the model's roster": with_("c", "000000000000"),
    "cut short": with_("f", f.slice(0, 40)),
    // four letters, so the result is still valid base64 whatever f's length
    // ("AA" was, or was not, depending on the start: f + "AA" can be a length
    // no base64 has)
    "extra data": with_("f", f + "AAAA"),
    "not in the expected letters": with_("f", f.slice(0, -2) + "!*"),
    "a ward winner is not on the roster": with_("f", tweak(b => { b[1] = 250; })),
    "a party is listed twice": with_("f", k > 1 ? tweak(b => { b[2] = b[1]; }) : f + "!"),
    "wins a ward with no ward vote": with_("f", MS.encode(without("ward"), [], ctx)),
    "wins a ward with no list vote": with_("f", MS.encode(without("list"), [], ctx)),
  };
  for (const [why, link] of Object.entries(cases)) {
    const p = MS.parse(link, ctx, REF, start);
    assert.equal(p.state, start, why);
    assert.deepEqual(p.coalition, [], why);
    assert.ok(p.note && p.note.includes(why), why + " -> " + p.note);
  }
  // section 1's settings and the name are not this part's: a link carrying
  // only them opens the start with no note
  for (const other of ["?t=5,0,0,0&mv=abc", "?n=Thandi", "?k=50&p=x"]) {
    const p = MS.parse(other, ctx, REF, start);
    assert.equal(p.state, start, other);
    assert.equal(p.note, null, other);
  }
});

test("the model's card draws the title, the map and every row, escaped", () => {
  // section 2's own cards are share-card.js's reader cards (share.test.mjs);
  // this is the model's card section 1 shares untouched, with a title that
  // needs escaping and the real ward boundaries
  const rows = [{ code: null, name: "DA", colour: "#1B5EA8", logo: false, value: "77", n: 77 }, { code: null, others: true, name: "Others", colour: "#555", logo: false, value: "6", n: 6 }];
  const map = { W: D.geometry.W, H: D.geometry.H, wards: D.geometry.wards.map(w => ({ path: w.path, fill: "#123456" })) };
  for (const size of ["link", "story"]) {
    const svg = modelCardSVG({ title: "A & B's settings", lines: [{ text: "s" }], map, rows, rowsNote: "n", foot: ["f"] }, {}, size);
    assert.ok(svg.includes("A &amp; B's settings"));
    const g = /<g transform="translate\([^)]*\) scale\([^)]*\)">([\s\S]*?)<\/g>/.exec(svg);
    assert.equal((g[1].match(/<path /g) || []).length, ctx.wards.length, size);
    for (const r of rows) assert.ok(svg.includes(">" + r.value + "<"), r.name);
  }
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
const bodiesOf = seen => seen.map(s => B.entryBody(s, ctx, { coalition: [ctx.codes[0]] }));

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
    { cwd: repo, input: JSON.stringify({ f: B.entryBody(start, ctx), schema }), maxBuffer: 1 << 26 }));
  assert.deepEqual(Object.fromEntries(Object.entries(cp[0].payload.seats).filter(([, v]) => v > 0)), native);
  // the untouched page seats exactly our prediction's council
  // (src/build_make.py start_state, prediction.seats_of)
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
