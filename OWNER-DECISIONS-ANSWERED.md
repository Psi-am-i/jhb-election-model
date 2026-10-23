# Owner decisions, answered

Each item as it stood when you answered it, newest first, with your words and
where the change was recorded. Open questions are in `OWNER-DECISIONS.md`.

---

### 31. Before the freeze: test two inputs the backtest never checks? — answered 2026-10-23

**Context.** The data audit (`rounds/2026-10-23-out-of-sample/DATA-USE-AUDIT.md`)
found two inputs of the 2026 forecast that no backtest scores:
- **By-elections.** Their pull on each party's share, the turnout tilt and the
  ward-level term act only in Johannesburg 2026.
- **γ (how much of each party's ward pattern carries over).** The forecast reads
  the 2014→2016 fit, kept so the 2019→2021 fit stays a validation set; every
  backtest reads the most recent fit.

**Options.**
1. Before 31 October, run the forecast with by-elections off, and with γ from
   2019→2021 and from both pooled, and send you an old-vs-new report for each;
   you choose what is frozen.
2. Freeze on the current inputs and state on the page that these two are not
   tested.

**Recommendation.** Option 1, with option 2's statement whichever is frozen.

**Blocks.** The freeze, by 31 October (`rounds/2026-10-23-out-of-sample/DATA-PLAN.md` §7).

**Your answer.** "test the two inputs."

**Recorded.** Option 1. The three arms (by-elections off; γ from 2019→2021; γ
from both fits pooled) are pre-registered under `prereg/` and run against the
current forecast with the same seed and draws, outside `data/`; each gets an
old-vs-new report in `reports/model-changes/`, and the frozen choice comes back
to you as a new item. Work in `TODO.md`. Run with the CPU left free for you
("please leave some cpu available").

### 30. Tooltips without the previous value: a corrections entry? — answered 2026-10-23

**Context.** Since the 22 October publication, a live figure's tooltip has said
only when its value started ("58% chance since 21 October") and not what it
was before ("Was 47% on 26 September"). The previous value showed only on the
day a figure moved. The 21 October build showed it; the 22 and 23 October
builds dropped it. Every figure on the page was correct; the history was
missing. A fix is being written (`audits/2026-10-23-site-sweep/BRIEF-tooltip-was.md`).

**Options.**
1. A corrections entry: what was missing, the dates, and that every tooltip now
   shows the previous value.
2. No entry: no published figure was wrong, and the corrections page lists
   wrong statements.

**Recommendation.** Option 1. Readers who looked on 22 or 23 October saw a
figure presented with no history, which is what the tooltip exists to prevent.

**Blocks.** Nothing; the fix ships either way. The entry, if wanted, goes in the
same release.

**Your answer.** "2. Just fix it. no corrections entry."

**Recorded.** No corrections entry. The fix is commit f51b54a on `site-sweep-1` (`publication.prior_values`; tests in `tests/test_tooltip_says.py` and `tests/test_published_page.py`).

### 29. Backtests that use later results: refit per election, then re-score? — answered 2026-10-23

**Context.** You allowed one exception to "only data from before the election":
the census, for each ward's population-group split. All 24 backtests (eight
metros at 2011, 2016 and 2021) also use settings chosen with results from the
election being tested, or later ones:

| Setting | Chosen on | Used in the test draws |
|---|---|---|
| Turnout correlation between groups | turnout changes 2011→2016 and 2016→2021, all eight metros | every test |
| Level shrink and its scale | Johannesburg 2016 and the eight metros at 2021 | every test |
| National-vs-local balance (spine k) | transitions up to 2016→2021; kept after a sweep scored on 16 backtests | every test |
| New-party chance and size | kept after a sweep scored on 9 backtests | 2011 tests only |
| Slate growth | changes up to 2016→2021 | none (real ballot lists used) |
| Dirichlet scale | sweep on 9 backtests | none (current draw method does not read it) |

Switches chosen by comparing backtest scores: polls off, the arrival-group draw
off, the draw method, ward noise and the level floor.

**Options.**
1. A pre-registered round: refit turnout correlation, level shrink and spine k
   for each test from earlier elections only, re-run all 24, and publish the new
   scores with the census as the stated exception and the switches listed.
2. Keep the settings; the scoring page names each one and the tests it touches.

**Recommendation.** Option 1, with option 2's wording on the page until it lands.

**Blocks.** The scoring page's claims about past accuracy.

**Your answer.** "For each election you can use all of those variations between previous elections- BUT YOU CANNOT INCLUDE THE ELECTION YOU ARE FORECASSTING. And teh data is patchy an inconsistent. Have all your changes planned. The submit the plan for review by a pollster skill agent before implementing anything." Then a data programme (complete national, provincial, local and by-election results for the 8 metros; every election pair local-local, national-local and local-national, at city and ward level: vote, turnout, population-group variation; per-party shrink, vote change and turnout change for every ward in every pair, saying exactly why where it cannot be done; how those changes themselves change; every by-election against the elections before and after it, and its correlation with the next; the backtest from data dated before each election only, the census and any exception the pollster finds accepted in the polling literature being the only exceptions). "DELETE ANY CONTAMINATED SCORES OR RESULTS. I WANT EXACTLY ZERIO chance they are being read and accepted blindly. START with Johannesburg data." On keeping the settings: "Seriously? It's embarrassingly bad. Go and ask Pollster agent if that is how forecasts are meant to work. i want the reply on record." On option 1: "You can do this as a stop gap. But it seems woefuly incomplete … Since it's what we cna do now, do it now. Make absolutely sure you do not ingest some earlier data thgat is contaminated."

**Recorded.** Option 1 now as a stop gap, then the full programme. Planned in `rounds/2026-10-23-out-of-sample/PLAN.md`, reviewed by a pollster agent before any implementation; the pollster's answer on keeping the settings is recorded there. TODO: the round.

### 27. Zille's 490,000 on both ballots: publish the test as a range? — answered 2026-10-23

**Context.** On 20 October Helen Zille said: "490 000 people need to vote DA
on both ballots. That would give us 136 of the council's 270 seats." (News24,
interviewed by Ann Bernstein of CDE). Brief 1 item E5 adds a dated note to
the claim card that tests it through the seat law, with every figure computed
by the build from the published simulations.

