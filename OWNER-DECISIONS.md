# Decisions waiting on the owner

The one place where every open question for the owner lives. Each item carries
its full context, so it can be answered without the chat transcript. A chat
message that needs a decision links here and names the item by its heading.
When an item is answered, it moves to `OWNER-DECISIONS-ANSWERED.md` with the
date and the answer, and the record it changed (JUDGEMENT-CALLS, MODEL-LOG)
is named.

Last updated: 2026-10-23.

---

## Open

Answered items: `OWNER-DECISIONS-ANSWERED.md`.

### 19. Running each city separately

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

### 20. Two Tshwane briefs

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

### 21. Outreach: the drafts, the X posts and the X ads

**Context.** New outreach, all in
`~/projects/atlas-jhb-model-newsdesk/marketing/outreach-2026-10-22/`. Nothing
is sent or posted.

* **Email:** 47 drafts are in Mail (Drafts, from psi@whysoserious.city,
  signed "Simon Davis, whysoserious.city"): 19 parties, 12 outlets, 9
  journalists, 1 analyst, 4 university departments, 2 civic bodies. Six are
  held because their address could not be confirmed (Wits Political
  Studies, Africa Check, SANEF, Code for Africa, Carol Paton, Kgothatso
  Madisa); `drafts-made-2026-10-22.md` lists them. The 38 drafts of 14
  October are still in Drafts (subjects ending "tested claims for your
  supporters" or "tested party claims, free to cite"); they are out of date,
  delete them. The party note is word for word the same for every party.
  Parties without an email: ActionSA and ATM have only a contact form; five
  sites were unreachable (EFF, Organic Humanity, Africa Restoration
  Alliance, APC, COPE); 55 others had no address found or were not
  searched (`emails.md`, with each party's ward count).
* **X posts:** 16 dated slots, 22 October to after polls close, no forecast
  figures, no party named, nothing between 07:00 and the close of polls on
  4 November (`x-posts.md`). Each needs your yes to the exact text.
* **X ads (R3,000):** X allows political-content ads in South Africa; an ad
  that argues for no party and asks for no vote needs no certification.
  Plan: website-traffic objective, Johannesburg, adults, no interest
  targeting, promoting only posts that name no party, landing on /x; R150 a
  day 22-25 October, R250 a day 26-31 October, R300 a day 1-3 November.
  X publishes no reach or cost range for South Africa. Sources in `x-ads.md`.

**Decisions.**
1. Party tags on X: (a) none, the public party note only; or (b) one
   identical reply per party with a known handle (parties without a handle
   get none).
2. Submit X's political-ads pre-approval form anyway, as insurance (X says
   1-3 business days)? And confirm @whyseriouscity is Premium or a Verified
   Organization (required to advertise).
3. Ads on their own short link (a site change, item 18.4) or sharing /x.
4. Add "send one claim for us to test" to every party email, or to none
   (item 18.6).

**Recommendation.** 1 (a); 2 yes; 3 own link; 4 to every party.

**Gates.** The first send and the first post.

### 22. New claims from other parties

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

### 23. The billboard's schedule and delivery

**Context.** Relativ Media's spec sheet for Monte Casino Digital (REL351):
an 8 m x 4.5 m screen, 768 x 480 pixels (the pixels are shown about 11%
wider than tall, which the spot is being drawn to compensate for), a 15 s
spot in a 180 s loop of 12, about 20 plays an hour, 24 hours a day.
Artwork is due 5 days before it goes live, by 14:00 Monday to Thursday or
12:00 on Friday, as an attachment or WeTransfer to digital@relativgroup.co.za,
the subject naming the brand and creative, the file named "Client Name
YYYY MM DD Campaign Name Site Name". A custom schedule (exact dates and
times) can be asked for.

So: delivered today (Thursday 22 October) by 14:00, it can go live on
Tuesday 27 October, 8 days before the vote; delivered by Friday 12:00, on
Wednesday 28 October.

**Decisions.**
1. Ask for a custom schedule with two creatives: the "seal your prediction"
   spot until 06:59 on 4 November (sealing closes at 07:00), and the
   "Joburg has voted" spot after that? Its first line is untrue until the
   polls close, so the second spot would start at 21:00 on 4 November (or 5
   November 00:00), with nothing of ours in between.
2. You send the email with the files attached (I prepare it as a draft in
   Mail once the spots pass their checks).

**Recommendation.** 1 yes, the second spot from 21:00 on 4 November and
nothing between 07:00 and 21:00; 2 today before 14:00.

**Gates.** The go-live date.

### 26. The site text sweep: how to fix what it found

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
