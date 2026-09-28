// The seam to the seat law. This Worker never computes a seat.
//
// DECISION: the server trusts only the reader's picks (ward winners, PR shares)
// and recomputes seats itself by calling the project's own Python seat code,
// src/reader_seats.py, running in a Python Worker (seats-py/) behind the SEATS
// service binding. The page runs the same file under Pyodide to show seats while
// the reader edits; the server's answer is the one stored and drawn on the card.
// A `seats` key sent by a client is refused by the validator. A JavaScript copy
// of the seat law is not an option (PUBLISHING-BACKLOG §9, BACKEND.md §6).
//
// CONTRACT (POST https://seats/v1/seats, JSON):
//   request   { ward_calls: [code × ward_seats], pr_share: {code: percent},
//               council_seats: int }
//   response  { seats: {code: int},            total seats per party
//               ward:  {code: int},            wards won (as picked)
//               pr:    {code: int},            PR councillors
//               council_total: int,            council_seats + any overhang
//               code_ref: string }             sha256 of reader_seats.py + seats.py
//
// What this module checks of the answer is arithmetic identity, not the law:
// ward counts equal the counts of the picks, seats = ward + pr per party, the
// totals add up, and no party appears that is not on the roster. A service
// answering anything else is treated as unavailable.

import { HttpError } from "./http.js";

export class SeatsUnavailable extends HttpError {
  constructor(why) { super(503, "seats cannot be computed right now; nothing was saved"); this.why = why; }
}

const isCount = v => Number.isInteger(v) && v >= 0;

export function checkSeatAnswer(ans, forecast, schema) {
  const roster = schema.properties.ward_calls.items.enum;
  const { council_seats } = schema["x-council"];
  if (!ans || typeof ans !== "object") throw new SeatsUnavailable("not an object");
  const { seats, ward, pr, council_total, code_ref } = ans;
  for (const [name, m] of [["seats", seats], ["ward", ward], ["pr", pr]]) {
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
  if (typeof code_ref !== "string" || !/^[0-9a-f]{16,64}$/.test(code_ref)) throw new SeatsUnavailable("no code_ref");
  return { seats, ward, pr, council_total, code_ref };
}

export async function computeSeats(env, forecast, schema) {
  if (!env.SEATS) throw new SeatsUnavailable("no SEATS binding");
  let r;
  try {
    r = await env.SEATS.fetch("https://seats/v1/seats", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        ward_calls: forecast.ward_calls,
        pr_share: forecast.pr_share,
        council_seats: schema["x-council"].council_seats,
      }),
    });
  } catch (e) {
    throw new SeatsUnavailable(String(e));
  }
  if (!r.ok) throw new SeatsUnavailable(`SEATS answered ${r.status}`);
  let ans;
  try { ans = await r.json(); } catch { throw new SeatsUnavailable("not JSON"); }
  return checkSeatAnswer(ans, forecast, schema);
}
