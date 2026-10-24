"""What every published figure is, in the reader's words: the second line of
its tooltip (audits/2026-10-22-tooltips/BRIEF.md).

⛔ THE OWNER'S RULE (2026-10-22, verbatim): "every time you use a technical
part ofteh model, simply say 'This Model'". A figure the model computes is
sourced to "This Model", and its plain sentence says what was counted, over
what, for which party or group, and never which component computed it: no
file, code name, pool, fold, regime, lever, a seat law's internal name, "the
draws", "the spec" or "the run". An outside source keeps its name (the IEC,
Statistics South Africa, a poll's house, a news outlet). The technical source
stays in the ledger and NUMBERS-REVIEW.md, which we read; the reader does not.

One table, :data:`SAYS`, keyed by token-name patterns. Each pattern gives the
unit word line 1 prints after the figure ("chance", "seats", "wards", "%"
for a share whose format leaves the sign to the prose, or none), ``<who>``, and the sentence. A sentence is filled from:

* the pattern's named groups: ``party`` (a party code, named through
  ``render_sheet.NAMES``, then ``build_play.reader_name``), ``coal`` (codes
  joined by ``+``), ``group`` (a population group's slug, named from the pool
  spec's own categories, ``Facts.groups``), ``city`` (a metro's slug, named by
  ``build_validation.CITIES``), ``year``, ``cand`` and ``opp`` (a minority
  scenario's codes, ``_``-joined);
* :class:`Facts`, the run's own counts (never typed here): the forecast's
  simulation count, the past-elections test's, the validation's and its year;
* ``ballot`` (``ward`` or ``list``), said as it is;
* constants read from the modules that define them (the map's safe share,
  the small-party test's two shares).

A token matches a pattern when the pattern's regex matches the WHOLE name and
every party code in it is a known party. Every token the build publishes must
match exactly one pattern, and every pattern must match a published token
(``tests/test_tooltip_says.py``); a token with no sentence stops the build
(``build_site.tooltip_text``).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Say:
    pattern: str
    unit: str
    who: str
    says: str


@dataclass(frozen=True)
class Facts:
    """The run's counts and names a sentence may need, from the run."""
    n: int                              # the forecast's simulations
    n_hist: int | None = None           # each past election's, in the test
    n_val: int | None = None            # each metro's, in the validation
    val_year: str | None = None         # the election the validation scores
    groups: dict = field(default_factory=dict)   # slug -> group name


M = "This Model"
IEC21 = "IEC 2021 results"
_P = r"(?P<party>[A-Z][A-Z0-9_]*)"            # a party code, as the run spells it
_p = r"(?P<party>[a-z][a-z0-9]*(?:_[a-z0-9]+)*?)"   # the same, lower case
_C = r"(?P<coal>[A-Z][A-Z0-9_]*(?:\+[A-Z][A-Z0-9_]*)+)"
_G = r"(?P<group>[a-z][a-z_]*)"
_CITY = r"(?P<city>[a-z]+)"
#: Said of a figure from the published forecast's simulations.
_SIMS = "{n} simulations"
#: The 7 August claim test's scenario, said without the lever's name.
_SURGE = "in a scenario where every DA and ActionSA supporter turns out at the highest rate their area has recorded"
#: An earlier edition's figure, as it was published.
_AS_PUBLISHED = "as published in an earlier forecast"

