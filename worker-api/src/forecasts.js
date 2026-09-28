// Saving, editing, reading, sharing, reporting and deleting readers' forecasts.

import schema from "../generated/forecast.schema.json";
import geom from "../generated/geometry.json";
import { HttpError, json, readJsonBody, requireSameOrigin, isLocked, intVar, clientIp } from "./http.js";
import { requireUser } from "./auth.js";
import { currentConsents, maySave } from "./consent.js";
import { validateForecast } from "./validate.js";
import { computeSeats } from "./seats.js";
import { verifyTurnstile } from "./turnstile.js";
import { randomId } from "./crypto.js";
import { deleteForecast } from "./deletion.js";
import { forecastPage, gonePage, cardSVG, renderPNG, cardKey } from "./render.js";

export { schema, geom };

export const ID_RE = /^[A-Za-z0-9]{10}$/;

function refuseIfLocked(env, now) {
  if (isLocked(env, now)) throw new HttpError(423, "forecasts are locked: polls have opened");
}

// Everything a write must pass before its body is read.
async function writeGate(request, env, now) {
  requireSameOrigin(request, env);
  refuseIfLocked(env, now);
  const user = await requireUser(request, env);
  if (!maySave(await currentConsents(env, user.id)))
    throw new HttpError(403, "saving needs your consent to store the forecast");
  if (env.RL_SAVE) {
    const { success } = await env.RL_SAVE.limit({ key: `save:${clientIp(request)}` });
    if (!success) throw new HttpError(429, "too many saves; wait a minute");
  }
  await verifyTurnstile(env, request);
  return user;
}

async function readValid(request, env) {
  const v = validateForecast(await readJsonBody(request, env), schema);
  if (!v.ok) throw new HttpError(400, v.reason, v.field);
  return v.value;
}

async function takeQuota(env, userId, now) {
  const day = new Date(now).toISOString().slice(0, 10);
  const row = await env.DB.prepare(
    `INSERT INTO save_quota (user_id, day, n) VALUES (?, ?, 1)
     ON CONFLICT (user_id, day) DO UPDATE SET n = n + 1 RETURNING n`).bind(userId, day).first();
  if (row.n > intVar(env, "SAVES_PER_USER_PER_DAY")) throw new HttpError(429, "daily save limit reached");
}

export async function createForecast(request, env, now = Date.now()) {
  const user = await writeGate(request, env, now);
  const f = await readValid(request, env);
  const { n } = await env.DB.prepare("SELECT COUNT(*) AS n FROM forecasts WHERE user_id = ?").bind(user.id).first();
  if (n >= intVar(env, "MAX_FORECASTS_PER_USER")) throw new HttpError(409, "you have the most forecasts one account may keep; delete one first");
  await takeQuota(env, user.id, now);
  const seats = await computeSeats(env, f, schema);
  const at = new Date(now).toISOString();
  for (let attempt = 0; attempt < 3; attempt++) {
    const id = randomId(10);
    try {
      await env.DB.prepare(
        `INSERT INTO forecasts (id, user_id, rev, body, model_ref, seats, seats_code_ref, created_at, updated_at)
         SELECT ?1, ?2, 1, ?3, ?4, ?5, ?6, ?7, ?7 WHERE NOT EXISTS (SELECT 1 FROM deleted_forecasts WHERE id = ?1)`)
        .bind(id, user.id, JSON.stringify(f), f.model_ref, JSON.stringify(seats), seats.code_ref, at).run()
        .then(r => { if (!r.meta.changes) throw new Error("UNIQUE: id was used before"); });
      return json({ id, rev: 1, url: `${env.SITE_ORIGIN}/f/${id}`, seats }, 201);
    } catch (e) {
      if (!/UNIQUE/i.test(String(e))) throw e;
    }
  }
  throw new HttpError(500, "could not allocate an id");
}

async function ownRow(env, id, user) {
  if (!ID_RE.test(id)) throw new HttpError(404, "no such forecast");
  const row = await env.DB.prepare("SELECT * FROM forecasts WHERE id = ?").bind(id).first();
  // Someone else's forecast answers 404, not 403: existence is not disclosed.
  if (!row || row.user_id !== user.id) throw new HttpError(404, "no such forecast");
  return row;
}

export async function updateForecast(request, env, id, now = Date.now()) {
  const user = await writeGate(request, env, now);
  const row = await ownRow(env, id, user);
  if (row.locked_at) throw new HttpError(423, "this forecast is locked");
  const f = await readValid(request, env);
  await takeQuota(env, user.id, now);
  const seats = await computeSeats(env, f, schema);
  const at = new Date(now).toISOString();
  const r = await env.DB.prepare(
    `UPDATE forecasts SET body = ?, model_ref = ?, seats = ?, seats_code_ref = ?, rev = rev + 1, updated_at = ?
     WHERE id = ? AND user_id = ? AND rev = ? AND locked_at IS NULL`)
    .bind(JSON.stringify(f), f.model_ref, JSON.stringify(seats), seats.code_ref, at, id, user.id, row.rev).run();
  if (!r.meta.changes) throw new HttpError(409, "the forecast changed while you were editing; reload");
  return json({ id, rev: row.rev + 1, url: `${env.SITE_ORIGIN}/f/${id}`, seats });
}

