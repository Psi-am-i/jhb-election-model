// A reader's shared forecast at the edge (audits/2026-10-03-share-design):
// what src/worker.js does for a link to /your-forecast/ that carries one.
//
//   /s/?<link>               the share sheet's links go out through here: 302 to
//                            /your-forecast/?<link>&from=1 (the arrival view),
//                            counted as one Analytics Engine data point, channel
//                            "share", with the share button used (`ch`). Only
//                            the channel, the button and the host are written.
//   /your-forecast/?f=…      the page, its og: and twitter: tags rewritten to
//                            name the forecast and point at its own image
//   /og/4/link.png?<link>    that image, drawn here: share-card.js's card,
//   /og/4/story.png?<link>   rasterised by resvg (src/og-render.js), cached at
//                            the edge by the link and the published draws'
//                            hash: a year when the link's seal checks, an
//                            hour otherwise (imageCache). Any failure
//                            answers 302 to /og.png.
//   POST /seal/1             seal a link's state (src/seal.js); refused from
//                            the moment polls open, and on preview versions
//   POST /seal/1/check       is this link sealed, and when: the signature
//                            first, then whether this page reads the forecast
//   GET /entries/1/count     how many forecasts have been sealed: one D1 count,
//                            kept at the edge COUNT_MAX_AGE_S seconds
//
// SEATS AND THE BADGE COME ONLY FROM PYTHON (DESIGN §3): the image's seats
// are the seat law's for the link's picks and its badge how close they are
// to the published prediction (reweight.outcome_badge), both from the seat
// Worker's /v1/card
// (worker-api/seats-py, reached through the service binding env.SEATS). The
// link's own figures are never read for the image, so a forged link cannot
// put on an image from this domain a seat count the law would not give. With
// no SEATS binding, or any answer but a checked 200, the image is the generic
// one.
//
// ENTRIES (owner, 2026-10-03). Every successful seal is stored as one entry
// in the D1 database bound as ENTRIES (migrations/0001_entries.sql, then
// 0002_entry_version.sql): the prediction, the name the reader typed, the
// seal's time and id, the model version and the entry version. Nothing about the person who asked: no IP address, user agent,
// cookie or account. Results night ranks every entry (src/rank_entries.py).
// The insert runs after the seal is answered (ctx.waitUntil): a failed or
// missing insert is logged with console.error, by reason only, and the reader
// keeps the seal. Before results the site shows only how many there are.
//
// The image lives in the edge cache only, which evicts on its own; the name
// on it is text the reader put in a link they chose to share. No URL, name or
// forecast is logged.

import * as MS from "../interactive/js/make-state.js";
import * as B from "../interactive/js/builder-state.js";
import { validateForecast } from "../worker-api/src/validate.js";
import { cardName } from "../interactive/js/play-state.js";
import * as SC from "../interactive/js/share-card.js";
import { seatRequest, checkSeatAnswer } from "../worker-api/src/seats.js";
import { makeSeal, checkSeal, rateKey, SEALED_KEYS } from "./seal.js";

// The keys of a shared forecast's link, in the order the image's address
// writes them: section 2's state (make-state.js), the name, the seal, and the
// friend's forecast and name on a return link (yf-url.js).
export const LINK_KEYS = ["v", "c", "f", "n", "s", "vs", "vn"];
// The share buttons that may be counted (make-share.js sets `ch`).
export const SHARE_CHANNELS = new Set(["wa", "x", "copy", "native"]);
export const FALLBACK_IMAGE = "/og.png";
export const SEATS_TIMEOUT_MS = 3000;
// How long an image whose link is not sealed may be kept, by the edge and by
// whoever fetched it, in seconds. A sealed link's image never changes and is
// kept for a year; an unsealed one would show "Sealed" once SEAL_KEY is set
// (it is not yet), so it is not kept for long.
export const UNSEALED_MAX_AGE_S = 3600;
// The image's Cache-Control: a year for a sealed link's image, an hour for any other.
export const imageCache = sealed => (sealed ? "public, max-age=31536000, immutable" : "public, max-age=" + UNSEALED_MAX_AGE_S);
const PAGE = "/your-forecast/";
// The card image's address carries CARD_VERSION, so a change to what the card
// draws changes the address and the edge's cache key: a sealed card's image
// is cached for a year as immutable. Version 2 (2026-10-10): the owner's
// reader badges and the boldest call. Version 3 (2026-10-12): the card prints
// the boldest call's own chance, measured from the published prediction, in
// place of the council outcome's. Version 4 (2026-10-13): the badge measures
// closeness to the published prediction and the card prints what it is, with
// no call and no chance (JUDGEMENT-CALLS §N10). An address of an earlier
// version answers 301 to the same image at the current one.
export const CARD_VERSION = 4;
// reweight.CLOSENESS_MEASURE: the card answer's `measure`, the same text
// (tests/test_worker_routing.py holds the two equal).
export const CLOSENESS_MEASURE = "closeness to the published prediction";
const IMAGE = /^\/og\/(\d+)\/(link|story)\.png$/;
const imagePath = size => `/og/${CARD_VERSION}/${size}.png`;

