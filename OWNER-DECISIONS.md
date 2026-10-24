# Decisions waiting on the owner

The one place where every open question for the owner lives. Each item carries
its full context, so it can be answered without the chat transcript. A chat
message that needs a decision links here and names the item by its heading.
When an item is answered, it moves to `OWNER-DECISIONS-ANSWERED.md` with the
date and the answer, and the record it changed (JUDGEMENT-CALLS, MODEL-LOG)
is named.

Last updated: 2026-10-24.

---

## Open

Answered items: `OWNER-DECISIONS-ANSWERED.md`.

### 35. Five wording questions before the freeze release

**Context.** The release (frozen forecast, tone sweep, withdrawal of the
in-sample scores) is built on `site-sweep-1`, not published. These five need
your words or a judgement. My recommendation is in brackets.

1. **A live corrections entry that is no longer true** (the "deliberate
   choice" entry). Its "What is right" says "This Model uses only what was known
   before each election it is tested on." Proposed: "Several of This Model's
   settings had been chosen on records that include the elections it is tested
   on; the test scores were withdrawn on 23 October 2026." [Yes]
2. **A live corrections entry describing tooltips that are being removed**
   ("forecasting that election from earlier ones"). Its "What is right" says the
   home tooltips now explain the settings; the withdrawal removes those
   tooltips. Proposed: "The ward counts are removed with This Model's other past
   scores, withdrawn on 23 October 2026." [Yes]
3. **The methodology repeats a claim already corrected.** It says the DA and
   ActionSA "drawing from the same population group means that when one rises
   in a simulation the other tends to fall… a mild offset". The correction of
   23 October removed that claim from the forecast page because This Model
   draws no such trade (the two rise and fall together). Remove the two
   sentences from the methodology, and add "and the methodology" to that
   correction's "What was wrong". [Yes]
4. **"simulations" twice in the home stamp:** "This Model's simulations as of
   23 October · 5,000 simulations". Proposed: "5,000 of This Model's
   simulations as of 23 October". [Yes]
5. **The "Single party majority" preset shows an empty table**, because the
   coalition table lists combinations of two parties or more. Proposed: the
   preset shows one row per party that ever wins a majority alone, with its
   chance (today: MK, 2 of 5,000 simulations), and "No party wins a majority
   alone in any simulation." when none does. [Yes]

Two more need a word:
- The who-can-govern lede keeps "The ANC without the DA has N workable
  majorities", one party singled out. Remove it, as with the DA preset? [Yes]
- The methodology says "Halfway is the owner's choice" (by-election weight).
  Proposed: "Halfway is our choice." [Yes]

**Partly answered 2026-10-24.** Owner: on 1 and 2, "These don't make any sense because the model now does not use information from before elections or what have we been doing? If we no longer use contaminated data, then say the model overclaimed this before today." On 5: "showing MK distorts their real chances, even if we say it. We need to show things that are more likely to be informational. The cut off for showing all coalitions should be 10% or even showing it there is a distortion." On the lede: "Put both the DA and the ANC's workable majorities since they are the two largest parties. The rest are fine." So 3, 4 and "Halfway is our choice" are approved as proposed.

**The facts behind 1 and 2.** The 2026 forecast uses only what was known before the 2026 election: its settings were chosen on elections up to 2021 (PLAN step 5.1), and its other inputs (by-elections, the September 2026 roll, nominations, Census 2022) all predate polling day. The tests on past elections did not: their settings were chosen on results that include the elections tested (MODEL-LOG §1.337). Re-testing each past election from earlier ones only is PLAN steps 3 and 4, not yet run.

**Revised proposals, for your yes:**
- **1a. A new corrections entry** for the overclaim. Heading: "The model uses only what was known before each election it is tested on" — published 2 October 2026 (the date the entry's text carries), corrected on the release date. What was wrong: "A correction on this page said This Model uses only what was known before each election it is tested on, and that the about page's accuracy figures came from that version. That overclaimed: several of its settings had been chosen on results that include those elections." What is right: "This Model's 2026 forecast uses only what was known before the 2026 election. Its scores on past elections are withdrawn; re-scored figures, from earlier elections only, will be published on the methodology page."
- **1b. The "deliberate choice" entry's What is right** becomes "This Model no longer uses party splits that happened after the election it is tested on." (Its What was wrong is about those splits, and that fix stands.)
- **2.** "The ward counts are withdrawn with This Model's other scores on past elections."
- **5. The 10% cut-off.** A combination is listed only if it governs in at least 10% of simulations (today the cut is a smallest majority in at least 5%). On the frozen forecast's page this takes the table from 21 rows to 16; the five dropped are DA+ActionSA+PA 8.6%, ANC+ActionSA+PA 8.5%, DA+MK+PA 8.1%, DA+EFF+PA 7.2%, ANC+EFF+PA 5.7% (`forecast-sheet.html`, `data-p`). The "How to read it" note gains: "Combinations that govern in fewer than 10% of the simulations are left out." The "Single party majority" preset shows the line "No party wins a majority alone in 10% or more of the simulations." while none does, and otherwise one row per party at or above 10%.
- **6. The lede's last sentence** becomes "The ANC without the DA has N workable majorities, n of them with a better than even chance of reaching {majority} seats; the DA without the ANC has M, m of them with a better than even chance." At the 10% cut: ANC 8 and 4, DA 7 and 4 (counted from the same page).
- **6b. Question.** The lede opens "If the DA rules out the ANC, the EFF and MK, ActionSA and the PA give it the numbers: 8.6% chance. With the smaller parties as well: 87.7% chance." That is one party's red lines, and the 8.6% route falls under the new cut. Remove those two sentences, so the lede is only the two-party sentence? [Yes]

**Blocks.** The publish build and UAT.

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

