# Plan to a new live forecast — amended 2026-08-23

**24 days to nomination lists (16 September). 73 days to polling day
(4 November).** Both are hard dates set by the IEC.

This supersedes the earlier plan, which was written when the panel was nine
city-years and the model list was believed closed. Four things have changed
since and each moves an item:

* **The panel is sixteen city-years** (§1.70) and one effective cycle became
  two. `ITERATING.md`'s "when to stop" section rests on the old premise and is
  obsolete.
* **Six raw inputs went missing and came back** (§1.75–§1.79). Everything
  derived in a four-hour window on 22 August was re-run; the guard that would
  have caught it now exists and runs.
* **The acceptance bar is amended** (2026-08-23, owner): paired and
  cycle-replicated, calibration as an untradeable floor, derivedness priced in
  seats against a budget that never refills.
* **The θ-record question is settled** (§1.82). Recency is refuted on
  forward-validated evidence; the 2009→2011 transition is the defect; the
  footprint and the party-event descriptions **interfere** rather than sum.

---

## The single decision this plan turns on

**The model's STRUCTURE is validated. The 2026 CONFIGURATION is not the thing
that was validated, and the difference must lead the published page.**

The structure is in good shape: **12 wins, 2 losses, 2 ties against uniform
swing across sixteen city-years — 7-1 on the 2016 cycle, 5-1-2 on the 2021 one.**
It replicates across two genuinely different elections, which is exactly what
the amended bar asks of any candidate. (It loses at Tshwane 2016 and Mangaung
2021; quote the split, not the pool.)

**But 384 is not a statement about the forecast being shipped**, and an earlier
draft of this plan wrongly treated it as one. The panel scores a configuration
that differs from the 4 November one in three ways, in both directions, and no
backtest can score any of them:

* **A 48-seat channel the panel scores is DARK at 2026.** The arrivals poll path
  **SUPERSEDED 2026-08-25 (§1.94): re-measured on sixteen city-years the poll channel is worth −6 coherent seats, not +48 — turning it OFF is better. The reversal is not the panel: on §1.65's own nine city-years it measures −4. Do not quote 48.** ~~— measured at 48 coherent seats (§1.65) — requires~~ a national-scope poll, and
  the register holds none for 2026. The backtest earned part of its margin from
  a channel that will be switched off on polling day.
* **A channel that decides the 2026 headline is UNSCORED by any panel.** The
  metro poll path fires at exactly one backtest city-year and is worth 2 seats
  there. Nothing in the panel scores a single unreplicated house deciding a
  metro — which is what happens at 2026.
* **Nine typed constants are live at 2026 and inert in every backtest** — the
  `w_bye` family and five poll levers. `JUDGEMENT-CALLS.md` §G says the panel
  cannot bound them *even in principle*.

That is not a reason to delay. It is the reason **A2 governs the headline rather
than sitting in a caveat box.**

So every modelling item below is optional and every publishing item is not.
**The plan is ordered by deadline, not by interest.** Model freeze **8
September**; documentation and re-scoring freeze **14 September**.

---

## Track A — publish (not optional, dated, owns the critical path)

### A1. Stage-1 forecast, frozen and hashed, BEFORE 16 September ★ blocking

`PUBLISHING-BACKLOG.md` §5c. A forecast issued *before* the nomination lists is
the only one that can later be shown to have been a forecast rather than a
retrodiction. It already runs. It needs: a frozen artefact, a published hash, a
date, and a statement of what it does and does not know.

**This is model work in disguise and it decays to zero value on 16 September.**
Do it first.

### A2. Say what the poll channel is doing, in public ★ blocking

The largest single risk to the November forecast, and it is not in the θ record.

* `polls.json` holds **four** 2026 entries — two SRF/Victory Research metro
  waves (n=504, n=503), a DA internal with no sample size, and an Ipsos
  metro-aggregate. Effective house count is **1.0**.
* **One house flips the Johannesburg lead**: polls off gives ANC 68 / DA 65;
  polls on gives DA 78 / ANC 63.
