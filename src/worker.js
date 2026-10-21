/**
 * Hostname routing for whysoserious.city.
 *
 *   whysoserious.city / www   -> the portal (one card per city)
 *   joburg.whysoserious.city  -> the Johannesburg build, which lives at the
 *                                asset root for historical reasons
 *   <city>.whysoserious.city  -> that city's build under /<city>/
 *
 * Static assets alone cannot rewrite by host, hence a Worker. Everything it
 * does is a path rewrite in front of the same asset bundle — there is no
 * per-city deploy and no duplicated content.
 *
 * Anything shared across cities (logos, share images, robots.txt, _headers)
 * stays at the root and is served to every host unchanged. So do /support and
 * /privacy, which only the Johannesburg build produces: the footer links them
 * relatively, so on <city>.whysoserious.city they must not be city-prefixed.
 * Those two match exactly (with or without .html), not as prefixes, so
 * /supporters on a city host still goes to the city directory.
 *
 * Every *.workers.dev host serves the Johannesburg build from the root, and
 * every response it sends carries X-Robots-Tag: noindex, nofollow. That covers
 * the Worker's own workers.dev URL and every Version URL printed by
 * `wrangler versions upload`, which is the UAT path (docs/DEPLOY-UAT.md).
 * Without this branch those hosts fell through to the city-directory lookup
 * and showed the portal.
 *
 * Channel short paths (/go, /x, /li, /fb, /ig, /g; any case, optional trailing
 * slash) on the apex and www answer 302 to the same path and query on
 * joburg.whysoserious.city, and log nothing. On the Johannesburg host and on
 * workers.dev hosts they answer 302 to the home page and log one object, which
 * Workers Logs indexes as fields:
 *   {event: "arrival", channel: "<name>", host: "<hostname>"}
 * Cloudflare Web Analytics does not record query strings, so UTM tags are
 * invisible there; Workers Logs ([observability] in wrangler.toml) counts these
 * lines instead. Version URLs are not visible in Workers Logs, so UAT clicks
 * never appear there.
 *
 * Pages that moved (MOVED) answer 301 to their new address on the Johannesburg
 * host and on workers.dev hosts, wherever the Johannesburg build is served
 * from the root, with the query string kept, so a link shared from the old
 * page opens the same settings on the new one. They log nothing. Each row says
 * which spellings of the old path move (owner's sweep, 2026-10-03):
 *   - /about merged into /methodology. It is matched exactly, with or without
 *     .html or a trailing slash, so /aboutx and /about/x still reach the
 *     assets. Sections that moved inside a page (old article anchors) cannot be
 *     redirected here: a fragment never reaches the server, so js/forward.js on
 *     the old page sends them on.
 *   - /play/ and /make/ became the two sections of /your-forecast/; /make/
 *     lands on its section, #break. The directory and anything under it moves,
 *     in any case: both were single pages and their files are gone.
 *
 * Each arrival is also written as one Workers Analytics Engine data point
 * (env.ARRIVALS, [[analytics_engine_datasets]] in wrangler.toml):
 *   blobs [channel, host], doubles [1], indexes [channel]
 * Analytics Engine keeps it three months against Workers Logs' seven days.
 * Version URLs have the binding too, so UAT clicks are written under their
 * workers.dev host; the count in docs/DEPLOY-UAT.md filters on host.
 *
 * A reader's shared forecast (src/share-edge.js, audits/2026-10-03-share-design)
 * has five routes on the Johannesburg host and on workers.dev hosts: /s/ (the
 * share sheet's links: counted as channel "share", with the button used, then
 * 302 to the arrival view on /your-forecast/), /your-forecast/ with a forecast
 * in its query (its og: tags rewritten to the forecast's own image),
 * /og/6/link.png and /og/6/story.png (that image, drawn here from the seat
 * Worker's answer over the SEATS service binding, its address versioned by
 * share-edge.js CARD_VERSION, an earlier version's answering 301; /og.png when anything
 * fails), POST /seal/1 and /seal/1/check (sealed links, under the Worker
 * secret SEAL_KEY; each seal stored as one entry in the D1 database ENTRIES,
 * /seal/1 rate-limited by SEAL_LIMIT), and GET /entries/1/count (how many
 * entries). Preview versions refuse /seal/1: they share the live
 * SEAL_KEY, and one built with a later polls_open would otherwise sign links
 * the live site accepts after polls open. They still check seals. The share
 * data point is
 *   blobs ["share", host, button], doubles [1], indexes ["share"]
 * On the apex and www, /s/ answers 302 to the same path and query on the
 * Johannesburg host, like a channel short path.
 */

