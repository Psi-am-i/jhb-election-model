# Pre-registration — the declared ward slates reach the contestation correction

**Written 2026-09-23, before any model run of the change.** Nothing below is
edited after the result; the result is scored against it in MODEL-LOG, including
what it falsifies.

## What is being changed, and why

MODEL-LOG §1.251: the certified per-ward nomination lists have been in
`judgements/joburg-2026.toml` under `[roster.wards]` since 2026-09-16, and the
ward contestation correction never sees them. `levels.contestation` reads who
stood from the target's own RESULT file, which does not exist for 2026 until
after 4 November, so `run_model` still projects 2026 slates from 2021 with
`contestation_expand = 0.220`. JUDGEMENT-CALLS §A5 has claimed since 2026-08-20
that the lever is "superseded automatically the day the IEC publishes 2026
lists". It was not, and `test_levers_are_live` sweeps the lever only at 2021,
where it is inert by construction, so nothing could catch it.

**The change.** At a target with no result file, `contestation` returns the
declared ward slates when the judgement file carries them: each party's count of
declared wards over the city's own ward count. `montecarlo`'s projection branch
(`if not _contest and _contest_prev`) is then not taken, and
`contestation_expand` is inert at 2026 — which is what §A5 already promises.

## Decisions fixed in advance

**D1 — denominator.** A party's declared wards over **the city's own wards**
(135 at Johannesburg 2026, from `vd_map`), never over the wards the paste
happens to mention. The other denominator was already a defect once, in the
`reach` derivation, where it made a party's value a function of how far through
the list the typist had got (POOLS-REEMIT-QUEUE entry 23, guard C).

**D2 — absence means zero ONLY under `complete = true`.** With a complete
declared roster, a party absent from `[roster.wards]` fields no ward candidates,
and zero is the true value. With `complete = false` the list is half-typed, so
absence means UNKNOWN and that party keeps the projection. A partial paste must
fail safe, for the reason §1.175 measured: the drop branch deletes 2.4–2.9% of a
city's vote when it fires wrongly.

**D3 — no previous record, no correction.** The correction is a CHANGE, `now /
was`. A party with no 2021 ward record (MK and 53 others at 2026) has no `was`
and is left alone, exactly as today.

**D4 — backtests are untouched.** The declared path is reachable only where the
target has no result file. Every backtest target has one.

## Predictions

Stated as facts about the mechanism and the nomination data, not as agreement
with any earlier output. Each is falsifiable, and the numbers below are computed
from the certified list and the 2021 result file, with no model run.

**P1 — panel invariance.** Every backtest city-year is **bit-identical**. The
coherent-seat scoreboard, `history.json` and every panel figure are unchanged by
this commit alone. If any panel number moves, the change has leaked into a path
it must not reach and it is wrong regardless of its effect at 2026.

**P2 — the lever goes inert at 2026.** Two Johannesburg 2026 runs on one seed
with `contestation_expand = 0.0` and `= 0.5` produce **identical seat draws**.
Today they do not. A 2026 entry joins `EXPECTED_INERT` and a lever with no test
at the target where it matters gets one.

**P3 — who moves, exactly.** 28 roster parties have a 2021 ward record. Of
those, **18 change** their ward/PR ratio (**7 up, 11 down**) and **10 are
unchanged**. The `[0, 2]` clip binds for exactly **three**: PA, Bolsheviks Party
of South Africa, Shosholoza Progressive Party.

**P4 — the PA is the story, and the clip eats part of it.** The PA's real slate
is **all 135 wards** against a projected 0.520, so its ward/PR ratio goes
**1.327 → 2.000**, and the unclipped value is 2.552. **The clip absorbs 22% of
the correction**, which is a real absorber and will be counted and reported, not
discovered later (NULL-RESULTS 4.3). Predicted consequence: the PA's mean seats
**rise by at least 3**, measured against the same tree with the projection on
the same seed. The DA and the ANC each **fall**, by less than the PA gains.

**P5 — one party loses its ward ballot entirely.** CHANGE is on the roster and
in no ward list: PR-only, so its ward ratio goes to exactly 0. Predicted seat
effect **at most 1 seat**, because it is tiny either way. PRO SOUTH AFRICA is
the other PR-only party and has no 2021 record, so D3 leaves it alone.

**P6 — direction of the whole.** More parties lose ward strength than gain it
(11 against 7), but the largest single move is a gain, so the corrected forecast
is **not** a uniform shrinking of the ward ballot.

## What this cannot claim

**Argued, not tested.** `contestation` is inert at every backtestable target
(§1.60), so the backtest cannot score this change in either direction. P1 says
so in the strongest form available: the panel must not move at all. The only
out-of-sample test is 4 November, and it is a test of the SLATES being right,
not of the correction's form.

**This is not a claim that the forecast improves.** It is a claim that the
forecast stops using a projection where the real answer is known and pasted in
the file it already reads. If the corrected forecast looks worse by any
subjective standard, it still ships, because the input is a published fact.

## How it will be scored

In MODEL-LOG, after the window: each of P1–P6 marked held or falsified, with the
run that settled it; the absorbed share at the clip reported as a number; and
JUDGEMENT-CALLS §A5 rewritten in the same commit, with its 2026-09-22 warning
removed only when it is true.
