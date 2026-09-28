// ⛔ STUB BACKEND. No network calls, no OAuth provider, no client IDs, no
// secrets. It imitates the Worker API (worker-api/src/index.js lists the real
// endpoints) so the pages can be built against the real contract; "saved"
// forecasts live in this browser's localStorage and nowhere else.
//
// The contract it imitates, and must not drift from:
//   GET  /auth/:provider/start          -> 302 to the provider (google, apple,
//                                          microsoft, facebook, x; nothing else)
//   GET  /api/me                        -> session, deletion date, wording version
//   POST /api/consent                   -> exactly the keys of
//                                          consent-terms.js CONSENT_KEYS
//   POST /api/forecasts                 -> {id, url, label}
//   GET  /api/forecasts/:id             -> the public forecast JSON
//   DELETE /api/forecasts/:id           -> 204, and /f/:id answers 410
//   DELETE /api/me                      -> erase account, forecasts, contact

import { loadJSON } from "./common.js";
import { CONSENT_KEYS, SCREEN_PURPOSES } from "./consent-terms.js";
import { randomLabel } from "./labels.js";

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

// What a provider hands back, minimised to what the server keeps: an account
// id, and an email only when the provider verified it. No name is read from
// any provider. Only X has a public handle (the default label).
export async function signIn(provider) {
  const fake = {
    google: { contact_confirmed: true },
    apple: { contact_confirmed: true },                  // may be a private-relay address
    microsoft: { contact_confirmed: false, unconfirmed_contact: "reader@example.com" },
    facebook: { contact_confirmed: false, unconfirmed_contact: "reader@example.com" },
    x: { contact_confirmed: false, handle: "reader_example" },
  }[provider];
  if (!fake) throw new Error("unknown provider");
  const s = { provider, provider_sub: "stub-" + newId(8), handle: null, unconfirmed_contact: null,
    ...fake, deletion_date: null, consent: null, stub: true };
  write(SESSION, s);
  return s;
}

// Refuses what the server refuses: an unknown key, a missing purpose.
export async function recordConsent(body) {
  const s = session(); if (!s) throw new Error("not signed in");
  for (const k of Object.keys(body)) if (!CONSENT_KEYS.includes(k)) throw new Error(`not accepted: ${k}`);
  for (const p of SCREEN_PURPOSES) if (typeof body[p] !== "boolean") throw new Error(`must be true or false: ${p}`);
  if (!body.wording_version) throw new Error("wording_version required");
  s.consent = { store: body.store, age18: body.age18, contact_if_win: body.contact_if_win,
    updates: body.updates, version: body.wording_version, at: new Date().toISOString() };
  // A typed address is NOT kept: the server sends one confirmation link.
  s.confirmation = body.contact ? "sent (stub: nothing was sent)" : null;
  write(SESSION, s);
  return s;
}

export function signOut() { try { localStorage.removeItem(SESSION); } catch (e) {} }

// The label rule the server applies: the forecast's own display_name if the
// reader set one, else a random default assigned once at creation.
export async function saveForecast(f) {
  const s = session();
  if (!s?.consent?.store) throw new Error("consent required");
  const all = read(STORE) || {};
  const id = f.id && all[f.id] ? f.id : newId();
  const default_label = all[id]?.default_label || randomLabel();
  all[id] = { ...f, id, default_label, created_at: all[id]?.created_at || new Date().toISOString(),
    updated_at: new Date().toISOString() };
  write(STORE, all);
  return { id, path: "f/?id=" + id, label: f.display_name ?? default_label };
}

export async function getForecast(id) {
  if (id === "demo7Qx2Lp") return loadJSON("demo-forecast.json");
  const all = read(STORE) || {};
  if (id in all) return { ...all[id], display_name: all[id].display_name ?? all[id].default_label };
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
