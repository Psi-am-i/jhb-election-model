# Model log — findings, obstacles, decisions, mitigations

A running record of what was built, what got in the way, what was decided and
why. Two purposes: to feed the eventual description of the model, and to keep an
honest register of the assumptions it rests on so they can be mitigated rather
than forgotten.

Append to this file as work proceeds. `SOURCES.md` records *where data came
from*; this records *what we learned and chose*.

Status key: **✅ resolved** · **🟡 mitigated, live risk** · **🔴 open, needs a human**

---

## 1. Findings that changed the model

### 1.1 Seat entitlement follows the combined ward+PR vote, not the PR ballot ✅

**What the plan said.** §0: "A party's total seat count is determined by its
citywide **PR ballot share**", and therefore "ward-level prediction is *not* the
primary target."

**What is actually true.** Entitlement follows the party's share of the ward and
PR votes *added together*. From the IEC's own Seat Calculation Detail report,
quoting Municipal Structures Act Schedule 1:

```
Q = (A / (B - C - D)) + 1 ; disregarding fractions
A = total valid votes for all parties, WARD AND PR BALLOTS ADDED TOGETHER
B = seats available (270)   C = independent ward councillors
D = ward seats held by parties with no PR list
```

Then `floor(votes / Q)` per party, shortfall by largest remainder. `A` excludes
independents *and* parties with no PR list.

**Evidence.** `src/seats.py` + `src/validate_seats.py` reproduce the published
council exactly — quota, `A`, and every party's seat count — for three
elections across two council sizes:

| | A | Q | Seats | Result |
|---|---|---|---|---|
| 2011 | 2,162,768 | 8,319 | 260 | quota matches published |
| 2016 | 2,496,617 | 9,247 | 270 | ANC 121, DA 104, EFF 30 — all match |
| 2021 | 1,834,260 | 6,794 | 270 | ANC 91, DA 71, ASA 44, EFF 29 — all match |

The exclusions reconcile to the vote: 1,846,189 − 11,904 independents − 24
Sakhisizwe − 1 African Covenant = 1,834,260.

**Why the error survived review.** Ward and PR shares usually agree within a
point, so PR is an excellent proxy. In 2016 the DA polled 38.34% ward / 38.48%
PR — which is precisely why the plan's own sanity check ("104 seats ≈ 38.4% of
270") appeared to confirm the PR-only rule. **ActionSA in 2021 is the
counter-example**: 13.98% ward against 18.12% PR, worth about five seats. They
contested 134 of 135 wards, so it is genuine ticket-splitting, not absent
candidates.

