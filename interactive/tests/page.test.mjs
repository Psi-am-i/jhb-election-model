// "Play with the model": the page runs the project's Python, never a copy of it.
//
//   node --test interactive/tests/
//
// 1. The served page code is a current byte copy (tools/sync_py.mjs), and its
//    file list is the import closure of pyboot/page.py, measured in a fresh
//    interpreter, in both directions (SPEC-v2 F18). Each direction is shown to
//    see a constructed violation and to go quiet when it is reverted.
// 2. Both served sets are hashed into interactive/py/manifest.json, and one
//    changed byte changes the hash of the set it belongs to.
// 3. The native fixture (tests/native-play.json) is what the project's CPython
//    computes now, and Pyodide computes the same thing (F19).
//
// Set PYODIDE_NODE to a directory holding node_modules/pyodide (0.29.5) to run
// 3's Pyodide half; without it that test is skipped and says so.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, mkdtempSync, writeFileSync, mkdirSync, rmSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { resolve, dirname } from "node:path";
import { tmpdir } from "node:os";
import { fileURLToPath, pathToFileURL } from "node:url";
import { createRequire } from "node:module";

import { check, pageRef, PAGE_FILES, PAGE_DATA, DST, SRC, REPO } from "../tools/sync_py.mjs";
import { FILES, ALL, CARD_FILES, codeRef } from "../../worker-api/tools/sync_seats_py.mjs";

const here = dirname(fileURLToPath(import.meta.url));
const PYTHON = resolve(REPO, ".venv/bin/python");
const HARNESS = resolve(REPO, "interactive/tools/native_play.py");
const FIXTURE = JSON.parse(readFileSync(resolve(here, "native-play.json"), "utf8"));
const SETTINGS = JSON.parse(readFileSync(resolve(here, "play-settings.json"), "utf8"));
const CASES = SETTINGS.cases;
const SECTION2 = SETTINGS.section2;

// ---------- 1. the served list is the measured closure ----------

// What a list names that the measurement did not see, and the reverse.
export function listVsMeasured(listed, measured) {
  const L = new Set(listed), M = new Set(measured);
  return { unlisted: [...M].filter(x => !L.has(x)).sort(), unused: [...L].filter(x => !M.has(x)).sort() };
}

let measuredP = null;
const measured = () => (measuredP ??= JSON.parse(execFileSync(PYTHON, [HARNESS, "--measure"], { cwd: REPO, maxBuffer: 1 << 26 })));

test("the served page code is a current copy", () => {
  assert.deepEqual(check(), []);
});

test("PAGE_FILES is exactly the src/ modules page.py imports, both directions", () => {
  const m = measured();
  // 0/1: it scanned the right thing, and it looked: reweight.py is the page's
  // reason to exist, and the closure is a handful of modules, not src/ entire
  assert.ok(m.modules.includes("reweight.py"), JSON.stringify(m.modules));
  assert.ok(m.modules.length >= 1 && m.modules.length <= 12, `measured ${m.modules.length} modules`);
  assert.deepEqual(listVsMeasured(PAGE_FILES, m.modules), { unlisted: [], unused: [] });
  // 2: it can see, both ways, and goes quiet again
  assert.deepEqual(listVsMeasured([...PAGE_FILES, "montecarlo.py"], m.modules).unused, ["montecarlo.py"]);
  assert.deepEqual(listVsMeasured(PAGE_FILES.filter(f => f !== "polling.py"), m.modules).unlisted, ["polling.py"]);
  assert.deepEqual(listVsMeasured(PAGE_FILES, m.modules), { unlisted: [], unused: [] });
});

test("PAGE_DATA is exactly the files page.py opens, both directions", () => {
  // Since 2026-09-30 the page opens NO data file: the poll set arrives in
  // index.json. So both lists are empty, and the checks below show the
  // comparison still sees a file in either direction.
  const m = measured();
  assert.ok(m.opened.length <= 10, JSON.stringify(m.opened));
  assert.deepEqual(listVsMeasured(PAGE_DATA, m.opened), { unlisted: [], unused: [] });
  assert.deepEqual(listVsMeasured(PAGE_DATA, [...m.opened, "polls.json"]).unlisted, ["polls.json"]);
  assert.deepEqual(listVsMeasured([...PAGE_DATA, "cities/tshwane.toml"], m.opened).unused, ["cities/tshwane.toml"]);
});

test("the page list and the seat Worker's list are separate (F18)", () => {
  // reweight.py is the page's; the seat Worker's FILES is held to reader_seats'
  // own closure by tests/test_reader_seats.py and must not carry it
  assert.ok(!FILES.includes("reweight.py"));
  assert.ok(PAGE_FILES.includes("reweight.py"));
  // the seat Worker's card answer runs it too, from its own second list
  assert.deepEqual(CARD_FILES, ["reweight.py"]);
  assert.deepEqual(ALL, [...FILES, ...CARD_FILES]);
});

