# Brief: the badge measures closeness to our prediction (owner, 2026-10-13)

QC.md §4b. Owner's direction 2026-10-13, after seeing the variants measured in
the scratchpad (`score/v4.py`). It replaces CARD-COHERENCE-BRIEF's "one chance
on the card" (boldest call) and its ten-seat amendment.

## The defect
- The analysis prints each party's chance of landing within 2 seats (or 2
  points) of the reader's number. A small party gets about 90% for almost any
  guess, while a large party gets about 11% even at our own number.
- The council-outcome chance gives our own prediction 47%.
- The card badge comes from the single boldest call.

Owner: "47% for everything looks broken. must feel right." Owner: "I would not
give them a score. A score gives the impression of chance and a wild call does
not have a 78% chance."

## Items

### 1. One closeness measure, never printed as a number
Each party's closeness is the weighted share of draws whose distance from OUR
published prediction (forecast.json `start`, the one definition the
ten-seat work already uses) is at least the reader's distance:
P(|X − ours| ≥ |reader − ours|).

How it is built:
- It is computed separately for seats and for the list vote. Seats count ties
  at integer distances as ≥, so ours scores 1 exactly.
- A party's closeness is the mean of its seats and vote values.
- Large L is the mean over the 6 parties with the most seats in our
  prediction. Small S is the mean over all other parties, excluding any party
  with 0 seats and under 0.5% list vote in both our prediction and the
  reader's.
- Overall = (2L + S)/3.

Declare 6, 2:1 and 0.5% in JUDGEMENT-CALLS.md as an amendment to §N10, with
the owner's reasons ("large parties and predictions are way more important").

One definition lives in `src/reweight.py`, reused by page.py and the seat
Worker through the existing sync mechanism. Reuse
`reweight.weighted_probability`. The scratch implementation is in
`/private/tmp/claude-501/-Users-simondavis-projects-atlas-jhb-election-model/4d474bc9-5cd8-4783-ae76-e5d72dbc3c81/scratchpad/score/v4.py`
(reference only; do not copy unreviewed).

### 2. The badge, banded from the overall closeness
Use the five existing reader badges: Safe bet, Steady as she goes, Long shot,
Wild call, Hail Mary.

Cut-offs are set from the model itself, not typed by feel:
- Score every draw of the published draws as if it were a reader's forecast,
  through the same function.
- The bands are fixed quantiles of that distribution:
  - Safe bet: closer than 75% of our simulated results;
  - Steady as she goes: 50-75%;
  - Long shot: 25-50%;
  - Wild call: 5-25%;
  - Hail Mary: closer than under 5%.
- Compute the cut-offs at build time from the published draws (build_make.py
  or wherever forecast.json's derived numbers are made) and write them into
  the artefact the page and Worker read. Never hand-type them.
- Our prediction must band as Safe bet (test).

The badge prints **no percentage**. Nothing on the page or card prints the
overall closeness as a number.
- If code draws the band text into the stamp (today "45%+" / "<30%", via the
  `_printed` helper), remove that code.
- If the number is in the SVG art itself, leave the art: the owner is making
  new badges with no numbers (2026-10-13). Make the stamps easy to replace
  file-for-file, and report which files carry numbers.

### 3. The card
- The badge, plus one short line saying what it is, for example "How close
  this is to our prediction, with the largest parties counting double."
  (STYLE.md tone; keep it short).
- No boldest-call line, no chance sentence, no council-outcome chance.
- Delete the boldest-call and minimum-seats machinery wherever nothing else
  uses it (`boldest_call`, `MIN_CALL_SEATS`, `min_seats` guards), and update
  §N10 accordingly. Keep one definition.
- Old sealed links keep working and redraw with the new badge.
- Bump the card version through the existing CARD_VERSION mechanism, with
  redirects from older /og/ versions as before.

### 4. The analysis page
- Keep the "Citywide vote and seats" table and its per-party chances as they
  are.
- Replace the footnote ("* Within 2 seats of yours. † Within 2 points of
  yours...") with plain column headings, for example "Chance it lands within 2
  seats" and "Chance it lands within 2 points". Wording follows STYLE.md, with
  no symbols.
- Show the badge with the same one-line explanation.
- Remove the council-outcome chance sentence. The outcome's description
  (largest party, majority, coalition) may stay.
- Add one line, on the analysis and wherever the badge appears beside a sealed
  entry, stating how entries are actually ranked. Reuse arrival.js's existing
  sentence: "seats per party first, then wards called right, then vote per
  party". Say that the badge plays no part in the ranking. Keep one definition
  of that sentence.

## Constraints
- No forecast number changes; `src/montecarlo.py` and `src/pools.py` are
  untouched.
- `src/reweight.py` and the copies in worker-api/seats-py and interactive/py
  stay identical by their sync scripts.
- Existing sealed links keep working.

## Checks (interactive tier)
- `tests/test_reweight.py`:
  - ours = 1 on every party;
  - the band of ours is Safe bet;
  - monotone: moving one party further from ours never raises its closeness;
  - the tiny-party exclusion both ways;
  - cut-offs equal the stated quantiles of the draws' own scores;
  - mutation checks: drop the ×2, include tiny parties, cap at ours; each must
    go red.
- Also run `tests/test_reader_seats.py`, the node share tests by file, the
  share fixture regenerated by its tool, and a scratch build.
- Report the band and overall closeness (closeness to the agent only, never
  printed) for:
  - our prediction;
  - fixtures A and B;
  - the owner's screenshot forecast (ANC 75/23.3, DA 65/25.8, ActionSA
    33/14.4, MK 26/10.6, EFF 25/9.5, PA 14/2.6, IFP 4/1.5, Rise 4/1.6,
    Al Jama-ah 3/0.9, ACP 3/0.9, BOSA 3/1.0, SACP 3/1.3, ACDP 2/0.7, VF+
    2/0.9);
  - the mild, moderate and wild forecasts in score/v4.py.
- Whole suite once before release.
- Then deploy the test seat Worker `joburg-seats-uat` and a site version bound
  to it (docs/DEPLOY-UAT.md), plus a normally bound version for promotion.
  Render cards at 1200 wide from the test site for our prediction, fixture B
  and wild.

Promotion to live is the owner's alone, as is any live `joburg-seats` deploy.
