// The seat table, drawn in the browser: the JavaScript twin of src/seat_table.py.
//
// ONE component for every list of party seats on the site (owner's sweep,
// 2026-10-03). The Python renderer draws the published tables at build time;
// this one draws the same table from a reader's figures, in "play with the
// model" (js/model.js) and "make your own forecast" (js/make.js). Both write
// the SAME markup for the same rows (tests/test_seat_table.py runs this file
// under node and compares), and src/css/seat-table.css is the look. The row's
// keys are documented in src/seat_table.py.
//
// It builds elements and hands them back; it looks nothing up in the page and
// writes into no region. The module that calls it is the LIVE writer
// (stats.LIVE_WRITERS) and appends what it returns into its own region, so
// this file is scanned as a non-writer by stats.script_writes: no data block,
// no data source, no markup strings.

const SVG = "http://www.w3.org/2000/svg";

function pct(v, scale) {
  return (100 * Number(v) / scale).toFixed(2) + "%";
}

function node(doc, tag, attrs, kids) {
  const e = doc.createElement(tag);
  for (const [k, v] of attrs) e.setAttribute(k, String(v));
  for (const k of kids) e.append(k);
  return e;
}

function svgNode(doc, tag, attrs, kids) {
  const e = doc.createElementNS(SVG, tag);
  for (const [k, v] of attrs) e.setAttribute(k, String(v));
  for (const k of kids || []) e.append(k);
  return e;
}

const has = v => v !== null && v !== undefined;

// The range graphic: geometry as attributes, percent coordinates.
export function graphic(doc, row, scale) {
  const parts = [svgNode(doc, "line", [["class", "st-axis"], ["x1", "0"], ["x2", "100%"], ["y1", "10"], ["y2", "10"]])];
  if (has(row.p5) && has(row.p95))
    parts.push(svgNode(doc, "rect", [["class", "st-band"], ["x", pct(row.p5, scale)], ["y", "6"],
      ["width", pct(Number(row.p95) - Number(row.p5), scale)], ["height", "8"], ["rx", "4"]]));
  if (has(row.ghost)) {
    const x = pct(row.ghost, scale);
    parts.push(svgNode(doc, "line", [["class", "st-ghost"], ["x1", x], ["x2", x], ["y1", "0"], ["y2", "20"]]));
  }
  if (has(row.m)) {
    const x = pct(row.m, scale);
    parts.push(svgNode(doc, "line", [["class", "st-med"], ["x1", x], ["x2", x], ["y1", "2"], ["y2", "18"]]));
  }
  return svgNode(doc, "svg", [["class", "st-svg"], ["width", "100%"], ["height", "20"], ["aria-hidden", "true"]], parts);
}

// One party's row.
export function seatRow(doc, row, scale) {
  const attrs = [];
  attrs.push(["class", "st-row"], ["data-code", row.code]);
  for (const k of ["m", "p5", "p95"]) if (has(row[k])) attrs.push(["data-" + k, row[k]]);
  const label = [node(doc, "span", [["class", "pchip pc-" + row.code]], []), row.name];
  if (row.sub) label.push(node(doc, "span", [["class", "st-sub"]], [row.sub]));
  const bold = [String(row.seats)];
  if (row.arrow) bold.push(node(doc, "span", [["class", "arrow reader"]], [row.arrow]));
  const seatAttrs = [];
  seatAttrs.push(["class", "st-seats"]);
  if (row.title) seatAttrs.push(["title", row.title]);
  const range = has(row.lo) && has(row.hi) ? [row.lo + "–" + row.hi] : has(row.lo) ? [String(row.lo)] : [];
  return node(doc, "div", attrs, [
    node(doc, "div", [["class", "st-name"]], label),
    node(doc, "div", [["class", "st-graphic"]], [graphic(doc, row, scale)]),
    node(doc, "div", seatAttrs, [node(doc, "b", [], bold)]),
    node(doc, "div", [["class", "st-range"]], range),
  ]);
}

export function headRow(doc, head) {
  return node(doc, "div", [["class", "st-row st-head"]], [
    node(doc, "div", [["class", "st-name"]], [head[0]]),
    node(doc, "div", [["class", "st-graphic"]], [head[1]]),
    node(doc, "div", [["class", "st-seats"]], [head[2]]),
    node(doc, "div", [["class", "st-range"]], [head[3]]),
  ]);
}

// The axis under the rows; its numbers are chart chrome.
export function scaleRow(doc, scale, ticks) {
  const last = ticks.length - 1;
  const texts = ticks.map((t, i) => svgNode(doc, "text",
    [["x", pct(t, scale)], ["y", "11"], ["text-anchor", i === 0 ? "start" : i === last ? "end" : "middle"]], [String(t)]));
  return node(doc, "div", [["class", "st-row st-scale"]], [
    node(doc, "div", [], []),
    svgNode(doc, "svg", [["class", "ticks st-ticks"], ["width", "100%"], ["height", "14"], ["aria-hidden", "true"]], texts),
    node(doc, "div", [], []), node(doc, "div", [], []),
  ]);
}

// The whole table: header, one row per party in the order given, scale.
// opts: { scale, ticks, head: [party, graphic, seats, range words], label }.
export function seatTable(doc, rows, opts) {
  const attrs = [];
  attrs.push(["class", "st"], ["data-scale", opts.scale]);
  if (opts.label) attrs.push(["aria-label", opts.label]);
  return node(doc, "div", attrs, [headRow(doc, opts.head), ...rows.map(r => seatRow(doc, r, opts.scale)),
    scaleRow(doc, opts.scale, opts.ticks)]);
}
