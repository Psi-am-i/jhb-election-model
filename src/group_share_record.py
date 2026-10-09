"""The group-share record: what each party has really taken of each voter pool.

BRIEF item 12 (owner, 2026-10-09: "tripwire just tells us but doesnt stop it?
if so yes"). ``run_model`` counts, per draw, each party's share of each pool's
vote (the within-pool split) against a threshold built from this artefact, and
reports the pairs that exceed it in ``41_guards.group_share_tripwire``. It
changes no number. This module builds the artefact; ``montecarlo`` reads the
JSON and never imports this module.

For each city and each target in ``TARGETS``:

* ``record[pool][party]`` — the party's largest Duncan-Davis UPPER bound on its
  share of that pool's vote over this city's real results strictly before the
  target: every local election this module can fit (``pools.fit_city``) and
  every national election after one, on that local election's wards and
  voter composition (carried forward: the national election's own
  composition is not observed, which is argued, not measured). A party with
  no result in the city has no entry, and its record is 0.
* ``margin[pool]`` — the largest one-cycle rise of a FITTED pool rate
  (``fit_city``'s ``rates``) by any party in any metro, between two
  consecutive fitted local elections both strictly before the target. A party
  absent from the earlier fit rises from 0. ``margin_cycles`` counts the
  cycles it was taken over; with none it is 0.
* ``sources`` — which elections entered the record, and for each national one
  the share of its votes that reached a ward.

A target with no fitted local election before it in that city is absent: the
run then reports ``"no record"`` rather than a threshold of zero.

The method is ``audits/2026-10-09-model-fixes/item7/scripts/panel_rates.py``,
``panel_2024.py`` and ``guard_probe.py``'s ``thresholds``, as functions (SPEC
§1.11), with one difference from the probe: the probe read only the 2024
national election, and this reads every national election that follows a
fitted local one.

Usage::

    .venv/bin/python src/group_share_record.py --emit        # the artefact
    .venv/bin/python src/group_share_record.py --out DIR     # to DIR instead

``--emit`` writes ``data/processed/group_share_record.json`` and belongs to a
re-emit window (``POOLS-REEMIT-QUEUE.md``): the file carries an
``artefact_key`` naming this module's code, ``pools.py`` and the emit's
dependencies, and ``montecarlo`` records whether it is current.
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import io
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

import cityconfig
import parties as P
import pools

ROOT = Path(__file__).resolve().parent.parent
CITIES = ("joburg", "tshwane", "ekurhuleni", "ethekwini", "capetown",
          "nelsonmandelabay", "buffalocity", "mangaung")
TARGETS = ("2011", "2016", "2021", "2026")
FITTED_LGE = ("2011", "2016", "2021")


def artefact_key() -> dict:
    """What the artefact was built from: this module, ``pools``, its deps."""
    here = Path(__file__).resolve()
    return {"schema": 1,
            "record_sha": pools._code_sha(here),
            "pools_sha": pools._code_sha(here.parent / "pools.py"),
            "deps_sha": pools._deps_sha()}


def _dd(party_votes: np.ndarray, comp: np.ndarray, votes: np.ndarray):
    """City-level Duncan-Davis bounds on a party's share of each pool's vote.

    Per ward ``w`` and pool ``g``: the party's votes from ``g`` lie in
    ``[max(0, p_w − (1 − c_wg)·V_w), min(p_w, c_wg·V_w)]``; summed over wards
    and divided by the pool's votes.
    """
    pool_votes = (comp * votes[:, None]).sum(0)
    lo = np.maximum(0.0, party_votes[:, None]
                    - (1.0 - comp) * votes[:, None]).sum(0)
    hi = np.minimum(party_votes[:, None], comp * votes[:, None]).sum(0)
    with np.errstate(divide="ignore", invalid="ignore"):
        return (np.where(pool_votes > 0, lo / pool_votes, 0.0),
                np.where(pool_votes > 0, hi / pool_votes, 0.0))


def _fit(slug: str, year: str, cfg):
    city = cityconfig.load(slug)
    cityconfig.use(slug)
    with contextlib.redirect_stdout(io.StringIO()):
        return city, pools.fit_city(city, year, cfg)


def lge_rows(slug: str, year: str, cfg) -> tuple[list[dict], dict]:
    """One fitted local election: per party and pool, the fitted rate and
    the Duncan-Davis upper bound. Returns the rows and the fit's context."""
    _city, (fits, ctx) = _fit(slug, year, cfg)
    cats = list(ctx["categories"])
    comp, votes, shares = ctx["comp"], ctx["votes"], ctx["Y"]
    rows = []
    for j, party in enumerate(ctx["parties"]):
        pv = shares[:, j] * votes
        if pv.sum() <= 0:
            continue
        _lo, hi = _dd(pv, comp, votes)
        for g, pool in enumerate(cats):
            rows.append({"party": party, "pool": pool,
                         "rate": float(fits[party].rates[g]),
                         "hi": float(hi[g])})
    return rows, ctx


