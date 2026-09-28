// Deletion removes the user, their forecasts, their consent log, their sessions
// and every rendered card; /f/<id> answers 410 afterwards.
import { describe, it, expect, beforeEach, vi } from "vitest";
import { env } from "cloudflare:test";
import { exports } from "cloudflare:workers";
import { makeUser, api, validForecast } from "./helpers.js";
import { runScheduled, parseSignedRequest, handleEmailEvents } from "../src/lifecycle.js";
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

describe("post-election message and deletion run (R5 finding 1)", () => {
  const dates = { POST_ELECTION_MESSAGE_AT: "2026-11-20T09:00:00+02:00", DELETION_AT: "2027-01-31T09:00:00+02:00" };
  const during = Date.parse("2026-12-01T00:00:00Z");
  const later = Date.parse("2027-02-01T00:00:00Z");
  // Each test starts from no accounts and no job records, so counts are its own.
  beforeEach(async () => {
    await env.DB.batch([env.DB.prepare("DELETE FROM users"), env.DB.prepare("DELETE FROM consents"), env.DB.prepare("DELETE FROM jobs")]);
  });
  // A mail binding that records every send and throws `code` for the addresses in `fail`.
  function mail(fail = {}) {
    const sent = [];
    return { sent, env: { ...env, ...dates, MAIL_FROM: "n@example.test", EMAIL: { send: async m => {
      if (fail[m.to]) throw Object.assign(new Error("refused"), { code: fail[m.to] });
      sent.push(m); return { messageId: String(sent.length) };
    } } } };
  }
  const users = async () => (await env.DB.prepare("SELECT id, contact, message_sent_at, message_status FROM users").all()).results;

  it("does nothing while the owner has not set the dates", async () => {
    const u = await makeUser();
    const r = await runScheduled(env, later);
    expect(r.skipped).toBe("dates not set");
    expect(await count("SELECT COUNT(*) AS n FROM users WHERE id = ?", u.id)).toBe(1);
  });

  it("mail unconfigured: nothing stamped, nobody deleted, and the refusal is raised as an alert", async () => {
    const u = await makeUser();
    const spy = vi.spyOn(console, "error");
    const r = await runScheduled({ ...env, ...dates }, later);
    expect(r.message).toMatchObject({ sent: 0, undeliverable: 0, failed: 1, remaining: 1 });
    expect(r.deletion.refused).toMatch(/not sent/);
    expect(await count("SELECT COUNT(*) AS n FROM users WHERE id = ?", u.id)).toBe(1);
    const alerts = spy.mock.calls.map(c => { try { return JSON.parse(c[0]); } catch { return null; } }).filter(x => x?.alert === "deletion_refused");
    expect(alerts.length).toBe(1);
    expect(alerts[0]).toMatchObject({ level: "alert", unsent: 1 });
    spy.mockRestore();
  });

  it("a hard-bounced (suppressed) address is recorded undeliverable-sent and does not block deletion (the old run never completed)", async () => {
    const good = await makeUser({ contact: "good@example.com" }), bad = await makeUser({ contact: "gone@example.com" });
    const m = mail({ "gone@example.com": "E_RECIPIENT_SUPPRESSED" });
    const r1 = await runScheduled(m.env, during);
    expect(r1.message).toMatchObject({ sent: 1, undeliverable: 1, failed: 0, remaining: 0 });
    const byId = Object.fromEntries((await users()).map(u => [u.id, u]));
    expect(byId[good.id].message_status).toBe("sent");
    expect(byId[bad.id].message_status).toBe("undeliverable");
    const r2 = await runScheduled(m.env, later);
    expect(r2.deletion).toMatchObject({ deleted: 2, done: true });
  });

  it("a sender-side failure is transient for everyone: nobody is marked undeliverable", async () => {
    await makeUser({ contact: "a@example.com" }); await makeUser({ contact: "b@example.com" });
    const m = mail({ "a@example.com": "E_SENDER_NOT_VERIFIED", "b@example.com": "E_SENDER_NOT_VERIFIED" });
    const r = await runScheduled(m.env, later);
    expect(r.message).toMatchObject({ failed: 2, remaining: 2 });
    expect((await users()).every(u => u.message_sent_at === null)).toBe(true);
    expect(r.deletion.refused).toBeTruthy();
  });

  it("sends in batches, never twice to one account, and resumes where it stopped", async () => {
    for (let i = 0; i < 5; i++) await makeUser({ contact: `r${i}@example.com` });
    const m = mail();
    const e = { ...m.env, MESSAGE_BATCH_SIZE: "2", MAIL_CONCURRENCY: "2" };
    expect((await runScheduled(e, during)).message).toMatchObject({ sent: 2, remaining: 3 });
    expect((await runScheduled(e, during)).message).toMatchObject({ sent: 2, remaining: 1 });
    expect((await runScheduled(e, during)).message).toMatchObject({ sent: 1, remaining: 0 });
    expect((await runScheduled(e, during)).message).toMatchObject({ sent: 0, remaining: 0 });
    const to = m.sent.map(x => x.to).sort();
    expect(to).toEqual([0, 1, 2, 3, 4].map(i => `r${i}@example.com`));
    expect(await count("SELECT COUNT(*) AS n FROM jobs WHERE name = 'post_election_message'")).toBe(1);
  });

  it("the reply links carry the token in the fragment, never the query string (R5 finding 10)", async () => {
    await makeUser({ contact: "f@example.com" });
    const m = mail();
    await runScheduled(m.env, during);
    expect(m.sent[0].text).toMatch(/\/api\/reply\/delete#t=\S+/);
    expect(m.sent[0].text).toMatch(/\/api\/reply\/notify#t=\S+/);
    expect(m.sent[0].text).not.toMatch(/\?t=/);
  });

  it("a hard bounce reported later marks the account undeliverable; a soft one changes nothing", async () => {
    const u = await makeUser({ contact: "later@example.com" });
    const m = mail();
    await runScheduled(m.env, during);
    const ev = type => ({ type: "cf.email.sending.message.bounced", payload: { recipient: "Later@example.com", bounce: { type } } });
    expect(await handleEmailEvents(env, [ev("soft")])).toBe(0);
    expect((await env.DB.prepare("SELECT message_status FROM users WHERE id = ?").bind(u.id).first()).message_status).toBe("sent");
    expect(await handleEmailEvents(env, [ev("hard"), { type: "other" }])).toBe(1);
    expect((await env.DB.prepare("SELECT message_status FROM users WHERE id = ?").bind(u.id).first()).message_status).toBe("undeliverable");
  });

  it("accounts with no confirmed contact get no message, do not block the run, and are deleted (finding 2)", async () => {
    const none = await makeUser({ contact: null, verified: 0 });
    const m = mail();
    const r = await runScheduled(m.env, later);
    expect(m.sent.length).toBe(0);
    expect(r.deletion).toMatchObject({ deleted: 1, done: true });
    expect(await count("SELECT COUNT(*) AS n FROM users WHERE id = ?", none.id)).toBe(0);
  });

  it("no reply => deleted; 'notify me' => kept, forecasts gone; in batches", async () => {
    const silent = await makeUser({ contact: "s@example.com" }), keen = await makeUser({ contact: "k@example.com" });
    const kf = await saveAndRender(keen);
    const m = mail();
    await runScheduled(m.env, during);
    // The reply, as the reader's click would post it (the token read from the mail).
    const t = decodeURIComponent(/notify#t=(\S+)/.exec(m.sent.find(x => x.to === "k@example.com").text)[1]);
    const rep = await worker.fetch(new Request(`${env.SITE_ORIGIN}/api/reply`, {
      method: "POST", headers: { "content-type": "application/x-www-form-urlencoded" }, body: `t=${encodeURIComponent(t)}&c=notify` }));
    expect(await rep.text()).toMatch(/Thank you/);
    const e = { ...m.env, DELETION_BATCH_SIZE: "1" };
    const r1 = await runScheduled(e, later);
    expect(r1.deletion.done).toBe(false);
    const r2 = await runScheduled(e, later);
    const r3 = await runScheduled(e, later);
    expect([r1, r2, r3].some(r => r.deletion?.done)).toBe(true);
    expect(await count("SELECT COUNT(*) AS n FROM users WHERE id = ?", silent.id)).toBe(0);
    expect(await count("SELECT COUNT(*) AS n FROM users WHERE id = ?", keen.id)).toBe(1);
    expect(await count("SELECT COUNT(*) AS n FROM forecasts WHERE user_id = ?", keen.id)).toBe(0);
    expect((await env.CARDS.list({ prefix: `cards/${kf}/` })).objects).toEqual([]);
  });

  it("the reply link's GET never acts (mail scanners follow links), and carries no token", async () => {
    const u = await makeUser();
    const r = await worker.fetch(new Request(`${env.SITE_ORIGIN}/api/reply/delete`));
    expect(r.status).toBe(200);
    const html = await r.text();
    expect(html).toMatch(/<form method="post" action="\/api\/reply">/);
    expect(html).toMatch(/location\.hash/);
    expect(await count("SELECT COUNT(*) AS n FROM users WHERE id = ?", u.id)).toBe(1);
  });

  it("a reply token for one purpose is refused at another; a button that does not match the link is refused", async () => {
    const u = await makeUser();
    const send = body => worker.fetch(new Request(`${env.SITE_ORIGIN}/api/reply`, {
      method: "POST", headers: { "content-type": "application/x-www-form-urlencoded" }, body }));
    const wrongPurpose = await signToken(env.SESSION_SIGNING_KEY, "pending", { u: u.id, c: "delete" }, 3600);
    expect(await (await send(`t=${encodeURIComponent(wrongPurpose)}&c=delete`)).text()).toMatch(/expired/);
    const notify = await signToken(env.SESSION_SIGNING_KEY, "reply", { u: u.id, c: "notify" }, 3600);
    expect(await (await send(`t=${encodeURIComponent(notify)}&c=delete`)).text()).toMatch(/does not match/);
    expect(await count("SELECT COUNT(*) AS n FROM users WHERE id = ?", u.id)).toBe(1);
  });
});