Run through the seat law, the figure depends on who wins the wards. The test
can only hold the wards fixed, so it gives two ends:

| Figure | Typical simulation's ward winners held (ANC wins 72 wards) | No party wins more wards than its vote entitles it to |
|---|---|---|
| DA seats from 490,000 on each ballot | 112 | 131 |
| DA votes needed on each ballot for 136 | 620,000 | 508,000 |

Common to both ends: This Model expects a median of 1,013,993 votes on each
ballot, so 490,000 is 48%. The DA reaches 490,000 on both ballots in 0 of
5,000 simulations. Your proportional check on 23 October (about 130 seats,
about 511,000 needed) is the second column. A DA on 48% would take some of
the ANC's wards; the test cannot say how many, and the card says so.

**Options.**
1. Publish the range as above.
2. Publish only the no-surplus end (131 seats, 508,000 needed), and say that
   the ANC's ward wins could lower it.
3. Publish only the two figures that need no ward assumption: 48% of the
   vote, and 0 of 5,000 simulations.

**Recommendation.** 1. Each end is a computed result under a stated
assumption, and the card names the limit.

**Status, 23 October.** Live since the brief 1 release (version 3b0fb7a7), as option 1, under your instruction to deploy if the review passed. Choosing 2 or 3 changes one note on the 490,000 card.

**Your answer.** "PUBLISH this: This Model expects a median of 1,013,993 votes on each ballot, so 490,000 is 48%. The DA reaches 490,000 on both ballots in 0 of 5,000 simulations. If the DA did in fact win 48% that would take some of the ANC's wards. (Can we not inflate turnout for teh DA population groups and see what wards they woudl in fact win in this scenario?)"

**Recorded.** Option 3 for the card's note (replaces the range now live). The turnout scenario is in `rounds/2026-10-23-out-of-sample/PLAN.md`. TODO: card note; scenario.

### 28. ActionSA's level: measure it instead of judging it? — answered 2026-10-23

**Context.** ActionSA's expected Johannesburg share is your judgement call
(JUDGEMENT-CALLS §SJ2), 17.6%. This Model already gives the national route
no weight for ActionSA. The parts that are judgement are retaining 0.72 of
its 2021 share and the blend with by-elections. The record holds two things
that could be measured instead:

* how much of its first local result a new party keeps at its second local
  election, across the eight metros;
* ActionSA's own by-election swings against its 2021 result in the same
  wards. This Model already reads these: four contests imply 18.9%, capped
  at 16.3%.

**Options.**
1. Commission the measurement as a pre-registered round. If it holds up,
   it replaces the judgement at the next forecast run.
2. Keep the judgement as it is.

**Recommendation.** 1. It would turn a hand-set number into a measured one.
It changes the forecast, so it goes through the normal round: pre-register,
measure against the record, report old against new.

**Blocks.** Nothing in brief 1.

**Your answer.** "DO THIS Commission the measurement as a pre-registered round." On new-party retention: "yes until 2021 not beyond." On the by-election cap: "how is the cap applied?" And: "turnout shrink is one thing, but if every party % shrinks where do the missing % of votes go?"

**Recorded.** A pre-registered round; second-election retention measured on pairs ending no later than 2021. Planned in `rounds/2026-10-23-out-of-sample/PLAN.md`. TODO: the round.


### 26. The site text sweep: how to fix what it found — answered 2026-10-23

**Context.** On 23 October seven read-only reviewers checked every reader-facing
page; the combined list is `audits/2026-10-23-site-sweep/FINDINGS.md`, with each
reviewer's report beside it. You found the first error: the review of 6 August
says overhang is "the council growing beyond 270". The council never grows;
This Model keeps it at 270 under Schedule 1 item 16. No other page says it
grows. The sweep found:

- about 20 statements wrong today on live pages, outside the dated pieces. The
  worst: the ward map on the home and forecast pages is from the 29 September
  run and disagrees with the headline beside it; Your prediction says its
  turnout control was checked against a full re-run, which the record says is
  untrue of the live model; the privacy page omits jsDelivr; the methodology
  page says Stats SA holds home language by ward;
- about 11 errors in the review and the 8 August articles, live since 8 August,
  including the review's council growth, and the minority-administrations claim
  that abstention installed the DA in 2021 (Phalatse won 144 to 121);
- errors in the claim cards dated 7 August to 7 October (the 190,000 figure, the
  red-lines label, the Soweto ward), and wording there that singles out one
  speaker ("Helen", "turnout fantasy");
- about 60 uses of "the model" for "This Model", "forecast" used for a reader's
  prediction, and a page named both "Your prediction" and "Your Forecast".

**Decisions.**
1. Order: (a) one brief now for every factual fix, the map redrawn, and a
   correction entry for each error that was live; then a second brief for the
   tone sweep, STYLE.md brought up to date, and a test that scans body text. Or
   (b) everything in one brief.
2. The claim cards are dated. Are they frozen like the articles (corrected only
   by a dated note or a correction entry), or live text fixed in place?
3. The page's name: "Your prediction" (menu and title now) or "Your Forecast".
4. The public GitHub repository is at 27 August (main) and 24 September
   (remediation). The emails say the code is public. Push the current
   remediation branch, after a scan for secrets?

**Recommendation.** 1 (a): the factual errors are live and the Stats SA and
university notes link these pages. 2 frozen, with correction entries, so the
rule is the same for every dated piece. 3 "Your prediction", which the page
already uses. 4 yes.

**Gates.** The first fix round (decision 1); the push (decision 4).

**Answered 2026-10-23:** "26. a brief to fix map and errors and post corrections (in the simple format agreed) taht shoud go up asap. another brief for tone sweep and automatic tests. 2. claim cards. you can add dated ammendements to them. They are dated claims and we are adding dated additions if teh paerty keeps claiming teh same thing adn we ae also giving dated evaluations. 3. Your Prediction if it's a single scenario. Forecast if it is a range of possibilities. 4. Yes fully update github with the latest everything. Scan for secrets and personal information, addresses, phone numbers etc." Then: "26 is highest priority."
**Recorded:** Brief 1 (map, factual errors, correction entries) and brief 2 (tone sweep, automatic tests) under `audits/2026-10-23-site-sweep/`; claim cards are corrected by dated amendments; naming rule to STYLE.md in brief 2; GitHub push after a secrets and personal-data scan.

