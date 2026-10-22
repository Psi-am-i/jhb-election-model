// The daily save quota is taken only when a save succeeds (owner, 2026-09-29),
// and every forecast gets its own random default label (owner, 2026-09-29).
import { describe, it, expect } from "vitest";
import { env } from "cloudflare:test";
import { exports } from "cloudflare:workers";
import { createForecast, updateForecast } from "../src/forecasts.js";
import { LABEL_RE } from "../../interactive/js/labels.js";
import { makeUser, api, validForecast } from "./helpers.js";

const worker = exports.default;
let ipn = 0;
const ip = () => `198.51.100.${(++ipn % 250) + 1}`;
const req = (u, body = validForecast(), path = "/api/forecasts", method = "POST") =>
  api(path, { method, body, headers: { cookie: u.cookie, "cf-connecting-ip": ip() } });
const quota = async id => (await env.DB.prepare("SELECT COALESCE(SUM(n), 0) AS n FROM save_quota WHERE user_id = ?").bind(id).first()).n;

const refusing = { fetch: async () => Response.json({ errors: ["wards won by parties with a zero share"] }, { status: 422 }) };
const down = { fetch: async () => new Response("", { status: 501 }) };
const counting = () => { const c = { n: 0 }; c.fetch = async () => { c.n++; return Response.json({}, { status: 500 }); }; return c; };

describe("the daily quota is taken only on success", () => {
  it("a save the seat law refuses (422) leaves the quota untouched (the old code spent it)", async () => {
    const u = await makeUser();
    const e = { ...env, SAVES_PER_USER_PER_DAY: "1", SEATS: refusing };
    const r = await createForecast(req(u), e).catch(x => x);
    expect(r.status).toBe(422);
    expect(await quota(u.id)).toBe(0);
    // With a quota of one, the reader can still save once the picks are fixed.
    const ok = await createForecast(req(u), { ...env, SAVES_PER_USER_PER_DAY: "1" });
    expect(ok.status).toBe(201);
    expect(await quota(u.id)).toBe(1);
  });

  it("a seat service failure (503) leaves the quota untouched", async () => {
    const u = await makeUser();
    const r = await createForecast(req(u), { ...env, SEATS: down }).catch(x => x);
    expect(r.status).toBe(503);
    expect(await quota(u.id)).toBe(0);
  });

  it("an edit the seat law refuses leaves the quota untouched", async () => {
    const u = await makeUser();
    const { id } = await (await createForecast(req(u), env)).json();
    const before = await quota(u.id);
    const r = await updateForecast(req(u, validForecast(), `/api/forecasts/${id}`, "PUT"), { ...env, SEATS: refusing }, id).catch(x => x);
    expect(r.status).toBe(422);
    expect(await quota(u.id)).toBe(before);
  });

  it("an exhausted reader is refused BEFORE the seat service is called", async () => {
    const u = await makeUser();
    await createForecast(req(u), { ...env, SAVES_PER_USER_PER_DAY: "1" });
    const seats = counting();
    const r = await createForecast(req(u), { ...env, SAVES_PER_USER_PER_DAY: "1", SEATS: seats }).catch(x => x);
    expect(r.status).toBe(429);
    expect(seats.n).toBe(0);
    expect(await quota(u.id)).toBe(1);
  });

  it("the per-minute limiter still stands in front of the seat call", async () => {
    const u = await makeUser();
    const seats = counting();
    const a = "198.51.100.251";
    const statuses = [];
    for (let i = 0; i < 7; i++) {
      const r = await createForecast(api("/api/forecasts", { method: "POST", body: validForecast(), headers: { cookie: u.cookie, "cf-connecting-ip": a } }),
        { ...env, SEATS: seats }).catch(x => x);
      statuses.push(r.status);
    }
    expect(statuses).toContain(429);
    expect(seats.n).toBe(statuses.filter(s => s !== 429).length);
  });
});

describe("default labels: random, per forecast, unique", () => {
  it("a forecast with no label gets a <word>-<number> label, shown on its page and card", async () => {
    const u = await makeUser();
    const r = await (await createForecast(req(u, { ...validForecast(), display_name: null }), env)).json();
    expect(r.label).toMatch(LABEL_RE);
    expect(r.default_label).toBe(r.label);
    const pub = await (await worker.fetch(new Request(`${env.SITE_ORIGIN}/api/forecasts/${r.id}`))).json();
    expect(pub.display_name).toBe(r.label);
    const html = await (await worker.fetch(new Request(`${env.SITE_ORIGIN}/f/${r.id}`))).text();
    expect(html).toContain(`${r.label}&#39;s forecast`);
  });

  it("two forecasts by one reader get different labels (not linkable by label)", async () => {
    const u = await makeUser();
    const a = await (await createForecast(req(u, { ...validForecast(), display_name: null }), env)).json();
    const b = await (await createForecast(req(u, { ...validForecast(), display_name: null }), env)).json();
    expect(a.label).not.toBe(b.label);
  });

  it("a collision with another forecast's default label is retried", async () => {
    const u = await makeUser();
    await createForecast(req(u, { ...validForecast(), display_name: null }), env, Date.now(), () => "pollster-1");
    const seq = ["pollster-1", "pollster-1", "pollster-2"];
    const r = await (await createForecast(req(u, { ...validForecast(), display_name: null }), env, Date.now(), () => seq.shift())).json();
    expect(r.label).toBe("pollster-2");
    expect(seq.length).toBe(0);
  });

  it("a collision with a label held in a forecast's body is retried too", async () => {
    // The validator refuses a typed label of this shape, so the row is written
    // directly: the insert's own guard is what is tested here.
    const u = await makeUser();
    const at = new Date().toISOString();
    await env.DB.prepare("INSERT INTO forecasts (id, user_id, body, model_ref, seats, seats_code_ref, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)")
      .bind("Typed00005", u.id, JSON.stringify({ display_name: "analyst-5" }), "m", "{}", "0", at, at).run();
    const seq = ["analyst-5", "analyst-6"];
    const r = await (await createForecast(req(u, { ...validForecast(), display_name: null }), env, Date.now(), () => seq.shift())).json();
    expect(r.default_label).toBe("analyst-6");
  });

  it("a typed label is shown instead; clearing it brings back the forecast's own default", async () => {
    const u = await makeUser();
    const c = await (await createForecast(req(u, { ...validForecast(), display_name: "@reader_x" }), env)).json();
    expect(c.label).toBe("@reader_x");
    const up = await (await updateForecast(req(u, { ...validForecast(), display_name: null }, `/api/forecasts/${c.id}`, "PUT"), env, c.id)).json();
    expect(up.label).toBe(c.default_label);
    expect(up.label).toMatch(LABEL_RE);
  });

  it("a typed label in the random shape is refused at save", async () => {
    const u = await makeUser();
    const r = await createForecast(req(u, { ...validForecast(), display_name: "pollster-23" }), env).catch(x => x);
    expect(r.status).toBe(400);
    expect(r.field).toBe("display_name");
  });

  it("an email address is refused as a label", async () => {
    const u = await makeUser();
    const r = await createForecast(req(u, { ...validForecast(), display_name: "me@example.fr" }), env).catch(x => x);
    expect(r.status).toBe(400);
    expect(r.field).toBe("display_name");
  });
});
