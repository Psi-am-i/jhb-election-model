// The consent screen's server side, the append-only consent log, and the
// confirmation of a contact address.
//
// The screen's wording, its four purposes and the keys the page sends are
// defined ONCE, in interactive/js/consent-terms.js, which the page renders
// from and this module imports:
//
//   store           REQUIRED to save: explicit consent to hold the reader's
//                   prediction, linked to their sign-in
//   age18           REQUIRED to save: the reader is 18 or older (s34-35)
//   contact_if_win  optional: contact me if my prediction wins
//   updates         optional: send me updates (s69 opt-in)
//   contact         optional: an address to confirm (below)
//   wording_version REQUIRED: the hash of the text the page showed
//
// Each purpose is sent explicitly as true or false; a missing one is refused
// rather than defaulted. A fifth purpose, next_election, is recorded only by
// the reply to the post-election message (src/lifecycle.js).
//
// WORDING VERSION: the hash of the displayed terms (consent-terms.js). The
// server recomputes it from the terms it would show today, with the deletion
// date it holds, and refuses a mismatch (409), so a stale page cannot record
// consent to text the server no longer shows.
//
// CONTACTS (R5 findings 2 and 7, owner 2026-09-29): only a CONFIRMED address is
// stored. A provider-verified email (Google, Apple, X) is stored at consent.
// Any other address (Facebook's and Microsoft's, which do not assert
// verification, or one the reader typed) is NOT stored: one confirmation email
// per account is sent to it, carrying the address inside a signed link, and
// the address becomes the account's contact only when that link is used
// (GET shows a button; only the POST acts, as mail scanners follow links).
// An account that never confirms holds no contact, gets no post-election
// message, and is deleted by the deletion run on DELETION_AT, as the consent
// screen states ("No confirmed email").
//
// Every decision is a new row carrying the wording version. Nothing updates or
// deletes a row while the account exists (migration triggers).

import { HttpError, json, readJsonBody, clearCookie, requireSameOrigin, readForm, clientIp } from "./http.js";
import { readPending, createSession, sessionUser, requireUser, handleCookie } from "./auth.js";
import { randomId, signToken, verifyToken } from "./crypto.js";
import { deleteForecastsOf } from "./deletion.js";
import { sendMail, confirmationMessage } from "./mail.js";
import { SCREEN_PURPOSES, CONSENT_KEYS, consentTerms, wordingVersion, deletionDateText } from "../../interactive/js/consent-terms.js";
import { esc } from "../../interactive/js/common.js";

export { SCREEN_PURPOSES };
const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
export const CONFIRM_TTL = 7 * 86400;   // seconds a confirmation link stays usable

// The wording version the server would record now: the hash of the terms it
// would display, with its own deletion date.
export async function currentWordingVersion(env) {
  return wordingVersion(consentTerms({ deletionDate: deletionDateText(env.DELETION_AT) }));
}

export function parseChoices(body) {
  if (!body || typeof body !== "object" || Array.isArray(body)) throw new HttpError(400, "must be a JSON object");
  const allowed = new Set(CONSENT_KEYS);
  for (const k of Object.keys(body)) if (!allowed.has(k)) throw new HttpError(400, "not accepted", k);
  const out = {};
  for (const p of SCREEN_PURPOSES) {
    if (typeof body[p] !== "boolean") throw new HttpError(400, "must be true or false (no default)", p);
    out[p] = body[p];
  }
  if (typeof body.wording_version !== "string" || !body.wording_version)
    throw new HttpError(400, "required: the version of the wording shown", "wording_version");
  if (body.contact !== undefined && body.contact !== null) {
    if (typeof body.contact !== "string" || body.contact.length > 254 || !EMAIL.test(body.contact))
      throw new HttpError(400, "not an email address", "contact");
    out.contact = body.contact.toLowerCase();
  }
  return { choices: out, shown: body.wording_version };
}