// ---------- the link ----------

// The link's own keys, in LINK_KEYS order, as one query string.
export function linkQuery(search) {
  const q = new URLSearchParams(search), out = new URLSearchParams();
  for (const k of LINK_KEYS) if (q.has(k)) out.set(k, q.get(k));
  return out.toString();
}

// The name as a card may print it: play-state.js cardName, the one rule the
// page and both share sheets use too.
export { cardName };

// ---------- the page's data, from the asset bundle ----------

let DATA = null;   // forecast.json and parties.json: assets, not a request's data
export async function pageData(env, url) {
  if (DATA) return DATA;
  const get = async p => {
    const r = await env.ASSETS.fetch(new Request(new URL(p, url)));
    if (!r.ok) throw new Error(p + ": " + r.status);
    return r.json();
  };
  const [forecast, parties] = await Promise.all([get(PAGE + "forecast.json"), get(PAGE + "parties.json")]);
  const ctx = B.contextOf(forecast.schema);
  DATA = { forecast, parties, ctx };
  return DATA;
}
export function forgetPageData() { DATA = null; }

// A link's forecast, or null: { state, coalition } from make-state's decoder
// against the page's context (version and context_ref first).
export function decodeLink(v, c, f, D) {
  if (v !== MS.FORMAT || c !== D.forecast.context_ref || !f) return null;
  try { return MS.decode(f, D.ctx); } catch { return null; }
}

// ---------- /s/: counted, then the arrival view ----------

export function shareArrival(url, host, env) {
  const q = new URLSearchParams(url.search);
  const raw = q.get("ch");
  const ch = SHARE_CHANNELS.has(raw) ? raw : "";
  q.delete("ch");
  if (q.has("f")) q.set("from", "1");
  console.log({ event: "arrival", channel: "share", host, via: ch });
  try {
    env.ARRIVALS?.writeDataPoint({ blobs: ["share", host, ch], doubles: [1], indexes: ["share"] });
  } catch {
    // the log line above still records the arrival
  }
  const s = q.toString().replace(/%2C/g, ",");
  return new Response(null, { status: 302, headers: { Location: new URL(PAGE + (s ? "?" + s : ""), url).toString() } });
}

// ---------- the page's tags ----------

const esc = s => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
// The tags the build writes (build_site.SITE_HEAD, build_your_forecast.OG_*)
// and what a shared forecast puts in them. Each is replaced by its attribute,
// never by position; a page missing one is served untouched
// (tests/test_worker_routing.py holds the built page to these).
export const TAGS = ["og:title", "og:description", "og:url", "og:image", "og:image:alt", "twitter:image"];
function setMeta(html, key, value) {
  const attr = key.startsWith("twitter:") ? "name" : "property";
  const re = new RegExp(`(<meta ${attr}="${key.replace(/[:.]/g, "\\$&")}" content=")[^"]*(">)`);
  return re.test(html) ? html.replace(re, (_, a, b) => a + esc(value) + b) : null;
}

