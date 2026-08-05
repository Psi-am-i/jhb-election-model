# Methodology and review brief

**City of Johannesburg 2026 local government election model**
Status as at 4 August 2026 · election date 4 November 2026

This document is written for external review. It describes what the model
predicts, where every input came from and how it was validated, what went wrong
along the way and what was done about it, and — importantly — where the
implementation departs from the original written plan and why.

Companion documents: `SOURCES.md` (acquisition detail, URLs, access
constraints), `MODEL-LOG.md` (running internal log and risk register; §1.14
records the 2026-08-04 implementation review, §1.15 the corrected forecast),
`joburg-prediction-model-plan-v2.md` (the original plan, now annotated with
corrections), `model-review.html` (the review that found six implementation
errors, with its resolution addendum), and `forecast-interactive.html` (every
scenario assumption as a bounded, defaulted control; its scenario JSON
reproduces a slider state exactly in `src/montecarlo.py --config`).

A reviewer wanting to check a specific claim should be able to find both the
script that produces it and the validation that it is right. Every figure quoted
below is reproducible from the scripts named.

---

## 1. What is being predicted

The City of Johannesburg council has 135 ward seats elected first-past-the-post
and 135 compensatory proportional-representation seats, 270 in total, with a
majority at 136. This was verified independently rather than taken on trust: the
Municipal Demarcation Board's 2026 ward layer contains exactly 135 CoJ wards
(`src/build_geo.py` fails loudly otherwise), which also refutes an April 2026
press report of 274 seats.

**The quantity the model must predict is a party's share of the ward and PR
votes added together.** This is the single most consequential correction made to
the plan and is set out in §3.1 below.

The honest output is a distribution over coalition viability, not a point seat
forecast. The reasons are quantified in §6.

---

## 2. Data: provenance and validation

### 2.1 What was acquired

| Input | Coverage | Source |
|---|---|---|
| LGE results, VD level, both ballots | 2011, 2016, 2021 | IEC results portal, `LGEPublicReports/{197,402,1091}` |
| NPE results, VD level, provincial ballot | 2014, 2019, 2024 | IEC bulk exports (two different hosts — see below) |
| Seat calculation reports | 2011, 2016, 2021 | IEC, used as validation targets |
| Ward boundaries | 2011, 2016, 2020(=2021), 2026 delimitations | MDB Spatial Knowledge Hub |
| Voting-district boundaries + ward links | 2026 | MDB `VotingDistricts2026_Final` |
| By-elections, VD level, all parties | 38 Gauteng contests since 2021, 15 in CoJ | IEC by-election dashboard |
| Census covariates by ward | 2022 | Stats SA ward-level Small Area Population Estimates |

Acquisition is fully scripted (`src/fetch_iec.py`, `fetch_boundaries.py`,
`fetch_byelections.py`) so it can be re-run and audited.

### 2.2 Access constraints encountered

These are recorded because they shaped what was obtainable, and because a
reviewer reproducing this work will hit them.

- **The IEC hosts return 403 to ordinary HTTP clients** regardless of user-agent
  or referer. Generated *report files* are served through unchallenged and are
  fetchable directly; the single-page-app shell and the bulk `.zip` exports are
  not, and required a real browser session.
- **Election identifiers are not years and differ per ballot.** The 2019
  provincial election is id 827, not 700 as the national/provincial pairing
  elsewhere would suggest. Guessing would have silently retrieved the wrong
  election. Ids were read from the portal's own dropdown and are recorded in
  `SOURCES.md`.
- **The 2014 NPE is not on the results portal at all** — that URL pattern 404s.
  It is published on a second host, found by working through the portal's report
  picker.
- **By-election reports are served only through per-session tokens**
  (`ReportViewer?_f=…`) which fail outside the browser that generated them. This
  was bypassed rather than worked around: the by-election *dashboard* is backed
  by static JSON needing no session, and its per-municipality file is richer than
  the PDF would have been — voting-district level, every party, candidate names,
  and historical comparators.

### 2.3 Validation performed on the data

Data was not accepted on arrival. Each of the following is an independent check
that passed:

| Check | Result |
|---|---|
| CoJ turnout, all five elections, vs IEC published figures | matches (2016: 57.06%, 2021: 42.61%) |
| 2024 CoJ party shares vs the plan's own §8 anchor table | every party within rounding |
| 2014 file's ward count vs the 2011 delimitation boundary layer | both give 130 |
| 2016/2021/2026 ward counts vs boundary layers | all give 135 |
| 2016 per-municipality CSV vs the independently generated national export | JHB PR totals identical, party for party |
| Seat allocator vs IEC's published Seat Calculation Detail | exact for 2011, 2016 and 2021 |
| 2026 VD-part registration (`WardPop`) vs VD totals (`REGPOP`) | reconciles exactly for all 865 VDs |

The seat-allocator check is the strongest: it reproduces the published council —
quota, total valid votes, and every party's seat count — for three elections
across two council sizes, from the VD-level result files alone.

### 2.4 Durability

Sources are not stable. The MDB has already retired the per-municipality
shapefile downloads its previous site served; they survive only in the Internet
Archive. `src/archive.py` therefore records every input with its size, SHA-256
and provenance. Data itself is not in version control, but the manifest is, and
`--verify` re-hashes and reports drift.

### 2.5 What could not be obtained

Recorded honestly because both bear on the model's limits:

- **Census 2022 Small Area Layer** (income, dwelling type, employment). Stats SA
  does not publish it; it is supplied on request only. The ward-level product was
  used instead, which carries age, sex and population group but no economic
  variables. This limits the turnout sub-model's covariate term.
- **Historic VD boundaries.** Not published anywhere reachable — checked against
  the MDB's full 43-service catalogue, both of its data portals, ArcGIS Online,
  the IEC's own GeoServer, and an Internet Archive sweep of both hosts. The
  consequence is discussed in §5.1, where it is shown empirically not to matter.

---

## 3. Corrections to the plan, with reasoning and impact

Each of these is a place where implementation revealed the plan to be wrong or
underspecified. They are ordered by consequence.

### 3.1 Seat entitlement follows the combined ward+PR vote — *material*

**What the plan said.** §0: entitlement is determined by citywide **PR ballot
share**, therefore "ward-level prediction is *not* the primary target".

**What is true.** Entitlement follows the ward and PR votes *added together*.
The IEC's own Seat Calculation Detail report quotes Municipal Structures Act
Schedule 1:

```
Q = (A / (B − C − D)) + 1, disregarding fractions
A = total valid votes for all parties, WARD AND PR BALLOTS ADDED TOGETHER
B = seats available (270)   C = independent ward councillors
D = ward seats held by parties with no PR list
```

Seats are `floor(votes / Q)`, remainder by largest remainder. `A` excludes
independents and parties with no PR list.

**How it was verified.** `src/validate_seats.py` reproduces the published
council exactly for 2011 (quota 8,319, 260 seats), 2016 (quota 9,247, ANC 121 /
DA 104 / EFF 30) and 2021 (quota 6,794, ANC 91 / DA 71 / ActionSA 44 / EFF 29).
The exclusions reconcile to the individual vote: 1,846,189 − 11,904 independents
− 24 − 1 = 1,834,260, the published `A`.

**Why the original reading survived scrutiny.** Ward and PR shares usually agree
within about a point, so PR is an excellent proxy. In 2016 the DA polled 38.34%
ward against 38.48% PR — which is exactly why the plan's own sanity check ("104
seats ≈ 38.4% of 270") appeared to confirm the PR-only rule. **ActionSA in 2021
is the counter-example**: 13.98% ward against 18.12% PR, a gap worth about five
seats. They contested 134 of 135 wards, so this is genuine ticket-splitting, not
absent candidates.

**Impact.** The ward ballot is roughly half the target quantity rather than a
secondary concern. Both ballots are now modelled and fitted separately. A
PR-only model would misforecast any party whose two ballots diverge — precisely
the insurgent parties that decide coalition arithmetic.

**Second-order consequences now tracked.** Contestation coverage is a distinct
effect from ticket-splitting (the PA fielded ward candidates in only 52 of 135
wards in 2021, structurally capping its ward total). And overhang, which the plan
treated as remote, is closer than implied: in 2021 the ANC took 87 wards against
an entitlement of 91.

### 3.2 The share model's renormalisation was inconsistent — *material*