// Deletion stays open after the lock: the right to delete does not expire.
export async function removeForecast(request, env, id) {
  requireSameOrigin(request, env);
  const user = await requireUser(request, env);
  await ownRow(env, id, user);
  await deleteForecast(env, id);
  return new Response(null, { status: 204 });
}

export async function listMine(request, env) {
  const user = await requireUser(request, env);
  const { results } = await env.DB.prepare(
    "SELECT id, rev, created_at, updated_at, locked_at FROM forecasts WHERE user_id = ? ORDER BY created_at DESC")
    .bind(user.id).all();
  return json({ forecasts: results.map(r => ({ ...r, url: `${env.SITE_ORIGIN}/f/${r.id}` })) });
}

// Public lookup. Returns { row } or { gone: "deleted" | "hidden" | "missing" }.
async function lookup(env, id) {
  if (!ID_RE.test(id)) return { gone: "missing" };
  const row = await env.DB.prepare("SELECT * FROM forecasts WHERE id = ?").bind(id).first();
  if (row) return row.hidden ? { gone: "hidden" } : { row };
  const del = await env.DB.prepare("SELECT 1 AS x FROM deleted_forecasts WHERE id = ?").bind(id).first();
  return { gone: del ? "deleted" : "missing" };
}

const goneStatus = g => (g === "missing" ? 404 : 410);

export async function getPublic(env, id) {
  const { row, gone } = await lookup(env, id);
  if (gone) return json({ error: gone }, goneStatus(gone));
  const body = JSON.parse(row.body);
  return json({ id: row.id, rev: row.rev, created_at: row.created_at, updated_at: row.updated_at,
    locked: Boolean(row.locked_at), ...body, seats: JSON.parse(row.seats) },
    200, { "cache-control": "public, max-age=60" });
}

export async function sharePage(env, id) {
  const { row, gone } = await lookup(env, id);
  const headers = { "content-type": "text/html; charset=utf-8", "x-robots-tag": "noindex" };
  if (gone) return new Response(gonePage(gone), { status: goneStatus(gone), headers: { ...headers, "cache-control": "no-store" } });
  return new Response(forecastPage(row, schema, geom, env), { headers: { ...headers, "cache-control": "public, max-age=60" } });
}

// The card is rendered only for an existing id at its current rev; any other
// `v` redirects, so arbitrary input cannot drive the renderer.
export async function card(request, env, ctx, id, size) {
  const { row, gone } = await lookup(env, id);
  if (gone) return new Response(null, { status: goneStatus(gone) });
  const v = new URL(request.url).searchParams.get("v");
  const file = size === "story" ? "card-story.png" : "card.png";
  if (v !== String(row.rev))
    return new Response(null, { status: 302, headers: { location: `/f/${id}/${file}?v=${row.rev}`, "cache-control": "no-store" } });
  const key = cardKey(row, size);
  const headers = { "content-type": "image/png", "cache-control": "public, max-age=31536000, immutable", "x-robots-tag": "noindex" };
  const hit = env.CARDS ? await env.CARDS.get(key) : null;
  if (hit) return new Response(hit.body, { headers });
  const png = await renderPNG(cardSVG(row, schema, geom, size));
  if (env.CARDS) ctx.waitUntil(env.CARDS.put(key, png, { httpMetadata: { contentType: "image/png" } }));
  return new Response(png, { headers });
}

const REPORT_REASONS = new Set(["abusive name", "impersonation", "personal information", "other"]);

export async function report(request, env, id) {
  requireSameOrigin(request, env);
  if (env.RL_SAVE) {
    const { success } = await env.RL_SAVE.limit({ key: `report:${clientIp(request)}` });
    if (!success) throw new HttpError(429, "too many reports; wait a minute");
  }
  const body = await readJsonBody(request, env);
  if (!body || !REPORT_REASONS.has(body.reason)) throw new HttpError(400, "reason must be one of: " + [...REPORT_REASONS].join(", "), "reason");
  const { row } = await lookup(env, id);
  if (!row) throw new HttpError(404, "no such forecast");
  await env.DB.prepare("INSERT INTO reports (forecast_id, reason, at) VALUES (?, ?, ?)")
    .bind(id, body.reason, new Date().toISOString()).run();
  return new Response(null, { status: 204 });
}
