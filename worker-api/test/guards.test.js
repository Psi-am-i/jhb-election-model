// The seat seam, sign-in state, Turnstile, request guards and rate limits.
import { describe, it, expect } from "vitest";
import { env } from "cloudflare:test";
import { exports } from "cloudflare:workers";
import { checkSeatAnswer, computeSeats, seatRequest } from "../src/seats.js";
import { checkIdToken, PROVIDERS } from "../src/providers.js";
import { safeReturn } from "../src/auth.js";
import { verifyTurnstile } from "../src/turnstile.js";
import { signToken, verifyToken, randomId } from "../src/crypto.js";
import { fakeSeats } from "./fake-seats.js";
import { schema, roster, validForecast, makeUser, api, clone } from "./helpers.js";

const worker = exports.default;

async function goodAnswer(f = validForecast()) {
  return (await fakeSeats(new Request("https://seats/", { method: "POST",
    body: JSON.stringify(seatRequest(f, schema)) }))).json();
}

describe("the seat request is reader_seats' own arguments", () => {
  const f = validForecast();
  const req = seatRequest(f, schema);
  it("carries exactly the four arguments, by name", () => {
    expect(Object.keys(req).sort()).toEqual(["combined_shares", "context", "total_votes", "ward_winners"]);
  });
  it("the shares are the reader's combined shares as fractions summing to 1", () => {
    const sum = Object.values(req.combined_shares).reduce((a, b) => a + b, 0);
    expect(Math.abs(sum - 1)).toBeLessThan(1e-12);
    const pct = Object.values(f.combined_share).reduce((a, b) => a + b, 0);
    for (const c of roster) expect(req.combined_shares[c]).toBeCloseTo(f.combined_share[c] / pct, 15);
    expect(Object.keys(req.combined_shares)).toEqual(schema["x-seat-context"].parties);
  });
  it("a share sum inside the tolerance still reaches the service summing to 1", () => {
    const g = clone(f); g.combined_share[roster[0]] += 0.4;
    const sum = Object.values(seatRequest(g, schema).combined_shares).reduce((a, b) => a + b, 0);
    expect(Math.abs(sum - 1)).toBeLessThan(1e-12);
  });
  it("every ward is keyed by its id, in ward_calls order", () => {
    const ids = schema["x-ward-ids"];
    expect(Object.keys(req.ward_winners)).toEqual(ids);
    ids.forEach((w, i) => expect(req.ward_winners[w]).toBe(f.ward_calls[i]));
  });
  it("context and total_votes are the schema's, which the artefact supplied", () => {
    const ctx = req.context;
    expect(ctx.council).toBe(schema["x-council"].council_seats);
    expect(ctx.wards).toEqual(schema["x-ward-ids"]);
    expect(ctx.parties).toEqual(roster);
    expect(Number.isInteger(req.total_votes) && req.total_votes > 0).toBe(true);
  });
});