// ---------- 2. both sets hashed, and the hash sees a byte ----------

test("both served sets are hashed into the manifest, and one byte moves the right hash", () => {
  const man = JSON.parse(readFileSync(resolve(DST, "manifest.json"), "utf8"));
  assert.equal(man.code_ref, codeRef(ALL.map(f => readFileSync(resolve(SRC, f)))));
  assert.equal(man.page.code_ref, pageRef());
  assert.deepEqual(man.page.files, PAGE_FILES);
  assert.deepEqual(man.page.data, PAGE_DATA);
  assert.notEqual(man.code_ref, man.page.code_ref);

  const tmp = mkdtempSync(resolve(tmpdir(), "page-ref-"));
  try {
    const srcCopy = resolve(tmp, "src"), repoCopy = tmp;
    mkdirSync(srcCopy);
    for (const f of new Set([...FILES, ...PAGE_FILES])) writeFileSync(resolve(srcCopy, f), readFileSync(resolve(SRC, f)));
    for (const f of PAGE_DATA) { mkdirSync(dirname(resolve(repoCopy, f)), { recursive: true }); writeFileSync(resolve(repoCopy, f), readFileSync(resolve(REPO, f))); }
    assert.equal(pageRef(srcCopy, repoCopy), pageRef());
    const flip = (p) => { const b = readFileSync(p); b[b.length - 1] ^= 1; writeFileSync(p, b); return () => { b[b.length - 1] ^= 1; writeFileSync(p, b); }; };
    let undo = flip(resolve(srcCopy, "reweight.py"));
    assert.notEqual(pageRef(srcCopy, repoCopy), pageRef());
    undo();
    undo = flip(resolve(srcCopy, "polling.py"));
    assert.notEqual(pageRef(srcCopy, repoCopy), pageRef());
    undo();
    assert.equal(pageRef(srcCopy, repoCopy), pageRef());
    undo = flip(resolve(srcCopy, "seats.py"));
    assert.equal(pageRef(srcCopy, repoCopy), pageRef(), "seats.py is not page code");
    assert.notEqual(codeRef(ALL.map(f => readFileSync(resolve(srcCopy, f)))), man.code_ref);
    undo();
  } finally { rmSync(tmp, { recursive: true, force: true }); }
});

// ---------- 3. native, then Pyodide ----------

test("the stored native fixture is what CPython computes now", () => {
  const man = JSON.parse(readFileSync(resolve(DST, "manifest.json"), "utf8"));
  const index = JSON.parse(readFileSync(resolve(REPO, "site/draws/index.json"), "utf8"));
  const stale = [];
  if (FIXTURE.page_ref !== man.page.code_ref) stale.push("the page code changed");
  for (const c of index.cells) if (FIXTURE.draws[c.path] !== c.code_sha256) stale.push(`cell ${c.path} was re-exported`);
  assert.deepEqual(stale, [], "regenerate: .venv/bin/python interactive/tools/native_play.py --write");
  const now = JSON.parse(execFileSync(PYTHON, [HARNESS], { cwd: REPO, maxBuffer: 1 << 28 }));
  assert.deepEqual(now.cases, FIXTURE.cases);
  assert.deepEqual(now.section2, FIXTURE.section2);
  assert.equal(FIXTURE.section2.length, SECTION2.cases.length);
  // it looked: every case computed, the untouched one on every draw, and the
  // case beyond the draws refused rather than answered
  assert.equal(FIXTURE.cases.length, CASES.length);
  const byName = Object.fromEntries(FIXTURE.cases.map(c => [c.name, c.result]));
  assert.equal(byName.untouched.effective_draws, byName.untouched.draws);
  assert.ok(byName["beyond-the-draws"].refused);
  assert.ok(Object.keys(byName.untouched.seats).length >= 5);
});

