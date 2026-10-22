# Your prediction, portal, privacy — reviewer report, 2026-10-23 (read-only agent)

1. Your prediction note 2: "checked against a full re-run of the model, and every party's seat change agreed within sampling error." FALSE now — MODEL-LOG.md:30516 says this rests on §1.271 under the old law and "is not true of the shipped law"; §1.315 (MODEL-LOG.md:30474): re-run moves ANC -0.035 seats vs re-weight DA -4.10. Limit: §1.315 shifted the band mode, §1.271 drawn turnout. interactive/your-forecast.html:360-364.
2. Portal footer: "A city appears here with numbers only once its allocator reproduces ... exactly — until then 'in preparation'". FALSE — all seven reproduce 2011/2016/2021 exactly (tests/test_seats.py); gate is a 2026 forecast file existing (build_portal.py:48). build_portal.py:134-138.
3. Seat-law labels "Germany 2000 law" / "Germany 2015 law": no German law of 2000 or 2015; overhang uncompensated until 2013, levelling from 2013. render_sheet.py:276-277 -> laws.json. Proposed "Germany before 2013", "Germany 2013 law". (Also flagged by articles reviewer.)
4. Note 1: "your settings are not recorded": opening the share sheet seals and stores the prediction (play-share.js:12-18; share-edge.js:343); settings travel in the link (yf-url.js:48). MISLEADING.
5. "'Registered' is the split of the voters' roll" / "percentage points of that group's registered voters": the roll has no population group; it is the roll split by ward census shares (pools.py:1524-1526). MISLEADING.
6. Poll control: accuracy "from its sample size, the polling house's typical miss and the time since fieldwork": also an undisclosed-screen allowance; the miss is one figure for all houses (polling.py:165, 376-381). MISLEADING.
7. Portal: "136 are needed to govern": 136 is a majority; fewer can govern. build_portal.py:95.
8. Portal: other metros' seat and ward counts are 2021 figures (cities/*.toml). Unverified against 2026 determinations.
9. og:description "let's see if you can beat us on election day": no house entry is ranked; ranking after the count. og_pages.py:88-89.
10. "ranked against the result on election day": after the count. share-card.js:118.
11. "The leaderboard shows names after the count": privacy page allows for no leaderboard. build_your_forecast.py:117; arrival.js:141.
12. Badge note "the largest parties ... count double": the six largest parties' mean counts twice the others' mean (reweight.py:1189-1190; JUDGEMENT-CALLS §N10).
13. Privacy: Your prediction loads Pyodide/numpy from cdn.jsdelivr.net — third party gets IP; page names only Cloudflare. FALSE by omission. privacy.md:135-148.
14. Privacy: "The only records ... held by Cloudflare": entries exported to the owner's computer on results night (~/joburg-entries.json; rank_entries.py:57-60). MISLEADING.
15. Privacy: "three things happen on the site's server": also a seal check when opening someone's link (make.js:394; nothing stored). Low.
16. Privacy: "to Your Forecast": page is now "Your prediction". privacy.md:41.
17. Loading/error strings name internals or give a developer command ("Run `node interactive/tools/sync_py.mjs` and reload."). reweight-engine.js, seat-engine.js, model.js.
18. Map tooltip "in over 9 of every 10": threshold is >= 0.90. render_map.py:160.
Not reader text: src/seats.py:373-374 docstring says overhang "pushes the council above total_seats" — wrong under deduct.

Checked true: SA law label and note 7 (council fixed); German laws labelled for comparison and never shared; majority 136; p5-p95 range; thresholds; 5,000 draws; by-elections half weight; badge bands; ranking order; seals close 07:00 4 Nov; stored columns match privacy list, no IP/UA/cookie; rate limit; cache times; short links; no accounts; only theme in localStorage; leaderboard gitignored; poll notes; BOSA/MK/Rise splits from 2024.
Not verified: seat Worker logging; 4 Nov / 07:00 proclamation source; D1 recovery; other metros' 2026 sizes; "Others (67 parties)" vs 81; published run "-dirty".
