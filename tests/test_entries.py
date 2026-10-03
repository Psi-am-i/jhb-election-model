"""Entries: every sealed forecast stored at sealing (owner, 2026-10-03).

The site's Worker (src/share-edge.js) inserts one row per successful seal into
the D1 database bound as ENTRIES, rate-limits /seal/1 with the SEAL_LIMIT
binding, and answers GET /entries/1/count. Run through the real worker under
node, with the fake D1 and the fake limiter of tests/test_worker_routing.py's
DRIVER (one of each per run, so cases see each other's rows and counts).

Detectors, each shown quiet on the real source and firing on a constructed
violation (CLAUDE.md §4):

* `entry_problems`  — a seal inserts exactly one row, whose columns are the
                      migration's and whose values are the seal's; a repeat of
                      the same seal inserts nothing new; a refused seal inserts
                      nothing; a failed or missing insert still returns the
                      seal and logs the reason only.
* `count_problems`  — the count endpoint answers the number of rows, kept
                      COUNT_MAX_AGE_S seconds; 503 without the binding or when
                      the read fails; GET only.
* `limit_problems`  — the limiter refuses the seal past its limit with 429 and
                      the reader's sentence, keyed by an HMAC of the address,
                      not the address; another address, and a new period,
                      pass; a preview is refused before it is counted.

Also here: the columns, both directions (migration, ENTRY_COLUMNS, the row
the fake D1 recorded); the privacy page's account of entries; the config.
"""
from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT, run_module  # noqa: E402
import test_worker_routing as W  # noqa: E402

EDGE = ROOT / "src" / "share-edge.js"
MIGRATION = ROOT / "migrations" / "0001_entries.sql"
PRIVACY = ROOT / "docs-public" / "privacy.md"
COUNT = f"https://{W.JOBURG}/entries/1/count"
#: An address and a user agent no stored or logged value may contain.
IP, UA = "203.0.113.7", "UA-test-agent/9"


def edge() -> str:
    return EDGE.read_text(encoding="utf-8")


def js_list(src: str, name: str) -> list[str]:
    m = re.search(rf"export const {name} = \[([^\]]*)\];", src)
    assert m, name
    return re.findall(r'"([a-z_]+)"', m.group(1))


def migration_columns(text: str | None = None) -> list[str]:
    text = text if text is not None else MIGRATION.read_text(encoding="utf-8")
    body = re.search(r"CREATE TABLE entries \((.*?)\n\);", text, re.S).group(1)
    return [ln.split()[0] for ln in body.splitlines()
            if ln.strip() and not ln.strip().startswith("--")]


def _seal(S, now, *, n="Thandi", f=None, host=W.JOBURG, entries="record", limit=None, ip=IP):
    case = {"url": f"https://{host}/seal/1", "method": "POST", "now": now,
            "env": {"SEAL_KEY": W.TEST_SEAL_KEY},
            "headers": {"content-type": "application/json", "CF-Connecting-IP": ip, "User-Agent": UA},
            "body": {"v": "1", "c": S["data"]["context_ref"], "f": f or S["f"], "n": n}}
    if entries:
        case["entries"] = entries
    if limit:
        case["limit"] = limit
    return case


def _times(S):
    from datetime import datetime
    opens = int(datetime.fromisoformat(S["data"]["election"]["polls_open"]).timestamp() * 1000)
    return opens - 86_400_000, opens


def _leaks(r) -> list[str]:
    blob = json.dumps({k: r[k] for k in ("body", "logs", "errors", "statements", "rows", "limitKeys", "headers")})
    return [f"{r['url']}: {x!r} reached the output" for x in (IP, UA, W.TEST_SEAL_KEY) if x in blob]


# ---------------------------------------------------------------- inserts

