// The account lifecycle after sign-up: the election-day lock, the one
// post-election message, the reply to it, the deletion run, and deletion
// requests that arrive from a provider (Facebook) rather than from the reader.
//
// Owner, DESIGN-decided §9: after the election every account gets ONE message
// asking "delete my data" or "tell me about the next election"; no reply means
// deletion at a date the owner sets. Both dates are config values
// (POST_ELECTION_MESSAGE_AT, DELETION_AT) and are EMPTY until the owner sets
// them; while either is empty the scheduled run does nothing and says why.
//
// Safety order: the deletion run refuses to act until the message run has
// recorded that every message was sent. Deleting people who were never asked
// is not "no reply". While src/mail.js is a stub, no message is sent, so the
// deletion run will not act; that is logged every hour after DELETION_AT.

import { instantVar, isLocked, HttpError, json, readForm } from "./http.js";
import { signToken, verifyToken, randomId, b64urlDecode } from "./crypto.js";
import { deleteUser, deleteForecastsOf } from "./deletion.js";
import { consentRows } from "./consent.js";
import { sendMail, postElectionMessage, POST_ELECTION_WORDING_VERSION } from "./mail.js";
import { esc } from "../../interactive/js/common.js";

const log = (o) => console.log(JSON.stringify({ at: "scheduled", ...o }));

async function jobDone(env, name) {
  return Boolean(await env.DB.prepare("SELECT 1 AS x FROM jobs WHERE name = ?").bind(name).first());
}
async function markDone(env, name, detail, now) {
  await env.DB.prepare("INSERT INTO jobs (name, done_at, detail) VALUES (?, ?, ?)")
    .bind(name, new Date(now).toISOString(), JSON.stringify(detail)).run();
}

export async function stampLocks(env, now) {
  if (!isLocked(env, now)) return 0;
  const r = await env.DB.prepare("UPDATE forecasts SET locked_at = ? WHERE locked_at IS NULL")
    .bind(new Date(now).toISOString()).run();
  return r.meta.changes;
}

export async function runScheduled(env, now = Date.now()) {
  const out = { locked: await stampLocks(env, now) };
  const msgAt = instantVar(env, "POST_ELECTION_MESSAGE_AT");
  const delAt = instantVar(env, "DELETION_AT");
  if (msgAt === null || delAt === null) {
    log({ skip: "POST_ELECTION_MESSAGE_AT or DELETION_AT not set by the owner" });
    return { ...out, skipped: "dates not set" };
  }
  if (delAt <= msgAt) {
    log({ skip: "DELETION_AT must be after POST_ELECTION_MESSAGE_AT" });
    return { ...out, skipped: "dates out of order" };
  }
  if (now >= msgAt && !(await jobDone(env, "post_election_message")))
    out.message = await sendPostElection(env, now, delAt);
  if (now >= delAt && !(await jobDone(env, "deletion_run"))) {
    if (!(await jobDone(env, "post_election_message"))) {
      log({ refuse: "deletion run: the post-election message has not been sent to everyone; nothing deleted" });
      out.deletion = "refused: message not sent";
    } else {
      out.deletion = await deletionRun(env, now);
    }
  }
  return out;
}

async function sendPostElection(env, now, delAt) {
  const { results } = await env.DB.prepare(
    "SELECT id, contact FROM users WHERE contact IS NOT NULL AND contact_verified = 1").all();
  const ttl = Math.ceil((delAt - now) / 1000);
  const deletionDate = new Date(delAt).toISOString().slice(0, 10);
  let sent = 0, failed = 0;
  for (const u of results) {
    const mk = async c => `${env.SITE_ORIGIN}/api/reply?t=${await signToken(env.SESSION_SIGNING_KEY, "reply", { u: u.id, c }, ttl, now)}`;
    const msg = postElectionMessage({ deleteUrl: await mk("delete"), notifyUrl: await mk("notify"), deletionDate });
    const r = await sendMail(env, { to: u.contact, ...msg });
    if (r.sent) sent++; else failed++;
  }
  log({ post_election_message: { sent, failed, wording: POST_ELECTION_WORDING_VERSION } });
  // Recorded as done only when every message went out; otherwise the next
  // hourly run tries again (a reader may then get it twice: preferable to never).
  if (failed === 0) await markDone(env, "post_election_message", { sent, wording: POST_ELECTION_WORDING_VERSION }, now);
  return { sent, failed };
}

// Accounts whose latest next_election consent is granted keep only the sign-in
// id and the contact; their forecasts go. Every other account is deleted.
export async function deletionRun(env, now) {
  const { results } = await env.DB.prepare(
    `SELECT u.id, (SELECT granted FROM consents c WHERE c.user_id = u.id AND c.purpose = 'next_election'
                   ORDER BY c.id DESC LIMIT 1) AS keep FROM users u`).all();
  let deleted = 0, kept = 0;
  for (const u of results) {
    if (u.keep === 1) { await deleteForecastsOf(env, u.id, new Date(now)); kept++; }
    else { await deleteUser(env, u.id, new Date(now)); deleted++; }
  }
  await markDone(env, "deletion_run", { deleted, kept }, now);
  log({ deletion_run: { deleted, kept } });
  return { deleted, kept };
}

