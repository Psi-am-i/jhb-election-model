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

## 3. The trust ceiling is the reader's, not ours

Owner: *"trust ceiling is user defined judgement call."* This closes the
question put to the owner in September (E = 3.0pp against ≥5pp) by moving it
onto the page. We ship a default and say what it is; the reader moves it.

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
