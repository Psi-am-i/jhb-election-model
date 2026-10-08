// The reader's prediction while it is being built. PURE: no DOM, no fetch, so
// interactive/tests drives it with random edits and checks every state it
// reaches against the server's validator and the seat law.
//
// A PREDICTION (STYLE.md rule 11; BRIEF change 13, owner 2026-10-08) holds
// what an election produces: a winner for every ward, and each party's WHOLE
// votes on the ward ballot and on the list ballot. Seats are derived by the
// seat law (src/reader_seats.py), never held here. The state is
//   { calls: [code per ward, schema ward order], ward: {code: int}, list: {code: int} }
// and each ballot's total is the sum of its votes: a prediction states its
// own totals (our prediction rule A's, a hand-off its own); nothing fixes them.
//
// VALIDITY (invariantErrors) is the seat law's refusals and nothing else:
//   * every ward has a winner on the roster;
//   * each ballot's votes are whole, non-negative, keyed by exactly the roster,
//     and total at least one vote;
//   * R1: a ward winner has at least one ward vote;
//   * R2: a ward winner with a PR list has at least one list vote, or the
//     statute would move its wards to the D term in silence (guard G14);
//   * a party the roster lists with no PR list has no list vote.
// The test suite holds R1 and R2 against reader_seats: at one vote the
// prediction seats, at zero it is refused, on each ballot.
//
// THE EDITOR'S BOUNDS (schema x-editor-bounds, src/build_make.py
// editor_bounds; JUDGEMENT-CALLS §R) limit what the EDITOR lets a reader set,
// never what is valid (SPEC-B D4): a link, a hand-off or our own prediction
// may lie outside them and still opens (outOfBounds names who). Each
// out-of-bounds value is clamped when it is next edited: every ward vote by
// the next change to any ward vote or ward call (setWardPercent rescales the
// others inside their ranges; clampToBounds after a change of calls), a list
// vote outside its gap range only when that party's gap is next set
// (setListGap; listFollow keeps a gap that is already outside where it is,
// never further out). For the
// calls on the map, with e[w] each ward's share of the expected ward vote:
//   won_e[P]   = sum of e[w] over the wards P is called for
//   floor[P]   = q_win * won_e[P] of the ward ballot, and one vote if P wins a ward
//   ceiling[P] = won_e[P] + q_run * (1 - won_e[P]) of the ward ballot
// a bound on the citywide ward vote, each ward treated alone; and each party's
// list share minus its ward share stays within [gap_min, gap_max] points.
// Every number is read from the schema; none is typed here.
//
// THE LIST FOLLOWS THE WARD: a party's list share is its ward share plus its
// own gap. Setting a ward vote rescales the others' ward votes inside their
// bounds and moves every list vote with its party's ward share, gaps kept.
// The gap is set on its own (setListGap). Parties are treated identically
// (DESIGN-decided §8): the only per-party facts used are the roster's
// no-PR-list flag, the reader's own picks and votes.

// What the builder needs from the generated schema (your-forecast/forecast.json
// "schema", written by src/build_make.py through worker-api/tools/make_schema.mjs).
export function contextOf(schema) {
  const seat = schema["x-seat-context"];
  const bounds = schema["x-editor-bounds"];
  if (!bounds || typeof bounds !== "object") throw new Error("the schema has no x-editor-bounds");
  const eWards = Object.keys(bounds.e || {});
  if (eWards.length !== seat.wards.length || !seat.wards.every(w => Object.prototype.hasOwnProperty.call(bounds.e, w)))
    throw new Error("the editor bounds' wards are not the schema's wards");
  for (const k of ["q_win", "q_run", "gap_min", "gap_max"])
    if (!Number.isFinite(bounds[k])) throw new Error("the editor bounds have no " + k);
  return {
    codes: seat.parties.slice(),
    wards: seat.wards.slice(),
    noList: new Set(seat.no_pr_list),
    model_ref: schema.properties.model_ref.enum[0],
    v: String(schema.properties.v.const),       // the entry version; make-state.js FORMAT must equal it
    bounds: { e: seat.wards.map(w => bounds.e[w]), q_win: bounds.q_win, q_run: bounds.q_run,
              gap_min: bounds.gap_min, gap_max: bounds.gap_max },
  };
}

