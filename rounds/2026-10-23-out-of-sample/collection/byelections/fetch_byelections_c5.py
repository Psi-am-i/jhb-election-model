"""DATA-PLAN.md section 4, items C5 and C7: by-election registration, spoilt and
cast, every contest the IEC by-election dashboard serves.

Patched copy of ``src/fetch_byelections.py`` (same endpoints, same flattening of
the party rows). Differences:

* every payload is archived verbatim under ``raw/`` before anything is parsed,
  so the tables can be rebuilt with ``build`` and no second request;
* both cycles (2016, 2021) and every province in one run;
* writes only into this directory, never into ``data/``;
* adds the registration and ballot totals the original dropped.

What the dashboard serves, by level (established by probing EEID 1935):

    municipality x event   RegisteredVoters, TotalVotesCast, ValidVotesCast,
                           SpoiltVotes, SpecialVotes (repeated on every party row)
    ward                   RegPop, party TotalValidVotes
    voting district        RegPop, party TotalValidVotes

So cast and spoilt exist per contest only where the municipality held one ward
on that date. Where it held several, the municipal total is not split here.

Usage:
    .venv/bin/python <this file> fetch     # sequential, 1 s between requests
    .venv/bin/python <this file> build     # tables + checks from raw/ only
"""

from __future__ import annotations

import csv
import json
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

DASH = "https://results.elections.org.za/dashboards/byelection/MapsJason"
USER_AGENT = "Mozilla/5.0 (jhb-election-model; by-election fetch)"
HERE = Path(__file__).resolve().parent
RAW = HERE / "raw"
CYCLES = ("2016", "2021")
DELAY = 1.0


# ---------------------------------------------------------------- fetch
def _fetch(rel: str, log) -> bytes | None:
    """GET MapsJason/<rel>, archive the body to raw/<rel>; None on 404."""
    dest = RAW / rel
    if dest.exists() and dest.stat().st_size > 0:
        return dest.read_bytes()
    url = f"{DASH}/{rel}"
    for attempt in (1, 2, 3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=60) as resp:
                body = resp.read()
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(body)
            log.write(f"{datetime.now(timezone.utc).isoformat()} 200 {len(body)} {url}\n")
            time.sleep(DELAY)
            return body
        except urllib.error.HTTPError as err:
            log.write(f"{datetime.now(timezone.utc).isoformat()} {err.code} 0 {url}\n")
            time.sleep(DELAY)
            if err.code == 404:
                return None
        except (urllib.error.URLError, TimeoutError) as err:
            log.write(f"{datetime.now(timezone.utc).isoformat()} ERR {err} {url}\n")
            time.sleep(DELAY * 5 * attempt)
    return None


def _json(body: bytes | None):
    if body is None or not body.strip():
        return None
    return json.loads(body.decode("utf-8-sig"))


def fetch() -> int:
    RAW.mkdir(exist_ok=True)
    with (HERE / "fetch.log").open("a", encoding="utf-8") as log:
        log.write(f"# fetch start {datetime.now(timezone.utc).isoformat()}\n")
        for cycle in CYCLES:
            _fetch(f"{cycle}/PartyList.js", log)
            events = _json(_fetch(f"{cycle}/ByElections.js", log)) or []
            print(f"cycle {cycle}: {len(events)} events", flush=True)
            for i, ev in enumerate(events, 1):
                eeid = ev["EEID"]
                nat = _json(_fetch(f"{eeid}/EEID{eeid}BigMapsNational.js", log))
                if not nat:
                    print(f"  [{i}] EEID {eeid}: no national file", flush=True)
                    continue
                for prov in nat.get("ProvinceResults", []):
                    for muni in prov.get("MunicipalityResults", []):
                        mid = muni["MunicipalityID"]
                        got = _fetch(f"{eeid}/EEID{eeid}Munic{mid}.js", log)
                        print(f"  [{i}/{len(events)}] EEID {eeid} {muni.get('Municipality','')}: "
                              f"{'ok' if got else 'MISSING'}", flush=True)
                log.flush()
        log.write(f"# fetch end {datetime.now(timezone.utc).isoformat()}\n")
    return 0


# ---------------------------------------------------------------- build
def _load(rel: str):
    p = RAW / rel
    return _json(p.read_bytes()) if p.exists() else None


def event_date(event: dict) -> str:
    if event.get("dtStartDate"):
        return event["dtStartDate"][:10]
    name = " ".join(event["Name"].split())
    for fmt in ("%d %b %Y", "%d %B %Y"):
        try:
            return datetime.strptime(name, fmt).date().isoformat()
        except ValueError:
            pass
    raise ValueError(f"EEID {event.get('EEID')}: no date in {event['Name']!r}")