* ~~The DA sits exactly on the `poll_house_k` cap (w = 0.50)~~ — **NO LONGER
  TRUE from 2026-08-24 (§1.91).** The cap is deleted with the adoption of the
  two-term σ; `poll_house_k` is inert on the shipped path. What bounds one
  house now is `polling.house_ceiling`, which is derived rather than chosen.
  Measured on the shipped register: DA σ **5.057pp** against a floor of
  **4.595pp**, and the DA's blend weight is **0.484 by arithmetic** where the
  cap pinned it at exactly 0.500. The 2026 forecast moves about a seat under
  the change (DA 79 → 78, ANC 63 → 64, ASA 24 → 25), so **the two seat figures
  above still stand to within a seat** — the dependence on one house is
  unchanged in magnitude, and what changed is that it is now arguable rather
  than typed.

**Publish the poll-off / poll-on split beside the headline.** It is cheap,
honest, and forecloses the criticism that will otherwise land hardest.

**Blocking checklist item, not a footnote: every figure above must be RE-DERIVED
on the settled tree before it goes on a page.** The seat numbers come from a run
neither this plan nor the review reproduced. The *preconditions* are confirmed —
four 2026 polls, none national, `montecarlo.py`'s national-scope gate on the
arrivals path — the seat movements are not.

**And A2 governs the headline.** It covers all three configuration differences
named at the top of this plan, not only the metro poll: the dark 48-seat channel,
the unreplicated house, and the nine constants live at 2026 that no backtest can
bound.

**Two more things A2 must publish, both added on review and both blocking:**

* **The half-life band, beside the poll-off/poll-on split.** `poll_half_life_days`
  is now reachable (§1.84) and nobody has chosen its value — the register calls
  it DECLARED, *"no SA metro series can fit it"*. And in THIS forecast it is not
  "how fast opinion drifts": the two admitted polls are two waves of the same
  house five months apart, with the **ANC falling 30% → 18%**, so the lever is
  arbitrating a twelve-point intra-house discontinuity with no second house to
  say which wave is right. At 120 days the model believes roughly 70% July /
  30% March. **Publish what the polls do AND what our choice about which wave to
  believe does** — two numbers, not one. A hostile reader will construct the
  second one otherwise.
* **The second house we declined.** `ipsos-w2-2025-metros` (ANC 35%, DA 25%)
  passes `polling.screen` and is discarded by a `scope == "metro"` filter
  because it is a `metro-aggregate`. Including it moves ANC +2.65pp, DA −3.18pp
  and takes H_eff from **1.00 to 1.46** (§1.85). Excluding it is defensible; the
  decision being unregistered is not. **A2 cannot print "one house" without
  printing the reading it declined and the reason.**

### A3. Chase one national 2026 poll ★ start now, long lead time

**SUPERSEDED 2026-08-25 (§1.94): re-measured on sixteen city-years the poll channel is worth −6 coherent seats, not +48 — turning it OFF is better. The reversal is not the panel: on §1.65's own nine city-years it measures −4. Do not quote 48.** ~~The arrivals poll path is **worth 48 coherent seats** (§1.65)~~ and **cannot fire
at 2026** — not for want of code, but because no national 2026 poll is in the
register. One acquisition re-enables the whole channel. This has external lead
time, so it starts today and runs in parallel with everything else.

**Adding SRF's national wave does NOT reduce one-house exposure — it extends the
same house into a second channel.** Today SRF sets the metro centre; add its
national reading and SRF also drives the arrivals path, for the same election,
from the same fieldwork. The two channels will then agree, and nothing in the
model records that the agreement is not independent evidence — `effective_houses`
counts houses *within* a channel and cannot see across them. SRF national is
DA 27% / ANC 34% against 2024 actual DA 21.81% / ANC 40.18%.