// Every numeric leaf compared; structure, strings, booleans and nulls must
// match exactly. Returns the largest RELATIVE difference, the figures the
// page shows that are not bit-identical, and the leaves in the degenerate
// regime below.
//
// The degenerate regime, measured 2026-09-30: for a quantile with every draw
// on its own side (a party's p95 of zero seats, say), reweight's
// `quantile_effective_draws` computes P(1-P)/V with P one ulp from 1 and V a
// few ulps above 0. The exact answer is (0, nan); what comes out is summation
// dust (level_se ~1e-16, effective draws ~1e17), and CPython's numpy and
// Pyodide's order the sums differently. A finding for src/reweight.py, not a
// difference in the page's figures: the page shows neither field, and such a
// leaf is accepted only when level_se is below DUST on both sides.
const DUST = 1e-12;
const DUST_FIELDS = new Set(["level_se", "quantile_effective_draws"]);
// (V exactly 0 on one side gives the exact answer, level_se null and 0 draws,
// against dust on the other; that is the same regime.)
const degenerate = p => p && (p.level_se === null || Math.abs(p.level_se) < DUST);
export function compareLeaves(a, b, path = "", out = { maxRel: 0, where: "", exactMiss: [], dust: 0 }, pa = null, pb = null) {
  const field = path.split(".").at(-1);
  if (a !== b && DUST_FIELDS.has(field) && degenerate(pa) && degenerate(pb)) {
    out.dust++;
    return out;
  }
  if (typeof a === "number" && typeof b === "number") {
    if (a === b) return out;
    const rel = Math.abs(a - b) / Math.max(Math.abs(a), Math.abs(b));
    if (rel > out.maxRel) { out.maxRel = rel; out.where = path; }
    if (/\.(value|effective_draws|majority|council)$/.test(path)) out.exactMiss.push(path);
    return out;
  }
  if (a === null || b === null || typeof a !== "object" || typeof b !== "object") {
    assert.deepEqual(a, b, `at ${path}`);
    return out;
  }
  assert.deepEqual(Object.keys(a).sort(), Object.keys(b).sort(), `keys at ${path}`);
  for (const k of Object.keys(a)) compareLeaves(a[k], b[k], `${path}.${k}`, out, a, b);
  return out;
}

test("the comparison sees a difference and tolerates only the named dust", () => {
  const f = { value: 3, level_se: 1e-16, quantile_effective_draws: 4e17 };
  const g = { value: 3, level_se: 2e-16, quantile_effective_draws: 9e17 };
  assert.deepEqual(compareLeaves({ x: f }, { x: g }), { maxRel: 0, where: "", exactMiss: [], dust: 2 });
  assert.equal(compareLeaves({ x: f }, { x: { value: 3, level_se: null, quantile_effective_draws: 0 } }).dust, 2);
  assert.throws(() => compareLeaves({ x: { value: 3, level_se: 0.01 } }, { x: { value: 3, level_se: null } }));
  assert.deepEqual(compareLeaves({ x: { ...f, value: 3.5 } }, { x: g }).exactMiss, [".x.value"]);
  const h = { value: 3, level_se: 0.01, quantile_effective_draws: 900 };
  assert.ok(compareLeaves({ x: h }, { x: { ...h, quantile_effective_draws: 901 } }).maxRel > 1e-4);
  assert.throws(() => compareLeaves({ x: { withheld: true } }, { x: { withheld: false } }));
});

