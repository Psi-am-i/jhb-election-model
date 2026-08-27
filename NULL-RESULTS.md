# Why nothing ever seems to change, and how to stop accepting that as an answer

**The owner, 2026-08-27:**

> *"many changes we make result in no discernable change to results. In a
> complex system that is possible for a process(es) that are isolated or a
> specific set of values becomes an attractor for a whole category of variables.
> In a connected system of adjustments, there should be knock on effects through
> the system when you change assumptions. To have no change be the normal result
> IS THE signal to look for."*

He is right, and this document is the answer to *how*. The short version: **the
harness cannot tell four different things apart, and reports all four as
"no change".**

---

## 1. The four causes of a null, and only one of them is a finding

| | cause | what it actually means |
|---|---|---|
| **A** | **UNDELIVERED** | the value never reached the computation |
| **B** | **ABSORBED** | it arrived, and something downstream ate it |
| **C** | **CANCELLED** | it arrived, and a fitted parameter moved to offset it |
| **D** | **INERT** | it arrived, propagated, and genuinely does not matter |

**Only D is a result.** A is a defect. B is a structural fact that must be
stated. C is a statement about identifiability, not about the world.

Today's evidence that all four are present and confused:

* **A** — of 48 constants pre-registered for the B2 sweep, **42 carry a
  blocker**, and the largest class is undeliverability: a module constant set in
  the parent process does not cross the `ProcessPoolExecutor` boundary, so a
  sweep fans out to eight workers that re-import the default and reports a flat,
  confident null.
* **B** — `logit` clips at `level_floor`, so a party under the floor stops
  responding to θ entirely (§1.98 F12). Rows are renormalised, so a change to one
  party is redistributed across the others.
* **C** — pool size and fitted rate are jointly identified by the votes, so
  changing the pool size changes nothing once the rate refits (§1.102). That is
  why repairing a 187% registration rate measured *worse*.
* **D** — genuinely inert levers exist and are worth knowing about.

## 2. The largest absorber is by design, and it was never written down

`solve_and_predict` exists to force each party's realised citywide share onto the
share that draw drew. It succeeds. Measured on a constructed city, 200 VDs,
6 parties:

| perturbation | `max abs(citywide − target)` |
|---|---|
| baseline | 3.1e-08 |
| `dev × 5` | 4.1e-07 |
| **`dev` reversed** | 5.5e-08 |
| **`dev` randomised** | 6.0e-08 |
| `gamma × 10` | 7.4e-07 |
| **`gamma = 0` (geography deleted)** | 1.7e-16 |

**Reverse the geography, randomise it, or delete it, and the citywide totals do
not move.** They cannot: the solver's whole purpose is to put them back.

### What that implies for the seat score

`pr_votes` and `ward_votes` are both `weight @ pred`, so both are pinned to their
drawn targets. `combined = pr_votes + ward_votes` is therefore **a function of
the drawn targets alone**. And in `allocate_with_overhang`, a party's ward wins
change its seat count **only when `wins >= entitlement`**.

> **Geography — `dev`, `gamma`, pool composition, anything at VD level — reaches
> `seat_abs_err_coherent` ONLY through overhang triggers.**

That single sentence explains most of the owner's observation. It is not a bug.
It is what a calibrated model *is*. But it means:

* judging geography work by seat error is **measuring with an instrument that
  cannot see it**;
* the seat score is concentrated almost entirely in the **target draw** — pools,
  centres, θ — and is close to blind everywhere else;
* an "improvement" to geography that shows no seat movement has told us nothing
  either way.

**This is a claim to verify at panel scale, not just on the constructed city
above.** The measurement: count what fraction of draws fire overhang at all
(`excessive_draws` and `overhang_count` are already in the `41_guards` trace),
and re-run the panel with `dev` randomised. If seat error barely moves, the
channel is confirmed near-dead for that metric.

---

## 3. What already exists, and where it stops

The repository is not naive about this. It has:

* `tests/test_levers_are_live.py::test_every_tunable_lever_actually_moves_the_forecast`
  — perturbs each lever to a value that *must* change the answer and fails if it
  does not. Written because `LEVEL_DF` swept 2.5→1000 byte-identical.
* `EXPECTED_INERT` — 18 registered exceptions, each with a prose reason.
* `note_constant` / `scenario["_constants_read"]` — **a read log**, already
  recording which constants were consulted during a run.
* `compare_history`'s serial-forcing guard — refuses to fan out when a module
  constant has moved.

**Three gaps, and they are why the machinery did not catch this:**

