# Tone rules — reviewer report, 2026-10-23 (read-only agent)

## The rules and where they live
- STYLE.md rules 0-11 (repo; CLAUDE.md §1 points at it).
- In memory only, not in the repo: "This Model" for body copy (repo has it only for tooltips: audits/2026-10-22-tooltips/BRIEF.md, src/tooltip_says.py); corrections cover only text that was live, heading format; no party singled out as an equal-treatment rule (STYLE 7 covers ordering and verdict words only); the banned-word list (~/CLAUDE.md rule 7: simply, actually, of course, in fact, turns out, it is worth noting), which STYLE.md lacks.
- Publication convention (pieces frozen, "Since then" notes): memory + PUBLISHING-BACKLOG.md:462.

## Contradictions and gaps in the rules
1. STYLE 3 says corrections' second part is "What changed"; the site and SITE-TEXT.md say "What is right" (owner, 2026-10-05, 0822586).
2. STYLE 11 cites "Analyse my forecast"; page says "Analyse my prediction" (test asserts old wording absent).
3. STYLE 1's good example says "the model's forecast", which the "This Model" rule forbids.
4. STYLE 6 allows "pools"/"draws" where explained; the "This Model" rule says always replace.
5. Scope of "This Model" undefined for plain "the model" in body prose.
6. STYLE 7's own bad examples ("fantasy", "special universe") are live on a dated claim card.
7. Enforcement: tooltip line 2 only (test_tooltip_says) and named regions (test_your_forecast_page). Nothing scans body prose, data-tip, meta descriptions, aria labels.

## Live text — violations
A. "the model"/internal terms (~60): index 7, sources 9, your-forecast ~8 + 4 JS strings, support 4, privacy 2, methodology 3, forecast 2, 2 meta descriptions; header template "21 October 2026◆: what the model says now" ×12.
   Hard leaks: forecast footer "generated ... by src/render_sheet.py", "seed 20261104", "(simulation 633▼)" with tooltip "633 since 22 October. Was 3128"; "the DUDULA 7.9%"; bar data-tips "Bosa", "Vfplus", "Rise", "ActionSA — 1 seats"; minority-administrations "DA+ASA"; "ward winners & overhang", "Schedule 1 item 16 applied"; methodology heading "Overhang's legal fine print..."; "(model log, §1.296)", "The poll channel's contribution", "a no-polls model", "the run prints"; home "Model run 21 October 2026", "Each run uses different values"; your-forecast "Loading the re-weighting code.", JS "The re-weighting code refused"; portal ×8 "backtest", "allocator"; claim since-note "The turnout setting this test used is no longer in the model"; page footers "generated from docs-public/corrections.md on 2026-10-22".
B. forecast/prediction/result (~19): home "Your Forecast" block ×7 (forecast → prediction); your-forecast "a changed forecast"; forecast.html "The most typical result: ... the one closest to the middle"; "in one typical simulation" (owner said reads as random); map aria-labels "predicted winning party"; "a party, a coalition or a result"; "not a prediction that the deal is made". Page name inconsistent: nav/title "Your prediction", privacy "Your Forecast", methodology "your forecast" ×8. Privacy: "A prediction you make on your prediction lives in its link" garbled.
C. Lilt / telling the reader what matters (~12): home lede "and it has a quirk", "That is surprisingly likely this year" (came in 64ef092 as owner's lede — check); "but not just any values"; your-forecast "But historical trends can always be broken."; methodology "the hardest part of forecasting", "hardest and most direct test", "the best-tested idea", "hard to beat"; forecast duplicate "arithmetic, not a judgement" line; "Polls are not an input" ×3 in footer; repeated "X's split is estimated..." ×3; "actually won" column headers ×8; portal em-dash asides ×8.
D. Tooltips: 562 correct. Failures: "21 October 2026." ×18 on claims.html (year printed, no "since"); "Is now 68." etc ×6 on laingsburg / nobody-will-win (one line, no SOURCE). Ward and bar data-tips use another structure (em-dash, no SOURCE) ×135 ×2 pages — brief says "identical everywhere". ~45 line-2 sentences over 170 chars (excessive-seats one rendered 8 times).
E. Corrections saying more than two parts (4): the 560,000 roll entry explains method; "57%" entry says what isn't; "deliberate choice" entry names a page that no longer exists; four-figures entry adds a table and arrow explanation.
F. Party singled out (2): methodology ActionSA level "set by our judgement instead, at 17.6%" (model question for owner); forecast coalition box fixed "DA without the ANC, EFF or MK" filter + "its one realistic option" (offset by ANC-without-DA box).
G. No banned filler words otherwise; no first person.

## Frozen text (dated note, not rewrite)
Articles (8 Aug) and review (6 Aug), ~45: em-dash asides, "simply" ×3 (german), "actually", "quietly" ×3, "In truth", "Genuinely blind", "absurdly confident", "modal", "overhang", "draw". Teasers reprinted on LIVE pages (home, commentary, every article footer): "Nobody will win Johannesburg — and an obscure voting law…", "— it became abstention", "The only place the clause has fired —". Live "Since then" notes: nobody-catches "The model then grouped voters ... The finding holds" (mechanism talk, "still holds"); nobody-will-win "still triggers".
Dated claim cards (7 Aug, 26 Sep, 7 Oct), ~30 — owner to rule whether frozen: "turnout fantasy", "special universe", "Helen" ×2, "At first glance it looks plausible, until you realise", "Not close.", "a two-horse race", "So what about 2026?", "All told, Mashaba is probably correct.", "Our model uses no poll at all ... actually voted", "draws" ×3, garbled Mashaba lines ("three realistic partners: ActionSA with the PA, or the ANC"), "The model counts seats"; DA-and-ActionSA-only turnout scenario (party-specific, later withdrawn) still named in 12 tooltips.

## Verdict
Tooltips follow the rules (the only text with a test). Body prose has no guard and fails most on "This Model" (~60) and forecast vs prediction (home block, page name). STYLE.md lags the owner's decisions of 5 and 13 October; several rules live only in memory. Scope decision for the owner: are dated claim cards frozen?