SAYS: tuple[Say, ...] = (
    # --- coalitions (the who-can-govern table) -------------------------------
    Say(rf"coal\.{_C}\.majority", "chance", M,
        "The % of " + _SIMS + " where {coalition} together held a majority of the council."),
    Say(rf"coal\.{_C}\.seats_when_wins", "seats", M,
        "The middle of the seats {coalition} hold together, in the simulations where they have a majority."),
    Say(rf"coal\.{_C}\.cushion_when_wins", "seats", M,
        "The seats {coalition} hold above the majority line, at their middle count in the simulations where they have a majority."),
    Say(rf"coal\.{_C}\.stability", "", M,
        "The % of the councillors of {coalition} who could leave without the majority being lost, at their middle count in the simulations where they have one."),
    Say(rf"coal\.{_C}\.survive\.{_P}", "chance", M,
        "Of the simulations where {coalition} have a majority, the % in which they keep it if {party} leaves."),
    # --- seats by party (the seat tables) ------------------------------------
    Say(rf"seats\.(?!OTHERS\.){_P}\.median", "seats", M,
        "{Party}'s middle seat count across " + _SIMS + "."),
    Say(rf"seats\.(?!OTHERS\.){_P}\.p5", "seats", M,
        "The low end of {party}'s seat range: about 1 in 20 of " + _SIMS + " give it fewer."),
    Say(rf"seats\.(?!OTHERS\.){_P}\.p95", "seats", M,
        "The high end of {party}'s seat range: about 1 in 20 of " + _SIMS + " give it more."),
    Say(r"seats\.OTHERS\.median", "seats", M,
        "The middle seat count of the parties not named in the table, taken together within each of " + _SIMS + "."),
    Say(r"seats\.OTHERS\.p5", "seats", M,
        "The low end of the range of seats held by the parties not named in the table: about 1 in 20 of " + _SIMS + " give them fewer."),
    Say(r"seats\.OTHERS\.p95", "seats", M,
        "The high end of the range of seats held by the parties not named in the table: about 1 in 20 of " + _SIMS + " give them more."),
    Say(r"(?:seats|home)\.band", "", M,
        "The share of " + _SIMS + " each party's seat range covers."),
    Say(rf"home\.seats\.(?!others\b){_p}", "seats", M,
        "{Party}'s middle seat count across " + _SIMS + "."),
    Say(rf"home\.seats\.(?!others_){_p}_lo", "seats", M,
        "The low end of {party}'s seat range: about 1 in 20 of " + _SIMS + " give it fewer."),
    Say(rf"home\.seats\.(?!others_){_p}_hi", "seats", M,
        "The high end of {party}'s seat range: about 1 in 20 of " + _SIMS + " give it more."),
    Say(r"home\.seats\.others", "seats", M,
        "The middle seat count of the parties not named in the table, taken together within each of " + _SIMS + "."),
    Say(r"home\.seats\.others_lo", "seats", M,
        "The low end of the range of seats held by the parties not named in the table: about 1 in 20 of " + _SIMS + " give them fewer."),
    Say(r"home\.seats\.others_hi", "seats", M,
        "The high end of the range of seats held by the parties not named in the table: about 1 in 20 of " + _SIMS + " give them more."),
    # --- who is largest, who governs alone -----------------------------------
    Say(r"(?:tile\.p_|home\.p_|p_)(?P<party>da|anc)_largest", "chance", M,
        "The % of " + _SIMS + " where {party} was the largest party."),
    Say(rf"play\.largest\.{_P}", "chance", M,
        "The % of " + _SIMS + " where {party} was the largest party."),
    Say(r"claim\.(?P<party>anc|da|mk)_largest\.share", "chance", M,
        "The % of " + _SIMS + " where {party} was the largest party."),
    Say(r"tile\.p_tied_largest|p_largest_tied|play\.largest_tied|claim\.largest_tied\.share", "chance", M,
        "The % of " + _SIMS + " where two or more parties tied for the most seats."),
    Say(r"tile\.p_alone|home\.p_alone|play\.alone|p_alone", "chance", M,
        "The % of " + _SIMS + " where one party won a majority of the council on its own."),
    Say(r"tile\.p_anc_da|p_anc_da", "chance", M,
        "The % of " + _SIMS + " where the ANC and the DA together held a majority of the council."),
    # --- the excessive-seats clause ------------------------------------------
    Say(r"tile\.p_anc_excessive|ballots\.p_anc_excessive|p_excessive_anc", "chance", M,
        "The % of " + _SIMS + " where the excessive-seats clause applied to the ANC: it won as many wards as its votes entitle it to in seats, or more, so it got no list seats."),
    Say(rf"(?:home|tile)\.p_excessive\.{_p}", "chance", M,
        "The % of " + _SIMS + " where the excessive-seats clause applied to {party}: it won as many wards as its votes entitle it to in seats, or more, so it got no list seats."),
    Say(r"tile\.p_excessive_any", "chance", M,
        "The % of " + _SIMS + " where the excessive-seats clause applied to at least one party."),
    Say(r"tile\.p_excessive_rest", "chance", M,
        "The highest chance, across " + _SIMS + ", that the excessive-seats clause applies to any one party not named beside it."),
    Say(r"home\.overhang_seat_share", "", M,
        "The middle share of the council's seats held by the party the excessive-seats clause applies to most often, in the simulations where it applies."),
    Say(r"home\.overhang_list_share", "", M,
        "The middle share of the party-list vote won by the party the excessive-seats clause applies to most often, in the simulations where it applies."),
    # --- the home page's run stamp and ward counts ---------------------------
    Say(r"home\.generated|generated_date", "", M,
        "The date of This Model's current simulations of the election."),
    Say(r"home\.n_draws|n_draws", "", M,
        "The number of times This Model simulated the election."),
    Say(rf"home\.wards\.{_p}", "wards", M,
        "The wards where {party} is the likeliest winner across " + _SIMS + "."),
    Say(rf"home\.wards_close\.{_p}", "wards", M,
        "The wards where {party} is the likeliest winner but wins in fewer than {safe} of " + _SIMS + "."),
    # --- the two-ballots strip: one typical simulation -----------------------
    Say(r"ballots\.typical\.anc_wards", "wards", M,
        "The wards the ANC wins in the most typical of " + _SIMS + ", the one closest to the middle of every party's range."),
    Say(r"ballots\.typical\.anc_list", "seats", M,
        "The list seats the ANC gets in the most typical of " + _SIMS + ", the one closest to the middle of every party's range."),
    # --- minority administrations --------------------------------------------
    Say(r"minority\.(?P<cand>[A-Z]+)_minority_(?:only_)?(?P<opp>[A-Z]+(?:_[A-Z]+)*?)_opposes?(?:_2021_pattern)?",
        "chance", M,
        "The % of " + _SIMS + " where {cand} has more seats than {opp}, so it can govern as a minority if every other party abstains."),
    # --- the who-can-govern lede ---------------------------------------------
    Say(r"govern\.anc_routes", "", M,
        "The coalitions in the table that include the ANC and not the DA."),
    Say(r"govern\.anc_routes_strong", "", M,
        "The coalitions in the table that include the ANC and not the DA and hold a majority in more than half of " + _SIMS + "."),
    # --- the claims ----------------------------------------------------------
    Say(r"claim\.anc_alone\.count", "", M,
        "The number of the " + _SIMS + " in which the ANC won a majority on its own."),
    Say(r"claim\.anc_alone\.best", "seats", M,
        "The ANC's highest seat count in any of " + _SIMS + "."),
    Say(r"claim\.(?P<party>anc|da|mk)\.median", "seats", M,
        "{Party}'s middle seat count across " + _SIMS + "."),
    Say(r"claim\.mk\.p95", "seats", M,
        "The seat count MK Party reaches or passes in 1 in 20 of " + _SIMS + "."),
    Say(r"claim\.anc_routes\.left_share", "chance", M,
        "The % of " + _SIMS + " where the ANC, the EFF and MK Party together held a majority of the council."),
    Say(r"claim\.anc_routes\.left_median", "seats", M,
        "The middle of the combined seats of the ANC, the EFF and MK Party across " + _SIMS + "."),
    Say(r"claim\.red_lines\.anc_side_share", "chance", M,
        "The % of " + _SIMS + " where every party except the DA, the EFF and MK Party together held a majority of the council."),
    Say(r"claim\.red_lines\.no_red_share", "chance", M,
        "The % of " + _SIMS + " where every party except the ANC, the EFF and MK Party together held a majority of the council."),
    Say(r"claim\.red_lines\.grand_share", "chance", M,
        "The % of " + _SIMS + " where the ANC and the DA together held a majority of the council."),
    Say(r"claim\.red_lines\.three_share", "chance", M,
        "The % of " + _SIMS + " where the DA, ActionSA and the PA together held a majority of the council."),
    Say(r"claim\.red_lines\.three_median", "seats", M,
        "The middle of the combined seats of the DA, ActionSA and the PA across " + _SIMS + "."),
    Say(r"claim\.red_lines\.three_median_when_wins", "seats", M,
        "The middle of the combined seats of the DA, ActionSA and the PA, in the simulations where they hold a majority."),
    Say(r"claim\.soweto\.none_share", "chance", M,
        "The % of " + _SIMS + " where the DA wins none of Soweto's wards."),
    Say(r"claim\.soweto\.some_share", "chance", M,
        "The % of " + _SIMS + " where the DA wins at least one of Soweto's wards."),
    Say(r"claim\.soweto\.da_small_share", "chance", M,
        "The % of " + _SIMS + " where the DA, ActionSA, the PA and the smaller parties outside the ANC, the EFF and MK Party hold a majority, with the DA larger than each of them."),
    Say(r"claim\.soweto\.realistic_given_none", "chance", M,
        "Of the simulations where the DA wins no Soweto ward, the % where it leads a majority with ActionSA and the PA, or with the ANC, as the largest party in it."),
    Say(r"claim\.soweto\.asa_pa_given_none", "chance", M,
        "Of the simulations where the DA wins no Soweto ward, the % where it leads a majority with ActionSA and the PA, as the largest party in it."),
    Say(r"claim\.soweto\.anc_given_none", "chance", M,
        "Of the simulations where the DA wins no Soweto ward, the % where it leads a majority with the ANC, as the larger party."),
    Say(r"claim\.soweto\.holds_given_none", "chance", M,
        "Of the simulations where the DA wins no Soweto ward, the % where it leads no majority, either with ActionSA and the PA or with the ANC."),
    Say(r"claim\.soweto\.realistic_given_some", "chance", M,
        "Of the simulations where the DA wins at least one Soweto ward, the % where it leads a majority with ActionSA and the PA, or with the ANC, as the largest party in it."),
    Say(r"claim\.soweto\.some_count", "", M,
        "The number of the " + _SIMS + " in which the DA wins at least one of Soweto's wards."),
    # the 490,000 claim on both ballots (Helen Zille, News24, 20 October 2026)
    Say(r"claim\.zille_both\.votes", "", "Helen Zille, News24",
        "The votes she said the DA needs on each of the two ballots."),
    Say(r"claim\.zille_both\.total", "", M,
        "The middle total of votes on each of the two ballots across " + _SIMS + "."),
    Say(r"claim\.zille_both\.share", "", M,
        "Helen Zille's figure as a % of the votes This Model expects on each ballot."),
    Say(r"claim\.zille_both\.reach", "", M,
        "The number of the " + _SIMS + " in which the DA wins at least Helen Zille's figure on both ballots."),
    Say(r"claim\.soweto\.wards_n", "wards", M,
        "The 2026 wards This Model counts as Soweto, from the addresses of their voting stations."),
    # the 490,000 claim (Helen Zille, Business Day): figures tested on 7 August
    Say(r"claim_zille_votes", "", "Helen Zille, Business Day",
        "The registered DA voters she said must vote for the DA to win an outright majority."),
    Say(r"claim_poll_2021", "", IEC21,
        "The votes cast on each ballot paper in Johannesburg's 2021 election."),
    Say(r"claim_490k_of_2021", "%", IEC21,
        "Helen Zille's DA vote target as a % of the votes cast in Johannesburg in 2021."),
    Say(r"claim_others_shed", "", IEC21,
        "The votes every other party would have to lose for the DA to double its vote while the total stays at the 2021 level."),
    Say(r"pub0807_claim_others_shed", "", IEC21,
        "The votes every other party would have to lose for the DA to double its vote while the total stays at the 2021 level, as the test of 7 August published it."),
    Say(r"claim_hi_turnout", "%", "IEC past results",
        "The highest turnout on record in Johannesburg's voting districts, weighted by their registered voters."),
    Say(r"claim_poll_base", "", M,
        "The votes This Model expected in Johannesburg: registered voters times its expected turnout."),
    Say(r"claim_prop_seats", "seats", M,
        "The seats the DA would hold if its seats matched its share of the vote " + _SURGE + "."),
    Say(r"claim_poll_surged", "", M, "The votes cast in Johannesburg " + _SURGE + "."),
    Say(r"claim_half_surged", "", M, "Half the votes cast in Johannesburg " + _SURGE + "."),
    Say(r"claim_da_votes_surge", "", M, "The DA's votes " + _SURGE + "."),
    Say(r"claim_da_share_surged", "%", M, "The DA's % of the vote " + _SURGE + "."),
    Say(r"claim_da_median", "seats", M, "The DA's middle seat count across the simulations " + _SURGE + "."),
    Say(r"claim_short_by", "seats", M,
        "The seats by which the DA's middle count fell short of a majority " + _SURGE + "."),
    Say(r"claim_anc_wards_surged", "wards", M, "The ANC's average ward wins " + _SURGE + "."),
    Say(r"claim_anc_entitlement_surged", "seats", M,
        "The seats the ANC's votes would give it in proportion " + _SURGE + "."),
    Say(r"claim_anc_collapse_seats", "seats", M,
        "The ANC's middle seat count in the simulations where the DA reached a majority " + _SURGE + "."),
    Say(r"claim_vote_share_needed", "%", M,
        "The % of the vote the DA would need for a majority with the ANC on its expected ward wins, in a one-off seat calculation."),
    Say(r"jhb_2021_coalition_parties", "", "News24",
        "The parties in Mpho Phalatse's coalition government in Johannesburg, formed after the 2021 election."),
    # --- /your-forecast/ ------------------------------------------------------
    Say(r"play\.others_count", "", M,
        "The parties outside the named rows that win a seat in at least one of " + _SIMS + "."),
    Say(rf"play\.roll\.{_G}", "", M,
        "The % of Johannesburg's registered voters who are {group}, as This Model estimates the 2026 roll."),
    Say(rf"play\.turnout\.{_G}", "", M,
        "The average turnout of {group} registered voters across " + _SIMS + "."),
    Say(rf"play\.votes\.{_P}\.{_G}", "", M,
        "The % of {party}'s votes This Model places among {group} voters."),
    Say(rf"play\.bye\.w_bye_1\.{_P}", "seats", M,
        "How far {party}'s middle seat count moves from the forecast when the by-elections since 2021 count fully."),
    Say(rf"play\.bye\.w_bye_0\.{_P}", "seats", M,
        "How far {party}'s middle seat count moves from the forecast when the by-elections since 2021 do not count at all."),
    Say(r"play\.closeness_large_parties", "", M,
        "The parties with the most seats in our prediction whose closeness, taken together, counts twice as much as the other parties' in the badge."),
    Say(r"play\.max_figure_se", "seats", M,
        "The largest standard error a figure on this page may have before the page withholds it: how far, typically, the figure would move if the same number of simulations were made again."),
    # --- the run and the council ---------------------------------------------
    Say(r"council_size", "seats", "Municipal Structures Act",
        "The number of seats on Johannesburg's council, set under the act."),
    Say(r"majority", "seats", "Municipal Structures Act",
        "The seats a majority of the council needs: more than half of them."),
    Say(r"n_vds", "", M, "The voting districts This Model simulates in Johannesburg."),
    Say(r"anc_entitlement", "seats", M,
        "The ANC's middle seat count across " + _SIMS + " if every party's seats matched its votes exactly."),
    Say(r"anc_ward_median", "wards", M, "The ANC's average ward wins across " + _SIMS + "."),
    Say(r"anc_list_share_median", "", M, "The ANC's middle share of the list vote across " + _SIMS + "."),
    Say(r"pub1021_asa_support", "", "Owner's call",
        "ActionSA's expected share of the list vote as set by hand in place of This Model's own estimate, from 21 October 2026 until the call was withdrawn on 23 October."),
    Say(r"record_cope_second_lge_kept", "", "IEC local election results",
        "What COPE kept of its 2011 share of the party-list vote at its second local election, in 2016, taken over the eight metros together."),
    Say(r"small_party_share", "", M,
        "The share of the party-list vote under which a party counts as small, in the test of past local elections."),
    Say(r"small_party_surge_share", "", M,
        "The share of the party-list vote a small party must pass at the next election to count as having surged."),
    Say(r"small_party_record_cases", "", "IEC local election results",
        "The times, in the eight metros' local elections from 2006 to 2021, that a party had under {small} of the party-list vote at one election, each counted against the next; a party that did not stand at the next counts at 0."),
    Say(r"small_party_surge", "chance", M,
        "The % of " + _SIMS + " where a party that stood in 2021 and averages under {small} of the party-list vote takes more than {surge}."),
    # --- earlier editions, as published --------------------------------------
    Say(r"pub0808_n_draws", "", M, "The number of times This Model simulated the election, " + _AS_PUBLISHED + "."),
    Say(r"pub0831_p_da_largest", "chance", M,
        "The % of simulations where the DA was the largest party, " + _AS_PUBLISHED + "."),
    Say(r"pub0831_p_excessive_anc", "chance", M,
        "The % of simulations where the excessive-seats clause applied to the ANC, " + _AS_PUBLISHED + "."),
    Say(r"pub0831_anc_entitlement", "seats", M,
        "The ANC's middle seat count if every party's seats matched its votes exactly, " + _AS_PUBLISHED + "."),
    Say(r"pub0831_anc_ward_median", "wards", M, "The ANC's average ward wins, " + _AS_PUBLISHED + "."),
    Say(r"rev0806_da_largest_first", "chance", M,
        "The % of simulations where the DA was the largest party, in the first forecast the review describes."),
    Say(r"rev0806_da_largest_fixed", "chance", M,
        "The % of simulations where the DA was the largest party, in the forecast after the fixes the review describes."),
    Say(r"rev0806_da_eff_mk_share", "chance", M,
        "The % of simulations where the DA, the EFF and MK Party together reached a majority, in the forecast the review describes."),
    Say(r"rev0806_da_minority_viable", "chance", M,
        "The % of simulations where a DA minority government had the numbers, in the forecast the review describes."),
    Say(r"rev0806_overvote_records", "", "IEC past results",
        "The voting-district results, one per district and election, whose turnout was above the ceiling the review set, a little over the registered voters."),
    # --- outside sources ------------------------------------------------------
    Say(r"asa_2021_seats", "seats", IEC21, "ActionSA's seats on Johannesburg's council after the 2021 election, its first."),
    Say(r"byelection_count", "", "IEC by-election results",
        "The Johannesburg ward by-elections held since the 2021 election."),
    Say(r"bloc_leak_votes", "", "IEC 2019 and 2021 results",
        "The votes the ANC's bloc of parties lost in Johannesburg from the 2019 national election to the 2021 local election."),
    Say(r"hist_da_bloc_change_votes", "", "IEC 2019 and 2021 results",
        "The votes the DA's bloc of parties lost in Johannesburg from the 2019 national election to the 2021 local election."),
    Say(r"hist_asa_pr_2021(?:_rounded)?", "", IEC21,
        "ActionSA's share of Johannesburg's party-list ballot in the 2021 local election."),
    Say(r"hist_asa_npe_2024", "", "IEC 2024 results",
        "ActionSA's share of Johannesburg's national ballot in the 2024 national election."),
    Say(r"hist_laingsburg_da_share", "", IEC21, "The DA's share of the vote in Laingsburg's 2021 local election."),
    Say(r"hist_mayor_2021_for", "", "Business Day, 22 November 2021",
        "The councillors' votes for the DA's candidate, Mpho Phalatse, when Johannesburg's council elected its mayor in November 2021."),
    Say(r"hist_mayor_2021_against", "", "Business Day, 22 November 2021",
        "The councillors' votes for the ANC's candidate, Mpho Moerane, in the same vote."),
    Say(r"byelection_wards", "wards", "IEC by-election results",
        "The Johannesburg wards that have held a by-election since the 2021 election; one ward held two."),
    Say(r"poll_asa_2021_scaled", "", "Ipsos",
        "ActionSA's share in Ipsos's national poll of August 2021, the only independent poll before that election, scaled to the areas ActionSA contested."),
    Say(r"hist_laingsburg_da_wards", "wards", IEC21, "The wards the DA won in Laingsburg in 2021."),
    Say(r"hist_laingsburg_wards", "wards", IEC21, "The wards in Laingsburg in 2021."),
    Say(r"poll_ipsos_w2_(?P<party>anc|da)", "", "Ipsos",
        "{Party}'s share in Ipsos's Khayabus poll of the metros' residents, first quarter of 2026."),
    Say(r"poll_srf_q2_(?P<party>anc|da)", "", "Social Research Foundation",
        "{Party}'s share in the Social Research Foundation's Johannesburg poll published on 5 August 2026."),
)

