# Pre-registrations

**A prediction written down before the run is what turns a result into
evidence.** This directory exists because one was written, paid off, and was
then cited from a path that did not survive the session: `MODEL-LOG.md` §1.144
pointed at a scratch directory under `/private/tmp`, which resolves to nothing
from the repository. The record of record had a hole in it exactly where it
mattered most — a reader could see the claim "pre-registered" and could not check
it. Found in blind review, 2026-08-31.

So: **a pre-registration that is going to be cited is committed here, before the
run it predicts.** One file per question, named `<date>-<subject>.md`. It is
never edited after the measurement — a pre-registration that moves is not one.

| file | question | outcome |
|---|---|---|
| `2026-08-31-sd-for-shape-mechanism.md` | what shape should `sd_for` take below 15% of the vote? | **OPEN — not yet run.** Written to satisfy the mechanism door in `JUDGEMENT-CALLS.md`'s `sd_for` row, which bars a third functional form against the same two folds. Gated behind re-emit entry 4. |
| `2026-08-31-crps-column-count.md` | does `crps["total"]` drift with the scored column count? | P1, P2, P4 held; **P3 refuted** (the intersection biases toward the baselines, not the model); the prediction that `energy` drifts was also **refuted** — it is invariant. MODEL-LOG §1.144. |
| `2026-09-13-held-back-quarantine-asymmetry.md` | where does the pre-2011 quarantine's damage live — the run-time θ/ρ records or the emit-time arrival records? | **OPEN — not yet run.** Two arms of `compare_history`, control and `HELD_BACK_OFF=1`, with **no re-emit**: that configuration lifts the gate on `theta_record` and `local_record` only and leaves the pooled records held, which is the decomposition MODEL-LOG §1.158 asked for. Blocked on a settled tree. |
| `2026-09-28-route-b-in-pyodide.md` | does the citywide table reproduce the model inside Pyodide, and against Atlas? | **All four held.** P1 identical in one interpreter; P2 seats exact against Atlas, shares within 9.9e-16; P3 exactly the two files; P4 6.6 s and 28.0 s. MODEL-LOG §1.267. |
| `2026-09-28-reweight-against-paired-rerun.md` | does re-weighting the published draws by pool turnout reproduce a paired re-run of the model? | **All seven held.** P0 the four seat laws share their draws; P1 the five parties within 2 SE (largest \|z\| 1.31); P2 every varying party within 3 SE (largest 2.05); P3 1,243 effective draws; P4 200 at +8pp; P5 one pool alone moves the DA 1.55 seats against 3.58; P6 all four seat files byte-equal. MODEL-LOG §1.271. ⚠️ Written before the runs by a delegated agent that could not commit, so no commit proves the order; attested, not provable. |
