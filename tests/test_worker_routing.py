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
* `moved_problems`    — every moved page (src/worker.js MOVED, 2026-10-03:
                        /about to /methodology; /play/ and /make/ to the two
                        sections of /your-forecast/) answers 301 to its new
                        address with its query string, in every spelling that
                        moves, on the Joburg host and every workers.dev host;
                        fetches nothing and logs nothing. The near misses
                        (/aboutx, /about/x, /About, /playground, /maker,
                        /make.html, /your-forecast/) are served as before. The
                        live differential runs the moved paths on the portal
                        and other city hosts, where nothing changed.
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
ASSETS = ["/", "/index.html", "/forecast", "/methodology", "/portal",
          "/logos/party.png", "/robots.txt", "/share.jpg",
          "/tshwane/index.html", "/tshwane/forecast", "/support", "/privacy"]
#: The real layer 307s an .html URL to its extensionless form.
REDIRECTS = {"/forecast.html": "/forecast", "/support.html": "/support",
             "/privacy.html": "/privacy"}
#: Pages every host serves from the asset root, and what ASSETS answers.
SHARED_PAGES = {"/support": 200, "/privacy": 200, "/support.html": 307,
                "/privacy.html": 307}

#: Near misses: none of these is a channel path on any host.
LIVE_PATHS = ["/", "/index.html", "/forecast", "/forecast.html", "/nope",
              "/logos/party.png", "/robots.txt", "/share.jpg", "/?x=1",
              "/go/x", "/gone", "/go.html", "/xx", "/gg", "/g/x", "/G/x",
              "/li.html", "/fbx", "/ig/ig", "//go",
              "/supporters", "/support/x", "/privacyx", "/Support",
              "/aboutx", "/about/x", "/About"]

#: Pages that moved (src/worker.js MOVED): every spelling that must redirect,
#: and where to. On the Joburg host and workers.dev hosts only. The query
#: strings on /play/ and /make/ are a shared /play/ link (`t=…&n=…`) and a
#: shared /make/ link (`v=1&c=…&f=…`): each must arrive whole, since the new
#: page reads both parts.
MOVED_PATHS = {
    "/about": "/methodology", "/about.html": "/methodology",
    "/about/": "/methodology", "/about?x=1": "/methodology?x=1",
    "/play": "/your-forecast/", "/play/": "/your-forecast/", "/PLAY/": "/your-forecast/",
    "/play/index.html": "/your-forecast/",
    "/play/?t=5,0,0,0&n=Thandi": "/your-forecast/?t=5,0,0,0&n=Thandi",
    "/make": "/your-forecast/#break", "/make/": "/your-forecast/#break",
    "/Make/index.html": "/your-forecast/#break",
    "/make/?v=1&c=abc123&f=AQID-_": "/your-forecast/?v=1&c=abc123&f=AQID-_#break",
}
#: Not moved: each must reach the asset layer unchanged on the Joburg and
#: workers.dev hosts.
NOT_MOVED = ["/aboutx", "/about/x", "/About",
             "/playground", "/maker", "/your-forecast/", "/plays", "/make.html"]