def entry_problems(src: str, overrides: dict | None = None) -> list[str]:
    S = W._share_setup()
    before, after = _times(S)
    out = []
    runs = W.run_worker(src, [
        _seal(S, before),                                  # 0 stored
        _seal(S, before),                                  # 1 the same seal again: nothing new
        _seal(S, before + 1000, n=""),                     # 2 unnamed, a second later: a second row
        _seal(S, before, f=S["f2"]),                       # 3 another forecast: a third row
        _seal(S, after),                                   # 4 polls open: refused, nothing stored
        _seal(S, before, n="the model"),                   # 5 a name the cards refuse
        _seal(S, before, host=W.PREVIEW_HOSTS[1]),         # 6 a preview: refused
        _seal(S, before + 2000, entries="throw"),          # 7 D1 fails: the seal stands
        _seal(S, before + 3000, entries=None),             # 8 no binding: the seal stands
    ], S["files"], overrides)
    want_status = [200, 200, 200, 200, 403, 400, 403, 200, 200]
    for i, (r, st) in enumerate(zip(runs, want_status)):
        if r["status"] != st:
            out.append(f"case {i}: {r['status']} {r['body'][:200]}, want {st}")
        out += _leaks(r)
        if r["logs"] or r["points"]:
            out.append(f"case {i}: logged {r['logs']} wrote {r['points']}")
    if out:
        return out
    seals = [json.loads(r["body"])["s"] for r in runs if r["status"] == 200]
    cols = js_list(src_edge(overrides), "ENTRY_COLUMNS")
    rows = runs[-1]["rows"]
    if len(rows) != 3:
        out.append(f"{len(rows)} rows after three distinct seals, a repeat and four refusals: {rows}")
    want_inserts = [1, 1, 1, 1, 0, 0, 0, 1, 0]
    for i, (r, n) in enumerate(zip(runs, want_inserts)):
        got = [s for s in r["statements"] if s["sql"].startswith("INSERT")]
        if len(got) != n:
            out.append(f"case {i}: {len(got)} inserts, want {n}")
    data = S["data"]
    by_id = {row["seal_id"]: row for row in rows}
    for k, (s, n, f) in enumerate(((seals[0], "Thandi", S["f"]), (seals[2], "", S["f"]),
                                   (seals[3], "Thandi", S["f2"]))):
        t, sig = s.split(".")
        row = by_id.get(sig)
        if row is None:
            out.append(f"seal {k}: no row for {sig}")
            continue
        if list(row) != cols:
            out.append(f"seal {k}: columns {list(row)}, want {cols}")
        want = {"seal_id": sig, "sealed_at": int(t, 36), "label": n, "model_ref": data["model_ref"],
                "context_ref": data["context_ref"], "state": f}
        for c, v in want.items():
            if row.get(c) != v:
                out.append(f"seal {k}: {c} = {row.get(c)!r}, want {v!r}")
        body = json.loads(row["forecast"])
        wards = data["schema"]["x-ward-ids"]
        if len(body.get("ward_calls", [])) != len(wards) or set(body.get("combined_share", {})) != \
                set(data["schema"]["x-seat-context"]["parties"]):
            out.append(f"seal {k}: the forecast is not in the stored shape: {sorted(body)}")
        if k == 0 and (body["ward_calls"] != S["calls"] or body["coalition"] != S["top"]):
            out.append("seal 0: the stored forecast is not the link's")
    if seals[0] != seals[1]:
        out.append("the same fields in the same second sealed differently")
    if runs[7]["errors"] != [{"event": "entry", "stored": False, "reason": "insert failed"}]:
        out.append(f"a failed insert logged {runs[7]['errors']}")
    if runs[8]["errors"] != [{"event": "entry", "stored": False, "reason": "no ENTRIES binding"}]:
        out.append(f"a missing binding logged {runs[8]['errors']}")
    if any(r["errors"] for r in runs[:7]):
        out.append(f"errors logged on a stored or refused seal: {[r['errors'] for r in runs[:7]]}")
    return out


def src_edge(overrides: dict | None) -> str:
    return (overrides or {}).get("share-edge.js", edge())


def test_every_seal_is_stored_once_and_a_failed_insert_keeps_the_seal():
    assert entry_problems(W.source()) == []