import { shareRoute } from "./share-edge.js";

// NB: request "/portal", not "/portal.html" — the assets layer 307s the
// extension away, which would move the visitor off the apex URL.
const PORTAL_HOSTS = new Set(["whysoserious.city", "www.whysoserious.city"]);

// Where the portal hosts send a channel short path.
const JOBURG_HOST = "joburg.whysoserious.city";

// Cities served from the asset root rather than a subdirectory. Johannesburg
// shipped before the portal existed and its URLs are already in the wild.
const ROOT_CITIES = new Set(["joburg"]);

// Paths that are shared by every city and must never be prefixed.
const SHARED = [
  "/logos/", "/share.jpg", "/robots.txt", "/favicon", "/_headers", "/sitemap",
];

// Pages shared by every city, matched exactly. Built by Johannesburg only.
const SHARED_PAGES = new Set([
  "/support", "/support.html", "/privacy", "/privacy.html",
]);

const NOINDEX = "noindex, nofollow";

// Johannesburg pages that moved: [old path, new path, fragment]. Add a row
// here to move a page; the query string is always kept.
const MOVED = [
  [/^\/about(?:\.html|\/)?$/, "/methodology", ""],
  [/^\/play(?:\/.*)?$/i, "/your-forecast/", ""],
  [/^\/make(?:\/.*)?$/i, "/your-forecast/", "#break"],
];

// "/about.html" -> ["/methodology", ""]; "/Make/index.html" ->
// ["/your-forecast/", "#break"]; anything else -> undefined.
function movedTo(path) {
  const row = MOVED.find(([old]) => old.test(path));
  return row ? row.slice(1) : undefined;
}

function moved(url, to) {
  const [path, hash] = to;
  return new Response(null, {
    status: 301,
    headers: { Location: new URL(path + url.search + hash, url).toString() },
  });
}

// The forecast page's share image is named by its content (src/og_pages.py),
// so an address a chat app kept from an earlier build no longer names a file.
// It moves like the pages above: to the image /forecast names now (its
// og:image), query kept. A name the assets serve, or a page that names none,
// is left to the asset layer. Johannesburg hosts only. Returns [path, ""] like
// a MOVED row, or undefined.
const FORECAST_IMAGE = /^\/og-page\/forecast-[a-p]{12}\.png$/;
async function staleForecastImage(url, env) {
  if (!FORECAST_IMAGE.test(url.pathname)) return undefined;
  if ((await env.ASSETS.fetch(new Request(url, { method: "HEAD" }))).status !== 404) return undefined;
  const page = await env.ASSETS.fetch(new Request(new URL("/forecast", url)));
  const m = page.ok ? /<meta property="og:image" content="([^"]+)"/.exec(await page.text()) : null;
  const now = m ? new URL(m[1]).pathname : "";
  return FORECAST_IMAGE.test(now) ? [now, ""] : undefined;
}

// Short path (lowercase, no slashes) -> channel name in the arrival log. Each
// lands on the home page; its twin ending in "p" lands on Your Forecast and
// logs "<channel>_prediction" (owner, 2026-10-22;
// audits/2026-10-22-short-links/BRIEF.md). This table is the only list.
const CHANNELS = new Map([
  ["go", "billboard"],
  ["x", "x"],
  ["li", "linkedin"],
  ["fb", "facebook"],
  ["ig", "instagram"],
  ["g", "google_ads"],
  ["e", "email"],
  ["r", "reddit"],
  ["yt", "youtube"],
  ["fm", "radio"],
]);
const PREDICTION = "/your-forecast/";