export async function sharedPage(request, url, env) {
  const res = await env.ASSETS.fetch(request);
  if (res.status !== 200 || !(res.headers.get("content-type") || "text/html").includes("html")) return res;
  const q = linkQuery(url.search);
  const name = cardName(new URLSearchParams(url.search).get("n"));
  const vn = new URLSearchParams(url.search).has("vs") ? cardName(new URLSearchParams(url.search).get("vn")) : "";
  const title = vn ? (name || "A reader") + " and " + vn : SC.cardTitle(name);
  const image = `${url.origin}${imagePath("link")}?${q}`;
  let html = await res.text();
  const values = {
    "og:title": title,
    "og:description": "A reader's forecast of the Johannesburg council, not the model's. Make yours.",
    "og:url": `${url.origin}${PAGE}?${q}`,
    "og:image": image,
    "og:image:alt": title + ": seats, who governs, and how close it is to our prediction.",
    "twitter:image": image,
  };
  for (const k of TAGS) {
    const next = setMeta(html, k, values[k]);
    if (next == null) return new Response(html, res);   // not the page we built: untouched
    html = next;
  }
  const out = new Response(html, res);
  out.headers.delete("content-length");
  return out;
}

// ---------- the image ----------

function withTimeout(p, ms) {
  let t;
  return Promise.race([p, new Promise((_, no) => { t = setTimeout(() => no(new Error("timeout")), ms); })])
    .finally(() => clearTimeout(t));
}

// sha256 (hex) of the published prediction's seats, one "code=seats" line per
// party in code order: the seat Worker's entry.py prediction_sha256, the same
// bytes. A card is drawn only from an answer measured from this prediction,
// and its cached image is keyed by it.
export async function predictionSha(seats) {
  const text = Object.keys(seats).sort().map(c => c + "=" + seats[c] + "\n").join("");
  const d = await globalThis.crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return [...new Uint8Array(d)].map(b => b.toString(16).padStart(2, "0")).join("");
}

// The seat law's answer and the forecast's badge, checked.
async function cardAnswer(env, D, got) {
  const psha = await predictionSha(D.forecast.start.seats);
  const body = B.entryBody(got.state, D.ctx, { coalition: got.coalition });
  const r = await withTimeout(env.SEATS.fetch("https://seats/v1/card", {
    method: "POST", headers: { "content-type": "application/json" },
    body: JSON.stringify({ seats: seatRequest(body, D.forecast.schema), coalition: got.coalition,
                           draws_sha256: D.forecast.draws_sha256, prediction_sha256: psha }),
  }), SEATS_TIMEOUT_MS);
  if (r.status !== 200) throw new Error("SEATS answered " + r.status);
  const ans = await r.json();
  const seats = checkSeatAnswer(ans, body, D.forecast.schema);   // arithmetic identities, or throws
  const o = ans.outcome;
  if (!o || typeof o.badge !== "string" || !Array.isArray(o.coalition) ||
      ans.draws_sha256 !== D.forecast.draws_sha256) throw new Error("the card answer is incomplete");
  // the badge measured as closeness to this page's published prediction, not
  // an earlier Worker's boldest call: a refused answer is the generic image,
  // never cached
  if (o.measure !== CLOSENESS_MEASURE || ans.prediction_sha256 !== psha) throw new Error("the card answer was not measured from the published prediction");
  return { ...seats, outcome: o };
}

function dataURI(bytes, type) {
  let bin = "";
  const u = new Uint8Array(bytes);
  for (let i = 0; i < u.length; i += 0x8000) bin += String.fromCharCode(...u.subarray(i, i + 0x8000));
  return `data:${type};base64,${btoa(bin)}`;
}

async function cardAssets(env, url, D, codes, badges = []) {
  const logos = {};
  await Promise.all(codes.filter(c => D.parties[c]?.logo).map(async c => {
    const r = await env.ASSETS.fetch(new Request(new URL(`/logos/${c}.png`, url)));
    if (r.ok) logos[c] = dataURI(await r.arrayBuffer(), "image/png");
  }));
  // the owner's badge for each badge's words (src/stamps/, served at /stamps/)
  const stamps = {};
  await Promise.all([...new Set(badges.filter(Boolean))].map(async w => {
    const r = await env.ASSETS.fetch(new Request(new URL(`/${SC.STAMP_DIR}/${SC.badgeFile(w)}`, url)));
    if (r.ok) stamps[w] = SC.stampOf(await r.text());
  }));
  const b = await env.ASSETS.fetch(new Request(new URL("/logo.svg", url)));
  return { logos, badges: stamps, brand: b.ok ? SC.brandOf(await b.text()) : null,
           geom: { W: D.forecast.geometry.W, H: D.forecast.geometry.H, wards: D.forecast.geometry.wards } };
}

