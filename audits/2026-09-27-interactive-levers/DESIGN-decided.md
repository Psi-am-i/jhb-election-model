# What the owner decided, 2026-09-27

Recorded here because they were said in conversation and conversation is where
this project loses things.

## 1. Turnout by area — the geography exists, the grouping is a choice

I said no geographic grouping of the 135 wards existed. **That was wrong about
the geography.** `data/processed/ward_hex_layout.json` places all 135 wards at
real coordinates (`method: "optimal"`), and `data/raw/geo/wards2026_JHB.geojson`
carries the polygons. What does not exist is a *named* grouping.

Derived here from the polygon centroids — central is the nearest fifth to the
city centroid, the rest by compass angle — and checked against the 2026 roll:

| sector | wards | registered |
|---|---|---|
| north | 21 | 453,445 |
| east | 32 | 541,497 |
| south | 23 | 420,195 |
| west | 32 | 519,665 |
| central | 27 | 483,113 |

Balanced enough to be usable. ⚠️ **It is a derived geometric split, not an
official one.** The City of Johannesburg's own administrative regions A–G are
official and would survive a challenge; compass sectors are ours and would have
to be defended. The owner picks: compass sectors as above, or the City's regions.

## 2. Polls — per poll, not one blended dial

Owner: *"show each poll and let user apply it and then slide trust level from no
effect to perfect prediction. show the variation between polls, enable or
disable certain polls and apply the average."*

So the control is not one number. It is:

* **a row per poll** — house, date, sample size, its numbers, and its caveat,
  which for several of them is the most informative field;
* **a toggle per poll** — in or out;
* **one trust slider**, 0 to 100, over whatever set is toggled on: 0 = the
  forecast is untouched, 100 = the poll's result is taken as the outcome;
* **the spread between polls shown**, because with five Johannesburg polls
  disagreeing by more than twenty points on the ANC, the disagreement is the
  finding and hiding it inside an average would be the dishonest move;
* **an average across the enabled set**, as one of the choices rather than the
  only one.

⛔ **This is a new parameterisation and not a relabelling.** `poll_credence`
multiplies a blend weight and clamps to [0,1]; 1.0 is the identity, not "the
poll happens exactly", and 0 does not turn polls off because the arrivals path
is gated by `poll_paths` alone. The dial above has to be built, and both paths
have to be gated together.

## 3. The trust ceiling is the reader's, and ours is zero

Owner: *"trust ceiling is user defined judgement call."* Then, asked what we
ship it at: *"our trust ceiling is zero basically."*

That closes the question put to the owner in September (E = 3.0pp against
≥5pp). It was never a number we had to choose — it is a number we decline to
use, and the reader supplies their own.

**It is also already true rather than a new position.** Polls left the forecast
on 12 September 2026 (MODEL-LOG §1.244) and `poll_paths` ships `"off"`. So a
trust slider at zero is not a default chosen for the page; it is the published
forecast, exactly.

Three things follow and they are all to our advantage:

* **The page's untouched state reproduces what we publish**, on this dimension.
  No caveat needed, no divergence to explain, and the reader who moves nothing
  sees our forecast rather than a variant of it.
* **We never have to defend a poll weighting**, because we do not apply one.
  The disagreement between the houses — the ANC at 18 in one Johannesburg poll
  and 31 in another — is shown to the reader as the state of the evidence,
  and it is the reader who decides what to do about it. That is a stronger
  position than any blend we could have justified.
* **The polls are still published.** At zero they are displayed and not
  applied. A poll nobody weights is still evidence a reader is entitled to see,
  and showing it while saying we give it no weight is more honest than omitting
  it.

⚠️ **Say the default out loud on the page.** A slider that starts at zero looks
like an unset control. It is a position, it is the site's position, and the page
has to say so or a reader will read it as an oversight and move it thinking they
are fixing something.

## 4. The roster follows the IEC, never a newspaper

Owner: *"we must match the iec party count and roster — not newspapers."*

Our roster is 82, hand-typed from reporting that disagreed with itself: Sowetan,
Sunday Times and Business Day say 82, IOL and Daily Friend say 75, all citing
the same 16 September certification. `complete = true` in the judgements file
**licenses deleting every party it omits**, so the count is load-bearing.

**Action: obtain the IEC's own certified Johannesburg list and reconcile the
roster to it.** The 23 September ballot draw fixed party order on the CoJ
double-column ballot and is the artefact most likely to carry the definitive
list. Until then the roster is a newspaper count wearing `complete = true`.

## 5. Post-election scoring — specified

Owner: *"post election scoring is the point. of course it can be done. we have a
result and thousands of forecasts. some are objectively superior to others."*

Three measures, his:

1. **seat count per party** — absolute error per party, summed;
2. **correct party by ward** — how many of the 135 ward winners were called;
3. **correct seat allocation, ward against PR** — whether a forecast got the
   split right, which is where the excessive-seats clause lives and is the thing
   this model exists to be tested on.

