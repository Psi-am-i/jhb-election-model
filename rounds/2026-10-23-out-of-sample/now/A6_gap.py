"""A6: national vs provincial ballot, City of Johannesburg, NPE 2009 and 2014.

Read-only. Reads the IEC bulk zips in data/raw/elections/_source/ and the
model's per-metro NPE files in data/raw/elections/; writes nothing but stdout.

    .venv/bin/python rounds/2026-10-23-out-of-sample/now/A6_gap.py

Format traps handled (ingest_historic.py docstring, ingest_npe.py docstring):
* VALID VOTES is the PARTY's votes, not the VD total.
* vote cells may carry thousands separators in quotes ("1,656").
* headers carry embedded newlines; decoded latin-1 line by line, as
  ingest_historic.open_member does (the file is not valid UTF-8).
* municipality matched on the head before " - " == "JHB".
"""
from __future__ import annotations

import csv
import io
import statistics
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "data/raw/elections/_source"
ZIPS = {"2009": "npe2009_national_and_provincial.zip",
        "2014": "npe2014_national_and_provincial.zip"}
MODEL = {y: ROOT / f"data/raw/elections/npe{y}_JHB_vd_party.csv" for y in ZIPS}


def num(cell: str) -> int:
    t = (cell or "").strip().replace(",", "").replace(" ", "")
    if not t.lstrip("-").isdigit():
        raise ValueError(f"unparseable vote cell {cell!r}")
    return int(t)


def hdr(c: str) -> str:
    return " ".join(c.replace('"', "").split()).upper()


def read_zip(year):
    """ballot -> {'votes': (ward, vd, party) -> n, 'vd': vd -> (cast, spoilt, ward)}"""
    out = {}
    events = set()
    with zipfile.ZipFile(SRC / ZIPS[year]) as z:
        (name,) = [n for n in z.namelist() if n.lower().endswith(".csv")]
        with z.open(name) as raw:
            reader = csv.reader(line.decode("latin-1") for line in raw)
            h = [hdr(c) for c in next(reader)]
            ix = {c: i for i, c in enumerate(h)}
            for row in reader:
                if len(row) < len(h):
                    continue
                ev = row[ix["ELECTORAL EVENT"]].upper()
                events.add(ev)
                if row[ix["MUNICIPALITY"]].split(" - ")[0].strip().upper() != "JHB":
                    continue
                ballot = ("NATIONAL" if "NATIONAL" in ev else
                          "PROVINCIAL" if "PROVINCIAL" in ev else None)
                if ballot is None:
                    raise SystemExit(f"unknown event {ev}")
                d = out.setdefault(ballot, {"votes": defaultdict(int), "vd": {}})
                ward = row[ix["WARD"]].strip()
                vd = row[ix["VOTING DISTRICT"]].strip()
                party = row[ix["PARTY NAME"]].strip()
                d["votes"][(ward, vd, party)] += num(row[ix["VALID VOTES"]])
                d["vd"][vd] = (num(row[ix["TOTAL VOTES CAST"]]),
                               num(row[ix["SPOILT VOTES"]]), ward)
    return out, events