def _write(name: str, rows: list[dict], cols: list[str]) -> None:
    with (HERE / name).open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


MUNI_TOTALS = ("RegisteredVoters", "TotalVotesCast", "ValidVotesCast", "SpoiltVotes", "SpecialVotes")


def build() -> int:
    parties = {c: {e["ID"]: (e.get("Name", ""), e.get("PartyFullName", ""))
                   for e in (_load(f"{c}/PartyList.js") or [])} for c in CYCLES}
    vd_party, vds, contests, munis, failures, checks = [], [], [], [], [], defaultdict(list)
    indep_names = defaultdict(set)

    for cycle in CYCLES:
        events = sorted(_load(f"{cycle}/ByElections.js") or [], key=event_date)
        for ev in events:
            eeid, date = ev["EEID"], event_date(ev)
            nat = _load(f"{eeid}/EEID{eeid}BigMapsNational.js")
            if not nat:
                failures.append((cycle, eeid, date, "", "", "BigMapsNational file absent (404 or empty)"))
                continue
            for prov in nat.get("ProvinceResults", []):
                for nm in prov.get("MunicipalityResults", []):
                    mid, mname, pname = nm["MunicipalityID"], nm.get("Municipality", ""), prov.get("Province", "")
                    payload = _load(f"{eeid}/EEID{eeid}Munic{mid}.js")
                    if not payload:
                        failures.append((cycle, eeid, date, mname,
                                         ";".join(str(w["WardID"]) for w in nm.get("WardResults", [])),
                                         "Munic file absent (404 or empty)"))
                        continue
                    base = dict(cycle=cycle, EEID=eeid, ByElectionDate=date, Province=pname,
                                Municipality=mname, MunicipalityID=mid)
                    # municipality totals: must be identical on every party row
                    mprs = payload.get("PartyBallotResults", [])
                    # From EEID 1598 (2024-12-04) independents carry per-candidate
                    # negative ids in every row, and the municipal file adds an
                    # aggregate party-0 row (totals zeroed) on top: a double count.
                    if any(p["ID"] < 0 for p in mprs) and any(p["ID"] == 0 for p in mprs):
                        checks["muni_party0_aggregate_duplicates_negative_ids_dropped"].append(f"{eeid} {mname}")
                        mprs = [p for p in mprs if p["ID"] != 0]
                    # Usually repeated on every party row; from late 2024 some files
                    # carry them on one row and 0 on the rest. Take the single
                    # non-zero value; two different non-zero values is a defect.
                    tot = {k: {p.get(k) for p in mprs} - {0, None} for k in MUNI_TOTALS}
                    totals_on_one_row = any(len({p.get(k) for p in mprs}) > 1 for k in MUNI_TOTALS)
                    if totals_on_one_row:
                        checks["muni_totals_on_one_row_only"].append(f"{eeid} {mname}")
                    for k, vals in tot.items():
                        if len(vals) > 1:
                            checks["muni_totals_differ_across_party_rows"].append(f"{eeid} {mname} {k} {vals}")
                    mt = {k: (next(iter(v)) if len(v) == 1 else (0 if not v else None)) for k, v in tot.items()}
                    muni_party = {p["ID"]: p.get("TotalValidVotes", 0) for p in mprs}
                    vd_party_all_wards = defaultdict(int)
                    wards = payload.get("WardResults", [])
                    mrow = dict(base, wards_that_day=len(wards),
                                WardIDs=";".join(str(w["WardID"]) for w in wards),
                                Muni_RegPop=payload.get("RegPop"),
                                party_valid_sum=sum(p.get("TotalValidVotes", 0) for p in mprs), **mt)
                    munis.append(mrow)
                    for ward in wards:
                        wid = ward["WardID"]
                        wpr = ward.get("PartyBallotResults", [])
                        ward_party = {p["ID"]: p.get("TotalValidVotes", 0) for p in wpr}
                        vd_sum_party = defaultdict(int)
                        vd_reg_sum = 0
                        dists = ward.get("VotingDistrictResults", [])
                        for d in dists:
                            vdn = d.get("VotingDistrictID", "")
                            dvalid = 0
                            for r in d.get("PartyBallotResults", []):
                                short, full = parties[cycle].get(r["ID"], ("", ""))
                                if not short:
                                    short, full = parties["2021" if cycle == "2016" else "2016"].get(r["ID"], ("", ""))
                                v = r.get("TotalValidVotes", 0)
                                dvalid += v
                                vd_sum_party[r["ID"]] += v
                                vd_party_all_wards[r["ID"]] += v
                                if r["ID"] == 0:
                                    indep_names[(eeid, wid)].add(r.get("CandidateName", ""))
                                vd_party.append(dict(base, WardID=wid, VD_Number=vdn, PartyID=r["ID"],
                                                     PartyName=short, PartyFullName=full,
                                                     CandidateName=r.get("CandidateName", ""),
                                                     Party_Votes=v, PercOfVotes=r.get("PercOfVotes", ""),
                                                     IsLeadingParty="Y" if r.get("IsLeadingPartyVotes") else "",
                                                     VD_RegPop=d.get("RegPop"), Ward_RegPop=ward.get("RegPop")))
                            vd_reg_sum += d.get("RegPop") or 0
                            vds.append(dict(base, WardID=wid, VD_Number=vdn, VD_RegPop=d.get("RegPop"),
                                            VD_valid_party_sum=dvalid,
                                            VDsComplete=d.get("VDsComplete"), VDExpected=d.get("VDExpected")))
                            if d.get("RegPop") is not None and d.get("RegPop") < dvalid:
                                checks["vd_registered_lt_valid"].append(f"{eeid} {wid} {vdn} {d.get('RegPop')}<{dvalid}")
                        # check: VD sums equal ward per party
                        if dict(vd_sum_party) != {k: v for k, v in ward_party.items()}:
                            diff = {k: (ward_party.get(k), vd_sum_party.get(k))
                                    for k in set(ward_party) | set(vd_sum_party)
                                    if ward_party.get(k) != vd_sum_party.get(k)}
                            checks["vd_sum_ne_ward_party"].append(f"{eeid} {mname} {wid} {diff}")
                        if not dists:
                            checks["ward_without_vds"].append(f"{eeid} {mname} {wid}")
                        if (ward.get("RegPop") or 0) != vd_reg_sum and dists:
                            checks["vd_regpop_sum_ne_ward_regpop"].append(
                                f"{eeid} {mname} {wid} ward={ward.get('RegPop')} vdsum={vd_reg_sum}")
                        if ward.get("VDsComplete") != ward.get("VDExpected"):
                            checks["ward_vds_incomplete"].append(
                                f"{eeid} {mname} {wid} {ward.get('VDsComplete')}/{ward.get('VDExpected')}")
                        wvalid = sum(ward_party.values())
                        single = len(wards) == 1
                        crow = dict(base, WardID=wid, wards_in_muni_that_day=len(wards), n_vds=len(dists),
                                    Ward_RegPop=ward.get("RegPop"), VD_RegPop_sum=vd_reg_sum,
                                    valid_party_sum=wvalid, n_parties=len(ward_party),
                                    VDsComplete=ward.get("VDsComplete"), VDExpected=ward.get("VDExpected"))
                        for k in MUNI_TOTALS:
                            crow[f"contest_{k}"] = mt[k] if single else ""
                        crow["independent_candidates_named_in_vds"] = len(indep_names[(eeid, wid)])
                        contests.append(crow)
                    # per party: municipal total vs the sum of the VD rows of every ward
                    for pid in set(muni_party) | set(vd_party_all_wards):
                        if muni_party.get(pid, 0) != vd_party_all_wards.get(pid, 0):
                            key = "muni_party_ne_vd_sum_independent" if pid == 0 else "muni_party_ne_vd_sum_party"
                            checks[key].append(f"{eeid} {date} {mname} party={pid} "
                                               f"muni={muni_party.get(pid, 0)} vdsum={vd_party_all_wards.get(pid, 0)}")
                    mrow["vd_sum_matches_muni_every_party"] = all(
                        muni_party.get(pid, 0) == vd_party_all_wards.get(pid, 0)
                        for pid in set(muni_party) | set(vd_party_all_wards))

    # municipality-level checks
    for m in munis:
        tag = f"{m['EEID']} {m['ByElectionDate']} {m['Municipality']}"
        if m["ValidVotesCast"] is None or m["TotalVotesCast"] is None:
            checks["muni_totals_missing"].append(tag)
            continue
        if not m["RegisteredVoters"]:
            checks["muni_registered_zero_or_missing"].append(tag)
        if m["party_valid_sum"] != m["ValidVotesCast"]:
            checks["muni_party_sum_ne_valid"].append(f"{tag} {m['party_valid_sum']}!={m['ValidVotesCast']}")
        if (m["ValidVotesCast"] or 0) + (m["SpoiltVotes"] or 0) != m["TotalVotesCast"]:
            checks["muni_valid_plus_spoilt_ne_cast"].append(
                f"{tag} {m['ValidVotesCast']}+{m['SpoiltVotes']}!={m['TotalVotesCast']}")
        if (m["RegisteredVoters"] or 0) < (m["TotalVotesCast"] or 0):
            checks["muni_registered_lt_cast"].append(f"{tag} {m['RegisteredVoters']}<{m['TotalVotesCast']}")
        if m["Muni_RegPop"] != m["RegisteredVoters"]:
            checks["muni_regpop_ne_registeredvoters"].append(f"{tag} {m['Muni_RegPop']} vs {m['RegisteredVoters']}")
    for c in contests:
        c["contest_totals_status"] = "not_split:municipality_held_several_wards"
        if c["wards_in_muni_that_day"] == 1:
            m = next(x for x in munis if x["EEID"] == c["EEID"] and x["MunicipalityID"] == c["MunicipalityID"])
            reasons = []
            if m["ValidVotesCast"] is None or m["TotalVotesCast"] is None:
                reasons.append("municipal_totals_conflict")
            else:
                if c["valid_party_sum"] != m["ValidVotesCast"]:
                    reasons.append("ward_valid_ne_municipal_valid"
                                   + ("(x2)" if m["ValidVotesCast"] == 2 * c["valid_party_sum"] else ""))
                if m["ValidVotesCast"] + m["SpoiltVotes"] != m["TotalVotesCast"]:
                    reasons.append("valid_plus_spoilt_ne_cast")
                if m["RegisteredVoters"] < m["TotalVotesCast"]:
                    reasons.append("registered_lt_cast")
                if c["Ward_RegPop"] != m["RegisteredVoters"]:
                    reasons.append("ward_regpop_ne_municipal_registered")
                if not m["vd_sum_matches_muni_every_party"]:
                    reasons.append("municipal_party_rows_ne_vd_rows")
            c["contest_totals_status"] = "consistent" if not reasons else "inconsistent:" + "+".join(reasons)
            if c["valid_party_sum"] != m["ValidVotesCast"]:
                checks["single_ward_valid_ne_muni_valid"].append(f"{c['EEID']} {c['WardID']}")
            if c["Ward_RegPop"] != m["RegisteredVoters"]:
                checks["single_ward_regpop_ne_muni_registered"].append(
                    f"{c['EEID']} {c['Municipality']} {c['WardID']} {c['Ward_RegPop']} vs {m['RegisteredVoters']}")

    base_cols = ["cycle", "EEID", "ByElectionDate", "Province", "Municipality", "MunicipalityID"]
    _write("byelections_vd_party.csv", vd_party, base_cols + [
        "WardID", "VD_Number", "PartyID", "PartyName", "PartyFullName", "CandidateName", "Party_Votes",
        "PercOfVotes", "IsLeadingParty", "VD_RegPop", "Ward_RegPop"])
    _write("byelections_vd.csv", vds, base_cols + [
        "WardID", "VD_Number", "VD_RegPop", "VD_valid_party_sum", "VDsComplete", "VDExpected"])
    _write("byelections_contest.csv", contests, base_cols + [
        "WardID", "wards_in_muni_that_day", "n_vds", "Ward_RegPop", "VD_RegPop_sum", "valid_party_sum",
        "n_parties", "VDsComplete", "VDExpected", "independent_candidates_named_in_vds",
        "contest_totals_status"]
        + [f"contest_{k}" for k in MUNI_TOTALS])
    _write("byelections_muni_event.csv", munis, base_cols + [
        "wards_that_day", "WardIDs", "Muni_RegPop", "party_valid_sum", *MUNI_TOTALS,
        "vd_sum_matches_muni_every_party"])
    with (HERE / "failures.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["cycle", "EEID", "ByElectionDate", "Municipality", "WardIDs", "reason"])
        w.writerows(failures)
    with (HERE / "checks.json").open("w", encoding="utf-8") as fh:
        json.dump({k: v for k, v in checks.items()}, fh, indent=1)
    print(f"vd_party={len(vd_party)} vd={len(vds)} contests={len(contests)} muni_events={len(munis)} "
          f"failures={len(failures)}")
    for k, v in checks.items():
        print(f"  check {k}: {len(v)}")
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    raise SystemExit({"fetch": fetch, "build": build}.get(cmd, lambda: print(__doc__) or 2)())
