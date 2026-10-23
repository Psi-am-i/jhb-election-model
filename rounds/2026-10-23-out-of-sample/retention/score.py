"""Score prereg/2026-10-23-second-election-retention.md: rules S and P, R1-R3.

Pure arithmetic over the raw local-election files. Writes nothing under data/;
writes results.json and results.md beside this file.

    nice -n 15 .venv/bin/python rounds/2026-10-23-out-of-sample/retention/score.py

**What is reused from `levels`, not reimplemented.**
- Shares: `levels._citywide_and_roster` (list/PR ballot, canonical names).
- The quarantine: `levels._held_back` (the `HELD_BACK` gate `_citywide` applies).
- The demarcation exclusion: `levels._crosses_demarcation`.
- Rule S: `levels.size_centre(levels.local_record(target))`, called directly.

Every file is parsed once here and cached; the cached pairs are then checked
against `levels.local_record` for each target, so a ratio used for rule P is the
ratio the live record holds (refuses to score otherwise).

**How "first local election" is decided** (each is a row in results.md's
departures table):
- Party-level: the earliest LGE in which the party has a non-zero list share
  in any of the eight metros. Read from EVERY file on disk, held-back ones
  included: whether a party stood is a fact about the ballot, and no share from
  a held-back file enters any ratio.
- The record starts in 2000, so every party present then is left-censored. Of
  that cohort only UDM is taken as a first-timer, as the pre-registration does.
- AIC is scored at 2021 on its 2016->21 metros, as the pre-registration's table
  names them; that is a per-metro "first" applied to AIC alone (SPEC note †).
- Exits (present at the first election, absent at the second) give no pair,
  as in the live record.

Natural logs throughout. S is evaluated at each pair's first-election share in
that metro.
"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT / "src"))

import cityconfig  # noqa: E402
import levels as L  # noqa: E402

YEARS = sorted((y for y, e in cityconfig.CALENDAR.items()
                if e.kind == "LGE" and e.results), key=int)
CODES = L.METRO_CODES
CITY = cityconfig.load("joburg")   # local_record reads only target.year

# The pre-registration's scored sets, by its table.
SCORED_2016 = {"COPE": None, "APC": None, "ALJAMAAH": None, "AIC": ("BUF",)}
SCORED_2021 = {"EFF": None, "AIC": "per-metro-first"}
# The parties the SPEC names; anything else the rule finds is listed.
SPEC_PARTIES = {"UDM", "COPE", "APC", "ALJAMAAH", "AIC", "EFF", "PA", "NFP", "ID",
                "INDEPENDENT_DEMOCRATS"}
CENSORED_KEEP = {"UDM"}            # the one 2000 first-timer the pre-reg takes


def path(year: str, code: str) -> str:
    return f"data/raw/elections/lge{year}_{code}_vd_party_clean.csv"


# --- read every file once --------------------------------------------------
ALL: dict[tuple[str, str], dict[str, float]] = {}
LIVE: dict[tuple[str, str], dict[str, float]] = {}
for y in YEARS:
    for c in CODES:
        shares, _roster = L._citywide_and_roster(path(y, c))
        ALL[(y, c)] = shares
        LIVE[(y, c)] = {} if L._held_back(path(y, c)) else shares


def first_lge(source) -> dict[str, str]:
    out: dict[str, str] = {}
    for (y, _c), s in source.items():
        for p, v in s.items():
            if v > 0 and (p not in out or int(y) < int(out[p])):
                out[p] = y
    return out


FIRST = first_lge(ALL)
FIRST_LIVE_ONLY = first_lge(LIVE)


def consecutive_pairs(target_year: str):
    """(party, earlier, later, code, s1, s2) for every pair local_record holds."""
    out = []
    for earlier, later in zip(YEARS, YEARS[1:]):
        if int(later) >= int(target_year):
            continue
        for c in CODES:
            if L._crosses_demarcation(c, later):
                continue
            b, a = LIVE[(earlier, c)], LIVE[(later, c)]
            for p in set(b) & set(a):
                if b[p] > 0:
                    out.append((p, earlier, later, c, b[p], a[p]))
    return out


def check_against_record(target_year: str, record) -> None:
    """The cached pairs are exactly local_record's ratios (as multisets)."""
    mine = defaultdict(list)
    for p, _e, _l, _c, s1, s2 in consecutive_pairs(target_year):
        mine[p].append((s2 / s1, s1))
    if set(mine) != set(record):
        raise SystemExit(f"{target_year}: party sets differ from local_record")
    for p in record:
        if sorted(mine[p]) != sorted(record[p]):
            raise SystemExit(f"{target_year}: {p} ratios differ from local_record")


