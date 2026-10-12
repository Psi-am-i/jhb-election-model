# Pre-registration — VD-level turnout propensity, and whether arrivals are counter-cyclical

⛔ **OUTCOME: P1's ESTIMATOR IS MALFORMED, P2's FALLING ARM IS DECISIVE, AND THE
SIGN TEST FAILS.** The normalisation is not rescued; the per-party lever stays
refused; one strong finding survives. **Nothing below is edited.** Result:
MODEL-LOG §1.204.

**Written 2026-09-07, BEFORE the study is run.** Arises from §1.203, which
refused both a turnout normalisation of the arrival record and a per-party
turnout lever, on the grounds that the metro-level panel has **one** usable
turnout regime and cannot separate a party's turnout propensity from the
co-movement of its appeal.

**This study exists to settle one number**: `γ_arrival`, the elasticity of an
arriving party's supporter turnout with respect to overall turnout. The
normalisation is right only if `γ_arrival < 1`, and is the exact opposite of
right if `γ_arrival > 1`.

---

## P0 — Design, fixed before running

* **Unit:** the voting district. ~800 per metro against 8 metro points.
* **Estimator:** first differences within VD, so the fixed compositional
  confound — wealthy districts vote more — differences out.
* **Ballot:** PR only, so ward-candidate availability cannot drive it.
* **Source:** `data/raw/elections/lge{year}_{CODE}_vd_party_clean.csv`,
  `Registered_Population`, `Total_Valid_Votes`, `Party_Votes`. VDs joined on
  `VD_Number`; **the match rate is reported, and below 70% the arm is void.**
* **Two arms, and the second is mandatory:**
  * **2016 → 2021**, turnout falling ~15pp.
  * **2006 → 2011**, turnout rising ~12pp — the only rise in the panel. **A
    coefficient that does not reverse here is measuring appeal, not turnout**,
    and the whole study fails with it.
* **Reported as bounds, not points.** This is ecological inference and the
  constant-rate assumption fails exactly where behaviour correlates with group
  share.

## P1 — The arrival question, which is the one that decides the normalisation

Per VD: `Δturnout` against the combined 2021 share of parties absent in 2016.

* **Negative** — arrivals strongest where turnout fell most → they collect the
  disaffected, `γ_arrival > 1`, **and the normalisation's direction is WRONG**.
* **Positive** — arrivals strongest where turnout held → they draw
  high-propensity voters, `γ_arrival < 1`, normalisation directionally right.

**PREDICTION: POSITIVE, weak, between +0.05 and +0.30.** Reasoning stated in
advance: ActionSA and the Cape Coloured Congress look like mobilisation stories
in specific communities rather than a harvest of the general disaffected, and a
brand-new party has no machinery for chasing reluctant voters. *Falsified by a
negative coefficient, or by anything above +0.30.*

⚠️ **A positive result does NOT license the normalisation as proposed.** It
would license `γ_arrival` somewhere in `(0, 1)`, and the proposal asserts the
endpoint `γ_arrival = 0`. The midpoint-and-widen response in §1.203 stands
either way.

## P2 — Per-party propensity

Per VD, regress `Δ(party votes ÷ registered)` on `Δ(votes cast ÷ registered)`.
The slope is the party's share of each point of turnout movement; compare it to
the party's own 2016 share.

* slope **>** share → its supporters are the marginal voters.
* slope **≈** share → it turns out like everyone else.
* slope **<** share → its supporters are differentially reliable.

**PREDICTIONS, written before the run:**

* **ANC slope EXCEEDS its share** in the falling arm — the abstention story.
* **DA slope is at or below its share.** ⚠️ This is the one that contradicts the
  metro-level estimate (§1.203 measured DA β = +0.90, its share falling faster
  than turnout) — **if the VD arm agrees with the metro arm instead, my reading
  of the DA's 2021 collapse as defection to ActionSA is wrong and abstention is
  the answer.** Stated so it cannot be re-explained afterwards.
* **EFF slope exceeds its share** — a young, low-propensity electorate.
* *Falsified per party by a slope on the wrong side of its own share.*

## P3 — What it cannot settle, declared now

* **It stays ecological.** A VD is not a voter, and no first difference makes it
  one. The output is a bound on a group rate, not a switching matrix.
* **Defection and abstention are still not separated at VD level** — only
  bounded better. §1.203's Duncan-Davis interval on the abstainer share of
  ActionSA's vote is [0%, 100%] on metro rows; VD rows narrow it, they do not
  close it.
* **Nothing here is wired to anything.** No code changes on this result alone.

## P4 — What decides what happens next

* `γ_arrival < 1` **and** the 2006→2011 sign test reverses → the normalisation is
  argued on a measurement, at the midpoint, with the band widened to span the
  interval. Its own change, after the re-emit window, never inside it.
* `γ_arrival > 1`, **or** the sign test fails → the normalisation is dead and
  §1.203's refusal stands as final. Written up either way.
