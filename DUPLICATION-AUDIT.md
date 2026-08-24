# Duplicated logic — audit, 2026-08-24

**Why this file exists.** `tests/test_polling_synthetic.py::_weight` re-implemented
the model's poll-blend decision. When the two-term σ was adopted the model
changed and the helper did not, so the whole module spent a day measuring a
hybrid the model never runs — the NEW σ against the OLD cap — and reported a
failure that was not real. The owner's instruction, twice: **detailed logic must
not live in two places.**

**The line numbers below are a snapshot of 2026-08-24 and will go stale.**
That is why `JUDGEMENT-CALLS.md` forbids them and `test_register_matches_code`
enforces it — a register is read as current, and this file is dated evidence
for a specific tree. Cite the function, not the line, anywhere else.

Three read-only audits were run over `src/`, `tests/` and the
code/config/docs/site boundary. Findings below are classified by what fixing
them costs, because that determines what may be done immediately.

| class | meaning | may be done |
|---|---|---|
| **N** | number-neutral — extract a shared definition, no arithmetic changes | immediately |
| **M** | fixing it MOVES a forecast number | only pre-registered and measured against the 16-city-year panel |
| **R** | already-wrong copy on a path that is currently inert | fix + record, measure if it becomes live |

---

## The rule this establishes

A second copy is permitted **only** where it is an independent oracle whose
independence is the point (`fold.py` validating the deterministic core;
`test_hex_cartogram.py` restating the closed-form hexagon identities). Every
such copy must say so in its docstring. Everything else imports.

---

## A. On the shipping gate

### A1 — the θ estimator is written four times, and the held-out NLL floor scores a copy  **[M]**

- `src/levels.py:718-729` — `theta_prior`, the definition
- `src/levels.py:819-830` — `_shrunk`, an extracted copy
- `src/theta_residual.py:243-262` — `form_b`
- `src/theta_residual.py:340-355` — `form_c`

All four compute `weight = worth/(worth+SHRINK)` and
`mu = weight·own + (1−weight)·centre(size)`. `theta_prior` carries a comment
claiming the estimators "agree party-for-party rather than merely in form" —
asserted by hand, not enforced by sharing the code.

`ITERATING.md`'s amended bar makes the estimation record's **held-out NLL an
untradeable floor**. That floor is computed at `theta_residual.py:376-398` from
forms A/B/C. `form_a`'s own docstring admits it uses the record's weighted size
where `levels.theta_prior:717` passes the party's size **at the target**. So the
floor is computed from an estimator the model does not run: a change to
`levels.py` moves the model and leaves the gate where it was.

**Fix:** promote the two closures to `levels.sd_from_fit(coef, size)` and
`levels.shrunk_centre(obs, fit, mu_all)`; every form differs only in which
residual it fits, which is what `_fit_line`'s docstring already claims.

### A2 — `theta_prior` and `_shrunk` disagree on the no-record fallback  **[M]**

`theta_prior:731` falls back to `_centre_for(size)` — the **size** centre.
`_shrunk` returns `mu_all`, the **flat** centre, and `spine` uses it
(`levels.py:879`). `theta_prior:688-698` states in terms that the flat centre is
the wrong one and was corrected there; the spine still takes it, and the spine
is what produces the level. The named case is **MK in 2026** — a national vote
and no local election yet.

---

## B. Bugs found by looking for duplication

### B0 — "which polls apply to this city" is decided twice, and the two disagree  **[N]**

The clearest case in the audit, and the one that shows why the rule matters even
when nothing is currently wrong.

- `polling.screen:` — `if poll.get("scope") == "metro" and not poll.get("city")`
- `montecarlo.py:2876-2877` — `[q for q in _screened if q.get("scope") == "metro"
  and q.get("city") == target.city.slug]`

`screen`'s guard is an **exact** match on the string `"metro"`. The register
holds `ipsos-w2-2025-metros` with `scope: "metro-aggregate"` and **no `city`**,
whose own `note` field reads:

> Scope is 'metro-aggregate' so it is NOT applied as a city poll: eight metros
> averaged is not a reading of one of them, and using it as one would import
> Cape Town's DA and eThekwini's MK into Johannesburg.

It passes `screen` — no city check fires, no `target` is declared, and its
fieldwork ends 277 days out, inside the 550-day window. `PG.screen(2026)` admits
it and `PG.aggregate` blends it:

| party | screen's aggregate | Johannesburg polls only | delta |
|---|---|---|---|
| DA | 37.92% | 41.10% | **−3.18pp** |
| ANC | 24.24% | 21.60% | **+2.65pp** |
| ASA | 8.81% | 10.00% | −1.19pp |
| EFF | 8.03% | 6.80% | +1.22pp |
| PA | **4.00%** | 0.00% | +4.00pp |
| IFP | **2.00%** | 0.00% | +2.00pp |

`H_eff` 1.464 against 1.0 — the σ narrows as though a second house had polled
Johannesburg. PA and IFP are conjured into Johannesburg out of Cape and KZN
numbers, exactly as the note predicts.

**It does not reach the forecast.** `montecarlo` re-states the rule inline and
its version is the strict one, so the published numbers are unaffected. That is
the whole point: `screen` is the layer that documents itself as *"Admitted
polls, and every exclusion WITH ITS REASON"*, and it is wrong; the forecast is
saved by a copy of the rule in another module. `test_polling_register.py`
asserts `usable_for` and `screen` agree **with each other**, and nothing asserts
either agrees with what the model uses.

**Fix:** one `polling.for_city(target, polls)`; `montecarlo:2876` calls it; the
`metro-without-city` exclusion becomes "does not name this city" and covers every
scope that is not a single-city reading. Number-neutral by construction — assert
`_metro` is unchanged.

### B1 — the by-election local mean applies the decay twice  **[R]**

`src/montecarlo.py:2513-2516`. `move` is already multiplied by `decay`; the
numerator then accumulates `decay * move`, so it sums `decay²·raw` against a
denominator of `decay`. A single contest yields `decay × raw_move`, not
`raw_move` — and the comment at `:2495-2499` states the opposite invariant and
claims it is "the same mean the citywide term takes in `byelections.py`".

Inert **only** because `w_bye_local_ward` and `w_bye_local_pr` ship at `0.0`.
`montecarlo.py:170-171` names 0.75 and 0.35 as "the value tested", so it has
been exercised in that state.

### B2 — the poll centre and the poll width weight the same polls differently  **[M]**

`polling._recency_weights:293-311` exists, and its docstring says it was
factored out "so the aggregate and `effective_houses` cannot weight the same
polls differently — two copies of one calculation is this repository's most
reliable defect." **`aggregate:799-814` does not call it** and recomputes the
decay inline. The two disagree three ways:

| | `_recency_weights` (σ path) | `aggregate` (the centre) |
|---|---|---|
| date parser | `_end()`, tolerant, returns `None` | `date.fromisoformat`, raises |
| undated poll | weight 0.0, still counted in `H_eff` | dropped entirely |
| default `asof` | newest **dated** poll | newest poll **with `numbers`** |

The centre is the path that moves the published number.

### B3 — `fold.py` allocates a 270-seat chamber for every city  **[R]**

`seats.allocate(combined, total_seats=270)` defaults to Johannesburg's council.
`fold.py:682` and `:700` call it **without** `total_seats`. `backtest.py:533`
and `montecarlo.py:1836` both pass it. Any non-Johannesburg use of `fold.py`
silently scores against the wrong chamber.

### B4 — `PERTURB` sets `turnout_correlation` twice  **[R]**

`tests/test_levers_are_live.py:296` (`0.0`, with the explanatory comment) and
`:307` (`-0.9`). Python keeps the last, so the documented perturbation has never
run. Confirmed by AST walk; it is the only duplicate key in either file.

### B5 — `pools._npe_citywide_for` is a pre-§1.75 copy of `levels._citywide`  **[N]**

`pools.py:2343-2360` duplicates `levels.py:201-226` verbatim (five identical
lines) but **without** the `_absent()` refusal added after twelve transitions
vanished in silence and cost 16 coherent seats. It still returns `{}` for a
missing file. It feeds `arrival_group_record`, so a vanished NPE file drops
metro-years from the arrival record with nothing going red.

---

## C. Constants and identities declared more than once

### C1 — six poll constants exist three times each  **[N]**

`polling` constant → `DEFAULTS` entry → **bare literal at the call site**:

| constant | `polling.py` | `DEFAULTS` | literal |
|---|---|---|---|
| `POLL_MIN_N` 300 | `:261` | `montecarlo:201` | `:2752`, `:2874` |
| `POLL_SCREEN_SD_UNDISCLOSED` 0.020 | `:173` | `:199` | `:2913` |
| `POLL_DRIFT_PP_PER_ROOT_DAY` 0.0010 | `:180` | `:200` | `:2914` |
| `POLL_DEFF_SUBSAMPLE` 1.6 | `:166` | `:198` | `:2916` |
| `POLL_HOUSE_K` 1.0 | `:256` | `:197` | `:2929` |
| `POLL_HALF_LIFE_DAYS` 120.0 | `:268` | `:208` | `:2920`, `:2939` |

The block is inconsistent with itself: `montecarlo:2889` correctly writes
`_pg.POLL_HALF_LIFE_DAYS`; thirty lines later `:2920` writes `120.0`. **Twenty**
`scenario.get(...)` call sites in `montecarlo.py` use a literal fallback and
**none** uses `DEFAULTS[...]`. The existing guard at `montecarlo.py:633-640`
links exactly one of the six.

Same shape: `level_sd_default` 0.45 (`:1485`, `:2899`), `level_shrink_scale`
0.04 (`:1171`), `bye_local_cap` 1.5 (`:2488`), `bye_tau_months` 18.0 (`:2489`
**and** `byelections.py:135`), `poll_paths` "all" (`:2755`, `:2877`).

### C2 — `METRO_CODES` declared twice, already out of order  **[N]**

`levels.py:199` `(JHB TSH CPT ETH EKU MAN NMA BUF)` against
`pools.py:1445` `(JHB TSH EKU ETH CPT MAN NMA BUF)` — CPT and EKU swapped.
Consumers split across both. Today it costs only float summation order; the
exposure is that adding a metro to one leaves the other short, silently.

### C3 — `SHARE_FLOOR` twice, and the two are coupled  **[N]**

`montecarlo.py:85` and `fold.py:93`, both `0.002`, no assert linking them.
`fold.fit_gamma` computes the logit deviations that produce the γ written to
`fold{n}_parameters.csv`, which `run_model:2537` reads and applies through its
own `logit`. If one floor moves, γ is fitted in one deviation space and applied
in another. `benchmarks.py:90` does it correctly (`SHARE_FLOOR = M.SHARE_FLOOR`).

`logit`/`expit` themselves exist three times: `montecarlo:326-334`,
`fold:110-117`, `benchmarks:485-487`.

### C4 — "half-life" names two different formulas  **[N, doc]**

`polling.py:309` divides by `log 2` — a real half-life. `byelections.py:186` and
`montecarlo.py:2489,2512` do not, so `tau` there is a **mean-life**: at τ=18 the
weight is 0.368, not 0.5. Each is internally consistent; the register describes
them as though they were the same quantity.

---

## D. Tests that re-implement the model

### D1 — `build_inputs` copied into two fixtures, both missing three of five spec keys  **[R]**

`tests/test_drawer.py:360-429` and `tests/test_ipf_feasibility.py:79-145` each
rebuild `run_model`'s assembly. `run_model:2148-2152` reads five keys off the
spec; both fixtures read one (`pools`). The missing `pool_seeds` and
`pool_seed_bands` are load-bearing: `blended_centres:1001` never takes the
seeded branch, `make_drawer:1497` always gets `seed_band = None`, and
`run_model:2361-2371` mutates the baseline with the seeds **before** building
the index, which the fixtures do not.

Inert today only because `pools_2026.json` has empty seeds. `pools_2021.json`
carries **32 seeds** including `ASA: 0.0685`. The branch is called
`splinter-rule-and-historical-tail`.

This is the defect the file already records against itself at
`test_drawer.py:310-333` — fixed for the level layer, left for the seed layer.

### D2 — `tests/test_seats.py` copies two `validate_seats.py` functions verbatim  **[N]**

`load_votes` (`test_seats.py:90-99` / `validate_seats.py:29-37`) and
`ward_winners` (`:101-111` / `:40-50`) differ by one word of docstring.
The C/D derivation is duplicated too (`:143-149` / `:81-84`), and the assertion
itself exists in both, with `validate_seats.main` the weaker of the two.

### D3 — `_weight` agrees with the model only at default levers  **[N]**