_COMPILED = [(s, re.compile(s.pattern)) for s in SAYS]

#: Words, not figures, that carry a tooltip of their own: a page writes
#: ``<span class="mstat" data-say="NAME" data-prov="">word</span>`` and
#: ``build_site.word_tooltips`` fills it with :func:`word_says`, in the same
#: pass as every figure's. One line, the owner's structure for a word
#: (2026-10-22, OWNER-DECISIONS 24): "SOURCE: This Model. A ward where the
#: leader wins in fewer than {safe} of {n} simulations.", filled from the run.
WORDS: dict[str, Say] = {
    # the home page's ward sentence (render_home.not_safe_word)
    "not_safe": Say("not_safe", "", M,
                    "A ward where the leader wins in fewer than {safe} of " + _SIMS + "."),
}


def word_says(name: str, facts: Facts) -> str:
    """The tooltip of the word ``name`` (:data:`WORDS`): "SOURCE: <who>.
    <sentence>". Refuses a name with no sentence."""
    if name not in WORDS:
        raise SystemExit(f"tooltip for the word {name!r}: no sentence in "
                         f"tooltip_says.WORDS ({sorted(WORDS)})")
    say = WORDS[name]
    return f"SOURCE: {say.who}. {_fill(say, re.fullmatch(re.escape(name), name), facts)}"


