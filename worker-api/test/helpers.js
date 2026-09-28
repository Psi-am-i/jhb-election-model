// Test fixtures. Every forecast here is built from the generated schema, so a
// change of roster or ward list moves the fixture with it.
import { env } from "cloudflare:test";
import schema from "../generated/forecast.schema.json";
import { randomId, sha256Hex, signToken } from "../src/crypto.js";

export { schema };
export const roster = schema.properties.ward_calls.items.enum;
export const nWards = schema.properties.ward_calls.minItems;

// A valid forecast: wards called round-robin over the roster, combined shares equal
// and nudged so they sum to exactly 100.
export function validForecast() {
  const share = Math.floor(10000 / roster.length) / 100;
  const pr = Object.fromEntries(roster.map(c => [c, share]));
  pr[roster[0]] = Math.round((100 - share * (roster.length - 1)) * 100) / 100;
  return {
    model_ref: schema.properties.model_ref.enum[0],
    ward_calls: Array.from({ length: nWards }, (_, i) => roster[i % roster.length]),
    combined_share: pr,
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
