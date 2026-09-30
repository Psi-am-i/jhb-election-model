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
 * Staging (wrangler.staging.toml sets STAGING = "1"), every *.workers.dev
 * host (including `wrangler versions upload` preview URLs) and the staging
 * custom domain serve the Johannesburg build from the root, and every response
 * they send carries X-Robots-Tag: noindex, nofollow. Without this branch those
 * hosts fell through to the city-directory lookup and showed the portal.
 *
 * /go on the Johannesburg site (live and staging) is the billboard short URL:
 * a 302 to the home page with the campaign's UTM parameters.
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

// Hosts that are not the public site. They serve Johannesburg and are never
// indexed. The staging Worker is caught by env.STAGING whatever its hostname;
// this set also catches the staging domain if it is ever routed to live.
const STAGING_HOSTS = new Set(["uat-joburg.whysoserious.city"]);
const NOINDEX = "noindex, nofollow";

// Billboard short URL (DOOH campaign, 2026 local government election).
const GO_PATHS = new Set(["/go", "/go/"]);
const GO_TARGET = "/?utm_source=billboard&utm_medium=dooh&utm_campaign=lge2026";

function isStaging(host, env) {
  return (env && env.STAGING === "1") || host.endsWith(".workers.dev") ||
    STAGING_HOSTS.has(host);
}

function go(url) {
  return new Response(null, {
    status: 302,
    headers: { Location: new URL(GO_TARGET, url).toString() },
  });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const host = url.hostname.toLowerCase();
    const path = url.pathname;

    if (isStaging(host, env)) {
      const res = GO_PATHS.has(path) ? go(url) : await env.ASSETS.fetch(request);
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

    if (ROOT_CITIES.has(sub) && GO_PATHS.has(path)) return go(url);

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
