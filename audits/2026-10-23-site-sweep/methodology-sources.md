# Methodology and sources pages — reviewer report, 2026-10-23 (read-only agent)

1. "The over-winner stays slightly over-represented; the cost falls on everyone else" / "always close to proportional": Laingsburg DA 3 of 7 on 23%; ANC median 72 vs entitlement 59. methodology.md:25-28. Misleading.
2. "catches the ANC in 90% ... a citywide vote in the mid-twenties": ANC list mean 21.2% (16.1-26.2), low twenties; 90% includes exactly-equal cases where no squeeze happens. methodology.md:30-31. Out of date.
3. "home language by ward, which Stats SA holds but does not publish ... we have requested it": Stats SA 24 and 27 Aug — not available at ward level; finest is municipality (SOURCES.md:494-504). FALSE. methodology.md:72-74; model-claims.toml four-census-pools. (Also SOURCES.md:476 "Requested" stale.)
4. "Income, employment and dwelling type ... request-only, since at ward level they can identify households": no Census 2022 SAL exists; not confidentiality (SOURCES.md:478-492). FALSE. methodology.md:74-76.
5. "Population group is the only ward-level characteristic Stats SA publishes": also age and sex. FALSE (minor). methodology.md:68-69.
6. GOOD "about one-eighteenth as much of the DA's vote in Johannesburg as in Cape Town": 0.0095 vs 0.0558 = about one-sixth (pools.py:3317-3318). FALSE. methodology.md:149-150.
7. "Only one such split had happened anywhere before 2021": page names Malema and De Lille; record holds GOOD and NFP. FALSE. build_validation.py:326-344; pools.py:3788.
8. "In one city the model loses ... Mangaung, the smallest council": Buffalo City (100) smaller than Mangaung (101); on seats This Model loses in eThekwini and Cape Town and ties in Mangaung and NMB. FALSE. build_validation.py:349-350.
9. Only the census is named as possible leakage; history.json marks eight inputs in-sample for JHB 2021 (level_shrink, turnout_correlation, dirichlet_scale, entrant_prob, entrant_share, contestation_expand...). Misleading. build_validation.py:191-195, 318-325.
10. "The seat columns judge only the single most likely outcome": it is each party's median; Johannesburg printed as 48 "seats given to the wrong party" and 96 "seats out" with no stated relation. Misleading.
11. Uniform swing described as "the national swing since the last election": code uses the city's own national-election change across the two national elections either side of the previous local (benchmarks.py:440-476). Misleading.
12. "Every party in this table existed in 2021": ActionSA first stood in 2021 and is the largest miss (-29 seats). Misleading.
13. JUDGEMENT-CALLS §H1 Plain: "Your forecast applies three versions of Germany's seat law instead; two of them enlarge the council": Your Forecast seats under SA law; Germany is comparison only. FALSE. JUDGEMENT-CALLS.md:1944-1947.
14. Heading "Overhang's legal fine print is untested in court": "overhang" is the German growth term; use excessive-seats clause. Wording.
15. §A57 Plain "Part of each simulation's move is shared by all parties": shared loading is zero from 20% up (DA, ANC share none). Misleading.
16. Polls: "one house had the DA on 42% ... another had the ANC on 35%": SRF is CoJ, Ipsos is an all-metro subsample. Misleading.
17. "pre-2021 polling missed ActionSA in this city by about ten points": no independent JHB poll; scaled national poll implied ~6% vs 18%, ~12 points. Typed. Misleading.
18. ActionSA "17.6%" typed in prose, not a token. Wording.
19. "Turnout, per pool. It is the one unknown quantity": party support is also drawn. Misleading.
20. "the model" in title, headings, column headers. Wording.
21. "872 voting districts": IEC snapshot sums to 862; 872 is the MDB layer. Minor, unresolved.
22. Display: duplicate "Independent" rows (Ekurhuleni); truncated names ("Active Citiz" ...); raw codes "Dop", "Rct".
S1. sources.md:67-69 small-area data "not published, because ... can identify households. Access under conditions exists": no SAL exists; not confidentiality. FALSE.
S2. sources.md:54 "Fifteen Johannesburg wards have held by-elections": 15 contests in 14 wards. FALSE (minor). Typed.
S3. "The model rests on six elections": turnout range also reads 2000 and 2006; registration 2009. Misleading.
S4. "the model" throughout sources page.

Checked true: council 270 (135+135), combined vote entitlement, deduct rule at fixed 270, Laingsburg, majority 136, 26 Sep roll and VD placement, four pools, equal registration assumption, joint pool fit, ActionSA 17.6% judgement, turnout fell in every group 2021, turnout range (own binds in all four), district pattern 0.5±0.25 with w_recency 0.70, turnout correlation 0.63, by-elections half weight, mergers 0.75, no polls, 5,000 draws, validation 30 Sep 400 draws, validation table values, 24 city-year seat reports present, six implementation errors.
Not verified: IEC correspondence; "Other" ~0.5%; Al Jama-ah / PA pool fractions (describe as 2021 fit); Cape Town entrants claim; seat law exact for 24 city-years (MACHINERY.md:799 says 6); sign-up weekends line; blind ward-call test 129/135.
