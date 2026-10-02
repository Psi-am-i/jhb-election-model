"""`src/worker.js` hostname routing: live unchanged, workers.dev and Version
URLs serve Joburg unindexed, channel short paths redirect and log (2026-10-01).

UAT is a Version URL of the live Worker (`wrangler versions upload`, then
`versions deploy <id>@100%`; docs/DEPLOY-UAT.md). Before this change every
`*.workers.dev` host, Version URLs included, fell through to the city-directory
lookup (first hostname label as a city slug), found nothing, and served the
portal.

The worker is run for real under node, with `env.ASSETS` stubbed by a fake that
records every URL it is asked for and answers 200 for a fixed asset set, 307
with a Location for an extension URL, 304 for a conditional request, and 404
otherwise (so the portal fallback is exercised). `console.log` is captured per
request. Detectors, each a function returning a list of problems:

* `live_diffs`        — DIFFERENTIAL against the worker as it was at BASELINE,
                        over every live hostname in `wrangler.toml` plus built
                        and unbuilt city subdomains, times a path set. Compares
                        status, headers, body, every asset URL requested and
                        every log line. Channel paths are excluded on the
                        Joburg host and the two portal hosts; on other cities
                        they must behave exactly as before.
* `preview_problems`  — every workers.dev host serves the requested path from
                        the asset root, logs nothing, and carries X-Robots-Tag.
* `passthrough_problems` — a 307 with Location and a 304 from ASSETS keep their
                        status and headers through the noindex wrap.
* `channel_problems`  — every channel path, in any case and with or without a
                        trailing slash, answers 302 to the home page, fetches
                        nothing and logs exactly one arrival object (an object,
                        so Workers Logs indexes its keys as fields).
* `portal_channel_problems` — on the apex and www, every channel path answers
                        302 to the same path and query on the Joburg host,
                        fetches nothing and logs nothing (the Joburg host logs
                        the arrival once).
* `shared_page_problems` — /support and /privacy (and their .html forms) are
                        served from the asset root on every host: Joburg, the
                        portal hosts, built and unbuilt cities and workers.dev
                        (2026-10-02; the footer links them relatively). The
                        live differential runs them on Joburg and the portal
                        hosts only, where they must behave as before; on other
                        cities the baseline city-prefixed them. Near misses
                        (/supporters, /support/x, /privacyx) run everywhere in
                        the differential, so the match is shown to be exact.
* `config_problems`   — `wrangler.toml` states workers_dev, preview_urls,
                        [observability], invocation_logs = false and the
                        ARRIVALS Analytics Engine binding where wrangler
                        reads them.

`env.ARRIVALS` is a fake Analytics Engine binding recording every data point
(`points` per request). `channel_problems` wants exactly one point per arrival,
matching the log object; every other detector wants none. `resilience_problems`
runs the channel paths with the binding absent and with a binding that throws:
the redirect and the log line must survive both.

Each is shown to fire on a constructed violation and to be quiet on the real
source (CLAUDE.md §4).
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT, skip  # noqa: E402

WORKER = ROOT / "src" / "worker.js"
WRANGLER = ROOT / "wrangler.toml"
#: The last worker.js with no preview branch and no short paths. Live
#: behaviour outside the Joburg channel paths must equal this one's.
BASELINE = "749d5ec"

NOINDEX = "noindex, nofollow"

#: Short path -> channel name in the arrival log (the cross-lane decision of
#: 2026-10-01). Ad and post links use these paths.
CHANNELS = {"go": "billboard", "x": "x", "li": "linkedin", "fb": "facebook",
            "ig": "instagram", "g": "google_ads"}
#: Every spelling that must count: lower, upper, mixed, trailing slash, and a
#: query string such as the gclid Google Ads appends.
CHANNEL_PATHS = {f"/{v}": n for k, n in CHANNELS.items()
                 for v in (k, k + "/", k.upper(), k.upper() + "/",
                           k[0].upper() + k[1:])}
CHANNEL_PATHS.update({"/g?gclid=abc": "google_ads", "/Go?x=1": "billboard"})

#: What the fake asset layer holds. Paths with no extension stand for what the
#: real layer serves at an extensionless URL.
ASSETS = ["/", "/index.html", "/forecast", "/about", "/portal",
          "/logos/party.png", "/robots.txt", "/share.jpg",
          "/tshwane/index.html", "/tshwane/forecast", "/support", "/privacy"]
#: The real layer 307s an .html URL to its extensionless form.
REDIRECTS = {"/about.html": "/about", "/support.html": "/support",
             "/privacy.html": "/privacy"}
#: Pages every host serves from the asset root, and what ASSETS answers.
SHARED_PAGES = {"/support": 200, "/privacy": 200, "/support.html": 307,
                "/privacy.html": 307}

#: Near misses: none of these is a channel path on any host.
LIVE_PATHS = ["/", "/index.html", "/forecast", "/about.html", "/nope",
              "/logos/party.png", "/robots.txt", "/share.jpg", "/?x=1",
              "/go/x", "/gone", "/go.html", "/xx", "/gg", "/g/x", "/G/x",
              "/li.html", "/fbx", "/ig/ig", "//go",
              "/supporters", "/support/x", "/privacyx", "/Support"]

DRIVER = r"""
import { readFileSync } from "node:fs";
const [workerPath, casesPath] = process.argv.slice(2);
const worker = (await import("file://" + workerPath)).default;
const { assets, redirects, cases } = JSON.parse(readFileSync(casesPath, "utf8"));
const have = new Set(assets);
const out = [];
const realLog = console.log;
for (const c of cases) {
  const fetched = [], logs = [], points = [];
  // env.ARRIVALS: a recorder by default; "absent" leaves it out, "throw" fails.
  const mode = c.arrivals || "record";
  const arrivals = mode === "absent" ? {} : { ARRIVALS: { writeDataPoint(p) {
    if (mode === "throw") throw new Error("analytics engine down");
    points.push(JSON.parse(JSON.stringify(p)));
  } } };
  const env = { ...c.env, ...arrivals, ASSETS: { async fetch(req) {
    const u = new URL(req.url);
    fetched.push(u.pathname + u.search);
    if (redirects[u.pathname]) return new Response(null, { status: 307,
      headers: { Location: redirects[u.pathname], "x-asset": u.pathname } });
    if (req.headers.get("if-none-match") === '"v1"' && have.has(u.pathname))
      return new Response(null, { status: 304,
        headers: { ETag: '"v1"', "x-asset": u.pathname } });
    const hit = have.has(u.pathname);
    return new Response(hit ? "asset:" + u.pathname : "missing",
      { status: hit ? 200 : 404, headers: { "x-asset": u.pathname } });
  } } };
  console.log = (...a) => logs.push(a.length === 1 && typeof a[0] === "object"
    ? a[0] : { text: a.join(" ") });
  let res, error = null;
  try { res = await worker.fetch(new Request(c.url, { headers: c.headers || {} }), env); }
  catch (e) { error = String(e); }
  finally { console.log = realLog; }
  out.push({ url: c.url, status: res ? res.status : null,
             headers: res ? [...res.headers].sort() : [],
             body: res ? await res.text() : "", fetched, logs, points, error });
}
process.stdout.write(JSON.stringify(out));
"""


def _node() -> str:
    node = shutil.which("node")
    if not node:
        skip("node is not installed; src/worker.js cannot be run")
    return node


def run_worker(source: str, cases: list[dict]) -> list[dict]:
    """Run `source` (worker.js text) over `cases` ({url, env, headers?})."""
    node = _node()
    with tempfile.TemporaryDirectory() as t:
        w, d, c = Path(t, "worker.mjs"), Path(t, "driver.mjs"), Path(t, "cases.json")
        w.write_text(source, encoding="utf-8")
        d.write_text(DRIVER, encoding="utf-8")
        c.write_text(json.dumps({"assets": ASSETS, "redirects": REDIRECTS,
                                 "cases": cases}), encoding="utf-8")
        p = subprocess.run([node, str(d), str(w), str(c)], capture_output=True,
                           text=True, timeout=60)
    assert p.returncode == 0, p.stderr
    return json.loads(p.stdout)


def baseline_source() -> str:
    p = subprocess.run(["git", "show", f"{BASELINE}:src/worker.js"], cwd=ROOT,
                       capture_output=True, text=True)
    assert p.returncode == 0, f"cannot read the baseline worker: {p.stderr}"
    assert "workers.dev" not in p.stdout and "console.log" not in p.stdout, "wrong baseline"
    return p.stdout


def source() -> str:
    return WORKER.read_text(encoding="utf-8")


def _path(url: str) -> str:
    return re.sub(r"^https://[^/]+", "", url)


JOBURG = "joburg.whysoserious.city"
PORTALS = ("whysoserious.city", "www.whysoserious.city")
PREVIEW_HOSTS = ("joburg-whysoserious.acct.workers.dev",           # live's workers.dev
                 "3f2a91bc-joburg-whysoserious.acct.workers.dev",  # Version URL
                 "uat-joburg-whysoserious.acct.workers.dev")       # aliased Version URL


def live_hosts() -> list[str]:
    routes = tomllib.loads(WRANGLER.read_text())["routes"]
    return [r["pattern"] for r in routes] + ["tshwane.whysoserious.city",
                                             "capetown.whysoserious.city"]


def live_cases() -> list[dict]:
    """Every live host x near misses; channel paths too, except on Joburg and
    the portal hosts, whose channel paths are checked by their own detectors;
    the shared pages on Joburg and the portal hosts only, since other cities
    city-prefixed them before 2026-10-02 (`shared_page_problems`)."""
    return [{"url": f"https://{h}{p}", "env": {}}
            for h in live_hosts()
            for p in LIVE_PATHS + (list(SHARED_PAGES) if h in (JOBURG, *PORTALS)
                                   else list(CHANNEL_PATHS))]


def live_diffs(new: str, old: str) -> list[str]:
    cases = live_cases()
    a, b = run_worker(old, cases), run_worker(new, cases)
    return [f"{x['url']}: {x} != {y}" for x, y in zip(a, b) if x != y]


PREVIEW_CASES = [{"url": f"https://{h}{p}", "env": {}}
                 for h in PREVIEW_HOSTS for p in LIVE_PATHS]


def preview_problems(src: str) -> list[str]:
    out = []
    for r in run_worker(src, PREVIEW_CASES):
        h = dict(r["headers"])
        if h.get("x-robots-tag") != NOINDEX:
            out.append(f"{r['url']}: X-Robots-Tag {h.get('x-robots-tag')!r}")
        if r["fetched"] != [_path(r["url"])]:
            out.append(f"{r['url']}: fetched {r['fetched']}, want [{_path(r['url'])!r}]")
        if r["logs"]:
            out.append(f"{r['url']}: logged {r['logs']}")
        if r["points"]:
            out.append(f"{r['url']}: wrote {r['points']}")
    return out


def passthrough_problems(src: str) -> list[str]:
    """A 307 and a 304 from ASSETS survive the noindex wrap unchanged."""
    host = PREVIEW_HOSTS[1]
    cases = [{"url": f"https://{host}/about.html", "env": {}},
             {"url": f"https://{host}/forecast", "env": {},
              "headers": {"If-None-Match": '"v1"'}}]
    r307, r304 = run_worker(src, cases)
    out = []
    for r, status, key, want in ((r307, 307, "location", "/about"),
                                 (r304, 304, "etag", '"v1"')):
        h = dict(r["headers"])
        if r["status"] != status or h.get(key) != want or r["body"]:
            out.append(f"{r['url']}: {r['status']} {key}={h.get(key)!r} "
                       f"body={r['body'][:20]!r}, want {status} {want!r}")
        if h.get("x-robots-tag") != NOINDEX:
            out.append(f"{r['url']}: X-Robots-Tag {h.get('x-robots-tag')!r}")
    return out


def channel_problems(src: str) -> list[str]:
    hosts = [(JOBURG, False)] + [(h, True) for h in PREVIEW_HOSTS]
    keys = [(h, p, n, pv) for h, pv in hosts for p, n in CHANNEL_PATHS.items()]
    cases = [{"url": f"https://{h}{p}", "env": {}} for h, p, _n, _pv in keys]
    out = []
    for r, (host, _p, name, preview) in zip(run_worker(src, cases), keys):
        h = dict(r["headers"])
        if r["status"] != 302 or h.get("location") != f"https://{host}/" or r["fetched"]:
            out.append(f"{r['url']}: {r['status']} {h.get('location')!r} "
                       f"fetched {r['fetched']}")
        want = {"event": "arrival", "channel": name, "host": host}
        logged = r["logs"]  # each a logged object; a string arrives as {"text": ...}
        if logged != [want]:
            out.append(f"{r['url']}: logged {r['logs']}, want [{want}]")
        point = {"blobs": [name, host], "doubles": [1], "indexes": [name]}
        if r["points"] != [point]:
            out.append(f"{r['url']}: wrote {r['points']}, want [{point}]")
        if preview != (h.get("x-robots-tag") == NOINDEX):
            out.append(f"{r['url']}: X-Robots-Tag {h.get('x-robots-tag')!r}")
    return out


def portal_channel_problems(src: str) -> list[str]:
    keys = [(h, p) for h in PORTALS for p in CHANNEL_PATHS]
    cases = [{"url": f"https://{h}{p}", "env": {}} for h, p in keys]
    out = []
    for r, (host, p) in zip(run_worker(src, cases), keys):
        h = dict(r["headers"])
        want = f"https://{JOBURG}{p}"
        if r["status"] != 302 or h.get("location") != want or r["fetched"]:
            out.append(f"{r['url']}: {r['status']} {h.get('location')!r} "
                       f"fetched {r['fetched']}, want 302 {want!r}")
        if r["logs"]:
            out.append(f"{r['url']}: logged {r['logs']}; only {JOBURG} logs")
        if r["points"]:
            out.append(f"{r['url']}: wrote {r['points']}; only {JOBURG} writes")
        if "x-robots-tag" in h:
            out.append(f"{r['url']}: X-Robots-Tag {h['x-robots-tag']!r}")
    return out


def resilience_problems(src: str) -> list[str]:
    """With ARRIVALS absent, or throwing on every write, each channel path on
    the Joburg host still answers 302 home and logs its one arrival."""
    keys = [(m, p, n) for m in ("absent", "throw") for p, n in CHANNEL_PATHS.items()]
    cases = [{"url": f"https://{JOBURG}{p}", "env": {}, "arrivals": m}
             for m, p, _n in keys]
    out = []
    for r, (mode, _p, name) in zip(run_worker(src, cases), keys):
        h = dict(r["headers"])
        if r["error"] or r["status"] != 302 or h.get("location") != f"https://{JOBURG}/":
            out.append(f"{r['url']} [{mode}]: {r['status']} {h.get('location')!r} "
                       f"error={r['error']!r}")
        want = {"event": "arrival", "channel": name, "host": JOBURG}
        if r["logs"] != [want]:
            out.append(f"{r['url']} [{mode}]: logged {r['logs']}, want [{want}]")
        if r["points"]:
            out.append(f"{r['url']} [{mode}]: recorded {r['points']}")
    return out


def shared_page_problems(src: str) -> list[str]:
    hosts = live_hosts() + list(PREVIEW_HOSTS)
    keys = [(h, p, st) for h in hosts for p, st in SHARED_PAGES.items()]
    cases = [{"url": f"https://{h}{p}", "env": {}} for h, p, _st in keys]
    out = []
    for r, (host, p, status) in zip(run_worker(src, cases), keys):
        h = dict(r["headers"])
        if r["status"] != status or r["fetched"] != [p]:
            out.append(f"{r['url']}: {r['status']} fetched {r['fetched']}, "
                       f"want {status} [{p!r}]")
        if r["logs"] or r["points"]:
            out.append(f"{r['url']}: logged {r['logs']} wrote {r['points']}")
        if (host in PREVIEW_HOSTS) != (h.get("x-robots-tag") == NOINDEX):
            out.append(f"{r['url']}: X-Robots-Tag {h.get('x-robots-tag')!r}")
    return out


def _mutate(src: str, old: str, new: str) -> str:
    assert src.count(old) == 1, f"mutation anchor not unique: {old!r}"
    return src.replace(old, new)


# ---------------------------------------------------------------- live

def test_the_live_population_is_the_one_wrangler_routes():
    routed = {r["pattern"] for r in tomllib.loads(WRANGLER.read_text())["routes"]}
    assert {JOBURG, "whysoserious.city", "www.whysoserious.city"} <= routed, routed
    assert not any(h.endswith(".workers.dev") for h in routed)
    n = len(live_cases())
    assert 100 <= n <= 400, n
    assert not {p.split("?")[0].lower().rstrip("/") for p in LIVE_PATHS} & \
        {"/" + k for k in CHANNELS}


def test_live_routing_matches_the_baseline_worker():
    old = baseline_source()
    # the differential looked: the baseline exercised the portal, the root,
    # the city directory, the unbuilt-city fallback and the 307
    runs = run_worker(old, live_cases())
    fetched = {f for r in runs for f in r["fetched"]}
    assert {"/portal", "/", "/tshwane/index.html", "/capetown/index.html",
            "/tshwane/go", "/about.html"} <= fetched, fetched
    assert any(r["status"] == 307 for r in runs)
    assert live_diffs(source(), old) == []


def test_live_differential_fires_on_a_changed_live_route():
    src, old = source(), baseline_source()
    for a, b in (('host.endsWith(".workers.dev")', 'host.endsWith(".city")'),
                 ("    if (ROOT_CITIES.has(sub)) {\n      const channel",
                  "    if (true) {\n      const channel"),
                 ('/^\\/([a-z]+)\\/?$/', '/^\\/([a-z]+)\\/?/')):
        assert live_diffs(_mutate(src, a, b), old), f"differential blind to {b!r}"


def test_live_hosts_are_never_noindexed():
    for r in run_worker(source(), live_cases()):
        assert "x-robots-tag" not in dict(r["headers"]), r["url"]


def test_no_data_point_off_the_channel_paths():
    """Near misses on every live host, and channel paths on cities other than
    Joburg, write no Analytics Engine point; neither does the 307 or 304."""
    runs = run_worker(source(), live_cases() + PREVIEW_CASES)
    assert not [(r["url"], r["points"]) for r in runs if r["points"]]
    assert not [r["url"] for r in runs if r["error"]]


# ---------------------------------------------------------------- shared pages

def test_support_and_privacy_resolve_from_every_host():
    assert {"tshwane.whysoserious.city", "capetown.whysoserious.city",
            JOBURG, *PORTALS} <= set(live_hosts())
    assert shared_page_problems(source()) == []


def test_shared_page_check_fires_on_each_constructed_violation():
    src = source()
    for a, b in (('  "/support", "/support.html", "/privacy", "/privacy.html",\n', ""),
                 ('"/support", "/support.html", ', ""),
                 ('"/privacy", "/privacy.html",', '"/privacy",'),
                 ("ROOT_CITIES.has(sub) || SHARED_PAGES.has(path) ||",
                  "ROOT_CITIES.has(sub) ||")):
        assert shared_page_problems(_mutate(src, a, b)), f"blind to {b!r}"
    # the baseline worker city-prefixed both pages on every other city host
    # (and on workers.dev, which it treated as a city); Joburg and the portal
    # hosts already served them from the root
    probs = shared_page_problems(baseline_source())
    for h in ("tshwane.", "capetown."):
        assert any(f"https://{h}" in p for p in probs), h
    assert not any(p.startswith(f"https://{h}/") for p in probs
                   for h in (JOBURG, *PORTALS)), probs


def test_shared_pages_are_exact_matches_in_the_differential():
    """A prefix match would send /supporters on a city host to the root; the
    differential carries the near misses on every host to catch that."""
    src, old = source(), baseline_source()
    for near in ("/supporters", "/support/x", "/privacyx"):
        assert near in LIVE_PATHS
    prefix = _mutate(src, "SHARED_PAGES.has(path) ||",
                     "[...SHARED_PAGES].some((p) => path.startsWith(p)) ||")
    assert live_diffs(prefix, old), "differential blind to a prefix match"


# ---------------------------------------------------------------- preview

def test_workers_dev_hosts_serve_joburg_with_noindex():
    assert len(PREVIEW_CASES) == len(PREVIEW_HOSTS) * len(LIVE_PATHS)
    assert preview_problems(source()) == []


def test_preview_check_fires_without_the_header_or_on_portal_routing():
    src = source()
    no_header = _mutate(src, '      out.headers.set("X-Robots-Tag", NOINDEX);\n', "")
    assert len(preview_problems(no_header)) == len(PREVIEW_CASES)
    no_branch = _mutate(src, 'return host.endsWith(".workers.dev");', "return false;")
    assert preview_problems(no_branch)
    # the baseline worker is the defect this change repairs
    assert preview_problems(baseline_source())


def test_307_and_304_survive_the_noindex_wrap():
    assert passthrough_problems(source()) == []


def test_passthrough_check_fires_when_the_wrap_drops_status_or_headers():
    src = source()
    anchor = "const out = new Response(res.body, res);"
    for b in ("const out = new Response(res.body, { headers: res.headers });",
              "const out = new Response(res.body, { status: res.status });"):
        assert passthrough_problems(_mutate(src, anchor, b)), f"blind to {b!r}"


# ---------------------------------------------------------------- channels

def test_every_channel_path_redirects_home_and_logs_one_arrival():
    for k in CHANNELS:  # each short path in lower, upper and slash forms
        assert {f"/{k}", f"/{k}/", f"/{k.upper()}", f"/{k.upper()}/"} <= set(CHANNEL_PATHS), k
    assert set(CHANNEL_PATHS.values()) == set(CHANNELS.values())
    assert channel_problems(source()) == []


def test_channel_check_fires_on_each_constructed_violation():
    src = source()
    for a, b in (('["go", "billboard"]', '["go", "dooh"]'),
                 ("path.toLowerCase()", "path"),
                 ("    status: 302,\n    headers: { Location: new URL",
                  "    status: 301,\n    headers: { Location: new URL"),
                 ('  console.log({ event: "arrival", channel, host });\n', ""),
                 ('console.log({ event: "arrival", channel, host })',
                  'console.log(JSON.stringify({ event: "arrival", channel, host }))'),
                 ('/^\\/([a-z]+)\\/?$/', '/^\\/([a-z]+)$/'),
                 ('new URL("/", url)', 'new URL("/forecast", url)'),
                 ('  ["ig", "instagram"],\n', ""),
                 (AE_WRITE, ""),
                 ("blobs: [channel, host]", "blobs: [host, channel]"),
                 ("indexes: [channel]", "indexes: [host]"),
                 ("doubles: [1]", "doubles: []"),
                 (AE_WRITE, AE_WRITE + "\n    " + AE_WRITE),
                 (AE_WRITE, AE_WRITE.replace("[channel, host]",
                                             "[channel, host, request.url]"))):
        assert channel_problems(_mutate(src, a, b)), f"channel check blind to {b!r}"
    assert channel_problems(baseline_source())


def test_portal_channel_paths_redirect_to_the_joburg_host_unlogged():
    assert portal_channel_problems(source()) == []
    # the gclid survives to the host that logs the arrival
    assert any("?gclid=" in p for p in CHANNEL_PATHS)


def test_portal_channel_check_fires_on_each_constructed_violation():
    src = source()
    for a, b in (("      if (channelOf(path)) {", "      if (false) {"),
                 ("${path}${url.search}", "${path}"),
                 ("${path}${url.search}", "/"),
                 ("          status: 302,\n          headers: { Location: `",
                  "          status: 301,\n          headers: { Location: `"),
                 ("      if (channelOf(path)) {",
                  "      if (channelOf(path)) {\n        console.log({ event: \"arrival\" });")):
        assert portal_channel_problems(_mutate(src, a, b)), f"blind to {b!r}"
    # the baseline worker served these paths from the asset layer
    assert portal_channel_problems(baseline_source())


# ---------------------------------------------------------------- analytics engine

AE_WRITE = ("env.ARRIVALS?.writeDataPoint({ blobs: [channel, host], "
            "doubles: [1], indexes: [channel] });")


def test_the_redirect_survives_a_missing_or_failing_binding():
    assert resilience_problems(source()) == []


def test_resilience_check_fires_on_each_constructed_violation():
    src = source()
    bare = "env.ARRIVALS.writeDataPoint({ blobs: [channel, host], doubles: [1], indexes: [channel] });"
    # `?.` and try/catch each cover the other's absence, so the violation
    # removes both: a bare call outside any try.
    i = src.index("  try {\n    " + AE_WRITE)
    j = src.index("  }\n", src.index("  } catch {", i)) + len("  }\n")
    unguarded = src[:i] + "  " + bare + "\n" + src[j:]
    assert unguarded.count("writeDataPoint(") == 1 and "catch" not in unguarded[i:i + 200]
    assert resilience_problems(unguarded), "blind to an unguarded write"
    # the throw case alone: `?.` without try/catch survives "absent" only
    no_try = src[:i] + "  " + AE_WRITE + "\n" + src[j:]
    probs = resilience_problems(no_try)
    assert probs and all("[throw]" in p for p in probs), probs
    # the absent case alone: try/catch without `?.` survives both, by catching
    assert resilience_problems(_mutate(src, AE_WRITE, bare)) == []


def test_the_worker_writes_nothing_about_the_visitor():
    """The data point carries the channel and hostname only."""
    src = source()
    assert src.count("writeDataPoint(") == 1 and AE_WRITE in src
    body = src[src.index("function arrival"):src.index("export default")]
    for leak in ("CF-Connecting-IP", "cf-connecting-ip", "User-Agent", "user-agent",
                 "request.cf", "url.search", "headers.get"):
        assert leak not in body, leak


# ---------------------------------------------------------------- config

def config_problems(text: str, staging_file: bool | None = None) -> list[str]:
    cfg = tomllib.loads(text)
    out = []
    if cfg.get("workers_dev") is not True:
        out.append("workers_dev is not true at the top level")
    if cfg.get("preview_urls") is not True:
        out.append("preview_urls is not true at the top level: no Version URL for UAT")
    if cfg.get("observability", {}).get("enabled") is not True:
        out.append("[observability] enabled is not true: arrivals are not counted")
    if cfg.get("observability", {}).get("logs", {}).get("invocation_logs") is not False:
        out.append("[observability.logs] invocation_logs is not false: every "
                   "request is logged, which docs-public/privacy.md says it is not")
    for table, body in cfg.items():
        if isinstance(body, dict):
            for key in ("routes", "preview_urls", "workers_dev"):
                if key in body:
                    out.append(f"{key} sits under [{table}] and is ignored")
    if "STAGING" in cfg.get("vars", {}):
        out.append("vars.STAGING is set on the live Worker")
    if not cfg.get("routes"):
        out.append("no top-level routes")
    if {"binding": "ARRIVALS", "dataset": "joburg_arrivals"} not in \
            cfg.get("analytics_engine_datasets", []):
        out.append("no top-level [[analytics_engine_datasets]] ARRIVALS -> "
                   "joburg_arrivals: arrivals are kept seven days only")
    if staging_file is None:
        staging_file = (ROOT / "wrangler.staging.toml").exists()
    if staging_file:
        out.append("wrangler.staging.toml exists; UAT is a Version URL now")
    return out


def test_wrangler_toml_states_preview_urls_and_observability():
    assert config_problems(WRANGLER.read_text(encoding="utf-8")) == []


AE_BLOCK = ('[[analytics_engine_datasets]]\nbinding = "ARRIVALS"\n'
            'dataset = "joburg_arrivals"\n')


def test_config_check_fires_on_each_constructed_violation():
    text = WRANGLER.read_text(encoding="utf-8")
    assert text.count(AE_BLOCK) == 1
    line = "preview_urls = true\n"
    assert text.count(line) == 1
    cases = {
        "preview_urls under [assets]": text.replace(line, "").replace(
            "run_worker_first = true\n", "run_worker_first = true\n" + line),
        "preview_urls off": text.replace(line, "preview_urls = false\n"),
        "preview_urls absent": text.replace(line, ""),
        "observability off": text.replace("[observability]\nenabled = true",
                                          "[observability]\nenabled = false"),
        "observability absent": text.replace("[observability]\nenabled = true\n", ""),
        "STAGING var": text + '\n[vars]\nSTAGING = "1"\n',
        "invocation logs on": text.replace("invocation_logs = false",
                                           "invocation_logs = true"),
        "invocation logs unstated": text.replace("invocation_logs = false\n", ""),
        "AE binding absent": text.replace(AE_BLOCK, ""),
        "AE binding renamed": text.replace('binding = "ARRIVALS"', 'binding = "ARRIVAL"'),
        "AE dataset renamed": text.replace('dataset = "joburg_arrivals"',
                                           'dataset = "arrivals"'),
        "AE binding inline under [observability.logs]": text.replace(AE_BLOCK, "") +
            'analytics_engine_datasets = [{ binding = "ARRIVALS", '
            'dataset = "joburg_arrivals" }]\n',
    }
    for name, t in cases.items():
        assert t != text, name
        assert config_problems(t), f"config check blind to {name}"
    assert config_problems(text, staging_file=True), "blind to wrangler.staging.toml"
