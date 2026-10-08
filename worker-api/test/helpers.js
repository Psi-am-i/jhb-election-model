// Test fixtures. Every entry here is built from the one entry schema (the one
// src/build_make.py writes into site/your-forecast/forecast.json), so a change
// of roster or ward list moves the fixture with it.
import { env } from "cloudflare:test";
import page from "../../site/your-forecast/forecast.json";
import { randomId, sha256Hex, signToken } from "../src/crypto.js";

const schema = page.schema;
export { schema };
export const roster = schema.properties.ward_calls.items.enum;
export const nWards = schema.properties.ward_calls.minItems;

// A valid entry (version 2): wards called round-robin over the roster, so every
// party wins a ward and holds a vote on both ballots (R1, R2); the ballots
// differ, so a test that confused them would see it.
export function validForecast() {
  return {
    v: schema.properties.v.const,
    model_ref: schema.properties.model_ref.enum[0],
    ward_calls: Array.from({ length: nWards }, (_, i) => roster[i % roster.length]),
    ward_votes: Object.fromEntries(roster.map((c, i) => [c, 1000 + i])),
    list_votes: Object.fromEntries(roster.map((c, i) => [c, 2000 - i])),
    coalition: [roster[0], roster[1]],
    mayor: roster[0],
    display_name: "Thandi M.",
  };
}

export const clone = o => JSON.parse(JSON.stringify(o));
export const ORIGIN = () => env.SITE_ORIGIN;
export const cookie = (name, v) => `${env.COOKIE_SECURE === "false" ? "dev-" : "__Host-"}${name}=${v}`;

// A consented account with a live session; returns { id, cookie }.
export async function makeUser({ provider = "google", sub = randomId(12), contact = "reader@example.com", verified = 1 } = {}) {
  const id = randomId(16), at = new Date().toISOString();
  const raw = randomId(32);
  await env.DB.batch([
    env.DB.prepare("INSERT INTO users (id, provider, provider_sub, contact_kind, contact, contact_verified, created_at) VALUES (?,?,?,?,?,?,?)")
      .bind(id, provider, sub, contact ? "email" : null, contact, verified, at),
    ...["store", "age18"].map(p => env.DB.prepare(
      "INSERT INTO consents (user_id, purpose, granted, wording_version, at) VALUES (?,?,1,?,?)").bind(id, p, "test", at)),
    env.DB.prepare("INSERT INTO sessions (id_hash, user_id, expires_at) VALUES (?,?,?)")
      .bind(await sha256Hex(raw), id, new Date(Date.now() + 86400e3).toISOString()),
  ]);
  return { id, sub, cookie: cookie("session", raw) };
}

export async function pendingCookie(payload) {
  return cookie("pending", await signToken(env.SESSION_SIGNING_KEY, "pending", payload, 600));
}

export function api(path, { method = "GET", body, headers = {}, origin = true } = {}) {
  const h = new Headers(headers);
  if (origin) h.set("origin", env.SITE_ORIGIN);
  if (body !== undefined) h.set("content-type", "application/json");
  return new Request(env.SITE_ORIGIN + path, { method, headers: h, body: body === undefined ? undefined : JSON.stringify(body) });
}