// One INSERT per purpose. `version` names the wording the reader was shown.
export function consentRows(env, userId, choices, at, version) {
  if (!version) throw new Error("consentRows: a wording version is required");
  return Object.entries(choices)
    .filter(([p]) => p !== "contact")
    .map(([purpose, granted]) => env.DB.prepare(
      "INSERT INTO consents (user_id, purpose, granted, wording_version, at) VALUES (?, ?, ?, ?, ?)")
      .bind(userId, purpose, granted ? 1 : 0, version, at));
}

export async function currentConsents(env, userId) {
  const { results } = await env.DB.prepare(
    `SELECT purpose, granted, wording_version, at FROM consents c
     WHERE user_id = ?1 AND id = (SELECT MAX(id) FROM consents WHERE user_id = ?1 AND purpose = c.purpose)`)
    .bind(userId).all();
  return Object.fromEntries(results.map(r => [r.purpose, { granted: r.granted === 1, wording_version: r.wording_version, at: r.at }]));
}

export const maySave = c => Boolean(c.store?.granted && c.age18?.granted);

// Sends the one confirmation email for this account, if none has been sent.
// Returns "sent", "not_sent" (the transport failed; nothing recorded, so the
// reader may ask again), or "already_sent".
export async function sendConfirmation(env, userId, address, now = Date.now()) {
  const row = await env.DB.prepare("SELECT contact, confirm_sent_at FROM users WHERE id = ?").bind(userId).first();
  if (!row) throw new HttpError(401, "sign in first");
  if (row.contact) throw new HttpError(400, "a contact is already held; delete the account to change it", "contact");
  if (row.confirm_sent_at) return "already_sent";
  const t = await signToken(env.SESSION_SIGNING_KEY, "confirm", { u: userId, c: address }, CONFIRM_TTL, now);
  // The token travels in the fragment, which browsers never send to a server,
  // so it reaches no request log (R5 finding 10).
  const r = await sendMail(env, { to: address, ...confirmationMessage({ confirmUrl: `${env.SITE_ORIGIN}/api/contact/confirm#t=${t}` }) });
  if (!r.sent) return "not_sent";
  // Conditional, so two racing requests cannot both count as the one email.
  await env.DB.prepare("UPDATE users SET confirm_sent_at = ? WHERE id = ? AND confirm_sent_at IS NULL")
    .bind(new Date(now).toISOString(), userId).run();
  return "sent";
}

export async function postConsent(request, env, now = new Date()) {
  const { choices, shown } = parseChoices(await readJsonBody(request, env));
  const version = await currentWordingVersion(env);
  if (shown !== version)
    throw new HttpError(409, "the consent wording has changed since this page loaded; reload and read it again", "wording_version");
  const at = now.toISOString();
  const user = await sessionUser(request, env);

  if (user) {
    if (choices.contact && user.contact) throw new HttpError(400, "a contact is already held; delete the account to change it", "contact");
    await env.DB.batch(consentRows(env, user.id, choices, at, version));
    // Withdrawing either required consent withdraws the basis for holding
    // forecasts: they are deleted now, the account and its log remain.
    let deleted = 0;
    if (!choices.store || !choices.age18) deleted = await deleteForecastsOf(env, user.id, now);
    const confirmation = choices.contact ? await sendConfirmation(env, user.id, choices.contact, now.getTime()) : null;
    return json({ ok: true, consents: await currentConsents(env, user.id), forecasts_deleted: deleted, confirmation });
  }

  const pending = await readPending(request, env);
  if (!pending) throw new HttpError(401, "sign in first");
  if (!choices.store || !choices.age18)
    throw new HttpError(400, "saving needs consent to store the prediction and confirmation of age 18 or over", !choices.store ? "store" : "age18");

  // Only a provider-verified address is stored now.
  const verified = Boolean(pending.c && pending.cv);
  const id = randomId(16);
  try {
    await env.DB.batch([
      env.DB.prepare(`INSERT INTO users (id, provider, provider_sub, contact_kind, contact, contact_verified, created_at)
                      VALUES (?, ?, ?, ?, ?, ?, ?)`)
        .bind(id, pending.provider, pending.sub, verified ? pending.ck : null, verified ? pending.c : null, verified ? 1 : 0, at),
      ...consentRows(env, id, choices, at, version),
    ]);
  } catch (e) {
    if (/UNIQUE/i.test(String(e))) throw new HttpError(409, "this account already exists; sign in again");
    throw e;
  }
  const confirmation = !verified && choices.contact ? await sendConfirmation(env, id, choices.contact, now.getTime()) : null;
  const h = new Headers({ "content-type": "application/json; charset=utf-8", "cache-control": "no-store" });
  h.append("set-cookie", await createSession(env, id, now.getTime()));
  h.append("set-cookie", clearCookie(env, "pending"));
  if (pending.h) h.append("set-cookie", await handleCookie(env, id, pending.h, now.getTime()));
  return new Response(JSON.stringify({ ok: true, consents: await currentConsents(env, id),
    contact_confirmed: verified, confirmation }), { status: 201, headers: h });
}