const fallback = url => new Response(null, {
  status: 302, headers: { Location: new URL(FALLBACK_IMAGE, url).toString(), "Cache-Control": "no-store" },
});

// The card a link asks for, from checked answers: { svg, sealed }, `sealed`
// when the image's own forecast carries this Worker's seal. Exported for the
// tests, which hand it a fake SEATS.
export async function cardFor(url, env, size) {
  const D = await pageData(env, url);
  const q = new URLSearchParams(url.search);
  const own = decodeLink(q.get("v"), q.get("c"), q.get("f"), D);
  if (!own) throw new Error("the link carries no forecast this page can read");
  if (!env.SEATS) throw new Error("no SEATS binding");
  const party = c => D.parties[c] || { name: c, colour: SC.OTHERS_COLOUR, article: "", logo: false };
  const fields = Object.fromEntries(SEALED_KEYS.map(k => [k, q.get(k) ?? ""]));
  const seal = env.SEAL_KEY && q.has("s") ? await checkSeal(env.SEAL_KEY, fields, q.get("s")) : { sealed: false };
  const made = seal.sealed ? { at: seal.at, sealed: true } : null;
  const specOf = async (got, name) => {
    const a = await cardAnswer(env, D, got);
    return SC.forecastSpec({ name, answer: a, outcome: a.outcome, vote: B.percentOf(got.state, D.ctx, "list"),
      calls: got.state.calls, party, baseline: D.forecast.baseline, election: D.forecast.election, made });
  };
  const friend = q.has("vs") ? decodeLink(q.get("v"), q.get("c"), q.get("vs"), D) : null;
  const A = await specOf(own, cardName(q.get("n")));
  if (friend && size === "link") {
    const Bspec = await specOf(friend, cardName(q.get("vn")) || "a friend");
    if (!A.name) A.name = "A reader";
    const codes = [...new Set([...A.rows, ...Bspec.rows].map(r => r.code))];
    return { svg: SC.duelCardSVG(A, Bspec, await cardAssets(env, url, D, codes), party), sealed: !!made };
  }
  const assets = await cardAssets(env, url, D, A.rows.map(r => r.code), [A.badge]);
  return { svg: size === "story" ? SC.storyCardSVG(A, assets, party) : SC.linkCardSVG(A, assets, party), sealed: !!made };
}

export async function cardImage(url, env, ctx, size) {
  let key = null;
  try {
    const D = await pageData(env, url);
    const cache = globalThis.caches?.default;
    const ps = (await predictionSha(D.forecast.start.seats)).slice(0, 16);
    key = new Request(`${url.origin}${imagePath(size)}?${linkQuery(url.search)}&ds=${D.forecast.draws_sha256}&ps=${ps}`);
    const hit = cache ? await cache.match(key) : null;
    if (hit) return hit;
    const card = await cardFor(url, env, size);
    const { renderPNG } = await import("./og-render.js");
    const res = new Response(await renderPNG(card.svg), {
      headers: { "Content-Type": "image/png", "Cache-Control": imageCache(card.sealed) },
    });
    if (cache) ctx?.waitUntil?.(cache.put(key, res.clone()));
    return res;
  } catch {
    return fallback(url);
  }
}

// ---------- the seal ----------

const json = (data, status = 200) => new Response(JSON.stringify(data), {
  status, headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
});

// The request's body and the link's four sealed fields, as strings.
async function sealBody(request, env, url) {
  if (request.method !== "POST") return { error: json({ error: "POST only" }, 405) };
  let body;
  try { body = await request.json(); } catch { return { error: json({ error: "the body is not JSON" }, 400) }; }
  if (!body || typeof body !== "object") return { error: json({ error: "the body is not an object" }, 400) };
  const D = await pageData(env, url);
  const fields = Object.fromEntries(SEALED_KEYS.map(k => [k, typeof body[k] === "string" ? body[k] : ""]));
  return { D, fields, body };
}

// ---------- entries ----------

