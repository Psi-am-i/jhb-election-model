// ⛔ TEST DOUBLE for the SEATS service contract (src/seats.js). NOT THE SEAT LAW.
// It exists so tests can exercise saving and rendering without the Python
// Worker. It takes the request reader_seats takes (ward_votes, list_votes,
// ward_winners, context). Ward seats are the picks counted; the remaining
// seats are handed out by flooring each party's share of the list ballot and
// giving the leftover to the first roster party: an arbitrary rule, chosen to
// be obviously not Schedule 1.
export async function fakeSeats(request) {
  const { list_votes, ward_winners, context } = await request.json();
  const calls = Object.values(ward_winners);
  const ward = {};
  for (const c of calls) ward[c] = (ward[c] || 0) + 1;
  const codes = Object.keys(list_votes);
  const total = codes.reduce((a, c) => a + list_votes[c], 0);
  const left = context.council - calls.length;
  const pr = Object.fromEntries(codes.map(c => [c, Math.floor(list_votes[c] / total * left)]));
  pr[codes[0]] += left - Object.values(pr).reduce((a, b) => a + b, 0);
  const seats = Object.fromEntries(codes.map(c => [c, (ward[c] || 0) + pr[c]]));
  return Response.json({ seats, ward, pr, council_total: context.council, majority: Math.floor(context.council / 2) + 1,
    excessive: {}, code_ref: "fa4e5ea75fa4e5ea75fa4e5ea75fa4e5" });
}
