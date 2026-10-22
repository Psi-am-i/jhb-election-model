# Pre-registration — the declared nomination roster at Johannesburg 2026

Written 2026-09-16 on branch `remediation` at `73eec0f`, **BEFORE the IEC
candidate list is in hand, before the two-spec re-emit, and before any run of the
model against a declared roster.** Not edited after the result.

⚠️ **Nothing below is predicted against a previous output of this model.** The
predictions are about MECHANISM — which code path opens, which artefact field
moves, which channel is constructed for the first time — and about the WORLD (the
IEC's published ballot). Where a figure is cited it is cited to the file or the
`MODEL-LOG` § that generated it. `PLAN-TO-LIVE.md` §A5 requires the reporting
rule to be fixed before the lists land, and §5 below is that rule.

---

## 0. ⛔ THE OBVIOUS PREDICTION IS THE WRONG ONE, AND THAT IS WHY THIS FILE EXISTS

`PUBLISHING-BACKLOG.md` §5c frames nomination day as a **contestation** event: the
real slates replace the projection, `contestation_expand` goes inert, and the
published band is *"about ±3 seats to the PA and about ∓2 to the DA"*.

> **[AMENDED 2026-09-16, BEFORE THE RUN AND BEFORE ANY RESULT — and the
> amendment REMOVES a crutch rather than weakening a prediction.]** That ±3/∓2
> band is now **STRUCK** in `PUBLISHING-BACKLOG.md` §5c on the owner's
> instruction: it was measured at §1.60 on 2026-08-20, on the nine-city-year
> panel, at 1200 draws, with polls ON and two re-emits ago. **It is not a
> disclosed judgement call and must not be published or quoted.** The disclosed
> call is the lever — `contestation_expand = 0.220`, `JUDGEMENT-CALLS.md` §A5.
> Nothing in §1 relied on the band; §5 rule 3 is restated below so that it does
> not either.

**A pre-registration built on that framing would be void before it was scored**,
for the reason `MEMORY.md` records under *pre-register the consumer, not the
quantity*: a correct, confirmed prediction about an inert channel is worthless
when the same change moves a dominant one. Reading the code, the declared roster
opens **three** paths, and contestation is the least of them:

| # | path | where | what changes |
|---|---|---|---|
| 1 | **the arrival group is CONSTRUCTED** | `pools.py:6047-6049` | `arrival_group` is built only `if roster_source in ("published", "declared")`. At a projected roster it is `None`. A declared list switches this channel from *cannot be constructed* to *live*, for the first time at 2026. |
| 2 | the off-ballot drop | `montecarlo.roster_for_target` | already runs against the projected ballot since entry 26; a declared roster changes WHICH parties it drops, by name |
| 3 | contestation | `levels.py:751` | `contestation_expand` becomes inert — the §5c channel, and the smallest |

**Path 1 is the one to watch.** `MEMORY.md` records that overhang decides the
majority of the live 2026 forecast and that a rare channel is not an inert one.
So the headline prediction of this file is about the arrival channel, not about
the PA's slate.

## 1. Predictions

Each is falsifiable from the emit diff, the `--run-dir` trace, or the IEC's own
published list. **P1-P4 are mechanism and should hold whatever the ballot says.
P5-P6 are about the world and may simply be wrong.**

- **P1.** After the two-spec re-emit, `pools_2026.json` carries `roster_source ==
  "declared"` and a `roster` equal to the pasted list, canonicalised. The
  `--simulation` spec carries the same roster.
- **P2.** `arrival_group` in `pools_2026.json` is **non-null** after the emit,
  having been `null` before it. This is the switch in §0 path 1 and it is the
  single largest mechanical change of the day.
- **P3.** The run's `03_roster` trace reports `state == "declared"`, **not**
  `"projected"` — and, per the correction recorded at `914a973`, the state
  `"projected"` clears on the *declaration*, while `"published"` is reached only
  after polling day, from the result file. A run that still says `projected`
  after the paste means the spec was not re-emitted.
- **P4.** `contestation_expand` is inert in the 2026 run afterwards: setting it
  to 0.0 and to 0.5 produces identical drawn seats. *(Cheap to check with `--set`
  and worth checking, because it is the §5c assumption everything downstream of
  the published band rests on.)*
- **P5.** The IEC list for Johannesburg contains **more** parties than the
  projection carried. The projection resolved 35 parties (`cf707e3`); the
  newsdesk digest of 2026-09-15 reports 80 parties on the CoJ PR ballot, from
  press coverage rather than from the IEC directly. If the real list is near 80,
  the projection under-counted the ballot by roughly half.
- **P6.** Most of those additional parties are **small**: the drop mass the
  `complete = true` ceiling measures stays under its 1.5% bound without
  `confirm_drop`. The two transitions we have are 8 parties / 1.16% (2016 against
  the 2011 fit) and 10 parties / 0.32% (2021 against 2016).

## 2. What would VOID this pre-registration

- The list not landing on 16 September, so the paste happens under different
  information.
- Taking queue entry 19 (`parties.ALIASES`) in the same window — it moves
  `deps_sha` and invalidates all 27 specs, so the emit would no longer be the
  two-spec event these predictions describe.
- Any model parameter changing between this file and the run.

## 3. What is NOT predicted, deliberately

**The seat numbers.** This model has never forecast a ballot it knew, at this
city, at this target. Predicting the headline here would be predicting against a
prior output of the model, which `CLAUDE.md` §1 bars, and scoring it would tell
us nothing about the world.

## 4. What this measures, and what it cannot

It is **not** a test of forecast skill — nothing is scored against a result until
4 November. It is a test of whether the declared-roster seam does what it claims
mechanically, taken on the one night it matters. `contestation_expand`'s only
out-of-sample test is P4's inertness plus the published movement; it is inert at
every backtestable target (§1.60), so the panel cannot score it even in
principle.

## 5. ⛔ THE REPORTING RULE, FIXED NOW — `PLAN-TO-LIVE.md` §A5

Decided before the movement is seen, because choosing afterwards is what
pre-registration exists to prevent.

1. **Stage 1 stands, unedited.** The pre-nomination forecast is published, hashed
   and frozen, and the revision goes **beside it, never over it** — both visible,
   both dated (§5c's rule).
2. **The difference is attributed to a channel, by name**, from the emit diff and
   the trace: arrival group, off-ballot drop, or contestation.
3. **The size of the revision is reported, against a band declared in the same
   breath as the revision — never against §5c's struck ±3.** Stage 1's own
   published interval is the only comparator that exists on the night: if the
   revision's median sits **inside** Stage 1's 5-95 interval for that party, say
   so; if it sits **outside**, that is a **finding about the projection** and is
   written up as one in `MODEL-LOG.md`, in the same commit, naming the channel
   and the magnitude. Either way it is **not** a reason to adjust the model on
   the night, and **not** a reason to suppress or delay the revision. ⚠️ Stage
   1's interval is an output of this model and therefore **not a standard of
   correctness** (CLAUDE.md §1) — it is being used to say *how far the answer
   moved*, which is a descriptive statement, never to decide whether the
   movement is right.
4. **No widening, no re-tuning, no lever moved on nomination night.** Publication
   gate 5b item 1 (parties with P(≥1 seat) < 0.02) is satisfied by **naming and
   defending** them, never by widening a distribution to make the list shorter.
   Widening is a measured decision for a later window, with its own
   pre-registration.
5. **If the emit or the run refuses**, the refusal is published as the day's
   outcome rather than worked around with an escape flag. A `complete = true`
   refusal on drop mass is read first as *the list is incomplete*, not as *the
   ceiling is wrong*.
