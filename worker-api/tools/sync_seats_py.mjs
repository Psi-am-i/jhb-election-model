#!/usr/bin/env node
// Copies the project's seat code into the Python Worker, byte for byte, and
// writes code_ref.py (sha256 over the copied files, in order). Never retype
// the seat law: this copy is the only way it reaches seats-py/.
//
//   node tools/sync_seats_py.mjs          copy (refuses if a source is missing)
//   node tools/sync_seats_py.mjs --check  exit 1 if any copy is missing, differs
//                                         from src/, or code_ref.py is stale
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { createHash } from "node:crypto";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const SRC = resolve(here, "../../src");
const DST = resolve(here, "../seats-py/src");
// reader_seats.py and every project module it imports, directly or through
// montecarlo (item 16 lives there), and prediction.py (prediction.seats_of, the
// one composition of the seat law for a prediction or a reader's forecast,
// which reader_seats delegates to). tests/test_reader_seats.py holds this list
// equal to the import closure measured in a fresh interpreter, both ways, so a
// module added to or dropped from that chain turns the suite red.
// byelections.py: montecarlo imports it at module level (item 19, M4). Its
// import defines constants only and reads no file (its SA_FILE and BYE_VALUE
// are names, opened only by functions the seat path never calls), and its own
// imports are cityconfig and parties, already here.
export const FILES = ["reader_seats.py", "montecarlo.py", "seats.py", "cityconfig.py",
  "coalitions.py", "fold.py", "parties.py", "polling.py", "prediction.py",
  "byelections.py"];
// The card answer's code (/v1/card in seats-py/src/entry.py): the chance of a
// reader's council-level outcome and its badge. reweight.py has no top-level
// import from src/ (its docstring), so it is one file. Kept apart from FILES,
// which the test holds equal to reader_seats' closure.
export const CARD_FILES = ["reweight.py"];
export const ALL = [...FILES, ...CARD_FILES];

export function codeRef(bufs) {
  const h = createHash("sha256");
  for (const b of bufs) { h.update(String(b.length) + "\n"); h.update(b); }
  return h.digest("hex");
}

// Every problem with the copy in `dst` against the sources in `src`, as
// strings; empty means the copy is complete and current. A MISSING copy is a
// problem (R5 finding 16): a partial copy would deploy a seat Worker whose
// import fails, and "not copied yet" used to pass. code_ref.py must exist and
// name the hash of exactly these sources.
export function checkCopy(src = SRC, dst = DST) {
  const problems = [];
  for (const f of ALL) {
    const s = resolve(src, f), d = resolve(dst, f);
    if (!existsSync(s)) problems.push(`source missing: src/${f}`);
    else if (!existsSync(d)) problems.push(`not copied: seats-py/src/${f}`);
    else if (!readFileSync(d).equals(readFileSync(s))) problems.push(`STALE: seats-py/src/${f} differs from src/${f}`);
  }
  const ref = resolve(dst, "code_ref.py");
  if (!existsSync(ref)) problems.push("not written: seats-py/src/code_ref.py");
  else if (ALL.every(f => existsSync(resolve(src, f)))) {
    const want = codeRef(ALL.map(f => readFileSync(resolve(src, f))));
    if (!readFileSync(ref, "utf8").includes(`CODE_REF = "${want}"`)) problems.push("STALE: seats-py/src/code_ref.py does not name the current sources");
  }
  return problems;
}

export function copy(src = SRC, dst = DST) {
  const missing = ALL.filter(f => !existsSync(resolve(src, f)));
  if (missing.length) throw new Error(`cannot copy: src/${missing.join(", src/")} does not exist`);
  const bufs = ALL.map(f => readFileSync(resolve(src, f)));
  ALL.forEach((f, i) => writeFileSync(resolve(dst, f), bufs[i]));
  writeFileSync(resolve(dst, "code_ref.py"), `# Written by worker-api/tools/sync_seats_py.mjs. Do not edit.\nCODE_REF = "${codeRef(bufs)}"\n`);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  if (process.argv.includes("--check")) {
    const problems = checkCopy();
    for (const p of problems) console.error(p);
    if (problems.length) console.error("run `npm run sync:seats` to copy the seat code into seats-py/");
    else console.log(`seats-py/src carries ${ALL.length} files and code_ref.py, current`);
    process.exit(problems.length ? 1 : 0);
  }
  try { copy(); } catch (e) { console.error(e.message); process.exit(1); }
  console.log(`copied ${ALL.join(", ")}; code_ref written`);
}