**CORRECTED 2026-08-24 (§1.91): acquiring a poll is NECESSARY AND NOT
SUFFICIENT.** The arrivals channel is blocked at 2026 by **two** independent
gates. The second is that `contesting_parties(joburg, 2026)` returns **zero
parties** — the roster is the nomination fact and the lists do not exist until
**16 September**. The loop skips every party against an empty roster, so **the
48-seat channel cannot fire before the lists land, whatever poll is acquired.**
Acquire the poll anyway, on its lead time; but book its benefit to 16 September,
not to the acquisition.

**Still add it** — a dark 48-seat channel is the worse error — but declare the
shared provenance, and let A2 say the true sentence: *one house sets the metro
centre, the same house sets the arrivals path, and there is no second house
anywhere in the 2026 Johannesburg forecast.*

**Do NOT add the Tshwane / eThekwini / Ekurhuleni metro readings before
November.** They raise H_eff for those metros only, and Johannesburg is the city
being published. Post-4-November work.

**Reconcile `ipsos-2021-lge-national` BEFORE the 8 September freeze.** The
register carries n=1,501; Ipsos's October 2021 release is n=1,346. That poll is
**in the backtest** and drives the arrivals path at 2021, so if the register
holds the wrong release a panel number moves — and it moves *after* the freeze if
this is left. It is the only poll-register item with a backtest consequence.

**And pre-register the poll-admission rule NOW, before any new poll exists** —
which houses are admissible, and what a second house is worth at H=2 —
measured under the two-term σ as 0.518 → 0.533 on the synthetic fixture, all of
it the halving of σ_idio, because σ_common is common (§1.92). `poll_house_k`
and its cap are retired and are no longer the thing to pre-register. Seven weeks of campaign sit between the lists and polling day and SRF will
publish again. A rule written after seeing the next wave is not a rule.

### A4. Rebuild the live pages ★ blocking, and badly under-scoped in the first draft

**This is the only place in the project currently publishing numbers it cannot
reproduce**, and the first draft filed it as routine.

`site/index.html` (17 August) carries a fact-check of Helen Zille's 490,000-voter
claim in which **eleven `mode="fixed"` stat tokens** — `claim_short_by` 39 seats,
`claim_da_median` 97, `claim_anc_wards_surged` 62, `claim_poll_surged` 1,290,000
and the rest — are each sourced to `run:turnout_tilt_da=1`, **a lever `run_model`
no longer has**. `content/joburg/stats.toml` already carries the warning, dated
2026-08-17: *"They are not wrong; they are unauditable, which for this project is
the same thing."* Because the tokens are `fixed`, the drift audit is **silent by
construction** — it cannot report a token it is told not to recompute.

The fix is a **content decision**, not a build step: either re-express the
scenario through the per-pool turnout bands, or retire the claim section. It
cannot be done in the hour before a deploy. **Decide it this week.**

Also: the site is rebuilt *from* `history.md`, so the generator fixes of
2026-08-23 must land first.

Rule: **never type a model figure into prose** — register it as a stat token and
let `build_site.py` audit it.

### A5. Nomination lists, 16 September

Dated and mechanical. Retires `contestation_expand`, makes contestation live,
and withdraws the phantom entrant mass. Then re-run, re-score, and publish the
revision under §5c's stated rule.

**Decide the rollback rule NOW, before the lists land.** §5c predicts the lists
are worth about ±3 seats to the PA and ∓2 to the DA. If the real lists move the
forecast by twenty, §5c's reporting rule does not cover it — it assumes the
movement lands inside the published band. **This is the only genuinely
out-of-sample test `contestation_expand` will ever get**, and choosing how to
report it after seeing the result is exactly what pre-registration exists to
prevent.

### A6. The seven weeks between the lists and polling day ★ missing from the first draft

16 September to 4 November is the window in which an unstructured decision is
most likely, and the first draft simply stopped at A5. Fix now:

* **an update cadence** — how often the forecast is re-run and republished;
* **a final-revision cutoff** — the date after which nothing changes but the
  clock;
* **the poll-admission rule from A3**, in force and published.

---

## Track C — the audit's residue (2026-08-23, four parallel audits, §1.84)

The repository was searched exhaustively for the first time. Two live bugs were
found and fixed in the same commit; what follows is what the audits found and the
fix commit deliberately did **not** do. **C1 and C2 are blocking — they are
correctness, not tidiness.**

