// Seats for a reader's forecast, from the project's own seat code running in
// the browser under Pyodide. There is no JavaScript seat law anywhere.
//
// The path is the server's, step for step (worker-api/src/seats.js):
//   seatRequest(forecast, schema)       the body the Worker sends, built by the
//                                       Worker's own function
//   entry.answer(body)                  the seat Worker's handler, which calls
//                                       src/reader_seats.py (pyboot/boot.py)
//   checkSeatAnswer(payload, ...)       the Worker's own arithmetic check
// so the seats on screen are the seats the server stores.
//
// The Python files are the served copy in interactive/py/, written by
// tools/sync_py.mjs from src/ (the same FILES list the seat Worker copies).
//
// Loading is slow (Pyodide, then numpy, then the modules), so the page paints
// first and calls loadSeatEngine() after; it reports each stage's time.

import { seatRequest, checkSeatAnswer } from "./seats.js";

// Pyodide 0.29 is Python 3.13, the interpreter the project's .venv runs.
export const PYODIDE_URL = "https://cdn.jsdelivr.net/pyodide/v0.29.5/full/";
const SEAT_DIR = "/seat";

export class SeatCodeMissing extends Error {}

// deps are injectable so a test can run this module under node:
//   loadPyodide(opts)  Pyodide's loader
//   readText(rel)      text of a file relative to interactive/ ("py/x.py")
export async function loadSeatEngine({ onStage = () => {}, loadPyodide, readText, indexURL = PYODIDE_URL } = {}) {
  const t0 = performance.now();
  const times = {};
  const mark = (k, label) => { times[k] = Math.round(performance.now() - t0); onStage(k, label, times[k]); };
  const base = new URL("../", import.meta.url);
  readText ??= async rel => {
    const r = await fetch(new URL(rel, base));
    if (!r.ok) throw new SeatCodeMissing(`${rel}: HTTP ${r.status}`);
    return r.text();
  };

  // Fetch the seat code while Pyodide boots.
  const code = (async () => {
    let manifest;
    try { manifest = JSON.parse(await readText("py/manifest.json")); }
    catch (e) {
      throw new SeatCodeMissing("The seat code is not being served (interactive/py/manifest.json is missing). " +
        "Run `node interactive/tools/sync_py.mjs` and reload.");
    }
    const files = await Promise.all(manifest.files.map(async f => [f, await readText("py/" + f)]));
    const boot = await readText("pyboot/boot.py");
    return { manifest, files, boot };
  })();

  onStage("start", "Loading Python", 0);
  if (!loadPyodide) ({ loadPyodide } = await import(/* @vite-ignore */ indexURL + "pyodide.mjs"));
  const py = await loadPyodide({ indexURL });
  mark("pyodide", "Loading numpy");
  await py.loadPackage("numpy", { messageCallback: () => {} });
  mark("numpy", "Loading the seat law");
  const { manifest, files, boot } = await code;
  py.FS.mkdirTree(SEAT_DIR);
  for (const [f, text] of files) py.FS.writeFile(`${SEAT_DIR}/${f}`, text);
  py.runPython(`import sys\nif ${JSON.stringify(SEAT_DIR)} not in sys.path: sys.path.insert(0, ${JSON.stringify(SEAT_DIR)})`);
  py.runPython(boot);
  const codeRef = py.globals.get("CODE_REF");
  if (codeRef !== manifest.code_ref) throw new Error(`the served seat code does not match its manifest (${codeRef} vs ${manifest.code_ref})`);
  const answerFn = py.globals.get("seat_answer");
  mark("import", "Ready");

  // Seats for one validated forecast body. Never throws for a refusal: returns
  // { ok:false, status, errors } so the page can say what happened.
  function seats(forecast, schema) {
    const body = seatRequest(forecast, schema);
    const [status, payload] = JSON.parse(answerFn(JSON.stringify(body)));
    if (status !== 200) return { ok: false, status, errors: payload.errors || [payload.error] };
    return { ok: true, answer: checkSeatAnswer(payload, forecast, schema) };
  }

  return { seats, codeRef, times };
}
