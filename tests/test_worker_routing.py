"""`src/worker.js` hostname routing: live unchanged, staging serves Joburg
unindexed, /go redirects (UAT/staging Worker, 2026-09-30).

Before this change every `*.workers.dev` host, every `wrangler versions upload`
preview URL and any staging hostname fell through to the city-directory lookup
(first hostname label as a city slug), found nothing, and served the portal.

The worker is run for real under node, with `env.ASSETS` stubbed by a fake that
records every URL it is asked for and answers 200 for a fixed asset set, 404
otherwise (so the portal fallback is exercised). Three detectors, each a
function returning a list of problems:

* `live_diffs`       — DIFFERENTIAL against the worker as it was at BASELINE,
                       over every live hostname in `wrangler.toml` plus built
                       and unbuilt city subdomains, times a path set. Compares
                       status, headers, body and every asset URL requested.
* `staging_problems` — every staging-class host serves the requested path
                       from the asset root and carries X-Robots-Tag.
* `go_problems`      — /go and /go/ answer 302 to the exact campaign URL on
                       the live Joburg host and on staging, and fetch nothing.

Each is shown to fire on a mutated worker source and to be quiet on the real
one (CLAUDE.md §4). `staging_config_problems` does the same for
`wrangler.staging.toml` against `wrangler.toml`.
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
#: The commit the staging branch was cut from: the last worker.js with no
#: staging branch and no /go. Live behaviour must equal this one's.
BASELINE = "749d5ec"

GO_LOCATION = "/?utm_source=billboard&utm_medium=dooh&utm_campaign=lge2026"
NOINDEX = "noindex, nofollow"

#: What the fake asset layer holds. Paths with no extension stand for what the
#: real layer serves at an extensionless URL.
ASSETS = ["/", "/index.html", "/forecast", "/about.html", "/portal",
          "/logos/ANC.png", "/robots.txt", "/share.jpg",
          "/tshwane/index.html", "/tshwane/forecast"]

#: /go and /go/ are the one intended change on live Joburg; they are tested by
#: go_problems and excluded from the differential. Near misses stay in.
GO_PATHS = ["/go", "/go/"]
LIVE_PATHS = ["/", "/index.html", "/forecast", "/about.html", "/nope",
              "/logos/ANC.png", "/robots.txt", "/share.jpg", "/?x=1",
              "/go/x", "/gone", "/go.html"]

DRIVER = r"""
import { readFileSync } from "node:fs";
const [workerPath, casesPath] = process.argv.slice(2);
const worker = (await import("file://" + workerPath)).default;
const { assets, cases } = JSON.parse(readFileSync(casesPath, "utf8"));
const have = new Set(assets);
const out = [];
for (const c of cases) {
  const fetched = [];
  const env = { ...c.env, ASSETS: { async fetch(req) {
    const u = new URL(req.url);
    fetched.push(u.pathname + u.search);
    const hit = have.has(u.pathname);
    return new Response(hit ? "asset:" + u.pathname : "missing",
      { status: hit ? 200 : 404, headers: { "x-asset": u.pathname } });
  } } };
  const res = await worker.fetch(new Request(c.url), env);
  out.push({ url: c.url, env: c.env, status: res.status,
             headers: [...res.headers].sort(), body: await res.text(), fetched });
}
process.stdout.write(JSON.stringify(out));
"""


def _node() -> str:
    node = shutil.which("node")
    if not node:
        skip("node is not installed; src/worker.js cannot be run")
    return node


def run_worker(source: str, cases: list[dict]) -> list[dict]:
    """Run `source` (worker.js text) over `cases` ({url, env}) under node."""
    node = _node()
    with tempfile.TemporaryDirectory() as t:
        w, d, c = Path(t, "worker.mjs"), Path(t, "driver.mjs"), Path(t, "cases.json")
        w.write_text(source, encoding="utf-8")
        d.write_text(DRIVER, encoding="utf-8")
        c.write_text(json.dumps({"assets": ASSETS, "cases": cases}), encoding="utf-8")
        p = subprocess.run([node, str(d), str(w), str(c)], capture_output=True,
                           text=True, timeout=60)
    assert p.returncode == 0, p.stderr
    return json.loads(p.stdout)


def baseline_source() -> str:
    p = subprocess.run(["git", "show", f"{BASELINE}:src/worker.js"], cwd=ROOT,
                       capture_output=True, text=True)
    assert p.returncode == 0, f"cannot read the baseline worker: {p.stderr}"
    assert "STAGING" not in p.stdout and "/go" not in p.stdout, "wrong baseline"
    return p.stdout


def live_hosts() -> list[str]:
    routes = tomllib.loads((ROOT / "wrangler.toml").read_text())["routes"]
    return [r["pattern"] for r in routes] + ["tshwane.whysoserious.city",
                                             "capetown.whysoserious.city"]


def live_cases() -> list[dict]:
    return [{"url": f"https://{h}{p}", "env": {}} for h in live_hosts() for p in LIVE_PATHS]


STAGING_CASES = (
    [{"url": f"https://{h}{p}", "env": {}}
     for h in ("joburg-whysoserious.acct.workers.dev",           # live's workers.dev
               "3f2a91bc-joburg-whysoserious.acct.workers.dev",  # versions upload
               "uat-joburg.whysoserious.city")                   # staging domain
     for p in LIVE_PATHS]
    + [{"url": f"https://{h}{p}", "env": {"STAGING": "1"}}
       for h in ("joburg-whysoserious-staging.acct.workers.dev",
                 "uat-joburg.whysoserious.city", "whysoserious.city",
                 "tshwane.whysoserious.city")
       for p in LIVE_PATHS])


def live_diffs(new: str, old: str) -> list[str]:
    cases = live_cases()
    a, b = run_worker(old, cases), run_worker(new, cases)
    return [f"{x['url']}: {x} != {y}" for x, y in zip(a, b) if x != y]


def staging_problems(source: str) -> list[str]:
    out = []
    for r in run_worker(source, STAGING_CASES):
        u = re.sub(r"^https://[^/]+", "", r["url"])
        h = dict(r["headers"])
        if h.get("x-robots-tag") != NOINDEX:
            out.append(f"{r['url']} {r['env']}: X-Robots-Tag {h.get('x-robots-tag')!r}")
        if r["fetched"] != [u]:
            out.append(f"{r['url']} {r['env']}: fetched {r['fetched']}, want [{u!r}]")
    return out


def go_problems(source: str) -> list[str]:
    hosts = [("joburg.whysoserious.city", {}, False),
             ("joburg-whysoserious.acct.workers.dev", {}, True),
             ("joburg-whysoserious-staging.acct.workers.dev", {"STAGING": "1"}, True),
             ("uat-joburg.whysoserious.city", {"STAGING": "1"}, True)]
    cases = [{"url": f"https://{h}{p}", "env": e} for h, e, _ in hosts for p in GO_PATHS]
    out = []
    for r, (host, _e, staged) in zip(run_worker(source, cases),
                                     [x for x in hosts for _ in GO_PATHS]):
        h = dict(r["headers"])
        want = f"https://{host}{GO_LOCATION}"
        if r["status"] != 302 or h.get("location") != want or r["fetched"]:
            out.append(f"{r['url']}: {r['status']} {h.get('location')!r} "
                       f"fetched {r['fetched']}")
        if staged != (h.get("x-robots-tag") == NOINDEX):
            out.append(f"{r['url']}: X-Robots-Tag {h.get('x-robots-tag')!r}")
    return out


def _mutate(source: str, old: str, new: str) -> str:
    assert source.count(old) == 1, f"mutation anchor not unique: {old!r}"
    return source.replace(old, new)


# ---------------------------------------------------------------- live

def test_the_live_population_is_the_one_wrangler_routes():
    hosts = live_hosts()
    routed = {r["pattern"] for r in tomllib.loads((ROOT / "wrangler.toml").read_text())["routes"]}
    assert routed <= set(hosts) and {"joburg.whysoserious.city", "whysoserious.city",
                                     "www.whysoserious.city"} <= routed, routed
    n = len(live_cases())
    assert 40 <= n <= 200, n
    assert not set(GO_PATHS) & set(LIVE_PATHS)


def test_live_routing_matches_the_baseline_worker():
    old = baseline_source()
    # the differential looked: the baseline exercised the portal, the root,
    # the city directory and the unbuilt-city fallback
    fetched = {f for r in run_worker(old, live_cases()) for f in r["fetched"]}
    assert {"/portal", "/", "/tshwane/index.html", "/capetown/index.html"} <= fetched, fetched
    assert live_diffs(WORKER.read_text(encoding="utf-8"), old) == []


def test_live_differential_fires_on_a_changed_live_route():
    src, old = WORKER.read_text(encoding="utf-8"), baseline_source()
    for a, b in ((' || host.endsWith(".workers.dev")', ' || host.endsWith(".city")'),
                 ('["uat-joburg.whysoserious.city"]', '["www.whysoserious.city"]'),
                 ('if (ROOT_CITIES.has(sub) && GO_PATHS.has(path))',
                  'if (ROOT_CITIES.has(sub) && path.startsWith("/go"))')):
        assert live_diffs(_mutate(src, a, b), old), f"differential blind to {b!r}"


def test_live_joburg_is_never_noindexed():
    for r in run_worker(WORKER.read_text(encoding="utf-8"), live_cases()):
        assert "x-robots-tag" not in dict(r["headers"]), r["url"]


# ---------------------------------------------------------------- staging

def test_staging_hosts_serve_joburg_with_noindex():
    assert len(STAGING_CASES) == 7 * len(LIVE_PATHS)
    assert staging_problems(WORKER.read_text(encoding="utf-8")) == []


def test_staging_check_fires_without_the_header_or_on_portal_routing():
    src = WORKER.read_text(encoding="utf-8")
    no_header = _mutate(src, '      out.headers.set("X-Robots-Tag", NOINDEX);\n', "")
    found = staging_problems(no_header)
    assert len(found) == len(STAGING_CASES), found[:3]
    no_workers_dev = _mutate(src, ' || host.endsWith(".workers.dev")', "")
    found = staging_problems(no_workers_dev)
    assert found and all("workers.dev" in f for f in found), found[:3]
    # the baseline worker is the defect this change repairs
    assert staging_problems(baseline_source())


# ---------------------------------------------------------------- /go

def test_go_redirects_to_the_campaign_url():
    assert go_problems(WORKER.read_text(encoding="utf-8")) == []


def test_go_check_fires_on_a_wrong_target_or_status():
    src = WORKER.read_text(encoding="utf-8")
    for a, b in (("utm_campaign=lge2026", "utm_campaign=lge2027"),
                 ("status: 302", "status: 301"),
                 ('new Set(["/go", "/go/"])', 'new Set(["/go"])')):
        assert go_problems(_mutate(src, a, b)), f"/go check blind to {b!r}"
    assert go_problems(baseline_source())


# ---------------------------------------------------------------- config

def staging_config_problems(live_text: str, staging_text: str, worker: str) -> list[str]:
    live, stg = tomllib.loads(live_text), tomllib.loads(staging_text)
    out = []
    if stg.get("name") in (None, live.get("name")):
        out.append(f"staging name {stg.get('name')!r} is not separate from live")
    for key in ("main", "compatibility_date", "assets", "build"):
        if stg.get(key) != live.get(key):
            out.append(f"{key}: staging {stg.get(key)!r} != live {live.get(key)!r}")
    if stg.get("vars", {}).get("STAGING") != "1":
        out.append("staging does not set vars.STAGING = \"1\"")
    if "STAGING" in live.get("vars", {}):
        out.append("live wrangler.toml sets STAGING: the live site would be noindexed")
    if stg.get("workers_dev") is not True or stg.get("preview_urls") is not True:
        out.append("staging must state workers_dev = true and preview_urls = true")
    for table in ("assets", "vars", "build"):
        if "routes" in stg.get(table, {}):
            out.append(f"routes sits under [{table}] and is ignored")
    routes = stg.get("routes")
    if not routes:
        out.append("staging has no top-level routes")
    live_patterns = {r["pattern"] for r in live.get("routes", [])}
    known = set(re.findall(r'"([^"]+)"', re.search(
        r"STAGING_HOSTS = new Set\(\[(.*?)\]\)", worker).group(1)))
    for r in routes or []:
        if r.get("pattern") in live_patterns:
            out.append(f"staging routes a live hostname: {r['pattern']}")
        if r.get("pattern") not in known:
            out.append(f"{r.get('pattern')} is not in worker.js STAGING_HOSTS")
    return out


def _configs() -> tuple[str, str, str]:
    return ((ROOT / "wrangler.toml").read_text(encoding="utf-8"),
            (ROOT / "wrangler.staging.toml").read_text(encoding="utf-8"),
            WORKER.read_text(encoding="utf-8"))


def test_staging_config_restates_live_and_differs_only_where_it_must():
    assert staging_config_problems(*_configs()) == []


def test_staging_config_check_fires_on_each_constructed_violation():
    live, stg, worker = _configs()
    routes = ('routes = [\n  { pattern = "uat-joburg.whysoserious.city", '
              'custom_domain = true }\n]\n')
    assert routes in stg
    buried = stg.replace(routes, "") + "routes = [{ pattern = \"x\" }]\n"
    cases = {
        "under [assets]": (live, buried, worker),
        "live name": (live, stg.replace('name = "joburg-whysoserious-staging"',
                                        'name = "joburg-whysoserious"'), worker),
        "live host": (live, stg.replace("uat-joburg.whysoserious.city",
                                        "joburg.whysoserious.city"), worker),
        "live STAGING": (live + '\n[vars]\nSTAGING = "1"\n', stg, worker),
        "assets drift": (live, stg.replace("run_worker_first = true",
                                           "run_worker_first = false"), worker),
        "no var": (live, stg.replace('STAGING = "1"', 'STAGING = "0"'), worker),
        "unknown host": (live, stg, worker.replace('"uat-joburg.whysoserious.city"',
                                                   '"uat.whysoserious.city"')),
    }
    for name, args in cases.items():
        assert staging_config_problems(*args), f"config check blind to {name}"
