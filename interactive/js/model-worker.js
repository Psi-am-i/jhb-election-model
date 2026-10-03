// The "your forecast" re-weighting Web Worker (SPEC-v2 F11): Pyodide, numpy,
// src/reweight.py and the published draws live here, off the page's main
// thread, so a slider stays responsive while the Python computes.
//
// Messages in:   {type: "compute", seq, settings}
//                {type: "call", id, fn, payload}   fn "handoff" or "analyse"
//                                                  (page.py), for section 2
// Messages out:  {type: "stage", key, label, ms}
//                {type: "ready", polls, pools, cells, laws, modelVersion, pageRef, times,
//                 byelection, parties}
//                {type: "result", seq, result, ms}   ({type: "error", seq, message})
//                {type: "answer", id, result}        ({type: "callerror", id, message})
//                {type: "failed", message, missing}  the engine could not load
//
// Only the newest compute is answered: a request that arrives while one runs
// replaces any queued one, and the page drops a reply whose seq is stale. A
// call is answered once, in order, and is never replaced.
import { loadReweightEngine, PageCodeMissing, PYODIDE_URL } from "./reweight-engine.js";

const INTERACTIVE = new URL("../", import.meta.url);
// Where the published draws are, relative to this file. In the prototype this
// file is interactive/js/ and the draws are site/draws/; served, it is
// /your-forecast/js/ and the draws are /draws/. build_your_forecast.py rewrites THIS ONE LINE
// for the served layout and refuses to build if it cannot find it exactly once.
const DRAWS = "../../site/draws/";
const DRAWS_URL = new URL(DRAWS, import.meta.url);

async function get(url) {
  const r = await fetch(url);
  if (!r.ok) throw new PageCodeMissing(`${url.pathname}: HTTP ${r.status}`);
  return r;
}

// Party names and colours, {code: {name, colour}}. Served, build_play.py
// writes parties.json beside the page from the site's one definition
// (render_sheet.NAMES and CHIPS, then parties.display_name). The prototype has
// no such file and falls back to its synthetic fixture's names; a party in
// neither is shown by its code.
async function roster() {
  for (const [rel, pick] of [["parties.json", j => j],
                             ["fixtures/placeholder-model.json", j => Object.fromEntries(j.parties.map(p => [p.code, p]))]]) {
    try {
      const r = await fetch(new URL(rel, INTERACTIVE));
      if (r.ok) return pick(await r.json());
    } catch (e) { /* the next source, or codes */ }
  }
  return {};
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

let callChain = Promise.resolve();
const callsWaiting = [];
function runCall({ id, fn, payload }) {
  callChain = callChain.then(async () => {
    try {
      if (fn !== "handoff" && fn !== "analyse") throw new Error("no call " + fn);
      postMessage({ type: "answer", id, result: await engine[fn](payload) });
    } catch (e) {
      postMessage({ type: "callerror", id, message: String(e.message || e) });
    }
  });
}

onmessage = e => {
  if (e.data.type === "compute") { queued = e.data; drain(); }
  else if (e.data.type === "call") { if (engine) runCall(e.data); else callsWaiting.push(e.data); }
};

(async () => {
  try {
    const { loadPyodide } = await import(/* @vite-ignore */ PYODIDE_URL + "pyodide.mjs");
    const partiesP = roster();
    engine = await loadReweightEngine({
      loadPyodide,
      drawsDir: ".",
      readText: async rel => (await get(new URL(rel, INTERACTIVE))).text(),
      readBytes: async rel => new Uint8Array(await (await get(new URL(rel, DRAWS_URL))).arrayBuffer()),
      onStage: (key, label, ms) => postMessage({ type: "stage", key, label, ms }),
    });
    postMessage({ type: "ready", polls: engine.polls, pools: engine.pools, cells: engine.cells, laws: engine.base.laws,
                  modelVersion: engine.modelVersion, pageRef: engine.pageRef, times: engine.times,
                  byelection: engine.byelection, parties: await partiesP });
    drain();
    for (const c of callsWaiting.splice(0)) runCall(c);
  } catch (e) {
    postMessage({ type: "failed", message: String(e.message || e), missing: e instanceof PageCodeMissing });
  }
})();
