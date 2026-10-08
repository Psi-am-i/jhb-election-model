// The seam to the seat law. This Worker never computes a seat.
//
// DECISION: the server trusts only the reader's picks (ward winners, whole
// votes on the ward ballot and on the list ballot) and recomputes seats itself by calling the project's own Python
// seat code, src/reader_seats.py, running in a Python Worker (seats-py/) behind
// the SEATS service binding. The page runs the same file under Pyodide to show
// seats while the reader edits; the server's answer is the one stored and drawn
// on the card. A `seats` key sent by a client is refused by the validator. A
// JavaScript copy of the seat law is not an option (PUBLISHING-BACKLOG §9,
// BACKEND.md §6).
//
// CONTRACT (POST https://seats/v1/seats, JSON). The request body is the four
// arguments of reader_seats.reader_seats(ward_votes, list_votes,
// ward_winners, context), by name, so seats-py/src/entry.py passes them
// through untouched:
//   request   { ward_votes: {code: int},             whole votes on the ward
//                                                    ballot, roster order
//               list_votes: {code: int},             whole votes on the list
//                                                    ballot, roster order
//               ward_winners: {ward_id: code},       every ward
//               context: {city, target, council, wards, parties, no_pr_list} }
//   200       { seats: {code: int},            total seats per party
//               ward:  {code: int},            wards won (as picked)
//               pr:    {code: int},            PR councillors
//               council_total: int,            the council the law seated
//               majority: int,                 floor(council_total / 2) + 1
//               excessive: {code: int},        item 16 parties and their excess
//               code_ref: string }             sha256 of the copied seat code
//   422       { errors: [string] }             the seat law refused the picks
//                                              (e.g. a ward won by a party
//                                              with no list vote): the
//                                              READER's input, answered as a 422
//
// `context` comes from the generated schema (x-seat-context), which
// make_schema.mjs reads from the model artefact. Each ballot's total is the
// sum of the entry's votes: no total is supplied.
//
// What this module checks of the answer is arithmetic identity, not the law:
// ward counts equal the counts of the picks, seats = ward + pr per party, the
// totals add up, and no party appears that is not on the roster. A service
// answering anything else is treated as unavailable.

import { HttpError } from "./http.js";

export class SeatsUnavailable extends HttpError {
  constructor(why) { super(503, "seats cannot be computed right now; nothing was saved"); this.why = why; }
}

// The seat law refused the reader's picks. A 422 naming the vote field: the
// validator accepted the shape, the statute did not accept the combination.
export class SeatsRefused extends HttpError {
  constructor(errors) {
    super(422, "the seat law cannot seat this prediction: " + errors.join("; "), "ward_votes");
    this.errors = errors;
  }
}

const isCount = v => Number.isInteger(v) && v >= 0;

// The request body: the reader's validated entry, as reader_seats takes it.
// Whole votes pass through as they are, in roster order; the ward list is the
// schema's, in the order ward_calls is written.
export function seatRequest(entry, schema) {
  const context = schema["x-seat-context"];
  return {
    ward_votes: Object.fromEntries(context.parties.map(c => [c, entry.ward_votes[c]])),
    list_votes: Object.fromEntries(context.parties.map(c => [c, entry.list_votes[c]])),
    ward_winners: Object.fromEntries(context.wards.map((w, i) => [w, entry.ward_calls[i]])),
    context,
  };
}

export function checkSeatAnswer(ans, forecast, schema) {
  const roster = schema.properties.ward_calls.items.enum;
  const { council_seats } = schema["x-council"];
  if (!ans || typeof ans !== "object") throw new SeatsUnavailable("not an object");
  const { seats, ward, pr, council_total, majority, excessive, code_ref } = ans;
  for (const [name, m] of [["seats", seats], ["ward", ward], ["pr", pr], ["excessive", excessive]]) {
    if (!m || typeof m !== "object") throw new SeatsUnavailable(`${name} missing`);
    for (const [k, v] of Object.entries(m)) {
      if (!roster.includes(k)) throw new SeatsUnavailable(`${name}: ${k} not on roster`);
      if (!isCount(v)) throw new SeatsUnavailable(`${name}.${k} not a count`);
    }
  }
  const picked = {};
  for (const c of forecast.ward_calls) picked[c] = (picked[c] || 0) + 1;
  for (const c of roster) {
    if ((ward[c] || 0) !== (picked[c] || 0)) throw new SeatsUnavailable(`ward.${c} differs from the picks`);
    if ((seats[c] || 0) !== (ward[c] || 0) + (pr[c] || 0)) throw new SeatsUnavailable(`seats.${c} != ward + pr`);
  }
  const total = Object.values(seats).reduce((a, b) => a + b, 0);
  if (!isCount(council_total) || total !== council_total || council_total < council_seats)
    throw new SeatsUnavailable("council total does not add up");
  if (majority !== Math.floor(council_total / 2) + 1) throw new SeatsUnavailable("majority is not half the council plus one");
  if (typeof code_ref !== "string" || !/^[0-9a-f]{16,64}$/.test(code_ref)) throw new SeatsUnavailable("no code_ref");
  return { seats, ward, pr, council_total, majority, excessive, code_ref };
}

export async function computeSeats(env, forecast, schema) {
  if (!env.SEATS) throw new SeatsUnavailable("no SEATS binding");
  let r;
  try {
    r = await env.SEATS.fetch("https://seats/v1/seats", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(seatRequest(forecast, schema)),
    });
  } catch (e) {
    throw new SeatsUnavailable(String(e));
  }
  if (r.status === 422) {
    let body;
    try { body = await r.json(); } catch { throw new SeatsUnavailable("422 without JSON"); }
    const errors = Array.isArray(body?.errors) && body.errors.length && body.errors.every(e => typeof e === "string")
      ? body.errors : null;
    if (!errors) throw new SeatsUnavailable("422 without errors");
    throw new SeatsRefused(errors);
  }
  if (!r.ok) throw new SeatsUnavailable(`SEATS answered ${r.status}`);
  let ans;
  try { ans = await r.json(); } catch { throw new SeatsUnavailable("not JSON"); }
  return checkSeatAnswer(ans, forecast, schema);
}
