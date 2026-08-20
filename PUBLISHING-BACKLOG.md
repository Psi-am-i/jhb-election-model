# Publishing backlog — the presentation layer, deliberately not the model

**This list is separate on purpose.** The other list is "get a working
prediction model that is publishable". This one is everything that only matters
*once* it is. Nothing here is allowed to compete for attention with the model,
and nothing here is a reason to change a forecast.

The project owner's standing position, 2026-08-18 and again 2026-08-20:

> "I am not concerned with the live page or what lives on it. Nor am I
> interested in the interactive... I am only interested in this model's ability
> to predict."
>
> "we will rebuild interactive and live page when model is ready."

So: **build these when the model is ready, not before.** Read
`ITERATING.md` rule 5 — nothing is republished until the model that produced it
has beaten the previous iteration on history.

---

## 1. The interactive is a frozen program, not a stale page

`forecast-interactive.html` and `site/dev/interactive.html` are **tracked**,
were built 7–8 August, and still carry a "PA's wider slate" slider driving
`paUplift` — a constant the model deleted on 2026-08-18.

`src/build_interactive.py` **refuses to rebuild them**, and says why:

> the interactive page has not been ported to voter pools: its in-browser
> drawer is the old two-bloc engine and there is nothing left to feed it. The
> published page stays frozen in the meantime.

So a reader opening either file sees controls for constants that no longer
exist, driving an engine that no longer exists. That is not a stale figure, it
is a **stale program**, and it is the third instance of a pattern `CLAUDE.md`
opens by warning about — after the `turnout_tilt_da` claims and `site/plan.html`
being served for weeks after no build produced it.

**Nothing in the model reads them.** They are inert as far as the forecast is
concerned. They are only a trap for a human.

When the model is ready, the options are:

* **port** the in-browser drawer to voter pools — the only one that makes the
  page true again, and the largest;
* **delete** both files — they are outputs of an engine that no longer exists;
* **banner** them as frozen, if they are wanted as a historical record.

Until then they should not be read as current by anyone, including us.

## 2. The 2026 forecast has moved and has not been republished

Two changes this week moved the live numbers, both deliberately, neither
published:

* the **level shrink** (§1.44) — DA 0.328 → 0.310 on the PR ballot;
* the **contestation correction** (§1.47) — PA ward share 8.07% → 2.67% and
  mean seats 19.5 → 12.4, with every other party gaining slightly.

Whatever is published next has to be produced by one settled run, with the
stat tokens regenerated from it, per `CLAUDE.md`'s rule that a model figure is
never typed into prose.

## 3. Orphaned stat tokens

`content/joburg/stats.toml` still carries claim tokens the build refuses to
publish. Removing or re-deriving them is a **content** decision, not a code one,
and it waits for the same settled run.
