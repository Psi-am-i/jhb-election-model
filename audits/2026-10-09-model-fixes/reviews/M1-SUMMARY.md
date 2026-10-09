# Slice M1 diff review: summary (2026-10-09)

**The statute citations and the seat law are correct.** The reviewer verified
them against the Act text: item 8(2) (lot), item 13(2)(b) and item 16(4)(c)
(higher votes). Laingsburg is pinned to the IEC's real votes and reproduces
the published council and the round-two ranking.

**Blocking for deploy:**
- B1: the deploy order is recorded nowhere. The new `reader_seats` requires
  the lot. If the seat Worker is redeployed before the rebuilt site Worker,
  every entry is refused.

**Should fix:**
- S1: item 2 alone moves 5 of 5,000 published councils. Each is an equal
  whole-vote surplus with unequal votes, where the float ranking put the
  smaller party first, so the move is what the statute requires. P1 must split
  the populations.
- S2: `test_export_draws` is red by design until the re-export.
- S3: G6 cannot see a reversion to float ranking. G5 can.
- S4: G2's leg for `montecarlo.main` is circular.
- S5: in deduct, an exact tie can fall differently in round 0 and round 1.
- S6: the key forms have no single definition.
- S7: §Q5's claim about C is false, and figures are retyped.
- S8: G3 checks the function, not the built file.

**Notes:**
- N1: an empty lot passes silently.
- N2: `benchmarks.council_from_shares` still uses argmax for ward winners.
- N3: pipes inside the GFM table cells.
- N4: MODEL-INDEX was regenerated mid-batch.

**Partial runs by the reviewer:** green in 25 modules apart from the expected
`test_export_draws` failures.

**Disposition:** all accepted and sent to the writer, 2026-10-09.