// The columns of one entry, in the order ENTRY_INSERT binds them. The table
// (migrations/0001_entries.sql and every later ALTER TABLE in migrations/) has
// exactly these; tests/test_entries.py holds the two to each other both ways.
//   seal_id      the signature half of `s`: the same fields sealed in the same
//                second give the same seal, so a repeat inserts nothing
//   sealed_at    the seal's time, seconds since 1970 (the Worker's clock)
//   label        the name the reader typed (play-state.js cardName), or ""
//   model_ref    forecast.json's model_ref when it was sealed
//   context_ref  the link's `c`: the roster and wards it is over
//   state        the link's `f`, as sealed: with label and sealed_at it
//                rebuilds the seal, so an entry can be checked against SEAL_KEY
//   forecast     the prediction decoded from `f` by the page's own decoder, as
//                JSON in the shape src/score_forecasts.py scores (B.entryBody,
//                checked by worker-api/src/validate.js before it is stored)
//   version      the entry version, make-state.js FORMAT (rows stored before
//                the column existed read 1; the scorer reads only FORMAT)
export const ENTRY_COLUMNS = ["seal_id", "sealed_at", "label", "model_ref", "context_ref", "state", "forecast", "version"];
export const ENTRY_INSERT = "INSERT OR IGNORE INTO entries (" + ENTRY_COLUMNS.join(", ") +
  ") VALUES (" + ENTRY_COLUMNS.map(() => "?").join(", ") + ")";
export const COUNT_SELECT = "SELECT COUNT(*) AS n FROM entries";
// How long the edge keeps the count, in seconds.
export const COUNT_MAX_AGE_S = 60;
const COUNT_PATH = "/entries/1/count";

// One entry's values, in ENTRY_COLUMNS order. The stored body must pass the
// validator on the page's own schema, or the row fails (the seal is kept,
// storeEntry).
export function entryRow(s, fields, got, D) {
  const [t, sig] = s.split(".");
  const body = B.entryBody(got.state, D.ctx, { coalition: got.coalition });
  const checked = validateForecast(body, D.forecast.schema);
  if (!checked.ok) throw new Error("the entry is not valid: " + checked.field + " " + checked.reason);
  return [sig, parseInt(t, 36), fields.n, D.forecast.model_ref, fields.c, fields.f,
          JSON.stringify(checked.value), Number(MS.FORMAT)];
}

// Store one entry. Never throws: the seal is already the reader's. `makeRow`
// builds the row inside the guard, so a forecast that cannot be put in the
// stored shape fails the entry, not the seal. A failure is logged by reason
// alone, with nothing from the entry.
export async function storeEntry(env, makeRow) {
  if (!env.ENTRIES) {
    console.error({ event: "entry", stored: false, reason: "no ENTRIES binding" });
    return;
  }
  let row;
  try {
    row = makeRow();
  } catch {
    console.error({ event: "entry", stored: false, reason: "row failed" });
    return;
  }
  try {
    await env.ENTRIES.prepare(ENTRY_INSERT).bind(...row).run();
  } catch {
    console.error({ event: "entry", stored: false, reason: "insert failed" });
  }
}

// GET /entries/1/count: { count }, kept at the edge COUNT_MAX_AGE_S seconds.
export async function entryCount(request, env, url, ctx) {
  if (request.method !== "GET" && request.method !== "HEAD") return json({ error: "GET only" }, 405);
  if (!env.ENTRIES) return json({ error: "entries are not set up" }, 503);
  const cache = globalThis.caches?.default;
  const key = new Request(url.origin + COUNT_PATH);
  const hit = cache ? await cache.match(key) : null;
  if (hit) return hit;
  let n;
  try {
    n = Number((await env.ENTRIES.prepare(COUNT_SELECT).first()).n);
  } catch {
    console.error({ event: "entry_count", read: false });
    return json({ error: "the count could not be read" }, 503);
  }
  const res = new Response(JSON.stringify({ count: n }), {
    headers: { "Content-Type": "application/json", "Cache-Control": "public, max-age=" + COUNT_MAX_AGE_S },
  });
  if (cache) ctx?.waitUntil?.(cache.put(key, res.clone()));
  return res;
}

// ---------- the rate limit on /seal/1 ----------

