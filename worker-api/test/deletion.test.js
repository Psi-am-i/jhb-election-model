// Deletion removes the user, their forecasts, their consent log, their sessions
// and every rendered card; /f/<id> answers 410 afterwards.
import { describe, it, expect } from "vitest";
import { env } from "cloudflare:test";
import { exports } from "cloudflare:workers";
import { makeUser, api, validForecast } from "./helpers.js";
import { runScheduled, parseSignedRequest } from "../src/lifecycle.js";
import { b64url, signToken } from "../src/crypto.js";

const worker = exports.default;
const count = async (sql, ...b) => (await env.DB.prepare(sql).bind(...b).first()).n;

async function saveAndRender(u) {
  // A distinct client address per save, so the per-IP limiter does not trip.
  const ip = `192.0.2.${Math.floor(Math.random() * 250) + 1}`;
  const r = await worker.fetch(api("/api/forecasts", { method: "POST", body: validForecast(), headers: { cookie: u.cookie, "cf-connecting-ip": ip } }));
  expect(r.status).toBe(201);
  const { id, rev } = await r.json();
  for (const f of ["card.png", "card-story.png"]) {
    const png = await worker.fetch(new Request(`${env.SITE_ORIGIN}/f/${id}/${f}?v=${rev}`));
    expect(png.status).toBe(200);
    await png.arrayBuffer();
  }
  // The card is written to R2 in waitUntil; wait for both objects to land.
  for (let i = 0; i < 50 && (await env.CARDS.list({ prefix: `cards/${id}/` })).objects.length < 2; i++)
    await new Promise(r => setTimeout(r, 20));
  expect((await env.CARDS.list({ prefix: `cards/${id}/` })).objects.length).toBe(2);
  return id;
}

describe("DELETE /api/forecasts/:id", () => {
  it("removes the row and its cards; the link answers 410", async () => {
    const u = await makeUser();
    const id = await saveAndRender(u);
    const r = await worker.fetch(api(`/api/forecasts/${id}`, { method: "DELETE", headers: { cookie: u.cookie } }));
    expect(r.status).toBe(204);
    expect(await count("SELECT COUNT(*) AS n FROM forecasts WHERE id = ?", id)).toBe(0);
    expect((await env.CARDS.list({ prefix: `cards/${id}/` })).objects).toEqual([]);
    expect((await worker.fetch(new Request(`${env.SITE_ORIGIN}/f/${id}`))).status).toBe(410);
    expect((await worker.fetch(new Request(`${env.SITE_ORIGIN}/api/forecasts/${id}`))).status).toBe(410);
    expect((await worker.fetch(new Request(`${env.SITE_ORIGIN}/f/${id}/card.png?v=1`))).status).toBe(410);
  });

  it("another reader cannot delete it (and cannot learn it exists)", async () => {
    const a = await makeUser(), b = await makeUser();
    const id = await saveAndRender(a);
    const r = await worker.fetch(api(`/api/forecasts/${id}`, { method: "DELETE", headers: { cookie: b.cookie } }));
    expect(r.status).toBe(404);
    expect(await count("SELECT COUNT(*) AS n FROM forecasts WHERE id = ?", id)).toBe(1);
  });
});

describe("DELETE /api/me", () => {
  it("removes user, forecasts, consents, sessions and cards", async () => {
    const u = await makeUser();
    const ids = [await saveAndRender(u), await saveAndRender(u)];
    const r = await worker.fetch(api("/api/me", { method: "DELETE", headers: { cookie: u.cookie } }));
    expect(r.status).toBe(200);
    expect(await r.json()).toEqual({ deleted: true, forecasts: 2 });
    for (const [t, col] of [["users", "id"], ["consents", "user_id"], ["sessions", "user_id"], ["forecasts", "user_id"], ["save_quota", "user_id"]])
      expect(await count(`SELECT COUNT(*) AS n FROM ${t} WHERE ${col} = ?`, u.id), t).toBe(0);
    for (const id of ids) {
      expect((await env.CARDS.list({ prefix: `cards/${id}/` })).objects).toEqual([]);
      expect(await count("SELECT COUNT(*) AS n FROM deleted_forecasts WHERE id = ?", id)).toBe(1);
      expect((await worker.fetch(new Request(`${env.SITE_ORIGIN}/f/${id}`))).status).toBe(410);
    }
    // The old session no longer works.
    expect((await worker.fetch(api("/api/my/forecasts", { headers: { cookie: u.cookie } }))).status).toBe(401);
  });

  it("leaves other readers untouched", async () => {
    const a = await makeUser(), b = await makeUser();
    const kept = await saveAndRender(b);
    await worker.fetch(api("/api/me", { method: "DELETE", headers: { cookie: a.cookie } }));
    expect(await count("SELECT COUNT(*) AS n FROM consents WHERE user_id = ?", b.id)).toBe(2);
    expect((await env.CARDS.list({ prefix: `cards/${kept}/` })).objects.length).toBe(2);
  });

  it("refuses without a session and cross-origin", async () => {
    const u = await makeUser();
    expect((await worker.fetch(api("/api/me", { method: "DELETE" }))).status).toBe(401);
    expect((await worker.fetch(api("/api/me", { method: "DELETE", origin: false, headers: { cookie: u.cookie, origin: "https://evil.example" } }))).status).toBe(403);
    expect(await count("SELECT COUNT(*) AS n FROM users WHERE id = ?", u.id)).toBe(1);
  });
});