export function wardCounts(calls) {
  const n = {};
  for (const c of calls) n[c] = (n[c] || 0) + 1;
  return n;
}

// The one-click party chips for painting wards (owner, 2026-10-05): ONE
// seat-based rule for every party. The CHIP_LIMIT parties with the most seats
// in `seats` ({party: seats}, the reader's council, or its start before the
// seat law has answered) have a chip; a tie for the last chip falls to
// `order`, which the page keeps alphabetical (DESIGN-decided §8), and the
// chips are shown in that order. Every other party is in the "More parties"
// select beside the chips.
export const CHIP_LIMIT = 8;
export function chipParties(order, seats, limit = CHIP_LIMIT) {
  const top = new Set(seatedIn(seats, order).slice(0, limit));
  return order.filter(c => top.has(c));
}

// The parties holding at least one seat in `seats` ({party: seats}), most
// seats first; a tie in `order` when given, else in `seats`' own order.
export function seatedIn(seats, order = Object.keys(seats || {})) {
  return order.filter(c => (seats || {})[c] > 0).sort((a, b) => seats[b] - seats[a]);
}

const sum = m => Object.values(m).reduce((a, b) => a + b, 0);
export const totalOf = (state, ballot) => sum(ballot === "ward" ? state.ward : state.list);

// Each party's share of the expected ward vote of the wards it is called for.
function wonE(calls, ctx) {
  const won = Object.fromEntries(ctx.codes.map(c => [c, 0]));
  calls.forEach((c, i) => { won[c] += ctx.bounds.e[i]; });
  return won;
}

// The editor's bounds on each party's WARD votes, in votes of the state's
// own ward total: { floor: {code: n}, ceil: {code: n} } (module comment).
export function wardBounds(calls, ctx, wardTotal) {
  const won = wonE(calls, ctx), held = wardCounts(calls);
  const { q_win, q_run } = ctx.bounds;
  const floor = {}, ceil = {};
  for (const c of ctx.codes) {
    floor[c] = Math.max(Math.ceil(q_win * won[c] * wardTotal), held[c] ? 1 : 0);
    ceil[c] = Math.max(floor[c], Math.floor((won[c] + q_run * (1 - won[c])) * wardTotal));
  }
  return { floor, ceil };
}

// A party's list share minus its ward share, in points.
export function gapOf(state, ctx, code) {
  return (state.list[code] / totalOf(state, "list") - state.ward[code] / totalOf(state, "ward")) * 100;
}

// Bounded largest remainder: whole numbers summing to `total`, each in
// [mins, maxes], in proportion to `weights` where the bounds allow (water
// filling: x = clamp(k * weight) with k found by bisection). Zero weight
// everywhere spreads evenly, which treats every party alike (§8). Ties in the
// remainders fall to `codes` order.
function apportion(codes, weights, total, mins, maxes) {
  const lo = codes.reduce((a, c) => a + mins[c], 0), hi = codes.reduce((a, c) => a + maxes[c], 0);
  if (lo > total || hi < total) throw new Error("no whole votes fit these bounds");
  const fill = w => {
    const at = k => codes.reduce((a, c) => a + Math.min(maxes[c], Math.max(mins[c], k * w[c])), 0);
    let a = 0, b = 1;
    for (let i = 0; i < 1000 && at(b) < total; i++) b *= 2;
    if (at(b) < total) return null;
    for (let i = 0; i < 200; i++) { const m = (a + b) / 2; if (at(m) < total) a = m; else b = m; }
    return Object.fromEntries(codes.map(c => [c, Math.min(maxes[c], Math.max(mins[c], b * w[c]))]));
  };
  const raw = fill(weights) || fill(Object.fromEntries(codes.map(c => [c, 1])));
  const out = Object.fromEntries(codes.map(c => [c, Math.min(maxes[c], Math.max(mins[c], Math.floor(raw[c])))]));
  let spare = total - codes.reduce((a, c) => a + out[c], 0);
  const order = codes.map((c, i) => [c, raw[c] - Math.floor(raw[c]), i]).sort((a, b) => b[1] - a[1] || a[2] - b[2]);
  while (spare > 0) {
    let gave = 0;
    for (const [c] of order) { if (spare <= 0) break; if (out[c] < maxes[c]) { out[c] += 1; spare -= 1; gave += 1; } }
    if (!gave) throw new Error("no whole votes fit these bounds");
  }
  while (spare < 0) {
    let took = 0;
    for (const [c] of order.slice().reverse()) { if (spare >= 0) break; if (out[c] > mins[c]) { out[c] -= 1; spare += 1; took += 1; } }
    if (!took) throw new Error("no whole votes fit these bounds");
  }
  return out;
}

