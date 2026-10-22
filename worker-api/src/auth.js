// OAuth start/callback, the pending identity, and sessions.
//
// No account row exists until the reader has consented (POST /api/consent).
// Between the provider's callback and the consent screen the identity lives in
// a short-lived signed, HttpOnly cookie ("pending"), so a person who signs in
// and walks away leaves nothing in the database.
//
// Accounts are not merged across providers: merging on an email address is an
// account-takeover route. A reader who signs in two ways has two accounts.

import { generateCodeVerifier, generateState } from "arctic";
import { PROVIDERS } from "./providers.js";
import { HttpError, readCookies, cookieName, setCookie, clearCookie, clientIp, intVar, readForm } from "./http.js";
import { signToken, verifyToken, safeEqual, sha256Hex, randomId, b64url } from "./crypto.js";

const OAUTH_TTL = 10 * 60;      // seconds the provider round trip may take
const PENDING_TTL = 30 * 60;    // seconds to answer the consent screen

// Only same-site relative paths are honoured as a return address.
export function safeReturn(r) {
  return typeof r === "string" && /^\/(?!\/)[\w\-./?=&%#]*$/.test(r) && !r.includes("\\") ? r : "/";
}

function provider(name) {
  const p = Object.prototype.hasOwnProperty.call(PROVIDERS, name) ? PROVIDERS[name] : null;
  if (!p) throw new HttpError(404, "unknown sign-in provider");
  return p;
}

export async function startAuth(request, env, name) {
  const p = provider(name);
  if (env.RL_AUTH) {
    const { success } = await env.RL_AUTH.limit({ key: `auth:${clientIp(request)}` });
    if (!success) throw new HttpError(429, "too many sign-in attempts; wait a minute");
  }
  const state = generateState();
  const verifier = generateCodeVerifier();
  const nonce = b64url(crypto.getRandomValues(new Uint8Array(16)));
  const ret = safeReturn(new URL(request.url).searchParams.get("return"));
  const url = p.authorizationURL(env, { state, verifier, nonce });
  const cookie = await signToken(env.SESSION_SIGNING_KEY, "oauth",
    { p: name, s: state, v: p.pkce ? verifier : null, n: nonce, r: ret }, OAUTH_TTL);
  return new Response(null, {
    status: 302,
    headers: { location: url.toString(), "set-cookie": setCookie(env, "oauth", cookie, { maxAge: OAUTH_TTL, sameSite: p.sameSite }), "cache-control": "no-store" },
  });
}

export async function callbackAuth(request, env, name) {
  const p = provider(name);
  if (request.method !== p.callbackMethod) throw new HttpError(405, "wrong method for this callback");
  let params;
  if (request.method === "POST") {
    params = await readForm(request);
  } else {
    params = new URL(request.url).searchParams;
  }
  const clear = clearCookie(env, "oauth", p.sameSite);
  if (params.get("error")) {
    return redirect(`/make?signin=cancelled`, [clear]);
  }
  const st = await verifyToken(env.SESSION_SIGNING_KEY, "oauth", readCookies(request)[cookieName(env, "oauth")]);
  if (!st || st.p !== name || !(await safeEqual(st.s, params.get("state") || "")))
    throw new HttpError(400, "sign-in expired or was not started here; try again");
  const code = params.get("code");
  if (!code) throw new HttpError(400, "no authorisation code");

  const id = await p.identity(env, { code, verifier: st.v, nonce: st.n });

  const user = await env.DB.prepare("SELECT id FROM users WHERE provider = ? AND provider_sub = ?")
    .bind(name, id.sub).first();
  if (user) {
    const cookies = [clear, await createSession(env, user.id)];
    if (id.handle) cookies.push(await handleCookie(env, user.id, id.handle));
    return redirect(st.r, cookies);
  }
  const pending = await signToken(env.SESSION_SIGNING_KEY, "pending",
    { provider: name, sub: id.sub, ck: id.contact_kind, c: id.contact, cv: id.contact_verified, h: id.handle || null, r: st.r }, PENDING_TTL);
  return redirect(`/make?consent=1&return=${encodeURIComponent(st.r)}`,
    [clear, setCookie(env, "pending", pending, { maxAge: PENDING_TTL })]);
}

function redirect(location, cookies) {
  const h = new Headers({ location, "cache-control": "no-store" });
  for (const c of cookies) h.append("set-cookie", c);
  return new Response(null, { status: 302, headers: h });
}

export async function readPending(request, env) {
  return verifyToken(env.SESSION_SIGNING_KEY, "pending", readCookies(request)[cookieName(env, "pending")]);
}

// A session is a random value in an HttpOnly cookie; the database holds only
// its hash, so a leaked table cannot be replayed. Revocable by deleting the row.
export async function createSession(env, userId, now = Date.now()) {
  const days = intVar(env, "SESSION_DAYS");
  const raw = randomId(32);
  await env.DB.prepare("INSERT INTO sessions (id_hash, user_id, expires_at) VALUES (?, ?, ?)")
    .bind(await sha256Hex(raw), userId, new Date(now + days * 86400e3).toISOString()).run();
  return setCookie(env, "session", raw, { maxAge: days * 86400 });
}

export async function sessionUser(request, env, now = Date.now()) {
  const raw = readCookies(request)[cookieName(env, "session")];
  if (!raw || raw.length > 64) return null;
  const row = await env.DB.prepare(
    "SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id WHERE s.id_hash = ? AND s.expires_at > ?")
    .bind(await sha256Hex(raw), new Date(now).toISOString()).first();
  return row || null;
}

export async function requireUser(request, env) {
  const u = await sessionUser(request, env);
  if (!u) throw new HttpError(401, "sign in to do this");
  return u;
}

export async function logout(request, env) {
  const raw = readCookies(request)[cookieName(env, "session")];
  if (raw) await env.DB.prepare("DELETE FROM sessions WHERE id_hash = ?").bind(await sha256Hex(raw)).run();
  const h = new Headers();
  h.append("set-cookie", clearCookie(env, "session"));
  h.append("set-cookie", clearCookie(env, "handle"));
  return new Response(null, { status: 204, headers: h });
}

// The X username, offered as the default label, is NOT stored in D1 (owner,
// 2026-09-29: store it only if the reader keeps it as a label). It lives in a
// signed HttpOnly cookie bound to the account, for as long as the session.
export async function handleCookie(env, userId, handle, now = Date.now()) {
  const days = intVar(env, "SESSION_DAYS");
  const t = await signToken(env.SESSION_SIGNING_KEY, "handle", { u: userId, h: handle }, days * 86400, now);
  return setCookie(env, "handle", t, { maxAge: days * 86400 });
}

export async function readHandle(request, env, userId) {
  const p = await verifyToken(env.SESSION_SIGNING_KEY, "handle", readCookies(request)[cookieName(env, "handle")]);
  return p && p.u === userId && typeof p.h === "string" ? p.h : null;
}
