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

### 18. The marketing decisions still open

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