def read_model(year):
    votes = defaultdict(int)
    vd_valid = {}
    with open(MODEL[year], encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            votes[(r["Ward"], r["VD_Number"], r["sPartyName"])] += int(r["Party_Votes"])
            vd_valid[r["VD_Number"]] = int(r["Total_Valid_Votes"] or 0)
    return votes, vd_valid


def roll(votes, keyf):
    agg = defaultdict(lambda: defaultdict(int))
    for k, n in votes.items():
        agg[keyf(k)][k[2]] += n
    return agg


def pct(xs, q):
    xs = sorted(xs)
    if not xs:
        return float("nan")
    pos = (len(xs) - 1) * q
    lo, hi = int(pos), min(int(pos) + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)


def main():
    for year in ZIPS:
        data, events = read_zip(year)
        print(f"\n===== NPE {year}  events in zip: {sorted(events)}")
        city = {}
        for ballot in ("NATIONAL", "PROVINCIAL"):
            d = data[ballot]
            tot = roll(d["votes"], lambda k: "city")["city"]
            valid = sum(tot.values())
            # per-VD reconciliation: party sum == cast - spoilt
            per_vd = roll(d["votes"], lambda k: k[1])
            bad = [(vd, sum(p.values()), d["vd"][vd][0] - d["vd"][vd][1])
                   for vd, p in per_vd.items()
                   if sum(p.values()) != d["vd"][vd][0] - d["vd"][vd][1]]
            vd_valid = sum(c - s for c, s, _ in d["vd"].values())
            spoilt = sum(s for _, s, _ in d["vd"].values())
            wards = {w for w, _, _ in d["votes"]}
            print(f"{ballot}: VDs {len(per_vd)} wards {len(wards)} parties {len(tot)} "
                  f"party-vote sum {valid} sum(cast-spoilt) {vd_valid} spoilt {spoilt} "
                  f"VDs failing party-sum==cast-spoilt: {len(bad)} {bad[:5]}")
            city[ballot] = (tot, valid)

        # citywide table
        nat, nv = city["NATIONAL"]
        prov, pv = city["PROVINCIAL"]
        parties = sorted(set(nat) | set(prov), key=lambda p: -(nat.get(p, 0)))
        print("\nparty | national votes | national % | provincial votes | provincial % | gap pp (nat-prov)")
        for p in parties:
            a, b = nat.get(p, 0), prov.get(p, 0)
            print(f"{p} | {a} | {100*a/nv:.3f} | {b} | {100*b/pv:.3f} | {100*a/nv-100*b/pv:+.3f}")
        print(f"TOTAL valid | {nv} | 100 | {pv} | 100 |")
        print(f"sum |gap| over parties, pp: {sum(abs(100*nat.get(p,0)/nv-100*prov.get(p,0)/pv) for p in parties):.3f}")

        # ward-level
        wn = roll(data["NATIONAL"]["votes"], lambda k: k[0])
        wp = roll(data["PROVINCIAL"]["votes"], lambda k: k[0])
        common = sorted(set(wn) & set(wp))
        print(f"\nwards: national {len(wn)} provincial {len(wp)} common {len(common)}")
        top = [p for p in parties[:6]]
        print("party | wards | median gap pp | p10 | p90 | min | max | mean |abs gap|")
        for p in top:
            gaps = []
            for w in common:
                tn, tp = sum(wn[w].values()), sum(wp[w].values())
                if tn and tp:
                    gaps.append(100 * wn[w].get(p, 0) / tn - 100 * wp[w].get(p, 0) / tp)
            print(f"{p} | {len(gaps)} | {statistics.median(gaps):+.3f} | {pct(gaps,.1):+.3f} | "
                  f"{pct(gaps,.9):+.3f} | {min(gaps):+.3f} | {max(gaps):+.3f} | "
                  f"{statistics.mean(abs(g) for g in gaps):.3f}")
        # ward valid-vote difference (turnout across ballots)
        dv = [sum(wn[w].values()) - sum(wp[w].values()) for w in common]
        print(f"ward valid votes national minus provincial: median {statistics.median(dv)} "
              f"min {min(dv)} max {max(dv)}")

        n, p_ = data["NATIONAL"]["vd"], data["PROVINCIAL"]["vd"]
        print(f"VDs whose ward differs between ballots: "
              f"{sum(1 for v in n if v in p_ and n[v][2] != p_[v][2])}; "
              f"VDs on one ballot only: {len(set(n) ^ set(p_))}; "
              f"VDs with national cast < provincial cast: "
              f"{sum(1 for v in n if v in p_ and n[v][0] < p_[v][0])}/{len(n)}")
        neg = sorted((sum(wn[w].values()) - sum(wp[w].values()), w) for w in common
                     if sum(wn[w].values()) < sum(wp[w].values()))
        print(f"wards with national valid < provincial valid: {len(neg)} {neg}")

        # compare provincial with model file
        mv, mvd = read_model(year)
        zp = data["PROVINCIAL"]["votes"]
        keys = set(mv) | set(zp)
        diff = [(k, zp.get(k, 0), mv.get(k, 0)) for k in keys if zp.get(k, 0) != mv.get(k, 0)]
        diff_nz = [x for x in diff if x[1] or x[2]]
        mcity = roll(mv, lambda k: "c")["c"]
        print(f"\nMODEL FILE {MODEL[year].relative_to(ROOT)}: rows-keys {len(mv)} zip-prov keys {len(zp)} "
              f"total votes model {sum(mv.values())} zip-prov {pv}; "
              f"(ward,vd,party) cells differing: {len(diff)} (nonzero {len(diff_nz)}) {diff_nz[:5]}")
        pd = [(p, prov.get(p, 0), mcity.get(p, 0)) for p in set(prov) | set(mcity)
              if prov.get(p, 0) != mcity.get(p, 0)]
        print(f"citywide party totals differing zip-prov vs model: {pd}")
        zvd = {vd: c - s for vd, (c, s, _) in data["PROVINCIAL"]["vd"].items()}
        vdd = [(vd, zvd.get(vd), mvd.get(vd)) for vd in set(zvd) | set(mvd) if zvd.get(vd) != mvd.get(vd)]
        print(f"VD Total_Valid_Votes differing (zip cast-spoilt vs model): {len(vdd)} {vdd[:5]}")
        # does model match NATIONAL instead? (sanity: it should not)
        zn = data["NATIONAL"]["votes"]
        print(f"model==national cells: {sum(1 for k in mv if mv[k]==zn.get(k,0))}/{len(mv)}; "
              f"model==provincial cells: {sum(1 for k in mv if mv[k]==zp.get(k,0))}/{len(mv)}")


if __name__ == "__main__":
    sys.exit(main())
