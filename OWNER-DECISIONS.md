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

### 33. How will the frozen forecast be chosen from the pre-freeze arms?

**Context.** You asked for the two untested inputs to be tested before the
freeze (item 31, answered). The runs are pre-registered in
`prereg/2026-10-23-prefreeze-arms.md`:
- **B:** the current forecast.
- **BF:** B with a defect fixed. Three parties (PA, ALJAMAAH, AIC) are drawn with
  a ward pattern of 1.0 because placeholder rows in the γ file hide their real
  fits.
- **A7t:** the by-election turnout tilt off.
- **A7:** all by-election terms off.
- **G2:** γ from 2019→2021.
- **GP:** γ from both fits pooled.

None of them can be scored, because 2026 has no result. A choice made after
seeing the numbers can drift toward the outcome someone prefers, so the
pollster review recommends fixing the rule before anything is read. The
results come to you in a fixed order, each opening with what is known about
its input, with the headline chances after.

**Options.**
1. Freeze B with the defect fixed (BF), and publish the other arms beside it
   as how far the untested inputs move the forecast.
2. Freeze on evidence status, decided now:
   - by-elections stay at ½, measured on 2021 (on scores now withdrawn as in-sample);
   - γ pooled from both folds, which uses the most data and adds no new judgement;
   - the defect fixed.
3. Decide after seeing the reports.

**Recommendation.** Option 2. It is fixed before any result, it uses the most
evidence for each input, and it fixes the defect. Option 1 is the cautious
alternative: one change from what readers have seen since 21 October.

**Blocks.** The freeze, by 31 October. The runs go ahead either way.

**Results, 2026-10-23** (run after this item was written; MODEL-LOG §1.333).
Reports, one per arm against the current forecast:
`reports/model-changes/2026-10-23-prefreeze-{BF,A7t,A7,G2,GP}/report.html`.

| arm | ANC largest alone | DA largest alone | what else moves |
|---|---|---|---|
| B, the current forecast | 58.1% | 33.8% | |
| BF, defect fixed | 61.2% | 30.9% | 4 wards PA → DA |
| A7t, by-election turnout tilt off | 58.4% | 33.5% | nothing measurable |
| A7, by-elections off | 72.1% | 20.6% | ANC +2 seats, DA −2.5, EFF +2; ANC list vote +0.9 points |
| G2, γ 2019 → 2021 | 56.7% | 34.9% | 6 wards; no seat median moves by more than 1 |
| GP, γ pooled | 59.1% | 32.9% | 6 wards; no seat median moves |

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

