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
// Safety order (R5 finding 1): the message is recorded PER ACCOUNT
// (users.message_sent_at, message_status). Each hourly run sends to at most
// MESSAGE_BATCH_SIZE accounts not yet stamped, MAIL_CONCURRENCY at a time, so
// a large list is worked through over several runs and an account already
// stamped is never mailed again. A permanent per-recipient failure (a
// suppressed recipient now, or a hard bounce reported later) is stamped
// 'undeliverable': the message went out and cannot arrive, which is not a
// reason to keep the account forever. A transient failure stamps nothing and
// is retried next hour; a sender-side fault (no binding, unverified domain)
// is always transient, because it affects everyone.
//
// The deletion run refuses to act while any account holding a confirmed
// contact has not been stamped: deleting people who were never asked is not
// "no reply". Each refusal is logged at error level with `alert` set, every
// hour, so the operator sees a stuck run rather than finding it later.
// Accounts with no confirmed contact were told at consent that they get no
// message and are deleted on DELETION_AT (consent-terms.js, "No confirmed
// email"); they do not hold the run back.

import { instantVar, isLocked, intVar, HttpError, json, readForm } from "./http.js";
import { signToken, verifyToken, randomId, b64urlDecode } from "./crypto.js";
import { deleteUser, deleteForecastsOf } from "./deletion.js";
import { consentRows, FRAGMENT_SCRIPT } from "./consent.js";
import { sendMail, postElectionMessage, POST_ELECTION_WORDING_VERSION } from "./mail.js";
import { esc } from "../../interactive/js/common.js";

const log = (o) => console.log(JSON.stringify({ at: "scheduled", ...o }));

const alert = (o) => console.error(JSON.stringify({ at: "scheduled", level: "alert", ...o }));

async function jobDone(env, name) {
  return Boolean(await env.DB.prepare("SELECT 1 AS x FROM jobs WHERE name = ?").bind(name).first());
}
async function markDone(env, name, detail, now) {
  await env.DB.prepare("INSERT OR IGNORE INTO jobs (name, done_at, detail) VALUES (?, ?, ?)")
    .bind(name, new Date(now).toISOString(), JSON.stringify(detail)).run();
}

export async function stampLocks(env, now) {
  if (!isLocked(env, now)) return 0;
  const r = await env.DB.prepare("UPDATE forecasts SET locked_at = ? WHERE locked_at IS NULL")
    .bind(new Date(now).toISOString()).run();
  return r.meta.changes;
}

// Accounts that hold a confirmed contact and have not been stamped.
const UNSENT = "FROM users WHERE contact IS NOT NULL AND contact_verified = 1 AND message_sent_at IS NULL";
export async function unsentCount(env) {
  return (await env.DB.prepare(`SELECT COUNT(*) AS n ${UNSENT}`).first()).n;
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
  if (now >= msgAt) out.message = await sendPostElection(env, now, delAt);
  if (now >= delAt && !(await jobDone(env, "deletion_run"))) {
    const unsent = await unsentCount(env);
    if (unsent > 0) {
      alert({ alert: "deletion_refused", unsent,
        why: "the post-election message has not gone to every account with a confirmed contact; nothing deleted" });
      out.deletion = { refused: "message not sent to every confirmed contact", unsent };
    } else {
      out.deletion = await deletionRun(env, now);
    }
  }
  return out;
}

// One batch of the post-election message. Returns the counts for this run and
// how many accounts are still waiting.
export async function sendPostElection(env, now, delAt) {
  const batch = intVar(env, "MESSAGE_BATCH_SIZE");
  const conc = intVar(env, "MAIL_CONCURRENCY");
  const { results } = await env.DB.prepare(`SELECT id, contact ${UNSENT} ORDER BY created_at LIMIT ?`).bind(batch).all();
  const ttl = Math.ceil((delAt - now) / 1000);
  const deletionDate = new Date(delAt).toISOString().slice(0, 10);
  const at = new Date(now).toISOString();
  let sent = 0, undeliverable = 0, failed = 0;
  // The reply token travels in the fragment, so it reaches no request log.
  const mk = async (u, c) => `${env.SITE_ORIGIN}/api/reply/${c}#t=${await signToken(env.SESSION_SIGNING_KEY, "reply", { u: u.id, c }, ttl, now)}`;
  for (let i = 0; i < results.length; i += conc) {
    const chunk = results.slice(i, i + conc);
    const outcomes = await Promise.all(chunk.map(async u => {
      const msg = postElectionMessage({ deleteUrl: await mk(u, "delete"), notifyUrl: await mk(u, "notify"), deletionDate });
      return [u, await sendMail(env, { to: u.contact, ...msg })];
    }));
    const stamps = [];
    for (const [u, r] of outcomes) {
      const status = r.sent ? "sent" : r.permanent ? "undeliverable" : null;
      if (status === "sent") sent++; else if (status) undeliverable++; else failed++;
      if (status) stamps.push(env.DB.prepare(
        "UPDATE users SET message_sent_at = ?, message_status = ? WHERE id = ? AND message_sent_at IS NULL").bind(at, status, u.id));
    }
    if (stamps.length) await env.DB.batch(stamps);
  }
  const remaining = await unsentCount(env);
  log({ post_election_message: { sent, undeliverable, failed, remaining, wording: POST_ELECTION_WORDING_VERSION } });
  if (remaining === 0) await markDone(env, "post_election_message", { wording: POST_ELECTION_WORDING_VERSION }, now);
  return { sent, undeliverable, failed, remaining };
}

