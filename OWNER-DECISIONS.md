# Decisions waiting on the owner

The one place where every open question for the owner lives. Each item carries
its full context, so it can be answered without the chat transcript. A chat
message that needs a decision links here and names the item by its heading.
When an item is answered, it moves to `OWNER-DECISIONS-ANSWERED.md` with the
date and the answer, and the record it changed (JUDGEMENT-CALLS, MODEL-LOG)
is named.

Last updated: 2026-10-25.

---

## Open

Answered items: `OWNER-DECISIONS-ANSWERED.md`.

### 40. Where each party's votes come from: the chart shows a fit sitting on its limits

**Context.** /your-forecast's chart "Where each party's votes come from" gives the ANC "over 99%" Black African and the EFF, IFP and MK 100%. You said this is impossible. Measured (MODEL-LOG §1.338): the chart prints the model's pool fit as it is, and the fit has put most parties on a corner of what the 2021 ward results allow. The ward arithmetic alone allows the ANC 0% to 71% of Indian/Asian voters and 0% to 26% of white voters; the fit chose 0% for both. The EFF, IFP and Al Jama-ah sit at the limit where every one of their votes comes from one group. The model's own record already marks the ANC's Indian/Asian and white figures as not pinned down by the data; the chart does not say so.

These figures are not only on the chart. They drive the population-group turnout controls on the same page and the forecast's turnout adjustment, so changing them moves forecast numbers.

**Options.**
1. Keep the fit; on the chart, mark the figures the data does not pin down (hatched, with a note). Needs your words for the note.
2. Re-fit (a method that does not run to the limits) as a model round after 4 November, with the usual checks.
3. Re-fit before 4 November. It moves the forecast ten days out, and the round (pre-registration, review, backtest, full suite) would have to finish in that time.
4. Take the chart off the page until it is re-fitted.

**Recommendation.** 4 now and 2 after 4 November. Option 1 still prints 0% for the ANC among white voters as a figure.

**Blocks.** Nothing else in Brief 6.

### 41. The ward vote and the list vote on /your-forecast

**Context.** Each party row has a list-vote slider and, under "Adjust ward vote", a box reading "Ward vote: points from list vote". The number in the box is the party's ward-ballot share minus its list-ballot share in the published forecast: ActionSA -2.7 means its ward vote starts 2.7 points below its list vote (9.1% against 11.8%); EFF +1.0 means 1.0 point above. Moving the slider keeps that gap. The figure is the gap, not a vote, which is why it reads as unexplained.

**Options.**
1. Show two plain figures per party, "Ward vote" and "List vote", each editable, no gap box.
2. Keep one slider (the list vote) and show the ward vote beside it as a figure, with the gap box removed; a reader who wants a different ward vote types it.
3. Keep the gap box and rename it.

**Recommendation.** 2: one control per party, and both ballots in view as percentages. Needs your yes to these words: the column headings "List vote" and "Ward vote", and no other text.

**Blocks.** That part of Brief 6.

### 42. "Tap or drag" on a phone

**Context.** Your instruction for the ward map is "Choose a party below, then tap or drag across wards to give them ward wins." On a computer both work. On a phone a tap gives a ward; a drag scrolls the page, by design, so a finger can scroll past the map.

**Options.**
1. Keep the one sentence everywhere.
2. Make a drag paint on a phone too, while a party is chosen; the page then scrolls only outside the map.
3. On phones only, "Choose a party below, then tap wards to give them ward wins."

**Recommendation.** 3.

**Blocks.** Nothing; Brief 6 uses your sentence until answered.

### 43. Two yeses: the methodology tooltip, and promoting the current UAT version

**Context.** UAT version d680538f (https://d680538f-joburg-whysoserious.psi-02e.workers.dev) holds the home-page top, the methodology changes, "Follow us on X" in the footer and the methodology's combined-vote "23%". Its page checks passed. Its tooltip on the methodology's 23% reads: "SOURCE: This Model. The ANC's middle share of the votes, ward and party-list together, across 5,000 simulations."

**Decisions.**
1. That tooltip text.
2. Promote d680538f to the live site now, with Brief 6 to follow as its own UAT version.

**Recommendation.** Yes to both. Promoting now keeps the publication record (dated 24 October) true; Brief 6 does not depend on it.

**Blocks.** The live site's next update.

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

**Partly answered 2026-10-23:** "please double check that all drafts are current and only one per person. Marketing - will address later". Checked 2026-10-23: iCloud Drafts holds 93 outreach drafts on your templates, one per recipient; 25 sent on 22 October; the 14 October drafts are in "Superseded drafts 2026-10-22". Decisions 1-4 stay open.

**Gates.** The first send and the first post.

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

**Asked 2026-10-23:** "Need to see some creative and copy proposed for billboard." Copy and frames sent 23 October. Owner chose the opening: "Who will govern Joburg?" / "Think you know?" (replacing "Nobody wins Joburg.", which stated a forecast result); the spot is re-rendered and verified (newsdesk 424ae93). Still open: decisions 1 and 2 and the go-live date.

**Gates.** The go-live date.