def test_entry_check_fires_on_each_constructed_violation():
    e, src = edge(), W.source()
    for a, b in (
        ("const stored = storeEntry(env, () => entryRow(s, fields, read, got.D));", "const stored = null;"),
        ('"INSERT OR IGNORE INTO entries ("', '"INSERT INTO entries ("'),
        ("  } catch {\n    console.error({ event: \"entry\", stored: false, reason: \"insert failed\" });\n  }",
         "  } finally {}"),
        ("[sig, parseInt(t, 36), fields.n,", "[sig, parseInt(t, 36), \"\","),
        ("JSON.stringify(B.forecastBody(got.state, D.ctx, { coalition: got.coalition }))",
         "JSON.stringify(B.forecastBody(got.state, D.ctx, {}))"),
    ):
        assert e.count(a) == 1, a
        assert entry_problems(src, {"share-edge.js": e.replace(a, b)}), f"blind to {b!r}"
    # an entry that also keeps the address
    a = 'export const ENTRY_COLUMNS = ["seal_id",'
    leaky = e.replace(a, 'export const ENTRY_COLUMNS = ["ip", "seal_id",').replace(
        "  return [sig, parseInt(t, 36),", "  return [globalThis.__ip, sig, parseInt(t, 36),").replace(
        "async function sealLimited(request, env) {",
        "async function sealLimited(request, env) {\n  globalThis.__ip = request.headers.get(\"CF-Connecting-IP\");")
    assert entry_problems(src, {"share-edge.js": leaky})


def row_failure_problems(src: str, overrides: dict | None = None) -> list[str]:
    """A row that cannot be built fails the entry, not the seal: the seal is
    returned, nothing is inserted, and the reason alone is logged."""
    S = W._share_setup()
    before, _ = _times(S)
    e = src_edge(overrides)
    broken = e.replace("export function entryRow(s, fields, got, D) {",
                       "export function entryRow(s, fields, got, D) {\n  throw new Error(\"no row\");", 1)
    r = W.run_worker(src, [_seal(S, before)], S["files"], {**(overrides or {}), "share-edge.js": broken})[0]
    out = []
    if r["status"] != 200 or "s" not in json.loads(r["body"] or "{}"):
        out.append(f"a row that cannot be built failed the seal: {r['status']} {r['body'][:120]}")
    if [s for s in r["statements"] if s["sql"].startswith("INSERT")]:
        out.append("a row that cannot be built was inserted")
    if r["errors"] != [{"event": "entry", "stored": False, "reason": "row failed"}]:
        out.append(f"a row that cannot be built logged {r['errors']}")
    return out + _leaks(r)


def test_a_row_that_cannot_be_built_keeps_the_seal():
    assert row_failure_problems(W.source()) == []
    e = edge()
    a = "storeEntry(env, () => entryRow(s, fields, read, got.D))"
    assert e.count(a) == 1
    # the row built before the guard, as first written: the seal fails
    old = e.replace(a, "storeEntry(env, (row => () => row)(entryRow(s, fields, read, got.D)))")
    assert row_failure_problems(W.source(), {"share-edge.js": old})


def test_a_stored_forecast_is_seated_by_the_scorer_as_the_link_called_it():
    """The seam between the Worker and results night: the forecast the Worker
    stores goes through score_forecasts.seat_forecast, on the live schema, with
    each ward's call where the link put it."""
    import score_forecasts
    S = W._share_setup()
    before, _ = _times(S)
    r = W.run_worker(W.source(), [_seal(S, before)], S["files"])[0]
    assert r["status"] == 200 and len(r["rows"]) == 1, r["body"]
    schema = S["data"]["schema"]
    seated = score_forecasts.seat_forecast(json.loads(r["rows"][0]["forecast"]), schema)
    assert seated["ok"], seated.get("errors")
    want = dict(zip(schema["x-seat-context"]["wards"], S["calls"]))
    assert seated["ward_winners"] == want
    assert [str(w) for w in schema["x-ward-ids"]] == [str(w) for w in schema["x-seat-context"]["wards"]]


# ---------------------------------------------------------------- columns

def column_problems(migration: list[str], declared: list[str]) -> list[str]:
    out = []
    if migration != declared:
        out.append(f"the migration's columns {migration} are not ENTRY_COLUMNS {declared}")
    for c in set(migration) | set(declared):
        if re.search(r"ip|agent|cookie|user|account|email|phone|address|country", c):
            out.append(f"column {c!r} stores something about the person")
    return out


def test_the_table_holds_exactly_the_entry_columns_both_ways():
    cols = js_list(edge(), "ENTRY_COLUMNS")
    assert cols == ["seal_id", "sealed_at", "label", "model_ref", "context_ref", "state", "forecast"]
    assert column_problems(migration_columns(), cols) == []
    # the insert names them in that order
    assert 'ENTRY_INSERT = "INSERT OR IGNORE INTO entries (" + ENTRY_COLUMNS.join(", ")' in edge()
    # constructed violations, each way
    text = MIGRATION.read_text(encoding="utf-8")
    extra = text.replace("  forecast    TEXT NOT NULL", "  forecast    TEXT NOT NULL,\n  ip TEXT")
    assert column_problems(migration_columns(extra), cols)
    assert column_problems(migration_columns(), cols + ["user_agent"])
    assert column_problems(migration_columns(), cols[:-1])
    # the primary key is the seal id, so a repeat cannot insert
    assert re.search(r"seal_id\s+TEXT PRIMARY KEY", text)


