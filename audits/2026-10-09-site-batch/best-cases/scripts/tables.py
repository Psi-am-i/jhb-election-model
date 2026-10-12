import json, sys
sys.path.insert(0, "/Users/simondavis/.claude/jobs/26965cd4/tmp/best-cases")
import common as C
R = json.load(open("/Users/simondavis/.claude/jobs/26965cd4/tmp/best-cases/results.json"))
N = C.NAMES
def nm(p): return N.get(p, p.title().replace("_", " "))
out = []
for p, G in R["full"].items():
    o = [f"### {G['name']}: tables", ""]
    o += [f"Best 1%: the **{G['n']}** simulations with **{G['cut']} seats or more** (out of 5,000; ties at the cut included). "
          f"Seats in this group: {G['seat_range'][0]} to {G['seat_range'][1]}, median {G['seats_group_median']:g}; median across all 5,000: {G['seats_all_median']}.", ""]
    o += ["| seats | median, best 1% | range, best 1% | median, all 5,000 |", "|---|---|---|---|",
          f"| ward seats | {G['ward_seats']['group_median']:g} | {G['ward_seats']['group_range'][0]} to {G['ward_seats']['group_range'][1]} | {G['ward_seats']['all_median']:g} |",
          f"| list seats | {G['list_seats']['group_median']:g} | {G['list_seats']['group_range'][0]} to {G['list_seats']['group_range'][1]} | {G['list_seats']['all_median']:g} |", ""]
    e = G["excessive"]
    who = ", ".join(f"{nm(k)} {v}" for k, v in e["others_who_group"]) or "none"
    o += ["| excessive-seats clause fired | share of best 1% | share of all 5,000 |", "|---|---|---|",
          f"| for {G['name']} | {e['own_group']:.0%} | {e['own_all']:.1%} |",
          f"| for any other party | {e['others_group']:.0%} | {e['others_all']:.0%} |", "",
          f"Other parties it fired for in the best 1% (simulations): {who}.", ""]
    lg = ", ".join(f"{'/'.join(nm(x) for x in k.split('/'))} {v}" for k, v in G["largest_party_group"])
    o += [f"Largest party in the best 1% (simulations): {lg}.", ""]
    o += ["| coalition of named parties | reaches a majority, best 1% | needs every member, best 1% | reaches a majority, all 5,000 |", "|---|---|---|---|"]
    for c in G["coalitions"]:
        o.append(f"| {' + '.join(nm(x) for x in c['coalition'].split('+'))} | {c['group']:.0%} | {c['minimal_group']:.0%} | {c['all']:.0%} |")
    o += ["", "Coalitions listed: those of one to three of the six main parties in which every member is needed for the majority in at least 10% of the best 1%. A majority is each simulation's own threshold (council size varies with excessive seats).", ""]
    r = G["representative"]
    seats = ", ".join(f"{nm(k)} {v}" for k, v in sorted(r["seats"].items(), key=lambda t: -t[1]))
    meds = ", ".join(f"{nm(k)} {v:g}" for k, v in sorted(r["group_median_seats"].items(), key=lambda t: -t[1]))
    o += [f"Representative simulation **{r['draw']}** (closest to the best 1%'s median seats of the six main parties, `scenarios.typical` on the group): {seats}, others {r['others']}; council {r['council']}, majority {r['threshold']}. "
          f"Majorities needing every member in it: {', '.join(' + '.join(nm(x) for x in m.split('+')) for m in r['majorities']) or 'none'}. Best 1% medians, for comparison: {meds}.", ""]
    o += ["| list-ballot share, pp | median, best 1% | median, all 5,000 | ward-ballot share, median best 1% | median, all 5,000 |", "|---|---|---|---|---|"]
    for k, v in sorted(G["shares"].items(), key=lambda t: (t[0] != p, t[0])):
        o.append(f"| {nm(k)} | {v['list_pp_group_median']:.1f} | {v['list_pp_all_median']:.1f} | {v['ward_pp_group_median']:.1f} | {v['ward_pp_all_median']:.1f} |")
    o += ["", "| turnout by voter group (drawn), % | mean, best 1% | mean, all 5,000 | best 1% mean as percentile of all |", "|---|---|---|---|"]
    for k, v in G["turnout"].items():
        o.append(f"| {k} | {v['group_mean_pp']:.1f} | {v['all_mean_pp']:.1f} | {v['group_mean_pctile_of_all']:.0f} |")
    o += ["", "| level shock (drawn): % above or below the party's central level | median, best 1% | 10th to 90th pct, best 1% | median, all 5,000 | sd(log) of the shock |", "|---|---|---|---|---|"]
    for k, v in sorted(G["level_shock"].items(), key=lambda t: (t[0] != p, t[0])):
        o.append(f"| {nm(k)} (central level {v['centre_pp']:.1f}% of the list vote) | {v['group_median_pct']:+.0f} | {v['group_p10_pct']:+.0f} to {v['group_p90_pct']:+.0f} | {v['all_median_pct']:+.0f} | {v['sd_log']:.2f} |")
    o += ["", f"| {G['name']}'s share within each voter group, % of that group's vote | expected after the level shock, median best 1% | same, all 5,000 | drawn (after the within-group split), median best 1% | same, all 5,000 | split residual, median best 1%, pp |", "|---|---|---|---|---|---|"]
    for k, v in G["within_pool"].items():
        if v["mean_share_pp_all_median"] < 0.1 and v["sample_share_pp_group_median"] < 1:
            continue
        o.append(f"| {k} | {v['mean_share_pp_group_median']:.1f} | {v['mean_share_pp_all_median']:.1f} | {v['sample_share_pp_group_median']:.1f} | {v['sample_share_pp_all_median']:.1f} | {v['residual_pp_group_median']:+.1f} |")
    r2 = G["r2_all_draws"]
    o += ["", f"Share of the variance of {G['name']}'s seats across all 5,000 simulations accounted for by each drawn quantity alone (least squares, R²): "
          f"its within-group split {r2['own_within_pool']:.2f}; its level shock {r2['own_level_shock']:.2f}; the six main parties' level shocks {r2['six_main_level_shocks']:.2f}; "
          f"the four turnouts {r2['pool_turnouts']:.2f}; the turnout-pattern blend {r2['blend']:.2f}; all of these together {r2['all_recorded_citywide']:.2f}. "
          f"The remainder (rivals' within-group splits, the interactions through the balancing step and the seat law, district turnout noise and ward noise) is not decomposed here.", ""]
    g = G["gain_wards"]
    if g:
        pos = ", ".join(f"{k} {v}" for k, v in G["gain_by_position"])
        frm = ", ".join(f"{nm(k)} {v}" for k, v in G["gain_from"])
        o += [f"Wards {G['name']} wins in at least half of its best 1% and in under half of all 5,000: **{len(g)}**. By position: {pos}. Each ward's most frequent winner across all 5,000: {frm}.", ""]
        o += ["| ward | where | won, all 5,000 | won, best 1% | most frequent winner, all 5,000 |", "|---|---|---|---|---|"]
        for x in g:
            o.append(f"| {x['ward']} | {x['map_position']} | {x['all']:.0%} | {x['group']:.0%} | {nm(x['usual_winner'])} |")
        wn = G.get("ward_noise_gain_wards")
        if wn:
            o += ["", f"Ward noise (drawn) in these wards: {G['name']}'s random ward factor minus the most frequent winner's averaged {wn['as_pct_group_mean']:+.1f}% across the best 1%, against a spread of {wn['sd_per_draw_log']*100:.0f}% (sd of the log difference) in any one simulation.", ""]
    else:
        o += [f"Wards {G['name']} wins in at least half of its best 1% and in under half of all 5,000: none.", ""]
    o += [f"Maps: `{p.lower()}-representative.svg`, `{p.lower()}-ward-frequency.svg`.", ""]
    out.append("\n".join(o))
rest = ["| party | best 1%: cut, seats | simulations in it | seat range | median seats, all 5,000 | ward seats, median best 1% | list seats, median best 1% | excessive seats for it, best 1% | list share, median best 1%, pp | list share, median all, pp | level-shock sd(log) | R² of seats on its within-group split |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|"]
for G in sorted(R["rest"], key=lambda g: -g["cut"]):
    p = G["party"]; sh = G["shares"].get(p, {}); lv = G["level_shock"][p]
    rest.append(f"| {nm(p)} | {G['cut']} | {G['n']} | {G['seat_range'][0]} to {G['seat_range'][1]} | {G['seats_all_median']} | {G['ward_seats']['group_median']:g} | {G['list_seats']['group_median']:g} | {G['excessive']['own_group']:.0%} | {sh.get('list_pp_group_median', 0):.1f} | {sh.get('list_pp_all_median', 0):.1f} | {lv['sd_log']:.2f} | {G['r2_all_draws']['own_within_pool']:.2f} |")
open("/Users/simondavis/.claude/jobs/26965cd4/tmp/best-cases/tables.md", "w").write("\n\n".join(out) + "\n\n## REST\n\n" + "\n".join(rest) + "\n")
