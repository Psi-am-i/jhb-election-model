# Home, forecast page, share image — reviewer report, 2026-10-23 (read-only agent)

1. Ward map, tooltips, legend counts, council bar (home + forecast): from the 29 Sep run (02fe902); render_map.py not re-run after 21 Oct. VERIFIED by me 2026-10-23: site Ward 1 "contested, ANC 84%", current ward_winner_probs.csv (21 Oct) ANC 0.9097; map's first-named leaders among contested wards include MK 9, current MK leads 4. Headline uses current file (77/45). Bar shows BOSA 16, VF+ 8 (outside their 90% ranges). Fix: re-run render_map.py. OUT OF DATE, live.
2. Map bar and two-ballots figure use different "typical simulations" (KEY_PARTIES -> 3869 vs named_parties -> 633); comment at render_map.py:348 says same. Misleading.
3. Forecast: "If the DA rules out the ANC, the EFF and MK, its one realistic option is ActionSA and the PA: 18%": with small parties 64%, all others 77.5%; contradicts claim card's NEAR CERTAIN. render_sheet.py:681-683.
4. "Parties that compete for the same voters trade support: when one rises ... the others tend to fall": current draw has no within-pool competition (montecarlo.py:420-428, 4691-4703); DA–ActionSA seat corr +0.40; only ANC–MK -0.73. forecast-sheet.html:232-233.
5. Backtest described as "forecasting that election from earlier ones": history.json manifest verdict IN-SAMPLE for joburg 2011/2016/2021 (fitted constants include level_shrink, pools, turnout_correlation...). tooltip_says.py:330,334; home.toml:46-49.
6. "It is arithmetic on results and registration" / "A new party is sized from history": ActionSA level set by owner judgement at 17.6% (JUDGEMENT-CALLS §SJ2) — not stated on forecast page. forecast-sheet.html:450-452.
7. ▼ arrows report a row redefinition (BOSA/VF+ own rows, 746397a) as forecast movement: Others 16->12, simulation 3128->633, ANC wards 73->72. Same simulations.
8. Share image "grey seats are too close to call": grey is seats the middles leave over (259 of 270). play-card.js:54.
9. Footer "Baseline 2024 provincial ballot": starting level blends 2024 and 2021 local. forecast-sheet.html:492. Also JUDGEMENT-CALLS §SJ2 says ActionSA 6.22% is "2024 national ballot"; SOURCES.md:61 says provincial.
10. "everything observed since 2006" and source list from 2011: 1999-2009 JHB files and all eight metros used. forecast-sheet.html:426, 476-479. (Files present; reading not confirmed by a run.)
11. Home card "Each source file is listed with its checksum": sources page has no checksums (they are on GitHub). home.html:191.
12. Footer "generated from the model outputs by src/render_sheet.py", "ward winners & overhang", "seed 20261104". Wording.
13. Party codes as names: "the DUDULA 7.9%", "Bosa", "Vfplus", "Rise". render_sheet.py:540; render_map.py:367.
14. "eight cities" typed, not token (backtest_cities). home.html:207-208.
15. Slips: "Figures generated 21 October 2026 ◆ ... Was 21 October 2026"; "1 seats"; "in over 9 of every 10" vs >= 0.90; heading "Seats, if the election were held now" (no poll input; election-day projection).
Teaser "The clause has fired exactly once before": record supports "the only case found" (~65 reports scanned).

Checked true: council 270 / 136 in all draws; law text matches item 16 and code; IEC asked 5 Aug, no reply recorded; 135+135; "27% of the seats on about 22%"; ANC+DA 56.5%, next pair 1.3%; ActionSA 1 ward 49 list in sim 633; ANC-without-DA 6 majorities; 15 by-elections half weight; polls off; certified roster; entrant sizing; ActionSA 44 in 2021; eight cities and three baselines; share image figures match tokens.
Not verified: "First issued 5 August 2026"; "Each version is reviewed against its own plan"; pre-2011 files read by the 2026 run; share-image map vs today's probabilities; 136 from the Act.
