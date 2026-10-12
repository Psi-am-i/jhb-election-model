// joburg-forecasts: the router.
//
//   GET    /auth/:provider/start?return=/path   302 to the provider
//   GET    /auth/:provider/callback             (POST for Apple: form_post)
//   POST   /auth/facebook/data-deletion         Facebook's deletion callback
//   POST   /auth/apple/notifications            501 stub (see lifecycle.js)
//   GET    /api/me                              session, pending sign-in, consents
//   DELETE /api/me                              erase the account and everything in it
//   POST   /api/consent                         the consent screen's answer
//   POST   /api/logout
//   GET    /api/my/forecasts
//   POST   /api/forecasts                       save (sign-in, consent, Turnstile)
//   GET    /api/forecasts/:id                   public JSON
//   PUT    /api/forecasts/:id                   edit (owner; not after the lock)
//   DELETE /api/forecasts/:id                   delete (owner; also after the lock)
//   POST   /api/forecasts/:id/report
//   POST   /api/contact                         ask for the one confirmation email
//   GET    /api/contact/confirm#t=  POST ...     confirm an address (token in the fragment)
//   GET    /api/reply/(delete|notify)#t=        the post-election message's answer:
//   POST   /api/reply                             GET shows a button, POST acts
//   GET    /api/deletion-status
//   GET    /f/:id                               HTML with Open Graph tags
//   GET    /f/:id/card.png?v=rev                1200x630, rendered here
//   GET    /f/:id/card-story.png?v=rev          1080x1920

import { errorResponse, json, requireSameOrigin, HttpError, clearCookie } from "./http.js";
import { startAuth, callbackAuth, sessionUser, readPending, logout, requireUser, readHandle } from "./auth.js";
import { postConsent, currentConsents, currentWordingVersion, requestConfirmation, confirmGet, confirmPost } from "./consent.js";
import { deletionDateText } from "../../interactive/js/consent-terms.js";
import { createForecast, updateForecast, removeForecast, listMine, getPublic, sharePage, card, report } from "./forecasts.js";
import { deleteUser } from "./deletion.js";
import { runScheduled, replyGet, replyPost, facebookDataDeletion, deletionStatus, appleNotifications, handleEmailEvents } from "./lifecycle.js";

// `deletion_date` and `wording_version` let the page render the consent terms
// exactly as the server will hash them (interactive/js/consent-terms.js).
async function me(request, env) {
  const terms = { deletion_date: env.DELETION_AT || null, wording_version: await currentWordingVersion(env),
    deletion_date_text: deletionDateText(env.DELETION_AT) };
  const u = await sessionUser(request, env);
  if (u) {
    return json({ signed_in: true, provider: u.provider, contact_kind: u.contact_kind,
      has_contact: Boolean(u.contact), confirmation_sent: Boolean(u.confirm_sent_at),
      handle: await readHandle(request, env, u.id),
      consents: await currentConsents(env, u.id), ...terms });
  }
  const p = await readPending(request, env);
  // An address the provider did not verify is shown back to its owner (to
  // prefill the confirmation box), never stored.
  if (p) return json({ signed_in: false, pending: true, provider: p.provider,
    contact_confirmed: Boolean(p.c && p.cv), unconfirmed_contact: p.c && !p.cv ? p.c : null,
    handle: p.h || null, ...terms });
  return json({ signed_in: false, ...terms });
}

async function deleteMe(request, env) {
  requireSameOrigin(request, env);
  const u = await requireUser(request, env);
  const r = await deleteUser(env, u.id);
  const h = new Headers({ "content-type": "application/json; charset=utf-8", "cache-control": "no-store" });
  h.append("set-cookie", clearCookie(env, "session"));
  h.append("set-cookie", clearCookie(env, "handle"));
  return new Response(JSON.stringify({ deleted: true, ...r }), { status: 200, headers: h });
}

async function route(request, env, ctx) {
  const url = new URL(request.url);
  const path = url.pathname;
  const m = request.method;
  let g;

  if ((g = path.match(/^\/auth\/([a-z]+)\/start$/)) && m === "GET") return startAuth(request, env, g[1]);
  if (path === "/auth/facebook/data-deletion" && m === "POST") return facebookDataDeletion(request, env);
  if (path === "/auth/apple/notifications" && m === "POST") return appleNotifications();
  if ((g = path.match(/^\/auth\/([a-z]+)\/callback$/)) && (m === "GET" || m === "POST")) return callbackAuth(request, env, g[1]);

  if (path === "/api/me" && m === "GET") return me(request, env);
  if (path === "/api/me" && m === "DELETE") return deleteMe(request, env);
  if (path === "/api/consent" && m === "POST") { requireSameOrigin(request, env); return postConsent(request, env); }
  if (path === "/api/logout" && m === "POST") { requireSameOrigin(request, env); return logout(request, env); }
  if (path === "/api/my/forecasts" && m === "GET") return listMine(request, env);
  if (path === "/api/forecasts" && m === "POST") return createForecast(request, env);
  if ((g = path.match(/^\/api\/forecasts\/([^/]+)$/))) {
    if (m === "GET") return getPublic(env, g[1]);
    if (m === "PUT") return updateForecast(request, env, g[1]);
    if (m === "DELETE") return removeForecast(request, env, g[1]);
  }
  if ((g = path.match(/^\/api\/forecasts\/([^/]+)\/report$/)) && m === "POST") return report(request, env, g[1]);
  if (path === "/api/contact" && m === "POST") return requestConfirmation(request, env);
  if (path === "/api/contact/confirm" && m === "GET") return confirmGet();
  if (path === "/api/contact/confirm" && m === "POST") return confirmPost(request, env);
  if ((g = path.match(/^\/api\/reply\/(delete|notify)$/)) && m === "GET") return replyGet(g[1]);
  if (path === "/api/reply" && m === "POST") return replyPost(request, env);
  if (path === "/api/deletion-status" && m === "GET") return deletionStatus();

  if ((g = path.match(/^\/f\/([^/]+)\/?$/)) && m === "GET") return sharePage(env, g[1]);
  if ((g = path.match(/^\/f\/([^/]+)\/card(-story)?\.png$/)) && m === "GET") return card(request, env, ctx, g[1], g[2] ? "story" : "link");

  throw new HttpError(404, "not found");
}

export default {
  async fetch(request, env, ctx) {
    try {
      return await route(request, env, ctx);
    } catch (e) {
      return errorResponse(e);
    }
  },
  // Email Service delivery events (a hard bounce after the message was accepted).
  // ⛔ NOT WIRED: no queue or event subscription exists in wrangler.jsonc; the
  // owner creates the queue, subscribes it to the sending domain's events and
  // adds the consumer. Until then a hard bounce is only seen synchronously
  // (E_RECIPIENT_SUPPRESSED, src/mail.js).
  async queue(batch, env) {
    await handleEmailEvents(env, batch.messages.map(m => m.body));
    batch.ackAll();
  },
  async scheduled(controller, env, ctx) {
    ctx.waitUntil(runScheduled(env, controller.scheduledTime).then(r => console.log(JSON.stringify({ scheduled: r }))));
  },
};
