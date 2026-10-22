# Review and corrections pages — reviewer report, 2026-10-23 (read-only agent)

All review items below were live from 8 August (archive/live-deployed-2026-08-08/review.html).

1. review.md:60-64, owner's paragraph. (a) "ward winners never counted": TRUE of the first forecast (e434fee montecarlo.py:202; MODEL-LOG §1.14 E3; first ward winners 3e45354). (b) "the council growing beyond 270": FALSE — Act 3 of 2021 Sch 1 item 16(3) keeps C = council seats; Laingsburg 2021 stayed at 7 (§1.17, which said the growth narrative "must be corrected site-wide"); code default overhang_rule="deduct" (montecarlo.py:384). Missed by efb2e5b's site-wide law fix; page contradicts its own "inside a fixed 270" bullet. (c) "modal outcome": true of excessive seats (ANC 90% today), false of council growth. Remedy: correction entry. Proposed text: "...which is the step that detects excessive seats: a party winning more wards than its vote entitles it to. It keeps those wards and gets no list seats, and the other parties share the remaining seats of the fixed 270-seat council. The plan had flagged this as a live risk. It happened in most simulations, and the first forecast could not see it."
2. review.md:111-113 "never been demonstrated in a published calculation by the electoral commission ... awaiting its answer": FALSE at deploy — IEC's published Laingsburg WC051 2021 seat calculation has an "Excessive Seat Calculation" block (§1.17; PDF in audits/2026-10-09-site-batch/law/sources/). Correction entry.
3. review.md:95-96 "Largest party in 63% of simulations, not 86%": no run gives 63%; §1.18 gives 61% for the 6 Aug run; 8 Aug live home 62%; token source points at the page itself (stats.toml:416-423). FALSE.
4. review.md:100-102 "DA-led minority ... viable in 61%": the expand-rule figure (§1.15-1.16); deduct gives 53.0% (§1.16). FALSE.
5. review.md:91-92 "roughly six of seven simulations": matches 5 Aug runs; the 8 Aug published run showed 96%. Out of date at publication.
6. review.md:14-15 link "model-review.html on GitHub": the linked document states the wrong law (council expands to ~281); 210a8ae archived it; the link 404s once local main (contains 210a8ae, not an ancestor of origin/main) is pushed. Plain fix.
7. review.md:79-81 "87 district-year records where more people had voted than were registered": the 87 are turnout above 105% (3e45354). Minor.
8. Since-then box "The figures below describe the first version ... kept as published": figures describe the corrected second version; title and opening paragraph were rewritten 21 Oct (5c35ade, owner's brief). Plain fix.
9. corrections.md:23,29,35 three headings "corrected 7 October 2026": went live 9 October (ledger: no deploy between 2026-10-06T23:29Z and 2026-10-09T01:26Z). Plain fix of dates.
10. No correction entries exist for review items 1-5, 7.
11. site/changes.json: no page reads it; 9 "material" rows moved only because BOSA and FF+ got their own seat rows (same forecast hash). Latent.

Checked true: e434fee claims; six coalitions; DA+EFF+MK 61%; DA largest 86% first forecast; six errors fixed same day; plan expected MK to underperform; fifteen by-elections; blind seat error five times larger (12 vs 60); kingmaker flip; item 16 description "inside a fixed 270"; since-box figures match ledger; correction entries 47%/45%, 59%, 587,000, 6.22%, 181 split VDs, 560,000, 57%->78%, 59%->87% match ledger.
Not verified: IEC reply to 5 Aug question; Zille 13 Sep date; 31 Aug column values; "adjustable dials" sentence; 6 Aug DA-minority figure.