describe("Facebook data-deletion callback", () => {
  async function signed(payload, secret = env.FACEBOOK_APP_SECRET) {
    const body = b64url(new TextEncoder().encode(JSON.stringify(payload)));
    const k = await crypto.subtle.importKey("raw", new TextEncoder().encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
    const sig = b64url(new Uint8Array(await crypto.subtle.sign("HMAC", k, new TextEncoder().encode(body))));
    return `${sig}.${body}`;
  }
  const post = sr => worker.fetch(new Request(`${env.SITE_ORIGIN}/auth/facebook/data-deletion`, {
    method: "POST", headers: { "content-type": "application/x-www-form-urlencoded" }, body: `signed_request=${encodeURIComponent(sr)}` }));

  it("deletes the matching account on a correctly signed request", async () => {
    const u = await makeUser({ provider: "facebook", sub: "fb-123" });
    await saveAndRender(u);
    const r = await post(await signed({ algorithm: "HMAC-SHA256", user_id: "fb-123" }));
    expect(r.status).toBe(200);
    expect(Object.keys(await r.json()).sort()).toEqual(["confirmation_code", "url"]);
    expect(await count("SELECT COUNT(*) AS n FROM users WHERE id = ?", u.id)).toBe(0);
  });

  it("refuses a request signed with another secret, and deletes nothing", async () => {
    const u = await makeUser({ provider: "facebook", sub: "fb-456" });
    const r = await post(await signed({ algorithm: "HMAC-SHA256", user_id: "fb-456" }, "wrong-secret"));
    expect(r.status).toBe(400);
    expect(await count("SELECT COUNT(*) AS n FROM users WHERE id = ?", u.id)).toBe(1);
    expect(await parseSignedRequest("a.b.c", env.FACEBOOK_APP_SECRET)).toBe(null);
  });
});

describe("post-election message and deletion run", () => {
  const dates = { POST_ELECTION_MESSAGE_AT: "2026-11-20T09:00:00+02:00", DELETION_AT: "2027-01-31T09:00:00+02:00" };
  const later = Date.parse("2027-02-01T00:00:00Z");

  it("does nothing while the owner has not set the dates", async () => {
    const u = await makeUser();
    const r = await runScheduled(env, later);
    expect(r.skipped).toBe("dates not set");
    expect(await count("SELECT COUNT(*) AS n FROM users WHERE id = ?", u.id)).toBe(1);
  });

  it("refuses to delete anyone while the message has not been sent (mail is a stub)", async () => {
    const u = await makeUser();
    const r = await runScheduled({ ...env, ...dates }, later);
    expect(r.message.sent).toBe(0);
    expect(r.deletion).toMatch(/refused/);
    expect(await count("SELECT COUNT(*) AS n FROM users WHERE id = ?", u.id)).toBe(1);
  });

  it("once the message is recorded as sent: no reply => deleted; 'notify me' => kept, forecasts gone", async () => {
    const silent = await makeUser(), keen = await makeUser();
    const kf = await saveAndRender(keen);
    // The reply, as the reader's click would post it.
    const t = await signToken(env.SESSION_SIGNING_KEY, "reply", { u: keen.id, c: "notify" }, 3600);
    const rep = await worker.fetch(new Request(`${env.SITE_ORIGIN}/api/reply`, {
      method: "POST", headers: { "content-type": "application/x-www-form-urlencoded" }, body: `t=${encodeURIComponent(t)}` }));
    expect(rep.status).toBe(200);
    await env.DB.prepare("INSERT INTO jobs (name, done_at, detail) VALUES ('post_election_message', ?, '{}')").bind(new Date().toISOString()).run();
    const r = await runScheduled({ ...env, ...dates }, later);
    expect(r.deletion.kept).toBeGreaterThanOrEqual(1);
    expect(await count("SELECT COUNT(*) AS n FROM users WHERE id = ?", silent.id)).toBe(0);
    expect(await count("SELECT COUNT(*) AS n FROM users WHERE id = ?", keen.id)).toBe(1);
    expect(await count("SELECT COUNT(*) AS n FROM forecasts WHERE user_id = ?", keen.id)).toBe(0);
    expect((await env.CARDS.list({ prefix: `cards/${kf}/` })).objects).toEqual([]);
  });

  it("the reply link's GET never acts (mail scanners follow links)", async () => {
    const u = await makeUser();
    const t = await signToken(env.SESSION_SIGNING_KEY, "reply", { u: u.id, c: "delete" }, 3600);
    const r = await worker.fetch(new Request(`${env.SITE_ORIGIN}/api/reply?t=${encodeURIComponent(t)}`));
    expect(r.status).toBe(200);
    expect(await r.text()).toMatch(/<form method="post"/);
    expect(await count("SELECT COUNT(*) AS n FROM users WHERE id = ?", u.id)).toBe(1);
  });

  it("a reply token for one purpose is refused at another", async () => {
    const u = await makeUser();
    const t = await signToken(env.SESSION_SIGNING_KEY, "pending", { u: u.id, c: "delete" }, 3600);
    const r = await worker.fetch(new Request(`${env.SITE_ORIGIN}/api/reply`, {
      method: "POST", headers: { "content-type": "application/x-www-form-urlencoded" }, body: `t=${encodeURIComponent(t)}` }));
    expect(await r.text()).toMatch(/expired/);
    expect(await count("SELECT COUNT(*) AS n FROM users WHERE id = ?", u.id)).toBe(1);
  });
});

