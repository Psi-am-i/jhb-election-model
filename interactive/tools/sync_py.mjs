#!/usr/bin/env node
// Serves the project's seat code to the builder page (make.html), which runs it
// under Pyodide. The copy is made by worker-api/tools/sync_seats_py.mjs's own
// `copy` and `checkCopy`, over its own FILES list, so the page and the seat
// Worker carry the same bytes by the same rule; nothing about the list or the
// hash is restated here. Two things are added:
//
//   entry.py       the seat Worker's request handler (worker-api/seats-py/src),
//                  so the page asks the same `answer(body)` the server asks;
//   manifest.json  the file list, in import order, and code_ref, which the page
//                  reads (a browser cannot import a node module).
//
//   node interactive/tools/sync_py.mjs          copy into interactive/py/
//   node interactive/tools/sync_py.mjs --check  exit 1 if interactive/py/ is
//                                               missing, differs, or is stale
//
// interactive/py/ is gitignored, as seats-py/src/ is: run this after checkout
// and after any change to the seat code. The page says so if it is missing.
import { readFileSync, writeFileSync, existsSync, mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { FILES, codeRef, copy, checkCopy } from "../../worker-api/tools/sync_seats_py.mjs";

const here = dirname(fileURLToPath(import.meta.url));
export const SRC = resolve(here, "../../src");
export const DST = resolve(here, "../py");
const ENTRY = resolve(here, "../../worker-api/seats-py/src/entry.py");
export const SERVED = [...FILES, "code_ref.py", "entry.py"];

function manifest(src) {
  return JSON.stringify({
    _about: "Written by interactive/tools/sync_py.mjs. Do not edit.",
    files: SERVED,
    code_ref: codeRef(FILES.map(f => readFileSync(resolve(src, f)))),
  }, null, 1) + "\n";
}

export function check(src = SRC, dst = DST) {
  const problems = checkCopy(src, dst);
  const e = resolve(dst, "entry.py");
  if (!existsSync(e)) problems.push("not copied: interactive/py/entry.py");
  else if (!readFileSync(e).equals(readFileSync(ENTRY))) problems.push("STALE: interactive/py/entry.py differs from worker-api/seats-py/src/entry.py");
  const m = resolve(dst, "manifest.json");
  if (!existsSync(m)) problems.push("not written: interactive/py/manifest.json");
  else if (problems.length === 0 && readFileSync(m, "utf8") !== manifest(src)) problems.push("STALE: interactive/py/manifest.json");
  return problems;
}

export function sync(src = SRC, dst = DST) {
  mkdirSync(dst, { recursive: true });
  copy(src, dst);
  writeFileSync(resolve(dst, "entry.py"), readFileSync(ENTRY));
  writeFileSync(resolve(dst, "manifest.json"), manifest(src));
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  if (process.argv.includes("--check")) {
    const problems = check();
    for (const p of problems) console.error(p);
    if (problems.length) console.error("run `node interactive/tools/sync_py.mjs` to copy the seat code into interactive/py/");
    else console.log(`interactive/py carries ${SERVED.length} files and manifest.json, current`);
    process.exit(problems.length ? 1 : 0);
  }
  try { sync(); } catch (e) { console.error(e.message); process.exit(1); }
  console.log(`copied ${SERVED.join(", ")}; manifest written`);
}