DRIVER = r"""
import { readFileSync } from "node:fs";
const [workerPath, casesPath] = process.argv.slice(2);
const worker = (await import("file://" + workerPath)).default;
const { assets, redirects, files, cases } = JSON.parse(readFileSync(casesPath, "utf8"));
const have = new Set(assets);
const out = [];
const realLog = console.log, realError = console.error;
const realNow = Date.now;
// A fake D1 for ENTRIES, one per run, so cases see each other's rows: it
// answers the two statements share-edge.js sends (the insert, INSERT OR IGNORE
// on the first column; the count) and records every statement and its values.
const db = { rows: new Map(), statements: [] };
function fakeD1(mode) {
  return { prepare(sql) {
    const stmt = { values: [], bind(...v) { stmt.values = v; return stmt; },
      async run() {
        db.statements.push({ sql, values: stmt.values });
        if (mode === "throw") throw new Error("D1 down");
        const m = /^INSERT OR IGNORE INTO entries \(([^)]*)\) VALUES/.exec(sql);
        if (!m) throw new Error("fake D1: unexpected statement " + sql);
        const cols = m[1].split(", ");
        if (cols.length !== stmt.values.length) throw new Error("fake D1: columns and values differ");
        const row = Object.fromEntries(cols.map((c, i) => [c, stmt.values[i]]));
        if (!db.rows.has(row[cols[0]])) db.rows.set(row[cols[0]], row);
        return { success: true };
      },
      async first() {
        db.statements.push({ sql, values: stmt.values });
        if (mode === "throw") throw new Error("D1 down");
        if (sql !== "SELECT COUNT(*) AS n FROM entries") throw new Error("fake D1: unexpected statement " + sql);
        return { n: db.rows.size };
      } };
    return stmt;
  } };
}
// A fake Rate Limiting binding, one per run: `limit` calls per key, then refused.
const counts = new Map();
const limiter = limit => ({ async limit({ key }) {
  counts.set(key, (counts.get(key) || 0) + 1);
  limitKeys.push(key);
  return { success: counts.get(key) <= limit };
} });
let limitKeys = [];
const TYPES = { json: "application/json", png: "image/png", svg: "image/svg+xml", html: "text/html; charset=utf-8" };
for (const c of cases) {
  const fetched = [], logs = [], errors = [], points = [], seatCalls = [], pending = [];
  limitKeys = [];
  const before = db.statements.length;
  // c.entries: "record" (the run's fake D1) or "throw"; c.limit: SEAL_LIMIT's limit
  const entries = c.entries ? { ENTRIES: fakeD1(c.entries) } : {};
  const limits = c.limit ? { SEAL_LIMIT: limiter(c.limit) } : {};
  // c.now: the Worker's clock for this case (ms), for the polls-open refusal
  Date.now = c.now ? () => c.now : realNow;
  // c.seats: a fake seat Worker answering every /v1/card with this status and body
  const seats = c.seats ? { SEATS: { async fetch(u, init) {
    seatCalls.push({ url: String(u), body: JSON.parse(init.body) });
    return new Response(JSON.stringify(c.seats.body), { status: c.seats.status });
  } } } : {};
  // env.ARRIVALS: a recorder by default; "absent" leaves it out, "throw" fails.
  const mode = c.arrivals || "record";
  const arrivals = mode === "absent" ? {} : { ARRIVALS: { writeDataPoint(p) {
    if (mode === "throw") throw new Error("analytics engine down");
    points.push(JSON.parse(JSON.stringify(p)));
  } } };
  const env = { ...c.env, ...arrivals, ...seats, ...entries, ...limits, ASSETS: { async fetch(req) {
    const u = new URL(req.url);
    fetched.push(u.pathname + u.search);
    if (files[u.pathname]) return new Response(readFileSync(files[u.pathname]),
      { status: 200, headers: { "content-type": TYPES[u.pathname.split(".").pop()] || TYPES.html, "x-asset": u.pathname } });
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
  console.error = (...a) => errors.push(a.length === 1 && typeof a[0] === "object"
    ? a[0] : { text: a.map(String).join(" ") });
  let res, error = null;
  const init = { headers: c.headers || {}, method: c.method || "GET" };
  if (c.body !== undefined) init.body = JSON.stringify(c.body);
  let body = "";
  try {
    res = await worker.fetch(new Request(c.url, init), env, { waitUntil(p) { pending.push(p); } });
    body = await res.text();
    await Promise.all(pending);   // what ran after the response, before the next case
  }
  catch (e) { error = String(e); }
  finally { console.log = realLog; console.error = realError; Date.now = realNow; }
  out.push({ url: c.url, status: res ? res.status : null,
             headers: res ? [...res.headers].sort() : [],
             body, fetched, logs, errors, points, seatCalls, error,
             statements: db.statements.slice(before), rows: [...db.rows.values()], limitKeys });
}
process.stdout.write(JSON.stringify(out));
"""


