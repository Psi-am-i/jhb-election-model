// The consent log is append-only, and the consent screen refuses defaults.
import { describe, it, expect } from "vitest";
import { env } from "cloudflare:test";
import { exports } from "cloudflare:workers";
import { makeUser, pendingCookie, api } from "./helpers.js";
import { deleteUser } from "../src/deletion.js";

const worker = exports.default;
const rows = async uid => (await env.DB.prepare("SELECT * FROM consents WHERE user_id = ? ORDER BY id").bind(uid).all()).results;

describe("append-only consent log", () => {
  it("accepts an insert", async () => {
    const u = await makeUser();
    await env.DB.prepare("INSERT INTO consents (user_id, purpose, granted, wording_version, at) VALUES (?, 'updates', 1, 'v', 'now')").bind(u.id).run();
    expect((await rows(u.id)).length).toBe(3);
  });

  it("refuses an UPDATE of any row", async () => {
    const u = await makeUser();
    await expect(env.DB.prepare("UPDATE consents SET granted = 0 WHERE user_id = ?").bind(u.id).run())
      .rejects.toThrow(/append-only/);
    expect((await rows(u.id)).every(r => r.granted === 1)).toBe(true);
  });

  it("refuses a DELETE while the account exists", async () => {
    const u = await makeUser();
    await expect(env.DB.prepare("DELETE FROM consents WHERE user_id = ?").bind(u.id).run())
      .rejects.toThrow(/append-only/);
    expect((await rows(u.id)).length).toBe(2);
  });

  it("the log goes with the account, and only then", async () => {
    const u = await makeUser();
    await deleteUser(env, u.id);
    expect(await rows(u.id)).toEqual([]);
    expect(await env.DB.prepare("SELECT 1 FROM users WHERE id = ?").bind(u.id).first()).toBe(null);
  });

  it("a withdrawal appends a row and leaves the earlier rows untouched", async () => {
    const u = await makeUser();
    const before = await rows(u.id);
    const r = await worker.fetch(api("/api/consent", { method: "POST", headers: { cookie: u.cookie },
      body: { store: true, age18: true, contact_if_win: false, updates: false } }));
    expect(r.status).toBe(200);
    const after = await rows(u.id);
    expect(after.slice(0, before.length)).toEqual(before);
    expect(after.length).toBe(before.length + 4);
    expect(after.at(-1).wording_version).toBe(env.CONSENT_WORDING_VERSION);
  });
});

describe("the consent screen", () => {
  const all = { store: true, age18: true, contact_if_win: false, updates: true };

  it("creates the account only on consent, with one row per choice", async () => {
    const sub = "g-" + crypto.randomUUID();
    expect(await env.DB.prepare("SELECT 1 FROM users WHERE provider_sub = ?").bind(sub).first()).toBe(null);
    const r = await worker.fetch(api("/api/consent", { method: "POST", body: all,
      headers: { cookie: await pendingCookie({ provider: "google", sub, ck: "email", c: "a@example.com", cv: 1, r: "/" }) } }));
    expect(r.status).toBe(201);
    const u = await env.DB.prepare("SELECT * FROM users WHERE provider_sub = ?").bind(sub).first();
    expect(u.contact).toBe("a@example.com");
    const got = Object.fromEntries((await rows(u.id)).map(x => [x.purpose, x.granted]));
    expect(got).toEqual({ store: 1, age18: 1, contact_if_win: 0, updates: 1 });
    expect(r.headers.getSetCookie().some(c => /session=/.test(c))).toBe(true);
  });

  for (const k of ["store", "age18", "contact_if_win", "updates"]) {
    it(`refuses a missing "${k}" rather than defaulting it`, async () => {
      const body = { ...all }; delete body[k];
      const r = await worker.fetch(api("/api/consent", { method: "POST", body,
        headers: { cookie: await pendingCookie({ provider: "google", sub: "x", ck: null, c: null, cv: 0, r: "/" }) } }));
      expect(r.status).toBe(400);
      expect((await r.json()).field).toBe(k);
    });
  }

  it("refuses to create an account without the storage consent", async () => {
    const sub = "g-" + crypto.randomUUID();
    const r = await worker.fetch(api("/api/consent", { method: "POST", body: { ...all, store: false },
      headers: { cookie: await pendingCookie({ provider: "google", sub, ck: null, c: null, cv: 0, r: "/" }) } }));
    expect(r.status).toBe(400);
    expect(await env.DB.prepare("SELECT 1 FROM users WHERE provider_sub = ?").bind(sub).first()).toBe(null);
  });

  it("refuses a forged pending cookie", async () => {
    const r = await worker.fetch(api("/api/consent", { method: "POST", body: all,
      headers: { cookie: "__Host-pending=eyJ4IjoxfQ.AAAA" } }));
    expect(r.status).toBe(401);
  });

  it("refuses a cross-origin consent post", async () => {
    const r = await worker.fetch(api("/api/consent", { method: "POST", body: all, origin: false,
      headers: { origin: "https://evil.example" } }));
    expect(r.status).toBe(403);
  });
});