// The list votes each party may hold, given its ward share on `ward` and the
// gap it had in `prev` (a state): its list share within its ward share plus
// [gap_min, gap_max] points, or within its own gap where that already lies
// outside them (an edit never takes a gap further out); one vote at least for
// a ward winner with a PR list (R2); none for a party with no PR list.
function listBounds(calls, ward, prev, ctx, Tl) {
  const Tw = sum(ward), held = wardCounts(calls);
  const { gap_min, gap_max } = ctx.bounds;
  const mins = {}, maxes = {};
  for (const c of ctx.codes) {
    if (ctx.noList.has(c)) { mins[c] = 0; maxes[c] = 0; continue; }
    const g = gapOf(prev, ctx, c), s = ward[c] / Tw;
    const r2 = held[c] ? 1 : 0;
    mins[c] = Math.min(Tl, Math.max(r2, Math.ceil((s + Math.min(gap_min, g) / 100) * Tl)));
    maxes[c] = Math.min(Tl, Math.max(mins[c], Math.floor((s + Math.max(gap_max, g) / 100) * Tl)));
  }
  return { mins, maxes };
}

// The least list vote R2 asks of each party, and the most a party with no PR
// list may hold: the bounds when the gap bounds cannot all be met.
function lawBounds(calls, ctx, Tl) {
  const held = wardCounts(calls);
  return { mins: Object.fromEntries(ctx.codes.map(c => [c, held[c] && !ctx.noList.has(c) ? 1 : 0])),
           maxes: Object.fromEntries(ctx.codes.map(c => [c, ctx.noList.has(c) ? 0 : Tl])) };
}

// The list ballot after the ward ballot moved from `prev.ward` to `ward`: each
// party's list share is its new ward share plus the gap it had, inside the gap
// bounds (listBounds), apportioned to the unchanged list total.
function listFollow(calls, prev, ward, ctx) {
  const Tw0 = sum(prev.ward), Tw = sum(ward), Tl = sum(prev.list);
  const want = Object.fromEntries(ctx.codes.map(c => [c, ctx.noList.has(c) ? 0
    : Math.max(0, ward[c] / Tw + (prev.list[c] / Tl - prev.ward[c] / Tw0))]));
  const gb = listBounds(calls, ward, prev, ctx, Tl);
  try { return apportion(ctx.codes, want, Tl, gb.mins, gb.maxes); } catch (e) {
    const lb = lawBounds(calls, ctx, Tl);
    return apportion(ctx.codes, want, Tl, lb.mins, lb.maxes);
  }
}

// Set one party's ward vote, as a percent of the ward ballot. The target is
// clamped to the party's bounds (and to what the others' bounds leave); the
// others' ward votes are rescaled inside their bounds, and every list vote
// follows its party's ward share. Returns { state, clamped: null|"floor"|"ceiling", which }.
export function setWardPercent(state, ctx, code, pct) {
  if (!ctx.codes.includes(code)) throw new Error("not on the roster: " + code);
  const Tw = totalOf(state, "ward");
  const { floor, ceil } = wardBounds(state.calls, ctx, Tw);
  const others = ctx.codes.filter(c => c !== code);
  const lo = Math.max(floor[code], Tw - others.reduce((a, c) => a + ceil[c], 0));
  const hi = Math.min(ceil[code], Tw - others.reduce((a, c) => a + floor[c], 0));
  const want = Math.round(Number(pct) / 100 * Tw);
  const v = Math.max(lo, Math.min(hi, Number.isFinite(want) ? want : state.ward[code]));
  const rest = apportion(others, state.ward, Tw - v, floor, ceil);
  const ward = Object.fromEntries(ctx.codes.map(c => [c, c === code ? v : rest[c]]));
  const list = listFollow(state.calls, state, ward, ctx);
  const clamped = v !== want ? (want < v ? "floor" : "ceiling") : null;
  return { state: { calls: state.calls, ward, list }, clamped, which: clamped ? code : null };
}

