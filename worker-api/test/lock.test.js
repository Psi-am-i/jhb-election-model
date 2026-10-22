// The election-day lock: 07:00 SAST on 4 November 2026 (LOCK_AT, a config value).
import { describe, it, expect } from "vitest";
import { env } from "cloudflare:test";
import { isLocked, instantVar } from "../src/http.js";
import { createForecast, updateForecast, removeForecast } from "../src/forecasts.js";
import { stampLocks } from "../src/lifecycle.js";
import { makeUser, api, validForecast } from "./helpers.js";

const at = s => Date.parse(s);
const BEFORE = at("2026-11-04T06:59:59+02:00");
const AT = at("2026-11-04T07:00:00+02:00");

// A distinct client address per save, so the per-IP save limiter never trips here.
let ipn = 0;
const ip = () => `192.0.2.${++ipn}`;

async function save(u, now = BEFORE) {
  const r = await createForecast(api("/api/forecasts", { method: "POST", body: validForecast(), headers: { cookie: u.cookie, "cf-connecting-ip": ip() } }), env, now);
  return r.json();
}

describe("lock time", () => {
  it("reads the configured instant, not a typed one", () => {
    expect(instantVar(env, "LOCK_AT")).toBe(Date.parse(env.LOCK_AT));
    expect(new Date(instantVar(env, "LOCK_AT")).toISOString()).toBe("2026-11-04T05:00:00.000Z");
  });
  it("is open one second before 07:00 SAST and locked at 07:00:00", () => {
    expect(isLocked(env, BEFORE)).toBe(false);
    expect(isLocked(env, AT)).toBe(true);
  });
  it("refuses a lock time without an explicit offset", () => {
    expect(() => isLocked({ LOCK_AT: "2026-11-04T07:00:00" })).toThrow(/offset/);
  });
  it("refuses to run with no lock time at all", () => {
    expect(() => isLocked({ LOCK_AT: "" })).toThrow(/LOCK_AT/);
  });
});

describe("writes around the lock", () => {
  it("saves before the lock", async () => {
    const u = await makeUser();
    const r = await createForecast(api("/api/forecasts", { method: "POST", body: validForecast(), headers: { cookie: u.cookie, "cf-connecting-ip": ip() } }), env, BEFORE);
    expect(r.status).toBe(201);
  });

  it("refuses a new forecast at the lock", async () => {
    const u = await makeUser();
    const r = await createForecast(api("/api/forecasts", { method: "POST", body: validForecast(), headers: { cookie: u.cookie } }), env, AT)
      .catch(e => e);
    expect(r.status).toBe(423);
  });

  it("refuses an edit at the lock, even before the stamp", async () => {
    const u = await makeUser();
    const { id } = await save(u);
    const e = await updateForecast(api(`/api/forecasts/${id}`, { method: "PUT", body: validForecast(), headers: { cookie: u.cookie } }), env, id, AT)
      .catch(x => x);
    expect(e.status).toBe(423);
  });

  it("the stamp locks rows; a stamped row refuses edits whatever the clock says", async () => {
    const u = await makeUser();
    const { id } = await save(u);
    expect(await stampLocks(env, BEFORE)).toBe(0);
    expect(await stampLocks(env, AT)).toBeGreaterThan(0);
    const row = await env.DB.prepare("SELECT locked_at FROM forecasts WHERE id = ?").bind(id).first();
    expect(row.locked_at).toBe(new Date(AT).toISOString());
    const e = await updateForecast(api(`/api/forecasts/${id}`, { method: "PUT", body: validForecast(), headers: { cookie: u.cookie } }), env, id, BEFORE)
      .catch(x => x);
    expect(e.status).toBe(423);
  });

  it("deletion stays open after the lock", async () => {
    const u = await makeUser();
    const { id } = await save(u);
    await stampLocks(env, AT);
    const r = await removeForecast(api(`/api/forecasts/${id}`, { method: "DELETE", headers: { cookie: u.cookie } }), env, id);
    expect(r.status).toBe(204);
  });
});