Scored identically for every reader's forecast and for the model's own, which is
what makes "objectively superior" mean something.

⛔ **THE RULE AND THE CODE MUST BE FROZEN BEFORE 4 NOVEMBER.** A scoring rule
written once the result is known is not a scoring rule. Two things it needs in
advance and does not have: the result-ingest path, and the party-name mapping —
`HANDOVER.md`'s nomination runbook already records that the IEC spells four
Johannesburg parties differently from the files their baselines come from, so
the result file will hit the same wall on the night.

## 6. The two IEC totals, explained

The IEC's registration page prints, in one snapshot dated 26 September 2026:

* **2,417,302** in the demographics block (the age/gender table's own total);
* **2,417,915** summing its 135 ward rows.

613 apart, 0.025%. Both were re-read rather than assumed — pages 1 and 2 of the
ward table were transcribed by hand and then re-extracted programmatically and
compared identical. Which is authoritative is unknown; the likeliest reading is
that the demographics table counts only voters with a complete age/gender record
while the ward table counts everyone allocated to a ward, but that is a guess
and is recorded as one. It changes nothing at this precision — it is 0.025% of a
denominator — and it is written down so nobody spends an afternoon rediscovering
it.

## 7. Three more, 2026-09-28

Asked with a recommendation each; the owner overrode one.

* **Route B is built first**, before the seat-law comparison ships on its own
  (recommended the reverse; owner chose Route B first).
* **Turnout by area uses the compass sectors** of §1 (north, east, south, west,
  central), not the City's regions A–G. They are ours and the page has to say
  how they were drawn.
* **The untouched page shows the published 5,000-draw forecast.** The engine runs
  300 draws only once a reader moves a control, and the page then says its band
  is wider than the published one. This dissolves the "first 300" problem in
  `INPUT-ROUTE.md`: no 300-draw figure is shown until a reader has asked for one.

## 8. No party is singled out (owner, 2026-09-28)

Owner, on the DA-among-Black-Africans slider of PUBLISHING-BACKLOG §9a:
*"doing it for one party is pointless. everything applies to everyone. no
special treatment."*

**Rule: every control a reader has applies to every party.** No control, range,
default or label exists for one party that does not exist for all. A
one-party control tells readers which claim we think matters. That is the
model taking a side, whatever the range.

So the DA slider is withdrawn as specified. If it survives at all it becomes
**each party's support within each population group**, with each range taken
from that party's own record. That control is larger than one slider and has not
been designed.

## 9. The freeze, the reader's forecast, and accounts (owner, 2026-09-28)

**Freeze: F3 + F5 only** (TODO §0): C1 conservation and mergers. F4 (partial
pooling of unidentified pools) waits until after the election; F6 was deferred
by measurement (MODEL-LOG §1.268). Target 1 October.

**A reader's forecast.** The owner's words:
*"let them run forecasts and adjust levers. Then make 2 specific changes: a
change to the PR vote and changes to ward seat winners and arithmetically we
force them to stay within statute. … it is ignoring all our levels and logic and
is only constrained by the correct count and law. Once they save it, we can
analyse how far out we think it is to the bounds of history."*

So:
* **Start** from a model state: the published forecast, or whatever the levers
  produce.
* **Two edits only:** the citywide PR vote shares, and the winner of any ward.
* **Seats come from the statute alone**, computed in the browser by the
  project's own seat-law code (`seats.allocate`, served from `src/`, never
  retyped). No model level, band or logic constrains the reader.
* **The one assumption the arithmetic needs, stated here so it is visible:** a
  reader supplies a PR vote and ward winners, not two ballots. The statute
  sizes each party's entitlement from the combined ward and PR vote, so the
  reader's PR shares stand for both ballots. Wards are then taken as picked,
  and PR seats fill each entitlement under the excessive-seats clause.
* **After saving**, the forecast is scored against the historical record ("how
  far out it is"). That is analysis of a saved forecast, not a constraint on
  making one.

**Sign-in is needed to save and share, not to create** (as prototyped).

**Accounts.**
* **Providers:** Facebook, Instagram, X, Apple, Google, Microsoft. Instagram
  closed personal-account sign-in in December 2024 (the Basic Display API), so
  Facebook covers Meta users. X returns an email only if the app is granted it.
  Library: `arctic`, which runs on Workers.
* **Data kept: the provider handle and one way to contact** (email, or phone
  where given), nothing else. Not even a display name unless the reader types
  one to show on a shared forecast.
* **After the election every account gets one message** asking whether to
  delete their data or to be told about the next election. **No reply means
  deletion** at a date the owner fixes. That default is the agent's
  recommendation and is not yet decided.
* **Lock time:** 07:00 SAST on 4 November, when polls open.
