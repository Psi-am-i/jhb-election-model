// "Play with the model": the reader's control settings, their bounds, and the
// share URL (SPEC-v2 F16). Pure: no DOM, no figures. Served with the page and
// imported by its LIVE writer, so stats.script_writes reads it as a module
// that may write no figure: no data block, no data source, no HTML and no
// template interpolation (string concatenation below, for that reason). What a setting MEANS is
// pyboot/page.py's and src/reweight.py's; this file holds only what a reader
// may set, so a hand-edited link cannot ask the engine for anything the
// controls could not.
//
// URL form (every field optional; an absent field is the published setting):
//   ?t=0,0,0,0        turnout shift per community, points, in the draws' pool order
//   &p=id1,id2        polls switched on
//   &k=0              trust, 0-100 (0 = the published forecast: no weight on polls)
//   &l=deduct         seat law
//   &b=.              by-election cell: the published one, or a grid cell's path
//   &mv=<sha>         the model version the link was made against, its first
//                     MV_CHARS hex digits (enough to tell versions apart)
// Commas are written bare, not as %2C, so a link stays readable.

// F21: the turnout range is what was tested: ±5 points for Black African
// against a paired re-run of the model (prereg/2026-09-28-reweight-against-
// paired-rerun.md). The same range is offered for every community (no
// community singled out, DESIGN-decided §8), and the other three are labelled
// "argued, not tested" on the page.
export const TURNOUT = { min: -5, max: 5, step: 0.5 };
export const TRUST = { min: 0, max: 100, step: 5 };
export const TESTED_POOL = "Black African";
export const PUBLISHED_LAW = "deduct";
export const PUBLISHED_CELL = ".";
export const MV_CHARS = 12;

export function defaults(ctx) {
  return { shift: ctx.pools.map(() => 0), polls: [], trust: 0, law: PUBLISHED_LAW, cell: PUBLISHED_CELL };
}

// Does this state differ from the published forecast's?
export function isTouched(st) {
  return st.shift.some(x => x !== 0) || st.trust > 0 || st.law !== PUBLISHED_LAW || st.cell !== PUBLISHED_CELL;
}

const onStep = (x, { min, max, step }) =>
  Number.isFinite(x) && x >= min && x <= max && Math.abs(x / step - Math.round(x / step)) < 1e-9;

// ctx: { pools: [names], polls: [ids], laws: [names], cells: [paths], modelVersion }
// Returns { state, dropped: [what was refused and why], otherVersion: sha|null }.
// A field out of bounds is dropped back to the published setting, never
// clamped: a clamped value is a setting the reader did not choose.
// `dropped` names the refused FIELD and what it accepts, never the value the
// link carried: the page prints these lines, and a link's text is anyone's
// (code review, 2026-10-01: "?p=ANC%20wins%2099%20seats" was echoed verbatim).
export function parse(search, ctx) {
  const q = new URLSearchParams(search);
  const st = defaults(ctx);
  const dropped = [];
  if (q.has("t")) {
    const xs = q.get("t").split(",").map(Number);
    if (xs.length === ctx.pools.length && xs.every(x => onStep(x, TURNOUT))) st.shift = xs;
    else dropped.push("turnout: needs " + ctx.pools.length + " values from " + TURNOUT.min + " to " + TURNOUT.max + " in steps of " + TURNOUT.step);
  }
  if (q.has("p")) {
    const ids = q.get("p").split(",").filter(Boolean);
    const known = ids.filter(id => ctx.polls.includes(id));
    if (known.length !== ids.length) dropped.push("polls: the link names a poll this page does not offer");
    st.polls = [...new Set(known)];
  }
  if (q.has("k")) {
    const k = Number(q.get("k"));
    if (onStep(k, TRUST)) st.trust = k;
    else dropped.push("trust: needs " + TRUST.min + " to " + TRUST.max + " in steps of " + TRUST.step);
  }
  if (q.has("l")) {
    if (ctx.laws.includes(q.get("l"))) st.law = q.get("l");
    else dropped.push("seat law: needs one of " + ctx.laws.join(", "));
  }
  if (q.has("b")) {
    if (ctx.cells.includes(q.get("b"))) st.cell = q.get("b");
    else dropped.push("by-election weight: not one this page offers");
  }
  // The link's version must be this model's first MV_CHARS characters
  // exactly: a shorter prefix would match more than one version.
  const mv = q.get("mv");
  return { state: st, dropped, otherVersion: mv != null && mv !== String(ctx.modelVersion).slice(0, MV_CHARS) ? mv : null };
}

// Only fields that differ from the published setting are written, plus mv.
export function serialize(st, ctx) {
  const q = new URLSearchParams();
  if (st.shift.some(x => x !== 0)) q.set("t", st.shift.join(","));
  if (st.polls.length) q.set("p", st.polls.join(","));
  if (st.trust) q.set("k", String(st.trust));
  if (st.law !== PUBLISHED_LAW) q.set("l", st.law);
  if (st.cell !== PUBLISHED_CELL) q.set("b", st.cell);
  if ([...q.keys()].length) q.set("mv", String(ctx.modelVersion).slice(0, MV_CHARS));
  const s = q.toString().replace(/%2C/g, ",");
  return s ? "?" + s : "";
}

// The settings pyboot/page.py computes: trust as a fraction; the polls are
// passed as switched on, and page.py gives them no weight at trust 0.
export function engineSettings(st) {
  return { cell: st.cell, law: st.law, shift: st.shift.slice(), polls: st.polls.slice(), trust: st.trust / 100 };
}
