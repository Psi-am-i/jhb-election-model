// The pages' one door to the backend: the stub (js/api-stub.js, localStorage,
// no network) for local preview, or the Worker API (worker-api/src/index.js)
// in production. Every page imports this, never the stub directly.
//
// MODE: loopback hosts and file: use the stub; anything else is production.
// `?api=stub` or `?api=live` overrides, for checking one against the other.
//
// A session, as the pages read it (from the stub, or mapped from GET /api/me):
//   { provider, handle, contact_confirmed, unconfirmed_contact,
//     deletion_date, wording_version, pending, consent: { store } | null }

import * as stub from "./api-stub.js";
import { validateForecast } from "../../worker-api/src/validate.js";
import { loadSchema } from "./common.js";

export function modeFor(loc) {
  if (!loc) return "stub";
  const q = new URLSearchParams(loc.search || "").get("api");
  if (q === "stub") return "stub";
  if (q === "live") return "production";
  if (loc.protocol === "file:") return "stub";
  return /^(127\.0\.0\.1|localhost|\[::1\])$/.test(loc.hostname) ? "stub" : "production";
}
export const mode = () => modeFor(typeof location === "undefined" ? null : location);

async function call(method, path, body) {
  const r = await fetch(path, {
    method, credentials: "same-origin",
    headers: body ? { "content-type": "application/json" } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  let data = null;
  try { data = r.status === 204 ? null : await r.json(); } catch (e) {}
  if (!r.ok) {
    const err = new Error(data?.error || `the server answered ${r.status}`);
    err.status = r.status; err.field = data?.field;
    throw err;
  }
  return data;
}

// GET /api/me, as a session. Pure, so a test can hold it to the Worker's shape.
export function sessionFromMe(me) {
  if (!me) return null;
  const base = { deletion_date: me.deletion_date ?? null, wording_version: me.wording_version ?? null,
    handle: me.handle ?? null, provider: me.provider ?? null };
  if (me.signed_in) {
    const c = me.consents || {};
    return { ...base, pending: false, contact_confirmed: Boolean(me.has_contact), unconfirmed_contact: null,
      consent: c.store?.granted && c.age18?.granted ? { store: true } : null };
  }
  if (me.pending) {
    return { ...base, pending: true, contact_confirmed: Boolean(me.contact_confirmed),
      unconfirmed_contact: me.unconfirmed_contact ?? null, consent: null };
  }
  return null;
}

export async function currentSession() {
  if (mode() === "stub") return stub.session();
  return sessionFromMe(await call("GET", "/api/me"));
}

// Production: the Worker's /auth/<provider>/start redirects to the provider,
// and its callback brings the reader back to /make?consent=1 (the draft
// survives in localStorage). The promise never resolves: the page is leaving.
export async function signIn(provider) {
  if (mode() === "stub") return stub.signIn(provider);
  const back = location.pathname;
  location.assign(`/auth/${encodeURIComponent(provider)}/start?return=${encodeURIComponent(back)}`);
  return new Promise(() => {});
}

export async function recordConsent(body) {
  if (mode() === "stub") return stub.recordConsent(body);
  await call("POST", "/api/consent", body);
  return currentSession();
}

// Save a validated forecast body. `seats` is the answer the page's seat engine
// gave for it; the stub keeps it as the server keeps its own recomputation.
// Returns { id, path, label }.
export async function saveForecast(body, { id = null, seats = null } = {}) {
  const v = validateForecast(body, await loadSchema());
  if (!v.ok) throw Object.assign(new Error(`${v.field}: ${v.reason}`), { field: v.field });
  if (mode() === "stub") return stub.saveForecast({ ...v.value, id, seats });
  const r = id ? await call("PUT", `/api/forecasts/${encodeURIComponent(id)}`, v.value)
    : await call("POST", "/api/forecasts", v.value);
  const newId = r.id || id;
  return { id: newId, path: `/f/${newId}`, label: r.label ?? v.value.display_name };
}

export async function deleteForecast(id) {
  if (mode() === "stub") return stub.deleteForecast(id);
  await call("DELETE", `/api/forecasts/${encodeURIComponent(id)}`);
}

export async function getForecast(id) {
  if (mode() === "stub") return stub.getForecast(id);
  try { return await call("GET", `/api/forecasts/${encodeURIComponent(id)}`); }
  catch (e) { if (e.status === 410) return { gone: true }; if (e.status === 404) return null; throw e; }
}