// Set one party's list vote as its ward share plus `points`. The points are
// clamped to [gap_min, gap_max]; the other parties' list votes are rescaled in
// proportion, each inside its own gap bounds (listBounds); if they cannot all
// stay inside, the change asked for is reduced to the largest that lets them.
// Returns { state, clamped: null|"gap_min"|"gap_max"|"others" }.
export function setListGap(state, ctx, code, points) {
  if (!ctx.codes.includes(code)) throw new Error("not on the roster: " + code);
  if (ctx.noList.has(code)) throw new Error(code + " has no PR list");
  const { gap_min, gap_max } = ctx.bounds;
  const now = gapOf(state, ctx, code);
  const asked = Number(points);
  const target = Math.max(gap_min, Math.min(gap_max, Number.isFinite(asked) ? asked : now));
  const Tl = totalOf(state, "list"), Tw = totalOf(state, "ward");
  const { mins, maxes } = listBounds(state.calls, state.ward, state, ctx, Tl);
  const others = ctx.codes.filter(c => c !== code);
  const tryGap = g => {
    const lo = Math.max(lawBounds(state.calls, ctx, Tl).mins[code], Tl - others.reduce((a, c) => a + maxes[c], 0));
    const hi = Tl - others.reduce((a, c) => a + mins[c], 0);
    if (lo > hi) return null;
    // whole votes inside the gap bounds: rounding never takes the party out
    const s = state.ward[code] / Tw;
    const inside = Math.min(Math.floor((s + gap_max / 100) * Tl), Math.max(Math.ceil((s + gap_min / 100) * Tl),
      Math.round((s + g / 100) * Tl)));
    const mine = Math.max(lo, Math.min(hi, inside));
    try {
      const rest = apportion(others, state.list, Tl - mine, mins, maxes);
      return Object.fromEntries(ctx.codes.map(c => [c, c === code ? mine : rest[c]]));
    } catch (e) { return null; }
  };
  let list = tryGap(target), clamped = target !== asked ? (asked < target ? "gap_min" : "gap_max") : null;
  if (!list) {
    let ok = now, bad = target;
    for (let i = 0; i < 40; i++) { const m = (ok + bad) / 2; if (tryGap(m)) ok = m; else bad = m; }
    list = tryGap(ok) || { ...state.list };
    clamped = "others";
  }
  return { state: { calls: state.calls, ward: { ...state.ward }, list }, clamped };
}

// Bring every party's ward vote inside its bounds for the calls on the map
// (others rescaled), the list following; and give a ward winner the one ward
// and list vote R1 and R2 need. Returns { state, moved }: the codes whose ward
// vote was outside its bounds, for the page's note.
export function clampToBounds(state, ctx) {
  const Tw = totalOf(state, "ward");
  const { floor, ceil } = wardBounds(state.calls, ctx, Tw);
  const moved = ctx.codes.filter(c => state.ward[c] < floor[c] || state.ward[c] > ceil[c]);
  const mins = lawBounds(state.calls, ctx, totalOf(state, "list")).mins;
  if (!moved.length && ctx.codes.every(c => state.list[c] >= mins[c]))
    return { state: { calls: state.calls, ward: { ...state.ward }, list: { ...state.list } }, moved };
  const ward = moved.length ? apportion(ctx.codes, state.ward, Tw, floor, ceil) : { ...state.ward };
  const list = listFollow(state.calls, state, ward, ctx);
  return { state: { calls: state.calls, ward, list }, moved };
}

// Give wards to a party, then clampToBounds.
export function assignWards(state, ctx, indices, code) {
  if (!ctx.codes.includes(code)) throw new Error("not on the roster: " + code);
  const calls = state.calls.slice();
  for (const i of indices) {
    if (!(i >= 0 && i < calls.length)) throw new Error("no ward at index " + i);
    calls[i] = code;
  }
  return clampToBounds({ calls, ward: state.ward, list: state.list }, ctx);
}