`tests/test_polling_synthetic.py:61-78` against `montecarlo.py:2913-2941`.
Bit-identical at defaults (σ 0.04338839, w 0.51822721 both sides) — but the
model passes `screen_sd`, `drift_rate`, `deff_subsample` and `half_life_days`
out of the scenario and the helper passes none. At
`--set poll_screen_sd=0.12` (which is `PERTURB`'s own value) the model prices
σ 0.12603 / w 0.1131 and the helper still says 0.04339 / 0.5182.

**Fix:** move the branch into `polling.blend(polls, party, share, model_sd,
scenario)`; both call it. `polling.house_ceiling` is the pattern.

### D4 — `test_chain.py` re-derives `fit_joint`'s objective  **[N]**

`:238-241` against `pools.py:1038-1039`. Agree to 2.2e-19. It is the **only**
test asserting `fit_joint` minimises anything, so if the weighting changed the
test would keep comparing the old objective and still pass.

### D5 — `test_chain.py:391-411` re-implements `fold.load` + `fold.citywide`  **[N]**

Max absolute difference 0.0 over 44 parties. The copy opens without
`newline=""` — the IEC CSV trap the production reader guards against.

### D6 — `test_data_coverage.py:172-176` inlines `archive.digest`  **[N]**

Identical chunked SHA-256. It asserts the manifest matches a column that
`archive.digest` writes, so if the hashing ever changed the test would report
drift on every correctly-rebuilt manifest.

### D7 — `test_regressions.py:302` passes while its stated property is false  **[N]**

It asserts the source line `_w = min(_pg.blend_weight(_psd, _msd), _cap)` is
present, "so the poll weight must stay bounded by `weight_cap`". The line is
present; `_cap` is `1.0` under the shipped switch, so the `min()` bounds
nothing. The same file records learning this exact lesson at `:288-296`, in the
opposite direction.

---

## E. Retired mechanisms still standing beside their replacements  **[N]**

- `weight_cap` (`polling.py:433`) is documented as retired and replaced by
  `sigma_floor`/`house_ceiling`, but `montecarlo.py:2927` still calls it behind
  the switch and `test_regressions.py:302` asserts its call site exists.
- `poll_sd`/`sd_components` (`polling.py:369-402`) still compute the retired
  four-component σ unconditionally, and `test_polling_sd.py:72-78` uses
  `poll_sd` for the calibration self-consistency check that `polling.py:152-154`
  advertises as the guard on the decomposition. **That check now guards a path
  the model does not take.**
- `tests/test_polling_sd.py:138` tests `weight_cap`'s monotonicity and passes
  while guarding nothing the forecast uses.
- The sampling term is written three times inside `polling.py` alone
  (`:367-368`, `:388-390`, `:916-917`).

---

## F. Presentation layer  **[N]**

`export_interactive.py:142-172` copies `montecarlo.py:2573-2622` and hardcodes
what the model derives:

| | `montecarlo` | `export_interactive` |
|---|---|---|
| turnout years | `[y for y in target.before if y >= "2011"]` | literal `(2011…2024)` |
| LGE years | `CALENDAR[y].kind == "LGE"` | literal `(2011, 2016, 2021)` |
| level column | `f"turnout_{target.previous_lge}"` | `"turnout_2026_level"` |
| clamp / nan filter | present | absent |

Adding an election to `CALENDAR` reaches the model and not the page.

---

## Checked and NOT reported as duplication

- `coherent_seats` vs `seats.allocate` — different rules on different
  quantities (a mean seat vector against a fixed council, versus Schedule 1's
  quota on votes). Not duplication.
- `fold.predict` vs `montecarlo.solve_and_predict` — an **intended** independent
  re-derivation; `backtest.py:3` describes `fold.py` as the validator of the
  deterministic core. Worth knowing only because they share `SHARE_FLOOR` by
  coincidence rather than by import (C3).
- `parties.py` holds the alias maps once; `P.canonical` is the single entry
  point everywhere.
- `score.crps_sample` is the only CRPS in the tree.
- `test_hex_cartogram.py`'s restatement of `1.5·√3·r²` — a closed-form identity
  serving as an independent oracle, which is the point.

---

## G. The registers, against the code

**The negative result first, because it changes how to read the rest.** Every
module-level numeric constant in `src/*.py` and every one of the 33 `DEFAULTS`
keys was cross-checked against every number quoted beside its name in
`MACHINERY.md`, `JUDGEMENT-CALLS.md`, `ITERATING.md`, `POLLING.md`,
`DATA-QUALITY.md`, `SOURCES.md`, `PLAN-TO-LIVE.md`, `CLAUDE.md`, `README.md`.
**Every restated value matches** — `SHRINK` 2.0, `SPINE_K` 1.0,
`RELIABILITY_HALF` 0.002, `SD_FLOOR`/`SD_CEILING` 0.15/1.20, `SPLIT_SD_FLOOR`
0.90, `SPLINTER_PARENT_WEIGHT` 0.35, `TURNOUT_CORRELATION` 0.63, `LEVEL_DF` 7.0,
the four `ALPHA_*`, `REFERENCE_SHARE`/`SLATE`, `CLAIM_FRACTION`,
`DIRICHLET_FLOOR`. **The registers are not where the drift is.** The drift is in
restated *mechanisms*, restated *rules*, and typed *outputs*.

### G1 — the poll block describes the σ that was switched off today  **[doc, blocking]**

`SIGMA_TWO_TERM` was adopted as the default on 2026-08-24
(`src/polling.py:251-254`). `JUDGEMENT-CALLS.md:348-349` still reads *"These are
pre-registered and OFF by default"*. Four further rows presenting themselves as
current state are now false:

- `:66` states the live σ as `σ² = deff·p̂(1−p̂)/n + σ_house² + σ_screen² +
  (drift·√days)²`. The live sum is `polling._sigma_total`.
- `:68` — *"the DA's inverse-variance weight is 0.560 and is held to 0.500"*.
  It is held to nothing: `montecarlo.py:2927` sets `_cap = 1.0`.
- `:64` — *"the DA sits exactly ON the cap … set by `poll_house_k` and not by
  the σ arithmetic"*. Now the opposite is true.
- `:225` — `POLL_HOUSE_SD | 0.025` filed as the live house term. It survives
  only as the `n_eff == 0` fallback.

`src/montecarlo.py` contradicts itself twenty lines apart: `:2909-2910` still
asserts *"the cap is 0.50 however many waves it publishes"*, `:2921` says the
cap is deleted.

**This is `CLAUDE.md`'s own non-negotiable — the record changes in the same
commit — missed on the most contested lever in the model.** MODEL-LOG §1.91
recorded the adoption; the register meant to be *current* was not touched.

### G2 — `MACHINERY.md` describes the retired mechanism  **[doc]**

`:284` gives the poll channel as `σ_poll = 3.03pp, a TRACK RECORD not a nominal
margin`, and `:307-308` states the blend as pure precision with no cap. Its poll
section mentions neither `n`/`deff` nor the decomposition. `MACHINERY.md` is the
file a reviewer reads to learn how the channel works.

### G3 — `POLLING.md` is pinned to a lever deleted 2026-08-17  **[doc]**

`:92-95` describes `polling_lean` endpoints and a `w_poll` "not yet
implemented". Both were deleted; `JUDGEMENT-CALLS.md:182` records it. The
register→code guard cannot see this, because it only walks
`JUDGEMENT-CALLS.md`.

### G4 — the bar is "three keys" in one file and four in another  **[doc]**

`ITERATING.md:56-57` — *"the bar has three keys"* — then defines four.
`CLAUDE.md:61` says four. `ITERATING.md` is wrong in the sentence a reader uses
to decide whether a change ships. Related: §H is titled *"The seventeen"* over a
16-row table, and the 2026-08-24 sub-section adds four more.

### G5 — `REG_DRIFT_TOLERANCE` is filed as "reporting, not belief"  **[register]**

`JUDGEMENT-CALLS.md:193` files it green beside `PAGE_SIZE` as a stat-audit
tolerance. It is not: `build_concordance.py:82-87` sets it to 0.30 as the
threshold at which a VD *"is treated as possibly redrawn rather than assumed
stable"*, and it traces `build_concordance:136` → `registration_drift` →
`vd_concordance.csv` → `fold.suspect_vds` → `fold.py:509` → the fold parameter
artefacts → the model. A green classification prices it at zero in the
Derivedness Debt sweep, defeating the register's stated purpose.

### G6 — a config-derived count restated wrongly three times  **[doc]**

`cities/joburg.toml` gives `vds = 865` (2026). **855 matches no year of any
city**, and appears at `MACHINERY.md:672`, `JUDGEMENT-CALLS.md:91`, `:179` and
`:280`. `README.md:4` and `MODEL-LOG.md:3` say 865 and are right.

### G7 — `README.md` links three files that moved to `archive/`  **[doc]**

`:26-31` links `METHODOLOGY.md`, the original plan and `model-review.html`. All
three are now under `archive/`; on the public GitHub these are 404s.

### G8 — `config/dimensions.toml` values re-typed as fallbacks  **[N]**

`extrapolation_damping = 0.6` has **three** independent defaults in `pools.py`
(`:103` dataclass, `:243` `raw.get`, `:700` a function default);
`extrapolation_max_years` two; `within_rate = 0.90` three (`:363`, `:367`,
`:605`); `min_oos_gain` and `gate_parties` one each. The first two are
registered; the third damping default and the `gate_parties` fallback are not
registered anywhere.

### G9 — two more divergent copies, beyond §B  **[R]**

- `montecarlo.months_before_election:674-687` claims in its docstring to feed
  *"the same exp(−age/τ) recency decay `byelections.py` uses … so a contest is
  weighted identically whichever term reads it"*. It returns `days/30.44`;
  `byelections.age_months:126-130` returns calendar-month arithmetic with a
  `/30.0` remainder. They disagree by up to ~2% of the age, and `--set
  bye_tau_months` moves one and not the other.
- `compare_history.coherent_seats:952-982` breaks ties with `np.argsort`
  (unspecified) where `seats.allocate:73-105` uses the statutory larger-vote-
  total rule. Unreachable on float means — but this is the function producing
  `seat_abs_err_coherent`, one of the four keys.

### G10 — three tools give three answers to "which city-years can I run"  **[R]**

`compare_history.py:84-129` requires a pool spec **and** a γ-fold file and
reports refusals; `sweep.py:49-60` checks the spec only; `arrivals.py:111-113`
checks the spec only and swallows failures in `except Exception`. Three panel
denominators — the silent-panel-shrink failure §1.69 exists to end.

---

## H. The published site  *(PUBLISHING-BACKLOG, not this repo's working list —*
*recorded here because the numbers are wrong now, not because it is next)*