### 22. New claims from other parties — answered 2026-10-23

**Context.** Your "We need to look for other comments": a search of news,
party sites, X and YouTube since August for testable claims about the
Johannesburg result by named figures of parties other than the DA, each
checked for exact wording at the source
(`audits/2026-10-22-site-round/CLAIM-CANDIDATES.md`).

1. **MK, Bongani Baloyi** (Daily Maverick, 6 October): voters "must not
   waste their vote on a party that will take 2% or 3%; they must be
   strategic". Testable: how many seats a party wins at 2 to 3% of the vote,
   and how often such parties decide who has a majority. Applies to every
   small party alike.
2. **MK, Baloyi** (same article): the ANC's losses are "a direct consequence
   or attributed to uMkhonto Wesizwe's growth". Testable only if the model's
   record of where votes move supports it; to be checked before a card.
3. **ANC, Dada Morero** (eNCA, 24 August): "Allow us to lead on our own, for
   the next five years". The same question as the ANC card already on the
   site: a dated second line on it, not a new card.
4. **IFP, Velenkosini Hlabisa** (News24, 7 October): "most of the
   municipalities are going to be led by a coalition of partners in the
   GNU". In Johannesburg the GNU parties include the ANC and the DA, so the
   answer is near certain and of little interest.
5. Not usable: MK's "can win Joburg outright" (reporter's paraphrase only;
   the newsdesk's draft card rests on it); the EFF's "50-plus-one" (a
   paraphrase); ActionSA and the PA made pledges, not claims about the
   result.

**Recommendation.** 1 as a new card; 3 as a line on the ANC card; 2 only if
the check supports it; not 4.

**Gates.** Nothing.

**Answered 2026-10-23:** "party claims: Recommendation. 1 as a new card; 3 as a line on the ANC card; 2 only if the check supports it; not 4. AGREE"
**Recorded:** TODO: Baloyi 2-3% card; Morero line on the ANC card; check Baloyi's MK-growth claim before any card.

### 20. Two Tshwane briefs — answered 2026-10-23

**Context.** For a Tshwane forecast and page, two pieces of new code, each
to be briefed first (your 16.3): (1) assigning the 2026 roll to Tshwane's
wards: the voting-district-to-ward assignment exists only for Johannesburg
and its path is fixed in the code; (2) the Tshwane headline page (ward map
and seats, its own address, e.g. tshwane.whysoserious.city), since every
page builder writes Johannesburg's site today. The by-election adjustment
for Tshwane is optional and moves its forecast, so it needs a
pre-registration first.

**Recommendation.** Yes to both briefs being written now, by-elections
included; each comes back to you before code.

**Gates.** The Tshwane forecast and page.

**Answered 2026-10-23:** "Recommendation. Yes to both briefs being written now, by-elections included; each comes back to you before code. AGREE - we also need a map of wards and other UI stuff."
**Recorded:** TODO: the two Tshwane briefs, the Tshwane page brief to include the ward map and the rest of the page UI; by-election pre-registration.

### 19. Running each city separately — answered 2026-10-23

**Context.** Your questions (16.2): why the cities are joined, and which
judgements are Johannesburg's. Answered in
`audits/2026-10-22-tshwane/JUDGEMENT-REVIEW.md`, and its two decisive facts
re-checked:

* **Tshwane's ten settings are the same values as Johannesburg's, and both
  are the model's general defaults**, which the backtest has scored on
  Tshwane 2011, 2016 and 2021. Only one block was ever Johannesburg's: a
  set of per-party ranges, removed from Tshwane in August, and inert
  without by-election data. So nothing needs changing for Tshwane, and my
  earlier claim that the copied values made a Tshwane forecast unpublishable
  was wrong; it was made without reading them.
* **What joins the cities is one fingerprint.** Every model input file
  records a hash of every city's settings file, byte for byte, so editing
  anything in `cities/tshwane.toml`, a comment included, marks Johannesburg's
  live inputs out of date. The reason it is there is real but narrow: the
  turnout band is measured across all the cities' past results, so it needs
  each city's code, layout and election dates, not the whole file.

Tshwane's forecast does not need `cities/tshwane.toml` edited (its roster
is in its own per-year file, which affects only Tshwane), so nothing is
blocked today.

**Options.** (a) Narrow the fingerprint now to the fields actually read, in
one re-emit window (about an hour including checks; Johannesburg's forecast
must come out identical, which is the test of the change, and the live site
is not republished). After it, a Tshwane edit never touches Johannesburg.
(b) Do it after 4 November.

**Recommendation.** (a), before more cities are added, with the check that
Johannesburg's numbers reproduce exactly.

**Gates.** Nothing for Tshwane's first forecast; any future edit to a
city's settings file.

**Answered 2026-10-23:** "Recommendation. (a), before more cities are added, with the check that Johannesburg's numbers reproduce exactly. AGREE"
**Recorded:** TODO: narrow the cities fingerprint in one re-emit window; Johannesburg must reproduce exactly.

### 25. Methodology page corrections — answered 2026-10-22

**What it is.** A check of the methodology page against the code found the
turnout paragraph true sentence by sentence but describing the wrong turnout,
and five other statements false or out of date.

- **Turnout (the paragraph you asked about).** Each district's turnout is projected
  from its 2024 national turnout and its fall from national to local in 2016 and 2021,
  with 2021 at 70% (`src/turnout.py`). Still true: the weight has never been tested,
  2016 fell less (in 712 of 766 districts), and equal weights would give higher turnout.
  - What it leaves out: the population groups on Your Forecast do not use that blend.
    Each group starts at its own 2021 turnout, with a range measured across the eight metros.
  - Also left out: the district projection was scored on 17 October and did no better than
    repeating the last local election.
  - Consequence: the 70% weight decides how a group's voters are spread across districts.
    It does not set the group's turnout.
- **"In 2021 every group's turnout was the lowest on record":** false. Each group has a
  lower turnout on record, back to 2000.
- **"Drawn from what turnout has done in that city before":** out of date. The range's
  width has been measured across the eight metros since an earlier round; only its centre
  is Johannesburg's.
- **By-elections, "Nobody knows the right weight, so the two count equally":** out of
  date. A test on 2021 (21 October) found equal weights gave the smallest error, by a
  small margin.
