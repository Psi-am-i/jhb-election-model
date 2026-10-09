# Model investigation packet: the PA's ward/list split (and two related flags)

One investigator, read-only. Issued 2026-10-09.

## Ground rules
- Edit nothing in the repository. Write only to
  `audits/2026-10-09-model-questions/`, plus scratch in the directory you are
  given.
- No `src/montecarlo.py` run as a script, no `compare_history`, no
  `build_site`, no `pools.py --emit`. In-process `run_model` calls are allowed,
  with output to scratch only.
- Use `.venv/bin/python`. Do not sub-delegate.
- Read `CLAUDE.md` (§1: only real elections are a standard; §4: re-derive,
  pre-register), `MACHINERY.md`, `JUDGEMENT-CALLS.md`, `DATA-QUALITY.md`, and
  `MODEL-LOG.md` (search for PA, θ_PA, by-election, ward/PR ratio, Dirichlet,
  centres).
- Mark every claim **verified** (file:line, or a command or run) or **argued**.

## The finding (the total review; re-derived by the coordinator)

In the published draws (`site/draws/`, 5,000 simulations), the PA's list-ballot
share minus its ward-ballot share averages −5.53 points (range −15.22 to
−1.20). Across 40 cleaned metro local-election files (2000–2021), the most
negative gap any party has had is −1.76 points. The PA's own Johannesburg 2021
gap was +0.05.

The owner: "The PA vote should certainly be within bounds and yes it sounds
like an error we introduced that should resolve. have a look."

## Questions

1. **Where the two ballots part.**
   - Trace how the model builds a party's ward-ballot target from its list
     target (`montecarlo.run_model`: `ward_target = pr_target * ratio`, and the
     ratio's source around `montecarlo.py:4683-4696`), and every input that
     feeds the PA's ratio and its two shares.
   - Quantify each input's part in the −5.5-point gap, by in-process runs with
     one input neutralised at a time. Name each neutralisation.
2. **Introduced, or inherited?** Find the change that introduced the gap: git
   history, MODEL-LOG entries, the θ_PA prior, by-election evidence (which is
   ward-ballot only), and the 2024 national file (list-type only). Was the
   ward/list relationship ever checked against real results?
3. **Every party.** For every party in the published draws, compare the model's
   ward−list gap distribution with the gaps real metro results have shown
   (same population of 40 files). Is the PA alone?
4. **The fix.** Propose the change that makes each party's ward−list gap
   consistent with real results, with the evidence. Pre-register, in a file in
   this directory and before any run that tests the fix, what it should do to:
   - the PA's gap;
   - other parties' gaps;
   - the PA's seats and ward wins;
   - the backtest (which `compare_history` metric, and in which direction).

   Then test it in-process only, and report against your pre-registration
   honestly, including anything it falsified.
5. **Secondary, read-only diagnosis; no fix proposed unless trivial.**
   - **The tails of the within-group split.** In 43.4% of simulations at least
     one of the 65 parties with a median of 0–1 seat wins 10 or more seats, and
     in 8.4% one wins 20 or more (coordinator, from the served draws). The
     IFP's 99th percentile is 28 seats against a median of 2, driven by a
     Dirichlet share of the Black African vote of 23% against a typical 1.2%.
     Are these within-group shares within anything real elections have shown?
     Compare against the per-voter-group party shares the model was fitted on.
     What sets the tail (the total concentration, 16.3–22.1)?
   - **Centres against the drawn means.** ANC centre 25.8% against a mean drawn
     list share of 22.1%; DA 30.1% against 25.4%. MACHINERY §2 says the
     centres bind. Is that a contradiction, a definitional difference (combined
     against list, median against mean), or a defect?

## Return

Findings ranked by severity, the pre-registration and its scoring, the
proposed fix with its measured effect, and a list of what is verified and what
is argued.

## Amendment 1 (owner, 2026-10-09): priorities

The owner, verbatim: "other variance needs to be investigated the last point of
no variation is the canary look there first."

1. **First priority: the canary.** 46 of the 74 parties have a level-shock
   sd(log) of 0, including the SACP and the All Citizens Party (best-case
   analysis, `audits/2026-10-09-site-batch/best-cases/FINDINGS.md`). For them
   the within-pool split is the only party-specific draw.
   - Is that a decision (registered where?), a fallback (which code path gives
     0?), or a defect?
   - Which parties are affected, and by which route?
   - What does it do to their seat distributions and to the forecast's width?
   - Every other variance source the model declares: check that it is actually
     drawn for every party it should be, with populations stated both ways.
2. **The within-pool split's machinery, documented precisely.** How the pool
   concentration is fitted (`pools.dirichlet_alpha`, method of moments over the
   yearly citywide splits, weighted by member size, `pools.py:~6340-6401`), and
   what that implies for small members. A single concentration per pool gives
   member i the concentration α·p_i, so relative variance grows as p_i shrinks.
   Compare each party's drawn within-pool share range against the range its
   pool share has had across real elections (the same yearly splits the fit
   uses), so the owner can see where draws leave history.
3. Then the PA question as before.

The owner will propose a reformulation of the within-pool split once the
machinery is clear. Do not design one; describe the current one exactly.