- **A live probability typed 25 points wrong.** `forecast-sheet.html:522` and
  the published `site/index.html`: *"The 87% for ANC+DA is arithmetic"*. The
  model says `P(ANC+DA is winning) = 0.622` — **62%**. A token
  `[p_anc_da]` exists at `content/joburg/stats.toml:47-51` and is **referenced
  nowhere**. The 87% is almost certainly a stale copy of `p_da_largest` (live
  0.714). `stats.audit` warns; `--strict` is off, so the build ships it.
- **The sample size is typed 11 times and is wrong.** The published run is
  **1,500 draws**; `DEFAULTS["draws"]` is 5000, which the prose was copied from.
  Nine occurrences in `forecast-sheet.html`, one deriving *"about 4,450 of the
  5,000 runs"* — and **`src/render_map.py:269` hard-codes it into generated
  HTML**, so regenerating does not fix it. `[n_draws]`'s own `used_in` field
  says *"restated 5+ times"* and it catches none of them, because
  `stats.audit`'s regex only matches `N%` or `N seats`.
- **One quantity, three published numbers.** `docs-public/review.md:73-74` says
  the DA is largest in 63%, `index.html` says 87%, the model says 71.4%.
- **Spelled-out digits are invisible to the audit.** `review.md:68-69` — *"In
  roughly six of seven simulations"* = 86%; live 0.59.
- `docs-public/methodology.md:279-281` — *"moved the DA from 83 to 77 seats"*;
  live median 78.0. Entered 2026-08-23, the newest untokenised figure.
- The colophon (`forecast-sheet.html:578-586`) is entirely hand-typed, including
  *"polls enter as levers, not gospel"* — the statement `methodology.md:265-268`
  records as the site's most serious error and corrected.
- **11 of 38 tokens are dead**, including `headline_overhang_party`, whose
  `used_in` names the two lines it is wired to neither of: a live guard that has
  never been armed. No token is missing — every `{{token}}` resolves.

*Not a finding:* the ten `turnout_tilt_da` orphans are correctly enumerated in
`stats.toml`'s own header and `build_site.py:468-477` now refuses to publish
them. Well-maintained duplication.