// Replace every ward's winner at once (the model's map, an area fill).
export function setCalls(state, ctx, calls) {
  return clampToBounds({ calls: checkCalls(calls, ctx), ward: state.ward, list: state.list }, ctx);
}

function checkCalls(calls, ctx) {
  if (!Array.isArray(calls) || calls.length !== ctx.wards.length) throw new Error("one winner per ward is needed");
  for (const c of calls) if (!ctx.codes.includes(c)) throw new Error("not on the roster: " + c);
  return calls.slice();
}

// THE ONE ENTRY FROM A PREDICTION OBJECT (src/prediction.py's shape): the
// build's start and section 1's hand-off. `pred` = { ward_calls, ward_votes,
// list_votes }, ward_calls a schema-ordered list or {ward: code}. Throws,
// naming the field, on anything missing, extra or invalid. No fallback calls,
// no even spread: a prediction arrives whole or says why it did not.
export function stateFromPrediction(ctx, pred) {
  if (!pred || typeof pred !== "object") throw new Error("the prediction is not an object");
  for (const k of ["ward_calls", "ward_votes", "list_votes"])
    if (pred[k] == null) throw new Error("the prediction has no " + k);
  const wc = pred.ward_calls;
  let calls;
  if (Array.isArray(wc)) calls = wc.slice();
  else if (typeof wc === "object") {
    const extra = Object.keys(wc).filter(w => !ctx.wards.includes(w));
    if (extra.length) throw new Error("the prediction's ward_calls name wards not on the map: " + extra.slice(0, 5).join(", "));
    const missing = ctx.wards.filter(w => !(w in wc));
    if (missing.length) throw new Error("the prediction's ward_calls have no winner for ward " + missing.slice(0, 5).join(", "));
    calls = ctx.wards.map(w => wc[w]);
  } else throw new Error("the prediction's ward_calls are neither a list nor a map");
  const votes = name => {
    const m = pred[name];
    if (typeof m !== "object" || Array.isArray(m)) throw new Error("the prediction's " + name + " is not a map");
    const extra = Object.keys(m).filter(c => !ctx.codes.includes(c));
    if (extra.length) throw new Error("the prediction's " + name + " name parties off the roster: " + extra.join(", "));
    const missing = ctx.codes.filter(c => !(c in m));
    if (missing.length) throw new Error("the prediction's " + name + " lack " + missing.slice(0, 5).join(", "));
    return Object.fromEntries(ctx.codes.map(c => [c, m[c]]));
  };
  const state = { calls, ward: votes("ward_votes"), list: votes("list_votes") };
  const bad = invariantErrors(state, ctx);
  if (bad.length) throw new Error("the prediction is not one the seat law can seat: " + bad[0]);
  return state;
}

// What section 2 does with section 1's hand-off (page.py handoff), as a pure
// decision so it can be tested without a page (guard G8): `h` is the engine's
// answer, `{ refused }`, or `{ threw: error }`. Returns { ok: true, state } or
// { ok: false, text, detail }: `text` is the plain cause the page shows,
// `detail` the developer's message, for the console only. Nothing is filled
// in: a hand-off missing a ballot, a party or a ward is a failure.
export function handoffResult(h, ctx) {
  if (h && h.threw) return { ok: false, text: "the model did not answer", detail: String(h.threw.message || h.threw) };
  if (h && h.refused) return { ok: false, text: "the model cannot use these settings, and says why beside them", detail: String(h.refused) };
  try {
    return { ok: true, state: stateFromPrediction(ctx, h) };
  } catch (e) {
    const m = /has no (ward|list)_votes/.exec(String(e.message));
    return { ok: false, text: m ? "the model's answer had no " + m[1] + " vote" : "the model's answer was incomplete",
             detail: String(e.message || e) };
  }
}

