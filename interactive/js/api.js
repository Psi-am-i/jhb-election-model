// The pages' one door to the backend: the Worker API (worker-api/src/index.js)
// in production. Every page imports this.
//
// MODE: loopback hosts and file: are a local preview, which has no backend
// (the prototype's localStorage stub, js/api-stub.js, was retired on
// 2026-10-08 with the save path it served: a stored entry is now the site
// Worker's sealed prediction, src/share-edge.js). `?api=stub` or `?api=live`
// overrides.
//
// A session, as the pages read it (mapped from GET /api/me):
//   { provider, handle, contact_confirmed, unconfirmed_contact,
//     deletion_date, wording_version, pending, consent: { store } | null }

const NO_BACKEND = "a local preview has no sign-in backend";

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
  if (mode() === "stub") return null;
  return sessionFromMe(await call("GET", "/api/me"));
}

// Production: the Worker's /auth/<provider>/start redirects to the provider,
// and its callback brings the reader back to /make?consent=1 (the draft
// survives in localStorage). The promise never resolves: the page is leaving.
export async function signIn(provider) {
  if (mode() === "stub") throw new Error(NO_BACKEND);
  const back = location.pathname;
  location.assign(`/auth/${encodeURIComponent(provider)}/start?return=${encodeURIComponent(back)}`);
  return new Promise(() => {});
}

export async function recordConsent(body) {
  if (mode() === "stub") throw new Error(NO_BACKEND);
  await call("POST", "/api/consent", body);
  return currentSession();
}
