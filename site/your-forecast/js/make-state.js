// "Your forecast", section 2 ("Break the model"): the reader's whole forecast
// in the page's address. PURE: no DOM, no fetch, so interactive/tests drives
// it directly. Read by stats.script_writes as a NON-writer module: it puts
// nothing on a page. Its part of the address is written through yf-url.js,
// the page's one address writer, beside section 1's part and the name.
//
// Anonymous: the address is the only place a forecast is kept. Nothing is
// stored or sent, and nothing about the reader is in it except the name they
// choose to type (yf-url.js, play-state.cardName).
//
// THE FORM, version 1 (FORMAT):
//   v=1&c=<context ref>&f=<payload>
// `c` is the data file's context_ref, a hash of the roster, the wards and the
// total vote (src/build_make.py): positions in the payload mean those parties,
// those wards and those votes, so a link made against another context is
// refused rather than read as different parties. `f` is base64url of:
//   k                       palette size, one byte
//   k roster indices        one byte each: the parties that win a ward
//   ward calls              each ward's palette position, packed in
//                           ceil(log2 k) bits, wards in schema order
//   one varint per party    whole votes, roster order (LEB128)
//   m, then m roster indices    the governing coalition
// with no byte left over.
//
// The WHOLE state is written, not a difference from the start: a difference
// would change meaning when the start changes, and the start of section 2
// is section 1's hand-off, which moves with section 1's settings.
//
// VALIDITY is DESIGN-decided §14's, the builder's own (builder-state.js
// invariantErrors): every ward has a winner on the roster, the whole votes sum
// to the total, a ward winner holds at least one vote. A link that fails any
// rule opens section 2 at its start, and `note` says why.

import * as B from "./builder-state.js";

export const FORMAT = "1";
const MAX_ROSTER = 255;

function toB64url(bytes) {
  let bin = "";
  for (const b of bytes) bin += String.fromCharCode(b);
  return btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}
function fromB64url(s) {
  if (!/^[A-Za-z0-9_-]*$/.test(s)) throw new Error("the forecast in the link is not in the expected letters");
  const pad = s + "===".slice((s.length + 3) % 4);
  const bin = atob(pad.replace(/-/g, "+").replace(/_/g, "/"));
  return Uint8Array.from(bin, ch => ch.charCodeAt(0));
}

const bitsFor = k => Math.max(1, Math.ceil(Math.log2(k)));

export function encode(state, coalition, ctx) {
  if (ctx.codes.length > MAX_ROSTER) throw new Error("the roster is too long for this form");
  const idx = new Map(ctx.codes.map((c, i) => [c, i]));
  const palette = [...new Set(state.calls)].sort((a, b) => idx.get(a) - idx.get(b));
  const pos = new Map(palette.map((c, i) => [c, i]));
  const out = [palette.length, ...palette.map(c => idx.get(c))];
  const bits = bitsFor(palette.length);
  let acc = 0, n = 0;
  for (const c of state.calls) {
    acc = (acc << bits) | pos.get(c); n += bits;
    while (n >= 8) { out.push((acc >> (n - 8)) & 255); n -= 8; acc &= (1 << n) - 1; }
  }
  if (n) out.push((acc << (8 - n)) & 255);
  for (const c of ctx.codes) {
    let v = state.votes[c];
    do { let b = v % 128; v = Math.floor(v / 128); if (v) b |= 128; out.push(b); } while (v);
  }
  out.push(coalition.length, ...coalition.map(c => idx.get(c)));
  return toB64url(out);
}

export function decode(payload, ctx) {
  const bytes = fromB64url(payload);
  let at = 0;
  const take = () => {
    if (at >= bytes.length) throw new Error("the forecast in the link is cut short");
    return bytes[at++];
  };
  const k = take();
  if (k < 1) throw new Error("no party wins a ward");
  const palette = [];
  for (let i = 0; i < k; i++) {
    const j = take();
    if (j >= ctx.codes.length) throw new Error("a ward winner is not on the roster");
    palette.push(ctx.codes[j]);
  }
  if (new Set(palette).size !== k) throw new Error("a party is listed twice");
  const bits = bitsFor(k);
  const calls = [];
  let acc = 0, n = 0;
  while (calls.length < ctx.wards.length) {
    while (n < bits) { acc = (acc << 8) | take(); n += 8; }
    const p = (acc >> (n - bits)) & ((1 << bits) - 1);
    n -= bits; acc &= (1 << n) - 1;
    if (p >= k) throw new Error("a ward winner is not on the roster");
    calls.push(palette[p]);
  }
  const votes = {};
  for (const c of ctx.codes) {
    let v = 0, mul = 1, b;
    do {
      b = take();
      v += (b & 127) * mul; mul *= 128;
      if (mul > 2 ** 49) throw new Error("a vote count is too large");
    } while (b & 128);
    votes[c] = v;
  }
  const m = take();
  const coalition = [];
  for (let i = 0; i < m; i++) {
    const j = take();
    if (j >= ctx.codes.length) throw new Error("a governing party is not on the roster");
    coalition.push(ctx.codes[j]);
  }
  if (new Set(coalition).size !== m) throw new Error("a governing party is listed twice");
  if (at !== bytes.length) throw new Error("the forecast in the link has extra data");
  const state = { calls, votes };
  const bad = B.invariantErrors(state, ctx);
  if (bad.length) throw new Error("the forecast is not one the seat law can seat (" + bad[0] + ")");
  return { state, coalition };
}

export function sameState(a, b, ctx) {
  return a.calls.every((c, i) => c === b.calls[i]) && ctx.codes.every(c => a.votes[c] === b.votes[c]);
}

// The query string for a forecast: empty for the untouched start.
export function serialize({ state, coalition }, ctx, ref, start) {
  if (sameState(state, start, ctx) && !coalition.length) return "";
  const q = new URLSearchParams({ v: FORMAT, c: ref, f: encode(state, coalition, ctx) });
  return "?" + q.toString();
}

// The forecast a query string carries, or the start and a note saying why
// not; `instead` is the caller's sentence for what opens in its place.
export function parse(search, ctx, ref, start, instead = "") {
  const q = new URLSearchParams(search);
  const fresh = { state: start, coalition: [], note: null };
  if (!q.has("f") && !q.has("v")) return fresh;
  const refuse = why => ({ ...fresh, note: ("The forecast in this link could not be opened: " + why + ". " + instead).trim() });
  if (q.get("v") !== FORMAT) return refuse("it was made by another version of this page");
  if (q.get("c") !== ref) return refuse("it was made against another version of the model's roster, wards or vote total");
  let got;
  try { got = decode(q.get("f") || "", ctx); } catch (e) { return refuse(String(e.message || e)); }
  return { state: got.state, coalition: got.coalition, note: null };
}
