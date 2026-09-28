#!/usr/bin/env node
// Copies the project's seat code into the Python Worker, byte for byte, and
// writes code_ref.py (sha256 over the copied files, in order). Never retype
// the seat law: this copy is the only way it reaches seats-py/.
//
//   node tools/sync_seats_py.mjs          copy (refuses if a source is missing)
//   node tools/sync_seats_py.mjs --check  exit 1 if any copy differs from src/
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { createHash } from "node:crypto";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const SRC = resolve(here, "../../src");
const DST = resolve(here, "../seats-py/src");
export const FILES = ["seats.py", "reader_seats.py"];

export function codeRef(bufs) {
  const h = createHash("sha256");
  for (const b of bufs) { h.update(String(b.length) + "\n"); h.update(b); }
  return h.digest("hex");
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const missing = FILES.filter(f => !existsSync(resolve(SRC, f)));
  if (process.argv.includes("--check")) {
    let bad = 0;
    for (const f of FILES) {
      const d = resolve(DST, f);
      if (!existsSync(d)) { console.log(`not copied yet: ${f}`); continue; }
      if (!existsSync(resolve(SRC, f)) || !readFileSync(d).equals(readFileSync(resolve(SRC, f)))) {
        console.error(`STALE: seats-py/src/${f} differs from src/${f}`); bad++;
      }
    }
    process.exit(bad ? 1 : 0);
  }
  if (missing.length) { console.error(`cannot copy: src/${missing.join(", src/")} does not exist yet`); process.exit(1); }
  const bufs = FILES.map(f => readFileSync(resolve(SRC, f)));
  FILES.forEach((f, i) => writeFileSync(resolve(DST, f), bufs[i]));
  writeFileSync(resolve(DST, "code_ref.py"), `# Written by worker-api/tools/sync_seats_py.mjs. Do not edit.\nCODE_REF = "${codeRef(bufs)}"\n`);
  console.log(`copied ${FILES.join(", ")}; code_ref written`);
}