def aic_per_metro_first(target_year: str):
    """AIC's pairs whose earlier election is its first in THAT metro."""
    out = []
    for earlier, later in zip(YEARS, YEARS[1:]):
        if int(later) > int(target_year):
            continue
        for c in CODES:
            if L._crosses_demarcation(c, later):
                continue
            seen_before = any(ALL[(y, c)].get("AIC", 0) > 0
                              for y in YEARS if int(y) < int(earlier))
            b, a = LIVE[(earlier, c)].get("AIC", 0), LIVE[(later, c)].get("AIC", 0)
            if not seen_before and b > 0 and a > 0:
                out.append(("AIC", earlier, later, c, b, a))
    return out


def first_second(pairs, first=FIRST):
    """Pairs whose earlier election is the party's first, with the 2000 cohort
    censored except UDM."""
    out = []
    for row in pairs:
        p, e = row[0], row[1]
        if first.get(p) != e:
            continue
        if e == YEARS[0] and p not in CENSORED_KEEP:
            continue
        out.append(row)
    return out


def rule_p(pairs) -> tuple[float, dict[str, float]]:
    by = defaultdict(list)
    for p, _e, _l, _c, s1, s2 in pairs:
        by[p].append(s2 / s1)
    med = {p: float(np.median(v)) for p, v in by.items()}
    return float(np.median(list(med.values()))), med


def rule_s(target_year: str):
    rec = L.local_record(cityconfig.Target(CITY, target_year))
    check_against_record(target_year, rec)
    fit = L.size_centre(rec)
    if fit is None:
        raise SystemExit(f"size_centre returned None at {target_year}")
    n = sum(len(v) for v in rec.values())
    return fit, n, len(rec)


def s_at(fit, share: float) -> float:
    a, b = fit
    return float(np.exp(a + b * np.log(share)))


def score(rows, predict) -> dict:
    """Mean |ln pred - ln realised|, metros averaged within party, then parties."""
    per = defaultdict(list)
    detail = []
    for p, e, l, c, s1, s2 in rows:
        r = s2 / s1
        pr = predict(s1)
        err = abs(np.log(pr) - np.log(r))
        per[p].append(err)
        detail.append({"party": p, "pair": f"{e}->{l}", "metro": c,
                       "s1_pct": 100 * s1, "s2_pct": 100 * s2, "ratio": r,
                       "predicted": pr, "abs_log_error": float(err)})
    parties = {p: float(np.mean(v)) for p, v in per.items()}
    return {"score": float(np.mean(list(parties.values()))) if parties else None,
            "per_party": parties, "pairs": detail}


# --- refusal checks --------------------------------------------------------
FIT_2026, N2026, P2026 = rule_s("2026")
line_2026 = s_at(FIT_2026, 0.1812)
if abs(line_2026 - 0.7202) > 0.0005:
    raise SystemExit(f"size line at 0.1812 is {line_2026:.4f}, not 0.7202: refusing")
e16, e21 = LIVE[("2016", "JHB")].get("EFF", 0) * 100, LIVE[("2021", "JHB")].get("EFF", 0) * 100
if abs(e16 - 10.93) > 0.01 or abs(e21 - 10.11) > 0.01:
    raise SystemExit(f"JHB EFF 2016->21 is {e16:.2f}->{e21:.2f}, not 10.93->10.11: refusing")