# ---------------------------------------------------------------- count

def count_problems(src: str, overrides: dict | None = None) -> list[str]:
    S = W._share_setup()
    before, _ = _times(S)
    out = []
    get = lambda **k: {"url": COUNT, "env": {}, **k}
    runs = W.run_worker(src, [
        get(entries="record"),                         # 0 empty: 0
        _seal(S, before), _seal(S, before + 1000, n=""), _seal(S, before),
        get(entries="record"),                         # 4 two distinct seals: 2
        get(),                                         # 5 no binding: 503
        get(entries="throw"),                          # 6 the read fails: 503
        get(entries="record", method="POST"),          # 7 GET only
        {**get(entries="record"), "url": f"https://{W.PREVIEW_HOSTS[1]}/entries/1/count"},  # 8 preview reads
    ], S["files"], overrides)
    want = [(200, 0), None, None, None, (200, 2), (503, None), (503, None), (405, None), (200, 2)]
    for i, (r, w) in enumerate(zip(runs, want)):
        if w is None:
            continue
        if r["status"] != w[0]:
            out.append(f"count case {i}: {r['status']} {r['body'][:120]}, want {w[0]}")
            continue
        h = dict(r["headers"])
        if w[0] == 200:
            if json.loads(r["body"]) != {"count": w[1]}:
                out.append(f"count case {i}: {r['body']}, want {w[1]}")
            if h.get("cache-control") != "public, max-age=60":
                out.append(f"count case {i}: Cache-Control {h.get('cache-control')!r}")
        if r["logs"] or r["points"]:
            out.append(f"count case {i}: logged {r['logs']}")
    if runs[5]["errors"]:
        out.append(f"no binding is not a failed read, but logged {runs[5]['errors']}")
    if runs[6]["errors"] != [{"event": "entry_count", "read": False}]:
        out.append(f"a failed count logged {runs[6]['errors']}")
    return out


def test_the_count_endpoint_answers_the_number_of_entries():
    assert count_problems(W.source()) == []
    assert re.search(r"export const COUNT_MAX_AGE_S = 60;", edge())


def test_count_check_fires_on_each_constructed_violation():
    e, src = edge(), W.source()
    for a, b in (
        ('"public, max-age=" + COUNT_MAX_AGE_S', '"no-store"'),
        ("n = Number((await env.ENTRIES.prepare(COUNT_SELECT).first()).n);", "n = 1;"),
        ('if (!env.ENTRIES) return json({ error: "entries are not set up" }, 503);', ""),
        ("  if (path === COUNT_PATH) return entryCount(request, env, url, ctx);\n", ""),
    ):
        assert e.count(a) == 1, a
        assert count_problems(src, {"share-edge.js": e.replace(a, b)}), f"blind to {b!r}"


# ---------------------------------------------------------------- rate limit

