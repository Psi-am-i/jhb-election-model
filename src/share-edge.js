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
//   /og/1/link.png?<link>    that image, drawn here: share-card.js's card,
//   /og/1/story.png?<link>   rasterised by resvg (src/og-render.js), cached at
//                            the edge by the link and the published draws'
//                            hash. Any failure answers 302 to /og.png.
//   POST /seal/1             seal a link's state (src/seal.js); refused from
//                            the moment polls open
//   POST /seal/1/check       is this link sealed, and when
//
// SEATS AND THE CHANCE COME ONLY FROM PYTHON (DESIGN §3): the image's seats
// are the seat law's for the link's picks and its chance the published
// forecast's for that outcome, both from the seat Worker's /v1/card
// (worker-api/seats-py, reached through the service binding env.SEATS). The
// link's own figures are never read for the image, so a forged link cannot
// put on an image from this domain a seat count the law would not give. With
// no SEATS binding, or any answer but a checked 200, the image is the generic
// one.
//
// NOTHING ABOUT A PERSON IS STORED. The image lives in the edge cache only,
// which evicts on its own; the name on it is text the reader put in a link
// they chose to share. No URL, name or forecast is logged.

import * as MS from "../interactive/js/make-state.js";
import * as B from "../interactive/js/builder-state.js";
import { cleanName, NAME_MAX } from "../interactive/js/play-state.js";
import * as SC from "../interactive/js/share-card.js";
import { seatRequest, checkSeatAnswer } from "../worker-api/src/seats.js";
import { BLOCKED_NAME_PATTERNS } from "../worker-api/src/blocklist.js";
import { makeSeal, checkSeal, SEALED_KEYS } from "./seal.js";

// The keys of a shared forecast's link, in the order the image's address
// writes them: section 2's state (make-state.js), the name, the seal, and the
// friend's forecast and name on a return link (yf-url.js).
export const LINK_KEYS = ["v", "c", "f", "n", "s", "vs", "vn"];
// The share buttons that may be counted (make-share.js sets `ch`).
export const SHARE_CHANNELS = new Set(["wa", "x", "copy", "native"]);
export const FALLBACK_IMAGE = "/og.png";
export const SEATS_TIMEOUT_MS = 3000;
const PAGE = "/your-forecast/";
const IMAGE = /^\/og\/1\/(link|story)\.png$/;

// ---------- the link ----------

// The link's own keys, in LINK_KEYS order, as one query string.
export function linkQuery(search) {
  const q = new URLSearchParams(search), out = new URLSearchParams();
  for (const k of LINK_KEYS) if (q.has(k)) out.set(k, q.get(k));
  return out.toString();
}

// The name as a card may print it, or "" (cleaned by the page's one rule,
// refused whole when too long or when it would pass for the site).
export function cardName(raw) {
  if (raw == null || raw.length > NAME_MAX) return "";
  const n = cleanName(raw);
  const folded = n.normalize("NFKC");
  return BLOCKED_NAME_PATTERNS.some(p => p.test(folded)) ? "" : n;
}

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
  const image = `${url.origin}/og/1/link.png?${q}`;
  let html = await res.text();
  const values = {
    "og:title": title,
    "og:description": "A reader's forecast of the Johannesburg council, not the model's. Make yours.",
    "og:url": `${url.origin}${PAGE}?${q}`,
    "og:image": image,
    "og:image:alt": title + ": seats, who governs, and the chance we give the outcome.",
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

// The seat law's answer and the outcome's chance for one forecast, checked.
async function cardAnswer(env, D, got) {
  const body = B.forecastBody(got.state, D.ctx, { coalition: got.coalition });
  const r = await withTimeout(env.SEATS.fetch("https://seats/v1/card", {
    method: "POST", headers: { "content-type": "application/json" },
    body: JSON.stringify({ seats: seatRequest(body, D.forecast.schema), coalition: got.coalition,
                           draws_sha256: D.forecast.draws_sha256 }),
  }), SEATS_TIMEOUT_MS);
  if (r.status !== 200) throw new Error("SEATS answered " + r.status);
  const ans = await r.json();
  const seats = checkSeatAnswer(ans, body, D.forecast.schema);   // arithmetic identities, or throws
  const o = ans.outcome;
  if (!o || typeof o.text !== "string" || typeof o.badge !== "string" || !Array.isArray(o.coalition) ||
      ans.draws_sha256 !== D.forecast.draws_sha256) throw new Error("the card answer is incomplete");
  return { ...seats, outcome: o };
}

function dataURI(bytes, type) {
  let bin = "";
  const u = new Uint8Array(bytes);
  for (let i = 0; i < u.length; i += 0x8000) bin += String.fromCharCode(...u.subarray(i, i + 0x8000));
  return `data:${type};base64,${btoa(bin)}`;
}

async function cardAssets(env, url, D, codes) {
  const logos = {};
  await Promise.all(codes.filter(c => D.parties[c]?.logo).map(async c => {
    const r = await env.ASSETS.fetch(new Request(new URL(`/logos/${c}.png`, url)));
    if (r.ok) logos[c] = dataURI(await r.arrayBuffer(), "image/png");
  }));
  const b = await env.ASSETS.fetch(new Request(new URL("/logo.svg", url)));
  return { logos, brand: b.ok ? SC.brandOf(await b.text()) : null,
           geom: { W: D.forecast.geometry.W, H: D.forecast.geometry.H, wards: D.forecast.geometry.wards } };
}

const fallback = url => new Response(null, {
  status: 302, headers: { Location: new URL(FALLBACK_IMAGE, url).toString(), "Cache-Control": "no-store" },
});

// The SVG of the card a link asks for, from checked answers; exported for the
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
    return SC.forecastSpec({ name, answer: a, outcome: a.outcome, vote: B.percentOf(got.state, D.ctx),
      calls: got.state.calls, party, baseline: D.forecast.baseline, election: D.forecast.election, made });
  };
  const friend = q.has("vs") ? decodeLink(q.get("v"), q.get("c"), q.get("vs"), D) : null;
  const A = await specOf(own, cardName(q.get("n")));
  if (friend && size === "link") {
    const Bspec = await specOf(friend, cardName(q.get("vn")) || "a friend");
    if (!A.name) A.name = "A reader";
    const codes = [...new Set([...A.rows, ...Bspec.rows].map(r => r.code))];
    return SC.duelCardSVG(A, Bspec, await cardAssets(env, url, D, codes), party);
  }
  const assets = await cardAssets(env, url, D, A.rows.map(r => r.code));
  return size === "story" ? SC.storyCardSVG(A, assets, party) : SC.linkCardSVG(A, assets, party);
}