test("the page's engine under Pyodide gives the native answer (F19)", { skip: !process.env.PYODIDE_NODE && "PYODIDE_NODE not set" }, async () => {
  const req = createRequire(resolve(process.env.PYODIDE_NODE, "package.json"));
  // Constructed cells served beside the real ones (G3's node leg, below).
  const CONSTRUCTED = new Map();
  const mod = await import(pathToFileURL(req.resolve("pyodide")).href);
  const loadPyodide = mod.loadPyodide ?? mod.default.loadPyodide;
  const { loadReweightEngine } = await import("../js/reweight-engine.js");
  const t0 = performance.now();
  const engine = await loadReweightEngine({
    loadPyodide: ({ indexURL, ...opts }) => loadPyodide({ ...opts, packageBaseUrl: indexURL,
      packageCacheDir: dirname(req.resolve("pyodide")) }),
    readText: async rel => readFileSync(resolve(REPO, "interactive", rel), "utf8"),
    readBytes: async rel => CONSTRUCTED.get(rel) ?? new Uint8Array(readFileSync(resolve(REPO, rel))),
  });
  console.log(`# node Pyodide load: ${Math.round(performance.now() - t0)} ms`, engine.times);
  assert.deepEqual(engine.polls, FIXTURE.polls);
  const ids = engine.polls.map(p => p.id);
  let compared = 0;
  for (const c of CASES) {
    const s = { ...c.settings, polls: c.settings.polls === "*" ? ids : c.settings.polls };
    const t = performance.now();
    const got = await engine.compute(s);
    const want = FIXTURE.cases.find(x => x.name === c.name).result;
    const d = compareLeaves(got, want);
    compared++;
    console.log(`# ${c.name}: max relative |pyodide - native| = ${d.maxRel}${d.where ? " at " + d.where : ""}; ` +
      `${d.exactMiss.filter(p => p.endsWith(".value")).length} seat figure(s) and ` +
      `${d.exactMiss.filter(p => !p.endsWith(".value")).length} effective-draw count(s) not bit-identical; ${d.dust} degenerate-tail leaves (${Math.round(performance.now() - t)} ms)`);
    // the untouched page is the published forecast: every figure it shows is
    // bit-identical (uniform weights reduce to np.percentile)
    if (c.name === "untouched") assert.deepEqual(d.exactMiss, []);
    assert.ok(d.maxRel <= 1e-9, `${c.name}: ${d.maxRel} at ${d.where}`);
  }
  assert.equal(compared, CASES.length);
  // section 2's hand-off and analysis: the prediction (ward calls and both
  // ballots' whole votes, rule A) and every share and chance as CPython gives
  // them. The hand-off carries no seats; the analysis is given each party's
  // called wards as its council, as native_play.py's held_wards gives it.
  const byName = Object.fromEntries(CASES.map(c => [c.name, c.settings]));
  for (const want of FIXTURE.section2) {
    const h = await engine.handoff({ settings: byName[want.name] });
    assert.deepEqual([h.ward_calls, h.ward_votes, h.list_votes],
                     [want.handoff.ward_calls, want.handoff.ward_votes, want.handoff.list_votes], want.name);
    assert.equal(h.seats, undefined, "the hand-off carries no seats: they are derived");
    const seats = {};
    for (const c of Object.values(h.ward_calls)) seats[c] = (seats[c] || 0) + 1;
    const two = Object.keys(seats).sort((x, y) => seats[y] - seats[x] || (x < y ? -1 : x > y ? 1 : 0)).slice(0, 2);
    // the reader's list-ballot percent, as make.js sends it (B.percentOf "list")
    const lt = Object.values(h.list_votes).reduce((x, y) => x + y, 0);
    const share = Object.fromEntries(Object.entries(h.list_votes).map(([c, v]) => [c, 100 * v / lt]));
    assert.deepEqual(Object.keys(h).sort(), ["list_votes", "ward_calls", "ward_votes"], "the hand-off is the prediction object, nothing more");
    const a = await engine.analyse({ ward_calls: h.ward_calls, share, seats, prediction: seats, coalition: two });
    // a prediction that is not the reader's seats: a real boldest call, as CPython has it
    const pred = { ...seats, [two[0]]: seats[two[0]] - 12, [two[1]]: seats[two[1]] + 12 };
    const a2 = await engine.analyse({ ward_calls: h.ward_calls, share, seats, prediction: pred, coalition: two });
    assert.ok(a2.outcome.boldest.party, want.name + ": a call");
    for (const [got, exp, what] of [[h, want.handoff, "handoff"], [a, want.analyse, "analyse"], [a2, want.analyse_moved, "analyse (moved prediction)"]]) {
      const d = compareLeaves(got, exp);
      assert.ok(d.maxRel <= 1e-9, `${want.name} ${what}: ${d.maxRel} at ${d.where}`);
    }
  }
  // G3, under Pyodide (SPEC-A): a cell whose file carries no list_vote block
  // is refused by the hand-off, naming the block. The cell is the base cell
  // with that block cut out of both the bytes and the block table, so it is a
  // real file that unpacks; the same cell with the block kept is answered.
  const withoutList = cutBlock("site/draws", "list_vote");
  CONSTRUCTED.set("site/draws/g3-no-list-vote/manifest.json", withoutList.manifest);
  CONSTRUCTED.set("site/draws/g3-no-list-vote/base.bin", withoutList.blob);
  const refused = await engine.handoff({ settings: { cell: "g3-no-list-vote" } });
  assert.ok(refused.refused && refused.refused.includes("list_vote"), JSON.stringify(refused));
  const kept = cutBlock("site/draws", null);
  CONSTRUCTED.set("site/draws/g3-kept/manifest.json", kept.manifest);
  CONSTRUCTED.set("site/draws/g3-kept/base.bin", kept.blob);
  const answered = await engine.handoff({ settings: { cell: "g3-kept" } });
  assert.ok(!answered.refused && answered.list_votes, JSON.stringify(answered).slice(0, 200));
});

// A served cell's manifest and bytes with one block removed (or none, when
// `name` is null), offsets recomputed, as the bytes the engine would fetch.
function cutBlock(dir, name) {
  const manifest = JSON.parse(readFileSync(resolve(REPO, dir, "manifest.json"), "utf8"));
  const blob = readFileSync(resolve(REPO, dir, "base.bin"));
  const keep = manifest.blocks.filter(b => b.name !== name);
  assert.ok(name === null || keep.length === manifest.blocks.length - 1, `no ${name} block to cut`);
  const parts = [];
  let offset = 0;
  const blocks = keep.map(b => {
    parts.push(blob.subarray(b.offset, b.offset + b.nbytes));
    const out = { ...b, offset };
    offset += b.nbytes;
    return out;
  });
  const enc = new TextEncoder();
  return { manifest: enc.encode(JSON.stringify({ ...manifest, blocks })),
           blob: new Uint8Array(Buffer.concat(parts)) };
}