# --- per-target ------------------------------------------------------------
results: dict = {
    "checks": {"size_line_2026_at_0.1812": line_2026,
               "size_fit_2026": {"a": FIT_2026[0], "b": FIT_2026[1],
                                 "ratios": N2026, "parties": P2026},
               "jhb_eff_2016_2021_pct": [e16, e21]},
    "targets": {},
}


def scored_rows(target: str):
    rows = []
    later_pairs = [r for r in consecutive_pairs(str(int(target) + 1))
                   if r[2] == target]
    spec = SCORED_2016 if target == "2016" else SCORED_2021
    for p, metros in spec.items():
        if metros == "per-metro-first":
            rows += [r for r in aic_per_metro_first(target) if r[2] == target]
        else:
            rows += [r for r in later_pairs if r[0] == p
                     and FIRST.get(p) == r[1]
                     and (metros is None or r[3] in metros)]
    rule_found = first_second(later_pairs)
    return rows, rule_found


def fit_p(target: str, include_aic_metro=True, first=FIRST, named_only=False):
    rows = first_second(consecutive_pairs(target), first)
    if include_aic_metro:
        extra = [r for r in aic_per_metro_first(target)
                 if int(r[2]) < int(target)]
        keys = {(r[0], r[1], r[3]) for r in rows}
        rows += [r for r in extra if (r[0], r[1], r[3]) not in keys]
    if named_only:
        rows = [r for r in rows if r[0] in SPEC_PARTIES]
    return rows


for target in ("2016", "2021"):
    fit, n, np_ = rule_s(target)
    p_rows = fit_p(target)
    P, p_med = rule_p(p_rows)
    rows, rule_found = scored_rows(target)
    sS = score(rows, lambda s1: s_at(fit, s1))
    sP = score(rows, lambda s1: P)
    # variants
    P_named, _ = rule_p(fit_p(target, named_only=True))
    P_live, _ = rule_p(fit_p(target, first=FIRST_LIVE_ONLY))
    extra_live = len(fit_p(target, first=FIRST_LIVE_ONLY)) - len(p_rows)
    unlisted = sorted({r[0] for r in rule_found} - SPEC_PARTIES)
    rf = [r for r in rule_found if not (r[0] == "AIC")] + \
         [r for r in rows if r[0] == "AIC"]
    v = {"rule_found_all": {"S": score(rf, lambda s1: s_at(fit, s1))["score"],
                            "P": score(rf, lambda s1: P)["score"],
                            "parties": sorted({r[0] for r in rf})},
         "P_named_parties_only": P_named,
         "P_first_from_live_files_only": P_live,
         "pairs_added_by_live_only_first": extra_live}
    if target == "2021":
        eff = [r for r in rows if r[0] == "EFF"]
        v["EFF_only"] = {"S": score(eff, lambda s1: s_at(fit, s1))["score"],
                         "P": score(eff, lambda s1: P)["score"]}
    results["targets"][target] = {
        "S": {"a": fit[0], "b": fit[1], "ratios": n, "parties": np_},
        "P": {"value": P, "party_medians": p_med, "pairs": len(p_rows)},
        "score_S": sS, "score_P": sP,
        "unlisted_parties_scorable_by_rule": unlisted,
        "variants": v,
    }

# --- R1-R3 -----------------------------------------------------------------
T = results["targets"]
gap = {t: abs(T[t]["score_S"]["score"] - T[t]["score_P"]["score"]) for t in T}
R1 = all(g <= 0.2 for g in gap.values())

eff_rows = [d for d in T["2021"]["score_S"]["pairs"] if d["party"] == "EFF"]
eff_S_low = sum(d["predicted"] < 0.9 for d in eff_rows)
eff_P_low = sum(d["predicted"] < 0.9 for d in
                T["2021"]["score_P"]["pairs"] if d["party"] == "EFF")
R2 = eff_S_low >= 6 and eff_P_low >= 6 and len(eff_rows) == 8

P26_rows = fit_p("2026")
P26, P26_med = rule_p(P26_rows)
P26_noPA, _ = rule_p([r for r in P26_rows if r[0] != "PA"])
P26_noAICm, _ = rule_p(fit_p("2026", include_aic_metro=False))
R3 = 0.4 <= P26 <= 1.2

