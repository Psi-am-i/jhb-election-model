// ⛔ PLACEHOLDER SEAT ALLOCATOR. THIS IS NOT THE LAW.
//
// The real page runs the project's own src/reader_seats.py under Pyodide —
// one definition of the seat law, never a JavaScript copy (PUBLISHING-BACKLOG
// §9, §10) — as `reader_seats(combined_shares, ward_winners, context,
// total_votes)`, and the server stores the answer of the same file
// (worker-api/src/seats.js). This stub exists only so the prototype can show
// seats moving while the interface is designed.
//
// What it does, deliberately naive: each party keeps the wards the reader gave
// it, and the 135 list seats are shared by largest remainder on the reader's
// combined-vote shares ALONE, ignoring that Schedule 1 sizes each party's
// whole entitlement from the combined vote and deducts its ward seats (and
// that the excessive-seats clause moves seats between other parties). It is
// used here precisely because nobody could mistake it for the real one.
//
// THE INTERFACE the page reads:
//
//   allocate({ wardCalls, combinedShare, parties, councilSeats, wardSeats })
//     wardCalls     : string[135]        party code per ward, or null if uncalled
//     combinedShare : { code: percent }  each party's share of ALL votes, ward
//                                         and list ballots together, any scale
//     returns { seats:{code:n}, wardWins:{code:n}, listSeats:{code:n},
//               total:n, council:n, majority:n, stub:true, note:string }
//
// `total` is the seats handed out so far (fewer while wards are uncalled);
// `council` and `majority` are the council as seated, which the page and the
// card print, and which reader_seats returns under the same names.

export function allocate({ wardCalls, combinedShare, parties, councilSeats, wardSeats }) {
  const codes = parties.map(p => p.code);
  const wardWins = Object.fromEntries(codes.map(c => [c, 0]));
  for (const c of wardCalls) if (c && c in wardWins) wardWins[c] += 1;

  const listSeats = Object.fromEntries(codes.map(c => [c, 0]));
  const listTotal = councilSeats - wardSeats;
  const tot = codes.reduce((s, c) => s + Math.max(0, +combinedShare[c] || 0), 0);
  if (tot > 0) {
    const raw = codes.map(c => Math.max(0, +combinedShare[c] || 0) / tot * listTotal);
    const fl = raw.map(Math.floor);
    let left = listTotal - fl.reduce((a, b) => a + b, 0);
    const order = raw.map((r, i) => [r - fl[i], i]).sort((a, b) => b[0] - a[0]);
    for (const [, i] of order) { if (left-- <= 0) break; fl[i] += 1; }
    codes.forEach((c, i) => { listSeats[c] = fl[i]; });
  }
  const seats = Object.fromEntries(codes.map(c => [c, wardWins[c] + listSeats[c]]));
  const total = Object.values(seats).reduce((a, b) => a + b, 0);
  return { seats, wardWins, listSeats, total, council: councilSeats, majority: Math.floor(councilSeats / 2) + 1, stub: true,
    note: "Placeholder allocator — not the seat law. The real page uses the model's seats.allocate." };
}