**Decision.** The ward ballot is roughly half the target quantity. §3 must model
both ballots (task #12). §0 carries a rev-3 correction box.

**Second-order effects now tracked.**
- *Contestation coverage* is distinct from ticket-splitting: the PA fielded ward
  candidates in only 52 of 135 wards in 2021, structurally capping its ward
  total regardless of support. A 2026 forecast needs a view on how many wards
  each party contests.
- *Overhang* did not occur in 2016 or 2021, but 2021 was closer than the plan
  implied — the ANC took 87 wards against an entitlement of 91, five wards of
  headroom. With its citywide share falling faster than its stronghold
  dominance, overhang is a live 2026 risk, not a theoretical one.

### 1.2 A3 holds, but λ is the wrong carrier of it 🟡

**What the plan said.** §3.3 predicts `T_2026(i) = T_2024(i) × λ̂(i)`, resting on
A3: the relative pattern of turnout drop-off across VDs is stable. The plan calls
this "the model's central bet" and "the most stable feature of South African
metro elections".

**What is measured.** `src/turnout.py` tests it rather than assuming it.

*A3 is real but modest.* Correlation between λ_2016 and λ_2021 across 823 VDs is
**+0.39**. Not a small-sample artefact — flat to slightly lower among larger VDs
(+0.32 above 2,000 registered), +0.33 registration-weighted. But λ_2016 explains
only ~15% of the variance in λ_2021.

*The previous LGE's level predicts better than λ does.* Predicting VD turnout,
every predictor rescaled to the true citywide total so only the relative pattern
is judged (MAE in turnout points):

| Predicting | Previous LGE level | Plan's ratio form | Preceding NPE level |
|---|---|---|---|
| 2021 | **0.0409** | 0.0592 | 0.0657 |
| 2016 | **0.0527** | *(needs 2009 NPE)* | 0.0769 |

Same ordering both cycles. **Like predicts like**: LGE patterns are predicted by
the previous LGE; the ratio form only partially closes the gap because it starts
from an NPE base and corrects toward LGE with λ.

**Decision.** Recorded in §3.3 as a *suggested* change, deliberately weaker than
the §0 correction: two cycles of evidence, and 2021 was Covid-affected. Task #19
scores both forms inside the folds on seat outcome, not VD turnout MAE, before
either is adopted. λ̂ is retained for the citywide level regardless — it implies
0.66 and a 41.7% citywide 2026 turnout, inside §8.2's 38–42%.

**Method note worth keeping.** The rescaling is load-bearing. Without it the
comparison is rigged: a citywide-drift predictor is handed the true 2021 total
while the ratio form must infer the level from 2016's drop-off. Unrescaled, the
ratio form overshoots the citywide level by 25%, because 2021's collapse was far
deeper than 2016's — which is what `w_recency` exists to hedge, and exactly why
it cannot be hedged from a single prior cycle.

### 1.3 The concordance is easier than planned, the ward apportionment harder ✅

The plan anticipated intersecting historic VD shapefiles against 2026 ones. Not
needed: 98.8–100% of each election's VDs persist in the 2026 set under the same
number, and those that do not carry 0.21–0.45% of votes.

The reverse is true for step 5. 181 of 865 VDs straddle a 2026 ward boundary, so
their votes must be split. Assumption A1 asks for registration weighting "wherever
the roll permits" — it does: on the MDB layer `REGPOP` is the VD total and
`WardPop` is the *part's own* registration, reconciling exactly for all 865 VDs
(grand total 2,348,781). This also correctly zero-weights **59 sliver parts**
holding no registered voters, which area weighting would have given real vote
share.

### 1.4 Two of the plan's four bloc transitions are confirmed ✅

From the party crosswalk, on the PR ballot: 2014→2016 gives ANC bloc −6.6 / DA
bloc +6.1 against the plan's cited −6 / +6; 2019→2021 gives −21.1 / +13.9
against −22 / +13.

### 1.5 §3.4(b) pairs binary logit with softmax, which is inconsistent ✅

**What the plan says.** Work in logit space, then "softmax renormalisation"
within each VD.

**Why that is wrong.** `logit(p) = log(p/(1−p))` exponentiates to *odds*, so a
softmax over logits normalises odds rather than shares. Odds and shares diverge
as p grows, so the error falls almost entirely on the largest parties. In fold 1
it put the ANC at 54.0% against an actual 44.9% *even though θ had been set to
the exactly-observed citywide ratio* — a 9-point error generated purely by the
renormalisation.

Softmax pairs with multinomial log-shares; binary logit pairs with expit followed
by rescaling.

**Decision.** Use logit → expit → rescale. This keeps the logit semantics
§3.4(b) actually wants (proportional swing where a party is small, additive where
mid-sized, never negative). VD-level MAE fell from 0.93pp to 0.49pp on the
change, and the EFF's citywide error from −5.4pp to +0.02pp.

### 1.6 θ has two incompatible definitions, and §3.5 quotes the wrong one 🟡

Calibrating fold 1 exposed that "θ" can mean two different numbers:

- **raw** — the observed citywide LGE/NPE ratio. This is what §3.5 quotes
  ("Observed: 44.5/52 ≈ 0.86 (2016)"), and fold 1 reproduces it exactly:
  θ_ANC raw = 0.86.
- **calibrated** — the value that reproduces that citywide ratio *through the
  model*, once within-VD renormalisation is accounted for. θ_ANC calibrated =
  **0.79**, θ_DA raw 1.19 against calibrated **1.46**.

Feeding a raw ratio in as if it were calibrated leaves a systematic residual on
the biggest parties — ANC +3.1pp, DA −3.3pp in fold 1 before the fix.

**Decision.** `calibrate_theta()` solves for the model-consistent value by
iterative proportional fitting. Both are reported and written to
`fold1_parameters.csv`. **§3.5's prior ranges are in raw units and cannot be fed
to the model directly** — they need converting, or restating in calibrated units,
before the Monte Carlo uses them. This is a live trap for task #11.

### 1.7 Fold 2: γ transfers across cycles, θ does not ✅

The plan's §4.1 discipline — fit on fold 1, validate on fold 2, never fit both
and report the fit — turns out to separate the two parameters cleanly.

| fold 2 configuration | VD MAE | ward winner | seat MAE | total seat error |
|---|---|---|---|---|
| refit in-sample (reference) | 0.54pp | — | — | — |
| **θ and γ both from fold 1** | 0.60pp | 128/135 | 1.86 | **54** |
| **γ from fold 1, θ recalibrated** | 0.58pp | 128/135 | 0.50 | **12** |

Transferring γ costs almost nothing — VD MAE 0.58 against an in-sample 0.54, and
the ward-winner count is identical either way. Transferring θ costs a great deal:
the seat error more than quadruples.

**Interpretation.** γ is structural — it encodes *where* a party's support sits
relative to its citywide mean, and that geography is stable between cycles. θ is
political weather, and 2014→2016 tells you very little about 2019→2021. This is
strong support for §3.5's treatment of θ as a wide scenario lever rather than a
fitted constant, and it means γ can reasonably be fitted once and reused.

Against §4.3's stated expectation of "±1.5 points MAE on established parties":
fully out-of-sample, the ANC came in at −0.42pp, the IFP −0.90pp, but the DA
+3.08pp and the EFF +2.60pp. So the expectation is roughly right for some and
optimistic for others.

### 1.8 Multiplicative θ cannot create a party from zero 🟡

ActionSA took 18.12% in 2021 from 0.00% in the 2019 baseline. Because θ is
multiplicative, no value of it can produce that — and worse, calibrating θ by IPF
with the entrant missing **silently distorts every other party's θ to absorb the
gap**: the ANC's calibrated θ came out at 0.12 and the DA's at 0.15, values that
look like parameters but are artefacts.

**Decision.** `--entrant CODE=SHARE` seeds a party absent from the baseline at an
assumed citywide share, spatially flat, and lets the rest renormalise around it.
With ActionSA seeded, fold 2's VD MAE drops from 0.94pp to 0.54pp and the θ
values become interpretable again.

**Consequence for 2026.** MK is present in the 2024 base at 12.22%, so it is
*not* this case and multiplicative θ_MK works. But any party that contests 2026
without a 2024 provincial-ballot presence needs an absolute share prior, not a θ.
The PA is a near-miss illustration: 0.03% → 2.96% is a raw θ of 122, which is
technically representable but not meaningfully a "factor".

### 1.9 2026 ward boundaries are a near-total redraw ✅

129 of 135 CoJ wards changed shape for 2026; only 6 are unchanged. Ward *count*
stays 135, confirming §0's 135/270/136 and refuting the press report of 274
seats. Of the 860 VDs common to 2021 and 2026: 640 stay in the same ward, 40
move ward, 180 are split across 2026 wards.

---

## 2. Obstacles and how they were handled

| # | Obstacle | Resolution | Status |
|---|---|---|---|
| O1 | `results.elections.org.za` and `www.elections.org.za` return 403 to curl regardless of UA/referer | Generated *report files* are served straight through and are curl-able; only the SPA shell and bulk zips are gated. Bulk zips fetched by navigating a real browser tab. | ✅ |
| O2 | Browser downloads land in `~/Downloads`, which macOS TCC blocked from the terminal | User granted Full Disk Access. This blocked the project for a full session. | ✅ |
| O3 | By-election reports reachable only via per-session `ReportViewer?_f=<token>` links; tokens fail outside the browser that made them | Bypassed entirely — the by-election *dashboard* is backed by static JSON needing no session, and its per-municipality file is *richer* than the PDF (VD level, all parties, candidate names). | ✅ |
| O4 | Election IDs are not years and differ per ballot | Read off the portal's dropdown. 2019 Provincial is **827**, not 700 — guessing from the National id would have failed silently. Recorded in `SOURCES.md`. | ✅ |
| O5 | 2014 NPE 404s on the results-portal pattern | Published on the other host (`www.elections.org.za/content/Elections/Downloadable-results/...`), found via the portal UI. | ✅ |
| O6 | Historic VD boundaries needed to verify the concordance geometrically | Not published anywhere reachable — checked the MDB's full 43-service ArcGIS list, both DCAT catalogues, ArcGIS Online search, the IEC's GeoServer, and an Internet Archive CDX sweep of both hosts. | 🔴 task #18 |
| O7 | Census 2022 Small Area Layer (income, dwelling, employment) not downloadable | Stats SA supplies on request only. Ward-level product acquired as partial substitute — age/sex/population group, no income or employment. | 🔴 task #16 |
| O8 | IEC publishes registration by age/sex only to municipality level, server-rendered, no API | VD-level registration *totals* come from the result files and the VD layer. Ward-level age/sex substituted from the census product. | 🟡 |
| O9 | 2026 registration-weekend deltas not published | Nothing to do but wait; §3.2 feeds them in when available. | 🔴 external |
| O10 | Sources disappear — the MDB has already retired the per-municipality shapefile downloads its old site served | `src/archive.py` records every file with SHA-256 and provenance; the manifest is committed even though `data/` is gitignored. `--verify` detects drift. | ✅ |

---

## 3. Data traps found (each corrupts silently rather than erroring)

| Trap | Where | Handling |
|---|---|---|
| Unquoted commas in voting-station names shift every later column, **while row width stays constant** because a trailing pad column absorbs it | 2019 NPE, e.g. JHB VD 32851278 `TENT (TSUTSUMANE, EXT 7 )` | Rows anchored at both ends, not by position. A column-count check does *not* catch this. |
| Encoding drift | 2019 is DOS CP850 (`CAF\x90` = CAFÉ), 2011 is UTF-16, rest UTF-8 | BOM check, then decode-probe |
| Header drift and a volatile `Generated Datetime: <timestamp>` header | across years | header normalisation |
| `VALID VOTES` / `TotalValidVotes` is the *party's* votes, not the VD total | 2014 NPE and all LGE files | VD total recomputed by summing parties |
| Initials-derived party codes collide | `ARISE SOUTH AFRICA` → `ASA` merged into ActionSA; `ALLIED MOVEMENT FOR CHANGE` → `AMC` merged into `AFRICAN MOVEMENT CONGRESS` | Derived codes are now full names; the builder *fails* on any merge via a derived code |
| Comparing station names against a file that has none flags everything | 2014 bulk carries no station names, so every 2011/2014 VD flagged as changed | compare only when both sides name a station |
| `REGPOP` on the 2026 VD layer is a **2024** snapshot (sums to 2,348,781) | boundary layer | documented; do not read as current registration |

---

## 4. Assumption and mitigation register

The model's live risks, and what is being done about each.

### R1 — VD boundary stability ✅ *tested in fold 2, immaterial*

**Resolved empirically (task #17).** Fold 2 was run three ways — all VDs, the 93
flagged VDs down-weighted at `w_split` 0.6, and those VDs excluded outright:

| | ward winner | seat MAE | total seat error | θ_ANC |
|---|---|---|---|---|
| all VDs | 128/135 | 0.50 | 12 | 1.32 |
| suspect down-weighted | 129/135 | 0.50 | 12 | 1.32 |
| suspect excluded | 127/134 | 0.43 | 10 | 1.30 |

Citywide party errors are identical to 0.01pp across all three, θ moves by at
most 0.03, and the ward-winner count moves by one either way. **The assumption is
not doing meaningful work**, so the missing historic VD boundaries (task #18) do
not block any conclusion the model draws. Task #18 stays open as a nice-to-have,
downgraded from a blocker.

The flags themselves are retained — they cost nothing and would catch a future
delimitation that *did* move VDs materially.

*Original entry, kept for the reasoning:*

### R1(prior) — why this looked like the highest residual risk 🟡

**Assumption.** A VD keeping its number kept its catchment, so historic votes
describe the same ground as the 2026 VD they are matched to.

**Why it may fail.** When a VD splits, one child conventionally keeps the
parent's number over a *smaller* area. An unchanged number can hide a changed
catchment. This cannot be checked geometrically — no historic VD boundaries are
published (O6).

**Evidence for.** Two independent proxies. Registration tracks the citywide
trend (median per-VD ratio 0.97–0.99; only 0–2 VDs per transition lose >30%
relative, where routine carve-ups would leave a fat left tail). And ~90% of VDs
keep the same voting station between consecutive elections, 99.1% for 2024→2026.

**Mitigation in place.** Every VD carries a `stability` flag (registration drift
>30% against citywide, or changed voting station), putting 2.8–13.1% of votes per
election under suspicion. Suspect VDs can be down-weighted via `w_split`.

**Mitigation outstanding.** Task #17: run fold 2 three ways — all VDs, suspect
down-weighted, suspect excluded — and compare θ. If estimates move materially the
assumption is doing real work and boundaries must be sourced (task #18). If they
barely move, the assumption is *tested* rather than hoped.

**Exposure is asymmetric.** The risk falls on the backtest folds, which compare
VD shares across time. The 2026 projection is much less exposed, because the 2026
VD set *is* the 2024 set.

### R2 — Which turnout specification 🟡

Covered in 1.2. Mitigation: task #19 scores both forms in the folds on seat
outcome. λ̂ retained for the citywide level either way.

### R3 — Within-VD homogeneity when apportioning split VDs 🟡

**Assumption (A1).** A VD's vote shares are uniform across its ward parts.

**Why it may fail.** Ward boundaries often follow the socioeconomic gradients
that predict voting, so a split VD's parts may genuinely differ.

**Mitigation in place.** Apportionment is weighted by *registered voters* per
part, not area, which is what A1 itself asks for; 59 zero-voter slivers correctly
get zero weight. Split-derived observations are flagged for `w_split`
down-weighting. Affects 181 of 865 VDs.

**Residual.** Registration weighting fixes the *size* of each part, not
differences in political composition between them. Irreducible without
sub-VD data.

### R4 — Missing covariates for the turnout sub-model 🔴

Income, dwelling type and employment are unavailable (O7). The turnout
sub-model can be built on age/sex/population group and refined later. Ward-level
rather than small-area granularity also limits the covariate term's resolution.

### R5 — Concordance leakage 🟡 *small and quantified*

0.21–0.45% of each election's votes sit in VDs that no longer exist (mostly tents
and temporary stations). Recorded as `method='unmatched'` rather than dropped, so
the loss stays visible downstream instead of becoming a silent shortfall.

### R7 — New-entrant blindness 🟡 *structural, quantified in fold 1*

**The problem.** §4.3 warns that new parties are where the model has no
information. Fold 1 measures it. Every established party's citywide share is
reproduced to within 0.03pp, ward winners are called correctly in 132 of 135
wards, and seat MAE is 0.71 — but the model misses **the AIC entirely (4 actual
seats, 0 predicted)** and Al Jama-ah (1 actual, 0 predicted), because both polled
0.00% in the 2014 baseline. It also invents single seats for six minor parties
that faded.

Total absolute seat error is 12, of which 5 is new-entrant blindness and most of
the rest is small-party churn in the largest-remainder tail.

**Why this matters more for 2026 than the headline suggests.** Every fold
contains a new entrant, and so does the live case (MK). §4.3's point stands and
is now measured rather than asserted: the model is near-exact on parties it has
seen and blind to those it has not.

**Mitigation.** θ for new entrants is a pure prior and must be treated as a
scenario lever, not an estimate. §4.3's conclusion — that the honest output is a
distribution over coalition viability rather than a seat forecast — is the right
response to this, and fold 1 supports it.

### R6 — Single-cycle inference 🟡

Several parameters rest on two observed NPE→LGE transitions, one of which (2021)
was Covid-affected and anomalously deep. `w_recency` exists to hedge this but
cannot be calibrated from one prior cycle. Treat 2021-derived defaults as scenario
levers, not estimates — which is what §3.5 already says, and the turnout work
confirms was wise.

---

## 5. Decisions taken

| Decision | Rationale |
|---|---|
| Keep canonical party code separate from modelling bloc | Seat allocation needs every party's identity — the IFP, VF+, ACDP and AIC all won CoJ seats in 2021. `OTHER` means "not separately modelled", never "discarded". |
| Derived party codes are full names, not initials | Initials collided and silently merged distinct parties. Verbosity costs nothing for residual-bucket parties; collisions cost a lot. |
| Merging raw party strings is only valid when explicit | The crosswalk builder fails on any merge that happens through a derived code. |
| Concordance keys on VD number, not geometry | 98.8–100% coverage, <0.5% leakage, and no historic geometry exists to intersect against. Risk carried as R1 with flags. |
| Apportion split VDs by registered voters, not area | A1 asks for it, the data permits it, and it correctly zero-weights 59 slivers. |
| Turnout defined as votes cast / registered, higher ballot at an LGE | MEC7 is not published per VD. Runs ~0.05pp below the IEC's published figure; λ is a ratio so a consistent bias largely divides out. Consistency across elections beats matching the headline. |
| Unmatched VDs recorded, not dropped | A silent shortfall is worse than a visible one. |
| Archive manifest committed though data is gitignored | Sources are not durable (O10). |
| §0 treated as a correction, §3.3 as a suggestion | §0 is verified against the IEC's own arithmetic three times over; §3.3 rests on two cycles, one anomalous. Different evidence, different confidence. |

---

## 6. What still needs a person

- **Task #16** — request Census 2022 Small Area Layer from Stats SA
  (`info@statssa.gov.za`, +27 12 310 8600).
- **Task #18** — request historic VD boundaries from the IEC Delimitation
  Directorate. Would convert R1 from mitigated to resolved.
- **External** — 2026 registration-weekend figures, when published.