results["R"] = {
    "R1": {"pass": R1, "abs_gap": gap},
    "R2": {"pass": R2, "eff_metros": len(eff_rows),
           "S_below_0.9": eff_S_low, "P_below_0.9": eff_P_low},
    "R3": {"pass": R3, "P_target_2026": P26, "pairs": len(P26_rows),
           "party_medians": P26_med,
           "P_target_2026_without_PA": P26_noPA,
           "P_target_2026_without_AIC_per_metro": P26_noAICm,
           "P_target_2021_for_comparison": T["2021"]["P"]["value"]},
    "R3_unlisted_parties": sorted(set(P26_med) - SPEC_PARTIES),
}

(HERE / "results.json").write_text(json.dumps(results, indent=1, sort_keys=True))

# --- results.md ------------------------------------------------------------
def f(x, k=3):
    return "–" if x is None else f"{x:.{k}f}"


md = ["# Second-election retention: scored (prereg 2026-10-23)", "",
      "Produced by `score.py` in this directory from the raw local-election "
      "files (list ballot, eight metros). Natural logs. Score = mean absolute "
      "log error of predicted against realised ratio, party-metros averaged "
      "within party, then over parties.", "",
      "## Checks the script refuses to score without", "",
      f"- Size line fitted at target 2026 ({N2026} ratios, {P2026} parties), "
      f"at share 0.1812: {line_2026:.4f}.",
      f"- Johannesburg EFF list share 2016 → 2021: {e16:.2f}% → {e21:.2f}%.", "",
      "## Rules fitted per target", "",
      "| target | S: a | S: b | S fitted on (ratios / parties) | P | P fitted on (first→second pairs / parties) |",
      "|---|---|---|---|---|---|"]
for t in T:
    s, p = T[t]["S"], T[t]["P"]
    md.append(f"| {t} | {s['a']:.4f} | {s['b']:.4f} | {s['ratios']} / {s['parties']} "
              f"| {p['value']:.3f} | {p['pairs']} / {len(p['party_medians'])} |")
md += ["", "## Each party's median first→second ratio (P's inputs)", ""]
for t in T:
    pm = T[t]["P"]["party_medians"]
    md.append(f"- **Target {t}:** " + ", ".join(
        f"{k} {v:.2f}" for k, v in sorted(pm.items(), key=lambda kv: kv[1])))
md += ["", "## Scores (mean absolute log error)", "",
       "| target | party | party-metros | S | P |", "|---|---|---|---|---|"]
for t in T:
    sS, sP = T[t]["score_S"], T[t]["score_P"]
    for party in sS["per_party"]:
        k = sum(d["party"] == party for d in sS["pairs"])
        md.append(f"| {t} | {party} | {k} | {f(sS['per_party'][party])} "
                  f"| {f(sP['per_party'][party])} |")
    md.append(f"| {t} | **all (mean over parties)** | {len(sS['pairs'])} "
              f"| **{f(sS['score'])}** | **{f(sP['score'])}** |")
md += ["", "## Scored pairs", "",
       "| target | party | metro | first % | second % | realised ratio | S predicted | P predicted |",
       "|---|---|---|---|---|---|---|---|"]
for t in T:
    for dS, dP in zip(T[t]["score_S"]["pairs"], T[t]["score_P"]["pairs"]):
        md.append(f"| {t} | {dS['party']} | {dS['metro']} | {dS['s1_pct']:.2f} "
                  f"| {dS['s2_pct']:.2f} | {dS['ratio']:.2f} | {dS['predicted']:.3f} "
                  f"| {dP['predicted']:.3f} |")
