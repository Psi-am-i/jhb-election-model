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
// others inside their limits; clampToBounds after a change of calls), a list
// vote outside its gap range only when that party's gap is next set
// (setListGap; listFollow keeps a gap that is already outside where it is,
// never further out). Every number is read from the schema; none is typed
// here. For the calls on the map (slice B2a, SPEC-B2r2 §4-§5):
//   * each ward w and party P has a RANGE for P's share of w's ward vote:
//     ward_ranges[w][P] where P has a prior in w, else party_ranges[P]
//     (wardCell). The painted winner holds at least q_win of the ward, every
//     other party at most q_run (the shape).
//   * wardRange gives, in closed form, the least and greatest share each
//     party can hold in a ward whose winner is W, with every share in its
//     range, the shares summing to one and W at least each other party. A
//     ward whose ranges no share vector satisfies falls back to the shape
//     alone, and is named (the fallback).
//   * boxOf sums those least and greatest shares over the wards, weighted by
//     e[w], each ward's share of the expected ward vote: the BOX.
//   * limits intersects the box with each party's CITYWIDE LIMIT
//     (city_limits). Where they do not meet, the map wins: the party is held
//     at its box (a conflict, named). Where the floors sum past the whole
//     ballot, or the ceilings fall short of it, the citywide parts are eased
//     in proportion until they fit.
//   * wardLimits turns the limits into whole votes of the state's own ward
//     total, a ward winner keeping one vote (R1).
// Each party's list share minus its ward share stays within [gap_min,
// gap_max] points.
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
  const codes = seat.parties.slice();
  const range = (name, r) => {
    if (!r || !Number.isFinite(r.lo) || !Number.isFinite(r.hi) || r.lo > r.hi)
      throw new Error("the editor bounds' " + name + " is not a range");
    return [r.lo, r.hi];
  };
  const byRoster = name => {
    const m = bounds[name];
    if (!m || typeof m !== "object") throw new Error("the editor bounds have no " + name);
    const keys = Object.keys(m);
    if (keys.length !== codes.length || !codes.every(c => Object.prototype.hasOwnProperty.call(m, c)))
      throw new Error("the editor bounds' " + name + " are not keyed by exactly the roster");
    return codes.map(c => range(name + " of " + c, m[c]));
  };
  const party = byRoster("party_ranges"), city = byRoster("city_limits");
  for (const c of codes)
    if (!["local", "national", "newcomer"].includes(bounds.city_limits[c].kind))
      throw new Error("the editor bounds' city_limits of " + c + " name no kind of history");
  const cells = bounds.ward_ranges;
  if (!cells || typeof cells !== "object") throw new Error("the editor bounds have no ward_ranges");
  for (const w of Object.keys(cells)) {
    if (!seat.wards.includes(w)) throw new Error("the editor bounds' ward_ranges name a ward not on the map: " + w);
    for (const c of Object.keys(cells[w]))
      if (!codes.includes(c)) throw new Error("the editor bounds' ward_ranges name a party off the roster: " + c);
  }
  // each ward's base ranges, party by party in roster order (wardCell)
  const base = seat.wards.map(w => {
    const lo = [], hi = [];
    codes.forEach((c, k) => {
      const r = cells[w] && cells[w][c] ? cells[w][c] : party[k];
      if (!Array.isArray(r) || !Number.isFinite(r[0]) || !Number.isFinite(r[1]) || r[0] > r[1])
        throw new Error("the editor bounds' range of " + c + " in ward " + w + " is not a range");
      lo.push(r[0]); hi.push(r[1]);
    });
    return { lo, hi };
  });
  return {
    codes,
    wards: seat.wards.slice(),
    noList: new Set(seat.no_pr_list),
    model_ref: schema.properties.model_ref.enum[0],
    v: String(schema.properties.v.const),       // the entry version; make-state.js FORMAT must equal it
    bounds: { e: seat.wards.map(w => bounds.e[w]), q_win: bounds.q_win, q_run: bounds.q_run,
              gap_min: bounds.gap_min, gap_max: bounds.gap_max, base,
              city: { lo: city.map(r => r[0]), hi: city.map(r => r[1]),
                      // which history each limit comes from: "local", "national" or "newcomer"
                      kind: Object.fromEntries(codes.map(c => [c, bounds.city_limits[c].kind])) } },
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

// The float tolerance of the closed form below: a comparison of two sums of
// shares, not a bound.
const EPS = 1e-12;

// The least sigma >= a with sigma + sum(min(hi_q, sigma)) >= 1: the least the
// winner can hold when every other party is capped at the winner's share.
function sigmaMin(a, his) {
  const g = x => his.reduce((t, h) => t + Math.min(h, x), x);
  if (g(a) >= 1) return a;
  const pts = his.filter(h => h > a).sort((x, y) => x - y);
  let lo = a;
  for (const b of [...pts, 1]) {
    if (g(b) >= 1) return lo + (1 - g(lo)) / (1 + his.filter(h => h > lo).length);
    lo = b;
  }
  return 1;
}

// One ward whose painted winner is party index W, each party k's share in
// [lo[k], hi[k]], the shares summing to one and W's at least each other's:
// { ok, min, max }, the least and greatest share each party can hold there
// (arrays in roster order), or { ok: false } when no share vector fits. The
// closed form of SPEC-B2 §3, checked against vertex enumeration in
// interactive/tests/builder.test.mjs.
export function wardRange(lo, hi, W) {
  const n = lo.length, oth = [];
  for (let k = 0; k < n; k++) if (k !== W) oth.push(k);
  const L = oth.reduce((t, k) => t + lo[k], 0);
  const his = oth.map(k => hi[k]);
  const a = oth.reduce((m, k) => Math.max(m, lo[k]), lo[W]);
  const smax = Math.min(hi[W], 1 - L);
  const smin = sigmaMin(a, his);
  if (smin > smax + EPS) return { ok: false };
  const capmax = oth.reduce((t, k) => t + Math.min(hi[k], smax), 0);
  // the two largest lower bounds among the others, for "the rest" of each
  let top = -1, second = -1;
  for (const k of oth) {
    if (top < 0 || lo[k] > lo[top]) { second = top; top = k; } else if (second < 0 || lo[k] > lo[second]) second = k;
  }
  const min = new Array(n), max = new Array(n);
  min[W] = smin; max[W] = smax;
  for (const p of oth) {
    const Lp = L - lo[p];
    const other = p === top ? second : top;
    const restLo = Math.max(lo[W], other < 0 ? lo[W] : lo[other]);
    min[p] = Math.max(lo[p], 1 - smax - (capmax - Math.min(hi[p], smax)));
    let best = lo[p];
    const sStar = Math.min(Math.max((1 - Lp) / 2, restLo), hi[W]);
    const u = Math.min(hi[p], sStar, 1 - sStar - Lp);
    if (u >= lo[p]) {
      const sig = Math.max(Math.min(hi[W], 1 - u - Lp), restLo, u);
      const rest = oth.reduce((t, k) => t + (k === p ? 0 : Math.min(hi[k], sig)), 0);
      if (sig + u + rest >= 1 - EPS && sig <= hi[W] + EPS) best = u;
      else best = Math.min(Math.max(lo[p], 1 - sig - rest), hi[p], sig);
    }
    max[p] = Math.max(best, min[p]);
  }
  return { ok: true, min, max };
}

// Ward i's ranges when party index W is painted there: its base ranges with
// the shape applied (W at least q_win, every other party at most q_run), or,
// when those leave no share vector, the shape alone (fallback: true).
// { lo, hi, fallback, min, max }.
function wardCell(ctx, i, W) {
  const { q_win, q_run, base } = ctx.bounds;
  const lo = base[i].lo.slice(), hi = base[i].hi.map((h, k) => (k === W ? h : Math.min(h, q_run)));
  lo[W] = Math.max(lo[W], q_win);
  let r = wardRange(lo, hi, W);
  if (r.ok) return { lo, hi, fallback: false, min: r.min, max: r.max };
  const flo = lo.map(() => 0), fhi = hi.map(() => q_run);
  flo[W] = q_win; fhi[W] = 1;
  r = wardRange(flo, fhi, W);
  if (!r.ok) throw new Error("ward " + ctx.wards[i] + " has no share vector even under the shape alone");
  return { lo: flo, hi: fhi, fallback: true, min: r.min, max: r.max };
}

// Each (ward, winner) is computed once per context: a paint stroke
// recomputes only the wards it repaints.
const CELLS = new WeakMap();
function cellOf(ctx, i, W) {
  let m = CELLS.get(ctx);
  if (!m) { m = new Map(); CELLS.set(ctx, m); }
  const key = i * ctx.codes.length + W;
  if (!m.has(key)) m.set(key, wardCell(ctx, i, W));
  return m.get(key);
}

// The per-party BOX for the calls on the map: { floor, ceil } in shares of the
// ward ballot, each the sum over the wards of e[w] times the least (greatest)
// share the party can hold there; fallback: [{ ward, code }] for each painted
// ward that uses the shape alone.
export function boxOf(calls, ctx) {
  const n = ctx.codes.length, e = ctx.bounds.e;
  const floor = new Array(n).fill(0), ceil = new Array(n).fill(0), fallback = [];
  calls.forEach((c, i) => {
    const W = ctx.codes.indexOf(c);
    if (W < 0) throw new Error("not on the roster: " + c);
    const cell = cellOf(ctx, i, W);
    if (cell.fallback) fallback.push({ ward: ctx.wards[i], code: c });
    for (let k = 0; k < n; k++) { floor[k] += e[i] * cell.min[k]; ceil[k] += e[i] * cell.max[k]; }
  });
  return { floor: Object.fromEntries(ctx.codes.map((c, k) => [c, floor[k]])),
           ceil: Object.fromEntries(ctx.codes.map((c, k) => [c, ceil[k]])), fallback };
}

// The editor's limits on each party's share of the ward ballot for the calls
// on the map: the box intersected with the citywide limit (module comment).
// { lo, hi: {code: share}, bind: {code: { floor, ceil }} ("box" or "city":
// which side sets each), conflict: [{ code, side }] (side "floor": its wards
// need more than its citywide limit allows; "ceiling": they leave it less),
// eased: null | "floors" | "ceilings", fallback, box }.
export function limits(calls, ctx) {
  const box = boxOf(calls, ctx);
  const city = ctx.bounds.city;
  const lo = {}, hi = {}, bind = {}, conflict = [];
  ctx.codes.forEach((c, k) => {
    const bf = box.floor[c], bc = box.ceil[c], cl = city.lo[k], ch = city.hi[k];
    let a = Math.max(bf, cl), b = Math.min(bc, ch);
    bind[c] = { floor: cl > bf ? "city" : "box", ceil: ch < bc ? "city" : "box" };
    if (a > b) {
      conflict.push({ code: c, side: bf > ch ? "floor" : "ceiling" });
      a = bf; b = Math.max(bf, Math.min(bc, ch));
      bind[c] = { floor: "box", ceil: "box" };
    }
    lo[c] = a; hi[c] = b;
  });
  const sum = m => ctx.codes.reduce((t, c) => t + m[c], 0);
  let eased = null;
  const over = sum(lo) - 1;
  if (over > 0) {
    // the citywide parts of the floors, eased in proportion until they fit
    const room = ctx.codes.reduce((t, c) => t + (lo[c] - box.floor[c]), 0);
    const k = room > 0 ? Math.max(0, 1 - over / room) : 0;
    for (const c of ctx.codes) lo[c] = box.floor[c] + k * (lo[c] - box.floor[c]);
    eased = "floors";
  }
  const under = 1 - sum(hi);
  if (under > 0) {
    const room = ctx.codes.reduce((t, c) => t + (box.ceil[c] - hi[c]), 0);
    const k = room > 0 ? Math.max(0, 1 - under / room) : 0;
    for (const c of ctx.codes) hi[c] = box.ceil[c] - k * (box.ceil[c] - hi[c]);
    eased = eased ? "both" : "ceilings";
  }
  return { lo, hi, bind, conflict, eased, fallback: box.fallback, box };
}

// The limits in whole votes of a ward total `wardTotal`: { floor, ceil:
// {code: n} } and the rest of limits(). A ward winner keeps one vote (R1);
// rounding never leaves the floors above the total or the ceilings below it.
export function wardLimits(calls, ctx, wardTotal) {
  const L = limits(calls, ctx), held = wardCounts(calls);
  const floor = {}, ceil = {}, least = {};
  for (const c of ctx.codes) {
    least[c] = held[c] ? 1 : 0;
    floor[c] = Math.min(wardTotal, Math.max(Math.ceil(L.lo[c] * wardTotal), least[c]));
    ceil[c] = Math.max(floor[c], Math.min(wardTotal, Math.floor(L.hi[c] * wardTotal)));
  }
  const total = m => ctx.codes.reduce((t, c) => t + m[c], 0);
  if (total(least) > wardTotal) throw new Error("the ward winners need more votes than the ward ballot holds");
  for (let spare = total(floor) - wardTotal; spare > 0;)
    for (const c of ctx.codes) if (spare > 0 && floor[c] > least[c]) { floor[c] -= 1; spare -= 1; }
  for (let short = wardTotal - total(ceil); short > 0;)
    for (const c of ctx.codes) if (short > 0 && ceil[c] < wardTotal) { ceil[c] += 1; short -= 1; }
  return { ...L, floor, ceil };
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
// clamped to the party's limits (and to what the others' limits leave); the
// others' ward votes are rescaled inside their limits, and every list vote
// follows its party's ward share. Returns { state, clamped: null|"floor"|"ceiling",
// which, by: null|"box"|"city"|"others" (what set the clamp) }.
export function setWardPercent(state, ctx, code, pct) {
  if (!ctx.codes.includes(code)) throw new Error("not on the roster: " + code);
  const Tw = totalOf(state, "ward");
  const { floor, ceil, bind } = wardLimits(state.calls, ctx, Tw);
  const others = ctx.codes.filter(c => c !== code);
  const lo = Math.max(floor[code], Tw - others.reduce((a, c) => a + ceil[c], 0));
  const hi = Math.min(ceil[code], Tw - others.reduce((a, c) => a + floor[c], 0));
  const want = Math.round(Number(pct) / 100 * Tw);
  const v = Math.max(lo, Math.min(hi, Number.isFinite(want) ? want : state.ward[code]));
  const rest = apportion(others, state.ward, Tw - v, floor, ceil);
  const ward = Object.fromEntries(ctx.codes.map(c => [c, c === code ? v : rest[c]]));
  const list = listFollow(state.calls, state, ward, ctx);
  const clamped = v !== want ? (want < v ? "floor" : "ceiling") : null;
  const by = !clamped ? null : clamped === "floor" ? (v > floor[code] ? "others" : bind[code].floor)
    : (v < ceil[code] ? "others" : bind[code].ceil);
  return { state: { calls: state.calls, ward, list }, clamped, which: clamped ? code : null, by };
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

// Bring every party's ward vote inside its limits for the calls on the map
// (others rescaled), the list following; and give a ward winner the one ward
// and list vote R1 and R2 need. Returns { state, moved, conflict, fallback,
// eased }: the codes whose ward vote was outside its limits, and limits()'
// conflicts, fallback wards and easing for the calls, for the page's note.
export function clampToBounds(state, ctx) {
  const Tw = totalOf(state, "ward");
  const { floor, ceil, conflict, fallback, eased } = wardLimits(state.calls, ctx, Tw);
  const moved = ctx.codes.filter(c => state.ward[c] < floor[c] || state.ward[c] > ceil[c]);
  const mins = lawBounds(state.calls, ctx, totalOf(state, "list")).mins;
  if (!moved.length && ctx.codes.every(c => state.list[c] >= mins[c]))
    return { state: { calls: state.calls, ward: { ...state.ward }, list: { ...state.list } }, moved, conflict, fallback, eased };
  const ward = moved.length ? apportion(ctx.codes, state.ward, Tw, floor, ceil) : { ...state.ward };
  const list = listFollow(state.calls, state, ward, ctx);
  return { state: { calls: state.calls, ward, list }, moved, conflict, fallback, eased };
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
// an error: such a state is valid. A ward vote outside its limits is clamped
// by the next change to any ward vote or call; a gap, when that party's gap is
// next set (module comment).
export function outOfBounds(state, ctx) {
  const Tw = totalOf(state, "ward");
  const { floor, ceil } = wardLimits(state.calls, ctx, Tw);
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
