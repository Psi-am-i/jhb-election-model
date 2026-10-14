# 1c: paired draw streams (common random numbers): design

Step 1c of `audits/2026-10-11-model-round/PLAN.md`, owner decision 1. Follows
MODEL-LOG §1.296, "The draws were not paired between three of the compared arm
pairs". Read-only design: no code was edited, no model run, no emit.

Line numbers are `src/montecarlo.py` at commit `c9e58c0` unless another file is
named.

---

## 1. Inventory: every consumer of randomness in a run

One `np.random.Generator` is built per run at L4507
(`rng = np.random.default_rng(scenario["seed"])`), handed to `make_drawer` at
L5689, and also read directly by the draw loop in `run_model`. Every call below
draws from that one stream, in this order, once per draw.

| # | file:line | what it draws | numpy call | values per draw | count depends on |
|---|---|---|---|---|---|
| 1 | L3236 | citywide turnout factor `z_common` | `standard_normal()` | 1 | nothing |
| 2 | L3242 via L792 (or L790 → L456 when `rho_t <= 0`) | each untied pool's own turnout normal, mapped through the triangular inverse CDF | `standard_normal()` (or `triangular`) | 1 per untied pool | the pool set (`pool_spec` drops a pool with no member on the ballot) and the tie structure |
| 3 | L3254 via L792 | one turnout normal per tie group | `standard_normal()` | 1 per tie group | the tie structure |
| 4 | L3288 via L557 | level shock, one Student-t per IPF party | `standard_t(df, size=len(ipf["parties"]))` | number of pooled parties | the party set; and `standard_t` draws a gamma by rejection, so the number of underlying bits consumed depends on `df` and on the outcomes |
| 5 | L3376 | within-pool split, one Dirichlet per pool | `dirichlet(moved * alpha)` | 1 vector of length m per pool | pool membership; `alpha` changes every draw (it is the IPF output `pool_props`), and numpy draws each gamma by rejection, so bits consumed depend on the shape and on earlier outcomes |
| 6 | L3383 via L557 | level shock for each non-pooled ("individual") party | `standard_t(df)` scalar | 1 per individual party | the party set; rejection as in 4 |
| 7 | L3393 | arrival-group total (off: `arrival_group_draw` is `False` at L347) | `normal(mu, sd)` | 1 | the switch |
| 8 | L3406 | arrival-group split (off, as 7) | `dirichlet` | 1 vector | the switch, group membership, rejection |
| 9 | L3415 | entrant gate | `random()` | 1 | whether `ENTRANT` is in `index` |
| 10 | L3414 → L456 | entrant share | `triangular` | **1 only when the gate passes** | **an earlier random outcome (9)** |
| 11 | L5775 | turnout-pattern blend jitter | `uniform(-1, 1)` | 1 | nothing |
| 12 | L5776 | per-VD turnout noise | `normal(0, turnout_noise_sd, nvd)` | nvd (VDs in sorted order, L4969) | the VD set |
| 13 | L5824 | ward-tally noise, one per (ward, party) | `normal(0, ward_noise_sd, (nwards, npar))` | nwards × npar | **the party set** (`npar`, columns in sorted-universe order, L4927); skipped entirely when `ward_noise_sd` is 0 |

Not random, checked:

* **The seeded lot** (batch item 1). `seats.lot_order` (`src/seats.py:109`) is
  `sha256(f"{key}#{i}")` over a key built by `seats.draw_key(run_lot, d)` at
  `allocate_with_overhang(..., lot=draw_key(run_lot, d))`; the run identity is
  `seats.lot_identity(city, target, seed)` at L4509. It reads no generator and
  no party name enters the key, so it is already keyed per draw. Out of scope:
  `lot_order` numbers the *tied* codes in sorted order, so a party joining a
  tie reorders that tie's tickets. Exact ties need equal surplus and equal
  votes, so this is rare and is not a draw-stream question.
* **Ward winners** use `ward_tally.argmax` after continuous noise (13); an
  exact tie has probability zero, and `prediction.top_party`'s lot is used on
  the published ward table, not in the draw loop.
* `solve_and_predict` (L983), `pool_spec`, `capped_targets`, `_balance`,
  `partial_balance`, `level_shock_sd`: deterministic.
* `pools`, `levels`, `reweight`: no generator is reached during a run (grep of
  `default_rng|np.random|random.Random|SeedSequence` over `src/` finds only
  `benchmarks.py`, `bye_value.py`, `score.py`, `theta_residual.py`,
  `width_budget.py`, all outside `run_model`). `bye_value.py:284` runs at emit
  time; `score.py:760,1366` and `score.column_rng` (`score.py:492`) randomise
  PITs during scoring, after the draws.

### Why the arms came out unpaired

Every row above reads one shared stream, so the values draw *d* receives depend
on everything every earlier call consumed. Three things make that consumption
vary between arms:

