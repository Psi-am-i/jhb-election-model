// The reader's forecast while it is being built. PURE: no DOM, no fetch, so
// interactive/tests drives it with random edits and checks every state it
// reaches against the server's validator and the seat law.
//
// DESIGN-decided §14 (owner, 2026-09-29): an impossible forecast cannot be
// built, so an honest save never fails. Every function here takes a valid state
// and returns a valid one:
//
//  * every ward has a winner on the roster;
//  * the vote is held as WHOLE VOTES per party, summing exactly to the
//    combined total the seat law scales to (schema x-total-votes). A percent
//    is derived for display and for the saved body, never stored. Integer
//    votes are what src/reader_seats.py counts (combined_votes), so the shares
//    the page sends come back as exactly these votes;
//  * a party holding a ward has at least FLOOR_VOTES votes, and a party the
//    roster lists with no PR list has none.
//
// THE FLOOR is the seat law's own condition, not a chosen number:
// reader_seats refuses a ward won by a party with a zero share, and refuses a
// positive share "too small to receive one vote" at total_votes. So the
// smallest share a ward-holder may have is one vote of total_votes. The test
// suite holds both sides of it against reader_seats: at one vote the forecast
// seats, at zero it is refused.
//
// The vote is the COMBINED vote, ward and list ballots together
// (DESIGN-decided §10). Parties are treated identically (§8): the only
// per-party facts used are the roster's no-PR-list flag and the reader's own
// ward picks.

export const FLOOR_VOTES = 1;

