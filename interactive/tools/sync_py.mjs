#!/usr/bin/env node
// Serves the project's Python to the interactive pages, which run it under
// Pyodide. Two sets, kept apart because they are two programs:
//
// THE SEAT CODE (make.html, the builder). Copied by
// worker-api/tools/sync_seats_py.mjs's own `copy` and `checkCopy`, over its own
// FILES list, so the page and the seat Worker carry the same bytes by the same
// rule; nothing about that list or its hash is restated here. Added beside it:
//
//   entry.py       the seat Worker's request handler (worker-api/seats-py/src),
//                  so the page asks the same `answer(body)` the server asks;
//
// THE PAGE CODE (model.html, "play with the model"; SPEC-v2 Lane P, F18).
// src/reweight.py and the rest of the import closure of pyboot/page.py
// (PAGE_FILES), plus the files that closure opens at run time (PAGE_DATA),
// copied into interactive/py/page/. It is NOT added to worker-api's FILES: the
// seat Worker does not run it, and tests/test_reader_seats.py holds FILES equal
// to reader_seats' own closure (F18). interactive/tests/page.test.mjs holds
// PAGE_FILES and PAGE_DATA equal to what page.py imports and opens, measured in
// a fresh interpreter, in both directions.
//
//   manifest.json  both file lists, in load order, each with its own hash
//                  (codeRef, the seat Worker's one definition): `files` and
//                  `code_ref` for the seat code, `page` for the page code. The
//                  pages read it (a browser cannot import a node module).
//
//   node interactive/tools/sync_py.mjs          copy into interactive/py/
//   node interactive/tools/sync_py.mjs --check  exit 1 if interactive/py/ is
//                                               missing, differs, or is stale
//
// interactive/py/ is gitignored, as seats-py/src/ is: run this after checkout
// and after any change to the copied code. The pages say so if it is missing.
import { readFileSync, writeFileSync, existsSync, mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { FILES, codeRef, copy, checkCopy } from "../../worker-api/tools/sync_seats_py.mjs";

const here = dirname(fileURLToPath(import.meta.url));
export const REPO = resolve(here, "../..");
export const SRC = resolve(REPO, "src");
export const DST = resolve(here, "../py");
const ENTRY = resolve(REPO, "worker-api/seats-py/src/entry.py");
export const SERVED = [...FILES, "code_ref.py", "entry.py"];

// The page's Python, in import order: pyboot/page.py imports cityconfig,
// polling and reweight; polling imports cityconfig. Measured, not argued:
// page.test.mjs fails if page.py imports a src/ module missing here or this
// names one it does not import. When Lane R's reweight.py imports more, the
// test says which.
export const PAGE_FILES = ["cityconfig.py", "polling.py", "reweight.py"];
// Files the page code opens, relative to the repository root, which is the
// page's working directory: the poll register (polling.REGISTER) and the city
// file (cityconfig.CITIES_DIR). Measured the same way, with an audit hook.
export const PAGE_DATA = ["polls.json", "cities/joburg.toml"];
export const PAGE_DST = resolve(DST, "page");
const PAGE_BOOT = resolve(REPO, "interactive/pyboot/page.py");

// What the page's hash covers: its code, its data and its entry, in that order.
function pageSources(src = SRC, repo = REPO) {
  return [...PAGE_FILES.map(f => [f, resolve(src, f)]),
          ...PAGE_DATA.map(f => [f, resolve(repo, f)]),
          ["page.py", PAGE_BOOT]];
}

export function pageRef(src = SRC, repo = REPO) {
  return codeRef(pageSources(src, repo).map(([, p]) => readFileSync(p)));
}

function manifest(src) {
  return JSON.stringify({
    _about: "Written by interactive/tools/sync_py.mjs. Do not edit.",
    files: SERVED,
    code_ref: codeRef(FILES.map(f => readFileSync(resolve(src, f)))),
    page: {
      dir: "page",
      files: PAGE_FILES,
      data: PAGE_DATA,
      boot: "pyboot/page.py",
      code_ref: pageRef(src),
    },
  }, null, 1) + "\n";
}

function checkPage(src, dst) {
  const problems = [];
  for (const [rel, s] of pageSources(src).slice(0, -1)) {
    const d = resolve(dst, "page", rel);
    if (!existsSync(s)) problems.push(`source missing: ${rel}`);
    else if (!existsSync(d)) problems.push(`not copied: interactive/py/page/${rel}`);
    else if (!readFileSync(d).equals(readFileSync(s))) problems.push(`STALE: interactive/py/page/${rel} differs from its source`);
  }
  const ref = resolve(dst, "page", "page_code_ref.py");
  if (!existsSync(ref)) problems.push("not written: interactive/py/page/page_code_ref.py");
  else if (problems.length === 0 && !readFileSync(ref, "utf8").includes(`PAGE_REF = "${pageRef(src)}"`))
    problems.push("STALE: interactive/py/page/page_code_ref.py does not name the current sources");
  return problems;
}

export function check(src = SRC, dst = DST) {
  const problems = checkCopy(src, dst);
  const e = resolve(dst, "entry.py");
  if (!existsSync(e)) problems.push("not copied: interactive/py/entry.py");
  else if (!readFileSync(e).equals(readFileSync(ENTRY))) problems.push("STALE: interactive/py/entry.py differs from worker-api/seats-py/src/entry.py");
  problems.push(...checkPage(src, dst));
  const m = resolve(dst, "manifest.json");
  if (!existsSync(m)) problems.push("not written: interactive/py/manifest.json");
  else if (problems.length === 0 && readFileSync(m, "utf8") !== manifest(src)) problems.push("STALE: interactive/py/manifest.json");
  return problems;
}

export function sync(src = SRC, dst = DST) {
  mkdirSync(dst, { recursive: true });
  copy(src, dst);
  writeFileSync(resolve(dst, "entry.py"), readFileSync(ENTRY));
  const missing = pageSources(src).filter(([, p]) => !existsSync(p)).map(([r]) => r);
  if (missing.length) throw new Error(`cannot copy the page code: ${missing.join(", ")} does not exist`);
  for (const [rel, s] of pageSources(src).slice(0, -1)) {
    const d = resolve(dst, "page", rel);
    mkdirSync(dirname(d), { recursive: true });
    writeFileSync(d, readFileSync(s));
  }
  writeFileSync(resolve(dst, "page", "page_code_ref.py"),
    `# Written by interactive/tools/sync_py.mjs. Do not edit.\nPAGE_REF = "${pageRef(src)}"\n`);
  writeFileSync(resolve(dst, "manifest.json"), manifest(src));
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  if (process.argv.includes("--check")) {
    const problems = check();
    for (const p of problems) console.error(p);
    if (problems.length) console.error("run `node interactive/tools/sync_py.mjs` to copy the Python into interactive/py/");
    else console.log(`interactive/py carries ${SERVED.length} seat files, ${PAGE_FILES.length + PAGE_DATA.length} page files and manifest.json, current`);
    process.exit(problems.length ? 1 : 0);
  }
  try { sync(); } catch (e) { console.error(e.message); process.exit(1); }
  console.log(`copied ${SERVED.join(", ")}; page: ${[...PAGE_FILES, ...PAGE_DATA].join(", ")}; manifest written`);
}