R = results["R"]
md += ["", "## Predictions", "",
       "| prediction | result | numbers |", "|---|---|---|",
       f"| R1: \\|S − P\\| ≤ 0.2 at both targets | {'PASS' if R1 else 'FAIL'} "
       f"| 2016: {gap['2016']:.3f}; 2021: {gap['2021']:.3f} |",
       f"| R2: at 2021 both rules predict below 0.9 in ≥ 6 of EFF's 8 metros "
       f"| {'PASS' if R2 else 'FAIL'} | S: {eff_S_low} of {len(eff_rows)}; "
       f"P: {eff_P_low} of {len(eff_rows)} |",
       f"| R3: P for use at 2026 (pairs through 2016→21) in [0.4, 1.2] "
       f"| {'PASS' if R3 else 'FAIL'} | {P26:.3f} ({len(P26_rows)} pairs, "
       f"{len(P26_med)} parties) |", "",
       "## Variants (not the pre-registered numbers)", "",
       "| variant | value |", "|---|---|"]
for t in T:
    v = T[t]["variants"]
    md.append(f"| {t}: scored on every first→second pair the rule finds "
              f"({len(v['rule_found_all']['parties'])} parties), S / P "
              f"| {f(v['rule_found_all']['S'])} / {f(v['rule_found_all']['P'])} |")
    md.append(f"| {t}: P fitted on parties the SPEC names only | {f(v['P_named_parties_only'])} |")
    md.append(f"| {t}: P with \"first\" read from live files only "
              f"(adds {v['pairs_added_by_live_only_first']} pairs) "
              f"| {f(v['P_first_from_live_files_only'])} |")
    if "EFF_only" in v:
        md.append(f"| {t}: scored on EFF alone (AIC dropped), S / P "
                  f"| {f(v['EFF_only']['S'])} / {f(v['EFF_only']['P'])} |")
md += [f"| R3 P without PA | {P26_noPA:.3f} |",
       f"| R3 P without AIC's per-metro 2016→21 pairs | {P26_noAICm:.3f} |",
       f"| P fitted at target 2021 (pairs through 2011→16) | {T['2021']['P']['value']:.3f} |",
       "", "## Parties the rule finds beyond the SPEC's list", ""]
for t in T:
    md.append(f"- **Scorable at {t}, not scored:** "
              + (", ".join(T[t]["unlisted_parties_scorable_by_rule"]) or "none"))
for t in T:
    md.append(f"- **In P's fit at {t}:** " + ", ".join(
        sorted(set(T[t]["P"]["party_medians"]) - SPEC_PARTIES)))
md.append("- **In P's fit for 2026 (R3):** " + ", ".join(R["R3_unlisted_parties"]))
md += ["", "## Departures from the pre-registration's wording", "",
       "| point | pre-registration | done here | why |", "|---|---|---|---|",
       "| first local election | not defined | earliest LGE with a non-zero list share in any metro, read from every file on disk including the held-back 2000 files | a party's having stood is a fact about the ballot; no held-back share enters a ratio |",
       "| 2000 cohort | P at 2016 fitted on \"UDM Johannesburg 2000 → 06\" | the record starts in 2000, so every party then is left-censored; only UDM kept. DA (formed 2000) is the one excluded party that was new then | follows the table |",
       "| fit sets | \"the 2006 first-time parties that stood again in 2011\", \"the 2011 → 16 pairs\" | every first→second pair the rule finds, named or not | plain reading; named-only variant reported |",
       "| scored sets | parties named in the table | exactly those; every other rule-found pair is a variant | the table names them |",
       "| AIC at 2021 | \"AIC's 2016 → 21 metros\" | metros where AIC's first appearance in that metro is 2016 (per-metro first, AIC only); also in P's 2026 fit | AIC's party-level first is 2011 (Buffalo City), so a party-level rule would not score it. Six metros qualify, not the SPEC's seven: AIC has no 2016 list share in Tshwane (first there in 2021), and Buffalo City's first is 2011 |",
       "| R3 | \"P fitted at 2021, for use at 2026\" | P on first→second pairs whose later election precedes 2026 (through 2016→21) | \"for use at 2026\"; the target-2021 fit is reported beside it |",
       "| S at a pair | not stated | the line evaluated at that party's first-election share in that metro | the size the model would see |",
       ""]
(HERE / "results.md").write_text("\n".join(md))
print("\n".join(md))
