# Articles and commentary — reviewer report, 2026-10-23 (read-only agent)

None of the six pages says the council grows; all describe a fixed 270, majority 136. Live = in archive/live-deployed-2026-08-08/index.html.

1. minority-administrations + commentary standfirst: "abstention installs minority governments — it is how the DA took this mayoralty in 2021." FALSE: Phalatse won 144 to Moerane's 121 (265 of 270 voted; 144 > 136); EFF voted for DA candidates (Daily Maverick 23 Nov 2021). forecast-sheet.html:403-405; articles.toml:55-56. Live. Correction note. Proposed: "The mayor needs a majority of the votes cast, not of the council, so councillors who stay out of the vote lower the bar. In 2021 the DA's candidate won with 144 of 265 votes, after the EFF voted for her."
2. minority table label "DA minority, only ANC opposes (2021 pattern)": FALSE of 2021 (121 opposed > ANC's 91). src/coalitions.py:220. Plain fix "DA minority, only the ANC opposes" + note.
3. "the shortfall is taken from every other party" (nobody-will-win standfirst, commentary, body; laingsburg "squeeze ... onto everyone else"): MISLEADING — remaining list seats are re-divided; in Laingsburg only the KDF lost a seat; in This Model's firing draws on average 46% of other seat-holders lose a seat (DA 98%, IFP 24%, Al Jama-ah 15%). Proposed: "the seats it is owed beyond its share come out of the other parties' list seats, mostly the larger ones." Live. Correction note.
4. "it has fired exactly once" / "The only place the clause has fired": record supports "the only case we found" — ~65 of ~213×3 seat calculations scanned (MODEL-LOG:561-563); subitems in force from 1 Nov 2021. Live. Correction note or scan all 2021 reports.
5. Since-then boxes "about 68 wards on a 59-seat entitlement" / "central case": token anc_ward_median reads the MEAN (67.6); median is 72; 59 is a Germany-2023 counterfactual median — mean vs median. stats.toml [anc_ward_median]. Plain fix.
6. If the law were German: dated 8 Aug but table regenerates from current run with no date or Since-then box (8 Aug: DA 79, ANC 74; council 270/279/308/270). Breaks frozen-piece rule.
7. Minority administrations: 8 Aug passage printed an empty figure ("viable in — of simulations") and was rewritten later with no correction or note. Live both. Correction note.
8. Laingsburg "on just 23% of the vote": cited report gives 1,530 of 6,453 = 23.7%. Token 0.2306. Minor.
9. nobody-catches since box "The finding holds in the new grouping": no measurement recorded (c60cd14 reworded, no evidence). Unverifiable.
10. nobody-catches: "ANC bloc" never defined (ANC alone lost 451,076; ANC+EFF ~585,000); "became abstention" inferred from net totals although every national->local transition drops; ActionSA "18%" is party-ballot share (combined 16.2%). Wording.
11. German labels "2000, 2015 and 2023" name years in force, not enactments (levelling 2013); caption order appears swapped. Wording.
12. "elected by councillors *present and voting*": italics read as statute; Sch 3 item 6(c) says "a majority of the votes"; s160(3)(a) quorum omitted. Wording.

Checked true: two ballots combined set entitlement; ward to highest total; ward wins deducted; item 16(3)-(8) keeps council fixed (every draw 270); Laingsburg arithmetic (DA 3 wards, entitlement 2, quota 1,231, KDF 2->1, council 7); thirty-eight-fold; German prose; biggest ANC collapse 2019->2021; DA+ActionSA fell ~50,000; mayor elected by secret ballot (Sch 3 items 6-7).
Not verified: MEC notice for 270/135; Laingsburg party-ballot share; "first time in democratic history"; exact 587,000 and 52,000 bloc membership; how parties voted in 2021 (secret ballot).