1. **Counts that follow the party set**: rows 4, 6 and 13 change length when a
   party is added (item 8, A/B8).
2. **Rejection samplers whose consumption follows their parameters**: rows 4,
   5, 6, 8. Item 11a and item 17 changed centres and widths but no party; the
   Dirichlet shapes then differ slightly, one gamma somewhere accepts on a
   different trial, and every later value in the run shifts. The draw index at
   which this first happens is itself random, which fits the partial
   correlations in §1.296's table (C/B 0.965 at ekurhuleni 2011 and 0.041 at
   mangaung 2021). Argued from the code, not measured: nobody has located the
   first divergent draw.
3. **A count that follows an earlier outcome**: row 10.

Measured on the gamma alone (scratch bench, not the model: 50,000 draws, J = 4
slots, numpy 2.5.1): numpy's `standard_gamma` on an array of shape *a* against
the same seed at shape 0.98·*a* gives a per-draw correlation of 0.046 (a =
0.05), 0.019 (a = 0.5), 0.145 (a = 3) and 1.000 (a = 30). A 2% change of shape
unpairs the stream wherever rejection occurs.

### The browser and the draws export

* **Nothing in the browser draws.** The interactive re-weights the published
  draws (`src/export_draws.py` → `site/draws/base.bin` + `manifest.json`;
  `src/reweight.py`; the seat Worker `interactive/py/entry.py:83` reads them and
  checks `draws_sha256`). `src/build_interactive.py` raises `SystemExit` at
  import, so the old JavaScript engine in `src/interactive_template.html`
  (`mulberry32`, L550 and L742, the two-bloc model) is dead and needs no port.
* **`interactive/py/montecarlo.py` is a byte copy** of `src/montecarlo.py`, made
  by `node interactive/tools/sync_py.mjs` (manifest `code_ref` per file set) and
  for the Worker by `worker-api/tools/sync_seats_py.mjs`. The change reaches the
  browser only through re-sync (`--check` fails until then) and the step 9
  re-export.
* **`export_draws` requires identical draws across seat laws** (its docstring:
  "the seat law acts after every random draw"). Keyed streams keep that
  property; nothing in the seat law draws.
* What must stay in sync, in step 9: `site/draws/*` re-exported from the
  canonical run; `interactive/py/` and `worker-api/seats-py/src/` re-synced;
  `draws_sha256` changes, so the Worker answers 409 to a card sealed against the
  old draws (`entry.py:105`). Any republish does this; it is not specific to
  this change.

---

## 2. Design

### 2.1 Principle

Every random quantity reads its own stream, named by what it is, and indexed by
the draw. A stream draws **only parameter-free primitives**, standard normals
and uniforms on [0, 1), in a **fixed count per draw**. Every parameter (a
shape, a band, a df, an sd, a probability) enters afterwards through a
deterministic transform. Consequences:

* Adding or removing a party adds or removes its streams and touches no other
  stream's values.
* Changing a parameter changes only the transform; the primitives under it are
  the same, so the drawn value moves smoothly with the parameter.
* Draw *d* reads row *d* of each stream whatever the total draw count, so a
  1,000-draw run is the prefix of a 5,000-draw run at the same seed.

### 2.2 Stream key

    entropy = [stable_entropy(run_lot), stable_entropy(kind),
               stable_entropy(stage),   stable_entropy(name)]
    generator = np.random.default_rng(entropy)        # PCG64 via SeedSequence

* `run_lot = seats.lot_identity(city, target, seed)`, the run identity the lot
  already uses (L4509). One definition of "this run".
* `kind` is `"z"` (standard normals) or `"u"` (uniforms); a stream needing both
  holds two generators, so a row's values do not depend on how a refill
  interleaves them.
* `stage` is a fixed string per random quantity (table 2.3). `name` is the
  entity: party code, pool name, `pool|party`, a tie key, or `""` for citywide
  quantities.
* `stable_entropy(text) = int.from_bytes(blake2b(text.encode("utf-8"),
  digest_size=8).digest(), "big")`. This is the body of
  `score._column_entropy` (`score.py:470`). It moves to `seats.py` (standard
  library only, already imported by `montecarlo` and shipped to Pyodide and the
  Worker), and `score._column_entropy` becomes a one-line delegation, so the
  existing pin `S._column_entropy("ANC") == 16408193524922255279`
  (`tests/test_calibration_report.py:2035`) holds and the hash has one
  definition. Never `hash()`: salted per process, and `fix_hash_seed` runs only
  under `__main__`.

**City and target are in the root key on purpose.** Keyed on (seed, stage,
party) alone, the ANC's level shocks would be the same numbers at every
city-year in the panel, the 24 city-years' Monte Carlo errors would be
correlated, and the panel-mean seed spread §1.296 measured would understate the
noise. Pairing is wanted between arms at one city-year, never between
city-years.

