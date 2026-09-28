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
//   GET    /api/reply?t=   POST /api/reply      the post-election message's answer
//   GET    /api/deletion-status
//   GET    /f/:id                               HTML with Open Graph tags
//   GET    /f/:id/card.png?v=rev                1200x630, rendered here
//   GET    /f/:id/card-story.png?v=rev          1080x1920

import { errorResponse, json, requireSameOrigin, HttpError, clearCookie } from "./http.js";
import { startAuth, callbackAuth, sessionUser, readPending, logout, requireUser } from "./auth.js";
import { postConsent, currentConsents } from "./consent.js";
import { createForecast, updateForecast, removeForecast, listMine, getPublic, sharePage, card, report } from "./forecasts.js";
import { deleteUser } from "./deletion.js";
import { runScheduled, replyGet, replyPost, facebookDataDeletion, deletionStatus, appleNotifications } from "./lifecycle.js";

async function me(request, env) {
  const u = await sessionUser(request, env);
  if (u) {
    return json({ signed_in: true, provider: u.provider, contact_kind: u.contact_kind,
      has_contact: Boolean(u.contact), contact_verified: Boolean(u.contact_verified),
      consents: await currentConsents(env, u.id), wording_version: env.CONSENT_WORDING_VERSION });
  }
  const p = await readPending(request, env);
  if (p) return json({ signed_in: false, pending: true, provider: p.provider, has_contact: Boolean(p.c),
    wording_version: env.CONSENT_WORDING_VERSION });
  return json({ signed_in: false });
}

async function deleteMe(request, env) {
  requireSameOrigin(request, env);
  const u = await requireUser(request, env);
  const r = await deleteUser(env, u.id);
  return json({ deleted: true, ...r }, 200, { "set-cookie": clearCookie(env, "session") });
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
  if (path === "/api/reply" && m === "GET") return replyGet(request, env);
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
  async scheduled(controller, env, ctx) {
    ctx.waitUntil(runScheduled(env, controller.scheduledTime).then(r => console.log(JSON.stringify({ scheduled: r }))));
  },
};
