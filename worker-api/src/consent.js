// The consent screen's server side, and the append-only consent log.
//
// Four separate choices, each sent explicitly as true or false; a missing
// choice is refused rather than defaulted (the boxes are unticked, and an
// unticked box is a "false" the page must send, not an absence we fill in).
//
//   store           REQUIRED to save: explicit consent to hold a forecast,
//                   which can reveal political persuasion (POPIA s26, s27(1)(a))
//   age18           REQUIRED to save: the reader is 18 or older (s34-35)
//   contact_if_win  optional: contact me if my forecast wins
//   updates         optional: send me updates (s69 opt-in)
//
// A fifth purpose, next_election, is recorded only by the reply to the
// post-election message (src/scheduled.js).
//
// Every decision is a new row carrying CONSENT_WORDING_VERSION. Nothing
// updates or deletes a row while the account exists (migration triggers).

import { HttpError, json, readJsonBody, clearCookie } from "./http.js";
import { readPending, createSession, sessionUser } from "./auth.js";
import { randomId } from "./crypto.js";
import { deleteForecastsOf } from "./deletion.js";

export const SCREEN_PURPOSES = ["store", "age18", "contact_if_win", "updates"];
const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function parseChoices(body) {
  if (!body || typeof body !== "object" || Array.isArray(body)) throw new HttpError(400, "must be a JSON object");
  const allowed = new Set([...SCREEN_PURPOSES, "contact"]);
  for (const k of Object.keys(body)) if (!allowed.has(k)) throw new HttpError(400, "not accepted", k);
  const out = {};
  for (const p of SCREEN_PURPOSES) {
    if (typeof body[p] !== "boolean") throw new HttpError(400, "must be true or false (no default)", p);
    out[p] = body[p];
  }
  if (body.contact !== undefined && body.contact !== null) {
    if (typeof body.contact !== "string" || body.contact.length > 254 || !EMAIL.test(body.contact))
      throw new HttpError(400, "not an email address", "contact");
    out.contact = body.contact.toLowerCase();
  }
  return out;
}

export function consentRows(env, userId, choices, at) {
  return Object.entries(choices)
    .filter(([p]) => p !== "contact")
    .map(([purpose, granted]) => env.DB.prepare(
      "INSERT INTO consents (user_id, purpose, granted, wording_version, at) VALUES (?, ?, ?, ?, ?)")
      .bind(userId, purpose, granted ? 1 : 0, env.CONSENT_WORDING_VERSION, at));
}

export async function currentConsents(env, userId) {
  const { results } = await env.DB.prepare(
    `SELECT purpose, granted, wording_version, at FROM consents c
     WHERE user_id = ?1 AND id = (SELECT MAX(id) FROM consents WHERE user_id = ?1 AND purpose = c.purpose)`)
    .bind(userId).all();
  return Object.fromEntries(results.map(r => [r.purpose, { granted: r.granted === 1, wording_version: r.wording_version, at: r.at }]));
}

export const maySave = c => Boolean(c.store?.granted && c.age18?.granted);

export async function postConsent(request, env, now = new Date()) {
  const choices = parseChoices(await readJsonBody(request, env));
  const at = now.toISOString();
  const user = await sessionUser(request, env);

  if (user) {
    if (choices.contact && user.contact) throw new HttpError(400, "a contact is already held; delete the account to change it", "contact");
    const stmts = consentRows(env, user.id, choices, at);
    if (choices.contact)
      stmts.push(env.DB.prepare("UPDATE users SET contact_kind = 'email', contact = ?, contact_verified = 0 WHERE id = ?")
        .bind(choices.contact, user.id));
    await env.DB.batch(stmts);
    // Withdrawing either required consent withdraws the basis for holding
    // forecasts: they are deleted now, the account and its log remain.
    let deleted = 0;
    if (!choices.store || !choices.age18) deleted = await deleteForecastsOf(env, user.id, now);
    return json({ ok: true, consents: await currentConsents(env, user.id), forecasts_deleted: deleted });
  }

  const pending = await readPending(request, env);
  if (!pending) throw new HttpError(401, "sign in first");
  if (!choices.store || !choices.age18)
    throw new HttpError(400, "saving needs consent to store the forecast and confirmation of age 18 or over", !choices.store ? "store" : "age18");

  let contact_kind = pending.ck, contact = pending.c, verified = pending.cv ? 1 : 0;
  if (!contact && choices.contact) { contact_kind = "email"; contact = choices.contact; verified = 0; }

  const id = randomId(16);
  try {
    await env.DB.batch([
      env.DB.prepare(`INSERT INTO users (id, provider, provider_sub, contact_kind, contact, contact_verified, created_at)
                      VALUES (?, ?, ?, ?, ?, ?, ?)`)
        .bind(id, pending.provider, pending.sub, contact_kind, contact, verified, at),
      ...consentRows(env, id, choices, at),
    ]);
  } catch (e) {
    if (/UNIQUE/i.test(String(e))) throw new HttpError(409, "this account already exists; sign in again");
    throw e;
  }
  const h = new Headers({ "content-type": "application/json; charset=utf-8", "cache-control": "no-store" });
  h.append("set-cookie", await createSession(env, id, now.getTime()));
  h.append("set-cookie", clearCookie(env, "pending"));
  return new Response(JSON.stringify({ ok: true, consents: await currentConsents(env, id),
    contact_needs_verification: Boolean(contact) && !verified }), { status: 201, headers: h });
}