**What the plan said.** §3.4(b): work in logit space, then "softmax
renormalisation" within each VD.

**Why that is wrong.** `logit(p) = log(p/(1−p))` exponentiates to *odds*, so a
softmax over logits normalises odds rather than shares. Odds and shares diverge
as p grows, so the entire error falls on the largest parties. Implemented as
written, it placed the ANC at 54.0% against an actual 44.9% *even with θ set to
the exactly observed citywide ratio* — nine percentage points of error generated
purely by the renormalisation step.

**Correction.** Logit → expit → rescale. Softmax pairs with multinomial
log-shares; binary logit pairs with expit and rescaling. The correction keeps the
behaviour §3.4(b) actually wants — proportional swing where a party is small,
additive where mid-sized, never negative.

**Impact.** VD-level MAE fell from 0.93pp to 0.49pp; the EFF's citywide error
from −5.42pp to +0.02pp.

### 3.3 θ has two incompatible definitions — *material for the Monte Carlo*

Calibrating fold 1 revealed that "θ" can mean two different numbers:

- **raw** — the observed citywide LGE/NPE ratio. This is what §3.5's parameter
  table quotes, and the fold reproduces its figure exactly (θ_ANC raw = 0.86
  against the plan's cited 0.86).
- **calibrated** — the value that reproduces that ratio *through the model*, once
  within-VD renormalisation is accounted for. θ_ANC calibrated = 0.79; θ_DA raw
  1.19 against calibrated 1.46.

Feeding raw ratios in as if calibrated leaves a systematic residual on the
largest parties: ANC +3.1pp, DA −3.3pp.

**Correction.** `calibrate_theta()` solves for the model-consistent value by
iterative proportional fitting. Both values are reported and written out.

**Impact and warning.** **§3.5's prior ranges are stated in raw units and cannot
be handed to the Monte Carlo directly.** They must be converted, or restated in
calibrated units, before use. This is an open trap for the forecasting stage.

### 3.4 Multiplicative θ cannot represent a new entrant — *material*

ActionSA took 18.12% in 2021 from 0.00% in the 2019 baseline. No multiplicative
factor can produce that. Worse, calibrating θ with the entrant missing **silently
distorts every other party's θ to absorb the gap** — the ANC's calibrated θ came
out at 0.12 and the DA's at 0.15, values that look like parameters but are
artefacts of the missing party.

**Correction.** New entrants are seeded with an explicit citywide share prior,
spatially flat, and the remaining parties renormalise around it.

**Impact.** With ActionSA seeded, fold 2's VD MAE falls from 0.94pp to 0.54pp
and the θ values become interpretable.

**For 2026.** MK is present in the 2024 base at 12.22%, so multiplicative θ_MK is
valid. Any party contesting 2026 without a 2024 provincial-ballot presence needs
an absolute share prior instead.

### 3.5 The VD concordance did not need a spatial intersection — *simplifying*

**What the plan anticipated.** §2 step 2: intersect historic VD shapefiles
against 2026 ones, apportion votes across children, threshold boundary nibbles.

**What the data shows.** Between 98.8% and 100% of each election's VDs persist
in the 2026 set under the same number, and those that do not carry only
0.21%–0.45% of that election's votes. The concordance is therefore keyed on VD
number. Unmatched VDs — mostly tents and temporary voting stations that stopped
existing — are recorded as `unmatched` rather than dropped, so the loss stays
visible rather than becoming a silent shortfall.

**The caveat, and how it was resolved.** A stable VD *number* is not a stable VD
*boundary*: when a VD splits, one child conventionally keeps the parent's number
over a smaller area. This cannot be checked geometrically because historic VD
boundaries are not published (§2.5). Rather than assume it away, two proxies were
computed — registration drift against the citywide trend, and voting-station
continuity — and every VD carries a stability flag. **The assumption was then
tested directly** (§5.1) and found immaterial.

### 3.6 Ward apportionment is registration-weighted, not area-weighted — *improving*

Step 5 is harder than the plan implies: 181 of 865 VDs straddle a 2026 ward
boundary and must have their votes split. Assumption A1 asks for registration
weighting "wherever the roll permits". It does permit: the MDB layer's `REGPOP`
is the VD total and `WardPop` is the individual part's registration, and they
reconcile exactly for all 865 VDs.

**Impact.** Beyond being what A1 asks for, this correctly assigns **zero weight
to 59 parts that contain no registered voters** — slivers where a VD polygon
crosses a ward boundary with nobody on the far side. Area weighting would have
given each of them a real share of the vote.

### 3.7 Turnout: A3 holds, but λ is the wrong carrier — *proposed, not adopted*

**What the plan says.** §3.3 predicts `T_2026(i) = T_2024(i) × λ̂(i)`, resting on
A3: the relative pattern of drop-off across VDs is stable. The plan calls this
"the model's central bet" and "the most stable feature of South African metro
elections".

**What was measured.** The correlation between λ_2016 and λ_2021 across 823 VDs
is **+0.39** — the right sign, robust to VD size (+0.32 among VDs above 2,000
registered, +0.33 registration-weighted), but explaining only about 15% of the
variance. Directionally sound, materially weaker than the plan's framing.

More usefully, predicting VD turnout with every predictor rescaled to the true
citywide total, so only the relative pattern is judged (MAE in turnout points):

| Predicting | Previous LGE level | Plan's ratio form | Preceding NPE level |
|---|---|---|---|
| 2021 | **0.0409** | 0.0592 | 0.0657 |
| 2016 | **0.0527** | *(needs 2009 NPE)* | 0.0769 |

Same ordering in both cycles. Like predicts like: LGE turnout patterns are better
predicted by the previous LGE than by the preceding NPE.

**Decision: recorded as a suggested change, not adopted.** Deliberately weaker
treatment than §3.1–§3.4 because the evidence is weaker — two cycles, one of them
Covid-affected. It will be scored inside the folds on seat outcome before being
adopted. λ̂ is retained for the citywide level regardless, where it performs well:
it implies 0.66 and a projected 41.9% citywide 2026 turnout (41.7% before the corrupt-VD cleanup and by-election tilt), inside §8.2's
expected 38–42%.

This asymmetry of treatment is deliberate and worth a reviewer's attention: §3.1
is a *correction* because it is verified against the IEC's own arithmetic three
times over; §3.7 is a *suggestion* because it rests on two observations.

---

## 4. Data quality problems found

Every one of the following corrupts data silently rather than raising an error,
which is why each is listed with the specific evidence that caught it.

| Problem | Where | Detection and handling |
|---|---|---|
| Unquoted commas in voting-station names shift every subsequent column, **while row width stays constant** because a trailing pad column absorbs the shift | 2019 NPE; e.g. JHB VD 32851278, `TENT (TSUTSUMANE, EXT 7 )` | A column-count check does *not* catch this. Rows are parsed anchored at both ends instead. |
| Character encoding varies by year | 2019 is DOS CP850 (`CAF\x90` = CAFÉ), 2011 is UTF-16, others UTF-8 | Byte-order-mark check, then decode probing |
| `VALID VOTES` / `TotalValidVotes` is the *party's* votes, not the VD total | 2014 NPE and all LGE files | VD totals recomputed by summing parties |
| Header punctuation drifts; one header embeds a timestamp | across years | header normalisation |
| Party codes derived from initials collide | `ARISE SOUTH AFRICA` merged into ActionSA; `ALLIED MOVEMENT FOR CHANGE` into `AFRICAN MOVEMENT CONGRESS` | Derived codes are now full names, and the builder *fails* on any merge occurring through a derived code — merging is only valid when explicitly declared |
| Ward geometry duplicated | 2011 geodatabase stores every ward twice, byte-identical | Exact duplicates dropped; a ward id appearing with *differing* geometry is treated as an error, not silently collapsed |
| Comparing station names against a file that has none flags everything | 2014 bulk carries no station names | Compare only when both sides name a station |
| `REGPOP` on the 2026 VD layer is a **2024** snapshot (sums to 2,348,781) | boundary layer | Documented; must not be read as current registration |
| Turnout above 100% — cast exceeds registered where a VD's roll shrank between snapshot and count | 87 VD-years, worst 245% (2019); one VD's λ projected 9.9% 2026 turnout | VD-years above 105% dropped from the λ series (found in the 2026-08-04 review); fold metrics re-scored below |

Two of these were bugs in our own first implementation (the party-code collision
and the station-name comparison), caught by validation checks rather than by
inspection. They are listed alongside the source-data problems deliberately.

---

## 5. Validation results

Following §4.1's discipline: parameters are fitted on fold 1 and validated on
fold 2. Fitting both and reporting the fit would not be validation.

### 5.1 Fold 2 — out-of-sample (2019 NPE → 2021 LGE)

| Configuration | VD MAE | Ward winner | Seat MAE | Total seat error |
|---|---|---|---|---|
| refit in-sample (reference only) | 0.52pp | 129/135 | 0.43 | 10 |
| θ and γ both carried from fold 1 | — | 126/135 | 2.22 | 60 |
| **γ from fold 1, θ recalibrated** | 0.52pp | 129/135 | 0.50 | 12 |

*(Figures re-scored 2026-08-04 after the implausible-turnout data fix — 87
VD-years with turnout above 105% dropped from the λ series; the earlier
version of this table read 128/135 and 54.)*

**The central validation finding: γ transfers across cycles, θ does not.**
Carrying γ over costs almost nothing; carrying θ over quintuples the seat error.
γ is structural — it encodes where a party's support sits relative to its
citywide mean, and that geography is stable. θ is political weather, and
2014→2016 says little about 2019→2021.

This supports the plan's own treatment of θ as a wide scenario lever rather than
a fitted constant, and means γ can reasonably be fitted once and reused.

**What this validation does and does not cover.** Fold 2 validates the
*spatial projection machinery* — given a citywide outcome, the model places it
across wards and VDs accurately. It cannot validate the 2026 citywide
*ranges*, which no backtest can reach: those are informed priors, and every
probability in §5B inherits them. This is stated here because the earlier
draft of the distribution sheet blurred the distinction ("without being shown
the answer") — the θ-recalibrated row is conditional on the actual citywide
result; the genuinely blind row's seat error was 60, not 12.

Against §4.3's stated expectation of "±1.5 points MAE on established parties":
the ANC came in at −0.42pp and the IFP at −0.90pp, but the DA at +3.08pp and the
EFF at +2.60pp. The expectation is about right for some parties and optimistic
for others.

### 5.2 Boundary-stability assumption — tested, immaterial

Fold 2 re-run three ways, varying the treatment of the 93 VDs flagged as
possibly redrawn:

| | Ward winner | Seat MAE | Total seat error |
|---|---|---|---|
| all VDs | 129/135 | 0.50 | 12 |
| suspect down-weighted (`w_split` 0.6) | 129/135 | 0.50 | 12 |
| suspect excluded | 129/134 | 0.50 | 12 |

*(Re-scored 2026-08-04 on the cleaned turnout series; the three variants now
agree even more closely than the original run.)* **The VD boundary-stability
assumption is not doing meaningful work**, so the unavailability of historic VD
boundaries does not compromise any conclusion the model draws. The flags are
retained because they cost nothing and would detect a future delimitation that
moved VDs materially.

### 5.3 Fold 1 — in-sample calibration (2014 NPE → 2016 LGE)

Every established party's citywide share reproduced to within 0.03pp, ward
winners correct in 135 of 135 (up from 132 before the turnout-data cleaning),
seat MAE 0.71.

The residual is almost entirely new-entrant blindness, which §4.3 predicts and
this quantifies: the **AIC took 4 seats from a 0.00% base in 2014** and the model
cannot see it, nor Al Jama-ah's 1. Total absolute seat error is 12, of which 5 is
new-entrant blindness and most of the remainder is churn among minor parties in
the largest-remainder tail.

---

## 5A. How the model works, end to end

Six stages. Each is a separate script and each can be inspected in isolation.

**1. Baseline.** VD-level party shares from the 2024 provincial ballot — the most
recent election with full VD coverage, 865 VDs, 1.42m votes.

**2. Citywide scenario.** A draw specifies where each party lands citywide in
2026. Following §3.4(a) this is drawn at *bloc* level — one shift for
{ANC, EFF, MK}, one for {DA, ActionSA, BOSA} — then split within the bloc by a
Dirichlet **centred on the plan's §3.5 θ-mode view of each party, tilted by
by-election evidence at weight w_bye and by the polling lever, with the
resulting modes clamped to the historically observed ranges** (review E2/E4).
Parties outside both blocs (PA, IFP, VF+, ACDP, Al Jama-ah, Rise) get
individual factors drawn independently, with ranges set around their observed
fold ratios (review E6). Each draw's implied per-party θ is checked against
§3.5's ranges and the excursion rate reported. A generic-entrant slot appears
with probability 0.25 at a drawn share (review A6) — every backtest fold and
the live case contained a party that did not previously exist.

The bloc structure matters more than it looks. Party-level factors are strongly
cross-correlated — the DA and ActionSA compete for the same voters — so sampling
them independently produces incoherent draws where both sit at the top of their
ranges simultaneously. Drawing the bloc and splitting within it makes them
negatively correlated, which is why DA+ActionSA's *combined* range (91–116) is
much tighter than ActionSA's own (5–38).

**3. Spatial distribution.** The citywide target is pushed down to VDs by

```
logit(share(i,p)) = logit(citywide(p)·θ_p) + γ_p·[logit(base(i,p)) − logit(citywide(p))]
```

then converted back and rescaled within each VD. γ controls how much of a party's
local geography is preserved versus flattened to its citywide mean; it is fitted
on fold 1 and, as §5.1 shows, transfers between cycles. θ is solved for so the
prediction reaches the drawn citywide target *through* the model, rather than
being taken as a raw ratio.

**4. Turnout.** Each VD's votes cast is its registered voters times projected
2026 turnout — drawn per simulation as a blend of the λ̂ ratio form and the
2021-LGE-level pattern, with VD-level noise (review A2). The same weighting is
used to calibrate θ and to aggregate the prediction — the fold work showed
that consistency matters more than the choice of turnout specification.

**5. Both ballots.** The PR ballot uses the drawn target directly. The ward
ballot scales it by each party's observed 2021 ward/PR ratio, which carries
the split-ticket structure that made the §3.1 correction necessary —
ActionSA's ratio is 0.77. Parties without a 2021 measurement carry documented
judgements instead of silent defaults: MK (list party, no ward machinery)
0.80; the PA's ratio takes a contestation uplift for fielding more than
2021's 52 ward candidates (review A1).

**6. Ward winners, seats, overhang.** The ward-ballot prediction is aggregated
into the 135 2026 wards and FPTP winners taken. Ward and PR votes are added
and run through Schedule 1 — the same code validated against three published
councils in §2.3. A party keeps every ward it wins: if wins exceed
entitlement, the council expands by the excess and the majority threshold
moves off 136 (review E3; the plan §3.7 reading of Schedule 1 — the statutory
fine print is unverified against a worked example, and a fixed-270
counterfactual toggle bounds its effect).

Repeated 5,000 times, the output is a distribution over coalition arithmetic —
fully enumerated: every subset, minimal winning coalitions, Banzhaf and
Shapley–Shubik power indices, and the minority-government (abstention) class,
judged against each draw's own threshold (review E1). All of it is also
explorable interactively in `forecast-interactive.html`, whose sliders are the
model's actual assumptions and whose scenario JSON round-trips to
`src/montecarlo.py --config`.

## 5B. Results

*(Corrected 2026-08-04 after external review — the earlier version of this
section rested on a pre-filtered coalition list and is superseded; see
`model-review.html` and MODEL-LOG §1.14–1.15.)*

**Seats** (median, 5th–95th percentile, 5,000 draws, seed 20261104): DA 81
(55–103), ANC 75 (58–86), EFF 28 (18–40), ActionSA 26 (10–50), MK 20 (12–29),
PA 14 (10–17), generic new entrant 0 (0–19). The DA is the largest single
party in most draws; the ANC's seat count includes its overhang wards.

**Overhang is the norm, not the edge case.** In ~90% of draws a party — almost
always the ANC — wins more wards (~73 of 135) than its entitlement, because
its citywide share is in the mid-20s while its stronghold wards hold against a
fragmented opposition. The council expands to a median of ~281 and the
majority threshold moves to ~141. Every probability below is judged against
each draw's own threshold. Caveat: the expansion rule is §3.7's reading of
Schedule 1, unverified against an IEC worked example (task #20); a fixed-270
counterfactual toggle bounds its effect.

**Coalition arithmetic, fully enumerated:**

| Finding | Value |
|---|---|
| **ANC + DA** (the dominant minimal winning coalition) | **86.5%**, median 156 |
| DA + EFF + ActionSA | 34% |
| DA + EFF + MK | 26% |
| DA + ActionSA | ~0%, median 108 |
| **DA minority via abstention, 2021 pattern (only the ANC votes against)** | **61%** |
| ANC minority (only the DA votes against) | 38% |
| Some majority without ANC, EFF and MK together | 99.2% — but at median 157 vs threshold ~141, it needs close to the whole non-bloc field |

**Power indices** (Banzhaf, median across draws): DA 29%, ANC 24%, EFF 11%,
ActionSA 11%, MK 8%, PA 5%. ActionSA out-ranks the PA as kingmaker — the
earlier sheet asserted the reverse without computing it.

The politically operative summary: the only reliable *majority* route is
ANC+DA; the realistic alternatives are a DA-led minority administration
resting on abstention (viable in 61% of draws under the 2021 pattern), or a
DA arrangement with one of EFF/MK — arithmetic the model reports and politics
the model deliberately does not judge.

**Turnout leverage** (§5). Per-ward turnout elasticity was computed by perturbing
each ward ±5 points with shares held fixed. The plan stated its expected finding
in advance to be falsified; the result is that the negative half holds and the
positive half does not. Leverage is *not* concentrated in marginal wards
(correlation −0.399 with marginality) and does rise with registration (+0.365) —
both as predicted. But it correlates −0.358 with ward ANC share and +0.321 with
ward turnout, the opposite of the predicted concentration in low-turnout Soweto
and Orange Farm wards. Leverage tracks a ward's *distinctiveness from the citywide
mix* weighted by registration, and the northern suburbs are as distinctive as the
south.

The magnitude claim fails by more. §5 expected a ten-point swing across Soweto to
reallocate "a dozen seats"; perturbing thirty-ward blocs across a full ten-point
span moves two.

**The A5 sensitivity check the plan asked for has now been run**
(`leverage.py --marginal blend`): with the perturbed voters voting as a 50/50
blend of their VD and the citywide mix, every leverage magnitude roughly
*halves* (the Soweto-cluster entitlement swing falls from −1.53 to −0.76) and
the rankings are unchanged. A5 is not doing load-bearing work — if anything it
flattered turnout.

**These two results agree.** The gap from DA+ActionSA's ~108 to the ~141
overhang-adjusted threshold is over thirty seats, and a large differential
turnout swing is worth about two under A5, one under the blend. The plan's
conclusion that the DA's path runs through ANC-inclined voters staying home
does not survive any version of the test — on this arithmetic the gap can only
be closed by persuasion, not mobilisation. That is also consistent with the
fold finding that θ dominates turnout for forecast accuracy.

## 6. Assumptions and limitations a reviewer should weigh

| # | Assumption / limitation | Status |
|---|---|---|
| A | VD number stability implies catchment stability | **Tested and immaterial** (§5.2) |
| B | Within-VD homogeneity when splitting across wards (A1) | Mitigated by registration weighting; residual is that political composition may differ between parts of a split VD, irreducible without sub-VD data. Affects 181 of 865 VDs |
| C | New entrants | **Structural blindness, now carried honestly.** The model is near-exact on parties it has seen and blind to those it has not; fold 1 quantifies the cost at ~5 seats. The forecast carries a generic-entrant slot (P 0.25, share mode 4%, user-adjustable) so the tails reflect the risk instead of footnoting it |
| D | Turnout specification | **Resolved by drawing it.** Each simulation blends the λ̂ ratio form and the 2021-level pattern with VD noise; the two candidate specifications bound the blend and their disagreement is inside the distribution |
| E | Turnout specification | **Resolved as second-order.** Turnout is now wired into the folds. With θ held fixed, a *perfect* turnout forecast scores no better on seats than the crude assumption that patterns are unchanged, and turnout weighting moves total seat error by ~6 against θ error moving it 12→54. Consistency between how θ is calibrated and applied matters more than the specification chosen. Note also that the citywide turnout *level* cannot affect seats at all — scaling all turnout scales the quota identically — so only differential turnout matters |
| F | Missing economic covariates | Turnout sub-model limited to age/sex/population group at ward level |
| G | Two-cycle inference | Several parameters rest on two observed NPE→LGE transitions, one Covid-affected. Treat 2021-derived values as scenario levers |
| H | Concordance leakage | 0.21–0.45% of votes per election sit in VDs that no longer exist; recorded, not dropped |
| I | By-election selection bias (plan A4) | By-elections enter only as within-ward deltas, ρ-weighted, clamped to §3.5's ranges, at weight w_bye 0.40. ActionSA is the party the blend moves most (centre 9.3%→13.1%) — set w_bye to 0 to see the forecast without it |
| J | Overhang mechanics | The council-expansion reading of Schedule 1 is unverified against an IEC worked example, and with P(overhang) ≈ 90% it now matters (task #20). The fixed-270 counterfactual toggle bounds its effect |
| K | Marginal-voter composition (plan A5) | **Tested.** Under the 50/50 blend, leverage magnitudes halve and rankings hold; the turnout conclusion strengthens |

**Limitation C is now the most important outstanding item.** It is also the
strongest argument for the plan's own conclusion that the defensible deliverable
is a distribution over coalition viability rather than a seat forecast: the
parties that decide Johannesburg's coalition arithmetic are precisely the ones
the model is least able to see. ActionSA did not exist in 2019 and took 44 seats
in 2021; nothing in this model would have anticipated that, and nothing in it
would anticipate an equivalent entrant in 2026.

---

## 7. Reproducibility

Everything is scripted and version-controlled. Data is excluded from version
control but inventoried with checksums.

```
src/fetch_iec.py          IEC report files (all curl-able reports, 3 LGE years)
src/fetch_boundaries.py   MDB ward and VD boundaries
src/fetch_byelections.py  by-election results via the dashboard JSON
src/ingest_npe.py         national/provincial ingest, both bulk layouts
src/ingest_lge.py         local-government ingest, both ballots
src/parties.py            party normalisation and bloc structure
src/build_crosswalk.py    party crosswalk + coverage checks
src/build_geo.py          boundary clipping + ward-count checks
src/build_concordance.py  VD concordance + ward apportionment
src/turnout.py            turnout series, λ, and the A3 test
src/seats.py              Schedule 1 seat allocation
src/validate_seats.py     allocator regression test against IEC publications
src/fold.py               backtest folds, both ballots, turnout specifications
src/leverage.py           per-ward turnout elasticity (§5)
src/byelections.py        §3.6 by-election deltas + §3.3 turnout covariate data
src/gamma_recent.py       γ fitted on 2021→2024 for parties fold 1 never saw
src/montecarlo.py         5,000-draw forecast; scenario knobs in DEFAULTS,
                          overridable via --config JSON / --set key=value
src/coalitions.py         full enumeration, MWCs, Banzhaf/Shapley, minority class
src/export_interactive.py ward-level data pack for the interactive page
src/build_interactive.py  assembles forecast-interactive.html (self-contained)
src/archive.py            checksum + provenance manifest
```

The interactive page (`forecast-interactive.html`) exposes every scenario knob
as a control at its default, bounded by its documented range, and emits a
scenario JSON that reproduces the slider state exactly in the Python model.
Its client-side engine is exact for citywide seat arithmetic and approximates
ward winners at ward rather than VD resolution; the Python reference figures
are displayed on the page for comparison.

Suggested order for a reviewer wanting to verify the most consequential claim
first — each self-asserts against the IEC's published figures and exits non-zero
on any mismatch, so no figures need checking by eye:

```
python src/validate_seats.py --year 2021               # quota 6,794  A 1,834,260  270 seats
python src/validate_seats.py --year 2016               # quota 9,247  A 2,496,617  270 seats
python src/validate_seats.py --year 2011 --seats 260   # quota 8,319  A 2,162,768  260 seats
```

2021 additionally asserts every individual party's seat count. If these three
pass, the seat arithmetic underpinning §3.1 — the model's most consequential
correction — is sound.

Then `python src/fold.py --fold 2 --fit-from 1 --transfer gamma --entrant
ASA=0.1812` reproduces the out-of-sample validation in §5.1, and
`python src/archive.py --verify` confirms no input has drifted from the copy
every figure above was computed on.
