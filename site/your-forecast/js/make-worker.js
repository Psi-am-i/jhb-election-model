// "Make your own forecast": the Web Worker that seats a reader's forecast.
// Pyodide, numpy and the project's seat code (js/seat-engine.js: the Worker
// API's own seatRequest, the seat Worker's own entry.answer over
// src/reader_seats.py, and the Worker API's own checkSeatAnswer) live here,
// off the page's thread, so the map and sliders stay responsive.
//
// Messages in:   {type: "init", schema}
//                {type: "seats", seq, forecast}    forecast: builder-state forecastBody
// Messages out:  {type: "stage", key, label, ms}
//                {type: "ready", codeRef, times}
//                {type: "result", seq, ok, answer, errors, ms}
//                {type: "failed", message, missing}
//
// Only the newest request is answered: one that arrives while another runs
// replaces any queued one, and the page drops a reply whose seq is stale.
import { loadSeatEngine, SeatCodeMissing } from "./seat-engine.js";

let engine = null, schema = null, queued = null;

function drain() {
  if (!engine || !queued) return;
  const { seq, forecast } = queued;
  queued = null;
  const t = performance.now();
  try {
    const r = engine.seats(forecast, schema);
    postMessage({ type: "result", seq, ok: r.ok, answer: r.answer || null, errors: r.errors || [],
                  ms: Math.round(performance.now() - t) });
  } catch (e) {
    postMessage({ type: "result", seq, ok: false, answer: null, errors: [String(e.message || e)] });
  }
}

onmessage = e => {
  const m = e.data;
  if (m.type === "init" && !schema) {
    schema = m.schema;
    loadSeatEngine({ onStage: (key, label, ms) => postMessage({ type: "stage", key, label, ms }) })
      .then(en => { engine = en; postMessage({ type: "ready", codeRef: en.codeRef, times: en.times }); drain(); })
      .catch(err => postMessage({ type: "failed", message: String(err.message || err), missing: err instanceof SeatCodeMissing }));
  } else if (m.type === "seats") {
    queued = m;
    drain();
  }
};
