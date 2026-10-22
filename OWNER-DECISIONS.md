# Decisions waiting on the owner

The one place where every open question for the owner lives. Each item carries
its full context, so it can be answered without the chat transcript. A chat
message that needs a decision links here and names the item by its heading.
When an item is answered, it moves to `OWNER-DECISIONS-ANSWERED.md` with the
date and the answer, and the record it changed (JUDGEMENT-CALLS, MODEL-LOG)
is named.

Last updated: 2026-10-21.

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

### 24. The home-page headline's ward sentence (22 October)

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
