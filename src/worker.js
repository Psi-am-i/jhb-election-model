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

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const host = url.hostname.toLowerCase();
    const path = url.pathname;

    if (PORTAL_HOSTS.has(host)) {
      if (path === "/" || path === "/index.html") {
        return env.ASSETS.fetch(new Request(new URL("/portal", url), request));
      }
      return env.ASSETS.fetch(request);
    }

    const sub = host.split(".")[0];

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