- **"Nothing is carried across from Johannesburg"** (the other-cities section): false.
  The turnout range and the turnout correlation are measured across the metros,
  Johannesburg included.
- **The validation block** is dated 30 September and names a code file, a data file
  and "a 400-draw run". The model has changed since.
- **Other page faults:**
  - One typed measurement, "337 times … eight metros", should be filled in by the build.
  - "before the draws" names a model internal.
  - The page says "the model", not "This Model".

**Options.** 1. Correct all of it in one change, with the headline (item 24),
under one brief, before the live release. 2. Release the current UAT version
first and correct the page next.

**Recommendation.** 1. The page states things that are false today.

**Gates.** The live release.

**Answered 2026-10-22:** "the page is live, so best we fix it immediately" (option 1).
**Recorded:** brief `audits/2026-10-22-headline-method/BRIEF.md`; commits 0bda701, 28aec63
(JUDGEMENT-CALLS §H2 and the by-election Plain fields, `docs-public/methodology.md`,
`src/build_validation.py`, stats token `small_party_record_cases`); UAT c18aeaa.
The turnout paragraph was rewritten from the code: each group starts at its 2021
turnout, its range is Johannesburg's own swing since 2000 (wider than the
eight-metro floor in all four groups), and the district pattern is half each
district's 2021 turnout and half the 70% projection.

### 24. The home-page headline's ward sentence — answered 2026-10-22

**What it is.** The UAT headline ends: "The ANC leads in 77 wards, but 32 of
them are close (won in under 90% of simulations); the DA leads in 45, 8 of
them close." You called it meaningless. The sentence came from your point that
the ANC's wards are far tighter than the DA's; the bracket explains "close" in
model terms, and "won in under 90% of simulations" is a second percentage
beside the two at the start of the headline.

**Options.**
1. Plain words, same point: "The ANC is ahead in 77 wards, but in 32 of them
   the lead is not safe. The DA is ahead in 45, and in only 8 is it not safe."
   "Not safe" carries a tooltip: "SOURCE: This Model. A ward where the leader
   wins in fewer than 90% of 5,000 simulations."
2. Drop the ward sentence. The headline ends at the two chances.
3. Replace it with seats: how many of the council's seats each of the two
   typically wins, and how many are needed to govern alone.

**Recommendation.** 1. It keeps your point and removes the model's terms.

**Gates.** The live release of UAT 88005769 (the headline is in it).

**Answered 2026-10-22:** "headline: A coalition is all but inevitable. The largest
party is leaning toward the ANC. sub-line: While the ANC is ahead in 77 wards, in
32 of them the lead is not safe. The DA's is ahead in 45 wards with only 8 that
are not safe." ("The DA's" written "The DA".)
**Recorded:** same brief and commit 0bda701 (`content/joburg/home.toml`,
`src/render_home.py`, the "not safe" tooltip in `src/tooltip_says.py`). The two
chances leave the headline; `home.p_anc_largest` and `home.p_da_largest` are retired
at the live publish.

### 18. The marketing decisions — answered 2026-10-22

**Context.** Item 17 settled that new drafts are needed (nothing was sent).
The rest of `~/projects/atlas-jhb-model-newsdesk/marketing/PLAN-2026-10-21.md`
§9 is still open, with its context there:

1. Budget — answered 2026-10-22: "We have a 3,000 budget and it will be
   entirely spent on Twitter/X" (taken as R3,000; say if not). Open: Workers
   Paid ($5 USD a month) if daily requests pass 50,000.
2. Channels to keep or drop: Reddit and forums, LinkedIn, Facebook and
   Instagram, radio.
3. Whether you front it in person (radio, a photo, named posts) or the site
   speaks as whysoserious.city.
4. An email short link (`/e`) and short links that land on Your Forecast.
5. What "every party" means for the party note: every party on the certified
   Johannesburg ballot, or every party with a seat range on the site.
6. The claims balance: with the Zille card, six claims from four parties (DA
   3). Leave it, say on the page how claims are chosen, or invite every party
   to submit one by a date.
7. Empty the live entries table of test predictions before the first post
   (your yes; a live change).
8. Store `CF_ANALYTICS_TOKEN` and `CF_ACCOUNT_ID` in the Keychain so the
   daily counts start (the free plan keeps logs 3 days).
9. The billboard: the slot's dates and format (size, seconds, still or
   moving), and which of the ideas in chat to make.

**Recommendation.** 5: every party on the certified ballot. 6: say on the
page how claims are chosen. 7 and 8 today.

**Gates.** The first post.

