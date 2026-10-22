# Blind pollster review — taking the poll channel out of the forecast

Commissioned 2026-09-12, after the change was implemented and both panel arms
were measured, and **before** any of its findings were written into the record.

**Blind, per `CLAUDE.md` §4.3.** The reviewer was given the change, the owner's
verbatim reason, both arms of the measurement with the per-row table, the prior
measurements (§1.65's +48, §1.94's −6, §1.95's credence dial), the poll register,
and the `methodology.md` / §A7 contradiction. It was **not** told what the
implementer concluded, and was told to say where it disagreed. Read-only: no
model run, no edit, no sub-delegation.

## Its verdict, in one line each

| question | answer |
|---|---|
| Is the switch defensible? | **Yes on design, and on better grounds than we had. No on measurement — it proves nothing either way.** |
| What does −2 license? | Nothing as a result. It fails Key 1. |
| Do the 2011 zeros establish anything? | Yes, but only as a negative control: the change does not perturb the RNG stream. The seven movers are the stronger check. |
| Which 2026 figure is right? | §A7's `65 → 78`. `methodology.md`'s `83 → 77` is directionally impossible. |
| Is `poll_paths="arrivals"` a middle way? | No — it is identical to `"off"` at 2026 and buys nothing. |
| Biggest risk? | The headline call, and MK's unevidenced level. |

## What was acted on, and where it landed

| finding | disposition |
|---|---|
| The panel decomposes the two paths EXACTLY (metro blend −4, arrivals +2), because they fire on disjoint city-years | **VERIFIED** against every row of `polls.json` and re-derived arithmetically. MODEL-LOG §1.225, and it reconciles the §A7/§A8 contradiction flagged unresolved on 2026-08-31. |
| The change fails Key 1 — sign flips between cycles | **VERIFIED.** §1.225. Recorded as `undetermined`, shipping under `ITERATING.md`'s defensibility trade, which is available only where Key 1 is undetermined. |
| `relabel_run` inflates the ABSOLUTE totals; quote paired differences | **ACCEPTED, and it re-diagnosed a queue item.** The ablation switch is inert (`test_the_relabel_ablation_actually_withholds_the_label` is red), so the label-free panel was never waiting on a settled tree — it is waiting on a repair. Audit item 2, HANDOVER. |
| `83 → 77` is directionally impossible | **MEASURED AND CONFIRMED.** DA 68 → 79. §1.226. |
| `arrivals` ≡ `off` at 2026 | **VERIFIED** — no poll on file carries `target: 2026` with `scope: "national"`. §1.225. |
| The within-house 12pp swing is underpriced ~10× by the drift term | **ACCEPTED** as an argument the decision should rest on. §1.225. |
| MK is now the largest unevidenced quantity in the live forecast | **ACCEPTED.** §1.226. `plan_bounds.MK = [0.3, 1.0]`, hand-typed, confirmed in `cities/joburg.toml`. |
| Run a calibration gate: does the polls-off DA interval cover the polls-on median? | **RUN, AND IT PASSES** — [47, 93] contains 79. §1.226. |

## Where the review was wrong, and it matters

**Its stated worst case does not hold.** It argued the risk was "the model calls
the wrong largest party with the contrary evidence switched off in its own
repository". Measured (§1.226), with polls off the largest-party call is
**ANC 47.3% / DA 47.0%** — a dead heat on 1000 draws. The model does not call it.
The risk is publishing a tie, not publishing a wrong winner. The review was
reasoning from §A7's "the lead FLIPS", which is true of the point estimate and
misleading about the distribution — the same trap as quoting a median without its
interval.

## Its recommendations NOT taken here, and why

1. **Publish both arms side by side.** The right answer and the site already
   promises it. Outward-facing and the owner's call; not taken unilaterally.
2. **Pre-commit both arms' medians before polling day**, so the poll question is
   settled by the election rather than argued afterwards. Cheap, and the
   strongest of its suggestions. Needs the freeze question resolved first.
3. **Design re-insertion around between-house σ estimated from the disagreement
   on file, plus a width-only entrant term** rather than a credence dial on a
   single-house inverse-variance blend. Recorded here as the design brief for the
   re-insertion the owner asked for. Note the review's own observation that
   realised between-house dispersion is a property of the WORLD, so estimating it
   is estimation and not tuning — which is the line `CLAUDE.md` §4 draws.