### C1. The register's guard is structurally blind ★ blocking, and FIRST in the whole plan

**The reason is not "correctness not tidiness" — it is a dependency.** Key 3 of
the amended bar computes Derivedness Debt *from the register*. A register blind
to default arguments, inline literals, argparse defaults and TOML does not
produce `D`; it produces `D` over 53 of the names that matter. So **C1 blocks
B2, and B2 is the input to A2's disclosure.** That chain makes this the first
item in the document, ahead of everything.

`test_every_tunable_constant_is_in_the_judgement_register` inspects **53 names**:
top-level `ast.Assign`, single target, UPPERCASE, literal int/float. It cannot
see numeric **default arguments** (the `LEVEL_DF` shape — three instances now,
the latest costing 5.6pp of ANC in the live forecast), **dataclass fields**,
**dict-valued** constants, **lowercase** constants, **inline literals**,
**argparse defaults**, or any number in a **TOML** file.

Everything in C2 was reachable because of this. **Widen the guard before
registering anything**, or the register will keep certifying a model it cannot
see.

### C2. Unregistered constants that decide real things ★ blocking

* **`overhang_rule = "deduct"`** — a legal interpretation that sets council size
  and the majority threshold. Four regimes give four different answers. Skipped
  by the guard because it is a *string*.
* **`w_recency = 0.70`, `kappa_bye = 0.25`** (`turnout.py` argparse defaults) and
  **`--w-split = 0.6`** (`fold.py`) — verbatim from the original plan §3.5, whose
  own text asks for a fold-2 sensitivity test that `MODEL-LOG` never records.
  They reach the model through **20 committed `turnout.csv` files with no
  artefact key**, so changing the constant changes nothing until someone re-runs
  the script and *nothing announces the mismatch*.
* **`GAMMA_FOLD`**, **`PLAN_BOUNDS`**, and the γ fallback of `1.0` — which is
  `np.ones(npar)`, not a literal, so no scan of any kind can see it.
* **`config/dimensions.toml`**: `extrapolation_damping = 0.6`,
  `extrapolation_max_years = 8`, and **`min_oos_gain = 0.01`** — the bar that
  decides which census dimensions exist at all. Age and sex are *rejected* by
  that number. `dimensions.toml` is not mentioned in the register once.
* **Nine arrival-path constants** inline in `pools.py`, on the path §1.65 prices
  **SUPERSEDED 2026-08-25 (§1.94): re-measured on sixteen city-years the poll channel is worth −6 coherent seats, not +48 — turning it OFF is better. The reversal is not the panel: on §1.65's own nine city-years it measures −4. Do not quote 48.** ~~at 48 coherent seats — including the comparator window~~ `abs(r - reach) < 0.25`
  and the no-record turnout band `(0.30, 0.50, 0.70)`.

### C3. Six of eight metros run with the θ clamp absent ★ blocking for DISCLOSURE

Not merely "untested". Four of the sixteen panel city-years (Johannesburg ×2,
Tshwane ×2) run with the θ clamp **active**; twelve run **without** it. So the
**384 figure is a mixture of two model configurations.** It invalidates no A/B
comparison — both arms share it — but it changes what "the model" means, and it
must be disclosed. Either give all eight cities the same bounds, or record the
heterogeneity in `history.md`.

`PLAN_BOUNDS` comes from `[judgements.plan_bounds]`, and six metros have no
`[judgements]` section at all — so `apply_city` sets it to `{}`, the clamp does
not apply, and the bounds-violation diagnostic reports zero. **The panel cannot
test that constant and does not say so.**

### C4. Stale artefacts wired to live outputs ★ blocking, and it belongs inside A4

**The general rule nobody had stated: `mode = "free"` is NOT a freshness
guarantee.** `anc_entitlement` is a *free* token — it resolves at build time —
but its source is `regime:cap:...`, i.e. the frozen `regime_cap_summary.json`.
A free token whose source is a derived artefact inherits that artefact's date,
and `stats.py` checks none of them. The drift report correctly reports no drift,
because a frozen file cannot drift.