function isPreview(host) {
  return host.endsWith(".workers.dev");
}

// "/GO", "/go/" -> {name: "billboard", to: "/"}; "/gop" -> {name:
// "billboard_prediction", to: "/your-forecast/"}; anything else -> undefined.
function channelOf(path) {
  const m = /^\/([a-z]+)\/?$/.exec(path.toLowerCase());
  if (!m) return undefined;
  if (CHANNELS.has(m[1])) return { name: CHANNELS.get(m[1]), to: "/" };
  const base = m[1].endsWith("p") ? m[1].slice(0, -1) : "";
  return CHANNELS.has(base) ? { name: `${CHANNELS.get(base)}_prediction`, to: PREDICTION } : undefined;
}

function arrival(url, host, ch, env) {
  const channel = ch.name;
  // An object, not a JSON string: Workers Logs indexes an object's keys as
  // fields (filter event, group by channel); a string is one message field.
  console.log({ event: "arrival", channel, host });
  // The same arrival as one Analytics Engine data point, kept three months
  // (Workers Logs keeps seven days). Channel and hostname only, nothing about
  // the visitor. Not awaited: writeDataPoint is non-blocking. A missing
  // binding or a failed write must never cost the visitor the redirect.
  try {
    env.ARRIVALS?.writeDataPoint({ blobs: [channel, host], doubles: [1], indexes: [channel] });
  } catch {
    // the log line above still records the arrival
  }
  return new Response(null, {
    status: 302,
    headers: { Location: new URL(ch.to, url).toString() },
  });
}

// "/s", "/s/": the share sheet's links (src/share-edge.js).
const isShare = path => path === "/s" || path === "/s/";

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const host = url.hostname.toLowerCase();
    const path = url.pathname;

    if (isPreview(host)) {
      const channel = channelOf(path);
      const to = movedTo(path) ?? await staleForecastImage(url, env);
      const res = channel ? arrival(url, host, channel, env)
        : to ? moved(url, to)
          : (await shareRoute(request, url, host, env, ctx, { preview: true })) ?? await env.ASSETS.fetch(request);
      const out = new Response(res.body, res);
      out.headers.set("X-Robots-Tag", NOINDEX);
      return out;
    }

    if (PORTAL_HOSTS.has(host)) {
      // A short path on the apex or www goes to the Johannesburg host, which
      // logs the arrival; logging here as well would count it twice.
      if (channelOf(path) || isShare(path)) {
        return new Response(null, {
          status: 302,
          headers: { Location: `https://${JOBURG_HOST}${path}${url.search}` },
        });
      }
      if (path === "/" || path === "/index.html") {
        return env.ASSETS.fetch(new Request(new URL("/portal", url), request));
      }
      return env.ASSETS.fetch(request);
    }

    const sub = host.split(".")[0];

    if (ROOT_CITIES.has(sub)) {
      const channel = channelOf(path);
      if (channel) return arrival(url, host, channel, env);
      const to = movedTo(path);
      if (to) return moved(url, to);
      const stale = await staleForecastImage(url, env);
      if (stale) return moved(url, stale);
      const shared = await shareRoute(request, url, host, env, ctx);
      if (shared) return shared;
    }

    // Johannesburg, and anything shared, is served straight from the root.
    if (ROOT_CITIES.has(sub) || SHARED_PAGES.has(path) ||
        SHARED.some((p) => path.startsWith(p))) {
      return env.ASSETS.fetch(request);
    }

    // Any other subdomain is a city directory. If that city has not been
    // built yet, fall back to the portal rather than a bare 404.
    const prefixed = new URL(`/${sub}${path === "/" ? "/index.html" : path}`, url);
    const hit = await env.ASSETS.fetch(new Request(prefixed, request));
    if (hit.status !== 404) return hit;
    return env.ASSETS.fetch(new Request(new URL("/portal", url), request));
  },
};