// The Workers Rate Limiting binding SEAL_LIMIT (wrangler.toml [[ratelimits]],
// JUDGEMENT-CALLS.md §N9) counts seals per connection. Its key is an HMAC of
// the connection's address under SEAL_KEY (seal.js rateKey), so neither this
// Worker nor the counter holds the address; the counter forgets it after the
// period. An IPv6 connection is counted by its /64 (seal.js rateAddress).
// This is the only place the address is read. Without the binding nothing is
// limited; when the limiter fails, the seal goes ahead and the reason alone
// is logged.
export const RATE_LIMITED = "Too many links sealed from this connection. Try again in a minute.";
async function sealLimited(request, env) {
  if (!env.SEAL_LIMIT) return false;
  try {
    const key = await rateKey(env.SEAL_KEY, request.headers.get("CF-Connecting-IP") || "");
    const { success } = await env.SEAL_LIMIT.limit({ key });
    return !success;
  } catch {
    console.error({ event: "seal_limit", counted: false, reason: "limiter failed" });
    return false;
  }
}

// Sealing needs a forecast this page reads, under a name a card may carry.
// Refused on a preview version (`preview`): a preview could carry a later
// polls_open and would sign with the live key.
export async function seal(request, env, url, { preview = false, ctx = null } = {}) {
  if (!env.SEAL_KEY) return json({ error: "sealing is not set up" }, 503);
  if (preview) return json({ error: "sealing is refused on a preview version" }, 403);
  if (request.method === "POST" && await sealLimited(request, env)) return json({ error: RATE_LIMITED }, 429);
  const got = await sealBody(request, env, url);
  if (got.error) return got.error;
  const read = decodeLink(got.fields.v, got.fields.c, got.fields.f, got.D);
  if (!read) return json({ error: "the link carries no forecast this page can read" }, 400);
  const fields = got.fields;
  if (fields.n !== "" && cardName(fields.n) !== fields.n) return json({ error: "the name is not one a card can carry" }, 400);
  const now = Date.now();
  const opens = Date.parse(got.D.forecast.election.polls_open);
  if (!(now < opens)) return json({ error: "Polls are open: a forecast can no longer be sealed." }, 403);
  const s = await makeSeal(env.SEAL_KEY, got.fields, now);
  const stored = storeEntry(env, () => entryRow(s, fields, read, got.D));
  if (ctx?.waitUntil) ctx.waitUntil(stored); else await stored;
  return json({ s });
}

// The signature is checked first, on the fields as the link carries them:
// a link sealed under an earlier context_ref (a new roster or wards) or entry
// version is still answered sealed, and when. `readable` says separately
// whether this page can read its forecast.
export async function sealCheck(request, env, url) {
  if (!env.SEAL_KEY) return json({ error: "sealing is not set up" }, 503);
  const got = await sealBody(request, env, url);
  if (got.error) return got.error;
  const r = await checkSeal(env.SEAL_KEY, got.fields, got.body.s);
  const opens = Date.parse(got.D.forecast.election.polls_open);
  return json({ sealed: r.sealed, at: r.sealed ? new Date(r.at).toISOString() : null,
                before_polls: r.sealed ? r.at < opens : false,
                readable: !!decodeLink(got.fields.v, got.fields.c, got.fields.f, got.D) });
}

// ---------- routing ----------

// The response for a share route on a host that serves the Johannesburg build
// from the root, or null when the path is not one. `preview`: a workers.dev
// host (src/worker.js), where /seal/1 is refused and /seal/1/check answers.
export async function shareRoute(request, url, host, env, ctx, { preview = false } = {}) {
  const path = url.pathname;
  if (path === "/s" || path === "/s/") return shareArrival(url, host, env);
  if (path === "/seal/1") return seal(request, env, url, { preview, ctx });
  if (path === COUNT_PATH) return entryCount(request, env, url, ctx);
  if (path === "/seal/1/check") return sealCheck(request, env, url);
  const img = IMAGE.exec(path);
  if (img && Number(img[1]) > 0 && Number(img[1]) < CARD_VERSION)
    return new Response(null, { status: 301, headers: { Location: new URL(imagePath(img[2]) + url.search, url).toString() } });
  if (img && Number(img[1]) === CARD_VERSION)
    return request.method === "GET" || request.method === "HEAD" ? cardImage(url, env, ctx, img[2]) : json({ error: "GET only" }, 405);
  if ((path === PAGE || path === PAGE + "index.html") && new URLSearchParams(url.search).has("f")) return sharedPage(request, url, env);
  return null;
}