### 2.3 Stages

| stage | name | kind, values per draw | replaces | transform |
|---|---|---|---|---|
| `turnout.common` | `""` | z, 1 | row 1 | as now |
| `turnout.pool` | pool name, or tie key `"|".join(sorted(names))` | z, 1 | rows 2, 3 | `correlated_triangular(z_own, spec, z_common, rho)`; at `rho <= 0`, `z = z_own` (no separate triangular call) |
| `level.z` | party | z, 1 | rows 4, 6 | `log_shock(sd, z, log_chi, df)` |
| `level.chi` | party | z, J and u, J+1 | rows 4, 6 | `log_gamma_slots(df/2, ...)` |
| `split` | `pool|party` | z, J and u, J+1 | row 5 | `pool_split(log_gamma_slots(moved_i * alpha, ...), moved * alpha)` |
| `arrival.total` | `""` | z, 1 | row 7 | `mu + sd * z` |
| `arrival.split` | party | z, J and u, J+1 | row 8 | as `split` |
| `entrant.gate` | `"ENTRANT"` | u, 1 | row 9 | `u < entrant_prob` |
| `entrant.share` | `"ENTRANT"` | z, 1, **drawn every draw** | row 10 | `tri_from_z(z, entrant_share)` used only when the gate passes |
| `vd_turnout.blend` | `""` | u, 1 | row 11 | `(2u - 1) * turnout_blend_jitter` |
| `vd_turnout.noise` | `""` | z, nvd in `vds` order (sorted, L4969) | row 12 | `turnout_noise_sd * z` |
| `ward_noise` | party | z, nwards in `wards` order (sorted, L5238) | row 13 | column of `ward_noise_sd * z`, assembled to `(nwards, npar)` by party |

Notes on the keys:

* **One `level` stream per party serves both the IPF path (row 4) and the
  individual path (row 6).** A party is on one path or the other; if an arm
  moves it between paths its shock keeps its values.
* **`split` is keyed `pool|party`** because a party is a member of several
  pools, each with its own split.
* `vd_turnout.noise` is one stream over the VD vector rather than one per VD:
  the VD set is data, not an arm choice, and per-VD streams would cost one
  generator per VD. A change of VD set (a delimitation change) therefore
  unpairs this stream. Stated, accepted.
* `ward_noise` is per party, so adding a party adds a column and leaves every
  other party's column bit-identical. A change of ward set unpairs it.

### 2.4 Exact samplers from primitives

All exact in distribution; none changes what the model draws from.

