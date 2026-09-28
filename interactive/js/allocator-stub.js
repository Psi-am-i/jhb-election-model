// ⛔ PLACEHOLDER SEAT ALLOCATOR. THIS IS NOT THE LAW.
//
// The real page calls the model's own `seats.allocate` (src/seats.py) under
// Pyodide — one definition of the seat law, never a JavaScript copy
// (PUBLISHING-BACKLOG §9, §10). This stub exists only so the prototype can
// show seats moving while the interface is designed.
//
// What it does, deliberately naive: each party keeps the wards the reader gave
// it, and the 135 list seats are shared by largest remainder on the reader's
// list-vote shares ALONE. That is the "PR-only" reading of Schedule 1 that
// the project has already shown to be wrong (seats follow combined ward+PR
// votes, and the excessive-seats clause deducts a surplus from everyone else).
// It is used here precisely because nobody could mistake it for the real one.
//
// THE INTERFACE the real integration must honour:
//
//   allocate({ wardCalls, prShare, parties, councilSeats, wardSeats })
//     wardCalls : string[135]        party code per ward, or null if uncalled
//     prShare   : { code: percent }  the reader's list vote, any scale
//     returns   { seats:{code:n}, wardWins:{code:n}, listSeats:{code:n},
//                 total:n, stub:true, note:string }
//
// ⚠ OPEN (model side, not the page's to decide): seats.allocate takes
// COMBINED VOTE COUNTS, and a reader supplies ward winners plus list-vote
// shares, not votes. How a hand-called ward map becomes combined votes — and
// so how a reader's ward wins meet the excessive-seats clause — has to be
// specified in the model with a JUDGEMENT-CALLS row. See README.md.

export function allocate({ wardCalls, prShare, parties, councilSeats = 270, wardSeats = 135 }) {
  const codes = parties.map(p => p.code);
  const wardWins = Object.fromEntries(codes.map(c => [c, 0]));
  for (const c of wardCalls) if (c && c in wardWins) wardWins[c] += 1;

  const listSeats = Object.fromEntries(codes.map(c => [c, 0]));
  const listTotal = councilSeats - wardSeats;
  const tot = codes.reduce((s, c) => s + Math.max(0, +prShare[c] || 0), 0);
  if (tot > 0) {
    const raw = codes.map(c => Math.max(0, +prShare[c] || 0) / tot * listTotal);
    const fl = raw.map(Math.floor);
    let left = listTotal - fl.reduce((a, b) => a + b, 0);
    const order = raw.map((r, i) => [r - fl[i], i]).sort((a, b) => b[0] - a[0]);
    for (const [, i] of order) { if (left-- <= 0) break; fl[i] += 1; }
    codes.forEach((c, i) => { listSeats[c] = fl[i]; });
  }
  const seats = Object.fromEntries(codes.map(c => [c, wardWins[c] + listSeats[c]]));
  const total = Object.values(seats).reduce((a, b) => a + b, 0);
  return { seats, wardWins, listSeats, total, stub: true,
    note: "Placeholder allocator — not the seat law. The real page uses the model's seats.allocate." };
}