// ---- the reply to the post-election message --------------------------------
// GET shows a confirmation page with a button; only the POST acts. Mail
// scanners follow GET links, and must not be able to delete an account.

const page = (title, body) => new Response(`<!doctype html><html lang="en-ZA"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex"><title>${title}</title></head>
<body style="font:16px/1.5 system-ui,sans-serif;max-width:40em;margin:2em auto;padding:0 16px"><h1>${title}</h1>${body}</body></html>`,
  { headers: { "content-type": "text/html; charset=utf-8", "cache-control": "no-store" } });

export async function replyGet(request, env) {
  const t = new URL(request.url).searchParams.get("t") || "";
  const p = await verifyToken(env.SESSION_SIGNING_KEY, "reply", t);
  if (!p) return page("This link has expired", "<p>Sign in and use “Delete my account” instead.</p>");
  const what = p.c === "delete" ? "Delete my account, my forecasts and my contact details" : "Tell me about the next election";
  return page("Confirm your choice", `<form method="post" action="/api/reply"><input type="hidden" name="t" value="${esc(t)}">
<button type="submit">${esc(what)}</button></form>`);
}

export async function replyPost(request, env, now = Date.now()) {
  const form = await readForm(request);
  const p = await verifyToken(env.SESSION_SIGNING_KEY, "reply", form.get("t") || "", now);
  if (!p) return page("This link has expired", "<p>Sign in and use “Delete my account” instead.</p>");
  const exists = await env.DB.prepare("SELECT 1 AS x FROM users WHERE id = ?").bind(p.u).first();
  if (!exists) return page("Nothing to do", "<p>This account no longer exists.</p>");
  if (p.c === "delete") {
    await deleteUser(env, p.u, new Date(now));
    return page("Deleted", "<p>Your account, forecasts and contact details are deleted.</p>");
  }
  await env.DB.batch(consentRows({ ...env, CONSENT_WORDING_VERSION: POST_ELECTION_WORDING_VERSION },
    p.u, { next_election: true }, new Date(now).toISOString()));
  return page("Thank you", "<p>We will tell you about the next election. Your forecasts will be deleted; we keep only your sign-in id and this address.</p>");
}

// ---- provider-initiated deletion -------------------------------------------

// Facebook's Data Deletion Request Callback: a POST with `signed_request`
// (base64url(signature) "." base64url(JSON payload)), HMAC-SHA256 with the app
// secret. The account is deleted at once; Facebook shows the reader the
// returned URL and confirmation code.
export async function facebookDataDeletion(request, env) {
  if (!env.FACEBOOK_APP_SECRET) throw new HttpError(503, "not configured");
  const sr = (await readForm(request)).get("signed_request") || "";
  const payload = await parseSignedRequest(sr, env.FACEBOOK_APP_SECRET);
  if (!payload) throw new HttpError(400, "bad signed_request");
  const u = await env.DB.prepare("SELECT id FROM users WHERE provider = 'facebook' AND provider_sub = ?")
    .bind(String(payload.user_id)).first();
  if (u) await deleteUser(env, u.id);
  const code = randomId(12);
  return json({ url: `${env.SITE_ORIGIN}/api/deletion-status?code=${code}`, confirmation_code: code });
}

export async function parseSignedRequest(sr, secret) {
  const [sig, body, extra] = sr.split(".");
  if (!sig || !body || extra !== undefined) return null;
  const enc = new TextEncoder();
  const key = await crypto.subtle.importKey("raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["verify"]);
  let ok = false;
  try { ok = await crypto.subtle.verify("HMAC", key, b64urlDecode(sig), enc.encode(body)); } catch { return null; }
  if (!ok) return null;
  let p;
  try { p = JSON.parse(new TextDecoder().decode(b64urlDecode(body))); } catch { return null; }
  if (p.algorithm !== "HMAC-SHA256" || !p.user_id) return null;
  return p;
}

// Deletion is immediate, so every confirmation code describes a completed deletion.
export function deletionStatus() {
  return page("Deletion complete", "<p>If an account was linked to that Facebook login, it has been deleted, with its forecasts and contact details.</p>");
}

// ⛔ STUB. Sign in with Apple server-to-server notifications (email-disabled,
// consent-revoked, account-delete) arrive as a JWT signed by Apple. Acting on
// one needs signature verification against Apple's JWKS, which is not built.
// Until it is, answer 501 so nothing is deleted on an unverified message.
export function appleNotifications() {
  return json({ error: "not implemented" }, 501);
}