**Your answers (2026-10-22), verbatim where quoted:**
1. Budget: "We have a 3,000 budget and it will be entirely spent on Twitter/X".
2. Channels: "Keep instagram - and if reddit has SA politics subreddits of any value. Radio woudl be nice. LinkedIn I don't see the tie-in? Facebook doesn't seem to fit either. Youtube is worth looking at though" (eNCA, SABC News, party channels, @_SMWX).
3. "Speak as whysoserious.city and I am representing it. But it should not be \"mine\"".
4. Email short link and short links to Your Forecast: "yes".
5. "on the ballot".
6. "Levae the DA's latest. It's not very interesting. We can update teh first one if she's made the same claim. We need to look for other comments." And: say on the page how claims are chosen.
7 and 8: "today".
9. Billboard (the operator's email, RE: Free DOOH Billboard): 4 to 8 weeks, subject to availability; a 15 s MP4 in a 180 s loop; 768x480, H.264 High, 30 fps CFR, 8-bit, Rec.709, 4:2:0, gamma 2.2 ("Looks good"); avoid static, avoid white backgrounds, avoid colour on similar colour.

Recorded: the Zille 40% card is withdrawn from the 22 October round (its dated line on the 490,000 card stays); a line on how claims are chosen goes on the claims page; a search for other parties' testable claims is running; /e and Your Forecast short links are briefed; the entries table is backed up and the delete command given to you (deleting is yours to run); the analytics token is yours to create and store; the billboard spot is being made, with a version for after 4 November since the slot outlasts the election.


### 17. Marketing plan — answered 2026-10-22

**Context.** The plan is
`~/projects/atlas-jhb-model-newsdesk/marketing/PLAN-2026-10-21.md`: 14 days to
4 November, free channels first, the prediction game as the main hook, a
day-by-day calendar, and measurement from the site's own arrival counts. It
waits on nine decisions in its §9: budget; which channels; whether you front
it in person; whether the 14 October Mail and X drafts were sent; an email
short link; what "every party" means for the party note; the claims balance;
confirming the live entries table was emptied of test predictions; the
billboard slot.

**Recommendation.** Read §9 and answer there or here. Two are urgent: empty
the entries table before the first post, and store the Cloudflare analytics
token so the daily counts start (the free plan keeps logs for 3 days).

**Gates.** The first post (planned 22 October).

**Your answer (2026-10-22):** "Nothing has been sent as it all changed. So we need new drafts X posts and emails. We also need to send emails to the people and aprties we identified - as wlel as use their twitter handles if we know them. Need billboard creative ASAP - ideas. It's on a busy road." Recorded: the 14 October drafts were not sent; new Mail drafts and X posts are prepared for your send and your per-post yes; the other §9 decisions (budget, channels, fronting it, short email link, every party, claims balance, entries table, billboard slot) remain open in the plan.

### 16. Tshwane: three decisions before a forecast — answered 2026-10-22

**Context.** Tshwane's inputs, checked read-only today: the 2026 ward map,
past results, census and national baselines are on disk. The IEC ward roll was
read from its page on 21 October (snapshot of 29 September: 107 wards,
1,684,463 registered; `archive/iec-registration-2026-09-29/`). Missing: the certified party roster and party lists (in the IEC's certified
Gauteng candidates PDF of 16 September, on disk; a first parse finds 79
parties, 70 with a party list), by-election adjustments (never built for
Tshwane), and a page builder (none exists; new code). Three things need you:

1. **The roster.** Marking Tshwane's roster complete deletes every party not
   on it. Johannesburg's yes was for its list only. Yes for Tshwane's
   certified list, once parsed and checked?
2. **Tshwane's judgement values.** `cities/tshwane.toml` carries values copied
   from Johannesburg and says nothing may be published until they are
   reviewed. Editing that file re-keys every city's pool specs, Johannesburg's
   live one included, so it needs a full re-emit window, and Johannesburg's
   forecast would be rebuilt with it (its numbers should not move; the
   re-emit checks that). Review now and accept the window, or publish Tshwane
   first with the copied values stated as copied?
3. **Two briefs to approve when written:** the voting-district-to-ward
   assignment for Tshwane (a code change so the assignment is per city) and
   the Tshwane headline page (ward map and seats, its own address).

**Recommendation.** 1 yes. 2: review now and take the window, because a
published forecast built on another city's judgement values would claim
calibration it does not have. 3: approve when written.

**Gates.** The Tshwane forecast.

**Your answer (2026-10-22):** 16.1: "If the roster is official and you are sure it's the one, go ahead and use it as the basis for the vote." 16.2: "We need to be able to run cities completely seperately. Why would we spend all teh time emitting something that does not change? What judgements are there and which are joburg specific? Unless there is a reason to change them becasue they are joburg specific - leave them alone becasue the idea is to have a model that can be eaily put onto other cities. I would be surprised if JHB judgements where all spoecially for joburg so do 1 yes and review 2 with my comment above taken into account. why are the cities joined at all and have you actually reviewed teh judgements before you make declaratiions of incompatibuility?" Recorded: roster used if verified as the IEC's certified list; the judgement review and the cities coupling go in audits/2026-10-22-tshwane/ (the earlier claim that the copied values make the forecast unpublishable had not been checked against the values; that review is now done there). 16.3 not answered; briefs come to you when written.

### 15. News for the site — answered 2026-10-22

**Context.** The newsdesk digests since 12 October were checked at their
sources (the routine cannot reach news sites; this check read them directly,
News24 through your subscription). Polls are not in the forecast; a poll
appears on the site only as reporting.

1. **Helen Zille's coalition arithmetic** (News24, 9 October, from her talk
   with the Centre for Development and Enterprise on 8 October): "if we get
   40%, although we will be the biggest party by a long shot, we won't be big
   enough to get into government", because the ANC, MK, the EFF, ActionSA
   and the PA together "might get over 50% before we can". A tested claim:
   when the DA is near 40%, how often does a bloc of those five parties reach
   136 of 270 seats? Needs a model query; no verdict yet. It would be the
   third DA claim of six (now DA 2, ANC 1, MK 1, ActionSA 1).
2. **Two polls not yet on the site**, both verified at source:
   eNCA/MarkData (DA 35.0, ANC 21.8, MK 12.5, EFF 11.9, ActionSA 10.3, PA 3.7
   of vote intention; 1,011 Johannesburg registered voters intending to vote;
   fieldwork 10 August to 14 September per eNCA's methodology page, though
   two other dates are also published; margin ±3.08 points) and
   News24/SABI (DA 29, ANC 23, MK 12, EFF 11, ActionSA 7 of registered
   voters; 1,000 voters; 25 August to 17 September; margin 3.3 points). They
   would go on Your Forecast's poll control as reporting, each with its
   caveat line.
3. **A dated "Since then" line on the 490,000 claim card:** Zille repeated
   the claim on 8 October ("136 seats out of 270").
4. **Not usable:** the digest's "new" ActionSA poll (ActionSA 31.7%) is the
   2021 poll, published 30 September 2021, already on file; MK's "can win
   Joburg outright" is reported only in paraphrase; the DA's Electoral Court
   case is reserved with no date; no new Johannesburg by-election.

**Recommendation.** 1, 2 and 3, in one site round with a brief. On 1, decide
with item 17's claims-balance question, since it adds a third DA claim.

**Gates.** Nothing in the forecast.

**Your answer (2026-10-22):** "do 1,2 and 3". Recorded: the Zille claim card, the two polls on Your Forecast, the dated line on the 490,000 card; same site round brief.

### 14. Which parties get their own seat row on Our Forecast and the home page — answered 2026-10-22

**Context.** The two forecast pages pick their rows by different rules, and on
the 21 October forecast they disagree. Your Forecast gives a party its own row
when its median is at least 2 seats (your rule, 2 October:
`interactive/pyboot/page.py` `MIN_SHOWN_SEATS`). Our Forecast and the home
page's seat table use a fixed list of nine named parties
(`scenarios.NAMED_PARTIES`: DA, ANC, EFF, ActionSA, MK, PA, IFP, Rise Mzansi,
Al Jama-ah). BOSA and Freedom Front Plus now have a median of 2 seats each
(5,000 simulations), so Your Forecast shows them and Our Forecast puts them in
"Others". The untouched Your Forecast page is meant to be the published
forecast exactly; `test_the_page_engine_at_uniform_weights_is_the_forecast_pages_rows`
is red on this.