// What the builder needs from the generated schema (worker-api/generated/
// forecast.schema.json), the file the server validates against.
export function contextOf(schema) {
  const seat = schema["x-seat-context"];
  const T = schema["x-total-votes"];
  if (!Number.isInteger(T) || T <= 0) throw new Error("the schema's x-total-votes is not a positive integer");
  return {
    codes: seat.parties.slice(),
    wards: seat.wards.slice(),
    noList: new Set(seat.no_pr_list),
    T,
    model_ref: schema.properties.model_ref.enum[0],
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

// The smallest vote each party may hold, given the ward picks.
export function floorsOf(calls, ctx) {
  const held = wardCounts(calls);
  return Object.fromEntries(ctx.codes.map(c => [c, !ctx.noList.has(c) && held[c] ? FLOOR_VOTES : 0]));
}

// The largest vote a party may hold: everything the others' floors leave.
export function ceilingOf(code, calls, ctx) {
  if (ctx.noList.has(code)) return 0;
  const f = floorsOf(calls, ctx);
  return ctx.T - ctx.codes.reduce((a, c) => a + (c === code ? 0 : f[c]), 0);
}

// Largest remainder: whole numbers summing to `total`, in proportion to
// `weights`, each at least its `mins` entry. Ties fall to roster order.
function apportion(codes, weights, total, mins) {
  const fixed = new Set();
  let raw;
  for (;;) {
    const free = codes.filter(c => !fixed.has(c));
    const left = total - [...fixed].reduce((a, c) => a + mins[c], 0);
    let w = free.reduce((a, c) => a + weights[c], 0);
    const wt = w > 0 ? c => weights[c] : () => 1;
    if (w <= 0) w = free.length;
    raw = Object.fromEntries(codes.map(c => [c, fixed.has(c) ? mins[c] : (free.length ? left * wt(c) / w : 0)]));
    const under = free.filter(c => raw[c] < mins[c]);
    if (!under.length) break;
    under.forEach(c => fixed.add(c));
  }
  const out = Object.fromEntries(codes.map(c => [c, Math.floor(raw[c])]));
  let spare = total - codes.reduce((a, c) => a + out[c], 0);
  const order = codes.map((c, i) => [c, raw[c] - out[c], i]).sort((a, b) => b[1] - a[1] || a[2] - b[2]);
  for (const [c] of order) { if (spare <= 0) break; out[c] += 1; spare -= 1; }
  return out;
}

// Set one party's vote; the others are rescaled in proportion to what they
// held, none below its floor. The target is clamped to [floor, ceiling].
// Returns { state, clamped } where clamped says the reader asked for less
// than the party's floor (or more than its ceiling).
export function setVotes(state, ctx, code, target) {
  if (!ctx.codes.includes(code)) throw new Error("not on the roster: " + code);
  const floors = floorsOf(state.calls, ctx);
  const hi = ceilingOf(code, state.calls, ctx);
  const want = Math.round(Number(target));
  const v = Math.max(floors[code], Math.min(hi, Number.isFinite(want) ? want : 0));
  const others = ctx.codes.filter(c => c !== code && !ctx.noList.has(c));
  const rest = apportion(others, state.votes, ctx.T - v, floors);
  const votes = Object.fromEntries(ctx.codes.map(c => [c, c === code ? v : (rest[c] ?? 0)]));
  const clamped = v !== want ? (want < v ? "floor" : "ceiling") : null;
  return { state: { calls: state.calls, votes }, clamped };
}

export function setPercent(state, ctx, code, pct) {
  return setVotes(state, ctx, code, Number(pct) / 100 * ctx.T);
}

// Raise every party below its floor to the floor, taking the votes from the
// others in proportion. Returns the codes raised.
function raiseFloors(state, ctx) {
  const floors = floorsOf(state.calls, ctx);
  const raised = [];
  for (const c of ctx.codes) {
    if (state.votes[c] < floors[c]) { state = setVotes(state, ctx, c, floors[c]).state; raised.push(c); }
  }
  return { state, raised };
}

// Give wards to a party. A party that had no votes and now holds a ward is
// raised to the floor; `raised` names it, for the page's note.
export function assignWards(state, ctx, indices, code) {
  if (!ctx.codes.includes(code)) throw new Error("not on the roster: " + code);
  const calls = state.calls.slice();
  for (const i of indices) {
    if (!(i >= 0 && i < calls.length)) throw new Error("no ward at index " + i);
    calls[i] = code;
  }
  return raiseFloors({ calls, votes: state.votes }, ctx);
}

// Replace every ward's winner at once (the model's map, an area fill).
export function setCalls(state, ctx, calls) {
  return raiseFloors({ calls: checkCalls(calls, ctx), votes: state.votes }, ctx);
}

function checkCalls(calls, ctx) {
  if (!Array.isArray(calls) || calls.length !== ctx.wards.length) throw new Error("one winner per ward is needed");
  for (const c of calls) if (!ctx.codes.includes(c)) throw new Error("not on the roster: " + c);
  return calls.slice();
}

// Whole votes from percents (any scale), by largest remainder; list-less
// parties get none. All zero is spread evenly over the parties that may hold
// votes, which treats every party alike (§8).
export function votesFromPercent(share, ctx) {
  const codes = ctx.codes.filter(c => !ctx.noList.has(c));
  const w = Object.fromEntries(codes.map(c => {
    const x = Number(share?.[c]);
    return [c, Number.isFinite(x) && x > 0 ? x : 0];
  }));
  const zeros = Object.fromEntries(codes.map(c => [c, 0]));
  const got = apportion(codes, w, ctx.T, zeros);
  return Object.fromEntries(ctx.codes.map(c => [c, got[c] ?? 0]));
}

// A valid starting state from whatever the page was handed: the published
// forecast, a lever state from the model page (calls may be null), or a
// draft. A missing or unknown ward winner is filled from `fallbackCalls` (the
// model's most likely winner, in ward order).
export function startState(ctx, { calls, share }, fallbackCalls) {
  const fb = checkCalls(fallbackCalls, ctx);
  const c = Array.isArray(calls) && calls.length === ctx.wards.length
    ? calls.map((x, i) => ctx.codes.includes(x) ? x : fb[i]) : fb.slice();
  return raiseFloors({ calls: c, votes: votesFromPercent(share, ctx) }, ctx);
}

export function percentOf(state, ctx) {
  return Object.fromEntries(ctx.codes.map(c => [c, state.votes[c] / ctx.T * 100]));
}

// The request body the page validates and saves: exactly the keys
// worker-api/src/validate.js accepts.
export function forecastBody(state, ctx, { coalition = [], mayor = null, display_name = null } = {}) {
  return {
    model_ref: ctx.model_ref,
    ward_calls: state.calls.slice(),
    combined_share: percentOf(state, ctx),
    coalition: coalition.slice(),
    mayor: mayor || null,
    display_name: display_name || null,
  };
}

// Every broken invariant, as sentences. Empty means valid. For tests and for
// a defensive check before the page shows a state.
export function invariantErrors(state, ctx) {
  const e = [];
  if (!Array.isArray(state.calls) || state.calls.length !== ctx.wards.length) e.push("not one winner per ward");
  else state.calls.forEach((c, i) => { if (!ctx.codes.includes(c)) e.push("ward " + ctx.wards[i] + " has no winner on the roster"); });
  let sum = 0;
  for (const c of ctx.codes) {
    const v = state.votes[c];
    if (!Number.isInteger(v) || v < 0) e.push(c + ": " + v + " is not a whole number of votes");
    sum += v;
  }
  if (sum !== ctx.T) e.push("votes sum to " + sum + ", not " + ctx.T);
  if (!e.length) {
    const f = floorsOf(state.calls, ctx);
    for (const c of ctx.codes) {
      if (state.votes[c] < f[c]) e.push(c + " holds a ward with fewer than " + f[c] + " vote");
      if (ctx.noList.has(c) && state.votes[c] > 0) e.push(c + " has no PR list and may hold no votes");
    }
  }
  return e;
}

// Undo keeps WHOLE states, calls and votes together. Keeping calls alone would
// break validity: A holds a ward at 5 votes, the ward goes to B, A is lowered
// to 0, and restoring the calls alone gives A the ward with no votes.
export class History {
  constructor(limit = 60) { this.limit = limit; this.stack = []; }
  push(state) {
    this.stack.push({ calls: state.calls.slice(), votes: { ...state.votes } });
    if (this.stack.length > this.limit) this.stack.shift();
  }
  pop() { return this.stack.pop() || null; }
  get size() { return this.stack.length; }
}
