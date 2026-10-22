# Site text sweep, 23 October 2026

Seven read-only reviewers covered every reader-facing page: home and forecast,
Your prediction with the portal and privacy pages, methodology and sources, the
review and corrections pages, the five articles, the claims pages, and the tone
rules across all of them. Their full reports are beside this file. Checked
again by me: the stale map, the 2021 mayoral vote, the 190,000 figure, the
council sizes, and the seat law. Everything else is the reviewer's evidence,
with the file and line it cites.

**The council never grows.** Schedule 1 item 16 as amended in 2021 keeps the
council at 270; a party that wins more wards than its vote entitles it to keeps
them and gets no list seats, and the other parties share the remaining seats.
This Model does exactly this (`overhang_rule = "deduct"`). The growth reading
came from the original plan, and the review of 6 August still carries it. No
other page says the council grows. `src/seats.py` has the same error in a
docstring.

## 1. Wrong today on live pages, not dated pieces (plain fixes)

| Page | Text | What is wrong |
|---|---|---|
| Home, forecast | the ward map, its tooltips and legend counts | Drawn from the 29 September run and never redrawn. Ward 1 shows "contested, ANC 84%"; the current run gives 91%, solid. The map has MK ahead in 9 wards; the current run has 4. The headline beside it uses current figures. |
| Your prediction | "checked against a full re-run of the model, and every party's seat change agreed" | MODEL-LOG records this is not true of the model now live. |
| Privacy | names only Cloudflare as a host | Your prediction loads its calculation code from jsDelivr, which receives readers' IP addresses. On results night the entries are also copied to the owner's computer to rank them. |
| Portal | "only once its allocator reproduces that city's published 2011, 2016 and 2021 councils" | All seven other metros already reproduce them exactly; what holds them back is the missing 2026 forecast. "136 are needed to govern": 136 is a majority; fewer can govern. |
| Methodology, sources | Stats SA "holds" home language by ward, "we have requested it"; small-area data withheld "because it can identify households" | Stats SA wrote in August that neither exists below municipality level. The Stats SA outreach note links this page. |
| Methodology | GOOD took "one-eighteenth" of the DA's vote | One-sixth (0.9% against 5.6%). |
| Methodology | "Only one such split had happened anywhere before 2021" | The same page names Malema and De Lille; the record holds GOOD and the NFP. |
| Methodology | "In one city the model loses ... Mangaung, the smallest council" | Buffalo City (100 seats) is smaller than Mangaung (101). On seats This Model loses in eThekwini and Cape Town. |
| Methodology | "Every party in this table existed in 2021" | ActionSA first stood in 2021 and is the largest miss. |
| Methodology | names only the census as a possible leak in the test | The test's own record marks eight settings as fitted on data that includes 2021. Home tooltips also call the test "forecasting that election from earlier ones". |
| Methodology | "Your forecast applies three versions of Germany's seat law instead" | Your prediction always seats under South African law; Germany is a comparison. |
| Forecast | "Parties that compete for the same voters trade support" | This Model no longer draws that way; the DA and ActionSA rise and fall together. |
| Forecast | "its one realistic option is ActionSA and the PA: 18%" | With the smaller parties it is 64%; the claim card on the same site rates the same coalition near certain. |
| Forecast | "It is arithmetic on results and registration" | ActionSA's level is your judgement, 17.6%; the forecast page does not say so. |
| Forecast | ▼ marks on Others, the typical simulation, ANC wards | Nothing in the forecast moved; BOSA and the Freedom Front Plus got their own rows. |
| Forecast | "the DUDULA", "Bosa", "Vfplus", "Rise", "src/render_sheet.py", "seed 20261104", "1 seats" | Party codes, a file name and a seed in reader text. |
| Your prediction, forecast | "Germany 2000 law", "Germany 2015 law" | Germany passed no seat law in those years: uncompensated surplus seats until 2013, levelling from 2013. |
| Share image | "grey seats are too close to call" | Grey is the seats the parties' middle counts leave over. |
| Corrections | three entries "corrected 7 October 2026" | They went live on 9 October. |

About 25 smaller items (a missing seal check in the privacy text, the
"Registered" bar described as the roll, "over 9 of every 10" against a ≥ 90%
rule, the ward-count of by-elections, and others) are in the reports.

## 2. Wrong in dated pieces that have been live since 8 August (each needs a correction entry)

| Piece | Text | What is wrong |
|---|---|---|
| Review (6 Aug) | "the step that detects overhang, the council growing beyond 270" | The council stays at 270. Your finding. |
| Review | "never been demonstrated in a published calculation by the electoral commission" | The IEC published the Laingsburg 2021 calculation, and the same page cites it. |
| Review | "Largest party in 63% of simulations" | No run gives 63%; the published run gave 61%. |
| Review | "DA-led minority ... viable in 61%" | That is the council-growth figure; under the law it was 53%. |
| Review | links model-review.html on GitHub | That document describes the council-growth reading. |
| Minority administrations | "abstention installs minority governments — it is how the DA took this mayoralty in 2021" | Phalatse won 144 to 121, a majority of the whole council. The table's "only ANC opposes (2021 pattern)" is wrong for the same reason. |
| Nobody will win, Laingsburg | "the shortfall is taken from every other party" | The remaining list seats are re-divided; in Laingsburg only one party lost a seat. |
| Nobody will win, Laingsburg | "it has fired exactly once" | About 65 of the Commission's seat calculations were searched; Laingsburg is the only case found. |
| Laingsburg | "on just 23% of the vote" | 1,530 of 6,453 is 23.7%. |
| If the law were German | dated 8 August, table regenerated from today's run | A frozen piece printing current figures with no date. |
| Minority administrations | the 8 August text printed an empty figure and was later rewritten | No correction entry records it. |

## 3. Claim cards (dated 7 August to 7 October)

| Card | Text | What is wrong |
|---|---|---|
| Zille, 490,000 | "every other party combined sheds about 190,000 votes" | With the total frozen, the others lose what the DA gains: about 250,000. |
| Zille, red lines | "A majority without the ANC, the EFF and MK" | She ruled out the EFF and MK only. The 93% beside "except the ANC" excludes all three. |
| Mashaba, Soweto | "the roll adds a ward to Soweto: 41" | No ward was added; ward 29 crossed this site's own 50% cut. Also "Inside Metros" links Inside Politics, and "80%" rests on about 10 simulations. |
| Zille, 490,000 | "what Helen wanted", "a turnout fantasy", "a special universe" | The only speaker called by first name; STYLE.md cites these exact phrases as wrong. |

## 4. Tone

The tooltips follow the rules; they are the only text a test checks. Elsewhere:
about 60 uses of "the model" where the rule says "This Model"; "forecast"
where a reader's prediction is meant, mostly in the home page's Your Forecast
block; and the page is named both "Your prediction" and "Your Forecast".
STYLE.md lags your decisions of 5 and 13 October, and four rules ("This
Model" in body text, corrections only of what was live, all parties or none,
the banned words) exist only in my notes, not in the repository.

## 5. Not reader text

The public GitHub repository is at 27 August (main) and 24 September
(remediation, 771 commits behind). The emails say the code is public.