* **Gamma (Marsaglia-Tsang with fixed slots).** For shape *a*: if *a* < 1, draw
  Gamma(*a*+1) and multiply by U^(1/*a*) (the boost; one extra uniform). With
  d = *a'* − 1/3, c = 1/√(9d), each of J slots holds (z_j, u_j); slot j accepts
  if v_j = (1 + c·z_j)³ > 0 and log u_j < z_j²/2 + d − d·v_j + d·log v_j. The
  value is d·v_j at the **first** accepted slot. This is rejection sampling on
  iid trials, so it is exact. Computed and returned **in log space**
  (`log d + log v + log(U)/a`), because at *a* near `DIRICHLET_FLOOR × alpha`
  the value underflows; numpy's gamma returns exact 0.0 there, and the log form
  agrees after normalisation (`exp` of a very negative log-share is 0.0).
  * **Exhaustion.** If all J slots reject, the value comes from an exact
    fallback generator keyed `[..., stage, name, d, "fallback"]`
    (`np.random.default_rng(...).standard_gamma`, boosted the same way). Exact,
    because conditional on J rejections the output must still be Gamma, and any
    independent exact sampler is. **Counted, never silent**:
    `DrawStreams.gamma_fallbacks`, carried to `ModelRun.gamma_fallbacks` and
    `41_guards.gamma_fallbacks` beside `ipf_failures`.
  * **J = 4.** Acceptance for shape ≥ 1 is above 0.95 (Marsaglia-Tsang), so
    P(all reject) < 0.05⁴ ≈ 6e-6 per gamma; at about 800,000 gammas per
    5,000-draw run that is about 5 fallbacks a run; counting split streams as
    about 300 (a party is a member of several pools, 2.8), about 1.9 million
    gammas and about 12 fallbacks a run. In the scratch bench (200,000 draws per shape,
    J = 6) no draw at shapes 0.01, 0.3, 1, 4, 60 exhausted. J changes no
    distribution, only how often the fallback runs; it is a numerical constant,
    named `GAMMA_SLOTS`. It and `STREAM_CHUNK` (2.5) are numeric module
    constants, visible to `test_register_matches_code`, and both must be
    declared in the register as distribution-neutral, with V1 (J) and V2
    (chunk) as the evidence.
* **Student t.** t = z / √(2G/df), G ~ Gamma(df/2) from `level.chi`. Exact.
  Built on slots rather than numpy's `standard_t` so that a `LEVEL_DF` change
  stays paired (numpy's resyncs, for the gamma reason above). df/2 for the
  gamma shape and df in the scale must be one value, so the drawer resolves
  `LEVEL_DF` once per draw (at call time, preserving the §1.33 property) and
  passes it to both; `log_shock` takes df as a **required** argument and never
  reads `LEVEL_DF` itself, so a gamma drawn at one df cannot be scaled at
  another.
* **Dirichlet.** Independent Gamma(α_i), normalised, is exactly Dirichlet(α).
  `pool_split(log_g, alpha) = exp(log_g − max) / Σ exp(log_g − max)`; `alpha`
  is not read by the model, only by the width-budget ablation that patches
  this function (2.5). numpy's
  `Generator.dirichlet` uses a beta stick-breaking method when every α is
  below 0.1; both are exact.
* **Triangular.** `tri_from_z(z, spec) = _tri_ppf(clip(Φ(z), 1e-9, 1−1e-9),
  spec)`, the copula path's existing mapping (L767, L792-795). The clip
  already applies to every correlated pool turnout; extending it to the
  `rho <= 0` path and the entrant share removes at most 2e-9 of probability
  mass from each tail.
* **Normal, lognormal, uniform(−1, 1).** `mu + sd·z`, `exp(sd·z)` as now, and
  `2u − 1`: exact.

### 2.5 Code-level specification

All in `src/montecarlo.py` except `stable_entropy`. Keeping the stream code in
`montecarlo.py` means no new module enters the Pyodide and Worker file lists
(`worker-api/tools/sync_seats_py.mjs` FILES, held equal to the import closure
by `tests/test_reader_seats.py` and `interactive/tests/page.test.mjs`).

**`src/seats.py`**, beside `lot_identity` (L68):

    def stable_entropy(text: str) -> int: ...          # blake2b-64, big-endian

**`src/score.py:470`**: `_column_entropy(party)` returns
`seats.stable_entropy(party)`; its docstring keeps the reasoning and points to
the definition.

**`src/montecarlo.py`**, a new block after `_tri_ppf` / `correlated_triangular`
(L767-796), replacing `triangular` (L454) and the bodies of `log_shock` (L528)
and `correlated_triangular` (L779):

    STREAM_CHUNK = 256     # draws per refill; changes no drawn number (V2)
    GAMMA_SLOTS = 4        # Marsaglia-Tsang trials per gamma per draw (2.4)

    class DrawStreams:
        """Keyed, draw-indexed random primitives for one run."""
        def __init__(self, run_lot: str, draws: int,
                     chunk: int | None = None): ...
            # `draws` bounds d: a read of d >= draws raises (a test passes a large enough value)
        def normals(self, stage: str, name: str, d: int, k: int = 1) -> np.ndarray   # (k,)
        def uniforms(self, stage: str, name: str, d: int, k: int = 1) -> np.ndarray  # (k,)
        def stacked_normals(self, stage: str, names: tuple[str, ...],
                            d: int, k: int = 1) -> np.ndarray                         # (m, k)
        def log_gamma(self, stage: str, names: tuple[str, ...],
                      shapes: np.ndarray, d: int) -> np.ndarray                       # (m,)
        keys: set[tuple[str, str]]   # every (stage, name) read: the population for tests
        gamma_fallbacks: int

    def log_gamma_slots(shape, z, u, u_boost) -> tuple[np.ndarray, np.ndarray]
        # (log value, accepted mask); vectorised over members; pure
    def student_t(z, log_chi, df) -> np.ndarray
    def log_shock(sd, z, log_chi, df: float) -> np.ndarray
        # exp(sd * sqrt((df-2)/df) * student_t(z, log_chi, df)); df required, resolved by the caller
    def tri_from_z(z, spec) -> float
    def correlated_triangular(z_own, spec, z_common: float, rho: float) -> float
    def pool_split(log_g: np.ndarray, alpha: np.ndarray) -> np.ndarray
        # the named patch point for the Dirichlet; alpha read only by width_budget's patch

Internals of `DrawStreams`:

* One generator per (kind, stage, name), created on first read; each holds a
  buffer of `chunk × k` values and the draw index the buffer starts at. A read
  of draw *d* past the buffer refills sequentially (generating any skipped
  chunks), so row *d* is the same for every chunk size. numpy's
  `standard_normal` and `random` fill sequentially: in the scratch bench,
  10,000 normals drawn at once equal 3,333 then 6,667 from the same key, and
  likewise for uniforms. A read of *d* earlier than the buffer start raises;
  a second read of one stream with a different `k` raises (a shape change is a
  defect, not a resize).
* `stacked_normals` / `log_gamma` cache the stacked `(m, chunk, k)` block per
  `names` tuple per chunk, so a draw costs one slice per pool, not one lookup
  per member.
* Memory at the shipped settings: per scalar stream one chunk of 256 floats;
  `ward_noise` 256 × nwards per party (Johannesburg, 135 wards, about 80
  parties: about 22 MB); `vd_turnout.noise` 256 × nvd. Nothing is held at
  `draws × …` size.

**`make_drawer`** (L2966): signature becomes
`make_drawer(scenario, base_city_d, centres, index, streams: DrawStreams)`.
Passing a `np.random.Generator` raises `TypeError` naming `DrawStreams`, so a
caller cannot silently fall back to a shared stream. The closure becomes
`draw_pools(d: int | None = None)`; `None` uses an internal counter starting at
0, so `draw()` called repeatedly in tests still means draws 0, 1, 2, …. Edits:

* L3236: `z_common = streams.normals("turnout.common", "", d)[0]`.
* L3241-3256: `z_own` from `turnout.pool` keyed by pool name or tie key;
  `correlated_triangular(z_own, ...)`.
* L3285-3288: `df = LEVEL_DF` resolved once; `parties = tuple(ipf["parties"])`;
  `z = streams.stacked_normals("level.z", parties, d)[:, 0]`;
  `lc = streams.log_gamma("level.chi", parties, np.full(m, df / 2), d)`;
  `shocked = base_c * log_shock(sds, z, lc, df)`, df passed explicitly.
* L3376: `split = pool_split(streams.log_gamma("split",
  tuple(f"{name}|{q}" for q in names), moved * alpha, d), moved * alpha)`. `names` is
  `pools[name][5]`, the members in spec order; the key is by name, so order
  does not matter.
* L3382-3383: the individual loop reads `level.z` / `level.chi` for its party.
  Vectorise once: stack the individual parties, one `log_gamma` call per draw.
* L3393, L3406: `arrival.total`, `arrival.split` (off by default; specified so
  the switch stays pairable).
* L3414-3415: `gate = streams.uniforms("entrant.gate", "ENTRANT", d)[0]`;
  `z = streams.normals("entrant.share", "ENTRANT", d)[0]`, both read every draw;
  `share = tri_from_z(z, scenario["entrant_share"]) if gate <
  scenario["entrant_prob"] else 0.0`.
* `draw_pools.streams = streams` beside `ipf_stats`, so `run_model` reads
  `keys` and `gamma_fallbacks`.

**`run_model`**:

* L4507: `rng = ...` is replaced by `streams = DrawStreams(run_lot,
  scenario["draws"])`, built after `run_lot` (L4509).
* L5689: `make_drawer(..., streams)`; L5760: `pr_target = draw_target(d)`.
* L5775: `blend = clip(base + (2 * streams.uniforms("vd_turnout.blend", "",
  d)[0] - 1) * jitter, 0, 1)`.
* L5776: `noise = scenario["turnout_noise_sd"] * streams.normals(
  "vd_turnout.noise", "", d, k=nvd)`.
* L5822-5824: `z = streams.stacked_normals("ward_noise", tuple(universe), d,
  k=len(wards))` → `(npar, nwards)`; `ward_tally *= np.exp(ward_noise_sd *
  z.T)`.
* `ModelRun` (L3727) gains `gamma_fallbacks: int` and `stream_keys:
  list[tuple[str, str]]`; `41_guards` (L5917) records both. `main` prints the
  fallback count the way it prints `ipf_failures`.

**`src/width_budget.py`** must change with it, or it measures nothing: its
Dirichlet ablation wraps `np.random.default_rng` to intercept `.dirichlet`
(L52-56, `_MeanDirichletRNG`), and the drawer will no longer call `.dirichlet`,
so the wrapper would go inert and report a zero Dirichlet contribution with no
error (ITERATING rule 6). Replace it by patching `montecarlo.pool_split` to
return the mean share `alpha / alpha.sum()` from its second argument, and
`_no_pool_turnout` to the new `correlated_triangular(z_own, spec, z_common,
rho)` signature. Its docstring's "READ THE NOISE FLOOR" paragraph becomes
partly obsolete: with keyed streams, switching one source off no longer moves
the others, so the ablations become paired. Re-measure, don't assume.

### 2.6 What cannot be paired, and how much pairing survives

Raw primitives of every stream present in both arms are bit-identical. Drawn
shares of unchanged parties still move through four normalisations and the
solve:

1. **IPF level-shock normalisation**, `shocked / shocked.sum()` (L3290): every
   share moves by a common factor per draw when a party is added.
2. **The balance**, `Rd = _balance(...)` (L3324): every pooled party's
   proportions depend on all shocked centres jointly, so `pool_props`, and
   with them each member's Dirichlet shape, change slightly. The slot gamma
   keeps the member's value close (bench: correlation 0.9995-1.0000 between
   shape *a* and 0.98·*a* at a = 0.05, 0.5, 3, 30; 50,000 draws, J = 4).
3. **Within-pool and citywide normalisation**: `pool_split`'s own sum, and
   `target / total` (L3386).
4. **The entrant rescale**, `target *= (1 - share)` (L3416).

Then `solve_and_predict` calibrates every VD to the target; seats and ward
winners are discontinuous functions of paired inputs, so they agree on most
draws and differ where a draw sits on a boundary.

Toy measurement of (3) only (one pool, 45 members, total concentration 30,
20,000 draws, seed 1; a toy proves the mechanism, not the magnitude on the
panel): adding a member of mean share 0.1%, 0.5%, 2%, 5% leaves the existing
members' shares correlated with their old values at median 1.0000, 0.9999,
0.9997, 0.9992 and minimum 0.9996, 0.9983, 0.9932, 0.9837. The same toy
unpaired: median −0.002. The magnitude on real arms after (1), (2) and (4) is
the measurement R2 below.

Quantities whose key changes are unpaired by design: a renamed party (lineage
gives a new code), a party moving between pools (new `split` key), a changed
tie structure (new tie key), a changed VD or ward set.

### 2.7 Rejected alternatives

| alternative | measurement or reason that rejected it |
|---|---|
| `np.random.SeedSequence(seed).spawn(n)` per party | children are numbered by spawn order, which follows the party set: adding a party renumbers every later child. The task proposed it; it fails the requirement it was proposed for. |
| Root key of seed alone (no city, target) | correlates every city-year's draws for the same party code, so the 24 city-years' errors stop being independent and the panel seed spread (§1.296) is understated |
| Per-party numpy `standard_gamma` / `dirichlet` / `standard_t` on a block | unpairs on any shape or df change: per-draw correlation between shape *a* and 0.98·*a* 0.046 / 0.019 / 0.145 at a = 0.05 / 0.5 / 3 (scratch bench, 50,000 draws, numpy 2.5.1) |
| One generator per (stream, draw) | exact and simple, but a generator costs about 10 µs (10,000 creations: 0.103 s in the bench); 5,000 draws × (about 160 level/split streams + 80 ward-noise columns) is about 1.2 million creations, about 12 s a run. Kept only for the gamma fallback. |
| Python `hash()` for keys | salted per process; `fix_hash_seed` runs only under `__main__` (`score.py:470` docstring, §1.145) |
| Inverse-CDF gamma | needs `gammaincinv`; scipy is not installed in `.venv` |

### 2.8 Runtime

Not measured on the model. Scratch bench, numpy 2.5.1, this machine:

* Stream creation: about 1,000 generators per run (about 80 parties × 3 level
  and ward streams, × 2 kinds where both are used, plus about 300 pool-member
  split streams × 2); 10,000 creations took 0.103 s, so about 0.01 s a run.
* Slot gammas: one vectorised transform per pool per draw and one per draw for
  the level shocks. 20,000 transforms over 50 members at J = 6, including
  generating the primitives, took 0.64 s (32 µs each). At about 10 transforms
  per draw, about 0.3 ms a draw, about 1.6 s per 5,000-draw run, against which
  the current numpy `dirichlet` and `standard_t` calls are removed.
* Chunk refills of `ward_noise` and `vd_turnout.noise` generate the same
  number of normals the current code does, in larger calls.

Estimate: under 2 s added per 5,000-draw city-year. The step-5 writer measures
wall time at Johannesburg 2021, 1,000 draws, before and after, and records it.

---

## 3. Verification

The standard for "distribution unchanged" is the mathematical distribution each
sampler claims, tested at unit level against numpy's own samplers. A comparison
of new-code runs with old-code runs is a tripwire for a wiring mistake, never a
judgement on the forecast (CLAUDE.md §1): it asks whether two implementations of
one distribution agree, not whether the distribution is right.

### V1. Samplers exact (suite; constructed inputs; seconds)

Two-sample Kolmogorov-Smirnov, N = 200,000 per side, statistic D against
c(α)·√(2/N) with α = 0.001 per comparison, c(0.001) = 1.949, so reject at
D > 0.00616. Comparisons:

* `log_gamma_slots` (exponentiated) against `rng.standard_gamma` at shapes
  1e-4, 0.01, 0.1, 0.5, 1, 3.5, 10, 100;
* the same at J = 1, which forces the fallback on a large fraction of draws:
  the distribution must still pass, and `gamma_fallbacks` must be positive
  (it proves the fallback is exact and is counted);
* `student_t` against `rng.standard_t` at df 2.5, 4, 7, 30;
* `pool_split` against `rng.dirichlet`, each component, for α vectors
  including one with a member at `DIRICHLET_FLOOR × alpha` and one with every
  α below 0.1 (numpy's stick-breaking branch);
* `tri_from_z` against `rng.triangular` for three bands including a mode at an
  edge.

Can see, where the test has power (effect sizes from a scratch bench at
1,000,000 draws per side, max CDF difference D, against the 0.00616 threshold):
Gamma(1.05·a) against Gamma(a) at shapes 0.01 to 100 (D 0.018 to 0.197) must
reject; t at 2·df against t at df for df 2.5, 4, 7 (D 0.028, 0.019, 0.012)
must reject; a Dirichlet with one α doubled must reject at that component. No
power: shape 1e-4 (both sides a spike at zero) and df 30 (D 0.003 at 2·df);
those rows check the sampler passes, not that the test can see.

### V2. Indexing (suite)

* Chunk sizes 1, 7, 256 give byte-identical rows for every stage.
* A run built with `draws = 100` equals the first 100 rows of `draws = 1000`.
* Reading draw 5 after draw 9 raises; a second read with a different `k` raises.
* Two subprocesses at `PYTHONHASHSEED` 0 and 4 produce byte-identical first
  rows for a fixed key (key stability across interpreters).
* `seats.stable_entropy("ANC") == 16408193524922255279` (the existing PIT pin,
  now on the one definition).

### V3. Pairing, constructed (suite; `make_drawer` on a constructed spec of
two pools and seven parties, in the style of `tests/test_pool_conservation.py`;
2,000 draws)

Arms against base: (i) a dummy party added to pool 1 at mean share 0.1%, 1%,
5%; (ii) a dummy individual party; (iii) one party's centre ×1.2; (iv)
`entrant_prob` 0.25 → 0.35; (v) `LEVEL_DF` 7 → 4; (vi) `ward_noise_sd` 0.10 →
0.12 (run-level, constructed ward table).

Assertions:

1. **Population.** The set compared is `streams.keys` of the base arm ∩ the
   other arm, asserted equal to the set the spec implies (each party's
   `level.*`, each `pool|member`'s `split`, each pool or tie, the citywide
   stages), checked both directions, and non-empty.
2. **Bit-identity of primitives** for every key in that set: `np.array_equal`
   over all 2,000 rows. This is the invariant, and it is exact.
3. **Bit-identity of derived quantities that depend on no changed input**:
   pool turnouts in (i)-(iii) and (v); `split` gammas of every member of pool 2
   in (i); every party's `level` gamma in (iii) except the changed party.
4. **Correlation of drawn list shares**, reported for every unchanged party and
   asserted against thresholds measured on this constructed spec at three
   seeds and written into `prereg/` before the test is committed. The toy in
   2.6 suggests at least 0.99 median for a 1% addition; the pre-registration,
   not this document, sets the number.
5. (iv): the gate draws and the share draws are bit-identical; the share is
   used in strictly more draws.

### V4. The detector goes red (suite; each mutation reverted → green again)

| mutation | must fail |
|---|---|
| key `level` by column position `str(index[party])` instead of the party code | V3.2 in arm (i), for every party sorted after the dummy |
| drop `city` and `target` from the root (seed only) | a test that the ANC's `level.z` rows at two city-years are uncorrelated (abs corr < 5/√2000) |
| one key for every stage (collision) | a test that two distinct keys' rows are uncorrelated, same bound; plus a distinct-entropy check over every key in `streams.keys` |
| entrant share drawn only when the gate passes, from a shared stream | V3.5 |
| `pool_split` replaced by `rng.dirichlet` on a per-pool stream | V3.2 and V3.3 for pool-1 members in arm (i) |
| `stable_entropy` via `hash()` | V2's two-interpreter test |

### Run-level measurements (one-off, step 7-8, recorded in MODEL-LOG; not in the suite)

**R1. Distribution unchanged.** The pre-change commit (`git archive` into a
scratch tree) and the new code, each at 5,000 draws on its own seed, at
ekurhuleni 2011, mangaung 2021, joburg 2021, joburg 2026. For each party with
mean list share at least 0.1%: two-sample KS on list share, ward share and seat
count, with α = 0.01 per city-year Bonferroni-split over its parties, i.e.
reject at D > √(−½ ln(α/(2m))) · √(2/5000) for m parties. Also mean, p5, p50,
p95 with bootstrap standard errors (|Δ|/SE < 4), and the rates of IPF
fallback, group-share tripwire firing and overhang within binomial error.

* *It can pass*: old code seed A against old code seed B must pass the same
  thresholds; run first.
* *It can see*: new code with one party's level sd ×1.5 must fail at that
  party. At 5,000 draws and about 80 parties the critical D is about 0.044;
  a ×1.1 change of a lognormal width is D ≈ 0.024 (bench above) and KS cannot
  see it, ×1.5 is D ≈ 0.097. Add the variance ratio of log share per party as a
  dispersion check with more power than KS for width changes.
* *A reference failure means the threshold is wrong, not the code.* At α =
  0.01 per city-year over 4 city-years and 3 metrics, the old-against-old
  reference has about a 12% chance of one false rejection. If it fails, fix the
  threshold and re-run the reference before reading the old-against-new result.

**R2. Pairing on the real arms.** Rebuild §1.296's table (median over parties of
the per-draw correlation of list shares, A/B8, C/B, C16/D at the three
city-years) and the bootstrap Monte Carlo error of a paired list-MAE
difference, set against the unpaired 0.19-0.20 points per city-year §1.296
reports. Pre-register the expected correlations in step 4.

---

## 4. Invalidated by the change

The change moves every drawn value at every seed. Expected, and each needs a
deliberate disposition:

| artefact or test | what happens | disposition |
|---|---|---|
| `tests/test_drawer.py` `GOLDEN_PARTIES`, `GOLDEN_POOLS` (L466-482, TOL 0.01 pp at 2,000 draws) | fail | re-record with `--record` after V1-V3 pass, say why in MODEL-LOG; its `draw_matrix` builds `default_rng(SEED)` (L576) and must build `DrawStreams` |
| `tests/test_drawer.py::test_drawer_is_deterministic_for_a_fixed_seed` | API only | builds `DrawStreams` |
| `tests/test_ipf_feasibility.py` L168, 252, 286, 382 (`make_drawer(..., rng)`), L367-369 (`log_shock(default_rng(11), sd)` for the LEVEL_DF binding) | `TypeError` | port to `DrawStreams`; the L367 unit test is re-scoped to `log_shock(sd, z, log_chi, df)` with df explicit; the §1.33 property (`LEVEL_DF` read at call time) is tested through `make_drawer`, as L382 already does |
| `tests/test_pool_conservation.py` L287, L513 | `TypeError` | port |
| `tests/test_draw_record.py` L91-96, L323-338 (patch `correlated_triangular(rng, spec, z_common, rho)`, pools identified by band) | signature | patch the new signature; identification by band unchanged |
| `tests/test_draw_record.py` check 2 (live run against published `seat_draws.csv`) | red until republish | its own docstring gives the shelf life; holds again after step 9 |
| `tests/test_reweight.py` L91-99 (same patch) | signature | as above |
| `tests/test_export_draws.py` (export at the published seed vs served files), `tests/test_served_draws.py` checks 1-3 and 5 | red until step 9 re-export | regenerate, don't re-pin |
| `data/processed/forecast_frozen.json` (`tests/test_freeze.py`) | the freeze trips | a tripwire: go and look, then re-freeze at step 9 |
| `data/arms/step11/*/arrays.npz`, `history.json`/`.md`, forecast artefacts, `content/<city>/stats.toml` tokens, `site/draws/*` | superseded | regenerated by the canonical run (step 7) and step 9; MODEL-LOG entries before the change describe the past and are not edited |
| `interactive/py/`, `worker-api/seats-py/src/` copies, manifest `code_ref` | stale (`sync_py.mjs --check` exits 1) | re-sync at step 9 |
| `src/width_budget.py` Dirichlet and turnout patches | inert or `TypeError` | rewrite per 2.5 |
| `tests/test_levers_are_live.py` | per-lever perturbations become paired, so small effects previously excused as draw noise may now register | read any `Null` whose evidence cites seed noise; expected to sharpen the harness, not break it |

Not affected: `tests/test_calibration_report.py` and `tests/test_chain.py`'s
own generators (synthetic data); `score.column_rng` PIT keys (the hash value is
pinned and unchanged); the seeded lot; `test_chain.py::
test_passing_a_run_directory_changes_no_drawn_number` (still holds: `--run-dir`
reads no stream).

---

## 5. Risks

1. **A key that silently collides or drifts** pairs the wrong things or none.
   Mitigated by `streams.keys` on the trace, the distinct-entropy check and
   V4's mutations.
2. **Gamma fallback rate.** If a pool's shapes sit where Marsaglia-Tsang
   acceptance is lower than the bench saw, fallbacks rise; the distribution
   stays exact (V1 at J = 1) but the fallback draws are unpaired. The counter
   on `41_guards` shows it.
3. **Pairing overstated in prose.** Bit-identity holds for primitives; shares
   are correlated, not identical. Every statement of a paired difference must
   cite R2's measured correlation, not "paired".
4. **The old-vs-new comparison read as a standard.** R1 checks equivalence of
   samplers and must never be used to argue that a forecast is right.
5. **Ward and VD noise are keyed by stage, not per element.** Comparisons
   across a delimitation change are unpaired in those two streams.
6. **One writer.** This touches `make_drawer`, `run_model`, `seats.py` and
   `score.py`; CLAUDE.md §3 applies. No run, sweep or `compare_history` while
   it lands; V1-V4 are unit-level and safe to run during the window.