def npe_rows(slug: str, npe: str, lge: str, ctx: dict) -> tuple[list[dict], float]:
    """One national election on a fitted local election's wards.

    VDs are joined to wards through the local election's own VD file, and the
    local election's voter composition is carried forward (argued). Returns
    the rows and the share of the national election's votes that reached a
    ward.
    """
    city = cityconfig.load(slug)
    lge_file = city.path("raw", "elections",
                         cityconfig.CALENDAR[lge].results.replace(
                             "{CODE}", city.code))
    npe_file = city.path("raw", "elections",
                         cityconfig.CALENDAR[npe].results.replace(
                             "{CODE}", city.code))
    if not (lge_file.exists() and npe_file.exists()):
        return [], 0.0
    ward_of = {}
    with open(lge_file, encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh):
            ward_of[row["VD_Number"]] = row["Ward"]
    comp = dict(zip(ctx["wards"], ctx["comp"]))
    tally: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    total = joined = 0.0
    with open(npe_file, encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh):
            v = float(row.get("Party_Votes") or 0)
            total += v
            ward = ward_of.get(row["VD_Number"])
            if ward in comp:
                tally[ward][P.canonical(row["sPartyName"])] += v
                joined += v
    wards = sorted(tally)
    if not wards:
        return [], 0.0
    c = np.array([comp[w] for w in wards])
    votes = np.array([sum(tally[w].values()) for w in wards])
    rows = []
    for party in sorted({q for w in wards for q in tally[w]}):
        pv = np.array([tally[w].get(party, 0.0) for w in wards])
        if pv.sum() <= 0:
            continue
        _lo, hi = _dd(pv, c, votes)
        for g, pool in enumerate(ctx["categories"]):
            rows.append({"party": party, "pool": pool, "rate": None,
                         "hi": float(hi[g])})
    return rows, (joined / total if total else 0.0)


def _npe_after(lge: str) -> list[str]:
    """National elections after ``lge`` and before the next local election."""
    lges = sorted((y for y, e in cityconfig.CALENDAR.items()
                   if e.kind == "LGE"), key=int)
    later = [y for y in lges if int(y) > int(lge)]
    stop = int(later[0]) if later else 10 ** 6
    return sorted((y for y, e in cityconfig.CALENDAR.items()
                   if e.kind == "NPE" and e.results
                   and int(lge) < int(y) < stop), key=int)


def panel(cities=CITIES, years=FITTED_LGE) -> dict:
    """Every city's fitted local elections and the national ones after them.

    ``{slug: [(election year, kind, rows, coverage)]}``, kind ``"LGE"`` or
    ``"NPE"``.
    """
    cfg = pools.load_config()
    out: dict[str, list] = {}
    for slug in cities:
        out[slug] = []
        for year in years:
            try:
                rows, ctx = lge_rows(slug, year, cfg)
            except SystemExit as exc:      # a city-year fit_city refuses
                print(f"  {slug} {year}: not fitted ({exc})", file=sys.stderr)
                continue
            out[slug].append((year, "LGE", rows, 1.0))
            for npe in _npe_after(year):
                nrows, coverage = npe_rows(slug, npe, year, ctx)
                if nrows:
                    out[slug].append((npe, "NPE", nrows, coverage))
    return out


def thresholds(data: dict, slug: str, target: str) -> dict | None:
    """The record and margin for one city at one target, or None."""
    before = [(y, k, rows, cov) for y, k, rows, cov in data.get(slug, [])
              if int(y) < int(target)]
    if not any(k == "LGE" for _y, k, _r, _c in before):
        return None
    record: dict[str, dict[str, float]] = defaultdict(dict)
    for _y, _k, rows, _c in before:
        for r in rows:
            pool, party = r["pool"], r["party"]
            record[pool][party] = max(record[pool].get(party, 0.0), r["hi"])
    margin: dict[str, float] = defaultdict(float)
    cycles = 0
    for other, entries in data.items():
        fitted = sorted(((y, rows) for y, k, rows, _c in entries
                         if k == "LGE" and int(y) < int(target)),
                        key=lambda e: int(e[0]))
        for (_y0, prev), (_y1, cur) in zip(fitted, fitted[1:]):
            cycles += 1
            was = {(r["party"], r["pool"]): r["rate"] for r in prev}
            for r in cur:
                rise = r["rate"] - was.get((r["party"], r["pool"]), 0.0)
                margin[r["pool"]] = max(margin[r["pool"]], rise)
    pools_seen = sorted({r["pool"] for _y, _k, rows, _c in before for r in rows})
    return {
        "record": {g: dict(sorted(record[g].items())) for g in sorted(record)},
        "margin": {g: float(margin.get(g, 0.0)) for g in pools_seen},
        "margin_cycles": cycles,
        "sources": [{"year": y, "kind": k, "coverage": round(float(c), 6)}
                    for y, k, _r, c in before],
    }


def build(cities=CITIES, targets=TARGETS) -> dict:
    data = panel(cities)
    out = {"artefact_key": artefact_key(), "cities": {}}
    for slug in cities:
        per = {}
        for target in targets:
            t = thresholds(data, slug, target)
            if t is not None:
                per[target] = t
        out["cities"][slug] = per
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    where = ap.add_mutually_exclusive_group(required=True)
    where.add_argument("--emit", action="store_true",
                       help="write data/processed/group_share_record.json")
    where.add_argument("--out", type=Path,
                       help="write group_share_record.json into this directory")
    args = ap.parse_args(argv)
    directory = (ROOT / "data" / "processed") if args.emit else args.out
    directory.mkdir(parents=True, exist_ok=True)
    payload = build()
    path = directory / pools.GROUP_SHARE_RECORD
    path.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n",
                    encoding="utf-8")
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