1. **Coverage is `DEFAULTS` keys only.** The 42 blocked constants are mostly
   *module* constants — `montecarlo.LEVEL_DF`, `SHARE_FLOOR`, `DIRICHLET_FLOOR`,
   `TURNOUT_DRAW_FLOOR/CEILING`, the whole `polling.SIGMA_*` family, `ALPHA_*` —
   none of which is in `DEFAULTS`, so none is swept for liveness.
2. **The serial-forcing guard names the defect it was built for and does not
   cover it.** Its comment cites *"the one `LEVEL_DF` was in for weeks"* — and it
   checks five `levels` names. `LEVEL_DF` is `montecarlo.LEVEL_DF`. It is not
   covered. Neither is anything in `polling`.
3. **`EXPECTED_INERT` reasons are claims, not evidence.** `pools.py:248` records
   that two of them were written from unstable readings and had to be retracted.
   A prose reason cannot distinguish A from D — which is the entire problem.

---

## 4. The plan

### 4.1 Make delivery provable, not assumed ★ do this first

`_constants_read` already logs *which* constants were read. Extend it to log the
**value**, and add one assertion to every sweep:

> **the swept constant must appear in the read log, at the value that was set.**

Until it does, a flat result is **VOID, not NULL**. This one change converts the
largest class of false finding — 42 of 48 constants — from a confident null into
a named delivery failure. It is cheap, it changes no forecast, and it makes every
subsequent measurement trustworthy.

### 4.2 Every null gets a cause code

A sweep result of "no change" must be classified `UNDELIVERED` /
`ABSORBED:<stage>` / `CANCELLED:<parameter>` / `INERT`, and only `INERT` is
reportable as a property of the model. `EXPECTED_INERT`'s 18 entries each get a
code and a delivery proof; any that cannot produce one is reopened.

### 4.3 Absorption accounting — the new instrument

Each absorbing stage reports **how much it absorbed**, per run, in the
`41_guards` trace beside the counters already there:

* `logit`'s clip — cells clipped and mass moved (partially exists as
  `ipf_clipped`);
* row renormalisation — mass redistributed;
* the θ solve — total |Δθ| compensation, and the share of the input perturbation
  it cancelled;
* the pool balance — already has `ipf_balances` / `ipf_failures`.

**A stage that absorbs ~100% of what it is given is an attractor and must be
declared as one.** That turns "no change" from a mystery into a location.

### 4.4 A sensitivity ladder, published

For each input, perturb it hard and record the effect on three things
separately, because they are not the same question:

| | metric | what it can see |
|---|---|---|
| 1 | drawn citywide target | the pool/centre/θ machinery |
| 2 | ward winners | geography |
| 3 | seats | (1) fully, (2) only via overhang |

Anything with no effect on all three is dead code. Anything with an effect only
on (2) is geography-only — and **must not be judged by seat error**.

### 4.5 Make the harness intolerant

* A sweep with no change **exits non-zero** unless delivery was proven and the
  null carries a cause code.
* Extend `test_every_tunable_lever_actually_moves_the_forecast` from `DEFAULTS`
  keys to **every constant in `JUDGEMENT-CALLS.md`**, module constants included.
  The register already names them; the test simply does not read it.
* Fix the serial-forcing guard to cover `montecarlo` and `polling`, not just
  `levels` — and derive its list from the register rather than hand-maintaining
  five names, because `test_every_defaults_key_is_swept_or_excused` already
  records what happens to hand-maintained allowlists ("13 of 27").
* **Mutation coverage as a standing gate** for the declared levers, not the
  one-off Phase A did.

### 4.6 Add a geography-sensitive key to `ITERATING.md`

Because `seat_abs_err_coherent` structurally cannot see geography, a fifth
measurement is needed for any change to `dev`, `gamma`, pools-as-geography, or
the VD layer: **ward-winner accuracy** — how many of the 135 contests are called
correctly. Without it, the pool-vs-`dev` experiment and every future geography
change are being scored by an instrument that is blind to them.

---

## 5. The order

1. **Delivery proof** (4.1) — unblocks everything, changes nothing
2. **Cause codes on the 18 `EXPECTED_INERT` entries** (4.2) — cheap, and likely
   to reopen several
3. **Fix the serial-forcing guard's coverage** (4.5) — two lines, prevents the
   largest class of false null
4. **Verify the overhang claim at panel scale** (§2) — one run with `dev`
   randomised
5. **Ward-winner key** (4.6) — needed before pool-vs-`dev` means anything
6. **Absorption accounting** (4.3) and the **sensitivity ladder** (4.4) — the
   bigger build, worth doing once the above stops the bleeding

**Then** B2 is worth running, and its nulls will mean something.
