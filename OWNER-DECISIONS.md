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