describe("the seat seam refuses an answer that does not add up", () => {
  const f = validForecast();
  const cases = [
    ["ward count differs from the picks", a => { a.ward[roster[0]] += 1; a.seats[roster[0]] += 1; a.council_total += 1; }],
    ["seats != ward + pr", a => { a.seats[roster[0]] += 1; }],
    ["a party off the roster", a => { a.seats.NOPE = 0; }],
    ["a fractional seat", a => { a.pr[roster[1]] += 0.5; a.seats[roster[1]] += 0.5; }],
    ["council total wrong", a => { a.council_total -= 1; }],
    ["majority not half the council plus one", a => { a.majority += 1; }],
    ["excessive missing", a => { delete a.excessive; }],
    ["an excessive party off the roster", a => { a.excessive.NOPE = 1; }],
    ["no code_ref", a => { delete a.code_ref; }],
  ];
  for (const [what, mutate] of cases) {
    it(what, async () => {
      const good = await goodAnswer(f);
      expect(() => checkSeatAnswer(clone(good), f, schema)).not.toThrow();
      const bad = clone(good); mutate(bad);
      expect(() => checkSeatAnswer(bad, f, schema)).toThrow();
    });
  }

  it("a SEATS service answering 501 (the stub) means 503 and nothing saved", async () => {
    const e = await computeSeats({ SEATS: { fetch: async () => new Response("", { status: 501 }) } }, f, schema).catch(x => x);
    expect(e.status).toBe(503);
    const e2 = await computeSeats({}, f, schema).catch(x => x);
    expect(e2.status).toBe(503);
  });

  it("the seat law refusing the picks is the reader's 422, naming the shares, not a 503", async () => {
    const refusing = errors => ({ SEATS: { fetch: async () => Response.json({ errors }, { status: 422 }) } });
    const e = await computeSeats(refusing(["wards won by parties with a zero share: ['X']"]), f, schema).catch(x => x);
    expect(e.status).toBe(422);
    expect(e.field).toBe("combined_share");
    expect(e.message).toMatch(/zero share/);
    // A 422 that does not say why is a broken service, not a reader error.
    for (const bad of [[], "nope", [3]]) {
      const e2 = await computeSeats(refusing(bad), f, schema).catch(x => x);
      expect(e2.status).toBe(503);
    }
  });

  it("a client-sent seats key is refused before the service is asked", async () => {
    const u = await makeUser();
    const r = await worker.fetch(api("/api/forecasts", { method: "POST", body: { ...validForecast(), seats: {} },
      headers: { cookie: u.cookie, "cf-connecting-ip": "203.0.113.1" } }));
    expect(r.status).toBe(400);
    expect((await r.json()).field).toBe("seats");
  });

  it("saved seats are the service's, stored with its code_ref", async () => {
    const u = await makeUser();
    const r = await worker.fetch(api("/api/forecasts", { method: "POST", body: validForecast(),
      headers: { cookie: u.cookie, "cf-connecting-ip": "203.0.113.2" } }));
    const { id, seats } = await r.json();
    const row = await env.DB.prepare("SELECT seats, seats_code_ref FROM forecasts WHERE id = ?").bind(id).first();
    expect(JSON.parse(row.seats)).toEqual(seats);
    expect(row.seats_code_ref).toBe(seats.code_ref);
  });
});

describe("id_token claims", () => {
  const now = Date.parse("2026-10-01T00:00:00Z");
  const good = { iss: "https://accounts.google.com", aud: "cid", exp: now / 1000 + 60, nonce: "n1", sub: "123" };
  const opts = { iss: ["https://accounts.google.com"], aud: "cid", nonce: "n1", now };
  it("accepts matching claims", () => expect(checkIdToken(good, opts).sub).toBe("123"));
  for (const [what, patch] of [["issuer", { iss: "https://evil" }], ["audience", { aud: "other" }],
    ["expiry", { exp: now / 1000 - 1 }], ["nonce", { nonce: "n2" }], ["subject", { sub: "" }]]) {
    it(`refuses a wrong ${what}`, () => expect(() => checkIdToken({ ...good, ...patch }, opts)).toThrow());
  }
});