def limit_problems(src: str, overrides: dict | None = None) -> list[str]:
    S = W._share_setup()
    before, _ = _times(S)
    out = []
    lim = 3
    runs = W.run_worker(src, [
        *[_seal(S, before + i * 1000, limit=lim) for i in range(lim + 1)],   # 0-3: the fourth refused
        _seal(S, before, limit=lim, ip="198.51.100.9"),                       # 4 another address passes
        _seal(S, before + 9000, limit=lim, host=W.PREVIEW_HOSTS[1]),          # 5 preview: 403, not counted
    ], S["files"], overrides)
    want = [200] * lim + [429, 200, 403]
    for i, (r, st) in enumerate(zip(runs, want)):
        if r["status"] != st:
            out.append(f"limit case {i}: {r['status']} {r['body'][:120]}, want {st}")
        out += _leaks(r)
    if runs[lim]["status"] == 429:
        if json.loads(runs[lim]["body"]).get("error") != re.search(
                r'export const RATE_LIMITED = "([^"]+)";', src_edge(overrides)).group(1):
            out.append(f"429 body {runs[lim]['body']}")
        if [s for s in runs[lim]["statements"] if s["sql"].startswith("INSERT")]:
            out.append("a refused seal was stored")
    keys = [r["limitKeys"] for r in runs]
    if any(len(k) != 1 for k in keys[:5]) or keys[5]:
        out.append(f"limiter calls per case: {keys}")
    else:
        if len({k[0] for k in keys[:lim + 1]}) != 1 or keys[4][0] == keys[0][0]:
            out.append(f"the key is not one per address: {keys}")
        if not re.fullmatch(r"[A-Za-z0-9_-]{22}", keys[0][0]):
            out.append(f"the key is not an HMAC: {keys[0][0]!r}")
    # a new period: a fresh limiter passes the same address again
    again = W.run_worker(src, [_seal(S, before + 20_000, limit=lim)], S["files"], overrides)[0]
    if again["status"] != 200:
        out.append(f"a new period: {again['status']}, want 200")
    # no limiter bound: nothing limited
    free = W.run_worker(src, [_seal(S, before + i * 1000) for i in range(lim + 2)], S["files"], overrides)
    if any(r["status"] != 200 for r in free):
        out.append(f"without SEAL_LIMIT: {[r['status'] for r in free]}")
    return out


def test_the_rate_limit_fires_past_its_limit_and_quiets_for_others():
    assert limit_problems(W.source()) == []


def test_limit_check_fires_on_each_constructed_violation():
    e, src = edge(), W.source()
    s = (ROOT / "src" / "seal.js").read_text(encoding="utf-8")
    for a, b in (
        ('if (request.method === "POST" && await sealLimited(request, env)) return json({ error: RATE_LIMITED }, 429);', ""),
        ("  return !success;", "  return false;"),
        ('rateKey(env.SEAL_KEY, request.headers.get("CF-Connecting-IP") || "")',
         'request.headers.get("CF-Connecting-IP") || ""'),
    ):
        assert e.count(a) == 1, a
        assert limit_problems(src, {"share-edge.js": e.replace(a, b)}), f"blind to {b!r}"
    a = 'enc.encode("rate1\\n" + rateAddress(address))'
    assert s.count(a) == 1
    assert limit_problems(src, {"seal.js": s.replace(a, "enc.encode(\"rate1\")")})


#: Two addresses in one /64, written differently, and one in the next /64.
V6_SAME = ("2001:db8:0:1::7", "2001:0db8:0000:0001:ffff:ffff:ffff:ffff")
V6_NEXT = "2001:db8:0:2::7"


def v6_problems(src: str, overrides: dict | None = None) -> list[str]:
    """An IPv6 connection is counted by its /64; IPv4 by its whole address;
    a limiter that fails lets the seal through and logs the reason alone."""
    S = W._share_setup()
    before, _ = _times(S)
    runs = W.run_worker(src, [
        _seal(S, before, limit=1, ip=V6_SAME[0]),            # 0 counted
        _seal(S, before + 1000, limit=1, ip=V6_SAME[1]),     # 1 same /64: refused
        _seal(S, before + 2000, limit=1, ip=V6_NEXT),        # 2 next /64: passes
        _seal(S, before + 3000, limit=1, ip="203.0.113.8"),  # 3 IPv4 neighbours are
        _seal(S, before + 4000, limit=1, ip="203.0.113.9"),  # 4 counted apart
        _seal(S, before + 5000, limit="throw"),              # 5 the limiter fails: sealed
    ], S["files"], overrides)
    out = []
    for i, (r, st) in enumerate(zip(runs, [200, 429, 200, 200, 200, 200])):
        if r["status"] != st:
            out.append(f"v6 case {i}: {r['status']} {r['body'][:120]}, want {st}")
        out += _leaks(r)
        blob = json.dumps({k: r[k] for k in ("body", "logs", "errors", "statements", "rows", "limitKeys")})
        out += [f"v6 case {i}: {a!r} reached the output" for a in (*V6_SAME, V6_NEXT) if a in blob]
    if runs[5]["errors"] != [{"event": "seal_limit", "counted": False, "reason": "limiter failed"}]:
        out.append(f"a failed limiter logged {runs[5]['errors']}")
    return out


