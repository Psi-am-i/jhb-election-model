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

### 34. ActionSA's level in the frozen forecast: which retention?

**Context.** With your 17.6% call withdrawn (item 33), ActionSA's level comes
from its 2021 list vote (18.1%) times a retention, how much of its first result
a party keeps at its second local election. The model uses 0.72, the typical
value for a party of its size, fitted mostly on established parties between
0.5% and 10%. You commissioned a measurement on second-election parties up to
2021 (MODEL-LOG §1.334; `rounds/2026-10-23-out-of-sample/retention/`).
- **The record splits:** COPE kept about 0.2 and APC about 0.4; UDM about 0.7;
  EFF 0.9–3.0, Al Jama-ah 1.2–1.6 and AIC 1.1 grew. No party was near
  ActionSA's 18% at its first local election.
- **The test.** Tried before 2016 and before 2021 on earlier elections only,
  neither the size line nor second-election parties' own median predicted the
  next second election better than the other, and both forecast EFF too low.
- **At 2026** the size line gives 0.72 and second-election parties' median
  gives 0.85. ActionSA's starting level would be 12.6% (as now) or about 14.0%
  (interpolated, not run).

**Options.**
1. Keep 0.72, the model's existing rule. No new judgement. The page says
   ActionSA's level rests on a typical retention and that second-election
   parties have kept from 0.2 to 1.5 of their first result.
2. Use 0.85, second-election parties' median. A measured value with no better
   record out of sample, so in practice a choice between two equal rules.
3. Keep 0.72 and widen ActionSA's range to cover both groups. That is a new
   judgement call.

**Recommendation.** Option 1. The evidence prefers neither number. Keeping
the existing rule adds nothing to argue about, and the page states the spread
plainly. Option 3 is the honest alternative if you want the range to show it,
but it is a judgement call of the kind you asked to avoid.

**Blocks.** The freeze, by 31 October. If no answer by then: option 1.

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

