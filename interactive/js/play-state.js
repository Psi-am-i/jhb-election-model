// "Your forecast", section 1 ("Adjust the model"): the reader's control
// settings, their bounds and their part of the address (SPEC-v2 F16). Pure:
// no DOM, no figures. Served with the page and imported by its LIVE writer,
// so stats.script_writes reads it as a module that may write no figure: no
// data block, no data source, no HTML and no template interpolation (string
// concatenation below, for that reason). What a setting MEANS is
// pyboot/page.py's and src/reweight.py's; this file holds only what a reader
// may set, so a hand-edited link cannot ask the engine for anything the
// controls could not.
//
// Address part (every field optional; an absent field is the published
// setting), written through yf-url.js, the page's one address writer:
//   ?t=0,0,0,0        turnout shift per group, points, in the draws' pool order
//   &p=id             the one poll chosen (owner, 2026-10-02: one at a time)
//   &k=0              how much to believe it, 0-100 (0 = the published forecast)
//   &l=deduct         seat law
//   &b=.              by-election cell: the published one, or a grid cell's path
//   &mv=<sha>         the model version the link was made against, its first
//                     MV_CHARS hex digits (enough to tell versions apart)
// The name for either share image (`n`, D7, owner 2026-10-02) is yf-url.js's,
// cleaned here by cardName, the one rule: the reader's text, at most
// NAME_MAX characters, put only in the name fields' values and on the images,
// drawn as text, never as markup.
// Commas are written bare, not as %2C, so a link stays readable.
//
// The one import is the owner's name blocklist (cardName, below). Served, it
// is the copy beside this file (build_your_forecast.BLOCKLIST_LINE).

import { BLOCKED_NAME_PATTERNS } from "../../worker-api/src/blocklist.js";

// F21: the turnout range is what was tested: ±5 points for Black African
// against a paired re-run of the model (prereg/2026-09-28-reweight-against-
// paired-rerun.md). The same range is offered for every group (no group
// singled out, DESIGN-decided §8); the page's first note says which was checked.
export const TURNOUT = { min: -5, max: 5, step: 0.5 };
export const TRUST = { min: 0, max: 100, step: 5 };
export const PUBLISHED_LAW = "deduct";
export const PUBLISHED_CELL = ".";
export const MV_CHARS = 12;
export const NAME_MAX = 24;

export function defaults(ctx) {
  return { shift: ctx.pools.map(() => 0), polls: [], trust: 0, law: PUBLISHED_LAW, cell: PUBLISHED_CELL, name: "" };
}

// Does this state differ from the published forecast's? A poll counts only
// once it is believed at all; the name is not a setting of the model, so a
// named, untouched page is the published forecast.
export function isTouched(st) {
  return st.shift.some(x => x !== 0) || (st.trust > 0 && st.polls.length > 0) ||
    st.law !== PUBLISHED_LAW || st.cell !== PUBLISHED_CELL;
}

// The name as the page keeps it: control characters (C0, C1) and the
// invisible direction and width controls dropped, so a name cannot reverse or
// hide the words drawn after it on the image (code review, 2026-10-02); runs
// of space made one; trimmed; at most NAME_MAX UTF-16 units, the unit the
// field's maxlength counts, never cutting a character in two. "" when nothing
// is left.
const INVISIBLE = /[\u0000-\u001f\u007f-\u009f\u061c\u200b-\u200f\u202a-\u202e\u2060-\u2069\ufeff]/g;
export function cleanName(s) {
  const t = String(s == null ? "" : s).replace(INVISIBLE, "").replace(/\s+/g, " ").trim();
  let out = "";
  for (const ch of t) {
    if (out.length + ch.length > NAME_MAX) break;
    out += ch;
  }
  return out.trim();
}

// The name as the page, both share sheets, the images and the site's Worker
// print it (review of the share build, 2026-10-03: one function for all of
// them): cleanName's text, or "" when the raw text is longer than NAME_MAX
// (refused whole, never cut) or when its NFKC form matches the owner's
// blocklist (worker-api/src/blocklist.js: names that pass for the site, the
// model or the IEC).
export function cardName(raw) {
  if (raw == null || String(raw).length > NAME_MAX) return "";
  const n = cleanName(raw);
  const folded = n.normalize("NFKC");
  return BLOCKED_NAME_PATTERNS.some(p => p.test(folded)) ? "" : n;
}
// Is `raw` a name the reader typed that cardName refuses for its words?
export function nameBlocked(raw) {
  return cleanName(raw) !== "" && String(raw).length <= NAME_MAX && cardName(raw) === "";
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
    const ids = [...new Set(q.get("p").split(",").filter(Boolean))];
    if (ids.length > 1) dropped.push("poll: one at a time");
    else if (ids.length === 1 && !ctx.polls.includes(ids[0])) dropped.push("poll: the link names a poll this page does not offer");
    else st.polls = ids;
  }
  if (q.has("k")) {
    const k = Number(q.get("k"));
    if (onStep(k, TRUST)) st.trust = k;
    else dropped.push("belief in the poll: needs " + TRUST.min + " to " + TRUST.max + " in steps of " + TRUST.step);
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

// May these settings be shared? Only under the law that seats the council
// (owner, 2026-10-03): the other laws are for comparison, and a shared image
// or link of a council seated under Germany's law would read as a forecast.
export function shareable(st) {
  return st.law === PUBLISHED_LAW;
}

// ---------- a slider's stops (owner, 2026-10-05: never a silent stop) ----------
// model.js bisects a slider that a figure's precision or the effective-draw
// floor stops, and records the furthest setting that passed in the
// direction it was moved: `limit` is { up, down }, each a value on the
// slider's step or null. Both hold only while every OTHER setting stays as it
// was; model.js forgets them when another control moves.

// The shaded zones beyond each stop, as fractions of the slider's track:
// [{ from, to }] with 0 <= from < to <= 1, `up` first. No zone where the stop
// is at the slider's own end.
export function stopZones(bounds, limit) {
  const span = bounds.max - bounds.min;
  const at = v => (v - bounds.min) / span;
  const out = [];
  if (limit && limit.up != null && limit.up < bounds.max) out.push({ from: at(limit.up), to: 1 });
  if (limit && limit.down != null && limit.down > bounds.min) out.push({ from: 0, to: at(limit.down) });
  return out;
}

// A value the reader dragged into a known zone, held at that zone's stop;
// any other value unchanged.
export function heldAtStop(value, limit) {
  if (limit && limit.up != null && value > limit.up) return limit.up;
  if (limit && limit.down != null && value < limit.down) return limit.down;
  return value;
}

// The limit after a stop at `reach`, moving `dir` (+1 up, -1 down), kept
// beside any stop already known the other way.
export function withStop(limit, dir, reach) {
  const next = { up: limit ? limit.up : null, down: limit ? limit.down : null };
  if (dir > 0) next.up = reach;
  else if (dir < 0) next.down = reach;
  return next;
}

// The settings pyboot/page.py computes: trust as a fraction; the poll is
// passed as chosen, and page.py gives it no weight at trust 0. The name is
// not the model's.
export function engineSettings(st) {
  return { cell: st.cell, law: st.law, shift: st.shift.slice(), polls: st.polls.slice(), trust: st.trust / 100 };
}