export async function cardImage(url, env, ctx, size) {
  let key = null;
  try {
    const D = await pageData(env, url);
    const cache = globalThis.caches?.default;
    key = new Request(`${url.origin}/og/1/${size}.png?${linkQuery(url.search)}&ds=${D.forecast.draws_sha256}`);
    const hit = cache ? await cache.match(key) : null;
    if (hit) return hit;
    const svg = await cardFor(url, env, size);
    const { renderPNG } = await import("./og-render.js");
    const res = new Response(await renderPNG(svg), {
      headers: { "Content-Type": "image/png", "Cache-Control": "public, max-age=31536000, immutable" },
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

async function sealBody(request, env, url) {
  if (request.method !== "POST") return { error: json({ error: "POST only" }, 405) };
  let body;
  try { body = await request.json(); } catch { return { error: json({ error: "the body is not JSON" }, 400) }; }
  if (!body || typeof body !== "object") return { error: json({ error: "the body is not an object" }, 400) };
  const D = await pageData(env, url);
  const fields = Object.fromEntries(SEALED_KEYS.map(k => [k, typeof body[k] === "string" ? body[k] : ""]));
  if (!decodeLink(fields.v, fields.c, fields.f, D)) return { error: json({ error: "the link carries no forecast this page can read" }, 400) };
  if (fields.n !== "" && cardName(fields.n) !== fields.n) return { error: json({ error: "the name is not one a card can carry" }, 400) };
  return { D, fields, body };
}

export async function seal(request, env, url) {
  if (!env.SEAL_KEY) return json({ error: "sealing is not set up" }, 503);
  const got = await sealBody(request, env, url);
  if (got.error) return got.error;
  const now = Date.now();
  const opens = Date.parse(got.D.forecast.election.polls_open);
  if (!(now < opens)) return json({ error: "Polls are open: a forecast can no longer be sealed." }, 403);
  return json({ s: await makeSeal(env.SEAL_KEY, got.fields, now) });
}

export async function sealCheck(request, env, url) {
  if (!env.SEAL_KEY) return json({ error: "sealing is not set up" }, 503);
  const got = await sealBody(request, env, url);
  if (got.error) return got.error;
  const r = await checkSeal(env.SEAL_KEY, got.fields, got.body.s);
  const opens = Date.parse(got.D.forecast.election.polls_open);
  return json({ sealed: r.sealed, at: r.sealed ? new Date(r.at).toISOString() : null,
                before_polls: r.sealed ? r.at < opens : false });
}

// ---------- routing ----------

// The response for a share route on a host that serves the Johannesburg build
// from the root, or null when the path is not one.
export async function shareRoute(request, url, host, env, ctx) {
  const path = url.pathname;
  if (path === "/s" || path === "/s/") return shareArrival(url, host, env);
  if (path === "/seal/1") return seal(request, env, url);
  if (path === "/seal/1/check") return sealCheck(request, env, url);
  const img = IMAGE.exec(path);
  if (img) return request.method === "GET" || request.method === "HEAD" ? cardImage(url, env, ctx, img[1]) : json({ error: "GET only" }, 405);
  if ((path === PAGE || path === PAGE + "index.html") && new URLSearchParams(url.search).has("f")) return sharedPage(request, url, env);
  return null;
}
