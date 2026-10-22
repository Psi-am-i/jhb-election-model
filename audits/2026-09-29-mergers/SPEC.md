# F5 mergers: the read-only specification, as returned by the research agent (2026-09-28)

Nothing here is built. Line numbers refer to commit `69cc6cc`.

**Checked by the lead:**
* RISE has no seed in `pools_2026.json`, and appears under `no_measured_vector`
  and `unclassified_with_national_record` at 0.015569.
* In `npe2024_JHB` (1,415,548 votes): GOOD 3,186, RISE Mzansi 22,039, Forum 4
  Service Delivery 260, ActionSA 88,013.
* RISE is on the Johannesburg 2026 roster; GOOD is not.

## 0. Two premises in the prereg are false

`prereg/2026-09-27-independents-and-mergers.md`, Change 2:

1. **RISE is not sized as an arrival.** It has no seed; its level comes from the
   2024 NPE baseline (`montecarlo.py:4015-4016`, `pools.py:5657-5668`,
   `newcomers` at `pools.py:5760`), and it takes the spine's national-only
   route (`levels.py:1280`).
2. **The prereg names the wrong quantity to transfer.** Its 6,773 (0.367%) is
   GOOD's 2021 LGE count over both ballots. The mechanism transfers the 2024
   baseline: GOOD 0.225% and RISE 1.557%; Forum 4 Service Delivery 0.018% and
   ActionSA 6.218%.
3. **The event is not the one the prereg describes** (press reports, not
   verified by the lead). Unite for Change (RISE, GOOD, BOSA) launched
   2025-10-05 and was deferred 2026-04-13. BOSA stands separately. On
   2026-05-25 GOOD and RISE announced they would run under their own names with
   integrated structures. That is a stand-down pact, not a legal merger.

## 1. No measurable merger in the archive

The agent scanned 74 readable metro-years (14 held back) for parties above 0.2%
that later vanish. Two known mergers have elections held on both sides:

| case | window | naive retention r, across metros |
|---|---|---|
| ID → DA (2010) | LGE 2006 → 2011 | 1.7 to 14.9 |
| ID → DA | NPE 2009 → 2014 | 2.7 to 27.0 |
| NNP → ANC (2005) | NPE 2004 → LGE 2006 | −12.4 to 0.95 |

The successor's own swing is 5–20× the predecessor's mass, so retention cannot
be identified from citywide shares; the estimates run from −17 to +56. A
VD-level regression within Cape Town was not run, and would still be
confounded.

**Conclusion:** retention is a declared 🔴 judgement.

## 2. The proposed mechanism

* **Data.** `Merger(parties: frozenset, date, why)` beside `Split`, with the
  mergers held in `MERGERS`.
* **Direction is decided per city from the roster.** Partners on the ballot
  inherit; partners off it transfer. It is a no-op when every partner is on the
  ballot or none is, and it refuses when more than one partner is on the ballot
  while another is off it. No successor is named in code.
* **One function,** `pools.apply_mergers(shares, roster, target_year, *,
  per_vd=None)`, called in three places:
  * in `run_model` after the baseline load and before `absent_from_ballot`,
    transferring r × predecessor in the citywide share and in every VD;
  * in `emit_pools` on the baseline;
  * on `prev_local` before `levels.spine`.

  `theta_residual.residuals` must call it too.
* **Rule proposed by the agent.** A merger adds to records the successor already
  holds and never creates one it lacks. RISE has no 2021 local record, so
  giving it GOOD's 2021 local vote would move RISE from the national-only route
  to the both-records route and blend it *down* toward about 0.2–0.3%. Under
  the rule, RISE takes the transfer on the national route only, and ActionSA on
  both.
* **Pool vector.** The mass-weighted blend of the successor's and the
  predecessor's vectors.
* **Declarations.**
  * GOOD + RISE, dated 2026-05-25.
  * Forum 4 Service Delivery + ActionSA, dated 2025-01-15.
  * Not BOSA.
* **Retention proposed as a 🔴 judgement:** `MERGER_RETENTION` in the range
  [0.5, 0.9], typed centre 0.75, not measured, swept at {0, 0.5, 0.75, 1.0}
  before shipping.

## 3. The prereg's prediction, and what it cannot detect

The prereg predicts RISE's median moves up 0–2 seats and no other party's moves
by more than 1. The agent's rough, unrun estimate is 0.1–0.2 percentage points,
which is 0–1 seat. A 0-seat result also satisfies the prediction, so the seat
check cannot tell a working transfer from a silent no-op; a test on r × P has to.