The free/fixed distinction is this project's headline provenance claim, and A4 is
about to rebuild the page and re-derive every free token — producing a page that
**looks freshly audited and is not.** Sequence it: **C6 → C4 → A4.**

* **`regime_cap_summary.json` feeds a published stat token** (`anc_entitlement`,
  used twice on the front page) and was produced on **7 August by a model that
  still had `turnout_tilt_da` in it** — the exact lever `CLAUDE.md` names as
  having put ten unauditable claims on the page. `stats.py` applies **no
  freshness check to a source file**: the drift audit catches typed figures and
  cannot see a stale source.
* **`forecast_summary.json`'s provenance is partial, not absent.** *(Corrected
  on review — the first draft said "no provenance at all" and that is wrong.)*
  Its `scenario` block does carry `_pools_artefact_key`, `_pools_stale` and
  `_constants_read`. What it lacks is **city, target, timestamp and a code
  hash**, so nothing can answer "was this produced by the current tree?" The
  gap is smaller than stated and belongs inside **A1**, whose whole job is to
  hash and freeze a forecast.
* **`gamma_recent.csv` exists for 5 of 18 city-year directories.** Most of the
  panel falls silently to γ = 1.0 where Johannesburg takes a measured value —
  a cross-city asymmetry in a model input, not a cosmetic one.

### C5. Latent breaks for any non-Johannesburg run

`vd_ward_<year>.csv` and `vd_concordance.csv` are **written at city level and
read at target level** — 14 files unreadable where they sit — and `fold.py`
hardcodes Johannesburg's concordance for every city. Joburg 2026 masks all of it.
**This binds the moment the portal runs a second city**, which is what
`EXPANSION.md` was for.

### C6. `build_all.py` cannot reach `build_site` or `build_portal` ★ blocking A4

`build_interactive.py` raises at module level (deliberately, correctly) and the
runner treats any non-zero return as fatal, so the documented one-command build
has been severed — and with it the only path that runs the stat-provenance
guards. They now execute only when a human invokes `build_site.py` by hand.
**Fix before A4.**

---

## Track B — model (all optional, all timeboxed, all behind the freeze)

### B1. Type A routing — the one modelling item worth opening

§1.74's own conclusion, confirmed by §1.82: **route, do not drop.**

The 2009→2011 transition is contaminated by party-structural events and accounts
for ~18 of §1.70's 26 seats (§1.78: nine 280→262, sixteen 384→360, CRPS
329.4→320.3). But an *exclusion* moves that volatility out of the model's prior
and into its error — §1.74 measured `sd_for` at 5–15% falling 0.203 → 0.150 with
the filter on while the measured dispersion stayed at 0.839, worsening the ratio
from 4.24× to 5.58×.

So route the volatility into the **width**, through the splinter and arrivals
machinery that already exists, instead of letting it vanish.

**Half the first draft's live-forecast justification was wrong, and the review
checked it.** `levels.TYPE_A_EVENTS` has keys `2011`, `2016`, `2021` and **no
2026 row** — nor should it under the register's own coding rules: the 2026
transition is 2024 NPE → 2026 LGE, MK contested 2024 so it exists at both ends,
the ANC schism pre-dates the base, and the PA is explicitly excluded as Type B.
**Under its own rules the register flags nothing at 2026.** So B1's 2026 benefit
comes through the *drop* half — a `sd_for` no longer inflated by 2009→2011 — and
the routing half is inert there unless a 2026 row is added and labelled as a live
judgement no backtest can score.

### What "route, do not drop" means mechanically

Four components, and the fourth is what makes it work:

1. **Carry the event on the observation.** `theta_record` emits
   `(ratio, share)`; emit `(ratio, share, event)`. Zero free parameters — the
   register is exogenous and already written.
2. **Fit `mu_all`, `size_centre` and `sd_for` on Type B only.** This is the drop,
   and §1.74 already measured it.