// POST /api/contact {contact}: a signed-in reader with no confirmed contact
// asks for the one confirmation email. Rate-limited per address like saves.
export async function requestConfirmation(request, env, now = Date.now()) {
  requireSameOrigin(request, env);
  const user = await requireUser(request, env);
  if (env.RL_AUTH) {
    const { success } = await env.RL_AUTH.limit({ key: `confirm:${clientIp(request)}` });
    if (!success) throw new HttpError(429, "too many requests; wait a minute");
  }
  const body = await readJsonBody(request, env);
  if (!body || typeof body !== "object" || Array.isArray(body)) throw new HttpError(400, "must be a JSON object");
  for (const k of Object.keys(body)) if (k !== "contact") throw new HttpError(400, "not accepted", k);
  if (typeof body.contact !== "string" || body.contact.length > 254 || !EMAIL.test(body.contact))
    throw new HttpError(400, "not an email address", "contact");
  return json({ confirmation: await sendConfirmation(env, user.id, body.contact.toLowerCase(), now) });
}

const page = (title, body) => new Response(`<!doctype html><html lang="en-ZA"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex"><meta name="referrer" content="no-referrer"><title>${title}</title></head>
<body style="font:16px/1.5 system-ui,sans-serif;max-width:40em;margin:2em auto;padding:0 16px"><h1>${title}</h1>${body}</body></html>`,
  { headers: { "content-type": "text/html; charset=utf-8", "cache-control": "no-store" } });

// The script copies the token from the fragment (never sent to the server) into
// the form. Without JavaScript the reader is told what to do instead.
export const FRAGMENT_SCRIPT = `<script>(function(){var m=/[#&]t=([^&]*)/.exec(location.hash);if(m){document.getElementById("t").value=decodeURIComponent(m[1]);}else{document.getElementById("go").disabled=true;document.getElementById("nolink").hidden=false;}})();</script>`;

export function confirmGet() {
  return page("Confirm your email address", `<form method="post" action="/api/contact/confirm"><input type="hidden" name="t" id="t" value="">
<button type="submit" id="go">Confirm this address</button></form>
<p id="nolink" hidden>This link is incomplete. Open it again from the email.</p>
<noscript><p>This page needs JavaScript to read the link. Open it in a browser with JavaScript on.</p></noscript>${FRAGMENT_SCRIPT}`);
}

export async function confirmPost(request, env, now = Date.now()) {
  const form = await readForm(request);
  const p = await verifyToken(env.SESSION_SIGNING_KEY, "confirm", form.get("t") || "", now);
  if (!p || typeof p.u !== "string" || typeof p.c !== "string" || !EMAIL.test(p.c))
    return page("This link has expired", "<p>Sign in and ask for a new confirmation from “My forecasts”.</p>");
  const r = await env.DB.prepare(
    "UPDATE users SET contact_kind = 'email', contact = ?, contact_verified = 1 WHERE id = ? AND contact IS NULL")
    .bind(p.c, p.u).run();
  if (!r.meta.changes) return page("Nothing to do", "<p>This account no longer exists, or already has a confirmed address.</p>");
  return page("Confirmed", `<p>We will use ${esc(p.c)} for the messages you asked for, and for the one message after the election.</p>`);
}