**Options.** (a) Our Forecast and the home page use the same rule as Your
Forecast: every party at a median of 2 seats or more gets a row, the rest are
"Others". BOSA and Freedom Front Plus gain rows; the named list goes. (b) Your
Forecast uses the named list. (c) Leave them different.

**Recommendation.** (a). One rule for every party, and a party enters or
leaves the table by its own figure, not by a list someone typed.

**Gates.** A change to two live pages: a brief, then UAT, then live with your
yes. One test stays red until then.

**Your answer (2026-10-22):** "Standardise them I do not care which - when listing 'other parties' do so alphabeticaly." Recorded: one rule on both pages (a party with a median of 2 seats or more gets a row), and wherever other parties are listed, alphabetically. Brief: audits/2026-10-22-site-round/BRIEF.md.

### 6. The splinter split — answered 2026-10-21

**Your answer (2026-10-21):** go live with 35% as it is, and measure it after
going live. "It seems incorrect as it stands in a country so divided by
population group."

Recorded as a task in TODO.md: re-measure `SPLINTER_PARENT_WEIGHT` after go-live
(JUDGEMENT-CALLS §F6), with the population-group question in the brief.

### 13. The share badge's bands on the new forecast — answered 2026-10-21

**Context.** When a reader shares a prediction, the site rates how close it is
to our prediction with a badge: Safe bet, Steady as she goes, Long shot, Wild
call, Hail Mary (`reweight.closeness_badge`, your ten-point bands). The share
brief fixed seven test predictions and the badge each should get, and
`tests/test_reweight.py` checks them on the published simulations. On the 21
October forecast, three of them get a harsher badge than the brief expects:

| test prediction | brief expects | 16 October forecast | 21 October forecast |
|---|---|---|---|
| our prediction | Safe bet | 1.000, Safe bet | 1.000, Safe bet |
| mild: largest party −8 seats, second +8 | Safe bet | 0.918, Safe bet | 0.871, Steady as she goes |
| moderate: largest −15, next three +5 each, IFP +2 | Steady as she goes | 0.846, Steady | 0.745, Long shot |
| your screenshot prediction | Steady as she goes | 0.820, Steady | 0.755, Long shot |
| wild: largest −25, fourth +25, three small +3 | Long shot | 0.780, Long shot | 0.736, Long shot |
| fixture A (a fixed prediction) | Safe bet | 0.991, Safe bet | 0.725, Long shot |
| fixture B (a fixed prediction) | Wild call | 0.685, Wild call | 0.637, Wild call |

Fixture A and your screenshot are fixed seat counts written against an earlier
forecast (ActionSA 33 seats in the screenshot; the forecast now has 40), so
part of their fall is distance from a moved prediction. The mild and moderate
predictions are moves relative to our prediction, and they fall too. Why the
same-sized move now scores lower is not yet measured.

**Options.** (a) Go live with the bands as they are; re-record the test table
on the new forecast and measure why relative moves score lower, after go-live.
(b) Hold go-live and re-set the bands so the brief's examples keep their
badges.

**Recommendation.** (a). The badge is a rating of readers' predictions, not a
forecast figure, and nothing is published from it until readers share.

**Gates.** Nothing in the forecast. One test stays red until it is answered.

**Your answer (2026-10-21):** "go live", given with this item open and
recommendation (a) standing; taken as (a). Re-recording the test table and
measuring why relative moves score lower are in TODO.md.

### 7. The go-live yes — answered 2026-10-21

**Context.** Items 2, 3, 5, 6 and 9 are answered. Item 1 is answered (ActionSA at 17.6%). After the rebuild, with your yes:

- regenerate the frozen forecast and the site's simulation files;
- rebuild the test site from today's model (the one there now, UAT version
  d22294e0, carries the 16 October model);
- redeploy the seat-picture worker (`joburg-seats`) if its code changed, in
  the order `docs/DEPLOY-UAT.md` sets (site first, then the seat worker).

Your instruction: skip anything that need not run. Promoting the test site to
live stays yours.

**Your answer (2026-10-21):** "go live when ready". Live promotion follows the
test site passing its checks (`docs/DEPLOY-UAT.md`).

### 11. Sign-in, and the three Cloudflare items listed for it — answered 2026-10-21

**Context.** These belong to the sign-in feature: readers signing in (Apple,
Facebook, X, Microsoft) so their predictions are saved and can go on a
leaderboard. It is built (`worker-api/`) but not switched on, and it has its
own security and privacy review gate (R5 in TODO.md §0). The three items:

- **Data location.** Where Cloudflare keeps the sign-in database (a "location
  hint" when it is created: Europe, Africa, and so on). It holds personal data
  (email addresses, and political predictions), so where it is stored matters
  under POPIA.
- **Provider app registrations.** Each sign-in button needs an app registered
  with that company under your account (Apple developer account, Facebook
  developer app, X developer app, Microsoft Entra). `worker-api/README.md` has
  the exact settings for each. Only you can create them.
- **Workers Paid.** Cloudflare's $5 a month plan. The free plan allows 100,000
  worker requests a day and very little processing time per request. Pages
  themselves are free and unlimited, but sealing a shared link and drawing its
  seat picture each count as worker requests, and results night could pass
  the limit. Above it, those requests fail. I have not checked which plan the
  account is on.

**Answer (owner, 2026-10-21):** sign-in is later; the data location and the
provider registrations wait for it.

**Your answer (2026-10-21), sign-in:** hold it for later, and design it
differently: readers sign in with X or another account, but the site keeps no
credentials; their contact details are sealed inside their entry and cannot be
read by the site's operators except in named circumstances where a key is
received. "make it a system of never needing someone's details with very
specific exceptions." Recorded in TODO.md as the brief for the sign-in redesign.

**Your answer (2026-10-21), Workers Paid:** "we will deal with if we see
traffic. Currently absolutely no guarantee of any." The account stays on the
free plan; `docs/DEPLOY-UAT.md` is updated to say so.

### 10. Letting readers make the judgement calls — answered 2026-10-21

**Context.** You asked (2026-10-21) whether readers could make calls like
these on the site: "part of judgement calls we make and they can make." It is
possible. The interactive already re-seats a council from a reader's own
picks. A judgement-call control would let a reader change a party's starting
level (for example, how much of its 2021 vote it keeps) and see the forecast
redrawn. Two constraints apply: the same control has to be offered for every
party (your rule, no party singled out), and the redraw has to happen from the
published simulations in the browser, because the full model does not run
there.

**Options.** (a) Build it after go-live, as a new site feature with a brief
first (the usual process). (b) Build it before go-live, which delays go-live
by the brief, the build and the test site round.

**Recommendation.** (a).

**Your answer (2026-10-21):** "(a) Build it after go-live, as a new site
feature with a brief first (the usual process)." Recorded in TODO.md (after
go-live).