3. **Estimate the event component from the observations just removed** —
   `(mu_class, sd_class)` per class, pooled where n is 1–2 **and said so**.
   §1.71 gives the material: 0.942 with events, 0.244 without. **The CENTRE must
   move too, not only the width** — `MERGER_ABSORBED` has E[log θ] > 0 (DA
   1.378–1.577), `SPLIT_PARENT` < 0 (IFP 0.465), `POST_FORMATION_COLLAPSE` ≪ 0
   (COPE 0.115–0.282). Routing width alone leaves the model unbiased-and-wide on
   exactly the parties it most needs to be right about. **This is the component
   most likely to be got wrong.**
4. **Apply it as a BASE-RATE MIXTURE, not a per-party flag.** Every party draws
   from the event distribution with probability `p_event` and from Type B
   otherwise, where `p_event` is the observed rate of Type A party-transitions in
   the record (to be computed, with an interval). This is the design decision: it
   means the model **cannot become narrower** — the §1.72-predicted, §1.74-measured
   failure — it works at 2026 **with no 2026 register row**, it makes the prior
   heavier-tailed as the external review separately recommends, and it introduces
   **zero typed constants**, so it is neutral-to-positive on Key 3.

**Prerequisite, not a separate item: fix `sd_for`'s covariate (was B4).** Every
observation of a party shares one x-value taken at the **target**, while
`_reliability` weights by the **base** share. COPE at 7.4% of the 2009 base and
near zero later lands at the small-party end of the size axis where the slope is
steepest — a plausible mechanism for why one contaminated transition moves the
whole dispersion curve. Confirmed in the code by the review.

### Gate it with an afternoon, not a week

The sensitive instrument is `theta_residual`'s held-out NLL: it runs on a fit
rather than 1500 draws, touches no `pools_*.json`, and sits on **18 clusters
rather than 2**.

> **Pre-register, then measure held-out NLL on both folds FIRST. If it does not
> improve at both 2016 and 2021, stop.**

Bare Type A fails that gate today (2016: 0.7531 → 0.8611). A correct mixture
should pass it, because the 2016 fold's held-out set contains AGANG and
MINORITY_FRONT — precisely the observations a Type-B-only prior assigns near-zero
density to. **That turns B1 from "a week that might not land" into "an afternoon
gate, then a week only if it passes."**

Pre-register per §1.80. Judge under the amended bar, Key 4 included. **Model
freeze 8 September.**

### B2. Sweep the nineteen never-swept constants ★ DO THIS FIRST in Track B

Filed as a chore in the first draft. It is **risk management**, and it belongs
this week.

It is the only measurement that says **how much of the November forecast is
decided by typed constants**. With the arrivals poll path dark, 2026's entrant
handling rests on `entrant_prob = 0.25`, `ARRIVAL_BAND_LO/HI` and the
never-swept `ALPHA_*` family that feeds *83–98% of drawn variance*. That is the
second-largest live risk after the poll channel and the first draft did not name
it as a risk at all.

One afternoon, changes no forecast, and it is the derivedness ledger's first
entry — nineteen "unknown" register rows become nineteen numbers. **Publish the
result as part of A2.**

### B3. Separate the width channel from the centre channel

Never measured. Adding the pre-2011 archive changed both the θ centre and
`sd_for`; §1.74's dispersion movement suggests the width channel does the work.
One arm with the new observations feeding the centre and `sd_for` frozen, one
the reverse. If the width arm carries most of the 26, the fix is in `sd_for`'s
specification, not in the record's membership.

### B4. The by-election half-life, confirmed

`byelections.py` applies `exp(-age/tau)` with `tau = 18.0` and help text calling
it a *"recency half-life in months"*. That is a **mean lifetime**: the actual
half-life is 18·ln2 ≈ **12.5 months**. `montecarlo.py` carries the same 18.0 as
`bye_tau_months`, and `polling.py` does the equivalent conversion correctly.

**Inert today** — `w_bye_local_ward` and `w_bye_local_pr` are both 0.0 — and
**wrong the day either is switched on**, which is a 2026-live path. Fix the
naming or the arithmetic, and say which. Cheap.