// A hard bounce reported after the message was accepted. The account is
// stamped undeliverable (whether or not it was stamped 'sent' before).
// Returns the number of accounts matched.
export async function recordHardBounce(env, recipient, now = Date.now()) {
  if (typeof recipient !== "string" || !recipient) return 0;
  const r = await env.DB.prepare(
    `UPDATE users SET message_status = 'undeliverable', message_sent_at = COALESCE(message_sent_at, ?)
     WHERE contact = ? AND message_sent_at IS NOT NULL`).bind(new Date(now).toISOString(), recipient.toLowerCase()).run();
  return r.meta.changes;
}

// Email Service event-subscription bodies (docs: "Event subscriptions",
// cf.email.sending.message.bounced). Only a HARD bounce of the post-election
// message changes anything; a bounce before the message was sent (the
// confirmation email) stores nothing, because nothing was stored.
export async function handleEmailEvents(env, events, now = Date.now()) {
  let n = 0;
  for (const e of events) {
    if (e?.type === "cf.email.sending.message.bounced" && e.payload?.bounce?.type === "hard")
      n += await recordHardBounce(env, e.payload.recipient, now);
  }
  return n;
}

// Accounts whose latest next_election consent is granted keep only the sign-in
// id and the contact; their forecasts go. Every other account is deleted. In
// batches of DELETION_BATCH_SIZE per run; recorded done only when nothing is
// left to do.
export async function deletionRun(env, now) {
  const batch = intVar(env, "DELETION_BATCH_SIZE");
  const KEEP = `(SELECT granted FROM consents c WHERE c.user_id = u.id AND c.purpose = 'next_election' ORDER BY c.id DESC LIMIT 1)`;
  const { results } = await env.DB.prepare(
    `SELECT u.id, ${KEEP} AS keep FROM users u
     WHERE ${KEEP} IS NOT 1 OR EXISTS (SELECT 1 FROM forecasts f WHERE f.user_id = u.id) LIMIT ?`).bind(batch).all();
  let deleted = 0, kept = 0;
  for (const u of results) {
    if (u.keep === 1) { await deleteForecastsOf(env, u.id, new Date(now)); kept++; }
    else { await deleteUser(env, u.id, new Date(now)); deleted++; }
  }
  const done = results.length < batch;
  if (done) await markDone(env, "deletion_run", { last_batch: { deleted, kept } }, now);
  log({ deletion_run: { deleted, kept, done } });
  return { deleted, kept, done };
}

// ---- the reply to the post-election message --------------------------------
// GET shows a confirmation page with a button; only the POST acts. Mail
// scanners follow GET links, and must not be able to delete an account. The
// token is in the fragment (#t=), which the browser never sends, so it reaches
// no log; a script copies it into the form.

const page = (title, body) => new Response(`<!doctype html><html lang="en-ZA"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex"><meta name="referrer" content="no-referrer"><title>${title}</title></head>
<body style="font:16px/1.5 system-ui,sans-serif;max-width:40em;margin:2em auto;padding:0 16px"><h1>${title}</h1>${body}</body></html>`,
  { headers: { "content-type": "text/html; charset=utf-8", "cache-control": "no-store" } });

const CHOICES = { delete: "Delete my account, my forecasts and my contact details", notify: "Tell me about the next election" };

export function replyGet(choice) {
  return page("Confirm your choice", `<form method="post" action="/api/reply"><input type="hidden" name="t" id="t" value="">
<input type="hidden" name="c" value="${esc(choice)}"><button type="submit" id="go">${esc(CHOICES[choice])}</button></form>
<p id="nolink" hidden>This link is incomplete. Open it again from the email.</p>
<noscript><p>This page needs JavaScript to read the link. Open it in a browser with JavaScript on, or sign in and use “Delete my account”.</p></noscript>${FRAGMENT_SCRIPT}`);
}

export async function replyPost(request, env, now = Date.now()) {
  const form = await readForm(request);
  const p = await verifyToken(env.SESSION_SIGNING_KEY, "reply", form.get("t") || "", now);
  if (!p) return page("This link has expired", "<p>Sign in and use “Delete my account” instead.</p>");
  // The button the reader pressed must be the choice the link was minted for.
  if (form.get("c") !== p.c) return page("This link does not match", "<p>Open the link again from the email.</p>");
  const exists = await env.DB.prepare("SELECT 1 AS x FROM users WHERE id = ?").bind(p.u).first();
  if (!exists) return page("Nothing to do", "<p>This account no longer exists.</p>");
  if (p.c === "delete") {
    await deleteUser(env, p.u, new Date(now));
    return page("Deleted", "<p>Your account, forecasts and contact details are deleted.</p>");
  }
  await env.DB.batch(consentRows(env, p.u, { next_election: true }, new Date(now).toISOString(), POST_ELECTION_WORDING_VERSION));
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
