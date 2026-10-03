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
 * Pages that moved (MOVED) answer 301 to their new address, query kept, on the
 * Johannesburg host and on workers.dev hosts, wherever the Johannesburg build
 * is served from the root, and log nothing. /about merged into /methodology in
 * the owner's sweep of 2026-10-03. A moved page is matched exactly, with or
 * without .html or a trailing slash, so /aboutx still reaches the assets.
 * Sections that moved inside a page (old article anchors) cannot be redirected
 * here: a fragment never reaches the server, so js/forward.js on the old page
 * sends them on.
 *
 * Each arrival is also written as one Workers Analytics Engine data point
 * (env.ARRIVALS, [[analytics_engine_datasets]] in wrangler.toml):
 *   blobs [channel, host], doubles [1], indexes [channel]
 * Analytics Engine keeps it three months against Workers Logs' seven days.
 * Version URLs have the binding too, so UAT clicks are written under their
 * workers.dev host; the count in docs/DEPLOY-UAT.md filters on host.
 */

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

// Johannesburg pages that moved: old path -> new path.
const MOVED = new Map([
  ["/about", "/methodology"],
]);

// "/about", "/about.html", "/about/" -> "/methodology"; anything else -> undefined.
function movedTo(path) {
  const m = /^(\/[a-z0-9-]+)(?:\.html|\/)?$/.exec(path);
  return m ? MOVED.get(m[1]) : undefined;
}

function moved(url, to) {
  return new Response(null, {
    status: 301,
    headers: { Location: new URL(to + url.search, url).toString() },
  });
}

// Short path (lowercase, no slashes) -> channel name in the arrival log.
const CHANNELS = new Map([
  ["go", "billboard"],
  ["x", "x"],
  ["li", "linkedin"],
  ["fb", "facebook"],
  ["ig", "instagram"],
  ["g", "google_ads"],
]);

function isPreview(host) {
  return host.endsWith(".workers.dev");
}

// "/GO", "/go/" -> "billboard"; anything else -> undefined.
function channelOf(path) {
  const m = /^\/([a-z]+)\/?$/.exec(path.toLowerCase());
  return m ? CHANNELS.get(m[1]) : undefined;
}

function arrival(url, host, channel, env) {
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
    headers: { Location: new URL("/", url).toString() },
  });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const host = url.hostname.toLowerCase();
    const path = url.pathname;

    if (isPreview(host)) {
      const channel = channelOf(path);
      const to = movedTo(path);
      const res = channel ? arrival(url, host, channel, env)
        : to ? moved(url, to) : await env.ASSETS.fetch(request);
      const out = new Response(res.body, res);
      out.headers.set("X-Robots-Tag", NOINDEX);
      return out;
    }

    if (PORTAL_HOSTS.has(host)) {
      // A short path on the apex or www goes to the Johannesburg host, which
      // logs the arrival; logging here as well would count it twice.
      if (channelOf(path)) {
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