def _node() -> str:
    node = shutil.which("node")
    if not node:
        skip("node is not installed; src/worker.js cannot be run")
    return node


def run_worker(source: str, cases: list[dict], files: dict | None = None,
               overrides: dict | None = None) -> list[dict]:
    """Run `source` (worker.js text) over `cases` ({url, env, headers?,
    method?, body?, now?, seats?}). The worker is written into a temporary
    `src/` beside copies of the other modules in src/ (`overrides` maps a
    file name to text that replaces its copy: a mutant, never written into
    the repository), next to links to the real `interactive/` and
    `worker-api/`, so every relative import resolves as it does in the
    repository. `files` maps an asset path to a file the fake ASSETS serves."""
    node = _node()
    with tempfile.TemporaryDirectory() as t:
        src = Path(t, "src")
        src.mkdir()
        for name in ("interactive", "worker-api"):
            Path(t, name).symlink_to(ROOT / name)
        for js in WORKER.parent.glob("*.js"):
            if js != WORKER:
                Path(src, js.name).write_text((overrides or {}).get(js.name, js.read_text(encoding="utf-8")),
                                             encoding="utf-8")
        for d_ in ("card-fonts",):
            Path(src, d_).symlink_to(WORKER.parent / d_)
        w, d, c = Path(src, "worker.mjs"), Path(t, "driver.mjs"), Path(t, "cases.json")
        w.write_text(source, encoding="utf-8")
        d.write_text(DRIVER, encoding="utf-8")
        c.write_text(json.dumps({"assets": ASSETS, "redirects": REDIRECTS,
                                 "files": {k: str(v) for k, v in (files or {}).items()},
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
    city-prefixed them before 2026-10-02 (`shared_page_problems`); the moved
    pages everywhere but Joburg, whose redirects `moved_problems` checks."""
    return [{"url": f"https://{h}{p}", "env": {}}
            for h in live_hosts()
            for p in LIVE_PATHS + (list(SHARED_PAGES) if h in (JOBURG, *PORTALS)
                                   else list(CHANNEL_PATHS))
            + ([] if h == JOBURG else list(MOVED_PATHS))]


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
    cases = [{"url": f"https://{host}/forecast.html", "env": {}},
             {"url": f"https://{host}/forecast", "env": {},
              "headers": {"If-None-Match": '"v1"'}}]
    r307, r304 = run_worker(src, cases)
    out = []
    for r, status, key, want in ((r307, 307, "location", "/forecast"),
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


def moved_problems(src: str) -> list[str]:
    hosts = [JOBURG, *PREVIEW_HOSTS]
    keys = [(h, p, to) for h in hosts for p, to in MOVED_PATHS.items()]
    cases = [{"url": f"https://{h}{p}", "env": {}} for h, p, _to in keys]
    out = []
    for r, (host, _p, to) in zip(run_worker(src, cases), keys):
        h = dict(r["headers"])
        want = f"https://{host}{to}"
        if r["status"] != 301 or h.get("location") != want or r["fetched"]:
            out.append(f"{r['url']}: {r['status']} {h.get('location')!r} "
                       f"fetched {r['fetched']}, want 301 {want!r}")
        if r["logs"] or r["points"]:
            out.append(f"{r['url']}: logged {r['logs']} wrote {r['points']}")
        if (host in PREVIEW_HOSTS) != (h.get("x-robots-tag") == NOINDEX):
            out.append(f"{r['url']}: X-Robots-Tag {h.get('x-robots-tag')!r}")
    near = [(h, p) for h in hosts for p in NOT_MOVED]
    for r, (host, p) in zip(run_worker(src, [{"url": f"https://{h}{p}", "env": {}}
                                             for h, p in near]), near):
        if r["fetched"] != [p] or r["status"] == 301:
            out.append(f"{r['url']}: {r['status']} fetched {r['fetched']}, want it served")
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
            "/tshwane/go", "/forecast.html"} <= fetched, fetched
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


# ---------------------------------------------------------------- moved pages

def test_the_moved_pages_redirect_with_their_query_strings():
    assert moved_problems(source()) == []
    # the population: every old page, with and without a link's settings
    assert {"/about", "/play/", "/make/"} <= set(MOVED_PATHS)
    assert any("?" in p for p in MOVED_PATHS if p.lower().startswith("/play"))
    assert any("f=" in p for p in MOVED_PATHS if p.lower().startswith("/make"))
    assert any("?" in p for p in MOVED_PATHS if p.startswith("/about"))


def test_moved_check_fires_on_each_constructed_violation():
    src = source()
    for a, b in (('  [/^\\/about(?:\\.html|\\/)?$/, "/methodology", ""],\n', ""),
                 ('  [/^\\/make(?:\\/.*)?$/i, "/your-forecast/", "#break"],\n', ""),
                 ('/^\\/about(?:\\.html|\\/)?$/', '/^\\/about$/'),
                 ('/^\\/about(?:\\.html|\\/)?$/', '/^\\/about/i'),
                 ('/^\\/play(?:\\/.*)?$/i', '/^\\/play(?:\\/.*)?$/'),
                 ('/^\\/play(?:\\/.*)?$/i', '/^\\/play/i'),
                 ("path + url.search + hash", "path + hash"),
                 ("status: 301,", "status: 302,"),
                 ("      const to = movedTo(path);\n      if (to) return moved(url, to);\n", ""),
                 ("        : to ? moved(url, to)\n          : (await shareRoute",
                  "        : (await shareRoute")):
        assert moved_problems(_mutate(src, a, b)), f"moved check blind to {b!r}"
    # the baseline worker had no moved page
    assert moved_problems(baseline_source())


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
    for a, b in (("      if (channelOf(path) || isShare(path)) {", "      if (isShare(path)) {"),
                 ("${path}${url.search}", "${path}"),
                 ("${path}${url.search}", "/"),
                 ("          status: 302,\n          headers: { Location: `",
                  "          status: 301,\n          headers: { Location: `"),
                 ("      if (channelOf(path) || isShare(path)) {",
                  "      if (channelOf(path) || isShare(path)) {\n        console.log({ event: \"arrival\" });")):
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


# ---------------------------------------------------------------- shared forecasts
#
# src/share-edge.js (audits/2026-10-03-share-design), driven through the
# worker: /s/ counted and sent to the arrival view, the page's tags rewritten
# for a link that carries a forecast, the image route's seat call and its
# fallback, and the seal. The fake ASSETS serves the real forecast.json (built
# here by build_make, not the possibly older one under site/), parties.json,
# the logos and the built page; the fake SEATS records what it is asked.

#: A key for these tests only. Obviously not a secret; the live key is a
#: Worker secret set by the owner (`wrangler secret put SEAL_KEY`).
TEST_SEAL_KEY = "test-only-seal-key"
_SHARE: dict = {}


def _share_setup() -> dict:
    """forecast.json and parties.json in a temp dir, and one valid link."""
    if _SHARE:
        return _SHARE
    sys.path.insert(0, str(ROOT / "src"))
    import build_make
    import build_play
    t = Path(tempfile.mkdtemp(prefix="share-"))
    data = build_make.forecast_data()
    (t / "forecast.json").write_text(json.dumps(data), encoding="utf-8")
    (t / "parties.json").write_bytes(build_play.roster_json())
    # the published start with a coalition, through the page's own encoder
    script = r"""
import { readFileSync } from "node:fs";
import * as B from "%s";
import * as MS from "%s";
const D = JSON.parse(readFileSync(process.argv[2], "utf8"));
const ctx = B.contextOf(D.schema);
const st = B.startState(ctx, { calls: D.start.ward_calls, share: D.start.combined_share }, D.start.ward_calls).state;
const seats = D.start.seats;
const top = Object.keys(seats).sort((a, b) => seats[b] - seats[a]).slice(0, 2);
const other = B.assignWards(st, ctx, [0], st.calls[1] === st.calls[0] ? top[1] : st.calls[1]).state;
process.stdout.write(JSON.stringify({ f: MS.encode(st, top, ctx), f2: MS.encode(other, [top[0]], ctx),
  calls: st.calls, top }));
""" % ((ROOT / "interactive/js/builder-state.js").as_uri(), (ROOT / "interactive/js/make-state.js").as_uri())
    (t / "enc.mjs").write_text(script, encoding="utf-8")
    p = subprocess.run([_node(), str(t / "enc.mjs"), str(t / "forecast.json")],
                       capture_output=True, text=True, timeout=120)
    assert p.returncode == 0, p.stderr
    enc = json.loads(p.stdout)
    _SHARE.update(dir=t, data=data, link=f"v=1&c={data['context_ref']}&f={enc['f']}", f=enc["f"],
                  f2=enc["f2"], calls=enc["calls"], top=enc["top"],
                  files={"/your-forecast/forecast.json": t / "forecast.json",
                         "/your-forecast/parties.json": t / "parties.json",
                         "/your-forecast/index.html": ROOT / "site/your-forecast/index.html",
                         "/your-forecast/": ROOT / "site/your-forecast/index.html",
                         "/logo.svg": ROOT / "site/logo.svg"})
    return _SHARE


def share_arrival_problems(src: str, overrides: dict | None = None) -> list[str]:
    S = _share_setup()
    out = []
    for host in (JOBURG, *PREVIEW_HOSTS):
        for ch, blob in (("wa", "wa"), ("copy", "copy"), ("evil<x>", ""), (None, "")):
            q = S["link"] + "&n=Thandi" + (f"&ch={ch}" if ch else "")
            r = run_worker(src, [{"url": f"https://{host}/s/?{q}", "env": {}}], overrides=overrides)[0]
            h = dict(r["headers"])
            want = f"https://{host}/your-forecast/?{S['link']}&n=Thandi&from=1"
            if r["status"] != 302 or h.get("location") != want or r["fetched"]:
                out.append(f"{host} ch={ch}: {r['status']} {h.get('location')!r} fetched {r['fetched']}, want {want!r}")
            point = {"blobs": ["share", host, blob], "doubles": [1], "indexes": ["share"]}
            if r["points"] != [point]:
                out.append(f"{host} ch={ch}: wrote {r['points']}, want [{point}]")
            log = {"event": "arrival", "channel": "share", "host": host, "via": blob}
            if r["logs"] != [log]:
                out.append(f"{host} ch={ch}: logged {r['logs']}, want [{log}]")
            if (host in PREVIEW_HOSTS) != (h.get("x-robots-tag") == NOINDEX):
                out.append(f"{host}: X-Robots-Tag {h.get('x-robots-tag')!r}")
    for host in PORTALS:
        for path in ("/s/", "/s"):
            r = run_worker(src, [{"url": f"https://{host}{path}?{S['link']}&ch=x", "env": {}}], overrides=overrides)[0]
            want = f"https://{JOBURG}{path}?{S['link']}&ch=x"
            if r["status"] != 302 or dict(r["headers"]).get("location") != want or r["logs"] or r["points"]:
                out.append(f"{host}{path}: {r['status']} {dict(r['headers']).get('location')!r} "
                           f"logged {r['logs']} wrote {r['points']}, want 302 {want!r} unlogged")
    return out


def test_share_links_count_once_and_open_the_arrival_view():
    assert share_arrival_problems(source()) == []


def test_share_arrival_check_fires_on_each_constructed_violation():
    edge = (ROOT / "src" / "share-edge.js").read_text(encoding="utf-8")
    src = source()
    write = 'env.ARRIVALS?.writeDataPoint({ blobs: ["share", host, ch], doubles: [1], indexes: ["share"] });'
    assert edge.count(write) == 1
    for a, b in ((write, ""), ('blobs: ["share", host, ch]', 'blobs: ["share", host, url.search]'),
                 ('if (q.has("f")) q.set("from", "1");', ""), ('q.delete("ch");', ""),
                 ("SHARE_CHANNELS.has(raw) ? raw : \"\"", "raw || \"\"")):
        assert edge.count(a) == 1, a
        assert share_arrival_problems(src, {"share-edge.js": edge.replace(a, b)}), f"blind to {b!r}"
    assert share_arrival_problems(_mutate(src, "      if (channelOf(path) || isShare(path)) {",
                                          "      if (channelOf(path)) {"))


def test_the_built_page_carries_every_tag_a_shared_link_rewrites():
    page = (ROOT / "site/your-forecast/index.html").read_text(encoding="utf-8")
    edge = (ROOT / "src" / "share-edge.js").read_text(encoding="utf-8")
    tags = re.findall(r'"((?:og|twitter):[a-z:]+)"', edge[edge.index("export const TAGS"):].split("\n")[0])
    assert len(tags) == 6, tags
    for t in tags:
        attr = "name" if t.startswith("twitter:") else "property"
        assert page.count(f'<meta {attr}="{t}" content="') == 1, t


def test_a_shared_link_names_its_forecast_and_points_at_its_own_image():
    S = _share_setup()
    cases = [{"url": f"https://{JOBURG}/your-forecast/?{S['link']}&n=Thandi&from=1&t=1,0,0,0", "env": {}},
             {"url": f"https://{JOBURG}/your-forecast/?{S['link']}&n=%3Cb%3EX%3C%2Fb%3E", "env": {}},
             {"url": f"https://{JOBURG}/your-forecast/?t=1,0,0,0", "env": {}},
             {"url": f"https://{PREVIEW_HOSTS[1]}/your-forecast/?{S['link']}&n=whysoserious", "env": {}}]
    named, escaped, plain, blocked = run_worker(source(), cases, S["files"])
    img = f"https://{JOBURG}/og/1/link.png?{S['link']}&amp;n=Thandi".replace("&amp;", "&")
    assert f'<meta property="og:image" content="{img.replace("&", "&amp;")}">' in named["body"], named["body"][:3000]
    assert f'<meta name="twitter:image" content="{img.replace("&", "&amp;")}">' in named["body"]
    assert '<meta property="og:title" content="Thandi&#x27;s Election Forecast">' in named["body"] or \
        '<meta property="og:title" content="Thandi\'s Election Forecast">' in named["body"]
    assert "from=1" not in re.search(r'og:image" content="([^"]*)"', named["body"]).group(1)
    assert "t=1" not in re.search(r'og:url" content="([^"]*)"', named["body"]).group(1)
    assert "<b>" not in escaped["body"].split("</head>")[0] or "&lt;b&gt;" in escaped["body"]
    page = (ROOT / "site/your-forecast/index.html").read_text(encoding="utf-8")
    assert plain["body"] == "asset:/your-forecast/" or plain["body"] == page   # no forecast: untouched
    assert "My Election Forecast" in blocked["body"] and "whysoserious&#x27;s" not in blocked["body"]
    assert dict(blocked["headers"]).get("x-robots-tag") == NOINDEX
    assert not any(r["logs"] or r["points"] for r in (named, escaped, plain, blocked))


def test_the_image_asks_the_seat_worker_and_falls_back_to_the_generic_image():
    """No binding, a failing seat Worker, an incomplete answer and an
    unreadable link each answer 302 to /og.png, never an error. The seat
    Worker is asked for the link's picks, never seats from the link, with the
    published draws' hash."""
    S = _share_setup()
    base = f"https://{JOBURG}/og/1/link.png?{S['link']}&n=Thandi&seats=999"
    ok = {"status": 200, "body": {"seats": {}, "outcome": {}}}
    cases = [{"url": base, "env": {}},
             {"url": base, "env": {}, "seats": {"status": 500, "body": {}}},
             {"url": base, "env": {}, "seats": ok},
             {"url": f"https://{JOBURG}/og/1/link.png?v=1&c=x&f=AAAA", "env": {}, "seats": ok},
             {"url": f"https://{PREVIEW_HOSTS[0]}/og/1/story.png?{S['link']}", "env": {}, "seats": ok}]
    runs = run_worker(source(), cases, S["files"])
    for r in runs:
        h = dict(r["headers"])
        assert r["status"] == 302 and h.get("location", "").endswith("/og.png"), (r["url"], r["status"], h, r["error"])
        assert h.get("cache-control") == "no-store" and not r["error"] and not r["logs"] and not r["points"]
    assert runs[0]["seatCalls"] == [] and runs[3]["seatCalls"] == []
    call = runs[2]["seatCalls"][0]
    assert call["url"] == "https://seats/v1/card"
    assert set(call["body"]) == {"seats", "coalition", "draws_sha256"}
    assert call["body"]["draws_sha256"] == S["data"]["draws_sha256"]
    assert call["body"]["coalition"] == S["top"]
    wards = S["data"]["schema"]["x-seat-context"]["wards"]
    assert call["body"]["seats"]["ward_winners"] == dict(zip(wards, S["calls"]))
    assert "999" not in json.dumps(call["body"])
    assert dict(runs[4]["headers"]).get("x-robots-tag") == NOINDEX


SEAL = f"https://{JOBURG}/seal/1"


def _seal_cases(S, now, env, **body):
    return {"url": SEAL, "method": "POST", "now": now, "env": env,
            "body": {"v": "1", "c": S["data"]["context_ref"], "f": S["f"], "n": "Thandi", **body}}


def seal_problems(src: str, overrides: dict | None = None) -> list[str]:
    S = _share_setup()
    from datetime import datetime
    opens = int(datetime.fromisoformat(S["data"]["election"]["polls_open"]).timestamp() * 1000)
    key = {"SEAL_KEY": TEST_SEAL_KEY}
    before, after = opens - 86_400_000, opens
    out = []
    made = run_worker(src, [_seal_cases(S, before, key)], S["files"], overrides)[0]
    if made["status"] != 200:
        return [f"seal: {made['status']} {made['body']}"]
    s = json.loads(made["body"])["s"]
    check = lambda **b: {**_seal_cases(S, before, key, **{"s": s, **b}), "url": SEAL + "/check"}
    runs = run_worker(src, [
        check(),                                   # sealed, before polls
        check(f=S["f2"]),                          # another forecast under this seal
        check(n="Kgomotso"),                       # relabelled
        check(s=s[:-2] + ("AA" if not s.endswith("AA") else "BB")),   # forged signature
        check(s=""),                               # unsigned
        _seal_cases(S, after, key),                # polls open: refused
        _seal_cases(S, before, {}),                # no key: not set up
        _seal_cases(S, before, key, f="AAAA"),     # not a forecast
        _seal_cases(S, before, key, n="the model"),  # a name the cards refuse
        {k: v for k, v in _seal_cases(S, before, key).items() if k != "body"} | {"method": "GET"},
        {**check(), "env": {"SEAL_KEY": "another-key"}},   # another key
        {**_seal_cases(S, before, key), "url": f"https://{PREVIEW_HOSTS[1]}/seal/1"},        # a preview: refused
        {**check(), "url": f"https://{PREVIEW_HOSTS[1]}/seal/1/check"},                       # a preview still checks
    ], S["files"], overrides)
    unsealed = {"sealed": False, "at": None, "before_polls": False, "readable": True}
    want = [(200, {"sealed": True, "at": datetime.fromtimestamp(before // 1000 * 1000 / 1000).astimezone().isoformat(), "before_polls": True}),
            (200, unsealed)] + \
        [(200, unsealed)] * 3 + \
        [(403, None), (503, None), (400, None), (400, None), (405, None),
         (200, unsealed), (403, None),
         (200, {"sealed": True, "at": None, "before_polls": True})]
    for r, (status, body) in zip(runs, want):
        got = json.loads(r["body"]) if r["body"] else None
        if r["status"] != status:
            out.append(f"{r['url']}: {r['status']} {r['body'][:200]}, want {status}")
        elif body is not None:
            if body["sealed"]:
                if not (got["sealed"] and got["before_polls"] and got["readable"] is True and
                        abs(datetime.fromisoformat(got["at"].replace("Z", "+00:00")).timestamp() * 1000 - before) < 1000):
                    out.append(f"check: {got}, want sealed at {before}")
            elif got != body:
                out.append(f"check: {got}, want {body}")
        if r["logs"] or r["points"]:
            out.append(f"{r['url']}: logged {r['logs']} wrote {r['points']}")
        if TEST_SEAL_KEY in r["body"]:
            out.append("the key is in a response")
    return out


def test_a_link_is_sealed_before_polls_open_and_its_seal_checks():
    assert seal_problems(source()) == []


def test_seal_check_fires_on_each_constructed_violation():
    edge = (ROOT / "src" / "share-edge.js").read_text(encoding="utf-8")
    seal = (ROOT / "src" / "seal.js").read_text(encoding="utf-8")
    src = source()
    for a, b in (("if (!(now < opens))", "if (false)"),
                 ('if (fields.n !== "" && cardName(fields.n) !== fields.n)', "if (false)"),
                 ('if (preview) return json(', 'if (false) return json(')):
        assert edge.count(a) == 1, a
        assert seal_problems(src, {"share-edge.js": edge.replace(a, b)}), f"blind to {b!r}"
    for a, b in (('return [SEAL_VERSION, String(seconds), ...SEALED_KEYS.map(k => String(fields[k] ?? ""))].join("\\n");',
                  'return [SEAL_VERSION, String(seconds), String(fields.f ?? "")].join("\\n");'),
                 ("return ok ? { sealed: true, at: seconds * 1000 } : no;", "return { sealed: true, at: seconds * 1000 };")):
        assert seal.count(a) == 1, a
        assert seal_problems(src, {"seal.js": seal.replace(a, b)}), f"blind to {b!r}"


def test_the_share_routes_write_nothing_about_the_visitor():
    """The connection's address is read once, in `sealLimited`, and goes
    only into seal.js `rateKey` (an HMAC); tests/test_entries.py shows it
    reaches no response, log, statement or limiter key in the clear."""
    edge = (ROOT / "src" / "share-edge.js").read_text(encoding="utf-8")
    assert edge.count("writeDataPoint(") == 1 and edge.count("console.log(") == 1
    limited = edge[edge.index("async function sealLimited"):]
    limited = limited[:limited.index("\n}\n") + 3]
    assert edge.count("CF-Connecting-IP") == 1 and limited.count(
        'rateKey(env.SEAL_KEY, request.headers.get("CF-Connecting-IP") || "")') == 1
    rest = edge.replace(limited, "")
    for leak in ("CF-Connecting-IP", "cf-connecting-ip", "User-Agent", "user-agent", "request.cf",
                 "headers.get(\"cookie\")", "SEAL_KEY)", "console.log(url", "console.log(q",
                 "console.error(url", "console.error(q", "console.error(e", "console.error(row"):
        assert leak not in rest.replace("env.SEAL_KEY)", ""), leak
    for line in re.findall(r"console\.error\((.*)\);", edge):
        assert re.fullmatch(r'\{ event: "[a-z_]+", [a-z]+: false(, reason: "[a-z A-Z]+")? \}', line), line
