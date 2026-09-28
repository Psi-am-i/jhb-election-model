// Deletion: a forecast, or a whole account. POPIA s24.
//
// Deleting an account removes, in one D1 batch (one transaction): the user row,
// which cascades to sessions, forecasts, reports and save_quota; then the
// consent log rows, which the append-only trigger permits only once the user
// row is gone. Each deleted forecast id is recorded in deleted_forecasts (the
// id only) so /f/<id> answers 410. Then every rendered card under
// cards/<forecast id>/ is deleted from R2.

export async function deleteCards(env, forecastId) {
  if (!env.CARDS) return 0;
  let cursor, n = 0;
  do {
    const page = await env.CARDS.list({ prefix: `cards/${forecastId}/`, cursor });
    const keys = page.objects.map(o => o.key);
    if (keys.length) { await env.CARDS.delete(keys); n += keys.length; }
    cursor = page.truncated ? page.cursor : undefined;
  } while (cursor);
  return n;
}

export async function deleteForecast(env, forecastId, now = new Date()) {
  const at = now.toISOString();
  await env.DB.batch([
    env.DB.prepare("INSERT OR IGNORE INTO deleted_forecasts (id, at) VALUES (?, ?)").bind(forecastId, at),
    env.DB.prepare("DELETE FROM forecasts WHERE id = ?").bind(forecastId),
  ]);
  await deleteCards(env, forecastId);
}

// Delete every forecast a user holds, keeping the account (withdrawal of the
// storage consent, or the post-election run for an account that asked to hear
// about the next election).
export async function deleteForecastsOf(env, userId, now = new Date()) {
  const { results } = await env.DB.prepare("SELECT id FROM forecasts WHERE user_id = ?").bind(userId).all();
  for (const r of results) await deleteForecast(env, r.id, now);
  return results.length;
}

export async function deleteUser(env, userId, now = new Date()) {
  const at = now.toISOString();
  const { results } = await env.DB.prepare("SELECT id FROM forecasts WHERE user_id = ?").bind(userId).all();
  const ids = results.map(r => r.id);
  await env.DB.batch([
    ...ids.map(id => env.DB.prepare("INSERT OR IGNORE INTO deleted_forecasts (id, at) VALUES (?, ?)").bind(id, at)),
    env.DB.prepare("DELETE FROM users WHERE id = ?").bind(userId),
    env.DB.prepare("DELETE FROM consents WHERE user_id = ?").bind(userId),
  ]);
  for (const id of ids) await deleteCards(env, id);
  return { forecasts: ids.length };
}
