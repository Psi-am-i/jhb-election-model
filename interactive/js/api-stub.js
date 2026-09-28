// ⛔ STUB BACKEND. No network calls, no OAuth provider, no client IDs, no
// secrets. It imitates the Worker API in BACKEND.md so the pages can be built
// against the real contract; "saved" forecasts live in this browser's
// localStorage and nowhere else.
//
// The real endpoints (BACKEND.md §3):
//   GET  /auth/:provider/start          -> 302 to the provider
//   GET  /auth/:provider/callback       -> session cookie, 302 to /consent
//   POST /auth/email/start {email}      -> sends a magic link
//   GET  /api/me                        -> session + consent state
//   POST /api/consent                   -> records the consent row
//   POST /api/forecasts                 -> {id, url}
//   GET  /api/forecasts/:id             -> the public forecast JSON
//   DELETE /api/forecasts/:id           -> 204, and /f/:id answers 410
//   DELETE /api/me                      -> erase account, forecasts, contact

import { loadJSON, cleanName } from "./common.js";

const SESSION = "jhb-stub-session";
const STORE = "jhb-stub-forecasts";
const read = k => { try { return JSON.parse(localStorage.getItem(k) || "null"); } catch (e) { return null; } };
const write = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} };

// Unguessable ids in production come from crypto.getRandomValues on the
// server (BACKEND.md §3); the same here.
function newId(n = 10) {
  const a = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
  const b = crypto.getRandomValues(new Uint8Array(n));
  return Array.from(b, x => a[x % 62]).join("");
}

export function session() { return read(SESSION); }

// What a provider would hand back, minimised to what we keep: a display name,
// an email, and the provider's stable account id. Nothing else is requested
// (scopes: openid email profile, or the provider's equivalent).
export async function signIn(provider, email = null) {
  const fake = {
    google: ["Reader Example", "reader@example.com"],
    apple: ["", "x7k2@privaterelay.appleid.com"],   // Apple: name only on first sign-in; relay email
    facebook: ["Reader Example", "reader@example.com"],
    x: ["Reader Example", null],                    // X may return no email; we then ask for one
    email: ["", email],
  }[provider];
  const s = { provider, provider_sub: "stub-" + newId(8), name: fake[0], email: fake[1],
    consent: null, stub: true };
  write(SESSION, s);
  return s;
}

export function recordConsent(c) {
  const s = session(); if (!s) throw new Error("not signed in");
  s.consent = { ...c, version: "draft-2026-09-28", at: new Date().toISOString() };
  s.display_name = cleanName(c.display_name);
  if (c.email) s.email = c.email;
  write(SESSION, s);
  return s;
}

export function signOut() { try { localStorage.removeItem(SESSION); } catch (e) {} }

export async function saveForecast(f) {
  const s = session();
  if (!s?.consent?.store) throw new Error("consent required");
  const all = read(STORE) || {};
  const id = f.id && all[f.id] ? f.id : newId();
  all[id] = { ...f, id, created_at: all[id]?.created_at || new Date().toISOString(),
    updated_at: new Date().toISOString(),
    display_name: s.consent.show_name ? s.display_name : "" };
  write(STORE, all);
  return { id, path: "f/?id=" + id };
}

export async function getForecast(id) {
  if (id === "demo7Qx2Lp") return loadJSON("demo-forecast.json");
  const all = read(STORE) || {};
  if (id in all) return all[id];
  const gone = read(STORE + "-deleted") || [];
  if (gone.includes(id)) return { gone: true };
  return null;
}

export async function deleteForecast(id) {
  const all = read(STORE) || {};
  delete all[id];
  write(STORE, all);
  write(STORE + "-deleted", [...(read(STORE + "-deleted") || []), id]);
}