def test_an_ipv6_connection_is_counted_by_its_slash_64():
    assert v6_problems(W.source()) == []
    e, s = edge(), (ROOT / "src" / "seal.js").read_text(encoding="utf-8")
    a = 'enc.encode("rate1\\n" + rateAddress(address))'
    assert s.count(a) == 1
    assert v6_problems(W.source(), {"seal.js": s.replace(a, 'enc.encode("rate1\\n" + address)')})
    a = '  } catch {\n    console.error({ event: "seal_limit", counted: false, reason: "limiter failed" });\n    return false;\n  }'
    assert e.count(a) == 1
    assert v6_problems(W.source(), {"share-edge.js": e.replace(a, "  } finally {}")})


# ---------------------------------------------------------------- config and text

def entries_config_problems(text: str) -> list[str]:
    cfg = tomllib.loads(text)
    out = []
    want = {"name": "SEAL_LIMIT", "namespace_id": "1003", "simple": {"limit": 30, "period": 60}}
    if cfg.get("ratelimits") != [want]:
        out.append(f"[[ratelimits]] is {cfg.get('ratelimits')}, want [{want}]")
    for d in cfg.get("d1_databases", []):
        if d.get("binding") == "ENTRIES" and (d.get("database_name") != "joburg-entries" or
                                               not re.fullmatch(r"[0-9a-f-]{36}", d.get("database_id", ""))
                                               or d.get("migrations_dir") != "migrations"):
            out.append(f"ENTRIES is declared with {d}")
    for cmd in ("npx wrangler d1 create joburg-entries",
                "npx wrangler d1 migrations apply joburg-entries --remote",
                "# binding = \"ENTRIES\""):
        if cmd not in text:
            out.append(f"the owner's command is missing: {cmd}")
    return out


def test_wrangler_toml_states_the_limit_and_the_owner_commands():
    text = W.WRANGLER.read_text(encoding="utf-8")
    assert entries_config_problems(text) == []
    for a, b in (("limit = 30", "limit = 3000"), ('name = "SEAL_LIMIT"', 'name = "LIMIT"'),
                 ("# binding = \"ENTRIES\"\n# database_name = \"joburg-entries\"\n# database_id = \"<the id `wrangler d1 create` printed>\"",
                  "binding = \"ENTRIES\"\ndatabase_name = \"joburg-entries\"\ndatabase_id = \"placeholder\"")):
        assert text.count(a) == 1, a
        mutant = text.replace(a, b)
        if a.startswith("# binding"):
            mutant = mutant.replace("# [[d1_databases]]", "[[d1_databases]]").replace(
                '# migrations_dir = "migrations"', 'migrations_dir = "migrations"')
        assert entries_config_problems(mutant), f"blind to {b!r}"


PRIVACY_MUST = (
    "## Forecasts entered",
    "the forecast", "the name you typed", "the time of the seal", "the seal's id",
    "the model's version",
    "No IP address, browser details, cookie or account",
    "ninety days after the leaderboard is published",
    "within six months of polling day if no leaderboard is published",
    "the names come off the leaderboard",
    "for up to thirty days after they are deleted",
    "share sheet seals the forecast, and so enters it",
    "the forecast as the link carries it",
    "from the leaderboard",
    "only its first half",
    "public on the leaderboard",
    "psi@whysoserious.city",
    "seal id",
)
PRIVACY_MUST_NOT = ("keeps no record of what it signed", "none of them\nkeeps the forecast",
                    "The site\nstores nothing that names a visitor")


def privacy_problems(text: str) -> list[str]:
    flat = re.sub(r"\s+", " ", text)
    out = [f"privacy.md lacks {m!r}" for m in PRIVACY_MUST if re.sub(r"\s+", " ", m) not in flat]
    out += [f"privacy.md still says {m!r}" for m in PRIVACY_MUST_NOT if re.sub(r"\s+", " ", m) in flat]
    return out


def test_the_privacy_page_says_what_an_entry_holds_and_for_how_long():
    text = PRIVACY.read_text(encoding="utf-8")
    assert privacy_problems(text) == []
    assert privacy_problems(re.sub(r"ninety days after the leaderboard is\s+published", "a while", text))
    assert privacy_problems(re.sub(r"and so enters\s+it", "", text))
    assert privacy_problems(re.sub(r"within six months of\s+polling day", "", text))
    assert privacy_problems(text + "\nThe server keeps no record of what it signed.\n")


if __name__ == "__main__":
    sys.exit(run_module(sys.modules[__name__]))
