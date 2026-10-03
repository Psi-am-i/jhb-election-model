// Request/response helpers and configuration readers.

export class HttpError extends Error {
  constructor(status, error, field) { super(error); this.status = status; this.field = field; }
}

export function json(data, status = 200, headers = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store", ...headers },
  });
}

export function errorResponse(e) {
  if (e instanceof HttpError) return json({ error: e.message, ...(e.field ? { field: e.field } : {}) }, e.status);
  console.error(JSON.stringify({ msg: "unhandled", error: String(e?.stack || e) }));
  return json({ error: "internal error" }, 500);
}

// ---- configuration -------------------------------------------------------

export function intVar(env, name) {
  const v = Number.parseInt(env[name], 10);
  if (!Number.isFinite(v)) throw new Error(`config ${name} is not an integer`);
  return v;
}

// A configured instant, or null when the owner has not set it. An unparseable
// value throws: a typo must not read as "not yet".
export function instantVar(env, name) {
  const s = (env[name] || "").trim();
  if (!s) return null;
  if (!/(Z|[+-]\d\d:\d\d)$/.test(s)) throw new Error(`config ${name} must carry an explicit UTC offset`);
  const t = Date.parse(s);
  if (!Number.isFinite(t)) throw new Error(`config ${name} is not a date: ${s}`);
  return t;
}

// Owner, 2026-09-28: no new or edited forecasts at or after LOCK_AT.
export function isLocked(env, now = Date.now()) {
  const t = instantVar(env, "LOCK_AT");
  if (t === null) throw new Error("LOCK_AT must be set");
  return now >= t;
}

// ---- cookies --------------------------------------------------------------

export function readCookies(request) {
  const out = {};
  for (const part of (request.headers.get("cookie") || "").split(";")) {
    const i = part.indexOf("=");
    if (i > 0) out[part.slice(0, i).trim()] = part.slice(i + 1).trim();
  }
  return out;
}

// Production names use the __Host- prefix (Secure, Path=/, no Domain), which a
// browser refuses over plain http, so `wrangler dev` uses plain names.
export function cookieName(env, base) {
  return env.COOKIE_SECURE === "false" ? `dev-${base}` : `__Host-${base}`;
}

export function setCookie(env, base, value, { maxAge, sameSite = "Lax" } = {}) {
  const secure = env.COOKIE_SECURE !== "false";
  const parts = [`${cookieName(env, base)}=${value}`, "Path=/", "HttpOnly", `SameSite=${sameSite}`];
  if (secure || sameSite === "None") parts.push("Secure");
  if (maxAge !== undefined) parts.push(`Max-Age=${maxAge}`);
  return parts.join("; ");
}

export const clearCookie = (env, base, sameSite = "Lax") => setCookie(env, base, "", { maxAge: 0, sameSite });

// ---- request guards -------------------------------------------------------

// CSRF: every state-changing API call must come from the site's own origin.
// (The OAuth callbacks are exempt; they are bound by `state` instead.)
export function requireSameOrigin(request, env) {
  if (request.headers.get("origin") !== env.SITE_ORIGIN)
    throw new HttpError(403, "cross-origin request refused");
}

export async function readJsonBody(request, env) {
  const max = intVar(env, "MAX_BODY_BYTES");
  const ct = (request.headers.get("content-type") || "").split(";")[0].trim().toLowerCase();
  if (ct !== "application/json") throw new HttpError(415, "Content-Type must be application/json");
  const declared = Number(request.headers.get("content-length"));
  if (Number.isFinite(declared) && declared > max) throw new HttpError(413, `body larger than ${max} bytes`);
  if (!request.body) throw new HttpError(400, "empty body");
  // Count bytes as they arrive; never buffer an unbounded body.
  const reader = request.body.getReader();
  const chunks = [];
  let n = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    n += value.byteLength;
    if (n > max) { await reader.cancel(); throw new HttpError(413, `body larger than ${max} bytes`); }
    chunks.push(value);
  }
  const buf = new Uint8Array(n);
  let o = 0;
  for (const c of chunks) { buf.set(c, o); o += c.byteLength; }
  try { return JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(buf)); }
  catch { throw new HttpError(400, "body is not valid JSON"); }
}

export const clientIp = request => request.headers.get("cf-connecting-ip") || "unknown";


// A small url-encoded form (OAuth form_post callbacks, the reply page, provider
// callbacks). Read as bytes, bounded, then parsed.
export async function readForm(request, max = 8192) {
  const ct = (request.headers.get("content-type") || "").split(";")[0].trim().toLowerCase();
  if (ct !== "application/x-www-form-urlencoded") throw new HttpError(415, "expected a form post");
  const declared = Number(request.headers.get("content-length"));
  if (Number.isFinite(declared) && declared > max) throw new HttpError(413, "form too large");
  const buf = await request.arrayBuffer();
  if (buf.byteLength > max) throw new HttpError(413, "form too large");
  return new URLSearchParams(new TextDecoder().decode(buf));
}
