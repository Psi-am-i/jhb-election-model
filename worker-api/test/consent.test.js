// The consent log is append-only, and the consent screen refuses defaults.
import { describe, it, expect, beforeAll, vi } from "vitest";
import { env } from "cloudflare:test";
import { exports } from "cloudflare:workers";
import { makeUser, pendingCookie, api } from "./helpers.js";
import { deleteUser } from "../src/deletion.js";
import { postConsent, currentWordingVersion, sendConfirmation, confirmPost } from "../src/consent.js";
import { signToken } from "../src/crypto.js";
import { consentPayload, consentTerms, wordingVersion, deletionDateText } from "../../interactive/js/consent-terms.js";

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
      body: { store: true, age18: true, contact_if_win: false, updates: false, wording_version: await currentWordingVersion(env) } }));
    expect(r.status).toBe(200);
    const after = await rows(u.id);
    expect(after.slice(0, before.length)).toEqual(before);
    expect(after.length).toBe(before.length + 4);
    expect(after.at(-1).wording_version).toBe(await currentWordingVersion(env));
  });
});

// The four choices plus the wording version the server expects today.
let all;
beforeAll(async () => { all = { store: true, age18: true, contact_if_win: false, updates: true, wording_version: await currentWordingVersion(env) }; });

describe("the consent screen", () => {

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

// ---- R5 finding 6: the page and the server agree ---------------------------

const pending = (extra = {}) => pendingCookie({ provider: "google", sub: "g-" + crypto.randomUUID(), ck: "email", c: "a@example.com", cv: 1, r: "/", ...extra });
const post = async (body, cookie) => worker.fetch(api("/api/consent", { method: "POST", body, headers: { cookie } }));

describe("the consent page's payload is what the server accepts (R5 finding 6)", () => {
  it("the old page's body is refused (every consent returned 400)", async () => {
    const old = { store: true, age18: true, show_name: true, display_name: "Thandi M.", contact_if_win: false, updates: false, email: null };
    const r = await post(old, await pending());
    expect(r.status).toBe(400);
    expect((await r.json()).field).toBe("show_name");
  });

  it("the body the page builds (consentPayload, the page's own hash) creates the account", async () => {
    // The page's side, exactly: terms from /api/me's deletion date, hashed.
    const me = await (await worker.fetch(api("/api/me"))).json();
    const version = await wordingVersion(consentTerms({ deletionDate: deletionDateText(me.deletion_date) }));
    expect(version).toBe(me.wording_version);
    const r = await post(consentPayload({ store: true, age18: true, contact_if_win: true, updates: false, contact: "", wording_version: version }), await pending());
    expect(r.status).toBe(201);
  });

  it("a stale page (text changed since it loaded) is refused with 409 and nothing is stored", async () => {
    const sub = "g-" + crypto.randomUUID();
    const r = await post({ ...all, wording_version: "w1-000000000000000000000000" }, await pendingCookie({ provider: "google", sub, ck: null, c: null, cv: 0, r: "/" }));
    expect(r.status).toBe(409);
    expect((await r.json()).field).toBe("wording_version");
    expect(await env.DB.prepare("SELECT 1 FROM users WHERE provider_sub = ?").bind(sub).first()).toBe(null);
  });

  it("the recorded version is the hash of the text with the server's deletion date", async () => {
    const withDate = { ...env, DELETION_AT: "2027-01-31T09:00:00+02:00" };
    const v = await currentWordingVersion(withDate);
    expect(v).not.toBe(await currentWordingVersion(env));
    expect(v).toBe(await wordingVersion(consentTerms({ deletionDate: "2027-01-31" })));
  });

  it("a missing wording_version is refused", async () => {
    const { wording_version, ...rest } = all; void wording_version;
    const r = await post(rest, await pending());
    expect(r.status).toBe(400);
    expect((await r.json()).field).toBe("wording_version");
  });
});

// ---- R5 findings 2 and 7: only confirmed contacts ---------------------------

function fakeMail() {
  const sent = [];
  return { sent, EMAIL: { send: async m => { sent.push(m); return { messageId: "m" + sent.length }; } }, MAIL_FROM: "noreply@example.test" };
}
const consentReq = (body, cookie) => api("/api/consent", { method: "POST", body, headers: { cookie } });
const userBySub = sub => env.DB.prepare("SELECT * FROM users WHERE provider_sub = ?").bind(sub).first();

describe("contacts are stored only once confirmed (R5 findings 2, 7)", () => {
  it("a provider-VERIFIED address is stored at consent", async () => {
    const sub = "g-" + crypto.randomUUID();
    const r = await post(all, await pendingCookie({ provider: "google", sub, ck: "email", c: "v@example.com", cv: 1, r: "/" }));
    expect(r.status).toBe(201);
    const u = await userBySub(sub);
    expect([u.contact, u.contact_verified]).toEqual(["v@example.com", 1]);
  });

  it("an address the provider did NOT verify is not stored (the old code stored it as unverified)", async () => {
    const sub = "fb-" + crypto.randomUUID();
    const r = await post(all, await pendingCookie({ provider: "facebook", sub, ck: "email", c: "u@example.com", cv: 0, r: "/" }));
    expect(r.status).toBe(201);
    const u = await userBySub(sub);
    expect([u.contact, u.contact_kind, u.contact_verified]).toEqual([null, null, 0]);
  });

  it("a TYPED address is not stored, and no mail goes to it while mail is unconfigured", async () => {
    const sub = "x-" + crypto.randomUUID();
    const r = await post({ ...all, contact: "typed@example.com" }, await pendingCookie({ provider: "x", sub, ck: null, c: null, cv: 0, r: "/" }));
    expect(r.status).toBe(201);
    expect((await r.json()).confirmation).toBe("not_sent");
    const u = await userBySub(sub);
    expect(u.contact).toBe(null);
    expect(u.confirm_sent_at).toBe(null);
  });

  it("exactly one confirmation email per account; its link carries the token in the fragment", async () => {
    const m = fakeMail();
    const sub = "x-" + crypto.randomUUID();
    const r = await postConsent(consentReq({ ...all, contact: "typed@example.com" }, await pendingCookie({ provider: "x", sub, ck: null, c: null, cv: 0, r: "/" })), { ...env, ...m });
    expect((await r.json()).confirmation).toBe("sent");
    const u = await userBySub(sub);
    expect(u.contact).toBe(null);
    expect(u.confirm_sent_at).not.toBe(null);
    expect(m.sent.length).toBe(1);
    expect(m.sent[0].to).toBe("typed@example.com");
    expect(m.sent[0].text).toMatch(/\/api\/contact\/confirm#t=/);
    expect(m.sent[0].text).not.toMatch(/\?t=/);
    // A second request, to any address, sends nothing.
    expect(await sendConfirmation({ ...env, ...m }, u.id, "other@example.com")).toBe("already_sent");
    expect(m.sent.length).toBe(1);
  });

  it("the link's GET never acts; its POST stores the address as confirmed", async () => {
    const m = fakeMail();
    const sub = "fb-" + crypto.randomUUID();
    await postConsent(consentReq({ ...all, contact: "mine@example.com" }, await pendingCookie({ provider: "facebook", sub, ck: "email", c: "mine@example.com", cv: 0, r: "/" })), { ...env, ...m });
    const t = decodeURIComponent(/#t=(\S+)/.exec(m.sent[0].text)[1]);
    const u0 = await userBySub(sub);
    const get = await worker.fetch(new Request(`${env.SITE_ORIGIN}/api/contact/confirm`));
    expect(await get.text()).toMatch(/<form method="post" action="\/api\/contact\/confirm">[\s\S]*location\.hash/);
    expect((await userBySub(sub)).contact).toBe(null);
    const post2 = await worker.fetch(new Request(`${env.SITE_ORIGIN}/api/contact/confirm`, { method: "POST",
      headers: { "content-type": "application/x-www-form-urlencoded" }, body: `t=${encodeURIComponent(t)}` }));
    expect(await post2.text()).toMatch(/Confirmed/);
    const u = await userBySub(sub);
    expect([u.id, u.contact, u.contact_kind, u.contact_verified]).toEqual([u0.id, "mine@example.com", "email", 1]);
  });

  it("a token for another purpose, or for an account that already has a contact, changes nothing", async () => {
    const u = await makeUser({ contact: "held@example.com" });
    const wrong = await signToken(env.SESSION_SIGNING_KEY, "reply", { u: u.id, c: "x@example.com" }, 600);
    const form = t => new Request(`${env.SITE_ORIGIN}/api/contact/confirm`, { method: "POST",
      headers: { "content-type": "application/x-www-form-urlencoded" }, body: `t=${encodeURIComponent(t)}` });
    expect(await (await confirmPost(form(wrong), env)).text()).toMatch(/expired/);
    const right = await signToken(env.SESSION_SIGNING_KEY, "confirm", { u: u.id, c: "x@example.com" }, 600);
    expect(await (await confirmPost(form(right), env)).text()).toMatch(/Nothing to do/);
    expect((await env.DB.prepare("SELECT contact FROM users WHERE id = ?").bind(u.id).first()).contact).toBe("held@example.com");
  });

  it("an address is never logged when mail fails", async () => {
    const spy = vi.spyOn(console, "error");
    const failing = { EMAIL: { send: async () => { throw Object.assign(new Error("x"), { code: "E_DELIVERY_FAILED" }); } }, MAIL_FROM: "n@example.test" };
    const u = await makeUser({ contact: null, verified: 0 });
    expect(await sendConfirmation({ ...env, ...failing }, u.id, "secret-address@example.com")).toBe("not_sent");
    expect(spy.mock.calls.flat().join(" ")).not.toMatch(/secret-address/);
    spy.mockRestore();
  });
});

// ---- owner, 2026-09-29: the X username is offered, never stored ----------

describe("the X username", () => {
  it("is returned to the page while pending and after consent, and never written to D1", async () => {
    const sub = "x-" + crypto.randomUUID();
    const pc = await pendingCookie({ provider: "x", sub, ck: null, c: null, cv: 0, h: "reader_x", r: "/" });
    expect((await (await worker.fetch(api("/api/me", { headers: { cookie: pc } }))).json()).handle).toBe("reader_x");
    const r = await post(all, pc);
    expect(r.status).toBe(201);
    const cookies = r.headers.getSetCookie().map(c => c.split(";")[0]).join("; ");
    const me = await (await worker.fetch(api("/api/me", { headers: { cookie: cookies } }))).json();
    expect(me.handle).toBe("reader_x");
    const u = await userBySub(sub);
    expect(JSON.stringify(u)).not.toMatch(/reader_x/);
  });
});

describe("POST /api/contact: ask for the one confirmation email", () => {
  const ask = (u, body, extra = {}) => api("/api/contact", { method: "POST", body, headers: { cookie: u?.cookie || "", "cf-connecting-ip": "203.0.113.77" }, ...extra });
  it("refuses without a session, and cross-origin", async () => {
    expect((await worker.fetch(ask(null, { contact: "a@example.com" }))).status).toBe(401);
    const u = await makeUser({ contact: null, verified: 0 });
    expect((await worker.fetch(ask(u, { contact: "a@example.com" }, { origin: false }))).status).toBe(403);
  });
  it("refuses an unknown key and a non-address", async () => {
    const u = await makeUser({ contact: null, verified: 0 });
    expect((await (await worker.fetch(ask(u, { contact: "a@example.com", display_name: "x" }))).json()).field).toBe("display_name");
    expect((await worker.fetch(ask(u, { contact: "not an address" }))).status).toBe(400);
  });
  it("sends one email; a second request sends nothing", async () => {
    const { requestConfirmation } = await import("../src/consent.js");
    const m = fakeMail();
    const u = await makeUser({ contact: null, verified: 0 });
    const r1 = await (await requestConfirmation(ask(u, { contact: "a@example.com" }), { ...env, ...m })).json();
    const r2 = await (await requestConfirmation(ask(u, { contact: "b@example.com" }), { ...env, ...m })).json();
    expect([r1.confirmation, r2.confirmation]).toEqual(["sent", "already_sent"]);
    expect(m.sent.map(x => x.to)).toEqual(["a@example.com"]);
  });
  it("refuses when a confirmed contact is already held", async () => {
    const u = await makeUser({ contact: "held@example.com" });
    expect((await worker.fetch(ask(u, { contact: "a@example.com" }))).status).toBe(400);
  });
});
