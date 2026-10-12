# 2: independent review of 1c (paired draw streams)

Reviews `audits/2026-10-11-model-round/step1/1c-paired-draws-design.md`.
Read-only: no model run, no `compare_history`, no emit. Code read at `HEAD` of
`remediation` (`09ddb27`); every `src/montecarlo.py` line the design cites
still matches. Numerical checks are scratch benches (numpy 2.5.1, Atlas) run in this
session's scratch directory, which is not preserved. The sampler they test is
reproduced in the appendix with a one-line description of each check. A bench
measures a sampler or a toy pool, not the model on the panel.

Severity: **blocking** (the design does not meet its own stated purpose until
fixed), **should-fix** (a defect that would cost a round or a red suite),
**note**.

---

## Findings

### 1. Blocking: the boost applied only below shape 1 breaks pairing for any gamma whose shape crosses 1

§2.4 boosts a gamma only when *a* < 1 (Gamma(*a*+1)·U^(1/*a*)), and runs
Marsaglia-Tsang at *a* itself when *a* ≥ 1. The two branches use different
primitives in different roles, so the drawn value jumps when the shape crosses
1. §2.1's premise, "changing a parameter changes only the transform … the drawn
value moves smoothly with the parameter", fails at that point.

Measured (`t2_pair.py`, 50,000 draws, J = 4, seed 7, same primitives both
sides; correlation of the gamma value):

| shape change | design (boost below 1 only) | boost at every shape |
|---|---|---|
| 0.995 → 1.005 | 0.652 | 0.9996 |
| 0.98 → 1.02 | 0.651 | 0.9991 |
| 0.9 → 1.1 | 0.648 | 0.9936 |
| 3 → 2.94 (no crossing) | 0.9990 | 0.9998 |
| 0.5 → 0.49 (no crossing) | 0.9996 | 0.9996 |

At pool level (`t6_pool.py`: one pool, 45 members, total concentration 30,
20,000 draws, seed 1; one member's mean share 3.2% → 3.5%, shape 0.96 → 1.05,
others renormalised): the crossing member's drawn share correlates 0.668
between arms under the design, 0.998 with boost at every shape. The other 44
members: median 0.9995 / min 0.9978 (design), 1.0000 / 0.9993 (boost always).

How often it applies (proxy, not the model's per-draw shapes): over the 27
`pools_*.json` specs, member weight normalised within the pool × the pool's
`alpha` puts 393 of 3,213 member shapes in [0.8, 1.25]. The real shapes are
`moved × alpha` with `moved` from the per-draw balance, so the true count
differs, but shapes near 1 are common, and centre changes (items 11a and 17,
the case §1.296 is about) move them.

Fix: boost at every shape. Gamma(*a*) = Gamma(*a*+1)·U^(1/*a*) is exact for
all *a* > 0; the J+1-th uniform is already in the stream layout, so no key,
count or memory changes. Measured exact (`t7`, 200,000 draws per side, seed
21, KS against `rng.standard_gamma`, threshold 0.00616): J = 4, D 0.0012-0.0033
at shapes 0.01, 0.5, 1, 3.5, 10, 100; J = 1, D 0.0021-0.0038 at the same
shapes, with 49-9,498 fallbacks. V1 then needs no new case; V3 needs an arm built to
cross *a* = 1 (finding 6), because arm (iii) (a centre ×1.2) may not.

### 2. Should-fix: V1's "every α below 0.1" Dirichlet comparison fails on a correct sampler

numpy's `Generator.dirichlet` switches to beta stick-breaking when every α <
0.1, and that path returns exact zeros wherever the remaining mass falls below
double precision. Measured (`t4_dir.py`, `t4b.py`, 200,000 draws, J = 4,
α = (0.05, 0.02, 0.08, 0.003)):

| α | numpy exact zeros | design's share < 1e-15 | KS D vs `rng.dirichlet` (linear) | KS D vs boost-identity reference (log) |
|---|---|---|---|---|
| 0.05 | 0.000 | 0.120 | 0.0032 | 0.0037 |
| 0.02 | 0.007 | 0.437 | 0.0075 | 0.0014 |
| 0.08 | 0.016 | 0.030 | 0.0162 | 0.0028 |
| 0.003 | 0.866 | 0.885 | 0.7614 | 0.0023 |

The threshold in V1 is D > 0.00616, so three of four components reject. The
difference lies entirely below 1e-15 of share, which no model quantity can
see. The vector with one member at `DIRICHLET_FLOOR × alpha` (largest α 16.1)
takes numpy's gamma path and passes (D 0.0019-0.0032).

The risk is the obvious repair, loosening the threshold, which removes V1's
power everywhere. Fix: for that vector compare in log space against an
independent exact reference (numpy `standard_gamma(a+1)` × U^(1/a), normalised
in log space), or compare `max(x, 1e-12)` on both sides. Keep the floor-member
vector against `rng.dirichlet`.

### 3. Should-fix: the tie-group key unpairs a tie whenever its membership changes

§2.3 keys a tie group by `"|".join(sorted(names))`. `pool_spec` drops a pool
with no member on the ballot (`montecarlo.py:2816-2821`), so an arm that
changes the party set (item 8) can change a group's surviving members, and the
key with it; a group reduced to one pool also moves to the untied branch,
keyed by pool name. Either way the remaining pools' turnout shock is
unpaired. The `ties` dict is already keyed by the declared label,
`scenario["pools"][name].get("tie") or name` (`montecarlo.py:3143-3144`).

Fix: key `turnout.pool` by that label, the same in both branches.

### 4. Should-fix: breakage the §4 list misses

| artefact or test | why it breaks | disposition |
|---|---|---|
| `tests/test_regressions.py:207`, `M.log_shock(rng, 0.3, size=20000)` | old signature; `TypeError` or silent misbinding under `log_shock(sd, z, log_chi, df)` | port to the new signature with explicit df; keep both assertions (tail, realised sd 0.3) |
| `src/width_budget.py:126-130`, `_no_shock(rng, sd, size=None, df=None)` patched over `log_shock` | §2.5 and §4 rewrite the Dirichlet and turnout patches only. Under the new positional signature `sd` binds to `z` and `size` to `log_chi`; a vector `z` returns ones by accident, a scalar raises | rewrite to the new signature, returning ones of `np.shape(z)` |
| `tests/test_stage_realisation.py:104-117` `GUARD_KEYS`, checked in both directions | adding `gamma_fallbacks` and `stream_keys` to `41_guards` turns it red | add both keys; add `stream_keys` to the non-counter list beside `NAME_LIST_KEYS` |
| same file, `GUARD_DENOMINATORS` (L122-126) | `gamma_fallbacks` is a count of gammas, and the design records no gamma count, so it cannot be quoted as a rate | record `gamma_draws` per run and map `gamma_fallbacks → gamma_draws` |
| `src/width_budget.py:52-56` `__dirichlet__` arm | it replaces `np.random.default_rng` globally; after the change it wraps every `DrawStreams` generator and the fallback, inert but not erroring | the design already replaces it; delete the global wrapper too, not only stop relying on it |

Checked and not affected: `tests/test_citywide_table.py:96` compares a
deterministic build, not draws; `tests/test_levels_dispersion.py` Key-4
baselines and `src/theta_residual.py:664,741,909` simulate the t law with their
own generators (same law after the change, no shared stream); `export_draws`
calls `run_model` twice and needs identical draws across seat laws, which keyed
streams keep.

### 5. Should-fix: the fallback test cannot see a subtly wrong fallback

V1 checks the fallback by running at J = 1 and requiring the KS test to pass.
Measured fallback fraction at J = 1 (`t1_ks.py`, 200,000 draws): 4.7-4.9% at
shapes ≤ 0.1 and at 1.0-1.01, 2.7% at 0.5, 0.93% at 3.5, 0.28% at 10, 0.033% at
100. A fallback that is wrong by a small amount (a 5% shape error moves D by
0.018-0.197 on its own, design V1) is diluted by those fractions to below
0.006 and passes. A gross error (missing boost) at shapes < 1 would be seen;
at shape 100 nothing would.

Fix: test the fallback path alone (force exhaustion, J = 0) against
`rng.standard_gamma` at shapes below and above 1, with the same KS threshold,
plus the J = 1 test for the counter.

### 6. Should-fix: nothing at `run_model` level proves the wiring

V2 tests `DrawStreams` in isolation; V3 tests `make_drawer` on a constructed
spec. Neither checks the run loop, where the drawer's internal counter and the
loop's `d` must agree, and where `vd_turnout.*` and `ward_noise` are read.
V3.2 (primitive bit-identity) holds by construction of the keys and tests the
stream class, not the wiring; V3.3 needs the derived values captured by party
name, which `log_shock` (arrays without names) does not expose.

Add:

* `run_model` on a small real city-year at about 30 draws with `STREAM_CHUNK`
  1, 7 and 256: every `*_draws` array of `ModelRun` byte-identical.
* `draws = 20` against `draws = 40`: the first 20 rows of `pr_share_draws`,
  `ward_winner_draws` and the seat draws identical.
* V3.3 by capture: wrap `log_shock` and `pool_split` in the test so each call
  records its inputs with the `names` tuple the drawer passes, and compare
  per party.
* V3 arm (vii): a centre change built so one pool member's Dirichlet shape
  crosses 1; its split gamma correlation must exceed 0.99 (fails under the
  design as written, finding 1).
* V4 mutation: the stacked block drawn from one generator keyed by the `names`
  tuple instead of per member; must fail V3.2 for every member in arm (i).
* V4 mutation: the drawer ignores the passed `d` and uses its counter while the
  loop also calls it elsewhere; must fail the prefix test.

### 7. Should-fix: R2's bootstrap must be paired

R2 compares "the bootstrap Monte Carlo error of a paired list-MAE difference"
with §1.296's unpaired 0.19-0.20 points. A bootstrap that resamples each arm's
draws independently re-imports the unpaired error and will report about the
same number. Specify one draw-index resample applied to both arms. Also report
the spread of the paired difference over the three seeds §1.296 used, since
the seed spread of one arm no longer measures the noise of a difference.

### 8. Note: inventory complete

`grep -nE "\brng\b"` over `src/montecarlo.py` finds generator reads at
L456, 557, 792, 3236, 3242, 3254, 3288, 3376, 3383, 3393, 3406, 3414, 3415,
5775, 5776, 5824 and the construction at L4507: the design's 13 rows, line for
line. `make_drawer` has one caller in `src/` (L5689); `draw_target` is called
once per draw (L5760). No module reached by `run_model` (`pools`, `levels`,
`seats`, `polling`, `coalitions`, `prediction`, `byelections`, `fold`) imports
`np.random` or `random`. Generators outside a run: `benchmarks.py:972`,
`theta_residual.py`, `score.py` (PIT, keyed per city-year through
`compare_history._pit_seed`), `bye_value.py`, `width_budget.py`.
`benchmarks.prior_lge_noise` (`benchmarks.py:972-977`) draws one normal vector
in `ctx.universe` order, so a comparison against that baseline across arms that
change the party set stays unpaired. Outside 1c's scope; worth one line in
§2.6.

### 9. Note: samplers exact as specified (apart from finding 1, which is about pairing, not law)

Measured, two-sample KS at N = 200,000 per side, threshold 0.00616:

* Slot gamma (`t1_ks.py`): J = 4 and J = 1, shapes 1e-4, 0.01, 0.1, 0.5,
  0.99, 1.0, 1.01, 3.5, 10, 100: D 0.0015-0.0040, all pass. Fallbacks at J = 4:
  2 in 200,000 at shape 1.0, none elsewhere; per-trial rejection at shape 1 is
  4.86%, so P(4 rejections) ≈ 5.6e-6, which matches §2.4's estimate. Shape 1e-4
  is compared in log space against Gamma(a+1)·U^(1/a) from numpy, since numpy's
  own gamma underflows there.
* Student t (`t3_t.py`): t = z/√(2G/df), G ~ Gamma(df/2), is correct
  (χ²_df = 2·Gamma(df/2)). D 0.0021-0.0036 at df 2.5, 4, 7, 30. The wrong
  constant, z/√(G/df), gives D 0.071-0.083, so V1 can see a constant error.
* Triangular from Φ(z) through `_tri_ppf` with the 1e-9 clip (`t4_dir.py`):
  D 0.0023-0.0030 for (0.3, 0.5, 0.7), (0.01, 0.01, 0.12), (0, 0.9, 1).
* Dirichlet as normalised slot gammas: passes in log space at every α tested
  (finding 2 is a defect in the reference, not the sampler).
* Fallback exactness is argued, and the argument holds: P(A) = (1 − r^J)·F(A) +
  r^J·F(A) for any independent exact fallback.

### 10. Note: no new or lost correlation found

Checked against the key scheme:

* Same party in several pools: `split` keyed `pool|party`, independent per pool
  as numpy's per-pool Dirichlets were.
* Same party across city-years and seeds: the root is
  `lot_identity(city, target, seed)` (`seats.py:68`), so both are independent;
  arms at one city-year and seed are paired, which is the intent. Seed spread
  stays honest.
* Gate and entrant share: separate stages; the share's distribution given the
  gate passes is the same triangular as before, and the gate-passing draws are
  nested as `entrant_prob` rises.
* `level.z` and `level.chi` are separate stages, so z ⟂ G as the t requires.
* The only cross-quantity dependence the model had, the turnout factor
  `z_common`, is kept.
* The seeded lot (sha256 of `run_lot|draw{d}#i`) and the PCG streams share a
  run identity string and nothing else.

### 11. Note: the entropy list is not strictly injective

`SeedSequence` coerces each list element to the fewest uint32 words and
concatenates them, so `[5, 7·2^32]` and `[5, 0, 7]` give the same state
(`t5_seq.py`, verified with `generate_state`). A 64-bit blake2b value has a
zero high word with probability 2^-32, and a collision needs a further
coincidence, so this is negligible. A fixed-width key is cleaner:
`blake2b("\x1f".join([run_lot, kind, stage, name]), digest_size=16)` as one
int, and the distinct-entropy check then covers the whole key.

### 12. Note: smaller points

* `Generator.random()` is on [0, 1), so U = 0 gives log U = −inf in the boost
  term. Probability 2^-53 per uniform; use `1 − u`.
* The acceptance test now runs through numpy's vectorised `np.log`, whose
  last-ulp results can differ across CPU instruction sets; a slot decision on a
  boundary could differ between machines. Pairing on one machine is unaffected
  and the project runs on Atlas.
* `stacked_normals` and `log_gamma` cache blocks per `names` tuple on top of the
  per-stream buffers. If the cache draws from the generator rather than from
  the per-stream buffer, the two desynchronise. The run-level chunk test in
  finding 6 catches it.
* `GAMMA_SLOTS` swept by `test_levers_are_live` would move drawn values only on
  exhaustion; §2.4 already requires a register entry declaring it
  distribution-neutral.

---

## Verdict

**Sound with listed fixes.** The architecture (keyed, draw-indexed,
parameter-free primitives with exact transforms) is correct and the samplers
are exact. One blocking fix: boost the gamma at every shape (finding 1); as
written, any pool member whose Dirichlet shape crosses 1 between arms is
unpaired (bench correlation 0.65-0.67), in the centre-change case the design
exists for. Findings 2-7 should be fixed before the step-5 writer starts.

---

## Appendix: the bench sampler and the checks

`slots.py`, the design's §2.4 sampler as written (`boost_all=False`), and the
proposed fix (`boost_all=True`):

    def log_gamma_slots(a, z, u, ub, boost_all=False, fb_rng=None):
        # a: (n,) shapes; z, u: (n, J) slot primitives; ub: (n,) boost uniform
        boost = (a < 1) | boost_all
        ap = np.where(boost, a + 1.0, a)
        d = ap - 1/3; c = 1/np.sqrt(9*d)
        v = (1 + c[:, None]*z)**3
        lv = np.log(v)                                  # nan where v <= 0
        acc = (v > 0) & (np.log(u) < 0.5*z**2 + d[:, None]
                         - d[:, None]*v + d[:, None]*lv)
        first = np.argmax(acc, axis=1)                  # first accepted slot
        lg = np.log(d) + lv[np.arange(len(a)), first]
        lg[~acc.any(1)] = np.log(fb_rng.standard_gamma(ap[~acc.any(1)]))  # fallback
        return lg + np.where(boost, np.log(ub)/a, 0.0)

| check | what it does |
|---|---|
| `t1` | KS of the design's sampler against `rng.standard_gamma`, J = 4 and J = 1, ten shapes; counts fallbacks |
| `t2` | same primitives at two shapes; correlation of the gamma value, design against boost-always |
| `t3` | Student t as z/√(2G/df) against `rng.standard_t`; and the wrong constant z/√(G/df) |
| `t4`, `t4b` | normalised slot gammas against `rng.dirichlet` per component, two α vectors; log-space reference by the boost identity; triangular from Φ(z) against `rng.triangular` |
| `t5` | sequential fill of `standard_normal`; the `_column_entropy("ANC")` pin; `SeedSequence` list coercion |
| `t6` | 45-member toy pool, one member crossing shape 1, share correlations between arms |
| `t7` | KS of the boost-always sampler, J = 4 and J = 1, six shapes |

