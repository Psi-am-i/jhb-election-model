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
 * stays at the root and is served to every host unchanged.
 *
 * Every *.workers.dev host serves the Johannesburg build from the root, and
 * every response it sends carries X-Robots-Tag: noindex, nofollow. That covers
 * the Worker's own workers.dev URL and every Version URL printed by
 * `wrangler versions upload`, which is the UAT path (docs/DEPLOY-UAT.md).
 * Without this branch those hosts fell through to the city-directory lookup
 * and showed the portal.
 *
 * Channel short paths (/go, /x, /li, /fb, /ig, /g; any case, optional trailing
 * slash) on the Johannesburg host and on workers.dev hosts answer 302 to the
 * home page and write one JSON line to the Worker log:
 *   {"event":"arrival","channel":"<name>","host":"<hostname>"}
 * Cloudflare Web Analytics does not record query strings, so UTM tags are
 * invisible there; Workers Logs ([observability] in wrangler.toml) counts these
 * lines instead. Version URLs are not visible in Workers Logs, so UAT clicks
 * are never counted.
 */

// NB: request "/portal", not "/portal.html" — the assets layer 307s the
// extension away, which would move the visitor off the apex URL.
const PORTAL_HOSTS = new Set(["whysoserious.city", "www.whysoserious.city"]);

// Cities served from the asset root rather than a subdirectory. Johannesburg
// shipped before the portal existed and its URLs are already in the wild.
const ROOT_CITIES = new Set(["joburg"]);

// Paths that are shared by every city and must never be prefixed.
const SHARED = [
  "/logos/", "/share.jpg", "/robots.txt", "/favicon", "/_headers", "/sitemap",
];

const NOINDEX = "noindex, nofollow";

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

function arrival(url, host, channel) {
  console.log(JSON.stringify({ event: "arrival", channel, host }));
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
      const res = channel ? arrival(url, host, channel) : await env.ASSETS.fetch(request);
      const out = new Response(res.body, res);
      out.headers.set("X-Robots-Tag", NOINDEX);
      return out;
    }

    if (PORTAL_HOSTS.has(host)) {
      if (path === "/" || path === "/index.html") {
        return env.ASSETS.fetch(new Request(new URL("/portal", url), request));
      }
      return env.ASSETS.fetch(request);
    }

    const sub = host.split(".")[0];

    if (ROOT_CITIES.has(sub)) {
      const channel = channelOf(path);
      if (channel) return arrival(url, host, channel);
    }

    // Johannesburg, and anything shared, is served straight from the root.
    if (ROOT_CITIES.has(sub) || SHARED.some((p) => path.startsWith(p))) {
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