describe("sign-in start and callback", () => {
  it("Google: PKCE S256, nonce, minimal scopes, redirect to our callback", async () => {
    const r = await worker.fetch(new Request(`${env.SITE_ORIGIN}/auth/google/start?return=/make`), { redirect: "manual" });
    expect(r.status).toBe(302);
    const u = new URL(r.headers.get("location"));
    expect(u.searchParams.get("code_challenge_method")).toBe("S256");
    expect(u.searchParams.get("scope")).toBe("openid email");
    expect(u.searchParams.get("nonce")).toBeTruthy();
    expect(u.searchParams.get("redirect_uri")).toBe(`${env.SITE_ORIGIN}/auth/google/callback`);
    expect(r.headers.get("set-cookie")).toMatch(/__Host-oauth=.*HttpOnly; SameSite=Lax; Secure/);
  });

  it("Apple: form_post, and a SameSite=None state cookie that survives the cross-site POST", async () => {
    const r = await worker.fetch(new Request(`${env.SITE_ORIGIN}/auth/apple/start`), { redirect: "manual" });
    const u = new URL(r.headers.get("location"));
    expect(u.searchParams.get("response_mode")).toBe("form_post");
    expect(u.searchParams.get("scope")).toBe("email");
    expect(r.headers.get("set-cookie")).toMatch(/SameSite=None; Secure/);
  });

  it("X and Microsoft use PKCE; Facebook asks only for email", async () => {
    for (const p of ["x", "microsoft"]) {
      const r = await worker.fetch(new Request(`${env.SITE_ORIGIN}/auth/${p}/start`), { redirect: "manual" });
      expect(new URL(r.headers.get("location")).searchParams.get("code_challenge_method"), p).toBe("S256");
    }
    const fb = await worker.fetch(new Request(`${env.SITE_ORIGIN}/auth/facebook/start`), { redirect: "manual" });
    expect(new URL(fb.headers.get("location")).searchParams.get("scope")).toBe("email");
  });

  it("a provider without its secrets answers 503, not 500", () => {
    let e;
    try { PROVIDERS.google.authorizationURL({ SITE_ORIGIN: env.SITE_ORIGIN }, { state: "s", verifier: "v", nonce: "n" }); } catch (x) { e = x; }
    expect(e.status).toBe(503);
  });

  it("an unknown provider answers 404 (Instagram is not one)", async () => {
    expect((await worker.fetch(new Request(`${env.SITE_ORIGIN}/auth/instagram/start`))).status).toBe(404);
  });

  it("a callback whose state does not match the cookie is refused before any code exchange", async () => {
    const st = await signToken(env.SESSION_SIGNING_KEY, "oauth", { p: "google", s: "right", v: "v", n: "n", r: "/" }, 600);
    const r = await worker.fetch(new Request(`${env.SITE_ORIGIN}/auth/google/callback?code=c&state=wrong`,
      { headers: { cookie: `__Host-oauth=${st}` } }));
    expect(r.status).toBe(400);
  });

  it("a state cookie minted for one provider is refused at another's callback", async () => {
    const st = await signToken(env.SESSION_SIGNING_KEY, "oauth", { p: "google", s: "s", v: "v", n: "n", r: "/" }, 600);
    const r = await worker.fetch(new Request(`${env.SITE_ORIGIN}/auth/microsoft/callback?code=c&state=s`,
      { headers: { cookie: `__Host-oauth=${st}` } }));
    expect(r.status).toBe(400);
  });

  it("only same-site relative return paths are honoured", () => {
    expect(safeReturn("/make?x=1")).toBe("/make?x=1");
    for (const bad of ["//evil.example", "https://evil.example", "/\\evil", "javascript:alert(1)", null])
      expect(safeReturn(bad)).toBe("/");
  });
});

describe("signed tokens", () => {
  it("expire, and are bound to their purpose", async () => {
    const t = await signToken("k", "a", { x: 1 }, 10, 0);
    expect((await verifyToken("k", "a", t, 5000)).x).toBe(1);
    expect(await verifyToken("k", "a", t, 11000)).toBe(null);
    expect(await verifyToken("k", "b", t, 5000)).toBe(null);
    expect(await verifyToken("other", "a", t, 5000)).toBe(null);
  });
  it("ids are 10 base62 characters", () => expect(randomId()).toMatch(/^[A-Za-z0-9]{10}$/));
});