### 1. Your party calls — answered 2026-10-21

**Context.** The party sheet (https://claude.ai/artifact/MvLaG1WzrzwVmq7driyMAb)
lists every party on Johannesburg's 2026 ballot with the model's expected share
and range. A party call is your judgement that the model has a party wrong
(too high, too low, too narrow). None is entered yet. Each call you make goes
into `judgements/joburg-2026.toml` with your reason, is listed in
JUDGEMENT-CALLS.md, and the forecast is run and reported both with and without
your calls.

**Your question (2026-10-21): how does ActionSA go from 18.1% to 12.5% if it is
sized on 2021?** The steps, from the model's trace of today's Johannesburg
2026 run (5,000 simulations, list vote):

| step | ActionSA | what happens |
|---|---|---|
| 2021 list vote | 18.1% | the starting record |
| carried to 2026 | 13.1% | multiplied by 0.72: how much of its share a party keeps from one local election to the next. ActionSA has stood in only one local election, so it takes the record's typical value for a party of its size (from 292 past party-metro cases) |
| by-elections | 14.7% | four contests imply 18.9%, capped at 16.3%, blended at ½ |
| level shrink | 14.5% | |
| the parties' shares made to add to 100% | 12.6% | every party's level is set on its own, and together they add to 114.6%, so each is divided by 1.146 |
| simulations | 12.7% average, 90% range 8.4%–17.9% | |

The step that does most of the work is the 0.72: 18.1% × 0.72 = 13.1%. It is
the record's typical value, applied because ActionSA has no
second local election of its own. Its share of Johannesburg's 2024 national
ballot, 6.22% (5.4% after the model's conversion to a local level), is not
used: the model reads ActionSA's 2026 level from its local
record only. A party call would be the place to say ActionSA keeps more (or
less) of its 2021 vote than the average party.

**Your answer (2026-10-21):** "no calls" depends on the scaling test; the only
change you would make is ActionSA "to hold their current percentage". The
scaling test kept today's rule, so the model's ActionSA stays at 12.6%.

**One question before I enter it: which percentage?**
- **18.1%**, its 2021 Johannesburg list vote (above the model's 90% range of
  8.4–17.9%), or
- **12.6%**, today's forecast, held so the rebuild cannot move it.

The evidence either way: 2021 list vote 18.1%; share of Johannesburg's
2024 national ballot 6.22%; four by-elections since 2021 imply 18.9% (capped at
16.3% by the model). A call is entered as ActionSA's own centre in
`judgements/joburg-2026.toml` with your reason, listed in JUDGEMENT-CALLS,
and the forecast is reported with and without it.

**Gates.** The final rebuild of the forecast inputs.

**Your answer (2026-10-21):** "Put action SA at 17.6%".

**Entered** as ActionSA's own centre, 17.6% of the list vote, with the
model's usual width at that size (`judgements/joburg-2026.toml`,
JUDGEMENT-CALLS §SJ2). Every other party is scaled down so the shares add to
100%. Johannesburg 2026, 5,000 simulations: list vote and seats, simulation
average, with ActionSA's 90% range in brackets. MODEL-LOG §1.330 has every
party's range:

| | list vote without the call | with it | seats without | with |
|---|---|---|---|---|
| ActionSA | 12.7% (8.4–17.9) | 17.6% (13.3–22.3) | 29.3 (20–41) | 40.5 (31–51) |
| DA | 26.7% | 25.2% | 71.0 | 66.7 |
| ANC | 22.5% | 21.2% | 70.0 | 69.2 |
| EFF | 10.1% | 9.6% | 27.7 | 26.0 |
| MK | 9.1% | 8.5% | 23.4 | 22.0 |


### 12. The two steps after the levels: the size pull and making shares add to 100% — answered 2026-10-21

**Your questions (2026-10-21):** what is the "small adjustment", and should
every party be scaled equally to fit 100%?

**Today's Johannesburg 2026 run, list vote (%):**

| party | level | after the size pull | after scaling to 100% |
|---|---|---|---|
| DA | 32.60 | 30.48 | 26.62 |
| ANC | 27.33 | 25.79 | 22.53 |
| ActionSA | 14.70 | 14.48 | 12.64 |
| EFF | 11.47 | 11.54 | 10.08 |
| MK | 10.26 | 10.42 | 9.11 |
| PA | 6.97 | 7.36 | 6.43 |

**The size pull (`level_shrink`, JUDGEMENT-CALLS §A23).** Each party is cut by
an amount that grows with its size: a party keeps `1 − 0.35 × s / (s + 0.04)`
of its level `s`. A party at 15% keeps 72.5%, one at 1% keeps 93%. The vote
cut is then handed back to every party in proportion to its share, so the
total does not change. Net: the largest parties lose, the middle gains a
little. It exists because forecasts of past elections gave the top three
parties too much and the next nine too little by about the same amount
(summed over nine city-years: +32.3 points against −36.2). The 0.35 was fitted
on Johannesburg 2016 alone (0.375) and leaving out each city-year in turn
picks 0.35 every time. Adopted 2026-08-17 (MODEL-LOG §1.44): seat error over
nine city-years 312 → 264. Known cost: the handed-back vote over-feeds the
smallest parties.

**Scaling to 100%.** Each party's level is estimated on its own, and nothing
makes the levels add up. Every party is then divided by the same number, so
each loses the same fraction of its own share (12.7% here), which in points
falls most on the largest parties (DA −3.9, PA −0.9).

Measured, from the traces of the 2021 backtest: the levels added to between
100.0% (Buffalo City) and 112.4% (Cape Town) across the eight metros, and
111.9% in Johannesburg. Johannesburg 2026's 114.6% is above all eight
2021 metros; on the 24-city-year panel Cape Town 2016 reached 117.6%. The
backtest scores include this rule, so it is tested in that sense, but it has
never been compared with another rule.

**The alternative worth testing.** Take the excess from each party in
proportion to how uncertain its level is, rather than in proportion to its
size. A party whose level rests on a typical value rather than its own record
(ActionSA's 0.72, a first-time party) would absorb more than one with a long
record. Dividing the excess equally in points is not a candidate: it would push
small parties below zero.

**Answer (owner, 2026-10-21):** test it now, with the note "no point
adhering to a level when one has a history of the level decreasing".

**Result (MODEL-LOG §1.328).** Tested on all 24 past city-years (eight metros,
2011, 2016, 2021):

| rule | summed list-vote error (points) |
|---|---|
| proportional (as now) | 77.19 |
| by uncertainty | 99.51 |
| a third form (`c σ²`) | 104.29 |

Both alternatives are worse in total and in 2016 and 2021; a few 2011
city-years and Mangaung 2021 improve. The least certain levels belong to
parties standing for the first time. In 2016 and 2021 the model already
under-forecasts them (signed list-vote error, summed: 2016 −20.5 points, 2021
−32.5), so taking the excess from them makes that worse (−39.1 and −49.8).
ActionSA in Johannesburg 2021 would have been forecast at 0.7% of the list
vote; it won 18.1%. Proportional scaling stays. Your point about a party
whose record is falling is not tested by this: the model's uncertainty is set
by size and newness, not by trend.

### 9. Separate by-election weights for small and large parties — answered 2026-10-21

**Your answer (2026-10-21):** one weight, ½, for every party, provisional on
one measured cycle.

**New evidence since you answered: the checker found my size classes were
not the model's.** The model puts a party with no list vote at the previous local election in the
class of its share at the national election before the target (for this 2021
test, the 2019 national vote: Cape Town GOOD, Mangaung PA); my analysis put
every such party under 1%, and it also counted parties the by-elections never
reached. Re-done with the model's
classes, counting only parties the by-elections reach:

| class | best-fitting weight | range, leaving one metro out | party-metros |
|---|---|---|---|
| under 1% of the previous vote | 0.91 | 0.81 to 1.80 | 6 (ACDP in three metros, VF Plus, ATM, Justice and Employment) |
| 1% and over | 0.32 | 0.16 to 0.57 | 22 |

The two ranges do not overlap, and the rule written before the run said
separate weights are recommended when they do not. Run through the full
model (summed list-vote error over the eight metros, 2021; the weights were
fitted on the same metros, so this is in-sample):

| weights | summed list-vote error (points) |
|---|---|
| ½ for every party | 21.78 |
| 0.91 under 1%, 0.32 over | 21.42 |
| ½ under 1%, 0.32 over | 22.01 |

The last row shows that giving the larger parties ⅓ on its own scores worse
than ½. All of the split's gain comes from letting the six small-party cases
move almost the whole way to their by-election level.

**My recommendation is unchanged: ½ for every party.** The small-party class
rests on six cases, one of them a party (ACDP) counted three times, and the
gain is in-sample. The measurement and the rule disagree here, so it is your
call. Your answer above stands unless you change it.

**Answer after the new evidence (owner, 2026-10-21):** keep ½.

### 2. Two MK confirmations — answered 2026-10-21

**Question.** MK stood in the 2024 national election but never in a
Johannesburg local election. On 15 October you chose option A: place MK from
its own 2024 national results. (2a) Does that fitted placement win over your
earlier "about 90% ANC" note (JUDGEMENT-CALLS §SJ1)? (2b) Does a party count as
identified if the fit finds it in at least one voter group?

**Answer (owner).** 2a: the placement wins for MK. 2b: "Yes. I confirm that as
a test." Recorded in JUDGEMENT-CALLS §SJ1 at the final rebuild.

### 3. The by-election cap — answered 2026-10-21

**Question.** A party's by-election level is held inside its usual range
before it is blended in. Keep the cap, or let by-elections move every party by
the full weight?

**Answer (owner).** Keep the cap. Evidence (MODEL-LOG §1.326): removing it is
better in 3 of the 6 metros where by-elections reach a party and worse in the
other 3; the rule written before the run needed 4 of 6. The cap moves levels
both ways (it raised the ANC and DA in Cape Town as well as lowering others).
My statement that the uncapped fit is "worse overall" depended on the measure:
on the measure the pre-registration named, it is slightly better overall
(200 against 202 points²) and wins 2 of 6 metros. Corrected in MODEL-LOG
§1.327.

### 5. Polls — answered 2026-10-21

**Answer (owner).** Go live without polls in the forecast. Polls stay on the
interactive, for readers to use.

### 8. The two site settings — found done, 2026-10-21

`SEAL_KEY` is already set on the site worker (checked 2026-10-21: the secret
exists; its value was not read). The seat-picture worker `joburg-seats` was
last deployed 2026-10-14. Nothing is needed from you. If its code changes
before go-live, I redeploy it as part of item 7.

### 4. The by-election weight before go-live — answered 2026-10-20

**Question as asked.** Go live at ½ and test afterwards (a), or let the 2021
test change the weight before go-live (b).

**Answer (owner, 2026-10-20).** (b), and more: "the results should tell us and
make this a measured variable."

**Result (MODEL-LOG §1.326, 2026-10-21).** Measured over twelve weights from
0 to 1 against the 2021 result in the eight metros. Summed list-vote error
(points, eight metros): 0 → 23.90, ⅓ → 22.24, 0.4 → 21.94, **½ → 21.78**,
0.6 → 21.91, 1 → 24.68. Leaving each metro out in turn, the other seven pick
0.4 to 0.6. A second measure (least-squares fit, which weights the big misses
more) gives 0.33, with a range of 0.17 to 0.59 that contains ½. The gain comes
from the by-election swing; pulling the forecast back toward the last result
alone gains nothing. The measured weight equals the shipped one, so the model
does not change.
