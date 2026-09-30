// The "play with the model" Web Worker (SPEC-v2 F11): Pyodide, numpy,
// src/reweight.py and the published draws live here, off the page's main
// thread, so a slider stays responsive while the Python computes.
//
// Messages in:   {type: "compute", seq, settings}
// Messages out:  {type: "stage", key, label, ms}
//                {type: "ready", polls, pools, cells, modelVersion, pageRef, times}
//                {type: "result", seq, result, ms}   ({type: "error", seq, message})
//                {type: "failed", message, missing}  the engine could not load
//
// Only the newest compute is answered: a request that arrives while one runs
// replaces any queued one, and the page drops a reply whose seq is stale.
import { loadReweightEngine, PageCodeMissing, PYODIDE_URL } from "./reweight-engine.js";

const INTERACTIVE = new URL("../", import.meta.url);
// The repository root in the prototype (site/draws/ beside interactive/);
// production serves the draws at /draws/ and passes that instead.
const ROOT = new URL("../../", import.meta.url);

async function get(url) {
  const r = await fetch(url);
  if (!r.ok) throw new PageCodeMissing(`${url.pathname}: HTTP ${r.status}`);
  return r;
}

let engine = null;
let queued = null;
let busy = false;

async function drain() {
  if (busy || !engine || !queued) return;
  busy = true;
  const { seq, settings } = queued;
  queued = null;
  const t = performance.now();
  try {
    const result = await engine.compute(settings);
    postMessage({ type: "result", seq, result, ms: Math.round(performance.now() - t) });
  } catch (e) {
    postMessage({ type: "error", seq, message: String(e.message || e) });
  }
  busy = false;
  drain();
}

onmessage = e => {
  if (e.data.type === "compute") { queued = e.data; drain(); }
};

(async () => {
  try {
    const { loadPyodide } = await import(/* @vite-ignore */ PYODIDE_URL + "pyodide.mjs");
    engine = await loadReweightEngine({
      loadPyodide,
      readText: async rel => (await get(new URL(rel, INTERACTIVE))).text(),
      readBytes: async rel => new Uint8Array(await (await get(new URL(rel, ROOT))).arrayBuffer()),
      onStage: (key, label, ms) => postMessage({ type: "stage", key, label, ms }),
    });
    postMessage({ type: "ready", polls: engine.polls, pools: engine.pools, cells: engine.cells, laws: engine.base.laws,
                  modelVersion: engine.modelVersion, pageRef: engine.pageRef, times: engine.times });
    drain();
  } catch (e) {
    postMessage({ type: "failed", message: String(e.message || e), missing: e instanceof PageCodeMissing });
  }
})();