describe("Turnstile fails closed", () => {
  const req = (tok) => new Request("https://x/", { headers: tok ? { "cf-turnstile-response": tok } : {} });
  const base = { TURNSTILE_REQUIRED: "true", SITE_ORIGIN: "https://joburg.whysoserious.city" };
  const answer = o => async () => Response.json(o);
  it("no secret configured: refuse", async () => {
    expect((await verifyTurnstile(base, req("t"), answer({ success: true })).catch(e => e)).status).toBe(503);
  });
  it("no token: refuse", async () => {
    expect((await verifyTurnstile({ ...base, TURNSTILE_SECRET: "s" }, req(null), answer({ success: true })).catch(e => e)).status).toBe(403);
  });
  it("siteverify says no: refuse", async () => {
    expect((await verifyTurnstile({ ...base, TURNSTILE_SECRET: "s" }, req("t"), answer({ success: false })).catch(e => e)).status).toBe(403);
  });
  it("a token for another hostname: refuse", async () => {
    expect((await verifyTurnstile({ ...base, TURNSTILE_SECRET: "s" }, req("t"), answer({ success: true, hostname: "evil.example" })).catch(e => e)).status).toBe(403);
  });
  it("siteverify unreachable: refuse", async () => {
    const down = async () => { throw new Error("net"); };
    expect((await verifyTurnstile({ ...base, TURNSTILE_SECRET: "s" }, req("t"), down).catch(e => e)).status).toBe(503);
  });
  it("siteverify says yes for our host: pass", async () => {
    expect(await verifyTurnstile({ ...base, TURNSTILE_SECRET: "s" }, req("t"), answer({ success: true, hostname: "joburg.whysoserious.city" })))
      .toEqual({ skipped: false });
  });
});

describe("request guards", () => {
  it("a save without consent is refused", async () => {
    const u = await makeUser();
    await env.DB.prepare("INSERT INTO consents (user_id, purpose, granted, wording_version, at) VALUES (?, 'store', 0, 't', 'now')").bind(u.id).run();
    const r = await worker.fetch(api("/api/forecasts", { method: "POST", body: validForecast(), headers: { cookie: u.cookie, "cf-connecting-ip": "203.0.113.3" } }));
    expect(r.status).toBe(403);
  });

  it("a save without sign-in is refused", async () => {
    expect((await worker.fetch(api("/api/forecasts", { method: "POST", body: validForecast() }))).status).toBe(401);
  });

  it("a body over the byte limit is refused (413) without being parsed", async () => {
    const u = await makeUser();
    const big = { ...validForecast(), display_name: "x".repeat(Number(env.MAX_BODY_BYTES)) };
    const r = await worker.fetch(api("/api/forecasts", { method: "POST", body: big, headers: { cookie: u.cookie, "cf-connecting-ip": "203.0.113.4" } }));
    expect(r.status).toBe(413);
  });

  it("a non-JSON content type is refused (415)", async () => {
    const u = await makeUser();
    const r = await worker.fetch(new Request(`${env.SITE_ORIGIN}/api/forecasts`, { method: "POST",
      headers: { cookie: u.cookie, origin: env.SITE_ORIGIN, "content-type": "text/plain", "cf-connecting-ip": "203.0.113.5" }, body: "{}" }));
    expect(r.status).toBe(415);
  });

  it("the per-IP save limiter trips, and a different address is unaffected", async () => {
    const u = await makeUser();
    const send = ip => worker.fetch(api("/api/forecasts", { method: "POST", body: validForecast(), headers: { cookie: u.cookie, "cf-connecting-ip": ip } }));
    const statuses = [];
    for (let i = 0; i < 7; i++) statuses.push((await send("203.0.113.99")).status);
    expect(statuses).toContain(429);
    expect(statuses.slice(0, 5).every(s => s === 201)).toBe(true);
    expect((await send("203.0.113.100")).status).toBe(201);
  });

  it("the per-account cap on live forecasts holds", async () => {
    const u = await makeUser();
    const cap = Number(env.MAX_FORECASTS_PER_USER);
    const at = new Date().toISOString();
    await env.DB.batch(Array.from({ length: cap }, (_, i) => env.DB.prepare(
      "INSERT INTO forecasts (id, user_id, body, model_ref, seats, seats_code_ref, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)")
      .bind(randomId(), u.id, "{}", "m", "{}", "0", at, at)));
    const r = await worker.fetch(api("/api/forecasts", { method: "POST", body: validForecast(), headers: { cookie: u.cookie, "cf-connecting-ip": "203.0.113.6" } }));
    expect(r.status).toBe(409);
  });
});