def _known(code: str) -> bool:
    import build_play
    import parties
    import render_sheet
    return (code in render_sheet.NAMES or code in build_play.READER_NAMES
            or code in parties.PARTIES)


def _cities() -> dict:
    import build_validation
    return dict(build_validation.CITIES)


#: Names in capitals that take no "the" (owner's call via the coordinator,
#: 2026-10-22: "no 'the' for BOSA and VF+"). The pages' rule ("the " before
#: a name in capitals, ``build_play.roster``) is left as it is: no page prose
#: puts an article before either name, so nothing there disagrees.
NO_ARTICLE = frozenset({"BOSA", "VFPLUS"})


def party_name(code: str, *, article: bool = True) -> str:
    """The reader's name for ``code``: ``render_map.party_label`` (the site's
    one names table, then ``reader_name``); "the " before a name in capitals,
    as every page writes it ("the ANC", "MK Party"), except :data:`NO_ARTICLE`."""
    import render_map
    name = render_map.party_label(code)
    return ("the " + name) if article and name.isupper() and code not in NO_ARTICLE else name


def _list(names: list[str]) -> str:
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def _codes(m: re.Match) -> list[str]:
    """Every party code a match names, upper case."""
    d = {k: v for k, v in m.groupdict().items() if v}
    out = []
    for k, v in d.items():
        if k.startswith("party"):
            out.append(v.upper())
        elif k == "coal":
            out += v.split("+")
        elif k in ("cand", "opp"):
            out += v.split("_")
    return out