*(The `sd_for` covariate defect that was the other half of this item has moved
into B1, where it is a prerequisite rather than an option.)*

### B5. Ingest the five held `lge2000` archives — **AFTER 4 NOVEMBER**

Data already on disk with `MUNI_HEAD` keys written (§1.79), and `ITERATING.md`
says the only thing licensing a restart is **more independent clusters**, which
this is.

**Moved out of the live window on review.** The first draft scheduled it between
the lists landing and polling day — on the very tree that must produce the
published revision, moving every number. §1.79 says it *"moves every number here,
so it is a measurement to be run deliberately"*, and §1.75 is the entry about
what happens when the archive shifts under a live artefact. Its value is more
clusters for the *next* iteration and it has **no November deadline at all.**

---

## Explicitly NOT doing before November, with reasons

* **A recency decay or date cutoff on the θ record.** Refuted (§1.82): held-out
  NLL is non-monotone in the age of the record, and the premise offered for it
  was false in the code.
* **Re-measuring `TURNOUT_CORRELATION`, `SPLINTER_PARENT_WEIGHT` or
  `SPLIT_SD_FLOOR` against the present record.** It would bake the 2009→2011
  contamination into three more constants.
* **The ward-level upset mechanism.** Real, diagnosed, no measured prize.
* **The tail (ranks 13+).** 33 of 2,960 seats — 1.1% — and the obvious fix was
  measured at 14–22 seats. The bias is carried on the record, deliberately.
* **`dirichlet_scale`.** Measured as a trade; fails Key 1 and buys nothing on
  Key 3.
* **The publishing revamp** — the interactive port, the fidelity gate, the
  sliders. Correctly separated, and its own order-of-work says "close the model
  list" first. **Exception: §5c stage 1, which is A1 above.**

---

## Sequencing, and the two hard rules

```
now ─────────► 27 Aug ────────► 8 Sep ──────► 14 Sep ──► 16 Sep ────────► 4 Nov ──────►
 A1 freeze+hash  GO/NO-GO       model         docs        lists land      polling
 A2 headline     on Track B     freeze        freeze      A5 re-run       A6 cadence
 A4 decide Zille                                          + rollback rule  in force
 A3 chase a poll + admission rule
 B2 sweep (this week)
 B1 NLL gate ──► B1 build only if the gate passes
                                                                          B5 lge2000
```

**Rule 1 — one writer on `pools_*.json`, and nobody measures while it writes.**
B1, B5 and every re-emit touch it. Canonical numbers come from **one settled run
at the end**, and every figure quoted anywhere comes from that run.

**Rule 2 — the go/no-go on Track B is 27 August, not 1 September.** The first
draft checked on 1 September, by which time up to nine days of Track B effort
would already be spent and B1's timebox would straddle the check. **Gate Track B
on A1 and A2 being DONE**, not on a date: freeze and hash the stage-1 forecast,
publish the configuration caveat, then decide.

---

## What would make me abandon Track B entirely

If **A1, A2 and the A4 content decision** are not done by **27 August**, drop
Track B. The model already replicates 12-2-2 against uniform swing across two
cycles, and the marginal seat is worth far less than a published, hashed, honest
forecast that exists before the lists close.

**A4 is the binding constraint** — it needs a content decision on the Zille
section plus a rebuild against a model that has moved, and under this plan's own
rule it blocks Track B.

---

## State C's disposition, stated rather than left on the floor

State C — the footprint exclusion, 384 → 368, CRPS 324.7, replicating 5-0 and
2-1 across cycles — **passes Keys 1 and 2 and FAILS Key 4** (held-out NLL at 2016
0.7531 → 0.9512).

**It does not ship.** Under the amended bar that is now a clean verdict rather
than the §1.81 judgement call it was, and §1.82's interference result says it is
a *worse description of the same defect* B1 addresses, not an independent gain.
If B1 does not land by the freeze, C may be revisited as an interim — **but only
with its NLL result printed beside it.**

An unremarked pass is how the last one got lost.