// The parties outside the editor's bounds: [{ code, ballot, kind, have, bound }],
// `have` and `bound` in votes for the ward ballot and in points for a gap. Not
// an error: such a state is valid. A ward vote outside its range is clamped by
// the next change to any ward vote or call; a gap, when that party's gap is
// next set (module comment).
export function outOfBounds(state, ctx) {
  const Tw = totalOf(state, "ward");
  const { floor, ceil } = wardBounds(state.calls, ctx, Tw);
  const { gap_min, gap_max } = ctx.bounds;
  const out = [];
  for (const c of ctx.codes) {
    const v = state.ward[c];
    if (v < floor[c]) out.push({ code: c, ballot: "ward", kind: "floor", have: v, bound: floor[c] });
    if (v > ceil[c]) out.push({ code: c, ballot: "ward", kind: "ceiling", have: v, bound: ceil[c] });
    if (ctx.noList.has(c)) continue;
    const g = gapOf(state, ctx, c);
    if (g < gap_min) out.push({ code: c, ballot: "list", kind: "gap_min", have: g, bound: gap_min });
    if (g > gap_max) out.push({ code: c, ballot: "list", kind: "gap_max", have: g, bound: gap_max });
  }
  return out;
}

// Each party's percent of one ballot ("ward" or "list"), of that ballot's own total.
export function percentOf(state, ctx, ballot) {
  if (ballot !== "ward" && ballot !== "list") throw new Error("percentOf needs a ballot, ward or list");
  const m = ballot === "ward" ? state.ward : state.list, T = sum(m);
  return Object.fromEntries(ctx.codes.map(c => [c, m[c] / T * 100]));
}

// The entry the site stores and the server validates: exactly the keys
// worker-api/src/validate.js accepts, entry version FORMAT.
export function entryBody(state, ctx, { coalition = [], mayor = null, display_name = null } = {}) {
  return {
    v: ctx.v,
    model_ref: ctx.model_ref,
    ward_calls: state.calls.slice(),
    ward_votes: Object.fromEntries(ctx.codes.map(c => [c, state.ward[c]])),
    list_votes: Object.fromEntries(ctx.codes.map(c => [c, state.list[c]])),
    coalition: coalition.slice(),
    mayor: mayor || null,
    display_name: display_name || null,
  };
}

// Every broken invariant, as sentences. Empty means valid (module comment).
export function invariantErrors(state, ctx) {
  const e = [];
  if (!Array.isArray(state.calls) || state.calls.length !== ctx.wards.length) e.push("not one winner per ward");
  else state.calls.forEach((c, i) => { if (!ctx.codes.includes(c)) e.push("ward " + ctx.wards[i] + " has no winner on the roster"); });
  for (const [name, m] of [["ward", state.ward], ["list", state.list]]) {
    if (!m || typeof m !== "object") { e.push("no " + name + " votes"); continue; }
    const keys = Object.keys(m);
    if (keys.length !== ctx.codes.length || !ctx.codes.every(c => Object.prototype.hasOwnProperty.call(m, c)))
      e.push(name + " votes are not keyed by exactly the roster");
    let t = 0;
    for (const c of ctx.codes) {
      const v = m[c];
      if (!Number.isSafeInteger(v) || v < 0) e.push(c + ": " + v + " is not a whole number of " + name + " votes");
      else t += v;
    }
    if (!(t >= 1)) e.push("the " + name + " ballot holds no vote");
  }
  if (!e.length) {
    const held = wardCounts(state.calls);
    for (const c of ctx.codes) {
      if (held[c] && state.ward[c] < 1) e.push(c + " wins a ward with no ward vote");
      if (held[c] && !ctx.noList.has(c) && state.list[c] < 1) e.push(c + " wins a ward with no list vote");
      if (ctx.noList.has(c) && state.list[c] > 0) e.push(c + " has no PR list and may hold no list vote");
    }
  }
  return e;
}

// Undo keeps WHOLE states, calls and both ballots together. Keeping calls
// alone would break validity: A holds a ward at 5 votes, the ward goes to B, A
// is lowered to 0, and restoring the calls alone gives A the ward with no votes.
export class History {
  constructor(limit = 60) { this.limit = limit; this.stack = []; }
  push(state) {
    this.stack.push({ calls: state.calls.slice(), ward: { ...state.ward }, list: { ...state.list } });
    if (this.stack.length > this.limit) this.stack.shift();
  }
  pop() { return this.stack.pop() || null; }
  get size() { return this.stack.length; }
}