def matches(token: str) -> list[tuple[Say, re.Match]]:
    """Every pattern ``token`` matches: the whole name, every party code in it
    a known party."""
    out = []
    for say, rx in _COMPILED:
        m = rx.fullmatch(token)
        if (m and all(_known(c) for c in _codes(m))
                and (not m.groupdict().get("city") or m.group("city") in _cities())):
            out.append((say, m))
    return out


def unsaid(tokens) -> list[tuple[str, int]]:
    """``(token, how many patterns it matches)`` for every token that does not
    match exactly one."""
    return [(t, len(matches(t))) for t in sorted(set(tokens)) if len(matches(t)) != 1]


def unused(tokens) -> list[str]:
    """The patterns no token in ``tokens`` matches."""
    used = {say.pattern for t in set(tokens) for say, _ in matches(t)}
    return [s.pattern for s in SAYS if s.pattern not in used]


def _fill(say: Say, m: re.Match, facts: Facts) -> str:
    import render_map
    import stats
    g = {k: v for k, v in m.groupdict().items() if v}
    vals: dict[str, str] = {"n": f"{int(facts.n):,}"}
    code = g.get("party") or g.get("party2")
    if code:
        vals["party"] = party_name(code.upper())
        vals["Party"] = vals["party"][:1].upper() + vals["party"][1:]
    if "coal" in g:
        vals["coalition"] = _list([party_name(c) for c in g["coal"].split("+")])
    if "cand" in g:
        vals["cand"] = party_name(g["cand"])
        vals["opp"] = _list([party_name(c) for c in g["opp"].split("_")])
        if "_" in g["opp"]:
            vals["opp"] += " combined"
    if "group" in g:
        if g["group"] not in facts.groups:
            raise SystemExit(f"tooltip for {m.string}: no population group {g['group']!r} "
                             f"in this run's spec ({sorted(facts.groups)})")
        vals["group"] = facts.groups[g["group"]]
    if "city" in g:
        vals["city"] = _cities()[g["city"]]
    if "year" in g:
        vals["year"] = g["year"]
    if "ballot" in g:
        vals["ballot"] = g["ballot"]
    needs = set(re.findall(r"\{(\w+)\}", say.says))
    if "n_hist" in needs:
        vals["n_hist"] = f"{int(facts.n_hist):,}" if facts.n_hist else "its"
    if "n_val" in needs:
        vals["n_val"] = f"{int(facts.n_val):,}" if facts.n_val else "its"
    if "val_year" in needs:
        vals["val_year"] = str(facts.val_year or "")
    if "safe" in needs:
        vals["safe"] = stats._fmt(render_map.SAFE, "pct0")
    if "small" in needs:
        vals["small"] = stats._fmt(stats.SMALL_PARTY_SHARE, "pct0")
        vals["surge"] = stats._fmt(stats.SMALL_PARTY_SURGE, "pct0")
    text = say.says.format(**vals)
    return text[:1].upper() + text[1:]


def says(token: str, facts: Facts) -> tuple[str, str, str]:
    """``(unit word, who, plain sentence)`` for ``token``. Refuses a token that
    does not match exactly one pattern: a figure with no sentence, or two."""
    got = matches(token)
    if len(got) != 1:
        raise SystemExit(f"tooltip for {token!r}: it matches {len(got)} patterns in "
                         f"src/tooltip_says.py, not one")
    say, m = got[0]
    return say.unit, say.who, _fill(say, m, facts)
