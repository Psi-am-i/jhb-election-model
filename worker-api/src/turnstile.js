// Turnstile on save. The page sends the widget's token in the
// `cf-turnstile-response` header, so the forecast body stays exactly the schema.
//
// Fails CLOSED: with TURNSTILE_REQUIRED other than "false" and no
// TURNSTILE_SECRET, every save is refused. Only the `dev` environment sets
// TURNSTILE_REQUIRED = "false".

import { HttpError } from "./http.js";

const SITEVERIFY = "https://challenges.cloudflare.com/turnstile/v0/siteverify";

export async function verifyTurnstile(env, request, fetcher = fetch) {
  if (env.TURNSTILE_REQUIRED === "false") return { skipped: true };
  if (!env.TURNSTILE_SECRET) throw new HttpError(503, "saving is not available: bot check not configured");
  const token = request.headers.get("cf-turnstile-response");
  if (!token || token.length > 2048) throw new HttpError(403, "bot check missing; reload and try again");
  const form = new FormData();
  form.append("secret", env.TURNSTILE_SECRET);
  form.append("response", token);
  const ip = request.headers.get("cf-connecting-ip");
  if (ip) form.append("remoteip", ip);
  let out;
  try {
    const r = await fetcher(SITEVERIFY, { method: "POST", body: form });
    out = await r.json();
  } catch {
    throw new HttpError(503, "bot check unavailable; try again");
  }
  if (!out?.success) throw new HttpError(403, "bot check failed; reload and try again");
  const host = new URL(env.SITE_ORIGIN).hostname;
  if (out.hostname && out.hostname !== host) throw new HttpError(403, "bot check was for another site");
  return { skipped: false };
}
