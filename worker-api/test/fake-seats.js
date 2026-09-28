// ⛔ TEST DOUBLE for the SEATS service contract (src/seats.js). NOT THE SEAT LAW.
// It exists so tests can exercise saving and rendering without the Python
// Worker. Ward seats are the picks counted; the remaining seats are handed out
// by flooring PR share and giving the leftover to the first roster party: an
// arbitrary rule, chosen to be obviously not Schedule 1.
export async function fakeSeats(request) {
  const { ward_calls, pr_share, council_seats } = await request.json();
  const ward = {};
  for (const c of ward_calls) ward[c] = (ward[c] || 0) + 1;
  const codes = Object.keys(pr_share);
  const left = council_seats - ward_calls.length;
  const pr = Object.fromEntries(codes.map(c => [c, Math.floor(pr_share[c] * left / 100)]));
  pr[codes[0]] += left - Object.values(pr).reduce((a, b) => a + b, 0);
  const seats = Object.fromEntries(codes.map(c => [c, (ward[c] || 0) + pr[c]]));
  return Response.json({ seats, ward, pr, council_total: council_seats, code_ref: "fa4e5ea75fa4e5ea75fa4e5ea75fa4e5" });
}
